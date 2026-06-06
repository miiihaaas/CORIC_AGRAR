---
story_id: "6.3"
story-key: 6-3-robots-txt-open-graph-twitter-card-meta
title: Robots.txt + Open Graph + Twitter Card Meta
status: ready-for-dev
epic: 6
epic_num: 6
epic_title: SEO & Discoverability
module: seo
created: 2026-06-06
last_modified: 2026-06-06
complexity: M
author: Mihas (SM autonomous; TREĆA story Epic 6 — SEO & Discoverability. EXTENDS deljeni `{% seo_head %}` tag (6-1) i dodaje GLOBALNI Open Graph + Twitter Card surface na SVAKU stranu (AC951) + NOVI javni `robots.txt` endpoint. **GLAVNA odluka (SM-D1) — GLOBALNI OG NA SVAKOJ STRANI BEZ DUPLIKATA:** base.html dobija JEDAN `{% block social_meta %}` koji renderuje site-level OG/twitter (obj=None fallback); detail strane OVERRIDE-uju TAJ ISTI block sa svojim objektom (mirror NO-DUPLICATE-<title> obrazac iz 6-1/SM-D2 — jedan block, child override → tačno JEDAN set OG tagova, NIKAD dva). **BEHAVIOR CHANGE (SM-D3):** `seo_head` trenutno emituje `og:image` SAMO kad `og_image` postoji; 6.3 čini `og:image` UVEK prisutan (fallback `static/img/og-default.jpg`) + dodaje pun OG/twitter set → ovo LOMI dva 6-1 no-og regression testa (`test_blog_post_detail.py:435 test_meta_no_open_graph_yet` + `test_seo_meta_tag.py:127 test_seo_head_no_og_image_when_unset`) → **6.3 VLASNIK tih testova** (prepisuje ih da asertuju OG PRISUTAN). OBJ-OPTIONAL site-level fallback (SM-D2): tag radi na home/listing/search/404 (BEZ objekta) bez 500 — `og:title`=company_name, `og:description`=SiteSettings.slogan, `og:url`=request.build_absolute_uri(request.path), `og:image`=og-default, `og:type`=website. og:type article-vs-website duck-type (SM-D5): `getattr(obj,"published_at",None)` postoji → "article" (blog Post), inače "website" (mirror `_display_title` low-coupling duck-typing iz 6-1). `_canonical_url(obj, request)` helper EKSTRAKCIJA (ARCH-3): canonical link + og:url DELE istu vrednost (build_absolute_uri(get_absolute_url()) sa graceful NoReverseMatch skip); obj=None → request.path. robots.txt (SM-D4): `apps/seo/views.py:robots_txt` → HttpResponse content_type="text/plain" renderuje `templates/seo/robots.txt` (User-agent: *, Allow: /, Disallow: admin path, Disallow: /htmx/, `Sitemap:` apsolutni URL preko reverse("django.contrib.sitemaps.views.sitemap")+build_absolute_uri — KONZUMIRA 6-2 stabilnu /sitemap.xml URL); registrovan u NO-PREFIX `urlpatterns` blok (mirror sitemap.xml/i18n-setlang — NIJE locale-prefiksovan). SECURITY (SM-D8): SVE OG/twitter content="" vrednosti (admin-uneti meta_title/meta_description/og_image) kroz `format_html` autoescape (mirror 6-1 SAFE pattern — NIKAD `|safe` na sirovim vrednostima; attribute-breakout-safe); robots.txt je text/plain (nema HTML injection). og-default.jpg (SM-D6): `static("img/og-default.jpg")` — asset NE postoji još → Dev dodaje placeholder fajl (static() gradi URL i bez fajla; placeholder sprečava broken link u prod-u; pravi brand asset = OQ biznis). 0 MIGRACIJA, 0 model promene, 0 novih dep-ova. RISK TIER: MEDIUM — 0 migracija + battle-tested Django HttpResponse/static, ALI: (a) BEHAVIOR CHANGE deljenog seo_head taga koji se renderuje na 3 detail strane + sad GLOBALNO → regression-blast-radius; (b) NO-DUPLICATE hazard (base site-level vs detail object OG — dupli tagovi lome social preview); (c) GLOBALNI <head> injection na SVAKU stranu = security surface (autoescape MORA biti tačan); (d) obj-optional graceful na SVAKOM tipu strane (home/listing/404) bez 500; (e) 2 owned regression testa.)
depends_on:
  - 6-1-seometa-model-per-page-admin                          # SeoMeta GFK model (meta_title/meta_description/og_image translatable); `{% seo_head %}`/`{% seo_title %}`/`{% seo_meta_description %}` tagovi + `_resolve_seometa` per-request keš + `_display_title`/`_display_description`/`_company_name`/`_load_site_settings` helperi; format_html SAFE pattern (SEO1-x); _canonical graceful NoReverseMatch skip (SM-D7 6-1) — 6.3 EKSTRAHUJE u `_canonical_url`
  - 6-2-sitemap-auto-generation-sa-hreflang                   # stabilna /sitemap.xml URL na `reverse("django.contrib.sitemaps.views.sitemap")` (NO-PREFIX blok) — robots.txt `Sitemap:` linija je referencira; NO-PREFIX urlpatterns obrazac za robots.txt registraciju
  - 3-4-sitesettings-singleton-config-model                   # SiteSettings.company_name (og:site_name + site-level og:title fallback) + .slogan (site-level og:description) — `_load_site_settings` per-request keš (6-1)
  - 1-4-i18n-setup-sa-locale-url-routing-i-switcher           # i18n_patterns(prefix_default_language=True) — robots.txt VAN i18n_patterns (NO-PREFIX); admin/ path JE pod i18n_patterns (/sr/admin/) → robots Disallow pokriva sve locale prefikse; build_absolute_uri za apsolutne OG URL-ove
  - 5-1-blogpost-category-tag-modeli-admin-stub               # Post.published_at (og:type="article" duck-type marker); Post.get_absolute_url (og:url/canonical)
  - 5-3-blog-post-detail-strana-kategorija-tag-arhive         # blog/post_detail.html (seo_head wiring) + test_blog_post_detail.py:435 test_meta_no_open_graph_yet (OWNED regression rewrite)
  - 2-6-brand-detail-strana                                   # brands/brand_detail.html (seo_head wiring); Brand.get_absolute_url
  - 2-7-product-detail-strana                                 # products/product_detail.html (seo_head wiring); Product.get_absolute_url
---

# Story 6.3: Robots.txt + Open Graph + Twitter Card Meta

Status: ready-for-dev

## Opis

As a **search engine bot ili social media platforma (Googlebot/Facebook/Twitter/LinkedIn crawler)**,

I want **`robots.txt` (koji navodi sitemap.xml lokaciju) + Open Graph i Twitter Card meta tagove na SVAKOJ strani**,

so that **mogu pravilno da indeksiram sadržaj i renderujem bogat social-share preview (naslov + opis + slika) kad neko podeli bilo koju URL sajta — sa fallback-om na site-level OG (i `og-default.jpg` sliku) za strane bez sopstvenog SeoMeta unosa**.

Ovo je **TREĆA story Epic 6 (SEO & Discoverability)** i ima DVA deliverable-a:

1. **`robots.txt` endpoint** — NOVI `apps/seo/views.py:robots_txt` (PRVI view u apps.seo) koji renderuje `templates/seo/robots.txt` kao `text/plain`, sa `Sitemap:` linijom koja navodi APSOLUTNU `/sitemap.xml` URL (konzumira 6-2). Registrovan VAN `i18n_patterns` (mirror sitemap.xml).
2. **GLOBALNI Open Graph + Twitter Card surface** — EXTENDS deljeni `{% seo_head %}` tag (6-1) da emituje pun OG set (`og:title`/`og:description`/`og:image`/`og:type`/`og:url` + `og:site_name`) + Twitter Card (`twitter:card`/`twitter:title`/`twitter:description`/`twitter:image`), i WIRE-uje ga GLOBALNO u `base.html` tako da SVAKA strana (ne samo detail strane) dobije OG/twitter — sa OBJ-OPTIONAL site-level fallback-om i BEZ DUPLIKATA.

> **GLAVNA odluka (SM-D1) — GLOBALNI OG BEZ DUPLIKATA:** `base.html` dobija JEDAN `{% block social_meta %}{% seo_head %}{% endblock %}` (poziv BEZ objekta → site-level OG fallback). Detail strane (product/brand/post) OVERRIDE-uju TAJ ISTI block sa `{% block social_meta %}{% seo_head <obj> %}{% endblock %}` (object-level OG). Pošto je to JEDAN block koji child šablon OVERRIDE-uje (NE dupli emit), dobija se TAČNO JEDAN set OG tagova po strani — IDENTIČAN NO-DUPLICATE-`<title>` obrazac iz 6-1/SM-D2 (gde base drži jedan `<title>{% block title %}`, child ga override-uje). Lock-uje se count-testom (`og:title` se pojavljuje TAČNO 1×; `<link rel="canonical">` 1×; `<title>` i dalje 1×).

> **BEHAVIOR CHANGE (SM-D3) — `og:image` SAD UVEK PRISUTAN:** 6-1 `seo_head` emituje `<meta property="og:image">` SAMO kad `SeoMeta.og_image` postoji (C-E latent tripwire). 6.3 menja to: `og:image` je UVEK prisutan (object og_image kad postoji, inače fallback `static("img/og-default.jpg")` — AC952). Ovo LOMI dva 6-1 regression testa koji asertuju OG-ODSUTNOST (`test_blog_post_detail.py:435` + `test_seo_meta_tag.py:127`). **6.3 JE VLASNIK tih testova** i prepisuje ih (asertuju da je OG sad PRISUTAN). Ovo je svesna, planirana evolucija deljenog taga — vidi SM-D3 + Owned Regression Tests.

### IN SCOPE (šta ova story isporučuje)

1. **NOVI `apps/seo/views.py:robots_txt(request)`** (AC1) — PRVI view u apps.seo. `HttpResponse(content_type="text/plain")` koji renderuje `templates/seo/robots.txt` sa kontekstom `{"sitemap_url": request.build_absolute_uri(reverse("django.contrib.sitemaps.views.sitemap"))}`. (Render kroz `render_to_string` ili `django.shortcuts.render` sa eksplicitnim `content_type`.)
2. **NOVI `templates/seo/robots.txt`** (AC1, SM-D4) — `User-agent: *`, `Allow: /`, `Disallow: /sr/admin/` + `/hu/admin/` + `/en/admin/` (admin je POD i18n_patterns → svi locale prefiksi; ILI generičko `Disallow: */admin/`), `Disallow: */htmx/` (HTMX partial endpoint-i su POD i18n_patterns → `/sr/htmx/...` — glob `*/htmx/`, NE `/htmx/` koji ne matchuje ništa; C3), `Sitemap: {{ sitemap_url }}` (apsolutna URL).
3. **`config/urls.py` EDIT: registruj `robots.txt` VAN i18n_patterns** (AC1, SM-D4) — `path("robots.txt", robots_txt, name="robots_txt")` u NO-PREFIX `urlpatterns` blok (gde su `i18n/setlang/` + `sitemap.xml`). NIJE locale-prefiksovan.
4. **`_canonical_url(obj, request)` helper EKSTRAKCIJA** (ARCH-3, SM-D7) u `seo_meta.py` — `request.build_absolute_uri(obj.get_absolute_url())` sa graceful skip (`AttributeError`/`NoReverseMatch` → `None`). canonical link I og:url DELE ovu funkciju (DRY). Za `obj=None` (site-level) → `request.build_absolute_uri(request.path)`.
5. **EXTEND `{% seo_head %}` tag: obj-optional + pun OG + Twitter Card** (AC2/AC3/AC4/AC5/AC7/AC8, SM-D1/D2/D5) — potpis `seo_head(context, obj=None)` (DEFAULT None → site-level mod). Emituje (uvek, redom):
   - `<link rel="canonical" href="{canonical}">` (graceful skip ako None) — NEPROMENJEN iz 6-1, sad kroz `_canonical_url`.
   - `<meta property="og:title" content="{title}">` — object: `seo_title`-vrednost (SeoMeta.meta_title ili `_display_title | company`); site-level: company_name.
   - `<meta property="og:description" content="{desc}">` — object: `seo_meta_description`-vrednost; site-level: SiteSettings.slogan.
   - `<meta property="og:image" content="{img}">` — **UVEK** (object og_image absolute URL, inače `static("img/og-default.jpg")` absolute; SM-D3/SM-D6).
   - `<meta property="og:type" content="{type}">` — "article" ako `getattr(obj,"published_at",None)` postoji (Post), inače "website" (SM-D5).
   - `<meta property="og:url" content="{canonical_or_path}">` — `_canonical_url` (= canonical); obj=None → request.path.
   - `<meta property="og:site_name" content="{company}">` — company_name (uvek; nice-to-have AC).
   - `<meta name="twitter:card" content="summary_large_image">` + `twitter:title`/`twitter:description`/`twitter:image` — MIRROR og:title/description/image (SM-D1).
