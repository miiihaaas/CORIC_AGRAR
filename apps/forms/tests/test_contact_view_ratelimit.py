"""Story 4.2 — AC7: security must-haves (CSRF + ratelimit → HTTP 429) — TEA RED phase.

Pokriva AC7/SM-D9/SM-D10:
- 5 submit-a sa istog IP-a u 1 min PROLAZI (status NIJE 429); 6. submit → HTTP 429
  (NE 403 — Dev koristi block=False + request.limited → HttpResponse(status=429)).
- Cache pinovan eksplicitno preko @override_settings(CACHES=locmem) + cache.clear()
  pre/posle svakog testa (autouse fixture) → deterministična 5-ok/6-ti-429 granica;
  ratelimit brojač NE curi između testova.
- CSRF token prisutan u renderovanoj kontakt formi (GET /sr/kontakt/).

RED razlog: apps.forms.urls/views ne postoje → NoReverseMatch / 404 → asercije padaju.
Ako test vidi 403 umesto 429 → story je u RED dok Dev ne ispravi decorator (block=False).

Pokrenuti:
    just test apps/forms/tests/test_contact_view_ratelimit.py -v

Refs: 4-2 AC7 + Task 3.3 + SM-D9/SM-D10; interface-contract § 2/6.
"""

from __future__ import annotations

import re

import pytest
from django.utils.translation import activate

pytestmark = pytest.mark.django_db

# Cache pinning + clear (locmem `default` backend, 5-ok/6-ti-429 determinizam) dolazi iz
# autouse `_pin_and_clear_ratelimit_cache` fixture-a u apps/forms/tests/conftest.py — pinuje
# i čisti brojač PRE/POSLE svakog forms testa (SM-D10/Task 3.3). NE duplirati ovde.


# AC-7: prvih 5 submit-a sa istog IP-a PROLAZI (status NIJE 429)
def test_first_five_submits_pass(
    htmx_post, contact_submit_url, valid_contact_payload, recipient_env, mailoutbox
):
    url = contact_submit_url
    for i in range(5):
        response = htmx_post(url, valid_contact_payload, ip="198.51.100.5")
        assert response.status_code != 429, (
            f"Submit #{i + 1} od 5 NE SME biti ograničen (rate=5/m; AC7), dobio "
            f"{response.status_code}."
        )


# AC-7: 6. uzastopni submit sa istog IP-a u 1 min → HTTP 429 (NE 403)
def test_sixth_submit_returns_429(
    htmx_post, contact_submit_url, valid_contact_payload, recipient_env, mailoutbox
):
    url = contact_submit_url
    statuses = [
        htmx_post(url, valid_contact_payload, ip="198.51.100.6").status_code
        for _ in range(6)
    ]
    assert statuses[-1] == 429, (
        f"6. submit sa istog IP-a u 1 min MORA biti HTTP 429 (block=False + request.limited "
        f"→ HttpResponse(status=429), SM-D9 — NE 403!), dobio statuse {statuses!r}."
    )
    assert 403 not in statuses, (
        "NIJEDAN submit NE SME vratiti 403 — to znači block=True (PermissionDenied → 403) "
        "umesto block=False (AC7/SM-D9). Story ostaje RED dok Dev ne ispravi decorator."
    )


# AC-7: različiti IP-ovi se broje odvojeno (ratelimit key='ip')
def test_ratelimit_is_per_ip(
    htmx_post, contact_submit_url, valid_contact_payload, recipient_env, mailoutbox
):
    url = contact_submit_url
    for _ in range(5):
        htmx_post(url, valid_contact_payload, ip="198.51.100.10")
    # drugi IP — prvi zahtev MORA proći (brojač je per-IP)
    response = htmx_post(url, valid_contact_payload, ip="198.51.100.20")
    assert response.status_code != 429, (
        "Ratelimit je key='ip' — drugi IP NE SME biti ograničen brojačem prvog IP-a (AC7)."
    )


# AC-7/Security#1: CSRF token prisutan u renderovanoj kontakt formi (GET /sr/kontakt/)
def test_contact_page_has_csrf_token(client):
    activate("sr")
    response = client.get("/sr/kontakt/")
    assert response.status_code == 200, (
        f"GET /sr/kontakt/ MORA biti 200, dobio {response.status_code}."
    )
    html = response.content.decode("utf-8")
    assert re.search(r'name=["\']csrfmiddlewaretoken["\']', html, re.IGNORECASE), (
        "Kontakt forma MORA sadržati {% csrf_token %} (csrfmiddlewaretoken) — Security#1/AC7."
    )
