"""Tests za Story 1.5 - Self-hosted Roboto + DESIGN.md tokens kao CSS Custom Properties.

Verifikuje:
- AC1: static/ folder hijerarhija (static/, static/css/, static/fonts/, static/fonts/roboto/)
- AC2: 6 Roboto woff2 fajlova sa kanonskim imenima + ukupan size < 300 KB + magic bytes
- AC3: static/css/tokens.css — 6 @font-face deklaracija (3 latin + 3 latin-ext),
       font-display: swap, font-family: 'Roboto', unicode-range
- AC4: 21 color tokena u :root sa lowercase 6-digit hex vrednostima
- AC5: 42 typography/rounded/shadow/spacing tokena (total 63 custom properties)
- AC6: Django integracija — pyproject.toml whitenoise dep, base.py STATIC_URL leading slash,
       STATICFILES_DIRS, STATIC_ROOT, STORAGES dict, WhiteNoiseMiddleware position,
       env-specific STORAGES override (development plain, staging/production manifest)
- AC7: templates/base.html — {% load static %} direktiva + tokens.css link PRE block extra_head
- AC8: Smoke validacija — manage.py check, collectstatic --dry-run, Django Client GET
       /static/css/tokens.css, /sr/ HTML render
- Anti-pattern guards: nema googleapis.com / gstatic.com / preconnect-a, nema uppercase hex-a

Pokrenuti sa:
    uv run pytest tests/test_static_tokens.py -v --tb=short

TEA RED faza: svi testovi MORAJU pasti (ili biti skip-ovani sa porukom za missing woff2)
dok Dev ne zavrsi Story 1.5. Naming convention: srpska latinica + engleski; bez cirilice.
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
SETTINGS_STAGING = SETTINGS_PKG_DIR / "staging.py"
SETTINGS_PROD = SETTINGS_PKG_DIR / "production.py"

PYPROJECT_PATH = PROJECT_ROOT / "pyproject.toml"
MANAGE_PY = PROJECT_ROOT / "manage.py"

STATIC_DIR = PROJECT_ROOT / "static"
STATIC_CSS_DIR = STATIC_DIR / "css"
STATIC_FONTS_DIR = STATIC_DIR / "fonts"
STATIC_FONTS_ROBOTO_DIR = STATIC_FONTS_DIR / "roboto"
TOKENS_CSS = STATIC_CSS_DIR / "tokens.css"

TEMPLATES_DIR = PROJECT_ROOT / "templates"
BASE_HTML = TEMPLATES_DIR / "base.html"

# Očekivanih 6 woff2 fajlova (kanonsko ime)
EXPECTED_WOFF2_FILES = [
    "roboto-latin-300.woff2",
    "roboto-latin-400.woff2",
    "roboto-latin-700.woff2",
    "roboto-latin-ext-300.woff2",
    "roboto-latin-ext-400.woff2",
    "roboto-latin-ext-700.woff2",
]

TEST_SECRET = "test-secret-key-for-tea-story-1-5-static-tokens-not-real"

# Poruka za graceful skip kad Mihas nije preuzeo woff2 fajlove
WOFF2_MISSING_MSG = (
    "Mihas mora ručno preuzeti woff2 fajlove pre Dev start-a "
    "(vidi Story 1.5 Task 3.1 — gwfh.mranftl.com Roboto download)."
)


# =============================================================================
# Helper funkcije
# =============================================================================


def _read_file(path: Path) -> str:
    """Procita fajl sa utf-8 encoding-om. Fail-uje ako ne postoji."""
    if not path.exists():
        pytest.fail(f"Fajl ne postoji na {path}")
    return path.read_text(encoding="utf-8")


def _read_file_bytes(path: Path) -> bytes:
    """Procita fajl kao bytes (za magic bytes provere)."""
    if not path.exists():
        pytest.fail(f"Fajl ne postoji na {path}")
    return path.read_bytes()


def _read_base_source() -> str:
    """Procita config/settings/base.py."""
    if not SETTINGS_BASE.exists():
        pytest.fail(f"config/settings/base.py ne postoji na {SETTINGS_BASE}")
    return SETTINGS_BASE.read_text(encoding="utf-8")


def _read_tokens_css() -> str:
    """Procita static/css/tokens.css. Fail-uje ako ne postoji."""
    if not TOKENS_CSS.exists():
        pytest.fail(
            f"static/css/tokens.css ne postoji na {TOKENS_CSS}. "
            f"Dev mora kreirati po Story 1.5 Dev Notes § tokens.css Template."
        )
    return TOKENS_CSS.read_text(encoding="utf-8")


def _woff2_files_present() -> bool:
    """True ako svih 6 očekivanih woff2 fajlova postoje u static/fonts/roboto/."""
    if not STATIC_FONTS_ROBOTO_DIR.exists():
        return False
    return all(
        (STATIC_FONTS_ROBOTO_DIR / fname).exists() for fname in EXPECTED_WOFF2_FILES
    )


def _load_settings_module(module_name: str):
    """Importuje config.settings.<module_name> sa DJANGO_SECRET_KEY + fresh reload."""
    os.environ.setdefault("DJANGO_SECRET_KEY", TEST_SECRET)
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    full_name = f"config.settings.{module_name}"
    for mod_key in list(sys.modules.keys()):
        if (
            mod_key == full_name
            or mod_key.startswith(f"{full_name}.")
            or mod_key.startswith("config.settings.")
        ):
            del sys.modules[mod_key]
    try:
        return importlib.import_module(full_name)
    except Exception as exc:
        pytest.fail(
            f"Import `config.settings.{module_name}` pukao: {type(exc).__name__}: {exc}. "
            f"Verovatno whitenoise paket nije instaliran (`uv add whitenoise>=6.8.0`) "
            f"ili settings fajl nije izmenjen po Story 1.5."
        )


def _load_pyproject() -> dict:
    """Load pyproject.toml kao dict."""
    if tomllib is None:
        pytest.skip("tomllib nije dostupan (Python < 3.11)")
    if not PYPROJECT_PATH.exists():
        pytest.fail(f"pyproject.toml ne postoji na {PYPROJECT_PATH}")
    with PYPROJECT_PATH.open("rb") as f:
        return tomllib.load(f)


def _run(
    cmd: list[str], env: dict[str, str] | None = None
) -> subprocess.CompletedProcess:
    """Subprocess wrapper. Inherits os.environ + optional override env."""
    full_env = os.environ.copy()
    if env:
        full_env.update(env)
    return subprocess.run(
        cmd,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        shell=False,
        timeout=120,
        env=full_env,
    )


# =============================================================================
# AC1 — static/ folder hijerarhija
# =============================================================================


def test_ac1_static_directory_exists():
    """AC1: static/ direktorijum mora postojati u repo root-u."""
    assert STATIC_DIR.exists(), (
        f"static/ direktorijum ne postoji na {STATIC_DIR}. "
        f"Story 1.5 Task 2 kreira ovu hijerarhiju."
    )
    assert STATIC_DIR.is_dir(), f"static/ postoji ali nije direktorijum: {STATIC_DIR}"


def test_ac1_static_subdirs_exist():
    """AC1: static/css/ i static/fonts/roboto/ moraju postojati."""
    missing = []
    for path in (STATIC_CSS_DIR, STATIC_FONTS_DIR, STATIC_FONTS_ROBOTO_DIR):
        if not path.exists() or not path.is_dir():
            missing.append(str(path.relative_to(PROJECT_ROOT)))
    assert not missing, (
        f"Sledeći static/ subdir-ovi ne postoje: {missing}. "
        f"Story 1.5 Task 2.1-2.4 ih kreira."
    )


def test_ac1_static_no_other_subdirs_yet():
    """AC1 / YAGNI: Story 1.5/1.6 forbids extra static/ subdirs.

    Updated for Story 1.8 (TEST_MODIFICATION GREEN-phase): Story 1.8 introduces
    `static/js/` (sticky-nav.js, AC1) and `static/img/` (Coric Agrar logo PNGs, Task 1.10).
    Both are explicit deliverables — the original YAGNI guard (forbidding js/ + img/)
    no longer applies. Story 1.5/1.6 invariant preserved as a passive comment.
    """
    if not STATIC_DIR.exists():
        pytest.skip(
            "static/ direktorijum ne postoji — drugi test (test_ac1_static_directory_exists) hvata."
        )
    # No subdirs are forbidden post-Story 1.8; static/{css,fonts,vendor,js,img}/ are all canonical.
    # Test retained as a regression sentinel — if a truly unexpected subdir appears, extend `forbidden`.
    forbidden: list[str] = []
    found = [name for name in forbidden if (STATIC_DIR / name).exists()]
    assert not found, f"static/ sadrži forbidden subdir-ove: {found}."


# =============================================================================
# AC2 — Roboto woff2 fajlovi
# =============================================================================


def test_ac2_six_woff2_files_present():
    """AC2: Tačno 6 woff2 fajlova u static/fonts/roboto/ sa kanonskim imenima.

    Skip ako Mihas još nije preuzeo (gwfh download je ručan korak).
    """
    if not STATIC_FONTS_ROBOTO_DIR.exists():
        pytest.skip(WOFF2_MISSING_MSG)
    woff2_files = sorted(STATIC_FONTS_ROBOTO_DIR.glob("*.woff2"))
    actual_names = sorted(f.name for f in woff2_files)
    expected = sorted(EXPECTED_WOFF2_FILES)

    if not woff2_files:
        pytest.skip(WOFF2_MISSING_MSG)

    assert actual_names == expected, (
        f"static/fonts/roboto/ ima {len(woff2_files)} woff2 fajlova, "
        f"očekivano tačno {len(expected)}.\n"
        f"  Pronađeno: {actual_names}\n"
        f"  Očekivano: {expected}\n"
        f"Story 1.5 AC2 + Task 3.1.8 specificira kanonska imena (bez 'vNN' prefix-a, "
        f"'regular' rename na '400')."
    )


def test_ac2_woff2_naming_convention():
    """AC2: woff2 filename-i moraju pratiti pattern `roboto-{latin|latin-ext}-{300|400|700}.woff2`."""
    if not STATIC_FONTS_ROBOTO_DIR.exists():
        pytest.skip(WOFF2_MISSING_MSG)
    woff2_files = list(STATIC_FONTS_ROBOTO_DIR.glob("*.woff2"))
    if not woff2_files:
        pytest.skip(WOFF2_MISSING_MSG)
    pattern = re.compile(r"^roboto-(latin|latin-ext)-(300|400|700)\.woff2$")
    bad = [f.name for f in woff2_files if not pattern.match(f.name)]
    assert not bad, (
        f"Sledeći woff2 fajlovi NE prate kanonski naming pattern: {bad}. "
        f"Pattern: `roboto-{{latin|latin-ext}}-{{300|400|700}}.woff2`. "
        f"Verovatno Mihas zaboravio rename ZIP-a (uklanjanje 'vNN' prefix-a + 'regular' → '400')."
    )


def test_ac2_woff2_total_size_under_300kb():
    """AC2: ukupna veličina svih 6 woff2 fajlova MORA biti < 300 KB (sanity).

    Ako je > 300 KB, subset je verovatno pogrešan (cyrillic/greek dodato slučajno).
    Lower bound > 50 KB — ako je manje, fajlovi su prazni ili korumpirani.
    """
    if not _woff2_files_present():
        pytest.skip(WOFF2_MISSING_MSG)
    total_bytes = sum(
        (STATIC_FONTS_ROBOTO_DIR / fname).stat().st_size
        for fname in EXPECTED_WOFF2_FILES
    )
    total_kb = total_bytes / 1024
    assert 50 < total_kb < 300, (
        f"Roboto woff2 ukupna veličina = {total_kb:.1f} KB. "
        f"Očekivano u opsegu (50, 300) KB.\n"
        f"  Ako > 300 KB: subset je pogrešan (verovatno cyrillic/greek uključen). "
        f"Ponovi gwfh download sa SAMO latin + latin-ext, weights 300/400/700, woff2 only.\n"
        f"  Ako < 50 KB: fajlovi su korumpirani ili prazni."
    )


def test_ac2_woff2_magic_bytes():
    """AC2: svaki woff2 fajl MORA početi sa `wOF2` magic bytes (`0x77 0x4F 0x46 0x32`)."""
    if not _woff2_files_present():
        pytest.skip(WOFF2_MISSING_MSG)
    bad = []
    for fname in EXPECTED_WOFF2_FILES:
        path = STATIC_FONTS_ROBOTO_DIR / fname
        head = path.read_bytes()[:4]
        if head != b"wOF2":
            bad.append((fname, head))
    assert not bad, (
        f"Sledeći fajlovi NEMAJU wOF2 magic bytes (nije validan woff2): {bad}. "
        f"Verovatno su woff (NE woff2) ili korumpirani. Re-download sa woff2 only."
    )


# =============================================================================
# AC3 — tokens.css @font-face deklaracije
# =============================================================================


def test_ac3_tokens_css_exists():
    """AC3: static/css/tokens.css mora postojati."""
    assert TOKENS_CSS.exists(), (
        f"static/css/tokens.css ne postoji na {TOKENS_CSS}. "
        f"Story 1.5 Task 4 kreira fajl po Dev Notes § tokens.css Template."
    )


def test_ac3_tokens_css_has_6_fontface_declarations():
    """AC3: tokens.css MORA imati tačno 6 `@font-face` deklaracija (3 latin + 3 latin-ext)."""
    content = _read_tokens_css()
    matches = re.findall(r"@font-face\s*\{", content)
    assert len(matches) == 6, (
        f"tokens.css ima {len(matches)} @font-face deklaracija, očekivano tačno 6 "
        f"(3 weights × 2 subsets = 6). Story 1.5 AC3 + Dev Notes Template."
    )


def test_ac3_tokens_css_has_font_display_swap():
    """AC3: `font-display: swap` MORA se pojaviti tačno 6 puta (po jednom za svaki @font-face).

    KRITIČNO: sprečava FOIT (Flash of Invisible Text). project-context.md § Performance.
    """
    content = _read_tokens_css()
    matches = re.findall(r"font-display\s*:\s*swap\b", content)
    assert len(matches) == 6, (
        f"tokens.css ima {len(matches)} `font-display: swap` deklaracija, "
        f"očekivano tačno 6 (jedna po @font-face). KRITIČNO: bez swap-a "
        f"dolazi do FOIT (Flash of Invisible Text)."
    )


def test_ac3_tokens_css_has_unicode_range_latin():
    """AC3: tokens.css MORA imati 3 latin `unicode-range` (sa `U+0000-00FF`)."""
    content = _read_tokens_css()
    matches = re.findall(r"U\+0000-00FF", content)
    assert len(matches) == 3, (
        f"tokens.css ima {len(matches)} `U+0000-00FF` matches, očekivano tačno 3 "
        f"(3 weight × 1 latin = 3 latin @font-face deklaracija)."
    )


def test_ac3_tokens_css_has_unicode_range_latin_ext():
    """AC3: tokens.css MORA imati 3 latin-ext `unicode-range` (sa `U+0100-024F`)."""
    content = _read_tokens_css()
    matches = re.findall(r"U\+0100-024F", content)
    assert len(matches) == 3, (
        f"tokens.css ima {len(matches)} `U+0100-024F` matches, očekivano tačno 3 "
        f"(3 weight × 1 latin-ext = 3 latin-ext @font-face deklaracija)."
    )


def test_ac3_tokens_css_font_family_roboto():
    """AC3: svaka @font-face MORA imati `font-family: 'Roboto'`."""
    content = _read_tokens_css()
    # Match: font-family: 'Roboto' (single ili double quotes; whitespace tolerant)
    matches = re.findall(r"font-family\s*:\s*['\"]Roboto['\"]", content)
    assert len(matches) >= 6, (
        f"tokens.css ima {len(matches)} `font-family: 'Roboto'` matches, "
        f"očekivano bar 6 (jedna po @font-face). Single quotes preferirane (Dev Notes Template)."
    )


def test_ac3_tokens_css_relative_font_src():
    """AC3 / Gotcha #4: src URL mora biti relativan `../fonts/roboto/...`.

    NE apsolutan (`/static/fonts/...`) — to lomi pri deploy na sub-path.
    """
    content = _read_tokens_css()
    # Mora imati 6 url('../fonts/roboto/...') matches
    matches = re.findall(r"url\s*\(\s*['\"]\.\./fonts/roboto/", content)
    assert len(matches) == 6, (
        f"tokens.css ima {len(matches)} `url('../fonts/roboto/...')` matches, "
        f"očekivano 6. Gotcha #4: NE apsolutan path, NE `fonts/roboto/...` bez `..`."
    )


# =============================================================================
# AC4 — Color tokeni (21)
# =============================================================================


def test_ac4_tokens_css_has_21_color_tokens():
    """AC4: tokens.css MORA imati tačno 21 `--color-*` custom properties.

    Brojanje: 4 brand-green + 2 accent + 1 brand-specific + 7 neutral + 7 semantic = 21.
    """
    content = _read_tokens_css()
    matches = re.findall(r"^\s*--color-[a-z0-9-]+\s*:", content, re.MULTILINE)
    assert len(matches) == 21, (
        f"tokens.css ima {len(matches)} `--color-*` custom properties, očekivano tačno 21. "
        f"Story 1.5 AC4: 4 brand + 2 accent + 1 brand-specific + 7 neutral + 7 semantic = 21."
    )


def test_ac4_tokens_css_specific_brand_colors():
    """AC4 acceptance signal: `--color-brand-green-800: #25402f` MORA postojati (lowercase hex)."""
    content = _read_tokens_css()
    expected_lines = [
        ("--color-brand-green-900", "#1f3f2f"),
        ("--color-brand-green-800", "#25402f"),
        ("--color-brand-green-600", "#395f48"),
        ("--color-brand-green-400", "#4d7e60"),
    ]
    missing = []
    for token, value in expected_lines:
        # Pattern: --token: value (whitespace + optional semicolon)
        pattern = rf"{re.escape(token)}\s*:\s*{re.escape(value)}\s*;"
        if not re.search(pattern, content):
            missing.append(f"{token}: {value}")
    assert not missing, (
        f"tokens.css nedostaju sledeći brand-green tokeni (exact match): {missing}. "
        f"Story 1.5 AC4 + Dev Notes Template."
    )


def test_ac4_tokens_css_jeegee_blue_lowercase():
    """AC4: `--color-jeegee-blue: #00a4e9` (lowercase hex — DESIGN.md ima `#00A4E9`,
    ali story AC4 mandate lowercase + 6-digit canonical).
    """
    content = _read_tokens_css()
    pattern = r"--color-jeegee-blue\s*:\s*#00a4e9\s*;"
    assert re.search(pattern, content), (
        "tokens.css NE sadrži `--color-jeegee-blue: #00a4e9;` (lowercase hex). "
        "DESIGN.md ima #00A4E9 (uppercase), ali Story 1.5 AC4 mandate lowercase: "
        "verifikuj `#00a4e9`, NE `#00A4E9`."
    )


def test_ac4_tokens_css_semantic_colors():
    """AC4: semantic color tokeni MORAJU biti prisutni (7 ukupno)."""
    content = _read_tokens_css()
    expected_tokens = [
        "--color-semantic-text-primary",
        "--color-semantic-text-on-dark",
        "--color-semantic-text-muted",
        "--color-semantic-border",
        "--color-semantic-error",
        "--color-semantic-success",
        "--color-semantic-focus-ring",
    ]
    missing = [
        t for t in expected_tokens if not re.search(rf"{re.escape(t)}\s*:", content)
    ]
    assert not missing, (
        f"tokens.css nedostaju semantic tokeni: {missing}. "
        f"AC4 zahteva svih 7 (text-primary, text-on-dark, text-muted, border, "
        f"error, success, focus-ring)."
    )


def test_ac4_no_uppercase_hex():
    """AC4 mandate: SVE hex vrednosti MORAJU biti lowercase 6-digit.

    Anti-pattern: `#25402F` (uppercase) ili `#fff` (3-digit shorthand). Regex hvata
    uppercase A-F slova u 6-digit hex (`#XXXXXX`) bilo gde u fajlu.
    """
    content = _read_tokens_css()
    # Match `#[0-9A-F]{6}` ali samo ako ima bar jedno uppercase A-F slovo
    matches = re.findall(r"#[0-9A-Fa-f]{6}", content)
    bad = [m for m in matches if any(c.isalpha() and c.isupper() for c in m[1:])]
    assert not bad, (
        f"tokens.css sadrži uppercase hex vrednosti: {bad}. "
        f"AC4 mandate: SVE hex vrednosti moraju biti lowercase 6-digit "
        f"(npr. `#25402f`, NE `#25402F`)."
    )


def test_ac4_no_3digit_shorthand_hex():
    """AC4 mandate: SVE hex vrednosti MORAJU biti 6-digit (NE 3-digit shorthand).

    Anti-pattern: `#fff` umesto `#ffffff` — story AC4 eksplicit: "lowercase + 6-digit
    (NE 3-digit shorthand poput `#fff` — eksplicitnost olakšava grep i text-diff)".
    Pattern detektuje `#XXX` koji NIJE deo dužeg 6-digit hex-a.
    """
    content = _read_tokens_css()
    # Match #XXX (tačno 3 hex char-a) ne praćeno drugim hex char-om (ne deo 6-digit-a)
    matches = re.findall(r"#[0-9A-Fa-f]{3}(?![0-9A-Fa-f])", content)
    assert not matches, (
        f"tokens.css sadrži 3-digit shorthand hex vrednosti: {matches}. "
        f"AC4 mandate: koristi 6-digit hex eksplicitno (npr. `#ffffff`, NE `#fff`). "
        f"Razlog: eksplicitnost olakšava grep i text-diff."
    )


# =============================================================================
# AC5 — Typography / rounded / shadow / spacing tokeni (42)
# =============================================================================


def test_ac5_typography_tokens_present():
    """AC5: typography family + weights + scale + line-height + tracking — sve grupe."""
    content = _read_tokens_css()
    expected_signals = [
        ("--typography-family-primary", r"'Roboto'.*system-ui.*sans-serif"),
        ("--typography-weight-light", r"\b300\b"),
        ("--typography-weight-regular", r"\b400\b"),
        ("--typography-weight-bold", r"\b700\b"),
        ("--typography-scale-h1", r"3\.5rem"),
        ("--typography-scale-h2", r"2\.5rem"),
        ("--typography-scale-body", r"1\.25rem"),
        ("--typography-line-height-base", r"1\.5"),
        ("--typography-tracking-wide", r"0\.05em"),
    ]
    missing = []
    for token, value_pattern in expected_signals:
        full = rf"{re.escape(token)}\s*:\s*[^;]*{value_pattern}"
        if not re.search(full, content):
            missing.append(f"{token} (value pattern: {value_pattern})")
    assert not missing, (
        f"tokens.css nedostaju typography tokeni / vrednosti: {missing}. "
        f"AC5 + Dev Notes Template."
    )


def test_ac5_rounded_tokens_present():
    """AC5: 6 rounded tokena (none/sm/md/lg/pill/full) + acceptance signal `--rounded-pill: 999px`."""
    content = _read_tokens_css()
    expected_signals = [
        ("--rounded-none", "0"),
        ("--rounded-sm", "6px"),
        ("--rounded-md", "8px"),
        ("--rounded-lg", "10px"),
        ("--rounded-pill", "999px"),
        ("--rounded-full", "50%"),
    ]
    missing = []
    for token, value in expected_signals:
        pattern = rf"{re.escape(token)}\s*:\s*{re.escape(value)}\s*;"
        if not re.search(pattern, content):
            missing.append(f"{token}: {value}")
    assert not missing, (
        f"tokens.css nedostaju rounded tokeni (exact match): {missing}. AC5 + Dev Notes Template."
    )


def test_ac5_shadow_tokens_present():
    """AC5: 5 shadow tokena + acceptance signal `--shadow-md: 0 2px 8px rgba(31, 63, 47, 0.06)`."""
    content = _read_tokens_css()
    # Verifikuj prisustvo svih 5 imena
    expected_names = [
        "--shadow-none",
        "--shadow-sm",
        "--shadow-md",
        "--shadow-lg",
        "--shadow-nav-shrunk",
    ]
    missing = [
        n for n in expected_names if not re.search(rf"{re.escape(n)}\s*:", content)
    ]
    assert not missing, f"tokens.css nedostaju shadow tokeni: {missing}. AC5."
    # Acceptance signal: shadow-md eksplicitno
    md_pattern = r"--shadow-md\s*:\s*0\s+2px\s+8px\s+rgba\(31,\s*63,\s*47,\s*0\.06\)"
    assert re.search(md_pattern, content), (
        "tokens.css NEMA `--shadow-md: 0 2px 8px rgba(31, 63, 47, 0.06)` (exact signal). "
        "AC5 acceptance kriterijum."
    )


def test_ac5_spacing_tokens_present():
    """AC5: spacing base + scale (10) + section (2) + container (3) = 15 spacing tokena."""
    content = _read_tokens_css()
    expected_signals = [
        ("--spacing-base", "4px"),
        ("--spacing-section", "80px"),
        ("--spacing-section-mobile", "48px"),
        ("--spacing-container-max-width", "1200px"),
        ("--spacing-container-gutter-desktop", "24px"),
        ("--spacing-container-gutter-mobile", "16px"),
    ]
    missing = []
    for token, value in expected_signals:
        pattern = rf"{re.escape(token)}\s*:\s*{re.escape(value)}\s*;"
        if not re.search(pattern, content):
            missing.append(f"{token}: {value}")
    assert not missing, (
        f"tokens.css nedostaju spacing tokeni (exact match): {missing}. AC5 + Dev Notes Template."
    )
    # Verifikuj prisustvo svih 9 scale stavki + base
    scale_names = [f"--spacing-scale-{i}" for i in (1, 2, 3, 4, 5, 6, 8, 10, 12)]
    missing_scale = [
        n for n in scale_names if not re.search(rf"{re.escape(n)}\s*:", content)
    ]
    assert not missing_scale, (
        f"tokens.css nedostaju spacing-scale tokeni: {missing_scale}. AC5."
    )


def test_ac5_total_custom_properties():
    """tokens.css MORA imati tačno 66 CSS custom properties u :root.

    Story 1.5 AC5 baseline: 63 tokens (21 color + 42 typography/rounded/shadow/spacing).
    Story 2-7 A2 cleanup: +3 spacing tokens (--spacing-card-min-width-{sm,md,lg}) za grid minmax().
    """
    content = _read_tokens_css()
    # Pattern: linija počinje (sa whitespace prefix-om) `--name:`
    matches = re.findall(r"^\s*--[a-z][a-z0-9-]*\s*:", content, re.MULTILINE)
    assert len(matches) == 66, (
        f"tokens.css ima {len(matches)} custom properties u :root, očekivano tačno 66 "
        f"(63 Story 1.5 baseline + 3 Story 2-7 spacing-card-min-width tokens). "
        f"AC4 + AC5 + AC8 + Story 2-7 A2 smoke check."
    )


def test_ac5_token_naming_convention():
    """AC5: svi tokeni prate naming convention `--<group>-...` (lowercase, alphanumeric + hyphens).

    project-context.md § CSS Custom Properties naming.
    """
    content = _read_tokens_css()
    # Sve linije sa `--name:` — name mora počinjati grupom (color/typography/rounded/shadow/spacing)
    expected_groups = ("color", "typography", "rounded", "shadow", "spacing")
    all_tokens = re.findall(r"^\s*(--[a-z][a-z0-9-]*)\s*:", content, re.MULTILINE)
    bad = [
        t
        for t in all_tokens
        if not any(t.startswith(f"--{g}-") for g in expected_groups)
    ]
    assert not bad, (
        f"tokens.css ima tokene koji NE prate naming convention `--<group>-...`: {bad}. "
        f"Dozvoljene grupe: {expected_groups}. AC5 + project-context.md."
    )


# =============================================================================
# AC6 — Django integration (settings + dependency)
# =============================================================================


def test_ac6_whitenoise_in_deps():
    """AC6: pyproject.toml [project].dependencies MORA imati `whitenoise>=6.8.0`."""
    data = _load_pyproject()
    deps = data.get("project", {}).get("dependencies", [])
    whitenoise_specs = [d for d in deps if d.lower().startswith("whitenoise")]
    assert whitenoise_specs, (
        f"pyproject.toml [project].dependencies NE sadrži `whitenoise`. "
        f"Story 1.5 Task 8.1: `uv add whitenoise>=6.8.0`. Trenutne deps: {deps}"
    )
    # Verifikuj minimum version
    spec = whitenoise_specs[0]
    assert ">=6.8" in spec or ">= 6.8" in spec, (
        f"whitenoise spec '{spec}' ne zahteva >=6.8.0. Story 1.5 zahteva >=6.8.0."
    )


def test_ac6_static_url_leading_slash():
    """AC6 / Gotcha #29: `STATIC_URL = "/static/"` (leading slash) za i18n_patterns kompatibilnost."""
    src = _read_base_source()
    pattern = r"^\s*STATIC_URL\s*=\s*['\"]/static/['\"]"
    assert re.search(pattern, src, re.MULTILINE), (
        'base.py nema `STATIC_URL = "/static/"` (sa leading slash-om). '
        "Gotcha #29: bez leading slash-a, {% static %} na /sr/ stranici "
        "resolve-uje u /sr/static/... → 404. Story 1.5 FIX 3."
    )
    # Negative — ne sme biti `STATIC_URL = "static/"` (bez leading slash)
    bad_pattern = r"^\s*STATIC_URL\s*=\s*['\"]static/['\"]"
    assert not re.search(bad_pattern, src, re.MULTILINE), (
        'base.py JOŠ uvek ima `STATIC_URL = "static/"` (bez leading slash-a). '
        'Story 1.4 vrednost; Story 1.5 mora promeniti na `"/static/"`.'
    )


