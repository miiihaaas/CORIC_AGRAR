---
project_name: 'CORIC_AGRAR'
user_name: 'Mihas'
date: '2026-05-27'
sections_completed: ['technology_stack', 'language_python', 'framework_django_htmx', 'testing', 'code_quality_style', 'workflow', 'critical_dont_miss']
status: 'complete'
optimized_for_llm: true
existing_patterns_found: 7
source_documents:
  - _bmad-output/planning-artifacts/architecture.md
  - pyproject.toml
---

# Project Context for AI Agents — Ćorić Agrar

_Ovaj fajl sadrži kritična pravila i patterne koje AI agenti MORAJU da slede pri implementaciji koda. Fokus je na neočiglednim detaljima koje agenti lako previde. Za detaljne arhitektonske odluke konsultuj `_bmad-output/planning-artifacts/architecture.md`._

**Komunikacija:** Srpski (latinica). UI strings: srpski (latinica) — **NIKAD ćirilica**.

---

## Technology Stack & Versions

### Core runtime
- **Python** `>=3.13` (pinned u `.python-version`)
- **Django** `>=5.2,<6.0` (LTS — supported do 2028)
- **PostgreSQL** (verzija via Docker image — preporuka 16+)

### Django ekosistem (production deps — sve u `pyproject.toml`)
- `psycopg[binary] >= 3.3.4` — PostgreSQL adapter (NE `psycopg2`)
- `django-modeltranslation >= 0.20.3` — i18n na model nivou (suffix `_sr/_hu/_en`)
- `django-htmx >= 1.27.0` — HTMX middleware + request introspection
- `django-template-partials >= 25.3` — reusable HTML fragments (kritično za HTMX swap)
- `django-bootstrap5 >= 26.2` — Bootstrap 5 template tags
- `django-environ >= 0.13.0` — `.env` parsing (NE `python-dotenv`)
- `django-anymail >= 15.0` — SMTP abstraction (provider: Resend primarni / Brevo alt)
- `django-ratelimit >= 4.1.0` — rate limit na formama
- `django-axes >= 8.3.1` — brute-force protection na admin login
- `django-csp >= 4.0` — Content Security Policy

### Media pipeline
- `sorl-thumbnail >= 13.0.0` — image thumbnails + srcset (NE `easy-thumbnails`, NE `imagekit`)
- `pdf2image >= 1.17.0` — PDF cover thumbnail (zahteva system `poppler-utils`)
- `python-magic >= 0.4.27` — MIME validacija (zahteva system `libmagic`)

### Dev tooling (sve u `dependency-groups.dev`)
- `ruff >= 0.15.14` — linter + formatter (zamenjuje black + flake8 + isort)
- `djade >= 1.9.0` — Django template formatter (zamenjuje djlint)
- `pytest >= 9.0.3` + `pytest-django >= 4.12.0`
- `playwright >= 1.60.0` — E2E testovi
- `pre-commit >= 4.6.0`
- `django-debug-toolbar >= 6.3.0`

### Package manager — **OBAVEZNO `uv`** (NE pip, NE poetry, NE pipenv)
```bash
uv add <package>              # production dep
uv add --dev <package>        # dev dep
uv tool install falco-cli     # global dev helper (opciono)
uv run <command>              # run sa active venv
uv sync                       # restore deps from uv.lock
```

### Task runner — **`just`** (zamenjuje Makefile)
- `just dev`, `just test`, `just lint`, `just messages`, `just migrate`

### Frontend (no build pipeline — vendor files se serviraju lokalno)
- **Bootstrap 5.3** — CDN u dev, local u prod (`static/vendor/`)
- **HTMX 1.9+** — local
- **GLightbox 3.x** — local (10 KB gzipped)
- **Roboto** — self-hosted subset (latin + latin-ext za sr/hu) u `static/fonts/roboto/`

### Infra
- **Docker Compose** — per-env fajlovi u `compose/{local,staging,production}.yml`
- **Hetzner VPS** — CX22 (staging) + CX32 (production)
- **Nginx + Gunicorn + Whitenoise** — static via Whitenoise, media via Nginx fallback
- **GlitchTip 6** (self-host) — error tracking (Sentry SDK protocol kompatibilan)
- **UptimeRobot** — uptime monitoring
- **Hetzner Storage Box** + `pg_dump` + restic — bekap, 30d retention

### Critical version constraints
- ⚠️ **Python 3.13 minimum** — neke deps (django 5.2) zahtevaju 3.10+, ali pinned je 3.13 za new typing features
- ⚠️ **Django 5.2 LTS, NE 5.1** — explicit constraint zbog support window-a
- ⚠️ **`psycopg[binary]` v3, NE `psycopg2`** — v3 je active dev, binary distribuira pre-built wheels
- ⚠️ **Bez Celery / Redis u v1** — sve async tasks su sync (post-save signali za thumbnails). Dodati TEK ako future scale traži.

---

## Language-Specific Rules — Python

