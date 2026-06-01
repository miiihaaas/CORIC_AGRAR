"""Story 4.3 — AC3/AC4/AC5: HTMX model_inquiry_submit view + URL wiring + subject — TEA RED.

Pokriva:
- AC3: reverse("forms:model_inquiry_submit") → /sr/htmx/forme/upit-za-model/ (i18n-prefiksovan);
  i18n routing hu/en; GET → 405 (require_POST).
- AC4: validan HTMX POST → 200; 1 Lead (form_type=model_inquiry, data={product_slug, product_name},
  locale=sr, ip set); success partial korišćen (model_inquiry_success.html); 1 email u mailoutbox;
  subject „[Ćorić Agrar] Upit za model: <Product.name>" (NE ime osobe); to == [CONTACT_EMAIL_TO].
- AC4 partial: success/error response su PARTIAL-i (NEMA <html>/<head>).
- AC4 subject regression (notifications.py SM-D3): _build_subject za MODEL_INQUIRY koristi
  lead.data.get("product_name", lead.name); + no-product_name-key fallback test (→ lead.name, no exc).
- AC5: nevalidan POST (prazno name) sa validnim slug → 200; 0 Lead; mailoutbox prazan; rerender
  ima role="alert" + aria-live="assertive"; rerender ČUVA product_slug + readonly model display.

RED razlog: apps.forms.urls/views model_inquiry_submit ne postoji → NoReverseMatch / import error.

Pokrenuti:
    just test apps/forms/tests/test_model_inquiry_view.py -v

Refs: 4-3 AC3/AC4/AC5 + Task 2.1/2.2/2.3/3.2 + SM-D3; interface-contract § 2/3/4.
"""

from __future__ import annotations

import re

import pytest
from django.conf import settings
from django.urls import reverse
from django.utils.translation import activate

from apps.forms.models import Lead

pytestmark = pytest.mark.django_db


# AC-3: URL rezolvuje na /sr/htmx/forme/upit-za-model/ (locale-prefiksovan)
def test_model_inquiry_submit_url_resolves_sr():
    activate("sr")
    assert reverse("forms:model_inquiry_submit") == "/sr/htmx/forme/upit-za-model/", (
        "reverse('forms:model_inquiry_submit') pod aktivnim sr MORA biti "
        "'/sr/htmx/forme/upit-za-model/' (i18n_patterns; AC3)."
    )


# AC-3 (low): i18n routing — hu i en takođe rezolvuju (i18n_patterns 3 jezika)
@pytest.mark.parametrize("lang", ["hu", "en"])
def test_model_inquiry_submit_url_resolves_per_locale(lang):
    activate(lang)
    url = reverse("forms:model_inquiry_submit")
    assert url == f"/{lang}/htmx/forme/upit-za-model/", (
        f"reverse pod '{lang}' MORA biti '/{lang}/htmx/forme/upit-za-model/' (i18n_patterns)."
    )


# AC-3: endpoint je POST-only — GET → 405 (require_POST)
def test_model_inquiry_submit_get_not_allowed(client, model_inquiry_submit_url):
    response = client.get(model_inquiry_submit_url)
    assert response.status_code == 405, (
        f"GET na model_inquiry_submit MORA biti 405 (require_POST), dobio {response.status_code}."
    )


# AC-4: validan HTMX POST → 200 + TAČNO 1 Lead sa očekivanim poljima + data shape
def test_valid_submit_creates_single_lead(
    published_product,
    htmx_post,
    model_inquiry_submit_url,
    model_inquiry_payload,
    recipient_env,
    mailoutbox,
):
    product = published_product
    payload = {**model_inquiry_payload, "product_slug": product.slug}

    response = htmx_post(model_inquiry_submit_url, payload)
    assert response.status_code == 200, (
        f"Validan submit MORA vratiti 200, dobio {response.status_code}."
    )
    assert Lead.objects.count() == 1, "Validan submit MORA kreirati TAČNO 1 Lead (AC4)."

    lead = Lead.objects.get()
    assert lead.form_type == Lead.FormType.MODEL_INQUIRY, (
        "Lead.form_type MORA biti 'model_inquiry'."
    )
    assert lead.name == payload["name"]
    assert lead.email == payload["email"]
    assert lead.phone == payload["phone"]
    assert lead.message == payload["message"]
    # data shape LOCKED (4-1-interface-contract § 7): {"product_slug", "product_name"}
    assert lead.data == {
        "product_slug": product.slug,
        "product_name": "Agri Tracking TB804",
    }, (
        f"Lead.data MORA biti {{product_slug, product_name}} iz DB Product-a (AC4), dobio {lead.data!r}."
    )
    assert lead.locale == "sr", "Lead.locale MORA pratiti aktivni jezik (get_language)."
    assert lead.ip_address, "Lead.ip_address MORA biti popunjen iz request-a (AC3)."


