"""Story 4.2 — AC2/AC3/AC4: HTMX contact_submit view + URL wiring — TEA RED phase.

Pokriva:
- AC2: reverse("forms:contact_submit") → /sr/htmx/forme/kontakt/ (i18n-prefiksovan);
  i18n routing sva 3 jezika (sr/hu/en); GET → 405 (require_POST).
- AC3: validan HTMX POST → 200; 1 Lead (form_type=contact, data={}, locale=sr, ip set);
  success partial korišćen + sadrži „Hvala"; 1 email u mailoutbox; subject „[Ćorić Agrar]
  Novi kontakt: {name}"; to == [CONTACT_EMAIL_TO].
- AC4: nevalidan POST → 200 (NE 4xx); 0 Lead; mailoutbox prazan; rerender ima role="alert"
  + aria-live="assertive" + error tekst.
- Partial check (AC2): success I error response su PARTIAL-i (NEMA <html>/<head>).
- XSS insurance (AC4): <script> u payload-u → auto-escaped &lt;script&gt;, NIKAD sirov.

RED razlog: apps.forms.urls/views ne postoje → NoReverseMatch / 404 → asercije padaju.

Pokrenuti:
    just test apps/forms/tests/test_contact_view.py -v

Refs: 4-2 AC2/AC3/AC4 + Task 2.1/2.2/2.3; interface-contract § 2/3/4/5.
"""

from __future__ import annotations

import re

import pytest
from django.conf import settings
from django.urls import reverse
from django.utils.translation import activate

from apps.forms.models import Lead

pytestmark = pytest.mark.django_db


# AC-2: URL rezolvuje na /sr/htmx/forme/kontakt/ (locale-prefiksovan)
def test_contact_submit_url_resolves_sr():
    activate("sr")
    assert reverse("forms:contact_submit") == "/sr/htmx/forme/kontakt/", (
        "reverse('forms:contact_submit') pod aktivnim sr MORA biti "
        "'/sr/htmx/forme/kontakt/' (i18n_patterns; AC2)."
    )


# AC-2 (low): i18n routing — hu i en takođe rezolvuju (i18n_patterns 3 jezika)
@pytest.mark.parametrize("lang", ["hu", "en"])
def test_contact_submit_url_resolves_per_locale(lang):
    activate(lang)
    url = reverse("forms:contact_submit")
    assert url == f"/{lang}/htmx/forme/kontakt/", (
        f"reverse pod '{lang}' MORA biti '/{lang}/htmx/forme/kontakt/' (i18n_patterns)."
    )


# AC-2: endpoint je POST-only — GET → 405 (require_POST)
def test_contact_submit_get_not_allowed(client, contact_submit_url):
    response = client.get(contact_submit_url)
    assert response.status_code == 405, (
        f"GET na contact_submit MORA biti 405 (require_POST), dobio {response.status_code}."
    )


# AC-3: validan HTMX POST → 200 + TAČNO 1 Lead sa očekivanim poljima
def test_valid_submit_creates_single_lead(
    htmx_post, contact_submit_url, valid_contact_payload, recipient_env, mailoutbox
):
    response = htmx_post(contact_submit_url, valid_contact_payload)
    assert response.status_code == 200, (
        f"Validan submit MORA vratiti 200, dobio {response.status_code}."
    )
    assert Lead.objects.count() == 1, "Validan submit MORA kreirati TAČNO 1 Lead (AC3)."

    lead = Lead.objects.get()
    assert lead.form_type == Lead.FormType.KONTAKT, "Lead.form_type MORA biti 'contact'."
    assert lead.name == valid_contact_payload["name"]
    assert lead.email == valid_contact_payload["email"]
    assert lead.phone == valid_contact_payload["phone"]
    assert lead.message == valid_contact_payload["message"]
    assert lead.data == {}, "Lead.data MORA biti prazan {} za form_type='contact' (SM-D7)."
    assert lead.locale == "sr", "Lead.locale MORA pratiti aktivni jezik (get_language)."
    assert lead.ip_address, "Lead.ip_address MORA biti popunjen iz request-a (AC2)."


