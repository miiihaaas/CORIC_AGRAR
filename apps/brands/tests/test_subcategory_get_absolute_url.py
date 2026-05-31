"""Story 2.11 — AC8 testovi za Subcategory.get_absolute_url().

RED phase (TEA): definiše model-method kontrakt PRE implementacije. Trenutno
`get_absolute_url()` baca NotImplementedError (live apps/brands/models.py:411-414);
ovi testovi MORAJU da padnu dok Dev ne implementira metodu (SM-D8).

Pokriva:
- AC8: per-depth path konstrukcija (depth 1/2/3) — category_slug + N subcat slugs.
- AC8: round-trip resolve() OBAVEZAN na sva 3 nivoa (URL → view_name → kwargs →
  isti broj subcat slugs) — test_get_absolute_url_roundtrip_depth_1_2_3.
- AC8: NotImplementedError je uklonjen.

NAPOMENA: round-trip proverava `resolve().view_name == subcategory_listing_lN`
umesto importa SubcategoryListView na modul nivou.
"""

from __future__ import annotations

import pytest
from django.urls import resolve

from apps.brands.models import Category
from apps.brands.tests.factories import CategoryFactory, SubcategoryFactory


@pytest.mark.django_db
class TestSubcategoryGetAbsoluteUrl:
    # AC8: depth-1 (parent=None) → category_slug + 1 subcat slug
    def test_get_absolute_url_depth_1(self):
        # NAPOMENA: slug NE sme kolidirati sa 0003 seed migracijom
        # (osnovna-obrada-zemljista je seed-ovan + Category.slug je globalno unique);
        # koristimo test-izolovan slug radi izolacije od seed podataka.
        cat = CategoryFactory.create(
            slug="t211-gau-kat", is_for=Category.CategoryScope.MEHANIZACIJA
        )
        l1 = SubcategoryFactory.create(category=cat, slug="plugovi")
        assert l1.get_depth() == 1
        assert (
            l1.get_absolute_url()
            == "/sr/mehanizacija/prikljucna/t211-gau-kat/plugovi/"
        )

    # AC8: depth-2 → category_slug + 2 subcat slug-a (1 ancestor + self)
    def test_get_absolute_url_depth_2(self):
        cat = CategoryFactory.create(
            slug="t211-gau-kat", is_for=Category.CategoryScope.MEHANIZACIJA
        )
        l1 = SubcategoryFactory.create(category=cat, slug="plugovi")
        l2 = SubcategoryFactory.create(parent=l1, slug="plugovi-obrtaci")
        assert l2.get_depth() == 2
        assert (
            l2.get_absolute_url()
            == "/sr/mehanizacija/prikljucna/t211-gau-kat/plugovi/plugovi-obrtaci/"
        )

    # AC8: depth-3 → category_slug + 3 subcat slug-a (2 ancestora + self)
    def test_get_absolute_url_depth_3(self):
        cat = CategoryFactory.create(
            slug="t211-gau-kat", is_for=Category.CategoryScope.MEHANIZACIJA
        )
        l1 = SubcategoryFactory.create(category=cat, slug="plugovi")
        l2 = SubcategoryFactory.create(parent=l1, slug="plugovi-obrtaci")
        l3 = SubcategoryFactory.create(parent=l2, slug="greda-120")
        assert l3.get_depth() == 3
        assert (
            l3.get_absolute_url()
            == "/sr/mehanizacija/prikljucna/t211-gau-kat/plugovi/plugovi-obrtaci/greda-120/"
        )

    # AC8: round-trip OBAVEZAN na depth 1, 2 I 3 — resolve(url) vodi nazad na
    # subcategory_listing_lN sa kwargs koji jednoznačno identifikuju isti čvor.
    def test_get_absolute_url_roundtrip_depth_1_2_3(self):
        cat = CategoryFactory.create(
            slug="t211-gau-kat", is_for=Category.CategoryScope.MEHANIZACIJA
        )
        l1 = SubcategoryFactory.create(category=cat, slug="plugovi")
        l2 = SubcategoryFactory.create(parent=l1, slug="plugovi-obrtaci")
        l3 = SubcategoryFactory.create(parent=l2, slug="greda-120")

        for node, expected_view, expected_subslugs in (
            (l1, "brands:subcategory_listing_l1", ["plugovi"]),
            (l2, "brands:subcategory_listing_l2", ["plugovi", "plugovi-obrtaci"]),
            (
                l3,
                "brands:subcategory_listing_l3",
                ["plugovi", "plugovi-obrtaci", "greda-120"],
            ),
        ):
            match = resolve(node.get_absolute_url())
            assert match.view_name == expected_view
            assert match.kwargs["category_slug"] == cat.slug
            # broj subcat slug kwargs == get_depth() (NEMA off-by-one)
            subslugs = [
                match.kwargs[k]
                for k in ("l1_slug", "l2_slug", "l3_slug")
                if k in match.kwargs
            ]
            assert subslugs == expected_subslugs
            assert len(subslugs) == node.get_depth()

    # AC8: NotImplementedError je uklonjen (metoda vraća string, ne baca).
    def test_no_longer_raises_not_implemented(self):
        cat = CategoryFactory.create(is_for=Category.CategoryScope.MEHANIZACIJA)
        l1 = SubcategoryFactory.create(category=cat, slug="plugovi")
        try:
            url = l1.get_absolute_url()
        except NotImplementedError:  # pragma: no cover
            pytest.fail("get_absolute_url() i dalje baca NotImplementedError")
        assert isinstance(url, str) and url.startswith("/")
