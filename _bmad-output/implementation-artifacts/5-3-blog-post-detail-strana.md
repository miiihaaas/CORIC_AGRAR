---
story_id: "5.3"
story-key: 5-3-blog-post-detail-strana
title: Blog Post Detail Strana
status: ready-for-dev
epic: 5
epic_num: 5
epic_title: Blog (Priče sa polja)
module: blog
created: 2026-06-05
last_modified: 2026-06-05
complexity: H
author: Mihas (SM autonomous; TREĆA story Epic 5 — Blog „Priče sa polja". Javna POST DETAIL strana `/sr/blog/<slug>/` koja OBOGAĆUJE 5-2 placeholder `BlogPostDetailView`. KLJUČNO: 5-3 NE prepisuje view — PROŠIRUJE ga (get_queryset → `Post.published.select_related("category","author").prefetch_related("tags")`; novi get_context_data za „Slične objave"); 5-2 detail testovi (200/draft-404/future-404/no-oracle) OSTAJU ZELENI. DODAJE 2 nove ARHIVE view-a (`BlogCategoryView`/`BlogTagView` — ListView mirror BlogIndexView listing/paginacija/HTMX, REUSE `_post_results.html`/`_post_card.html`) + 2 URL-a (`blog:category` `blog/kategorija/<slug>/` + `blog:tag` `blog/tag/<slug>/`) registrovana PRE catch-all `blog/<slug>/` (url-ordering — inače „kategorija"/„tag" captured kao post slug). SECURITY-CRITICAL ODLUKA (SM-D1): body render OSTAJE plain `|linebreaks` (auto-escape — XSS-safe); rich-text/inline-slike/video-embed DEFEROVAN na Epic 8.7 (WYSIWYG + sanitizacija) — NIKAD raw `|safe` (stored-XSS). Draft-not-leaked SVUDA (detail + obe arhive + Slične objave = `Post.published`). NEMA model promene/migracije, NEMA novog dep. RISK TIER: HIGH — body-render XSS granica + 2 nove javne view + url-ordering-before-catch-all + draft-not-leaked na 4+ puta + N+1 na Slične-objave/arhivama.)
depends_on:
  - 5-1-blogpost-category-tag-modeli-admin-stub              # Post (body PLAIN TextField, main_image, author FK AUTH_USER_MODEL SET_NULL [može NULL — template MORA guard], category FK SET_NULL, tags M2M, perex, get_absolute_url); Category/Tag modeli; Post.published manager (status='published' AND published_at__lte=now — draft-not-leaked granica)
  - 5-2-blog-index-strana-sa-paginacijom-filter              # BlogPostDetailView PLACEHOLDER (model=Post, get_queryset=Post.published.select_related("category"), context_object_name="post", template blog/post_detail.html, draft/future→404) koju 5-3 OBOGAĆUJE; apps/blog/urls.py (app_name="blog", blog:index, blog:detail blog/<slug>/); BlogIndexView listing/paginacija/HTMX/categories_for_dropdown/active_filters/_post_results.html/_post_card.html/_blog_empty_state.html pattern (arhive REUSE); blog-listing.css/coric-blog-card; test_blog_urls.py (detail-200/draft-404/future-404/no-oracle — OSTAJU ZELENI)
  - 2-7-product-detail-strana                                # ProductDetailView DetailView + get_context_data similar_products (manual/auto fallback, related_product__is_published=True, exclude(pk=...), [:LIMIT]) + product_detail.html „Slične objave" sekcija (_similar_products.html) + meta block override PRECEDENT (mirror za blog Slične objave + detail layout)
  - 2-3-product-image-thumbnail-pipeline                     # {% responsive_picture %} sorl-thumbnail inclusion tag (main_image srcset + loading=lazy) — REUSE za detail naslovnu sliku + Slične-objave kartice
---

# Story 5.3: Blog Post Detail Strana

Status: ready-for-dev

## Opis

As a **posetilac sajta Ćorić Agrar**,

I want **da otvorim pojedinačnu blog objavu `/sr/blog/<slug>/` koja prikazuje naslovnu sliku, meta (datum + autor + kategorija), naslov, telo teksta, sekciju „Slične objave" iz iste kategorije i social-share dugmad, sa klikabilnim linkovima na kategorija/tag arhive**,

so that **mogu da pročitam celu „priču sa polja" i lako podelim korisnu informaciju ili pronađem srodne objave**.

Ovo je **TREĆA story Epic 5 (Blog — Priče sa polja)**. 5-2 je položio JAVNI sloj: index stranu `/sr/blog/` + `apps/blog/urls.py` (`blog:index` + `blog:detail`) + **MINIMALAN placeholder `BlogPostDetailView`** (render naslov+datum+telo iz `Post.published`; draft/future → 404). 5-3 **OBOGAĆUJE** taj placeholder do PUNE detail strane i dodaje **kategorija/tag arhive** strane.

**KRITIČNO — 5-3 PROŠIRUJE, NE PREPISUJE (SM-D2):** `BlogPostDetailView` ostaje ista klasa — 5-3 SAMO (a) proširuje `get_queryset()` da doda `select_related("author")` + `prefetch_related("tags")` (5-2 forward-note — sprečava N+1 kad detail renderuje autora/tagove) i (b) dodaje `get_context_data()` za „Slične objave". `context_object_name="post"`, `template_name="blog/post_detail.html"`, `model=Post`, draft/future→404 OSTAJU NEPROMENJENI. **5-2 detail testovi (`test_blog_urls.py` — detail-200/draft-404/future-404/context_object_name=post/no-oracle) MORAJU OSTATI ZELENI.**

5-3 takođe dodaje **2 nove ARHIVE view-a** (`BlogCategoryView` + `BlogTagView`) koje mirroruju `BlogIndexView` listing pattern (ListView + paginacija + HTMX swap + REUSE `_post_results.html`/`_post_card.html`) filtrirajući `Post.published` po `category__slug` / `tags__slug`, sa URL-ovima registrovanim **PRE catch-all `blog/<slug>/`** (url-ordering odluka SM-D3).

### IN SCOPE (šta ova story isporučuje)

1. **`apps/blog/views.py` — `BlogPostDetailView` OBOGAĆENJE (SM-D2; NE rewrite):**
   - `get_queryset()` → proširi 5-2 `Post.published.select_related("category")` u **`Post.published.select_related("category", "author").prefetch_related("tags")`** (autor meta + tag linkovi se renderuju → N+1 lock; 5-2 forward-note IMP-5).
   - `get_context_data()` (NOVO) → **„Slične objave"**: `Post.published.filter(category=post.category).exclude(pk=post.pk)` (iz ISTE kategorije, EXCLUDING current, kroz `Post.published` — draft-not-leaked), `select_related("category")`, ordering najnovije-prvo (Meta default), bounded `[:_SIMILAR_POSTS_LIMIT]` (2-4 — epics.md:889). Ako `post.category` je `None` (SET_NULL) → prazna lista (NE crash). `ctx["similar_posts"]`.
   - NEPROMENJENO: `model=Post`, `context_object_name="post"`, `template_name="blog/post_detail.html"`, draft/future→404 (5-2 placeholder kontrakt).
2. **`apps/blog/views.py` — `BlogCategoryView(ListView)` + `BlogTagView(ListView)` (NOVO; mirror `BlogIndexView`):** `model=Post`, queryset `Post.published.select_related("category")` `.filter(category__slug=<slug>)` / `.filter(tags__slug=<slug>).distinct()`, `paginate_by=10`, `get_template_names()` request.htmx branching (full page vs `_post_results.html`), `Paginator.get_page()` overflow safety, `@vary_on_headers("HX-Request")`. **404 ako kategorija/tag slug ne postoji** (`get_object_or_404(Category, slug=...)` / `Tag` u `setup()`/`get_queryset()` — SM-D4). Kontekst: `count`, kategorija/tag objekat za heading (`archive_object`), prazna-lista grana za empty state.
3. **`apps/blog/urls.py` EDIT — 2 nove rute PRE catch-all (SM-D3):** dodaj `path("blog/kategorija/<slug:slug>/", BlogCategoryView.as_view(), name="category")` + `path("blog/tag/<slug:slug>/", BlogTagView.as_view(), name="tag")` **PRE** `path("blog/<slug:slug>/", BlogPostDetailView..., name="detail")`. ⛔ Redosled je load-bearing — Django resolver iterira; ako su arhive POSLE catch-all-a, `blog/kategorija/X/` bi pokušao da match-uje `blog/<slug>/` sa slug="kategorija" (a `kategorija/X` ne pasuje single `<slug>` segmentu, ali `blog/tag/` analogno) → garantovano registruj arhive PRE detail-a.
4. **`templates/blog/post_detail.html` OBOGAĆENJE (5-2 placeholder → pun detail):** naslovna slika (`{% responsive_picture post.main_image %}` REUSE 2-3, `{% if post.main_image %}` guard), meta linija (datum `|date:"SHORT_DATE_FORMAT"` + autor **`{% if post.author %}` guard** SM-D5 + kategorija link `{% url 'blog:category' slug=post.category.slug %}` `{% if post.category %}` guard), naslov, telo (`{{ post.body|linebreaks }}` — plain auto-escape, SM-D1), tag linkovi (`{% for tag in post.tags.all %}` → `{% url 'blog:tag' slug=tag.slug %}`), „Slične objave" sekcija (`{% if similar_posts %}` → REUSE `_post_card.html`), social-share dugmad (include `_social_share.html`). Meta `{% block title %}`/`{% block meta_description %}` iz `post.title`/`post.perex` (SM-D7).
5. **`templates/blog/partials/_social_share.html` (NOVO — SM-D6):** Facebook / Viber / WhatsApp / Copy-link dugmad; share URL = post apsolutni URL izračunat U VIEW-u (`ctx["share_url"] = request.build_absolute_uri(post.get_absolute_url())`; template `{{ share_url }}` — IMP-2, jer `{{ }}` ne može metodi proslediti argument); egzaktni href-ovi (FB `sharer/sharer.php?u=`, WhatsApp `wa.me/?text=`, Viber `viber://forward?text=` — IMP-3); Copy-link je vanilla JS (NE jQuery); `{% translate %}` aria-label/title pune dijakritike; sticky-left desktop / below-title mobile kroz CSS (SM-D6).
6. **`templates/blog/partials/_similar_posts.html` (NOVO ili inline):** „Slične objave" grid (2-4 kartice REUSE `_post_card.html` — mirror 2-7 `_similar_products.html`); render SAMO `{% if similar_posts %}`.
7. **`templates/blog/blog_archive.html` (NOVO; ili REUSE `blog_index.html` sa heading override):** full-page arhiva (kategorija/tag) — heading „Objave u kategoriji: <ime>" / „Objave sa tagom: <ime>" + `{% include "blog/partials/_post_results.html" %}` (REUSE 5-2 results grid + paginacija + empty state). Filter dropdown se NE prikazuje na arhivi (arhiva JE već filtrirana — SM-D4).
8. **`static/css/components/blog-detail.css` (NOVO; ili dopuna blog-listing.css):** detail layout (naslovna slika, meta, telo prose, Slične-objave grid, social-share sticky-left desktop / below-title mobile responsive — epics.md:890); `var(--token)` (NE magic px). main.css `@import` ako novi fajl.
9. **`static/js/blog-share-copy.js` (NOVO; ili inline `{% block scripts %}`):** Copy-link clipboard (vanilla `navigator.clipboard.writeText`); `coric:` namespace custom event opciono; aria-live najava „Link kopiran" (SM-D6).
10. **i18n** — svi novi string-ovi (meta labeli „Autor"/„Kategorija", „Slične objave", social-share aria-label, arhiva heading-ovi, „Link kopiran") kroz `{% translate %}`/`{% blocktranslate %}` pune dijakritike; `.po` sr/hu/en (`just messages`).

