"""Story 7.1 — AC6: singleton-friendly CookiePolicyAdmin (TranslationAdmin) (TEA RED).

Pokriva (mirror SiteSettingsAdmin):
- CookiePolicy registrovan na admin.site; CookiePolicyAdmin je TranslationAdmin subclass.
- has_add_permission → False kad red postoji; True kad je tabela prazna.
- has_delete_permission(obj) / (None) → False.
- changelist_view REDIREKTUJE (302) na change-view jedinog reda; kreira pk=1 kad prazno.
- change-view 200 za superuser; per-locale title_sr/title_hu/... u formi (TranslationAdmin).

⛔ Admin URL-ovi kroz reverse("admin:gdpr_cookiepolicy_*") — NIKAD hardkodovan
/admin/... ni /sr/admin/... (admin pod i18n_patterns; SM-D10).

⚠️ COLLECTION-SAFETY: apps.gdpr importi + admin registry pristup UNUTAR test body-ja
— apps.gdpr NE postoji → KeyError/ImportError per-test (RED).

Refs:
- 7-1-...-admin.md AC6 + SM-D6/D10
- apps/pages/tests/test_sitesettings_admin.py (mirror)
"""

from __future__ import annotations

import pytest
from django.contrib import admin
from django.test import RequestFactory
from django.urls import reverse

pytestmark = pytest.mark.django_db


def _get_model():
    from apps.gdpr.models import CookiePolicy

    return CookiePolicy


def _fake_request():
    return RequestFactory().get("/")


# AC6: CookiePolicy registrovan na admin.site
def test_cookiepolicy_registered_in_admin():
    CookiePolicy = _get_model()
    assert CookiePolicy in admin.site._registry, (
        "CookiePolicy MORA biti registrovan na admin.site (@admin.register; AC6/SM-D6)."
    )


# AC6: CookiePolicyAdmin je TranslationAdmin subclass (per-locale title/body tabovi)
def test_admin_is_translation_admin():
    from modeltranslation.admin import TranslationAdmin

    CookiePolicy = _get_model()
    model_admin = admin.site._registry[CookiePolicy]
    assert isinstance(model_admin, TranslationAdmin), (
        "CookiePolicyAdmin MORA biti TranslationAdmin (NE plain ModelAdmin) — "
        "modeltranslation auto-grupiše title/body po jeziku (AC6/SM-D6)."
    )


# AC6: has_add_permission → False kad red postoji (singleton — nema „Add another")
def test_has_add_permission_false_when_row_exists():
    CookiePolicy = _get_model()
    model_admin = admin.site._registry[CookiePolicy]
    CookiePolicy.load()  # garantuj da red postoji
    assert model_admin.has_add_permission(_fake_request()) is False, (
        "has_add_permission MORA biti False kad red postoji (singleton; AC6)."
    )


# AC6: has_add_permission → True/enabled kad je tabela prazna (not exists())
def test_has_add_permission_true_when_table_empty():
    CookiePolicy = _get_model()
    model_admin = admin.site._registry[CookiePolicy]
    CookiePolicy.objects.all().delete()  # QuerySet path zaobilazi instance guard
    assert model_admin.has_add_permission(_fake_request()) is True, (
        "has_add_permission MORA biti True kad je tabela prazna (not exists() — AC6)."
    )


# AC6: has_delete_permission → False (singleton se ne briše)
def test_has_delete_permission_false():
    CookiePolicy = _get_model()
    model_admin = admin.site._registry[CookiePolicy]
    obj = CookiePolicy.load()
    assert model_admin.has_delete_permission(_fake_request(), obj) is False, (
        "has_delete_permission(obj) MORA biti False za singleton (AC6)."
    )
    assert model_admin.has_delete_permission(_fake_request(), None) is False, (
        "has_delete_permission(obj=None) MORA biti False (bulk delete iz changelist-a)."
    )


# AC6: changelist (302) REDIREKTUJE na change-view jedinog reda (kroz reverse)
def test_changelist_redirects_to_change_view(client, superuser):
    CookiePolicy = _get_model()
    obj = CookiePolicy.load()
    client.force_login(superuser)

    changelist_url = reverse("admin:gdpr_cookiepolicy_changelist")
    expected_change_url = reverse("admin:gdpr_cookiepolicy_change", args=[obj.pk])

    response = client.get(changelist_url)
    assert response.status_code == 302, (
        f"Changelist MORA REDIREKTOVATI (302) na change-view jedinog reda (singleton UX; "
        f"AC6/SM-D6), dobio {response.status_code}."
    )
    assert response.url == expected_change_url, (
        f"Changelist redirect MORA voditi TAČNO na change-view {expected_change_url!r}, "
        f"dobio {response.url!r} (egzaktna jednakost — pogrešan redirect target NE SME proći)."
    )


# AC6: changelist kreira pk=1 kad je tabela prazna pa redirektuje (load() get_or_create)
def test_changelist_creates_row_when_empty_then_redirects(client, superuser):
    CookiePolicy = _get_model()
    CookiePolicy.objects.all().delete()
    client.force_login(superuser)

    response = client.get(reverse("admin:gdpr_cookiepolicy_changelist"))
    assert response.status_code == 302, (
        "Changelist na praznoj tabeli MORA load() get_or_create(pk=1) pa REDIREKT (302) "
        f"na change-view (AC6), dobio {response.status_code}."
    )
    assert CookiePolicy.objects.filter(pk=1).exists(), (
        "Changelist MORA materijalizovati pk=1 red kroz load() (AC6)."
    )


# AC6: change-view jedinog reda → HTTP 200 za superuser (TranslationAdmin renderuje)
def test_change_view_returns_200(client, superuser):
    CookiePolicy = _get_model()
    obj = CookiePolicy.load()
    client.force_login(superuser)

    change_url = reverse("admin:gdpr_cookiepolicy_change", args=[obj.pk])
    response = client.get(change_url)
    assert response.status_code == 200, (
        f"Change-view MORA biti 200 za superuser (TranslationAdmin per-locale title/body "
        f"bez greške; AC6), dobio {response.status_code}."
    )


# AC6: change-view forma sadrži per-locale polja (title_sr/title_hu/body_sr/... — TranslationAdmin)
def test_change_view_renders_per_locale_fields(client, superuser):
    CookiePolicy = _get_model()
    obj = CookiePolicy.load()
    client.force_login(superuser)

    response = client.get(reverse("admin:gdpr_cookiepolicy_change", args=[obj.pk]))
    assert response.status_code == 200
    html = response.content.decode("utf-8")
    # TranslationAdmin renderuje per-locale form polja (name="title_sr", "body_hu", ...)
    for field in ("title_sr", "title_hu", "title_en", "body_sr"):
        assert f'name="{field}"' in html, (
            f"Change-view forma MORA imati per-locale polje name=\"{field}\" "
            f"(TranslationAdmin; AC6)."
        )


# AC6: list_display definisan (project-context.md:200)
def test_list_display_defined():
    CookiePolicy = _get_model()
    model_admin = admin.site._registry[CookiePolicy]
    assert model_admin.list_display, (
        "CookiePolicyAdmin.list_display MORA biti definisan (project-context.md:200; AC6)."
    )


# AC6: run_checks bez admin.E* grešaka (admin valjan)
def test_admin_no_errors():
    from django.core.checks import run_checks

    errors = [e for e in run_checks() if e.is_serious() and e.id.startswith("admin.")]
    assert errors == [], (
        f"Admin registracija NE SME imati admin.E* greške (AC6). Greške: {errors}."
    )
