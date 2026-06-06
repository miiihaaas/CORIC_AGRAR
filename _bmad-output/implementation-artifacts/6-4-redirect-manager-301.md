---
story_id: "6.4"
story-key: 6-4-redirect-manager-301
title: Redirect Manager (301)
status: ready-for-dev
epic: 6
epic_num: 6
epic_title: SEO & Discoverability
module: seo
created: 2026-06-06
last_modified: 2026-06-06
complexity: M
author: Mihas (SM autonomous; ČETVRTA story Epic 6 — SEO & Discoverability. NOVI deliverable u apps.seo: admin-upravljani 301 redirect sistem. **DVA artefakta:** (1) NOVI `apps/seo/models.py:Redirect` (old_path/new_path/is_active + created_at-iz-TimestampedModel) sa admin CRUD; (2) NOVI `apps/seo/middleware.py:RedirectMiddleware` registrovan PRE `LocaleMiddleware` u MIDDLEWARE listi. **GLAVNA odluka (SM-D1) — MIDDLEWARE ORDER + RAW PATH MATCH:** RedirectMiddleware mora trčati PRE LocaleMiddleware (verifikovano base.py:61) tako da matchuje SIROVI dolazni `request.path` (UKLJUČUJUĆI locale prefiks `/sr/`, `/hu/`, `/en/`) — pa admin upisuje old_path TAČNO kako bot/korisnik kuca URL (sa prefiksom). **SECURITY (SM-D2) — OPEN-REDIRECT GUARD (MANDATORY na sve write puteve):** `new_path` se VALIDIRA u `Redirect.clean()` kroz Django built-in `url_has_allowed_host_and_scheme(url=new_path, allowed_hosts=None)` (odbija scheme-relative `//`, apsolutni `http(s)://`, backslash `/\`, encoded bypass — NE ručni startswith) + `old_path == new_path` self-loop guard; `Redirect.save()` override zove `self.full_clean()` → guard radi i na programski `.create()`/`.save()`/shell/migracije (NE samo admin form; bulk_create izuzetak prihvaćen) → sprečava open-redirect attack (301 na zlonameran eksterni sajt) i beskonačni 301 loop. **PERF (SM-D4) — QUERY-BUDGET na SVAKI request:** middleware trči na SVAKOM zahtevu → lookup mora biti jeftin (db_index na old_path + `is_active=True` filter + exact match `.filter(old_path=path, is_active=True).first()` — JEDAN indeksiran upit; NE učitava sve rule-ove u memoriju). **EXCLUSION (SM-D3):** middleware preskače admin (forward-safe segment-match derivirano iz konfigurisanog admin base-a — pokriva tekući `/sr/admin/` I budući Epic 8 `/sr/admin-coric/`; NE krhki `'/admin/' in path` substring) + statiku/mediju (`/static/`, `/media/`) — NE pravi DB lookup za te puteve. **301 PERMANENT (SM-D5):** isključivo `HttpResponsePermanentRedirect` (301); redirect-tip NIJE konfigurabilan u v1 (YAGNI; epics traži 301). **NORMALIZACIJA (SM-D6):** old_path/new_path su ASCII URL putevi (NE translatable — modeltranslation se NE primenjuje); old_path je `unique=True` (jedan rule po starom putu). **SCHEMA-CHANGING migracija** — `CreateModel Redirect` → JEDNA migracija (apps/seo/migrations/0002). 1 NOVI model + 1 NOVI middleware + admin registracija + MIDDLEWARE edit + translation.py NETAKNUT (Redirect NIJE translatable) + 1 migracija. RISK TIER: HIGH — (a) MIDDLEWARE na svaki request = global blast-radius (greška lomi CEO sajt); (b) MIDDLEWARE ORDER security/correctness-kritičan (PRE LocaleMiddleware — pogrešan red lomi raw-path match); (c) OPEN-REDIRECT je HIGH-severity security surface (new_path validacija MORA biti tačna); (d) query-na-svaki-request perf (DB lookup za svaki path — mora biti indeksiran + admin/static skip); (e) CreateModel migracija (schema change).)
depends_on:
  - 6-1-seometa-model-per-page-admin                          # apps.seo app foundation: AppConfig (apps.seo), TimestampedModel base reuse pattern (SeoMeta(TimestampedModel)), admin.py registracije obrazac, modeltranslation translation.py pattern (Redirect ga NE koristi — ASCII path); per-app tests/ layout
  - 6-3-robots-txt-open-graph-twitter-card-meta              # apps/seo/views.py PRVI seo view (6.3) — 6.4 dodaje middleware.py (NE dira views.py); robots.txt Disallow */admin/ + */htmx/ obrazac (admin pod i18n /sr/admin/) — isti exclusion-prefix logika koju RedirectMiddleware skip primenjuje
  - 1-4-i18n-setup-sa-locale-url-routing-i-switcher          # i18n_patterns(prefix_default_language=True) → SVI app URL-ovi nose locale prefiks (/sr/...); LocaleMiddleware u MIDDLEWARE (base.py:61) → RedirectMiddleware ide PRE njega (SM-D1 raw-path match SA prefiksom)
---

# Story 6.4: Redirect Manager (301)

Status: ready-for-dev

## Opis

As a **admin (sadržajni urednik / SEO menadžer)**,

I want **da kreiram, izmenim i deaktiviram 301 redirect pravila (stari URL → novi URL) kroz admin UI**,

so that **mogu da preusmerim stare/promenjene URL-ove na nove bez gubitka SEO ranking-a i bez broken-link 404-a kad se slug ili struktura strane promeni**.

Ovo je **ČETVRTA story Epic 6 (SEO & Discoverability)** i ima DVA deliverable-a:

1. **`apps/seo/models.py:Redirect` model + admin CRUD** — NOVI model (`old_path`, `new_path`, `is_active`, `created_at` iz `TimestampedModel`) sa generičkim Django admin-om (list/add/edit/deactivate). Admin može da listuje sva pravila, doda novo, izmeni postojeće, i deaktivira (toggle `is_active`).
2. **`apps/seo/middleware.py:RedirectMiddleware`** — NOVI middleware registrovan u `MIDDLEWARE` PRE `LocaleMiddleware` (verifikovano `config/settings/base.py:61`). Na svakom zahtevu proverava da li `request.path` matchuje aktivno `Redirect.old_path` pravilo → ako da, vraća **HTTP 301** (`HttpResponsePermanentRedirect`) sa novim `Location` header-om (`new_path`). Preskače admin/static/media puteve (NE pravi DB lookup za njih).

> **GLAVNA odluka (SM-D1) — MIDDLEWARE ORDER + RAW-PATH MATCH (mirror epics:962 „registrujem middleware ranije od LocaleMiddleware").** `RedirectMiddleware` se ubacuje u `MIDDLEWARE` listu **PRE `django.middleware.locale.LocaleMiddleware`** (base.py:61). Razlog: LocaleMiddleware u `process_request` postavlja `request.LANGUAGE_CODE`/aktivira prevod, ali **NE menja/ne strip-uje `request.path`** — locale prefiks (`/sr/`, `/hu/`, `/en/`) je u `request.path` BEZ OBZIRA na red. STVARNI razlog za PRE-poziciju je da RedirectMiddleware short-circuit-uje (vrati 301) **PRE APPEND_SLASH (CommonMiddleware) i locale-redirect interakcija** (inače bi mogli praviti dvostruke redirect-e/loop — SEO4-1). RedirectMiddleware vidi **SIROVI `request.path` tačno kako ga je bot/korisnik zatražio — UKLJUČUJUĆI locale prefiks** (`/sr/stari-url/`). Zato admin upisuje `old_path` SA prefiksom (kako URL stvarno izgleda: `/sr/stara-strana/`). Ovo je jednostavno, eksplicitno i predvidljivo — exact-match na pun path (vidi SM-D7 za i18n-prefiks razmatranje). **Pozicija:** odmah POSLE `SessionMiddleware` (base.py:60), PRE `LocaleMiddleware` (base.py:61) — tj. insert na indeks 4 (između sessions i locale).

> **SECURITY odluka (SM-D2) — OPEN-REDIRECT GUARD (HIGH-severity surface; enforced na SVE write puteve).** `new_path` je admin-uneta vrednost koja postaje `Location` header u 301 odgovoru. Ako bi admin (ili kompromitovani nalog) uneo `new_path = "https://zlonamerni-sajt.com"`, `//evil.com` (scheme-relative), ili `/\evil.com` (backslash bypass koji browser tretira kao `//`), middleware bi izdao **301 na eksterni sajt** = open-redirect (phishing/SEO-poisoning vektor). **Odluka: `new_path` MORA biti INTERNI site-internal path** — validira se u `Redirect.clean()` koristeći **Django built-in `django.utils.http.url_has_allowed_host_and_scheme(url=self.new_path, allowed_hosts=None)`** (kanonska Django provera koja odbija scheme-relative `//`, apsolutni eksterni URL, **backslash `/\` varijantu**, i encoded bypass-eve — ručno sklepan `startswith('//')`/`'://'` check NE pokriva backslash i encoded slučajeve, zato se NE koristi). Dodatno, `clean()` odbija `old_path == new_path` (self-loop → beskonačni 301 na site-wide middleware-u — correctness blocker). **Enforcement NIJE opcioni:** osim `clean()`-a (koji admin ModelForm zove kroz `full_clean`), `Redirect.save()` je **MANDATORY override** koji zove `self.full_clean()` PRE čuvanja → guard se primenjuje i na ne-admin write puteve (`.objects.create()`, shell, management komande, fixtures, data migracije, testovi). **Poznato i prihvaćeno ograničenje:** `Model.bulk_create()` zaobilazi `save()` (Django ne zove save() po objektu) — prihvatljivo jer redirect tabela realno nikad ne treba bulk_create (admin-jedan-po-jedan, ~desetine rule-ova; OUT OF SCOPE bulk import). Middleware trust-uje validirani `new_path` (NE re-validira na svaki request — perf; validacija je na write-time, ne read-time).

## IN SCOPE (šta ova story isporučuje)

1. **NOVI `apps/seo/models.py:Redirect(TimestampedModel)`** (AC1) — polja:
   - `old_path = models.CharField(max_length=255, unique=True, db_index=True)` — stari put koji se matchuje protiv `request.path` (SA locale prefiksom; SM-D1). `unique=True` → jedan rule po starom putu (SM-D6).
   - `new_path = models.CharField(max_length=255)` — odredišni interni put (`Location` header). Validiran u `clean()` (SM-D2).
   - `is_active = models.BooleanField(default=True, db_index=True)` — toggle za deaktivaciju bez brisanja (admin deactivate; AC3).
   - `created_at` / `updated_at` — iz `TimestampedModel` (epics:961 traži `created_at`; TimestampedModel pruža oba; reuse 6-1 SeoMeta obrazac).
   - `clean()` — open-redirect guard za `new_path` (MANDATORY, koristi `django.utils.http.url_has_allowed_host_and_scheme` — SM-D2) + `old_path == new_path` self-loop guard (SM-D2) + (opciono) normalizacija trailing slash-a (SM-D6).
   - `save()` — **MANDATORY override** koji zove `self.full_clean()` PRE `super().save()` → open-redirect guard se primenjuje na SVE write puteve (`.save()`/`.objects.create()`/shell/migracije/fixtures), NE samo admin form (SM-D2).
   - `Meta`: `verbose_name`/`verbose_name_plural` (srpski, dijakritike), `ordering = ["old_path"]`.
   - `__str__` → `f"{self.old_path} → {self.new_path}"`.
2. **NOVI `apps/seo/migrations/0002_redirect.py`** (AC1) — `CreateModel Redirect`. Schema-changing. Manual review PRE commit (project-context migrations discipline).
3. **NOVI `apps/seo/middleware.py:RedirectMiddleware`** (AC2, SM-D1/D3/D4/D5) — standardni Django middleware (callable klasa sa `__init__(self, get_response)` + `__call__(self, request)`). Logika u `process_request` fazi (PRE view):
   - **EXCLUSION skip (SM-D3):** ako `request.path` počinje sa nekim od skip-prefiksa (`/static/`, `/media/`) ILI je admin path (segment-aware, derivirano iz konfigurisanog admin base-a — NE magic substring `'/admin/' in path`) → NE radi DB lookup, prosledi `get_response(request)`. (Admin skip je AC2 zahtev — middleware NE procesira admin URL-ove.)
   - **Lookup (SM-D4):** `redirect = Redirect.objects.filter(old_path=request.path, is_active=True).first()` — JEDAN indeksiran upit (db_index na old_path + is_active filter). Ako `None` → prosledi dalje (no-match passthrough).
   - **301 (SM-D5):** ako match → `return HttpResponsePermanentRedirect(redirect.new_path)` (status 301, `Location: new_path`).
4. **`config/settings/base.py` EDIT: registruj RedirectMiddleware PRE LocaleMiddleware** (AC2, SM-D1) — dodaj `"apps.seo.middleware.RedirectMiddleware"` u `MIDDLEWARE` listu IZMEĐU `SessionMiddleware` (`:60`) i `LocaleMiddleware` (`:61`).
5. **`apps/seo/admin.py` EDIT: registruj `RedirectAdmin`** (AC3) — `@admin.register(Redirect)` sa:
   - `list_display = ("old_path", "new_path", "is_active", "created_at")`.
   - `list_filter = ("is_active",)`.
   - `search_fields = ("old_path", "new_path")`.
   - `list_editable = ("is_active",)` (toggle deaktivacije direktno iz liste) ILI admin action `make_inactive`/`make_active` (Dev bira; oba zadovoljavaju „deaktivira" AC3).
   - (Redirect je SAMOSTALAN ModelAdmin — NIJE inline, NE koristi SeoMetaInline; NE koristi SeoWarningAdminMixin.)
6. **Test surface (TEA RED)** (AC4) — enumerisan u Testing sekciji (301 status + Location, admin-skip, is_active=False skip, open-redirect odbijanje, middleware-order, i18n-prefiks match, no-match passthrough, static/media skip, migracija sanity).

## OUT OF SCOPE (eksplicitno — granice)

- **Regex / wildcard / prefix redirect pravila** = **NE** (YAGNI; v1 je EXACT-match na pun `old_path`). Ako biznis zatraži pattern-based redirect (npr. `/stari-blog/* → /blog/*`), to je 6.x enhancement (OQ-1). 6.4 je exact-string match.
- **302 (privremeni) redirect / konfigurabilan redirect-tip** = **NE** (SM-D5; epics:963 traži 301 PERMANENT; `is_permanent` boolean polje bi bio YAGNI v1 — DEFER OQ-2). Isključivo `HttpResponsePermanentRedirect`.
- **`django.contrib.redirects`** (Django built-in redirects app) = **NE** (SM-D8 — Django built-in vezuje za `django.contrib.sites`/SITE_ID koji projekat NE koristi (6-2 SM-D2 RequestSite/Host odluka); custom Redirect model je lakši i konzistentan sa apps.seo + bez sites dependency). Custom model + custom middleware.
- **Translatable old_path/new_path** = **NE** (SM-D6 — putevi su ASCII URL-ovi, jezik-neutralni; modeltranslation se NE primenjuje; `translation.py` NETAKNUT; Redirect NEMA _sr/_hu/_en kolone). Locale-specifični redirect se postiže zasebnim rule-om po locale prefiksu (`/sr/stari/` i `/hu/regi/` su 2 rule-a) — SM-D7.
- **Redirect na 404 (catch-missing) / automatsko logovanje hit-ova** = **NE** (v1 je manuelno admin-upravljano; hit-counter/last-accessed analytika je 6.x — OQ-3). Bez `hit_count` polja.
- **Middleware match na query string / fragment** = **NE** (match je SAMO na `request.path` — bez `request.GET`/query string; query string se NE poredi ni prenosi u v1; OQ-4). `Location` je čist `new_path`.
- **Promena admin slug-a `/admin-coric/`** = **NE** (project-context preporučuje `/admin-coric/` ali config/urls.py:42 trenutno registruje `admin/` pod i18n_patterns → stvarni admin path je `/sr/admin/`. Promena slug-a na `/admin-coric/` je Epic 8 (8-1 custom admin login) — NE 6.4. ALI: 6.4 skip MORA biti forward-safe — derivira admin base iz JEDNOG izvora istine (settings konstanta / `reverse('admin:index')` / segment-aware regex koji tolerise budući `admin-coric` slug), tako da Epic 8 slug-promena NE regresira admin-skip. SM-D3 dokumentuje robustan forward-safe skip; test zaključava i `admin/` i `admin-coric/`.)
- **Bulk import redirect-a (CSV)** = **NE** (admin-jedan-po-jedan v1; bulk je 6.x/8.x admin polish).

## Princip

DVA deliverable-a, oba minimalna i KONZISTENTNA sa apps.seo: (1) `Redirect` model = tanak `TimestampedModel` potomak sa 3 polja + `clean()` open-redirect guard + samostalan admin (list/add/edit/deactivate). (2) `RedirectMiddleware` = standardna Django callable-klasa middleware sa JEDNIM indeksiranim upitom po request-u (db_index old_path + is_active), exclusion-skip za admin/static/media (NE DB lookup za njih), i `HttpResponsePermanentRedirect` (301) na match. Middleware ide PRE LocaleMiddleware (raw-path match SA locale prefiksom — SM-D1). Open-redirect je validiran na write-time (`clean()`), trust-ovan na read-time (perf). 1 schema migracija (CreateModel). NEMA regex/wildcard (exact match — YAGNI). NEMA 302/konfigurabilan tip (301 only). NEMA translatable path (ASCII URL). NEMA django.contrib.redirects/sites coupling (custom, RequestSite-konzistentno). NEMA hit-logging/analytike (v1 manuelno).

## Strukturna arhitektura — repository delta

**3 NOVA fajla (`apps/seo/models.py` EXTEND je edit, ne nov; `apps/seo/middleware.py` NOV + migracija NOVA) + 2 EDIT (`config/settings/base.py` MIDDLEWARE + `apps/seo/admin.py`) + 1 MIGRACIJA (CreateModel Redirect) + translation.py NETAKNUT.**

| Path | Tip | Razlog |
|---|---|---|
| `apps/seo/models.py` | EDIT (ADD `Redirect`) | NOVI `Redirect(TimestampedModel)` model: `old_path`(unique,db_index) + `new_path` + `is_active`(default True, db_index) + `clean()` open-redirect guard (SM-D2) + Meta(ordering, verbose_name srpski) + `__str__`. SeoMeta OSTAJE netaknut (6.4 SAMO dodaje klasu). (AC1/SM-D2/D6) |
| `apps/seo/middleware.py` | NOVO | `RedirectMiddleware` callable klasa (`__init__(get_response)` + `__call__(request)`): exclusion-skip (admin/static/media — SM-D3) → `Redirect.objects.filter(old_path=request.path, is_active=True).first()` (1 indeksiran upit — SM-D4) → `HttpResponsePermanentRedirect(new_path)` na match (301 — SM-D5), inače `get_response(request)`. PRVI middleware u apps.seo. (AC2) |
| `apps/seo/migrations/0002_redirect.py` | NOVO | `CreateModel Redirect` (old_path CharField unique+db_index, new_path CharField, is_active BooleanField db_index, created_at/updated_at iz TimestampedModel). Manual review PRE commit. (AC1) |
| `config/settings/base.py` | EDIT | Dodaj `"apps.seo.middleware.RedirectMiddleware"` u `MIDDLEWARE` IZMEĐU `SessionMiddleware`(:60) i `LocaleMiddleware`(:61) — insert indeks 4. (AC2/SM-D1) |
| `apps/seo/admin.py` | EDIT | `@admin.register(Redirect)` `RedirectAdmin`: list_display(old_path,new_path,is_active,created_at) + list_filter(is_active) + search_fields(old_path,new_path) + list_editable(is_active) ILI make_active/make_inactive akcije (deaktivacija — AC3). Samostalan ModelAdmin (NE inline). (AC3) |
| `apps/seo/tests/*` | NOVO (TEA) | RED-phase testovi (vidi Testing): test_redirect_model.py + test_redirect_middleware.py + test_redirect_admin.py + test_redirect_migration.py + test_redirect_open_redirect.py. Dev NE piše testove. |
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | EDIT | `6-4-redirect-manager-301` → `ready-for-dev`. SM handoff tracking (NIJE deliverable). |

**NETAKNUTO (regression guards):** `apps/seo/translation.py` (Redirect NIJE translatable — ASCII path; SM-D6; modeltranslation NETAKNUT); `apps/seo/views.py` (6-3 robots_txt — 6.4 NE dira; 6.4 dodaje middleware.py, NE views.py); `apps/seo/sitemaps.py` (6-2 — netaknut); `apps/seo/templatetags/seo_meta.py` (6-1/6-3 — netaknut); SVE postojeće migracije (`0001_initial` — NE menjati; NOVA `0002` je CreateModel, NE altera SeoMeta); `apps/seo/models.py:SeoMeta` (OSTAJE — 6.4 SAMO dodaje Redirect klasu uz njega); ostatak `MIDDLEWARE` reda (insert NE menja relativni red ostalih — Security/Whitenoise/Session OSTAJU PRE, Common/Csrf/Auth/Messages/XFrame/Htmx/LocaleSwitcher OSTAJU POSLE); `config/urls.py` (Redirect je middleware-driven — NE zahteva URL registraciju); `pyproject.toml` (0 novih dep-ova — HttpResponsePermanentRedirect/ValidationError su Django core).

## Kriterijumi prihvatanja

**AC1 — `apps/seo/models.py:Redirect` model + migracija (old_path/new_path/is_active/created_at) (SM-D1/D2/D6)**

- **Given** apps.seo app (6-1) sa `TimestampedModel` base
- **When** kreiram `Redirect(TimestampedModel)` sa `old_path`(CharField, unique=True, db_index=True), `new_path`(CharField), `is_active`(BooleanField, default=True, db_index=True) + `makemigrations seo`
- **Then**:
  - Migracija `0002_redirect` kreira tabelu `seo_redirect` sa kolonama old_path/new_path/is_active/created_at/updated_at
  - `Redirect.objects.create(old_path="/sr/stari/", new_path="/sr/novi/")` radi; `is_active` default True
  - `old_path` je `unique` (drugi rule sa istim old_path → IntegrityError)
  - `__str__` vraća `"/sr/stari/ → /sr/novi/"`
- **And** `Redirect.save()` override zove `self.full_clean()` PRE `super().save()` → open-redirect/self-loop guard se aktivira na SVE write puteve (`.create()`/`.save()`), ne samo admin form (SM-D2/AC5)
- **And** `makemigrations --check --dry-run` posle commit-a → „No changes detected" (model i migracija usklađeni; `save()`/`clean()` override NE menjaju schemu)
- **And** Redirect NIJE registrovan u `translation.py` (NEMA _sr/_hu/_en kolone — ASCII path; SM-D6)

**AC2 — `RedirectMiddleware` vraća 301 sa novim Location, registrovan PRE LocaleMiddleware, preskače admin (SM-D1/D3/D5)**

- **Given** aktivno pravilo `Redirect(old_path="/sr/stara-strana/", new_path="/sr/nova-strana/", is_active=True)`
- **When** GET `/sr/stara-strana/`
- **Then**:
  - Odgovor je HTTP **301** (`HttpResponsePermanentRedirect`)
  - `Location` header == `/sr/nova-strana/` (== `new_path`)
- **And** `RedirectMiddleware` je u `MIDDLEWARE` PRE `django.middleware.locale.LocaleMiddleware` (indeks(RedirectMiddleware) < indeks(LocaleMiddleware))
- **And** **admin-skip semantika (eksplicitno — SM-D3):** middleware preskače sve puteve čiji je locale-prefiksovan path ispod admin base-a, gde se admin base DERIVIRA iz jednog izvora istine (settings/modul konstanta ILI `reverse('admin:index')` ILI segment-aware regex `^/[a-z]{2}/admin(-coric)?/`) — **NE** kroz krhki substring `'/admin/' in path` i **NE** kroz hardkodovan `/admin-coric/`-prefiks iz epics:964 (taj slug NIJE registrovan). Skip MORA pokriti i tekući `admin/` i planirani `admin-coric/` (Epic 8) slug.
- **And** GET na admin path (`/sr/admin/...`) sa pravilom koje bi matchovalo admin → middleware NE redirektuje (admin skip); admin odgovara normalno
- **And** GET na budući admin path (`/sr/admin-coric/...`) → TAKOĐE skip-ovan (forward-safe — Epic 8 slug-promena ne regresira skip)
- **And** GET path BEZ matchujućeg pravila → middleware NE redirektuje (no-match passthrough; status NIJE 301)

**AC3 — Admin može da listuje, doda, izmeni, deaktivira redirect pravila (AC3)**

- **Given** `RedirectAdmin` registrovan
- **When** superuser otvori admin
- **Then**:
  - Lista prikazuje sva pravila (`list_display` old_path/new_path/is_active/created_at)
  - Može da doda novo pravilo (add form)
  - Može da izmeni postojeće (change form)
  - Može da deaktivira pravilo (toggle `is_active=False` kroz `list_editable` ILI admin action) — deaktivirano pravilo NE redirektuje (AC4)
  - `search_fields` omogućava pretragu po old_path/new_path; `list_filter` po is_active

**AC4 — is_active=False pravilo se NE primenjuje (deaktivacija) (SM-D4)**

- **Given** pravilo `Redirect(old_path="/sr/x/", new_path="/sr/y/", is_active=False)`
- **When** GET `/sr/x/`
- **Then** middleware NE redirektuje (lookup filtrira `is_active=True` → no match); odgovor NIJE 301
- **And When** isto pravilo se aktivira (`is_active=True`)
- **Then** GET `/sr/x/` → 301 → `/sr/y/`

**AC5 — OPEN-REDIRECT guard: new_path mora biti interni site-internal path, enforced na SVE write puteve (SM-D2)**

- **Given** open-redirect security boundary
- **When** pokušam da sačuvam `Redirect(old_path="/sr/x/", new_path="https://evil.com")` (apsolutni URL) ILI `new_path="//evil.com"` (scheme-relative) ILI `new_path="/\evil.com"` (backslash bypass) — kroz `full_clean()` / admin form
- **Then** `Redirect.clean()` raise-uje `ValidationError` na `new_path` (provera kroz `django.utils.http.url_has_allowed_host_and_scheme(url=new_path, allowed_hosts=None)` → odbija scheme-relative `//`, apsolutni eksterni, backslash `/\`, i encoded varijante; new_path mora biti site-internal path)
- **And** validan `new_path="/sr/novi/"` (site-internal) PROLAZI `clean()`
- **And** `old_path == new_path` (npr. oba `"/sr/x/"`) raise-uje `ValidationError` (self-loop guard — beskonačni 301; SM-D2)
- **And** `old_path` koji NE počinje sa `/` (npr. `"sr/stara/"` — admin typo) raise-uje `ValidationError` na `old_path` (mora odgovarati `request.path` koji uvek počinje sa `/`; sprečava tiho-mrtvo pravilo koje nikad ne matchuje)
- **And** enforcement NIJE admin-only: `Redirect.save()` override zove `self.full_clean()`, pa **programski `Redirect.objects.create(old_path="/sr/x/", new_path="https://evil.com")` / `.save()` TAKOĐE raise-uje `ValidationError`** (guard radi van admin forme — shell/migracije/fixtures/testovi). (Poznato ograničenje: `bulk_create` zaobilazi `save()` — prihvaćeno, redirect tabela ne koristi bulk_create.)
- **And** zato što write-time guard pokriva sve `save()`/`create()` puteve, nevalidan `new_path` ne može biti perzistiran → middleware u praksi nikad ne izda 301 na eksterni domen (osim ako se svesno zaobiđe `save()` kroz `bulk_create`/raw SQL — van scope-a)

**AC6 — i18n locale-prefiks: middleware matchuje SIROVI request.path (sa prefiksom) PRE LocaleMiddleware (SM-D1/D7)**

- **Given** RedirectMiddleware PRE LocaleMiddleware + pravilo `old_path="/sr/stari-url/"`
- **When** GET `/sr/stari-url/`
- **Then** middleware vidi `request.path == "/sr/stari-url/"` (SA locale prefiksom — LocaleMiddleware još nije obradio) → match → 301
- **And** GET `/hu/stari-url/` (drugi locale, BEZ posebnog rule-a za hu) → NE matchuje `/sr/stari-url/` rule (path se razlikuje po prefiksu) → no redirect (passthrough)
- **And** za hu redirect, admin pravi ZASEBAN rule `old_path="/hu/regi-url/"` (locale-specifični rule per prefiks — SM-D7)

**AC7 — Middleware NE procesira static/media puteve (perf skip) (SM-D3)**

- **Given** RedirectMiddleware sa exclusion-skip
- **When** GET `/static/...` ili `/media/...` ili admin path
- **Then** middleware NE pravi DB lookup za te puteve (skip-prefiks grana) → prosledi dalje bez Redirect upita
- **And** test ovo dokazuje merenjem **upita SAMO protiv `seo_redirect` tabele**: koristi `django.test.utils.CaptureQueriesContext` i filtriraj uhvaćene upite na one koji pominju `seo_redirect` (Redirect model) → asertuj **NULA** Redirect-upita za skip-ovan path. **NE** koristi bare `assertNumQueries(0)` na ceo `client.get()` — to FAIL-uje zbog session/auth/contenttype/migracija upita koji nemaju veze sa Redirect-om (skip se odnosi SAMO na Redirect lookup, ne na ceo request)
- **And** za normalne puteve (NE static/media/admin) middleware pravi TAČNO JEDAN upit protiv `seo_redirect` (isti `CaptureQueriesContext` filtriran na `seo_redirect` → count == 1; indeksiran exact lookup — SM-D4)

## Tasks / Subtasks

> **Konvencija:** `[TEA-RED]` = Test Architect piše test PRE implementacije (mora FAIL). `[DEV-GREEN]` = Developer implementira da test prođe. **Dev NIKAD ne piše testove.** **IMA migracije** (6.4 je SCHEMA-CHANGING — `CreateModel Redirect`; manual review PRE commit per project-context migrations discipline). **NEMA `uv add`** (HttpResponsePermanentRedirect/ValidationError/CharField/BooleanField su Django core).

- [x] **Task 1 — `apps/seo/models.py:Redirect` model + open-redirect `clean()` (AC1/AC5, SM-D2/D6)** `[DEV-GREEN]`
  - [x] 1.1 U `apps/seo/models.py` dodaj `class Redirect(TimestampedModel):` (uz postojeći SeoMeta — NE menjaj SeoMeta). Polja:
    - `old_path = models.CharField(_("Stari put"), max_length=255, unique=True, db_index=True)` (verbose srpski sa dijakritikom).
    - `new_path = models.CharField(_("Novi put"), max_length=255)`.
    - `is_active = models.BooleanField(_("Aktivno"), default=True, db_index=True)`.
  - [x] 1.2 `Meta`: `verbose_name = _("Preusmerenje")`, `verbose_name_plural = _("Preusmerenja")`, `ordering = ["old_path"]`.
  - [x] 1.3 `__str__`: `return f"{self.old_path} → {self.new_path}"`.
  - [x] 1.4 **`clean()` open-redirect + self-loop guard (SM-D2 — SECURITY, MANDATORY):**
    ```python
    from django.core.exceptions import ValidationError
    from django.utils.http import url_has_allowed_host_and_scheme

    def clean(self):
        super().clean()
        # Open-redirect guard: new_path mora biti site-internal path.
        # url_has_allowed_host_and_scheme(allowed_hosts=None) odbija scheme-relative
        # //evil.com, apsolutni http(s)://, backslash /\evil.com, i encoded bypass-eve
        # (kanonska Django provera — pokriva slučajeve koje ručni startswith check propušta).
        if not url_has_allowed_host_and_scheme(url=self.new_path, allowed_hosts=None):
            raise ValidationError({"new_path": _("Novi put mora biti interni (site-internal path koji počinje sa „/“, bez domena ili šeme).")})
        # Self-loop guard: identičan old_path/new_path → beskonačni 301 na site-wide middleware-u.
        if self.old_path == self.new_path:
            raise ValidationError({"new_path": _("Novi put ne sme biti identičan starom putu (preusmerenje bi pravilo beskonačnu petlju).")})
        # old_path leading-slash guard: middleware matchuje protiv request.path (uvek počinje sa "/").
        # Bez "/" rule je TIHO mrtav (nikad ne matchuje) — admin typo "sr/stara/" se nikad ne aktivira.
        if not self.old_path.startswith("/"):
            raise ValidationError({"old_path": _("Stari put mora počinjati sa „/“ (mora odgovarati request.path, npr. „/sr/stara/“).")})
    ```
    **OBAVEZNO** koristi `django.utils.http.url_has_allowed_host_and_scheme` (NE ručno sklepan `startswith("//")`/`"://"` check — taj propušta backslash `/\evil.com` i encoded slash varijante). **`old_path` MORA početi sa `/`** (NE opciono): middleware matchuje protiv `request.path` koji UVEK počinje sa `/`; rule bez vodećeg `/` (admin typo `sr/stara/`) nikad ne matchuje = TIHO mrtvo pravilo zauvek. Guard sprečava silent-broken rule (graceful admin UX; primarni security check ostaje na `new_path`).
  - [x] 1.5 **`save()` override (SM-D2 — MANDATORY, enforcement na SVE write puteve):** dodaj override koji zove `self.full_clean()` PRE `super().save()`:
    ```python
    def save(self, *args, **kwargs):
        self.full_clean()  # primeni clean() open-redirect/self-loop guard na .save()/.create()/shell/migracije
        super().save(*args, **kwargs)
    ```
    Ovo čini guard obaveznim na svim ne-admin write putevima (Django `Model.save()` inače NE zove `full_clean()`). **Poznato ograničenje (prihvaćeno):** `bulk_create` zaobilazi `save()` — OK jer redirect tabela ne koristi bulk_create (admin-jedan-po-jedan; bulk import je OUT OF SCOPE). (Ekvivalentan field-level `validators=[...]` pristup na `new_path` je prihvatljiva alternativa — ali MORA da se okida na plain `.save()`/`.create()`, ne samo na admin formi; `save()`+`full_clean()` je DEFAULT zbog self-loop guard-a koji zahteva pristup i old_path i new_path.)
  - [x] 1.6 (Opciono — SM-D6 normalizacija) NE dodaj agresivnu trailing-slash normalizaciju u v1 (YAGNI; admin upisuje tačan path). Ako se odlučiš na normalizaciju, dokumentuj u `clean()` (NE menjaj path tiho — to bi zbunilo admin-a). **DEFAULT: bez normalizacije** (exact match na uneti path).

- [x] **Task 2 — Migracija `0002_redirect` (AC1) — ⚠️ SCHEMA-CHANGING, manual review** `[DEV-GREEN]`
  - [x] 2.1 `uv run python manage.py makemigrations seo` → generiše `apps/seo/migrations/0002_redirect.py` (`CreateModel Redirect`).
  - [x] 2.2 **MANUAL REVIEW** generisanog migration fajla (project-context anti-pattern „Migracija bez review-a"): potvrdi `CreateModel` ima old_path(CharField max_length=255, unique, db_index), new_path(CharField 255), is_active(BooleanField default True, db_index), created_at(DateTimeField auto_now_add), updated_at(DateTimeField auto_now), id BigAutoField. `dependencies` = `[("seo", "0001_initial")]`. NEMA alter na SeoMeta. NEMA modeltranslation _sr/_hu/_en kolone (Redirect nije u translation.py).
  - [x] 2.3 `uv run python manage.py migrate --plan` (verify plan) → `uv run python manage.py migrate seo`.
  - [x] 2.4 Commit model + migracija ZAJEDNO (atomic — project-context).

- [x] **Task 3 — `apps/seo/middleware.py:RedirectMiddleware` (AC2/AC4/AC6/AC7, SM-D1/D3/D4/D5)** `[DEV-GREEN]`
  - [x] 3.1 Kreiraj `apps/seo/middleware.py`. **Redosled definicija (presentation clarity): module-level konstante (`_SKIP_PREFIXES`, `_ADMIN_RE`) → `_is_skipped` helper → `RedirectMiddleware` klasa.** Helper `_is_skipped` MORA biti definisan PRE klase koja ga koristi u `__call__` (Python module-load redosled; klasa-telo se ne izvršava na import ali poziv u `__call__` zahteva da je ime u scope-u u runtime — bezbedno je definisati ga iznad radi jasnoće):
    ```python
    import re

    from django.http import HttpResponsePermanentRedirect

    from apps.seo.models import Redirect

    _SKIP_PREFIXES = ("/static/", "/media/")
    # 2-slovni locale prefiks (i18n_patterns) + admin base (tekući `admin` ili budući `admin-coric`).
    _ADMIN_RE = re.compile(r"^/[a-z]{2}/admin(-coric)?/")

    def _is_skipped(path):
        return path.startswith(_SKIP_PREFIXES) or bool(_ADMIN_RE.match(path))

    class RedirectMiddleware:
        def __init__(self, get_response):
            self.get_response = get_response

        def __call__(self, request):
            path = request.path
            if not _is_skipped(path):
                redirect = Redirect.objects.filter(old_path=path, is_active=True).first()
                if redirect is not None:
                    return HttpResponsePermanentRedirect(redirect.new_path)
            return self.get_response(request)
    ```
  - [x] 3.2 **EXCLUSION skip (SM-D3 — admin + static + media):** `_is_skipped(path)` (definisan u 3.1 PRE klase) → True ako path počinje sa `/static/`, `/media/`, ILI je admin path. **Admin-skip MORA biti forward-safe i derivirati admin base iz JEDNOG izvora istine (NE magic substring `'/admin/' in path`, NE hardkodovan `/admin-coric/`).** Admin je POD i18n_patterns → `/sr/admin/`, `/hu/admin/`, `/en/admin/`; a Epic 8 (8-1) planira preimenovanje slug-a na `admin-coric` → `/sr/admin-coric/`. Skip mora pokriti OBA bez budućeg silent-regress-a. **Preporučeni pristup (već prikazan u 3.1) — segment-aware regex `^/[a-z]{2}/admin(-coric)?/` koji tolerише i tekući i budući slug.** **Alternativa (još robusnija, ako Dev preferira jedinstveni izvor):** derivuj admin base iz `reverse('admin:index')` jednom na import-time (NE u `__call__` na svaki request — perf), uzmi locale-neutralni segment i izgradi prefiks-check. Bilo koji izbor MORA: (a) biti tačan za sve locale prefikse (`/sr/`, `/hu/`, `/en/`), (b) pokriti tekući `admin/` I planirani `admin-coric/` slug, (c) NE oslanjati se na `'/admin/' in path` substring (lomi se na `admin-coric` i rizikuje false-positive na content path koji sadrži `/admin/` segment). (Reconciliacija sa epics:964 `/admin-coric/` wording → vidi SM-D3.)
  - [x] 3.3 **Lookup (SM-D4 — JEDAN indeksiran upit):** `Redirect.objects.filter(old_path=path, is_active=True).first()` — koristi db_index na old_path + is_active filter; `.first()` vraća None ako nema match (no-match passthrough). **NE** `.all()` + Python iteracija (učitalo bi sve rule-ove — perf anti-pattern); **NE** keširaj sve rule-ove u memoriju u v1 (YAGNI; indeksiran upit je jeftin za ~desetine rule-ova; OQ-6 ako rule-set naraste).
  - [x] 3.4 **301 (SM-D5):** `HttpResponsePermanentRedirect(redirect.new_path)` — status 301, `Location: new_path`. NE 302 (epics:963 PERMANENT). new_path je već validiran (clean() write-time) → middleware ga trust-uje (NE re-validira na read — perf).

- [x] **Task 4 — `config/settings/base.py` MIDDLEWARE registracija PRE LocaleMiddleware (AC2, SM-D1) — ⚠️ ORDER-KRITIČNO** `[DEV-GREEN]`
  - [x] 4.1 U `MIDDLEWARE` listi (`base.py:57-69`) dodaj `"apps.seo.middleware.RedirectMiddleware"` **IZMEĐU** `"django.contrib.sessions.middleware.SessionMiddleware"` (`:60`) i `"django.middleware.locale.LocaleMiddleware"` (`:61`). Rezultat:
    ```python
    "django.contrib.sessions.middleware.SessionMiddleware",
    "apps.seo.middleware.RedirectMiddleware",  # NOVO Story 6.4 — PRE LocaleMiddleware (raw-path match SA locale prefiksom; SM-D1)
    "django.middleware.locale.LocaleMiddleware",
    ```
  - [x] 4.2 **Verifikuj order (AC2):** indeks(RedirectMiddleware) < indeks(LocaleMiddleware) u MIDDLEWARE. (Whitenoise/Security OSTAJU PRE Session; ostali OSTAJU POSLE Locale — insert NE remeti relativni red.)
  - [x] 4.3 `uv run python manage.py check` exit 0.

- [x] **Task 5 — `apps/seo/admin.py:RedirectAdmin` (AC3)** `[DEV-GREEN]`
  - [x] 5.1 U `apps/seo/admin.py` dodaj (uz postojeće SeoMetaInline/SeoWarningAdminMixin — NE menjaj njih):
    ```python
    from django.contrib import admin
    from apps.seo.models import Redirect

    @admin.register(Redirect)
    class RedirectAdmin(admin.ModelAdmin):
        list_display = ("old_path", "new_path", "is_active", "created_at")
        list_filter = ("is_active",)
        search_fields = ("old_path", "new_path")
        list_editable = ("is_active",)
    ```
  - [x] 5.2 (Deaktivacija — AC3) `list_editable = ("is_active",)` omogućava toggle direktno iz liste. ALTERNATIVA (Dev bira): admin akcije `make_active`/`make_inactive` (`actions = [...]`) — oba zadovoljavaju „deaktivira". (Ako `list_editable` na is_active + `list_display` prvi element NIJE link — Django zahteva da bar jedan list_display bude clickable link; old_path je default link → OK.)
  - [x] 5.3 Redirect admin form automatski poziva `full_clean()` (ModelForm) → `clean()` open-redirect guard se aktivira u admin add/edit (AC5 kroz admin). Potvrdi: unos `new_path="https://evil.com"` u admin → form error (NE save).

- [x] **Task 6 — RED testovi (TEA; Dev NE piše) (AC1-AC7)** `[TEA-RED]`
  - [x] 6.1 `test_redirect_model.py` (AC1): create + default is_active=True; `__str__`; old_path unique (drugi isti old_path → IntegrityError); Redirect NIJE u modeltranslation registry (`get_translatable_fields` ili sl. — NEMA _sr suffix kolone).
  - [x] 6.2 `test_redirect_open_redirect.py` (AC5 — SECURITY LOCK): pokrij SVE bypass-vektore + enforcement-na-write:
    - `Redirect(old_path="/sr/x/", new_path="https://evil.com").full_clean()` → ValidationError (apsolutni eksterni).
    - `new_path="//evil.com"` → ValidationError (scheme-relative).
    - `new_path="/\evil.com"` (backslash bypass) → ValidationError (dokazuje da `url_has_allowed_host_and_scheme` hvata backslash koji ručni `startswith` propušta).
    - `new_path="javascript:alert(1)"` → ValidationError.
    - **Self-loop:** `Redirect(old_path="/sr/x/", new_path="/sr/x/").full_clean()` → ValidationError (SM-D2 self-loop guard).
    - **old_path leading-slash:** `Redirect(old_path="sr/stara/", new_path="/sr/nova/").full_clean()` → ValidationError na `old_path` (sprečava tiho-mrtvo pravilo — admin typo bez vodećeg „/").
    - **Enforcement NIJE admin-only:** `Redirect.objects.create(old_path="/sr/x/", new_path="https://evil.com")` → ValidationError (dokazuje da `save()` override zove `full_clean()` — guard radi van admin forme); analogno `r = Redirect(...invalid...); r.save()` → ValidationError.
    - `new_path="/sr/ok/"` (old_path različit, site-internal) → PROLAZI (no error). (Open-redirect guard — SM-D2/SEO4-2.)
  - [x] 6.3 `test_redirect_middleware.py` (AC2/AC4/AC6/AC7): 
    - aktivno pravilo `/sr/stara/`→`/sr/nova/`: `client.get("/sr/stara/")` → status 301, `response["Location"] == "/sr/nova/"`.
    - is_active=False pravilo → `client.get(...)` NIJE 301 (passthrough — AC4).
    - no-match path → NIJE 301 (passthrough).
    - admin path (`/sr/admin/`) sa pravilom koje bi matchovalo → NIJE redirektovan middleware-om (admin skip — AC2/SM-D3).
    - **forward-safe admin slug (CRITICAL-2 LOCK):** pravilo `old_path="/sr/admin-coric/secret/"` → `client.get("/sr/admin-coric/secret/")` NIJE redirektovan našim middleware-om (skip pokriva i budući `admin-coric` slug — Epic 8 ne sme regresirati skip). Dokazuje da skip NIJE krhki `'/admin/'` substring.
    - static/media path → NE pravi Redirect DB upit: koristi `CaptureQueriesContext` filtriran na `seo_redirect` tabelu (asertuj ZERO Redirect-upita na `/static/x`); normalan path → TAČNO 1 `seo_redirect` upit. **NE** bare `assertNumQueries(0)` na ceo request (session/auth/contenttype upiti bi ga oborili — AC7/SM-D4).
    - i18n: `/hu/stara/` NE matchuje `/sr/stara/` rule (raw-path razlika — AC6).
  - [x] 6.4 `test_redirect_middleware_order.py` (AC2/SM-D1 — ORDER LOCK): `from django.conf import settings`; `mw = settings.MIDDLEWARE`; `assert mw.index("apps.seo.middleware.RedirectMiddleware") < mw.index("django.middleware.locale.LocaleMiddleware")`. (Lock-uje SM-D1 ordering — ako neko premesti middleware POSLE Locale, test RED.)
  - [x] 6.5 `test_redirect_admin.py` (AC3): RedirectAdmin registrovan (`admin.site.is_registered(Redirect)`); list_display/list_filter/search_fields/list_editable konfigurisani; superuser changelist GET 200; add form sa nevalidnim new_path → form invalid (open-redirect kroz admin — AC5). **list_editable round-trip (AC3/AC4):** kreiraj aktivno pravilo → `client.get("/sr/stara/")` 301 → superuser POST na changelist sa `is_active=False` (changelist `list_editable` save formset) → re-fetch iz DB `is_active is False` → `client.get("/sr/stara/")` više NIJE 301 (middleware vidi deaktivirano). Dokazuje da admin-deaktivacija kroz changelist stvarno zaustavi redirect (osim već-keširanih klijenata — SEO4-9).
  - [x] 6.6 `test_redirect_migration.py` (AC1): `makemigrations --check --dry-run` → „No changes detected" (model/migracija sync); migracija primenjiva (pytest-django auto-applies; sanity da tabela postoji + kolone).

- [x] **Task 7 — Verifikacija + sprint-status (svi AC)** `[DEV-GREEN]`
  - [x] 7.1 Pokreni ceo `apps/seo/tests/` suite — SVE GREEN. **6-1/6-2/6-3 seo testovi MORAJU ostati GREEN** (6.4 SAMO dodaje Redirect model + middleware + admin; ne menja SeoMeta/sitemaps/views/templatetags).
  - [x] 7.2 `uv run python manage.py makemigrations --check --dry-run` → „No changes detected" (migracija 0002 committed; model sync).
  - [x] 7.3 `uv run python manage.py check` exit 0. **Manualno (opciono):** runserver, kreiraj Redirect u admin (`/sr/admin/seo/redirect/add/`), GET `/sr/stara/` → potvrdi 301 → `/sr/nova/` (browser dev-tools Network tab status 301 + Location).
  - [x] 7.4 **Regression — middleware blast-radius:** potvrdi da BEZ ijednog Redirect pravila (prazna tabela) middleware NE lomi normalan saobraćaj — GET home `/sr/` → 200 (1 dodatni Redirect upit po request-u, no-match passthrough; potvrdi da NEMA 500 ni redirect-loop). Test: full home/detail strane render GREEN sa middleware aktivnim.
  - [x] 7.5 Update `_bmad-output/implementation-artifacts/sprint-status.yaml`: `6-4` → done/ready-for-review.

## SM odluke (Decision log)

**SM-D1 — MIDDLEWARE ORDER (PRE LocaleMiddleware) + RAW-PATH MATCH (GLAVNA odluka; epics:962).** `RedirectMiddleware` se registruje u `MIDDLEWARE` PRE `django.middleware.locale.LocaleMiddleware` (verifikovano base.py:61 — Locale je odmah posle Session:60). Insert na indeks 4 (između Session i Locale). **Razlog (TAČAN — bez netačne kauzalne tvrdnje):** `LocaleMiddleware.process_request` postavlja `request.LANGUAGE_CODE` i aktivira prevod na osnovu locale prefiksa, ALI **NE menja/ne strip-uje `request.path`** — locale prefiks (`/sr/`, `/hu/`, `/en/`) je prisutan u `request.path` BEZ OBZIRA na red middleware-a (i pre i posle LocaleMiddleware path ostaje `/sr/stari/`). Dakle prefiks je vidljiv u oba slučaja; STVARNI razlog da RedirectMiddleware trči PRE LocaleMiddleware/CommonMiddleware je da **short-circuit-uje (vrati 301) PRE nego što se uključe APPEND_SLASH (CommonMiddleware) i locale-redirect interakcije** — ako bi naš redirect trčao POSLE njih, APPEND_SLASH/locale-redirect bi mogli prvi da intervenišu na isti path i naprave dvostruke redirect-e ili loop (vidi SEO4-1). Admin upisuje `old_path` tačno kako URL stvarno izgleda (sa prefiksom) → exact match je predvidljiv. Ovo je epics:962 doslovce („registrujem middleware ranije od LocaleMiddleware"). **Process flow:** middleware kao callable-klasa — logika u `__call__` PRE `self.get_response(request)` (process_request ekvivalent); ako match → vrati 301 ODMAH (short-circuit, view se NE poziva); ako ne → `get_response` (nastavi lanac). Whitenoise/Security OSTAJU PRE Session (statiku/security handluju prvi); ostali (Common/Csrf/Auth/...) OSTAJU POSLE Locale (insert ne remeti njih). **Order-lock test (Task 6.4) zaključava ovaj poredak** — premeštanje POSLE Locale → RED.

**SM-D2 — OPEN-REDIRECT GUARD (HIGH-severity security; write-time validacija, read-time trust).** `new_path` postaje `Location` header u 301. Bez guard-a, admin (ili kompromitovan nalog) može uneti `new_path="https://evil.com"` → 301 na eksterni sajt = open-redirect (phishing, SEO-poisoning, OAuth-token-theft vektor). **Odluka: `new_path` MORA biti site-internal path** — `Redirect.clean()` validira kroz Django built-in `django.utils.http.url_has_allowed_host_and_scheme(url=self.new_path, allowed_hosts=None)` (kanonska provera koja odbija scheme-relative `//evil.com`, apsolutni `http(s)://`, backslash `/\evil.com`, i encoded bypass-eve — ručni `startswith("//")`/`"://"` check se NE koristi jer propušta backslash i encoded varijante). Dodatno, `clean()` odbija `old_path == new_path` (self-loop guard — beskonačni 301 na site-wide middleware-u). `ValidationError({"new_path": ...})` na kršenje. Validacija je na WRITE granici — middleware NE re-validira na svaki read (perf: trust validated data; boundary-validacija je project-context-saglasna). **Enforcement je MANDATORY na SVIM write putevima (NE opcioni).** Django `Model.save()` NE poziva `full_clean()` automatski — admin ModelForm DA (kroz form validaciju), ali programski `.objects.create()`/`.save()`/shell/migracije/fixtures/testovi NE bi. Pošto je ovo HIGH-severity Location-header-injection surface, **DEFAULT je MANDATORY `Redirect.save()` override koji zove `self.full_clean()` PRE `super().save()`** (Task 1.5/AC1/AC5/SEO4-2) → guard se primenjuje na SVE write puteve, ne samo admin formu. **Dokumentovan i prihvaćen izuzetak:** `bulk_create` (i raw-SQL insert) zaobilazi `save()` (Django ne zove save() po objektu) — prihvatljivo jer redirect tabela realno ne koristi bulk_create (admin-jedan-po-jedan, ~desetine rule-ova; bulk import OUT OF SCOPE). Ekvivalentan field-level `validators=[...]` na `new_path` je prihvatljiva alternativa ALI MORA okidati na plain `.save()`/`.create()`; `save()`+`full_clean()` je DEFAULT jer self-loop guard zahteva pristup i `old_path` i `new_path`.

**SM-D3 — EXCLUSION SKIP (admin + static + media; forward-safe admin derivacija; NE DB lookup za njih).** Middleware trči na SVAKOM request-u (uključujući admin, static, media). **AC2 eksplicitno traži admin-skip.** Dodatno skip-ujemo static/media (perf — nema smisla raditi Redirect upit za asset). Skip logika: `path.startswith(("/static/", "/media/"))` ILI admin-path (segment-aware). **Admin-skip MORA biti derivirano iz JEDNOG izvora istine, NE magic substring.** Razlog za odbacivanje `"/admin/" in path`: (a) **silent regress na Epic 8 slug-promenu** — kad 8-1 preimenuje admin na `admin-coric` → stvarni path postaje `/sr/admin-coric/secret/`, a `'/admin/'` NIJE substring toga (`admin-coric` nema `/admin/` segment) → admin stranice postaju redirectable = availability/security regresija; (b) **false-positive rizik** na legitiman content path koji slučajno sadrži `/admin/` segment. **Odluka — forward-safe skip:** segment-aware regex `^/[a-z]{2}/admin(-coric)?/` (locale-prefiks + admin base koji tolerише i tekući `admin` i planirani `admin-coric` slug) ILI derivacija admin base-a iz `reverse('admin:index')` (import-time, ne per-request — perf). Bilo koji izbor pokriva sve locale prefikse (`/sr/`, `/hu/`, `/en/`) i OBA slug-a bez budućeg ažuriranja. **Reconciliacija epics:964 vs stvarni slug:** epics:964 doslovce kaže „middleware NE procesira admin URL-ove `/admin-coric/`" ALI config/urls.py:42 trenutno registruje `admin/` (stvarni path `/sr/admin/`); project-context:197 preporučuje `admin-coric` ali to je Epic 8 deliverable, NIJE primenjeno u 6.4. **Resolucija: skip se derivira iz konfigurisanog admin base-a i tačan je za OBA — tekući `admin/` I planirani `admin-coric/`** — pa ni TEA ni Dev NE implementira literal `/admin-coric/`-prefiks (lomilo bi tekući admin) ni krhki `'/admin/'` substring (lomi se na budući slug). Mirror 6-3 robots `*/admin/` Disallow je pojmovno isti (admin pod i18n), ali za skip-grananje koristimo robusniji segment-match jer je correctness/availability-kritičan (vidi SEO4-4).

**SM-D4 — PERF: JEDAN INDEKSIRAN UPIT po request-u (query budget).** Middleware na svaki request pravi `Redirect.objects.filter(old_path=request.path, is_active=True).first()`. `old_path` ima `db_index=True` + `is_active` ima `db_index=True` → exact-match upit je jeftin (index seek). `.first()` → None ako nema (no-match passthrough — najčešći slučaj). **NE `.all()`+Python loop** (učitalo bi sve rule-ove svaki put — O(n) memorija/transfer). **NE in-memory cache svih rule-ova u v1** (YAGNI — ~desetine rule-ova, indeksiran upit je <1ms; ako rule-set naraste na hiljade ILI postane hot-path bottleneck → 6.x može dodati cache sa invalidacijom na save signal — OQ-6). Skip-ovani putevi (admin/static/media — SM-D3) NE prave NIJEDAN upit (`assertNumQueries(0)` za Redirect na static — AC7). Normalan path = TAČNO 1 dodatni upit po request-u (dokumentovan query-budget porast — mirror 6-1 cache-budget disciplina).

**SM-D5 — 301 PERMANENT ONLY (NE 302, NE konfigurabilan tip).** epics:963 traži „HTTP 301". Odluka: isključivo `HttpResponsePermanentRedirect` (301). Redirect-tip NIJE konfigurabilan polje (`is_permanent` boolean) u v1 — YAGNI (sve SEO redirect-e su 301 permanent; 302 je za privremene koji se retko admin-upravljaju). 301 govori search engine-ima da prenose ranking na novi URL (cela svrha story-je — epics:956 „bez gubitka SEO ranking-a"). Ako biznis ikad zatraži 302 (privremena promociona preusmerenja) → 6.x dodaje `is_permanent` polje + grananje (`HttpResponsePermanentRedirect` vs `HttpResponseRedirect`) — OQ-2 DEFER.

**SM-D6 — old_path/new_path su ASCII URL PUTEVI (NIJE translatable; old_path unique).** Putevi su jezik-neutralni URL stringovi (locale-prefiks JE deo old_path-a — `/sr/...` vs `/hu/...` — ali sam string nije „prevod"). `translation.py` se NE dira — Redirect NEMA _sr/_hu/_en kolone (mirror project-context „slugovi/URL-ovi su ASCII"; ne-translatable URL). `old_path` je `unique=True` (jedan rule po starom putu — ako se isti stari put redirektuje na dva mesta = greška; unique sprečava). Verbose_name-ovi polja su srpski sa dijakritikom (admin UI label-i — to JE user-facing → „Stari put"/„Novi put"/„Aktivno" sa punim dijakritikama), ali VREDNOSTI polja su ASCII URL (NE prolaze kroz gettext). **SM-D6 normalizacija (trailing slash):** DEFAULT bez auto-normalizacije (exact match na uneti path; admin je odgovoran da unese tačan path uključujući trailing slash — Django APPEND_SLASH ionako dodaje `/` na ne-slash puteve pre nego stignu do match-a, ali to je CommonMiddleware POSLE Locale → van našeg raw-path domena). Ne menjaj path tiho u clean() (zbunilo bi admin-a). Ako trailing-slash mismatch postane čest support-problem → 6.x normalizacija (OQ-7).

**SM-D7 — i18n LOCALE-PREFIKS interakcija (raw-path SA prefiksom; locale-specifični rule-ovi).** Pošto RedirectMiddleware trči PRE LocaleMiddleware (SM-D1), vidi `request.path` SA locale prefiksom (`/sr/stara/`). **Posledica:** `old_path` se upisuje SA prefiksom; redirect je locale-specifičan po dizajnu. Da bi se isti logički redirect primenio na sve jezike, admin pravi 3 rule-a (`/sr/stara/`, `/hu/regi/`, `/en/old/` → odgovarajući novi putevi). **Alternativa razmotrena i ODBAČENA:** middleware POSLE LocaleMiddleware (path bez prefiksa) + locale-agnostični old_path — ALI to (a) krši epics:962 („pre LocaleMiddleware"), (b) zahteva re-konstrukciju prefiksa za new_path Location, (c) komplikuje match logiku. **Odluka: raw-path SA prefiksom, locale-specifični rule-ovi** — jednostavno, eksplicitno, epics-saglasno. Većina realnih redirect-a je ionako locale-specifična (sr URL se menja nezavisno od hu). Cross-locale redirect (jedan rule za sve jezike) je 6.x enhancement ako zatreba (OQ-8 — npr. prefix-stripping middleware varijanta).

**SM-D8 — CUSTOM model + middleware (NE `django.contrib.redirects`/`django.contrib.sites`).** Django ima built-in `django.contrib.redirects` app, ALI ON ZAHTEVA `django.contrib.sites` + `SITE_ID` (RedirectFallbackMiddleware vezuje redirect za Site objekat). Projekat NE koristi sites framework (6-2 SM-D2 — RequestSite/Host iz request-a, NE SITE_ID; ALLOWED_HOSTS granica). Uvođenje sites samo za redirects bi dodalo SITE_ID config + sites migraciju + Site fixture = nepotreban coupling. **Odluka: custom `Redirect` model + custom `RedirectMiddleware`** — bez sites dependency, konzistentno sa apps.seo (RequestSite-style host-agnostic), lakše (3 polja vs sites-vezan model). Dodatno, custom middleware nam daje kontrolu nad raw-path-match (SM-D1) i open-redirect guard (SM-D2) koje contrib.redirects ne nudi out-of-box. Mirror 6-2 odluke da se NE uvodi sites framework.

**SM-D9 — FORWARD: 6.4 zatvara redirect-management; 6.5/6.6 su zasebni.** 6.4 isporučuje admin-upravljani 301 redirect (model + middleware + admin). **NE over-reach:** 6.5 (i18n fallback ⓘ tooltip — `apps/core/templatetags/i18n_fallback.py`), 6.6 (hreflang HTML `<link>` tagovi + locale-aware slug verifikacija) su ZASEBNE story-je. 6.4 NE dodaje hreflang, NE dodaje i18n marker, NE dira seo_meta.py/views.py/sitemaps.py (6-1/6-2/6-3 artefakti netaknuti). `apps/seo/middleware.py` koji 6.4 kreira je PRVI middleware u apps.seo. Posle 6.4, apps.seo sadrži: models (SeoMeta + Redirect), views (robots_txt), sitemaps, middleware (RedirectMiddleware), templatetags (seo_meta), admin (SeoMetaInline + RedirectAdmin) — kompletan SEO surface osim i18n marker/hreflang (6.5/6.6).

## Gotchas

**SEO4-1 — MIDDLEWARE ORDER je correctness-kritičan (PRE LocaleMiddleware).** Ako se RedirectMiddleware ubaci POSLE LocaleMiddleware, raw-path-match (SM-D1) se lomi suptilno: LocaleMiddleware ne menja `request.path` (ostaje sa prefiksom) ALI red middleware-a određuje semantiku i epics:962 eksplicitno traži „ranije". GLAVNI rizik: ako se stavi POSLE CommonMiddleware (koji radi APPEND_SLASH i redirect na slash-varijantu) → interakcija sa našim redirect-om može praviti dvostruke redirect-e ili loop. **MORA biti PRE Locale (indeks 4, između Session i Locale).** `test_redirect_middleware_order.py` (Task 6.4) zaključava indeks-poredak — ako iko premesti, test RED.

**SEO4-2 — OPEN-REDIRECT: `save()` MORA zvati `full_clean()` (Django `Model.save()` NE zove clean automatski).** Django `Model.save()` NE poziva `full_clean()`/`clean()` — po default-u validacija je odgovornost FORME (admin ModelForm to radi). Ako bi guard ostao SAMO u `clean()`, programski `Redirect.objects.create(new_path="https://evil.com")` / `.save()` / shell / data-migracija / fixture BI prošao bez validacije = open-redirect surface i dalje otvoren na ne-admin putevima. **Pošto je ovo HIGH-severity Location-header-injection surface, enforcement NIJE opcioni** (Task 1.5): `Redirect.save()` je MANDATORY override koji zove `self.full_clean()` PRE `super().save()` → guard se primenjuje na SVE write puteve, ne samo admin formu. **Granica (poznato ograničenje, prihvaćeni rezidualni rizik):** `QuerySet.update()`, `bulk_create()` i raw SQL ZAOBILAZE `save()`/`full_clean()` (Django ih ne rutira po objektu) — OK jer redirect tabela realno ne koristi te puteve (admin-jedan-po-jedan, ~desetine rule-ova; bulk import OUT OF SCOPE) i to su trusted-operator putevi gde NIJEDAN untrusted input ne dospeva do `new_path`. Ako ikad uđe untrusted bulk import, validacija MORA biti dodata eksplicitno na tom putu. Test (Task 6.2) proverava OBA puta: `redirect.full_clean()` direktno I da programski `.save()`/`.objects.create()` sa nevalidnim new_path raise-uje `ValidationError` (dokazuje da enforcement nije admin-only). **NB hardening:** guard koristi `url_has_allowed_host_and_scheme` (NE ručni `startswith` check — propušta backslash/encoded bypass) + `old_path == new_path` self-loop guard.

**SEO4-3 — MIDDLEWARE na svaki request = global blast-radius.** RedirectMiddleware trči za SVAKI HTTP request (uključujući 404, static fallback, admin). Greška u `__call__` (npr. neuhvaćen exception u DB lookup-u, redirect-loop, ili match koji ne treba) → CEO sajt 500/loop. **Disciplina:** (a) skip admin/static/media PRE DB lookup (SM-D3) — admin mora ostati dostupan čak i ako Redirect tabela ima problem; (b) `.first()` (NE `.get()` — `.get()` raise-uje DoesNotExist/MultipleObjectsReturned → 500); (c) NE redirect na isti path (self-loop guard: `new_path == old_path` rule pravi beskonačni 301 — **MANDATORY clean() guard, SM-D2/AC5**, odbija identičan par sa ValidationError; ostaje samo A→B i B→A lanac koji NE guard-ujemo u v1 — admin odgovornost, OQ); (d) prazna tabela → svaki request 1 no-match upit + passthrough (Task 7.4 potvrđuje 200, ne 500).

**SEO4-4 — admin skip MORA biti PRE DB lookup (dostupnost admin-a).** Ako bi middleware radio DB lookup za `/sr/admin/...` PRE skip-a, i Redirect tabela/DB ima problem → admin nedostupan = ne možeš popraviti redirect-e. Skip admin/static/media PRVO (rana grana), DB lookup TEK za ostale puteve. Forward-safe admin-segment match (SM-D3 — regex `^/[a-z]{2}/admin(-coric)?/` ili `reverse('admin:index')`-derivacija, NE `'/admin/' in path` substring) PRE `Redirect.objects.filter`. Ovo je i AC2 zahtev (admin-skip) i dostupnost-safety. **NB:** krhki substring NE samo da rizikuje false-positive već BI lomilo skip kad Epic 8 preimenuje slug na `admin-coric` → admin postaje redirectable (availability regresija) — zato je derivacija iz jednog izvora istine obavezna (SM-D3).

**SEO4-5 — old_path/new_path NISU translatable (NE dodaj u translation.py).** Iskušenje: pošto su drugi apps.seo modeli (SeoMeta) translatable, mogao bi neko dodati Redirect u translation.py. **NE** — putevi su ASCII URL-ovi, locale je deo old_path-a (`/sr/` prefiks), NEMA „prevoda" URL-a. Dodavanje u translation.py bi generisalo besmislene _sr/_hu/_en kolone + nepotrebnu migraciju. `translation.py` OSTAJE netaknut (samo SeoMeta). Verbose_name LABEL-i (admin UI) JESU srpski-dijakritika (user-facing), ali to je `_("Stari put")` gettext na LABEL, NE modeltranslation na VREDNOST (SM-D6).

**SEO4-6 — CharField unique+db_index (NE URLField).** `old_path`/`new_path` su `CharField` (NE `URLField`) jer `URLField` validira FULL URL (sa shemom/domenom) — a mi želimo INTERNE puteve (`/sr/stara/`) koji NISU validni „URL-ovi" po URLField (nemaju scheme/host). `CharField(max_length=255)` + naš `clean()` guard (SM-D2) je tačan tip. `unique=True` + `db_index=True` na old_path (jedan rule + brz lookup — SM-D4/D6). max_length=255 pokriva realne path-dužine (URL path retko >255 char).

**SEO4-7 — `.first()` NE `.get()` (MultipleObjectsReturned/DoesNotExist guard).** old_path je `unique` → teoretski `.get()` bi radio, ALI `.get()` raise-uje `DoesNotExist` kad nema match (svaki no-match request = exception = 500). `.filter(...).first()` vraća None graceful (no-match passthrough — najčešći put). Mirror standardni Django middleware obrazac. NIKAD `.get()` u middleware hot-path.

**SEO4-8 — i18n prefiks: rule je locale-specifičan (NE cross-locale).** `/sr/stara/` rule NE redirektuje `/hu/stara/` (raw-path razlika — SM-D7). Ovo je OČEKIVANO (NE bug): admin pravi rule per locale. Dev/test NE treba da očekuje da jedan rule pokriva sve jezike. Ako test proverava cross-locale, to je pogrešan test (SM-D7 — locale-specifični rule-ovi su dizajn). AC6 zaključava: `/hu/...` ne matchuje `/sr/...` rule.

**SEO4-9 — 301 je AGRESIVNO i TRAJNO keširan u browser-ima/proxy-jima (deaktivacija NE „odvezuje" već-poslužene posetioce).** HTTP 301 (`HttpResponsePermanentRedirect`) browser-i i proxy-ji keširaju agresivno, često **indefinitely** (bez Cache-Control/Expires, 301 je po RFC perzistentno keširabilan). **Posledica za operatere:** AC3/AC4 „deaktiviraj pravilo da zaustaviš redirect" radi SAMO za klijente koji JOŠ NISU keširali 301. Posetilac/bot koji je već dobio 301 → ostaje preusmeren (ide direktno na `new_path`, NE pogađa server) čak i posle `is_active=False`, dok mu se keš ne istekne/očisti. **Praktična smernica:** (a) tretiraj 301 kao teško-reverzibilan — uvedi rule tek kad je `new_path` stabilan; (b) ako redirect MORA biti privremen/reverzibilan, 301 NIJE pravi izbor (to bi bio 302 — OQ-2, van v1 scope-a); (c) za pogrešno uneto pravilo, ispravka je da se kreira NOVI redirect ka tačnoj destinaciji (deaktivacija sama ne dohvata keširane klijente). **Napomena o odgovoru:** v1 NE postavlja eksplicitan dug `Cache-Control` (`HttpResponsePermanentRedirect` ne dodaje ga sam) — keširanje zavisi od heuristike klijenta; ovo je svesno (YAGNI, NE komplikujemo header u v1), ali admin/dev MORAJU biti svesni da je 301 de-facto trajan na klijentskoj strani.

**SEO4-10 — trailing-slash: middleware trči PRE CommonMiddleware (APPEND_SLASH), pa `/sr/stara` (bez `/`) NE matchuje rule `/sr/stara/`.** RedirectMiddleware je PRE `CommonMiddleware` (SM-D1), a APPEND_SLASH (dodavanje `/` na ne-slash GET) radi CommonMiddleware — TEK POSLE našeg middleware-a. Zato naš middleware vidi SIROV path: inbound legacy URL `/sr/stara` (bez trailing slash) **NE matchuje** rule sačuvan kao `/sr/stara/` → pada kroz na 404 (ili na APPEND_SLASH koji doda `/` pa view-routing odluči) — defeating cilj baš za one legacy URL-ove koji su najverovatnije pogođeni starim/eksternim linkovima bez slash-a. **Smernica za Dev/admin (trade-off eksplicitan, implementacija NIJE nametnuta):** (a) **minimalno** — instruiši admin-a da unese KANONSKI (slash-ovan) path tačno kako Django rute izgledaju (`/sr/stara/`), i prihvati da non-slash varijanta neće matchovati u v1 (dokumentovano ograničenje, OQ-7); ILI (b) **robusnije** — u middleware lookup-u matchuj i `request.path` i `request.path.rstrip('/')` (npr. `Redirect.objects.filter(old_path__in=[path, path.rstrip('/')], is_active=True)` ili dva `.filter().first()` pokušaja) tako da i slash i non-slash varijanta pogode isti rule. Opcija (b) hvata više legacy URL-ova ali blago komplikuje lookup; ako se ne usvoji, (a) je prihvatljiv v1 default uz jasnu admin-instrukciju. **NE forsiraj (b) ako komplikuje model** — ali trade-off (legacy non-slash → 404) MORA biti svesna odluka, ne slučajnost. (Vidi OQ-7 za trailing-slash normalizaciju.)

## Open Questions

**OQ-1 — regex/wildcard/prefix redirect pravila?** v1 je EXACT-match na pun old_path. Pattern-based (`/stari-blog/* → /blog/*`, regex capture groups) je moćnije ali kompleksnije (perf — ne može indeksiran exact lookup; mora iterirati pattern-e). **SM odluka: EXACT-match v1** (epics:961 implicira exact path par; ~desetine manuelnih redirect-a). Ako biznis migrira celu URL-strukturu (masovni pattern redirect) → 6.x dodaje `is_regex`/`match_type` polje + pattern engine. NE-blocking.

**OQ-2 — 302 (privremeni) redirect podrška?** v1 je 301 PERMANENT only (SM-D5). `is_permanent` boolean polje + grananje (`HttpResponsePermanentRedirect` vs `HttpResponseRedirect`) bi dodalo 302 podršku. **SM odluka: 301 only** (epics:963; SEO redirect = permanent). DEFER do biznis-zahteva za privremena preusmerenja. NE-blocking.

**OQ-3 — hit-logging / analytika (last_accessed, hit_count)?** v1 NE loguje hit-ove na redirect rule. `hit_count`/`last_accessed_at` polje bi pokazalo koja pravila se koriste (čišćenje mrtvih rule-ova) ALI dodaje write na svaki redirect (perf — write-na-read). **SM odluka: bez logging-a v1** (manuelno admin-upravljano; GlitchTip/access-log pokriva diagnostiku). 6.x/8.x admin-dashboard može dodati hit-counter (async/signal da ne blokira redirect). NE-blocking.

**OQ-4 — query string / fragment u match-u?** v1 matchuje SAMO `request.path` (bez `?query=...`). Redirect-i sa query-param (`/stara/?id=5 → /nova/`) nisu podržani; query string se NE prenosi u Location (`new_path` je čist). **SM odluka: path-only match** (epics:961 „old_path"/„new_path" su putevi; query je retko deo SEO redirect-a). Ako zatreba query-preservation (`?utm=...` prenos) → 6.x. NE-blocking.

**OQ-5 — admin skip prefiks (RESOLVED u SM-D3 — forward-safe derivacija, NIJE deferral).** Ranije razmatrano kao `"/admin/" in path` labav match sa deferral-om za Epic 8 slug-promenu. **REŠENO (CRITICAL-2):** skip se sada DERIVIRA iz jednog izvora istine (segment-aware regex `^/[a-z]{2}/admin(-coric)?/` ILI `reverse('admin:index')`-derivacija na import-time), tačan za OBA — tekući `admin/` I planirani `admin-coric/` slug. Krhki substring je ODBAČEN (lomi se na slug-promenu = availability regresija; SM-D3/SEO4-4). Test zaključava oba slug-a (Task 6.3). **Više nije open** — forward-compatibility je deo 6.4 deliverable-a, ne deferred. (Ostatak možda-budućeg admin-path razmatranja: ako Epic 8 uvede potpuno drugačiji slug van `admin`/`admin-coric` para, regex/derivacija se trivijalno proširi — ali `reverse('admin:index')` pristup to već automatski hvata.)

**OQ-6 — in-memory cache redirect rule-ova (skaliranje)?** v1 pravi 1 indeksiran DB upit po request-u (SM-D4). Za ~desetine rule-ova to je <1ms (zanemarljivo). Ako rule-set naraste na hiljade ILI postane hot-path bottleneck (visok saobraćaj) → cache svih aktivnih rule-ova u memoriji (dict old_path→new_path) sa invalidacijom na `Redirect` save/delete signal. **SM odluka: DB-upit-po-request v1** (YAGNI; no-Celery/no-Redis duh projekta v1 — project-context:84). Cache je 6.x/9.x perf optimizacija AKO load-test pokaže potrebu. NE-blocking.

**OQ-7 — trailing-slash normalizacija / non-slash legacy URL match?** v1 je exact-match (SM-D6) — `/sr/stara` i `/sr/stara/` su RAZLIČITI putevi. Django APPEND_SLASH (CommonMiddleware, POSLE Locale → van našeg raw-domena) dodaje `/` na ne-slash GET-ove pre view-a, ali NAŠ middleware (PRE Locale/Common) vidi sirov path. **Posledica (SEO4-10):** inbound legacy `/sr/stara` (bez `/`) NE matchuje rule `/sr/stara/` → fall-through na 404 — baš za legacy URL-ove koji su najverovatnije pogođeni. **SM odluka za v1:** DEFAULT bez auto-normalizacije (admin upisuje KANONSKI slash-ovan path kako Django rute izgledaju — `/sr/stara/`). **Refinement za Dev (SEO4-10) — opciono, NE-blocking:** ako se želi pokriti i non-slash varijanta, middleware može matchovati i `request.path` i `request.path.rstrip('/')` (npr. `old_path__in=[path, path.rstrip('/')]`) — hvata više legacy linkova uz blago složeniji lookup. Ako trailing-slash mismatch postane čest support-problem → 6.x normalizacija u `clean()` ILI match-time. NE-blocking.

**OQ-8 — cross-locale redirect (jedan rule za sve jezike)?** SM-D7: rule je locale-specifičan (raw-path sa prefiksom). Jedan logički redirect = 3 rule-a (sr/hu/en). Ako admin-burden postane problem (mnogo redirect-a × 3 jezika) → 6.x varijanta sa locale-agnostičnim old_path (strip prefiks pre match, re-add za Location) ILI „apply to all locales" admin flag koji auto-generiše 3 rule-a. **SM odluka: locale-specifični rule-ovi v1** (epics:962 raw-path; jednostavno/eksplicitno). NE-blocking.

## Testing

> **TEA piše SVE testove PRE implementacije (RED). Dev NE piše testove.** Mirror `apps/seo/tests/` (6-1/6-2/6-3) layout + conftest. Django test `client` za middleware end-to-end (301 status + Location); `RequestFactory` ILI direktan model za clean()/open-redirect; `settings.MIDDLEWARE` introspekcija za order-lock. **IMA migracija** → `test_redirect_migration.py` sanity (`makemigrations --check` clean).

- **`test_redirect_model.py`** (AC1) — `Redirect.objects.create(old_path, new_path)` → is_active default True; `__str__`==`"old → new"`; old_path unique (drugi isti → IntegrityError, koristi `pytest.raises(IntegrityError)` + `transaction.atomic`); Redirect NIJE u modeltranslation registry (nema `old_path_sr` atribut).
- **`test_redirect_open_redirect.py`** (AC5 — SECURITY LOCK) — open-redirect bypass vektori + self-loop + enforcement-na-write:
  - `Redirect(old_path="/sr/x/", new_path="https://evil.com").full_clean()` → `pytest.raises(ValidationError)`; `new_path="//evil.com"` (scheme-relative) → ValidationError; `new_path="http://x.com"` → ValidationError; `new_path="ftp://x"` → ValidationError; `new_path="/\evil.com"` (**backslash bypass**) → ValidationError; `new_path="javascript:alert(1)"` → ValidationError; `new_path="/sr/ok/"` (site-internal) → NO error.
  - **Self-loop:** `Redirect(old_path="/sr/x/", new_path="/sr/x/").full_clean()` → ValidationError.
  - **old_path leading-slash:** `Redirect(old_path="sr/stara/", new_path="/sr/nova/").full_clean()` → ValidationError na `old_path` (sprečava tiho-mrtvo pravilo zbog admin typo bez „/").
  - **Enforcement nije admin-only (PROVES save() guard):** `Redirect.objects.create(old_path="/sr/x/", new_path="//evil.com")` → `pytest.raises(ValidationError)` (programski `.create()`/`.save()` zaobilazi admin formu ali NE zaobilazi guard jer `save()` zove `full_clean()`).
  - (Open-redirect guard — SM-D2/SEO4-2; koristi `url_has_allowed_host_and_scheme`, ne ručni startswith.)
- **`test_redirect_middleware.py`** (AC2/AC4/AC6/AC7) —
  - aktivno `/sr/stara/`→`/sr/nova/`: `client.get("/sr/stara/")` → `response.status_code == 301`; `response["Location"] == "/sr/nova/"`.
  - is_active=False → `client.get(...)` status != 301 (passthrough — AC4); pa aktiviraj → 301.
  - no-match path → status != 301.
  - admin path: pravilo `old_path="/sr/admin/secret/"` postoji → `client.get("/sr/admin/secret/")` NIJE redirektovan našim middleware-om (admin skip — AC2/SM-D3; možda 302-login ili 200 admin, ALI NE 301-na-new_path).
  - **forward-safe admin slug (CRITICAL-2 LOCK):** pravilo `old_path="/sr/admin-coric/secret/"` → `client.get("/sr/admin-coric/secret/")` NIJE redirektovan našim middleware-om (skip pokriva i budući Epic 8 `admin-coric` slug, ne samo tekući `admin`; lock-uje da skip NIJE krhki `'/admin/'` substring koji bi se lomio na slug-promenu).
  - static skip: `CaptureQueriesContext` filtriran na `seo_redirect` tabelu → `/static/...` pravi ZERO Redirect-upita (AC7; meri SAMO Redirect lookup — NE bare `assertNumQueries(0)` na ceo request).
  - i18n: `/hu/stara/` (samo `/sr/stara/` rule postoji) → NIJE 301 (AC6/SM-D7).
- **`test_redirect_middleware_order.py`** (AC2/SM-D1 — ORDER LOCK) — `settings.MIDDLEWARE.index("apps.seo.middleware.RedirectMiddleware") < settings.MIDDLEWARE.index("django.middleware.locale.LocaleMiddleware")`. (Premeštanje POSLE Locale → RED.)
- **`test_redirect_admin.py`** (AC3) — `admin.site.is_registered(Redirect)`; RedirectAdmin.list_display/list_filter/search_fields konfigurisani; superuser changelist GET 200; add form POST sa `new_path="https://evil.com"` → form invalid (open-redirect kroz admin — AC5); validan POST → save + redirect na changelist.
- **`test_redirect_migration.py`** (AC1) — `makemigrations --check --dry-run` exit 0 („No changes detected"); tabela `seo_redirect` postoji posle migrate (pytest-django auto-apply); kolone old_path/new_path/is_active/created_at/updated_at prisutne.
- **Regression:** ceo `apps/seo/tests/` (6-1 SeoMeta/seo_head + 6-2 sitemap + 6-3 robots/OG) MORA ostati GREEN (6.4 SAMO dodaje Redirect — ne dira SeoMeta/sitemaps/views/templatetags). `makemigrations --check` clean (0002 committed). **Middleware blast-radius:** sa praznom Redirect tabelom, full home/detail render GREEN (no-match passthrough, +1 upit, NE 500/loop — Task 7.4).
- **Manualni QA (NE-automated):** runserver → admin kreiraj Redirect → GET stari URL u browser-u → Network tab status 301 + Location header → potvrdi da završi na novom URL-u. Test open-redirect: pokušaj uneti `https://evil.com` u admin new_path → potvrdi form error.

### TEA napomene za pisanje testova

- **Middleware end-to-end:** koristi Django test `client.get(path)` (prolazi kroz CEO middleware lanac, uključujući RedirectMiddleware PRE Locale). `response.status_code == 301` + `response["Location"]`. NE `RequestFactory` za end-to-end (RequestFactory NE prolazi middleware) — RequestFactory SAMO za izolovan model/clean test.
- **Order-lock test:** `from django.conf import settings` + `settings.MIDDLEWARE` je lista stringova; `.index(...)` poredi pozicije. Ovo je najjeftiniji a najvredniji test (zaključava SM-D1 — glavnu odluku).
- **Open-redirect:** dve provere — (1) `Redirect(...).full_clean()` → `pytest.raises(ValidationError)` za svaki bypass-vektor (apsolutni `http(s)://`, scheme-relative `//`, **backslash `/\`**, `javascript:`); validan `/internal/` prolazi; (2) **enforcement-na-write:** `Redirect.objects.create(...invalid...)` / `r.save()` → `pytest.raises(ValidationError)` (dokazuje da `save()` override zove `full_clean()` — guard radi i van admin forme; SEO4-2). Plus self-loop: `old_path == new_path` → ValidationError. NB: guard koristi `url_has_allowed_host_and_scheme(url=new_path, allowed_hosts=None)`, NE ručni `startswith`.
- **admin-skip test (CRITICAL-2 — zaključava OBA slug-a):** kreiraj pravilo čiji old_path POČINJE sa `/sr/admin/` → GET tog path-a → potvrdi da NAŠ middleware NE vraća 301-na-new_path (admin može vratiti 302-na-login ili 200 — ključno je da NIJE naš 301 redirect; ili asertuj `response["Location"]` NIJE rule.new_path). **DODATNO obavezno:** ponovi sa `old_path="/sr/admin-coric/secret/"` → GET → NIJE naš 301 (forward-safe: lock-uje da skip pokriva i budući Epic 8 slug; sprečava silent regress kad se admin preimenuje). Oba testa zajedno dokazuju da skip NIJE krhki `'/admin/'` substring (taj bi propustio `admin-coric`).
- **Query-budget perf (AC7) — OBAVEZNO `CaptureQueriesContext` filtriran na `seo_redirect`, NE bare `assertNumQueries(0)`:** za `/static/x` ILI admin path → Redirect lookup se NE izvršava (skip grana). Meri kroz `django.test.utils.CaptureQueriesContext(connection)` pa filtriraj `ctx.captured_queries` na one čiji `sql` pominje `seo_redirect` (Redirect tabela) → asertuj **0** Redirect-upita za skip-ovan path, **1** za normalan path. **NE** `assertNumQueries(0)` na ceo `client.get()` — taj broji SVE upite (session load, auth, contenttype, CSP/contentsecuritypolicy, itd.) i FAIL-uje iako Redirect lookup nije pokrenut; skip-budget se odnosi ISKLJUČIVO na Redirect model. (Primer: `with CaptureQueriesContext(connection) as ctx: client.get("/static/x"); redirect_q = [q for q in ctx.captured_queries if "seo_redirect" in q["sql"]]; assert len(redirect_q) == 0`.)
- **is_active toggle:** kreiraj is_active=False → GET → ne-301; `redirect.is_active=True; redirect.save()` → GET → 301. Dokazuje da middleware filtrira is_active (SM-D4).
- **Migracija:** `from django.core.management import call_command`; `call_command("makemigrations", "seo", "--check", "--dry-run")` ne sme raise SystemExit(1) (znači sync). pytest-django već primenjuje migracije na test DB (tabela postoji).

## Reference

- **epics.md:954-965** — Story 6.4 ACs (Redirect model old_path/new_path/created_at/is_active + RedirectMiddleware; registruj middleware ranije od LocaleMiddleware; pristup starom path-u → HTTP 301 sa novim Location; middleware NE procesira admin URL-ove — epics:964 kaže `/admin-coric/` ALI stvarni registrovani slug je `admin/` (config/urls.py:42); 6.4 skip je forward-safe za OBA slug-a, SM-D3; admin listuj/dodaj/izmeni/deaktiviraj).
- **epics.md:967+** — Story 6.5 (i18n fallback ⓘ tooltip) — granica; 6.4 NE dodaje i18n marker.
- **epics.md:980+** — Story 6.6 (hreflang HTML tagovi + locale-aware slug) — granica; 6.4 NE dodaje hreflang.
- **config/settings/base.py:57-69** — `MIDDLEWARE` lista. `SessionMiddleware`(:60), `LocaleMiddleware`(:61), `CommonMiddleware`(:62). 6.4 dodaje `RedirectMiddleware` IZMEĐU :60 i :61 (PRE Locale — SM-D1). Whitenoise(:59)/Security(:58) OSTAJU PRE Session; Csrf/Auth/Messages/XFrame/Htmx(:67)/LocaleSwitcher(:68) OSTAJU POSLE.
- **config/urls.py:42** — `path("admin/", admin.site.urls)` POD `i18n_patterns` → stvarni admin path `/sr/admin/` (NE `/admin-coric/` iz project-context/epics:964 — taj slug NIJE primenjen; Epic 8 8-1). RedirectMiddleware admin-skip je forward-safe segment-match (regex `^/[a-z]{2}/admin(-coric)?/` ili `reverse('admin:index')`-derivacija) koji pokriva i tekući `admin/` i budući `admin-coric/` (SM-D3/SEO4-4) — NE krhki `'/admin/' in path` substring. config/urls.py NEMA prefix bloka koji 6.4 dira (middleware-driven, ne URL-driven).
- **apps/core/models.py:15-22** — `TimestampedModel` (abstract; `created_at` auto_now_add + `updated_at` auto_now). `Redirect(TimestampedModel)` → epics:961 `created_at` pokriven + updated_at bonus (mirror 6-1 `SeoMeta(TimestampedModel)`).
- **apps/seo/models.py:24-62** — `SeoMeta(TimestampedModel)` (6-1) — OBRAZAC za `Redirect` (TimestampedModel base, Meta verbose_name srpski-dijakritika, `__str__`, db_index na lookup polja). 6.4 dodaje Redirect klasu u ISTI fajl (SeoMeta netaknut).
- **apps/seo/admin.py:1-80** — 6-1 admin (SeoMetaInline + SeoWarningAdminMixin). 6.4 dodaje samostalan `@admin.register(Redirect) RedirectAdmin` (NE inline; NE koristi SeoWarningAdminMixin). list_display/list_filter/search_fields (project-context:200 admin obrazac).
- **apps/seo/views.py** (6-3) — robots_txt; **6.4 NE dira** (dodaje middleware.py, ne views.py — SEO3/6-3 SM-D9 forward-note „6.4 dodaje middleware.py, NE dira views.py").
- **apps/seo/translation.py:18-20** — registruje SAMO SeoMeta(meta_title/meta_description). **6.4 NE dira** (Redirect NIJE translatable — ASCII path; SM-D6/SEO4-5).
- **apps/seo/apps.py** — SeoConfig (name="apps.seo"). Redirect/middleware se auto-discover-uju (models import; middleware kroz settings string path).
- **6-1-seometa-model-per-page-admin.md** — SeoMeta(TimestampedModel) model obrazac + admin registracija + per-app tests/ layout + migrations discipline (manual review) — 6.4 mirror za Redirect.
- **6-3-robots-txt-open-graph-twitter-card-meta.md** (SM-D9, SEO3-12) — „6.4 (Redirect 301 model + middleware) je zaseban; apps/seo/views.py je PRVI seo view — 6.4 dodaje middleware.py, NE dira views.py"; `*/admin/` glob obrazac (admin pod i18n /sr/admin/) → RedirectMiddleware admin-skip mirror.
- **project-context.md:218-228** — Migrations discipline (makemigrations → manual review → migrate --plan → atomic commit) za 0002_redirect (Task 2). **:197** — admin slug `/admin-coric/` (PREPORUKA, NIJE primenjena — stvarni registrovani slug je `admin/`; 6.4 admin-skip je forward-safe za OBA slug-a — SM-D3, OQ-5 RESOLVED). **:594** — NIKAD direct User import (Redirect NEMA User FK — N/A, ali napomena). **:355-360** — YAGNI/no-premature-abstraction (301-only, exact-match, no-cache v1).