6. **`base.html` EDIT: `{% block social_meta %}{% seo_head %}{% endblock %}`** (AC2/AC5/AC6, SM-D1) — JEDAN block u `<head>` (POSLE `{% block title %}`, PRE/uz `{% block extra_head %}`), default poziv BEZ objekta (site-level OG na svakoj strani). `{% load seo_meta %}` u base.html.
7. **Detail šabloni EDIT: override `{% block social_meta %}`** (AC8, SM-D1) — `products/product_detail.html`/`brands/brand_detail.html`/`blog/post_detail.html`: ZAMENI `{% block extra_head %}{% seo_head <obj> %}{% endblock %}` sa `{% block social_meta %}{% seo_head <obj> %}{% endblock %}` (object-level OG override). (Vidi SM-D1 za extra_head reconciliation — `seo_head` celokupno seli iz extra_head u social_meta block; canonical+og:image se ne dupliraju.)
8. **`static/img/og-default.jpg` placeholder** (AC4, SM-D6) — Dev dodaje placeholder JPG fajl (1200×630 prazna/brand boja) da `static()` URL nije broken link u prod-u. Pravi brand asset = OQ biznis.
9. **Owned regression test rewrite (TEA)** (AC10, SM-D3) — `test_blog_post_detail.py:435 test_meta_no_open_graph_yet` + `test_seo_meta_tag.py:127 test_seo_head_no_og_image_when_unset`: prepisati da asertuju OG SAD PRISUTAN (og:title + og:image sa fallback-om), NE odsutan.

### OUT OF SCOPE (eksplicitno — granice)

- **Redirect Manager (301)** = **Story 6.4** (`apps/seo/models.py:Redirect` + `RedirectMiddleware`). 6.3 NE dodaje model/middleware. (6.3 `apps/seo/views.py` je PRVI fajl u seo views — 6.4 dodaje middleware.py, NE dira views.py.)
- **i18n Fallback Marker (ⓘ tooltip)** = **Story 6.5**. Nije OG/robots.
- **hreflang HTML `<link rel="alternate">` tagovi u `<head>`** = **Story 6.6** (sitemap već ima hreflang iz 6-2; 6.6 dodaje HTML-head varijantu). 6.3 NE dodaje hreflang link tagove. **`og:locale` / `og:locale:alternate`** = DEFER do 6.6 (i18n locale surface; OQ-5 — AC951 traži samo OG core set, ne locale alternate).
- **Promena `seo_title`/`seo_meta_description` taga** = **NE** — oni ostaju STRING tagovi za `{% block title %}`/`{% block meta_description %}` (6-1; NEPROMENJENI). OG `og:title`/`og:description` se izvode iz ISTE fallback logike (reuse `_resolve_seometa`+`_display_title`+`_display_description`+`_company_name`) ali kroz `seo_head`, NE menjajući string tagove.
- **Novi `og:image` validacija / dimenzije / resize** = **NE** (OQ-2 — `og_image` se uzima kako jeste; 1200×630 preporuka je admin help-text/biznis briga, NE runtime validacija; YAGNI).
- **`noindex` meta per-strana / `robots` meta tag u `<head>`** = **NE** za 6.3 (robots.txt Disallow je dovoljan za htmx/admin; per-page `<meta name="robots" content="noindex">` na search/htmx je low-value polish — OQ-4 defer). 6.3 robots.txt je file-level, NE per-page meta.
- **`django.contrib.sites` / SITE_ID** = **NE** (6-2 SM-D2 — RequestSite/Host; build_absolute_uri derivira domen iz request Host; ALLOWED_HOSTS granica). robots `Sitemap:` URL je build_absolute_uri (request-derived domen).
- **Cache-ovanje robots.txt** = **NE** (YAGNI; trivijalan render; bot ga pita retko).
- **OG na HTMX partial response-ima** = **NE** (HTMX fragmenti ne nasleđuju base.html `<head>` — OG je samo na full-page render-ima koji extend-uju base.html; htmx partials nemaju `<head>` uopšte). Nije propust.
- **`changefreq`/`priority` u robots** = N/A (to je sitemap, ne robots; robots nema te direktive).

### Princip

DVA deliverable-a, oba LOW-COUPLING reuse: (1) `robots.txt` = jedan tanak view + jedan text/plain template + jedna NO-PREFIX URL registracija, koji KONZUMIRA 6-2 stabilnu `/sitemap.xml` URL (jedini 6-2→6-3 ugovor). (2) GLOBALNI OG/twitter = EXTEND postojećeg deljenog `seo_head` taga (obj-optional, pun OG set, format_html autoescape) + JEDAN `{% block social_meta %}` u base.html koji detail strane override-uju (NO-DUPLICATE-`<title>` obrazac iz 6-1/SM-D2 — jedan block, child override, NIKAD dupli emit). `og:type` duck-type kroz `published_at` (low-coupling, mirror `_display_title`). canonical+og:url dele `_canonical_url` helper (ARCH-3 DRY). `og:image` UVEK prisutan sa `og-default.jpg` fallback-om (BEHAVIOR CHANGE — owned regression). SVE vrednosti kroz `format_html` autoescape (head-injection-safe — SM-D8; NIKAD `|safe` na sirovim admin vrednostima). 0 migracija, 0 model promene, 0 novih dep-ova. NEMA defensive boilerplate-a oko render-a. NEMA premature OG locale-alternate (defer 6.6).

### Strukturna arhitektura — repository delta

**2 NOVA fajla (`apps/seo/views.py` + `templates/seo/robots.txt`) + 5 EDIT (config/urls.py + seo_meta.py + base.html + 3 detail šablona) + 1 placeholder asset (`static/img/og-default.jpg`) + 0 MIGRACIJA + 0 model promene + 0 novih dep-ova.**

| Path | Tip | Razlog |
|---|---|---|
| `apps/seo/views.py` | NOVO | `robots_txt(request)` view — `HttpResponse(content_type="text/plain")` renderuje `seo/robots.txt` sa `sitemap_url = request.build_absolute_uri(reverse("django.contrib.sitemaps.views.sitemap"))`. PRVI view u apps.seo (AC1/SM-D4). |
| `templates/seo/robots.txt` | NOVO | `User-agent: *` + `Allow: /` + `Disallow: */admin/` + `Disallow: */htmx/` (glob — htmx je POD i18n → `/sr/htmx/`; C3) + `Sitemap: {{ sitemap_url }}`. text/plain (AC1/SM-D4). |
| `config/urls.py` | EDIT | `from apps.seo.views import robots_txt` → `path("robots.txt", robots_txt, name="robots_txt")` u NO-PREFIX `urlpatterns` blok (uz `i18n/setlang/` + `sitemap.xml`). VAN `i18n_patterns` (SM-D4). |
| `apps/seo/templatetags/seo_meta.py` | EDIT (EXTEND) | (a) NOVI `_canonical_url(obj, request)` helper (ARCH-3/SM-D7 ekstrakcija). (b) `seo_head(context, obj=None)` — obj-optional + pun OG (og:title/description/image-UVEK/type/url/site_name) + Twitter Card. (c) `_og_type(obj)` duck-type helper (published_at → article; SM-D5). SVE kroz `format_html` (SM-D8). `seo_title`/`seo_meta_description`/`_resolve_seometa`/`_display_*`/`_company_name`/`_load_site_settings` NEPROMENJENI (reuse). |
| `templates/base.html` | EDIT | `{% load seo_meta %}` (vrh) + `{% block social_meta %}{% seo_head %}{% endblock %}` u `<head>` (POSLE `<title>`, oko/pre `{% block extra_head %}`). Site-level OG na SVAKOJ strani (AC2/AC5/AC6/SM-D1). |
| `templates/products/product_detail.html` | EDIT | ZAMENI `{% block extra_head %}{% seo_head product %}{% endblock %}` → `{% block social_meta %}{% seo_head product %}{% endblock %}` (object-level OG override; SM-D1). seo_title/seo_meta_description blokovi NEPROMENJENI. |
| `templates/brands/brand_detail.html` | EDIT | Isto: `{% block social_meta %}{% seo_head brand %}{% endblock %}` (SM-D1). |
| `templates/blog/post_detail.html` | EDIT | Isto: `{% block social_meta %}{% seo_head post %}{% endblock %}` (post ima published_at → og:type=article; SM-D5). |
| `static/img/og-default.jpg` | NOVO (placeholder) | Default OG fallback slika (1200×630). Placeholder dok biznis ne isporuči brand asset (SM-D6/OQ-1). static() gradi URL i bez fajla, ali placeholder sprečava broken link u prod social preview-u. |
| `apps/seo/tests/*` + `apps/blog/tests/test_blog_post_detail.py` (OWNED) | NOVO/EDIT (TEA) | RED-phase testovi (vidi Testing) + 2 OWNED regression rewrite (SM-D3). Dev NE piše testove. |
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | EDIT | `6-3-robots-txt-open-graph-twitter-card-meta` → `ready-for-dev`. SM handoff tracking (NIJE deliverable). |

