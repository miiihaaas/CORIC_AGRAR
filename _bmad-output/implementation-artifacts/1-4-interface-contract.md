---
story-id: "1.4"
story-key: 1-4-i18n-setup-sa-locale-url-routing-i-switcher
artifact: interface-contract
author: TEA (Test Architect)
status: RED phase — kontrakt definiše tests; svi testovi MORAJU pasti dok Dev ne implementira.
language: Srpski (latinica)
---

# Story 1.4 — Interface Contract

Ovaj dokument opisuje **mašinski-verifikatibilan** kontrakt između TEA testova i
Dev implementacije za Story 1.4. Dev mora ispoštovati sve stavke ispod **doslovno**
(imena fajlova, atribut imena, redoslede, string vrednosti) — bilo kakva devijacija
prouzrokuje test fail.

## 1. Očekivani novi fajlovi (Dev MORA kreirati)

### 1.1 Django app skeleton — `apps/core/`

| Fajl | Sadržaj (minimalan kontrakt) |
|---|---|
| `apps/__init__.py` | Prazan ili docstring-only namespace marker. |
| `apps/core/__init__.py` | Prazan. |
| `apps/core/apps.py` | `class CoreConfig(AppConfig)` sa `name = "apps.core"`, `default_auto_field = "django.db.models.BigAutoField"`, `verbose_name = "Core"`. |
| `apps/core/middleware.py` | `class LocaleSwitcherMiddleware` (vidi § 3 Key contracts). |
| `apps/core/translation.py` | Placeholder modul — module docstring + commented-out primer (vidi § 3.4). |
| `apps/core/views.py` | `def home(request): return render(request, "base.html", {})` |
| `apps/core/urls.py` | `app_name = "core"`, `urlpatterns = [path("", home, name="home")]`. |
| `apps/core/tests/__init__.py` | Prazan (test package marker). |

**Forbidden (Story 1.4 ne sme imati):** `apps/core/models.py`, `apps/core/admin.py`, `apps/core/forms.py`, `apps/core/signals.py`, `apps/core/managers.py`, `apps/core/migrations/`.

### 1.2 Templates

| Fajl | Ključni elementi |
|---|---|
| `templates/base.html` | `<!DOCTYPE html>`, `{% load i18n %}`, `<html lang="{{ LANGUAGE_CODE }}">`, `{% include "partials/language_switcher.html" %}` u `<header>`, `{% block content %}{% endblock %}` u `<main>`, default content `<h1>Ćorić Agrar</h1>` + `{% translate "Dobrodošli." %}`. |
| `templates/partials/language_switcher.html` | `{% load i18n %}`, `<form action="{% url 'set_language' %}" method="post">`, `{% csrf_token %}`, `<input name="next" type="hidden" value="{{ request.path }}">`, `<select name="language">` sa 3 `<option>` (sr/hu/en, endonim labele), `<noscript>` fallback dugme. |

### 1.3 Locale struktura

```
locale/
├── sr/LC_MESSAGES/.gitkeep
├── hu/LC_MESSAGES/.gitkeep
└── en/LC_MESSAGES/.gitkeep
```

## 2. Očekivane modifikacije postojećih fajlova

### 2.1 `config/settings/base.py`

- `INSTALLED_APPS` — dodaj `"apps.core"` kao **poslednji** element.
- `MIDDLEWARE` — ubaci `"django.middleware.locale.LocaleMiddleware"` između `SessionMiddleware` i `CommonMiddleware`; dodaj `"apps.core.middleware.LocaleSwitcherMiddleware"` kao **poslednji** element.
- `TEMPLATES[0]["DIRS"]` — promeni iz `[]` na `[BASE_DIR / "templates"]`.
- `TEMPLATES[0]["OPTIONS"]["context_processors"]` — dodaj `"django.template.context_processors.i18n"`.
- `LANGUAGE_CODE` — promeni iz `"en-us"` u `"sr"`.
- **NOVO:** `LANGUAGES = [("sr", "Srpski"), ("hu", "Magyar"), ("en", "English")]`.
- **NOVO:** `LOCALE_PATHS = [BASE_DIR / "locale"]`.
- **NOVO:** `USE_L10N = True` (deklarativno, no-op u Django 5.x).
- `USE_I18N = True` — već postoji, verifikuj očuvanje.

