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
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.media_pipeline.utils import validate_image_mime


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


# ── Story 4.4 (Servisni zahtev forma sa foto upload-om) ──────────────────────

# Kanonski Django 5.x multi-file idiom (SM-D4 — NE `MultipleHiddenInput`).
# Django stock `forms.FileField` NE podržava `multiple` bez custom widget/field-a.


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single = super().clean
        if isinstance(data, (list, tuple)):
            return [single(d, initial) for d in data]
        return [single(data, initial)] if data else []


class ServiceRequestForm(forms.Form):
    """Story 4.4 — servisni zahtev (server-side validation SOT) + foto double-check.

    `phone` je OBAVEZAN (SM-D9 — RAZLIKA od ContactForm); `email`/`brand_model`/`photos`
    opcioni. `description` je `required=True` NA FORMI iako je `Lead.message` `blank=True`
    na modelu (forma je validacioni SOT). `clean_photos` radi all-or-nothing foto
    double-check kroz `validate_image_mime` (REUSE 2.3).
    """

    class MachineType(models.TextChoices):
        TRACTOR = "tractor", _("Traktor")
        ATTACHMENT = "attachment", _("Priključna mehanizacija")
        WORK_MACHINE = "work_machine", _("Radna mašina")
        OTHER = "other", _("Ostalo")

    name = forms.CharField(
        label=_("Ime i prezime"),
        max_length=200,
        required=True,
        error_messages={"required": _("Unesite ime i prezime.")},
        widget=forms.TextInput(
            attrs={
                "id": "service-name",
                "class": "coric-contact-form__input",
                "required": True,
                "aria-required": "true",
            }
        ),
    )
    phone = forms.CharField(
        label=_("Telefon"),
        max_length=50,
        required=True,
        error_messages={"required": _("Unesite broj telefona.")},
        widget=forms.TextInput(
            attrs={
                "id": "service-phone",
                "class": "coric-contact-form__input",
                "type": "tel",
                "required": True,
                "aria-required": "true",
            }
        ),
    )
    email = forms.EmailField(
        label=_("E-pošta"),
        required=False,
        error_messages={"invalid": _("Unesite ispravnu e-poštu.")},
        widget=forms.EmailInput(
            attrs={
                "id": "service-email",
                "class": "coric-contact-form__input",
            }
        ),
    )
    machine_type = forms.ChoiceField(
        label=_("Vrsta mehanizacije"),
        choices=MachineType.choices,
        required=True,
        error_messages={"required": _("Izaberite vrstu mehanizacije.")},
        widget=forms.Select(
            attrs={
                "id": "service-machine-type",
                "class": "coric-contact-form__input",
                "required": True,
                "aria-required": "true",
            }
        ),
    )
    brand_model = forms.CharField(
        label=_("Brend i model"),
        max_length=200,
        required=False,
        widget=forms.TextInput(
            attrs={
                "id": "service-brand-model",
                "class": "coric-contact-form__input",
            }
        ),
    )
    description = forms.CharField(
        label=_("Opis kvara"),
        required=True,
        error_messages={"required": _("Opišite kvar.")},
        widget=forms.Textarea(
            attrs={
                "id": "service-description",
                "class": "coric-contact-form__textarea",
                "rows": 5,
                "required": True,
                "aria-required": "true",
            }
        ),
    )
    photos = MultipleFileField(
        label=_("Fotografije"),
        required=False,
        widget=MultipleFileInput(
            attrs={
                "id": "service-photos",
                "class": "coric-contact-form__input",
                "multiple": True,
                "accept": "image/jpeg,image/png",
            }
        ),
    )

    def clean_photos(self):
        """All-or-nothing foto double-check (AC3 — KRITIČNO; NIKAD partial-accept).

        Iterira fajlove; broji (> 3 → ValidationError); per fajl poziva
        `validate_image_mime` (MIME signature + Pillow verify + size). Na PRVOM
        nevalidnom fajlu PROPAGIRA ValidationError (cela forma invalid). Na uspehu
        vraća punu validiranu listu.
        """
        max_size_bytes = 5 * 1024 * 1024
        files = self.cleaned_data.get("photos") or []
        if len(files) > 3:
            raise ValidationError(_("Možete priložiti najviše 3 slike."))

        for f in files:
            # Size granu proveravamo STRUKTURNO (NE substring na util poruci) da clean
            # epics string („5 MB") bude deterministički vezan za uzrok — locale/util-message
            # promena ne može tiho da ukloni konkretnu poruku. I dalje RAISE pre util-a
            # (all-or-nothing — prvi nevalidan fajl ruši celu formu).
            if getattr(f, "size", 0) and f.size > max_size_bytes:
                raise ValidationError(_("Slika je veća od 5 MB. Probajte manju."))
            # MIME signature + Pillow verify (+ rezerva za size) preko util-a (REUSE 2.3);
            # pinovan allowed_mimes/max_size_bytes je behavior-assertovan (spy test).
            validate_image_mime(
                f,
                allowed_mimes=("image/jpeg", "image/png"),
                max_size_bytes=max_size_bytes,
            )

        return files


# ── Story 4.5 (Rezervni delovi forma sa single-file foto upload-om) ──────────