**NETAKNUTO (regression guards):** `apps/seo/models.py` (SeoMeta — 6.3 SAMO čita; 0 model promene); SVE postojeće migracije (`makemigrations --check --dry-run` mora reći „No changes detected"); `apps/seo/sitemaps.py` (6-2 — 6.3 SAMO referencira `sitemap` URL name, NE dira); `seo_title`/`seo_meta_description` tagovi (string tagovi — NEPROMENJENI; OG ih reuse-uje kroz fallback helpere, ne menjajući ih); `{% block title %}`/`{% block meta_description %}`/`{% block extra_head %}` u base.html (postojeći blokovi — `social_meta` je NOVI block, NE menja postojeće; detail strane PRESELE seo_head iz extra_head u social_meta ali extra_head OSTAJE definisan u base za druge namene); `pyproject.toml` (0 novih dep-ova — HttpResponse/static/format_html su Django core); sav CSS/JS; `i18n_patterns` blok (robots.txt ide u NO-PREFIX blok — NE menja prefiksovane rute).

## Kriterijumi prihvatanja

**AC1 — `apps/seo/views.py:robots_txt` + `/robots.txt` → 200 text/plain sa Sitemap: linijom + Disallow admin (SM-D4)**

- **Given** 6-2 registrovan `/sitemap.xml` na stabilnoj NO-PREFIX URL-i (`reverse("django.contrib.sitemaps.views.sitemap")`)
- **When** kreiram `apps/seo/views.py:robots_txt` + `templates/seo/robots.txt` + registrujem `path("robots.txt", robots_txt, name="robots_txt")` u NO-PREFIX blok
- **Then**:
  - GET `/robots.txt` → HTTP 200, `Content-Type` počinje sa `text/plain`
  - Telo sadrži `User-agent: *`
  - Telo sadrži `Allow: /`
  - Telo sadrži `Disallow:` direktivu koja pokriva admin (`*/admin/` ILI `/sr/admin/`+`/hu/`+`/en/`)
  - Telo sadrži `Sitemap: ` liniju sa APSOLUTNOM `/sitemap.xml` URL-om (`http://testserver/sitemap.xml` u testu; build_absolute_uri + reverse)
  - `reverse("robots_txt")` razrešava na `/robots.txt` (NO-PREFIX); GET `/sr/robots.txt` → 404 (NIJE locale-prefiksovan)
- **And** Sitemap URL u robots-u JE ISTA URL koju 6-2 sitemap registruje (reverse-based, NE hardkodovan path)

**AC2 — Svaka strana ima OG u `<head>` (og:title/description/image/type/url) (SM-D1)**

- **Given** `base.html` sa `{% block social_meta %}{% seo_head %}{% endblock %}`
- **When** renderujem BILO KOJU full-page stranu (home/listing/detail)
- **Then** `<head>` sadrži `<meta property="og:title" content="...">`, `og:description`, `og:image`, `og:type`, `og:url` — SVE prisutne (5 core OG tagova)
- **And** ovo važi za strane SA objektom (detail) I BEZ objekta (home/listing) — site-level fallback (AC5)

**AC3 — Twitter Card meta prisutan na svakoj strani (SM-D1)**

- **Given** AC2
- **When** renderujem stranu
- **Then** `<head>` sadrži `<meta name="twitter:card" content="summary_large_image">` + `twitter:title` + `twitter:description` + `twitter:image`
- **And** twitter:title/description/image MIRROR-uju og:title/description/image vrednosti

**AC4 — og:image fallback na og-default.jpg kad nema SeoMeta.og_image; object og_image kad postoji (SM-D3/SM-D6)**

- **Given** detail objekat BEZ `SeoMeta.og_image` (ili bez SeoMeta uopšte)
- **When** renderujem detail stranu
- **Then** `og:image` (i `twitter:image`) sadrži apsolutnu URL `static("img/og-default.jpg")` (fallback)
- **And When** objekat IMA `SeoMeta.og_image`
- **Then** `og:image` sadrži apsolutnu URL te slike (NE default)
- **And** `og:image` je UVEK prisutan (NIKAD izostavljen — BEHAVIOR CHANGE od 6-1; SM-D3)

**AC5 — obj-optional site-level fallback (home/listing strana ima site-level OG) (SM-D2)**

- **Given** strana BEZ objekta (home/listing/search — base.html `{% seo_head %}` bez argumenta)
- **When** renderujem
- **Then** `seo_head` NE pada (NE 500) i emituje:
  - `og:title` = SiteSettings.company_name
  - `og:description` = SiteSettings.slogan
  - `og:url` = `request.build_absolute_uri(request.path)` (trenutna strana)
  - `og:image` = apsolutni `static("img/og-default.jpg")`
  - `og:type` = "website"
  - `og:site_name` = company_name
- **And** tag radi i kad SiteSettings.slogan prazan (og:description prazan string ili izostavljen — graceful, NE 500)

**AC6 — NEMA duplikata: og:title 1×, canonical 1×, `<title>` i dalje 1× (SM-D1)**

- **Given** detail strana (override-uje `{% block social_meta %}` sa objektom, dok base ima site-level default u ISTOM block-u)
- **When** renderujem detail stranu i prebrojim
- **Then** `og:title` se pojavljuje TAČNO 1× (NE 2× — child override zamenjuje base default, NE dodaje uz njega)
- **And** `<link rel="canonical">` se pojavljuje TAČNO 1×
- **And** `<title>` se pojavljuje TAČNO 1× (regression — 6-1 SM-D2 NO-DUPLICATE-`<title>` očuvan)
- **And** `og:image` TAČNO 1×

**AC7 — og:type article za Post, website inače (SM-D5)**

- **Given** blog Post (ima `published_at` atribut) vs Product/Brand (nemaju) vs obj=None
- **When** renderujem
- **Then** Post detail → `og:type` content="article"
- **And** Product/Brand detail → `og:type` content="website"
- **And** site-level (obj=None) → `og:type` content="website"
- **And** rezolucija je duck-type: `getattr(obj, "published_at", None)` truthy → "article" (NE isinstance/import Post — low-coupling, mirror `_display_title`)

**AC8 — detail strana OG koristi SeoMeta meta_title/meta_description (ili fallback) (SM-D1)**

- **Given** detail objekat SA `SeoMeta(meta_title="Custom", meta_description="Opis")`
- **When** renderujem detail stranu
- **Then** `og:title` content sadrži "Custom" (admin SeoMeta.meta_title — ISTA logika kao `seo_title`)
- **And** `og:description` content sadrži "Opis" (SeoMeta.meta_description — ISTA logika kao `seo_meta_description`)
- **And When** nema SeoMeta → og:title = `_display_title | company`, og:description = `_display_description` fallback (reuse 6-1 fallback chain, CRIT-1 očuvan)

**AC9 — Security: OG/twitter content="" autoescaped (NEMA head injection) (SM-D8)**

- **Given** objekat sa `SeoMeta.meta_title` koji sadrži `">` ili `"` ili `<script>` (attribute-breakout / XSS pokušaj)
- **When** renderujem OG
- **Then** te vrednosti su HTML-escaped u `content="..."` (kroz `format_html` — `"` → `&quot;`, `<` → `&lt;`, `>` → `&gt;`); NE mogu probiti atribut/`<head>` ni injektovati tag
- **And** NIGDE se ne koristi `|safe` na sirovim admin/object vrednostima (mirror 6-1 SAFE pattern)
- **And** robots.txt je `text/plain` (nema HTML konteksta → nema HTML injection vektora; `sitemap_url` je reverse-derived, NE user input)

**AC10 — 6-1 no-og regression testovi prepisani (OG sad PRISUTAN) (SM-D3)**

- **Given** BEHAVIOR CHANGE: `seo_head` sad UVEK emituje OG (og:image sa fallback-om + pun set)
- **When** TEA prepiše `test_blog_post_detail.py:435 test_meta_no_open_graph_yet` + `test_seo_meta_tag.py:127 test_seo_head_no_og_image_when_unset`
- **Then** `test_meta_no_open_graph_yet` (preimenovan npr. `test_meta_has_open_graph`) asertuje `property="og:title"` I `property="og:image"` PRISUTNI u detail HTML-u (NE odsutni)
- **And** `test_seo_head_no_og_image_when_unset` (preimenovan npr. `test_seo_head_og_image_falls_back_to_default`) asertuje da bez `og_image` → `og:image` SADRŽI `og-default.jpg` (fallback), NE da je odsutan
- **And** `test_seo_head_emits_og_image_when_set` (`test_seo_meta_tag.py:113`) OSTAJE GREEN (object og_image se i dalje koristi kad postoji — sad samo NIJE jedini slučaj sa og:image)

## Tasks / Subtasks

> **Konvencija:** `[TEA-RED]` = Test Architect piše test PRE implementacije (mora FAIL). `[DEV-GREEN]` = Developer implementira da test prođe. **Dev NIKAD ne piše testove.** **NEMA migracije** (6.3 je 0-migration; `makemigrations --check` mora ostati čist). **NEMA `uv add`** (HttpResponse/static/format_html su Django core).

- [ ] **Task 1 — `apps/seo/views.py:robots_txt` + `templates/seo/robots.txt` + URL registracija (AC1)** `[DEV-GREEN]`
  - [ ] 1.1 Kreiraj `apps/seo/views.py`: `robots_txt(request)`. Import `from django.shortcuts import render` (ili `render_to_string` + `HttpResponse`), `from django.urls import reverse`. `sitemap_url = request.build_absolute_uri(reverse("django.contrib.sitemaps.views.sitemap"))`. Return `render(request, "seo/robots.txt", {"sitemap_url": sitemap_url}, content_type="text/plain")`.
  - [ ] 1.2 Kreiraj `templates/seo/robots.txt`:
    ```
    User-agent: *
    Allow: /
    Disallow: */admin/
    Disallow: */htmx/
    Sitemap: {{ sitemap_url }}
    ```
    **⚠️ C3 — htmx je POD i18n_patterns (`/sr/htmx/...`, NE `/htmx/`):** verifikovano `config/urls.py:40-42` — search (`htmx/pretraga/`) i forms (`htmx/forme/...`) URL-ovi su unutar `i18n_patterns` bloka → stvarni path je `/sr/htmx/...`, `/hu/htmx/...`, `/en/htmx/...`. Zato `Disallow: /htmx/` (root) **NE matchuje NIŠTA** (taj path ne postoji). MORA biti `Disallow: */htmx/` (glob `*` — isti obrazac kao admin) da pokrije sve locale prefikse. (OQ-6 razrešen: koristi `*/htmx/` glob.)
    (`Disallow: */admin/` pokriva `/sr/admin/`+`/hu/admin/`+`/en/admin/` jer je admin POD i18n_patterns (`config/urls.py:37`); `*` mid-path glob je podržan od Googlebot/Bingbot — projektni target crawler-i. Alternativa za maksimalnu portabilnost: 3 eksplicitne linije po locale-u (`Disallow: /sr/admin/` + `/hu/admin/` + `/en/admin/`) — Dev bira; `*/admin/` je sažetije i dovoljno za target crawler-e.)
  - [ ] 1.3 `config/urls.py`: `from apps.seo.views import robots_txt` + dodaj `path("robots.txt", robots_txt, name="robots_txt")` u NO-PREFIX `urlpatterns` listu (uz `i18n/setlang/` + `sitemap.xml`). **VAN `i18n_patterns`** (SM-D4).
  - [ ] 1.4 `uv run python manage.py check` exit 0. GET `/robots.txt` → 200 text/plain (manualna provera + AC1 test).

- [ ] **Task 2 — `_canonical_url` helper ekstrakcija (ARCH-3, AC2/AC5)** `[DEV-GREEN]`
  - [ ] 2.1 U `seo_meta.py` dodaj `def _canonical_url(obj, request):` — ako `obj is None` → `return request.build_absolute_uri(request.path) if request else None`. Inače: `try: url = obj.get_absolute_url(); return request.build_absolute_uri(url) if request else url; except (AttributeError, NoReverseMatch): return None`.
  - [ ] 2.2 Refaktoriši postojeći `seo_head` canonical blok da koristi `_canonical_url(obj, request)` (umesto inline try/except) — REGRESSION: 6-1 canonical testovi (`test_seo_meta_tag.py` graceful-skip + i18n-prefix) MORAJU ostati GREEN.

- [ ] **Task 3 — `_og_type` duck-type helper (AC7)** `[DEV-GREEN]`
  - [ ] 3.1 `def _og_type(obj): return "article" if getattr(obj, "published_at", None) else "website"`. (obj=None → getattr na None vraća None → "website"; bezbedno.) **NE import-uj Post / NE isinstance** (low-coupling — SM-D5, mirror `_display_title`).

- [ ] **Task 4 — EXTEND `seo_head`: obj-optional + pun OG + Twitter Card (AC2/AC3/AC4/AC5/AC7/AC8/AC9, SM-D1/D2/D8)** `[DEV-GREEN]`
  - [ ] 4.1 Promeni potpis na `def seo_head(context, obj=None):` (DEFAULT None — site-level mod; obj-optional je SRŽ globalnog OG-a).
  - [ ] 4.2 Izvedi vrednosti (reuse 6-1 helpere):
    - `title`: ako `obj is None` → `_company_name(context)`; inače reuse `seo_title`-logiku — `seo = _resolve_seometa(obj, context); title = seo.meta_title if (seo and seo.meta_title.strip()) else f"{_display_title(obj)} | {_company_name(context)}"`. (Može pozvati postojeću `seo_title(context, obj)` funkciju direktno radi DRY.)
    - `description`: ako `obj is None` → `_load_site_settings(context).slogan or ""`; inače reuse `seo_meta_description`-logiku (`seo.meta_description` ili `_display_description(obj, context)`).
    - `image`: object `seo.og_image` (ako postoji) → `request.build_absolute_uri(seo.og_image.url)`; inače `request.build_absolute_uri(static("img/og-default.jpg"))`. **UVEK postavljena** (SM-D3). `from django.templatetags.static import static`.
    - `og_type`: `_og_type(obj)`.
    - `url`: `_canonical_url(obj, request)` (= canonical; obj=None → request.path).
    - `company`: `_company_name(context)` (og:site_name).
  - [ ] 4.3 Emituj parts redom kroz `format_html` (SM-D8 — SVE vrednosti autoescaped): canonical link (ako url not None i obj postoji — vidi 4.4), og:title, og:description, og:image, og:type, og:url, og:site_name, twitter:card (statički "summary_large_image"), twitter:title, twitter:description, twitter:image. `return mark_safe("\n".join(parts))`.
  - [ ] 4.4 **canonical link + og:url emisija (C7 — VEZANI, isti uslov):** izračunaj `canonical = _canonical_url(obj, request)` JEDNOM. Emituj `<link rel="canonical" href="{canonical}">` **I** `<meta property="og:url" content="{canonical}">` **SAMO kad `canonical is not None`** (graceful skip — zadrži 6-1 canonical ponašanje, og:url prati ISTI uslov). Za obj=None sa request-om → canonical = request.path → oba se emituju (site-level canonical/og:url na trenutnu stranu; social_meta je JEDAN block → nema duplikata). **Kad `canonical is None` (request=None ILI obj bez get_absolute_url) → skip OBA** (NE emituj `og:url content=""` prazan tag, NE 500). **NE „og:url se uvek emituje"** — to je bila kontradikcija sa 4.5; og:url i canonical su vezani na isti `_canonical_url` rezultat. (Ostali OG tagovi — og:title/description/image/type/site_name — se emituju nezavisno od canonical/url skip-a.)
  - [ ] 4.5 Graceful: ako `request is None` (npr. izolovan tag-unit render bez request u contextu) — `_canonical_url` vraća None → canonical+og:url se preskaču (NE 500). Ostali OG tagovi (og:title/description/type/site_name) se i dalje emituju; og:image gradi relativnu `static()` URL bez build_absolute_uri (ili skip apsolutizacije). (Mirror 6-1 `if request is not None` guard. U produkciji request je UVEK prisutan — ovo je samo unit-render bezbednost.)

- [ ] **Task 5 — `base.html` global `{% block social_meta %}` (AC2/AC5/AC6, SM-D1)** `[DEV-GREEN]`
  - [ ] 5.1 Dodaj `{% load seo_meta %}` u `base.html` (vrh, uz ostale load-ove).
  - [ ] 5.2 Dodaj `{% block social_meta %}{% seo_head %}{% endblock %}` u `<head>` — POSLE `<title>` linije, oko/pre `{% block extra_head %}{% endblock %}`. Site-level OG default (poziv BEZ objekta) na SVAKOJ strani.
  - [ ] 5.3 `{% block extra_head %}` OSTAJE (za druge per-page head potrebe) — ali seo_head se SELI iz njega u social_meta (vidi Task 6).
  - [ ] 5.4 **(C5 — OČEKIVANO ponašanje, NE bug):** strane koje NE override-uju `social_meta` (npr. `brands/brand_coming_soon.html` — noindex coming-soon, home, listing) dobijaju base **site-level** OG (og:title=company_name, og:image=og-default, og:type=website). To je PRIHVATLJIVO: `noindex` upravlja INDEKSIRANJEM (search), NE social scraper-ima; coming-soon site-level OG izlaže samo javne company info (ime/slogan/default sliku) — bez curenja brand detalja. **Dev NE treba da flag-uje ovo kao bug tokom testiranja.** (Buduća story bi mogla da `brand_coming_soon` override-uje `social_meta` sa brand objektom za bogatiji preview — ALI NIJE traženo u 6.3.)

- [ ] **Task 6 — Detail šabloni: PRESELI seo_head iz `extra_head` u `social_meta` (DELETE+ADD, NE samo ADD) (AC8, SM-D1)** `[DEV-GREEN]`
  - [ ] **⚠️ C2 — MORA SE PRESELITI (DELETE stari + ADD novi), NE samo dodati:** za SVAKU od 3 detail strane: **(1) OBRIŠI postojeću liniju `{% block extra_head %}{% seo_head <obj> %}{% endblock %}` (NE ostavljaj je!) + (2) DODAJ `{% block social_meta %}{% seo_head <obj> %}{% endblock %}`.** Ako Dev DODA `social_meta` a OSTAVI stari `extra_head` seo_head → detail strana emituje seo_head DVAPUT (2 canonical, 2 og:image, 2 og:title) → AC6 count-test (og:title==1, canonical==1) PADA + social crawler dobija dupli/zbunjen preview. seo_head sme postojati u TAČNO JEDNOM block-u po strani.
  - [ ] 6.1 `products/product_detail.html`: **OBRIŠI** `{% block extra_head %}{% seo_head product %}{% endblock %}` (`:8`) → **DODAJ** `{% block social_meta %}{% seo_head product %}{% endblock %}`. (Ako product_detail nema drugih extra_head sadržaja, extra_head override se uklanja u celosti — base prazan extra_head default ostaje; seo_title/seo_meta_description blokovi OSTAJU.)
  - [ ] 6.2 `brands/brand_detail.html`: isto — **OBRIŠI** `{% block extra_head %}{% seo_head brand %}{% endblock %}` → **DODAJ** `{% block social_meta %}{% seo_head brand %}{% endblock %}`.
  - [ ] 6.3 `blog/post_detail.html`: isto — **OBRIŠI** `{% block extra_head %}{% seo_head post %}{% endblock %}` → **DODAJ** `{% block social_meta %}{% seo_head post %}{% endblock %}`. (post ima published_at → og:type=article; AC7.)
  - [ ] 6.4 **NO-DUPLICATE verifikacija (SM-D1):** pošto detail strane override-uju ISTI `social_meta` block koji base default-uje, base site-level seo_head se NE renderuje na detail stranama (child override zamenjuje) → tačno JEDAN set OG. **A pošto je seo_head OBRISAN iz extra_head (6.1-6.3 DELETE), nema drugog seo_head poziva.** Lock-uje AC6 count-test (og:title==1, canonical==1, og:image==1).

- [ ] **Task 7 — `static/img/og-default.jpg` placeholder (AC4, SM-D6) — ⚠️ MANDATORY/BLOCKING (PROD 500 ako fali; C6)** `[DEV-GREEN]`
  - [ ] 7.1 **(BLOCKING)** Dodaj VALIDAN placeholder JPG (1200×630, brand boja ili logo-na-pozadini) na `static/img/og-default.jpg`. **NIJE nicety — fajl MORA postojati pre ship-a.** Razlog (C6): prod I staging koriste `CompressedManifestStaticFilesStorage` (`production.py:39-44`/`staging.py:25-30`) — pod manifest storage `static("img/og-default.jpg")` za NEPOSTOJEĆI fajl raise-uje `ValueError: Missing staticfiles manifest entry` u REQUEST vremenu. Pošto se site-level OG `static()` poziva na SVAKOJ strani → fajl-koji-fali = **SITE-WIDE 500 u prod/staging**. (Dev/test plain StaticFilesStorage NE raise-uje → testovi maskiraju ovo.)
  - [ ] 7.2 **(BLOCKING — GREEN verifikacija)** Potvrdi da fajl FIZIČKI postoji na disku: `static/img/og-default.jpg`. Po mogućstvu (jeftino) pokreni smoke `uv run python manage.py collectstatic --noinput` pod manifest storage (`DJANGO_SETTINGS_MODULE=config.settings.staging`) i potvrdi da manifest unos za `img/og-default.jpg` postoji (NE raise Valueable pri prvom request-u). ILI dodaj jeftin test (TEA, Task 9) koji asertuje `(Path(settings.BASE_DIR)/"static/img/og-default.jpg").exists()`. **Bez ovog koraka prod = site-wide 500.**
  - [ ] 7.3 (Opciono) help-text u SeoMeta.og_image admin (1200×630 preporuka) — NE-blocking, može u 6.x. NE menja model (0 migracija). Pravi brand OG banner = OQ-1 biznis (placeholder ostaje dok ga biznis ne zameni — 0 koda).

- [ ] **Task 8 — OWNED regression test rewrite (AC10, SM-D3)** `[TEA-RED]`
  - [ ] 8.1 `apps/blog/tests/test_blog_post_detail.py:435` — prepiši `test_meta_no_open_graph_yet` → `test_meta_has_open_graph` (ili sl.): asertuj `'property="og:title"' in html` I `'property="og:image"' in html` (OG SAD PRISUTAN — BEHAVIOR CHANGE). Ukloni stari `assert 'property="og:' not in html`.
  - [ ] 8.2 `apps/seo/tests/test_seo_meta_tag.py:127` — prepiši `test_seo_head_no_og_image_when_unset` → `test_seo_head_og_image_falls_back_to_default`: asertuj `'property="og:image"' in out` I `"og-default.jpg" in out` (fallback PRISUTAN, NE odsutan). Ukloni stari `not in` assert.
  - [ ] 8.3 Verifikuj `test_seo_head_emits_og_image_when_set` (`test_seo_meta_tag.py:113`) OSTAJE validan/GREEN — object og_image se i dalje koristi (sad samo NIJE jedini izvor og:image; assert `'property="og:image"' in out` i dalje važi; opciono pojačaj: assert da SADRŽI uploadovani fajl path, NE og-default).
  - [ ] 8.4 **(C1 — OWNED HARNESS UPDATE)** `apps/seo/tests/test_head_integration.py:26-32` — AŽURIRAJ `_HARNESS`: poslednju liniju `"{% block extra_head %}{% seo_head obj %}{% endblock %}\n"` ZAMENI sa `"{% block social_meta %}{% seo_head obj %}{% endblock %}\n"` (mirror stvarne detail-template migracije iz Task 6 / SEO3-9). Razlog: posle 6.3 base.html default-uje `{% block social_meta %}{% seo_head %}{% endblock %}` (site-level, obj=None) koji TAKOĐE emituje canonical; ako harness ostane na `extra_head`, base site-level seo_head OSTAJE renderovan → DVA seo_head poziva → `test_canonical_present_once_in_full_head` (`:74`) vidi 2 canonical-a → RED. Selidbom seo_head u `social_meta` override → child zamenjuje base default → tačno 1 seo_head → 1 canonical. **Asertacije svih 3 head_integration testova ostaju NEPROMENJENE (== 1)** — menja se SAMO harness (block ime). Verifikuj POSLE: `test_canonical_present_once_in_full_head` GREEN (1 canonical), `test_exactly_one_title_tag` GREEN (seo_head ne emituje `<title>`), `test_exactly_one_meta_description_tag` GREEN (seo_head ne emituje `name="description"`).

- [ ] **Task 9 — RED testovi (TEA; Dev NE piše) (AC1-AC9)** `[TEA-RED]`
  - [ ] 9.1 `test_robots_txt.py` (AC1): GET `/robots.txt`→200; Content-Type text/plain; telo ima `User-agent: *` + `Allow: /` + `Disallow:`(admin) + `Sitemap: http://testserver/sitemap.xml`; `reverse("robots_txt")`==`/robots.txt`; `/sr/robots.txt`→404. Sitemap linija == build_absolute_uri(reverse(sitemap)).
  - [ ] 9.2 `test_open_graph.py` (AC2/AC8): detail strana (product/post sa+bez SeoMeta) ima og:title/description/image/type/url; sa SeoMeta(meta_title="X") → og:title sadrži "X"; bez → fallback `_display_title | company`.
  - [ ] 9.3 `test_twitter_card.py` (AC3): strana ima twitter:card=summary_large_image + twitter:title/description/image; mirror og vrednosti.
  - [ ] 9.4 `test_og_fallback.py` (AC4/AC5): (a) detail bez og_image → og:image sadrži `og-default.jpg`; sa og_image → sadrži upload path. (b) site-level (render base-only strane / home BEZ objekta) → og:title=company_name, og:description=slogan, og:type=website, og:url=request path, og:image=og-default; NE 500 kad slogan prazan.
  - [ ] 9.5 `test_og_no_duplicate.py` (AC6): detail strana — `html.count('property="og:title"')`==1; `html.count('rel="canonical"')`==1; `html.count("<title")`==1; `html.count('property="og:image"')`==1. (NO-DUPLICATE lock — SM-D1 mirror.)
  - [ ] 9.6 `test_og_type.py` (AC7): Post detail → og:type=article; Product/Brand detail → website; obj=None → website. (Duck-type published_at.)
  - [ ] 9.7 `test_og_security.py` (AC9): SeoMeta.meta_title=`'"><script>alert(1)</script>'` (ili `'" onload="x'`) → render → vrednost je HTML-escaped u content="" (`&quot;`/`&lt;`/`&gt;`); NE probija atribut; NIGDE `|safe`. (format_html autoescape lock — SEO3-6.)
  - [ ] 9.8 (opciono) `test_robots_template.py` — render `seo/robots.txt` template direktno; struktura linija; bez HTML.

- [ ] **Task 10 — Verifikacija + sprint-status (svi AC)** `[DEV-GREEN]`
  - [ ] 10.1 Pokreni ceo `apps/seo/tests/` + `apps/blog/tests/` suite — SVE GREEN. **6-1 SeoMeta/seo_head testovi MORAJU ostati GREEN osim 2 OWNED (Task 8) koja su namerno prepisana** (regression-aware).
  - [ ] 10.2 `uv run python manage.py makemigrations --check --dry-run` → „No changes detected" (0 migracija lock).
  - [ ] 10.3 `uv run python manage.py check` exit 0. (Opciono manualno: server, GET /robots.txt + GET home/detail strane, vizuelno potvrdi OG/twitter u view-source; propusti detail URL kroz Facebook Sharing Debugger / Twitter Card Validator — AC manualni QA.)
  - [ ] 10.4 Update `_bmad-output/implementation-artifacts/sprint-status.yaml`: `6-3` → done/ready-for-review.

## SM odluke (Decision log)

**SM-D1 — GLOBALNI OG NA SVAKOJ STRANI + NO-DUPLICATE (GLAVNA odluka; mirror 6-1 SM-D2 NO-DUPLICATE-`<title>`).** AC951 traži OG na SVAKOJ strani, ali samo detail strane imaju `object`. Mehanizam:
  - `base.html` dobija JEDAN `{% block social_meta %}{% seo_head %}{% endblock %}` u `<head>` — poziv BEZ objekta → site-level OG fallback (AC5). Ovo se renderuje na SVAKOJ strani koja extend-uje base (home/listing/search/404 — sve dobiju OG).
  - Detail strane (product/brand/post) OVERRIDE-uju TAJ ISTI block: `{% block social_meta %}{% seo_head <obj> %}{% endblock %}` → object-level OG.
  - **NO-DUPLICATE garancija:** Django template nasleđivanje — child `{% block X %}` ZAMENJUJE parent default, NE dodaje uz njega. Pošto je `social_meta` JEDAN block, detail strana renderuje SAMO svoj object-OG; base site-level default se NE renderuje na detail stranama. Rezultat: TAČNO jedan set OG tagova po strani. **Ovo je IDENTIČAN obrazac kao 6-1 NO-DUPLICATE-`<title>`** (base drži jedan `<title>{% block title %}`, child override-uje → nikad dva `<title>`). AC6 count-test zaključava (og:title 1×, canonical 1×, title 1×, og:image 1×).
  - **extra_head reconciliation:** 6-1 detail strane su imale `{% block extra_head %}{% seo_head obj %}{% endblock %}`. 6.3 SELI `seo_head` iz `extra_head` u `social_meta` (i base ga sad default-uje). `extra_head` OSTAJE definisan u base (za druge per-page head potrebe) ali detail strane više NE stavljaju seo_head u njega → canonical+og:image (koji su bili u extra_head/seo_head) sad žive u social_meta seo_head → **NEMA duplikata** (jedan poziv seo_head po strani, u jednom block-u).

**SM-D2 — OBJ-OPTIONAL SITE-LEVEL FALLBACK (`seo_head(context, obj=None)`).** Tag MORA raditi na strani BEZ objekta (home/listing/search/404) bez 500. Potpis dobija `obj=None` default. Kad `obj is None`:
  - `og:title` = SiteSettings.company_name (`_company_name`).
  - `og:description` = SiteSettings.slogan (`_load_site_settings(context).slogan or ""` — graceful prazan).
  - `og:url` = `request.build_absolute_uri(request.path)` (trenutna strana — `_canonical_url(None, request)`).
  - `og:image` = `request.build_absolute_uri(static("img/og-default.jpg"))` (fallback).
  - `og:type` = "website" (`_og_type(None)` → published_at getattr na None → None → "website").
  - `og:site_name` = company_name.
  Sve vrednosti su site-level (NEMA objekta da se konsultuje) → tag je 100% obj-optional. `_resolve_seometa(None, ...)` već vraća None graceful (6-1) → bezbedno.

**SM-D3 — BEHAVIOR CHANGE + REGRESSION-TEST OWNERSHIP (`og:image` sad UVEK; 2 owned testa).** 6-1 `seo_head` emituje `og:image` SAMO kad `og_image` postoji (`if seo and seo.og_image:`). 6.3 menja: `og:image` je UVEK prisutan (object og_image ili `og-default.jpg` fallback — AC4/AC952) + dodaje pun OG/twitter set. **Ovo LOMI dva 6-1 testa koji asertuju OG-ODSUTNOST:**
  - `apps/blog/tests/test_blog_post_detail.py:435 test_meta_no_open_graph_yet` — asertuje `'property="og:' not in html`. SAD pada (OG prisutan). **6.3 prepisuje** → `test_meta_has_open_graph`: asertuj og:title + og:image PRISUTNI.
  - `apps/seo/tests/test_seo_meta_tag.py:127 test_seo_head_no_og_image_when_unset` — asertuje `'property="og:image"' not in out` kad nema og_image. SAD pada (fallback og:image prisutan). **6.3 prepisuje** → `test_seo_head_og_image_falls_back_to_default`: asertuj og:image PRISUTAN + sadrži `og-default.jpg`.
  - `test_seo_head_emits_og_image_when_set` (`:113`) OSTAJE GREEN (object og_image se i dalje koristi; sad nije jedini izvor og:image).
  Ovo je SVESNA, PLANIRANA evolucija deljenog taga — ne slučajna regresija. 6.3 je VLASNIK (autor menja) tih testova jer mu story-scope direktno menja njihovu pretpostavku (mirror Epic 5 test-ownership lekcija: kad story menja ponašanje koje tuđi test zaključava, TA story prepisuje test).

**SM-D4 — robots.txt sadržaj + endpoint (text/plain, NO-PREFIX).** `apps/seo/views.py:robots_txt(request)` → `render(request, "seo/robots.txt", {"sitemap_url": request.build_absolute_uri(reverse("django.contrib.sitemaps.views.sitemap"))}, content_type="text/plain")`. Template direktive (minimal-correct):
  - `User-agent: *` (svi botovi).
  - `Allow: /` (dozvoli ključne strane — eksplicitno, iako je default).
  - `Disallow: */admin/` (admin je POD i18n_patterns → `/sr/admin/`+`/hu/`+`/en/`; `*/admin/` glob ih sve pokriva; Google podržava `*` u path-u). Alternativa: 3 eksplicitne linije po locale-u — Dev bira.
  - `Disallow: */htmx/` (HTMX partial endpoint-i — search/forms htmx submit URL-ovi; nisu indeks targeti. **C3 — verifikovano `config/urls.py:40-42`: htmx je POD i18n_patterns → stvarni path je `/sr/htmx/...` (NE `/htmx/`).** Zato `Disallow: /htmx/` (root) ne matchuje NIŠTA; MORA biti `*/htmx/` glob (isti obrazac kao `*/admin/`) da pokrije sve locale prefikse. OQ-6 razrešen: `*/htmx/`.)
  - `Sitemap: {{ sitemap_url }}` (apsolutna URL — reverse 6-2 sitemap + build_absolute_uri; NE hardkodovan path; jedini 6-2→6-3 ugovor).
  Registracija: `path("robots.txt", robots_txt, name="robots_txt")` u NO-PREFIX `urlpatterns` (mirror sitemap.xml/i18n-setlang). VAN i18n_patterns → `/robots.txt` (ne `/sr/robots.txt`). Google očekuje robots na root-u.

**SM-D5 — og:type article-vs-website (duck-type `published_at`).** `_og_type(obj)` = `"article" if getattr(obj, "published_at", None) else "website"`. Blog Post ima `published_at` (DateTimeField) → "article". Product/Brand/Subcategory nemaju → "website". obj=None → getattr(None, ...) → None → "website". **Duck-type (NE isinstance/import Post)** — low-coupling, mirror `_display_title` getattr-chain iz 6-1 (seo_meta.py NE treba da zna za blog.Post). Ako ikad neki ne-Post model dobije `published_at`, on bi se tretirao kao article — prihvatljivo (published_at je semantički „objavljen članak" marker; OQ-3 ako zatreba precizniji `get_og_type()` metod na modelu).

**SM-D6 — og:image fallback asset (`static("img/og-default.jpg")` + placeholder) — ⚠️ BLOCKING (PROD 500, NE samo broken preview; SEVERITY KOREKCIJA C6).** OG zahteva sliku za rich preview. Kad objekat nema `SeoMeta.og_image`, fallback = `request.build_absolute_uri(static("img/og-default.jpg"))`. **Asset NE postoji još** (static/img/ ima logo-e ali ne og-default.jpg — verifikovano). Odluka: **Dev dodaje placeholder JPG** (1200×630, brand boja/logo) na `static/img/og-default.jpg` — **OBAVEZNO/BLOCKING, NE nicety**.
  - **PRAVA SEVERITY (C6 — verifikovano `config/settings/production.py:39-44` + `staging.py:25-30`):** prod I staging koriste `whitenoise.storage.CompressedManifestStaticFilesStorage` (`ManifestStaticFilesStorage`). Pod manifest storage, `static("img/og-default.jpg")` za **NEPOSTOJEĆI fajl raise-uje `ValueError: Missing staticfiles manifest entry for 'img/og-default.jpg'` u REQUEST vremenu** (NE samo broken link — hard exception). Pošto site-level OG poziva `static("img/og-default.jpg")` na **SVAKOJ strani** (global `social_meta`), fajl-koji-fali = **SITE-WIDE 500 na SVAKOJ strani u prod/staging**. Dev/test okruženje koristi plain `StaticFilesStorage` (base) → `static()` gradi URL i bez fajla bez greške → **testovi PROLAZE i MASKIRAJU prod-500** (zato fajl MORA fizički postojati pre ship-a, ne samo „URL se gradi").
  - **GREEN faza MORA verifikovati da fajl postoji na disku** (`static/img/og-default.jpg`). Po mogućstvu (jeftino): smoke `collectstatic --noinput` pod manifest storage (`DJANGO_SETTINGS_MODULE=config.settings.staging`/prod) da potvrdi da manifest unos postoji, ILI test koji proverava `(Path(settings.BASE_DIR)/"static/img/og-default.jpg").exists()`.
  - **Pravi brand asset = OQ-1 biznis** (dizajniran 1200×630 OG banner) — TO ostaje OQ. ALI **validan placeholder JPG MORA postojati pre ship-a** (nije OQ — blocking). Placeholder je privremen (kao SiteSettings PLACEHOLDER help-text obrazac iz 3-4); zamena fajla = 0 koda.

**SM-D7 — `_canonical_url(obj, request)` helper ekstrakcija (ARCH-3; canonical + og:url DELE).** 6-1 je imao inline canonical try/except u seo_head (build_absolute_uri(get_absolute_url()) sa NoReverseMatch/AttributeError skip). 6.3 EKSTRAHUJE u `_canonical_url(obj, request)` jer canonical `<link>` I `og:url` MORAJU biti ISTA vrednost (Architect ARCH-3 forward-note iz 6-1). Helper: `obj is None` → `request.build_absolute_uri(request.path) if request else None`; inače `try: build_absolute_uri(obj.get_absolute_url()) except (AttributeError, NoReverseMatch): None`; ako `request is None` → vrati relativnu URL ili None (NE 500 — C7/4.5).
  **C7 — og:url se emituje TAČNO KADA i canonical (NE „uvek"):** `og:url` (i canonical link) se emituju **SAMO kad `_canonical_url` vrati ne-None** — tj. kad je canonical URL razrešiv: `request` prisutan I (`obj.get_absolute_url()` radi, ILI `obj is None` → `request.path`). Kad `_canonical_url` vrati `None` (npr. izolovan tag-unit render BEZ request-a, ILI objekat bez get_absolute_url) → **skip og:url emit** (NE emituj `content=""` prazan tag, NE 500). Ovo ispravlja raniju kontradikciju („og:url se UVEK emituje" vs Task 4.5 koji preskače build_absolute_uri kad request=None). DRY: jedna istina (`_canonical_url`) za canonical I og:url — oba se emituju zajedno ili oba skip-uju (isti uslov). U normalnom full-page render-u (request UVEK prisutan — Django request/response ciklus) → oba se UVEK emituju; skip je samo za request-less unit render.

**SM-D8 — SECURITY: OG/twitter content="" autoescape kroz `format_html` (head injection; mirror 6-1 SAFE pattern).** SVE OG/twitter vrednosti (admin-uneti `SeoMeta.meta_title`/`meta_description`/`og_image.url`, + `_display_title`/`_display_description` koji čitaju model polja) ulaze u `content="..."` atribut u `<head>`. MORAJU biti autoescaped: koristi `format_html('<meta property="og:title" content="{}">', title)` (placeholder `{}` autoescape-uje argument → `"`→`&quot;`, `<`→`&lt;`, `>`→`&gt;`). **NIKAD `|safe` ni `mark_safe` na sirovim vrednostima** (mirror 6-1 SEO1-x SAFE pattern). Attribute-breakout (`">` ili `" onload=`) je escaped → ne može probiti atribut ni injektovati tag u `<head>`. `mark_safe("\n".join(parts))` je bezbedno SAMO zato što su SVI `parts` već `format_html` rezultati (escaped SafeString). robots.txt je `text/plain` → nema HTML konteksta → nema HTML injection; `sitemap_url` je reverse-derived (NE user input) → bezbedan. AC9 test zaključava (XSS payload u meta_title → escaped).

**SM-D9 — FORWARD: 6.3 zaokružuje CORE SEO meta surface; 6.4/6.5/6.6 su zasebni.** 6.3 isporučuje robots.txt + global OG/twitter — time je core indeks/social-preview surface kompletan (sitemap 6-2 + meta/OG 6-1/6-3). **NE over-reach:** 6.4 (Redirect 301 model + middleware), 6.5 (i18n fallback ⓘ tooltip), 6.6 (hreflang HTML `<link>` tagovi + `og:locale`/`og:locale:alternate`) su ZASEBNE story-je. 6.3 NE dodaje Redirect model, NE dodaje fallback marker, NE dodaje hreflang head tagove ni og:locale (OQ-5 defer 6.6). `apps/seo/views.py` koji 6.3 kreira je PRVI seo view — 6.4 dodaje `middleware.py` (NE dira views.py).

## Gotchas

**SEO3-1 — NO-DUPLICATE OG (base site-level vs detail object — JEDAN block, child override).** Najveći hazard: ako bi base.html emitovao site-level OG I detail strana DODATNO emitovala object OG (npr. u zasebnim blokovima ILI seo_head ostane u extra_head a OG u social_meta), dobio bi DVA seta OG → social crawler-i čitaju prvi/zbunjeni preview. REŠENJE: JEDAN `{% block social_meta %}` koji detail strana OVERRIDE-uje (zamenjuje, NE dodaje) — Django block override semantika garantuje jedan set. **seo_head MORA biti SAMO u social_meta block-u (NE i u extra_head)** — preseli ga u celosti. AC6 count-test (og:title==1) zaključava.

**SEO3-2 — obj=None graceful na SVAKOM tipu strane.** `seo_head` se sad zove BEZ objekta na home/listing/search/404. Svaki helper MORA podneti None: `_resolve_seometa(None)` → None (6-1 guard); `_og_type(None)` → "website" (getattr None); `_canonical_url(None, request)` → request.path; title/description fallback na SiteSettings. **NE pozivaj `obj.get_absolute_url()` ni `_display_title(obj)` kad obj=None** — granaj na `if obj is None`. Testirati na strani BEZ objekta (home) da NE 500.

**SEO3-3 — seo_head BEHAVIOR CHANGE lomi 2 owned testa (regression-aware).** `og:image` sad UVEK prisutan → `test_meta_no_open_graph_yet` + `test_seo_head_no_og_image_when_unset` PADAJU. To je OČEKIVANO (SM-D3) — 6.3 ih prepisuje (Task 8). Dev NE „popravlja" seo_head da prođu stari testovi; TEA prepisuje testove. Ako iko vidi te 2 fail-ova bez Task-8 rewrite-a, to je nedovršen Task 8, NE bug u seo_head.

**SEO3-4 — og-default.jpg asset MORA postojati (placeholder) — ⚠️ PROD SITE-WIDE 500, NE samo broken preview (C6 SEVERITY KOREKCIJA).** `static("img/og-default.jpg")` u **dev/test** (plain `StaticFilesStorage`) gradi URL string i bez fajla → testovi prolaze (MASKIRA problem). ALI u **prod I staging** (`CompressedManifestStaticFilesStorage` — `production.py:39-44`/`staging.py:25-30`), `static()` za NEPOSTOJEĆI fajl **raise-uje `ValueError: Missing staticfiles manifest entry` u REQUEST vremenu** — NE 404 broken link, nego hard exception. Pošto site-level OG zove `static("img/og-default.jpg")` na SVAKOJ strani → fajl-koji-fali = **SITE-WIDE 500 na CELOM sajtu u prod/staging**. Dev MORA dodati placeholder JPG (Task 7 — BLOCKING) i verifikovati da fajl postoji na disku (collectstatic smoke pod manifest storage). Bez fajla: prod = svaka strana 500. (SM-D6; pravi brand banner = OQ-1.)

**SEO3-5 — og:url == canonical (reuse `_canonical_url`); oba se emituju ZAJEDNO ili oba SKIP (C7).** og:url i canonical link MORAJU biti ISTA apsolutna URL (Google/Facebook best practice). Oba kroz `_canonical_url(obj, request)` — izračunaj JEDNOM, NE računaj URL dvaput različito. **Oba se emituju SAMO kad `_canonical_url` vrati ne-None** (request prisutan I canonical razrešiv); kad vrati None (request=None izolovan render, ili obj bez get_absolute_url) → **oba SKIP** (NE prazan `og:url content=""`, NE 500). NIJE „og:url se uvek emituje" — vezan je za isti uslov kao canonical (C7). Za obj=None sa request-om (normalan full-page render) → oba = request.path (emituju se). (ARCH-3/SM-D7.)

**SEO3-6 — `format_html` autoescape za head injection (NIKAD `|safe`).** SVE OG/twitter vrednosti idu kroz `format_html('...content="{}"...', value)` — placeholder `{}` autoescape-uje. `mark_safe("\n".join(parts))` na KRAJU je bezbedno jer su parts već escaped SafeString. **NIKAD ne stavljaj sirov `seo.meta_title` u f-string pa `mark_safe`** (to bi bio attribute-breakout XSS u `<head>`). Mirror 6-1 SEO1-x. AC9 lock.

**SEO3-7 — robots.txt text/plain + NO-PREFIX.** `content_type="text/plain"` (NE default text/html — botovi očekuju plain). Registracija u NO-PREFIX `urlpatterns` (uz sitemap.xml) — ako se stavi u i18n_patterns, postaje `/sr/robots.txt` a `/robots.txt` daje 404 (bot ga ne nalazi). Mirror 6-2 SM2-3 sitemap NO-PREFIX. AC1 test: `/robots.txt`→200, `/sr/robots.txt`→404.

**SEO3-8 — og:type duck-type (NE import Post).** `_og_type` koristi `getattr(obj, "published_at", None)` — NE `isinstance(obj, Post)` (to bi uvelo blog import u seo_meta.py → coupling). Post ima published_at → article. Mirror `_display_title` getattr-chain low-coupling (SM-D5). obj=None bezbedno (getattr None → None → website).

**SEO3-9 — extra_head reconciliation (seo_head SELI iz extra_head u social_meta).** 6-1 detail strane: `{% block extra_head %}{% seo_head obj %}{% endblock %}`. 6.3: seo_head se MESTI u `{% block social_meta %}` (i base ga default-uje site-level). Ako bi seo_head ostao i u extra_head I bio u social_meta → DVOSTRUKI canonical+og:image (jer seo_head emituje canonical). MORA se PRESELITI (ukloniti iz extra_head, staviti u social_meta). Ako detail strana nema drugi extra_head sadržaj, extra_head override se uklanja iz te strane (base default prazan extra_head ostaje). SEO3-1 NO-DUPLICATE direktno zavisi od ovog.

**SEO3-10 — `static()` import u template tag-u.** `seo_head` (Python tag) gradi og:image fallback URL kroz `from django.templatetags.static import static` (NE `{% static %}` template tag — to je za šablone). `static("img/og-default.jpg")` vraća relativnu URL (`/static/img/og-default.jpg`); `request.build_absolute_uri(...)` je čini apsolutnom. Bez build_absolute_uri OG image bi bio relativna URL → social crawler-i traže apsolutnu.

**SEO3-11 — Twitter Card mirror og (NE duplo računaj).** twitter:title/description/image su ISTE vrednosti kao og:title/description/image. Izračunaj title/desc/image JEDNOM, reuse za oba seta. twitter:card="summary_large_image" je statički string (format_html bez argumenta ili literal — bezbedan).

**SEO3-12 — robots `*/admin/` + `*/htmx/` glob + i18n path (C3).** Admin I htmx su POD i18n_patterns (`/sr/admin/`, `/sr/htmx/...`) — NE root `/admin/` ni `/htmx/`. `Disallow: */admin/` + `Disallow: */htmx/` (glob `*`) pokrivaju sve locale prefikse u jednoj liniji svako. **NE `/htmx/` (root) — taj path NE postoji (htmx je prefiksovan: `config/urls.py:40-42` search+forms u i18n_patterns) → bila bi no-op koja ne blokira ništa (C3).** Isto za `/admin/` → no-op (admin je `config/urls.py:37` u i18n_patterns). `*` mid-path glob podržavaju Googlebot/Bingbot (target crawler-i). Verifikovano oba pod i18n_patterns.

**SEO3-13 — coming-soon / not-overriding strane dobijaju SITE-LEVEL OG (OČEKIVANO, NE bug; C5).** Strane koje NE override-uju `{% block social_meta %}` (npr. `brands/brand_coming_soon.html` noindex coming-soon, home, listing, search) dobijaju base **site-level** OG (og:title=company_name, og:description=slogan, og:image=og-default, og:type=website). Konkretno coming-soon (noindex): `noindex` meta upravlja INDEKSIRANJEM (search engine), NE social scraper-ima — pa site-level OG na noindex strani je VALIDAN (izlaže samo javne company info: ime/slogan/default sliku; bez brand-specifičnih detalja). **Dev NE flag-uje ovo kao bug.** Buduća story sme `brand_coming_soon` da override-uje `social_meta` sa brand objektom (bogatiji preview) — NIJE 6.3 scope.

## Open Questions

**OQ-1 — og-default.jpg brand asset (biznis).** 6.3 dodaje PLACEHOLDER `static/img/og-default.jpg` (1200×630). **Pravi brand OG banner (dizajniran, sa logom/sloganom)** = biznis isporučuje. Placeholder je privremen (kao SiteSettings PLACEHOLDER help-text 3-4). Zameniti fajl kad biznis isporuči — 0 koda (ista putanja).

**OQ-2 — og:image dimenzije/validacija?** Facebook/Twitter preporučuju 1200×630 (1.91:1). 6.3 NE validira dimenzije ni resize-uje (`og_image` se uzima kako jeste). **SM odluka: NE runtime validacija** (YAGNI; preporuka = admin help-text/biznis briga). Ako social preview bude loš (pogrešne dimenzije), 6.x može dodati help-text ili sorl-thumbnail resize na og_image. NE-blocking.

**OQ-3 — og:type beyond article/website (precizniji `get_og_type()` metod)?** 6.3 koristi duck-type `published_at` → article/website. OG ima više tipova (product, profile, video). **SM odluka: SAMO article/website** (AC traži samo Post=article, ostalo=website). Ako biznis želi `og:type=product` za Product (sa og:product:price itd.), to je 6.x enhancement (model bi dobio `get_og_type()` metod — duck-type `getattr(obj, "get_og_type", None)` rung pre published_at). NE-blocking.

**OQ-4 — per-page `<meta name="robots" content="noindex">` na search/htmx/filter strane?** robots.txt Disallow pokriva file-level (admin/htmx). Per-page `noindex` meta (npr. na search rezultatima sa query param, paginiranim listing-ima) je finija kontrola. **SM odluka: DEFER** (AC ne traži; robots.txt Disallow je dovoljan za v1; per-page noindex je 6.x SEO polish ako Search Console pokaže thin-content indeksiranje). NE-blocking.

**OQ-5 — og:locale + og:locale:alternate (i18n OG)?** OG podržava `og:locale` (npr. sr_RS) + `og:locale:alternate` (hu_HU, en_US) za multi-jezični preview. **SM odluka: DEFER do 6.6** (hreflang HTML tagovi su 6.6 — og:locale je isti i18n-locale surface; AC951 traži samo OG core set, ne locale alternate). 6.6 dodaje hreflang `<link>` + og:locale zajedno (jedan i18n-head deliverable). NE-blocking za 6.3.

**OQ-6 — robots Disallow htmx prefiks tačan? → RAZREŠENO (C3): `*/htmx/` glob.** Task 1.2 je ranije imao `Disallow: /htmx/` što pretpostavlja root prefiks. **Verifikovano `config/urls.py:40-42`:** htmx URL-ovi (search `htmx/pretraga/` 2.13 + forms `htmx/forme/...` 4.2) su UNUTAR `i18n_patterns` bloka → stvarni path je `/sr/htmx/...`, `/hu/htmx/...`, `/en/htmx/...`. `Disallow: /htmx/` (root) NE matchuje ništa. **Odluka: koristi `Disallow: */htmx/` (glob `*`, isti obrazac kao `*/admin/`)** — pokriva sve locale prefikse. (htmx fragmenti ionako nemaju `<head>`/canonical pa ih botovi retko indeksiraju samostalno; ali glob je sad tačan, ne no-op.) NE-blocking za AC1 (admin Disallow + Sitemap su obavezni; htmx je dodatak ali sad ispravan).

## Owned Regression Tests

> **6.3 menja ponašanje deljenog `seo_head` taga (BEHAVIOR CHANGE — SM-D3) → VLASNIK je 2 postojeća testa koja asertuju OG-ODSUTNOST. TEA ih prepisuje u istom story-ju (mirror Epic 5 test-ownership lekcija: story koja menja ponašanje koje tuđi test zaključava — prepisuje taj test).**

| Test (file:line) | Stara asertacija (6-1) | Nova asertacija (6.3) | Razlog |
|---|---|---|---|
| `apps/blog/tests/test_blog_post_detail.py:435` `test_meta_no_open_graph_yet` | `assert 'property="og:' not in html` (5-3 NEMA OG) | preimenovati → `test_meta_has_open_graph`: `assert 'property="og:title" in html` I `'property="og:image"' in html` | BEHAVIOR CHANGE: OG sad GLOBALNO prisutan na svakoj strani (AC2/AC951). |
| `apps/seo/tests/test_seo_meta_tag.py:127` `test_seo_head_no_og_image_when_unset` | `assert 'property="og:image"' not in out` (bez og_image → nema og:image) | preimenovati → `test_seo_head_og_image_falls_back_to_default`: `assert 'property="og:image"' in out` I `"og-default.jpg" in out` | BEHAVIOR CHANGE: og:image UVEK prisutan sa fallback-om (AC4/AC952/SM-D3). |
| `apps/seo/tests/test_head_integration.py:74` `test_canonical_present_once_in_full_head` | `_HARNESS` (`:26-32`) override-uje `{% block extra_head %}{% seo_head obj %}{% endblock %}` (a NE `social_meta`); asertuje TAČNO 1 `rel="canonical"` | **AŽURIRATI `_HARNESS`** da mirror-uje stvarnu detail-template migraciju (SEO3-9): override-uje `{% block social_meta %}{% seo_head obj %}{% endblock %}` (NE `extra_head`) → tačno JEDAN `seo_head` poziv → TAČNO 1 canonical. Asertacija (`== 1`) NEPROMENJENA. | **GREEN-BLOCKER (C1):** posle 6.3 base.html ima `{% block social_meta %}{% seo_head %}{% endblock %}` (site-level, obj=None) koji TAKOĐE emituje canonical; ako harness ostane na `extra_head` → DVA canonical-a (base social_meta default + harness extra_head seo_head) → test RED. Harness MORA preseliti seo_head iz `extra_head` u `social_meta` override (NE-dupli emit; isti SEO3-9 reconciliation kao stvarne detail strane). |

> **Nova `_HARNESS` forma (C1 — TEA ažurira u Task 8):**
> ```python
> _HARNESS = (
>     "{% extends 'base.html' %}\n"
>     "{% load seo_meta %}\n"
>     "{% block title %}{% seo_title obj %}{% endblock %}\n"
>     "{% block meta_description %}{% seo_meta_description obj %}{% endblock %}\n"
>     "{% block social_meta %}{% seo_head obj %}{% endblock %}\n"  # ← BILO extra_head; SADA social_meta (mirror SEO3-9 detail migracija)
> )
> ```
> Razlog: posle 6.3 base.html default-uje `{% block social_meta %}{% seo_head %}{% endblock %}` (obj=None). Ako harness drži seo_head u `extra_head` (NE override-uje `social_meta`), base site-level seo_head OSTAJE → DVA seo_head poziva → 2 canonical, 2 og:image → svi NO-DUPLICATE/canonical-once asserti RED. Selidbom seo_head u `social_meta` override → child zamenjuje base default → tačno JEDAN seo_head → tačno 1 canonical (asertacija ostaje `== 1`). Ovo je IDENTIČAN obrazac koji stvarne detail strane primenjuju (Task 6 / SEO3-9).
>
> **`test_exactly_one_title_tag` (`:44`) OSTAJE GREEN** — `seo_head` NE emituje `<title>` (emituje SAMO canonical + og/twitter property/name meta tagove); jedini `<title>` dolazi iz `{% block title %}{% seo_title obj %}` (base-ov jedan `<title>` block). Selidba seo_head iz extra_head u social_meta NE menja broj `<title>` tagova (oba block-a su odvojena od `title`). Slično `test_exactly_one_meta_description_tag` (`:61`) OSTAJE GREEN (seo_head NE emituje `<meta name="description">`). **POVUČENA bilo kakva tvrdnja „svi head_integration testovi prežive bez izmene"** — `test_canonical_present_once_in_full_head` IZRIČITO zahteva harness ažuriranje (gore); samo title/desc-count testovi prežive bez izmene.

**OSTAJE GREEN (NE owned, ali regression-relevantno):**
- `apps/seo/tests/test_seo_meta_tag.py:113 test_seo_head_emits_og_image_when_set` — object og_image se i dalje koristi kad postoji (sad nije JEDINI izvor og:image; `'property="og:image"' in out` i dalje važi). Opciono pojačati da asertuje upload path (NE og-default) kad og_image set.
- `apps/seo/tests/test_seo_meta_tag.py:104-109` (seo_head NE emituje `<title>`/`<meta name="description">`) — OSTAJE (SM-D2 6-1; OG NIJE `<title>`/`name="description"` — to su `property="og:*"`/`name="twitter:*"`; NO-DUPLICATE-`<title>` očuvan; AC6).
- `apps/seo/tests/test_seo_meta_tag.py:134 canonical graceful skip` + i18n canonical prefix (`test_seo_meta_tag.py:172` + `test_seo_i18n.py:78`) — OSTAJE (`_canonical_url` ekstrakcija ne menja ponašanje; Task 2.2 regression). **Ovi testovi render-uju IZOLOVAN tag (`_render` — JEDAN seo_head poziv, NE kroz base.html)** → globalni `social_meta` ih NE dira (nema base+child interakcije).
- `apps/seo/tests/test_head_integration.py:44 test_exactly_one_title_tag` + `:61 test_exactly_one_meta_description_tag` — OSTAJU GREEN i POSLE harness ažuriranja (C1): `seo_head` NE emituje `<title>`/`<meta name="description">` (samo canonical + og/twitter property/name tagove), pa selidba seo_head extra_head→social_meta NE menja broj `<title>`/`description` tagova (1×). **(NB: `test_head_integration.py:74 test_canonical_present_once_in_full_head` JE OWNED — vidi tabelu gore; zahteva harness override `social_meta` umesto `extra_head`.)**
- `apps/blog/tests/test_blog_post_detail.py` `<title>`/`name="description"` testovi (5-3) — OSTAJU (seo_title/seo_meta_description tagovi NEPROMENJENI).

> **RE-SCAN rezultat (C1 (c) — full-suite grep za canonical-count / og-count / full-page base.html head asercije koje bi globalni `social_meta` slomio):** Pronađena su TAČNO 3 testa koja (i) render-uju full-page kroz base.html ILI asertuju OG-odsutnost, I (ii) globalni site-level `social_meta` ih lomi: `test_blog_post_detail.py:435` (no-og — owned), `test_seo_meta_tag.py:127` (no-og-image — owned), `test_head_integration.py:74` (canonical-once full-head — owned, C1). **Nema dodatnih.** Svi ostali `og:`/`canonical`/`count(` testovi su ILI izolovan-tag render (`_render` — JEDAN seo_head, ne kroz base.html: `test_seo_meta_tag.py` :88/:113/:135/:172, `test_seo_i18n.py` :78) ILI ne diraju OG/canonical (blog reverse/url testovi, footer-news count testovi — count na blog:detail linkovima, NE na og:/canonical). Detail-view testovi (`test_views_brand_detail.py`/`test_views_product_detail.py`/`test_blog_post_detail.py` ostali) NE asertuju og/canonical count → ne lome se.

## Testing

> **TEA piše SVE testove PRE implementacije (RED). Dev NE piše testove.** Mirror `apps/seo/tests/` (6-1/6-2) + `apps/blog/tests/` layout. Test render kroz `_render`/`_render_shared_request` (RequestFactory + Context sa request — postojeći seo conftest helper) za tag-level testove; Django test `client` za `/robots.txt` + full-page OG testove. **OWNED rewrite (Task 8) = regression-aware (2 testa prepisana — SM-D3).**

- **`test_robots_txt.py`** (AC1) — GET `/robots.txt`→200; `Content-Type` startswith `text/plain`; telo sadrži `User-agent: *`, `Allow: /`, `Disallow:`(admin glob/locale), `Sitemap: http://testserver/sitemap.xml` (== `build_absolute_uri(reverse("django.contrib.sitemaps.views.sitemap"))`); `reverse("robots_txt")`==`/robots.txt`; `/sr/robots.txt`→404 (NO-PREFIX; SEO3-7). (Host=testserver iz test client — NE hardkoduj domen, asertuj sufiks `/sitemap.xml`.)
- **`test_open_graph.py`** (AC2/AC8) — detail strana (product/post): `<head>` ima og:title/description/image/type/url (5 core). SeoMeta(meta_title="Custom") → og:title sadrži "Custom"; bez SeoMeta → og:title sadrži `_display_title | company` (fallback). og:description: SeoMeta.meta_description ili `_display_description` fallback (CRIT-1 očuvan — prazan perex Post pada na title).
- **`test_twitter_card.py`** (AC3) — strana ima `twitter:card`=summary_large_image + twitter:title/description/image; twitter vrednosti == og vrednosti (mirror).
- **`test_og_fallback.py`** (AC4/AC5) — (a) detail bez og_image → og:image SADRŽI `og-default.jpg`; sa og_image (png_upload) → og:image SADRŽI upload path (NE og-default). (b) SITE-LEVEL: render strane BEZ objekta (`{% seo_head %}` bez arg — preko base.html home render ILI `_render("{% load seo_meta %}{% seo_head %}", {})`) → og:title=company_name, og:description=slogan, og:type=website, og:url sadrži request path, og:image=og-default; NE 500 kad slogan prazan (SiteSettings.slogan="" default).
- **`test_og_no_duplicate.py`** (AC6 — NO-DUPLICATE LOCK) — detail full-page render: `html.count('property="og:title"')`==1; `html.count('rel="canonical"')`==1; `html.count("<title")`==1; `html.count('property="og:image"')`==1. (Dokazuje child block override NE duplira base site-level OG — SM-D1.)
- **`test_og_type.py`** (AC7) — Post detail → og:type content="article"; Product/Brand detail → "website"; site-level (obj=None) → "website". (Duck-type published_at — SEO3-8.)
- **`test_og_security.py`** (AC9 — SECURITY LOCK) — SeoMeta.meta_title sa XSS payload (`'"><script>alert(1)</script>'` ili `'" onload="x'`) → render → payload je HTML-escaped u `content="..."` (`&quot;`/`&lt;`/`&gt;` prisutni; `<script>` NIJE sirovo; `"` NE probija atribut). NIGDE `|safe`. (format_html autoescape — SEO3-6.)
- **OWNED rewrite (Task 8 — SM-D3):** `test_blog_post_detail.py:435` → `test_meta_has_open_graph` (OG prisutan); `test_seo_meta_tag.py:127` → `test_seo_head_og_image_falls_back_to_default` (og:image fallback prisutan). (Vidi Owned Regression Tests tabelu.)
- **Regression:** `apps/seo/tests/` (6-1 seo_head/title/desc + 6-2 sitemap) + `apps/blog/tests/` MORAJU ostati GREEN OSIM 2 owned (namerno prepisana). `makemigrations --check --dry-run` → „No changes detected" (0 migracija lock). `seo_head` NE emituje `<title>`/`name="description"` (6-1 test :104 ostaje).
- **Manualni QA (NE-automated):** server → GET /robots.txt (vizuelno User-agent/Disallow/Sitemap); GET home + detail strane → view-source potvrdi OG/twitter; propusti detail URL kroz Facebook Sharing Debugger + Twitter Card Validator (rich preview render). Dokumentuj u review.

### TEA napomene za pisanje testova

- **Site-level OG test (obj=None):** može se testirati ILI full-page (GET home `/sr/` → base.html social_meta default render) ILI direktno tag (`_render("{% load seo_meta %}{% seo_head %}", {})` — bez objekta). Direktan tag test je brži i izoluje obj-optional granu (SM-D2). Full-page test dokazuje base.html wiring (AC2 „svaka strana").
- **NO-DUPLICATE count test:** koristi `html.count(...)` na full-page detail render-u (kroz `client.get(detail_url)`), NE na izolovanom tag render-u (tag sam emituje jedan set; duplikat hazard je base+child interakcija → MORA full-page kroz base.html).
- **Security test:** SeoMeta.meta_title je modeltranslation polje — set `meta_title_sr` (aktivni locale `activate("sr")`). Payload u meta_title, render kroz seo_head/full-page, asertuj escaped u og:title content. Mirror 6-1 SEO1-x security testovi (ako postoje u test_seo_meta_tag.py).
- **Sitemap URL u robots:** asertuj `"/sitemap.xml" in body` + da je apsolutna (`"http://testserver/sitemap.xml" in body` ILI da počinje `http`); reverse-based (NE hardkodovan). build_absolute_uri daje testserver host (RequestSite-style; 6-2 SM2-2).
- **og:image fallback test:** `_isolate_media_root` (autouse conftest fixture) izoluje MEDIA_ROOT — png_upload za object og_image; bez upload-a → fallback og-default.jpg (static, NE media). Asertuj `"og-default.jpg" in og_image_content`.
- **og:type test — duck-type:** Post fixture ima `published_at` (set kroz `_published` helper); Product/Brand fixture nema → "website". obj=None → "website". NE import Post u test radi isinstance — asertuj content string.

## Reference

- **epics.md:941-952** — Story 6.3 ACs (robots.txt view + sitemap link; base.html OG og:title/description/image/type/url + Twitter Card iz `{% seo_meta object %}`; robots.txt validan format dozvoljava ključne strane + navodi sitemap.xml; svaka strana ima OG+Twitter u `<head>`; og:image fallback `static/img/og-default.jpg` ako SeoMeta nema og_image).
- **epics.md:954-965** — Story 6.4 (Redirect 301 model + middleware) — granica; 6.3 NE dodaje model/middleware (`apps/seo/views.py` je PRVI seo view; 6.4 dodaje middleware.py).
- **epics.md:967+** — Story 6.5 (i18n fallback ⓘ tooltip) — granica.
- **apps/seo/templatetags/seo_meta.py** — 6-1 implementacija: `seo_head` (canonical + og:image-SAMO-kad-set → 6.3 EXTEND obj-optional + pun OG + uvek og:image); `seo_title`/`seo_meta_description` (STRING tagovi — NEPROMENJENI; OG reuse fallback); `_resolve_seometa` (per-request keš), `_display_title`/`_display_description` (getattr-chain duck-type — mirror za `_og_type`), `_company_name`/`_load_site_settings` (SiteSettings keš); `format_html` SAFE pattern (SEO1-x → SM-D8); canonical graceful NoReverseMatch/AttributeError skip (→ `_canonical_url` ekstrakcija ARCH-3/SM-D7).
- **apps/seo/tests/test_seo_meta_tag.py:104-134** — 6-1 tag testovi: seo_head NE emituje title/desc (:104 ostaje); og:image emit-when-set (:113 ostaje GREEN); **og:image no-when-unset (:127 OWNED rewrite — SM-D3)**; canonical graceful skip (:134 ostaje). `_render`/`_render_shared_request` helperi (RequestFactory + Context).
- **apps/blog/tests/test_blog_post_detail.py:435** — **`test_meta_no_open_graph_yet` (OWNED rewrite — SM-D3):** `'property="og:' not in html` → OG prisutan. Susedni `<title>`/`name="description"` testovi (:400-431) OSTAJU (seo_title/seo_meta_description NEPROMENJENI).
- **templates/base.html:10-16** — `<head>`: `{% block meta_description %}` (:10), `{% block title %}` (:11), `{% block extra_head %}` (:16). 6.3 dodaje `{% load seo_meta %}` (vrh) + `{% block social_meta %}{% seo_head %}{% endblock %}` (POSLE :11, oko :16). NO-DUPLICATE-`<title>` obrazac (6-1 SM-D2) → mirror za social_meta.
- **templates/products/product_detail.html:8** / **brands/brand_detail.html:8** / **blog/post_detail.html:8** — `{% block extra_head %}{% seo_head <obj> %}{% endblock %}` → 6.3 SELI u `{% block social_meta %}{% seo_head <obj> %}{% endblock %}` (SEO3-9 reconciliation). seo_title/seo_meta_description blokovi (:4/:6) NEPROMENJENI.
- **config/urls.py:22-33** — NO-PREFIX `urlpatterns` (`i18n/setlang/` :24 + `sitemap.xml` :27-32). 6.3 dodaje `path("robots.txt", robots_txt, name="robots_txt")` ovde (VAN i18n_patterns; SEO3-7). admin/ (:37) je POD i18n_patterns → robots `*/admin/` glob (SEO3-12).
- **apps/seo/sitemaps.py** (6-2) — `sitemap` URL name `django.contrib.sitemaps.views.sitemap` (registrovan config/urls.py:31) → robots `Sitemap:` linija ga reverse-uje (jedini 6-2→6-3 ugovor; SM-D4).
- **apps/pages/models.py:31-40** — SiteSettings.company_name (default "Ćorić Agrar"; og:site_name + site-level og:title fallback) + .slogan (:36, blank=True; site-level og:description; modeltranslation translatable). `SiteSettings.load()` (:126) per-request keš (6-1 `_load_site_settings`).
- **apps/blog/models.py:176** — Post.published_at (DateTimeField null/blank; og:type="article" duck-type marker — SM-D5/SEO3-8); :207 get_absolute_url reverse("blog:detail") (og:url/canonical).
- **static/img/** — postoji `coric-agrar-logo-transp-200.png` + light variant; **`og-default.jpg` NE postoji** → 6.3 dodaje placeholder (SM-D6/OQ-1; Task 7).
- **6-1-seometa-model-per-page-admin.md** — SeoMeta GFK model (meta_title/meta_description/og_image translatable; UniqueConstraint content_type+object_id); SEO1-x gotchas (format_html SAFE, GFK no-GenericRelation, duck-typed fallback CRIT-1); ARCH-3 forward-note (canonical/og:url shared helper → SM-D7).
- **6-2-sitemap-auto-generation-sa-hreflang.md** — stabilna /sitemap.xml NO-PREFIX URL (SM-D8 forward: „robots.txt referencira /sitemap.xml lokaciju"); NO-PREFIX urlpatterns obrazac (SM-D2/SM2-3 → robots mirror).