**REGRESSION GUARD:** `DATABASES`, `EMAIL_*` (`vars().update(...)`), `AUTH_PASSWORD_VALIDATORS`, `STATIC_URL`, `DEFAULT_AUTO_FIELD`, `ROOT_URLCONF`, `WSGI_APPLICATION`, `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `TIME_ZONE`, `USE_TZ` — sve ostaje neizmenjeno.

### 2.2 `config/urls.py` — kompletna prepravka

```python
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.urls import include, path
from django.views.i18n import set_language

urlpatterns = [
    path("i18n/setlang/", set_language, name="set_language"),
]

urlpatterns += i18n_patterns(
    path("admin/", admin.site.urls),
    path("", include("apps.core.urls")),
    prefix_default_language=True,
)
```

**Admin URL ostaje `admin/`** (NE `admin-coric/`) — promena je deferred na Story 8.1 per Gotcha #25.

### 2.3 `pyproject.toml` — `[tool.pytest.ini_options]` (NOVO)

Dev MORA dodati pytest-django konfiguraciju:

```toml
[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "config.settings.development"
python_files = ["test_*.py", "*_test.py", "tests.py"]
```

Bez ovoga, `pytest-django` Client/RequestFactory testovi se ne mogu izvršiti.

### 2.4 `_bmad-output/project-context.md` (linija 205)

- Pre: `LANGUAGE_CODE = 'sr-latn'`
- Posle: `LANGUAGE_CODE = 'sr'` (matches `LANGUAGES` key — Story 1.4 odluka per Gotcha #4)

## 3. Key contracts (imena, signature, vrednosti)

### 3.1 `CoreConfig` (apps/core/apps.py)

```python
class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"
    verbose_name = "Core"
```

### 3.2 `LocaleSwitcherMiddleware` (apps/core/middleware.py)

- **Signature:** `def __init__(self, get_response)` + `def __call__(self, request)`.
- **Cookie-only persistencija:** koristi `settings.LANGUAGE_COOKIE_NAME` (default `"django_language"`).
- **NE SME** referencirati `translation.LANGUAGE_SESSION_KEY` (uklonjeno u Django 4.0 — `AttributeError` na prvi request).
- **Trust-but-verify:** `?lang=de` (unsupported) — ne baca exception, samo ignoriše.
- **Validne lokale:** `dict(settings.LANGUAGES).keys()` = `{"sr", "hu", "en"}`.
- Poziva `translation.activate(lang)` PRE `self.get_response(request)`.
- Postavlja `response.set_cookie(settings.LANGUAGE_COOKIE_NAME, lang, ...)` POSLE response-a ako je lokal promenjen.

### 3.3 `LANGUAGES` tuple (config/settings/base.py)

```python
LANGUAGES = [
    ("sr", "Srpski"),
    ("hu", "Magyar"),
    ("en", "English"),
]
```

**Tačno taj redosled** (sr → hu → en). **Tačno te endonim vrednosti** ("Srpski", "Magyar", "English").

### 3.4 `translation.py` example pattern (apps/core/translation.py)

- Modul docstring objašnjava ulogu fajla — pominje `TranslationOptions`, `modeltranslation`, `register`.
- Commented-out primer sadrži `fields = ("name", "description")` (NE `slogan` ili druga polja — to je primer iz story spec-a).
- **NIKAKAV** aktivan kod — fajl je čisto edukativan.
- Importable bez exception (`python -c "import apps.core.translation"` exit 0).

### 3.5 URL routing (config/urls.py)

- `set_language` MORA biti registrovan **van** `i18n_patterns()` na path-u `i18n/setlang/` sa imenom `"set_language"`.
- `i18n_patterns()` MORA imati `prefix_default_language=True` eksplicitno.
- Unutar `i18n_patterns()`: `admin/` (lokalizovan), `""` → `include("apps.core.urls")`.

### 3.6 Cookie name

`settings.LANGUAGE_COOKIE_NAME` (Django default `"django_language"`) — middleware koristi `settings.LANGUAGE_COOKIE_NAME`, NE hardcoded string.

### 3.7 `next` polje u language switcher form-i

**Kanonski oblik (jedini koji TEA test prihvata):** `<input type="hidden" name="next" value="{{ request.path }}">`.

NE koristiti: `|slice:'3:'`, `redirect_to|default:request.path`, `request.get_full_path`, ili bilo koji drugi pattern. Razlog: Django `set_language` view interno koristi `translate_url()` koji handluje locale prefix translation — `request.path` je dovoljan.

## 4. Test organizacija

| Test fajl | Šta testira |
|---|---|
| `apps/core/tests/__init__.py` | (prazan — package marker; Dev mora kreirati u step 3.3 + konfigurisati `importmode = "importlib"`) |
| `apps/core/tests/test_apps.py` | AC1 + AC2 (CoreConfig, registracija u INSTALLED_APPS, runtime app config). |
| `apps/core/tests/test_middleware.py` | AC3 (LocaleSwitcherMiddleware signature, behavior, cookie-only persistence, captures active locale during view via dummy_view). |
| `apps/core/tests/test_translation_module.py` | AC4 (translation.py importability + minimalan example sa `fields = ("name", "description")`). |
| `tests/test_i18n_setup.py` | AC2/AC5/AC6/AC7/AC8/AC9 — settings, URL routing (i18n_patterns + set_language pozicija + admin + apps.core.urls), templates, locale dirs + .gitkeep, regression, pytest-django config, manage.py check + apps.core runtime registracija. |

### 4.1 Test Client HTTP_HOST

TEA `_get_test_client()` helper konstruise `Client(HTTP_HOST="localhost")` jer
`config/settings/development.py::ALLOWED_HOSTS = ["localhost", "127.0.0.1", "[::1]"]`
NE sadrzi Django default `testserver`. Bez ovog override-a sve HTTP behavior
testove (AC5 routes + AC7 POST set_language) bi vracale 400 (DisallowedHost) cak
i posle pravilne Dev implementacije. Dev NE treba da menja settings — testovi
sami handluju.

## 5. Anti-regression flags (KRITIČNO za Dev)

1. **`test_bootstrap.py::test_ac3_installed_apps_is_default_django`** — testira da je `INSTALLED_APPS` Django default (6 stavki). Dodavanje `"apps.core"` BREAKS ovaj test. **Dev MORA u Step 3.3 ažurirati taj test** da prihvati `apps.core` kao 7. element (isti pattern kao Story 1.2/1.3 amendments).

2. **`test_bootstrap.py::test_no_out_of_scope_artifacts_yet`** — testira da `apps/`, `templates/`, `static/` NE postoje. Story 1.4 kreira `apps/` i `templates/`. **Dev MORA ažurirati forbidden listu** (skinuti `apps` i `templates`) — isti pattern kao Story 1.2 amendment (`.env.example`, `config/settings/`) i Story 1.3 amendment (`compose/`).

3. **`config/urls.py`** — Dev briše ceo postojeći sadržaj. Ne smeju ostati boilerplate komentari iz Django startproject template-a.

## 6. Smoke validacija (post-implementation)

```bash
uv run python manage.py check
uv run python manage.py shell -c "from apps.core.apps import CoreConfig; print(CoreConfig.name)"  # → apps.core
uv run python manage.py shell -c "from django.apps import apps; apps.get_app_config('core'); print('registered')"  # → registered
uv run python manage.py shell -c "from django.conf import settings; print(settings.LANGUAGE_CODE, dict(settings.LANGUAGES))"  # → sr {'sr': 'Srpski', ...}
uv run pytest tests/ apps/ -v  # → svi prolaze
```

## 7. Baseline brojanje testova (RED phase)

Posle TEA review-a (TEA Reviewer 🧪 v6.8.0):

- `apps/core/tests/`: 14 testova (test_apps + test_middleware + test_translation_module)
- `tests/test_i18n_setup.py`: 39 testova (uracunato 7 NOVIH dodatih u review-u)
- **Ukupno Story 1.4 testovi:** 53
- **RED baseline:** 45 failed + 7 passed (regression/vacuous guards) + 1 skipped

Regression/vacuous passes pre-implementation:
- `test_ac1_core_does_not_have_models_admin_yet` — scope guard (modeli ne smeju postojati)
- `test_ac2_use_i18n_true` — Story 1.2 vec postavila True, ovo je regression guard
- `test_ac5_de_route_404` — DEBUG mode 404 za nepoznat path (sa HTTP_HOST="localhost" fix-om)
- `test_ac8_just_messages_recipe_present` — Story 1.1 vec dodala recipe, regression guard
- `test_ac8_locale_dirs_have_tracked_content` — skipuje subdir koji ne postoji (drugi test hvata)
- `test_no_cirillic_anywhere_in_new_files` — fajlovi jos ne postoje, vacuous (aktivira se posle Dev-a)
- `test_admin_url_still_admin_not_admin_coric` — current `admin/` matches; aktivira se kao guard posle Dev urls.py prepravke
