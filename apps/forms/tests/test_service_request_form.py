"""Story 4.4 — AC2: `ServiceRequestForm` (server-side validation SOT) — TEA RED phase.

Pokriva AC2 / Task 2.1:
- polja postoje (name/phone/email/machine_type/brand_model/description/photos);
- obavezni: name/phone/machine_type/description; opcioni: email/brand_model/photos;
- machine_type choices == {tractor, attachment, work_machine, other}; nevalidan choice → invalid;
- description required=True NA FORMI iako Lead.message blank=True na modelu (forma je SOT);
- labele/error kroz gettext (pune dijakritike „Priključna"/„E-pošta"; NEMA ćirilice);
- validan payload (sa i bez slika) → valid.

RED razlog: `apps.forms.forms.ServiceRequestForm` ne postoji → ImportError → SVE padaju.

Pokrenuti:
    just test apps/forms/tests/test_service_request_form.py -v

Refs: 4-4 AC2 + Task 2.1 + SM-D9; interface-contract § 2.
"""

from __future__ import annotations

import re

import pytest

_CYRILLIC = re.compile(r"[Ѐ-ӿ]")


def _make_form(files=None, **overrides):
    from apps.forms.forms import ServiceRequestForm

    data = {
        "name": "Stojan Stojanović",
        "phone": "+381641234567",
        "email": "stojan@example.com",
        "machine_type": "tractor",
        "brand_model": "Agri Tracking TB804",
        "description": "Curi ulje iz hidraulike.",
    }
    data.update(overrides)
    return ServiceRequestForm(data, files or {})


# AC-2: forma deklariše TAČNO očekivana polja
def test_form_has_expected_fields():
    from apps.forms.forms import ServiceRequestForm

    fields = set(ServiceRequestForm().fields)
    assert fields == {
        "name",
        "phone",
        "email",
        "machine_type",
        "brand_model",
        "description",
        "photos",
    }, (
        f"ServiceRequestForm MORA imati TAČNO polja name/phone/email/machine_type/"
        f"brand_model/description/photos (AC2), dobio {fields!r}."
    )


# AC-2: validan kompletan payload (BEZ slika) → valid
def test_complete_payload_without_photos_is_valid():
    form = _make_form()
    assert form.is_valid(), f"Kompletan payload bez slika MORA biti valid, errors={form.errors!r}."


# AC-2: obavezna polja prazna → invalid sa per-field greškom
@pytest.mark.parametrize("missing_field", ["name", "phone", "machine_type", "description"])
def test_required_fields_missing_invalid(missing_field):
    form = _make_form(**{missing_field: ""})
    assert not form.is_valid(), f"Prazno `{missing_field}` MORA učiniti formu nevalidnom (AC2)."
    assert missing_field in form.errors, (
        f"Greška za `{missing_field}` MORA biti per-field, dobio {form.errors!r}."
    )


# AC-2: email je OPCIONO (RAZLIKA od obaveznog ContactForm email-a — epics.md:814)
def test_email_is_optional():
    form = _make_form(email="")
    assert form.is_valid(), (
        f"`email` MORA biti opciono (required=False — epics.md:814 bez zvezdice), errors={form.errors!r}."
    )


# AC-2: phone je OBAVEZAN (RAZLIKA od opcionog ContactForm phone-a — SM-D9)
def test_phone_is_required():
    form = _make_form(phone="")
    assert not form.is_valid(), (
        "`phone` MORA biti OBAVEZAN na servisnoj formi (Telefon * — SM-D9; RAZLIKA od ContactForm)."
    )
    assert "phone" in form.errors, f"Greška MORA biti per-field na `phone`, dobio {form.errors!r}."


# AC-2: brand_model je OPCIONO (free text, epics.md:814 bez zvezdice)
def test_brand_model_is_optional():
    form = _make_form(brand_model="")
    assert form.is_valid(), (
        f"`brand_model` MORA biti opciono (free text, epics.md:814), errors={form.errors!r}."
    )


# AC-2: machine_type choices == {tractor, attachment, work_machine, other}
def test_machine_type_choices_locked():
    from apps.forms.forms import ServiceRequestForm

    choice_values = {value for value, _label in ServiceRequestForm().fields["machine_type"].choices if value}
    assert choice_values == {"tractor", "attachment", "work_machine", "other"}, (
        f"machine_type DB vrednosti MORAJU biti {{tractor, attachment, work_machine, other}} "
        f"(AC2 LOCK), dobio {choice_values!r}."
    )


# AC-2: nevalidan machine_type (van choices) → invalid
def test_invalid_machine_type_rejected():
    form = _make_form(machine_type="kombajn-koji-ne-postoji")
    assert not form.is_valid(), "machine_type van choices MORA učiniti formu nevalidnom (AC2)."
    assert "machine_type" in form.errors, (
        f"Greška MORA biti per-field na `machine_type`, dobio {form.errors!r}."
    )


# AC-2: description je required NA FORMI (iako Lead.message blank=True na modelu)
def test_description_required_on_form():
    form = _make_form(description="")
    assert not form.is_valid(), (
        "Prazno `description` MORA biti nevalidno NA FORMI (AC2 — forma je SOT, model je "
        "storage; Lead.message blank=True se NE menja)."
    )
    assert "description" in form.errors, "Greška MORA biti per-field na `description`."


# AC-2/AC-12: machine_type labele pune dijakritike („Priključna" sa č/š), NEMA ćirilice
def test_machine_type_labels_diacritics_no_cyrillic():
    from django.utils.translation import activate

    from apps.forms.forms import ServiceRequestForm

    activate("sr")
    labels = " ".join(
        str(label) for _value, label in ServiceRequestForm().fields["machine_type"].choices
    )
    assert "Priključna mehanizacija" in labels, (
        f"machine_type MORA imati labelu 'Priključna mehanizacija' (pun dijakritik č), labels={labels!r}."
    )
    assert "Radna mašina" in labels, (
        f"machine_type MORA imati labelu 'Radna mašina' (pun dijakritik š), labels={labels!r}."
    )
    assert not _CYRILLIC.search(labels), (
        f"machine_type labele NE SMEJU sadržati ćirilicu, labels={labels!r}."
    )


# AC-2/AC-12: field labele pune dijakritike („E-pošta" sa š), NEMA ćirilice
def test_field_labels_diacritics_no_cyrillic():
    from django.utils.translation import activate

    from apps.forms.forms import ServiceRequestForm

    activate("sr")
    labels = " ".join(str(f.label or "") for f in ServiceRequestForm().fields.values())
    assert "E-pošta" in labels, (
        f"Email label MORA biti 'E-pošta' (pun dijakritik š), labels={labels!r}."
    )
    assert not _CYRILLIC.search(labels), (
        f"Labele NE SMEJU sadržati ćirilicu (latinica only), labels={labels!r}."
    )
