# 7-3 Interface Contract — GA4 + FB Pixel Template Tagovi (Conditional Render)

**Story:** 7-3 (GDPR & Privacy, Epic 7) · **Module:** `apps/gdpr` · **Phase:** TEA RED → Dev GREEN
**Status:** TEA canonical contract — Dev MORA zadovoljiti SVAKU stavku ispod. NE menja 7-1/7-2 artefakte.

---

## 1. `apps/gdpr/context_processors.py:consent_state(request)` (NOVI)

```python
def consent_state(request) -> dict:
    ...  # vraca {"consent_state": {"necessary": True, "analytical": bool, "marketing": bool}}
```

- Cita `request.COOKIES.get("consent_state")` (7-2 `SetConsentView` postavlja kao `json.dumps(dict)`).
- `raw is None` → DEFAULT-DENY.
- `try: data = json.loads(raw) except (ValueError, TypeError): data = {}` (`JSONDecodeError` je `ValueError` podklasa).
- `if not isinstance(data, dict): data = {}`.
- Rezultat: `{"necessary": True, "analytical": data.get("analytical") is True, "marketing": data.get("marketing") is True}`.
- **STRIKTAN `is True`** (SM-D10/CRITICAL-2): SAMO pravi JSON `true` (Python `True`) prolazi. Off-tip truthy (`"yes"`, `1`, `"true"`-string) → `False`. NIKAD `bool(...)`.
- `necessary` UVEK `True` (server-forced).
- **DEFAULT-DENY** na: odsutan / malformed JSON / ne-dict (`[]`/`42`/`"true"`) / nedostajuci kljuc. **NIKAD crash, NIKAD default-allow.**
- Vraca u obliku `{"consent_state": <dict>}` (template lookup `consent_state.analytical` = dict-key, G-11).
- **Registracija:** `config/settings/base.py` `TEMPLATES[0]["OPTIONS"]["context_processors"]` POSLE `apps.blog.context_processors.latest_blog_posts` (base.py:86), G-9.

## 2. `apps/gdpr/templatetags/tracking.py` (NOVI; pored 7-2 `gdpr_banner.py`)

`register = template.Library()`. Import `template`, `settings`, `format_html`, `mark_safe`, `DEFAULT_DENY` (iz `apps.gdpr.context_processors`).

- **`@register.simple_tag(takes_context=True) def ga_pixel(context)`**
  - `consent = context.get("consent_state", DEFAULT_DENY)` (**privacy-fail-safe**, G-1 — ako cp neregistrovan ILI manual Context render bez ključa → default-deny → render "", NIKAD KeyError/500. Mis-registracija je pokrivena dedikovanim `test_consent_state_context_processor_registered` → fail-loud bi dodao 0 detekcije; `.get(DEFAULT_DENY)` je decoupled + fail-safe izbor — ARCH improvement od code review-a).
  - `gid = settings.GA_MEASUREMENT_ID`.
  - **Guard:** `if not consent.get("analytical") or not gid: return ""` (kanonska forma; ekvivalentno striktnom `is True` jer cp cuva SAMO bool-ove, SM-D10).
  - Inace render GA4 gtag: `<script async src="https://www.googletagmanager.com/gtag/js?id={GID}">` + inline `gtag('js', new Date())` + `gtag('config', '{GID}')`.
- **`@register.simple_tag(takes_context=True) def fb_pixel(context)`**
  - `consent = context.get("consent_state", DEFAULT_DENY)` (privacy-fail-safe, G-1); `pid = settings.FB_PIXEL_ID`.
  - **Guard:** `if not consent.get("marketing") or not pid: return ""`.
  - Inace render FB Pixel: fbq IIFE + `fbq('init', '{PID}')` + `fbq('track', 'PageView')` + gated `<noscript><img ...facebook.com/tr?id={PID}...></noscript>` (G-6).

### Brace-safe build (CRITICAL-1 / SM-D11 — OBAVEZNO)

