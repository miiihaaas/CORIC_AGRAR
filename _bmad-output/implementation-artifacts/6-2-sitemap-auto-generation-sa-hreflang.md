---
story_id: "6.2"
story-key: 6-2-sitemap-auto-generation-sa-hreflang
title: Sitemap Auto-generation sa Hreflang
status: ready-for-dev
epic: 6
epic_num: 6
epic_title: SEO & Discoverability
module: seo
created: 2026-06-05
last_modified: 2026-06-05
complexity: M
author: Mihas (SM autonomous; DRUGA story Epic 6 — SEO & Discoverability. KONZUMIRA 6-1 SeoMeta GFK + sve postojeće content modele. ČIST READ-ONLY agregator: NOVI `apps/seo/sitemaps.py` sa Django `Sitemap` podklasama za Product/Brand/Subcategory/BlogPost(Post) + statički PageSitemap (home/about/contact). **SeriesSitemap EKSPLICITNO IZOSTAVLJEN (SM-D6/CRIT-2)** — `Series.get_absolute_url()` referencira `brands:series_detail` rutu koja NE POSTOJI u brands/urls.py (verifikovano grep-om project-wide: jedini hit je sam model:231) → poziv RAISE-uje `NoReverseMatch` → uključen SeriesSitemap bi oborio CEO /sitemap.xml u HTTP 500 (Django `Sitemap.location()` default = get_absolute_url BEZ try/except). Series trenutno NEMA standalone javnu URL → ne MOŽE biti u sitemap-u; ista logika izostavlja Category (`brands:category_traktori`/`category_mehanizacija` takođe ne postoje). Dakle 5 Sitemap klasa, NE 6 — divergencija od epics.md:934 (koja lista Series) je OPRAVDANA: render-safe > doslovnost; re-uključiti kad/ako 2.x doda series detail rutu. HREFLANG kroz Django built-in `i18n=True`+`alternates=True` (NE hand-rolled XML — SM-D1). DRAFT-NOT-LEAKED security boundary preko 5 javnih predikata (SM-D3): Product is_published=True, Brand is_coming_soon=False, Subcategory uvek-javna (NEMA visibility flag — verifikovano live), Post.published (status=published AND published_at<=now), Page (home/about/contact). `exclude_from_sitemap=True` izostavljen kroz GFK exclusion-set (SeoMeta filter na content_type+flag → values_list object_id; NEMA join jer NEMA GenericRelation — OQ-4/ARCH-2 iz 6-1; SM-D4). `sitemap.xml` registrovan VAN `i18n_patterns` (NIJE locale-prefiksovan; jedan /sitemap.xml lista sve locale alternate — SM-D2 mirror i18n/setlang/ no-prefix blok). NEMA `django.contrib.sites` / NEMA SITE_ID → Django sitemap koristi `RequestSite` (domen iz request Host header-a; ALLOWED_HOSTS ograničava — SM-D2). 0 MIGRACIJA (consumes 6-1 + postojeći modeli; NEMA model promene). FORWARD 6.3: robots.txt referencira /sitemap.xml lokaciju — 6.2 samo treba da sitemap POSTOJI na stabilnoj URL-i. RISK TIER: MEDIUM — 0 migracija + Django-sitemaps-framework-backed (battle-tested), ALI draft-not-leaked preko content tipova = security boundary + hreflang i18n correctness + GFK exclude_from_sitemap integracija + no-sites RequestSite Host handling + get_absolute_url NoReverseMatch render hazard (CRIT-2 — Series/Category izostavljeni).)
depends_on:
  - 6-1-seometa-model-per-page-admin                          # SeoMeta GFK model (content_type+object_id) + exclude_from_sitemap BooleanField (db_index); ContentType.get_for_model exclusion-set pattern (ARCH-2 forward-note: NEMA GenericRelation → exclude preko object_id values_list); apps.seo app već registrovan u INSTALLED_APPS
  - 1-4-i18n-setup-sa-locale-url-routing-i-switcher          # i18n_patterns(prefix_default_language=True) — sitemap MORA biti VAN; LANGUAGES [sr,hu,en] izvor hreflang alternate-a; reverse()-based get_absolute_url per-lang activation
  - 2-1-brand-series-category-subcategory-modeli             # Brand (is_coming_soon predikat); Subcategory (uvek-javna — NEMA visibility flag; get_absolute_url reverse → brands:subcategory_listing_l* ruta POSTOJI 2.11); Series/Category get_absolute_url RAISE NoReverseMatch (rute ne postoje) → IZOSTAVLJENI iz sitemap-a (CRIT-2/SM-D6); updated_at = lastmod izvor
  - 2-2-product-i-related-modeli                             # Product is_published predikat (default False → public=True); get_absolute_url; TimestampedModel.updated_at
  - 5-1-blogpost-category-tag-modeli-admin-stub              # Post.published manager (status=published AND published_at<=now); get_absolute_url; TimestampedModel.updated_at
  - 5-2-blog-index-strana-sa-paginacijom-filter              # blog:detail URL registrovan (Post.get_absolute_url više NE raise NoReverseMatch); products:detail/brands:detail takođe wired (2-6/2-7)
  - 3-2-o-nama-strana                                        # pages:about static view name
  - 3-3-kontakt-strana                                       # pages:contact static view name
---

# Story 6.2: Sitemap Auto-generation sa Hreflang

Status: ready-for-dev

## Opis

As a **search engine bot (Googlebot/Bingbot)**,

I want **dinamičan `sitemap.xml` koji lista SVE objavljene sadržajne tipove sa hreflang alternate oznakama za sva 3 jezika (sr/hu/en)**,

so that **pretraživači indeksiraju svaki javni Product/Brand/Subcategory/blog Post + statičke strane (home/o-nama/kontakt) u sve 3 jezičke varijante — bez da ijedan nacrt (draft/coming-soon/unpublished) ili admin-isključen (`exclude_from_sitemap=True`) objekat iscuri u indeks**.

Ovo je **DRUGA story Epic 6 (SEO & Discoverability)** i čist **READ-ONLY AGREGATOR**: KONZUMIRA `SeoMeta` model iz 6-1 (za `exclude_from_sitemap` filter) + javne content modele (Product/Brand/Subcategory/Post). **NEMA NIJEDNE MODEL PROMENE, NIJEDNE MIGRACIJE.** Isporučuje JEDAN novi fajl (`apps/seo/sitemaps.py`) + 1 INSTALLED_APPS EDIT (`django.contrib.sitemaps`) + 1 `config/urls.py` EDIT (registracija `sitemap.xml` VAN `i18n_patterns`).

