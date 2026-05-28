---
story-id: "1.5"
story-key: 1-5-self-hosted-roboto-design-md-tokens-kao-css-custom-properties
artifact: interface-contract
author: TEA (Test Architect)
status: RED phase — kontrakt definiše tests; svi testovi MORAJU pasti dok Dev ne implementira.
language: Srpski (latinica)
---

# Story 1.5 — Interface Contract

Ovaj dokument opisuje **mašinski-verifikatibilan** kontrakt između TEA testova i
Dev implementacije za Story 1.5 (Self-hosted Roboto + DESIGN.md tokens kao CSS
Custom Properties + Whitenoise integracija). Dev mora ispoštovati sve stavke
ispod **doslovno** (imena fajlova, atribut imena, redoslede, string vrednosti) —
bilo kakva devijacija prouzrokuje test fail.

## 1. Očekivani novi fajlovi (Dev MORA kreirati)

### 1.1 Static folder hijerarhija

| Putanja | Tip | Napomena |
|---|---|---|
| `static/` | dir | Root static folder (NOVO — Story 1.5 ga kreira from scratch). |
| `static/css/` | dir | Custom CSS fajlovi. |
| `static/fonts/` | dir | Fonts root. |
| `static/fonts/roboto/` | dir | Roboto woff2 fajlovi. |

**Forbidden u Story 1.5 (YAGNI — uvode ih kasnije story-je):**
- `static/js/` (Story 1.6/1.7)
- `static/img/` (Story 2.3)
- `static/vendor/` (Story 1.6)

### 1.2 Roboto woff2 fajlovi (6 fajlova — Mihas ručno preuzima preko gwfh)

Tačno 6 fajlova u `static/fonts/roboto/` sa kanonskim imenima:

| Filename | Subset | Weight | Approx Size |
|---|---|---|---|
| `roboto-latin-300.woff2` | latin | 300 | ~16-25 KB |
| `roboto-latin-400.woff2` | latin | 400 | ~16-25 KB |
| `roboto-latin-700.woff2` | latin | 700 | ~16-25 KB |
| `roboto-latin-ext-300.woff2` | latin-ext | 300 | ~10-18 KB |
| `roboto-latin-ext-400.woff2` | latin-ext | 400 | ~10-18 KB |
| `roboto-latin-ext-700.woff2` | latin-ext | 700 | ~10-18 KB |

**Sanity bounds:** ukupna veličina svih 6 fajlova MORA biti **< 300 KB**
(preporučeno > 50 KB lower bound — sanity).

**Magic bytes:** svaki fajl počinje sa `b'wOF2'` (`0x77 0x4F 0x46 0x32`).

### 1.3 `static/css/tokens.css`

Kanonski sadržaj definisan u story Dev Notes § tokens.css Template. Mora
sadržati:

**`@font-face` deklaracije (6 ukupno):**
- 3 latin deklaracije (weight 300/400/700) sa `unicode-range: U+0000-00FF, ...`
- 3 latin-ext deklaracije (weight 300/400/700) sa `unicode-range: U+0100-024F, ...`
- Svaka ima: `font-family: 'Roboto'`, `font-style: normal`, `font-weight: <num>`,
  `font-display: swap`, `font-stretch: normal`, `src: url('../fonts/roboto/...')`.

**`:root { ... }` blok (63 CSS Custom Properties):**

- **21 color tokena:**
  - 4 brand greens (`--color-brand-green-900/800/600/400`)
  - 2 accents (`--color-accent-gold-500`, `--color-accent-lime-500`)
  - 1 brand-specific (`--color-jeegee-blue` — **MORA biti lowercase `#00a4e9`**)
  - 7 neutrals (`--color-neutral-cream/white/gray-100/300/500/700/black`)
  - 7 semantic (`--color-semantic-text-primary/text-on-dark/text-muted/border/error/success/focus-ring`)
- **42 ne-color tokena:**
  - 1 typography family (`--typography-family-primary`)
  - 3 weights (`--typography-weight-light/regular/bold`)
  - 7 scale (`--typography-scale-h1/h2/h3/h4/body/small/caption`)
  - 3 line-height (`--typography-line-height-tight/base/relaxed`)
  - 2 tracking (`--typography-tracking-normal/wide`)
  - 6 rounded (`--rounded-none/sm/md/lg/pill/full`)
  - 5 shadows (`--shadow-none/sm/md/lg/nav-shrunk`)
  - 1 spacing base (`--spacing-base`)
  - 9 spacing scale (`--spacing-scale-1/2/3/4/5/6/8/10/12`)
  - 2 section (`--spacing-section`, `--spacing-section-mobile`)
  - 3 container (`--spacing-container-max-width/gutter-desktop/gutter-mobile`)

