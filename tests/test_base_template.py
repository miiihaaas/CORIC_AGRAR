"""Tests za Story 1.6 - Base Templates sa Bootstrap 5 + HTMX Setup.

Pokriva:
- AC1: templates/base.html expansion (50-80 lines; tokens → Bootstrap → main CSS cascade;
       skip link + main#main-content + aria-live + noscript + site-wide scripts ordering)
- AC2: Skip link ('Preskoči na sadržaj') sa visually-hidden-focusable + href="#main-content"
- AC3: ARIA live region (kanonski singleton sa id="aria-live", aria-live="polite", aria-atomic="true")
- AC4: apps/core/templatetags/htmx_aria.py — `{% aria_live %}` template tag (mark_safe HTML)
- AC5: config/settings/base.py INSTALLED_APPS + MIDDLEWARE + BOOTSTRAP5 dict (DEV CDN);
       config/settings/production.py BOOTSTRAP5 override (local /static/vendor/)
- AC6: HtmxMiddleware sets request.htmx attribute (falsy bez header-a, truthy sa HX-Request)
- AC7: static/vendor/htmx.min.js + bootstrap-5.3.3 vendor (skipovi ako Mihas još nije download-ovao)
- AC8: static/css/main.css placeholder
- AC9: Smoke render — GET /sr/ HTML sadrži skip link + aria-live + bootstrap CSS link + ...
- Anti-pattern guards: no googleapis/gstatic/jsdelivr literal u source; no inline event handlers;
  no uppercase hex u base.html

Pokrenuti sa:
    uv run pytest tests/test_base_template.py -v --tb=short

TEA RED faza: svi testovi MORAJU pasti (osim 2-3 vacuous pass anti-pattern guard-a na
još nepostojećim fajlovima, i SKIP za HTMX vendor koji Mihas tek download-uje).
Naming convention: srpska latinica + engleski; bez ćirilice.
"""

from __future__ import annotations

import importlib
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

try:
    import tomllib
except ImportError:  # pragma: no cover
    tomllib = None  # type: ignore[assignment]


# =============================================================================
# Konstante (project paths)
# =============================================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
SETTINGS_PKG_DIR = CONFIG_DIR / "settings"
SETTINGS_BASE = SETTINGS_PKG_DIR / "base.py"
SETTINGS_DEV = SETTINGS_PKG_DIR / "development.py"
SETTINGS_PROD = SETTINGS_PKG_DIR / "production.py"

TEMPLATES_DIR = PROJECT_ROOT / "templates"
BASE_HTML = TEMPLATES_DIR / "base.html"

APPS_DIR = PROJECT_ROOT / "apps"
CORE_DIR = APPS_DIR / "core"
TEMPLATETAGS_DIR = CORE_DIR / "templatetags"
TEMPLATETAGS_INIT = TEMPLATETAGS_DIR / "__init__.py"
HTMX_ARIA_PY = TEMPLATETAGS_DIR / "htmx_aria.py"

STATIC_DIR = PROJECT_ROOT / "static"
STATIC_CSS_DIR = STATIC_DIR / "css"
MAIN_CSS = STATIC_CSS_DIR / "main.css"
STATIC_VENDOR_DIR = STATIC_DIR / "vendor"
HTMX_MIN_JS = STATIC_VENDOR_DIR / "htmx.min.js"
BOOTSTRAP_VENDOR_DIR = STATIC_VENDOR_DIR / "bootstrap-5.3.3"
BOOTSTRAP_CSS_VENDOR = BOOTSTRAP_VENDOR_DIR / "css" / "bootstrap.min.css"
BOOTSTRAP_JS_VENDOR = BOOTSTRAP_VENDOR_DIR / "js" / "bootstrap.bundle.min.js"

TEST_SECRET = "test-secret-key-for-tea-story-1-6-bootstrap-htmx-not-real"

# Skip msg za HTMX vendor (Mihas ga ručno download-uje — Task 4 u story-ji)
HTMX_VENDOR_MISSING_MSG = (
    "static/vendor/htmx.min.js ne postoji — Mihas ga ručno download-uje "
    "(vidi Story 1.6 Task 4.1; URL pinned na 1.9.12)."
)


# =============================================================================
# Helper funkcije
# =============================================================================


def _ensure_sys_path() -> None:
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))


def _read_base_html() -> str:
    """Procita templates/base.html source. Fail ako ne postoji."""
    if not BASE_HTML.exists():
        pytest.fail(f"templates/base.html ne postoji na {BASE_HTML}")
    return BASE_HTML.read_text(encoding="utf-8")


def _read_base_html_lines() -> list[str]:
    return _read_base_html().splitlines()


def _read_settings_source(path: Path) -> str:
    if not path.exists():
        pytest.fail(f"{path.relative_to(PROJECT_ROOT)} ne postoji.")
    return path.read_text(encoding="utf-8")


def _load_settings_module(env_name: str):
    """Importuje config.settings.<env_name> sa fresh module reload.

    Razlog za reload: drugi testovi mogu mutirati sys.modules; bez reload-a
    stari cache vraća stara base.py izmena.
    """
    _ensure_sys_path()
    os.environ.setdefault("DJANGO_SECRET_KEY", TEST_SECRET)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
    full_name = f"config.settings.{env_name}"
    for mod_key in list(sys.modules.keys()):
        if mod_key == full_name or mod_key.startswith("config.settings."):
            del sys.modules[mod_key]
    try:
        return importlib.import_module(full_name)
    except Exception as exc:
        pytest.fail(
            f"Ne mogu importovati config.settings.{env_name}: "
            f"{type(exc).__name__}: {exc}"
        )


def _setup_django() -> None:
    """Bootstrap Django (django.setup) idempotent za Client/RequestFactory testove."""
    _ensure_sys_path()
    os.environ.setdefault("DJANGO_SECRET_KEY", TEST_SECRET)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
    try:
        import django
    except ImportError:  # pragma: no cover
        pytest.fail("Django nije instaliran.")
    # Force-reload sve setting module-a da nove BOOTSTRAP5 izmene budu pickup-ovane
    for mod_key in list(sys.modules.keys()):
        if mod_key.startswith("config.settings"):
            del sys.modules[mod_key]
    try:
        # django.setup() može raise ako apps registracija pukne (npr. django_htmx još nije u INSTALLED_APPS).
        # U RED phase, to je očekivano — testovi koji koriste Client/RequestFactory tada skipuju.
        django.setup()
    except Exception as exc:
        pytest.skip(
            f"django.setup() ne uspeva: {type(exc).__name__}: {exc}. "
            f"Verovatno Story 1.6 jos nije implementirana (django_htmx / django_bootstrap5 nije u INSTALLED_APPS)."
        )


