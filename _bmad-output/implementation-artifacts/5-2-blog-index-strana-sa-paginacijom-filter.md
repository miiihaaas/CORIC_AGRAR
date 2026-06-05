---
story_id: "5.2"
story-key: 5-2-blog-index-strana-sa-paginacijom-filter
title: Blog Index Strana sa Paginacijom + Filter
status: ready-for-dev
epic: 5
epic_num: 5
epic_title: Blog (Priče sa polja)
module: blog
created: 2026-06-04
last_modified: 2026-06-04
complexity: H
author: Mihas (SM autonomous; DRUGA story Epic 5 — Blog „Priče sa polja". PRVI KONZUMENT 5-1 modela. Javna blog INDEX strana `/sr/blog/` koja listira OBJAVLJENE Post-ove kroz `Post.published` manager (NIKAD `Post.objects` — draft/future MORA biti nevidljiv javno) kao kartice (main_image, datum, naslov, perex, CTA „SAZNAJ VIŠE"), paginacija 10/strani, filter po kategoriji + empty state + responsive 1col/2-3col. KLJUČNA SEQUENCING ODLUKA (SM-D11): 5-2 kreira NOVI `apps/blog/urls.py` sa `app_name="blog"` + DVA path-a — `blog:index` (BlogIndexView, `/sr/blog/`) I `blog:detail` (`/sr/blog/<slug>/` → MINIMALNA placeholder DetailView koju 5-3 OBOGAĆUJE) — tako da `Post.get_absolute_url()` (iz 5-1, reverse('blog:detail')) RAZREŠAVA i kartice linkuju ispravno. POSLEDICA: 5-1 `test_get_absolute_url.py` koji asertuje `NoReverseMatch` MORA se ažurirati (5-2 owns taj update — sad razrešava na `/sr/blog/<slug>/`). HTMX vs plain: HTMX category filter (mirror 2-9 UsedMachineryListView request.htmx branching + OOB aria-live + push-url) — opravdano jer epics.md:876 traži filter + projekt-konvencija (2-8/2-9/2-13) je HTMX swap. N+1: `Post.published.select_related("category")` zaključan `assertNumQueries` (BEZ `prefetch_related("tags")` — kartica ne renderuje tagove; IMP-1). Mount: `path("", include("apps.blog.urls"))` u config/urls.py pod i18n_patterns. NEMA model promene / NEMA migracije (views/templates/urls SAMO — konzumira 5-1 šemu). RISK TIER: HIGH — nova javna view + HTMX filter + N+1 + URL wiring koji aktivira 5-1 get_absolute_url + blog:detail placeholder kontrakt koji 5-3 nasleđuje.)
depends_on:
  - 5-1-blogpost-category-tag-modeli-admin-stub              # Post/Category/Tag modeli; Post.published manager (status='published' AND published_at__lte=now — draft-not-leaked granica); Post.get_absolute_url=reverse('blog:detail'); Post.main_image/perex/title/published_at/category fields; Category model za filter dropdown
  - 1-4-i18n-setup-sa-locale-url-routing-i-switcher          # i18n_patterns (blog URL pod /sr/blog/); {% translate %}/{% blocktranslate %}; LANGUAGE switcher
  - 2-8-traktori-listing-strana-sa-htmx-filterima            # ListView + paginate_by + request.htmx get_template_names() branching + OOB aria-live guarded {% if request.htmx %} + @vary_on_headers('HX-Request') + {% querystring %} paginacija PATTERN; coric-product-card grid; _empty_state PATTERN
  - 2-9-polovna-mehanizacija-listing-sa-htmx-filterima       # HTMX category dropdown filter (?kategorija=<slug>) + Paginator.get_page() overflow safety + active_filters context + invalid-slug normalizacija + categories_for_dropdown PATTERN (1:1 mirror za blog category filter)
  - 2-3-product-image-thumbnail-pipeline                     # sorl-thumbnail responsive_picture inclusion tag (main_image srcset + loading=lazy) — REUSE za blog card main_image
---

# Story 5.2: Blog Index Strana sa Paginacijom + Filter

Status: ready-for-dev

## Opis

As a **posetilac sajta Ćorić Agrar**,

I want **javnu blog index stranu `/sr/blog/` koja listira OBJAVLJENE „Priče sa polja" (najnovije prvo) kao kartice (naslovna slika, datum, naslov, perex, CTA „SAZNAJ VIŠE"), sa paginacijom 10/strani i filterom po kategoriji**,

so that **lakše nalazim teme koje me zanimaju i otvaram pojedinačnu objavu**.

Ovo je **DRUGA story Epic 5 (Blog — Priče sa polja)** i **PRVI KONZUMENT 5-1 model-temelja**: prva strana koja čita `Post`/`Category` kroz `Post.published` manager. 5-1 je položio modele (NEMA nijednog view-a/URL-a/template-a); 5-2 dodaje `views.py` + `urls.py` + `templates/blog/` (index strana + card partial + results partial) + mount u `config/urls.py`. **NEMA model promene, NEMA migracije** — 5-2 SAMO konzumira 5-1 šemu kroz view/template/URL sloj.

5-2 takođe rešava **KLJUČNU SEQUENCING ODLUKU (SM-D11)**: 5-1 `Post.get_absolute_url()` poziva `reverse("blog:detail", kwargs={"slug": ...})` koji trenutno raise-uje `NoReverseMatch` (jer blog URL-ovi NE postoje). Da bi kartice na index strani linkovale na `/sr/blog/<slug>/`, 5-2 MORA registrovati `blog:detail` URL. 5-2 ga registruje sa **MINIMALNOM placeholder `BlogPostDetailView`** koju **Story 5-3 OBOGAĆUJE** (slične objave, social share, telo, kategorija/tag linkovi). Time `get_absolute_url` razrešava, kartice linkuju, a 5-3 nasleđuje radni URL + placeholder view koji proširuje.

### IN SCOPE (šta ova story isporučuje)

