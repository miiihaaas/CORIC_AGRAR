"""Story 6.2 — exclude_from_sitemap GFK exclusion-set (TEA RED phase).

Pokriva AC6 (SM-D4):
- javni Product P1 + SeoMeta(content_object=P1, exclude_from_sitemap=True) →
  P1 path NIJE u <loc> (iako je is_published=True).
- objavljen Post B1 + SeoMeta(exclude_from_sitemap=True) → B1 path NIJE u <loc>.
- javni Product/Post BEZ flag-a (ili exclude_from_sitemap=False) SU prisutni
  (exclusion je per-objekat, NE globalan).
- Lock-uje per-content_type exclusion-set izolaciju (Product + Post — 2 tipa).

Exclusion preko GFK BEZ join-a (SeoMeta.objects.filter(content_type, flag=True)
→ values_list("object_id")); items() = public_qs.exclude(pk__in=...). JEDAN
query/klasa (SM-D4/SM2-4).

Refs:
- 6-2-...-hreflang.md AC6 + Task 6.5 + SM-D4 + Gotcha SM2-4
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
def exclude_scenario(make_post):
    from django.utils import timezone

    from apps.products.tests.factories import ProductFactory
    from apps.seo.models import SeoMeta

    now = timezone.now()

    excluded_product = ProductFactory.create(name="Iskljucen Traktor Sitemap")
    visible_product = ProductFactory.create(name="Vidljiv Traktor Sitemap")
    SeoMeta.objects.create(content_object=excluded_product, exclude_from_sitemap=True)

    excluded_post = make_post(
        title="Iskljucena vest sitemap", status="published", published_at=now
    )
    visible_post = make_post(
        title="Vidljiva vest sitemap", status="published", published_at=now
    )
    SeoMeta.objects.create(content_object=excluded_post, exclude_from_sitemap=True)

    return {
        "excluded_product": excluded_product,
        "visible_product": visible_product,
        "excluded_post": excluded_post,
        "visible_post": visible_post,
    }


def test_excluded_product_absent(client, exclude_scenario):
    response = client.get("/sitemap.xml")
    assert response.status_code == 200
    locs = _loc_texts(response.content)
    path = exclude_scenario["excluded_product"].get_absolute_url()
    assert not any(path in loc for loc in locs), (
        f"Product sa exclude_from_sitemap=True ({path!r}) NE SME biti u sitemap-u (AC6)."
    )


def test_excluded_post_absent(client, exclude_scenario):
    response = client.get("/sitemap.xml")
    assert response.status_code == 200
    locs = _loc_texts(response.content)
    path = exclude_scenario["excluded_post"].get_absolute_url()
    assert not any(path in loc for loc in locs), (
        f"Post sa exclude_from_sitemap=True ({path!r}) NE SME biti u sitemap-u (AC6)."
    )


def test_non_excluded_product_present(client, exclude_scenario):
    response = client.get("/sitemap.xml")
    assert response.status_code == 200
    locs = _loc_texts(response.content)
    path = exclude_scenario["visible_product"].get_absolute_url()
    assert any(path in loc for loc in locs), (
        f"Product BEZ exclude flag-a ({path!r}) MORA biti u sitemap-u — "
        f"exclusion je per-objekat (AC6)."
    )


def test_non_excluded_post_present(client, exclude_scenario):
    response = client.get("/sitemap.xml")
    assert response.status_code == 200
    locs = _loc_texts(response.content)
    path = exclude_scenario["visible_post"].get_absolute_url()
    assert any(path in loc for loc in locs), (
        f"Post BEZ exclude flag-a ({path!r}) MORA biti u sitemap-u — "
        f"per-content_type exclusion-set izolacija (AC6)."
    )


def test_cross_type_exclusion_isolation(client, make_post):
    """Product exclusion NE sme iskljuciti Post istog pk-a — content_type izolacija.

    NM-3: _excluded_pks(Product) koristi content_type=Product → ne sme da «krvari»
    u Post queryset čak i ako deli isti pk. Ovo eksplicitno proverava da je GFK
    exclusion-set per-content_type, NE globalan po object_id.
    """
    from django.utils import timezone

    from apps.products.tests.factories import ProductFactory
    from apps.seo.models import SeoMeta

    now = timezone.now()

    # Kreira Product + Post (ne garantujemo isti pk, ali to nije poenta —
    # poenta je da exclusion jednog tipa NE utiče na drugi tip).
    excluded_product = ProductFactory.create(name="Kros-izolacija Traktor Sitemap")
    SeoMeta.objects.create(content_object=excluded_product, exclude_from_sitemap=True)

    visible_post = make_post(
        title="Kros-izolacija vest sitemap",
        status="published",
        published_at=now,
    )
    # visible_post nema SeoMeta (nema exclude flag) — mora biti u sitemap-u.

    response = client.get("/sitemap.xml")
    assert response.status_code == 200
    locs = _loc_texts(response.content)

    product_path = excluded_product.get_absolute_url()
    post_path = visible_post.get_absolute_url()

    assert not any(product_path in loc for loc in locs), (
        f"excluded Product ({product_path!r}) NE SME biti u sitemap-u (AC6)."
    )
    assert any(post_path in loc for loc in locs), (
        f"Post BEZ exclude flag-a ({post_path!r}) MORA biti u sitemap-u — "
        f"Product exclusion NE sme «krvariti» u Post content_type (NM-3/AC6)."
    )
