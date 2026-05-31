"""Story 2.11 — AC1 + AC3/AC13 URL routing testovi za Subcategory Listing drill-down.

RED phase (TEA): definiše URL kontrakt PRE implementacije. Svi testovi MORAJU
da padnu dok Dev ne registruje `subcategory_listing_l1/l2/l3` pattern-e (SM-D6
BINDING) + `SubcategoryListView` (SM-D4).

Pokriva:
- AC1: 3 nivoa drill-down rezolvuju SubcategoryListView; sva 3 locale prefiksa;
  statički `/mehanizacija/prikljucna/` i dalje JeegeePrikljucnaView (no-shadow);
  novi pattern-i ne kolidiraju sa traktori/proizvod/polovna.
- AC3/AC13: >3 subcategory segmenta posle category → 404 (URL-level depth cap).

NAPOMENA: NE importuje SubcategoryListView na modul nivou (to bi dalo collection
ImportError koji blokira ceo fajl). View identitet se proverava kroz
`resolve().view_name == "brands:subcategory_listing_lN"`.
"""

from __future__ import annotations

import pytest
from django.urls import resolve, reverse
from django.urls.exceptions import Resolver404
from django.utils import translation


@pytest.mark.django_db
class TestSubcategoryListingUrls:
    # AC1: nivo-1 drill (category root → top-level subcategories) rezolvuje view
    def test_l1_url_resolves_to_view(self):
        match = resolve("/sr/mehanizacija/prikljucna/osnovna-obrada-zemljista/plugovi/")
        assert match.view_name == "brands:subcategory_listing_l1"
        assert match.kwargs["category_slug"] == "osnovna-obrada-zemljista"
        assert match.kwargs["l1_slug"] == "plugovi"

    # AC1: nivo-2 drill rezolvuje view sa 3 slug kwarg-a
    def test_l2_url_resolves_to_view(self):
        match = resolve(
            "/sr/mehanizacija/prikljucna/osnovna-obrada-zemljista/plugovi/plugovi-obrtaci/"
        )
        assert match.view_name == "brands:subcategory_listing_l2"
        assert match.kwargs["category_slug"] == "osnovna-obrada-zemljista"
        assert match.kwargs["l1_slug"] == "plugovi"
        assert match.kwargs["l2_slug"] == "plugovi-obrtaci"

    # AC1: nivo-3 drill (leaf u 3-deep grani) rezolvuje view sa 4 slug kwarg-a
    def test_l3_url_resolves_to_view(self):
        match = resolve(
            "/sr/mehanizacija/prikljucna/osnovna-obrada-zemljista/plugovi/plugovi-obrtaci/greda-120/"
        )
        assert match.view_name == "brands:subcategory_listing_l3"
        assert match.kwargs["category_slug"] == "osnovna-obrada-zemljista"
        assert match.kwargs["l1_slug"] == "plugovi"
        assert match.kwargs["l2_slug"] == "plugovi-obrtaci"
        assert match.kwargs["l3_slug"] == "greda-120"

    # AC1: reverse round-trip za sva 3 named pattern-a (BINDING SM-D6 imena + putanje)
    def test_reverse_named_patterns(self):
        u1 = reverse(
            "brands:subcategory_listing_l1",
            kwargs={"category_slug": "c", "l1_slug": "a"},
        )
        assert u1 == "/sr/mehanizacija/prikljucna/c/a/"
        u2 = reverse(
            "brands:subcategory_listing_l2",
            kwargs={"category_slug": "c", "l1_slug": "a", "l2_slug": "b"},
        )
        assert u2 == "/sr/mehanizacija/prikljucna/c/a/b/"
        u3 = reverse(
            "brands:subcategory_listing_l3",
            kwargs={
                "category_slug": "c",
                "l1_slug": "a",
                "l2_slug": "b",
                "l3_slug": "d",
            },
        )
        assert u3 == "/sr/mehanizacija/prikljucna/c/a/b/d/"

    # AC1: rezolucija radi za sva 3 locale prefiksa (sr/hu/en)
    @pytest.mark.parametrize("lang", ["sr", "hu", "en"])
    def test_url_resolves_all_locales(self, lang):
        with translation.override(lang):
            match = resolve(
                f"/{lang}/mehanizacija/prikljucna/osnovna-obrada-zemljista/plugovi/"
            )
            assert match.view_name == "brands:subcategory_listing_l1"

    # AC1: statički /mehanizacija/prikljucna/ (BEZ segmenta) NIJE shadow-ovan —
    # i dalje rezolvuje JeegeePrikljucnaView (Story 2-10 regression guard).
    def test_static_prikljucna_not_shadowed(self):
        match = resolve("/sr/mehanizacija/prikljucna/")
        assert match.view_name == "brands:jeegee_prikljucna"

    # AC1: novi pattern-i NE kolidiraju sa postojećim brands/products pattern-ima.
    def test_no_collision_with_existing_patterns(self):
        # traktori/<slug>/ → brands:detail (BrandDetailView), NE Subcategory drill
        assert resolve("/sr/traktori/john-deere/").view_name == "brands:detail"
        # proizvod/<slug>/ → products:detail
        assert resolve("/sr/proizvod/neki-proizvod/").view_name == "products:detail"
        # mehanizacija/polovna/ → products:used_machinery_list
        assert (
            resolve("/sr/mehanizacija/polovna/").view_name
            == "products:used_machinery_list"
        )

    # AC3/AC13: >3 subcategory segmenta posle category-slug → 404 (URL-level depth
    # cap; nema _l4 pattern-a). resolve() baca Resolver404.
    def test_url_depth_exceeds_max_returns_404(self):
        with pytest.raises(Resolver404):
            resolve(
                "/sr/mehanizacija/prikljucna/c/a/b/d/e/"  # 4 subcat segmenta = preko MAX 3
            )
