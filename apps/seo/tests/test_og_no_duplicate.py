"""Story 6.3 — NO-DUPLICATE lock na full-page detail render (TEA RED, AC6).

Detail strana override-uje ISTI {% block social_meta %} koji base default-uje
(site-level) → child override zamenjuje base default → TAČNO JEDAN set OG. Lock:
- property="og:title" == 1
- rel="canonical" == 1
- <title == 1 (6-1 SM-D2 NO-DUPLICATE-<title> očuvan)
- property="og:image" == 1

⚠️ RED razlog: pre Dev impl, detail strana NEMA OG uopšte (og:title==0 != 1) →
RED. Posle nedovršene migracije (C2 — seo_head ostane i u extra_head I u social_meta)
ovaj test bi uhvatio duplikat (==2 != 1). Lock-uje SM-D1 child-override semantiku.

count na decoded full-page response (client.get → kroz base.html → base+child
interakcija; izolovan tag render NE bi pokazao duplikat hazard).

Refs:
- 6-3-...-meta.md AC6 + Task 6/9.5 + SM-D1 + Gotcha SEO3-1/SEO3-9
"""

from __future__ import annotations

import pytest
from django.utils.translation import activate

pytestmark = pytest.mark.django_db


def _product_url(product):
    return f"/sr/proizvod/{product.slug}/"


def _post_url(post):
    return f"/sr/blog/{post.slug}/"


def test_product_detail_no_duplicate_og_or_canonical_or_title(client, product):
    """AC6: og:title==1, canonical==1, <title==1, og:image==1 na product detail."""
    activate("sr")
    response = client.get(_product_url(product), HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    assert html.count('property="og:title"') == 1, (
        f"property=\"og:title\" MORA biti TAČNO 1× (child override zamenjuje base "
        f"default, NE dodaje); pronađeno {html.count('property=\"og:title\"')} (SM-D1)."
    )
    assert html.count('rel="canonical"') == 1, (
        f"rel=\"canonical\" MORA biti TAČNO 1×; pronađeno {html.count('rel=\"canonical\"')} "
        "(seo_head SAMO u social_meta block-u — C2/SEO3-9)."
    )
    assert html.count("<title") == 1, (
        f"<title MORA biti TAČNO 1× (6-1 SM-D2 NO-DUPLICATE-<title> očuvan); "
        f"pronađeno {html.count('<title')}."
    )
    assert html.count('property="og:image"') == 1, (
        f"property=\"og:image\" MORA biti TAČNO 1×; pronađeno {html.count('property=\"og:image\"')} "
        "(NO-DUPLICATE lock — SM-D1)."
    )


def test_post_detail_no_duplicate_og_or_canonical_or_title(client, post):
    """AC6: isti NO-DUPLICATE lock na blog post detail (drugi detail tip)."""
    activate("sr")
    response = client.get(_post_url(post), HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    assert html.count('property="og:title"') == 1
    assert html.count('rel="canonical"') == 1
    assert html.count("<title") == 1
    assert html.count('property="og:image"') == 1
