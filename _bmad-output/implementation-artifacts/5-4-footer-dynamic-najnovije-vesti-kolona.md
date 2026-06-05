---
story_id: "5.4"
story-key: 5-4-footer-dynamic-najnovije-vesti-kolona
title: Footer Dynamic „Najnovije vesti" Kolona
status: ready-for-dev
epic: 5
epic_num: 5
epic_title: Blog (Priče sa polja)
module: blog
created: 2026-06-05
last_modified: 2026-06-05
complexity: M
author: Mihas (SM autonomous; ČETVRTA i POSLEDNJA story Epic 5 — Blog „Priče sa polja". Dinamizuje footer kolonu „Najnovije vesti" (Story 1.8 placeholder Lorem Ipsum × 3) tako da prikazuje ≤3 NAJNOVIJE OBJAVLJENE blog objave kao linkove na post detail. KLJUČNO — NOVI `apps/blog/context_processors.py:latest_blog_posts(request)` (PRVI blog context processor; mirror Django idiom) registrovan u config/settings/base.py context_processors listi → footer je u base.html → context processor se izvršava na SVAKOM renderu (uključujući HTMX partial response-e koji NE renderuju footer). SM-D2 ODLUKA: queryset umotan u `SimpleLazyObject` da DB upit puca SAMO kad template stvarno iterira `latest_blog_posts` (full-page render sa footerom), NE na HTMX partialima → 0 upita kad se ne pristupa, 1 upit kad footer renderuje. SM-D1 ODLUKA (load-bearing, OQ-5 RESOLVED): EKSPLICITAN `.order_by("-published_at", "-created_at")` — published_at je semantički ispravno polje za „najnovije OBJAVE" (kada je postalo javno vidljivo), NE created_at (kada je draft red kreiran). epics.md:902/UX-DR-27:239 doslovno kažu „created_at" — reconcile: wording je nepreciznost; published_at je user-facing recency. Draft-not-leaked SVUDA (`Post.published`, NIKAD `Post.objects`). 0 migracija, 0 novih view/url, 0 model promene, 0 novi dep. RISK TIER: MEDIUM — footer je deljen na SVAKOJ strani sajta → greška u context processoru 500-uje CEO sajt + every-request perf granica (lazy) + draft-not-leaked + ordering reconciliation; ALI scope je uzak (1 NEW modul + 1 settings linija + 1 template kolona) i sav pattern je dokazan.)
depends_on:
  - 5-1-blogpost-category-tag-modeli-admin-stub              # Post model (title translatable [modeltranslation → aktivna lokala], slug, published_at, created_at, get_absolute_url=reverse("blog:detail", slug) [5-2 registruje URL]); `Post.published` manager (status="published" AND published_at__lte=now — draft-not-leaked granica; published_at IS NOT NULL & <=now garantovan → order_by("-published_at") uvek dobro-definisan); `objects` PRVI / `published` DRUGI (BL-3); Meta.ordering=["-published_at","-created_at"]
  - 5-2-blog-index-strana-sa-paginacijom-filter              # blog:detail URL registrovan (get_absolute_url razrešava → footer linkovi rade); `_blog_empty_state.html` postojeći msgid „Uskoro nove priče sa polja" (REUSE — SM-D5/OQ-3); BlogIndexView Post.published pattern (draft-not-leaked presedan)
  - 1-8-footer                                               # `templates/partials/footer.html` (Story 1.8); kolona 3 „Najnovije vesti" sa 3 Lorem Ipsum {% translate %} placeholdera + TODO komentar koji pokazuje na 5-4; section_eyebrow „NAJNOVIJE VESTI" heading; `coric-footer__news` <ul> (5-4 zamenjuje SAMO <ul> sadržaj); footer je u base.html → render na SVAKOJ strani (every-request granica — SM-D2)
---

# Story 5.4: Footer Dynamic „Najnovije vesti" Kolona

Status: ready-for-dev

## Opis

As a **posetilac sajta Ćorić Agrar**,

I want **da iz footera (sa bilo koje strane) direktno dođem do najnovijih objavljenih blog objava**,

so that **vidim svežu „priču sa polja" i lako otvorim najnoviji sadržaj bez navigacije do blog index-a**.

Ovo je **ČETVRTA i POSLEDNJA story Epic 5 (Blog — Priče sa polja)**. Story 1.8 je položio statičan footer sa kolonom „Najnovije vesti" koja trenutno renderuje **3 Lorem Ipsum `{% translate %}` placeholdera** (sa TODO komentarom koji eksplicitno pokazuje na 5-4). 5-1 je položio `Post` model + `Post.published` manager. 5-2 je registrovao `blog:detail` URL (`Post.get_absolute_url()` razrešava). 5-4 **dinamizuje** tu footer kolonu: NOVI `apps/blog/context_processors.py:latest_blog_posts(request)` exposes ≤3 najnovije OBJAVLJENE objave svakom template-u, a footer kolona 3 ih renderuje kao linkove na post detail.

**KRITIČNO — EVERY-REQUEST GRANICA (SM-D2):** footer je u `base.html` → context processor se izvršava na **SVAKOM renderu** (uključujući HTMX partial response-e koji NE renderuju footer). Da se izbegne nepotreban DB upit na svakom HTMX partialu, queryset se umotava u `SimpleLazyObject` → DB upit puca SAMO kad template stvarno iterira `latest_blog_posts` (full-page render sa footerom). Lazy callable materializuje u **listu** (`list(...)`) tako da `{% if %}` + `{% for %}` u template-u NE re-query-ju.

**KRITIČNO — ORDERING (SM-D1, OQ-5 RESOLVED, load-bearing):** epics.md:902 + UX-DR-27:239 doslovno kažu „3 najnovije po `created_at`". ALI za JAVNE „najnovije OBJAVE" semantički ispravno polje je `published_at` (kada je objava postala JAVNO VIDLJIVA), NE `created_at` (kada je DB red nacrta kreiran — dugo-draftovana objava objavljena DANAS bi pod `created_at` bila pogrešno zakopana ispod starijih). Odluka: **EKSPLICITAN `.order_by("-published_at", "-created_at")`** (NE oslanjanje na implicitni `Meta.ordering` — intent zaključan; buduća Meta promena ne sme tiho preurediti footer). Vidi SM-D1 za punu reconcilijaciju.

### IN SCOPE (šta ova story isporučuje)

1. **`apps/blog/context_processors.py` — `latest_blog_posts(request)` (NOVO; PRVI blog context processor):** funkcija prima `request`, vraća dict `{"latest_blog_posts": <SimpleLazyObject koji materializuje listu ≤3 najnovijih PUBLISHED objava>}`. Lazy callable: `list(Post.published.order_by("-published_at", "-created_at")[:3])`. **`Post.published`** (NIKAD `Post.objects` — draft/future NEVIDLJIV; SM-D3). EKSPLICITAN order_by (SM-D1). `SimpleLazyObject` wrapper (SM-D2 — upit puca SAMO na iteraciji; HTMX partial = 0 upita).
2. **`config/settings/base.py` EDIT — registruj context processor:** append `"apps.blog.context_processors.latest_blog_posts"` u `TEMPLATES[0]["OPTIONS"]["context_processors"]` listu (posle postojećih Django processora). 1 linija.
3. **`templates/partials/footer.html` EDIT — kolona 3 `<ul class="coric-footer__news">`:** zameni 3 Lorem Ipsum `<li>` placeholdera `{% for post in latest_blog_posts %}<li><a href="{{ post.get_absolute_url }}">{{ post.title }}</a></li>{% empty %}<li class="coric-footer__news-empty">{% translate "Uskoro nove priče sa polja" %}</li>{% endfor %}` (`{% empty %}` → 0 objava placeholder; <3 → loop renderuje koliko ima — prirodno). Ažuriraj/ukloni postojeći TODO komentar (5-4 ga rešava). `section_eyebrow` „NAJNOVIJE VESTI" heading OSTAJE (uvek renderovan — SM-D5).
4. **Empty-state copy (SM-D5; OQ-3 RESOLVED):** 0 objava → `{% empty %}` grana renderuje **`{% translate "Uskoro nove priče sa polja" %}`** — **REUSE postojeći msgid** iz 5-2 `_blog_empty_state.html` (već preveden u sr/hu/en .po). Vidi SM-D5 za reconcilijaciju sa epics.md:906 doslovnim „Uskoro nove priče" (kraćom frazom).
5. **i18n** — jedini novi-u-footeru string je „Uskoro nove priče sa polja" koji VEĆ POSTOJI kao msgid (REUSE — bez novog .po unosa); `post.title` je modeltranslation → renderuje se u aktivnoj lokali automatski. `just messages` se pokreće radi higijene (potvrdi da nema novog/orphan msgid-a). `.po` sr/hu/en netaknuti (osim ako `just messages` doda fuzzy — Dev proverava).

