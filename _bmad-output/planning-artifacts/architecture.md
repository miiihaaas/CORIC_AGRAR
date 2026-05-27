---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8]
lastStep: 8
completedAt: '2026-05-27'
inputDocuments:
  - _bmad-output/planning-artifacts/briefs/brief-CORIC_AGRAR-2026-05-27/brief.md
  - _bmad-output/planning-artifacts/briefs/brief-CORIC_AGRAR-2026-05-27/addendum.md
  - _bmad-output/planning-artifacts/prds/prd-CORIC_AGRAR-2026-05-27/prd.md
  - _bmad-output/planning-artifacts/ux-designs/ux-CORIC_AGRAR-2026-05-27/DESIGN.md
  - _bmad-output/planning-artifacts/ux-designs/ux-CORIC_AGRAR-2026-05-27/EXPERIENCE.md
workflowType: 'architecture'
project_name: 'CORIC_AGRAR'
user_name: 'Mihas'
date: '2026-05-27'
status: complete
mode: fast-path
language: srpski-latinica
---

# Architecture Decision Document — Ćorić Agrar

_Ovaj dokument se gradi kolaborativno kroz step-by-step discovery. Sekcije se dodaju kako se kreće kroz svaku arhitektonsku odluku._

## Project Context Analysis

### Requirements Overview

**Funkcionalni domeni:** 48 FR-ova grupisanih u 13 feature klastera + 1 cross-feature (variant selektor). Obuhvataju katalog (traktori + 4 kategorije mehanizacije + polovna), stranicu pojedinačnog proizvoda, servis i rezervne delove forme, blog „Priče sa polja", globalnu pretragu, trojezičnost (sr/hu/en sa fallback), kompletan admin panel (sadržaj, pristup, SEO, podešavanja).

**Non-Functional zahtevi koji oblikuju arhitekturu:**

- **WCAG 2.1 nivo AA** (eksplicitno u PRD § 5.2 + EXPERIENCE.md Accessibility Floor) — utiče na HTMX feedback (aria-live), focus management, ARIA atribute akordiona i Lightbox-a
- **Performance:** HTMX filter <500ms, responsive images, page load 4G mobilna veza — konkretni LCP/TTFB targeti otvoreni za odluku
- **Sigurnost:** Django auth (bcrypt/argon2), CSRF na svim formama, rate limiting (forme + login), MIME validacija upload-a, HTTPS enforcement
- **SEO:** sitemap.xml auto-gen, hreflang oznake, robots.txt, semantic HTML, OG/Twitter meta
- **Reliability:** dnevni automatski bekap baze + media, SSL Let's Encrypt sa auto-renewal
- **Browser podrška:** evergreen modern (Chrome/FF/Safari/Edge poslednje 2 verzije)

**Scale & Complexity:**

- **Primary domain:** full-stack web (Django MVT + HTMX server-rendered partials + PostgreSQL)
- **Complexity level:** medium — multi-language + CMS + 4 brendova + multiple forms + search + filtering, ali bez real-time, multi-tenancy ili payments
- **Procenjen broj arhitektonskih komponenti:** ~12-15 Django app-ova/modula (catalog, products, brands, categories, blog, forms, search, i18n, seo, admin-extensions, media, accounts, gdpr, analytics)
- **Data volume:** ~100 proizvoda + ~50 blog objava/godišnje + polovna inventar (varija). Single PostgreSQL instance dovoljna; bez sharding-a
- **Write velocity:** vrlo nizak (admin updates, forme par dnevno)
- **Read velocity:** low-medium (regionalni traffic, B2C/B2B catalog browsing)

### Technical Constraints & Dependencies

**Fiksirani tech stack (iz Brief addendum-a, ne menja se):**

- **Backend:** Django (Python) + PostgreSQL + django-modeltranslation + Gunicorn + Nginx
- **Frontend:** HTML5/CSS3/JS + Bootstrap 5.3 + HTMX + Font Awesome 6, Roboto (Google Fonts)
- **DevOps:** uv (Python package manager) + Docker (containerization) + Hetzner VPS (hosting) + Git (VCS) + Let's Encrypt (SSL)
- **3 okruženja:** lokalno / staging / produkcija

**Eksterne integracije:**

- Google Analytics 4 (uslovna aktivacija — GDPR consent)
- Google Search Console (verifikacija + opciono admin link)
- Facebook Pixel (uslovna aktivacija — GDPR consent Marketing)
- Google Maps (embed na Kontakt strani)
- SMTP servis (još nije izabran — kandidati Mailgun / SendGrid / Resend / Hetzner SMTP)

**Foundation dependencies:**

- `DESIGN.md` kao single source za vizuelne tokens (CSS variables strategija treba odluka u sledećim koracima)
- `EXPERIENCE.md` kao izvor za behavioral patterns (HTMX feedback, slider keyboard pause, accordion ARIA)

### Cross-Cutting Concerns Identified

1. **i18n prožima sve slojeve** — model (`django-modeltranslation`), URL routing (locale prefix), templates (switcher + `<html lang>` atribut), SEO (hreflang per strana), forme (lokalizovani subject email-ova)
2. **GDPR-conditional tracking** — kolačić consent → aktivacija GA + FB Pixel (post-consent samo). Treba consent state management.
3. **Media pipeline** — slike (responsive srcset, masonry, Lightbox), PDF (brošure + katalozi + cover-thumbnail render za UI)
4. **Admin RBAC** — Superadmin / Editor uloga; svi CRUD-ovi proveravaju permisije
5. **Lead-gen flow** — 4 forme različitih shape-ova → SMTP email + dashboard count segmentovan po vrsti
6. **HTMX consistency** — svaka dinamička izmena mora da pošalje aria-live obaveštenje, partial templates moraju da budu izolovani i renderabilni nezavisno
7. **Search across content types** — proizvodi + blog objave u jednom indeksu, locale-aware ranking

## Starter Template Evaluation

### Primary Technology Domain

Full-stack web — Django MVT + PostgreSQL + HTMX server-rendered partials. Tech stack je **fiksiran** u Brief addendum-u i ne menja se.

### Starter Options Considered

| Option | Verdict |
|---|---|
| **falco-cli** v0.26.5 (Tobi-De) | HTMX-first, uv-based, Docker production, ali Tailwind default — koristimo CLI helper-e, ne template |
| **cookiecutter-django** 2026.20.6 | Battle-tested ali Poetry default (ne uv), heavyweight, mnogo neželjenih opcija (Celery, S3, allauth) |
| **digipodium/django-bootstrap-htmx-template** | Stale (2023), bez uv, bez Docker-a |
| **Manual `uv init` + `django-admin startproject`** | ⭐ Pun control, exact match sa našim stack-om |

### Selected: Manual setup + falco-cli kao dev helper

**Rationale:**

- Naš stack je vrlo specifičan (uv + Bootstrap 5 + Hetzner + 3 environments + django-modeltranslation) — nijedan starter ne pogađa savršeno
- Cookiecutter-django nosi opcionalne kompleksnosti koje su out-of-scope (Celery, S3, allauth)
- falco-cli ima odlične dev helper-e (`falco crud` generiše HTMX CRUD views) ali se može instalirati **kao alat** bez korišćenja template-a
- Manual setup je transparentan i lakši za solo dev-a da razume šta gde radi
- Bootstrap 5 + HTMX kombinacija je dobro pokrivena standardnim Django paketima

