"""Story 7.1 — AC7: javna strana /sr/politika-kolacica/ (TEA RED).

Pokriva:
- GET /sr/politika-kolacica/ → 200; template gdpr/cookie_policy.html; renderuje
  title + body; <title> sadrži policy.title.
- effective_date GUARD: None → „Važi od" NIJE prikazan; postavljen → prikazan.
- updated_at UVEK prikazan kao „Poslednja izmena" (G-10 mitigacija).
- /hu/ i /en/ → 200 renderujući sr fallback (seed popunjava SAMO _sr; SM-D5).
- reverse("gdpr:cookie_policy") rezolvuje; get_absolute_url daje aktivni-locale prefiks.
- GET-only: POST → 405 (http_method_names izostavlja post — mirror ContactView).

⚠️ COLLECTION-SAFETY: apps.gdpr importi UNUTAR funkcija; URL preko literalnog
path-a (slug ASCII fiksan) ili reverse UNUTAR test tela.

Refs:
- 7-1-...-admin.md AC7 + SM-D3/D7 + Gotcha G-5/G-10/G-11
- apps/blog/tests/test_blog_post_detail.py (render mirror)
"""

from __future__ import annotations

import re

import pytest
from django.utils.translation import override

from .conftest import (
    COOKIE_POLICY_PATH_EN,
    COOKIE_POLICY_PATH_HU,
    COOKIE_POLICY_PATH_SR,
)

pytestmark = pytest.mark.django_db


def _seed_sr(title="Politika kolačića", body="Srpski tekst politike kolačića."):
    """Postavi sr sadržaj na singleton (test-determinizam — NE oslanja se na data seed)."""
    from apps.gdpr.models import CookiePolicy

    obj = CookiePolicy.load()
    obj.title_sr = title
    obj.body_sr = body
    obj.effective_date = None
    obj.save()
    return obj


# AC7: reverse("gdpr:cookie_policy") rezolvuje na /sr/politika-kolacica/ pod sr
def test_url_reverse_resolves_under_sr():
    from django.urls import reverse

    with override("sr"):
        url = reverse("gdpr:cookie_policy")
    assert url == COOKIE_POLICY_PATH_SR, (
        f"reverse('gdpr:cookie_policy') pod sr MORA biti {COOKIE_POLICY_PATH_SR!r} "
        f"(i18n_patterns prefiks; G-5/SM-D7), dobio {url!r}."
    )


# AC7: GET /sr/ → 200, koristi gdpr/cookie_policy.html, renderuje title + body
def test_sr_page_renders_title_and_body(client):
    _seed_sr(title="Politika kolačića", body="Mi koristimo kolačiće na sajtu.")

    response = client.get(COOKIE_POLICY_PATH_SR, HTTP_HOST="localhost")
    assert response.status_code == 200, (
        f"GET {COOKIE_POLICY_PATH_SR} MORA biti 200 (AC7), dobio {response.status_code}."
    )
    template_names = [t.name for t in response.templates if t.name]
    assert "gdpr/cookie_policy.html" in template_names, (
        f"Render MORA koristiti 'gdpr/cookie_policy.html' (AC7), dobio {template_names!r}."
    )
    html = response.content.decode("utf-8")
    assert "Politika kolačića" in html, "<h1>/<title> MORA sadržati policy.title (AC7)."
    assert "Mi koristimo kolačiće na sajtu." in html, (
        "Telo MORA renderovati policy.body kroz |linebreaks (AC7)."
    )


# AC7: effective_date None → „Važi od" NIJE prikazan (seed guard — G-11)
def test_effective_date_hidden_when_none(client):
    _seed_sr()  # effective_date=None

    response = client.get(COOKIE_POLICY_PATH_SR, HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")
    assert "Važi od" not in html, (
        "'Važi od' NE SME biti prikazan kad effective_date is None "
        "(`{% if policy.effective_date %}` guard — G-11/AC7)."
    )


# AC7: effective_date postavljen → „Važi od" prikazan
def test_effective_date_shown_when_set(client):
    import datetime

    from apps.gdpr.models import CookiePolicy

    obj = _seed_sr()
    obj.effective_date = datetime.date(2026, 1, 15)
    obj.save()
    assert CookiePolicy.objects.get(pk=1).effective_date == datetime.date(2026, 1, 15)

    response = client.get(COOKIE_POLICY_PATH_SR, HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")
    assert "Važi od" in html, (
        "'Važi od' MORA biti prikazan kad je effective_date postavljen (AC7)."
    )


# AC7/G-10: updated_at UVEK prikazan kao „Poslednja izmena" (mitigacija stale effective_date)
def test_updated_at_always_shown(client):
    _seed_sr()

    response = client.get(COOKIE_POLICY_PATH_SR, HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")
    assert "Poslednja izmena" in html, (
        "'Poslednja izmena' (updated_at) MORA biti UVEK prikazan (auto-timestamp "
        "mitigacija stale effective_date — G-10/AC7)."
    )


# AC7: /hu/ → 200, renderuje sr fallback sadržaj (seed SAMO _sr; SM-D5)
def test_hu_page_renders_sr_fallback(client):
    _seed_sr(title="Politika kolačića HU-fallback", body="Telo na srpskom za HU fallback.")

    response = client.get(COOKIE_POLICY_PATH_HU, HTTP_HOST="localhost")
    assert response.status_code == 200, (
        f"GET {COOKIE_POLICY_PATH_HU} MORA biti 200 (AC7), dobio {response.status_code}."
    )
    html = response.content.decode("utf-8")
    assert "Politika kolačića HU-fallback" in html, (
        "hu strana MORA prikazati sr fallback title (MODELTRANSLATION_FALLBACK_"
        "LANGUAGES=('sr',); SM-D5/AC7) — hu se NE seed-uje."
    )
    assert "Telo na srpskom za HU fallback." in html, (
        "hu strana MORA prikazati sr fallback body (AC7)."
    )


# AC7: /en/ → 200, renderuje sr fallback sadržaj
def test_en_page_renders_sr_fallback(client):
    _seed_sr(title="Politika kolačića EN-fallback", body="Telo na srpskom za EN fallback.")

    response = client.get(COOKIE_POLICY_PATH_EN, HTTP_HOST="localhost")
    assert response.status_code == 200, (
        f"GET {COOKIE_POLICY_PATH_EN} MORA biti 200 (AC7), dobio {response.status_code}."
    )
    html = response.content.decode("utf-8")
    assert "Politika kolačića EN-fallback" in html, (
        "en strana MORA prikazati sr fallback title (SM-D5/AC7)."
    )


# AC7: <title> blok sadrži policy.title
def test_title_block_contains_policy_title(client):
    _seed_sr(title="Naslov u title bloku")

    response = client.get(COOKIE_POLICY_PATH_SR, HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")
    m = re.search(r"<title>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    assert m, "Strana MORA imati <title> tag."
    assert "Naslov u title bloku" in m.group(1), (
        "<title> MORA sadržati policy.title (`{% block title %}` — AC7)."
    )


# AC7: GET-only — POST → 405 (http_method_names izostavlja post; mirror ContactView)
def test_post_returns_405(client):
    _seed_sr()
    response = client.post(COOKIE_POLICY_PATH_SR, HTTP_HOST="localhost")
    assert response.status_code == 405, (
        "CookiePolicyView je GET-only — POST MORA biti 405 (http_method_names izostavlja "
        f"post; AC7), dobio {response.status_code}."
    )
