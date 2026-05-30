"""Story 2.3 — pytest fixtures za media_pipeline testove (TEA RED phase).

Pillow-generated image bytes (PNG/WebP) umesto hardcoded stub bytes-a.
Razlog: PIL.Image.verify() raise-uje UnidentifiedImageError na ne-validnim
hardcoded `b"RIFF\\x00\\x00\\x00\\x00WEBP"` stub-ovima — moramo generisati
realan binary kroz Pillow runtime da bi test bio meaningful.

Per project-context.md § Mock policy:
- NEMA mock-a Django ORM / PostgreSQL
- NEMA mock-a python-magic / Pillow / sorl-thumbnail (real binaries)
- Mock-uje se SAMO `MEDIA_ROOT` kroz monkeypatch da testovi pišu u tmp_path

Pokrenuti kroz Docker (libmagic SEGFAULT na Windows host-u):
    docker compose -f compose/local.yml run --rm django uv run pytest apps/media_pipeline/tests/ -v
"""

from __future__ import annotations

from io import BytesIO

import pytest
from PIL import Image


@pytest.fixture
def temp_media_root(tmp_path, settings):
    """Override MEDIA_ROOT na pytest tmp_path da testovi ne pišu u repo media/ dir.

    Side-effect cleanup: pytest tmp_path se automatski briše posle test session-a.

    Cache invalidation: tri sloja cache-a se moraju invalidirati pre svakog testa:
    1. `FileSystemStorage.base_location` je `@cached_property` — pamti prvu MEDIA_ROOT
    2. Django `storages` handler cache-uje storage instance po alias-u
    3. sorl-thumbnail `Storage` LazyObject pamti `_wrapped` posle prvog access-a
    """
    from django.core.files.storage import default_storage, storages
    from django.utils.functional import empty

    def _invalidate():
        # default_storage je DefaultStorage LazyObject — moramo reset _wrapped da
        # pri sledećem access-u ponovo učita iz storages["default"]
        default_storage._wrapped = empty
        if hasattr(storages, "_storages"):
            storages._storages.clear()
        try:
            from sorl.thumbnail.default import kvstore as sorl_kvstore
            from sorl.thumbnail.default import storage as sorl_storage

            sorl_storage._wrapped = empty
            sorl_kvstore._wrapped = empty
        except ImportError:
            pass
        # Django cache (LocMem) drži sorl-thumbnail cached_db KVStore entries —
        # između testova MEDIA_ROOT se menja a cache entry-ji bi vratili stale URL-ove
        from django.core.cache import cache

        cache.clear()

    _invalidate()
    settings.MEDIA_ROOT = str(tmp_path)
    _invalidate()
    yield tmp_path
    _invalidate()


@pytest.fixture
def valid_jpeg_bytes():
    """Pillow-generated validan JPEG (RGB 10×10 red, quality=85).

    REVIEW FIX MP-R2: prethodni 62-byte hardcoded minimal JPEG (SOI + JFIF + truncated DQT
    + SOF0 + 2× DHT + SOS + 0x7F + EOI) NIJE prošao `Image.verify()` (UnidentifiedImageError).
    Empirijski potvrđeno: DQT header je deklarisao 67 byte payload ali je truncated na 14
    bytes pre nego što je sledeći marker (SOF0) počeo — invalidan DQT segment.

    Hardcoded minimal JPEG generalno NIJE pouzdan u Pillow ekosistemu — `Image.verify()`
    striktno parsira sve segmente. Pillow runtime generacija je jedini deterministički način
    da se dobije validan JPEG koji passes oba check-a u `validate_image_mime()`.

    NIJE za thumbnail size assertion (samo ~600 bytes na 10×10 source-u, manji od svakog
    target width-a) — za size asserciju vidi `realistic_source_image_bytes` fixture.
    """
    img = Image.new("RGB", (10, 10), color="red")
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


