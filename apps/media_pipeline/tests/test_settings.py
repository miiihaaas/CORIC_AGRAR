"""Story 2.3 — settings contract smoke testovi za media pipeline + sorl-thumbnail.

Pokriva AC2 (interface contract section 3 — sorl-thumbnail settings keys added):
- THUMBNAIL_BACKEND: sorl base backend
- THUMBNAIL_KVSTORE: cached_db KVStore
- THUMBNAIL_QUALITY: 85 (default JPEG quality)
- THUMBNAIL_PREFIX: 'thumbnails/' (subdir u MEDIA_ROOT; FIX-7 rename iz THUMBNAIL_DIRNAME)
- THUMBNAIL_DEBUG: hardcoded False (FIX-3 / Security HIGH-2 — info-leak prevention)
- MEDIA_URL + MEDIA_ROOT: validne vrednosti za thumbnail generaciju

Test discipline:
- Bez Django setup zavisnosti (pytest-django ucitava settings preko fixture-a)
- Bez fixture file-system pisanja (čist setting reflection)

Refs:
- 2-3-image-pipeline-sa-sorl-thumbnail-responsive-srcset.md AC2
- 2-3-interface-contract.md section 3 settings_keys_added
- Story 2.3 Testing Notes section 9.1
"""

from __future__ import annotations

from pathlib import Path

from django.conf import settings


def test_thumbnail_backend_configured():
    """AC2: sorl-thumbnail koristi canonical ThumbnailBackend (NE custom subclass)."""
    assert settings.THUMBNAIL_BACKEND == "sorl.thumbnail.base.ThumbnailBackend", (
        f"THUMBNAIL_BACKEND očekivan 'sorl.thumbnail.base.ThumbnailBackend', "
        f"dobio: {settings.THUMBNAIL_BACKEND!r}"
    )


def test_thumbnail_kvstore_configured():
    """AC2: sorl-thumbnail koristi cached_db KVStore (Django cache + DB fallback).

    Decision: cached_db (NE memcached/redis) jer Story 2.3 ne uvodi external cache;
    LocMem cache + DB fallback je dovoljan za development + small-scale production.
    """
    assert (
        settings.THUMBNAIL_KVSTORE
        == "sorl.thumbnail.kvstores.cached_db_kvstore.KVStore"
    ), (
        f"THUMBNAIL_KVSTORE očekivan 'sorl.thumbnail.kvstores.cached_db_kvstore.KVStore', "
        f"dobio: {settings.THUMBNAIL_KVSTORE!r}"
    )


def test_thumbnail_quality_85():
    """AC2: default JPEG quality je 85 (balans bandwidth ↔ vizualni kvalitet).

    85 je industry standard za web JPEG (browser-perceptible kvalitet razlika preko 85
    je marginalna, file size kontinualno raste).
    """
    assert settings.THUMBNAIL_QUALITY == 85, (
        f"THUMBNAIL_QUALITY očekivan 85, dobio: {settings.THUMBNAIL_QUALITY!r}"
    )


def test_thumbnail_prefix_is_thumbnails_slash():
    """AC2 + FIX-7: kanonski sorl setting je THUMBNAIL_PREFIX (sa trailing slash).

    Prethodna verzija interface contract-a je referencirala THUMBNAIL_DIRNAME što NIJE
    sorl-thumbnail setting key (no-op assignment). FIX-7 rename + Decision MP-D7.
    """
    assert settings.THUMBNAIL_PREFIX == "thumbnails/", (
        f"THUMBNAIL_PREFIX očekivan 'thumbnails/' (sa trailing slash), "
        f"dobio: {settings.THUMBNAIL_PREFIX!r}"
    )


