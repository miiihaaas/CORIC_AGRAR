---
story_id: "7.2"
story-key: 7-2-gdpr-banner-sa-consent-management
title: GDPR Banner sa Consent Management
status: ready-for-dev
epic: 7
epic_num: 7
epic_title: GDPR & Privacy
module: gdpr
created: 2026-06-06
last_modified: 2026-06-06
complexity: M
author: Mihas (SM autonomous; DRUGA story Epic 7 — GDPR & Privacy. PROŠIRUJE postojeći apps/gdpr/ app (7-1). NOVI deliverable-i: apps/gdpr/templatetags/gdpr_banner.py:{% gdpr_banner %} simple_tag(takes_context=True) koji render-uje baner partial SAMO kad consent_state kolačić ODSUTAN u request.COOKIES (inače "") + apps/gdpr/views.py:SetConsentView (POST, CSRF mandatory) koja postavlja long-lived consent_state kolačić (365d) iz POST podataka (prihvati-sve → sve True; odbij-sve → samo necessary; podesi → per-checkbox) + redirect-back na same-origin next/referer (open-redirect guard url_has_allowed_host_and_scheme mirror 6-4) + templates/gdpr/_consent_banner.html partial (role="dialog"+aria-labelledby+aria-modal="false" NON-BLOKIRAJUĆI; 3 kategorije Neophodan[disabled+checked]/Analitički/Marketing; 3 akcije Prihvati sve/Odbij sve/Sačuvaj izbor; "Više info"→{% url 'gdpr:cookie_policy' %}) + static/js/gdpr-banner.js (vanilla IIFE EKSTERNI fajl NE inline; Esc=Odbij sve; fokus na baner on-show + return on-dismiss BEZ focus-trap jer aria-modal=false; prefers-reduced-motion; coric: events; PROGRESSIVE ENHANCEMENT — baner radi BEZ JS kroz plain form POST, JS samo enhancement) + static/css/components/gdpr-banner.css (@import u main.css; var(--...) tokeni + coric- BEM) + base.html mount {% gdpr_banner %} (POSLE footer, PRE/blizu {% aria_live %}) + i18n.po. consent_state kolačić: JSON {"necessary":true,"analytical":bool,"marketing":bool} (SM-D1); max_age=60*60*24*365; SameSite=Lax; Secure=settings.SESSION_COOKIE_SECURE (True u prod); httponly=False (SM-D5 — 7-3 čita server-side, ALI buduća "manage consent" re-open čita client-side da pre-checkuje toggle-ove → NE httponly); path=/. URL: POST endpoint /htmx/gdpr/consent/ name=gdpr:set_consent registrovan u apps/gdpr/urls.py UNUTAR i18n_patterns (mirror forms htmx/ prefiks — htmx/ pod locale prefiksom; SM-D6). RATELIMIT: @ratelimit key=ip rate=10/m block=False + request.limited→429 guard (SM-D7 — javan state-change POST; rate blaži od 5/m forma jer je low-risk + legitimno više klikova; NE reuse htmx_form_endpoint jer to vraća HTMX partial a consent NE koristi HTMX). 7-2↔7-3 GRANICA (SM-D8): 7-2 SAMO postavlja consent_state kolačić + render-uje baner; baner-tag čita request.COOKIES DIREKTNO (NE treba context_processor); 7-3 dodaje apps/gdpr/context_processors.py:consent_state (čita kolačić → request.consent_state) + conditional GA4/FB pixele. 7-2 NE kreira context_processor, NE učitava NIJEDAN tracker (security granica). NEMA MIGRACIJE (0 model promene). NEMA novog dep-a (django-ratelimit/Django prisutni). RISK TIER: MEDIUM-HIGH — state-change POST (CSRF+ratelimit+open-redirect-guard) + kolačić security atributi (SameSite/Secure/httponly/max_age semantika) + GDPR-consent korektnost (necessary uvek True NE može biti isključen; odbij-sve=default-deny) + a11y non-modal dialog (role/aria-labelledby/aria-modal=false/Esc/fokus/prefers-reduced-motion) + vanilla JS progressive-enhancement (radi BEZ JS). NEMA migracije/upload/auth.)
depends_on:
  - 7-1-cookiepolicy-model-admin                              # gdpr:cookie_policy ruta („Više info" link) + apps/gdpr/ app scaffolding (views.py/urls.py EXTEND); CookiePolicy.get_absolute_url
  - 4-6-htmx-form-patterns-aria-live-oob-rate-limiting        # POST/CSRF/ratelimit PATTERN (@ratelimit key=ip block=False + request.limited→429); _oob_aria_live PATTERN; htmx_form_endpoint (REFERENCA — NE reuse, SM-D7)
  - 4-2-kontakt-forma-model-i-htmx-submit                     # forms POST view + htmx/ URL prefiks PATTERN
  - 2-13-global-search-sa-postgresql-fts                      # search-expand.js JS KONVENCIJA (IIFE 'use strict' + Esc-to-close + fokus management + prefers-reduced-motion + coric: events + data-* atributi)
  - 1-8-sticky-nav-top-header-footer-language-switcher-partial # base.html chrome mount PATTERN (partials mount-ovani u base.html); footer/aria-live region
  - 6-4-redirect-manager-301                                  # url_has_allowed_host_and_scheme open-redirect guard PRESEDAN (apps/seo/models.py:98)
---

# Story 7.2: GDPR Banner sa Consent Management

Status: ready-for-dev

## Opis

As a **posetilac**,

I want **da se prikazuje GDPR baner sa opcijama prihvatanja kolačića (prihvati sve / odbij sve osim neophodnih / podesi po kategoriji), sa izborom koji se trajno čuva u `consent_state` kolačiću (365 dana), pristupačan tastaturom i screen reader-om (non-blokirajući dijalog), sa „Više info" linkom ka politici kolačića**,

so that **kontrolišem koje kolačiće dozvoljavam pre nego što sajt aktivira bilo kakav tracking**.

Ovo je **DRUGA story Epic 7 (GDPR & Privacy)** i predstavlja **CONSENT BOUNDARY**: 7-2 **POSTAVLJA** `consent_state` kolačić i prikazuje baner pri prvoj poseti; **7-3** će **ČITATI** taj kolačić (kroz `apps/gdpr/context_processors.py:consent_state`) i uslovno render-ovati GA4/FB pixele. 7-2 **NE učitava NIJEDAN tracker** — to je security granica epika. PROŠIRUJE postojeći `apps/gdpr/` app iz 7-1 (`views.py` + `urls.py`); dodaje template tag, baner partial, vanilla JS, CSS, i mount u `base.html`. **NEMA model promene → NEMA migracije.**

### IN SCOPE (šta ova story isporučuje)

1. **`apps/gdpr/templatetags/gdpr_banner.py:{% gdpr_banner %}`** (SM-D2) — `simple_tag(takes_context=True)` koji čita `context["request"].COOKIES`; render-uje baner partial (`templates/gdpr/_consent_banner.html`) SAMO kad je `consent_state` kolačić **ODSUTAN**; vraća `""` (prazan string) kad je prisutan. NOVI direktorijum `apps/gdpr/templatetags/` + `__init__.py`.
2. **`apps/gdpr/views.py:SetConsentView`** (EXTEND postojeći `views.py`; SM-D3/D7) — POST-only state-change view. Postavlja `consent_state` kolačić iz POST podataka:
   - **Prihvati sve** (`action=accept_all`) → `{"necessary": true, "analytical": true, "marketing": true}`
   - **Odbij sve** (`action=reject_all`) → `{"necessary": true, "analytical": false, "marketing": false}` (default-deny; `necessary` UVEK `true`)
   - **Podesi / Sačuvaj izbor** (`action=save`) → `necessary` UVEK `true`; `analytical`/`marketing` iz checkbox-a (`"analytical" in request.POST` itd.)
   - **Nepoznata / nedostajuća `action`** → default-deny (kao `reject_all`: samo `necessary` True); NE crash/KeyError (G-15).
   - CSRF MANDATORY (state-change POST; `{% csrf_token %}` u baner formi); django CSRF middleware aktivan.
   - `@ratelimit(key="ip", rate="10/m", block=False)` + `request.limited → HttpResponse(status=429)` guard (SM-D7).
   - Vraća **redirect-back** (HTTP 303 See Other — POST→GET semantika) na same-origin `next` (POST param) ili `HTTP_REFERER`, sa fallback-om na `reverse("pages:home")`; **open-redirect guard** `url_has_allowed_host_and_scheme(...)` (SM-D9, mirror 6-4). Cookie se postavlja na taj redirect response.
3. **`apps/gdpr/urls.py`** (EXTEND) — `path("htmx/gdpr/consent/", SetConsentView.as_view(), name="set_consent")` (SM-D6 — `htmx/` prefiks konvencija; ostaje u `i18n_patterns` kao 7-1, pa stvarni URL je `/sr/htmx/gdpr/consent/`).
4. **`templates/gdpr/_consent_banner.html`** (SM-D4) — baner partial; `role="dialog"` + `aria-labelledby` (pokazuje na heading `id`) + `aria-modal="false"` (**NON-blokirajući** — stranica ostaje upotrebljiva). Sadrži:
   - `<form method="post" action="{% url 'gdpr:set_consent' %}">` sa `{% csrf_token %}` + hidden `next` = trenutni path (za redirect-back bez JS).
   - 3 kategorije kao checkbox-i: **Neophodan** (`checked` + `disabled` — uvek-uključen, ne može da se isključi; takođe hidden input da vrednost stigne iako je disabled NIJE potrebno jer server uvek forsira `necessary=true`), **Analitički** (`name="analytical"`), **Marketing** (`name="marketing"`).
   - 3 dugmeta (submit): **Prihvati sve** (`name="action" value="accept_all"`), **Odbij sve** (`name="action" value="reject_all"`), **Sačuvaj izbor** (`name="action" value="save"`).
   - **„Više info"** link → `{% url 'gdpr:cookie_policy' %}` (7-1 ruta).
   - Sav UI tekst `{% translate %}` pune dijakritike.