**Specifične vrednosti (acceptance signals iz epics.md):**
- `--color-brand-green-800: #25402f;`
- `--typography-scale-h1: 3.5rem;`
- `--rounded-pill: 999px;`
- `--shadow-md: 0 2px 8px rgba(31, 63, 47, 0.06);`
- `--spacing-section: 80px;`

**Hex pravila:** svi hex kodovi MORAJU biti **lowercase 6-digit** (`#25402f`, NE
`#25402F`, NE `#fff`). Testovi `test_ac4_no_uppercase_hex` (uppercase guard) +
`test_ac4_no_3digit_shorthand_hex` (3-digit shorthand guard) enforce-uju.

**Anti-pattern guards:**
- NIKAKAV `googleapis.com` ili `gstatic.com` string u fajlu.
- NIKAKAV `@import url(...)` direktiv (sve `@font-face` su inline).

## 2. Očekivane modifikacije postojećih fajlova

### 2.1 `pyproject.toml`

- Dodaj `"whitenoise>=6.8.0"` u `[project.dependencies]` listu.
- **Pokreni:** `uv add whitenoise>=6.8.0` (NE ručno editovati — `uv.lock` mora
  biti sinhron).

### 2.2 `config/settings/base.py` — `# ── Static ──` sekcija

**Before (Story 1.4 stanje):**
```python
STATIC_URL = "static/"
```

**After (Story 1.5 stanje):**
```python
STATIC_URL = "/static/"                              # leading slash (FIX 3 / Gotcha 29)
STATICFILES_DIRS = [BASE_DIR / "static"]             # NOVO
STATIC_ROOT = BASE_DIR / "staticfiles"               # NOVO

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
```

**MIDDLEWARE modifikacija — ubaci `WhiteNoiseMiddleware` POSLE Security, PRE Session:**
```python
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",        # NOVO
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    ...
    "apps.core.middleware.LocaleSwitcherMiddleware",
]
```

**REGRESSION GUARD:** `LANGUAGE_CODE`, `LANGUAGES`, `LOCALE_PATHS`, `DATABASES`,
`EMAIL_*`, `AUTH_PASSWORD_VALIDATORS`, `TEMPLATES`, `INSTALLED_APPS` ostaju
**netaknuti** iz Story 1.4. `whitenoise` **NE** ide u `INSTALLED_APPS`.

### 2.3 `config/settings/development.py`

Dodaj `STORAGES` override (plain — bez manifesta; vidi Gotcha 28):
```python
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
```

### 2.4 `config/settings/staging.py` + `config/settings/production.py`

Dodaj `STORAGES` override sa Whitenoise manifest:
```python
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}
```

