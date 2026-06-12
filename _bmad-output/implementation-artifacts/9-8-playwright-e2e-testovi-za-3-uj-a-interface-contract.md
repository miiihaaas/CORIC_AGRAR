# Interface Contract — Story 9.8 Playwright E2E (3 UJ-a)

**RED phase artifact.** Test Architect (TEA) je napisao izvršni test CONTRACT (spec-ovi
+ conftest + page objects). Dev (GREEN) implementira protiv ovog kontrakta. Suite je
RED dok se NE ispune svi delovi ispod.

Playwright = **Python** (`pytest-playwright` + sync API). NE Node.

---

## 1. `data-testid` DELTA (AC8) — SAMO genuino nedostajuće (grep-verifikovano)

**NE diraj postojeće hook-ove** (Epic 5/6 markup-lock). Dodaj SAMO ASCII `data-testid`
atribut (ne-invazivno) u sledeće template-e:

| `data-testid` | Template fajl | Element |
|---|---|---|
| `model-inquiry-success` | `templates/forms/partials/model_inquiry_success.html` | root `<section class="...--success">` |
| `service-request-success` | `templates/forms/partials/service_request_success.html` | root `<section class="...--success">` |
| `mobile-nav-toggle` | `templates/partials/header.html` | `<button class="navbar-toggler coric-nav__hamburger">` (linija ~72) |
| `filter-snaga-min` | `templates/products/partials/_filter_form.html` | `<input type="hidden" name="snaga_min" data-range-min-input>` (linija 32) |
| `filter-snaga-max` | `templates/products/partials/_filter_form.html` | `<input type="hidden" name="snaga_max" data-range-max-input>` (linija 33) |
| `model-inquiry-model` *(opciono)* | `templates/forms/partials/_model_inquiry_form_fields.html` | readonly Model `<input ... readonly>` (linija ~38) |

**VEĆ POSTOJE (NE DIRATI):** `tractor-filter-form`, `reset-filters-button`
(`_filter_form.html`); `tractor-results-grid`, `tractor-card-<slug>`, `pagination-prev/next`
(`_results_grid.html`); `model-inquiry-form`, `model-inquiry-submit`
(`_model_inquiry_form_fields.html`); `service-form`, `service-submit`
(`_service_request_form_fields.html`); `product-detail-page`, `product-inquiry-cta`
(`product_detail.html`); `search-results-container` (`header.html`);
**`spec-section-motor`** (`_specs_accordion.html` — već postoji, NE diramo; page object
ga koristi za Motor default-open asserciju).

**aria-live:** `id="aria-live"` već renderuje `{% aria_live %}` tag
(`apps/core/templatetags/htmx_aria.py`, Story 1-6 markup-lock). Playwright cilja `#aria-live`
direktno. **NE menjati taj tag.** `cena_min`/`cena_max` testid NIJE potreban (UJ-1 koristi
SAMO snagu — C-6).

---

## 2. `conftest.py` fixtures — GREEN kontrakt

Lokacija: `tests/e2e/conftest.py` (napisan). Fixtures + šta Dev mora obezbediti:

| Fixture | Scope | GREEN kontrakt |
|---|---|---|
| `base_url` | session | Čita `E2E_BASE_URL` env (default `http://localhost:8000`). **GOTOVO** — nema Dev posla. |
| `e2e_data` | session | Poziva `python manage.py seed_e2e_data --force`. **Dev mora napraviti command `seed_e2e_data`** (vidi §5). Alt: `E2E_SKIP_DATA_SETUP=1` (remote-staging mod) preskače subprocess — tada je data-setup zaseban CI step. |
| `dev_superuser` | session | (1) `manage.py axes_reset` (MANDATORY axes-flush, AC1d); (2) `createsuperuser --noinput` sa env `DJANGO_SUPERUSER_USERNAME`/`_EMAIL`/`_PASSWORD`. **Fail-loud ako `DJANGO_SUPERUSER_PASSWORD` nije set** (AC11 — NIKAD hardkodovan). Idempotentno (already-exists toleriše). |
| `sample_image_path` | session | `tests/e2e/assets/sample.png` (commit-ovan validan PNG). Dev može zameniti realnijim JPG-om. |
| `mobile_context_args` / `mobile_page` | function | Mobile viewport 390×844 (<768px) za UJ-2. Pravi zaseban browser context. Zahteva `pytest-playwright` `browser` fixturu. |

