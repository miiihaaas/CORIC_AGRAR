"""Story 2.4 — apps/media_pipeline/signals.py RED phase testovi.

Pokriva AC3 (handler skip uslovi + on_commit callback) + AC4 (signal registracija
introspekcija) + AC6 (graceful failure) + AC7 (infinite loop guard + replace PDF regen).

Per Story 2.4 spec: TEA piše PURE UNIT TESTE — koristi MagicMock instance umesto realan
ProductBrochure.objects.create() (FIX iter-1 CRIT-7 rationale — model je FileField BEZ
blank=True, integration testovi sa pdf_file=None nisu mogući). Integration testovi sa
realnim DB-jem i `@pytest.mark.django_db(transaction=True)` su POZAJMLJENI od Step 4
GREEN-phase (Dev scope) — ovde fokus na handler logiku.

Per Story 2.3 MP-D6 + Story 2.4 PDF-1: pokrenuti kroz Docker:

    docker compose -f compose/local.yml run --rm django uv run pytest \
        apps/media_pipeline/tests/test_signals.py -v

TEA RED phase: SVI testovi MORAJU pasti dok Dev ne kreira
`apps/media_pipeline/signals.py` sa `handle_brochure_post_save()` funkcijom.
"""

from __future__ import annotations

import logging
from unittest.mock import MagicMock

import pytest


# =============================================================================
# Helpers
# =============================================================================


def _make_instance(pdf_name: str = "products/brochures/test.pdf"):
    """MagicMock za ProductBrochure instance — `instance.pdf_file` truthy + ima `.name`."""
    instance = MagicMock()
    instance.id = 1
    instance.pdf_file = MagicMock()
    instance.pdf_file.name = pdf_name
    instance.pdf_file.__bool__ = lambda self: bool(pdf_name)
    instance.cover_thumbnail_image = MagicMock()
    instance.cover_thumbnail_image.name = ""
    instance.product = MagicMock()
    instance.product.slug = "test-product"
    return instance


# =============================================================================
# AC3 — Handler skip uslovi i on_commit callback registracija
# =============================================================================


def test_post_save_skips_when_raw_true(mocker):
    """AC3 — raw=True (loaddata fixture import) → early return; on_commit NIJE pozvan."""
    from apps.media_pipeline.signals import handle_brochure_post_save

    on_commit_spy = mocker.patch("apps.media_pipeline.signals.transaction.on_commit")
    generate_spy = mocker.patch("apps.media_pipeline.signals.generate_brochure_cover_thumbnail")

    instance = _make_instance()
    handle_brochure_post_save(
        sender=MagicMock(),
        instance=instance,
        created=True,
        raw=True,
        update_fields=None,
    )

    assert on_commit_spy.call_count == 0, "on_commit ne sme biti pozvan kad raw=True"
    assert generate_spy.call_count == 0, "render ne sme biti pozvan kad raw=True"


def test_post_save_skips_when_update_fields_only_cover(mocker):
    """AC3 + AC7 Layer A guard — internal save (update_fields={'cover_thumbnail_image'}) → skip."""
    from apps.media_pipeline.signals import handle_brochure_post_save

    on_commit_spy = mocker.patch("apps.media_pipeline.signals.transaction.on_commit")
    generate_spy = mocker.patch("apps.media_pipeline.signals.generate_brochure_cover_thumbnail")

    instance = _make_instance()
    handle_brochure_post_save(
        sender=MagicMock(),
        instance=instance,
        created=False,
        raw=False,
        update_fields=frozenset({"cover_thumbnail_image"}),
    )

    assert on_commit_spy.call_count == 0, "Layer A guard mora skip-ovati interni save"
    assert generate_spy.call_count == 0


def test_handler_skips_when_no_pdf_file(mocker):
    """AC6 + FIX iter-1 CRIT-7 — defensive guard: instance.pdf_file == None / empty → skip.

    Pure UNIT test sa MagicMock per spec (model je FileField BEZ blank=True; integration
    test sa pdf_file=None nije moguć). Defensive guard štiti od bulk_create() ili raw SQL
    bypass-a koji bi pozvao signal sa praznim pdf_file poljem.
    """
    from apps.media_pipeline.signals import handle_brochure_post_save

    on_commit_spy = mocker.patch("apps.media_pipeline.signals.transaction.on_commit")
    generate_spy = mocker.patch("apps.media_pipeline.signals.generate_brochure_cover_thumbnail")

    instance = MagicMock()
    instance.pdf_file = MagicMock()
    instance.pdf_file.name = ""
    instance.pdf_file.__bool__ = lambda self: False
    instance.cover_thumbnail_image = MagicMock()
    instance.cover_thumbnail_image.name = ""

    handle_brochure_post_save(
        sender=MagicMock(),
        instance=instance,
        created=True,
        raw=False,
        update_fields=None,
    )

    assert on_commit_spy.call_count == 0
    assert generate_spy.call_count == 0