### OUT OF SCOPE (eksplicitno — granice)

- **Model promene / migracije** = NEMA. 5-1 šema je finalna; 5-4 konzumira `Post.published` queryset. `makemigrations --check --dry-run` MORA „No changes detected".
- **Novi view / URL** = NEMA. Context processor NIJE view; footer linkuje na POSTOJEĆI `blog:detail` (5-2). 5-4 NE dira `apps/blog/urls.py` / `apps/blog/views.py` / `config/urls.py`.
- **Novi Python dep** = NEMA (`SimpleLazyObject` je `django.utils.functional` — stdlib Django). NEMA `uv add`.
- **Caching layer (Redis/Celery/template-fragment cache)** = NE (OQ-2). Projekat NEMA Redis/Celery (mirror 2-13 „no-cache duh"); `SimpleLazyObject` (upit puca SAMO na render sa footerom) + jedan indeksiran upit sa LIMIT 3 (`blog_post_status_pub_idx` na `(status, -published_at)`) je right-sized optimizacija. Cache je v1.1 razmatranje, NE 5-4.
- **Datum/perex/slika u footer linku** = NE (OQ-1). epics.md:903 traži SAMO „linkove ka post detail-u" → footer renderuje TITLE + LINK, bez datuma/perexa/thumbnaila. Minimalno.
- **Broj objava ≠ 3** = NE (parametrizacija/admin-podešavanje broja). Hard `[:3]` (epics.md:904 „3 najnovije"; <3 → koliko ima). Konfigurabilan broj je YAGNI.
- **Drugi delovi footera (kolona 1/2/4 — logo/proizvodi/kontakt)** = NETAKNUTO. 5-4 dira SAMO kolonu 3 `<ul class="coric-footer__news">` sadržaj. Kolone 1/2/4 + `section_eyebrow` heading-ovi + social + copyright OSTAJU.
- **`_blog_empty_state.html` izmena** = NE. 5-4 REUSE msgid-a „Uskoro nove priče sa polja", NE ceo partial (footer empty je inline `{% empty %}` `<li>`, NE include `_blog_empty_state.html` — taj partial nosi home-CTA dugme koje ne pripada footer koloni). SM-D5.

### Princip

5-4 **dinamizuje** Story 1.8 footer kolonu „Najnovije vesti": NOVI `latest_blog_posts(request)` context processor exposes ≤3 najnovije PUBLISHED objave (kroz `Post.published` — draft-not-leaked; EKSPLICITAN `.order_by("-published_at", "-created_at")` — SM-D1) svim template-ima, umotano u `SimpleLazyObject` (upit puca SAMO kad footer renderuje — every-request perf; SM-D2). Footer kolona 3 renderuje svaku objavu kao link na `blog:detail` (`get_absolute_url`); 0 objava → `{% empty %}` placeholder „Uskoro nove priče sa polja" (REUSE 5-2 msgid); <3 → koliko ima (loop prirodno). `post.title` je modeltranslation → aktivna lokala automatski. NEMA model promene/migracije/novog view/url/dep. NEMA caching layera (`SimpleLazyObject` + indeksiran LIMIT-3 upit je right-sized). NEMA defensive validacije. NEMA premature abstrakcije.

### Strukturna arhitektura — repository delta

**1 NEW modul (context_processors.py) + 1 EDIT (settings registracija) + 1 EDIT (footer kolona) + 0 migracija + 0 model promene + 0 novi view/url + 0 novi dep.**

| Path | Tip | Razlog |
|---|---|---|
| `apps/blog/context_processors.py` | NEW (SM-D1/SM-D2/SM-D3) | `latest_blog_posts(request)` → `{"latest_blog_posts": SimpleLazyObject(lambda: list(Post.published.order_by("-published_at", "-created_at")[:3]))}`. **`Post.published`** (draft-not-leaked — SM-D3; NIKAD `Post.objects`). EKSPLICITAN `.order_by("-published_at", "-created_at")` (SM-D1 — NE oslanjaj se na Meta.ordering; published_at je user-facing recency, NE created_at). `SimpleLazyObject` + `list(...)` materializacija (SM-D2 — upit SAMO na iteraciji; HTMX partial = 0 upita; template re-iteracija NE re-query). BEZ `.only()` (SM-D4 — modeltranslation + .only() hazard; plain queryset je već minimalan: 3 reda). Docstring: WHY published_at (SM-D1), WHY lazy (SM-D2), WHY ne .only() (SM-D4), every-request granica. |
| `config/settings/base.py` | EDIT | Append `"apps.blog.context_processors.latest_blog_posts"` u `TEMPLATES[0]["OPTIONS"]["context_processors"]` (posle 4 Django processora, linija ~81). 1 linija. |
| `templates/partials/footer.html` | EDIT (kolona 3) | Zameni 3 Lorem `<li>` u `<ul class="coric-footer__news">` (linije 34-38) sa `{% for post in latest_blog_posts %}<li><a href="{{ post.get_absolute_url }}">{{ post.title }}</a></li>{% empty %}<li class="coric-footer__news-empty">{% translate "Uskoro nove priče sa polja" %}</li>{% endfor %}` (SM-D5/SM-D6). Ukloni postojeći TODO komentar (linija 33 — referiše **stari** ime `latest_posts|slice:":3"`; 5-4 standardizuje na `latest_blog_posts` — IMP-1: nijedna varijabla `latest_posts` NE preživljava). `section_eyebrow` „NAJNOVIJE VESTI" + `<ul>` wrapper OSTAJU. Kolone 1/2/4 NETAKNUTE. |
| `tests/test_navigation_chrome.py` | EDIT (TEA — 5-4 OWNS; SM-D7) | **OBAVEZNO** — 5-4 footer edit (ukloni 3 Lorem `<li>` + ukloni „Story 5.4" TODO) DETERMINISTIČKI obara postojeći `test_ac6_footer_renders_lorem_ipsum_news_placeholder_with_todo` (`:726` — asertuje `Lorem ipsum >= 3` AND `Story 5.4` u footer SOURCE). Ovaj test MORA biti REWRITTEN (NE samo obrisan — čuvamo AC6-source-level lock): asertuj NOVI dinamički markup (`{% for post in latest_blog_posts %}` u source-u) + `Lorem ipsum` NIJE prisutno + „Story 5.4" TODO NIJE prisutno. Intent (footer „Najnovije vesti" kolona postoji) je OČUVAN — migriran sa Lorem-placeholdera na dinamiku. `test_ac6_footer_renders_4_columns_with_3_section_eyebrows` (`:701`) PREŽIVLJAVA netaknut (5-4 čuva „NAJNOVIJE VESTI" eyebrow + 4 kolone). Vidi SM-D7 + Task 3.4. |
| `apps/blog/tests/test_context_processors.py` | NEW (TEA) | AC1-AC4 + AC7 + AC8: context processor exposes ≤3 PUBLISHED najnovije po published_at; draft/future excluded; <3 → koliko ima; SimpleLazyObject lazy (assertNumQueries — 0 kad se ne pristupa, 1 kad se pristupa); i18n title aktivna lokala. |
| `apps/blog/tests/test_footer_news.py` | NEW (TEA) | AC2/AC5/AC6: footer render (full page) prikazuje ≤3 linka na `blog:detail` (`get_absolute_url`); 0 objava → „Uskoro nove priče sa polja" placeholder (validan markup, bez broken `<li>`); HTMX partial response ne renderuje footer i ne pravi upit (AC7 integracija). |
| `locale/{sr,hu,en}/LC_MESSAGES/django.po` | (verovatno NETAKNUTO) | „Uskoro nove priče sa polja" VEĆ postoji kao msgid (REUSE — SM-D5). `just messages` higijena; Dev proverava da nema novog/fuzzy unosa. |
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | EDIT | `5-4` → `ready-for-dev`; po implementaciji epic-5 → `done` (POSLEDNJA story epika). SM handoff (NIJE deliverable). |

**NETAKNUTO (regression guards):** `apps/blog/models.py`/`managers.py`/`translation.py`/`admin.py`/`views.py`/`urls.py` (5-1/5-2/5-3 — NE menja se); `apps/blog/migrations/` (NEMA nove migracije — `makemigrations --check` MORA „No changes"); `config/urls.py` (NE dira — context processor nije URL); `templates/blog/partials/_blog_empty_state.html` (5-2 — NE menja; 5-4 REUSE samo msgid); footer kolone 1/2/4 + `section_eyebrow` + social + copyright; svi postojeći app-ovi/testovi; `pyproject.toml` (NEMA novog dep). **0 migracija, 0 model promene, 0 novi view/url/dep.**

## Kriterijumi prihvatanja

**AC1 — `latest_blog_posts(request)` context processor exposes ≤3 PUBLISHED objave (SM-D2/SM-D3)**

- **Given** `apps/blog/context_processors.py` registrovan u `config/settings/base.py` context_processors listi; više PUBLISHED objava (>3)
- **When** bilo koji template se renderuje sa `RequestContext` (request prisutan)
- **Then** context sadrži ključ `latest_blog_posts` koji (kad se iterira) daje **najviše 3** objave
  - queryset je `Post.published.order_by("-published_at", "-created_at")[:3]` (LIMIT 3)
  - **kroz `Post.published`** (NIKAD `Post.objects` — draft-not-leaked; SM-D3)
  - vrednost je `SimpleLazyObject` koji materializuje **listu** (SM-D2 — template `{% if %}`/`{% for %}` ne re-query)
- **And** sa 5 PUBLISHED objava → tačno 3 (najnovije 3); sa 2 PUBLISHED → 2 (AC4)

**AC2 — Najnovije-prvo po `published_at` (NE created_at — SM-D1; OQ-5 RESOLVED, load-bearing)**

- **Given** AC1; više PUBLISHED objava sa RAZLIČITIM `published_at` i `created_at` (uključujući objavu sa STARIM `created_at` ali NOVIM `published_at` — dugo-draftovana, danas objavljena)
- **When** context processor vrati `latest_blog_posts`
- **Then** objave su sortirane **`-published_at` PRVO, pa `-created_at`** (najnovije objavljene prve)
  - EKSPLICITAN `.order_by("-published_at", "-created_at")` (NE oslanjanje na `Meta.ordering` — intent zaključan; SM-D1)
  - **published_at je primarni kriterijum** (kada je postala javno vidljiva), NE created_at (epics.md:902 doslovno „created_at" je nepreciznost — SM-D1 reconcile)
- **And** **load-bearing test (SM-D1):** objava A (`created_at` star, `published_at` DANAS) MORA biti PRE objave B (`created_at` skoriji, `published_at` JUČE) — dokazuje published_at-prvo ordering (pod created_at-prvo bi B bio prvi → POGREŠNO)
- **And** `Post.published` garantuje `published_at IS NOT NULL & <= now` → `order_by("-published_at")` je UVEK dobro-definisan (nema NULL sortiranja)

**AC3 — Samo PUBLISHED: draft + future-dated EXCLUDED (draft-not-leaked; SM-D3)**

- **Given** AC1; mix objava: PUBLISHED (status="published", published_at<=now), DRAFT (status="draft"), FUTURE (status="published", published_at>now)
- **When** context processor vrati `latest_blog_posts`
- **Then** SAMO PUBLISHED objave su prisutne; **DRAFT NIJE; FUTURE NIJE** (`Post.published` granica — status="published" AND published_at__lte=now)
- **And** **draft-not-leaked test**: kreiraj draft objavu + future objavu → ni jedna nije u `latest_blog_posts` (test asertuje OBE excluded — ista bezbednosna granica kao 5-2/5-3)
- **And** sa SAMO draft/future objavama (0 published) → prazna lista → empty placeholder (AC5)

**AC4 — Manje od 3 objave → renderuje koliko ima (epics.md:905)**

- **Given** AC1; tačno 2 PUBLISHED objave (ili 1)
- **When** footer renderuje `latest_blog_posts`
- **Then** prikazuje TAČNO 2 (ili 1) linka — NE 3, NE prazne `<li>`, NE „None"
  - `{% for %}` loop renderuje koliko ima (prirodno — bez padding-a)
- **And** test: 2 published → 2 `<li><a>`; 1 published → 1; 0 → `{% empty %}` placeholder (AC5)

**AC5 — 0 objava → placeholder „Uskoro nove priče sa polja" (epics.md:906; SM-D5)**

- **Given** AC1; 0 PUBLISHED objava (prazan blog ILI samo draft/future)
- **When** footer kolona 3 renderuje
- **Then** `{% empty %}` grana renderuje **`{% translate "Uskoro nove priče sa polja" %}`** kao `<li class="coric-footer__news-empty">` (validan markup — NE broken `<li>`, NE prazan `<ul>`)
  - **REUSE postojeći msgid** „Uskoro nove priče sa polja" (iz 5-2 `_blog_empty_state.html` — već preveden sr/hu/en; SM-D5/OQ-3)
  - `section_eyebrow` „NAJNOVIJE VESTI" heading OSTAJE renderovan (uvek — SM-D5)
- **And** test: 0 published → response sadrži „Uskoro nove priče sa polja" + validan `<ul>...</ul>` (1 `<li>`, bez praznih); „NAJNOVIJE VESTI" heading prisutan

**AC6 — Svaka objava renderuje kao link na post detail (`get_absolute_url`; epics.md:903)**

- **Given** AC1; PUBLISHED objava sa slug-om
- **When** footer renderuje objavu
- **Then** `<li><a href="{{ post.get_absolute_url }}">{{ post.title }}</a></li>`
  - `href` = `post.get_absolute_url()` = `reverse("blog:detail", slug=post.slug)` → `/sr/blog/<slug>/` (5-2 URL razrešava; slug ASCII)
  - tekst linka = `post.title` (modeltranslation — aktivna lokala; AC8)
- **And** test: footer link href == `post.get_absolute_url()` (`/sr/blog/<slug>/`); klik vodi na detail (5-3 detail strana)

**AC7 — Every-request perf: lazy → 0 upita na HTMX partial / 1 na full page (SM-D2)**

- **Given** AC1; `latest_blog_posts` umotan u `SimpleLazyObject`
- **When** (a) HTMX partial response koji NE renderuje footer; (b) full-page render koji renderuje footer
- **Then**:
  - (a) **HTMX partial (footer se NE iterira)** → `latest_blog_posts` DB upit se **NE izvršava** (`assertNumQueries(0)` za blog Post upit — lazy callable se ne poziva); context processor se izvršava ali ne query-je
  - (b) **full page (footer iterira `latest_blog_posts`)** → DB upit se izvršava **TAČNO 1×** (`assertNumQueries(1)` za blog Post upit); LIMIT 3 indeksiran (`blog_post_status_pub_idx`)
  - template re-iteracija (`{% if latest_blog_posts %}` + `{% for %}`) NE re-query (materijalizovan u `list()` — SM-D2)
- **And** **lazy test (load-bearing):** render template KOJI NE pristupa `latest_blog_posts` → 0 upita; render template KOJI iterira → 1 upit; pristupanje DVA puta u istom template-u → i dalje 1 upit (lista keširana u lazy objektu)
- **And** NEMA caching layera (OQ-2 — projekat nema Redis/Celery; lazy + indeksiran LIMIT-3 upit je right-sized)

**AC8 — i18n: title u aktivnoj lokali; smoke hu/en (SM-D6)**

- **Given** AC1; PUBLISHED objava sa `title_sr`/`title_hu`/`title_en` (modeltranslation)
- **When** footer renderuje pod aktivnom lokalom (sr default; hu/en smoke)
- **Then**:
  - `post.title` renderuje u AKTIVNOJ lokali (modeltranslation virtuelni atribut — automatski; npr. `/hu/` strana → title_hu)
  - link `get_absolute_url` daje locale-prefiksovan URL (`/sr/blog/<slug>/` na sr, `/hu/blog/<slug>/` na hu — slug NIJE translatable; i18n_patterns)
  - „Uskoro nove priče sa polja" placeholder kroz `{% translate %}` (pun dijakritik; postojeći prevod sr/hu/en)
- **And** „NAJNOVIJE VESTI" `section_eyebrow` heading je već translatable (Story 1.8 — NE 5-4)
- **And** smoke render `/hu/` + `/en/` → title u toj lokali (NE crash, NE sr-fallback osim ako prevod prazan)

## Tasks / Subtasks

> **Konvencija:** `[TEA-RED]` = Test Architect piše test PRE implementacije (mora FAIL). `[DEV-GREEN]` = Developer implementira. **Dev NIKAD ne piše testove.** **NEMA migracije** (context processor/settings/template — konzumira 5-1 šemu + 5-2 URL). **NEMA `uv add`.** ⚠️ Footer je u base.html → context processor na SVAKOM renderu (every-request granica — SM-D2 lazy).

- [ ] **Task 1 — `apps/blog/context_processors.py` modul (AC1/AC2/AC3/SM-D1/SM-D2/SM-D3/SM-D4)** `[DEV-GREEN]`
  - [ ] 1.1 NEW `apps/blog/context_processors.py`: `from django.utils.functional import SimpleLazyObject` + `from apps.blog.models import Post`. `def latest_blog_posts(request): return {"latest_blog_posts": SimpleLazyObject(lambda: list(Post.published.order_by("-published_at", "-created_at")[:3]))}`.
  - [ ] 1.2 **`Post.published`** (NIKAD `Post.objects` — SM-D3 draft-not-leaked). **EKSPLICITAN `.order_by("-published_at", "-created_at")`** (SM-D1 — NE oslanjaj se na Meta.ordering; published_at user-facing recency). `[:3]` LIMIT. **`list(...)` UNUTAR lambda** (SM-D2 — materijalizuj da template re-iteracija NE re-query). **BEZ `.only()`** (SM-D4 — modeltranslation + .only() hazard; plain queryset je već minimalan).
  - [ ] 1.3 Docstring: WHY published_at-PRVO (SM-D1 reconcile epics „created_at"), WHY `SimpleLazyObject` (SM-D2 every-request — upit SAMO na iteraciji; HTMX partial = 0), WHY ne `.only()` (SM-D4), WHY ne caching (OQ-2). Komentari samo WHY (project-context.md).
  - [ ] 1.4 `manage.py check` exit 0; modul se importuje bez kružne zavisnosti (`Post` import na vrhu modula je OK — context_processors se importuje pri startup-u, posle app registry; mirror site_settings templatetag import pattern).

- [ ] **Task 2 — Registracija u `config/settings/base.py` (AC1)** `[DEV-GREEN]`
  - [ ] 2.1 EDIT `config/settings/base.py`: append `"apps.blog.context_processors.latest_blog_posts"` u `TEMPLATES[0]["OPTIONS"]["context_processors"]` listu (posle `"django.contrib.messages.context_processors.messages"`, linija ~81). Komentar `# NOVO Story 5.4 — footer Najnovije vesti`.
  - [ ] 2.2 `manage.py check` exit 0; render bilo koje strane → `latest_blog_posts` u context-u (Dev shell smoke).

- [ ] **Task 3 — `footer.html` kolona 3 dinamizacija (AC4/AC5/AC6/SM-D5/SM-D6)** `[DEV-GREEN]`
  - [ ] 3.1 EDIT `templates/partials/footer.html` kolona 3 `<ul class="coric-footer__news">` (linije 34-38): zameni 3 Lorem `<li>` sa `{% for post in latest_blog_posts %}<li><a href="{{ post.get_absolute_url }}">{{ post.title }}</a></li>{% empty %}<li class="coric-footer__news-empty">{% translate "Uskoro nove priče sa polja" %}</li>{% endfor %}`.
  - [ ] 3.2 Ukloni postojeći TODO komentar (linija 33 — „TODO: Story 5.4 (Epic 5) zamenice ovo sa {% for post in latest_posts|slice:":3" %}…" → 5-4 ga rešava; obriši TODO ili zameni kratkim WHY komentarom). **IMP-1: stari TODO referiše ime `latest_posts` — 5-4 standardizuje na registrovani context ključ `latest_blog_posts`; nijedna varijabla pod imenom `latest_posts` NE sme preživeti** (ni u markupu ni u komentaru). `section_eyebrow` „NAJNOVIJE VESTI" heading + `<ul>` wrapper OSTAJU. Kolone 1/2/4 NETAKNUTE.
  - [ ] 3.3 (CSS opciono) `coric-footer__news-empty` klasa — ako footer CSS treba placeholder styling, dopuni postojeći footer CSS (`var(--token)`). Default: nasleđuje `coric-footer__news li` stil (verovatno nije potrebno novo pravilo — Dev proverava vizuelno).
  - [ ] 3.4 **`tests/test_navigation_chrome.py` REWRITE — 5-4 OWNS ovaj test (SM-D7; mirror 5-2 lekcija)** `[TEA-RED]` Footer edit (3.1/3.2) DETERMINISTIČKI obara postojeći `test_ac6_footer_renders_lorem_ipsum_news_placeholder_with_todo` (`:726`) jer asertuje `Lorem ipsum >= 3` AND `Story 5.4` u footer SOURCE — a 5-4 uklanja OBA. **TEA MORA REWRITE-ovati taj test** (NE samo obrisati — čuvamo AC6-source-level lock): asertuj NOVI dinamički markup u footer source-u (`re.search(r"\{%\s*for\s+post\s+in\s+latest_blog_posts", src)`) + `Lorem ipsum` NIJE u source-u + „Story 5.4" TODO NIJE u source-u. INTENT (footer „Najnovije vesti" kolona postoji + markirana) je OČUVAN, samo migriran sa Lorem-placeholdera na dinamiku. **NE diraj** `test_ac6_footer_renders_4_columns_with_3_section_eyebrows` (`:701`) — PREŽIVLJAVA netaknut (5-4 čuva „NAJNOVIJE VESTI" eyebrow + 4 `col-md-3` kolone). Alternativno (manje preferirano): obriši stari test i superseduj novim `test_footer_news.py` source-level pokrivanjem — ali REWRITE je preferiran (zadržava lock na istom mestu).

- [ ] **Task 4 — i18n higijena (AC5/AC8)** `[DEV-GREEN]`
  - [ ] 4.1 Potvrdi „Uskoro nove priče sa polja" VEĆ postoji kao msgid (5-2 `_blog_empty_state.html`); REUSE — bez novog .po unosa (SM-D5). `just messages` higijena (potvrdi nema novog/orphan/fuzzy msgid-a; ako `just messages` doda fuzzy → Dev review). `post.title` modeltranslation (aktivna lokala — bez .po).
  - [ ] 4.2 Smoke render `/sr/` + `/hu/` + `/en/` → footer title u toj lokali; placeholder „Uskoro nove priče sa polja" preveden.

- [ ] **Task 5 — RED-phase testovi (AC1-AC8)** `[TEA-RED]`
  - [ ] 5.1 `apps/blog/tests/test_context_processors.py` (NEW) + REUSE `conftest.py` (`make_post`/`make_category`). `@pytest.mark.django_db`. Direktno testiranje funkcije `latest_blog_posts(request_factory.get("/"))` + integraciono kroz render.
  - [ ] 5.2 **AC1 (≤3 published):** 5 published → `latest_blog_posts` materializuje 3; vrednost je `SimpleLazyObject`; `Post.published` baza (ne `Post.objects`).
  - [ ] 5.3 **AC2 (ordering published_at — SM-D1, LOAD-BEARING):** objava A (created_at star, published_at DANAS) + objava B (created_at skoriji, published_at JUČE) → A je PRE B (dokazuje published_at-prvo, NE created_at-prvo); EKSPLICITAN order_by zaključan (test bi PUKAO pod created_at-prvo). **NIT: seed-uj DISTINCT `published_at`/`created_at` po svakom post-u (bez same-timestamp flakiness).**
  - [ ] 5.4 **AC3 (draft-not-leaked — SM-D3):** mix published + draft + future → SAMO published; draft NIJE; future NIJE (OBA excluded). Ista granica kao 5-2/5-3.
  - [ ] 5.5 **AC4 (<3):** 2 published → 2; 1 published → 1; 0 → prazna lista. NE padding, NE „None".
  - [ ] 5.6 **AC7 (lazy — SM-D2, LOAD-BEARING):** `apps/blog/tests/test_footer_news.py` (NEW) ili u test_context_processors.py — **`assertNumQueries(0)`** kad se `latest_blog_posts` NE iterira; **`assertNumQueries(1)`** kad footer iterira; pristupanje DVA puta → i dalje 1 (lista keširana u lazy). Lock empirijski. **⚠️ C3/IMP-3: NE koristi `_render_partial`/`render_to_string` (bypass-uje context processore → LAŽNO 0). 1-upit vehicle = `client.get(reverse("pages:home"))` (RequestContext → footer iterira → 1). 0-upit vehicle = `client.get("/sr/blog/", HTTP_HX_REQUEST="true")` → `_post_results.html` ne extend-uje base.html → footer se ne iterira → lazy se ne razrešava → 0. Opciono unit shape: `latest_blog_posts(RequestFactory().get("/"))` za oblik povratne vrednosti (NE za query-count).**
  - [ ] 5.6b **`tests/test_navigation_chrome.py` REWRITE (SM-D7 — vidi Task 3.4):** REWRITE `test_ac6_footer_renders_lorem_ipsum_news_placeholder_with_todo` (`:726`) — nova asercija: footer source sadrži `{% for post in latest_blog_posts %}`, NE sadrži „Lorem ipsum", NE sadrži „Story 5.4" TODO. NE diraj `test_ac6_footer_renders_4_columns_with_3_section_eyebrows` (`:701` — preživljava). Intent (footer „Najnovije vesti" kolona postoji) očuvan.
  - [ ] 5.7 **AC5 (empty placeholder):** 0 published (prazan ili samo draft/future) → footer sadrži „Uskoro nove priče sa polja" + validan `<ul>` (1 `<li class="coric-footer__news-empty">`, bez praznih `<li>`); „NAJNOVIJE VESTI" heading prisutan.
  - [ ] 5.8 **AC6 (link na detail):** published objava → footer `<a href>` == `post.get_absolute_url()` (`/sr/blog/<slug>/`); tekst == `post.title`. (Zahteva 5-2 `blog:detail` URL registrovan — REUSE.)
  - [ ] 5.9 **AC8 (i18n):** smoke render `/sr/` + `/hu/` → `post.title` u toj lokali (modeltranslation); placeholder preveden; link locale-prefiksovan; NE crash.
  - [ ] 5.10 **AC4/AC5 footer integracija:** `client.get(reverse("pages:home"))` → footer kolona 3 render (≤3 linka ILI placeholder); full-page render (NE HTMX) sadrži footer.

- [ ] **Task 6 — Dev manual gate (NE pytest) (AC regression)** `[DEV-GREEN]`
  - [ ] 6.1 `manage.py check` exit 0; **`makemigrations --check --dry-run` → „No changes detected"** (NEMA model promene — regression guard).
  - [ ] 6.2 Dev shell smoke: 3+ published → footer prikazuje 3 najnovije (po published_at); 0 published → „Uskoro nove priče sa polja"; HTMX partial (npr. blog filter swap) → footer se NE renderuje, query lock potvrđen (Django Debug Toolbar / `assertNumQueries`).
  - [ ] 6.3 `just lint` clean (ruff `apps/blog/context_processors.py` + djade `templates/partials/footer.html`). Commit context_processors+settings+footer+testovi ZAJEDNO (atomic). **VAŽNO (C1c — NE „svi 1.8 footer testovi ostaju zeleni" bez kvalifikacije):** `test_ac6_footer_renders_4_columns_with_3_section_eyebrows` (`:701`) PREŽIVLJAVA netaknut (5-4 čuva „NAJNOVIJE VESTI" eyebrow + 4 `col-md-3` kolone), ALI `test_ac6_footer_renders_lorem_ipsum_news_placeholder_with_todo` (`:726`) MORA biti REWRITTEN od strane OVE story (Task 3.4 — TEA) jer 5-4 menja markup koji taj test asertuje. **LEKCIJA (mirror 5-2): kada story zameni markup koji test druge story asertuje, OVA story OWNS taj test update.** Potvrdi: rewritten Lorem-test zelen + blog testovi (5-1/5-2/5-3) zeleni + ostali footer/nav testovi (1.8) zeleni.

## Dev Notes

### SM Decisions (SM-D log)

**SM-D1 — ORDERING RECONCILIATION (OQ-5 RESOLVED, LOAD-BEARING): EKSPLICITAN `.order_by("-published_at", "-created_at")` — published_at PRVO, NE created_at.** epics.md:902 + UX-DR-27:239 doslovno kažu „3 najnovije po `created_at`". **ALI** za JAVNE „najnovije OBJAVE" semantički ispravno polje je **`published_at`** (kada je objava postala JAVNO VIDLJIVA), NE `created_at` (kada je DB red NACRTA kreiran).
- **PROBLEM sa created_at:** objava draftovana pre 3 meseca ali OBJAVLJENA DANAS bi pod `created_at` ordering bila pogrešno zakopana ispod objava koje su kreirane skorije ali objavljene ranije → footer „Najnovije vesti" bi prikazao STARIJE javne objave umesto najsvežijih. To je suprotno korisničkoj nameri („vidim svežu sadržaj" — Opis).
- **REUSE Meta.ordering?** `Post.Meta.ordering = ["-published_at", "-created_at"]` (5-1 models.py:182) je VEĆ published_at-prvo. ALI odluka je **EKSPLICITAN `.order_by(...)` u context processoru** (NE oslanjanje na implicitni Meta.ordering) — intent footera je ZAKLJUČAN; buduća Meta promena (npr. 8.x doda „featured" ordering) NE sme tiho preurediti footer „Najnovije vesti". Eksplicitnost > implicitno nasleđivanje za load-bearing javni redosled.
- **RECONCILE sa epics „created_at":** epics.md:902/UX-DR-27:239 wording („created_at") je **nepreciznost** — autor je mislio „najnovije objave" (recency), a `published_at` JE user-facing recency za objavljene objave. `created_at` je tie-breaker (sekundarni), NE primarni. Ova story EKSPLICITNO reconcile-uje: primarni `-published_at`, sekundarni `-created_at`. (RESOLVED OQ — vidi Open Questions OQ-5.)
- **Dobro-definisan:** `Post.published` manager garantuje `published_at IS NOT NULL & published_at <= now` (managers.py:24-29) → `order_by("-published_at")` UVEK ima ne-NULL vrednost za sortiranje (nema NULL-sort dvosmislenosti). Test (5.3) load-bearing: A(created star/published danas) PRE B(created skoriji/published juče).

**SM-D2 — EVERY-REQUEST PERFORMANCE: `SimpleLazyObject` — DB upit puca SAMO kad footer renderuje (full page), NE na HTMX partialima.** Footer je u `base.html` → context processor `latest_blog_posts(request)` se izvršava na **SVAKOM renderu** (svaka strana sajta + svaki HTMX partial response koji prolazi kroz `RequestContext`). HTMX partial response-i (npr. 2-8/2-9/5-2 filter swap → `_post_results.html`) NE renderuju footer → ne treba im `latest_blog_posts` upit.
- **ODLUKA:** umotaj queryset u **`SimpleLazyObject(lambda: list(Post.published.order_by(...)[:3]))`** (`django.utils.functional`). Lazy callable se poziva **SAMO** kada template prvi put pristupi/iterira `latest_blog_posts` (tj. footer render na full-page) → DB upit puca SAMO tada. HTMX partial koji ne dira `latest_blog_posts` → **0 upita** (lazy se ne razrešava).
- **`list()` MATERIJALIZACIJA UNUTAR lambda:** lazy callable vraća `list(...)` (NE goli QuerySet) — tako da template `{% if latest_blog_posts %}` (boolean check) + `{% for %}` (iteracija) NE re-evaluiraju QuerySet (QuerySet bi se evaluirao 2× bez `list()`-keširanja unutar lazy). `SimpleLazyObject` kešira rezultat callable-a posle prvog poziva → drugi pristup vraća keširanu listu (1 upit ukupno, čak i sa višestrukim `{% %}` pristupom). (Gotcha BL4-1.)
- **Upit je JEFTIN:** jedan indeksiran SELECT (`blog_post_status_pub_idx` na `(status, -published_at)` — 5-1 models.py:185-190) sa `WHERE status='published' AND published_at<=now ORDER BY -published_at LIMIT 3` → B-tree leftmost-prefix scan, 3 reda. NEMA N+1 (footer renderuje samo title+link, NEMA related access — SM-D4).
- **NEMA CACHING LAYERA (OQ-2):** projekat NEMA Redis/Celery (mirror 2-13 „no-cache duh"). `SimpleLazyObject` (upit SAMO na footer render) + indeksiran LIMIT-3 upit je **right-sized** optimizacija — template-fragment cache / Redis bi bio premature (1 jeftin upit po full-page render, ne po partialu). Cache je v1.1 razmatranje. Test (5.6/AC7) lock: 0 upita kad se ne pristupa, 1 kad footer renderuje, re-iteracija ne re-query.

**SM-D3 — DRAFT-NOT-LEAKED: `Post.published` (NIKAD `Post.objects`).** Ista bezbednosna granica kao 5-2 index + 5-3 detail/arhive/Slične-objave. `latest_blog_posts` MORA koristiti `Post.published` (status="published" AND published_at__lte=now — managers.py:24-29) → draft + future-dated objave NEVIDLJIVE u footeru. Najlakša greška (`Post.objects.order_by(...)[:3]`) procuruje nacrt/zakazanu objavu na SVAKU stranu sajta (footer je svuda) → kritičan leak. Test (5.4) asertuje draft I future excluded. **NIKAD `Post.objects` u javnom kontekst processoru.**

**SM-D4 — QUERY SHAPE: BEZ `.only()` (modeltranslation hazard); plain queryset je već minimalan.** Footer renderuje SAMO `post.title` (link tekst) + `post.get_absolute_url()` (koristi `post.slug`). Iskušenje je `.only("slug", "published_at", "created_at", "title")` da se smanji SELECT. **ODLUKA: NE micro-optimizuj sa `.only()`** jer:
- **modeltranslation hazard:** `title` je modeltranslation polje → realne DB kolone su `title_sr`/`title_hu`/`title_en`, a aktivno-jezička virtuelna `title` se razrešava kroz suffiksovanu kolonu. `.only("title")` bi DEFEROVALO `title_<lang>` kolone → pristup `post.title` u template-u bi okinuo **dodatni per-row upit** (deferred-field load) → tihi N+1 (suprotno nameri `.only()`).
- **već minimalan:** `Post.published.order_by(...)[:3]` je SAMO 3 reda; ušteda od `.only()` (par kolona × 3 reda) je zanemarljiva, a rizik (deferred title N+1) je realan.
- **jasnoća > premature .only():** plain `[:3]` queryset je čitljiv, bezbedan, dovoljno brz. (Gotcha BL4-3.)

**SM-D5 — EMPTY-STATE COPY: REUSE postojeći msgid „Uskoro nove priče sa polja" (OQ-3 RESOLVED).** epics.md:906 doslovno kaže placeholder „**Uskoro nove priče**" (kraća fraza). ALI 5-2 `_blog_empty_state.html` (linija 15) VEĆ koristi msgid „**Uskoro nove priče sa polja**" (duža fraza — već preveden u sr/hu/en .po; grep potvrdio locale/{sr,hu,en}/django.po).
- **ODLUKA: REUSE postojeći duži msgid „Uskoro nove priče sa polja"** (NE uvodi novi „Uskoro nove priče" msgid). Razlozi: (1) konzistentnost — ista fraza na blog index empty-state I footer empty (jedan glas); (2) već preveden u sva 3 jezika (NEMA novog .po unosa za prevodioca); (3) epics.md:906 „Uskoro nove priče" je skraćeni opis iste namere (footer empty placeholder), a 5-2 je već kanonizovao puniju frazu. Reconcile: epics wording je sažet; koristimo postojeću kanoničku frazu.
- **NE include `_blog_empty_state.html`:** footer empty je INLINE `{% empty %}` `<li>` (NE include cele partial-e) — `_blog_empty_state.html` nosi home-CTA dugme („POVRATAK NA POČETNU") + filter granu koji NE pripadaju footer koloni. Footer samo treba minimalan placeholder tekst. REUSE je SAMO msgid (string), NE markup.
- **`section_eyebrow` „NAJNOVIJE VESTI" heading OSTAJE uvek** (i kad je 0 objava — kolona zadržava naslov; SM-D6). (RESOLVED OQ — vidi OQ-3.)

**SM-D6 — i18n: post.title modeltranslation (aktivna lokala automatski); placeholder `{% translate %}`; link locale-prefiksovan.** `post.title` je modeltranslation virtuelni atribut → renderuje se u AKTIVNOJ lokali automatski (npr. `/hu/` strana → `title_hu`) BEZ posebnog template koda. Link `{{ post.get_absolute_url }}` = `reverse("blog:detail", slug)` pod `i18n_patterns` → daje locale-prefiksovan URL (`/sr/blog/<slug>/`, `/hu/blog/<slug>/`); **slug NIJE translatable** (5-1 slugify_ascii — isti ASCII slug u svim lokalama). Jedini eksplicitan `{% translate %}` u footer koloni je „Uskoro nove priče sa polja" (placeholder — REUSE msgid SM-D5). „NAJNOVIJE VESTI" `section_eyebrow` heading je već translatable iz Story 1.8 (NE 5-4). `just messages` higijena (potvrdi nema novog/orphan msgid-a). Smoke render sr/hu/en (AC8).

**SM-D7 — TEST OWNERSHIP: 5-4 OWNS `tests/test_navigation_chrome.py::test_ac6_footer_renders_lorem_ipsum_news_placeholder_with_todo` REWRITE (C1; mirror 5-2 lekcija).** Story 1.8 je položio source-level lock na footer kolonu 3: `test_ac6_footer_renders_lorem_ipsum_news_placeholder_with_todo` (`tests/test_navigation_chrome.py:726`) čita footer.html SOURCE i asertuje `len(re.findall(r"Lorem ipsum", src)) >= 3` AND `re.search(r"Story\s*5\.4", src)`. **5-4 footer edit (ukloni 3 Lorem `<li>` + ukloni „Story 5.4" TODO) DETERMINISTIČKI obara taj test.**
- **ODLUKA: 5-4 OWNS update ovog testa** (NE Dev — TEA u RED fazi; Dev NIKAD ne piše/ne menja testove). Test se **REWRITE-uje** (NE briše): nova asercija lock-uje DINAMIČKI markup u footer source-u — `{% for post in latest_blog_posts %}` PRISUTNO, `Lorem ipsum` NIJE prisutno, „Story 5.4" TODO NIJE prisutno. **INTENT testa (footer „Najnovije vesti" kolona postoji + markirana) je OČUVAN** — samo migriran sa Lorem-placeholdera na dinamiku. REWRITE > delete jer zadržava AC6-source-level lock na istom mestu.
- **`test_ac6_footer_renders_4_columns_with_3_section_eyebrows` (`:701`) PREŽIVLJAVA NETAKNUT:** 5-4 čuva „NAJNOVIJE VESTI" `section_eyebrow` + sve 4 `col-md-3` kolone → taj test ostaje zelen bez izmene. (NE menjaj ga.)
- **LEKCIJA (eksplicitno, mirror 5-2):** kada story zameni markup koji test DRUGE story asertuje, **OVA story OWNS taj test update**. Zato je `tests/test_navigation_chrome.py` u file-delta tabeli kao EDIT + Task 3.4 ga eksplicitno dodeljuje TEA. Story NE sme biti „silent" o tome da menja postojeći lock.

### Gotchas (footer-context-processor-specific traps)

**Gotcha BL4-1 — `SimpleLazyObject` BEZ `list()` materijalizacije → re-query na svaki template pristup.** Ako lazy callable vrati goli QuerySet (`SimpleLazyObject(lambda: Post.published...[:3])` bez `list()`), template `{% if latest_blog_posts %}` (boolean → evaluacija 1) + `{% for post in latest_blog_posts %}` (iteracija → evaluacija 2) bi evaluirao QuerySet 2× → 2 upita (QuerySet keš ne preživljava preko SimpleLazyObject boundary konzistentno). **MORA `list(...)` UNUTAR lambda** (SM-D2) → lazy kešira listu posle prvog poziva → 1 upit ukupno bez obzira na broj `{% %}` pristupa. Test (5.6/AC7): dvostruki pristup → i dalje 1 upit.

**Gotcha BL4-2 — context processor se izvršava na SVAKOM renderu (incl HTMX partiali) → bez lazy = upit na svaki partial.** Footer je u base.html, ali context processor se poziva za SVAKI `RequestContext` render — uključujući HTMX partial response-e (2-8/2-9/5-2 filter swap) koji NE renderuju footer. Bez `SimpleLazyObject` (SM-D2) svaki HTMX swap bi nepotrebno pravio blog upit. **Lazy → upit SAMO kad footer iterira (full page).** Test (5.6/AC7): HTMX partial → `assertNumQueries(0)` za blog upit.

**Gotcha BL4-3 — `.only("title")` + modeltranslation → deferred-field N+1 (SM-D4).** Iskušenje `.only("slug", "title")` da se smanji SELECT. ALI `title` modeltranslation → realne kolone `title_sr`/`_hu`/`_en`; `.only("title")` defer-uje `title_<lang>` → pristup `post.title` u template-u okida per-row deferred load (N+1). **NE koristi `.only()`** — plain `[:3]` (3 reda) je već minimalan, bez N+1 rizika (SM-D4). Footer ne dira related objekte (samo title+slug) → nema potrebe za select_related.

**Gotcha BL4-4 — EKSPLICITAN order_by, NE Meta.ordering oslanjanje (SM-D1).** `Post.Meta.ordering` je trenutno published_at-prvo, ali context processor MORA EKSPLICITNO `.order_by("-published_at", "-created_at")` — buduća Meta promena (8.x featured/pinned ordering) NE sme tiho preurediti footer „Najnovije vesti". Eksplicitnost zaključava intent. Test (5.3) load-bearing: published_at-prvo (NE created_at-prvo iz epics doslovnog teksta).

**Gotcha BL4-5 — `Post.objects` u footeru = draft/future leak na CEO sajt (SM-D3).** Footer je svuda → `Post.objects.order_by(...)[:3]` (umesto `Post.published`) procuruje nacrt/zakazanu objavu na SVAKU stranu. **MORA `Post.published`** (status="published" AND published_at__lte=now). Test (5.4) asertuje draft I future excluded.

**Gotcha BL4-6 — context processor greška 500-uje CEO sajt (footer je deljen).** Footer je na svakoj strani → bilo koji izuzetak u `latest_blog_posts` (ili u lazy callable) 500-uje SVAKU stranu, ne samo blog. **Defensive: lazy callable mora biti prost i bezbedan** — `list(Post.published.order_by(...)[:3])` je jednostavan (nema parsiranja request-a, nema spoljnih poziva, nema atributa koji mogu biti None). NE dodaj kompleksnu logiku u context processor. **(C2 — REVIEWED & ACCEPTED:** sitewide-500 blast radius je svesno prihvaćen rizik za prost indeksiran upit — **NE dodaj defensive try/except** oko upita; to bi prekršilo no-defensive-validation princip i sakrilo realne greške. Prost callable JE mitigacija.) `Post` import na vrhu modula je bezbedan (context_processors se importuje posle app registry-ja pri startup-u). Ako `blog:detail` URL ne bi bio registrovan (nije slučaj — 5-2 ga registruje), `get_absolute_url` u template-u bi pucao → još jedan razlog zašto je 5-2 hard dependency.

### Project Structure Notes

- `apps/blog/` POSTOJI (5-1 models/managers + 5-2 views/urls/templates/css + 5-3 detail/arhive). 5-4 dodaje SAMO `context_processors.py` (PRVI blog context processor — `apps/**/context_processors.py` glob trenutno PRAZAN; mirror Django idiom). NEMA izmene views/urls/models.
- Context-exposure presedan: `apps/pages/templatetags/site_settings.py` (`{% site_setting %}` simple_tag — per-request keš na request objektu) je presedan za „prost query po request-u" u footeru. Footer VEĆ koristi `{% site_setting %}` (kolona 4 kontakt). 5-4 dodaje `latest_blog_posts` kroz CONTEXT PROCESSOR (NE templatetag) jer je to Django idiom za „expose-uj nešto svim template-ima"; `SimpleLazyObject` igra istu ulogu kao site_setting per-request keš (upit SAMO kad treba).
- Footer (1.8): `templates/partials/footer.html` — kolona 3 „Najnovije vesti" (linije 30-39) sa 3 Lorem `<li>` + TODO na 5-4 (linija 33). 5-4 zamenjuje SAMO `<ul class="coric-footer__news">` sadržaj (linije 34-38). `section_eyebrow` „NAJNOVIJE VESTI" (linija 32) OSTAJE.
- Settings: `config/settings/base.py:77-82` context_processors lista (4 Django processora). 5-4 append-uje 5. (`apps.blog.context_processors.latest_blog_posts`).
- **FORWARD-DEP:** ovo je POSLEDNJA Epic 5 story — epic-5 → `done` po implementaciji. Nema 5-5. (8.x može dodati caching layer — OQ-2 — ali to je novi epik.)
- **INHERITED kontrakt (5-4 konzumira, NE menja):** 5-1 `Post.published` + `Post.title` (modeltranslation) + `Post.get_absolute_url` + `published_at`/`created_at`/`Meta.ordering` + `blog_post_status_pub_idx`; 5-2 `blog:detail` URL (get_absolute_url razrešava) + „Uskoro nove priče sa polja" msgid (`_blog_empty_state.html`); 1-8 footer markup + `section_eyebrow` + `coric-footer__news` <ul>.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-5.4] (`:895-906`) — footer „Najnovije vesti": context_processors.py exposes `latest_blog_posts` (3 najnovije objavljene — epics kaže „po created_at", SM-D1 reconcile → published_at); footer renderuje 3 kao linkove na post detail; <3 → koliko ima; 0 → placeholder „Uskoro nove priče"
- [Source: _bmad-output/planning-artifacts/epics.md] (`:239` UX-DR-27) — „3 najnovije po created_at" (SM-D1 reconcile: published_at je user-facing recency)
- [Source: _bmad-output/planning-artifacts/epics.md] (`:287` FR-30) — footer dinamička „Najnovije vesti" kolona zahtev
- [Source: _bmad-output/planning-artifacts/epics.md] (`:33` FR-3) — blog „Priče sa polja" funkcionalni zahtev
- [Source: apps/blog/models.py:178-190] — `objects` PRVI (`_default_manager`) / `published` DRUGI (PublishedManager); `Meta.ordering=["-published_at","-created_at"]` :182; `blog_post_status_pub_idx` na `(status,-published_at)` :185-190; `published_at`/`created_at` polja; `get_absolute_url=reverse("blog:detail", slug)` :207-209; `title` modeltranslation
- [Source: apps/blog/managers.py:24-29] — `PublishedManager.get_queryset()` → `.filter(status="published", published_at__lte=now)` (draft-not-leaked granica; published_at IS NOT NULL & <=now garantovan → order_by dobro-definisan — SM-D1/SM-D3)
- [Source: templates/partials/footer.html:30-39] — Story 1.8 kolona 3 „Najnovije vesti": `section_eyebrow` „NAJNOVIJE VESTI" :32 + 3 Lorem `<li>` + TODO na 5-4 :33 (5-4 zamenjuje `<ul>` sadržaj :34-38)
- [Source: templates/blog/partials/_blog_empty_state.html:15] — postojeći msgid „Uskoro nove priče sa polja" (REUSE — SM-D5; već preveden sr/hu/en)
- [Source: config/settings/base.py:71-85] — `TEMPLATES[0]["OPTIONS"]["context_processors"]` lista (4 Django processora :77-82 — 5-4 append-uje latest_blog_posts)
- [Source: apps/pages/templatetags/site_settings.py:30-48] — `{% site_setting %}` per-request keš presedan (footer kolona 4 — context-exposure konvencija; SimpleLazyObject igra istu „upit-samo-kad-treba" ulogu)
- [Source: apps/blog/views.py:1-32] — 5-2/5-3 `BlogIndexView` `Post.published` pattern (draft-not-leaked presedan — SM-D3) + HTMX partial render-i (`_post_results.html`) koji NE renderuju footer (every-request lazy motivacija — SM-D2)
- [Source: locale/{sr,hu,en}/LC_MESSAGES/django.po] — „Uskoro nove priče sa polja" msgid postoji sva 3 jezika (REUSE — SM-D5)
- [Source: _bmad-output/implementation-artifacts/5-2-blog-index-strana-sa-paginacijom-filter.md] — `Post.published` draft-not-leaked + „Uskoro nove priče sa polja" empty-state msgid (5-4 REUSE)
- [Source: _bmad-output/implementation-artifacts/5-3-blog-post-detail-strana.md] — blog:detail strana koju footer linkovi otvaraju (Project Structure Notes :337 FORWARD-DEP 5-4 footer)
- [Source: _bmad-output/implementation-artifacts/5-1-blogpost-category-tag-modeli-admin-stub.md] (`:55`) — footer placeholder „Uskoro nove priče" je 1-8/5-4 scope; 5-4 dodaje `context_processors.py:latest_blog_posts`
- [Source: _bmad-output/project-context.md] — context processor every-request granica + N+1 MANDATORY :743; SimpleLazyObject lazy idiom; :497-527 pune dijakritike; :350-353 komentari samo WHY; no-cache duh (2-13)

### Open Questions (OQ)

- **OQ-1 (footer link — datum/perex/thumbnail?):** epics.md:903 traži SAMO „linkove ka post detail-u" → **DEFAULT: title + link, BEZ datuma/perexa/thumbnaila.** Footer kolona je kompaktna (mirror Lorem placeholder = samo tekst link). Ako biznis traži datum pored naslova → trivijalan dodatak (`{{ post.published_at|date }}`), ali NIJE u 5-4 scope-u (minimalno). NE blokira.
- **OQ-2 (caching layer — DEFERRED v1.1):** template-fragment cache / Redis za footer upit? **ODLUKA: NE u 5-4** (SM-D2). Projekat nema Redis/Celery (2-13 no-cache duh); `SimpleLazyObject` (upit SAMO na footer render, NE na HTMX partial) + indeksiran LIMIT-3 upit je right-sized. Cache je v1.1/8.x razmatranje ako profiling pokaže footer upit kao hot path (malo verovatno — 1 jeftin upit po full-page). NE blokira.
- **OQ-3 (empty-state copy „Uskoro nove priče" vs „Uskoro nove priče sa polja" — RESOLVED; SM-D5):** epics.md:906 doslovno „Uskoro nove priče" (kraće); 5-2 `_blog_empty_state.html` već kanonizovao „Uskoro nove priče sa polja" (već preveden). **ODLUKA: REUSE postojeći duži msgid** (konzistentnost + nema novog .po unosa + epics wording je sažet opis iste namere). RESOLVED — ne blokira; specifikovano AC5/SM-D5.
- **OQ-5 (ordering created_at vs published_at — RESOLVED, LOAD-BEARING; SM-D1):** epics.md:902 + UX-DR-27:239 doslovno „po created_at"; ALI semantički ispravno za javne „najnovije OBJAVE" je `published_at`. **ODLUKA: EKSPLICITAN `.order_by("-published_at", "-created_at")`** (published_at primarni — kada postala javno vidljiva; created_at tie-breaker). epics „created_at" je nepreciznost (autor mislio recency = published_at za objavljene). RESOLVED — ne blokira; AC2 load-bearing test zaključava published_at-prvo. (Napomena: ovo je „OQ-5" iz Epic 5 progress memory note — sada formalno resolved u ovoj story.)

### Testing notes (šta TEA pokriva — RED phase)

- **Context processor exposes ≤3 (AC1):** 5 published → 3 najnovije; vrednost `SimpleLazyObject`; `Post.published` baza. Direktno (`latest_blog_posts(rf.get("/"))`) + kroz render.
- **Ordering published_at-prvo (AC2 — SM-D1 LOAD-BEARING):** A(created star/published danas) PRE B(created skoriji/published juče) — dokazuje published_at-prvo, NE created_at-prvo (test bi PUKAO pod created_at ordering); EKSPLICITAN order_by.
  - **NIT (seed determinizam):** TEA seed-ovi MORAJU koristiti RAZLIČITE `published_at` (i `created_at`) timestamp-e preko svih post-ova u test-u → newest-first asercija je deterministička (isti timestamp na 2 posta → nedefinisan tie redosled → flaky test). Eksplicitno postavi distinct `published_at`/`created_at` po post-u (NE oslanjaj se na `auto_now_add` koji može dati identičan timestamp u brzom seed-u).
- **draft-not-leaked (AC3 — SM-D3):** published + draft + future → SAMO published; draft NIJE; future NIJE (oba excluded). Ista granica kao 5-2/5-3.
- **<3 (AC4):** 2 published → 2; 1 → 1; 0 → prazna (NE padding/„None").
- **empty placeholder (AC5 — SM-D5):** 0 published → „Uskoro nove priče sa polja" + validan `<ul>` (1 `<li class="coric-footer__news-empty">`, bez praznih); „NAJNOVIJE VESTI" heading prisutan.
- **link na detail (AC6):** footer `<a href>` == `post.get_absolute_url()` (`/sr/blog/<slug>/`); tekst == `post.title`. (REUSE 5-2 `blog:detail`.)
- **lazy every-request (AC7 — SM-D2 LOAD-BEARING):** `assertNumQueries(0)` kad se `latest_blog_posts` NE iterira (HTMX partial / template bez footera); `assertNumQueries(1)` kad footer iterira; dvostruki pristup → i dalje 1 (list keširan u lazy). NEMA caching layera.
  - **⚠️ C3/IMP-3 — KRITIČNO za TEA: NE reuse-uj `_render_partial` / `render_to_string` helper (`tests/test_navigation_chrome.py:133`) za AC7 `assertNumQueries` lock.** Taj helper renderuje BEZ `RequestContext` → **context processori se NE izvršavaju** → `latest_blog_posts` nikad NIJE u context-u → `assertNumQueries(0)` bi bio LAŽNO zelen (0 upita jer processor uopšte ne radi, NE jer je lazy radio ispravno). Taj test ne bi ništa dokazao.
  - **AC7(b) — 1 upit na full page:** koristi `client.get(<full-page URL>)` (npr. `client.get(reverse("pages:home"))`) — pravi `RequestContext` → context processor radi → footer iterira `latest_blog_posts` → TAČNO 1 upit. (Client request prolazi kroz pun template-render stack sa svim context processorima.)
  - **AC7(a) — 0 upita na HTMX partial (KONKRETAN nosač):** koristi 5-2 HTMX partial zahtev koji renderuje `_post_results.html` i NE extend-uje `base.html` → footer se nikad ne iterira → lazy se nikad ne razrešava → 0 blog Post upita. Konkretno: `client.get("/sr/blog/", HTTP_HX_REQUEST="true")` (ili category/tag arhiva HTMX partial). Context processor SE izvršava (RequestContext postoji), ali lazy callable se NE poziva → `assertNumQueries(0)` za blog Post upit DOKAZUJE lazy ponašanje (NE odsustvo processora).
  - **Unit-level shape test (opciono):** TEA može pozvati processor direktno preko `latest_blog_posts(RequestFactory().get("/"))` da proveri OBLIK povratne vrednosti (`SimpleLazyObject`, ključ `latest_blog_posts`) — ALI to NIJE valjan vehicle za query-count lock (RequestFactory ne pokreće template render). Query lock IDE kroz `client.get(...)` (gore).
- **i18n (AC8):** smoke `/sr/`+`/hu/` → title u toj lokali (modeltranslation); placeholder preveden; link locale-prefiksovan; slug ASCII; NE crash.
- **footer integracija (AC4/AC5):** `client.get(reverse("pages:home"))` → footer kolona 3 (≤3 linka ILI placeholder); full-page (NE HTMX) sadrži footer.
- **regression:** postojeći footer testovi (1.8) + blog testovi (5-1/5-2/5-3) OSTAJU ZELENI; `makemigrations --check` → „No changes".
- **TEA policy:** `@pytest.mark.django_db`; pytest-django (NE unittest). REUSE 5-1 `conftest.py` (`make_post`/`make_category`). HTMX kroz `client.get(url, HTTP_HX_REQUEST="true")`. `RequestFactory` za direktan context processor poziv. `assertNumQueries` lock lazy ponašanje (TEA struktura — broj 0/1 empirijski). **Dev NIKAD ne piše testove.**

## Risk-Tier Self-Assessment

**TIER: MEDIUM.**

**Obrazloženje:** Footer je DELJEN na svakoj strani sajta → greška u context processoru ima sajt-wide blast radius (500-uje CEO sajt, ne samo blog), a context processor se izvršava na svakom renderu (every-request perf granica). Kombinuje:
1. **Every-request perf granica (SM-D2/Gotcha BL4-1/BL4-2)** — context processor na SVAKOM renderu (incl HTMX partiali koji ne renderuju footer); bez `SimpleLazyObject` svaki partial pravi nepotreban upit. Lazy + `list()` materijalizacija (upit SAMO kad footer iterira, re-iteracija ne re-query); `assertNumQueries(0/1)` lock.
2. **Sajt-wide blast radius (Gotcha BL4-6)** — footer je svuda → bilo koji izuzetak 500-uje SVAKU stranu. Lazy callable mora biti prost i bezbedan (nema kompleksne logike).
3. **draft-not-leaked (SM-D3/Gotcha BL4-5)** — `Post.published` (NIKAD `Post.objects`); footer je svuda → leak nacrta/zakazane objave bi bio sajt-wide. Test asertuje draft I future excluded.
4. **Ordering reconciliation (SM-D1/Gotcha BL4-4 — LOAD-BEARING)** — epics doslovno „created_at" ali semantički ispravno `published_at`; EKSPLICITAN order_by (NE Meta.ordering oslanjanje); pogrešno polje → footer prikazuje pogrešne „najnovije" objave. Load-bearing test.

NIJE LOW: every-request perf + sajt-wide blast radius + draft-leak + ordering-reconciliation prelaze trivijalan prag. NIJE HIGH: scope je uzak (1 NEW modul + 1 settings linija + 1 footer kolona; 0 migracija/model/view/url/dep); sav pattern dokazan (`Post.published` 5-2/5-3, `SimpleLazyObject` Django stdlib, context_processor Django idiom, footer markup 1.8); jedan jeftin indeksiran LIMIT-3 upit; nema novih javnih ruta/forme/upload-a. Mitigacija: lazy + `list()` (perf), `Post.published` (draft-not-leaked), EKSPLICITAN order_by (ordering lock), prost bezbedan callable (blast-radius), `assertNumQueries` + draft + ordering testovi. Gotchas (BL4-1..BL4-6) eksplicitno dokumentovani.