def test_ac6_staticfiles_dirs_configured():
    """AC6: base.py mora imati `STATICFILES_DIRS = [BASE_DIR / "static"]`."""
    src = _read_base_source()
    # Match: STATICFILES_DIRS = [BASE_DIR / "static"]
    pattern = r"STATICFILES_DIRS\s*=\s*\[\s*BASE_DIR\s*/\s*['\"]static['\"]\s*\]"
    assert re.search(pattern, src), (
        'base.py NEMA `STATICFILES_DIRS = [BASE_DIR / "static"]`. '
        "Story 1.5 AC6 + Task 7.4: lista (ne tuple, ne string)."
    )


def test_ac6_static_root_configured():
    """AC6: base.py mora imati `STATIC_ROOT = BASE_DIR / "staticfiles"`."""
    src = _read_base_source()
    pattern = r"STATIC_ROOT\s*=\s*BASE_DIR\s*/\s*['\"]staticfiles['\"]"
    assert re.search(pattern, src), (
        'base.py NEMA `STATIC_ROOT = BASE_DIR / "staticfiles"`. '
        "Story 1.5 AC6 + Task 7.5: destinacija za collectstatic (prod-only)."
    )


def test_ac6_whitenoise_middleware_position():
    """AC6: WhiteNoiseMiddleware mora biti u MIDDLEWARE listi POSLE SecurityMiddleware, PRE SessionMiddleware.

    Whitenoise docs eksplicit zahteva ovaj order. Runtime check kroz _load_settings_module.
    """
    base = _load_settings_module("base")
    assert hasattr(base, "MIDDLEWARE"), "base.py NEMA MIDDLEWARE setting."
    mw = base.MIDDLEWARE
    sec = "django.middleware.security.SecurityMiddleware"
    wn = "whitenoise.middleware.WhiteNoiseMiddleware"
    sess = "django.contrib.sessions.middleware.SessionMiddleware"
    assert wn in mw, (
        f"MIDDLEWARE NE sadrži `{wn}`. Story 1.5 AC6 + Task 7.9. Trenutna lista: {mw}"
    )
    sec_idx = mw.index(sec)
    wn_idx = mw.index(wn)
    sess_idx = mw.index(sess)
    assert sec_idx < wn_idx < sess_idx, (
        f"WhiteNoiseMiddleware position pogrešan. "
        f"SecurityMiddleware idx={sec_idx}, WhiteNoise idx={wn_idx}, "
        f"SessionMiddleware idx={sess_idx}. "
        f"Mora biti: Security < Whitenoise < Session (Whitenoise docs)."
    )


