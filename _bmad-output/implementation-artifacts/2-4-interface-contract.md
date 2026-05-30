---
story-id: "2.4"
story-key: 2-4-pdf-cover-thumbnail-generator
title: Interface Contract — PDF Cover-thumbnail Generator (pdf_utils + signals + ready hook)
status: contract
created: 2026-05-30
last_modified: 2026-05-30
author: TEA (RED phase)
---

# Story 2.4 — Interface Contract

Ovaj dokument je kanonska specifikacija ugovora za sve artifakte Story 2.4. TEA RED-phase
test-suite (`apps/media_pipeline/tests/test_pdf_utils.py`, `test_signals.py`, `test_apps_ready.py`,
proširenje `apps/media_pipeline/tests/conftest.py`) direktno enkodira asercije definisane ovde.
Dev MUST satisfy ovaj ugovor da bi Story 2.4 prešla u GREEN.

Story 2.4 **proširuje** Story 2.3 `apps/media_pipeline/` utility app sa:

1. `apps/media_pipeline/pdf_utils.py` — `validate_pdf_mime()` + `generate_brochure_cover_thumbnail()`
2. `apps/media_pipeline/signals.py` — `handle_brochure_post_save()` post_save handler
3. `apps/media_pipeline/apps.py` — Edit: dodavanje `MediaPipelineConfig.ready()` hook-a koji
   wire-uje signal kroz `apps.get_model("products", "ProductBrochure")` kasnu resoluciju

App boundaries (Story 2.3 AC8 + Story 2.4 AC9): `apps.media_pipeline` **NE SME uvoziti
`apps.products` ni `apps.brands`** direktno — sva cross-app resolucija ide kroz string-based
`apps.get_model()` registry lookup.

---

## 1. Artifact inventory

### 1.1 Novi fajlovi (production code — Dev deliverable u GREEN phase)

| Path | Purpose |
|---|---|
| `apps/media_pipeline/pdf_utils.py` | `validate_pdf_mime()` + `generate_brochure_cover_thumbnail()` + konstante (`ALLOWED_PDF_MIME_TYPES`, `MAX_PDF_UPLOAD_SIZE_BYTES`, `MAX_PDF_PAGE_COUNT`, `PDF_RENDER_TIMEOUT_SECONDS`, `MAX_RENDERED_PIXELS`, `COVER_THUMBNAIL_SIZE`, `COVER_THUMBNAIL_QUALITY`, `COVER_THUMBNAIL_FORMAT`). |
| `apps/media_pipeline/signals.py` | `handle_brochure_post_save(sender, instance, created, raw, update_fields, **kwargs)` — non-raising, koristi `transaction.on_commit` callback (FIX iter-1 CRIT-5) + multi-layer infinite loop guard (FIX iter-1 CRIT-3). |

### 1.2 Modifikovani fajlovi (Dev u GREEN phase)

| Path | Modifications |
|---|---|
| `apps/media_pipeline/apps.py` | Targeted Edit — dodavanje `from django.db.models.signals import post_save` import-a + `MediaPipelineConfig.ready()` metode (koja resolvuje sender kroz `apps.get_model("products", "ProductBrochure")` + `post_save.connect(..., dispatch_uid="apps.media_pipeline.signals.handle_brochure_post_save")`). Story 2.3 docstring + class skeleton OČUVANI. |
| `pyproject.toml` | Task 0 — dodavanje `pytest-mock>=3.14.0` u `[dependency-groups].dev` + `pillow>=10.0` u `[project].dependencies` (defensive promote iz tranzitivne sorl-thumbnail). |

### 1.3 Novi fajlovi (test code — TEA RED phase deliverable, ovaj dokument)

