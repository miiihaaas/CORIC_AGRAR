"""Tests za Story 1.7 - Reusable Visual Komponente.

Pokriva:
- AC1: templates/partials/ + static/css/components/ struktura (5 partials + 5 CSS fajlova)
- AC2: Repeating Element partial — 2 varijante (green / jeegee) + __corner positioning + aria-hidden
- AC3: Pill Button partial — 3 varijante (primary / secondary / cta-light) + as=link|button + type
- AC4: Wave Divider partial — inline SVG sa aria-hidden + token-based fill (IMP-17)
- AC5: Section Eyebrow partial — UPPERCASE caption sa 2 zlatne linije
- AC6: Hero Overlay Card partial — h1 + bullets (cap @ 3) + watermark + brand_logo_alt
- AC7: Token discipline — bez hardcoded hex/rgb/hsl/64px; sve preko var(--...)
- AC8: CSS load strategy (Strategy A — @import u main.css) + base.html load order
- A11y: prefers-reduced-motion + forced-colors + min-height 44px (WCAG 2.5.5)
- IMP-8 / AC9.10: collectstatic hash verification — DEFERRED via @pytest.mark.skip

Pokrenuti sa:
    uv run pytest tests/test_visual_components.py -v --tb=short

TEA RED faza: svi testovi MORAJU pasti (FileNotFoundError, AssertionError, TemplateDoesNotExist)
osim 1 test koji je @pytest.mark.skip (deferred).
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

# 5 partial-a koje Story 1.7 uvodi
PARTIAL_REPEATING = PARTIALS_DIR / "repeating_element.html"
PARTIAL_PILL_BUTTON = PARTIALS_DIR / "pill_button.html"
PARTIAL_WAVE_DIVIDER = PARTIALS_DIR / "wave_divider.html"
PARTIAL_SECTION_EYEBROW = PARTIALS_DIR / "section_eyebrow.html"
PARTIAL_HERO_OVERLAY = PARTIALS_DIR / "hero_overlay_card.html"

ALL_NEW_PARTIALS = [
    PARTIAL_REPEATING,
    PARTIAL_PILL_BUTTON,
    PARTIAL_WAVE_DIVIDER,
    PARTIAL_SECTION_EYEBROW,
    PARTIAL_HERO_OVERLAY,
]

# 5 CSS fajlova koje Story 1.7 uvodi
CSS_REPEATING = COMPONENTS_DIR / "repeating-element.css"
CSS_PILL_BUTTON = COMPONENTS_DIR / "pill-button.css"
CSS_WAVE_DIVIDER = COMPONENTS_DIR / "wave-divider.css"
CSS_SECTION_EYEBROW = COMPONENTS_DIR / "section-eyebrow.css"
CSS_HERO_OVERLAY = COMPONENTS_DIR / "hero-overlay-card.css"

ALL_NEW_CSS_FILES = [
    CSS_REPEATING,
    CSS_PILL_BUTTON,
    CSS_WAVE_DIVIDER,
    CSS_SECTION_EYEBROW,
    CSS_HERO_OVERLAY,
]

TEST_SECRET = "test-secret-key-for-tea-story-1-7-visual-components-not-real"


# =============================================================================
# Helper funkcije
# =============================================================================


def _ensure_sys_path() -> None:
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))


def _setup_django() -> None:
    """Bootstrap Django (django.setup) idempotent za render testove.

    Identičan pattern kao u test_base_template.py (Story 1.6).
    """
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
            f"Verovatno Story 1.6 / 1.5 environment je broken."
        )


def _render_partial(template_path: str, context: dict | None = None) -> str:
    """Render Django partial sa datim context-om i vrati HTML string.

    Skip-uje test ako Django setup pukne; fail-uje ako partial ne postoji
    ili ne renderuje. Ovaj helper je SOT za sve render testove ovde.
    """
    _setup_django()
    try:
        from django.template import TemplateDoesNotExist
        from django.template.loader import render_to_string
    except ImportError:
        pytest.skip("Django template engine nedostupan.")
    ctx = context or {}
    try:
        return render_to_string(template_path, ctx)
    except TemplateDoesNotExist as exc:
        pytest.fail(
            f"Partial '{template_path}' ne postoji (TemplateDoesNotExist). "
            f"Story 1.7 mora kreirati. {exc}"
        )


def _read_css(path: Path) -> str:
    """Procita CSS fajl. Fail-uje sa jasnom porukom ako ne postoji."""
    if not path.exists():
        pytest.fail(
            f"CSS fajl ne postoji na {path.relative_to(PROJECT_ROOT)}. "
            f"Story 1.7 mora kreirati."
        )
    return path.read_text(encoding="utf-8")


def _read_partial(path: Path) -> str:
    """Procita partial source fajl. Fail-uje ako ne postoji."""
    if not path.exists():
        pytest.fail(
            f"Partial ne postoji na {path.relative_to(PROJECT_ROOT)}. "
            f"Story 1.7 mora kreirati."
        )
    return path.read_text(encoding="utf-8")


# =============================================================================
# AC1 — Struktura: 5 partials + 5 CSS fajlova + components/ direktorijum
# =============================================================================


# AC-1: static/css/components/ direktorijum mora postojati
def test_ac1_components_directory_exists():
    """AC1: static/css/components/ direktorijum mora postojati.

    Story 1.7 ga prvi put kreira (Task 2.1).
    """
    assert COMPONENTS_DIR.exists() and COMPONENTS_DIR.is_dir(), (
        f"static/css/components/ ne postoji na {COMPONENTS_DIR.relative_to(PROJECT_ROOT)}. "
        f"Story 1.7 AC1 + Task 2.1 — Dev mora kreirati direktorijum."
    )


# AC-1: svih 5 partial-a mora postojati u templates/partials/
def test_ac1_all_5_partials_present():
    """AC1: svih 5 novih partial-a mora postojati u templates/partials/.

    Story 1.4 language_switcher.html ostaje netaknut (regression guard
    je u zasebnim render testovima drugih story-ja).
    """
    missing = [p.relative_to(PROJECT_ROOT) for p in ALL_NEW_PARTIALS if not p.exists()]
    assert not missing, (
        f"Sledeći partial-i ne postoje: {missing}. "
        f"Story 1.7 AC1 — svih 5 mora biti kreirano."
    )


# AC-1: svih 5 CSS fajlova mora postojati u static/css/components/
def test_ac1_all_5_css_files_present():
    """AC1: svih 5 component CSS fajlova mora postojati u static/css/components/."""
    missing = [p.relative_to(PROJECT_ROOT) for p in ALL_NEW_CSS_FILES if not p.exists()]
    assert not missing, (
        f"Sledeći CSS fajlovi ne postoje: {missing}. "
        f"Story 1.7 AC1 — svih 5 mora biti kreirano."
    )


# =============================================================================
# AC2 — Repeating Element partial (green + jeegee variants)
# =============================================================================


# AC-2: Repeating Element rendera green variantu sa BEM klasom + aria-hidden + SVG corner
def test_ac2_repeating_element_renders_green_variant():
    """AC2: render sa variant="green" → BEM klasa --green + aria-hidden + SVG corner cluster."""
    html = _render_partial("partials/repeating_element.html", {"variant": "green"})
    assert "coric-repeating-element" in html, (
        "Render NE sadrži `coric-repeating-element` base klasu. AC2."
    )
    assert "coric-repeating-element--green" in html, (
        "Render NE sadrži `coric-repeating-element--green` modifier klasu. AC2."
    )
    assert 'aria-hidden="true"' in html, (
        "Render NE sadrži `aria-hidden=\"true\"` (dekorativan element). AC2."
    )
    # Mora sadržati inline SVG sa corner klasom (NE <img>)
    assert "<svg" in html, "Render NE sadrži inline `<svg>` korner cluster. AC2."
    assert "coric-repeating-element__corner" in html, (
        "Render NE sadrži `.coric-repeating-element__corner` klasu (CRITICAL-2 — "
        "SVG mora imati corner positioning klasu). AC2."
    )


# AC-2: Repeating Element SVG path-ovi sadrže koncentrične bele lukove
def test_ac2_repeating_element_has_white_arcs_with_opacity():
    """AC2: SVG path-ovi MORAJU imati `stroke="white"` + `opacity="0.5"` + `stroke-width="1"`.

    Interface contract §2.1 + Dev Notes Template predlog: 3-4 koncentričnih lukova
    u gornjem desnom uglu sa tankim belim crtama (named CSS keyword exemption per
    AC7 EXCEPTION clause).
    """
    html = _render_partial("partials/repeating_element.html", {"variant": "green"})
    # Mora imati bar 1 path sa stroke="white"
    assert re.search(r'stroke\s*=\s*["\']white["\']', html), (
        "Render NE sadrži `stroke=\"white\"` na SVG path-u. AC2 + Dev Notes Template — "
        "koncentrični lukovi u gornjem desnom uglu MORAJU biti beli."
    )
    # Mora imati opacity="0.5" za suptilnost
    assert re.search(r'opacity\s*=\s*["\']0\.5["\']', html), (
        "Render NE sadrži `opacity=\"0.5\"` na SVG path-u. AC2 — luci su suptilni "
        "(0.5 opacity per DESIGN.md repeating-element)."
    )
    # Mora imati stroke-width="1" (tanke crte)
    assert re.search(r'stroke-width\s*=\s*["\']1["\']', html), (
        "Render NE sadrži `stroke-width=\"1\"` na SVG path-u. AC2 — tanki lukovi."
    )


# AC-2: Repeating Element rendera jeegee variantu (brand-specific Jeegee blue)
def test_ac2_repeating_element_renders_jeegee_variant():
    """AC2: render sa variant="jeegee" → BEM modifier --jeegee."""
    html = _render_partial("partials/repeating_element.html", {"variant": "jeegee"})
    assert "coric-repeating-element--jeegee" in html, (
        "Render NE sadrži `coric-repeating-element--jeegee` modifier. AC2."
    )
    # green variant ne sme biti naivno injektovan — modifier mora biti samo jeegee
    assert "coric-repeating-element--green" not in html, (
        "Render sadrži `--green` modifier iako je variant='jeegee'. AC2."
    )


# AC-2 + CRITICAL-2: `.coric-repeating-element__corner` CSS sa absolute positioning
def test_ac2_repeating_element_has_corner_positioning_css():
    """AC2 + CRITICAL-2: repeating-element.css sadrži __corner sa position: absolute + top:0 + right:0.

    Bez ovoga SVG renderuje kao block child sa pogrešnim pozicioniranjem (vidi story Task 3.7).
    """
    css = _read_css(CSS_REPEATING)
    # Mora sadržati __corner klasu sa absolute positioning
    assert re.search(r"\.coric-repeating-element__corner\s*\{", css), (
        "repeating-element.css NE sadrži `.coric-repeating-element__corner` blok. "
        "CRITICAL-2 — bez ovoga SVG arcs ne idu u ugao."
    )
    # Position absolute + top: 0 + right: 0 moraju biti prisutni u CSS-u
    assert re.search(r"position\s*:\s*absolute", css), (
        "repeating-element.css NE sadrži `position: absolute` (verovatno u __corner). CRITICAL-2."
    )
    assert re.search(r"top\s*:\s*0", css), (
        "repeating-element.css NE sadrži `top: 0` (verovatno u __corner). CRITICAL-2."
    )
    assert re.search(r"right\s*:\s*0", css), (
        "repeating-element.css NE sadrži `right: 0` (verovatno u __corner). CRITICAL-2."
    )


# =============================================================================
# AC3 — Pill Button partial (3 variants, as=link|button, type)
# =============================================================================


# AC-3: Pill Button primary varijanta — render sa label + href + klase
def test_ac3_pill_button_renders_primary_variant():
    """AC3: render sa variant="primary" label="Saznaj više" href="/proizvodi/" → BEM klase + label + href."""
    html = _render_partial(
        "partials/pill_button.html",
        {"variant": "primary", "label": "Saznaj više", "href": "/proizvodi/"},
    )
    assert "coric-button" in html, "Render NE sadrži `coric-button` base klasu. AC3."
    assert "coric-button--primary" in html, (
        "Render NE sadrži `coric-button--primary` modifier. AC3."
    )
    assert "Saznaj više" in html, "Render NE sadrži label tekst. AC3."
    assert 'href="/proizvodi/"' in html, "Render NE sadrži href atribut. AC3."
    # Default je <a> (as="link"); NE sme biti <button> ovde
    assert "<a " in html or html.lstrip().startswith("<a"), (
        "Render NE sadrži <a> element (default as='link'). AC3."
    )


# AC-3: Pill Button secondary + cta-light varijante
def test_ac3_pill_button_renders_secondary_and_cta_light_variants():
    """AC3: render sa variant="secondary" i "cta-light" → odgovarajuće BEM modifier klase."""
    html_sec = _render_partial(
        "partials/pill_button.html",
        {"variant": "secondary", "label": "Kontakt", "href": "/kontakt/"},
    )
    assert "coric-button--secondary" in html_sec, (
        "Render NE sadrži `coric-button--secondary` modifier. AC3."
    )
    html_cta = _render_partial(
        "partials/pill_button.html",
        {"variant": "cta-light", "label": "Preuzmi katalog", "href": "/katalog.pdf"},
    )
    assert "coric-button--cta-light" in html_cta, (
        "Render NE sadrži `coric-button--cta-light` modifier. AC3."
    )


# AC-3: Pill Button as="link" rendera <a>, as="button" rendera <button>
def test_ac3_pill_button_renders_as_anchor_and_button():
    """AC3 + IMP-11: as='link' (default) rendera <a>; as='button' rendera <button>."""
    html_link = _render_partial(
        "partials/pill_button.html",
        {"variant": "primary", "label": "Link CTA", "href": "/"},
    )
    # Default render mora biti <a>
    assert "<a " in html_link, "Default render NIJE <a>. AC3 + IMP-11."
    html_button = _render_partial(
        "partials/pill_button.html",
        {"as": "button", "variant": "primary", "label": "Klikni"},
    )
    assert "<button" in html_button, (
        "Render sa as='button' NIJE <button> element. AC3 + IMP-11."
    )
    # button render mora imati type atribut
    assert re.search(r'type\s*=\s*["\']button["\']', html_button), (
        "Render sa as='button' NE sadrži default `type=\"button\"`. AC3 + IMP-11."
    )


# AC-3 + IMP-11: as="button" + type="submit" → <button type="submit">
def test_ac3_pill_button_supports_as_button_with_type_submit():
    """AC3 + IMP-11: as='button' + type='submit' → <button type="submit"> (form submit support)."""
    html = _render_partial(
        "partials/pill_button.html",
        {"as": "button", "type": "submit", "variant": "primary", "label": "Pošalji"},
    )
    assert "<button" in html, "Render NIJE <button> element."
    assert re.search(r'type\s*=\s*["\']submit["\']', html), (
        "Render NE sadrži `type=\"submit\"`. AC3 + IMP-11 — form submit support."
    )
    assert "Pošalji" in html, "Render NE sadrži label tekst."


# =============================================================================
# AC4 — Wave Divider partial (inline SVG, aria-hidden, token-based fill)
# =============================================================================


# AC-4: Wave Divider rendera inline SVG sa aria-hidden + token-based fill (IMP-17)
def test_ac4_wave_divider_renders_with_aria_hidden_and_token_fill():
    """AC4 + IMP-17: render sadrži <svg sa aria-hidden + fill='var(--color-brand-green-800)'.

    NE sme biti <img src="..."> (inline only); NE sme biti `currentColor` ili hardcoded hex.
    """
    html = _render_partial("partials/wave_divider.html", {})
    assert "<svg" in html, (
        "Render NE sadrži inline `<svg>` (mora biti inline, NE <img>). AC4."
    )
    assert "<img " not in html, (
        "Render sadrži `<img>` tag — Wave Divider MORA biti inline SVG. AC4."
    )
    assert 'aria-hidden="true"' in html, (
        "Render NE sadrži `aria-hidden=\"true\"`. AC4."
    )
    # IMP-17: SVG path mora imati eksplicitan token-based fill
    assert 'fill="var(--color-brand-green-800)"' in html, (
        "Render NE sadrži `fill=\"var(--color-brand-green-800)\"` na SVG path-u. "
        "AC4 + IMP-17 (FOUC fallback — NE `currentColor`, NE hardcoded hex)."
    )
    # KRITIČNO: NE sme biti hardcoded hex na SVG path-u
    assert not re.search(r'fill\s*=\s*["\']#[0-9a-fA-F]{3,8}["\']', html), (
        "Render sadrži hardcoded hex u fill atributu (npr. `fill=\"#25402f\"`). "
        "AC4 + AC7 — token discipline."
    )


# AC-4: Wave Divider position="top" (default) i position="bottom" → BEM modifier
def test_ac4_wave_divider_supports_top_and_bottom_position():
    """AC4: position='bottom' dodaje modifier klasu `--bottom`; default 'top' ne dodaje."""
    html_top = _render_partial("partials/wave_divider.html", {})
    assert "coric-wave-divider--bottom" not in html_top, (
        "Default render (position='top') NE sme imati `--bottom` modifier. AC4."
    )
    html_bot = _render_partial("partials/wave_divider.html", {"position": "bottom"})
    assert "coric-wave-divider--bottom" in html_bot, (
        "Render sa position='bottom' NE sadrži `coric-wave-divider--bottom` modifier. AC4."
    )


# =============================================================================
# AC5 — Section Eyebrow partial (UPPERCASE caption sa zlatnim linijama)
# =============================================================================


# AC-5: Section Eyebrow rendera tekst + 2 zlatne linije span-a
def test_ac5_section_eyebrow_renders_uppercase_text_with_gold_lines():
    """AC5: render sa text='PROIZVODI' → coric-section-eyebrow + 2 __line span-a + text."""
    html = _render_partial(
        "partials/section_eyebrow.html", {"text": "PROIZVODI"}
    )
    assert "coric-section-eyebrow" in html, (
        "Render NE sadrži `coric-section-eyebrow` base klasu. AC5."
    )
    # 2 __line span-a (leva i desna zlatna lenta)
    line_count = len(re.findall(r"coric-section-eyebrow__line", html))
    assert line_count == 2, (
        f"Render ima {line_count} `__line` span-ova, očekivano TAČNO 2 (leva i desna). AC5."
    )
    # Tekst u __text span-u
    assert "coric-section-eyebrow__text" in html, (
        "Render NE sadrži `coric-section-eyebrow__text` span. AC5."
    )
    assert "PROIZVODI" in html, "Render NE sadrži tekst 'PROIZVODI'. AC5."


# AC-5: Section Eyebrow `variant="on-dark"` dodaje modifier klasu
def test_ac5_section_eyebrow_on_dark_variant_adds_modifier_class():
    """AC5: render sa variant='on-dark' → klasa sadrži `coric-section-eyebrow--on-dark`.

    Interface contract §2.4 — `on-dark` je jedina validna variant vrednost; menja text
    color na `var(--color-semantic-text-on-dark)` (white) za upotrebu na green-800 pozadini.
    """
    html = _render_partial(
        "partials/section_eyebrow.html",
        {"text": "Naša priča", "variant": "on-dark"},
    )
    assert "coric-section-eyebrow--on-dark" in html, (
        "Render sa variant='on-dark' NE sadrži `coric-section-eyebrow--on-dark` modifier. AC5."
    )


# AC-5: Section Eyebrow `tag="p"` rendera koren kao <p>
def test_ac5_section_eyebrow_custom_tag_renders_as_p():
    """AC5: render sa tag='p' → korenski element je `<p>`, NE default `<div>`.

    Interface contract §2.4 — `tag` parametar default `div`, prihvata `p`, `span`, `h6`
    za semantičku hijerarhiju.
    """
    html = _render_partial(
        "partials/section_eyebrow.html", {"text": "O nama", "tag": "p"}
    )
    # Koren mora biti <p ...> (sa whitespace ili klasom posle)
    assert re.search(r"<p[\s>]", html), (
        "Render sa tag='p' NE počinje sa `<p>` korenom. AC5 — `tag` parametar mora "
        "kontrolisati korenski element."
    )
    # Default <div> NE sme biti korenski element kad je tag='p'
    # (matcher hvata <div> kao prvi tag — pre svih spanova)
    first_tag_match = re.search(r"<(\w+)[\s>]", html.lstrip())
    assert first_tag_match is not None, "Render je prazan ili nema HTML tagova."
    assert first_tag_match.group(1) == "p", (
        f"Korenski tag je `<{first_tag_match.group(1)}>` umesto `<p>`. AC5."
    )


# =============================================================================
# AC6 — Hero Overlay Card partial (h1 + bullets cap + brand_logo_alt)
# =============================================================================


# AC-6 + IMP-14: Hero Overlay Card rendera sa brand_logo_alt
def test_ac6_hero_overlay_card_renders_with_brand_logo_alt():
    """AC6 + IMP-14: render sa brand_logo='/img/logo.png' brand_logo_alt='Coric Agrar' → alt postavljen."""
    html = _render_partial(
        "partials/hero_overlay_card.html",
        {
            "title": "Hero Test",
            "brand_logo": "/static/img/logo.png",
            "brand_logo_alt": "Coric Agrar",
            "bullets": ["Stavka 1", "Stavka 2"],
        },
    )
    assert "coric-hero-overlay-card" in html, (
        "Render NE sadrži `coric-hero-overlay-card` base klasu. AC6."
    )
    assert "<h1" in html, "Render NE sadrži h1 element. AC6."
    assert "Hero Test" in html, "Render NE sadrži title tekst. AC6."
    assert 'src="/static/img/logo.png"' in html, (
        "Render NE sadrži brand_logo src. AC6."
    )
    assert 'alt="Coric Agrar"' in html, (
        "Render NE sadrži `alt=\"Coric Agrar\"`. AC6 + IMP-14."
    )


# AC-6 + IMP-15: Hero Overlay Card limitira bullets na 3 (|slice:":3")
def test_ac6_hero_overlay_card_caps_bullets_at_3():
    """AC6 + IMP-15: render sa 5 bullets → samo prvih 3 render-ovan."""
    html = _render_partial(
        "partials/hero_overlay_card.html",
        {
            "title": "Cap Test",
            "bullets": ["Prva", "Druga", "Treca", "Cetvrta", "Peta"],
        },
    )
    assert "Prva" in html, "Render NE sadrži 1. bullet. AC6."
    assert "Druga" in html, "Render NE sadrži 2. bullet. AC6."
    assert "Treca" in html, "Render NE sadrži 3. bullet. AC6."
    assert "Cetvrta" not in html, (
        "Render sadrži 4. bullet — cap na 3 NE radi (verovatno |slice:\":3\" nedostaje). "
        "AC6 + IMP-15."
    )
    assert "Peta" not in html, (
        "Render sadrži 5. bullet — cap na 3 NE radi. AC6 + IMP-15."
    )


# AC-6 + IMP-14: brand_logo_alt default je prazan string
def test_ac6_hero_overlay_card_brand_logo_alt_default_empty():
    """AC6 + IMP-14: render sa brand_logo bez brand_logo_alt → alt="" (prazan default)."""
    html = _render_partial(
        "partials/hero_overlay_card.html",
        {
            "title": "Alt Default Test",
            "brand_logo": "/static/img/logo.png",
            # NEMA brand_logo_alt — default mora biti prazno
        },
    )
    # alt="" mora biti prisutno (caller je odgovoran da postavi non-empty kad je info)
    assert 'alt=""' in html, (
        "Render bez brand_logo_alt NE sadrži `alt=\"\"` (default empty). AC6 + IMP-14."
    )


# AC-6 + IMP-14: brand_logo_alt explicit override
def test_ac6_hero_overlay_card_brand_logo_alt_explicit():
    """AC6 + IMP-14: render sa brand_logo_alt='Jeegee logo' → alt='Jeegee logo'."""
    html = _render_partial(
        "partials/hero_overlay_card.html",
        {
            "title": "Alt Explicit Test",
            "brand_logo": "/static/img/jeegee.png",
            "brand_logo_alt": "Jeegee logo",
        },
    )
    assert 'alt="Jeegee logo"' in html, (
        "Render NE sadrži `alt=\"Jeegee logo\"`. AC6 + IMP-14."
    )


# AC-6: Hero Overlay Card includes watermark Repeating Element
def test_ac6_hero_overlay_card_includes_watermark_repeating_element():
    """AC6: render → sadrži `coric-hero-overlay-card__watermark` div + watermark Repeating Element.

    Interface contract §2.5 mandates watermark u dole desnom uglu — `{% include
    "partials/repeating_element.html" with variant=variant|default:"green" %}`.
    Bez ovog includa, watermark ne postoji (vizuelni regression).
    """
    html = _render_partial(
        "partials/hero_overlay_card.html",
        {"title": "Watermark Test", "bullets": ["A", "B"]},
    )
    assert "coric-hero-overlay-card__watermark" in html, (
        "Render NE sadrži `coric-hero-overlay-card__watermark` element. AC6 — "
        "watermark MORA biti renderovan."
    )
    # Watermark Repeating Element MORA biti unutar — default variant 'green'
    assert "coric-repeating-element" in html, (
        "Render NE sadrži `coric-repeating-element` unutar watermark-a. AC6 — "
        "watermark mora include-ovati Repeating Element partial."
    )
    assert "coric-repeating-element--green" in html, (
        "Render NE sadrži `coric-repeating-element--green` default variant u watermark-u. "
        "AC6 — default variant je 'green'."
    )


# AC-6: Hero Overlay Card prosleđuje variant na watermark Repeating Element
def test_ac6_hero_overlay_card_passes_variant_to_watermark():
    """AC6: render sa variant='jeegee' → watermark Repeating Element ima `--jeegee` klasu.

    Interface contract §2.5 — `variant` parametar se prosleđuje na watermark Repeating
    Element (Jeegee strana koristi 'jeegee', default je 'green').
    """
    html = _render_partial(
        "partials/hero_overlay_card.html",
        {"title": "Jeegee Test", "variant": "jeegee", "bullets": ["X"]},
    )
    assert "coric-repeating-element--jeegee" in html, (
        "Render sa variant='jeegee' NE sadrži `coric-repeating-element--jeegee` "
        "u watermark-u. AC6 — variant mora biti prosleđen na watermark."
    )
    # Green variant NE sme biti naivno injektovan
    assert "coric-repeating-element--green" not in html, (
        "Render sa variant='jeegee' sadrži `--green` modifier u watermark-u "
        "(verovatno default nije pravilno override-an). AC6."
    )


# =============================================================================
# AC7 — Token discipline (no hardcoded hex/rgb/64px; var(--...) korišćenje)
# =============================================================================


# AC-7: nijedan hardcoded hex (#XXX, #XXXXXX, #XXXXXXXX) u nijednom CSS-u
def test_ac7_no_hardcoded_hex_in_component_css():
    """AC7: grep -E '#[0-9a-fA-F]{3,8}' static/css/components/*.css → 0 matches."""
    offending = []
    for css_path in ALL_NEW_CSS_FILES:
        css = _read_css(css_path)
        # Pattern hex literal (3, 4, 6, ili 8 hex chars) — bilo gde u source-u
        matches = re.findall(r"#[0-9a-fA-F]{3,8}\b", css)
        if matches:
            offending.append((css_path.name, matches))
    assert not offending, (
        f"Hardcoded hex pronađen u CSS fajlovima: {offending}. "
        f"AC7 — sve boje MORAJU biti `var(--color-*)`."
    )


# AC-7: nijedan hardcoded rgb()/hsl() u CSS-u
def test_ac7_no_hardcoded_rgb_hsl_in_component_css():
    """AC7: nijedan rgb(...) ili hsl(...) literal u component CSS-ovima."""
    offending = []
    for css_path in ALL_NEW_CSS_FILES:
        css = _read_css(css_path)
        # rgb/rgba/hsl/hsla sa numerckim argumentima (NE `rgb(var(--x))` koji je legitiman)
        rgb_matches = re.findall(r"\brgba?\s*\(\s*\d", css)
        hsl_matches = re.findall(r"\bhsla?\s*\(\s*\d", css)
        if rgb_matches or hsl_matches:
            offending.append((css_path.name, rgb_matches, hsl_matches))
    assert not offending, (
        f"Hardcoded rgb()/hsl() pronađen u CSS-u: {offending}. "
        f"AC7 — sve boje preko `var(--color-*)`."
    )


# AC-7 + IMP-5: nijedan hardcoded 64px u CSS-u (mora var(--spacing-scale-10))
def test_ac7_no_hardcoded_64px_in_component_css():
    """AC7 + IMP-5: grep '64px' static/css/components/*.css → 0 matches.

    Section Eyebrow line width MORA biti `var(--spacing-scale-10)`, NE hardcoded 64px.
    """
    offending = []
    for css_path in ALL_NEW_CSS_FILES:
        css = _read_css(css_path)
        # Tačan 64px sa word boundary (NE 164px, 640px, itd.)
        if re.search(r"(?<!\d)64px\b", css):
            offending.append(css_path.name)
    assert not offending, (
        f"Hardcoded `64px` pronađen u: {offending}. "
        f"AC7 + IMP-5 — mora biti `var(--spacing-scale-10)`."
    )


# AC-7: svaki component CSS koristi bar 1 var(--...) token
def test_ac7_components_use_var_tokens():
    """AC7: svaki component CSS MORA koristiti bar 1 `var(--...)` referencu."""
    missing = []
    for css_path in ALL_NEW_CSS_FILES:
        css = _read_css(css_path)
        if not re.search(r"var\(\s*--", css):
            missing.append(css_path.name)
    assert not missing, (
        f"Sledeći CSS fajlovi NE koriste nijedan `var(--...)` token: {missing}. "
        f"AC7 — komponente MORAJU konzumirati tokene iz tokens.css."
    )


# AC-9.3: kvantitativni token usage threshold-ovi kroz SVE komponente
def test_ac9_components_meet_token_usage_thresholds():
    """AC9.3: aggregate token usage kroz `static/css/components/*.css` mora pogoditi minimume.

    AC9.3 specifies:
      - `>= 5 matches` za `var(--color`   (svaka komponenta konzumira bar 1 color token)
      - `>= 4 matches` za `var(--rounded` (button, repeating-element, hero-overlay-card pills/radii)
      - `>= 6 matches` za `var(--spacing` (eyebrow gap/margin, button padding, hero padding/title margin)
    """
    combined = ""
    for css_path in ALL_NEW_CSS_FILES:
        combined += _read_css(css_path) + "\n"
    color_count = len(re.findall(r"var\(\s*--color", combined))
    rounded_count = len(re.findall(r"var\(\s*--rounded", combined))
    spacing_count = len(re.findall(r"var\(\s*--spacing", combined))
    assert color_count >= 5, (
        f"Aggregate `var(--color` matches kroz components/*.css = {color_count}, "
        f"AC9.3 zahteva >= 5 (svaka komponenta bar 1 color token)."
    )
    assert rounded_count >= 4, (
        f"Aggregate `var(--rounded` matches = {rounded_count}, AC9.3 zahteva >= 4 "
        f"(pill button, repeating-element, hero-overlay-card, ostali radii)."
    )
    assert spacing_count >= 6, (
        f"Aggregate `var(--spacing` matches = {spacing_count}, AC9.3 zahteva >= 6 "
        f"(eyebrow gap+margin, button padding, hero padding+title margin+watermark offsets)."
    )


# =============================================================================
# A11y / Edge case tests (CRITICAL-3 + IMP-12 + IMP-13)
# =============================================================================


# CRITICAL-3: Pill Button @media (prefers-reduced-motion: reduce) override
def test_pill_button_has_prefers_reduced_motion_override():
    """CRITICAL-3: pill-button.css MORA imati `@media (prefers-reduced-motion: reduce)` override.

    Story 1.7 ship-uje motion (200ms transition na hover), dakle Story 1.7 isporučuje guard.
    """
    css = _read_css(CSS_PILL_BUTTON)
    assert re.search(r"@media\s*\(\s*prefers-reduced-motion\s*:\s*reduce\s*\)", css), (
        "pill-button.css NE sadrži `@media (prefers-reduced-motion: reduce)` blok. "
        "CRITICAL-3 — ko ship-uje motion ship-uje i guard."
    )


# IMP-13: Pill Button @media (forced-colors: active) override (Windows High Contrast Mode)
def test_pill_button_has_forced_colors_override():
    """IMP-13: pill-button.css MORA imati `@media (forced-colors: active)` override.

    Primary varijanta ima `2px solid transparent` border koji postaje nevidljiv u WHCM —
    override postavlja `border-color: ButtonText` da bude vidljivo.
    """
    css = _read_css(CSS_PILL_BUTTON)
    assert re.search(r"@media\s*\(\s*forced-colors\s*:\s*active\s*\)", css), (
        "pill-button.css NE sadrži `@media (forced-colors: active)` blok. "
        "IMP-13 — Windows High Contrast Mode border visibility."
    )


# IMP-12: Pill Button min-height: 44px (WCAG 2.5.5/2.5.8 touch target minimum)
def test_pill_button_has_min_touch_target():
    """IMP-12: pill-button.css MORA imati `min-height: 44px` na .coric-button (WCAG touch target)."""
    css = _read_css(CSS_PILL_BUTTON)
    assert re.search(r"min-height\s*:\s*44px", css), (
        "pill-button.css NE sadrži `min-height: 44px` (WCAG 2.5.5/2.5.8 touch target). "
        "IMP-12."
    )


# AC-4 + IMP-17: SVG path fill je var(--color-brand-green-800) (FOUC fallback)
def test_wave_divider_path_uses_token_fill():
    """AC4 + IMP-17: wave_divider.html SOURCE sadrži `fill="var(--color-brand-green-800)"`.

    Source check (NE samo rendered) — sprečava FOUC gde bi currentColor
    pre nego što CSS učita rezolvovao u default browser color (crno).
    """
    source = _read_partial(PARTIAL_WAVE_DIVIDER)
    assert 'fill="var(--color-brand-green-800)"' in source, (
        "wave_divider.html SOURCE NE sadrži `fill=\"var(--color-brand-green-800)\"` "
        "na SVG path-u. AC4 + IMP-17 FOUC fallback."
    )


# =============================================================================
# Integration / load-order tests (IMP-D2, Strategy A)
# =============================================================================


# IMP-D2: base.html load order — tokens.css < bootstrap_css < main.css
def test_base_html_css_load_order():
    """IMP-D2: u templates/base.html, tokens.css MORA biti pre `{% bootstrap_css %}` i pre main.css.

    Unconditional regression guard koji radi nezavisno od Strategy A/B.
    """
    if not BASE_HTML.exists():
        pytest.fail("templates/base.html ne postoji (Story 1.6 regression).")
    src = BASE_HTML.read_text(encoding="utf-8")
    tokens_idx = src.find("css/tokens.css")
    bootstrap_idx = src.find("{% bootstrap_css %}")
    main_idx = src.find("css/main.css")
    assert tokens_idx != -1, "base.html ne sadrži tokens.css link (Story 1.5 regression)."
    assert bootstrap_idx != -1, (
        "base.html ne sadrži `{% bootstrap_css %}` tag (Story 1.6 regression). "
        "IMP-D2 — Dev mora koristiti `bootstrap_css` token (NE plain `bootstrap`)."
    )
    assert main_idx != -1, "base.html ne sadrži main.css link (Story 1.6 regression)."
    assert tokens_idx < bootstrap_idx, (
        f"tokens.css (idx={tokens_idx}) NIJE PRE `{{% bootstrap_css %}}` (idx={bootstrap_idx}). "
        f"IMP-D2 — Story 1.7 NE sme razbiti Story 1.5/1.6 cascade."
    )
    assert bootstrap_idx < main_idx, (
        f"`{{% bootstrap_css %}}` (idx={bootstrap_idx}) NIJE PRE main.css (idx={main_idx}). "
        f"IMP-D2 — main.css mora doći POSLE Bootstrap-a (overrides)."
    )


# AC-8: Strategy A — main.css mora imati 5 Story 1.7 @import url('./components/...') direktiva
def test_main_css_imports_all_5_components():
    """AC8 (Strategy A — D1 default): main.css sadrži 5 Story 1.7 component @import linija.

    Mandatory relative-with-dot syntax `./components/...` (IMP-7) — sprečava Whitenoise/Manifest
    edge cases. Ako Dev izabere Strategy B, ovaj test mora biti adapted (vidi interface contract § 9).

    Updated for Story 1.8 (TEST_MODIFICATION GREEN-phase): Story 1.8 adds 3 more
    @import lines (header.css, footer.css, sticky-nav.css) — total 8 imports expected.
    Assertion changed from `== 5` to `>= 5` and explicitly checks each Story 1.7
    component is present (positional invariant preserved). Story 1.8 separate test in
    tests/test_navigation_chrome.py verifies the 3 Story 1.8 imports.
    """
    if not MAIN_CSS.exists():
        pytest.fail("static/css/main.css ne postoji (Story 1.6 regression).")
    css = MAIN_CSS.read_text(encoding="utf-8")
    pattern = r"@import\s+url\(\s*['\"]\./components/[a-z-]+\.css['\"]\s*\)"
    matches = re.findall(pattern, css)
    assert len(matches) >= 5, (
        f"main.css ima {len(matches)} `@import url('./components/...')` direktiva, očekivano >= 5. "
        f"AC8 Strategy A + IMP-7 — relative-with-dot syntax MANDATORY. "
        f"Pronađeni: {matches}"
    )
    # Story 1.7 invariant — each of 5 canonical components must be present.
    for name in (
        "repeating-element.css",
        "pill-button.css",
        "wave-divider.css",
        "section-eyebrow.css",
        "hero-overlay-card.css",
    ):
        component_pattern = rf"@import\s+url\(\s*['\"]\./components/{re.escape(name)}['\"]\s*\)"
        assert re.search(component_pattern, css), (
            f"main.css NE sadrži `@import url('./components/{name}')`. "
            f"Story 1.7 component invariant — must persist post-Story 1.8 expansion."
        )


# AC-7 (template check): nijedan inline `style="..."` u novim partial-ima
def test_no_inline_style_attribute_in_partials():
    """AC7 (template check): nijedan novi partial NE SME sadržati inline `style="..."`.

    Sve preko klasa + tokens. NE testira language_switcher.html (Story 1.4 — orthogonal).
    """
    offending = []
    for partial_path in ALL_NEW_PARTIALS:
        src = _read_partial(partial_path)
        # Pattern: style=" ili style=' (inline atribut)
        if re.search(r'\bstyle\s*=\s*["\']', src):
            offending.append(partial_path.name)
    assert not offending, (
        f"Inline `style=\"...\"` pronađen u sledećim partial-ima: {offending}. "
        f"AC7 — sve preko klasa + tokens."
    )


# =============================================================================
# DEFERRED tests (vendor blocker — vidi AC9.10)
# =============================================================================


@pytest.mark.skip(
    reason=(
        "DEFERRED until Story 1.6 vendor sourceMappingURL cleanup adds missing "
        "bootstrap.min.css.map OR Story 1.9 CI prep overrides STORAGES with "
        "manifest_strict=False — see Story 1.7 AC9.10 deferral note. "
        "Whitenoise CompressedManifestStaticFilesStorage post-processing fails on "
        "missing .map regardless of --ignore flag; --dry-run gives false positive "
        "per Django storage.py line 286."
    )
)
def test_collectstatic_rewrites_import_paths_to_hashed():
    """DEFERRED: collectstatic hash-rewrite verifikacija za Strategy A @import paths.

    Aspirational test scaffold — kad re-enable se desi (Story 1.6 vendor cleanup ili
    Story 1.9 CI prep), test postavlja DJANGO_SETTINGS_MODULE='config.settings.production'
    + DJANGO_SECRET_KEY='x' pre call_command('collectstatic', interactive=False),
    zatim grep `staticfiles/css/main.*.css` za @import paths sa hash-ima.

    Test MORA force-ovati production settings module jer dev settings koristi plain
    StaticFilesStorage (bez hash-a) — pod dev-om assertion je structurally nemoguć.
    """
    pytest.fail(
        "Test je @pytest.mark.skip — ne bi smeo biti pozvan. "
        "Ako vidiš ovu poruku, deferral decorator je uklonjen prematurno."
    )