def test_ac6_whitenoise_not_in_installed_apps():
    """AC6 / Gotcha #12: `whitenoise` NE SME biti u INSTALLED_APPS (middleware-only)."""
    base = _load_settings_module("base")
    apps_lower = [a.lower() for a in base.INSTALLED_APPS]
    bad = [a for a in apps_lower if a.startswith("whitenoise")]
    assert not bad, (
        f"INSTALLED_APPS sadrži whitenoise reference: {bad}. "
        f"Gotcha #12: Whitenoise je middleware-only, NE app. Ukloni iz INSTALLED_APPS."
    )


def test_ac6_base_storages_plain():
    """AC6: base.py STORAGES dict mora imati plain StaticFilesStorage default (FIX 2).

    Per-env settings override-uju sa Whitenoise (prod/staging) ili ostavljaju plain (dev).
    """
    base = _load_settings_module("base")
    assert hasattr(base, "STORAGES"), (
        "base.py NEMA `STORAGES` dict. Story 1.5 AC6 + Task 7.6 zahteva canonical "
        "Django 5.1+ pattern (NE deprecated STATICFILES_STORAGE)."
    )
    storages = base.STORAGES
    assert "default" in storages, "STORAGES dict NEMA 'default' key (Gotcha #27)."
    assert "staticfiles" in storages, "STORAGES dict NEMA 'staticfiles' key."
    backend = storages["staticfiles"]["BACKEND"]
    assert backend == "django.contrib.staticfiles.storage.StaticFilesStorage", (
        f"base.py STORAGES['staticfiles']['BACKEND'] = '{backend}'. "
        f"Očekivano plain `django.contrib.staticfiles.storage.StaticFilesStorage` (FIX 2). "
        f"Per-env override (production/staging) postavlja Whitenoise manifest."
    )


