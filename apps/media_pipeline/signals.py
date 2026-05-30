"""Media pipeline signals — automatska post-save logika za media polja.

Story 2.4 (Epic 2) — prvi signal handler u media_pipeline app-u.
Wire-uje se kroz apps/media_pipeline/apps.py.ready() (per Django best practice).

KRITIČNO (Story 2.3 AC8 boundary regression):
  apps.media_pipeline NE SME importovati apps.products direktno.
  `tests/integration/test_app_boundaries.py` enforces ovo kroz AST static check.
  Posledica: signal handler koristi `apps.get_model("products", "ProductBrochure")`
  kasnu resoluciju u ready() hook-u (vidi apps.py), NE statički import.

FIX iter-1 CRIT-3 — Replace-PDF UX:
  Handler regeneriše cover SVAKI put kad se pdf_file menja. NEMA
  `if cover_already_exists: return` skip-a (stara verzija je hidirala bug gde
  Editor zameni pdf_file ali cover ostane stale). Detection:
  `pdf_file_touched = update_fields is None or "pdf_file" in update_fields`.
  Multi-layer infinite loop guard:
  - Layer A: skip ako update_fields == {"cover_thumbnail_image"} (interni save)
  - Layer B: instance.cover_thumbnail_image.save(..., save=False) — Storage write
    bez post_save fires; jedini eksplicitan instance.save() je pod Layer A skip-om

FIX iter-1 CRIT-5 — Transaction safety:
  ImageField.save() piše na disk PRE commit-a outer transakcije. Ako outer save
  rollback-uje (npr. drugi pre_save signal raise-uje ValidationError), file ostaje
  orphan na disku. Rešenje: render + storage save unutar
  `transaction.on_commit()` callback-a — izvršava se SAMO ako outer transakcija
  uspešno commit-uje.
"""

from __future__ import annotations

import logging
from typing import Any

from django.db import transaction

from apps.media_pipeline.pdf_utils import generate_brochure_cover_thumbnail

logger = logging.getLogger("apps.media_pipeline.signals")


def handle_brochure_post_save(
    sender: Any,
    instance: Any,
    created: bool,
    raw: bool,
    update_fields: frozenset[str] | None = None,
    **kwargs: Any,
) -> None:
    """post_save handler za ProductBrochure — auto-populiše cover_thumbnail_image.

    Wire-uje se eksplicitno u apps/media_pipeline/apps.py.ready() kroz
    `post_save.connect(handle_brochure_post_save, sender=ProductBrochure, ...)`.

    Skip conditions (return early):
    - raw=True (loaddata fixtures — Django ne triggeruje user save flow)
    - update_fields == {"cover_thumbnail_image"} (interni save iz callback-a — Layer A)
    - instance.pdf_file je prazan (defensive guard)
    - pdf_file NIJE u update_fields (title-only edit → performance skip)

    Stvarni render + storage save izvršavaju se UNUTAR transaction.on_commit()
    callback-a (FIX iter-1 CRIT-5 — orphan-file safety pri rollback-u).

    Failure modes: NIKAD ne raise-uje (callback hvata sve exception-e defensive-no).
    """
    if raw:
        return

    # Layer A — infinite loop guard: interni save iz on_commit callback-a
    if (
        update_fields is not None
        and "cover_thumbnail_image" in update_fields
        and len(update_fields) == 1
    ):
        return

    # FIX iter-1 CRIT-3: regeneration trigger detection.
    # update_fields=None → full save (create ili .save() bez argumenta) → regeneriši
    # "pdf_file" in update_fields → Editor je menjao PDF → regeneriši
    # Multi-field save bez pdf_file (npr. {"title"}) → skip (performance optimization)
    pdf_file_touched = update_fields is None or "pdf_file" in update_fields
    if not pdf_file_touched:
        return

    # Defensive guard — pdf_file required po model-u ali AC6 + FIX iter-1 CRIT-7:
    # bulk_create / raw SQL bypass admin form mogu pozvati signal sa praznim poljem.
    if not instance.pdf_file or not getattr(instance.pdf_file, "name", ""):
        return

    # FIX iter-1 CRIT-5: defer render + storage save u on_commit callback —
    # ako outer transakcija rollback-uje, callback se NIKAD ne poziva (no orphan).
    def _generate_cover_on_commit() -> None:
        try:
            cover_file = generate_brochure_cover_thumbnail(instance.pdf_file)
            if cover_file is None:
                # Graceful failure — pdf_utils.py je već logovao detaljan warning.
                # Brochure ostaje sa praznim cover_thumbnail_image; Story 2.7 template
                # ima fallback (generic PDF icon).
                logger.warning(
                    "Brochure cover generation returned None. Brochure ID: %s. "
                    "Product slug: %s.",
                    getattr(instance, "id", "unknown"),
                    getattr(getattr(instance, "product", None), "slug", "unknown"),
                )
                return

            # save=False → Storage piše fajl ali NE poziva instance.save() (no signal).
            instance.cover_thumbnail_image.save(cover_file.name, cover_file, save=False)
            # Layer A guard će skip-ovati ovaj signal (single-field update_fields).
            instance.save(update_fields=["cover_thumbnail_image"])
            logger.info(
                "Brochure cover generated successfully. Brochure ID: %s. "
                "Product slug: %s.",
                getattr(instance, "id", "unknown"),
                getattr(getattr(instance, "product", None), "slug", "unknown"),
            )
        except Exception:  # noqa: BLE001 — defensive catch-all u callback-u
            # AC3 non-raising contract: callback NE sme raise-ovati u outer transakciju.
            # Ako generate_brochure_cover_thumbnail nekontrolisano raise-uje (bug u
            # contract-u), logujemo error sa stack trace i return-ujemo.
            logger.exception(
                "Brochure cover generation callback raised unexpected exception. "
                "Brochure ID: %s.",
                getattr(instance, "id", "unknown"),
            )

    transaction.on_commit(_generate_cover_on_commit)
