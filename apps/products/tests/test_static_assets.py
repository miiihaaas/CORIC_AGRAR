"""Story 2.7 — Cross-cutting static asset + i18n + a11y audit tests (RED phase TDD).

Pokriva Subtask 12.6 — verifikuje:
1. Sve user-facing strings u products templates kroz `{% translate %}` / `{% blocktranslate %}`
   (NEMA hardcoded srpski/cyrillic strings van translation tag-ova)
2. NEMA inline style="..." atributa u products templates (per project-context.md anti-pattern)
3. `static/css/main.css` sadrži 3 nove `@import url('./components/product-*.css')` linije
4. `static/css/components/brand-listing.css` više NEMA `coric-product-placeholder*` selektore
   (SM-D21 cleanup verification — placeholder klase migrated u product-detail.css ili obrisane)

OVI TESTOVI ĆE PASTI U RED PHASE — templates + CSS fajlovi ne postoje.
Posle Dev GREEN phase (Task 2-7 templates + Task 10 CSS), testovi će PROĆI.

Pokrenuti sa:
    docker compose -f compose/local.yml exec django uv run pytest \\
        apps/products/tests/test_static_assets.py -v

Refs:
- 2-7-product-detail-strana.md (Subtask 12.6 + SM-D21 cleanup + AC8 i18n/a11y guards)
- project-context.md § Anti-pattern: inline style + Section: Templates Django (linija 341)
"""

from __future__ import annotations

import pathlib
import re

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[3]


# =============================================================================
# Subtask 12.6 — Cross-cutting audits
# =============================================================================


def test_no_hardcoded_serbian_in_product_templates():
    """Subtask 12.6: nijedan products template ne sme hardkodovati srpske string-ove van
    {% translate %} / {% blocktranslate %} tag-ova.

    Audit strategija (mirror Story 2.6 AC8): tražimo karakteristične srpske diakritike
    (č, ć, š, ž, đ) u template plain text-u. Sve karakteristike koje se javljaju MORAJU
    biti unutar {% translate "..." %} ili {% blocktranslate %}...{% endblocktranslate %} tag-a.

    NAPOMENA: ovo je heuristički test (false-positive moguć ako se diakritik javlja u HTML
    atributu kao data-* value); konzervativna implementacija samo proverava da svaki
    products template ima bar jedan {% translate %} ili {% blocktranslate %} tag (negative
    proof — bez i18n tag-a, hardcoded user-facing string-ovi su 100% sigurni).
    """
    products_templates_dir = PROJECT_ROOT / "templates/products"
    assert products_templates_dir.exists(), (
        f"Templates direktorijum {products_templates_dir} MORA postojati (Story 2.7 Task 2)."
    )

    # Listaj sve .html fajlove
    template_files = list(products_templates_dir.rglob("*.html"))
    assert template_files, (
        f"products templates dir MORA imati bar 1 .html fajl posle Story 2.7 GREEN. "
        f"Pronađeno: {template_files!r}."
    )

    i18n_tag_pattern = re.compile(
        r"\{%\s*(translate|trans|blocktranslate|blocktrans)\b", re.IGNORECASE
    )

    failures = []
    for template_path in template_files:
        content = template_path.read_text(encoding="utf-8")
        # Heuristic: ako fajl sadrži srpske diakritike u plain text-u (van atributa),
        # mora imati bar jedan {% translate %} tag
        has_diacritics = bool(re.search(r"[čćšžđČĆŠŽĐ]", content))
        has_i18n_tag = bool(i18n_tag_pattern.search(content))
        if has_diacritics and not has_i18n_tag:
            failures.append(str(template_path.relative_to(PROJECT_ROOT)))

    assert not failures, (
        f"Templates sa srpskim diakritikom ALI BEZ {{% translate %}} / {{% blocktranslate %}} "
        f"tag-a (mogući hardcoded user-facing strings): {failures}. "
        "Sve user-facing strings MORAJU kroz i18n (project-context.md § A11y must-haves)."
    )


