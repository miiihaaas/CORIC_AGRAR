"""Story 7.1 — AC3: 0002 data seed migracija (RunPython reverzibilan) (TEA RED).

Pokriva:
- Posle migrate, singleton postoji (count==1, pk==1) sa title_sr/body_sr (Lorem Ipsum,
  puni dijakritik), effective_date IS None (G-11 — bez fake pravnog datuma).
- 0002 forward idempotentan (get_or_create(pk=1) — re-run → još uvek count==1 & pk==1).
- 0002 reverse_code briše pk=1 red (filter(pk=1).delete()).

NAPOMENA (TEA-D2): pytest-django primenjuje SVE migracije (uklj. 0002 seed) → seeded
red postoji po default-u. Reverse/forward callable testovi importuju migration modul
direktno (mirror apps/pages/tests/test_sitesettings_migration_seed.py +
apps/brands/tests/test_seed_migration_0003.py).

⚠️ COLLECTION-SAFETY: apps.gdpr importi UNUTAR funkcija — RED: model/migracije ne
postoje → ImportError / LookupError.

Refs:
- 7-1-...-admin.md AC3 + SM-D5 + Gotcha G-2/G-3/G-11
- apps/pages/tests/test_sitesettings_migration_seed.py (mirror)
"""

from __future__ import annotations

from importlib import import_module

import pytest

pytestmark = pytest.mark.django_db


def _get_model():
    from apps.gdpr.models import CookiePolicy

    return CookiePolicy


def _import_seed_module():
    try:
        return import_module("apps.gdpr.migrations.0002_seed_cookie_policy")
    except ImportError:
        pytest.fail(
            "Migration modul 'apps.gdpr.migrations.0002_seed_cookie_policy' nije "
            "pronađen. Dev MORA kreirati RunPython data seed migraciju (AC3/SM-D5)."
        )


# AC3: posle migrate seed je kreiran — count==1, pk==1 (postoji pre prvog deploy-a)
def test_seed_creates_single_singleton_row():
    CookiePolicy = _get_model()
    assert CookiePolicy.objects.count() == 1, (
        "Posle migracija (0002 seed auto-applied u test bazi) MORA postojati TAČNO 1 "
        f"CookiePolicy red, dobio count()={CookiePolicy.objects.count()} (AC3/SM-D5)."
    )
    assert CookiePolicy.objects.filter(pk=1).exists(), (
        "Seed MORA kreirati pk=1 red — 'postoji pre prvog deploy-a' (AC3/epics.md:1007)."
    )


# AC3/G-3: seed popunjava title_sr/body_sr direktno (NE prazno) — sr fallback radi
def test_seed_populates_sr_columns():
    CookiePolicy = _get_model()
    obj = CookiePolicy.objects.get(pk=1)
    assert (obj.title_sr or "").strip() != "", (
        "Seed MORA popuniti title_sr DIREKTNO (Lorem Ipsum; G-3 — bar _sr da fallback "
        "vrati srpski). Prazan title_sr → seed nije popunio _sr kolonu."
    )
    assert (obj.body_sr or "").strip() != "", (
        "Seed MORA popuniti body_sr DIREKTNO (Lorem Ipsum; G-3)."
    )


# AC3/G-11: seed effective_date IS None (NE fake pravni datum — Adversarial #3)
def test_seed_effective_date_is_none():
    CookiePolicy = _get_model()
    obj = CookiePolicy.objects.get(pk=1)
    assert obj.effective_date is None, (
        "Seed NE SME postaviti effective_date (placeholder politika bez zavaravajućeg "
        f"pravnog datuma — G-11/Adversarial #3), dobio {obj.effective_date!r}."
    )


# AC3/SM-D5: hu/en se NE seed-uju (oslanjaju se na sr fallback) — title_hu/title_en prazni
def test_seed_does_not_populate_hu_en():
    CookiePolicy = _get_model()
    obj = CookiePolicy.objects.get(pk=1)
    assert (obj.title_hu or "") == "" and (obj.title_en or "") == "", (
        "Seed NE SME popuniti title_hu/title_en (OQ-1 — hu/en se oslanjaju na sr "
        "fallback dok biznis ne unese prevod kroz admin; SM-D5)."
    )


# AC3: 0002 forward idempotentan (get_or_create(pk=1) — re-run NE kreira pk=2; G-2)
def test_seed_forward_idempotent():
    from django.apps import apps as django_apps

    CookiePolicy = _get_model()
    module = _import_seed_module()

    forward_fn = None
    for cand in ("seed_cookie_policy", "forward", "seed", "forward_code"):
        forward_fn = getattr(module, cand, None)
        if callable(forward_fn):
            break
    if forward_fn is None:
        from django.db.migrations.operations import RunPython

        for op in module.Migration.operations:
            if isinstance(op, RunPython) and op.code is not None:
                forward_fn = op.code
                break
    assert forward_fn is not None, "0002 MORA imati RunPython forward callable (AC3)."

    class _StubSchemaEditor:
        pass

    count_before = CookiePolicy.objects.count()
    forward_fn(django_apps, _StubSchemaEditor())  # re-run forward
    assert CookiePolicy.objects.count() == count_before == 1, (
        "0002 forward MORA biti idempotentan (get_or_create(pk=1) — NE kreira pk=2 na "
        f"re-run; G-2), count pre={count_before}, posle={CookiePolicy.objects.count()}."
    )
    assert CookiePolicy.objects.filter(pk=1).exists(), "pk=1 MORA i dalje postojati."


# AC3: 0002 reverse_code briše pk=1 red (filter(pk=1).delete())
def test_seed_reverse_code_removes_row():
    from django.apps import apps as django_apps

    CookiePolicy = _get_model()
    module = _import_seed_module()

    reverse_fn = None
    for cand in ("reverse_seed", "reverse", "reverse_code", "unseed_cookie_policy"):
        reverse_fn = getattr(module, cand, None)
        if callable(reverse_fn):
            break
    if reverse_fn is None:
        from django.db.migrations.operations import RunPython

        for op in module.Migration.operations:
            if isinstance(op, RunPython) and op.reverse_code is not None:
                reverse_fn = op.reverse_code
                break
    assert reverse_fn is not None, (
        "0002 RunPython MORA imati reverse_code definisan (NE noop; AC3/SM-D5)."
    )

    class _StubSchemaEditor:
        pass

    assert CookiePolicy.objects.filter(pk=1).exists(), (
        "Seed pk=1 red mora postojati pre reverse-a."
    )
    reverse_fn(django_apps, _StubSchemaEditor())
    assert not CookiePolicy.objects.filter(pk=1).exists(), (
        "reverse_code MORA obrisati pk=1 red (AC3/SM-D5 reverz bez greške)."
    )


# AC3: 0002 dependencies → ("gdpr","0001_initial")
def test_seed_depends_on_initial():
    module = _import_seed_module()
    deps = list(module.Migration.dependencies)
    assert ("gdpr", "0001_initial") in deps, (
        f"0002 dependencies MORA imati ('gdpr','0001_initial') — AC3, dobio {deps}."
    )
