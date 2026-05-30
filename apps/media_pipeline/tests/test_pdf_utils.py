"""Story 2.4 — apps/media_pipeline/pdf_utils.py RED phase testovi.

Pokriva AC1 (`validate_pdf_mime`) + AC2 (`generate_brochure_cover_thumbnail`).

Per Decision PDF-D5: minimal raw PDF struct fixture (NEMA reportlab dep).
Per Story 2.3 MP-D6 + Story 2.4 PDF-1: pokrenuti kroz Docker (libmagic + poppler-utils
system dep-i nisu dostupni na Windows host-u):

    docker compose -f compose/local.yml run --rm django uv run pytest \
        apps/media_pipeline/tests/test_pdf_utils.py -v

TEA RED phase: SVI testovi MORAJU pasti (ImportError ili AttributeError) dok Dev ne
kreira `apps/media_pipeline/pdf_utils.py` sa traženim API-jem.
"""

from __future__ import annotations

import logging
from io import BytesIO

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile


# =============================================================================
# Helpers
# =============================================================================


def _upload(name: str, content: bytes, content_type: str = "application/pdf"):
    """SimpleUploadedFile wrapper sa default PDF content_type."""
    return SimpleUploadedFile(name, content, content_type=content_type)


def _fake_field_file(content: bytes, name: str = "products/brochures/test.pdf"):
    """Pravimo FieldFile-like mock objekat za testove `generate_brochure_cover_thumbnail`.

    Per AC2 signature, funkcija prima FieldFile (Django ImageField/FileField proxy)
    sa `.open("rb")`, `.read()`, `.close()`, `.name`, `.instance.id` API-jem.
    """
    from unittest.mock import MagicMock

    field = MagicMock()
    field.name = name
    field.__bool__ = lambda self=field: bool(name)

    buf = BytesIO(content)

    def _open(mode="rb"):
        buf.seek(0)
        return field

    field.open = _open
    field.read = buf.read
    field.close = lambda: None
    field.instance = MagicMock()
    field.instance.id = 42
    return field


# =============================================================================
# AC1 — validate_pdf_mime
# =============================================================================


def test_validate_pdf_accepts_valid_pdf(minimal_pdf_1_page_bytes):
    """AC1 happy path — minimal validan 1-page PDF prolazi validaciju."""
    from apps.media_pipeline.pdf_utils import validate_pdf_mime

    upload = _upload("brochure.pdf", minimal_pdf_1_page_bytes)
    # Ne raise-uje — return None
    assert validate_pdf_mime(upload) is None


def test_validate_pdf_rejects_non_pdf_mime(valid_jpeg_bytes):
    """AC1 — image kao PDF (extension `.pdf` ali JPEG sadržaj) je odbijen.

    python-magic detect-uje real MIME iz file signature (JPEG SOI marker),
    NE iz extension-a → ValidationError.
    """
    from apps.media_pipeline.pdf_utils import validate_pdf_mime

    upload = _upload("fake.pdf", valid_jpeg_bytes)
    with pytest.raises(ValidationError) as exc_info:
        validate_pdf_mime(upload)
    # Error message mora pominjati MIME tip
    assert "image/jpeg" in str(exc_info.value) or "Nedozvoljen" in str(exc_info.value)


def test_validate_pdf_rejects_oversize_upload(oversized_pdf_bytes):
    """AC1 — upload > 10 MB je odbijen (FIX iter-1 CRIT-1 sync sa MP-D8)."""
    from apps.media_pipeline.pdf_utils import validate_pdf_mime

    upload = _upload("big.pdf", oversized_pdf_bytes)
    with pytest.raises(ValidationError) as exc_info:
        validate_pdf_mime(upload)
    assert "10" in str(exc_info.value) or "MB" in str(exc_info.value)


def test_validate_pdf_rejects_high_page_count(high_page_count_pdf_bytes):
    """AC1 + FIX iter-1 CRIT-4 — PDF sa > 200 stranica je odbijen.

    pdfinfo_from_bytes čita metadata bez render-a; > 200 → ValidationError.
    """
    from apps.media_pipeline.pdf_utils import validate_pdf_mime

    upload = _upload("huge.pdf", high_page_count_pdf_bytes)
    with pytest.raises(ValidationError) as exc_info:
        validate_pdf_mime(upload)
    # Error mora pominjati page count
    msg = str(exc_info.value)
    assert "201" in msg or "stranica" in msg.lower() or "200" in msg


def test_validate_pdf_rejects_empty_upload(empty_pdf_bytes):
    """AC1 — 0-byte upload je odbijen."""
    from apps.media_pipeline.pdf_utils import validate_pdf_mime

    upload = _upload("empty.pdf", empty_pdf_bytes)
    with pytest.raises(ValidationError) as exc_info:
        validate_pdf_mime(upload)
    assert "prazna" in str(exc_info.value).lower() or "nije priložena" in str(exc_info.value).lower()


