"""Story 4.4 — AC1: `LeadAttachment` child model surface — TEA RED phase.

Pokriva AC1 / Task 1.2:
- `lead` FK (on_delete=CASCADE, related_name="attachments");
- `file` FileField (NIJE ImageField — validacija je u formi);
- brisanje Lead-a kaskadno briše LeadAttachment;
- `__str__` informativan (sadrži „Prilog" + file name);
- Meta.verbose_name/_plural pun dijakritik („Prilog"/„Prilozi");
- NEMA `created_at` polja (SM-D3 — NE nasleđuje TimestampedModel; sprečava da Dev tiho doda timestamp).

RED razlog: `apps.forms.models.LeadAttachment` ne postoji → ImportError → SVE padaju.

Pokrenuti:
    just test apps/forms/tests/test_lead_attachment_model.py -v

Refs: 4-4 AC1 + Task 1.2 + SM-D1/SM-D3; interface-contract § 1.
"""

from __future__ import annotations

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import models

pytestmark = pytest.mark.django_db


def _make_lead():
    from apps.forms.models import Lead

    return Lead.objects.create(
        form_type=Lead.FormType.SERVICE_REQUEST,
        name="Stojan Stojanović",
        email="stojan@example.com",
        phone="+381641234567",
        message="Curi ulje iz hidraulike.",
        data={"machine_type": "tractor", "brand_model": "Agri Tracking TB804"},
    )


def _make_attachment(lead):
    from apps.forms.models import LeadAttachment

    upload = SimpleUploadedFile("kvar.jpg", b"fake-jpeg-bytes", content_type="image/jpeg")
    return LeadAttachment.objects.create(lead=lead, file=upload)


# AC-1: `lead` je FK na Lead sa on_delete=CASCADE
def test_lead_fk_on_delete_cascade():
    from apps.forms.models import LeadAttachment

    field = LeadAttachment._meta.get_field("lead")
    assert isinstance(field, models.ForeignKey), (
        f"`lead` MORA biti ForeignKey, dobio {type(field).__name__}."
    )
    assert field.remote_field.on_delete is models.CASCADE, (
        "LeadAttachment.lead FK MORA biti on_delete=CASCADE (brisanje Lead-a briše "
        "attachment-e — SM-D3/AC1)."
    )


# AC-1: FK ima related_name="attachments" (view + notifications koriste lead.attachments)
def test_lead_fk_related_name_is_attachments():
    from apps.forms.models import Lead, LeadAttachment

    field = LeadAttachment._meta.get_field("lead")
    assert field.remote_field.related_name == "attachments", (
        f"LeadAttachment.lead FK MORA imati related_name='attachments' (SM-D3 — "
        f"`lead.attachments.all()` u view-u/notifications), dobio "
        f"{field.remote_field.related_name!r}."
    )
    # reverse accessor mora realno postojati na Lead-u
    assert hasattr(Lead, "attachments"), (
        "Lead MORA imati reverse accessor `attachments` (related_name)."
    )


# AC-1: `file` je FileField (NIJE ImageField — validacija je u formi kroz validate_image_mime)
def test_file_is_filefield_not_imagefield():
    from apps.forms.models import LeadAttachment

    field = LeadAttachment._meta.get_field("file")
    assert isinstance(field, models.FileField), (
        f"`file` MORA biti FileField, dobio {type(field).__name__}."
    )
    assert not isinstance(field, models.ImageField), (
        "`file` NE SME biti ImageField (SM-D3 — validacija je u formi kroz "
        "validate_image_mime; ImageField bi duplirao slabiju MIME proveru)."
    )


# AC-1: brisanje Lead-a kaskadno briše LeadAttachment redove
def test_deleting_lead_cascades_attachments():
    from apps.forms.models import LeadAttachment

    lead = _make_lead()
    _make_attachment(lead)
    _make_attachment(lead)
    assert LeadAttachment.objects.count() == 2

    lead.delete()
    assert LeadAttachment.objects.count() == 0, (
        "Brisanje Lead-a MORA kaskadno obrisati sve LeadAttachment redove (CASCADE — AC1)."
    )


# AC-1: __str__ je informativan — sadrži „Prilog" + file name
def test_str_is_informative():
    lead = _make_lead()
    attachment = _make_attachment(lead)
    text = str(attachment)
    assert "Prilog" in text, (
        f"LeadAttachment.__str__ MORA sadržati 'Prilog' (informativan prikaz), dobio {text!r}."
    )
    assert "kvar" in text, (
        f"LeadAttachment.__str__ MORA sadržati ime fajla, dobio {text!r}."
    )


# AC-1: Meta.verbose_name/_plural pun dijakritik („Prilog"/„Prilozi")
def test_meta_verbose_name_diacritics():
    from apps.forms.models import LeadAttachment

    assert str(LeadAttachment._meta.verbose_name) == "Prilog", (
        f"Meta.verbose_name MORA biti 'Prilog', dobio {LeadAttachment._meta.verbose_name!r}."
    )
    assert str(LeadAttachment._meta.verbose_name_plural) == "Prilozi", (
        f"Meta.verbose_name_plural MORA biti 'Prilozi', dobio "
        f"{LeadAttachment._meta.verbose_name_plural!r}."
    )


# AC-1: NEMA `created_at` polja (SM-D3 — NE nasleđuje TimestampedModel)
def test_no_created_at_field():
    from apps.forms.models import LeadAttachment

    field_names = {f.name for f in LeadAttachment._meta.get_fields()}
    assert "created_at" not in field_names, (
        "LeadAttachment NE SME imati `created_at` polje (SM-D3 — NE nasleđuje "
        "TimestampedModel; lead.created_at je dovoljan; YAGNI). Sprečava tihi timestamp "
        f"dodatak. Polja: {sorted(field_names)!r}."
    )
    assert "updated_at" not in field_names, (
        "LeadAttachment NE SME imati `updated_at` polje (NE nasleđuje TimestampedModel — SM-D3)."
    )


# AC-1: `file` upload_to particioniše per godina/mesec (media dir ne eksplodira)
def test_file_upload_to_partitioned_by_year_month():
    from apps.forms.models import LeadAttachment

    field = LeadAttachment._meta.get_field("file")
    upload_to = field.upload_to
    # upload_to je string template "leads/attachments/%Y/%m/" (SM-D3)
    assert "leads/attachments" in str(upload_to), (
        f"`file` upload_to MORA biti pod 'leads/attachments/...' (SM-D3), dobio {upload_to!r}."
    )
    assert "%Y" in str(upload_to) and "%m" in str(upload_to), (
        f"`file` upload_to MORA particionisati per godina/mesec (%Y/%m — SM-D3), dobio {upload_to!r}."
    )
