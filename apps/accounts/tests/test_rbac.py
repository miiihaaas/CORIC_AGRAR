"""Story 8.2 — User Accounts + RBAC (Superadmin / Editor Groups) — TEA RED phase.

Pokriva svih 14 AC sigurnosno-kritične RBAC FOUNDATION story:
- permissions.py: GROUP_SUPERADMIN/GROUP_EDITOR konstante + EDITOR_CONTENT_MODELS allowlist (15 modela).
- IsSuperadminMixin / IsEditorMixin (LoginRequiredMixin + UserPassesTestMixin, raise_exception=True).
- post_migrate handler sync_rbac_groups → kreira Superadmin+Editor grupe, dodeljuje Editor CRUD perms
  TAČNO za 15 content modela; idempotentno; NIKAD auth/admin/infra perms (AC6 CRITICAL).
- CustomUserAdmin re-register + self-escalation hardening (AC13); Editor 403 na auth.User admin (AC8).
- AC14 fail-closed dokaz na REALNOM throwaway view-u kroz urlconf override.

────────────────────────────────────────────────────────────────────────────────
COLLECTION-SAFETY (KRITIČNO — RED faza):
Sve `apps.accounts.permissions` importe radimo UNUTAR funkcija (lazy), NIKAD na
module-level. Razlog: u RED fazi `apps/accounts/permissions.py` NE postoji još →
module-level import bi ABORT-ovao collection celog fajla (ImportError) i sakrio sve
ostale RED failure-e. Lazy import → svaki test fail-uje pojedinačno (pravi RED).

Test-view klase za AC14 se definišu UNUTAR `_editor_view_class()` / `_superadmin_view_class()`
factory-ja (lazy import mixina) — bez factory-ja, top-level `class X(IsEditorMixin)` bi
takođe abort-ovao collection dok mixin ne postoji.

GROUP/PERMISIJE NAPOMENA (G-1): grupe kreira `sync_rbac_groups` post_migrate handler
tokom test-DB setup-a. Dok handler NE postoji (RED), grupe NEĆE postojati → group/perm
testovi padaju ispravno. Idempotency test poziva handler DIREKTNO (lazy import).

Refs:
- 8-2-user-accounts-rbac-superadmin-editor-groups.md (AC1–AC14, SM-D1..D17, G-1..G-15)
- 8-2-interface-contract.md
"""

from __future__ import annotations

import inspect

import pytest
from django.contrib.auth import get_user_model
from django.test import Client, override_settings
from django.urls import path, reverse

pytestmark = pytest.mark.django_db


# ──────────────────────────────────────────────────────────────────────────────
# Helpers (lazy — kreiraju usere/grupe kroz get_user_model; collection-safe)
# ──────────────────────────────────────────────────────────────────────────────
def _make_superuser(email="super@coricagrar.rs", username="superuser"):
    User = get_user_model()
    return User.objects.create_user(
        username=username, email=email, password="X", is_staff=True, is_superuser=True
    )


def _make_editor(email="editor@coricagrar.rs", username="editoruser"):
    """Editor = is_staff=True (SM-D11 — mora da uđe u admin) + član Editor grupe, NE superuser.

    Grupa Editor se kreira post_migrate handler-om — u RED fazi NE postoji, pa
    `Group.objects.get(name="Editor")` baca → test fail-uje ispravno.
    """
    from django.contrib.auth.models import Group

    User = get_user_model()
    user = User.objects.create_user(
        username=username, email=email, password="X", is_staff=True, is_superuser=False
    )
    editor_group = Group.objects.get(name="Editor")
    user.groups.add(editor_group)
    return user


def _make_plain_staff(email="plain@coricagrar.rs", username="plainstaff"):
    """Autentifikovan staff koji NIJE ni Editor ni superuser — non-group (AC14 negativni slučaj)."""
    User = get_user_model()
    return User.objects.create_user(
        username=username, email=email, password="X", is_staff=True, is_superuser=False
    )


def _call_sync_rbac():
    """Pozovi sync_rbac_groups DIREKTNO sa AccountsConfig sender-om (idempotency test)."""
    from django.apps import apps as django_apps

    from apps.accounts.permissions import sync_rbac_groups

    sender = django_apps.get_app_config("accounts")
    sync_rbac_groups(sender=sender)


# ══════════════════════════════════════════════════════════════════════════════
# AC14 — throwaway test-only view-ovi + urlconf override (REALAN request/response)
# ══════════════════════════════════════════════════════════════════════════════
def _editor_view_class():
    """Factory: View klasa gated IsEditorMixin-om (lazy import — collection-safe)."""
    from django.http import HttpResponse
    from django.views import View

    from apps.accounts.permissions import IsEditorMixin

    class _EditorGatedView(IsEditorMixin, View):
        def get(self, request, *args, **kwargs):
            return HttpResponse("editor-ok")

    return _EditorGatedView