### OUT OF SCOPE (eksplicitno — granice)

- **RICH-TEXT / inline-slike / video-embed render tela (`post.body`)** = **Epic 8.7** (WYSIWYG editor + sanitizacija pipeline). 5-3 render-uje `body` kao **plain `|linebreaks` (auto-escape — XSS-safe)**. epics.md:889 spominje „rich text sa inline slikama i video embed", ALI 5-1 model `body` je PLAIN TextField (5-1 SM-D10), WYSIWYG editor je 8.7. **Rich render NIJE u 5-3 scope-u** — zahtevao bi NOVI dep (bleach/nh3 sanitizacija) + `|safe` (XSS surface). Vidi SM-D1 za punu justifikaciju. ⛔ NIKAD raw `{{ post.body|safe }}` (stored-XSS).
- **SEO/SeoMeta override (OG/twitter/canonical)** = **Epic 6** (6.1 SeoMeta, 6.2 sitemap). 5-3 radi SAMO bazičan `<title>` + `<meta name="description">` iz `post.title`/`post.perex` (block override). epics.md:893 eksplicitno „override-ovi dolaze u Epic 6".
- **Footer „Najnovije vesti" dynamic kolona** = **Story 5-4** (`apps/blog/context_processors.py`). 5-3 NE dira footer.
- **Index filter izmene / nova listing logika** = NE. 5-2 `BlogIndexView`/`_blog_filter.html` NETAKNUT. 5-3 arhive su DEDIKOVANE strane (`/sr/blog/kategorija/X/`), RAZLIČITE od 5-2 index querystring filtera (`/sr/blog/?kategorija=X`) — obe koegzistiraju (5-2 SM-D4 NAPOMENA).
- **Model promene / migracije** = NEMA. 5-1 šema je finalna; 5-3 je čist view/template/url/css/js sloj. `makemigrations --check` MORA „No changes".
- **Novi Python dep** = NEMA (deferral rich-body → NE bleach/nh3; share/copy je vanilla JS). NEMA `uv add`.
- **Komentari/lajkovi/share-count** = NE (nema u epics.md:881-893). Social-share su SAMO outbound dugmad (FB/Viber/WhatsApp/Copy-link).
- **Author profil strana / autor arhiva** = NE (epics.md ne traži). Autor je SAMO meta-linija ime (NULL-guarded SM-D5), bez linka na autor-arhivu.
- **PostAdmin.view_on_site re-enable** = van scope-a (5-2 OQ-3 → 8.7). 5-3 NE dira admin.py.

### Princip

5-3 **OBOGAĆUJE** (NE prepisuje) 5-2 placeholder `BlogPostDetailView`: proširuje `get_queryset()` (`select_related("category","author")` + `prefetch_related("tags")` — N+1 lock kad render-uje autora/tagove) i dodaje `get_context_data()` za „Slične objave" (2-4 published iz iste kategorije, exclude-self, bounded, draft-not-leaked). Dodaje 2 ARHIVE view-a (`BlogCategoryView`/`BlogTagView` mirror `BlogIndexView` + REUSE `_post_results.html`/`_post_card.html`) sa URL-ovima registrovanim PRE catch-all detail-a. Telo render-uje `|linebreaks` (plain auto-escape — NIKAD `|safe`; rich-text=8.7). Autor NULL-guarded (`{% if post.author %}` — SET_NULL FK). Social-share FB/Viber/WhatsApp/Copy-link (Copy = vanilla JS, sticky-left desktop/below-title mobile). Meta title/description iz title+perex (OG=Epic 6). Sve user-facing pune dijakritike; `{% translate %}`/`{% blocktranslate %}`; .po sr/hu/en. ASCII slug u URL-u. NEMA model promene/migracije/novog dep. **Svaka javna query (detail, obe arhive, Slične objave) kroz `Post.published`** — draft-not-leaked granica. NEMA defensive validacije na internim pozivima. NEMA premature abstrakcije.

### Strukturna arhitektura — repository delta

**2 EDIT (views.py + urls.py) + ~4 NEW template-a + 1 NEW/EDIT CSS + 1 NEW JS + 0 migracija + 0 model promene + 0 novi dep.**

| Path | Tip | Razlog |
|---|---|---|
| `apps/blog/views.py` | EDIT (SM-D2) | `BlogPostDetailView` OBOGAĆENJE: `get_queryset()` proširi na `Post.published.select_related("category","author").prefetch_related("tags")`; NOVI `get_context_data()` „Slične objave" (`Post.published.filter(category=self.object.category).exclude(pk=self.object.pk).select_related("category")[:LIMIT]`; `post.category is None` → prazna). NEPROMENJENO: model/context_object_name/template/draft-404. NOVO `BlogCategoryView(ListView)` + `BlogTagView(ListView)` (mirror BlogIndexView: paginate_by=10, get_template_names() htmx branching, Paginator.get_page() overflow, @vary_on_headers; `get_object_or_404(Category/Tag, slug=...)` → 404 nepostojeća; queryset `.filter(category__slug=...)` / `.filter(tags__slug=...).distinct()`; count/archive_object context). `_SIMILAR_POSTS_LIMIT=4` konstanta (mirror 2-7 `_SIMILAR_PRODUCTS_LIMIT`). |
| `apps/blog/urls.py` | EDIT (SM-D3) | Dodaj `path("blog/kategorija/<slug:slug>/", views.BlogCategoryView.as_view(), name="category")` + `path("blog/tag/<slug:slug>/", views.BlogTagView.as_view(), name="tag")` **PRE** `path("blog/<slug:slug>/", ..., name="detail")`. ⛔ url-ordering — arhive PRE catch-all (inače „kategorija"/„tag" segment captured kao post slug). `blog/` index ostaje prvi. |
| `templates/blog/post_detail.html` | EDIT (placeholder → pun detail) | Naslovna slika (`{% if post.main_image %}{% responsive_picture %}{% endif %}` REUSE 2-3), meta (datum + `{% if post.author %}`autor`{% endif %}` SM-D5 + `{% if post.category %}`kategorija link `{% url 'blog:category' slug=post.category.slug %}``{% endif %}`), naslov, telo `{{ post.body|linebreaks }}` (plain — SM-D1; postojeći TODO komentar ažuriraj), tag linkovi `{% for tag in post.tags.all %}{% url 'blog:tag' slug=tag.slug %}{% endfor %}`, `{% include "blog/partials/_social_share.html" %}`, `{% if similar_posts %}{% include "blog/partials/_similar_posts.html" %}{% endif %}`. `{% block title %}`=post.title; `{% block meta_description %}`=`post.perex|default:post.title` (IMP-4 — neprazan; SM-D7). |
| `templates/blog/partials/_social_share.html` | NOVO (SM-D6) | FB/Viber/WhatsApp share linkovi (href sa `{{ share_url }}` iz view-context-a — IMP-2; egzaktni intent URL-ovi FB `sharer/sharer.php?u=` / WhatsApp `wa.me/?text=` / Viber `viber://forward?text=` — IMP-3) + Copy-link dugme (vanilla JS `navigator.clipboard.writeText(share_url)`); `{% translate %}` aria-label/title pune dijakritike; `data-testid`. |
| `templates/blog/partials/_similar_posts.html` | NOVO | „Slične objave" grid (mirror 2-7 `_similar_products.html`): `{% for post in similar_posts %}{% include "blog/partials/_post_card.html" %}{% endfor %}`. Render SAMO `{% if similar_posts %}` (iz parent template-a). |
| `templates/blog/blog_archive.html` | NOVO (ili REUSE blog_index.html) | Full-page arhiva: heading „Objave u kategoriji: <ime>" / „Objave sa tagom: <ime>" (`archive_object`) + `{% include "blog/partials/_post_results.html" %}` (REUSE 5-2). BEZ filter dropdown-a (arhiva je već filtrirana — SM-D4). `{% block title %}`/`meta_description`. |
| `static/css/components/blog-detail.css` (ili dopuna blog-listing.css) | NOVO/EDIT | Detail layout (naslovna slika, meta, telo prose, Slične-objave grid) + social-share sticky-left desktop / below-title mobile (epics.md:890); `var(--token)`. main.css `@import` ako novi fajl. |
| `static/js/blog-share-copy.js` (ili inline scripts blok) | NOVO (SM-D6) | Copy-link `navigator.clipboard.writeText(...)` (vanilla); aria-live „Link kopiran"; `coric:` event opciono. |
| `apps/blog/urls.py` redosled | (vidi gore) | KLJUČNO SM-D3. |
| `apps/blog/tests/test_blog_post_detail.py` | NOVO (TEA) | AC1-AC2 obogaćen detail (slika/meta/autor-NULL/kategorija-link/telo/tagovi/Slične-objave/social/meta). |
| `apps/blog/tests/test_blog_archives.py` | NOVO (TEA) | AC3-AC4 kategorija/tag arhive (Post.published, paginacija, 404 bad slug, url-ordering, draft-not-leaked, HTMX). |
| `apps/blog/tests/test_blog_detail_n_plus_1.py` | NOVO (TEA) | N+1 lock: detail (author/tags/Slične-objave) + arhive assertNumQueries. |
| `locale/{sr,hu,en}/LC_MESSAGES/django.po` | EDIT | Novi string-ovi. `just messages`. |
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | EDIT | `5-3` → `ready-for-dev` (epic-5 ostaje `in-progress`). SM handoff (NIJE deliverable). |