| Path | Purpose |
|---|---|
| `apps/media_pipeline/tests/test_pdf_utils.py` | 15 scenarija za `validate_pdf_mime()` (AC1) + `generate_brochure_cover_thumbnail()` (AC2). |
| `apps/media_pipeline/tests/test_signals.py` | 10 scenarija za `handle_brochure_post_save()` (AC3 + AC6 + AC7 — UNIT testovi sa MagicMock + spy patterns). |
| `apps/media_pipeline/tests/test_apps_ready.py` | 2 scenarija za `MediaPipelineConfig.ready()` (AC4 — signal registracija + dispatch_uid idempotency). |
| `apps/media_pipeline/tests/conftest.py` | EXTEND — dodaje 5 novih PDF fixture-a: `minimal_pdf_1_page_bytes`, `corrupt_pdf_bytes`, `oversized_pdf_bytes`, `high_page_count_pdf_bytes`, `empty_pdf_bytes`. Postojeći image fixture-i OČUVANI. |

### 1.4 NIJE kreirano u Story 2.4

- NEMA `apps/media_pipeline/views.py` (utility app i dalje bez views)
- NEMA `apps/media_pipeline/admin.py`
- NEMA `apps/media_pipeline/urls.py`
- NEMA novih modela → NEMA migracija
- NEMA template tagova za PDF (Story 2.7 koristi postojeći `{% responsive_picture %}` za cover thumbnail)
- NEMA `apps/products/admin.py` izmena (Story 8.6 scope)
- NEMA `apps/products/forms.py` izmena (Story 8.6 prvi konzument `validate_pdf_mime` u ProductBrochureForm.clean_pdf_file)
- NEMA promene u `apps/products/models.py` (`ProductBrochure` već definisano u Story 2.2)
- NEMA novih testova u `tests/integration/test_app_boundaries.py` — postojeći Story 2.3 AC8 testovi pokrivaju Story 2.4 boundary regression (AC9)

---

## 2. `apps/media_pipeline/pdf_utils.py` — PDF utility (AC1, AC2)

### 2.1 Module-level konstante

| Konstanta | Tip | Vrednost | Razlog |
|---|---|---|---|
| `ALLOWED_PDF_MIME_TYPES` | `tuple[str, ...]` | `("application/pdf",)` | Single MIME per Decision PDF-D7 (libmagic vraća jedan MIME za sve PDF varijante). |
| `MIME_SNIFF_BYTES` | `int` | `2048` | Mirror Story 2.3 utils.py. |
| `MAX_PDF_UPLOAD_SIZE_BYTES` | `int` | `10 * 1024 * 1024` (10 MB) | FIX iter-1 CRIT-1 — sync sa MP-D8 FILE_UPLOAD_MAX_MEMORY_SIZE. |
| `MAX_PDF_PAGE_COUNT` | `int` | `200` | FIX iter-1 CRIT-4 — DoS guard (pdfinfo metadata check pre rendering-a). |
| `PDF_RENDER_TIMEOUT_SECONDS` | `int` | `15` | FIX iter-1 CRIT-4 — pdf2image >= 1.17.0 `timeout` kwarg za convert_from_bytes. |
| `MAX_RENDERED_PIXELS` | `int` | `50_000_000` | FIX iter-1 CRIT-4 — decompression bomb guard (pdf2image bypass-uje Pillow `MAX_IMAGE_PIXELS`). |
| `COVER_THUMBNAIL_SIZE` | `tuple[int, int]` | `(240, 320)` | AC2 — širina × visina (portrait). |
| `COVER_THUMBNAIL_QUALITY` | `int` | `85` | Mirror Story 2.3 `THUMBNAIL_QUALITY`. |
| `COVER_THUMBNAIL_FORMAT` | `str` | `"JPEG"` | AC2 — JPG izlaz. |

### 2.2 `validate_pdf_mime(upload, *, allowed_mimes=..., max_size_bytes=..., max_page_count=...) -> None`

**Signatura:**

```python
def validate_pdf_mime(
    upload: UploadedFile | None,
    *,
    allowed_mimes: Iterable[str] = ALLOWED_PDF_MIME_TYPES,
    max_size_bytes: int = MAX_PDF_UPLOAD_SIZE_BYTES,
    max_page_count: int = MAX_PDF_PAGE_COUNT,
) -> None:
```

