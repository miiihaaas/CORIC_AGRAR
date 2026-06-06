"""Story 6.3 — Open Graph core tagovi na detail stranama (TEA RED, AC2/AC8).

Detail strana (product/post) `<head>` ima og:title/description/image/type/url (5
core OG). SeoMeta.meta_title/meta_description se koriste kad postoje (ISTA logika kao
seo_title/seo_meta_description); inače fallback `_display_title | company` /
`_display_description` (6-1 fallback chain — CRIT-1 očuvan).

⚠️ RED razlog: seo_head (6-1) emituje SAMO canonical + og:image-kad-set; base.html
NEMA {% block social_meta %}{% seo_head %}{% endblock %} → og:title/description/type/
url ODSUTNI u head-u dok Dev ne EXTEND-uje seo_head + ne doda social_meta block.
NE collection error (apps.* importi UNUTAR test tela / fixture).

Asercije na response.content (full-page kroz base.html → context processors + request
za build_absolute_uri); namespace-free string search.

Refs:
- 6-3-...-meta.md AC2/AC8 + Task 4/9.2 + SM-D1/D2 + Gotcha SEO3-1
"""

from __future__ import annotations

import pytest
from django.utils.translation import activate

pytestmark = pytest.mark.django_db


def _product_url(product):
    return f"/sr/proizvod/{product.slug}/"


def _post_url(post):
    return f"/sr/blog/{post.slug}/"


def test_product_detail_has_five_core_og_tags(client, product):
    """AC2: product detail head ima og:title/description/image/type/url."""
    activate("sr")
    response = client.get(_product_url(product), HTTP_HOST="localhost")

    assert response.status_code == 200
    html = response.content.decode("utf-8")
    for prop in ("og:title", "og:description", "og:image", "og:type", "og:url"):
        assert f'property="{prop}"' in html, (
            f"Product detail head MORA imati <meta property=\"{prop}\"> "
            "(AC2 — 5 core OG; seo_head EXTEND + base.html social_meta block)."
        )


def test_post_detail_has_five_core_og_tags(client, post):
    """AC2: blog post detail head ima og:title/description/image/type/url."""
    activate("sr")
    response = client.get(_post_url(post), HTTP_HOST="localhost")

    assert response.status_code == 200
    html = response.content.decode("utf-8")
    for prop in ("og:title", "og:description", "og:image", "og:type", "og:url"):
        assert f'property="{prop}"' in html, (
            f"Post detail head MORA imati <meta property=\"{prop}\"> (AC2)."
        )


def test_og_title_uses_seometa_meta_title_when_set(client, product):
    """AC8: og:title content sadrži SeoMeta.meta_title (ISTA logika kao seo_title)."""
    from apps.seo.models import SeoMeta

    activate("sr")
    SeoMeta.objects.create(content_object=product, meta_title_sr="Custom OG naslov")

    response = client.get(_product_url(product), HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    assert 'property="og:title"' in html
    assert "Custom OG naslov" in html, (
        "og:title MORA koristiti SeoMeta.meta_title kad je postavljen "
        "(ISTA logika kao seo_title — AC8)."
    )


def test_og_description_uses_seometa_meta_description_when_set(client, product):
    """AC8: og:description content sadrži SeoMeta.meta_description."""
    from apps.seo.models import SeoMeta

    activate("sr")
    SeoMeta.objects.create(
        content_object=product, meta_description_sr="Custom OG opis za share."
    )

    response = client.get(_product_url(product), HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    assert 'property="og:description"' in html
    assert "Custom OG opis za share." in html, (
        "og:description MORA koristiti SeoMeta.meta_description kad je postavljen (AC8)."
    )


def test_og_title_falls_back_to_display_title_company(client, product):
    """AC8: bez SeoMeta → og:title = `_display_title | company` (6-1 fallback)."""
    activate("sr")
    response = client.get(_product_url(product), HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    assert 'property="og:title"' in html
    # _display_title(product) == product.name; fallback chain dodaje ' | company'
    assert product.name in html, (
        "Bez SeoMeta → og:title MORA pasti na `_display_title | company` "
        "(reuse 6-1 fallback — CRIT-1 očuvan; AC8)."
    )


def test_og_url_is_canonical_path(client, product):
    """AC2: og:url == canonical (apsolutna; sadrži get_absolute_url path sufiks)."""
    activate("sr")
    response = client.get(_product_url(product), HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    # og:url == canonical apsolutna URL; asertuj PATH sufiks (host=testserver/localhost)
    assert 'property="og:url"' in html
    assert f"/sr/proizvod/{product.slug}/" in html, (
        "og:url MORA biti canonical apsolutna URL (get_absolute_url path; ARCH-3/SM-D5)."
    )