### Naming (Python kod)
- **Klase:** `PascalCase` → `Product`, `BrandViewSet`, `ServiceRequestForm`
- **Funkcije / metode / varijable:** `snake_case` → `get_active_products`, `render_partial`
- **Konstante:** `UPPER_SNAKE_CASE` → `MAX_UPLOAD_SIZE`, `DEFAULT_LOCALE`
- **Privatne članove:** leading underscore → `_internal_helper`
- **Django CBV:** `<Resource><Action>View` → `ProductListView`, `TractorListView`
- **Django FBV:** `<resource>_<action>` → `product_list`
- **Forms:** `<Resource>Form` → `ContactForm`, `ServiceRequestForm`
- **Signals:** `<resource>_<event>` → `product_published`, `lead_received`
- **Managers:** `<Adjective><Resource>Manager` → `PublishedProductManager`, `ActiveBrandManager`

### File organization
- **Django apps** uvek u `apps/<appname>/`, NIKAD na root nivou projekta
- Per-app fajlovi: `models.py`, `admin.py`, `views.py`, `urls.py`, `forms.py`, `signals.py`, `managers.py`, `translation.py`, `tests/`, `migrations/`
- **`translation.py`** per-app — gde se registruje `TranslationOptions` za modeltranslation
- **`apps/core/`** sadrži shared base klase (TimestampedModel, SluggedModel, PublishableModel) — uvek prvi instaliran
- Cross-app utility kod ide u `apps/core/utils.py` ili `apps/core/mixins.py`

### Imports
- **Apsolutni imports** preferirani → `from apps.products.models import Product`
- **Relativni imports** dozvoljeni samo unutar istog app-a → `from .models import Product`
- Grupisanje (ruff isort): stdlib → third-party → django → local apps
- **NIKAD** import `from django.contrib.auth.models import User` direktno — koristi `get_user_model()` ili `settings.AUTH_USER_MODEL`

### Type hints
- Type hints **preporučeni** za nove funkcije i metode, posebno za public API
- Modeli ne moraju imati type hints na poljima (Django field types su deklarativni)
- Koristi `from __future__ import annotations` kod modula sa mnogo type hints (Python 3.13 default lazy)
- Za QuerySet-ove: `QuerySet[Product]` umesto generičkog `QuerySet`

### Error handling
- **Specifični exceptions**, NIKAD bare `except:`
- View layer: koristi `Http404`, `PermissionDenied` za HTTP semantiku
- Form validation: `ValidationError` iz `django.core.exceptions`
- File upload: `SuspiciousOperation` chain za invalid MIME/signature
- **Sve unhandled exceptions** → GlitchTip capture (automatski preko SDK)

### Async / Sync
- **Sync only u v1** — nema `async def` views, nema Celery
- Tasks koje se mogu pokrenuti sync (thumbnail gen, email send) idu u **signals** ili direktno u view
- Ako future scale traži async: dodaje se Celery + Redis, NE asyncio

### gettext / i18n u kodu
- **Modeli, forme:** `from django.utils.translation import gettext_lazy as _` → `_("Naziv")`
- **Views runtime:** `from django.utils.translation import gettext as _` → runtime evaluation
- **NIKAD** hardcoded user-facing string bez `gettext` — sve UI strings moraju biti translatable
- **Email subjects:** koristi `gettext` runtime, jer subject zavisi od lokala primaoca

### Datetime
- **DB storage:** uvek UTC, Django default (`USE_TZ = True`)
- **Display:** kroz custom template tag `{% locale_date %}` u `apps/core/templatetags/coric_format.py`
- **NIKAD** `datetime.datetime.now()` — koristi `django.utils.timezone.now()`
- **NIKAD** naive datetime u DB — Django će raise warning u dev, error u prod

---

## Framework-Specific Rules — Django + HTMX

### Django models
- **Sve modele** nasleđuju iz `apps/core/models.py` base klasa kad je primenljivo:
  - `TimestampedModel` (`created_at`, `updated_at`)
  - `SluggedModel` (slug field sa ASCII transliteration)
  - `PublishableModel` (`is_published`, `published_at`, `PublishedManager`)
- **DB tabele:** Django default `appname_modelname` (lowercase + underscore) → `products_product`, `brands_brand`
- **Translated polja:** suffix `_sr`, `_hu`, `_en` — automatski generiše `django-modeltranslation` na osnovu `translation.py`
- **FK fields:** uvek navedi `on_delete` eksplicitno (`PROTECT`, `CASCADE`, `SET_NULL`) — Django >= 4 zahteva
- **FK `related_name`:** uvek navedi → `brand = FK(Brand, related_name="products")` (sprečava `_set` magic)
- **Indexes:** dodaj `db_index=True` na slug i polja koja se filtruju; composite indexes u `Meta.indexes` sa nazivom `<table>_<columns>_idx`
- **`get_absolute_url`** uvek implementirati na content modelima — koristi se za sitemap, admin, share linkove

### Django URLs
- **URL paths:** `kebab-case` ili srpske reči → `/o-nama/`, `/proizvod/<slug>/`, `/mehanizacija/prikljucna/`
- **URL names:** `<app>:<action>` namespace → `products:detail`, `forms:contact_submit`
- **HTMX-only endpoints:** prefix `/htmx/` → `GET /htmx/products/filter/`, `POST /htmx/forme/kontakt/`
- **i18n routing:** koristi `i18n_patterns()` u root URLconf → automatski dodaje `/sr/`, `/hu/`, `/en/` prefix
- **Slug-ovi u URL-u:** isključivo ASCII transliteration (`Ć→c`, `Č→c`, `Š→s`, `Ž→z`, `Đ→d`) — NIKAD Unicode u URL-u
- **Reverse:** uvek koristi `reverse()` ili `{% url %}` — NIKAD hardcoded URL string

