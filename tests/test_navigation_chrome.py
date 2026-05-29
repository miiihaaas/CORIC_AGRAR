"""Tests za Story 1.8 — Sticky Nav + Top Header + Footer + Language Switcher Partial.

Pokriva [MUST] scenarios iz Story 1.8 Testing section (Decision D14: novi fajl umesto
extension u test_visual_components.py; kohezija scope-a "navigation/chrome").

AC pokrivenost (~37 testova):
- AC1 base.html structure + new files presence (~6 testova)
- AC2 top header rendering + role banner + height 40px (~5 testova)
- AC3 sticky nav layout + navbar-expand-md + z-index 1020 + logo URL (~5 testova)
- AC4 language switcher nav partial: aria-current, forms, no inline handlers (~5 testova)
- AC5 sticky-nav.js IIFE + IntersectionObserver + no global pollution + matchMedia (~5 testova)
- AC6 footer: 4 columns + section_eyebrow consumption + lorem placeholder + copyright (~4 testa)
- AC7 a11y guards: prefers-reduced-motion + forced-colors (~3 testa)
- AC8 ARIA landmarks present (~2 testa)
- AC9 token discipline: no hardcoded hex/px outside whitelist, no inline style, no cyrillic (~5 testova)
- AC10 Story 1.6 regression test migrated (Task 10a) (~1 test)
- Deferred SHOULD tests sa skip decorators (~1 test)

Pokrenuti sa:
    uv run pytest tests/test_navigation_chrome.py -v --tb=short

TEA RED faza: svi testovi MORAJU pasti (FileNotFoundError, TemplateDoesNotExist,
AssertionError) — clean failure modes, NE collection errors. Tests su SPECIFIKACIJA
za Dev; Dev RED → GREEN cikl mora satisfijati svaki [MUST] test.

Naming convention: srpska latinica + engleski; bez ćirilice.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

import pytest


# =============================================================================
# Konstante (project paths)
# =============================================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

TEMPLATES_DIR = PROJECT_ROOT / "templates"
PARTIALS_DIR = TEMPLATES_DIR / "partials"
BASE_HTML = TEMPLATES_DIR / "base.html"

STATIC_DIR = PROJECT_ROOT / "static"
STATIC_CSS_DIR = STATIC_DIR / "css"
MAIN_CSS = STATIC_CSS_DIR / "main.css"
COMPONENTS_DIR = STATIC_CSS_DIR / "components"
STATIC_JS_DIR = STATIC_DIR / "js"
STATIC_IMG_DIR = STATIC_DIR / "img"

# Story 1.8 — 3 nova partial-a
PARTIAL_HEADER = PARTIALS_DIR / "header.html"
PARTIAL_FOOTER = PARTIALS_DIR / "footer.html"
PARTIAL_LANGUAGE_SWITCHER_NAV = PARTIALS_DIR / "language_switcher_nav.html"

ALL_NEW_PARTIALS = [
    PARTIAL_HEADER,
    PARTIAL_FOOTER,
    PARTIAL_LANGUAGE_SWITCHER_NAV,
]

# Story 1.8 — 3 nova CSS fajla
CSS_HEADER = COMPONENTS_DIR / "header.css"
CSS_FOOTER = COMPONENTS_DIR / "footer.css"
CSS_STICKY_NAV = COMPONENTS_DIR / "sticky-nav.css"

ALL_NEW_CSS_FILES = [
    CSS_HEADER,
    CSS_FOOTER,
    CSS_STICKY_NAV,
]

# Story 1.8 — 1 novi JS fajl
JS_STICKY_NAV = STATIC_JS_DIR / "sticky-nav.js"

# Story 1.8 — 2 nova logo asset-a (Task 1.10 provisioning)
LOGO_DARK = STATIC_IMG_DIR / "coric-agrar-logo-transp-200.png"
LOGO_LIGHT = STATIC_IMG_DIR / "coric-agrar-logo-transp-light-200.png"

# Test 1.6 regression file (Task 10a target)
TEST_BASE_TEMPLATE_PY = PROJECT_ROOT / "tests" / "test_base_template.py"

# px whitelist (AC9 — hardkoderani px dozvoljeni u nova CSS fajla)
# Includes 767 because Decision D4/D5 + multiple AC tests (e.g.
# test_ac2_top_header_mobile_height_auto_override_in_sticky_nav_css) mandate
# `@media (max-width: 767px)` literal breakpoint in 3 new CSS files. Without 767
# in the whitelist, AC9 px-discipline test conflicts with the mobile-breakpoint
# AC2/AC6 tests (TEST_MODIFICATION GREEN-phase fix).
PX_WHITELIST = {1, 2, 44, 60, 80, 40, 56, 100, 120, 767}

# unitless magic number whitelist (AC9 — CRITICAL-12 split)
UNITLESS_WHITELIST = {1020}

TEST_SECRET = "test-secret-key-for-tea-story-1-8-navigation-chrome-not-real"


# =============================================================================
# Helper funkcije (paralela sa test_visual_components.py)
# =============================================================================


def _ensure_sys_path() -> None:
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))


def _setup_django() -> None:
    """Bootstrap Django (django.setup) idempotent za render testove."""
    _ensure_sys_path()
    os.environ.setdefault("DJANGO_SECRET_KEY", TEST_SECRET)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
    try:
        import django
    except ImportError:  # pragma: no cover
        pytest.fail("Django nije instaliran.")
    for mod_key in list(sys.modules.keys()):
        if mod_key.startswith("config.settings"):
            del sys.modules[mod_key]
    try:
        django.setup()
    except Exception as exc:
        pytest.skip(
            f"django.setup() ne uspeva: {type(exc).__name__}: {exc}. "
            f"Verovatno Story 1.6 / 1.7 environment je broken."
        )


def _render_partial(template_path: str, context: dict | None = None) -> str:
    """Render Django partial sa context-om. Fail-uje ako partial ne postoji."""
    _setup_django()
    try:
        from django.template import TemplateDoesNotExist
        from django.template.loader import render_to_string
        from django.test import RequestFactory
    except ImportError:
        pytest.skip("Django template engine nedostupan.")
    ctx = context or {}
    # language_switcher_nav.html requires request context — auto-inject ako nije već
    if "request" not in ctx:
        rf = RequestFactory()
        ctx["request"] = rf.get("/sr/")
    if "LANGUAGE_CODE" not in ctx:
        ctx["LANGUAGE_CODE"] = "sr"
    try:
        return render_to_string(template_path, ctx)
    except TemplateDoesNotExist as exc:
        pytest.fail(
            f"Partial '{template_path}' ne postoji (TemplateDoesNotExist). "
            f"Story 1.8 mora kreirati. {exc}"
        )


def _read_file(path: Path, kind: str = "file") -> str:
    """Procita fajl. Fail-uje ako ne postoji."""
    if not path.exists():
        pytest.fail(
            f"{kind} ne postoji na {path.relative_to(PROJECT_ROOT)}. "
            f"Story 1.8 mora kreirati."
        )
    return path.read_text(encoding="utf-8")


def _read_css(path: Path) -> str:
    return _read_file(path, kind="CSS fajl")


def _read_partial(path: Path) -> str:
    return _read_file(path, kind="Partial")


def _read_js_source(path: Path = JS_STICKY_NAV) -> str:
    return _read_file(path, kind="JS fajl")


def _read_base_html() -> str:
    if not BASE_HTML.exists():
        pytest.fail(f"templates/base.html ne postoji na {BASE_HTML}")
    return BASE_HTML.read_text(encoding="utf-8")


# =============================================================================
# AC1 — base.html structure + new files presence (6 testova)
# =============================================================================


# AC-1: 3 nova partial-a postoje
def test_ac1_all_3_new_partials_exist():
    """AC1: 3 nova partial-a (header.html, footer.html, language_switcher_nav.html) moraju postojati."""
    missing = [p.relative_to(PROJECT_ROOT) for p in ALL_NEW_PARTIALS if not p.exists()]
    assert not missing, (
        f"Sledeći partial-i ne postoje: {missing}. "
        f"Story 1.8 AC1 — svih 3 mora biti kreirano."
    )


# AC-1: 3 nova CSS fajla + 1 JS fajl postoje
def test_ac1_all_3_new_css_files_and_js_exist():
    """AC1: 3 nova CSS fajla + sticky-nav.js moraju postojati."""
    missing = [p.relative_to(PROJECT_ROOT) for p in ALL_NEW_CSS_FILES if not p.exists()]
    if not JS_STICKY_NAV.exists():
        missing.append(JS_STICKY_NAV.relative_to(PROJECT_ROOT))
    assert not missing, (
        f"Sledeći Story 1.8 fajlovi ne postoje: {missing}. Story 1.8 AC1."
    )


# AC-1: logo assets provisionovani (CRITICAL-8 + Task 1.10)
def test_ac1_logo_assets_present():
    """AC1 + CRITICAL-8: static/img/ + 2 logo PNG-a moraju postojati posle Task 1.10."""
    assert STATIC_IMG_DIR.exists() and STATIC_IMG_DIR.is_dir(), (
        "static/img/ direktorijum ne postoji. Story 1.8 Task 1.9 mora kreirati."
    )
    missing = []
    if not LOGO_DARK.exists():
        missing.append(LOGO_DARK.relative_to(PROJECT_ROOT))
    if not LOGO_LIGHT.exists():
        missing.append(LOGO_LIGHT.relative_to(PROJECT_ROOT))
    assert not missing, (
        f"Logo assets nedostaju: {missing}. "
        f"Story 1.8 Task 1.10 — `cp docs/Dizajn/_HTML/img/coric-agrar-logo-transp*.png static/img/`."
    )


# AC-1: main.css ima 3 nova @import direktiva za Story 1.8 komponente
def test_ac1_main_css_imports_3_story_1_8_components():
    """AC1: main.css mora sadržati 3 nova @import za header.css, footer.css, sticky-nav.css.

    Sintaksa: relative-with-dot `./components/...` per IMP-7 (Story 1.7 invariant).
    Story 1.7 imports 5 komponenata; Story 1.8 dodaje još 3 → ukupno 8.
    """
    css = _read_file(MAIN_CSS, kind="main.css")
    for name in ("header.css", "footer.css", "sticky-nav.css"):
        pattern = rf"@import\s+url\(\s*['\"]\./components/{re.escape(name)}['\"]\s*\)"
        assert re.search(pattern, css), (
            f"main.css NE sadrži `@import url('./components/{name}')`. "
            f"Story 1.8 AC1 + Task 1.8 — relative-with-dot syntax IMP-7."
        )


# AC-1: base.html includes header + footer + sticky-nav.js
def test_ac1_base_html_includes_header_footer_sticky_script():
    """AC1: base.html mora sadržati include header.html, include footer.html, i sticky-nav.js script tag."""
    src = _read_base_html()
    # header partial include
    header_pattern = r'\{%\s*include\s*[\'"]partials/header\.html[\'"]\s*%\}'
    assert re.search(header_pattern, src), (
        'base.html NE sadrži `{% include "partials/header.html" %}`. '
        "Story 1.8 AC1 + Task 5.2."
    )
    # footer partial include
    footer_pattern = r'\{%\s*include\s*[\'"]partials/footer\.html[\'"]\s*%\}'
    assert re.search(footer_pattern, src), (
        'base.html NE sadrži `{% include "partials/footer.html" %}`. '
        "Story 1.8 AC1 + Task 5.3."
    )
    # sticky-nav.js script tag with defer
    js_pattern = r'<script\s+src\s*=\s*[\'"]\{%\s*static\s*[\'"]js/sticky-nav\.js[\'"]\s*%\}[\'"]\s+defer\s*>'
    assert re.search(js_pattern, src), (
        "base.html NE sadrži `<script src=\"{% static 'js/sticky-nav.js' %}\" defer>`. "
        "Story 1.8 AC1 + Task 5.4."
    )


# AC-1 + CRITICAL-5: sentinel je direct child <body> PRE include header.html
def test_ac1_base_html_sentinel_before_header_include():
    """AC1 + CRITICAL-5: sentinel `<div class="coric-sticky-sentinel">` mora biti
    direct child <body> i pojaviti se PRE `{% include "partials/header.html" %}`.

    Sentinel mora biti VAN header.html — inače observer izgubi signal kad
    top-header dobije height: 0 u shrunk state.
    """
    src = _read_base_html()
    sentinel_idx = src.find("coric-sticky-sentinel")
    header_match = re.search(
        r'\{%\s*include\s*[\'"]partials/header\.html[\'"]\s*%\}', src
    )
    body_open_idx = src.find("<body>")
    assert sentinel_idx != -1, (
        "base.html NE sadrži `coric-sticky-sentinel`. Story 1.8 Task 5.2 + CRITICAL-5."
    )
    assert header_match is not None, (
        "base.html NE sadrži header.html include (drugi test hvata)."
    )
    assert body_open_idx != -1, "base.html NEMA <body> tag (regression)."
    assert body_open_idx < sentinel_idx < header_match.start(), (
        f"Sentinel nije direct child <body> PRE header.html include. "
        f"body_open={body_open_idx}, sentinel={sentinel_idx}, "
        f"header_include={header_match.start()}. CRITICAL-5."
    )


# AC-1 + CRITICAL-4: footer between </main> and {% aria_live %}
def test_ac1_base_html_footer_between_main_and_aria_live():
    """AC1 + CRITICAL-4: order u base.html mora biti: `</main>` → footer include → `{% aria_live %}`."""
    src = _read_base_html()
    main_close_idx = src.find("</main>")
    footer_match = re.search(
        r'\{%\s*include\s*[\'"]partials/footer\.html[\'"]\s*%\}', src
    )
    aria_live_idx = src.find("{% aria_live %}")
    assert main_close_idx != -1, "base.html NEMA </main> (regression)."
    assert footer_match is not None, "base.html NEMA footer include."
    assert aria_live_idx != -1, "base.html NEMA `{% aria_live %}` (regression)."
    assert main_close_idx < footer_match.start() < aria_live_idx, (
        f"Footer pozicija pogrešna. "
        f"</main>={main_close_idx}, footer={footer_match.start()}, aria_live={aria_live_idx}. "
        f"CRITICAL-4 kanonski order."
    )


# =============================================================================
# AC2 — Top header rendering (5 testova)
# =============================================================================


# AC-2: header partial rendera .coric-top-header sa role="banner"
def test_ac2_top_header_has_role_banner():
    """AC2 + CRITICAL-CASCADE-1 iter 2: `.coric-top-header` mora imati `role="banner"`.

    Promoted iz iter 1 role="region" → role="banner" jer flatten Option A uklonio
    <header class="coric-site-header"> wrapper koji je default banner landmark.
    """
    html = _render_partial("partials/header.html")
    assert "coric-top-header" in html, "Render NE sadrži `coric-top-header` klasu. AC2."
    # role="banner" mora biti u istom elementu kao coric-top-header
    pattern = r'class\s*=\s*["\'][^"\']*coric-top-header[^"\']*["\'][^>]*role\s*=\s*["\']banner["\']|role\s*=\s*["\']banner["\'][^>]*class\s*=\s*["\'][^"\']*coric-top-header'
    assert re.search(pattern, html), (
        'Render NE sadrži `role="banner"` na `.coric-top-header` div-u. '
        "AC2 + CRITICAL-CASCADE-1 iter 2 — banner ARIA landmark restoration."
    )


# AC-2: top header koristi <p> NE <address> za address (IMP-2)
def test_ac2_top_header_uses_p_not_address_for_address():
    """AC2 + IMP-2: top header koristi `<p class="coric-top-header__address">`, NE `<address>`.

    HTML5 `<address>` je rezervisan za nearest <article>/<body> contact info;
    company contact u top headeru NIJE semantički <address>. Footer koristi
    `<address>` (canonical site contact); top header je redundant nav chrome.
    """
    src = _read_partial(PARTIAL_HEADER)
    # Mora postojati <p class="...coric-top-header__address...">
    assert re.search(r"<p[^>]*coric-top-header__address", src), (
        'header.html NEMA `<p class="coric-top-header__address">`. '
        "AC2 + IMP-2 — top header address mora biti <p>, NE <address>."
    )
    # NE sme biti <address class="coric-top-header__address">
    assert not re.search(r"<address[^>]*coric-top-header__address", src), (
        'header.html koristi `<address class="coric-top-header__address">` — '
        "AC2 + IMP-2 zabranjuje (HTML5 semantika rezervisana za nearest body/article)."
    )


# AC-2: top header ima eksplicitnu height: 40px u full state (CRITICAL-CASCADE-4)
def test_ac2_top_header_has_explicit_height_40px_in_full_state():
    """AC2 + CRITICAL-CASCADE-4 iter 2: `.coric-top-header` mora imati `height: 40px` u full state.

    Bez eksplicitne numeričke vrednosti, CSS NE može animirati iz `auto` u `0`
    pri tranziciji u shrunk state-u.
    """
    css = _read_css(CSS_HEADER)
    # Mora postojati .coric-top-header blok sa height: 40px
    pattern = r"\.coric-top-header\s*\{[^}]*height\s*:\s*40px"
    assert re.search(pattern, css, re.DOTALL), (
        "header.css NEMA `height: 40px` na `.coric-top-header` (full state). "
        "AC2 + CRITICAL-CASCADE-4 iter 2 — explicit value enables shrunk-state animation."
    )


# AC-2: mobile override `.coric-top-header { height: auto }` u sticky-nav.css (POLISH-2 single source)
def test_ac2_top_header_mobile_height_auto_override_in_sticky_nav_css():
    """AC2 + POLISH-2 iter 3: mobile override `.coric-top-header { height: auto }`
    mora biti u sticky-nav.css (NE u header.css — single source per Decision D4).
    """
    css = _read_css(CSS_STICKY_NAV)
    # Mora postojati @media (max-width: 767px) blok koji sadrži .coric-top-header sa height: auto
    pattern = r"@media\s*\(\s*max-width\s*:\s*767px\s*\)\s*\{[^}]*\.coric-top-header[^}]*height\s*:\s*auto"
    assert re.search(pattern, css, re.DOTALL), (
        "sticky-nav.css NEMA `@media (max-width: 767px)` block sa `.coric-top-header { height: auto }`. "
        "AC2 + POLISH-2 iter 3 — single-sourced canonical mobile override."
    )


# AC-2: top header rendera <a href="tel:...">  za prodaja i servis telefon
def test_ac2_top_header_renders_tel_links_for_sales_and_service():
    """AC2: top header mora imati 2× `<a href="tel:...">` link-a (prodaja + servis)."""
    html = _render_partial("partials/header.html")
    tel_matches = re.findall(r'<a[^>]*href\s*=\s*["\']tel:[^"\']+["\']', html)
    assert len(tel_matches) >= 2, (
        f"Render ima {len(tel_matches)} `tel:` link(s), očekivano >= 2 (prodaja + servis). "
        f"AC2 + IMP-4 (servis hardkoderan placeholder)."
    )


# =============================================================================
# AC3 — Main nav rendering (5 testova)
# =============================================================================


# AC-3: nav ima navbar-expand-md klasu (CRITICAL-3, NE -lg)
def test_ac3_nav_uses_navbar_expand_md_not_lg():
    """AC3 + CRITICAL-3: `.coric-nav` mora imati `navbar-expand-md` klasu (NE `-lg`).

    EXPERIENCE.md mandira <768px = mobile breakpoint za hamburger; Bootstrap default
    `navbar-expand-lg` collapses <992px što ne odgovara.
    """
    html = _render_partial("partials/header.html")
    assert "navbar-expand-md" in html, (
        "Render NE sadrži `navbar-expand-md` klasu na nav. "
        "AC3 + CRITICAL-3 + Decision D5."
    )
    # NE sme biti navbar-expand-lg
    assert "navbar-expand-lg" not in html, (
        "Render sadrži `navbar-expand-lg` — CRITICAL-3 mandira `-md` umesto `-lg`."
    )


# AC-3: nav ima position: sticky sa z-index: 1020 (CRITICAL-12)
def test_ac3_nav_has_position_sticky_and_z_index_1020():
    """AC3 + CRITICAL-12: `.coric-nav` mora imati `position: sticky` + `z-index: 1020`.

    z-index 1020 je iznad Bootstrap dropdown 1000 + popover 1010, ispod modal 1055.
    """
    css = _read_css(CSS_HEADER)
    # .coric-nav mora imati position: sticky + z-index: 1020
    nav_block_pattern = r"\.coric-nav\s*\{[^}]*\}"
    nav_blocks = re.findall(nav_block_pattern, css, re.DOTALL)
    assert nav_blocks, "header.css NE sadrži `.coric-nav` blok. AC3."
    # Sve relevantne deklaracije proveravamo na globalnom CSS-u (sticky + z-index mogu biti u istom ili odvojenim pravilima)
    assert re.search(
        r"\.coric-nav\b[^{]*\{[^}]*position\s*:\s*sticky", css, re.DOTALL
    ), "header.css NEMA `position: sticky` na `.coric-nav`. AC3 + CRITICAL-7."
    assert re.search(r"\.coric-nav\b[^{]*\{[^}]*z-index\s*:\s*1020", css, re.DOTALL), (
        "header.css NEMA `z-index: 1020` na `.coric-nav`. AC3 + CRITICAL-12 "
        "(iznad Bootstrap dropdown 1000 i popover 1010)."
    )
    # NE sme biti z-index: 1000 na .coric-nav (stara vrednost)
    assert not re.search(
        r"\.coric-nav\b[^{]*\{[^}]*z-index\s*:\s*1000\b", css, re.DOTALL
    ), (
        "header.css koristi staru `z-index: 1000` na `.coric-nav` — CRITICAL-12 mandira 1020."
    )


# AC-3: logo wrap u {% url 'core:home' %} (CRITICAL-9)
def test_ac3_header_logo_uses_core_home_url_namespace():
    """AC3 + CRITICAL-9: header.html mora koristiti `{% url 'core:home' %}` na logo link-u.

    apps/core/urls.py ima `app_name = 'core'` + `path('', home, name='home')`;
    URL name je `core:home` (fully qualified namespace).
    """
    src = _read_partial(PARTIAL_HEADER)
    # Positive grep za core:home
    assert re.search(r"\{%\s*url\s+['\"]core:home['\"]", src), (
        "header.html NE koristi `{% url 'core:home' %}`. "
        "AC3 + CRITICAL-9 — namespace `core:home` je mandatory."
    )
    # Negative grep za bare 'home' bez namespace-a
    assert not re.search(r"\{%\s*url\s+['\"]home['\"]\s*%\}", src), (
        "header.html koristi `{% url 'home' %}` bez namespace-a — "
        "CRITICAL-9 mandira `core:home`."
    )


# AC-3 + IMP-3: search button NEMA aria-expanded atribut
def test_ac3_search_toggle_has_no_aria_expanded():
    """AC3 + IMP-3: search button NE SME imati `aria-expanded` atribut.

    Button trenutno NE controlsuje expanded state; Bootstrap toggle wiring stiže
    u Story 2.13. aria-expanded bez funkcionalnog toggle = a11y misinformation.
    """
    src = _read_partial(PARTIAL_HEADER)
    # Pronađi search-toggle button blok
    search_button_pattern = r"<button[^>]*coric-nav__search-toggle[^>]*>"
    matches = re.findall(search_button_pattern, src)
    assert matches, (
        'header.html NE sadrži `<button class="...coric-nav__search-toggle...">`. AC3.'
    )
    # Ni jedan match ne sme imati aria-expanded
    for m in matches:
        assert "aria-expanded" not in m, (
            f"Search-toggle button sadrži `aria-expanded` atribut. "
            f"AC3 + IMP-3 — button trenutno ne controls expanded state (Story 2.13 wiring). "
            f"Pronađen blok: {m!r}"
        )


# AC-3: header.html NEMA <header class="coric-site-header"> wrapper (CRITICAL-7 flatten)
def test_ac3_header_html_no_coric_site_header_wrapper():
    """AC3 + CRITICAL-7 + D17: header.html source NEMA `<header class="coric-site-header">` wrapper.

    Flatten Option A: .coric-top-header i <nav class="coric-nav"> su standalone
    siblings na template root.
    """
    src = _read_partial(PARTIAL_HEADER)
    assert not re.search(r"<header[^>]*coric-site-header", src), (
        'header.html sadrži `<header class="coric-site-header">` wrapper. '
        "AC3 + CRITICAL-7 + Decision D17 — flatten Option A mandira NO wrapper "
        "(top-header i nav su standalone siblings, nav-ov sticky containing block je <body>)."
    )


# =============================================================================
# AC4 — Language switcher nav partial (5 testova)
# =============================================================================


# AC-4: language_switcher_nav.html partial postoji
def test_ac4_language_switcher_nav_partial_exists():
    """AC4 + CRITICAL-1: NOVI partial language_switcher_nav.html mora postojati."""
    assert PARTIAL_LANGUAGE_SWITCHER_NAV.exists(), (
        f"Partial ne postoji na {PARTIAL_LANGUAGE_SWITCHER_NAV.relative_to(PROJECT_ROOT)}. "
        f"AC4 + CRITICAL-1 + Decision D3 — novi CSP-safe partial."
    )


# AC-4: language_switcher_nav.html NEMA inline event handlers
def test_ac4_language_switcher_nav_no_inline_handlers():
    """AC4 + CRITICAL-1: NOVI partial NE SME imati inline `onchange=`, `onclick=`, `onsubmit=`.

    Story 1.4 language_switcher.html ima inline `onchange="this.form.submit()"` —
    to je known CSP debt deferred to Story 1.9/8.x. NOVI partial mora biti CSP-friendly.
    """
    src = _read_partial(PARTIAL_LANGUAGE_SWITCHER_NAV)
    bad_handlers = ["onchange=", "onclick=", "onsubmit=", "onload=", "onmouseover="]
    found = [h for h in bad_handlers if h in src]
    assert not found, (
        f"language_switcher_nav.html sadrži inline handler(s): {found}. "
        f"AC4 + CRITICAL-1 + AC9 — CSP-friendly mandate."
    )


# AC-4: language_switcher_nav rendera <form action="{% url 'set_language' %}"> per locale
def test_ac4_language_switcher_nav_renders_forms_per_locale():
    """AC4: rendered output mora imati `<form>` element sa `action="..."` (set_language endpoint)."""
    html = _render_partial(
        "partials/language_switcher_nav.html", {"LANGUAGE_CODE": "sr"}
    )
    # Mora imati bar 1 <form action=...> (URL `set_language` resolve-uje na /i18n/setlang/)
    form_matches = re.findall(
        r'<form[^>]*action\s*=\s*["\'][^"\']*setlang[^"\']*["\']', html
    )
    assert form_matches, (
        'Rendered output NEMA `<form action="...setlang...">`. '
        "AC4 — language switcher mora koristiti POST na `{% url 'set_language' %}`."
    )
    # Mora imati bar 1 <button type="submit">
    assert re.search(r'<button[^>]*type\s*=\s*["\']submit["\']', html), (
        'Rendered output NEMA `<button type="submit">`. '
        "AC4 — CSP-friendly submit (NE inline onchange)."
    )


# AC-4: aria-current="page" na trenutnom locale buttonu
def test_ac4_language_switcher_nav_has_aria_current_on_current_locale():
    """AC4 + CRITICAL-2: rendered output mora imati `aria-current="page"` na trenutnom locale-u.

    GOV.UK precedent: `aria-current="page"` (NE `aria-current="true"`) — NVDA + JAWS
    najavljuju identično, ali `page` je semantic-richer za multi-page sajt.
    """
    html = _render_partial(
        "partials/language_switcher_nav.html", {"LANGUAGE_CODE": "sr"}
    )
    # Bar jedan element mora imati aria-current="page"
    assert 'aria-current="page"' in html, (
        'Rendered output NEMA `aria-current="page"`. '
        "AC4 + CRITICAL-2 — trenutni locale mora imati landmark indicator."
    )
    # Ukupno mora biti TAČNO 1 (samo trenutni)
    aria_current_count = html.count('aria-current="page"')
    assert aria_current_count == 1, (
        f'Rendered output ima {aria_current_count} `aria-current="page"`, očekivano TAČNO 1. '
        f"AC4 — samo trenutni locale (LANGUAGE_CODE='sr')."
    )


# AC-4: csrf_token rendered u language_switcher_nav.html
def test_ac4_language_switcher_nav_has_csrf_token():
    """AC4: NOVI partial mora koristiti `{% csrf_token %}` u svakom <form> (Django POST securty).

    POLISH-9 iter 3: 3× csrf_token per page rendered (cost ~450 bytes DOM, accepted per D3).
    """
    src = _read_partial(PARTIAL_LANGUAGE_SWITCHER_NAV)
    assert "{% csrf_token %}" in src, (
        "language_switcher_nav.html NE sadrži `{% csrf_token %}`. "
        "AC4 — POST form requires CSRF protection."
    )


# =============================================================================
# AC5 — sticky-nav.js (5 testova)
# =============================================================================


# AC-5: sticky-nav.js postoji i koristi IntersectionObserver
def test_ac5_sticky_nav_js_uses_intersection_observer():
    """AC5: sticky-nav.js mora sadržati `IntersectionObserver` substring.

    Anti-pattern: NE koristiti `addEventListener('scroll', ...)` (memory-leak; nije observer).
    """
    src = _read_js_source()
    assert "IntersectionObserver" in src, (
        "sticky-nav.js NE sadrži `IntersectionObserver`. "
        "AC5 — sentinel pattern za shrink-on-scroll."
    )


# AC-5: sticky-nav.js koristi IIFE pattern
def test_ac5_sticky_nav_js_uses_iife_pattern():
    """AC5: sticky-nav.js mora koristiti IIFE wrapper (function expression invocation).

    Pattern: `(function () { ... })();` ili `(() => { ... })();`.
    """
    src = _read_js_source()
    # Match (function () { ... })(); ili (() => { ... })();
    iife_pattern = r"\(\s*(?:function\s*\(\s*\)\s*\{|\(\s*\)\s*=>\s*\{)"
    assert re.search(iife_pattern, src), (
        "sticky-nav.js NE koristi IIFE pattern `(function () { ... })();` ili "
        "`(() => { ... })();`. AC5 — namespace isolation."
    )


# AC-5: NEMA global window pollution
def test_ac5_sticky_nav_js_no_window_pollution():
    """AC5: sticky-nav.js NE SME pisati u `window.<anything> = ...` (global pollution forbidden).

    Anti-pattern #6 — koristi se IIFE da spreči propagation u globalni namespace.
    `window.matchMedia(...)` poziv je dozvoljen (read-only API access, NE assignment).
    """
    src = _read_js_source()
    # Pattern: window.<name>\s*=\s*<value>  (assignment); izbegavamo window.matchMedia(...) callsite
    # window.matchMedia(...) je callsite (`(` ne `=`), nije match
    pollution_pattern = r"window\.\w+\s*="
    matches = re.findall(pollution_pattern, src)
    assert not matches, (
        f"sticky-nav.js sadrži global window assignment(s): {matches}. "
        f"AC5 — IIFE pattern + Anti-pattern #6: NEMA `window.<x> = ...`."
    )


# AC-5: matchMedia mobile bail + change listener (IMP-1)
def test_ac5_sticky_nav_js_has_matchmedia_change_listener():
    """AC5 + IMP-1: sticky-nav.js mora imati `mobileQuery.addEventListener('change', ...)`.

    Re-init/teardown observer pri prelazu 768px breakpoint-a (rotacija tableta).
    """
    src = _read_js_source()
    # Pattern: matchMedia(...max-width...767...)
    assert re.search(r"matchMedia\s*\(\s*['\"][^'\"]*max-width[^'\"]*767", src), (
        "sticky-nav.js NEMA `window.matchMedia('(max-width: 767px)')` poziv. "
        "AC5 + Decision D4 — mobile bail."
    )
    # Mora imati addEventListener('change', ...) na mobileQuery
    assert re.search(r"addEventListener\s*\(\s*['\"]change['\"]", src), (
        "sticky-nav.js NEMA `mobileQuery.addEventListener('change', ...)` listener. "
        "AC5 + IMP-1 — orientation/resize handling."
    )


# AC-5: toggle body.coric-nav-shrunk klasu (IMP-10 + Decision D13)
def test_ac5_sticky_nav_js_toggles_body_coric_nav_shrunk():
    """AC5 + IMP-10 + Decision D13: JS mora prebacivati `coric-nav-shrunk` klasu na document.body.

    body klasa je SOT za top-header collapse (D13 — sibling selector ne radi unazad).
    """
    src = _read_js_source()
    # Pattern: document.body.classList.toggle('coric-nav-shrunk', ...) ili add/remove
    body_toggle_pattern = r"document\.body\.classList\.(?:toggle|add|remove)\s*\(\s*['\"]coric-nav-shrunk['\"]"
    assert re.search(body_toggle_pattern, src), (
        "sticky-nav.js NEMA `document.body.classList.toggle('coric-nav-shrunk', ...)` (ili add/remove). "
        "AC5 + IMP-10 + Decision D13 — body klasa SOT za top-header collapse selector."
    )


# =============================================================================
# AC6 — Footer (4 testa)
# =============================================================================


# AC-6: footer ima role="contentinfo"
def test_ac6_footer_has_role_contentinfo():
    """AC6: `<footer>` mora imati `role="contentinfo"` (eksplicitno za starije AT-ove)."""
    html = _render_partial("partials/footer.html")
    assert re.search(r'<footer[^>]*role\s*=\s*["\']contentinfo["\']', html), (
        'footer.html NE rendera `<footer role="contentinfo">`. '
        "AC6 + AC8 — eksplicitan ARIA landmark."
    )


# AC-6: footer ima 4 col-md-3 kolone i 3 section_eyebrow include-a (PROIZVODI, NAJNOVIJE VESTI, KONTAKT)
def test_ac6_footer_renders_4_columns_with_3_section_eyebrows():
    """AC6: footer mora imati 4 `col-md-3` kolone + 3 Section Eyebrow include-a sa
    eksplicitnim heading-ovima ('PROIZVODI', 'NAJNOVIJE VESTI', 'KONTAKT').
    """
    html = _render_partial("partials/footer.html")
    # 4 col-md-3 kolone
    col_count = len(re.findall(r'class\s*=\s*["\'][^"\']*col-md-3', html))
    assert col_count == 4, (
        f"Rendered footer ima {col_count} `col-md-3` kolona, očekivano 4. AC6."
    )
    # 3 section_eyebrow konzumacije (verifikujemo eksplicitne heading tekstove)
    for heading in ("PROIZVODI", "NAJNOVIJE VESTI", "KONTAKT"):
        assert heading in html, (
            f"Rendered footer NE sadrži heading '{heading}'. "
            f"AC6 — Section Eyebrow konzumacija za sve 3 kolone (Story 1.7 reuse)."
        )
    # Section Eyebrow base klasa mora biti renderovana (3×)
    eyebrow_count = len(re.findall(r"coric-section-eyebrow\b", html))
    assert eyebrow_count >= 3, (
        f"Rendered footer ima {eyebrow_count} `.coric-section-eyebrow` mention(s), "
        f"očekivano >= 3 (jedan po koloni 2, 3, 4). AC6 + Story 1.7 reuse."
    )


# AC-6: footer rendera Lorem Ipsum placeholder (3×) + TODO komentar za Story 5.4
def test_ac6_footer_renders_lorem_ipsum_news_placeholder_with_todo():
    """AC6: kolona 3 mora imati 3× Lorem Ipsum naslova + TODO komentar za Story 5.4 replacement."""
    src = _read_partial(PARTIAL_FOOTER)
    # 3× Lorem ipsum u source-u (može biti `Lorem ipsum dolor sit amet`)
    lorem_count = len(re.findall(r"Lorem ipsum", src, re.IGNORECASE))
    assert lorem_count >= 3, (
        f"footer.html ima {lorem_count} Lorem ipsum naslov(a), očekivano >= 3. "
        f"AC6 — placeholder za Story 5.4 (dinamički BlogPost queryset)."
    )
    # TODO komentar za Story 5.4
    assert re.search(r"TODO:?\s*Story\s*5\.4", src) or re.search(
        r"Story\s*5\.4", src
    ), (
        "footer.html NE sadrži `TODO Story 5.4` komentar. "
        "AC6 — placeholder mora biti markiran za buduće dinamičko zamenjivanje."
    )


# AC-6 + BONUS-2: footer logo wrapped u {% url 'core:home' %}
def test_ac6_footer_logo_wrapped_in_core_home_link():
    """AC6 + BONUS-2 iter 3: footer logo mora biti wrapped u `<a href="{% url 'core:home' %}">`.

    Parity sa header logo-om (konzistentna UX expectation da klik na logo navigira na home).
    """
    src = _read_partial(PARTIAL_FOOTER)
    # Mora postojati {% url 'core:home' %} u footer.html
    assert re.search(r"\{%\s*url\s+['\"]core:home['\"]", src), (
        "footer.html NE koristi `{% url 'core:home' %}`. "
        "AC6 + BONUS-2 iter 3 — footer logo mora biti home link za parity sa header logo-om."
    )


# =============================================================================
# AC7 — A11y guards (3 testa)
# =============================================================================


# AC-7: sticky-nav.css ima @media (prefers-reduced-motion: reduce) override
def test_ac7_sticky_nav_css_has_prefers_reduced_motion_override():
    """AC7: sticky-nav.css MORA imati `@media (prefers-reduced-motion: reduce)` blok.

    Story 1.8 ŠALJE motion u produkciju (sticky shrink transition 200ms ease) →
    MORA da ga guard-uje (Story 1.7 CRITICAL-3 lekcija: ko šalje motion šalje i guard).
    """
    css = _read_css(CSS_STICKY_NAV)
    assert re.search(r"@media\s*\(\s*prefers-reduced-motion\s*:\s*reduce\s*\)", css), (
        "sticky-nav.css NE sadrži `@media (prefers-reduced-motion: reduce)`. "
        "AC7 + Story 1.7 CRITICAL-3 lekcija."
    )


# AC-7 + POLISH-3: reduced-motion takođe disable-uje visibility transition na shrunk top-header
def test_ac7_sticky_nav_css_reduced_motion_disables_visibility_transition():
    """AC7 + POLISH-3 iter 3: u reduced-motion mode-u, `body.coric-nav-shrunk .coric-top-header`
    mora imati `transition: none` (visibility instant-flips bez 200ms delay-a).

    Razlog: u reduced-motion mode-u, nema height transition da se sačeka, pa visibility
    mora flip instantno (kombinacija WCAG 2.4.7 tab order + reduced-motion respect).
    """
    css = _read_css(CSS_STICKY_NAV)
    # Pronađi @media (prefers-reduced-motion: reduce) blok
    reduced_motion_match = re.search(
        r"@media\s*\(\s*prefers-reduced-motion\s*:\s*reduce\s*\)\s*\{(.+?)\}\s*(?=@media|\Z)",
        css,
        re.DOTALL,
    )
    assert reduced_motion_match, (
        "sticky-nav.css NE sadrži `@media (prefers-reduced-motion: reduce)` blok (drugi test hvata)."
    )
    reduced_motion_block = reduced_motion_match.group(1)
    # Unutar blok-a mora postojati body.coric-nav-shrunk .coric-top-header { transition: none }
    pattern = (
        r"body\.coric-nav-shrunk\s+\.coric-top-header[^{]*\{[^}]*transition\s*:\s*none"
    )
    assert re.search(pattern, reduced_motion_block, re.DOTALL), (
        "sticky-nav.css `@media (prefers-reduced-motion: reduce)` blok NE sadrži "
        "`body.coric-nav-shrunk .coric-top-header { transition: none }`. "
        "POLISH-3 iter 3 — bez ovog, WCAG 2.4.7 tab order failu se u reduced-motion mode-u."
    )


# AC-7: header.css i footer.css imaju @media (forced-colors: active) override (WHCM)
def test_ac7_header_css_has_forced_colors_override():
    """AC7: header.css mora imati `@media (forced-colors: active)` override.

    Windows High Contrast Mode — focus-visible outline mora postati `CanvasText`
    da bude vidljivo u WHCM.
    """
    css = _read_css(CSS_HEADER)
    assert re.search(r"@media\s*\(\s*forced-colors\s*:\s*active\s*\)", css), (
        "header.css NE sadrži `@media (forced-colors: active)`. "
        "AC7 — Windows High Contrast Mode focus visibility."
    )


# =============================================================================
# AC8 — ARIA landmarks (2 testa)
# =============================================================================


# AC-8: header.html rendera role="banner" + role="navigation" (top-header + nav)
def test_ac8_header_renders_banner_and_navigation_landmarks():
    """AC8: rendered header.html mora imati `role="banner"` (top-header) + `role="navigation"` (nav)."""
    html = _render_partial("partials/header.html")
    # role="banner"
    assert 'role="banner"' in html, (
        'Rendered header NEMA `role="banner"` (top-header). '
        "AC8 + CRITICAL-CASCADE-1 iter 2."
    )
    # role="navigation"
    assert 'role="navigation"' in html, (
        'Rendered header NEMA `role="navigation"` (nav). AC8.'
    )


# AC-8: tačno 1× role="banner" per partial (WAI-ARIA APG compliance)
def test_ac8_header_has_exactly_one_banner_landmark():
    """AC8: rendered header.html mora imati TAČNO 1× `role="banner"`.

    WAI-ARIA Authoring Practices: jedan banner po stranici je preporučen.
    """
    html = _render_partial("partials/header.html")
    banner_count = html.count('role="banner"')
    assert banner_count == 1, (
        f'Rendered header ima {banner_count} `role="banner"` landmark(s), očekivano TAČNO 1. '
        f"AC8 + WAI-ARIA APG."
    )


# =============================================================================
# AC9 — Token discipline + anti-patterns (5 testova)
# =============================================================================


# AC-9: nijedan hardcoded hex u 3 nova CSS fajla
def test_ac9_no_hardcoded_hex_in_3_new_css_files():
    """AC9: grep negative za `#XXXXXX`, `#XXX` u 3 nova CSS fajla.

    Sve boje preko `var(--color-*)` tokena. Whitelist: `transparent`, `inherit`,
    `currentColor`, `white` (CSS keyword).
    """
    offending = []
    for css_path in ALL_NEW_CSS_FILES:
        css = _read_css(css_path)
        matches = re.findall(r"#[0-9a-fA-F]{3,8}\b", css)
        if matches:
            offending.append((css_path.name, matches))
    assert not offending, (
        f"Hardcoded hex u 3 nova CSS fajla: {offending}. "
        f"AC9 — sve boje MORAJU biti `var(--color-*)`."
    )


# AC-9: nijedan hardcoded px van whitelist-a u 3 nova CSS fajla
def test_ac9_no_hardcoded_px_outside_whitelist_in_3_new_css_files():
    """AC9: grep `\\d+px` u 3 nova CSS, sve van whitelist-a `[1, 2, 44, 60, 80, 40, 56, 100, 120]` forbidden.

    Whitelist obuhvata: borders (1, 2), WCAG touch target (44), nav heights (60, 80),
    logo dimensions (40, 56), sentinel offset (100), chrome reserve (120).
    """
    offending = []
    for css_path in ALL_NEW_CSS_FILES:
        css = _read_css(css_path)
        # Match svaki `<int>px` token sa word boundary
        for m in re.finditer(r"(?<!\d)(\d+)px\b", css):
            value = int(m.group(1))
            if value not in PX_WHITELIST:
                offending.append((css_path.name, f"{value}px"))
    assert not offending, (
        f"Hardcoded px van whitelist-a {sorted(PX_WHITELIST)} u 3 nova CSS fajla: {offending}. "
        f"AC9 — sve ostale vrednosti MORAJU biti `var(--spacing-*)`."
    )


# AC-9: nijedan inline style="" u 3 nova partial-a
def test_ac9_no_inline_style_attribute_in_3_new_partials():
    """AC9: grep negative za `style="..."` u 3 nova partial-a.

    Scope STROGO na NEW files; Story 1.4 language_switcher.html (sa inline onchange=)
    je known CSP debt — NE testira se ovde.
    """
    offending = []
    for partial_path in ALL_NEW_PARTIALS:
        src = _read_partial(partial_path)
        if re.search(r'\bstyle\s*=\s*["\']', src):
            offending.append(partial_path.name)
    assert not offending, (
        f'Inline `style="..."` u 3 nova partial-a: {offending}. '
        f"AC9 — sve preko klasa + tokens."
    )


# AC-9: nijedan inline event handler ili <script> u 3 nova partial-a
def test_ac9_no_inline_scripts_or_handlers_in_3_new_partials():
    """AC9: grep negative za inline `onclick=`, `onchange=`, `onsubmit=`, `<script` u 3 nova partial-a."""
    bad_handlers = [
        "onclick=",
        "onchange=",
        "onsubmit=",
        "onload=",
        "onmouseover=",
        "<script",
    ]
    offending = []
    for partial_path in ALL_NEW_PARTIALS:
        src = _read_partial(partial_path)
        for handler in bad_handlers:
            if handler in src:
                offending.append((partial_path.name, handler))
    assert not offending, (
        f"Inline scripts ili handlers u 3 nova partial-a: {offending}. "
        f"AC9 — CSP-friendly mandate."
    )


# AC-9: nijedan ćirilični karakter u novim fajlovima
def test_ac9_no_cyrillic_in_new_files():
    """AC9: grep negative za ćirilične karaktere `[Ѐ-ӿ]` u svim novim Story 1.8 fajlovima."""
    cyrillic_pattern = re.compile(r"[Ѐ-ӿ]")
    offending = []
    all_new_files = list(ALL_NEW_PARTIALS) + list(ALL_NEW_CSS_FILES) + [JS_STICKY_NAV]
    for path in all_new_files:
        if not path.exists():
            continue  # Drugi testovi hvataju missing files
        try:
            src = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue  # Logo PNG fajlovi — skip
        if cyrillic_pattern.search(src):
            offending.append(path.name)
    assert not offending, (
        f"Ćirilični karakteri pronađeni u: {offending}. "
        f"AC9 — sve latinica (project-context.md § Critical Don't-Miss)."
    )


# =============================================================================
# AC10 — Story 1.6 regression test update (Task 10a — 1 test)
# =============================================================================


# AC-10 + CRITICAL-CASCADE-2: test_base_template.py::test_ac2_skip_link_first_child_of_body migriran
def test_ac10_story_1_6_regression_test_migrated_to_regex_pattern():
    """AC10 + CRITICAL-CASCADE-2 + POLISH-7 iter 3: Story 1.6 regression test invariant
    je migriran iz literal `src.find("<header>")` u regex `re.search` pattern.

    Task 10a deliverable Story 1.8 — tests/test_base_template.py::test_ac2_skip_link_first_child_of_body
    mora biti UPDATE-ovan da se ne oslanja na `<header>` tag presence (Story 1.8 flatten Option A
    uklanja <header> wrapper). Novi assert: `re.search(r'\\{%\\s*include\\s*[\\'\"]partials/header\\.html[\\'\"]\\s*%\\}', src)`.
    """
    src = _read_file(TEST_BASE_TEMPLATE_PY, kind="test_base_template.py")
    # Pronađi telo test_ac2_skip_link_first_child_of_body funkcije
    func_match = re.search(
        r"def\s+test_ac2_skip_link_first_child_of_body\s*\([^)]*\)\s*:(.+?)(?=\ndef\s+|\Z)",
        src,
        re.DOTALL,
    )
    assert func_match, (
        "tests/test_base_template.py NEMA `test_ac2_skip_link_first_child_of_body` funkciju (regression)."
    )
    func_body = func_match.group(1)
    # Telo NE SME imati `src.find("<header>")` (stari pattern)
    assert (
        'src.find("<header>")' not in func_body
        and "src.find('<header>')" not in func_body
    ), (
        'test_ac2_skip_link_first_child_of_body i dalje koristi `src.find("<header>")` '
        "(stari Story 1.6 pattern). Task 10a + POLISH-7 iter 3 mandira migration na "
        "`re.search(r'\\{%\\s*include\\s*...partials/header.html...\\s*%\\}', src)`."
    )
    # Telo MORA imati re.search za partials/header.html pattern
    assert re.search(r"re\.search\s*\([^)]*partials/header", func_body), (
        "test_ac2_skip_link_first_child_of_body NEMA `re.search(...partials/header...)` pattern. "
        "Task 10a + POLISH-7 iter 3 — regex umesto literal .find()."
    )


# =============================================================================
# DEFERRED tests (SHOULD scenarios deferred to Story 9.8 Playwright)
# =============================================================================


@pytest.mark.skip(
    reason=(
        "DEFERRED to Story 1.9 Lighthouse CI gate / Story 9.8 Playwright E2E. "
        "CLS metric measurement requires browser-driven scroll simulation; "
        "pytest cannot measure scroll-induced reflow timing. "
        "Story 1.8 accepts CLS impact minimized via smooth transition + CWV "
        "user input grace window (see CRITICAL-CASCADE-5 + Acceptable Layout Behavior subsection)."
    )
)
def test_cls_metric_top_header_collapse_within_threshold():
    """DEFERRED: CLS (Cumulative Layout Shift) verification top-header collapse < 0.1.

    Aspirational test — verifikuje da scroll past 100px sentinel-a NE prelazi
    CLS threshold 0.1 (Lighthouse Good rating). Pending Story 1.9 CI Lighthouse
    gate sa `lighthouse --emulated-form-factor=desktop` + scroll simulation.
    """
    pytest.fail(
        "Test je @pytest.mark.skip — ne bi smeo biti pozvan. "
        "Deferred do Story 1.9 Lighthouse gate."
    )


@pytest.mark.skip(
    reason=(
        "DEFERRED to Story 9.8 Playwright E2E. "
        "Real scroll behavior (`window.scrollTo` + assert class promenjena) requires "
        "browser DOM (pytest cannot simulate IntersectionObserver fire); "
        "Story 1.8 grep-tests verifikuju observer wiring + CSS contract."
    )
)
def test_sticky_nav_real_scroll_toggles_shrunk_class():
    """DEFERRED: real scroll behavior — window.scrollTo(0, 200) → body.coric-nav-shrunk added.

    Aspirational E2E test — Playwright zna ovo, pytest ne.
    """
    pytest.fail(
        "Test je @pytest.mark.skip — ne bi smeo biti pozvan. "
        "Deferred do Story 9.8 Playwright."
    )
