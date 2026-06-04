"""Story 4.5 — AC3/AC4/AC5/AC6: HTMX part_request_submit view + Lead.data + slika + subject — TEA RED.

Pokriva:
- AC3: reverse("forms:part_request_submit") → /sr/htmx/forme/rezervni-delovi/ (i18n-prefiksovan); GET → 405.
- AC4: success SA slikom (single-file `photo` idiom) → 200; 1 Lead (form_type=part_request,
  message==note, data={tractor_model,part_name,extra_description,payment_method,delivery_method},
  locale=sr, ip set); lead.attachments.count()==1; success partial; 1 email; to==[PARTS_EMAIL_TO];
  len(mailoutbox[0].attachments)==1.
- AC5: subject „[Ćorić Agrar] Upit za rezervni deo: Filter ulja (Agri Tracking TB804)" (iz lead.data,
  NE lead.name) — FORSIRA _build_subject izmenu PART_REQUEST grane. Direktan notifications unit test +
  prazan-data fallback (lead.name) + regression za druge grane.
- AC6: success BEZ slike → attachments 0, mailoutbox attachments 0; prazan opcioni → data shape lock.
- AC4 partial: success I error response su PARTIAL-i (NEMA <html>/<head>).

RED razlog: apps.forms.urls/views part_request_submit + _build_subject PART_REQUEST izmena
ne postoje → NoReverseMatch / pogrešan subject → asercije padaju.

Pokrenuti:
    just test apps/forms/tests/test_part_request_view.py -v

Refs: 4-5 AC3/AC4/AC5/AC6 + Task 3.1/3.2/3.3/3.4 + SM-D2/SM-D5; interface-contract § 3/5.
"""

from __future__ import annotations

import pytest
from django.conf import settings
from django.urls import reverse
from django.utils.translation import activate

from apps.forms.models import Lead

pytestmark = pytest.mark.django_db


# AC-3: URL rezolvuje na /sr/htmx/forme/rezervni-delovi/ (locale-prefiksovan)
def test_part_request_submit_url_resolves_sr():
    activate("sr")
    assert reverse("forms:part_request_submit") == "/sr/htmx/forme/rezervni-delovi/", (
        "reverse('forms:part_request_submit') pod aktivnim sr MORA biti "
        "'/sr/htmx/forme/rezervni-delovi/' (i18n_patterns; AC3)."
    )


# AC-3 (low): i18n routing — hu i en takođe rezolvuju
@pytest.mark.parametrize("lang", ["hu", "en"])
def test_part_request_submit_url_resolves_per_locale(lang):
    activate(lang)
    url = reverse("forms:part_request_submit")
    assert url == f"/{lang}/htmx/forme/rezervni-delovi/", (
        f"reverse pod '{lang}' MORA biti '/{lang}/htmx/forme/rezervni-delovi/' (i18n_patterns)."
    )


# AC-3: endpoint je POST-only — GET → 405 (require_POST)
def test_part_request_submit_get_not_allowed(client, part_request_submit_url):
    response = client.get(part_request_submit_url)
    assert response.status_code == 405, (
        f"GET na part_request_submit MORA biti 405 (require_POST), dobio {response.status_code}."
    )


