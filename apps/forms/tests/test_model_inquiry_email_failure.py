"""Story 4.3 — AC4 (SM-D5 obrazac): email-failure ne ruši UX (graceful degradation) — TEA RED.

Pokriva Task 4.2: kad `send_lead_email(lead)` vrati False (provider fail), Lead OSTAJE
sačuvan (NIJE rollback) i posetilac i dalje dobija success partial.

Mock SAMO servis-povratnu vrednost (`apps.forms.views.send_lead_email` → False), NIKAD
Django ORM (project-context.md:267) — Lead se realno upisuje u test DB.

RED razlog: apps.forms.views model_inquiry_submit ne postoji → mock.patch target / 404 → padaju.

Pokrenuti:
    just test apps/forms/tests/test_model_inquiry_email_failure.py -v

Refs: 4-3 Task 4.2 + 4.2 SM-D5; interface-contract § 2.
"""

from __future__ import annotations

import pytest

from apps.forms.models import Lead
from apps.products.tests.factories import ProductFactory

pytestmark = pytest.mark.django_db


# AC-4/Task 4.2: send_lead_email → False → Lead OSTAJE (count==1, NIJE rollback)
def test_email_failure_keeps_lead(
    htmx_post, model_inquiry_submit_url, model_inquiry_payload, recipient_env, mailoutbox, mocker
):
    mocker.patch("apps.forms.views.send_lead_email", return_value=False)
    product = ProductFactory.create(name="Agri Tracking TB804")
    payload = {**model_inquiry_payload, "product_slug": product.slug}

    response = htmx_post(model_inquiry_submit_url, payload)
    assert response.status_code == 200
    assert Lead.objects.count() == 1, (
        "Email-failure NE SME rollback-ovati Lead — lead JE u DB (lead primljen, email retry "
        "je interni problem)."
    )


# AC-4/Task 4.2: posetilac i dalje dobija success partial
def test_email_failure_still_shows_success(
    htmx_post, model_inquiry_submit_url, model_inquiry_payload, recipient_env, mailoutbox, mocker
):
    mocker.patch("apps.forms.views.send_lead_email", return_value=False)
    product = ProductFactory.create(name="Agri Tracking TB804")
    payload = {**model_inquiry_payload, "product_slug": product.slug}

    response = htmx_post(model_inquiry_submit_url, payload)
    template_names = [t.name for t in response.templates if t.name]
    assert "forms/partials/model_inquiry_success.html" in template_names, (
        "Posetilac i dalje MORA videti success partial i kad send_lead_email vrati False "
        "(SM-D5 default = čist success)."
    )


# AC-4/Task 4.2: send_lead_email JESTE pozvan sa VEĆ sačuvanim lead-om (save-before-send)
def test_email_failure_service_called_with_saved_lead(
    htmx_post, model_inquiry_submit_url, model_inquiry_payload, recipient_env, mailoutbox, mocker
):
    spy = mocker.patch("apps.forms.views.send_lead_email", return_value=False)
    product = ProductFactory.create(name="Agri Tracking TB804")
    payload = {**model_inquiry_payload, "product_slug": product.slug}

    htmx_post(model_inquiry_submit_url, payload)
    assert spy.call_count == 1, "send_lead_email MORA biti pozvan TAČNO 1 put (Task 4.2)."
    called_lead = spy.call_args.args[0]
    assert called_lead.pk is not None, (
        "send_lead_email MORA primiti VEĆ sačuvan Lead (save-before-send — pk popunjen)."
    )