5. **`static/js/gdpr-banner.js`** (SM-D10 — vanilla IIFE EKSTERNI fajl, **NE inline**) — progressive enhancement: Esc = trigger „Odbij sve" submit; fokus na baner on-show + return on-dismiss (BEZ focus-trap jer `aria-modal="false"`); `prefers-reduced-motion` respect (CSS-driven slide-in, JS ne forsira transform); opciono `coric:consent-set` event. Baner MORA raditi BEZ JS (plain form POST → server redirect-back).
6. **`static/css/components/gdpr-banner.css`** (SM-D11) — `@import` u `main.css`; `.coric-gdpr-banner` BEM + `var(--...)` tokeni (BEZ magic vrednosti); fixed-bottom non-blokirajući layout; `prefers-reduced-motion` media query; focus-visible; kontrast 4.5:1.
7. **`templates/base.html`** (EDIT) — mount `{% gdpr_banner %}` (load `gdpr_banner` tag lib) **IZMEĐU `{% include "partials/footer.html" %}` i `{% aria_live %}`** (POSLE footer-a, NEPOSREDNO PRE aria-live regiona — pinovana pozicija; SM-D12).
8. **i18n** — nove UI string-ove dodati u `locale/*/LC_MESSAGES/django.po` (`just messages`).

### OUT OF SCOPE (eksplicitno — granice)

- **GA4 + FB Pixel tracking pixeli + `apps/gdpr/context_processors.py:consent_state` + `request.consent_state`** = **Story 7.3** (epics.md:1024). **7-2 NE kreira context_processor** — baner tag čita `request.COOKIES["consent_state"]` DIREKTNO (baner se prikazuje SAMO kad kolačić ODSUTAN, pa nema potrebe za parsiranjem). 7-3 dodaje context_processor (parsira JSON → `request.consent_state` dict) + uslovni render pixela (SM-D8). **7-2 NE učitava NIJEDAN tracker** (security granica).
- **`apps/gdpr/middleware.py:GdprConsentMiddleware`** (architecture.md:767 ga pominje kao buduću opciju) = **NE u 7-2**. 7-3 može da bira context_processor (preporuka — jednostavnije) ili middleware; 7-2 ne kreira nijedan (SM-D8).
- **„Manage consent" / re-open baner-a posle prvog izbora** (npr. dugme u footeru „Podešavanja kolačića") = **deferred** (OQ-2). 7-2 baner se prikazuje SAMO kad kolačić ODSUTAN; posle izbora više se ne prikazuje. Re-open UI (sa pre-check-ovanim toggle-ovima iz postojećeg kolačića) je budući polish. `httponly=False` je već postavljen (SM-D5) tako da budući re-open može da čita kolačić client-side bez promene back-end-a.
- **Politika privatnosti strana + footer linkovi** = **Story 7.4**. 7-2 baner linkuje SAMO na `gdpr:cookie_policy` (7-1).
- **Verzionisanje consent zapisa / audit log ko-je-kad-pristao** = **deferred** (OQ-3; v1 čuva samo trenutno stanje u kolačiću, NEMA server-side consent record).
- **NEMA model promene → NEMA migracije.** `consent_state` je kolačić (client-side), NE DB red.
- **Defensive validacija za nemoguće slučajeve** (project-context.md:358) — NE. `next`/referer validacija JESTE security boundary (open-redirect — validira se), ali NEMA suvišnih `if request is None` guard-ova na internim pozivima.

### Princip