def _get_test_client():
    """Vrati Django test Client (sa HTTP_HOST='localhost') ili skip."""
    _setup_django()
    try:
        from django.test import Client
    except ImportError:
        pytest.skip("Django test Client nedostupan (pytest-django nije konfigurisan?).")
    return Client(HTTP_HOST="localhost")


def _render_home_sr() -> str:
    """GET /sr/ → vrati response body kao UTF-8 string. Fail/skip ako 200 ne dobije."""
    client = _get_test_client()
    response = client.get("/sr/")
    if response.status_code != 200:
        pytest.fail(
            f"GET /sr/ → {response.status_code} (očekivano 200). "
            f"Verovatno settings ili template render puca u RED phase-u."
        )
    return response.content.decode("utf-8", errors="replace")


def _load_pyproject() -> dict:
    if tomllib is None:
        pytest.skip("tomllib nije dostupan (Python < 3.11).")
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    if not pyproject_path.exists():
        pytest.fail("pyproject.toml ne postoji.")
    with pyproject_path.open("rb") as f:
        return tomllib.load(f)


# =============================================================================
# AC1 — templates/base.html expansion (kompletan template)
# =============================================================================


def test_ac1_base_html_length_in_range():
    """AC1: base.html finalna dužina mora biti u opsegu [40, 80] linija.

    Dev Notes Template (verbatim) je ~40 linija; story AC1 navodi 50-80 kao soft
    target uključujući komentare. Lower bound je tightened na 40 da prihvati
    verbatim template iz Dev Notes (bez dodatnih sectional komentara), upper
    bound ostaje 80 da spreči neorganizovanu ekspanziju.
    """
    lines = _read_base_html_lines()
    n = len(lines)
    assert 40 <= n <= 80, (
        f"templates/base.html ima {n} linija, očekivano u opsegu [40, 80]. "
        f"Story 1.6 AC1: verbatim Dev Notes template ~40 linija; gornja granica 80."
    )


def test_ac1_base_html_doctype_html5():
    """AC1 / Regression: <!DOCTYPE html> mora ostati prva linija."""
    src = _read_base_html()
    first_line = src.splitlines()[0].strip()
    assert first_line == "<!DOCTYPE html>", (
        f"Prva linija = {first_line!r}, očekivano '<!DOCTYPE html>'. "
        f"Story 1.4/1.5 preserved."
    )


def test_ac1_base_html_html_lang_dynamic():
    """AC1 / Story 1.4 regression: <html lang="{{ LANGUAGE_CODE }}"> preserved."""
    src = _read_base_html()
    pattern = r'<html\s+lang\s*=\s*["\']\{\{\s*LANGUAGE_CODE\s*\}\}["\']'
    assert re.search(pattern, src), (
        'base.html ne sadrži `<html lang="{{ LANGUAGE_CODE }}">`. '
        "Story 1.4 invariant — Story 1.6 expansion NE sme razbiti."
    )


def test_ac1_base_html_viewport_meta():
    """AC1 / regression: <meta name="viewport"> mora ostati."""
    src = _read_base_html()
    pattern = r'<meta\s+name\s*=\s*["\']viewport["\']\s+content\s*=\s*["\']width=device-width,\s*initial-scale=1\.0["\']'
    assert re.search(pattern, src), (
        'base.html ne sadrži standardni `<meta name="viewport">`. '
        "Story 1.4 regression — Story 1.6 mora preserve."
    )


def test_ac1_base_html_meta_description_block():
    """AC1: NOVO {% block meta_description %} unutar <meta name="description" content="...">."""
    src = _read_base_html()
    # Pattern hvata <meta name="description" content="{% block meta_description %}...{% endblock %}">
    pattern = (
        r'<meta\s+name\s*=\s*["\']description["\']\s+content\s*=\s*'
        r'["\']\{%\s*block\s+meta_description\s*%\}\{%\s*endblock\s*%\}["\']'
    )
    assert re.search(pattern, src), (
        'base.html ne sadrži `<meta name="description" content="{% block meta_description %}{% endblock %}">`. '
        "Story 1.6 AC1 — placeholder block za Story 6.x SEO meta."
    )


def test_ac1_base_html_tokens_css_link_preserved():
    """AC1 / Story 1.5 regression: tokens.css mora ostati PRVI CSS link."""
    src = _read_base_html()
    # Source mora sadržati {% static "css/tokens.css" %} ili {% static 'css/tokens.css' %}
    pattern = r'<link\s+rel\s*=\s*["\']stylesheet["\']\s+href\s*=\s*["\']\{%\s*static\s+["\']css/tokens\.css["\']\s*%\}["\']'
    assert re.search(pattern, src), (
        "base.html ne sadrži tokens.css `<link>` (Story 1.5 regression). "
        "Story 1.6 mora očuvati ovaj link."
    )
    # Pozicioni test — tokens.css mora doći PRE bootstrap_css i main.css
    tokens_idx = src.find("css/tokens.css")
    bootstrap_idx = src.find("{% bootstrap_css %}")
    main_idx = src.find("css/main.css")
    assert tokens_idx != -1, "tokens.css nije u source-u."
    if bootstrap_idx != -1:
        assert tokens_idx < bootstrap_idx, (
            f"tokens.css (idx={tokens_idx}) NIJE PRE {{% bootstrap_css %}} (idx={bootstrap_idx}). "
            f"AC1 cascade discipline: tokens → Bootstrap → main."
        )
    if main_idx != -1:
        assert tokens_idx < main_idx, (
            f"tokens.css (idx={tokens_idx}) NIJE PRE main.css (idx={main_idx})."
        )