# AC-3: success partial template korišćen + sadrži „Hvala"
def test_valid_submit_renders_success_partial(
    htmx_post, contact_submit_url, valid_contact_payload, recipient_env, mailoutbox
):
    response = htmx_post(contact_submit_url, valid_contact_payload)
    template_names = [t.name for t in response.templates if t.name]
    assert "forms/partials/contact_success.html" in template_names, (
        f"Success render MORA koristiti 'forms/partials/contact_success.html', dobio "
        f"{template_names!r}."
    )
    html = response.content.decode("utf-8")
    # Asertuj PUNU success poruku (uklj. dijakritiku š u „Vaš") — ne samo ASCII „Hvala"
    # koji bi prošao i sa šišanom latinicom / pogrešnom porukom (AC3/AC9).
    assert "Hvala! Vaš upit je primljen." in html, (
        "Success partial MORA sadržati TAČNU poruku „Hvala! Vaš upit je primljen.” sa punim "
        "dijakritikama (AC3/AC9). Sadržaj: " + html[:400]
    )


# AC-3: send_lead_email pozvan — 1 email, subject + to korektni
def test_valid_submit_sends_one_email(
    htmx_post, contact_submit_url, valid_contact_payload, recipient_env, mailoutbox
):
    htmx_post(contact_submit_url, valid_contact_payload)
    assert len(mailoutbox) == 1, f"MORA biti TAČNO 1 email u mailoutbox, dobio {len(mailoutbox)}."

    msg = mailoutbox[0]
    expected_subject_fragment = f"[Ćorić Agrar] Novi kontakt: {valid_contact_payload['name']}"
    assert expected_subject_fragment in msg.subject, (
        f"Subject MORA sadržati {expected_subject_fragment!r}, dobio {msg.subject!r}."
    )
    assert msg.to == [settings.CONTACT_EMAIL_TO], (
        f"Email `to` MORA biti [CONTACT_EMAIL_TO] ({settings.CONTACT_EMAIL_TO!r}), dobio {msg.to!r}."
    )


# AC-3 (Task 2.2): success response je PARTIAL (NEMA <html>/<head>)
def test_success_response_is_partial(
    htmx_post, contact_submit_url, valid_contact_payload, recipient_env, mailoutbox
):
    response = htmx_post(contact_submit_url, valid_contact_payload)
    html = response.content.decode("utf-8").lower()
    assert "<html" not in html, "Success HTMX response NE SME imati <html> (partial — project-context:194)."
    assert "<head" not in html, "Success HTMX response NE SME imati <head> (partial)."


# AC-4: nevalidan POST (prazno name) → 200 (NE 4xx); 0 Lead; mailoutbox prazan
def test_invalid_submit_no_lead_no_email(
    htmx_post, contact_submit_url, valid_contact_payload, recipient_env, mailoutbox
):
    payload = {**valid_contact_payload, "name": ""}
    response = htmx_post(contact_submit_url, payload)
    assert response.status_code == 200, (
        f"Nevalidan submit MORA vratiti 200 (HTMX swap error UI-a, NE 4xx), dobio "
        f"{response.status_code}."
    )
    assert Lead.objects.count() == 0, "Nevalidan submit NE SME kreirati Lead (AC4)."
    assert len(mailoutbox) == 0, "Nevalidan submit NE SME poslati email (AC4)."


