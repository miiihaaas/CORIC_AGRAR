---
story-id: 9-8-playwright-e2e-testovi-za-3-uj-a
title: Playwright E2E Testovi za 3 ključna User Journey-a (UJ-1/UJ-2/UJ-3)
epic: 9
module: tests/e2e
status: ready-for-dev
risk-tier: HIGH
base-branch: epic-9
depends_on: [9-7, 1-9, 8-1, 8-6]
forward-dep: [9-9]
---

# Story 9.8: Playwright E2E Testovi za 3 ključna User Journey-a

Status: ready-for-dev

## Opis (Description)

As a **dev**,
I want **automatizovan Playwright E2E test suite za 3 ključna user journey-a (Marko kupuje traktor, Stojan šalje servisni zahtev, Marijana dodaje proizvod u admin)**,
so that **regresije na revenue/lead-critical path-evima (katalog/filter, HTMX lead forme, admin publish) budu uhvaćene automatski pre go-live-a i na svaki staging push**.

**SPECIJALNA STORY — deliverable je TEST SUITE, ne nova feature.** Funkcionalnost koju
journey-i prolaze (katalog + live-filter, HTMX lead/servis forme, admin product CRUD + publish-gate)
**već postoji i merged je** kroz Epike 1–8. Implementacija ove story-je se sastoji od:

1. Pisanja 3 Playwright spec fajla (Python — `pytest-playwright`, NE Node) sa page object pattern-om.
2. Instrumentacije postojećih template-a `data-testid` hook-ovima gde su selektori potrebni (ne-invazivno, dijakritika-bezbedno).
3. Playwright konfiguracije + `conftest.py` fixtures (base_url, seeded DB, dev-only superuser provisioning).
4. `just e2e` recepta + CI integracije (E2E se vozi na **staging** push, NE na `master`/`main`).

E2E cilja **determinističke slug-ove iz Story 9-7 seed manifesta** (`seed_sample_data` command).
9-7 je TVRD preduslov — bez seed-ovanih podataka E2E nema determinističke fixtures.

**Host/CI realnost (vidi Dev Notes):** native Windows host pytest collection pada na `libmagic`
(dokumentovan baseline) i ne mora da pokrene Playwright browsere lokalno. E2E je dizajniran da se
vozi protiv **Dockerizovane app** (Django + Postgres iz `compose/local.yml`) sa 9-7 seed-om,
headless. **Autoritativni E2E runner je GitHub Actions CI.** Story NE zahteva green-on-Windows-host —
zahteva korektnu konfiguraciju + RED potvrdu + CI-runnable suite.

## Acceptance Criteria

