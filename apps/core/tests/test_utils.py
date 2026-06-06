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


# =============================================================================
# Story 6.6 AC4 (SM-D7, G1) — kanonski hreflang/slug primer
#
# VERIFIKACIONI test (NE novi kod, NE migracija, NE `safe_slugify` alias — G1:
# stvarno ime je `slugify_ascii`). Dijakritici (Č/Š/Ž/Đ→c/s/z/d) + digrafovi
# (Dž/Lj/Nj) su VEĆ pokriveni gore (test_slugify_ascii_handles_diakritici /
# _handles_digraphs / _handles_mixed) → 6.6 NE duplira. Dodaje SAMO tačan AC4
# string literal `'Ćorić Agrar' == 'coric-agrar'` koji do sada NIJE asertovan.
# NAPOMENA: ovaj test prolazi ODMAH (slugify_ascii već radi od Story 2.1) — to je
# by-design GREEN verifikacioni guard za AC4 (potvrđuje postojeće ponašanje).
# =============================================================================


def test_slugify_ascii_coric_agrar_example():
    """AC4: kanonski primer iz Story 6.6 — `Ćorić Agrar` → `coric-agrar`.

    Ć/ć→c, razmak→`-`, lowercase, allow_unicode=False (čist ASCII kebab-case).
    Slug je DELJENI-ASCII kroz locale (jedan slug po objektu; locale = SAMO URL
    prefiks /sr//hu//en/ — SluggedModel slug NIJE translatable; SM-D7).
    """
    from apps.core.utils import slugify_ascii

    result = slugify_ascii("Ćorić Agrar")
    assert result == "coric-agrar", (
        f"AC4: slugify_ascii('Ćorić Agrar') MORA biti 'coric-agrar' "
        f"(Ć→c, razmak→-, lowercase; SM-D7/G1); dobijeno: {result!r}."
    )
    # Slug NE SME sadržati Unicode dijakritike (project-context § Slugovi: ASCII u URL-u)
    assert result.isascii(), f"Slug MORA biti čist ASCII (allow_unicode=False); {result!r}."
