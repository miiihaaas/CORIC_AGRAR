"""Tests za Story 2.5 — GLightbox Integracija (static asset + base.html wiring).

Pokriva:
- AC1: static/vendor/glightbox/{glightbox.min.css, glightbox.min.js} postoje + minified heuristika
- AC2: static/js/lightbox-init.js postoji + IIFE + 'use strict' + GLightbox options +
       coric: namespace events + locale lookup + idempotent re-init + htmx:afterSwap listener
- AC3: static/css/components/lightbox.css postoji + backdrop rgba(15,15,15,0.85) +
       @media (prefers-reduced-motion: reduce)
- AC4: static/css/main.css sadrzi @import url('./components/lightbox.css');
- AC5: templates/base.html sadrzi glightbox.min.css link u HEAD (POSLE tokens, PRE bootstrap) +
       glightbox.min.js + lightbox-init.js script tags POSLE sticky-nav.js (sa defer);
       Django komentar na liniji 38 preserved (regression guard za Story 1.6 deliverable);
       vendor-before-init order guard
- AC7: Anti-CDN guard — no cdnjs.cloudflare.com / unpkg.com / jsdelivr.net reference u
       templates/, static/css/, static/js/ source-u

Pokrenuti sa: uv run pytest tests/test_lightbox_integration.py -v --tb=short

TEA RED faza: 16 od 21 testova MORAJU pasti dok Dev ne zavrsi Story 2.5.
3 AC1 testa (file-existence + size + global) mogu PASS-ovati ako Mihas vec preuzeo
vendor fajlove (per Story 2.5 AC1 Napomena). 1 AC5 regression guard test (Django komentar
linija 38) PASS-uje pre i posle Dev Edit-a. 1 AC7 anti-CDN guard PASS-uje prazno dok Dev
ne kreira fajlove (skipped non-existent paths).

Naming convention: srpska latinica + engleski; bez cirilice.

AC6 (manuelni browser smoke check kroz DevTools Console injection) je EKSPLICITNO
out-of-scope automatizovanih testova — Story 9.8 Playwright pokriva E2E keyboard nav.
"""

from __future__ import annotations

from pathlib import Path


# =============================================================================
# Konstante (project paths)
# =============================================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

STATIC_DIR = PROJECT_ROOT / "static"
VENDOR_GLIGHTBOX_DIR = STATIC_DIR / "vendor" / "glightbox"
GLIGHTBOX_CSS = VENDOR_GLIGHTBOX_DIR / "glightbox.min.css"
GLIGHTBOX_JS = VENDOR_GLIGHTBOX_DIR / "glightbox.min.js"

LIGHTBOX_INIT_JS = STATIC_DIR / "js" / "lightbox-init.js"
LIGHTBOX_CSS = STATIC_DIR / "css" / "components" / "lightbox.css"
MAIN_CSS = STATIC_DIR / "css" / "main.css"

BASE_HTML = PROJECT_ROOT / "templates" / "base.html"


# =============================================================================
# AC1 — Vendor files (3 testa)
# =============================================================================


# AC-1: static/vendor/glightbox/ direktorijum postoji (Mihas pre-download)
def test_ac1_glightbox_vendor_directory_exists():
    """AC1: static/vendor/glightbox/ direktorijum mora postojati."""
    assert VENDOR_GLIGHTBOX_DIR.exists() and VENDOR_GLIGHTBOX_DIR.is_dir(), (
        f"Direktorijum ne postoji na {VENDOR_GLIGHTBOX_DIR}. "
        "Story 2.5 AC1 — Mihas mora preuzeti GLightbox 3.x sa "
        "https://github.com/biati-digital/glightbox/releases i smestiti u static/vendor/glightbox/."
    )


