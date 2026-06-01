"""Story 4.1 — AC1 `Lead` model surface (TEA RED phase).

Pokriva AC1: Lead u apps/forms/models.py; nasleđuje TimestampedModel; TAČNA polja
+ tipovi; form_type 4 DB vrednosti LOWERCASE (cross-story query ugovor); name
blank=False; data default=dict (mutable-safe); locale default „sr"; created_at/
updated_at nasleđeni; NEMA `photo` atributa (attachment-i = 4-4 LeadAttachment);
`__str__`; NEMA FK; NEMA get_absolute_url; verbose_name.

TEA RED phase: SVI testovi MORAJU pasti — apps.forms ne postoji
(ModuleNotFoundError: No module named 'apps.forms').

Refs:
- 4-1-lead-model-smtp-setup.md AC1 + Task 8.2 + SM-D3/D3a/D10/D13/D14
- 4-1-interface-contract.md § 2 (Model surface)
"""

from __future__ import annotations

import pytest
from django.db import models

pytestmark = pytest.mark.django_db


# AC1: form_type DB vrednosti su TAČNO lowercase stringovi (cross-story query ugovor C3)
def test_form_type_db_values_are_lowercase():
    from apps.forms.models import Lead

    assert Lead.FormType.KONTAKT == "contact", (
        f"FormType.KONTAKT DB vrednost MORA biti 'contact', dobio {Lead.FormType.KONTAKT!r}. "
        "DB vrednosti su LOCKED za 4-2…4-5 + Epic 8.3 query (epics.md:791)."
    )
    assert Lead.FormType.MODEL_INQUIRY == "model_inquiry", (
        f"FormType.MODEL_INQUIRY DB vrednost MORA biti 'model_inquiry', "
        f"dobio {Lead.FormType.MODEL_INQUIRY!r} (epics.md:802)."
    )
    assert Lead.FormType.SERVICE_REQUEST == "service_request", (
        f"FormType.SERVICE_REQUEST DB vrednost MORA biti 'service_request', "
        f"dobio {Lead.FormType.SERVICE_REQUEST!r}."
    )
    assert Lead.FormType.PART_REQUEST == "part_request", (
        f"FormType.PART_REQUEST DB vrednost MORA biti 'part_request', "
        f"dobio {Lead.FormType.PART_REQUEST!r}."
    )


# AC1: form_type ima TAČNO 4 choices
def test_form_type_has_four_choices():
    from apps.forms.models import Lead

    values = {value for value, _label in Lead.FormType.choices}
    assert values == {"contact", "model_inquiry", "service_request", "part_request"}, (
        f"FormType MORA imati TAČNO 4 choices (contact/model_inquiry/service_request/"
        f"part_request), dobio {values}."
    )


# AC1: form_type je CharField sa choices, max_length >= 15 (pokriva „service_request")
def test_form_type_field_charfield_maxlen_covers_longest_value():
    from apps.forms.models import Lead

    field = Lead._meta.get_field("form_type")
    assert isinstance(field, models.CharField), (
        f"form_type MORA biti CharField, dobio {type(field).__name__}."
    )
    assert field.max_length >= 15, (
        f"form_type max_length MORA biti >= 15 (pokriva 'service_request' = 15 znakova), "
        f"dobio {field.max_length} (C3 — kraći max_length bi tiho odsekao DB vrednost)."
    )
    assert field.choices is not None, "form_type MORA imati choices (FormType.choices)."


# AC1: name CharField(200) blank=False (obavezno za sve form_type-ove)
def test_name_field_charfield_required():
    from apps.forms.models import Lead

    field = Lead._meta.get_field("name")
    assert isinstance(field, models.CharField), "name MORA biti CharField."
    assert field.max_length == 200, f"name max_length MORA biti 200, dobio {field.max_length}."
    assert field.blank is False, (
        "name MORA biti blank=False (obavezno za sve forme — epics.md:801/814/829 'Ime *')."
    )


# AC1: email je EmailField
def test_email_field_is_emailfield():
    from apps.forms.models import Lead

    field = Lead._meta.get_field("email")
    assert isinstance(field, models.EmailField), (
        f"email MORA biti EmailField, dobio {type(field).__name__}."
    )


# AC1: phone CharField blank=True (opciono)
def test_phone_field_optional():
    from apps.forms.models import Lead

    field = Lead._meta.get_field("phone")
    assert isinstance(field, models.CharField), "phone MORA biti CharField."
    assert field.blank is True, "phone MORA biti blank=True (opciono za neke forme)."


# AC1: message TextField blank=True (opciono)
def test_message_field_optional_textfield():
    from apps.forms.models import Lead

    field = Lead._meta.get_field("message")
    assert isinstance(field, models.TextField), "message MORA biti TextField."
    assert field.blank is True, "message MORA biti blank=True (npr. model_inquiry poruka opciona)."