> **CRIT-2 (render-safe scope) — Series i Category IZOSTAVLJENI:** `Series.get_absolute_url()` → `reverse("brands:series_detail", ...)` i `Category.get_absolute_url()` → `reverse("brands:category_traktori"/"category_mehanizacija", ...)` referenciraju URL imena koja **NE POSTOJE** u `apps/brands/urls.py` (verifikovano grep-om project-wide — jedini hit je sam model). Django `Sitemap` poziva default `location(item)` = `item.get_absolute_url()` BEZ try/except → `NoReverseMatch` bi se propagirao i oborio CEO `/sitemap.xml` u **HTTP 500**. Series/Category trenutno NEMAJU standalone javnu detail URL → ne mogu biti u sitemap-u uopšte. Zato 6.2 isporučuje **5 Sitemap klasa** (Product/Brand/Subcategory/BlogPost/Page), NE 6. Ovo svesno divergira od epics.md:934 (koja lista „Series, Subcategory"): render-bezbednost + tačnost > doslovno praćenje liste. Series re-ulazi u sitemap čim 2.x doda `brands:series_detail` rutu (vidi OQ-6).

### IN SCOPE (šta ova story isporučuje)

1. **INSTALLED_APPS: dodaj `"django.contrib.sitemaps"`** (AC1) — Django sitemaps framework (template + view). **NE `django.contrib.sites`** (SM-D2 — RequestSite fallback iz request Host-a; NEMA SITE_ID, NEMA sites migracije).
2. **NOVI `apps/seo/sitemaps.py`** (AC1) — Django `Sitemap` podklase: `ProductSitemap`, `BrandSitemap`, `SubcategorySitemap`, `BlogPostSitemap` (za Post) + statički `PageSitemap` (home/about/contact). **5 klasa** (NEMA `SeriesSitemap`/`CategorySitemap` — CRIT-2/SM-D6). **SVE sa `i18n = True` + `alternates = True`** (hreflang per locale — SM-D1). Plus `sitemaps` dict (registry) za `config/urls.py`.
3. **DRAFT-NOT-LEAKED predikati** (AC4, security boundary, SM-D3) — svaka `items()` vraća SAMO javne objekte: `Product.objects.filter(is_published=True)`, `Brand.objects.filter(is_coming_soon=False)`, `Subcategory.objects.all()` (NEMA visibility flag — uvek javna), `Post.published.all()` (status=published AND published_at<=now).
4. **`exclude_from_sitemap` exclusion-set helper** (AC6, SM-D4) — deljena funkcija u `sitemaps.py`: za dati model vrati skup `object_id`-jeva sa `exclude_from_sitemap=True` iz `SeoMeta` (preko `ContentType.get_for_model`). `items()` = `public_qs.exclude(pk__in=excluded_set)`. **JEDAN query po sitemap klasi** (NE N+1). GFK — NEMA join (ARCH-2/OQ-4 iz 6-1).
5. **HREFLANG kroz Django built-in** (AC5, SM-D1) — `i18n=True` + `alternates=True` → Django automatski emituje `<xhtml:link rel="alternate" hreflang="sr|hu|en">` za SVAKI jezik iz `LANGUAGES`, po URL stavci. **NE hand-roll XML.** `x_default` defer (OQ-2 — AC traži samo sr|hu|en).
6. **`lastmod()` = `obj.updated_at`** (AC9, SM-D7) — za sve model sitemap-e (Product/Post kroz TimestampedModel; Brand/Subcategory inline `updated_at`; svi verifikovani). PageSitemap (statički) NEMA lastmod (OQ-4 — omit).
7. **`config/urls.py` EDIT: registruj `sitemap.xml` VAN `i18n_patterns`** (AC2, AC7, SM-D2) — `path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="django.contrib.sitemaps.views.sitemap")` u no-prefix `urlpatterns` bloku (mirror `path("i18n/setlang/", ...)`). **NIJE locale-prefiksovan** — jedan `/sitemap.xml` lista sve locale alternate.

### OUT OF SCOPE (eksplicitno — granice)

- **`robots.txt`** = **Story 6.3** (`apps/seo/views.py:robots_txt` koji NAVODI `sitemap.xml` lokaciju). 6.2 SAMO obezbeđuje da `/sitemap.xml` POSTOJI na stabilnoj URL-i (SM-D8 forward). NEMA `apps/seo/views.py` u 6.2.
- **Open Graph / Twitter Card meta** = **Story 6.3** (`base.html` OG tagovi). 6.2 NE dira template-e (`og:image` render je 6-1 + pun OG je 6.3).
- **`django.contrib.sites` + SITE_ID + sites migracija** = **NE** (SM-D2). Django sitemap view koristi `RequestSite` (domen iz request Host header-a) kad `sites` NIJE instaliran — to je IDIOMATSKI fallback, NE bug. NEMA `SITE_ID` settinga, NEMA sites tabele/migracije. Apsolutne URL-e u sitemap-u derivira request Host (`ALLOWED_HOSTS` ga ograničava u prod-u).
- **Hand-rolled hreflang XML / custom sitemap template** = **NE** (SM-D1). Django built-in `i18n=True`+`alternates=True` generiše schema-validan `<xhtml:link rel="alternate">` markup. Custom template = error-prone reinvencija.
- **`SeriesSitemap` (brands.Series)** = **NE** (CRIT-2/SM-D6 — `Series.get_absolute_url()` → `reverse("brands:series_detail")` RAISE-uje `NoReverseMatch`; ruta ne postoji u brands/urls.py). Uključen SeriesSitemap bi oborio CEO `/sitemap.xml` u 500. Iako epics.md:934 lista Series — render-bezbednost je preča. Re-uključiti čim 2.x doda series detail rutu (OQ-6).
- **`CategorySitemap` (brands.Category)** = **NE** (CRIT-2/SM-D6 — `Category.get_absolute_url()` → `reverse("brands:category_traktori"/"category_mehanizacija")` RAISE-uje `NoReverseMatch`; rute ne postoje). Isti 500-render hazard kao Series. Category NIJE ni naveden u epics.md:934. Category JESTE dobio inline SeoMeta u 6-1 (C-F) ali NEMA javnu detail rutu → ne kvalifikuje se za sitemap. Dokumentovano + OQ-1.
- **`changefreq` / `priority`** = **NE postavljati** (SM-D7 / OQ-3 — AC ne traži; izostavljanje je validno; defaulti = Google ih ionako tretira kao savetodavne/ignoriše). NE over-engineer.
- **`x_default` hreflang** = **DEFER** (OQ-2 — Django 5.2 ima `x_default` atribut, ali AC937 traži SAMO sr|hu|en alternate. Dodavanje x-default je low-risk poboljšanje ali van AC-a; defer za 6.x polish ili dodaj ako TEA/dev odluči — NE-blocking).
- **Sitemap index (više `<sitemap>` fajlova)** = **NE** (single `sitemap.xml` urlset je dovoljan za v1 volumen; Django auto-paginira na 50k URL-ova po sekciji ako ikad zatreba — bez ručne intervencije). NEMA `index()` view-a u 6.2.
- **Caching sitemap-a** = **NE** (YAGNI; sitemap query je par desetina objekata; cache je Epic 9 perf odluka ako ikad zatreba).
- **`PageSitemap` za servis/rezervne-delove** = **NE** (OQ-4 boundary — epics „Page" sitemap = home/about/contact public marketing strane; service/parts su lead-gen forme, NE primarni indeks targeti za v1; mogu se dodati u 6.x). 6.2 PageSitemap = TAČNO home/about/contact (`pages:home`/`pages:about`/`pages:contact`).
- **Defensive validacija / try-except oko cele sitemap items()** = **NE** (project-context.md:358 — Django sitemap framework hendluje render; NE wrap-uj u defensive boilerplate).

### Princip

Jedan READ-ONLY agregator fajl (`apps/seo/sitemaps.py`) sa 5 Django `Sitemap` podklasa (4 model — Product/Brand/Subcategory/BlogPost + 1 statički Page) + deljen exclusion-set helper + `sitemaps` registry dict. **Series/Category izostavljeni — get_absolute_url RAISE NoReverseMatch (rute ne postoje) → 500-render hazard; CRIT-2/SM-D6.** HREFLANG kroz Django built-in `i18n=True`+`alternates=True` (NIKAD hand-rolled XML — SM-D1). DRAFT-NOT-LEAKED preko 5 eksplicitnih javnih predikata (security boundary — SM-D3). `exclude_from_sitemap` preko GFK exclusion-set (jedan query/klasa, NEMA join — SM-D4). `lastmod`=`updated_at` (model sitemap-i; PageSitemap omit). NO-SITES → RequestSite iz request Host-a (SM-D2). `sitemap.xml` registrovan VAN `i18n_patterns` (NIJE locale-prefiksovan — SM-D2). 0 migracija (consumes 6-1 + postojeći modeli). NEMA novog dep-a (`django.contrib.sitemaps` je Django core). NEMA defensive boilerplate-a. NEMA premature abstrakcije (NEMA sitemap index, NEMA caching, NEMA changefreq/priority).

### Strukturna arhitektura — repository delta

**1 NOVI fajl (`apps/seo/sitemaps.py`) + 2 EDIT (INSTALLED_APPS + config/urls.py) + 0 MIGRACIJA + 0 model promene + 0 template-strana + 0 CSS/JS.**

| Path | Tip | Razlog |
|---|---|---|
| `apps/seo/sitemaps.py` | NOVO | **5** `Sitemap` podklasa (`ProductSitemap`/`BrandSitemap`/`SubcategorySitemap`/`BlogPostSitemap`/`PageSitemap` — **NEMA Series/Category**, CRIT-2) + `_excluded_pks(model)` helper (GFK exclusion-set) + `sitemaps` registry dict. SVE model-sitemap-e: `i18n=True`, `alternates=True`, `items()`=javni-qs MINUS excluded, `lastmod()`=`obj.updated_at`. `PageSitemap`: `i18n=True`, `alternates=True`, statički `items()`=["pages:home","pages:about","pages:contact"], `location()`=`reverse(item)`, NEMA lastmod. (vidi AC1–AC9.) |
| `config/settings/base.py` | EDIT | Dodaj `"django.contrib.sitemaps"` u `INSTALLED_APPS` (Django core contrib; redosled — može POSLE `django.contrib.staticfiles`/contrib blok ili pre `apps.*`; bezbedno bilo gde u contrib grupi). **NE `django.contrib.sites`** (SM-D2). |
| `config/urls.py` | EDIT | `from django.contrib.sitemaps.views import sitemap` + `from apps.seo.sitemaps import sitemaps` → `path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="django.contrib.sitemaps.views.sitemap")` dodat u NO-PREFIX `urlpatterns` blok (gde je `i18n/setlang/`) — **VAN `i18n_patterns`** (SM-D2/AC7). |
| `apps/seo/tests/*` | NOVO (TEA) | RED-phase testovi (vidi Testing). Dev NE piše testove. Mirror apps/seo/tests + apps/blog/tests layout. |
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | EDIT | `6-2-sitemap-auto-generation-sa-hreflang` → `ready-for-dev`. SM handoff tracking (NIJE deliverable). |

**NETAKNUTO (regression guards):** `apps/seo/models.py` (SeoMeta — NE menja se; 6.2 SAMO čita `exclude_from_sitemap`); SVE postojeće migracije (`makemigrations --check --dry-run` mora reći „No changes detected" — 6.2 NE dodaje nijednu migraciju); `apps/products/*`, `apps/brands/*`, `apps/blog/*`, `apps/pages/*` modeli (čisto čitanje — NEMA polja/predikat promene); `base.html` + svi template-i (OG je 6.3); `apps/seo/views.py` (NE postoji — robots je 6.3); `pyproject.toml` (`django.contrib.sitemaps` je Django core — NEMA novog dep-a); sve CSS/JS; `i18n_patterns` blok (sitemap.xml ide u NO-PREFIX blok — NE menja postojeće prefiksovane rute).

## Kriterijumi prihvatanja

**AC1 — `django.contrib.sitemaps` u INSTALLED_APPS + `apps/seo/sitemaps.py` sa 5 `Sitemap` podklasa + `sitemaps` registry (SM-D1)**

- **Given** SeoMeta iz 6-1; postojeći content modeli; LANGUAGES [sr,hu,en]
- **When** dodam `"django.contrib.sitemaps"` u INSTALLED_APPS i kreiram `apps/seo/sitemaps.py`
- **Then**:
  - `"django.contrib.sitemaps"` je u `INSTALLED_APPS` (config/settings/base.py); **`"django.contrib.sites"` NIJE** (SM-D2)
  - `apps/seo/sitemaps.py` definiše TAČNO 5 podklasa: `ProductSitemap`, `BrandSitemap`, `SubcategorySitemap`, `BlogPostSitemap`, `PageSitemap` (**NEMA `SeriesSitemap` ni `CategorySitemap`** — CRIT-2/SM-D6: njihov get_absolute_url RAISE NoReverseMatch)
  - Svaka model-sitemap podklasa (Product/Brand/Subcategory/BlogPost) postavlja `i18n = True` i `alternates = True` (klasni atributi)
  - `PageSitemap` takođe ima `i18n = True` + `alternates = True`
  - `sitemaps` modul-level dict postoji: `{"products": ProductSitemap, "brands": BrandSitemap, "subcategories": SubcategorySitemap, "blog": BlogPostSitemap, "pages": PageSitemap}` (5 sekcijskih ključeva — koriste se u `config/urls.py`)
  - `uv run python manage.py check` exit 0
- **And** `apps/seo/sitemaps.py` importuje content modele (`Product`, `Brand`, `Subcategory`, `Post`) + `SeoMeta` + `ContentType` + `Sitemap` (`django.contrib.sitemaps.Sitemap`) + `reverse` — bez kružnog import-a (sitemaps modul se importuje LAZY kroz urls.py, NE u models/apps.ready)

**AC2 — `/sitemap.xml` vraća HTTP 200 validan XML (SM-D2)**

- **Given** AC1; `config/urls.py` registruje sitemap (AC7)
- **When** GET `/sitemap.xml` (bez locale prefiksa)
- **Then**:
  - HTTP 200; `Content-Type` sadrži `application/xml` (Django sitemap view default `text/xml` / `application/xml`)
  - Telo je well-formed XML (parsabilno kroz `xml.etree.ElementTree.fromstring` bez `ParseError`)
  - Root element je `<urlset>` u namespace-u `http://www.sitemaps.org/schemas/sitemap/0.9` (AC8)
  - Sadrži `xmlns:xhtml="http://www.w3.org/1999/xhtml"` deklaraciju (za `<xhtml:link>` alternate — AC5/AC8)
  - Sadrži bar jedan `<url><loc>` element (sa seed podacima)
- **And** apsolutne URL-e u `<loc>` derivira request Host (RequestSite — SM-D2; npr. `http://testserver/sr/...` u test client-u)

**AC3 — Sitemap sadrži SAV javni sadržaj (Product/Brand/Subcategory/Post + statičke strane) (SM-D3)**

- **Given** AC2; seed: bar 1 javni Product (is_published=True), 1 javni Brand (is_coming_soon=False), 1 Subcategory, 1 objavljen Post (published)
- **When** parsiram `/sitemap.xml`
- **Then** `<loc>` skup sadrži:
  - `get_absolute_url()` javnog Product-a (locale-prefiksovan, npr. `/sr/...`)
  - `get_absolute_url()` javnog Brand-a
  - `get_absolute_url()` Subcategory-ja (`brands:subcategory_listing_l*` — ruta POSTOJI 2.11)
  - `get_absolute_url()` objavljenog Post-a (`/sr/blog/<slug>/`)
  - `reverse("pages:home")`, `reverse("pages:about")`, `reverse("pages:contact")` (statičke strane kroz PageSitemap)
  - **(NE sadrži Series ni Category** — nemaju javnu detail rutu; CRIT-2)
- **And** jer je `i18n=True`, svaka stavka se pojavljuje za SVAKI jezik (sr/hu/en `<loc>` + cross-reference alternate-i — AC5); test asertuje prisustvo BAR sr-prefiksovane `<loc>` po tipu

**AC4 — DRAFT-NOT-LEAKED: nacrt/coming-soon/unpublished se NE pojavljuje (security boundary, SM-D3)**

- **Given** AC3 + seed: 1 unpublished Product (is_published=False), 1 coming-soon Brand (is_coming_soon=True), 1 draft Post (status=draft), 1 PUBLISHED Post sa `published_at` u BUDUĆNOSTI (scheduled)
- **When** parsiram `/sitemap.xml`
- **Then** NIJEDAN od ovih se NE pojavljuje u `<loc>` skupu:
  - unpublished Product (`get_absolute_url` NIJE u sitemap-u)
  - coming-soon Brand
  - draft Post
  - scheduled (buduća published_at) Post (jer `Post.published` filtrira `published_at__lte=now`)
- **And** predikati su EKSPLICITNI po tipu (5 predikata — SM-D3):
  - `ProductSitemap.items()` baza = `Product.objects.filter(is_published=True)`
  - `BrandSitemap.items()` baza = `Brand.objects.filter(is_coming_soon=False)`
  - `SubcategorySitemap.items()` baza = `Subcategory.objects.all()` (NEMA visibility flag — uvek javna; get_absolute_url ruta POSTOJI)
  - `BlogPostSitemap.items()` baza = `Post.published.all()` (status=published AND published_at<=now)
  - PageSitemap = statičke javne strane (home/about/contact — uvek javne)
  - **(Series/Category NEMAJU sitemap klasu** — CRIT-2; njihova vidljivost je svejedno nebitna jer nemaju javnu detail URL)
- **And** ovo je SECURITY BOUNDARY — test je „draft-not-leaked lock" (jedan unpublished objekat u sitemap-u = curenje nacrta u Google indeks)

**AC5 — Svaka URL stavka ima hreflang alternate sr/hu/en (`<xhtml:link rel="alternate">`) (SM-D1)**

- **Given** AC2; LANGUAGES [sr,hu,en]; `i18n=True`+`alternates=True` na svim sitemap klasama
- **When** parsiram `/sitemap.xml` i ispitam `<url>` elemente
- **Then**:
  - Svaki `<url>` element sadrži `<xhtml:link rel="alternate" hreflang="sr" href="...">`, `<xhtml:link rel="alternate" hreflang="hu" href="...">`, `<xhtml:link rel="alternate" hreflang="en" href="...">` (sva 3 jezika — Django auto-emit iz `alternates=True`)
  - `href` u alternate-u je locale-prefiksovana apsolutna URL (npr. `hreflang="hu"` → `/hu/...`)
  - hreflang vrednosti su TAČNO Django `LANGUAGES` kodovi (`sr`/`hu`/`en`)
- **And** ovo je generisano Django built-in-om (`i18n=True`+`alternates=True`), NE hand-rolled XML-om (SM-D1) — test asertuje prisustvo `xhtml:link rel="alternate"` markup-a sa sva 3 hreflang koda
- **And** `<xhtml:link>` koristi `xmlns:xhtml` namespace deklarisan na `<urlset>` (AC8)

**AC6 — Stavke sa `exclude_from_sitemap=True` se NE pojavljuju (GFK exclusion-set, SM-D4)**

- **Given** AC3 + seed: javni Product P1 sa `SeoMeta(content_object=P1, exclude_from_sitemap=True)`; objavljen Post B1 sa `SeoMeta(content_object=B1, exclude_from_sitemap=True)`
- **When** parsiram `/sitemap.xml`
- **Then**:
  - `P1.get_absolute_url()` NIJE u `<loc>` skupu (iako je P1 is_published=True)
  - `B1.get_absolute_url()` NIJE u `<loc>` skupu (iako je B1 published)
  - Drugi javni Product/Post BEZ `exclude_from_sitemap` SU prisutni (exclusion je per-objekat, ne globalan)
- **And** exclusion-set se gradi kroz GFK BEZ join-a (SM-D4, ARCH-2/OQ-4 iz 6-1):
  ```python
  def _excluded_pks(model):
      ct = ContentType.objects.get_for_model(model)
      return set(
          SeoMeta.objects.filter(
              content_type=ct, exclude_from_sitemap=True
          ).values_list("object_id", flat=True)
      )
  ```
  i `items()` = `public_qs.exclude(pk__in=_excluded_pks(Model))`
- **And** **JEDAN query po sitemap klasi** (helper poziva se jednom u `items()`, NE per-objekat — NE N+1). Test može asertovati prisustvo `exclude` u `items()` queryset-u + bihevioralni izostanak P1/B1.

**AC7 — `sitemap.xml` registrovan VAN `i18n_patterns` (NIJE locale-prefiksovan) (SM-D2)**

- **Given** AC1; `config/urls.py` (`i18n_patterns(prefix_default_language=True)` + no-prefix `urlpatterns` blok sa `i18n/setlang/`)
- **When** dodam sitemap rutu u `config/urls.py`
- **Then**:
  - `path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="django.contrib.sitemaps.views.sitemap")` je u NO-PREFIX `urlpatterns` listi (gde je `i18n/setlang/`) — **NE unutar `i18n_patterns(...)`**
  - GET `/sitemap.xml` → 200 (AC2); GET `/sr/sitemap.xml` → 404 (NIJE locale-prefiksovan — sitemap index nije per-locale; jedan /sitemap.xml lista sve locale alternate)
  - `reverse("django.contrib.sitemaps.views.sitemap")` razrešava na `/sitemap.xml` (bez locale prefiksa)
- **And** ovo je IDENTIČAN no-prefix obrazac kao `i18n/setlang/` (SM-D2 mirror)

**AC8 — Sitemap validan po sitemap.org schema (well-formed XML, urlset + xhtml namespace) (SM-D1)**

- **Given** AC2, AC5
- **When** validiram `/sitemap.xml` strukturu
- **Then**:
  - Well-formed XML (parsabilan; AC2)
  - `<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">` (oba namespace-a prisutna)
  - Svaki `<url>` ima TAČNO jedan `<loc>` + (opciono) `<lastmod>` (AC9) + 3×`<xhtml:link rel="alternate">` (AC5)
  - NEMA `<changefreq>`/`<priority>` (SM-D7 — izostavljeni; izostanak je schema-validan)
- **And** struktura je generisana Django sitemaps template-om (`sitemaps/sitemap.xml`) — NE custom — pa je schema-conformance garantovana frameworkom (SM-D1 obrazloženje)
- **And** (opciono manualno) external validator (sitemap.org / Google Search Console) prihvata — to je manualni QA korak, NE automated test (epics.md:939 „testirati sa external validator-om" = manualna verifikacija)

**AC9 — `<lastmod>` prisutan iz `updated_at` (model sitemap-i); PageSitemap bez lastmod (SM-D7)**

- **Given** AC3; model objekti imaju `updated_at` (Product/Post TimestampedModel; Brand/Subcategory inline `updated_at`)
- **When** parsiram `<url>` elemente za model sadržaj
- **Then**:
  - Svaki model `<url>` (Product/Brand/Subcategory/Post) ima `<lastmod>` = ISO-8601 datum iz `obj.updated_at` (Django formatira `lastmod()` povratnu vrednost)
  - `ProductSitemap.lastmod(obj)` / itd. vraća `obj.updated_at` (jedna metoda na deljenoj bazi ili po klasi)
  - **PageSitemap NEMA `lastmod`** (statičke strane — nema `updated_at`; OQ-4 — omit; izostanak `<lastmod>` je schema-validan)
- **And** `lastmod` koristi `updated_at` (NE `created_at`) jer reflektuje poslednju izmenu (Google koristi za re-crawl prioritet)

## Tasks / Subtasks

> **Konvencija:** `[TEA-RED]` = Test Architect piše test PRE implementacije (mora FAIL). `[DEV-GREEN]` = Developer implementira da test prođe. **Dev NIKAD ne piše testove.** **NEMA migracije** (6.2 je 0-migration read-only agregator — `makemigrations --check` mora ostati čist). **NEMA `uv add`** (`django.contrib.sitemaps` je Django core).

- [ ] **Task 1 — INSTALLED_APPS: `django.contrib.sitemaps` (AC1)** `[DEV-GREEN]`
  - [ ] 1.1 Dodaj `"django.contrib.sitemaps"` u `INSTALLED_APPS` (config/settings/base.py) — u Django contrib grupi (npr. POSLE `django.contrib.staticfiles` ili `django.contrib.postgres`). **NE dodaj `django.contrib.sites`** (SM-D2).
  - [ ] 1.2 `uv run python manage.py check` exit 0. `uv run python manage.py makemigrations --check --dry-run` → „No changes detected" (sitemaps NEMA modele → 0 migracija; SM-D potvrda).

- [ ] **Task 2 — exclusion-set helper + ProductSitemap + BrandSitemap (AC1/AC3/AC4/AC6)** `[DEV-GREEN]`
  - [ ] 2.1 Kreiraj `apps/seo/sitemaps.py`. Import: `from django.contrib.sitemaps import Sitemap`, `from django.contrib.contenttypes.models import ContentType`, `from django.urls import reverse`, content modeli (`Product`, `Brand`, `Subcategory`, `Post` — **NE Series/Category**, CRIT-2), `SeoMeta`.
  - [ ] 2.2 `_excluded_pks(model)` helper (SM-D4): `ct = ContentType.objects.get_for_model(model)` → `set(SeoMeta.objects.filter(content_type=ct, exclude_from_sitemap=True).values_list("object_id", flat=True))`. JEDAN query.
  - [ ] 2.3 `ProductSitemap(Sitemap)`: `i18n=True`, `alternates=True`, `def items(self): return Product.objects.filter(is_published=True).exclude(pk__in=_excluded_pks(Product))`, `def lastmod(self, obj): return obj.updated_at`. (`location()` default = `obj.get_absolute_url()` — NE override.)
  - [ ] 2.4 `BrandSitemap(Sitemap)`: isto, baza `Brand.objects.filter(is_coming_soon=False).exclude(...)`, `lastmod`=`updated_at`.

- [ ] **Task 3 — SubcategorySitemap + BlogPostSitemap (AC1/AC3/AC4/AC6)** `[DEV-GREEN]`
  - [ ] 3.1 `SubcategorySitemap(Sitemap)`: `i18n`/`alternates` True, `lastmod`=`updated_at`. **items() MORA koristiti select_related radi N+1 mitigacije (GAP-1):** `Subcategory.objects.select_related("category", "parent", "parent__parent").exclude(pk__in=_excluded_pks(Subcategory))`. Razlog: `Subcategory.get_absolute_url()` poziva `get_ancestors_chain()` (parent-chain traversal) + `self.category.slug`; Django sitemap sa `i18n=True` poziva `get_absolute_url()` PO JEZIKU (3× za sr/hu/en) → bez `select_related` = N+1 na ancestor chain-u po stavci. Volume je nizak ali mitigacija je trivijalna i ispravna. Product/Brand/Post sitemapi NE trebaju `select_related` (njihov `get_absolute_url` je prost `reverse(slug)`). **Zašto je SubcategorySitemap bezbedno uključen (C1):** `Subcategory.get_absolute_url()` referencira SOPSTVENU postojeću rutu porodicu `brands:subcategory_listing_l{1,2,3}` (registrovana u `apps/brands/urls.py` — verifikovano), NE Series/Category rutu. Nema „subcategory-under-coming-soon-Brand curenje" jer Subcategory FK pokazuje na `Category` (NE na `Brand`) — Subcategory-jeva listing URL je uvek validna nezavisno od Brand-ove `is_coming_soon` vidljivosti. (Subcategory NEMA visibility flag — uvek javna; SM-D3.)
  - [ ] 3.2 `BlogPostSitemap(Sitemap)`: isto, baza `Post.published.all().exclude(pk__in=_excluded_pks(Post))`, `lastmod`=`updated_at`. (`Post.published` već filtrira status=published AND published_at<=now — SM-D3.)
  - [ ] 3.3 **NE kreiraj `SeriesSitemap` ni `CategorySitemap`** (CRIT-2/SM-D6): `Series.get_absolute_url()`/`Category.get_absolute_url()` referenciraju nepostojeće rute (`brands:series_detail`/`category_traktori`/`category_mehanizacija`) → `NoReverseMatch` → oboren ceo `/sitemap.xml` (500). Verifikuj grep-om da te rute ne postoje PRE nego što odlučiš da ih dodaš.
  - [ ] 3.4 (DRY opciono) `lastmod` se može deliti kroz mali mixin/base sa `def lastmod(self, obj): return obj.updated_at` — ALI NE over-abstract (svaka klasa može imati svoj `lastmod` ako je čitljivije; Dev bira). `_excluded_pks` MORA biti deljen (jedna funkcija).

- [ ] **Task 4 — PageSitemap (statički home/about/contact) + sitemaps registry (AC1/AC3)** `[DEV-GREEN]`
  - [ ] 4.1 `PageSitemap(Sitemap)`: `i18n=True`, `alternates=True`, `def items(self): return ["pages:home", "pages:about", "pages:contact"]`, `def location(self, item): return reverse(item)`. **NEMA `lastmod`** (statičke strane — OQ-4; SM-D7).
  - [ ] 4.2 `sitemaps` modul-level dict (5 ključeva): `{"products": ProductSitemap, "brands": BrandSitemap, "subcategories": SubcategorySitemap, "blog": BlogPostSitemap, "pages": PageSitemap}`.
  - [ ] 4.3 `uv run python manage.py check` exit 0.

- [ ] **Task 5 — `config/urls.py`: registruj `sitemap.xml` VAN i18n_patterns (AC2/AC7)** `[DEV-GREEN]`
  - [ ] 5.1 `from django.contrib.sitemaps.views import sitemap` + `from apps.seo.sitemaps import sitemaps as sitemaps_dict` (alias da izbegne shadow sa import imenom) na vrhu `config/urls.py`.
  - [ ] 5.2 Dodaj `path("sitemap.xml", sitemap, {"sitemaps": sitemaps_dict}, name="django.contrib.sitemaps.views.sitemap")` u NO-PREFIX `urlpatterns` listu (gde je `i18n/setlang/`) — **NE unutar `i18n_patterns(...)`** (SM-D2/AC7; Gotcha SM2-3).
  - [ ] 5.3 GET `/sitemap.xml` → 200 (manualna provera + AC2 test); `/sr/sitemap.xml` → 404 (AC7 test).

- [ ] **Task 6 — RED testovi (TEA; Dev NE piše)** `[TEA-RED]`
  - [ ] 6.1 `test_sitemap_xml.py` — 200 + Content-Type application/xml + well-formed (ElementTree.fromstring bez ParseError) + root `<urlset>` + sitemaps.org 0.9 namespace + xhtml namespace deklaracija (AC2/AC8).
  - [ ] 6.2 `test_sitemap_content.py` — svaki tip prisutan: javni Product/Brand/Subcategory/Post `get_absolute_url` u `<loc>` skupu + pages:home/about/contact reverse u `<loc>` (AC3). (NE seed-uj Series/Category u sitemap-očekivanja — nemaju klasu.) **+ guard: render `/sitemap.xml` sa seed-ovanim Series/Category u DB NE sme oboriti 200 (jer nemaju sitemap klasu → nisu ni dodirnuti) — potvrđuje da CRIT-2 izostavljanje radi.** **TEA napomena (C2 — depth-4 hazard):** Subcategory seed-ovi MORAJU biti kreirani kroz normalan `save()` (ili `full_clean()`+`save()`), NE `bulk_create`/raw SQL koji zaobilazi `clean()`. Subcategory model `clean()`/`save()` ograničava dubinu na ≤3 (rute `subcategory_listing_l{1,2,3}` — `_l4` ne postoji). Ručno izgrađen `depth=4` chain bi pokušao reverse nepostojećeg `_l4` URL-a → `NoReverseMatch` → 500 sitemap-a — to bi bio artefakt test seed-ovanja, NE product bug.
  - [ ] 6.3 `test_sitemap_draft_not_leaked.py` — **SECURITY LOCK**: unpublished Product, coming-soon Brand, draft Post, scheduled (buduća published_at) Post NISU u `<loc>` skupu (AC4).
  - [ ] 6.4 `test_sitemap_hreflang.py` — svaki `<url>` ima `<xhtml:link rel="alternate" hreflang="sr|hu|en">` sa locale-prefiksovanim href; sva 3 koda prisutna (AC5).
  - [ ] 6.5 `test_sitemap_exclude.py` — Product/Post sa `SeoMeta.exclude_from_sitemap=True` NISU u `<loc>` skupu; bez-flag-a javni objekti SU prisutni (AC6).
  - [ ] 6.6 `test_sitemap_registration.py` — `/sitemap.xml`→200, `/sr/sitemap.xml`→404; `reverse("django.contrib.sitemaps.views.sitemap")`==`/sitemap.xml`; `"django.contrib.sitemaps"` u INSTALLED_APPS, `"django.contrib.sites"` NIJE; `apps.seo.sitemaps.sitemaps` dict ima TAČNO 5 ključeva (products/brands/subcategories/blog/pages — NEMA series/category) (AC1/AC7).
  - [ ] 6.7 (opciono) `test_sitemap_lastmod.py` — model `<url>` ima `<lastmod>` (iz updated_at); PageSitemap `<url>` NEMA lastmod (AC9). `makemigrations --check` čist (0 migracija).

- [ ] **Task 7 — Verifikacija + sprint-status (svi AC)** `[DEV-GREEN]`
  - [ ] 7.1 Pokreni ceo `apps/seo/tests/` suite (6-1 52 testa + 6-2 novi) — SVE GREEN. 6-1 SeoMeta testovi MORAJU ostati GREEN (regression).
  - [ ] 7.2 `uv run python manage.py makemigrations --check --dry-run` → „No changes detected" (0 migracija lock — SM-D).
  - [ ] 7.3 `uv run python manage.py check` exit 0. (Opciono manualno: pokreni server, GET /sitemap.xml, vizuelno potvrdi xhtml:link alternate + lastmod; pusti kroz sitemap.org validator — AC8 manualni korak.)
  - [ ] 7.4 Update `_bmad-output/implementation-artifacts/sprint-status.yaml`: `6-2` → done/ready-for-review.

## SM odluke (Decision log)

**SM-D1 — HREFLANG kroz Django built-in `i18n=True`+`alternates=True` (NE hand-rolled XML).** Postavljanjem `i18n = True` + `alternates = True` na svaku `Sitemap` podklasu, Django: (a) aktivira svaki jezik iz `LANGUAGES` i poziva `location()`/`get_absolute_url()` po jeziku (locale-prefiksovan URL kroz `reverse()` pod `i18n_patterns`), (b) emituje `<xhtml:link rel="alternate" hreflang="sr|hu|en">` cross-reference za svaku stavku, (c) deklariše `xmlns:xhtml` na `<urlset>`. **ZAŠTO built-in:** idiomatski (Django 5.2 native), schema-validan (framework template garantuje sitemap.org 0.9 + xhtml namespace conformance), manje error-prone (NEMA ručnog string formatiranja XML-a, NEMA escape bug-ova), automatski prati `LANGUAGES` (dodavanje jezika = 0 koda u sitemaps). Hand-rolled XML bi reinventovao framework + uveo XML-injection/escape rizik. `x_default` (Django 5.2 `Sitemap.x_default` atribut → `hreflang="x-default"`) = DEFER (OQ-2 — AC937 traži SAMO sr|hu|en; x-default je low-risk dodatak van AC-a).

**SM-D2 — NO sites framework: RequestSite iz request Host-a + sitemap.xml VAN i18n_patterns.** (a) **NEMA `django.contrib.sites`:** kad `sites` NIJE u INSTALLED_APPS, Django `sitemap` view koristi `RequestSite(request)` (domen iz `request.get_host()` → Host header). To je IDIOMATSKI fallback (Django docs § „Sitemap framework — sites framework not installed"), NE bug. NEMA `SITE_ID` settinga, NEMA sites tabele/migracije (0-migration cilj očuvan). Apsolutne URL-e u `<loc>` derivira request Host — `ALLOWED_HOSTS` ga ograničava u prod-u (Host-header trust granica — Gotcha SM2-6). `protocol`: Django default biraju request scheme; u prod-u (HTTPS) emituje `https://` (može se eksplicitno zaključati `Sitemap.protocol="https"` ako se želi forsirati — OQ-5, NE-blocking; default request-derived je OK). (b) **sitemap.xml VAN `i18n_patterns`:** registrovan u NO-PREFIX `urlpatterns` blok (mirror `i18n/setlang/`). Razlog: sitemap index NIJE per-locale — JEDAN `/sitemap.xml` lista SVE locale varijante kroz `i18n=True` alternate-e. Da je u `i18n_patterns`, postao bi `/sr/sitemap.xml` (+ `/hu/`, `/en/`) → 3 redundantna sitemap-a + bot konfuzija. Google očekuje sitemap na root-u (`/sitemap.xml`). (Gotcha SM2-3.)

**SM-D3 — DRAFT-NOT-LEAKED preko 5 eksplicitnih javnih predikata (SECURITY BOUNDARY).** Svaka `items()` vraća SAMO javne objekte — nacrt/coming-soon/unpublished/scheduled MORA biti odsutan (curenje u Google indeks = bezbednosni/poslovni propust). 5 predikata (verifikovano live čitanjem modela):
  - **Product:** `Product.objects.filter(is_published=True)` (`is_published` BooleanField default False → public = True; products/models.py:172).
  - **Brand:** `Brand.objects.filter(is_coming_soon=False)` (`is_coming_soon` default False → public = False; brands/models.py:98).
  - **Subcategory:** `Subcategory.objects.all()` — **NEMA visibility flag** (verifikovano; brands/models.py:311-360) → uvek javna; get_absolute_url ruta POSTOJI (2.11). **Napomena (C1):** SubcategorySitemap je bezbedno uključen jer `Subcategory.get_absolute_url()` referencira SOPSTVENU rutu porodicu `brands:subcategory_listing_l{1,2,3}` (registrovanu u `apps/brands/urls.py`), NE Series/Category rutu. Nema „subcategory-under-coming-soon-Brand curenja" jer Subcategory FK pokazuje na `Category` (NE na `Brand`) — Subcategory-jeva listing URL je uvek validna nezavisno od Brand-ove `is_coming_soon` vidljivosti.
  - **Post:** `Post.published.all()` — PublishedManager filtrira `status="published"` AND `published_at__lte=now` (5-1 AC3; blog/managers.py) → draft + scheduled (buduća published_at) automatski izostaju.
  - **Page:** home/about/contact su uvek-javne marketing strane (NEMA draft koncepta).
  - **Series/Category:** N/A — **IZOSTAVLJENI iz sitemap-a** (CRIT-2/SM-D6 — get_absolute_url RAISE NoReverseMatch). Iako bi oba bila „uvek-javna" (NEMA visibility flag), nemaju javnu detail URL → ne postoji ništa što bi sitemap mogao da izlista.

**SM-D4 — `exclude_from_sitemap` integracija preko GFK exclusion-set (NEMA join — ARCH-2/OQ-4 iz 6-1).** SeoMeta je GFK (content_type+object_id) BEZ `GenericRelation` na receiving modelima (6-1 OQ-4 odluka) → NE može se JOIN-ovati iz Product/Post ka SeoMeta. Umesto toga, `_excluded_pks(model)` gradi skup isključenih pk-jeva JEDNIM query-jem: `SeoMeta.objects.filter(content_type=get_for_model(model), exclude_from_sitemap=True).values_list("object_id", flat=True)`. `items()` = `public_qs.exclude(pk__in=excluded_set)`. **JEDAN query po sitemap klasi** (helper poziva se jednom u `items()`, NE per-objekat → NEMA N+1). Ovo je TAČAN forward-note obrazac koji je Architect ostavio u 6-1 (ARCH-2). Helper je deljen (jedna funkcija u sitemaps.py).

**SM-D5 — PageSitemap statički (home/about/contact).** „Page" sitemap = statičke marketing strane (NEMA `Page` modela — 6-1 potvrdio). `PageSitemap.items()` vraća listu URL-imena `["pages:home", "pages:about", "pages:contact"]` (verifikovano live: pages/urls.py `app_name="pages"` + name-ovi home/about/contact postoje). `location(item)` = `reverse(item)`. `i18n=True` → svaka strana dobija sr/hu/en alternate. **lastmod: OMIT** (statičke strane nemaju `updated_at`; SiteSettings.updated_at bi bio nategnut proxy — OQ-4 odluka: izostavi, izostanak `<lastmod>` je schema-validan; SM-D7). Service/parts/blog-index strane NISU u PageSitemap-u (OUT OF SCOPE — OQ-4; mogu se dodati u 6.x).

**SM-D6 / CRIT-2 — Series I Category IZOSTAVLJENI: get_absolute_url RAISE NoReverseMatch (render-safe > doslovnost).** Ovo je NAJVAŽNIJA korektnosna odluka 6.2 i divergencija od epics.md:934 (koja eksplicitno lista „Series, Subcategory"). **Dokaz (grep project-wide, verifikovano):**
  - `Series.get_absolute_url()` (brands/models.py:228-233) = `reverse("brands:series_detail", kwargs={...})`. Ime `brands:series_detail` se NIGDE ne registruje u `apps/brands/urls.py` (jedini hit u celom projektu je sam model na :231). → `reverse()` baca `NoReverseMatch`.
  - `Category.get_absolute_url()` (brands/models.py:296-303) = `reverse("brands:category_traktori"/"category_mehanizacija", ...)`. Ta imena takođe NE POSTOJE u brands/urls.py (postoje samo `detail`, `subcategory_listing_l1..l3`, `jeegee_prikljucna`, `hzm_radne_masine`, `tulip_mix_prikolice`). → `NoReverseMatch`.
  - Django `Sitemap._location(item)` poziva `item.get_absolute_url()` BEZ try/except. Kad `i18n=True`, poziva se po jeziku. Prvi `NoReverseMatch` se propagira kroz `sitemap` view → **CEO `/sitemap.xml` vraća HTTP 500** (ne samo ta sekcija). Jedan slomljen tip obara ceo sitemap.
  - **Zaključak:** Series/Category trenutno NEMAJU javnu standalone detail URL → ne postoji ništa indeksabilno. Uključiti ih = garantovan 500. **Odluka: NEMA `SeriesSitemap` ni `CategorySitemap`.** 6.2 isporučuje 5 klasa (Product/Brand/Subcategory/BlogPost/Page).
  - **Re-uključenje:** trivijalno čim 2.x doda `brands:series_detail` (i/ili category) rutu — dodaj klasu po istom obrascu kao Subcategory (`Series.objects.all().exclude(...)`, `lastmod`=`updated_at`). Vidi OQ-6.
  - **Zašto NE „guard-uj location() sa try/except umesto izostavljanja":** mogao bi se override-ovati `location()` da preskoči stavke koje raise — ALI to bi tiho izlistalo PRAZNE sekcije i maskiralo nedostajuću rutu (defensive boilerplate za nemoguć-trenutno slučaj; project-context.md:358). Čisto izostavljanje je jasnije i bez mrtvog koda. Kad ruta postoji, dodaje se cela klasa eksplicitno.

**SM-D7 — `lastmod`=`updated_at`; changefreq/priority OMIT.** `lastmod()` vraća `obj.updated_at` (TimestampedModel za Product/Post; inline `updated_at` za Brand/Series/Subcategory — svi imaju; verifikovano). NE `created_at` (lastmod treba poslednju izmenu za Google re-crawl). `changefreq`/`priority` = **OMIT** (OQ-3 — AC ne traži; Google ih tretira kao savetodavne/uglavnom ignoriše; izostanak je schema-validan; postavljanje = lažna preciznost). PageSitemap `lastmod` = OMIT (statičke strane bez updated_at).

**SM-D8 — FORWARD 6.3: sitemap.xml MORA postojati na stabilnoj URL-i.** Story 6.3 dodaje `robots.txt` koji NAVODI `Sitemap: https://.../sitemap.xml` lokaciju. 6.2 obezbeđuje da `/sitemap.xml` postoji na fiksnoj, stabilnoj, ne-locale-prefiksovanoj URL-i (`reverse("django.contrib.sitemaps.views.sitemap")` = `/sitemap.xml`) — 6.3 robots samo referencira tu URL. **6.2 NE gradi robots** (granica). Stabilna `sitemap.xml` URL je jedini 6.2→6.3 ugovor.

## Gotchas

**SM2-1 — `i18n=True`+`alternates=True` mehanika.** `i18n=True` čini da Django za svaku stavku iterira kroz `LANGUAGES`, aktivira jezik (`translation.activate`), i pozove `location()`/`get_absolute_url()` → pošto je `get_absolute_url` `reverse()`-baziran pod `i18n_patterns(prefix_default_language=True)`, vraća locale-prefiksovan URL (`/sr/...`, `/hu/...`, `/en/...`) AUTOMATSKI tačno. `alternates=True` dodaje cross-reference `<xhtml:link rel="alternate">` za svaki jezik na svakom `<url>`. **Oba MORAJU biti True** — `i18n=True` bez `alternates=True` daje per-locale `<loc>` ali BEZ hreflang cross-linkova (AC5 fail).

**SM2-2 — NO-SITES → RequestSite/Host.** Bez `django.contrib.sites` u INSTALLED_APPS, `sitemap` view automatski koristi `RequestSite(request)` (domen iz Host header-a). NE treba `SITE_ID`. U test client-u domen je `testserver` → `<loc>` = `http://testserver/sr/...`. NE asertuj fiksni domen u testu (asertuj path sufiks `/sr/<slug>/`). Prod domen dolazi iz stvarnog Host-a (`ALLOWED_HOSTS` ograničava — SM2-6).

**SM2-3 — sitemap.xml VAN i18n_patterns (inače `/sr/sitemap.xml`).** Ako se sitemap path stavi UNUTAR `i18n_patterns(...)`, dobija locale prefiks → `/sr/sitemap.xml` (+ hu/en), a `/sitemap.xml` daje 404 (Google ga ne nalazi na očekivanom root-u) + 3 redundantna sitemap-a. MORA ići u NO-PREFIX `urlpatterns` blok (gde je `i18n/setlang/`). AC7 test zaključava: `/sitemap.xml`→200, `/sr/sitemap.xml`→404.

**SM2-4 — GFK exclusion-set (NEMA join).** SeoMeta NEMA `GenericRelation` na receiving modelima (6-1 OQ-4) → `Product.objects.filter(seometa__exclude_from_sitemap=False)` NE radi (nema reverse accessor). MORA preko `_excluded_pks(model)` (filter SeoMeta po `content_type`+flag → `values_list("object_id")`) + `qs.exclude(pk__in=...)`. JEDAN query/klasa. NE pokušavaj reverse GFK lookup.

**SM2-5 — DRAFT-NOT-LEAKED × 5 predikata.** Svaki tip ima RAZLIČIT predikat (Product is_published / Brand is_coming_soon NEGIRAN / Subcategory uvek-javna / Post.published manager / Page statične). Lako je pogrešiti polaritet (npr. `Brand.objects.filter(is_coming_soon=True)` bi listao SAMO coming-soon → invertovano curenje). Brand je `is_coming_soon=False` (public). Post koristi `Post.published` MANAGER (ne `Post.objects.filter(status="published")` — manager DODATNO filtrira `published_at__lte=now` za scheduled).

**SM2-6 — Host-header u apsolutnim URL-ovima.** RequestSite uzima domen iz Host header-a → spoofovan Host može ubaciti tuđi domen u `<loc>`. `ALLOWED_HOSTS` (prod settings) ograničava prihvaćene Host vrednosti → mitigacija. NE dodatna validacija u sitemaps.py (project-context.md:358 — ALLOWED_HOSTS je prava granica).

**SM2-7 — `lastmod` None za statičke strane.** PageSitemap nema `lastmod` metodu → Django izostavi `<lastmod>` element (validno). NE vraćaj `None` iz `lastmod()` ako bi metoda postojala — bolje je NE definisati metodu (Django proverava `hasattr`). PageSitemap jednostavno NEMA `lastmod`.

**SM2-8 — get_absolute_url per-lang activation MORA biti reverse()-bazirana.** `i18n=True` oslanja se na to da `location()`/`get_absolute_url()` koristi `reverse()` (koji poštuje aktivni jezik pod `i18n_patterns`). Sitemap-ovani content modeli (Product/Brand/Subcategory/Post) sve rade (verifikovano: svi `get_absolute_url` = `reverse(...)` na POSTOJEĆE rute). Da neki vrati hardkodovan path, hreflang bi bio pogrešan. Blog `get_absolute_url` više NE raise NoReverseMatch (5-2 registrovao `blog:detail`); products:detail (2-7), brands:detail (2-6), brands:subcategory_listing_l* (2-11) postoje.

**SM2-11 — CRIT-2 NoReverseMatch render hazard (Series/Category).** `Series.get_absolute_url` → `brands:series_detail` i `Category.get_absolute_url` → `brands:category_traktori`/`category_mehanizacija` su jedini get_absolute_url-ovi u domenu koji raise `NoReverseMatch` (rute ne postoje — verifikovano grep-om). Django `Sitemap.location()` default NE hvata izuzetke → uključen SeriesSitemap/CategorySitemap obara CEO `/sitemap.xml` u 500 (ne samo svoju sekciju). ZATO se izostavljaju (SM-D6). **Dev MORA grep-om potvrditi da rute i dalje ne postoje pre eventualnog dodavanja klase.** TEA test (6.2): seed Series/Category u DB + render `/sitemap.xml` → 200 (jer nemaju klasu → nisu dodirnuti) — guard protiv slučajnog dodavanja klase.

**SM2-9 — 0-migration lock.** `django.contrib.sitemaps` NEMA modele → dodavanje u INSTALLED_APPS NE generiše migraciju. `makemigrations --check --dry-run` MORA reći „No changes detected". Ako iko slučajno doda `django.contrib.sites`, to UVODI sites migraciju + SITE_ID zahtev → krši 0-migration cilj. Drži `sites` ODSUTAN.

**SM2-10 — `name="django.contrib.sitemaps.views.sitemap"`.** Django dokumentovani URL name za sitemap view je upravo `django.contrib.sitemaps.views.sitemap` (puni dotted path kao name) — ovo je konvencija (omogućava `reverse()` + neke third-party integracije). Zadrži tačno taj `name=`.

## Open Questions

**OQ-1 — Series/Category u sitemap-u: in ili out?** epics.md:934 lista Series (NE Category). ALI `Series.get_absolute_url()`→`brands:series_detail` i `Category.get_absolute_url()`→`brands:category_traktori`/`category_mehanizacija` referenciraju **nepostojeće rute** (verifikovano grep-om) → `NoReverseMatch` → 500 ako se uključe. **SM odluka (CRIT-2/SM-D6): OBA IZVAN scope-a** — render-bezbednost > doslovno praćenje epic liste. Nije „opciono niskorizično" kao u prethodnoj verziji ove story — uključenje je TRENUTNO GARANTOVAN 500. **Re-uključiti tek kad 2.x doda series/category detail rutu.** Vidi OQ-6.

**OQ-2 — `x_default` hreflang?** Django 5.2 `Sitemap.x_default = True` dodaje `<xhtml:link rel="alternate" hreflang="x-default">` (pokazuje na default lang = sr). AC937 traži SAMO sr|hu|en. **SM odluka: DEFER** (van AC-a; low-risk poboljšanje za 6.x polish). Dev/TEA može uključiti ako želi best-practice — NE-blocking.

**OQ-3 — `changefreq`/`priority`?** AC ne traži. Google ih uglavnom ignoriše. **SM odluka: OMIT** (SM-D7 — lažna preciznost; izostanak je schema-validan). Ako SEO konsultant zatraži, trivijalno dodati po klasi.

**OQ-4 — PageSitemap lastmod + obim statičkih strana?** (a) lastmod za statičke strane: nemaju `updated_at`. **SM odluka: OMIT** (SiteSettings.updated_at bi bio nategnut proxy). (b) Koje strane: home/about/contact (marketing). Service/parts (lead-gen forme) + blog-index/search NISU uključene. **Odluka: TAČNO home/about/contact** — re-evaluacija u 6.x.

**OQ-5 — `protocol="https"` u prod vs request-derived u dev?** RequestSite + Django default biraju scheme iz request-a (`http://testserver` u testu, `https://` u prod-u iza TLS). Eksplicitno `Sitemap.protocol="https"` bi forsiralo https svuda (bolje za prod, ali lomi dev http). **SM odluka: request-derived default** (NE forsiraj protocol; prod iza HTTPS/proxy emituje https automatski ako je `SECURE_PROXY_SSL_HEADER`/scheme tačan). NE-blocking; ako prod sitemap emituje http (proxy scheme problem), eksplicitan `protocol="https"` je fix — dokumentovano za 6.3/deploy.

**OQ-6 — Re-uključenje Series/Category kad rute postanu dostupne + Subcategory visibility flag.** (a) **Series/Category re-ulazak (CRIT-2 follow-up):** čim 2.x (ili kasnija story) registruje `brands:series_detail` i/ili `brands:category_traktori`/`category_mehanizacija` rute, `Series.get_absolute_url`/`Category.get_absolute_url` prestaju da raise → dodaj `SeriesSitemap`/`CategorySitemap` po obrascu Subcategory (`.all().exclude(_excluded_pks(...))`, `lastmod`=`updated_at`, `i18n`/`alternates` True) + ključ u `sitemaps` dict + ažuriraj `test_sitemap_content.py`/`test_sitemap_registration.py`. **Ovo je jedini realan put da Series uđe u sitemap — NE pre rute.** (b) **Subcategory visibility flag:** trenutno Subcategory NEMA visibility flag (uvek javna — `.all()`). Ako buduća story doda `is_published`/`is_visible`, predikat MORA se ažurirati. Predikat je `.all()` SAMO jer flag ne postoji — NE jer je „sve javno" trajna odluka.

## Testing

> **TEA piše SVE testove PRE implementacije (RED). Dev NE piše testove.** Mirror `apps/seo/tests/` (6-1) + `apps/blog/tests/` layout. Test DB seed kroz fixtures/factory (mirror postojeći seo/blog conftest). SECURITY LOCK = `test_sitemap_draft_not_leaked.py` (najvažniji).

- **`test_sitemap_xml.py`** (AC2/AC8) — GET /sitemap.xml → 200; Content-Type application/xml (ili text/xml); telo parsabilno (`ElementTree.fromstring` bez `ParseError`); root tag `{http://www.sitemaps.org/schemas/sitemap/0.9}urlset`; `xmlns:xhtml` namespace prisutan; bar 1 `<url><loc>`.
- **`test_sitemap_content.py`** (AC3) — seed javni Product/Brand/Subcategory/Post; parsiraj `<loc>` skup; asertuj da svaki `get_absolute_url()` (sr-prefiksovan) JESTE prisutan; `reverse("pages:home")`/`about`/`contact` prisutni. **+ CRIT-2 guard: seed-uj i Series + Category objekat u DB → render `/sitemap.xml` MORA ostati 200 (oni nemaju sitemap klasu → nisu dodirnuti; sprečava regresiju ako neko doda SeriesSitemap a ruta i dalje ne postoji).** NE asertuj Series/Category `<loc>` (ne postoje).
- **`test_sitemap_draft_not_leaked.py`** (AC4 — **SECURITY LOCK**) — seed unpublished Product (is_published=False), coming-soon Brand (is_coming_soon=True), draft Post (status=draft), scheduled Post (status=published, published_at=future); asertuj da NIJEDAN od njihovih `get_absolute_url()` NIJE u `<loc>` skupu. (+ pozitivna kontrola: paralelni javni objekti JESU prisutni.)
- **`test_sitemap_hreflang.py`** (AC5) — parsiraj `<url>` elemente; svaki ima `<xhtml:link rel="alternate">` za hreflang sr + hu + en; href je locale-prefiksovan (hreflang="hu" → `/hu/`); sva 3 koda prisutna po stavci.
- **`test_sitemap_exclude.py`** (AC6) — seed javni Product P1 + Post B1 sa `SeoMeta(exclude_from_sitemap=True)`; asertuj P1/B1 `get_absolute_url()` NISU u `<loc>`; paralelni javni objekti BEZ flag-a JESU. (Opciono: asertuj `_excluded_pks(Product)` sadrži P1.pk.)
- **`test_sitemap_registration.py`** (AC1/AC7) — `/sitemap.xml`→200; `/sr/sitemap.xml`→404; `reverse("django.contrib.sitemaps.views.sitemap")` == `/sitemap.xml`; `"django.contrib.sitemaps"` u `settings.INSTALLED_APPS`; `"django.contrib.sites"` NIJE u INSTALLED_APPS; `apps.seo.sitemaps.sitemaps` dict ima TAČNO 5 ključeva (products/brands/subcategories/blog/pages — **NEMA series/category**, CRIT-2).
- **`test_sitemap_lastmod.py`** (AC9, opciono) — model `<url>` (Product) ima `<lastmod>` matching `updated_at` ISO datum; PageSitemap `<url>` (home) NEMA `<lastmod>`.
- **Regression:** `apps/seo/tests/` 6-1 (52 SeoMeta testa) MORAJU ostati GREEN (sitemaps.py ne dira model/admin/translation). `makemigrations --check --dry-run` → „No changes detected" (0 migracija lock).
- **Manualni QA (AC8, NE-automated):** pokreni server, GET /sitemap.xml, propusti kroz sitemap.org / Google Search Console validator (epics.md:939). Dokumentuj rezultat u review.

### TEA napomene za pisanje testova (IMP-4/5)

- **Asertovati na URL PATH SUFIKSIMA** (npr. `"/sr/proizvod/<slug>/"`, `"/sr/blog/<slug>/"`), NE na punim apsolutnim URL-ovima. `Client.get()` koristi host `"testserver"` + `http` scheme; domen dolazi iz `RequestSite(request)` → nikad ga ne hardkodovati u asercijama. (Vidi Gotcha SM2-2 — cross-reference: ista napomena o RequestSite/Host-u.) Tipičan pattern: `assert any("/sr/proizvod/" in loc for loc in loc_set)`.
- **Hreflang test — namespace-svestan XML parsing:** `<xhtml:link>` elemente parsovati NAMESPACE-AWARE metodom — koristiti `ElementTree.findall` sa punim URI-jem: `tree.findall(".//{http://www.w3.org/1999/xhtml}link")`, NE bare prefix string `"xhtml:link"` (koji ElementTree ne razrešava). Asertovati `rel="alternate"` + `hreflang` in `{"sr", "hu", "en"}` po svakom `<url>` elementu sa seed sadržajem.
- **Registration lock:** GET `/sitemap.xml` → 200; GET `/sr/sitemap.xml` → 404 (NIJE locale-prefiksovan — AC7). Oba asertovati u `test_sitemap_registration.py`.

## Reference

- **epics.md:927-939** — Story 6.2 ACs (Page/Product/Brand/Series/Subcategory/BlogPost sitemap klase; `alternates` hreflang; `sitemaps_dict` registracija; validan XML sa objavljenim sadržajem; `<xhtml:link rel="alternate" hreflang="sr|hu|en">`; `exclude_from_sitemap=True` izostanak; sitemap.org schema validacija).
- **epics.md:941-952** — Story 6.3 (robots.txt referencira sitemap.xml + pun OG) — granica; 6.2 samo obezbeđuje stabilan /sitemap.xml.
- **6-1-interface-contract.md** — SeoMeta GFK (content_type+object_id), `exclude_from_sitemap` BooleanField db_index; NEMA GenericRelation (OQ-4); ARCH-2 forward-note (exclusion-set pattern); apps.seo u INSTALLED_APPS.
- **config/urls.py:19-34** — no-prefix `urlpatterns` (`i18n/setlang/`) + `i18n_patterns(prefix_default_language=True)` blok (sitemap.xml ide u no-prefix).
- **config/settings/base.py:28-54** — INSTALLED_APPS (dodaj `django.contrib.sitemaps`); :146-150 LANGUAGES [sr,hu,en]; :155 MODELTRANSLATION_FALLBACK_LANGUAGES.
- **apps/products/models.py:172** — `is_published` BooleanField default False (public=True); :278-280 get_absolute_url reverse("products:detail").
- **apps/brands/models.py:98** — Brand.is_coming_soon default False (public=False); :156-158 get_absolute_url=reverse("brands:detail") (ruta POSTOJI 2.6); :166-233 Series get_absolute_url=reverse("brands:series_detail") → **ruta NE POSTOJI → NoReverseMatch → izvan scope CRIT-2/SM-D6**; :241-303 Category get_absolute_url=reverse("brands:category_traktori"/"category_mehanizacija") → **rute NE POSTOJE → NoReverseMatch → izvan scope CRIT-2**; :311-417 Subcategory get_absolute_url=reverse("brands:subcategory_listing_l*") (rute POSTOJE 2.11; NEMA visibility flag).
- **apps/brands/urls.py** — registrovane rute: `detail`, `jeegee_prikljucna`, `subcategory_listing_category`, `subcategory_listing_l1/l2/l3`, `hzm_radne_masine`, `tulip_mix_prikolice`. **NEMA `series_detail`, `category_traktori`, `category_mehanizacija`** (verifikovano grep-om project-wide — to je dokaz za CRIT-2).
- **apps/blog/models.py:207-209** — Post.get_absolute_url reverse("blog:detail"); 5-1 PublishedManager (status=published AND published_at<=now); 5-2 registrovao blog:detail URL.
- **apps/pages/urls.py:13-18** — `app_name="pages"`; name-ovi home/about/contact (PageSitemap items).
- **Django 5.2 sitemaps** — `Sitemap` (i18n/alternates/x_default/protocol atributi); `django.contrib.sitemaps.views.sitemap`; RequestSite fallback kad sites NIJE instaliran.
