"""Story 2.10 — JeegeePrikljucnaView view + context + branching tests (RED phase TDD).

Pokriva AC2 (view CBV + context + query budget) + AC2.5 (coming-soon branching) +
AC2/SM-D7 (Http404 missing brand).

Test scope (5 tests):
- test_context_contains_brand_and_categories
- test_categories_ordered_by_display_order
- test_assert_num_queries_initial_render_under_budget (placeholder; Dev locks empirijski)
- test_coming_soon_jeegee_renders_brand_coming_soon_template
- test_http404_when_jeegee_brand_does_not_exist

Pokrenuti sa:
    docker compose -f compose/local.yml exec django pytest \\
        apps/brands/tests/test_jeegee_prikljucna_view.py -v

Refs:
- 2-10-jeegee-prikljucna-mehanizacija-strana.md (AC2, AC2.5, SM-D7)
- 2-10-interface-contract.md (§ 3 Views)
"""

from __future__ import annotations

import pytest
from django.utils.translation import activate

from apps.brands.models import Brand

pytestmark = pytest.mark.django_db


def test_context_contains_brand_and_categories(client):
    """AC2: context sadrži 'brand' (Jeegee) + 'categories' (3 mehanizacija kategorije)."""
    activate("sr")
    url = "/sr/mehanizacija/prikljucna/"

    response = client.get(url)
    assert response.status_code == 200, (
        "Jeegee brand mora postojati u DB kroz 0003 seed migraciju (pytest-django "
        "auto-applies migracije u --create-db fazi)."
    )

    ctx = response.context
    assert "brand" in ctx, (
        "Context MORA sadržati 'brand' (DetailView default + context_object_name)."
    )
    assert ctx["brand"].slug == "jeegee", (
        f"Context['brand'].slug treba 'jeegee', dobio {ctx['brand'].slug!r}. "
        "JeegeePrikljucnaView.get_object() MORA hardcode-ovati slug='jeegee' lookup."
    )

    assert "categories" in ctx, (
        "Context MORA sadržati 'categories' ključ (3 mehanizacija kategorije queryset)."
    )
    categories = ctx["categories"]
    assert len(categories) == 3, (
        f"Context['categories'] MORA imati TAČNO 3 instance (whitelist osnovna-obrada-"
        f"zemljista + priprema-zemljista + masine-za-setvu), dobio {len(categories)}."
    )

    slugs = {c.slug for c in categories}
    expected_slugs = {
        "osnovna-obrada-zemljista",
        "priprema-zemljista",
        "masine-za-setvu",
    }
    assert slugs == expected_slugs, (
        f"Categories slug-ovi se ne podudaraju sa whitelist-om. "
        f"Očekivano: {expected_slugs!r}, dobijeno: {slugs!r}."
    )


def test_categories_ordered_by_display_order(client):
    """AC2: categories ordering po display_order (10 → 20 → 30) ascending."""
    activate("sr")
    url = "/sr/mehanizacija/prikljucna/"

    response = client.get(url)
    assert response.status_code == 200

    categories = response.context["categories"]
    display_orders = [c.display_order for c in categories]

    assert display_orders == sorted(display_orders), (
        f"Categories MORAJU biti ordered po display_order ascending, dobio: "
        f"{display_orders!r}. JeegeePrikljucnaView.get_context_data() MORA pozvati "
        ".order_by('display_order', 'name') na queryset-u."
    )

    # Specifični očekivani redosled (per 0003 migracija): osnovna-obrada (10) →
    # priprema (20) → masine-za-setvu (30)
    slugs_in_order = [c.slug for c in categories]
    expected_order = [
        "osnovna-obrada-zemljista",
        "priprema-zemljista",
        "masine-za-setvu",
    ]
    assert slugs_in_order == expected_order, (
        f"Categories MORAJU biti u redosledu {expected_order!r}, dobio "
        f"{slugs_in_order!r}."
    )