# AC1: data JSONField default=dict (mutable-safe — NIKAD default={})
def test_data_field_jsonfield_default_dict_mutable_safe():
    from apps.forms.models import Lead

    field = Lead._meta.get_field("data")
    assert isinstance(field, models.JSONField), (
        f"data MORA biti JSONField, dobio {type(field).__name__}."
    )
    # default MORA biti `dict` callable (NE mutable {} literal) — dve instance ne dele isti dict.
    lead_a = Lead(form_type=Lead.FormType.KONTAKT, name="A", email="a@example.com")
    lead_b = Lead(form_type=Lead.FormType.KONTAKT, name="B", email="b@example.com")
    assert lead_a.data == {}, f"data default MORA biti prazan dict, dobio {lead_a.data!r}."
    lead_a.data["x"] = 1
    assert lead_b.data == {}, (
        "data default MORA biti `dict` callable (NE mutable {} literal) — mutacija jedne "
        f"instance NE sme curiti u drugu. lead_b.data == {lead_b.data!r}."
    )


# AC1: ip_address GenericIPAddressField null=True
def test_ip_address_field_nullable():
    from apps.forms.models import Lead

    field = Lead._meta.get_field("ip_address")
    assert isinstance(field, models.GenericIPAddressField), (
        f"ip_address MORA biti GenericIPAddressField, dobio {type(field).__name__}."
    )
    assert field.null is True, "ip_address MORA biti null=True."


# AC1: locale CharField(max_length=10) default „sr"
def test_locale_field_default_sr():
    from apps.forms.models import Lead

    field = Lead._meta.get_field("locale")
    assert isinstance(field, models.CharField), "locale MORA biti CharField."
    assert field.default == "sr", f"locale default MORA biti 'sr', dobio {field.default!r}."


# AC1: nasleđuje TimestampedModel (created_at + updated_at)
def test_inherits_timestamped_model_fields():
    from apps.core.models import TimestampedModel
    from apps.forms.models import Lead

    assert issubclass(Lead, TimestampedModel), (
        "Lead MORA nasleđivati apps.core.models.TimestampedModel (REUSE — SM-D10)."
    )
    # created_at/updated_at moraju postojati kao polja
    field_names = {f.name for f in Lead._meta.get_fields()}
    assert "created_at" in field_names, "Lead MORA imati nasleđeno created_at (TimestampedModel)."
    assert "updated_at" in field_names, "Lead MORA imati nasleđeno updated_at (TimestampedModel)."


# AC1: NEMA `photo` polja (attachment-i = 4-4 LeadAttachment child model — SM-D14)
def test_lead_has_no_photo_field():
    from django.core.exceptions import FieldDoesNotExist

    from apps.forms.models import Lead

    with pytest.raises(FieldDoesNotExist):
        Lead._meta.get_field("photo")
    field_names = {f.name for f in Lead._meta.get_fields()}
    assert "photo" not in field_names, (
        "Lead NE SME imati `photo`/attachment polje u 4-1 — attachment-i su 4-4 "
        "`LeadAttachment` child model (SM-D14). Single FileField ne može držati 3 fajla."
    )


# AC1: NEMA FK / relacija (product context kroz data JSON — SM-D3a) + NEMA get_absolute_url + __str__
def test_no_fk_no_get_absolute_url_and_str():
    from apps.forms.models import Lead

    # NEMA FORWARD FK / OneToOne / ManyToMany relacija deklarisanih na Lead-u.
    # Filtriramo SAMO forward/concrete relacije: future reverse accessor (npr. 4-4
    # `LeadAttachment` FK→Lead → reverse `attachments`) je `is_relation=True` ali
    # `concrete=False` i NE SME oboriti ovaj test (legitimna buduća reverse relacija).
    forward_relation_fields = [
        f for f in Lead._meta.get_fields()
        if f.is_relation and getattr(f, "concrete", False)
    ]
    assert forward_relation_fields == [], (
        f"Lead NE SME deklarisati forward FK/relacije (product context kroz data JSON — SM-D3a). "
        f"Pronađene forward relacije: {[f.name for f in forward_relation_fields]}."
    )
    assert not hasattr(Lead, "get_absolute_url"), (
        "Lead NE SME imati get_absolute_url (lead nije content sa javnom stranom — "
        "isti izuzetak kao 3-4 SiteSettings)."
    )
    lead = Lead.objects.create(
        form_type=Lead.FormType.KONTAKT, name="Marko Marković", email="marko@example.com"
    )
    assert "Marko Marković" in str(lead), (
        f"__str__ MORA biti informativan i sadržati ime, dobio {str(lead)!r}."
    )
    # __str__ MORA sadržati i čitljiv prikaz form_type-a (get_form_type_display), NE samo ime.
    assert lead.get_form_type_display() in str(lead), (
        f"__str__ MORA sadržati get_form_type_display() ({lead.get_form_type_display()!r}), "
        f"dobio {str(lead)!r}."
    )


# AC1: Meta.verbose_name + ordering
def test_meta_verbose_name_and_ordering():
    from apps.forms.models import Lead

    assert str(Lead._meta.verbose_name), "Lead MORA imati Meta.verbose_name."
    assert str(Lead._meta.verbose_name_plural), (
        "Lead MORA imati ne-prazan Meta.verbose_name_plural."
    )
    assert Lead._meta.ordering == ["-created_at"], (
        f"Meta.ordering MORA biti ['-created_at'], dobio {Lead._meta.ordering}."
    )
