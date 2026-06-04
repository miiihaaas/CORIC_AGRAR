"""Story 4.4 — AC9 + AC7 (dve a11y regije): OOB aria-live announcement — TEA RED phase.

Dve ODVOJENE a11y regije (KRITIČNO — REUSE 4.2 SM-D12):
- Regija #1: in-form `role="alert"` + `aria-live="assertive"` (SAMO error, unutar form partial-a).
- Regija #2: OOB `hx-swap-oob="innerHTML:#aria-live"` ka base.html `polite` singletonu (success I error).

Pokriva:
- AC9: success → SAMO OOB polite „Servisni zahtev je poslat."; error → OBE regije + OOB „Greška pri slanju, proverite polja.";
- AC9: OOB guarded `{% if request.htmx %}` — non-HTMX POST → NEMA hx-swap-oob;
- AC9: singleton OSTAJE polite (OOB blok NE postavlja assertive na #aria-live).

RED razlog: apps.forms.urls/views service_request_submit ne postoji → NoReverseMatch → padaju.

Pokrenuti:
    just test apps/forms/tests/test_service_request_aria_live.py -v

Refs: 4-4 AC9/AC7 + Task 4.2 + SM-D12; interface-contract § 6.
"""

from __future__ import annotations

import re

import pytest
from django.urls import reverse
from django.utils.translation import activate

pytestmark = pytest.mark.django_db


# AC-9: success → OOB hx-swap-oob ka #aria-live sa „Servisni zahtev je poslat." (SAMO polite)
def test_success_has_oob_polite_announcement(
    htmx_post, service_request_submit_url, service_request_payload, recipient_env, mailoutbox
):
    response = htmx_post(service_request_submit_url, service_request_payload)
    html = response.content.decode("utf-8")

    assert 'hx-swap-oob="innerHTML:#aria-live"' in html, (
        'Success HTMX response MORA imati OOB hx-swap-oob="innerHTML:#aria-live" (AC9, regija #2).'
    )
    assert "Servisni zahtev je poslat." in html, (
        "Success OOB najava MORA biti 'Servisni zahtev je poslat.' (AC9, contract paragraf 6). "
        "Sadržaj: " + html[:400]
    )


# AC-9/AC-7: success ima SAMO OOB (NEMA in-form role="alert" assertive summary)
def test_success_has_no_inform_assertive_alert(
    htmx_post, service_request_submit_url, service_request_payload, recipient_env, mailoutbox
):
    response = htmx_post(service_request_submit_url, service_request_payload)
    html = response.content.decode("utf-8")
    assert 'role="alert"' not in html, (
        "Success response NE SME imati in-form role=\"alert\" error summary (samo OOB polite, AC9)."
    )


# AC-7/AC-9: error → OBE regije (in-form assertive I OOB polite sa tačnim tekstom)
def test_error_has_both_aria_regions(
    htmx_post, service_request_submit_url, service_request_payload, recipient_env, mailoutbox
):
    payload = {**service_request_payload, "name": ""}
    response = htmx_post(service_request_submit_url, payload)
    html = response.content.decode("utf-8")

    assert 'role="alert"' in html and 'aria-live="assertive"' in html, (
        "Error response MORA imati in-form role=\"alert\" + aria-live=\"assertive\" (regija #1, AC7)."
    )
    assert 'hx-swap-oob="innerHTML:#aria-live"' in html, (
        "Error response MORA imati ODVOJEN OOB hx-swap-oob (regija #2, AC9)."
    )
    assert "Greška pri slanju, proverite polja." in html, (
        "Error OOB najava MORA biti 'Greška pri slanju, proverite polja.' (AC9, contract paragraf 6)."
    )


# AC-9: OOB blok NE postavlja assertive na #aria-live (singleton ostaje polite)
def test_oob_block_does_not_force_assertive_on_singleton(
    htmx_post, service_request_submit_url, service_request_payload, recipient_env, mailoutbox
):
    response = htmx_post(service_request_submit_url, service_request_payload)
    html = response.content.decode("utf-8")
    oob_match = re.search(
        r'<[^>]*hx-swap-oob="innerHTML:#aria-live"[^>]*>', html, re.IGNORECASE
    )
    assert oob_match, "OOB element mora postojati za success (regija #2)."
    assert 'aria-live="assertive"' not in oob_match.group(0), (
        "OOB blok NE SME postavljati assertive na #aria-live singleton — singleton ostaje "
        "polite (AC9/SM-D12)."
    )


# AC-9 (low): non-HTMX POST → NEMA hx-swap-oob (guard {% if request.htmx %})
def test_non_htmx_post_has_no_oob(
    client, service_request_payload, recipient_env, mailoutbox
):
    activate("sr")
    response = client.post(
        reverse("forms:service_request_submit"),
        service_request_payload,
        REMOTE_ADDR="203.0.113.9",
    )
    html = response.content.decode("utf-8")
    assert "hx-swap-oob" not in html, (
        "Non-HTMX POST NE SME sadržati OOB div (guard {% if request.htmx %} — AC9)."
    )