**Initialization Command (ide kao prva story u sprint planning-u):**

```bash
# 1. Project init sa uv (Python 3.13+)
uv init coric-agrar --python 3.13
cd coric-agrar

# 2. Add Django + core deps
uv add django>=5.2 psycopg[binary] django-modeltranslation django-htmx \
       django-template-partials django-bootstrap5

# 3. Django project skeleton
uv run django-admin startproject config .

# 4. Dev deps
uv add --dev pytest pytest-django ruff djade pre-commit playwright

# 5. Falco kao globalni dev helper (opciono, za CRUD scaffolding)
uv tool install falco-cli
```

**Architectural Decisions Provided by This Setup:**

- **Language & Runtime:** Python 3.13+, Django 5.2 LTS
- **Package management:** `uv` + `pyproject.toml` kao single source of truth
- **Code quality:** `ruff` (linter + formatter, zamenjuje black + flake8 + isort), `djade` (Django template formatter, zamenjuje djlint za brzinu), `pre-commit` hooks
- **Testing:** `pytest-django` (umesto unittest), `playwright` (E2E)
- **Frontend deps:** `django-bootstrap5` (Bootstrap 5 helper template tags), `django-htmx` (request introspection middleware), `django-template-partials` (reusable HTML fragments — kritično za HTMX response patterns)
- **Task runner:** `just` (zamenjuje Makefile)

**Project structure (detalji u step-04 decisions):**

```text
coric-agrar/
├── config/              # Django settings (split base/dev/staging/prod)
├── apps/                # Django apps (catalog, products, brands, ...)
├── templates/           # Django templates + partials/
├── static/              # CSS, JS, img, fonts
├── locale/              # i18n .po files
├── compose/             # Docker Compose files (local/staging/production)
├── pyproject.toml       # uv-managed
├── manage.py
└── justfile             # task runner
```

**Note:** Project initialization using these commands should be the **first implementation story** u sprint-u (Story 1.1: Project Bootstrap).

## Core Architectural Decisions

### Decision Priority Analysis

**Critical (block implementation):** ORM/i18n storage, auth method, HTMX response patterns, static serving, environment config, database backup
**Important (shape architecture):** Search backend, cache, lightbox, image processing, error tracking, CI/CD
**Deferred (post-MVP):** CDN, Celery worker (samo ako future scale traži), Redis (samo ako cache contention)

### Data Architecture

| Decision | Choice | Rationale |
|---|---|---|
| **ORM & migrations** | Django ORM + manual review pre `migrate` deploy-a | Standard, transparent; review sprečava nehoticne schema promene u prod |
| **i18n storage** | `django-modeltranslation` | Već u Brief addendum-u; field suffix `_sr`, `_hu`, `_en` automatski |
| **Search backend** | PostgreSQL FTS sa `SearchVector` + `SearchRank` | ~100 proizvoda + blog = mala kolekcija; FTS dovoljan, no extra service |
| **Cache strategija** | LocMem (Django default) + `cached_property` na model methods | Solo VPS, single process; Redis je premature za v1 |
| **Session storage** | DB-backed (Django default) | Persistent, jednostavno; admin sessions retke |
| **Image processing** | `sorl-thumbnail` 12.10+ | Battle-tested, lazy generation, srcset helper, manji overhead nego imagekit |

### Authentication & Security

| Decision | Choice | Rationale |
|---|---|---|
| **Auth method** | Django built-in `auth` + custom email-as-username backend | Admin-only, nema customer naloga |
| **Authorization** | Django Groups + `is_staff`/`is_superuser` flag | 2 uloge (Superadmin, Editor) — group-based dovoljno, ne treba object-level |
| **Rate limiting** | `django-ratelimit` na formama + `django-axes` na admin login | App-level kontrola, lakše testirati; nginx kao backup |
| **Session timeout** | 4h (`SESSION_COOKIE_AGE = 14400`) | Potvrđujem PRD §FR-34 assumption |
| **Admin URL** | `/admin-coric/` (custom slug) | Lagana security-through-obscurity protiv bot probe |
| **HTTPS** | Nginx forced HTTPS + Django `SECURE_*` settings + HSTS | Standard hardening |
| **File upload validacija** | Pillow `Image.verify()` + `python-magic` za PDF MIME check | Dvostruka provera (signature + MIME) |
| **CSP** | Django defaults + Content-Security-Policy header via `django-csp` | XSS hardening |

### API & Communication Patterns

| Decision | Choice | Rationale |
|---|---|---|
| **Public API** | Nema u v1 | PRD § 9 Non-Goals |
| **HTMX response patterns** | `django-template-partials` + `hx-swap-oob` za aria-live region | Reusable fragmenti; live region za screen reader announcement |
| **Email transport (SMTP)** | **Resend** (primarni) ILI **Brevo** (alt, besplatan 300/dan, EU servers) | Resend ima najlepši DX; Brevo dobra rezerva za GDPR-strict scenario |
| **Email helper** | `django-anymail` | Abstraction nad providerima; lakše menjati kasnije |
| **Email templates** | Django templates + plain inheritance | Solo dev, no extra abstraction |
| **Error handling** | `SuspiciousOperation` chains + **GlitchTip 6** (self-host) | Vidi Infrastructure |

### Frontend Architecture

| Decision | Choice | Rationale |
|---|---|---|
| **CSS strategy** | Bootstrap 5 (CDN dev, local prod) + custom CSS + DESIGN.md tokens kao CSS Custom Properties | Token-driven, no build pipeline |
| **CSS token system** | CSS Custom Properties (`--color-brand-green-800: #25402f;`) u `:root` | Native, runtime-mutable, perfect mapping DESIGN.md tokens |
| **JavaScript** | Vanilla JS + HTMX + male targeted lib-e | Bez build pipeline-a; Alpine.js opcionalno za stateful komponente |
| **Lightbox biblioteka** | **GLightbox** 3.x (10 KB gzipped) | Lightweight, full a11y, video support kao bonus |
| **Vremenska lenta** | SVG inline + CSS + `IntersectionObserver` za reveal | Već UX odluka; minimal weight |
| **Animacije** | CSS transitions/animations + `IntersectionObserver` za count-up | No external lib; reduced-motion-respect built-in |
| **Static files serving** | Whitenoise sa compressed manifest + Nginx fallback za media | Whitenoise simplifikuje static; manifest cache-busting |
| **Font loading** | Self-hosted Roboto subset (latin + latin-ext za sr/hu), `font-display: swap` | GDPR-friendly (no GFonts CDN), brži FCP |
| **PDF cover-thumbnail** | `pdf2image` (poppler) sync task pri admin upload-u | Generate-once, store kao image; no runtime overhead |
| **Image srcset** | `sorl-thumbnail` `{% thumbnail %}` template tag + responsive `<picture>` element | Standard pattern |

### Infrastructure & Deployment

