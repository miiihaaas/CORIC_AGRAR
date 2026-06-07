# Interface Contract — Story 8.5: Category + Subcategory CRUD sa Hierarchy

**Status:** RED phase (TEA) — DEFINES the contract Dev must satisfy to GREEN.
**Module:** `apps/brands` (admin-only change). **Migrations:** 0. **New deps:** 0.
**Canonical tests:** `apps/brands/tests/test_category_subcategory_crud_admin.py`
**Story:** `8-5-category-subcategory-crud-sa-hierarchy.md` (AC1-AC11, SM-D1..D8, G-1..G-13).

> THE ONLY FILE Dev edits: `apps/brands/admin.py` — the `CategoryAdmin` and
> `SubcategoryAdmin` blocks (currently `SeoWarningAdminMixin + admin.ModelAdmin`
> stubs with `inlines=[SeoMetaInline]`). `BrandAdmin`/`SeriesAdmin` (8.4) stay
> UNTOUCHED. No model changes, no migrations, no new dependencies, no custom
> form, no public URLs.

---

## 1. CategoryAdmin

Convert the stub into a `TranslationAdmin` subclass while preserving the 6.1 SEO inline.

```python
@admin.register(Category)
class CategoryAdmin(SeoWarningAdminMixin, TranslationAdmin):  # MRO: mixin FIRST (G-2)
    inlines = [SeoMetaInline]                         # 6.1 regression KEPT (G-8)
    view_on_site = False                              # MANDATORY (G-3/AC9) — see note
    list_display = ("name", "is_for", "display_order", "slug")  # name FIRST = link (G-9)
    list_editable = ("display_order",)                # G-9: name NOT here, is the link
    list_filter = ("is_for",)
    search_fields = ("name_sr",)                      # REAL column, NOT virtual `name` (G-1)
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (_("Osnovno"), {"fields": ("name", "slug", "is_for", "display_order", "icon")}),
        (_("Sadržaj"), {"fields": ("description",)}),
        (_("Meta"), {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )
```

**Key constraints**
- **`TranslationAdmin`** (NOT plain `ModelAdmin`) — modeltranslation AUTO-expands per-locale `name_*`/`description_*` from the BASE field names in `fieldsets`. Never enumerate `name_sr`/`name_hu`/`name_en` manually.
- **`view_on_site = False` MANDATORY (G-3/AC9):** `Category.get_absolute_url` reverses `brands:category_traktori` / `brands:category_mehanizacija`, which are **NOT registered** in `apps/brands/urls.py` (confirmed: `apps/search/views.py` already wraps the call in `try/except NoReverseMatch`). Without the guard, the "View on site" affordance throws `NoReverseMatch` → HTTP 500. Defensive guard — revisit when those public URLs are registered (out of 8.5 scope).
- **`search_fields = ("name_sr",)` (G-1):** the registered `name` is a virtual modeltranslation field — `search_fields=("name",)` raises `FieldError` on the FIRST changelist search query (NOT caught by `manage.py check`). Use the real column.
- **`list_editable` + `list_display_links` (G-9):** `display_order` IS in `list_display` and IS in `list_editable`; `name` is first in `list_display`, is the clickable change link, and is NOT in `list_editable`. Otherwise `admin.E124`/`admin.E125`.
- `is_for` is REQUIRED (model `blank=False`, no default — SM-D7). `name_sr` is REQUIRED (model `name` `blank=False` + sr default locale — G-11). Neither is relaxed; empty → graceful 200 form error.
- `list_select_related` NOT needed on Category (no FK columns in `list_display`; `__str__` uses `get_is_for_display()` = in-memory choices, no query — G-10).

---

## 2. SubcategoryAdmin

```python
@admin.register(Subcategory)
class SubcategoryAdmin(SeoWarningAdminMixin, TranslationAdmin):  # MRO: mixin FIRST (G-2)
    inlines = [SeoMetaInline]                         # 6.1 regression KEPT (G-8)
    view_on_site = False                              # MANDATORY (G-3/AC9) — see note
    list_display = ("name", "category", "parent", "display_order", "slug")  # name FIRST (G-9)
    list_editable = ("display_order",)
    list_filter = ("category",)                       # optional: + "parent" (OQ-3)
    search_fields = ("name_sr",)                      # REAL column (G-1)
    prepopulated_fields = {"slug": ("name",)}
    list_select_related = ("category", "parent")      # N+1 guard for FK columns (G-10)
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (_("Hijerarhija"), {"fields": ("category", "parent")}),
        (_("Osnovno"), {"fields": ("name", "slug", "display_order", "icon")}),
        (_("Sadržaj"), {"fields": ("description",)}),
        (_("Meta"), {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )
```

