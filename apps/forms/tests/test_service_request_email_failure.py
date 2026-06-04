"""Story 4.4 — AC7: email-failure ne ruši UX (graceful degradation) — TEA RED phase.

Pokriva Task 4.4 (REUSE 4.2 SM-D5 obrazac): kad `send_lead_email(lead)` vrati False,
Lead I attachment-i OSTAJU sačuvani (NIJE rollback) i posetilac i dalje dobija success partial.

Mock SAMO servis-povratnu vrednost (`apps.forms.views.send_lead_email` → False), NIKAD
Django ORM (project-context.md:267) — Lead + LeadAttachment se realno upisuju u test DB.

RED razlog: apps.forms.views service_request_submit ne postoji → mock.patch target ne postoji.

Pokrenuti:
    just test apps/forms/tests/test_service_request_email_failure.py -v

Refs: 4-4 AC7 + Task 4.4 + SM-D5; interface-contract § 3.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.django_db


# AC-7: send_lead_email → False → Lead + attachment-i OSTAJU (NIJE rollback); success partial
def test_email_failure_keeps_lead_and_attachments(
    htmx_post,
    service_request_submit_url,
    service_request_payload,
    valid_image_jpeg,
    valid_image_png,
    recipient_env,
    mailoutbox,
    mocker,
):
    from apps.forms.models import Lead, LeadAttachment

    mocker.patch("apps.forms.views.send_lead_email", return_value=False)

    payload = {**service_request_payload, "photos": [valid_image_jpeg, valid_image_png]}
    response = htmx_post(service_request_submit_url, payload)

    assert response.status_code == 200
    assert Lead.objects.count() == 1, (
        "Email-failure NE SME rollback-ovati Lead — lead JE u DB (AC7; email retry je interni problem)."
    )
    assert LeadAttachment.objects.count() == 2, (
        "Email-failure NE SME rollback-ovati attachment-e — slike OSTAJU u DB (AC7)."
    )

    template_names = [t.name for t in response.templates if t.name]
    assert "forms/partials/service_request_success.html" in template_names, (
        "Posetilac i dalje MORA videti success partial i kad send_lead_email vrati False (SM-D5)."
    )


# AC-7: send_lead_email JESTE pozvan sa VEĆ sačuvanim lead-om (save-before-send — pk popunjen)
def test_email_failure_service_called_with_saved_lead(
    htmx_post,
    service_request_submit_url,
    service_request_payload,
    recipient_env,
    mailoutbox,
    mocker,
):
    spy = mocker.patch("apps.forms.views.send_lead_email", return_value=False)

    htmx_post(service_request_submit_url, service_request_payload)
    assert spy.call_count == 1, "send_lead_email MORA biti pozvan TAČNO 1 put (AC7)."
    called_lead = spy.call_args.args[0]
    assert called_lead.pk is not None, (
        "send_lead_email MORA primiti VEĆ sačuvan Lead (save-before-send — pk popunjen)."
    )
