"""Story 2.10 — Static assets tests (CSS tokens + main.css import + repeating-element selektor).

Pokriva AC6 — `category-showcase.css` postoji + `main.css` ima @import + tokens postoje +
repeating-element--jeegee selektor postoji.

Test scope (3 tests):
- test_category_showcase_css_imported_in_main_css
- test_repeating_element_jeegee_variant_css_selector_exists
- test_required_css_tokens_exist

Pokrenuti sa:
    docker compose -f compose/local.yml exec django pytest \\
        apps/brands/tests/test_jeegee_prikljucna_static_assets.py -v

Refs:
- 2-10-jeegee-prikljucna-mehanizacija-strana.md (AC6)
- 2-10-interface-contract.md (§ 5 CSS)
"""

from __future__ import annotations

from pathlib import Path


# Repo root = manage.py parent (compose runs from /code which is repo root)
_REPO_ROOT = Path(__file__).resolve().parents[3]
_MAIN_CSS = _REPO_ROOT / "static" / "css" / "main.css"
_CATEGORY_SHOWCASE_CSS = (
    _REPO_ROOT / "static" / "css" / "components" / "category-showcase.css"
)
_REPEATING_ELEMENT_CSS = (
    _REPO_ROOT / "static" / "css" / "components" / "repeating-element.css"
)
_TOKENS_CSS = _REPO_ROOT / "static" / "css" / "tokens.css"


def test_category_showcase_css_imported_in_main_css():
    """AC6: main.css MORA imati @import url('./components/category-showcase.css'); linija.

    Sintaksa mirror Story 1.7/1.8/2.5/2.6/2.7/2.8/2.9 (url(...) wrap + leading ./
    + trailing semicolon) — IMP-7 relative-with-dot konvencija.
    """
    assert _MAIN_CSS.exists(), (
        f"main.css MORA postojati na {_MAIN_CSS} (Story 1.7 deliverable)."
    )

    main_css_content = _MAIN_CSS.read_text(encoding="utf-8")

    expected_import = "@import url('./components/category-showcase.css');"
    assert expected_import in main_css_content, (
        f"main.css MORA sadržati '{expected_import}' liniju (AC6 +1 @import). "
        f"Pozicionira POSLE postojeće "
        f"`@import url('./components/used-machinery-listing.css');` (Story 2-9 linija 32)."
    )

    # Verifikuj NOVA komponenta CSS fajl postoji
    assert _CATEGORY_SHOWCASE_CSS.exists(), (
        f"category-showcase.css MORA biti kreiran na "
        f"{_CATEGORY_SHOWCASE_CSS} (AC6 NOVI fajl)."
    )


