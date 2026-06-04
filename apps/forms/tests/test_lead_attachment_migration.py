"""Story 4.4 — AC1: migracija `0002` (CreateModel LeadAttachment) — TEA RED phase.

Pokriva AC1 / Task 1.3:
- migracija `0002` postoji i sadrži SAMO CreateModel("LeadAttachment") (FK na Lead);
- NEMA AlterField/AddField na Lead (NEMA `photo` kolone na Lead-u — multi-file je child model);
- posle migracije `makemigrations --check --dry-run` NE traži NOVE migracije (model+migracija sinhronizovani).

RED razlog: migracija 0002 + LeadAttachment model ne postoje → migration introspekcija ne nalazi
CreateModel; makemigrations --check bi tražio nove migracije (model nedostaje).

Pokrenuti:
    just test apps/forms/tests/test_lead_attachment_migration.py -v

Refs: 4-4 AC1 + Task 1.3 + SM-D1; interface-contract § 1.
"""

from __future__ import annotations

from io import StringIO

import pytest
from django.core.management import call_command
from django.db.migrations.loader import MigrationLoader

pytestmark = pytest.mark.django_db


def _forms_0002():
    loader = MigrationLoader(connection=None, ignore_no_migrations=True)
    matches = [k for k in loader.disk_migrations if k[0] == "forms" and k[1].startswith("0002")]
    assert matches, (
        "Migracija forms/0002_*.py MORA postojati (CreateModel LeadAttachment — SM-D1/AC1). "
        f"Pronađene forms migracije: {sorted(k[1] for k in loader.disk_migrations if k[0] == 'forms')!r}."
    )
    return loader.disk_migrations[matches[0]]


# AC-1: migracija 0002 postoji i sadrži CreateModel("LeadAttachment")
def test_migration_0002_creates_lead_attachment():
    from django.db import migrations

    migration = _forms_0002()
    create_ops = [
        op for op in migration.operations
        if isinstance(op, migrations.CreateModel) and op.name == "LeadAttachment"
    ]
    assert create_ops, (
        "forms/0002 MORA imati CreateModel('LeadAttachment') (SM-D1). Operacije: "
        f"{[type(op).__name__ for op in migration.operations]!r}."
    )


# AC-1: migracija 0002 NE menja Lead (NEMA AlterField/AddField na Lead — samo NOVI model)
def test_migration_0002_does_not_alter_lead():
    from django.db import migrations

    migration = _forms_0002()
    lead_mutations = [
        op for op in migration.operations
        if isinstance(op, (migrations.AlterField, migrations.AddField))
        and getattr(op, "model_name", "").lower() == "lead"
    ]
    assert lead_mutations == [], (
        "forms/0002 NE SME imati AlterField/AddField na Lead (SM-D1 — NEMA `photo` kolone, "
        f"NEMA FormType izmene; samo NOVI LeadAttachment model). Pronađeno: "
        f"{[type(op).__name__ for op in lead_mutations]!r}."
    )


# AC-1: posle 0002, makemigrations --check NE traži NOVE migracije (model+migracija sinhronizovani)
def test_no_pending_migrations_after_0002():
    out = StringIO()
    try:
        call_command(
            "makemigrations", "forms", "--check", "--dry-run", stdout=out, stderr=out
        )
    except SystemExit as exc:
        pytest.fail(
            "makemigrations forms --check --dry-run prijavljuje NEPRIMENJENE promene "
            "(model i migracija 0002 NISU sinhronizovani — Dev mora regenerisati 0002). "
            f"Exit: {exc.code}. Output: {out.getvalue()!r}"
        )


# AC-1: LeadAttachment tabela je realno aplicirana (round-trip insert iz DB)
def test_lead_attachment_row_round_trips_from_db():
    from django.core.files.uploadedfile import SimpleUploadedFile

    from apps.forms.models import Lead, LeadAttachment

    lead = Lead.objects.create(
        form_type=Lead.FormType.SERVICE_REQUEST,
        name="Stojan Stojanović",
        email="stojan@example.com",
    )
    attachment = LeadAttachment.objects.create(
        lead=lead,
        file=SimpleUploadedFile("kvar.jpg", b"bytes", content_type="image/jpeg"),
    )
    refetched = LeadAttachment.objects.get(pk=attachment.pk)
    assert refetched.lead_id == lead.pk, (
        "LeadAttachment round-trip MORA očuvati FK na Lead (migracija 0002 aplicirana — AC1)."
    )
