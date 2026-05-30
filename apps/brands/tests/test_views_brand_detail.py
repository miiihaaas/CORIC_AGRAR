"""Story 2.6 — BrandDetailView + URL routing tests (RED phase TDD).

Pokriva AC1 (URL routing) + AC2 (view query optimization + context + coming-soon path).

Test scope (9 tests):
- AC1 URL routing: 5 tests (sr/hu/en locale resolve + 404 + APPEND_SLASH redirect)
- AC2 view + queries: 4 tests (context keys + assertNumQueries(5) + coming-soon path + 404 unpublished)

Naming: srpska latinica + engleski code identifiers (per project-context.md).
TEA RED phase: SVI testovi MORAJU pasti dok Dev ne implementira BrandDetailView, urls, templates.

Pokrenuti sa:
    docker compose -f compose/local.yml exec django uv run pytest \\
        apps/brands/tests/test_views_brand_detail.py -v

Refs:
- 2-6-brand-listing-strana-sa-grid-extended-layout-om.md (story spec, AC1 + AC2)
- 2-6-interface-contract.md (TEA canonical contract — Dev MUST satisfy)
"""

from __future__ import annotations

import pytest
from django.conf import settings
from django.urls import reverse
from django.utils.translation import activate

from apps.brands.tests.factories import BrandFactory, SeriesFactory
from apps.products.tests.factories import (
    ProductFactory,
    ProductSpecificationFactory,
    ProductTestimonialFactory,
)

pytestmark = pytest.mark.django_db


# =============================================================================
# AC1 — URL routing: sr/hu/en locale resolve + 404 + APPEND_SLASH redirect
# =============================================================================


def test_brand_detail_url_resolves_sr_locale(client):
    """AC1: /sr/traktori/<slug>/ vraća HTTP 200 za postojeći brend."""
    activate("sr")
    brand = BrandFactory.create(name="Agri Tracking")
    url = f"/sr/traktori/{brand.slug}/"

    response = client.get(url)

    assert response.status_code == 200, (
        f"GET {url} treba HTTP 200 za postojeći brend, dobio {response.status_code}. "
        "Dev mora kreirati BrandDetailView + apps/brands/urls.py + wire u config/urls.py."
    )


def test_brand_detail_url_resolves_hu_locale(client):
    """AC1: /hu/traktori/<slug>/ vraća HTTP 200 (i18n_patterns)."""
    activate("hu")
    brand = BrandFactory.create(name="Agri Tracking")
    url = f"/hu/traktori/{brand.slug}/"

    response = client.get(url)

    assert response.status_code == 200, (
        f"GET {url} treba HTTP 200 (i18n_patterns multi-locale), dobio {response.status_code}. "
        "URL pattern MORA biti include-ovan UNUTAR i18n_patterns(...) blok-a u config/urls.py."
    )


def test_brand_detail_url_resolves_en_locale(client):
    """AC1: /en/traktori/<slug>/ vraća HTTP 200 (i18n_patterns)."""
    activate("en")
    brand = BrandFactory.create(name="Agri Tracking")
    url = f"/en/traktori/{brand.slug}/"

    response = client.get(url)

    assert response.status_code == 200, (
        f"GET {url} treba HTTP 200, dobio {response.status_code}."
    )


def test_brand_detail_404_for_nonexistent_slug(client):
    """AC1: /sr/traktori/nepostojeci-slug/ vraća HTTP 404 KROZ DetailView (NE catch-all 404).

    Mora prvo potvrditi da URL pattern POSTOJI (reverse rezolvuje) — tek onda nepostojeći
    slug daje 404 kroz DetailView.get_object_or_404. Bez URL pattern-a, ovaj test bi se
    trivially passed (svaki nepoznat URL je 404), pa koristimo django.urls.reverse() da
    osiguramo URL name 'brands:detail' postoji.
    """
    from django.urls import NoReverseMatch, reverse

    activate("sr")
    # Sanity: URL name MORA biti registrovan
    try:
        reverse("brands:detail", kwargs={"slug": "nepostojeci-slug-koji-sigurno-ne-postoji"})
    except NoReverseMatch:
        pytest.fail(
            "URL name 'brands:detail' nije registrovan. Dev mora kreirati apps/brands/urls.py "
            "sa app_name='brands' + path('traktori/<slug:slug>/', ..., name='detail') i "
            "include u i18n_patterns u config/urls.py."
        )

    url = "/sr/traktori/nepostojeci-slug-koji-sigurno-ne-postoji/"
    response = client.get(url)

    assert response.status_code == 404, (
        f"GET {url} (nepostojeći brand slug, ali URL pattern POSTOJI) treba HTTP 404 "
        f"(DetailView.get_object_or_404), dobio {response.status_code}."
    )


def test_append_slash_redirect_for_missing_trailing_slash(client):
    """AC1: GET /sr/traktori/<slug> (BEZ trailing slash) treba APPEND_SLASH redirect."""
    activate("sr")
    brand = BrandFactory.create(name="Agri Tracking")
    url_no_slash = f"/sr/traktori/{brand.slug}"  # bez završnog /

    response = client.get(url_no_slash)

    # Django CommonMiddleware sa APPEND_SLASH=True (default) → 301 redirect na sa-slash URL
    assert response.status_code in (301, 302), (
        f"GET {url_no_slash} treba APPEND_SLASH redirect (301 ili 302), dobio {response.status_code}. "
        "Verifikuj da CommonMiddleware aktivan u MIDDLEWARE setting + APPEND_SLASH=True."
    )


# =============================================================================
# AC2 — View + queries + context + coming-soon branching
# =============================================================================


