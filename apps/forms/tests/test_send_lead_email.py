"""Story 4.1 — AC4/AC8 `send_lead_email(lead)` happy-path (TEA RED phase).

Pokriva AC4/AC8: save-before-send (Lead perzistiran PRE poziva); funkcija vraća True;
TAČNO 1 email u mailoutbox; `to` po form_type (parametrizovano 4 form_type-a → CONTACT/
SERVICE/PARTS recipient, SM-D7); from_email==DEFAULT_FROM_EMAIL; subject sadrži
„[Ćorić Agrar]" + pun dijakritik; body sadrži lead podatke; SYNC (email odmah posle
poziva). NIKAD pravi send — `mailoutbox` (locmem).

TEA RED phase: SVI testovi MORAJU pasti — apps.forms.notifications ne postoji.

Refs:
- 4-1-lead-model-smtp-setup.md AC4 + AC8 + Task 8.5 + SM-D5/D7
- 4-1-interface-contract.md § 4 (send_lead_email)
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.django_db


# AC4/AC8: recipient rezolucija po form_type (parametrizovano 4 form_type-a — SM-D7)
@pytest.mark.parametrize(
    "form_type_member,expected_setting_attr",
    [
        ("KONTAKT", "CONTACT_EMAIL_TO"),
        ("MODEL_INQUIRY", "CONTACT_EMAIL_TO"),  # deli kontakt recipient (OQ-2)
        ("SERVICE_REQUEST", "SERVICE_EMAIL_TO"),
        ("PART_REQUEST", "PARTS_EMAIL_TO"),
    ],
)
def test_send_lead_email_recipient_by_form_type(
    form_type_member, expected_setting_attr, recipient_env, mailoutbox
):
    from apps.forms.models import Lead
    from apps.forms.notifications import send_lead_email

    form_type = getattr(Lead.FormType, form_type_member)
    lead = Lead.objects.create(
        form_type=form_type,
        name="Marko Marković",
        email="marko@example.com",
        phone="+381 11 222 333",
        message="Test poruka.",
        locale="sr",
    )

    result = send_lead_email(lead)

    assert result is True, (
        f"send_lead_email MORA vratiti True na uspeh ({form_type_member}), dobio {result!r}."
    )
    assert len(mailoutbox) == 1, (
        f"MORA biti TAČNO 1 email u mailoutbox za {form_type_member}, dobio {len(mailoutbox)}."
    )
    expected_to = getattr(recipient_env, expected_setting_attr)
    assert mailoutbox[0].to == [expected_to], (
        f"{form_type_member} email `to` MORA biti [{expected_to!r}] "
        f"({expected_setting_attr} — SM-D7), dobio {mailoutbox[0].to!r}."
    )


# AC4/AC8: save-before-send — Lead perzistiran PRE poziva (count==1)
def test_lead_persisted_before_send(recipient_env, mailoutbox):
    from apps.forms.models import Lead
    from apps.forms.notifications import send_lead_email

    lead = Lead.objects.create(
        form_type=Lead.FormType.KONTAKT, name="Ana Anić", email="ana@example.com", locale="sr"
    )
    assert Lead.objects.count() == 1, "Lead MORA biti perzistiran PRE send-a (save-before-send AC4)."

    send_lead_email(lead)

    assert Lead.objects.filter(pk=lead.pk).exists(), "Lead OSTAJE sačuvan posle send-a."


# AC4/AC8: from_email == DEFAULT_FROM_EMAIL
def test_send_lead_email_from_is_default_from_email(recipient_env, mailoutbox):
    from apps.forms.models import Lead
    from apps.forms.notifications import send_lead_email

    lead = Lead.objects.create(
        form_type=Lead.FormType.KONTAKT, name="Jovan Jovanović", email="jovan@example.com", locale="sr"
    )
    send_lead_email(lead)

    assert len(mailoutbox) == 1
    assert mailoutbox[0].from_email == recipient_env.DEFAULT_FROM_EMAIL, (
        f"from_email MORA biti settings.DEFAULT_FROM_EMAIL ({recipient_env.DEFAULT_FROM_EMAIL!r}), "
        f"dobio {mailoutbox[0].from_email!r}."
    )


# AC4/AC8: subject sadrži „[Ćorić Agrar]" + pun dijakritik (sr); body sadrži lead podatke
def test_send_lead_email_subject_and_body_content(recipient_env, mailoutbox):
    from apps.forms.models import Lead
    from apps.forms.notifications import send_lead_email

    lead = Lead.objects.create(
        form_type=Lead.FormType.KONTAKT,
        name="Đorđe Đorđević",
        email="djordje@example.com",
        message="Zanima me ponuda traktora.",
        locale="sr",
    )
    send_lead_email(lead)

    assert len(mailoutbox) == 1
    msg = mailoutbox[0]
    assert "[Ćorić Agrar]" in msg.subject, (
        f"subject MORA sadržati '[Ćorić Agrar]' (pun dijakritik — epics.md:790), "
        f"dobio {msg.subject!r}."
    )
    # body (telo ili HTML alternative) MORA sadržati lead podatke (ime + email)
    bodies = [msg.body] + [content for content, _mime in getattr(msg, "alternatives", [])]
    joined = "\n".join(bodies)
    assert "Đorđe Đorđević" in joined, (
        f"email telo MORA sadržati ime lead-a, telo: {joined[:300]!r}."
    )
    assert "djordje@example.com" in joined, "email telo MORA sadržati email lead-a."
