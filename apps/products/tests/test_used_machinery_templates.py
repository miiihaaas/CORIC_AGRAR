"""Story 2.9 — Templates + partials structural tests (RED phase TDD).

Pokriva AC3 (template structure, single h1, single main, semantic HTML5 section order;
NEMA brand header sekcije — različito od Story 2.8) + AC4 (filter form: 2 dropdown +
2 slider + 1 sort + stanje hidden input SM-D26) + AC5 (results grid wrapper id="used-results",
coric-product-card BEM reuse, year display SM-D12) + AC6 (empty state copy verbatim
iz epics.md FR-13) + AC7 (REUSE vendor noUiSlider + tractor-filters.js refs) +
cross-cutting (no inline styles, no Cyrillic).

Test scope (~22 tests):
- AC3 template structure: 5 testa (single h1, single main, outer section, section order, NO brand header)
- AC4 filter form structure: 7 testa (2 dropdowns, 2 sliders, 1 sort, 1 stanje hidden, HTMX attrs, RESETUJ FILTERE, no csrf, label-for)
- AC5 results grid: 4 testa (wrapper id, coric-product-card BEM, year display, linkable card with aria-label)
- AC6 empty state: 3 testa (title verbatim, CTA verbatim, CTA link to tractor_list)
- AC7 vendor + JS refs: 2 testa (noUiSlider <link> + <script>, tractor-filters.js)
- Cross-cutting: 2 testa (no inline styles, no Cyrillic)

Pokrenuti sa:
    docker compose -f compose/local.yml exec django uv run pytest \\
        apps/products/tests/test_used_machinery_templates.py -v

Refs:
- 2-9-used-machinery-listing-sa-filterima.md (AC3-AC7 + SM-D12/D16/D17/D23/D26)
- 2-9-interface-contract.md § 3 + § 6
"""

from __future__ import annotations

import pathlib
import re
from decimal import Decimal

import pytest
from django.utils.translation import activate

from apps.brands.tests.factories import BrandFactory
from apps.products.tests.factories import UsedProductFactory

pytestmark = pytest.mark.django_db

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[3]


# =============================================================================
# AC3 — Template structure: single h1, single main, section order
# =============================================================================


