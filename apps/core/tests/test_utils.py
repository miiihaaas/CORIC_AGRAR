"""Story 2.1 — apps/core/utils.py slugify_ascii unit testovi (RED phase).

Verifikuje:
- Modul se učitava bez ValueError (BR-14 regression guard — str.maketrans single-char keys)
- Empty string returns empty
- Srpska dijakritici (Ć/č/Š/š/Ž/ž/Đ/đ) → ASCII
- Srpska digrafovi (Dž/dž, Lj/lj, Nj/nj) → ASCII
- Mixed strings sa razmacima → kebab-case slug

Pokrenuti sa:
    uv run pytest apps/core/tests/test_utils.py -v

TEA RED phase: svi testovi MORAJU pasti dok Dev ne kreira apps/core/utils.py.
Naming: srpska latinica (no Cyrillic), engleski code identifiers.
"""

from __future__ import annotations


# =============================================================================
# Regression guard — modul mora učitati bez ValueError (BR-14, NEW-CRIT-1)
# =============================================================================


def test_slugify_ascii_module_imports_without_error():
    """BR-14: str.maketrans(dict) zahteva single-char ključeve.

    Naivan pokušaj str.maketrans({"Dž": "dz", ...}) raise-uje
    ValueError: string keys in translate table must be of length 1
    pri module-level evaluation. Two-stage replacement fix u Task 2.4 sprečava ovo.

    Ovaj test je MODULE-LEVEL crash regression guard.
    """
    from apps.core.utils import slugify_ascii  # noqa: F401

    # Ako stigne ovde, module se učitao OK
    assert callable(slugify_ascii)


# =============================================================================
# Empty / edge cases
# =============================================================================


def test_slugify_ascii_empty_string_returns_empty():
    """Empty input → empty output (bez exception)."""
    from apps.core.utils import slugify_ascii

    assert slugify_ascii("") == ""


# =============================================================================
# Dijakritici (single-character — preko str.translate)
# =============================================================================


def test_slugify_ascii_handles_diakritici():
    """Ć/č, Š/š, Ž/ž, Đ/đ → c/c, s/s, z/z, d/d."""
    from apps.core.utils import slugify_ascii

    assert slugify_ascii("Čorić") == "coric"
    assert slugify_ascii("Šargarepa") == "sargarepa"
    assert slugify_ascii("Žutilo") == "zutilo"
    assert slugify_ascii("Đak") == "dak"


def test_slugify_ascii_handles_uppercase_mixed_diakritici():
    """All-uppercase sa dijakriticima → lowercase ASCII."""
    from apps.core.utils import slugify_ascii

    assert slugify_ascii("ČORIĆ") == "coric"


# =============================================================================
# Digrafovi (multi-character — preko str.replace PRE str.translate)
# =============================================================================


def test_slugify_ascii_handles_digraphs():
    """Dž/dž, Lj/lj, Nj/nj → dz, lj, nj (već ASCII).

    Digrafovi MORAJU se zameniti PRE str.translate() jer maketrans
    ne podržava multi-char ključeve.
    """
    from apps.core.utils import slugify_ascii

    assert slugify_ascii("Džon") == "dzon"
    assert slugify_ascii("Ljubo") == "ljubo"
    assert slugify_ascii("Njuska") == "njuska"


# =============================================================================
# Mixed (multiword + razmaci + kombinacija dijakritika i digrafova)
# =============================================================================


def test_slugify_ascii_handles_mixed():
    """Multiword input sa razmacima i kombinovanim dijakriticima → kebab-case."""
    from apps.core.utils import slugify_ascii

    assert slugify_ascii("Đorđe Šarac") == "dorde-sarac"
