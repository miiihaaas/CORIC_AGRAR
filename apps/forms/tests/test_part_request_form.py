"""Story 4.5 — AC1: `PartRequestForm` (server-side validation SOT) — TEA RED phase.

Pokriva AC1 / Task 2.1:
- polja postoje (tractor_model/part_name/extra_description/photo/name/phone/email/
  payment_method/delivery_method/note);
- obavezni: tractor_model/part_name/name/phone/email/payment_method/delivery_method;
- opcioni: extra_description/photo/note;
- payment_method choices == {cod, proforma}; delivery_method choices == {delivery, pickup};
  nevalidan choice → invalid;
- EMAIL OBAVEZAN (prazan email → invalid — RAZLIKA od servisne forme; SM-D3);
- labele/dropdown opcije kroz gettext (pune dijakritike „E-pošta"/„Pouzeće"/„Lično"; NEMA ćirilice);
- validan payload (sa i bez slike) → valid.

RED razlog: `apps.forms.forms.PartRequestForm` ne postoji → ImportError → SVE padaju.

Pokrenuti:
    just test apps/forms/tests/test_part_request_form.py -v

Refs: 4-5 AC1 + Task 2.1 + SM-D3/SM-D4; interface-contract § 2.
"""

from __future__ import annotations

import re

import pytest
from django.utils.datastructures import MultiValueDict

_CYRILLIC = re.compile(r"[Ѐ-ӿ]")


def _base_data(**overrides) -> dict:
    data = {
        "tractor_model": "Agri Tracking TB804",
        "part_name": "Filter ulja",
        "extra_description": "Original deo.",
        "name": "Marko Marković",
        "phone": "+381641234567",
        "email": "marko@example.com",
        "payment_method": "cod",
        "delivery_method": "delivery",
        "note": "Pozovite popodne.",
    }
    data.update(overrides)
    return data


def _make_form(files=None, **overrides):
    from apps.forms.forms import PartRequestForm

    return PartRequestForm(_base_data(**overrides), files or {})


# AC-1: forma deklariše TAČNO očekivana polja
def test_form_has_expected_fields():
    from apps.forms.forms import PartRequestForm

    fields = set(PartRequestForm().fields)
    assert fields == {
        "tractor_model",
        "part_name",
        "extra_description",
        "photo",
        "name",
        "phone",
        "email",
        "payment_method",
        "delivery_method",
        "note",
    }, (
        f"PartRequestForm MORA imati TAČNO polja tractor_model/part_name/extra_description/"
        f"photo/name/phone/email/payment_method/delivery_method/note (AC1), dobio {fields!r}."
    )


# AC-1: validan kompletan payload (BEZ slike) → valid
def test_complete_payload_without_photo_is_valid():
    form = _make_form()
    assert form.is_valid(), f"Kompletan payload bez slike MORA biti valid, errors={form.errors!r}."


# AC-1: validan payload SA slikom → valid
def test_complete_payload_with_photo_is_valid(valid_image_jpeg):
    from apps.forms.forms import PartRequestForm

    files = MultiValueDict({"photo": [valid_image_jpeg]})
    form = PartRequestForm(_base_data(), files)
    assert form.is_valid(), f"Kompletan payload sa validnom slikom MORA biti valid, errors={form.errors!r}."


# AC-1: obavezna polja prazna → invalid sa per-field greškom
@pytest.mark.parametrize(
    "missing_field",
    ["tractor_model", "part_name", "name", "phone", "email", "payment_method", "delivery_method"],
)
def test_required_fields_missing_invalid(missing_field):
    form = _make_form(**{missing_field: ""})
    assert not form.is_valid(), f"Prazno `{missing_field}` MORA učiniti formu nevalidnom (AC1)."
    assert missing_field in form.errors, (
        f"Greška za `{missing_field}` MORA biti per-field, dobio {form.errors!r}."
    )


# AC-1 (SM-D3 — KRITIČNA RAZLIKA): email je OBAVEZAN (prazan → invalid; RAZLIKA od servisne forme)
def test_email_is_required():
    form = _make_form(email="")
    assert not form.is_valid(), (
        "`email` MORA biti OBAVEZAN na rezervni-delovi formi (Email * — SM-D3; RAZLIKA od "
        "ServiceRequestForm gde je email opciono)."
    )
    assert "email" in form.errors, f"Greška MORA biti per-field na `email`, dobio {form.errors!r}."


# AC-1: opciona polja prazna → valid (extra_description/note; photo pokriven u zaseban test fajl)
@pytest.mark.parametrize("optional_field", ["extra_description", "note"])
def test_optional_fields_blank_is_valid(optional_field):
    form = _make_form(**{optional_field: ""})
    assert form.is_valid(), (
        f"Prazno `{optional_field}` MORA biti opciono (required=False — AC1), errors={form.errors!r}."
    )