PROŠIRUJE `apps/gdpr/` app (7-1): NOVI `{% gdpr_banner %}` template tag (`simple_tag(takes_context=True)`, render baner partial SAMO kad `consent_state` kolačić odsutan) + `SetConsentView` (POST, CSRF mandatory, `@ratelimit` 10/m, postavlja `consent_state` JSON kolačić 365d sa SameSite=Lax/Secure-settings-driven/httponly=False/path=/, redirect-back na same-origin sa open-redirect guard) + baner partial (`role="dialog"`/`aria-labelledby`/`aria-modal="false"` non-blokirajući; 3 kategorije Neophodan-disabled-checked/Analitički/Marketing; 3 akcije; „Više info"→`gdpr:cookie_policy`) + vanilla JS EKSTERNI fajl (Esc=Odbij-sve, fokus management bez focus-trap, prefers-reduced-motion, progressive-enhancement BEZ-JS-radi) + CSS tokeni+BEM + mount u base.html. **`necessary` UVEK True** (ne može da se isključi); **odbij-sve = default-deny**. 7-2↔7-3 granica: 7-2 postavlja, 7-3 čita (context_processor + pixeli). **7-2 NE učitava tracker.** Pune dijakritike u UI tekstu; ASCII u URL slug-u (`htmx/gdpr/consent/`). NEMA migracije. NEMA novog dep-a. NEMA context_processor (7-3). NEMA defensive validacije.

### Strukturna arhitektura — repository delta

**EXTEND postojeći `apps/gdpr/` app: 2 EDIT (`views.py` + `urls.py`) + 3 NOVO (templatetags + JS + CSS) + 1 NOVI template + 1 base.html EDIT + 1 main.css EDIT + .po; 0 migracije; 0 DELETE; 0 novog dep-a.**

| Path | Tip | Razlog |
|---|---|---|
| `apps/gdpr/templatetags/__init__.py` | NOVO | Package marker (NOVI templatetags dir u gdpr app-u). |
| `apps/gdpr/templatetags/gdpr_banner.py` | NOVO | `register.simple_tag(takes_context=True) def gdpr_banner(context)`: `request = context["request"]`; ako `"consent_state" in request.COOKIES` → `return ""`; inače `return render_to_string("gdpr/_consent_banner.html", {"next": request.get_full_path()}, request=request)`. **KANONIČNI oblik:** eksplicitni dict sadrži SAMO `{"next": request.get_full_path()}`; `request=request` (KWARG, NE u dict-u) je ono što injektuje `csrf_token` + `{% url %}` i18n + `{% translate %}` u partial context — `"request"` se NE dodaje redundantno u dict (G-1). (SM-D2; vidi AC1.) |
| `apps/gdpr/views.py` | EDIT | DODAJ `SetConsentView(View)` (POST-only). **Ratelimit MORA biti `@method_decorator(ratelimit(key="ip", rate="10/m", block=False), name="dispatch")` na KLASI** (NE goli `@ratelimit` na `post`/`dispatch` metodi — `django_ratelimit.decorators.ratelimit` je FUNKCIJSKI dekorator i primenjen direktno na CBV metodu SILENTLY NO-OP-uje → rate-limit se NE primeni; CRITICAL-2). `post`: `if getattr(request, "limited", False): return HttpResponse(status=429)` guard → parse `action` → izgradi `consent` dict (`necessary` UVEK True) → `_safe_redirect(request)` (open-redirect-guard helper) → `response.set_cookie("consent_state", json.dumps(consent), max_age=CONSENT_MAX_AGE, samesite="Lax", secure=settings.SESSION_COOKIE_SECURE, httponly=False, path="/")` → return. `CONSENT_MAX_AGE = 60*60*24*365`. Import `json`, `settings`, `reverse`, `url_has_allowed_host_and_scheme`, `method_decorator` (`django.utils.decorators`), `ratelimit`, `HttpResponse`, `HttpResponseRedirect`. **Zadrži postojeći `CookiePolicyView` netaknut.** (SM-D3/D7/D9; vidi AC2/AC3/AC4.) |
| `apps/gdpr/urls.py` | EDIT | DODAJ `path("htmx/gdpr/consent/", SetConsentView.as_view(), name="set_consent")` u `urlpatterns`. Import `SetConsentView`. Ostaje u `i18n_patterns` (config/urls.py:49 već uključuje `apps.gdpr.urls`) → `/sr/htmx/gdpr/consent/`. (SM-D6; vidi AC5.) |
| `templates/gdpr/_consent_banner.html` | NOVO | Baner partial. `role="dialog"` + `aria-labelledby="coric-gdpr-banner-title"` + `aria-modal="false"`. Heading `<h2 id="coric-gdpr-banner-title">`. `<form method="post" action="{% url 'gdpr:set_consent' %}">` + `{% csrf_token %}` + `<input type="hidden" name="next" value="{{ next }}">`. 3 checkbox kategorije (Neophodan `checked disabled`, Analitički `name="analytical"`, Marketing `name="marketing"`). 3 submit dugmeta (`name="action"` values `accept_all`/`reject_all`/`save`). „Više info" `<a href="{% url 'gdpr:cookie_policy' %}">`. `data-coric-gdpr-banner` root atribut (JS hook). Pune dijakritike, `{% translate %}`. (SM-D4; vidi AC6.) |
| `static/js/gdpr-banner.js` | NOVO | Vanilla IIFE `'use strict'` (mirror search-expand.js). On-load: ako baner u DOM-u → fokus na baner **root** (`[data-coric-gdpr-banner]` ima `tabindex="-1"` u template-u → `.focus()` radi; pinovan root-focus, NE prvo dugme); **Esc handler MORA biti gate-ovan na focus-within-banner** (`if (banner.contains(document.activeElement)) { ... submit reject_all }`) — NE globalno dok je baner samo prisutan (baner je non-modal i na svakoj strani → globalni Esc bi okinuo „Odbij sve" iz search-box-a/forme; CRITICAL-4). on-submit opciono dispatch `coric:consent-set`. BEZ focus-trap (aria-modal=false). `prefers-reduced-motion` se respektuje kroz CSS (JS ne forsira animaciju). NE inline (CSP-readiness + project konvencija). Učitan `defer` u base.html. (SM-D10; vidi AC7.) |
| `static/css/components/gdpr-banner.css` | NOVO | `.coric-gdpr-banner` (fixed bottom, non-blokirajući, z-index iznad sadržaja ALI page scroll-abilan), `__title`/`__categories`/`__category`/`__actions`/`__more-info` BEM. SAMO `var(--...)` tokeni (boja/spacing/rounded/shadow/typography). `@media (prefers-reduced-motion: reduce)` — instant (bez slide-in transform). `:focus-visible` vidljiv. Kontrast 4.5:1. (SM-D11; vidi AC8.) |
| `static/css/main.css` | EDIT | DODAJ `@import url('./components/gdpr-banner.css');` (relative-with-dot syntax MANDATORY — IMP-7; mirror postojeći @import-i). |
| `templates/base.html` | EDIT | DODAJ `gdpr_banner` u `{% load %}` (linija 2) + `{% gdpr_banner %}` **IZMEĐU `{% include "partials/footer.html" %}` i `{% aria_live %}`** (tj. POSLE footer-a, NEPOSREDNO PRE aria-live regiona — pinovana pozicija, SM-D12) + `<script src="{% static 'js/gdpr-banner.js' %}" defer></script>` u site-wide scripts blok (POSLE htmx/bootstrap, mirror sticky-nav.js linija 37). |
| `locale/{sr,hu,en}/LC_MESSAGES/django.po` | EDIT | `just messages` ekstraktuje nove `{% translate %}` string-ove. sr pune dijakritike. |
| `apps/gdpr/tests/*` | NOVO (TEA) | RED-phase testovi (vidi Testing). Dodaj `test_gdpr_banner_tag.py` + `test_set_consent_view.py` + `test_consent_banner_template.py` + `test_banner_mount.py` (integration: base.html mount + no-tracker) u `apps/gdpr/tests/`. |
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | EDIT | `7-2-gdpr-banner-sa-consent-management` → `ready-for-dev`. SM handoff tracking (NIJE deliverable). |

**NETAKNUTO (regression guards):** `apps/gdpr/models.py` (CookiePolicy — 7-2 ne dira model; NEMA migracije); `apps/gdpr/views.py:CookiePolicyView` (zadržati netaknut — SAMO dodati SetConsentView); `apps/gdpr/admin.py`/`translation.py` (ne diraju se); `apps/forms/views.py:htmx_form_endpoint` (REFERENCA pattern-a, NE menja se i NE reuse-uje se — SM-D7); `apps/seo/models.py` (`url_has_allowed_host_and_scheme` presedan — NE menja se, samo MIRROR-uje se import); `templates/partials/footer.html` (footer link „Podešavanja kolačića" = OUT OF SCOPE OQ-2; NE dira se); `config/urls.py` (već uključuje `apps.gdpr.urls` od 7-1 — `path("htmx/gdpr/consent/")` se dodaje u `apps/gdpr/urls.py`, NE u config/urls.py); `config/settings/base.py` context_processors (7-3 dodaje consent_state, NE 7-2); MIDDLEWARE (NE dodaje se GdprConsentMiddleware). **KRITIČNO:** `makemigrations --check --dry-run` posle 7-2 → „No changes detected" (0 model promene).

### Boundary tabela (7-2 ↔ 7-3 — eksplicitno za 7-3 dev-a)

| Odgovornost | Vlasnik | Pravilo |
|---|---|---|
| Postavlja `consent_state` kolačić | **7-2 (`SetConsentView`)** | 7-3 NE postavlja kolačić — samo ga čita. |
| Prikazuje GDPR baner | **7-2 (`{% gdpr_banner %}`)** | Baner tag čita `request.COOKIES` DIREKTNO (kolačić odsutan → render). |
| Čita `consent_state` → `request.consent_state` | **7-3 (`context_processors.py:consent_state`)** | 7-2 NE kreira context_processor (baner se prikazuje samo kad kolačić odsutan; nema potrebe parsirati). |
| Uslovni render GA4/FB pixela | **7-3 (`templatetags/tracking.py`)** | 7-2 NE učitava NIJEDAN tracker (security granica). |
| Malformed/stari/forged `consent_state` (npr. `consent_state=garbage`) | **7-2 suzbija re-prompt na PRISUSTVU; 7-3 mora bezbedno parsirati** | 7-2 baner-tag suzbija baner SAMO na PRISUSTVU kolačića (`"consent_state" in request.COOKIES`), pa bilo koja prisutna vrednost (i neispravna) trajno krije baner. **CONTRACT za 7-3: svaki prisutan-ali-neparsabilan `consent_state` (npr. `json.loads` baci grešku ili nije očekivana šema) MORA se tretirati kao pun DENY (`{necessary:true, analytical:false, marketing:false}`) — NE crash, NE default-allow.** Prisustvo samo suzbija re-prompt u 7-2; 7-3 nosi parsiranje + default-deny na grešci. (7-2 NE dodaje parsiranje.) |

## Kriterijumi prihvatanja

**AC1 — `{% gdpr_banner %}` tag render-uje baner SAMO kad `consent_state` kolačić ODSUTAN; inače `""` (SM-D2)**

- **Given** NOVI `apps/gdpr/templatetags/gdpr_banner.py`; `request` u context-u (base.py:82 `request` context_processor)
- **When** template render-uje `{% gdpr_banner %}`
- **Then**:
  - `simple_tag(takes_context=True)`; čita `context["request"].COOKIES`
  - `"consent_state" NOT in request.COOKIES` → render-uje `templates/gdpr/_consent_banner.html` (kroz `render_to_string(..., request=request)` da `csrf_token`/`request` budu u partial context-u)
  - `"consent_state" in request.COOKIES` → vraća `""` (baner se NE prikazuje — bilo koja vrednost kolačića znači da je posetilac već izabrao)
  - tag se učitava sa `{% load gdpr_banner %}`
- **And** `uv run python manage.py check` exit 0

**AC2 — `SetConsentView` POST „Prihvati sve" → kolačić `{necessary,analytical,marketing}` svi True, 365d, ispravni atributi (SM-D3)**

- **Given** `SetConsentView` na `gdpr:set_consent`; CSRF token validan
- **When** POST `action=accept_all` (sa CSRF token-om)
- **Then**:
  - response postavlja `consent_state` kolačić = `json.dumps({"necessary": true, "analytical": true, "marketing": true})`
  - `max_age == 60*60*24*365` (365 dana)
  - `samesite == "Lax"`, `path == "/"`, `httponly == False` (SM-D5), `secure == settings.SESSION_COOKIE_SECURE` (False u dev/test, True u prod)
  - response je redirect (HTTP 303 ili 302 — SM-D3 preporuka 303)
- **And** posle ovog POST-a, sledeći GET sa tim kolačićem → `{% gdpr_banner %}` vraća `""` (baner nestaje)

**AC3 — „Odbij sve" → samo `necessary` True (default-deny); „Podesi/Sačuvaj" → per-checkbox; `necessary` UVEK True (SM-D3)**

- **Given** AC2
- **When**:
  - POST `action=reject_all` → kolačić `{"necessary": true, "analytical": false, "marketing": false}`
  - POST `action=save` SA `analytical` checkbox-om (`marketing` izostavljen) → `{"necessary": true, "analytical": true, "marketing": false}`
  - POST `action=save` BEZ ijednog checkbox-a → `{"necessary": true, "analytical": false, "marketing": false}`
- **Then**:
  - `necessary` je UVEK `true` u SVAKOM ishodu (neophodni kolačići se ne mogu isključiti; server forsira `necessary=True`, NE čita iz POST-a)
  - `analytical`/`marketing` reflektuju prisustvo checkbox imena u `request.POST` (`"analytical" in request.POST`)

**AC4 — CSRF MANDATORY: POST bez tokena → 403; ratelimit 10/m → 429; redirect-back same-origin sa open-redirect guard (SM-D7/D9)**

- **Given** AC2; Django CSRF middleware aktivan (base.py:65); ratelimit primenjen kao `@method_decorator(ratelimit(key="ip", rate="10/m", block=False), name="dispatch")` na KLASI (NE goli dekorator na metodi — CRITICAL-2) + `request.limited → 429` guard u `post`
- **When**:
  - POST BEZ CSRF token-a (test koristi `Client(enforce_csrf_checks=True)` — NE default klijent koji isključuje CSRF; CRITICAL-1) → **HTTP 403** (CsrfViewMiddleware odbija)
  - 11. POST u minuti sa istog IP-a → **HTTP 429** (`request.limited`; NE 403 — `block=False`, mirror 4-6 SM-D9)
  - POST sa `next=/sr/proizvodi/` (same-origin) → redirect na `/sr/proizvodi/`
  - POST sa `next=https://evil.com/` (cross-origin) → redirect NE ide na evil.com (open-redirect guard `url_has_allowed_host_and_scheme(url=next, allowed_hosts={request.get_host()}, require_https=request.is_secure())` → fallback na `HTTP_REFERER` ako same-origin, inače `reverse("pages:home")`)
  - POST bez `next` i bez `referer` → redirect na `reverse("pages:home")`
- **Then**: open-redirect je nemoguć; kolačić se postavlja na SVIM validnim redirect ishodima
- **And** GET na `gdpr:set_consent` → **HTTP 405** (POST-only — `http_method_names=["post"]` ili `View.post` only)

**AC5 — URL `gdpr:set_consent` na `htmx/gdpr/consent/` u i18n_patterns (SM-D6)**

- **Given** `apps/gdpr/urls.py` (EXTEND); config/urls.py:49 već uključuje `apps.gdpr.urls` u `i18n_patterns`
- **When** dodam `path("htmx/gdpr/consent/", SetConsentView.as_view(), name="set_consent")`
- **Then**:
  - `reverse("gdpr:set_consent")` → `/sr/htmx/gdpr/consent/` (locale-prefiksovan, mirror 7-1 cookie_policy)
  - `htmx/` prefiks ASCII (mirror forms `htmx/forme/...`)
  - `app_name = "gdpr"` zadržan (već postoji)
- **And** `uv run python manage.py check` exit 0

**AC6 — Baner partial a11y: `role="dialog"` + `aria-labelledby` + `aria-modal="false"` + 3 kategorije + 3 akcije + „Više info" (SM-D4)**

- **Given** NOVI `templates/gdpr/_consent_banner.html`
- **When** baner se render-uje (kolačić odsutan)
- **Then**:
  - root element ima `role="dialog"`, `aria-modal="false"` (**NON-blokirajući** — page ostaje upotrebljiv, NIJE focus-trap), `aria-labelledby` koji POKAZUJE na `id` heading-a (taj `id` POSTOJI u markup-u), `data-coric-gdpr-banner` hook + **`tabindex="-1"`** (da JS root-focus radi; AC7)
  - `<form method="post" action="{% url 'gdpr:set_consent' %}">` SA `{% csrf_token %}` (token PRISUTAN u render-ovanom HTML-u) + hidden `next` input
  - 3 checkbox kategorije: **Neophodan** (`checked` + `disabled` — uvek-uključen), **Analitički** (`name="analytical"`, **BEZ `checked` — podrazumevano odčekiran**), **Marketing** (`name="marketing"`, **BEZ `checked` — podrazumevano odčekiran**) — svaki sa `<label>` (keyboard/screen-reader-friendly). Nema pre-ticked ne-neophodnih kategorija (GDPR; AC10/CRITICAL-3).
  - 3 submit dugmeta: **Prihvati sve**, **Odbij sve**, **Sačuvaj izbor** (svaki `<button type="submit" name="action" value="...">`, tab-focusable). **„Odbij sve" i „Prihvati sve" dele isti dugme-tier/komponentnu klasu (jednaka prominentnost — AC10/CRITICAL-3); „Odbij sve" NIJE faint link.**
  - **„Više info"** `<a href="{% url 'gdpr:cookie_policy' %}">` (7-1 ruta) — `href` se rezolvuje na `/sr/politika-kolacica/`
  - SAV UI tekst pune dijakritike (č/ć/ž/š/đ) kroz `{% translate %}`
- **And** baner radi BEZ JS (plain form POST → server postavlja kolačić + redirect-back)

**AC7 — Vanilla JS `gdpr-banner.js` (EKSTERNI fajl): Esc=Odbij-sve, fokus on-show/return, prefers-reduced-motion, progressive enhancement (SM-D10)**

- **Given** NOVI `static/js/gdpr-banner.js`; baner u DOM-u
- **When** JS se učita (`defer`)
- **Then**:
  - IIFE `'use strict'` (mirror search-expand.js konvencija)
  - on-show: fokus na baner **root** (`[data-coric-gdpr-banner]` ima `tabindex="-1"` u template-u → JS `.focus()` na root radi). Pinovan ROOT-focus pattern (NE prvo dugme — uklonjena ranija dvosmislenost). Baner ostaje non-modal, BEZ focus-trap.
  - Esc taster **SAMO kad je fokus UNUTAR banera** (`banner.contains(document.activeElement)` — NE globalno na `document` dok je baner samo prisutan) → trigger „Odbij sve" submit (`form` sa `action=reject_all`). KRITIČNO: baner je non-modal i prisutan na SVAKOJ strani dok consent nije postavljen — globalni Esc bi okinuo „Odbij sve" kad korisnik pritisne Esc u search box-u / kontakt formi / bilo kom polju (CRITICAL-4). Zato se Esc gate-uje na focus-within-banner.
  - **BEZ focus-trap** (aria-modal=false — fokus sme da napusti baner; stranica je upotrebljiva)
  - `prefers-reduced-motion` respektovan kroz CSS (JS NE forsira transform/animaciju)
  - opciono `coric:consent-set` custom event na submit
  - **PROGRESSIVE ENHANCEMENT:** ako JS ne postoji/ne radi, plain form POST i dalje postavlja kolačić (AC2) — JS je SAMO a11y/UX enhancement
- **And** JS je EKSTERNI fajl učitan kroz `<script src=... defer>` (NE inline — CSP-readiness + project konvencija)

**AC8 — Baner CSS: tokeni + coric- BEM + prefers-reduced-motion + kontrast (SM-D11)**

- **Given** NOVI `static/css/components/gdpr-banner.css` `@import`-ovan u main.css
- **When** baner se stiluje
- **Then**:
  - `.coric-gdpr-banner` + `__title`/`__categories`/`__category`/`__actions`/`__more-info` BEM (coric- prefiks)
  - SAMO `var(--...)` tokeni (boja/spacing/rounded/shadow/typography) — BEZ magic hex/px vrednosti
  - non-blokirajući layout (fixed bottom; page scroll radi; NE full-screen overlay koji blokira interakciju)
  - `@media (prefers-reduced-motion: reduce)` — bez slide-in transform/animacije
  - `:focus-visible` vidljiv na dugmićima/checkbox-ima/linku; kontrast 4.5:1
  - **„Odbij sve" i „Prihvati sve" stilizovani sa JEDNAKOM prominentnošću** (ista button-komponentna klasa/veličina/font-weight/padding; razlika SAMO u boji/akcentu) — NE jedno bold primary CTA + drugo izbledelo (GDPR; AC10/CRITICAL-3)

**AC9 — `{% gdpr_banner %}` mount-ovan u base.html (site-wide, uslovno); 7-2 NE učitava tracker (SM-D8/D12)**

- **Given** `base.html` (EDIT)
- **When** dodam `{% gdpr_banner %}` (IZMEĐU `{% include "partials/footer.html" %}` i `{% aria_live %}` — POSLE footer, NEPOSREDNO PRE aria-live) + `gdpr_banner` u `{% load %}` + JS script tag
- **Then**:
  - SVAKA strana koja extend-uje base.html prikazuje baner kad `consent_state` kolačić ODSUTAN; NE prikazuje kad prisutan (AC1)
  - **7-2 NE render-uje NIJEDAN GA4/FB/tracking script** (verify: response sadrži baner, ALI NE sadrži `googletagmanager`/`google-analytics`/`facebook`/`fbq`/`gtag` reference) — tracking je 7-3
  - 7-2 NE kreira `apps/gdpr/context_processors.py` ni `request.consent_state` (7-3 granica)
- **And** `uv run python manage.py check` exit 0; `makemigrations --check --dry-run` → „No changes detected"

**AC10 — GDPR validnost consent-a: „Odbij sve" jednako prominentno kao „Prihvati sve"; opcioni checkbox-i podrazumevano ODČEKIRANI (CRITICAL-3)**

GDPR (EDPB Guidelines 05/2020) zahteva da je ODBIJANJE consent-a jednako lako/prominentno kao PRIHVATANJE, i da NIJEDAN ne-neophodni checkbox NIJE unapred čekiran (nema pre-ticked boxes). Bez ovoga je consent pravno NEVALIDAN čak i ako svi ostali AC-ovi prođu.

- **Given** baner partial + CSS
- **When** baner se render-uje
- **Then**:
  - **„Odbij sve" i „Prihvati sve" imaju JEDNAKU vizuelnu prominentnost** — isti tier dugmeta (ista komponenta-klasa/veličina/font-weight/visina), NE jedno kao bold primarni CTA a drugo kao izbledeli sekundarni link. Oba dele istu osnovnu CSS button-komponentnu klasu (npr. oba `.coric-gdpr-banner__action`); razlika sme biti SAMO u boji/akcentu, NIKAD u veličini/težini/tipu (link vs dugme). „Odbij sve" je `<button type="submit">`, NE `<a>` ili faint link.
  - **„Analitički" i „Marketing" checkbox-i su podrazumevano ODČEKIRANI** (BEZ `checked` atributa) — samo „Neophodan" je `checked` (i `disabled`). Nema pre-ticked ne-neophodnih kategorija.
- **And** testabilno: „Prihvati sve" i „Odbij sve" dele istu osnovnu button-komponentnu klasu (assertable u markup-u); „Analitički"/„Marketing" input-i NEMAJU `checked` atribut.

## Tasks / Zadaci

- [x] **Task 1 — `{% gdpr_banner %}` template tag** (AC1)
  - [x] 1.1 Kreiraj `apps/gdpr/templatetags/__init__.py` + `apps/gdpr/templatetags/gdpr_banner.py`
  - [x] 1.2 `simple_tag(takes_context=True) def gdpr_banner(context)`: čita `context["request"].COOKIES`; kolačić odsutan → `render_to_string("gdpr/_consent_banner.html", {"next": request.get_full_path()}, request=request)` (KANONIČNI oblik — dict SAMO `{"next": ...}`; `request=request` kwarg injektuje `csrf_token`/`{% url %}`/`{% translate %}` u partial; NE dodavati `"request"` u dict redundantno); prisutan → `""`
  - [x] 1.3 `uv run python manage.py check` exit 0

- [x] **Task 2 — `SetConsentView` (POST, CSRF, ratelimit, cookie)** (AC2, AC3, AC4)
  - [x] 2.1 EXTEND `apps/gdpr/views.py`: `SetConsentView(View)` POST-only (`http_method_names=["post"]` → GET 405); zadrži `CookiePolicyView` netaknut
  - [x] 2.2 **`@method_decorator(ratelimit(key="ip", rate="10/m", block=False), name="dispatch")` na KLASI** (NE goli `@ratelimit` na metodi — funkcijski dekorator na CBV metodi SILENTLY NO-OP-uje; CRITICAL-2) + `if getattr(request, "limited", False): return HttpResponse(status=429)` guard u `post` (mirror 4-6 htmx_form_endpoint logiku, BEZ reuse). Import `from django.utils.decorators import method_decorator` + `from django_ratelimit.decorators import ratelimit`.
  - [x] 2.3 Parse `action` → izgradi `consent` dict (`necessary` UVEK True; `analytical`/`marketing` = `"analytical" in request.POST` itd.; accept_all=sve True; reject_all=samo necessary). **Nepoznata ILI nedostajuća `action` vrednost → default-deny (tretira se kao `reject_all`: samo `necessary` True) — NE crash/KeyError (G-15).**
  - [x] 2.4 `_safe_redirect(request)` helper: open-redirect guard `url_has_allowed_host_and_scheme(next, {request.get_host()}, request.is_secure())` → fallback referer → `reverse("pages:home")`; vrati `HttpResponseRedirect(..., status=303)`
  - [x] 2.5 `response.set_cookie("consent_state", json.dumps(consent), max_age=CONSENT_MAX_AGE, samesite="Lax", secure=settings.SESSION_COOKIE_SECURE, httponly=False, path="/")` (CONSENT_MAX_AGE = 60*60*24*365)

- [x] **Task 3 — URL routing** (AC5)
  - [x] 3.1 EXTEND `apps/gdpr/urls.py`: import `SetConsentView`; dodaj `path("htmx/gdpr/consent/", SetConsentView.as_view(), name="set_consent")`
  - [x] 3.2 Verifikuj `reverse("gdpr:set_consent")` → `/sr/htmx/gdpr/consent/`

- [x] **Task 4 — Baner partial template** (AC6)
  - [x] 4.1 `templates/gdpr/_consent_banner.html`: `role="dialog"` + `aria-labelledby` (heading `id`) + `aria-modal="false"`; `data-coric-gdpr-banner` root atribut + **`tabindex="-1"` na root-u** (da JS `focus()` na root radi — pinovan root-focus pattern, vidi AC7/Task 5.1)
  - [x] 4.2 `<form method="post" action="{% url 'gdpr:set_consent' %}">` + `{% csrf_token %}` + hidden `next`
  - [x] 4.3 3 kategorije (Neophodan checked+disabled / Analitički name=analytical BEZ checked / Marketing name=marketing BEZ checked) sa `<label>`-ima — opcioni checkbox-i podrazumevano ODČEKIRANI (AC10/CRITICAL-3)
  - [x] 4.4 3 submit dugmeta (`name="action"` value accept_all/reject_all/save) — **„Odbij sve" i „Prihvati sve" istog dugme-tier-a/komponentne klase (jednaka prominentnost; „Odbij sve" je `<button>`, NE faint link — AC10/CRITICAL-3)** + „Više info" `{% url 'gdpr:cookie_policy' %}`
  - [x] 4.5 Pune dijakritike u svim `{% translate %}` string-ovima

- [x] **Task 5 — Vanilla JS (progressive enhancement)** (AC7)
  - [x] 5.1 `static/js/gdpr-banner.js`: IIFE `'use strict'`; fokus on-show **na baner root** (`[data-coric-gdpr-banner]` sa `tabindex="-1"` → `.focus()`; pinovan root-focus, NE prvo dugme); **Esc gate-ovan na focus-within-banner** (`banner.contains(document.activeElement)`) → reject_all submit — NE globalni `document` Esc (CRITICAL-4); BEZ focus-trap; opciono `coric:consent-set`
  - [x] 5.2 Verifikuj baner radi BEZ JS (plain POST) — JS je SAMO enhancement
  - [x] 5.3 Učitaj `<script src=... defer>` u base.html (NE inline)

- [x] **Task 6 — CSS (tokeni + BEM)** (AC8)
  - [x] 6.1 `static/css/components/gdpr-banner.css`: `.coric-gdpr-banner` BEM, SAMO `var(--...)` tokeni, non-blokirajući fixed-bottom, prefers-reduced-motion, focus-visible, kontrast 4.5:1. **„Odbij sve" i „Prihvati sve" jednaka prominentnost (isti dugme-tier; razlika samo boja/akcenat) — AC10/CRITICAL-3.**
  - [x] 6.2 `@import url('./components/gdpr-banner.css');` u `static/css/main.css` (relative-with-dot)

- [x] **Task 7 — base.html mount + i18n** (AC9)
  - [x] 7.1 `base.html`: `gdpr_banner` u `{% load %}`; `{% gdpr_banner %}` **IZMEĐU `{% include "partials/footer.html" %}` i `{% aria_live %}`** (POSLE footer, NEPOSREDNO PRE aria-live); JS script tag
  - [x] 7.2 Verifikuj 7-2 NE render-uje tracker (response NE sadrži gtag/fbq/google-analytics)
  - [x] 7.3 `just messages` (sr/hu/en .po); sr pune dijakritike

- [x] **Task 8 — Lint + finalna verifikacija**
  - [x] 8.1 `just lint` clean (ruff + djade)
  - [x] 8.2 `makemigrations --check --dry-run` → „No changes detected" (0 model promene)
  - [x] 8.3 `just test` — gdpr testovi + broader suite GREEN (TEA piše testove RED phase PRE Dev-a; Dev GREEN)

## Dev Notes

### POST/CSRF/ratelimit — REFERENCA 4-6, NE reuse htmx_form_endpoint (SM-D7)

`SetConsentView` NIJE HTMX endpoint — to je obična form POST sa server redirect-om (progressive enhancement). `htmx_form_endpoint` dekorator (apps/forms/views.py:58) vraća HTMX **partial** (200 sa OOB aria-live) — pogrešna semantika za consent. KOPIRAJ ratelimit logiku (`ratelimit(key="ip", rate=..., block=False)` + `request.limited → 429`), NE reuse-uj dekorator. Rate `10/m` (NE `5/m` kao forme — consent je low-risk, low-value, legitiman posetilac može kliknuti više puta; SM-D7). CSRF je MANDATORY (CsrfViewMiddleware aktivan base.py:65; form `{% csrf_token %}`).

**CRITICAL-2 — `@ratelimit` na CBV metodi NE radi (silent no-op).** `django_ratelimit.decorators.ratelimit` je dekorator za FUNKCIJSKE poglede; primenjen direktno na CBV metodu (`post`/`dispatch`) NE veže se ispravno i rate-limit se **TIHO NE PRIMENJUJE** (tačno upozorenje iz forms docstring-a). Ispravan mehanizam: dekorisi KLASU sa `@method_decorator(ratelimit(key="ip", rate="10/m", block=False), name="dispatch")` (na `dispatch` da pokrije ceo request lifecycle pre `post`). Primer skeleta:

```python
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit

@method_decorator(ratelimit(key="ip", rate="10/m", block=False), name="dispatch")
class SetConsentView(View):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        if getattr(request, "limited", False):
            return HttpResponse(status=429)
        ...
```

Alternativa bi bila konverzija u funkcijski pogled sa golim `@ratelimit` (mirror forms presedan), ali se ovde bira CBV + `method_decorator` jer view ostaje `View` podklasa (`http_method_names` daje 405 besplatno). Test `test_ratelimit_429_after_limit` MORA realno okinuti 429 (NE samo asertovati postojanje dekoratora) da silent no-op bude uhvaćen.

### Cookie semantika — JSON, atributi, necessary-always-true (SM-D1/D3/D5)

- Vrednost: `json.dumps({"necessary": True, "analytical": bool, "marketing": bool})`. `necessary` se NE čita iz POST-a — server ga UVEK postavlja `True` (neophodni kolačići pravno ne traže consent; ne mogu da se isključe).
- `max_age = 60*60*24*365` (365 dana — AC epics.md:1019).
- `samesite="Lax"` (consent je first-party state; Lax je dovoljan + ne lomi top-level navigaciju).
- `secure=settings.SESSION_COOKIE_SECURE` (settings-driven: False u dev/test, True u staging/prod gde je `SESSION_COOKIE_SECURE = True` — production.py:15).
- `httponly=False` (SM-D5 — 7-3 čita server-side ALI buduća „manage consent" re-open (OQ-2) treba client-side čitanje da pre-checkuje toggle-ove; consent NIJE sensitive PII pa httponly nije neophodan; dokumentovana odluka).
- `path="/"` (site-wide).

### 7-2 ↔ 7-3 granica — NE kreiraj context_processor (SM-D8)

7-2 baner tag čita `request.COOKIES` DIREKTNO i prikazuje baner SAMO kad kolačić ODSUTAN — pa NE treba parsirati JSON ni `request.consent_state`. **7-3** dodaje `apps/gdpr/context_processors.py:consent_state` (parsira kolačić → dict na `request`) + uslovni render GA4/FB pixela. Ako 7-2 kreira context_processor, 7-3 bi ga duplirao/menjao → coupling. Granica: 7-2 PIŠE kolačić, 7-3 ČITA. **7-2 NE učitava NIJEDAN tracker** (epics.md:1034 — „Network request ka googleanalytics.com / facebook.com NE postoji pre prihvatanja consent-a"; 7-2 ne sme da ga uvede).

**Stale/malformed/forged kolačić — contract za 7-3.** 7-2 baner-tag suzbija baner na samom PRISUSTVU (`"consent_state" in request.COOKIES`), pa neispravna/stara-šema/forge-ovana vrednost (npr. `consent_state=garbage`) trajno krije baner (re-prompt se ne pojavljuje). To je prihvatljivo za 7-2 (presence-only suppression je namerno jednostavna). ALI 7-3, koji JEDINI parsira kolačić, MORA da bude robustan: **na `json.loads` grešci ili neočekivanoj šemi → tretirati kao pun DENY (`{necessary:true, analytical:false, marketing:false}`), NIKAD crash niti default-allow.** Time garbage/forged vrednost ne aktivira nijedan tracker (fail-safe). 7-2 NE dodaje parsiranje — samo predaje ovaj contract 7-3-u (vidi Boundary tabelu).

### Open-redirect guard — 6-4 presedan (SM-D9, security-critical)

`SetConsentView` redirektuje na `next`/referer posle postavljanja kolačića. NIKAD ne redirektuj na neproverenu vrednost (open-redirect). Koristi `url_has_allowed_host_and_scheme(url=next, allowed_hosts={request.get_host()}, require_https=request.is_secure())` (mirror apps/seo/models.py:98) → ako fail, probaj `HTTP_REFERER` (isti guard), pa fallback `reverse("pages:home")`. Scheme-relative (`//evil.com`) i cross-host se odbijaju.

### STYLE guardrails (log-only — ne menjaju core; sprečavaju buduće false-positive bug-reportove)

- **`next` hidden field autoescape:** `<input type="hidden" name="next" value="{{ next }}">` se oslanja na Django default autoescape — **NIKAD `|safe`**. Server svejedno re-validira vrednost open-redirect guard-om (G-5) pre redirect-a, pa je dvostruka zaštita (escape u markup-u + server-side validacija).
- **`_safe_redirect` — prazan `next`:** prazan string `next=""` korektno PADA na `url_has_allowed_host_and_scheme` (vraća False) → fall-through na referer/`pages:home`. NE treba prevremeni `if not next:` guard (izbegavamo defensive over-engineering — helper sam ispravno propada na praznu/nevalidnu vrednost).
- **Multi-tab:** baner u drugom već-otvorenom tab-u ostaje vidljiv do reload-a (server-rendered, NEMA cross-tab JS sinhronizacije). Prihvatljivo za v1 — log only (sledeća navigacija/reload tog taba sakrije baner jer kolačić sad postoji).
- **Open-redirect guard `require_https=request.is_secure()`:** apsolutni same-host ali different-scheme `next` (npr. `http://host/...` dok je request HTTPS) se ODBIJA (pada na referer/home). Branljivo (scheme-downgrade zaštita) — dokumentovano da se kasnije NE prijavi kao bug.

### Vanilla JS — search-expand.js konvencija (SM-D10)

Mirror `static/js/search-expand.js`: IIFE `'use strict'`, `init()` na `DOMContentLoaded` (ili odmah ako `readyState != loading`), `document.querySelector('[data-coric-gdpr-banner]')` hook, Esc handler. **Fokus on-show ide na baner ROOT** (`[data-coric-gdpr-banner]` nosi `tabindex="-1"` u template-u → `root.focus()` radi) — pinovan root-focus, BEZ ranije „root ILI prvo dugme" dvosmislenosti. RAZLIKA od search panela: aria-modal=false → **BEZ focus-trap** (fokus sme da izađe; baner je non-blokirajući). Esc = „Odbij sve" (AC epics.md:1021), **ALI SAMO kad je fokus UNUTAR banera** (CRITICAL-4 — vidi dole). `prefers-reduced-motion` se rešava u CSS-u (JS ne dira animaciju). JS-runtime ponašanje je manual smoke / Playwright (Epic 9.8) — pytest asertuje statički markup (mirror 2-13 napomena).

**CRITICAL-4 — Esc MORA biti gate-ovan na focus-within-banner, NE globalno.** Baner je non-modal (`aria-modal="false"`) i prisutan je na SVAKOJ strani sve dok consent nije postavljen. Ako bi Esc bio vezan globalno na `document` dok je baner samo prisutan, korisnik koji pritisne Esc dok kuca u search box-u, kontakt formi ili bilo kom polju bi NEHOTICE okinuo „Odbij sve" submit + reload — gubitak unosa i lažno odbijanje consent-a. Search-expand.js gate-uje Esc na sopstveno `open` stanje; ovde nema „open/closed" stanja (baner je uvek prisutan dok se ne reši), pa se gate-uje na **focus-within-banner**: u keydown handler-u proveri `if (event.key === "Escape" && banner.contains(document.activeElement)) { /* submit reject_all */ }`. Tako Esc reaguje samo dok korisnik interaguje sa banerom. (Esc=reject-all semantika ostaje per epics.md:1021, samo ispravno scope-ovana.)

### base.html mount (SM-D12)

`{% gdpr_banner %}` ide **IZMEĐU `{% include "partials/footer.html" %}` i `{% aria_live %}`** (linija 28) — tj. POSLE footer-a a NEPOSREDNO PRE aria-live regiona (pinovana pozicija; ne pre footer-a, ne posle aria-live). Tag sam interno odlučuje da li render-uje (kolačić odsutan) ili `""`. `{% load gdpr_banner %}` dodati u postojeći `{% load %}` (base.html:2). JS `<script src="{% static 'js/gdpr-banner.js' %}" defer>` u site-wide scripts blok (POSLE htmx/bootstrap — mirror sticky-nav.js:37).

### Project Structure Notes

- EXTEND postojeći `apps/gdpr/` (NE novi app). NOVI `templatetags/` dir prati per-app strukturu.
- URL u `i18n_patterns` (config/urls.py:49 već uključuje gdpr.urls) → `/sr/htmx/gdpr/consent/`. `htmx/` prefiks + ASCII slug.
- 0 model promene → 0 migracija. `makemigrations --check --dry-run` MORA biti čist.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 7.2] (gdpr_banner tag + SetConsentView + prihvati/odbij/podesi + consent_state 365d + role=dialog/aria-labelledby/aria-modal=false + Esc=Odbij-sve + Više-info→/sr/politika-kolacica/)
- [Source: _bmad-output/planning-artifacts/epics.md#Story 7.3] (7-3 čita request.consent_state iz context_processors.py + uslovni pixeli — GRANICA)
- [Source: _bmad-output/planning-artifacts/architecture.md:615-621,728,767,800] (gdpr app struktura: views.SetConsentView + templatetags/gdpr_banner.py + context_processors.consent_state 7-3; GdprConsentMiddleware buduća opcija; gdpr samostalan expose context processor)
- [Source: apps/gdpr/views.py + urls.py + models.py:99-101] (CookiePolicyView zadržati; EXTEND urls; CookiePolicy.get_absolute_url→gdpr:cookie_policy za „Više info")
- [Source: apps/forms/views.py:55-87] (@ratelimit key=ip block=False + request.limited→429 PATTERN — KOPIRAJ logiku, NE reuse htmx_form_endpoint jer vraća HTMX partial)
- [Source: apps/forms/urls.py:15-32] (htmx/forme/... URL prefiks konvencija)
- [Source: apps/seo/models.py:94-100] (url_has_allowed_host_and_scheme open-redirect guard PRESEDAN — 6-4)
- [Source: static/js/search-expand.js] (vanilla IIFE 'use strict' + Esc + fokus + prefers-reduced-motion + data-* hook + coric: event konvencija)
- [Source: templates/base.html:2,28,37] ({% load %} + footer/{% aria_live %} mount point + site-wide script defer pattern)
- [Source: static/css/main.css:1-15] (@import './components/*.css' relative-with-dot MANDATORY IMP-7)
- [Source: config/settings/production.py:15] (SESSION_COOKIE_SECURE=True u prod → Secure cookie flag settings-driven)
- [Source: config/settings/base.py:65,82] (CsrfViewMiddleware aktivan; request context_processor → request u template-ima)
- [Source: _bmad-output/implementation-artifacts/7-1-cookiepolicy-model-admin.md] (apps/gdpr scaffolding + gdpr:cookie_policy + SM-D10 admin URL realnost)
- [Source: _bmad-output/implementation-artifacts/4-6-htmx-form-patterns-aria-live-oob-rate-limiting.md] (ratelimit 429 SM-D9; OOB aria-live PATTERN)
- [Source: _bmad-output/project-context.md] (CSRF+ratelimit na formama; vanilla JS no-jQuery no-inline; coric: events; var(--token) BEM; a11y aria/keyboard/prefers-reduced-motion; ASCII slug + pune dijakritike UI; HTMX-only prefiks /htmx/)

## SM Decision Log

- **SM-D1 — consent_state kolačić = JSON `{"necessary":true,"analytical":bool,"marketing":bool}`.** JSON je čitljiv, eksplicitan, lak za 7-3 da parsira u dict (`request.consent_state`). Kompaktno kodiranje (npr. bitmask) bi uštedelo bajtove ali smanjilo čitljivost bez realne koristi (kolačić je mali). `necessary` UVEK True (neophodni kolačići pravno ne traže consent — ne mogu da se isključe; server ga forsira, NE čita iz POST-a).
- **SM-D2 — `{% gdpr_banner %}` = `simple_tag(takes_context=True)`.** Čita `context["request"].COOKIES`; render baner partial kroz `render_to_string(..., request=request)` SAMO kad `consent_state` ODSUTAN (bilo koja vrednost = posetilac izabrao → baner nestaje). `simple_tag` (NE `inclusion_tag`) jer treba uslovno render-ovanje (`""` vs partial) + `render_to_string` daje partial-u `request`/`csrf_token` context koji forma zahteva.
- **SM-D3 — `SetConsentView` = obična POST view + server redirect-back (HTTP 303), progressive enhancement.** NE HTMX (HTMX bi vratio partial — pogrešna semantika za site-wide consent state). Plain form POST radi BEZ JS (server postavlja kolačić + redirektuje nazad na trenutnu stranicu → baner nestaje). JS je enhancement (Esc/fokus), NE preduslov. 303 See Other = ispravna POST→GET semantika.
- **SM-D4 — Baner partial: `role="dialog"` + `aria-labelledby` + `aria-modal="false"` (NON-blokirajući).** AC epics.md:1020 eksplicitno `aria-modal="false"` — baner NIJE focus-trap modal; stranica ostaje upotrebljiva (posetilac može da skroluje/čita pre izbora). 3 kategorije (Neophodan disabled+checked / Analitički / Marketing) + 3 akcije + „Više info"→gdpr:cookie_policy. Sav UI tekst pune dijakritike. **NAPOMENA (a11y tenzija):** za NON-modalno, trajno cookie-obaveštenje WAI-ARIA APG preporučuje `role="region"`/`complementary` sa `aria-label` (NE `dialog`). 7-2 svesno sledi epics-mandirani `role="dialog"`+`aria-modal="false"` (vernost upstream spec-u; odluka „BEZ focus-trap" ublažava glavni rizik dialog-without-trap obrasca). Moguć budući a11y refinement → OQ-5. AC se NE menja.
- **SM-D5 — Kolačić atributi: SameSite=Lax, Secure=settings.SESSION_COOKIE_SECURE, httponly=False, path=/, max_age=365d.** `httponly=False` jer (a) 7-3 čita server-side ALI (b) buduća „manage consent" re-open (OQ-2) treba client-side čitanje da pre-checkuje toggle-ove; consent NIJE sensitive PII (samo zapis izbora), pa httponly nije neophodan. Secure je settings-driven (True u prod kroz SESSION_COOKIE_SECURE production.py:15). Dokumentovana odluka.
- **SM-D6 — URL `htmx/gdpr/consent/` u i18n_patterns → `/sr/htmx/gdpr/consent/`.** `htmx/` prefiks (project-context.md:163 HTMX-only/AJAX endpoint konvencija — POST je AJAX-style state-change). Ostaje u i18n_patterns jer apps.gdpr.urls je već tamo (config/urls.py:49 od 7-1); konzistentno sa forms `htmx/forme/...` koji su takođe locale-prefiksovani. ASCII slug. `name="set_consent"`.
- **SM-D7 — Ratelimit `@method_decorator(ratelimit(key="ip", rate="10/m", block=False), name="dispatch")` na KLASI + `request.limited→429`; KOPIRAJ 4-6 logiku, NE reuse htmx_form_endpoint.** Consent POST je javan state-change → ratelimit (project-context.md:721 #2 ratelimit na javnim endpoint-ima). **Mehanizam je `method_decorator` na klasi jer je `SetConsentView` CBV — goli `@ratelimit` na metodi tiho NO-OP-uje (CRITICAL-2).** Rate `10/m` blaži od `5/m` forma jer je consent low-risk/low-value i legitiman posetilac može kliknuti više puta (predomisli se). `block=False` + ručni 429 (mirror 4-6 SM-D9 — NE 403). `htmx_form_endpoint` se NE reuse-uje jer vraća HTMX partial (pogrešna semantika; SetConsentView vraća redirect).
- **SM-D8 — 7-2 ↔ 7-3 granica: 7-2 PIŠE kolačić + render baner; 7-3 ČITA (context_processor + pixeli). 7-2 NE kreira context_processor, NE učitava tracker.** Baner tag čita `request.COOKIES` direktno (prikazuje samo kad odsutan → nema potrebe parsirati). 7-3 dodaje `context_processors.py:consent_state` (parse → `request.consent_state`) + `templatetags/tracking.py` (uslovni GA4/FB). Sprečava dupliranje/coupling. SECURITY: 7-2 NE sme da uvede NIJEDAN tracker script (epics.md:1034).
- **SM-D9 — Open-redirect guard na redirect-back (mirror 6-4).** `url_has_allowed_host_and_scheme(next, {request.get_host()}, request.is_secure())` (apps/seo/models.py:98 presedan) → same-origin only; fallback referer (isti guard) → `reverse("pages:home")`. Sprečava `next=https://evil.com` open-redirect. Security boundary (NE defensive over-engineering — `next` je untrusted user input).
- **SM-D10 — Vanilla JS EKSTERNI fajl `gdpr-banner.js` (NE inline), progressive enhancement.** Mirror search-expand.js (IIFE 'use strict', data-* hook, Esc, fokus, prefers-reduced-motion-kroz-CSS, coric: event). RAZLIKA: aria-modal=false → BEZ focus-trap. **Esc=Odbij-sve ALI gate-ovan na focus-within-banner (`banner.contains(document.activeElement)`), NE globalno na `document` — baner je non-modal i prisutan na svakoj strani, pa bi globalni Esc okidao „Odbij sve" iz search-box-a/forme (CRITICAL-4).** EKSTERNI fajl jer: (a) project konvencija (svi JS u static/js/), (b) CSP-readiness (django-csp je u deps ali NIJE konfigurisan — no CspMiddleware/CSP_* settings; ipak inline JS je anti-pattern za buduću CSP). Baner radi BEZ JS (plain POST) — JS je SAMO a11y/UX sloj.
- **SM-D11 — CSS `gdpr-banner.css` @import u main.css, tokeni + coric- BEM.** `.coric-gdpr-banner` BEM, SAMO `var(--...)` (project-context.md:317 NIKAD magic), non-blokirajući fixed-bottom (NE full-screen overlay — aria-modal=false znači stranica je upotrebljiva), prefers-reduced-motion, focus-visible, kontrast 4.5:1. Relative-with-dot @import (IMP-7).
- **SM-D12 — base.html mount IZMEĐU footer-a i {% aria_live %} (pinovana pozicija).** `{% gdpr_banner %}` ide POSLE `{% include "partials/footer.html" %}` a NEPOSREDNO PRE `{% aria_live %}` regiona (ne pre footer-a, ne posle aria-live). Baner je site-wide chrome (kao footer/aria-live); tag sam odlučuje render. JS učitan `defer` u site-wide scripts blok (POSLE htmx/bootstrap).
- **SM-D13 — GDPR validnost: equal-prominence „Odbij sve"↔„Prihvati sve" + ne-pre-ticked opcioni checkbox-i (CRITICAL-3).** EDPB Guidelines 05/2020 traže da je odbijanje jednako lako/prominentno kao prihvatanje i da nijedan ne-neophodni checkbox nije unapred čekiran. Bez ovoga je consent pravno nevalidan iako funkcionalno radi. Odluka: oba dugmeta su `<button type="submit">` istog tier-a/komponentne klase (`.coric-gdpr-banner__action`), razlika samo boja/akcenat; „Analitički"/„Marketing" su podrazumevano odčekirani; SAMO „Neophodan" `checked`+`disabled`. Encoded u AC10 + AC6 + AC8 + Task 4.3/4.4 + Task 6.1 + G-13 + testovi.

## Gotchas

- **G-1 (`{% gdpr_banner %}` mora dobiti `request` u partial context-u):** `simple_tag(takes_context=True)` → `render_to_string("gdpr/_consent_banner.html", {"next": request.get_full_path()}, request=request)`. **Upravo `request=request` (KWARG) injektuje `csrf_token` + `{% url %}` i18n + `{% translate %}` u partial context** — eksplicitni dict NE treba (i ne sme redundantno) da sadrži `"request"`. BEZ `request=request`, `{% csrf_token %}` u baner formi NE radi (CSRF token zahteva request context) → forma submit → 403. KRITIČNO.
- **G-2 (CSRF na consent formi MANDATORY):** baner forma je state-change POST → `{% csrf_token %}` OBAVEZAN (project-context.md:213). BEZ njega svaki submit → 403. CsrfViewMiddleware je aktivan (base.py:65). Test `test_post_without_csrf_403` MORA koristiti `Client(enforce_csrf_checks=True)` — default pytest-django `client` ISKLJUČUJE CSRF pa bi test bio lažno-zelen i NE bi otkrio nedostajući `{% csrf_token %}` (CRITICAL-1).
- **G-3 (`necessary` UVEK True — NE čita iz POST-a):** server forsira `consent["necessary"] = True` u SVAKOM action-u (uključujući reject_all). Neophodni kolačići se ne mogu isključiti. NE čitaj `"necessary" in request.POST` (Neophodan checkbox je `disabled` → disabled checkbox se NE šalje u POST-u → kad bi server čitao iz POST-a, necessary bi bio False; zato server forsira True).
- **G-4 (disabled checkbox se NE submit-uje):** „Neophodan" checkbox je `disabled` (UX — ne može da se isključi) → browser ga NE uključuje u POST. Zato server forsira `necessary=True` nezavisno od POST-a (G-3). NE oslanjaj se na hidden mirror input — server-forced je čistije.
- **G-5 (open-redirect — `next` je untrusted):** `next` POST param i `HTTP_REFERER` su user-controlled → MORA proći `url_has_allowed_host_and_scheme` PRE redirect-a (SM-D9). `next=https://evil.com` / `//evil.com` se odbijaju → fallback pages:home. Mirror seo/models.py:98.
- **G-6 (ratelimit 429 NE 403):** `block=False` + ručni `if request.limited: return HttpResponse(status=429)` (mirror 4-6 SM-D9). NE `block=True` (koji vraća 403). Konzistentno sa formama.
- **G-6b (ratelimit na CBV → `method_decorator`, NIKAD goli `@ratelimit` na metodi — CRITICAL-2):** `django_ratelimit` je funkcijski dekorator; primenjen direktno na `post`/`dispatch` metodu CBV-a se ne veže i rate-limit TIHO NE RADI (silent security no-op). Koristi `@method_decorator(ratelimit(...), name="dispatch")` na klasi. Test `test_ratelimit_429_after_limit` MORA realno okinuti 429 (ne samo proveriti da dekorator postoji) — tako se silent no-op hvata.
- **G-7 (JS EKSTERNI, NE inline — progressive enhancement):** `gdpr-banner.js` u static/js/, učitan `<script src=... defer>`. Baner MORA raditi BEZ JS (plain POST). JS je SAMO Esc/fokus enhancement. NE inline `<script>` (CSP-readiness + project konvencija).
- **G-8 (aria-modal=false → BEZ focus-trap):** baner JE `role="dialog"` ALI `aria-modal="false"` → NIJE blokirajući modal. JS NE sme da implementira focus-trap (fokus sme da izađe na ostatak strane). Razlika od search-panel-a. Fokus on-show (move u baner) + return on-dismiss je OK; trap NIJE.
- **G-14 (Esc gate-ovan na focus-within-banner, NE globalno — CRITICAL-4):** baner je non-modal i prisutan na svakoj strani dok consent nije postavljen. Globalni `document` Esc handler bi okinuo „Odbij sve" + reload kad korisnik pritisne Esc u search box-u/kontakt formi/bilo kom polju → gubitak unosa + lažno odbijanje. Gate Esc na `banner.contains(document.activeElement)` (Esc radi SAMO dok je fokus unutar banera). Esc=reject-all semantika ostaje (epics.md:1021), samo ispravno scope-ovana.
- **G-15 (nepoznata/nedostajuća `action` → default-deny, NE crash):** `action` je untrusted POST input. Ako vrednost nije `accept_all`/`reject_all`/`save` (ili izostane), view NE sme da padne (KeyError) niti da default-uje na „prihvati" — tretira se kao `reject_all` (samo `necessary` True, default-deny). Implementacija: npr. `if action == "accept_all": ... elif action == "save": ... else: # reject_all + nepoznato/nedostaje` → default grana = deny. (Granica je tu jedina dozvoljena „defensive" obrada — ostalo NE over-engineer-ovati per OUT OF SCOPE; ovo je consent-safety default.)
- **G-9 (0 migracije — verify):** 7-2 NE menja modele → `makemigrations --check --dry-run` MORA biti „No changes detected". Ako Dev slučajno dodirne model → STOP (van scope-a).
- **G-10 (7-2 NE učitava tracker — security):** verify response NE sadrži `gtag`/`fbq`/`googletagmanager`/`google-analytics`/`facebook`. Tracking je 7-3. 7-2 baner sam NE sme da uvede nijedan analytics/pixel script.
- **G-11 (slug ASCII / UI dijakritike):** URL `htmx/gdpr/consent/` ASCII (project-context.md:165). Baner UI tekst (Prihvati sve / Odbij sve / Neophodan / Analitički / Marketing / Više info) pune dijakritike kroz `{% translate %}`.
- **G-12 (GET na set_consent → 405):** view je POST-only (`http_method_names=["post"]`). GET → 405 (sprečava da link/prefetch slučajno postavi consent). Test `test_get_returns_405`.
- **G-13 (GDPR validnost — equal-prominence + no pre-ticked; CRITICAL-3):** „Odbij sve" MORA biti jednako prominentno kao „Prihvati sve" (isti `<button>` tier/klasa/veličina/težina — NE faint sekundarni link), a „Analitički"/„Marketing" checkbox-i MORAJU biti podrazumevano ODČEKIRANI (BEZ `checked`). Inače je consent pravno NEVALIDAN (EDPB 05/2020) iako svi funkcionalni AC-ovi prođu. Test: oba dugmeta dele istu osnovnu button-klasu; opcioni input-i nemaju `checked`.

## Open Questions

- **OQ-1 — Da li baner treba da blokira/zamagli sadržaj do izbora (cookie-wall)?** AC eksplicitno traži `aria-modal="false"` (NON-blokirajući) → v1 odluka: baner je non-blokirajući (posetilac može da koristi sajt pre izbora; tracking je ionako off do consent-a kroz 7-3). Cookie-wall (forsiranje izbora pre pristupa) je pravno sporan u EU (GDPR — consent mora biti slobodan) → NE radimo cookie-wall. RESOLVED: non-blokirajući (per AC).
- **OQ-2 — „Manage consent" / re-open baner posle prvog izbora (footer dugme „Podešavanja kolačića")?** Deferred. v1 baner se prikazuje SAMO kad kolačić odsutan; posle izbora nestaje zauvek (do isteka 365d / brisanja kolačića). Re-open UI (sa pre-check-ovanim toggle-ovima iz kolačića) je polish — `httponly=False` (SM-D5) već omogućava buduće client-side čitanje. Footer dugme + JS toggle = budući story / Epic 8. (NE blokira 7-2.)
- **OQ-3 — Server-side consent audit log (ko-je-kad-pristao)?** Deferred (YAGNI v1). GDPR ponekad traži dokaz consent-a; v1 čuva samo trenutno stanje u kolačiću (NEMA server-side record). Ako legal traži audit trail → zaseban model + zapis u SetConsentView (budući story). Dokumentovan rizik za Mihas sign-off pre go-live (mirror 7-1 RISK-1 stil).
- **OQ-4 — Da li „save" bez ijednog opcionog checkbox-a == „reject_all"?** v1: da (oba daju `{necessary:true, analytical:false, marketing:false}`). Razlikuju se samo UX-om (dugme koje korisnik klikne). Funkcionalno isto. RESOLVED: isto stanje, dva dugmeta (UX izbor).
- **OQ-5 — `role="dialog"` vs `role="region"`/`complementary` za trajno cookie-obaveštenje (a11y refinement).** WAI-ARIA APG preferira `role="region"`/`complementary` + `aria-label` za NON-modalno persistentno obaveštenje; `role="dialog"`+`aria-modal="false"` bez focus-trap-a je manje idiomatičan (dialog implicira modalnu interakciju). 7-2 sledi epics.md:1020 mandat (`role="dialog"`+`aria-modal="false"`) vernos upstream-u; „BEZ focus-trap" (G-8) ublažava glavni rizik. Budući refinement: prebaciti na `region`/`complementary` ako a11y audit (Epic 9) tako preporuči. NE menja se u 7-2 (AC fiksiran). Dokumentovano da se kasnije NE prijavi kao bug.

## Testing

**TEA piše testove (RED phase) PRE Dev implementacije (project-context.md:294). Dev NIKAD ne piše testove.** pytest-django; `@pytest.mark.django_db` gde dira DB/sesiju. JS-runtime ponašanje (Esc/fokus) = manual smoke / Playwright Epic 9.8 — pytest asertuje statički markup + view ponašanje.

**KRITIČNO — CSRF-enforcing klijent za security testove (CRITICAL-1):** pytest-django default `client` fixture (i `django.test.Client()` bez argumenata) **ISKLJUČUJE CSRF enforcement** — pa bi `test_post_without_csrf_403` bio **lažno-zelen** (prošao bi čak i da `{% csrf_token %}` NEDOSTAJE). Zato:
- **CSRF-negativni test (`test_post_without_csrf_403`)** MORA koristiti CSRF-enforcing klijent: `Client(enforce_csrf_checks=True)` (`from django.test import Client`) — ili dedicated `csrf_client` fixture (`@pytest.fixture def csrf_client(): return Client(enforce_csrf_checks=True)`). Bez ovoga test ne dokazuje ništa.
- **Happy-path POST testovi** (accept_all/reject_all/save/cookie atributi/redirect/ratelimit) koriste **standardni non-enforcing `client`** (CSRF se ne proverava → ne treba slati token; testira se view logika, ne CSRF). Alternativno, ako se koristi enforcing klijent i za njih, MORAJU slati validan token (GET baner stranu → izvuci `csrfmiddlewaretoken` → uključi u POST). **Preporuka: standardni `client` za happy-path, `enforce_csrf_checks=True` SAMO za `test_post_without_csrf_403`** — suite ostaje koherentan i svaki test je smislen.

### Template tag (apps/gdpr/tests/test_gdpr_banner_tag.py)
- `test_banner_rendered_when_cookie_absent` — render `{% gdpr_banner %}` bez `consent_state` kolačića → sadrži baner markup (`role="dialog"`)
- `test_banner_empty_when_cookie_present` — request sa `consent_state` kolačićem → tag vraća `""` (baner odsutan)
- `test_banner_includes_csrf_token` — render-ovan baner sadrži CSRF token (`name="csrfmiddlewaretoken"`) — dokazuje `render_to_string(request=request)` (G-1)
- `test_banner_hidden_next_is_current_path` — hidden `next` input = `request.get_full_path()`

### SetConsentView (apps/gdpr/tests/test_set_consent_view.py)
- `test_accept_all_sets_all_true` — POST action=accept_all (sa CSRF) → kolačić `{necessary:true, analytical:true, marketing:true}`
- `test_reject_all_only_necessary` — POST action=reject_all → `{necessary:true, analytical:false, marketing:false}`
- `test_save_per_category` — POST action=save SA analytical (bez marketing) → `{necessary:true, analytical:true, marketing:false}`
- `test_save_no_checkboxes_default_deny` — POST action=save BEZ checkbox-a → samo necessary true
- `test_unknown_or_missing_action_default_deny` — POST sa `action=garbage` (ili BEZ `action` polja) → kolačić `{necessary:true, analytical:false, marketing:false}` (default-deny; NE 500/KeyError, NE prihvati-sve; G-15)
- `test_necessary_always_true_even_on_reject` — reject_all → `necessary` je True (G-3; necessary se NE čita iz POST-a)
- `test_cookie_attributes` — max_age==60*60*24*365, samesite=="Lax", path=="/", httponly==False; secure prati settings.SESSION_COOKIE_SECURE
- `test_post_without_csrf_403` — POST bez CSRF token-a koristeći **`Client(enforce_csrf_checks=True)`** (NE default `client` — taj isključuje CSRF i dao bi lažno-zeleno; CRITICAL-1) → 403 (G-2). Ovaj test dokazuje da `{% csrf_token %}` + CsrfViewMiddleware zaista štite endpoint.
- `test_get_returns_405` — GET → 405 (G-12)
- `test_ratelimit_429_after_limit` — **realno okini limit**: pošalji 11 POST-ova/min sa istog IP → 11. vraća **429** (NE 403; G-6). Ovaj test MORA zaista preći prag (NE samo asertovati da dekorator postoji) — tako hvata silent no-op ako ratelimit nije pravilno vezan na CBV (CRITICAL-2/G-6b). **TEA napomena: django-ratelimit backend je locmem cache koji je PROCES-deljen kroz testove → brojač curi između testova i pravi flakiness zavisnu od redosleda izvršavanja.** Reši sa `cache.clear()` u setup-u/fixture-u (`from django.core.cache import cache; cache.clear()` pre testa) ILI mock `django_ratelimit.decorators.is_ratelimited`. Bez ovoga drugi POST testovi mogu da potroše budžet pa ovaj test okine 429 prerano (ili obrnuto). Po potrebi parametrizuj prag.
- `test_redirect_back_same_origin` — POST next=/sr/proizvodi/ → redirect na /sr/proizvodi/ (303/302)
- `test_redirect_open_redirect_blocked` — POST next=https://evil.com/ → redirect NE ide na evil.com (fallback pages:home ili same-origin referer; G-5/SM-D9)
- `test_redirect_no_next_fallback_home` — POST bez next/referer → redirect na reverse("pages:home")
- `test_set_consent_url_reverse` — `reverse("gdpr:set_consent")` == `/sr/htmx/gdpr/consent/` (AC5)

### Baner template a11y (apps/gdpr/tests/test_consent_banner_template.py)
- `test_role_dialog_and_aria_modal_false` — root ima `role="dialog"` + `aria-modal="false"`
- `test_aria_labelledby_resolves` — `aria-labelledby` vrednost == `id` postojećeg heading elementa u markup-u
- `test_three_categories` — Neophodan (checked+disabled), Analitički (name=analytical), Marketing (name=marketing) prisutni sa label-ima
- `test_three_actions` — 3 submit dugmeta name=action values accept_all/reject_all/save
- `test_reject_equal_prominence_to_accept` — „Odbij sve" i „Prihvati sve" su oba `<button type="submit">` i dele istu osnovnu button-komponentnu klasu (`.coric-gdpr-banner__action`); „Odbij sve" NIJE `<a>`/faint link (GDPR equal-prominence; AC10/CRITICAL-3/G-13)
- `test_optional_checkboxes_default_unchecked` — „Analitički" (`name="analytical"`) i „Marketing" (`name="marketing"`) input-i NEMAJU `checked` atribut; SAMO „Neophodan" je `checked` (i `disabled`) — nema pre-ticked ne-neophodnih kategorija (AC10/CRITICAL-3/G-13)
- `test_more_info_href` — „Više info" href == `reverse("gdpr:cookie_policy")` (== /sr/politika-kolacica/)
- `test_form_action_is_set_consent` — form action == `reverse("gdpr:set_consent")`; method=post

### base.html mount + no-tracker (apps/gdpr/tests/test_banner_mount.py — integration)
- `test_banner_visible_on_any_page_when_cookie_absent` — GET `/sr/` bez consent kolačića → response sadrži baner. **TEA napomena: home (`/sr/`) može da zahteva DB fixtures (proizvodi/kategorije/brendovi) da render-uje bez 500.** Ako je tako, izaberi minimalnu/jednostavniju stranu koja extend-uje `base.html` i nema teške context-zahteve (npr. statična `pages:` strana) ILI dokumentuj/obezbedi minimalne fixtures (`@pytest.mark.django_db` + factory). Cilj je dokazati site-wide mount, ne render home-a.
- `test_banner_absent_when_cookie_present` — GET `/sr/` sa consent kolačićem → response NE sadrži baner
- `test_no_tracker_loaded_by_72` — GET strana → response NE sadrži `gtag`/`fbq`/`google-analytics`/`googletagmanager`/`facebook` (G-10 — tracking je 7-3)
- `test_gdpr_banner_js_external_script_present` — base.html render → `<script src=".../gdpr-banner.js" defer>` prisutan; NEMA inline consent JS

### i18n / dijakritike
- `test_ui_strings_use_full_diacritics` — baner UI string-ovi koriste č/ć/ž/š/đ (Prihvati sve / Odbij sve / Neophodan / Analitički / Marketing / Više info / Sačuvaj izbor)
- `test_consent_slug_is_ascii` — URL `/htmx/gdpr/consent/` ASCII (G-11)

### No migration
- `test_no_pending_migrations` — `makemigrations --check --dry-run` clean (G-9; 0 model promene)

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
