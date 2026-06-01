"""Story 4.1 — AC3 NOVI app scaffolding + INSTALLED_APPS + dep boundary (TEA RED phase).

Pokriva AC3: FormsConfig.name=="apps.forms"; default_auto_field BigAutoField;
„apps.forms" u INSTALLED_APPS POSLE domain app-ova; dep boundary — apps/forms/
NIGDE ne importuje products/brands/search/catalog/blog (samo apps.core + Django/anymail).

TEA RED phase: SVI testovi MORAJU pasti — apps.forms ne postoji, NIJE u INSTALLED_APPS.

Refs:
- 4-1-lead-model-smtp-setup.md AC3 + Task 8.4 + SM-D1/D3a
- 4-1-interface-contract.md § 1 (apps.py) + § 8 (INSTALLED_APPS) + Project Structure Notes
- mirror apps/search/tests/test_app_config.py
"""

from __future__ import annotations

import re
from pathlib import Path

from django.conf import settings


# AC3: FormsConfig.name == "apps.forms" (sa prefiksom)
def test_forms_config_name_is_apps_forms():
    from apps.forms.apps import FormsConfig

    assert FormsConfig.name == "apps.forms", (
        f"FormsConfig.name mora biti 'apps.forms' (sa apps. prefiksom), "
        f"dobio: {FormsConfig.name!r}."
    )


# AC3: FormsConfig.default_auto_field == BigAutoField
def test_forms_config_default_auto_field_is_bigautofield():
    from apps.forms.apps import FormsConfig

    assert FormsConfig.default_auto_field == "django.db.models.BigAutoField", (
        f"FormsConfig.default_auto_field mora biti BigAutoField, "
        f"dobio: {FormsConfig.default_auto_field!r}."
    )


# AC3: "apps.forms" registrovan u INSTALLED_APPS
def test_apps_forms_in_installed_apps():
    assert "apps.forms" in settings.INSTALLED_APPS, (
        "'apps.forms' MORA biti u INSTALLED_APPS (AC3/SM-D1)."
    )


# AC3: "apps.forms" POSLE domain app-ova (forms je samostalan top-level)
def test_apps_forms_after_domain_apps():
    apps_list = list(settings.INSTALLED_APPS)
    assert "apps.forms" in apps_list, "'apps.forms' MORA biti u INSTALLED_APPS."
    assert apps_list.index("apps.forms") > apps_list.index("apps.products"), (
        "'apps.forms' MORA biti POSLE 'apps.products' u INSTALLED_APPS (forms samostalan "
        "top-level — POSLE domain app-ova)."
    )


# AC3: dep boundary — apps/forms/ NIGDE ne importuje brands/search/catalog/blog;
# products SAMO u views.py (READ-ONLY izuzetak — 4.3 SM-D6, dokumentovan u project-context.md)
def test_dep_boundary_forms_does_not_import_other_domain_apps():
    """Statički grep import izvora apps/forms/ — forms koristi SAMO apps.core
    (+ Django/anymail). Import brands/search/catalog/blog KRŠI invariantu
    (architecture.md:739; project-context.md:665; SM-D3a). `products` je dozvoljen
    SAMO u views.py kao READ-ONLY view-layer query (4.3 SM-D6 — mirror brands→products
    2.6 SM-D16 izuzetka; NEMA .save/.create, NEMA FK)."""
    forms_dir = Path(settings.BASE_DIR) / "apps" / "forms"
    assert forms_dir.exists(), (
        f"apps/forms/ direktorijum MORA postojati ({forms_dir}). RED: app još ne postoji."
    )

    forbidden = ("brands", "search", "catalog", "blog")
    # match: `from apps.brands...` / `import apps.brands` (i bare `import brands` itd.)
    pattern = re.compile(
        r"^\s*(from|import)\s+(apps\.)?(" + "|".join(forbidden) + r")\b",
        re.MULTILINE,
    )
    # products import je dozvoljen SAMO u views.py (4.3 SM-D6 READ-ONLY izuzetak)
    products_pattern = re.compile(
        r"^\s*(from|import)\s+(apps\.)?products\b",
        re.MULTILINE,
    )
    offenders = []
    for py in forms_dir.rglob("*.py"):
        if "tests" in py.parts:
            continue  # testovi smeju importovati šta treba
        text = py.read_text(encoding="utf-8")
        if pattern.search(text):
            offenders.append(str(py.relative_to(forms_dir)))
        if products_pattern.search(text) and py.name != "views.py":
            offenders.append(str(py.relative_to(forms_dir)))
    assert offenders == [], (
        f"apps/forms/ NE SME importovati brands/search/catalog/blog (bilo gde) ni products "
        f"(van views.py) — dep boundary SM-D3a + 4.3 SM-D6. Prekršioci: {offenders}."
    )


# AC3 (SM-D6 READ-ONLY invarijanta): forms→products je SAMO read-only query-layer —
# NIGDE u apps/forms/ NE SME postojati .save()/.create() na Product instanci/manageru
def test_dep_boundary_forms_does_not_write_to_product():
    """Statički grep — forms→products izuzetak je READ-ONLY (SM-D6): NEMA `Product.objects.create`,
    NEMA `Product(...).save()`, NEMA `.save()`/`.create()` na Product instanci. Lead.data čuva slug-u-JSON,
    NE FK. Ovo zaključava invarijantu da forms ne piše u products domen (mirror brands→products 2.6 SM-D16)."""
    forms_dir = Path(settings.BASE_DIR) / "apps" / "forms"
    write_patterns = (
        re.compile(r"Product\.objects\.create\b"),
        re.compile(r"Product\.objects\.bulk_create\b"),
        re.compile(r"Product\([^)]*\)\.save\b"),
        re.compile(r"\bproduct\.save\("),
        re.compile(r"\bproduct\.create\("),
        re.compile(r"\bproduct\.delete\("),
    )
    offenders = []
    for py in forms_dir.rglob("*.py"):
        if "tests" in py.parts:
            continue
        text = py.read_text(encoding="utf-8")
        for pat in write_patterns:
            if pat.search(text):
                offenders.append(f"{py.relative_to(forms_dir)} :: {pat.pattern}")
    assert offenders == [], (
        f"apps/forms/ forms→products izuzetak je READ-ONLY (SM-D6) — NE SME pozivati "
        f".save()/.create()/.delete() na Product. Prekršioci: {offenders}."
    )
