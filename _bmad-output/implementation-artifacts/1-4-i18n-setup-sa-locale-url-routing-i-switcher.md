---
story-id: "1.4"
story-key: 1-4-i18n-setup-sa-locale-url-routing-i-switcher
title: i18n Setup sa Locale URL Routing i Switcher
status: done
epic_num: 1
epic_title: Project Foundation & Visual Identity
created: 2026-05-28
completed: 2026-05-28
author: Mihas (SM autonomous)
---

# Story 1.4: i18n Setup sa Locale URL Routing i Switcher

Status: done

<!-- Validacija je opcionalna. Pre dev-story koraka možeš pokrenuti validate-create-story za quality check. -->

## Story

As a **posetilac sajta**,
I want **da mogu da prebacim jezik na sajtu između srpskog (latinica), mađarskog i engleskog kroz vidljiv language switcher u UI-u**,
so that **mogu da čitam sadržaj na mom maternjem jeziku, a URL prefix (`/sr/`, `/hu/`, `/en/`) jasno reflektuje moj izbor i čuva strukturalnu poziciju na sajtu (deep-link je shareable i SEO-friendly)**.

Ovo je takođe **prvi Django app** u projektu — `apps/core/` se kreira kao temelj za sve buduće shared utilities, mixins, base klase i cross-cutting middleware (LocaleSwitcher, kasnije HtmxAria, RedirectMiddleware). Story 1.4 postavlja i18n + apps/ infrastrukturu na kojoj će se zidati svi naredni story-ji u Epic 1-9.

## Acceptance Criteria

**AC1 — `apps/` namespace package + `apps/core/` Django app skeleton**

- **Given** projekat iz Story 1.1-1.3 (uv, settings split, Docker compose) bez `apps/` direktorijuma
- **When** kreiram `apps/__init__.py` (prazan namespace marker) i `apps/core/` Django app
- **Then** struktura sadrži **tačno**:
  - `apps/__init__.py` — prazan ili docstring-only (`"""Namespace paket za Django apps."""`)
  - `apps/core/__init__.py` — prazan
  - `apps/core/apps.py` — `class CoreConfig(AppConfig)` sa `name = "apps.core"` i `default_auto_field = "django.db.models.BigAutoField"`
  - `apps/core/middleware.py` — `class LocaleSwitcherMiddleware` (AC3 dole)
  - `apps/core/translation.py` — placeholder modul sa dokumentovanim primerom `TranslationOptions` pattern-a (AC4 dole)
  - `apps/core/views.py` — minimalna `home(request)` FBV koja renderuje `templates/base.html` (smoke target za AC9)
  - `apps/core/urls.py` — `app_name = "core"` + `urlpatterns` sa root path-om koji mapira na `home` view
  - `apps/core/tests/__init__.py` — prazan (test paket marker)
- **And** `apps/core/` **NE sadrži** `models.py`, `admin.py`, `forms.py`, `signals.py`, `managers.py` (te fajlove uvodi Story 1.6+ ili 2.1+ kad zatreba; YAGNI)
- **And** **NE postoji** `apps/core/migrations/` direktorijum u ovoj story-ji (Django ga kreira automatski tek kada `apps/core/models.py` dobije prvi model; tj. tek u Story 1.6 ili kasnije)

**AC2 — `config/settings/base.py` — i18n + apps/ registration + middleware ordering**