# AC-4: success partial template korišćen
def test_valid_submit_renders_success_partial(
    published_product,
    htmx_post,
    model_inquiry_submit_url,
    model_inquiry_payload,
    recipient_env,
    mailoutbox,
):
    product = published_product
    payload = {**model_inquiry_payload, "product_slug": product.slug}
    response = htmx_post(model_inquiry_submit_url, payload)

    template_names = [t.name for t in response.templates if t.name]
    assert "forms/partials/model_inquiry_success.html" in template_names, (
        f"Success render MORA koristiti 'forms/partials/model_inquiry_success.html', dobio "
        f"{template_names!r}."
    )


# AC-4: send_lead_email pozvan — 1 email; subject = Product.name (NE ime osobe); to korektan
def test_valid_submit_sends_one_email_subject_is_product_name(
    published_product,
    htmx_post,
    model_inquiry_submit_url,
    model_inquiry_payload,
    recipient_env,
    mailoutbox,
):
    product = published_product
    payload = {**model_inquiry_payload, "product_slug": product.slug}
    htmx_post(model_inquiry_submit_url, payload)

    assert len(mailoutbox) == 1, f"MORA biti TAČNO 1 email, dobio {len(mailoutbox)}."
    msg = mailoutbox[0]
    assert "[Ćorić Agrar] Upit za model: Agri Tracking TB804" in msg.subject, (
        f"Subject MORA sadržati '[Ćorić Agrar] Upit za model: Agri Tracking TB804' "
        f"(= Product.name, NE ime osobe — AC4/SM-D3), dobio {msg.subject!r}."
    )
    assert "Marko Marković" not in msg.subject, (
        f"Subject NE SME sadržati ime OSOBE (mora biti Product.name — SM-D3), dobio {msg.subject!r}."
    )
    assert msg.to == [settings.CONTACT_EMAIL_TO], (
        f"Email `to` MORA biti [CONTACT_EMAIL_TO] ({settings.CONTACT_EMAIL_TO!r}), dobio {msg.to!r}."
    )


# AC-6: success partial sadrži emergency `tel:` link + labelu za hitne pozive
def test_success_has_emergency_tel_link(
    published_product,
    htmx_post,
    model_inquiry_submit_url,
    model_inquiry_payload,
    recipient_env,
    mailoutbox,
):
    product = published_product
    payload = {**model_inquiry_payload, "product_slug": product.slug}
    response = htmx_post(model_inquiry_submit_url, payload)

    html = response.content.decode("utf-8")
    assert 'href="tel:' in html, (
        'Success partial MORA sadržati klikabilan emergency `<a href="tel:...">` link (AC6).'
    )
    assert "Za hitne upite pozovite:" in html, (
        "Success partial MORA sadržati labelu „Za hitne upite pozovite:” uz emergency tel link (AC6)."
    )


# AC-4 (Task 2.2): success response je PARTIAL (NEMA <html>/<head>)
def test_success_response_is_partial(
    published_product,
    htmx_post,
    model_inquiry_submit_url,
    model_inquiry_payload,
    recipient_env,
    mailoutbox,
):
    product = published_product
    payload = {**model_inquiry_payload, "product_slug": product.slug}
    response = htmx_post(model_inquiry_submit_url, payload)

    html = response.content.decode("utf-8").lower()
    assert "<html" not in html, (
        "Success HTMX response NE SME imati <html> (partial — project-context:194)."
    )
    assert "<head" not in html, "Success HTMX response NE SME imati <head> (partial)."


# AC-5: nevalidan POST (prazno name) sa validnim slug → 200; 0 Lead; mailoutbox prazan
def test_invalid_submit_no_lead_no_email(
    published_product,
    htmx_post,
    model_inquiry_submit_url,
    model_inquiry_payload,
    recipient_env,
    mailoutbox,
):
    product = published_product
    payload = {**model_inquiry_payload, "name": "", "product_slug": product.slug}
    response = htmx_post(model_inquiry_submit_url, payload)

    assert response.status_code == 200, (
        f"Nevalidan submit MORA vratiti 200 (HTMX swap error UI-a, NE 4xx), dobio {response.status_code}."
    )
    assert Lead.objects.count() == 0, "Nevalidan submit NE SME kreirati Lead (AC5)."
    assert len(mailoutbox) == 0, "Nevalidan submit NE SME poslati email (AC5)."


