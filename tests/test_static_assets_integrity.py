"""Integritet static asset-a — svaka `url()` referenca u CSS-u mora da postoji.

MOTIVACIJA (2026-09-08, prod incident): PR #1 je vendorovao FontAwesome 6.7.2 sa
`css/all.min.css` koji referencira i `.ttf` i `.woff2`, ali su commit-ovani SAMO
`.woff2` fajlovi (VERSION.txt to i kaze: "webfonts/*.woff2 only (ttf omitted)").

Lokalni dev to NE vidi: development.py koristi plain StaticFilesStorage koji ne
prolazi kroz CSS i ne razresava `url()`. Produkcija koristi Whitenoise
CompressedManifestStaticFilesStorage, koji post-procesira SVAKI `url()` i puca sa
`MissingFileError` -> `collectstatic` pada -> deploy staje.

Rezultat: bug nevidljiv i lokalno i u CI-ju, a obara produkcioni deploy. Ovaj test
hvata tacno tu klasu greske staticki, bez pokretanja collectstatic-a.
"""

from __future__ import annotations

import re
from pathlib import Path

from django.conf import settings

_STATIC_DIR = Path(settings.BASE_DIR) / "static"

# `url()` vrednosti koje NE pokazuju na fajl na disku.
_NON_FILE_PREFIXES = ("data:", "http:", "https:", "//", "#")

_URL_RE = re.compile(r"url\(\s*([^)]+?)\s*\)")


def _iter_css_url_refs():
    """Yield-uje (css_path, ref) za svaki `url(...)` u svakom static CSS fajlu."""
    for css_path in sorted(_STATIC_DIR.rglob("*.css")):
        text = css_path.read_text(encoding="utf-8", errors="ignore")
        for raw in _URL_RE.findall(text):
            yield css_path, raw.strip("'\"")


def test_every_css_url_reference_resolves_to_existing_file():
    """Svaki `url()` u static CSS-u mora da pokazuje na postojeci fajl.

    Ista provera koju Whitenoise manifest storage radi u `collectstatic` tokom
    deploy-a — samo sto ovde pada u CI-ju, a ne na produkcionom boxu.
    """
    missing = []
    for css_path, ref in _iter_css_url_refs():
        if ref.startswith(_NON_FILE_PREFIXES):
            continue
        # Odbaci query string i fragment (`?v=1`, `#iefix`) pre resolve-a.
        rel = ref.split("?")[0].split("#")[0]
        if not rel:
            continue
        if not (css_path.parent / rel).resolve().exists():
            missing.append(f"{css_path.relative_to(_STATIC_DIR)} -> {ref}")

    assert not missing, (
        "CSS referencira fajlove kojih NEMA u static/ — produkcioni `collectstatic` "
        "(Whitenoise manifest) ce pasti sa MissingFileError i oboriti deploy. "
        "Pokvarene reference:\n  " + "\n  ".join(missing)
    )