- [ ] **AC1 — `tests/e2e/conftest.py` Playwright fixtures + seed + dev superuser provisioning.**
  `tests/e2e/conftest.py` postoji i obezbeđuje: (a) `base_url` fixture (env-driven `E2E_BASE_URL`,
  default `http://localhost:8000`); (b) garanciju da je baza seed-ovana 9-7 `seed_sample_data`
  command-om (idempotentno; pokreće se kao session-scoped setup ili je dokumentovan kao CI step);
  (c) **dev-only superuser provisioning** preko `createsuperuser --noinput` sa env-driven
  `DJANGO_SUPERUSER_USERNAME`/`_EMAIL`/`_PASSWORD` (ILI ekvivalentan `get_or_create` u fixture-u);
  **NIKAD hardkodovan realan password** — kredencijali dolaze iz env-a/CI secrets. Fixture je
  idempotentan (re-run ne pada ako superuser već postoji). **(d) MANDATORY axes-flush (NE opciono):**
  conftest MORA, PRE admin login fixture-a (UJ-3), očistiti `django-axes` stanje
  (`AccessAttempt.objects.all().delete()` + cache flush, ili `axes_reset`) da Epic 8-1 lockout iz
  prethodnih/paralelnih run-ova NE flap-uje admin login. Ovaj korak je OBAVEZAN deo conftest setup-a
  (vidi Task 2.4 / Dev Note „Admin (UJ-3)"), ne best-effort.

- [ ] **AC2 — `test_marko_buys_traktor.py` (UJ-1, anon, desktop) — pun flow + locale sample.**
  Spec prolazi: `/` → klik *Traktori* → `/sr/traktori/` listing → HTMX live-filter **SAMO po snazi**
  (`snaga_min=61` → `agri-tracking-tb804` 80 KS i `saillong-sl904` 90 KS vidljivi, `wuzheng-wz504`
  50 KS filtriran VAN) → **assert slug-scoped** prisustvo/odsustvo KONKRETNIH traktorskih kartica
  (NE grid count; vidi AC9) → klik product kartice *Agri Tracking TB804* (cela kartica klikabilna,
  `data-testid="tractor-card-agri-tracking-tb804"`) → `/sr/proizvod/agri-tracking-tb804/`
  → **galerija/Lightbox vidljiva (zavisi od E2E setup-a iz AC12 koji dodaje ≥1 `ProductImage`;
  bez te slike `<section id="product-gallery">` se NE renderuje — `{% if product.images.all %}`)** →
  Specifikacije akordion (Motor default-open) → skrol do model-inquiry forme
  (`data-testid="model-inquiry-form"`; polje *Model* readonly auto-popunjeno na `product.name`) →
  popuni 4 polja (Ime, Email opciono Telefon, Poruka — `Model` je readonly, NE unosi se) → submit
  (HTMX) → **assert** success kartica preko **substring** `to_contain_text("Vaš upit za model je
  primljen")` (REALNI string: *„Hvala! Vaš upit za model je primljen. Javićemo vam se uskoro."*) +
  aria-live announcement (`#aria-live` region) vidljiv. **NAPOMENA:** UJ-1 koristi model-inquiry
  formu sa product-detail strane (`_model_inquiry_form_fields.html`) — ona NEMA cenu/price filter u
  flow-u; cena filter se NE koristi u TB804 aserciji (TB804 = €28.500 > €25.000, pao bi pod
  „cena ≤ 25.000" — vidi C-6/Dev Notes). Locale sample: core flow se **parametrizuje** (pytest
  `parametrize`) na `sr` + 1 sample `hu`/`en` varijanti unutar ISTOG spec fajla (locale-aware slug,
  `<html lang>` ažuriran; ako hu/en sadržaj nije seed-ovan — OQ-2 — sample se scope-uje na
  locale-routing/`<html lang>`, ne pun sadržaj). **Parametrize NOSI scope flag** —
  `("sr","full")` vs `("hu"|"en","locale_only")` — da dev EKSPLICITNO razdvoji pun-sadržaj-flow
  od locale-only asercije i NE napiše content-asercije koje hu/en (neseed-ovan) ruše.

- [ ] **AC3 — `test_stojan_service_request.py` (UJ-2, anon, MOBILE viewport) — mobile + file upload + locale sample.**
  Spec postavlja mobile viewport (<768px) → otvara hamburger nav (`.navbar-toggler.coric-nav__hamburger`,
  `data-testid` dodaje se u AC8 delti) → `/sr/servis` → popunjava servisnu formu (Ime, Telefon,
  Email opciono, *Vrsta mehanizacije* `<select name="machine_type">`, *Brend i model* slobodan unos,
  *Opis kvara*) → **prilaže fotografiju preko plain `<input type="file" name="photos" multiple>`**
  (`page.set_input_files(...)` — REALNOST: ovo je obični multipart file input sa labelom
  *„Fotografije kvara (do 3, JPG/PNG)"*; **NEMA** „Dodaj sliku" dugmeta, **NEMA** thumbnail
  preview-a, **NEMA** X-remove widget-a — vidi C-8 / Dev Notes) → submit (HTMX) → **assert** success
  preko **substring** `to_contain_text("Vaš servisni zahtev je primljen")` (REALNI string:
  *„Hvala! Vaš servisni zahtev je primljen. Javićemo vam se uskoro."*) + aria-live (`#aria-live`).
  Locale sample: 1 `hu`/`en` parametrizovana varijanta. Selektori `data-testid` na mobile nav toggle,
  file input-u (`data-testid` delta AC8), success kartici (`data-testid` delta AC8); form polja VEĆ
  imaju stabilne `id`-jeve (`#service-name`, `#service-phone`, `#service-machine-type`, …) + forma ima
  `data-testid="service-form"` / submit `data-testid="service-submit"` (postoje).

- [ ] **AC3b — UJ-2 server-side >5MB foto edge (server validacija, NE client preview).** Edge
  asercija (opciono u istom spec-u ILI deferred): prilaganje fotografije > 5 MB → submit → server
  vraća **validacionu grešku u response-u** (forma re-render sa bound error, `coric-contact-form__error`/
  `coric-contact-form__alert`). Validacija je **SERVER-side** (`media_pipeline`/forma), NE
  „greška PRE upload-a" client-side — taj JS widget NE postoji i **NE sme da se gradi u ovoj E2E
  story-ji** (scope creep). Ako je edge previše krhak za v1 E2E (tačan size/MIME prag — OQ-1),
  može se markirati `@pytest.mark.skip(reason="deferred — server-side upload validation edge")` uz
  Dev Note; AC3b NE sme da blokira green core flow AC3.

- [ ] **AC4 — `test_marijana_adds_product.py` (UJ-3, ADMIN, auth) — login + create + publish-gate + appears-on-public + edge.**
  Spec prolazi: `/admin-coric/` login (username/email + password iz env/fixture) → admin dashboard →
  *DODAJ PROIZVOD* → product forma (Naziv, opis, kategorija/brend/serija, ključne karakteristike
  + Specifikacije inline + Galerija slike inline) → unos na **SR**, HU/EN prazno → status **Objavljeno**
  + ≥1 inline `ProductImage` slika + ≥1 inline `ProductSpecification` → Sačuvaj → **PRIMARNA
  ASERCIJA (poslovni signal):** otvori PUBLIC `/sr/proizvod/<slug>/` (anon kontekst) i **assert da je
  proizvod dostupan i objavljen** (HTTP 200 + `data-testid="product-detail-page"` vidljiv) — to je
  smislena cross-surface potvrda objave. **Dodatno (opciono):** assert Django admin standardnu
  success poruku preko **substring** na `.messagelist` (npr. `was changed successfully` / lokalizovani
  ekvivalent). **NE asertuj nepostojeći toast** *„Proizvod '...' je objavljen."* — `save_related`
  taj string NIKAD ne emituje (vidi C-2 / Dev Notes; admin emituje samo `messages.error` na fail).

- [ ] **AC4b — UJ-3 publish-gate edge (error poruka + revert na Skicu, NE „link na polja").** Edge:
  pokušaj statusa **Objavljeno** BEZ kompletnog SR sadržaja (nedostaje SR Naziv ILI ≥1 slika galerije
  ILI ≥1 specifikacija) → Sačuvaj → **assert** (a) `messages.error` poruka koja sadrži substring
  *„Za objavljivanje je potrebno"* na `.messagelist`, **I** (b) da je status posle save-a vraćen na
  **Skica** (`is_published=False` + `status=Skica`) — re-open forme pokazuje Skicu. To je REALNO
  ponašanje (`save_related` graceful `messages.error` + `QuerySet.update()` revert OBA flag-a;
  vidi Dev Notes). **NE asertuj** „blokirano sa linkom na nedostajuća polja" — takav link NE postoji.
  Admin je na `/admin-coric/` (Epic 8 hardening, van i18n prefiksa).

- [ ] **AC5 — Page object pattern.** Svi specovi koriste page object pattern u
  `tests/e2e/page_objects/` (npr. `tractor_listing_page.py`, `product_detail_page.py`,
  `service_page.py`, `admin_product_page.py`). Selektori i akcije su enkapsulirani u page objektima,
  NE inline u spec-ovima (DRY + održivost).

- [ ] **AC6 — `just e2e` recept.** `justfile` ima `e2e` recept koji pokreće Playwright E2E suite
  (headless) protiv pokrenute, seed-ovane app (Docker dev stack ili `E2E_BASE_URL`). Recept je
  dokumentovan (kako podići stack + seed pre pokretanja).

- [ ] **AC7 — CI vozi E2E na staging push (NE na master/main fast loop) — PRIMARNO self-contained.**
  CI je konfigurisan da pokrene E2E suite na push na **`staging`** branch (po project konvenciji: E2E
  je suviše spor za svaki commit). E2E job podiže app + Postgres, seed-uje 9-7, instalira Playwright
  browsere (`playwright install --with-deps chromium`), vozi headless. NE blokira fast PR/feedback loop.
  **Sekvenciranje (mora biti dokumentovano — vidi Dev Note „CI sequencing"):** `deploy.yml` VEĆ
  triggeruje na `staging` push (deploy na staging box), pa E2E job NE sme implicitno da zavisi od
  tog deploy-a. **PRIMARNI (preporučeni, default) pristup je SELF-CONTAINED:** E2E job u GitHub
  Actions sam diže svoj Postgres service + Django + seed unutar job-a i cilja
  `E2E_BASE_URL=http://localhost:8000` — nezavisan od deploy-a i OQ-3 staging URL-a (sigurnija
  default opcija, deterministički ephemeral env). **ALTERNATIVA (env-driven):** vožnja PROTIV
  deploy-ovanog staging URL-a — onda E2E job MORA biti `workflow_run`-zavisan od `deploy.yml`
  (čeka completed+success) i čita `E2E_BASE_URL` iz staging URL secret-a (OQ-3). Story bira
  self-contained kao primarni; staging-URL mode je env-driven opcija, ne default.
  **NAPOMENA (branch realnost):** default branch projekta je **`master`** (ne `main`); `deploy.yml`
  triggeruje na `[staging, main]` — `master` se NE poklapa sa tim listom, pa E2E (staging-only)
  ostaje van glavnog dev push-a kako i treba.

- [ ] **AC8 — `data-testid` DELTA — dodati SAMO ono što GENUINO nedostaje (ne dirati postojeće hook-ove).**
  Mnogi `data-testid` hook-ovi VEĆ postoje (verifikovano grep-om — vidi Dev Notes „Postojeći vs
  nedostajući hook-ovi"): `tractor-filter-form`, `reset-filters-button`, `tractor-results-grid`,
  `tractor-card-<slug>`, `pagination-prev/next`, `model-inquiry-form`, `model-inquiry-submit`,
  `service-form`, `service-submit`, `search-results-container`, `product-detail-page`,
  `product-inquiry-cta`. **NE menjati template-e koji već imaju potreban hook** (Epic 5/6 lekcija:
  diranje postojećeg markup-a rizikuje lomljenje markup-asertujućih testova). GENUINO NEDOSTAJU i
  dodaju se (ASCII-only vrednosti, ne-invazivno, samo atribut):
  - **(1)** success kartice: `model_inquiry_success.html` (`data-testid="model-inquiry-success"`) +
    `service_request_success.html` (`data-testid="service-request-success"`).
  - **(2)** mobile hamburger `.navbar-toggler.coric-nav__hamburger` u `header.html`
    (`data-testid="mobile-nav-toggle"`).
  - **(3)** range-slider hidden inputs u `_filter_form.html`: na `<input type="hidden" name="snaga_min"
    data-range-min-input>` i `name="snaga_max"` dodaj `data-testid="filter-snaga-min"` /
    `"filter-snaga-max"` (i `cena_min`/`cena_max` AKO se koriste u testu). Ovi inputi VEĆ imaju
    `data-range-min-input`/`data-range-max-input` markere (slider JS); dodaje se samo `data-testid`.
  - **(4)** model-inquiry *Model* readonly polje (`data-testid="model-inquiry-model"`) — opciono, za
    aserciju auto-popune; polje je trenutno bez stabilnog selektora.
  - **aria-live region:** VEĆ ima `id="aria-live"` (Playwright cilja preko `#aria-live`) — render-uje
    ga `{% aria_live %}` simple_tag (`apps/core/templatetags/htmx_aria.py`, `mark_safe` string), NE
    `_oob_aria_live.html`. **NE menjati taj tag/string** (Story 1-6 markup-lock); koristiti `#aria-live`
    direktno. `data-testid` na aria-live NIJE potreban.

- [ ] **AC9 — Deterministične filter asercije (slug-scoped među 3 poznata traktora).** UJ-1 filter
  asercije su scope-ovane po **slug-u** — assertuju prisustvo/odsustvo KONKRETNIH traktorskih
  slug-ova (`agri-tracking-tb804`, `wuzheng-wz504`, `saillong-sl904`), NIKAD puki count celog grid-a.
  **ISPRAVKA premise (vidi C-5/Dev Notes):** migration-seed-ovani `tulip-mix-6m3`/`tulip-mix-8m3`
  **NE MOGU** kontaminirati traktorski listing — oni nemaju `subcategory` (brend `tulip`, kategorija
  „prikljucna", `subcategory=None`), pa ih `TractorListView` (filter `subcategory__category__is_for=
  "traktori"`) isključuje istom NULL-JOIN logikom kao i seed-ovane traktore PRE AC12 remedijacije.
  Pravi determinizam dolazi iz: **(1)** AC12 listing-visibility fix (traktori dobijaju `traktori`
  Subcategory); **(2)** slug-scoped asercije među 3 traktora; **(3)** filter se vozi preko hidden
  inputa `snaga_min`/`snaga_max` JS slider-a (vidi AC8/Dev Notes „slider mehanizam").

- [ ] **AC10 — Wait strategija: `expect().to_be_visible()`, NE `sleep`.** Svako čekanje na HTMX/DOM
  promenu koristi Playwright auto-waiting (`expect(locator).to_be_visible()` / `to_have_text()` /
  `to_have_count()`). NEMA `time.sleep()` / `page.wait_for_timeout()` kao primarne sinhronizacije.

- [ ] **AC11 — Nema hardkodovanih kredencijala.** Nijedan spec/fixture/conftest/justfile/CI fajl ne
  sadrži hardkodovan realan password ili tajni token. Admin kredencijali dolaze iz env vars
  (`DJANGO_SUPERUSER_*`) / CI secrets. (Dev-only placeholder string u `.env.example` je OK.)

- [ ] **AC12 — E2E setup GARANTUJE listing-vidljive traktore + ≥1 sliku galerije (REALNI GAP iz 9-7 seed-a).**
  ⚠️ **KRITIČNO — UJ-1 je bez ovoga strukturno nemoguć.** 9-7 `seed_sample_data` kreira traktore sa
  `subcategory=None` (linija ~333: `"subcategory": None`), a `TractorListView.get_queryset()` filtrira
  `subcategory__category__is_for="traktori"` → NULL JOIN ISKLJUČUJE seed-ovane traktore → `/sr/traktori/`
  listing je **PRAZAN** → AC2 „klik TB804 kartice" nemoguć. Dodatno, seed kreira **0 `ProductImage` i
  0 `main_image`** → galerija (`{% if product.images.all %}`) se NIKAD ne renderuje (AC2/Lightbox pada).
  **REMEDIJACIJA (E2E OWNED, scoped na E2E setup — NE menja 9-7 command logiku):** `tests/e2e/conftest.py`
  session-scoped fixture (ili dokumentovan CI setup step) MORA, idempotentno i DEV-only, posle 9-7 seed-a:
  - **(a)** `get_or_create` jedne `traktori` Subcategory pod Category `slug="traktori"` (`is_for="traktori"`)
    i dodeli je trima NOVIM traktorima (`agri-tracking-tb804`, `wuzheng-wz504`, `saillong-sl904`) →
    postaju vidljivi u listing-u;
  - **(b)** `get_or_create` ≥1 `ProductImage` za `agri-tracking-tb804` (dev-only test asset, npr. mali
    placeholder JPG/PNG iz `tests/e2e/assets/`) → galerija + Lightbox (Epic 5 feature) dobiju realno
    E2E pokriće.
  Fixture je idempotentan (re-run ne pravi duplikate; `get_or_create` po `slug`/`(product, order)`).
  **Dev Notes MORA glasno zabeležiti:** ovo je REALAN GAP koji E2E razotkriva — 9-7 seed je proizveo
  **published-ali-nelistirane** traktore i traktore bez ijedne slike. Remedijacija je u E2E setup-u
  (dev/staging only); ako biznis želi da traktori budu listirani van E2E, 9-7 seed treba follow-up
  (logovati kao OQ). **NE ostavljati UJ-1 da asertuje protiv praznog listinga / nepostojeće galerije.**

- [ ] **AC13 — `e2e` pytest marker izoluje E2E suite iz `just test` (unit suite ostaje green).**
  `pyproject.toml` ima `testpaths = ["tests", "apps"]`, pa bi regularni `just test` POKUPIO
  `tests/e2e/` — što pada na libmagic-broken Windows host-u i traži pokrenut browser. Zato:
  - **(a)** registruj `e2e` marker u `[tool.pytest.ini_options].markers` (pored postojećeg `docker`
    markera), npr. `"e2e: Playwright end-to-end suite (Story 9.8); traži pokrenutu seed-ovanu app + browser; deselect sa -m 'not e2e'"`;
  - **(b)** SVAKI E2E spec/test je dekorisan `@pytest.mark.e2e` (modul-level `pytestmark =
    pytest.mark.e2e` u svakom `tests/e2e/test_*.py` je prihvatljiv);
  - **(c)** `just test` ISKLJUČUJE E2E (dodaj `-m 'not e2e'` u `addopts` u `pyproject.toml`,
    ILI u `test` recept u `justfile`) → default unit suite ostaje green i NE pokušava browser/libmagic;
  - **(d)** `just e2e` recept (AC6) bira ISKLJUČIVO E2E suite (`-m e2e` i/ili `tests/e2e/` path) i NE
    pokreće ostatak suite.
  Cilj: unit i E2E suite su čisto razdvojeni — jedan komandno ne povlači drugi.

## Tasks / Subtasks

- [x] **Task 1 — Dev deps + Playwright browseri.**
  - 1.1 Dodaj `pytest-playwright` u `[dependency-groups].dev` u `pyproject.toml` (`playwright>=1.60.0`
    VEĆ postoji — dodaj samo `pytest-playwright`). Regen `uv.lock` (`uv lock`).
  - 1.2 Dokumentuj `playwright install --with-deps chromium` (browser binarije) kao setup korak
    (u justfile recept-u i CI-ju; NE u uv.lock).
  - 1.3 **`e2e` marker izolacija (AC13):** registruj `e2e` marker u
    `[tool.pytest.ini_options].markers` (pored postojećeg `docker` markera) i dodaj `-m 'not e2e'`
    u `addopts` (ILI u `test` recept u `justfile`) da `just test` NE pokupi `tests/e2e/`
    (libmagic/browser-free unit suite ostaje green). `addopts` trenutno = `--import-mode=importlib`
    → postaje `--import-mode=importlib -m 'not e2e'`.

- [x] **Task 2 — `tests/e2e/` scaffolding.**
  - 2.1 Kreiraj `tests/e2e/__init__.py`, `tests/e2e/conftest.py`, `tests/e2e/page_objects/__init__.py`.
  - 2.2 `conftest.py`: `base_url` fixture (env `E2E_BASE_URL`, default `http://localhost:8000`);
    seed garancija (poziv `seed_sample_data` ili dokumentovan CI step); **dev superuser fixture**
    (`createsuperuser --noinput` env-driven, idempotentan, NIKAD hardkodovan password — AC1/AC11).
  - 2.3 **AC12 listing-visibility + galerija remedijacija (E2E OWNED, DEV-only, idempotentno):**
    session-scoped fixture posle 9-7 seed-a (a) `get_or_create` `traktori` Subcategory pod Category
    `slug="traktori"` + dodeli je trima NOVIM traktorima (da `TractorListView` ih više ne isključuje
    NULL-JOIN-om); (b) `get_or_create` ≥1 `ProductImage` za `agri-tracking-tb804` (dev test asset iz
    `tests/e2e/assets/`). BEZ ovoga UJ-1 je strukturno nemoguć (prazan listing + 0 galerija).
  - 2.4 **MANDATORY axes-flush conftest korak (NE opciono):** pre admin login fixture-a očisti
    `django-axes` stanje (`AccessAttempt.objects.all().delete()` + cache flush, ili `axes_reset`)
    da Epic 8-1 lockout iz prethodnih run-ova/paralelnih testova NE flap-uje admin login (UJ-3).
  - 2.5 Page object skeleti u `tests/e2e/page_objects/`: `tractor_listing_page.py`,
    `product_detail_page.py`, `service_page.py`, `admin_product_page.py` (selektori = `data-testid`/`id`).

- [x] **Task 3 — `test_marko_buys_traktor.py` (UJ-1).** Pun flow per AC2, locale-parametrizovan
  (`sr` + 1 `hu`/`en`). Filter: **SAMO `snaga_min=61`** (slug-scoped — AC9; cena filter se NE koristi
  za TB804 jer €28.5k > €25k). Galerija asercija zavisi od AC12 setup-a (≥1 `ProductImage`).
  Model-inquiry: `Model` polje je readonly (ne unosi se). Wait = `expect().to_be_visible()` (AC10).
  **Svi E2E specovi (Task 3/4/5) nose `@pytest.mark.e2e` (modul-level `pytestmark = pytest.mark.e2e`)
  da `just test` sa `-m 'not e2e'` ne pokuša da ih kolektuje/pokrene — AC13.**
  **Locale parametrize NOSI scope flag (OQ-2):** `parametrize` vrednosti su `("sr", "full")` i
  `("hu"|"en", "locale_only")` — `full` vozi pun sadržaj-flow, `locale_only` asertuje SAMO
  locale-routing (lokalizovani URL) + `<html lang>`; dev NE piše content-asercije za hu/en
  (sadržaj nije seed-ovan). Isto važi za locale sample u Task 4.

- [x] **Task 4 — `test_stojan_service_request.py` (UJ-2).** Mobile viewport + hamburger + servis
  forma + **plain file upload (`set_input_files` na `<input type=file name=photos multiple>`; NEMA
  preview/X-remove widget-a — AC3)** + (opciono/deferred) server-side >5MB edge per AC3b. Locale
  sample. Page object reuse.

- [x] **Task 5 — `test_marijana_adds_product.py` (UJ-3).** Admin `/admin-coric/` login (axes-flush iz
  Task 2.4) + create Objavljeno (+ inline slika + inline spec) + **appears-on-public assert kao
  PRIMARNI signal** (AC4) + publish-gate edge: `messages.error("Za objavljivanje je potrebno…")` +
  revert na Skicu (AC4b). **NE asertovati nepostojeći „je objavljen" toast.**
  **FIKSAN deterministički slug:** proizvod se kreira sa FIKSNIM naslovom `„E2E Test Produkt"` →
  slug `e2e-test-produkt` da je public-asercija URL (`/sr/proizvod/e2e-test-produkt/`) STABILAN i da
  se re-run-ovi ne sudaraju. Conftest/fixture čisti (ILI `get_or_create`-guard-uje) bilo koji
  prethodni `e2e-test-produkt` PRE testa → ponovljeni run-ovi su idempotentni (vidi Dev Note
  „UJ-3 fiksan slug + idempotentnost").

- [x] **Task 6 — `data-testid` DELTA u template-e (AC8) — SAMO nedostajuće, ne dirati postojeće.**
  Grep-om potvrđeni POSTOJEĆI hook-ovi (`tractor-filter-form`, `reset-filters-button`,
  `tractor-results-grid`, `tractor-card-<slug>`, `model-inquiry-form/submit`, `service-form/submit`,
  `product-detail-page`, `product-inquiry-cta`, `search-results-container`) se **NE DIRAJU**
  (Epic 5/6 markup-lock lekcija). Dodaj ASCII `data-testid` SAMO u:
  - `templates/forms/partials/model_inquiry_success.html` → `data-testid="model-inquiry-success"`.
  - `templates/forms/partials/service_request_success.html` → `data-testid="service-request-success"`.
  - `templates/partials/header.html` → `.navbar-toggler.coric-nav__hamburger` `data-testid="mobile-nav-toggle"`.
  - `templates/products/partials/_filter_form.html` → hidden inputi `name="snaga_min"`/`"snaga_max"`
    (i `cena_*` ako se koriste) dobijaju `data-testid="filter-snaga-min"`/`"filter-snaga-max"` (već
    imaju `data-range-min-input`/`data-range-max-input` markere — dodaje se samo `data-testid`).
  - (opciono) `templates/forms/partials/_model_inquiry_form_fields.html` → `Model` readonly input
    `data-testid="model-inquiry-model"`.
  - **NE menjati** `apps/core/templatetags/htmx_aria.py` (`aria_live()` tag) — aria-live region VEĆ ima
    `id="aria-live"`, Playwright cilja preko `#aria-live` (Story 1-6 markup-lock).
  - **NAPOMENA:** admin (UJ-3) već ima stabilne Django admin selektore (`id_*` / `.messagelist` / CSS);
    `data-testid` se dodaje SAMO ako se pokaže da admin markup nije dovoljno stabilan.

- [x] **Task 7 — `just e2e` recept (AC6/AC13).** Dodaj u `justfile` recept koji vozi
  ISKLJUČIVO E2E suite — `pytest -m e2e tests/e2e/` (ili kroz Docker) headless protiv pokrenute
  seed-ovane app; komentariši prereqs (podigni `just dev`, pokreni `seed_sample_data`,
  `playwright install`). Recept bira SAMO E2E (`-m e2e` / `tests/e2e/` path), dok `just test`
  (sa `-m 'not e2e'` iz Task 1.3) NE povlači E2E — dve suite su komandno razdvojene.

- [x] **Task 8 — CI workflow update (AC7).** Dodaj E2E job/workflow koji se trigeruje na `staging`
  push (NE `master`/PR fast loop). **PRIMARNO self-contained:** job sam diže Postgres service + Django
  + `seed_sample_data --force` + AC12 remedijaciju, `playwright install --with-deps chromium`,
  `pytest -m e2e tests/e2e/` headless protiv `E2E_BASE_URL=http://localhost:8000` — NEZAVISNO od
  `deploy.yml` (koji takođe triggeruje na `staging`). Admin password iz CI secret (`DJANGO_SUPERUSER_*`).
  Dodaj zaseban `e2e.yml` (čistije od mešanja sa deploy-om). **ALTERNATIVA (ako se cilja deploy-ovan
  staging URL):** `workflow_run`-zavisnost od `deploy.yml` (completed+success) + `E2E_BASE_URL` iz
  staging URL secret-a (OQ-3) — env-driven, NE default. **NE praviti E2E job da implicitno trči pre
  ili paralelno sa deploy-om uz pretpostavku gotovog staging-a.**

- [ ] **Task 9 — RED verifikacija → GREEN.**
  - 9.1 RED: pokreni suite protiv app BEZ `data-testid` hook-ova / pre seed-a → potvrdi smislen
    fail (selektor not found / element not visible), NE collection-error.
  - 9.2 GREEN: posle Task 6 hook-ova + 9-7 seed-a → suite prolazi headless u Docker/CI.
  - 9.3 Story NE zahteva green-on-Windows-host (libmagic baseline + browser launch); CI je autoritet.

## Dev Notes

### Seed manifest (9-7 — TVRD preduslov)
- Seed command: `python manage.py seed_sample_data` (DEBUG=True dev) ili `--force` na staging/CI. Idempotentan.
- TRAKTORI kategorija slug: `traktori`. Brend slug-ovi: `wuzheng`, `agri-tracking`, `saillong`.
- Objavljeni NOVI traktori: `agri-tracking-tb804` (80 KS / 2024 / €28.500 — **UJ-1 headline + UJ-2 inquiry target**),
  `wuzheng-wz504` (50 KS / 2023 / €19.900), `saillong-sl904` (90 KS / 2025 / €32.400).
- URL-ovi: product detail `/sr/proizvod/<slug>/`; brand detail `/sr/traktori/<brand-slug>/`; traktori listing `/sr/traktori/`.
- HTMX form endpoint-i: `/sr/htmx/forme/kontakt/`, `/sr/htmx/forme/upit-za-model/`, `/sr/htmx/forme/servis/`, `/sr/htmx/forme/rezervni-delovi/`.

### ⚠️ KRITIČAN GAP — listing-visibility + 0 galerija (C-1/C-3, AC12)
- **9-7 seed kreira traktore sa `subcategory=None`** (`seed_sample_data._seed_products`, `"subcategory": None`).
  `TractorListView.get_queryset()` filtrira `is_published=True, subcategory__category__is_for="traktori"`.
  NULL JOIN na `subcategory` → seed-ovani traktori **NISU u listing-u** → `/sr/traktori/` PRAZAN.
- **Seed kreira 0 `ProductImage` i 0 `main_image`** (samo `ProductSpecification` za TB804). Galerija
  `product_detail.html` je gated na `{% if product.images.all %}` → **NIKAD se ne renderuje** → kartica
  na listingu nema sliku, detail strana nema galeriju/Lightbox.
- **Posledica:** UJ-1 (AC2) je bez remedijacije strukturno nemoguć. **AC12** uvodi E2E-owned, DEV-only,
  idempotentnu remedijaciju u `conftest.py` (dodaj `traktori` Subcategory + dodeli je 3 traktora; dodaj
  ≥1 `ProductImage` za `agri-tracking-tb804`). Ovo je REALAN proizvodni gap koji E2E razotkriva —
  published-ali-nelistirani traktori; ako biznis hoće traktore listirane van E2E, 9-7 seed treba
  follow-up (OQ).

### ⚠️ Filter-determinizam (AC9 — ISPRAVLJENO, prethodni caveat je bio POGREŠAN)
- **PREĐAŠNJA TVRDNJA JE BILA NETAČNA:** ranija verzija je tvrdila da `tulip-mix-6m3`/`tulip-mix-8m3`
  „leak-uju" u traktorski filter jer su `condition=new`. **REALNOST (verifikovano):** ti proizvodi
  (migration `apps/brands/migrations/0004_seed_hzm_tulip_brands.py`) imaju brend `tulip`, kategoriju
  „prikljucna/hzm", i **`subcategory=None`** → `TractorListView` ih isključuje ISTIM NULL-JOIN-om kao
  i seed-ovane traktore. **NE mogu da kontaminiraju traktorski listing** bez obzira na `condition`.
- **PRAVI determinizam (AC9):** posle AC12 listing-fix-a, filter asercije su **slug-scoped** među 3
  poznata traktora. UJ-1 koristi **SAMO snagu**: `snaga_min=61` → vidljivi `agri-tracking-tb804` (80KS)
  + `saillong-sl904` (90KS), filtriran VAN `wuzheng-wz504` (50KS). Assertuj prisustvo/odsustvo
  konkretnih `tractor-card-<slug>` lokatora, NIKAD puki grid count.
- **NE koristi cena ≤ 25.000 € u TB804 aserciji** (C-6): TB804 = €28.500 > €25.000 → pao bi pod taj
  prag. Cena filter, ako se uopšte testira, drži se ODVOJEN od TB804 prisustva.

### Admin (UJ-3) — REALNO ponašanje publish-gate-a (C-2 ISPRAVKA)
- Login na `/admin-coric/` (Epic 8 hardening — NE `/admin/`, van i18n prefiksa).
- Seed NE kreira kredencijale (9-7 SM-D7). E2E provizionira **dev-only superuser** preko
  `createsuperuser --noinput` sa env `DJANGO_SUPERUSER_USERNAME`/`_EMAIL`/`_PASSWORD` (ili `get_or_create`
  u fixture-u). **NIKAD hardkodovan realan password** (AC11).
- **MANDATORY axes-flush (Task 2.4, NE opciono):** Epic 8-1 `django-axes` lockout može da flap-uje
  admin login (prethodni run-ovi / paralelni testovi / deljeni cache). Conftest MORA da očisti
  `AccessAttempt` + axes cache PRE login fixture-a. E2E koristi ISPRAVNE kredencijale (nema brute-force
  petlje), ali lockout state iz okruženja je realan rizik → flush je obavezan, ne „ako flap-uje".
- **Publish success NEMA poseban toast (C-2):** `ProductAdmin.save_related` (apps/products/admin.py)
  na USPEŠNU objavu NE emituje nikakvu „Proizvod '...' je objavljen." poruku — prolazi stock Django
  admin `was changed successfully` (lokalizovano). **AC4 PRIMARNA asercija = appears-on-public**
  (`/sr/proizvod/<slug>/` HTTP 200 + `product-detail-page`); admin-message substring je opcioni dodatak.
- **Publish-gate edge (Epic 8-6, AC4b) — REALNO:** status `Objavljeno` bez (SR Naziv ∨ ≥1 galerija slika
  ∨ ≥1 spec) → `save_related` NE raise-uje (to bi bilo HTTP 500); umesto toga emituje
  `messages.error("Za objavljivanje je potrebno: …")` i radi `QuerySet.update(is_published=False,
  status=DRAFT)` revert OBA flag-a (bypass `save()/full_clean`). **NEMA „link na nedostajuća polja".**
  UJ-3 edge asertuje: error-poruka substring *„Za objavljivanje je potrebno"* + status vraćen na Skicu.

### UJ-3 fiksan slug + idempotentnost (I-3)
- Proizvod koji UJ-3 admin test kreira koristi **FIKSAN, deterministički naslov** `„E2E Test Produkt"`
  → Django `slugify` daje `e2e-test-produkt`. Public cross-surface asercija onda cilja STABILAN URL
  `/sr/proizvod/e2e-test-produkt/` — nema random sufiksa, re-run-ovi ne prave nove slug-ove.
- **Idempotentnost:** conftest/fixture PRE UJ-3 testa obriše (ILI `get_or_create`-guard-uje) eventualni
  ranije kreiran `e2e-test-produkt` (i njegove inline `ProductImage`/`ProductSpecification` ako FK
  CASCADE ne pokriva), da ponovljeni run na istoj (dev/staging) bazi ne padne na unique-slug koliziju
  ili na „već postoji" stanje. Ova provera je DEV-only (isti scope kao AC12 remedijacija).
- **NAPOMENA:** ovo je RAZLIČIT slug od 9-7 seed traktora (`agri-tracking-tb804` itd.) — UJ-3 sam pravi
  svoj test-artefakt i ne dira seed-ovane proizvode.

### Realni success string-ovi (C-4 — verbatim iz template-a)
- Model-inquiry success (`model_inquiry_success.html`): **„Hvala! Vaš upit za model je primljen.
  Javićemo vam se uskoro."** → assert substring `to_contain_text("Vaš upit za model je primljen")`.
- Servis success (`service_request_success.html`): **„Hvala! Vaš servisni zahtev je primljen.
  Javićemo vam se uskoro."** → assert substring `to_contain_text("Vaš servisni zahtev je primljen")`.
- **NE** koristi raniji string „Vaš upit je primljen." — ne postoji u markup-u. Substring/`to_contain_text`
  je preferiran nad equality (otporno na lokale/dijakritiku).

### Filter slider mehanizam (C-7 — kako E2E vozi filter)
- `_filter_form.html` koristi **custom JS range-slider** (`data-range-slider`) koji piše u **hidden
  inpute** `<input type="hidden" name="snaga_min" data-range-min-input>` / `name="snaga_max"
  data-range-max-input>` (+ `cena_min`/`cena_max`). NEMA native `<input type=range>`.
- Forma ima `hx-trigger="input changed delay:300ms, change delay:300ms"` → HTMX re-fetch `#tractor-results`.
- **E2E pristup:** AC8 dodaje `data-testid` na hidden inpute (`filter-snaga-min`/`filter-snaga-max`).
  Page object popunjava hidden input + dispatch-uje `input`/`change` event (npr.
  `locator.fill("61")` + `locator.dispatch_event("change")`) → čeka HTMX swap →
  `expect(tractor_card_locator).to_be_visible()/to_have_count(...)` slug-scoped (AC9/AC10).

### File upload — REALNOST (C-8)
- `_service_request_form_fields.html` ima **plain `<input type="file" name="photos" multiple
  accept="image/jpeg,image/png">`** sa labelom „Fotografije kvara (do 3, JPG/PNG)". **NEMA** „Dodaj
  sliku" dugmeta, **NEMA** thumbnail preview-a, **NEMA** X-remove JS widget-a. E2E koristi
  `page.set_input_files(...)` na file input.
- **>5MB validacija je SERVER-side** (forma/`media_pipeline`), ne client-side „pre upload-a". AC3b edge
  asertuje server-rendered grešku posle submita (bound error / `coric-contact-form__alert`), ILI je
  deferred (`@pytest.mark.skip`). **NE graditi JS preview widget** — scope creep van E2E story-je.

### Postojeći vs nedostajući `data-testid` hook-ovi (C-9 — grep-verifikovano)
- **VEĆ POSTOJE (NE DIRATI):** `tractor-filter-form`, `reset-filters-button` (`_filter_form.html`);
  `tractor-results-grid`, `tractor-card-<slug>`, `pagination-prev`, `pagination-next`
  (`_results_grid.html`); `model-inquiry-form`, `model-inquiry-submit`
  (`_model_inquiry_form_fields.html`); `service-form`, `service-submit`
  (`_service_request_form_fields.html`); `search-results-container` (`header.html`);
  `product-detail-page`, `product-inquiry-cta` (`product_detail.html`).
- **NEDOSTAJE → dodaj (AC8 delta):** `model-inquiry-success`, `service-request-success` (success
  kartice); `mobile-nav-toggle` (`.navbar-toggler.coric-nav__hamburger`); `filter-snaga-min`/
  `filter-snaga-max` (hidden slider inputi); opciono `model-inquiry-model` (readonly Model polje).
- **aria-live region:** `id="aria-live"` rendera `{% aria_live %}` simple_tag u
  `apps/core/templatetags/htmx_aria.py` (`mark_safe` string), NE template partial. Cilj Playwright preko
  `#aria-live`; **NE menjati taj tag** (Story 1-6 markup-lock). Stari Task-6 unos
  `_oob_aria_live.html` → `data-testid="aria-live"` je bio POGREŠAN (taj partial radi samo OOB swap).

### aria-live success-partial pattern
- HTMX forme vraćaju success partial + OOB swap u `_oob_aria_live.html` (Epic 4 standard:
  `htmx_form_endpoint` dekorator + `_oob_aria_live` include). E2E asertuje I success karticu I
  aria-live announcement (`expect(...).to_be_visible()` — AC10).

### `data-testid` dijakritika-bezbedno pravilo (AC8)
- Vrednosti `data-testid` su **ASCII-only** (npr. `data-testid="inquiry-submit"`, NE `"posalji-upit"`
  sa dijakritikom) da bi Playwright selektori bili robustni cross-platform. Vidljiv tekst u UI ostaje
  pun srpski (č/ć/ž/š/đ) — testira se preko `get_by_text` gde je smisleno, ali stabilni hook je `data-testid`.

### Playwright = PYTHON, ne Node (project konvencija)
- `pytest-playwright` (`page` fixture, `expect` iz `playwright.sync_api`). NE `@playwright/test` Node runner.
- `playwright>=1.60.0` je VEĆ u dev deps; dodaj samo `pytest-playwright`. Browser binarije:
  `playwright install --with-deps chromium`.

### Locale parametrizacija (3 spec fajla, ne 9)
- `e2e_count = 3` → tri spec fajla, jedan po journey-u. Svaki journey ima `sr` (primarni, pun flow)
  + 1 sample `hu`/`en` varijantu **parametrizovanu unutar istog spec fajla** (pytest `parametrize`),
  NE kao zasebne fajlove. UJ-3 admin je primarno `sr`; sample varijanta pokriva locale-switch tab u
  formi (SR→HU prazno) umesto pun pre-prod.

### Host / Docker / CI env
- Native Windows host: pytest collect pada na `libmagic` (dokumentovan baseline) + ne mora da pokreće
  browsere. E2E se vozi protiv **Dockerizovane app** (`compose/local.yml`: Django + Postgres) sa 9-7
  seed-om, headless. **Autoritativni runner = GitHub Actions CI** (Story 1-9 / staging trigger).
- Story NE zahteva green-on-Windows-host; zahteva korektnu konfiguraciju + RED potvrdu + CI-runnable.
- CI: E2E na **`staging`** push (AC7), NE `master`/PR fast loop. Zaseban `e2e.yml` (preporučeno) ili
  reuse `deploy.yml` staging trigger pattern.

### CI sequencing — self-contained vs deploy-zavisan (I-2)
- **`deploy.yml` VEĆ triggeruje na `staging` push** (`on.push.branches: [staging, main]` →
  deploy na staging box). Ako se E2E doda kao push-trigger na isti `staging`, OBA workflow-a krenu
  paralelno — E2E NE sme da pretpostavi da je deploy gotov.
- **PRIMARNO (default, sigurnije) — SELF-CONTAINED:** E2E job sam diže ephemeral Postgres service +
  Django + 9-7 seed + AC12 remedijaciju UNUTAR GitHub Actions job-a i cilja
  `E2E_BASE_URL=http://localhost:8000`. Deterministički, OQ-3-nezavisan, nema race sa deploy-om.
- **ALTERNATIVA — DEPLOY-ZAVISAN (env-driven, ne default):** vožnja protiv deploy-ovanog staging
  URL-a → E2E mora biti `workflow_run`-zavisan od `deploy.yml` (`types: [completed]` + guard na
  `conclusion == 'success'`) i čita `E2E_BASE_URL` iz staging URL secret-a (OQ-3). Koristiti SAMO
  ako biznis hoće smoke protiv realnog deploy-a; inače self-contained.
- **Branch realnost:** default branch je **`master`** (ne `main`); `deploy.yml` lista je
  `[staging, main]`. E2E (AC7) je `staging`-only — `master` push ga ne pokreće, što je željeno
  ponašanje (fast dev loop bez E2E). Ako se ikad doda E2E na `master`, to je svestan go-live izbor.

### Ciljani template fajlovi za AC8 DELTA (samo ovi se diraju — grep-verifikovani putevi)
- `templates/forms/partials/model_inquiry_success.html` → `data-testid="model-inquiry-success"`.
- `templates/forms/partials/service_request_success.html` → `data-testid="service-request-success"`.
- `templates/partials/header.html` → hamburger `.navbar-toggler.coric-nav__hamburger` `data-testid="mobile-nav-toggle"`.
- `templates/products/partials/_filter_form.html` → hidden inputi `snaga_min`/`snaga_max` (i `cena_*`
  ako se koriste) `data-testid="filter-snaga-min"`/`"filter-snaga-max"`.
- (opciono) `templates/forms/partials/_model_inquiry_form_fields.html` → readonly Model input.
- **NE diraj:** `_results_grid.html`, glavne forme (`_model_inquiry_form_fields.html` submit/form,
  `_service_request_form_fields.html` submit/form), `product_detail.html`, `_oob_aria_live.html`,
  `apps/core/templatetags/htmx_aria.py` — svi imaju potrebne hook-ove ili su markup-lock (C-9).

## Risk / Test tier

**HIGH.** E2E pokriva auth/admin login (Epic 8 hardening + axes), lead/servis HTMX forme + file
upload, publish-gate, locale routing — sve revenue/lead-critical. Plus rizik je u SAMOJ test infra
(flaky waits, seed-determinizam, dev-superuser provisioning bez secret leak-a). Test pristup:
Playwright E2E (3 speca, locale-parametrizovani) + page object pattern; RED-potvrda pa GREEN u
Docker/CI (NE Windows-host gate). `needs_e2e: true`, `e2e_count: 3`.

## Open Questions (go-live gates)
- **OQ-1:** Egzaktan threshold za UJ-1 RAZREŠEN u story-ji: **`snaga_min=61`** (TB804 80KS +
  SL904 90KS unutra; WZ504 50KS van) — SAMO snaga, bez cene (C-6). Otvoreno ostaje samo tačan
  size/MIME prag za AC3b >5MB edge (server-side) — ako nije lako determinisati, AC3b je deferred.
- **OQ-4 (NOVO — produkt/9-7 follow-up):** 9-7 seed proizvodi published-ali-NELISTIRANE traktore
  (`subcategory=None`) i traktore bez ijedne slike. E2E ovo zaobilazi AC12 setup-om (dev/staging only).
  Ako biznis želi da seed-ovani traktori budu vidljivi na javnom `/sr/traktori/` listing-u i van E2E,
  potreban je 9-7 seed follow-up (dodeli `traktori` Subcategory + bar 1 slika) — go-live odluka za Mihasa.
- **OQ-2:** hu/en prevodi slug-ova/sadržaja deferred u 9-7 (sr-only v1) — locale sample varijanta
  cilja postojeći lokalizovani URL; ako hu/en sadržaj nije seed-ovan, sample se scope-uje na
  locale-routing/`<html lang>` assert, ne pun sadržaj.
- **OQ-3:** Staging E2E box/URL (`E2E_BASE_URL`) + CI secret za `DJANGO_SUPERUSER_PASSWORD` — postaviti pre staging E2E vožnje.
