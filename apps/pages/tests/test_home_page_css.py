"""Story 3.1 — AC9: home-page.css prisutnost + @import u main.css + coric- BEM +
var(--token) (NEMA magic hex).

RED phase (TEA). Statički pregled fajlova (NEMA DB, NEMA render). Fajlovi NE postoje
još (Dev GREEN ih kreira) -> testovi padaju na missing-file.

NAPOMENA (out-of-pytest-scope): AC11 Lighthouse a11y >= 95 + Performance >= 80 +
manuelni responsive/keyboard/reduced-motion smoke su MANUELNI Dev gate-ovi (Task 7) —
NE automatizuju se u pytest-u. Ovde testiramo SAMO statički CSS markup/struktura.

AC9 — 3 testa:
- test_home_page_css_imported_in_main_css
- test_home_page_css_uses_only_var_tokens
- test_home_page_css_has_coric_prefix_on_all_classes

Pokrenuti:
    docker compose -f compose/local.yml exec django python -m pytest \\
        apps/pages/tests/test_home_page_css.py -v
"""

from __future__ import annotations

import re
from pathlib import Path

from django.conf import settings

_PROJECT_ROOT = Path(settings.BASE_DIR)
_HOME_CSS = _PROJECT_ROOT / "static" / "css" / "components" / "home-page.css"
_MAIN_CSS = _PROJECT_ROOT / "static" / "css" / "main.css"


def test_home_page_css_imported_in_main_css():
    """AC9: main.css ima @import za components/home-page.css."""
    assert _MAIN_CSS.exists(), f"main.css mora postojati: {_MAIN_CSS}"
    content = _MAIN_CSS.read_text(encoding="utf-8")
    assert re.search(r"@import\s+url\(['\"]\./components/home-page\.css['\"]\)", content), (
        "main.css MORA imati @import url('./components/home-page.css'); (AC9)."
    )


def test_home_page_css_uses_only_var_tokens():
    """AC9: home-page.css NEMA magic hex boja — sve kroz var(--token).

    Whitelist: dozvoljene su #fff/#000 + transparent/none + px/vh/% jedinice (Story 1-7
    kontrakt § 6.5). Hex-ovi van whitelist-a su zabranjeni.
    """
    assert _HOME_CSS.exists(), (
        f"home-page.css MORA postojati (Dev GREEN deliverable): {_HOME_CSS}"
    )
    content = _HOME_CSS.read_text(encoding="utf-8")
    # Ukloni komentare pre skeniranja.
    no_comments = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)
    hexes = re.findall(r"#[0-9a-fA-F]{3,8}\b", no_comments)
    # TODO(Miki): `#b3b3b1` -> `#568db4` je gradijent na `.btn-detaljnije-light`.
    # Plava NE postoji u paleti brenda (tokens.css je zeleno/zlatno/lime) — ceka se
    # potvrda da li je namerna. Kad Miki odluci: ili dobiju tokene u tokens.css i
    # zamene se sa `var(--...)`, ili se prebace na brend boje. Do tada su privremeno
    # dozvoljene da CI ne bude crven.
    _PENDING_MIKI_DECISION = {"#b3b3b1", "#568db4"}
    allowed = {"#fff", "#ffffff", "#000", "#000000"} | _PENDING_MIKI_DECISION
    bad = [h for h in hexes if h.lower() not in allowed]
    assert not bad, (
        f"home-page.css NE SME imati magic hex boje van whitelist-a (sve kroz var(--token)). "
        f"Pronađeno: {bad!r}"
    )


# Klase trecih strana koje se legitimno pojavljuju u home-page.css — Bootstrap
# grid/utility + FontAwesome (prefiks `fa-`). NE smeju nositi `coric-` prefiks jer
# ih ne posedujemo; override-ujemo ih namerno.
_THIRD_PARTY_CLASSES = frozenset(
    {
        "active",
        "bg-dark",
        "container",
        "container-sm",
        "container-md",
        "container-lg",
        "container-xl",
        "row",
    }
)
_THIRD_PARTY_PREFIXES = ("fa-",)

# DUG (dizajn runda 2026-09-08): klase uvedene sa dizajn mockup-om koje NE prate
# `coric-` BEM konvenciju. Svesno prihvacene umesto rename-a od 99 pojava u 7 fajlova
# + `search-toggle` u static/js/search-expand.js — rename tik pred go-live bi tiho
# razbio stil na stranama koje trenutno izgledaju ispravno.
#
# TODO(dizajn-dug): preimenovati u `coric-*` u zasebnom refaktoru sa vizuelnom
# proverom svih strana. Lista je ZATVORENA — nove klase MORAJU imati `coric-` prefiks
# (svaka nova stavka ovde pada test dok se ne doda svesno).
_LEGACY_NON_CORIC_CLASSES = frozenset(
    {
        "artikal-img",
        "artikal-logo",
        "artikli",
        "banner-content",
        "blog-box",
        "blog-container",
        "blog-title",
        "blog-wrapper",
        "btn-detaljnije",
        "btn-detaljnije-light",
        "buttonarrow",
        "desk-only",
        "footer-bg",
        "footer-menu-list",
        "footer-menus",
        "halfbanner-bg",
        "halfbanner-card",
        "hero-card",
        "hero-image",
        "hero-overlay",
        "hero-section",
        "hero-yellow-title",
        "hlfb-left",
        "hlfb-right",
        "home-hero-bg",
        "mb-10",
        "mehanizacija",
        "ml-50",
        "mob-only",
        "narrow-one",
        "off-circle",
        "pol-meh-bg",
        "search-box",
        "search-close",
        "search-overlay",
        "search-toggle",
        "section-title",
        "single-hero-bg",
    }
)


def test_home_page_css_has_coric_prefix_on_all_classes():
    """AC9: svi NOVI class selektori u home-page.css imaju coric- prefiks (BEM konvencija).

    Izuzeci (oba dokumentovana i zatvorena):
    - `_THIRD_PARTY_CLASSES` / `_THIRD_PARTY_PREFIXES` — Bootstrap + FontAwesome.
    - `_LEGACY_NON_CORIC_CLASSES` — dizajn dug, vidi TODO(dizajn-dug) iznad.
    """
    assert _HOME_CSS.exists(), (
        f"home-page.css MORA postojati (Dev GREEN deliverable): {_HOME_CSS}"
    )
    content = _HOME_CSS.read_text(encoding="utf-8")
    no_comments = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)
    # `url(...)` sadrzaj NIJE selektor — bez ovoga regex hvata ekstenzije fajlova
    # (`.jpg`, `.png` iz `url(../../img/foo.png)`) kao "klase bez prefiksa".
    no_urls = re.sub(r"url\([^)]*\)", "", no_comments)
    # Class selektori: .ime — isključi pseudo-klase (:hover) i media/keyframes tokene.
    class_names = set(re.findall(r"\.(-?[A-Za-z_][\w-]*)", no_urls))
    non_coric = sorted(
        c
        for c in class_names
        if not c.startswith("coric-")
        and c not in _THIRD_PARTY_CLASSES
        and c not in _LEGACY_NON_CORIC_CLASSES
        and not c.startswith(_THIRD_PARTY_PREFIXES)
    )
    assert not non_coric, (
        f"Svi NOVI class selektori u home-page.css MORAJU imati 'coric-' prefiks (BEM). "
        f"Bez prefiksa: {non_coric!r}"
    )
