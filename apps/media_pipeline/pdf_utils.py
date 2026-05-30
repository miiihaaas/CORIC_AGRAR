"""Media pipeline PDF utilities — PDF MIME validacija + cover thumbnail generation.

Story 2.4 (Epic 2) — proširenje Story 2.3 image pipeline foundation-a.
Konzumiran od:
  - apps/media_pipeline/signals.py (post_save handler za ProductBrochure)
  - Story 8.6 admin ProductBrochureForm.clean_pdf_file() (per Story 2.3 AC5 pattern analog)

Per project-context.md § Anti-pattern: File upload bez double-check —
Django FileField validate file extension samo (`.pdf`), NE MIME signature.
PDF MIME check kroz python-magic detect-uje `application/pdf` iz fajl signature
(magic bytes `b"%PDF-"`).

System dependency: poppler-utils (Dockerfile linija 42, verifikovano live) —
pdf2image.convert_from_bytes() raise-uje PDFInfoNotInstalledError ako poppler
nije instaliran. Razdvojeno od utils.py (image module) per Decision PDF-D1:
separation of concerns + Story 8.6 može import-ovati validate_pdf_mime BEZ
Pillow tranzitivnih import-a.

FIX iter-1 DoS guards (CRIT-4):
- MAX_PDF_PAGE_COUNT (200) — pdfinfo metadata check pre render-a
- PDF_RENDER_TIMEOUT_SECONDS (15) — pdf2image timeout kwarg (>= 1.17)
- MAX_RENDERED_PIXELS (50_000_000) — eksplicitan pixel check posle render-a
  (pdf2image bypass-uje Pillow MAX_IMAGE_PIXELS)
"""

from __future__ import annotations

import logging
from io import BytesIO
from typing import Iterable

import magic
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import UploadedFile
from django.db.models.fields.files import FieldFile
from django.utils.translation import gettext_lazy as _
from pdf2image import convert_from_bytes, pdfinfo_from_bytes
from pdf2image.exceptions import (
    PDFInfoNotInstalledError,
    PDFPageCountError,
    PDFPopplerTimeoutError,
    PDFSyntaxError,
)
from PIL import Image

logger = logging.getLogger("apps.media_pipeline.pdf_utils")

ALLOWED_PDF_MIME_TYPES: tuple[str, ...] = ("application/pdf",)
MIME_SNIFF_BYTES: int = 2048
# FIX iter-1 CRIT-1: 10 MB sync sa Story 2.3 MP-D8 (FILE_UPLOAD_MAX_MEMORY_SIZE).
MAX_PDF_UPLOAD_SIZE_BYTES: int = 10 * 1024 * 1024
# FIX iter-1 CRIT-4: page count DoS guard — pdfinfo provera PRE render-a.
MAX_PDF_PAGE_COUNT: int = 200
# FIX iter-1 CRIT-4: pdf2image render timeout (poppler PDF-bomb / loop guard).
PDF_RENDER_TIMEOUT_SECONDS: int = 15
# FIX iter-1 CRIT-4: rendered page pixel ceiling (decompression bomb guard).
MAX_RENDERED_PIXELS: int = 50_000_000
COVER_THUMBNAIL_SIZE: tuple[int, int] = (240, 320)
COVER_THUMBNAIL_QUALITY: int = 85
COVER_THUMBNAIL_FORMAT: str = "JPEG"


