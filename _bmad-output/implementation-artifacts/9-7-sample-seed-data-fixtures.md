---
story-id: 9-7-sample-seed-data-fixtures
title: Sample Seed Data (DEV-only idempotentni management command)
epic: 9
status: ready-for-dev
risk-tier: MEDIUM
base-branch: epic-9
depends_on: [2-1, 2-2, 5-1, 3-4, 7-1, 7-4, 8-x]
forward-dep: [9-8]
---

# Story 9.7: Sample Seed Data (DEV-only idempotentni management command)

Status: ready-for-dev

## Story

As a **dev**,
I want **idempotentan DEV-only Django management command koji puni bazu realnim demo content-om (traktori + mehanizacija + blog)**,
so that **lokalni dev / staging demo ima realan sadržaj i Story 9-8 Playwright E2E može da cilja determinističke, unapred poznate slug-ove**.

## Opis (Description)

Epic 9 (Go-Live Readiness) traži „sample seed data" da prod/staging deploy ima realan content
za demo i da Story 9-8 (Playwright E2E za 3 user journey-a) ima determinističke fixtures.

epics.md 9.7 doslovno traži `tests/fixtures/sample_data.json` + `loaddata`. **Ova story
RECONCILE-uje tu nameru kroz Django-idiomatičniji mehanizam: idempotentan management command
`apps/core/management/commands/seed_sample_data.py`** (vidi SM-D1 za rationale — JSON fixture sa
hardkodovanim PK-ovima bi se sudario sa postojećim get_or_create data-migration seed-ovima u
migracijama `apps/brands/0003`/`0004` i bio bi krhak zbog django-modeltranslation `_sr/_hu/_en`
kolona + cross-app FK-ova).

Command je **ADITIVAN** (referencira postojeće seed-ovane brendove/kategorije kroz get_or_create,
ne duplira ih) i **DEV-only** (hard guard: odbija izvršavanje sa `DEBUG=False` bez `--force`).
Glavni nov sadržaj koji command dodaje je **TRAKTORI strana** (NE postoji u postojećim seed-ovima):
TRAKTORI `Category` + 3 nova brenda (Wuzheng, Agri Tracking, Saillong) + objavljeni traktor
`Product`-i sa `horse_power`/`year`/`price_eur`/`condition` popunjenim — što je tačno ono što
9-8 UJ-1 (filtriranje traktora po snazi/godini/ceni) treba da bi vraćao determinističke rezultate.

Takođe seed-uje 5 polovnih (`condition="used"`) mašina i 3-5 objavljenih blog `Post`-ova
(sa `Category` + `Tag`), i defanzivno osigurava `SiteSettings` singleton.

**Ova story je TVRD preduslov za 9-8.** Sekcija „## Seed Identifiers za 9-8 E2E" je ugovor koji
Siniša predaje 9-8: svi slug-ovi su finalni i ASCII.

## Acceptance Criteria

1. **Command postoji i pokreće se bez greške** — `apps/core/management/commands/seed_sample_data.py`
   postoji; `call_command("seed_sample_data")` na sveže migrirane DEV baze (`DEBUG=True`) izvršava
   se bez izuzetka i ispisuje sažetak kreiranih/postojećih objekata na stdout.

2. **Aditivan, bez kolizije sa postojećim seed-ovima** — command ne duplira i ne ruši postojeće
   migration-seed-ovane objekte. `brands` slug-ovi `jeegee`/`hzm`/`tulip`, kategorije
   `osnovna-obrada-zemljista`/`priprema-zemljista`/`masine-za-setvu`/`radne-masine`, podkategorije
   pod `radne-masine`, i proizvodi `tulip-mix-6m3`/`tulip-mix-8m3` ostaju tačno 1 instanca svaki
   posle pokretanja command-a (command ih referencira kroz get_or_create, ne pravi nove).