# AC-1: glightbox.min.css postoji + minified heuristika (st_size <= 50_000 bytes)
def test_ac1_glightbox_css_file_exists_and_size_under_50kb():
    """AC1: glightbox.min.css mora postojati + biti minified (file size <= 50 KB).

    Minified GLightbox CSS je ~6 KB; pretty-printed ~80 KB. Threshold 50 KB
    pouzdano hvata un-minified varijantu.
    """
    assert GLIGHTBOX_CSS.exists(), (
        f"glightbox.min.css ne postoji na {GLIGHTBOX_CSS}. Story 2.5 AC1."
    )
    size = GLIGHTBOX_CSS.stat().st_size
    assert size <= 50_000, (
        f"glightbox.min.css ima {size} bajtova (> 50_000). "
        "Verovatno je preuzeta pretty-printed verzija. "
        "Mihas mora preuzeti dist/glightbox.min.css (TACNO `.min` build)."
    )


# AC-1: glightbox.min.js postoji + exportuje GLightbox global
def test_ac1_glightbox_js_file_exists_and_exposes_global():
    """AC1: glightbox.min.js mora postojati + source mora sadrzati `GLightbox` token
    (sanity check — vendor module exposes window.GLightbox constructor).
    """
    assert GLIGHTBOX_JS.exists(), (
        f"glightbox.min.js ne postoji na {GLIGHTBOX_JS}. Story 2.5 AC1."
    )
    source = GLIGHTBOX_JS.read_text(encoding="utf-8", errors="replace")
    assert "GLightbox" in source, (
        "glightbox.min.js source NE sadrzi `GLightbox` token. "
        "Verovatno je preuzeta pogresna biblioteka ili je fajl korumpiran. "
        "Story 2.5 AC1 — vendor module mora exportovati window.GLightbox constructor."
    )


# =============================================================================
# AC2 — lightbox-init.js modul (9 testova — 7 funkcionalnih + 2 anti-pattern guards)
# =============================================================================


# AC-2: static/js/lightbox-init.js postoji
def test_ac2_lightbox_init_js_exists():
    """AC2: static/js/lightbox-init.js mora postojati (Dev deliverable)."""
    assert LIGHTBOX_INIT_JS.exists(), (
        f"lightbox-init.js ne postoji na {LIGHTBOX_INIT_JS}. "
        "Story 2.5 AC2 + Task 2 — Dev mora kreirati vanilla JS init modul."
    )


# AC-2: IIFE wrap + 'use strict' direktiva
def test_ac2_lightbox_init_uses_iife_with_use_strict():
    """AC2: lightbox-init.js mora biti IIFE wrap-ovan + sadrzati 'use strict' direktivu.

    Pattern: source sadrzi `(function ()` + `'use strict'` (Story 1.8 sticky-nav.js mirror).
    """
    assert LIGHTBOX_INIT_JS.exists(), (
        f"lightbox-init.js ne postoji na {LIGHTBOX_INIT_JS} (drugi test hvata)."
    )
    source = LIGHTBOX_INIT_JS.read_text(encoding="utf-8")
    assert "(function ()" in source, (
        "lightbox-init.js NE sadrzi `(function ()` IIFE wrap. "
        "AC2 — mirror Story 1.8 sticky-nav.js IIFE pattern."
    )
    assert "'use strict'" in source, (
        "lightbox-init.js NE sadrzi `'use strict'` direktivu. "
        "AC2 + Story 1.8 sticky-nav.js linija 10 pattern."
    )


# AC-2: buildOptions ukljucuje sve potrebne GLightbox opcije iz Story Dev Notes sample
def test_ac2_buildoptions_includes_required_keys():
    """AC2: lightbox-init.js mora sadrzati TACNE kljuc-imena GLightbox opcija iz
    Story 2.5 AC2 Dev Notes sample (linija 131-142).

    Required keys: touchNavigation, loop, openEffect, closeEffect, slideEffect, moreText.
    (keyboardNavigation NIJE u Story sample-u — vendor GLightbox 3.x ima keyboard nav
    enabled by default, ne treba eksplicitan opt-in.)
    """
    assert LIGHTBOX_INIT_JS.exists(), "lightbox-init.js ne postoji (drugi test hvata)."
    source = LIGHTBOX_INIT_JS.read_text(encoding="utf-8")
    required_keys = [
        "touchNavigation",
        "openEffect",
        "closeEffect",
        "slideEffect",
        "loop",
        "moreText",
    ]
    missing = [k for k in required_keys if k not in source]
    assert not missing, (
        f"lightbox-init.js NE sadrzi GLightbox option key(s): {missing}. "
        "AC2 buildOptions mora ukljuciti sve required keys per Dev Notes sample."
    )