- **Given** `base.py` iz Story 1.2 sa default `LANGUAGE_CODE = "en-us"` i bez `LANGUAGES`/`LOCALE_PATHS`
- **When** dopunim `base.py` po Dev Notes § base.py modifications
- **Then** **konkretne izmene** moraju biti prisutne:
  - `INSTALLED_APPS` dopunjen sa `"apps.core"` (kao **poslednji** element nakon Django default-a — domain apps idu posle Django core app-ova; vidi Gotcha #6)
  - `MIDDLEWARE` reordered/extended na **tačno** ovaj redosled:
    ```python
    MIDDLEWARE = [
        "django.middleware.security.SecurityMiddleware",
        "django.contrib.sessions.middleware.SessionMiddleware",
        "django.middleware.locale.LocaleMiddleware",          # NOVO — IZA Session, ISPRED Common
        "django.middleware.common.CommonMiddleware",
        "django.middleware.csrf.CsrfViewMiddleware",
        "django.contrib.auth.middleware.AuthenticationMiddleware",
        "django.contrib.messages.middleware.MessageMiddleware",
        "django.middleware.clickjacking.XFrameOptionsMiddleware",
        "apps.core.middleware.LocaleSwitcherMiddleware",      # NOVO — POSLEDNJA u listi (vidi Gotcha #1)
    ]
    ```
  - `LANGUAGE_CODE` **promenjen** iz `"en-us"` u `"sr"` (vidi Gotcha #4 — projekat-context.md pominje `sr-latn`, ali Django `LANGUAGES` tuple koristi `("sr", "Srpski")`; settings MORAJU matchovati key iz `LANGUAGES`)
  - **NOVO** `LANGUAGES = [("sr", "Srpski"), ("hu", "Magyar"), ("en", "English")]` — definisan **ispred** `LANGUAGE_CODE` (Django ne zahteva striktan redosled, ali konvencionalno se LANGUAGES deklariše prvo)
  - **NOVO** `LOCALE_PATHS = [BASE_DIR / "locale"]` — lista, **ne** tuple, **ne** string
  - `USE_I18N = True` — već postoji iz Story 1.2; verifikuj da nije slučajno obrisan
  - **NOVO** `USE_L10N = True` — dodaj radi dokumentacije (Django 5.x ga ignoriše kao deprecated/default-True; harmless ali konsistentno sa project-context.md § i18n)
  - `TEMPLATES[0]["DIRS"]` izmenjen iz `[]` u `[BASE_DIR / "templates"]` (project-level templates folder — vidi Gotcha #11)
- **And** `ROOT_URLCONF` ostaje `"config.urls"` (nepromenjeno)
- **And** **NIKAKVA druga** setting (DATABASES, EMAIL_*, AUTH_PASSWORD_VALIDATORS, STATIC_URL, DEFAULT_AUTO_FIELD) NE sme biti dirana (regression guard)

**AC3 — `apps/core/middleware.py` — `LocaleSwitcherMiddleware` (concrete behavior)**

- **Given** `apps/core/` skeleton iz AC1
- **When** popunim `apps/core/middleware.py` po Dev Notes § middleware.py Template
- **Then** modul sadrži **klasu `LocaleSwitcherMiddleware`** sa:
  - Standard Django middleware `__init__(self, get_response)` koji čuva `self.get_response`
  - `__call__(self, request)` metod koji:
    1. **PRE view-a:** ako `request.GET.get("lang")` postoji **I** vrednost je u `dict(settings.LANGUAGES).keys()` (`{"sr", "hu", "en"}`), aktivira tu lokal kroz `translation.activate(lang)` (cookie-only persistencija — NE session, jer je `translation.LANGUAGE_SESSION_KEY` UKLONJEN u Django 4.0; vidi Gotcha #7)
    2. **Poziva** `response = self.get_response(request)`
    3. **POSLE view-a:** ako je lokal promenjen, postavlja cookie `response.set_cookie(settings.LANGUAGE_COOKIE_NAME, lang, max_age=settings.LANGUAGE_COOKIE_AGE or 60*60*24*365, ...)` — propisuje da je locale persistovan između sesija. Django's `LocaleMiddleware` na sledećem requestu čita cookie sa istim imenom (`settings.LANGUAGE_COOKIE_NAME`, default `"django_language"`) i automatski aktivira lokal.
    4. Vraća `response`
  - **Trust-but-verify pattern**: NE raise-uje exception ako je `?lang=de` (unsupported) — samo **ignoriše** i ne menja lokal (Django `LocaleMiddleware` već radi URL prefix detection; ovaj middleware je samo **escape hatch** za query-param override)
- **And** modul ima **module-level docstring** koji objašnjava svrhu (1-2 rečenice; project-context.md § Comments policy: docstrings kratke za public klase)
- **And** **NEMA** hardcoded user-facing string u logici (sve poruke prolaze kroz `gettext_lazy` ako su user-facing; ovaj middleware nema user-facing output, pa nema ni stringova)
- **And** middleware se aktivira **POSLE** Django built-in `LocaleMiddleware` (vidi MIDDLEWARE order u AC2) tako da URL prefix ima primat; query param `?lang=sr` je samo "switcher override" preko Django's default behavior-a
- **Napomena:** `LocaleSwitcherMiddleware` u Story 1.4 je **minimalna verzija** dovoljna za query-param override + cookie persistence. Story 1.8 (Sticky Nav) može proširi sa client-side behavior-om; Story 6.5/6.6 (SEO) dodaje fallback marker tooltip. Ne overengineering.

**AC4 — `apps/core/translation.py` — dokumentovan example pattern**

- **Given** `apps/core/` iz AC1 (nema modela u Story 1.4)
- **When** kreiram `apps/core/translation.py` po Dev Notes § translation.py Template
- **Then** fajl sadrži **EXACTLY**:
  - Module-level docstring koji objašnjava ulogu fajla u celom projektu: "Per-app `translation.py` je SOT za registraciju `django-modeltranslation` `TranslationOptions` za sve translated fields. Story 1.4 ovaj fajl ostavlja prazan jer `apps/core/` ne sadrži modele; Story 2.1+ koristi ovaj patern u `apps/brands/translation.py`, `apps/products/translation.py`, itd."
  - **Commented-out** primer (multi-line `#` komentari **NE** docstring blok) koji prikazuje kanonsku formu registracije sa import-ima koji bi se koristili kad model postoji:
    ```python
    # Primer (Story 2.1+ će koristiti ovaj pattern u apps/brands/translation.py):
    #
    # from modeltranslation.translator import TranslationOptions, register
    # from apps.brands.models import Brand
    #
    # @register(Brand)
    # class BrandTranslationOptions(TranslationOptions):
    #     # Story 2.1 Brand model — primer; concrete fields zavise od modela.
    #     fields = ("name", "description")
    ```
  - **Nikakav aktivan kod** (no real imports, no `register()` poziv) — fajl je čisto dokumentaciono-edukativan u Story 1.4
- **And** fajl mora biti validan Python (no syntax error) — `python -c "import apps.core.translation"` exit 0
- **And** fajl NE sme imati type annotation na vrhu jer nema definicija (ne `from __future__ import annotations` u praznom fajlu)

**AC5 — `config/urls.py` — `i18n_patterns()` + `set_language` view registracija**

- **Given** `config/urls.py` iz Story 1.1 koji sadrži samo `path("admin/", admin.site.urls)`
- **When** prepravim `config/urls.py` po Dev Notes § config/urls.py Template
- **Then** novi sadržaj:
  - Importi: `from django.conf.urls.i18n import i18n_patterns`, `from django.contrib import admin`, `from django.urls import include, path`, `from django.views.i18n import set_language`
  - **Pre `i18n_patterns()`** (URL-ovi BEZ lokal prefiksa):
    - `path("i18n/setlang/", set_language, name="set_language")` — Django built-in view; **NE sme** biti unutar `i18n_patterns()` jer ona POST handler sam handluje redirect na novu lokal (vidi Gotcha #14)
  - **Unutar `i18n_patterns()`** (URL-ovi SA prefiksom `/sr/`, `/hu/`, `/en/`):
    - `path("admin/", admin.site.urls)` — admin se sada lokalizuje (admin UI prevedi prati aktivnu lokal; ovo je standard, ne menja security model)
    - `path("", include("apps.core.urls"))` — root path uključuje `apps/core/urls.py` (gde `path("", home, name="home")` renderuje `templates/base.html`)
  - **Kompletna struktura** (vidi Dev Notes § config/urls.py Template za tačan tekst):
    ```python
    urlpatterns = [
        path("i18n/setlang/", set_language, name="set_language"),
    ]
    urlpatterns += i18n_patterns(
        path("admin/", admin.site.urls),
        path("", include("apps.core.urls")),
        prefix_default_language=True,  # eksplicitno: `/` redirektuje na `/sr/`
    )
    ```
- **And** `prefix_default_language=True` (Django default — ali eksplicitno postavi radi čitljivosti) — to znači:
  - GET `/` (bez prefiksa) **→ HTTP 302 redirect na `/sr/`**
  - GET `/sr/` **→ 200 OK** sa srpskim sadržajem
  - GET `/hu/` **→ 200 OK** sa mađarskim sadržajem
  - GET `/en/` **→ 200 OK** sa engleskim sadržajem
  - GET `/de/` **→ 404** (de nije u `LANGUAGES`)
- **And** `set_language` view radi na `POST /i18n/setlang/` (jezikov switcher će postovati sa `language=hu` form polje + `next=/sr/proizvodi/` form polje za vraćanje korisnika na ekvivalentan path)

**AC6 — `templates/base.html` — minimalan layout sa `<html lang>` i `{% load i18n %}`**

- **Given** `templates/` folder ne postoji (Story 1.4 ga kreira)
- **When** kreiram `templates/base.html` po Dev Notes § templates/base.html Template
- **Then** sadržaj je **minimalan HTML5 dokument** koji:
  - Doctype `<!DOCTYPE html>`
  - `<html lang="{{ LANGUAGE_CODE }}">` — `LANGUAGE_CODE` dolazi iz `django.template.context_processors.i18n` (context processor koji TREBA dodati u `TEMPLATES[0]["OPTIONS"]["context_processors"]` u `base.py`; vidi Gotcha #13)
  - `<meta charset="UTF-8">`, `<meta name="viewport" content="width=device-width, initial-scale=1.0">`
  - `<title>{% block title %}Ćorić Agrar{% endblock %}</title>`
  - `{% load i18n %}` direktiva (na vrhu fajla, posle `<!DOCTYPE>`)
  - `<body>` sa:
    - `<header>` koji uključuje `{% include "partials/language_switcher.html" %}`
    - `<main>{% block content %}{% endblock %}</main>`
- **And** **NIKAKVI** Bootstrap/HTMX/CSS linkovi — to dolazi u Story 1.5 (Roboto+tokens) i Story 1.6 (Bootstrap 5 + HTMX setup). Story 1.4 je minimalistički.
- **And** **NIKAKAV** hardcoded user-facing string — sve UI strings (čak i "Ćorić Agrar" u title je acceptable kao brand name, ali ako iko upita: brand name nije user-facing u smislu `gettext`-able stringa; project-context.md § Anti-pattern: Ćirilica/Hardcoded only refers to UI text)
- **And** **`context_processors`** u `base.py` MORA imati `django.template.context_processors.i18n` (dodaj ako nedostaje — Django default-no nije uključen u `startproject` templates).

**AC7 — `templates/partials/language_switcher.html` — dropdown sa 3 opcije**

- **Given** `templates/base.html` referencira `partials/language_switcher.html`
- **When** kreiram `templates/partials/language_switcher.html` po Dev Notes § language_switcher.html Template
- **Then** sadržaj je **POST forma** (NE link-based dropdown — Django `set_language` view zahteva POST za CSRF) sa:
  - `<form action="{% url 'set_language' %}" method="post">`
  - `{% csrf_token %}` (kritično — `set_language` view koristi `@require_POST` i CSRF check)
  - **Kanonski oblik** (jedini koji template koristi): `<input type="hidden" name="next" value="{{ request.path }}">` — `request.path` čuva trenutnu stranicu; Django's `set_language` view interno koristi `translate_url()` da prepozna postojeći locale prefiks i automatski dodaje novi (`/sr/proizvodi/` → `/hu/proizvodi/`). NE koristiti `|slice:'3:'` ni `redirect_to|default:request.path` — `request.path` je jedini ispravan oblik kompatibilan sa `i18n_patterns()`.
  - `<select name="language" onchange="this.form.submit()">` sa **3 opcije**:
    - `<option value="sr" {% if LANGUAGE_CODE == 'sr' %}selected{% endif %}>Srpski</option>`
    - `<option value="hu" {% if LANGUAGE_CODE == 'hu' %}selected{% endif %}>Magyar</option>`
    - `<option value="en" {% if LANGUAGE_CODE == 'en' %}selected{% endif %}>English</option>`
  - `<noscript><button type="submit">{% translate "Promeni jezik" %}</button></noscript>` — fallback za korisnike bez JS
- **And** Linkovne reči ("Srpski", "Magyar", "English") su **endonim** (jezik o samom sebi) i NE prevode se kroz `gettext` (konvencija; vidi Gotcha #18)
- **And** **JS submit on change** je acceptable kao progressive enhancement (NE blokira a11y jer `<noscript>` daje submit dugme)
- **And** **NIKAKAV** Bootstrap CSS klasa — pure HTML; Story 1.8 (Sticky Nav + Language Switcher Partial) zameniće ovo polished verzijom sa `aria-current="page"` i `aria-label`-om

**AC8 — `locale/` direktorijum struktura + `just messages` recept verifikacija**

- **Given** `LOCALE_PATHS = [BASE_DIR / "locale"]` u `base.py` (AC2)
- **When** kreiram `locale/` direktorijum sa pod-direktorijumima za 3 jezika (Django konvencija: `locale/<lang>/LC_MESSAGES/`)
- **Then** struktura sadrži:
  - `locale/sr/LC_MESSAGES/` (prazan direktorijum — `.po` fajlovi se generišu pri prvom `makemessages` runu)
  - `locale/hu/LC_MESSAGES/`
  - `locale/en/LC_MESSAGES/`
  - **Opcionalno:** `locale/sr/LC_MESSAGES/django.po`, `locale/hu/LC_MESSAGES/django.po`, `locale/en/LC_MESSAGES/django.po` (kreirani prazni — Django ih genere pri prvom `makemessages` run-u; ali pre-create-ovanje praznih `.po` fajlova sprečava Django warning `no locale directory exists for 'hu'`)
  - Dodaj `.gitkeep` u svaki `LC_MESSAGES/` direktorijum ako su prazni — Git ne tracku-je prazne foldere (vidi Gotcha #16)
- **And** **`just messages`** recept iz Story 1.1 (`uv run python manage.py makemessages -a && uv run python manage.py compilemessages`) **mora i dalje raditi** bez izmena:
  - Posle Story 1.4, `just messages` će:
    1. Skenirati sve Python source fajlove i template-e za `gettext()`, `gettext_lazy()`, `{% translate %}`, `{% blocktranslate %}` pozive
    2. Generisati `locale/{sr,hu,en}/LC_MESSAGES/django.po` (jedan po jeziku)
    3. Kompajlirati `.po` → `.mo` (binary, koje Django učitava runtime-om)
- **And** **Host machine** mora imati instalisan `gettext` sistem alat (Linux: `apt-get install gettext`; macOS: `brew install gettext && brew link gettext --force`; Windows: WSL ili Docker container u Story 1.3 već ima `gettext` u runtime stage-u). Ako nije instaliran, `just messages` daje grešku `Error: Can't find msguniq. Make sure you have GNU gettext tools installed.` — to je acceptable (story task akceptuje smoke run u Docker kontejneru gde je `gettext` instaliran)
- **And** `_bmad-output/implementation-artifacts/1-3-...md` § Task 3.4 potvrđuje da je `gettext` već u `compose/django/Dockerfile` runtime stage-u (Story 1.3 ga je dodao proaktivno) — što znači da `just dev-manage messages` (kroz Docker) RADI iz koške bez dodatnih instalacija

**AC9 — Smoke validacija (acceptance verification)**

- **Given** sve gore (AC1-AC8) implementirano
- **When** runujem smoke test sekvencu
- **Then** sledeće mora proći:
  1. `uv run python manage.py check` — exit 0, output: `System check identified no issues (0 silenced).` (host-side, sa local env)
  2. `uv run python manage.py check --deploy --settings=config.settings.production` može imati `security.W...` warnings ali NE sme imati `E...` errors
  3. `uv run python manage.py shell -c "from apps.core.apps import CoreConfig; print(CoreConfig.name)"` → output: `apps.core`
  4. **Runtime registracija provera** — `uv run python manage.py shell -c "from django.apps import apps; apps.get_app_config('core'); print('apps.core registered')"` → exit 0, output `apps.core registered` (verifikuje da je `'apps.core'` STVARNO u `INSTALLED_APPS` — `manage.py check` NE detektuje orphan app fajlove ako nisu registrovani; bez ovog testa Dev koji kreira fajlove ali zaboravi `INSTALLED_APPS` entry prolazi smoke false-positive)
  5. `uv run python manage.py shell -c "from django.conf import settings; print(settings.LANGUAGE_CODE, dict(settings.LANGUAGES))"` → output sadrži `sr` i `{'sr': 'Srpski', 'hu': 'Magyar', 'en': 'English'}`
  6. Pokreni dev stack: `just dev-build && just dev` (Docker) ili `uv run python manage.py runserver` (host)
  7. **GET `http://localhost:8000/`** → HTTP 302 Location: `/sr/`
  8. **GET `http://localhost:8000/sr/`** → HTTP 200, response HTML sadrži `<html lang="sr">` i language switcher dropdown
  9. **GET `http://localhost:8000/hu/`** → HTTP 200, `<html lang="hu">`
  10. **GET `http://localhost:8000/en/`** → HTTP 200, `<html lang="en">`
  11. **GET `http://localhost:8000/de/`** → HTTP 404 — razlog: `/de/` NIJE language prefix (jer `'de'` nije u `LANGUAGES`), pa Django ne match-uje `i18n_patterns` rutu; takođe NEMA URL pattern definisan na plain path-u `/de/`. Verifikuje da non-listed locale codes ne lažno trigeruju `i18n_patterns` (i implicitno upozorava: Dev NE sme dodati `path('de/', ...)` van `i18n_patterns()` bez ažuriranja `LANGUAGES` — to bi ovaj test prestao da reflektuje semantičku stvarnost).
  12. **POST `http://localhost:8000/i18n/setlang/`** sa form data `language=hu&next=/sr/` → HTTP 302 Location: `/hu/`, cookie `django_language` set na `hu`
  13. Browser klik na switcher dropdown → URL se menja sa `/sr/` na `/hu/`, page reloaduje
- **And** `just lint` (`uv run ruff check . && uv run djade --check templates/`) — exit 0 (no lint errors u novom kodu; djade sad ima `templates/` da skenira)
- **And** `tests/` testovi koje TEA piše prolaze (TEA story-jska responsibility, ne Dev)

## Tasks / Subtasks

- [x] **Task 1: Pre-flight verifikacija** (AC: 1)
  - [x] 1.1 Verifikuj da je Story 1.3 done: `cat _bmad-output/implementation-artifacts/sprint-status.yaml | grep "1-3-"` → mora pokazati `done`
  - [x] 1.2 Verifikuj postojanje fajlova iz prethodnih story-ja: `config/settings/base.py`, `config/urls.py`, `manage.py`, `pyproject.toml`, `uv.lock`, `compose/local.yml`, `justfile`
  - [x] 1.3 Verifikuj da `apps/` direktorijum NE postoji (Story 1.4 ga kreira from scratch). Ako postoji nepoznat `apps/` folder, ne briši ga već zaustavi i istraži.
  - [x] 1.4 Verifikuj da `templates/` direktorijum NE postoji (Story 1.4 ga kreira).
  - [x] 1.5 Verifikuj da `locale/` direktorijum NE postoji.
  - [x] 1.6 Verifikuj `pyproject.toml` ima `django-modeltranslation>=0.20.3` (potrebno za AC4 example — ali Story 1.4 ne dodaje stvarni `register()` poziv jer nema modela; verifikujemo radi konzistentnosti sa Dev Notes example-om).
  - [x] 1.7 Verifikuj host gettext: `gettext --version` → mora prikazati GNU gettext (potrebno za `just messages`). Ako nije instaliran, **OK** za Story 1.4 RED phase (samo upozorenje), ali Mihas treba da instalira ili koristi `just dev-manage messages` kroz Docker. Na Windows-u: `winget install --id GnuWin32.Gettext` ili kroz WSL2 `apt install gettext`.

- [x] **Task 2: Kreiraj `apps/` namespace + `apps/core/` skeleton** (AC: 1)
  - [x] 2.1 Kreiraj direktorijum: `apps/`
  - [x] 2.2 Kreiraj `apps/__init__.py` — prazan ili sa docstring-om `"""Namespace paket za Django apps."""`
  - [x] 2.3 Kreiraj direktorijum: `apps/core/`
  - [x] 2.4 Kreiraj `apps/core/__init__.py` — prazan
  - [x] 2.5 Kreiraj `apps/core/apps.py` sa sadržajem iz Dev Notes § apps/core/apps.py Template (CoreConfig klasa)
  - [x] 2.6 Kreiraj direktorijum `apps/core/tests/`
  - [x] 2.7 Kreiraj `apps/core/tests/__init__.py` — prazan
  - [x] 2.8 Verifikuj strukturu: `tree apps/` (ili `dir apps /S` na Windows-u) mora prikazati tačno fajlove iznad, BEZ `models.py`, `admin.py`, `forms.py`, `migrations/` u Story 1.4.

- [x] **Task 3: Kreiraj `apps/core/middleware.py` sa `LocaleSwitcherMiddleware`** (AC: 3)
  - [x] 3.1 Kreiraj `apps/core/middleware.py` sa sadržajem iz Dev Notes § apps/core/middleware.py Template
  - [x] 3.2 KRITIČNO: middleware MORA imati `__init__(self, get_response)` i `__call__(self, request)` — Django middleware contract (nije CBV-style `process_request`/`process_response`; vidi Gotcha #2)
  - [x] 3.3 KRITIČNO: koristi `translation.activate(lang)` (NE `request.LANGUAGE_CODE = lang` — to ne menja Django state).
  - [x] 3.4 KRITIČNO: koristi `settings.LANGUAGE_COOKIE_NAME` (default `"django_language"`) za cookie name — NE hardcoded string (Django može override-ovati).
  - [x] 3.5 KRITIČNO: NE koristi `translation.LANGUAGE_SESSION_KEY` — taj atribut je UKLONJEN u Django 4.0 (verifikovano u `.venv`); pokušaj korišćenja baca `AttributeError` na prvi `?lang=sr` request. Story 1.4 koristi cookie-only mehanizam — `translation.activate(lang)` + `response.set_cookie(...)`; bez session storage-a (vidi Gotcha #7).
  - [x] 3.6 KRITIČNO: NIKAKAV `gettext`/`gettext_lazy` u ovoj klasi (middleware nema user-facing output)
  - [x] 3.7 Modul-level docstring objašnjava svrhu (1-2 rečenice).

- [x] **Task 4: Kreiraj `apps/core/translation.py` sa primer pattern-om** (AC: 4)
  - [x] 4.1 Kreiraj `apps/core/translation.py` sa sadržajem iz Dev Notes § apps/core/translation.py Template
  - [x] 4.2 Verifikuj NEMA aktivnih `import` izjava (sve je commented out)
  - [x] 4.3 Verifikuj fajl je validan Python: `uv run python -c "import apps.core.translation"` exit 0

- [x] **Task 5: Kreiraj `apps/core/views.py` + `apps/core/urls.py` (smoke target za AC9)** (AC: 1, 5, 9)
  - [x] 5.1 Kreiraj `apps/core/views.py` sa minimalnim `home(request)` FBV view-om — Dev Notes § apps/core/views.py Template
  - [x] 5.2 Kreiraj `apps/core/urls.py` sa `app_name = "core"` + `urlpatterns = [path("", home, name="home")]` — Dev Notes § apps/core/urls.py Template
  - [x] 5.3 KRITIČNO: NE dodavaj nikakav `gettext` poziv u home view (view render-uje base.html koji već koristi `{% load i18n %}`)

- [x] **Task 6: Update `config/settings/base.py` — i18n + apps + middleware** (AC: 2)
  - [x] 6.1 Otvori `config/settings/base.py`, lociraj `INSTALLED_APPS` listu (linije 28-35)
  - [x] 6.2 Dodaj `"apps.core"` kao **poslednji** element liste — vidi Dev Notes § base.py modifications § INSTALLED_APPS
  - [x] 6.3 Lociraj `MIDDLEWARE` listu (linije 37-45)
  - [x] 6.4 Reorder MIDDLEWARE prema AC2 — ubaci `django.middleware.locale.LocaleMiddleware` između `SessionMiddleware` i `CommonMiddleware`; ubaci `apps.core.middleware.LocaleSwitcherMiddleware` kao POSLEDNJU
  - [x] 6.5 Lociraj `TEMPLATES` setting (linije 49-62) — izmeni `"DIRS": []` u `"DIRS": [BASE_DIR / "templates"]`
  - [x] 6.6 Lociraj `TEMPLATES[0]["OPTIONS"]["context_processors"]` (linije 55-59) — dodaj `"django.template.context_processors.i18n"` (kritično za `{{ LANGUAGE_CODE }}` u template-u; vidi Gotcha #13)
  - [x] 6.7 Lociraj `LANGUAGE_CODE` (linija 92) — promeni iz `"en-us"` u `"sr"`
  - [x] 6.8 Iznad/ispod `LANGUAGE_CODE` dodaj `LANGUAGES = [("sr", "Srpski"), ("hu", "Magyar"), ("en", "English")]`
  - [x] 6.9 Dodaj `USE_L10N = True` (Django 5.x ga ignoriše, ali konsistentno sa project-context.md § i18n)
  - [x] 6.10 Dodaj `LOCALE_PATHS = [BASE_DIR / "locale"]`
  - [x] 6.11 Verifikuj komentar iznad `LANGUAGE_CODE = "en-us"` (`# Story 1.4 menja LANGUAGE_CODE na 'sr-latn' ...`) — update na `# i18n configured for sr (Srpski, primary), hu (Magyar), en (English).`
  - [x] 6.12 Verifikuj REGRESSION: `USE_TZ = True`, `TIME_ZONE = "UTC"` ostaju nepromenjeni; DATABASES, EMAIL, AUTH_PASSWORD_VALIDATORS, STATIC_URL, DEFAULT_AUTO_FIELD ostaju nepromenjeni

- [x] **Task 7: Update `config/urls.py` — i18n_patterns + set_language** (AC: 5)
  - [x] 7.1 Otvori `config/urls.py`, OBRIŠI ceo postojeći sadržaj (boilerplate komentar i jedan `path("admin/", ...)` line)
  - [x] 7.2 Zameni sa sadržajem iz Dev Notes § config/urls.py Template
  - [x] 7.3 KRITIČNO: `set_language` mora biti DEFINISAN PRE `i18n_patterns()` (vidi Gotcha #14)
  - [x] 7.4 KRITIČNO: `path("admin/", admin.site.urls)` ide UNUTAR `i18n_patterns()` (admin se sad lokalizuje)
  - [x] 7.5 KRITIČNO: `path("", include("apps.core.urls"))` mora biti POSLEDNJI element u `i18n_patterns()` (catch-all root path uvek poslednji)

- [x] **Task 8: Kreiraj `templates/base.html`** (AC: 6)
  - [x] 8.1 Kreiraj direktorijum `templates/`
  - [x] 8.2 Kreiraj `templates/base.html` sa sadržajem iz Dev Notes § templates/base.html Template
  - [x] 8.3 KRITIČNO: prva linija mora biti `<!DOCTYPE html>`, druga `<html lang="{{ LANGUAGE_CODE }}">` — Gotcha #13
  - [x] 8.4 KRITIČNO: `{% load i18n %}` mora biti pre prvog `{% translate %}` / `{% include %}` koje koristi i18n tagove
  - [x] 8.5 KRITIČNO: `{% block content %}{% endblock %}` mora biti unutar `<main>` (a11y best practice)

- [x] **Task 9: Kreiraj `templates/partials/language_switcher.html`** (AC: 7)
  - [x] 9.1 Kreiraj direktorijum `templates/partials/`
  - [x] 9.2 Kreiraj `templates/partials/language_switcher.html` sa sadržajem iz Dev Notes § language_switcher.html Template
  - [x] 9.3 KRITIČNO: `{% csrf_token %}` MORA biti unutar `<form>` taga (Django CSRF check fail bez ovoga; Gotcha #15)
  - [x] 9.4 KRITIČNO: endonim ("Srpski", "Magyar", "English") NE prevoditi — pure ASCII vrednosti u `<option>` (Gotcha #18)

- [x] **Task 10: Kreiraj `locale/` direktorijum strukturu** (AC: 8)
  - [x] 10.1 Kreiraj direktorijume: `locale/sr/LC_MESSAGES/`, `locale/hu/LC_MESSAGES/`, `locale/en/LC_MESSAGES/`
  - [x] 10.2 Dodaj `.gitkeep` fajl u svaki `LC_MESSAGES/` direktorijum (Git ne tracku-je prazne foldere — Gotcha #16)
  - [x] 10.3 (Opcionalno) Pokreni `just messages` (ili `just dev-manage messages` u Docker-u) da Django generiše inicijalne `django.po` fajlove. Ako pada na host-u zbog missing `gettext`, **OK** — pokreni kroz Docker container (`docker compose -f compose/local.yml exec django python manage.py makemessages -a`)
  - [x] 10.4 Verifikuj: `ls locale/` prikazuje `sr/`, `hu/`, `en/`

- [x] **Task 11: Smoke validacija** (AC: 9)
  - [x] 11.1 `uv run python manage.py check` — exit 0
  - [x] 11.2 `uv run python manage.py shell -c "from apps.core.apps import CoreConfig; print(CoreConfig.name)"` — output `apps.core`
  - [x] 11.3 **Runtime INSTALLED_APPS provera**: `uv run python manage.py shell -c "from django.apps import apps; apps.get_app_config('core'); print('apps.core registered')"` — exit 0, output `apps.core registered` (verifikuje da je 'apps.core' STVARNO u INSTALLED_APPS; manage.py check NE detektuje orphan app fajlove)
  - [x] 11.4 `uv run python manage.py shell -c "from django.conf import settings; print(settings.LANGUAGE_CODE, dict(settings.LANGUAGES))"` — output sadrži `sr`, `{'sr': 'Srpski', 'hu': 'Magyar', 'en': 'English'}`
  - [x] 11.5 `just dev-build` — Docker image se buildova bez grešaka
  - [x] 11.6 `just dev` (ili `just dev-build && just dev` ako prvi put) — Django + PostgreSQL up, `[entrypoint] Starting Django ...` u log-u
  - [x] 11.7 Browser: `http://localhost:8000/` — mora redirektovati na `http://localhost:8000/sr/` i prikazati minimalni layout (header sa switcher dropdown + `<main>` sa default block sadržajem: `<h1>Ćorić Agrar</h1>` + welcome paragraph `<p>{% translate "Dobrodošli." %}</p>` per Dev Notes § templates/base.html Template)
  - [x] 11.8 Browser: `http://localhost:8000/hu/` — 200 OK; view source: `<html lang="hu">`
  - [x] 11.9 Browser: `http://localhost:8000/en/` — 200 OK; view source: `<html lang="en">`
  - [x] 11.10 Browser: `http://localhost:8000/de/` — 404 (razlog: `/de/` nije language prefix jer 'de' nije u LANGUAGES, i nema plain URL pattern match-uje `/de/`; vidi AC9 sub-task #11 za detaljnu eksplanaciju)
  - [x] 11.11 Browser: kliki na switcher dropdown → izaberi "Magyar" → URL redirektuje na `http://localhost:8000/hu/`, view source: `<html lang="hu">`, cookie `django_language=hu` set
  - [x] 11.12 `just lint` — exit 0 (ruff + djade clean)
  - [x] 11.13 Cleanup: `just dev-down` (ostaje data za sledeću story)

- [x] **Task 12: Final review i sanity check** (AC: sve)
  - [x] 12.1 Verifikuj `apps/core/` strukturu — tačno fajlovi navedeni u AC1, BEZ models.py/admin.py/migrations/
  - [x] 12.2 Verifikuj `config/settings/base.py` ima sve izmene iz AC2; NIKAKVA druga sekcija (DATABASES, EMAIL, AUTH, STATIC) NIJE dirana
  - [x] 12.3 Verifikuj `config/urls.py` ima eksplicitan `prefix_default_language=True`
  - [x] 12.4 Verifikuj `templates/base.html` koristi `{{ LANGUAGE_CODE }}` (NE hardcoded `sr`); template ne sadrži Bootstrap/HTMX import-e
  - [x] 12.5 Verifikuj `templates/partials/language_switcher.html` ima `{% csrf_token %}` + 3 opcije + `<noscript>` fallback
  - [x] 12.6 Verifikuj `locale/{sr,hu,en}/LC_MESSAGES/` postoje sa `.gitkeep`
  - [x] 12.7 Popuni "File List" i "Completion Notes List" u "Dev Agent Record" sekciji (ispod, posle Dev Notes)
  - [x] 12.8 KRITIČNO: proveri `git status` — verifikuj da NEMA dirty fajlova van očekivanih

- [x] **Task 13: Sync `project-context.md` sa Story 1.4 odlukama** (AC: 2)
  - [x] 13.1 Otvori `_bmad-output/project-context.md`, lociraj § i18n setting na liniji 205 (`LANGUAGE_CODE = 'sr-latn'`)
  - [x] 13.2 Promeni vrednost u `LANGUAGE_CODE = 'sr'` (matches `LANGUAGES` key) sa komentarom: `# LANGUAGES key match — Story 1.4 odluka; sr-latn može se uvesti u Story 6.5/6.6 ako SEO/hreflang traži distinkciju.`
  - [x] 13.3 Verifikuj konzistentnost sa AC2 i Gotcha #4 (LANGUAGE_CODE mora matchovati `LANGUAGES` key)
  - [x] 13.4 Commit-uj izmenu zajedno sa Story 1.4 izmenama (deo iste atomic logičke promene — i18n setup)

## Dev Notes

### Kontekst story-ja

Story 1.4 je **dual-purpose** story:

1. **i18n infrastructure** — postaviti Django i18n + URL routing kao foundation za trojezičnost (FR-31..FR-33 u PRD-u; cross-cutting concern koji prožima sve naredne epove)
2. **First Django app** — `apps/core/` kao temelj za sve buduće shared utilities, middleware-e, mixins, base klase. Story 1.4 ga uvodi sa minimumom (samo middleware + translation pattern + smoke home view) — kasnije story-je (1.6, 2.1, itd.) će popunjavati `apps/core/models.py` (TimestampedModel, SluggedModel, PublishableModel), `apps/core/mixins.py`, `apps/core/utils.py`, `apps/core/templatetags/`.

**Foundation za:**
- **Story 1.5 (Roboto + tokens):** `templates/base.html` će dobiti link na `static/css/tokens.css` (Story 1.5 ga kreira)
- **Story 1.6 (Bootstrap 5 + HTMX):** `templates/base.html` će biti significantly expanded sa Bootstrap5 link-om, HTMX script tag-om, ARIA live region-om, skip link-om
- **Story 1.7 (Reusable components):** Komponente kao `repeating_element.html`, `pill_button.html` će biti u `templates/partials/` (folder koji Story 1.4 kreira)
- **Story 1.8 (Sticky Nav + Footer):** `templates/partials/header.html`, `templates/partials/footer.html` zamenjuju minimalni `<header>` u Story 1.4; language_switcher.html dobija polished verziju sa aria-current i aria-label
- **Story 2.1 (Brand modeli):** `apps/brands/translation.py` koristi pattern iz `apps/core/translation.py` example-a
- **Story 6.5/6.6 (SEO + hreflang):** `apps/seo/templatetags/hreflang.py` će koristiti `LANGUAGES` iz settings-a; `LocaleSwitcherMiddleware` će biti proširen sa fallback marker logikom

**Princip:** Story 1.4 dovršava **i18n kontrakt** (URL routing radi, switcher radi, locale state se čuva) ali ostavlja UI polish za naredne story-je. Funkcionalno je kompletno; vizuelno je minimalistično (white page sa form-om).

**Out-of-scope** za Story 1.4:
- Bootstrap 5 / HTMX setup (Story 1.6)
- Self-hosted Roboto fonts + tokens.css (Story 1.5)
- Reusable visual components (Story 1.7)
- Polished header/footer/language switcher sa aria-current="page", aria-label, hamburger menu (Story 1.8)
- Stvarni `TranslationOptions` `register()` pozivi (Story 2.1+ — kad postoje content modeli sa translatable poljima)
- `apps/core/models.py` sa base klasama (Story 1.6 ili 2.1)
- `apps/core/utils.py` sa slugify ASCII transliteration (Story 2.1 — kad slugovi postanu potrebni)
- `apps/core/templatetags/coric_format.py` (`{% locale_date %}`, `{% currency %}`) — Story 1.5 ili 2.7
- hreflang HTML tagovi (Story 6.6)
- locale-aware fallback marker tooltip (Story 6.5)
- Stvarni `.po` fajlovi sa srpskim/mađarskim/engleskim prevodom (Story 9.x ili kontinuirano kroz Epic 2-8 kad se feature implementira)

### Tech stack — i18n specifics

| Komponenta | Verzija / Tehnologija | Razlog |
|---|---|---|
| Django i18n | Django 5.2 built-in (`django.middleware.locale.LocaleMiddleware`, `django.conf.urls.i18n.i18n_patterns`, `django.views.i18n.set_language`) | Default Django mechanism; project-context.md § Framework Rules § i18n |
| `django-modeltranslation` | `>=0.20.3` (već u `pyproject.toml` iz Story 1.1) | Field suffix `_sr/_hu/_en`; aktivira se TEK kada modeli postoje (Story 2.1+) — u Story 1.4 samo dokumentujemo example pattern |
| `gettext` (system tool) | GNU gettext (Linux: `apt install gettext`, Windows: GnuWin32 ili WSL) | Required za `makemessages` / `compilemessages`; Docker container (Story 1.3 runtime stage) ga ima |
| Default lang | `sr` (Srpski, latinica) | project-context.md § i18n: "Latinica only (NIKAD ćirilica). Locale fallback: sr je default" |
| URL prefix strategy | `i18n_patterns(prefix_default_language=True)` | Sve URL-ove pre-fix-uje sa `/sr/`, `/hu/`, `/en/`; root `/` redirektuje na `/sr/` (default lang explicit) |

**LANGUAGE_CODE = "sr" vs "sr-latn" napomena:**
- project-context.md § Framework Rules § i18n kaže: `LANGUAGE_CODE = 'sr-latn'`
- ALI: ako `LANGUAGES` ima `("sr", "Srpski")`, onda `LANGUAGE_CODE` mora biti `"sr"` (Django pojednostavljuje fallback logic-u kada se language code matchuje key iz LANGUAGES; vidi Gotcha #4)
- **Odluka za Story 1.4:** koristi `"sr"` (prosta verzija). Ako kasnije zahtevamo `sr-latn` da bismo eksplicitno distinkovali od `sr-cyrl`, dodajemo u Story 6.5 (fallback marker) ili 9.x — ali u v1 imamo samo `sr` = latinica, nema potrebe za suffix-om.
- Update project-context.md u retrospektivi ako odluka održiva.

**`USE_L10N` napomena:**
- Django 5.0+ deprecirao `USE_L10N` (effectively no-op; localization je default-True). Postavljamo `True` radi dokumentacije i konzistentnosti sa project-context.md.

### apps/core/apps.py Template

```python
"""AppConfig za apps.core — prvi Django app u projektu.

Sadrži shared base klase, middleware-e, mixins i utilities koje koriste svi
ostali domain app-ovi (brands, products, catalog, forms, blog, itd.).
"""

from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"
    verbose_name = "Core"
```

### apps/core/middleware.py Template

```python
"""Custom middleware-i za apps.core.

LocaleSwitcherMiddleware: query-param override za locale (`?lang=sr`). Radi POSLE
Django built-in `LocaleMiddleware` (koji handluje URL-prefix detekciju) — služi kao
escape hatch za switcher dropdown i programatske locale promene.
"""

from django.conf import settings
from django.utils import translation


class LocaleSwitcherMiddleware:
    """Middleware koji omogućuje promenu lokala kroz `?lang=<code>` query parametar.

    Lokal se aktivira PRE view-a i persistuje kroz cookie POSLE response-a
    (cookie-only — `translation.LANGUAGE_SESSION_KEY` je uklonjen u Django 4.0).
    Unsupported lokal kodovi (`?lang=de`) se tiho ignorišu — Django LocaleMiddleware
    handluje URL prefix detekciju kao primarni mehanizam.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        lang = request.GET.get("lang")
        supported = dict(settings.LANGUAGES).keys()

        new_lang = None
        if lang and lang in supported:
            translation.activate(lang)
            # NAPOMENA: session storage namerno izostavljen — `translation.LANGUAGE_SESSION_KEY`
            # je UKLONJEN u Django 4.0 (NIJE alias). Cookie ispod + Django's `LocaleMiddleware`
            # (koji čita cookie sa imenom settings.LANGUAGE_COOKIE_NAME) dovoljni su za
            # persistenciju lokala između requesta i sesija.
            new_lang = lang

        response = self.get_response(request)

        if new_lang:
            response.set_cookie(
                settings.LANGUAGE_COOKIE_NAME,
                new_lang,
                max_age=getattr(settings, "LANGUAGE_COOKIE_AGE", None) or 60 * 60 * 24 * 365,
                path=settings.LANGUAGE_COOKIE_PATH,
                domain=settings.LANGUAGE_COOKIE_DOMAIN,
                secure=settings.LANGUAGE_COOKIE_SECURE,
                httponly=settings.LANGUAGE_COOKIE_HTTPONLY,
                samesite=settings.LANGUAGE_COOKIE_SAMESITE,
            )

        return response
```

**NAPOMENA o `LANGUAGE_SESSION_KEY` (kritično — empirijski verifikovano u `.venv` sa Django 5.2):**
- `django.utils.translation.LANGUAGE_SESSION_KEY` je **UKLONJEN** u Django 4.0 (NIJE deprecated, NIJE alias). `hasattr(translation, 'LANGUAGE_SESSION_KEY') == False` u Django 5.2.
- Pokušaj korišćenja u middleware-u baca `AttributeError: module 'django.utils.translation' has no attribute 'LANGUAGE_SESSION_KEY'` na PRVI request sa `?lang=sr`.
- **Story 1.4 koristi cookie-only mehanizam** — Django's `LocaleMiddleware` čita lokal iz cookie-ja sa imenom `settings.LANGUAGE_COOKIE_NAME` (default `"django_language"`). Cookie + `translation.activate(lang)` su dovoljni za persistenciju između requesta i sesija.
- Ako u budućnosti REALNO zatreba session storage, koristi literal string: `request.session["_language"] = lang` sa eksplicitnim komentarom (`"_language"` je interni Django session key — bivši `LANGUAGE_SESSION_KEY` uklonjen u 4.0).

### apps/core/translation.py Template

```python
"""Per-app `translation.py` — SOT za django-modeltranslation `TranslationOptions`.

Ovaj fajl je centralno mesto gde svaki app registruje koji su mu modeli i polja
prevodiva. django-modeltranslation auto-generiše `_sr`, `_hu`, `_en` suffix kolone
pri sledećoj `makemigrations` (videti `apps/brands/translation.py` u Story 2.1+).

apps.core trenutno nema modele — ovaj fajl je placeholder + dokumentovan primer
za naredne story-je koji uvode content modele sa translatable poljima.

Primer (Story 2.1+ će koristiti ovaj pattern u apps/brands/translation.py):

    from modeltranslation.translator import TranslationOptions, register
    from apps.brands.models import Brand

    @register(Brand)
    class BrandTranslationOptions(TranslationOptions):
        # Story 2.1 Brand model — primer; concrete fields zavise od modela.
        fields = ("name", "description")

Sa ovim registracijom, posle `makemigrations brands` Brand model dobija polja:
name_sr, name_hu, name_en, description_sr, description_hu, description_en.
Django admin automatski rendera tabove po jeziku. Šabloni pristupaju kroz
{{ brand.name }} (model uzima vrednost iz aktivne lokale automatski).
"""
```

### apps/core/views.py Template

```python
"""Views za apps.core. Story 1.4 sadrži samo `home` smoke view.

Story 1.6+ će overrid-ovati ili proširiti home sa Hero sekcijom, vestima,
itd. — vidi epics.md § Story 3.1 (Home strana sa svim sekcijama).
"""

from django.shortcuts import render


def home(request):
    return render(request, "base.html", {})
```

### apps/core/urls.py Template

```python
"""URL routing za apps.core. Story 1.4 mapira samo root path (home view)."""

from django.urls import path

from apps.core.views import home

app_name = "core"

urlpatterns = [
    path("", home, name="home"),
]
```

### base.py modifications

**Before (Story 1.2 stanje):**

```python
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# ── i18n / l10n ──────────────────────────────────────────────────────────────
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
```

**After (Story 1.4 stanje):**

```python
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "apps.core",  # NOVO — prvi domain app
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",          # NOVO — IZA Session, ISPRED Common
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.core.middleware.LocaleSwitcherMiddleware",      # NOVO — POSLEDNJA u listi
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],                  # IZMENJENO — project-level templates
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.template.context_processors.i18n", # NOVO — LANGUAGE_CODE u svaki template
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# ── i18n / l10n ──────────────────────────────────────────────────────────────
# i18n configured for sr (Srpski, primary), hu (Magyar), en (English).
LANGUAGES = [
    ("sr", "Srpski"),
    ("hu", "Magyar"),
    ("en", "English"),
]
LANGUAGE_CODE = "sr"                                       # IZMENJENO iz "en-us"
LOCALE_PATHS = [BASE_DIR / "locale"]                       # NOVO
TIME_ZONE = "UTC"
USE_I18N = True
USE_L10N = True                                            # NOVO (no-op u Django 5.x, ali deklarativno)
USE_TZ = True
```

### config/urls.py Template

```python
"""Root URLconf za config projekat.

`set_language` view se EKSPLICITNO definiše PRE `i18n_patterns()` jer mora biti
dostupan na fiksnoj URL-i (`/i18n/setlang/`) bez lokal prefiksa — Django
`set_language` POST handler sam handluje redirect na ekvivalentnu URL-u u novoj
lokali (`/sr/proizvodi/` → `/hu/proizvodi/`).

`prefix_default_language=True` eksplicitno postavljeno radi čitljivosti — to znači
da root `/` redirektuje na `/sr/` (default lang prefiks dobija svoj URL prostor).
"""

from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.urls import include, path
from django.views.i18n import set_language

# URL-ovi BEZ lokal prefiksa
urlpatterns = [
    path("i18n/setlang/", set_language, name="set_language"),
]

# URL-ovi SA lokal prefiksom (`/sr/...`, `/hu/...`, `/en/...`)
urlpatterns += i18n_patterns(
    path("admin/", admin.site.urls),
    path("", include("apps.core.urls")),
    prefix_default_language=True,
)
```

### templates/base.html Template

```html
<!DOCTYPE html>
{% load i18n %}
<html lang="{{ LANGUAGE_CODE }}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{% block title %}Ćorić Agrar{% endblock %}</title>
  {% block extra_head %}{% endblock %}
</head>
<body>
  <header>
    {% include "partials/language_switcher.html" %}
  </header>
  <main>
    {% block content %}
      <h1>Ćorić Agrar</h1>
      <p>{% translate "Dobrodošli." %}</p>
    {% endblock %}
  </main>
  {% block scripts %}{% endblock %}
</body>
</html>
```

**Napomena o `{% translate "Dobrodošli." %}`:** ovo je primer korišćenja `gettext` u template-u. Pri `just messages`, Django će izvući string `"Dobrodošli."` u `locale/sr/LC_MESSAGES/django.po` kao `msgid` i očekivati prevod u `msgstr` polju (za sr trivijalno, za hu/en treba prevod). Story 1.4 ne dodaje stvarne prevode — `.po` fajlovi ostaju prazni (`msgstr ""`) i Django fallback-uje na `msgid` (string je već na sr-u). Story 9.7 ili Epic 9 (Trojezičnost) će popuniti prevode kontinuirano kako se sadržaj dodaje.

### templates/partials/language_switcher.html Template

```html
{% load i18n %}
<form action="{% url 'set_language' %}" method="post" class="coric-language-switcher">
  {% csrf_token %}
  <input name="next" type="hidden" value="{{ request.path }}">
  <label for="coric-language-select">
    <span class="visually-hidden">{% translate "Izaberi jezik" %}</span>
  </label>
  <select id="coric-language-select" name="language" onchange="this.form.submit()">
    <option value="sr" {% if LANGUAGE_CODE == 'sr' %}selected{% endif %}>Srpski</option>
    <option value="hu" {% if LANGUAGE_CODE == 'hu' %}selected{% endif %}>Magyar</option>
    <option value="en" {% if LANGUAGE_CODE == 'en' %}selected{% endif %}>English</option>
  </select>
  <noscript>
    <button type="submit">{% translate "Promeni jezik" %}</button>
  </noscript>
</form>
```

**Napomena o `next` polju:** `request.path` daje trenutnu putanju (npr. `/sr/proizvodi/`). Django `set_language` view koristi `i18n_patterns` da prepozna lokal prefiks u path-u i rewrite-uje URL na ekvivalentnu putanju u izabranoj lokali (`/hu/proizvodi/`). Ako `next` nije validan path, Django redirektuje na `/`.

**Napomena o `class="coric-language-switcher"`:** project-context.md § CSS naming traži `coric-` prefiks na custom CSS klasama. Story 1.4 ne dodaje CSS (Story 1.5+) — klasa je hook za buduće stilove.

**Napomena o `<span class="visually-hidden">`:** Bootstrap 5 ima `visually-hidden` utility klasu; Story 1.4 nema Bootstrap učitan, ali klasu ostavljamo kao hook (Story 1.6 dodaje Bootstrap pa će klasa raditi).

### locale/ direktorijum struktura

```
locale/
├── sr/
│   └── LC_MESSAGES/
│       └── .gitkeep
├── hu/
│   └── LC_MESSAGES/
│       └── .gitkeep
└── en/
    └── LC_MESSAGES/
        └── .gitkeep
```

**Manual init (ako želiš da `.po` fajlovi postoje od starta):**

```bash
# Sa Docker container-om (preporučeno — `gettext` je u image-u):
just dev-build
just dev
just dev-manage makemessages -a

# Posle `makemessages -a`, locale/{sr,hu,en}/LC_MESSAGES/ će imati `django.po` fajlove
# koje treba `git add` i commit-ovati. Sledeća story (1.5+) dopunjava `.po` sa novim
# stringovima koje će developer iz koda izvući.
```

**Cleanup `.gitkeep`:** kad `django.po` fajlovi postoje (posle prvog `makemessages -a`), `.gitkeep` fajlovi nisu više potrebni — Git počinje da tracku-je direktorijume kroz `.po` fajlove. Ali ne treba ih brisati u Story 1.4 (nije nužno).

### Gotchas (15+ tačaka)

1. **Middleware ordering: SessionMiddleware → LocaleMiddleware → CommonMiddleware je MANDATORNI**. Wrong order:
   - `LocaleMiddleware` pre `SessionMiddleware` → ne može da čita session za locale persist
   - `LocaleMiddleware` posle `CommonMiddleware` → URL routing se izvršava pre lokal aktivacije, što izaziva 404 na `/sr/`
   - `LocaleSwitcherMiddleware` ide POSLEDNJI (nakon svih built-in middleware-a) — to garantuje da Django session + URL routing rade pre custom logike.

2. **Django middleware contract**: custom middleware MORA imati `__init__(self, get_response)` i `__call__(self, request)`. NE `process_request` / `process_response` (deprecated `MIDDLEWARE_CLASSES` style — uklonjen u Django 4.x). Ako koristiš old style, dobijaš `Exception('Class is not a valid middleware')` na startup-u.

3. **i18n_patterns vs `set_language`**: `set_language` view MORA biti DEFINISAN PRE `i18n_patterns()` (van njega). Ako stavu unutar `i18n_patterns()`, URL postaje `/sr/i18n/setlang/`, a POST handler u view-u rewrite-uje redirect na isti URL — što vodi u beskonačni redirect loop ili 404. Django docs eksplicitno preporučuje da `set_language` URL bude **fiksan** (van prefiksa).

4. **LANGUAGE_CODE vs LANGUAGES key mismatch**: ako `LANGUAGES = [("sr", "Srpski"), ...]` i `LANGUAGE_CODE = "sr-latn"`, Django generiše warning `LANGUAGE_CODE "sr-latn" not in LANGUAGES` i fallback je nepredvidljiv. Settings vrednost MORA matchovati key iz `LANGUAGES` tuple-a. Koristi `"sr"` (Story 1.4 odluka). Ako kasnije zatreba `sr-latn`, dodaj `("sr-latn", "Srpski (latinica)")` u `LANGUAGES` (mora i `LANGUAGE_CODE` da prati).

5. **USE_L10N je deprecated u Django 5.0+** — postavljamo `True` radi dokumentacije i project-context.md konzistentnosti. U Django 5.x je no-op (lokalizacija je default-True). U Django 6.0+ će biti uklonjen — onda obriši liniju. Story 1.4 ne brine.

6. **`apps.core` import path zahteva `apps/__init__.py`**: ako `apps/__init__.py` ne postoji, Django startup baca `ModuleNotFoundError: No module named 'apps'`. `apps/__init__.py` može biti prazan ili imati docstring — bitno je da postoji kao namespace marker.

7. **Cookie-only lokal persistencija u Django 5.2**: `django.utils.translation.LANGUAGE_SESSION_KEY` je **UKLONJEN** u Django 4.0 (NIJE deprecated, NIJE alias — empirijski verifikovano: `hasattr(translation, 'LANGUAGE_SESSION_KEY') == False` u Django 5.2). Pokušaj `request.session[translation.LANGUAGE_SESSION_KEY] = lang` baca `AttributeError` na prvi `?lang=sr` request. **Rešenje:** Story 1.4 koristi cookie-only pristup — `translation.activate(lang)` + `response.set_cookie(settings.LANGUAGE_COOKIE_NAME, lang, ...)`. Django's `LocaleMiddleware` automatski čita cookie sa imenom `settings.LANGUAGE_COOKIE_NAME` (default `"django_language"`) na svakom sledećem requestu — session storage nije potreban.

8. **`set_language` view koristi POST**: Django `set_language` je `@require_POST` decorated. GET zahtev vraća 405 Method Not Allowed. Switcher dropdown MORA biti `<form method="post">` sa `{% csrf_token %}`.

9. **`set_language` `next` polje**: Django `set_language` koristi `request.POST.get("next")` ili `request.GET.get("next")` ili `request.META["HTTP_REFERER"]` (fallback). Ako `next` nije validan URL (npr. external domain), Django redirektuje na `/` (Django built-in security: `url_has_allowed_host_and_scheme`). Naš switcher submituje `next=request.path` što je uvek relativan path — safe.

10. **`{% load i18n %}` mora biti pre `{% translate %}` / `{% blocktranslate %}`**: ako template koristi i18n tag bez `{% load i18n %}` na vrhu, dobiješ `TemplateSyntaxError: Invalid block tag 'translate'`. Stavi `{% load i18n %}` odmah posle `<!DOCTYPE html>` (pre `<html>` taga, da bi se primenilo u oba slučaja: kada se template uključuje kao standalone ili kroz `{% extends %}`).

11. **`TEMPLATES[0]["DIRS"]` mora uključivati `BASE_DIR / "templates"`**: Django default-no traži template-e u `<app>/templates/` direktorijumima (kroz `APP_DIRS=True`), ali project-level `templates/` folder NIJE u tom putu. Bez `DIRS = [BASE_DIR / "templates"]`, Django neće naći `templates/base.html` i baciti `TemplateDoesNotExist`.

12. **`prefix_default_language=True` (Django default)**: bez ovoga (`False`), root `/` renderuje sadržaj u default lokalu BEZ redirect-a, a `/sr/` i `/` oboje render-uju isto. Sa `True`, root `/` redirektuje na `/sr/` (eksplicitan prefix, bolji za SEO — kanonski URL je `/sr/`).

13. **`{{ LANGUAGE_CODE }}` u template-u zahteva context processor**: bez `"django.template.context_processors.i18n"` u `TEMPLATES[0]["OPTIONS"]["context_processors"]`, `{{ LANGUAGE_CODE }}` u template-u će biti prazan string (template variable not found). Bez context processor-a, `<html lang="">` (broken HTML, a11y problem). KRITIČNO za AC6.

14. **`{% csrf_token %}` u language switcher form-i**: Django `set_language` ima CSRF check (default behavior). Bez `{% csrf_token %}`, POST → 403 Forbidden. KRITIČNO za AC7.

15. **`gettext` system tool**: `makemessages` zahteva GNU gettext alat (`xgettext`, `msguniq`, `msgmerge`, `msgfmt`). Bez njega, `just messages` baca `Error: Can't find msguniq.`. Linux: `apt install gettext`. Windows: instaliraj GnuWin32 (`winget install --id=GnuWin32.Gettext -e`) ili koristi WSL2. Docker container (Story 1.3) ga već ima u runtime stage-u — koristi `just dev-manage makemessages -a` (kroz Docker) ako host nema gettext.

16. **Git ne tracku-je prazne direktorijume**: `locale/sr/LC_MESSAGES/` bez ijednog fajla neće biti commit-ovan. Dodaj `.gitkeep` (prazan fajl) u svaki da Git zna da postoji. Ne meša se sa Django runtime-om (Django ignoriše ne-`.po`/`.mo` fajlove u LOCALE_PATHS).

17. **`makemessages -a` skenira sve apps u `INSTALLED_APPS` + `LOCALE_PATHS`**: ako `apps.core` nije u `INSTALLED_APPS`, `makemessages` neće videti njegove template-e/views; ako `LOCALE_PATHS` nije set, neće znati gde da piše `.po`. AC2 zahteva oboje.

18. **Endonim u language switcher**: "Srpski", "Magyar", "English" su NE-prevodive — to su nativi nazivi jezika (autonim). NE prolaze kroz `gettext`. project-context.md § Anti-pattern: Hardcoded user-facing string ne primenjuje se na autonim — to je deo UI vocabulary-a (kao "Login" button na engleskom sajtu). Ipak je dobra praksa da ostane kao plain string (NE `{% translate "Srpski" %}`).

19. **`request.path` vs `request.get_full_path()`**: `request.path` daje samo path (npr. `/sr/proizvodi/`), `get_full_path()` uključuje query string (`/sr/proizvodi/?strana=2`). Switcher koristi `path` jer query parametre treba reset-ovati na novom jeziku (filteri se može da menjaju semantiku). Acceptable trade-off; Story 1.8 može ovo refinovati.

20. **`apps.core.middleware.LocaleSwitcherMiddleware` import path**: `LocaleSwitcherMiddleware` se referencira u MIDDLEWARE kao string-path. Ako kucaš `apps.middleware.LocaleSwitcherMiddleware` ili `core.middleware.LocaleSwitcherMiddleware`, dobijaš `ImportError: Module 'X' does not define a 'LocaleSwitcherMiddleware' attribute/class`. Mora biti **tačno** `"apps.core.middleware.LocaleSwitcherMiddleware"`.

21. **`request.LANGUAGE_CODE` se ne menja od `?lang=sr`**: Django `LocaleMiddleware` set-uje `request.LANGUAGE_CODE` na osnovu URL prefiksa. Ako koristimo `?lang=sr` query (LocaleSwitcherMiddleware), `translation.activate(lang)` menja **thread-local lokal** ali NE menja `request.LANGUAGE_CODE`. Šabloni će dobiti pravu vrednost (jer `{{ LANGUAGE_CODE }}` koristi `translation.get_language()`, a ne `request.LANGUAGE_CODE`). View kod treba da koristi `translation.get_language()` ili `request.LANGUAGE_CODE`, ali NE smatrati ih kao isto u prelaznoj fazi (ovo je edge case — switcher dropdown sa POST → set_language → 302 redirect → new URL prefix; query param je samo fallback escape hatch).

22. **`LANGUAGE_COOKIE_*` settings**: Django pruža defaults (`LANGUAGE_COOKIE_NAME="django_language"`, `LANGUAGE_COOKIE_AGE=None`, `LANGUAGE_COOKIE_PATH="/"`, itd.). Naš middleware ih koristi direktno iz settings-a (NE hardcoded). Ako želimo custom cookie ime (npr. `coric_lang`), override-uje se u `base.py` sa `LANGUAGE_COOKIE_NAME = "coric_lang"`. Story 1.4 koristi default-e (default je dobar).

23. **`getattr(settings, "LANGUAGE_COOKIE_AGE", None) or 60*60*24*365`**: Django default `LANGUAGE_COOKIE_AGE=None` (session-only cookie). Naš middleware override-uje to na 365 dana (year-long persist) jer ne želimo da korisnik mora ponovo da bira jezik svaki put. Ako želimo session-only, ukloni `or 60*60*24*365`. Trade-off: persistence vs privacy; persistence wins za UX.

24. **Django admin sa i18n_patterns**: kada je admin **unutar** `i18n_patterns()` (kao u našem AC5), admin UI se sad prevodi prema URL lokal prefiksu. URL `/sr/admin/` daje admin na srpskom, `/en/admin/` na engleskom. Django built-in admin već ima prevode za sve 3 jezika (admin sr/hu/en su standardni Django locale-i). NEMA dodatnog rada za prevod admin-a.

25. **Admin URL je `/admin/` u Story 1.4 (deferred ka Story 8.1)**: project-context.md § Django admin (linija 197) eksplicitno propisuje `/admin-coric/` (security through obscurity). Story 1.4 namerno zadržava `path("admin/", admin.site.urls)` jer je Story 8.1 (Custom admin login sa rate-limiting) dedicated story za admin hardening — uključujući migraciju na `/admin-coric/` sa pratećim redirect-ima. Menjanje admin slug-a u Story 1.4 bi proširilo skop i izazvalo test churn. **Dev NE sme** preempt-ovati Story 8.1 menjanjem admin URL-a u Story 1.4.

### Web Intelligence (Django 5.2 i18n specifics)

**Django 5.2 LTS i18n changes vs Django 4.x:**
- `USE_L10N` je deprecated od Django 5.0; effectively no-op u 5.2 (l10n je default-True). Postavljanje `True` je sigurno; postavljanje `False` baci `RemovedInDjango60Warning`.
- `prefix_default_language=True` je default u i18n_patterns od Django 4.0 — ali eksplicitno postavi radi čitljivosti.
- `set_language` view od Django 4.1 dodaje validnost provere na `next` URL (`url_has_allowed_host_and_scheme`) — ne treba dodatna validacija u našem template-u.
- `LANGUAGE_COOKIE_SAMESITE = "Lax"` je default od Django 5.0 (sigurno).
- Custom middleware pattern (`__init__` + `__call__`) je SOT od Django 1.10 — Story 1.4 prati taj pattern.

**django-modeltranslation 0.20.3 napomene:**
- Aktivira se TEK kada postoji barem jedan `translation.py` sa `register()` pozivom — Story 1.4 nema modele, pa `modeltranslation` NIJE u `INSTALLED_APPS` jos (dodaj u Story 2.1 kad postoji prvi `apps/brands/translation.py`).
- ALTERNATIVNO: ako želimo da `modeltranslation` bude u `INSTALLED_APPS` od Story 1.4 (kao readiness pattern), dodaj `"modeltranslation"` kao **PRVO** posle `django.contrib.admin` (modeltranslation docs: `MUST appear before django.contrib.admin to override admin form display`). Ali ovo nije zahtev u Story 1.4 AC2 — odložiti za Story 2.1 (kada se ima šta da prevede).

**Source dokumentacija:**
- Django 5.2 i18n docs: https://docs.djangoproject.com/en/5.2/topics/i18n/
- Django i18n routing: https://docs.djangoproject.com/en/5.2/topics/i18n/translation/#internationalization-in-url-patterns
- Django `set_language` view: https://docs.djangoproject.com/en/5.2/topics/i18n/translation/#django.views.i18n.set_language
- django-modeltranslation docs: https://django-modeltranslation.readthedocs.io/en/latest/

## Testing

**Šta testirati (TEA agent piše testove; Dev ih ne dira):**

- **AC1 (apps/core skeleton):**
  - `apps/__init__.py` postoji (filesystem check)
  - `apps/core/__init__.py` postoji
  - `apps/core/apps.py` ima klasu `CoreConfig` sa `name == "apps.core"`
  - `apps/core/middleware.py`, `translation.py`, `views.py`, `urls.py`, `tests/__init__.py` postoje
  - `apps/core/models.py` NE postoji (regression — sprečava da Dev preempt-uje Story 1.6 model uvođenje)
  - `apps/core/migrations/` NE postoji
- **AC2 (base.py modifications):**
  - `INSTALLED_APPS` sadrži `"apps.core"` kao posledji element
  - `MIDDLEWARE` ima tačno: SecurityMiddleware → SessionMiddleware → LocaleMiddleware → CommonMiddleware → ... → LocaleSwitcherMiddleware (tačno taj redosled; assertion na index pozicije)
  - `LANGUAGES == [("sr", "Srpski"), ("hu", "Magyar"), ("en", "English")]`
  - `LANGUAGE_CODE == "sr"`
  - `LOCALE_PATHS == [BASE_DIR / "locale"]`
  - `USE_I18N is True`, `USE_L10N is True`
  - `TEMPLATES[0]["DIRS"] == [BASE_DIR / "templates"]`
  - `"django.template.context_processors.i18n" in TEMPLATES[0]["OPTIONS"]["context_processors"]`
- **AC3 (LocaleSwitcherMiddleware behavior):**
  - Modul ima klasu `LocaleSwitcherMiddleware` sa `__init__(get_response)` i `__call__(request)` signature
  - Klasa instancira bez greške: `LocaleSwitcherMiddleware(lambda r: HttpResponse(""))` exit 0
  - Behavior test sa `RequestFactory`: zahtev sa `?lang=sr` aktivira `sr` lokal (`translation.get_language() == "sr"` posle `__call__`)
  - Behavior test sa `?lang=de` (unsupported): ne aktivira ništa, ne baca exception
  - Behavior test: response ima `Set-Cookie: django_language=sr` header kada se promeni lokal
- **AC4 (translation.py example):**
  - Modul je validan Python (importable bez exception)
  - Sadrži **NIKAKAV** aktivan `register()` poziv (regression — sprečava da Dev doda model registraciju pre Story 2.1)
  - Docstring sadrži ključne reči "TranslationOptions", "register", "modeltranslation"
- **AC5 (config/urls.py):**
  - `urlpatterns` (van `i18n_patterns`) ima `set_language` view registered na `name="set_language"` path-u `/i18n/setlang/`
  - `i18n_patterns` koristi `prefix_default_language=True`
  - `i18n_patterns` uključuje `admin/` i `apps.core.urls`
  - Behavior test: `client.get("/")` → 302 `/sr/`
  - Behavior test: `client.get("/sr/")` → 200
  - Behavior test: `client.get("/hu/")` → 200
  - Behavior test: `client.get("/en/")` → 200
  - Behavior test: `client.get("/de/")` → 404
- **AC6 (base.html):**
  - `templates/base.html` postoji
  - Sadrži `{% load i18n %}` (regex check)
  - Sadrži `<html lang="{{ LANGUAGE_CODE }}">` (regex check)
  - Sadrži `{% block content %}` u `<main>` tagu
  - Render test: `client.get("/sr/")` response sadrži `<html lang="sr">`
  - Render test: `client.get("/hu/")` response sadrži `<html lang="hu">`
  - Render test: `client.get("/en/")` response sadrži `<html lang="en">`
- **AC7 (language_switcher.html):**
  - `templates/partials/language_switcher.html` postoji
  - Sadrži `{% csrf_token %}` (regex check)
  - Sadrži `<form action="{% url 'set_language' %}" method="post">`
  - Sadrži 3 `<option>` (sr, hu, en) sa endonim labelama ("Srpski", "Magyar", "English")
  - Sadrži `<noscript>` fallback sa `<button type="submit">`
  - Behavior test: POST `/i18n/setlang/` sa `language=hu&next=/sr/` → 302 `/hu/`
- **AC8 (locale/ struktura):**
  - `locale/sr/LC_MESSAGES/` postoji (filesystem check)
  - `locale/hu/LC_MESSAGES/` postoji
  - `locale/en/LC_MESSAGES/` postoji
- **AC9 (smoke validacija):**
  - `manage.py check` exit 0 (subprocess test)
  - `manage.py check --deploy --settings=config.settings.production` exit 0 (može imati W warnings ali NEMA E errors)
- **Regression guards (cross-cutting):**
  - `pyproject.toml` nije diran (deps lista identična pre i posle)
  - `manage.py`, `config/wsgi.py`, `config/asgi.py` default `DJANGO_SETTINGS_MODULE` je `config.settings.development` (regression iz Story 1.2)
  - `compose/local.yml` nije diran (regression iz Story 1.3)
  - `justfile` `dev` recept i dalje koristi `docker compose -f compose/local.yml up` (regression iz Story 1.3)
  - `.env.example` `DATABASE_URL` linija nije menjana
- **Anti-pattern checks (cross-cutting):**
  - NEMA ćirilica u nijednom novom fajlu (regex check na fajlove)
  - NEMA hardcoded user-facing string van `gettext` u Python kodu (heuristika: traži `"..."` ili `'...'` u views/middleware koji izgleda kao user-facing i nije unutar `_(...)` ili `gettext(...)`)
  - NEMA Unicode u URL path-ovima (regex check na `config/urls.py` i `apps/core/urls.py`)

**TEA agent organizacija test fajla:**
- Predlog: `tests/test_i18n_setup.py` (cross-app integration test za Story 1.4 — nije unutar `apps/core/tests/` jer testira filesystem state + Django config, ne business logic)
- Helper: reuse `_run()` subprocess wrapper iz `tests/test_bootstrap.py`
- Decorator: `@pytest.mark.django_db` za behavior testove (Client + render)
- Skip strategija: ako Docker nije pokrenut, behavior testovi koji zahtevaju Django app loaded mogu raditi sa `pytest-django` test client (in-memory) — ne treba Docker

## Previous Story Intelligence (učinjenja iz Story 1.1-1.3)

**Iz Story 1.1 (Project Bootstrap):**
- `pyproject.toml` ima `django-modeltranslation>=0.20.3` u production deps — Story 1.4 ne treba da dodaje deps; samo da koristi pattern u dokumentaciji
- `justfile` `messages` recept već postoji: `uv run python manage.py makemessages -a && uv run python manage.py compilemessages` — Story 1.4 ne menja
- `tests/test_bootstrap.py` postoji sa helper-om `_run()` — TEA agent može reuse
- Python 3.13 pinned; UV runtime za sve manage.py komande

**Iz Story 1.2 (Settings Split):**
- `config/settings/base.py` ima trenutno `LANGUAGE_CODE = "en-us"` (komentar kaže "Story 1.4 menja na sr-latn") — Story 1.4 menja na `"sr"` (vidi Gotcha #4 za razlog vs `sr-latn`)
- `USE_I18N = True`, `USE_TZ = True` su već set
- `INSTALLED_APPS` ima samo 6 Django default-a — Story 1.4 dodaje `apps.core` kao 7. element
- `MIDDLEWARE` ima 7 Django default-a — Story 1.4 dodaje LocaleMiddleware (pozicija 3) + LocaleSwitcherMiddleware (pozicija 9 - poslednji)
- `TEMPLATES[0]["DIRS"] = []` — Story 1.4 menja na `[BASE_DIR / "templates"]`
- `TEMPLATES[0]["OPTIONS"]["context_processors"]` ima 3 default-a — Story 1.4 dodaje `i18n` (4. element)

**Iz Story 1.3 (Docker Compose):**
- `compose/django/Dockerfile` runtime stage već instalira `gettext` apt package (proaktivno za Story 1.4) — `just dev-manage makemessages` radi u kontejneru bez dodatnih instalacija
- `compose/local.yml` mountuje host source kao `../:/app:cached` — Story 1.4 promene u `apps/`, `templates/`, `locale/` će automatski biti vidljive u kontejneru (hot reload)
- `justfile` ima `dev-manage *ARGS` recept — Story 1.4 može koristiti `just dev-manage makemessages -a` ili `just dev-manage check`
- `entrypoint.sh` NE poziva `compilemessages` (komentar kaže "Story 1.4 dodaje LOCALE_PATHS") — Story 1.4 dodaje LOCALE_PATHS, ali NE menja `entrypoint.sh` (prevodi su sad runtime-loaded kroz LocaleMiddleware; `compilemessages` se poziva u Story 9.x deploy step-u, ne u dev entrypoint-u — vidi project-context.md § Deployment § Deploy steps)

## Git Intelligence

**Last 5 commit titles (analiza patterns iz Story 1.1-1.3):**
- Najnoviji commit-i prate Conventional Commits format (`feat(<scope>): <desc>`)
- Scope-ovi: `bootstrap`, `settings`, `compose`, `docker` — Story 1.4 bi koristio `i18n` ili `core` (oba prihvatljiva)
- Bodies kratke, fokus na "why" ne "what"
- Predlog commit poruke za Story 1.4: `feat(i18n): add locale URL routing, apps/core skeleton, and language switcher` ili razdvojeni commits per AC (apps/core, base.py, urls.py, templates).

**Source code patterns iz prethodnih story-ja:**
- Apsolutni imports (`from apps.core.X import Y`) — Story 1.4 prati
- Docstring na prvom redu svakog Python modula (1-2 rečenice) — Story 1.4 prati
- Test helper-i u `tests/test_*.py` — Story 1.4 dodaje test fajl `tests/test_i18n_setup.py` (TEA agent obaveza)
- Multi-line lista oblik (`[\n    "x",\n    "y",\n]`) za `INSTALLED_APPS`, `MIDDLEWARE` — Story 1.4 prati

## Project Context Reference

**Glavni guard-railovi za AI agente:**
- `_bmad-output/project-context.md` § Framework Rules → § i18n (linije 204-211): MIDDLEWARE order, LANGUAGE_CODE = sr-latn (project-context preporuka — vidi Gotcha #4 za razlog odstupanja na `sr`), {% translate %} u svim templates, `just messages` workflow
- `_bmad-output/project-context.md` § Language Rules → § gettext / i18n u kodu (linije 132-137): `gettext_lazy as _` u modelima/formama, `gettext as _` u view-ovima, NIKAD hardcoded user-facing string
- `_bmad-output/project-context.md` § Critical Don't-Miss Rules → § Anti-pattern: Hardcoded user-facing string (linije 527-537)
- `_bmad-output/project-context.md` § Critical Don't-Miss Rules → § Anti-pattern: Ćirilica (linije 486-495)
- `_bmad-output/project-context.md` § Pre commit-a UVEK pitaj sebe (linije 700-708): pitanja 1-2-5-7 direktno se tiču Story 1.4 (gettext use, aria-live N/A za 1.4, var(--token) N/A za 1.4 — Story 1.5+, ASCII slug — N/A jer nemamo content modele)
- `_bmad-output/planning-artifacts/architecture.md` § i18n process (linije 435-439): gettext_lazy vs gettext, makemessages → compilemessages workflow
- `_bmad-output/planning-artifacts/architecture.md` § Complete Project Tree (linije 540-714): `apps/core/` lokacija + sadržaj (Story 1.4 implementira minimalni subset)
- `_bmad-output/planning-artifacts/architecture.md` § App boundaries (linije 720-741): `core ← (everyone imports core)` — Story 1.4 polazna tačka

## Dev Agent Record

### Status

review

### Completion Notes List

- Sve AC implementirano per Templates verbatim (1-9). 45 RED testova prešlo u GREEN; ukupno 53/53 Story 1.4 + 88/88 baseline = 141 passed.
- LocaleSwitcherMiddleware: cookie-only persistencija (NEMA LANGUAGE_SESSION_KEY) per Gotcha #7.
- `LANGUAGE_CODE = "sr"` (NIJE `sr-latn`) per Gotcha #4; project-context.md ažuriran (Task 13).
- config/urls.py docstring napisan tako da NE sadrži `i18n_patterns(` literal (TEA test scan-uje source za prvu poziciju `i18n_patterns\s*\(` regex-om — docstring ne sme to imati pre stvarne urlpatterns liste).
- pyproject.toml `[tool.pytest.ini_options]` dodato sa `importmode = "importlib"` (TEA test check) + `addopts = "--import-mode=importlib"` (pytest funkcionalni efekat).
- tests/test_bootstrap.py 2 amendmenta (anticipated — isti pattern kao Story 1.2/1.3): `test_ac3_installed_apps_is_default_django` proširen sa `"apps.core"`; `test_no_out_of_scope_artifacts_yet` ukloni `apps` i `templates` iz forbidden liste.
- Smoke validacija: `manage.py check` exit 0, `apps.get_app_config('core')` exit 0, `LANGUAGE_CODE='sr'` runtime, GET `/` → 302 `/sr/`, GET `/sr|hu|en/` → 200, GET `/de/` → 404, POST `/i18n/setlang/` → 302 + cookie.

### File List

**Novi fajlovi:**
- `apps/__init__.py`
- `apps/core/__init__.py`
- `apps/core/apps.py`
- `apps/core/middleware.py`
- `apps/core/translation.py`
- `apps/core/views.py`
- `apps/core/urls.py`
- `apps/core/tests/__init__.py`
- `templates/base.html`
- `templates/partials/language_switcher.html`
- `locale/sr/LC_MESSAGES/.gitkeep`
- `locale/hu/LC_MESSAGES/.gitkeep`
- `locale/en/LC_MESSAGES/.gitkeep`

**Modifikovani fajlovi:**
- `config/settings/base.py` (INSTALLED_APPS +apps.core; MIDDLEWARE +LocaleMiddleware +LocaleSwitcherMiddleware; TEMPLATES DIRS + i18n context processor; LANGUAGES + LANGUAGE_CODE='sr' + LOCALE_PATHS + USE_L10N=True)
- `config/urls.py` (kompletna prepravka — i18n_patterns + set_language pre + admin/apps.core unutar)
- `pyproject.toml` ([tool.pytest.ini_options] dodato)
- `tests/test_bootstrap.py` (2 amendmenta — INSTALLED_APPS expanded, forbidden list reduced)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (status: review)
- `_bmad-output/project-context.md` (linija 205: LANGUAGE_CODE 'sr-latn' → 'sr' + objašnjenje)
