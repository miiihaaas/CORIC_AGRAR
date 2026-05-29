---
story-id: "2.3"
story-key: 2-3-image-pipeline-sa-sorl-thumbnail-responsive-srcset
title: Interface Contract — Image Pipeline (sorl-thumbnail + responsive srcset)
status: contract
created: 2026-05-29
last_modified: 2026-05-29
author: TEA (RED phase)
---

# Story 2.3 — Interface Contract

Ovaj dokument je kanonski specifikacija ugovora za sve artifakte Story 2.3. TEA RED-phase
test-suite (`apps/media_pipeline/tests/test_*.py`, proširenje `tests/integration/test_app_boundaries.py`)
direktno enkodira asercije definisane ovde. Dev MUST satisfy ovaj ugovor da bi Story 2.3
prešla u GREEN.

Story 2.3 uvodi **prvi utility Django app u Epic 2** (`apps/media_pipeline/`) — utility-only
app **bez modela**, **bez admin-a**, **bez views-a**. Sadrži:

1. `validate_image_mime()` helper za double-check MIME validaciju (python-magic + Pillow)
2. `{% responsive_picture %}` template tag za `<picture>` element sa srcset 400w/800w/1600w
3. Kanonsku `sorl-thumbnail` konfiguraciju u `config/settings/base.py`

App je **cross-cutting utility** (per architecture.md § App dependency graph): `media_pipeline ←
(utility, importovan od products + brands + blog)`. Domain app-ovi konzumiraju utility kroz
template tagove / helper-e; utility SAM NE SME uvoziti domain app-ove (`apps.products`,
`apps.brands`) — enforced kroz boundary test.

---

## 1. Artifact inventory

### 1.1 Novi fajlovi (production code — Dev deliverable u GREEN phase)

| Path | Purpose |
|---|---|
| `apps/media_pipeline/__init__.py` | Prazan paket marker (startapp generiše). |
| `apps/media_pipeline/apps.py` | `MediaPipelineConfig(AppConfig)` sa `name = "apps.media_pipeline"`, `verbose_name = _("Media pipeline")`. |
| `apps/media_pipeline/models.py` | Prazan placeholder docstring (utility app NEMA modela). |
| `apps/media_pipeline/utils.py` | `validate_image_mime(upload, *, allowed_mimes=..., max_size_bytes=...)` helper + `ALLOWED_IMAGE_MIME_TYPES` + `MAX_UPLOAD_SIZE_BYTES` + `MIME_SNIFF_BYTES` konstante. |
| `apps/media_pipeline/templatetags/__init__.py` | Prazan paket marker. |
| `apps/media_pipeline/templatetags/media_tags.py` | `{% responsive_picture %}` inclusion_tag + `RESPONSIVE_WIDTHS = (400, 800, 1600)` konstanta. |
| `apps/media_pipeline/migrations/__init__.py` | Prazan paket marker (startapp generiše); NEMA migracija u media_pipeline. |
| `templates/media_pipeline/responsive_picture.html` | Inclusion tag template — renderuje `<picture><img src=.. srcset=.. sizes=.. alt=.. loading=.. width=..></picture>`. |

### 1.2 Novi fajlovi (test code — TEA RED phase deliverable)

| Path | Purpose |
|---|---|
| `apps/media_pipeline/tests/` | Test direktorijum **BEZ `__init__.py`** (REVIEW FIX MP-R1 — kolizija sa root `tests/__init__.py` zbog `--import-mode=importlib`). |
| `apps/media_pipeline/tests/conftest.py` | 7 Pillow-generated image bytes fixture-i + `temp_media_root` monkeypatch fixture. |
| `apps/media_pipeline/tests/test_apps.py` | `MediaPipelineConfig.name` smoke (Gotcha MP-1 regression — stronger assertion kroz `apps.get_app_config()`). |
| `apps/media_pipeline/tests/test_utils.py` | 11 scenarija za `validate_image_mime()` (AC3, AC5 — pozitivni + negativni + edge case). |
| `apps/media_pipeline/tests/test_templatetags.py` | 10 scenarija za `{% responsive_picture %}` (AC4, AC10 — render, srcset, format kwarg). |
| `apps/media_pipeline/tests/test_thumbnails.py` | 4 integration scenarija za thumbnail generation (AC6 — lazy create, KVStore cache, PNG→JPEG, size ratio). |
| `tests/integration/test_app_boundaries.py` | **Proširenje** postojećeg fajla — 2 nove test funkcije, reuse `_assert_no_import` helper-a. |

