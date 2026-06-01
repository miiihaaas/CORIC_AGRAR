"""Story 4.3 — AC7 + AC5 (dve a11y regije): OOB aria-live announcement — TEA RED.

Dve ODVOJENE a11y regije (KRITIČNO — REUSE 4.2 SM-D12):
- Regija #1: in-form `role="alert"` + `aria-live="assertive"` (SAMO error, unutar form partial-a).
- Regija #2: OOB `hx-swap-oob="innerHTML:#aria-live"` ka base.html `polite` singletonu (success I error).

Pokriva AC7 / Task 4.1:
- success response → SAMO OOB polite najava „Upit za model je poslat." (NEMA in-form assertive);
- error response → OBE regije + OOB error najava „Greška pri slanju, proverite polja.";
- OOB guarded `{% if request.htmx %}` — NE curi u non-HTMX render;
- singleton OSTAJE polite (OOB blok NE postavlja assertive na #aria-live);
- non-HTMX POST → response NEMA hx-swap-oob.

RED razlog: apps.forms.urls/views model_inquiry_submit ne postoji → NoReverseMatch / import error.

Pokrenuti:
    just test apps/forms/tests/test_model_inquiry_aria_live.py -v

Refs: 4-3 AC5/AC7 + Task 4.1 + SM-D12; interface-contract § 5.
"""

from __future__ import annotations

import re

import pytest
from django.urls import reverse
from django.utils.translation import activate

from apps.products.tests.factories import ProductFactory

pytestmark = pytest.mark.django_db


def _published_product_payload(model_inquiry_payload):
    product = ProductFactory.create(name="Agri Tracking TB804")
    return product, {**model_inquiry_payload, "product_slug": product.slug}


# AC-7: success response sadrži OOB hx-swap-oob ka #aria-live + tačnu polite najavu (SAMO OOB)
def test_success_has_oob_aria_live(
    htmx_post, model_inquiry_submit_url, model_inquiry_payload, recipient_env, mailoutbox
):
    _product, payload = _published_product_payload(model_inquiry_payload)
    response = htmx_post(model_inquiry_submit_url, payload)
    html = response.content.decode("utf-8")

    assert 'hx-swap-oob="innerHTML:#aria-live"' in html, (
        "Success HTMX response MORA imati OOB `hx-swap-oob=\"innerHTML:#aria-live\"` (AC7, regija #2)."
    )
    assert "Upit za model je poslat." in html, (
        "Success OOB najava MORA biti TAČNO „Upit za model je poslat.” (AC7). Sadržaj: " + html[:400]
    )
    oob = re.search(
        r'<[^>]*hx-swap-oob="innerHTML:#aria-live"[^>]*>(.*?)</', html, re.IGNORECASE | re.DOTALL
    )
    assert oob and oob.group(1).strip(), "Success OOB blok NE SME biti prazan (AC7)."


# AC-7/AC-5: success ima SAMO OOB (NEMA in-form role="alert" assertive summary)
def test_success_has_no_inform_assertive_alert(
    htmx_post, model_inquiry_submit_url, model_inquiry_payload, recipient_env, mailoutbox
):
    _product, payload = _published_product_payload(model_inquiry_payload)
    response = htmx_post(model_inquiry_submit_url, payload)
    html = response.content.decode("utf-8")
    assert 'role="alert"' not in html, (
        "Success response NE SME imati in-form role=\"alert\" error summary (samo OOB polite, AC7)."
    )


# AC-5/AC-7: error response sadrži OBE regije — in-form assertive I OOB polite + tačan tekst
def test_error_has_both_aria_regions(
    htmx_post, model_inquiry_submit_url, model_inquiry_payload, recipient_env, mailoutbox
):
    product = ProductFactory.create(name="Agri Tracking TB804")
    payload = {**model_inquiry_payload, "name": "", "product_slug": product.slug}
    response = htmx_post(model_inquiry_submit_url, payload)
    html = response.content.decode("utf-8")

    assert 'role="alert"' in html and 'aria-live="assertive"' in html, (
        "Error response MORA imati in-form role=\"alert\" + aria-live=\"assertive\" (regija #1, AC5)."
    )
    assert 'hx-swap-oob="innerHTML:#aria-live"' in html, (
        "Error response MORA imati ODVOJEN OOB `hx-swap-oob=\"innerHTML:#aria-live\"` (regija #2, AC7)."
    )
    assert "Greška pri slanju, proverite polja." in html, (
        "Error OOB najava MORA biti TAČNO „Greška pri slanju, proverite polja.” (pun dijakritik š, AC7)."
    )


