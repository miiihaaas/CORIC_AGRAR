"""Story 3.4 — AC6: singleton-friendly admin (Task 9.6) — RED phase (TEA).

Verifikuje `apps/pages/admin.py`:
- SiteSettings registrovan na admin.site
- has_add_permission → False kad red postoji (singleton — nema „Add another")
- has_delete_permission → False (singleton se ne briše)
- list_display + search_fields definisani
- changelist_view REDIREKTUJE (302) na change-view jedinog objekta (singleton UX)
- change-view 200 za superuser

⛔ Admin URL-ovi MORAJU se graditi kroz reverse("admin:pages_sitesettings_*") — NIKAD
hardkodovan /admin/... ni /sr/admin/... (admin je pod i18n_patterns; SM-D6).

RED razlog: model + admin ne postoje → ImportError / NoReverseMatch
(admin:pages_sitesettings_changelist nije registrovan).

Dev NE piše testove. Pokrenuti:
    just test apps/pages/tests/test_sitesettings_admin.py -v
"""

from __future__ import annotations

import pytest
from django.contrib import admin
from django.urls import reverse

pytestmark = pytest.mark.django_db


def _get_model():
    from apps.pages.models import SiteSettings

    return SiteSettings


@pytest.fixture
def superuser(django_user_model):
    return django_user_model.objects.create_superuser(
        username="murat_tea",
        email="tea@coricagrar.rs",
        password="x-tea-pass-12345",
    )


def test_sitesettings_registered_in_admin():
    """AC6: SiteSettings je registrovan na admin.site (pojavljuje se u admin listi)."""
    SiteSettings = _get_model()
    assert SiteSettings in admin.site._registry, (
        "SiteSettings MORA biti registrovan na admin.site (@admin.register ili "
        "admin.site.register; AC6/SM-D6)."
    )


def test_has_add_permission_false_when_row_exists():
    """AC6: has_add_permission → False kad SiteSettings.objects.exists() (singleton)."""
    SiteSettings = _get_model()
    model_admin = admin.site._registry[SiteSettings]

    SiteSettings.load()  # garantuj da red postoji
    request = _fake_request()
    assert model_admin.has_add_permission(request) is False, (
        "has_add_permission MORA biti False kad red postoji (singleton — nema 'Add "
        "another'; AC6)."
    )


def test_has_delete_permission_false():
    """AC6: has_delete_permission → False (singleton se ne briše)."""
    SiteSettings = _get_model()
    model_admin = admin.site._registry[SiteSettings]
    request = _fake_request()
    obj = SiteSettings.load()
    assert model_admin.has_delete_permission(request, obj) is False, (
        "has_delete_permission MORA biti False za singleton (AC6)."
    )
    assert model_admin.has_delete_permission(request, None) is False, (
        "has_delete_permission(obj=None) MORA biti False (bulk delete iz changelist-a)."
    )


def test_list_display_and_search_fields_defined():
    """AC6: list_display + search_fields definisani (project-context.md:200)."""
    SiteSettings = _get_model()
    model_admin = admin.site._registry[SiteSettings]
    assert model_admin.list_display, (
        "ModelAdmin.list_display MORA biti definisan (project-context.md:200; AC6)."
    )
    assert model_admin.search_fields, (
        "ModelAdmin.search_fields MORA biti definisan (project-context.md:200; AC6)."
    )


def test_changelist_redirects_to_change_view(client, superuser):
    """AC6: changelist (302) REDIREKTUJE na change-view jedinog objekta (singleton UX).

    URL kroz reverse("admin:pages_sitesettings_changelist") — NE hardkodovan put (SM-D6).
    """
    SiteSettings = _get_model()
    obj = SiteSettings.load()
    client.force_login(superuser)

    changelist_url = reverse("admin:pages_sitesettings_changelist")
    expected_change_url = reverse("admin:pages_sitesettings_change", args=[obj.pk])

    response = client.get(changelist_url)
    assert response.status_code == 302, (
        f"Changelist MORA REDIREKTOVATI (302) na change-view jedinog objekta (singleton "
        f"UX; AC6/SM-D6), dobio {response.status_code}."
    )
    assert response.url.endswith(expected_change_url) or response.url == expected_change_url, (
        f"Changelist redirect MORA voditi na change-view {expected_change_url!r}, dobio "
        f"{response.url!r}."
    )


def test_change_view_returns_200(client, superuser):
    """AC6: change-view jedinog objekta → HTTP 200 za superuser (kroz reverse())."""
    SiteSettings = _get_model()
    obj = SiteSettings.load()
    client.force_login(superuser)

    change_url = reverse("admin:pages_sitesettings_change", args=[obj.pk])
    response = client.get(change_url)
    assert response.status_code == 200, (
        f"Change-view MORA biti 200 za superuser (kroz reverse(); SM-D6), dobio "
        f"{response.status_code}."
    )


def _fake_request():
    """Minimalan request stub za has_*_permission pozive (NE treba pun WSGI)."""
    from django.test import RequestFactory

    rf = RequestFactory()
    request = rf.get("/")
    return request
