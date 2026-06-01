"""Story 4.1 — AC2 schema migracija `0001_initial` (TEA RED phase).

Pokriva AC2: 0001_initial CreateModel Lead aplicirana (round-trip create+refetch iz
DB dokazuje schemu); composite index (form_type, created_at) postoji na Meta.indexes;
NEMA `_sr/_hu/_en` modeltranslation kolona; NEMA data seed (Lead startuje PRAZAN).

pytest-django primenjuje 0001_initial u test bazi automatski (@pytest.mark.django_db).

TEA RED phase: SVI testovi MORAJU pasti — apps.forms ne postoji.

Refs:
- 4-1-lead-model-smtp-setup.md AC2 + Task 8.3 + SM-D4
- 4-1-interface-contract.md § 3 (Migracija)
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.django_db


# AC2: 0001_initial aplicirana — Lead red se kreira i round-trip-uje iz DB
def test_lead_row_round_trip_from_db():
    from apps.forms.models import Lead

    lead = Lead.objects.create(
        form_type=Lead.FormType.SERVICE_REQUEST,
        name="Petar Petrović",
        email="petar@example.com",
        phone="+381 11 123 456",
        message="Traktor neće da upali.",
        data={"machine_type": "traktor"},
        locale="sr",
    )
    refetched = Lead.objects.get(pk=lead.pk)
    assert refetched.form_type == "service_request", (
        f"form_type DB round-trip MORA vratiti 'service_request', dobio {refetched.form_type!r} "
        "(potvrđuje da kolona max_length pokriva celu vrednost — C3)."
    )
    assert refetched.name == "Petar Petrović"
    assert refetched.data == {"machine_type": "traktor"}
    assert refetched.created_at is not None, "created_at MORA biti popunjen (auto_now_add)."


# AC2: composite index (form_type, created_at) postoji na Meta.indexes (Epic 8.3 count)
def test_composite_index_form_type_created_at_exists():
    from apps.forms.models import Lead

    matching = [
        idx for idx in Lead._meta.indexes
        if list(idx.fields) == ["form_type", "created_at"]
    ]
    assert matching, (
        f"Lead.Meta.indexes MORA sadržati composite index na (form_type, created_at) "
        f"(SM-D4 — Epic 8.3 segmentovan count). Pronađeni indeksi: "
        f"{[list(i.fields) for i in Lead._meta.indexes]}."
    )


# AC2: NEMA `_sr/_hu/_en` modeltranslation kolona (Lead nema translatable polja)
def test_no_modeltranslation_columns():
    from apps.forms.models import Lead

    field_names = {f.name for f in Lead._meta.get_fields()}
    suffixed = [n for n in field_names if n.endswith(("_sr", "_hu", "_en"))]
    assert suffixed == [], (
        f"Lead NE SME imati modeltranslation kolone (nema translatable polja). "
        f"Pronađeno: {suffixed}."
    )


# AC2: NEMA data seed — Lead startuje PRAZAN (count==0 na čistoj test bazi)
def test_no_data_seed_lead_starts_empty():
    from apps.forms.models import Lead

    assert Lead.objects.count() == 0, (
        f"Lead MORA startovati PRAZAN (NEMA data seed migracije — SM-D4). "
        f"Lead.objects.count() == {Lead.objects.count()} (za razliku od 3-4 SiteSettings seed-a)."
    )