### Django views (CBV preferred za standard CRUD)
- **CBV** za standardne liste/detail/forms — koristi mixins iz `apps/core/mixins.py`
- **FBV** za jednostavne ili HTMX-specific endpoints
- **HTMX detection** kroz `django-htmx` middleware → `if request.htmx: return partial`
- **Permission check:** `LoginRequiredMixin` + custom `IsEditorMixin` / `IsSuperadminMixin` iz `apps/accounts/permissions.py`
- **QuerySet optimizacija:** uvek `.select_related()` za FK + `.prefetch_related()` za reverse FK / M2M na list views

### Django forms
- **Sve forme** koje primaju user input MORAJU imati:
  - CSRF token (`{% csrf_token %}` u template)
  - `@ratelimit` decorator iz `django-ratelimit` (key='ip', rate='5/m')
  - Server-side validation kao SOT (client HTML5 je samo UX layer)
  - Locale-aware error messages preko `gettext_lazy`
- **File upload polja:** double-check (Pillow `Image.verify()` ZA slike + `python-magic` ZA MIME) u `clean_<field>`
- **HTMX form submit:** view vraća `partials/form_success.html` ili `partials/form_with_errors.html`

### HTMX response patterns (KRITIČNO — najlakše promašiti)
- **Svaki dinamički swap** vraća dva fragmenta:
  1. **Main partial** (npr. `partials/product_grid.html`) — ono što HTMX swap-uje u DOM
  2. **`hx-swap-oob` aria-live region** sa announcement → `<div hx-swap-oob="innerHTML:#aria-live">Pronađeno 12 rezultata</div>`
- **Partials lokacija:** `templates/<app>/partials/<entity>_<action>.html`
- **Partial template MORA** biti standalone-renderable (može da se uključi i kroz `{% include %}` van HTMX)
- **`HX-Trigger` header** za client-side custom events → `HX-Trigger: coric:filter-applied`
- **`HX-Redirect` header** za server-driven redirect (ne `HttpResponseRedirect` u HTMX flow-u)
- **Loading indicator:** dodaj `htmx-indicator` class + Bootstrap spinner; HTMX automatski postavlja `aria-busy="true"`
- **Min loading time:** 200ms (sprečava flicker za brze response-e)
- **NIKAD** vrati full HTML page kao response na HTMX request — uvek partial

### Django admin
- **Custom admin URL slug:** `/admin-coric/` (security-through-obscurity protiv bot probe)
- **Admin login** dodatno zaštićen `django-axes` (lockout posle N pokušaja)
- **Admin Dashboard** u `apps/admin_ext/views.py` zamenjuje default admin index
- **Per-app `admin.py`:** registruj sve modele sa `list_display`, `list_filter`, `search_fields`
- **Translated fields u admin:** `django-modeltranslation` auto-generiše tabove po lokalu — ne dodavati ručno
- **Inline editing:** koristi `TabularInline` / `StackedInline` za FK relationships (Product images, Product variants)

### i18n u Django
- **Settings:** `LANGUAGE_CODE = 'sr'`, `LANGUAGES = [('sr', 'Srpski'), ('hu', 'Magyar'), ('en', 'English')]`  # 'sr' matches LANGUAGES tuple key — Story 1.4 odluka; sr-latn može u Story 6.5/6.6 ako SEO/hreflang traži distinkciju
- **`USE_I18N = True`**, `USE_L10N = True`, `USE_TZ = True`
- **Middleware order:** `LocaleMiddleware` IZA `SessionMiddleware`, ISPRED `CommonMiddleware`
- **Locale fallback:** sr je default; ako neki prevod nedostaje → fallback na sr (custom logic ako treba)
- **`{% translate %}`** ili `{% blocktranslate %}` u svim templates — NIKAD hardcoded string
- **`makemessages` / `compilemessages`** workflow: `just messages` regeneriše + kompajlira

### CSRF / Security
- **Sve forme** uključuju `{% csrf_token %}` — uključujući HTMX forms
- **HTMX CSRF:** koristi `django-htmx` automatski csrf header propagation
- **Static files:** Whitenoise sa compressed manifest → cache-busting automatski
- **Media files:** Nginx fallback, ali validacija svih upload-a obavezna PRE save-a

### Migrations discipline
- **Workflow:**
  1. `python manage.py makemigrations <app>`
  2. **Manual review** generisanog migration fajla (PRE commit-a)
  3. `python manage.py migrate --plan` (provera plana)
  4. Commit migracija + model promene **zajedno** (atomic)
  5. Prod deploy: `migrate` kao deploy step
- **NIKAD** auto-applied migracije bez review-a
- **NIKAD** edit applied migration — uvek nova migracija za korekcije
- **Data migrations:** koristi `RunPython` sa `reverse_code` definisan

---

## Testing Rules