def _superadmin_view_class():
    """Factory: View klasa gated IsSuperadminMixin-om (lazy import — collection-safe)."""
    from django.http import HttpResponse
    from django.views import View

    from apps.accounts.permissions import IsSuperadminMixin

    class _SuperadminGatedView(IsSuperadminMixin, View):
        def get(self, request, *args, **kwargs):
            return HttpResponse("superadmin-ok")

    return _SuperadminGatedView


# ──────────────────────────────────────────────────────────────────────────────
# AC1 — Group konstante + permissions.py postoji
# ──────────────────────────────────────────────────────────────────────────────
def test_ac1_group_name_constants_exist_and_exact():
    """AC1/SM-D5: permissions.py izvozi GROUP_SUPERADMIN=='Superadmin' + GROUP_EDITOR=='Editor'."""
    from apps.accounts.permissions import GROUP_EDITOR, GROUP_SUPERADMIN

    assert GROUP_SUPERADMIN == "Superadmin", (
        f"GROUP_SUPERADMIN MORA biti 'Superadmin' (single-source naziv — SM-D5), dobio {GROUP_SUPERADMIN!r}."
    )
    assert GROUP_EDITOR == "Editor", (
        f"GROUP_EDITOR MORA biti 'Editor' (single-source naziv — SM-D5), dobio {GROUP_EDITOR!r}."
    )


# ──────────────────────────────────────────────────────────────────────────────
# AC1/AC5 — EDITOR_CONTENT_MODELS allowlist (15 parova; eksplicitne ekskluzije)
# ──────────────────────────────────────────────────────────────────────────────
def test_ac5_editor_content_models_is_exact_15_pair_allowlist():
    """AC5/SM-D3/G-13: EDITOR_CONTENT_MODELS sadrži TAČNO 15 (app_label, model) parova."""
    from apps.accounts.permissions import EDITOR_CONTENT_MODELS

    expected = {
        ("brands", "brand"),
        ("brands", "series"),
        ("brands", "category"),
        ("brands", "subcategory"),
        ("products", "product"),
        ("products", "productimage"),
        ("products", "productvariant"),
        ("products", "productspecification"),
        ("products", "productbrochure"),
        ("products", "producttestimonial"),
        ("products", "productsimilar"),
        ("blog", "post"),
        ("blog", "category"),
        ("blog", "tag"),
        ("pages", "page"),
    }
    actual = set(tuple(p) for p in EDITOR_CONTENT_MODELS)
    assert actual == expected, (
        f"EDITOR_CONTENT_MODELS MORA biti TAČNO 15 content parova (4 brands + 7 products + "
        f"3 blog + 1 pages). Razlika: nedostaje={expected - actual}, višak={actual - expected}."
    )


def test_ac5_editor_content_models_excludes_legal_and_config():
    """AC5/SM-D15/D16: allowlist NE sadrži pages.sitesettings ni gdpr.cookiepolicy (Superadmin-only)."""
    from apps.accounts.permissions import EDITOR_CONTENT_MODELS

    pairs = set(tuple(p) for p in EDITOR_CONTENT_MODELS)
    assert ("pages", "sitesettings") not in pairs, (
        "SiteSettings je Superadmin-only (globalna config — SM-D15); NE sme biti u Editor allowlist-u."
    )
    assert ("gdpr", "cookiepolicy") not in pairs, (
        "CookiePolicy je Superadmin-only (pravni dokument + RISK-1 — SM-D16); NE u Editor allowlist-u."
    )
    assert not any(app == "gdpr" for app, _m in pairs), (
        "Editor NE sme imati NIJEDAN gdpr.* model u allowlist-u (SM-D16)."
    )


# ──────────────────────────────────────────────────────────────────────────────
# AC2 — IsSuperadminMixin test_func logika
# ──────────────────────────────────────────────────────────────────────────────
def test_ac2_superadmin_mixin_subclasses_login_required_and_user_passes_test():
    """AC2: IsSuperadminMixin kombinuje LoginRequiredMixin + UserPassesTestMixin + raise_exception=True."""
    from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

    from apps.accounts.permissions import IsSuperadminMixin

    assert issubclass(IsSuperadminMixin, LoginRequiredMixin), (
        "IsSuperadminMixin MORA naslediti LoginRequiredMixin (anon → login redirect; G-9/AC2)."
    )
    assert issubclass(IsSuperadminMixin, UserPassesTestMixin), (
        "IsSuperadminMixin MORA naslediti UserPassesTestMixin (test_func gate — AC2)."
    )
    assert IsSuperadminMixin.raise_exception is True, (
        "IsSuperadminMixin.raise_exception MORA biti True (autentifikovan-neovlašćen → 403; SM-D8/AC2)."
    )


def test_ac2_superadmin_mixin_login_required_is_first_in_mro():
    """AC2/G-9: LoginRequiredMixin PRVI u MRO (anon obrada PRE test_func)."""
    from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

    from apps.accounts.permissions import IsSuperadminMixin

    mro = IsSuperadminMixin.__mro__
    assert mro.index(LoginRequiredMixin) < mro.index(UserPassesTestMixin), (
        "LoginRequiredMixin MORA biti PRE UserPassesTestMixin u MRO (anon → login PRE test_func; G-9)."
    )