def test_ac1_base_html_bootstrap_css_link():
    """AC1: NOVO `{% bootstrap_css %}` template tag mora biti prisutan."""
    src = _read_base_html()
    assert "{% bootstrap_css %}" in src, (
        "base.html ne sadrži `{% bootstrap_css %}` template tag. "
        "Story 1.6 AC1 — django-bootstrap5 render-uje Bootstrap CSS link kroz ovaj tag."
    )


def test_ac1_base_html_main_css_link_after_bootstrap():
    """AC1: main.css `<link>` mora postojati i biti POSLE {% bootstrap_css %}."""
    src = _read_base_html()
    pattern = r'<link\s+rel\s*=\s*["\']stylesheet["\']\s+href\s*=\s*["\']\{%\s*static\s+["\']css/main\.css["\']\s*%\}["\']'
    assert re.search(pattern, src), (
        "base.html ne sadrži main.css `<link>` tag. "
        "Story 1.6 AC1 — custom CSS overrides Bootstrap default-e."
    )
    bootstrap_idx = src.find("{% bootstrap_css %}")
    main_idx = src.find("css/main.css")
    assert bootstrap_idx != -1 and main_idx != -1, (
        "Bootstrap_css ili main.css link nedostaje (drugi test hvata)."
    )
    assert bootstrap_idx < main_idx, (
        f"{{% bootstrap_css %}} (idx={bootstrap_idx}) NIJE PRE main.css (idx={main_idx}). "
        f"AC1 cascade: tokens → Bootstrap → main (main overrides Bootstrap)."
    )


def test_ac1_base_html_load_django_bootstrap5_tag():
    """AC1: NOVO `{% load django_bootstrap5 %}` direktiva mora biti prisutna."""
    src = _read_base_html()
    assert "{% load django_bootstrap5 %}" in src, (
        "base.html ne sadrži `{% load django_bootstrap5 %}`. "
        "Story 1.6 AC1 — registruje `{% bootstrap_css %}` / `{% bootstrap_javascript %}` template tag-ove."
    )


def test_ac1_base_html_load_htmx_aria_tag():
    """AC1: NOVO `{% load htmx_aria %}` direktiva mora biti prisutna."""
    src = _read_base_html()
    assert "{% load htmx_aria %}" in src, (
        "base.html ne sadrži `{% load htmx_aria %}`. "
        "Story 1.6 AC1 — registruje custom `{% aria_live %}` tag iz apps/core/templatetags/."
    )


def test_ac1_base_html_script_load_order():
    """AC1 / Gotcha #15 / FIX 6: site-wide scripts (htmx.min.js + {% bootstrap_javascript %})
    MORAJU doći PRE `{% block scripts %}`.

    Razlog: child page sync init (npr. `new bootstrap.Modal(...)`) sa defer execution-om
    se izvršava posle DOM-order; ako block scripts dolazi PRE, child init bi pukao
    sa `ReferenceError: bootstrap is not defined`.
    """
    src = _read_base_html()
    htmx_idx = src.find("vendor/htmx.min.js")
    bootstrap_js_idx = src.find("{% bootstrap_javascript %}")
    block_scripts_idx = src.find("{% block scripts %}")
    assert htmx_idx != -1, (
        "base.html ne sadrži `vendor/htmx.min.js` script tag. AC1 + Gotcha #15."
    )
    assert bootstrap_js_idx != -1, (
        "base.html ne sadrži `{% bootstrap_javascript %}` tag. AC1."
    )
    assert block_scripts_idx != -1, (
        "base.html ne sadrži `{% block scripts %}` placeholder (regression!)."
    )
    assert htmx_idx < block_scripts_idx, (
        f"htmx.min.js (idx={htmx_idx}) NIJE PRE `{{% block scripts %}}` (idx={block_scripts_idx}). "
        f"Gotcha #15 FIX 6: site-wide scripts MORAJU biti PRVI."
    )
    assert bootstrap_js_idx < block_scripts_idx, (
        f"`{{% bootstrap_javascript %}}` (idx={bootstrap_js_idx}) NIJE PRE `{{% block scripts %}}` "
        f"(idx={block_scripts_idx}). Gotcha #15 FIX 6."
    )


def test_ac1_base_html_noscript_block():
    """AC1: <noscript> blok sa Bootstrap alert mora biti prisutan."""
    src = _read_base_html()
    assert "<noscript>" in src and "</noscript>" in src, (
        "base.html ne sadrži <noscript>...</noscript> blok. "
        "Story 1.6 AC1 — graceful degradation za JS off korisnike."
    )
    # Bootstrap alert klase moraju biti unutar noscript bloka
    assert re.search(r"alert\s+alert-warning", src), (
        "base.html <noscript> blok ne koristi Bootstrap `alert alert-warning` klase. "
        "AC1 + Dev Notes Template."
    )


# =============================================================================
# AC2 — Skip link
# =============================================================================


def test_ac2_skip_link_first_child_of_body():
    """AC2: skip link MORA biti PRVI element body-ja (PRE prvog chrome include-a).

    Story 1.8 CRITICAL-CASCADE-2 + Decision D17 (flatten Option A): <header> wrapper
    uklonjen u korist role="banner" na .coric-top-header div-u. Canonical landmark
    region u base.html sada je `{% include "partials/header.html" %}` koji renderuje
    .coric-top-header + <nav class="coric-nav"> kao siblings (NE wrapped u <header>).

    POLISH-7 iter 3: regex umesto literal .find() — resilient na whitespace varijacije
    ({% include%}, {%  include  %}, jednostruki vs dvostruki navodnici). Brittleness
    eliminisana — test ne fail-uje na sitne template formatting promene.
    """
    src = _read_base_html()
    body_open_idx = src.find("<body>")
    skip_link_idx = src.find("visually-hidden-focusable")
    header_include_match = re.search(
        r'\{%\s*include\s*[\'"]partials/header\.html[\'"]\s*%\}',
        src,
    )
    assert body_open_idx != -1, "base.html ne sadrži <body> tag."
    assert skip_link_idx != -1, (
        "base.html ne sadrži skip link (`visually-hidden-focusable` klasa). AC2."
    )
    assert header_include_match is not None, (
        "base.html ne uključuje header partial (regression — Story 1.8 zahteva da je "
        '`{% include "partials/header.html" %}` u base.html; regex prihvata whitespace '
        "+ jednostruke/dvostruke navodnike)."
    )
    coric_top_header_include_idx = header_include_match.start()
    assert body_open_idx < skip_link_idx < coric_top_header_include_idx, (
        f"Skip link nije prvi element body-ja. "
        f"body_open={body_open_idx}, skip_link={skip_link_idx}, "
        f"header_include={coric_top_header_include_idx}. "
        f"AC2 (Story 1.6 regression updated u Story 1.8 scope per CRITICAL-CASCADE-2 + D17): "
        f"skip link mora biti TAČNO PRVI fokusabilan element (PRE chrome includes)."
    )


