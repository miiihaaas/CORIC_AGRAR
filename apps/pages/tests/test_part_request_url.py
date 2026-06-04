"""Story 4.5 — AC10: PartRequestView u apps/pages + pages:part_request URL + regresija — TEA RED.

RED phase (TEA): definiše URL/view kontrakt PRE Dev GREEN. Svi testovi MORAJU pasti dok Dev
ne doda `PartRequestView(TemplateView)` (`http_method_names=["get","head","options"]`) +
`path("servis/rezervni-delovi/", PartRequestView.as_view(), name="part_request")` +
`templates/pages/part-request.html`.

RED razlog: `reverse("pages:part_request")` → NoReverseMatch; GET /sr/servis/rezervni-delovi/ → 404;
template pages/part-request.html ne postoji → TemplateDoesNotExist.

Pokriva AC10:
- reverse('pages:part_request') pod sr → /sr/servis/rezervni-delovi/ (+ 3-locale GET 200);
- POST na pages:part_request → 405 (GET-only — submit ide na ZASEBAN forms endpoint);
- template pages/part-request.html korišćen;
- regresija: HomeView/ContactView/ServiceView i dalje 200.

Pokrenuti:
    just test apps/pages/tests/test_part_request_url.py -v

Refs: 4-5 AC10 + Task 5.1 + SM-D10/SM-D12; interface-contract § 7.
"""

from __future__ import annotations

import pytest
from django.urls import reverse
from django.utils.translation import activate

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    ("lang", "expected_url"),
    [
        ("sr", "/sr/servis/rezervni-delovi/"),
        ("hu", "/hu/servis/rezervni-delovi/"),
        ("en", "/en/servis/rezervni-delovi/"),
    ],
)
def test_part_request_url_resolves(client, lang, expected_url):
    """AC10: GET /<lang>/servis/rezervni-delovi/ → HTTP 200 za sva 3 locale (PartRequestView)."""
    activate(lang)
    response = client.get(expected_url)
    assert response.status_code == 200, (
        f"GET {expected_url} MORA vratiti 200 (pages:part_request PartRequestView), dobio "
        f"{response.status_code}."
    )
    template_names = [t.name for t in response.templates if t.name]
    assert "pages/part-request.html" in template_names, (
        f"GET {expected_url} MORA renderovati 'pages/part-request.html', dobio {template_names!r}."
    )


def test_pages_part_request_reverse_resolves():
    """AC10: reverse('pages:part_request') → '/sr/servis/rezervni-delovi/'."""
    activate("sr")
    url = reverse("pages:part_request")
    assert url == "/sr/servis/rezervni-delovi/", (
        f"reverse('pages:part_request') MORA dati '/sr/servis/rezervni-delovi/' (i18n_patterns + "
        f"slug 'servis/rezervni-delovi'), dobio {url!r}."
    )


def test_part_request_view_is_get_only_post_returns_405(client):
    """AC10: POST na pages:part_request → 405 (GET-only; submit ide na forms endpoint, NE page view)."""
    activate("sr")
    response = client.post("/sr/servis/rezervni-delovi/", {})
    assert response.status_code == 405, (
        "POST na pages:part_request MORA biti 405 (PartRequestView je GET-only — http_method_names "
        f"bez 'post'; submit ide na forms:part_request_submit). Dobio {response.status_code}."
    )


def test_existing_pages_views_still_work(client):
    """AC10 (regresija): dodavanje PartRequestView NE sme pokvariti Home/Contact/Service."""
    activate("sr")

    home = client.get("/sr/")
    assert home.status_code == 200, f"GET /sr/ MORA ostati 200 (HomeView regresija), dobio {home.status_code}."

    contact = client.get("/sr/kontakt/")
    assert contact.status_code == 200, (
        f"GET /sr/kontakt/ MORA ostati 200 (ContactView regresija), dobio {contact.status_code}."
    )

    service = client.get("/sr/servis/")
    assert service.status_code == 200, (
        f"GET /sr/servis/ MORA ostati 200 (ServiceView regresija), dobio {service.status_code}."
    )
