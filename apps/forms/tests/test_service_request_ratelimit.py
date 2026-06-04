"""Story 4.4 — AC10: security must-haves (ratelimit → HTTP 429) — TEA RED phase.

Pokriva AC10 / Task 4.5 (REUSE 4.2 SM-D9/SM-D10):
- 5 submit-a sa istog IP-a u 1 min PROLAZI (status NIJE 429); 6. submit → HTTP 429 (NE 403 —
  block=False + request.limited → HttpResponse(status=429)).
- Cache pinovan + clear-ovan preko autouse `_pin_and_clear_ratelimit_cache` (forms conftest).

RED razlog: apps.forms.urls/views service_request_submit ne postoji → NoReverseMatch → padaju.
Ako test vidi 403 umesto 429 → story je RED dok Dev ne ispravi decorator (block=False).

Pokrenuti:
    just test apps/forms/tests/test_service_request_ratelimit.py -v

Refs: 4-4 AC10 + Task 4.5 + SM-D9/SM-D10; interface-contract § 9.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.django_db

# Cache pinning + clear (locmem `default`, 5-ok/6-ti-429 determinizam) dolazi iz autouse
# `_pin_and_clear_ratelimit_cache` fixture-a u apps/forms/tests/conftest.py — NE duplirati.


# AC-10: prvih 5 submit-a sa istog IP-a PROLAZI (status NIJE 429)
def test_first_five_submits_pass(
    htmx_post, service_request_submit_url, service_request_payload, recipient_env, mailoutbox
):
    for i in range(5):
        response = htmx_post(
            service_request_submit_url, service_request_payload, ip="198.51.100.5"
        )
        assert response.status_code != 429, (
            f"Submit #{i + 1} od 5 NE SME biti ograničen (rate=5/m; AC10), dobio {response.status_code}."
        )


# AC-10: 6. uzastopni submit sa istog IP-a u 1 min → HTTP 429 (NE 403)
def test_sixth_submit_returns_429(
    htmx_post, service_request_submit_url, service_request_payload, recipient_env, mailoutbox
):
    statuses = [
        htmx_post(service_request_submit_url, service_request_payload, ip="198.51.100.6").status_code
        for _ in range(6)
    ]
    assert statuses[-1] == 429, (
        f"6. submit sa istog IP-a u 1 min MORA biti HTTP 429 (block=False + request.limited → "
        f"HttpResponse(status=429), SM-D9 — NE 403!), dobio statuse {statuses!r}."
    )
    assert 403 not in statuses, (
        "NIJEDAN submit NE SME vratiti 403 — to znači block=True (PermissionDenied → 403) "
        "umesto block=False (AC10/SM-D9). Story ostaje RED dok Dev ne ispravi decorator."
    )


# AC-10: različiti IP-ovi se broje odvojeno (key='ip')
def test_ratelimit_is_per_ip(
    htmx_post, service_request_submit_url, service_request_payload, recipient_env, mailoutbox
):
    for _ in range(5):
        htmx_post(service_request_submit_url, service_request_payload, ip="198.51.100.10")
    response = htmx_post(service_request_submit_url, service_request_payload, ip="198.51.100.20")
    assert response.status_code != 429, (
        "Ratelimit je key='ip' — drugi IP NE SME biti ograničen brojačem prvog IP-a (AC10)."
    )