| Decision | Choice | Rationale |
|---|---|---|
| **CI/CD** | GitHub Actions (free tier 2000 min/mo) | Standard; free za solo dev |
| **Container registry** | GitHub Container Registry (GHCR) | Free; isti login kao Actions |
| **Hosting** | Hetzner CX22 (staging) + CX32 (production) | Iz Brief addendum-a; right-sized |
| **Reverse proxy** | Nginx | Iz Brief stack-a; battle-tested |
| **SSL** | `certbot` + Nginx auto-renewal cron | Standard Let's Encrypt setup |
| **Database backup** | `pg_dump` cron job → Hetzner Storage Box (encrypted), retencija **30 dana** | Affordable, off-host, EU storage (GDPR) |
| **Monitoring (uptime)** | UptimeRobot free tier (50 monitors / 5 min) | Dovoljno za 3 env |
| **Error tracking** | **GlitchTip 6** self-host na istoj/zasebnoj VPS (Docker, 512 MB RAM) | EU sovereignty, no per-event limits, ~3 € marginalni trošak; alt: Sentry free 5K/mo |
| **Logging** | Django logging → JSON na fajl + `logrotate` 14d retencija | Standard, no overhead |
| **Performance budget** | LCP < 2.5s, TTFB < 600ms, total page weight < 1.5 MB na 3G/4G | Conservative targets za rural agro public |
| **CDN** | None za v1 | Regionalni traffic, Hetzner EU latencija dovoljna |
| **Environment config** | `django-environ` (`.env` files per env) | Standard, type-safe parsing |
| **Secret management** | env vars iz Hetzner Cloud secrets panel + Docker secrets | Solo dev, manage-by-hand OK |

### Decision Impact Analysis

**Implementation Sequence (preporuka za sprint plan):**

1. Project bootstrap (uv init + django startproject) — Story 1.1
2. Settings split + django-environ — Story 1.2
3. Docker compose (local + production) — Story 1.3
4. Core models (Brand, Category, Product) sa modeltranslation — Story 1.4
5. Base templates + CSS Custom Properties + Bootstrap 5 + HTMX setup — Story 1.5
6. i18n routing (locale prefix middleware) — Story 1.6
7. Admin panel scaffolding (Superadmin/Editor groups) — Story 1.7
8. Public katalog: listing + detail templates — Epic 2
9. Lead-gen forme + email transport — Epic 3
10. Search backend + filteri — Epic 4
11. Blog — Epic 5
12. GDPR baner + tracking pixel toggle — Epic 6
13. SEO modul + redirect manager — Epic 7
14. CI/CD pipeline + bekap setup — Epic 8
15. Polish, performance, accessibility audit — Epic 9

**Cross-Component Dependencies:**

- **i18n routing** → svi templates + svi modeli + svi URL-ovi (kreiraj rano)
- **GDPR consent** → GA/FB Pixel aktivacija (cascade kroz template `base.html`)
- **DESIGN.md tokens → CSS Custom Properties** → svaka komponenta (svaka kasnija story zavisi)
- **django-template-partials + HTMX patterns** → svaka view koja koristi HTMX swap mora pratiti pattern
- **GlitchTip self-host** → dodatni Docker servis u compose, nije blocker za prvi launch ali brzo nakon

## Implementation Patterns & Consistency Rules

### Conflict Points Identified

7 oblasti gde implementacija može da se razlikuje između dev iteracija (ili između solo dev-a i AI agent-a): naming, struktura, format, HTMX response, error handling, loading states, i18n process.

### Naming Patterns

**Database (Django ORM defaults preserved):**

| Element | Pattern | Primer |
|---|---|---|
| Tabele | `appname_modelname` (Django default, lowercase + underscore) | `products_product`, `brands_brand`, `forms_servicerequest` |
| Kolone | `snake_case` | `created_at`, `published_status`, `is_featured` |
| Foreign keys | `<relation>` field name, DB column dobija `_id` suffix automatski | `brand = FK(Brand)` → DB `brand_id` |
| Indexes | `<table>_<column>_idx` | `products_product_slug_idx` |
| Translated fields | Suffix `_sr`, `_hu`, `_en` (modeltranslation default) | `title_sr`, `title_hu`, `title_en` |

**Python kod:**

| Element | Pattern | Primer |
|---|---|---|
| Klase | `PascalCase` | `Product`, `BrandViewSet`, `ServiceRequestForm` |
| Funkcije / metode | `snake_case` | `get_active_products`, `render_partial` |
| Konstante | `UPPER_SNAKE_CASE` | `MAX_UPLOAD_SIZE`, `DEFAULT_LOCALE` |
| Privatne | leading `_` | `_internal_helper` |
| Django views | `<Resource><Action>View` (CBV) ili `<resource>_<action>` (FBV) | `ProductListView` ili `product_list` |
| Forms | `<Resource>Form` | `ContactForm`, `ServiceRequestForm` |
| Signals | `<resource>_<event>` | `product_published`, `lead_received` |

**Templates & URLs:**

| Element | Pattern | Primer |
|---|---|---|
| Template fajlovi | `kebab-case.html` | `product-detail.html`, `brand-card.html` |
| Template direktorijumi | `<app>/` | `templates/products/`, `templates/brands/` |
| HTMX partials | `partials/<entity>_<action>.html` | `partials/product_card.html`, `partials/filter_results.html` |
| URL paths | `kebab-case` ili descriptive Serbian | `/o-nama/`, `/proizvod/<slug>/`, `/mehanizacija/prikljucna/` |
| URL names (reverse) | `<app>:<action>` namespace | `products:detail`, `forms:contact_submit` |
| Slug-ovi | `kebab-case`, lowercase, ASCII transliteration | `agri-tracking-tb804` (ne `agri_tracking_tb804`) |

**CSS:**

| Element | Pattern | Primer |
|---|---|---|
| Custom classes | `kebab-case` BEM-like (Block__Element--Modifier) | `.product-card`, `.product-card__title`, `.product-card--featured` |
| CSS Custom Properties | `--<group>-<name>-<variant>` (matchuje DESIGN.md tokens) | `--color-brand-green-800`, `--spacing-scale-4`, `--rounded-pill` |
| Utility (Bootstrap) | kept as-is | `.d-flex`, `.gap-3`, `.text-center` |
| Component scope | prefix `coric-` na custom-e da izbegne Bootstrap clash | `.coric-hero-overlay`, `.coric-stat-medallion` |

**JavaScript:**

| Element | Pattern | Primer |
|---|---|---|
| Funkcije / varijable | `camelCase` | `initLightbox`, `updateAriaLive` |
| Konstante | `UPPER_SNAKE_CASE` | `HTMX_TIMEOUT_MS` |
| Module fajlovi | `kebab-case.js` | `lightbox-init.js`, `statistic-counter.js` |
| Custom events | `coric:<event>` namespace | `coric:filter-applied`, `coric:lightbox-open` |

### Structure Patterns

**Project layout (detalji u step-06):**