def validate_pdf_mime(
    upload: UploadedFile | None,
    *,
    allowed_mimes: Iterable[str] = ALLOWED_PDF_MIME_TYPES,
    max_size_bytes: int = MAX_PDF_UPLOAD_SIZE_BYTES,
    max_page_count: int = MAX_PDF_PAGE_COUNT,
) -> None:
    """Double-check da je upload validan PDF kroz MIME signature + size + page count.

    Raise-uje ValidationError sa locale-aware porukom ako:
    - File je prazan (0 bytes) ili upload is None
    - File je veći od max_size_bytes (DoS guard; default 10MB sync sa MP-D8)
    - python-magic detect-uje MIME koji NIJE u allowed_mimes
    - PDF ima više od max_page_count stranica (FIX iter-1 CRIT-4)

    Side-effect: upload.seek(0) na ulazu i izlazu (caller nije obavezan da reset-uje).

    Mirror Story 2.3 validate_image_mime() pattern — isti error message stil,
    isti seek-back discipline, isti gettext_lazy korišćenje.
    """
    if upload is None or not upload.size:
        raise ValidationError(_("PDF brošura je prazna ili nije priložena."))

    if upload.size > max_size_bytes:
        raise ValidationError(
            _(
                "PDF brošura je veća od %(limit)d MB. "
                "Maksimalna dozvoljena veličina je %(limit)d MB."
            )
            % {"limit": max_size_bytes // (1024 * 1024)}
        )

    upload.seek(0)
    header = upload.read(MIME_SNIFF_BYTES)
    upload.seek(0)

    detected_mime = magic.from_buffer(header, mime=True)
    allowed_tuple = tuple(allowed_mimes)
    if detected_mime not in allowed_tuple:
        raise ValidationError(
            _("Nedozvoljen tip fajla: %(mime)s. Dozvoljen je samo PDF format.")
            % {"mime": detected_mime}
        )

    # FIX iter-1 CRIT-4 — DoS guard: page count provera PRE render-a.
    # FIX iter-2 SEC-1: suženo `except Exception` → konkretni PDF/IO exception-i.
    # Pošteno bypass: korumpiran PDF struct PRE pages tree — propustimo na render-time
    # guards (timeout + pixel cap). Defense-in-depth: render-time render-fn ima
    # nezavisni timeout + decompression bomb guard. NIJE bezbednosna rupa.
    try:
        upload.seek(0)
        info = pdfinfo_from_bytes(upload.read())
        upload.seek(0)
        page_count = int(info.get("Pages", 0))
        if page_count > max_page_count:
            raise ValidationError(
                _("PDF brošura ima %(pages)d stranica. Maksimum je %(limit)d.")
                % {"pages": page_count, "limit": max_page_count}
            )
    except ValidationError:
        raise
    except (
        PDFInfoNotInstalledError,
        PDFPageCountError,
        PDFSyntaxError,
        OSError,
        ValueError,
    ):
        upload.seek(0)
        return


def generate_brochure_cover_thumbnail(pdf_field: FieldFile) -> ContentFile | None:
    """Render-uje prvu stranu PDF-a kao 240×320 JPG ContentFile (in-memory).

    Args:
        pdf_field: ProductBrochure.pdf_file FieldFile (Django FileField proxy)

    Returns:
        ContentFile sa JPEG bytes-ima (ime "brochure-cover.jpg") spreman za save na
        ProductBrochure.cover_thumbnail_image polje. Ako je PDF korumpiran ili nema
        validnu prvu stranu, vraća `None` (caller signal handler interpretira `None` kao
        graceful failure → loguje warning + skip save).

    Used by: apps/media_pipeline/signals.py handle_brochure_post_save() (AC3-AC5).

    NEVER raises — sve exception-e (PDFInfoNotInstalledError, PDFPageCountError,
    PDFPopplerTimeoutError, PDFSyntaxError, OSError, ValueError, generic Exception)
    hvata i loguje kroz logger.warning() / logger.error(). Garantuje da signal
    handler ne pukne admin save flow.

    FIX iter-1 CRIT-4 DoS guards:
    - timeout=PDF_RENDER_TIMEOUT_SECONDS (15s) → PDFPopplerTimeoutError @ render time
    - rendered_pixels > MAX_RENDERED_PIXELS (50M) → graceful None return
    FIX iter-1 CRIT-8: enkriptovan PDF triggeruje PDFSyntaxError → graceful None.
    """
    if not pdf_field or not getattr(pdf_field, "name", ""):
        return None

    try:
        # Read PDF kao bytes — pdf2image.convert_from_bytes je sigurnije od
        # convert_from_path (ne mora znati apsolutni storage path; Django Storage
        # API može biti S3 ili Whitenoise-served).
        pdf_field.open("rb")
        try:
            pdf_bytes = pdf_field.read()
        finally:
            pdf_field.close()

        # Render samo prvu stranu — dpi=100 (balans kvalitet/brzina; 240×320 thumbnail
        # ne treba viši dpi); fmt="jpeg" eksplicitno za čitljivost.
        # FIX iter-1 CRIT-4: timeout kwarg (pdf2image >= 1.17) — poppler hang guard.
        images = convert_from_bytes(
            pdf_bytes,
            first_page=1,
            last_page=1,
            fmt="jpeg",
            dpi=100,
            timeout=PDF_RENDER_TIMEOUT_SECONDS,
        )
        if not images:
            logger.warning(
                "Brochure cover render: convert_from_bytes returned empty list "
                "(PDF has 0 pages?). Brochure ID: %s",
                getattr(getattr(pdf_field, "instance", None), "id", "unknown"),
            )
            return None

        # FIX iter-2 ARCH-4: eksplicitan close() za sve PIL Image objekte iz pdf2image.
        # Bez ovog wrap-a, page_image i ostale stranice mogu držati temp file handle
        # do GC ciklusa — resource leak risk na high-volume admin save flow.
        try:
            page_image = images[0]

            # FIX iter-1 CRIT-4: decompression bomb guard — eksplicitan pixel check.
            rendered_pixels = page_image.width * page_image.height
            if rendered_pixels > MAX_RENDERED_PIXELS:
                logger.warning(
                    "Brochure cover render: rendered page too large (%d px > %d). "
                    "Brochure ID: %s",
                    rendered_pixels,
                    MAX_RENDERED_PIXELS,
                    getattr(getattr(pdf_field, "instance", None), "id", "unknown"),
                )
                return None

            # Force RGB pre JPEG save (Gotcha PDF-9 — libjpeg ne podržava RGBA/P modes).
            if page_image.mode != "RGB":
                page_image = page_image.convert("RGB")
            # Aspect ratio preserved (Decision PDF-D3) — thumbnail() je in-place mutation.
            page_image.thumbnail(COVER_THUMBNAIL_SIZE, Image.Resampling.LANCZOS)

            # FIX iter-2 ARCH-3: BytesIO u with-block — garantuje close() i pri exception-u.
            with BytesIO() as buffer:
                page_image.save(
                    buffer,
                    format=COVER_THUMBNAIL_FORMAT,
                    quality=COVER_THUMBNAIL_QUALITY,
                )
                buffer.seek(0)
                return ContentFile(buffer.getvalue(), name="brochure-cover.jpg")
        finally:
            # Close ALL pages (not just images[0]) — first_page=last_page=1 obično vraća 1,
            # ali defensive: zatvaramo sve da ne curi handle ako pdf2image vrati više.
            for img in images:
                try:
                    img.close()
                except Exception:  # noqa: BLE001 — close() je best-effort; ignoriši errore
                    pass

    except (
        PDFInfoNotInstalledError,
        PDFPageCountError,
        PDFPopplerTimeoutError,
        PDFSyntaxError,
        OSError,
        ValueError,
    ) as exc:
        logger.warning(
            "Brochure cover render failed (recoverable). Brochure ID: %s. Error: %s",
            getattr(getattr(pdf_field, "instance", None), "id", "unknown"),
            exc,
        )
        return None
    except Exception as exc:  # noqa: BLE001 — defensive catch-all, see docstring
        logger.error(
            "Brochure cover render: unexpected exception. Brochure ID: %s. Error: %s",
            getattr(getattr(pdf_field, "instance", None), "id", "unknown"),
            exc,
            exc_info=True,
        )
        return None
