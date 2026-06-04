"""Story 4.4 — AC11: ServiceView u apps/pages + pages:service URL + Home/Contact regresija — TEA RED.

RED phase (TEA): definiše URL/view kontrakt PRE Dev GREEN. Svi testovi MORAJU pasti dok Dev
ne doda `ServiceView(TemplateView)` (`http_method_names=["get","head","options"]`) +
`path("servis/", ServiceView.as_view(), name="service")` + `templates/pages/service.html`.

RED razlog: `reverse("pages:service")` → NoReverseMatch; GET /sr/servis/ → 404;
template pages/service.html ne postoji → TemplateDoesNotExist.

Pokriva AC11:
- reverse('pages:service') pod sr → /sr/servis/ (+ 3-locale GET 200);
- POST na pages:service → 405 (GET-only — submit ide na ZASEBAN forms endpoint);
- template pages/service.html korišćen;
- regresija: HomeView/ContactView i dalje 200.

Pokrenuti:
    just test apps/pages/tests/test_service_url.py -v

Refs: 4-4 AC11 + Task 5.1 + SM-D12; interface-contract § 7.
"""

from __future__ import annotations

import pytest
from django.urls import reverse
from django.utils.translation import activate

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    ("lang", "expected_url"),
    [
        ("sr", "/sr/servis/"),
        ("hu", "/hu/servis/"),
        ("en", "/en/servis/"),
    ],
)
def test_service_url_resolves(client, lang, expected_url):
    """AC11: GET /<lang>/servis/ → HTTP 200 za sva 3 locale (ServiceView)."""
    activate(lang)
    response = client.get(expected_url)
    assert response.status_code == 200, (
        f"GET {expected_url} MORA vratiti 200 (pages:service ServiceView), dobio {response.status_code}."
    )
    template_names = [t.name for t in response.templates if t.name]
    assert "pages/service.html" in template_names, (
        f"GET {expected_url} MORA renderovati 'pages/service.html', dobio {template_names!r}."
    )


def test_pages_service_reverse_resolves():
    """AC11: reverse('pages:service') → '/sr/servis/'."""
    activate("sr")
    url = reverse("pages:service")
    assert url == "/sr/servis/", (
        f"reverse('pages:service') MORA dati '/sr/servis/' (i18n_patterns + slug 'servis'), dobio {url!r}."
    )


def test_service_view_is_get_only_post_returns_405(client):
    """AC11: POST na pages:service → 405 (GET-only; submit ide na forms endpoint, NE page view)."""
    activate("sr")
    response = client.post("/sr/servis/", {})
    assert response.status_code == 405, (
        "POST na pages:service MORA biti 405 (ServiceView je GET-only — http_method_names bez "
        f"'post'; submit ide na forms:service_request_submit). Dobio {response.status_code}."
    )


def test_home_and_contact_views_still_work(client):
    """AC11 (regresija): dodavanje ServiceView NE sme pokvariti HomeView/ContactView."""
    activate("sr")

    home = client.get("/sr/")
    assert home.status_code == 200, f"GET /sr/ MORA ostati 200 (HomeView regresija), dobio {home.status_code}."

    contact = client.get("/sr/kontakt/")
    assert contact.status_code == 200, (
        f"GET /sr/kontakt/ MORA ostati 200 (ContactView regresija), dobio {contact.status_code}."
    )