```text
coric-agrar/
├── apps/                          # SVI Django apps idu ovde, ne u root
│   ├── catalog/                   # Listing + search funkcije (cross-domain)
│   ├── products/                  # Product model + variants
│   ├── brands/                    # Brand + Serija + Category models
│   ├── blog/                      # Blog (Priče sa polja)
│   ├── forms/                     # 4 lead-gen forme
│   ├── seo/                       # Meta, sitemap, redirects
│   ├── gdpr/                      # Cookie consent, tracking activation
│   ├── accounts/                  # Auth + RBAC ekstenzije
│   ├── media_pipeline/            # Image + PDF processing helpers
│   └── core/                      # Shared utilities, base models, mixins
├── config/                        # Project settings (ne `coric_agrar/` ili `project/`)
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   ├── staging.py
│   │   └── production.py
│   ├── urls.py
│   └── wsgi.py
├── templates/                     # GLOBAL templates (project-wide)
├── static/                        # CSS, JS, fonts, img
├── locale/                        # i18n .po files (sr/hu/en)
├── media/                         # User uploads (Docker volume)
├── compose/                       # Docker Compose files per environment
├── ops/                           # Deployment scripts, nginx configs, backup
├── tests/                         # Cross-app integration tests
├── pyproject.toml
└── justfile
```

**Test layout:**

- **Unit tests:** `apps/<app>/tests/test_<module>.py` (kolokovani uz app)
- **Integration tests:** `tests/<feature>/`
- **E2E tests (Playwright):** `tests/e2e/`
- **Pytest discovery:** `pyproject.toml` config sa `testpaths = ["apps", "tests"]`

### Format Patterns

**Datum/vreme:**

| Kontekst | Format | Primer |
|---|---|---|
| DB storage | UTC ISO 8601 (Django default) | `2026-05-27T14:23:00Z` |
| UI display SR | `DD.MM.YYYY.` | `27.05.2026.` |
| UI display HU | `YYYY.MM.DD.` | `2026.05.27.` |
| UI display EN | `MMM DD, YYYY` | `May 27, 2026` |
| Vreme uvek | 24h format (`HH:MM`) | `14:23` |

**Brojevi:**

| Tip | Format SR | Primer |
|---|---|---|
| Cena EUR | `€ XX.XXX` (tačka kao thousands separator) | `€ 25.000` |
| Konjska snaga | `XX KS` | `60 KS` |
| Dimenzije | `XXXX mm` | `4035 mm` |
| Zapremina | `X m³` ili `X kubika` | `6 m³` |

**Slug-ovi (URL paths):**

- ASCII transliteration sa srpskih dijakritika (`Ć → c`, `Č → c`, `Š → s`, `Ž → z`, `Đ → d`)
- Lowercase, kebab-case, bez stop words
- Django-autoslug ili custom slug field koji koristi `unidecode`

### Communication Patterns (HTMX)

**Endpoint convention:**

| Patern | Primer |
|---|---|
| Standardni URL | `GET /proizvodi/<slug>/` |
| HTMX-specific | `GET /htmx/products/filter/` (samo kad endpoint isključivo služi HTMX request-ima) |
| Detect | `HtmxMiddleware` (django-htmx) → request.htmx je truthy, view bira template |

**Response patterns:**

| Akcija | Response | aria-live |
|---|---|---|
| Filter update | `partials/product_grid.html` (samo grid kontejner) | `<div hx-swap-oob="innerHTML:#aria-live">Pronađeno 12 rezultata</div>` |
| Form submit success | `partials/form_success.html` (zameni form-u) | `<div hx-swap-oob="...">Forma poslata</div>` |
| Form submit error | `partials/form_with_errors.html` (rerender) | `aria-live="assertive"` summary iznad |
| Search dropdown | `partials/search_results.html` | `<div hx-swap-oob="...">5 predloga</div>` |

**HTMX headers convention:**

- Custom headers: `HX-<Name>` (django-htmx prefix)
- Trigger custom event po response-u: `HX-Trigger: coric:filter-applied`
- Redirect: `HX-Redirect: /sr/proizvodi/`

### Process Patterns

**Error handling:**

| Layer | Pattern |
|---|---|
| View-level | Try/except sa specific exceptions; raise `Http404` ili `PermissionDenied` |
| HTMX form error | Return form sa `aria-invalid` polja + summary u aria-live |
| Network/timeout | Generic poruka u aria-live + `htmx:responseError` event listener |
| 500 errors | Custom `500.html` (no DB queries) + GlitchTip capture |
| 404 errors | Custom `404.html` per locale sa suggested links |
| Form validation | Django form validation + locale-aware messages (gettext) |

**Loading states:**

- HTMX dugmadi: `htmx-indicator` class sa Bootstrap spinner
- Element prelazi u `aria-busy="true"` automatski
- Min loading time: 200ms (sprečava flicker za brze response-e); `htmx.config.timeout = 10000`

**Validation:**

- **Trigger:** na `blur` event polja (`hx-trigger="blur"`)
- **Server-side validation** je SOT; client-side HTML5 validacija je samo UX layer
- **Error rendering:** Django form errors → inline pod poljem + `aria-describedby` link

**i18n process:**

- Strings u kodu: `gettext_lazy` import as `_` za model/form fields, `gettext` za view runtime
- Template strings: `{% translate "..." %}` ili `{% blocktranslate %}`
- Workflow: `just makemessages` → translator unosi prevode → `just compilemessages` lokalno + CI

**Migration process:**

1. `python manage.py makemigrations <app>`
2. **Manual review** generated migration file
3. Test sa `python manage.py migrate --plan`
4. Commit migracija + model promene zajedno
5. U prod-u: `migrate` korak u deploy pipeline-u

### Enforcement Guidelines

**Sve buduće implementacije MORAJU:**

1. Slug-ovi ASCII transliteration; nigde Unicode u URL-u
2. Svaki novi model proširen sa `TranslationOptions` u `apps/<app>/translation.py` ako ima translatable polja
3. Svaki HTMX endpoint ima par-partial template + aria-live announcement
4. CSS custom vrednosti samo kroz CSS Custom Properties (`var(--color-...)`) — nikad inline magic numbers
5. Datum prikazi kroz `{% load humanize %}` ili custom `{% locale_date %}` template tag
6. SR latinica u kodu, srpski (latinica) u UI strings; nikad ćirilica
7. Migracije manually reviewed pre commit-a — nikad auto-applied bez review-a
8. Forme: HTMX `hx-post` + django-ratelimit + CSRF token uvek

**Pattern enforcement automatika:**

- `ruff` linter sa custom config (line length 100, naming conventions)
- `djade` Django template formatter
- `pre-commit` hooks na svaki commit
- GitHub Actions CI fail na lint/test/typing error
- Konvencija review checklist u svakom PR-u (čak i solo, kao self-review template)

### Pattern Examples

**Good:**

```python
# apps/products/models.py
class Product(models.Model):
    slug = models.SlugField(max_length=200, unique=True, db_index=True)
    brand = models.ForeignKey("brands.Brand", on_delete=models.PROTECT, related_name="products")
    name = models.CharField(max_length=200)  # translatable
    description = models.TextField(blank=True)  # translatable
    is_published = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["is_published", "-created_at"], name="products_product_pub_created_idx"),
        ]

    def get_absolute_url(self):
        return reverse("products:detail", kwargs={"slug": self.slug})
```