@pytest.fixture
def valid_png_bytes():
    """Pillow-generated PNG (RGB 10×10, solid red).

    Passes python-magic `image/png` detect + PIL Image.verify().
    Korišćen za PNG → JPEG konverziju test (AC6 thumbnail format check).
    """
    img = Image.new("RGB", (10, 10), color="red")
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def valid_png_with_alpha_bytes():
    """Pillow-generated PNG (RGBA 10×10, alpha=128) — semi-transparent red.

    Korišćen za format='PNG' kwarg test (AC10) — verifikuje da output thumbnail
    preserve-uje alpha channel kad caller eksplicitno prosledi format='PNG'.
    """
    img = Image.new("RGBA", (10, 10), color=(255, 0, 0, 128))
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def large_png_with_alpha_bytes():
    """Pillow-generated PNG (RGBA 1000×800, alpha=128) — dovoljno velika za sorl downscale.

    FIX-5 (TEA BUG#2 + #3): 10×10 source NE prolazi kroz sorl downscale na 400/800/1600w
    (sorl ne upscale-uje). Test AC10 mora da verifikuje stvarno generisan thumbnail mod
    je RGBA/LA — za to source mora biti veći od najmanjeg target-a.

    1000×800 prevazilazi 400w → sorl generiše barem 400w varijantu sa stvarnom downscale
    operacijom. Solid color (alpha=128) → ne treba realistic noise jer test gleda format
    integrity, ne file size.
    """
    img = Image.new("RGBA", (1000, 800), color=(120, 80, 200, 128))
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def valid_webp_bytes():
    """Pillow-generated WebP (RGB 10×10, solid red) — validan VP8 lossless.

    Hardcoded `b"RIFF\\x00\\x00\\x00\\x00WEBP"` stub NIJE validan — Image.verify()
    raise-uje UnidentifiedImageError. Pillow runtime generacija je jedini deterministički
    način da se dobije validan WebP koji passes oba check-a u validate_image_mime().
    """
    img = Image.new("RGB", (10, 10), color="red")
    buf = BytesIO()
    img.save(buf, format="WEBP")
    return buf.getvalue()


@pytest.fixture
def corrupt_jpeg_bytes():
    """JPEG sa validnim SOI markerom + truncated body — passes libmagic, FAIL Image.verify().

    Konstrukcija: validan SOI (`FF D8 FF E0`) + JFIF header + truncated DCT scan
    (presečen pre Huffman tabele, bez SOS markera, bez EOI markera).
    python-magic detect-uje `image/jpeg` PASS prvi check; PIL Image.verify() raise-uje
    OSError ili UnidentifiedImageError.

    Test scenario AC5: validate_image_mime mora hvatati corrupted-but-MIME-valid uploads.
    """
    return (
        b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
        b"\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07"
        b"\x00\x00\x00\x00CORRUPT_TRUNCATED_BODY_NO_EOI_MARKER"
    )


@pytest.fixture
def pdf_as_image_bytes():
    """PDF magic bytes (`%PDF-1.4`) sa `.jpg` extension (faked).

    Attacker upload pattern — Editor upload-uje malware.pdf preimenovan u image.jpg.
    Django ImageField validira extension SAMO; python-magic detect-uje real
    `application/pdf` MIME → validate_image_mime raise-uje ValidationError.

    Test scenario AC5 — kritičan security test.
    """
    return (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 100 100] >>\nendobj\n"
        b"xref\n0 4\n0000000000 65535 f\ntrailer\n<< /Root 1 0 R /Size 4 >>\n"
        b"%%EOF\n"
    )


@pytest.fixture
def decompression_bomb_bytes():
    """
    Pillow image declaring dimensions > Image.MAX_IMAGE_PIXELS (50M).
    8000×8000 = 64M pixels — triggers DecompressionBombWarning (escalated to error per FIX-2).
    Used by test_validate_image_mime_rejects_decompression_bomb to verify Security HIGH-1 guard.

    Note: optimized PNG of 64M solid-color pixels je svega ~30KB na disku (well below
    10MB MAX_UPLOAD_SIZE_BYTES), pa size guard NEĆE early-out — bomb mora biti uhvaćen
    eksplicitno od strane DecompressionBomb guard-a unutar Image.verify() path-a.
    """
    buf = BytesIO()
    img = Image.new("RGB", (8000, 8000), color="white")
    img.save(buf, format="PNG", optimize=False)
    return buf.getvalue()


@pytest.fixture
def realistic_source_image_bytes():
    """Realistic JPEG (2400×1800 ~4.3MP, high-entropy noise, quality=95) za thumbnail size assertion.

    AC6 traži da generated 400w/800w/1600w thumbnails MUST biti smaller than source —
    moguće je verifikovati SAMO kad source ima realne dimenzije i visok entropy
    (≥ 2000px wide, complex content). 62-byte minimalan JPEG (valid_jpeg_bytes) je
    NEVALIDAN za ovaj test.

    Solid-color slike JPEG-uju u ~5-10KB čak i na 2400×1800 (DCT high-compression za
    uniform polje), pa bi thumbnail mogao biti VEĆI od source-a zbog header overhead-a.

    Rešenje (IMP-A3): Image.effect_noise generiše visoko-entropijski noise pattern koji
    NE kompresuje dobro (sigma=64 → ~500KB-1MB JPEG @ quality=95) — garantuje da su sve
    tri varijante 400/800/1600 strogo manje u file bytes.

    `effect_noise` vraća "L" (grayscale) mode — convert-ujemo u "RGB" radi konzistentnosti
    sa JPEG output-om (libjpeg interno YCbCr, RGB standardni input).
    """
    img = Image.effect_noise((2400, 1800), sigma=64)
    img = img.convert("RGB")
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=95)
    return buf.getvalue()


