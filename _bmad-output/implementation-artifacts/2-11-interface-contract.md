# Story 2.11 — Interface Contract (TEA RED phase)

> **Status:** BINDING for Dev (GREEN phase). Defines the exact public surface the
> RED tests in `apps/brands/tests/test_subcategory_listing_*.py` +
> `test_subcategory_get_absolute_url.py` assert against. Derived from the story's
> BINDING SM-D6 (URL signature), SM-D4 (TemplateView), SM-D8 (`get_absolute_url`),
> SM-D9 (breadcrumb), SM-D11/D12 (intermediate-vs-leaf + query budget).
>
> The Test Architect writes the SPECIFICATION here; Dev satisfies it. Do **NOT**
> deviate from these names/signatures — `reverse()`/`resolve()` round-trips and
> template `data-testid` assertions depend on them verbatim.

---

## 1. URL patterns — `apps/brands/urls.py` (EDIT, ADD 3 paths)

Registered **AFTER** the existing static `mehanizacija/prikljucna/`
(`brands:jeegee_prikljucna`) so the Jeegee landing is **not shadowed** (SM-D6).
`app_name = "brands"` (unchanged). All three resolve to `SubcategoryListView`.

| name (namespaced) | path template | kwargs |
|---|---|---|
| `brands:subcategory_listing_category` | `mehanizacija/prikljucna/<slug:category_slug>/` | `category_slug` |
| `brands:subcategory_listing_l1` | `mehanizacija/prikljucna/<slug:category_slug>/<slug:l1_slug>/` | `category_slug`, `l1_slug` |
| `brands:subcategory_listing_l2` | `mehanizacija/prikljucna/<slug:category_slug>/<slug:l1_slug>/<slug:l2_slug>/` | `category_slug`, `l1_slug`, `l2_slug` |
| `brands:subcategory_listing_l3` | `mehanizacija/prikljucna/<slug:category_slug>/<slug:l1_slug>/<slug:l2_slug>/<slug:l3_slug>/` | `category_slug`, `l1_slug`, `l2_slug`, `l3_slug` |

> **4th pattern — `subcategory_listing_category` (BINDING, added in GREEN):** the bare
> `<category_slug>/` route renders the **category-root intermediate** listing (top-level
> Subcategories with `parent=None`, per SM-D11) and is the reverse target for the AC9
> Jeegee-landing `_category_showcase.html` CTA (`{% url 'brands:subcategory_listing_category' category_slug=category.slug %}`).
> It resolves the AC9 single-slug ambiguity SM-D6 left to the Dev. The view's
> `current is None` branch handles it; covered by `TestSubcategoryListingCategoryRoot`
> (200 + top-level cards + breadcrumb-current + empty-state).

Wait — kwarg count rule (BINDING, matches AC8 / SM-D8, no off-by-one):

- `subcategory_listing_l1` URL has **2** slug segments after `prikljucna/`:
  `<category_slug>/<l1_slug>/`. kwargs = `{category_slug, l1_slug}`. Maps to a
  **depth-1** Subcategory (`parent=None`): `category_slug` + 1 subcat slug.
- `subcategory_listing_l2` URL has **3** slug segments:
  `<category_slug>/<l1_slug>/<l2_slug>/`. kwargs = `{category_slug, l1_slug, l2_slug}`.
  Maps to **depth-2** Subcategory: `category_slug` + 2 subcat slugs.
- `subcategory_listing_l3` URL has **4** slug segments:
  `<category_slug>/<l1_slug>/<l2_slug>/<l3_slug>/`. kwargs =
  `{category_slug, l1_slug, l2_slug, l3_slug}`. Maps to **depth-3** Subcategory:
  `category_slug` + 3 subcat slugs.

> **Naming convention note (BINDING):** `lN` in the pattern name == the
> Subcategory `get_depth()` it renders == the number of **subcategory** slug
> kwargs (NOT counting `category_slug`). `l1`→1 subcat slug, `l2`→2, `l3`→3.
> `category_slug` is always present and is never counted toward `N`.

