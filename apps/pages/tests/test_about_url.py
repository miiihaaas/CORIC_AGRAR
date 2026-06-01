"""Story 3.2 — AC1: AboutView u apps/pages + pages:about URL + HomeView regresija.

RED phase (TEA): definiše URL/view kontrakt PRE Dev GREEN. Svi testovi MORAJU pasti
dok Dev ne doda `AboutView(TemplateView)` u apps/pages/views.py +
`path("o-nama/", AboutView.as_view(), name="about")` u apps/pages/urls.py +
`templates/pages/about.html`.

RED razlog: `reverse("pages:about")` baca NoReverseMatch; GET /sr/o-nama/ → 404;
template pages/about.html ne postoji → TemplateDoesNotExist.

AC1 — 4 testa:
- test_about_url_resolves (sr/hu/en — 3 lokala HTTP 200)
- test_about_uses_pages_about_template (assertTemplateUsed pages/about.html)
- test_pages_about_reverse_resolves (reverse('pages:about') -> /sr/o-nama/)
- test_home_view_still_works (regresija — GET /sr/ 200, pages/home.html — AboutView NE pokvario HomeView)

Pokrenuti:
    just test apps/pages/tests/test_about_url.py -v
"""

from __future__ import annotations

import pytest
from django.urls import reverse
from django.utils.translation import activate

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    ("lang", "expected_url"),
    [
        ("sr", "/sr/o-nama/"),
        ("hu", "/hu/o-nama/"),
        ("en", "/en/o-nama/"),
    ],
)
def test_about_url_resolves(client, lang, expected_url):
    """AC1: GET /<lang>/o-nama/ -> HTTP 200 za sva 3 locale (AboutView)."""
    activate(lang)
    response = client.get(expected_url)
    assert response.status_code == 200, (
        f"GET {expected_url} MORA vratiti HTTP 200 (pages:about AboutView). "
        f"Dobio {response.status_code}. RED: AboutView/pages:about još ne postoji."
    )
    template_names = [t.name for t in response.templates if t.name]
    assert "pages/about.html" in template_names, (
        f"GET {expected_url} MORA renderovati 'pages/about.html', dobio {template_names!r}."
    )


def test_about_uses_pages_about_template(client):
    """AC1: render koristi 'pages/about.html' (AboutView.template_name)."""
    activate("sr")
    response = client.get("/sr/o-nama/")
    assert response.status_code == 200, (
        "GET /sr/o-nama/ MORA biti 200 (RED: AboutView ne postoji)."
    )
    template_names = [t.name for t in response.templates if t.name]
    assert "pages/about.html" in template_names, (
        "About MORA renderovati 'pages/about.html' (AboutView.template_name). "
        f"Renderovani template-i: {template_names!r}"
    )


def test_pages_about_reverse_resolves():
    """AC1: reverse('pages:about') -> '/sr/o-nama/' (app_name='pages', name='about')."""
    activate("sr")
    url = reverse("pages:about")
    assert url == "/sr/o-nama/", (
        f"reverse('pages:about') MORA dati '/sr/o-nama/' (i18n_patterns + slug 'o-nama'), "
        f"dobio {url!r}."
    )


def test_home_view_still_works(client):
    """AC1 (regresija): dodavanje AboutView NE sme pokvariti HomeView.

    GET /sr/ i dalje 200 + renderuje pages/home.html.
    """
    activate("sr")
    response = client.get("/sr/")
    assert response.status_code == 200, (
        f"GET /sr/ MORA ostati 200 (HomeView regresija), dobio {response.status_code}."
    )
    template_names = [t.name for t in response.templates if t.name]
    assert "pages/home.html" in template_names, (
        f"Home MORA i dalje renderovati 'pages/home.html', dobio {template_names!r}."
    )