def test_no_inline_styles_in_product_templates():
    """Subtask 12.6: nijedan products template ne sme imati inline `style="..."` atribut.

    Per project-context.md § Anti-pattern + AC3 product_detail.html spec: sve stilizovanje
    kroz `coric-*` BEM klase + var(--token) reference; inline style sa magic vrednostima
    je zabranjeno.
    """
    products_templates_dir = PROJECT_ROOT / "templates/products"
    assert products_templates_dir.exists()

    template_files = list(products_templates_dir.rglob("*.html"))
    inline_style_pattern = re.compile(r'\bstyle\s*=\s*["\']', re.IGNORECASE)

    failures = []
    for template_path in template_files:
        content = template_path.read_text(encoding="utf-8")
        if inline_style_pattern.search(content):
            failures.append(str(template_path.relative_to(PROJECT_ROOT)))

    assert not failures, (
        f"Templates sa inline `style='...'` atributom: {failures}. "
        "NEMA inline styling (per project-context.md § Anti-pattern + AC3 spec). "
        "Sve kroz coric-* BEM klase + var(--token) reference."
    )


def test_product_detail_css_imports_in_main_css():
    """Subtask 12.6 + Subtask 10.4: `static/css/main.css` MORA sadržati 3 nove
    @import linije za product-detail.css + product-gallery.css + product-variants.css.
    """
    main_css_path = PROJECT_ROOT / "static/css/main.css"
    assert main_css_path.exists(), (
        f"{main_css_path} MORA postojati (Story 1.5 deliverable)."
    )
    content = main_css_path.read_text(encoding="utf-8")

    required_imports = [
        "components/product-detail.css",
        "components/product-gallery.css",
        "components/product-variants.css",
    ]
    missing = []
    for imp in required_imports:
        # Akceptuj oba: @import url('./components/...');  ili  @import url("./components/...");
        # ili bare @import './components/...';
        pattern = re.compile(
            r"@import\s+url\(\s*['\"]\.?/?" + re.escape(imp) + r"['\"]\s*\)\s*;"
            r"|@import\s+['\"]\.?/?" + re.escape(imp) + r"['\"]\s*;",
            re.IGNORECASE,
        )
        if not pattern.search(content):
            missing.append(imp)

    assert not missing, (
        f"main.css NEDOSTAJU 3 nove `@import` linije za {missing} (Subtask 10.4). "
        f"Sintaksa MORA biti `@import url('./components/{{file}}.css');` mirror Story 2.6 pattern."
    )


def test_brand_listing_css_no_longer_has_placeholder_selectors():
    """Subtask 12.6 + Subtask 10.5 (SM-D21 cleanup): brand-listing.css više NE SME
    sadržati `coric-product-placeholder*` selektore.

    Story 2.6 SM-D21 najavila: kad Story 2.7 uvede pravu ProductDetailView, 3 placeholder
    klase (`.coric-product-placeholder`, `.coric-product-placeholder__title`, `.coric-product-placeholder__message`)
    se brišu iz brand-listing.css (defunkcionalne posle template DELETE).
    """
    brand_listing_css_path = PROJECT_ROOT / "static/css/components/brand-listing.css"
    assert brand_listing_css_path.exists(), (
        f"{brand_listing_css_path} MORA postojati (Story 2.6 deliverable)."
    )
    content = brand_listing_css_path.read_text(encoding="utf-8")

    forbidden_selectors = [
        "coric-product-placeholder",
        "coric-product-placeholder__title",
        "coric-product-placeholder__message",
    ]
    found = []
    for sel in forbidden_selectors:
        if sel in content:
            found.append(sel)

    assert not found, (
        f"brand-listing.css JOŠ sadrži `{found}` selektore (Subtask 10.5 SM-D21 cleanup NIJE izvršen). "
        "Dev mora UKLONITI 3 placeholder selektora — defunkcionalni su posle _placeholder.html DELETE."
    )