def test_ac6_development_storages_plain():
    """AC6: development.py MORA imati STORAGES override sa plain StaticFilesStorage (Gotcha #28).

    Bez plain override-a (ako bi development nasleđivao prod manifest) — dobija
    `ValueError: Missing staticfiles manifest entry` pri prvom {% static %} pozivu.
    """
    src = SETTINGS_DEV.read_text(encoding="utf-8") if SETTINGS_DEV.exists() else ""
    assert "STORAGES" in src, (
        "development.py NEMA STORAGES override. Story 1.5 Task 7.7 + Gotcha #28: "
        "dev mora override-ovati sa plain StaticFilesStorage."
    )
    assert "django.contrib.staticfiles.storage.StaticFilesStorage" in src, (
        "development.py STORAGES override NE sadrži plain StaticFilesStorage backend string. "
        "Story 1.5 zahteva `django.contrib.staticfiles.storage.StaticFilesStorage`."
    )


def test_ac6_production_storages_whitenoise():
    """AC6: production.py MORA imati STORAGES override sa Whitenoise CompressedManifestStaticFilesStorage."""
    src = SETTINGS_PROD.read_text(encoding="utf-8") if SETTINGS_PROD.exists() else ""
    assert "STORAGES" in src, (
        "production.py NEMA STORAGES override. Story 1.5 Task 7.8."
    )
    assert "whitenoise.storage.CompressedManifestStaticFilesStorage" in src, (
        "production.py STORAGES override NE koristi `whitenoise.storage.CompressedManifestStaticFilesStorage`. "
        "Story 1.5 zahteva manifest + compression za prod cache-busting."
    )