# AC-2: coric: namespace custom events dispatch
def test_ac2_dispatches_coric_namespace_events():
    """AC2: lightbox-init.js mora dispatch-ovati `coric:lightbox-open` + `coric:lightbox-close`
    custom events na `window` (per project-context.md JavaScript style — `coric:` namespace).
    """
    assert LIGHTBOX_INIT_JS.exists(), "lightbox-init.js ne postoji (drugi test hvata)."
    source = LIGHTBOX_INIT_JS.read_text(encoding="utf-8")
    assert "coric:lightbox-open" in source, (
        "lightbox-init.js NE sadrzi string `coric:lightbox-open`. "
        "AC2 — custom event za konzumente (Story 2.6 slider auto-advance pause)."
    )
    assert "coric:lightbox-close" in source, (
        "lightbox-init.js NE sadrzi string `coric:lightbox-close`. AC2."
    )
    assert "dispatchEvent" in source, (
        "lightbox-init.js NE poziva `dispatchEvent` (custom event emission). AC2."
    )
    # window-attached dispatch (a ne document) — per AC2 + architecture.md naming
    assert "window.dispatchEvent" in source, (
        "lightbox-init.js NE koristi `window.dispatchEvent` za custom event emission. "
        "AC2 — event mora biti na `window` (architecture.md naming conventions)."
    )


# AC-2: locale lookup za moreText (MORE_TEXT mapa sr/hu/en + getLocale)
def test_ac2_uses_locale_lookup_for_moretext():
    """AC2: lightbox-init.js mora imati `getLocale` funkciju + `MORE_TEXT` lookup table
    sa kljucevima `sr`, `hu`, `en` (fallback na sr).
    """
    assert LIGHTBOX_INIT_JS.exists(), "lightbox-init.js ne postoji (drugi test hvata)."
    source = LIGHTBOX_INIT_JS.read_text(encoding="utf-8")
    assert "getLocale" in source, (
        "lightbox-init.js NE sadrzi `getLocale` funkciju. "
        "AC2 — moreText mora biti locale-aware kroz document.documentElement.lang."
    )
    assert "MORE_TEXT" in source, (
        "lightbox-init.js NE sadrzi `MORE_TEXT` lookup table. AC2."
    )
    # Sve tri locale kljuce — sr (primarni), hu, en
    for locale_key in ("sr", "hu", "en"):
        # Pattern: kljuc moze biti `sr:`, `'sr':`, `"sr":` — provera substring koji
        # razlikuje od slucajnog susreta u JS source-u (npr. komentar)
        # MORE_TEXT objekat ima format `sr: 'Vise'` — trazimo `sr:` ili 'sr':
        assert (
            f"{locale_key}:" in source
            or f"'{locale_key}':" in source
            or f'"{locale_key}":' in source
        ), (
            f"lightbox-init.js NE sadrzi MORE_TEXT kljuc za locale `{locale_key}`. "
            "AC2 — sr (default), hu, en moraju svi biti mapirani."
        )