**Key constraints**
- **`view_on_site = False` MANDATORY (G-3/AC9):** `Subcategory.get_absolute_url` reverses `brands:subcategory_listing_l{depth}`, registered ONLY for the mehanizacija/prikljucna branch — other branches throw `NoReverseMatch` → 500.
- **`category` / `parent` = default FK `<select>` widget.** NO custom `SubcategoryAdminForm` (SM-D4 / OQ-2 — model `clean()` is sufficient; less code, less risk). If Dev ever adds one, `Meta.exclude = ()` or `Meta.fields` is MANDATORY (G-12).
- **`list_select_related = ("category", "parent")` (G-10):** `list_display` has two FK columns; without this each changelist row issues extra queries for `__str__`.
- **Hierarchy validation is DELEGATED to `Subcategory.clean()` (SM-D4 / G-5/G-7).** The admin re-implements NOTHING. `clean()` (models.py:365-396) already enforces depth ≤ 3 (`_SUBCATEGORY_MAX_DEPTH=3`) and the cycle guard (`visited_ids`). The admin ModelForm calls `full_clean()`, so those `ValidationError`s surface as non-field (`__all__`) form errors and re-render the form at **HTTP 200 — never 500**.
- **Slug uniqueness is per-scope (G-6):** `UniqueConstraint(category, parent, slug)` — NOT globally unique. Same `name`/slug under DIFFERENT `(category, parent)` is VALID; under the SAME scope → constraint violation surfaced graceful (200). The admin adds NO custom slug-uniqueness logic.
- `name_sr` REQUIRED (G-11). `category` REQUIRED (FK, no null). `parent` optional (nullable root).

---

## 3. Contract summary table

| Aspect | CategoryAdmin | SubcategoryAdmin |
|---|---|---|
| Base class | `SeoWarningAdminMixin, TranslationAdmin` | `SeoWarningAdminMixin, TranslationAdmin` |
| Inlines | `[SeoMetaInline]` | `[SeoMetaInline]` |
| `view_on_site` | `False` | `False` |
| `search_fields` | `("name_sr",)` | `("name_sr",)` |
| `list_display` (incl.) | `name`, `is_for`, `display_order`, `slug` | `name`, `category`, `parent`, `display_order`, `slug` |
| `list_editable` | `("display_order",)` | `("display_order",)` |
| `list_filter` | `("is_for",)` | `("category",)` |
| `list_display_links` link | `name` (default first, not editable) | `name` (default first, not editable) |
| `prepopulated_fields` | `{"slug": ("name",)}` | `{"slug": ("name",)}` |
| `list_select_related` | — (not needed) | `("category", "parent")` |
| `readonly_fields` | `created_at`, `updated_at` | `created_at`, `updated_at` |
| Custom form | NONE | NONE (SM-D4) |
| Hierarchy/cycle/slug validation | n/a | DELEGATED to `Subcategory.clean()` + DB constraint |

---

## 4. Behaviors Dev must satisfy (mapped to ACs)

