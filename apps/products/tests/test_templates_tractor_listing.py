"""Story 2.8 — Tractor listing templates + partials tests (RED phase TDD).

Pokriva AC3 (template structure, single h1, single main, semantic HTML5 section order) +
AC4 (brand header partial — is_coming_soon filter, klikabilni links, logo fallback) +
AC5 (filter form partial — HTMX atributi, fieldset/legend, RESETUJ FILTERE CTA,
slider thumb ARIA labels SM-D20) + AC6 (results grid wrapper id="tractor-results",
coric-product-card linkable card, OOB guard SM-D23) + AC7 (empty state) +
cross-cutting (vendor noUiSlider files, no inline styles, i18n heuristic, NEMA ćirilica).

TEA RED phase: SVI testovi MORAJU pasti — templates ne postoje, vendor folder ne postoji.

Pokrenuti sa:
    docker compose -f compose/local.yml exec django uv run pytest \\
        apps/products/tests/test_templates_tractor_listing.py -v

Refs:
- 2-8-tractor-listing-strana-sa-htmx-filterima.md (AC3-AC8 + SM-D5/D6/D14/D20/D23)
- 2-8-interface-contract.md § 3 + § 6
"""

from __future__ import annotations

import pathlib
import re

import pytest
from django.utils.translation import activate

from apps.brands.tests.factories import BrandFactory
from apps.products.tests.factories import TractorProductFactory

pytestmark = pytest.mark.django_db

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[3]


# =============================================================================
# AC3 — Template structure: single h1, single main, section order, ARIA landmarks
# =============================================================================


