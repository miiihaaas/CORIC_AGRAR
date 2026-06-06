"""Story 6.3 — robots.txt endpoint (TEA RED phase, AC1 / SM-D4).

GET /robots.txt → 200, text/plain, User-agent/Allow/Disallow(admin)/Sitemap:
apsolutni reverse-based sitemap.xml URL. NO-PREFIX registracija → /sr/robots.txt
je 404 (NIJE locale-prefiksovan; mirror sitemap.xml — SEO3-7).

⚠️ RED razlog: apps/seo/views.py:robots_txt + templates/seo/robots.txt + URL
registracija JOŠ NE postoje → GET /robots.txt vraća 404 (Django default no-match)
dok Dev ne registruje view. NE module-level import apps.seo.views (Client.get only).

Refs:
- 6-3-...-meta.md AC1 + Task 1/9.1 + SM-D4 + Gotcha SEO3-7/SEO3-12
"""

from __future__ import annotations

import pytest
from django.urls import NoReverseMatch, reverse

pytestmark = pytest.mark.django_db


def test_robots_txt_returns_200_text_plain(client):
    """AC1: GET /robots.txt → 200, Content-Type počinje sa text/plain."""
    response = client.get("/robots.txt")

    assert response.status_code == 200, (
        f"GET /robots.txt MORA vratiti 200, dobio {response.status_code}. "
        "Dev mora kreirati apps/seo/views.py:robots_txt + registrovati URL (AC1/SM-D4)."
    )
    content_type = response.headers.get("Content-Type", "")
    assert content_type.startswith("text/plain"), (
        f"robots.txt MORA biti text/plain (botovi očekuju plain), dobio {content_type!r} "
        "(SEO3-7)."
    )


def test_robots_txt_has_user_agent_and_allow(client):
    """AC1: telo sadrži `User-agent: *` + `Allow: /`."""
    response = client.get("/robots.txt")
    assert response.status_code == 200
    body = response.content.decode("utf-8")

    assert "User-agent: *" in body, "robots.txt MORA imati `User-agent: *` (AC1/SM-D4)."
    assert "Allow: /" in body, "robots.txt MORA imati `Allow: /` (AC1/SM-D4)."


def test_robots_txt_disallows_admin(client):
    """AC1: telo sadrži Disallow direktivu koja pokriva admin (`*/admin/` ili po-locale)."""
    response = client.get("/robots.txt")
    assert response.status_code == 200
    body = response.content.decode("utf-8")

    assert "Disallow:" in body, "robots.txt MORA imati bar jednu Disallow direktivu (AC1)."
    # admin je POD i18n_patterns (/sr/admin/...) → `*/admin/` glob ILI eksplicitno po-locale
    has_admin_disallow = ("*/admin/" in body) or (
        "/sr/admin/" in body and "/hu/admin/" in body and "/en/admin/" in body
    )
    assert has_admin_disallow, (
        "robots.txt MORA Disallow-ovati admin (`Disallow: */admin/` glob ILI "
        "3 eksplicitne locale linije /sr/admin/ + /hu/admin/ + /en/admin/) — SEO3-12."
    )


def test_robots_txt_has_absolute_sitemap_line(client):
    """AC1: `Sitemap: ` linija sa APSOLUTNOM reverse-based /sitemap.xml URL-om."""
    response = client.get("/robots.txt")
    assert response.status_code == 200
    body = response.content.decode("utf-8")

    assert "Sitemap:" in body, "robots.txt MORA imati `Sitemap:` liniju (AC1/SM-D4)."
    # Apsolutna URL (build_absolute_uri → http://testserver/sitemap.xml na test client-u)
    assert "/sitemap.xml" in body, (
        "Sitemap linija MORA referencirati /sitemap.xml (6-2 reverse — jedini 6-2→6-3 ugovor)."
    )
    # build_absolute_uri(reverse(sitemap)) — apsolutna (host iz request); NE hardkoduj domen
    sitemap_path = reverse("django.contrib.sitemaps.views.sitemap")
    assert f"http://testserver{sitemap_path}" in body, (
        "Sitemap linija MORA biti APSOLUTNA "
        f"(build_absolute_uri(reverse(sitemap)) == http://testserver{sitemap_path}); "
        "reverse-based, NE hardkodovan path (SM-D4)."
    )


def test_robots_txt_url_is_not_locale_prefixed(client):
    """AC1: reverse('robots_txt') == /robots.txt (NO-PREFIX); /sr/robots.txt → 404."""
    url = reverse("robots_txt")
    assert url == "/robots.txt", (
        f"reverse('robots_txt') MORA biti /robots.txt (NO-PREFIX blok), dobio {url!r} "
        "(VAN i18n_patterns — SEO3-7)."
    )

    # locale-prefiksovana varijanta NE postoji → 404 (bot traži na root-u)
    response = client.get("/sr/robots.txt")
    assert response.status_code == 404, (
        "/sr/robots.txt MORA biti 404 (robots.txt je NO-PREFIX — NIJE locale-prefiksovan; "
        f"dobio {response.status_code}; SEO3-7)."
    )


def test_robots_txt_reverse_resolves(client):
    """AC1: `robots_txt` URL name razreši (NoReverseMatch = view nije registrovan)."""
    try:
        url = reverse("robots_txt")
    except NoReverseMatch:
        pytest.fail(
            "reverse('robots_txt') raise NoReverseMatch — Dev nije registrovao "
            "path('robots.txt', robots_txt, name='robots_txt') u NO-PREFIX blok (AC1)."
        )
    assert url == "/robots.txt"


def test_robots_txt_disallows_htmx_glob(client):
    """NM-3 (C3 regression lock): htmx endpointi su pod i18n (/sr/htmx/...) →
    `Disallow: */htmx/` glob ILI eksplicitne locale linije MORAJU biti u robots.txt.
    Regresija na `/htmx/` (root, no-op) bi propustila i18n-prefiksovane htmx URL-ove.
    """
    body = client.get("/robots.txt").content.decode("utf-8")
    assert ("*/htmx/" in body) or all(p in body for p in ("/sr/htmx/", "/hu/htmx/", "/en/htmx/")), (
        "robots.txt MORA Disallow-ovati htmx via glob (*/htmx/) — htmx je pod i18n "
        "(/sr/htmx/); root /htmx/ no-op (C3)."
    )