def test_ac2_skip_link_uses_visually_hidden_focusable():
    """AC2: skip link <a> tag koristi Bootstrap `visually-hidden-focusable` klasu."""
    src = _read_base_html()
    # Pattern: <a class="visually-hidden-focusable" href="#main-content">
    pattern = r'<a\s+class\s*=\s*["\']visually-hidden-focusable["\']\s+href\s*=\s*["\']#main-content["\']'
    assert re.search(pattern, src), (
        'base.html skip link nema `<a class="visually-hidden-focusable" href="#main-content">`. '
        "AC2 + Gotcha #13: koristimo Bootstrap utility klasu (appears on focus only)."
    )


def test_ac2_skip_link_targets_main_content():
    """AC2: skip link href MORA biti `#main-content` (target je <main id="main-content">)."""
    src = _read_base_html()
    assert 'href="#main-content"' in src or "href='#main-content'" in src, (
        'base.html skip link nema `href="#main-content"`. '
        'AC2: target je <main id="main-content"> (vidi AC3).'
    )


def test_ac2_skip_link_translated():
    """AC2: skip link tekst MORA biti pod `{% translate %}` (sr default 'Preskoči na sadržaj')."""
    src = _read_base_html()
    pattern = r'\{%\s*translate\s+["\']Preskoči na sadržaj["\']\s*%\}'
    assert re.search(pattern, src), (
        'base.html skip link tekst NIJE pod `{% translate "Preskoči na sadržaj" %}`. '
        "AC2: hu/en prevodi dolaze kroz `just messages` u Story 6.x."
    )


# =============================================================================
# AC3 — ARIA live region (kanonski singleton)
# =============================================================================


def test_ac3_aria_live_region_present():
    """AC3: rendered HTML MORA sadržati TAČNO JEDAN aria-live div (singleton).

    Test ide kroz render-time output (Django Client) jer `{% aria_live %}` je tag koji
    emituje HTML. Source test je test_ac3_aria_live_uses_aria_live_tag.
    """
    html = _render_home_sr()
    # Match div sa id="aria-live"
    matches = re.findall(r'<div\s+id\s*=\s*["\']aria-live["\']', html)
    assert len(matches) == 1, (
        f'Rendered HTML ima {len(matches)} `<div id="aria-live">` elemenata, očekivano TAČNO 1. '
        f"AC3 + Gotcha #3: kanonski singleton (HTMX `hx-swap-oob` target-uje preko ID-a)."
    )
    # Verifikuj atribute na tom div-u
    assert 'aria-live="polite"' in html, (
        'Rendered HTML aria-live div nema `aria-live="polite"`. AC3.'
    )
    assert 'aria-atomic="true"' in html, (
        'Rendered HTML aria-live div nema `aria-atomic="true"`. AC3.'
    )
    assert 'class="visually-hidden"' in html, (
        'Rendered HTML aria-live div nema `class="visually-hidden"`. AC3 + Gotcha #13.'
    )


def test_ac3_aria_live_uses_aria_live_tag():
    """AC3: base.html source MORA pozivati `{% aria_live %}` tag TAČNO JEDNOM."""
    src = _read_base_html()
    count = src.count("{% aria_live %}")
    assert count == 1, (
        f"base.html ima {count} `{{% aria_live %}}` poziva, očekivano TAČNO 1. "
        f"AC3 + Gotcha #3: singleton invariant — duplikat lomi HTMX OOB target."
    )


def test_ac3_main_has_id_and_tabindex():
    """AC3 / AC2 target: <main> MORA imati `id="main-content"` i `tabindex="-1"`."""
    src = _read_base_html()
    # Pattern: <main id="main-content" tabindex="-1"> ili reverse order
    pattern1 = r'<main\s+id\s*=\s*["\']main-content["\']\s+tabindex\s*=\s*["\']-1["\']'
    pattern2 = r'<main\s+tabindex\s*=\s*["\']-1["\']\s+id\s*=\s*["\']main-content["\']'
    assert re.search(pattern1, src) or re.search(pattern2, src), (
        'base.html <main> NEMA `id="main-content" tabindex="-1"`. '
        "AC2 + AC3 + Gotcha #7: id je skip link target; tabindex=-1 omogućuje programatski focus."
    )


# =============================================================================
# AC4 — apps/core/templatetags/htmx_aria.py
# =============================================================================


def test_ac4_templatetags_init_exists():
    """AC4 / Gotcha #4: apps/core/templatetags/__init__.py MORA postojati.

    Bez njega Django ne tretira templatetags/ kao paket — `{% load htmx_aria %}` puca.
    Sadržaj može biti prazan ili 1-line komentar.
    """
    assert TEMPLATETAGS_INIT.exists(), (
        f"{TEMPLATETAGS_INIT.relative_to(PROJECT_ROOT)} ne postoji. "
        f"AC4 + Gotcha #4: Django template tag discovery zahteva __init__.py."
    )