# =============================================================================
# Story 2.4 — PDF fixtures (TEA RED phase EXTEND)
# =============================================================================
#
# Per Decision PDF-D5: minimal raw PDF struct kao pre-defined bytes konstanta
# (mirror Story 2.3 valid_jpeg_bytes 62-byte pattern). NEMA reportlab dep, NEMA
# checked-in binary fixture fajla.
#
# Mihas MORA pokrenuti kroz Docker (poppler-utils + libmagic system deps):
#     docker compose -f compose/local.yml run --rm django uv run pytest \
#         apps/media_pipeline/tests/test_pdf_utils.py \
#         apps/media_pipeline/tests/test_signals.py \
#         apps/media_pipeline/tests/test_apps_ready.py -v


# Minimal validan 1-page PDF struct (PDF 1.4) sa "Hello PDF!" text-om.
# Pdf2image convert_from_bytes() može render-ovati prvu stranu kao ~595×842 PIL Image.
# Python-magic detect-uje `application/pdf` MIME iz `%PDF-` magic bytes.
_MINIMAL_PDF_1_PAGE = (
    b"%PDF-1.4\n"
    b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
    b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
    b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
    b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n"
    b"4 0 obj\n<< /Length 44 >>\nstream\nBT /F1 24 Tf 100 700 Td (Hello PDF!) Tj ET\nendstream\nendobj\n"
    b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
    b"xref\n0 6\n0000000000 65535 f\n"
    b"0000000009 00000 n\n0000000058 00000 n\n0000000111 00000 n\n"
    b"0000000212 00000 n\n0000000293 00000 n\n"
    b"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n358\n%%EOF\n"
)


@pytest.fixture
def minimal_pdf_1_page_bytes():
    """Minimal 1-page validan PDF struct (per Decision PDF-D5).

    Passes python-magic `application/pdf` MIME detect + pdf2image convert_from_bytes()
    render. Korišćen za AC1 happy path (`test_validate_pdf_accepts_valid_pdf`) i AC2
    happy path (`test_generate_brochure_cover_thumbnail_returns_content_file`).
    """
    return _MINIMAL_PDF_1_PAGE


@pytest.fixture
def corrupt_pdf_bytes():
    """Random bytes pretvarajući se da je PDF — NIJE validan PDF struct.

    Bez `%PDF-` magic bytes na početku → python-magic detect-uje `application/octet-stream`
    ili sl., NE `application/pdf`. Test scenario AC1 (rejection) i AC2 (graceful fail).
    """
    return b"NOT_A_PDF_AT_ALL_JUST_RANDOM_BYTES"


@pytest.fixture
def empty_pdf_bytes():
    """0-byte upload — guard za empty/missing file (AC1)."""
    return b""


@pytest.fixture
def oversized_pdf_bytes():
    """Validan PDF struct + padding stream > 10 MB (size guard test AC1).

    FIX iter-1 CRIT-1: MAX_PDF_UPLOAD_SIZE_BYTES = 10 MB. Test mora upload size > 10 MB.
    Generisemo minimal PDF + padding 11 MB raw bytes posle xref (Pillow ignoruje, poppler
    fails ali nas ne zanima render — size check je prvi).
    """
    padding = b"X" * (11 * 1024 * 1024)
    return _MINIMAL_PDF_1_PAGE + b"\n% PADDING\n" + padding


@pytest.fixture
def high_page_count_pdf_bytes():
    """PDF struct sa /Count > 200 stranica (page count guard test AC1, FIX iter-1 CRIT-4).

    Generišemo PDF gde /Pages /Kids lista referencira 201 page objekat. Realno renderovanje
    NIJE bitno za test — pdfinfo_from_bytes čita SAMO metadata (Pages count).

    NOTE: Ako pdfinfo ne uspe da parsira (zbog truncated struct ili sl), `validate_pdf_mime`
    swallow-uje exception i defers to render. Test mora staviti pdfinfo-parseable struct
    sa /Count 201 — koristimo realan /Kids array sa 201 reference iako su objekti sami
    nepostojeći (pdfinfo gleda samo /Count int).
    """
    # Generišemo /Kids sa 201 reference. Sami page objekti su prazni (poppler render
    # bi pukao ali nas zanima pdfinfo metadata extract).
    kids_refs = " ".join(f"{i} 0 R" for i in range(3, 3 + 201))
    pdf = (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [" + kids_refs.encode() + b"] /Count 201 >>\nendobj\n"
    )
    # Dodaj 201 minimal page objekata (3..203)
    for i in range(3, 3 + 201):
        pdf += (
            f"{i} 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n".encode()
        )
    pdf += b"xref\n0 1\n0000000000 65535 f\ntrailer\n<< /Size 1 /Root 1 0 R >>\nstartxref\n9\n%%EOF\n"
    return pdf