# AC-4: validan multipart POST SA slikom (single-file idiom) → 1 Lead sa očekivanim poljima
def test_valid_submit_with_photo_creates_lead(
    htmx_post,
    part_request_submit_url,
    part_request_payload,
    valid_image_jpeg,
    recipient_env,
    mailoutbox,
):
    payload = {**part_request_payload, "photo": valid_image_jpeg}
    response = htmx_post(part_request_submit_url, payload)

    assert response.status_code == 200, (
        f"Validan submit MORA vratiti 200, dobio {response.status_code}."
    )
    assert Lead.objects.count() == 1, "Validan submit MORA kreirati TAČNO 1 Lead (AC4)."

    lead = Lead.objects.get()
    assert lead.form_type == Lead.FormType.PART_REQUEST, (
        "Lead.form_type MORA biti 'part_request'."
    )
    assert lead.name == part_request_payload["name"]
    assert lead.phone == part_request_payload["phone"]
    assert lead.email == part_request_payload["email"]
    assert lead.message == "Pozovite popodne.", (
        "Lead.message MORA biti `note` (note → message — SM-D2)."
    )
    # data shape LOCKED (SM-D2): SVI ključevi prisutni
    assert lead.data == {
        "tractor_model": "Agri Tracking TB804",
        "part_name": "Filter ulja",
        "extra_description": "Original deo.",
        "payment_method": "cod",
        "delivery_method": "delivery",
    }, (
        f"Lead.data MORA biti puni SM-D2 shape (5 ključeva), dobio {lead.data!r}."
    )
    assert lead.locale == "sr", "Lead.locale MORA pratiti aktivni jezik (get_language)."
    assert lead.ip_address, "Lead.ip_address MORA biti popunjen iz request-a (AC4)."


# AC-4: 1 LeadAttachment red za 1 priloženu sliku
def test_valid_submit_persists_single_attachment(
    htmx_post,
    part_request_submit_url,
    part_request_payload,
    valid_image_jpeg,
    recipient_env,
    mailoutbox,
):
    payload = {**part_request_payload, "photo": valid_image_jpeg}
    htmx_post(part_request_submit_url, payload)

    lead = Lead.objects.get()
    assert lead.attachments.count() == 1, (
        f"1 priložena slika MORA dati 1 LeadAttachment red (AC4), dobio {lead.attachments.count()}."
    )


# AC-4: success partial template korišćen
def test_valid_submit_renders_success_partial(
    htmx_post,
    part_request_submit_url,
    part_request_payload,
    valid_image_jpeg,
    recipient_env,
    mailoutbox,
):
    payload = {**part_request_payload, "photo": valid_image_jpeg}
    response = htmx_post(part_request_submit_url, payload)

    template_names = [t.name for t in response.templates if t.name]
    assert "forms/partials/part_request_success.html" in template_names, (
        f"Success render MORA koristiti 'forms/partials/part_request_success.html', dobio "
        f"{template_names!r}."
    )


# AC-4/AC-5: 1 email; to==[PARTS_EMAIL_TO]; 1 email attachment; subject iz lead.data (NE lead.name)
def test_valid_submit_sends_email_with_attachment_and_subject(
    htmx_post,
    part_request_submit_url,
    part_request_payload,
    valid_image_jpeg,
    recipient_env,
    mailoutbox,
):
    payload = {**part_request_payload, "photo": valid_image_jpeg}
    htmx_post(part_request_submit_url, payload)

    assert len(mailoutbox) == 1, f"MORA biti TAČNO 1 email, dobio {len(mailoutbox)}."
    msg = mailoutbox[0]
    assert msg.to == [settings.PARTS_EMAIL_TO], (
        f"Email `to` MORA biti [PARTS_EMAIL_TO] ({settings.PARTS_EMAIL_TO!r}), dobio {msg.to!r}."
    )
    # AC-5 (KRITIČNO): subject iz lead.data {part_name} ({tractor_model}) — NE lead.name.
    # Ovaj assert FORSIRA _build_subject PART_REQUEST izmenu (trenutno vraća lead.name).
    assert "[Ćorić Agrar] Upit za rezervni deo: Filter ulja (Agri Tracking TB804)" in msg.subject, (
        f"Subject MORA biti '[Ćorić Agrar] Upit za rezervni deo: Filter ulja (Agri Tracking TB804)' "
        f"(iz lead.data — AC5/SM-D5; NE lead.name), dobio {msg.subject!r}."
    )
    assert "Marko Marković" not in msg.subject, (
        "Subject NE SME sadržati lead.name — mora biti part_name (tractor_model) iz data (AC5)."
    )
    assert len(msg.attachments) == 1, (
        f"Email MORA imati 1 attachment (priložena slika — attach-loop 4.4), dobio {len(msg.attachments)}."
    )


