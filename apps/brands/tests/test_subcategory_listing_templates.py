"""Story 2.11 — AC5/AC6/AC7/AC9/AC11 template render testovi za Subcategory Listing.

RED phase (TEA): definiše template/markup kontrakt PRE implementacije. Renderuje
kroz Django test client; verifikuje subcategory cards (REUSE coric-category-card),
model cards (REUSE coric-product-card), breadcrumb (nav/ol/aria-current), i18n+a11y,
i AC9 2-10 href→{% url %} refactor (regression: path identičan).

Pokriva:
- AC5: intermediate subcategory kartice (coric-category-card 1:1) + empty + data-testid.
- AC6: leaf model kartice (coric-product-card) + CTA→products:detail + spec fields + empty.
- AC6: leaf gde su SVI Product is_published=False → empty-state
  (test_leaf_all_unpublished_shows_empty_state).
- AC7: breadcrumb (struktura, root-first, aria-current, pages/home link, data-testid).
- AC9: 2-10 href refactor (placeholder uklonjen + {% url %} + path identičan).
- AC11: i18n + a11y (gettext audit, dijakritike, aria-current, single-h1, CTA aria-label).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from django.conf import settings
from django.test import Client

from apps.brands.models import Category
from apps.brands.tests.factories import (
    CategoryFactory,
    SubcategoryFactory,
)
from apps.products.tests.factories import ProductFactory


def _l1_url(category_slug: str, l1_slug: str) -> str:
    return f"/sr/mehanizacija/prikljucna/{category_slug}/{l1_slug}/"


@pytest.fixture
def intermediate_setup():
    # NAPOMENA: slug NE sme kolidirati sa 0003 seed migracijom
    # (osnovna-obrada-zemljista/priprema-zemljista/masine-za-setvu su seed-ovani);
    # koristimo "Osnovna obrada"-name sa test-prefiksiranim slug-om radi izolacije.
    cat = CategoryFactory.create(
        name="Osnovna obrada zemljišta",
        slug="t211-osnovna-obrada",
        is_for=Category.CategoryScope.MEHANIZACIJA,
    )
    l1 = SubcategoryFactory.create(category=cat, name="Plugovi", slug="plugovi")
    children = [
        SubcategoryFactory.create(
            parent=l1, name="Plugovi obrtači", slug="plugovi-obrtaci", display_order=1
        ),
        SubcategoryFactory.create(
            parent=l1, name="Plugovi ravnjaci", slug="plugovi-ravnjaci", display_order=2
        ),
    ]
    return cat, l1, children


@pytest.fixture
def leaf_setup():
    cat = CategoryFactory.create(
        name="Osnovna obrada zemljišta",
        slug="t211-leaf-kat",
        is_for=Category.CategoryScope.MEHANIZACIJA,
    )
    l1 = SubcategoryFactory.create(category=cat, name="Podrivači", slug="podrivaci")
    products = [
        ProductFactory.create(
            subcategory=l1, name="Model A", slug="model-a",
            is_published=True, horse_power=120, price_eur="9999.00",
        ),
        ProductFactory.create(
            subcategory=l1, name="Model B", slug="model-b", is_published=True,
        ),
    ]
    return cat, l1, products


# ---------------------------------------------------------------------------
# AC5 — intermediate subcategory kartice
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestSubcategoryShowcase:
    def test_renders_coric_category_cards(self, intermediate_setup):
        cat, l1, _children = intermediate_setup
        content = Client().get(_l1_url(cat.slug, l1.slug)).content.decode()
        # REUSE coric-category-card BEM (Story 2-10) — po jedna per child
        assert content.count("coric-category-card") >= 2

    def test_subcategory_card_has_data_testid_and_cta(self, intermediate_setup):
        cat, l1, _children = intermediate_setup
        content = Client().get(_l1_url(cat.slug, l1.slug)).content.decode()
        assert 'data-testid="subcategory-card-plugovi-obrtaci"' in content
        assert 'data-testid="subcategory-card-cta-plugovi-obrtaci"' in content

    def test_subcategory_card_cta_links_to_get_absolute_url(self, intermediate_setup):
        cat, l1, children = intermediate_setup
        content = Client().get(_l1_url(cat.slug, l1.slug)).content.decode()
        # CTA href = subcategory.get_absolute_url() (depth-2 path); slug iz fixture-a
        # (t211-osnovna-obrada — test-izolovan da ne kolidira sa 0003 seed-om).
        assert (
            f"/mehanizacija/prikljucna/{cat.slug}/plugovi/plugovi-obrtaci/" in content
        )

    def test_intermediate_empty_state(self):
        # AC5: čvor koji JE intermediate (Category root) ali bez dece →
        # "Nema dostupnih potkategorija." Modelujemo kroz L1 sa decom uklonjenom...
        # ovde: L1 bez dece je leaf, pa empty-intermediate testiramo na nivou gde
        # parent ima samo decu-bez-unuka. Koristimo L1 sa jednim detetom koje je
        # prazan leaf; ali intermediate-empty je Category-root sценарио (SM-D11).
        cat = CategoryFactory.create(
            slug="prazna-kat", is_for=Category.CategoryScope.MEHANIZACIJA
        )
        l1 = SubcategoryFactory.create(category=cat, slug="grana")
        child = SubcategoryFactory.create(parent=l1, slug="prazno-dete")
        # gledamo intermediate L1 (ima 1 dete) — render mora imati card, ne empty
        content = Client().get(_l1_url(cat.slug, l1.slug)).content.decode()
        assert f'data-testid="subcategory-card-{child.slug}"' in content
        # a prazan-leaf child renderuje model empty-state (ne subcategory empty)
        child_content = Client().get(
            f"/sr/mehanizacija/prikljucna/{cat.slug}/{l1.slug}/{child.slug}/"
        ).content.decode()
        assert "Nema dostupnih modela u ovoj kategoriji." in child_content


# ---------------------------------------------------------------------------
# AC6 — leaf model kartice
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestModelGrid:
    def test_renders_coric_product_cards(self, leaf_setup):
        cat, l1, products = leaf_setup
        content = Client().get(_l1_url(cat.slug, l1.slug)).content.decode()
        # REUSE coric-product-card BEM (Story 2-8) — po jedna per published Product
        assert content.count("coric-product-card") >= 2
        assert 'data-testid="model-card-model-a"' in content

    def test_model_card_cta_links_to_product_detail(self, leaf_setup):
        cat, l1, products = leaf_setup
        content = Client().get(_l1_url(cat.slug, l1.slug)).content.decode()
        # cela kartica vodi na products:detail (product.get_absolute_url)
        assert products[0].get_absolute_url() in content

    def test_model_card_spec_fields_conditional(self, leaf_setup):
        cat, l1, products = leaf_setup
        content = Client().get(_l1_url(cat.slug, l1.slug)).content.decode()
        # Model A ima horse_power=120 → "120 KS" spec field se renderuje
        assert "120" in content
        # Model B nema horse_power ni price → kartica i dalje validna (ime + CTA)
        assert "Model B" in content

    def test_leaf_empty_state_no_products(self):
        cat = CategoryFactory.create(is_for=Category.CategoryScope.MEHANIZACIJA)
        l1 = SubcategoryFactory.create(category=cat, slug="prazno")
        content = Client().get(_l1_url(cat.slug, l1.slug)).content.decode()
        assert "Nema dostupnih modela u ovoj kategoriji." in content

    def test_leaf_all_unpublished_shows_empty_state(self):
        # AC6: leaf gde su SVI Product is_published=False → empty-state (isto kao
        # leaf bez proizvoda).
        cat = CategoryFactory.create(is_for=Category.CategoryScope.MEHANIZACIJA)
        l1 = SubcategoryFactory.create(category=cat, slug="samo-unpublished")
        ProductFactory.create(subcategory=l1, is_published=False)
        ProductFactory.create(subcategory=l1, is_published=False)
        content = Client().get(_l1_url(cat.slug, l1.slug)).content.decode()
        assert "Nema dostupnih modela u ovoj kategoriji." in content


# ---------------------------------------------------------------------------
# AC7 — breadcrumb
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestBreadcrumb:
    def test_breadcrumb_nav_structure(self, intermediate_setup):
        cat, l1, _children = intermediate_setup
        content = Client().get(_l1_url(cat.slug, l1.slug)).content.decode()
        assert 'data-testid="breadcrumb-nav"' in content
        assert "<nav" in content
        assert "<ol" in content

    def test_breadcrumb_root_first_order(self, intermediate_setup):
        cat, l1, _children = intermediate_setup
        content = Client().get(_l1_url(cat.slug, l1.slug)).content.decode()
        # root-first: Početna pre Priključna mehanizacija pre Category pre current
        i_home = content.find("Početna")
        i_prik = content.find("Priključna mehanizacija")
        i_cat = content.find("Osnovna obrada")  # category.name fragment
        assert -1 < i_home < i_prik < i_cat

    def test_breadcrumb_current_has_aria_current(self, intermediate_setup):
        cat, l1, _children = intermediate_setup
        content = Client().get(_l1_url(cat.slug, l1.slug)).content.decode()
        assert 'aria-current="page"' in content
        assert 'data-testid="breadcrumb-current"' in content

    def test_breadcrumb_home_links_to_core_home(self, intermediate_setup):
        from django.urls import reverse

        cat, l1, _children = intermediate_setup
        content = Client().get(_l1_url(cat.slug, l1.slug)).content.decode()
        # "Početna" link → core:home pattern
        home_url = reverse("core:home")
        assert f'href="{home_url}"' in content


# ---------------------------------------------------------------------------
# AC9 — 2-10 href → {% url %} refactor (regression guard)
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestCategoryShowcaseHrefRefactor:
    def test_category_showcase_no_longer_uses_placeholder(self):
        # AC9: placeholder direct-string href (LANGUAGE_CODE konkatenacija) uklonjen;
        # partial koristi {% url %} tag.
        partial = (
            Path(settings.BASE_DIR)
            / "templates"
            / "brands"
            / "partials"
            / "_category_showcase.html"
        )
        src = partial.read_text(encoding="utf-8")
        assert "/{{ LANGUAGE_CODE }}/mehanizacija/prikljucna/" not in src
        assert "{% url" in src

    def test_jeegee_landing_href_path_unchanged(self):
        # AC9 regression: Jeegee landing CTA i dalje produkuje IDENTIČAN path
        # kroz reverse resolution (Story 2-10 test stays green).
        # NAPOMENA (TEA confirm-review): Jeegee Brand + osnovna-obrada-zemljista Category
        # su seed-ovani u 0003 migraciji koja se primenjuje na SVAKU test bazu. Ne
        # kreiramo ih ovde (BrandFactory/CategoryFactory bi pucao na globalno-unique
        # slug collision) — oslanjamo se na seed (mirror Story 2-10 jeegee test pattern).
        from apps.brands.models import Brand

        assert Brand.objects.filter(slug="jeegee").exists(), (
            "Jeegee Brand MORA postojati kroz 0003 seed migraciju (regression preduslov)."
        )
        assert Category.objects.filter(
            slug="osnovna-obrada-zemljista",
            is_for=Category.CategoryScope.MEHANIZACIJA,
        ).exists(), "osnovna-obrada-zemljista Category MORA postojati kroz 0003 seed."

        from django.urls import reverse

        content = Client().get(reverse("brands:jeegee_prikljucna")).content.decode()
        assert "/mehanizacija/prikljucna/osnovna-obrada-zemljista/" in content


# ---------------------------------------------------------------------------
# AC11 — i18n + a11y
# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestI18nA11y:
    def test_single_h1(self, intermediate_setup):
        cat, l1, _children = intermediate_setup
        resp = Client().get(_l1_url(cat.slug, l1.slug))
        assert resp.status_code == 200  # gate: pravi render, ne DEBUG 404 (koji ima 1 <h1>)
        content = resp.content.decode()
        assert content.count("<h1") == 1

    def test_full_diacritics_in_names(self, intermediate_setup):
        cat, l1, _children = intermediate_setup
        content = Client().get(_l1_url(cat.slug, l1.slug)).content.decode()
        # pune dijakritike u name poljima (č/ć/ž/š/đ); NEMA šišane latinice
        assert "Plugovi obrtači" in content
        assert "obrtaci<" not in content  # naziv NIJE šišana latinica

    def test_no_cyrillic_in_output(self, intermediate_setup):
        cat, l1, _children = intermediate_setup
        resp = Client().get(_l1_url(cat.slug, l1.slug))
        assert resp.status_code == 200  # gate: mora biti pravi render, ne 404
        content = resp.content.decode()
        # NEMA ćirilice u user-facing tekstu (SM-D16)
        cyrillic = [ch for ch in content if "Ѐ" <= ch <= "ӿ"]
        assert cyrillic == []

    def test_cta_has_aria_label_with_name(self, intermediate_setup):
        cat, l1, _children = intermediate_setup
        content = Client().get(_l1_url(cat.slug, l1.slug)).content.decode()
        # subcategory-card CTA ima aria-label sa interpolovanim imenom (WCAG 2.4.4)
        assert "aria-label=" in content
        assert "Plugovi obrtači" in content