def test_ac2_superadmin_test_func_passes_superuser_blocks_editor():
    """AC2: test_func True za superuser; False za Editor-a; False za običan staff."""
    from apps.accounts.permissions import IsSuperadminMixin

    superuser = _make_superuser()
    editor = _make_editor()
    plain = _make_plain_staff()

    def _eval(user):
        m = IsSuperadminMixin()
        m.request = type("R", (), {"user": user})()
        return m.test_func()

    assert _eval(superuser) is True, "IsSuperadminMixin.test_func MORA biti True za is_superuser (AC2)."
    assert _eval(editor) is False, "IsSuperadminMixin.test_func MORA biti False za Editor-a (AC2)."
    assert _eval(plain) is False, "IsSuperadminMixin.test_func MORA biti False za običan staff (AC2)."


# ──────────────────────────────────────────────────────────────────────────────
# AC3 — IsEditorMixin test_func logika (superset)
# ──────────────────────────────────────────────────────────────────────────────
def test_ac3_editor_mixin_subclasses_and_raise_exception():
    """AC3: IsEditorMixin = LoginRequiredMixin + UserPassesTestMixin + raise_exception=True."""
    from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

    from apps.accounts.permissions import IsEditorMixin

    assert issubclass(IsEditorMixin, LoginRequiredMixin)
    assert issubclass(IsEditorMixin, UserPassesTestMixin)
    assert IsEditorMixin.raise_exception is True, (
        "IsEditorMixin.raise_exception MORA biti True (autentifikovan-neovlašćen → 403; SM-D8/AC3)."
    )


def test_ac3_editor_test_func_superset_superuser_and_editor_pass():
    """AC3/SM-D7: test_func True za Editor-a I za superuser (superset); False za običan staff."""
    from apps.accounts.permissions import IsEditorMixin

    superuser = _make_superuser()
    editor = _make_editor()
    plain = _make_plain_staff()

    def _eval(user):
        m = IsEditorMixin()
        m.request = type("R", (), {"user": user})()
        return m.test_func()

    assert _eval(editor) is True, "IsEditorMixin.test_func MORA biti True za Editor-a (AC3)."
    assert _eval(superuser) is True, (
        "IsEditorMixin.test_func MORA biti True i za superuser (superset — SM-D7/AC3)."
    )
    assert _eval(plain) is False, "IsEditorMixin.test_func MORA biti False za ne-Editor/ne-superuser (AC3)."


# ──────────────────────────────────────────────────────────────────────────────
# Opcioni helper-i is_editor / is_superadmin (testovi se skip-uju ako ne postoje)
# ──────────────────────────────────────────────────────────────────────────────
def test_helper_is_superadmin_if_defined():
    """is_superadmin(user) helper (opciono): True za superuser, False za Editor-a."""
    perms = pytest.importorskip("apps.accounts.permissions")
    if not hasattr(perms, "is_superadmin"):
        pytest.skip("is_superadmin helper nije definisan (opciono).")
    assert perms.is_superadmin(_make_superuser()) is True
    assert perms.is_superadmin(_make_editor()) is False


def test_helper_is_editor_if_defined():
    """is_editor(user) helper (opciono): True za Editor-a i superuser (superset)."""
    perms = pytest.importorskip("apps.accounts.permissions")
    if not hasattr(perms, "is_editor"):
        pytest.skip("is_editor helper nije definisan (opciono).")
    assert perms.is_editor(_make_editor()) is True
    assert perms.is_editor(_make_superuser()) is True
    assert perms.is_editor(_make_plain_staff()) is False


# ──────────────────────────────────────────────────────────────────────────────
# AC4 / AC7 — post_migrate kreira obe grupe; idempotentno
# ──────────────────────────────────────────────────────────────────────────────
def test_ac4_both_groups_exist_after_migrate():
    """AC4/AC7: posle migrate (test-DB setup okida post_migrate) postoje Superadmin + Editor grupe."""
    from django.contrib.auth.models import Group

    assert Group.objects.filter(name="Superadmin").exists(), (
        "Superadmin grupa MORA postojati posle migrate (post_migrate sync_rbac_groups — AC4/AC7)."
    )
    assert Group.objects.filter(name="Editor").exists(), (
        "Editor grupa MORA postojati posle migrate (post_migrate sync_rbac_groups — AC4)."
    )


def test_ac7_superadmin_group_has_zero_permissions():
    """AC7/SM-D6: Superadmin grupa MORA biti PRAZNA (0 perms).

    Superadmin moć = is_superuser (implicitno pokriva sve), NE group perms.
    Locks SM-D6 invarijantu: grupa ostaje prazna kroz sync_rbac_groups.
    """
    from django.contrib.auth.models import Group

    assert Group.objects.get(name="Superadmin").permissions.count() == 0, (
        "Superadmin grupa MORA biti prazna (0 perms) — moć dolazi od is_superuser, "
        "NE od group permisija (SM-D6/AC7)."
    )


