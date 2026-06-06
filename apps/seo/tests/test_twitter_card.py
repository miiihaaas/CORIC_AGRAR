"""Story 6.3 — Twitter Card meta na svakoj strani (TEA RED, AC3).

Detail strana head ima twitter:card=summary_large_image + twitter:title/description/
image; twitter vrednosti MIRROR-uju og:title/description/image (SM-D1/SEO3-11).

⚠️ RED razlog: seo_head (6-1) NE emituje twitter:* tagove → ODSUTNI dok Dev ne
EXTEND-uje seo_head (Task 4) + ne doda social_meta block u base.html (Task 5).

Refs:
- 6-3-...-meta.md AC3 + Task 4.3/9.3 + SM-D1 + Gotcha SEO3-11
"""

from __future__ import annotations

import re

import pytest
from django.utils.translation import activate

pytestmark = pytest.mark.django_db


def _meta_content(html, prop):
    """Izvuci content atribut meta taga po property= ili name= vrednosti.

    Radi i za og:* (property=) i za twitter:* (name=) tagove.
    """
    m = re.search(
        rf'<meta\s+(?:property|name)="{re.escape(prop)}"\s+content="([^"]*)"',
        html,
        re.IGNORECASE,
    )
    return m.group(1) if m else None


def _product_url(product):
    return f"/sr/proizvod/{product.slug}/"


def test_twitter_card_type_present(client, product):
    """AC3: twitter:card content='summary_large_image'."""
    activate("sr")
    response = client.get(_product_url(product), HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    assert 'name="twitter:card"' in html, (
        "Head MORA imati <meta name=\"twitter:card\"> (AC3)."
    )
    assert 'content="summary_large_image"' in html, (
        "twitter:card MORA biti 'summary_large_image' (AC3/SM-D1)."
    )


def test_twitter_title_description_image_present(client, product):
    """AC3: twitter:title/description/image prisutni."""
    activate("sr")
    response = client.get(_product_url(product), HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    for name in ("twitter:title", "twitter:description", "twitter:image"):
        assert f'name="{name}"' in html, (
            f"Head MORA imati <meta name=\"{name}\"> (AC3)."
        )


def test_twitter_values_mirror_og(client, product):
    """AC3: twitter:title/description/image MIRROR-uju og: vrednosti."""
    from apps.seo.models import SeoMeta

    activate("sr")
    SeoMeta.objects.create(
        content_object=product,
        meta_title_sr="Mirror naslov",
        meta_description_sr="Mirror opis",
    )

    response = client.get(_product_url(product), HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    # twitter:title sadrži istu vrednost kao og:title; isto za description
    assert 'name="twitter:title"' in html and "Mirror naslov" in html, (
        "twitter:title MORA mirror-ovati og:title vrednost (SM-D1/SEO3-11)."
    )
    assert 'name="twitter:description"' in html and "Mirror opis" in html, (
        "twitter:description MORA mirror-ovati og:description vrednost (SEO3-11)."
    )


def test_twitter_image_value_equals_og_image(client, product, png_upload):
    """NM-2 (value-equality lock): twitter:image extracted value MORA biti identičan
    og:image extracted value — ne samo da oba postoje, nego da pokazuju NA ISTI URL.
    Ovo hvata wiring bug gde bi Dev navukao twitter:image iz drugog izvora.
    """
    from apps.seo.models import SeoMeta

    activate("sr")
    seo = SeoMeta.objects.create(content_object=product)
    seo.og_image = png_upload("og_hero.png")
    seo.save()

    response = client.get(_product_url(product), HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    og_image_val = _meta_content(html, "og:image")
    twitter_image_val = _meta_content(html, "twitter:image")

    assert og_image_val is not None, (
        "og:image MORA biti renderovan (AC4) — bez njega NM-2 lock je no-op."
    )
    assert twitter_image_val is not None, (
        "twitter:image MORA biti renderovan (AC3) — bez njega NM-2 lock je no-op."
    )
    assert twitter_image_val == og_image_val, (
        f"twitter:image ({twitter_image_val!r}) MORA biti identičan og:image ({og_image_val!r}) "
        "— oba MORAJU pokazivati na isti URL (SM-D1/SEO3-11 value-equality, NM-2)."
    )