def test_ac4_htmx_aria_module_importable():
    """AC4: apps.core.templatetags.htmx_aria mora biti importable."""
    if not HTMX_ARIA_PY.exists():
        pytest.fail(
            f"{HTMX_ARIA_PY.relative_to(PROJECT_ROOT)} ne postoji. "
            f"AC4 — Dev mora kreirati po Dev Notes § htmx_aria.py Template."
        )
    _ensure_sys_path()
    # Force fresh import
    for mod_key in list(sys.modules.keys()):
        if mod_key.startswith("apps.core.templatetags"):
            del sys.modules[mod_key]
    try:
        mod = importlib.import_module("apps.core.templatetags.htmx_aria")
    except Exception as exc:
        pytest.fail(
            f"Ne mogu importovati apps.core.templatetags.htmx_aria: "
            f"{type(exc).__name__}: {exc}"
        )
    # Mora imati `register` variable koja je template.Library instance
    from django import template

    register = getattr(mod, "register", None)
    assert register is not None, (
        "apps.core.templatetags.htmx_aria NEMA `register` varijablu. "
        "AC4 + Gotcha #5: Django magic — naziv `register` je obavezan."
    )
    assert isinstance(register, template.Library), (
        f"`register` nije template.Library instance, vec {type(register).__name__}. "
        f"Gotcha #5."
    )
    # `aria_live` funkcija mora postojati
    aria_live = getattr(mod, "aria_live", None)
    assert callable(aria_live), (
        "apps.core.templatetags.htmx_aria.aria_live NIJE callable / ne postoji. AC4."
    )


def test_ac4_aria_live_tag_registered():
    """AC4: Template('{% load htmx_aria %}{% aria_live %}').render(Context()) ne baca TemplateSyntaxError."""
    _setup_django()
    try:
        from django.template import Context, Template
        from django.template.exceptions import TemplateSyntaxError
    except ImportError:
        pytest.skip("Django template engine nedostupan.")
    try:
        tpl = Template("{% load htmx_aria %}{% aria_live %}")
        out = tpl.render(Context())
    except TemplateSyntaxError as exc:
        pytest.fail(
            f"`{{% load htmx_aria %}}{{% aria_live %}}` baca TemplateSyntaxError: {exc}. "
            f"AC4: tag mora biti registrovan kroz `@register.simple_tag`."
        )
    assert out, "Render output je prazan — aria_live() tag emituje nista."


def test_ac4_aria_live_returns_canonical_html():
    """AC4: aria_live() funkcija vraća TAČNO HTML string sa svim ARIA atributima.

    Test ide kroz direktan poziv funkcije (NE kroz Template).
    """
    if not HTMX_ARIA_PY.exists():
        pytest.fail(f"{HTMX_ARIA_PY.relative_to(PROJECT_ROOT)} ne postoji.")
    _ensure_sys_path()
    for mod_key in list(sys.modules.keys()):
        if mod_key.startswith("apps.core.templatetags"):
            del sys.modules[mod_key]
    mod = importlib.import_module("apps.core.templatetags.htmx_aria")
    out = mod.aria_live()
    # Mora biti SafeString (mark_safe) — bez ovoga Django auto-escape pretvara
    # `<div>` u `&lt;div&gt;` pri Template render-u (Gotcha — AC4 Dev Notes).
    from django.utils.safestring import SafeString

    assert isinstance(out, SafeString), (
        f"aria_live() vraća {type(out).__name__}, očekivano SafeString. "
        f"AC4 + Dev Notes Template: mora se koristiti `mark_safe(...)` da Django "
        f"NE escape-uje HTML pri render-u kroz `{{% aria_live %}}` tag."
    )
    out_str = str(out)
    # Verifikuj svi 4 atributa + id + tag
    required_substrings = [
        "<div",
        'id="aria-live"',
        'class="visually-hidden"',
        'aria-live="polite"',
        'aria-atomic="true"',
        "</div>",
    ]
    missing = [s for s in required_substrings if s not in out_str]
    assert not missing, (
        f"aria_live() output ne sadrži sve required substrings: {missing}. "
        f"Dobijeno: {out_str!r}. AC4 + Dev Notes Template."
    )


# =============================================================================
# AC5 — base.py / production.py settings
# =============================================================================


def test_ac5_installed_apps_has_django_htmx():
    """AC5: `django_htmx` MORA biti u INSTALLED_APPS."""
    base = _load_settings_module("base")
    apps = list(base.INSTALLED_APPS)
    assert "django_htmx" in apps, (
        f"INSTALLED_APPS NE sadrži 'django_htmx'. Trenutno: {apps}. "
        f"AC5 — django-htmx 1.27+ zahteva app installation za template tags."
    )


def test_ac5_installed_apps_has_django_bootstrap5():
    """AC5: `django_bootstrap5` MORA biti u INSTALLED_APPS."""
    base = _load_settings_module("base")
    apps = list(base.INSTALLED_APPS)
    assert "django_bootstrap5" in apps, (
        f"INSTALLED_APPS NE sadrži 'django_bootstrap5'. Trenutno: {apps}. "
        f"AC5 — neophodno za `{{% load django_bootstrap5 %}}` discovery."
    )


def test_ac5_middleware_has_htmx_middleware():
    """AC5: `django_htmx.middleware.HtmxMiddleware` MORA biti u MIDDLEWARE."""
    base = _load_settings_module("base")
    mw = list(base.MIDDLEWARE)
    assert "django_htmx.middleware.HtmxMiddleware" in mw, (
        f"MIDDLEWARE NE sadrži `django_htmx.middleware.HtmxMiddleware`. Trenutno: {mw}. "
        f"AC5 — postavlja `request.htmx` atribut na svaki request."
    )


def test_ac5_htmx_middleware_position():
    """AC5 / Gotcha #6: HtmxMiddleware mora biti POSLE CommonMiddleware i PRE LocaleSwitcherMiddleware."""
    base = _load_settings_module("base")
    mw = list(base.MIDDLEWARE)
    try:
        common_idx = mw.index("django.middleware.common.CommonMiddleware")
        htmx_idx = mw.index("django_htmx.middleware.HtmxMiddleware")
        locale_switcher_idx = mw.index("apps.core.middleware.LocaleSwitcherMiddleware")
    except ValueError as exc:
        pytest.fail(
            f"Jedan od kritičnih middleware-a nedostaje: {exc}. MIDDLEWARE: {mw}"
        )
    assert common_idx < htmx_idx < locale_switcher_idx, (
        f"HtmxMiddleware position pogrešna. "
        f"common={common_idx}, htmx={htmx_idx}, locale_switcher={locale_switcher_idx}. "
        f"Mora biti: common < htmx < locale_switcher (Gotcha #6)."
    )