```html
<!-- templates/products/partials/product_card.html -->
{% load thumbnail i18n %}
<article class="coric-product-card" data-product-id="{{ product.id }}">
  {% thumbnail product.main_image "400x300" crop="center" as thumb %}
    <img src="{{ thumb.url }}" alt="{{ product.name }}" loading="lazy">
  {% endthumbnail %}
  <h3 class="coric-product-card__title">{{ product.name }}</h3>
  <a class="btn btn-primary" href="{{ product.get_absolute_url }}">{% translate "OPŠIRNIJE" %}</a>
</article>
```

**Anti-patterns (ne raditi):**

```python
# ❌ Camel case for Python
class productCard(models.Model):  # treba PascalCase
    Slug = models.SlugField()      # treba snake_case + lowercase

# ❌ Inline CSS / magic numbers
<div style="color: #25402f; padding: 32px;">  <!-- use tokens i CSS classes -->

# ❌ Ćirilica u kodu
naziv = "Ћорић Аграр"  # uvek latinica

# ❌ Skipping aria-live na HTMX swap
return HttpResponse(rendered_partial)  # nedostaje aria-live OOB

# ❌ Skipping i18n
return JsonResponse({"message": "Operation successful"})  # treba gettext_lazy
```

## Project Structure & Boundaries

### Complete Project Tree

```text
coric-agrar/
│
├── pyproject.toml                          # uv-managed deps + project metadata
├── uv.lock                                 # uv lock fajl
├── manage.py
├── justfile                                # task runner (init, run, test, lint, deploy, makemessages)
├── README.md                               # quickstart za solo dev
├── .gitignore
├── .editorconfig
├── .pre-commit-config.yaml                 # ruff + djade hooks
├── .python-version                         # uv pinned (3.13)
├── .env.example                            # template za .env (NIKAD ne komituj .env)
│
├── .github/
│   └── workflows/
│       ├── ci.yml                          # lint + test + build na svaki push
│       └── deploy.yml                      # deploy to Hetzner na main branch push
│
├── apps/                                   # SVE Django apps (ne na root)
│   ├── core/                               # Shared base — uvek prvi instaliran
│   │   ├── models.py                       # TimestampedModel, SluggedModel, PublishableModel
│   │   ├── mixins.py                       # ListViewMixin, LocaleAwareViewMixin
│   │   ├── managers.py                     # PublishedManager
│   │   ├── templatetags/
│   │   │   ├── coric_format.py             # {% locale_date %}, {% currency %} filteri
│   │   │   └── htmx_aria.py                # {% aria_live %} template tag
│   │   ├── middleware.py                   # LocaleSwitcherMiddleware, HtmxAriaMiddleware
│   │   ├── utils.py                        # slugify ASCII transliteration, etc.
│   │   └── tests/
│   ├── accounts/                           # Auth + RBAC ekstenzije (FR-34, FR-41)
│   │   ├── models.py                       # ExtendedUser proxy (samo ako treba)
│   │   ├── forms.py                        # AdminLoginForm
│   │   ├── views.py                        # Custom login view sa rate limit
│   │   ├── permissions.py                  # IsEditor, IsSuperadmin checks
│   │   └── migrations/
│   ├── brands/                             # Brand + Series + Category + Subcategory (FR-7, FR-37, FR-38)
│   │   ├── models.py                       # Brand, Series, Category, Subcategory
│   │   ├── admin.py                        # BrandAdmin (hero image, statistike, color picker)
│   │   ├── translation.py                  # name_sr/_hu/_en, description, slogan
│   │   ├── views.py                        # BrandDetailView (statistike, modeli grupisani po serijama)
│   │   ├── urls.py                         # /traktori/<brand-slug>/
│   │   └── managers.py                     # ActiveBrandManager
│   ├── products/                           # Product + ProductVariant + ProductSpecification (FR-14-21, FR-36, FR-48)
│   │   ├── models.py                       # Product, ProductVariant, ProductImage, ProductBrochure, ProductTestimonial
│   │   ├── admin.py                        # ProductAdmin sa galerija upload, specs editor, varijante inline
│   │   ├── translation.py                  # name, description, key_features
│   │   ├── views.py                        # ProductDetailView
│   │   ├── urls.py                         # /proizvod/<slug>/
│   │   ├── managers.py                     # PublishedProductManager
│   │   └── signals.py                      # product_published → cache invalidation, sitemap re-gen
│   ├── catalog/                            # Listing + filters + search (FR-6, FR-8-13, FR-27)
│   │   ├── views.py                        # TractorListView, MechanizationListView, UsedListView, SearchView
│   │   ├── urls.py                         # /traktori/, /mehanizacija/, /pretraga/, /htmx/filter/
│   │   ├── filters.py                      # django-filter form klase
│   │   ├── search.py                       # PostgreSQL FTS query helpers
│   │   └── pagination.py
│   ├── pages/                              # Statičke strane (Home, O nama, Kontakt) (FR-1-5, FR-40, FR-45)
│   │   ├── models.py                       # Page, HomeSection, AboutTimelineEvent, GalleryImage, SiteSettings
│   │   ├── admin.py                        # PageAdmin sa WYSIWYG, sekcija upravljanje
│   │   ├── translation.py
│   │   ├── views.py                        # HomeView, AboutView, ContactView
│   │   ├── urls.py                         # /, /o-nama/, /kontakt/
│   │   └── templatetags/site_settings.py
│   ├── forms/                              # 4 lead-gen forme (FR-5, FR-19, FR-22, FR-23)
│   │   ├── models.py                       # Lead (sa form_type discriminator), ServiceRequest, PartRequest
│   │   ├── forms.py                        # ContactForm, ModelInquiryForm, ServiceRequestForm, PartRequestForm
│   │   ├── views.py                        # HTMX submit views
│   │   ├── urls.py                         # /htmx/forme/kontakt/, /htmx/forme/upit-model/
│   │   ├── admin.py                        # LeadAdmin (read-only listing po form_type)
│   │   └── notifications.py                # send_lead_email helper (sync)
│   ├── blog/                               # Priče sa polja (FR-24-26, FR-39)
│   │   ├── models.py                       # Post, Category, Tag, PostImage
│   │   ├── admin.py                        # PostAdmin sa WYSIWYG
│   │   ├── translation.py                  # title, perex, body
│   │   ├── views.py                        # PostListView, PostDetailView, CategoryView, TagView
│   │   └── urls.py
│   ├── seo/                                # Meta, sitemap, redirect manager (FR-42-44)
│   │   ├── models.py                       # SeoMeta (generic FK), Redirect
│   │   ├── sitemaps.py                     # Kombinovani sitemap sa hreflang
│   │   ├── middleware.py                   # RedirectMiddleware (301 handler)
│   │   ├── views.py                        # robots.txt, sitemap.xml endpoints
│   │   └── templatetags/
│   │       ├── seo_meta.py                 # {% seo_meta page %}
│   │       └── hreflang.py                 # {% hreflang_links %}
│   ├── gdpr/                               # Cookie consent + tracking activation (FR-47)
│   │   ├── models.py                       # CookiePolicy
│   │   ├── views.py                        # SetConsentView
│   │   ├── templatetags/
│   │   │   ├── gdpr_banner.py
│   │   │   └── tracking.py                 # {% ga_pixel %}, {% fb_pixel %} sa consent check
│   │   └── context_processors.py           # consent_state u svaki template
│   ├── admin_ext/                          # Admin Dashboard, brze akcije, statistike (FR-35)
│   │   ├── views.py                        # DashboardView (replaces Django admin index)
│   │   ├── analytics.py                    # GA Reporting API client
│   │   └── stats.py                        # Lead count po form_type
│   └── media_pipeline/                     # Image + PDF processing (cross-cutting)
│       ├── utils.py                        # generate_pdf_cover_thumbnail, validate_image_mime
│       └── signals.py                      # post_save hook za Product/Brand → thumbnails
│
├── config/                                 # Project settings
│   ├── settings/
│   │   ├── base.py                         # Common settings, INSTALLED_APPS, MIDDLEWARE
│   │   ├── development.py                  # DEBUG=True, console email
│   │   ├── staging.py                      # Production-like, staging URL
│   │   └── production.py                   # DEBUG=False, full security, GlitchTip
│   ├── urls.py                             # Root URLconf, i18n_patterns
│   ├── wsgi.py
│   └── asgi.py
│
├── templates/                              # GLOBAL templates
│   ├── base.html
│   ├── partials/                           # Cross-app partials
│   │   ├── aria_live.html
│   │   ├── header.html
│   │   ├── footer.html
│   │   ├── gdpr_banner.html
│   │   ├── language_switcher.html
│   │   └── repeating_element.html
│   ├── 404.html
│   ├── 500.html
│   ├── 403.html
│   ├── brands/                             # Per-app templates
│   ├── products/
│   ├── catalog/
│   ├── pages/
│   ├── forms/
│   ├── blog/
│   ├── seo/
│   └── emails/                             # Email templates (HTML + TXT)
│
├── static/                                 # Static assets
│   ├── css/
│   │   ├── tokens.css                      # CSS Custom Properties iz DESIGN.md
│   │   ├── base.css                        # Reset + typography
│   │   ├── layout.css
│   │   └── components/                     # Per-komponenta CSS
│   ├── js/
│   │   ├── lightbox-init.js                # GLightbox setup
│   │   ├── statistic-counter.js            # IntersectionObserver count-up
│   │   ├── timeline-reveal.js              # SVG timeline animation
│   │   ├── slider.js                       # Testimonijali (sa pause/play)
│   │   ├── sticky-nav.js                   # Shrink-on-scroll
│   │   ├── search-expand.js
│   │   └── htmx-aria.js                    # aria-live updates listener
│   ├── fonts/roboto/                       # Self-hosted Roboto subset
│   ├── img/
│   └── vendor/                             # Lokalni Bootstrap 5 + HTMX + GLightbox
│
├── locale/                                 # i18n .po files (sr/hu/en)
├── media/                                  # User uploads (Docker volume)
├── compose/                                # Docker Compose files
│   ├── local.yml
│   ├── staging.yml
│   ├── production.yml
│   ├── django/
│   │   ├── Dockerfile                      # Multi-stage uv build
│   │   ├── entrypoint.sh
│   │   └── start.sh
│   └── nginx/
│       ├── Dockerfile
│       └── nginx.conf
│
├── ops/                                    # Deployment & ops scripts
│   ├── backup/
│   │   ├── pg_backup.sh                    # pg_dump → encrypted → Hetzner Storage Box
│   │   ├── media_backup.sh
│   │   ├── restore.sh
│   │   └── crontab.txt
│   ├── deploy/
│   │   ├── deploy.sh
│   │   └── rollback.sh
│   ├── monitoring/glitchtip-compose.yml
│   └── secrets/README.md
│
├── tests/                                  # Cross-app integration + E2E
│   ├── integration/
│   ├── e2e/                                # Playwright (UJ-1, UJ-2, UJ-3)
│   └── fixtures/
│
└── docs/                                   # Project docs (internal)
    ├── ADRs/                               # Architecture Decision Records
    ├── runbook.md                          # Deploy, backup, restore
    └── project-context.md                  # AI agent guidance
```

