"""Story 3.3 — AC1: ContactView u apps/pages + pages:contact URL + Home/About regresija.

RED phase (TEA): definiše URL/view kontrakt PRE Dev GREEN. Svi testovi MORAJU pasti
dok Dev ne doda `ContactView(TemplateView)` u apps/pages/views.py
(`http_method_names = ["get", "head", "options"]`) +
`path("kontakt/", ContactView.as_view(), name="contact")` u apps/pages/urls.py +
`templates/pages/contact.html`.

RED razlog: `reverse("pages:contact")` baca NoReverseMatch; GET /sr/kontakt/ → 404;
template pages/contact.html ne postoji → TemplateDoesNotExist.

AC1 — 4 testa:
- test_contact_url_resolves (sr/hu/en — 3 lokala HTTP 200)
- test_contact_uses_pages_contact_template (assertTemplateUsed pages/contact.html)
- test_pages_contact_reverse_resolves (reverse('pages:contact') -> /sr/kontakt/)
- test_home_and_about_views_still_work (regresija — GET /sr/ + /sr/o-nama/ 200)

Pokrenuti:
    just test apps/pages/tests/test_contact_url.py -v
"""

from __future__ import annotations

import pytest
from django.urls import reverse
from django.utils.translation import activate

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    ("lang", "expected_url"),
    [
        ("sr", "/sr/kontakt/"),
        ("hu", "/hu/kontakt/"),
        ("en", "/en/kontakt/"),
    ],
)
def test_contact_url_resolves(client, lang, expected_url):
    """AC1: GET /<lang>/kontakt/ -> HTTP 200 za sva 3 locale (ContactView)."""
    activate(lang)
    response = client.get(expected_url)
    assert response.status_code == 200, (
        f"GET {expected_url} MORA vratiti HTTP 200 (pages:contact ContactView). "
        f"Dobio {response.status_code}. RED: ContactView/pages:contact još ne postoji."
    )
    template_names = [t.name for t in response.templates if t.name]
    assert "pages/contact.html" in template_names, (
        f"GET {expected_url} MORA renderovati 'pages/contact.html', dobio {template_names!r}."
    )


def test_contact_uses_pages_contact_template(client):
    """AC1: render koristi 'pages/contact.html' (ContactView.template_name)."""
    activate("sr")
    response = client.get("/sr/kontakt/")
    assert response.status_code == 200, (
        "GET /sr/kontakt/ MORA biti 200 (RED: ContactView ne postoji)."
    )
    template_names = [t.name for t in response.templates if t.name]
    assert "pages/contact.html" in template_names, (
        "Kontakt MORA renderovati 'pages/contact.html' (ContactView.template_name). "
        f"Renderovani template-i: {template_names!r}"
    )


def test_pages_contact_reverse_resolves():
    """AC1: reverse('pages:contact') -> '/sr/kontakt/' (app_name='pages', name='contact')."""
    activate("sr")
    url = reverse("pages:contact")
    assert url == "/sr/kontakt/", (
        f"reverse('pages:contact') MORA dati '/sr/kontakt/' (i18n_patterns + slug 'kontakt'), "
        f"dobio {url!r}."
    )


def test_home_and_about_views_still_work(client):
    """AC1 (regresija): dodavanje ContactView NE sme pokvariti HomeView/AboutView.

    GET /sr/ i /sr/o-nama/ i dalje 200 + renderuju svoje template-e.
    """
    activate("sr")

    home = client.get("/sr/")
    assert home.status_code == 200, (
        f"GET /sr/ MORA ostati 200 (HomeView regresija), dobio {home.status_code}."
    )
    home_templates = [t.name for t in home.templates if t.name]
    assert "pages/home.html" in home_templates, (
        f"Home MORA i dalje renderovati 'pages/home.html', dobio {home_templates!r}."
    )

    about = client.get("/sr/o-nama/")
    assert about.status_code == 200, (
        f"GET /sr/o-nama/ MORA ostati 200 (AboutView regresija), dobio {about.status_code}."
    )
    about_templates = [t.name for t in about.templates if t.name]
    assert "pages/about.html" in about_templates, (
        f"About MORA i dalje renderovati 'pages/about.html', dobio {about_templates!r}."
    )