1. **`apps/blog/views.py`** — `BlogIndexView(ListView)` (mirror 2-8/2-9 `TractorListView`/`UsedMachineryListView`): `model=Post`, queryset kroz **`Post.published`** (NIKAD `Post.objects` — SM-D2), `.select_related("category")` (N+1 lock — SM-D6; **BEZ `prefetch_related("tags")`** — kartica ne renderuje tagove, IMP-1), `paginate_by=10` (epics.md:875 — SM-D3), category filter `?kategorija=<slug>` (SM-D4), `get_template_names()` request.htmx branching (full page vs results partial — SM-D5), `Paginator.get_page()` overflow safety (mirror 2-9 SM-D25), `categories_for_dropdown` + `active_filters` + `count` context. **`BlogPostDetailView(DetailView)`** — MINIMALAN placeholder (SM-D11): `model=Post`, queryset kroz `Post.published.select_related("category")`, `context_object_name="post"`, render bazičnog `blog/post_detail.html` (naslov + telo + datum); **5-3 OBOGAĆUJE** (slične objave, social share, kategorija/tag linkovi, meta — uz `select_related("author")`/`prefetch_related("tags")` kad ih renderuje).
2. **`apps/blog/urls.py`** (NOVO — 5-2 kreira; SM-D11) — `app_name="blog"` + `blog:index` (`path("blog/", BlogIndexView, name="index")`) + `blog:detail` (`path("blog/<slug:slug>/", BlogPostDetailView, name="detail")`). Mount u `config/urls.py` `path("", include("apps.blog.urls"))` pod `i18n_patterns` → `/sr/blog/` + `/sr/blog/<slug>/`.
3. **`templates/blog/blog_index.html`** — full-page index (mirror `tractor_listing.html`): header (naslov „Priče sa polja" + lead), category filter sekcija, results sekcija (`{% include "blog/partials/_post_results.html" %}`).
4. **`templates/blog/partials/_post_results.html`** — results grid partial (HTMX swap target — mirror `_results_grid.html`): kartice grid + paginacija (`{% querystring %}` mirror 2-8) + empty state include + guarded `{% if request.htmx %}` OOB aria-live announcement.
5. **`templates/blog/partials/_post_card.html`** — pojedinačna blog kartica: `main_image` (responsive_picture srcset + loading=lazy — REUSE 2-3), `published_at` datum (`|date:"SHORT_DATE_FORMAT"` — locale-aware, IMP-2/OQ-1 RESOLVED), `title`, `perex`, CTA „SAZNAJ VIŠE" → `post.get_absolute_url`.
6. **`templates/blog/partials/_blog_filter.html`** — category filter (dropdown — mirror 2-9 `_used_filter_form.html`): `<select name="kategorija">` „Sve kategorije" + Category opcije, HTMX `hx-get`/`hx-target`/`hx-push-url`, htmx-indicator spinner.
7. **`templates/blog/partials/_blog_empty_state.html`** — empty state sa DVE grane (`{% if active_filters.kategorija %}` — IMP-4): filter-0 → „Nema objava u ovoj kategoriji." + „prikaži sve" link (`blog:index`); prazan-blog → „Uskoro nove priče sa polja" (epics.md:879) + CTA „POVRATAK NA POČETNU" → `pages:home`.
8. **`templates/blog/post_detail.html`** — MINIMALAN placeholder detail (SM-D11) koju 5-3 OBOGAĆUJE: naslov + datum + telo (bez slične-objave/social-share — to je 5-3).
9. **5-1 `test_get_absolute_url.py` AŽURIRANJE (SM-D11/SM-D12) — RANO, uparено sa Task 1 (Task 8.0)** — 5-1 test asertuje `NoReverseMatch`; 5-2 registruje `blog:detail` → test SAD razrešava na `/sr/blog/<slug>/`. 5-2 OWNS taj update (NE 5-3). DVE izmene: (a) prepiši asertaciju `pytest.raises(NoReverseMatch)` → `get_absolute_url() == "/sr/blog/<slug>/"`; (b) ažuriraj STALE docstring/komentar „5.3 ažurira ovaj test" → „5.2 ažurira ovaj test (SM-D12)". TEA uradi PRE `blog:detail` GREEN wiringa (inače crveni CI usred implementacije — vidi Task 8.0/Gotcha BL2-3).
10. **CSS** (blog-listing.css ili REUSE) — responsive grid 1col mobile / 2-3col desktop (epics.md:878). REUSE `coric-product-card` BEM ili novi `coric-blog-card` (Dev/UX odluka — SM-D8); `var(--token)` tokens (NE magic vrednosti).

### OUT OF SCOPE (eksplicitno — granice)

- **PUN Blog Post Detail (slične objave, social share, telo rich-text+video, kategorija/tag linkovi, meta title/description)** = **Story 5-3** (`5-3-blog-post-detail-strana`, epics.md:881-893). 5-2 registruje `blog:detail` URL + MINIMALAN placeholder `BlogPostDetailView` (render naslov+datum+telo) SAMO da `get_absolute_url` razreši i kartice linkuju. **5-3 OBOGAĆUJE istu view klasu** (slične objave iz Category, social share dugmad, `/sr/blog/kategorija/<slug>/` + `/sr/blog/tag/<slug>/` linkovi, meta iz title+perex). 5-2 NE implementira nijedan od tih 5-3 deliverable-a. (Vidi SM-D11 za tačan placeholder kontrakt koji 5-3 nasleđuje.)
- **Footer „Najnovije vesti" dynamic kolona** = **Story 5-4** (`apps/blog/context_processors.py:latest_blog_posts` + footer.html). 5-2 NE dira footer ni context_processor.
- **Home „Priče sa polja" preview popuna** — 3-1 shipped Lorem Ipsum placeholder (`latest_posts=[]` → 2 statičke kartice; 3-1 SM-D7). 5-2 NE dira `apps/pages` ni home template (popuna je 5-4 ili buduća 3-x revizija). 5-2 je SAMO `/sr/blog/` index.
- **Search „Objave" grupa popuna (2-13)** — 2-13 SM-D3 prazan skelet. 5-2 NE dira `apps/search`.
- **Kategorija/Tag arhive strane** (`/sr/blog/kategorija/<slug>/`, `/sr/blog/tag/<slug>/`) — **Story 5-3** (epics.md:891-892). 5-2 filter je querystring `?kategorija=<slug>` na index strani (NE dedikovana arhiva URL). 5-2 NE registruje `blog:category`/`blog:tag` URL-ove (5-3 ih dodaje). (NAPOMENA: 5-2 index filter i 5-3 kategorija-arhiva su DVE razne stvari — index filter sužava listu na `/sr/blog/?kategorija=X`; arhiva je posebna `/sr/blog/kategorija/X/` strana iz 5-3.)
- **SEO/SeoMeta na index/detail** = **Epic 6** (6.1 SeoMeta, 6.2 sitemap BlogPost). 5-2 koristi statički `{% block title %}`/`meta_description` (mirror tractor_listing.html), NE SeoMeta model.
- **Sortiranje/dodatni filteri (po tag-u, datumu, autoru, full-text search)** — NE. epics.md:876 traži SAMO filter po kategoriji. Sort je fiksan `Meta.ordering=["-published_at","-created_at"]` (najnovije prvo — epics.md:874). Tag/datum filter + search nije u 5-2 scope-u (YAGNI; epics ne traži).
- **Featured/istaknuta objava logika** — NE (nema u epics.md:866-879). Sve published objave ravnopravne, sortirane najnovije-prvo.
- **Model promene / migracije** — NEMA. 5-1 šema je finalna; 5-2 je čist view/template/URL sloj. `makemigrations --check` MORA vratiti „No changes" (regression guard — Task gate).
- **Novi dep / WYSIWYG render body-ja** — NE. 5-2 placeholder detail render-uje `body` kao plain (5-3/8.7 rešavaju safe-render/sanitizaciju). NEMA `uv add`.
- **Defensive parsing slider-a (snaga/cena/godina)** — NE primenljivo (blog nema numeričke filtere; SAMO category slug). Invalid category slug → normalizuj na „" (mirror 2-9 IMP-3) + empty/full lista (NE 404).

### Princip

Jedan novi `BlogIndexView(ListView)` (mirror 2-8/2-9) koji čita `Post.published` (NIKAD `Post.objects` — draft/future nevidljiv javno), sa `.select_related("category")` (N+1 lock kroz assertNumQueries; BEZ `prefetch_related("tags")` — kartica ne renderuje tagove, IMP-1), `paginate_by=10`, HTMX category filter (`?kategorija=<slug>` swap + OOB aria-live + push-url — mirror 2-9), `Paginator.get_page()` overflow safety, kartice grid (main_image responsive srcset + datum + title + perex + „SAZNAJ VIŠE" CTA → `get_absolute_url`), empty state, responsive 1col/2-3col. **KLJUČNO:** 5-2 kreira `apps/blog/urls.py` (`app_name="blog"` + `blog:index` + `blog:detail`→placeholder view) tako da 5-1 `get_absolute_url` razreši i kartice linkuju; 5-3 obogaćuje detail view. Mount pod `i18n_patterns` (`/sr/blog/`). Pune dijakritike (č/ć/ž/š/đ) u svim user-facing string-ovima; `{% translate %}`/`{% blocktranslate %}`; .po sr/hu/en. ASCII slug u URL-u. NEMA model promene/migracije. NEMA defensive validacije na internim pozivima. NEMA premature abstrakcije.

### Strukturna arhitektura — repository delta

**5 NOVO (views.py + urls.py + 1 EDIT config/urls.py + ~5 template-a + opciono CSS) + 1 TEST EDIT (5-1 get_absolute_url) + 0 migracija + 0 model promene.**

| Path | Tip | Razlog |
|---|---|---|
| `apps/blog/views.py` | NOVO | `BlogIndexView(ListView)` (`model=Post`; queryset `Post.published.select_related("category")` — BEZ `prefetch_related("tags")` (IMP-1); `paginate_by=10`; `?kategorija` filter; `get_template_names()` request.htmx branching; `Paginator.get_page()` overflow; `categories_for_dropdown`/`active_filters`/`count` context; `@method_decorator(vary_on_headers("HX-Request"))`). `BlogPostDetailView(DetailView)` MINIMALAN placeholder (`model=Post`; queryset `Post.published.select_related("category")`; `context_object_name="post"`; `template_name="blog/post_detail.html"`; SM-D11 — 5-3 OBOGAĆUJE). Mirror `apps/products/views.py`. |
| `apps/blog/urls.py` | NOVO (SM-D11) | `app_name="blog"`; `path("blog/", BlogIndexView.as_view(), name="index")`; `path("blog/<slug:slug>/", BlogPostDetailView.as_view(), name="detail")`. Redosled: `blog/` (index, bez slug-a) PRE `blog/<slug>/` (Django resolver iterira; slug converter zahteva segment posle `blog/`). |
| `config/urls.py` | EDIT | `path("", include("apps.blog.urls"))` u `i18n_patterns` blok (mirror search/pages/forms include linije :29-31). → `/sr/blog/` + `/sr/blog/<slug>/`. |
| `templates/blog/blog_index.html` | NOVO | Full-page index (`{% extends "base.html" %}`; mirror `tractor_listing.html`): header (naslov+lead), `{% include "blog/partials/_blog_filter.html" %}`, results sekcija = SAMO `{% include "blog/partials/_post_results.html" %}` BEZ wrapping id div-a (id="blog-results" je U partialu — mirror tractor_listing.html koji NE wrap-uje _results_grid.html). `{% block title %}`/`meta_description` statički. |
| `templates/blog/partials/_post_results.html` | NOVO | HTMX swap target (mirror `_results_grid.html` 1:1): partial SE SAM otvara `<div id="blog-results">` (mirror `<div id="tractor-results">` :3) koji obuhvata `{% if posts %}` grid (`{% for post in posts %}{% include "blog/partials/_post_card.html" %}{% endfor %}`) + paginacija (`{% querystring page=... %}` + hx-get/hx-target="#blog-results"/hx-swap="innerHTML"/hx-push-url mirror 2-8 :39-58) `{% else %}{% include "blog/partials/_blog_empty_state.html" %}` + `</div>`; POSLE id div-a guarded `{% if request.htmx %}` OOB `<div hx-swap-oob="innerHTML:#aria-live">` count announcement (mirror SM-D23 2-8 :69-71). Tačno JEDAN id="blog-results", unutar partiala. |
| `templates/blog/partials/_post_card.html` | NOVO | `<a href="{{ post.get_absolute_url }}">`: `main_image` (`{% responsive_picture post.main_image alt=post.title sizes=... loading="lazy" %}` REUSE 2-3, `{% if post.main_image %}` guard), datum (`{{ post.published_at|date:"SHORT_DATE_FORMAT" }}` — locale-aware, IMP-2), `{{ post.title }}`, `{{ post.perex }}`, CTA „SAZNAJ VIŠE". data-testid. |
| `templates/blog/partials/_blog_filter.html` | NOVO | Category dropdown (mirror 2-9 `_used_filter_form.html` — NE 2-8 slider): `<form method="get" hx-get hx-trigger="change delay:300ms" hx-target="#blog-results" hx-swap="innerHTML" hx-push-url="true">` + `<select name="kategorija">` „Sve kategorije" + `{% for c in categories_for_dropdown %}` opcije (`{% if active_filters.kategorija == c.slug %}selected{% endif %}`) + htmx-indicator spinner. „dropdown" izabran (epics.md:876 „dropdown ili tabovi" — SM-D8). |
| `templates/blog/partials/_blog_empty_state.html` | NOVO | DVE grane `{% if active_filters.kategorija %}` (IMP-4): filter-0 → „Nema objava u ovoj kategoriji." + „prikaži sve" link (`blog:index`); `{% else %}` prazan-blog → „Uskoro nove priče sa polja" (epics.md:879) + „POVRATAK NA POČETNU" → `{% url 'pages:home' %}` (mirror `_empty_state.html`). |
| `templates/blog/post_detail.html` | NOVO (placeholder — SM-D11) | MINIMALAN detail koju 5-3 OBOGAĆUJE: `{% extends "base.html" %}`; naslov + datum + telo (`{{ post.body }}` plain — safe-render je 5-3/8.7). NEMA slične-objave/social-share (5-3). |
| `static/css/blog-listing.css` (ili REUSE) | NOVO/EDIT (SM-D8) | Responsive grid 1col mobile / 2-3col desktop (epics.md:878); `coric-blog-card` BEM ILI REUSE `coric-product-card`; `var(--token)` tokens. main.css `@import` ako novi fajl. (Dev/UX odluka — REUSE preferiran ako product-card pasuje.) |
| `apps/blog/tests/test_get_absolute_url.py` | EDIT (SM-D11/SM-D12 — TEA) | 5-1 test asertuje `NoReverseMatch`; 5-2 registruje `blog:detail` → prepiši asertaciju da `get_absolute_url` razrešava na `/sr/blog/<slug>/` (5-2 OWNS — Gotcha BL2-3). |
| `apps/blog/tests/test_views.py` | NOVO (TEA) | AC1-AC8 (vidi Testing) — BlogIndexView + filter + paginacija + N+1 + empty state + URL wiring + placeholder detail. |
| `locale/{sr,hu,en}/LC_MESSAGES/django.po` | EDIT | Novi `{% translate %}` string-ovi (naslov, lead, „SAZNAJ VIŠE", „Sve kategorije", empty state, „POVRATAK NA POČETNU", paginacija, aria announcement). `just messages` regeneriše. |
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | EDIT | `5-2-blog-index-strana-sa-paginacijom-filter` → `ready-for-dev` (epic-5 ostaje `in-progress`). SM handoff (NIJE deliverable). |

**NETAKNUTO (regression guards):** `apps/blog/models.py`/`managers.py`/`translation.py`/`admin.py` (5-1 — NE menja se; 5-2 SAMO konzumira); `apps/blog/migrations/` (NEMA nove migracije — `makemigrations --check` MORA „No changes"); svi postojeći app-ovi (`products`/`brands`/`search`/`pages`/`forms`/`core`/`media_pipeline`); `apps/pages` home `latest_posts=[]` placeholder (3-1 SM-D7 — 5-4/3-x popunjava, NE 5-2); `templates/partials/footer.html` (1-8/5-4); `apps/search` „Objave" prazna grana (2-13 SM-D3); `pyproject.toml` (NEMA novog dep). **0 migracija, 0 model promene, 0 novi dep.** `PostAdmin.view_on_site` ostaje `False` u 5-2 (re-enable je 5-3/8.7 — `get_absolute_url` sad razrešava, ali admin „View on site" re-enable nije 5-2 scope; OQ-3).

## Kriterijumi prihvatanja

**AC1 — `BlogIndexView` listira `Post.published` (NIKAD `Post.objects`) kao kartice, najnovije prvo; draft/future NEVIDLJIV javno (SM-D2)**

- **Given** 5-1 `Post`/`Category` modeli + `Post.published` manager (status="published" AND published_at__lte=now); `apps/blog/views.py` + `urls.py` registrovani (AC6); GET `/sr/blog/`
- **When** posetilac otvori `/sr/blog/` (bez filtera)
- **Then** `BlogIndexView(ListView)` MORA:
  - `model = Post`; `context_object_name = "posts"`; queryset bazira na **`Post.published`** (NIKAD `Post.objects` — draft-not-leaked granica; SM-D2)
  - render-uje SAMO objave sa `status="published"` I `published_at__lte=now` (najnovije prvo kroz `Meta.ordering=["-published_at","-created_at"]` iz 5-1)
  - svaka kartica prikazuje: `main_image` (ako postoji — responsive_picture srcset; AC4), `published_at` datum (`|date:"SHORT_DATE_FORMAT"` — locale-aware; sr → DD.MM.YYYY.), `title`, `perex`, CTA „SAZNAJ VIŠE"
  - **DRAFT post NIJE u listi** (test: kreiraj DRAFT → NE pojavljuje se na `/sr/blog/`)
  - **PUBLISHED + future published_at NIJE u listi** (test: scheduled post → NE pojavljuje se)
  - **PUBLISHED + published_at=None NIJE u listi** (test: NULL <= now je False)
  - **PUBLISHED + past published_at JESTE u listi**
- **And** status code 200; template `blog/blog_index.html` (non-HTMX); `<h1>` naslov „Priče sa polja" (pun dijakritik)

**AC2 — N+1 lock: `select_related("category")` + `assertNumQueries` (SM-D6)**

- **Given** AC1; više published Post-ova svaki sa `category` FK
- **When** GET `/sr/blog/` render-uje listu
- **Then** queryset MORA imati `.select_related("category")` (FK — kartica/filter ne sme N+1 per-post category lookup). **`prefetch_related("tags")` se NE dodaje u 5-2** (index kartica NE renderuje tagove — epics.md:874 samo slika/datum/naslov/perex/CTA; prefetch bez konzumenta je no-op koji assertNumQueries NE hvata i protivreči YAGNI rationale-u za `select_related("author")` izostavljanje; vidi SM-D6/IMP-1). 5-3 detail dodaje `prefetch_related("tags")`/`select_related("author")` kad ih renderuje.
- **And** broj SQL upita je **KONSTANTAN bez obzira na broj objava** na strani (test: `assertNumQueries(N)` sa 3 objave == `assertNumQueries(N)` sa 10 objava — fiksni budžet; N empirijski zaključan u GREEN: Post slice + count + category select_related join + categories_for_dropdown + session/middleware overhead). Dodavanje objava NE sme povećati query broj (count-variation lock hvata baš `select_related("category")` — bez njega bi N rastao po objavi).

**AC3 — Paginacija 10 objava/strani; overflow-safe (epics.md:875; SM-D3)**

- **Given** AC1; 25+ published objava
- **When** GET `/sr/blog/` pa `/sr/blog/?page=2` pa `/sr/blog/?page=999`
- **Then**:
  - `paginate_by = 10` (epics.md:875 — TAČNO 10/strani); `is_paginated=True` kad >10 objava
  - strana 1 prikazuje 10 objava; strana 3 (od 25) prikazuje 5; `page_obj`/`paginator` u kontekstu
  - paginacija nav (Prethodna/Sledeća + „Strana X od Y") render-uje se SAMO kad `is_paginated` (mirror 2-8 `_results_grid.html`)
  - **`?page=999` (overflow) → clamp na poslednju stranu (NE 404 EmptyPage)** — `Paginator.get_page()` override (mirror 2-9 SM-D25)
  - paginacija linkovi koriste `{% querystring page=... %}` (čuva `?kategorija` filter kroz stranice — mirror 2-8) + HTMX `hx-get`/`hx-target="#blog-results"`/`hx-swap="innerHTML"`/`hx-push-url="true"`
  - **kombinovani deep-link** (non-HTMX GET `/sr/blog/?kategorija=<slug>&page=2`) → full page, dropdown pre-selektovan na `<slug>`, strana-2 rezultati TE kategorije, filter sačuvan kroz paginaciju (IMP-3; test 8.6b)
- **And** `?page=abc` (invalid) → strana 1 (get_page graceful)

**AC4 — Kartica: main_image (responsive srcset) + datum + title + perex + „SAZNAJ VIŠE" → get_absolute_url (epics.md:874; SM-D7)**

- **Given** AC1; published Post sa main_image + published_at + title + perex
- **When** kartica se render-uje (`_post_card.html`)
- **Then**:
  - `main_image` kroz `{% responsive_picture post.main_image alt=post.title sizes="(max-width: 768px) 100vw, 33vw" loading="lazy" %}` (REUSE 2-3 media_tags) — sa `{% if post.main_image %}` guard (main_image je nullable iz 5-1)
  - `alt` atribut = `post.title` (pun dijakritik — NIKAD prazan/šišan)
  - datum = `{{ post.published_at|date:"SHORT_DATE_FORMAT" }}` (**locale-aware — IMP-2/OQ-1 RESOLVED**): Django L10N respektuje aktivni locale (USE_L10N on) → sr `DD.MM.YYYY.`, hu `YYYY.MM.DD.`, en `MMM DD, YYYY` (project-context.md:364-366). NE hardcoded `d.m.Y.` (koji bi renderovao sr format za SVE lokale — pogrešno za hu/en). Dev-check: ako sr/hu locale-format fajl nema eksplicitan `SHORT_DATE_FORMAT`, Django pada na ugrađene locale formate; potvrdi da hu daje `YYYY.MM.DD.` (ili dodaj `formats.py`/`SHORT_DATE_FORMAT` override po locale-u ako se razlikuje od željenog)
  - `{{ post.title }}` (naslov) + `{{ post.perex }}` (perex/lead)
  - CTA dugme „SAZNAJ VIŠE" (epics.md:874 — pun dijakritik, `{% translate %}`)
  - cela kartica je klikabilna `<a href="{{ post.get_absolute_url }}">` → vodi na `/sr/blog/<slug>/` (epics.md:877) — `get_absolute_url` SAD razrešava (AC6/SM-D11)
- **And** `data-testid="blog-card-{{ post.slug }}"` (E2E selektor — mirror 2-8)

**AC5 — Filter po kategoriji (`?kategorija=<slug>` HTMX dropdown swap + OOB aria-live; epics.md:876; SM-D4/SM-D5)**

- **Given** AC1; više published objava u različitim Category; `categories_for_dropdown` u kontekstu
- **When** posetilac izabere kategoriju u dropdown-u (HTMX) ILI GET `/sr/blog/?kategorija=ratarstvo`
- **Then**:
  - queryset filtrira `Post.published.filter(category__slug=<slug>)` — SAMO objave te kategorije
  - dropdown ima „Sve kategorije" opciju (prazan slug → bez filtera) + sve `Category` opcije (`categories_for_dropdown = Category.objects.order_by("name")`)
  - **HTMX request** (`request.htmx==True`) → `get_template_names()` vraća `blog/partials/_post_results.html` (SAMO results grid, NE full page — mirror 2-9); `hx-target="#blog-results"`, `hx-swap="innerHTML"`, `hx-push-url="true"` (URL se ažurira `?kategorija=X`). **Tačno JEDAN `id="blog-results"` — UNUTAR `_post_results.html` partiala (mirror `_results_grid.html` `<div id="tractor-results">`), NIKAD u `blog_index.html` parentu (sprečava dupli-id HTMX/DOM bug).** Filter form i paginacijski linkovi oba koriste `hx-target="#blog-results"` + `hx-swap="innerHTML"` (konzistentno sa _results_grid.html); HTMX response (partial) nosi svoj `#blog-results` div čiji se `innerHTML` zamenjuje
  - **non-HTMX request** (direktan GET `/sr/blog/?kategorija=X`) → full page render sa pre-selektovanim dropdown-om (`active_filters.kategorija` → `selected`) — deep-link radi
  - **OOB aria-live announcement** guarded `{% if request.htmx %}`: `<div hx-swap-oob="innerHTML:#aria-live">` sa count („Pronađeno N objava") — mirror 2-8 SM-D23 (NIKAD plain-text u full-page render)
  - **invalid kategorija slug** (`?kategorija=nepostoji`) → 0 rezultata + empty state (NE 404); `active_filters.kategorija` normalizuje na „" za dropdown koherenciju (mirror 2-9 IMP-3)
  - `@method_decorator(vary_on_headers("HX-Request"))` na dispatch (cache poisoning defense — mirror 2-8 SM-D24/2-9 SM-D21)
- **And** `count` u kontekstu = `paginator.count` (broj filtriranih objava za announcement)

**AC6 — `apps/blog/urls.py` (`app_name="blog"` + `blog:index` + `blog:detail`) mount-ovan pod i18n_patterns; `get_absolute_url` razrešava (SM-D11)**

- **Given** 5-1 `Post.get_absolute_url()` → `reverse("blog:detail", kwargs={"slug": ...})` (raise NoReverseMatch dok URL ne postoji); `config/urls.py` `i18n_patterns`
- **When** kreiram `apps/blog/urls.py` + mount u `config/urls.py`
- **Then**:
  - `apps/blog/urls.py`: `app_name = "blog"`; `path("blog/", BlogIndexView.as_view(), name="index")`; `path("blog/<slug:slug>/", BlogPostDetailView.as_view(), name="detail")` (redosled: `blog/` PRE `blog/<slug>/`)
  - `config/urls.py`: `path("", include("apps.blog.urls"))` dodat u `i18n_patterns` blok (mirror :29-31 search/pages/forms)
  - `reverse("blog:index")` → `/sr/blog/`; `reverse("blog:detail", kwargs={"slug": "x"})` → `/sr/blog/x/` (locale prefiks kroz i18n_patterns)
  - **`Post.get_absolute_url()` SAD razrešava** na `/sr/blog/<slug>/` (više NE raise NoReverseMatch — SM-D11/SM-D12)
  - `BlogPostDetailView` (placeholder — SM-D11): `model=Post`, queryset `Post.published` (draft/future detail → 404), `template_name="blog/post_detail.html"`; render naslov+datum+telo (5-3 OBOGAĆUJE)
  - GET `/sr/blog/<slug-published-objave>/` → 200; GET `/sr/blog/<slug-draft-objave>/` → 404 (Post.published queryset)
- **And** **5-1 `test_get_absolute_url.py` AŽURIRAN RANO (Task 8.0; SM-D12)**: PRE `blog:detail` GREEN wiringa — (a) asertacija prelazi sa `pytest.raises(NoReverseMatch)` na razrešen `/sr/blog/<slug>/` put (pod `activate("sr")`), I (b) STALE docstring/komentar „5.3 ažurira ovaj test" → „5.2 ažurira ovaj test (SM-D12 — 5-2 registruje blog:detail)". 5-2 OWNS update (Gotcha BL2-3). Bez ranog update-a: `NoReverseMatch` asertacija pukne čim se registruje `blog:detail` → crveni CI.
- **And** `BlogPostDetailView` (placeholder) eksplicitno postavlja `context_object_name="post"` — tako da 5-3 template i ovaj template dele isto `{{ post }}` ime. **FORWARD-NOTE (5-3):** kad 5-3 doda render autora/tagova na detail, MORA proširiti detail `get_queryset()` sa `select_related("author")` / `prefetch_related("tags")` (5-2 placeholder treba SAMO `select_related("category")` za naslov/datum/telo) — sprečava 5-3 N+1.

**AC7 — Empty state DVE grane: filter-0 vs prazan-blog (epics.md:879; SM-D9; IMP-4/OQ-5 RESOLVED)**

- **Given** AC1; 0 published objava (prazan blog) ILI category filter daje 0 rezultata (objave postoje, samo ne u toj kategoriji); `active_filters.kategorija` u kontekstu
- **When** GET `/sr/blog/` (prazan blog) ILI `/sr/blog/?kategorija=prazna-kategorija`
- **Then** `_blog_empty_state.html` ima `{% if active_filters.kategorija %}` granu (IMP-4):
  - **filter-0 grana** (`active_filters.kategorija` truthy → objave postoje ali ne u toj kategoriji): poruka „Nema objava u ovoj kategoriji." (`{% translate %}`, pun dijakritik) + „prikaži sve" / clear-filter link → `{% url 'blog:index' %}` (bez `?kategorija` — resetuje filter)
  - **prazan-blog grana** (`active_filters.kategorija` prazan → blog stvarno prazan): naslov „Uskoro nove priče sa polja" (epics.md:879 — pun dijakritik) + CTA „POVRATAK NA POČETNU" → `{% url 'pages:home' %}` (vraća na home `/sr/`)
  - NEMA paginacije, NEMA praznog grid-a u obe grane; `posts` prazan → `{% if posts %}...{% else %}{% include "blog/partials/_blog_empty_state.html" %}{% endif %}` grana (mirror 2-8)
- **And** status 200 u obe grane (prazan blog/filter-0 NIJE greška); DRAFT-only blog (svi draft, bez filtera) → prazan-blog grana („Uskoro nove priče sa polja", jer `Post.published` prazan I `active_filters.kategorija` prazan)

**AC8 — Responsive 1col mobile / 2-3col desktop + i18n full diacritics (epics.md:878; SM-D8)**

- **Given** AC1; card grid render
- **When** strana se gleda na mobile (<768px) pa desktop (≥992px)
- **Then**:
  - grid je **1 kolona na mobile**, **2-3 kolone na desktop** (epics.md:878) — kroz CSS grid `repeat(auto-fit, minmax(...))` ili media query breakpoint sa `var(--token)` (NE magic px; mirror 2-8 grid)
  - SVI user-facing string-ovi kroz `{% translate %}`/`{% blocktranslate %}` sa PUNIM dijakritikama (naslov „Priče sa polja", „SAZNAJ VIŠE", „Sve kategorije", „Uskoro nove priče sa polja", „POVRATAK NA POČETNU", filter-0 „Nema objava u ovoj kategoriji."/„prikaži sve" (IMP-4), paginacija „Strana X od Y"/„Prethodna"/„Sledeća", aria announcement) — NIKAD hardcoded/šišana latinica (project-context.md:497-527)
  - slug u URL-u je ASCII (iz 5-1 slugify_ascii) — NIKAD Unicode
- **And** `.po` fajlovi sr/hu/en imaju nove string-ove (`just messages`); `loading="lazy"` na main_image (ispod fold-a; performance must-have)

## Tasks / Subtasks

> **Konvencija:** `[TEA-RED]` = Test Architect piše test PRE implementacije (mora FAIL). `[DEV-GREEN]` = Developer implementira da test prođe. **Dev NIKAD ne piše testove.** **NEMA migracije** (5-2 je views/templates/urls — konzumira 5-1 šemu). **NEMA `uv add`.**

- [x] **Task 1 — `apps/blog/urls.py` + `BlogPostDetailView` placeholder + config/urls.py mount (AC6) — KLJUČNA SEQUENCING (SM-D11)** `[DEV-GREEN]`
  - [x] 1.1 Kreiraj `apps/blog/views.py` sa MINIMALNOM `BlogPostDetailView(DetailView)`: `model=Post`, `get_queryset()` → `Post.published.select_related("category")`, `context_object_name="post"`, `template_name="blog/post_detail.html"`. (5-3 OBOGAĆUJE — slične objave/social/meta.)
  - [x] 1.2 Kreiraj `apps/blog/urls.py`: `app_name="blog"`; `path("blog/", views.BlogIndexView.as_view(), name="index")` (Task 2); `path("blog/<slug:slug>/", views.BlogPostDetailView.as_view(), name="detail")`. Redosled `blog/` PRE `blog/<slug>/`.
  - [x] 1.3 EDIT `config/urls.py`: dodaj `path("", include("apps.blog.urls"))` u `i18n_patterns` blok (posle forms include — mirror :29-31). `reverse("blog:index")`/`reverse("blog:detail", slug=...)` razrešavaju.
  - [x] 1.4 Kreiraj `templates/blog/post_detail.html` (placeholder): `{% extends "base.html" %}`; naslov + `{{ post.published_at|date:"SHORT_DATE_FORMAT" }}` (locale-aware — IMP-2) + `{{ post.body }}` (plain). NEMA slične-objave/social (5-3). `{% block title %}` = post.title.
  - [x] 1.5 `uv run python manage.py check` exit 0; `Post().get_absolute_url()` više NE raise-uje NoReverseMatch (razrešava `/sr/blog/<slug>/`).

- [x] **Task 2 — `BlogIndexView(ListView)` + queryset Post.published + N+1 (AC1/AC2)** `[DEV-GREEN]`
  - [x] 2.1 `BlogIndexView(ListView)` u `apps/blog/views.py`: `model=Post`, `context_object_name="posts"`, `paginate_by=10` (AC3), `@method_decorator(vary_on_headers("HX-Request"), name="dispatch")` (mirror 2-8).
  - [x] 2.2 `get_queryset()` → **`Post.published`** (NIKAD `Post.objects` — SM-D2) `.select_related("category")` (AC2 N+1). **NE dodavati `prefetch_related("tags")`** (kartica ne renderuje tagove — YAGNI; SM-D6/IMP-1). Default ordering iz `Meta.ordering` (najnovije prvo). Category filter (Task 4).
  - [x] 2.3 `get_template_names()` → `["blog/partials/_post_results.html"]` ako `request.htmx` else `["blog/blog_index.html"]` (mirror 2-8/2-9 SM-D3).

- [x] **Task 3 — Paginacija 10/strani + overflow safety (AC3)** `[DEV-GREEN]`
  - [x] 3.1 `paginate_by=10` (Task 2.1). `paginate_queryset()` override sa `Paginator.get_page()` (clamp overflow/invalid na poslednju/prvu stranu — NE 404; mirror 2-9 SM-D25).
  - [x] 3.2 `get_context_data` → `count = paginator.count` (za aria announcement); `page_obj`/`paginator`/`is_paginated` (ListView default).

- [x] **Task 4 — Category filter `?kategorija=<slug>` + active_filters + categories_for_dropdown (AC5)** `[DEV-GREEN]`
  - [x] 4.1 `get_queryset()`: `kategorija_slug = self.request.GET.get("kategorija","").strip()`; ako truthy → `.filter(category__slug=kategorija_slug)` (mirror 2-9).
  - [x] 4.2 `get_context_data`: `categories_for_dropdown = Category.objects.order_by("name")`; `active_filters = {"kategorija": self.request.GET.get("kategorija","")}`; **invalid-slug normalizacija** (mirror 2-9 IMP-3 — ako slug not in {c.slug} → reset na „" za dropdown koherenciju; queryset i dalje 0 → empty state).

- [x] **Task 5 — Templates: blog_index + _post_results + _post_card + _blog_filter + _blog_empty_state (AC1/AC4/AC5/AC7)** `[DEV-GREEN]`
  - [x] 5.1 `templates/blog/blog_index.html` (`{% extends "base.html" %}`; mirror tractor_listing.html): header (`<h1>` „Priče sa polja" + lead), `{% include "blog/partials/_blog_filter.html" %}`, results sekcija = SAMO `{% include "blog/partials/_post_results.html" %}` **BEZ wrapping `id` div-a**. **KRITIČNO (mirror _results_grid.html 1:1):** swap-target `id="blog-results"` živi UNUTAR `_post_results.html` (partial self-sadrži svoj id), a NE u `blog_index.html`. blog_index.html NE sme imati svoj `<div id="blog-results">` — inače DUPLI `id="blog-results"` (jedan u parentu, jedan u partialu) → suptilan HTMX/DOM bug. `{% block title %}`/`meta_description` statički (pun dijakritik).
  - [x] 5.2 `templates/blog/partials/_post_results.html` (HTMX swap target — mirror _results_grid.html EXACTLY): partial počinje svojim `<div id="blog-results" ...>` wrapper-om (1:1 kao `_results_grid.html` `<div id="tractor-results">` :3) koji obuhvata: `{% if posts %}` grid `{% for post in posts %}{% include "blog/partials/_post_card.html" %}{% endfor %}` + paginacija (`{% querystring page=... %}` + `hx-get`/`hx-target="#blog-results"`/`hx-swap="innerHTML"`/`hx-push-url="true"` na paginacijskim linkovima — mirror 2-8 :39-58) `{% else %}{% include "blog/partials/_blog_empty_state.html" %}` `{% endif %}`, pa `</div>` ZATVARA `#blog-results`. POSLE zatvaranja id div-a: guarded `{% if request.htmx %}` OOB aria-live count (mirror 2-8 SM-D23 :69-71 — `{% blocktranslate count %}`; OOB div je IZVAN `#blog-results` jer cilja `#aria-live` singleton). **Tačno JEDAN `id="blog-results"`, unutar partiala.** HTMX swap mode: `hx-target="#blog-results"` + `hx-swap="innerHTML"` (mirror _results_grid.html — swap-uje SADRŽAJ self-id'd div-a; filter i paginacija oba ciljaju `#blog-results` sa `innerHTML`).
  - [x] 5.3 `templates/blog/partials/_post_card.html`: `<a href="{{ post.get_absolute_url }}" data-testid="blog-card-{{ post.slug }}">`: `{% if post.main_image %}{% responsive_picture post.main_image alt=post.title sizes="(max-width: 768px) 100vw, 33vw" loading="lazy" %}{% endif %}`, `{{ post.published_at|date:"SHORT_DATE_FORMAT" }}` (locale-aware — IMP-2), `{{ post.title }}`, `{{ post.perex }}`, „SAZNAJ VIŠE" CTA. `{% load i18n media_tags %}` (`date:"SHORT_DATE_FORMAT"` je ugrađen `date` filter — NE treba `{% load l10n %}`).
  - [x] 5.4 `templates/blog/partials/_blog_filter.html` (**mirror 2-9 `_used_filter_form.html` dropdown** — NE 2-8 tractor slider; blog filter je SAMO category `<select>`, bez range slider-a): `<form method="get" action="{% url 'blog:index' %}" hx-get="{% url 'blog:index' %}" hx-trigger="change delay:300ms" hx-target="#blog-results" hx-swap="innerHTML" hx-push-url="true" hx-indicator="#blog-filter-loading">` + `<select name="kategorija">` „Sve kategorije" + `{% for c in categories_for_dropdown %}<option value="{{ c.slug }}"{% if active_filters.kategorija == c.slug %} selected{% endif %}>{{ c.name }}</option>{% endfor %}` + htmx-indicator spinner. **STYLE:** `hx-trigger="change delay:300ms"` SAMO (NE `"input changed delay:300ms, change delay:300ms"` — to je 2-9 varijanta za text/range input-e; blog ima samo `<select>` → reaguje na `change`).
  - [x] 5.5 `templates/blog/partials/_blog_empty_state.html` (DVE grane — IMP-4): `{% if active_filters.kategorija %}` → „Nema objava u ovoj kategoriji." + „prikaži sve" link `{% url 'blog:index' %}` (clear-filter); `{% else %}` → „Uskoro nove priče sa polja" naslov + „POVRATAK NA POČETNU" CTA `{% url 'pages:home' %}` (mirror _empty_state.html). Sve `{% translate %}` pun dijakritik.

- [x] **Task 6 — CSS responsive grid 1col/2-3col (AC8; SM-D8)** `[DEV-GREEN]`
  - [x] 6.1 REUSE `coric-product-card` ILI novi `coric-blog-card` BEM (Dev/UX odluka — SM-D8); grid `repeat(auto-fit, minmax(...))` ili media query (1col mobile / 2-3col desktop — epics.md:878); `var(--token)` (NE magic px). main.css `@import` ako novi CSS fajl.
  - [x] 6.2 `loading="lazy"` na main_image (Task 5.3 — performance); aria/alt pun dijakritik.

- [x] **Task 7 — i18n string-ovi + .po (AC8)** `[DEV-GREEN]`
  - [x] 7.1 Svi user-facing string-ovi kroz `{% translate %}`/`{% blocktranslate %}` (pun dijakritik). `just messages` regeneriše sr/hu/en .po; popuni hu/en prevode (ili sr fallback).

- [ ] **Task 8 — RED-phase testovi (AC1-AC8)** `[TEA-RED]`
  - [ ] **8.0 — AŽURIRAJ 5-1 `test_get_absolute_url.py` PRVO (PRE blog:detail GREEN wiring; SM-D12/Gotcha BL2-3 — AC6).** Ovo je INHERITED-test update i MORA se uraditi RANO (uparено sa Task 1, PRE nego što `blog:detail` postane razrešiv u GREEN) — inače `pytest.raises(NoReverseMatch)` asertacija PUKNE čim Task 1.3 registruje `blog:detail` → crveni CI usred implementacije. Dev/TEA koji čita SAMO test fajl (NE ovu story) bi odložio update → break. Zato je spelovano kao zaseban prvi korak. DVE izmene u `apps/blog/tests/test_get_absolute_url.py`:
    - **(a) Prepiši asertaciju:** `test_get_absolute_url_raises_no_reverse_match()` (ime + telo) → asertuj RAZREŠEN put umesto `pytest.raises(NoReverseMatch)`. Tj. pod `translation.activate("sr")` (ili `with override("sr")`), `post.get_absolute_url() == f"/sr/blog/{post.slug}/"` (i `reverse("blog:detail", kwargs={"slug": post.slug}) == f"/sr/blog/{post.slug}/"`). Ukloni `from django.urls import NoReverseMatch` import ako više nije korišćen. Preimenuj test u npr. `test_get_absolute_url_resolves_blog_detail()`.
    - **(b) Ažuriraj STALE docstring/komentar:** u istom fajlu (~linija 6) tekst „5.3 ažurira ovaj test da asertuje stvarni /sr/blog/<slug>/." → „5.2 ažurira ovaj test (SM-D12 — 5-2 registruje blog:detail) i asertuje razrešen /sr/blog/<slug>/." (5-2 OWNS update, NE 5-3 — jer je 5-2 prvi registrator `blog:detail`). Takođe ažuriraj inline komentar u telu testa (`reverse("blog:detail", ...) — URL pattern dolazi u 5.2/5.3` → „...registrovan u 5.2") da nema rezidualne „5.3" reference.
    - **NE preskočiti nijednu od (a)/(b)** — i asertacija i docstring/komentar moraju biti ažurirani u istom commit-u kao Task 1 (atomic — Task 9.3).
  - [ ] 8.1 `apps/blog/tests/test_views.py` (NOVO) + reuse `conftest.py` (5-1 — `make_post`/`make_category` factory helpers; `@pytest.mark.django_db`).
  - [ ] 8.2 **AC1 (Post.published, draft-not-leaked):** GET `/sr/blog/` (`reverse("blog:index")`) → 200, template `blog/blog_index.html`, `context["posts"]`. Kreiraj DRAFT + PUBLISHED-past + PUBLISHED-future + PUBLISHED-None → SAMO PUBLISHED-past u `posts` (DRAFT/future/None NEVIDLJIVI). Naslov „Priče sa polja" u HTML. **Test asertuje view koristi `Post.published` NE `Post.objects`** (kroz behavior — draft excluded).
  - [ ] 8.3 **AC2 (N+1 lock):** `assertNumQueries(N)` sa 3 published objave (svaki sa category) == isti N sa 10 objava (fiksni budžet; dodavanje objava NE povećava query broj — `select_related("category")` drži category JOIN konstantnim). NE testira tags prefetch (kartica ne renderuje tagove — IMP-1). Lock N empirijski (Dev GREEN fix iter).
  - [ ] 8.4 **AC3 (paginacija):** 25 published → strana 1 = 10 objava, `is_paginated=True`; `?page=3` = 5; `?page=999` → clamp poslednja (NE 404); `?page=abc` → strana 1. `{% querystring %}` čuva `?kategorija`.
  - [ ] 8.5 **AC4 (kartica):** kartica ima main_image responsive (ako postoji) + `published_at` datum (d.m.Y.) + title + perex + „SAZNAJ VIŠE" + `<a href>` = `post.get_absolute_url` (`/sr/blog/<slug>/`); `data-testid="blog-card-<slug>"`; main_image `{% if %}` guard (nullable).
  - [ ] 8.6 **AC5 (filter HTMX):** GET `/sr/blog/?kategorija=<slug>` → SAMO te kategorije; „Sve kategorije" (prazan) → sve; HTMX request (`HTTP_HX_REQUEST=true` ili client.get header) → template `_post_results.html` (NE full page) + OOB aria-live u response; non-HTMX → full page + `selected` dropdown; invalid slug → 0 + empty + active_filters normalizovan; `vary_on_headers("HX-Request")` (Vary header u response).
  - [ ] 8.6b **AC3+AC5 (kombinovani filter+paginacija deep-link — IMP-3):** non-HTMX GET `/sr/blog/?kategorija=<slug>&page=2` (kategorija sa 11+ objava) → full page render (200, `blog/blog_index.html`); dropdown PRE-SELEKTOVAN na `<slug>` (`active_filters.kategorija == slug` → `selected`); prikazane su SAMO objave TE kategorije sa STRANE 2 (NE druge kategorije, NE strana 1); filter `?kategorija` SAČUVAN kroz paginaciju (`{% querystring %}` tag drži `kategorija` na prev/next linkovima — proveri da paginacijski href/hx-get sadrži i `kategorija` i `page`). Ovo je najverovatnija regresiona tačka (kombinovani-param progressive-enhancement put) — zaključaj.
  - [ ] 8.7 **AC6 (URL wiring + get_absolute_url + placeholder detail):** `reverse("blog:index")=="/sr/blog/"`; `reverse("blog:detail", slug="x")=="/sr/blog/x/"`; `Post(slug="x").get_absolute_url()=="/sr/blog/x/"` (više NE NoReverseMatch); GET `/sr/blog/<published-slug>/` → 200 (placeholder detail, naslov+telo); GET `/sr/blog/<draft-slug>/` → 404 (Post.published); placeholder detail koristi `context_object_name="post"` (5-3 ugovor). **Inherited-test update `test_get_absolute_url.py` (5-1) je već uradjen u Task 8.0** (PRE GREEN wiring — asertacija + stale docstring/komentar; SM-D12/Gotcha BL2-3). NE dupliraj ovde.
  - [ ] 8.8 **AC7 (empty state DVE grane — IMP-4):** 0 published (bez filtera) → prazan-blog grana „Uskoro nove priče sa polja" + „POVRATAK NA POČETNU" link (`pages:home`); DRAFT-only (bez filtera) → prazan-blog grana (Post.published prazan, `active_filters.kategorija` prazan); VALIDNA kategorija sa 0 objava (`?kategorija=<valid-slug>` ali 0 published u njoj) → filter-0 grana „Nema objava u ovoj kategoriji." + „prikaži sve" link (`blog:index`); invalid slug → normalizovan na „" → prazan-blog grana; NEMA paginacije u obe grane.
  - [ ] 8.9 **AC8 (i18n):** ključni string-ovi prisutni pun-dijakritik (NE šišana); render za sr (+ smoke hu/en kroz `translation.activate` ili `LANGUAGE_CODE`); slug ASCII u href.

- [ ] **Task 9 — Dev manual gate (NE pytest) (AC6/regression)** `[DEV-GREEN]`
  - [ ] 9.1 `uv run python manage.py check` exit 0; **`makemigrations --check --dry-run` → „No changes detected"** (5-2 je views/templates/urls — NEMA model promene/migracije; regression guard).
  - [ ] 9.2 Dev shell smoke: kreiraj 1 PUBLISHED + 1 DRAFT Post; GET `/sr/blog/` → samo PUBLISHED; klik kartice → `/sr/blog/<slug>/` (placeholder detail 200); DRAFT detail → 404.
  - [ ] 9.3 `just lint` clean (ruff apps/blog/ + djade templates/blog/); commit views+urls+templates+config+css+po+5-1-test-update ZAJEDNO (atomic).

## Dev Notes

### SM Decisions (SM-D log)

**SM-D1 — PLACEMENT: 5-2 dodaje `apps/blog/views.py` + `urls.py` + `templates/blog/` u POSTOJEĆI (5-1) `apps/blog/` app.** 5-1 je kreirao `apps/blog/` kao models-only (models/managers/translation/admin/migrations/tests; NEMA views/urls/templates — 5-1 OUT OF SCOPE eksplicitno). 5-2 popunjava view/URL/template sloj. blog dep boundary OSTAJE (importuje SAMO `apps.core` + Django + `settings.AUTH_USER_MODEL`; 5-2 dodaje import `pages:home` reverse u template SAMO — NE Python cross-app import). View importuje SAMO `apps.blog.models` (Post/Category) — NE products/brands/forms.

**SM-D2 — `Post.published` (NIKAD `Post.objects`) — draft-not-leaked granica (KRITIČNO).** 5-1 SM-D5/AC3: `Post.published` = `status="published"` AND `published_at__lte=now`; `Post.objects` = sav content (uključujući DRAFT + future). **Javna index strana MORA koristiti `Post.published`** — DRAFT objava ili PUBLISHED-sa-budućim-published_at NE SME procuriti javno. Ovo je SECURITY/correctness granica (autor sprema draft → ne sme biti javno vidljiv pre objave). `BlogIndexView.get_queryset()` bazira na `Post.published.select_related(...)`. `BlogPostDetailView` ISTO `Post.published` (draft detail → 404). Test (8.2/8.7) asertuje DRAFT/future/None NEVIDLJIVI. Kontrast: products koriste `.filter(is_published=True)` inline (nemaju manager — 5-1 SM-D2/D5); blog ima dedikovan `Post.published` manager → koristi ga.

**SM-D3 — `paginate_by=10` (epics.md:875 EKSPLICITNO „10 objava/strani").** ListView `paginate_by=10`. (Kontrast: traktori 2-8 = 24/strani, polovna 2-9 = 12/strani; blog je 10 per epics.) `is_paginated`/`page_obj`/`paginator` ListView default. Overflow safety kroz `Paginator.get_page()` override (mirror 2-9 SM-D25 — `?page=999` clamp NE 404).

**SM-D4 — Category filter = querystring `?kategorija=<slug>` (NE dedikovana arhiva URL).** epics.md:876 „Filter po kategoriji (dropdown ili tabovi)". 5-2 implementira kao querystring filter na INDEX strani (`/sr/blog/?kategorija=ratarstvo`) — NE kao posebnu `/sr/blog/kategorija/<slug>/` arhivu (to je 5-3 epics.md:891). `get_queryset` filtrira `category__slug=<slug>`; `categories_for_dropdown` u kontekstu; invalid-slug normalizacija (mirror 2-9 IMP-3). Mirror 2-9 `?kategorija` filter 1:1 (polovna mehanizacija ima identičan category-slug querystring filter).

**SM-D5 — HTMX category filter (NE plain GET) — mirror 2-8/2-9 request.htmx branching.** **ODLUKA: HTMX swap** (NE plain page reload). Opravdanje: (a) projekt-konvencija — SVE listing+filter strane (2-8 traktori, 2-9 polovna, 2-13 search) koriste HTMX request.htmx branching + OOB aria-live; konzistentnost; (b) epics.md:876 traži filter — HTMX swap daje glatkiji UX (bez full-page reload) + push-url za deep-linkable filter; (c) infrastruktura već postoji (django-htmx middleware, `aria_live` singleton base.html, `{% querystring %}`, `vary_on_headers` pattern) — REUSE bez novog koda. `get_template_names()` vraća `_post_results.html` za HTMX, `blog_index.html` za non-HTMX. **non-HTMX deep-link MORA raditi** (direktan GET `/sr/blog/?kategorija=X` → full page sa selektovanim dropdown-om) — progressive enhancement (form `method="get"` radi bez JS). OOB aria-live guarded `{% if request.htmx %}` (mirror 2-8 SM-D23 — sprečava plain-text u full-page render). `@vary_on_headers("HX-Request")` cache-poisoning defense (mirror 2-8 SM-D24).

**SM-D6 — N+1 lock: `select_related("category")` + assertNumQueries (MANDATORY — project-context.md:743). `prefetch_related("tags")` NE u 5-2 (IMP-1 — YAGNI konzistentnost).** Listing view sa per-post `category` FK lookup = klasičan N+1 (svaka kartica čita category → +1 query/post). `.select_related("category")` JOIN-uje u jedan upit — JESTE load-bearing (kartica/filter ga koriste) i count-variation `assertNumQueries` ga hvata. **`prefetch_related("tags")` se NAMERNO IZOSTAVLJA u 5-2:** index kartica renderuje SAMO `main_image`/datum/`title`/`perex`/CTA (epics.md:874 — NEMA tagova na kartici). Bez konzumenta tagova, `prefetch_related("tags")` je no-op čiji assertNumQueries lock ništa ne štiti (ništa ne iterira `post.tags`), I protivreči istom YAGNI rationale-u kojim ova ista odluka izostavlja `select_related("author")` („ne select_related/prefetch polja koja se ne renderuju"). Konzistentnost: index queryset = `Post.published.select_related("category")` SAMO. **5-3 detail dodaje `prefetch_related("tags")` + `select_related("author")` kad ih renderuje** (autor meta + tag linkovi). Test (8.3) zaključava budžet `assertNumQueries(N)` — 3 objave == 10 objava (konstanta) na `select_related("category")`. Mirror 2-8 query budget lock.

**SM-D7 — Kartica sadržaj: main_image + datum + title + perex + „SAZNAJ VIŠE" (epics.md:874). Datum = `|date:"SHORT_DATE_FORMAT"` (locale-aware — IMP-2/OQ-1 RESOLVED).** epics.md:874 „kartice (naslovna slika, datum, naslov, perex, CTA „SAZNAJ VIŠE")". main_image kroz `responsive_picture` (REUSE 2-3 sorl-thumbnail srcset + loading=lazy) sa `{% if post.main_image %}` guard (nullable iz 5-1). **Datum = `published_at|date:"SHORT_DATE_FORMAT"` (NE hardcoded `d.m.Y.`):** Django L10N (USE_L10N on) respektuje aktivni locale → sr `DD.MM.YYYY.`, hu `YYYY.MM.DD.`, en `MMM DD, YYYY` (project-context.md:364-366). Hardcoded `d.m.Y.` bi renderovao sr format za SVE lokale (pogrešno za hu/en koji imaju različit raspored — to je bila greška u OQ-1). `SHORT_DATE_FORMAT` je standardni Django L10N pristup (ugrađen `date` filter; NE treba custom tag). **Dev-check:** ako hu/sr locale-format ne daje željeni izlaz iz Django ugrađenih formata, dodaj `SHORT_DATE_FORMAT` u project locale `formats.py` override — ali default ugrađeni Django formati su obično ispravni. **NAPOMENA — `locale_date` tag NE postoji:** project-context.md:140 referencira `{% locale_date %}` custom tag (`apps/core/templatetags/coric_format.py`), ALI fajl/tag NE postoji (verifikovano live — `apps/core/templatetags/` ima SAMO `htmx_aria.py`; isti stale-doc kao 5-1 OQ-6 PublishableModel). 5-2 koristi ugrađeni `|date:"SHORT_DATE_FORMAT"` (NE izmišlja `locale_date`). (Ako se ikad uvede `coric_format.locale_date`, zaseban refaktor.) CTA „SAZNAJ VIŠE" → `post.get_absolute_url` (epics.md:877 link na `/sr/blog/<slug>/`).

**SM-D8 — Filter UI = dropdown (NE tabovi); card grid REUSE `coric-product-card` ili novi `coric-blog-card` (Dev/UX).** epics.md:876 „dropdown ili tabovi" — **dropdown izabran**: mirror 2-9 `_used_filter_form.html` `<select name="kategorija">` (dokazan pattern, REUSE, manje koda nego tabovi; tabovi bi zahtevali novi CSS+a11y rad). Card grid: Dev/UX bira REUSE `coric-product-card` BEM (2-8 — ako blog kartica strukturno pasuje: slika+title+meta+CTA) ILI novi `coric-blog-card` (ako blog kartica treba perex/datum layout drugačiji). Preferiraj REUSE ako pasuje (YAGNI). Responsive 1col/2-3col (epics.md:878) kroz grid `auto-fit minmax` ili media query (`var(--token)`).

**SM-D9 — Empty state DVE grane: filter-0 vs prazan-blog (IMP-4/OQ-5 RESOLVED).** Mirror 2-8 `_empty_state.html` strukturu, ali blog copy + DVE grane kroz `{% if active_filters.kategorija %}` (kontekst već nosi `active_filters` — Task 4.2): **(1) prazan-blog grana** (`active_filters.kategorija` prazan): naslov „Uskoro nove priče sa polja" (epics.md:879 doslovno) + CTA „POVRATAK NA POČETNU" → `{% url 'pages:home' %}` (home `/sr/`; pages:home iz 3-1). **(2) filter-0 grana** (`active_filters.kategorija` truthy): poruka „Nema objava u ovoj kategoriji." + „prikaži sve" / clear-filter link → `{% url 'blog:index' %}` (resetuje na sve). **OBRAZLOŽENJE (IMP-4):** „Uskoro nove priče sa polja" je ZAVARAVAJUĆE kad CATEGORY FILTER vrati 0 (priče POSTOJE, samo ne u toj kategoriji) — drugačija semantika traži drugačiju poruku. **NUANSA (invalid slug):** AC5/Task 4.2 normalizuje INVALID slug → `active_filters.kategorija=""` (dropdown koherencija) → invalid-slug filter pokazuje prazan-blog granu (ne filter-0) — prihvatljivo jer invalid slug nije realan korisnički izbor (dropdown nudi samo validne); VALIDNA kategorija-sa-0-objava zadržava svoj slug → filter-0 grana. (epics.md:879 daje samo prazan-blog copy; filter-0 copy je IMP-4 dopuna — UX-ispravnije od jednog teksta za oba.)

**SM-D10 — NEMA model promene / NEMA migracije.** 5-2 je čist view/template/URL sloj nad 5-1 šemom. `Post`/`Category`/`Tag`/`PublishedManager`/`translation.py` NETAKNUTI. `makemigrations --check --dry-run` MORA „No changes detected" (Task 9.1 regression guard) — ako bilo šta generiše migraciju → STOP (5-2 NE sme dirati šemu). Kontrast 5-1 (CreateModel ×3 migracija); 5-2 = 0 migracija.

**SM-D11 — KLJUČNA SEQUENCING: 5-2 registruje `blog:detail` sa MINIMALNOM placeholder `BlogPostDetailView` koju 5-3 OBOGAĆUJE (lowest-risk).** PROBLEM: 5-1 `Post.get_absolute_url()` = `reverse("blog:detail", kwargs={"slug": ...})` raise-uje `NoReverseMatch` (blog URL-ovi ne postoje). epics.md:877 traži da kartice na index strani linkuju na `/sr/blog/<slug>/`. ALI detail strana je 5-3 scope. **RAZMOTRENE OPCIJE:**
- (a) **5-2 registruje `blog:detail` URL → MINIMALAN placeholder `BlogPostDetailView`** (render naslov+datum+telo iz `Post.published`), koji **5-3 OBOGAĆUJE** (slične objave, social share, kategorija/tag linkovi, meta). ✅ IZABRANO.
- (b) Samo URL pattern → bare placeholder FBV koji vraća HttpResponse („uskoro"). ❌ ODBAČENO — mrtav kod, loš UX ako neko klikne karticu pre 5-3, i 5-3 bi morao zameniti ceo view (više rada).
- (c) 5-2 NE registruje `blog:detail`, kartice koriste manuelni `{% url %}` placeholder ili `#`. ❌ ODBAČENO — `get_absolute_url` (5-1 ugovor) i dalje raise NoReverseMatch (admin, sitemap, share linkovi i dalje slomljeni); kartice bi imale dead `#` link.
**ZAŠTO (a) je lowest-risk:** (1) `get_absolute_url` razrešava → kartice linkuju ISPRAVNO na pravi `/sr/blog/<slug>/` (NE dead link); (2) placeholder detail je FUNKCIONALAN (render published objave) — klik kartice daje smislenu stranu, NE 404/„uskoro"; (3) **5-3 OBOGAĆUJE istu `BlogPostDetailView` klasu** (dodaje get_context_data slične-objave + template social-share + kategorija/tag linkove + meta) — NE zamenjuje je; placeholder kontrakt koji 5-3 nasleđuje: `model=Post`, `get_queryset()=Post.published.select_related("category")`, `context_object_name="post"`, `template_name="blog/post_detail.html"`, draft→404. **5-3 INHERITS:** radni `blog:detail` URL (+ dodaje `blog:category`/`blog:tag` arhive epics.md:891-892), placeholder DetailView klasu (proširuje get_context_data + template), placeholder template (obogaćuje sa slične-objave/social/meta). **5-3 NE mora menjati URL signature** (`blog:detail` + slug kwarg je stabilan — mirror products:detail). `BlogIndexView` (`blog:index`) je takođe 5-2 (ne placeholder — pun index). **EKSPLICITNO (IMP-5):** placeholder `BlogPostDetailView` MORA postaviti `context_object_name="post"` (tako da 5-3 template + 5-2 placeholder template dele isto `{{ post }}` ime — bez ovoga 5-3 bi koristio default `object`/`post` koji možda ne pasuje). **FORWARD-NOTE 5-3 N+1:** 5-2 placeholder `get_queryset()=Post.published.select_related("category")` (treba SAMO category za naslov/datum/telo). Kad 5-3 doda render AUTORA (meta) i TAGOVA (tag linkovi) na detail, **MORA proširiti `get_queryset()` sa `select_related("author")` + `prefetch_related("tags")`** — inače 5-3 uvodi N+1 na detail strani (per-render author FK + tags M2M lookup). 5-2 ih NE dodaje (placeholder ih ne renderuje — YAGNI, mirror IMP-1 index odluke).

**SM-D12 — 5-1 `test_get_absolute_url.py` MORA se ažurirati (5-2 OWNS).** 5-1 `test_get_absolute_url.py` (Task 8.3) asertuje `Post.get_absolute_url()` → `NoReverseMatch` (jer URL nije registrovan u 5-1). 5-2 registruje `blog:detail` → taj test bi sad FAIL-ovao (više NE raise NoReverseMatch). **5-2 OWNS taj update** (TEA u RED fazi prepiše asertaciju: `assert post.get_absolute_url() == f"/sr/blog/{post.slug}/"` umesto `pytest.raises(NoReverseMatch)`). 5-1 sam je flag-ovao ovo (5-1 Task 8.3: „Kad 5.3 doda URL, ovaj test se ažurira" — ALI URL dolazi u 5-2, NE 5-3, jer 5-2 je prvi konzument kartica → 5-2 ažurira). Gotcha BL2-3. (Drugi 5-1 testovi NETAKNUTI — samo get_absolute_url asertacija.)

### Gotchas (blog-index-specific traps)

**Gotcha BL2-1 — `Post.published` NE `Post.objects` (draft procurivanje).** Najlakša greška: `BlogIndexView` napiše `queryset = Post.objects.all()` (default manager) → DRAFT i future objave PROCURE javno. **MORA `Post.published`** (SM-D2). Manager je opt-in (5-1 BL-3 — `objects` je default_manager, `published` je eksplicitan). Test (8.2) asertuje DRAFT/future NEVIDLJIVI — ako test prođe sa `Post.objects`, test je preslab (DRAFT bi se pojavio). Isto za `BlogPostDetailView` (draft detail → 404 kroz `Post.published` queryset).

**Gotcha BL2-2 — OOB aria-live SAMO za HTMX (`{% if request.htmx %}` guard).** `_post_results.html` se render-uje I za inicijalni full-page GET (kroz `{% include %}` u `blog_index.html`) I za HTMX swap. OOB `<div hx-swap-oob>` element u full-page render-u bi se prikazao kao plain tekst (broken). **MORA `{% if request.htmx %}` guard** oko OOB div-a (mirror 2-8 SM-D23). Aria-live target je `#aria-live` singleton iz base.html (`{% aria_live %}` tag).

**Gotcha BL2-3 — 5-1 test_get_absolute_url AŽURIRANJE (NE preskočiti).** 5-2 registruje `blog:detail` → 5-1 `test_get_absolute_url.py` `NoReverseMatch` asertacija PUKNE. **MORA se prepisati** (SM-D12). Ako se zaboravi → 5-1 test fails u 5-2 suite (crveni CI). TEA u RED fazi ažurira (Task 8.7). (Ovo je „inherited test" — 5-2 menja ponašanje koje 5-1 test verifikuje, pa 5-2 vlasnik update-a.)

**Gotcha BL2-4 — URL redosled `blog/` PRE `blog/<slug>/` (NE shadow).** `apps/blog/urls.py`: `path("blog/", ...)` (index) MORA biti PRE `path("blog/<slug:slug>/", ...)` (detail) — Django resolver iterira u redu; `blog/` (tačan, bez segmenta) match-uje `/blog/` pre nego slug pattern (koji zahteva segment). Obrnut redosled bi `blog/<slug>/` i dalje ne match-ovao prazan `/blog/` (slug zahteva content) — ali kanonski redosled je statički-pre-slug (mirror products urls.py SM-D1 `traktori/` pre `traktori/<slug>/`). Mount `path("", include("apps.blog.urls"))` POSLE postojećih include-ova (NE shadow products/brands/search/pages — blog/ je nov prefiks, nema kolizije).

**Gotcha BL2-5 — `categories_for_dropdown` query u N+1 budžetu.** `get_context_data` dodaje `Category.objects.order_by("name")` (dropdown) — to je +1 query (lista kategorija). MORA biti u assertNumQueries budžetu (AC2), ali je KONSTANTA (1 query bez obzira na broj kategorija — NE per-post). Ne meša se sa per-post N+1 (category FK na Post je `select_related`, dropdown lista je zaseban 1 query). Test broji ukupan fiksan budžet.

### Project Structure Notes

- `apps/blog/` POSTOJI iz 5-1 (models-only). 5-2 dodaje `views.py` + `urls.py` (NOVO) + `templates/blog/` (NOVO direktorijum). NEMA `forms.py`/`context_processors.py` u 5-2 (context_processor = 5-4).
- View pattern REUSE: `BlogIndexView` mirror `apps/products/views.py:TractorListView` (2-8) + `UsedMachineryListView` (2-9) — ListView + paginate_by + get_template_names() request.htmx branching + get_queryset filter + get_context_data + @vary_on_headers + Paginator.get_page() override. `BlogPostDetailView` mirror `ProductDetailView` (2-7) DetailView strukturu (minimalan u 5-2; 5-3 obogaćuje).
- Template pattern REUSE: `blog_index.html` mirror `tractor_listing.html`; `_post_results.html` mirror `_results_grid.html` (grid + querystring paginacija + guarded OOB aria-live + empty include); `_blog_filter.html` mirror `_used_filter_form.html` (category dropdown); `_blog_empty_state.html` mirror `_empty_state.html`; `_post_card.html` mirror `coric-product-card` u `_results_grid.html`.
- Media REUSE: `{% responsive_picture %}` (apps/media_pipeline/templatetags/media_tags.py — 2-3) za main_image srcset+lazy.
- i18n: `path("", include("apps.blog.urls"))` u `i18n_patterns` (config/urls.py — mirror :29-31). `/sr/blog/` + `/sr/blog/<slug>/`. `reverse("blog:index")`/`reverse("blog:detail")` daju locale prefiks.
- **FORWARD-DEP konzumenti (5-2 obezbeđuje):** 5-3 (OBOGAĆUJE `BlogPostDetailView` + `blog:detail` URL — slične objave/social/meta/kategorija-tag-arhive; nasleđuje placeholder kontrakt SM-D11), 5-4 (footer context_processor — nezavisan od 5-2 view-a; čita `Post.published`).
- **INHERITED-DEP (5-2 menja):** 5-1 `test_get_absolute_url.py` (SM-D12 — 5-2 prepisuje `NoReverseMatch` → razrešen put).

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-5.2] (`:866-879`) — `/sr/blog/` index; kartice (naslovna slika/datum/naslov/perex/„SAZNAJ VIŠE"); paginacija 10/strani; filter po kategoriji (dropdown ili tabovi); klik kartice → `/sr/blog/<slug>/`; mobile 1col/desktop 2-3col; empty state „Uskoro nove priče sa polja" + „POVRATAK NA POČETNU"
- [Source: _bmad-output/planning-artifacts/epics.md#Story-5.3] (`:881-893`) — detail strana koju kartice linkuju (5-2 placeholder, 5-3 obogaćuje); `/sr/blog/kategorija/<slug>/` + `/sr/blog/tag/<slug>/` arhive (5-3 dodaje); meta iz title+perex
- [Source: _bmad-output/planning-artifacts/epics.md#Story-5.4] (`:895-906`) — footer `latest_blog_posts` (nezavisno od 5-2)
- [Source: apps/blog/models.py] — `Post` (title/perex/body/main_image/category FK/tags M2M/author FK/status/published_at; `get_absolute_url`=reverse("blog:detail") :207-209; Meta.ordering=["-published_at","-created_at"] :182); `Category` (name/slug/description); `Post.objects` (default) + `Post.published` (PublishedManager) :178-179
- [Source: apps/blog/managers.py] — `PublishedManager.get_queryset()` → `.filter(status="published", published_at__lte=timezone.now())` (draft-not-leaked granica; SM-D2)
- [Source: apps/products/views.py:182-394] — `TractorListView` (2-8) + `UsedMachineryListView` (2-9): ListView + paginate_by + get_template_names() request.htmx branching :203-206/:273-276; get_queryset filter :208-233/:278-326; `?kategorija` category-slug filter :288-293; Paginator.get_page() overflow :328-340; categories_for_dropdown :345-347; active_filters + invalid-slug normalizacija :353-373; @vary_on_headers("HX-Request") :182/:254; count=paginator.count
- [Source: templates/products/tractor_listing.html] — full-page listing mirror (extends base.html; header; filter include; results include; block title/meta_description/scripts)
- [Source: templates/products/partials/_results_grid.html] — HTMX swap target mirror (grid + querystring paginacija hx-get/hx-target/hx-push-url :39-58; guarded `{% if request.htmx %}` OOB aria-live :69-71; empty include :62)
- [Source: templates/products/partials/_used_filter_form.html] — category dropdown mirror (`<select name="kategorija">` „Sve kategorije" + options + selected :19-29; form method=get + hx-get/hx-target/hx-push-url :6-16)
- [Source: templates/products/partials/_empty_state.html] — empty state mirror (naslov + lead + CTA button)
- [Source: apps/media_pipeline/templatetags/media_tags.py:31-32] — `{% responsive_picture %}` inclusion tag (main_image srcset + loading=lazy — REUSE 2-3)
- [Source: templates/emails/lead_received.html:44] — `{{ ...|date:"d.m.Y. H:i" }}` real `date` filter precedent (potvrđuje ugrađeni `date` filter; SM-D7 — `locale_date` tag NE postoji; 5-2 ipak koristi locale-aware `SHORT_DATE_FORMAT` za karticu — IMP-2/OQ-1, jer kartica mora biti ispravna na hu/en, a email je sr-only)
- [Source: config/urls.py:25-33] — `i18n_patterns` (mount `apps.blog.urls` mirror search/pages/forms include :29-31)
- [Source: apps/products/urls.py] — `app_name` + statički-pre-slug redosled (SM-D1 — mirror za blog `blog/` pre `blog/<slug>/`)
- [Source: apps/pages/urls.py:16] — `pages:home` (empty state „POVRATAK NA POČETNU" CTA target)
- [Source: _bmad-output/implementation-artifacts/5-1-blogpost-category-tag-modeli-admin-stub.md] — 5-1 model temelj: SM-D5 PublishedManager, SM-D6 get_absolute_url=reverse raise NoReverseMatch, BL-3 manager redosled, OQ-1 blog:detail signature, OQ-6 stale-doc precedent (locale_date paralela)
- [Source: _bmad-output/project-context.md] — :168-194 CBV preferred + HTMX request.htmx branching + OOB aria-live two-region + min loading 200ms; :173/:743 select_related+prefetch_related N+1 MANDATORY; :161-166 URL kebab-case + ASCII slug + reverse; :341-347 templates kebab-case + partials lokacija; :365 datum sr DD.MM.YYYY.; :497-527 pune dijakritike; :742-748 performance (srcset/lazy)

### Open Questions (OQ)

- **OQ-1 (datum format — `|date:"SHORT_DATE_FORMAT"`) — RESOLVED (IMP-2):** **ODLUKA: `{{ post.published_at|date:"SHORT_DATE_FORMAT" }}` (locale-aware, Django L10N — USE_L10N on).** Hardcoded `|date:"d.m.Y."` bi renderovao sr format za SVE lokale (pogrešno za hu `YYYY.MM.DD.` / en `MMM DD, YYYY` — project-context.md:364-366). `SHORT_DATE_FORMAT` respektuje aktivni LANGUAGE_CODE → ispravan datum po locale-u. Primenjeno na kartici (`_post_card.html`) I placeholder detail (`post_detail.html`). Dev-check: ako Django ugrađeni `SHORT_DATE_FORMAT` po locale-u ne daje željeni izlaz (npr. hu), dodaj override u project `formats.py` per-locale — ali ugrađeni formati su obično ispravni; ne blokira. (`locale_date` custom tag NE postoji — project-context.md:140 je stale-doc; 5-2 koristi ugrađeni `date` filter, NE izmišlja tag — vidi SM-D7.)
- **OQ-2 (`blog:detail` signature — 5-3 potvrđuje):** 5-2 registruje `blog:detail` = `path("blog/<slug:slug>/", ...)` (mirror products:detail; 5-1 OQ-1 ugovor `slug` kwarg). 5-3 dodaje `blog:category` (`blog/kategorija/<slug>/`) + `blog:tag` (`blog/tag/<slug>/`) arhive (epics.md:891-892). Ako 5-3 traži drugačiji detail signature → uskladi `get_absolute_url` (5-1) + test. Default: `blog:detail` + slug stabilan. NE blokira 5-2.
- **OQ-3 (`PostAdmin.view_on_site` re-enable — 5-2 ili 5-3?):** 5-1 postavio `PostAdmin.view_on_site=False` (jer `get_absolute_url` → NoReverseMatch → 500). 5-2 registruje `blog:detail` → `get_absolute_url` SAD razrešava → „View on site" dugme bi radilo (vodi na placeholder detail). Da li 5-2 re-enable-uje `view_on_site`? **Default: NE u 5-2** (admin polish je 8.7; placeholder detail je minimalan — admin „View on site" na placeholder nije prioritet). 5-3 (pun detail) ili 8.7 re-enable. 5-2 NE dira admin.py (regression guard). Ako se želi rano re-enable → trivijalno (ukloni `view_on_site=False`), ali van 5-2 scope-a. Flag za 5-3/8.7.
- **OQ-4 (card grid: REUSE `coric-product-card` vs novi `coric-blog-card`):** SM-D8 prepušta Dev/UX. Blog kartica ima `perex` (duži tekst) + `datum` koje product-card nema (product ima KS/cena). Ako product-card layout ne pasuje blog sadržaju → novi `coric-blog-card`. Preferiraj REUSE ako pasuje (YAGNI). NE blokira (oba validna; CSS odluka). Možda UX (Sally) sign-off na vizuelni layout pre Dev GREEN.
- **OQ-5 (empty state: jedan tekst vs filter-0/prazan-blog razdvajanje) — RESOLVED (IMP-4):** **ODLUKA: RAZDVOJ** — `{% if active_filters.kategorija %}` grana u `_blog_empty_state.html`: filter-0 → „Nema objava u ovoj kategoriji." + „prikaži sve"/clear-filter link (`{% url 'blog:index' %}`); prazan-blog → „Uskoro nove priče sa polja." (epics.md:879) + „POVRATAK NA POČETNU" (`pages:home`). „Uskoro nove priče sa polja" je zavaravajuće za filter-0 (objave postoje, samo ne u toj kategoriji). `active_filters.kategorija` je već u kontekstu (Task 4.2) → grana je trivijalna. Vidi SM-D9/AC7. (Invalid slug normalizuje na „" → pokazuje prazan-blog granu — prihvatljivo; vidi SM-D9 nuansu.)

### Testing notes (šta TEA pokriva — RED phase)

- **BlogIndexView (AC1/AC2):** GET `/sr/blog/` (`reverse("blog:index")`) → 200, template `blog/blog_index.html`, `context["posts"]`; **Post.published (NE Post.objects)** — DRAFT/future/None NEVIDLJIVI, PUBLISHED-past JESTE (draft-not-leaked); naslov „Priče sa polja" pun dijakritik. **N+1: assertNumQueries(N) konstanta** — 3 objave == 10 objava; `select_related("category")` (BEZ `prefetch_related("tags")` — IMP-1, kartica ne renderuje tagove); `categories_for_dropdown` +1 query (konstanta, NE per-post — Gotcha BL2-5).
- **Paginacija (AC3):** 25 published → strana 1 = 10, `is_paginated`; `?page=3` = 5; `?page=999` clamp (NE 404); `?page=abc` → strana 1; `{% querystring %}` čuva `?kategorija`.
- **Kartica (AC4):** main_image responsive (`{% if %}` guard nullable) + `published_at|date:"SHORT_DATE_FORMAT"` (locale-aware — IMP-2; pod `activate("sr")` daje `DD.MM.YYYY.`) + title + perex + „SAZNAJ VIŠE" + `href=get_absolute_url`=`/sr/blog/<slug>/`; `data-testid="blog-card-<slug>"`.
- **Filter HTMX (AC5):** `?kategorija=<slug>` → te kategorije; „Sve" → sve; HTMX request → `_post_results.html` (NE full) + OOB aria-live; non-HTMX → full + selected dropdown; invalid slug → 0 + empty + normalizovan active_filters; Vary: HX-Request header. **OOB guarded `{% if request.htmx %}`** (Gotcha BL2-2 — non-HTMX render NE sme imati OOB plain-text).
- **URL wiring + get_absolute_url + placeholder detail (AC6):** `reverse("blog:index")="/sr/blog/"`; `reverse("blog:detail", slug="x")="/sr/blog/x/"`; `Post.get_absolute_url()` razrešava (NE NoReverseMatch); GET published detail → 200; draft detail → 404 (Post.published). **AŽURIRAJ 5-1 `test_get_absolute_url.py`** (SM-D12/Gotcha BL2-3 — `NoReverseMatch` → razrešen put).
- **Empty state DVE grane (AC7/IMP-4):** 0 published (bez filtera) → prazan-blog „Uskoro nove priče sa polja" + „POVRATAK NA POČETNU" (`pages:home`); DRAFT-only → prazan-blog; VALIDNA kategorija sa 0 objava → filter-0 „Nema objava u ovoj kategoriji." + „prikaži sve" (`blog:index`); invalid slug → prazan-blog (normalizovan); NEMA paginacije.
- **i18n (AC8):** ključni string-ovi pun-dijakritik (NE šišana); sr render (+ smoke hu/en); slug ASCII u href; `loading="lazy"`.
- **TEA policy:** `@pytest.mark.django_db` na DB testove; pytest-django (NE unittest.TestCase). REUSE 5-1 `conftest.py` factory helpers (`make_post`/`make_category`). HTMX simulacija kroz `client.get(url, HTTP_HX_REQUEST="true")` ili django-htmx test helper. **5-1 `test_get_absolute_url.py` je INHERITED test** — 5-2 ga ažurira (NE dodaje novi fajl; menja postojeću asertaciju). assertNumQueries lock N empirijski u GREEN (TEA piše assertNumQueries strukturu, Dev fix-uje broj).

## Risk-Tier Self-Assessment

**TIER: HIGH.**

**Obrazloženje:** PRVI konzument 5-1 modela + prva javna blog view + URL wiring koji aktivira 5-1 `get_absolute_url` ugovor. Kombinuje:
1. **Draft-not-leaked granica (SM-D2/Gotcha BL2-1)** — najlakša greška (`Post.objects` umesto `Post.published`) procuruje DRAFT/scheduled objave javno (correctness/privacy bug). Mora `Post.published` + test koji asertuje DRAFT/future nevidljivi.
2. **URL wiring koji menja 5-1 ponašanje (SM-D11/D12)** — registracija `blog:detail` aktivira `get_absolute_url` (admin „View on site", buduća sitemap/share linkovi) I pravi 5-1 `NoReverseMatch` test zastarelim → 5-2 mora ažurirati inherited test. `blog:detail` placeholder kontrakt koji 5-3 nasleđuje mora biti tačno specifikovan (pogrešan signature → 5-3 lomi `get_absolute_url`).
3. **HTMX filter + paginacija kombinatorika** — request.htmx branching + OOB aria-live guard + querystring filter-preservation kroz stranice + Paginator overflow + vary_on_headers cache defense (5 pattern-a iz 2-8/2-9 koji se moraju ispravno složiti; OOB-bez-guarda = plain-text bug — Gotcha BL2-2).
4. **N+1 (SM-D6/Gotcha BL2-5)** — listing view sa per-post category FK = klasičan N+1; mora select_related+prefetch_related + assertNumQueries lock; categories_for_dropdown +1 query mora biti u budžetu (konstanta).
5. **Placeholder DetailView koji 5-3 nasleđuje** — mora biti minimalan ali funkcionalan (published-only, 404 za draft) + tačan kontrakt (model/queryset/template) da 5-3 obogaćuje BEZ refaktora.

NIJE MEDIUM: nova javna view + draft-leak rizik + URL wiring koji menja 5-1 (inherited test + get_absolute_url aktivacija) + HTMX/N+1 + 5-3-nasleđeni placeholder kontrakt zajedno prelaze prag. Mitigacija: SVI patterni REUSE iz 2-8/2-9 (dokazani — ListView/HTMX/paginacija/filter/empty/N+1); NEMA migracije/model promene (0 schema rizik); NEMA novog dep; placeholder detail je minimalan (5-3 obogaćuje); Post.published manager već postoji+testiran (5-1). Gotchas (BL2-1..BL2-5) eksplicitno dokumentovani; draft-not-leaked + inherited-test-update + OOB-guard su glavni risk-mitigacioni testovi.

## Dev Agent Record

### Agent Model Used

Opus 4.8 (1M) — autonomous Dev (GREEN phase).

### Debug Log References

- Blog suite: 109 passed (50 nove 5-2 + 5-1 inherited test_get_absolute_url green).
- Full suite: 1734 passed, 6 failed, 7 skipped, 4 xfailed. Svih 6 failova su PRE-POSTOJEĆI (verifikovano stash-om 5-2 wiring-a — identično padaju bez blog izmena; nepovezani sa 5-2: test_app_boundaries::brands_imports_products, base_template htmx-version/main-css-placeholder, bootstrap installed_apps_default, navigation_chrome ×2).
- `manage.py check` → 0 issues. `makemigrations --check --dry-run` → No changes detected (0 migracija).
- ruff + djade (templates/blog/) clean (pokrenuto u containeru — host uv resolve pada na cert/network grešku, nepovezano sa kodom).
- `makemessages -a` regenerisao sr/hu/en .po (blog string-ovi ekstraktovani; sr authoritative; hu/en fallback na sr).

### TEST_MODIFICATION

- `apps/blog/tests/test_blog_index_n_plus_1.py:35-46,67` | Original: `_seed_published(... n ...)` koristio `range(n)` bez offset-a → drugi seed poziv (7 objava) reciklirao title-ove `broj 0..2` prvog batch-a (3 objave) → Post.slug globalno-unique kolizija (ValidationError „Objava sa poljem Slug već postoji"; 5-1 IMP-5 nema auto-dedup). | Changed to: dodat `start=0` kwarg → `range(start, start+n)`; drugi poziv `start=3` → jedinstveni slug-ovi. | Reason: genuine test-seed bug (slug kolizija), NE production-kod problem; count-variation intent (3 vs 10 objava) očuvan.

### Completion Notes List

- BlogIndexView + BlogPostDetailView placeholder oba kroz `Post.published` (draft/future → off-index + 404 na detail).
- Tačno JEDAN `id="blog-results"` unutar `_post_results.html`; OOB aria-live guarded `{% if request.htmx %}`.
- 0 migracija; CSS novi `coric-blog-card` (1col/2-3col responsive var(--token)) + main.css @import.

### File List

NEW:
- apps/blog/views.py
- apps/blog/urls.py
- templates/blog/blog_index.html
- templates/blog/post_detail.html
- templates/blog/partials/_post_results.html
- templates/blog/partials/_post_card.html
- templates/blog/partials/_blog_filter.html
- templates/blog/partials/_blog_empty_state.html
- static/css/components/blog-listing.css

MODIFIED:
- config/urls.py (blog.urls mount pod i18n_patterns)
- static/css/main.css (@import blog-listing.css)
- locale/{sr,hu,en}/LC_MESSAGES/django.po (makemessages)
- apps/blog/tests/test_blog_index_n_plus_1.py (test-seed slug-kolizija fix — vidi TEST_MODIFICATION)
- _bmad-output/implementation-artifacts/sprint-status.yaml (5-2 → review)