**Depth cap (AC3/AC13):** there is intentionally **no** `_l4` pattern. A URL with
4+ subcategory segments after `<category_slug>` (5+ total slug segments) has no
matching pattern → Django returns **404** at the URL layer, independent of model
`clean()`. Tests assert this via a literal 4-deep path string.

**No collision:** new paths are all `mehanizacija/prikljucna/<category_slug>/...`;
they do not collide with `traktori/<slug:slug>/` (brands `detail`),
`proizvod/<slug>/` / `traktori/` / `mehanizacija/polovna/` (products app, included
before brands).

`SubcategoryListView` must be added to the import in `apps/brands/urls.py`.

---

## 2. View — `apps/brands/views.py` (EDIT, ADD class)

```python
class SubcategoryListView(TemplateView):
    template_name = "brands/subcategory_listing.html"
```

- Base class: `django.views.generic.TemplateView` (SM-D4). `view_class` attribute
  on the resolved match must be `SubcategoryListView` (tests assert
  `resolve(...).func.view_class is SubcategoryListView`).
- Existing `BrandDetailView` + `JeegeePrikljucnaView` remain **untouched**.
- Import edit: add `Subcategory` to `from apps.brands.models import Brand, Category, Series`
  → `... Brand, Category, Series, Subcategory`. Reuse existing `Product` import +
  existing `Http404` import (SM-D13/D16 read-only cross-boundary).

### Resolution algorithm (BINDING)

1. **Category root (AC2):** `Category.objects.get(slug=category_slug, is_for=Category.CategoryScope.MEHANIZACIJA)`.
   `DoesNotExist` (missing OR wrong scope, e.g. `is_for=TRAKTORI`) → `raise Http404`.
2. **Chain (AC3):** for each subcat slug kwarg in order (`l1_slug`, then `l2_slug`,
   then `l3_slug` if present):
   - first segment: `Subcategory.objects.get(category=<category>, parent=None, slug=l1_slug)`
   - each subsequent segment: `Subcategory.objects.get(parent=<prev>, slug=<next>)`
   - any `DoesNotExist` (missing segment, wrong parent, depth mismatch) → `raise Http404`.
     Never render partially.
3. **Intermediate vs leaf (AC4/AC11/AC14 — DATA-DRIVEN, children win):**
   - current node = last resolved Subcategory (or the Category at L1-with-no-subcat... see note).
   - if current node **has children** (`children.exists()` for Subcategory;
     Category root is checked via top-level subcategories) → **INTERMEDIATE**.
   - else → **LEAF**.
   - **Mixed node:** a node having BOTH children AND own `products` → INTERMEDIATE
     (children win; own products ignored at this level).
   - **Category root is ALWAYS intermediate** (SM-D11); empty Category → empty
     intermediate state, never leaf.

### Context contract (`get_context_data`)

| key | type | when | notes |
|---|---|---|---|
| `is_leaf` | `bool` | always | `False` for intermediate, `True` for leaf |
| `children` | `list[Subcategory]` | intermediate | ordered `display_order, name`; materialized list |
| `products` | iterable/QS of `Product` | leaf | `Product.objects.filter(subcategory=<leaf>, is_published=True).select_related("brand")` ordered deterministically |
| `breadcrumb_items` | `list[dict]` | always | see §5 |
| `current_title` | `str` | always | `Category.name` at L1-empty edge, else current Subcategory `name`; rendered in the single `<h1>` |

> **Note (L1 with no subcategories):** at `subcategory_listing_l1` the URL always
> carries an `l1_slug`, so the resolved node is a Subcategory, not the Category.
> The "Category root is always intermediate" rule (SM-D11) is exercised through
> the breadcrumb (Category is always a link) and through a Subcategory L1 node that
> itself has children. The empty-Category case is reachable only if a Subcategory
> L1 node has neither children nor products (renders leaf empty-state) — which is
> the data-driven outcome. Dev MAY additionally support a bare category root, but
> the RED suite only requires the `_lN` patterns above.

### Query budget (AC10 — RED ceiling, SM-D12)

- Intermediate render: `assertNumQueries` **≤ 4**.
- Leaf render: `assertNumQueries` **≤ 4**.
- Dev tightens to exact value after GREEN iteration 1.

---

