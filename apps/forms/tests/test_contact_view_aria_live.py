"""Story 4.2 — AC6 + AC4 (dve a11y regije): OOB aria-live announcement — TEA RED phase.

Dve ODVOJENE a11y regije (KRITIČNO — ne mešati):
- Regija #1: in-form `role="alert"` + `aria-live="assertive"` (SAMO error, unutar form partial-a).
- Regija #2: OOB `hx-swap-oob="innerHTML:#aria-live"` ka base.html `polite` singletonu (success I error).

Pokriva:
- AC6: success response → SAMO OOB polite najava; error response → OBE regije.
- AC6: OOB guarded `{% if request.htmx %}` — NE curi u non-HTMX render.
- AC6: singleton OSTAJE polite — OOB blok NE postavlja `assertive` na #aria-live.
- (low) Non-HTMX POST → response NEMA hx-swap-oob (guard radi i kad request.htmx False).

RED razlog: apps.forms.urls/views ne postoje → NoReverseMatch / 404 → asercije padaju.

Pokrenuti:
    just test apps/forms/tests/test_contact_view_aria_live.py -v

Refs: 4-2 AC4/AC6 + Task 3.1 + SM-D12; interface-contract § 5.
"""

from __future__ import annotations

import re

import pytest
from django.urls import reverse
from django.utils.translation import activate

pytestmark = pytest.mark.django_db


# AC-6: success response sadrži OOB hx-swap-oob ka #aria-live (polite najava)
def test_success_has_oob_aria_live(
    htmx_post, contact_submit_url, valid_contact_payload, recipient_env, mailoutbox
):
    response = htmx_post(contact_submit_url, valid_contact_payload)
    html = response.content.decode("utf-8")
    assert 'hx-swap-oob="innerHTML:#aria-live"' in html, (
        "Success HTMX response MORA imati OOB `hx-swap-oob=\"innerHTML:#aria-live\"` (AC6, regija #2)."
    )
    # OOB najava MORA imati sadržaj (NE prazan div) — kratka success poruka (AC6, contract § 5).
    oob = re.search(
        r'<[^>]*hx-swap-oob="innerHTML:#aria-live"[^>]*>(.*?)</', html, re.IGNORECASE | re.DOTALL
    )
    assert oob and oob.group(1).strip(), (
        "Success OOB blok NE SME biti prazan — MORA nositi kratku najavu „Upit je poslat.” (AC6)."
    )
    assert "Upit je poslat." in html, (
        "Success OOB najava MORA biti „Upit je poslat.” (AC6, contract § 5). Sadržaj: " + html[:400]
    )


# AC-6/AC-4: success ima SAMO OOB (NEMA in-form role="alert" assertive summary)
def test_success_has_no_inform_assertive_alert(
    htmx_post, contact_submit_url, valid_contact_payload, recipient_env, mailoutbox
):
    response = htmx_post(contact_submit_url, valid_contact_payload)
    html = response.content.decode("utf-8")
    assert 'role="alert"' not in html, (
        "Success response NE SME imati in-form role=\"alert\" error summary (samo OOB polite, AC6)."
    )


# AC-4/AC-6: error response sadrži OBE regije — in-form assertive I OOB polite
def test_error_has_both_aria_regions(
    htmx_post, contact_submit_url, valid_contact_payload, recipient_env, mailoutbox
):
    payload = {**valid_contact_payload, "name": ""}
    response = htmx_post(contact_submit_url, payload)
    html = response.content.decode("utf-8")
    # regija #1 — in-form assertive
    assert 'role="alert"' in html and 'aria-live="assertive"' in html, (
        "Error response MORA imati in-form role=\"alert\" + aria-live=\"assertive\" (regija #1, AC4)."
    )
    # regija #2 — OOB polite
    assert 'hx-swap-oob="innerHTML:#aria-live"' in html, (
        "Error response MORA imati ODVOJEN OOB `hx-swap-oob=\"innerHTML:#aria-live\"` (regija #2, AC6)."
    )
    # OOB error najava MORA imati tačan tekst (puni dijakritik š u „Greška") — NE prazan div (AC6).
    assert "Greška pri slanju, proverite polja." in html, (
        "Error OOB najava MORA biti „Greška pri slanju, proverite polja.” (AC6, contract § 5)."
    )


# AC-6: OOB blok NE postavlja assertive na #aria-live (singleton ostaje polite)
def test_oob_block_does_not_force_assertive_on_singleton(
    htmx_post, contact_submit_url, valid_contact_payload, recipient_env, mailoutbox
):
    response = htmx_post(contact_submit_url, valid_contact_payload)
    html = response.content.decode("utf-8")
    # Pronađi OOB element i potvrdi da ne nosi aria-live="assertive" na #aria-live targetu.
    oob_match = re.search(
        r'<[^>]*hx-swap-oob="innerHTML:#aria-live"[^>]*>', html, re.IGNORECASE
    )
    assert oob_match, "OOB element mora postojati za success (regija #2)."
    assert 'aria-live="assertive"' not in oob_match.group(0), (
        "OOB blok NE SME postavljati assertive na #aria-live singleton — singleton ostaje "
        "polite (AC6/SM-D12)."
    )


# AC-6 (low): non-HTMX POST → NEMA hx-swap-oob (guard {% if request.htmx %})
def test_non_htmx_post_has_no_oob(client, valid_contact_payload, recipient_env, mailoutbox):
    activate("sr")
    # običan client POST BEZ HX-Request header-a → request.htmx je False
    response = client.post(reverse("forms:contact_submit"), valid_contact_payload, REMOTE_ADDR="203.0.113.9")
    html = response.content.decode("utf-8")
    assert "hx-swap-oob" not in html, (
        "Non-HTMX POST NE SME sadržati OOB div (guard {% if request.htmx %} radi i kad "
        "request.htmx je False — AC6, sprečava plain-text leak)."
    )