# AC-5: error rerender ima in-form role="alert" + aria-live="assertive" + error tekst
def test_invalid_submit_has_assertive_alert(
    published_product,
    htmx_post,
    model_inquiry_submit_url,
    model_inquiry_payload,
    recipient_env,
    mailoutbox,
):
    product = published_product
    payload = {**model_inquiry_payload, "name": "", "product_slug": product.slug}
    response = htmx_post(model_inquiry_submit_url, payload)

    html = response.content.decode("utf-8")
    assert 'role="alert"' in html, (
        'Error rerender MORA imati in-form <div role="alert"> error summary (regija #1, AC5).'
    )
    assert 'aria-live="assertive"' in html, (
        'In-form error summary MORA biti aria-live="assertive" (regija #1, AC5).'
    )


# AC-5: error response je TAKOĐE partial (NEMA <html>/<head>)
def test_error_response_is_partial(
    published_product,
    htmx_post,
    model_inquiry_submit_url,
    model_inquiry_payload,
    recipient_env,
    mailoutbox,
):
    product = published_product
    payload = {**model_inquiry_payload, "name": "", "product_slug": product.slug}
    response = htmx_post(model_inquiry_submit_url, payload)

    html = response.content.decode("utf-8").lower()
    assert "<html" not in html, (
        "Error HTMX response NE SME imati <html> (partial — simetrično success-u)."
    )
    assert "<head" not in html, "Error HTMX response NE SME imati <head> (partial)."


# AC-5: error rerender ČUVA product_slug (hidden) + readonly model display (Product.name)
def test_invalid_submit_preserves_slug_and_model_display(
    published_product,
    htmx_post,
    model_inquiry_submit_url,
    model_inquiry_payload,
    recipient_env,
    mailoutbox,
):
    product = published_product
    payload = {**model_inquiry_payload, "name": "", "product_slug": product.slug}
    response = htmx_post(model_inquiry_submit_url, payload)

    html = response.content.decode("utf-8")
    assert product.slug in html, (
        f"Error rerender MORA ČUVATI hidden product_slug={product.slug!r} (UX — forma se ne gubi, AC5)."
    )
    assert "Agri Tracking TB804" in html, (
        "Error rerender MORA prikazati readonly model display (Product.name) tako da korisnik "
        "vidi isti model posle greške (AC5)."
    )


# AC-4 (Task 2.3 — notifications.py SM-D3): _build_subject za MODEL_INQUIRY koristi
# lead.data.get("product_name", lead.name) → subject sadrži Product.name, NE lead.name
def test_build_subject_uses_product_name_for_model_inquiry(recipient_env):
    from apps.forms.notifications import _build_subject

    lead = Lead.objects.create(
        form_type=Lead.FormType.MODEL_INQUIRY,
        name="Marko Marković",
        email="marko@example.com",
        locale="sr",
        data={
            "product_slug": "agri-tracking-tb804",
            "product_name": "Agri Tracking TB804",
        },
    )
    subject = _build_subject(lead)
    assert "Agri Tracking TB804" in subject, (
        f"_build_subject(MODEL_INQUIRY) MORA koristiti data['product_name'] (SM-D3), dobio {subject!r}."
    )
    assert "Marko Marković" not in subject, (
        f"_build_subject(MODEL_INQUIRY) NE SME koristiti lead.name (ime osobe), dobio {subject!r}."
    )


# AC-4 (Task 2.3 — no-product_name-key fallback): MODEL_INQUIRY lead sa data={} → subject
# pada nazad na lead.name BEZ KeyError/exception (defensive fallback grana — SM-D3/OQ-5)
def test_build_subject_fallback_to_lead_name_when_no_product_name(recipient_env):
    from apps.forms.notifications import _build_subject

    lead = Lead.objects.create(
        form_type=Lead.FormType.MODEL_INQUIRY,
        name="Ana Anić",
        email="ana@example.com",
        locale="sr",
        data={},
    )
    subject = _build_subject(lead)  # NE sme raise KeyError
    assert "[Ćorić Agrar]" in subject, (
        f"Fallback subject MORA i dalje sadržati brend marker '[Ćorić Agrar]', dobio {subject!r}."
    )
    assert "Ana Anić" in subject, (
        f"Bez data['product_name'], subject MORA pasti nazad na lead.name (defensive fallback, "
        f"SM-D3/OQ-5), dobio {subject!r}."
    )


# Sanity: success response NIJE escaped-leak — Product.name renderovan u success bez exception
def test_subject_format_not_person_name_via_view(
    published_product,
    htmx_post,
    model_inquiry_submit_url,
    model_inquiry_payload,
    recipient_env,
    mailoutbox,
):
    product = published_product
    payload = {**model_inquiry_payload, "product_slug": product.slug}
    htmx_post(model_inquiry_submit_url, payload)
    assert re.search(r"Upit za model:\s*Agri Tracking TB804", mailoutbox[0].subject), (
        f"Subject format MORA biti 'Upit za model: {{Product.name}}', dobio {mailoutbox[0].subject!r}."
    )
