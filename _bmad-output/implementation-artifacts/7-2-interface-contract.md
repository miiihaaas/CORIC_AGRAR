# Story 7.2 — Interface Contract (TEA RED phase, authoritative)

GDPR Banner sa Consent Management. EXTEND `apps/gdpr/` (7-1). **0 migracije, 0 novog dep-a, 0 context_processor (7-3 granica), 0 tracker (security granica).** Dev MORA zadovoljiti svaki potpis dole; testovi u `apps/gdpr/tests/` su izvršni contract.

---

## 1. Template tag — `apps/gdpr/templatetags/gdpr_banner.py` (NOVO)

```python
from django import template
from django.template.loader import render_to_string

register = template.Library()

@register.simple_tag(takes_context=True)
def gdpr_banner(context):
    request = context["request"]
    if "consent_state" in request.COOKIES:
        return ""                                   # presence-only suppression
    return render_to_string(
        "gdpr/_consent_banner.html",
        {"next": request.get_full_path()},          # dict SAMO {"next": ...}
        request=request,                            # KWARG → injektuje csrf_token / {% url %} / {% translate %} (G-1)
    )
```

- `simple_tag(takes_context=True)`; cita `context["request"].COOKIES`.
- Renderuje partial SAMO kad `"consent_state" NOT in request.COOKIES`; inace `""`.
- **Bilo koja prisutna vrednost** (uključujući garbage/forged) suzbija baner (NE parsira JSON — 7-3 parsira; SM-D2/Boundary).
- `request=request` kwarg je OBAVEZAN — bez njega `{% csrf_token %}` u partial-u ne radi → submit 403 (G-1).
- NOVI `apps/gdpr/templatetags/__init__.py` (package marker).

---

## 2. View — `apps/gdpr/views.py:SetConsentView` (EXTEND; zadrži `CookiePolicyView` netaknut)

```python
@method_decorator(ratelimit(key="ip", rate="10/m", block=False), name="dispatch")
class SetConsentView(View):
    http_method_names = ["post"]                     # GET → 405 (G-12)

    def post(self, request, *args, **kwargs):
        if getattr(request, "limited", False):
            return HttpResponse(status=429)          # NE 403 (block=False; G-6)
        ...
```

- **Ratelimit:** `@method_decorator(ratelimit(key="ip", rate="10/m", block=False), name="dispatch")` na **KLASI** (NIKAD goli `@ratelimit` na metodi — silent no-op na CBV; CRITICAL-2/G-6b) + `request.limited → 429` guard. KOPIRAJ logiku iz 4-6, NE reuse `htmx_form_endpoint` (vraca HTMX partial — pogresna semantika).
- **action parsing** (untrusted POST):
  - `accept_all` → `{"necessary": True, "analytical": True, "marketing": True}`
  - `reject_all` → `{"necessary": True, "analytical": False, "marketing": False}`
  - `save` → `necessary=True`; `analytical = "analytical" in request.POST`; `marketing = "marketing" in request.POST`
  - **nepoznata ILI nedostajuca action → default-deny** (== reject_all; NE crash/KeyError; G-15)
- **`necessary` SERVER-FORCED True** u SVAKOM ishodu — NE cita se iz POST-a (G-3; disabled checkbox se ionako ne salje, G-4). Tamper (`necessary=false` u POST-u) se ignoriše.
- **Cookie** `response.set_cookie("consent_state", json.dumps(consent), ...)`:
  - `max_age = 60*60*24*365` (`CONSENT_MAX_AGE` konstanta; 365d)
  - `samesite="Lax"`, `path="/"`, `httponly=False` (SM-D5; consent nije sensitive, buduce client-side OQ-2), `secure=settings.SESSION_COOKIE_SECURE` (settings-driven)
- **Redirect-back:** `HttpResponseRedirect(target, status=303)` (POST→GET semantika). Cookie se postavlja na taj redirect response.
- **Open-redirect guard** (`_safe_redirect(request)` helper; mirror 6-4 / seo/models.py:98):
  `url_has_allowed_host_and_scheme(url=next, allowed_hosts={request.get_host()}, require_https=request.is_secure())` → same-origin only; fallback `HTTP_REFERER` (isti guard) → `reverse("pages:home")`. Odbija `https://evil.com`, `//evil.com` (G-5).