# AC-5/AC-7 (product_not_found): valid forma + nepostojeći slug → OBE regije fire
def test_product_not_found_has_both_aria_regions(
    htmx_post, model_inquiry_submit_url, model_inquiry_payload, recipient_env, mailoutbox
):
    payload = {**model_inquiry_payload, "product_slug": "ne-postoji-nikako"}
    response = htmx_post(model_inquiry_submit_url, payload)
    html = response.content.decode("utf-8")

    assert 'role="alert"' in html and 'aria-live="assertive"' in html, (
        "product_not_found (valid forma) MORA imati in-form role=\"alert\" + "
        "aria-live=\"assertive\" (regija #1, AC5)."
    )
    assert "Proizvod nije pronađen." in html, (
        "In-form assertive alert MORA sadržati „Proizvod nije pronađen.” (pun dijakritik đ)."
    )
    assert 'hx-swap-oob="innerHTML:#aria-live"' in html, (
        "product_not_found MORA imati ODVOJEN OOB `hx-swap-oob=\"innerHTML:#aria-live\"` "
        "(regija #2, AC7) — guard ne sme da bude samo form.errors (BUG: form.is_valid() "
        "je True pa form.errors prazan)."
    )
    oob = re.search(
        r'<[^>]*hx-swap-oob="innerHTML:#aria-live"[^>]*>(.*?)</', html, re.IGNORECASE | re.DOTALL
    )
    assert oob and "Proizvod nije pronađen." in oob.group(1), (
        "OOB polite najava za product_not_found MORA sadržati „Proizvod nije pronađen.” "
        f"Sadržaj OOB: {oob.group(1) if oob else None!r}"
    )


# AC-5/AC-7 (product_not_found): unpublished slug → identičan dvo-regijski tretman
def test_unpublished_slug_product_not_found_has_oob(
    htmx_post, model_inquiry_submit_url, model_inquiry_payload, recipient_env, mailoutbox
):
    product = ProductFactory.create_unpublished(name="Skriveni Model")
    payload = {**model_inquiry_payload, "product_slug": product.slug}
    response = htmx_post(model_inquiry_submit_url, payload)
    html = response.content.decode("utf-8")

    assert 'hx-swap-oob="innerHTML:#aria-live"' in html, (
        "Unpublished slug (product_not_found) MORA imati OOB aria-live najavu (regija #2, AC7)."
    )
    assert 'role="alert"' in html and 'aria-live="assertive"' in html, (
        "Unpublished slug MORA imati in-form assertive alert (regija #1, AC5)."
    )


# AC-7: OOB blok NE postavlja assertive na #aria-live (singleton ostaje polite)
def test_oob_block_does_not_force_assertive_on_singleton(
    htmx_post, model_inquiry_submit_url, model_inquiry_payload, recipient_env, mailoutbox
):
    _product, payload = _published_product_payload(model_inquiry_payload)
    response = htmx_post(model_inquiry_submit_url, payload)
    html = response.content.decode("utf-8")
    oob_match = re.search(
        r'<[^>]*hx-swap-oob="innerHTML:#aria-live"[^>]*>', html, re.IGNORECASE
    )
    assert oob_match, "OOB element mora postojati za success (regija #2)."
    assert 'aria-live="assertive"' not in oob_match.group(0), (
        "OOB blok NE SME postavljati assertive na #aria-live singleton — ostaje polite (AC7/SM-D12)."
    )


# AC-7 (low): non-HTMX POST → response NEMA hx-swap-oob (guard {% if request.htmx %})
def test_non_htmx_post_has_no_oob(client, model_inquiry_payload, recipient_env, mailoutbox):
    activate("sr")
    product = ProductFactory.create(name="Agri Tracking TB804")
    payload = {**model_inquiry_payload, "product_slug": product.slug}
    # običan client POST BEZ HX-Request header-a → request.htmx je False
    response = client.post(
        reverse("forms:model_inquiry_submit"), payload, REMOTE_ADDR="203.0.113.9"
    )
    html = response.content.decode("utf-8")
    assert "hx-swap-oob" not in html, (
        "Non-HTMX POST NE SME sadržati OOB div (guard {% if request.htmx %} radi i kad "
        "request.htmx je False — AC7, sprečava plain-text leak)."
    )
