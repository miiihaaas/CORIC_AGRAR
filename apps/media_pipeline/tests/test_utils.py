"""Story 2.3 — apps/media_pipeline/utils.py validate_image_mime() testovi (RED phase TDD).

Pokriva AC3 + AC5 + AC8 — `validate_image_mime()` helper sa python-magic + Pillow
Image.verify() double-check pattern (per project-context.md § Anti-pattern: File upload
bez double-check).

Test scope (11 scenarija):
- 3 pozitivna: validan JPEG, PNG, WebP
- 4 negativna (MIME mismatch): PDF, EXE, corrupt JPEG, empty
- 4 edge case / negativna: None upload, oversize, size=None streaming, seek-back side-effect

Naming convention: srpska latinica + engleski code identifiers.
TEA RED phase: svi testovi MORAJU pasti (ImportError) dok Dev ne kreira apps.media_pipeline.utils.

Pokrenuti kroz Docker (libmagic SEGFAULT na Windows host-u per Decision MP-D6):
    docker compose -f compose/local.yml run --rm django uv run pytest apps/media_pipeline/tests/test_utils.py -v

Refs:
- 2-3-image-pipeline-sa-sorl-thumbnail-responsive-srcset.md (story spec, AC3 + AC5)
- 2-3-interface-contract.md (TEA canonical contract — Dev MUST satisfy)
- project-context.md § Anti-pattern: File upload bez double-check + § Security must-haves
"""

from __future__ import annotations

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile


# =============================================================================
# AC3 / AC5 — Pozitivni testovi: validate_image_mime PASS za validne tipove
# =============================================================================


def test_validate_image_mime_accepts_valid_jpeg(valid_jpeg_bytes):
    """AC3/AC5: Validan JPEG sa SOI markerom passes MIME + Image.verify() check.

    `b"\\xff\\xd8\\xff\\xe0..."` SOI marker → python-magic detect-uje image/jpeg →
    Image.verify() success → helper return-uje None (no ValidationError).
    """
    from apps.media_pipeline.utils import validate_image_mime

    upload = SimpleUploadedFile("test.jpg", valid_jpeg_bytes, content_type="image/jpeg")

    # Ne raise-uje — pozitivan path
    result = validate_image_mime(upload)
    assert result is None, "validate_image_mime mora vratiti None za validan JPEG"


def test_validate_image_mime_accepts_valid_png(valid_png_bytes):
    """AC3/AC5: Validan PNG passes MIME + Image.verify() check.

    Pillow-generated PNG bytes → python-magic detect-uje image/png → PASS.
    """
    from apps.media_pipeline.utils import validate_image_mime

    upload = SimpleUploadedFile("test.png", valid_png_bytes, content_type="image/png")

    result = validate_image_mime(upload)
    assert result is None, "validate_image_mime mora vratiti None za validan PNG"


def test_validate_image_mime_accepts_valid_webp(valid_webp_bytes):
    """AC3/AC5: Validan WebP (Pillow-generated, VP8 lossless) passes oba check-a.

    Hardcoded `b"RIFF...WEBP"` stub NIJE validan — Image.verify() raise-uje
    UnidentifiedImageError. Pillow runtime generacija je jedini deterministički način.
    """
    from apps.media_pipeline.utils import validate_image_mime

    upload = SimpleUploadedFile(
        "test.webp", valid_webp_bytes, content_type="image/webp"
    )

    result = validate_image_mime(upload)
    assert result is None, "validate_image_mime mora vratiti None za validan WebP"


# =============================================================================
# AC5 — Negativni testovi: validate_image_mime REJECT za nedozvoljene tipove
# =============================================================================


def test_validate_image_mime_rejects_pdf_as_image(pdf_as_image_bytes):
    """AC5: PDF magic bytes sa fake `.jpg` extension MUST raise ValidationError.

    Attacker scenario: Editor upload-uje malware.pdf preimenovan u image.jpg.
    Django ImageField validira extension SAMO; python-magic detect-uje real
    `application/pdf` MIME → helper raise-uje ValidationError sa porukom
    `_("Nedozvoljen tip slike: %(mime)s. Dozvoljeni tipovi: %(allowed)s.")`.
    """
    from apps.media_pipeline.utils import validate_image_mime

    upload = SimpleUploadedFile(
        "malware.jpg", pdf_as_image_bytes, content_type="image/jpeg"
    )

    with pytest.raises(ValidationError) as exc_info:
        validate_image_mime(upload)

    # ValidationError može sadržati lokalizovanu poruku — substring check je dovoljan
    assert "Nedozvoljen tip slike" in str(exc_info.value) or "application/pdf" in str(
        exc_info.value
    ), f"ValidationError mora pomenuti nedozvoljen MIME; dobio: {exc_info.value!r}"