class PartRequestForm(forms.Form):
    """Story 4.5 — rezervni delovi (server-side validation SOT) + single-file foto double-check.

    REUSE 1:1 4.4 mašinerije, RAZLIKE (SM-D3/SM-D4):
    - `email` je OBAVEZAN (Email * — SM-D3; RAZLIKA od ServiceRequestForm gde je opciono);
    - `photo` je stock `forms.FileField` (single-file — OQ-1/SM-D4), NE `MultipleFileField`
      i NE `ImageField` (ImageField poziva Pillow u `to_python()` → duplira + može poremetiti
      `seek()` poziciju koju `validate_image_mime` interno koristi). `validate_image_mime` u
      `clean_photo` je JEDINI autoritativni gate.

    Dva `ChoiceField`-a (`payment_method`/`delivery_method`) sa nested `TextChoices`. „Model
    traktora"/„Rezervni deo" su free text (NE FK/slug — SM-D7). Sve labele/error kroz
    `gettext_lazy` (pune dijakritike). Widget `id` konvencija `part-<field>`.
    """

    class PaymentMethod(models.TextChoices):
        COD = "cod", _("Pouzeće")
        PROFORMA = "proforma", _("Predračun")

    class DeliveryMethod(models.TextChoices):
        DELIVERY = "delivery", _("Dostava")
        PICKUP = "pickup", _("Lično preuzimanje")

    tractor_model = forms.CharField(
        label=_("Model traktora"),
        max_length=200,
        required=True,
        error_messages={"required": _("Unesite model traktora.")},
        widget=forms.TextInput(
            attrs={
                "id": "part-tractor-model",
                "class": "coric-contact-form__input",
                "required": True,
                "aria-required": "true",
            }
        ),
    )
    part_name = forms.CharField(
        label=_("Rezervni deo"),
        max_length=200,
        required=True,
        error_messages={"required": _("Unesite naziv rezervnog dela.")},
        widget=forms.TextInput(
            attrs={
                "id": "part-name",
                "class": "coric-contact-form__input",
                "required": True,
                "aria-required": "true",
            }
        ),
    )
    extra_description = forms.CharField(
        label=_("Dodatni opis (opc.)"),
        required=False,
        widget=forms.Textarea(
            attrs={
                "id": "part-extra-description",
                "class": "coric-contact-form__textarea",
                "rows": 4,
            }
        ),
    )
    photo = forms.FileField(
        label=_("Slika (opc., max 1)"),
        required=False,
        widget=forms.FileInput(
            attrs={
                "id": "part-photo",
                "class": "coric-contact-form__input coric-service-form__file",
                "accept": "image/jpeg,image/png",
            }
        ),
    )
    name = forms.CharField(
        label=_("Ime i prezime"),
        max_length=200,
        required=True,
        error_messages={"required": _("Unesite ime i prezime.")},
        widget=forms.TextInput(
            attrs={
                "id": "part-name-full",
                "class": "coric-contact-form__input",
                "required": True,
                "aria-required": "true",
            }
        ),
    )
    phone = forms.CharField(
        label=_("Telefon"),
        max_length=50,
        required=True,
        error_messages={"required": _("Unesite broj telefona.")},
        widget=forms.TextInput(
            attrs={
                "id": "part-phone",
                "class": "coric-contact-form__input",
                "type": "tel",
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
                "id": "part-email",
                "class": "coric-contact-form__input",
                "required": True,
                "aria-required": "true",
            }
        ),
    )
    payment_method = forms.ChoiceField(
        label=_("Način plaćanja"),
        choices=PaymentMethod.choices,
        required=True,
        error_messages={"required": _("Izaberite način plaćanja.")},
        widget=forms.Select(
            attrs={
                "id": "part-payment-method",
                "class": "coric-contact-form__input",
                "required": True,
                "aria-required": "true",
            }
        ),
    )
    delivery_method = forms.ChoiceField(
        label=_("Način preuzimanja"),
        choices=DeliveryMethod.choices,
        required=True,
        error_messages={"required": _("Izaberite način preuzimanja.")},
        widget=forms.Select(
            attrs={
                "id": "part-delivery-method",
                "class": "coric-contact-form__input",
                "required": True,
                "aria-required": "true",
            }
        ),
    )
    note = forms.CharField(
        label=_("Napomena (opc.)"),
        required=False,
        widget=forms.Textarea(
            attrs={
                "id": "part-note",
                "class": "coric-contact-form__textarea",
                "rows": 4,
            }
        ),
    )

    def clean_photo(self):
        """Single-file foto double-check (AC2 — KRITIČNO; REUSE 2.3 util).

        Prazno → vrati bez double-check-a (NE poziva util). Inače strukturna size
        pre-provera (clean „5 MB" string deterministički vezan za uzrok) PRE util-a,
        pa `validate_image_mime` (MIME signature + Pillow verify + size) sa pinovanim
        allowed_mimes/max_size_bytes (EXCLUSION webp; NE default 10 MB).
        """
        photo = self.cleaned_data.get("photo")
        if not photo:
            return photo
        if getattr(photo, "size", 0) > 5 * 1024 * 1024:
            raise ValidationError(_("Slika je veća od 5 MB. Probajte manju."))
        validate_image_mime(
            photo,
            allowed_mimes=("image/jpeg", "image/png"),
            max_size_bytes=5 * 1024 * 1024,
        )
        return photo