### 1.3 Modifikovani fajlovi (Dev u GREEN)

| Path | Modifications |
|---|---|
| `config/settings/base.py` | (a) `INSTALLED_APPS` APENDUJ DVE linije POSLE `"apps.products",`: `"sorl.thumbnail",` + `"apps.media_pipeline",`. (b) Dodaj `MEDIA_URL` + `MEDIA_ROOT` ako ne postoje (verifikuj prvo). (c) Dodaj `THUMBNAIL_*` blok (8 settings) POSLE `STORAGES` blok i PRE `BOOTSTRAP5` blok. |
| `config/urls.py` | (Conditional) Dodaj `urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)` u `DEBUG` block ako ne postoji. |
| `justfile` | Task 1.6 — modifikuje `test` recept da koristi Docker (per Decision MP-D6). Cross-cutting infra promena. |

### 1.4 NIJE kreirano u Story 2.3

- NEMA `apps/media_pipeline/views.py` (Task 1.2b briše startapp default; utility app NEMA views)
- NEMA `apps/media_pipeline/admin.py` (Task 1.2b briše; sorl-thumbnail KVStore se ostavlja u default-u)
- NEMA `apps/media_pipeline/urls.py` (utility app NEMA URL routes)
- NEMA `apps/media_pipeline/forms.py` (utility helpers, no forme)
- NEMA `apps/media_pipeline/managers.py`
- NEMA `apps/media_pipeline/signals.py` (Story 2.4 prvi put kreira za ProductBrochure post_save)
- NEMA `apps/media_pipeline/apps.py.ready()` hook (Story 2.4 dodaje za signal registraciju)
- NEMA modela u media_pipeline → NEMA `migrations/0001_initial.py` (sorl-thumbnail KVStore migracija je vlasništvo paketa)
- NEMA admin form integration sa `validate_image_mime()` — Story 8.4 (Brand admin) + Story 8.6 (Product admin) prvi konzumenti
- NEMA `validate_pdf_mime()` helper — Story 2.4 dodaje paralelno
- NEMA promena u `apps/brands/models.py` / `apps/products/models.py` — image polja već postoje, ostaju netaknuta

---

## 2. `apps/media_pipeline/apps.py` — AppConfig

```python
"""AppConfig za apps.media_pipeline — image + PDF utility (cross-cutting).

Story 2.3 (Epic 2) — utility app bez modela. Konzumiran od domain app-ova
(brands, products, blog) kroz template tagove i helper-e.
Jednosmerna zavisnost: media_pipeline NE SME uvoziti apps.products / apps.brands.

Story 2.4 proširuje ovaj app sa post_save signal handler-om za ProductBrochure
(`signals.py`) i registracijom kroz `ready()` hook — Story 2.3 NEMA ready() hook.
"""
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class MediaPipelineConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.media_pipeline"               # KRITIČNO — sa apps. prefiksom (Gotcha MP-1)
    verbose_name = _("Media pipeline")
```

**KRITIČNO (Gotcha MP-1):** `name = "apps.media_pipeline"` MORA imati `apps.` prefix. Bez prefiksa
Django INSTALLED_APPS resolve fail-uje sa `LookupError: No installed app with label
'media_pipeline'`. Mirror BR-1 (brands) / PR-1 (products) regression guard pattern.

---

## 3. `apps/media_pipeline/utils.py` — `validate_image_mime()` (AC3, AC5)

### 3.1 Module-level konstante

