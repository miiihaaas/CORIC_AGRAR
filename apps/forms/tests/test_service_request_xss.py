"""Story 4.4 — AC7: XSS auto-escape u OBA konteksta (error + success/echo) — TEA RED.

Javna unauth forma → svaki echo unetog teksta MORA biti auto-escaped (Django autoescape).

Pokriva Task 4.3:
- (1) ERROR partial: nevalidan POST (nedostaje obavezni phone) SA <script> u name → error rerender
  auto-escape (&lt;script&gt;), NIKAD sirov <script>.
- (2) SUCCESS/echo površina: validan submit SA <script> u name → ako se name echo-uje u success
  response, escape-ovan je; sirov <script> NIKAD prisutan.

RED razlog: apps.forms.urls/views service_request_submit ne postoji → NoReverseMatch → padaju.

Pokrenuti:
    just test apps/forms/tests/test_service_request_xss.py -v

Refs: 4-4 AC7 + Task 4.3; interface-contract § 3/6.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.django_db


# AC-7 (XSS error partial): <script> u name → error rerender auto-escape, NIKAD sirov
def test_error_partial_escapes_script_payload(
    htmx_post, service_request_submit_url, service_request_payload, recipient_env, mailoutbox
):
    payload = {
        **service_request_payload,
        "phone": "",  # učini formu nevalidnom (phone obavezan — SM-D9) da se bound forma rerenderuje
        "name": "<script>alert(1)</script>",
        "description": "<script>alert(2)</script>",
    }
    response = htmx_post(service_request_submit_url, payload)
    html = response.content.decode("utf-8")

    assert "<script>alert(1)</script>" not in html, (
        "Sirov <script> NE SME biti u error response-u (Django auto-escape — XSS, Task 4.3)."
    )
    assert "&lt;script&gt;" in html, (
        "Payload MORA biti auto-escaped (&lt;script&gt;) u rerender-ovanoj bound formi (Task 4.3)."
    )


# AC-7 (XSS success/echo): <script> u name → success response NE SME imati sirov <script>
def test_success_surface_never_contains_raw_script(
    htmx_post, service_request_submit_url, service_request_payload, recipient_env, mailoutbox
):
    payload = {**service_request_payload, "name": "<script>alert(3)</script>"}
    response = htmx_post(service_request_submit_url, payload)
    html = response.content.decode("utf-8")

    assert response.status_code == 200
    assert "<script>alert(3)</script>" not in html, (
        "Sirov <script> NE SME biti u success response-u — ako se name echo-uje, MORA biti "
        "escape-ovan (Django auto-escape — XSS, Task 4.3)."
    )