def test_ac3_single_h1_element(client):
    """AC3: render-uje TAČNO 1 `<h1>` element ('Polovna mehanizacija'); sve ostale sekcije h2/h3."""
    activate("sr")
    BrandFactory.create()
    UsedProductFactory.create(name="H1 Test")

    response = client.get("/sr/mehanizacija/polovna/", HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    h1_count = len(re.findall(r"<h1\b", html, re.IGNORECASE))
    assert h1_count == 1, (
        f"Used machinery listing MORA imati TAČNO 1 `<h1>` (UX/SEO single-h1 rule), "
        f"dobio {h1_count}. Page heading je 'Polovna mehanizacija' "
        "(id='used-machinery-listing-title')."
    )


def test_ac3_single_main_element(client):
    """AC3: render-uje TAČNO 1 `<main>` element (base.html provider; outer wrapper je
    `<section>` NIJE drugi `<main>`). Regression guard mirror Story 2.7+2.8.
    """
    activate("sr")
    BrandFactory.create()
    UsedProductFactory.create(name="Main Test")

    response = client.get("/sr/mehanizacija/polovna/", HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    main_count = len(re.findall(r"<main\b", html, re.IGNORECASE))
    assert main_count == 1, (
        f"Used machinery listing MORA imati TAČNO 1 `<main>` element. Dobio {main_count}."
    )


def test_ac3_outer_section_has_data_testid_used_machinery_listing_page(client):
    """AC3: outer wrapper je `<section class="coric-used-machinery-listing"
    data-testid="used-machinery-listing-page">`.
    """
    activate("sr")
    BrandFactory.create()
    UsedProductFactory.create(name="Outer Section Test")

    response = client.get("/sr/mehanizacija/polovna/", HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    pattern_a = re.compile(
        r'<section[^>]*class="[^"]*coric-used-machinery-listing[^"]*"[^>]*data-testid="used-machinery-listing-page"',
        re.IGNORECASE,
    )
    pattern_b = re.compile(
        r'<section[^>]*data-testid="used-machinery-listing-page"[^>]*class="[^"]*coric-used-machinery-listing',
        re.IGNORECASE,
    )
    assert pattern_a.search(html) or pattern_b.search(html), (
        "used_machinery_listing.html MORA imati outer `<section "
        "class=\"coric-used-machinery-listing\" data-testid=\"used-machinery-listing-page\">`."
    )


def test_ac3_sections_render_in_correct_order(client):
    """AC3: sekcije renderuju TAČNIM redosledom — page heading (h1) → filter form → results.

    NEMA brand header sekcije (Story 2.9 različito od 2.8 — brendovi su u filter dropdown-u).
    """
    activate("sr")
    BrandFactory.create()
    UsedProductFactory.create(name="Section Order")

    response = client.get("/sr/mehanizacija/polovna/", HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    h1_idx = html.find('id="used-machinery-listing-title"')
    filter_form_idx = html.find('id="used-filters"')
    results_idx = html.find('id="used-results-wrap"')

    assert h1_idx >= 0, "Page heading (#used-machinery-listing-title) MORA postojati."
    assert filter_form_idx >= 0, "Filter form sekcija (#used-filters) MORA postojati."
    assert results_idx >= 0, "Results sekcija (#used-results-wrap) MORA postojati."

    assert h1_idx < filter_form_idx < results_idx, (
        f"Section order BROKEN. Pozicije: h1={h1_idx}, filter_form={filter_form_idx}, "
        f"results={results_idx}. Očekivan: h1 < filter_form < results."
    )


def test_ac3_no_brand_header_section(client):
    """AC3: Story 2.9 NEMA brand header sekciju (različito od Story 2.8) — brendovi su
    u filter dropdown-u, NE kao banner.
    """
    activate("sr")
    BrandFactory.create(name="Brand For Header Check")
    UsedProductFactory.create(name="No Brand Header")

    response = client.get("/sr/mehanizacija/polovna/", HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    # Story 2.8 koristi #brand-header — NE SME biti u Story 2.9 template-u
    assert 'id="brand-header"' not in html, (
        "Story 2.9 NEMA brand header sekciju (#brand-header) — različito od Story 2.8. "
        "Brendovi su u filter dropdown-u, NE banner."
    )
    # Stari Story 2.8 testid takođe ne sme biti tu
    assert 'data-testid="brand-header-grid"' not in html


# =============================================================================
# AC4 — Filter form: 2 dropdown + 2 slider + 1 sort + 1 stanje hidden (SM-D26)
# =============================================================================


def test_ac4_filter_form_has_2_dropdowns_2_sliders_1_sort_and_stanje_hidden_input(client):
    """AC4 + SM-D26: form ima 2 select dropdown filtera (Kategorija, Brend) + 2 range
    slider container-a (Cena, Godina) + 1 sort select dropdown + 1 stanje hidden input.

    Per SM-D26 IMP-6: stanje je hidden input u v1 (NIJE dropdown — jednoopcioni
    dropdown je UX noise).
    """
    activate("sr")
    BrandFactory.create()
    UsedProductFactory.create(name="Form Structure")

    response = client.get("/sr/mehanizacija/polovna/", HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    # Extract filter form content
    form_match = re.search(
        r'<form[^>]*data-testid="used-filter-form"[^>]*>(.*?)</form>',
        html,
        re.IGNORECASE | re.DOTALL,
    )
    assert form_match, "Filter form sa data-testid='used-filter-form' MORA postojati."
    form_content = form_match.group(1)

    # 2 dropdown filtera: Kategorija + Brend (NE računa sort dropdown!)
    assert 'data-testid="filter-kategorija"' in form_content, (
        "Filter form MORA imati `<select data-testid=\"filter-kategorija\">`."
    )
    assert 'data-testid="filter-brend"' in form_content, (
        "Filter form MORA imati `<select data-testid=\"filter-brend\">`."
    )

    # 2 range slider container-a
    slider_containers = re.findall(
        r'<div[^>]*data-range-slider[^>]*>',
        form_content,
        re.IGNORECASE,
    )
    assert len(slider_containers) == 2, (
        f"Filter form MORA imati TAČNO 2 `[data-range-slider]` container-a "
        f"(Cena + Godina), dobio {len(slider_containers)}."
    )

    # 1 sort dropdown
    assert 'data-testid="filter-sort"' in form_content, (
        "Filter form MORA imati `<select data-testid=\"filter-sort\">`."
    )

    # 1 stanje hidden input (SM-D26)
    stanje_pattern = re.compile(
        r'<input[^>]*type="hidden"[^>]*name="stanje"[^>]*value="used"',
        re.IGNORECASE,
    )
    stanje_pattern_alt = re.compile(
        r'<input[^>]*name="stanje"[^>]*value="used"[^>]*type="hidden"',
        re.IGNORECASE,
    )
    stanje_pattern_alt2 = re.compile(
        r'<input[^>]*type="hidden"[^>]*value="used"[^>]*name="stanje"',
        re.IGNORECASE,
    )
    assert (
        stanje_pattern.search(form_content)
        or stanje_pattern_alt.search(form_content)
        or stanje_pattern_alt2.search(form_content)
    ), (
        "Filter form MORA imati `<input type=\"hidden\" name=\"stanje\" value=\"used\">` "
        "(SM-D26 IMP-6 — stanje je hidden input u v1, NIJE dropdown)."
    )
    assert 'data-testid="filter-stanje"' in form_content


def test_ac4_filter_form_has_correct_htmx_attributes(client):
    """AC4: filter form MORA imati hx-get, hx-trigger sa debounce, hx-target=#used-results,
    hx-swap=innerHTML, hx-push-url=true, hx-indicator=#used-filter-loading.
    """
    activate("sr")
    BrandFactory.create()
    UsedProductFactory.create(name="HTMX Attrs")

    response = client.get("/sr/mehanizacija/polovna/", HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    form_match = re.search(
        r'<form[^>]*data-testid="used-filter-form"[^>]*>',
        html,
        re.IGNORECASE,
    )
    assert form_match, "Filter form data-testid='used-filter-form' MORA postojati."
    form_tag = form_match.group(0)

    assert "hx-get" in form_tag, f"Form MORA imati hx-get atribut. Form: {form_tag!r}."
    assert "delay:300ms" in form_tag, f"Form MORA imati `delay:300ms`. Form: {form_tag!r}."
    assert "input changed" in form_tag, f"Form MORA listening `input changed`. Form: {form_tag!r}."
    assert 'hx-target="#used-results"' in form_tag
    assert 'hx-swap="innerHTML"' in form_tag
    assert 'hx-push-url="true"' in form_tag
    assert 'hx-indicator="#used-filter-loading"' in form_tag


def test_ac4_filter_form_has_no_csrf_token(client):
    """AC4: GET form NE SME imati `{% csrf_token %}` (Django CSRF only POST/PUT/DELETE/PATCH)."""
    activate("sr")
    BrandFactory.create()
    UsedProductFactory.create(name="No CSRF")

    response = client.get("/sr/mehanizacija/polovna/", HTTP_HOST="localhost")
    html = response.content.decode("utf-8")

    form_match = re.search(
        r'<form[^>]*data-testid="used-filter-form"[^>]*>(.*?)</form>',
        html,
        re.IGNORECASE | re.DOTALL,
    )
    assert form_match
    form_content = form_match.group(1)
    assert "csrfmiddlewaretoken" not in form_content, (
        "GET filter form NE SME sadržati csrfmiddlewaretoken (CSRF samo POST). "
        "Anti-pattern: copy-paste CSRF na GET form je dead code."
    )


def test_ac4_filter_form_reset_cta_is_anchor_full_reload(client):
    """AC4 + SM-D6: RESETUJ FILTERE CTA je `<a href="{% url 'products:used_machinery_list' %}">`
    full reload, NIJE HTMX-trigger.
    """
    activate("sr")
    BrandFactory.create()
    UsedProductFactory.create(name="Reset CTA")

    response = client.get("/sr/mehanizacija/polovna/", HTTP_HOST="localhost")
    html = response.content.decode("utf-8")

    reset_match = re.search(
        r'<(a|button)[^>]*data-testid="reset-filters-button"[^>]*>',
        html,
        re.IGNORECASE,
    )
    assert reset_match, "Reset CTA data-testid='reset-filters-button' MORA postojati."
    tag_name = reset_match.group(1).lower()
    tag = reset_match.group(0)

    assert tag_name == "a", (
        f"RESETUJ FILTERE CTA MORA biti `<a>` (SM-D6 full reload), dobio `<{tag_name}>`."
    )
    assert 'href="/sr/mehanizacija/polovna/"' in tag, (
        f"Reset CTA MORA imati `href=\"/sr/mehanizacija/polovna/\"`. Tag: {tag!r}."
    )
    assert "hx-get" not in tag, (
        f"Reset CTA NE SME imati `hx-get` (SM-D6 terminal action je full reload, NE HTMX). Tag: {tag!r}."
    )


def test_ac4_dropdown_filters_have_label_for_a11y(client):
    """AC4 + a11y SC 1.3.1: svaki vidljivi `<select>` ima `<label for="filter-...">`."""
    activate("sr")
    BrandFactory.create()
    UsedProductFactory.create(name="Label For Test")

    response = client.get("/sr/mehanizacija/polovna/", HTTP_HOST="localhost")
    html = response.content.decode("utf-8")

    # Mora postojati label for="filter-kategorija", "filter-brend", "filter-sort"
    for select_id in ("filter-kategorija", "filter-brend", "filter-sort"):
        pattern = re.compile(
            r'<label[^>]*for="' + re.escape(select_id) + r'"',
            re.IGNORECASE,
        )
        assert pattern.search(html), (
            f"Filter form MORA imati `<label for=\"{select_id}\">` "
            f"(a11y SC 1.3.1). Dropdown bez label-for je inaccessible."
        )


def test_ac4_sort_dropdown_renders_4_options(client):
    """AC4: sort `<select>` ima TAČNO 4 `<option>` (default, cena_asc, cena_desc, godina_desc)."""
    activate("sr")
    BrandFactory.create()
    UsedProductFactory.create(name="Sort Options Count")

    response = client.get("/sr/mehanizacija/polovna/", HTTP_HOST="localhost")
    html = response.content.decode("utf-8")

    # Extract sort select content
    sort_select_match = re.search(
        r'<select[^>]*data-testid="filter-sort"[^>]*>(.*?)</select>',
        html,
        re.IGNORECASE | re.DOTALL,
    )
    assert sort_select_match, "Sort select MORA postojati."
    sort_content = sort_select_match.group(1)
    options = re.findall(r'<option[^>]*value="([^"]*)"', sort_content, re.IGNORECASE)
    assert len(options) == 4, (
        f"Sort dropdown MORA imati TAČNO 4 options, dobio {len(options)}: {options!r}."
    )
    expected = {"default", "cena_asc", "cena_desc", "godina_desc"}
    assert set(options) == expected, (
        f"Sort options MORAJU biti {expected!r}, dobio {set(options)!r}."
    )


# =============================================================================
# AC5 — Results grid wrapper + coric-product-card BEM + year display (SM-D12)
# =============================================================================


def test_ac5_results_wrapper_has_id_used_results(client):
    """AC5 + SM-D17: results grid outer wrapper je `<div id="used-results">`
    (INVARIJANTAN ID — HTMX hx-target referencira ovo).
    """
    activate("sr")
    BrandFactory.create()
    UsedProductFactory.create(name="Wrapper ID")

    response = client.get("/sr/mehanizacija/polovna/", HTTP_HOST="localhost")
    html = response.content.decode("utf-8")

    pattern = re.compile(r'<div[^>]*\bid="used-results"', re.IGNORECASE)
    assert pattern.search(html), (
        "Results grid MORA imati `<div id=\"used-results\">` wrapper "
        "(INVARIJANTAN ID — HTMX hx-target referencira ovo per SM-D17)."
    )


def test_ac5_product_card_uses_coric_product_card_bem(client):
    """AC5: product kartice koriste `coric-product-card` BEM (REUSE iz Story 2.6)."""
    activate("sr")
    brand = BrandFactory.create()
    UsedProductFactory.create(brand=brand, name="BEM Used Test")

    response = client.get("/sr/mehanizacija/polovna/", HTTP_HOST="localhost")
    html = response.content.decode("utf-8")

    assert "coric-product-card" in html, (
        "Product card MORA reuse `coric-product-card` BEM iz Story 2.6 (brand-listing.css). "
        "Story 2.9 NE re-definiše istu BEM."
    )


def test_ac5_product_card_displays_year_with_visually_hidden_prefix(client):
    """AC5 + SM-D12 (WCAG SC 1.3.1): kartica sa product.year prikazuje godinu sa
    visually-hidden „Godina proizvodnje:" prefix za screen reader context.
    """
    activate("sr")
    brand = BrandFactory.create()
    product = UsedProductFactory.create(brand=brand, name="Year Display", year=2018)

    response = client.get("/sr/mehanizacija/polovna/", HTTP_HOST="localhost")
    html = response.content.decode("utf-8")

    # Pronađi card markup
    card_match = re.search(
        r'<a[^>]*data-testid="used-card-' + re.escape(product.slug) + r'"[^>]*>(.*?)</a>',
        html,
        re.IGNORECASE | re.DOTALL,
    )
    assert card_match, f"Used card data-testid='used-card-{product.slug}' MORA postojati."
    card_content = card_match.group(1)

    # Year je u kartici
    assert "2018" in card_content, (
        f"Kartica MORA prikazati product.year=2018. Card content: {card_content[:500]!r}."
    )
    # visually-hidden prefix
    assert "visually-hidden" in card_content, (
        f"Year display MORA imati visually-hidden „Godina proizvodnje:\" prefix "
        f"(SM-D12 WCAG SC 1.3.1). Card content: {card_content[:500]!r}."
    )


def test_ac5_product_card_linkable_with_aria_label(client):
    """AC5: product card je `<a>` wraps card sa aria-label + data-testid="used-card-{slug}"."""
    activate("sr")
    brand = BrandFactory.create()
    product = UsedProductFactory.create(brand=brand, name="Linkable Used", price_eur=Decimal("8000.00"))

    response = client.get("/sr/mehanizacija/polovna/", HTTP_HOST="localhost")
    html = response.content.decode("utf-8")

    expected_testid = f'data-testid="used-card-{product.slug}"'
    assert expected_testid in html

    card_pattern = re.compile(
        r'<a[^>]*data-testid="used-card-' + re.escape(product.slug) + r'"[^>]*>',
        re.IGNORECASE,
    )
    card_match = card_pattern.search(html)
    assert card_match
    card_tag = card_match.group(0)
    assert "aria-label" in card_tag, (
        f"Product card `<a>` MORA imati aria-label (WCAG SC 2.4.4). Tag: {card_tag!r}."
    )


# =============================================================================
# AC6 — Empty state copy verbatim iz epics.md FR-13
# =============================================================================


def test_ac6_empty_state_renders_when_zero_results(client):
    """AC6: empty state markup renderuje kad filter daje 0 rezultata."""
    activate("sr")
    BrandFactory.create()
    # NEMA UsedProductFactory.create — 0 USED proizvoda

    response = client.get("/sr/mehanizacija/polovna/", HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    assert 'data-testid="used-empty-state"' in html, (
        "Empty state markup (data-testid='used-empty-state') MORA biti renderovan "
        "kad 0 USED proizvoda u DB."
    )


def test_ac6_empty_state_title_matches_epics_md_fr13_verbatim(client):
    """AC6: empty state TITLE TAČAN string „Trenutno nemamo polovne mehanizacije u ponudi"
    (EKSPLICITNO iz epics.md FR-13 — Dev NE SME parafrazirati).
    """
    activate("sr")
    BrandFactory.create()

    response = client.get("/sr/mehanizacija/polovna/", HTTP_HOST="localhost")
    html = response.content.decode("utf-8")

    assert "Trenutno nemamo polovne mehanizacije u ponudi" in html, (
        "Empty state title MORA biti TAČAN string „Trenutno nemamo polovne mehanizacije "
        "u ponudi\" (EKSPLICITNO iz epics.md FR-13)."
    )


def test_ac6_empty_state_cta_text_matches_epics_md_fr13_verbatim(client):
    """AC6: empty state CTA TAČAN string „POGLEDAJ NOVE TRAKTORE"
    (EKSPLICITNO iz epics.md FR-13).
    """
    activate("sr")
    BrandFactory.create()

    response = client.get("/sr/mehanizacija/polovna/", HTTP_HOST="localhost")
    html = response.content.decode("utf-8")

    assert "POGLEDAJ NOVE TRAKTORE" in html, (
        "Empty state CTA MORA biti TAČAN string „POGLEDAJ NOVE TRAKTORE\" "
        "(EKSPLICITNO iz epics.md FR-13)."
    )


def test_ac6_empty_state_cta_links_to_tractor_list(client):
    """AC6: empty state CTA href je `/sr/traktori/` (reverse products:tractor_list)
    — full reload, NIJE HTMX swap.
    """
    activate("sr")
    BrandFactory.create()

    response = client.get("/sr/mehanizacija/polovna/", HTTP_HOST="localhost")
    html = response.content.decode("utf-8")

    cta_pattern_a = re.compile(
        r'<a[^>]*data-testid="empty-view-new-tractors-button"[^>]*href="/sr/traktori/"',
        re.IGNORECASE,
    )
    cta_pattern_b = re.compile(
        r'<a[^>]*href="/sr/traktori/"[^>]*data-testid="empty-view-new-tractors-button"',
        re.IGNORECASE,
    )
    assert cta_pattern_a.search(html) or cta_pattern_b.search(html), (
        "Empty state CTA MORA biti `<a href=\"/sr/traktori/\" "
        "data-testid=\"empty-view-new-tractors-button\">`."
    )


# =============================================================================
# AC7 — REUSE vendor noUiSlider + tractor-filters.js refs
# =============================================================================


def test_ac7_template_includes_nouislider_vendor_refs(client):
    """AC7 + SM-D4: template uključuje REUSE vendor noUiSlider CSS+JS iz Story 2.8
    (`static/vendor/nouislider/`).
    """
    activate("sr")
    BrandFactory.create()
    UsedProductFactory.create(name="Vendor Refs")

    response = client.get("/sr/mehanizacija/polovna/", HTTP_HOST="localhost")
    html = response.content.decode("utf-8")

    assert "nouislider.min.css" in html, (
        "Template MORA imati `<link>` za nouislider.min.css (REUSE Story 2.8 vendor)."
    )
    assert "nouislider.min.js" in html, (
        "Template MORA imati `<script>` za nouislider.min.js (REUSE Story 2.8 vendor)."
    )


def test_ac7_template_includes_tractor_filters_js_reuse(client):
    """AC7: template uključuje REUSE `static/js/tractor-filters.js` (Story 2.8 generic IIFE).
    NEMA novi JS modul za Story 2.9 — `tractor-filters.js` radi na bilo kom
    `[data-range-slider]` container-u.
    """
    activate("sr")
    BrandFactory.create()
    UsedProductFactory.create(name="JS Reuse")

    response = client.get("/sr/mehanizacija/polovna/", HTTP_HOST="localhost")
    html = response.content.decode("utf-8")

    assert "js/tractor-filters.js" in html, (
        "Template MORA imati `<script src=\"...js/tractor-filters.js\" defer>` "
        "(REUSE Story 2.8 generic IIFE — NEMA novi JS modul za Story 2.9 per AC7)."
    )


# =============================================================================
# Cross-cutting: no inline styles + no Cyrillic in templates
# =============================================================================


def test_no_inline_styles_in_used_machinery_templates():
    """No inline `style="..."` u Story 2.9 templates (project-context.md § Anti-pattern)."""
    products_templates_dir = PROJECT_ROOT / "templates" / "products"
    assert products_templates_dir.exists()

    target_files = [
        products_templates_dir / "used_machinery_listing.html",
        products_templates_dir / "partials" / "_used_filter_form.html",
        products_templates_dir / "partials" / "_used_results_grid.html",
        products_templates_dir / "partials" / "_used_empty_state.html",
    ]
    # Filter na one koji postoje (Dev MORA kreirati sve — ali ako neki nedostaje, drugi test već flagovan)
    existing = [f for f in target_files if f.exists()]
    assert existing, "Story 2.9 templates MORAJU postojati (Dev deliverable)."

    inline_pattern = re.compile(r'\bstyle\s*=\s*["\']', re.IGNORECASE)
    failures = []
    for fpath in existing:
        content = fpath.read_text(encoding="utf-8")
        if inline_pattern.search(content):
            failures.append(str(fpath.relative_to(PROJECT_ROOT)))
    assert not failures, (
        f"Used machinery templates sa inline `style=\"...\"`: {failures}. "
        "NEMA inline styling — coric-* BEM + var(--token)."
    )


def test_no_cyrillic_in_used_machinery_templates():
    """NEMA ćirilice u Story 2.9 templates (project-context.md § Anti-pattern — srpska latinica)."""
    products_templates_dir = PROJECT_ROOT / "templates" / "products"
    target_files = [
        products_templates_dir / "used_machinery_listing.html",
        products_templates_dir / "partials" / "_used_filter_form.html",
        products_templates_dir / "partials" / "_used_results_grid.html",
        products_templates_dir / "partials" / "_used_empty_state.html",
    ]
    existing = [f for f in target_files if f.exists()]
    assert existing

    cyrillic_pattern = re.compile(r"[Ѐ-ӿ]")
    failures = []
    for fpath in existing:
        content = fpath.read_text(encoding="utf-8")
        if cyrillic_pattern.search(content):
            failures.append(str(fpath.relative_to(PROJECT_ROOT)))
    assert not failures, (
        f"Used machinery templates sa ćirilicom: {failures}. "
        "Sve user-facing tekstove kroz `{% translate %}` sa srpska latinica msgstr."
    )


def test_no_leaked_django_comment_markers_used_listing(client):
    """No raw `{#` or `#}` substrings u rendered HTML (regression guard mirror Story 2.8
    commit 19ab259 — multi-line `{# ... #}` Django comments leak as plain text).

    Pre-condition: view MORA biti 200 (Dev je implementirao). Ako view ne postoji još,
    test verifikuje DA SE NIJE LEAKED-OVAO ni u 404 stranici (defensive — base.html
    se renderuje i za 404).
    """
    activate("sr")
    BrandFactory.create()
    UsedProductFactory.create(name="Comment Leak Test")

    # Full page — view mora biti 200 da bi test bio meaningful
    response = client.get("/sr/mehanizacija/polovna/", HTTP_HOST="localhost")
    assert response.status_code == 200, (
        f"View MORA vraćati 200 (Dev implementacija). Dobio {response.status_code}."
    )
    html = response.content.decode("utf-8")
    assert "{#" not in html, (
        f"Multi-line Django comment leaked into rendered HTML (full page render, "
        f"pos {html.find('{#')}). Use `{{% comment %}}...{{% endcomment %}}`."
    )
    assert "#}" not in html

    # HTMX partial
    htmx_response = client.get(
        "/sr/mehanizacija/polovna/",
        HTTP_HOST="localhost",
        HTTP_HX_REQUEST="true",
    )
    assert htmx_response.status_code == 200
    htmx_html = htmx_response.content.decode("utf-8")
    assert "{#" not in htmx_html
    assert "#}" not in htmx_html