# AC-2: idempotent re-init (destroy pre nove init) + defensive typeof guard
def test_ac2_idempotent_reinit_destroys_before_init():
    """AC2: lightbox-init.js mora biti idempotent — pre re-init poziva,
    prethodni `window._coricLightbox` instance se destroy-uje.

    Mora sadrzati: `_coricLightbox` + `destroy()` poziv + `typeof window._coricLightbox`
    defensive check (sprecava memory leak + duplikate listenere).
    """
    assert LIGHTBOX_INIT_JS.exists(), "lightbox-init.js ne postoji (drugi test hvata)."
    source = LIGHTBOX_INIT_JS.read_text(encoding="utf-8")
    assert "_coricLightbox" in source, (
        "lightbox-init.js NE koristi `window._coricLightbox` instance handle. "
        "AC2 — idempotency zahteva da se prethodni instance referencira pre destroy."
    )
    assert "destroy" in source, (
        "lightbox-init.js NE poziva `destroy()` metod. "
        "AC2 — pre re-init prethodni instance mora biti unisten."
    )
    # Defensive typeof guard — moze biti `typeof window._coricLightbox` ili
    # `typeof window.GLightbox`. Story Dev Notes pokazuje oba primera.
    assert "typeof" in source, (
        "lightbox-init.js NE sadrzi `typeof` defensive check. "
        "AC2 — vendor script 404 NE sme bacati exception."
    )


# AC-2: htmx:afterSwap listener + opened guard
def test_ac2_htmx_afterswap_listener_with_opened_guard():
    """AC2: lightbox-init.js mora imati `htmx:afterSwap` listener na document.body
    + `instance.opened` guard (HTMX OOB updates dok je modal otvoren NE smeju yank-ovati fokus).
    """
    assert LIGHTBOX_INIT_JS.exists(), "lightbox-init.js ne postoji (drugi test hvata)."
    source = LIGHTBOX_INIT_JS.read_text(encoding="utf-8")
    assert "htmx:afterSwap" in source, (
        "lightbox-init.js NE sadrzi `htmx:afterSwap` listener. "
        "AC2 — HTMX swap (Story 2.8 tractor filter) mora re-init Lightbox za nove .glightbox elemente."
    )
    assert ".opened" in source, (
        "lightbox-init.js NE proverava `.opened` guard. "
        "AC2 — skip re-init ako je Lightbox trenutno otvoren (sprecava fokus yank)."
    )


# AC-2: prefers-reduced-motion respect u JS source-u (matchMedia query string)
def test_ac2_lightbox_init_respects_prefers_reduced_motion():
    """AC2: lightbox-init.js mora referencirati `prefers-reduced-motion` kroz matchMedia
    query (per project-context.md § A11y must-haves linija 689 + UX-DR-13).

    Story AC7 enumeration linija 334 explicitno mandira ovaj test.
    """
    assert LIGHTBOX_INIT_JS.exists(), "lightbox-init.js ne postoji (drugi test hvata)."
    source = LIGHTBOX_INIT_JS.read_text(encoding="utf-8")
    assert "prefers-reduced-motion" in source, (
        "lightbox-init.js NE sadrzi `prefers-reduced-motion` string. "
        "AC2 — mora koristiti matchMedia('(prefers-reduced-motion: reduce)') za a11y respect."
    )


# AC-2: Anti-pattern guard — no jQuery, no ES module imports
def test_ac2_lightbox_init_no_jquery_no_module_imports():
    """AC2: lightbox-init.js NE SME sadrzati jQuery reference (`jQuery`, `$(`) ili
    ES module direktive (`import `, `export `).

    Per project-context.md § JavaScript style linija 338: "Vanilla JS preferred ... NIKAD jQuery".
    Per Story AC2 linija 204: "NEMA jQuery ... NEMA import/export statements".
    Story AC7 enumeration linija 337 explicitno mandira ovaj anti-pattern guard test.
    """
    assert LIGHTBOX_INIT_JS.exists(), "lightbox-init.js ne postoji (drugi test hvata)."
    source = LIGHTBOX_INIT_JS.read_text(encoding="utf-8")
    forbidden = {
        "jQuery": "jQuery",
        "jQuery shorthand `$(`": "$(",
        "ES module `import ` statement": "import ",
        "ES module `export ` statement": "export ",
    }
    offending = [name for name, token in forbidden.items() if token in source]
    assert not offending, (
        f"lightbox-init.js sadrzi zabranjen token(e): {offending}. "
        "AC2 — vanilla JS, no jQuery, no ES module bundler u v1 (no build pipeline)."
    )


