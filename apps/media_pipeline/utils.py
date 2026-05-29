"""Media pipeline utility helpers — image MIME validacija + Pillow signature check.

Story 2.3 (Epic 2) utility-only deliverable. NEMA modela. NEMA admin.
Konzumiran od Epic 8 admin forme (Story 8.4/8.6) i future contact forms (Epic 4).

Per project-context.md anti-pattern: File upload bez double-check —
ImageField/FileField u Django default validate file extension samo (`.jpg`, `.png`),
NE MIME signature. Treba dvostruka provera:
  1. python-magic na prvih 2048 bytes — detect real MIME iz signature
  2. PIL Image.verify() — verify image structure integrity (nije corrupt)

System dependency: libmagic1 (Dockerfile per Story 1.3) — bez nje python-magic
importuje ali magic.from_buffer() raise-uje na svakom pozivu.
"""

from __future__ import annotations

import warnings
from typing import Iterable

import magic
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from django.utils.translation import gettext_lazy as _
from PIL import Image, UnidentifiedImageError

ALLOWED_IMAGE_MIME_TYPES: tuple[str, ...] = (
    "image/jpeg",
    "image/png",
    "image/webp",
)
MIME_SNIFF_BYTES: int = 2048
MAX_UPLOAD_SIZE_BYTES: int = 10 * 1024 * 1024

# FIX-2 (Security HIGH-1) — Decompression-bomb DoS guard.
# Pillow default je ~89M px (samo WARNING). Smanjujemo na 50MP što je dovoljno za
# 8K source slike (7680×4320 = 33MP) i blokira "1 GB px" payload-e koji bi OOM-ovali
# Gunicorn worker pri thumbnail generaciji.
Image.MAX_IMAGE_PIXELS = 50_000_000


def validate_image_mime(
    upload: UploadedFile | None,
    *,
    allowed_mimes: Iterable[str] = ALLOWED_IMAGE_MIME_TYPES,
    max_size_bytes: int = MAX_UPLOAD_SIZE_BYTES,
) -> None:
    """Double-check da je upload validna slika kroz MIME signature + Pillow verify + size limit.

    Raise-uje ValidationError sa locale-aware porukom ako:
    - File je prazan (0 bytes) ili upload is None
    - File je veci od max_size_bytes (DoS guard; default 10MB)
    - python-magic detect-uje MIME koji NIJE u allowed_mimes
    - PIL Image.verify() raise-uje UnidentifiedImageError ili SyntaxError

    Side-effect: upload.seek(0) na ulazu i izlazu (caller nije obavezan da reset-uje).
    """
    if upload is None or not upload.size:
        raise ValidationError(_("Slika je prazna ili nije priložena."))

    if upload.size > max_size_bytes:
        raise ValidationError(
            _(
                "Slika je veća od %(limit)d MB. Maksimalna dozvoljena veličina je %(limit)d MB."
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
            _("Nedozvoljen tip slike: %(mime)s. Dozvoljeni tipovi: %(allowed)s.")
            % {
                "mime": detected_mime,
                "allowed": ", ".join(allowed_tuple),
            }
        )

    # FIX-2 (Security HIGH-1 + LOW-2): `with Image.open(...)` zatvara FD na izlazu,
    # `warnings.catch_warnings` escalates DecompressionBombWarning u error (default je
    # samo warning), `DecompressionBombError` (subclass of ValueError) explicit u except
    # da se ne propagira kao 500.
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(upload) as img:
                img.verify()
    except (
        UnidentifiedImageError,
        SyntaxError,
        OSError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ) as exc:
        raise ValidationError(_("Slika je oštećena ili nije validan format.")) from exc
    finally:
        upload.seek(0)
