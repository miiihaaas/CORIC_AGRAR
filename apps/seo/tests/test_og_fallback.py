"""Story 6.3 — og:image fallback ↔ object og_image (TEA RED, AC4).

Lock OBE grane:
- detail objekat BEZ SeoMeta.og_image → og:image SADRŽI 'og-default.jpg' (fallback).
- detail objekat SA SeoMeta.og_image → og:image == upload URL (NE og-default).
og:image je UVEK prisutan (BEHAVIOR CHANGE od 6-1 — SM-D3/AC4).

⚠️ RED razlog: 6-1 seo_head emituje og:image SAMO kad og_image postoji (`if seo and
seo.og_image:`). Bez og_image → NEMA og:image (fallback grana NE postoji) →
fallback test RED dok Dev ne učini og:image UVEK prisutnim sa og-default fallback-om.

Refs:
- 6-3-...-meta.md AC4 + Task 4.2/9.4 + SM-D3/D6 + Gotcha SEO3-4/SEO3-10
"""

from __future__ import annotations

import re

import pytest
from django.utils.translation import activate

pytestmark = pytest.mark.django_db


def _product_url(product):
    return f"/sr/proizvod/{product.slug}/"


def _og_image_content(html):
    m = re.search(r'<meta\s+property="og:image"\s+content="([^"]*)"', html, re.IGNORECASE)
    return m.group(1) if m else None


def test_og_image_falls_back_to_default_when_no_og_image(client, product):
    """AC4: detail bez SeoMeta.og_image → og:image SADRŽI og-default.jpg."""
    activate("sr")
    response = client.get(_product_url(product), HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    content = _og_image_content(html)
    assert content is not None, (
        "og:image MORA biti UVEK prisutan (BEHAVIOR CHANGE — SM-D3/AC4)."
    )
    assert "og-default" in content, (
        "Bez SeoMeta.og_image → og:image MORA biti static('img/og-default.jpg') fallback; "
        f"dobio content={content!r} (AC4/SM-D6)."
    )


def test_og_image_uses_object_image_when_set(client, product, png_upload):
    """AC4: detail SA SeoMeta.og_image → og:image == upload URL (NE og-default)."""
    from apps.seo.models import SeoMeta

    activate("sr")
    seo = SeoMeta.objects.create(content_object=product)
    seo.og_image = png_upload("hero_og.png")
    seo.save()

    response = client.get(_product_url(product), HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    content = _og_image_content(html)
    assert content is not None and 'property="og:image"' in html
    assert "hero_og" in content, (
        "Sa SeoMeta.og_image → og:image MORA biti URL te slike "
        f"(sadrži upload path), dobio {content!r} (AC4)."
    )
    assert "og-default" not in content, (
        "Sa SeoMeta.og_image → og:image NE SME biti og-default fallback (AC4)."
    )
