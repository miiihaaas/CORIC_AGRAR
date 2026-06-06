"""Story 7.1 — AC8: XSS granica na body render (SECURITY LOCK) (TEA RED).

Pokriva (mirror blog post_detail.html:44-45 / 5-3 SM-D1):
- body sa `<script>alert(1)</script>` → response SADRŽI escape-ovan `&lt;script&gt;`,
  NE sirov `<script>alert` (|linebreaks auto-escape; NIKAD |safe / mark_safe).
- body sa `<img src=x onerror=...>` → onerror atribut escape-ovan (NE izvršiv).

Ovo je AC8 — security-critical lock. Legalni dokument editorom kontrolisan, ali
admin-kompromis = stored-XSS vektor → autoescape obavezan. Rich-HTML body =
Epic 8.7 (sanitizacija pipeline), NE 7.1.

⚠️ COLLECTION-SAFETY: apps.gdpr importi UNUTAR funkcija.

Refs:
- 7-1-...-admin.md AC8 + SM-D3 + Gotcha G-7
- apps/blog/tests/test_blog_post_detail.py::test_detail_body_escapes_script_no_safe_filter
"""

from __future__ import annotations

import pytest

from .conftest import COOKIE_POLICY_PATH_SR

pytestmark = pytest.mark.django_db


def _seed_body(body):
    from apps.gdpr.models import CookiePolicy

    obj = CookiePolicy.load()
    obj.title_sr = "Politika kolačića"
    obj.body_sr = body
    obj.save()
    return obj


# AC8: <script> u body → ESCAPE-ovan (`&lt;script&gt;`), NE sirov tag (|linebreaks; NE |safe)
def test_body_script_is_escaped_not_executed(client):
    _seed_body("<script>alert(1)</script>")

    response = client.get(COOKIE_POLICY_PATH_SR, HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    assert "&lt;script&gt;" in html, (
        "body MORA biti auto-escape-ovan (`&lt;script&gt;`) — `|linebreaks` auto-escape "
        "(SM-D3/G-7/AC8). Odsustvo = potencijalni `|safe` (stored-XSS)."
    )
    assert "<script>alert" not in html, (
        "SIROV `<script>alert` NE SME biti u response-u (stored-XSS). body NIKAD `|safe` "
        "bez sanitizacije — rich-text = Epic 8.7 (AC8/SM-D3)."
    )


# AC8: <img onerror> u body → onerror escape-ovan (NE izvršiv handler)
def test_body_img_onerror_is_escaped(client):
    _seed_body('<img src=x onerror="alert(1)">')

    response = client.get(COOKIE_POLICY_PATH_SR, HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    assert "&lt;img" in html, (
        "<img ...> u body MORA biti escape-ovan (`&lt;img`) — autoescape (AC8/SM-D3)."
    )
    assert '<img src=x onerror="alert(1)">' not in html, (
        "SIROV `<img ... onerror=...>` NE SME biti u response-u (stored-XSS DOM event "
        "handler) — body NIKAD |safe (AC8/G-7)."
    )
