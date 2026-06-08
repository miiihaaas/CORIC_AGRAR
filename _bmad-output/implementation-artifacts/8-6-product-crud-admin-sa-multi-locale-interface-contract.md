# 8.6 — Product CRUD Admin sa Multi-locale — Interface Contract (TEA)

Canonical contract Dev MUST satisfy. RED tests: `apps/products/tests/test_8_6_product_crud_admin.py`.
Mirrors 8.4 BrandAdmin (`apps/brands/admin.py`) + 8.5 Category/Subcategory patterns. ONLY edits
`apps/products/admin.py` (+ optional `apps/products/forms.py`). 0 migrations, 0 new deps.

RUN (Docker only — libmagic/python-magic + Pillow + poppler are NOT on the Windows host):
```
just test apps/products/tests/test_8_6_product_crud_admin.py -v
just dev-manage makemigrations products --check --dry-run   # expect "No changes"
```

---

## Module-level constants (in `apps/products/admin.py`)

```python
MAX_IMAGE_UPLOAD_SIZE = 5 * 1024 * 1024    # 5 MB  (NOT media_pipeline MAX_UPLOAD_SIZE_BYTES)
MAX_PDF_UPLOAD_SIZE = 20 * 1024 * 1024     # 20 MB
ALLOWED_IMAGE_MIME_TYPES = ("image/jpeg", "image/png", "image/webp")   # SVG omitted (XSS)
ALLOWED_PDF_MIME_TYPES = ("application/pdf",)
```
Imports: `from apps.media_pipeline.utils import validate_image_mime`,
`from apps.media_pipeline.pdf_utils import validate_pdf_mime`. NEVER reimplement (8.4 M2: inline
duplicate leaked a 121 Mpx PNG bomb). Helpers carry the canonical Serbian messages + the
decompression-bomb guard (`Image.MAX_IMAGE_PIXELS=50M` + `DecompressionBombWarning→error`).

---

## ProductAdmin (the class shape)

```python
@admin.register(Product)
class ProductAdmin(SeoWarningAdminMixin, TranslationAdmin):   # MRO: mixin FIRST (G-2)
    form = ProductAdminForm
    inlines = [
        ProductImageInline, ProductVariantInline, ProductSpecificationInline,
        ProductBrochureInline, ProductTestimonialInline, ProductSimilarInline,
        SeoMetaInline,                                        # 6.1 KEPT (G-8) → 7 total
    ]
    list_display = ("name", "brand", "is_published", "status", "price_eur", "condition")
    list_filter = ("is_published", "status", "brand", "condition")
    search_fields = ("name_sr",)                              # REAL column, NOT virtual `name` (G-1)
    list_select_related = ("brand",)                          # MANDATORY N+1 guard (G-10)
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("created_at", "updated_at", "main_image_preview")
    # view_on_site NOT set False — products:detail IS registered (urls.py:10, SM-D9)
    fieldsets = (...)  # BASE field names only; TranslationAdmin auto-expands _sr/_hu/_en

    @admin.display(description=_("Pregled glavne slike"))
    def main_image_preview(self, obj):
        if obj.main_image:
            return format_html('<img src="{}" style="max-height:120px">', obj.main_image.url)
        return "—"                                            # static em-dash; NEVER raw <field>.url concat (G-15)

    def save_related(self, request, form, formsets, change):  # publish-gate (SM-D5/G-3/G-5/G-6)
        super().save_related(request, form, formsets, change) # FIRST — persists inlines + SeoWarning chain
        instance = form.instance
        publishing = instance.is_published or instance.status == Product.StatusChoice.PUBLISHED
        if not publishing:
            return                                            # draft save NEVER gated
        missing = []
        if not (instance.name_sr or ""):
            missing.append(_("naziv na srpskom"))
        if instance.images.count() == 0:                      # DB COUNT after super() — G-5
            missing.append(_("bar jedna slika galerije"))
        if instance.specifications.count() == 0:
            missing.append(_("bar jedna specifikacija"))
        if missing:
            messages.error(request, _("Za objavljivanje je potrebno: %(items)s.") % {"items": "; ".join(str(m) for m in missing)})
            instance.is_published = False
            instance.status = Product.StatusChoice.DRAFT
            instance.save(update_fields=["is_published", "status"])  # revert; NEVER raise→500 (G-6)
```

Publish-gate rules:
- Gate lives in `save_related` AFTER `super().save_related()` — it counts persisted inline rows via
  `instance.images.count()` / `instance.specifications.count()` (real related_names). Form `clean()`
  has NO inline count (G-5).
- "Published" = `is_published is True` OR `status == "published"` (OR semantics — G-16).
- On failure: `messages.error` + revert BOTH flags to draft via `save(update_fields=[...])`. NEVER
  `raise` (raise from `save_related` → HTTP 500, G-6). Graceful HTTP 200, product stays draft.
- Draft save with 0 images/specs PASSES.

---

## ProductAdminForm + inline forms (upload validators — AC3/G-13/G-14)