def test_validate_image_mime_rejects_executable_bytes():
    """AC5: EXE magic bytes (`MZ\\x90\\x00`) sa fake `.jpg` extension MUST raise ValidationError.

    Attacker scenario: Windows PE32 executable preimenovan u image.jpg.
    python-magic detect-uje `application/x-dosexec` (ili sličan) → ValidationError.
    """
    from apps.media_pipeline.utils import validate_image_mime

    exe_bytes = (
        b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff\x00\x00" + b"\x00" * 512
    )
    upload = SimpleUploadedFile("malware.jpg", exe_bytes, content_type="image/jpeg")

    with pytest.raises(ValidationError):
        validate_image_mime(upload)


def test_validate_image_mime_rejects_corrupt_jpeg(corrupt_jpeg_bytes):
    """AC5: Validan JPEG SOI marker + truncated body → passes MIME, FAIL Image.verify().

    python-magic detect-uje `image/jpeg` (SOI marker zadovoljava signature check),
    ali PIL Image.verify() raise-uje UnidentifiedImageError/OSError zbog truncated
    Huffman tabele bez EOI markera → helper konvertuje u ValidationError sa porukom
    `_("Slika je oštećena ili nije validan format.")`.

    Ovaj test verifikuje da MIME-only check NIJE dovoljan — Pillow Image.verify()
    je drugi nezavisni check (double-check pattern per project-context.md).
    """
    from apps.media_pipeline.utils import validate_image_mime

    upload = SimpleUploadedFile(
        "corrupt.jpg", corrupt_jpeg_bytes, content_type="image/jpeg"
    )

    with pytest.raises(ValidationError) as exc_info:
        validate_image_mime(upload)

    assert "oštećena" in str(exc_info.value) or "nije validan" in str(exc_info.value), (
        f"ValidationError mora pomenuti corrupt/oštećena sliku; dobio: {exc_info.value!r}"
    )


def test_validate_image_mime_rejects_empty_upload():
    """AC5: Prazan upload (size=0) → ValidationError pre MIME check-a.

    Empty file ne sme da dođe do magic.from_buffer() — early guard.
    Poruka: `_("Slika je prazna ili nije priložena.")`
    """
    from apps.media_pipeline.utils import validate_image_mime

    upload = SimpleUploadedFile("empty.jpg", b"", content_type="image/jpeg")

    with pytest.raises(ValidationError) as exc_info:
        validate_image_mime(upload)

    assert "prazna" in str(exc_info.value) or "nije priložena" in str(exc_info.value), (
        f"ValidationError mora pomenuti prazan upload; dobio: {exc_info.value!r}"
    )


def test_validate_image_mime_rejects_none_upload():
    """AC5: `validate_image_mime(None)` → ValidationError, NE AttributeError.

    Graceful guard: helper hvata None upload pre nego što pokuša `upload.size` pristup.
    Ovo je critical za form `clean_<field>()` integration gde `cleaned_data.get("field")`
    može vratiti None ako Editor ne priloži fajl.
    """
    from apps.media_pipeline.utils import validate_image_mime

    with pytest.raises(ValidationError) as exc_info:
        validate_image_mime(None)

    assert "prazna" in str(exc_info.value) or "nije priložena" in str(exc_info.value), (
        f"ValidationError mora gracefully obraditi None; dobio: {exc_info.value!r}"
    )


def test_validate_image_mime_rejects_oversize_upload(valid_jpeg_bytes):
    """AC5: Upload veći od MAX_UPLOAD_SIZE_BYTES (10 MB) → ValidationError.

    DoS guard per project-context.md § Security must-haves: file size validation na upload
    boundary. 50MB+ JPEG → 3× thumbnail gen u Pillow → OOM kill u Gunicorn worker-u.

    Mock-ujemo `upload.size` direktno (ne kreiramo stvarno 11MB blob da uštedimo memoriju).
    """
    from apps.media_pipeline.utils import MAX_UPLOAD_SIZE_BYTES, validate_image_mime

    upload = SimpleUploadedFile("huge.jpg", valid_jpeg_bytes, content_type="image/jpeg")
    # Simuliraj 11MB upload bez stvarnog allocate-a
    upload.size = MAX_UPLOAD_SIZE_BYTES + 1

    with pytest.raises(ValidationError) as exc_info:
        validate_image_mime(upload)

    assert "veća" in str(exc_info.value) or "MB" in str(exc_info.value), (
        f"ValidationError mora pomenuti veličinu i MB limit; dobio: {exc_info.value!r}"
    )


