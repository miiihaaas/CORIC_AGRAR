"""Story 6.2 — Sitemap sadrži SAV javni sadržaj + CRIT-2 guard (TEA RED phase).

Pokriva AC3 (SM-D3):
- javni Product/Brand/Subcategory/Post get_absolute_url path SUFIKS u <loc> skupu.
- pages:home/about/contact reverse path u <loc> skupu (PageSitemap).
- NE asertuj Series/Category (nemaju sitemap klasu — CRIT-2).

CRIT-2 GUARD (Task 6.2 / SM2-11): seed Series + brands.Category u DB →
/sitemap.xml MORA ostati 200 (oni NEMAJU sitemap klasu → location() se nikad ne
poziva → nema NoReverseMatch → nema 500). Sprečava slučajnu re-introdukciju
SeriesSitemap/CategorySitemap koji bi oborili ceo sitemap u 500.

⚠️ C2 depth-4 hazard: Subcategory seed kroz factory (normalan save()/full_clean()),
NE bulk_create/raw SQL — model clean() ograničava depth ≤3 (rute l1/l2/l3; l4 ne
postoji → NoReverseMatch). Top-level (depth=1) je bezbedno.

IMP-4: asertuj PATH SUFIKSE (get_absolute_url()), NE pune apsolutne URL-e
(host=testserver iz RequestSite).

Refs:
- 6-2-...-hreflang.md AC3 + Task 6.2 + SM-D3/D6 + Gotcha SM2-2/SM2-11/CRIT-2
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

import pytest

pytestmark = pytest.mark.django_db

SM_NS = "http://www.sitemaps.org/schemas/sitemap/0.9"


def _loc_texts(content: bytes) -> list[str]:
    root = ET.fromstring(content)
    return [el.text for el in root.findall(f".//{{{SM_NS}}}loc") if el.text]


@pytest.fixture
def public_subcategory():
    """Top-level (depth=1) Subcategory kroz factory (save()/full_clean — C2 depth-safe)."""
    from apps.brands.tests.factories import SubcategoryFactory

    return SubcategoryFactory.create(slug="seo-sitemap-subcat")


@pytest.fixture
def public_content(product, brand, post, public_subcategory):
    """Po jedan javni objekat svakog sitemap-ovanog tipa."""
    return {
        "product": product,
        "brand": brand,
        "post": post,
        "subcategory": public_subcategory,
    }


def test_public_product_in_sitemap(client, public_content):
    response = client.get("/sitemap.xml")
    assert response.status_code == 200
    locs = _loc_texts(response.content)
    path = public_content["product"].get_absolute_url()
    assert any(path in loc for loc in locs), (
        f"javni Product path {path!r} MORA biti u <loc> skupu (AC3)."
    )


def test_public_brand_in_sitemap(client, public_content):
    response = client.get("/sitemap.xml")
    assert response.status_code == 200
    locs = _loc_texts(response.content)
    path = public_content["brand"].get_absolute_url()
    assert any(path in loc for loc in locs), (
        f"javni Brand path {path!r} MORA biti u <loc> skupu (AC3)."
    )


def test_public_subcategory_in_sitemap(client, public_content):
    response = client.get("/sitemap.xml")
    assert response.status_code == 200
    locs = _loc_texts(response.content)
    path = public_content["subcategory"].get_absolute_url()
    assert any(path in loc for loc in locs), (
        f"Subcategory path {path!r} MORA biti u <loc> skupu (AC3)."
    )


def test_published_post_in_sitemap(client, public_content):
    response = client.get("/sitemap.xml")
    assert response.status_code == 200
    locs = _loc_texts(response.content)
    path = public_content["post"].get_absolute_url()
    assert any(path in loc for loc in locs), (
        f"objavljen Post path {path!r} MORA biti u <loc> skupu (AC3)."
    )


def test_static_pages_in_sitemap(client, public_content):
    from django.urls import reverse

    response = client.get("/sitemap.xml")
    assert response.status_code == 200
    locs = _loc_texts(response.content)
    for name in ("pages:home", "pages:about", "pages:contact"):
        path = reverse(name)
        assert any(path in loc for loc in locs), (
            f"statička strana {name} ({path!r}) MORA biti u <loc> skupu (PageSitemap; AC3)."
        )


# ── CRIT-2 GUARD: Series/Category u DB ne sme oboriti sitemap u 500 ───────────


def test_seeded_series_and_category_do_not_break_sitemap(client, product, brand, post):
    """Seed Series + brands.Category → /sitemap.xml STILL 200.

    Series/Category get_absolute_url RAISE NoReverseMatch (rute ne postoje), ALI
    nemaju sitemap klasu → location() se nikad ne poziva → nema 500. Ovaj guard
    pada (500) ako neko slučajno doda SeriesSitemap/CategorySitemap dok rute još
    ne postoje (SM2-11/CRIT-2).
    """
    from apps.brands.tests.factories import CategoryFactory, SeriesFactory

    SeriesFactory.create()
    CategoryFactory.create(slug="seo-sitemap-guard-cat")

    response = client.get("/sitemap.xml")
    assert response.status_code == 200, (
        "Seed-ovan Series/Category u DB NE SME oboriti /sitemap.xml u 500 — "
        "oni nemaju sitemap klasu (CRIT-2/SM2-11)."
    )


def test_series_and_category_not_in_loc(client):
    """Series/Category nemaju javnu detail rutu → njihovi slug-ovi nisu u sitemap-u.

    Slugovi se biraju tako da su RAZLIČITI od slug-ova javnih objekata u conftest
    fiksturama (npr. "traktor-coric-5000", "duro-dakovic") — asercija je load-bearing.

    NM-1 fix: umesto trivijalno-true `if "series" in loc.lower()` gard-a (koji nikad
    ne filtrira ništa → can't fail) koristimo direktnu slug pretragu po svim loc-ovima.
    SeriesFactory auto-generiše slug iz "Test Series N"; CategoryFactory dobija
    eksplicitni slug "seo-sitemap-absent-cat" — oba su DISTINCT od javnih objekata.
    """
    from apps.brands.tests.factories import CategoryFactory, SeriesFactory

    series = SeriesFactory.create()
    category = CategoryFactory.create(slug="seo-sitemap-absent-cat")

    response = client.get("/sitemap.xml")
    assert response.status_code == 200
    locs = _loc_texts(response.content)
    # Slug Series-a ne sme se pojaviti ni u jednom loc-u (nemaju sitemap klasu — CRIT-2).
    assert not any(series.slug in loc for loc in locs), (
        f"Series slug {series.slug!r} NE SME biti u <loc> skupu — "
        f"Series nema sitemap klasu (CRIT-2/SM2-11)."
    )
    # Slug Category-je ne sme se pojaviti ni u jednom loc-u.
    assert not any(category.slug in loc for loc in locs), (
        f"Category slug {category.slug!r} NE SME biti u <loc> skupu — "
        f"Category nema sitemap klasu (CRIT-2/SM2-11)."
    )