def test_single_h1_element(client):
    """AC3: render-uje TAČNO 1 `<h1>` element ('Traktori'); sve ostale sekcije imaju h2/h3."""
    activate("sr")
    brand = BrandFactory.create()
    TractorProductFactory.create(brand=brand, name="H1 Test Tractor")

    response = client.get("/sr/traktori/", HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    h1_count = len(re.findall(r"<h1\b", html, re.IGNORECASE))
    assert h1_count == 1, (
        f"Tractor listing MORA imati TAČNO 1 `<h1>` (UX/SEO single-h1 rule), "
        f"dobio {h1_count}. Page heading je 'Traktori' (id='tractor-listing-title')."
    )


def test_single_main_element(client):
    """AC3: render-uje TAČNO 1 `<main>` element (base.html provider; outer wrapper je
    `<section>` NIJE drugi `<main>`). Mirror Story 2.7 I7 regression guard.
    """
    activate("sr")
    brand = BrandFactory.create()
    TractorProductFactory.create(brand=brand, name="Main Test Tractor")

    response = client.get("/sr/traktori/", HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    main_count = len(re.findall(r"<main\b", html, re.IGNORECASE))
    assert main_count == 1, (
        f"Tractor listing MORA imati TAČNO 1 `<main>` element (base.html provider; "
        f"outer wrapper je `<section>` NIJE `<main>`). Dobio {main_count}."
    )


def test_outer_section_has_data_testid_tractor_listing_page(client):
    """AC3: outer wrapper je `<section class="coric-tractor-listing" data-testid="tractor-listing-page">`."""
    activate("sr")
    brand = BrandFactory.create()
    TractorProductFactory.create(brand=brand, name="Outer Wrapper Test")

    response = client.get("/sr/traktori/", HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    # Akceptuj oba atribut redosleda (class + data-testid)
    pattern_a = re.compile(
        r'<section[^>]*class="[^"]*coric-tractor-listing[^"]*"[^>]*data-testid="tractor-listing-page"',
        re.IGNORECASE,
    )
    pattern_b = re.compile(
        r'<section[^>]*data-testid="tractor-listing-page"[^>]*class="[^"]*coric-tractor-listing',
        re.IGNORECASE,
    )

    assert pattern_a.search(html) or pattern_b.search(html), (
        "tractor_listing.html MORA imati outer `<section class=\"coric-tractor-listing\" "
        "data-testid=\"tractor-listing-page\">` wrapper. "
        "Provera fail-ovala u oba atribut redosleda."
    )


def test_sections_render_in_correct_order(client):
    """AC3: sekcije renderuju TAČNIM redosledom — page heading (h1) → brand header →
    filter form → results wrap.

    Verifikuje monotono rastuće position indices u HTML render-u.
    """
    activate("sr")
    brand = BrandFactory.create()
    TractorProductFactory.create(brand=brand, name="Section Order Test")

    response = client.get("/sr/traktori/", HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    h1_idx = html.find('id="tractor-listing-title"')
    brand_header_idx = html.find('id="brand-header"')
    filter_form_idx = html.find('id="tractor-filters"')
    results_idx = html.find('id="tractor-results-wrap"')

    assert h1_idx >= 0, "Page heading (#tractor-listing-title) MORA postojati."
    assert brand_header_idx >= 0, "Brand header sekcija (#brand-header) MORA postojati."
    assert filter_form_idx >= 0, "Filter form sekcija (#tractor-filters) MORA postojati."
    assert results_idx >= 0, "Results sekcija (#tractor-results-wrap) MORA postojati."

    assert h1_idx < brand_header_idx < filter_form_idx < results_idx, (
        f"Section order BROKEN. Pozicije: h1={h1_idx}, brand_header={brand_header_idx}, "
        f"filter_form={filter_form_idx}, results={results_idx}. "
        "Očekivan: h1 < brand_header < filter_form < results."
    )


# =============================================================================
# AC4 — Brand header partial (SM-D5)
# =============================================================================


def test_brand_header_lists_non_coming_soon_brands_only(client):
    """AC4 + SM-D5: brand header iterira SAMO kroz `is_coming_soon=False` brendove."""
    activate("sr")
    live_a = BrandFactory.create(name="Aaa Live")
    coming = BrandFactory.create_coming_soon(name="Bbb Coming Soon")
    TractorProductFactory.create(brand=live_a, name="Live Brand Tractor")

    response = client.get("/sr/traktori/", HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    assert f'data-testid="brand-header-link-{live_a.slug}"' in html, (
        f"Live brand link (testid='brand-header-link-{live_a.slug}') MORA biti renderovan."
    )
    assert f'data-testid="brand-header-link-{coming.slug}"' not in html, (
        f"Coming-soon brand link (testid='brand-header-link-{coming.slug}') NE SME biti "
        "renderovan (SM-D5 is_coming_soon=False filter)."
    )


def test_brand_header_link_uses_brands_detail_url(client):
    """AC4: brand header link `href` je `{% url 'brands:detail' slug=brand.slug %}` —
    klik vodi na Story 2.6 BrandDetailView.
    """
    activate("sr")
    brand = BrandFactory.create(name="Click Through Brand")
    TractorProductFactory.create(brand=brand, name="Click Test")

    response = client.get("/sr/traktori/", HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    expected_href = f'href="/sr/traktori/{brand.slug}/"'
    assert expected_href in html, (
        f"Brand header link MORA imati href='/sr/traktori/{brand.slug}/' "
        f"(brands:detail). Search pattern: {expected_href!r}."
    )


def test_brand_without_logo_renders_text_fallback(client):
    """AC4: brand bez logo-a renderuje text fallback `<span>` sa brand name
    (defensive — admin može zaboraviti logo upload).
    """
    activate("sr")
    # BrandFactory.create() default-no NE postavlja logo — brand.logo je None
    brand = BrandFactory.create(name="Logoless Brand")
    TractorProductFactory.create(brand=brand, name="Logoless Test")

    response = client.get("/sr/traktori/", HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    # Text fallback markup — `<span class="coric-brand-header__name-fallback">{brand.name}</span>`
    fallback_pattern = re.compile(
        r'<span[^>]*class="[^"]*coric-brand-header__name-fallback[^"]*"[^>]*>\s*Logoless Brand\s*</span>',
        re.IGNORECASE,
    )
    assert fallback_pattern.search(html), (
        "Brand bez logo-a MORA imati `<span class=\"coric-brand-header__name-fallback\">"
        "{brand.name}</span>` fallback. Defensive UX guard."
    )


# =============================================================================
# AC5 — Filter form partial (HTMX atributi + slider ARIA + RESETUJ FILTERE CTA)
# =============================================================================


def test_filter_form_has_hx_get_attribute(client):
    """AC5: filter form ima `hx-get` atribut koji ukazuje na products:tractor_list URL."""
    activate("sr")
    BrandFactory.create()
    TractorProductFactory.create(name="HX-Get Test")

    response = client.get("/sr/traktori/", HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    # Form sa data-testid="tractor-filter-form" + hx-get="/sr/traktori/"
    form_match = re.search(
        r'<form[^>]*data-testid="tractor-filter-form"[^>]*>',
        html,
        re.IGNORECASE,
    )
    assert form_match, "Filter form MORA imati `data-testid=\"tractor-filter-form\"`."
    form_tag = form_match.group(0)
    assert 'hx-get="/sr/traktori/"' in form_tag or "hx-get='/sr/traktori/'" in form_tag, (
        f"Filter form MORA imati `hx-get=\"/sr/traktori/\"` atribut. Form tag: {form_tag!r}."
    )


def test_filter_form_has_hx_trigger_with_debounce(client):
    """AC5: filter form ima `hx-trigger="input changed delay:300ms, change delay:300ms"`
    (debounce 300ms + dual input/change events per SM A I3).
    """
    activate("sr")
    BrandFactory.create()
    TractorProductFactory.create(name="HX-Trigger Test")

    response = client.get("/sr/traktori/", HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    form_match = re.search(r'<form[^>]*data-testid="tractor-filter-form"[^>]*>', html, re.IGNORECASE)
    assert form_match
    form_tag = form_match.group(0)

    assert "delay:300ms" in form_tag, (
        f"Filter form MORA imati `hx-trigger` sa `delay:300ms` (debounce per AC5). "
        f"Form tag: {form_tag!r}."
    )
    assert "input changed" in form_tag, (
        f"Filter form MORA listening na `input changed` event (slider drag). "
        f"Form tag: {form_tag!r}."
    )


def test_filter_form_has_hx_push_url_and_target(client):
    """AC5: filter form ima `hx-push-url="true"`, `hx-target="#tractor-results"`,
    `hx-swap="innerHTML"`, `hx-indicator="#filter-loading"`.
    """
    activate("sr")
    BrandFactory.create()
    TractorProductFactory.create(name="HX-Push-URL Test")

    response = client.get("/sr/traktori/", HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    form_match = re.search(r'<form[^>]*data-testid="tractor-filter-form"[^>]*>', html, re.IGNORECASE)
    assert form_match
    form_tag = form_match.group(0)

    assert 'hx-push-url="true"' in form_tag, f"Filter form MORA imati `hx-push-url=\"true\"`. Form: {form_tag!r}."
    assert 'hx-target="#tractor-results"' in form_tag, (
        f"Filter form MORA imati `hx-target=\"#tractor-results\"`. Form: {form_tag!r}."
    )
    assert 'hx-swap="innerHTML"' in form_tag, f"Filter form MORA imati `hx-swap=\"innerHTML\"`. Form: {form_tag!r}."
    assert 'hx-indicator="#filter-loading"' in form_tag, (
        f"Filter form MORA imati `hx-indicator=\"#filter-loading\"`. Form: {form_tag!r}."
    )


def test_filter_form_has_no_csrf_token(client):
    """AC5: GET form NE SME imati `{% csrf_token %}` (Django CSRF samo POST/PUT/DELETE/PATCH)."""
    activate("sr")
    BrandFactory.create()
    TractorProductFactory.create(name="No-CSRF Test")

    response = client.get("/sr/traktori/", HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    # Extract filter form content (od <form data-testid="tractor-filter-form" do prvog </form>)
    form_match = re.search(
        r'<form[^>]*data-testid="tractor-filter-form"[^>]*>(.*?)</form>',
        html,
        re.IGNORECASE | re.DOTALL,
    )
    assert form_match, "Filter form sa data-testid='tractor-filter-form' MORA postojati."
    form_content = form_match.group(1)

    assert "csrfmiddlewaretoken" not in form_content, (
        "GET filter form NE SME sadržati `csrfmiddlewaretoken` (CSRF only POST). "
        "Anti-pattern: copy-paste CSRF na GET formu je dead code."
    )


def test_filter_form_reset_cta_is_anchor_not_htmx(client):
    """AC5 + SM-D6: RESETUJ FILTERE CTA je `<a href="{% url 'products:tractor_list' %}">`
    full reload, NIJE `hx-get` HTMX-trigger.
    """
    activate("sr")
    BrandFactory.create()
    TractorProductFactory.create(name="Reset CTA Test")

    response = client.get("/sr/traktori/", HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    # Reset CTA sa data-testid="reset-filters-button" mora biti <a> (NE <button>)
    reset_match = re.search(
        r'<(a|button)[^>]*data-testid="reset-filters-button"[^>]*>',
        html,
        re.IGNORECASE,
    )
    assert reset_match, "Reset CTA sa data-testid='reset-filters-button' MORA postojati."
    tag_name = reset_match.group(1).lower()
    tag = reset_match.group(0)

    assert tag_name == "a", (
        f"RESETUJ FILTERE CTA MORA biti `<a>` (SM-D6 full reload), dobio `<{tag_name}>`."
    )
    assert 'href="/sr/traktori/"' in tag, (
        f"Reset CTA MORA imati `href=\"/sr/traktori/\"` (full reload bez query params). Tag: {tag!r}."
    )
    assert "hx-get" not in tag, (
        f"Reset CTA NE SME imati `hx-get` atribut (SM-D6 terminal action je full reload, NE HTMX). Tag: {tag!r}."
    )


def test_slider_thumbs_have_aria_labels(client):
    """AC5 + SM-D20 (A11Y-S): svaki `[data-range-slider]` container ima `data-aria-label-min`
    + `data-aria-label-max` data attributes koji template prosleđuje iz `{% translate %}`.

    Bez ovih, JS noUiSlider config ne može postaviti aria-label na thumb-ove → NVDA reads
    "2 slider" bez konteksta.
    """
    activate("sr")
    BrandFactory.create()
    TractorProductFactory.create(name="Slider ARIA Test")

    response = client.get("/sr/traktori/", HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    # 2 slider container-a (Snaga + Cena), svaki ima oba aria-label attributes
    slider_containers = re.findall(
        r'<div[^>]*data-range-slider[^>]*>',
        html,
        re.IGNORECASE,
    )
    assert len(slider_containers) >= 2, (
        f"MORA postojati >=2 `[data-range-slider]` container-a (Snaga + Cena), "
        f"dobio {len(slider_containers)}."
    )
    for container in slider_containers:
        assert "data-aria-label-min" in container, (
            f"Slider container MORA imati `data-aria-label-min` attribute (SM-D20). "
            f"Container: {container!r}."
        )
        assert "data-aria-label-max" in container, (
            f"Slider container MORA imati `data-aria-label-max` attribute (SM-D20). "
            f"Container: {container!r}."
        )


# =============================================================================
# AC6 — Results grid: wrapper id, linkable card pattern, nested-interactive guard
# =============================================================================


def test_results_wrapper_has_id_tractor_results(client):
    """AC6: results grid outer wrapper je `<div id="tractor-results">` (INVARIJANTAN ID
    — HTMX hx-target referencira ovaj).
    """
    activate("sr")
    BrandFactory.create()
    TractorProductFactory.create(name="Wrapper ID Test")

    response = client.get("/sr/traktori/", HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    pattern = re.compile(r'<div[^>]*\bid="tractor-results"', re.IGNORECASE)
    assert pattern.search(html), (
        "Results grid MORA imati `<div id=\"tractor-results\">` wrapper "
        "(INVARIJANTAN ID — HTMX hx-target referencira ovo)."
    )


def test_product_card_uses_coric_product_card_bem(client):
    """AC6: product kartice koriste `coric-product-card` BEM (reuse iz Story 2.6)."""
    activate("sr")
    brand = BrandFactory.create()
    TractorProductFactory.create(brand=brand, name="BEM Test Tractor")

    response = client.get("/sr/traktori/", HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    assert "coric-product-card" in html, (
        "Product card MORA reuse `coric-product-card` BEM iz Story 2.6 (brand-listing.css). "
        "Story 2.8 NE re-definiše istu BEM."
    )


def test_product_card_linkable_with_aria_label_and_testid(client):
    """AC6: product card je `<a>` wraps card sa `aria-label` + `data-testid="tractor-card-{slug}"`."""
    activate("sr")
    brand = BrandFactory.create()
    product = TractorProductFactory.create(brand=brand, name="Linkable Test", price_eur=15000)

    response = client.get("/sr/traktori/", HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    expected_testid = f'data-testid="tractor-card-{product.slug}"'
    assert expected_testid in html, (
        f"Product card MORA imati `{expected_testid}` (Playwright hook)."
    )
    # aria-label u istoj <a> tag-i
    card_pattern = re.compile(
        r'<a[^>]*data-testid="tractor-card-' + re.escape(product.slug) + r'"[^>]*>',
        re.IGNORECASE,
    )
    card_match = card_pattern.search(html)
    assert card_match, f"Product card `<a>` sa data-testid='tractor-card-{product.slug}' MORA postojati."
    card_tag = card_match.group(0)
    assert "aria-label" in card_tag, (
        f"Product card `<a>` MORA imati `aria-label` atribut (WCAG SC 2.4.4). Tag: {card_tag!r}."
    )


def test_product_card_cta_is_aria_hidden_span(client):
    """AC6: „OPŠIRNIJE" CTA unutar product card je `<span aria-hidden="true">` (NE `<a>` ili
    `<button>` — nested-interactive WCAG SC 4.1.2 violation guard).
    """
    activate("sr")
    brand = BrandFactory.create()
    TractorProductFactory.create(brand=brand, name="CTA Span Test")

    response = client.get("/sr/traktori/", HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    # CTA je <span aria-hidden="true">OPŠIRNIJE</span> ili sa class coric-product-card__cta
    span_pattern = re.compile(
        r'<span[^>]*aria-hidden="true"[^>]*>[^<]*OPŠIRNIJE',
        re.IGNORECASE,
    )
    assert span_pattern.search(html), (
        "Product card 'OPSIRNIJE' CTA MORA biti `<span aria-hidden=\"true\">` "
        "(nested-interactive guard — outer <a> wraps card already)."
    )


# =============================================================================
# AC7 — Empty state
# =============================================================================


def test_empty_state_renders_when_zero_results(client):
    """AC7: empty state markup renderuje kad filter daje 0 rezultata."""
    activate("sr")
    BrandFactory.create()
    # NEMA TractorProductFactory.create — 0 traktor product-a u DB

    response = client.get("/sr/traktori/", HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    assert 'data-testid="tractor-empty-state"' in html, (
        "Empty state markup (data-testid='tractor-empty-state') MORA biti renderovan "
        "kad 0 traktor product-a matchuje queryset."
    )


def test_empty_state_has_reset_cta_anchor(client):
    """AC7: empty state „RESETUJ FILTERE" CTA je `<a href="{% url 'products:tractor_list' %}">`
    sa `data-testid="empty-reset-button"` (per SM-D6 — full reload, NIJE HTMX).
    """
    activate("sr")
    BrandFactory.create()

    response = client.get("/sr/traktori/", HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    reset_pattern = re.compile(
        r'<a[^>]*data-testid="empty-reset-button"[^>]*href="/sr/traktori/"',
        re.IGNORECASE,
    )
    reset_pattern_alt = re.compile(
        r'<a[^>]*href="/sr/traktori/"[^>]*data-testid="empty-reset-button"',
        re.IGNORECASE,
    )
    assert reset_pattern.search(html) or reset_pattern_alt.search(html), (
        "Empty state RESETUJ FILTERE CTA MORA biti `<a href=\"/sr/traktori/\" "
        "data-testid=\"empty-reset-button\">` (SM-D6 full reload, NIJE HTMX)."
    )


# =============================================================================
# Cross-cutting: vendor noUiSlider + i18n + no inline styles
# =============================================================================


def test_vendor_nouislider_files_exist():
    """SM-D4 + SM-D22 (VEN fix): vendored noUiSlider fajlovi MORAJU postojati u
    static/vendor/nouislider/ — pin 15.7.1 (mirror Story 2.5 GLightbox vendoring).
    """
    vendor_dir = PROJECT_ROOT / "static" / "vendor" / "nouislider"
    assert vendor_dir.exists(), (
        f"Vendor folder {vendor_dir} MORA postojati (SM-D4 noUiSlider lock + SM-D22 pin 15.7.1)."
    )

    required_files = ["nouislider.min.js", "nouislider.min.css"]
    missing = []
    for fname in required_files:
        if not (vendor_dir / fname).exists():
            missing.append(fname)
    assert not missing, (
        f"Vendor folder {vendor_dir} NEDOSTAJU fajlovi: {missing!r}. "
        "Mirror Story 2.5 GLightbox vendoring pattern."
    )


def test_no_inline_styles_in_tractor_templates():
    """Subtask 9.6: nijedan products/tractor*.html template ne sme imati `style="..."` atribut.

    Per project-context.md § Anti-pattern: sve stilizovanje kroz coric-* BEM klase + var(--token).
    """
    products_templates_dir = PROJECT_ROOT / "templates" / "products"
    assert products_templates_dir.exists(), (
        f"Templates folder {products_templates_dir} MORA postojati (Story 2.7 + 2.8 deliverable)."
    )

    target_files = (
        list(products_templates_dir.glob("tractor_*.html"))
        + list((products_templates_dir / "partials").glob("_brand_header.html"))
        + list((products_templates_dir / "partials").glob("_filter_form.html"))
        + list((products_templates_dir / "partials").glob("_results_grid.html"))
        + list((products_templates_dir / "partials").glob("_empty_state.html"))
    )
    assert target_files, "Story 2.8 templates MORAJU postojati (bar jedan tractor_*.html)."

    inline_pattern = re.compile(r'\bstyle\s*=\s*["\']', re.IGNORECASE)
    failures = []
    for fpath in target_files:
        content = fpath.read_text(encoding="utf-8")
        if inline_pattern.search(content):
            failures.append(str(fpath.relative_to(PROJECT_ROOT)))
    assert not failures, (
        f"Tractor templates sa inline `style=\"...\"` atributom: {failures}. "
        "NEMA inline styling (project-context.md § Anti-pattern)."
    )


def test_no_leaked_django_comment_markers(client):
    """Story 2-8 review iter 1 (BUG-1 + commit 19ab259 mirror): NO raw '{#' or '#}'
    substrings in rendered HTML.

    Razlog: multi-line `{# ... #}` Django comments are NOT supported by the template
    engine — they leak as plain text into rendered HTML. Same regression that was
    fixed for Story 2.5 in commit 19ab259. This guard catches reintroduction
    across BOTH non-HTMX (full page) and HTMX (partial swap) render paths.
    """
    activate("sr")
    BrandFactory.create(slug="cmt-leak-test")
    TractorProductFactory.create(slug="comment-leak-test", name="Comment Leak Test")

    # Non-HTMX full-page render
    response = client.get("/sr/traktori/", HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")
    assert "{#" not in html, (
        f"Multi-line Django comment leaked into rendered HTML "
        f"(non-HTMX render, pos {html.find('{#')}). "
        f"Convert `{{# ... #}}` to `{{% comment %}}...{{% endcomment %}}` block."
    )
    assert "#}" not in html, (
        "Closing `#}` comment marker leaked into rendered HTML (non-HTMX render)."
    )

    # HTMX partial swap render path (mirror — same template `_results_grid.html`
    # MUST be clean for HTMX response too).
    htmx_response = client.get(
        "/sr/traktori/",
        HTTP_HOST="localhost",
        HTTP_HX_REQUEST="true",
    )
    assert htmx_response.status_code == 200
    htmx_html = htmx_response.content.decode("utf-8")
    assert "{#" not in htmx_html, (
        f"Multi-line Django comment leaked into HTMX partial response "
        f"(pos {htmx_html.find('{#')})."
    )
    assert "#}" not in htmx_html, (
        "Closing `#}` comment marker leaked into HTMX partial response."
    )


def test_no_cyrillic_in_tractor_templates():
    """Subtask 2.5: NEMA ćirilice u tractor templates — srpska latinica striktno
    (project-context.md § Slug-ovi).
    """
    products_templates_dir = PROJECT_ROOT / "templates" / "products"
    target_files = (
        list(products_templates_dir.glob("tractor_*.html"))
        + list((products_templates_dir / "partials").glob("_brand_header.html"))
        + list((products_templates_dir / "partials").glob("_filter_form.html"))
        + list((products_templates_dir / "partials").glob("_results_grid.html"))
        + list((products_templates_dir / "partials").glob("_empty_state.html"))
    )
    assert target_files, "Story 2.8 templates MORAJU postojati."

    # Cyrillic ranges: U+0400-U+04FF (full Cyrillic block; sve Latinice su U+0000-U+017F + var-i)
    cyrillic_pattern = re.compile(r"[Ѐ-ӿ]")
    failures = []
    for fpath in target_files:
        content = fpath.read_text(encoding="utf-8")
        if cyrillic_pattern.search(content):
            failures.append(str(fpath.relative_to(PROJECT_ROOT)))
    assert not failures, (
        f"Tractor templates sa ćirilicom: {failures}. "
        "Sve user-facing tekstove kroz `{% translate %}` sa srpska latinica msgstr."
    )
