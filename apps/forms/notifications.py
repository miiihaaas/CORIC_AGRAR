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
import mimetypes
import os
import smtplib

from anymail.exceptions import AnymailError
from django.conf import settings
from django.core.mail import BadHeaderError, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import translation
from django.utils.html import strip_tags
from django.utils.translation import gettext as _

from apps.forms.models import Lead

logger = logging.getLogger(__name__)


def _no_crlf(value: str) -> str:
    """Defense-in-depth: izbaci CR/LF iz USER-supplied vrednosti koje idu u Subject header.

    Story 4.5 PART_REQUEST interpolira slobodan tekst (`part_name`/`tractor_model`) u Subject.
    CRLF u tom tekstu izaziva Django `BadHeaderError` (blokira header smuggling — dobro), ali bi
    inače propagirao kao 500. Strip-ujemo \r/\n → razmak da subject bude čist i da greška NE nastane
    (primarni catch u send_lead_email i dalje hvata BadHeaderError za sve ostale slučajeve — C1).
    """
    return (value or "").replace("\r", " ").replace("\n", " ")


# Subject format po form_type (mapira epics.md:790/803/831 — sadrži "[Ćorić Agrar]")
def _build_subject(lead: Lead) -> str:
    if lead.form_type == Lead.FormType.SERVICE_REQUEST:
        return _("[Ćorić Agrar] Novi servisni zahtev: %(name)s") % {
            "name": _no_crlf(lead.name)
        }
    if lead.form_type == Lead.FormType.PART_REQUEST:
        return _("[Ćorić Agrar] Upit za rezervni deo: %(part)s (%(model)s)") % {
            # fallback na lead.name (OQ-6); CRLF-strip (defense-in-depth, security 4-5)
            "part": _no_crlf(lead.data.get("part_name", lead.name)),
            # fallback prazan string; CRLF-strip
            "model": _no_crlf(lead.data.get("tractor_model", "")),
        }
    if lead.form_type == Lead.FormType.MODEL_INQUIRY:
        return _("[Ćorić Agrar] Upit za model: %(name)s") % {
            "name": _no_crlf(lead.data.get("product_name", lead.name))
        }
    return _("[Ćorić Agrar] Novi kontakt: %(name)s") % {"name": _no_crlf(lead.name)}


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
        # Story 4.4 (SM-D5) — attach servisne slike PRE send-a. Prazan queryset (kontakt/
        # model-inquiry/service-bez-slika) → no-op (regression). Context manager je handle-safe.
        # Čitanje fajla je UNUTAR try/except: file-read OSError (nedostaje fajl na disku /
        # unmounted media volume / permission) → graceful return False (C1 NETAKNUT), NE 500.
        for attachment in lead.attachments.all():
            with attachment.file.open("rb") as f:
                content = f.read()
            name = os.path.basename(attachment.file.name)
            mimetype = mimetypes.guess_type(name)[0] or "application/octet-stream"
            message.attach(name, content, mimetype)

        message.send()
    except (AnymailError, smtplib.SMTPException, OSError, BadHeaderError):
        # Uži boundary ka third-party (Resend) / SMTP transport-u + attachment file-read +
        # BadHeaderError (CRLF u user-supplied Subject vrednosti → Django blokira smuggling, ali
        # mi degradiramo na return False umesto 500 — C1 za SVE form tipove, security 4-5) (C1).
        # Programski bug-ovi (TemplateDoesNotExist/TypeError/AttributeError) NAMERNO propagiraju.
        logger.exception(
            "send_lead_email: provider send ili attachment-read pao za lead pk=%s "
            "(form_type=%r) — lead OSTAJE sačuvan; GlitchTip-capturable.",
            lead.pk,
            lead.form_type,
        )
        return False
    return True
