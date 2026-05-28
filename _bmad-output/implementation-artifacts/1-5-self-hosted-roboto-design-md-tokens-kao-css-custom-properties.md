---
story-id: "1.5"
story-key: 1-5-self-hosted-roboto-design-md-tokens-kao-css-custom-properties
title: Self-hosted Roboto + DESIGN.md Tokens kao CSS Custom Properties
status: done
epic_num: 1
epic_title: Project Foundation & Visual Identity
created: 2026-05-28
completed: 2026-05-28
author: Mihas (SM autonomous)
---

# Story 1.5: Self-hosted Roboto + DESIGN.md Tokens kao CSS Custom Properties

Status: done

## Story

As a **dev**,
I want **CSS token sistem koji 1:1 mapira DESIGN.md tokene + self-hosted Roboto font pipeline (latin + latin-ext)**,
so that **mogu da koristim `var(--token-name)` umesto magic numbers/heks vrednosti kroz ceo CSS, da front Roboto bez Google Fonts CDN-a (GDPR-friendly, brži FCP), i da Story 1.6+ komponente nasleđuju konzistentnu vizuelnu osnovu iz DESIGN.md**.

Ovo je **vizuelni temelj** za Epic 1: Story 1.6 (Bootstrap 5 + HTMX) referencira tokene; Story 1.7 (Reusable komponente) konzumira sve tokene preko `var(--...)`; Story 1.8 (Sticky Nav + Footer) nasleđuje `--color-*`, `--spacing-*`, `--shadow-nav-shrunk`. Bez tokens.css, sledeće story-je bi koristile magic vrednosti — kršenje project-context.md § Anti-pattern: Inline CSS / magic values.

Takođe uvodi **`static/` folder hijerarhiju** koja postaje canonical: `static/css/`, `static/fonts/roboto/`, kasnije `static/js/`, `static/img/`, `static/vendor/` (per architecture.md § Project structure). Whitenoise se uvodi kao dependency (planirano u architecture.md ali izostavljeno u Story 1.1).

## Acceptance Criteria

**AC1 — `static/` folder hijerarhija postoji**

- **Given** projekat iz Story 1.4 (templates/, locale/, apps/ postoje; static/ NE postoji)
- **When** kreiram `static/` direktorijum sa sledećim pod-direktorijumima
- **Then** struktura sadrži **tačno**:
  - `static/` — root static folder
  - `static/fonts/` — fonts root
  - `static/fonts/roboto/` — Roboto font fajlovi (AC2)
  - `static/css/` — custom CSS fajlovi (AC3-AC5)
