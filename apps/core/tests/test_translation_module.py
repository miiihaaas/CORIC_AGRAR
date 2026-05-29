"""Tests za Story 1.4 - AC4: apps/core/translation.py placeholder + example pattern.

Verifikuje:
- AC4: modul importable bez exception-a (`import apps.core.translation` exit 0)
- AC4: example sadrzi `fields = ("name", "description")` (canonical iz story spec-a;
       NE 'slogan' ili drugi field — iter-1 koristio pogresan field, sad fixed)

Pokrenuti sa:
    uv run pytest apps/core/tests/test_translation_module.py -v

TEA RED faza: svi testovi MORAJU pasti dok Dev ne zavrsi Story 1.4.
Naming convention: srpska latinica + engleski; bez cirilice.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

# =============================================================================
# Konstante (project paths)
# =============================================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
TRANSLATION_PY = PROJECT_ROOT / "apps" / "core" / "translation.py"


# =============================================================================
# Helper
# =============================================================================


def _ensure_sys_path():
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))


# =============================================================================
# AC4 — translation.py importability + minimalan example
# =============================================================================


def test_ac4_translation_module_importable():
    """AC4: `import apps.core.translation` mora prolaziti bez exception-a.

    Modul je placeholder + dokumentovan primer. Sav primer kod je commented-out
    (nema aktivnih import-a / register() poziva), pa import mora biti trivijalan.
    """
    if not TRANSLATION_PY.exists():
        pytest.fail(
            f"apps/core/translation.py ne postoji na {TRANSLATION_PY}. "
            f"Story 1.4 AC4 zahteva placeholder modul."
        )
    _ensure_sys_path()
    # Force fresh import
    for mod_key in list(sys.modules.keys()):
        if mod_key.startswith("apps.core.translation"):
            del sys.modules[mod_key]
    try:
        importlib.import_module("apps.core.translation")
    except Exception as exc:
        pytest.fail(
            f"`import apps.core.translation` raise-uje {type(exc).__name__}: {exc}. "
            f"Modul mora biti validan Python (sav primer kod commented-out)."
        )


def test_ac4_translation_example_fields_minimal():
    """AC4: example pattern u docstring-u / komentaru koristi `fields = ("name", "description")`.

    Canonical iz Story 1.4 spec-a (Dev Notes § apps/core/translation.py Template).
    Iter-1 koristio razlicit field set (slogan) — sada normalizovano na "name", "description".
    """
    if not TRANSLATION_PY.exists():
        pytest.fail("apps/core/translation.py ne postoji (videti prethodni test).")
    src = TRANSLATION_PY.read_text(encoding="utf-8")
    # Tolerantno na varijacije u whitespace-u/quote tipu (single/double)
    has_canonical = (
        'fields = ("name", "description")' in src
        or "fields = ('name', 'description')" in src
        or 'fields=("name", "description")' in src
    )
    assert has_canonical, (
        'apps/core/translation.py ne sadrzi canonical example `fields = ("name", "description")`. '
        "Story 1.4 spec (Dev Notes § translation.py Template) propisuje tacno ovaj redosled. "
        "Pronadji `fields = (...)` red u modulu i normalizuj."
    )
    # Dodatno: pominje TranslationOptions + register + modeltranslation u docstring-u
    for keyword in ("TranslationOptions", "register", "modeltranslation"):
        assert keyword in src, (
            f"apps/core/translation.py ne pominje `{keyword}` u docstring-u/komentaru. "
            f"AC4 zahteva edukativan placeholder koji eksplicitno referencira "
            f"django-modeltranslation API."
        )


def test_ac4_translation_no_active_register_call():
    """AC4 (regression guard): translation.py NE SME imati AKTIVAN `@register(...)` poziv.

    Story 1.4 nema modele — sav primer kod je commented-out (`#` prefix). Ako Dev
    preempt-uje Story 2.1+ i doda stvarni register() poziv, ovaj test ga uhvati.
    """
    if not TRANSLATION_PY.exists():
        pytest.fail("apps/core/translation.py ne postoji.")
    src = TRANSLATION_PY.read_text(encoding="utf-8")
    # Skipuj komentare i docstring blokove
    active_register_lines = []
    in_docstring = False
    docstring_delim = None
    for raw in src.splitlines():
        line = raw.strip()
        if line.startswith("#"):
            continue
        for delim in ('"""', "'''"):
            if delim in line:
                count = line.count(delim)
                if count % 2 == 1:
                    if not in_docstring:
                        in_docstring = True
                        docstring_delim = delim
                    elif docstring_delim == delim:
                        in_docstring = False
                        docstring_delim = None
                break
        if in_docstring:
            continue
        # Trazi @register(...) ili register(<Model>) na nivou modula (ne u komentaru)
        if line.startswith("@register") or "register(" in line:
            active_register_lines.append(raw)
    assert not active_register_lines, (
        f"apps/core/translation.py sadrzi AKTIVAN register(...) poziv: {active_register_lines}. "
        f"Story 1.4 nema modele — sav primer kod MORA biti commented-out (# prefix). "
        f"Stvarna registracija dolazi u Story 2.1+ (apps/brands/translation.py)."
    )
