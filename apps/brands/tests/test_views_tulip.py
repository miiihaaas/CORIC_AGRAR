"""Story 2.12 — TulipMixPrikoliceView view + context + spec_rows + N+1 guard (RED phase).

Pokriva AC3: brand/products/spec_rows/testimonials context, price ordering,
spec_rows transponovanje (SM-D7), missing-value None, coming-soon, Http404,
N+1 query budget (SM-D14 — Prefetch ordered queryset NIJE pobijen).

Pokrenuti sa:
    docker compose -f compose/local.yml run --rm django uv run pytest \\
        apps/brands/tests/test_views_tulip.py -v

Refs:
- 2-12-hzm-radne-masine-tulip-mix-prikolice-strane.md (AC3, Subtask 8.3)
- 2-12-interface-contract.md (§ 2.2 TulipMixPrikoliceView)
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils.translation import activate

from apps.brands.models import Brand
from apps.products.models import Product, ProductSpecification

pytestmark = pytest.mark.django_db

_TULIP_URL = "/sr/mehanizacija/mix-prikolice/"


def _tulip_brand() -> Brand:
    return Brand.objects.get(slug="tulip")


def test_tulip_context_contains_brand_products_spec_rows_testimonials(client):
    """AC3: context sadrži 'brand' (Tulip) + 'products' + 'spec_rows' + 'testimonials'."""
    activate("sr")
    response = client.get(_TULIP_URL)
    assert response.status_code == 200, (
        "Tulip brand + 2 Product + 8 ProductSpecification MORAJU biti seed-ovani kroz 0004."
    )

    ctx = response.context
    assert ctx["brand"].slug == "tulip", (
        f"Context['brand'].slug treba 'tulip', dobio {ctx['brand'].slug!r}."
    )
    assert "products" in ctx and len(ctx["products"]) == 2, (
        f"Context['products'] MORA imati TAČNO 2 Tulip modela (6 m³ + 8 m³), dobio "
        f"{len(ctx.get('products', []))}."
    )
    assert "spec_rows" in ctx, "Context MORA sadržati 'spec_rows' (transponovan SM-D7)."
    assert "testimonials" in ctx, "Context MORA sadržati 'testimonials' ključ."


def test_tulip_products_ordered_by_price(client):
    """AC3: products ordered by price_eur — 6 m³ (6500) PRE 8 m³ (8200).

    PRIMARNI sort ključ je price_eur deterministički (seed 6500 < 8200), NE string
    fallback na name.
    """
    activate("sr")
    response = client.get(_TULIP_URL)
    assert response.status_code == 200

    products = response.context["products"]
    prices = [p.price_eur for p in products]
    assert prices == sorted(prices), (
        f"Products MORAJU biti ordered po price_eur ascending, dobio {prices!r}. "
        f"get_context_data() MORA .order_by('price_eur', 'name')."
    )
    assert products[0].slug == "tulip-mix-6m3", (
        f"Prvi product (jeftiniji 6 m³) MORA biti 'tulip-mix-6m3', dobio "
        f"{products[0].slug!r}."
    )
    assert products[1].slug == "tulip-mix-8m3", (
        f"Drugi product (skuplji 8 m³) MORA biti 'tulip-mix-8m3', dobio {products[1].slug!r}."
    )


def test_spec_rows_transposed_correctly(client):
    """AC3 + SM-D7: spec_rows je transponovan — prvi red Zapremina sa values 6 m³/8 m³."""
    activate("sr")
    response = client.get(_TULIP_URL)
    assert response.status_code == 200

    spec_rows = response.context["spec_rows"]
    assert len(spec_rows) >= 1, "spec_rows MORA imati bar 1 red (Zapremina)."

    first = spec_rows[0]
    assert first["key"] == "Zapremina", (
        f"Prvi spec_row key MORA biti 'Zapremina' (order=0 u seed-u), dobio {first['key']!r}."
    )
    assert first["values"] == ["6 m³", "8 m³"], (
        f"Zapremina red MORA imati values ['6 m³', '8 m³'] (side-by-side po price ordering), "
        f"dobio {first['values']!r}. SM-D7 transponovanje: red = key + lista vrednosti po "
        f"modelu istim redosledom kao products."
    )


def test_spec_rows_missing_value_yields_none(client):
    """AC3 + SM-D7: model bez nekog spec key-a → None u values (template → '—').

    Dodaj spec key 'Težina' SAMO na 6 m³ model; spec_rows red 'Težina' MORA imati
    None u koloni 8 m³ modela.
    """
    activate("sr")
    p6 = Product.objects.get(slug="tulip-mix-6m3")
    ProductSpecification.objects.create(
        product=p6, section="ostalo", key="Težina", value="3200 kg", order=10
    )

    response = client.get(_TULIP_URL)
    assert response.status_code == 200

    spec_rows = response.context["spec_rows"]
    tezina = next((r for r in spec_rows if r["key"] == "Težina"), None)
    assert tezina is not None, "spec_rows MORA sadržati red 'Težina' (key sa 6 m³ modela)."
    assert tezina["values"][0] == "3200 kg", (
        f"6 m³ kolona za Težina MORA biti '3200 kg', dobio {tezina['values'][0]!r}."
    )
    assert tezina["values"][1] is None, (
        f"8 m³ model NEMA 'Težina' spec → values[1] MORA biti None (template renderuje "
        f"'—'), dobio {tezina['values'][1]!r}."
    )


def test_tulip_coming_soon_renders_brand_coming_soon(client):
    """AC3: tulip.is_coming_soon=True → brand_coming_soon.html; NE fetch products."""
    activate("sr")
    Brand.objects.filter(slug="tulip").update(is_coming_soon=True)

    response = client.get(_TULIP_URL)
    assert response.status_code == 200

    template_names = [t.name for t in response.templates if t.name]
    assert "brands/brand_coming_soon.html" in template_names, (
        f"Coming-soon Tulip MORA renderovati 'brands/brand_coming_soon.html'. "
        f"Renderovani: {template_names!r}."
    )
    assert "brands/tulip_mix_prikolice.html" not in template_names, (
        "Coming-soon Tulip NE SME renderovati 'brands/tulip_mix_prikolice.html'."
    )
    assert response.context.get("products") in (None, []), (
        "Coming-soon Tulip NE SME fetch-ovati products."
    )


def test_tulip_404_when_brand_does_not_exist(client):
    """AC3: Tulip Brand obrisan → get_object() raise Http404.

    PROTECT FK Product.brand → moramo obrisati Product-e PRE Brand-a.
    """
    from django.urls import Resolver404, resolve

    activate("sr")
    try:
        match = resolve(_TULIP_URL)
    except Resolver404:
        pytest.fail(
            f"URL {_TULIP_URL} se ne rezolvuje — TulipMixPrikoliceView još NE postoji "
            f"(RED phase). Test verifikuje get_object() Http404."
        )
    assert match.func.view_class.__name__ == "TulipMixPrikoliceView"

    # Product.brand je PROTECT — obriši Tulip products + brand
    Product.objects.filter(brand__slug="tulip").delete()
    Brand.objects.filter(slug="tulip").delete()

    response = client.get(_TULIP_URL)
    assert response.status_code == 404, (
        f"GET {_TULIP_URL} sa OBRISANIM Tulip brand-om treba HTTP 404 ('Tulip brand nije "
        f"konfigurisan u sistemu.'), dobio {response.status_code}."
    )


def test_tulip_no_testimonials_yields_empty_list(client):
    """AC3: 0 testimonijala (seed ih ne kreira) → testimonials=[]."""
    activate("sr")
    response = client.get(_TULIP_URL)
    assert response.status_code == 200

    testimonials = response.context["testimonials"]
    assert list(testimonials) == [], (
        f"Bez seed-ovanih testimonijala, testimonials MORA biti prazna lista, dobio "
        f"{list(testimonials)!r}."
    )


def test_tulip_view_query_count_constant_with_more_products(client):
    """AC3 + SM-D14: query count KONSTANTAN bez obzira na broj proizvoda (N+1 guard).

    Meri query count za 2 seeded proizvoda, zatim dodaje 3. proizvod sa 5
    specifikacija i ponovo meri. Ako broj upita RASTE → Prefetch(queryset=...order_by)
    je POBIJEN per-product .order_by() (SM-D14 greška) → budget se NE sme lock-ovati.

    Ovaj test ZAKLJUČAVA query budget AC3.
    """
    activate("sr")

    # Baseline: 2 seeded proizvoda
    with CaptureQueriesContext(connection) as ctx_baseline:
        response = client.get(_TULIP_URL)
        assert response.status_code == 200
    baseline_count = len(ctx_baseline)

    # Dodaj 3. proizvod sa 5 specifikacija (skuplji da ne menja ordering invariant)
    tulip = _tulip_brand()
    p3 = Product.objects.create(
        brand=tulip,
        name="Tulip MIX 10 m³",
        is_published=True,
        status=Product.StatusChoice.PUBLISHED,
        price_eur=Decimal("9900.00"),
        key_features=["Zapremina 10 m³"],
    )
    for i in range(5):
        ProductSpecification.objects.create(
            product=p3, section="ostalo", key=f"Spec {i}", value=f"Val {i}", order=i
        )

    with CaptureQueriesContext(connection) as ctx_more:
        response = client.get(_TULIP_URL)
        assert response.status_code == 200
    more_count = len(ctx_more)

    assert more_count == baseline_count, (
        f"Query count MORA biti KONSTANTAN (SM-D14 N+1 guard): 2 proizvoda → "
        f"{baseline_count} upita, 3 proizvoda + 5 specs → {more_count} upita. Ako raste, "
        f"Prefetch(queryset=ProductSpecification.objects.order_by('order','id')) je "
        f"POBIJEN per-product .order_by() u _build_spec_rows. Koristi .all() BEZ "
        f".order_by() da čitaš prefetch cache."
    )


def test_spec_rows_uses_prefetched_specifications_no_extra_query(client):
    """AC3 + SM-D14: _build_spec_rows čita iz prefetch cache-a (NE generiše nove upite).

    Lock-uje TAČAN query budget na ~4 upita (Brand get_object + Product list + prefetch
    specifications + ProductTestimonial). Dev empirijski lock-uje broj posle GREEN.
    """
    activate("sr")
    with CaptureQueriesContext(connection) as ctx:
        response = client.get(_TULIP_URL)
        assert response.status_code == 200

    query_count = len(ctx)
    # Konstantan, mali broj — prefetch znači per-product specs NE generišu dodatne upite.
    # Budget: ~4 view upita (Brand + Product + prefetch specs + testimonials) + 3 chrome
    # upita konstantna po request-u: SiteSettings (3.4) + RedirectMiddleware seo_redirect
    # lookup (6-4) + footer latest_blog_posts blog_post LIMIT 3 (5-4). Ceiling 8 (ostavlja
    # 1 upit slack-a). Real N+1 (pobijen prefetch, per-product spec query) probija ceiling.
    assert query_count <= 8, (
        f"Tulip view MORA imati mali konstantan query budget (Brand + Product + prefetch "
        f"specs + testimonials ≈ 4 + 3 chrome upita po request-u), dobio {query_count}. Ako "
        f"je veliki, prefetch je pobijen ili nedostaje."
    )
