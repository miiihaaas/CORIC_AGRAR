"""Story 5.1 — NOVI apps/blog/ app scaffolding + INSTALLED_APPS (TEA RED phase).

Pokriva AC5: BlogConfig.name=="apps.blog"; default_auto_field BigAutoField;
"apps.blog" u INSTALLED_APPS POSLE modeltranslation (KRITIČNO za translatable model);
dep boundary (apps/blog NE importuje products/brands/search/pages/forms — samostalan
content app, samo apps.core + Django + modeltranslation + AUTH_USER_MODEL);
manage.py check čist (0 ozbiljnih grešaka).

⚠️ GUARD: apps.blog importi UNUTAR funkcija (collection-safety). Dep-boundary test
čita izvor sa fajl-sistema (NE importuje apps.blog) → može se evaluirati i pre Dev-a
(daje čist RED kroz „direktorijum ne postoji" assertion).

TEA RED phase: SVI testovi MORAJU pasti — apps.blog NE postoji / NIJE u INSTALLED_APPS.

Refs:
- 5-1-...-admin-stub.md AC5 + Task 8.7 + SM-D1
- 5-1-interface-contract.md § 7 (settings/AppConfig)
- apps/forms/tests/test_app_config.py (precedent)
"""

from __future__ import annotations

import re
from pathlib import Path

from django.conf import settings


# AC5: BlogConfig.name == "apps.blog" (sa apps. prefiksom — Gotcha PR-1)
def test_blog_config_name_is_apps_blog():
    from apps.blog.apps import BlogConfig

    assert BlogConfig.name == "apps.blog", (
        f"BlogConfig.name MORA biti 'apps.blog' (sa apps. prefiksom — Gotcha PR-1), "
        f"dobio {BlogConfig.name!r}."
    )


# AC5: BlogConfig.default_auto_field == BigAutoField
def test_blog_config_default_auto_field():
    from apps.blog.apps import BlogConfig

    assert BlogConfig.default_auto_field == "django.db.models.BigAutoField", (
        f"BlogConfig.default_auto_field MORA biti BigAutoField, "
        f"dobio {BlogConfig.default_auto_field!r}."
    )


# AC5: "apps.blog" registrovan u INSTALLED_APPS
def test_apps_blog_in_installed_apps():
    assert "apps.blog" in settings.INSTALLED_APPS, (
        "'apps.blog' MORA biti u INSTALLED_APPS (AC5/SM-D1)."
    )


# AC5: "apps.blog" POSLE "modeltranslation" (KRITIČNO za translatable model — base.py:34)
def test_apps_blog_after_modeltranslation():
    apps_list = list(settings.INSTALLED_APPS)
    assert "apps.blog" in apps_list and "modeltranslation" in apps_list, (
        "'apps.blog' i 'modeltranslation' MORAJU biti u INSTALLED_APPS."
    )
    assert apps_list.index("apps.blog") > apps_list.index("modeltranslation"), (
        "'apps.blog' MORA biti POSLE 'modeltranslation' u INSTALLED_APPS "
        "(translatable model zahtev — base.py:34)."
    )


# AC5: dep boundary — apps/blog/ NE importuje products/brands/search/pages/forms
def test_dep_boundary_blog_does_not_import_other_domain_apps():
    """Statički grep import izvora apps/blog/ — blog koristi SAMO apps.core
    (+ Django/modeltranslation/AUTH_USER_MODEL). Import products/brands/search/pages/forms
    KRŠI invariantu (blog je samostalan content domen — SM-D1)."""
    blog_dir = Path(settings.BASE_DIR) / "apps" / "blog"
    # Guard na apps.py (app marker), NE na direktorijum — tests/ dir VEĆ postoji (TEA),
    # ali sam app (apps.py/models.py) NE postoji pre Dev-a → čist RED dok Dev ne kreira app.
    assert (blog_dir / "apps.py").exists(), (
        f"apps/blog/apps.py MORA postojati ({blog_dir / 'apps.py'}). RED: app još ne postoji."
    )

    forbidden = ("products", "brands", "search", "pages", "forms")
    pattern = re.compile(
        r"^\s*(from|import)\s+(apps\.)?(" + "|".join(forbidden) + r")\b",
        re.MULTILINE,
    )
    offenders = []
    for py in blog_dir.rglob("*.py"):
        if "tests" in py.parts:
            continue  # testovi smeju importovati šta treba
        text = py.read_text(encoding="utf-8")
        if pattern.search(text):
            offenders.append(str(py.relative_to(blog_dir)))
    assert offenders == [], (
        f"apps/blog/ NE SME importovati products/brands/search/pages/forms — dep boundary "
        f"SM-D1 (blog je samostalan content app). Prekršioci: {offenders}."
    )


# AC5: manage.py check čist (0 ozbiljnih grešaka) — app/model/translation/admin valjani
def test_manage_check_clean():
    from django.core.checks import run_checks

    errors = [e for e in run_checks() if e.is_serious()]
    assert errors == [], (
        f"manage.py check MORA biti čist (exit 0) sa registrovanim apps.blog — AC5. "
        f"Ozbiljne greške: {errors}."
    )
