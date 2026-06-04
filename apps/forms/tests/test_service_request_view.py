"""Story 4.4 — AC4/AC5/AC6: HTMX service_request_submit view + Lead.data + attachments + email attach — TEA RED.

Pokriva:
- AC4: reverse("forms:service_request_submit") → /sr/htmx/forme/servis/ (i18n-prefiksovan); GET → 405.
- AC5: success sa VIŠE slika (multi-file `getlist` idiom — lista pod jednim ključem) → 200; 1 Lead
  (form_type=service_request, message==description, data={machine_type, brand_model}, locale=sr, ip set);
  lead.attachments.count()==2; success partial; 1 email; subject „Novi servisni zahtev: {name}";
  to==[SERVICE_EMAIL_TO]; len(mailoutbox[0].attachments)==2 + mimetype ∈ (image/jpeg, image/png).
- AC6: success bez slika → attachments 0, mailoutbox attachments 0; empty brand_model → data {brand_model:""}.
- AC5 partial: success I error response su PARTIAL-i (NEMA <html>/<head>).
- notifications.py regression (SM-D5/SM-D7): _build_subject SERVICE_REQUEST koristi lead.name (NETAKNUT);
  recipient SERVICE_EMAIL_TO; direktan send_lead_email attach test (1 attachment → 1 email attachment).

RED razlog: apps.forms.urls/views service_request_submit + LeadAttachment + notifications attach
ne postoje → NoReverseMatch / ImportError → asercije padaju.

Pokrenuti:
    just test apps/forms/tests/test_service_request_view.py -v

Refs: 4-4 AC4/AC5/AC6 + Task 3.1/3.2/3.4 + SM-D2/SM-D5/SM-D7; interface-contract § 3/4/5.
"""

from __future__ import annotations

import pytest
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils.translation import activate

from apps.forms.models import Lead

pytestmark = pytest.mark.django_db


# AC-4: URL rezolvuje na /sr/htmx/forme/servis/ (locale-prefiksovan)
def test_service_request_submit_url_resolves_sr():
    activate("sr")
    assert reverse("forms:service_request_submit") == "/sr/htmx/forme/servis/", (
        "reverse('forms:service_request_submit') pod aktivnim sr MORA biti "
        "'/sr/htmx/forme/servis/' (i18n_patterns; AC4)."
    )


# AC-4 (low): i18n routing — hu i en takođe rezolvuju
@pytest.mark.parametrize("lang", ["hu", "en"])
def test_service_request_submit_url_resolves_per_locale(lang):
    activate(lang)
    url = reverse("forms:service_request_submit")
    assert url == f"/{lang}/htmx/forme/servis/", (
        f"reverse pod '{lang}' MORA biti '/{lang}/htmx/forme/servis/' (i18n_patterns)."
    )


# AC-4: endpoint je POST-only — GET → 405 (require_POST)
def test_service_request_submit_get_not_allowed(client, service_request_submit_url):
    response = client.get(service_request_submit_url)
    assert response.status_code == 405, (
        f"GET na service_request_submit MORA biti 405 (require_POST), dobio {response.status_code}."
    )


# AC-5: validan multipart POST sa 2 slike (multi-file LISTA idiom) → 1 Lead sa očekivanim poljima
def test_valid_submit_with_photos_creates_lead_and_attachments(
    htmx_post,
    service_request_submit_url,
    service_request_payload,
    valid_image_jpeg,
    valid_image_png,
    recipient_env,
    mailoutbox,
):
    # KRITIČNO: lista pod jednim ključem → Django test client kodira više file part-ova →
    # request.FILES.getlist("photos") vraća sve (multi-file putanja se STVARNO izvršava).
    payload = {**service_request_payload, "photos": [valid_image_jpeg, valid_image_png]}
    response = htmx_post(service_request_submit_url, payload)

    assert response.status_code == 200, (
        f"Validan submit MORA vratiti 200, dobio {response.status_code}."
    )
    assert Lead.objects.count() == 1, "Validan submit MORA kreirati TAČNO 1 Lead (AC5)."

    lead = Lead.objects.get()
    assert lead.form_type == Lead.FormType.SERVICE_REQUEST, (
        "Lead.form_type MORA biti 'service_request'."
    )
    assert lead.name == service_request_payload["name"]
    assert lead.phone == service_request_payload["phone"]
    assert lead.email == service_request_payload["email"]
    assert lead.message == service_request_payload["description"], (
        "Lead.message MORA biti opis kvara (description → message — SM-D2)."
    )
    # data shape LOCKED (SM-D2): {machine_type, brand_model}
    assert lead.data == {
        "machine_type": "tractor",
        "brand_model": "Agri Tracking TB804",
    }, (
        f"Lead.data MORA biti {{machine_type, brand_model}} (SM-D2), dobio {lead.data!r}."
    )
    assert lead.locale == "sr", "Lead.locale MORA pratiti aktivni jezik (get_language)."
    assert lead.ip_address, "Lead.ip_address MORA biti popunjen iz request-a (AC4)."