# AC-4: error rerender ima in-form role="alert" + aria-live="assertive" + error tekst
def test_invalid_submit_has_assertive_alert(
    htmx_post, contact_submit_url, valid_contact_payload, recipient_env, mailoutbox
):
    payload = {**valid_contact_payload, "name": "", "email": ""}
    response = htmx_post(contact_submit_url, payload)
    html = response.content.decode("utf-8")
    assert 'role="alert"' in html, (
        "Error rerender MORA imati in-form <div role=\"alert\"> error summary (regija #1, AC4)."
    )
    assert 'aria-live="assertive"' in html, (
        "In-form error summary MORA biti aria-live=\"assertive\" (trenutna snažna najava, AC4)."
    )
    # TEST_GAP (Dev A/TEA): NE samo ATRIBUTI — sam role="alert" blok MORA sadržati realan
    # per-field error tekst (prazna regija bi prošla samo atribut-asercije). Izvuci sadržaj
    # role="alert" elementa i potvrdi da nosi „Unesite ime i prezime." (name-required poruka).
    alert = re.search(
        r'<div[^>]*role="alert"[^>]*>(.*?)</div>', html, re.IGNORECASE | re.DOTALL
    )
    assert alert and "Unesite ime i prezime." in alert.group(1), (
        "In-form role=\"alert\" blok MORA sadržati stvarnu per-field grešku "
        "„Unesite ime i prezime.” (ne sme biti prazna a11y regija). Sadržaj: "
        + (alert.group(1)[:300] if alert else "<nema role=alert>")
    )


# AC-2 (Task 2.2 simetrija): error response je TAKOĐE partial (NEMA <html>/<head>)
def test_error_response_is_partial(
    htmx_post, contact_submit_url, valid_contact_payload, recipient_env, mailoutbox
):
    payload = {**valid_contact_payload, "name": ""}
    response = htmx_post(contact_submit_url, payload)
    html = response.content.decode("utf-8").lower()
    assert "<html" not in html, "Error HTMX response NE SME imati <html> (partial — simetrično success-u)."
    assert "<head" not in html, "Error HTMX response NE SME imati <head> (partial)."


# AC-4 (Task 2.3): XSS insurance — <script> u payload-u → escaped, NIKAD sirov
def test_invalid_submit_escapes_script_payload(
    htmx_post, contact_submit_url, valid_contact_payload, recipient_env, mailoutbox
):
    payload = {
        **valid_contact_payload,
        "email": "",  # učini formu nevalidnom da se bound forma rerenderuje sa payload-om
        "name": "<script>alert(1)</script>",
        "message": "<script>alert(2)</script>",
    }
    response = htmx_post(contact_submit_url, payload)
    html = response.content.decode("utf-8")
    assert "<script>alert(1)</script>" not in html, (
        "Sirov <script> NE SME biti u response-u (Django auto-escape — XSS, Task 2.3)."
    )
    assert "&lt;script&gt;" in html, (
        "Payload MORA biti auto-escaped (&lt;script&gt;) u rerender-ovanoj bound formi (Task 2.3)."
    )


# AC-9 (TEST_GAP/TEA): per-locale RESPONSE sadržaj — gettext rezolvuje PREVOD na view sloju.
# Uspešan en submit MORA renderovati ENGLESKI success string (ne sr original), čime se
# dokazuje da je render lokalizovan po aktivnom jeziku, ne samo URL rezolucija.
def test_valid_submit_renders_translated_success_en(
    htmx_post, valid_contact_payload, recipient_env, mailoutbox
):
    activate("en")
    url = reverse("forms:contact_submit")
    response = htmx_post(url, valid_contact_payload)
    html = response.content.decode("utf-8")
    assert "Thank you! Your inquiry has been received." in html, (
        "Pod aktivnim 'en', success partial MORA renderovati ENGLESKI prevod "
        "(gettext rezolucija na view sloju, ne samo URL). Sadržaj: " + html[:400]
    )


# AC-9 (TEST_GAP/TEA): nevalidan en submit → ENGLESKA per-field error poruka u response-u.
def test_invalid_submit_renders_translated_error_en(
    htmx_post, valid_contact_payload, recipient_env, mailoutbox
):
    activate("en")
    url = reverse("forms:contact_submit")
    payload = {**valid_contact_payload, "name": ""}
    response = htmx_post(url, payload)
    html = response.content.decode("utf-8")
    assert "Enter your full name." in html, (
        "Pod aktivnim 'en', error rerender MORA renderovati ENGLESKI prevod per-field "
        "greške („Enter your full name.”) — gettext rezolucija po lokalu. Sadržaj: " + html[:400]
    )
