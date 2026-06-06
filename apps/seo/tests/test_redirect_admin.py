"""Story 6.4 — RedirectAdmin (TEA RED phase, AC3 + AC5-kroz-admin).

Pokriva:
- AC3: `admin.site.is_registered(Redirect)`; list_display/list_filter/search_fields/
  list_editable konfigurisani; superuser changelist GET 200.
- AC5: add-form POST sa nevalidnim new_path (`https://evil.com`) → form invalid
  (open-redirect guard kroz admin ModelForm full_clean).
- AC3/AC4: list_editable round-trip — kreiraj aktivno pravilo → GET 301 →
  changelist POST is_active=False → re-fetch DB is_active False → GET više NIJE 301.

`superuser` fixture iz conftest.py (django_user_model.create_superuser).

Refs:
- 6-4-redirect-manager-301.md AC3 + Task 5/6.5 + SM-D2
- 6-4-interface-contract.md § 3. Admin
"""

from __future__ import annotations

import pytest
from django.contrib import admin
from django.urls import reverse

pytestmark = pytest.mark.django_db


# AC3: RedirectAdmin registrovan
def test_redirect_admin_registered():
    from apps.seo.models import Redirect

    assert admin.site.is_registered(Redirect), (
        "Redirect MORA biti registrovan u admin.site (@admin.register(Redirect) — AC3)."
    )


# AC3: list_display / list_filter / search_fields / list_editable konfigurisani
def test_redirect_admin_options():
    from apps.seo.models import Redirect

    model_admin = admin.site._registry[Redirect]
    assert tuple(model_admin.list_display) == ("old_path", "new_path", "is_active", "created_at"), (
        "RedirectAdmin.list_display MORA biti (old_path, new_path, is_active, created_at) — AC3."
    )
    assert "is_active" in tuple(model_admin.list_filter), (
        "RedirectAdmin.list_filter MORA imati is_active (AC3)."
    )
    assert tuple(model_admin.search_fields) == ("old_path", "new_path"), (
        "RedirectAdmin.search_fields MORA biti (old_path, new_path) — AC3."
    )
    assert "is_active" in tuple(model_admin.list_editable), (
        "RedirectAdmin.list_editable MORA imati is_active (changelist toggle deaktivacije — AC3)."
    )


# AC3: superuser changelist GET → 200
def test_changelist_get_200(client, superuser):
    from apps.seo.models import Redirect

    Redirect.objects.create(old_path="/sr/a/", new_path="/sr/b/")
    client.force_login(superuser)
    url = reverse("admin:seo_redirect_changelist")
    response = client.get(url)
    assert response.status_code == 200, (
        f"superuser changelist GET MORA biti 200, dobio {response.status_code} (AC3)."
    )


# AC5 (kroz admin): add-form POST sa nevalidnim new_path → form invalid (open-redirect guard)
def test_admin_add_rejects_open_redirect(client, superuser):
    from apps.seo.models import Redirect

    client.force_login(superuser)
    url = reverse("admin:seo_redirect_add")
    response = client.post(
        url,
        data={"old_path": "/sr/x/", "new_path": "https://evil.com", "is_active": "on"},
    )
    # form invalid → 200 (re-render sa greškom), NE 302 (save+redirect na changelist)
    assert response.status_code == 200, (
        "Admin add sa new_path='https://evil.com' MORA re-renderovati form (200) sa greškom, "
        f"NE save+redirect (302). Dobio {response.status_code} (open-redirect guard — AC5)."
    )
    assert not Redirect.objects.filter(new_path="https://evil.com").exists(), (
        "Nevalidan open-redirect new_path NE SME biti perzistiran kroz admin (AC5)."
    )


# AC3/AC5: add-form POST sa VALIDNIM pravilom → 302 (save+redirect) + red u DB
def test_admin_add_persists_valid_rule(client, superuser):
    from apps.seo.models import Redirect

    client.force_login(superuser)
    url = reverse("admin:seo_redirect_add")
    response = client.post(
        url,
        data={"old_path": "/sr/stara/", "new_path": "/sr/nova/", "is_active": "on"},
    )
    # validan rule → 302 (save + redirect na changelist), NE 200 (re-render sa greškom)
    assert response.status_code == 302, (
        "Admin add sa validnim old_path/new_path MORA save-ovati + redirect-ovati na "
        f"changelist (302), dobio {response.status_code} (zaključava da admin ModelForm "
        "save put radi end-to-end, ne samo .objects.create() — AC3/AC5)."
    )
    assert Redirect.objects.filter(
        old_path="/sr/stara/", new_path="/sr/nova/", is_active=True
    ).exists(), (
        "Validan rule unet kroz admin add-form MORA biti perzistiran u DB "
        "(admin ModelForm → full_clean → save end-to-end — AC3/AC5)."
    )


# AC3/AC4: list_editable round-trip — changelist POST deaktivira → middleware NE redirektuje
def test_list_editable_deactivation_stops_redirect(client, superuser):
    from apps.seo.models import Redirect
    from django.test import Client

    r = Redirect.objects.create(old_path="/sr/stara/", new_path="/sr/nova/", is_active=True)

    # pre-deaktivacije: aktivno pravilo → 301
    pre = Client().get("/sr/stara/")
    assert pre.status_code == 301, (
        "Pre deaktivacije GET /sr/stara/ MORA biti 301 (baseline — AC4)."
    )

    # superuser POST na changelist sa is_active OFF (list_editable formset save)
    client.force_login(superuser)
    changelist_url = reverse("admin:seo_redirect_changelist")
    post_data = {
        "form-TOTAL_FORMS": "1",
        "form-INITIAL_FORMS": "1",
        "form-MIN_NUM_FORMS": "0",
        "form-MAX_NUM_FORMS": "1000",
        "form-0-id": str(r.pk),
        # is_active checkbox NIJE u POST → BooleanField=False (deaktivirano)
        "_save": "Save",
    }
    response = client.post(changelist_url, data=post_data)
    assert response.status_code == 302, (
        "changelist list_editable save MORA biti 302 (save-and-redirect na changelist), "
        f"dobio {response.status_code} — precizan assert da skriveni 403/500 ne prođe (AC3)."
    )

    r.refresh_from_db()
    assert r.is_active is False, (
        "changelist list_editable POST (bez is_active checkbox-a) MORA deaktivirati pravilo "
        "(is_active=False u DB — AC3/AC4)."
    )

    # posle deaktivacije: middleware vidi is_active=False → NIJE 301 (AC4)
    post = Client().get("/sr/stara/")
    assert post.status_code != 301, (
        "Posle admin-deaktivacije kroz changelist, GET /sr/stara/ NE SME biti 301 "
        "(middleware filtrira is_active=True — AC3/AC4)."
    )
