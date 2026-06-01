"""Story 4.2/4.3 — `ContactForm` + `ModelInquiryForm` (server-side validation source-of-truth).

`forms.Form` (NE ModelForm) jer je forma ulazna kapija: `message` je `required=True`
NA FORMI iako je `Lead.message` `blank=True` na modelu (AC1 — model je samo storage,
forma je validacioni SOT). Sve labele/error poruke kroz `gettext_lazy` (pune dijakritike
č/ć/ž/š/đ). HTML5 widget atributi (`type=email`, `required`) su SAMO UX sloj.

`ModelInquiryForm` (4.3) dodaje hidden `product_slug` (trusted source za server-side
product lookup; `max_length=140` poklapa `SluggedModel.slug`). „Model" je readonly UX
display iz `{{ product.name }}` u template-u, NIJE form field koji nosi podatak (SM-D2).

Refs: 4-2 AC1 + Task 5; 4-3 AC1 + Task 6; interface-contract § 1.
"""

from __future__ import annotations

from django import forms
from django.utils.translation import gettext_lazy as _


class ContactForm(forms.Form):
    name = forms.CharField(
        label=_("Ime i prezime"),
        max_length=200,
        required=True,
        error_messages={"required": _("Unesite ime i prezime.")},
        widget=forms.TextInput(
            attrs={
                "id": "contact-name",
                "class": "coric-contact-form__input",
                "required": True,
                "aria-required": "true",
            }
        ),
    )
    email = forms.EmailField(
        label=_("E-pošta"),
        required=True,
        error_messages={
            "required": _("Unesite e-poštu."),
            "invalid": _("Unesite ispravnu e-poštu."),
        },
        widget=forms.EmailInput(
            attrs={
                "id": "contact-email",
                "class": "coric-contact-form__input",
                "required": True,
                "aria-required": "true",
            }
        ),
    )
    phone = forms.CharField(
        label=_("Telefon"),
        max_length=50,
        required=False,
        widget=forms.TextInput(
            attrs={
                "id": "contact-phone",
                "class": "coric-contact-form__input",
                "type": "tel",
            }
        ),
    )
    message = forms.CharField(
        label=_("Poruka"),
        required=True,
        error_messages={"required": _("Unesite poruku.")},
        widget=forms.Textarea(
            attrs={
                "id": "contact-message",
                "class": "coric-contact-form__textarea",
                "rows": 5,
                "required": True,
                "aria-required": "true",
            }
        ),
    )


class ModelInquiryForm(forms.Form):
    name = forms.CharField(
        label=_("Ime i prezime"),
        max_length=200,
        required=True,
        error_messages={"required": _("Unesite ime i prezime.")},
        widget=forms.TextInput(
            attrs={
                "id": "inquiry-name",
                "class": "coric-contact-form__input",
                "required": True,
                "aria-required": "true",
            }
        ),
    )
    email = forms.EmailField(
        label=_("E-pošta"),
        required=True,
        error_messages={
            "required": _("Unesite e-poštu."),
            "invalid": _("Unesite ispravnu e-poštu."),
        },
        widget=forms.EmailInput(
            attrs={
                "id": "inquiry-email",
                "class": "coric-contact-form__input",
                "required": True,
                "aria-required": "true",
            }
        ),
    )
    phone = forms.CharField(
        label=_("Telefon"),
        max_length=50,
        required=False,
        widget=forms.TextInput(
            attrs={
                "id": "inquiry-phone",
                "class": "coric-contact-form__input",
                "type": "tel",
            }
        ),
    )
    message = forms.CharField(
        label=_("Poruka"),
        required=True,
        error_messages={"required": _("Unesite poruku.")},
        widget=forms.Textarea(
            attrs={
                "id": "inquiry-message",
                "class": "coric-contact-form__textarea",
                "rows": 5,
                "required": True,
                "aria-required": "true",
            }
        ),
    )
    product_slug = forms.SlugField(
        max_length=140,
        required=True,
        widget=forms.HiddenInput,
    )