**Behavior contract (test-encoded asercije u `test_pdf_utils.py`):**

| Slučaj | Input | Output |
|---|---|---|
| Validan PDF | UploadedFile sa minimal validan 1-page PDF bytes | return `None` (PASS) |
| Image kao PDF | UploadedFile sa `b"\xff\xd8\xff\xe0..."` JPEG bytes + `.pdf` ext | `ValidationError(_("Nedozvoljen tip fajla: %(mime)s..."))` |
| Empty upload | `SimpleUploadedFile("e.pdf", b"")` (size=0) | `ValidationError(_("PDF brošura je prazna ili nije priložena."))` |
| None upload | `validate_pdf_mime(None)` | `ValidationError(_("PDF brošura je prazna ili nije priložena."))`, NE `AttributeError` |
| Oversize upload | `upload.size > 10 MB` | `ValidationError(_("PDF brošura je veća od %(limit)d MB..."))` |
| High page count | PDF sa >200 stranica | `ValidationError(_("PDF brošura ima %(pages)d stranica..."))` |
| Corrupt PDF | invalid struct posle %PDF magic | NO RAISE (deferred to render-time graceful fail — `pdfinfo` exception swallowed, upload.seek(0) preserved) |
| Side-effect (success) | nakon successful return | `upload.tell() == 0` (stream reset) |
| Side-effect (rejection) | nakon ValidationError | `upload.tell() == 0` (stream reset) |

**Implementacija detalji:**
- `gettext_lazy as _` za sve ValidationError poruke
- Order of checks: (1) None/empty → (2) size limit → (3) MIME sniff → (4) `pdfinfo_from_bytes` page count
- `pdfinfo_from_bytes` exception (corrupt PDF) → swallow → return (defer to render-time)
- Mirror Story 2.3 `validate_image_mime()` pattern strukturalno

### 2.3 `generate_brochure_cover_thumbnail(pdf_field) -> ContentFile | None`

**Signatura:**

```python
def generate_brochure_cover_thumbnail(pdf_field: FieldFile) -> ContentFile | None:
```

**Behavior contract (test-encoded asercije u `test_pdf_utils.py`):**

| Slučaj | Input | Output |
|---|---|---|
| Validan PDF | FieldFile sa minimal 1-page PDF | `ContentFile(jpeg_bytes, name="brochure-cover.jpg")` |
| `pdf_field is None` | None | `None` (no raise) |
| `pdf_field.name == ""` | empty FieldFile | `None` (no raise) |
| Corrupt PDF | FieldFile sa random bytes | `None` + `logger.warning("Brochure cover render failed...")` |
| Encrypted PDF | mocked `convert_from_bytes` raising `PDFSyntaxError` | `None` + `logger.warning` (FIX iter-1 CRIT-8) |
| Render timeout | mocked `convert_from_bytes` raising `PDFPopplerTimeoutError` | `None` + `logger.warning` (FIX iter-1 CRIT-4) |
| Decompression bomb | mocked `convert_from_bytes` returning Image 8000×8000 (64M px > 50M) | `None` + `logger.warning` (FIX iter-1 CRIT-4) |
| Output dimensions | Validan A4 portrait (595×842) | output `width <= 240` AND `height <= 320` (aspect ratio preserved per Decision PDF-D3) |
| Output format | Validan PDF | output `Image.format == "JPEG"`, `Image.mode == "RGB"` |
| Side-effect (success) | FieldFile sa validan PDF | output ContentFile.name == `"brochure-cover.jpg"` |

