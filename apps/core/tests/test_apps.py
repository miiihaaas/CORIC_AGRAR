"""Tests za Story 1.4 - AC1 + AC2: apps/core/ Django app skeleton + registracija.

Verifikuje:
- AC1: apps/__init__.py + apps/core/__init__.py + apps/core/apps.py postoje
- AC1: CoreConfig klasa definisana sa name="apps.core" i BigAutoField default
- AC2: apps.core registrovan u INSTALLED_APPS (runtime via django.apps.apps.get_app_config)

Pokrenuti sa:
    uv run pytest apps/core/tests/test_apps.py -v

TEA RED faza: svi testovi MORAJU pasti dok Dev ne zavrsi Story 1.4.
Naming convention: srpska latinica + engleski; bez cirilice.
"""

from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

import pytest

# =============================================================================
# Konstante (project paths)
# =============================================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
APPS_DIR = PROJECT_ROOT / "apps"
APPS_INIT = APPS_DIR / "__init__.py"
CORE_DIR = APPS_DIR / "core"
CORE_INIT = CORE_DIR / "__init__.py"
CORE_APPS_PY = CORE_DIR / "apps.py"

TEST_SECRET = "test-secret-key-for-tea-story-1-4-not-a-real-secret"


# =============================================================================
# Helper funkcije
# =============================================================================


def _ensure_sys_path():
    """Project root mora biti u sys.path da bi `import apps.core.X` radio."""
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))


def _setup_django():
    """Bootstrap Django (settings configured) sa DJANGO_SECRET_KEY env varom.

    Treba u testovima koji koriste django.apps.apps registry ili shell-level
    operations koje zahtevaju settings.configure() / django.setup().
    """
    _ensure_sys_path()
    os.environ.setdefault("DJANGO_SECRET_KEY", TEST_SECRET)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
    try:
        import django
    except ImportError:  # pragma: no cover
        pytest.fail("Django nije instaliran (uv sync prvo).")
    if not getattr(django, "_setup_done", False):
        django.setup()
        django._setup_done = True  # type: ignore[attr-defined]


# =============================================================================
# AC1 — apps/ namespace + apps/core/ skeleton (filesystem)
# =============================================================================


def test_ac1_apps_namespace_dir_exists():
    """AC1: apps/__init__.py mora postojati (namespace marker).

    Bez njega Django startup baca `ModuleNotFoundError: No module named 'apps'`
    pri registraciji `apps.core` u INSTALLED_APPS (Gotcha #6).
    """
    assert APPS_DIR.exists(), (
        f"apps/ direktorijum ne postoji na {APPS_DIR}. "
        f"Kreiraj direktorijum + __init__.py (Story 1.4 AC1)."
    )
    assert APPS_INIT.exists(), (
        f"apps/__init__.py ne postoji na {APPS_INIT}. "
        f"Mora biti prazan ili docstring-only (namespace marker)."
    )


def test_ac1_core_app_dir_exists():
    """AC1: apps/core/__init__.py + apps/core/apps.py moraju postojati."""
    assert CORE_DIR.exists(), (
        f"apps/core/ direktorijum ne postoji na {CORE_DIR}. "
        f"Story 1.4 kreira prvi Django app (apps/core/)."
    )
    assert CORE_INIT.exists(), (
        f"apps/core/__init__.py ne postoji na {CORE_INIT}. "
        f"Bez njega apps.core nije validan Python paket."
    )
    assert CORE_APPS_PY.exists(), (
        f"apps/core/apps.py ne postoji na {CORE_APPS_PY}. "
        f"Mora sadrzati CoreConfig(AppConfig) klasu."
    )