def test_assert_num_queries_initial_render_under_budget(client, django_assert_num_queries):
    """AC2 (SM-D27 placeholder): pun render = TAČNO 2 SQL upita.

    1. SELECT Brand WHERE slug='jeegee' (get_object)
    2. SELECT Category WHERE is_for='mehanizacija' AND slug IN (...) ORDER BY display_order, name

    Story 2-10 NEMA cross-boundary Product query (NEMA testimonijala, NEMA serija,
    NEMA flat product grid) — view je dramatično lakši nego BrandDetailView (Story 2-6
    koji ima 5 upita). select_related NIJE potreban (NEMA FK relacija na Brand/Category
    koje view koristi u template-u).

    Dev MORA empirijski lock-ovati posle GREEN iter 1 (mirror Story 2-9 SM-D27).
    """
    activate("sr")
    url = "/sr/mehanizacija/prikljucna/"

    # Query budget: 5 = 2 view upita (Brand get_object + Category whitelist)
    #   + SiteSettings chrome (3.4) + RedirectMiddleware seo_redirect lookup (6-4)
    #   + footer latest_blog_posts blog_post LIMIT 3 (5-4). Sve tri chrome upite su
    #   konstantne po request-u (indeksirane). Real N+1 u view-u i dalje obara budget.
    with django_assert_num_queries(5):
        response = client.get(url)
        assert response.status_code == 200


def test_coming_soon_jeegee_renders_brand_coming_soon_template(client):
    """AC2.5: kad jeegee.is_coming_soon=True, get_template_names vraća brand_coming_soon.html.

    Coming-soon path NE fetch-uje categories (get_context_data early return).
    """
    activate("sr")
    # Privremeno set Jeegee kao coming-soon (0003 seed-uje is_coming_soon=False default)
    Brand.objects.filter(slug="jeegee").update(is_coming_soon=True)

    url = "/sr/mehanizacija/prikljucna/"
    response = client.get(url)

    assert response.status_code == 200, (
        f"Coming-soon Jeegee treba HTTP 200 (NE 404), dobio {response.status_code}."
    )

    template_names = [t.name for t in response.templates if t.name]
    assert "brands/brand_coming_soon.html" in template_names, (
        f"Coming-soon Jeegee MORA renderovati 'brands/brand_coming_soon.html' "
        f"(REUSE Story 2-6 deliverable, JeegeePrikljucnaView.get_template_names() "
        f"override). Renderovani template-i: {template_names!r}"
    )
    assert "brands/jeegee_prikljucna.html" not in template_names, (
        "Coming-soon Jeegee NE SME renderovati 'brands/jeegee_prikljucna.html'."
    )

    # Coming-soon path NE fetch-uje categories
    ctx = response.context
    assert "brand" in ctx
    assert ctx.get("categories") in (None, []), (
        f"Coming-soon Jeegee NE SME fetch-ovati categories; "
        f"ctx['categories']={ctx.get('categories')!r}."
    )


def test_http404_when_jeegee_brand_does_not_exist(client):
    """AC2 + SM-D7: Jeegee Brand obrisan iz DB → get_object() raise Http404.

    Defensive guard za scenario gde admin manualno DELETE Jeegee Brand kroz admin GUI
    ili gde data migracija nije primenjena. Http404 message ('Jeegee brand nije
    konfigurisan u sistemu.') surface-uje se SAMO u DEBUG=True dev mode + logs/Sentry;
    production 404 strana koristi Django default template (IMP-1).
    """
    from django.urls import Resolver404, resolve

    activate("sr")
    url = "/sr/mehanizacija/prikljucna/"

    # PRECONDITION: 404 mora doći iz JeegeePrikljucnaView.get_object() Http404 raise
    # (SM-D7), NE iz nerutirane URL putanje. Bez ove provere test bi prošao vacuously
    # u RED fazi (URL pattern ne postoji → 404) bez verifikacije AC2 ponašanja.
    try:
        match = resolve(url)
    except Resolver404:
        pytest.fail(
            f"URL {url} se ne rezolvuje — JeegeePrikljucnaView + apps/brands/urls.py "
            f"pattern još NE postoje (RED phase). Ovaj test verifikuje get_object() "
            f"Http404 raise (SM-D7), NE nerutiran-URL 404; mora pasti dok view ne "
            f"postoji."
        )
    assert match.func.view_class.__name__ == "JeegeePrikljucnaView", (
        f"URL {url} MORA biti mapiran na JeegeePrikljucnaView (AC1), dobio "
        f"{match.func.view_class.__name__!r}. 404 u ovom testu MORA poticati iz "
        f"get_object() Http404 raise-a, ne iz pogrešnog routing-a."
    )

    # DELETE Jeegee Brand — simulira admin GUI deletion ili migracija nije primenjena
    Brand.objects.filter(slug="jeegee").delete()

    response = client.get(url)

    assert response.status_code == 404, (
        f"GET {url} sa OBRISANIM Jeegee brand-om treba HTTP 404 "
        f"(JeegeePrikljucnaView.get_object() explicit Http404 raise per SM-D7), "
        f"dobio {response.status_code}."
    )
