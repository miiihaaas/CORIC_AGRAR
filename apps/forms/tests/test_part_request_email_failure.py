"""Story 4.5 — AC7: email-failure ne ruši UX (graceful degradation) — TEA RED phase.

Pokriva Task 4.4 (REUSE 4.2/4.4 SM-D5 obrazac): kad `send_lead_email(lead)` vrati False,
Lead I opciona slika (LeadAttachment) OSTAJU sačuvani (NIJE rollback) i posetilac i dalje
dobija success partial.

Mock SAMO servis-povratnu vrednost (`apps.forms.views.send_lead_email` → False), NIKAD
Django ORM (project-context.md:267) — Lead + LeadAttachment se realno upisuju u test DB.

RED razlog: apps.forms.views part_request_submit ne postoji → mock.patch target ne postoji.

Pokrenuti:
    just test apps/forms/tests/test_part_request_email_failure.py -v

Refs: 4-5 AC7 + Task 4.4 + SM-D5; interface-contract § 3.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.django_db


# DEFENSIVE (subject render guard): PART_REQUEST subject pod non-sr locale ne sme crash-ovati.
# _build_subject interpolira `%(part)s (%(model)s)` placeholder-e. Ako budući hu/en prevodilac
# dostavi msgstr sa neusklađenim placeholder-om, runtime interpolacija bi KeyError-ovala. Trenutni
# hu msgstr je prazan → fallback na source string → prolazi sad; ovaj test čuva od loše buduće
# translacije (render-ne-crash-uje garancija, NE asertuje prevedeni tekst).
def test_part_request_subject_hu_locale_does_not_crash(recipient_env, mailoutbox):
    from apps.forms.models import Lead

    from apps.forms.notifications import send_lead_email

    lead = Lead.objects.create(
        form_type=Lead.FormType.PART_REQUEST,
        name="Marko Marković",
        email="marko@example.com",
        locale="hu",
        data={"part_name": "Filter ulja", "tractor_model": "TB804"},
    )

    # NE sme raise-ovati (KeyError iz loše-prevedenog placeholder-a) i MORA poslati 1 email.
    result = send_lead_email(lead)
    assert result is True, "send_lead_email MORA uspeti za hu PART_REQUEST (recipient popunjen)."
    assert len(mailoutbox) == 1, "hu PART_REQUEST MORA proizvesti TAČNO 1 email."
    assert "Filter ulja" in mailoutbox[0].subject, (
        "hu subject MORA sadržati part_name (fallback na sr source string dok hu prevod fali)."
    )


# AC-7: send_lead_email → False → Lead + opciona slika OSTAJU (NIJE rollback); success partial
def test_email_failure_keeps_lead_and_attachment(
    htmx_post,
    part_request_submit_url,
    part_request_payload,
    valid_image_jpeg,
    recipient_env,
    mailoutbox,
    mocker,
):
    from apps.forms.models import Lead, LeadAttachment

    mocker.patch("apps.forms.views.send_lead_email", return_value=False)

    payload = {**part_request_payload, "photo": valid_image_jpeg}
    response = htmx_post(part_request_submit_url, payload)

    assert response.status_code == 200
    assert Lead.objects.count() == 1, (
        "Email-failure NE SME rollback-ovati Lead — lead JE u DB (AC7; email retry je interni problem)."
    )
    assert LeadAttachment.objects.count() == 1, (
        "Email-failure NE SME rollback-ovati attachment — slika OSTAJE u DB (AC7)."
    )

    template_names = [t.name for t in response.templates if t.name]
    assert "forms/partials/part_request_success.html" in template_names, (
        "Posetilac i dalje MORA videti success partial i kad send_lead_email vrati False (SM-D5)."
    )


# AC-7: send_lead_email JESTE pozvan sa VEĆ sačuvanim lead-om (save-before-send — pk popunjen)
def test_email_failure_service_called_with_saved_lead(
    htmx_post,
    part_request_submit_url,
    part_request_payload,
    recipient_env,
    mailoutbox,
    mocker,
):
    spy = mocker.patch("apps.forms.views.send_lead_email", return_value=False)

    htmx_post(part_request_submit_url, part_request_payload)
    assert spy.call_count == 1, "send_lead_email MORA biti pozvan TAČNO 1 put (AC7)."
    called_lead = spy.call_args.args[0]
    assert called_lead.pk is not None, (
        "send_lead_email MORA primiti VEĆ sačuvan Lead (save-before-send — pk popunjen)."
    )


# SECURITY (4-5 Mandatory): CRLF u part_name (header-injection pokušaj) → NEMA 500, NEMA smuggle.
# Subject interpolira USER-supplied part_name/tractor_model; CRLF bi (a) izazvao Django
# BadHeaderError → bez fix-a 500 (krši C1, lead je već commit-ovan), i (b) pokušao Bcc smuggling.
# Fix: _no_crlf strip (defense-in-depth) + BadHeaderError u except tuple (degradacija na False).
def test_part_name_crlf_does_not_500_or_smuggle_header(
    htmx_post,
    part_request_submit_url,
    part_request_payload,
    recipient_env,
    mailoutbox,
):
    from apps.forms.models import Lead

    payload = {
        **part_request_payload,
        "part_name": "Filter\r\nBcc: evil@example.com",
        "tractor_model": "TB804\r\nX-Injected: 1",
    }
    response = htmx_post(part_request_submit_url, payload)

    # (a) Posetilac dobija success partial — NIKAD 500 (C1: email kvar ne ruši UX).
    assert response.status_code == 200, (
        "CRLF u part_name NE SME izazvati 500 — graceful degradacija (C1 + security 4-5)."
    )
    template_names = [t.name for t in response.templates if t.name]
    assert "forms/partials/part_request_success.html" in template_names, (
        "Posetilac MORA videti success partial čak i uz CRLF-injection pokušaj (C1)."
    )

    # (b) Lead JE perzistiran (atomic commit pre send-a; CRLF ne sme rollback-ovati).
    assert Lead.objects.count() == 1, "Lead MORA ostati sačuvan i uz CRLF-injection pokušaj."

    # (c) NEMA smuggle-ovanog header-a: CRLF je neutralizovan u razmak, pa evil@example.com
    #     ostaje BEZAZLEN plaintext u Subject-u (NIJE Bcc). Bezbednosna garancija = NEMA CR/LF u
    #     Subject-u + NEMA stvarnog Bcc primaoca + NEMA injektovanog extra header-a.
    if mailoutbox:
        msg = mailoutbox[0]
        assert "\r" not in msg.subject and "\n" not in msg.subject, (
            "Subject NE SME sadržati CR/LF (header-injection vektor neutralizovan)."
        )
        assert "evil@example.com" not in msg.bcc, "NEMA smuggle-ovanog Bcc primaoca."
        assert "X-Injected" not in msg.extra_headers, "NEMA smuggle-ovanog extra header-a."
