"""Story 3.1 — AC2: HomeView.get_context_data READ-ONLY agregacija + N+1 guard.

RED phase (TEA): definiše context kontrakt PRE Dev GREEN.

AC2 — 8 testova:
- test_home_context_contains_traktori_brands_hzm_subcategories_latest_posts
- test_home_traktori_brands_are_traktori_only   (SM-D4 — mehanizacija brendovi NISU)
- test_home_traktori_brand_representative_image_from_prefetch  (published_products to_attr)
- test_home_hzm_subcategories_ordered_by_display_order
- test_home_latest_posts_is_empty_list           (SM-D7 forward-compat)
- test_home_empty_hzm_subcategories_when_category_missing  (defensive guard)
- test_home_view_query_count_constant            (N+1 GUARD — GLAVNI RIZIK, SM-D4)
- test_home_view_does_not_write_to_models        (READ-ONLY)

Pokrenuti:
    docker compose -f compose/local.yml exec django python -m pytest \\
        apps/pages/tests/test_home_view.py -v
"""

from __future__ import annotations

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils.translation import activate

from .conftest import (
    assert_home_template,
    get_hzm_category,
    make_mehanizacija_brand,
    make_traktori_brand,
)

pytestmark = pytest.mark.django_db


def test_home_context_contains_traktori_brands_hzm_subcategories_latest_posts(client, home_url):
    """AC2: context ima 'traktori_brands', 'hzm_subcategories', 'latest_posts'."""
    activate("sr")
    make_traktori_brand(name="Test Traktor Brend A")

    response = client.get(home_url)
    assert response.status_code == 200, "Home mora vratiti 200 (RED: HomeView ne postoji)."

    ctx = response.context
    for key in ("traktori_brands", "hzm_subcategories", "latest_posts"):
        assert key in ctx, (
            f"HomeView.get_context_data() MORA dati ključ '{key}' (AC2). "
            f"Prisutni ključevi: {list(ctx.keys())!r}"
        )


def test_home_traktori_brands_are_traktori_only(client, home_url):
    """AC2/SM-D4: Traktori sekcija lista SAMO brendove sa objavljenim condition=NEW
    proizvodom. Mehanizacija brendovi (samo USED proizvod) NE smeju da iscure.
    """
    activate("sr")
    traktor_brand, _ = make_traktori_brand(name="Pravi Traktor Brend")
    mehanizacija_brand = make_mehanizacija_brand(name="Mehanizacija Brend")

    response = client.get(home_url)
    assert response.status_code == 200

    brand_ids = {b.pk for b in response.context["traktori_brands"]}
    assert traktor_brand.pk in brand_ids, (
        "Brend sa objavljenim condition=NEW proizvodom MORA biti u traktori_brands."
    )
    assert mehanizacija_brand.pk not in brand_ids, (
        "SM-D4 LOCK: brend BEZ condition=NEW objavljenog proizvoda (samo USED) NE SME "
        "biti u traktori_brands (sprečava curenje mehanizacija brendova u Traktori)."
    )


def test_home_traktori_brand_representative_image_from_prefetch(client, home_url):
    """AC2/SM-D4: reprezentativna slika dolazi iz prefetch to_attr 'published_products'
    (NE per-brand .first() upit). Verifikuje da je to_attr lista popunjena objavljenim
    proizvodima i da prvi ima main_image.
    """
    activate("sr")
    brand, product = make_traktori_brand(name="Brend Sa Slikom", with_image=True)

    response = client.get(home_url)
    assert response.status_code == 200

    brands = {b.pk: b for b in response.context["traktori_brands"]}
    assert brand.pk in brands
    b = brands[brand.pk]
    assert hasattr(b, "published_products"), (
        "SM-D4: Prefetch MORA koristiti to_attr='published_products' (N+1 guard). "
        "Brand instanca u context-u nema atribut 'published_products'."
    )
    pub = list(b.published_products)
    assert len(pub) >= 1, "published_products mora sadržati bar 1 objavljen proizvod."
    assert pub[0].main_image, (
        "Reprezentativna slika = published_products[0].main_image (mora biti popunjena)."
    )