**NETAKNUTO (regression guards):** `apps/blog/models.py`/`managers.py`/`translation.py`/`admin.py` (5-1 — NE menja se); `apps/blog/migrations/` (NEMA nove migracije — `makemigrations --check` MORA „No changes"); `BlogIndexView` + `_blog_filter.html` + `_blog_empty_state.html` (5-2 — NE menja); `test_blog_urls.py` (5-2 detail testovi — **OSTAJU ZELENI**, NE menja se — 5-3 obogaćenje NE sme slomiti detail-200/draft-404/future-404/no-oracle); svi postojeći app-ovi; `pyproject.toml` (NEMA novog dep). **0 migracija, 0 model promene, 0 novi dep.**

## Kriterijumi prihvatanja

**AC1 — `BlogPostDetailView` OBOGAĆEN: slika + meta (datum + autor[NULL-guard] + kategorija-link) + naslov + telo[plain] + tagovi (SM-D2/SM-D5/SM-D1)**

- **Given** 5-2 `BlogPostDetailView` placeholder; published Post sa main_image + published_at + author + category + tags + body
- **When** posetilac otvori `/sr/blog/<published-slug>/`
- **Then** detail strana (template `blog/post_detail.html`, status 200) prikazuje:
  - **naslovnu sliku** `{% responsive_picture post.main_image %}` (REUSE 2-3) sa `{% if post.main_image %}` guard (nullable); `alt=post.title` (pun dijakritik)
  - **meta liniju**: datum `{{ post.published_at|date:"SHORT_DATE_FORMAT" }}` (locale-aware); **autor `{% if post.author %}` guard (SM-D5 — author FK SET_NULL, može biti None; bez autora meta linija se gracefully render-uje BEZ autora, NE crash/„None")**; kategorija ime kao link `{% url 'blog:category' slug=post.category.slug %}` sa `{% if post.category %}` guard (category SET_NULL)
  - **naslov** `<h1>{{ post.title }}</h1>`
  - **telo** `{{ post.body|linebreaks }}` (**plain auto-escape — SM-D1; NIKAD `|safe`**; HTML u body-ju se ESCAPE-uje, NE izvršava — XSS-safe)
  - **tag linkovi** `{% for tag in post.tags.all %}` → `{% url 'blog:tag' slug=tag.slug %}` (svaki tag link na svoju arhivu)
- **And** `context_object_name="post"` (NEPROMENJEN 5-2 ugovor); `model=Post`; draft/future detail i dalje → 404 (Post.published — 5-2 testovi zeleni)
- **And** **autor=None test**: published Post sa `author=None` → detail 200, meta linija render-uje BEZ autor-imena (NE „None", NE crash) — SM-D5 guard
- **And** **XSS test (SM-D1)**: Post sa `body="<script>alert(1)</script>"` → response body sadrži ESCAPE-ovan `&lt;script&gt;` (NE izvršiv `<script>`) — dokazuje `|linebreaks` auto-escape, NEMA `|safe`

**AC2 — „Slične objave": 2-4 published iz ISTE kategorije, exclude-self, draft-not-leaked, bounded (epics.md:889; SM-D8)**

- **Given** AC1; published Post P sa kategorijom K; više drugih objava (published u K, draft u K, published u drugoj kategoriji)
- **When** detail `/sr/blog/<P-slug>/` render-uje „Slične objave" sekciju
- **Then** `get_context_data` postavlja `similar_posts`:
  - SAMO objave iz ISTE kategorije K (`Post.published.filter(category=post.category)`)
  - **EXCLUDING current post** (`.exclude(pk=post.pk)` — P nije u svojim „sličnim")
  - **kroz `Post.published`** (draft/future u K **NE** procuruje — draft-not-leaked; SM-D2)
  - ordering najnovije-prvo (Meta.ordering); **bounded** `[:_SIMILAR_POSTS_LIMIT]` (2-4 — epics.md:889; LIMIT=4)
  - render SAMO `{% if similar_posts %}` (REUSE `_post_card.html` kartice)
- **And** **`post.category is None` (SET_NULL)** → `similar_posts` prazna lista (NE crash, NE „sve objave"); sekcija se NE render-uje
- **And** kategorija K sa SAMO current-post (nema drugih published) → `similar_posts` prazna → sekcija se NE render-uje (graceful)
- **And** draft objava u K → **NIJE** u similar_posts (test asertuje draft excluded)

**AC3 — `BlogCategoryView` arhiva: `blog:category` `/sr/blog/kategorija/<slug>/` (Post.published, paginacija, 404 bad slug; epics.md:891; SM-D4)**

- **Given** AC1; Category K sa published objavama; `blog:category` URL registrovan PRE catch-all (AC5)
- **When** posetilac otvori `/sr/blog/kategorija/<K-slug>/`
- **Then** `BlogCategoryView(ListView)` (mirror BlogIndexView):
  - queryset `Post.published.select_related("category").filter(category__slug=<K-slug>)` (draft-not-leaked; SAMO objave kategorije K, najnovije-prvo)
  - `paginate_by=10`; `Paginator.get_page()` overflow safety (`?page=999` clamp, NE 404); `is_paginated`/`page_obj`/`paginator`
  - `get_template_names()` request.htmx branching (full `blog_archive.html` vs `_post_results.html` REUSE 5-2); HTMX paginacija swap + OOB aria-live count
  - `@vary_on_headers("HX-Request")`
  - heading „Objave u kategoriji: <K-ime>" (`archive_object`=Category); BEZ filter dropdown-a (arhiva je već filtrirana)
  - klik na kategoriju u detail-meta vodi OVDE (`{% url 'blog:category' slug=post.category.slug %}`)
- **And** **nepostojeća kategorija slug** (`/sr/blog/kategorija/ne-postoji/`) → **404** (`get_object_or_404(Category, slug=...)` — SM-D4)
- **And** validna kategorija sa **0 published** objava (postoje samo draft) → 200 + empty state sa **ARHIVA-PRIKLADNOM porukom** (NE generičkom „Uskoro nove priče sa polja" + home CTA). REUSE `_blog_empty_state.html` filter-0 grana: view prosleđuje `active_filters={"kategorija": <K-slug>}` u kontekst → `{% if active_filters.kategorija %}` je True → render-uje „Nema objava u ovoj kategoriji." + „prikaži sve" → `blog:index` link (IMP-1). draft-not-leaked. Test (9.6) asertuje arhiva-prikladnu kopiju (`data-testid="blog-empty-filter"`, NE `blog-empty-home`).

**AC4 — `BlogTagView` arhiva: `blog:tag` `/sr/blog/tag/<slug>/` (Post.published, paginacija, 404 bad slug; epics.md:892; SM-D4)**

- **Given** AC1; Tag T sa published objavama; `blog:tag` URL registrovan PRE catch-all (AC5)
- **When** posetilac otvori `/sr/blog/tag/<T-slug>/`
- **Then** `BlogTagView(ListView)` (mirror BlogCategoryView):
  - queryset `Post.published.select_related("category").filter(tags__slug=<T-slug>).distinct()` (`.distinct()` jer M2M join može duplirati — kanonski M2M-guard, IMP-6a; draft-not-leaked)
  - `paginate_by=10` + overflow + htmx branching + vary_on_headers (kao AC3)
  - heading „Objave sa tagom: <T-ime>" (`archive_object`=Tag)
  - klik na tag u detail-u vodi OVDE (`{% url 'blog:tag' slug=tag.slug %}`)
- **And** **nepostojeći tag slug** → 404 (`get_object_or_404(Tag, slug=...)`)
- **And** validan tag sa 0 published objava → 200 + empty state sa **ARHIVA-PRIKLADNOM porukom** (IMP-1): view prosleđuje `active_filters={"kategorija": <T-slug>}` → `_blog_empty_state.html` filter-0 grana („Nema objava u ovoj kategoriji." + „prikaži sve" → `blog:index`), NE generička home-CTA grana. draft-not-leaked. Test (9.7) asertuje `data-testid="blog-empty-filter"` (NE `blog-empty-home`).

**AC5 — URL ordering: arhive (`blog:category`/`blog:tag`) registrovane PRE catch-all `blog:detail` (SM-D3; KLJUČNO)**

- **Given** `apps/blog/urls.py` (5-2: `blog/` + `blog/<slug>/`); 5-3 dodaje `blog/kategorija/<slug>/` + `blog/tag/<slug>/`
- **When** registrujem nove rute
- **Then** redosled u `urlpatterns`: `blog/` (index) → `blog/kategorija/<slug>/` (category) → `blog/tag/<slug>/` (tag) → **`blog/<slug>/` (detail catch-all) POSLEDNJI**
  - `reverse("blog:category", slug="x")` → `/sr/blog/kategorija/x/`; `reverse("blog:tag", slug="x")` → `/sr/blog/tag/x/`; `reverse("blog:detail", slug="x")` → `/sr/blog/x/`
  - `/sr/blog/kategorija/<K-slug>/` rezolvira na `BlogCategoryView` (NE na `BlogPostDetailView` sa slug="kategorija") — **resolver-order lock**
  - `/sr/blog/tag/<T-slug>/` rezolvira na `BlogTagView`
- **And** **test asertuje resolved view** (`resolve("/sr/blog/kategorija/x/").func.view_class is BlogCategoryView`) — dokazuje 2-segment arhivu; postojeći `blog:detail` (`/sr/blog/<slug>/`) i dalje radi (5-2 detail testovi zeleni)
- **And** **NEMA strukturne kolizije**: arhive su 2-segmentne (`blog/kategorija/<slug>/`, `blog/tag/<slug>/`) a detail je 1-segmentni (`blog/<slug>/`) — `/sr/blog/kategorija/x/` razrešava na `BlogCategoryView`, a 1-segment `/sr/blog/kategorija/` (post sa slug-om TAČNO „kategorija") i dalje razrešava na `BlogPostDetailView(slug="kategorija")` i OSTAJE DOSTUPAN (NIJE shadow-ovan). url-ordering (arhive PRE catch-all) je kanonska higijena/disciplina, NE load-bearing za shadowing (2-segment i 1-segment se strukturno ne preklapaju). (OQ-1 RESOLVED — nema realne kolizije.)

**AC6 — Social share: FB/Viber/WhatsApp/Copy-link (sticky-left desktop / below-title mobile; epics.md:890; SM-D6)**

- **Given** AC1; published Post
- **When** detail render-uje social-share (`_social_share.html`)
- **Then**:
  - 4 dugmeta: **Facebook**, **Viber**, **WhatsApp**, **Copy-link** (epics.md:890)
  - **share URL = post apsolutni URL, izračunat U VIEW-u (IMP-2):** `get_context_data` postavlja `ctx["share_url"] = self.request.build_absolute_uri(self.object.get_absolute_url())`. Template koristi `{{ share_url }}`. ⛔ NE koristi `{{ request.build_absolute_uri(post.get_absolute_url) }}` u template-u — Django template jezik NE MOŽE da prosledi argument metodi u `{{ }}` (sintaksno nevalidno). View-context `share_url` je PREFERIRAN (čist, testabilan). (Alternativa AKO se izbegava view izmena: `{{ request.scheme }}://{{ request.get_host }}{{ post.get_absolute_url }}` — bez argumenta — ali view-context je biran.)
  - **EGZAKTNI share href-ovi (IMP-3 — dev NE pogađa):**
    - Facebook: `https://www.facebook.com/sharer/sharer.php?u={{ share_url|urlencode }}`
    - WhatsApp: `https://wa.me/?text={{ share_url|urlencode }}` (ili `https://api.whatsapp.com/send?text={{ share_url|urlencode }}`)
    - Viber: `viber://forward?text={{ share_url|urlencode }}` (mobilni deep-link; na DESKTOP-u gracefully no-op-uje — prihvatljivo za mobile-first poljoprivrednu publiku)
    - sve sa `target="_blank" rel="noopener"` za FB/WhatsApp (Viber je app-scheme)
  - **Copy-link** = vanilla JS (`navigator.clipboard.writeText(share_url)` — NE jQuery; secure-context/HTTPS — prod pokriva, localhost OK); klik kopira URL + aria-live najava „Link kopiran" (a11y)
  - **pozicija**: sticky leva strana na desktop / ispod naslova na mobile (epics.md:890) — kroz CSS (sticky desktop / static mobile breakpoint; `var(--token)`)
  - aria-label/title svih dugmadi `{% translate %}` pune dijakritike (npr. „Podeli na Facebook-u", „Podeli na Viber-u", „Podeli na WhatsApp-u", „Kopiraj link")
  - `data-testid` na svakom dugmetu (E2E)

**AC7 — Meta title/description iz Post.title + Post.perex (epics.md:893; SM-D7; OG=Epic 6)**

- **Given** AC1; published Post sa title + perex
- **When** detail render-uje `<head>`
- **Then**:
  - `{% block title %}` → `{{ post.title }} | Ćorić Agrar` (mirror 5-2 placeholder; override base.html)
  - `{% block meta_description %}` → **`{{ post.perex|default:post.title }}` (IMP-4 — fallback na title kad je perex prazan; meta description NIKAD prazan/empty tag)**; pun dijakritik
  - **NEMA OG/twitter/canonical** (Epic 6 — 6.1 SeoMeta; epics.md:893 „override-ovi dolaze u Epic 6"); 5-3 SAMO bazičan title+description
- **And** title/description su HTML-escaped (auto-escape — perex je plain text)
- **And** **prazan perex test (IMP-4)**: published Post sa `perex=""` → `<meta name="description">` sadrži `post.title` (NE prazan string) — `|default:post.title` fallback zaključan (test 9.10)

**AC8 — N+1 lock: detail (author/tags/Slične-objave) + arhive `assertNumQueries` (SM-D2/SM-D8; project-context.md:743)**

- **Given** AC1-AC4
- **When** detail/arhiva render-uje
- **Then**:
  - **detail** `get_queryset()` MORA `select_related("category","author")` + `prefetch_related("tags")` (autor meta + tag linkovi → bez ovoga N+1: per-render author FK + tags M2M lookup; 5-2 forward-note IMP-5). „Slične objave" query je `Post.published.filter(category=...).select_related("category")[:LIMIT]` (1 dodatni bounded query, NE per-post N+1)
  - **detail assertNumQueries** KONSTANTAN bez obzira na broj tagova/sličnih-objava (test: post sa 2 taga + 4 slične == post sa 5 tagova + 4 slične → isti budžet; prefetch/select_related drže query broj konstantnim)
  - **arhive** queryset `select_related("category")` (kartica/grid ne sme N+1 per-post category lookup; mirror BlogIndexView AC2); count-variation lock (3 objave == 10 objava → konstanta)
  - `archive_object` (`get_object_or_404`) je +1 konstanta query (NE per-post)
- **And** N empirijski zaključan u GREEN (TEA piše assertNumQueries strukturu, Dev fix-uje broj)

**AC9 — Responsive + i18n full diacritics + draft-not-leaked SVUDA (epics.md:890; SM-D2)**

- **Given** AC1-AC8
- **When** detail/arhiva se gleda mobile (<768px) pa desktop (≥992px); render za sr (+ smoke hu/en)
- **Then**:
  - detail responsive: social-share sticky-left desktop / below-title mobile (epics.md:890); Slične-objave grid 1col mobile / 2-3col desktop (REUSE blog-listing grid); naslovna slika full-width responsive
  - SVI user-facing string-ovi `{% translate %}`/`{% blocktranslate %}` pune dijakritike („Slične objave", „Autor", „Kategorija", „Objave u kategoriji:", „Objave sa tagom:", social-share labeli, „Link kopiran") — NIKAD hardcoded/šišana latinica (project-context.md:497-527)
  - slug u URL-u ASCII (iz 5-1 slugify_ascii)
  - **draft-not-leaked KONSOLIDOVANO**: detail (`Post.published`→draft/future 404) + Slične-objave (`Post.published`→draft excluded) + kategorija-arhiva (`Post.published.filter(category__slug=...)`→draft excluded) + tag-arhiva (`Post.published.filter(tags__slug=...)`→draft excluded) — **SVE 4 javne tačke kroz `Post.published`** (NIKAD `Post.objects`); test asertuje draft NEVIDLJIV na svakoj
- **And** `.po` sr/hu/en imaju nove string-ove (`just messages`); `loading="lazy"` na ispod-fold slikama (Slične-objave kartice)

## Tasks / Subtasks

> **Konvencija:** `[TEA-RED]` = Test Architect piše test PRE implementacije (mora FAIL). `[DEV-GREEN]` = Developer implementira. **Dev NIKAD ne piše testove.** **NEMA migracije** (views/templates/urls/css/js — konzumira 5-1 šemu). **NEMA `uv add`.** ⚠️ 5-3 OBOGAĆUJE 5-2 `BlogPostDetailView` (NE prepisuje) — **5-2 `test_blog_urls.py` detail testovi MORAJU OSTATI ZELENI**.

- [ ] **Task 1 — URL ordering: arhive PRE catch-all detail (AC5; SM-D3 — KLJUČNO)** `[DEV-GREEN]`
  - [ ] 1.1 EDIT `apps/blog/urls.py`: dodaj `path("blog/kategorija/<slug:slug>/", views.BlogCategoryView.as_view(), name="category")` + `path("blog/tag/<slug:slug>/", views.BlogTagView.as_view(), name="tag")` **PRE** `path("blog/<slug:slug>/", ..., name="detail")`. Redosled: `blog/` → `blog/kategorija/<slug>/` → `blog/tag/<slug>/` → `blog/<slug>/`.
  - [ ] 1.2 `reverse("blog:category", slug="x")`/`reverse("blog:tag", slug="x")`/`reverse("blog:detail", slug="x")` razrešavaju; `resolve("/sr/blog/kategorija/x/")` → `BlogCategoryView` (NE detail). Ažuriraj urls.py docstring (5-3 dodaje arhive + url-ordering rationale).

- [ ] **Task 2 — `BlogPostDetailView` OBOGAĆENJE: get_queryset proširenje + get_context_data „Slične objave" (AC1/AC2/AC8; SM-D2/SM-D8) — NE rewrite** `[DEV-GREEN]`
  - [ ] 2.1 PROŠIRI `BlogPostDetailView.get_queryset()`: 5-2 `Post.published.select_related("category")` → `Post.published.select_related("category", "author").prefetch_related("tags")` (autor/tagovi render → N+1 lock; 5-2 forward-note IMP-5). NEPROMENJENO: model/context_object_name="post"/template_name/draft-404.
  - [ ] 2.2 Dodaj `_SIMILAR_POSTS_LIMIT = 4` konstanta (mirror 2-7 `_SIMILAR_PRODUCTS_LIMIT`).
  - [ ] 2.3 NOVI `BlogPostDetailView.get_context_data()`: `post = self.object`; ako `post.category` → `similar = Post.published.filter(category=post.category).exclude(pk=post.pk).select_related("category")[:_SIMILAR_POSTS_LIMIT]` (draft-not-leaked, exclude-self, bounded, najnovije-prvo Meta.ordering); else `similar = Post.published.none()` (category None — NE crash). `ctx["similar_posts"] = list(similar)`. **`ctx["share_url"] = self.request.build_absolute_uri(post.get_absolute_url())` (IMP-2 — apsolutni share URL izračunat u view-u; template `{{ share_url }}` jer `{{ }}` ne može metodi proslediti argument).**
  - [ ] 2.4 `manage.py check` exit 0; 5-2 `test_blog_urls.py` detail testovi i dalje zeleni (200/draft-404/future-404/context_object_name/no-oracle).

- [ ] **Task 3 — `BlogCategoryView` + `BlogTagView` arhive (AC3/AC4/AC8; SM-D4) — mirror BlogIndexView** `[DEV-GREEN]`
  - [ ] 3.1 `BlogCategoryView(ListView)`: `model=Post`, `context_object_name="posts"`, `paginate_by=10`, `@method_decorator(vary_on_headers("HX-Request"), name="dispatch")`. `setup()`/`get()` → `self.archive_object = get_object_or_404(Category, slug=self.kwargs["slug"])` (404 nepostojeća — SM-D4). `get_queryset()` → `Post.published.select_related("category").filter(category__slug=self.kwargs["slug"])` (najnovije-prvo). `get_template_names()` htmx branching (`_post_results.html` vs `blog_archive.html`). `paginate_queryset()` Paginator.get_page() overflow (REUSE 5-2 BlogIndexView override — razmotri shared mixin AKO se ponavlja 3×, inače inline). `get_context_data` → `count=paginator.count` (OOB aria-live), `archive_object`, `archive_kind="category"`, **`active_filters={"kategorija": self.kwargs["slug"]}` (IMP-1 — KLJUČNO: arhive REUSE `_post_results.html` → `_blog_empty_state.html` koji grana na `{% if active_filters.kategorija %}`; BEZ ovoga arhiva-empty render-uje POGREŠNU generičku „Uskoro nove priče sa polja" + home CTA. Prosleđivanje `active_filters` aktivira filter-0 granu → arhiva-prikladna „Nema objava u ovoj kategoriji." + „prikaži sve" → `blog:index`)**.
  - [ ] 3.2 `BlogTagView(ListView)` (mirror 3.1): `get_object_or_404(Tag, slug=...)`; `get_queryset()` → `Post.published.select_related("category").filter(tags__slug=self.kwargs["slug"]).distinct()` (`.distinct()` — kanonski M2M-guard; IMP-6a). `archive_kind="tag"`; **`active_filters={"kategorija": self.kwargs["slug"]}` (IMP-1 — isti empty-state mehanizam kao 3.1; arhiva-prikladna empty kopija umesto home CTA)**.
  - [ ] 3.3 (Opciono) ako Paginator.get_page() override + htmx branching se ponavljaju kroz 3 view-a (Index+Category+Tag) → izvuci mali `BlogListingMixin` (YAGNI prag: 3 kopije). Default: inline kopija prihvatljiva (2-8/2-9 imaju duplikate; SM-D9). Dev odluka.

- [ ] **Task 4 — `post_detail.html` OBOGAĆENJE: slika + meta + autor[NULL] + telo[plain] + tagovi + Slične + social + meta (AC1/AC2/AC6/AC7; SM-D1/D5/D6/D7)** `[DEV-GREEN]`
  - [ ] 4.1 Naslovna slika: `{% if post.main_image %}{% responsive_picture post.main_image alt=post.title sizes="100vw" %}{% endif %}` (REUSE 2-3). `{% load media_tags %}`.
  - [ ] 4.2 Meta linija: datum `{{ post.published_at|date:"SHORT_DATE_FORMAT" }}` (postojeći); **`{% if post.author %}`autor (`{{ post.author.get_full_name|default:post.author.username }}`)`{% endif %}` (SM-D5 — NULL guard izostavlja celu „autor" liniju kad author=None; `get_full_name|default:username` jer get_full_name vraća „" za autora bez first/last → `default` hvata prazan string i prikazuje username, NE prazan/„None" — IMP-6b)**; `{% if post.category %}`kategorija `<a href="{% url 'blog:category' slug=post.category.slug %}">{{ post.category.name }}</a>``{% endif %}` (SET_NULL guard).
  - [ ] 4.3 Telo: `{{ post.body|linebreaks }}` (**plain auto-escape — SM-D1; NIKAD `|safe`**). Ažuriraj postojeći 5-2 TODO komentar (5-3 zadržava plain; rich-text + sanitizacija = 8.7 forward-note).
  - [ ] 4.4 Tag linkovi: `{% for tag in post.tags.all %}<a href="{% url 'blog:tag' slug=tag.slug %}">{{ tag.name }}</a>{% endfor %}`.
  - [ ] 4.5 `{% include "blog/partials/_social_share.html" %}` (Task 5); `{% if similar_posts %}{% include "blog/partials/_similar_posts.html" %}{% endif %}` (Task 6).
  - [ ] 4.6 Meta: `{% block title %}{{ post.title }} | Ćorić Agrar{% endblock %}`; `{% block meta_description %}{{ post.perex|default:post.title }}{% endblock %}` (**IMP-4 — `|default:post.title` fallback: meta description NIKAD prazan kad je perex blank; SM-D7**).

- [ ] **Task 5 — `_social_share.html` + copy JS (AC6; SM-D6)** `[DEV-GREEN]`
  - [ ] 5.1 `templates/blog/partials/_social_share.html`: share URL je **`{{ share_url }}`** (izračunat u view-u — Task 2.3; IMP-2 — NE `{{ request.build_absolute_uri(post.get_absolute_url) }}`, sintaksno nevalidno u template-u). EGZAKTNI href-ovi (IMP-3): Facebook `https://www.facebook.com/sharer/sharer.php?u={{ share_url|urlencode }}` (`target="_blank" rel="noopener"`); WhatsApp `https://wa.me/?text={{ share_url|urlencode }}` (`target="_blank" rel="noopener"`); Viber `viber://forward?text={{ share_url|urlencode }}` (mobilni deep-link — komentar: na desktop-u no-op, OK za mobile-first). Copy-link `<button data-share-copy data-copy-url="{{ share_url }}">`. `{% translate %}` aria-label/title pune dijakritike („Podeli na Facebook-u"/„Podeli na Viber-u"/„Podeli na WhatsApp-u"/„Kopiraj link"). `data-testid` na svakom.
  - [ ] 5.2 `static/js/blog-share-copy.js` (ILI inline `{% block scripts %}`): vanilla `navigator.clipboard.writeText` na `[data-share-copy]` klik; aria-live „Link kopiran" (target `#aria-live` singleton base.html); `coric:link-copied` event opciono. `static/js/...` registruj u `{% block scripts %}`.

- [ ] **Task 6 — `_similar_posts.html` + `blog_archive.html` (AC2/AC3/AC4)** `[DEV-GREEN]`
  - [ ] 6.1 `templates/blog/partials/_similar_posts.html`: heading „Slične objave" + grid `{% for post in similar_posts %}{% include "blog/partials/_post_card.html" %}{% endfor %}` (mirror 2-7 `_similar_products.html`; REUSE coric-blog-card).
  - [ ] 6.2 `templates/blog/blog_archive.html` (`{% extends "base.html" %}`): heading iz `archive_object`/`archive_kind` („Objave u kategoriji: <ime>" / „Objave sa tagom: <ime>") + `{% include "blog/partials/_post_results.html" %}` (REUSE 5-2 grid+paginacija+empty; empty-state render-uje arhiva-prikladnu kopiju jer view prosleđuje `active_filters` — IMP-1). **BEZ filter dropdown-a — arhiva je već filtrirana (SM-D4); NE include-uj `_blog_filter.html` / `<select name="kategorija">` (test 9.6 asertuje odsutan — IMP-6c).** `{% block title %}`/`meta_description`. (Razmotri REUSE `blog_index.html` sa conditional heading — ali dedikovan `blog_archive.html` je čistiji; Dev/UX odluka.)

- [ ] **Task 7 — CSS detail layout + social-share sticky responsive (AC9; epics.md:890)** `[DEV-GREEN]`
  - [ ] 7.1 `static/css/components/blog-detail.css` (ILI dopuna blog-listing.css): detail layout (naslovna slika, meta, telo prose width, Slične-objave grid REUSE) + **social-share sticky-left desktop / below-title mobile** (epics.md:890 — `position: sticky` desktop / static mobile breakpoint; `var(--token)`, NE magic px). main.css `@import` ako novi fajl. `prefers-reduced-motion` ako ima animacija.

- [ ] **Task 8 — i18n string-ovi + .po (AC9)** `[DEV-GREEN]`
  - [ ] 8.1 Svi novi user-facing string-ovi `{% translate %}`/`{% blocktranslate %}` pune dijakritike. `just messages` regeneriše sr/hu/en .po; popuni hu/en (ili sr fallback).

- [ ] **Task 9 — RED-phase testovi (AC1-AC9)** `[TEA-RED]`
  - [ ] 9.1 `apps/blog/tests/test_blog_post_detail.py` (NOVO) + REUSE `conftest.py` (`make_post`/`make_category`/`make_tag`/`author_user`). `@pytest.mark.django_db`.
  - [ ] 9.2 **AC1 (obogaćen detail):** published Post sa slika/datum/autor/kategorija/telo/tagovi → detail 200, template `blog/post_detail.html`; slika prisutna (`{% if %}` guard); meta datum + autor + kategorija-link (`/sr/blog/kategorija/<slug>/`); naslov; telo render-ovan; tag linkovi (`/sr/blog/tag/<slug>/`). `context_object_name="post"` (5-2 ugovor).
  - [ ] 9.3 **AC1 (autor display — SM-D5; IMP-6b):** (a) published Post `author=None` → detail 200, „autor" linija je IZOSTAVLJENA (`{% if post.author %}` guard — NE „None", NE crash, NE prazna linija); (b) published Post sa autorom koji ima first_name+last_name → meta prikazuje puno ime; (c) **published Post sa autorom čiji su `first_name=""` i `last_name=""` (prazni) → renderovani autor je `username` (NE „", NE „None") — dokazuje `get_full_name|default:username` fallback (get_full_name vraća „" kad nema imena → `default` hvata prazan string).**
  - [ ] 9.4 **AC1 (XSS — SM-D1; SECURITY):** Post `body="<script>alert(1)</script>"` → response sadrži ESCAPE-ovan `&lt;script&gt;` (NE sirov `<script>`); dokazuje `|linebreaks` auto-escape, NEMA `|safe`. (Load-bearing security lock — sprečava regresiju ka `|safe`.)
  - [ ] 9.5 **AC2 (Slične objave):** Post P u kategoriji K + 3 published u K + 1 draft u K + 1 published u drugoj kategoriji → `similar_posts` = 3 published-K (NE P sam, NE draft-K, NE druga-kategorija); bounded ≤4; `post.category=None` → `similar_posts` prazna (NE crash); K sa samo-P → prazna → sekcija ne render-uje.
  - [ ] 9.6 **AC3 (kategorija arhiva):** `/sr/blog/kategorija/<K-slug>/` → 200, template `blog_archive.html`, `posts` = published-K (najnovije-prvo, draft-not-leaked); paginacija (25 → strana 1=10, `?page=999` clamp); HTMX request → `_post_results.html` + OOB aria-live; `/sr/blog/kategorija/ne-postoji/` → 404; **validna-K-sa-0-published → 200 + ARHIVA-PRIKLADAN empty state (IMP-1): asertuj `data-testid="blog-empty-filter"` prisutan i „prikaži sve" → `blog:index` link; asertuj da NIJE renderovana generička home grana (`data-testid="blog-empty-home"` ODSUTAN, „POVRATAK NA POČETNU" ODSUTAN)**. **Arhiva NEMA filter dropdown (IMP-6c; SM-D4): asertuj `<select name="kategorija">` ODSUTAN u `blog_archive.html` (arhiva je već filtrirana).**
  - [ ] 9.7 **AC4 (tag arhiva + `.distinct()` M2M-guard — IMP-6a):** `/sr/blog/tag/<T-slug>/` → 200, `posts` = published sa tagom T; **`.distinct()` kanonski M2M-guard test: kreiraj post sa 2 taga, filtriraj po slug-u JEDNOG od ta dva → asertuj da se post pojavljuje TAČNO JEDNOM (single-slug filter retko duplira jer join match-uje 1 red, ali `.distinct()` je kanonski guard protiv M2M join duplikata — dokumentuj WHY u testu)**; 404 bad slug; draft-not-leaked; HTMX branching. validan tag sa 0 published → 200 + empty (arhiva-prikladna kopija, IMP-1).
  - [ ] 9.8 **AC5 (url-ordering — KLJUČNO):** `reverse("blog:category"/"blog:tag"/"blog:detail")` razrešavaju; `resolve("/sr/blog/kategorija/x/").func.view_class is BlogCategoryView` (NE BlogPostDetailView); `resolve("/sr/blog/tag/x/")` → BlogTagView; `resolve("/sr/blog/neki-post/")` → BlogPostDetailView (catch-all i dalje radi). **Test dokazuje arhive PRE catch-all-a.**
  - [ ] 9.9 **AC6 (social share):** detail HTML ima 4 dugmeta (FB/Viber/WhatsApp/Copy-link); **`share_url` u kontekstu == apsolutni post URL (IMP-2); FB href sadrži `facebook.com/sharer/sharer.php?u=` + urlencoded share_url, WhatsApp `wa.me/?text=`, Viber `viber://forward?text=` (IMP-3)**; Copy-link `[data-share-copy]` `data-copy-url`==share_url + aria-label pun dijakritik; `data-testid`.
  - [ ] 9.10 **AC7 (meta):** `<title>` sadrži `post.title`; `<meta name="description">` sadrži `post.perex`; **prazan-perex (IMP-4): published Post `perex=""` → meta description == `post.title` (NE prazan `content=""`) — `|default:post.title` fallback**; NEMA OG/twitter (Epic 6).
  - [ ] 9.11 **AC8 (N+1):** `apps/blog/tests/test_blog_detail_n_plus_1.py` (NOVO): detail assertNumQueries KONSTANTAN (post 2 taga+4 slične == post 5 tagova+4 slične); arhiva count-variation (3==10 objava); `select_related("category","author")`+`prefetch_related("tags")` na detail; `select_related("category")` na arhivi. Lock N empirijski.
  - [ ] 9.12 **AC9 (draft-not-leaked SVUDA + i18n):** draft NEVIDLJIV na: detail (404), Slične-objave (excluded), kategorija-arhiva (excluded), tag-arhiva (excluded) — 4 tačke. Ključni string-ovi pun-dijakritik (NE šišana); sr render (+ smoke hu/en); slug ASCII u href. `apps/blog/tests/test_blog_archives.py` (NOVO) za AC3/AC4/AC5.
  - [ ] 9.13 **5-2 regression (KRITIČNO):** potvrdi `test_blog_urls.py` (detail-200/draft-404/future-404/context_object_name/no-oracle) OSTAJU ZELENI posle 5-3 obogaćenja (NE menjaj taj fajl — 5-3 obogaćenje NE sme slomiti placeholder ugovor).

- [ ] **Task 10 — Dev manual gate (NE pytest) (AC regression)** `[DEV-GREEN]`
  - [ ] 10.1 `manage.py check` exit 0; **`makemigrations --check --dry-run` → „No changes detected"** (NEMA model promene — regression guard).
  - [ ] 10.2 Dev shell smoke: published Post sa kategorijom+tagom+autorom → detail render (slika/meta/telo/tagovi/Slične/social); klik kategorija → arhiva; klik tag → arhiva; draft detail → 404; nepostojeća kategorija → 404; Copy-link kopira URL.
  - [ ] 10.3 `just lint` clean (ruff apps/blog/ + djade templates/blog/); commit views+urls+templates+css+js+po ZAJEDNO (atomic). Potvrdi 5-2 `test_blog_urls.py` zelen.

## Dev Notes

### SM Decisions (SM-D log)

**SM-D1 — BODY RENDER (SECURITY-CRITICAL): KEEP plain `|linebreaks` (auto-escape — XSS-safe); DEFER rich-text/inline-slike/video-embed na Epic 8.7. NIKAD raw `|safe`.** epics.md:889 opisuje telo kao „rich text sa inline slikama i video embed". ALI: (1) 5-1 model `body` je **PLAIN TextField** (5-1 SM-D10 eksplicitno — „body je PLAIN TextField (NE WYSIWYG model field); rich editor je Epic 8.7"); (2) WYSIWYG editor + sanitizacija pipeline su **Epic 8.7** scope; (3) rich HTML render SADA bi zahtevao NOVI dep (bleach/nh3 sanitizacija allowlist) + `{{ post.body|safe }}` — što otvara **stored-XSS surface** ako se sanitizacija pogreši (admin Editor role unosi body; bez sanitizacije `|safe` izvršava proizvoljan `<script>`).
- **RAZMOTRENE OPCIJE:**
  - (a) **`{{ post.body|linebreaks }}` (plain, auto-escape; rich/inline-media/video DEFER na 8.7).** ✅ IZABRANO — lowest-risk v1.
  - (b) Sanitizovan rich HTML SADA (`bleach`/`nh3` allowlist + `|safe` + novi dep). ❌ ODBAČENO za 5-3 — uvodi novi dep + XSS surface + sanitizacijski tuning PRE nego što WYSIWYG editor (8.7) uopšte postoji da generiše rich body; YAGNI (body je plain text dok 8.7 ne uvede rich unos).
  - (c) Raw `{{ post.body|safe }}` bez sanitizacije. ❌ NIKAD — stored-XSS (admin unosi `<script>` → izvršava se kod svakog posetioca). Eksplicitno zabranjeno.
- **ZAŠTO (a) je lowest-risk:** `|linebreaks` auto-escape-uje HTML (`<` → `&lt;`) → XSS-safe; plain text body (5-1 realnost) se ispravno render-uje (paragraf/prelomi). Kad 8.7 uvede WYSIWYG + sanitizaciju, telo render postaje sanitizovan-`|safe` (8.7 owns taj prelaz). **FORWARD-NOTE 8.7:** kad body postane rich-HTML, zameni `|linebreaks` sa **sanitizovanim renderom** (bleach/nh3 allowlist + `|safe`) — `|linebreaks` bi tada DOUBLE-escape-ovao (prikazao sirove tagove). 5-2 `post_detail.html` već nosi ovaj TODO komentar (zadrži/ažuriraj). **NIKAD raw `|safe` bez sanitizacije.** AC1 XSS test (9.4) trajno zaključava auto-escape (sprečava regresiju ka `|safe`).

**SM-D2 — OBOGAĆENJE, NE REWRITE: 5-3 PROŠIRUJE 5-2 `BlogPostDetailView` (get_queryset + get_context_data); 5-2 testovi OSTAJU ZELENI.** 5-2 placeholder kontrakt (SM-D11): `model=Post`, `get_queryset()=Post.published.select_related("category")`, `context_object_name="post"`, `template_name="blog/post_detail.html"`, draft/future→404. 5-3 (a) PROŠIRUJE `get_queryset()` → `Post.published.select_related("category","author").prefetch_related("tags")` (autor meta + tag linkovi render → N+1 lock; 5-2 forward-note IMP-5 eksplicitno tražio ovo); (b) DODAJE `get_context_data()` za „Slične objave". **NE menja**: model/context_object_name/template/draft-404 logiku. **5-2 `test_blog_urls.py` (detail-200/draft-404/future-404/context_object_name/no-oracle) MORA OSTATI ZELEN** — 5-3 obogaćenje NE sme slomiti placeholder ugovor (Task 9.13 regression lock). `Post.published` baza ostaje (draft-not-leaked).

**SM-D3 — URL ORDERING: arhive (`blog:category`/`blog:tag`) registrovane PRE catch-all `blog:detail` (kanonska higijena).** `apps/blog/urls.py` redosled: `blog/` (index) → `blog/kategorija/<slug>/` (category) → `blog/tag/<slug>/` (tag) → **`blog/<slug>/` (detail catch-all) POSLEDNJI**. Django resolver iterira urlpatterns REDOM; prvi match pobeđuje.

**KLJUČNA KOREKCIJA (IMP-5) — NEMA strukturne kolizije:** arhive su **2-segmentne** (`blog/kategorija/<slug>/` = literal `kategorija` + drugi `<slug>` segment; isto `blog/tag/<slug>/`) a detail je **1-segmentni** (`blog/<slug>/`). 2-segment ruta strukturno NE MOŽE da shadow-uje 1-segment rutu i obrnuto — različit broj path segmenata. Zato:
- `/sr/blog/kategorija/x/` (2 segmenta) razrešava na `BlogCategoryView` — bez obzira na redosled (1-segment detail ionako ne pasuje 2 segmenta).
- `/sr/blog/kategorija/` (1 segment, post sa slug-om TAČNO „kategorija") razrešava na `BlogPostDetailView(slug="kategorija")` i **OSTAJE DOSTUPAN** — NIJE shadow-ovan arhivom (arhiva zahteva DRUGI segment posle „kategorija").

Dakle url-ordering (specifične-PRE-catch-all; mirror products/brands hijerarhijske URL-ove) je **kanonska disciplina/higijena, NE load-bearing za shadowing**. Test (9.8) `resolve("/sr/blog/kategorija/x/").func.view_class is BlogCategoryView` + `resolve("/sr/blog/<post>/").func.view_class is BlogPostDetailView` zaključava korektan resolver-order. Post sa slug-om „kategorija"/„tag" ostaje normalno dostupan na 1-segment detail ruti (OQ-1 RESOLVED — nema rezervisanih slug-ova, nema kolizije).

**SM-D4 — Arhive (`BlogCategoryView`/`BlogTagView`) mirror `BlogIndexView`; nepostojeća kategorija/tag → 404.** Arhive su DEDIKOVANE filter strane (`/sr/blog/kategorija/X/`), RAZLIČITE od 5-2 index querystring filtera (`/sr/blog/?kategorija=X`) — obe koegzistiraju (5-2 SM-D4 NAPOMENA: index filter sužava listu na index strani; arhiva je posebna strana). Arhive REUSE 5-2 listing infrastrukturu: `ListView` + `paginate_by=10` + `get_template_names()` htmx branching + `Paginator.get_page()` overflow + `@vary_on_headers` + `_post_results.html`/`_post_card.html`/`_blog_empty_state.html`. **404 na nepostojeću kategorija/tag slug** (`get_object_or_404(Category/Tag, slug=...)` u `get()`/`setup()`) — RAZLIKA od index filtera koji invalid slug normalizuje na „" (5-2 IMP-3): arhiva URL je eksplicitna ruta (`/sr/blog/kategorija/<slug>/`) → nepostojeći resurs = 404 (REST semantika; mirror products detail 404 za bad slug), NE empty state. Validna kategorija/tag sa 0 published objava → 200 + empty state (resurs postoji, samo prazan) — **arhiva prosleđuje `active_filters={"kategorija": <slug>}` da `_blog_empty_state.html` render-uje ARHIVA-PRIKLADNU filter-0 kopiju, NE generičku home-CTA granu (IMP-1; vidi OQ-5)**. Arhiva NE prikazuje filter dropdown (već je filtrirana — test asertuje `<select name="kategorija">` odsutan, IMP-6c). Tag arhiva koristi `.distinct()` (kanonski M2M-guard; IMP-6a).

**SM-D5 — AUTOR NULL GUARD: `{% if post.author %}` (author FK SET_NULL — može None).** 5-1: `author = FK(settings.AUTH_USER_MODEL, on_delete=SET_NULL, null=True)`. Brisanje autora ne briše objavljen content → `author` može biti `None`. Meta linija MORA `{% if post.author %}` guard — bez njega `{{ post.author.get_full_name }}` na None → render-uje „None" ili AttributeError. Test (9.3) asertuje: (a) published Post sa `author=None` → detail 200 + „autor" linija IZOSTAVLJENA (graceful, NE prazna linija); (c) autor sa praznim first/last → username (IMP-6b — vidi dole). Autor ime kroz **`get_full_name|default:username`**: `User.get_full_name()` vraća `"%s %s" % (first, last)` `.strip()` → kad su first/last prazni vraća **prazan string `""`**, koji `|default` hvata → prikazuje `username` (NE prazan, NE „None"). Test (9.3c) zaključava taj fallback (autor first_name=""/last_name="" → renderovan username). NEMA autor-profil-link (van scope-a).

**SM-D6 — SOCIAL SHARE: FB/Viber/WhatsApp/Copy-link (sticky-left desktop / below-title mobile; Copy=vanilla JS).** epics.md:890: 4 dugmeta + pozicija sticky-leva-desktop/ispod-naslova-mobile.

**SHARE URL — VIEW-CONTEXT (IMP-2, KOREKCIJA):** share URL = post apsolutni URL, **izračunat u view-u**: `get_context_data` postavlja `ctx["share_url"] = self.request.build_absolute_uri(self.object.get_absolute_url())` (Task 2.3); template koristi `{{ share_url }}`. ⛔ Ranija preporuka `request.build_absolute_uri(post.get_absolute_url)` kao TEMPLATE recept je **sintaksno nevalidna** — Django template jezik NE MOŽE da prosledi argument metodi unutar `{{ }}`. View-context `share_url` je PREFERIRAN (čist, testabilan, jedna tačka istine). Alternativa (ako se izbegava view izmena): `{{ request.scheme }}://{{ request.get_host }}{{ post.get_absolute_url }}` (bez argumenta) — ali view-context je biran.

**EGZAKTNI SHARE HREF-ovi (IMP-3 — dev NE pogađa):** FB/Viber/WhatsApp su outbound share intent URL-ovi:
- Facebook: `https://www.facebook.com/sharer/sharer.php?u={{ share_url|urlencode }}` (`target="_blank" rel="noopener"`)
- WhatsApp: `https://wa.me/?text={{ share_url|urlencode }}` (ili `https://api.whatsapp.com/send?text={{ share_url|urlencode }}`; `target="_blank" rel="noopener"`)
- Viber: `viber://forward?text={{ share_url|urlencode }}` (mobilni deep-link — na DESKTOP-u gracefully no-op-uje; prihvatljivo za mobile-first poljoprivrednu publiku)

**Copy-link = vanilla JS** (`navigator.clipboard.writeText(share_url)` — project-context.md:338 NIKAD jQuery; secure-context/HTTPS — prod pokriva preko SECURE_SSL_REDIRECT, localhost je secure-context; `coric:` namespace event opciono) + aria-live „Link kopiran" najava (a11y — target `#aria-live` singleton base.html). Pozicija kroz CSS (`position: sticky` desktop / static below-title mobile breakpoint; `var(--token)`). aria-label/title pune dijakritike (`{% translate %}`). NEMA share-count/lajkova (van scope-a — samo outbound).

**SM-D7 — META title/description iz Post.title+Post.perex (bazičan; OG/twitter/canonical=Epic 6).** epics.md:893: „Meta title/description popunjeni iz Post.title + Post.perex (override-ovi dolaze u Epic 6)". 5-3: `{% block title %}{{ post.title }} | Ćorić Agrar{% endblock %}` + `{% block meta_description %}{{ post.perex|default:post.title }}{% endblock %}` (base.html override). **IMP-4 FALLBACK:** `|default:post.title` jer `perex` je opcionalan/može biti prazan (`{{ post.perex }}` bez fallback-a render-uje PRAZAN `<meta name="description" content="">` — beskoristan/SEO-loš); fallback na `post.title` garantuje neprazan meta description. **NEMA OG/twitter/canonical** — Epic 6 (6.1 SeoMeta model + per-page admin override; 6.2 sitemap). 5-3 radi SAMO bazičan title+description (mirror 5-2 placeholder title block). Auto-escape (perex/title plain text). Test (9.10): `perex=""` → meta description == title.

**SM-D8 — „Slične objave": 2-4 published iz ISTE kategorije, exclude-self, draft-not-leaked, bounded (mirror 2-7 auto-fallback).** epics.md:889: „sekcija „Slične objave" (2-4 objave iz iste kategorije)". `get_context_data`: `Post.published.filter(category=post.category).exclude(pk=post.pk).select_related("category")[:_SIMILAR_POSTS_LIMIT]` (LIMIT=4 — gornja granica 2-4; ako kategorija ima <2 → render koliko ima, graceful). **kroz `Post.published`** (draft-not-leaked — draft u istoj kategoriji NE procuruje). `.exclude(pk=post.pk)` (current post nije u svojim „sličnima"). Ordering najnovije-prvo (Meta.ordering). **`post.category is None`** (SET_NULL) → `Post.published.none()` / prazna lista (NE crash, NE „sve objave"); sekcija se NE render-uje. Mirror 2-7 `ProductDetailView` auto-fallback (`Product.objects.filter(brand=..., is_published=True).exclude(pk=...).order_by("-created_at")[:LIMIT]`) — blog je samo-auto (NEMA manual `ProductSimilar` ekvivalent; YAGNI — epics.md ne traži ručni odabir sličnih). `select_related("category")` (Slične-objave kartice ne smeju N+1 per-post category).

**SM-D9 — Paginator.get_page() overflow + htmx branching REUSE; mixin SAMO ako 3 kopije.** 5-2 `BlogIndexView` ima `paginate_queryset()` override (Paginator.get_page() overflow) + `get_template_names()` htmx branching + `@vary_on_headers`. 5-3 arhive (Category+Tag) trebaju isti pattern → POTENCIJALNO 3 kopije (Index+Category+Tag). YAGNI prag (project-context.md:356 „tri slične linije nisu razlog za apstrakciju", ali 3 PUNE kopije paginate+template+vary jeste): Dev odluka — inline kopija (mirror 2-8/2-9 koji imaju duplikate) ILI mali `BlogListingMixin` (paginate_queryset + get_template_names). Default: inline prihvatljivo; mixin ako Dev proceni čistije. NE blokira.

**SM-D10 — NEMA model promene / NEMA migracije / NEMA novog dep.** 5-3 je čist view/template/url/css/js sloj nad 5-1 šemom + 5-2 infrastrukturom. `Post`/`Category`/`Tag`/`PublishedManager`/`translation.py` NETAKNUTI. `makemigrations --check --dry-run` MORA „No changes detected" (Task 10.1). Deferral rich-body (SM-D1) → NEMA bleach/nh3; share/copy = vanilla JS → NEMA novog Python dep. NEMA `uv add`.

### Gotchas (blog-detail-specific traps)

**Gotcha BL3-1 — body render NIKAD `|safe` (stored-XSS).** Najopasnija greška: render `{{ post.body|safe }}` (da bi „rich text" iz epics.md:889 radio) → admin-uneti `<script>` izvršava se kod svakog posetioca (stored-XSS). **MORA `{{ post.body|linebreaks }}`** (auto-escape — SM-D1). Rich-text/sanitizacija je 8.7. AC1 XSS test (9.4) zaključava. NE „popraviti" deferral dodavanjem `|safe`.

**Gotcha BL3-2 — autor None (SET_NULL) bez guarda → „None"/AttributeError.** `{{ post.author.get_full_name }}` kad `author=None` → render „None" ili crash. **MORA `{% if post.author %}` guard** (SM-D5). Test (9.3) sa `author=None`.

**Gotcha BL3-3 — Slične-objave: `Post.objects` (draft leak) / bez exclude-self / category=None crash.** Tri zamke: (1) `Post.objects` umesto `Post.published` → draft u istoj kategoriji procuruje kao „sličan" (draft-not-leaked break — SM-D2); (2) bez `.exclude(pk=post.pk)` → current post je u svojim „sličnima" (besmisleno); (3) `Post.published.filter(category=None)` kad `post.category=None` → vraća SVE objave bez kategorije (pogrešno) ili crash — **MORA `if post.category` guard → else prazna** (SM-D8). Test (9.5) pokriva sve 3.

**Gotcha BL3-4 — tag arhiva bez `.distinct()` (M2M join dup).** `Post.published.filter(tags__slug=...)` preko M2M join-a može vratiti duplikate ako post ima više tagova koji match-uju (single-slug filter retko duplira jer join match-uje 1 red, ali `.distinct()` je KANONSKI M2M-guard pattern) → **`.distinct()`** (SM-D4/IMP-6a). Test (9.7) — kreiraj post sa 2 taga, filtriraj po 1 → post se pojavljuje TAČNO JEDNOM (kanonski M2M-guard).

**Gotcha BL3-5 — 5-2 detail testovi MORAJU ostati zeleni (NE menjaj test_blog_urls.py).** 5-3 OBOGAĆUJE `BlogPostDetailView` (get_queryset proširenje + get_context_data). Ako Dev slučajno promeni `context_object_name`/`template_name`/`Post.published` bazu → 5-2 `test_blog_urls.py` (detail-200/draft-404/future-404/context_object_name/no-oracle) PUCA. **NE menjaj taj fajl** — 5-3 obogaćenje mora biti aditivno (Task 9.13 lock). Ako 5-3 test traži drugačiji detail behavior → STOP (kontrakt break).

**Gotcha BL3-6 — url-ordering: arhive PRE catch-all (SM-D3 — kanonska higijena, NE shadow-fix).** Arhive (2-segment `blog/kategorija/<slug>/`) registruj PRE catch-all detail-a (1-segment `blog/<slug>/`) kao kanonsku disciplinu (specifične-PRE-catch-all). NAPOMENA (IMP-5): 2-segment i 1-segment se strukturno NE preklapaju — redosled NIJE load-bearing za shadowing (ranija „captureovati kategorija/tag kao slug" pretpostavka je netačna; 1-segment detail ionako ne pasuje 2 segmenta). Post sa slug-om „kategorija"/„tag" ostaje dostupan na 1-segment detail ruti. **Arhive PRE detail** (Task 1.1) je dobra higijena, ali NE garant protiv kolizije (koje nema). Test (9.8) `resolve(...).func.view_class` zaključava korektan resolver-order u oba smera.

### Project Structure Notes

- `apps/blog/` POSTOJI (5-1 models + 5-2 views/urls/templates/css). 5-3 EDIT `views.py`+`urls.py` + NEW ~4 template-a + NEW/EDIT css + NEW js. NEMA `forms.py`/`context_processors.py` (context_processor=5-4).
- View pattern REUSE: `BlogPostDetailView` mirror `ProductDetailView` (2-7 — get_context_data similar_products auto-fallback + select_related/prefetch). `BlogCategoryView`/`BlogTagView` mirror `BlogIndexView` (5-2 — ListView+paginate+htmx+Paginator.get_page+vary_on_headers) + `ProductListView` family (2-8/2-9).
- Template REUSE: `post_detail.html` obogaćuje 5-2 placeholder; `_similar_posts.html` mirror 2-7 `_similar_products.html`; `blog_archive.html` REUSE 5-2 `_post_results.html`/`_post_card.html`/`_blog_empty_state.html`; `_social_share.html` NOVO.
- Media REUSE: `{% responsive_picture %}` (2-3) za naslovnu sliku + Slične-objave kartice.
- i18n: arhive pod `i18n_patterns` (5-2 mount `apps.blog.urls` već postoji — 5-3 SAMO dodaje rute u taj include). `reverse("blog:category"/"blog:tag")` daju locale prefiks.
- **FORWARD-DEP konzumenti:** 5-4 (footer — nezavisan; čita `Post.published`), 8.7 (WYSIWYG body rich-render + sanitizacija — zameni `|linebreaks` sanitizovan-`|safe`; SM-D1 forward-note).
- **INHERITED kontrakt (5-3 nasleđuje, NE menja):** 5-2 `BlogPostDetailView` placeholder (SM-D2) + `blog:detail` URL + `_post_card.html`/`_post_results.html`/`_blog_empty_state.html` partials + blog-listing.css/coric-blog-card.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-5.3] (`:881-893`) — `/sr/blog/<slug>/`: naslovna slika, datum+autor+kategorija meta, naslov, telo (rich text — DEFER 8.7 SM-D1), „Slične objave" (2-4 iz iste kategorije), social share (FB/Viber/WhatsApp/Copy-link, sticky-left desktop/below-title mobile), kategorija→`/sr/blog/kategorija/<slug>/`, tag→`/sr/blog/tag/<slug>/`, meta title/desc iz title+perex (override=Epic 6)
- [Source: _bmad-output/planning-artifacts/epics.md#Story-5.2] (`:866-879`) — placeholder detail koji 5-3 obogaćuje (5-2 SM-D11)
- [Source: _bmad-output/planning-artifacts/epics.md#Story-5.4] (`:895-906`) — footer (nezavisno od 5-3)
- [Source: apps/blog/views.py:90-110] — 5-2 `BlogPostDetailView` placeholder (model=Post; get_queryset=Post.published.select_related("category"); context_object_name="post"; template blog/post_detail.html; FORWARD-NOTE 5-3 N+1 :98-100 — proširi select_related("author")/prefetch_related("tags"))
- [Source: apps/blog/views.py:32-87] — 5-2 `BlogIndexView` (ListView + paginate_by + get_template_names htmx branching :46-49 + Paginator.get_page override :59-71 + categories_for_dropdown/active_filters/count :73-87 + @vary_on_headers :32) — mirror za arhive
- [Source: apps/blog/urls.py:15-18] — 5-2 `app_name="blog"` + `blog:index` `blog/` + `blog:detail` `blog/<slug>/` (5-3 dodaje kategorija/tag PRE catch-all — SM-D3)
- [Source: apps/blog/models.py] — Post (body PLAIN TextField :134-136; main_image nullable :137-143; category FK SET_NULL :144-151; tags M2M :152-157; author FK AUTH_USER_MODEL SET_NULL :158-165 [NULL guard]; perex :131-133; get_absolute_url=reverse("blog:detail") :207-209; Meta.ordering :182); Post.published manager :179
- [Source: apps/blog/managers.py:24-29] — `PublishedManager.get_queryset()` → `.filter(status="published", published_at__lte=now)` (draft-not-leaked granica — SM-D2)
- [Source: apps/blog/tests/test_blog_urls.py] — 5-2 detail testovi (detail-200/draft-404/future-404/context_object_name=post/no-oracle) koji MORAJU OSTATI ZELENI (SM-D2/Gotcha BL3-5)
- [Source: apps/blog/tests/conftest.py] — `make_post`/`make_category`/`make_tag`/`author_user` factory helpers (REUSE; tags kwarg :109/:119)
- [Source: apps/products/views.py:73-179] — `ProductDetailView` (DetailView; get_queryset select_related+prefetch :104-128; get_context_data similar_products auto-fallback Product.objects.filter(brand=...,is_published=True).exclude(pk=...).order_by("-created_at")[:_SIMILAR_PRODUCTS_LIMIT] :148-152; `_SIMILAR_PRODUCTS_LIMIT=4` :33) — mirror za blog Slične-objave + detail
- [Source: templates/products/product_detail.html:43-46] — „Slične objave" sekcija `{% if similar_products %}` + `{% include "products/partials/_similar_products.html" %}` (mirror za blog)
- [Source: templates/blog/post_detail.html:18-20] — 5-2 placeholder body `{{ post.body|linebreaks }}` + TODO komentar (5-3/8.7 rich-render forward-note — SM-D1)
- [Source: templates/blog/partials/_post_card.html] — kartica REUSE za Slične-objave + arhiva grid
- [Source: templates/blog/partials/_post_results.html] — results grid + paginacija + OOB aria-live REUSE za arhive
- [Source: templates/blog/partials/_blog_empty_state.html] — empty state REUSE (arhiva 0-objava grana)
- [Source: templates/base.html:10-11,29] — `{% block meta_description %}` + `{% block title %}` (SM-D7 override) + `{% aria_live %}` singleton (Copy-link najava — SM-D6)
- [Source: config/urls.py:31] — `path("", include("apps.blog.urls"))` (5-2 mount — 5-3 SAMO dodaje rute u include, NE dira config/urls.py)
- [Source: static/css/components/blog-listing.css] — coric-blog-card + grid (5-3 dopuna blog-detail.css ili EDIT)
- [Source: _bmad-output/implementation-artifacts/5-2-blog-index-strana-sa-paginacijom-filter.md] — 5-2 SM-D11 (placeholder kontrakt 5-3 nasleđuje) + SM-D4 NAPOMENA (index filter vs arhiva — DVE razne stvari) + FORWARD-NOTE 5-3 N+1
- [Source: _bmad-output/project-context.md] — :168-179 CBV DetailView/ListView + select_related/prefetch N+1 MANDATORY :743; :161-166 URL ASCII slug + reverse; :184-194 HTMX request.htmx + OOB aria-live; :338 vanilla JS NIKAD jQuery (Copy-link); :497-527 pune dijakritike; :350-353 komentari samo WHY; XSS/security boundary (body render — SM-D1)

### Open Questions (OQ)

- **OQ-1 (slug-ovi „kategorija"/„tag" — RESOLVED, nema kolizije; IMP-5):** Ranija pretpostavka da SM-D3 url-ordering čini post sa slug-om „kategorija"/„tag" nedostupnim (shadow-ovanim) je **POGREŠNA i ispravljena**. Arhive su 2-segmentne (`blog/kategorija/<slug>/`) a detail je 1-segmentni (`blog/<slug>/`) — strukturno se ne preklapaju. Post sa slug-om TAČNO „kategorija" je dostupan na `/sr/blog/kategorija/` (1 segment → `BlogPostDetailView(slug="kategorija")`); `/sr/blog/kategorija/<x>/` (2 segmenta) je arhiva. **Nema rezervisanih slug-ova, nema realne kolizije.** url-ordering je kanonska higijena (specifične-PRE-catch-all), NE load-bearing za shadowing. RESOLVED — ne blokira, nema izuzetka za prihvatanje.
- **OQ-2 (Slične-objave fallback kad kategorija ima <2 published):** SM-D8 → render koliko ima (graceful, čak i 1; sekcija se NE render-uje ako 0). epics.md:889 traži „2-4" — ali ako kategorija ima samo 1 drugu published objavu, prikaži 1 (NE fabrikuj fallback na drugu kategoriju kao 2-7 manual/auto — blog je samo-auto same-category; YAGNI). Ako biznis traži cross-category fallback kad nema dovoljno → 8.x. Default: same-category-only, render-koliko-ima.
- **OQ-3 (autor display ime):** SM-D5 → `get_full_name|default:username` ili samo `username`. Default `get_full_name` sa username fallback (lepše ime ako autor ima first/last). UX/Dev sitno; NE blokira. (Autor-profil-link van scope-a.)
- **OQ-4 (Copy-link clipboard fallback za HTTP/stari browser + Viber desktop):** `navigator.clipboard.writeText(share_url)` zahteva secure context (HTTPS — prod ima SECURE_SSL_REDIRECT; localhost je secure). Stari browser bez clipboard API → graceful no-op ili `document.execCommand` fallback (deprecated). Default: `navigator.clipboard` (prod HTTPS pokriva; localhost OK). Fallback opciono (YAGNI — moderni browseri + HTTPS prod). **Viber (IMP-3):** `viber://forward?text=` je mobilni app deep-link; na DESKTOP-u bez Viber desktop klijenta gracefully no-op-uje (browser ignoriše nepoznat scheme) — PRIHVATLJIVO za mobile-first poljoprivrednu publiku (primarni share kanal je mobilni). NE blokira.
- **OQ-5 (arhiva empty-state copy — RESOLVED; IMP-1):** validna kategorija/tag sa 0 published → empty state. **ODLUKA: arhive views prosleđuju `active_filters={"kategorija": <slug>}`** u kontekst → `_blog_empty_state.html` `{% if active_filters.kategorija %}` filter-0 grana se aktivira → render-uje arhiva-prikladnu „Nema objava u ovoj kategoriji." + „Pokušajte sa drugom kategorijom ili pogledajte sve objave." + „prikaži sve" → `blog:index` link. Bez ovog prosleđivanja arhiva-empty bi render-ovala POGREŠNU else-granu (generička „Uskoro nove priče sa polja" + home CTA — semantički netačno za arhivu). Pristup (a) izabran (active_filters pass-through) jer NE menja `_blog_empty_state.html` (5-2 regression guard) i postojeća filter-0 kopija je već arhiva-prikladna. Test (9.6/9.7) zaključava `data-testid="blog-empty-filter"` (NE `blog-empty-home`). RESOLVED — ne blokira; specifikovano u Task 3.1/3.2 + AC3/AC4.

### Testing notes (šta TEA pokriva — RED phase)

- **Obogaćen detail (AC1):** published Post → slika(`{% if %}` guard)+datum+autor(`{% if %}` NULL guard SM-D5)+kategorija-link(`/sr/blog/kategorija/<slug>/`)+naslov+telo(`|linebreaks` plain)+tag-linkovi(`/sr/blog/tag/<slug>/`); `context_object_name="post"`. **autor=None → „autor" linija IZOSTAVLJENA (NE „None"/crash); autor sa praznim first/last → username (IMP-6b). XSS: body `<script>` → ESCAPE-ovan (NE `|safe`).**
- **Slične objave (AC2):** same-category + exclude-self + draft-excluded + bounded≤4 + category=None→prazna + 0-similar→sekcija-ne-render. **Post.published (draft-not-leaked).**
- **Kategorija arhiva (AC3):** `/sr/blog/kategorija/<slug>/` → 200 Post.published-K (najnovije-prvo); paginacija(25→10, ?page=999 clamp); HTMX→`_post_results.html`+OOB; **bad slug→404**; valid-K-0-published→200+**arhiva-prikladan empty (`blog-empty-filter`, NE home CTA — IMP-1)**; **NEMA filter dropdown (`<select name="kategorija">` odsutan — IMP-6c)**; draft-not-leaked.
- **Tag arhiva (AC4):** `/sr/blog/tag/<slug>/` → 200 Post.published-tag; **`.distinct()` M2M-guard (post sa 2 taga, filter po 1 → tačno JEDNOM — IMP-6a)**; bad slug→404; valid-tag-0-published→arhiva-prikladan empty (IMP-1); draft-not-leaked; HTMX.
- **URL ordering (AC5 — kanonska higijena, NE shadow-fix; IMP-5):** reverse category/tag/detail; **`resolve("/sr/blog/kategorija/x/").func.view_class is BlogCategoryView`** (2-segment); resolve tag→BlogTagView; resolve `/sr/blog/post/`→BlogPostDetailView (1-segment catch-all radi; post sa slug-om „kategorija" DOSTUPAN na 1-segment ruti — 2-segment arhiva strukturno NE shadow-uje 1-segment detail).
- **Social share (AC6):** 4 dugmeta FB/Viber/WhatsApp/Copy-link; **`share_url` view-context==apsolutni (IMP-2); egzaktni href-ovi FB `sharer.php?u=`/WhatsApp `wa.me/?text=`/Viber `viber://forward?text=` (IMP-3)**; Copy `[data-share-copy]`+aria-label pun-dijakritik; data-testid.
- **Meta (AC7):** `<title>`⊇post.title; `<meta description>`⊇post.perex; **prazan perex → description==title (`|default:post.title` — IMP-4)**; NEMA OG/twitter.
- **N+1 (AC8):** detail assertNumQueries KONSTANTAN (2 taga+4 slične == 5 tagova+4 slične); select_related("category","author")+prefetch_related("tags"); arhiva count-variation(3==10); Lock N empirijski GREEN.
- **draft-not-leaked SVUDA (AC9):** draft NEVIDLJIV na detail(404)+Slične(excluded)+kategorija-arhiva(excluded)+tag-arhiva(excluded) — 4 tačke Post.published.
- **i18n (AC9):** pun-dijakritik string-ovi; sr render (+smoke hu/en); slug ASCII.
- **5-2 regression (Task 9.13 — KRITIČNO):** `test_blog_urls.py` (detail-200/draft-404/future-404/context_object_name/no-oracle) OSTAJU ZELENI (NE menja se taj fajl).
- **TEA policy:** `@pytest.mark.django_db`; pytest-django (NE unittest). REUSE 5-1 `conftest.py` (`make_post`/`make_category`/`make_tag`/`author_user`). HTMX kroz `client.get(url, HTTP_HX_REQUEST="true")`. assertNumQueries lock N empirijski (TEA struktura, Dev broj). **Dev NIKAD ne piše testove.**

## Risk-Tier Self-Assessment

**TIER: HIGH.**

**Obrazloženje:** Pun javni detail + 2 nove javne arhive view + body-render security granica + url-ordering. Kombinuje:
1. **Body-render XSS granica (SM-D1/Gotcha BL3-1)** — epics.md:889 traži „rich text" ali model je plain TextField; pogrešno „popravljanje" deferral-a dodavanjem `|safe` (bez sanitizacije) = stored-XSS (admin-uneti `<script>` izvršava se javno). Mora `|linebreaks` (auto-escape) + XSS test lock; rich-text DEFER na 8.7.
2. **2 nove javne view (arhive) + url-ordering (SM-D3/SM-D4)** — `BlogCategoryView`/`BlogTagView` registrovane PRE catch-all detail-a (resolver-order lock); nepostojeća slug→404; `.distinct()` na tag M2M; mirror BlogIndexView pattern (paginate+htmx+overflow+vary).
3. **draft-not-leaked na 4+ nova puta (SM-D2/AC9)** — detail + Slične-objave + kategorija-arhiva + tag-arhiva svaki kroz `Post.published` (NIKAD `Post.objects`); najlakša greška procuruje draft/scheduled javno. Test asertuje draft nevidljiv na svakoj.
4. **OBOGAĆENJE-NE-REWRITE (SM-D2/Gotcha BL3-5)** — 5-3 proširuje 5-2 `BlogPostDetailView` (get_queryset+get_context_data) BEZ menjanja placeholder kontrakta; 5-2 detail testovi MORAJU ostati zeleni (aditivno obogaćenje).
5. **N+1 na Slične-objave + autor/tagovi + arhive (SM-D8/AC8)** — detail render-uje autor FK + tags M2M + Slične-objave query → select_related("author")+prefetch_related("tags")+bounded similar query; assertNumQueries lock. autor NULL guard (SM-D5).

NIJE MEDIUM: body-XSS granica + 2 nove javne view + url-ordering-before-catch-all + draft-leak na 4 puta + obogaćenje-bez-rewrite (5-2 test regression) + N+1 zajedno prelaze prag. Mitigacija: SVI patterni REUSE iz 5-2/2-7 (dokazani — ListView/DetailView/HTMX/paginacija/similar/N+1); NEMA migracije/model promene (0 schema rizik); NEMA novog dep (deferral rich-body); body `|linebreaks` (najjednostavniji XSS-safe; rich=8.7); autor NULL guard + draft-not-leaked + XSS + url-ordering + 5-2-regression su glavni risk-mitigacioni testovi. Gotchas (BL3-1..BL3-6) eksplicitno dokumentovani.