| Konstanta | Tip | Vrednost |
|---|---|---|
| `ALLOWED_IMAGE_MIME_TYPES` | `tuple[str, ...]` | `("image/jpeg", "image/png", "image/webp")` |
| `MIME_SNIFF_BYTES` | `int` | `2048` |
| `MAX_UPLOAD_SIZE_BYTES` | `int` | `10 * 1024 * 1024` (10 MB) |

### 3.2 `validate_image_mime(upload, *, allowed_mimes=..., max_size_bytes=...) -> None`

**Signatura:**

```python
def validate_image_mime(
    upload: UploadedFile,
    *,
    allowed_mimes: Iterable[str] = ALLOWED_IMAGE_MIME_TYPES,
    max_size_bytes: int = MAX_UPLOAD_SIZE_BYTES,
) -> None:
```

**Behavior contract (test-encoded asercije):**

| Slučaj | Input | Output |
|---|---|---|
| Validan JPEG | UploadedFile sa `b"\xff\xd8\xff\xe0..."` content | return `None` (PASS) |
| Validan PNG | UploadedFile sa Pillow-generated PNG bytes | return `None` (PASS) |
| Validan WebP | UploadedFile sa Pillow-generated WebP bytes | return `None` (PASS) |
| PDF kao slika | UploadedFile sa `b"%PDF-1.4\n..."` + `.jpg` ext | `ValidationError(_("Nedozvoljen tip slike: %(mime)s. Dozvoljeni tipovi: %(allowed)s."))` |
| EXE kao slika | UploadedFile sa `b"MZ\x90\x00..."` + `.jpg` ext | `ValidationError("Nedozvoljen tip slike: ...")` |
| Corrupt JPEG | UploadedFile sa validan SOI marker + truncated body | `ValidationError(_("Slika je oštećena ili nije validan format."))` |
| Empty upload | `SimpleUploadedFile("e.jpg", b"")` (size=0) | `ValidationError(_("Slika je prazna ili nije priložena."))` |
| None upload | `validate_image_mime(None)` | `ValidationError(_("Slika je prazna ili nije priložena."))`, NE `AttributeError` |
| Oversize upload | `upload.size > 10 MB` | `ValidationError(_("Slika je veća od %(limit)d MB..."))` |
| `upload.size is None` (streaming) | TemporaryUploadedFile sa size=None | `ValidationError(_("Slika je prazna..."))`, NE `TypeError` |
| Side-effect | nakon successful return | `upload.tell() == 0` (stream reset) |

**Implementacija detalji:**
- `gettext_lazy as _` za sve error poruke (lazy evaluation za i18n)
- `not upload.size` truthy check hvata oba: `0` i `None` (NE `upload.size == 0`)
- Order of checks: (1) None/empty → (2) size limit → (3) MIME sniff → (4) Pillow verify
- `finally: upload.seek(0)` u Pillow block-u — Image.verify() troši stream
- `Image.open(upload).verify()` raise (UnidentifiedImageError, SyntaxError, OSError) → ValidationError

### 3.3 Importi (module header)

```python
from __future__ import annotations

from typing import Iterable

import magic
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from django.utils.translation import gettext_lazy as _
from PIL import Image, UnidentifiedImageError
```

---

## 4. `apps/media_pipeline/templatetags/media_tags.py` — `{% responsive_picture %}` (AC4, AC10)

### 4.1 Module-level konstante

| Konstanta | Tip | Vrednost |
|---|---|---|
| `RESPONSIVE_WIDTHS` | `tuple[int, ...]` | `(400, 800, 1600)` |

### 4.2 `responsive_picture` inclusion_tag

**Signatura:**

```python
@register.inclusion_tag("media_pipeline/responsive_picture.html")
def responsive_picture(
    image: ImageFieldFile | None,
    alt: str = "",
    sizes: str = "(max-width: 768px) 100vw, 50vw",
    loading: str = "lazy",
    css_class: str = "",
    crop: str = "center",
    format: str = "JPEG",
) -> dict:
```

**Behavior contract (test-encoded asercije):**

