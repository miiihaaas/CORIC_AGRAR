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
    allowed = {"#fff", "#ffffff", "#000", "#000000"}
    bad = [h for h in hexes if h.lower() not in allowed]
    assert not bad, (
        f"home-page.css NE SME imati magic hex boje van whitelist-a (sve kroz var(--token)). "
        f"Pronađeno: {bad!r}"
    )


def test_home_page_css_has_coric_prefix_on_all_classes():
    """AC9: svi class selektori u home-page.css imaju coric- prefiks (BEM konvencija)."""
    assert _HOME_CSS.exists(), (
        f"home-page.css MORA postojati (Dev GREEN deliverable): {_HOME_CSS}"
    )
    content = _HOME_CSS.read_text(encoding="utf-8")
    no_comments = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)
    # Class selektori: .ime — isključi pseudo-klase (:hover) i media/keyframes tokene.
    class_names = set(re.findall(r"\.(-?[A-Za-z_][\w-]*)", no_comments))
    non_coric = sorted(c for c in class_names if not c.startswith("coric-"))
    assert not non_coric, (
        f"Svi class selektori u home-page.css MORAJU imati 'coric-' prefiks (BEM). "
        f"Bez prefiksa: {non_coric!r}"
    )
