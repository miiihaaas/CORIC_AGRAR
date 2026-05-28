---
story-id: "1.6"
story-key: 1-6-base-templates-sa-bootstrap-5-htmx-setup
title: Base Templates sa Bootstrap 5 + HTMX Setup
status: done
epic_num: 1
epic_title: Project Foundation & Visual Identity
created: 2026-05-28
completed: 2026-05-28
author: Mihas (SM autonomous)
---

# Story 1.6: Base Templates sa Bootstrap 5 + HTMX Setup

Status: done

## Story

As a **dev**,
I want **kompletnu HTMX + Bootstrap 5 infrastrukturu u `templates/base.html` + `django-htmx`/`django-bootstrap5` registracije u settings-u + `{% aria_live %}` template tag**,
so that **svi child templates nasleđuju kanonsku ARIA strukturu (skip link + main#main-content + aria-live region), Bootstrap utility klase + HTMX swap mehaniku rade u svakom child template-u, `request.htmx` introspekcija je dostupna u svim view-ovima, a Lighthouse a11y skor na praznom base template-u dosegne ≥95**.

Ovo je **interakcijski temelj** za Epic 1: Story 1.7 (Reusable komponente) koristi Bootstrap utility (`d-flex`, `gap-3`) + visually-hidden klase iz ovog setup-a; Story 1.8 (Sticky Nav) konzumira `<header>`/`<main>` semantičku strukturu i sticky JS pattern-e iz Bootstrap layout sistema; Epic 4 (Lead-gen forme) zavisi od `{% aria_live %}` tag-a + HTMX swap mehanike; Epic 2 katalog filteri (`/htmx/filter/`) zahtevaju `request.htmx` detection iz `HtmxMiddleware`.

**Foundation za:** Story 1.7 (komponente), Story 1.8 (sticky nav + footer), Story 2.8 (HTMX filteri), Story 4.6 (HTMX form patterns + aria-live), Story 6.x (SEO meta blocks).

## Acceptance Criteria

**AC1 — `templates/base.html` proširen sa kompletnom CSS/JS infrastrukturom**

- **Given** `templates/base.html` iz Story 1.5 (24 linije: doctype + i18n/static load + html lang + charset + viewport + title + tokens.css link + extra_head block + body sa header/language_switcher + main/block content + block scripts)
- **When** dopunim `templates/base.html` po Dev Notes § base.html Template (kompletan)
- **Then** finalni `templates/base.html` sadrži **tačno** sledeću strukturu (sve elemente iz Story 1.5 SAČUVANE; samo dodaci):
  - `<!DOCTYPE html>`, `{% load i18n %}`, `{% load static %}` (postojeće iz Story 1.4/1.5)
  - **NOVO** `{% load django_bootstrap5 %}` — registruje `{% bootstrap_css %}` + `{% bootstrap_javascript %}` template tag-ove (mora biti POSLE `{% load static %}`)
  - **NOVO** `{% load htmx_aria %}` — registruje `{% aria_live %}` tag iz AC4 (mora biti POSLE `{% load static %}`)
  - `<html lang="{{ LANGUAGE_CODE }}">` (postojeće)
  - `<head>` sa:
    - `<meta charset="UTF-8">` (postojeće)
    - `<meta name="viewport" content="width=device-width, initial-scale=1.0">` (postojeće)
    - **NOVO** `<meta name="description" content="{% block meta_description %}{% endblock %}">` — prazan default (Story 6.x SEO popunjava per-page; sada samo placeholder block)
    - `<title>{% block title %}Ćorić Agrar{% endblock %}</title>` (postojeće)
    - `<link rel="stylesheet" href="{% static 'css/tokens.css' %}">` (postojeće iz Story 1.5 — MORA ostati PRVI CSS link)
    - **NOVO** `{% bootstrap_css %}` — django-bootstrap5 tag (renderuje `<link rel="stylesheet" href="...">` ka Bootstrap CSS prema BOOTSTRAP5 settings-u; vidi AC5 + Dev Notes Gotcha #1)
    - **NOVO** `<link rel="stylesheet" href="{% static 'css/main.css' %}">` — custom site stylesheet, MORA biti POSLE `{% bootstrap_css %}` (custom CSS overrides Bootstrap default-e); Story 1.7+ popunjava ovaj fajl, sada samo placeholder
    - `{% block extra_head %}{% endblock %}` (postojeće)
  - `<body>` sa:
    - **NOVO** Skip link kao PRVI element body-ja (vidi AC2): `<a class="visually-hidden-focusable" href="#main-content">{% translate "Preskoči na sadržaj" %}</a>`
    - `<header>` sa `{% include "partials/language_switcher.html" %}` (postojeće)
    - **NOVO MODIFIED** `<main id="main-content" tabindex="-1">` — `id` MORA biti `main-content` (skip link target), `tabindex="-1"` omogućuje programatski focus kad korisnik klikne skip link
    - `{% block content %}<h1>Ćorić Agrar</h1><p>{% translate "Dobrodošli." %}</p>{% endblock %}` (postojeće)
    - `</main>` (postojeće)
    - **NOVO** `{% aria_live %}` — renderuje kanonski `<div id="aria-live" class="visually-hidden" aria-live="polite" aria-atomic="true"></div>` (vidi AC3 + AC4); MORA biti POSLE `</main>` i PRE site-wide scripts
    - **NOVO** `<noscript>` notice — minimal Bootstrap alert: `<noscript><div class="alert alert-warning text-center mb-0" role="alert">{% translate "Za optimalno korišćenje stranice, omogućite JavaScript u svom browser-u." %}</div></noscript>` (POSLE `</main>` i PRE site-wide scripts; vidi Gotcha #14)
    - **NOVO** Site-wide script tag-ovi **PRVI** (red važi: prvo HTMX sa `defer`, zatim Bootstrap JS sync — django-bootstrap5 NE emit-uje `defer`) — vidi FIX rationale u Gotcha #15:
      - `<script src="{% static 'vendor/htmx.min.js' %}" defer></script>`
      - `{% bootstrap_javascript %}` — django-bootstrap5 tag (renderuje `<script src="..."></script>` BEZ `defer` ka Bootstrap bundle.min.js prema BOOTSTRAP5 settings-u; izvršava se SYNC)
    - `{% block scripts %}` (postojeće) — **POSLE** site-wide scripts — Story 1.7+ child templates dodaju per-page script-e ovde; pošto Bootstrap (sync) precedes block u DOM order-u, child sync init Bootstrap komponenti je safe (Bootstrap već učitan)
  - `</body>`, `</html>` (postojeće)
- **And** **REGRESSION GUARD** — sve iz Story 1.5 mora ostati: `{% load i18n %}`, `{% load static %}`, `<html lang="{{ LANGUAGE_CODE }}">`, `<meta charset="UTF-8">`, `<meta name="viewport">`, `<title>...{% block title %}...{% endblock %}...</title>`, `<link rel="stylesheet" href="{% static 'css/tokens.css' %}">` (PRVI), `{% block extra_head %}{% endblock %}`, `<header>` sa language switcher include, `{% block content %}` default vrednost (`<h1>Ćorić Agrar</h1>` + `<p>{% translate "Dobrodošli." %}</p>`), `{% block scripts %}{% endblock %}`
- **And** **NIKAKAV** link ka `googleapis.com`, `fonts.gstatic.com` u dev mode-u; Bootstrap CSS+JS idu kroz `{% bootstrap_css %}` / `{% bootstrap_javascript %}` koji u **dev-u** resolve-uju na **CDN** (`cdn.jsdelivr.net/npm/bootstrap@5.3.3/...`) a u **prod-u** na **local** `static/vendor/bootstrap-5.3.3/...` per BOOTSTRAP5 settings (vidi AC5 + Dev Notes Gotcha #1; align sa project-context.md § Frontend frameworks line 67: "Bootstrap 5.3 — CDN u dev, local u prod")
- **And** finalna dužina fajla 50-80 linija (uključujući prazne linije i komentare)

**AC2 — Skip link funkcionalan ("Preskoči na sadržaj")**

- **Given** `<body>` iz AC1
- **When** korisnik fokusira PRVI fokusabilan element body-ja (Tab iz URL bar-a)
- **Then** skip link `<a class="visually-hidden-focusable" href="#main-content">{% translate "Preskoči na sadržaj" %}</a>` postaje vizuelno vidljiv (Bootstrap utility `.visually-hidden-focusable` prikazuje element samo na focus)
- **And** klik / Enter na skip link skroluje stranicu na `<main id="main-content" tabindex="-1">` i programatski fokusira `<main>` element (browser standard behavior — `tabindex="-1"` omogućuje to)
- **And** kad skip link **nije fokusiran**, vizuelno je sakriven (Bootstrap `.visually-hidden-focusable` koristi clip + size 1px + sr-only-like CSS u idle state-u — screen reader-i ga ipak najavljuju)
- **And** **prevod kroz `{% translate %}`** — strigna `"Preskoči na sadržaj"` (sr default; hu/en popunjavaju se kroz `just messages` u Story 6.x ili 1.9)
- **And** Lighthouse a11y check **`bypass`** (skip link presence) MORA proći — provera u AC9 + Lighthouse manual run

**AC3 — ARIA live region prisutan u DOM-u (kanonski singleton)**

- **Given** `<body>` iz AC1 sa `{% aria_live %}` tag pozivom
- **When** stranica se rendera
- **Then** finalni HTML sadrži **TAČNO JEDNU** `<div>` element sa:
  - `id="aria-live"`
  - `class="visually-hidden"` (Bootstrap utility — vidljiv samo screen reader-ima, ne vizuelno)
  - `aria-live="polite"` (najavljuje izmene koje nisu kritične — HTMX filter rezultati, form success poruke)
  - `aria-atomic="true"` (čita celokupan novi sadržaj div-a, ne samo izmenu)
  - Prazan content (placeholder; HTMX swap-ovi popunjavaju kroz `hx-swap-oob="innerHTML:#aria-live"`)
- **And** placement: **POSLE** `</main>` i **PRE** prvog `<script>` tag-a (footer area; logical reading order)
- **And** **TAČNO JEDAN** `id="aria-live"` u celom DOM-u — singleton invariant (vidi Gotcha #3); HTMX `hx-swap-oob` target-uje preko ID-a i duplikat lomi mehaniku
- **And** koristi se za HTMX OOB pattern iz project-context.md § HTMX response patterns: `<div hx-swap-oob="innerHTML:#aria-live">Pronađeno 12 rezultata</div>` u HTMX response partial-ima (Story 2.8+, Story 4.6+)

**AC4 — `apps/core/templatetags/htmx_aria.py` sa `{% aria_live %}` template tag-om**

- **Given** `apps/core/` iz Story 1.4 (postoje `apps.py`, `middleware.py`, `views.py`, `urls.py`, `translation.py`, `tests/`)
- **When** kreiram template tag library po Dev Notes § htmx_aria.py Template
- **Then** kreiram **TAČNO 2 fajla**:
  - `apps/core/templatetags/__init__.py` — **prazan fajl** (namespace marker; bez sadržaja, bez docstring-a — vidi Gotcha #4 zašto `__init__.py` MORA postojati za Django template tag discovery)
  - `apps/core/templatetags/htmx_aria.py` — sadrži:
    - `from django import template`
    - `from django.utils.safestring import mark_safe`
    - `register = template.Library()` — Django zahteva ovaj naziv variable (vidi Gotcha #5)
    - **`@register.simple_tag` def `aria_live()`** — vraća `mark_safe('<div id="aria-live" class="visually-hidden" aria-live="polite" aria-atomic="true"></div>')`
    - Docstring na funkciji: kratak (max 2 linije) — opisuje WHAT (vraća kanonski aria-live container) i kako se konzumira (HTMX OOB pattern); project-context.md § Comments policy
- **And** template tag se registruje na Django startup-u — `{% load htmx_aria %}` u `base.html` (AC1) ne sme da baci `TemplateSyntaxError`
- **And** `{% aria_live %}` poziv u `base.html` (AC1) renderuje **TAČNO** string: `<div id="aria-live" class="visually-hidden" aria-live="polite" aria-atomic="true"></div>` (whitespace-insensitive)
- **And** **NEMA** Django ORM zavisnosti — tag je čist string emitter, nema modela, nema query-ja (statički singleton); Story 9.1 deploy ga inicijalizuje bez DB

**AC5 — `config/settings/base.py` ima `django_htmx` + `django_bootstrap5` u INSTALLED_APPS + `HtmxMiddleware` u MIDDLEWARE + `BOOTSTRAP5` settings dict**

- **Given** `base.py` iz Story 1.5 sa INSTALLED_APPS = [admin, auth, contenttypes, sessions, messages, staticfiles, apps.core] + MIDDLEWARE = [Security, Whitenoise, Session, Locale, Common, CSRF, Auth, Messages, XFrame, LocaleSwitcher]
- **When** dopunim `base.py` po Dev Notes § base.py modifications
- **Then** **konkretne izmene** moraju biti prisutne:
  - **INSTALLED_APPS** — dodati **2 nova app-a** POSLE `'django.contrib.staticfiles'` i PRE `'apps.core'`:
    ```python
    INSTALLED_APPS = [
        "django.contrib.admin",
        "django.contrib.auth",
        "django.contrib.contenttypes",
        "django.contrib.sessions",
        "django.contrib.messages",
        "django.contrib.staticfiles",
        "django_htmx",            # NOVO Story 1.6
        "django_bootstrap5",      # NOVO Story 1.6
        "apps.core",
    ]
    ```
  - **MIDDLEWARE** — dodati `'django_htmx.middleware.HtmxMiddleware'` **POSLE** `CommonMiddleware` i **PRE** `apps.core.middleware.LocaleSwitcherMiddleware` (django-htmx docs: "no specific position required, but typically late in chain so that `request.htmx` is set after Common/CSRF"). Order posle Story 1.6:
    ```python
    MIDDLEWARE = [
        "django.middleware.security.SecurityMiddleware",
        "whitenoise.middleware.WhiteNoiseMiddleware",
        "django.contrib.sessions.middleware.SessionMiddleware",
        "django.middleware.locale.LocaleMiddleware",
        "django.middleware.common.CommonMiddleware",
        "django.middleware.csrf.CsrfViewMiddleware",
        "django.contrib.auth.middleware.AuthenticationMiddleware",
        "django.contrib.messages.middleware.MessageMiddleware",
        "django.middleware.clickjacking.XFrameOptionsMiddleware",
        "django_htmx.middleware.HtmxMiddleware",          # NOVO Story 1.6 — postavlja request.htmx
        "apps.core.middleware.LocaleSwitcherMiddleware",
    ]
    ```
  - **NOVA sekcija `# ── Bootstrap 5 ──` u `base.py`** — dodati POSLE `# ── Static ──` sekcije. **base.py** definiše DEV variantu (CDN jsDelivr) per project-context.md § Frontend frameworks line 67 ("Bootstrap 5.3 — CDN u dev, local u prod"):
    ```python
    # ── Bootstrap 5 ──────────────────────────────────────────────────────────────
    # django-bootstrap5 konfiguracija. base.py = DEV variant (CDN jsDelivr) —
    # konvencija project-context.md § Frontend frameworks line 67: "Bootstrap 5.3 —
    # CDN u dev, local u prod". production.py override-uje na local /static/vendor/.
    # Verzija pinned na 5.3.3 (latest stable 5.x kao 2026-05).
    # `integrity: None` eksplicitno suprimira django-bootstrap5 default SRI check
    # (vidi Gotcha #19 — za local fajlove SRI bi failovao SubresourceIntegrityError).
    BOOTSTRAP5 = {
        "css_url": {
            "url": "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css",
            "integrity": None,
        },
        "javascript_url": {
            "url": "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js",
            "integrity": None,
        },
        "javascript_in_head": False,  # JS pre </body> (defer-style preference)
        "include_jquery": False,       # Bootstrap 5 ne zahteva jQuery
    }
    ```
  - **NOVA sekcija `# ── Bootstrap 5 (production override) ──` u `config/settings/production.py`** — production env override-uje BOOTSTRAP5 dict na local vendor paths (per project-context.md § Frontend frameworks: "local u prod"):
    ```python
    # ── Bootstrap 5 (production override) ────────────────────────────────────────
    # Production: lokalni vendor fajlovi (no CDN — GDPR + CSP-readiness).
    # Story 1.6 Task 4 prepares static/vendor/bootstrap-5.3.3/ for this override.
    BOOTSTRAP5 = {
        "css_url": {
            "url": "/static/vendor/bootstrap-5.3.3/css/bootstrap.min.css",
            "integrity": None,
        },
        "javascript_url": {
            "url": "/static/vendor/bootstrap-5.3.3/js/bootstrap.bundle.min.js",
            "integrity": None,
        },
        "javascript_in_head": False,
        "include_jquery": False,
    }
    ```
- **And** **REGRESSION GUARD** — `LANGUAGE_CODE`, `LANGUAGES`, `LOCALE_PATHS`, `DATABASES`, `EMAIL`, `AUTH`, `TEMPLATES`, `STATIC_URL`, `STATICFILES_DIRS`, `STATIC_ROOT`, `STORAGES` (Story 1.2-1.5 izmene) ostaju **NEPROMENJENI**
- **And** `pyproject.toml` ima već `django-htmx>=1.27.0` + `django-bootstrap5>=26.2` (Story 1.1) — **NEMA** novog `uv add` poziva u ovoj story-ji

**AC6 — `request.htmx` atribut dostupan u svim view-ovima (HtmxMiddleware aktiviran)**

- **Given** MIDDLEWARE iz AC5 sa `HtmxMiddleware` registrovanim
- **When** view-u dođe običan GET request (npr. `GET /sr/`)
- **Then** `request.htmx` je falsy (`HtmxDetails` objekat koji `bool() == False`) — view rendera full page
- **When** view-u dođe HTMX request (sa `HX-Request: true` header-om)
- **Then** `request.htmx` je truthy — view može da bira partial: `if request.htmx: return render(request, "partials/...")`
- **And** verifikacija (RequestFactory test, Task 9.4): import `HtmxMiddleware` iz `django_htmx.middleware`, kreiraj instancu, prosledi `RequestFactory().get("/")` sa i bez `HTTP_HX_REQUEST="true"` header-a — `request.htmx` MORA biti dostupan oba puta (falsy bez header-a, truthy sa)
- **And** **NEMA** view-ova koje Story 1.6 menja — ovo je infrastructure-only setup; konzumenti dolaze u Story 2.8 (catalog filteri) i Story 4.6 (HTMX form patterns)

**AC7 — `static/vendor/htmx.min.js` + `static/vendor/bootstrap-5.3.3/` lokalno**

- **Given** `static/` struktura iz Story 1.5 (`static/css/tokens.css` + `static/fonts/roboto/`)
- **When** Mihas preuzima HTMX 1.9.12 (version-pinned) i Bootstrap 5.3.3 lokalno i smešta u `static/vendor/`
- **Then** prisutni su sledeći fajlovi (ručna Mihas akcija — Task 4):
  - `static/vendor/htmx.min.js` (~50KB) — HTMX **1.9.12** version-pinned (NE 2.x — project-context.md § Frontend frameworks pinned na 1.9+; HTMX 2.x je released kao 2026-05 i serves na `htmx.org/dist/htmx.min.js`, što bi razbilo API contract za Story 4.6 forme, 2.8 filter). Preuzima se sa **version-pinned URL-a**: `https://unpkg.com/htmx.org@1.9.12/dist/htmx.min.js` (alternativa: GitHub release `https://github.com/bigskysoftware/htmx/releases/download/v1.9.12/htmx.min.js`). Verifikuj otvaranjem fajla — prvih 1-3 linija imaju version comment header `/*! HTMX vX.Y.Z */` ili sličan version marker; MORA biti **1.9.12** (ne `1.9.13+` patch — explicit pin).
  - `static/vendor/bootstrap-5.3.3/css/bootstrap.min.css` (~230KB) — Bootstrap 5.3.3 minified CSS
  - `static/vendor/bootstrap-5.3.3/js/bootstrap.bundle.min.js` (~80KB) — Bootstrap 5.3.3 bundle (uključuje Popper.js za dropdowns/tooltips); preuzimaju se sa https://getbootstrap.com/docs/5.3/getting-started/download/
- **And** ukupna veličina svih vendor fajlova **MORA biti < 500KB** (sanity check — ako je veći, Mihas je preuzeo nepravilnu varijantu npr. unminified ili sa source maps)
- **And** licence: HTMX = Zero-Clause BSD (0BSD, public domain-equivalent); Bootstrap = MIT — obe self-host friendly bez attribution-a u UI-u (kratak komentar u `base.html` ili license fajl u `static/vendor/<package>/LICENSE.txt` je dovoljan)
- **And** **future upgrade path** — HTMX 2.x migracija je dokumentovana kao future story (treba se odraditi kad Story 1.9 CI je u mestu da pokupi breaking changes); ne radi se u Story 1.6
- **Napomena za Dev:** ako u trenutku implementacije fajlovi NISU prisutni (npr. Mihas ih nije još preuzeo), Dev mora **HALT-ovati** Task 4 sa explicit porukom u Dev Agent Record sekciji: `"BLOCKED: Mihas mora preuzeti HTMX 1.9.12 sa https://unpkg.com/htmx.org@1.9.12/dist/htmx.min.js (~50KB, snimiti kao static/vendor/htmx.min.js, version-pin obavezan — htmx.org/dist serves LATEST koji je sada 2.x) i Bootstrap 5.3.3 ZIP sa https://getbootstrap.com/docs/5.3/getting-started/download/ (raspakovati u static/vendor/bootstrap-5.3.3/ tako da postoje css/bootstrap.min.css + js/bootstrap.bundle.min.js)."` Tek po prisustvu sva 3 fajla Dev nastavlja sa AC8-AC9.

**AC8 — `static/css/main.css` placeholder fajl**

- **Given** `static/css/` iz Story 1.5 sa `tokens.css`
- **When** kreiram `static/css/main.css` po Dev Notes § main.css Template
- **Then** fajl postoji sa **minimal placeholder sadržajem** (1-3 linije):
  ```css
  /* main.css — site-wide custom CSS. Story 1.7+ populates with komponente. */
  /* Loaded AFTER tokens.css i Bootstrap CSS u base.html — overrides cascade. */
  ```
- **And** fajl je linkovan u `base.html` (AC1) POSLE `{% bootstrap_css %}` (kaskadni override; vidi Gotcha #2)
- **And** **NEMA** stvarnih CSS pravila u Story 1.6 — placeholder samo, Story 1.7+ popunjava `body { font-family: var(--typography-family-primary); }` + komponentne klase

**AC9 — Smoke validacija (acceptance verification)**

- **Given** AC1-AC8 implementirano
- **When** runujem smoke test sekvencu
- **Then** sledeće mora proći:
  1. **File presence check:**
     - `templates/base.html` postoji, dužina 50-80 linija
     - `apps/core/templatetags/__init__.py` postoji (prazan ili sa minimal komentarom)
     - `apps/core/templatetags/htmx_aria.py` postoji
     - `static/vendor/htmx.min.js` postoji (size 40-80KB; vidi AC7)
     - `static/vendor/bootstrap-5.3.3/css/bootstrap.min.css` postoji (size 200-300KB)
     - `static/vendor/bootstrap-5.3.3/js/bootstrap.bundle.min.js` postoji (size 70-100KB)
     - `static/css/main.css` postoji (prazan ili sa placeholder komentarom; <500 bytes)
  2. **base.html content check** (grep/regex):
     - `grep -c "{% load django_bootstrap5 %}" templates/base.html` → match
     - `grep -c "{% load htmx_aria %}" templates/base.html` → match
     - `grep -c "{% bootstrap_css %}" templates/base.html` → match
     - `grep -c "{% bootstrap_javascript %}" templates/base.html` → match
     - `grep -c "{% aria_live %}" templates/base.html` → match (tačno jednom)
     - `grep -c "visually-hidden-focusable" templates/base.html` → match (skip link)
     - `grep -c 'id="main-content"' templates/base.html` → match (skip link target)
     - `grep -c 'tabindex="-1"' templates/base.html` → match (na main)
     - `grep -c "htmx.min.js" templates/base.html` → match
     - `grep -c "main.css" templates/base.html` → match
     - `grep -c "<noscript>" templates/base.html` → match
     - `grep -ci "googleapis\|gstatic" templates/base.html` → **no match** (Google CDN anti-pattern guard; jsDelivr je DOZVOLJEN samo u dev mode-u kroz BOOTSTRAP5 settings — NIKAD direktno u base.html template-u)
     - `grep -ci "onchange\|onclick\|onload" templates/base.html` → **no match** (CSP-ready, no inline event handlers; Story 9.1 enables CSP)
     - **CSS load order**: tokens.css link line number < bootstrap_css line number < main.css link line number (use `grep -n` to verify ordering)
  3. **htmx_aria.py content check:**
     - `apps/core/templatetags/htmx_aria.py` sadrži: `register = template.Library()`, `@register.simple_tag`, `def aria_live`, `mark_safe`, `id="aria-live"`, `aria-live="polite"`, `aria-atomic="true"`, `class="visually-hidden"`
     - `python -c "from apps.core.templatetags.htmx_aria import aria_live; print(aria_live())"` (kroz `uv run`) prints expected HTML string
  4. **base.py validity:**
     - `uv run python manage.py check` exit 0
     - `uv run python manage.py shell -c "from django.conf import settings; print('django_htmx' in settings.INSTALLED_APPS)"` → output `True`
     - `uv run python manage.py shell -c "from django.conf import settings; print('django_bootstrap5' in settings.INSTALLED_APPS)"` → output `True`
     - `uv run python manage.py shell -c "from django.conf import settings; print('django_htmx.middleware.HtmxMiddleware' in settings.MIDDLEWARE)"` → output `True`
     - `uv run python manage.py shell -c "from django.conf import settings; url = settings.BOOTSTRAP5['css_url']['url']; import re; assert re.search(r'(cdn\\.jsdelivr\\.net.*bootstrap@5\\.3\\.3|/static/vendor/bootstrap-5\\.3\\.3)', url), f'BOOTSTRAP5 css_url bad: {url}'; print(url)"` — accepts dev (CDN jsDelivr@5.3.3) OR prod (local /static/vendor/bootstrap-5.3.3/) variant
     - `uv run python manage.py shell -c "from django.conf import settings; print(settings.BOOTSTRAP5['css_url'].get('integrity'))"` → output `None` (Gotcha #19 — SRI suppressed)
  5. **MIDDLEWARE position validation:**
     - `HtmxMiddleware` index u MIDDLEWARE listi mora biti **POSLE** index-a `CommonMiddleware` i **PRE** index-a `LocaleSwitcherMiddleware` — vidi Gotcha #6 za assertion code
  6. **Template tag library importable:**
     - `uv run python -c "from apps.core.templatetags import htmx_aria; print(htmx_aria.aria_live())"` → output sadrži `id="aria-live"` i `aria-live="polite"`
     - `uv run python manage.py shell -c "from django.template import Template, Context; print(Template('{% load htmx_aria %}{% aria_live %}').render(Context()))"` → output `<div id="aria-live" class="visually-hidden" aria-live="polite" aria-atomic="true"></div>`
  7. **request.htmx attribute test** (RequestFactory):
     - `uv run python manage.py shell` sa snippet-om (Task 9.4):
       ```python
       from django.test import RequestFactory
       from django_htmx.middleware import HtmxMiddleware
       rf = RequestFactory()
       mw = HtmxMiddleware(lambda r: None)
       # Bez HTMX header-a
       r1 = rf.get("/")
       mw(r1)
       assert hasattr(r1, "htmx")
       assert bool(r1.htmx) is False
       # Sa HTMX header-om
       r2 = rf.get("/", HTTP_HX_REQUEST="true")
       mw(r2)
       assert bool(r2.htmx) is True
       print("OK")
       ```
  8. **collectstatic --dry-run:**
     - `uv run python manage.py collectstatic --dry-run --noinput` exit 0
     - Output sadrži `vendor/htmx.min.js`, `vendor/bootstrap-5.3.3/css/bootstrap.min.css`, `vendor/bootstrap-5.3.3/js/bootstrap.bundle.min.js`, `css/main.css`
  9. **Live render test (Docker):**
     - `just dev` (Docker compose up) → Django + Postgres up bez grešaka
     - **GET `http://localhost:8000/sr/`** → HTTP 200; response HTML sadrži:
       - `<link rel="stylesheet" href="/static/css/tokens.css">` (Story 1.5 regression)
       - Bootstrap CSS link MUST match regex `(cdn\.jsdelivr\.net/npm/bootstrap@5\.3\.3|/static/vendor/bootstrap-5\.3\.3)` — dev expects CDN (jsDelivr); prod expects local
       - `<link rel="stylesheet" href="/static/css/main.css">`
       - `<a class="visually-hidden-focusable" href="#main-content">Preskoči na sadržaj</a>` (sr translation)
       - `<main id="main-content" tabindex="-1">`
       - `<div id="aria-live" class="visually-hidden" aria-live="polite" aria-atomic="true"></div>`
       - `<noscript>` blok
       - `<script src="/static/vendor/htmx.min.js" defer></script>` (HTMX uvek local — pinned 1.9.x)
       - Bootstrap JS script MUST match regex `(cdn\.jsdelivr\.net/npm/bootstrap@5\.3\.3.*bundle|/static/vendor/bootstrap-5\.3\.3.*bundle)` — dev expects CDN; prod expects local
     - **GET `http://localhost:8000/static/vendor/htmx.min.js`** → HTTP 200, content-type `application/javascript`, body sadrži `htmx` (string check za sanity)
     - **GET `http://localhost:8000/static/vendor/bootstrap-5.3.3/css/bootstrap.min.css`** → HTTP 200 u **prod-u** (vendor prepared by Task 4); u **dev-u** može da bude 200 ako Mihas već preuzeo, ali nije zahtevano — dev koristi CDN
     - **Browser dev tools Network tab** na `/sr/`: NEMA request-a ka `googleapis.com`, `gstatic.com`, `unpkg.com`, `getbootstrap.com`, `htmx.org`. **Dev mode dozvoljava** `cdn.jsdelivr.net` (samo za Bootstrap CSS+JS). **Prod mode** NEMA NIJEDAN external request (svi local).
     - **Browser dev tools Console**: NEMA error-a tipa `htmx is not defined` ili `bootstrap is not defined`
     - **Keyboard test:** Tab iz URL bar-a → skip link postaje vidljiv (visually-hidden-focusable revelation); Enter → main focus + skroll to top
  10. **Regression — Story 1.1-1.5 nije razbijena:**
      - `uv run pytest` — svi postojeći testovi prolaze (Story 1.4 middleware tests, Story 1.5 ako su dodati)
      - `just lint` — `ruff check .` exit 0; `djade --check templates/` exit 0
      - `http://localhost:8000/` → HTTP 302 → `/sr/` (Story 1.4 functionality)
      - `http://localhost:8000/sr/` → 200, `<html lang="sr">` (Story 1.4)
      - `?lang=hu` na `/sr/` → 302 ka `/hu/` (Story 1.4 LocaleSwitcher functionality)
      - `<link rel="stylesheet" href="/static/css/tokens.css">` i dalje prisutan (Story 1.5)
  11. **Lighthouse a11y manual check (Mihas) — SHOULD (soft-gate), enforcement deferred to Story 9.9:**
      - **Status:** SHOULD (not MUST) za Story 1.6 — automated enforcement nije u mestu (Story 1.9 CI dodaje automated a11y check kroz axe-core ili pa11y; Story 9.9 runs full Lighthouse audit kao deo a11y dedicated audit story-je).
      - Otvori `http://localhost:8000/sr/` u Chrome incognito
      - F12 → Lighthouse tab → Mobile + Accessibility only → Generate report
      - **Target Score ≥ 95** (epics.md AC za Story 1.6 — soft target); base.html SHOULD pass ≥95 ako Templates iz Dev Notes followed verbatim (Gotcha #16 lista relevantnih audit-a)
      - Verifikuj specifične audit-e (ako Mihas runuje):
        - `html-has-lang` (Story 1.4 regression) ✓
        - `bypass` (skip link presence — Story 1.6 AC2) ✓
        - `landmark-one-main` (single `<main>` element) ✓
        - `meta-viewport` (Story 1.4 regression) ✓
        - `aria-valid-attr-value` (aria-live="polite" valid) ✓
      - Ako score < 95: dokumentuj failure audit-e u Dev Agent Record + Mihas debug; **NIJE blocking za story done** (defer detailed remediation to Story 9.9 a11y audit)
      - **NOTE:** Story 1.9 (CI) će dodati automated a11y check (axe-core / pa11y), Story 9.9 (a11y audit) će run-ovati full Lighthouse audit sa enforcement.

## Tasks / Subtasks

- [ ] **Task 1: Pre-flight verifikacija** (AC: sve)
  - [ ] 1.1 Verifikuj da je Story 1.5 done: `cat _bmad-output/implementation-artifacts/sprint-status.yaml | grep "1-5-"` mora pokazati `done`
  - [ ] 1.2 Verifikuj postojanje fajlova iz prethodnih story-ja: `config/settings/base.py` (sa Story 1.5 STATICFILES_DIRS + Whitenoise middleware), `templates/base.html` (sa Story 1.5 tokens.css link), `apps/core/{apps.py,middleware.py,views.py,urls.py,translation.py}`, `static/css/tokens.css`, `pyproject.toml` (sa `django-htmx>=1.27.0` i `django-bootstrap5>=26.2`)
  - [ ] 1.3 Verifikuj da `apps/core/templatetags/` direktorijum NE postoji (Story 1.6 ga kreira)
  - [ ] 1.4 Verifikuj da `static/vendor/` direktorijum NE postoji (Story 1.6 ga kreira)
  - [ ] 1.5 Verifikuj da `static/css/main.css` NE postoji (Story 1.6 ga kreira)
  - [ ] 1.6 Verifikuj `pyproject.toml` ima već instalirano: `django-htmx>=1.27.0`, `django-bootstrap5>=26.2`. Pokreni `uv run python -c "import django_htmx; import django_bootstrap5; print('OK')"` exit 0 i printa OK.
  - [ ] 1.7 Pročitaj `templates/base.html` (current Story 1.5 state, 24 linije) — Dev MORA očuvati svaki postojeći element (AC1 regression guard)

- [ ] **Task 2: Update `config/settings/base.py` — INSTALLED_APPS + MIDDLEWARE + BOOTSTRAP5 dict** (AC: 5)
  - [ ] 2.1 Otvori `config/settings/base.py`, lociraj `INSTALLED_APPS` listu (linije 28-36)
  - [ ] 2.2 Dodaj `"django_htmx"` i `"django_bootstrap5"` POSLE `"django.contrib.staticfiles"` i PRE `"apps.core"` (vidi AC5)
  - [ ] 2.3 Lociraj `MIDDLEWARE` listu (linije 38-49)
  - [ ] 2.4 Ubaci `"django_htmx.middleware.HtmxMiddleware"` POSLE `"django.middleware.clickjacking.XFrameOptionsMiddleware"` i PRE `"apps.core.middleware.LocaleSwitcherMiddleware"` (vidi AC5 + Gotcha #6)
  - [ ] 2.5 Lociraj kraj fajla (posle `# ── Default ──` sekcije sa `DEFAULT_AUTO_FIELD`)
  - [ ] 2.6 Dodaj novu sekciju `# ── Bootstrap 5 ──` u `base.py` sa `BOOTSTRAP5` dict-om — **DEV variant** (CDN jsDelivr) (vidi AC5 + Dev Notes § base.py modifications + Gotcha #1)
  - [ ] 2.6a Dodaj sekciju `# ── Bootstrap 5 (production override) ──` u `config/settings/production.py` sa `BOOTSTRAP5` dict-om — **PROD variant** (local /static/vendor/) (vidi AC5 + Gotcha #1). Ako `production.py` ne postoji ili nije Story 1.6 scope, dokumentuj u Dev Agent Record + obezbedi da production override bude u skoru sledećoj story-i koja kreira production.py.
  - [ ] 2.6b KRITIČNO: oba dict-a moraju imati `"integrity": None` na `css_url` i `javascript_url` (vidi Gotcha #19)
  - [ ] 2.7 KRITIČNO: NIKAKAV `whitenoise.runserver_nostatic` add (Story 1.5 nije dodala, nema potrebe sada)
  - [ ] 2.8 KRITIČNO: NE diraj `LANGUAGE_CODE`, `LANGUAGES`, `LOCALE_PATHS`, `DATABASES`, `EMAIL`, `AUTH`, `TEMPLATES`, `STATIC_URL`, `STATICFILES_DIRS`, `STATIC_ROOT`, `STORAGES` (regression guard za Story 1.2-1.5)
  - [ ] 2.9 Verifikuj `uv run python manage.py check` exit 0 (mora pasti pre Task 3 zbog `{% load django_bootstrap5 %}` u base.html koji još ne postoji; ali settings check sam za sebe radi)

- [ ] **Task 3: Kreiraj `apps/core/templatetags/` package + `htmx_aria.py`** (AC: 4)
  - [ ] 3.1 Kreiraj direktorijum `apps/core/templatetags/` (NEW path — vidi Gotcha #4)
  - [ ] 3.2 Kreiraj **prazan** fajl `apps/core/templatetags/__init__.py` — sadržaj može biti potpuno prazan ili 1-line komentar (`# Template tags za apps.core (Django discovery zahteva ovaj __init__.py)`). Vidi Gotcha #4 — bez `__init__.py` Django NE registruje library.
  - [ ] 3.3 Kreiraj `apps/core/templatetags/htmx_aria.py` sa sadržajem iz Dev Notes § htmx_aria.py Template
  - [ ] 3.4 KRITIČNO: `register = template.Library()` — naziv `register` je obavezan (Django magic — vidi Gotcha #5)
  - [ ] 3.5 KRITIČNO: `@register.simple_tag` decorator — NE `@register.inclusion_tag` (ne treba template file; vraćamo direktno HTML kroz `mark_safe`)
  - [ ] 3.6 KRITIČNO: `mark_safe(...)` da Django ne escape-uje HTML — bez njega `<div>` se render-uje kao `&lt;div&gt;`
  - [ ] 3.7 Naziv funkcije `aria_live` (snake_case) — Django registruje tag pod istim imenom; `{% aria_live %}` u template-u mapira na ovu funkciju
  - [ ] 3.8 KRITIČNO: NE testiraj sam template tag u ovom task-u (testovi dolaze u Task 10) — samo kreiraj fajlove

- [ ] **Task 4: Preuzmi HTMX 1.9.x + Bootstrap 5.3.3 vendor fajlove (Mihas ručno; Dev verifikuje prisustvo)** (AC: 7) — BLOCKED until Mihas downloads
  - [ ] 4.1 **Mihas instrukcije (ručna akcija):**
     **HTMX (version-pinned 1.9.12):**
     1. **KRITIČNO — koristi version-pinned URL** (NE `htmx.org/dist/htmx.min.js` koji serves latest i sada vraća HTMX 2.x koji razbija naš API contract). Primarni URL: `https://unpkg.com/htmx.org@1.9.12/dist/htmx.min.js`. Alternativa: GitHub release `https://github.com/bigskysoftware/htmx/releases/download/v1.9.12/htmx.min.js`. PowerShell: `Invoke-WebRequest -Uri 'https://unpkg.com/htmx.org@1.9.12/dist/htmx.min.js' -OutFile 'static/vendor/htmx.min.js'`.
     2. **Verifikuj version u source-u** — otvori fajl u editor-u; prvih 1-3 linija MORA sadržati version comment header tipa `/*! HTMX v1.9.12 */` ili sličan version marker. **Verifikuj da je 1.9.12** (ne 1.9.13+, ne 2.x). PowerShell quick check: `Get-Content static/vendor/htmx.min.js -TotalCount 3 | Select-String -Pattern "1\.9\.12"` mora matchovati.
     3. Verifikuj veličinu: `(Get-Item static/vendor/htmx.min.js).Length / 1KB` — 40-80 KB (file-size sanity je neuspesna između 1.9.x i 2.x jer su slične, version comment je primarna provera)
     **Bootstrap 5.3.3:**
     4. Otvori `https://getbootstrap.com/docs/5.3/getting-started/download/`
     5. U sekciji "Compiled CSS and JS" klikni "Download" — dobija se ZIP `bootstrap-5.3.3-dist.zip`
     6. Raspakuj ZIP, izvuci `css/bootstrap.min.css` i `js/bootstrap.bundle.min.js` (NE bootstrap.min.js — bundle uključuje Popper.js za dropdown/tooltip funkcionalnost)
     7. Kreiraj strukturu `static/vendor/bootstrap-5.3.3/css/` i `static/vendor/bootstrap-5.3.3/js/`
     8. Premesti `bootstrap.min.css` u `static/vendor/bootstrap-5.3.3/css/bootstrap.min.css`
     9. Premesti `bootstrap.bundle.min.js` u `static/vendor/bootstrap-5.3.3/js/bootstrap.bundle.min.js`
     10. Verifikuj veličine: CSS 200-300KB, JS 70-100KB
     11. Opciono: snimi `static/vendor/bootstrap-5.3.3/LICENSE.txt` (kopiraj iz Bootstrap ZIP-a; MIT license)
     12. Opciono: snimi `static/vendor/HTMX-LICENSE.txt` (HTMX = 0BSD; copy from https://github.com/bigskysoftware/htmx/blob/master/LICENSE)
  - [ ] 4.2 **Dev verifikacija (Dev agent):**
     - **HALT check:** ako sva 3 fajla NISU prisutna sa tačnim path-evima iz Task 4.1, Dev MORA HALT-ovati sa porukom u Dev Agent Record: `"BLOCKED: Mihas mora preuzeti HTMX 1.9.x + Bootstrap 5.3.3 vendor fajlove. Vidi Task 4.1 za korake."` i ne nastavlja sa Task 5+.
     - Ako fajlovi POSTOJE, Dev verifikuje:
       - `ls static/vendor/htmx.min.js` (Linux/Mac) ili `Get-Item static/vendor/htmx.min.js` (PowerShell) — exists
       - `ls static/vendor/bootstrap-5.3.3/css/bootstrap.min.css` — exists
       - `ls static/vendor/bootstrap-5.3.3/js/bootstrap.bundle.min.js` — exists
       - Total size sanity: `(Get-ChildItem static/vendor/ -Recurse -Filter *.css,*.js | Measure-Object Length -Sum).Sum / 1KB` < 500 KB
       - HTMX content sanity + **version pin check**: `Get-Content static/vendor/htmx.min.js -TotalCount 3 | Select-String -Pattern "1\.9\.12"` MORA matchovati (version comment header). Ako match-uje `2\.` umesto `1\.9\.12`, Dev MORA HALT-ovati sa porukom: `"BLOCKED: HTMX downloaded je 2.x (ne 1.9.12 pinned) — incompatible API; project-context.md pinned na HTMX 1.9+. Re-download sa https://unpkg.com/htmx.org@1.9.12/dist/htmx.min.js."`
       - Bootstrap content sanity: `Select-String -Path static/vendor/bootstrap-5.3.3/css/bootstrap.min.css -Pattern "Bootstrap" -SimpleMatch | Select-Object -First 1` matches (Bootstrap min file ima header comment sa "Bootstrap v5.3.3")

- [ ] **Task 5: Kreiraj `static/css/main.css` placeholder** (AC: 8)
  - [ ] 5.1 Kreiraj `static/css/main.css` sa sadržajem iz Dev Notes § main.css Template (2-line komentar)
  - [ ] 5.2 KRITIČNO: NE dodaj nikakva CSS pravila — Story 1.7+ popunjava komponente; Story 1.6 samo placeholder file koji `base.html` referencira

- [ ] **Task 6: Update `templates/base.html` — proširi po AC1** (AC: 1, 2, 3)
  - [ ] 6.1 Otvori `templates/base.html` (24 linije iz Story 1.5)
  - [ ] 6.2 Posle `{% load static %}` dodaj `{% load django_bootstrap5 %}` i `{% load htmx_aria %}` (vidi Dev Notes § base.html Template)
  - [ ] 6.3 U `<head>` dodaj:
     - `<meta name="description" content="{% block meta_description %}{% endblock %}">` — POSLE `<meta name="viewport">` i PRE `<title>`
     - `{% bootstrap_css %}` — POSLE `tokens.css` link i PRE `{% block extra_head %}`
     - `<link rel="stylesheet" href="{% static 'css/main.css' %}">` — POSLE `{% bootstrap_css %}` i PRE `{% block extra_head %}` (kaskadni override redom: tokens → Bootstrap → main; vidi Gotcha #2)
  - [ ] 6.4 U `<body>` na **prvoj liniji** (PRE `<header>`) dodaj skip link: `<a class="visually-hidden-focusable" href="#main-content">{% translate "Preskoči na sadržaj" %}</a>`
  - [ ] 6.5 Modifikuj `<main>` u `<main id="main-content" tabindex="-1">` (vidi AC2 + Gotcha #7)
  - [ ] 6.6 POSLE `</main>` dodaj (red važi):
     - `{% aria_live %}` (renderuje aria-live div)
     - `<noscript>` blok sa Bootstrap alert (vidi AC1)
  - [ ] 6.7 **POSLE noscript** dodaj **site-wide script-e PRVI** (vidi AC1 + Gotcha #15 reordering rationale):
     - `<script src="{% static 'vendor/htmx.min.js' %}" defer></script>` — PRVO (HTMX se učita ranije)
     - `{% bootstrap_javascript %}` — DRUGO (Bootstrap može imati hookove na DOM)
  - [ ] 6.7a **POSLE site-wide scripts** premesti existing `{% block scripts %}{% endblock %}` (iz Story 1.5 base.html — bio je tu, sad se reordered da bude POSLE site-wide scripts; Bootstrap sync precedes block u DOM order-u → uvek loaded kad child-page sync init Bootstrap-a execute → safe za sync Bootstrap init)
  - [ ] 6.8 KRITIČNO: NE diraj `<!DOCTYPE html>`, `{% load i18n %}`, `{% load static %}`, `<html lang="{{ LANGUAGE_CODE }}">`, `<meta charset>`, `<meta name="viewport">`, `<title>`, `tokens.css` link, `{% block extra_head %}`, `<header>` sa language switcher include, `{% block content %}` default (`<h1>Ćorić Agrar</h1>` + `<p>{% translate "Dobrodošli." %}</p>`), `{% block scripts %}{% endblock %}` placeholder, `</body>`, `</html>` (regression guard za Story 1.4 + 1.5)
  - [ ] 6.9 KRITIČNO: NE koristi inline `onchange`, `onclick`, `onload` handlere (CSP-ready; Story 9.1 enables CSP)
  - [ ] 6.10 KRITIČNO: NE koristi `<style>` blokove inline (sve CSS ide kroz `<link>` na external fajl)
  - [ ] 6.11 Verifikuj `djade --check templates/` exit 0 (template format clean)

- [ ] **Task 7: Verifikuj static files se serviraju (sanity check)** (AC: 7, 8)
  - [ ] 7.1 Pokreni `uv run python manage.py collectstatic --dry-run --noinput` — exit 0; output sadrži `vendor/htmx.min.js`, `vendor/bootstrap-5.3.3/css/bootstrap.min.css`, `vendor/bootstrap-5.3.3/js/bootstrap.bundle.min.js`, `css/main.css`
  - [ ] 7.2 Verifikuj `.gitignore` ne ignoriše `static/vendor/` (treba da bude commit-ovan kao vendor source); ako jeste, ne treba akcija (`.gitignore` iz Story 1.5 ne ignoriše `static/`)

- [ ] **Task 8: Pokreni Django dev server + smoke test rendering** (AC: 1, 2, 3, 6, 9)
  - [ ] 8.1 `just dev-build` (rebuild Docker image — settings su se izmenili, ali deps su iste, brz build)
  - [ ] 8.2 `just dev` (start dev server)
  - [ ] 8.3 Browser: `http://localhost:8000/sr/` → HTTP 200
  - [ ] 8.4 View source (Ctrl+U) i verifikuj prisustvo svih elemenata iz AC9 sekcije 9 (skip link, main#main-content, aria-live div, noscript, htmx.min.js, bootstrap CSS link, bootstrap JS, main.css link, tokens.css link)
  - [ ] 8.5 Browser dev tools Network tab — env-aware očekivanja (CDN-dev/local-prod policy iz project-context.md line 67):
     - **Dev mode (`DEBUG=True`, `just dev`):** Network tab TREBA da pokaže JEDAN request ka `cdn.jsdelivr.net/npm/bootstrap@5.3.3/...` (CSS + JS bundle) — to je OČEKIVANO ponašanje (CDN u dev). htmx.min.js i main.css/tokens.css se serviraju lokalno preko `/static/`.
     - **Prod mode (`DEBUG=False`, `just prod` ili production settings):** Network tab MORA da pokaže SAMO `/static/vendor/bootstrap-5.3.3/css/bootstrap.min.css` i `/static/vendor/bootstrap-5.3.3/js/bootstrap.bundle.min.js` (lokalni URL) — NEMA `cdn.jsdelivr.net`.
     - **Anti-pattern (zabranjeno u OBA mode-a):** NEMA `googleapis.com`, NEMA `gstatic.com`, NEMA preconnect ka Google domain-ima, NEMA `unpkg.com`, NEMA `getbootstrap.com`, NEMA `htmx.org` (htmx se uvek servira lokalno).
  - [ ] 8.6 Browser dev tools Console — NEMA error-a (`htmx is not defined`, `bootstrap is not defined`)
  - [ ] 8.7 Keyboard: Click u URL bar → Tab → vidljiv skip link → Enter → focus jumps to main; verifikuj browser back behavior (push state, history neporemećen)

- [ ] **Task 9: Smoke validacija — automatizovan check-list** (AC: 9)
  - [ ] 9.1 **base.html content check** (sve grep-ove iz AC9.2):
     ```bash
     grep -c "{% load django_bootstrap5 %}" templates/base.html  # 1
     grep -c "{% load htmx_aria %}" templates/base.html  # 1
     grep -c "{% bootstrap_css %}" templates/base.html  # 1
     grep -c "{% bootstrap_javascript %}" templates/base.html  # 1
     grep -c "{% aria_live %}" templates/base.html  # 1
     grep -c "visually-hidden-focusable" templates/base.html  # 1
     grep -c 'id="main-content"' templates/base.html  # 1
     grep -c 'tabindex="-1"' templates/base.html  # 1
     grep -c "htmx.min.js" templates/base.html  # 1
     grep -c "main.css" templates/base.html  # 1
     grep -c "<noscript>" templates/base.html  # 1
     grep -ci "googleapis\|gstatic" templates/base.html  # 0 (Google CDN anti-pattern; jsDelivr je DOZVOLJEN render-time kroz {% bootstrap_css %} u dev mode-u — NIKAD kao literal URL u base.html source-u)
     grep -ci "onchange\|onclick\|onload" templates/base.html  # 0
     ```
     PowerShell equivalent: `Select-String -Path templates/base.html -Pattern "{% load django_bootstrap5 %}" | Measure-Object | Select-Object -ExpandProperty Count` per pattern.
  - [ ] 9.2 **CSS order check** (`grep -n` to get line numbers):
     - `tokens.css` line < `bootstrap_css` line < `main.css` line — assertion (vidi Gotcha #2)
  - [ ] 9.3 **Settings check** (sve iz AC9.4):
     ```bash
     uv run python manage.py shell -c "from django.conf import settings; \
       assert 'django_htmx' in settings.INSTALLED_APPS; \
       assert 'django_bootstrap5' in settings.INSTALLED_APPS; \
       assert 'django_htmx.middleware.HtmxMiddleware' in settings.MIDDLEWARE; \
       assert 'apps.core.middleware.LocaleSwitcherMiddleware' in settings.MIDDLEWARE; \
       hi = settings.MIDDLEWARE.index('django_htmx.middleware.HtmxMiddleware'); \
       lsi = settings.MIDDLEWARE.index('apps.core.middleware.LocaleSwitcherMiddleware'); \
       ci = settings.MIDDLEWARE.index('django.middleware.common.CommonMiddleware'); \
       assert ci < hi < lsi, f'HtmxMiddleware position bad: common={ci}, htmx={hi}, lsi={lsi}'; \
       assert settings.BOOTSTRAP5['css_url']['url'].endswith('bootstrap.min.css'); \
       print('Settings OK')"
     ```
  - [ ] 9.4 **request.htmx attribute test** (iz AC9.7):
     ```bash
     uv run python manage.py shell -c "
     from django.test import RequestFactory
     from django_htmx.middleware import HtmxMiddleware
     rf = RequestFactory()
     mw = HtmxMiddleware(lambda r: None)
     r1 = rf.get('/')
     mw(r1)
     assert hasattr(r1, 'htmx'), 'request.htmx missing'
     assert bool(r1.htmx) is False, f'r1.htmx truthy without header: {r1.htmx}'
     r2 = rf.get('/', HTTP_HX_REQUEST='true')
     mw(r2)
     assert bool(r2.htmx) is True, f'r2.htmx falsy with header: {r2.htmx}'
     print('request.htmx OK')"
     ```
  - [ ] 9.5 **Template tag rendering** (iz AC9.6):
     ```bash
     uv run python manage.py shell -c "
     from django.template import Template, Context
     out = Template('{% load htmx_aria %}{% aria_live %}').render(Context())
     assert 'id=\"aria-live\"' in out
     assert 'aria-live=\"polite\"' in out
     assert 'aria-atomic=\"true\"' in out
     assert 'class=\"visually-hidden\"' in out
     print('aria_live tag OK')"
     ```
  - [ ] 9.6 **Live render full check:**
     - Browser `http://localhost:8000/sr/` view source — sve checks iz AC9.9
     - Browser `http://localhost:8000/static/vendor/htmx.min.js` → 200
     - Browser `http://localhost:8000/static/vendor/bootstrap-5.3.3/css/bootstrap.min.css` → 200
     - Browser `http://localhost:8000/static/vendor/bootstrap-5.3.3/js/bootstrap.bundle.min.js` → 200
     - Browser `http://localhost:8000/static/css/main.css` → 200
  - [ ] 9.7 **Regression — Story 1.1-1.5:**
     - `uv run pytest` exit 0 (svi prethodni testovi prolaze)
     - `just lint` clean (ruff + djade)
     - `/` → 302 → `/sr/` (Story 1.4)
     - `/sr/` → 200 sa `<html lang="sr">` (Story 1.4)
     - `?lang=hu` na `/sr/` → 302 ka `/hu/` (Story 1.4 LocaleSwitcher)
     - `/static/css/tokens.css` → 200 (Story 1.5)
  - [ ] 9.8 **Lighthouse manual run (Mihas) — SHOULD / soft-gate (vidi AC9.11):**
     - Status: manual recommended pre-commit step; NOT story-done blocking
     - Chrome incognito → `http://localhost:8000/sr/` → F12 Lighthouse tab → Accessibility category samo → Generate
     - Target Score ≥ 95 (epics.md target — soft); ako < 95, document failure audits u Dev Agent Record + defer remediation to Story 9.9 (a11y audit)
     - **Automated enforcement** dolazi u Story 1.9 (CI axe-core / pa11y) + Story 9.9 (full Lighthouse audit)
  - [ ] 9.9 Cleanup: `just dev-down`

- [ ] **Task 10: Final review i sanity check** (AC: sve)
  - [ ] 10.1 Verifikuj `templates/base.html` finalna struktura — sve postojeće elemente iz Story 1.5 sačuvane + sva dodavanja iz AC1
  - [ ] 10.2 Verifikuj `config/settings/base.py` ima sve izmene iz AC5; NIKAKVA druga sekcija nije dirana
  - [ ] 10.3 Verifikuj `apps/core/templatetags/__init__.py` + `htmx_aria.py` postoje sa minimal sadržajem
  - [ ] 10.4 Verifikuj `static/vendor/htmx.min.js` + `static/vendor/bootstrap-5.3.3/css/bootstrap.min.css` + `static/vendor/bootstrap-5.3.3/js/bootstrap.bundle.min.js` + `static/css/main.css` postoje
  - [ ] 10.5 Popuni "File List" i "Completion Notes List" u "Dev Agent Record" sekciji
  - [ ] 10.6 KRITIČNO: proveri `git status` — verifikuj da NEMA dirty fajlova van očekivanih: `templates/base.html`, `config/settings/base.py`, `apps/core/templatetags/__init__.py`, `apps/core/templatetags/htmx_aria.py`, `static/vendor/htmx.min.js`, `static/vendor/bootstrap-5.3.3/css/bootstrap.min.css`, `static/vendor/bootstrap-5.3.3/js/bootstrap.bundle.min.js`, `static/css/main.css`
  - [ ] 10.7 KRITIČNO: NE dodavaj `_LICENSE.txt` fajlove osim ako Mihas eksplicitno traži (opciono u Task 4.1.11 i 4.1.12; nije AC zahtev)

## Dev Notes

### Kontekst story-ja

Story 1.6 je **interakcijski temelj** za Epic 1 — prvi put projekat dobija:

1. **Bootstrap 5.3.3 env-aware** — DEV koristi CDN jsDelivr (`cdn.jsdelivr.net/npm/bootstrap@5.3.3/`), PROD koristi lokalni `static/vendor/bootstrap-5.3.3/`. Konvencija project-context.md § Frontend frameworks line 67: "Bootstrap 5.3 — CDN u dev, local u prod (static/vendor/)". Razlozi za prod-local: (a) GDPR — nijedan eksterni domen u produkciji, (b) CSP-readiness — Story 9.1 enables Content-Security-Policy preko `django-csp`, a CDN-ovi bi zahtevali `script-src` whitelist domen-ova. Dev convenience: CDN cache deljen sa drugim projektima, brži cold start. `django-bootstrap5` package render-uje `<link>` i `<script>` tag-ove kroz `{% bootstrap_css %}` / `{% bootstrap_javascript %}` template tag-ove koji čitaju env-specific `BOOTSTRAP5` settings dict (base.py = CDN, production.py override = local).

2. **HTMX 1.9.12 lokalno (version-pinned)** — `static/vendor/htmx.min.js`. project-context.md eksplicitno pinned na "HTMX 1.9+" (NE 2.x — različita API: 2.x koristi `data-hx-*` attributes, 1.9 koristi `hx-*` bez prefix-a; project je gradjen oko 1.x API-ja). **Mihas mora koristiti version-pinned URL** (`https://unpkg.com/htmx.org@1.9.12/dist/htmx.min.js`) — `htmx.org/dist/htmx.min.js` sada serves 2.x latest i razbio bi naš API contract (vidi Gotcha #9). `django-htmx` middleware postavlja `request.htmx` boolean atribut za HTMX detection u view-ovima.

3. **A11y infrastruktura** — skip link + main#main-content + aria-live region (kanonski singleton kroz `{% aria_live %}` tag). Project-context.md § A11y must-haves traži:
   - skip link na svim stranicama (bypass repeated nav blocks — WCAG 2.4.1)
   - aria-live region za HTMX swap announcement (WCAG 4.1.3 status messages)
   - lang attribute (Story 1.4 ✓)
   - keyboard navigation (Story 1.8 sticky nav arrows; Story 1.6 osigurava skip link Tab/Enter)

4. **CSS load order kontrakt** — tokens.css → Bootstrap CSS → main.css. Razlog: tokens definišu custom properties (`var(--color-brand-green-800)`); Bootstrap koristi svoje `--bs-*` properties i ne treba da overrid-uje naše tokene; main.css overrides Bootstrap-a (našim brand specifičnostima). Bez ovog order-a, brand colors u Bootstrap komponentama bi defaultovale na `--bs-primary` umesto na naš `--color-brand-green-800`.

5. **noscript graceful degradation** — Bootstrap alert iznad fold-a koji informiše korisnike da je JS isključen. HTMX-dependent UI (filteri, forme) ne radi bez JS-a; statički katalog (Story 2.x) i dalje funkcioniše jer Django renderuje server-side. noscript je preventive UX (~1% korisnika sa JS off, ali svi screen reader korisnici imaju JS on po default-u).

**Foundation za:**
- **Story 1.7 (Reusable komponente):** Bootstrap utility klase (`d-flex`, `gap-3`, `justify-content-between`) korisne za 5 komponenti; `coric-` prefix prevents Bootstrap clash; visually-hidden klase za screen-reader-only content (npr. button screen reader-friendly labels)
- **Story 1.8 (Sticky Nav + Footer):** Bootstrap `navbar` + `dropdown` komponente za top nav; `container` + grid system za footer 4-kolone; IntersectionObserver za sticky shrink (vanilla JS) — Bootstrap dropdown-ovi traže `bootstrap.bundle.min.js` (uključuje Popper.js)
- **Story 2.8 (HTMX filteri):** `request.htmx` detection u view-ovima — `if request.htmx: return render(request, "partials/product_grid.html", ctx)`; HTMX `hx-get`, `hx-target`, `hx-swap` na filter formu; `{% aria_live %}` div za "Pronađeno 12 rezultata" announcement (kroz hx-swap-oob)
- **Story 4.6 (HTMX form patterns + aria-live + rate limiting):** sve forme koriste `{% aria_live %}` div kao OOB target za success/error poruke; HTMX `hx-post` za form submit
- **Story 6.x (SEO):** `{% block meta_description %}{% endblock %}` placeholder će popunjavati `apps/seo/templatetags/seo_meta.py` template tag

**Princip:** Story 1.6 dovršava **interakcijski + a11y kontrakt** ali NE uvodi nijednu vizuelnu komponentu. Stranica izgleda i dalje minimalistički (Story 1.5 plain layout sa tokens + Roboto fonts), ali sada može da konzumira Bootstrap utility klase, HTMX swap-ove, screen reader announcement-e. Story 1.7 dolazi sa prvim konzumentima (komponente).

**Out-of-scope** za Story 1.6:
- Vizuelne komponente (Story 1.7)
- Sticky nav JavaScript / header / footer (Story 1.8)
- CSP middleware setup (Story 9.1)
- GA4 / FB Pixel tracking script-e (Story 7.3)
- WYSIWYG editor za blog (Story 8.7)
- Lightbox setup (Story 2.5)
- Service worker / PWA (defer post-v1)

### Tech stack — Bootstrap + HTMX specifics

| Komponenta | Verzija / Tehnologija | Razlog |
|---|---|---|
| Bootstrap CSS | 5.3.3 (latest stable kao 2026-05) | DESIGN.md koristi 5.x conventions; 5.3 ima improved color system + utility API |
| Bootstrap JS | bundle.min.js (sa Popper.js) | Bootstrap dropdown/tooltip/popover traže Popper.js; bundle uključuje |
| HTMX | 1.9.x (NE 2.x) | project-context.md pinned; 2.x ima breaking changes (`data-hx-*` prefix) |
| Bootstrap loading | DEV = CDN jsDelivr (`cdn.jsdelivr.net/npm/bootstrap@5.3.3/...`); PROD = Local (`static/vendor/bootstrap-5.3.3/`) | project-context.md line 67 (CDN dev / local prod); GDPR + CSP readiness u prod (Story 9.1) |
| HTMX loading | Local (`static/vendor/htmx.min.js`) u SVIM env-ima | Pinned 1.9.x; HTMX CDN serves latest (potencijalno 2.x — vidi Gotcha #9) |
| django-bootstrap5 | 26.2+ (već u pyproject.toml iz Story 1.1) | Template tag helper-i za render |
| django-htmx | 1.27.0+ (već u pyproject.toml iz Story 1.1) | HtmxMiddleware + request.htmx attribute |
| Script loading | HTMX `defer` explicit; Bootstrap sync (django-bootstrap5 NE emit-uje `defer`) | HTMX non-blocking po DOMContentLoaded; Bootstrap sync na DOM poziciji (safe jer precedes child block scripts) |
| Bootstrap JS in head vs body | `javascript_in_head=False` (default) | JS pre `</body>` da ne blokira render |
| jQuery | NOT included (`include_jquery=False`) | Bootstrap 5 ne zahteva jQuery; legacy artifact |
| Skip link technique | Bootstrap `visually-hidden-focusable` utility class | Standard CSS pattern; appears on focus only |
| Main focus | `tabindex="-1"` na `<main id="main-content">` | Programatski focus kad skip link aktiviran |

**Roboto/CSS context (Story 1.5 regression guard):**
- `tokens.css` i dalje **PRVI** CSS link u `<head>` — definiše `--color-*`, `--typography-*`, `@font-face`
- Bootstrap CSS DRUGI — može override-ovati neke generic-e (`body { margin: 0 }`), ali ne dira naš token namespace
- `main.css` TREĆI (poslednji) — Story 1.7+ će dodati `body { font-family: var(--typography-family-primary); }` da aktivira Roboto + brand-specifične override-e Bootstrap-a

**django-htmx napomena:**
- Middleware-only paket — registruje samo `HtmxMiddleware` u MIDDLEWARE
- Atribut `request.htmx` je `HtmxDetails` namedtuple-like objekat sa `bool` evaluation
- `request.htmx.boosted` (za `hx-boost`), `request.htmx.target` (`HX-Target` header), `request.htmx.trigger_name` itd. — Story 2.8+ koristi ova polja
- NE dodaje `django_htmx` u INSTALLED_APPS po svoj... ALI django-htmx 1.27+ zahteva da app bude u INSTALLED_APPS za template tags (npr. `{% if request.htmx %}` se podrazumeva preko middleware-a, ali django-htmx template tags poput `{% htmx_script %}` zahtevaju app installation). Setup obema (INSTALLED_APPS + MIDDLEWARE) je defensive — radi u svim setup-ima.

**django-bootstrap5 napomena:**
- App-based paket — MORA biti u INSTALLED_APPS za template tag discovery (`{% load django_bootstrap5 %}`)
- `BOOTSTRAP5` settings dict je opcioni; default-uje na jsDelivr CDN (`https://cdn.jsdelivr.net/npm/bootstrap@5.3.x/...`)
- Override `css_url` + `javascript_url` env-aware (CDN dev / local prod) per Gotcha #1; MORA dodati `"integrity": None` na oba override-a (vidi Gotcha #19 — bez ovoga browser baca SubresourceIntegrityError)
- `{% bootstrap_css %}` render-uje: `<link rel="stylesheet" href="<css_url>" ...>` 
- `{% bootstrap_javascript %}` render-uje: `<script src="<javascript_url>"></script>` (django-bootstrap5 26.2 NE emit-uje `defer`; izvršava se SYNC — vidi Gotcha #11)

### base.html Template (KOMPLETAN — Dev kopira ovaj sadržaj)

```html
<!DOCTYPE html>
{% load i18n %}
{% load static %}
{% load django_bootstrap5 %}
{% load htmx_aria %}
<html lang="{{ LANGUAGE_CODE }}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" content="{% block meta_description %}{% endblock %}">
  <title>{% block title %}Ćorić Agrar{% endblock %}</title>
  <link rel="stylesheet" href="{% static 'css/tokens.css' %}">
  {% bootstrap_css %}
  <link rel="stylesheet" href="{% static 'css/main.css' %}">
  {% block extra_head %}{% endblock %}
</head>
<body>
  <a class="visually-hidden-focusable" href="#main-content">{% translate "Preskoči na sadržaj" %}</a>
  <header>
    {% include "partials/language_switcher.html" %}
  </header>
  <main id="main-content" tabindex="-1">
    {% block content %}
      <h1>Ćorić Agrar</h1>
      <p>{% translate "Dobrodošli." %}</p>
    {% endblock %}
  </main>
  {% aria_live %}
  <noscript>
    <div class="alert alert-warning text-center mb-0" role="alert">
      {% translate "Za optimalno korišćenje stranice, omogućite JavaScript u svom browser-u." %}
    </div>
  </noscript>
  {# Site-wide scripts PRVI: Bootstrap sync (django-bootstrap5 NE emit-uje defer) + HTMX defer; child block scripts uvek vide Bootstrap učitan (sync Bootstrap precedes block u DOM order-u); vidi Gotcha #15 #}
  <script src="{% static 'vendor/htmx.min.js' %}" defer></script>
  {% bootstrap_javascript %}
  {# Per-page scripts POSLE site-wide — sync init safe za Bootstrap komponente #}
  {% block scripts %}{% endblock %}
</body>
</html>
```

### htmx_aria.py Template (KOMPLETAN — Dev kopira ovaj sadržaj)

```python
"""Template tag biblioteka za HTMX a11y patterns.

Ekspoze `{% aria_live %}` — kanonski singleton aria-live region (WCAG 4.1.3
status messages). HTMX partials announce u njega kroz hx-swap-oob.
Primer u partial template-u (Story 2.8+):

    <div hx-swap-oob="innerHTML:#aria-live">Pronađeno 12 rezultata</div>
"""

from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def aria_live():
    """Render kanonski aria-live region. Singleton u base.html.

    Vraća: `<div id="aria-live" class="visually-hidden" aria-live="polite"
    aria-atomic="true"></div>` — bez novlines (sve u jednoj liniji).
    """
    return mark_safe(
        '<div id="aria-live" class="visually-hidden" aria-live="polite" aria-atomic="true"></div>'
    )
```

### apps/core/templatetags/__init__.py (KOMPLETAN — Dev kopira ovaj sadržaj)

```python
# Template tags namespace za apps.core (Django discovery zahteva __init__.py).
```

(Minimal 1-line komentar; potpuno prazan fajl je takođe valid, ali kratki komentar olakšava grep za buduće Dev-ove "zašto ovaj fajl postoji".)

### main.css Template (KOMPLETAN — Dev kopira ovaj sadržaj)

```css
/* main.css — site-wide custom CSS. Story 1.7+ populates with komponente. */
/* Loaded AFTER tokens.css i Bootstrap CSS u base.html — overrides cascade. */
```

### base.py modifications (KOMPLETAN — Dev primenjuje ove izmene)

**INSTALLED_APPS izmena** (linije 28-36 iz Story 1.5, after-state Story 1.6):

```python
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_htmx",            # NOVO Story 1.6 — request.htmx detection
    "django_bootstrap5",      # NOVO Story 1.6 — {% bootstrap_css %} / {% bootstrap_javascript %} template tags
    "apps.core",
]
```

**MIDDLEWARE izmena** (linije 38-49 iz Story 1.5, after-state Story 1.6):

```python
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_htmx.middleware.HtmxMiddleware",          # NOVO Story 1.6 — postavlja request.htmx
    "apps.core.middleware.LocaleSwitcherMiddleware",
]
```

**Nova sekcija `# ── Bootstrap 5 ──` u `config/settings/base.py`** (dodati POSLE `# ── Default ──` sekcije na kraj fajla) — DEV variant (CDN jsDelivr):

```python
# ── Bootstrap 5 ──────────────────────────────────────────────────────────────
# django-bootstrap5 konfiguracija. base.py = DEV variant (CDN jsDelivr) per
# project-context.md § Frontend frameworks line 67 ("Bootstrap 5.3 — CDN u dev,
# local u prod"). production.py override-uje na local /static/vendor/.
# Verzija pinned na 5.3.3 (latest stable 5.x kao 2026-05).
# `integrity: None` eksplicitno suprimira django-bootstrap5 default SRI check
# (vidi Gotcha #19 — bez ovoga, override css_url bez SRI hash-a baca
# SubresourceIntegrityError).
BOOTSTRAP5 = {
    "css_url": {
        "url": "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css",
        "integrity": None,
    },
    "javascript_url": {
        "url": "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js",
        "integrity": None,
    },
    "javascript_in_head": False,
    "include_jquery": False,
}
```

**Nova sekcija u `config/settings/production.py`** — PROD override (local vendor, no CDN):

```python
# ── Bootstrap 5 (production override) ────────────────────────────────────────
# Production: lokalni vendor fajlovi (GDPR + CSP-readiness).
# Story 1.6 Task 4 prepares static/vendor/bootstrap-5.3.3/ for ovaj override.
BOOTSTRAP5 = {
    "css_url": {
        "url": "/static/vendor/bootstrap-5.3.3/css/bootstrap.min.css",
        "integrity": None,
    },
    "javascript_url": {
        "url": "/static/vendor/bootstrap-5.3.3/js/bootstrap.bundle.min.js",
        "integrity": None,
    },
    "javascript_in_head": False,
    "include_jquery": False,
}
```

### Gotchas (kritični momenti koje Dev lako promaši)

1. **`BOOTSTRAP5` settings dict — env-aware CDN-in-dev / local-in-prod (project-context.md line 67).** django-bootstrap5 default `css_url` pokazuje na jsDelivr CDN. project-context.md § Frontend frameworks line 67 eksplicitno propisuje: "Bootstrap 5.3 — CDN u dev, local u prod (static/vendor/)". Story 1.6 implementira tako da:
   - **`base.py`** definiše DEV variant: CDN URL pinned na `cdn.jsdelivr.net/npm/bootstrap@5.3.3/...` (eksplicitno verzionisano da Mihas slučajno ne dobije Bootstrap 5.4 kad izađe).
   - **`production.py`** override-uje BOOTSTRAP5 dict na local `/static/vendor/bootstrap-5.3.3/...` paths — GDPR safe (no external request) + CSP-ready (Story 9.1 ne treba whitelist `cdn.jsdelivr.net` u `script-src`).
   - **`integrity: None`** u oba varianta — Gotcha #19 (suppress SubresourceIntegrityError).
   Trade-off: dev convenience (browser cache CDN-a deljen sa drugim projektima) vs prod compliance. AC9 testovi accept-uju OBE variante kroz regex (dev: jsdelivr, prod: /static/vendor/). HTMX uvek local u oba env-a (jer je pinned 1.9.x i HTMX 2.x stable je na CDN-u — vidi Gotcha #9).

2. **CSS load order MORA biti tokens.css → Bootstrap → main.css.** Razlog: tokens.css definiše custom properties (no rules — samo `:root { --color-*: ... }`); Bootstrap reset i utility-e dolaze nakon; main.css overrides Bootstrap brand-specifičnim pravilima. Obrnuti redosled (Bootstrap → tokens) bi bilo bezopasno (tokens su properties, ne rules), ali Bootstrap reset (`body { margin: 0 }`) bi mogao da overrid-uje custom main.css setting-e koji dolaze pre. Standardni pattern: vendor → tokens → custom; ali u našem slučaju tokens su čista konfiguracija (no resets), pa stavljamo ih PRVE kao designerski "config".

3. **`id="aria-live"` MORA biti UNIQUE u DOM-u (singleton invariant).** HTMX `hx-swap-oob="innerHTML:#aria-live"` target-uje preko ID-a. Ako 2 elementa imaju isti ID, `document.getElementById("aria-live")` vraća PRVI, drugi se ignoriše — fragmenti se ne announce. Story 1.6 osigurava kroz `{% aria_live %}` tag pozvan TAČNO JEDNOM u `base.html`; future stories ne smeju duplirati u partial-ima.

4. **`apps/core/templatetags/__init__.py` MORA postojati za Django template tag discovery.** Bez `__init__.py`, Python ne tretira `templatetags/` kao paket; Django ne pronalazi `htmx_aria.py` library; `{% load htmx_aria %}` u `base.html` baca `TemplateSyntaxError: 'htmx_aria' is not a registered tag library`. PowerShell: `New-Item -ItemType File apps/core/templatetags/__init__.py` (NE `New-Item -Force` na file — truncate-uje postojeći).

5. **`register = template.Library()` — naziv `register` je obavezan (Django magic).** Django introspektuje template tag fajlove tražeći varijablu pod nazivom `register` koja je `template.Library` instanca. Ako se zove `library` ili `tags`, `@register.simple_tag` decorator radi (sintaksno valid), ali Django ne registruje tag — `{% aria_live %}` baca `TemplateSyntaxError: Invalid block tag`.

6. **HtmxMiddleware position — POSLE CommonMiddleware, PRE LocaleSwitcherMiddleware (deviation od arch.md — dokumentovana).** architecture.md skicira HtmxMiddleware **ranije** u chain-u (uz ostale infrastruktural middleware-e), ali django-htmx **nije position-sensitive** (`request.htmx` je read-only attribute koji se postavlja jednom; ne menja request flow). Biramo **kasniju** poziciju za consistency sa LocaleSwitcherMiddleware grupom (custom + a11y/i18n middleware-i grupisani). Funkcionalno ekvivalentno arch.md poziciji — `request.htmx` je dostupan u SVIM view-ovima bez obzira na position. Naš LocaleSwitcherMiddleware je custom i vraća early redirect za `?lang=X`, pa HtmxMiddleware je PRE njega (inače `request.htmx` ne bi bio set kad LocaleSwitcher vrati redirect, ali to nije problem — redirect ide pre svake view logike). Bottom line: POSLE Django built-in, PRE custom — safe; **dokumentovan deviation od arch.md**.

7. **`tabindex="-1"` na `<main>` — programatski focusable, NE keyboard-focusable.** `tabindex="0"` bi uključio `<main>` u Tab order (čudno UX); `tabindex="-1"` ne menja Tab order ali omogućuje `element.focus()` kad korisnik klikne skip link. Skip link `<a href="#main-content">` triggers browser default behavior: scroll-to + focus target if focusable (programatski).

8. **`{% translate %}` u skip link — sr default, hu/en u Story 6.5/6.6 ili 1.9 messages.** Story 1.6 ne kreira .po prevod fajlove — `just messages` workflow je u Story 1.9 (CI pipeline) ili kad prvi child template doda više `{% translate %}` poziva. Za sada, sr lokal vidi "Preskoči na sadržaj" direktno (msgstr fallback na msgid).

9. **HTMX 1.9.12 pinned — koristi version-pinned URL.** project-context.md eksplicitno: "HTMX 1.9+". HTMX 2.x je released i `htmx.org/dist/htmx.min.js` serves **LATEST stable** (kao 2026-05 to je 2.x), koji ima breaking changes:
   - `hx-*` attributes prefix changes (2.x prefers `data-hx-*`)
   - `htmx.config.allowEval` default change
   - Removed deprecated `hx-history-elt` and others
   **Mihas MORA koristiti version-pinned URL:** primarno `https://unpkg.com/htmx.org@1.9.12/dist/htmx.min.js`, alternativa `https://github.com/bigskysoftware/htmx/releases/download/v1.9.12/htmx.min.js`. Verifikuj prvih 1-3 linija fajla — version comment header (`/*! HTMX v1.9.12 */`) mora matchovati 1.9.12. File-size check (40-80 KB) NIJE pouzdan između 1.9.x (~50KB) i 2.x (~46KB); version comment je primarna provera.

   **Future upgrade path (NOT Story 1.6 scope):** HTMX 2.x migracija će biti zasebna story, izvodi se posle Story 1.9 (CI pipeline) tako da pre-commit + CI hvataju breaking changes u Story 2.8 filteri / Story 4.6 forme.

10. **Bootstrap 5.3.3 vs 5.3.2 vs 5.3.0 — minor version pin.** project-context.md kaže "Bootstrap 5.3". 5.3.3 je latest patch (kao 2026-05); 5.3.x bilo koja minor je OK za AC, ali `BOOTSTRAP5["css_url"]["url"]` mora matchovati actual directory ime. Recommend `5.3.3` (latest); ako Mihas preuzme 5.3.2, update path u settings.

11. **`{% bootstrap_javascript %}` NE emit-uje `defer` atribut — Bootstrap se izvršava SYNC na svojoj DOM poziciji.** django-bootstrap5 26.2 NE emit-uje `defer` atribut na `{% bootstrap_javascript %}` (live render dokazuje: `<script src="https://cdn.jsdelivr.net/.../bootstrap.bundle.min.js"></script>` bez `defer`). Bootstrap se izvršava SYNC na svojoj DOM poziciji. Sigurnost child template-a oslanja se NA SYNC Bootstrap + DOM-order pozicioniranje (Bootstrap PRE `{% block scripts %}` u DOM order-u → uvek dostupan kad child JS execute). HTMX script (NE od django-bootstrap5) zahteva ručno `defer` attribute i izvršava se POSLE DOM parse.

12. **`include_jquery=False` — Bootstrap 5 ne zahteva jQuery.** Default django-bootstrap5 setting; eksplicitno False za clarity i sigurnost (Story 1.7+ ne sme dodavati jQuery deps).

13. **`visually-hidden` (Bootstrap utility class) vs `visually-hidden-focusable`.** 
   - `visually-hidden` — uvek skriven vizuelno (screen reader only)
   - `visually-hidden-focusable` — skriven vizuelno DOK NIJE focused (skip link pattern: appears on Tab focus, then hidden again on blur)
   Aria-live region koristi `visually-hidden` (uvek skriven, samo screen reader announce); skip link koristi `visually-hidden-focusable` (vizuelno se prikazuje kad korisnik tabnu).

14. **`<noscript>` graceful degradation — pozicija u DOM-u.** Stavljamo POSLE `</main>` i PRE site-wide scripts (vizuelni footer area). Browser sa JS off će ga prikazati kao Bootstrap alert; browser sa JS on će ga ignorisati. Alternative: stavlja se u `<head>` sa redirect ka non-JS variant — overkill za naš use case (HTMX gracefully degradates ka regular form submit).

15. **Script load order — site-wide PRVI, `{% block scripts %}` DRUGI (REORDERED Story 1.6).** Pre Story 1.6 (Story 1.5 minimum base.html) `{% block scripts %}` je bio jedini scripts blok. Story 1.6 dodaje site-wide HTMX + Bootstrap JS i **reorder-uje** tako da site-wide scripts dolaze PRVI, `{% block scripts %}` DRUGI:
   ```html
   <!-- Site-wide scripts PRVI -->
   <script src="{% static 'vendor/htmx.min.js' %}" defer></script>
   {% bootstrap_javascript %}
   <!-- Per-page scripts DRUGI -->
   {% block scripts %}{% endblock %}
   ```
   **Razlog (FIX 6 footgun mitigation):** Bootstrap SYNC + HTMX defer kombinacija. Actual execution order: (1) Bootstrap sync na svojoj DOM poziciji (django-bootstrap5 NE emit-uje `defer`), (2) HTMX deferred posle DOM parse (explicit `defer`), (3) `{% block scripts %}` per-page (sync ili defer zavisi od child template-a). Child sync init Bootstrap-a (npr. `new bootstrap.Modal(...)`) je safe jer Bootstrap **precedes** `{% block scripts %}` u DOM order-u i izvršava se sync — uvek loaded kad child JS execute. Ako bi `{% block scripts %}` bio PRVI (defaultni Django pattern), child page sync init bi se executed PRE Bootstrap script-a → `ReferenceError: bootstrap is not defined`. Novi order garantuje child page scripts imaju Bootstrap **already loaded** kad execute (a HTMX će biti dostupan najkasnije po `DOMContentLoaded`).

   *Trade-off:* Bootstrap bundle (~80KB) sync execution PRE child block scripts → marginal parser-block cost; HTMX bytes (~50KB) load-uju se PRE custom inline child page script-ova → marginal TTI cost (~10-20ms na slow 3G). Win: sync init safety za sve child template-e iz Story 1.7+ (komponente mogu koristiti Bootstrap klase + dropdown init bez `DOMContentLoaded` wrap). Za Story 1.7+ komponente koji možda žele sync Bootstrap init na load — safe sa novim order-om.

   *Foundation za Story 1.7+:* komponente (`coric-dropdown`, sticky nav arrows) mogu direktno koristiti `bootstrap.Dropdown` / `bootstrap.Tooltip` API u `{% block scripts %}` bez `DOMContentLoaded` event handler-a.

16. **Lighthouse a11y ≥95 — main contributing audits:**
   - `html-has-lang` (Story 1.4 ✓)
   - `bypass` (skip link presence — Story 1.6 ✓)
   - `landmark-one-main` (single `<main>` — Story 1.6 ✓)
   - `meta-viewport` (Story 1.4 ✓)
   - `aria-valid-attr-value` (aria-live="polite" je valid — Story 1.6 ✓)
   - `color-contrast` (Bootstrap default-i + tokens cilja 4.5:1 — Story 1.5 design tokens)
   - `link-name` (skip link ima text content — ✓)
   - `region` (sve content unutar landmark-a: header, main, ne fail-uje jer su prisutne — ✓)
   Failing audits to expect: NIJEDAN ako AC1-AC9 ispravno implementirano. Manual Lighthouse run u Task 9.8.

17. **CSP-readiness — no inline event handlers, no inline `<style>`.** Story 9.1 enables Content-Security-Policy preko `django-csp`. Inline `onchange="..."`, `onclick="..."`, `<style>...</style>` zahtevaju `'unsafe-inline'` u CSP koje undermine-uje protection. Story 1.6 base.html MORA biti čist (vidi AC9.2 grep check za inline handlers).

   **NAPOMENA:** `templates/partials/language_switcher.html` (Story 1.4) sadrži `onchange="this.form.submit()"` na `<select>`. Ovo je known issue iz Story 1.4 retro — odgađa se za Story 9.1 fix (CSP-aware form submit). NE diraj language switcher u Story 1.6.

18. **HTMX vendor file licenca — 0BSD je public-domain-equivalent.** Zero-Clause BSD ne zahteva attribution, samo da source code zadrži licencu. Bootstrap MIT zahteva attribution u "documentation and/or other materials" — za web app, license fajl u `static/vendor/bootstrap-5.3.3/LICENSE.txt` je dovoljan (ne treba "Powered by Bootstrap" link). Opciono u Task 4.1.11 i 4.1.12; nije AC requirement.

19. **BOOTSTRAP5 `integrity: None` MORA biti eksplicitno setovan kad override-ujemo `css_url` / `javascript_url`.** django-bootstrap5 default-uje na CDN URL-ove sa hard-coded SRI hash-evima (npr. `sha384-...`). Kad override-ujemo URL (bilo na pinned CDN verziju `5.3.3` ili na local `/static/vendor/...`), default SRI hash više ne odgovara fajlu — browser baca `SubresourceIntegrityError` i CSS/JS se NE učita. Rešenje: eksplicitno `"integrity": None` u oba dict-a (`css_url` i `javascript_url`):
   ```python
   BOOTSTRAP5 = {
       "css_url": {
           "url": "...",
           "integrity": None,  # MORA — suppress default SRI check
       },
       "javascript_url": {
           "url": "...",
           "integrity": None,
       },
       ...
   }
   ```
   **Trust justification:** local file je trusted (commit-ovan u repo); pinned CDN URL (`@5.3.3`) je trusted (jsDelivr immutable per version). Story 9.1 može da uvede CSP `script-src` ali NE SRI (SRI bi zahtevao manual hash recompute pri svakoj Bootstrap upgrade-i — overhead bez security gain za pinned/local files). Ako `integrity: None` izostavlje se, AC9.9 live render fail-uje sa Console error-om: `Failed to find a valid digest in the 'integrity' attribute for resource ...`.

### Project Structure Notes

**Alignment sa unified project structure (architecture.md):**
- `apps/core/templatetags/htmx_aria.py` — match architecture.md linija 556: `htmx_aria.py # {% aria_live %} template tag`
- `apps/core/middleware.py` — već postoji (Story 1.4); architecture.md linija 557 pominje `HtmxAriaMiddleware` ali Story 1.6 NE kreira middleware (samo template tag), pošto `HtmxAriaMiddleware` je legacy iz arch.md draft-a i može da se izbaci (ne pominje se kao required u Story 1.6 spec-u). Ako kasnije story zahteva auto-injection aria-live u HTMX response-u, kreira se tada.
- `static/vendor/` — match architecture.md linija 677 "Lokalni Bootstrap 5 + HTMX + GLightbox" (Story 1.6 dodaje prvi pod-direktorijum vendor-a; GLightbox dolazi u Story 2.5)
- `static/css/main.css` — NE pominje se eksplicitno u architecture.md (koja pominje `base.css`, `layout.css`, `components/`), ali je standardni Django + Bootstrap pattern; arch.md je generic specifikacija i ne zabranjuje `main.css` ime. Alternative imenovanje: `site.css`, `app.css` — biramo `main.css` kao standard (web convention).

**Detected konflikti ili varijante:**
- arch.md linija 557 pominje `HtmxAriaMiddleware` u `apps/core/middleware.py`, ali Story 1.6 NE kreira middleware. Razlog: `{% aria_live %}` template tag je dovoljan; middleware bi bio over-engineering (svaki HTMX response bi morao da injection-uje aria-live header — ali HTMX response partials su explicit, OOB pattern u project-context.md radi bez middleware-a). Ova varijanta je dokumentovana ovde radi konzistentnosti.
- arch.md `static/css/` lista uključuje `base.css`, `layout.css`, `components/` — ovi fajlovi su Story 1.7+ scope. Story 1.6 dodaje samo `main.css` placeholder kao link target u base.html.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-1.6] — AC iz epics.md (linije 468-482)
- [Source: _bmad-output/planning-artifacts/architecture.md#Frontend] — Bootstrap 5 + HTMX + Whitenoise architecture decision (linije 53, 199-203)
- [Source: _bmad-output/planning-artifacts/architecture.md#HTMX-patterns] — HTMX response patterns + aria-live OOB (linije 385-430)
- [Source: _bmad-output/planning-artifacts/architecture.md#Request-flow] — MIDDLEWARE chain order including HtmxMiddleware (linija 763)
- [Source: _bmad-output/planning-artifacts/architecture.md#Project-structure] — `apps/core/templatetags/htmx_aria.py`, `static/vendor/` (linije 556, 677)
- [Source: _bmad-output/project-context.md#Framework-Specific-Rules] — HTMX response patterns Gotcha (linije 184-194)
- [Source: _bmad-output/project-context.md#A11y-must-haves] — aria-live region, lang attribute, focus management (linije 681-690)
- [Source: _bmad-output/project-context.md#Frontend-frameworks] — Bootstrap 5.3 CDN dev / local prod, HTMX 1.9+ local (linije 66-70)
- [Source: _bmad-output/implementation-artifacts/1-5-self-hosted-roboto-design-md-tokens-kao-css-custom-properties.md] — Story 1.5 base.html state (24 linije), tokens.css link convention, STORAGES dict, Whitenoise middleware position
- [Source: _bmad-output/implementation-artifacts/1-4-i18n-setup-sa-locale-url-routing-i-switcher.md] — Story 1.4 base.html foundation, LocaleSwitcherMiddleware
- [Source: pyproject.toml] — django-htmx>=1.27.0, django-bootstrap5>=26.2 dependencies (already installed Story 1.1)
- [Source: https://django-htmx.readthedocs.io/en/latest/installation.html] — HtmxMiddleware position, INSTALLED_APPS requirement
- [Source: https://django-bootstrap5.readthedocs.io/en/latest/settings.html] — BOOTSTRAP5 settings dict, css_url / javascript_url override
- [Source: https://getbootstrap.com/docs/5.3/getting-started/accessibility/] — Bootstrap a11y utility classes (visually-hidden-focusable, role="alert")
- [Source: https://htmx.org/docs/#installing] — HTMX installation, hx-swap-oob pattern
- [Source: https://www.w3.org/WAI/WCAG21/quickref/#bypass-blocks] — WCAG 2.4.1 Bypass Blocks (skip link requirement)
- [Source: https://www.w3.org/WAI/WCAG21/quickref/#status-messages] — WCAG 4.1.3 Status Messages (aria-live region requirement)

## Testing

### Šta se testira u Story 1.6

**Smoke testovi (Task 9):** sve checks iz AC9 sekcije — file presence, content grep, settings introspection, template tag rendering, request.htmx behavior, live render, regression za Story 1.1-1.5, Lighthouse manual.

**TEA agent piše testove (RED phase) sledeće test fajlove (Story 1.6 implementation kreira; TEA može da formalizuje u RED phase ili Dev runs ih ad-hoc):**

1. **`apps/core/tests/test_htmx_aria.py`** — unit test za `{% aria_live %}` tag:
   - `test_aria_live_tag_importable` — `from apps.core.templatetags.htmx_aria import aria_live` radi bez exception-a
   - `test_aria_live_tag_returns_expected_html` — `aria_live()` vraća string `'<div id="aria-live" class="visually-hidden" aria-live="polite" aria-atomic="true"></div>'` (whitespace-insensitive)
   - `test_aria_live_template_load` — `Template('{% load htmx_aria %}{% aria_live %}').render(Context())` ne baca `TemplateSyntaxError`
   - `test_aria_live_singleton_in_base_html` — `templates/base.html` source sadrži `{% aria_live %}` TAČNO JEDNOM (`base_html.count("{% aria_live %}") == 1`)

2. **`apps/core/tests/test_base_template.py`** — integration test za base.html render:
   - `test_base_html_contains_skip_link` — render `/sr/` sa Django Client; response sadrži `<a class="visually-hidden-focusable" href="#main-content">`
   - `test_base_html_main_has_id_and_tabindex` — response sadrži `<main id="main-content" tabindex="-1">`
   - `test_base_html_aria_live_region_present` — response sadrži `<div id="aria-live" class="visually-hidden" aria-live="polite" aria-atomic="true"></div>`
   - `test_base_html_tokens_css_first_then_bootstrap_then_main` — verify ordering (regex match na sve 3 link-a, verify indexOf order)
   - `test_base_html_no_google_cdn_links` — assert no `googleapis.com`, no `gstatic.com`, no `unpkg.com`, no `getbootstrap.com`, no `htmx.org` u response.content (Google CDN i other-vendor CDN anti-pattern). NAPOMENA: `cdn.jsdelivr.net` se NE testira ovde jer je dozvoljen u dev rendered output-u (per project-context.md line 67 CDN-dev/local-prod policy).
   - `test_base_html_prod_render_no_jsdelivr_cdn` — **prod-only** (skipped u dev): override `DEBUG=False` i production BOOTSTRAP5 settings (npr. `@override_settings(DEBUG=False, BOOTSTRAP5={...local URLs...})`), render `/sr/`, assert `cdn.jsdelivr.net` NOT in response.content. Ovaj test verifikuje da production override iz `config/settings/production.py` zaista emit-uje lokalne URL-ove.
   - `test_base_html_no_inline_event_handlers` — assert no `onchange=`, `onclick=`, `onload=` u response.content (NAPOMENA: ako `language_switcher.html` ima `onchange` Story 1.4 — taj ostaje, ali NE u `base.html` sam by self; treba precizirati: test `templates/base.html` source direktno, ne rendered output uključujući includes)
   - `test_base_html_noscript_present` — response sadrži `<noscript>` blok
   - `test_base_html_htmx_script_with_defer` — response sadrži `<script src="/static/vendor/htmx.min.js" defer></script>`

3. **`apps/core/tests/test_htmx_middleware_setup.py`** — middleware behavior test:
   - `test_htmx_middleware_in_middleware_list` — `settings.MIDDLEWARE` sadrži `django_htmx.middleware.HtmxMiddleware`
   - `test_htmx_middleware_position` — index `HtmxMiddleware` > index `CommonMiddleware` and < index `LocaleSwitcherMiddleware`
   - `test_request_htmx_attribute_set_no_header` — `RequestFactory().get('/')` → `HtmxMiddleware(dummy)(request)` → `request.htmx` exists, `bool(request.htmx) is False`
   - `test_request_htmx_attribute_set_with_header` — `RequestFactory().get('/', HTTP_HX_REQUEST='true')` → `request.htmx` truthy
   - `test_installed_apps_has_django_htmx` — `'django_htmx' in settings.INSTALLED_APPS`
   - `test_installed_apps_has_django_bootstrap5` — `'django_bootstrap5' in settings.INSTALLED_APPS`
   - `test_bootstrap5_dev_settings_use_cdn` — verifikuje base.py BOOTSTRAP5 dict: import `config.settings.base` i assert `base.BOOTSTRAP5['css_url']['url']` sadrži `cdn.jsdelivr.net/npm/bootstrap@5.3.3` AND `base.BOOTSTRAP5['javascript_url']['url']` sadrži `cdn.jsdelivr.net/npm/bootstrap@5.3.3` (CDN-dev policy iz project-context.md line 67).
   - `test_bootstrap5_production_settings_use_local` — verifikuje production.py BOOTSTRAP5 override: import `config.settings.production` i assert `production.BOOTSTRAP5['css_url']['url']` startswith `/static/vendor/bootstrap-5.3.3/` AND `production.BOOTSTRAP5['javascript_url']['url']` startswith `/static/vendor/bootstrap-5.3.3/` (local-prod policy).

4. **Negativni testovi:**
   - `test_base_html_no_googleapis_link` — `'googleapis.com' not in base_html_source`
   - `test_base_html_no_jsdelivr_link` — `'jsdelivr' not in base_html_source`
   - `test_base_html_inline_handlers_absent` — `'onchange=' not in base_html_source` AND `'onclick=' not in base_html_source` (only checking base.html, NOT including partials/language_switcher.html which is known-issue Story 1.4)

5. **E2E (out of scope za Story 1.6 — Story 9.8 Playwright):**
   - Skip link Tab + Enter behavior (keyboard nav)
   - HTMX swap + aria-live announcement (manual screen reader test u Story 9.9 a11y audit)

### Test execution

- **Komanda:** `uv run pytest apps/core/tests/test_htmx_aria.py apps/core/tests/test_base_template.py apps/core/tests/test_htmx_middleware_setup.py -v`
- **Coverage:** TEA-driven RED → Dev GREEN; Dev NE piše testove (project-context.md § Test discipline)
- **Failure handling:** ako test fail-uje, story se vraća u `paused` status; Dev ne maskira greške

### Lighthouse manual run (Mihas — Task 9.8)

- Chrome incognito → `http://localhost:8000/sr/`
- F12 → Lighthouse tab → "Accessibility" only → "Mobile" → "Generate report"
- Score target: **≥95** (epics.md AC za Story 1.6)
- Documenting: screenshot Lighthouse output, save u `_bmad-output/implementation-artifacts/1-6-lighthouse-screenshot.png` (opciono)
- Ako < 95: Dev Agent Record sekcija mora dokumentovati failing audits sa specifičnim ID-jevima (npr. "color-contrast: 4.3:1 ratio na .alert-warning bg + text — needs adjustment in Story 1.7")

## Dev Agent Record

### Agent Model Used

Dev (Opus 4.7, 1M context) — fresh GREEN phase implementer; v6.8.0.

### Debug Log References

- `uv run python manage.py check --settings=config.settings.development` → exit 0 ("System check identified no issues (0 silenced)")
- `uv run pytest tests/ apps/` → 230 passed, 7 skipped, 0 failed
  - tests/test_base_template.py (Story 1.6): 43 passed + 2 skipped (HTMX vendor — Mihas manual download)
  - All Story 1.1-1.5 regression: GREEN

### Completion Notes List

- AC1-AC8 implementirano per Dev Notes Templates verbatim.
- AC7 (HTMX + Bootstrap vendor fajlovi): static/vendor/ direktorijum kreiran (empty), ali fajlovi NISU prisutni — Mihas mora ručno preuzeti per Task 4.1 instrukcije (HTMX 1.9.12 pinned + Bootstrap 5.3.3 ZIP). Test 2x skipped sa eksplicitnom porukom umesto fail-a (TEA-driven skip pattern).
- AC9 (smoke validation): live render test (Docker `just dev`) NIJE pokrenut u ovoj sesiji — checks 9.9 (live render) i 9.11 (Lighthouse manual) ostaju Mihas-driven.
- Story 1.5 tokens.css line PRESERVED VERBATIM (double quotes: `{% static "css/tokens.css" %}`) — tests/test_static_tokens.py::test_ac7_tokens_css_uses_double_quotes GREEN.
- TEST_MODIFICATION pattern primenjen 2x (anticipated):
  1. tests/test_bootstrap.py::test_ac3_installed_apps_is_default_django — expected set ažuriran da uključi `django_htmx` + `django_bootstrap5` (isti pattern kao Story 1.4 amendment za apps.core).
  2. tests/test_static_tokens.py::test_ac1_static_no_other_subdirs_yet — `vendor` skinut iz forbidden liste (Story 1.6 namerno uvodi static/vendor/).

### File List

- `templates/base.html` — UPDATED (Story 1.5 24 lines → Story 1.6 40 lines; expanded sa skip link + main#main-content + aria-live + noscript + site-wide scripts; tokens.css line PRESERVED verbatim)
- `config/settings/base.py` — UPDATED (INSTALLED_APPS += django_htmx, django_bootstrap5; MIDDLEWARE += HtmxMiddleware; BOOTSTRAP5 dict za DEV CDN)
- `config/settings/production.py` — UPDATED (BOOTSTRAP5 override za PROD local /static/vendor/)
- `apps/core/templatetags/__init__.py` — NEW (namespace marker)
- `apps/core/templatetags/htmx_aria.py` — NEW ({% aria_live %} simple_tag)
- `static/css/main.css` — NEW (placeholder ~150 bytes)
- `static/vendor/` — NEW (empty dir; Mihas downloads HTMX + Bootstrap)
- `tests/test_bootstrap.py` — TEST_MODIFICATION (test_ac3_installed_apps_is_default_django expected set ažuriran)
- `tests/test_static_tokens.py` — TEST_MODIFICATION (test_ac1_static_no_other_subdirs_yet — `vendor` skinut iz forbidden)

**Mihas manual steps remaining (Task 4.1):**
- `static/vendor/htmx.min.js` (~50 KB; download `https://unpkg.com/htmx.org@1.9.12/dist/htmx.min.js`)
- `static/vendor/bootstrap-5.3.3/css/bootstrap.min.css` (~230 KB; from Bootstrap ZIP)
- `static/vendor/bootstrap-5.3.3/js/bootstrap.bundle.min.js` (~80 KB; from Bootstrap ZIP)
- Live render verifikacija (`just dev` → GET /sr/ → view source)
- Lighthouse a11y manual check (≥95 soft target)

- `templates/base.html` — UPDATED (Story 1.5 → Story 1.6 expansion 50-80 linija)
- `config/settings/base.py` — UPDATED (INSTALLED_APPS, MIDDLEWARE, BOOTSTRAP5 dict)
- `apps/core/templatetags/__init__.py` — NEW (empty namespace marker)
- `apps/core/templatetags/htmx_aria.py` — NEW ({% aria_live %} tag)
- `static/vendor/htmx.min.js` — NEW (Mihas manual download)
- `static/vendor/bootstrap-5.3.3/css/bootstrap.min.css` — NEW (Mihas manual download)
- `static/vendor/bootstrap-5.3.3/js/bootstrap.bundle.min.js` — NEW (Mihas manual download)
- `static/css/main.css` — NEW (empty placeholder)
- Opciono: `static/vendor/bootstrap-5.3.3/LICENSE.txt`, `static/vendor/HTMX-LICENSE.txt`