def test_ac4_sync_is_idempotent_no_duplicate_groups_or_perms():
    """AC4/G-2: dvostruko pozivanje sync_rbac_groups NE duplira grupe ni menja Editor perm-set."""
    from django.contrib.auth.models import Group

    _call_sync_rbac()
    _call_sync_rbac()  # drugi put — idempotentno

    assert Group.objects.filter(name="Superadmin").count() == 1, (
        "Dvostruki sync NE sme duplirati Superadmin grupu (get_or_create — G-2/AC4)."
    )
    assert Group.objects.filter(name="Editor").count() == 1, (
        "Dvostruki sync NE sme duplirati Editor grupu (get_or_create — G-2/AC4)."
    )

    perms_after_two = set(
        Group.objects.get(name="Editor").permissions.values_list("id", flat=True)
    )
    _call_sync_rbac()  # treći put
    perms_after_three = set(
        Group.objects.get(name="Editor").permissions.values_list("id", flat=True)
    )
    assert perms_after_two == perms_after_three, (
        "Editor perm-set MORA biti deterministički kroz re-sync (set() ne add() — G-2/AC4)."
    )


# ──────────────────────────────────────────────────────────────────────────────
# AC5 — Editor grupa ima content CRUD permisije (reprezentativan podskup)
# ──────────────────────────────────────────────────────────────────────────────
def test_ac5_editor_has_representative_content_crud_perms():
    """AC5: Editor ima bar po jedan add/change/delete/view + po jedan model po app-u."""
    from django.contrib.auth.models import Group

    editor = Group.objects.get(name="Editor")
    codenames = set(editor.permissions.values_list("codename", flat=True))

    expected = {
        "add_product",      # products + add
        "change_post",      # blog + change
        "delete_brand",     # brands + delete
        "view_page",        # pages + view
        "view_series",      # brands sekundarni model
        "add_tag",          # blog sekundarni model
        "change_productimage",  # products related
    }
    missing = expected - codenames
    assert not missing, (
        f"Editor grupa MORA imati content CRUD permisije; nedostaju: {sorted(missing)} (AC5)."
    )


def test_ac5_editor_has_full_crud_for_all_15_models():
    """AC5: Editor ima TAČNO add/change/delete/view × 15 content modela = 60 content permisija."""
    from django.contrib.auth.models import Group

    from apps.accounts.permissions import EDITOR_CONTENT_MODELS

    editor = Group.objects.get(name="Editor")
    have = set(
        editor.permissions.values_list("content_type__app_label", "content_type__model", "codename")
    )
    missing = []
    for app_label, model in EDITOR_CONTENT_MODELS:
        for action in ("add", "change", "delete", "view"):
            codename = f"{action}_{model}"
            if (app_label, model, codename) not in have:
                missing.append(f"{app_label}.{codename}")
    assert not missing, (
        f"Editor MORA imati svе 4 CRUD perms za svih 15 modela (60 ukupno); nedostaju: {missing} (AC5)."
    )


def test_ac5_editor_excludes_sitesettings_and_gdpr():
    """AC5/SM-D15/D16: Editor NEMA pages.sitesettings ni ijednu gdpr.* perm; ALI IMA pages.view_page."""
    from django.contrib.auth.models import Group

    editor = Group.objects.get(name="Editor")

    assert not editor.permissions.filter(content_type__app_label="gdpr").exists(), (
        "Editor NE SME imati NIJEDNU gdpr.* permisiju (CookiePolicy Superadmin-only — SM-D16/AC5)."
    )
    assert not editor.permissions.filter(
        content_type__app_label="pages", content_type__model="sitesettings"
    ).exists(), (
        "Editor NE SME imati pages.*_sitesettings (SiteSettings Superadmin-only — SM-D15/AC5)."
    )
    # granica je po-modelu: Page JESTE dozvoljen
    assert editor.permissions.filter(
        content_type__app_label="pages", content_type__model="page", codename="view_page"
    ).exists(), (
        "Editor I DALJE MORA imati pages.view_page (Page je dozvoljen — granica je po-modelu, AC5)."
    )


# ──────────────────────────────────────────────────────────────────────────────
# AC6 — Editor NEMA auth/admin/infra permisije (CRITICAL privilege guard)
# ──────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("app_label", ["auth", "admin", "contenttypes", "sessions", "axes"])
def test_ac6_editor_has_no_dangerous_app_perms(app_label):
    """AC6 CRITICAL/G-3: Editor grupa NEMA NIJEDNU permisiju iz auth/admin/contenttypes/sessions/axes."""
    from django.contrib.auth.models import Group

    editor = Group.objects.get(name="Editor")
    leaked = list(
        editor.permissions.filter(content_type__app_label=app_label).values_list("codename", flat=True)
    )
    assert leaked == [], (
        f"PRIVILEGE ESCALATION: Editor grupa NE SME imati NIJEDNU '{app_label}.*' permisiju "
        f"(G-3 — Editor ne sme upravljati korisnicima/ulogama/infra); procurelo: {leaked} (AC6)."
    )


