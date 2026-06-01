"""Story 4.1 — reusable email service `send_lead_email(lead)` (SM-D5/SM-D7).

SYNC (NO Celery — project-context.md:84/127), VIEW-CALLED (NE post_save signal).
Prima VEĆ sačuvanu Lead instancu (save-before-send ugovor za 4-2+); NE save-uje,
NE rollback-uje. Recipient rezolucija po `lead.form_type`; subject lokalizovan po
`lead.locale`; telo iz `templates/emails/lead_received.html`.

FAILURE CONTRACT (C1 — LOCKED): provider-send poziv obavijen u try/except (specifičan
exception, NE bare); na fail → `logger.exception(...)` (GlitchTip-capturable) + return
False. Prazan recipient → tretira se kao failed send (log + return False). NIKAD re-raise.

Refs: 4-1-lead-model-smtp-setup.md AC4/AC8/AC9; 4-1-interface-contract.md § 4.
"""

from __future__ import annotations

import logging
import smtplib

from anymail.exceptions import AnymailError
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import translation
from django.utils.html import strip_tags
from django.utils.translation import gettext as _

from apps.forms.models import Lead

logger = logging.getLogger(__name__)


# Subject format po form_type (mapira epics.md:790/803/831 — sadrži "[Ćorić Agrar]")
def _build_subject(lead: Lead) -> str:
    if lead.form_type == Lead.FormType.SERVICE_REQUEST:
        return _("[Ćorić Agrar] Novi servisni zahtev: %(name)s") % {"name": lead.name}
    if lead.form_type == Lead.FormType.PART_REQUEST:
        return _("[Ćorić Agrar] Upit za rezervni deo: %(name)s") % {"name": lead.name}
    if lead.form_type == Lead.FormType.MODEL_INQUIRY:
        return _("[Ćorić Agrar] Upit za model: %(name)s") % {"name": lead.name}
    return _("[Ćorić Agrar] Novi kontakt: %(name)s") % {"name": lead.name}


def _resolve_recipient(lead: Lead) -> str:
    """Recipient po `lead.form_type` (SM-D7) — poredi sa FormType member-ima."""
    if lead.form_type == Lead.FormType.SERVICE_REQUEST:
        return getattr(settings, "SERVICE_EMAIL_TO", "") or ""
    if lead.form_type == Lead.FormType.PART_REQUEST:
        return getattr(settings, "PARTS_EMAIL_TO", "") or ""
    # KONTAKT + MODEL_INQUIRY dele kontakt recipient (OQ-2)
    return getattr(settings, "CONTACT_EMAIL_TO", "") or ""


def send_lead_email(lead: Lead) -> bool:
    """SYNC; prima VEĆ sačuvanu Lead instancu (save-before-send). View-called (NE signal).

    Vraća True na uspeh, False na fail (provider exception ILI prazan recipient).
    NE re-raise; NE rollback Lead-a.
    """
    recipient = _resolve_recipient(lead)
    if not recipient:
        logger.error(
            "send_lead_email: prazan recipient za form_type=%r (lead pk=%s) — "
            "env recipient nije popunjen; tretiram kao failed send (C1).",
            lead.form_type,
            lead.pk,
        )
        return False

    # Subject + telo lokalizovani po lead.locale (translation.override + gettext runtime)
    with translation.override(lead.locale or "sr"):
        subject = _build_subject(lead)
        # `locale` u context-u → email `<html lang=...>` prati lead.locale (render_to_string
        # nema request, pa LANGUAGE_CODE nije dostupan u template-u).
        html_body = render_to_string(
            "emails/lead_received.html",
            {"lead": lead, "locale": lead.locale or "sr"},
        )

    # text/plain part MORA biti čist tekst (ne sirov HTML) — bolja deliverability +
    # ispravan prikaz u text-mode klijentima. HTML ide kao alternative (multipart/alternative).
    plain_body = strip_tags(html_body)

    message = EmailMultiAlternatives(
        subject=subject,
        body=plain_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[recipient],
    )
    message.attach_alternative(html_body, "text/html")

    try:
        message.send()
    except (AnymailError, smtplib.SMTPException, OSError):
        # Uži boundary ka third-party (Resend) / SMTP transport-u (C1). Programski
        # bug-ovi (TemplateDoesNotExist/TypeError/AttributeError) NAMERNO propagiraju.
        logger.exception(
            "send_lead_email: provider send pao za lead pk=%s (form_type=%r) — "
            "lead OSTAJE sačuvan; GlitchTip-capturable.",
            lead.pk,
            lead.form_type,
        )
        return False
    return True
