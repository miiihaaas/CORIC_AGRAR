---
story-id: "1.6"
artifact: interface-contract
author: TEA (🧪)
created: 2026-05-28
status: red-phase
---

# Story 1.6 — Interface Contract (TEA RED phase)

Ovaj dokument definiše **interfejs kontrakt** (filesystem + Python API + render API)
za Story 1.6. Sve tačke su **testabilne** — TEA-ovi RED testovi (`tests/test_base_template.py`)
direktno verifikuju ovaj kontrakt. Dev MORA implementirati tačno ovo da bi testovi prošli GREEN.

Kontrakt je izveden iz story 1.6 AC1-AC9 + Dev Notes templates + Gotchas #1-19.

---

## 1. Filesystem kontrakt (Dev kreira ili menja)

| Path | Stanje pre 1.6 | Akcija | Min. sadržaj |
|---|---|---|---|
| `templates/base.html` | exists (24 lines, Story 1.5) | UPDATE | 50-80 lines; tokens.css PRVI link; expanded body sa skip link + main#main-content + aria-live + noscript + site-wide scripts |
| `config/settings/base.py` | exists (132 lines, Story 1.5) | UPDATE | INSTALLED_APPS += django_htmx, django_bootstrap5; MIDDLEWARE += HtmxMiddleware (POSLE Common, PRE LocaleSwitcher); BOOTSTRAP5 dict (CDN dev) |
| `config/settings/production.py` | exists (36 lines, Story 1.5) | UPDATE | BOOTSTRAP5 dict override sa local /static/vendor/ |
| `apps/core/templatetags/__init__.py` | does NOT exist | CREATE | empty file (or 1-line komentar) |
| `apps/core/templatetags/htmx_aria.py` | does NOT exist | CREATE | template.Library() sa `aria_live` simple_tag |
| `static/css/main.css` | does NOT exist | CREATE | placeholder (max 500 bytes) |
| `static/vendor/htmx.min.js` | does NOT exist | Mihas manual download | HTMX 1.9.12 pinned (~50KB) |
| `static/vendor/bootstrap-5.3.3/css/bootstrap.min.css` | does NOT exist | Mihas manual download | ~230KB |
| `static/vendor/bootstrap-5.3.3/js/bootstrap.bundle.min.js` | does NOT exist | Mihas manual download | ~80KB |

---

## 2. `config/settings/base.py` izmene

### 2.1 INSTALLED_APPS (after-state, mora biti tačno ovaj redosled)

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
    "apps.core",              # Story 1.4 — ostaje POSLEDNJI
]
```

Invarijante:
- `"django_htmx"` i `"django_bootstrap5"` su POSLE `"django.contrib.staticfiles"` i PRE `"apps.core"`.
- `"apps.core"` ostaje POSLEDNJI (Story 1.4 contract preserved).

### 2.2 MIDDLEWARE (after-state)

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
    "django_htmx.middleware.HtmxMiddleware",          # NOVO Story 1.6
    "apps.core.middleware.LocaleSwitcherMiddleware",   # POSLEDNJI (Story 1.4)
]
```

Invarijante:
- `HtmxMiddleware` mora biti POSLE `CommonMiddleware` i PRE `LocaleSwitcherMiddleware`
  (`idx(common) < idx(htmx) < idx(locale_switcher)`).
- `LocaleSwitcherMiddleware` ostaje POSLEDNJI.
- Sve ostale Story 1.4 + 1.5 middleware-i ostaju **NEPROMENJENI** (regression guard).

### 2.3 BOOTSTRAP5 dict (DEV variant, na kraju fajla)

```python
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

Invarijante:
- `BOOTSTRAP5["css_url"]["url"]` sadrži substring `cdn.jsdelivr.net/npm/bootstrap@5.3.3`.
- `BOOTSTRAP5["css_url"]["integrity"] is None` (Gotcha #19).
- `BOOTSTRAP5["javascript_url"]["integrity"] is None`.

## 3. `config/settings/production.py` izmene

```python
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

Invarijante (production override):
- `production.BOOTSTRAP5["css_url"]["url"].startswith("/static/vendor/bootstrap-5.3.3/")`.
- `production.BOOTSTRAP5["javascript_url"]["url"].startswith("/static/vendor/bootstrap-5.3.3/")`.
- Oba `integrity is None`.