def test_ac6_editor_has_no_change_user_or_change_group_perm():
    """AC6 CRITICAL: konkretno NEMA auth.change_user / auth.add_user / auth.change_group."""
    from django.contrib.auth.models import Group

    editor = Group.objects.get(name="Editor")
    dangerous = {"change_user", "add_user", "delete_user", "change_group", "add_group"}
    have = set(editor.permissions.values_list("codename", flat=True))
    leaked = dangerous & have
    assert not leaked, (
        f"PRIVILEGE ESCALATION: Editor NE SME imati {sorted(leaked)} (kreiranje/izmena korisnika/grupa — AC6)."
    )


# ──────────────────────────────────────────────────────────────────────────────
# AC14 — fail-closed na REALNOM view-u (integration, raise_exception=True dokaz)
# ──────────────────────────────────────────────────────────────────────────────
def _run_gated_request(view_factory, url_name, path_str, user=None):
    """Registruj test-only urlconf sa gated view-om i izvrši GET (force_login ako user dat)."""
    test_urls = type("M", (), {"urlpatterns": [path(path_str, view_factory().as_view(), name=url_name)]})
    with override_settings(ROOT_URLCONF=test_urls):
        client = Client()
        if user is not None:
            client.force_login(user)
        return client.get(reverse(url_name))


def test_ac14_editor_gate_anonymous_redirects_to_login():
    """AC14: IsEditorMixin view — anoniman → 302 login redirect (LoginRequiredMixin; G-9)."""
    resp = _run_gated_request(_editor_view_class, "test_editor_gate", "test-editor-gate/", user=None)
    assert resp.status_code == 302, (
        f"Anoniman na IsEditor view MORA biti 302 (login redirect — LoginRequiredMixin), dobio {resp.status_code} (AC14)."
    )


def test_ac14_editor_gate_plain_staff_gets_403():
    """AC14: IsEditorMixin view — autentifikovan non-group (običan staff) → 403 (raise_exception=True)."""
    resp = _run_gated_request(
        _editor_view_class, "test_editor_gate", "test-editor-gate/", user=_make_plain_staff()
    )
    assert resp.status_code == 403, (
        f"Običan staff (ne-Editor/ne-superuser) na IsEditor view MORA biti 403 (raise_exception=True; SM-D8), "
        f"dobio {resp.status_code} (AC14)."
    )


def test_ac14_editor_gate_editor_gets_200():
    """AC14: IsEditorMixin view — Editor → 200."""
    resp = _run_gated_request(
        _editor_view_class, "test_editor_gate", "test-editor-gate/", user=_make_editor()
    )
    assert resp.status_code == 200, (
        f"Editor na IsEditor view MORA biti 200, dobio {resp.status_code} (AC14)."
    )


def test_ac14_editor_gate_superuser_gets_200():
    """AC14/SM-D7: IsEditorMixin view — superuser → 200 (superset)."""
    resp = _run_gated_request(
        _editor_view_class, "test_editor_gate", "test-editor-gate/", user=_make_superuser()
    )
    assert resp.status_code == 200, (
        f"Superuser na IsEditor view MORA biti 200 (superset — SM-D7), dobio {resp.status_code} (AC14)."
    )


def test_ac14_superadmin_gate_editor_gets_403():
    """AC14: IsSuperadminMixin view — Editor → 403 (raise_exception=True; Editor NIJE superadmin)."""
    resp = _run_gated_request(
        _superadmin_view_class, "test_superadmin_gate", "test-superadmin-gate/", user=_make_editor()
    )
    assert resp.status_code == 403, (
        f"Editor na IsSuperadmin view MORA biti 403 (raise_exception=True; SM-D8), dobio {resp.status_code} (AC14)."
    )


def test_ac14_superadmin_gate_plain_staff_gets_403():
    """AC14: IsSuperadminMixin view — autentifikovan non-group (običan staff) → 403 (raise_exception=True)."""
    resp = _run_gated_request(
        _superadmin_view_class, "test_superadmin_gate", "test-superadmin-gate/", user=_make_plain_staff()
    )
    assert resp.status_code == 403, (
        f"Običan staff (ne-superadmin/ne-superuser) na IsSuperadmin view MORA biti 403 "
        f"(raise_exception=True; SM-D8), dobio {resp.status_code} (AC14)."
    )


def test_ac14_superadmin_gate_superuser_gets_200():
    """AC14: IsSuperadminMixin view — superuser → 200."""
    resp = _run_gated_request(
        _superadmin_view_class, "test_superadmin_gate", "test-superadmin-gate/", user=_make_superuser()
    )
    assert resp.status_code == 200, (
        f"Superuser na IsSuperadmin view MORA biti 200, dobio {resp.status_code} (AC14)."
    )


