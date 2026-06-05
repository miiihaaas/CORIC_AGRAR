"""Story 6.1 — schema migracija 0001_initial introspekcija (TEA RED phase).

Pokriva AC2: `apps/seo/migrations/0001_initial.py` postoji; `CreateModel("SeoMeta")`;
`content_object` GFK NIJE kolona; `content_type` FK + `object_id`; `_sr/_hu/_en`
kolone (meta_title/meta_description); `UniqueConstraint seo_seometa_ct_obj_uniq`;
`dependencies` ima `("contenttypes","__first__")`. REGRESSION: `makemigrations
--check` → no changes (receiving modeli NE dobijaju migraciju — OQ-4).

PREFERIRA introspekciju operations liste (IMP-7 presedan) NAD round-trip migrate.

⚠️ GUARD: apps.seo importi UNUTAR funkcija (collection-safety) — migration modul
NE postoji još → ModuleNotFoundError per-test (RED), NE collection-abort.

Refs:
- 6-1-...-admin.md AC2 + Task 7.4 + SM-D4 + Gotcha SEO1-5
"""

from __future__ import annotations

import pytest


# AC2: 0001_initial.py modul postoji i nosi Migration sa initial=True
def test_initial_migration_module_exists():
    from importlib import import_module

    mod = import_module("apps.seo.migrations.0001_initial")
    assert hasattr(mod, "Migration"), "0001_initial MORA definisati Migration klasu (AC2)."
    assert getattr(mod.Migration, "initial", False) is True, (
        "0001_initial MORA imati initial=True (AC2)."
    )


def _get_create_seometa_operation():
    from importlib import import_module

    from django.db import migrations

    mod = import_module("apps.seo.migrations.0001_initial")
    for op in mod.Migration.operations:
        if isinstance(op, migrations.CreateModel) and op.name == "SeoMeta":
            return op
    raise AssertionError("0001_initial MORA imati CreateModel('SeoMeta') (AC2).")


# AC2: CreateModel('SeoMeta') sa GFK fields + content_object NIJE kolona
def test_createmodel_seometa_columns():
    op = _get_create_seometa_operation()
    field_names = {name for name, _ in op.fields}

    # content_type FK + object_id su realne kolone
    assert "content_type" in field_names, "0001 MORA imati content_type FK kolonu (AC2)."
    assert "object_id" in field_names, "0001 MORA imati object_id kolonu (AC2)."

    # content_object GFK NIJE DB kolona (composite accessor — Gotcha SEO1-1)
    assert "content_object" not in field_names, (
        "content_object (GenericForeignKey) NE SME biti kolona u 0001 — composite accessor (AC2)."
    )

    # _sr/_hu/_en kolone za translatable polja (Gotcha SEO1-5)
    for base in ("meta_title", "meta_description"):
        for lang in ("sr", "hu", "en"):
            assert f"{base}_{lang}" in field_names, (
                f"0001 MORA imati {base}_{lang} kolonu (modeltranslation — AC2)."
            )

    # og_image + exclude_from_sitemap
    assert "og_image" in field_names, "0001 MORA imati og_image kolonu (AC2)."
    assert "exclude_from_sitemap" in field_names, (
        "0001 MORA imati exclude_from_sitemap kolonu (AC2)."
    )

    # nasleđene TimestampedModel kolone
    assert {"created_at", "updated_at"} <= field_names, (
        "0001 MORA imati created_at/updated_at (TimestampedModel — AC2)."
    )


# AC2: UniqueConstraint(content_type, object_id) seo_seometa_ct_obj_uniq u migraciji
def test_migration_has_unique_constraint():
    op = _get_create_seometa_operation()
    constraints = op.options.get("constraints", [])
    names = {getattr(c, "name", None) for c in constraints}
    assert "seo_seometa_ct_obj_uniq" in names, (
        "0001 CreateModel options MORA imati UniqueConstraint 'seo_seometa_ct_obj_uniq' (SM-D4)."
    )


# AC2: dependencies sadrži ("contenttypes", "__first__") (FK→ContentType na fresh DB)
def test_migration_depends_on_contenttypes():
    from importlib import import_module

    mod = import_module("apps.seo.migrations.0001_initial")
    deps = list(mod.Migration.dependencies)
    assert any(app == "contenttypes" for app, _ in deps), (
        "0001 dependencies MORA imati ('contenttypes', '__first__') — FK→ContentType (AC2)."
    )


# AC2 REGRESSION: makemigrations --check → no pending changes (sve materijalizovano)
@pytest.mark.django_db
def test_no_pending_migrations():
    from io import StringIO

    from django.core.management import call_command

    out = StringIO()
    try:
        call_command("makemigrations", "--check", "--dry-run", stdout=out, stderr=out)
        exit_code = 0
    except SystemExit as exc:
        exit_code = exc.code or 0
    assert exit_code == 0, (
        "makemigrations --check --dry-run MORA biti čist (0 pending) — model i 0001 "
        f"sinhronizovani, receiving modeli NE dobijaju migraciju (OQ-4). Output: {out.getvalue()}"
    )