**Env vars (CI secrets / `.env`):**
- `E2E_BASE_URL` (default `http://localhost:8000`)
- `DJANGO_SUPERUSER_USERNAME` (default `e2e_admin`)
- `DJANGO_SUPERUSER_EMAIL` (default `e2e_admin@example.com`)
- `DJANGO_SUPERUSER_PASSWORD` — **OBAVEZAN, bez default-a** (CI secret / `.env`)
- `E2E_SKIP_DATA_SETUP` (opciono — `1` za remote-staging mod)

`.env.example` sme imati dev-only placeholder password (AC11 dozvoljava).

---

## 3. `pyproject.toml` + `justfile` (AC6/AC13)

### Task 1.1 — dev dep
U `[dependency-groups].dev` dodaj `pytest-playwright` (`playwright>=1.60.0` VEĆ postoji).
Regen `uv lock`. **POTVRĐENO RED:** `pytest-playwright` je trenutno MISSING.

### Task 1.3 — `e2e` marker (AC13). **POTVRĐENO RED:** marker NIJE registrovan.
U `[tool.pytest.ini_options]`:
```toml
markers = [
    "docker: runnable container smoke (Story 9.1 prod stack); deselect sa `-m 'not docker'`",
    "e2e: Playwright end-to-end suite (Story 9.8); trazi pokrenutu seed-ovanu app + browser; deselect sa -m 'not e2e'",
]
addopts = "--import-mode=importlib -m 'not e2e'"
```
(`addopts` trenutno = `--import-mode=importlib` → dodaj `-m 'not e2e'` da `just test`
NE pokupi `tests/e2e/` — libmagic/browser-free unit suite ostaje green.)

### Task 7 — `just e2e` recept (AC6)
```
# Pokrece ISKLJUCIVO Playwright E2E suite (headless) protiv pokrenute, seed-ovane app.
# Prereqs: `just dev` (Django+Postgres up), `manage.py seed_e2e_data --force`,
#          `playwright install --with-deps chromium`, DJANGO_SUPERUSER_PASSWORD u env-u.
e2e *ARGS:
    docker compose -f compose/local.yml run --rm django uv run pytest -m e2e tests/e2e/ {{ARGS}}
```
Recept bira SAMO E2E (`-m e2e` + `tests/e2e/` path); `just test` (sa `-m 'not e2e'`) ne povlači ga.

---

## 4. CI job kontrakt (AC7) — `e2e.yml`, self-contained (PRIMARNO)

- Trigger: push na **`staging`** (NE `master`/PR fast loop). Default branch je `master`;
  `deploy.yml` lista je `[staging, main]` → `master` push NE pokreće E2E (željeno).
- **Self-contained job** (default): job sam diže Postgres service + Django, `seed_e2e_data --force`
  + AC12 remedijacija, `playwright install --with-deps chromium`,
  `pytest -m e2e tests/e2e/` headless protiv `E2E_BASE_URL=http://localhost:8000`.
  NEZAVISNO od `deploy.yml` (koji takođe triggeruje na `staging`) — NEMA race.
- `DJANGO_SUPERUSER_PASSWORD` iz CI secret-a (`DJANGO_SUPERUSER_*`).
- **ALTERNATIVA (env-driven, NE default):** vožnja protiv deploy-ovanog staging URL-a →
  `workflow_run`-zavisnost od `deploy.yml` (`types:[completed]` + guard `conclusion=='success'`)
  + `E2E_BASE_URL` iz staging URL secret-a (OQ-3) + `E2E_SKIP_DATA_SETUP=1` (data-setup je
  zaseban step na boxu).

---

## 5. AC12 data-setup mehanizam (KRITIČNO — UJ-1 bez ovoga nemoguć)

**REALAN GAP koji E2E razotkriva:** 9-7 `seed_sample_data` kreira traktore sa
`subcategory=None` (linija 333) → `TractorListView` filtrira
`subcategory__category__is_for="traktori"` → NULL JOIN ISKLJUČUJE seed-ovane traktore →
`/sr/traktori/` PRAZAN. Dodatno: 0 `ProductImage` / 0 `main_image` → galerija
(`{% if product.images.all %}`) se NIKAD ne renderuje.

**GREEN: napravi idempotentni management command `apps/core/management/commands/seed_e2e_data.py`**
(DEV-only guard, mirror `seed_sample_data` SM-D2 `--force`):

1. Pozovi `call_command("seed_sample_data", force=True)`.
2. **(a) Listing-visibility:** `Category.objects.get(slug="traktori")` (is_for="traktori",
   već seed-ovana) → `Subcategory.objects.get_or_create(category=cat, slug="traktori",
   defaults={"name": "Traktori"})`. Dodeli je trima traktorima:
   `Product.objects.filter(slug__in=["agri-tracking-tb804","wuzheng-wz504","saillong-sl904"])
   .update(subcategory=sub)`.
