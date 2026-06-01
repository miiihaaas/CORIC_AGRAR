"""Story 3.3 — AC7: contact-page.css prisutnost + @import u main.css + coric- BEM +
var(--token) (NEMA magic hex).

RED phase (TEA). Statički pregled fajlova (NEMA DB, NEMA render). Fajlovi NE postoje
još (Dev GREEN ih kreira) -> testovi padaju na missing-file / missing-@import.

KOLOKOVANO uz app (apps/pages/tests/), mirror Story 3-2 test_about_page_css.py —
project-context.md § Test organization: unit testovi u apps/<app>/tests/, NE root tests/.

NAPOMENA (AC7 — layout vrednosti dozvoljene): mapa wrapper koristi aspect-ratio (npr.
16 / 9) i layout dimenzije (px/%/vh/fr) bez token-a — to su layout vrednosti, ne boje.
Token-test zabranjuje SAMO magic hex boje van whitelist-a (mirror Story 3-2 AC8 toleranca).
url() je isključen iz class-prefix skeniranja (mapa je iframe, NE CSS bg).

AC7 — 3 testa:
- test_contact_page_css_imported_in_main_css
- test_contact_page_css_uses_only_var_tokens
- test_contact_page_css_has_coric_prefix_on_all_classes

Pokrenuti:
    just test apps/pages/tests/test_contact_page_css.py -v
"""

from __future__ import annotations

import re
from pathlib import Path

from django.conf import settings

_PROJECT_ROOT = Path(settings.BASE_DIR)
_CONTACT_CSS = _PROJECT_ROOT / "static" / "css" / "components" / "contact-page.css"
_MAIN_CSS = _PROJECT_ROOT / "static" / "css" / "main.css"


def test_contact_page_css_imported_in_main_css():
    """AC7: main.css ima @import za components/contact-page.css (POSLE about-page.css)."""
    assert _MAIN_CSS.exists(), f"main.css mora postojati: {_MAIN_CSS}"
    content = _MAIN_CSS.read_text(encoding="utf-8")
    assert re.search(
        r"@import\s+url\(['\"]\./components/contact-page\.css['\"]\)", content
    ), "main.css MORA imati @import url('./components/contact-page.css'); (AC7)."


def test_contact_page_css_uses_only_var_tokens():
    """AC7: contact-page.css NEMA magic hex boja — sve kroz var(--token).

    Whitelist: dozvoljeni su #fff/#000 (+8-cifrene varijante) + transparent/none
    (mirror Story 3-2 AC8 toleranca). Hex-ovi van whitelist-a su zabranjeni.
    """
    assert _CONTACT_CSS.exists(), (
        f"contact-page.css MORA postojati (Dev GREEN deliverable): {_CONTACT_CSS}"
    )
    content = _CONTACT_CSS.read_text(encoding="utf-8")
    no_comments = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)
    hexes = re.findall(r"#[0-9a-fA-F]{3,8}\b", no_comments)
    allowed = {"#fff", "#ffffff", "#000", "#000000"}
    bad = [h for h in hexes if h.lower() not in allowed]
    assert not bad, (
        "contact-page.css NE SME imati magic hex boje van whitelist-a (sve kroz var(--token)). "
        f"Pronađeno: {bad!r}"
    )


def test_contact_page_css_has_coric_prefix_on_all_classes():
    """AC7: svi class selektori u contact-page.css imaju coric- prefiks (BEM konvencija).

    Reuse Story 3-1/3-2 token-test class-selektor regex. Defensive: uklanjamo url(...)
    sadržaj pre skeniranja (mapa je iframe, NE CSS bg — sprečava lažni .png/.jpg
    false-positive ako ipak postoji url()).
    """
    assert _CONTACT_CSS.exists(), (
        f"contact-page.css MORA postojati (Dev GREEN deliverable): {_CONTACT_CSS}"
    )
    content = _CONTACT_CSS.read_text(encoding="utf-8")
    no_comments = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)
    no_urls = re.sub(r"url\([^)]*\)", "", no_comments, flags=re.IGNORECASE)
    class_names = set(re.findall(r"\.(-?[A-Za-z_][\w-]*)", no_urls))
    non_coric = sorted(c for c in class_names if not c.startswith("coric-"))
    assert not non_coric, (
        "Svi class selektori u contact-page.css MORAJU imati 'coric-' prefiks (BEM). "
        f"Bez prefiksa: {non_coric!r}"
    )
