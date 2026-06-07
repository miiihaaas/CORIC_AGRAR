---
story_id: "8.2"
story-key: 8-2-user-accounts-rbac-superadmin-editor-groups
title: User Accounts + RBAC (Superadmin / Editor Groups) — INTERFACE CONTRACT (TEA RED)
status: red-phase
epic: 8
created: 2026-06-07
author: TEA (Test Architect) — RED phase; defines the production interface the FAILING tests bind to. NO production code written here.
---

# Story 8.2 — Interface Contract (RBAC: Superadmin / Editor)

> Ovaj dokument je **ugovor** koji RED-faza testovi (`apps/accounts/tests/test_rbac.py`)
> očekuju. Dev (GREEN faza) implementira TAČNO ove simbole/potpise/semantiku. Bilo
> kakvo odstupanje u imenu, potpisu ili ponašanju mora biti reflektovano i u testovima.
>
> KLJUČNE ODLUKE (iz story SM-Log): default `auth.User` (NEMA custom AUTH_USER_MODEL),
> grupe kroz `post_migrate` handler (NE data-migracija), Editor = default-deny allowlist
> od 15 content modela, oba mixina `raise_exception = True`, `CustomUserAdmin`
> self-escalation hardening, 0 schema migracija za accounts.

---

## 1. `apps/accounts/permissions.py` — NOVI (RBAC core)

Sav RBAC živi u jednom modulu (SM-D14 — YAGNI zaseban `signals.py`). Modul je
**collection-safe za top-level import** (`Group`/`Permission`/`ContentType` import iz
`django.contrib.auth.models` / `django.contrib.contenttypes.models` je dozvoljen —
G-12; SAMO `from django.contrib.auth.models import User` je ZABRANJEN).

### 1.1 Group-name konstante (single-source-of-truth — SM-D5)

```python
GROUP_SUPERADMIN: str = "Superadmin"
GROUP_EDITOR: str = "Editor"
```

- Tačne string vrednosti `"Superadmin"` / `"Editor"`. Dele ih mixin (membership check)
  i `sync_rbac_groups` (creation) — NE hardkoduj string na dva mesta.

### 1.2 `EDITOR_CONTENT_MODELS` — eksplicitan default-deny allowlist (SM-D3/G-13)

```python
EDITOR_CONTENT_MODELS: list[tuple[str, str]] = [
    # brands (4)
    ("brands", "brand"),
    ("brands", "series"),
    ("brands", "category"),
    ("brands", "subcategory"),
    # products (7 — _ProductIndex je models.Index, NIJE Model → izostavljen)
    ("products", "product"),
    ("products", "productimage"),
    ("products", "productvariant"),
    ("products", "productspecification"),
    ("products", "productbrochure"),
    ("products", "producttestimonial"),
    ("products", "productsimilar"),
    # blog (3)
    ("blog", "post"),
    ("blog", "category"),
    ("blog", "tag"),
    # pages (1 — SAMO Page; SiteSettings IZOSTAVLJEN, SM-D15)
    ("pages", "page"),
]
```

- TAČNO **15 parova** (4 + 7 + 3 + 1). Model imena **lowercase** (`ContentType.model` konvencija).
- IZOSTAVLJENO (NE sme se pojaviti): `pages.sitesettings`, `gdpr.cookiepolicy`, sve
  `auth.*`, `admin.*`, `contenttypes.*`, `sessions.*`, `axes.*`, `search.*`.

### 1.3 `IsSuperadminMixin` (AC2)

```python
class IsSuperadminMixin(LoginRequiredMixin, UserPassesTestMixin):
    raise_exception = True
    def test_func(self) -> bool:
        u = self.request.user
        return u.is_superuser or u.groups.filter(name=GROUP_SUPERADMIN).exists()
```

- MRO: `LoginRequiredMixin` PRVI (anon → login redirect PRE `test_func`; G-9).
- `raise_exception = True` (SM-D8): autentifikovan-neovlašćen → **403 PermissionDenied**;
  anoniman → **302 login redirect** (LoginRequiredMixin).
- `test_func`: `True` za `is_superuser` ILI člana `Superadmin` grupe; inače `False`.

### 1.4 `IsEditorMixin` (AC3 — superset)

```python
class IsEditorMixin(LoginRequiredMixin, UserPassesTestMixin):
    raise_exception = True
    def test_func(self) -> bool:
        u = self.request.user
        return u.is_superuser or u.groups.filter(name=GROUP_EDITOR).exists()
```

- `True` za `is_superuser` (superadmin prolazi Editor gate — superset, SM-D7) ILI
  člana `Editor` grupe; inače `False`.
- Isto `raise_exception=True` / MRO ponašanje kao 1.3.

### 1.5 (Opciono) helper funkcije

Ako Dev izdvoji logiku članstva u helpere, testovi ih koriste preko **getattr**
(prisutnost nije obavezna — testovi `pytest.skip` ako ne postoje):

```python
def is_superadmin(user) -> bool: ...   # user.is_superuser or group=Superadmin
def is_editor(user) -> bool: ...       # user.is_superuser or group=Editor
```

### 1.6 `sync_rbac_groups(sender, **kwargs)` — post_migrate handler (AC4/5/6/7)

