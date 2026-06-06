"""Story 7.1 — AC3/AC5: 0001_initial schema introspekcija + app scaffold (TEA RED).

Pokriva:
- AC5: GdprConfig.name=="apps.gdpr" (apps. prefiks — G-1) + BigAutoField; "apps.gdpr"
  u INSTALLED_APPS POSLE modeltranslation; dep boundary (gdpr NE importuje domain app-ove).
- AC3: 0001_initial CreateModel("CookiePolicy") sa title/body + _sr/_hu/_en kolone +
  effective_date + created_at/updated_at; effective_date/timestamp NISU _sr/_hu/_en.
- AC3 REGRESSION: makemigrations --check → no changes (dodavanje apps.gdpr NE dira
  postojeće app migracije — G-8).

PREFERIRA introspekciju operations liste (IMP-7 presedan) NAD round-trip migrate.

⚠️ COLLECTION-SAFETY: apps.gdpr importi UNUTAR funkcija — apps.gdpr NE postoji →
ModuleNotFoundError per-test (RED), NE collection-abort.

Refs:
- 7-1-...-admin.md AC3/AC5 + SM-D1 + Gotcha G-1/G-8/G-9
- apps/seo/tests/test_seometa_migration.py + apps/blog/tests/test_app_scaffold.py (mirror)
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from django.conf import settings


# ─────────────────────────────────────────────────────────────────────────────
# AC5 — app scaffold + INSTALLED_APPS
# ─────────────────────────────────────────────────────────────────────────────


# AC5/G-1: GdprConfig.name == "apps.gdpr" (sa apps. prefiksom)
def test_gdpr_config_name_is_apps_gdpr():
    from apps.gdpr.apps import GdprConfig

    assert GdprConfig.name == "apps.gdpr", (
        f"GdprConfig.name MORA biti 'apps.gdpr' (apps. prefiks — G-1), dobio "
        f"{GdprConfig.name!r}."
    )


# AC5: GdprConfig.default_auto_field == BigAutoField
def test_gdpr_config_default_auto_field():
    from apps.gdpr.apps import GdprConfig

    assert GdprConfig.default_auto_field == "django.db.models.BigAutoField", (
        f"GdprConfig.default_auto_field MORA biti BigAutoField, dobio "
        f"{GdprConfig.default_auto_field!r}."
    )


# AC5: "apps.gdpr" registrovan u INSTALLED_APPS
def test_apps_gdpr_in_installed_apps():
    assert "apps.gdpr" in settings.INSTALLED_APPS, (
        "'apps.gdpr' MORA biti u INSTALLED_APPS (AC5/SM-D1)."
    )


# AC5: "apps.gdpr" POSLE "modeltranslation" (KRITIČNO za translatable model)
def test_apps_gdpr_after_modeltranslation():
    apps_list = list(settings.INSTALLED_APPS)
    assert "apps.gdpr" in apps_list and "modeltranslation" in apps_list, (
        "'apps.gdpr' i 'modeltranslation' MORAJU biti u INSTALLED_APPS."
    )
    assert apps_list.index("apps.gdpr") > apps_list.index("modeltranslation"), (
        "'apps.gdpr' MORA biti POSLE 'modeltranslation' u INSTALLED_APPS "
        "(translatable model zahtev — base.py:34 / SM-D1)."
    )


# AC5: dep boundary — apps/gdpr/ NE importuje domain app-ove (products/brands/blog/pages/seo)
def test_dep_boundary_gdpr_does_not_import_other_domain_apps():
    """Statički grep import izvora apps/gdpr/ — gdpr koristi SAMO apps.core (+ Django/
    modeltranslation). Import products/brands/blog/pages/seo/search/forms KRŠI invariantu."""
    gdpr_dir = Path(settings.BASE_DIR) / "apps" / "gdpr"
    apps_py = gdpr_dir / "apps.py"
    assert apps_py.exists(), (
        f"apps/gdpr/apps.py MORA postojati ({apps_py}). RED: app još ne postoji."
    )

    forbidden = ("products", "brands", "search", "pages", "forms", "blog", "seo")
    pattern = re.compile(
        r"^\s*(from|import)\s+(apps\.)?(" + "|".join(forbidden) + r")\b",
        re.MULTILINE,
    )
    offenders = []
    for py in gdpr_dir.rglob("*.py"):
        if "tests" in py.parts:
            continue  # testovi smeju importovati šta treba
        text = py.read_text(encoding="utf-8")
        if pattern.search(text):
            offenders.append(str(py.relative_to(gdpr_dir)))
    assert offenders == [], (
        f"apps/gdpr/ NE SME importovati domain app-ove — dep boundary AC5/SM-D1. "
        f"Prekršioci: {offenders}."
    )


# AC5: manage.py check čist (0 ozbiljnih grešaka)
def test_manage_check_clean():
    from django.core.checks import run_checks

    errors = [e for e in run_checks() if e.is_serious()]
    assert errors == [], (
        f"manage.py check MORA biti čist (exit 0) sa registrovanim apps.gdpr — AC5. "
        f"Ozbiljne greške: {errors}."
    )


# ─────────────────────────────────────────────────────────────────────────────
# AC3 — 0001_initial schema introspekcija
# ─────────────────────────────────────────────────────────────────────────────


def _get_create_cookiepolicy_operation():
    from importlib import import_module

    from django.db import migrations

    mod = import_module("apps.gdpr.migrations.0001_initial")
    for op in mod.Migration.operations:
        if isinstance(op, migrations.CreateModel) and op.name == "CookiePolicy":
            return op
    raise AssertionError("0001_initial MORA imati CreateModel('CookiePolicy') (AC3).")


# AC3: 0001_initial modul postoji i nosi Migration sa initial=True
def test_initial_migration_module_exists():
    from importlib import import_module

    mod = import_module("apps.gdpr.migrations.0001_initial")
    assert hasattr(mod, "Migration"), (
        "0001_initial MORA definisati Migration klasu (AC3)."
    )
    assert getattr(mod.Migration, "initial", False) is True, (
        "0001_initial MORA imati initial=True (AC3)."
    )


# AC3: CreateModel('CookiePolicy') sa title/body + _sr/_hu/_en + effective_date + timestamp
def test_createmodel_cookiepolicy_columns():
    op = _get_create_cookiepolicy_operation()
    field_names = {name for name, _ in op.fields}

    # base translatable + jezik-neutralna polja
    assert "title" in field_names, "0001 MORA imati title kolonu (AC3)."
    assert "body" in field_names, "0001 MORA imati body kolonu (AC3)."
    assert "effective_date" in field_names, (
        "0001 MORA imati effective_date kolonu (jezik-neutralna — AC3)."
    )

    # _sr/_hu/_en kolone (modeltranslation; translation.py PRE makemigrations — G-9)
    for base in ("title", "body"):
        for lang in ("sr", "hu", "en"):
            assert f"{base}_{lang}" in field_names, (
                f"0001 MORA imati {base}_{lang} kolonu (modeltranslation — AC3/G-9)."
            )

    # nasleđene TimestampedModel kolone
    assert {"created_at", "updated_at"} <= field_names, (
        "0001 MORA imati created_at/updated_at (TimestampedModel — AC3)."
    )


# AC3: effective_date/timestamp NISU _sr/_hu/_en (jezik-neutralni — NE translatable)
def test_no_locale_columns_for_neutral_fields():
    op = _get_create_cookiepolicy_operation()
    field_names = {name for name, _ in op.fields}
    for base in ("effective_date", "created_at", "updated_at"):
        for lang in ("sr", "hu", "en"):
            assert f"{base}_{lang}" not in field_names, (
                f"{base}_{lang} NE SME postojati — {base} je jezik-neutralan (AC3)."
            )


# AC3 REGRESSION/G-8: makemigrations --check → no pending changes (gdpr izolovan)
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
        "makemigrations --check --dry-run MORA biti čist (0 pending) — dodavanje "
        "apps.gdpr NE dira postojeće app migracije (G-8). Output: " + out.getvalue()
    )
