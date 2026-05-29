"""Story 2.2 — Cross-app boundary regression testovi (TEA RED phase).

Pokriva AC12/AC13 — architecture.md § Architectural Boundaries (jednosmerne zavisnosti):
    core ← brands ← products ← catalog

Specifično:
- `apps.brands` NIKAD NE SME importovati `apps.products` (regression guard za 2.2).
- `apps.products` NIKAD NE SME importovati `apps.catalog` (defensive — catalog
  app još NE postoji u Story 2.2 vreme, ali ovaj test odmah uhvati prvu boundary
  violation kad Epic 3+ uvede catalog).

Pattern: AST-based static check — parsira sve `.py` fajlove u target direktorijumu
i asertuje da nijedan `import X` ili `from X import ...` ne počinje zabranjenim
prefiksom. Pristup je deterministički, zero-runtime-cost, i radi bez Django setup-a.

Lokacija fajla: `tests/integration/test_app_boundaries.py` (per project-context.md
§ Test organization — cross-app boundary testovi NISU per-app testovi nego pripadaju
canonical integration dir-u).

Pokrenuti sa:
    uv run pytest tests/integration/test_app_boundaries.py -v
"""

from __future__ import annotations

import ast
from pathlib import Path

# Repo root = parent direktorijum od tests/ folder-a (2 levels up od ovog fajla)
REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _assert_no_import(scan_dir: Path, forbidden_prefix: str) -> None:
    """Walk sve `.py` fajlove pod scan_dir (excl. tests/) i asertuj da nijedan
    `import X` ili `from X import ...` ne počinje sa `forbidden_prefix`.

    Raises:
        AssertionError: ako bilo koji fajl import-uje modul koji počinje sa
        zabranjenim prefiksom — error message lista sve violations.
    """
    violations: list[str] = []
    py_files = list(scan_dir.rglob("*.py"))

    for py_file in py_files:
        # Skip per-app testove iz scan-a — testovi mogu legitimno da import-uju
        # cross-app modele (npr. apps.products.tests koristi apps.brands.models
        # za FK chain setup), ali to nije production-code boundary violation.
        if "tests" in py_file.parts:
            continue

        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"))
        except SyntaxError as exc:
            # Defensive: nepotpun fajl tokom WIP staje test sa jasnim msg
            violations.append(f"{py_file}: SyntaxError parsing — {exc}")
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith(forbidden_prefix):
                        violations.append(
                            f"{py_file}: import {alias.name} — boundary violation"
                        )
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.module.startswith(forbidden_prefix):
                    violations.append(
                        f"{py_file}: from {node.module} — boundary violation"
                    )

    assert not violations, (
        f"App boundary violated (forbidden prefix: {forbidden_prefix!r}):\n"
        + "\n".join(f"  - {v}" for v in violations)
    )


# =============================================================================
# AC12 — apps.brands NE SME importovati apps.products
# =============================================================================


def test_brands_does_not_import_products():
    """Story 2.2 AC12 / architecture.md § Zabranjene zavisnosti.

    apps.brands NIKAD NE SME importovati apps.products. Reverse access kroz
    `brand.products.all()` (related_name FK reverse) je SVE što brands sloj treba.

    Regression guard: future Stories (2.6 Brand listing, 8.4 Brand admin) mogu
    biti iskušanje da `from apps.products.models import Product` u apps/brands.
    Ovaj test odmah uhvati takvu liniju.
    """
    brands_dir = REPO_ROOT / "apps" / "brands"
    assert brands_dir.exists(), (
        f"Story 2.1 prerequisite missing — apps/brands dir not found at {brands_dir}"
    )
    _assert_no_import(brands_dir, "apps.products")


# =============================================================================
# AC13 I8 extension — apps.products NE SME importovati apps.catalog (defensive)
# =============================================================================


def test_products_does_not_import_catalog():
    """architecture.md dependency chain: core ← brands ← products ← catalog.

    apps.products NIKAD NE SME importovati apps.catalog. Defensive: catalog app
    još NE postoji u Story 2.2 (uvodi se u Epic 2.6+), pa ova provera prolazi
    trivijalno za sada — ali ostaje kao regression guard čim catalog uđe u repo.

    Pattern (I8 extension): 1-line extension postojećeg AST walk pristupa.
    Kada `apps.catalog` ne postoji (Story 2.2 vreme), test PASS jer forbidden
    prefix nije pronađen ni u jednoj import-u. Kada Epic 3+ uvede `apps.catalog`,
    postojeći test odmah uhvati svaku `from apps.catalog import ...` liniju.
    """
    products_dir = REPO_ROOT / "apps" / "products"
    if not products_dir.exists():
        # Defensive: ako apps/products još ne postoji (RED phase pre Dev implementacije),
        # test prolazi trivijalno. Posle Dev GREEN phase, ovaj guard počinje da pokriva
        # apps/products production code.
        return
    _assert_no_import(products_dir, "apps.catalog")