| Slučaj | Input | Output template context |
|---|---|---|
| Image present | ImageFieldFile sa upload | dict sa keys: `image`, `alt`, `sizes`, `loading`, `css_class`, `fallback_url`, `srcset`, `width` |
| `image=None` | `responsive_picture(None, alt="x")` | dict sa `image: None` → template renderuje prazno (`<picture>` NIJE u outputu) |
| Empty ImageFieldFile | ImageFieldFile bez `.name` | dict sa `image: None` → template renderuje prazno |
| `loading` default | bez kwarg-a | `loading="lazy"` u rendered HTML |
| `loading="eager"` | eksplicitan kwarg | `loading="eager"` u rendered HTML |
| `css_class="x"` | eksplicitan kwarg | `class="x"` atribut na `<img>` |
| `format="JPEG"` (default) | PNG source sa alpha | thumbnail je `.jpg` (loses alpha) |
| `format="PNG"` (override) | PNG source sa alpha | thumbnail je `.png` (preserves alpha, mode "RGBA" ili "LA") |
| Srcset structure | bilo koji image | srcset string sadrži `400w`, `800w`, `1600w` substring-ove |
| Fallback src | bilo koji image | `fallback_url` == URL za 1600w varijantu (largest) |

**Implementacija detalji:**
- `image` može biti pozicionalni ili keyword arg (testovi pokrivaju oba pattern-a)
- Defensive `if not image or not getattr(image, "name", ""):` early return (boundary defensive validation)
- `quality = getattr(settings, "THUMBNAIL_QUALITY", 85)` — čita iz settings (testabilna globalna konfiguracija)
- `sorl.thumbnail.get_thumbnail(image, f"{width}", crop=crop, quality=quality, format=format)` poziv po width-u
- `fallback = variants[-1]` (1600w je largest)
- `srcset_str = ", ".join(f"{v['url']} {v['width']}w" for v in variants)`

### 4.3 Importi (module header)

```python
from __future__ import annotations

from django import template
from django.db.models.fields.files import ImageFieldFile
from sorl.thumbnail import get_thumbnail

register = template.Library()
```

---

## 5. `templates/media_pipeline/responsive_picture.html` (AC4)

```html
{% comment %}
Story 2.3 — responsive `<picture>` element za sve ImageField-ove.
Renderuje se kroz {% responsive_picture <field> alt=... sizes=... %} tag.
Lazy loading podrazumevan; above-the-fold caller prosleđuje loading="eager".
{% endcomment %}
{% if image %}
<picture>
  <img
    src="{{ fallback_url }}"
    srcset="{{ srcset }}"
    sizes="{{ sizes }}"
    alt="{{ alt }}"
    loading="{{ loading }}"
    width="{{ width }}"
    {% if css_class %}class="{{ css_class }}"{% endif %}
  >
</picture>
{% endif %}
```

**KRITIČNO:** template path je `templates/media_pipeline/responsive_picture.html` (root-level
templates direktorijum), NIJE `apps/media_pipeline/templates/media_pipeline/...`. Django template
discovery preferira root-level `templates/` per project konvenciji.

---

## 6. `config/settings/base.py` — delta

### 6.1 `INSTALLED_APPS` — APENDUJ DVE linije POSLE `"apps.products",`

```python
INSTALLED_APPS = [
    "modeltranslation",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_htmx",
    "django_bootstrap5",
    "apps.core",
    "apps.brands",                          # Story 2.1
    "apps.products",                        # Story 2.2
    "sorl.thumbnail",                       # NOVO Story 2.3 — third-party paket POSLE domain app-ova (utility lib)
    "apps.media_pipeline",                  # NOVO Story 2.3 — utility app POSLE sorl.thumbnail (koristi njegove template tags)
]
```

**KRITIČNO:** NE rewrite cele liste. Live `config/settings/base.py` (linije 28-46) ima trailing
komentare iz Story 1.6/2.1/2.2 koji moraju biti preserved. Targeted Edit operacija = TAČNO dve
nove linije apendovane (mirror 2.1 D2 / 2.2 PR-D1 dependency-ordered pattern).