# AC-5: po 1 LeadAttachment red po priloženoj slici (2 slike → 2 attachment-a)
def test_valid_submit_persists_one_attachment_per_photo(
    htmx_post,
    service_request_submit_url,
    service_request_payload,
    valid_image_jpeg,
    valid_image_png,
    recipient_env,
    mailoutbox,
):
    payload = {**service_request_payload, "photos": [valid_image_jpeg, valid_image_png]}
    htmx_post(service_request_submit_url, payload)

    lead = Lead.objects.get()
    assert lead.attachments.count() == 2, (
        f"2 priložene slike MORAJU dati 2 LeadAttachment reda (AC5), dobio {lead.attachments.count()}."
    )


# AC-5: success partial template korišćen
def test_valid_submit_renders_success_partial(
    htmx_post,
    service_request_submit_url,
    service_request_payload,
    valid_image_jpeg,
    recipient_env,
    mailoutbox,
):
    payload = {**service_request_payload, "photos": [valid_image_jpeg]}
    response = htmx_post(service_request_submit_url, payload)

    template_names = [t.name for t in response.templates if t.name]
    assert "forms/partials/service_request_success.html" in template_names, (
        f"Success render MORA koristiti 'forms/partials/service_request_success.html', dobio "
        f"{template_names!r}."
    )


# AC-5: 1 email; subject = lead.name (SERVICE_REQUEST — SM-D7); to==[SERVICE_EMAIL_TO];
# 2 email attachment-a + mimetype ∈ (image/jpeg, image/png)
def test_valid_submit_sends_email_with_attachments(
    htmx_post,
    service_request_submit_url,
    service_request_payload,
    valid_image_jpeg,
    valid_image_png,
    recipient_env,
    mailoutbox,
):
    payload = {**service_request_payload, "photos": [valid_image_jpeg, valid_image_png]}
    htmx_post(service_request_submit_url, payload)

    assert len(mailoutbox) == 1, f"MORA biti TAČNO 1 email, dobio {len(mailoutbox)}."
    msg = mailoutbox[0]
    assert "[Ćorić Agrar] Novi servisni zahtev: Stojan Stojanović" in msg.subject, (
        f"Subject MORA sadržati '[Ćorić Agrar] Novi servisni zahtev: Stojan Stojanović' "
        f"(= lead.name — SM-D7, SERVICE_REQUEST grana NETAKNUTA), dobio {msg.subject!r}."
    )
    assert msg.to == [settings.SERVICE_EMAIL_TO], (
        f"Email `to` MORA biti [SERVICE_EMAIL_TO] ({settings.SERVICE_EMAIL_TO!r}), dobio {msg.to!r}."
    )
    assert len(msg.attachments) == 2, (
        f"Email MORA imati 2 attachment-a (po slici — epics.md:818/SM-D5), dobio {len(msg.attachments)}."
    )
    # mimetype tuple lock — NE sme biti None (SM-D5 fallback); za jpeg/png → image/jpeg|png
    for attachment in msg.attachments:
        _name, _content, mimetype = attachment
        assert mimetype in ("image/jpeg", "image/png"), (
            f"Email attachment mimetype MORA biti image/jpeg ili image/png (NE None — SM-D5 "
            f"fallback sprečava part bez Content-Type), dobio {mimetype!r}."
        )


# AC-6: submit BEZ slika → Lead kreiran, attachments 0, email bez priloga
def test_valid_submit_without_photos(
    htmx_post,
    service_request_submit_url,
    service_request_payload,
    recipient_env,
    mailoutbox,
):
    response = htmx_post(service_request_submit_url, service_request_payload)
    assert response.status_code == 200
    assert Lead.objects.count() == 1, "Submit bez slika MORA kreirati Lead (foto opciono — AC6)."

    lead = Lead.objects.get()
    assert lead.attachments.count() == 0, "Bez slika → 0 LeadAttachment (AC6)."
    assert len(mailoutbox) == 1, "Bez slika → i dalje 1 email (AC6)."
    assert len(mailoutbox[0].attachments) == 0, "Bez slika → email BEZ priloga (AC6)."


# AC-6 (SM-D2 lock): prazan brand_model → data={machine_type, brand_model:""} (ključ PRISUTAN, prazan string)
def test_empty_brand_model_data_shape(
    htmx_post,
    service_request_submit_url,
    service_request_payload,
    recipient_env,
    mailoutbox,
):
    payload = {**service_request_payload, "brand_model": ""}
    htmx_post(service_request_submit_url, payload)

    lead = Lead.objects.get()
    assert lead.data == {"machine_type": "tractor", "brand_model": ""}, (
        f"Prazan brand_model MORA dati data={{'machine_type':'tractor','brand_model':''}} "
        f"(ključ PRISUTAN sa praznim stringom, NE izostavljen — SM-D2 lock), dobio {lead.data!r}."
    )