### Test framework
- **`pytest-django`** je SOT — NIKAD `unittest.TestCase` za nove testove
- **Playwright** za E2E testove (UJ-1, UJ-2, UJ-3 scenariji iz UX dokumenta)
- **Pokretanje:** `just test` (pokriva `apps/` + `tests/` direktorijume)
- **`pyproject.toml`** sadrži `[tool.pytest.ini_options]` sa `DJANGO_SETTINGS_MODULE = "config.settings.development"` i `testpaths = ["apps", "tests"]`

### Test organization
- **Unit tests** — kolokovani uz app → `apps/<app>/tests/test_<module>.py`
  - `apps/products/tests/test_models.py`, `apps/products/tests/test_views.py`
- **Integration tests** — cross-app → `tests/integration/test_<feature>.py`
- **E2E tests (Playwright)** — `tests/e2e/test_<journey>.py`
- **Test fixtures** — `tests/fixtures/` (shared data); per-app fixtures u `apps/<app>/tests/conftest.py`

### Fixtures
- **`pytest fixtures`** umesto Django `setUp` metoda
- Shared fixtures u `tests/conftest.py` (root) ili `apps/<app>/tests/conftest.py`
- **Database fixtures:** koristi `@pytest.fixture` sa `@pytest.mark.django_db`
- **Factory pattern:** koristi `factory_boy` (dodati u dev deps kad zatreba) za test data generation — NE inline `Model.objects.create()` u svakom testu

### Test naming
- **Fajlovi:** `test_<module>.py` (prefix `test_` obavezan za pytest discovery)
- **Funkcije:** `test_<scenario_description>` snake_case → `test_product_with_no_variants_returns_404`
- **Klase (kad se grupišu):** `Test<Feature>` PascalCase → `TestProductDetailView`
- **NIKAD** generička imena (`test_1`, `test_basic`) — naziv testa MORA opisati scenario

### What to test
- **Models:** validacije, custom managers, `__str__`, `get_absolute_url`, `clean()` metode
- **Views:** status code, template used, context data, redirect behavior, permission denial
- **Forms:** validacija polja, `clean_<field>` ponašanje, `clean()` cross-field rules
- **HTMX endpoints:** test sa `request.htmx = True` simulacijom (django-htmx pruža pomoć)
- **i18n:** test renderovanja za sr/hu/en (parametrizuj `LANGUAGE_CODE`)
- **Security:** ratelimit aktivacija, CSRF failure, permission denied, MIME validation rejection

### Mock policy
- **Mock samo external services** (SMTP, Resend API, GA reporting API)
- **NIKAD mock-uj Django ORM ili PostgreSQL** — koristi real test DB (pytest-django pravi/uništava)
- **`responses` lib** za mock-ovanje HTTP poziva ka external API-ima (kad zatreba)
- **`mailoutbox` fixture** za email assertions — Django/pytest-django built-in

### Database tests
- **`@pytest.mark.django_db`** decorator na svaki test koji dira DB
- **`@pytest.mark.django_db(transaction=True)`** samo kad test treba transakciju (npr. signals testing)
- **NIKAD** `--keepdb` u CI; uvek fresh DB
- **Migracije se primenjuju automatski** preko pytest-django

### E2E (Playwright)
- **Pokriva 3 kritična user journey-a:**
  - UJ-1 — Marko: catalog browsing + filter (anonimni korisnik)
  - UJ-2 — Stojan: forma submit (servis ili rezervni delovi)
  - UJ-3 — Marijana: admin product create + publish
- **Headless u CI**, headed lokalno za debugging (`PWDEBUG=1`)
- **Per-locale variants:** test svakog journey-a za sr (primarni) + 1 sample za hu/en (po fixture-u)
- **Selectors:** prefer `data-testid` attribute pre nego CSS class (koje se mogu menjati)
- **Wait strategy:** `await expect(locator).toBeVisible()` umesto `sleep`

### Coverage
- **No hard threshold u v1** — kvalitet testova iznad procenta
- **Critical paths MORAJU imati testove:** auth, lead form submission, admin product save, locale routing
- **Coverage report:** `pytest --cov=apps --cov-report=html` (dodati `pytest-cov` u dev deps kad zatreba)

### Test discipline (BMad Method)
- **TEA agent piše testove (RED phase)**, Dev agent piše kod (GREEN phase) — **Dev NIKAD ne piše testove**
- Testovi se commit-uju **pre** implementacije (red phase commit)
- Implementacija se commit-uje kao **green phase** (zasebno commit od testova)
- Failure: ako TEA testovi failuju, story se vraća u `paused` status — ne maskiraj greške u Dev fazi

---

## Code Quality & Style Rules

### Linting / formatting (mandatory)
- **`ruff`** je SOT za Python lint + format → `ruff check .` + `ruff format .`
  - Line length: **100** (NE 88 default-a)
  - Naming conventions enforced (PEP 8 + Django conventions)
  - Import sorting enforced (zamenjuje isort)
- **`djade`** za Django template format → `djade --check templates/`
- **`pre-commit`** hooks pokreću oba na svaki commit — fail = blokira commit
- **CI** (GitHub Actions `ci.yml`) re-pokreće ruff + djade + pytest na svaki push