### Architectural Boundaries

#### App boundaries (dozvoljene zavisnosti)

```text
core ← (everyone imports core)
brands ← products, catalog
products ← catalog, forms, blog (cross-ref)
catalog ← (top-level, koristi brands + products)
forms ← (samostalan, koristi core utilities)
blog ← (samostalan)
seo ← (koristi sve content modele kroz generic FK)
gdpr ← (samostalan, expose context processor)
pages ← (top-level, ima reference na blog za „Najnovije vesti")
accounts ← (samostalan + admin customization)
admin_ext ← (proširuje sve admin-e, top-level)
media_pipeline ← (utility, importovan od products + brands + blog)
```

**Zabranjene zavisnosti:**

- `core` NIKAD ne sme importovati domain apps
- `brands` NIKAD ne sme importovati `products` (jednosmerna — products zavisi od brands)
- `forms` NIKAD ne sme importovati `catalog`/`blog` direktno; context pass-uje se kroz form fields
- Nijedan domain app ne sme importovati iz `admin_ext`

#### Data boundaries

- **Sva data persistencija** kroz Django ORM; nema raw SQL osim u FTS upit
- **Cache:** LocMem default; nikakvi cache key-evi van `apps/<app>/cache.py` modula
- **Sessions:** DB-backed (`django.contrib.sessions.backends.db`)
- **Media:** Lokalni storage u dev, Docker volume u staging/prod; nikakav S3/cloud storage u v1
- **Search index:** PostgreSQL `tsvector` polje na Product, BlogPost (held in DB)

#### Request flow

```text
Request
  ↓
Nginx (HTTPS termination, static fallback)
  ↓
Gunicorn (WSGI)
  ↓
Django middleware chain:
  - SecurityMiddleware
  - WhitenoiseMiddleware (statički fajlovi)
  - LocaleMiddleware (URL prefix → activate locale)
  - HtmxMiddleware (django-htmx detekcija)
  - SessionMiddleware
  - CsrfViewMiddleware
  - AuthMiddleware
  - GdprConsentMiddleware (set consent_state na request)
  - RedirectMiddleware (apps/seo) — 301 deprecated URL handler
  ↓
URLconf (config/urls.py → i18n_patterns → app urls)
  ↓
View (CBV ili FBV u apps/<app>/views.py)
  ↓
Template (templates/<app>/<template>.html ili partials/<partial>.html za HTMX)
  ↓
Response (HTML, sa hx-swap-oob za aria-live ako je HTMX request)
```

#### External integration boundaries