# AC-5: success response je PARTIAL (NEMA <html>/<head>)
def test_success_response_is_partial(
    htmx_post,
    service_request_submit_url,
    service_request_payload,
    recipient_env,
    mailoutbox,
):
    response = htmx_post(service_request_submit_url, service_request_payload)
    html = response.content.decode("utf-8").lower()
    assert "<html" not in html, "Success HTMX response NE SME imati <html> (partial)."
    assert "<head" not in html, "Success HTMX response NE SME imati <head> (partial)."


# AC-7 (simetrija): error response je TAKOĐE partial (NEMA <html>/<head>)
def test_error_response_is_partial(
    htmx_post,
    service_request_submit_url,
    service_request_payload,
    recipient_env,
    mailoutbox,
):
    payload = {**service_request_payload, "name": ""}
    response = htmx_post(service_request_submit_url, payload)
    html = response.content.decode("utf-8").lower()
    assert "<html" not in html, "Error HTMX response NE SME imati <html> (partial)."
    assert "<head" not in html, "Error HTMX response NE SME imati <head> (partial)."


# AC-5 (notifications.py regression — SM-D7): _build_subject SERVICE_REQUEST koristi lead.name (NETAKNUT)
def test_build_subject_uses_lead_name_for_service_request(recipient_env):
    from apps.forms.notifications import _build_subject

    lead = Lead.objects.create(
        form_type=Lead.FormType.SERVICE_REQUEST,
        name="Stojan Stojanović",
        email="stojan@example.com",
        locale="sr",
        data={"machine_type": "tractor", "brand_model": "Agri Tracking TB804"},
    )
    subject = _build_subject(lead)
    assert "Novi servisni zahtev: Stojan Stojanović" in subject, (
        f"_build_subject(SERVICE_REQUEST) MORA koristiti lead.name (SM-D7 — NETAKNUT), dobio {subject!r}."
    )


# AC-5 (notifications.py regression — SM-D6): recipient SERVICE_REQUEST → SERVICE_EMAIL_TO (NETAKNUT)
def test_resolve_recipient_service_request_unchanged(recipient_env):
    from apps.forms.notifications import _resolve_recipient

    lead = Lead.objects.create(
        form_type=Lead.FormType.SERVICE_REQUEST,
        name="Stojan Stojanović",
        email="stojan@example.com",
    )
    assert _resolve_recipient(lead) == settings.SERVICE_EMAIL_TO, (
        "_resolve_recipient(SERVICE_REQUEST) MORA vratiti SERVICE_EMAIL_TO (SM-D6 — NETAKNUT)."
    )


# AC-5 (SM-D5 direktan attach test): lead sa 1 LeadAttachment → send_lead_email attach-uje 1 prilog
def test_send_lead_email_attaches_lead_attachment(recipient_env, mailoutbox):
    from apps.forms.models import LeadAttachment
    from apps.forms.notifications import send_lead_email

    lead = Lead.objects.create(
        form_type=Lead.FormType.SERVICE_REQUEST,
        name="Stojan Stojanović",
        email="stojan@example.com",
        locale="sr",
    )
    LeadAttachment.objects.create(
        lead=lead,
        file=SimpleUploadedFile("kvar.jpg", b"jpeg-bytes", content_type="image/jpeg"),
    )

    result = send_lead_email(lead)
    assert result is True, "send_lead_email MORA vratiti True na uspeh (recipient postavljen)."
    assert len(mailoutbox) == 1
    assert len(mailoutbox[0].attachments) == 1, (
        "Lead sa 1 LeadAttachment → email MORA imati 1 attachment (SM-D5)."
    )
    name, _content, mimetype = mailoutbox[0].attachments[0]
    assert name == "kvar.jpg", (
        f"Attachment ime MORA biti basename fajla (split na '/' — SM-D5), dobio {name!r}."
    )
    assert mimetype is not None and mimetype == "image/jpeg", (
        f"Attachment mimetype MORA biti detektovan (NE None — guess_type fallback, SM-D5), "
        f"dobio {mimetype!r}."
    )


# AC-5 (SM-D5 regression): lead BEZ attachment-a → email bez priloga (postojeći 4.1 send ostaje zelen)
def test_send_lead_email_no_attachment_no_email_attachment(recipient_env, mailoutbox):
    from apps.forms.notifications import send_lead_email

    lead = Lead.objects.create(
        form_type=Lead.FormType.KONTAKT,
        name="Marko Marković",
        email="marko@example.com",
        locale="sr",
    )
    send_lead_email(lead)
    assert len(mailoutbox) == 1
    assert len(mailoutbox[0].attachments) == 0, (
        "Lead BEZ attachment-a → email BEZ priloga (regression — prazan queryset no-op, SM-D5)."
    )