def test_post_save_uses_on_commit_callback(mocker):
    """AC3 + AC7 + FIX iter-1 CRIT-5 — render + storage save MORAJU biti deferred kroz
    transaction.on_commit. Verifikuje da handler registruje callback ali NIJE
    sinhrono izvršava render.
    """
    from apps.media_pipeline.signals import handle_brochure_post_save

    on_commit_spy = mocker.patch("apps.media_pipeline.signals.transaction.on_commit")
    generate_spy = mocker.patch("apps.media_pipeline.signals.generate_brochure_cover_thumbnail")

    instance = _make_instance()
    handle_brochure_post_save(
        sender=MagicMock(),
        instance=instance,
        created=True,
        raw=False,
        update_fields=None,
    )

    # Callback je registrovan
    assert on_commit_spy.call_count == 1, "Handler MORA registrovati on_commit callback"
    # Render NIJE pozvan direktno iz handler-a (samo iz callback-a koji mock ne poziva)
    assert generate_spy.call_count == 0, (
        "generate_brochure_cover_thumbnail NE sme biti pozvan sinhrono iz handler-a — "
        "samo unutar on_commit callback-a"
    )


def test_post_save_skips_when_update_fields_does_not_include_pdf_file(mocker):
    """AC3 + AC7 + FIX iter-1 CRIT-3 — title-only edit (update_fields=['title']) → skip render.

    Performance optimization: ako pdf_file nije menjan, nepotrebno je rerender-ovati cover.
    """
    from apps.media_pipeline.signals import handle_brochure_post_save

    on_commit_spy = mocker.patch("apps.media_pipeline.signals.transaction.on_commit")

    instance = _make_instance()
    handle_brochure_post_save(
        sender=MagicMock(),
        instance=instance,
        created=False,
        raw=False,
        update_fields=frozenset({"title"}),
    )

    assert on_commit_spy.call_count == 0, "Title-only edit ne sme triggerovati on_commit"


def test_post_save_regenerates_cover_when_pdf_replaced(mocker):
    """AC3 + AC7 + FIX iter-1 CRIT-3 — Editor menja pdf_file → cover MORA biti regen.

    Stara verzija handler-a je imala `if instance.cover_thumbnail_image: return` skip
    koji je hidirao bug (stale cover na zameni PDF-a). Sada handler regeneriše uvek.
    """
    from apps.media_pipeline.signals import handle_brochure_post_save

    on_commit_spy = mocker.patch("apps.media_pipeline.signals.transaction.on_commit")

    instance = _make_instance()
    # Simuliraj da cover_thumbnail_image VEĆ POSTOJI (Editor menja pdf_file na već-saved brochure)
    instance.cover_thumbnail_image.name = "products/brochure_covers/old.jpg"
    instance.cover_thumbnail_image.__bool__ = lambda self: True

    handle_brochure_post_save(
        sender=MagicMock(),
        instance=instance,
        created=False,
        raw=False,
        update_fields=frozenset({"pdf_file"}),
    )

    # Mora se registrovati callback za regeneraciju
    assert on_commit_spy.call_count == 1, (
        "Replace pdf_file MORA triggerovati regen — handler ne sme skip-ovati ako "
        "cover_thumbnail_image već postoji (FIX iter-1 CRIT-3)"
    )


# =============================================================================
# AC6 — Graceful failure handling u callback-u
# =============================================================================


def test_handler_logs_warning_on_generate_failure(mocker, caplog):
    """AC6 — kad generate_brochure_cover_thumbnail vrati None, callback mora logovati
    WARNING sa logger-om 'apps.media_pipeline.signals'."""
    from apps.media_pipeline.signals import handle_brochure_post_save

    # Mock on_commit da odmah pozove callback (simuliramo commit)
    captured_callbacks = []

    def fake_on_commit(callback, *args, **kwargs):
        captured_callbacks.append(callback)

    mocker.patch(
        "apps.media_pipeline.signals.transaction.on_commit",
        side_effect=fake_on_commit,
    )
    mocker.patch(
        "apps.media_pipeline.signals.generate_brochure_cover_thumbnail",
        return_value=None,  # graceful failure
    )

    instance = _make_instance()
    handle_brochure_post_save(
        sender=MagicMock(),
        instance=instance,
        created=True,
        raw=False,
        update_fields=None,
    )

    # Sad ručno pokreni callback (simuliramo commit-after-handler)
    assert captured_callbacks, "Callback mora biti registrovan"
    with caplog.at_level(logging.WARNING, logger="apps.media_pipeline.signals"):
        captured_callbacks[0]()

    relevant = [
        r
        for r in caplog.records
        if r.name == "apps.media_pipeline.signals" and r.levelno >= logging.WARNING
    ]
    assert relevant, (
        "Callback mora logovati WARNING preko 'apps.media_pipeline.signals' kad render vrati None"
    )