def test_ac6_staging_storages_whitenoise():
    """AC6: staging.py MORA imati STORAGES override sa Whitenoise CompressedManifestStaticFilesStorage."""
    src = (
        SETTINGS_STAGING.read_text(encoding="utf-8")
        if SETTINGS_STAGING.exists()
        else ""
    )
    assert "STORAGES" in src, "staging.py NEMA STORAGES override. Story 1.5 Task 7.8."
    assert "whitenoise.storage.CompressedManifestStaticFilesStorage" in src, (
        "staging.py STORAGES override NE koristi `whitenoise.storage.CompressedManifestStaticFilesStorage`. "
        "Staging je production-like — manifest se koristi za realan test."
    )


# =============================================================================
# AC7 — base.html modifikacija
# =============================================================================


def test_ac7_base_html_loads_static():
    """AC7: templates/base.html MORA imati `{% load static %}` direktivu."""
    content = _read_file(BASE_HTML)
    assert "{% load static %}" in content, (
        "templates/base.html NEMA `{% load static %}`. "
        "Story 1.5 Task 9.2: direktiva ide odmah POSLE {% load i18n %}. "
        "Bez nje, {% static %} tag daje TemplateSyntaxError (Gotcha #13)."
    )


def test_ac7_base_html_links_tokens_css():
    """AC7: templates/base.html MORA imati `<link rel="stylesheet" href="{% static "css/tokens.css" %}">`."""
    content = _read_file(BASE_HTML)
    # Tolerant pattern — single ili double quotes oko CSS path-a
    pattern = r'<link\s+rel\s*=\s*"stylesheet"\s+href\s*=\s*"\{%\s*static\s+["\']css/tokens\.css["\']\s*%\}"'
    assert re.search(pattern, content), (
        'templates/base.html NEMA `<link rel="stylesheet" href="{% static "css/tokens.css" %}">`. '
        "Story 1.5 Task 9.4 + AC7 egzaktan placement."
    )