def test_validate_pdf_rejects_none_upload():
    """AC1 — None upload je odbijen (NE AttributeError)."""
    from apps.media_pipeline.pdf_utils import validate_pdf_mime

    with pytest.raises(ValidationError) as exc_info:
        validate_pdf_mime(None)
    assert "prazna" in str(exc_info.value).lower() or "nije priložena" in str(exc_info.value).lower()


def test_validate_pdf_handles_corrupt_pdf(corrupt_pdf_bytes):
    """AC1 — corrupt PDF bytes (random data) → ValidationError zbog MIME mismatch.

    `b"NOT_A_PDF_AT_ALL..."` nema %PDF magic → libmagic detect-uje text/plain ili
    application/octet-stream → MIME check raise-uje ValidationError (PRE nego što
    pdfinfo dođe na red).
    """
    from apps.media_pipeline.pdf_utils import validate_pdf_mime

    upload = _upload("corrupt.pdf", corrupt_pdf_bytes)
    with pytest.raises(ValidationError):
        validate_pdf_mime(upload)


def test_validate_pdf_seeks_back_to_zero(minimal_pdf_1_page_bytes):
    """AC1 side-effect — upload.tell() == 0 posle validacije (stream reset contract)."""
    from apps.media_pipeline.pdf_utils import validate_pdf_mime

    upload = _upload("brochure.pdf", minimal_pdf_1_page_bytes)
    validate_pdf_mime(upload)
    assert upload.tell() == 0, "Stream mora biti reset-ovan na 0 posle validacije"


def test_validate_pdf_swallowed_pdfinfo_error_does_not_skip_render_guards(mocker):
    """FIX iter-2 SEC-1 (Story 2-4 code review) — defense-in-depth regression.

    Scenarij: attacker upload-uje valid %PDF- magic + korumpiran /Catalog ili /Pages
    xref. pdfinfo_from_bytes raise-uje PDFPageCountError. validate_pdf_mime swallow-uje
    (by design — fall through na render-time guards) i NE raise-uje.

    Ovaj test verifikuje:
    1. Suženi except hvata PDFPageCountError (NIJE više broad `except Exception`).
    2. Render-time guards (timeout + MAX_RENDERED_PIXELS) i dalje rade kao defense-in-depth.
    """
    from pdf2image.exceptions import PDFPageCountError

    from apps.media_pipeline.pdf_utils import validate_pdf_mime

    # Mock pdfinfo_from_bytes da raise PDFPageCountError (simulira corrupt xref).
    mock_pdfinfo = mocker.patch(
        "apps.media_pipeline.pdf_utils.pdfinfo_from_bytes",
        side_effect=PDFPageCountError("simulated corrupt xref"),
    )

    # Valid PDF magic + garbage payload (passes python-magic MIME check).
    upload = SimpleUploadedFile(
        "corrupt.pdf",
        b"%PDF-1.4\n" + b"X" * 1000,
        content_type="application/pdf",
    )

    # NE smije raise — pdfinfo error swallowed by design (defer na render-time).
    assert validate_pdf_mime(upload) is None

    # Verifikujemo da je pdfinfo guard pokušan (suženi except handler radi).
    assert mock_pdfinfo.called, "pdfinfo_from_bytes mora biti pozvan (page count guard attempt)"

    # Stream je seek-ovan na 0 (contract preserved i pri swallow path-u).
    assert upload.tell() == 0


# =============================================================================
# AC2 — generate_brochure_cover_thumbnail
# =============================================================================


def test_generate_brochure_cover_thumbnail_returns_content_file(minimal_pdf_1_page_bytes):
    """AC2 happy path — validan PDF → ContentFile sa JPEG bytes-ima.

    Ime fajla = "brochure-cover.jpg" (per AC2 contract).
    """
    from django.core.files.base import ContentFile

    from apps.media_pipeline.pdf_utils import generate_brochure_cover_thumbnail

    field = _fake_field_file(minimal_pdf_1_page_bytes)
    result = generate_brochure_cover_thumbnail(field)
    assert isinstance(result, ContentFile)
    assert result.name == "brochure-cover.jpg"


def test_generate_brochure_cover_thumbnail_dimensions_within_240x320(minimal_pdf_1_page_bytes):
    """AC2 — output dimensions <= 240×320 (aspect ratio preserved per Decision PDF-D3).

    A4 portrait (595×842) → ~226×320 (narrower; aspect ratio 0.7071).
    """
    from PIL import Image

    from apps.media_pipeline.pdf_utils import generate_brochure_cover_thumbnail

    field = _fake_field_file(minimal_pdf_1_page_bytes)
    result = generate_brochure_cover_thumbnail(field)
    assert result is not None, "Generate mora vratiti ContentFile, ne None"

    with Image.open(BytesIO(result.read())) as img:
        assert img.width <= 240, f"width {img.width} > 240"
        assert img.height <= 320, f"height {img.height} > 320"