3. **(b) Galerija:** za `agri-tracking-tb804` → `ProductImage.objects.get_or_create(
   product=tb804, order=0, defaults={"image": <tests/e2e/assets/sample.png>, "alt_text": "..."})`.
   (Učitaj asset kroz `ContentFile`/`File`.)
4. **(c) UJ-3 idempotentnost (I-3):** obriši (ILI get_or_create-guard) eventualni prethodni
   `Product.objects.filter(slug__in=["e2e-test-produkt","e2e-test-produkt-gate"]).delete()`
   (CASCADE briše inline ProductImage/ProductSpecification) PRE UJ-3 testova.
   ⚠️ **OBA fiksna slug-a** moraju biti očišćena: happy-path test kreira `e2e-test-produkt`
   (published), a publish-gate edge test kreira ZASEBAN `e2e-test-produkt-gate` (jer je
   `Product.slug` unique=True → isti slug bi pao na unique-koliziju PRE nego što
   publish-gate u `save_related` fire-uje — TEA fix, test-izolacija).
5. *(Opciono — axes reset može biti deo ovog command-a umesto zasebnog `axes_reset` poziva.)*

Model činjenice (verifikovano):
- `brands.Subcategory`: `category` (FK, CASCADE), `slug` (NIJE globally unique — unique per
  category nije enforced na DB; get_or_create po `(category, slug)`), `name`, `parent` (nullable).
- `brands.Category`: `traktori` slug postoji posle 9-7 seed-a (`is_for="traktori"`).
- `products.ProductImage`: `product` (FK CASCADE, related_name="images"), `image` (ImageField,
  upload_to="products/gallery/"), `order` (default 0), `alt_text`.
- `Product.subcategory` je nullable FK (PR-D3) — `.update(subcategory=...)` je validan.

Sve `get_or_create` → re-run ne duplira (idempotentno). DEV/staging only.

---

## 6. Page Object klase — signatura (AC5)

`tests/e2e/page_objects/`:

**`TraktoriListingPage(page, base_url)`** — `traktori_listing_page.py`
- `goto(locale="sr")`; `filter_by_snaga_min(value)` (fill hidden + dispatch `change`);
- `expect_grid_visible()`; `expect_card_present(slug)`; `expect_card_absent(slug)`; `open_card(slug)`.
- Lokatori: `filter_form`, `results_grid`, `snaga_min_input` (testid `filter-snaga-min`),
  `tractor_card(slug)` (testid `tractor-card-<slug>`).

**`ProductDetailPage(page, base_url)`** — `product_detail_page.py`
- `goto(slug, locale="sr")`; `expect_loaded()`; `expect_gallery_visible()`;
  `expect_specs_motor_open()`; `expect_model_autofilled(slug)`;
  `fill_and_submit_inquiry(name, email, phone, message)`; `expect_inquiry_success()`.
- Konstante: `MODEL_INQUIRY_SUCCESS_SUBSTRING = "Vaš upit za model je primljen"`,
  `MODEL_INQUIRY_ARIA_ANNOUNCEMENT = "Upit za model je poslat"`.
- **aria-live (TEA fix):** `#aria-live` je `visually-hidden` singleton (`htmx_aria.aria_live`,
  uvek u DOM-u, prazan do OOB swap-a) → `expect_inquiry_success()` asertuje da je OOB swap
  UPISAO announcement tekst (`to_contain_text(MODEL_INQUIRY_ARIA_ANNOUNCEMENT)`), NE puko
  `to_be_visible()` (koje bi prošlo i PRE submita → bezvredan signal). Verbatim iz
  `model_inquiry_success.html` `_oob_aria_live` include message-a.

**`ServicePage(page, base_url)`** — `service_page.py`
- `goto(locale="sr")`; `open_mobile_nav()` (testid `mobile-nav-toggle`);
  `fill_form(name, phone, email="", machine_type="tractor", brand_model="", description)`;
  `attach_photo(path)` (set_input_files na `#service-photos`); `submit()`;
  `expect_success()`; `expect_server_validation_error()` (AC3b).
- Konstante: `SERVICE_SUCCESS_SUBSTRING = "Vaš servisni zahtev je primljen"`,
  `SERVICE_ARIA_ANNOUNCEMENT = "Servisni zahtev je poslat"`.