def test_ac7_tokens_css_link_before_block_extra_head():
    """AC7: tokens.css <link> MORA biti PRE `{% block extra_head %}` u HTML redosledu.

    Razlog: Story 1.6 dodaje Bootstrap CSS u extra_head — tokens.css mora load prvo
    da custom properties postoje kad Bootstrap override-i koriste var(--...).
    """
    content = _read_file(BASE_HTML)
    tokens_idx = content.find("tokens.css")
    extra_head_idx = content.find("{% block extra_head %}")
    assert tokens_idx != -1, "tokens.css link NIJE u base.html (drugi test hvata)."
    assert extra_head_idx != -1, (
        "base.html NEMA `{% block extra_head %}` (regression!)."
    )
    assert tokens_idx < extra_head_idx, (
        f"tokens.css link je POSLE `{{% block extra_head %}}` u base.html "
        f"(tokens_idx={tokens_idx}, extra_head_idx={extra_head_idx}). "
        f"AC7 zahteva PRE — Bootstrap u Story 1.6 mora učitati tokens prvo."
    )


def test_ac7_tokens_css_uses_double_quotes():
    """AC7 / Task 9.6: `{% static "css/tokens.css" %}` koristi double quotes (konzistentnost)."""
    content = _read_file(BASE_HTML)
    # Pattern hvata double quotes oko path-a unutar {% static %}
    pattern = r'\{%\s*static\s+"css/tokens\.css"\s*%\}'
    assert re.search(pattern, content), (
        "templates/base.html `{% static %}` tag NE koristi double quotes oko 'css/tokens.css'. "
        "Story 1.5 Task 9.6: konzistentnost sa Story 1.4 stilom — double quotes preferirane."
    )