```python
def sync_rbac_groups(sender, **kwargs) -> None:
    # import Group/Permission/ContentType UNUTAR funkcije (post_migrate je app-registry-ready)
    superadmin, _ = Group.objects.get_or_create(name=GROUP_SUPERADMIN)   # prazna — is_superuser pokriva
    editor, _ = Group.objects.get_or_create(name=GROUP_EDITOR)
    perms = []
    for app_label, model in EDITOR_CONTENT_MODELS:
        perms.extend(
            Permission.objects.filter(
                content_type__app_label=app_label,
                content_type__model=model,
            )
        )
    editor.permissions.set(perms)   # set (NE add) → idempotentno + deterministički krajnji skup
```

- **Pozivljiv direktno** sa `sender=<AccountsConfig>` u testu (idempotency test poziva 2×).
- IDEMPOTENTAN (G-2): `get_or_create` + `permissions.set()`. Re-run NE duplira grupe ni
  permisije.
- Editor dobija TAČNO `add/change/delete/view` × 15 modela; NIJEDNU `auth/admin/infra` perm (G-3).
- Superadmin grupa kreirana ali bez eksplicitnih permisija (SM-D6).
- Robusno: `Permission.objects.filter(...)` (ne-postojeći model → prazan QS, ne crash; G-5).

---

## 2. `apps/accounts/admin.py` — NOVI (CustomUserAdmin)

```python
User = get_user_model()                          # NIKAD `from django.contrib.auth.models import User`
admin.site.unregister(User)                      # default auth UserAdmin (G-7 — INSTALLED_APPS redosled)

@admin.register(User)
class CustomUserAdmin(UserAdmin):                 # subclass django.contrib.auth.admin.UserAdmin
    # default UserAdmin fieldsets/add_form/UserChangeForm (password change link) ZADRŽANI (SM-D10/D12)

    _SENSITIVE_FIELDS = ("is_superuser", "is_staff", "groups", "user_permissions")

    def get_form(self, request, obj=None, **kwargs):
        # za ne-superusera ukloni/zaštiti osetljiva polja (AC13/SM-D17/G-14)
        ...
    def get_fieldsets(self, request, obj=None):
        # za ne-superusera fieldsets BEZ osetljivih polja (ili readonly)
        ...
    # (alternativno get_readonly_fields)
```

- **AC8:** Editor (`is_staff=True`, Editor grupa, `is_superuser=False`) → GET
  `admin:auth_user_changelist` / `admin:auth_group_changelist` → **403** (nema `auth.*` perm).
- **AC9:** Editor → GET `admin:products_product_changelist` (i ostali content) → **200**.
- **AC10:** Editor i superuser → GET `admin:password_change` → **200** (self password change,
  NEZAVISNO od `auth.change_user`; G-6).
- **AC12:** `admin.site._registry[User]` je instanca `UserAdmin` (subclass; re-register radi).
- **AC13 (defense-in-depth):** ne-superuser staff (čak i sa eksplicitno datim
  `auth.change_user`) NE sme videti `is_superuser`/`is_staff`/`groups`/`user_permissions`
  kao editabilna polja u `get_form`/`get_fieldsets`. Superuser → sva polja prisutna i editabilna.

---

## 3. `apps/accounts/apps.py` — EDIT (`ready()` wiring)

```python
def ready(self):
    # 8.1 (OSTAJE NETAKNUT — SM-D13)
    from django.contrib import admin
    from apps.accounts.forms import AdminLoginForm
    admin.site.login_form = AdminLoginForm

    # 8.2 (NOVO — SM-D9)
    from django.db.models.signals import post_migrate
    from apps.accounts.permissions import sync_rbac_groups
    post_migrate.connect(sync_rbac_groups, sender=self)
```

- `sender=self` (AccountsConfig) → handler se okida JEDNOM po `migrate` ciklusu (G-10).
- Importi UNUTAR `ready()` (circular-safe). 8.1 `login_form` wiring koegzistira.

---

## 4. Migracije / settings (AC11)

- `settings.AUTH_USER_MODEL == "auth.User"` (default — NIJE promenjen; SM-D1).
- `apps.accounts` NEMA novih schema migracija (`makemigrations --check` → no changes; G-8).
  RBAC je runtime `post_migrate`, NE schema. `models.py` ostaje prazan.

---

## 5. Sažetak garancija po AC

| AC | Garancija |
|---|---|
| AC1 | `GROUP_SUPERADMIN=="Superadmin"`, `GROUP_EDITOR=="Editor"` |
| AC2 | `IsSuperadminMixin` (LoginRequired+UserPassesTest, raise_exception=True); test_func super/group |
| AC3 | `IsEditorMixin` superset (superuser prolazi); raise_exception=True |
| AC4 | post_migrate kreira obe grupe; idempotentno (get_or_create + set) |
| AC5 | Editor ima CRUD × 15 content modela; NEMA gdpr / pages.sitesettings |
| AC6 | Editor NEMA NIJEDNU auth/admin/contenttypes/sessions/axes perm (CRITICAL) |
| AC7 | Superadmin grupa postoji; superuser pristupa user changelist (200) |
| AC8 | Editor → auth_user/auth_group changelist → 403 |
| AC9 | Editor → content changelist → 200 |
| AC10 | password_change → 200 za Editor i superuser |
| AC11 | AUTH_USER_MODEL=="auth.User"; 0 accounts schema migracija |
| AC12 | `_registry[User]` je UserAdmin subclass; get_user_model() korišćen |
| AC13 | ne-superuser get_form/get_fieldsets BEZ osetljivih polja; superuser ima ih |
| AC14 | realan throwaway view: anon→302, non-group→403, editor→200(IsEditor)/403(IsSuper), superuser→200 oba |