| Service | App location | Boundary type |
|---|---|---|
| **SMTP (Resend/Brevo)** | `apps/forms/notifications.py` | Single point — `django-anymail` apstrakcija |
| **Google Analytics 4** | `apps/gdpr/templatetags/tracking.py` | Conditional render template tag |
| **Facebook Pixel** | `apps/gdpr/templatetags/tracking.py` | Conditional render template tag |
| **Google Maps** | `templates/pages/contact.html` (inline iframe) | Static embed, no JS dep |
| **GlitchTip** | `config/settings/production.py` SDK config | Captures uncaught exceptions automatski |
| **Google Search Console** | Verifikacija meta tag u `templates/base.html` | Read-only — manual log-in van sajta |
| **Hetzner Storage Box** | `ops/backup/pg_backup.sh` (rclone) | Cron-driven, outbound only |

### Requirements → Structure Mapping (Epic-level)

| Epic | FR coverage | Primary directories |
|---|---|---|
| **Epic 1 — Foundation** | Stories 1.1-1.7 (bootstrap) | `config/`, `apps/core/`, `apps/accounts/`, `templates/base.html`, `static/css/tokens.css`, `compose/`, `.github/workflows/ci.yml` |
| **Epic 2 — Public katalog** | FR-1..FR-13, FR-14..FR-21, FR-48 | `apps/brands/`, `apps/products/`, `apps/catalog/`, `apps/pages/` (HomeView), `templates/{brands,products,catalog,pages}/` |
| **Epic 3 — Lead-gen forme** | FR-5, FR-19, FR-22, FR-23 | `apps/forms/`, `templates/forms/partials/`, `templates/emails/` |
| **Epic 4 — Search + filteri** | FR-6, FR-13, FR-27 | `apps/catalog/search.py`, `apps/catalog/filters.py`, `templates/catalog/partials/search_dropdown.html` |
| **Epic 5 — Blog** | FR-24..FR-26, FR-39 | `apps/blog/`, `templates/blog/` |
| **Epic 6 — GDPR + tracking** | FR-47 | `apps/gdpr/`, `templates/partials/gdpr_banner.html` |
| **Epic 7 — SEO + redirect manager** | FR-42, FR-43, FR-44, FR-33 | `apps/seo/`, `templates/seo/meta.html`, `config/urls.py` sitemap |
| **Epic 8 — Admin Dashboard** | FR-34..FR-41, FR-45, FR-46 | `apps/admin_ext/`, `apps/accounts/`, per-app `admin.py` |
| **Epic 9 — Trojezičnost** (kros-epoha) | FR-31..FR-33 | `apps/<app>/translation.py`, `locale/`, `config/settings/base.py` |
| **Epic 10 — Polish** (a11y, performance) | Cross-cutting | Svaki view, template, ARIA, IntersectionObserver, lazy load, srcset |

### Data Flow Diagrams

**Public catalog browsing (UJ-1 Marko):**

```text
Browser → GET /sr/traktori/?konjska_snaga_min=60&cena_max=25000
  → Nginx → Gunicorn → Django
  → LocaleMiddleware activates locale="sr"
  → catalog.TractorListView
  → Filter form parses query params
  → Product.objects.filter(...).select_related("brand").prefetch_related("variants")
  → If HTMX request: render templates/catalog/partials/product_grid.html
    + hx-swap-oob aria-live: "12 rezultata"
  → Else: render templates/catalog/tractors_list.html (full page)
  → HTTP 200 response
```

**Form submission (UJ-2 Stojan):**

```text
Browser → POST /sr/htmx/forme/servisni-zahtev/ (HTMX)
  → forms.ServiceRequestView
  → ServiceRequestForm validation (with django-ratelimit decorator)
  → If valid: Save Lead → notifications.send_lead_email() → django-anymail → Resend
              → Render templates/forms/partials/form_success.html + aria-live OOB
  → If invalid: Render templates/forms/partials/form_with_errors.html
                + aria-live="assertive" iznad forme
```

**Admin product save (UJ-3 Marijana):**

```text
Admin → POST /admin-coric/products/product/add/
  → Django admin view (ProductAdmin)
  → ProductForm validation (sva multi-locale polja)
  → Save Product + ProductImages + ProductVariants
  → post_save signal "product_published" (ako status == Objavljeno)
    → media_pipeline.tasks: generate thumbnails (sync, no Celery)
    → seo.tasks: invalidate sitemap cache
    → cache.delete("products_grid_*")
  → Redirect to changelist
```

### Development Workflow Integration

- **Lokalni dev:** `just dev` → `docker compose -f compose/local.yml up` → `http://localhost:8000`
- **Tests:** `just test` → `pytest -p no:cacheprovider apps tests`
- **Lint:** `just lint` → `ruff check . && djade --check templates/`
- **i18n update:** `just messages` → `makemessages` + `compilemessages`
- **DB migrations:** `just migrate` → `python manage.py migrate --plan` zatim apply
- **Deploy staging:** push na `staging` branch → GitHub Actions deploy.yml → SSH na staging Hetzner box → `ops/deploy/deploy.sh staging`
- **Deploy production:** push na `main` (po PR review-u) → ista mehanika sa production env

## Architecture Validation Results

### Coherence Validation ✅

**Decision Compatibility:**

- Django 5.2 LTS + Python 3.13 — stable, supported until 2028
- Django + PostgreSQL + django-modeltranslation — kanonska kombinacija
- HTMX + django-htmx + django-template-partials — designed-to-work-together stack
- sorl-thumbnail + Pillow + pdf2image (poppler) — sve Pillow-based, coherent media pipeline
- django-anymail + Resend SMTP — abstraction layer omogućava provider swap
- GlitchTip 6 + Sentry SDK protocol — drop-in compatible
- Whitenoise + Nginx + Bootstrap CDN-fallback — clean separation of concerns
- pg_dump + restic + Hetzner Storage Box — outbound, encrypted, EU-resident

**Pattern Consistency:**

- Django defaults preserved (snake_case tabele, PascalCase klase, `app_modelname`)
- BEM-like custom CSS + Bootstrap utility + CSS Custom Properties — non-conflicting
- HTMX patterns (partials + aria-live OOB) konzistentno na svim form/filter endpointima
- Migration process (manual review) — sigurnost iznad brzine

**Structure Alignment:**

- `apps/` layout podržava sve FR-ove kroz domenske app-ove
- Per-app `translation.py` + `locale/` + `LANGUAGES` setting podržava trojezičnost
- Templates `<app>/partials/` patern podržava HTMX response design
- App dependency graph je jednosmerni (no cycles): `core ← brands ← products ← catalog`

### Requirements Coverage Validation ✅

**48 FR-ova mapirano na arhitektonske komponente:**

| FR opseg | Pokrivenost |
|---|---|
| FR-1..FR-5 (Početna + statičke strane) | `apps/pages/` + templates |
| FR-6..FR-13 (Katalog traktora + mehanizacije) | `apps/catalog/` + `apps/brands/` + `apps/products/` |
| FR-14..FR-21, FR-48 (Stranica proizvoda + varijante) | `apps/products/` + `apps/media_pipeline/` |
| FR-22, FR-23 (Servis forme) | `apps/forms/` |
| FR-24..FR-26 (Blog) | `apps/blog/` |
| FR-27..FR-30 (Pretraga + nav + footer) | `apps/catalog/search.py` + `templates/partials/` + dinamički footer iz `apps/blog/` |
| FR-31..FR-33 (Trojezičnost) | `django-modeltranslation` + `i18n_patterns` + `apps/seo/templatetags/hreflang.py` |
| FR-34..FR-41 (Admin sadržaj + pristup) | `apps/accounts/` + `apps/admin_ext/` + per-app `admin.py` |
| FR-42..FR-44 (SEO admin) | `apps/seo/` |
| FR-45..FR-47 (Podešavanja sajta + GDPR) | `apps/pages/SiteSettings` + `apps/gdpr/` |

