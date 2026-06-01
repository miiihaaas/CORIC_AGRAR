"""Story 3.4 — AC3+AC4: 0001 schema (+ modeltranslation kolone) + 0002 data seed (Task 9.3).

RED phase (TEA). Verifikuje:
- 0001_initial CreateModel materijalizuje DB tabelu sa modeltranslation kolonama
  (`slogan_sr/hu/en`, `address_sr/hu/en`, `working_hours_sr/hu/en`) — DB introspect.
- 0002 seed popunjava jedinu instancu pk=1 (count==1; phone_sales; puni-dijakritik address).
- reverse_code briše pk=1 (idempotentnost forward + čist reverse).

NAPOMENA (TEA-D2): pytest-django primenjuje SVE migracije (uklj. 0002 seed) → seeded red
postoji po default-u. Reverse/forward callable testovi importuju migration modul direktno
(mirror apps/brands/tests/test_seed_migration_0003.py pattern).

RED razlog: apps/pages/migrations/ + model ne postoje → ImportError / LookupError.

Dev NE piše testove. Pokrenuti:
    just test apps/pages/tests/test_sitesettings_migration_seed.py -v
"""

from __future__ import annotations

from importlib import import_module

import pytest
from django.db import connection

pytestmark = pytest.mark.django_db


def _get_model():
    from apps.pages.models import SiteSettings

    return SiteSettings


def test_0001_creates_modeltranslation_columns():
    """AC3: 0001_initial materijalizuje DB kolone uklj. _sr/_hu/_en za translatable polja."""
    SiteSettings = _get_model()
    table = SiteSettings._meta.db_table

    with connection.cursor() as cursor:
        columns = {col.name for col in connection.introspection.get_table_description(cursor, table)}

    expected_translation_cols = {
        "slogan_sr", "slogan_hu", "slogan_en",
        "address_sr", "address_hu", "address_en",
        "working_hours_sr", "working_hours_hu", "working_hours_en",
    }
    missing = expected_translation_cols - columns
    assert not missing, (
        f"0001_initial MORA uključiti modeltranslation kolone {missing} (translation.py "
        f"registrovan PRE makemigrations; AC3/AC5). Postojeće kolone: {sorted(columns)!r}"
    )
    # Nasleđeni timestamp-ovi takođe u tabeli
    assert {"created_at", "updated_at"} <= columns, (
        "0001_initial MORA uključiti nasleđene created_at/updated_at (TimestampedModel)."
    )


def test_seed_creates_single_row_with_values():
    """AC4: 0002 seed (auto-applied) → count()==1, phone_sales popunjen."""
    SiteSettings = _get_model()

    assert SiteSettings.objects.count() == 1, (
        "Posle migracija (0002 seed auto-applied u test bazi) MORA postojati TAČNO 1 "
        f"SiteSettings red, dobio count()={SiteSettings.objects.count()} (AC4/SM-D4)."
    )
    obj = SiteSettings.load()
    assert obj.phone_sales == "+381 230 468 168", (
        f"Seed phone_sales MORA biti '+381 230 468 168' (SA razmacima — SM-D8), dobio "
        f"{obj.phone_sales!r}."
    )


def test_seed_address_is_full_diacritic():
    """AC4/OQ-6: seed address (sr) je PUNI-dijakritik „Vojvođanska" (NE šišana „Vojvodjanska")."""
    from django.utils.translation import activate

    SiteSettings = _get_model()
    activate("sr")
    obj = SiteSettings.load()
    address = obj.address or ""
    assert "Vojvođanska" in address, (
        f"Seed address (sr) MORA sadržati puni-dijakritik 'Vojvođanska' (AC4/OQ-6), dobio "
        f"{address!r}."
    )
    assert "Vojvodjanska" not in address, (
        "Seed address NE SME koristiti šišanu latinicu 'Vojvodjanska' (AC4/OQ-6)."
    )


def test_seed_reverse_code_removes_row():
    """AC4: 0002 reverse_code briše pk=1 red (project-context.md:227 — reverse_code obavezan).

    Direktno poziva reverse callable iz migration modula (mirror test_seed_migration_0003).
    """
    SiteSettings = _get_model()

    try:
        migration_module = import_module(
            "apps.pages.migrations.0002_seed_sitesettings"
        )
    except ImportError:
        pytest.fail(
            "Migration modul 'apps.pages.migrations.0002_seed_sitesettings' nije pronađen. "
            "Dev MORA kreirati RunPython data seed migraciju sa reverse_code (AC4/SM-D4)."
        )

    # Pronađi reverse callable. RunPython čuva (code, reverse_code) — pokušaj uobičajena imena;
    # fallback: izvuci iz Migration.operations RunPython.reverse_code.
    from django.apps import apps as django_apps

    class _StubSchemaEditor:
        pass

    reverse_fn = None
    for cand in ("reverse_code", "reverse_seed", "unseed_sitesettings", "delete_sitesettings"):
        reverse_fn = getattr(migration_module, cand, None)
        if callable(reverse_fn):
            break

    if reverse_fn is None:
        # Izvuci iz Migration.operations
        migration_cls = getattr(migration_module, "Migration", None)
        assert migration_cls is not None, (
            "0002 modul MORA imati Migration klasu sa RunPython operacijom."
        )
        from django.db.migrations.operations import RunPython

        for op in migration_cls.operations:
            if isinstance(op, RunPython) and op.reverse_code is not None:
                reverse_fn = op.reverse_code
                break
        assert reverse_fn is not None, (
            "0002 RunPython MORA imati reverse_code definisan (NE noop; project-context.md:227)."
        )

    # Seed red postoji pre reverse-a
    assert SiteSettings.objects.filter(pk=1).exists(), "Seed pk=1 red mora postojati pre reverse-a."

    reverse_fn(django_apps, _StubSchemaEditor())

    assert not SiteSettings.objects.filter(pk=1).exists(), (
        "reverse_code MORA obrisati pk=1 red (AC4/SM-D4 reverz bez greške)."
    )