### 2.5 `templates/base.html`

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
...
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
...
```

**Pravila:**
- `{% load static %}` ide odmah POSLE `{% load i18n %}` (multi-line, ne kombinovano).
- `<link>` ka `tokens.css` ide **PRE** `{% block extra_head %}` (jer Story 1.6
  doda Bootstrap CSS u `extra_head` — tokens.css mora load prvo).
- `{% static "css/tokens.css" %}` — **double quotes** (konzistentno sa Story 1.4 stilom).

**Anti-pattern guards:**
- NIKAKAV link ka `googleapis.com`, `gstatic.com`, `cdn.jsdelivr.net`.
- NIKAKAV `<link rel="preconnect">` ka external domains.

**REGRESSION GUARD:** `<html lang>`, `<header>` sa language_switcher include,
`<main>` sa block content, `{% block scripts %}`, `</body>` ostaju **netaknuti**.

### 2.6 `.gitignore` (opciono — ako `staticfiles/` nije već u njemu)

Dodaj liniju `staticfiles/` (Whitenoise `collectstatic` destinacija — prod-only,
ne commit).

## 3. Test organizacija

| Test fajl | Šta testira |
|---|---|
| `tests/test_static_tokens.py` | AC1-AC8 — filesystem (static/, woff2 fajlovi), tokens.css sadržaj (@font-face, :root tokens), Django integracija (settings STATICFILES_DIRS/STATIC_ROOT/STORAGES/MIDDLEWARE, env override), base.html render, smoke ( manage.py check + collectstatic --dry-run + Django Client GET-ovi), anti-pattern guards. |

**Cross-cutting modul — NIJE Django app:** `static/` nije app folder, pa testovi
idu u `tests/` (uz `test_bootstrap.py`, `test_docker_compose.py`,
`test_i18n_setup.py`, `test_settings_split.py`).

## 4. Anti-regression flags (KRITIČNO za Dev)

1. **`tests/test_settings_split.py::test_ac1_manage_py_check_passes_for_development`** —
   pokreće `manage.py check`. Posle dodavanja `whitenoise.middleware.WhiteNoiseMiddleware`
   u `MIDDLEWARE` (pre nego što je `whitenoise` dep instaliran), `check` će
   pucati sa `ModuleNotFoundError`. **Dev MORA prvo `uv add whitenoise>=6.8.0`
   PA TEK ONDA editovati `base.py` MIDDLEWARE** (ili sekvencijalno: `uv add` +
   edit + `just dev-build` u Docker-u).

2. **`tests/test_static_tokens.py::test_ac6_whitenoise_in_deps`** — proverava
   `pyproject.toml`. Dodavanjem deps u nepoznat order ne lomi se, ali Dev MORA
   koristiti `uv add` (ne ručan edit) da bi `uv.lock` ostao sinhron.

3. **`tests/test_static_tokens.py::test_ac8_django_check_passes`** —
   pokreće `manage.py check` sa novim settings-ima. Ako Dev preempt-ira ovaj
   test pre nego što `whitenoise` paket bude instaliran u .venv-u, dobija
   `ModuleNotFoundError: No module named 'whitenoise'`. Order: `uv add` →
   `just dev-build` (Docker) ili `uv sync` (host) → edit settings → run test.

4. **Roboto woff2 fajlovi su user-provided artifact** — Dev ne može sam preuzeti
   (gwfh.mranftl.com je external service). Testovi koji proveravaju woff2 file
   presence ili magic bytes **gracefully skip** sa porukom "Mihas mora ručno
   preuzeti woff2 fajlove pre Dev start-a" ako fajlovi ne postoje. Ovo nije
   regresija — to je pre-requisite handling.

## 5. Smoke validacija (post-implementation)

```bash
uv run python manage.py check
uv run python manage.py shell -c "from django.conf import settings; print(settings.STATICFILES_DIRS)"
uv run python manage.py shell -c "from django.conf import settings; print('whitenoise' in str(settings.MIDDLEWARE).lower())"
uv run python manage.py collectstatic --dry-run --noinput
uv run pytest tests/ apps/ -v  # → svi prolaze
```

## 6. Baseline brojanje testova (RED phase)

- `tests/test_static_tokens.py`: **50 testova** (organizovano po AC1-AC8 +
  anti-pattern guards; review iter 2 dodao `test_ac4_no_3digit_shorthand_hex`)
- **Stari testovi (Story 1.1-1.4):** 127 — moraju i dalje prolaziti (verifikovano
  da Story 1.5 settings izmene ne lome `tests/test_settings_split.py`)
- **RED očekivanje pre Dev-a:** 35 **fail**, 5 **vacuous pass** (anti-pattern
  guards koji su trivijalno tačni na pre-impl state-u: `whitenoise_not_in_installed_apps`,
  `django_check_passes`, `no_googleapis_reference_in_base_html`,
  `no_gstatic_reference_anywhere`, `no_preconnect_to_google`), 10 **skip**
  (4 woff2 fajlovi nedostaju + 3 tokens.css čeka Dev + 3 anti-pattern guards koji
  skip-uju ako fajlovi ne postoje + 1 forbidden-subdirs).

## 7. Open notes za Dev

- **STATIC_URL change u base.py** može pokrenuti istraživanje u
  `test_settings_split.py` — ovaj fajl trenutno NE testira STATIC_URL direktno
  (verifikovano u TEA review iter 2 — Grep za STATIC/STORAGES/MIDDLEWARE = 0
  match-eva), pa Story 1.4 amendment pattern NE TREBA primeniti. Ali Dev mora
  očekivati da `manage.py check` zavisi od instalacije Whitenoise paketa pre
  prvog testa.
- **`{% static %}` template tag** zahteva da `STATICFILES_DIRS` postoji na disku.
  Story 1.5 Task 2 kreira folder PRE Task 7 (settings izmena) — order matters.
- **KRITIČAN dep install order** (TEA review flag): Dev MORA prvo `uv add
  whitenoise>=6.8.0` PA TEK ONDA editovati `base.py` MIDDLEWARE. Razlog: ako se
  MIDDLEWARE update-uje pre nego što je whitenoise paket u .venv-u, sledeći
  `manage.py check` (ili pytest run) puca sa `ModuleNotFoundError: No module
  named 'whitenoise'`. Sekvenca: (1) `uv add whitenoise>=6.8.0` → (2) `just
  dev-build` (ili `uv sync` na host) → (3) edit `base.py` STORAGES + MIDDLEWARE
  → (4) edit per-env settings (`development.py`, `production.py`, `staging.py`)
  → (5) create static/ + tokens.css + base.html update → (6) `manage.py check`
  + pytest run.
- **DESIGN.md hex case** (TEA review flag): DESIGN.md frontmatter koristi
  uppercase hex (`#25402F`, `#00A4E9`). Story 1.5 AC4 mandate je **lowercase
  canonical** (`#25402f`, `#00a4e9`) — Dev MORA da konvertuje pri kopiranju
  iz DESIGN.md u `tokens.css`. Test `test_ac4_no_uppercase_hex` enforce-uje.
