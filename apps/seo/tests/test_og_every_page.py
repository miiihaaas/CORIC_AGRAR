"""Story 6.3 — OG na NON-detail strani (obj-optional every-page lock; TEA RED, AC2/AC5).

Site-level fallback: home (pages:home) — strana BEZ objekta — TAKOĐE ima
og:title/description/image/type=website/og:url. Dokazuje da base.html
{% block social_meta %}{% seo_head %}{% endblock %} (obj=None) radi na svakoj strani
bez 500 (SM-D2). Ovo je obj-optional SRŽ globalnog OG-a (AC951 „svaka strana").

⚠️ RED razlog: base.html NEMA social_meta block + seo_head(6-1) NIJE obj-optional
(potpis seo_head(context, obj) bez default) → home nema OG dok Dev ne doda block +
ne promeni potpis na seo_head(context, obj=None) (Task 4.1/5.2).

Refs:
- 6-3-...-meta.md AC2/AC5 + Task 4.1/5.2/9.4 + SM-D2 + Gotcha SEO3-2/SEO3-13
"""

from __future__ import annotations

import pytest
from django.utils.translation import activate

pytestmark = pytest.mark.django_db


def test_home_has_site_level_og(client):
    """AC2/AC5: home (obj=None) ima og:title/description/image/type/url — site-level."""
    activate("sr")
    response = client.get("/sr/", HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    for prop in ("og:title", "og:description", "og:image", "og:type", "og:url"):
        assert f'property="{prop}"' in html, (
            f"Home (NON-detail) MORA imati <meta property=\"{prop}\"> — site-level "
            "fallback (AC5/SM-D2; obj-optional every-page lock)."
        )


def test_home_og_title_is_company_name(client):
    """AC5: site-level og:title = SiteSettings.company_name."""
    activate("sr")
    response = client.get("/sr/", HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    assert 'property="og:title"' in html
    # default company_name == "Ćorić Agrar" (SiteSettings)
    assert "Ćorić Agrar" in html, (
        "site-level og:title MORA biti SiteSettings.company_name (AC5/SM-D2)."
    )


def test_home_og_type_is_website(client):
    """AC5/AC7: site-level og:type=website (obj=None → _og_type → website)."""
    activate("sr")
    response = client.get("/sr/", HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    assert 'property="og:type"' in html
    assert 'content="website"' in html, (
        "site-level og:type MORA biti 'website' (obj=None duck-type — AC5/AC7/SM-D5)."
    )


def test_home_og_image_is_default(client):
    """AC5: site-level og:image = static og-default.jpg fallback."""
    activate("sr")
    response = client.get("/sr/", HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    assert 'property="og:image"' in html
    assert "og-default" in html, (
        "site-level og:image MORA biti static('img/og-default.jpg') fallback "
        "(AC5/SM-D6)."
    )


def test_home_og_url_is_current_path(client):
    """AC5: site-level og:url = request.build_absolute_uri(request.path) (trenutna strana)."""
    activate("sr")
    response = client.get("/sr/", HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    assert 'property="og:url"' in html
    # og:url == request.path apsolutni; asertuj path sufiks (obj=None → _canonical_url(None))
    assert "/sr/" in html, (
        "site-level og:url MORA biti request.build_absolute_uri(request.path) — "
        "trenutna strana (AC5/SM-D2)."
    )