# AC-6: submit BEZ slike → Lead kreiran, attachments 0, email bez priloga
def test_valid_submit_without_photo(
    htmx_post,
    part_request_submit_url,
    part_request_payload,
    recipient_env,
    mailoutbox,
):
    response = htmx_post(part_request_submit_url, part_request_payload)
    assert response.status_code == 200
    assert Lead.objects.count() == 1, "Submit bez slike MORA kreirati Lead (foto opciono — AC6)."

    lead = Lead.objects.get()
    assert lead.attachments.count() == 0, "Bez slike → 0 LeadAttachment (AC6)."
    assert len(mailoutbox) == 1, "Bez slike → i dalje 1 email (AC6)."
    assert len(mailoutbox[0].attachments) == 0, "Bez slike → email BEZ priloga (AC6)."


# AC-6 (SM-D2 lock): prazan extra_description/note → data["extra_description"]=="" + message==""
def test_empty_optional_fields_data_shape(
    htmx_post,
    part_request_submit_url,
    part_request_payload,
    recipient_env,
    mailoutbox,
):
    payload = {**part_request_payload, "extra_description": "", "note": ""}
    htmx_post(part_request_submit_url, payload)

    lead = Lead.objects.get()
    assert lead.data["extra_description"] == "", (
        f"Prazan extra_description MORA dati data['extra_description']=='' (ključ PRISUTAN sa "
        f"praznim stringom, NE izostavljen — SM-D2 lock), dobio {lead.data!r}."
    )
    assert "extra_description" in lead.data, "Ključ 'extra_description' MORA biti prisutan (SM-D2)."
    assert lead.message == "", "Prazan note → Lead.message=='' (SM-D2)."


# AC-4: success response je PARTIAL (NEMA <html>/<head>)
def test_success_response_is_partial(
    htmx_post,
    part_request_submit_url,
    part_request_payload,
    recipient_env,
    mailoutbox,
):
    response = htmx_post(part_request_submit_url, part_request_payload)
    html = response.content.decode("utf-8").lower()
    assert "<html" not in html, "Success HTMX response NE SME imati <html> (partial)."
    assert "<head" not in html, "Success HTMX response NE SME imati <head> (partial)."


# AC-7 (simetrija): error response je TAKOĐE partial (NEMA <html>/<head>)
def test_error_response_is_partial(
    htmx_post,
    part_request_submit_url,
    part_request_payload,
    recipient_env,
    mailoutbox,
):
    payload = {**part_request_payload, "tractor_model": ""}
    response = htmx_post(part_request_submit_url, payload)
    html = response.content.decode("utf-8").lower()
    assert "<html" not in html, "Error HTMX response NE SME imati <html> (partial)."
    assert "<head" not in html, "Error HTMX response NE SME imati <head> (partial)."


# ── Task 3.4 — notifications.py direktan unit test (subject iz data + fallback + regression) ──


# AC-5: send_lead_email gradi subject iz lead.data (part_name + tractor_model)
def test_build_subject_uses_lead_data_for_part_request(recipient_env, mailoutbox):
    from apps.forms.notifications import send_lead_email

    lead = Lead.objects.create(
        form_type=Lead.FormType.PART_REQUEST,
        name="Marko Marković",
        email="marko@example.com",
        locale="sr",
        data={"part_name": "Filter ulja", "tractor_model": "Agri Tracking TB804"},
    )
    result = send_lead_email(lead)
    assert result is True, "send_lead_email MORA vratiti True na uspeh (recipient postavljen)."
    assert len(mailoutbox) == 1
    assert "Upit za rezervni deo: Filter ulja (Agri Tracking TB804)" in mailoutbox[0].subject, (
        f"_build_subject(PART_REQUEST) MORA graditi subject iz lead.data (part_name (tractor_model) "
        f"— AC5/SM-D5), dobio {mailoutbox[0].subject!r}."
    )


