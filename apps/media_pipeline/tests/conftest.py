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