def test_ac1_core_config_class_defined():
    """AC1: apps/core/apps.py sadrzi `class CoreConfig(AppConfig)` sa name='apps.core'.

    Importuje modul i verifikuje atribute (NIJE regex check — assertion na realnoj
    klasi da bismo uhvatili typos kao `name = "core"` ili `name = "apps_core"`).
    """
    if not CORE_APPS_PY.exists():
        pytest.fail("apps/core/apps.py ne postoji (videti prethodni test).")
    _ensure_sys_path()
    # Force fresh import
    for mod_key in list(sys.modules.keys()):
        if mod_key.startswith("apps.core.apps") or mod_key == "apps.core":
            del sys.modules[mod_key]
    try:
        module = importlib.import_module("apps.core.apps")
    except ImportError as exc:
        pytest.fail(
            f"Ne mogu importovati apps.core.apps: {exc}. "
            f"Verovatno apps/__init__.py ili apps/core/__init__.py nedostaju."
        )
    assert hasattr(module, "CoreConfig"), (
        "apps/core/apps.py ne eksponuje klasu `CoreConfig`. "
        "Mora biti definisana kao subclass od django.apps.AppConfig."
    )
    CoreConfig = module.CoreConfig
    # Verifikuj name
    assert getattr(CoreConfig, "name", None) == "apps.core", (
        f"CoreConfig.name mora biti 'apps.core', dobijeno: "
        f"{getattr(CoreConfig, 'name', None)!r}. "
        f"Bilo kakav drugi naziv (npr. 'core', 'apps_core') BREAKS INSTALLED_APPS path."
    )
    # Verifikuj default_auto_field
    assert (
        getattr(CoreConfig, "default_auto_field", None)
        == "django.db.models.BigAutoField"
    ), (
        f"CoreConfig.default_auto_field mora biti 'django.db.models.BigAutoField', "
        f"dobijeno: {getattr(CoreConfig, 'default_auto_field', None)!r}."
    )


# =============================================================================
# AC2 — apps.core registrovan u INSTALLED_APPS (runtime check)
# =============================================================================


def test_ac2_apps_core_in_installed_apps_runtime():
    """AC2 / AC9.4: apps.core MORA biti runtime-registrovan u Django app registry.

    `django.apps.apps.get_app_config('core')` raise-uje LookupError ako nije.
    Ovaj test je STRONGER od regex check-a u base.py — uhvati slucaj kada Dev
    kreira apps/core/ skeleton ali zaboravi da doda 'apps.core' u INSTALLED_APPS.
    """
    _setup_django()
    try:
        from django.apps import apps as django_apps
    except ImportError:
        pytest.fail("Django nije importable.")
    try:
        config = django_apps.get_app_config("core")
    except LookupError as exc:
        pytest.fail(
            f"django.apps.apps.get_app_config('core') raise-uje LookupError: {exc}. "
            f"Verovatno 'apps.core' NIJE u INSTALLED_APPS u config/settings/base.py."
        )
    assert config.name == "apps.core", (
        f"AppConfig.name = {config.name!r}, ocekivano 'apps.core'."
    )


# =============================================================================
# Negative checks / scope hygiene
# =============================================================================


def test_ac1_core_tests_package_init_exists():
    """AC1: apps/core/tests/__init__.py MORA postojati (test package marker).

    NAPOMENA: TEA RED phase je IZBRISALA ovaj fajl da bi izbegla pytest collection
    collision sa top-level `tests/` paketom (oba dele ime 'tests' kada se koristi
    default importmode='prepend'). Dev MORA:
      1. Vratiti apps/core/tests/__init__.py (prazan fajl)
      2. Konfigurisati [tool.pytest.ini_options] sa importmode='importlib' u pyproject.toml
         (videti tests/test_i18n_setup.py::test_pytest_django_configured)
    """
    tests_init = APPS_DIR / "core" / "tests" / "__init__.py"
    assert tests_init.exists(), (
        f"apps/core/tests/__init__.py ne postoji na {tests_init}. "
        f"AC1 zahteva test package marker. TEA ga je izbrisala u RED phase-u "
        f"(collision); Dev mora vratiti + konfigurisati importmode='importlib'."
    )


def test_ac1_core_does_not_have_admin_or_forms_yet():
    """Story 1.4 scope guard (relaksirano u Story 2.1).

    Story 2.1 LEGITIMNO uvodi apps/core/models.py (TimestampedModel, SluggedModel)
    i apps/core/utils.py (slugify_ascii) kao FOUNDATION za Epic 2 domain apps.
    Vidi Story 2.1 AC9 + Decision D3.

    Ali admin.py, forms.py, signals.py, managers.py, migrations/ ostaju forbidden
    u apps/core/ — apps.core je infrastructure namespace, ne domain app sa CRUD.
    """
    forbidden = [
        CORE_DIR / "admin.py",
        CORE_DIR / "forms.py",
        CORE_DIR / "signals.py",
        CORE_DIR / "managers.py",
        CORE_DIR / "migrations",
    ]
    existing = [str(p.relative_to(PROJECT_ROOT)) for p in forbidden if p.exists()]
    assert not existing, (
        f"Forbidden artefakti u apps/core/: {existing}. "
        f"apps.core je infrastructure namespace — domain CRUD pripada apps/<domain>/."
    )