### CSS naming (BEM-like + Bootstrap prefix isolation)
- **Custom komponente** koriste BEM: `block__element--modifier`
  - `.product-card`, `.product-card__title`, `.product-card--featured`
- **`coric-` prefix** na svim custom class-ovima da izbegnu Bootstrap clash → `.coric-hero-overlay`, `.coric-stat-medallion`
- **Bootstrap utility classes** ostaju kako jesu → `.d-flex`, `.gap-3`, `.text-center`
- **NIKAD inline `style="..."` sa magic vrednostima** — uvek kroz class ili CSS Custom Property

### CSS Custom Properties (tokens)
- **Definicija** u `static/css/tokens.css` u `:root { ... }` (matchuje DESIGN.md tokens 1:1)
- **Naming:** `--<group>-<name>-<variant>` → `--color-brand-green-800`, `--spacing-scale-4`, `--rounded-pill`
- **Korišćenje:** uvek `var(--token-name)` u CSS pravilima — NIKAD direktan hex/px u komponentnom CSS-u
- **Token primer:**
  ```css
  :root {
    --color-brand-green-800: #25402f;
    --spacing-scale-4: 1.5rem;
    --rounded-pill: 9999px;
  }
  .coric-hero { background: var(--color-brand-green-800); }
  ```

### JavaScript style
- **Funkcije / varijable:** `camelCase` → `initLightbox`, `updateAriaLive`
- **Konstante:** `UPPER_SNAKE_CASE` → `HTMX_TIMEOUT_MS`
- **Module fajlovi:** `kebab-case.js` → `lightbox-init.js`, `statistic-counter.js`
- **Custom DOM events:** `coric:` namespace → `coric:filter-applied`, `coric:lightbox-open`
- **Vanilla JS preferred** — Alpine.js opciono za stateful komponente, NIKAD jQuery
- **No build pipeline** — JS se servira direktno iz `static/js/` (ne tree-shake, ne bundle)

### Templates (Django)
- **Fajlovi:** `kebab-case.html` → `product-detail.html`, `brand-card.html`
- **Direktorijumi:** per-app → `templates/products/`, `templates/brands/`
- **Partials:** `templates/<app>/partials/<entity>_<action>.html` — snake_case za partial nazive (Django convention)
- **Block naming:** `{% block content %}`, `{% block extra_head %}`, `{% block scripts %}` — konzistentno kroz `base.html`
- **`{% load %}`** uvek na vrhu template-a, posle `{% extends %}`
- **NIKAD logic u template-u** koji može biti u view-u — template je za render, view za pripremu konteksta

### Comments policy
- **Default: nema komentara.** Imena identifikatora moraju opisati WHAT.
- **Komentar samo za WHY** koji nije očigledan: skrivena ograničenja, suptilni invariantni, workaround za specifičan bug
- **NIKAD** komentari tipa `# this used to be X`, `# added for issue #123`, `# TODO: refactor`
- **Docstrings:** kratke (max 1-2 linije) za public funkcije/klase; bez multi-paragraph blokova

### Code organization principles
- **YAGNI** — nemoj graditi za hipotetičke buduće potrebe. Tri slične linije nisu razlog za apstrakciju.
- **No premature abstractions** — bug fix ne treba okolni cleanup; jednokratna operacija ne treba helper
- **No defensive validation** za scenarije koji se ne mogu desiti (trust internal code, validate only at boundaries)
- **No backwards-compat shims** kad možeš samo da promeniš kod
- **No feature flags** osim ako business explicitly traži ramp-up

### Format patterns (lokali)
- **Datum DB:** UTC ISO 8601 (Django default)
- **Datum UI sr:** `DD.MM.YYYY.` → `27.05.2026.`
- **Datum UI hu:** `YYYY.MM.DD.` → `2026.05.27.`
- **Datum UI en:** `MMM DD, YYYY` → `May 27, 2026`
- **Vreme uvek:** 24h `HH:MM` → `14:23`
- **Cena EUR:** `€ XX.XXX` (tačka kao thousands separator) → `€ 25.000`
- **Konjska snaga:** `XX KS` → `60 KS`
- **Dimenzije:** `XXXX mm` → `4035 mm`
- **Zapremina:** `X m³` ili `X kubika` → `6 m³`

### Slugovi (URL paths)
- **ASCII transliteration** sa srpskih dijakritika (`Ć→c`, `Č→c`, `Š→s`, `Ž→z`, `Đ→d`)
- **Lowercase, kebab-case**, bez stop words
- Implementacija: `apps/core/utils.py` sa `unidecode` (ili custom helper)
- Slug field na modelu koristi `prepopulated_fields = {'slug': ('name',)}` u admin-u, ali server-side validacija u `save()`

### Configuration files (lokalni standardi)
- **`.editorconfig`** — UTF-8, LF endings, 4-space Python, 2-space HTML/CSS/JS
- **`.python-version`** — pinned 3.13
- **`.env.example`** — template; **NIKAD** komituj `.env`
- **`pyproject.toml`** — single source of truth (deps + tool configs)
- **`justfile`** — task runner sa standardnim komandama

---

## Development Workflow Rules

