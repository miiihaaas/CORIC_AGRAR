"""Story 9.10 — Hero <picture> markup + variant existence/format/size (RED phase, TEA).

Import-light / markup-parse / file-stat. NE Playwright, NE Lighthouse run, NE Docker.
Host caveat (Epic-9 baseline): native-Win pytest collect pada na libmagic — zato ovaj
fajl NE importuje Django app-registry/settings. Parsira IZVOR `_home_hero.html` kroz
pathlib+re (statički {% static %} markup je predvidljiv) i koristi PIL.Image/os.stat
za binarne varijante.

Pokreni:
    python -m pytest apps/pages/tests/test_home_hero_picture.py -p no:django -q

RED: skoro svi testovi padaju dok Dev ne (a) konvertuje hero u <picture>, (b) generiše
.avif/.webp varijante. Regression guard (responsive_picture lazy default) MOŽE proći
već sada — to je dizajn (postojeće ponašanje koje 9.10 NE sme slomiti).

Pokriva: AC2, AC3, AC4, AC8, AC9 + AC4-regresija.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import pytest

# REPO_ROOT: .../apps/pages/tests/ -> parent x3
REPO_ROOT = Path(__file__).resolve().parents[3]
HERO_TEMPLATE = REPO_ROOT / "templates" / "pages" / "partials" / "_home_hero.html"
STATIC_HOME = REPO_ROOT / "static" / "img" / "home"
JPG = STATIC_HOME / "home-hero-1.jpg"
AVIF = STATIC_HOME / "home-hero-1.avif"
WEBP = STATIC_HOME / "home-hero-1.webp"
MEDIA_TAGS = (
    REPO_ROOT / "apps" / "media_pipeline" / "templatetags" / "media_tags.py"
)


# =============================================================================
# Fixtures / helpers
# =============================================================================


@pytest.fixture(scope="module")
def hero_src() -> str:
    """Raw text `_home_hero.html`. Fail-uje ako fajl ne postoji."""
    if not HERO_TEMPLATE.exists():
        pytest.fail(f"Missing required file: {HERO_TEMPLATE}")
    return HERO_TEMPLATE.read_text(encoding="utf-8")


def _picture_block(src: str) -> str:
    """Vrati <picture>...</picture> blok (ili pytest.fail ako fali)."""
    m = re.search(r"<picture\b.*?</picture>", src, re.IGNORECASE | re.DOTALL)
    if not m:
        pytest.fail(
            "Hero NEMA <picture> element — 9.10 Task 2.1 menja plain <img> u "
            "<picture> (AVIF/WebP/JPG). Trenutno je plain <img>."
        )
    return m.group(0)


def _hero_img_tag(src: str) -> str:
    """Vrati <img ... class="coric-home-hero__bg" ...> tag iz hero markup-a."""
    for m in re.finditer(r"<img\b[^>]*>", src, re.IGNORECASE | re.DOTALL):
        if "coric-home-hero__bg" in m.group(0):
            return m.group(0)
    pytest.fail(
        "Nije pronadjen hero <img> sa class='coric-home-hero__bg' u markup-u."
    )
    return ""  # unreachable


def _static_paths_in(markup: str) -> list[str]:
    """Izvuci sve {% static 'img/home/...' %} target path-ove iz markup-a."""
    return re.findall(
        r"{%\s*static\s*['\"]([^'\"]+)['\"]\s*%}", markup
    )


# =============================================================================
# AC2 — <picture> + source order (AVIF before WebP) + <img> last
# =============================================================================


def test_hero_has_picture_element(hero_src):
    """AC2: hero koristi <picture> element (NE plain <img>)."""
    assert "<picture" in hero_src.lower(), (
        "Hero MORA koristiti <picture> element (Task 2.1). Trenutno plain <img>."
    )


def test_avif_source_before_webp_source(hero_src):
    """AC2: <source type='image/avif'> se pojavljuje PRE <source type='image/webp'>."""
    block = _picture_block(hero_src)
    avif_idx = block.lower().find('type="image/avif"')
    if avif_idx < 0:
        avif_idx = block.lower().find("type='image/avif'")
    webp_idx = block.lower().find('type="image/webp"')
    if webp_idx < 0:
        webp_idx = block.lower().find("type='image/webp'")
    assert avif_idx >= 0, "Nema <source type='image/avif'> u <picture>."
    assert webp_idx >= 0, "Nema <source type='image/webp'> u <picture>."
    assert avif_idx < webp_idx, (
        f"AVIF source (idx {avif_idx}) MORA biti PRE WebP source (idx {webp_idx}) — "
        "browser bira prvi podržan format (AVIF -> WebP -> JPG)."
    )


def test_avif_source_has_srcset(hero_src):
    """AC2: <source type='image/avif'> ima srcset koji pokazuje na .avif."""
    block = _picture_block(hero_src)
    m = re.search(
        r"<source\b[^>]*type=['\"]image/avif['\"][^>]*>", block, re.IGNORECASE
    )
    assert m, "Nema <source type='image/avif'> taga."
    assert "srcset" in m.group(0).lower() and ".avif" in m.group(0).lower(), (
        f"AVIF <source> MORA imati srcset sa .avif path-om. Dobijeno: {m.group(0)!r}"
    )


def test_webp_source_has_srcset(hero_src):
    """AC2: <source type='image/webp'> ima srcset koji pokazuje na .webp."""
    block = _picture_block(hero_src)
    m = re.search(
        r"<source\b[^>]*type=['\"]image/webp['\"][^>]*>", block, re.IGNORECASE
    )
    assert m, "Nema <source type='image/webp'> taga."
    assert "srcset" in m.group(0).lower() and ".webp" in m.group(0).lower(), (
        f"WebP <source> MORA imati srcset sa .webp path-om. Dobijeno: {m.group(0)!r}"
    )


def test_img_jpg_fallback_is_last_in_picture(hero_src):
    """AC2/AC9: <img> JPG fallback je POSLEDNJI element u <picture> (posle oba <source>)."""
    block = _picture_block(hero_src)
    last_source = max(
        (m.start() for m in re.finditer(r"<source\b", block, re.IGNORECASE)),
        default=-1,
    )
    img_idx = block.lower().find("<img")
    assert img_idx >= 0, "Nema <img> fallback-a u <picture>."
    assert last_source >= 0, "Nema <source> taga u <picture>."
    assert img_idx > last_source, (
        f"<img> JPG fallback (idx {img_idx}) MORA biti POSLEDNJI — posle svih <source> "
        f"(poslednji source idx {last_source})."
    )


def test_picture_sources_use_static_tag(hero_src):
    """AC2: sva tri path-a (avif/webp/jpg) koriste {% static %} (NE media URL)."""
    block = _picture_block(hero_src)
    static_targets = _static_paths_in(block)
    exts = {Path(p).suffix.lower() for p in static_targets}
    assert {".avif", ".webp", ".jpg"} <= exts, (
        f"<picture> MORA referencirati .avif + .webp + .jpg kroz {{% static %}}. "
        f"Pronadjeni static path-ovi: {static_targets!r}"
    )


# =============================================================================
# AC3 — alt='' + aria-hidden='true' očuvani EGZAKTNO (dekorativni hero)
# =============================================================================


def test_hero_img_alt_is_empty(hero_src):
    """AC3: <img> unutar <picture> zadržava alt='' (prazan — dekorativna slika)."""
    img = _hero_img_tag(hero_src)
    m = re.search(r"alt\s*=\s*(['\"])(.*?)\1", img, re.IGNORECASE | re.DOTALL)
    assert m is not None, f"Hero <img> nema alt atribut. Tag: {img!r}"
    assert m.group(2) == "", (
        f"Hero <img> alt MORA biti EGZAKTNO prazan ('') — dekorativna slika, "
        f"semantiku nosi <h1>. NE izmišljaj alt. Dobijeno alt={m.group(2)!r}"
    )


def test_hero_img_has_aria_hidden_true(hero_src):
    """AC3: <img> zadržava aria-hidden='true' EGZAKTNO."""
    img = _hero_img_tag(hero_src)
    assert re.search(r'aria-hidden\s*=\s*["\']true["\']', img, re.IGNORECASE), (
        f"Hero <img> MORA imati aria-hidden='true' (dekorativna). Tag: {img!r}"
    )


def test_hero_img_class_preserved(hero_src):
    """AC3/Task 2.2: class='coric-home-hero__bg' OČUVAN na <img> (CSS cilja <img>, NE <picture>)."""
    img = _hero_img_tag(hero_src)
    assert "coric-home-hero__bg" in img, (
        f"Hero <img> MORA zadržati class='coric-home-hero__bg' (CSS background pozicioniranje). "
        f"Tag: {img!r}"
    )


# =============================================================================
# AC4 — loading='eager' na LCP hero; fetchpriority vidljivost; lazy regression
# =============================================================================


def test_hero_img_loading_eager(hero_src):
    """AC4: hero <img> ima loading='eager' (NE lazy — lazy na LCP element usporava LCP)."""
    img = _hero_img_tag(hero_src)
    assert re.search(r'loading\s*=\s*["\']eager["\']', img, re.IGNORECASE), (
        f"Hero <img> MORA imati loading='eager' (LCP element). Tag: {img!r}"
    )


def test_hero_img_not_lazy(hero_src):
    """AC4: hero <img> NE SME imati loading='lazy' (regresija-guard za LCP)."""
    img = _hero_img_tag(hero_src)
    assert not re.search(r'loading\s*=\s*["\']lazy["\']', img, re.IGNORECASE), (
        f"Hero <img> NE SME biti loading='lazy' (LCP usporava). Tag: {img!r}"
    )


def test_hero_img_has_fetchpriority_high(hero_src):
    """AC4: hero <img> ima fetchpriority='high' (LCP boost) — HARD assert.

    9.10 je dodao `fetchpriority="high"` u hero <img> (vidi _home_hero.html).
    Promovisano iz xfail u tvrdu tvrdnju: slučajno BUDUĆE uklanjanje
    fetchpriority sada OBARA suite (regresija-guard), ne tihi prolaz.
    """
    img = _hero_img_tag(hero_src)
    assert re.search(
        r'fetchpriority\s*=\s*["\']high["\']', img, re.IGNORECASE
    ), (
        f"Hero <img> SHOULD imati fetchpriority='high' (LCP boost). Tag: {img!r}"
    )


def test_responsive_picture_default_loading_lazy_unchanged(hero_src):
    """AC4 regresija: responsive_picture tag default loading='lazy' NETAKNUT.

    Below-the-fold uploaded media ostaje lazy — 9.10 menja SAMO static hero (eager),
    NE sme slomiti lazy default za uploaded media (6+ caller-a Epic 2/3/5).
    Ovaj test MOŽE proći već sada — dizajn (existing behavior guard).
    """
    if not MEDIA_TAGS.exists():
        pytest.fail(f"Missing required file: {MEDIA_TAGS}")
    src = MEDIA_TAGS.read_text(encoding="utf-8")
    assert re.search(r'loading\s*:\s*str\s*=\s*["\']lazy["\']', src), (
        "responsive_picture MORA zadržati default `loading: str = \"lazy\"` "
        "(below-the-fold lazy regresija-guard)."
    )


# =============================================================================
# AC8 / AC1 — variant existence + format + strictly-smaller-than-jpg
# =============================================================================


def test_jpg_source_exists():
    """AC8: source home-hero-1.jpg fizički postoji (baseline za size compare)."""
    assert JPG.exists(), (
        f"Source JPG ne postoji: {JPG}. Ovo je baseline (≈413 KB) za size-guard."
    )


def test_avif_variant_exists():
    """AC1/AC8: home-hero-1.avif fizički postoji u static/img/home/."""
    assert AVIF.exists(), (
        f"AVIF varijanta ne postoji: {AVIF}. 9.10 Task 1.3: generiši + komituj. (RED)"
    )


def test_webp_variant_exists():
    """AC1/AC8: home-hero-1.webp fizički postoji u static/img/home/."""
    assert WEBP.exists(), (
        f"WebP varijanta ne postoji: {WEBP}. 9.10 Task 1.3: generiši + komituj. (RED)"
    )


def test_avif_strictly_smaller_than_jpg():
    """AC1: home-hero-1.avif je STRIKTNO manji od home-hero-1.jpg (os.stat size)."""
    if not AVIF.exists():
        pytest.fail(f"AVIF varijanta ne postoji: {AVIF} (RED — Task 1.3).")
    if not JPG.exists():
        pytest.fail(f"Source JPG ne postoji: {JPG}.")
    avif_size = os.stat(AVIF).st_size
    jpg_size = os.stat(JPG).st_size
    assert avif_size < jpg_size, (
        f"AVIF ({avif_size} B) MORA biti STRIKTNO manji od JPG ({jpg_size} B). "
        f"AC1 — NEMA tihog komitovanja >= varijante; spusti quality= i re-enkoduj."
    )


def test_webp_strictly_smaller_than_jpg():
    """AC1: home-hero-1.webp je STRIKTNO manji od home-hero-1.jpg (os.stat size)."""
    if not WEBP.exists():
        pytest.fail(f"WebP varijanta ne postoji: {WEBP} (RED — Task 1.3).")
    if not JPG.exists():
        pytest.fail(f"Source JPG ne postoji: {JPG}.")
    webp_size = os.stat(WEBP).st_size
    jpg_size = os.stat(JPG).st_size
    assert webp_size < jpg_size, (
        f"WebP ({webp_size} B) MORA biti STRIKTNO manji od JPG ({jpg_size} B). AC1."
    )


def test_avif_format_is_avif():
    """AC8: PIL.Image.open(avif).format == 'AVIF' (hvata WebP-bytes-na-.avif-path mismatch)."""
    if not AVIF.exists():
        pytest.fail(f"AVIF varijanta ne postoji: {AVIF} (RED — Task 1.3).")
    from PIL import Image

    with Image.open(AVIF) as im:
        fmt = im.format
    assert fmt == "AVIF", (
        f"home-hero-1.avif format = {fmt!r}, mora biti 'AVIF'. "
        f"Format/ekstenzija mismatch bi naterao <source type='image/avif'> da servira ne-AVIF."
    )


def test_webp_format_is_webp():
    """AC8: PIL.Image.open(webp).format == 'WEBP' (format/ekstenzija guard)."""
    if not WEBP.exists():
        pytest.fail(f"WebP varijanta ne postoji: {WEBP} (RED — Task 1.3).")
    from PIL import Image

    with Image.open(WEBP) as im:
        fmt = im.format
    assert fmt == "WEBP", (
        f"home-hero-1.webp format = {fmt!r}, mora biti 'WEBP'."
    )


# =============================================================================
# AC8 — svaki path u hero markup-u fizički postoji (no 404)
# =============================================================================


def test_all_picture_paths_physically_exist(hero_src):
    """AC8: SVAKI {% static %} path u hero <picture> pokazuje na fajl koji POSTOJI."""
    block = _picture_block(hero_src)
    static_targets = _static_paths_in(block)
    assert static_targets, "Nijedan {% static %} path nije pronadjen u <picture>."
    missing = []
    for target in static_targets:
        # target je npr. 'img/home/home-hero-1.avif' relativno na static/ root
        fs_path = REPO_ROOT / "static" / target
        if not fs_path.exists():
            missing.append(target)
    assert not missing, (
        f"<picture> referencira fajl(ove) koji NE postoje u static/: {missing}. "
        f"AC8 — nema 404 reference; generiši varijante (Task 1.3)."
    )


# =============================================================================
# AC9 — <img> ima validan src= (jpg), NE samo srcset (legacy fallback)
# =============================================================================


def test_hero_img_has_real_src_jpg(hero_src):
    """AC9: <img> ima validan src= (jpg) — NE samo srcset na <source>; legacy-browser fallback."""
    img = _hero_img_tag(hero_src)
    m = re.search(
        r"src\s*=\s*['\"]?\s*{%\s*static\s*['\"]([^'\"]+)['\"]", img, re.IGNORECASE
    )
    assert m is not None, (
        f"Hero <img> MORA imati src={{% static '...jpg' %}} (legacy browser fallback, AC9). "
        f"Tag: {img!r}"
    )
    assert m.group(1).lower().endswith(".jpg"), (
        f"Hero <img> src MORA pokazivati na .jpg fallback, dobijeno: {m.group(1)!r}"
    )