def test_ac14_superadmin_gate_anonymous_redirects_to_login():
    """AC14: IsSuperadminMixin view — anoniman → 302 login redirect."""
    resp = _run_gated_request(
        _superadmin_view_class, "test_superadmin_gate", "test-superadmin-gate/", user=None
    )
    assert resp.status_code == 302, (
        f"Anoniman na IsSuperadmin view MORA biti 302 (login redirect), dobio {resp.status_code} (AC14)."
    )


# ──────────────────────────────────────────────────────────────────────────────
# AC8 — Editor vidi admin ALI NEMA pristup User/Group adminu → 403
# ──────────────────────────────────────────────────────────────────────────────
def test_ac8_editor_denied_user_changelist_403():
    """AC8: Editor (is_staff + Editor grupa) → GET admin:auth_user_changelist → 403."""
    editor = _make_editor()
    client = Client()
    client.force_login(editor)
    resp = client.get(reverse("admin:auth_user_changelist"))
    assert resp.status_code == 403, (
        f"Editor NE SME pristupiti User changelist-u (nema auth.view_user — AC8). "
        f"PRIMARNO 403; dobio {resp.status_code} (!=200 je dokumentovani fallback, ali očekuj 403)."
    )


def test_ac8_editor_denied_group_changelist_403():
    """AC8: Editor → GET admin:auth_group_changelist → 403."""
    editor = _make_editor()
    client = Client()
    client.force_login(editor)
    resp = client.get(reverse("admin:auth_group_changelist"))
    assert resp.status_code == 403, (
        f"Editor NE SME pristupiti Group changelist-u (nema auth.view_group — AC8), dobio {resp.status_code}."
    )


# ──────────────────────────────────────────────────────────────────────────────
# AC9 — Editor MOŽE CRUD content modele kroz admin
# ──────────────────────────────────────────────────────────────────────────────
def test_ac9_editor_can_access_product_changelist_200():
    """AC9: Editor → GET admin:products_product_changelist → 200 (ima content perms iz AC5)."""
    editor = _make_editor()
    client = Client()
    client.force_login(editor)
    resp = client.get(reverse("admin:products_product_changelist"))
    assert resp.status_code == 200, (
        f"Editor MORA pristupiti Product changelist-u (ima content perms — AC9), dobio {resp.status_code}."
    )


def test_ac9_editor_can_access_blog_post_changelist_200():
    """AC9: Editor → GET admin:blog_post_changelist → 200."""
    editor = _make_editor()
    client = Client()
    client.force_login(editor)
    resp = client.get(reverse("admin:blog_post_changelist"))
    assert resp.status_code == 200, (
        f"Editor MORA pristupiti Blog Post changelist-u (ima content perms — AC9), dobio {resp.status_code}."
    )


# ──────────────────────────────────────────────────────────────────────────────
# AC7 — Superadmin pristup User adminu
# ──────────────────────────────────────────────────────────────────────────────
def test_ac7_superuser_can_access_user_changelist_200():
    """AC7: superuser → GET admin:auth_user_changelist → 200 (User management)."""
    superuser = _make_superuser()
    client = Client()
    client.force_login(superuser)
    resp = client.get(reverse("admin:auth_user_changelist"))
    assert resp.status_code == 200, (
        f"Superuser MORA pristupiti User changelist-u (AC7), dobio {resp.status_code}."
    )


# ──────────────────────────────────────────────────────────────────────────────
# AC10 — Password change dostupan oba (Editor i Superadmin)
# ──────────────────────────────────────────────────────────────────────────────
def test_ac10_editor_password_change_200():
    """AC10/SM-D12/G-6: Editor → GET admin:password_change → 200 (self password, NEZAVISNO od change_user)."""
    editor = _make_editor()
    client = Client()
    client.force_login(editor)
    resp = client.get(reverse("admin:password_change"))
    assert resp.status_code == 200, (
        f"Editor MORA moći otvoriti password_change (self — G-6/AC10), dobio {resp.status_code}."
    )


def test_ac10_superuser_password_change_200():
    """AC10: superuser → GET admin:password_change → 200."""
    superuser = _make_superuser()
    client = Client()
    client.force_login(superuser)
    resp = client.get(reverse("admin:password_change"))
    assert resp.status_code == 200, (
        f"Superuser MORA moći otvoriti password_change (AC10), dobio {resp.status_code}."
    )


# ──────────────────────────────────────────────────────────────────────────────
# AC11 — NEMA custom AUTH_USER_MODEL / NEMA accounts schema migracije
# ──────────────────────────────────────────────────────────────────────────────
def test_ac11_auth_user_model_is_default():
    """AC11/SM-D1: settings.AUTH_USER_MODEL == 'auth.User' (NIJE promenjen)."""
    from django.conf import settings

    assert settings.AUTH_USER_MODEL == "auth.User", (
        f"AUTH_USER_MODEL MORA ostati 'auth.User' (NEMA custom User — SM-D1/AC11), dobio {settings.AUTH_USER_MODEL!r}."
    )