### Git branching
- **`main`** — production-ready, deployable u svakom trenutku. Push na main triggers production deploy.
- **`staging`** — staging environment branch. Push na staging triggers staging deploy.
- **Feature branches:** `feature/<epic>-<story-id>-<short-slug>` → `feature/epic2-story-2.3-product-detail-view`
- **Bugfix branches:** `bugfix/<short-slug>` → `bugfix/htmx-csrf-token-missing`
- **Hotfix branches:** `hotfix/<short-slug>` → `hotfix/login-rate-limit`
- **NIKAD** direktan commit na `main` ili `staging` — uvek kroz PR

### Commit messages (Conventional Commits style — lagana verzija)
- **Format:** `<type>(<scope>): <subject>`
- **Types:** `feat`, `fix`, `refactor`, `test`, `docs`, `style`, `chore`, `perf`
- **Scope:** ime app-a ili komponente → `feat(products): add ProductVariant model`
- **Subject:** kratak (~50 char), imperative mood, lowercase (npr. "add", "fix", ne "added", "fixes")
- **Body** opcioni, za WHY (ne WHAT) — odvojen praznim redom
- **Footer** za breaking changes ili issue refs → `BREAKING CHANGE: Lead model schema changed`

### BMad story workflow (5-step ciklus)
- **Story file (`.md`)** je UGOVOR između SM (Scrum Master) i Dev agenta — nikad se ne preskače radi efikasnosti
- **Step-00:** Init — sprint health check, story selection (Story Orchestrator u glavnom kontekstu)
- **Step-01:** Create — SM agent piše story sa context koji Dev treba (fresh subagent)
- **Step-02:** Validate — paralelni subagenti (run_in_background=true) za multi-perspective validaciju; auto-fix svih problema
- **Step-03:** Implement — sekvencijalan:
  1. **TEA agent** piše testove (RED phase)
  2. **Dev agent** piše implementaciju (GREEN phase)
  3. Dev NIKAD ne piše testove
- **Step-04:** Review — paralelni subagenti za code review; auto-fix svih nalaza
- **Fresh subagent po koraku** — nikad reuse, nikad SlashCommand (clean slate prevents context pollution)
- **File system je message bus** — subagentima šalji INSTRUKCIJE i putanje, NIKAD sadržaj fajlova

### Sprint status tracking
- **`_bmad-output/implementation-artifacts/sprint-status.yaml`** je progress tracker
- **Story statuses:** `draft` → `validated` → `in-progress` → `review` → `done`; ili `paused` ako blokirana
- **Update posle svakog Step-a:** orkestrator update-uje status, Dev/TEA/QA agenti samo izveštavaju
- **Resume support:** ako se workflow prekine, sprint-status.yaml omogućava restart sa tačke prekida

### PR review checklist (solo dev — self-review template)
- [ ] Sve testove passuju lokalno (`just test`)
- [ ] `just lint` clean (ruff + djade)
- [ ] Migracija manually reviewed (ako postoji)
- [ ] Sva user-facing strings prolaze kroz `gettext` / `{% translate %}`
- [ ] Slugovi su ASCII (no Unicode u URL-u)
- [ ] HTMX endpointi imaju `aria-live` OOB announcement
- [ ] Forme imaju CSRF token + ratelimit
- [ ] CSS koristi tokens (`var(--...)`) umesto magic vrednosti
- [ ] Komentari samo gde je WHY non-obvious
- [ ] No defensive validation, no premature abstraction

### Local development
- **Bootstrap:** `uv sync` (instalira deps iz `uv.lock`)
- **Run dev server:** `just dev` → `docker compose -f compose/local.yml up`
- **Sve dev komande kroz `just`** — ne pokreći `python manage.py` direktno (ide kroz `uv run`)
- **PostgreSQL** lokalno preko Docker compose (NE lokalna instalacija)
- **Hot reload** Django autoreload + browser refresh (no HMR jer no build pipeline)

### Deployment (push-driven)
- **Staging:** `git push origin staging` → GitHub Actions `deploy.yml` → SSH na staging Hetzner box → `ops/deploy/deploy.sh staging`
- **Production:** PR merge u `main` (posle review-a) → ista mehanika sa production env
- **Deploy steps (`ops/deploy/deploy.sh`):**
  1. `git pull`
  2. `uv sync --frozen`
  3. `python manage.py collectstatic --noinput`
  4. `python manage.py migrate --plan` (assertion check)
  5. `python manage.py migrate`
  6. `python manage.py compilemessages`
  7. `docker compose restart django`
- **Rollback:** `ops/deploy/rollback.sh` → checkout previous tag + redeploy
- **NIKAD** force push na `main` ili `staging` — koristi `revert` umesto

### Environment management
- **3 env-a:** local / staging / production
- **Settings split:** `config/settings/{base,development,staging,production}.py`
- **`.env` per environment** — NIKAD u repo, držati van Git-a
- **Secrets:** Hetzner Cloud secrets panel + Docker secrets (production); `.env` (local + staging)
- **Migrations konzistentne:** local → staging → production (test svake migracije na staging-u pre prod-a)

### Backup & restore
- **Cron:** dnevni `pg_dump` (3:00 UTC) → encrypted + uploaded na Hetzner Storage Box
- **Retencija:** 30 dana
- **Restore test:** mesečno (manual) — verify backup nije corrupted
- **Media bekap:** sedmični rsync ka Storage Box-u

