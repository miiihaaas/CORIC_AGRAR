"""Story 3.2 — AC8: about-page.css prisutnost + @import u main.css + coric- BEM +
var(--token) (NEMA magic hex).

RED phase (TEA). Statički pregled fajlova (NEMA DB, NEMA render). Fajlovi NE postoje
još (Dev GREEN ih kreira) -> testovi padaju na missing-file / missing-@import.

KOLOKOVANO uz app (apps/pages/tests/), mirror Story 3-1 test_home_page_css.py —
project-context.md § Test organization: unit testovi u apps/<app>/tests/, NE root tests/.

NAPOMENA (AC8 — url() isključenje): watermark logo + hero foto-pozadina su <img>
elementi (NE CSS background-image: url(...)), pa about-page.css NEMA url() i token-test
class-selektor regex ne hvata .png/.jpg kao lažne class selektore. Defensive:
ako Dev ipak ubaci url(...), uklanjamo url(...) sadržaj pre class-prefix skeniranja
(mirror namera AC8) da test ne bi davao buggy non-coric false-positive na imenu fajla.

AC8 — 4 testa:
- test_about_page_css_imported_in_main_css
- test_about_page_css_uses_only_var_tokens
- test_about_page_css_has_coric_prefix_on_all_classes
- test_about_timeline_hidden_state_gated_by_coric_js_marker  (AC6 NO-JS fallback)

Pokrenuti:
    just test apps/pages/tests/test_about_page_css.py -v
"""

from __future__ import annotations

import re
from pathlib import Path

from django.conf import settings

_PROJECT_ROOT = Path(settings.BASE_DIR)
_ABOUT_CSS = _PROJECT_ROOT / "static" / "css" / "components" / "about-page.css"
_MAIN_CSS = _PROJECT_ROOT / "static" / "css" / "main.css"


def test_about_page_css_imported_in_main_css():
    """AC8: main.css ima @import za components/about-page.css."""
    assert _MAIN_CSS.exists(), f"main.css mora postojati: {_MAIN_CSS}"
    content = _MAIN_CSS.read_text(encoding="utf-8")
    assert re.search(
        r"@import\s+url\(['\"]\./components/about-page\.css['\"]\)", content
    ), "main.css MORA imati @import url('./components/about-page.css'); (AC8)."


def test_about_page_css_uses_only_var_tokens():
    """AC8: about-page.css NEMA magic hex boja — sve kroz var(--token).

    Whitelist: dozvoljeni su #fff/#000 + transparent/none (mirror Story 3-1 AC9 toleranca).
    Hex-ovi van whitelist-a su zabranjeni.
    """
    assert _ABOUT_CSS.exists(), (
        f"about-page.css MORA postojati (Dev GREEN deliverable): {_ABOUT_CSS}"
    )
    content = _ABOUT_CSS.read_text(encoding="utf-8")
    no_comments = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)
    hexes = re.findall(r"#[0-9a-fA-F]{3,8}\b", no_comments)
    allowed = {"#fff", "#ffffff", "#000", "#000000"}
    bad = [h for h in hexes if h.lower() not in allowed]
    assert not bad, (
        "about-page.css NE SME imati magic hex boje van whitelist-a (sve kroz var(--token)). "
        f"Pronađeno: {bad!r}"
    )


def test_about_page_css_has_coric_prefix_on_all_classes():
    """AC8: svi class selektori u about-page.css imaju coric- prefiks (BEM konvencija).

    Reuse Story 3-1 token-test class-selektor regex. Defensive: uklanjamo
    url(...) sadržaj pre skeniranja (AC8 url() isključenje) — watermark/hero su <img>,
    pa CSS ne sme imati url(); ovo sprečava lažni .png/.jpg false-positive ako ipak
    postoji bg-url.
    """
    assert _ABOUT_CSS.exists(), (
        f"about-page.css MORA postojati (Dev GREEN deliverable): {_ABOUT_CSS}"
    )
    content = _ABOUT_CSS.read_text(encoding="utf-8")
    no_comments = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)
    # AC8: isključi url(...) sadržaj iz class-prefix skeniranja.
    no_urls = re.sub(r"url\([^)]*\)", "", no_comments, flags=re.IGNORECASE)
    class_names = set(re.findall(r"\.(-?[A-Za-z_][\w-]*)", no_urls))
    non_coric = sorted(c for c in class_names if not c.startswith("coric-"))
    assert not non_coric, (
        "Svi class selektori u about-page.css MORAJU imati 'coric-' prefiks (BEM). "
        f"Bez prefiksa: {non_coric!r}"
    )


def test_about_timeline_hidden_state_gated_by_coric_js_marker():
    """AC6/AC8 NO-JS fallback: timeline segment hidden stanje (opacity:0) MORA biti
    gejtovano `.coric-js` markerom — NE bezuslovno na bare segmentu.

    Lock (AC6 NO-JS fallback + AC8 + contract:169,186): bez JS-a (modul se ne učita /
    observer nikad ne okine) segmenti MORAJU ostati VIDLJIVI (graceful degradation,
    mirror statistic-counter). Zato `opacity:0` na timeline segmentu sme postojati SAMO
    pod `.coric-js` prefiksom (`timeline-reveal.js` dodaje marker na init); bezuslovno
    skrivanje segmenta (`.coric-about-timeline__segment { opacity:0 }`) je BUG —
    sadržaj bi nestao bez JS-a.
    """
    assert _ABOUT_CSS.exists(), (
        f"about-page.css MORA postojati (Dev GREEN deliverable): {_ABOUT_CSS}"
    )
    content = _ABOUT_CSS.read_text(encoding="utf-8")
    no_comments = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)

    # Pronađi sva pravila koja skrivaju timeline segment (opacity: 0 u istom rule bloku
    # sa segment selektorom). Svako takvo pravilo MORA biti gejtovano `.coric-js`.
    rule_re = re.compile(r"([^{}]*\bcoric-about-timeline__segment\b[^{}]*)\{([^{}]*)\}", re.IGNORECASE)
    rules = rule_re.findall(no_comments)
    assert rules, (
        "about-page.css MORA stilizovati `.coric-about-timeline__segment` (reveal stanje). "
        "Nijedno pravilo za timeline segment nije pronađeno."
    )

    hidden_rules = [
        (sel, body) for sel, body in rules
        if re.search(r"opacity\s*:\s*0(?:\.0+)?\s*(?:;|$|\})", body, re.IGNORECASE)
    ]
    assert hidden_rules, (
        "about-page.css MORA imati hidden stanje (opacity:0) za timeline segment "
        "(reveal-from-hidden — AC6)."
    )
    for sel, _body in hidden_rules:
        assert "coric-js" in sel.lower(), (
            "Timeline segment hidden stanje (opacity:0) MORA biti gejtovano `.coric-js` "
            "markerom (NO-JS fallback — bez JS-a segmenti vidljivi; AC6/contract:186). "
            f"Bezuslovno skrivanje je BUG. Selektor: {sel.strip()!r}"
        )
