"""Story 4.1 — AC4/C1 `send_lead_email` FAILURE CONTRACT (TEA RED phase).

Pokriva AC4/C1:
- Provider send baca (Resend 500 / timeout / loš key) → `send_lead_email` HVATA, LOGUJE
  (logger.exception → GlitchTip-capturable), VRAĆA `False` (NE re-raise) i perzistirani
  Lead red i dalje POSTOJI (NIJE rollback-ovan; save je prethodio send-u).
- Prazan/nedostajući recipient (env recipient "") → tretira se kao failed send (False + log),
  Lead ostaje, NEMA uncaught exception.

Mock SAMO eksterni provider-send put (project-context.md:267) — patch-uje Django mail
send tako da baci. NIKAD pravi network send.

TEA RED phase: SVI testovi MORAJU pasti — apps.forms.notifications ne postoji.

Refs:
- 4-1-lead-model-smtp-setup.md AC4 (C1) + Task 8.5b + SM-D5
- 4-1-interface-contract.md § 4 (FAILURE CONTRACT)
"""

from __future__ import annotations

import logging
import smtplib

import pytest

pytestmark = pytest.mark.django_db


# AC4/C1: provider send baca → send_lead_email vraća False (NE propušta) + loguje + Lead ostaje
def test_provider_failure_returns_false_logs_and_keeps_lead(
    recipient_env, mailoutbox, caplog, monkeypatch
):
    from django.core.mail import EmailMultiAlternatives

    from apps.forms.models import Lead
    from apps.forms import notifications

    lead = Lead.objects.create(
        form_type=Lead.FormType.KONTAKT, name="Marko Marković", email="marko@example.com", locale="sr"
    )

    def _boom(*args, **kwargs):
        # Realističan transport/provider exception (SMTP/Resend), NE generički RuntimeError —
        # failure contract hvata SAMO transport-exception set (AnymailError/SMTPException/OSError),
        # dok programski bug-ovi (TypeError/TemplateDoesNotExist) namerno propagiraju.
        raise smtplib.SMTPException("Resend 500 — simulirani provider fail")

    # EFEKTIVAN patch je `EmailMultiAlternatives.send` — send_lead_email koristi
    # `EmailMultiAlternatives.send()` (NE `send_mail`) kao NAJ-eksterniji provider-send poziv.
    monkeypatch.setattr(EmailMultiAlternatives, "send", _boom, raising=False)

    with caplog.at_level(logging.ERROR):
        result = notifications.send_lead_email(lead)

    assert result is False, (
        f"send_lead_email MORA vratiti False na provider fail (NE re-raise), dobio {result!r} "
        "(C1 failure contract)."
    )
    # Lead red i dalje postoji (NIJE rollback-ovan — save je prethodio send-u)
    assert Lead.objects.filter(pk=lead.pk).exists(), (
        "Perzistirani Lead red MORA OSTATI posle provider fail-a (save-before-send; "
        "`except` NE rollback-uje red — C1)."
    )
    # Fail je observable — logovan (logger.exception/error → GlitchTip-capturable)
    assert any(rec.levelno >= logging.ERROR for rec in caplog.records), (
        "send_lead_email MORA LOGOVATI fail (logger.exception/error — GlitchTip-capturable; "
        f"project-context.md:125). caplog records: {[r.message for r in caplog.records]}."
    )


# AC4/C1: prazan/nedostajući recipient → False + log + Lead ostaje (NEMA uncaught)
def test_empty_recipient_returns_false_logs_and_keeps_lead(settings, mailoutbox, caplog):
    from apps.forms.models import Lead
    from apps.forms.notifications import send_lead_email

    # Recipient env PRAZAN (realan dev/staging slučaj pre OQ-4)
    settings.CONTACT_EMAIL_TO = ""
    settings.SERVICE_EMAIL_TO = ""
    settings.PARTS_EMAIL_TO = ""
    settings.DEFAULT_FROM_EMAIL = "no-reply@coricagrar.rs"

    lead = Lead.objects.create(
        form_type=Lead.FormType.KONTAKT, name="Ana Anić", email="ana@example.com", locale="sr"
    )

    with caplog.at_level(logging.ERROR):
        result = send_lead_email(lead)

    assert result is False, (
        f"prazan recipient MORA dati False (tretira se kao failed send — C1), dobio {result!r}."
    )
    assert Lead.objects.filter(pk=lead.pk).exists(), (
        "Lead MORA OSTATI sačuvan i kad je recipient prazan (NEMA rollback)."
    )
    assert any(rec.levelno >= logging.ERROR for rec in caplog.records), (
        "prazan recipient MORA biti logovan (fail observable — C1)."
    )
    # NEMA poslatog email-a (nema recipient-a)
    assert len(mailoutbox) == 0, (
        f"prazan recipient NE SME poslati email, dobio {len(mailoutbox)} u mailoutbox."
    )
