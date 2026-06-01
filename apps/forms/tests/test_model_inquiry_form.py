"""Story 4.3 — AC1: `ModelInquiryForm` (server-side validation SOT + trusted slug) — TEA RED.

Pokriva AC1 / Task 1.2:
- polja postoje (`name`/`email`/`phone`/`message`/`product_slug`);
- `name`/`email`/`message`/`product_slug` obavezni; `phone` opciono;
- `product_slug` je HiddenInput SlugField sa `max_length == 140` (LOCK — sprečava regresiju
  na Django default 50 koji bi odbio legitiman dug slug PRE view DB lookupa);
- model display NIJE form field koji nosi podatak (samo `product_slug` hidden je izvor);
- nevalidan email → invalid; validan payload → valid; labele/errori kroz gettext (pune
  dijakritike, NEMA ćirilice).

RED razlog: `apps.forms.forms.ModelInquiryForm` ne postoji → ImportError → SVE padaju.

Pokrenuti:
    just test apps/forms/tests/test_model_inquiry_form.py -v

Refs: 4-3 AC1 + Task 1.2 + SM-D2/SM-D11; interface-contract § 1.
"""

from __future__ import annotations

import re

import pytest
from django import forms as dj_forms

_CYRILLIC = re.compile(r"[Ѐ-ӿ]")


def _make_form(**overrides):
    from apps.forms.forms import ModelInquiryForm

    data = {
        "name": "Marko Marković",
        "email": "marko@example.com",
        "phone": "+381641234567",
        "message": "Zanima me ovaj model.",
        "product_slug": "agri-tracking-tb804",
    }
    data.update(overrides)
    return ModelInquiryForm(data)


# AC-1: forma deklariše TAČNO očekivana polja (name/email/phone/message/product_slug)
def test_form_has_expected_fields():
    from apps.forms.forms import ModelInquiryForm

    fields = set(ModelInquiryForm().fields)
    assert fields == {"name", "email", "phone", "message", "product_slug"}, (
        f"ModelInquiryForm MORA imati TAČNO polja name/email/phone/message/product_slug "
        f"(SM-D11 — model display NIJE data field), dobio {fields!r}."
    )


# AC-1: validan kompletan payload → is_valid() True
def test_complete_payload_is_valid():
    form = _make_form()
    assert form.is_valid(), (
        f"Kompletan validan payload MORA biti valid, errors={form.errors!r}."
    )


# AC-1: prazno name/email/message/product_slug → invalid sa per-field greškom
@pytest.mark.parametrize("missing_field", ["name", "email", "message", "product_slug"])
def test_required_fields_missing_invalid(missing_field):
    form = _make_form(**{missing_field: ""})
    assert not form.is_valid(), f"Prazno `{missing_field}` MORA učiniti formu nevalidnom (AC1)."
    assert missing_field in form.errors, (
        f"Greška za `{missing_field}` MORA biti per-field, dobio {form.errors!r}."
    )


# AC-1: phone je opciono (odsustvo telefona NE čini formu nevalidnom)
def test_phone_is_optional():
    form = _make_form(phone="")
    assert form.is_valid(), (
        f"`phone` MORA biti opciono (required=False — mirror ContactForm), errors={form.errors!r}."
    )


# AC-1: nevalidan email → invalid
def test_invalid_email_rejected():
    form = _make_form(email="nije-email")
    assert not form.is_valid(), "Nevalidan email MORA učiniti formu nevalidnom (AC1)."
    assert "email" in form.errors, f"Greška MORA biti na `email`, dobio {form.errors!r}."


# AC-1: product_slug je HiddenInput (NIJE vidljivo editabilno korisničko polje)
def test_product_slug_is_hidden_input():
    from apps.forms.forms import ModelInquiryForm

    widget = ModelInquiryForm().fields["product_slug"].widget
    assert isinstance(widget, dj_forms.HiddenInput), (
        f"`product_slug` MORA koristiti forms.HiddenInput (trusted hidden source, SM-D2), "
        f"dobio {type(widget).__name__}."
    )


# AC-1: product_slug max_length == 140 (LOCK — poklapa SluggedModel.slug; default 50 bi
# odbio legitiman dug slug PRE view DB lookupa → zbunjujuća lažna greška)
def test_product_slug_max_length_is_140():
    from apps.forms.forms import ModelInquiryForm

    max_len = ModelInquiryForm().fields["product_slug"].max_length
    assert max_len == 140, (
        f"`product_slug` max_length MORA biti 140 (poklapa SluggedModel.slug — AC1/Task 6.1), "
        f"dobio {max_len!r} (Django SlugField default je 50 — REGRESIJA!)."
    )


# AC-1: legitiman dug slug (>50 chars) NE sme biti odbijen na nivou forme (zbog max_length=140)
def test_long_slug_not_rejected_by_form_max_length():
    long_slug = "a" * 120  # >50 (default) ali <=140
    form = _make_form(product_slug=long_slug)
    assert form.is_valid(), (
        f"Legitiman dug slug ({len(long_slug)} chars, <=140) NE sme biti odbijen na nivou "
        f"forme (max_length=140), errors={form.errors!r}."
    )


# AC-1: model display NIJE form field koji nosi podatak — NEMA editabilno `model`/`product_name`
# polje koje bi server čitao kao izvor istine (samo `product_slug` hidden je izvor — SM-D2)
def test_no_data_bearing_model_field():
    from apps.forms.forms import ModelInquiryForm

    fields = set(ModelInquiryForm().fields)
    assert "model" not in fields, (
        "Forma NE SME imati editabilno `model` polje koje server čita kao izvor — "
        "product identitet je SAMO `product_slug` (hidden, SM-D2 security)."
    )
    assert "product_name" not in fields, (
        "Forma NE SME imati `product_name` data field — display je iz {{ product.name }} "
        "template-a, NE form field (SM-D2)."
    )


# AC-1: labele su lokalizovane sa punim dijakritikama, NEMA ćirilice (gettext_lazy)
def test_labels_have_diacritics_no_cyrillic():
    from apps.forms.forms import ModelInquiryForm

    labels = "".join(str(f.label or "") for f in ModelInquiryForm().fields.values())
    # E-pošta sadrži pun dijakritik š
    assert "E-pošta" in labels, (
        f"Email label MORA biti „E-pošta” (pun dijakritik š, NE šišana latinica), labels={labels!r}."
    )
    assert not _CYRILLIC.search(labels), (
        f"Labele NE SMEJU sadržati ćirilicu (latinica only), labels={labels!r}."
    )


# AC-1: required error poruke prolaze kroz gettext (pun dijakritik, NEMA ćirilice)
def test_required_error_messages_localized():
    form = _make_form(name="", email="", message="")
    joined = " ".join(str(e) for errs in form.errors.values() for e in errs)
    assert not _CYRILLIC.search(joined), (
        f"Error poruke NE SMEJU sadržati ćirilicu, dobio {joined!r}."
    )