# =============================================================================
# AC3 — lightbox.css override (2 testa)
# =============================================================================


# AC-3: backdrop rgba boja na .glightbox-clean .goverlay selektoru
def test_ac3_backdrop_color_rgba_specified():
    """AC3: static/css/components/lightbox.css mora postojati + sadrzati
    `.glightbox-clean .goverlay` selektor + boju `rgba(15, 15, 15, 0.85)`
    (per DESIGN.md § Modal/Lightbox linija 287).

    Selektor JE TACAN: `.glightbox-clean` (default skin) + `.goverlay` (backdrop wrapper) —
    NIKAD `.gcontainer` (modal content wrapper), NIKAD `.glightbox-modern` (non-default skin).
    """
    assert LIGHTBOX_CSS.exists(), (
        f"lightbox.css ne postoji na {LIGHTBOX_CSS}. "
        "Story 2.5 AC3 + Task 3 — Dev mora kreirati custom theme override."
    )
    css = LIGHTBOX_CSS.read_text(encoding="utf-8")
    assert ".glightbox-clean .goverlay" in css, (
        "lightbox.css NE sadrzi `.glightbox-clean .goverlay` selektor. "
        "AC3 — backdrop override target. NIKAD `.gcontainer` (modal content)."
    )
    # rgba moze biti sa razlicitim whitespace-om — proveri obe varijante
    has_rgba = (
        "rgba(15, 15, 15, 0.85)" in css or "rgba(15,15,15,0.85)" in css
    )
    assert has_rgba, (
        "lightbox.css NE sadrzi `rgba(15, 15, 15, 0.85)` (ili bez whitespace-a). "
        "AC3 + DESIGN.md § Modal/Lightbox linija 287 — backdrop boja je locked."
    )


# AC-3: @media (prefers-reduced-motion: reduce) blok
def test_ac3_lightbox_css_respects_prefers_reduced_motion():
    """AC3: lightbox.css mora imati `@media (prefers-reduced-motion: reduce)` blok
    (defensive CSS guard — JS init vec postavlja openEffect: 'none', ali CSS race condition guard).
    """
    assert LIGHTBOX_CSS.exists(), "lightbox.css ne postoji (drugi test hvata)."
    css = LIGHTBOX_CSS.read_text(encoding="utf-8")
    assert "@media (prefers-reduced-motion: reduce)" in css, (
        "lightbox.css NE sadrzi `@media (prefers-reduced-motion: reduce)` blok. "
        "AC3 + project-context.md § A11y must-haves linija 689."
    )


# =============================================================================
# AC4 — main.css @import (1 test)
# =============================================================================


# AC-4: main.css sadrzi @import url('./components/lightbox.css');
def test_ac4_main_css_imports_lightbox_component():
    """AC4: static/css/main.css mora sadrzati red `@import url('./components/lightbox.css');`
    (TACNO mirror postojecih 8 @import url('./components/...') linija — Story 1.7 + 1.8 invariant).

    Quote-agnostic substring search: provera `@import` + `components/lightbox.css` u istom file-u.
    """
    assert MAIN_CSS.exists(), f"main.css ne postoji na {MAIN_CSS} (regression — Story 1.6 deliverable)."
    css = MAIN_CSS.read_text(encoding="utf-8")
    assert "@import" in css, (
        "main.css NE sadrzi nijedan @import direktiv (regression — Story 1.7 dodala 5)."
    )
    assert "components/lightbox.css" in css, (
        "main.css NE sadrzi referencu na `components/lightbox.css`. "
        "AC4 — Dev mora dodati `@import url('./components/lightbox.css');` na kraju imports lista."
    )
    # Verifikuj da TA `components/lightbox.css` referenca jeste u kontekstu @import direktive
    # (NE u komentaru ili drugom kontekstu) — provera kombinacije supstring-a
    # u jednoj liniji.
    found_import_line = False
    for line in css.splitlines():
        if "@import" in line and "components/lightbox.css" in line:
            found_import_line = True
            break
    assert found_import_line, (
        "main.css ima `components/lightbox.css` substring, ali NE u redu sa `@import`. "
        "AC4 — referenca mora biti `@import url('./components/lightbox.css');` direktiv."
    )