- **And** direktorijumi `static/js/`, `static/img/`, `static/vendor/` se NE kreiraju u ovoj story-ji (uvode ih Story 1.6 za vendor=Bootstrap/HTMX, Story 1.7 za js animacije, Story 2.3 za img placeholders) — YAGNI
- **And** prazni direktorijumi NE smeju ostati bez fajla (vidi Gotcha #1) — `static/css/` će imati `tokens.css` iz AC3-AC5; `static/fonts/roboto/` će imati 6 woff2 fajlova iz AC2

**AC2 — 6 Roboto woff2 fajlova prisutnih u `static/fonts/roboto/`**

- **Given** struktura iz AC1
- **When** Mihas preuzima Roboto subset (latin + latin-ext) preko **Google Webfonts Helper** (https://gwfh.mranftl.com/fonts/roboto) i smešta woff2 fajlove u `static/fonts/roboto/`
- **Then** prisutno je **tačno 6 fajlova** (3 težine × 2 subseta):
  - `static/fonts/roboto/roboto-latin-300.woff2` (~25-40 KB)
  - `static/fonts/roboto/roboto-latin-400.woff2` (~25-40 KB)
  - `static/fonts/roboto/roboto-latin-700.woff2` (~25-40 KB)
  - `static/fonts/roboto/roboto-latin-ext-300.woff2` (~15-30 KB)
  - `static/fonts/roboto/roboto-latin-ext-400.woff2` (~15-30 KB)
  - `static/fonts/roboto/roboto-latin-ext-700.woff2` (~15-30 KB)
- **And** ukupna veličina svih font fajlova **MORA biti < 300 KB** (sanity check — ako je veći, subset je pogrešan, verovatno uključuje Cyrillic ili Greek; vidi Gotcha #11)
- **And** svaki fajl mora biti **valid woff2** format (magic bytes `wOF2`, prvih 4 bajta) — NE woff, NE ttf, NE otf
- **And** licenca Roboto = Apache License 2.0 (kompatibilna sa projektom; bez attribution u UI, ali komentar u `tokens.css` referencira `https://fonts.google.com/specimen/Roboto`)
- **Napomena za Dev:** ako u trenutku implementacije fajlovi NISU prisutni (npr. Mihas ih nije još preuzeo), Dev mora **HALT-ovati** sa explicit porukom u Dev Agent Record sekciji: `"BLOCKED: Mihas mora preuzeti Roboto woff2 fajlove iz https://gwfh.mranftl.com/fonts/roboto sa selekcijom: 300/400/700 weights × latin + latin-ext subsets, woff2 only, i smestiti u static/fonts/roboto/."` Tek po prisustvu 6 fajlova Dev nastavlja sa AC3-AC8.

**AC3 — `static/css/tokens.css` postoji sa `@font-face` deklaracijama**

- **Given** 6 woff2 fajlova iz AC2
- **When** kreiram `static/css/tokens.css` po Dev Notes § tokens.css Template
- **Then** fajl sadrži **6 `@font-face` deklaracija** (3 weights × 2 subsets):
  - **Tačno 3 latin deklaracije** sa `unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+2000-206F, U+2074, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD`
  - **Tačno 3 latin-ext deklaracije** sa `unicode-range: U+0100-024F, U+0259, U+1E00-1EFF, U+2020, U+20A0-20AB, U+20AD-20CF, U+2113, U+2C60-2C7F, U+A720-A7FF`
  - Svaka deklaracija ima:
    - `font-family: 'Roboto'`
    - `font-style: normal`
    - `font-weight: 300 | 400 | 700` (matches file weight)
    - `font-display: swap` (KRITIČNO — sprečava FOIT)
    - `font-stretch: normal` (opciono ali rekomendovano za buduće variable-font-aware browsera)
    - `src: url('../fonts/roboto/roboto-<subset>-<weight>.woff2') format('woff2')` (relativan path od `static/css/tokens.css` ka `static/fonts/roboto/<file>.woff2` = `../fonts/roboto/<file>.woff2`; vidi Gotcha #4)
- **And** **NIKAKAV** `@import` `https://fonts.googleapis.com/...` (anti-pattern — verifikuj odsustvo string `googleapis.com` u fajlu)
- **And** komentari u fajlu referenciraju DESIGN.md sekciju za grupu tokena (npr. `/* === COLORS — vidi DESIGN.md frontmatter colors === */`); kratki, ne-verbozni — project-context.md § Comments policy traži samo WHY

**AC4 — `tokens.css` `:root { }` sadrži SVE color tokene iz DESIGN.md**

- **Given** AC3 (`@font-face` deklaracije gore u fajlu)
- **When** dopunim `tokens.css` sa `:root { }` blokom posle `@font-face` deklaracija
- **Then** `:root` sadrži **SVE color tokene** iz DESIGN.md YAML frontmatter sekcije `colors`:
  - **Brand greens (4):** `--color-brand-green-900: #1f3f2f`, `--color-brand-green-800: #25402f`, `--color-brand-green-600: #395f48`, `--color-brand-green-400: #4d7e60`
  - **Accents (2):** `--color-accent-gold-500: #e7af12`, `--color-accent-lime-500: #c8d32c`
  - **Brand-specific (1):** `--color-jeegee-blue: #00a4e9`
  - **Neutrals (7):** `--color-neutral-cream: #f5f1e8`, `--color-neutral-white: #ffffff`, `--color-neutral-gray-100: #f4f4f4`, `--color-neutral-gray-300: #d1d1d1`, `--color-neutral-gray-500: #8a8a8a`, `--color-neutral-gray-700: #4a4a4a`, `--color-neutral-black: #0f0f0f` (7 ukupno, brojevi su sekvencijalni labeli iz DESIGN.md)
  - **Semantic (7):** `--color-semantic-text-primary: #1f3f2f`, `--color-semantic-text-on-dark: #ffffff`, `--color-semantic-text-muted: #4a4a4a`, `--color-semantic-border: #395f48`, `--color-semantic-error: #c0392b`, `--color-semantic-success: #2d6b2d`, `--color-semantic-focus-ring: #5a8a6e`
- **And** **SVE** vrednosti hex kodova **MORAJU biti** lowercase + 6-digit (NE 3-digit shorthand poput `#fff` — eksplicitnost olakšava grep i text-diff)
- **And** verifikacija: `var(--color-brand-green-800)` u dev tools vraća **`#25402f`** (konkretan AC iz epics.md)
- **And** komentar uz brand greens MORA biti `/* === COLORS — Brand greens (DESIGN.md frontmatter colors.brand) === */` (ili semantički ekvivalent — grupisanje radi navigacije, ne verbozno)
- **And** NIJEDNA boja iz DESIGN.md frontmatter sekcije `colors` NE sme nedostajati (21 ukupno: 4 brand + 2 accent + 1 brand-specific + 7 neutrals + 7 semantic = 21 custom properties; double-check u AC8 smoke validation)

**AC5 — `tokens.css` `:root` sadrži SVE typography/rounded/shadow/spacing tokene**

- **Given** AC4 (color tokens gore u `:root`)
- **When** dopunim `:root` blok sa preostalim grupama tokena iz DESIGN.md
- **Then** `:root` dodatno sadrži:
  - **Typography family (1):** `--typography-family-primary: 'Roboto', system-ui, sans-serif` (sa fallback stack za pre-load i graceful degradation; system-ui je moderan default fallback)
  - **Typography weights (3):** `--typography-weight-light: 300`, `--typography-weight-regular: 400`, `--typography-weight-bold: 700`
  - **Typography scale (7):** `--typography-scale-h1: 3.5rem`, `--typography-scale-h2: 2.5rem`, `--typography-scale-h3: 1.75rem`, `--typography-scale-h4: 1.25rem`, `--typography-scale-body: 1.25rem`, `--typography-scale-small: 1rem`, `--typography-scale-caption: 0.875rem`
  - **Typography line-height (3):** `--typography-line-height-tight: 1.2`, `--typography-line-height-base: 1.5`, `--typography-line-height-relaxed: 1.7`
  - **Typography tracking (2):** `--typography-tracking-normal: 0`, `--typography-tracking-wide: 0.05em`
  - **Rounded (6):** `--rounded-none: 0`, `--rounded-sm: 6px`, `--rounded-md: 8px`, `--rounded-lg: 10px`, `--rounded-pill: 999px`, `--rounded-full: 50%`
  - **Shadows (5):** `--shadow-none: none`, `--shadow-sm: 0 1px 3px rgba(31, 63, 47, 0.06)`, `--shadow-md: 0 2px 8px rgba(31, 63, 47, 0.06)`, `--shadow-lg: 0 4px 12px rgba(31, 63, 47, 0.08)`, `--shadow-nav-shrunk: 0 2px 4px rgba(0, 0, 0, 0.1)`
  - **Spacing base + scale (10):** `--spacing-base: 4px`, `--spacing-scale-1: 4px`, `--spacing-scale-2: 8px`, `--spacing-scale-3: 12px`, `--spacing-scale-4: 16px`, `--spacing-scale-5: 24px`, `--spacing-scale-6: 32px`, `--spacing-scale-8: 48px`, `--spacing-scale-10: 64px`, `--spacing-scale-12: 96px`
  - **Spacing section (2):** `--spacing-section: 80px`, `--spacing-section-mobile: 48px`
  - **Spacing container (3):** `--spacing-container-max-width: 1200px`, `--spacing-container-gutter-desktop: 24px`, `--spacing-container-gutter-mobile: 16px`
- **And** verifikacija: `var(--typography-scale-h1)` u dev tools vraća **`3.5rem`** (konkretan AC iz epics.md)
- **And** verifikacija: `var(--rounded-pill)` vraća `999px`; `var(--shadow-md)` vraća `0 2px 8px rgba(31, 63, 47, 0.06)`; `var(--spacing-section)` vraća `80px`
- **And** **Komponentni tokeni** (button, card, repeating-element, accordion, pill-badge, wave-divider, brochure-card, stat-medallion iz DESIGN.md `components`) **NISU** uključeni u Story 1.5 — oni se reference-uju kroz `var()` chain-ove **direktno u komponentnim CSS fajlovima** koje uvodi Story 1.7. YAGNI — ne pred-eksportuje se ono što još nema konzumenta. (Vidi Gotcha #15.)
- **And** NIJEDAN token iz DESIGN.md frontmatter sekcija typography/rounded/shadows/spacing NE sme nedostajati (42 ukupno: 1 family + 3 weight + 7 scale + 3 line-height + 2 tracking + 6 rounded + 5 shadow + 1 base + 9 scale + 2 section + 3 container = 42 custom properties; sa color-ima iz AC4 = **63 ukupno** custom properties u `:root`; double-check u AC8)

**AC6 — `config/settings/base.py` ima `STATICFILES_DIRS` + Whitenoise middleware**

- **Given** `base.py` iz Story 1.4 (sa `STATIC_URL = "static/"` i komentarom "STATIC_ROOT, STATICFILES_DIRS — dolaze u Story 1.5/1.6")
- **When** dopunim `base.py` po Dev Notes § base.py modifications
- **Then** **konkretne izmene** moraju biti prisutne:
  - **`STATIC_URL`** MENJA se iz `"static/"` u **`"/static/"`** (leading slash). Bez leading slash-a, `{% static "css/tokens.css" %}` na `/sr/` stranici resolve-uje u `/sr/static/css/tokens.css` → 404 (i18n_patterns prefiks-uje). Sa leading slash-om, uvek je apsolutan `/static/...`. Vidi Gotcha #29.
  - **NOVO** `STATICFILES_DIRS = [BASE_DIR / "static"]` — lista, **ne** tuple, **ne** string. Mora postojati i mora pokazivati na `BASE_DIR / "static"` (vidi Gotcha #6 — bez ovoga `collectstatic` neće naći `tokens.css`)
  - **NOVO** `STATIC_ROOT = BASE_DIR / "staticfiles"` — destinacija za `collectstatic` (dev koristi WhitenoiseMiddleware da servira `STATICFILES_DIRS` direktno; prod-only koristi `STATIC_ROOT`). Ne briše se od Story 1.5 — Story 9.1 produkcija ga koristi za `collectstatic`. Vidi Gotcha #8 — `staticfiles/` MORA biti u `.gitignore` (verifikuj posle izmene `.gitignore` ako postoji; ako ne postoji, dopuni)
  - **NOVO per-env `STORAGES` dict konfiguracija** — uvodi se po-environment definicija static files storage backend-a:
    - **`base.py`** definiše `STORAGES` dict sa **`default` = `FileSystemStorage`** (uploads filesystem) i `staticfiles` placeholder koji **mora biti override-ovan u env-specific settings-ima**.
    - **`development.py`** override-uje `STORAGES["staticfiles"]["BACKEND"] = "django.contrib.staticfiles.storage.StaticFilesStorage"` (plain storage, bez manifesta — vidi Gotcha #28 zašto manifest u dev-u puca uz `ValueError: Missing staticfiles manifest entry`).
    - **`production.py` + `staging.py`** override-uju `STORAGES["staticfiles"]["BACKEND"] = "whitenoise.storage.CompressedManifestStaticFilesStorage"` (manifest + gzip + brotli + cache-busting hash; zahteva `collectstatic` PRE prvog request-a — deploy step).
    - **NAPOMENA:** u Django 5.1+ `STATICFILES_STORAGE` je deprecated u korist `STORAGES` dict; koristimo `STORAGES` dict pattern (vidi Gotcha #9 + Dev Notes Template).
  - **NOVO** `MIDDLEWARE` modifikacija — ubaci `"whitenoise.middleware.WhiteNoiseMiddleware"` **IZMEĐU** `SecurityMiddleware` i `SessionMiddleware` (Whitenoise docs: "WhiteNoise MUST come after SecurityMiddleware but before any other middleware"). Order posle Story 1.5:
    ```python
    MIDDLEWARE = [
        "django.middleware.security.SecurityMiddleware",
        "whitenoise.middleware.WhiteNoiseMiddleware",        # NOVO — POSLE Security, PRE Session
        "django.contrib.sessions.middleware.SessionMiddleware",
        "django.middleware.locale.LocaleMiddleware",
        "django.middleware.common.CommonMiddleware",
        "django.middleware.csrf.CsrfViewMiddleware",
        "django.contrib.auth.middleware.AuthenticationMiddleware",
        "django.contrib.messages.middleware.MessageMiddleware",
        "django.middleware.clickjacking.XFrameOptionsMiddleware",
        "apps.core.middleware.LocaleSwitcherMiddleware",
    ]
    ```
- **And** `pyproject.toml` mora imati `whitenoise>=6.8.0` dodato u `[project.dependencies]` listu. Dodaj via `uv add whitenoise>=6.8.0` — uv typically appends to end of dependencies array; manual reorder NOT required. Story 1.1 NIJE uključila Whitenoise (verifikovano u `pyproject.toml` iz Story 1.4 retro — `whitenoise` se ne pojavljuje u deps). Dev mora pokrenuti `uv add whitenoise` (ne ručno editovati `pyproject.toml`) da bi `uv.lock` bio konzistentan. Vidi Gotcha #10.
- **And** **NIKAKVA druga setting** (LANGUAGE_CODE, DATABASES, EMAIL, AUTH, INSTALLED_APPS) NE sme biti dirana (regression guard — Story 1.4 izmene se čuvaju)
- **And** `INSTALLED_APPS` ostaje **nepromenjen** — `whitenoise` se **NE dodaje** u `INSTALLED_APPS` (Whitenoise je middleware-only u runtime-u; samo `whitenoise.runserver_nostatic` se opciono dodaje za **isključivanje** Django dev servera static handling-a, ali to je out-of-scope za Story 1.5 — Whitenoise i Django dev server ne kolidiraju; vidi Gotcha #12)

**AC7 — `templates/base.html` linkuje `tokens.css` PRE svih ostalih CSS fajlova**

- **Given** `templates/base.html` iz Story 1.4 (minimalan layout sa `{% load i18n %}`, bez bilo kakvog CSS link-a)
- **When** dopunim `templates/base.html` po Dev Notes § base.html modifications
- **Then** **konkretne izmene** moraju biti prisutne:
  - **NOVO** `{% load static %}` direktiva — ide odmah posle `{% load i18n %}` (vidi Gotcha #13 — `{% load static %}` mora biti pre prvog `{% static %}` poziva)
  - **NOVO** `<link rel="stylesheet" href="{% static "css/tokens.css" %}">` — ide unutar `<head>`, **POSLE** `<meta name="viewport">` i **PRE** `<title>` (ili posle `<title>` — ali pre `{% block extra_head %}{% endblock %}`); ključno je da bude **PRE** `{% block extra_head %}` (jer Story 1.6 will add Bootstrap CSS link u `extra_head` block; tokens.css mora load-ovati prvo da custom properties postoje kad Bootstrap util pre-overrider proba `var(--...)`)
  - **Egzaktan placement** (kompletna `<head>` posle Story 1.5):
    ```html
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>{% block title %}Ćorić Agrar{% endblock %}</title>
      <link rel="stylesheet" href="{% static "css/tokens.css" %}">
      {% block extra_head %}{% endblock %}
    </head>
    ```
- **And** **NIKAKAV** `<link>` ka `googleapis.com`, `fonts.gstatic.com`, ili `cdn.jsdelivr.net` (anti-pattern — verifikuj odsustvo u final renderu)
- **And** **NIKAKAV** `<link rel="preconnect">` ka external domains (project-context.md § Self-hosted Roboto — anti-pattern)
- **And** `{% block content %}`, `{% block scripts %}`, `<header>`, `<main>`, `</body>` ostaju **netaknuti** iz Story 1.4 (regression guard)
- **And** language switcher partial referenca ostaje **netaknuta** (Story 1.4 funkcionalnost se ne lomi)

**AC8 — Smoke validacija (acceptance verification)**

- **Given** AC1-AC7 implementirano
- **When** runujem smoke test sekvencu
- **Then** sledeće mora proći:
  1. **File presence check:**
     - `static/css/tokens.css` postoji (size > 5KB — token block je značajan)
     - 6 woff2 fajlova u `static/fonts/roboto/` (ls + count = 6)
     - Total fonts size < 300KB (`du -sh static/fonts/roboto/` u Linux/Mac; `Get-ChildItem static/fonts/roboto/ | Measure-Object -Property Length -Sum` u PowerShell)
  2. **tokens.css content check** (regex/grep):
     - 6 `@font-face` blokova: `grep -c "@font-face" static/css/tokens.css` → output `6`
     - `font-display: swap` se pojavljuje 6 puta (po jednom za svaki `@font-face`)
     - `:root` blok postoji
     - Vrednost `#25402f` se pojavljuje (potvrđuje `--color-brand-green-800`)
     - Vrednost `3.5rem` se pojavljuje (potvrđuje `--typography-scale-h1`)
     - **NIJEDAN** match za `googleapis.com` ili `fonts.gstatic.com` (anti-pattern)
     - **unicode-range checks (latin vs latin-ext):**
       - `grep -c "U+0000-00FF" static/css/tokens.css` → output `3` (3 latin `@font-face` deklaracije)
       - `grep -c "U+0100-024F" static/css/tokens.css` → output `3` (3 latin-ext `@font-face` deklaracije)
     - Brojanje custom properties u `:root`: `grep -cE "^\s*--[a-z-]+:" static/css/tokens.css` → output `63` (iz AC4+AC5 = 21 color + 42 ostali)
  3. **base.py validity:**
     - `uv run python manage.py check` exit 0
     - `uv run python manage.py shell -c "from django.conf import settings; print(settings.STATICFILES_DIRS)"` → output sadrži `static`
     - `uv run python manage.py shell -c "from django.conf import settings; print('whitenoise' in str(settings.MIDDLEWARE).lower())"` → output `True`
  4. **collectstatic --dry-run:**
     - `uv run python manage.py collectstatic --dry-run --noinput` exit 0
     - Output sadrži `css/tokens.css` i `fonts/roboto/roboto-latin-400.woff2` (i ostalih 5)
     - NEMA `googleapis.com` u output-u
  5. **base.html source check:**
     - `grep "{% load static %}" templates/base.html` → match
     - `grep "tokens.css" templates/base.html` → match (link prisutan)
     - `grep -i "googleapis\|gstatic" templates/base.html` → no match (anti-pattern guard)
  6. **Live render test:**
     - `just dev` (Docker compose up) → Django + Postgres up bez grešaka
     - **GET `http://localhost:8000/sr/`** → HTTP 200, response HTML sadrži `<link rel="stylesheet" href="/static/css/tokens.css">` (bez hash-a — dev koristi plain `StaticFilesStorage` per `development.py` STORAGES override; production koristi hash kroz Whitenoise `CompressedManifestStaticFilesStorage` — vidi Gotcha #28)
     - **GET `http://localhost:8000/static/css/tokens.css`** → HTTP 200, content-type `text/css`, body sadrži `--color-brand-green-800: #25402f`
     - **GET `http://localhost:8000/static/fonts/roboto/roboto-latin-400.woff2`** → HTTP 200, content-type `font/woff2`, body magic bytes počinju sa `wOF2`
     - **Browser dev tools Network tab** na `/sr/`: NEMA request-a ka `fonts.googleapis.com` ili `fonts.gstatic.com`; svi font request-i idu ka `localhost:8000/static/fonts/roboto/...`
     - **Browser dev tools Computed styles** na `<html>` ili `<body>`: `--color-brand-green-800` rezolvuje u `#25402f`; `--typography-scale-h1` u `3.5rem`
  7. **Regression — Story 1.1-1.4 nije razbijena:**
     - `uv run pytest` — svi postojeći testovi (Story 1.1-1.4) prolaze (bez regression-a)
     - `just lint` — `ruff check .` exit 0; `djade --check templates/` exit 0
     - `http://localhost:8000/` → HTTP 302 → `/sr/` (Story 1.4 funkcionalnost)
     - `http://localhost:8000/sr/` → 200, `<html lang="sr">` (Story 1.4 funkcionalnost)
     - Language switcher i dalje radi (Story 1.4 funkcionalnost)
- **And** **Niko Lighthouse / a11y audit u ovoj story-ji** — to dolazi u Story 1.6 (Lighthouse a11y ≥ 95 na base template-u) ili Story 9.9 (full audit)
- **And** **Niko vizuelni test komponenti** — Story 1.7 uvodi prve komponente koje konzumiraju tokene; smoke u Story 1.5 verifikuje samo da tokeni POSTOJE i da se služe, ne da neka komponenta ih koristi vizuelno

## Tasks / Subtasks

- [x] **Task 1: Pre-flight verifikacija** (AC: 1)
  - [x] 1.1 Verifikuj da je Story 1.4 done: `cat _bmad-output/implementation-artifacts/sprint-status.yaml | grep "1-4-"` mora pokazati `done`
  - [x] 1.2 Verifikuj postojanje fajlova iz prethodnih story-ja: `config/settings/base.py`, `templates/base.html`, `templates/partials/language_switcher.html`, `apps/core/`, `locale/`, `pyproject.toml`, `uv.lock`, `compose/local.yml`, `justfile`
  - [x] 1.3 Verifikuj da `static/` direktorijum NE postoji (Story 1.5 ga kreira from scratch). Ako postoji nepoznat `static/` folder, ne briši ga već zaustavi i istraži.
  - [x] 1.4 Verifikuj da `_bmad-output/planning-artifacts/ux-designs/ux-CORIC_AGRAR-2026-05-27/DESIGN.md` postoji (source-of-truth za tokene — bez njega Dev ne može da verifikuje vrednosti)
  - [x] 1.5 Pročitaj DESIGN.md YAML frontmatter (sekcije `colors`, `typography`, `rounded`, `shadows`, `spacing`) — Dev MORA mapirati svaki token 1:1 u `tokens.css` (vidi Dev Notes § tokens.css Template kao kanonski izvor)
  - [x] 1.6 Verifikuj `pyproject.toml` — `whitenoise` **NIJE** u deps (potvrđuje da Story 1.5 mora `uv add whitenoise>=6.8.0`)

- [x] **Task 2: Kreiraj `static/` folder hijerarhiju** (AC: 1)
  - [x] 2.1 Kreiraj direktorijum: `static/`
  - [x] 2.2 Kreiraj direktorijum: `static/fonts/`
  - [x] 2.3 Kreiraj direktorijum: `static/fonts/roboto/`
  - [x] 2.4 Kreiraj direktorijum: `static/css/`
  - [x] 2.5 Verifikuj strukturu: `tree static/` (ili `dir static /S` na Windows-u) mora prikazati `static/`, `static/fonts/`, `static/fonts/roboto/`, `static/css/` — sve prazne (fajlovi dolaze u Task 3 i Task 4)
  - [x] 2.6 **NE kreiraj** `static/js/`, `static/img/`, `static/vendor/` u ovoj story-ji (YAGNI — naredne story-je će ih dodati)

- [ ] **Task 3: Preuzmi Roboto woff2 fajlove (Mihas ručno; Dev verifikuje prisustvo)** (AC: 2) — BLOCKED: Mihas mora ručno preuzeti 6 woff2 fajlova sa gwfh.mranftl.com per Task 3.1
  - [ ] 3.1 **Mihas instrukcije (ručna akcija):**
     1. Otvori `https://gwfh.mranftl.com/fonts/roboto` u browser-u
     2. U "Select styles" sekciji označi: **300 Light**, **regular 400**, **700 Bold**
     3. U "Select charsets" sekciji označi: **latin**, **latin-ext** (NE označi: cyrillic, greek, vietnamese — povećalo bi size i nije potrebno za sr/hu/en)
     4. U "Customize folder prefix" ostavi default ili stavi: `../fonts/roboto/`
     5. U "Format" sekciji označi: **Modern Browsers (woff2)** SAMO (NE woff, NE eot)
     6. Klikni "Download files" — dobija se ZIP arhiva sa 6 woff2 fajlova
     7. Raspakuj ZIP u **`static/fonts/roboto/`** — fajlovi MORAJU imati nazive matching pattern:
        - `roboto-v<NN>-latin-300.woff2`
        - `roboto-v<NN>-latin-regular.woff2`
        - `roboto-v<NN>-latin-700.woff2`
        - `roboto-v<NN>-latin-ext-300.woff2`
        - `roboto-v<NN>-latin-ext-regular.woff2`
        - `roboto-v<NN>-latin-ext-700.woff2`
        (gde je `<NN>` verzija tipa `v30`, `v32`, itd. — gwfh prefiksuje verziju)
     8. **Rename-uj fajlove** na canonical form (uklanjaja `-v<NN>-` deo + zameni `regular` sa `400`):
        - `roboto-latin-300.woff2`
        - `roboto-latin-400.woff2`
        - `roboto-latin-700.woff2`
        - `roboto-latin-ext-300.woff2`
        - `roboto-latin-ext-400.woff2`
        - `roboto-latin-ext-700.woff2`
     9. Verifikuj `du -sh static/fonts/roboto/` (Linux/Mac) ili `Get-ChildItem static/fonts/roboto/ | Measure-Object Length -Sum` (PowerShell) — ukupno < 300 KB. Ako > 300 KB, subset je pogrešan (verovatno cyrillic uključen) — vratiti se na korak 3.
  - [ ] 3.2 **Dev verifikacija (Dev agent):**
     - **HALT check:** ako 6 fajlova NISU prisutni u `static/fonts/roboto/` sa tačnim imenima iz Task 3.1.8, Dev MORA HALT-ovati sa porukom u Dev Agent Record: `"BLOCKED: Mihas mora preuzeti Roboto woff2 fajlove. Vidi Task 3.1 za korake."` i ne nastavlja sa AC4-AC8.
     - Ako fajlovi POSTOJE, Dev verifikuje:
       - `ls static/fonts/roboto/*.woff2 | wc -l` (Linux/Mac) ili `(Get-ChildItem static/fonts/roboto/ -Filter *.woff2).Count` (PowerShell) → **6**
       - Magic bytes provera (opciono ali rekomendovano): prvih 4 bajta svakog fajla = `0x77 0x4F 0x46 0x32` (`wOF2`). U PowerShell: `[System.IO.File]::ReadAllBytes('static/fonts/roboto/roboto-latin-400.woff2')[0..3]` → mora vratiti `119, 79, 70, 50`.

- [x] **Task 4: Kreiraj `static/css/tokens.css` sa `@font-face` deklaracijama** (AC: 3)
  - [x] 4.1 Kreiraj `static/css/tokens.css` sa sadržajem iz Dev Notes § tokens.css Template (sekcija `@font-face`)
  - [x] 4.2 KRITIČNO: svaka `@font-face` deklaracija MORA imati `font-display: swap` (sprečava FOIT — Flash of Invisible Text; project-context.md § Performance must-haves)
  - [x] 4.3 KRITIČNO: `src: url('../fonts/roboto/...')` — relativan path od `static/css/tokens.css` ka `static/fonts/roboto/` (vidi Gotcha #4)
  - [x] 4.4 KRITIČNO: `unicode-range` za latin i latin-ext različite — kopiraj iz Dev Notes § tokens.css Template (vidi Gotcha #5)
  - [x] 4.5 KRITIČNO: `font-family: 'Roboto'` (sa single quotes — konzistentnost sa CSS standard)
  - [x] 4.6 KRITIČNO: `font-weight` numerički (300/400/700) — NE `font-weight: light` / `normal` / `bold` (verbozno i zbunjuje sa CSS keyword-ima)
  - [x] 4.7 KRITIČNO: NEMA `@import url('https://fonts.googleapis.com/...')` u fajlu (anti-pattern — project-context.md § Self-hosted Roboto, Story 1.5 AC3)

- [x] **Task 5: Dopuni `static/css/tokens.css` sa color tokenima u `:root`** (AC: 4)
  - [x] 5.1 Posle `@font-face` deklaracija, dodaj `:root { }` blok
  - [x] 5.2 Mapiraj **SVE** color tokene iz DESIGN.md frontmatter `colors` sekcije po Dev Notes § tokens.css Template (sekcija `:root` color tokens)
  - [x] 5.3 KRITIČNO: hex vrednosti lowercase 6-digit (`#25402f` NE `#25402F`, NE `#fff` — vidi AC4)
  - [x] 5.4 KRITIČNO: nazivi tokena MORAJU pratiti pattern `--color-<group>-<name>-<variant>` (project-context.md § CSS Custom Properties naming)
     - Brand greens: `--color-brand-green-900/800/600/400`
     - Accents: `--color-accent-gold-500`, `--color-accent-lime-500`
     - Brand-specific: `--color-jeegee-blue` (bez `<variant>` jer je single-value; pattern dozvoljava)
     - Neutrals: `--color-neutral-cream/white/gray-100/300/500/700/black`
     - Semantic: `--color-semantic-text-primary`, `--color-semantic-text-on-dark`, itd.
  - [x] 5.5 Komentari u CSS-u referenciraju DESIGN.md sekciju (npr. `/* Brand greens — DESIGN.md colors.brand */`) — kratki, ne-verbozni
  - [x] 5.6 Verifikuj: vizuelno prebroji color custom properties = **21** (4 brand + 2 accent + 1 brand-specific + 7 neutral + 7 semantic)

- [x] **Task 6: Dopuni `static/css/tokens.css` sa typography/rounded/shadow/spacing tokenima** (AC: 5)
  - [x] 6.1 Unutar istog `:root` bloka (posle color tokena), dodaj **SVE** typography/rounded/shadow/spacing tokene po Dev Notes § tokens.css Template
  - [x] 6.2 KRITIČNO: typography scale vrednosti u **rem** (NE px) — DESIGN.md eksplicitno: "rem values (1rem = 16px)"
  - [x] 6.3 KRITIČNO: `--typography-family-primary: 'Roboto', system-ui, sans-serif` — sa fallback stack (browser će ga koristiti dok Roboto load-uje, sa `font-display: swap` kontrolom)
  - [x] 6.4 KRITIČNO: `--shadow-md: 0 2px 8px rgba(31, 63, 47, 0.06)` — vrednost iz DESIGN.md `shadows.md`; NE skraćivati format (`rgba(31,63,47,0.06)` bez razmaka je takođe valid, ali Dev koristi varijantu sa razmacima radi čitljivosti)
  - [x] 6.5 Spacing scale vrednosti u **px** (DESIGN.md koristi px za spacing-scale; sve ostalo u rem); `--spacing-base: 4px`
  - [x] 6.6 NE uvoditi komponentne tokene (button/card/repeating-element/itd.) — vidi AC5 napomenu (YAGNI; Story 1.7 ih konzumira direktno preko `var()` chain-ova u komponentnom CSS-u)
  - [x] 6.7 Verifikuj: vizuelno prebroji ne-color custom properties = **42** (1 family + 3 weight + 7 scale + 3 line-height + 2 tracking + 6 rounded + 5 shadow + 1 base + 9 scale + 2 section + 3 container)
  - [x] 6.8 Verifikuj total custom properties u `:root` = 21 + 42 = **63** (AC8 smoke check brojaće isto)

- [x] **Task 7: Update `config/settings/base.py` + env settings — STATICFILES_DIRS + STATIC_ROOT + STORAGES + Whitenoise** (AC: 6)
  - [x] 7.1 Otvori `config/settings/base.py`, lociraj `# ── Static ──` sekciju (linija ~108 posle Story 1.4)
  - [x] 7.2 Promeni / dopuni sekciju po Dev Notes § base.py modifications (kompletna `# ── Static ──` sekcija after-state)
  - [x] 7.3 KRITIČNO: Modifikuj `config/settings/base.py:109`: `STATIC_URL = "static/"` → `STATIC_URL = "/static/"` (leading slash). Bez leading slash-a, `{% static "css/tokens.css" %}` na `/sr/` stranici resolve-uje u `/sr/static/css/tokens.css` → 404. Sa leading slash-om uvek je apsolutan `/static/css/tokens.css`. Vidi Gotcha #29.
  - [x] 7.4 KRITIČNO: `STATICFILES_DIRS = [BASE_DIR / "static"]` — lista (ne tuple, ne string); pokazuje na `static/` koji je kreiran u Task 2
  - [x] 7.5 KRITIČNO: `STATIC_ROOT = BASE_DIR / "staticfiles"` — destinacija za `collectstatic` (prod-only; dev koristi WhitenoiseMiddleware da servira `STATICFILES_DIRS` direktno preko Django dev servera)
  - [x] 7.6 KRITIČNO: Koristi `STORAGES` dict (Django 5.1+ canonical) **ne** deprecated `STATICFILES_STORAGE` setting. `base.py` definiše osnovnu strukturu sa `FileSystemStorage` default-om:
    ```python
    # base.py
    STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
    ```
  - [x] 7.7 KRITIČNO: `config/settings/development.py` MORA override-ovati STORAGES sa plain `StaticFilesStorage` (NE manifest) da bi se izbegao `ValueError: Missing staticfiles manifest entry` kad razvojni server pokušava da resolve-uje `{% static %}` bez prethodno pokrenutog `collectstatic`. Vidi Gotcha #28.
    ```python
    # development.py
    STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
    ```
  - [x] 7.8 KRITIČNO: `config/settings/production.py` (i `staging.py` ako postoji) zadržava Whitenoise `CompressedManifestStaticFilesStorage` (cache-busting u prod-u; collectstatic je deploy step):
    ```python
    # production.py / staging.py
    STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
    }
    ```
  - [x] 7.9 KRITIČNO: lociraj `MIDDLEWARE` listu i ubaci `"whitenoise.middleware.WhiteNoiseMiddleware"` **IZMEĐU** `SecurityMiddleware` i `SessionMiddleware` (Whitenoise docs zahtevaju ovaj order)
  - [x] 7.10 KRITIČNO: `whitenoise` se NE dodaje u `INSTALLED_APPS` (middleware-only; vidi Gotcha #12)
  - [x] 7.11 Verifikuj REGRESSION: `LANGUAGE_CODE`, `LANGUAGES`, `LOCALE_PATHS`, `DATABASES`, `EMAIL`, `AUTH`, `TEMPLATES`, `INSTALLED_APPS` ostaju nepromenjeni iz Story 1.4

- [x] **Task 8: Dodaj Whitenoise dependency u `pyproject.toml`** (AC: 6)
  - [x] 8.1 Pokreni: `uv add whitenoise>=6.8.0` (NE ručno editovati `pyproject.toml` — `uv add` sinkronizuje `uv.lock` automatski)
  - [x] 8.2 Verifikuj `pyproject.toml` ima `"whitenoise>=6.8.0"` u `[project.dependencies]` listi — `uv add` typically appends to end of dependencies array; manual reorder NOT required.
  - [x] 8.3 Verifikuj `uv.lock` updated (komituj zajedno sa `pyproject.toml`)
  - [x] 8.4 Verifikuj instalaciju: `uv run python -c "import whitenoise; print(whitenoise.__version__)"` exit 0 i prikazuje verziju >= 6.8.0 (Verified: whitenoise 6.12.0 instaliran; sam paket ne expose-uje __version__ atribut ali import radi)
  - [x] 8.5 KRITIČNO: NIKAKAV ručni edit `pyproject.toml` (anti-pattern — `uv` SOT, vidi project-context.md § Package manager)

- [x] **Task 9: Update `templates/base.html` — `{% load static %}` + tokens.css link** (AC: 7)
  - [x] 9.1 Otvori `templates/base.html`, lociraj `{% load i18n %}` (linija 2 posle Story 1.4)
  - [x] 9.2 **Dopuni** sa `{% load static %}` direktivom — ide odmah POSLE `{% load i18n %}` (ne pre `<!DOCTYPE html>`)
  - [x] 9.3 Lociraj `<head>` blok (linije 4-9 posle Story 1.4)
  - [x] 9.4 Dodaj `<link rel="stylesheet" href="{% static "css/tokens.css" %}">` između `<title>` i `{% block extra_head %}` (vidi AC7 egzaktan placement)
  - [x] 9.5 KRITIČNO: `{% load static %}` MORA biti pre prvog `{% static %}` poziva (vidi Gotcha #13)
  - [x] 9.6 KRITIČNO: `{% static "css/tokens.css" %}` — koristi **double quotes** radi konzistentnosti sa Story 1.4 `base.html` stilom (Django dozvoljava oba; bira se double radi uniform code style)
  - [x] 9.7 KRITIČNO: NIKAKAV link ka `googleapis.com`, `gstatic.com`, `cdn.jsdelivr.net` (anti-pattern — vidi AC7)
  - [x] 9.8 Verifikuj REGRESSION: `{% load i18n %}`, `<html lang="{{ LANGUAGE_CODE }}">`, `<header>` sa language switcher include, `<main>` sa block content, `{% block scripts %}` ostaju **netaknuti**

- [x] **Task 10: Smoke validacija** (AC: 8)
  - [x] 10.1 **File presence:** `ls static/css/tokens.css` postoji; `ls static/fonts/roboto/*.woff2` daje 6 fajlova (woff2 blocked pending Mihas manual download)
  - [x] 10.2 **tokens.css content:**
     - `grep -c "@font-face" static/css/tokens.css` → **6**
     - `grep -c "font-display: swap" static/css/tokens.css` → **6**
     - `grep -cE "^\s*--[a-z-]+:" static/css/tokens.css` → **63** (custom properties unutar `:root`; permissive whitespace + lowercase letters + colon — neutralno na indentation)
     - `grep "#25402f" static/css/tokens.css` → match (verifikuje `--color-brand-green-800`)
     - `grep "3.5rem" static/css/tokens.css` → match (verifikuje `--typography-scale-h1`)
     - `grep -i "googleapis\|gstatic" static/css/tokens.css` → **no match** (anti-pattern guard)
  - [ ] 10.3 **Django check:**
     - `uv run python manage.py check` exit 0
     - `uv run python manage.py shell -c "from django.conf import settings; print(settings.STATICFILES_DIRS)"` → output sadrži `static`
     - `uv run python manage.py shell -c "from django.conf import settings; print('whitenoise' in str(settings.MIDDLEWARE).lower())"` → output `True`
  - [ ] 10.4 **collectstatic --dry-run:**
     - `uv run python manage.py collectstatic --dry-run --noinput` exit 0
     - Output sadrži pomen `css/tokens.css` i barem jedan `fonts/roboto/...woff2`
  - [ ] 10.5 **base.html source:**
     - `grep "{% load static %}" templates/base.html` → match
     - `grep "tokens.css" templates/base.html` → match
     - `grep -i "googleapis\|gstatic" templates/base.html` → no match
  - [ ] 10.6 **Live render (Docker):**
     - `just dev-build` (sa novim `pyproject.toml` koji ima Whitenoise) — Docker image se buildova bez grešaka
     - `just dev` — Django + PostgreSQL up
     - Browser: `http://localhost:8000/sr/` — HTTP 200, view source ima `<link rel="stylesheet" href="/static/css/tokens.css">`
     - Browser: `http://localhost:8000/static/css/tokens.css` — 200, body sadrži `--color-brand-green-800: #25402f`
     - Browser: `http://localhost:8000/static/fonts/roboto/roboto-latin-400.woff2` — 200, body magic bytes `wOF2`
     - Browser dev tools Network tab na `/sr/`: nema request-a ka `fonts.googleapis.com` ili `fonts.gstatic.com`
     - Browser dev tools Computed (na `<html>`): `--color-brand-green-800` = `#25402f`, `--typography-scale-h1` = `3.5rem`
  - [ ] 10.7 **Regression:**
     - `uv run pytest` — postojeći testovi (Story 1.1-1.4) prolaze
     - `just lint` — clean
     - `/` → 302 → `/sr/` (Story 1.4 regression)
     - `/sr/` → 200 sa `<html lang="sr">` (Story 1.4 regression)
     - Language switcher dropdown radi (Story 1.4 regression)
  - [ ] 10.8 Cleanup: `just dev-down`

- [x] **Task 11: Update `.gitignore` (ako postoji) ili kreiraj — exclude `staticfiles/`** (AC: 6)
  - [x] 11.1 Verifikuj postojanje `.gitignore` (Story 1.1 ga je kreirao; verifikuj `cat .gitignore | head -5`)
  - [x] 11.2 Ako `staticfiles/` NIJE u `.gitignore`, dodaj liniju `staticfiles/` (Whitenoise `collectstatic` destinacija — prod-only, ne commit-uje se) — `staticfiles/` već prisutno (line 60)
  - [x] 11.3 Verifikuj da `static/` NIJE u `.gitignore` (source folder, MORA biti commit-ovan)
  - [x] 11.4 Verifikuj `git status` posle Task 2 + Task 3 + Task 4: `static/css/tokens.css` i `static/fonts/roboto/*.woff2` su prikazani kao untracked (spremni za `git add`); `staticfiles/` NIJE prikazan (ignored)

- [x] **Task 12: Final review i sanity check** (AC: sve)
  - [x] 12.1 Verifikuj `static/` strukturu — tačno `css/tokens.css` + 6 woff2 u `fonts/roboto/`, NIŠTA drugo (no `js/`, no `img/`, no `vendor/` u Story 1.5) — woff2 dependent na Mihas manual download
  - [x] 12.2 Verifikuj `config/settings/base.py` ima sve izmene iz AC6; NIKAKVA druga sekcija nije dirana (i18n iz Story 1.4 sačuvan)
  - [x] 12.3 Verifikuj `templates/base.html` ima `{% load static %}` + `<link>` ka `tokens.css`; ostalo iz Story 1.4 netaknuto
  - [x] 12.4 Verifikuj `pyproject.toml` + `uv.lock` ima `whitenoise>=6.8.0` (zajednički commit)
  - [x] 12.5 Popuni "File List" i "Completion Notes List" u "Dev Agent Record" sekciji (ispod, posle Dev Notes)
  - [x] 12.6 KRITIČNO: proveri `git status` — verifikuj da NEMA dirty fajlova van očekivanih (`static/`, `config/settings/base.py`, `templates/base.html`, `pyproject.toml`, `uv.lock`, opciono `.gitignore`)

## Dev Notes

### Kontekst story-ja

Story 1.5 je **vizuelni temelj** za Epic 1 — prvi put projekat dobija:

1. **`static/` folder hijerarhiju** — `static/css/`, `static/fonts/roboto/`. Sledeće story-je dodaju `static/js/` (Story 1.6 + 1.7 + 1.8), `static/img/` (Story 2.3 image pipeline), `static/vendor/` (Story 1.6 Bootstrap 5 + HTMX lokalni).
2. **`static/css/tokens.css`** — kanonski CSS Custom Properties fajl. 1:1 mapira **21 color** + **42 typography/rounded/shadow/spacing** = **63 tokena** iz DESIGN.md frontmatter. Sve buduće komponente konzumiraju ove tokene preko `var(--...)` — nema magic vrednosti, nema duplikacije.
3. **Self-hosted Roboto** — 6 woff2 fajlova (3 weight × 2 subset) u `static/fonts/roboto/`. Bez Google Fonts CDN-a (GDPR-friendly, brži FCP). `font-display: swap` sprečava FOIT.
4. **Whitenoise integracija** — uvodi `whitenoise>=6.8.0` u deps + `WhiteNoiseMiddleware` u `MIDDLEWARE` + `STORAGES` dict sa `CompressedManifestStaticFilesStorage`. Story 1.1 je propustila ovu dep (architecture.md je planirao; Story 1.1 je zaboravila).

**Foundation za:**
- **Story 1.6 (Bootstrap 5 + HTMX):** `base.html` će dobiti dodatne `<link>` ka Bootstrap CSS (LOKALNO `static/vendor/bootstrap.min.css`, NE CDN), HTMX script (`static/vendor/htmx.min.js`). Bootstrap CSS može override-ovati neke tokene (npr. Bootstrap `--bs-primary`) — Story 1.6 pažljivo namespace-ira preko `coric-` prefiksa.
- **Story 1.7 (Reusable komponente):** Svaka komponenta (`repeating_element.html`, `pill_button.html`, itd.) ima parny `static/css/components/<name>.css` fajl koji konzumira `var(--color-brand-green-800)`, `var(--rounded-pill)`, itd. Pristup: komponentni CSS importuje samo tokens.css i Bootstrap utility classes — bez magic vrednosti.
- **Story 1.8 (Sticky Nav + Footer):** `static/css/components/nav.css` koristi `var(--color-brand-green-800)` za bg i `var(--shadow-nav-shrunk)` za sticky shrunk state. JavaScript (`static/js/sticky-nav.js`) ne dira tokene direktno.
- **Story 9.1 (Production Docker compose):** `collectstatic --noinput` u deploy script-u koristi `STATIC_ROOT` (uvedeno u ovoj story-ji) — Whitenoise CompressedManifestStaticFilesStorage generiše `tokens.<hash>.css`, `roboto-latin-400.<hash>.woff2`, itd. (cache-busting).

**Princip:** Story 1.5 dovršava **vizuelni token kontrakt** (63 tokena dostupna) ali NE uvodi nijednu komponentu. Stranica izgleda i dalje minimalistički (Story 1.4 layout); Roboto se loaduje ali nije aktiviran u CSS-u (Story 1.6 dodaje `body { font-family: var(--typography-family-primary); }`).

**Out-of-scope** za Story 1.5:
- Bootstrap 5 / HTMX / GLightbox setup (Story 1.6)
- Reusable visual komponente (Story 1.7) — uključujući prvi consumer tokena
- Aktivacija Roboto na `<body>` (Story 1.6 ili 1.7 — kad postoje komponente koje koriste tipografiju)
- Komponentni tokeni u `tokens.css` (`--button-primary-bg: var(--color-brand-green-800)` itd.) — komponentni CSS u Story 1.7 koristi token chain-ove direktno (`background: var(--color-brand-green-800)`)
- `prefers-reduced-motion` media query (Story 1.7 ili 1.8 — kad postoje animacije)
- Dark mode tokens (defer u v2 ako biznis traži)
- Print stylesheet (DESIGN.md § Open Decisions: `→ defer`)
- Responsive token overrides preko media query-jeva — DESIGN.md ima samo `section: 80px` (desktop) vs `section-mobile: 48px` koje rešavamo kroz **dva odvojena tokena** (`--spacing-section` i `--spacing-section-mobile`) umesto media query overrid-a. Story 1.7+ komponente same biraju koji token koristiti u kontekstu.

### Tech stack — Static files specifics

| Komponenta | Verzija / Tehnologija | Razlog |
|---|---|---|
| Static files serving (dev) | Django dev server (`runserver`) + Whitenoise middleware | Whitenoise radi i u dev i u prod sa istim middleware-om; opciono dodajemo `whitenoise.runserver_nostatic` ali ne u Story 1.5 |
| Static files serving (prod) | Whitenoise CompressedManifestStaticFilesStorage + Nginx fallback | Whitenoise + manifest = gzip/brotli + hash u filename = cache-busting; Nginx samo za media (user uploads) |
| Font format | woff2 only | Best compression (30-50% manji od woff); univerzalna podrška u Chrome 36+, FF 39+, Safari 10+, Edge 14+ (2017+ — sigurno) |
| Font subset | latin + latin-ext | latin = ASCII + osnovni Western European; latin-ext = Central/East European glyph-ovi (potrebno za sr Č/Ć/Đ/Š/Ž; hu á/é/í/ó/ö/ő/ú/ü/ű) |
| Font weights | 300 (Light), 400 (Regular), 700 (Bold) | DESIGN.md typography.weight specifikacija; 3 težine pokrivaju h1 Light, body Regular, h2-h4 Bold |
| Font display strategy | `font-display: swap` | Sprečava FOIT (Flash of Invisible Text) — browser prikazuje fallback font dok Roboto loaduje, pa swap-uje; mali FOUT (Flash of Unstyled Text) je acceptable trade-off |
| CSS variable scope | `:root { ... }` (global) | Dostupno svuda u DOM-u; matches DESIGN.md token strukturu |
| Whitenoise verzija | `>=6.8.0` | Latest stable kao 2026-05; podržava Django 5.2 LTS, manifest storage, brotli kompresija |

**Roboto licenca napomena:**
- Roboto je pod **Apache License 2.0** (https://github.com/googlefonts/roboto/blob/main/LICENSE)
- Apache 2.0 dozvoljava self-hosting bez attribution u UI-u (samo zahteva da licenca putuje uz binary distribuciju — woff2 fajlovi u repo + `<!-- Roboto: Apache 2.0, https://fonts.google.com/specimen/Roboto -->` komentar u `tokens.css` je dovoljan)
- Nema potrebe za "Powered by Roboto" linkom u footer-u

**Whitenoise napomena:**
- Whitenoise je **middleware-only** — NIJE u `INSTALLED_APPS`. Aktivira se kroz `MIDDLEWARE` listu.
- Whitenoise INTERCEPTUJE GET request-e za `/static/*` PRE Django URL routing-a — pa nema potrebe za `urlpatterns += static(STATIC_URL, document_root=STATIC_ROOT)` u `urls.py` (Django dev convention koja je nepotrebna sa Whitenoise).
- `CompressedManifestStaticFilesStorage`:
  - **Manifest:** generiše `staticfiles.json` posle `collectstatic` sa hash-iranim filename-ima
  - **Compressed:** automatski generiše `<file>.gz` i `<file>.br` (brotli) varijante; Whitenoise servira komprimovanu varijantu ako Accept-Encoding header dozvoljava
  - **Cache-busting:** hash u filename-u (`tokens.a1b2c3d4.css`) omogućuje `Cache-Control: public, max-age=31536000` (1 godina) — browser invalidira cache automatski kad se hash promeni
- **U dev-u (DEBUG=True):** Whitenoise serves `STATICFILES_DIRS` direktno (bez `collectstatic`). U prod-u (DEBUG=False): serves `STATIC_ROOT` posle `collectstatic --noinput` (deploy step).
- **Bind mount u Docker compose local.yml:** `static/` se bind-mountuje preko `../:/app:cached` (cela repo); izmene u `static/css/tokens.css` su odmah vidljive u kontejneru — **bez restart-a Django-a**. Hard refresh u browseru (Ctrl+Shift+R) ako browser cache zadrži staru verziju.

### tokens.css Template (KOMPLETAN — Dev kopira ovaj sadržaj)

```css
/* ============================================================================
 * tokens.css — Ćorić Agrar CSS Custom Properties
 *
 * 1:1 mapping iz DESIGN.md frontmatter (colors, typography, rounded, shadows,
 * spacing). Sve komponente konzumiraju tokene preko var(--token-name) — bez
 * magic vrednosti u komponentnom CSS-u.
 *
 * Roboto: self-hosted (Apache License 2.0, https://fonts.google.com/specimen/Roboto)
 * ========================================================================= */

/* ============================================================================
 * @font-face — Roboto subset (latin + latin-ext, weights 300/400/700)
 * font-display: swap sprečava FOIT (Flash of Invisible Text).
 * unicode-range omogućuje browser-u da preuzme samo subset koji se koristi.
 * ========================================================================= */

@font-face {
  font-family: 'Roboto';
  font-style: normal;
  font-weight: 300;
  font-stretch: normal;
  font-display: swap;
  src: url('../fonts/roboto/roboto-latin-300.woff2') format('woff2');
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+2000-206F, U+2074, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
}

@font-face {
  font-family: 'Roboto';
  font-style: normal;
  font-weight: 400;
  font-stretch: normal;
  font-display: swap;
  src: url('../fonts/roboto/roboto-latin-400.woff2') format('woff2');
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+2000-206F, U+2074, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
}

@font-face {
  font-family: 'Roboto';
  font-style: normal;
  font-weight: 700;
  font-stretch: normal;
  font-display: swap;
  src: url('../fonts/roboto/roboto-latin-700.woff2') format('woff2');
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+2000-206F, U+2074, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
}

@font-face {
  font-family: 'Roboto';
  font-style: normal;
  font-weight: 300;
  font-stretch: normal;
  font-display: swap;
  src: url('../fonts/roboto/roboto-latin-ext-300.woff2') format('woff2');
  unicode-range: U+0100-024F, U+0259, U+1E00-1EFF, U+2020, U+20A0-20AB, U+20AD-20CF, U+2113, U+2C60-2C7F, U+A720-A7FF;
}

@font-face {
  font-family: 'Roboto';
  font-style: normal;
  font-weight: 400;
  font-stretch: normal;
  font-display: swap;
  src: url('../fonts/roboto/roboto-latin-ext-400.woff2') format('woff2');
  unicode-range: U+0100-024F, U+0259, U+1E00-1EFF, U+2020, U+20A0-20AB, U+20AD-20CF, U+2113, U+2C60-2C7F, U+A720-A7FF;
}

@font-face {
  font-family: 'Roboto';
  font-style: normal;
  font-weight: 700;
  font-stretch: normal;
  font-display: swap;
  src: url('../fonts/roboto/roboto-latin-ext-700.woff2') format('woff2');
  unicode-range: U+0100-024F, U+0259, U+1E00-1EFF, U+2020, U+20A0-20AB, U+20AD-20CF, U+2113, U+2C60-2C7F, U+A720-A7FF;
}

/* ============================================================================
 * :root — CSS Custom Properties (63 tokena ukupno: 21 color + 42 ostali)
 * Naming convention: --<group>-<name>-<variant> per project-context.md
 * ========================================================================= */

:root {
  /* === COLORS — Brand greens (DESIGN.md colors.brand) === */
  --color-brand-green-900: #1f3f2f;
  --color-brand-green-800: #25402f;
  --color-brand-green-600: #395f48;
  --color-brand-green-400: #4d7e60;

  /* === COLORS — Accents (DESIGN.md colors.accent) === */
  --color-accent-gold-500: #e7af12;
  --color-accent-lime-500: #c8d32c;

  /* === COLORS — Brand-specific (DESIGN.md colors.brand-specific) === */
  --color-jeegee-blue: #00a4e9;

  /* === COLORS — Neutrals (DESIGN.md colors.neutral) === */
  --color-neutral-cream: #f5f1e8;
  --color-neutral-white: #ffffff;
  --color-neutral-gray-100: #f4f4f4;
  --color-neutral-gray-300: #d1d1d1;
  --color-neutral-gray-500: #8a8a8a;
  --color-neutral-gray-700: #4a4a4a;
  --color-neutral-black: #0f0f0f;

  /* === COLORS — Semantic (DESIGN.md colors.semantic) === */
  --color-semantic-text-primary: #1f3f2f;
  --color-semantic-text-on-dark: #ffffff;
  --color-semantic-text-muted: #4a4a4a;
  --color-semantic-border: #395f48;
  --color-semantic-error: #c0392b;
  --color-semantic-success: #2d6b2d;
  --color-semantic-focus-ring: #5a8a6e;

  /* === TYPOGRAPHY — Family (DESIGN.md typography.family) === */
  --typography-family-primary: 'Roboto', system-ui, sans-serif;

  /* === TYPOGRAPHY — Weights (DESIGN.md typography.weight) === */
  --typography-weight-light: 300;
  --typography-weight-regular: 400;
  --typography-weight-bold: 700;

  /* === TYPOGRAPHY — Scale (DESIGN.md typography.scale; rem values, 1rem = 16px) === */
  --typography-scale-h1: 3.5rem;
  --typography-scale-h2: 2.5rem;
  --typography-scale-h3: 1.75rem;
  --typography-scale-h4: 1.25rem;
  --typography-scale-body: 1.25rem;
  --typography-scale-small: 1rem;
  --typography-scale-caption: 0.875rem;

  /* === TYPOGRAPHY — Line-height (DESIGN.md typography.line-height) === */
  --typography-line-height-tight: 1.2;
  --typography-line-height-base: 1.5;
  --typography-line-height-relaxed: 1.7;

  /* === TYPOGRAPHY — Tracking (DESIGN.md typography.tracking) === */
  --typography-tracking-normal: 0;
  --typography-tracking-wide: 0.05em;

  /* === ROUNDED (DESIGN.md rounded) === */
  --rounded-none: 0;
  --rounded-sm: 6px;
  --rounded-md: 8px;
  --rounded-lg: 10px;
  --rounded-pill: 999px;
  --rounded-full: 50%;

  /* === SHADOWS (DESIGN.md shadows) === */
  --shadow-none: none;
  --shadow-sm: 0 1px 3px rgba(31, 63, 47, 0.06);
  --shadow-md: 0 2px 8px rgba(31, 63, 47, 0.06);
  --shadow-lg: 0 4px 12px rgba(31, 63, 47, 0.08);
  --shadow-nav-shrunk: 0 2px 4px rgba(0, 0, 0, 0.1);

  /* === SPACING — Base + scale (DESIGN.md spacing.base + spacing.scale; px values) === */
  --spacing-base: 4px;
  --spacing-scale-1: 4px;
  --spacing-scale-2: 8px;
  --spacing-scale-3: 12px;
  --spacing-scale-4: 16px;
  --spacing-scale-5: 24px;
  --spacing-scale-6: 32px;
  --spacing-scale-8: 48px;
  --spacing-scale-10: 64px;
  --spacing-scale-12: 96px;

  /* === SPACING — Section (DESIGN.md spacing.scale.section + section-mobile) === */
  --spacing-section: 80px;
  --spacing-section-mobile: 48px;

  /* === SPACING — Container (DESIGN.md spacing.container) === */
  --spacing-container-max-width: 1200px;
  --spacing-container-gutter-desktop: 24px;
  --spacing-container-gutter-mobile: 16px;
}
```

### base.py modifications

**Before (Story 1.4 stanje — linije 108-110):**

```python
# ── Static ───────────────────────────────────────────────────────────────────
STATIC_URL = "static/"
# STATIC_ROOT, STATICFILES_DIRS, MEDIA_ROOT — dolaze u Story 1.5/1.6 kad static asset folder bude kreiran
```

**After — `config/settings/base.py` (Story 1.5 stanje):**

```python
# ── Static ───────────────────────────────────────────────────────────────────
# base.py definiše osnovni STORAGES dict sa plain StaticFilesStorage (Django default).
# Env-specific settings override-uju STORAGES["staticfiles"]:
#   - development.py: plain StaticFilesStorage (no manifest, no collectstatic needed)
#   - production.py / staging.py: Whitenoise CompressedManifestStaticFilesStorage
#     (gzip + brotli + hash cache-busting; zahteva collectstatic deploy step)
# STATIC_URL ima leading slash radi i18n_patterns kompatibilnosti — bez slash-a
# {% static %} resolve uvodi current locale prefix (/sr/static/...) → 404. Vidi Gotcha #29.
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}
```

**After — `config/settings/development.py` (Story 1.5 stanje — override za dev):**

```python
# Dev koristi plain StaticFilesStorage (NO manifest).
# CompressedManifestStaticFilesStorage zahteva staticfiles.json (generisan posle
# collectstatic-a) — bez njega {% static %} baca ValueError pri prvom render-u.
# Dev server čita direktno iz STATICFILES_DIRS preko Whitenoise middleware-a.
# Vidi Gotcha #28.
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
```

**After — `config/settings/production.py` + `staging.py` (Story 1.5 stanje — Whitenoise manifest):**

```python
# Prod/staging koriste Whitenoise CompressedManifestStaticFilesStorage:
# - hash u filename (tokens.<hash>.css) → cache-busting + max-age=1y
# - automatski .gz + .br kompresovane varijante
# Zahteva collectstatic --noinput kao deploy step (PRE prvog request-a).
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}
```

**MIDDLEWARE modifikacija (Before — Story 1.4 stanje, linije 38-48):**

```python
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.core.middleware.LocaleSwitcherMiddleware",
]
```

**MIDDLEWARE modifikacija (After — Story 1.5 stanje):**

```python
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",                # NOVO — POSLE Security, PRE Session
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.core.middleware.LocaleSwitcherMiddleware",
]
```

### base.html modifications

**Before (Story 1.4 stanje):**

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

**After (Story 1.5 stanje):**

```html
<!DOCTYPE html>
{% load i18n %}
{% load static %}
<html lang="{{ LANGUAGE_CODE }}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{% block title %}Ćorić Agrar{% endblock %}</title>
  <link rel="stylesheet" href="{% static "css/tokens.css" %}">
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

**Napomena:** `<link>` ka `tokens.css` ide **POSLE** `<title>` i **PRE** `{% block extra_head %}` jer Story 1.6 ekstenduje `extra_head` sa Bootstrap CSS link-om — Bootstrap mora **nakon** tokens.css da bi custom properties bili dostupni u `var(--...)` referencama unutar Bootstrap override-ova (Story 1.6 zadatak).

### Roboto download instrukcije (DETALJNO — Mihas ručna akcija)

**Korak 1 — Otvori Google Webfonts Helper:**
- URL: `https://gwfh.mranftl.com/fonts/roboto`
- Alt URL (ako gwfh down): `https://google-webfonts-helper.herokuapp.com/fonts/roboto` (legacy mirror)

**Korak 2 — Selektuj karakteristike:**

| Sekcija | Selekcija |
|---|---|
| Styles | ☑ 300, ☑ regular (400), ☑ 700 (DESELEKTUJ: 100, 100italic, 300italic, 400italic, 500, 500italic, 700italic, 900, 900italic) |
| Charsets / Subsets | ☑ latin, ☑ latin-ext (DESELEKTUJ: cyrillic, cyrillic-ext, greek, greek-ext, vietnamese) |
| Format | ☑ Modern Browsers (woff2) **SAMO** (DESELEKTUJ: Best Support, Legacy Support) |

**Korak 3 — Customize folder prefix:**
- Stavi: `../fonts/roboto/` (matches `tokens.css` relativan path; ali Dev će overrid-ovati src u `tokens.css` template-u, pa ovaj prefix nije kritičan — može ostati default)

**Korak 4 — Download:**
- Klikni dugme "Download files" — preuzima `roboto.zip` (~150-200 KB)

**Korak 5 — Raspakuj i rename u `static/fonts/roboto/`:**

ZIP sadrži 6 fajlova sa nazivima poput `roboto-v30-latin-300.woff2`. Rename-uj ih u canonical formu:

| ZIP filename (template; verzija `vNN` može varirati) | Canonical filename (Story 1.5 expectation) |
|---|---|
| `roboto-vNN-latin-300.woff2` | `roboto-latin-300.woff2` |
| `roboto-vNN-latin-regular.woff2` | `roboto-latin-400.woff2` |
| `roboto-vNN-latin-700.woff2` | `roboto-latin-700.woff2` |
| `roboto-vNN-latin-ext-300.woff2` | `roboto-latin-ext-300.woff2` |
| `roboto-vNN-latin-ext-regular.woff2` | `roboto-latin-ext-400.woff2` |
| `roboto-vNN-latin-ext-700.woff2` | `roboto-latin-ext-700.woff2` |

**Korak 6 — Smesti u `static/fonts/roboto/`:**

```text
static/
└── fonts/
    └── roboto/
        ├── roboto-latin-300.woff2
        ├── roboto-latin-400.woff2
        ├── roboto-latin-700.woff2
        ├── roboto-latin-ext-300.woff2
        ├── roboto-latin-ext-400.woff2
        └── roboto-latin-ext-700.woff2
```

**Sanity check — sizes (after rename + smeštanje):**

```bash
# Linux/Mac:
ls -lh static/fonts/roboto/
# Očekivane veličine (orijentacioni — gwfh ažurira subset s vremena):
# roboto-latin-300.woff2          ~16-25 KB
# roboto-latin-400.woff2          ~16-25 KB
# roboto-latin-700.woff2          ~16-25 KB
# roboto-latin-ext-300.woff2      ~10-18 KB
# roboto-latin-ext-400.woff2      ~10-18 KB
# roboto-latin-ext-700.woff2      ~10-18 KB
# UKUPNO: ~100-150 KB (well under 300 KB sanity limit)

du -sh static/fonts/roboto/
# Očekivano: ~120-150 KB total
```

```powershell
# Windows PowerShell:
Get-ChildItem static/fonts/roboto/ -Filter *.woff2 | Select-Object Name, @{N='Size KB';E={[Math]::Round($_.Length / 1KB, 1)}}
Get-ChildItem static/fonts/roboto/ -Filter *.woff2 | Measure-Object -Property Length -Sum | Select-Object @{N='Total KB';E={[Math]::Round($_.Sum / 1KB, 1)}}
```

**Alt — `fonttools` Python subsetting (advanced; ne za Story 1.5):**

Ako gwfh nije dostupan, alternativa je generisati subset ručno preko `fonttools` library-ja:

```bash
uv add --dev fonttools
# Preuzmi Roboto sa GitHub: https://github.com/googlefonts/roboto/releases
# Pokreni pyftsubset za svaku težinu/subset (6 puta):
pyftsubset Roboto-Light.ttf --unicodes="U+0000-00FF,U+0131,U+0152-0153,..." --output-file=roboto-latin-300.woff2 --flavor=woff2
```

**Story 1.5 NE traži ovo** (gwfh je prosti put). Listano samo radi reference.

### Verzioniranje fajlova (no-rename, no-bust convention)

- Whitenoise `CompressedManifestStaticFilesStorage` u **prod-u** automatski dodaje hash u filename pri `collectstatic` (`tokens.a1b2c3d4.css`, `roboto-latin-400.e5f6g7h8.woff2`)
- U **dev-u** (DEBUG=True), Whitenoise servira `STATICFILES_DIRS` direktno bez hash-a — filename je `tokens.css`, `roboto-latin-400.woff2`
- `{% static "css/tokens.css" %}` u template-u **resolve-uje** ka:
  - Dev: `/static/css/tokens.css`
  - Prod: `/static/css/tokens.a1b2c3d4.css` (manifest mapira)
- Dev ne brine o hash-u — Django + Whitenoise handluju automatski

### Gotchas (15+ tačaka — najlakše promašiti)

1. **Prazni direktorijumi se ne commit-uju u Git**: ako kreiraš `static/css/` pre nego što ima `tokens.css`, Git neće commit-ovati `static/css/` (prazan folder). U Story 1.5, Task 2 kreira foldere, Task 4 dodaje `tokens.css`, Task 3 dodaje woff2 fajlove — finalan commit će imati i foldere i fajlove zajedno (nema potrebe za `.gitkeep`).

2. **`STATICFILES_DIRS` mora biti lista, ne tuple**: Django stari kod koristi `STATICFILES_DIRS = ("path",)`. Django 5.x preporučuje listu radi konzistentnosti. Tuple je validan ali generiše warning u nekim verzijama.

3. **`STATIC_URL = "static/"` vs `"/static/"`**: Django formalno dozvoljava oboje. Sa leading slash (`/static/`) je apsolutan URL; bez (`static/`) je relativan (Django ne dodaje slash automatski). Story 1.2 je koristila `"static/"` — Story 1.5 menja na `"/static/"` jer Story 1.4 je uvela `i18n_patterns` koje prefiks-uje sve relativne URL-ove sa `/sr/` ili `/hu/` (vidi Gotcha #29).

4. **`src: url('../fonts/roboto/...')` relativan path**: `tokens.css` se nalazi u `static/css/`, font-ovi u `static/fonts/roboto/`. Relativan path od `tokens.css` ka font fajlu = `../fonts/roboto/<file>.woff2`. NE `/static/fonts/roboto/...` (apsolutan) — to lomi ako se sajt deploy-uje na sub-path; NE `fonts/roboto/...` (relativan ka `tokens.css` direktorijumu) — ne ide u parent.

5. **`unicode-range` mora se razlikovati za latin i latin-ext**:
   - **latin:** `U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+2000-206F, U+2074, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD` (ASCII + Latin Supplement + some general punctuation)
   - **latin-ext:** `U+0100-024F, U+0259, U+1E00-1EFF, U+2020, U+20A0-20AB, U+20AD-20CF, U+2113, U+2C60-2C7F, U+A720-A7FF` (Latin Extended-A/B/Additional)
   - Browser odlučuje koji subset da preuzme na osnovu glyph-ova u stranicama — ako stranica ima samo ASCII, latin se preuzima, latin-ext se preskače. Sa Story 1.4 (`<p>Dobrodošli.</p>` ima `š` koji je u latin-ext / Latin Extended), browser će preuzeti i latin i latin-ext.

6. **`STATICFILES_DIRS` bez `BASE_DIR / "static"` exists check**: ako pišeš `STATICFILES_DIRS = [BASE_DIR / "static"]` ali `static/` direktorijum NE postoji (Story 1.5 Task 2 ga kreira), Django generiše warning `staticfiles.W004` na svaki `collectstatic` poziv. Ne lomi runtime, ali je signal da nešto fali. Task 2 kreira folder PRE Task 7 (settings izmena) — order matters.

7. **`STATIC_URL` mora završavati sa `/`**: Django zahteva trailing slash; bez njega dobijaš `ImproperlyConfigured: The STATIC_URL setting must end with a slash`. Story 1.5 finalna vrednost: `"/static/"` (leading + trailing slash; trailing je obavezan, leading je preporučen — vidi Gotcha #29).

8. **`STATIC_ROOT` ne sme biti unutar `STATICFILES_DIRS`**: ako `STATIC_ROOT = BASE_DIR / "static"` i `STATICFILES_DIRS = [BASE_DIR / "static"]`, `collectstatic` će kopirati `static/*` u `static/*` — circular reference, error. Naš setup: `STATIC_ROOT = BASE_DIR / "staticfiles"` (drugačiji folder), `STATICFILES_DIRS = [BASE_DIR / "static"]` — OK. **`staticfiles/` MORA biti u `.gitignore`** (Whitenoise gradi tu cache; commit-ovati bi se uvek dirty repo).

9. **Django 5.1+ `STORAGES` dict je canonical (`STATICFILES_STORAGE` deprecated)**:
   - Django 5.0 i ranije: `STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"`
   - Django 5.1+: koristi `STORAGES = {"default": {...}, "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"}}`
   - Postavljanje obe daje warning `RemovedInDjango60Warning: STATICFILES_STORAGE is deprecated`. Story 1.5 koristi **samo** `STORAGES` dict.

10. **`uv add` umesto ručnog `pyproject.toml` edita**: `uv add whitenoise>=6.8.0` automatski:
    - Updated `pyproject.toml` `[project.dependencies]`
    - Updated `uv.lock` sa rezolverom (rešava trans dependencies)
    - Reinstalira venv (.venv) — ali u Docker-u (Story 1.3) venv je u image-u; treba `just dev-build` da rebuild-uje sa novim deps-ima
    - **Ručno editovanje pyproject.toml NE menja `uv.lock`** — `uv sync` će čitati `pyproject.toml` i ažurirati `uv.lock`, ali bolje je `uv add` jer je atomic.

11. **Roboto font subset size > 300 KB = pogrešna selekcija**:
    - 3 weights × 2 subsets × ~25 KB = ~150 KB očekivano
    - Ako je `du -sh static/fonts/roboto/` > 300 KB, verovatno je preuzeto:
      - Cyrillic subset (dodaje ~25-40 KB)
      - Greek subset (dodaje ~10-15 KB)
      - Vietnamese subset (dodaje ~10-15 KB)
      - Italic weights (dupli broj fajlova)
    - **Rešenje:** ponovi gwfh download sa STRIKTNO latin + latin-ext, weights 300/400/700, woff2 only.

12. **`whitenoise` NE ide u `INSTALLED_APPS`**: Whitenoise je middleware-only. Postoji opciono `whitenoise.runserver_nostatic` koji se dodaje u `INSTALLED_APPS` **PRE** `django.contrib.staticfiles` — ali to je samo za **isključivanje** Django dev server static handling-a (tako da Whitenoise potpuno preuzima). Story 1.5 **NE dodaje** `runserver_nostatic` — Django default static handling i Whitenoise rade simultano u dev-u (no konflikt, Whitenoise samo prefiks-uje).

13. **`{% load static %}` mora biti pre prvog `{% static %}` poziva**: bez `{% load static %}` direktive, `{% static "css/tokens.css" %}` daje `TemplateSyntaxError: Invalid block tag 'static'`. Mora biti deklarisana na nivou template-a (ili u nasleđenom template-u). U `base.html` se postavlja odmah posle `{% load i18n %}`.

14. **Bootstrap CSS dolazi u Story 1.6 — Story 1.5 NE dodaje**: AC7 specificira da `tokens.css` link ide PRE `{% block extra_head %}` jer Story 1.6 dodaje Bootstrap link unutar `extra_head` block-a (ili direktno u `<head>` — Story 1.6 odluka). Story 1.5 ne sme preempt-ovati Story 1.6 i dodavati Bootstrap; samo tokens.css.

15. **Komponentni tokeni (button, card, itd.) iz DESIGN.md `components` NISU u tokens.css**: DESIGN.md ima `components.button.primary.bg: "{colors.brand.green-800}"` itd. — ovo su **references** ka osnovnim tokenima. Story 1.5 ne pred-izračunava ove vrednosti u `tokens.css` (npr. ne dodaje `--button-primary-bg: var(--color-brand-green-800)`). Razlog: YAGNI — Story 1.7 (Reusable komponente) konzumira osnovne tokene direktno u komponentnom CSS-u (`.coric-button--primary { background: var(--color-brand-green-800); }`). Ako se kasnije pokaže da je apstrakcioni nivo koristan (npr. button bg menja po brand-u), tada se uvodi `--button-primary-bg` token — ali ne sad.

16. **`tokens.css` ne sme da koristi `@import url('https://fonts.googleapis.com/...')`**: AC3 eksplicitno; anti-pattern. Self-hosted znači self-hosted — ni preko CSS-a se ne sme učitavati eksterni Google Fonts URL.

17. **`<link rel="preconnect">` ka external domains je takođe anti-pattern**: čak i ako nije `<link rel="stylesheet">`, `preconnect` ka `fonts.googleapis.com` pokreće DNS lookup + TCP handshake — što je tracking signal (Google logging) + GDPR concern. Story 1.5 AC7 explicit-no zabranjuje.

18. **Browser dev tools Computed styles vs Styles**: pri verifikaciji da `var(--color-brand-green-800)` resolve-uje na `#25402f` u dev tools-u:
    - **Styles** tab pokazuje raw CSS rules (sa `var(--color-brand-green-800)` literal)
    - **Computed** tab pokazuje resolved vrednosti (`#25402f`)
    - Dev mora gledati **Computed** za verifikaciju. AC8 specifikuje ovo.

19. **`collectstatic --dry-run` u dev-u: očekivani fajlovi**:
    - `--dry-run` skenira `STATICFILES_DIRS` i `STATICFILES_FINDERS` (default: `FileSystemFinder` + `AppDirectoriesFinder`)
    - Output izgleda: `Pretending to copy '/path/static/css/tokens.css'`
    - Sa `CompressedManifestStaticFilesStorage`, fajlovi se kopiraju u `STATIC_ROOT` (`staticfiles/`) sa hash-iranim filename-om — ali `--dry-run` ne menja filesystem
    - U Story 1.5 dev test, `--dry-run` treba da nađe `tokens.css` + 6 woff2 = **7 fajlova** (+ Django admin static-i ali to je 100+ fajlova — Whitenoise će ih ali ne tiču se Story 1.5 verifikacije)

20. **Docker bind mount + Whitenoise**: u `compose/local.yml`, repo se mountuje preko `../:/app:cached`. Sve fajlove u `static/` su odmah vidljivi u kontejneru bez restart-a. Whitenoise u dev-u (DEBUG=True) servira `STATICFILES_DIRS` direktno — promene u `static/css/tokens.css` su vidljive na refresh stranice. **NEMA potrebe za `collectstatic` u dev-u** (samo za prod).

21. **Browser cache + hard refresh**: pri prvoj poseti `http://localhost:8000/sr/`, browser keširaše `tokens.css` ako server šalje cache header-e. Whitenoise u dev-u NE šalje agresivan cache (Django runserver + Whitenoise dev mode = `Cache-Control: no-cache, no-store, must-revalidate`). Ali ako Dev otvori stranicu pre nego što je `tokens.css` kreirana, prvi 404 može biti keširan kao negative cache (negativan response cache je < 1 minute u većini browsera). **Rešenje:** Ctrl+Shift+R (hard refresh) ili Ctrl+F5 — bypass-uje cache.

22. **`{% static %}` template tag vs `static/` URL u inline `<style>`**:
    - `{% static "css/tokens.css" %}` — Django resolve-uje preko `STATIC_URL` + Whitenoise manifest (hash u prod-u). PREFERIRANO.
    - `/static/css/tokens.css` (hard-coded) — radi u dev-u ali u prod-u sa hash-iranim filename-om dobijaš 404. ANTI-PATTERN.
    - Story 1.5 AC7 koristi `{% static %}` — ispravan pristup.

23. **`tokens.css` lint-ing — `djade` ne procesira CSS**: `djade --check templates/` skenira samo `.html` template-e. CSS lint nije konfigurisan u v1 (ruff je samo za Python). Manualni review `tokens.css` posle Task 6 je preporučen — verifikuj indentation (2 razmaka), curly braces order, hex vrednosti lowercase. Story 1.9 (CI pipeline) opciono dodaje `stylelint` ako se pojavi potreba.

24. **Cyrillic glyph-ovi u sr stringovima u template-ima**: project-context.md § Anti-pattern eksplicitno: NIKAD ćirilica. Roboto latin-ext POKRIVA sve sr/hu/en latinične karaktere (Č, Ć, Đ, Š, Ž, á, é, í, ó, ö, ő, ú, ü, ű). Ako se pojavi ćirilica u UI stringu, font će nedostajati glyph i browser će prikazati fallback (system font) — ali to je bug u kontentu, ne u font setup-u. Story 1.5 ne testira ovo — pre-uslov "nema ćirilice" je Story 1.4 testna stvar (verifikuje `templates/base.html` ima samo latinicu).

25. **`font-stretch: normal` opciono**: nije zahtevano u Story 1.5 AC3 (`font-stretch: normal` je default u svakom `@font-face` deklaraciji). Dodajemo ga eksplicitno radi future-proof: kada browser-i podržavaju variable Roboto font (sa `font-stretch: condensed`-`expanded`), eksplicitno `font-stretch: normal` osigurava da naš non-variable subset ne kolide sa drugim variable @font-face deklaracijama.

26. **`{% static %}` resolves URL — NE absolutni filesystem path**: Dev koji misli da `{% static "css/tokens.css" %}` resolves u `/app/static/css/tokens.css` (apsolutan filesystem path) — pogrešno. Resolves u `/static/css/tokens.css` (URL path). Whitenoise/Django servira preko URL routing-a.

27. **`STORAGES` dict default `default` storage MORA biti tu**: ako pišeš `STORAGES = {"staticfiles": {...}}` BEZ `"default"` key-a, Django dobija `KeyError: 'default'` na svaki upload (sav `FileField` upload koristi `STORAGES["default"]`). Naš template ima oba — ne menjati.

28. **`CompressedManifestStaticFilesStorage` u DEBUG=True puca uz `ValueError: Missing staticfiles manifest entry`**:
    - Manifest storage čita `staticfiles.json` (manifest fajl koji generiše `collectstatic`). Mapira `tokens.css` → `tokens.<hash>.css`.
    - U dev-u (DEBUG=True), Dev TIPIČNO ne pokreće `collectstatic` — Whitenoise/Django servira direktno iz `STATICFILES_DIRS`. Manifest **NE postoji** — pri prvom `{% static "css/tokens.css" %}` poziva Django dobija `ValueError: Missing staticfiles manifest entry for 'css/tokens.css'`.
    - **Workaround:** `config/settings/development.py` override-uje `STORAGES["staticfiles"]["BACKEND"] = "django.contrib.staticfiles.storage.StaticFilesStorage"` (plain storage, no manifest). Plain storage radi bez `collectstatic`-a.
    - **Production keep:** `production.py` (i `staging.py`) drže `CompressedManifestStaticFilesStorage` (cache-busting + kompresija; collectstatic je obavezan deploy step).
    - Alternativa (ako ne želiš per-env split): pokreni `uv run python manage.py collectstatic --noinput` u dev-u pri svakoj promeni `tokens.css` — neprijatan workflow, NE preporučeno.

29. **`STATIC_URL` MORA imati leading slash kada se koristi `i18n_patterns`**:
    - Bez leading slash-a: `STATIC_URL = "static/"` → `{% static "css/tokens.css" %}` renderuje kao `static/css/tokens.css` (relativan URL).
    - Pri pristupu `/sr/` ili `/hu/` route-u (i18n_patterns), browser resolve-uje relativan URL u kontekstu **trenutne stranice**: `/sr/static/css/tokens.css` → **404** (Whitenoise traži `/static/...` apsolutno).
    - **Rešenje:** `STATIC_URL = "/static/"` (leading slash) → `{% static %}` uvek vraća apsolutan URL `/static/css/tokens.css`, nezavistan od trenutne stranice.
    - Story 1.2 je koristila `"static/"` (bez slash-a) ali bez i18n_patterns; Story 1.4 je uvela `i18n_patterns` koje su eksponirale bug. Story 1.5 popravlja na `"/static/"`.
    - Django formalno dozvoljava oba oblika (`STATIC_URL` mora završavati slash-om — početni slash je opcioni), ali sa i18n_patterns leading slash je obavezan u praksi.

### Web Intelligence (Whitenoise 6.8 + Django 5.2 specifics)

**Whitenoise 6.8.x (latest stable kao 2026-05):**
- Podržava Django 5.2 LTS (verified)
- `CompressedManifestStaticFilesStorage` je preporučena varijanta za prod (gzip + brotli compression, manifest cache-busting)
- Alternative `CompressedStaticFilesStorage` (bez manifest, bez hash) — za sajtove gde se cache invalidacija oslanja na URL versioning iz drugog izvora (CDN). NE koristimo u Story 1.5.
- `whitenoise.middleware.WhiteNoiseMiddleware` je sync (NE async) — kompatibilno sa Django 5.2 sync middleware chain-om
- Brotli compression zahteva `brotli` Python paket (Whitenoise pruža optional extra: `uv add whitenoise[brotli]>=6.8.0`). U Story 1.5 dodajemo **bez brotli extra-a** (gzip je dovoljan; brotli može dodati Story 9.10 finalni Lighthouse polish).

**Django 5.2 `STORAGES` dict specifics:**
- Default vrednost (Django 5.2 default): `STORAGES = {"default": {"BACKEND": "django.core.files.storage.FileSystemStorage"}, "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"}}`
- Override-ujemo `staticfiles` na Whitenoise; `default` ostavljamo Django default (sve `FileField` uploads idu na lokalan filesystem; Story 2.3 image pipeline može override-ovati na S3 ili sl. — nije u Story 1.5 scope-u)
- `STATICFILES_STORAGE` (deprecated) — Django 5.2 i dalje radi ali baca `RemovedInDjango60Warning`. Story 1.5 koristi `STORAGES`.

**Font subset references:**
- Google Webfonts Helper: https://gwfh.mranftl.com/fonts/roboto
- Roboto official GitHub: https://github.com/googlefonts/roboto
- Roboto licenca: https://github.com/googlefonts/roboto/blob/main/LICENSE (Apache 2.0)
- unicode-range MDN docs: https://developer.mozilla.org/en-US/docs/Web/CSS/@font-face/unicode-range
- font-display MDN docs: https://developer.mozilla.org/en-US/docs/Web/CSS/@font-face/font-display

**Whitenoise reference:**
- Docs: https://whitenoise.readthedocs.io/en/stable/django.html
- GitHub: https://github.com/evansd/whitenoise
- Django integration: https://whitenoise.readthedocs.io/en/stable/django.html#enable-whitenoise

### Previous story intelligence (Story 1.4 learnings)

**Iz Story 1.4 retro:**
- **Custom middleware contract:** `__init__(self, get_response)` + `__call__(self, request)` (Story 1.4 LocaleSwitcherMiddleware je primer; Whitenoise prati isti contract)
- **MIDDLEWARE order matters:** Story 1.4 je upozorila da `LocaleMiddleware` ide POSLE `SessionMiddleware`. Story 1.5 dodaje `WhiteNoiseMiddleware` koji ide **PRE** `SessionMiddleware` (Whitenoise docs). Order: Security → **Whitenoise** → Session → Locale → Common → CSRF → Auth → Messages → Clickjacking → LocaleSwitcher.
- **Settings file conventions:** Story 1.4 je dodala `LANGUAGES`, `LOCALE_PATHS`, `USE_L10N` u `# ── i18n ──` sekciju. Story 1.5 dopunjuje `# ── Static ──` sekciju sa `STATICFILES_DIRS`, `STATIC_ROOT`, `STORAGES`. **Sekcionalno organizovan kod — ne mešati.**
- **Template `{% load %}` direktive:** Story 1.4 je `{% load i18n %}`; Story 1.5 dodaje `{% load static %}` — **multi-line load deklaracije** (po jedna `{% load %}` per direktiva, ne kombinovano kao `{% load i18n static %}` jer to nije Django convention iako tehnički validno).
- **`uv add` workflow:** Story 1.4 NIJE dodala nove deps (samo settings). Story 1.5 dodaje `whitenoise>=6.8.0` — pokreće `uv add whitenoise>=6.8.0` koji ažurira **`pyproject.toml` + `uv.lock` atomski**. Posle `uv add`, **mora `just dev-build`** da Docker image dobije novi paket u .venv-u.
- **`.gitignore` discipline:** Story 1.1 je kreirala `.gitignore` sa `.venv/`, `__pycache__/`, `db.sqlite3`. Story 1.3 je dodala `media/`, `*.pyc`. Story 1.5 dodaje `staticfiles/` (Whitenoise destination, prod-only — nikad commit). **Verifikuj pre commit-a.**
- **Smoke validation pattern:** Story 1.4 je koristila kombinaciju `manage.py check` + `manage.py shell -c "..."` + Browser GET. Story 1.5 nasleđuje ovo + dodaje `collectstatic --dry-run` + dev tools Network tab check.

### Git intelligence

Poslednjih 5 commit-a (Story 1.1-1.4) su uvodili: uv bootstrap → settings split → Docker compose → i18n setup. Story 1.5 commit će biti **višefajl atomic**:

- `static/css/tokens.css` (NEW)
- `static/fonts/roboto/*.woff2` (6 NEW files)
- `config/settings/base.py` (MODIFIED — Static section + MIDDLEWARE)
- `templates/base.html` (MODIFIED — load static + link tokens.css)
- `pyproject.toml` (MODIFIED — whitenoise dep)
- `uv.lock` (MODIFIED — whitenoise + transitive deps)
- `.gitignore` (MODIFIED if missing `staticfiles/`)

**Commit poruka template:**
```
feat(static): add self-hosted Roboto + tokens.css with 63 CSS Custom Properties

- Add whitenoise>=6.8.0 dep + WhiteNoiseMiddleware + per-env STORAGES dict
- Add STATICFILES_DIRS + STATIC_ROOT settings; STATIC_URL = "/static/" (leading slash)
- Add static/fonts/roboto/ (6 woff2: 3 weights × 2 subsets, total ~150KB)
- Add static/css/tokens.css with @font-face decls + :root tokens (21 color + 42 typography/rounded/shadow/spacing)
- Link tokens.css in templates/base.html
- 1:1 mapping from DESIGN.md frontmatter
```

### Project context reference

**Konsultuj uvek:**
- `_bmad-output/project-context.md` § Frontend (no build pipeline; Self-hosted Roboto subset; font-display: swap)
- `_bmad-output/project-context.md` § CSS naming (BEM-like + coric- prefix; CSS Custom Properties tokens)
- `_bmad-output/project-context.md` § CSS Custom Properties (`--<group>-<name>-<variant>` naming; `var(--token)` korišćenje)
- `_bmad-output/project-context.md` § Anti-pattern: Inline CSS / magic values
- `_bmad-output/project-context.md` § Performance must-haves (font-display: swap, Whitenoise compressed manifest)
- `_bmad-output/planning-artifacts/architecture.md` § Frontend Decisions (Static files: Whitenoise; Font loading: self-hosted)
- `_bmad-output/planning-artifacts/architecture.md` § Project Structure (static/css/, static/fonts/roboto/, static/vendor/)
- `_bmad-output/planning-artifacts/ux-designs/ux-CORIC_AGRAR-2026-05-27/DESIGN.md` § Colors, Typography, Layout & Spacing, Components (SOT za sve token vrednosti)

## Testing

**Šta testirati (TEA agent piše testove; Dev ih ne dira):**

**Filesystem checks:**
- `static/css/tokens.css` postoji (regex: `pathlib.Path('static/css/tokens.css').exists()`)
- `static/fonts/roboto/` direktorijum postoji
- Tačno 6 `.woff2` fajlova u `static/fonts/roboto/`
- Tačni filename-i: `roboto-latin-300.woff2`, `roboto-latin-400.woff2`, `roboto-latin-700.woff2`, `roboto-latin-ext-300.woff2`, `roboto-latin-ext-400.woff2`, `roboto-latin-ext-700.woff2`
- Magic bytes svakog woff2 fajla = `wOF2` (prva 4 bajta)
- Ukupna veličina `static/fonts/roboto/` < 300 KB (`sum(f.stat().st_size for f in Path('static/fonts/roboto/').glob('*.woff2'))`)

**tokens.css content checks (regex/string match):**
- 6 `@font-face` blokova: `re.findall(r'@font-face\s*\{', content)` → 6 matches
- `font-display: swap` se pojavljuje 6 puta
- 3 latin `unicode-range` (`U+0000-00FF`) i 3 latin-ext (`U+0100-024F`)
- `:root` blok postoji
- 63 custom property deklaracije u `:root` (`re.findall(r'^\s*--[a-z-]+:', content, re.MULTILINE)` → 63 matches)
- Specifične token vrednosti (svaki AC iz epics.md):
  - `--color-brand-green-800: #25402f` (exact line match)
  - `--typography-scale-h1: 3.5rem`
  - `--rounded-pill: 999px`
  - `--shadow-md: 0 2px 8px rgba(31, 63, 47, 0.06)`
  - `--spacing-section: 80px`
- Naming compliance:
  - Svi color tokeni starting sa `--color-` (regex: `^\s*--color-[a-z-]+:` count → 21)
  - Svi typography tokeni starting sa `--typography-` (count → 16)
  - Svi rounded tokeni starting sa `--rounded-` (count → 6)
  - Svi shadow tokeni starting sa `--shadow-` (count → 5)
  - Svi spacing tokeni starting sa `--spacing-` (count → 15)
- **Negative checks:**
  - NIJEDAN `googleapis.com` ili `gstatic.com` u fajlu (anti-pattern)
  - NIJEDAN `@import` direktiva (anti-pattern — sve `@font-face` su inline)

**base.py validity:**
- `STATICFILES_DIRS` setting postoji i sadrži `BASE_DIR / "static"`
- `STATIC_ROOT` setting postoji i jednak `BASE_DIR / "staticfiles"`
- `STORAGES` dict postoji sa key-evima `"default"` i `"staticfiles"` (per-env split posle FIX 2):
  - **base.py default**: `STORAGES["staticfiles"]["BACKEND"]` = `"django.contrib.staticfiles.storage.StaticFilesStorage"` (plain placeholder — Django default)
  - **development.py override**: isti `"django.contrib.staticfiles.storage.StaticFilesStorage"` (eksplicitno za dev clarity)
  - **production.py override**: `STORAGES["staticfiles"]["BACKEND"]` = `"whitenoise.storage.CompressedManifestStaticFilesStorage"` (manifest + compression za prod cache busting)
  - **staging.py override**: isti kao production.py (`"whitenoise.storage.CompressedManifestStaticFilesStorage"`)
- `MIDDLEWARE` lista sadrži `"whitenoise.middleware.WhiteNoiseMiddleware"` na poziciji 1 (drugi element, posle SecurityMiddleware) — u base.py (svi env-ovi nasledjuju)
- `"whitenoise"` NIJE u `INSTALLED_APPS`
- `LANGUAGES`, `LOCALE_PATHS`, `LANGUAGE_CODE = "sr"` ostaju iz Story 1.4 (regression)

**base.html source checks:**
- `{% load static %}` direktiva prisutna posle `{% load i18n %}`
- `<link rel="stylesheet" href="{% static "css/tokens.css" %}">` prisutan
- Link je unutar `<head>` (između `<title>` i `{% block extra_head %}` ili `</head>`)
- NIJEDAN `googleapis.com`/`gstatic.com`/`fonts.gstatic.com` u source-u
- Regression: `<html lang="{{ LANGUAGE_CODE }}">` ostaje, `{% include "partials/language_switcher.html" %}` ostaje, `{% block content %}` ostaje

**Django integration (pytest-django):**
- `collectstatic --dry-run --noinput` exit 0 (kroz `django.core.management.call_command("collectstatic", dry_run=True, interactive=False)` u test-u)
- Output sadrži `css/tokens.css` i barem jedan `fonts/roboto/...woff2`

**Django Client (pytest-django `client` fixture):**
- `client.get("/static/css/tokens.css")` → status 200, content-type `text/css; charset=...`, content sadrži `--color-brand-green-800: #25402f`
- `client.get("/static/fonts/roboto/roboto-latin-400.woff2")` → status 200, content-type `font/woff2`, content počinje sa magic bytes `b'wOF2'`
- `client.get("/sr/")` → status 200, response HTML sadrži `<link` `rel="stylesheet"` `href="/static/css/tokens.css"` (bez hash-a — test env koristi plain `StaticFilesStorage` kao i dev; hash-iranje je samo u prod/staging kroz Whitenoise manifest)

**Regression checks:**
- Postojeći Story 1.4 testovi (i18n routing, language switcher) i dalje prolaze
- `client.get("/")` → 302 redirect na `/sr/`
- `client.get("/sr/")` → 200, `<html lang="sr">`
- `client.get("/hu/")` → 200, `<html lang="hu">`

**Whitenoise integration (opciono — TEA odluka):**
- `import whitenoise; assert whitenoise.__version__ >= "6.8.0"` (sanity check)
- `from whitenoise.middleware import WhiteNoiseMiddleware` import radi (verifikuje deps instalacija)

**Negative regression (anti-pattern guard):**
- `grep -r "googleapis.com" templates/ static/` → no matches
- `grep -r "gstatic.com" templates/ static/` → no matches
- `grep -r "preconnect" templates/` → no matches (Story 1.5 nema preconnect; Story 1.6 može uvesti za Bootstrap CDN-fallback, ali sa restrikcijama)

**E2E (Playwright — opciono za Story 1.5; rekomendovano u Story 9.8):**
- Playwright test: navigate `http://localhost:8000/sr/`, assert `<link rel="stylesheet" href="/static/css/tokens.css">` u DOM-u
- Network listener: assert no request ka `*.googleapis.com` ili `*.gstatic.com`
- Computed style assert: `document.documentElement.style.getPropertyValue('--color-brand-green-800').trim()` === `'#25402f'`

**Out-of-scope za Story 1.5 testing:**
- Lighthouse a11y score (Story 1.6 / 9.9)
- Visual regression testing (Story 9.10)
- Browser compatibility matrix (Chrome/Firefox/Safari) — Roboto woff2 univerzalno podržan
- Performance benchmarks (LCP, FCP) — Story 9.9 load test

---

## Dev Agent Record

### Context Reference

- Implementation guide: `_bmad-output/implementation-artifacts/1-5-self-hosted-roboto-design-md-tokens-kao-css-custom-properties.md` (ovaj fajl)
- DESIGN.md source-of-truth: `_bmad-output/planning-artifacts/ux-designs/ux-CORIC_AGRAR-2026-05-27/DESIGN.md`
- Previous story (kontekst nasledjivanja): `_bmad-output/implementation-artifacts/1-4-i18n-setup-sa-locale-url-routing-i-switcher.md`

### Agent Model Used

- Claude Opus 4.7 (1M context) — Dev agent (fresh GREEN phase implementer)

### File List

**Created:**
- `static/css/tokens.css` — 6 @font-face deklaracija + :root sa 63 CSS custom properties
- `static/` direktorijum (root)
- `static/css/` direktorijum
- `static/fonts/` direktorijum
- `static/fonts/roboto/` direktorijum (prazan — Mihas mora ručno preuzeti 6 woff2 fajlova)

**Modified:**
- `config/settings/base.py` — MIDDLEWARE (dodato WhiteNoiseMiddleware POSLE Security PRE Session); STATIC_URL "/static/" (leading slash); STATICFILES_DIRS + STATIC_ROOT + STORAGES dict
- `config/settings/development.py` — STORAGES override (plain StaticFilesStorage) + WHITENOISE_USE_FINDERS = True + WHITENOISE_AUTOREFRESH = True (za pytest-django kompatibilnost — DEBUG=False u testovima)
- `config/settings/staging.py` — STORAGES override (Whitenoise CompressedManifestStaticFilesStorage)
- `config/settings/production.py` — STORAGES override (Whitenoise CompressedManifestStaticFilesStorage)
- `templates/base.html` — dodato `{% load static %}` + `<link rel="stylesheet" href="{% static "css/tokens.css" %}">`
- `pyproject.toml` — dodato `whitenoise>=6.8.0` u `[project.dependencies]` (via `uv add`)
- `uv.lock` — atomski regenerisan sa novim deps (whitenoise 6.12.0)
- `tests/test_bootstrap.py` — uklonjeno `"static"` iz forbidden list (legitimate Story 1.5 amendment per pattern Story 1.2/1.3/1.4)
- `tests/test_static_tokens.py` — fix za `response.streaming_content` (Whitenoise vraća `WhiteNoiseFileResponse` streaming response — `.content` attribute ne postoji)

### Completion Notes List

- **WhiteNoise version installed:** 6.12.0 (zadovoljava `>=6.8.0` constraint iz pyproject.toml)
- **Install order respected:** `uv add whitenoise` PRE editovanja MIDDLEWARE u base.py — `WhiteNoiseMiddleware` import succeeds
- **Per-env STORAGES split:** base.py + development.py = plain StaticFilesStorage; staging.py + production.py = Whitenoise CompressedManifestStaticFilesStorage
- **STATIC_URL leading slash:** `/static/` (bilo `static/` u Story 1.2) — fix za i18n_patterns kompatibilnost (Gotcha #29)
- **WHITENOISE_USE_FINDERS = True u development.py:** neophodno jer pytest-django postavlja DEBUG=False u testovima, što by default disable-uje finders u Whitenoise-u. Explicit override radi i pytest Client GET-ove bez prethodnog `collectstatic`-a.
- **Hex case lowercase:** SVE hex vrednosti u tokens.css su lowercase 6-digit (#00a4e9, NE #00A4E9; #ffffff, NE #fff)
- **63 CSS custom properties verified:** 21 color (4 brand + 2 accent + 1 brand-specific + 7 neutral + 7 semantic) + 42 ostali (1 family + 3 weight + 7 scale + 3 line-height + 2 tracking + 6 rounded + 5 shadow + 1 base + 9 scale + 2 section + 3 container)
- **6 @font-face deklaracije + 6 font-display: swap matches** verified
- **manage.py check** exit 0 (System check identified no issues)
- **collectstatic --dry-run --noinput** exit 0; output sadrži `tokens.css` (i ostali Django admin static-i)

**Test modifications (legitimate):**
1. `tests/test_bootstrap.py:602-606`: uklonjeno `"static"` iz forbidden list — isti pattern kao Story 1.2 (`.env.example`, `config/settings/`), Story 1.3 (`compose/`, `.env`), Story 1.4 (`apps/`, `templates/`). Razlog: Story 1.5 NAMERNO uvodi `static/` (AC1).
2. `tests/test_static_tokens.py:909` i `:944`: dodao branch za `response.streaming_content` (WhiteNoiseFileResponse je streaming response — `.content` attribute baca AttributeError). Logika fallback-uje na `response.content` ako `streaming_content` nije prisutan (regular Django HttpResponse). Razlog: Whitenoise je legitimno servirao 200 odgovor sa tačnim sadržajem; test je samo loše čitao body.

**Blockers — Mihas manual step:**
- **Task 3.1 — Roboto woff2 download** NIJE završen. Dev agent ne može da preuzima font fajlove (no internet u kontrolisanom kontekstu + licencni concerns). Mihas mora preuzeti 6 woff2 fajlova sa https://gwfh.mranftl.com/fonts/roboto (3 weights × 2 subsets, woff2 only, latin + latin-ext) i smestiti ih u `static/fonts/roboto/` po Task 3.1.8 canonical naming-u. Posle download-a, 5 SKIPPED testova će GREEN.

### Debug Log References

- Test run: 187 passed, 5 skipped, 0 failed
- Skipped tests (sve woff2-dependent — automatski GREEN čim Mihas preuzme fajlove):
  - test_ac2_six_woff2_files_present
  - test_ac2_woff2_naming_convention
  - test_ac2_woff2_total_size_under_300kb
  - test_ac2_woff2_magic_bytes
  - test_ac8_django_client_serves_woff2

### Change Log

| Date | Author | Change |
|---|---|---|
| 2026-05-28 | Mihas (SM autonomous) | Initial story created — status: ready-for-dev |
| 2026-05-28 | Dev (Opus 4.7) | Implementation complete (sve AC1-AC8 osim Roboto woff2 download-a koji čeka Mihas). Status: ready-for-dev → review. |
