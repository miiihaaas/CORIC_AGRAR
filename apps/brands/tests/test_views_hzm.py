"""Story 2.12 — HzmRadneMasineView view + context + branching tests (RED phase TDD).

Pokriva AC2 (view CBV + context + subcategories + query budget) + coming-soon
branching + Http404 missing brand + empty-subcategories defensive guard.

Pokrenuti sa:
    docker compose -f compose/local.yml run --rm django uv run pytest \\
        apps/brands/tests/test_views_hzm.py -v

Refs:
- 2-12-hzm-radne-masine-tulip-mix-prikolice-strane.md (AC2, Subtask 8.2)
- 2-12-interface-contract.md (§ 2.1 HzmRadneMasineView)
"""

from __future__ import annotations

import pytest
from django.utils.translation import activate

from apps.brands.models import Brand, Category

pytestmark = pytest.mark.django_db

_HZM_URL = "/sr/mehanizacija/radne-masine/"


def test_hzm_context_contains_brand_and_4_subcategories(client):
    """AC2: context sadrži 'brand' (HZM) + 'subcategories' (4 dece radne-masine Category)."""
    activate("sr")
    response = client.get(_HZM_URL)
    assert response.status_code == 200, (
        "HZM brand + radne-masine Category + 4 Subcategory MORAJU biti seed-ovani kroz "
        "0004 migraciju (pytest-django auto-applies migracije)."
    )

    ctx = response.context
    assert "brand" in ctx, "Context MORA sadržati 'brand' (DetailView context_object_name)."
    assert ctx["brand"].slug == "hzm", (
        f"Context['brand'].slug treba 'hzm', dobio {ctx['brand'].slug!r}. get_object() "
        f"MORA hardcode-ovati slug='hzm'."
    )

    assert "subcategories" in ctx, (
        "Context MORA sadržati 'subcategories' ključ (4 dece radne-masine Category-je)."
    )
    subcategories = ctx["subcategories"]
    assert len(subcategories) == 4, (
        f"Context['subcategories'] MORA imati TAČNO 4 instance (mini-utovarivaci + "
        f"utovarivaci-bez-teleskopa + teleskopski-utovarivaci + telehendleri), dobio "
        f"{len(subcategories)}."
    )

    slugs = {s.slug for s in subcategories}
    expected_slugs = {
        "mini-utovarivaci",
        "utovarivaci-bez-teleskopa",
        "teleskopski-utovarivaci",
        "telehendleri",
    }
    assert slugs == expected_slugs, (
        f"Subcategory slug-ovi se ne podudaraju sa seed-om. Očekivano: {expected_slugs!r}, "
        f"dobijeno: {slugs!r}."
    )


def test_hzm_subcategories_ordered_by_display_order(client):
    """AC2: subcategories ordering po display_order (10 → 20 → 30 → 40) ascending."""
    activate("sr")
    response = client.get(_HZM_URL)
    assert response.status_code == 200

    subcategories = response.context["subcategories"]
    display_orders = [s.display_order for s in subcategories]
    assert display_orders == sorted(display_orders), (
        f"Subcategories MORAJU biti ordered po display_order ascending, dobio: "
        f"{display_orders!r}. get_context_data() MORA pozvati "
        f".order_by('display_order', 'name')."
    )

    slugs_in_order = [s.slug for s in subcategories]
    expected_order = [
        "mini-utovarivaci",
        "utovarivaci-bez-teleskopa",
        "teleskopski-utovarivaci",
        "telehendleri",
    ]
    assert slugs_in_order == expected_order, (
        f"Subcategories MORAJU biti u redosledu {expected_order!r}, dobio {slugs_in_order!r}."
    )


def test_hzm_subcategories_are_top_level_children_of_radne_masine(client):
    """AC2: sve 4 Subcategory su parent=None dece radne-masine Category-je."""
    activate("sr")
    response = client.get(_HZM_URL)
    assert response.status_code == 200

    for sub in response.context["subcategories"]:
        assert sub.parent_id is None, (
            f"Subcategory {sub.slug!r} MORA imati parent=None (top-level dete), "
            f"dobio parent_id={sub.parent_id!r}."
        )
        assert sub.category.slug == "radne-masine", (
            f"Subcategory {sub.slug!r} MORA pripadati radne-masine Category-ji, dobio "
            f"{sub.category.slug!r}."
        )