def test_ac11_accounts_has_no_models():
    """AC11/G-8: apps.accounts NEMA modele (prazan models.py → nema schema migracije)."""
    from django.apps import apps as django_apps

    accounts_models = list(django_apps.get_app_config("accounts").get_models())
    assert accounts_models == [], (
        f"apps.accounts NE SME imati modele (RBAC je runtime post_migrate — G-8/AC11); "
        f"našao {[m.__name__ for m in accounts_models]}."
    )


def test_ac11_no_pending_migration_for_accounts():
    """AC11/Task7.1: makemigrations --check NE generiše migraciju za accounts (RBAC je runtime)."""
    from django.apps import apps as django_apps
    from django.db.migrations.autodetector import MigrationAutodetector
    from django.db.migrations.loader import MigrationLoader
    from django.db.migrations.state import ProjectState

    loader = MigrationLoader(None, ignore_no_migrations=True)
    autodetector = MigrationAutodetector(
        loader.project_state(),
        ProjectState.from_apps(django_apps),
    )
    changes = autodetector.changes(graph=loader.graph)
    assert "accounts" not in changes, (
        f"apps.accounts NE SME imati pending schema migraciju (RBAC je runtime post_migrate — AC11/G-8); "
        f"autodetector predlaže: {changes.get('accounts')}."
    )


# ──────────────────────────────────────────────────────────────────────────────
# AC12 — CustomUserAdmin re-registrovan; get_user_model (NE direktan import)
# ──────────────────────────────────────────────────────────────────────────────
def test_ac12_custom_user_admin_registered_as_useradmin_subclass():
    """AC12: admin.site._registry[User] je STROGI UserAdmin subclass (CustomUserAdmin), NE default UserAdmin.

    KRITIČNO: `isinstance(registered, UserAdmin)` je TAČNO i za default-registrovan UserAdmin
    (RED faza), pa bi bilo false-green. AC12 zahteva da se default UserAdmin UNREGISTER-uje i
    zameni vlastitim subclass-om → asertujemo `type(registered) is not UserAdmin` (strogi subclass).
    """
    from django.contrib import admin
    from django.contrib.auth.admin import UserAdmin

    User = get_user_model()
    registered = admin.site._registry.get(User)
    assert registered is not None, (
        "User model MORA biti registrovan u admin (CustomUserAdmin re-register — AC12)."
    )
    assert isinstance(registered, UserAdmin), (
        f"Registrovan admin za User MORA biti UserAdmin subclass (CustomUserAdmin) — AC12; "
        f"dobio {type(registered).__name__}."
    )
    assert type(registered) is not UserAdmin, (
        "Registrovan admin za User je TAČNO default django UserAdmin — AC12 zahteva da se default "
        "UNREGISTER-uje i zameni CustomUserAdmin subclass-om (NE smeš ostaviti default; SM-D10/G-7)."
    )


def test_ac12_admin_module_uses_get_user_model_not_direct_import():
    """AC12/project-context:112: admin.py koristi get_user_model() (NIKAD direktan User import)."""
    from apps.accounts import admin as accounts_admin

    src = inspect.getsource(accounts_admin)
    assert "get_user_model" in src, (
        "apps/accounts/admin.py MORA koristiti get_user_model() (AC12/project-context:112)."
    )
    assert "from django.contrib.auth.models import User" not in src, (
        "NIKAD `from django.contrib.auth.models import User` u admin.py — koristi get_user_model() (AC12)."
    )


# ──────────────────────────────────────────────────────────────────────────────
# AC13 — CustomUserAdmin self-escalation hardening (HIGH security, defense-in-depth)
# ──────────────────────────────────────────────────────────────────────────────
def _flatten_fieldset_fields(fieldsets):
    """Izvuci sve field-name iz (name, opts) fieldsets struktura (flat skup)."""
    out = set()
    for _name, opts in fieldsets:
        for f in opts.get("fields", ()):
            if isinstance(f, (tuple, list)):
                out.update(f)
            else:
                out.add(f)
    return out


def _user_change_request(user):
    """RequestFactory GET sa autentifikovanim user-om (za get_form/get_fieldsets)."""
    from django.test import RequestFactory

    req = RequestFactory().get("/admin-coric/auth/user/1/change/")
    req.user = user
    return req


