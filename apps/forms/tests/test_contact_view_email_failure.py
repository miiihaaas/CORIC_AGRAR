"""Story 4.2 — AC5: email-failure ne ruši UX (graceful degradation) — TEA RED phase.

Pokriva AC5/SM-D5: kad `send_lead_email(lead)` vrati False (provider fail ILI prazan
recipient), Lead OSTAJE sačuvan (NIJE rollback) i posetilac i dalje dobija success partial.

Mock SAMO servis-povratnu vrednost (`apps.forms.views.send_lead_email` → False), NIKAD
Django ORM (project-context.md:267) — Lead se realno upisuje u test DB.

RED razlog: apps.forms.views ne postoji → mock.patch target ne postoji / 404 → padaju.

Pokrenuti:
    just test apps/forms/tests/test_contact_view_email_failure.py -v

Refs: 4-2 AC5 + Task 3.2 + SM-D5; interface-contract § 2.
"""

from __future__ import annotations

import pytest

from apps.forms.models import Lead

pytestmark = pytest.mark.django_db


# AC-5: send_lead_email → False → Lead OSTAJE (count==1, NIJE rollback)
def test_email_failure_keeps_lead(
    htmx_post, contact_submit_url, valid_contact_payload, recipient_env, mailoutbox, mocker
):
    mocker.patch("apps.forms.views.send_lead_email", return_value=False)

    response = htmx_post(contact_submit_url, valid_contact_payload)
    assert response.status_code == 200
    assert Lead.objects.count() == 1, (
        "Email-failure NE SME rollback-ovati Lead — lead JE u DB (AC5; lead primljen, email "
        "retry je interni problem)."
    )


# AC-5: posetilac i dalje dobija success partial (SM-D5 default = čist success)
def test_email_failure_still_shows_success(
    htmx_post, contact_submit_url, valid_contact_payload, recipient_env, mailoutbox, mocker
):
    mocker.patch("apps.forms.views.send_lead_email", return_value=False)

    response = htmx_post(contact_submit_url, valid_contact_payload)
    template_names = [t.name for t in response.templates if t.name]
    assert "forms/partials/contact_success.html" in template_names, (
        "Posetilac i dalje MORA videti success partial i kad send_lead_email vrati False "
        "(SM-D5 default = čist success)."
    )
    assert "Hvala! Vaš upit je primljen." in response.content.decode("utf-8"), (
        "Success partial MORA sadržati TAČNU poruku „Hvala! Vaš upit je primljen.” (puni "
        "dijakritik) čak i pri email-failure (AC5/AC9)."
    )


# AC-5: send_lead_email JESTE pozvan (sa sačuvanim lead-om koji ima pk — save-before-send)
def test_email_failure_service_was_called_with_saved_lead(
    htmx_post, contact_submit_url, valid_contact_payload, recipient_env, mailoutbox, mocker
):
    spy = mocker.patch("apps.forms.views.send_lead_email", return_value=False)

    htmx_post(contact_submit_url, valid_contact_payload)
    assert spy.call_count == 1, "send_lead_email MORA biti pozvan TAČNO 1 put (AC5)."
    called_lead = spy.call_args.args[0]
    assert called_lead.pk is not None, (
        "send_lead_email MORA primiti VEĆ sačuvan Lead (save-before-send — pk popunjen)."
    )