def test_hzm_query_budget_two_queries(client, django_assert_num_queries):
    """AC2 (SM-D empirical-lock placeholder): pun render = 2 SQL upita.

    1. SELECT Brand WHERE slug='hzm' (get_object)
    2. SELECT Subcategory WHERE category=radne-masine AND parent IS NULL ORDER BY ...

    HZM NE query-uje Product → NEMA N+1 rizika. Plus 1 upit za Category lookup u
    get_context_data — Dev empirijski lock-uje TAČAN broj posle GREEN iter 1.
    """
    activate("sr")
    # Story 3.4: 3 view upita + 1 SiteSettings chrome upit (header/footer site_setting, 1/request).
    with django_assert_num_queries(4):
        response = client.get(_HZM_URL)
        assert response.status_code == 200


def test_hzm_coming_soon_renders_brand_coming_soon_template(client):
    """AC2: hzm.is_coming_soon=True → get_template_names vraća brand_coming_soon.html.

    Coming-soon path NE fetch-uje subcategories (early return).
    """
    activate("sr")
    Brand.objects.filter(slug="hzm").update(is_coming_soon=True)

    response = client.get(_HZM_URL)
    assert response.status_code == 200, (
        f"Coming-soon HZM treba HTTP 200, dobio {response.status_code}."
    )

    template_names = [t.name for t in response.templates if t.name]
    assert "brands/brand_coming_soon.html" in template_names, (
        f"Coming-soon HZM MORA renderovati 'brands/brand_coming_soon.html' (REUSE Story "
        f"2-6). Renderovani: {template_names!r}."
    )
    assert "brands/hzm_radne_masine.html" not in template_names, (
        "Coming-soon HZM NE SME renderovati 'brands/hzm_radne_masine.html'."
    )
    assert response.context.get("subcategories") in (None, []), (
        f"Coming-soon HZM NE SME fetch-ovati subcategories; "
        f"ctx['subcategories']={response.context.get('subcategories')!r}."
    )


def test_hzm_404_when_brand_does_not_exist(client):
    """AC2: HZM Brand obrisan → get_object() raise Http404 sa custom porukom."""
    from django.urls import Resolver404, resolve

    activate("sr")

    try:
        match = resolve(_HZM_URL)
    except Resolver404:
        pytest.fail(
            f"URL {_HZM_URL} se ne rezolvuje — HzmRadneMasineView + urls path još NE "
            f"postoje (RED phase). Test verifikuje get_object() Http404, NE nerutiran 404."
        )
    assert match.func.view_class.__name__ == "HzmRadneMasineView", (
        f"URL {_HZM_URL} MORA biti mapiran na HzmRadneMasineView, dobio "
        f"{match.func.view_class.__name__!r}."
    )

    Brand.objects.filter(slug="hzm").delete()
    response = client.get(_HZM_URL)
    assert response.status_code == 404, (
        f"GET {_HZM_URL} sa OBRISANIM HZM brand-om treba HTTP 404 (get_object() Http404 "
        f"raise — 'HZM brand nije konfigurisan u sistemu.'), dobio {response.status_code}."
    )


def test_hzm_empty_subcategories_when_category_missing(client):
    """AC2: radne-masine Category obrisan → subcategories=[] (empty state, NE crash)."""
    activate("sr")
    Category.objects.filter(slug="radne-masine").delete()

    response = client.get(_HZM_URL)
    assert response.status_code == 200, (
        f"GET {_HZM_URL} bez radne-masine Category-je MORA renderovati HTTP 200 "
        f"(defensive empty guard, NE crash), dobio {response.status_code}."
    )
    assert response.context.get("subcategories") == [], (
        f"Kad radne-masine Category ne postoji, subcategories MORA biti [] (empty), dobio "
        f"{response.context.get('subcategories')!r}."
    )
