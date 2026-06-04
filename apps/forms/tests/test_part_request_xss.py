"""Story 4.5 — AC7: XSS auto-escape u OBA konteksta (error + success/echo) — TEA RED.

Javna unauth forma → svaki echo unetog teksta MORA biti auto-escaped (Django autoescape).

Pokriva Task 4.3:
- (1) ERROR partial: nevalidan POST (nedostaje obavezni payment_method) SA <script> u
  tractor_model/name → error rerender auto-escape (&lt;script&gt;), NIKAD sirov <script>.
- (2) SUCCESS/echo površina: validan submit SA <script> u tractor_model/name → ako se
  echo-uje u success response, escape-ovan je; sirov <script> NIKAD prisutan.

RED razlog: apps.forms.urls/views part_request_submit ne postoji → NoReverseMatch → padaju.

Pokrenuti:
    just test apps/forms/tests/test_part_request_xss.py -v

Refs: 4-5 AC7 + Task 4.3; interface-contract § 3/6.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.django_db


# AC-7 (XSS error partial): <script> u tractor_model/name → error rerender auto-escape, NIKAD sirov
def test_error_partial_escapes_script_payload(
    htmx_post, part_request_submit_url, part_request_payload, recipient_env, mailoutbox
):
    payload = {
        **part_request_payload,
        "payment_method": "",  # učini formu nevalidnom da se bound forma rerenderuje
        "tractor_model": "<script>alert(1)</script>",
        "name": "<script>alert(2)</script>",
    }
    response = htmx_post(part_request_submit_url, payload)
    html = response.content.decode("utf-8")

    assert "<script>alert(1)</script>" not in html, (
        "Sirov <script> NE SME biti u error response-u (Django auto-escape — XSS, Task 4.3)."
    )
    assert "&lt;script&gt;" in html, (
        "Payload MORA biti auto-escaped (&lt;script&gt;) u rerender-ovanoj bound formi (Task 4.3)."
    )


# AC-7 (XSS success/echo): <script> u tractor_model → success response NE SME imati sirov <script>
def test_success_surface_never_contains_raw_script(
    htmx_post, part_request_submit_url, part_request_payload, recipient_env, mailoutbox
):
    payload = {**part_request_payload, "tractor_model": "<script>alert(3)</script>"}
    response = htmx_post(part_request_submit_url, payload)
    html = response.content.decode("utf-8")

    assert response.status_code == 200
    assert "<script>alert(3)</script>" not in html, (
        "Sirov <script> NE SME biti u success response-u — ako se polje echo-uje, MORA biti "
        "escape-ovan (Django auto-escape — XSS, Task 4.3)."
    )