3. **Idempotentnost** — svaki objekat se kreira kroz `get_or_create` po prirodnom unique ključu
   koji je UVEK EKSPLICITAN lookup argument (`slug=...` za Brand/Category/Subcategory/Product/blog
   Post/blog Category/blog Tag; `pk=1` za SiteSettings singleton). `slug` se NIKAD ne izvodi
   auto-derivacijom unutar `defaults` (vidi Dev Note „Idempotency — slug je uvek eksplicitan lookup
   ključ"). Dvostruko pokretanje (`call_command` 2×) NE pravi duplikate i NE baca grešku; test tvrdi
   da su brojevi objekata identični posle drugog pokretanja, **I** da egzaktni manifest slug objekti
   i dalje rezolvuju posle 2. pokretanja (npr. `Product.objects.get(slug="agri-tracking-tb804")` ne
   baca i `is_published=True` ostaje) — da uhvati delete-and-recreate-with-different-PK scenario koji
   bi održao count-ove stabilnim ali promenio identitet.

4. **Modeltranslation `_sr` + dijakritika** — za svako translatable polje command popunjava i `_sr`
   kolonu i bazni accessor (npr. `name`+`name_sr`, `description`+`description_sr`,
   `title`+`title_sr`, `perex`+`perex_sr`, `body`+`body_sr`, `key_features`+`key_features_sr`),
   prateći tačno pattern iz `apps/brands/migrations/0004_seed_hzm_tulip_brands.py`. Sav srpski
   UI tekst koristi **pune dijakritike** (č/ć/ž/š/đ) — NIKAD šišana latinica, NIKAD ćirilica.
   Svi slug-ovi su ASCII transliteracija. hu/en MOGU ostati prazni u v1 (mirror postojećih seed-ova).
   Test tvrdi da je npr. `product.name_sr` truthy i da bar jedno polje sadrži dijakritiku.

5. **Production guard (TVRD go-live gate)** — sa `DEBUG=False` i bez `--force`, command baca
   `CommandError("seed_sample_data je DEV-only; odbijam izvršavanje sa DEBUG=False bez --force")`.
   Sa `--force` (uz `DEBUG=False`) command nastavlja izvršavanje. Test pokriva oba puta kroz
   `override_settings(DEBUG=False)`.

6. **Deterministički slug manifest za 9-8** — posle pokretanja command-a postoje TAČNO ovi
   determinstički identifikatori (vidi „## Seed Identifiers za 9-8 E2E"). Podeljeno na 6a (novi
   traktori sa filter determinizmom) i 6b (polovne mašine), oba nezavisno testabilna:

   **AC6 (taksonomija):**
   - TRAKTORI `brands.Category` sa slug-om `traktori` (`is_for="traktori"`).
   - 3 nova traktor brenda: `wuzheng`, `agri-tracking`, `saillong`.

   **AC6a (NOVI traktori — `condition="new"` — filter determinizam):**
   - objavljeni traktor proizvodi sa popunjenim `horse_power`/`year`/`price_eur`,
     `condition="new"`, `is_published=True`, `status="published"`, uključujući headline
     `agri-tracking-tb804` (80 KS / 2024 / €28.500) + bar 2 dodatna sa različitom snagom/godinom/cenom
     (`wuzheng-wz504` 50 KS/2023, `saillong-sl904` 90 KS/2025).
   - **FILTER DETERMINIZAM (TVRD za UJ-1):** TAČNO 2 nova traktora imaju `year >= 2024`
     (`agri-tracking-tb804`=2024 + `saillong-sl904`=2025); TAČNO 1 nov traktor ima `horse_power < 60`
     (`wuzheng-wz504`=50). Polovne mašine NE smeju upasti u te bucket-e (vidi AC6b + Dev Note
     „Filter determinizam").
   - test tvrdi `Product.objects.filter(slug="agri-tracking-tb804", is_published=True, condition="new").exists()`
     i da filter po `horse_power`/`year`/`price_eur` (npr. `year__gte=2024` → tačno 2 NOVA;
     `horse_power__lt=60, condition="new"` → tačno `wuzheng-wz504`) vraća deterministički podskup.

   **AC6b (POLOVNE mašine — `condition="used"`):**
   - 5 polovnih proizvoda, svaki `condition="used"`, `is_published=True`, `status="published"`,
     sa EKSPLICITNO popunjenim `horse_power`/`year`/`price_eur` po Dev Note tabeli „Polovne mašine —
     finalne vrednosti".
   - **DETERMINIZAM GRANICA:** sve polovne mašine imaju `year <= 2022` (NIKAD `>= 2024`) tako da
     `year >= 2024` bucket ostaje tačno 2 NOVA traktora — bez obzira da li 9-8 filtrira preko svih
     published proizvoda ili scope-uje na `condition="new"`. `horse_power` vrednosti polovnih
     (35/45/55/65/75 KS) su izabrane da NE razbiju „`horse_power < 60` (uz `condition="new"`) → samo
     `wuzheng-wz504`" assertion — assertion uvek mora scope-ovati na `condition="new"`.
   - test tvrdi count == 5 polovnih i da nijedna polovna mašina nema `year >= 2024`.

7. **Blog objave objavljene** — command kreira 3-5 `blog.Post` sa `status="published"`,
   `published_at=timezone.now()`, `title_sr`/`perex_sr`/`body_sr` popunjenim, ASCII slug-ovima,
   svaki vezan za bar jednu `blog.Category` + bar jedan `blog.Tag`. `Post.published` queryset ih
   vraća (test tvrdi count ≥ 3 i da headline post slug postoji).

8. **SiteSettings prisutan** — posle command-a postoji `pages.SiteSettings` singleton (`pk=1`).
   Command ga osigurava defanzivno preko `SiteSettings.load()` / `get_or_create(pk=1)` — NE duplira
   migration-auto-seed (`apps/pages/0002`) i NE pravi drugi red.

9. **Testovi prolaze** — `apps/core/tests/test_seed_sample_data.py` pokriva AC1–AC8 (run-no-error,
   aditivnost, idempotentnost uključujući egzaktnu slug-rezoluciju posle 2. pokretanja,
   modeltranslation `_sr`+dijakritika, production guard oba puta, slug manifest, AC6a filter
   determinizam + AC6b polovne `year <= 2022`, blog published count, SiteSettings prisutan). Bez
   novih dependency-ja, bez modifikacije postojećih migracija.

## Tasks / Subtasks

- [x] **Task 1: Skeleton management command + production guard (AC1, AC5)**
  - [x] Kreiraj `apps/core/management/__init__.py` i `apps/core/management/commands/__init__.py` ako ne postoje.
  - [x] Kreiraj `apps/core/management/commands/seed_sample_data.py` sa `class Command(BaseCommand)`.
  - [x] `add_arguments`: `--force` (`action="store_true"`) sa help tekstom; docstring/`help` opisuje DEV-only + kako 9-8 dobija admin usera (createsuperuser, NE seed-ovan password).
  - [x] `handle()`: PRVO production guard — `if not settings.DEBUG and not options["force"]: raise CommandError(...)`.
  - [x] `handle()`: posle guard-a, OBAVI seeding unutar `with transaction.atomic():` (all-or-nothing) tako da `full_clean()` greška usred seed-a NE ostavi polu-seed-ovanu bazu sa zavaravajućim stdout sažetkom (vidi Dev Note „Atomicity"). Sažetak ispiši TEK posle uspešnog izlaska iz atomic bloka.
  - [x] Modeli se učitavaju kroz direktan import (`from apps.brands.models import Brand, Category, Subcategory` itd.) — command radi protiv real modela (NE historical `apps.get_model`).

- [x] **Task 2: Aditivni referenc na postojeće seed-ove (AC2)**
  - [x] `get_or_create(slug=...)` za postojeće brendove (`jeegee`/`hzm`/`tulip`) i kategorije/podkategorije/proizvode samo AKO command treba da ih referencira; inače ih ne dira.
  - [x] Verifikuj da defaults NE prepisuju postojeća polja (get_or_create defaults se primenjuju samo pri kreiranju).

- [x] **Task 3: TRAKTORI seed — Category + 3 brenda + traktor proizvodi (AC4, AC6)**
  - [x] `Category` get_or_create `slug="traktori"`, `is_for="traktori"`, `name`/`name_sr="Traktori"`, `description`/`description_sr` (dijakritika), `display_order`.
  - [x] 3 Brenda: `wuzheng`/`agri-tracking`/`saillong` (`name`+`name_sr`, `description`+`description_sr`, `slogan`+`slogan_sr` opciono, `is_coming_soon=False`).
  - [x] Traktor `Product`-i (`brand` FK PROTECT obavezan; `subcategory=None` — top-tier traktori nemaju drill-down per PR-D3): popuni `name`+`name_sr`, `description`+`description_sr`, `key_features`+`key_features_sr` (MAX 3 stavke — NE prekoračiti ili `clean()` baca), `year`, `price_eur` (Decimal), `horse_power`, `condition="new"`, `is_published=True`, `status="published"`.
  - [x] Headline: `agri-tracking-tb804` (80 KS / 2024 / €28.500); + bar 2 dodatna sa varijabilnom snagom/godinom/cenom za filter pokrivenost (vidi manifest).
  - [x] (Opciono) par `ProductSpecification` za headline traktor (`section`, `key`+`key_sr`, `value`+`value_sr`, `order`) da obogati UJ-1 detail.

- [x] **Task 4: Polovne mašine (AC6b)**
  - [x] 5 `Product`-a sa `condition="used"`, `is_published=True`, `status="published"`; EKSPLICITNO popuni `horse_power`/`year`/`price_eur` po Dev Note tabeli „Polovne mašine — finalne vrednosti" (sve `year <= 2022` za filter determinizam); vezani za seed-ovane brendove kroz get_or_create (npr. `tulip`/`hzm`/traktor brendovi). Slug-ovi iz manifesta (`polovni-traktor-agri-tracking-tb804` headline + 4 ostala).

- [x] **Task 5: Blog seed — Category + Tag + 3-5 Post (AC7)**
  - [x] `blog.Category` get_or_create `slug="ratarstvo"` (`name`+`name_sr`, `description`+`description_sr`).
  - [x] `blog.Tag` get_or_create `slug="zetva"` (`name`+`name_sr`).
  - [x] 3-5 `blog.Post`: `status="published"`, `published_at=timezone.now()`, `title`+`title_sr`, `perex`+`perex_sr`, `body`+`body_sr`, `category` FK, `tags.add(tag)` (M2M posle save), `author=None` (NE seed-uj usera). Headline slug: `pet-saveta-za-prolecnu-setvu`.

- [x] **Task 6: SiteSettings defanzivni get_or_create (AC8)**
  - [x] `SiteSettings.load()` (ili `get_or_create(pk=1)`) — osiguraj prisutnost, NE duplira migration-seed.

- [x] **Task 7: Sažetak na stdout + idempotentnost (AC1, AC3)**
  - [x] Akumuliraj created-vs-existing brojeve; `self.stdout.write(self.style.SUCCESS(...))` sažetak.
  - [x] Verifikuj ručno da drugo pokretanje ne pravi duplikate (test to formalizuje u Task 8).

- [ ] **Task 8: Testovi (TEA RED phase — Dev NE piše testove) (AC9)**
  - [ ] `apps/core/tests/test_seed_sample_data.py` sa `@pytest.mark.django_db`:
    - run-no-error na svežoj bazi;
    - count assertions (3 traktor brenda, ≥3 objavljena traktor proizvoda sa `horse_power` set, 5 polovnih, ≥3 objavljene objave, `traktori` Category postoji, SiteSettings postoji);
    - egzaktni deterministički slug-ovi postoje (`agri-tracking-tb804` itd.);
    - filter determinizam (`year__gte=2024` → tačno 2 NOVA traktora; `horse_power__lt=60, condition="new"` → tačno `wuzheng-wz504`; nijedna polovna mašina nema `year >= 2024`);
    - idempotentnost (2× call_command → identičan count **I** `Product.objects.get(slug="agri-tracking-tb804").is_published is True` posle 2. pokretanja — hvata delete-and-recreate-different-PK);
    - modeltranslation (`_sr` truthy + dijakritika prisutna);
    - production guard (`override_settings(DEBUG=False)` bez `--force` → `CommandError`; sa `--force` → prolazi).
  - [ ] HOST CAVEAT: native Windows pytest collection pada na libmagic (dokumentovan baseline, NIJE regresija) → testovi se pokreću kroz Docker (Postgres) ili import-light; TEA/Dev bira put.

## SM Decisions

- **SM-D1 (APPROACH, autoritativno):** Idempotentan Django management command
  `apps/core/management/commands/seed_sample_data.py`, **NE** `loaddata` JSON fixture. Rationale:
  (a) svaki postojeći seed u repo-u (`apps/brands/migrations/0003`, `0004`) je idempotentna
  get_or_create data-migracija — JSON fixture sa hardkodovanim PK-ovima bi se sudario; (b) modeli
  koriste django-modeltranslation (`_sr/_hu/_en`) + cross-app FK-ove (Brand→Product,
  Subcategory→Product) što čini JSON fixture krhkim i ne-idempotentnim; (c) command se može
  bezbedno ponovo pokretati (get_or_create) i može tvrdo zaštititi protiv produkcije. Command
  RECONCILE-uje epics.md 9.7 nameru (realan demo content, ne Lorem) kroz bolji Django-idiomatičan
  mehanizam. Reconciliacija dokumentovana eksplicitno.

- **SM-D2 (PRODUCTION SAFETY, autoritativno, MANDATORY):** Command MORA odbiti izvršavanje u
  produkciji. Guard: ako je `settings.DEBUG is False` I `--force` NIJE prosleđen → 
  `raise CommandError("seed_sample_data je DEV-only; odbijam izvršavanje sa DEBUG=False bez --force")`.
  NIKAD auto-run u migracijama ili entrypoint-u. Tvrd go-live gate (prod seed leak = data pollution).

- **SM-D3 (IDEMPOTENCY, autoritativno):** Svaki objekat kroz `get_or_create` po prirodnom unique
  ključu (slug za Brand/Category/Subcategory/Product/blog Post/blog Category/blog Tag; `pk=1` za
  SiteSettings). Dvostruko pokretanje NE pravi duplikate i NE baca grešku. Test tvrdi identičan
  count posle drugog pokretanja.

- **SM-D4 (MODELTRANSLATION, autoritativno):** Za svako translatable polje popuni `_sr` kolonu I
  bazni accessor (bazni accessor čita default-locale `_sr` kolonu). Prati tačno pattern iz
  `apps/brands/migrations/0004` (postavlja i `name` i `name_sr`). hu/en MOGU ostati prazni u v1.
  Sav srpski UI tekst = pune dijakritike (č/ć/ž/š/đ). Slug-ovi = ASCII transliteracija.

- **SM-D5 (NO COLLISION, autoritativno):** Ovi slug-ovi VEĆ POSTOJE iz migracija `0003`/`0004` —
  command je ADITIVAN i sme da ih referencira kroz get_or_create (bez dupliranja/kolizije):
  Brendovi `jeegee`/`hzm`/`tulip`; Kategorije (globally unique)
  `osnovna-obrada-zemljista`/`priprema-zemljista`/`masine-za-setvu`/`radne-masine`
  (sve `is_for="mehanizacija"`); Podkategorije pod `radne-masine`
  `mini-utovarivaci`/`utovarivaci-bez-teleskopa`/`teleskopski-utovarivaci`/`telehendleri`;
  Proizvodi `tulip-mix-6m3`/`tulip-mix-8m3`. **GAP:** NEMA seed-ovane TRAKTORI kategorije ni
  traktor proizvoda — ovu stranu DODAJE 9-7.

- **SM-D6 (DESIGN ZA 9-8 TRI USER JOURNEY-A, autoritativno — ključni deliverable):**
  - UJ-1 (Marko: catalog browse + FILTER traktore po snazi/godini/ceni → otvori model → upit):
    bar 1 TRAKTORI `Category` + 3 nova traktor brenda + više objavljenih traktor proizvoda sa
    `horse_power`/`year`/`price_eur`/`condition="new"` da filter vraća determinističke rezultate +
    5 polovnih (`condition="used"`).
  - UJ-2 (Stojan: lead form submit — servis/rezervni delovi): forme već postoje
    (`forms:contact_submit`/`model_inquiry_submit`/`service_request_submit`/`part_request_submit`).
    Model-inquiry forma re-validira `product_slug` protiv `Product.objects.filter(is_published=True,
    slug=...)` → mora postojati objavljen traktor sa poznatim slug-om (`agri-tracking-tb804`).
    NEMA Lead seed-ovanja (lead-ovi su user-generated).
  - UJ-3 (Marijana: admin product create + publish): admin mora biti dostupan; editor/superadmin
    user je potreban ALI — vidi SM-D7 — NE seed-uj password. 9-8 pravi svog dev-only test usera.

- **SM-D7 (NO SEEDED CREDENTIALS, autoritativno, CRITICAL):** NE seed-uj realne password-e, NE
  hardkoduj kredencijale. Default User model je `django.contrib.auth.models.User`
  (`AUTH_USER_MODEL` default; `apps/accounts` NEMA custom usera). Koristi `get_user_model()`,
  NIKAD direktan import. Dokumentovano (i u command docstring/`--help`) da 9-8 MORA da napravi
  svog DEV-only test usera (npr. `createsuperuser` u CI setup-u ili jasno označen env-driven dev
  user). Command SME opciono napraviti NON-LOGIN-CAPABLE marker, ali NE SME postaviti upotrebljiv
  password. Preporuka v1: command NE pravi usera uopšte (manje blast-radius); 9-8 ga pravi sam.

- **SM-D8 (BLOG + SITESETTINGS + GDPR):** Seed-uj 3-5 objavljenih `blog.Post` sa `blog.Category`
  + `blog.Tag` (`status="published"`, `published_at=timezone.now()`, `title_sr`/`perex_sr`/`body_sr`,
  ASCII slug-ovi) da blog index/footer renderuju realan content za E2E. Osiguraj `SiteSettings`
  singleton (`SiteSettings.load()`/`get_or_create(pk=1)` defanzivno — auto-seed-ovan
  `apps/pages/0002`, NE dupliraj). `CookiePolicy` + privacy `Page` su već seed-ovani
  (`gdpr/0002`, `pages/0004`) — referenciraj, ne dupliraj.

- **SM-D9 (IMAGES DEFERRED):** Image polja (`main_image` itd.) su `blank/null` i OSTAJU prazna u v1
  (template-ovi već handle-uju nedostajuće slike placeholder-ima). NE fabrikuj binarne slike. Realna
  sample imagery je odložen go-live OQ (biznis daje assete). Drži seed import-light, bez MIME/upload
  coupling-a.

- **SM-D10 (TESTING):** Testovi u `apps/core/tests/test_seed_sample_data.py`, `pytest-django` +
  `@pytest.mark.django_db`, kroz `call_command("seed_sample_data")`. Pokrivenost: run-no-error,
  count-ovi, egzaktni slug-ovi, idempotentnost (2× call), modeltranslation `_sr`+dijakritika,
  production guard (override_settings DEBUG=False). HOST CAVEAT: native Windows pytest pada na
  libmagic (dokumentovan baseline, NIJE regresija) → Docker (Postgres) ili import-light.

- **SM-D11 (SLUG MANIFEST, MANDATORY):** Story MORA sadržati sekciju
  „## Seed Identifiers za 9-8 E2E" sa egzaktnim determinističkim identifikatorima (slug-ovi,
  brojevi, URL imena/putanje, kako 9-8 dobija admin usera). Slug-ovi su finalni i ASCII.

## Dev Notes

### Model field fakti (za korektne get_or_create pozive)

- **`brands.Brand`** (`apps/brands/models.py:61`): `name`, `slug`(unique), `description`, `slogan`,
  `statistics`(JSON lista, max 4 dict-a), `brand_color`(`#RRGGBB` ili blank), `is_coming_soon`(bool).
  Translatable: `name`/`description`/`slogan`. `save()` auto-slug + `full_clean()`.
- **`brands.Category`** (`:241`): `name`, `slug`(globally unique), `description`,
  `is_for`(`"traktori"`/`"mehanizacija"`), `display_order`, `icon`. Translatable: `name`/`description`.
  `get_absolute_url` rutira po `is_for` → `brands:category_traktori` / `brands:category_mehanizacija`.
- **`brands.Subcategory`** (`:311`): `category` FK, `parent` self-FK nullable, `name`, `slug`,
  `description`, `icon`, `display_order`. `UniqueConstraint(category, parent, slug)`. Depth max 3.
- **`products.Product`** (`apps/products/models.py:80`): `brand` FK PROTECT (obavezan), `series` FK
  nullable, `subcategory` FK nullable PROTECT, `name`, `slug`(unique), `description`,
  `key_features`(JSON lista, **MAX 3 stavke** — `clean()` baca preko), `main_image`(blank ok),
  `year`(PositiveSmallInt), `price_eur`(Decimal max_digits=10/decimal_places=2),
  `horse_power`(PositiveSmallInt), `condition`(`"new"`/`"used"`),
  `status`(`"draft"`/`"published"`/`"archived"`), `is_published`(bool). **Za objavljene: postavi I
  `is_published=True` I `status="published"` (PR-D4 paralelna polja).** Translatable:
  `name`/`description`/`key_features`. `save()` auto-slug + `full_clean()`.
- **`products.ProductSpecification`** (`:376`): `product` FK, `section`
  (`"motor"`/`"transmisija"`/`"hidraulika"`/`"ostalo"`), `key`, `value`, `order`. Translatable:
  `key`/`value`.
- **`blog.Category`** (`apps/blog/models.py:42`): `name`, `slug`, `description` (translatable
  `name`/`description`). **`blog.Tag`** (`:80`): `name`, `slug` (translatable `name`). **`blog.Post`**
  (`:110`): `title`, `slug`, `perex`, `body`, `main_image`(blank ok), `category` FK SET_NULL, `tags`
  M2M, `author` FK SET_NULL nullable (**ostavi null** da se izbegne seed-ovanje usera),
  `status`(`"draft"`/`"published"`), `published_at`(timezone-aware). Translatable: `title`/`perex`/`body`.
- **`pages.SiteSettings`** (`apps/pages/models.py:29`): singleton `pk=1`
  (`SiteSettings.load()` / `get_or_create(pk=1)`). Već auto-seed-ovan migracijom — referenciraj
  defanzivno.

### Gotchas

- **G-1 (key_features MAX 3):** `Product.clean()` iterira `settings.LANGUAGES` i baca
  `ValidationError` ako `key_features` ima > 3 stavke (i u `_sr` varijanti). NE seed-uj 4+ stavke.
- **G-2 (save() poziva full_clean()):** Sva 3 sloga (Brand/Category/Product/blog) overrid-uju
  `save()` koji poziva `full_clean()` → seed-ovani podaci MORAJU proći validaciju (hex `brand_color`,
  statistics shape, key_features). get_or_create poziva `save()` na novom objektu pa validacija radi.
- **G-3 (M2M posle save):** `Post.tags.add(tag)` MORA biti posle `post.save()` (M2M zahteva PK).
- **G-4 (modeltranslation bazni accessor = `_sr`):** postavi OBA (`name` i `name_sr`) kao u 0004 —
  bazni accessor čita default-locale (`_sr`) kolonu; postavljanje samo `name` bez `name_sr` može
  ostaviti `_sr` praznim u zavisnosti od redosleda.
- **G-5 (Subcategory PROTECT na Product):** `Product.subcategory` je PROTECT; traktor proizvodi
  `subcategory=None` (top-tier, PR-D3) → nema potrebe za podkategorijom.
- **G-6 (get_or_create defaults):** `defaults` se primenjuju SAMO pri kreiranju; postojeći seed-ovi
  ostaju netaknuti pri drugom pokretanju (idempotentnost).
- **G-7 (NIKAD direktan User import):** koristi `get_user_model()` ako command ikad dodirne User
  (preporuka v1: ne dodiruje — vidi SM-D7).
- **G-8 (timezone):** `published_at=timezone.now()` (`django.utils.timezone`), NIKAD `datetime.now()`.
- **G-9 (management __init__):** `apps/core/management/__init__.py` i
  `apps/core/management/commands/__init__.py` MORAJU postojati ili Django ne otkriva command.

### Idempotency — slug je UVEK eksplicitan lookup ključ (HIGH — correctness)

Za SVAKI `get_or_create` poziv, `slug` (ili `pk=1` za `SiteSettings`) MORA biti EKSPLICITAN lookup
keyword argument; SVA ostala polja (uključujući `name`/`name_sr`/`title`/`title_sr`) idu u
`defaults={...}`. **`slug` se NIKAD ne izvodi auto-derivacijom u seed-u.** Razlog: `Brand`/`Category`/
`Product`/`Post` `.save()` auto-derivuje `slug` iz `name`/`title` kada je `slug` prazan — ako dev
izostavi `slug` lookup ključ i osloni se na auto-slug unutar `defaults`, drugo pokretanje NE može da
match-uje postojeći red i baca `unique IntegrityError` (ruši idempotentnost). Uvek prosledi `slug`
eksplicitno kao lookup ključ.

### Modeltranslation canonical get_or_create shape (MED — zero ambiguity)

Kanonski oblik (mirror `apps/brands/migrations/0004_seed_hzm_tulip_brands.py`): I bazni accessor I
`_sr` idu u ISTI `defaults` dict JEDNOG `get_or_create` poziva (`slug` ostaje lookup ključ izvan
`defaults`):

```python
Brand.objects.get_or_create(
    slug="wuzheng",
    defaults={"name": "Wuzheng", "name_sr": "Wuzheng", "description": "", "description_sr": "", ...},
)
```

`name` i `name_sr` (i `title`/`title_sr`, `perex`/`perex_sr`, `body`/`body_sr`, `key_features`/
`key_features_sr`) UVEK zajedno u `defaults` istog poziva — nikakva dvosmislenost da bazni i `_sr`
idu na različita mesta.

### Atomicity — transaction.atomic() (MED)

`handle()` TREBA da obavije seeding u `django.db.transaction.atomic()` (all-or-nothing) tako da
`full_clean()` greška usred seed-a NE ostavi polu-seed-ovanu bazu sa zavaravajućim stdout sažetkom.
(`get_or_create` i dalje čini re-run bezbednim — ali `atomic` sprečava nekonzistentno međustanje.)
Akumuliraj created/existing brojeve unutar atomic bloka, a SUCCESS sažetak ispiši TEK posle uspešnog
commit-a.

### Filter determinizam — polovne mašine namerno year ≤ 2022 (HIGH — UJ-1)

Ako 9-8 UJ-1 catalog filter spanuje SVE published proizvode (new + used), polovne mašine su namerno
`year <= 2022` da NEW-traktor filter bucket-i ostanu deterministički. Predloženi deterministički
filter za 9-8: `year >= 2024` → `{agri-tracking-tb804 (2024), saillong-sl904 (2025)}` (tačno 2
NOVA); `condition="new"` → 3 nova traktora. Ako 9-8 koristi `condition`-scoped filter, još
jednostavnije. `horse_power < 60` assertion MORA scope-ovati na `condition="new"` da bi vratio tačno
`wuzheng-wz504` (polovne mašine na 35/45/55 KS su < 60 ali su `used`).

#### Polovne mašine — finalne vrednosti (`condition="used"`, `is_published=True`, `status="published"`)

| slug | brend | horse_power (KS) | year | price_eur (€) |
|---|---|---|---|---|
| `polovni-traktor-agri-tracking-tb804` | agri-tracking | 75 | 2022 | 18500.00 |
| `polovni-tulip-mix-6m3` | tulip | 35 | 2018 | 4200.00 |
| `polovni-hzm-utovarivac` | hzm | 65 | 2020 | 15900.00 |
| `polovni-wuzheng-wz504` | wuzheng | 45 | 2019 | 9800.00 |
| `polovni-saillong-sl904` | saillong | 55 | 2021 | 13400.00 |

Sve `year <= 2022` (van `year >= 2024` bucket-a); `horse_power` (35/45/55/65/75) ne razbija
`condition="new"`-scoped `< 60` assertion. (`polovni-tulip-mix-6m3` referencira postojeći `tulip`
brend kroz get_or_create — ne pravi nov brend.)

### key_features dijakritika (LOW — user-facing tekst)

`key_features` stringovi su USER-FACING i MORAJU koristiti pune dijakritike (č/ć/ž/š/đ) — NIKAD šišana
latinica. NE kopiraj postojeći `0004` „Pocinkovano" presedan ako bi to ispustilo dijakritiku; koristi
„Pocinkovano kućište" samo gde je tačno (ova fraza nema dijakritiku u prve dve reči — to je korektno),
a inače preferiraj potpuno dijakritičan srpski (npr. „Robusna konstrukcija", „Hidraulična dizalica",
„Klimatizovana kabina").

### Project Structure Notes

- Novi fajlovi: `apps/core/management/__init__.py`, `apps/core/management/commands/__init__.py`,
  `apps/core/management/commands/seed_sample_data.py`, `apps/core/tests/test_seed_sample_data.py`.
- 0 migracija, 0 novih dependency-ja (NE factory_boy), 0 modifikacija postojećih migracija.
- `apps/core` ne sme importovati domain apps PO PRAVILU — ALI ovaj command je
  **operativni/management sloj** (ne model/runtime kod core-a) i mora importovati domain modele da
  seed-uje. Ovo je svesna granica: dokumentuj u command docstring-u da je import dozvoljen jer je ovo
  data-bootstrap utility (mirror data-migration seed-ova koji žive u `apps/brands/migrations`),
  ne runtime core kod. (Alternativa razmotrena: smestiti command u domain app — ali seed je
  cross-app pa `apps/core` je najneutralniji dom. SM-D1.)

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 9.7] — original loaddata namera (reconcil. SM-D1)
- [Source: _bmad-output/planning-artifacts/epics.md#Story 9.8] — konzument seed-a (UJ-1/2/3)
- [Source: apps/brands/migrations/0004_seed_hzm_tulip_brands.py] — get_or_create + `_sr` pattern (SM-D4)
- [Source: apps/products/models.py] — Product field fakti + key_features MAX 3 clean()
- [Source: apps/blog/models.py] — Post/Category/Tag field fakti + PublishedManager
- [Source: apps/pages/models.py] — SiteSettings singleton load()
- [Source: _bmad-output/project-context.md] — modeltranslation _sr, ASCII slug, dijakritika, timezone, get_user_model

## Seed Identifiers za 9-8 E2E

> **Ovo je ugovor koji Siniša predaje 9-8. Svi slug-ovi su FINALNI i ASCII.**

### TRAKTORI taksonomija
- **TRAKTORI Category slug:** `traktori` (`is_for="traktori"`, `name="Traktori"`).
- **Traktor brend slug-ovi:** `wuzheng`, `agri-tracking`, `saillong`.

### Objavljeni traktor proizvodi (`condition="new"`, `is_published=True`, `status="published"`)
| slug | brend | horse_power (KS) | year | price_eur (€) |
|---|---|---|---|---|
| `agri-tracking-tb804` (HEADLINE — UJ-1 + UJ-2) | agri-tracking | 80 | 2024 | 28500.00 |
| `wuzheng-wz504` | wuzheng | 50 | 2023 | 19900.00 |
| `saillong-sl904` | saillong | 90 | 2025 | 32400.00 |

> Filter determinizam za 9-8: `horse_power < 60` → samo `wuzheng-wz504`;
> `year >= 2024` → `agri-tracking-tb804` + `saillong-sl904`;
> `price_eur <= 20000` → samo `wuzheng-wz504`.

### Polovne mašine (`condition="used"`, `is_published=True`) — 5 ukupno
- Determinstički headline polovni slug: **`polovni-traktor-agri-tracking-tb804`** (agri-tracking brend).
- Ostala 4 polovna: `polovni-tulip-mix-6m3`, `polovni-hzm-utovarivac`, `polovni-wuzheng-wz504`,
  `polovni-saillong-sl904` (svi `condition="used"`, `is_published=True`, `year`/`price_eur` popunjeni).
- Finalne `horse_power`/`year`/`price_eur` vrednosti: vidi Dev Note tabelu „Polovne mašine — finalne
  vrednosti". Sve `year <= 2022` (NIKAD `>= 2024`); `horse_power` ∈ {35,45,55,65,75}.

> **UJ-1 filter determinizam:** ako 9-8 filtrira preko svih published proizvoda (new+used), polovne
> mašine su namerno `year <= 2022`; predloženi deterministički filter za 9-8: `year >= 2024` →
> `{agri-tracking-tb804, saillong-sl904}` (tačno 2 NOVA); `condition="new"` → 3 nova traktora. Ako 9-8
> koristi `condition`-scoped filter, još jednostavnije. `horse_power < 60` assertion MORA scope-ovati
> na `condition="new"` (polovne na 35/45/55 KS su < 60 ali `used`).

### Blog
- **Blog Category slug:** `ratarstvo`.
- **Blog Tag slug:** `zetva`.
- **Headline objavljen Post slug:** `pet-saveta-za-prolecnu-setvu` (+ 2-4 dodatna objavljena posta).

### Form URL imena (UJ-2 — već postoje, NE menjaju se; putanje verifikovane protiv `apps/forms/urls.py`)
- `forms:contact_submit` → `POST /sr/htmx/forme/kontakt/`
- `forms:model_inquiry_submit` → `POST /sr/htmx/forme/upit-za-model/` (re-validira `product_slug`
  protiv objavljenog Product-a; koristi `agri-tracking-tb804`)
- `forms:service_request_submit` → `POST /sr/htmx/forme/servis/`
- `forms:part_request_submit` → `POST /sr/htmx/forme/rezervni-delovi/`

### Javne URL putanje (UJ-1)
- Product detail: `/sr/proizvod/<slug>/` (`products:detail`) → npr. `/sr/proizvod/agri-tracking-tb804/`
- Brand detail: `/sr/traktori/<brand-slug>/` (`brands:detail`) → npr. `/sr/traktori/agri-tracking/`
- Blog detail: `/sr/blog/<slug>/` (`blog:detail`); blog kategorija `/sr/blog/kategorija/ratarstvo/`
  (`blog:category`); blog tag `/sr/blog/tag/zetva/` (`blog:tag`)

### Kako 9-8 dobija admin usera (UJ-3) — NE seed-ovan password
9-8 MORA da provisionuje svog SOPSTVENOG DEV-only superusera; `seed_sample_data` ga NE pravi
(SM-D7 zabranjuje seed-ovan password). Konkretno: u CI/E2E setup-u pokreni
`python manage.py createsuperuser --noinput` sa env-driven kredencijalima (`DJANGO_SUPERUSER_USERNAME`/
`DJANGO_SUPERUSER_PASSWORD`/`DJANGO_SUPERUSER_EMAIL`) ili jasno označen env-driven dev user fixture.
`seed_sample_data` NE postavlja upotrebljiv password (SM-D7).
**Admin login putanja je `/admin-coric/` (NE `/admin/`)** — Story 8-1 premestila admin van i18n
prefiksa; 9-8 UJ-3 mora ciljati `/admin-coric/`.

## Open Questions (go-live gates)

- **OQ-1 (real imagery — go-live deferral):** sample slike (`main_image`, blog `main_image`) ostaju
  prazne u v1 (placeholder render). Realna sample imagery je odložen go-live OQ — biznis (Mihas)
  obezbeđuje assete pre go-live. Da li je placeholder render prihvatljiv za 9-8 E2E? (Pretpostavka:
  da, template-ovi handle-uju missing image.)
- **OQ-2 (hu/en prevodi — deferred):** hu/en translatable kolone ostaju prazne u v1 (mirror
  postojećih seed-ova). 9-8 per-locale E2E (hu/en sample) može tražiti bar 1 preveden objekat —
  potvrditi sa 9-8 da li je sr-only seed dovoljan ili treba bar 1 hu/en uzorak.
- **OQ-3 (egzaktni filter test thresholds):** brojevi u manifestu (80/50/90 KS, 2023/24/25,
  €19.900/28.500/32.400) su finalni za determinizam — ali 9-8 filter UI granice (slider min/max
  korak) mogu zahtevati fino podešavanje thresholds-a. Potvrditi sa 9-8 da seed pokriva sve filter
  bucket-e (npr. treba li traktor < 50 KS ili > 90 KS za boundary test).
- **OQ-4 (admin user provisioning mehanizam):** preporuka je `createsuperuser --noinput` env-driven
  (SM-D7) — potvrditi da CI/E2E pipeline iz 9-8 to podržava (ili treba li `seed_sample_data` opciono
  da napravi NON-LOGIN marker usera bez password-a).

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