## 3. Model method — `apps/brands/models.py` (EDIT, implement `Subcategory.get_absolute_url`)

Replace the current `raise NotImplementedError(...)` (lines ~411-414) with an
implementation that:

- computes `depth = self.get_depth()` (existing helper; 1/2/3),
- builds `slugs = [a.slug for a in self.get_ancestors_chain()] + [self.slug]`
  (root-first ancestors + self; `len(slugs) == depth`),
- selects pattern `subcategory_listing_lN` where `N == depth`,
- calls `reverse(f"brands:subcategory_listing_l{depth}", kwargs={...})` where kwargs
  are `{"category_slug": self.category.slug, "l1_slug": slugs[0], ...}` filling
  `l1_slug..lN_slug` from `slugs` in order.

**Round-trip (AC8, BINDING):** for depth 1, 2, AND 3,
`resolve(subcat.get_absolute_url())` returns a match whose `view_class is
SubcategoryListView` and whose `kwargs` reproduce `category_slug` + exactly
`depth` subcategory slugs identifying the same Subcategory. No new migration
(method, not a field). The `NotImplementedError` is removed.

---

## 4. Templates (5 NEW + 1 EDIT)

| path | type | key markup contract |
|---|---|---|
| `templates/brands/subcategory_listing.html` | NEW | `{% extends "base.html" %}`; outer `<section class="coric-subcategory-listing" data-testid="subcategory-listing-page" aria-labelledby="subcategory-listing-title">`; renders `_breadcrumb.html` **before** the single `<h1 id="subcategory-listing-title">{{ current_title }}</h1>`; then `{% if is_leaf %}{% include "brands/partials/_model_grid.html" %}{% else %}{% include "brands/partials/_subcategory_showcase.html" %}{% endif %}`. Exactly one `<h1>`. No inline `style=`. |
| `templates/brands/partials/_breadcrumb.html` | NEW | `<nav aria-label="..." data-testid="breadcrumb-nav"><ol>...`; iterate `breadcrumb_items`; non-current item → `<a href>`; current item → not a link, `aria-current="page"` + `data-testid="breadcrumb-current"`. |
| `templates/brands/partials/_subcategory_showcase.html` | NEW | Section eyebrow + grid; per child `<article class="coric-category-card" data-testid="subcategory-card-{{ subcategory.slug }}">` with title `{{ subcategory.name }}`, optional icon/desc, CTA `<a class="coric-category-card__cta" href="{{ subcategory.get_absolute_url }}" data-testid="subcategory-card-cta-{{ subcategory.slug }}" aria-label="...{{ name }}...">`. `{% empty %}` → "Nema dostupnih potkategorija." |
| `templates/brands/partials/_model_grid.html` | NEW | Section eyebrow + grid; per product `<article class="coric-product-card" data-testid="model-card-{{ product.slug }}">` wrapping `<a href="{{ product.get_absolute_url }}">` (→ products:detail), `responsive_picture(main_image)` if present, `{{ product.name }}`, deterministic spec fields (`horse_power` + " KS" if not null; `price_eur` if not null; both null → no spec field), CTA aria-label. `{% empty %}` → "Nema dostupnih modela u ovoj kategoriji." |
| `templates/brands/partials/_category_showcase.html` | **EDIT (AC9)** | Replace placeholder `href="/{{ LANGUAGE_CODE }}/mehanizacija/prikljucna/{{ category.slug }}/"` with `href="{% url 'brands:subcategory_listing_l1' category_slug=category.slug l1_slug=... %}"` — **see AC9 note below**. |

### AC9 refactor note (BINDING, important)

`subcategory_listing_l1` requires **both** `category_slug` AND `l1_slug`. The
Jeegee landing CTA points at a **Category root** (`/mehanizacija/prikljucna/<category-slug>/`),
which has only one slug. The story text shows `{% url 'brands:subcategory_listing_l1' category_slug=category.slug %}`
(single kwarg), but that is a `NoReverseMatch` against the BINDING SM-D6 signature
(`l1` needs 2 slugs). **Resolution for Dev (the contract the RED regression test
enforces):** the resulting rendered href MUST still equal
`/sr/mehanizacija/prikljucna/<category-slug>/` so Story 2-10
`test_jeegee_prikljucna_templates.py::test_category_card_has_cta_href` stays green.