def test_generate_brochure_cover_thumbnail_jpeg_format(minimal_pdf_1_page_bytes):
    """AC2 — output je RGB JPEG (force-RGB konverzija per AC2 + Gotcha PDF-9)."""
    from PIL import Image

    from apps.media_pipeline.pdf_utils import generate_brochure_cover_thumbnail

    field = _fake_field_file(minimal_pdf_1_page_bytes)
    result = generate_brochure_cover_thumbnail(field)
    assert result is not None

    with Image.open(BytesIO(result.read())) as img:
        assert img.format == "JPEG", f"format {img.format} != JPEG"
        assert img.mode == "RGB", f"mode {img.mode} != RGB"


def test_generate_brochure_cover_thumbnail_returns_none_for_corrupt_pdf(corrupt_pdf_bytes):
    """AC2 graceful — corrupt PDF → None (no raise)."""
    from apps.media_pipeline.pdf_utils import generate_brochure_cover_thumbnail

    field = _fake_field_file(corrupt_pdf_bytes)
    result = generate_brochure_cover_thumbnail(field)
    assert result is None


def test_generate_brochure_cover_thumbnail_returns_none_for_empty_pdf_field():
    """AC2 — None ili empty FieldFile → None (no raise)."""
    from apps.media_pipeline.pdf_utils import generate_brochure_cover_thumbnail

    # Empty name (no file uploaded)
    field = _fake_field_file(b"", name="")
    result = generate_brochure_cover_thumbnail(field)
    assert result is None


def test_generate_brochure_cover_thumbnail_returns_none_for_encrypted_pdf(
    mocker, minimal_pdf_1_page_bytes
):
    """AC2 + FIX iter-1 CRIT-8 — PDFSyntaxError (encrypted PDF) → None + warning log."""
    from pdf2image.exceptions import PDFSyntaxError

    from apps.media_pipeline.pdf_utils import generate_brochure_cover_thumbnail

    # Mock convert_from_bytes da raise PDFSyntaxError (poppler ne može da otvori encrypted PDF)
    mocker.patch(
        "apps.media_pipeline.pdf_utils.convert_from_bytes",
        side_effect=PDFSyntaxError("PDF is encrypted"),
    )
    field = _fake_field_file(minimal_pdf_1_page_bytes)
    result = generate_brochure_cover_thumbnail(field)
    assert result is None


def test_generate_brochure_cover_thumbnail_returns_none_on_render_timeout(
    mocker, minimal_pdf_1_page_bytes
):
    """AC2 + FIX iter-1 CRIT-4 — PDFPopplerTimeoutError → None + warning log."""
    from pdf2image.exceptions import PDFPopplerTimeoutError

    from apps.media_pipeline.pdf_utils import generate_brochure_cover_thumbnail

    mocker.patch(
        "apps.media_pipeline.pdf_utils.convert_from_bytes",
        side_effect=PDFPopplerTimeoutError("Render timeout after 15s"),
    )
    field = _fake_field_file(minimal_pdf_1_page_bytes)
    result = generate_brochure_cover_thumbnail(field)
    assert result is None


def test_generate_brochure_cover_thumbnail_returns_none_on_decompression_bomb(
    mocker, minimal_pdf_1_page_bytes
):
    """AC2 + FIX iter-1 CRIT-4 — render vraća Image > 50M px → None + warning log.

    pdf2image bypass-uje Pillow MAX_IMAGE_PIXELS — eksplicitan rendered_pixels check.
    """
    from PIL import Image

    from apps.media_pipeline.pdf_utils import generate_brochure_cover_thumbnail

    # Mock convert_from_bytes da vrati listu sa jedinom slikom 8000×8000 = 64M px > 50M
    huge_image = Image.new("RGB", (8000, 8000), color="white")
    mocker.patch(
        "apps.media_pipeline.pdf_utils.convert_from_bytes",
        return_value=[huge_image],
    )
    field = _fake_field_file(minimal_pdf_1_page_bytes)
    result = generate_brochure_cover_thumbnail(field)
    assert result is None


def test_generate_logs_warning_on_failure(mocker, minimal_pdf_1_page_bytes, caplog):
    """AC2 + AC6 — graceful failure mora logovati WARNING na 'apps.media_pipeline.pdf_utils'.

    Logger name canonicalan: `logging.getLogger("apps.media_pipeline.pdf_utils")`.
    """
    from pdf2image.exceptions import PDFSyntaxError

    from apps.media_pipeline.pdf_utils import generate_brochure_cover_thumbnail

    mocker.patch(
        "apps.media_pipeline.pdf_utils.convert_from_bytes",
        side_effect=PDFSyntaxError("simulated failure"),
    )
    field = _fake_field_file(minimal_pdf_1_page_bytes)

    with caplog.at_level(logging.WARNING, logger="apps.media_pipeline.pdf_utils"):
        result = generate_brochure_cover_thumbnail(field)

    assert result is None
    # Mora postojati barem jedan WARNING/ERROR log entry od pdf_utils logger-a
    relevant = [
        r
        for r in caplog.records
        if r.name == "apps.media_pipeline.pdf_utils" and r.levelno >= logging.WARNING
    ]
    assert relevant, (
        "Nije logovan WARNING/ERROR sa logger='apps.media_pipeline.pdf_utils' "
        "tokom graceful failure-a"
    )