def test_ac13_nonsuperuser_cannot_edit_sensitive_fields():
    """AC13/SM-D17/G-14: ne-superuser (čak sa auth.change_user) NE vidi is_superuser/is_staff/groups/
    user_permissions kao editabilna polja (skrivena ili readonly)."""
    from django.contrib import admin
    from django.contrib.auth.models import Permission

    User = get_user_model()
    admin_instance = admin.site._registry[User]

    # ne-superuser staff sa eksplicitno datim auth.change_user (simulirana misconfig)
    staff = _make_plain_staff(email="esc@coricagrar.rs", username="escstaff")
    change_user = Permission.objects.get(content_type__app_label="auth", codename="change_user")
    staff.user_permissions.add(change_user)
    staff = User.objects.get(pk=staff.pk)  # osveži perm cache

    target = _make_editor(email="target@coricagrar.rs", username="targetuser")
    req = _user_change_request(staff)

    sensitive = {"is_superuser", "is_staff", "groups", "user_permissions"}

    fieldset_fields = _flatten_fieldset_fields(admin_instance.get_fieldsets(req, target))
    readonly = set(admin_instance.get_readonly_fields(req, target))
    # editabilna osetljiva polja = u fieldsets I NISU readonly
    editable_sensitive = (sensitive & fieldset_fields) - readonly
    assert not editable_sensitive, (
        f"SELF-ESCALATION: ne-superuser staff NE SME imati editabilna polja {sorted(editable_sensitive)} "
        f"(skrivena iz fieldsets ILI readonly — SM-D17/G-14/AC13)."
    )


def test_ac13_nonsuperuser_add_form_obj_none_is_sane():
    """AC13: add-form (obj=None) za ne-superusera ne razbija get_fieldsets/get_readonly_fields/get_form.

    Pokriva admin.py add-form put (obj=None) — default add_fieldsets bez osetljivih
    polja; ne sme da pukne ni da izloži osetljiva polja kao editabilna.
    """
    from django.contrib import admin
    from django.test import RequestFactory

    User = get_user_model()
    admin_instance = admin.site._registry[User]

    staff = _make_plain_staff(email="addform@coricagrar.rs", username="addformstaff")
    req = RequestFactory().get("/admin-coric/auth/user/add/")
    req.user = staff

    fieldset_fields = _flatten_fieldset_fields(admin_instance.get_fieldsets(req, None))
    readonly = set(admin_instance.get_readonly_fields(req, None))
    sensitive = {"is_superuser", "is_staff", "groups", "user_permissions"}
    editable_sensitive = (sensitive & fieldset_fields) - readonly
    assert not editable_sensitive, (
        f"Add-form (obj=None) za ne-superusera NE SME izložiti editabilna osetljiva polja "
        f"{sorted(editable_sensitive)} (AC13)."
    )
    # get_form ne sme da padne na add-form putanji (obj=None) za ne-superusera
    form = admin_instance.get_form(req, None)
    assert form is not None, "get_form(obj=None) za ne-superusera MORA vratiti form klasu (AC13)."


def test_ac13_superuser_retains_sensitive_fields_editable():
    """AC13: superuser ZADRŽAVA is_superuser/groups/user_permissions kao editabilna polja."""
    from django.contrib import admin

    User = get_user_model()
    admin_instance = admin.site._registry[User]

    superuser = _make_superuser(email="su13@coricagrar.rs", username="su13")
    target = _make_editor(email="t13@coricagrar.rs", username="t13")
    req = _user_change_request(superuser)

    fieldset_fields = _flatten_fieldset_fields(admin_instance.get_fieldsets(req, target))
    readonly = set(admin_instance.get_readonly_fields(req, target))
    for f in ("is_superuser", "groups", "user_permissions"):
        assert f in fieldset_fields and f not in readonly, (
            f"Superuser MORA zadržati editabilno polje '{f}' (pun pristup — AC13); "
            f"u_fieldsets={f in fieldset_fields}, readonly={f in readonly}."
        )


# ──────────────────────────────────────────────────────────────────────────────
# Wiring sanity — post_migrate handler konektovan + ready() ne razbija 8.1
# ──────────────────────────────────────────────────────────────────────────────
def test_post_migrate_handler_is_connected():
    """SM-D9: sync_rbac_groups je konektovan na post_migrate signal (ready() wiring)."""
    from django.db.models.signals import post_migrate

    from apps.accounts.permissions import sync_rbac_groups

    receivers = []
    for entry in post_migrate.receivers:
        # Django 5.2: receivers su (lookup_key, receiver_ref, is_async) 3-tuple
        ref = entry[1]
        rcv = ref() if callable(ref) else ref
        if rcv is not None:
            receivers.append(rcv)
    assert sync_rbac_groups in receivers, (
        "sync_rbac_groups MORA biti konektovan na post_migrate signal u AccountsConfig.ready() (SM-D9)."
    )


def test_ready_does_not_break_81_login_form_wiring():
    """SM-D13: 8.1 admin.site.login_form wiring OSTAJE netaknut posle 8.2 ready() dodatka."""
    from django.contrib import admin

    from apps.accounts.forms import AdminLoginForm

    assert admin.site.login_form is AdminLoginForm, (
        "8.1 admin.site.login_form = AdminLoginForm MORA ostati netaknut posle 8.2 ready() dodatka (SM-D13)."
    )