### 6.2 `Media` blok — POSLE `STATIC_ROOT` definicije, AKO ne postoji

```python
# ── Media ────────────────────────────────────────────────────────────────────
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
```

### 6.3 `THUMBNAIL_*` blok — POSLE `STORAGES` blok, PRE `BOOTSTRAP5` blok

```python
# ── sorl-thumbnail (Story 2.3) ───────────────────────────────────────────────
THUMBNAIL_BACKEND = "sorl.thumbnail.base.ThumbnailBackend"
THUMBNAIL_KVSTORE = "sorl.thumbnail.kvstores.cached_db_kvstore.KVStore"
THUMBNAIL_FORMAT = "JPEG"
THUMBNAIL_QUALITY = 85
THUMBNAIL_PRESERVE_FORMAT = False  # per-call override via `format='PNG'` u {% responsive_picture %} (Decision MP-D5)
# FIX-7 / Decision MP-D7: kanonski sorl-thumbnail setting je THUMBNAIL_PREFIX (sa
# trailing slash). THUMBNAIL_DIRNAME ne postoji u sorl source-u (no-op assignment).
THUMBNAIL_PREFIX = "thumbnails/"
# FIX-3 (Security HIGH-2): hardcoded False — sorl stack trace u template render-u
# kad je True leak-uje Pillow verziju i MEDIA_ROOT putanju.
THUMBNAIL_DEBUG = False
```

### 6.4 Settings keys added (summary)

| Setting | Value |
|---|---|
| `MEDIA_URL` | `"/media/"` |
| `MEDIA_ROOT` | `BASE_DIR / "media"` |
| `THUMBNAIL_BACKEND` | `"sorl.thumbnail.base.ThumbnailBackend"` |
| `THUMBNAIL_KVSTORE` | `"sorl.thumbnail.kvstores.cached_db_kvstore.KVStore"` |
| `THUMBNAIL_FORMAT` | `"JPEG"` |
| `THUMBNAIL_QUALITY` | `85` |
| `THUMBNAIL_PRESERVE_FORMAT` | `False` |
| `THUMBNAIL_PREFIX` | `"thumbnails/"` (FIX-7 / Decision MP-D7) |
| `THUMBNAIL_DEBUG` | `False` (FIX-3 / Security HIGH-2 — hardcoded, never `DEBUG`) |
| `DATA_UPLOAD_MAX_MEMORY_SIZE` | `11 * 1024 * 1024` (FIX-4 / Security MEDIUM-1 / Decision MP-D8 — cross-cutting upload limit trade-off) |
| `FILE_UPLOAD_MAX_MEMORY_SIZE` | `10 * 1024 * 1024` (FIX-4 / Security MEDIUM-1 / Decision MP-D8 — matches `MAX_UPLOAD_SIZE_BYTES` da prevent disk DoS) |

---

## 7. `config/urls.py` — MEDIA URL handler (DEBUG only)

