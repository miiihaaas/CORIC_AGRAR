"""Story 4.1 — AC9 email subject lokalizovan po `lead.locale` (TEA RED phase).

Pokriva AC9: subject + telo renderovani po lead.locale (translation.override);
sr render → pune dijakritike (č/ć/ž/š/đ), NEMA ćirilice, NEMA šišane latinice;
hu/en kroz gettext (fallback sr ako prevod fali — prihvatljivo).

TEA RED phase: SVI testovi MORAJU pasti — apps.forms.notifications ne postoji.

Refs:
- 4-1-lead-model-smtp-setup.md AC9 + Task 8.6 + SM-D9
- 4-1-interface-contract.md § 4 (SUBJECT lokalizovan)
"""

from __future__ import annotations

import re

import pytest

pytestmark = pytest.mark.django_db

# Ćirilica (Unicode opseg) — sr render NE sme sadržati ćirilicu
_CYRILLIC = re.compile(r"[Ѐ-ӿ]")
# Šišana latinica markeri (ASCII zamene za dijakritike u kontekstu reči — heuristika)
# Proveravamo da sr subject SADRŽI bar jedan pravi dijakritik (č/ć/ž/š/đ).
_DIACRITICS = set("čćžšđČĆŽŠĐ")


# Sve 4 _build_subject grane × 3 lokale — subject lokalizacija mora raditi za SVAKI
# form_type (NE samo KONTAKT). Ne asertujemo hu/en prevedeni tekst (sr fallback je OK).
@pytest.mark.parametrize(
    "form_type",
    [
        "contact",
        "model_inquiry",
        "service_request",
        "part_request",
    ],
)
@pytest.mark.parametrize("locale", ["sr", "hu", "en"])
def test_subject_localized_per_lead_locale(form_type, locale, recipient_env, mailoutbox):
    from apps.forms.models import Lead
    from apps.forms.notifications import send_lead_email

    lead = Lead.objects.create(
        form_type=form_type,
        name="Marko Marković",
        email="marko@example.com",
        locale=locale,
    )
    send_lead_email(lead)

    assert len(mailoutbox) == 1, f"form_type={form_type} locale={locale}: MORA biti 1 email."
    subject = mailoutbox[0].subject
    assert subject, f"form_type={form_type} locale={locale}: subject NE SME biti prazan."
    # Brend marker pun-dijakritik prisutan u svim lokalama (fallback sr ako hu/en prevod fali)
    assert "[Ćorić Agrar]" in subject, (
        f"form_type={form_type} locale={locale}: subject MORA sadržati '[Ćorić Agrar]' "
        f"(pune dijakritike; fallback sr ako prevod fali), dobio {subject!r}."
    )


def test_sr_subject_has_diacritics_and_no_cyrillic(recipient_env, mailoutbox):
    from apps.forms.models import Lead
    from apps.forms.notifications import send_lead_email

    lead = Lead.objects.create(
        form_type=Lead.FormType.KONTAKT,
        name="Đorđe Đorđević",
        email="djordje@example.com",
        locale="sr",
    )
    send_lead_email(lead)

    subject = mailoutbox[0].subject
    assert _DIACRITICS & set(subject), (
        "sr subject MORA imati pune dijakritike (c/c/z/s/dj — npr. Coric Agrar). "
        f"Dobio: {subject!r}."
    )
    assert not _CYRILLIC.search(subject), (
        f"sr subject NE SME sadržati ćirilicu, dobio {subject!r}."
    )
