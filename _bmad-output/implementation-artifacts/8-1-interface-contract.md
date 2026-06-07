---
story_id: "8.1"
story-key: 8-1-custom-admin-login-sa-rate-limiting
artifact: interface-contract
phase: RED (TEA) — definiše ugovor; Dev implementira GREEN
created: 2026-06-07
author: TEA (Test Architect, autonomous)
---

# Interface Contract — Story 8.1: Custom Admin Login sa Rate Limiting

> Ovaj dokument je MAŠINSKI UGOVOR koji RED-faza testovi
> (`apps/accounts/tests/test_admin_login.py`) asertuju. Dev MORA implementirati
> TAČNO ove simbole/putanje/vrednosti da bi testovi prešli u GREEN. Svako
> odstupanje (drugi naziv, druga vrednost, druga putanja) lomi RED→GREEN ugovor.

---

## 1. `apps/accounts/` — NOVI app skeleton

Kreiraj paket sa SLEDEĆOM strukturom (SM-D3):

```
apps/accounts/__init__.py          # prazan
apps/accounts/apps.py              # AccountsConfig + ready() wiring
apps/accounts/models.py            # prazan (app loading; bez schema migracije)
apps/accounts/forms.py             # AdminLoginForm
apps/accounts/migrations/__init__.py   # prazan paket (axes donosi SVOJE migracije)
apps/accounts/tests/__init__.py    # test paket (TEA)
apps/accounts/tests/test_admin_login.py  # TEA RED testovi
```

### 1.1 `apps/accounts/apps.py`

```python
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts"
    verbose_name = _("Nalozi i pristup")

    def ready(self):
        # CRITICAL-5 / SM-D13: STVARNO ožičenje forme u admin login flow.
        # Import UNUTAR ready() — circular-import safe (admin/app registry).
        from django.contrib import admin

        from apps.accounts.forms import AdminLoginForm

        admin.site.login_form = AdminLoginForm
```

UGOVOR (asertovan AC7/AC11):
- `AccountsConfig.name == "apps.accounts"`.
- Posle app-loading-a: `django.contrib.admin.site.login_form is AdminLoginForm`.

### 1.2 `apps/accounts/forms.py:AdminLoginForm`

```python
from django.contrib.admin.forms import AdminAuthenticationForm
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _


class AdminLoginForm(AdminAuthenticationForm):
    """Email-as-username admin login (SM-D4/SM-D13).

    Subclass AdminAuthenticationForm → zadržava confirm_login_allowed
    is_staff guard. UI label `username` polja prikazuje „Email". `clean()`
    rezolvuje uneti email → username (case-insensitive, prvi match) PRE
    super().clean() → authenticate(). NIKAD direktan User import — get_user_model().
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = _("Email")

    def clean(self):
        identifier = self.cleaned_data.get("username") or self.data.get("username")
        if identifier and "@" in identifier:
            user = (
                get_user_model()
                .objects.filter(email__iexact=identifier)
                .first()
            )
            if user is not None:
                # mapiraj rezolvovani email → username PRE authenticate()
                self.cleaned_data["username"] = user.get_username()
        return super().clean()
```

UGOVOR (asertovan AC7):
- Klasa `AdminLoginForm` postoji u `apps/accounts/forms.py`.
- `issubclass(AdminLoginForm, AdminAuthenticationForm)` → True (zadržava is_staff guard).
- Login POST sa email-om kao identifikatorom rezolvuje email→user i dolazi do
  `authenticate()` (validan email+password → uspešan login na `/admin-coric/`).
- `get_user_model()` (NE direktan `User` import).

> NAPOMENA (V1 granica, SM-D13): ako email ne rezolvuje na user → standardna
> „invalid login" greška (NE leak da li email postoji). Email rezolucija je
> case-insensitive, prvi match.

---

## 2. `config/settings/base.py` — dodaci

### 2.1 INSTALLED_APPS
- Dodaj `"axes"` POSLE `django.contrib.*` blok-a (G-16: MORA biti posle
  `django.contrib.contenttypes` + `django.contrib.auth`).
- Dodaj `"apps.accounts"` (posle domain app-ova; mirror ostalih `apps.*`).

### 2.2 AUTHENTICATION_BACKENDS (NOVO — ne postoji danas; G-1)
```python
AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesStandaloneBackend",   # PRVI — v8 standalone (G-4)
    "django.contrib.auth.backends.ModelBackend",  # OBAVEZAN — bez njega niko se ne loguje
]
```
UGOVOR (AC11):
- `AUTHENTICATION_BACKENDS[0] == "axes.backends.AxesStandaloneBackend"`.
- `"django.contrib.auth.backends.ModelBackend" in AUTHENTICATION_BACKENDS`.

### 2.3 MIDDLEWARE
- Dodaj `"axes.middleware.AxesMiddleware"` kao **POSLEDNJI** element
  (posle `apps.core.middleware.LocaleSwitcherMiddleware` — G-2/SM-D17).
UGOVOR (AC11):
- `MIDDLEWARE[-1] == "axes.middleware.AxesMiddleware"`.