```python
from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

**Conditional:** ako block već postoji (verifikuj kroz `Select-String` u Task 2.4), preskoči.

---

## 8. Migracija — sorl-thumbnail KVStore (AC7)

**`apps/media_pipeline/migrations/`** ostaje prazan (`__init__.py` only). Utility-only app
NEMA modela, NEMA migracija.

**Sorl-thumbnail KVStore migracija** je vlasništvo `sorl.thumbnail` paketa:
- `thumbnail.0001_initial` — kreira `thumbnail_kvstore` tabelu (key, value polja)
- Aplicira se automatski pri `manage.py migrate` posle registracije `"sorl.thumbnail"` u INSTALLED_APPS

**`makemigrations media_pipeline` MORA vratiti `No changes detected`** (no models, no migrations).

---

## 9. Test infrastructure (RED phase pattern)

Story 2.3 testovi prate Story 2.1/2.2 pattern:

- `pytestmark = pytest.mark.django_db` na module level za DB-based testove
- Plain `SimpleUploadedFile` (NIJE factory_boy)
- Pillow-generated image bytes za PNG/WebP fixture-i (NIJE hardcoded stub bytes — `Image.verify()` raise-uje na ne-validnim stub bytes)
- `tmp_path` monkeypatch za `MEDIA_ROOT` (per-test isolation)
- Inline JPEG magic bytes (validan SOI marker — vidi conftest)
- Docker test run command (per Decision MP-D6 — libmagic SEGFAULT na Windows host-u)

### 9.1 Test summary mapping AC → test files

| AC | Test file | Tests |
|---|---|---|
| AC1 (app skeleton) | `apps/media_pipeline/tests/test_apps.py` | `test_media_pipeline_config_name_has_apps_prefix` |
| AC3 (validate_image_mime) | `apps/media_pipeline/tests/test_utils.py` | 11 scenarija (positive: JPEG/PNG/WebP; negative: PDF/EXE/corrupt/empty/None/oversize; edge: size=None streaming, seek-back side-effect) |
| AC4 (responsive_picture) | `apps/media_pipeline/tests/test_templatetags.py` | 10 scenarija (render structure, srcset, lazy/eager, css_class, alt, format kwarg) |
| AC5 (rejection) | `apps/media_pipeline/tests/test_utils.py` (deo gornjeg seta) | `test_validate_image_mime_rejects_*` |
| AC6 (thumbnail dir + KVStore) | `apps/media_pipeline/tests/test_thumbnails.py` | 4 scenarija (lazy create, cache hit, PNG→JPEG, size ratio) |
| AC7 (migracija) | Manual review | — |
| AC8 (boundary) | `tests/integration/test_app_boundaries.py` | `test_media_pipeline_does_not_import_products`, `test_media_pipeline_does_not_import_brands` |
| AC10 (format='PNG') | `apps/media_pipeline/tests/test_templatetags.py` | `test_responsive_picture_format_png_preserves_alpha`, `test_responsive_picture_format_jpeg_default_loses_alpha` |

### 9.2 Conftest fixtures (apps/media_pipeline/tests/conftest.py)

| Fixture | Scope | Output |
|---|---|---|
| `valid_jpeg_bytes` | function | Minimal validan JPEG (62 bytes) — SOI + JFIF + DCT + EOI marker |
| `valid_png_bytes` | function | Pillow-generated PNG (10×10 red, RGB) |
| `valid_png_with_alpha_bytes` | function | Pillow-generated PNG (10×10, RGBA, alpha=128) |
| `valid_webp_bytes` | function | Pillow-generated WebP (10×10 red) |
| `corrupt_jpeg_bytes` | function | Validan SOI marker + truncated body (no EOI) |
| `pdf_as_image_bytes` | function | `b"%PDF-1.4\n..."` magic bytes |
| `realistic_source_image_bytes` | function | Pillow `effect_noise((2400, 1800), sigma=64)` → RGB → JPEG quality=95 (high-entropy noise → ~500KB-1MB) |
| `temp_media_root` | function | monkeypatch `settings.MEDIA_ROOT` na `tmp_path` |

---

## 10. Boundary regression tests

```python
# tests/integration/test_app_boundaries.py — DODATI dve nove funkcije
# `_assert_no_import` helper VEĆ DEFINISAN u fajlu (Story 2.2 AC12) — REUSE-uj.

def test_media_pipeline_does_not_import_products():
    """architecture.md § App dependency graph — media_pipeline je utility,
    NE SME importovati domain app apps.products.
    """
    media_pipeline_dir = REPO_ROOT / "apps" / "media_pipeline"
    if not media_pipeline_dir.exists():
        return  # defensive: RED phase pre Dev kreiranja app-a
    _assert_no_import(media_pipeline_dir, "apps.products")


def test_media_pipeline_does_not_import_brands():
    """architecture.md § App dependency graph — media_pipeline je utility,
    NE SME importovati domain app apps.brands.
    """
    media_pipeline_dir = REPO_ROOT / "apps" / "media_pipeline"
    if not media_pipeline_dir.exists():
        return
    _assert_no_import(media_pipeline_dir, "apps.brands")
```

---

**End of Interface Contract 2.3**