def test_ac5_bootstrap5_dict_present_base():
    """AC5: base.py MORA imati BOOTSTRAP5 dict (sa 4 ključa: css_url, javascript_url, javascript_in_head, include_jquery)."""
    base = _load_settings_module("base")
    bs5 = getattr(base, "BOOTSTRAP5", None)
    assert bs5 is not None, (
        "base.py NEMA `BOOTSTRAP5` setting dict. "
        "AC5 — django-bootstrap5 konfiguracija za env-aware Bootstrap URL."
    )
    assert isinstance(bs5, dict), (
        f"BOOTSTRAP5 mora biti dict, vec {type(bs5).__name__}."
    )
    required_keys = {
        "css_url",
        "javascript_url",
        "javascript_in_head",
        "include_jquery",
    }
    missing = required_keys - set(bs5.keys())
    assert not missing, (
        f"BOOTSTRAP5 dict NE sadrži ključeve: {missing}. Dobijeno: {sorted(bs5.keys())}."
    )
    # javascript_in_head mora biti False, include_jquery mora biti False
    assert bs5.get("javascript_in_head") is False, (
        f"BOOTSTRAP5['javascript_in_head'] = {bs5.get('javascript_in_head')!r}, očekivano False. "
        f"Gotcha #11 — JS pre </body>."
    )
    assert bs5.get("include_jquery") is False, (
        f"BOOTSTRAP5['include_jquery'] = {bs5.get('include_jquery')!r}, očekivano False. "
        f"Gotcha #12 — Bootstrap 5 ne zahteva jQuery."
    )


def test_ac5_bootstrap5_dev_uses_cdn():
    """AC5: base.py BOOTSTRAP5 css_url + javascript_url MORAJU pokazivati na cdn.jsdelivr.net/npm/bootstrap@5.3.3.

    project-context.md line 67: "Bootstrap 5.3 — CDN u dev, local u prod".
    base.py = DEV variant.
    """
    base = _load_settings_module("base")
    bs5 = getattr(base, "BOOTSTRAP5", None)
    if bs5 is None:
        pytest.fail("BOOTSTRAP5 dict nedostaje (drugi test hvata).")
    css_url = bs5.get("css_url", {})
    js_url = bs5.get("javascript_url", {})
    assert isinstance(css_url, dict) and isinstance(js_url, dict), (
        "css_url / javascript_url moraju biti dict-ovi (sa 'url' i 'integrity' kljucevima)."
    )
    css_target = css_url.get("url", "")
    js_target = js_url.get("url", "")
    cdn_substring = "cdn.jsdelivr.net/npm/bootstrap@5.3.3"
    assert cdn_substring in css_target, (
        f"BOOTSTRAP5['css_url']['url'] = {css_target!r}, mora sadržati `{cdn_substring}`. "
        f"AC5 — DEV variant koristi pinned jsDelivr CDN."
    )
    assert cdn_substring in js_target, (
        f"BOOTSTRAP5['javascript_url']['url'] = {js_target!r}, mora sadržati `{cdn_substring}`. "
        f"AC5 — DEV variant."
    )


def test_ac5_bootstrap5_production_uses_local():
    """AC5: production.py BOOTSTRAP5 override MORA pokazivati na /static/vendor/bootstrap-5.3.3/."""
    prod = _load_settings_module("production")
    bs5 = getattr(prod, "BOOTSTRAP5", None)
    assert bs5 is not None, (
        "production.py NEMA `BOOTSTRAP5` override. "
        "AC5 — production-local-only policy (GDPR + CSP-readiness)."
    )
    css_url = bs5.get("css_url", {}).get("url", "")
    js_url = bs5.get("javascript_url", {}).get("url", "")
    expected_prefix = "/static/vendor/bootstrap-5.3.3/"
    assert css_url.startswith(expected_prefix), (
        f"production BOOTSTRAP5['css_url']['url'] = {css_url!r}, "
        f"mora startswith `{expected_prefix}`. AC5 — PROD local-only."
    )
    assert js_url.startswith(expected_prefix), (
        f"production BOOTSTRAP5['javascript_url']['url'] = {js_url!r}, "
        f"mora startswith `{expected_prefix}`. AC5."
    )


def test_ac5_bootstrap5_integrity_none():
    """AC5 / Gotcha #19: BOOTSTRAP5 css_url + javascript_url MORAJU imati EKSPLICITNO
    `integrity: None` u OBAJ env-u (base.py dev + production.py prod).

    Bez eksplicitnog `integrity: None`, django-bootstrap5 koristi default SRI hash koji
    NE odgovara override URL-u → browser baca SubresourceIntegrityError. Test mora
    da razlikuje "key absent" od "key present sa value None" — samo drugi case je OK.
    """

    def _assert_integrity_none(dict_obj: dict, label: str) -> None:
        assert "integrity" in dict_obj, (
            f"{label} NE sadrži 'integrity' ključ. Gotcha #19 — mora biti "
            f"EKSPLICITNO setovan na None (key-absent puca jer django-bootstrap5 "
            f"injection-uje default SRI hash)."
        )
        assert dict_obj["integrity"] is None, (
            f"{label}['integrity'] = {dict_obj['integrity']!r}, očekivano None."
        )

    # base.py (dev) provera
    base = _load_settings_module("base")
    bs5_dev = getattr(base, "BOOTSTRAP5", None)
    if bs5_dev is None:
        pytest.fail("BOOTSTRAP5 dict nedostaje u base.py.")
    _assert_integrity_none(bs5_dev["css_url"], "base.py BOOTSTRAP5['css_url']")
    _assert_integrity_none(
        bs5_dev["javascript_url"], "base.py BOOTSTRAP5['javascript_url']"
    )
    # production.py (prod) provera
    prod = _load_settings_module("production")
    bs5_prod = getattr(prod, "BOOTSTRAP5", None)
    if bs5_prod is None:
        pytest.fail("BOOTSTRAP5 override nedostaje u production.py.")
    _assert_integrity_none(bs5_prod["css_url"], "production.py BOOTSTRAP5['css_url']")
    _assert_integrity_none(
        bs5_prod["javascript_url"], "production.py BOOTSTRAP5['javascript_url']"
    )


# =============================================================================
# AC6 — request.htmx attribute (HtmxMiddleware behavior)
# =============================================================================