def test_validate_image_mime_handles_none_size_gracefully(valid_jpeg_bytes):
    """AC5 edge case (IMP-A2): UploadedFile sa `.size = None` (streaming) → ValidationError.

    TemporaryUploadedFile tokom streaming-a velikog upload-a može vratiti None za .size
    dok upload nije završen. `upload.size == 0` PROPUŠTA None case → kasnije
    `upload.size > max_size_bytes` raise-uje TypeError.

    Helper MORA koristiti `not upload.size` truthy check (hvata oba: 0 i None).
    Očekivan output: ValidationError sa porukom `_("Slika je prazna...")`, NE TypeError.
    """
    from apps.media_pipeline.utils import validate_image_mime

    upload = SimpleUploadedFile(
        "streaming.jpg", valid_jpeg_bytes, content_type="image/jpeg"
    )
    # Streaming scenario: size još nije resolved
    upload.size = None

    with pytest.raises(ValidationError) as exc_info:
        validate_image_mime(upload)

    # FIX-6 (TEA BUG#9): assertion mora razlikovati "prazna/None" putanju od
    # "oversized" putanje. Bez ovoga, test bi prošao i da helper greškom raise-uje
    # oversize error na None size (`None > max_bytes` → TypeError, NE poruka).
    assert "prazna" in str(exc_info.value) or "nije priložena" in str(exc_info.value), (
        f"None size mora gađati 'prazna/nije priložena' putanju "
        f"(NE oversize); dobio: {exc_info.value!r}"
    )


def test_validate_image_mime_rejects_decompression_bomb(decompression_bomb_bytes):
    """AC5 Security HIGH-1 (FIX-2 regression guard): 8000×8000 PNG (64M pixels)
    exceeds Image.MAX_IMAGE_PIXELS=50M.

    Pillow's DecompressionBombWarning je escalated u error kroz
    `warnings.simplefilter("error", Image.DecompressionBombWarning)` u
    validate_image_mime, a `DecompressionBombError` je explicit u except —
    oba pathovi rezultuju ValidationError sa porukom 'oštećena/nije validan'.

    Bez ovog regression guard-a, future refactor koji ukloni `Image.MAX_IMAGE_PIXELS = 50_000_000`
    iz utils.py (vraćanje na Pillow ~89M default) bio bi tiho propušten.
    """
    from apps.media_pipeline.utils import validate_image_mime

    upload = SimpleUploadedFile(
        "huge.png",
        decompression_bomb_bytes,
        content_type="image/png",
    )
    with pytest.raises(ValidationError) as exc_info:
        validate_image_mime(upload)

    assert "oštećena" in str(exc_info.value) or "nije validan" in str(exc_info.value), (
        f"Decompression bomb mora biti odbijen sa 'oštećena/nije validan' porukom; "
        f"dobio: {exc_info.value!r}"
    )


def test_validate_image_mime_seeks_back_to_zero_after_validation(valid_jpeg_bytes):
    """AC3 side-effect contract: posle validate_image_mime, upload.tell() == 0.

    Pillow Image.verify() troši stream do EOF; bez explicit seek(0) u helper-u, caller
    form pokušaj save-a `upload` na disk će ga snimiti prazan (cursor na kraju fajla).

    Helper MORA `upload.seek(0)` u finally block-u Pillow verify-a (Gotcha MP-6).
    """
    from apps.media_pipeline.utils import validate_image_mime

    upload = SimpleUploadedFile("test.jpg", valid_jpeg_bytes, content_type="image/jpeg")
    validate_image_mime(upload)

    assert upload.tell() == 0, (
        f"upload.tell() mora biti 0 posle validate_image_mime (Gotcha MP-6 — Image.verify "
        f"troši stream, seek(0) u finally), dobio: {upload.tell()}"
    )