- **CSRF MANDATORY** (CsrfViewMiddleware aktivan; form ima `{% csrf_token %}`).
- Importi: `json`, `settings`, `reverse`, `url_has_allowed_host_and_scheme` (django.utils.http), `method_decorator` (django.utils.decorators), `ratelimit` (django_ratelimit.decorators), `HttpResponse`, `HttpResponseRedirect`, `View`.

---

## 3. URL — `apps/gdpr/urls.py` (EXTEND)

```python
path("htmx/gdpr/consent/", SetConsentView.as_view(), name="set_consent")
```

- `reverse("gdpr:set_consent")` == `/sr/htmx/gdpr/consent/` (i18n_patterns, već u config/urls.py:49; SM-D6).
- `htmx/` prefiks, ASCII slug. `app_name = "gdpr"` zadržan.

---

## 4. Template — `templates/gdpr/_consent_banner.html` (NOVO)

- Root: `role="dialog"` + `aria-modal="false"` (NON-blokirajuci, NE focus-trap) + `aria-labelledby="<id>"` koji pokazuje na POSTOJECI heading `id` (npr. `<h2 id="coric-gdpr-banner-title">`) + `data-coric-gdpr-banner` JS hook + **`tabindex="-1"`** (za JS root-focus; AC7).
- `<form method="post" action="{% url 'gdpr:set_consent' %}">` + `{% csrf_token %}` + `<input type="hidden" name="next" value="{{ next }}">` (NIKAD `|safe`).
- **3 checkbox kategorije** (svaka sa `<label>`):
  - Neophodan: `checked` + `disabled`
  - Analitički: `name="analytical"` — **BEZ `checked`** (default odčekiran)
  - Marketing: `name="marketing"` — **BEZ `checked`** (default odčekiran)
- **3 submit dugmeta** `<button type="submit" name="action" value="...">`: `accept_all` / `reject_all` / `save`.
- **AC10 / equal-prominence:** „Prihvati sve" i „Odbij sve" oba `<button type="submit">` koji **dele istu osnovnu button-komponentnu klasu** (npr. `coric-gdpr-banner__action`); „Odbij sve" NIJE faint `<a>`/link. Razlika sme biti SAMO boja/akcenat.
- „Više info" `<a href="{% url 'gdpr:cookie_policy' %}">` (7-1 → `/sr/politika-kolacica/`).
- Sav UI tekst `{% translate %}` — pune dijakritike (Analitički / Više info / Sačuvaj izbor / kolačić ...).

---

## 5. JS — `static/js/gdpr-banner.js` (NOVO, EKSTERNI; NE inline)

- Vanilla IIFE `'use strict'` (mirror search-expand.js).
- On-show: fokus na baner **root** (`[data-coric-gdpr-banner]` ima `tabindex="-1"` → `.focus()`). Pinovan root-focus (NE prvo dugme).
- **Esc gate-ovan na focus-within-banner:** `if (event.key === "Escape" && banner.contains(document.activeElement)) { /* submit reject_all */ }` — NIKAD globalni `document` Esc (baner je non-modal i na svakoj strani → globalni Esc bi okidao reject iz search/forme; CRITICAL-4/G-14).
- **BEZ focus-trap** (`aria-modal="false"`; G-8).
- `prefers-reduced-motion` se rešava u CSS-u (JS ne forsira transform).
- Opciono `coric:consent-set` event na submit.
- **Progressive enhancement:** baner radi BEZ JS (plain form POST → server redirect-back). JS je SAMO a11y/UX sloj.
- Učitan `<script src="{% static 'js/gdpr-banner.js' %}" defer>`.

## 5b. CSS — `static/css/components/gdpr-banner.css` (NOVO) + `static/css/main.css` (EDIT)

