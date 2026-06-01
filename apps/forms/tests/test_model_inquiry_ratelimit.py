"""Story 4.3 — AC8: security must-haves (ratelimit → HTTP 429) — TEA RED.

Pokriva AC8 / Task 4.3:
- 5 submit-a sa istog IP-a u 1 min PROLAZI (status NIJE 429); 6. → HTTP 429 (NE 403 —
  block=False + request.limited → HttpResponse(status=429), REUSE 4.2 SM-D9).
- ratelimit je key='ip' → različiti IP-ovi se broje odvojeno.
- Cache pinovan + cache.clear() pre/posle (autouse `_pin_and_clear_ratelimit_cache` iz
  forms conftest-a) → deterministična 5-ok/6-ti-429 granica; brojač NE curi.

(CSRF-token-u-renderovanoj-formi asercija je u test_model_inquiry_page_wired.py — zavisi
od product-page wiringa, ne od ratelimita; ovaj fajl je fokusiran SAMO na ratelimit.)

RED razlog: apps.forms.urls/views model_inquiry_submit ne postoji → NoReverseMatch / import error.

Pokrenuti:
    just test apps/forms/tests/test_model_inquiry_ratelimit.py -v

Refs: 4-3 AC8 + Task 4.3 + SM-D9/SM-D10; interface-contract § 2/6.
"""

from __future__ import annotations

import pytest

from apps.products.tests.factories import ProductFactory

pytestmark = pytest.mark.django_db

# Cache pinning + clear (locmem `default` backend, 5-ok/6-ti-429 determinizam) dolazi iz
# autouse `_pin_and_clear_ratelimit_cache` fixture-a u apps/forms/tests/conftest.py.


# AC-8: prvih 5 submit-a sa istog IP-a PROLAZI (status NIJE 429)
def test_first_five_submits_pass(
    htmx_post, model_inquiry_submit_url, model_inquiry_payload, recipient_env, mailoutbox
):
    product = ProductFactory.create(name="Agri Tracking TB804")
    payload = {**model_inquiry_payload, "product_slug": product.slug}
    for i in range(5):
        response = htmx_post(model_inquiry_submit_url, payload, ip="198.51.100.5")
        assert response.status_code != 429, (
            f"Submit #{i + 1} od 5 NE SME biti ograničen (rate=5/m; AC8), dobio {response.status_code}."
        )


# AC-8: 6. uzastopni submit sa istog IP-a u 1 min → HTTP 429 (NE 403)
def test_sixth_submit_returns_429(
    htmx_post, model_inquiry_submit_url, model_inquiry_payload, recipient_env, mailoutbox
):
    product = ProductFactory.create(name="Agri Tracking TB804")
    payload = {**model_inquiry_payload, "product_slug": product.slug}
    statuses = [
        htmx_post(model_inquiry_submit_url, payload, ip="198.51.100.6").status_code
        for _ in range(6)
    ]
    assert statuses[-1] == 429, (
        f"6. submit sa istog IP-a u 1 min MORA biti HTTP 429 (block=False + request.limited "
        f"→ HttpResponse(status=429), SM-D9 — NE 403!), dobio statuse {statuses!r}."
    )
    assert 403 not in statuses, (
        "NIJEDAN submit NE SME vratiti 403 — to znači block=True (PermissionDenied → 403) umesto "
        "block=False (AC8/SM-D9). Story ostaje RED dok Dev ne ispravi decorator."
    )


# AC-8: različiti IP-ovi se broje odvojeno (ratelimit key='ip')
def test_ratelimit_is_per_ip(
    htmx_post, model_inquiry_submit_url, model_inquiry_payload, recipient_env, mailoutbox
):
    product = ProductFactory.create(name="Agri Tracking TB804")
    payload = {**model_inquiry_payload, "product_slug": product.slug}
    for _ in range(5):
        htmx_post(model_inquiry_submit_url, payload, ip="198.51.100.10")
    # drugi IP — prvi zahtev MORA proći (brojač je per-IP)
    response = htmx_post(model_inquiry_submit_url, payload, ip="198.51.100.20")
    assert response.status_code != 429, (
        "Ratelimit je key='ip' — drugi IP NE SME biti ograničen brojačem prvog IP-a (AC8)."
    )