def test_thumbnail_debug_is_false_in_base():
    """FIX-3 (Security HIGH-2): THUMBNAIL_DEBUG MORA biti hardcoded False.

    Razlog: sorl-thumbnail u template render-u vraća stack trace (Pillow verzija +
    MEDIA_ROOT putanja) kad je THUMBNAIL_DEBUG=True — info leak rizik ako DEBUG=True
    nepovoljno curne u staging/production. Drživo False bez obzira na DEBUG.
    Dev investigation override: u development.py eksplicitno postaviti True ako treba.
    """
    assert settings.THUMBNAIL_DEBUG is False, (
        f"THUMBNAIL_DEBUG MORA biti hardcoded False (Security HIGH-2 — info-leak guard); "
        f"dobio: {settings.THUMBNAIL_DEBUG!r}"
    )


def test_image_max_pixels_capped_at_50m():
    """Security HIGH-1 (FIX-2): Image.MAX_IMAGE_PIXELS lowered from Pillow default ~89M to 50M.

    Caps Pillow decompression bomb tolerance at 50M pixels (8K source has 33M — comfortable).
    Set on module import side-effect u apps/media_pipeline/utils.py — verifikujemo da je
    veza aktivna posle import-a.
    """
    # Force module load — Image.MAX_IMAGE_PIXELS is set at import time
    from apps.media_pipeline import utils  # noqa: F401
    from PIL import Image

    assert Image.MAX_IMAGE_PIXELS == 50_000_000, (
        f"Image.MAX_IMAGE_PIXELS expected 50M, got {Image.MAX_IMAGE_PIXELS}"
    )


def test_data_upload_max_memory_size_aligned_with_helper():
    """Security MEDIUM-1 (FIX-4): DATA_UPLOAD_MAX_MEMORY_SIZE = 11MB (1MB buffer iznad 10MB helper-a).

    Prevents Django from accepting larger POST bodies than the validate_image_mime helper allows.
    11MB buffer dozvoljava form metadata + 10MB image bez Django RequestDataTooBig-a.
    """
    assert settings.DATA_UPLOAD_MAX_MEMORY_SIZE == 11 * 1024 * 1024, (
        f"DATA_UPLOAD_MAX_MEMORY_SIZE expected 11MB, got {settings.DATA_UPLOAD_MAX_MEMORY_SIZE}"
    )


def test_file_upload_max_memory_size_matches_helper():
    """Security MEDIUM-1 (FIX-4): FILE_UPLOAD_MAX_MEMORY_SIZE = 10MB (matches MAX_UPLOAD_SIZE_BYTES).

    Ako se ova dva limita razdvoje, Django bi mogao spool-ovati > 10MB upload na disk
    pre nego što validate_image_mime helper raise-uje ValidationError → disk DoS vektor.
    """
    from apps.media_pipeline.utils import MAX_UPLOAD_SIZE_BYTES

    assert settings.FILE_UPLOAD_MAX_MEMORY_SIZE == MAX_UPLOAD_SIZE_BYTES, (
        f"FILE_UPLOAD_MAX_MEMORY_SIZE ({settings.FILE_UPLOAD_MAX_MEMORY_SIZE}) "
        f"must match MAX_UPLOAD_SIZE_BYTES ({MAX_UPLOAD_SIZE_BYTES})"
    )


def test_media_url_and_root_set():
    """AC2: MEDIA_URL je '/media/' (leading slash zbog i18n_patterns) + MEDIA_ROOT validan path.

    MEDIA_URL bez leading slash bi izazvao i18n locale prefix redirect (`/sr/media/...` → 404).
    MEDIA_ROOT mora biti Path/str — sorl-thumbnail koristi FileSystemStorage default location.
    """
    assert settings.MEDIA_URL == "/media/", (
        f"MEDIA_URL očekivan '/media/' (sa leading slash); dobio: {settings.MEDIA_URL!r}"
    )
    assert settings.MEDIA_ROOT, "MEDIA_ROOT ne sme biti prazan string"
    # MEDIA_ROOT može biti Path ili str (Django dozvoljava oba); konvertujemo u Path za check
    media_root = Path(settings.MEDIA_ROOT)
    # U test okruženju MEDIA_ROOT može biti override-an na tmp_path; sanity check je samo
    # da je validna apsolutna putanja (NE relativna), ne da postoji.
    assert media_root.is_absolute(), (
        f"MEDIA_ROOT mora biti apsolutna putanja; dobio: {media_root}"
    )