# =============================================================================
# AC5 — base.html cascade (4 testa + 1 vendor-before-init)
# =============================================================================


# AC-5: GLightbox CSS link u HEAD izmedju tokens.css i bootstrap_css
def test_ac5_base_html_links_glightbox_css_in_head():
    """AC5: templates/base.html mora sadrzati `vendor/glightbox/glightbox.min.css` u HEAD
    sekciji IZMEDJU `css/tokens.css` linka i `bootstrap_css` poziva.

    Quote-agnostic indeks comparisons. Razlog za pozicioniranje: nas override
    (`static/css/components/lightbox.css` ucitan kroz `main.css` posle Bootstrap-a)
    pobedjuje u cascade.
    """
    assert BASE_HTML.exists(), f"base.html ne postoji na {BASE_HTML}."
    source = BASE_HTML.read_text(encoding="utf-8")
    assert "css/tokens.css" in source, (
        "base.html NE sadrzi `css/tokens.css` (regression — Story 1.5 deliverable)."
    )
    assert "vendor/glightbox/glightbox.min.css" in source, (
        "base.html NE sadrzi `vendor/glightbox/glightbox.min.css` link. "
        "AC5 + Task 5.2 — Dev mora dodati GLightbox CSS link u HEAD."
    )
    assert "bootstrap_css" in source, (
        "base.html NE sadrzi `bootstrap_css` (regression — Story 1.6 deliverable)."
    )
    tokens_idx = source.index("css/tokens.css")
    glightbox_css_idx = source.index("vendor/glightbox/glightbox.min.css")
    bootstrap_css_idx = source.index("bootstrap_css")
    assert tokens_idx < glightbox_css_idx, (
        f"base.html — `tokens.css` ({tokens_idx}) MORA biti PRE "
        f"`vendor/glightbox/glightbox.min.css` ({glightbox_css_idx}). AC5 cascade order."
    )
    assert glightbox_css_idx < bootstrap_css_idx, (
        f"base.html — `vendor/glightbox/glightbox.min.css` ({glightbox_css_idx}) MORA biti PRE "
        f"`bootstrap_css` ({bootstrap_css_idx}). AC5 — nas override mora pobediti u cascade."
    )


# AC-5: glightbox.min.js + lightbox-init.js script tags PRE {% block scripts %}
def test_ac5_base_html_scripts_in_body_before_block():
    """AC5: base.html mora sadrzati `vendor/glightbox/glightbox.min.js` + `js/lightbox-init.js`
    script tag-ove PRE `{% block scripts %}` (per-page scripts dolaze POSLE site-wide).
    """
    assert BASE_HTML.exists(), f"base.html ne postoji na {BASE_HTML}."
    source = BASE_HTML.read_text(encoding="utf-8")
    assert "vendor/glightbox/glightbox.min.js" in source, (
        "base.html NE sadrzi `vendor/glightbox/glightbox.min.js` script tag. "
        "AC5 + Task 5.3 — vendor JS mora biti ucitan PRE init modula."
    )
    assert "js/lightbox-init.js" in source, (
        "base.html NE sadrzi `js/lightbox-init.js` script tag. "
        "AC5 + Task 5.3 — init modul mora biti ucitan POSLE vendor JS-a."
    )
    assert "{% block scripts %}" in source, (
        "base.html NE sadrzi `{% block scripts %}` (regression — Story 1.6 deliverable)."
    )
    block_scripts_idx = source.index("{% block scripts %}")
    vendor_js_idx = source.index("vendor/glightbox/glightbox.min.js")
    init_js_idx = source.index("js/lightbox-init.js")
    assert vendor_js_idx < block_scripts_idx, (
        f"base.html — `vendor/glightbox/glightbox.min.js` ({vendor_js_idx}) MORA biti PRE "
        f"`{{% block scripts %}}` ({block_scripts_idx}). AC5 — site-wide scripts PRVI."
    )
    assert init_js_idx < block_scripts_idx, (
        f"base.html — `js/lightbox-init.js` ({init_js_idx}) MORA biti PRE "
        f"`{{% block scripts %}}` ({block_scripts_idx}). AC5 — site-wide scripts PRVI."
    )