- **aria-live (TEA fix):** `expect_success()` asertuje OOB announcement tekst
  (`to_contain_text(SERVICE_ARIA_ANNOUNCEMENT)`), NE `to_be_visible()` na visually-hidden regionu.

**`AdminProductPage(page, base_url)`** — `admin_product_page.py`
- `login(username, password)` (na `/admin-coric/login/`);
  `goto_add()`; `fill_core_sr(name_sr, slug, brand_index=1)`;
  `add_inline_specification(section="motor", key, value)`; `add_inline_image(path)`;
  `set_status(status)`; `save()`; `expect_saved()`; `expect_admin_changed_message()`;
  `expect_publish_gate_error()`; `reopen_and_expect_status(slug, expected_status)`.
- Konstante: `PUBLISH_GATE_ERROR_SUBSTRING = "Za objavljivanje je potrebno"`,
  `STATUS_DRAFT="draft"`, `STATUS_PUBLISHED="published"`.
- **Inline add-row (TEA fix):** SVI Product inline-ovi su `extra = 0` (apps/products/admin.py)
  → add forma NEMA praznih inline redova; `#id_<prefix>-0-*` polja NE postoje dok se ne
  klikne Django dynamic-inline „Add another" link (`#<prefix>-group tr.add-row a`).
  `add_inline_specification` / `add_inline_image` PRVO kliknu `_add_inline_row(group_id)`
  (`specifications-group` / `images-group`), TEK ONDA popune `-0-` polja. Bez ovog klika
  selektor not-found (NE zato što markup fali nego što formset još nema red).
- **Publish-gate edge (AC4b, TEA fix):** edge test NE sme da koristi prazan `name_sr` —
  `name_sr` je BEZUSLOVNO required na admin formi → prazan name_sr pada na FIELD-level
  required grešku PRE `save_related`, pa „Za objavljivanje je potrebno" NIKAD ne bi bio
  emitovan. Edge daje VALIDAN `name_sr` + ZASEBAN slug (`e2e-test-produkt-gate`) + brend,
  ali IZOSTAVLJA inline sliku galerije I inline spec → gate puca na
  `images.count()==0`/`specifications.count()==0` → `messages.error` + `QuerySet.update`
  revert na Skicu.
- Admin selektori (Django stock — NE dodajemo testid osim ako se markup pokaže nestabilnim):
  `#id_username`, `#id_password`, `#id_name_sr`, `#id_slug`, `#id_brand`, `#id_status`,
  `#id_is_published`, `#specifications-group tr.add-row a` + `#id_specifications-0-section/-key_sr/-value_sr`,
  `#images-group tr.add-row a` + `#id_images-0-image`, `.messagelist`, `input[name="_save"]`.

---

## 7. RED verifikacija (na ovom Windows host-u)

- **Python syntax (py_compile + AST):** svih 10 `.py` fajlova VALIDNO.
- **Collection:** PADA na 2 nivoa (oba očekivana RED signala):
  1. `pytest-playwright` **MISSING** (Task 1.1 nije urađen → `page`/`browser` fixtures ne postoje).
  2. `libmagic` ImportError tokom Django admin autodiscover
     (`apps/media_pipeline/pdf_utils.py:32 import magic`) — dokumentovani Windows baseline;
     E2E je dizajniran za Docker/CI, NE Windows host.
- **`e2e` marker:** NIJE registrovan u pyproject.toml (AC13 nije urađen).

**Zašto RED (sve nedostaje dok Dev ne instrumentuje):**
`pytest-playwright` dep + `e2e` marker + `seed_e2e_data` command + AC12 Subcategory/ProductImage
setup + `data-testid` delta (6 hook-ova) + env-driven superuser + axes-flush command poziv.
Posle GREEN-a suite se vozi headless u Docker/CI (NE Windows-host gate — AC9.3).

---

## 8. Test inventar

3 spec fajla + conftest + 4 page objekta + 1 asset:
- `tests/e2e/test_marko_buys_traktor.py` (UJ-1) — 2 testa × {sr-full, hu-locale_only} param na
  glavnom + 1 direct-detail = **3 test case-a**.
- `tests/e2e/test_stojan_service_request.py` (UJ-2) — glavni × {sr-full, hu-locale_only} +
  1 skip-ovan AC3b edge = **3 test case-a**.
- `tests/e2e/test_marijana_adds_product.py` (UJ-3) — happy + publish-gate-edge + locale-tabs
  × {hu, en} = **4 test case-a**.

Ukupno ~**10 test funkcija → ~14 parametrizovanih case-ova**.