1. **AC1** — Both admins are `TranslationAdmin`; changelist/add/change render 200 for superuser AND Editor; `search_fields=("name_sr",)` causes no runtime `FieldError`; `manage.py check` → 0 `admin.E*` (incl. the `list_editable`/`list_display_links` trap).
2. **AC2 (depth)** — `Category → L1 → L2 → L3` created via sequential admin POSTs all succeed; an `L4` POST (parent chain depth 4) is rejected graceful (200 re-render, non-field error "…ne sme prelaziti 3 nivoa dubine."), NO row, NEVER 500. Admin delegates to `Subcategory.clean()`.
3. **AC3 (cycle)** — change-form POST. (a) **self-ref** (existing B → parent=B) → 200 form error "…ne sme imati cikličnu referencu.", NEVER 500 — this is the REAL cycle-rejection lock (model `clean()` line 380 explicit `pk == self.pk` pre-check survives the admin DB-reload path). (b) **2-node loop** (A parent=None, B parent=A, then A → parent=B) → handled **GRACEFULLY (200 re-render OR 302), NEVER 400/500**. ⚠️ **TEA REVIEW FINDING:** rejecting the 2-node loop via the admin POST is UNSATISFIABLE without a model change (forbidden — AC11). `Subcategory.clean()`'s `visited_ids` loop guard only fires when the in-memory object graph is wired; the admin assigns `instance.parent=<fresh B>` whose `.parent` lazily loads a fresh A from the DB with `parent_id=None` (cycle not yet persisted) → the walk terminates, `full_clean()` passes, the POST SAVES (302). This is a PRE-EXISTING model-clean gap (inherited from 2-1, sibling of the OQ-5 cross-category and G-13 null-parent gaps) → flag for a future model-validation story, NOT 8.5's job. The 8.5 contract for the 2-node-via-admin path is only "graceful, no 500"; the self-ref test carries the cycle-rejection discriminator. (New/unsaved obj `pk is None` → direct self-ref unreachable on add; cycle only on CHANGE.)
4. **AC4 (display_order)** — `display_order` is in `list_editable`; changelist bulk reorder persists; `name` is the change-link and is NOT in `list_editable`.
5. **AC5 (icon)** — `icon` (plain text CharField) editable in change form; blank allowed. No icon-picker widget.
6. **AC6 (delete)** — Category delete cascades to its Subcategories (confirmation page lists them, 200). Deleting a Subcategory that has a `Product` with `subcategory` explicitly set → Django "protected" page (200, blocked, Product NOT deleted), NEVER 500. Django gives this for free; admin adds no custom delete.
7. **AC7 (listing)** — `list_display`/`list_filter` as in the table; FK columns render via `__str__`; no N+1 panic (`list_select_related` on Subcategory).
8. **AC8 (slug)** — `prepopulated_fields` slug; `Category.save()`/`Subcategory.save()` auto-gen slug from `name`. Duplicate explicit slug under SAME `(category, parent)` (non-null parent) → graceful 200 error; under DIFFERENT scope → allowed. (G-13: null-parent duplicate slug is NOT caught on Postgres — NULL is DISTINCT — accepted v1 gap, NOT 8.5's job to fix.)
9. **AC9 (view_on_site)** — Both `view_on_site is False`; both change-views render 200 (no NoReverseMatch).
10. **AC10 (RBAC)** — anon → 302 admin login; Editor (8.2 group, untouched) and superuser can add/change both models. 8.5 does NOT touch `permissions.py`.
11. **AC11 (no migrations / regression)** — `makemigrations brands --check` = No changes; `BrandAdmin`/`SeriesAdmin` untouched; 6.1 `test_seometa_admin_inline.py` stays green.

---

## 5. Notes for Dev

- **Auth in tests uses `force_login`** (NOT `client.login` — django-axes from 8.1 pollutes lockout state). Admin is at bare `/admin-coric/`; tests always `reverse("admin:brands_category_*")` / `..._subcategory_*`, never hardcode.
- **Editor user** = `is_staff` + member of the `Editor` group, created by the 8.2 `sync_rbac_groups` post_migrate handler during test-DB setup, already carrying brands CRUD (`EDITOR_CONTENT_MODELS`). 8.5 does NOT re-grant (SM-D8).
- **Dependency-order fixtures (CRITICAL):** depth and cascade-delete fixtures MUST be built Category → L1 → L2 → L3 in order (each `parent` requires the prior level to exist) or an `IntegrityError` from the wrong cause masks the real assert.
- **PROTECT fixture must set `subcategory` explicitly:** `Product.subcategory` is `null=True, blank=True` PROTECT — a Product with `subcategory=None` does NOT trigger PROTECT (false-green). The protected-delete test creates `ProductFactory.create(subcategory=<target>)`.
- **No-JS duplicate-slug test (G-11/G-13):** `prepopulated_fields` JS does NOT run in the no-JS POST scraper — duplicate-slug tests POST the SAME explicit `slug` (+ same `name_sr`), never relying on auto-gen collision.
- **Both `view_on_site = False`** — Category because `category_traktori`/`category_mehanizacija` are unregistered; Subcategory because `subcategory_listing_l*` is registered only on one branch.
- **No custom form, no depth/cycle re-implementation in admin** — `Subcategory.clean()` is the single source of truth.
