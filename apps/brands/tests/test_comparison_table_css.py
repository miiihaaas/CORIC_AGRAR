"""Story 2.12 — comparison-table.css static asset tests (RED phase, AC6).

Pokriva: comparison-table.css coric-comparison-table BEM selektore, main.css @import,
samo var(--token) vrednosti (0 magic hex), svi BEM klasi coric- prefiks, svi
referencirani tokeni definisani u tokens.css.

Mirror Story 2-11 test_subcategory_listing_static_assets.py style.

Pokrenuti sa:
    docker compose -f compose/local.yml run --rm django uv run pytest \\
        apps/brands/tests/test_comparison_table_css.py -v

Refs:
- 2-12-hzm-radne-masine-tulip-mix-prikolice-strane.md (AC6, Subtask 8.7)
- 2-12-interface-contract.md (§ 4 CSS)
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from django.conf import settings


def _static_root() -> Path:
    base = Path(settings.BASE_DIR)
    for c in (base / "static", base.parent / "static"):
        if (c / "css" / "main.css").exists():
            return c
    for d in getattr(settings, "STATICFILES_DIRS", []):
        p = Path(d)
        if (p / "css" / "main.css").exists():
            return p
    return base / "static"


def _read(rel: str) -> str:
    path = _static_root() / rel
    if not path.exists():
        pytest.fail(
            f"Fajl {rel!r} ne postoji ({path}). Dev MORA kreirati ga per AC6 "
            f"(RED phase — fajl još ne postoji)."
        )
    return path.read_text(encoding="utf-8")


def test_comparison_table_css_imported_in_main_css():
    """AC6: main.css @import-uje comparison-table.css (POSLE breadcrumb.css)."""
    main = _read("css/main.css")
    assert "components/comparison-table.css" in main, (
        "main.css MORA imati '@import url(\"./components/comparison-table.css\");' "
        "(POSLE breadcrumb.css)."
    )
    assert "@import" in main


def test_comparison_table_css_has_bem_selectors():
    """AC6: comparison-table.css definiše coric-comparison-table BEM selektore."""
    css = _read("css/components/comparison-table.css")
    for selector in (
        ".coric-comparison-table",
        ".coric-comparison-table__scroll",
        ".coric-comparison-table__key",
        ".coric-comparison-table__value",
    ):
        assert selector in css, (
            f"comparison-table.css MORA definisati selektor {selector!r} (AC6)."
        )


def test_comparison_table_css_uses_only_var_tokens():
    """AC6: NEMA magic hex/px vrednosti — sve kroz var(--token).

    Allow keyword vrednosti (white/transparent/none/auto/0/100%) + var() reference.
    Zabranjeno: bukvalan hex (#rrggbb) u declaration vrednostima.
    """
    css = _read("css/components/comparison-table.css")

    # Zabranjen bukvalan hex literal (magic boja umesto tokena)
    hex_literals = re.findall(r"#[0-9a-fA-F]{3,8}\b", css)
    assert not hex_literals, (
        f"comparison-table.css NE SME imati magic hex literale (sve boje kroz "
        f"var(--token)), pronađeno: {hex_literals!r}."
    )


def test_comparison_table_css_has_coric_prefix_on_all_classes():
    """AC6: svi BEM klasi imaju coric- prefiks (nijedan unprefiksiran custom selektor)."""
    css = _read("css/components/comparison-table.css")

    # Klasni selektori (.foo) — ignoriši pseudo (:hover) i kombinatore
    class_selectors = set(re.findall(r"\.([a-zA-Z][\w-]*)", css))
    non_coric = {c for c in class_selectors if not c.startswith("coric-")}
    assert not non_coric, (
        f"Svi klasni selektori u comparison-table.css MORAJU imati 'coric-' prefiks, "
        f"pronađeni bez prefiksa: {sorted(non_coric)!r}."
    )


def test_comparison_table_css_tokens_all_defined_in_tokens_file():
    """AC6: svaki var(--token) referenciran u comparison-table.css definisan u tokens.css."""
    comparison_css = _read("css/components/comparison-table.css")
    tokens_css = _read("css/tokens.css")

    defined = set(re.findall(r"(--[a-z0-9-]+)\s*:", tokens_css))
    referenced = set(re.findall(r"var\(\s*(--[a-z0-9-]+)", comparison_css))

    undefined = referenced - defined
    assert not undefined, (
        f"comparison-table.css referencira tokene koji NISU definisani u tokens.css: "
        f"{sorted(undefined)}. Dev MORA koristiti postojeće tokene (NE dodavati nove — "
        f"tokens.css je Story 1-5 deliverable)."
    )


def test_no_cdn_reference_in_comparison_table_css():
    """AC6: NEMA CDN referenci (sve lokalno servirano)."""
    css = _read("css/components/comparison-table.css")
    for cdn in ("http://", "https://", "//cdn"):
        assert cdn not in css, (
            f"comparison-table.css NE SME imati CDN/external referencu ({cdn!r})."
        )