---

## 4. `apps/core/templatetags/htmx_aria.py` Python API

```python
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def aria_live():
    return mark_safe(
        '<div id="aria-live" class="visually-hidden" '
        'aria-live="polite" aria-atomic="true"></div>'
    )
```

Invarijante:
- Modul je importable: `from apps.core.templatetags.htmx_aria import aria_live, register`.
- `register` je instanca `django.template.Library`.
- `aria_live` je registrovan tag (`"aria_live" in register.tags` ili Template render bez TemplateSyntaxError).
- `aria_live()` vraća string (SafeString) koji sadrži:
  - `id="aria-live"`
  - `class="visually-hidden"`
  - `aria-live="polite"`
  - `aria-atomic="true"`
  - tag je `<div>` (i `</div>`).
- Tag NEMA DB query (statički singleton emitter).

---

## 5. `templates/base.html` render kontrakt

### 5.1 Source-level invarijante

`templates/base.html` source MORA sadržati:

1. `<!DOCTYPE html>` (Story 1.5 preserved)
2. `{% load i18n %}` (Story 1.4 preserved)
3. `{% load static %}` (Story 1.5 preserved)
4. `{% load django_bootstrap5 %}` (NOVO)
5. `{% load htmx_aria %}` (NOVO)
6. `<html lang="{{ LANGUAGE_CODE }}">` (Story 1.4 preserved)
7. `<meta charset="UTF-8">` (preserved)
8. `<meta name="viewport" content="width=device-width, initial-scale=1.0">` (preserved)
9. `{% block meta_description %}{% endblock %}` unutar `<meta name="description" content="...">` (NOVO)
10. `<title>{% block title %}Ćorić Agrar{% endblock %}</title>` (preserved)
11. `<link rel="stylesheet" href="{% static 'css/tokens.css' %}">` ili sa double quotes (Story 1.5 PRESERVED — PRVI CSS link)
12. `{% bootstrap_css %}` (NOVO — POSLE tokens.css, PRE main.css)
13. `<link rel="stylesheet" href="{% static 'css/main.css' %}">` (NOVO — POSLE bootstrap_css)
14. `{% block extra_head %}{% endblock %}` (preserved)
15. `<a class="visually-hidden-focusable" href="#main-content">{% translate "Preskoči na sadržaj" %}</a>` (NOVO — PRVI element body-ja)
16. `<header>` sa `{% include "partials/language_switcher.html" %}` (preserved)
17. `<main id="main-content" tabindex="-1">` (MODIFIED — id i tabindex dodati)
18. `{% block content %}` ... `{% endblock %}` (preserved)
19. `</main>`
20. `{% aria_live %}` (NOVO — POSLE </main>, PRE noscript)
21. `<noscript>` blok sa Bootstrap alert (NOVO)
22. `<script src="{% static 'vendor/htmx.min.js' %}" defer></script>` (NOVO — site-wide, PRVI script)
23. `{% bootstrap_javascript %}` (NOVO — DRUGI script)
24. `{% block scripts %}{% endblock %}` (preserved, ali REORDERED — POSLE site-wide scripts)
25. `</body>`, `</html>` (preserved)

Source-level zabranjeno:
- `googleapis.com`, `gstatic.com` substring (anywhere)
- `cdn.jsdelivr.net` substring (literal URL u base.html source — jsDelivr je render-time samo)
- `unpkg.com`, `getbootstrap.com`, `htmx.org` literal URL substring
- Inline event handlers: `onclick=`, `onchange=`, `onload=` (CSP-readiness)
- Inline `<style>` blokovi
- Uppercase hex (`#[0-9A-F]{6}` sa bilo kojim uppercase A-F slovom)

Dužina fajla: **50-80 linija** (uključujući prazne linije i komentare).

### 5.2 Render-level invarijante (GET `/sr/` kroz Django test Client)

Response.content (decoded UTF-8) MORA sadržati:

- `<html lang="sr"` (Story 1.4 regression)
- `<link rel="stylesheet" href="/static/css/tokens.css">` (Story 1.5 regression)
- Bootstrap CSS link: regex match `(cdn\.jsdelivr\.net/npm/bootstrap@5\.3\.3.*bootstrap\.min\.css|/static/vendor/bootstrap-5\.3\.3/.*bootstrap\.min\.css)`.
- `<link rel="stylesheet" href="/static/css/main.css">`
- `<a class="visually-hidden-focusable" href="#main-content">` (skip link)
- `<main id="main-content" tabindex="-1">` (main landmark sa skip target)
- `<div id="aria-live" class="visually-hidden" aria-live="polite" aria-atomic="true"></div>` (ARIA live region)
- `<noscript>` blok
- `<script src="/static/vendor/htmx.min.js" defer>` (HTMX script — uvek local)
- Bootstrap JS script (regex CDN ili local).

Render-level zabranjeno:
- Sve iz § 5.1 source-level zabranjeno PLUS:
- `<script src="...googleapis.com..."` ili sličan tracking domain.

---

## 6. HtmxMiddleware behavior (request.htmx attribute)

```python
from django.test import RequestFactory
from django_htmx.middleware import HtmxMiddleware

rf = RequestFactory()
mw = HtmxMiddleware(lambda r: None)

# Plain request — falsy
r1 = rf.get("/")
mw(r1)
assert hasattr(r1, "htmx")
assert bool(r1.htmx) is False

# HTMX request — truthy
r2 = rf.get("/", HTTP_HX_REQUEST="true")
mw(r2)
assert bool(r2.htmx) is True
```

Story 1.6 NE MENJA bilo koji view — samo registruje middleware. `request.htmx` postaje dostupan globalno.

---

## 7. Out-of-scope (NE testira se u 1.6)

- Vizualne komponente (Story 1.7).
- Sticky nav + footer (Story 1.8).
- HTMX swap E2E (Story 2.8, 4.6).
- Lighthouse a11y automated audit (Story 1.9, 9.9).
- Playwright keyboard nav (Story 9.8).
- HTMX 2.x migracija (future story).

---

## 8. Regression invariants (Story 1.1-1.5 NE SME pasti)

- `test_bootstrap.py::test_ac3_installed_apps_is_default_django` — **MORA SE AMEND-OVATI** (current expects samo Django defaults + apps.core; Story 1.6 dodaje django_htmx + django_bootstrap5). Amendment je očekivana side-effect (kao Story 1.4 isti tip amendmenta) — Dev mora ažurirati taj test ili TEA mora pre-empt-ovati.
- Sva ostala `test_bootstrap.py` (uv/pyproject/justfile/skeleton) ostaju netaknuta.
- `test_i18n_setup.py` (Story 1.4) — sve ostaje GREEN (LocaleMiddleware position, language_switcher, set_language URL...).
- `test_static_tokens.py` (Story 1.5) — sve ostaje GREEN (tokens.css ostaje PRVI link; nove izmene base.html ne remetiti taj ordering).
- `apps/core/tests/*` — sve ostaje GREEN (Story 1.4 middleware + apps + translation).

Total baseline: 192 testova, 187 pass, 5 skip (woff2 nedostaje).

---

## 9. Test file kontrakt

TEA piše: `tests/test_base_template.py` (cross-cutting, source + settings + render layer).

Distribucija (~30-40 testova):
- AC1 base.html expansion: 12 testova
- AC2 skip link: 4 testa
- AC3 aria-live: 3 testa
- AC4 htmx_aria template tag: 4 testa
- AC5 settings (INSTALLED_APPS + MIDDLEWARE + BOOTSTRAP5): 8 testova
- AC6 request.htmx behavior: 2 testa
- AC7 HTMX vendor: 3 testa (mostly skip)
- AC8 main.css: 1 test
- AC9 smoke + render: 5 testova
- Anti-pattern guards: 3 testa

Sve fail-uje sada (RED phase). Dev implementira AC1-AC9 i sve postaje GREEN.

Pre-empted regression: `test_bootstrap.py::test_ac3_installed_apps_is_default_django` će puknuti čim Dev doda django_htmx + django_bootstrap5 — Dev ga ažurira (isti pattern kao Story 1.4 invariant supersession).