**Implementacija detalji:**
- **NEVER raises** — sve poznate exception-e (`PDFInfoNotInstalledError`, `PDFPageCountError`, `PDFPopplerTimeoutError`, `PDFSyntaxError`, `OSError`, `ValueError`) hvata; nepoznate hvata `except Exception` blokom
- `convert_from_bytes(pdf_bytes, first_page=1, last_page=1, fmt="jpeg", dpi=100, timeout=PDF_RENDER_TIMEOUT_SECONDS)`
- Decompression bomb guard: `if rendered_pixels > MAX_RENDERED_PIXELS: log + return None`
- Force RGB mode pre JPEG save (Pillow `OSError: cannot write mode RGBA as JPEG`)
- `Image.thumbnail((240, 320), Image.Resampling.LANCZOS)` — aspect ratio preserved
- Output ContentFile sa name=`"brochure-cover.jpg"` (final storage path zavisi od `ProductBrochure.cover_thumbnail_image.upload_to`)

### 2.4 Importi (module header)

```python
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
from PIL import Image
from pdf2image import convert_from_bytes
from pdf2image.exceptions import (
    PDFInfoNotInstalledError,
    PDFPageCountError,
    PDFPopplerTimeoutError,
    PDFSyntaxError,
)
```

### 2.5 Logger name

```python
logger = logging.getLogger("apps.media_pipeline.pdf_utils")
```

---

## 3. `apps/media_pipeline/signals.py` — Signal handler (AC3)

### 3.1 Public function

```python
def handle_brochure_post_save(
    sender: Any,
    instance: Any,
    created: bool,
    raw: bool,
    update_fields: frozenset[str] | None,
    **kwargs: Any,
) -> None:
```

**Behavior contract (test-encoded asercije u `test_signals.py`):**

| Slučaj | Input | Behavior |
|---|---|---|
| `raw=True` (loaddata) | raw=True | EARLY RETURN — no render, no callback registered |
| Internal save (Layer A guard) | `update_fields == frozenset({"cover_thumbnail_image"})` | EARLY RETURN — no callback registered (infinite loop guard) |
| `pdf_file` empty | `instance.pdf_file = None` ili `instance.pdf_file.name == ""` | EARLY RETURN — no callback registered (FIX iter-1 CRIT-7) |
| `update_fields` ne sadrži `pdf_file` | `update_fields == ["title"]` | EARLY RETURN — no callback (performance optimization, FIX iter-1 CRIT-3) |
| Create (update_fields=None) sa validnim pdf_file | created=True, raw=False, update_fields=None | `transaction.on_commit(_generate_cover_on_commit)` REGISTERED — sync render se izvršava POSLE commit-a |
| Replace pdf_file | `update_fields = ["pdf_file"]` | `transaction.on_commit` registered — cover regen-uje se (FIX iter-1 CRIT-3) |
| Render vraća None | `generate_brochure_cover_thumbnail` returns None (graceful fail) | callback ne save-uje na `cover_thumbnail_image` polje; brochure ostaje sa praznim cover-om |
| Render raise-uje (hypothetical bug) | mocked generate raising Exception | handler NE raise-uje (callback hvata) |

**Implementacija detalji:**
- **NIKAD ne koristi `from apps.products.models import ProductBrochure`** (boundary)
- Sve cross-app reference se resolvuju kroz `sender` parametar (rešen u `apps.py.ready()`)
- `transaction.on_commit(_generate_cover_on_commit)` — render + save samo posle uspešnog commit-a (FIX iter-1 CRIT-5)
- Unutar callback-a:
  - `cover_file = generate_brochure_cover_thumbnail(instance.pdf_file)`
  - Ako `cover_file is None` → log warning + return (graceful failure)
  - Inače: `instance.cover_thumbnail_image.save(cover_file.name, cover_file, save=False)` (`save=False` ne triggeruje post_save)
  - Inače: `instance.save(update_fields=["cover_thumbnail_image"])` (Layer A guard će skip-ovati ovaj signal call)
  - `logger.info("Brochure cover generated successfully...")` za GREEN audit

### 3.2 Importi (module header)

```python
from __future__ import annotations

import logging
from typing import Any

from django.db import transaction
from django.db.models.signals import post_save

from apps.media_pipeline.pdf_utils import generate_brochure_cover_thumbnail
```