def test_home_hzm_subcategories_ordered_by_display_order(client, home_url):
    """AC2: hzm_subcategories = HZM radne-masine subcategories (parent=None), ordered
    po display_order. Seed (migracija 0004) ima 4 top-level potkategorije (10/20/30/40).
    """
    activate("sr")
    if get_hzm_category() is None:
        pytest.skip("HZM radne-masine Category nije seed-ovana u test DB (migracija 0004).")

    response = client.get(home_url)
    assert response.status_code == 200

    subs = list(response.context["hzm_subcategories"])
    assert len(subs) == 4, (
        f"HZM radne-masine MORA imati 4 top-level potkategorije (seed 0004), dobio {len(subs)}."
    )
    orders = [s.display_order for s in subs]
    assert orders == sorted(orders), (
        f"hzm_subcategories MORAJU biti ordered po display_order ascending, dobio {orders!r}."
    )


def test_home_latest_posts_is_empty_list(client, home_url):
    """AC2/SM-D7: latest_posts je UVEK prazna lista u v1 (forward-compat blog placeholder)."""
    activate("sr")
    response = client.get(home_url)
    assert response.status_code == 200
    assert response.context["latest_posts"] == [], (
        "SM-D7: latest_posts MORA biti prazna lista [] u v1 (Post model ne postoji; "
        "template grana renderuje Lorem Ipsum placeholder)."
    )


def test_home_empty_hzm_subcategories_when_category_missing(client, home_url):
    """AC2: ako HZM radne-masine Category ne postoji -> hzm_subcategories=[] (NE crash)."""
    activate("sr")
    from apps.brands.models import Category

    # DELETE HZM kategoriju (CASCADE briše i njene subcategories) — simulira missing seed.
    Category.objects.filter(slug="radne-masine", is_for=Category.CategoryScope.MEHANIZACIJA).delete()

    response = client.get(home_url)
    assert response.status_code == 200, (
        "Home MORA preživeti odsutnu HZM kategoriju (defensive guard, NE crash)."
    )
    assert list(response.context["hzm_subcategories"]) == [], (
        "Bez HZM Category, hzm_subcategories MORA biti prazna lista (empty-state render)."
    )


def test_home_view_query_count_constant(client, home_url):
    """AC2/SM-D4 — N+1 GUARD (GLAVNI RIZIK): broj ORM upita protiv katalog tabela
    (brands_*/products_*) MORA biti KONSTANTAN bez obzira na broj Traktori brendova.

    Dokazuje da reprezentativna slika dolazi iz Prefetch(to_attr=...), NE iz per-brand
    .first() upita u petlji/template-u. Sorl-thumbnail KVStore upiti se ISKLJUČUJU iz
    brojanja (mirror Story 2-11 test_leaf_with_images_query_budget) jer skaliraju po
    slici nezavisno od view ORM-a.

    Budžet se zaključava TEK posle GREEN runa (TEA potvrđuje tačan broj). RED: HomeView
    ne postoji -> 404, captured_queries ne odgovara očekivanju -> pad.
    """
    activate("sr")

    def catalog_query_count(brand_count: int) -> int:
        from django.contrib.auth import get_user_model  # noqa: F401  (ensure apps loaded)

        for i in range(brand_count):
            make_traktori_brand(name=f"QC Brend {brand_count}-{i}", with_image=True)
        with CaptureQueriesContext(connection) as captured:
            resp = client.get(home_url)
            assert resp.status_code == 200, (
                "Home mora vratiti 200 da bi N+1 lock bio merljiv (RED: HomeView ne postoji)."
            )
            assert_home_template(resp)
        catalog = [
            q for q in captured.captured_queries
            if "brands_" in q["sql"] or "products_" in q["sql"]
        ]
        return len(catalog)

    count_2 = catalog_query_count(2)
    count_6 = catalog_query_count(6)

    assert count_2 == count_6, (
        "N+1 REGRESIJA: broj katalog ORM upita raste sa brojem brendova "
        f"(2 brenda -> {count_2}, dodatnih 6 -> {count_6}). Reprezentativna slika MORA "
        "doći iz Prefetch(to_attr='published_products'), NE per-brand .first()."
    )


