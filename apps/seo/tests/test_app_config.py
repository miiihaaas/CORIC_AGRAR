"""Story 6.1 — apps/seo/ app scaffolding + INSTALLED_APPS registracija (TEA RED phase).

Pokriva AC5: SeoConfig.name == "apps.seo"; "apps.seo" u INSTALLED_APPS POSLE
modeltranslation + domain app-ova + apps.blog (SM-D9); seo NE FK-uje receiving
modele direktno (GFK loose — apps/seo/models.py importuje SAMO core/contenttypes/
Django/modeltranslation).

⚠️ GUARD: apps.seo importi UNUTAR funkcija (collection-safety).
TEA RED phase: SVI testovi MORAJU pasti — apps.seo NE postoji / NIJE u INSTALLED_APPS.

Refs:
- 6-1-...-admin.md AC5 + Task 7.9 + SM-D1/D9
- apps/blog/apps.py (SeoConfig mirror)
"""

from __future__ import annotations


# AC5: SeoConfig.name == "apps.seo" (sa apps. prefiksom — Gotcha PR-1)
def test_seoconfig_name():
    from apps.seo.apps import SeoConfig

    assert SeoConfig.name == "apps.seo", (
        "SeoConfig.name MORA biti 'apps.seo' (sa apps. prefiksom — Gotcha PR-1; AC5)."
    )
    assert SeoConfig.default_auto_field == "django.db.models.BigAutoField"


# AC5: "apps.seo" u INSTALLED_APPS
def test_seo_in_installed_apps():
    from django.conf import settings

    assert "apps.seo" in settings.INSTALLED_APPS, (
        "'apps.seo' MORA biti u INSTALLED_APPS (AC5)."
    )


# AC5/SM-D9: apps.seo POSLE modeltranslation i POSLE apps.blog (admin reg redosled)
def test_seo_installed_after_modeltranslation_and_blog():
    from django.conf import settings

    apps_list = list(settings.INSTALLED_APPS)
    assert "apps.seo" in apps_list, "'apps.seo' nije u INSTALLED_APPS (AC5)."
    seo_idx = apps_list.index("apps.seo")
    assert seo_idx > apps_list.index("modeltranslation"), (
        "apps.seo MORA biti POSLE modeltranslation (translatable model; SM-D9)."
    )
    assert seo_idx > apps_list.index("apps.blog"), (
        "apps.seo MORA biti POSLE apps.blog (generic inline importuje njihove admin-e; SM-D9)."
    )


# AC5: seo NE FK-uje receiving modele direktno — GFK je loose.
# AST assert: apps/seo/models.py importuje SAMO core + contenttypes + Django + modeltranslation
def test_seo_models_does_not_import_receiving_models():
    import ast
    import inspect

    import apps.seo.models as seo_models

    source = inspect.getsource(seo_models)
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.add(node.module)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                imported_modules.add(alias.name)

    forbidden = {"apps.products", "apps.brands", "apps.blog", "apps.pages"}
    leaked = {
        m for m in imported_modules if any(m == f or m.startswith(f + ".") for f in forbidden)
    }
    assert leaked == set(), (
        f"apps/seo/models.py NE SME FK-ovati/importovati receiving app modele "
        f"(GFK je loose — SeoMeta FK-uje SAMO ContentType; AC5). Procurelo: {leaked}."
    )