### 3.3 Logger name

```python
logger = logging.getLogger("apps.media_pipeline.signals")
```

---

## 4. `apps/media_pipeline/apps.py` — `MediaPipelineConfig.ready()` (AC4)

### 4.1 Targeted Edit (Dev GREEN scope)

Story 2.3 docstring + class skeleton MORAJU biti OČUVANI. Edit dodaje:

1. Novi import: `from django.db.models.signals import post_save`
2. Novi metod `ready()` u `MediaPipelineConfig` klasi.

### 4.2 `ready()` method signature

```python
class MediaPipelineConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.media_pipeline"
    verbose_name = _("Media pipeline")

    def ready(self) -> None:
        from django.apps import apps
        from apps.media_pipeline.signals import handle_brochure_post_save

        product_brochure_model = apps.get_model("products", "ProductBrochure")
        post_save.connect(
            handle_brochure_post_save,
            sender=product_brochure_model,
            dispatch_uid="apps.media_pipeline.signals.handle_brochure_post_save",
        )
```

**Behavior contract (test-encoded asercije u `test_apps_ready.py`):**

| Slučaj | Input | Behavior |
|---|---|---|
| Django startup | INSTALLED_APPS contains `apps.media_pipeline` | `handle_brochure_post_save` je live receiver za `post_save` signal sa sender=`ProductBrochure` |
| Double `ready()` call | manual second `ready()` call posle startup-a | `dispatch_uid` deduplicira — broj registered receiver-a sa tim UID ostaje 1 |

**Critical:**
- `signals` import je UNUTAR `ready()` metode (NE module-level) — `apps.get_model()` zahteva populated registry
- `dispatch_uid="apps.media_pipeline.signals.handle_brochure_post_save"` — kanonska full module path string

---

## 5. Signal registration contract

| Property | Value |
|---|---|
| Signal | `django.db.models.signals.post_save` |
| Sender (resolved at runtime) | `apps.get_model("products", "ProductBrochure")` |
| Receiver | `apps.media_pipeline.signals.handle_brochure_post_save` |
| dispatch_uid | `"apps.media_pipeline.signals.handle_brochure_post_save"` |
| Wired in | `apps.media_pipeline.apps.MediaPipelineConfig.ready()` |
| Connection style | Eksplicitan `post_save.connect()` (NIJE `@receiver` decorator — boundary compliance, vidi Decision PDF-D6) |

---

## 6. Test fixture additions (TEA scope — `conftest.py` EXTEND)

### 6.1 New fixtures

| Fixture | Scope | Output |
|---|---|---|
| `minimal_pdf_1_page_bytes` | function | Minimal validan 1-page PDF struct (per Decision PDF-D5 — raw bytes konstanta) |
| `corrupt_pdf_bytes` | function | Random bytes pretvarajući se da je PDF (`b"NOT_A_PDF_AT_ALL_JUST_RANDOM_BYTES"`) |
| `empty_pdf_bytes` | function | 0-byte upload (`b""`) |
| `oversized_pdf_bytes` | function | Validan PDF + padding stream > 10 MB (size guard test) |
| `high_page_count_pdf_bytes` | function | Validan PDF struct sa /Count >200 (page count guard test) |

### 6.2 Reused fixtures (Story 2.3)

- `temp_media_root` (Story 2.3) — monkeypatch `settings.MEDIA_ROOT` na pytest tmp_path; cache invalidation tri sloja
- `pdf_as_image_bytes` (Story 2.3) — minimal PDF bytes pre-postojeći; reuse za `test_validate_pdf_accepts_valid_pdf` ako se ne želi nov `minimal_pdf_1_page_bytes`
- `valid_jpeg_bytes` (Story 2.3) — image bytes za `test_validate_pdf_rejects_non_pdf_mime` (Image kao PDF)

---

## 7. Cross-references

### 7.1 Story 2.3 decisions (consumed, not redefined)