# AC-5: Django komentar `{# Per-page scripts POSLE site-wide ...` preserved
def test_ac5_base_html_line_38_django_comment_preserved():
    """AC5: base.html mora ZADRZATI Django komentar `{# Per-page scripts POSLE site-wide ...`
    (Story 1.6 deliverable + regression guard). Komentar je shift-ovan posle Story 2.5 Edit-a
    (sa linije 38 na liniju ~41), ali substring mora ostati u source-u.
    """
    assert BASE_HTML.exists(), f"base.html ne postoji na {BASE_HTML}."
    source = BASE_HTML.read_text(encoding="utf-8")
    assert "{# Per-page scripts POSLE site-wide" in source, (
        "base.html NE sadrzi Django komentar `{# Per-page scripts POSLE site-wide ...`. "
        "AC5 + Story 1.6 regression — Dev Edit MORA ocuvati ovaj komentar (deliverable Story 1.6)."
    )


# AC-5: lightbox-init.js indeks > sticky-nav.js indeks (sticky-nav PRVI, lightbox POSLE)
def test_ac5_lightbox_scripts_after_sticky_nav():
    """AC5: u base.html source-u, indeks `lightbox-init.js` MORA biti VECI od indeksa
    `sticky-nav.js` (vendor + init Lightbox dolaze POSLE Story 1.8 sticky-nav.js).
    """
    assert BASE_HTML.exists(), f"base.html ne postoji na {BASE_HTML}."
    source = BASE_HTML.read_text(encoding="utf-8")
    assert "js/sticky-nav.js" in source, (
        "base.html NE sadrzi `js/sticky-nav.js` (regression — Story 1.8 deliverable)."
    )
    assert "js/lightbox-init.js" in source, (
        "base.html NE sadrzi `js/lightbox-init.js` (drugi test hvata)."
    )
    sticky_nav_idx = source.index("js/sticky-nav.js")
    lightbox_init_idx = source.index("js/lightbox-init.js")
    assert lightbox_init_idx > sticky_nav_idx, (
        f"base.html — `lightbox-init.js` ({lightbox_init_idx}) MORA biti POSLE "
        f"`sticky-nav.js` ({sticky_nav_idx}). AC5 redosled enforcement."
    )


# AC-5 + Vendor-before-init guard: glightbox.min.js indeks < lightbox-init.js indeks
def test_ac5_glightbox_vendor_before_init_script():
    """AC5: u base.html source-u, indeks `vendor/glightbox/glightbox.min.js` MORA biti
    MANJI od indeksa `js/lightbox-init.js`. Vendor library mora biti ucitan PRE init modula
    (defensive guard `typeof window.GLightbox !== 'function'` u init.js oslanja se na ovo).
    """
    assert BASE_HTML.exists(), f"base.html ne postoji na {BASE_HTML}."
    source = BASE_HTML.read_text(encoding="utf-8")
    assert "vendor/glightbox/glightbox.min.js" in source, (
        "base.html NE sadrzi `vendor/glightbox/glightbox.min.js` (drugi test hvata)."
    )
    assert "js/lightbox-init.js" in source, (
        "base.html NE sadrzi `js/lightbox-init.js` (drugi test hvata)."
    )
    vendor_idx = source.index("vendor/glightbox/glightbox.min.js")
    init_idx = source.index("js/lightbox-init.js")
    assert vendor_idx < init_idx, (
        f"base.html — `vendor/glightbox/glightbox.min.js` ({vendor_idx}) MORA biti PRE "
        f"`js/lightbox-init.js` ({init_idx}). AC5 — vendor library mora biti loaded "
        "pre init modula (typeof window.GLightbox guard zavisi od ovog redosleda)."
    )


