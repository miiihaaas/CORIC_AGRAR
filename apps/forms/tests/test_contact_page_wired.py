"""Story 4.2 — AC8: wire u postojeću Kontakt stranu (a11y/regression) — TEA RED phase.

Pokriva AC8/Task 4.1: GET /sr/kontakt/ → 200; renderovani _contact_form.html SADA NEMA
`disabled` na poljima/submit-u; sadrži `hx-post` ka forms:contact_submit; više NE sadrži
„Forma će uskoro biti dostupna"; data-testid="contact-form"/"contact-submit" očuvani.
Regression: POST na pages:contact (ContactView) i dalje vraća 405 (ContactView NETAKNUT).

RED razlog: Story 3.3 skelet je još disabled + bez hx-post → asercije za AKTIVNU formu
padaju dok Dev (GREEN, Task 8) ne oživi skelet.

Pokrenuti:
    just test apps/forms/tests/test_contact_page_wired.py -v

Refs: 4-2 AC8 + Task 4.1 + SM-D6/SM-D12; interface-contract § 7.
"""

from __future__ import annotations

import re

import pytest
from django.urls import reverse
from django.utils.translation import activate

pytestmark = pytest.mark.django_db

_FORM_OPEN_RE = re.compile(
    r"<form\b[^>]*data-testid=[\"']contact-form[\"'][^>]*>",
    re.IGNORECASE,
)
_SUBMIT_RE = re.compile(
    r"<button\b[^>]*data-testid=[\"']contact-submit[\"'][^>]*>",
    re.IGNORECASE,
)


def _contact_html(client) -> str:
    activate("sr")
    response = client.get("/sr/kontakt/")
    assert response.status_code == 200, (
        f"GET /sr/kontakt/ MORA biti 200, dobio {response.status_code}."
    )
    return response.content.decode("utf-8")


# AC-8: forma SADA ima hx-post ka forms:contact_submit
def test_form_has_hx_post(client):
    activate("sr")
    html = _contact_html(client)
    m = _FORM_OPEN_RE.search(html)
    assert m, "Kontakt forma <form data-testid=\"contact-form\"> MORA postojati."
    submit_url = reverse("forms:contact_submit")
    assert re.search(r"hx-post=", m.group(0), re.IGNORECASE), (
        "Forma SADA MORA imati `hx-post` (oživljen skelet, AC8). Tag: " + repr(m.group(0))
    )
    assert submit_url in html, (
        f"Forma `hx-post` MORA ciljati forms:contact_submit ({submit_url}), AC8."
    )


# AC-8: submit dugme VIŠE NEMA disabled / aria-disabled (forma je aktivna)
def test_submit_not_disabled(client):
    html = _contact_html(client)
    m = _SUBMIT_RE.search(html)
    assert m, "Submit dugme [data-testid=\"contact-submit\"] MORA postojati."
    tag = m.group(0)
    assert not re.search(r"\bdisabled\b", tag, re.IGNORECASE), (
        f"Submit dugme VIŠE NE SME imati `disabled` (forma aktivna, AC8). Tag: {tag!r}"
    )
    assert not re.search(r'aria-disabled=["\']true["\']', tag, re.IGNORECASE), (
        f"Submit dugme VIŠE NE SME imati aria-disabled=\"true\" (AC8). Tag: {tag!r}"
    )


# AC-8: user input/textarea polja VIŠE NEMAJU disabled
def test_inputs_not_disabled(client):
    html = _contact_html(client)
    field_tags = re.findall(r"<(?:input|textarea)\b[^>]*>", html, re.IGNORECASE)
    user_fields = [
        t for t in field_tags
        if "csrfmiddlewaretoken" not in t.lower() and 'type="hidden"' not in t.lower()
    ]
    assert user_fields, "Forma MORA imati input/textarea polja."
    for t in user_fields:
        assert not re.search(r"\bdisabled\b", t, re.IGNORECASE), (
            f"User polje VIŠE NE SME imati `disabled` (aktivna forma, AC8): {t!r}"
        )


# AC-8: hint „Forma će uskoro biti dostupna" je UKLONJEN
def test_uskoro_hint_removed(client):
    html = _contact_html(client)
    assert "uskoro biti dostupna" not in html, (
        "Hint „Forma ce uskoro biti dostupna...” MORA biti uklonjen (forma je sada aktivna, AC8)."
    )


# AC-8: swap target id="contact-form-section" prisutan (SM-D6 PINNED)
def test_swap_target_id_present(client):
    html = _contact_html(client)
    assert re.search(r'id=["\']contact-form-section["\']', html, re.IGNORECASE), (
        "Obuhvatajuća <section> MORA dobiti id=\"contact-form-section\" (swap target, SM-D6 PINNED)."
    )


# AC-8: data-testid hookovi očuvani
def test_testid_hooks_preserved(client):
    html = _contact_html(client)
    assert 'data-testid="contact-form"' in html, "data-testid=\"contact-form\" MORA biti očuvan (AC8)."
    assert 'data-testid="contact-submit"' in html, "data-testid=\"contact-submit\" MORA biti očuvan (AC8)."


# AC-8 (regression): POST na pages:contact (ContactView) i dalje 405 (NETAKNUT GET-only)
def test_contactview_post_still_405(client):
    activate("sr")
    response = client.post(reverse("pages:contact"))
    assert response.status_code == 405, (
        "ContactView OSTAJE GET-only (NETAKNUT) — POST na pages:contact MORA biti 405 (AC8). "
        f"Dobio {response.status_code}."
    )