def test_handler_does_not_raise_on_generate_exception(mocker):
    """AC3 non-raising contract — ako generate_brochure_cover_thumbnail neočekivano
    raise-uje (bug u Dev kodu), handler MORA da hvata da ne pucu admin save flow.

    NOTE: AC2 garantuje da generate NEVER raises, ali defensive — handler mora biti
    robust ako se contract slučajno prekrši.
    """
    from apps.media_pipeline.signals import handle_brochure_post_save

    captured_callbacks = []

    def fake_on_commit(callback, *args, **kwargs):
        captured_callbacks.append(callback)

    mocker.patch(
        "apps.media_pipeline.signals.transaction.on_commit",
        side_effect=fake_on_commit,
    )
    mocker.patch(
        "apps.media_pipeline.signals.generate_brochure_cover_thumbnail",
        side_effect=RuntimeError("simulated unexpected exception"),
    )

    instance = _make_instance()
    # Handler call sam ne sme raise-ovati
    handle_brochure_post_save(
        sender=MagicMock(),
        instance=instance,
        created=True,
        raw=False,
        update_fields=None,
    )

    # Callback je registered ali ne pozvan — pokrenimo ga i verifikuj da NE raise-uje
    assert captured_callbacks
    # Callback NE sme raise-ovati exception u outer transakciju (admin save flow safety)
    try:
        captured_callbacks[0]()
    except Exception as exc:
        pytest.fail(
            f"Callback iz signal handler-a NE sme raise-ovati exception (AC3 non-raising "
            f"contract). Dobio: {type(exc).__name__}: {exc}"
        )


def test_handler_skips_save_when_generate_returns_none(mocker):
    """AC6 — kad generate vrati None, callback NE sme save-ovati na cover_thumbnail_image.

    Brochure ostaje sa praznim cover-om; Editor vidi save uspeh.
    """
    from apps.media_pipeline.signals import handle_brochure_post_save

    captured_callbacks = []

    def fake_on_commit(callback, *args, **kwargs):
        captured_callbacks.append(callback)

    mocker.patch(
        "apps.media_pipeline.signals.transaction.on_commit",
        side_effect=fake_on_commit,
    )
    mocker.patch(
        "apps.media_pipeline.signals.generate_brochure_cover_thumbnail",
        return_value=None,
    )

    instance = _make_instance()
    handle_brochure_post_save(
        sender=MagicMock(),
        instance=instance,
        created=True,
        raw=False,
        update_fields=None,
    )

    assert captured_callbacks
    captured_callbacks[0]()

    # Verifikuj da cover_thumbnail_image.save NIJE pozvan (generate vratio None)
    assert instance.cover_thumbnail_image.save.call_count == 0, (
        "Kad generate vrati None, callback NE sme save-ovati cover_thumbnail_image"
    )
    # Verifikuj da instance.save NIJE pozvan
    assert instance.save.call_count == 0, (
        "Kad generate vrati None, callback NE sme pozvati instance.save()"
    )


def test_handler_saves_cover_when_generate_returns_content_file(mocker):
    """AC6 + AC3 — kad generate vrati ContentFile, callback save-uje na storage + emit-uje
    instance.save(update_fields=['cover_thumbnail_image']) (Layer B contract)."""
    from django.core.files.base import ContentFile

    from apps.media_pipeline.signals import handle_brochure_post_save

    captured_callbacks = []

    def fake_on_commit(callback, *args, **kwargs):
        captured_callbacks.append(callback)

    mocker.patch(
        "apps.media_pipeline.signals.transaction.on_commit",
        side_effect=fake_on_commit,
    )
    fake_content = ContentFile(b"fake-jpeg-bytes", name="brochure-cover.jpg")
    mocker.patch(
        "apps.media_pipeline.signals.generate_brochure_cover_thumbnail",
        return_value=fake_content,
    )

    instance = _make_instance()
    handle_brochure_post_save(
        sender=MagicMock(),
        instance=instance,
        created=True,
        raw=False,
        update_fields=None,
    )

    assert captured_callbacks
    captured_callbacks[0]()

    # Storage write: cover_thumbnail_image.save(name, content, save=False)
    assert instance.cover_thumbnail_image.save.call_count == 1, (
        "Callback MORA pozvati cover_thumbnail_image.save() jednom"
    )
    # save=False mora biti kwarg (sprečava implicit instance.save() u Storage API-u)
    call_kwargs = instance.cover_thumbnail_image.save.call_args.kwargs
    assert call_kwargs.get("save") is False, (
        "cover_thumbnail_image.save() MORA biti pozvan sa save=False kako bi sprečio "
        "implicit instance.save() u Storage API-u (Layer B infinite loop guard)"
    )
    # Eksplicitan instance.save(update_fields=['cover_thumbnail_image'])
    assert instance.save.call_count == 1, "Callback MORA pozvati instance.save() jednom"
    save_kwargs = instance.save.call_args.kwargs
    assert save_kwargs.get("update_fields") == ["cover_thumbnail_image"], (
        "instance.save MORA biti pozvan sa update_fields=['cover_thumbnail_image'] "
        "(Layer A guard će skip-ovati ovaj signal call)"
    )