def test_context_contains_brand_and_testimonials_only(client):
    """AC2 (I2 fix): context sadrži `brand` + `testimonials` ključeve; NEMA `series_list`.

    Template treba pristupati seriji kroz `brand.series.all` (prefetched relation),
    NE kroz odvojen `series_list` ključ.
    """
    activate("sr")
    brand = BrandFactory.create(name="Agri Tracking")
    SeriesFactory.create_grid(brand=brand, name="Grid Serija")
    url = f"/sr/traktori/{brand.slug}/"

    response = client.get(url)

    assert response.status_code == 200
    ctx = response.context
    assert "brand" in ctx, "Context MORA sadržati 'brand' (DetailView default + context_object_name)."
    assert ctx["brand"].pk == brand.pk, (
        f"Context['brand'].pk={ctx['brand'].pk!r} ne matchuje očekivan brand.pk={brand.pk!r}."
    )
    assert "testimonials" in ctx, (
        "Context MORA sadržati 'testimonials' ključ za not-coming-soon brendove "
        "(BrandDetailView.get_context_data() override)."
    )
    assert "series_list" not in ctx, (
        "Context NE SME sadržati 'series_list' (I2 fix — template pristupa kroz brand.series.all)."
    )


def test_assert_num_queries_equals_5(client, django_assert_num_queries):
    """AC2 (I1 fix): pun render strane = TAČNO 5 SQL upita (brand + serije + produkti + spec + testimonijali).

    Prefetch chain mora biti N+1-free:
    1. SELECT Brand (DetailView get_object)
    2. SELECT Series WHERE brand_id IN (...) (prefetch)
    3. SELECT Product WHERE series_id IN (...) AND is_published=True (prefetch + filter)
    4. SELECT ProductSpecification WHERE product_id IN (...) (prefetch + annotate Case/When)
    5. SELECT ProductTestimonial JOIN Product WHERE brand_id=? AND is_published=True (filter + select_related)
    """
    activate("sr")
    brand = BrandFactory.create(name="Agri Tracking")
    grid_series = SeriesFactory.create_grid(brand=brand, name="Grid Serija")
    ext_series = SeriesFactory.create_extended(brand=brand, name="Extended Serija")
    p1 = ProductFactory.create(brand=brand, series=grid_series, name="Model A")
    p2 = ProductFactory.create(brand=brand, series=grid_series, name="Model B")
    p3 = ProductFactory.create(brand=brand, series=ext_series, name="Model C")
    ProductSpecificationFactory.create(product=p3, section="motor", key="Snaga")
    ProductSpecificationFactory.create(product=p3, section="transmisija", key="Brzina")
    ProductTestimonialFactory.create(product=p1, author_name="Marko")
    ProductTestimonialFactory.create(product=p2, author_name="Stojan")

    url = f"/sr/traktori/{brand.slug}/"

    # Django Client GET wraps full request/response cycle; assertNumQueries
    # broji samo DB query-je (ne template render — koji ne radi query-je kroz prefetched relations).
    with django_assert_num_queries(5):
        response = client.get(url)
        assert response.status_code == 200

    # Ako test pokupi više od 5 query-ja, prefetch chain je BROKEN (N+1 svako iteriranje
    # brand.series.all → series.products.all → product.specifications.all dodaje query po item-u).


def test_coming_soon_brand_renders_brand_coming_soon_template(client):
    """AC2 + AC2.5: brand sa is_coming_soon=True renderuje brand_coming_soon.html (SM-D19)."""
    activate("sr")
    brand = BrandFactory.create_coming_soon(name="Future Brand")
    url = f"/sr/traktori/{brand.slug}/"

    response = client.get(url)

    assert response.status_code == 200, (
        f"Coming-soon brand treba HTTP 200 (SM-D4 — NE 404), dobio {response.status_code}."
    )
    # assertTemplateUsed verifikuje da je render-ovan TAČNO coming_soon template
    template_names = [t.name for t in response.templates if t.name]
    assert "brands/brand_coming_soon.html" in template_names, (
        f"Coming-soon brand MORA renderovati 'brands/brand_coming_soon.html' "
        f"(BrandDetailView.get_template_names() override per SM-D19). "
        f"Renderovani template-i: {template_names!r}"
    )
    assert "brands/brand_detail.html" not in template_names, (
        "Coming-soon brand NE SME renderovati 'brands/brand_detail.html'."
    )
    # Coming-soon path NE fetch-uje testimonijale (get_context_data early return)
    ctx = response.context
    assert "brand" in ctx
    # `testimonials` NIJE u context-u (ili je prazan/odsutan — early return);
    # akceptujemo oba interpretacije (Dev može vratiti super().get_context_data()
    # koji nema testimonials key).
    assert ctx.get("testimonials") in (None, []), (
        f"Coming-soon brand NE SME fetch-ovati testimonijale; ctx['testimonials']={ctx.get('testimonials')!r}."
    )


def test_404_when_brand_does_not_exist(client):
    """AC2: nepostojeći brand slug → DetailView.get_object_or_404 raise-uje Http404.

    Verifikuje da URL pattern POSTOJI (reverse rezolvuje) pre nego testira 404 path —
    tako se sprečava trivijalni "default 404 jer URL nema match" prolaz testa.
    """
    from django.urls import NoReverseMatch, reverse

    activate("sr")
    # Sanity: URL name MORA biti registrovan
    try:
        reverse("brands:detail", kwargs={"slug": "test"})
    except NoReverseMatch:
        pytest.fail(
            "URL name 'brands:detail' nije registrovan — Dev mora kreirati URL pattern pre "
            "ovog testa."
        )

    # BEZ kreiranja brand-a; URL pattern matchuje ali DetailView ne nađe Brand u DB → 404
    url = "/sr/traktori/ovaj-brand-stvarno-ne-postoji-12345/"
    response = client.get(url)

    assert response.status_code == 404