- **MP-D1 (sorl-thumbnail):** Story 2.4 NE konzumira direktno (PDF cover je pre-rendered JPG, ne lazy srcset).
- **MP-D3 (raise vs bool return):** Story 2.4 `validate_pdf_mime` prati pattern (raise ValidationError); `generate_brochure_cover_thumbnail` ODSTUPA — vraća `ContentFile | None` (caller signal mora biti non-raising).
- **MP-D6 (Docker test recept):** **KRITIČNO Story 2.4 SOT.** Mihas MORA koristiti `just test apps/media_pipeline/tests/` — libmagic + poppler-utils nisu na Windows host-u.
- **MP-D8 (DATA_UPLOAD_MAX_MEMORY_SIZE = 11 MB, FILE_UPLOAD_MAX_MEMORY_SIZE = 10 MB):** Story 2.4 `MAX_PDF_UPLOAD_SIZE_BYTES = 10 MB` je IZJEDNAČEN — FIX iter-1 CRIT-1.

### 7.2 Story 2.4 decisions (definisane u 2-4 story file)

- **PDF-D1** — Signal handler vs management command (signal wins, sync acceptable per project-context.md)
- **PDF-D1.5** — Eager regeneration na pdf_file replace (FIX iter-1 CRIT-3)
- **PDF-D2** — Novi `pdf_utils.py` (NE extend `utils.py`)
- **PDF-D3** — Aspect ratio preserved (NE strict resize) — `Image.thumbnail((240, 320), LANCZOS)`
- **PDF-D4** — Sync signal je acceptable za v1 (no Celery)
- **PDF-D5** — Minimal raw PDF struct fixture (NE reportlab, NE static fixture)
- **PDF-D6** — Eksplicitan `post_save.connect()` u `ready()` + `dispatch_uid` (NIJE `@receiver` decorator)
- **PDF-D7** — Single MIME `("application/pdf",)` (libmagic ne distinguishes PDF varijante)
- **PDF-D8** — epics.md vs Story 2.2 model upload_to neslaganje — deferred docs sync u Story 9.x

### 7.3 Boundary compliance (AC9)

- `apps/media_pipeline/pdf_utils.py` — NEMA `apps.products` / `apps.brands` import-a
- `apps/media_pipeline/signals.py` — NEMA `from apps.products.models import ProductBrochure` (sender resolution kroz parametar)
- `apps/media_pipeline/apps.py` — koristi `from django.apps import apps` (Django built-in) + `apps.get_model("products", "ProductBrochure")` (string-based, NE AST import node)
- Postojeći `tests/integration/test_app_boundaries.py` `test_media_pipeline_does_not_import_products` + `test_media_pipeline_does_not_import_brands` (Story 2.3 deliverable) **MORAJU ostati GREEN** posle Story 2.4 implementacije.

---

## 8. Logger names (full list)

| Module | Logger name |
|---|---|
| `apps/media_pipeline/pdf_utils.py` | `"apps.media_pipeline.pdf_utils"` |
| `apps/media_pipeline/signals.py` | `"apps.media_pipeline.signals"` |
| `apps/media_pipeline/utils.py` (Story 2.3, ne dotaknut) | nije logger user |

**Convention:**
- `logger.info` za uspeh (signal cover generated)
- `logger.warning` za graceful failure (PDF nevalidan, render timeout, decompression bomb)
- `logger.error` za neočekivane exception-e (defensive catch-all u `generate_brochure_cover_thumbnail`)

---

## 9. Test discipline reminders

- **TEA piše testove (RED), Dev piše implementaciju (GREEN)** — Dev NIKAD ne menja testove
- Test fajlovi se commit-uju **PRE** implementacije
- Implementacija se commit-uje **POSLE** (zasebno) — green phase
- Failure: ako TEA testovi failuju posle Dev implementacije, story se vraća u `paused`; Dev fix-uje implementaciju, NE testove

---

**End of Interface Contract 2.4**
