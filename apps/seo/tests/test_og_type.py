"""Story 6.3 — og:type article-vs-website duck-type (TEA RED, AC7).

Post (ima published_at) → og:type='article'; Product/Brand (nemaju) → 'website';
obj=None (site-level) → 'website'. Rezolucija je duck-type
`getattr(obj, "published_at", None)` (NE isinstance/import Post — low-coupling SM-D5).

⚠️ RED razlog: seo_head (6-1) NE emituje og:type uopšte → ODSUTNO dok Dev ne doda
_og_type helper + og:type emit (Task 3/4).

Refs:
- 6-3-...-meta.md AC7 + Task 3/9.6 + SM-D5 + Gotcha SEO3-8
"""

from __future__ import annotations

import re

import pytest
from django.utils.translation import activate

pytestmark = pytest.mark.django_db


def _og_type_content(html):
    m = re.search(r'<meta\s+property="og:type"\s+content="([^"]*)"', html, re.IGNORECASE)
    return m.group(1) if m else None


def test_post_detail_og_type_is_article(client, post):
    """AC7: blog Post detail (ima published_at) → og:type='article'."""
    activate("sr")
    response = client.get(f"/sr/blog/{post.slug}/", HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    assert _og_type_content(html) == "article", (
        "Post (ima published_at) → og:type MORA biti 'article' (duck-type — AC7/SM-D5)."
    )


def test_product_detail_og_type_is_website(client, product):
    """AC7: Product detail (nema published_at) → og:type='website'."""
    activate("sr")
    response = client.get(f"/sr/proizvod/{product.slug}/", HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    assert _og_type_content(html) == "website", (
        "Product (nema published_at) → og:type MORA biti 'website' (AC7/SM-D5)."
    )


def test_brand_detail_og_type_is_website(client, brand):
    """AC7: Brand detail (nema published_at) → og:type='website'."""
    activate("sr")
    response = client.get(f"/sr/traktori/{brand.slug}/", HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    assert _og_type_content(html) == "website", (
        "Brand (nema published_at) → og:type MORA biti 'website' (AC7/SM-D5)."
    )


def test_site_level_og_type_is_website(client):
    """AC7: obj=None (home) → og:type='website' (getattr None → None → website)."""
    activate("sr")
    response = client.get("/sr/", HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    assert _og_type_content(html) == "website", (
        "site-level (obj=None) → og:type MORA biti 'website' (AC7/SM-D5)."
    )