# AC-1: photo je opciono — forma bez fajla je validna
def test_photo_is_optional():
    form = _make_form(files={})
    assert form.is_valid(), (
        f"`photo` MORA biti opciono (max 1, opc. — AC1; forma bez fajla je validna), "
        f"errors={form.errors!r}."
    )


# AC-1: payment_method choices == {cod, proforma}
def test_payment_method_choices_locked():
    from apps.forms.forms import PartRequestForm

    values = {value for value, _label in PartRequestForm().fields["payment_method"].choices if value}
    assert values == {"cod", "proforma"}, (
        f"payment_method DB vrednosti MORAJU biti {{cod, proforma}} (AC1 LOCK), dobio {values!r}."
    )


# AC-1: delivery_method choices == {delivery, pickup}
def test_delivery_method_choices_locked():
    from apps.forms.forms import PartRequestForm

    values = {value for value, _label in PartRequestForm().fields["delivery_method"].choices if value}
    assert values == {"delivery", "pickup"}, (
        f"delivery_method DB vrednosti MORAJU biti {{delivery, pickup}} (AC1 LOCK), dobio {values!r}."
    )


# AC-1: nevalidan payment_method (van choices) → invalid
def test_invalid_payment_method_rejected():
    form = _make_form(payment_method="bitcoin")
    assert not form.is_valid(), "payment_method van choices MORA učiniti formu nevalidnom (AC1)."
    assert "payment_method" in form.errors, (
        f"Greška MORA biti per-field na `payment_method`, dobio {form.errors!r}."
    )


# AC-1: nevalidan delivery_method (van choices) → invalid
def test_invalid_delivery_method_rejected():
    form = _make_form(delivery_method="teleportacija")
    assert not form.is_valid(), "delivery_method van choices MORA učiniti formu nevalidnom (AC1)."
    assert "delivery_method" in form.errors, (
        f"Greška MORA biti per-field na `delivery_method`, dobio {form.errors!r}."
    )


# AC-1/AC-12: payment_method labele pune dijakritike („Pouzeće" sa ć), NEMA ćirilice
def test_payment_method_labels_diacritics_no_cyrillic():
    from django.utils.translation import activate

    from apps.forms.forms import PartRequestForm

    activate("sr")
    labels = " ".join(
        str(label) for _value, label in PartRequestForm().fields["payment_method"].choices
    )
    assert "Pouzeće" in labels, (
        f"payment_method MORA imati labelu 'Pouzeće' (pun dijakritik ć), labels={labels!r}."
    )
    assert "Predračun" in labels, (
        f"payment_method MORA imati labelu 'Predračun' (pun dijakritik č), labels={labels!r}."
    )
    assert not _CYRILLIC.search(labels), (
        f"payment_method labele NE SMEJU sadržati ćirilicu, labels={labels!r}."
    )


# AC-1/AC-12: delivery_method labele pune dijakritike („Lično" sa č), NEMA ćirilice
def test_delivery_method_labels_diacritics_no_cyrillic():
    from django.utils.translation import activate

    from apps.forms.forms import PartRequestForm

    activate("sr")
    labels = " ".join(
        str(label) for _value, label in PartRequestForm().fields["delivery_method"].choices
    )
    assert "Dostava" in labels, (
        f"delivery_method MORA imati labelu 'Dostava', labels={labels!r}."
    )
    assert "Lično preuzimanje" in labels, (
        f"delivery_method MORA imati labelu 'Lično preuzimanje' (pun dijakritik č), labels={labels!r}."
    )
    assert not _CYRILLIC.search(labels), (
        f"delivery_method labele NE SMEJU sadržati ćirilicu, labels={labels!r}."
    )


# AC-1/AC-12: field labele pune dijakritike („E-pošta" sa š), NEMA ćirilice
def test_field_labels_diacritics_no_cyrillic():
    from django.utils.translation import activate

    from apps.forms.forms import PartRequestForm

    activate("sr")
    labels = " ".join(str(f.label or "") for f in PartRequestForm().fields.values())
    assert "E-pošta" in labels, (
        f"Email label MORA biti 'E-pošta' (pun dijakritik š), labels={labels!r}."
    )
    assert not _CYRILLIC.search(labels), (
        f"Labele NE SMEJU sadržati ćirilicu (latinica only), labels={labels!r}."
    )


# AC-1: forma je konstruktabilna sa praznim files dict-om (None-safe; foto validacija u zaseban fajl)
def test_form_constructs_with_empty_files():
    from apps.forms.forms import PartRequestForm

    form = PartRequestForm(_base_data(), {})
    assert hasattr(form, "fields"), "PartRequestForm MORA biti konstruktabilna sa praznim files."