### Hooks (NIKAD `--no-verify`)
- **`pre-commit` hooks** moraju da prođu — fail = fix uzrok, ne bypass
- **Ako je hook potreban da se promeni** (nova ruff verzija, novi format): commit hook update kao zasebnu izmenu

### CI / CD philosophy
- **CI fail = block merge** — nikad ne mergeuj sa crvenom CI lampom
- **Deploy je idempotentan** — pokretanje isti deploy script dva puta ne menja stanje
- **Migrations su deploy-time, ne app-startup** — Django ne migrira u `entrypoint.sh`

---

## Critical Don't-Miss Rules

_Ovo je distilacija pravila koja AI agenti najlakše promaše. Pre svake nove komponente proveri ovu sekciju._

### 🚫 Anti-pattern: Ćirilica u kodu
```python
# ❌ NIKAD
naziv = "Ћорић Аграр"
PORUKA_USPEH = "Успешно сачувано"

# ✅ UVEK latinica
naziv = "Ćorić Agrar"
PORUKA_USPEH = _("Uspešno sačuvano")
```

### 🚫 Anti-pattern: Unicode u URL-u
```python
# ❌ NIKAD
slug = "agri-tracking-tb804-šanežno"
url = f"/proizvod/ćorić-agrar/"

# ✅ UVEK ASCII transliteration
slug = "agri-tracking-tb804-sanezno"
url = "/proizvod/coric-agrar/"
```

### 🚫 Anti-pattern: Inline CSS / magic values
```html
<!-- ❌ NIKAD -->
<div style="color: #25402f; padding: 32px;">

<!-- ✅ UVEK kroz tokens i klase -->
<div class="coric-hero">  <!-- CSS koristi var(--color-brand-green-800) -->
```

### 🚫 Anti-pattern: HTMX swap bez aria-live
```python
# ❌ NIKAD samo partial vraćen
return render(request, "products/partials/grid.html", ctx)

# ✅ UVEK partial + aria-live OOB
return render(request, "products/partials/grid_with_aria.html", ctx)
# template uključuje: <div hx-swap-oob="innerHTML:#aria-live">12 rezultata</div>
```

### 🚫 Anti-pattern: Hardcoded user-facing string
```python
# ❌ NIKAD
def get_success_message():
    return "Forma je poslata"

# ✅ UVEK gettext
from django.utils.translation import gettext as _
def get_success_message():
    return _("Forma je poslata")
```

### 🚫 Anti-pattern: Naive datetime
```python
# ❌ NIKAD
from datetime import datetime
product.published_at = datetime.now()

# ✅ UVEK timezone-aware
from django.utils import timezone
product.published_at = timezone.now()
```

### 🚫 Anti-pattern: Direct User import
```python
# ❌ NIKAD
from django.contrib.auth.models import User
class Lead(models.Model):
    created_by = models.ForeignKey(User, ...)

# ✅ UVEK kroz settings
from django.conf import settings
class Lead(models.Model):
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, ...)
```

### 🚫 Anti-pattern: Forma bez CSRF / ratelimit
```python
# ❌ NIKAD
def contact_submit(request):
    form = ContactForm(request.POST)
    if form.is_valid():
        form.save()

# ✅ UVEK
from django_ratelimit.decorators import ratelimit

@ratelimit(key='ip', rate='5/m', block=True)
def contact_submit(request):
    # template MORA imati {% csrf_token %}
    form = ContactForm(request.POST)
    if form.is_valid():
        form.save()
```

### 🚫 Anti-pattern: File upload bez double-check
```python
# ❌ NIKAD samo Django field validacija
class ProductForm(forms.ModelForm):
    main_image = forms.ImageField()  # samo extension check

# ✅ UVEK MIME + signature double-check
import magic
from PIL import Image

def clean_main_image(self):
    image = self.cleaned_data['main_image']
    # MIME signature check
    mime = magic.from_buffer(image.read(2048), mime=True)
    image.seek(0)
    if mime not in ['image/jpeg', 'image/png', 'image/webp']:
        raise ValidationError(_("Nedozvoljen tip fajla"))
    # PIL verify
    Image.open(image).verify()
    image.seek(0)
    return image
```

### 🚫 Anti-pattern: Migracija bez review-a
```bash
# ❌ NIKAD
python manage.py makemigrations && git add -A && git commit -m "wip"

# ✅ UVEK
python manage.py makemigrations <app>
# OPEN generisan migration fajl, pročitaj svaku operaciju
python manage.py migrate --plan  # verify plan
# Tek onda commit:
git add apps/<app>/migrations/ apps/<app>/models.py
git commit -m "feat(<app>): add <field> to <model>"
```

### 🚫 Anti-pattern: Cross-boundary import
App dependency rules (iz architecture.md):
- ❌ `core` ne sme importovati domain apps (products, brands, ...)
- ❌ `brands` ne sme importovati `products` (jednosmerna — `products → brands`)
- ❌ `forms` ne sme importovati `catalog` / `blog` direktno
- ❌ Domain apps ne smeju importovati iz `admin_ext`

### 🚫 Anti-pattern: Bare except
```python
# ❌ NIKAD
try:
    product.save()
except:
    pass

# ✅ UVEK specific
try:
    product.save()
except IntegrityError as exc:
    raise ValidationError(_("Slug već postoji")) from exc
```