def test_mehanizacija_brand_slug_blacklist_latent_bug(client, home_url):
    """ITEM-1b — ZAKLJUČAVA POZNATO OGRANIČENJE slug-blacklist filtera (SM-D4).

    Traktori sekcija isključuje mehanizaciju kroz HARDCODED `_MEHANIZACIJA_BRAND_SLUGS`
    (jeegee/hzm/tulip). To je PRIVREMENI guardrail vezan za trenutni seed (migracija
    0004 — Tulip condition=NEW default, Brand bez scope diskriminatora).

    LATENTNI BUG koji ovaj test čini VIDLJIVIM: budući mehanizacija brend čiji slug
    NIJE u blacklist-i (ovde 'vogel-noot'), a ima objavljen condition=NEW proizvod bez
    subcategory, BIVA POGREŠNO klasifikovan u Traktori sekciju. Test asertuje TRENUTNO
    (pogrešno) ponašanje da bude zaključano i da regresija (npr. neko doda 'vogel-noot'
    u blacklist umesto da popravi model) ili buduća model-driven ispravka (Brand.scope /
    Product.subcategory filter, story 8-x) eksplicitno OBORI ovaj test — što je signal
    da je TODO u views.py adresiran. Dok god prolazi, gap nije nevidljiv.
    """
    from apps.brands.tests.factories import BrandFactory
    from apps.products.models import Product
    from apps.products.tests.factories import ProductFactory

    activate("sr")

    future_mehanizacija = BrandFactory.create(name="Vogel Noot")
    assert future_mehanizacija.slug == "vogel-noot", (
        "Test pretpostavlja ASCII slug 'vogel-noot' (NIJE u _MEHANIZACIJA_BRAND_SLUGS)."
    )
    assert future_mehanizacija.slug not in ("jeegee", "hzm", "tulip"), (
        "Slug MORA biti VAN hardcoded blacklist-e da reprodukuje latentni bug."
    )
    # Objavljen condition=NEW proizvod BEZ subcategory — mirror Tulip seed (0004) scenario.
    ProductFactory.create(
        brand=future_mehanizacija,
        is_published=True,
        condition=Product.ConditionChoice.NEW,
    )

    response = client.get(home_url)
    assert response.status_code == 200

    brand_ids = {b.pk for b in response.context["traktori_brands"]}
    assert future_mehanizacija.pk in brand_ids, (
        "ITEM-1b LATENT-BUG LOCK: mehanizacija brend van slug-blacklist-e TRENUTNO "
        "(pogrešno) curi u Traktori sekciju jer filter ne razlučuje mehanizaciju od "
        "traktora bez model-driven diskriminatora. Kada se ovaj assert OBORI, znači da "
        "je robusno rešenje (Brand.scope / Product.subcategory filter, story 8-x) "
        "implementirano — ukloni ovaj test i očisti TODO u apps/pages/views.py."
    )


def test_home_view_does_not_write_to_models(client, home_url):
    """AC2/SM-D6: HomeView je READ-ONLY agregacija — nijedan INSERT/UPDATE/DELETE na
    domain tabelama tokom GET render-a.
    """
    activate("sr")
    make_traktori_brand(name="ReadOnly Brend")

    with CaptureQueriesContext(connection) as captured:
        resp = client.get(home_url)
        assert resp.status_code == 200
        assert_home_template(resp)

    write_prefixes = ("INSERT", "UPDATE", "DELETE")
    catalog_writes = [
        q["sql"]
        for q in captured.captured_queries
        if q["sql"].lstrip().upper().startswith(write_prefixes)
        and ("brands_" in q["sql"] or "products_" in q["sql"])
    ]
    assert not catalog_writes, (
        "SM-D6: HomeView NE SME WRITE-ovati domain modele tokom render-a. "
        f"Detektovani write upiti: {catalog_writes!r}"
    )