# AC-5 (OQ-6 RESOLVED — fallback): prazan data + postavljen name → subject SADRŽI lead.name, NE crash
def test_build_subject_fallback_empty_data_uses_lead_name(recipient_env, mailoutbox):
    from apps.forms.notifications import send_lead_email

    lead = Lead.objects.create(
        form_type=Lead.FormType.PART_REQUEST,
        name="Marko Marković",
        email="marko@example.com",
        locale="sr",
        data={},
    )
    result = send_lead_email(lead)
    assert result is True, (
        "send_lead_email sa praznim data NE SME crash-ovati (fallback .get(...,default) — SM-D5)."
    )
    assert len(mailoutbox) == 1
    subject = mailoutbox[0].subject
    assert "Marko Marković" in subject, (
        f"Prazan data → part_name default-uje na lead.name; subject MORA sadržati 'Marko Marković' "
        f"(SM-D5/OQ-6), dobio {subject!r}."
    )
    assert ": ()" not in subject, (
        f"Subject NIKAD ne sme biti '...: ()' (fallback obezbeđuje informativnost), dobio {subject!r}."
    )


# AC-5 (regression): KONTAKT subject grana NETAKNUTA (koristi lead.name)
def test_build_subject_kontakt_branch_unchanged(recipient_env, mailoutbox):
    from apps.forms.notifications import send_lead_email

    lead = Lead.objects.create(
        form_type=Lead.FormType.KONTAKT,
        name="Marko Marković",
        email="marko@example.com",
        locale="sr",
    )
    send_lead_email(lead)
    assert "Novi kontakt: Marko Marković" in mailoutbox[0].subject, (
        f"KONTAKT subject grana MORA ostati NETAKNUTA (lead.name — regression), dobio "
        f"{mailoutbox[0].subject!r}."
    )


# AC-5 (regression): SERVICE_REQUEST subject grana NETAKNUTA (koristi lead.name)
def test_build_subject_service_request_branch_unchanged(recipient_env, mailoutbox):
    from apps.forms.notifications import send_lead_email

    lead = Lead.objects.create(
        form_type=Lead.FormType.SERVICE_REQUEST,
        name="Stojan Stojanović",
        email="stojan@example.com",
        locale="sr",
    )
    send_lead_email(lead)
    assert "Novi servisni zahtev: Stojan Stojanović" in mailoutbox[0].subject, (
        f"SERVICE_REQUEST subject grana MORA ostati NETAKNUTA (lead.name — regression), dobio "
        f"{mailoutbox[0].subject!r}."
    )


# AC-5 (regression): MODEL_INQUIRY subject grana NETAKNUTA (koristi data['product_name'])
def test_build_subject_model_inquiry_branch_unchanged(recipient_env, mailoutbox):
    from apps.forms.notifications import send_lead_email

    lead = Lead.objects.create(
        form_type=Lead.FormType.MODEL_INQUIRY,
        name="Marko Marković",
        email="marko@example.com",
        locale="sr",
        data={"product_slug": "agri-tracking-tb804", "product_name": "Agri Tracking TB804"},
    )
    send_lead_email(lead)
    assert "Upit za model: Agri Tracking TB804" in mailoutbox[0].subject, (
        f"MODEL_INQUIRY subject grana MORA ostati NETAKNUTA (data['product_name'] — regression), "
        f"dobio {mailoutbox[0].subject!r}."
    )


# AC-5 (regression — SM-D6): recipient PART_REQUEST → PARTS_EMAIL_TO (NETAKNUT)
def test_resolve_recipient_part_request_unchanged(recipient_env):
    from apps.forms.notifications import _resolve_recipient

    lead = Lead.objects.create(
        form_type=Lead.FormType.PART_REQUEST,
        name="Marko Marković",
        email="marko@example.com",
    )
    assert _resolve_recipient(lead) == settings.PARTS_EMAIL_TO, (
        "_resolve_recipient(PART_REQUEST) MORA vratiti PARTS_EMAIL_TO (SM-D6 — NETAKNUT)."
    )