**NFR coverage (PRD § 5):**

- **Performance** (LCP < 2.5s, TTFB < 600ms) — Whitenoise compression, lazy loading, srcset, no JS framework overhead ✓
- **WCAG 2.1 AA** — aria-live patterns u HTMX flow, focus management, alt text, ARIA atributi ✓
- **Sigurnost** — Django auth + bcrypt/argon2, CSRF, django-ratelimit, MIME validacija, HTTPS, CSP via django-csp ✓
- **SEO** — sitemap.xml gen, hreflang, robots, semantic HTML, OG/Twitter meta ✓
- **Reliability** — pg_dump cron + 30d retention + restic encrypted off-host ✓
- **Browser podrška** — Modern evergreen (Bootstrap 5 + HTMX 1.9+ podržavaju) ✓

### Implementation Readiness Validation ✅

**Decision Completeness:**

Sve 11 originalnih open decisions iz PRD § 12 razrešeno:

- SMTP = Resend (alt Brevo)
- Search = PostgreSQL FTS
- Lightbox = GLightbox 3.x
- Performance budget = LCP < 2.5s, TTFB < 600ms
- Image processing = sorl-thumbnail 12.10+
- Monitoring = UptimeRobot + GlitchTip 6 self-host
- Bekap retencija = 30 dana
- Vremenska lenta = SVG/CSS-only + IntersectionObserver
- PDF cover-thumbnail = pdf2image (poppler) sync pri upload-u
- HTMX aria-live = django-template-partials + `hx-swap-oob`
- CSS token system = CSS Custom Properties u `:root`

**Structure Completeness:**

- Pun projekt tree definisan do file-level detalja
- 12 Django app-ova jasno razgraničena, sa dependency rules
- 5 external integration boundary-ja dokumentovana

**Pattern Completeness:**

- 7 conflict-point oblasti pokriveno (naming, struct, format, HTMX, errors, loading, i18n)
- Konkretni primeri za good vs anti-patterns dati
- Enforcement automatika (ruff, djade, pre-commit, CI) definisana

### Gap Analysis Results

**Critical Gaps:** **None found.** Sve što je potrebno za prvi sprint je definisano.

**Important Gaps (ne blokiraju, ali zaslužuju attention):**

1. **FR-46 Navigation meni admin** — trenutno nije eksplicitno odlučeno da li je menu statički u kodu ili dinamičan kroz `NavigationItem` model. **Preporuka:** statički u v1, dinamičan u v1.1 (kao tech debt).
2. **Performance targets** su konzervativna pretpostavka — treba **load test posle staging deploy-a** da se verifikuju.
3. **Search ranking algoritam** — PostgreSQL FTS sa `SearchRank` odlučeno, ali konkretni weight-evi (title vs body, recency tie-break) treba tune-ovati posle sample podataka.

**Nice-to-Have Gaps (defer do v1.1+):**

- **Celery worker** — sve trenutne async potrebe su sync-friendly; dodati ako bulk email zatreba
- **Redis cache** — LocMem dovoljan za solo VPS; dodati ako contention
- **CDN** — premature; Hetzner EU latencija dovoljna za regionalni traffic
- **WebP/AVIF** image format — dodati u Polish epic
- **Audit log** za admin akcije — Django admin ima built-in `LogEntry`; custom audit nije u PRD-u

### Architecture Completeness Checklist

**Requirements Analysis**
- [x] Project context thoroughly analyzed
- [x] Scale and complexity assessed
- [x] Technical constraints identified
- [x] Cross-cutting concerns mapped

**Architectural Decisions**
- [x] Critical decisions documented with versions
- [x] Technology stack fully specified
- [x] Integration patterns defined
- [x] Performance considerations addressed

**Implementation Patterns**
- [x] Naming conventions established
- [x] Structure patterns defined
- [x] Communication patterns specified
- [x] Process patterns documented

**Project Structure**
- [x] Complete directory structure defined
- [x] Component boundaries established
- [x] Integration points mapped
- [x] Requirements to structure mapping complete

**Rezultat: 16/16 checked**

### Architecture Readiness Assessment

**Overall Status:** **READY WITH MINOR GAPS** — sve critical i important checklist stavke pokrivene; manji gaps (FR-46 nav admin, performance fine-tune) ne blokiraju start sprint-a.

**Confidence Level:** **HIGH** — comprehensive coverage, kompatibilan tech stack, jasni patterns, well-mapped FR-ovi na arhitekturu.

**Key Strengths:**

1. Fiksiran, koherentan tech stack (Django 5.2 + HTMX + Bootstrap 5) — proven combo
2. Domain-driven app decomposition (12 app-ova sa jasnim dependency grafom) — sprečava future coupling
3. HTMX-first interakcioni model — bez build pipeline-a, brži dev loop
4. Token-driven CSS preko CSS Custom Properties matchuje DESIGN.md 1:1
5. A11y built-in — aria-live OOB patterns nisu after-thought
6. Solo-dev friendly — no Celery/Redis ako ne treba; LocMem cache, sync tasks
7. EU-resident infrastruktura (Hetzner + Storage Box + GlitchTip self-host) — GDPR-clean

**Areas for Future Enhancement:**

- Dinamički navigation menu admin (FR-46 ekstenzija) → v1.1
- Background tasks via Celery + Redis → ako future scale traži
- CDN (Cloudflare ili BunnyCDN) → ako traffic ekspanduje
- WebP/AVIF image formats → Polish epic
- Custom audit log za admin akcije → ako compliance traži

### Implementation Handoff

**AI Agent Guidelines:**

- Pratiti sve arhitektonske odluke striktno onako kako su dokumentovane
- Koristiti implementacione patterns konzistentno kroz sve komponente — naming, structure, HTMX, error, i18n
- Poštovati app boundaries iz § Architectural Boundaries (zabranjene zavisnosti)
- Referencirati ovaj dokument za sva arhitektonska pitanja
- Pre svake nove vrste komponente: provera da li je već definisan pattern u § Implementation Patterns

**First Implementation Priority (Story 1.1 — Project Bootstrap):**

```bash
# 1. Project init
uv init coric-agrar --python 3.13
cd coric-agrar

# 2. Add Django + core deps
uv add django>=5.2 psycopg[binary] django-modeltranslation django-htmx \
       django-template-partials django-bootstrap5 django-environ \
       django-anymail django-ratelimit django-axes django-csp \
       sorl-thumbnail pdf2image python-magic

# 3. Django project skeleton
uv run django-admin startproject config .

# 4. Dev deps
uv add --dev pytest pytest-django ruff djade pre-commit playwright \
              django-debug-toolbar

# 5. Falco kao globalni dev helper
uv tool install falco-cli
```
