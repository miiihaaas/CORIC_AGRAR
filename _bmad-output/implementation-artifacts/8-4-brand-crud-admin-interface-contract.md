# 8.4 — Brand CRUD Admin — Interface Contract (TEA / RED phase)

> **Authority:** This document is the canonical contract for Story 8.4. The Dev (GREEN phase)
> MUST implement to it. Every named symbol, constant, attribute, and behavior below is a
> requirement locked by the failing tests in
> `apps/brands/tests/test_brand_crud_admin.py`.
>
> **Scope:** ONLY `apps/brands/admin.py` (Dev MAY split `BrandAdminForm` into
> `apps/brands/forms.py` — the tests import it from `apps.brands.admin`, so it MUST be
> importable as `apps.brands.admin.BrandAdminForm` regardless; re-export if split).
> NO migrations, NO new deps, NO model/translation/urls/permissions changes.

---

## 0. Files Dev edits

| File | Change |
|------|--------|
| `apps/brands/admin.py` | `BrandAdmin` → `TranslationAdmin`; `+ BrandAdminForm`; `+ SeriesInline`; `+ MAX_*_UPLOAD_SIZE` constants; `+ image-preview / has_pdf` methods; `SeriesAdmin.view_on_site = False`. Keep `SeoMetaInline` + `SeoWarningAdminMixin` on both Brand & Series admins. Keep `CategoryAdmin`/`SubcategoryAdmin` UNTOUCHED. |
| (optional) `apps/brands/forms.py` | If `BrandAdminForm` is extracted — MUST still be re-exported/importable from `apps.brands.admin`. |

---

## 1. Module-level constants (UPPER_SNAKE_CASE — AC3 / SM-D9 / G-13)

Defined at top of `apps/brands/admin.py`:

```python
MAX_IMAGE_UPLOAD_SIZE = 5 * 1024 * 1024    # 5 MB  — logo, hero_image
MAX_PDF_UPLOAD_SIZE   = 20 * 1024 * 1024   # 20 MB — catalog_pdf

ALLOWED_IMAGE_MIME_TYPES = ("image/jpeg", "image/png", "image/webp")
ALLOWED_PDF_MIME_TYPES   = ("application/pdf",)
```

- Names are **load-bearing** (tests assert `admin.MAX_IMAGE_UPLOAD_SIZE == 5*1024*1024`
  and `admin.MAX_PDF_UPLOAD_SIZE == 20*1024*1024`).
- Image allowlist EXCLUDES `gif`/`svg` (SVG = XSS — OQ-5).
- Values are v1 defaults pending Mihas/biznis confirmation (OQ-5) but are locked for this story.

---

## 2. `BrandAdminForm(forms.ModelForm)`

```python
class BrandAdminForm(forms.ModelForm):
    class Meta:
        model = Brand
        exclude = ()                # MANDATORY — Meta.fields OR Meta.exclude (G-12)
        widgets = {
            "brand_color": forms.TextInput(attrs={"type": "color"}),   # AC4 / G-6
        }
```

