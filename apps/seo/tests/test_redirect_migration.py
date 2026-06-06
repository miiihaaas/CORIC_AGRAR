"""Story 6.4 — migracija `0002_redirect` introspekcija (TEA RED phase, AC1).

Pokriva AC1: `apps/seo/migrations/0002_redirect.py` postoji; `CreateModel("Redirect")`
sa kolonama old_path(CharField 255, unique, db_index)/new_path(CharField 255)/
is_active(BooleanField default True, db_index)/created_at/updated_at; `dependencies`
ima `("seo","0001_initial")`; NEMA _sr/_hu/_en kolone (Redirect nije translatable).
REGRESSION: `makemigrations --check` → no changes (model/migracija sync).

PREFERIRA introspekciju operations liste (mirror test_seometa_migration.py).

⚠️ GUARD: apps.seo migration import UNUTAR funkcija (collection-safety) — modul
0002_redirect JOŠ NE postoji → ModuleNotFoundError per-test (RED), NE collection-abort.

Refs:
- 6-4-redirect-manager-301.md AC1 + Task 2/6.6 + SM-D6
- 6-4-interface-contract.md § 4. Migration
"""

from __future__ import annotations

import pytest


def _get_create_redirect_operation():
    from importlib import import_module

    from django.db import migrations

    mod = import_module("apps.seo.migrations.0002_redirect")
    for op in mod.Migration.operations:
        if isinstance(op, migrations.CreateModel) and op.name == "Redirect":
            return op
    raise AssertionError("0002_redirect MORA imati CreateModel('Redirect') (AC1).")


# AC1: 0002_redirect.py modul postoji i nosi Migration klasu
def test_migration_module_exists():
    from importlib import import_module

    mod = import_module("apps.seo.migrations.0002_redirect")
    assert hasattr(mod, "Migration"), "0002_redirect MORA definisati Migration klasu (AC1)."


# AC1: CreateModel('Redirect') sa očekivanim kolonama
def test_createmodel_redirect_columns():
    op = _get_create_redirect_operation()
    field_names = {name for name, _ in op.fields}

    assert "old_path" in field_names, "0002 MORA imati old_path kolonu (AC1)."
    assert "new_path" in field_names, "0002 MORA imati new_path kolonu (AC1)."
    assert "is_active" in field_names, "0002 MORA imati is_active kolonu (AC1)."
    assert {"created_at", "updated_at"} <= field_names, (
        "0002 MORA imati created_at/updated_at (TimestampedModel — AC1)."
    )


# AC1/SM-D6: NEMA _sr/_hu/_en kolone (Redirect NIJE translatable)
def test_createmodel_has_no_translation_columns():
    op = _get_create_redirect_operation()
    field_names = {name for name, _ in op.fields}
    for base in ("old_path", "new_path"):
        for lang in ("sr", "hu", "en"):
            assert f"{base}_{lang}" not in field_names, (
                f"0002 NE SME imati {base}_{lang} kolonu — Redirect NIJE u translation.py "
                "(SM-D6/SEO4-5)."
            )


# AC1: old_path field — unique + db_index u migraciji
def test_old_path_unique_and_indexed_in_migration():
    op = _get_create_redirect_operation()
    fields = dict(op.fields)
    old_path = fields["old_path"]
    assert old_path.unique is True, "0002 old_path MORA biti unique=True (AC1)."
    # unique=True implicitno indeksira; db_index ostaje True u definiciji
    assert getattr(old_path, "db_index", False) is True, (
        "0002 old_path MORA imati db_index=True (AC1/SM-D4)."
    )


# AC1: is_active field — default True + db_index u migraciji
def test_is_active_default_and_indexed_in_migration():
    op = _get_create_redirect_operation()
    fields = dict(op.fields)
    is_active = fields["is_active"]
    assert is_active.default is True, "0002 is_active MORA imati default=True (AC1)."
    assert getattr(is_active, "db_index", False) is True, (
        "0002 is_active MORA imati db_index=True (AC1/SM-D4)."
    )


# AC1: dependencies sadrži ("seo", "0001_initial")
def test_migration_depends_on_0001_initial():
    from importlib import import_module

    mod = import_module("apps.seo.migrations.0002_redirect")
    deps = list(mod.Migration.dependencies)
    assert ("seo", "0001_initial") in deps, (
        "0002 dependencies MORA imati ('seo', '0001_initial') — AC1."
    )


# AC1 REGRESSION: makemigrations --check → no pending changes (model/migracija sync)
@pytest.mark.django_db
def test_no_pending_migrations():
    from io import StringIO

    from django.core.management import call_command

    out = StringIO()
    try:
        call_command("makemigrations", "seo", "--check", "--dry-run", stdout=out, stderr=out)
        exit_code = 0
    except SystemExit as exc:
        exit_code = exc.code or 0
    assert exit_code == 0, (
        "makemigrations seo --check --dry-run MORA biti čist (0 pending) — Redirect model i "
        f"0002 sinhronizovani. Output: {out.getvalue()}"
    )