# =============================================================================
# AC7 — Anti-CDN guard (1 test)
# =============================================================================


# AC-7: no CDN URL reference za GLightbox bilo gde u svim relevantnim fajlovima
def test_anti_cdn_no_external_lightbox_references():
    """AC7: nijedan od `templates/base.html`, `static/css/main.css`, `static/js/lightbox-init.js`,
    `static/css/components/lightbox.css` NE SME sadrzati CDN reference:
    `cdnjs.cloudflare.com`, `unpkg.com`, `jsdelivr.net`, `cdn.jsdelivr.net`.

    Sva referenca na GLightbox vendor mora biti relativna `{% static 'vendor/glightbox/...' %}`.
    Mirror Story 1.6 AC8 anti-pattern guard pattern.
    """
    cdn_patterns = [
        "cdnjs.cloudflare.com",
        "unpkg.com",
        "jsdelivr.net",
        "cdn.jsdelivr.net",
    ]
    files_to_check = [
        ("base.html", BASE_HTML),
        ("main.css", MAIN_CSS),
        ("lightbox-init.js", LIGHTBOX_INIT_JS),
        ("lightbox.css", LIGHTBOX_CSS),
    ]
    offending = []
    for name, path in files_to_check:
        if not path.exists():
            # Skip — drugi testovi hvataju missing files (file existence assertions)
            continue
        source = path.read_text(encoding="utf-8", errors="replace")
        for cdn in cdn_patterns:
            if cdn in source:
                offending.append((name, cdn))
    assert not offending, (
        f"CDN reference pronadjene u source-u: {offending}. "
        "AC7 — GLightbox MORA biti lokalno hostovan (no cdnjs.cloudflare.com / unpkg.com / "
        "jsdelivr.net / cdn.jsdelivr.net). Sva referenca preko `{% static 'vendor/glightbox/...' %}`."
    )


# AC-7 (fix-iter-1): plyr:false guard — dormant CDN risk u vendor source-u
def test_ac7_plyr_cdn_dormant_via_buildoptions_disable():
    """Anti-CDN reinforcement (Security review iter 1 — SEC-MEDIUM):
    lightbox-init.js MUST set `plyr: false` in buildOptions() to neutralize
    the hard-coded `cdn.plyr.io` URLs baked into GLightbox 3.x vendor source.

    GLightbox 3.3.1 vendor JS sadrzi hard-coded `cdn.plyr.io` URL-ove za video
    player. Trenutno DORMANT (image galerije ne trigger-uju), ali buduca story
    sa video lightbox-om bi silently fetch-ovala sa third-party CDN — GDPR
    risk + supply-chain attack surface. Eksplicitan `plyr: false` u
    buildOptions() neutralise tu code path.

    If a future Dev removes `plyr: false`, ovaj test fail-uje PRE nego sto
    dormant CDN fire-uje (defensive regression guard).
    """
    assert LIGHTBOX_INIT_JS.exists(), "lightbox-init.js ne postoji (drugi test hvata)."
    source = LIGHTBOX_INIT_JS.read_text(encoding="utf-8")
    assert "plyr: false" in source or "plyr:false" in source, (
        "buildOptions() mora eksplicitno postaviti `plyr: false` da disable-uje "
        "vendor hard-coded cdn.plyr.io fetch path-eve (Security review iter 1 finding). "
        "Re-enable tek kad Plyr bude lokalno hostovan (future story)."
    )