def test_category_showcase_css_defines_required_bem_selectors():
    """AC6: category-showcase.css MORA definisati BEM selektore + reduced-motion block.

    Sprečava regression gde @import postoji ali je fajl prazan (test_category_showcase_
    css_imported_in_main_css proverava SAMO @import + file existence, ne sadržaj).

    Per contract § 5 — required selektori (svi `coric-` prefiks):
    - .coric-category-showcase (grid wrapper)
    - .coric-category-showcase__title
    - .coric-category-card (kartica root sa transition)
    - .coric-category-card__icon / __title / __description / __cta
    - .coric-empty-state ({% empty %} clause CSS — IMP-2)
    - @media (prefers-reduced-motion: reduce) block
    - responsive grid: repeat(auto-fit, minmax(280px, 1fr))
    """
    assert _CATEGORY_SHOWCASE_CSS.exists(), (
        f"category-showcase.css MORA biti kreiran na {_CATEGORY_SHOWCASE_CSS} "
        f"(AC6 NOVI fajl)."
    )

    css = _CATEGORY_SHOWCASE_CSS.read_text(encoding="utf-8")

    required_selectors = [
        ".coric-category-showcase",
        ".coric-category-showcase__title",
        ".coric-category-card",
        ".coric-category-card__icon",
        ".coric-category-card__title",
        ".coric-category-card__description",
        ".coric-category-card__cta",
        ".coric-empty-state",
    ]
    for selector in required_selectors:
        assert selector in css, (
            f"category-showcase.css MORA definisati `{selector}` selektor "
            f"(contract § 5 BEM komponenta). Nije pronađen u fajlu."
        )

    # Responsive grid foundation za Story 2-12 (3 vs 4 vs N kartica auto-fit)
    assert "repeat(auto-fit, minmax(280px, 1fr))" in css, (
        "category-showcase.css `.coric-category-showcase` MORA koristiti "
        "`grid-template-columns: repeat(auto-fit, minmax(280px, 1fr))` (AC6 — "
        "responsive grid koji automatski handluje 3 vs 4 kartice; foundation za Story 2-12)."
    )

    # prefers-reduced-motion block (AC6 a11y — uklanja transform animaciju)
    assert "prefers-reduced-motion" in css, (
        "category-showcase.css MORA imati `@media (prefers-reduced-motion: reduce)` "
        "block koji uklanja transform/transition animaciju (AC6 a11y zahtev)."
    )

    # Sve vrednosti kroz var(--token) — bar jedna token referenca prisutna
    assert "var(--" in css, (
        "category-showcase.css MORA koristiti `var(--token)` reference (NEMA hardcoded "
        "boja/spacing vrednosti — project-context.md token discipline)."
    )


def test_repeating_element_jeegee_variant_css_selector_exists():
    """AC4 + AC6 + SM-D9 regression guard: .coric-repeating-element--jeegee MORA postojati.

    Verifikuje da Story 1-7 `repeating-element.css` (NETAKNUT u Story 2-10) ima
    `.coric-repeating-element--jeegee` selektor koji mapira na
    `background-color: var(--color-jeegee-blue)`. Ako Story 1-7 file je accidentally
    obrisan/modifikovan, hero render bi imao unstyled watermark.
    """
    assert _REPEATING_ELEMENT_CSS.exists(), (
        f"repeating-element.css MORA postojati na {_REPEATING_ELEMENT_CSS} "
        f"(Story 1-7 deliverable, NETAKNUT u Story 2-10)."
    )

    css_content = _REPEATING_ELEMENT_CSS.read_text(encoding="utf-8")

    assert ".coric-repeating-element--jeegee" in css_content, (
        "repeating-element.css MORA imati `.coric-repeating-element--jeegee` "
        "selektor (SM-D9 lock — Story 2-10 hero koristi variant='jeegee' koji "
        "rezolvuje na ovu klasu). Live verifikovano `static/css/components/"
        "repeating-element.css:14`."
    )
    # Mora referencirati --color-jeegee-blue token
    assert "var(--color-jeegee-blue)" in css_content, (
        "repeating-element.css `--jeegee` variant MORA koristiti "
        "`var(--color-jeegee-blue)` token (Story 1-5 tokens.css)."
    )


def test_required_css_tokens_exist():
    """AC6: tokens.css MORA imati sva tokena koja category-showcase.css koristi.

    Live verifikovano 2026-05-30:
    - --color-jeegee-blue (linija 94) — za .coric-category-card__icon color
    - --color-neutral-gray-700 (linija 102) — za description + empty-state color
    - --spacing-scale-5 (linija 161) — za grid gap + padding
    """
    assert _TOKENS_CSS.exists(), (
        f"tokens.css MORA postojati na {_TOKENS_CSS} (Story 1-5 deliverable)."
    )

    tokens_content = _TOKENS_CSS.read_text(encoding="utf-8")

    required_tokens = [
        "--color-jeegee-blue",
        "--color-neutral-gray-700",
        "--spacing-scale-5",
        "--color-brand-green-800",
        "--color-neutral-white",
        "--rounded-md",
    ]
    for token in required_tokens:
        assert token in tokens_content, (
            f"tokens.css MORA definisati `{token}` (Story 2-10 category-showcase.css "
            f"koristi var(--token) reference)."
        )
