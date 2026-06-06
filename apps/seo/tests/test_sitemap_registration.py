"""Story 6.2 — Sitemap registration + INSTALLED_APPS + sitemaps dict (TEA RED phase).

Pokriva AC1 + AC7 (SM-D1/SM-D2):
- "django.contrib.sitemaps" u INSTALLED_APPS; "django.contrib.sites" NIJE.
- /sitemap.xml → 200 (registrovan VAN i18n_patterns); /sr/sitemap.xml → 404
  (NIJE locale-prefiksovan — AC7 lock).
- reverse("django.contrib.sitemaps.views.sitemap") == "/sitemap.xml".
- apps.seo.sitemaps.sitemaps dict ima TAČNO 5 ključeva (products/brands/
  subcategories/blog/pages — NEMA series/category, CRIT-2/SM-D6).

⚠️ RED-phase discipline: apps.seo.sitemaps NE postoji još → import je LAZY
(unutar test body-ja). /sitemap.xml NIJE registrovan → status 404 ≠ 200 = clean RED
(URL absent, NE collection-abort). Existing 6-1 seo testovi ostaju green.

Refs:
- 6-2-...-hreflang.md AC1/AC7 + Task 6.6 + SM-D1/D2 + Gotcha SM2-3/SM2-9/SM2-10
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.django_db


# ── AC1: INSTALLED_APPS ───────────────────────────────────────────────────────


def test_sitemaps_framework_in_installed_apps():
    from django.conf import settings

    assert "django.contrib.sitemaps" in settings.INSTALLED_APPS, (
        "'django.contrib.sitemaps' MORA biti u INSTALLED_APPS (AC1)."
    )


def test_sites_framework_NOT_in_installed_apps():
    from django.conf import settings

    assert "django.contrib.sites" not in settings.INSTALLED_APPS, (
        "'django.contrib.sites' NE SME biti u INSTALLED_APPS — NO-SITES / "
        "RequestSite fallback + 0-migration lock (SM-D2/SM2-9)."
    )


# ── AC1: sitemaps dict — TAČNO 5 ključeva (NEMA series/category) ───────────────


def test_sitemaps_dict_has_exactly_five_keys():
    from apps.seo.sitemaps import sitemaps

    assert set(sitemaps.keys()) == {
        "products",
        "brands",
        "subcategories",
        "blog",
        "pages",
    }, (
        "sitemaps dict MORA imati TAČNO 5 sekcijskih ključeva "
        "(products/brands/subcategories/blog/pages); NEMA series/category — "
        "CRIT-2/SM-D6 (get_absolute_url RAISE NoReverseMatch)."
    )


def test_sitemaps_dict_no_series_no_category():
    from apps.seo.sitemaps import sitemaps

    assert "series" not in sitemaps, "NEMA series sitemap klase (CRIT-2/SM-D6)."
    assert "category" not in sitemaps, "NEMA category sitemap klase (CRIT-2/SM-D6)."


def test_sitemap_classes_have_i18n_and_alternates():
    from apps.seo.sitemaps import sitemaps

    for key, cls in sitemaps.items():
        instance = cls()
        assert getattr(instance, "i18n", False) is True, (
            f"{key} sitemap MORA imati i18n=True (hreflang per-locale; SM-D1)."
        )
        assert getattr(instance, "alternates", False) is True, (
            f"{key} sitemap MORA imati alternates=True (xhtml:link cross-ref; SM-D1)."
        )


# ── AC7: registracija VAN i18n_patterns ───────────────────────────────────────


def test_sitemap_url_reverses_to_root_no_prefix():
    from django.urls import reverse

    assert reverse("django.contrib.sitemaps.views.sitemap") == "/sitemap.xml", (
        "sitemap MORA biti registrovan na /sitemap.xml VAN i18n_patterns "
        "pod name='django.contrib.sitemaps.views.sitemap' (AC7/SM2-10)."
    )


def test_sitemap_xml_returns_200(client):
    response = client.get("/sitemap.xml")
    assert response.status_code == 200, (
        "GET /sitemap.xml MORA vratiti 200 (registrovan u NO-PREFIX urlpatterns; AC2/AC7)."
    )


def test_sitemap_locale_prefixed_returns_404(client):
    response = client.get("/sr/sitemap.xml")
    assert response.status_code == 404, (
        "GET /sr/sitemap.xml MORA vratiti 404 — sitemap NIJE locale-prefiksovan; "
        "JEDAN /sitemap.xml lista sve locale alternate (AC7/SM-D2/SM2-3)."
    )