- `.coric-gdpr-banner` BEM (`__title`/`__categories`/`__category`/`__actions`/`__more-info`); SAMO `var(--...)` tokeni; fixed-bottom non-blokirajuci; `@media (prefers-reduced-motion: reduce)`; `:focus-visible`; kontrast 4.5:1.
- Equal-prominence: oba action dugmeta isti tier/komponentna klasa (AC10/AC8).
- `@import url('./components/gdpr-banner.css');` u main.css (relative-with-dot; IMP-7).

---

## 6. Mount — `templates/base.html` (EDIT)

- `gdpr_banner` dodat u `{% load %}` (linija 2).
- `{% gdpr_banner %}` **IZMEĐU `{% include "partials/footer.html" %}` i `{% aria_live %}`** (pinovana pozicija; SM-D12).
- `<script src="{% static 'js/gdpr-banner.js' %}" defer></script>` u site-wide scripts blok (POSLE htmx/bootstrap, mirror sticky-nav.js).
- **7-2 NE render-uje NIJEDAN tracker** (gtag/fbq/google-analytics/googletagmanager/facebook) — to je 7-3 (G-10).

---

## 7. Dev — fajlovi koje kreira/menja

| Path | Tip |
|---|---|
| `apps/gdpr/templatetags/__init__.py` | NOVO |
| `apps/gdpr/templatetags/gdpr_banner.py` | NOVO |
| `apps/gdpr/views.py` | EDIT (+ SetConsentView; CookiePolicyView netaknut) |
| `apps/gdpr/urls.py` | EDIT (+ set_consent path) |
| `templates/gdpr/_consent_banner.html` | NOVO |
| `static/js/gdpr-banner.js` | NOVO |
| `static/css/components/gdpr-banner.css` | NOVO |
| `static/css/main.css` | EDIT (@import) |
| `templates/base.html` | EDIT (load + mount + script) |
| `locale/{sr,hu,en}/LC_MESSAGES/django.po` | EDIT (just messages) |

**NETAKNUTO:** `apps/gdpr/models.py` (0 migracije — `makemigrations --check --dry-run` MORA biti „No changes detected"), `apps/gdpr/views.py:CookiePolicyView`, `apps/forms/views.py:htmx_form_endpoint` (referenca, NE reuse), `apps/seo/models.py`, `config/urls.py`, `config/settings/base.py` context_processors (7-3), MIDDLEWARE.

---

## 8. Test contract (RED phase — `apps/gdpr/tests/`)

| Fajl | Pokriva |
|---|---|
| `test_gdpr_banner_tag.py` | AC1: render/empty/garbage-suppress, csrf-token, hidden next, Više-info |
| `test_set_consent_view.py` | AC2/AC3/AC4/AC5: accept/reject/save/default-deny, necessary-forced, cookie attrs, 303, open-redirect, 405, CSRF-403, ratelimit-429, url reverse |
| `test_consent_banner_template.py` | AC6/AC10: role/aria-modal/labelledby/tabindex, form/csrf, 3 kategorije, 3 akcije, equal-prominence, default-unchecked, Više-info, dijakritike |
| `test_banner_mount.py` | AC9: site-wide mount (`/sr/o-nama/`), absent-when-cookie, no-tracker, external JS |

**Dev napomene (test-coherence):**
- CSRF-negativni test koristi `csrf_client` fixture = `Client(enforce_csrf_checks=True)` (CRITICAL-1). Happy-path koristi standardni `client` (CSRF off).
- Ratelimit test REALNO šalje 11 POST-ova → 11. = 429 (hvata silent no-op CRITICAL-2). Autouse `_pin_and_clear_ratelimit_cache` fixture (conftest) radi `cache.clear()` pre/posle svakog gdpr testa.
- Mount integracija koristi **`/sr/o-nama/` (AboutView — staticka, bez DB fixtura)**, NE home (`/sr/` zahteva proizvod/brend seed).
- Puna Esc/fokus JS-runtime ponašanja su E2E (Playwright Epic 9.8) — pytest asertuje samo statički markup hooks (`data-coric-gdpr-banner`, `tabindex="-1"`) + eksterni script tag.