- Brace-heavy JS telo (`function gtag(){dataLayer.push(arguments);}`, `!function(f,b,e,v,n,t,s){...}(...)`) je **STATICKI `mark_safe(...)` string** — NIKAD ne prolazi kroz `format_html` format-string (literalne `{`/`}` → `str.format()` → `KeyError`/`ValueError`/`IndexError` → 500 na svakom consented render-u).
- SAMO ID (`gid`/`pid`) ide kroz `format_html` na BRACE-FREE fragment (`{}` placeholder, NIJEDNU drugu `{`/`}`): `format_html('<script async src="...gtag/js?id={}"></script>', gid)`, `format_html("gtag('config', '{}');", gid)`.
- Sklopi `mark_safe("\n".join(parts))` (mirror `apps/seo/templatetags/seo_meta.py:seo_head`).
- `format_html` escape-uje ID (defense-in-depth, G-5/SM-D4); NIKAD `mark_safe(f"...{gid}...")` na neescapiranom ID-u.
- Rezultat MORA sadrzati `function gtag(){...}` / `!function(...){` sa JEDNOSTRUKIM brace-ovima (NIKAD `{{`/`}}`).

## 3. Settings (`config/settings/base.py` EDIT)

```python
GA_MEASUREMENT_ID = env("GA_MEASUREMENT_ID", default="")
FB_PIXEL_ID = env("FB_PIXEL_ID", default="")
```

- Uz ostale env-driven (mirror `ANYMAIL_RESEND_API_KEY`, base.py:121). Prazan default → dev/test render NISTA (no-tracker fail-safe). NE SiteSettings model (per-environment infra config). 0 migracije.
- `.env.example`: `# ── Tracking (Epic 7, Story 7.3) ──` sa `GA_MEASUREMENT_ID=` + `FB_PIXEL_ID=` (prazni placeholderi).

## 4. base.html mount (`templates/base.html` EDIT)

- **APPEND `tracking` na POSTOJECI `{% load %}` (linija 2), alfabetski POSLE `static`:** `{% load django_bootstrap5 gdpr_banner hreflang htmx_aria i18n seo_meta static tracking %}`. NE odvojen `{% load tracking %}` red.
- `{% ga_pixel %}` VISOKO u `<head>` (POSLE `<title>` linija 8, PRE/oko CSS link-ova; NE na dnu posle `{% block extra_head %}`); `{% fb_pixel %}` neposredno posle. Oba UNUTAR `<head>`.
- **G-14:** NIKAD out-of-gate `preconnect`/`dns-prefetch`/`preload` ka `googletagmanager.com`/`connect.facebook.net`/`google-analytics.com`/`facebook.com` u `<head>`.

## 5. Files Dev creates / edits

| Path | Tip |
|---|---|
| `apps/gdpr/context_processors.py` | NOVO |
| `apps/gdpr/templatetags/tracking.py` | NOVO |
| `config/settings/base.py` | EDIT (cp registracija + 2 env settings) |
| `templates/base.html` | EDIT (`{% load %}` append + 2 mount taga) |
| `.env.example` | EDIT (2 placeholder-a) |

**NETAKNUTO (regression guards):** `apps/gdpr/{models,views,urls}.py`, `templatetags/gdpr_banner.py`, `templates/gdpr/_consent_banner.html`, JS/CSS, MIDDLEWARE (NE GdprConsentMiddleware), `apps/blog/context_processors.py`. `makemigrations --check --dry-run` → „No changes detected".

---

## TEA test files (RED)

- `apps/gdpr/tests/test_consent_state_context_processor.py`
- `apps/gdpr/tests/test_tracking_tags.py`
- `apps/gdpr/tests/test_tracking_mount_no_load.py` (integration `/sr/o-nama/`)
- `apps/gdpr/tests/test_tracking_settings_env.py`

**Dev notes:** positive-render testovi koriste `override_settings(GA_MEASUREMENT_ID=..., FB_PIXEL_ID=...)`; integration na `/sr/o-nama/` (pages:about, NO fixtures); single-brace JS asercija (CRITICAL-1); privacy-fail-safe missing-consent_state → render "" (G-1; bivse fail-loud KeyError, promenjeno per code-review ARCH improvement — `.get(DEFAULT_DENY)`); no-tracker asercija cilja SAMO tracker-specificne tokene (`googletagmanager.com/gtag/js`, `gtag(`, `connect.facebook.net`, `facebook.com/tr`, `fbq(`) — NIKAD bare `facebook`/`google` (CRITICAL-3).