### 2.4 AXES_* config
```python
from datetime import timedelta  # vrh fajla

AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = timedelta(hours=1)
AXES_RESET_ON_SUCCESS = True
AXES_LOCKOUT_PARAMETERS = [["ip_address"]]      # v8 IP-based (G-4/SM-D16)
AXES_LOCKOUT_TEMPLATE = "accounts/lockout.html"
AXES_HTTP_RESPONSE_CODE = 429                    # eksplicitno (AC4 lockout status)
# AXES_ENABLED ostaje True (SM-D15 — NE isključuj; force_login zaobilazi axes)
```
UGOVOR (AC5/AC4):
- `AXES_FAILURE_LIMIT == 5`.
- `AXES_COOLOFF_TIME == timedelta(hours=1)`.
- `AXES_RESET_ON_SUCCESS is True`.
- `AXES_LOCKOUT_PARAMETERS == [["ip_address"]]`.
- `AXES_LOCKOUT_TEMPLATE == "accounts/lockout.html"`.
- lockout odgovor → HTTP 429.

### 2.5 SESSION
```python
SESSION_COOKIE_AGE = 14400  # 4h = 14400s (epics 8.1 / arch:178 / NFR-3)
```
UGOVOR (AC8): `SESSION_COOKIE_AGE == 14400`.
- `SESSION_EXPIRE_AT_BROWSER_CLOSE` ostaje default False (G-10).

---

## 3. `config/urls.py` — admin slug migracija (SM-D1)

- UKLONI `path("admin/", admin.site.urls)` iz `i18n_patterns(...)` bloka.
- DODAJ `path("admin-coric/", admin.site.urls)` u **non-i18n** `urlpatterns`
  listu (uz sitemap.xml/robots.txt — VAN locale prefiksa; G-3).

UGOVOR (AC1/AC2/AC3):
- GET `/admin/` → 404; GET `/sr/admin/` → 404.
- GET `/admin-coric/` → admin login (200 sa login formom; ili redirect na
  `/admin-coric/login/` → 200).
- `reverse("admin:index")` počinje sa `/admin-coric/` (NE `/sr/`, NE `/admin/`).
- `reverse("admin:login") == "/admin-coric/login/"`.

---

## 4. `apps/seo/middleware.py` — `_ADMIN_RE` (CRITICAL-1 / SM-D12)

```python
# locale prefiks OPCIONI — pokriva bare `/admin-coric/` (Epic 8, VAN i18n_patterns)
# I prefiksovani `/sr/admin/` (backward-safe).
_ADMIN_RE = re.compile(r"^(/[a-z]{2})?/admin(-coric)?/")
```
UGOVOR (AC13):
- bare `/admin-coric/...` → 0 `seo_redirect` upita (skip PRE DB lookup).
- Redirect pravilo `old_path="/admin-coric/login/"` → NE proizvodi naš 301
  (admin login nije oteto; open-redirect na auth entry sprečen).
- postojeći `/sr/admin/` + `/sr/admin-coric/` skip i dalje rade.

---

## 5. `templates/seo/robots.txt` — UKLONI admin Disallow (CRITICAL-2 / SM-D14)

PRE:
```
User-agent: *
Allow: /
Disallow: */admin/
Disallow: */htmx/

Sitemap: {{ sitemap_url }}
```
POSLE (ukloni `Disallow: */admin/` liniju):
```
User-agent: *
Allow: /
Disallow: */htmx/

Sitemap: {{ sitemap_url }}
```
UGOVOR (AC14):
- telo `/robots.txt` NE sadrži `admin` ni `admin-coric` (NIJEDNA admin Disallow).
- `Disallow: */htmx/` + `Sitemap:` ostaju.

---

## 6. `templates/accounts/lockout.html` — STANDALONE (CRITICAL-4 / SM-D11)

- MORA biti STANDALONE: vlastiti `<!DOCTYPE html>` + `<head>` + `<body>`,
  **NE `{% extends "base.html" %}`** (axes renderuje VAN view pipeline-a →
  context_processori `consent_state`/`latest_blog_posts` NISU garantovani).
- `{% load i18n %}` + sve string-ove kroz `{% translate %}`.
- Srpski tekst (pune dijakritike), npr.:
  „Nalog je privremeno zaključan zbog previše neuspelih pokušaja prijave.
   Pokušajte ponovo kasnije." + lock-out indikator (npr. trajanje 1h).

UGOVOR (AC9/AC9b):
- Lockout odgovor → 429 + renderovan `accounts/lockout.html` BEZ greške
  (NE KeyError/context-var/TemplateSyntaxError).
- Telo sadrži srpski lockout tekst sa dijakritikama (npr. „zaključan").
- Telo NE sadrži `<base.html>` markere (npr. footer „Najnovije vesti" /
  consent banner) — standalone potvrda.

---

## 7. Migracije (AC12)
- `apps/accounts` NE generiše schema migraciju (prazan `models.py`).
- `migrate --plan` sadrži `axes` migracije (AccessAttempt/AccessLog/AccessFailureLog).

---

## 8. Test izolacija (SM-D15 / G-6 / G-12)
- `AXES_ENABLED` OSTAJE True (NE isključivati).
- Lockout testovi POST-uju DIREKTNO na `reverse("admin:login")` sa pogrešnim
  password-om (NE `force_login`/`client.login` — ti zaobilaze axes).
- OBAVEZAN teardown po lockout testu: `axes.utils.reset()` +
  `AccessAttempt.objects.all().delete()` + `cache.clear()`.