# =============================================================================
# AC8 — Smoke validation
# =============================================================================


def test_ac8_django_check_passes():
    """AC8: `uv run python manage.py check --settings=config.settings.development` exit 0.

    KRITIČNO: ovaj test puca ako whitenoise nije instaliran (`uv add whitenoise>=6.8.0` first).
    """
    uv_bin = shutil.which("uv")
    if uv_bin is None:
        pytest.skip("uv binary nije u PATH-u.")
    if not MANAGE_PY.exists():
        pytest.fail("manage.py ne postoji — Story 1.1 nije done.")
    result = _run(
        [
            uv_bin,
            "run",
            "python",
            "manage.py",
            "check",
            "--settings=config.settings.development",
        ],
        env={"DJANGO_SECRET_KEY": TEST_SECRET},
    )
    assert result.returncode == 0, (
        f"`manage.py check` exit code {result.returncode}.\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}\n"
        f"Verovatno whitenoise nije instaliran (uv add whitenoise>=6.8.0) ili "
        f"settings sintaksa ima grešku."
    )


def test_ac8_collectstatic_dry_run_finds_tokens_css():
    """AC8: `collectstatic --dry-run --noinput` exit 0 i sadrži pomen tokens.css."""
    uv_bin = shutil.which("uv")
    if uv_bin is None:
        pytest.skip("uv binary nije u PATH-u.")
    if not TOKENS_CSS.exists():
        pytest.skip(
            "tokens.css ne postoji — drugi test (test_ac3_tokens_css_exists) hvata."
        )
    result = _run(
        [
            uv_bin,
            "run",
            "python",
            "manage.py",
            "collectstatic",
            "--dry-run",
            "--noinput",
            "--settings=config.settings.development",
        ],
        env={"DJANGO_SECRET_KEY": TEST_SECRET},
    )
    assert result.returncode == 0, (
        f"`collectstatic --dry-run` exit code {result.returncode}.\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    combined = result.stdout + result.stderr
    # Output mora pomenuti tokens.css (Django collectstatic format: 'css/tokens.css' ili 'tokens.css')
    assert "tokens.css" in combined, (
        f"`collectstatic --dry-run` output NE pominje tokens.css. "
        f"stdout: {result.stdout[:500]}"
    )
    # Negative — ne sme imati googleapis.com
    assert "googleapis.com" not in combined, (
        "`collectstatic` output sadrži 'googleapis.com' — anti-pattern."
    )


def test_ac8_django_client_serves_tokens_css():
    """AC8: Django Client GET /static/css/tokens.css → 200 + sadrži --color-brand-green-800.

    Skip ako pytest-django nije instaliran (fallback test_ac8_collectstatic_dry_run hvata).
    """
    pytest.importorskip(
        "pytest_django", reason="pytest-django nije instaliran — skip Client test."
    )
    if not TOKENS_CSS.exists():
        pytest.skip("tokens.css ne postoji — drugi test hvata.")
    os.environ.setdefault("DJANGO_SECRET_KEY", TEST_SECRET)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    # Force fresh settings reload (Story 1.5 može modifikovati settings posle imports-a iznad)
    for mod_key in list(sys.modules.keys()):
        if mod_key.startswith("config.settings"):
            del sys.modules[mod_key]
    try:
        import django

        django.setup()
    except Exception as exc:
        pytest.skip(f"Django setup pukao: {exc}")
    from django.test import Client

    client = Client(HTTP_HOST="localhost")
    response = client.get("/static/css/tokens.css")
    assert response.status_code == 200, (
        f"GET /static/css/tokens.css → status {response.status_code}, očekivano 200. "
        f"Whitenoise mora servirati ovaj fajl preko STATICFILES_DIRS."
    )
    # Whitenoise vraća WhiteNoiseFileResponse (streaming) — koristi streaming_content
    if hasattr(response, "streaming_content"):
        body_bytes = b"".join(response.streaming_content)
    else:
        body_bytes = response.content
    body = body_bytes.decode("utf-8", errors="replace")
    assert "--color-brand-green-800" in body, (
        "GET /static/css/tokens.css body NE sadrži `--color-brand-green-800`. "
        "Verovatno se servira pogrešan fajl ili je fajl prazan."
    )


def test_ac8_django_client_serves_woff2():
    """AC8: GET /static/fonts/roboto/roboto-latin-400.woff2 → 200 + magic bytes wOF2."""
    pytest.importorskip(
        "pytest_django", reason="pytest-django nije instaliran — skip Client test."
    )
    if not _woff2_files_present():
        pytest.skip(WOFF2_MISSING_MSG)
    os.environ.setdefault("DJANGO_SECRET_KEY", TEST_SECRET)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    for mod_key in list(sys.modules.keys()):
        if mod_key.startswith("config.settings"):
            del sys.modules[mod_key]
    try:
        import django

        django.setup()
    except Exception as exc:
        pytest.skip(f"Django setup pukao: {exc}")
    from django.test import Client

    client = Client(HTTP_HOST="localhost")
    response = client.get("/static/fonts/roboto/roboto-latin-400.woff2")
    assert response.status_code == 200, (
        f"GET /static/fonts/roboto/roboto-latin-400.woff2 → status {response.status_code}, očekivano 200."
    )
    # Whitenoise vraća WhiteNoiseFileResponse (streaming) — koristi streaming_content
    if hasattr(response, "streaming_content"):
        body = b"".join(response.streaming_content)
    else:
        body = bytes(response.content)
    assert body[:4] == b"wOF2", (
        f"Response body NEMA `wOF2` magic bytes. Prvih 4: {body[:4]!r}"
    )


def test_ac8_render_home_includes_tokens_css_link():
    """AC8: GET /sr/ → 200 + HTML sadrži `<link href="/static/css/tokens.css">` (apsolutan URL, ne /sr/static/...)."""
    pytest.importorskip(
        "pytest_django", reason="pytest-django nije instaliran — skip Client test."
    )
    os.environ.setdefault("DJANGO_SECRET_KEY", TEST_SECRET)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    for mod_key in list(sys.modules.keys()):
        if mod_key.startswith("config.settings"):
            del sys.modules[mod_key]
    try:
        import django

        django.setup()
    except Exception as exc:
        pytest.skip(f"Django setup pukao: {exc}")
    from django.test import Client

    client = Client(HTTP_HOST="localhost")
    response = client.get("/sr/")
    assert response.status_code == 200, (
        f"GET /sr/ → status {response.status_code}, očekivano 200. "
        f"Story 1.4 regression — sr lokal mora servirati home."
    )
    html = response.content.decode("utf-8", errors="replace")
    # Mora sadržati /static/css/tokens.css (NE /sr/static/css/...)
    assert "/static/css/tokens.css" in html, (
        f"Render-ovani HTML NE sadrži `/static/css/tokens.css`. "
        f"Verovatno STATIC_URL nema leading slash (Gotcha #29). "
        f"HTML head excerpt: {html[:1000]}"
    )
    assert "/sr/static/" not in html, (
        "Render-ovani HTML sadrži `/sr/static/...` (locale-prefixed static URL). "
        'Gotcha #29: STATIC_URL = "/static/" (leading slash) je obavezno za i18n_patterns.'
    )


# =============================================================================
# Negative / anti-pattern guards
# =============================================================================


def test_no_googleapis_reference_in_base_html():
    """Anti-pattern: templates/base.html NE SME sadržati `googleapis.com`."""
    content = _read_file(BASE_HTML)
    assert "googleapis.com" not in content, (
        "templates/base.html sadrži `googleapis.com` referencu — anti-pattern. "
        "Project-context.md § Self-hosted Roboto: NIKAKAV Google Fonts CDN link."
    )


def test_no_googleapis_reference_in_tokens_css():
    """Anti-pattern: tokens.css NE SME sadržati `googleapis.com` (AC3 explicit)."""
    if not TOKENS_CSS.exists():
        pytest.skip("tokens.css ne postoji — drugi test hvata.")
    content = TOKENS_CSS.read_text(encoding="utf-8")
    assert "googleapis.com" not in content, (
        "tokens.css sadrži `googleapis.com` referencu — anti-pattern. "
        "AC3: NIKAKAV @import url('https://fonts.googleapis.com/...'). Self-hosted only."
    )


def test_no_gstatic_reference_anywhere():
    """Anti-pattern: NIKO od base.html / tokens.css NE SME sadržati `gstatic.com`."""
    for path in (BASE_HTML, TOKENS_CSS):
        if not path.exists():
            continue
        content = path.read_text(encoding="utf-8")
        assert "gstatic.com" not in content, (
            f"{path.relative_to(PROJECT_ROOT)} sadrži `gstatic.com` referencu — anti-pattern. "
            f"Self-hosted Roboto: nikakvi Google CDN-i."
        )


def test_no_preconnect_to_google():
    """Anti-pattern: NIKAKAV `<link rel="preconnect">` ka fonts.googleapis.com / gstatic.com.

    Project-context.md § Self-hosted Roboto. Čak i preconnect je tracking signal.
    """
    if not BASE_HTML.exists():
        pytest.skip("base.html ne postoji.")
    content = BASE_HTML.read_text(encoding="utf-8")
    # Match preconnect link sa Google domenom
    bad = re.findall(
        r'<link[^>]+rel\s*=\s*["\']preconnect["\'][^>]+(?:googleapis|gstatic)\.com',
        content,
        re.IGNORECASE,
    )
    assert not bad, (
        f'templates/base.html ima `<link rel="preconnect">` ka Google domenima: {bad}. '
        f"Anti-pattern — Story 1.5 AC7 + Gotcha #17."
    )


def test_no_at_import_in_tokens_css():
    """Anti-pattern: tokens.css NE SME sadržati `@import` direktiv (sve @font-face inline)."""
    if not TOKENS_CSS.exists():
        pytest.skip("tokens.css ne postoji — drugi test hvata.")
    content = TOKENS_CSS.read_text(encoding="utf-8")
    matches = re.findall(r"^\s*@import\b", content, re.MULTILINE)
    assert not matches, (
        f"tokens.css sadrži @import direktiv(e): {len(matches)} matches. "
        f"AC3 + project-context.md: sve @font-face deklaracije moraju biti inline (no @import)."
    )


# =============================================================================
# Story 2-8 review iter 1 — Undefined-token regression guard
# =============================================================================


def test_story_2_8_css_uses_only_defined_tokens():
    """Story 2-8 (review iter 1 lesson — mirror Story 2-7 iter 1 token rename N1):
    All var(--token) references in tractor-listing.css + range-slider.css MUST resolve
    to :root declarations in tokens.css. Catches undefined-token silent visual drift.

    Razlog: browser silently fall-back na invalid value kad var(--undefined) nema
    declaration u :root → komponenta renderuje sa null/inherit umesto očekivanim
    tokenom (visual regression bez crash-a). Story 2-7 iter 1 N1 + Story 2-8 iter 1
    BUG-B1 — DEDUPLIKOVANA klasa bug-a kroz CSS components.
    """
    if not TOKENS_CSS.exists():
        pytest.skip("tokens.css ne postoji — drugi test hvata.")
    tokens_content = _read_tokens_css()
    defined_tokens = set(re.findall(r"--([a-z][a-z0-9-]*)\s*:", tokens_content))

    component_paths = [
        STATIC_CSS_DIR / "components" / "tractor-listing.css",
        STATIC_CSS_DIR / "components" / "range-slider.css",
    ]
    for path in component_paths:
        if not path.exists():
            pytest.skip(f"{path.relative_to(PROJECT_ROOT)} ne postoji — Story 2-8 možda nije implementirana.")
        css = path.read_text(encoding="utf-8")
        # Strip CSS comments (/* ... */) pre token extraction — comments mogu sadržati
        # literal `var(--token)` placeholder tekst u doc-stringovima koji NIJE pravi
        # CSS reference (false positive guard).
        css_no_comments = re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)
        used = set(re.findall(r"var\(\s*--([a-z][a-z0-9-]*)", css_no_comments))
        undefined = used - defined_tokens
        assert not undefined, (
            f"{path.relative_to(PROJECT_ROOT)} uses undefined tokens: {sorted(undefined)}. "
            f"Add to tokens.css OR rename to existing token (per project-context.md § "
            f"'NE uvoditi nove tokene — koristiti najbliži postojeći')."
        )
