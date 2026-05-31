"""RED-phase tests za Story 2.11 — static assets (SM-D2).

Pokriva: breadcrumb.css mora imati coric-breadcrumb BEM selektore,
main.css mora @import breadcrumb.css, NO-EDIT guard za category-showcase.css
(coric-category-card) i tractor-listing.css (coric-product-card).

BUG-1 regression guard (Review-Fix iter 1): svaki var(--token) referenciran u
breadcrumb.css MORA biti definisan u tokens.css — sprečava ship-ovanje
komponente koja referencira nepostojeće tokene (link boja / focus-ring tiho
otkažu → WCAG/a11y regresija vs AC11/AC12).
"""

import re
from pathlib import Path

from django.conf import settings


def _static_root() -> Path:
    # repo static dir: <BASE>/static
    base = Path(settings.BASE_DIR)
    candidates = [base / "static", base.parent / "static"]
    for c in candidates:
        if (c / "css" / "main.css").exists():
            return c
    # fallback na prvi STATICFILES_DIRS
    for d in getattr(settings, "STATICFILES_DIRS", []):
        p = Path(d)
        if (p / "css" / "main.css").exists():
            return p
    return base / "static"


def _read(rel: str) -> str:
    path = _static_root() / rel
    return path.read_text(encoding="utf-8")


class TestBreadcrumbStaticAssets:
    # static: breadcrumb.css sadrzi coric-breadcrumb BEM selektore
    def test_breadcrumb_css_has_bem_selectors(self):
        css = _read("css/components/breadcrumb.css")
        assert ".coric-breadcrumb" in css
        assert ".coric-breadcrumb__item" in css
        assert ".coric-breadcrumb__link" in css
        assert ".coric-breadcrumb__current" in css

    # static: main.css importuje breadcrumb.css
    def test_main_css_imports_breadcrumb(self):
        main = _read("css/main.css")
        assert "components/breadcrumb.css" in main
        assert "@import" in main

    # static NO-EDIT guard: category-showcase.css zadrzava coric-category-card
    def test_category_showcase_css_unchanged_marker(self):
        css = _read("css/components/category-showcase.css")
        assert ".coric-category-card" in css

    # static NO-EDIT guard: tractor-listing.css zadrzava coric-product-card
    def test_tractor_listing_css_unchanged_marker(self):
        css = _read("css/components/tractor-listing.css")
        assert "coric-product-card" in css

    # BUG-1 guard: svaki var(--token) u breadcrumb.css MORA biti definisan u tokens.css.
    def test_breadcrumb_css_tokens_all_defined_in_tokens_file(self):
        breadcrumb_css = _read("css/components/breadcrumb.css")
        tokens_css = _read("css/tokens.css")

        # Custom properties DEFINED in tokens.css (LHS of a declaration `--foo:`).
        defined = set(re.findall(r"(--[a-z0-9-]+)\s*:", tokens_css))
        # Custom properties REFERENCED via var(--foo) in breadcrumb.css.
        referenced = set(re.findall(r"var\(\s*(--[a-z0-9-]+)", breadcrumb_css))

        undefined = referenced - defined
        assert not undefined, (
            "breadcrumb.css referencira tokene koji NISU definisani u tokens.css: "
            f"{sorted(undefined)}"
        )