Dev satisfies this by **either**:
(a) keeping a `{% url %}`-based href that produces that exact path — e.g. register
the L1 category-root reverse so a single-slug reverse yields the category path
(the cleanest reading of AC9/SM-D10 intent: the L1 drill = category root listing), **or**
(b) any reverse that yields the identical path.

The RED test for AC9 (`test_category_showcase_href_uses_url_tag` +
`test_category_showcase_href_path_unchanged`) asserts: (1) the partial source no
longer contains the hardcoded `LANGUAGE_CODE` placeholder string and uses a
`{% url %}` tag, and (2) the rendered Jeegee page still contains
`/mehanizacija/prikljucna/osnovna-obrada-zemljista/`. Dev MUST reconcile the
single-slug category-root case with the `_l1` signature (this is the one genuine
ambiguity SM-D6 left for Dev; the test pins the observable outcome, not the
mechanism).

---

## 5. `breadcrumb_items` shape (AC7, SM-D9)

Root-first `list[dict]`; each dict:

```python
{"label": str, "url": str | None, "is_current": bool}
```

Order for a node at chain depth N:
1. `{"label": _("Početna"), "url": reverse("core:home"), "is_current": False}`
2. `{"label": _("Priključna mehanizacija"), "url": reverse("brands:jeegee_prikljucna"), "is_current": False}`
3. `{"label": category.name, "url": <category root listing>, "is_current": False}`
4. one entry per ancestor Subcategory (`get_ancestors_chain()`, root-first),
   each `{"label": ancestor.name, "url": ancestor.get_absolute_url(), "is_current": False}`
5. current node: `{"label": current.name, "url": None, "is_current": True}`

Partial renders non-current as `<a href>`, current as plain text with
`aria-current="page"`.

---

## 6. Static assets

| path | type | contract |
|---|---|---|
| `static/css/components/breadcrumb.css` | NEW | contains BEM selectors `.coric-breadcrumb`, `.coric-breadcrumb__item` (or `__link`/`__current`); uses `var(--` tokens; no hardcoded color hex required (token-only). |
| `static/css/main.css` | EDIT | add `@import url('./components/breadcrumb.css');` after the existing `category-showcase.css` import. |
| `static/css/components/category-showcase.css` | **NO-EDIT guard** | must still exist + contain `.coric-category-card`. |
| `static/css/components/tractor-listing.css` | **NO-EDIT guard** | must still exist + contain `.coric-product-card`. |

---

## 7. Test factory additions

`apps/brands/tests/factories.py` (EDIT): add `SubcategoryFactory` with
`category` (auto via `CategoryFactory` if omitted) + optional `parent` kwarg for
chaining. Respects model `clean()` depth ≤ 3. `display_order`/`name`/`slug`
overridable; slug auto-gen from name via `Subcategory.save()`.

Reuses: `CategoryFactory` (brands, Story 2-10), `ProductFactory` (products,
accepts `subcategory=`, `is_published=`, `horse_power=`, `price_eur=`,
`name=` overrides).

---

## 8. i18n strings (locale .po EDIT ×3 — sr/hu/en)

New msgids introduced by templates/view: `Početna`, `Priključna mehanizacija`,
intermediate/leaf empty-states (`Nema dostupnih potkategorija.`,
`Nema dostupnih modela u ovoj kategoriji.`), eyebrow texts, CTA labels, breadcrumb
`aria-label`, `KS` (already exists). All user-facing strings via
`{% translate %}` / `{% blocktranslate %}` / `gettext_lazy`.

---

## 9. Summary (machine-readable)

- **urls:** `brands:subcategory_listing_l1`, `brands:subcategory_listing_l2`, `brands:subcategory_listing_l3`
- **views:** `SubcategoryListView` (TemplateView)
- **models:** `Subcategory.get_absolute_url()` (depth→`l{N}`→`category_slug` + N subcat slugs)
- **context:** `is_leaf`, `children`, `products`, `breadcrumb_items`, `current_title`
