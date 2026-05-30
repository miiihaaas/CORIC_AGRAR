"""Story 2.4 — apps/media_pipeline/apps.py MediaPipelineConfig.ready() RED phase testovi.

Pokriva AC4 — signal registracija + dispatch_uid idempotency.

Per Story 2.4 AC4: `MediaPipelineConfig.ready()` MORA:
1. Resolvovati ProductBrochure model kroz `apps.get_model("products", "ProductBrochure")`
   (kasna resolucija — NIJE statički import; očuvana Story 2.3 AC8 boundary).
2. Registrovati `handle_brochure_post_save` kao post_save receiver za ProductBrochure.
3. Koristiti `dispatch_uid="apps.media_pipeline.signals.handle_brochure_post_save"` za
   deduplication (sprečava double-registration ako ready() bude pozvan dva puta).

Per Story 2.3 MP-D6 + Story 2.4 PDF-1: pokrenuti kroz Docker:

    docker compose -f compose/local.yml run --rm django uv run pytest \
        apps/media_pipeline/tests/test_apps_ready.py -v

TEA RED phase: SVI testovi MORAJU pasti dok Dev ne doda `ready()` u
MediaPipelineConfig + `signals.py` modul.
"""

from __future__ import annotations


# =============================================================================
# AC4 — Signal registracija introspekcija
# =============================================================================


def _sync_live_receivers(signal, sender):
    """Helper — vraća SAMO sync receivers iz `signal._live_receivers(sender=...)`.

    Django `_live_receivers` API vraća `tuple[list[sync], list[async]]` (Python 3.13 +
    Django 5.2 verifikovano). Za boundary tests u Story 2.4 nas zanima sync layer
    (post_save handler je sync funkcija).
    """
    result = signal._live_receivers(sender=sender)
    # Django 5.x: tuple (sync_receivers, async_receivers)
    if isinstance(result, tuple) and len(result) == 2:
        sync_list, _async_list = result
        return list(sync_list)
    # Fallback (defensive — starije Django verzije vraćaju single list)
    return list(result)


def test_ready_method_wires_post_save_signal():
    """AC4 — posle Django startup-a, handle_brochure_post_save je live receiver za
    post_save signal sa sender=ProductBrochure.

    Test je integration-style — proverava efekat AppConfig.ready() koji Django automatski
    poziva pri startup-u. Bez Dev implementacije (Story 2.4 GREEN), test failuje na
    ImportError za apps.media_pipeline.signals.
    """
    from django.db.models.signals import post_save

    from apps.media_pipeline.signals import handle_brochure_post_save
    from apps.products.models import ProductBrochure

    live_receivers = _sync_live_receivers(post_save, sender=ProductBrochure)

    assert handle_brochure_post_save in live_receivers, (
        "handle_brochure_post_save NIJE registrovan kao post_save receiver za ProductBrochure. "
        "Verifikuj da MediaPipelineConfig.ready() poziva post_save.connect(...) "
        "sa dispatch_uid='apps.media_pipeline.signals.handle_brochure_post_save'."
    )


def test_ready_method_idempotent_double_call():
    """AC4 + IMP iter-1 IMP-7 — dispatch_uid sprečava double-registration.

    Test pravi sledeću asercije:
    (a) Posle Django startup-a, handle_brochure_post_save je tačno JEDAN put u
        live_receivers (signal je registrovan kroz ready()).
    (b) Manualan drugi ready() poziv NE menja broj — dispatch_uid deduplicira.

    Bez Dev implementacije ready() metoda + signals.py + dispatch_uid-a, test failuje:
    - ImportError za apps.media_pipeline.signals (Dev nije napravio modul), ILI
    - handle_brochure_post_save NIJE u live receiver-ima (ready() ga ne wire-uje), ILI
    - dispatch_uid nije postavljen → drugi ready() call duplira receiver.
    """
    from django.apps import apps as django_apps
    from django.db.models.signals import post_save

    from apps.media_pipeline.signals import handle_brochure_post_save
    from apps.products.models import ProductBrochure

    # (a) Asertiraj baseline registraciju (jedan receiver = handle_brochure_post_save)
    before = _sync_live_receivers(post_save, sender=ProductBrochure)
    assert handle_brochure_post_save in before, (
        "handle_brochure_post_save NIJE registrovan kao post_save receiver za "
        "ProductBrochure posle Django startup-a. MediaPipelineConfig.ready() mora "
        "pozvati post_save.connect(handle_brochure_post_save, sender=ProductBrochure, "
        "dispatch_uid='apps.media_pipeline.signals.handle_brochure_post_save')."
    )
    media_pipeline_receivers_before = [
        r for r in before if r is handle_brochure_post_save
    ]

    # (b) Drugi ready() poziv MORA biti idempotent (dispatch_uid deduplicira)
    media_config = django_apps.get_app_config("media_pipeline")
    media_config.ready()

    after = _sync_live_receivers(post_save, sender=ProductBrochure)
    media_pipeline_receivers_after = [
        r for r in after if r is handle_brochure_post_save
    ]

    assert len(media_pipeline_receivers_after) == len(media_pipeline_receivers_before), (
        f"dispatch_uid mora deduplicirati signal connection. "
        f"Pre druge ready() call: {len(media_pipeline_receivers_before)} kopija "
        f"handle_brochure_post_save; posle: {len(media_pipeline_receivers_after)}. "
        f"Dev MORA proslediti dispatch_uid='apps.media_pipeline.signals.handle_brochure_post_save' "
        f"u post_save.connect() pozivu."
    )
    assert len(media_pipeline_receivers_after) == 1, (
        f"Tačno jedna kopija handle_brochure_post_save mora biti registrovana "
        f"(dispatch_uid contract). Nađeno: {len(media_pipeline_receivers_after)}."
    )