`ProductAdminForm(forms.ModelForm)`: `Meta.model = Product`, `Meta.exclude = ()` (G-13 — else
`ImproperlyConfigured` 500). `main_image` overridden to `forms.FileField(required=False)` so Django's
`ImageField.to_python()` Pillow step does NOT pre-empt the Serbian media_pipeline message (G-14).
`clean_main_image` → blank-skip (`if not f: return f`) THEN `validate_image_mime(f, allowed_mimes=..., max_size_bytes=MAX_IMAGE_UPLOAD_SIZE)`.

Inline ModelForms (each set via `form=` on its inline):
| Inline form | Field | Required? | blank-skip | Validator | FileField override |
|---|---|---|---|---|---|
| `ProductImageInlineForm` | `image` | YES (model not blank) | NO — always validate | `validate_image_mime` | YES (G-14, required=True kept) |
| `ProductVariantInlineForm` | `image` | no (blank) | YES `if not f: return f` | `validate_image_mime` | YES |
| `ProductTestimonialInlineForm` | `photo` | no (blank) | YES | `validate_image_mime` | YES |
| `ProductBrochureInlineForm` | `pdf_file` | YES | NO | `validate_pdf_mime` | NO (FileField — no Pillow to_python) |
| `ProductBrochureInlineForm` | `cover_thumbnail_image` | no (blank) | YES | `validate_image_mime` | YES |

HARD RULE (8.4 M2 residual): `validate_image_mime` RAISES on None/empty upload ("Slika je prazna…").
Therefore it MUST NEVER be called unconditionally on a blank-able field. The `if not f: return f`
skip MUST precede the helper call for `main_image`, `variant.image`, `testimonial.photo`,
`cover_thumbnail_image`. Required `ProductImage.image` has NO skip (empty upload on a required field
should fail). Each inline ModelForm needs `Meta.exclude = ()` too (G-13).

REQUIRED-FK NOTE (TEA review fix — divergence from 8.4 Brand which had NO required FK): `Product.brand`
(PROTECT, not null/blank) and the inline models' parent FK (`ProductVariant.product`,
`ProductBrochure.product`, `ProductImage.product`) are REQUIRED on the raw ModelForm when it is bound
DIRECTLY in a test (outside the inline formset, which would otherwise exclude the parent FK). Any
positive-path `form.is_valid() is True` test MUST therefore put the FK pk in `data` (`data["brand"]` /
`data["product"]`). Through the real admin POST the parent FK is supplied by the inline formset, so the
admin-POST publish/draft tests do not need this. Dev does NOT exclude `brand`/`product` — they are
genuine required fields; the test supplies them.

---

## Inline classes (6 domain + SeoMetaInline)

| Inline | Base | model | extra | notes |
|---|---|---|---|---|
| `ProductImageInline` | `TranslationTabularInline` | ProductImage | 0 | `image`/`order`/`alt_text` (alt_text per-locale); `form=ProductImageInlineForm` |
| `ProductVariantInline` | `TranslationStackedInline` | ProductVariant | 0 | `name`/`code`/`image`/`description`/`order`; `form=ProductVariantInlineForm` |
| `ProductSpecificationInline` | `TranslationTabularInline` | ProductSpecification | 0 | `section`/`key`/`value`/`order`; NO upload |
| `ProductBrochureInline` | `TranslationStackedInline` | ProductBrochure | 0 | `pdf_file`/`cover_thumbnail_image`/`title`; `form=ProductBrochureInlineForm` |
| `ProductTestimonialInline` | `TranslationStackedInline` | ProductTestimonial | 0 | `photo`/`quote`/`author_name`/`location`/`order`; `form=ProductTestimonialInlineForm` |
| `ProductSimilarInline` | `admin.TabularInline` (PLAIN — G-12, not translatable) | ProductSimilar | 0 | `fk_name="product"` MANDATORY (two FKs → admin.E202, G-11); `related_product`/`order` |
| `SeoMetaInline` | (6.1, unchanged) | SeoMeta | — | KEPT (G-8) |

`ProductSimilar.clean()` (self-reference) is delegated — admin does NOT re-implement (G-7); surfaces
graceful 200. The bare `admin.site.register(Product*)` lines are REMOVED (the 6 models become inlines).

---

## Summary

- **admin_classes:** `ProductAdmin(SeoWarningAdminMixin, TranslationAdmin)` (mixin first); bare registers removed.
- **inlines:** 7 — 5 Translation* (Image/Variant/Specification/Brochure/Testimonial) + plain `ProductSimilarInline` (fk_name="product") + KEPT `SeoMetaInline`.
- **forms:** `ProductAdminForm` (main_image→FileField, clean_main_image) + 4 inline ModelForms (Image/Variant/Brochure/Testimonial). All `Meta.exclude=()`.
- **validators:** delegate to `validate_image_mime` / `validate_pdf_mime`; blank-skip before helper on every blank-able image/PDF field; required `ProductImage.image` always validated.
- **publish_gate:** in `save_related` after `super()`; counts `images`/`specifications`; messages.error + revert-to-draft (update_fields) on failure; NEVER raise; OR semantics for "published".
- **list_config:** `list_display`(name/brand/is_published/status/price_eur/condition), `list_filter`(is_published/status/brand/condition), `search_fields=("name_sr",)`, `list_select_related=("brand",)`, `prepopulated_fields={"slug":("name",)}`, `view_on_site` left default (registered).