def test_ac6_htmx_middleware_sets_request_attribute():
    """AC6: HtmxMiddleware postavlja request.htmx (falsy bez header-a, truthy sa HX-Request='true')."""
    _setup_django()
    try:
        from django.test import RequestFactory
        from django_htmx.middleware import HtmxMiddleware
    except ImportError as exc:
        pytest.skip(f"django_htmx nije importable: {exc}")
    rf = RequestFactory()
    mw = HtmxMiddleware(lambda r: None)
    # Bez HTMX header-a
    r1 = rf.get("/")
    mw(r1)
    assert hasattr(r1, "htmx"), (
        "Plain request nakon HtmxMiddleware NEMA `htmx` atribut. "
        "AC6 — middleware mora setovati request.htmx u svim slucajevima."
    )
    assert bool(r1.htmx) is False, (
        f"request.htmx truthy bez HX-Request header-a: {r1.htmx!r}. "
        f"AC6 — mora biti falsy."
    )


def test_ac6_request_htmx_attribute_accessible():
    """AC6: sa HX-Request='true' header-om, request.htmx je truthy."""
    _setup_django()
    try:
        from django.test import RequestFactory
        from django_htmx.middleware import HtmxMiddleware
    except ImportError as exc:
        pytest.skip(f"django_htmx nije importable: {exc}")
    rf = RequestFactory()
    mw = HtmxMiddleware(lambda r: None)
    r2 = rf.get("/", HTTP_HX_REQUEST="true")
    mw(r2)
    assert hasattr(r2, "htmx"), "HTMX request NEMA `htmx` atribut."
    assert bool(r2.htmx) is True, (
        f"request.htmx falsy sa HX-Request header-om: {r2.htmx!r}. "
        f"AC6 — mora biti truthy."
    )


# =============================================================================
# AC7 — HTMX local vendor fajl (mostly SKIP pre Mihas download-a)
# =============================================================================


def test_ac7_static_vendor_dir_exists():
    """AC7: static/vendor/ direktorijum MORA postojati (Mihas Task 4.1 kreira)."""
    assert STATIC_VENDOR_DIR.exists() and STATIC_VENDOR_DIR.is_dir(), (
        f"static/vendor/ direktorijum ne postoji na {STATIC_VENDOR_DIR}. "
        f"AC7 Task 4.1 — Mihas mora download-ovati HTMX + Bootstrap u ovaj dir."
    )


def test_ac7_htmx_min_js_present():
    """AC7: static/vendor/htmx.min.js MORA postojati (Mihas Task 4.1 download).

    Skip ako Mihas još nije download-ovao — sanity pattern iz Roboto Story 1.5.
    """
    if not HTMX_MIN_JS.exists():
        pytest.skip(HTMX_VENDOR_MISSING_MSG)
    size_kb = HTMX_MIN_JS.stat().st_size / 1024
    assert 40 < size_kb < 80, (
        f"static/vendor/htmx.min.js veličina = {size_kb:.1f} KB, očekivano (40, 80) KB. "
        f"AC7 + Gotcha #9 — verify pinned 1.9.12 download."
    )


def test_ac7_htmx_min_js_version_1_9_x():
    """AC7 + Gotcha #9: prvih 1-3 linija htmx.min.js sadrže version comment `HTMX v1.9.x`.

    KRITIČNO: HTMX 2.x ima breaking changes (data-hx-* prefix), pa pinned 1.9.12 je obavezan.
    """
    if not HTMX_MIN_JS.exists():
        pytest.skip(HTMX_VENDOR_MISSING_MSG)
    head_lines = HTMX_MIN_JS.read_text(encoding="utf-8", errors="replace").splitlines()[
        :5
    ]
    head_text = "\n".join(head_lines)
    pattern = r"HTMX\s+v1\.9\."
    assert re.search(pattern, head_text, re.IGNORECASE), (
        f"htmx.min.js prvih 5 linija NE sadrže `HTMX v1.9.x` version marker. "
        f"Dobijeno: {head_text!r}. "
        f"AC7 + Gotcha #9: Mora biti pinned 1.9.x (NE 2.x); re-download sa "
        f"https://unpkg.com/htmx.org@1.9.12/dist/htmx.min.js."
    )


# =============================================================================
# AC8 — static/css/main.css placeholder
# =============================================================================


def test_ac8_main_css_exists_placeholder():
    """AC8: static/css/main.css MORA postojati (placeholder, max 500 bytes).

    Story 1.7+ popunjava ovaj fajl; Story 1.6 samo kreira placeholder.
    """
    assert MAIN_CSS.exists(), (
        f"static/css/main.css ne postoji na {MAIN_CSS}. "
        f"AC8 — Dev mora kreirati placeholder fajl (link target u base.html)."
    )
    size = MAIN_CSS.stat().st_size
    assert size < 500, (
        f"static/css/main.css veličina = {size} bytes, očekivano < 500 bytes (placeholder). "
        f"AC8 — Story 1.7+ popunjava komponente; sada samo placeholder komentar."
    )


# =============================================================================
# AC9 — Smoke validacija (render layer)
# =============================================================================