### 🚫 Anti-pattern: Defensive validation na internim pozivima
```python
# ❌ NIKAD — preinastruktirano za internal code
def get_product_url(product):
    if product is None:
        return ""
    if not hasattr(product, 'slug'):
        return ""
    if not product.slug:
        return ""
    return reverse("products:detail", kwargs={"slug": product.slug})

# ✅ Trust internal code, validate na boundary
def get_product_url(product):
    return reverse("products:detail", kwargs={"slug": product.slug})
```

### 🚫 Anti-pattern: Skipping pre-commit hooks
```bash
# ❌ NIKAD
git commit --no-verify -m "rush"

# ✅ UVEK fix uzrok hook failure-a
ruff check . --fix
djade templates/
git commit -m "..."
```

### ✅ Security must-haves (provera na svakom PR-u)
1. **CSRF token** na svim formama (uključujući HTMX)
2. **ratelimit** na javnim formama (kontakt, login, registracija) — `5/m` na IP
3. **MIME validation** na svakom upload polju (Pillow + python-magic)
4. **HTTPS only** u prod (`SECURE_SSL_REDIRECT = True`)
5. **HSTS** enabled (`SECURE_HSTS_SECONDS = 31536000`)
6. **CSP header** preko `django-csp` (no inline scripts bez nonce)
7. **`django-axes` lockout** na admin login (5 pokušaja → 1h lockout)
8. **`SECRET_KEY` u env**, ne u settings
9. **`DEBUG = False`** u prod (provera u CI deploy)
10. **Admin URL slug `/admin-coric/`** (security through obscurity layer)

### ✅ A11y must-haves (WCAG 2.1 AA)
1. **aria-live region** prisutan u `base.html` — sve HTMX swaps announce u njega
2. **`<html lang="{{ LANGUAGE_CODE }}">`** automatski preko Django middleware-a
3. **Focus management** posle HTMX swap (vrati focus na trigger element ili specifični target)
4. **Alt text** na svim slikama — `alt=""` za dekoraciju, deskriptivan inače
5. **Color contrast** 4.5:1 minimum (DESIGN.md tokens već prošli)
6. **Keyboard navigation** — slider mora imati pause na fokus + arrow keys
7. **`prefers-reduced-motion`** respect — sve CSS animations imaju `@media (prefers-reduced-motion: reduce)`
8. **`aria-busy="true"`** na HTMX containers tokom load (HTMX automatski)

### ✅ Performance must-haves
1. **`select_related` + `prefetch_related`** na svakoj list view (sprečava N+1)
2. **Image srcset** preko `sorl-thumbnail` na svim user-facing slikama
3. **`loading="lazy"`** atribut na slikama ispod fold-a
4. **`font-display: swap`** na Roboto font-faces
5. **Whitenoise compressed manifest** — automatski gzip + brotli + cache busting
6. **HTMX min loading time** 200ms (sprečava flicker)
7. **LCP target < 2.5s, TTFB < 600ms** — verify u staging load testu

### 🎯 Pre commit-a UVEK pitaj sebe:
1. Da li sam koristio `_("text")` za sve user-facing strings?
2. Da li sam dodao `aria-live` OOB ako je ovo HTMX endpoint?
3. Da li je migracija manually reviewed?
4. Da li forma ima CSRF + ratelimit?
5. Da li sam koristio `var(--token)` umesto magic CSS value?
6. Da li slug koristi ASCII transliteration?
7. Da li sam izbegao defensive validation na internim pozivima?
8. Da li `just test` i `just lint` prolaze?

---

## Usage Guidelines

### Za AI agente
- **Pročitaj ovaj fajl PRE implementacije** — svaki Dev/TEA/Architect/QA agent
- **Sledi sva pravila tačno** kako su dokumentovana — odstupanja se ne tolerišu bez explicit razloga
- **Kad si u dilemi**, biraj **strožu opciju** (npr. više validacije, više testova, više a11y)
- **Ako naletiš na novi pattern** koji se ponavlja a nije ovde dokumentovan — update ovaj fajl kao deo svoje story-je
- **Za detaljne arhitektonske odluke** uvek konsultuj `_bmad-output/planning-artifacts/architecture.md`

### Za Mihas-a (i ljudske kolaboratore)
- **Drži fajl lean** — fokus na pravila koja AI često promaši, ne duplikat architecture.md
- **Update kad se promeni tech stack** — nova verzija Django, novi dep, deprecated alat
- **Review kvartalno** — uklanjaj pravila koja su postala očigledna ili više ne važe
- **Source of truth za stack:** `pyproject.toml`. Source of truth za arhitekturu: `architecture.md`. Ovaj fajl je **distilacija** za AI agente.

### Prioritet konflikata
Ako se pravilo ovde **sukobljava** sa nečim u `architecture.md`:
1. Ako je arch.md **eksplicitno o tom pravilu** → `architecture.md` pobeđuje (i update ovaj fajl)
2. Ako je arch.md **opštije** → ovaj fajl pobeđuje (specifičnije pravilo za AI agente)

**Last Updated:** 2026-05-27 (Mihas)