### 2.1 `__init__` — DO NOT relax `name_sr` required-promotion (AC7 / G-11 — M1 fix)
```python
def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    if "brand_color" in self.fields:
        self.fields["brand_color"].widget.attrs["type"] = "color"
    # NO name_sr/name/slug required relaxation — name_sr is unconditionally required.
```
- `name_sr` (default-locale of `blank=False` `name`) MUST stay a required form field. A
  nameless Brand is not a valid model state (`Brand.save()`→`full_clean()` rejects blank
  `name`). Empty `name_sr` → graceful FORM error on `name_sr` (admin re-renders, HTTP 200),
  NEVER a 400/500 model `full_clean` escape. (Corrects the wrong step-02 C2 "draft with empty
  name_sr" premise.)
- `is_coming_soon` is an INDEPENDENT flag — it does NOT relax the required name.
- `slug` is also required on the admin form; `prepopulated_fields` JS fills it from `name` in
  a browser (no-JS test scrapers must pass `slug` explicitly for a successful save).

### 2.2 `clean_logo` / `clean_hero_image` — DELEGATE to blessed `validate_image_mime` (AC3 / G-13 / M2)
For each of `logo`, `hero_image`:
```python
from apps.media_pipeline.utils import validate_image_mime

def clean_logo(self):
    f = self.cleaned_data.get("logo")
    if not f:
        return f                                   # graceful skip (blank=True)
    validate_image_mime(
        f,
        allowed_mimes=ALLOWED_IMAGE_MIME_TYPES,
        max_size_bytes=MAX_IMAGE_UPLOAD_SIZE,
    )                                              # MIME + Pillow verify + size cap + BOMB guard; seek(0)
    return f
```
- The helper does MIME signature + Pillow `verify()` + size cap + **decompression-bomb guard
  (`Image.MAX_IMAGE_PIXELS=50M` + `DecompressionBombWarning→error`)** + `seek(0)` reset (file
  stays intact for save). DO NOT re-implement inline — the inline duplicate dropped the bomb
  guard (a 121M-px PNG passed; M2).
- Reuse the SAME pattern for `clean_hero_image` against `hero_image`.

### 2.3 `clean_catalog_pdf` — DELEGATE to blessed `validate_pdf_mime` (AC3 / G-13 / M2)
```python
from apps.media_pipeline.pdf_utils import validate_pdf_mime

def clean_catalog_pdf(self):
    f = self.cleaned_data.get("catalog_pdf")
    if not f:
        return f                                   # graceful skip
    validate_pdf_mime(
        f,
        allowed_mimes=ALLOWED_PDF_MIME_TYPES,
        max_size_bytes=MAX_PDF_UPLOAD_SIZE,
    )                                              # MIME + size + page-count guard; seek(0)
    return f
```

> **MESSAGE CONTRACT (canonical helper messages — tests assert these substrings):**
> - image wrong MIME → **`Nedozvoljen tip slike: …`**
> - image corrupt / decompression-bomb → **`Slika je oštećena ili nije validan format.`**
> - PDF wrong MIME → **`Nedozvoljen tip fajla: … Dozvoljen je samo PDF format.`**
>
> The media_pipeline helper is the project's CANONICAL validator — do NOT keep a divergent
> `"Nedozvoljen tip fajla."` message for images just to satisfy an old assertion.

### 2.4 NO `clean()` publish-gate (AC7 / SM-D4 / M1 fix)
- The conditional `is_coming_soon=False ⇒ name_sr required` publish-gate is **REMOVED**: since
  `name_sr` is now unconditionally required (§2.1), the gate is dead/contradictory logic.
- `is_coming_soon` stays an INDEPENDENT flag (it does NOT gate name presence).
- Empty `name_sr` (either `is_coming_soon` value) → graceful field error on `name_sr` (HTTP 200),
  no Brand row, never 400/500.
- A custom `clean()` is OPTIONAL; if present it MUST NOT re-implement hex/statistics validation
  (`Brand.clean()` is the single source — G-7) and MUST NOT re-add a name_sr publish-gate.

---

## 3. `SeriesInline(TranslationStackedInline)` (AC6 / G-3 / G-10)

```python
from modeltranslation.admin import TranslationStackedInline

class SeriesInline(TranslationStackedInline):
    model = Series
    extra = 0
    exclude = ("slug",)             # MANDATORY (G-10) — Series.save() auto-gens slug
```
- MUST be a subclass of `modeltranslation.admin.TranslationStackedInline` (per-locale name/description).
- `exclude = ("slug",)` — `Series.slug` is `SlugField` (NOT blank=True); including it as a
  required inline field breaks form validation before `Series.save()` auto-gen. Adding a Series
  inline row with only `name_sr` MUST save (slug auto-generated).
- MUST NOT enable `show_change_link` (would route to Series change-view → `get_absolute_url` →
  `brands:series_detail` NoReverseMatch — G-3).

---

## 4. `BrandAdmin(SeoWarningAdminMixin, TranslationAdmin)` (AC1, AC2, AC8, AC9)

```python
class BrandAdmin(SeoWarningAdminMixin, TranslationAdmin):     # MRO: mixin FIRST (G-2)
    form = BrandAdminForm
    inlines = [SeoMetaInline, SeriesInline]                   # SeoMetaInline KEPT (G-8) + SeriesInline
    list_display = ("name", "is_coming_soon", "brand_color", "has_pdf", "slug")
    list_filter = ("is_coming_soon",)
    search_fields = ("name_sr",)                              # REAL column, NOT virtual `name` (G-1)
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("created_at", "updated_at", "logo_preview", "hero_preview")
    # view_on_site NOT set — brands:detail IS registered → "View on site" works (G-4)
    fieldsets = (...)   # base field names only (name/description/slogan auto-expand per-locale)
```

### Contract for `BrandAdmin`
| Attribute / method | Requirement |
|---|---|
| base class | `isinstance(admin, modeltranslation.admin.TranslationAdmin)` is True; `issubclass(BrandAdmin, SeoWarningAdminMixin)` is True. |
| `inlines` | contains BOTH `SeoMetaInline` (regression-lock, G-8) AND `SeriesInline`. |
| `form` | is `BrandAdminForm`. |
| `list_display` | contains at least `name` and `is_coming_soon`; SHOULD include `has_pdf` (boolean indicator). |
| `list_filter` | contains `is_coming_soon`. |
| `search_fields` | equals `("name_sr",)` (real column — must NOT raise `FieldError` on changelist search). |
| `view_on_site` | NOT set to `False` (Brand `brands:detail` is registered — G-4). |

### `has_pdf(obj)` — boolean indicator (AC9, recommended)
```python
@admin.display(boolean=True, description="PDF katalog")
def has_pdf(self, obj):
    return bool(obj.catalog_pdf)
```
- True when `catalog_pdf` set, False when not. No HTML render, no `get_absolute_url`.

### `logo_preview(obj)` / `hero_preview(obj)` — image preview (AC2 / G-6)
```python
@admin.display(description="Pregled logoa")
def logo_preview(self, obj):
    if obj.logo:
        return format_html('<img src="{}" style="max-height:80px">', obj.logo.url)
    return "—"
```
- MUST use `format_html` with `{}` placeholder (XSS boundary — escape `obj.logo.url`); NEVER
  raw f-string/`%`/`+` with `mark_safe` on user data (G-6).
- Truthy-guard: renders `<img>` ONLY when the file exists; empty/None → `"—"` (no broken `<img>`).
- Same contract for `hero_preview` against `obj.hero_image`.

---

## 5. `SeriesAdmin` — proactive view_on_site hardening (AC6 / G-3 / SM-D6 / SM-D8)

```python
@admin.register(Series)
class SeriesAdmin(SeoWarningAdminMixin, admin.ModelAdmin):   # standalone @register KEPT (SM-D6)
    view_on_site = False                                     # NEW (G-3 / mirror blog BL-5)
    inlines = [SeoMetaInline]                                # 6.1 regression KEPT
```
- `SeriesAdmin.view_on_site is False` (locks against future `brands:series_detail` NoReverseMatch).
- Standalone Series changelist + change-view stay 200.
- `SeoMetaInline` STILL present on `SeriesAdmin` (6.1 regression-lock).
- Series stays a standalone `@admin.register(Series)` — the Brand inline is ADDITIVE, not a replacement.

---

## 6. UNTOUCHED (regression boundaries)

- `apps/brands/models.py`, `translation.py`, `migrations/` — **0 schema** (`makemigrations brands --check` = No changes).
- `apps/accounts/permissions.py` — Editor already has brands CRUD (8.2 / SM-D7). 8.4 does NOT re-grant.
- `CategoryAdmin` / `SubcategoryAdmin` — unchanged (8.5 scope, SM-D1); keep their 6.1 `SeoMetaInline`.
- `config/urls.py`, `pyproject.toml` — unchanged (0 deps).

---

## 7. RBAC behavior (AC10 / AC11)

- **Anonymous** → Brand changelist/add/change → 302 redirect to admin login (assert 302; do NOT
  hardcode the URL — admin is at `/admin-coric/`).
- **Editor** (`is_staff`, member of `Editor` group via 8.2 post_migrate) → changelist/add/change → 200;
  can POST-save a valid Brand.
- **Superuser** (`is_superuser`) → same.
- `manage.py check` → 0 serious errors (no `admin.E*`).

---

## 8. Summary (machine-readable)

```yaml
admin_classes:
  - BrandAdmin(SeoWarningAdminMixin, TranslationAdmin)   # form=BrandAdminForm, inlines=[SeoMetaInline, SeriesInline]
  - SeriesAdmin(SeoWarningAdminMixin, ModelAdmin)        # + view_on_site=False, keeps SeoMetaInline
form:
  name: BrandAdminForm
  importable_from: apps.brands.admin
  meta: { model: Brand, exclude: "()", widgets: { brand_color: "TextInput type=color" } }
  init: "brand_color widget type=color ONLY — NO name_sr/name/slug required relaxation (M1)"
  clean_methods: [clean_logo, clean_hero_image, clean_catalog_pdf]   # delegate to media_pipeline helpers; NO publish-gate clean()
  upload_validation: "clean_<field> delegates to validate_image_mime / validate_pdf_mime (DRY + bomb guard — M2)"
  name_sr_semantics: "name_sr unconditionally required; empty -> graceful form error (200), no 400/500; is_coming_soon independent (M1)"
inlines:
  - SeriesInline(TranslationStackedInline)  # model=Series, extra=0, exclude=("slug",)
new_constants:
  - MAX_IMAGE_UPLOAD_SIZE   # 5 * 1024 * 1024
  - MAX_PDF_UPLOAD_SIZE     # 20 * 1024 * 1024
  - ALLOWED_IMAGE_MIME_TYPES  # ("image/jpeg","image/png","image/webp")
  - ALLOWED_PDF_MIME_TYPES    # ("application/pdf",)
key_behaviors:
  - "BrandAdmin is TranslationAdmin (not plain ModelAdmin); per-locale name/description/slogan auto-rendered"
  - "search_fields=('name_sr',) — no FieldError on changelist search"
  - "upload clean_<field> DELEGATE to validate_image_mime/validate_pdf_mime: reject non-image/non-pdf (MIME+Pillow), oversized, decompression-bomb (50M px); accept valid; skip blank (M2/DRY)"
  - "name_sr unconditionally required (model name blank=False); empty name_sr -> graceful 200 form-error on name_sr, no row, never 400/500; is_coming_soon independent flag (M1)"
  - "brand_color widget type=color; invalid hex blocked by Brand.clean() (model single source)"
  - "statistics invalid JSON -> field-level ValidationError, no 500; >4 / non-dict blocked by Brand.clean()"
  - "SeriesInline exclude slug -> name_sr-only inline row saves (slug auto-gen)"
  - "image preview format_html escaped, truthy-guarded; has_pdf boolean indicator"
  - "SeoMetaInline kept on Brand & Series (6.1 regression); SeriesAdmin.view_on_site=False"
  - "Editor AND Superuser CRUD 200; anonymous 302 login; 0 migrations; 0 admin.E*"
```