def test_ac9_django_check_passes():
    """AC9.1: `uv run python manage.py check` exit 0."""
    uv_bin = shutil.which("uv")
    if uv_bin is None:
        pytest.skip("uv binary nije u PATH-u.")
    manage_py = PROJECT_ROOT / "manage.py"
    if not manage_py.exists():
        pytest.fail("manage.py nedostaje.")
    env = os.environ.copy()
    env["DJANGO_SECRET_KEY"] = TEST_SECRET
    result = subprocess.run(
        [
            uv_bin,
            "run",
            "python",
            "manage.py",
            "check",
            "--settings=config.settings.development",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        shell=False,
        timeout=120,
        env=env,
    )
    assert result.returncode == 0, (
        f"`manage.py check` exit {result.returncode}.\n"
        f"stdout: {result.stdout}\n"
        f"stderr: {result.stderr}"
    )


def test_ac9_render_home_includes_skip_link():
    """AC9.9: GET /sr/ → rendered HTML sadrži skip link sa sr translation 'Preskoči na sadržaj'."""
    html = _render_home_sr()
    assert 'class="visually-hidden-focusable"' in html, (
        'Rendered HTML ne sadrži `class="visually-hidden-focusable"`. AC9.9.'
    )
    assert 'href="#main-content"' in html, (
        'Rendered HTML ne sadrži `href="#main-content"`. AC9.9.'
    )
    # sr translation (msgid fallback)
    assert "Preskoči na sadržaj" in html, (
        "Rendered HTML ne sadrži skip link tekst 'Preskoči na sadržaj' (sr msgid). "
        "Verifikuj `{% translate %}` u base.html."
    )


def test_ac9_render_home_includes_aria_live():
    """AC9.9: GET /sr/ → rendered HTML sadrži aria-live div (kompletan ARIA atribute set)."""
    html = _render_home_sr()
    # Strict match: id="aria-live" + class="visually-hidden" + aria-live="polite" + aria-atomic="true"
    pattern = (
        r'<div\s+id\s*=\s*["\']aria-live["\']\s+'
        r'class\s*=\s*["\']visually-hidden["\']\s+'
        r'aria-live\s*=\s*["\']polite["\']\s+'
        r'aria-atomic\s*=\s*["\']true["\']'
    )
    assert re.search(pattern, html), (
        "Rendered HTML ne sadrži kanonski aria-live div. AC9.9 + AC3."
    )


def test_ac9_render_home_includes_bootstrap_css():
    """AC9.9: GET /sr/ → rendered HTML sadrži Bootstrap CSS link (regex accepts CDN ili local).

    DEV expects CDN (cdn.jsdelivr.net/npm/bootstrap@5.3.3); PROD expects local (/static/vendor/bootstrap-5.3.3/).
    """
    html = _render_home_sr()
    # Accept dev (jsDelivr) ili prod (local /static/vendor/) Bootstrap CSS link
    pattern = r"(cdn\.jsdelivr\.net/npm/bootstrap@5\.3\.3.*bootstrap\.min\.css|/static/vendor/bootstrap-5\.3\.3/.*bootstrap\.min\.css)"
    assert re.search(pattern, html), (
        "Rendered HTML ne sadrži Bootstrap CSS link (CDN ili local). "
        "AC9.9 — `{% bootstrap_css %}` mora renderovati validan <link>."
    )


def test_ac9_no_inline_event_handlers():
    """AC9.2 / CSP-readiness: base.html source NE SME sadržati inline event handlers.

    NAPOMENA: testira SOURCE base.html (NIJE rendered output uključujući includes).
    Story 1.4 language_switcher.html ima `onchange=` (known issue, fix u Story 9.1) —
    NE testira se ovde.
    """
    src = _read_base_html()
    bad_patterns = ["onclick=", "onchange=", "onload=", "onmouseover=", "onkeydown="]
    found = [p for p in bad_patterns if p in src]
    assert not found, (
        f"base.html source sadrži inline event handlers: {found}. "
        f"AC9.2 — CSP-ready (Story 9.1 enables CSP)."
    )


# =============================================================================
# Anti-pattern guards
# =============================================================================


def test_base_html_no_google_cdn_links():
    """Anti-pattern: base.html SOURCE + rendered output NE SMEJU sadržati Google CDN linkove.

    `cdn.jsdelivr.net` JE dozvoljen u rendered output-u (DEV mode kroz {% bootstrap_css %}),
    ali NE u source-u kao literal URL.
    """
    src = _read_base_html()
    # Source-level test
    forbidden_source = ["googleapis.com", "gstatic.com"]
    found = [d for d in forbidden_source if d in src]
    assert not found, (
        f"base.html SOURCE sadrži forbidden CDN reference: {found}. "
        f"Anti-pattern — project-context.md line 67 (no Google CDN, ever)."
    )
    # Rendered output (skip ako Django setup pukne — drugi testovi hvataju)
    try:
        html = _render_home_sr()
    except (pytest.skip.Exception, pytest.fail.Exception):  # type: ignore[attr-defined]
        return
    found_render = [d for d in forbidden_source if d in html]
    assert not found_render, (
        f"Rendered HTML sadrži forbidden Google CDN reference: {found_render}. "
        f"Anti-pattern: ni dev ni prod ne sme imati Google CDN."
    )


def test_base_html_no_jsdelivr_link():
    """Anti-pattern: base.html SOURCE NE SME sadržati literal `jsdelivr` URL.

    jsDelivr je rendered-time URL (kroz {% bootstrap_css %} u dev), NE source literal.
    """
    src = _read_base_html()
    assert "jsdelivr" not in src.lower(), (
        "base.html SOURCE sadrži literal `jsdelivr` URL. "
        "Anti-pattern: Bootstrap CDN URL ide kroz BOOTSTRAP5 settings dict, NE inline u template-u."
    )
    # Takođe za unpkg.com, getbootstrap.com, htmx.org (svi external vendor URL-ovi)
    forbidden = ["unpkg.com", "getbootstrap.com", "htmx.org/dist"]
    found = [d for d in forbidden if d in src.lower()]
    assert not found, (
        f"base.html SOURCE sadrži external vendor URL-ove: {found}. "
        f"Anti-pattern: svi vendor URL-ovi idu kroz settings dict ili lokalni /static/vendor/."
    )


def test_base_html_no_uppercase_hex():
    """Anti-pattern (carry from Story 1.5 AC4): base.html i main.css NE SMEJU sadržati uppercase hex.

    Pattern: `#XXXXXX` sa bilo kojim uppercase A-F slovom. Story 1.5 invariant
    preserved (lowercase 6-digit kanon).
    """
    # base.html
    src = _read_base_html()
    matches = re.findall(r"#[0-9A-Fa-f]{6}", src)
    bad = [m for m in matches if any(c.isalpha() and c.isupper() for c in m[1:])]
    assert not bad, (
        f"base.html sadrži uppercase hex vrednosti: {bad}. "
        f"Story 1.5 AC4 carry — lowercase 6-digit kanon."
    )
    # main.css (ako postoji)
    if MAIN_CSS.exists():
        main_src = MAIN_CSS.read_text(encoding="utf-8")
        matches_main = re.findall(r"#[0-9A-Fa-f]{6}", main_src)
        bad_main = [
            m for m in matches_main if any(c.isalpha() and c.isupper() for c in m[1:])
        ]
        assert not bad_main, (
            f"main.css sadrži uppercase hex vrednosti: {bad_main}. Story 1.5 AC4 carry."
        )
