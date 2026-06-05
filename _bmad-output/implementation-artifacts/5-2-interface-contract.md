---
story-id: "5.2"
story-key: 5-2-blog-index-strana-sa-paginacijom-filter
artifact: interface-contract
created: 2026-06-04
author: TEA / Murat (autonomous RED phase)
purpose: Canonical contract za DRUGU story Epic 5 — PRVI KONZUMENT 5-1 modela.
         Javna blog INDEX strana `/sr/blog/` (`BlogIndexView(ListView)`) koja listira
         OBJAVLJENE „Priče sa polja" kroz `Post.published` manager (NIKAD `Post.objects`
         — draft/future NEVIDLJIV javno) kao kartice (main_image/datum/title/perex/
         „SAZNAJ VIŠE"), paginacija 10/strani, HTMX category filter `?kategorija=<slug>`
         (request.htmx branching + OOB aria-live guard + push-url — mirror 2-8/2-9),
         Paginator.get_page() overflow safety, N+1 lock `select_related("category")`
         (BEZ tags prefetch — IMP-1), empty state DVE grane (filter-0 vs prazan-blog).
         5-2 kreira NOVI `apps/blog/urls.py` (`app_name="blog"` + `blog:index` +
         `blog:detail`→MINIMALAN placeholder `BlogPostDetailView` koju 5-3 OBOGAĆUJE)
         tako da 5-1 `Post.get_absolute_url()` RAZREŠAVA i kartice linkuju ispravno.
         Mount `path("", include("apps.blog.urls"))` pod i18n_patterns. NEMA model
         promene / NEMA migracije (views/templates/urls SAMO — konzumira 5-1 šemu).
         INHERITED-TEST UPDATE (Task 8.0): 5-1 `test_get_absolute_url.py` prepisan
         iz `NoReverseMatch` → razrešen `/sr/blog/<slug>/` (5-2 OWNS — SM-D12).
         Dev MORA satisfy svaku klauzulu u GREEN.
---

# Interface Contract — Story 5.2 „Blog Index Strana + Paginacija + Filter"

Story 5.2 dodaje view/URL/template sloj u POSTOJEĆI (5-1) `apps/blog/` app:

- `apps/blog/views.py` (NOVO) — `BlogIndexView(ListView)` + `BlogPostDetailView(DetailView)` placeholder.
- `apps/blog/urls.py` (NOVO) — `app_name="blog"`; `blog:index` (`blog/`) + `blog:detail` (`blog/<slug>/`).
- `config/urls.py` (EDIT) — `path("", include("apps.blog.urls"))` pod `i18n_patterns`.
- `templates/blog/` (NOVO direktorijum) — `blog_index.html` + `partials/_post_results.html` +
  `partials/_post_card.html` + `partials/_blog_filter.html` + `partials/_blog_empty_state.html` +
  `post_detail.html` (placeholder).
- CSS responsive grid (REUSE `coric-product-card` ILI novi `coric-blog-card`).
- `apps/blog/tests/test_get_absolute_url.py` (EDIT — INHERITED) — `NoReverseMatch` → razrešen put (Task 8.0).

**NEMA model promene / NEMA migracije** — 5-2 čist view/template/URL sloj nad 5-1 šemom.
`makemigrations --check --dry-run` MORA „No changes detected" (Task 9.1 regression guard).

> **TEST POLITIKA (TEA-D1):** `@pytest.mark.django_db` na DB testove; pytest-django (NE unittest.TestCase).
> REUSE 5-1 `conftest.py` factory helpers (`make_post`/`make_category`/`make_tag`). HTMX simulacija kroz
> `client.get(url, HTTP_HOST="localhost", HTTP_HX_REQUEST="true")` → django-htmx middleware postavlja
> `request.htmx=True`. `activate("sr")` / `with override("sr")` za locale-prefiksovane URL-ove.

> **COLLECTION-SAFETY (TEA-D3):** SVI test moduli importuju `apps.blog.*` UNUTAR test funkcija/fixtura
> (NIKAD module-top-level) → missing view/url daje per-test FAIL (čist RED), NE collection abort.

---

## 1. File-system delta

| Path | Status | Vlasništvo |
|---|---|---|
| `apps/blog/views.py` | NOVO (Dev) | `BlogIndexView(ListView)` + `BlogPostDetailView(DetailView)` — vidi §2/§3. |
| `apps/blog/urls.py` | NOVO (Dev) | `app_name="blog"` + 2 path-a — vidi §4. |
| `config/urls.py` | EDIT (Dev) | `path("", include("apps.blog.urls"))` u `i18n_patterns` (posle forms include — mirror :29-31). |
| `templates/blog/blog_index.html` | NOVO (Dev) | Full-page index — vidi §5. |
| `templates/blog/partials/_post_results.html` | NOVO (Dev) | HTMX swap target (self-id `blog-results`) — vidi §5. |
| `templates/blog/partials/_post_card.html` | NOVO (Dev) | Blog kartica — vidi §5. |
| `templates/blog/partials/_blog_filter.html` | NOVO (Dev) | Category dropdown — vidi §5. |
| `templates/blog/partials/_blog_empty_state.html` | NOVO (Dev) | Empty state DVE grane — vidi §5. |
| `templates/blog/post_detail.html` | NOVO (Dev) | MINIMALAN placeholder detail — vidi §5. |
| `static/css/blog-listing.css` (ili REUSE) | NOVO/EDIT (Dev) | Responsive grid 1col/2-3col (SM-D8). |
| `locale/{sr,hu,en}/LC_MESSAGES/django.po` | EDIT (Dev) | Novi `{% translate %}` string-ovi (`just messages`). |
| `apps/blog/tests/test_get_absolute_url.py` | EDIT (TEA) | INHERITED — `NoReverseMatch` → razrešen put (Task 8.0/SM-D12). |
| `apps/blog/tests/test_blog_index_view.py` | NOVO (TEA) | AC1 (draft-not-leaked). |
| `apps/blog/tests/test_blog_index_n_plus_1.py` | NOVO (TEA) | AC2 (N+1 count-variation lock). |
| `apps/blog/tests/test_blog_index_pagination.py` | NOVO (TEA) | AC3 (+ Task 8.6b combined deep-link). |
| `apps/blog/tests/test_blog_index_card.py` | NOVO (TEA) | AC4 (kartica). |
| `apps/blog/tests/test_blog_index_filter.py` | NOVO (TEA) | AC5 (HTMX filter + OOB guard). |
| `apps/blog/tests/test_blog_urls.py` | NOVO (TEA) | AC6 (URL wiring + placeholder detail). |
| `apps/blog/tests/test_blog_index_empty.py` | NOVO (TEA) | AC7 (empty DVE grane). |
| `apps/blog/tests/test_blog_index_i18n.py` | NOVO (TEA) | AC8 (i18n + responsive smoke). |

**NETAKNUTO (regression guards):** `apps/blog/models.py`/`managers.py`/`translation.py`/`admin.py` (5-1 —
NE menja se); `apps/blog/migrations/` (NEMA nove migracije); svi postojeći app-ovi; `apps/pages` home
`latest_posts=[]`; `templates/partials/footer.html`; `apps/search` „Objave" prazna grana; `pyproject.toml`
(NEMA novog dep). `PostAdmin.view_on_site` ostaje `False` (re-enable je 5-3/8.7 — OQ-3).
**0 migracija, 0 model promene, 0 novi dep.**

---

## 2. `BlogIndexView(ListView)` — `apps/blog/views.py`

```python
@method_decorator(vary_on_headers("HX-Request"), name="dispatch")
class BlogIndexView(ListView):
    model = Post
    context_object_name = "posts"
    paginate_by = 10                       # AC3 — epics.md:875 (SM-D3)

    def get_template_names(self):
        if getattr(self.request, "htmx", False):
            return ["blog/partials/_post_results.html"]
        return ["blog/blog_index.html"]

    def get_queryset(self):
        qs = Post.published.select_related("category")   # NIKAD Post.objects (SM-D2/BL2-1)
        kategorija = self.request.GET.get("kategorija", "").strip()
        if kategorija:
            qs = qs.filter(category__slug=kategorija)
        return qs                          # default ordering iz Meta (najnovije prvo)

    def paginate_queryset(self, queryset, page_size):
        # SM-D25 overflow safety — Paginator.get_page() clamp (NE 404 EmptyPage).
        paginator = self.get_paginator(
            queryset, page_size,
            orphans=self.get_paginate_orphans(),
            allow_empty_first_page=self.get_allow_empty(),
        )
        page_kwarg = self.page_kwarg
        page = self.kwargs.get(page_kwarg) or self.request.GET.get(page_kwarg) or 1
        page_obj = paginator.get_page(page)
        return (paginator, page_obj, page_obj.object_list, page_obj.has_other_pages())

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["categories_for_dropdown"] = Category.objects.order_by("name")
        active_filters = {"kategorija": self.request.GET.get("kategorija", "")}
        valid_slugs = {c.slug for c in ctx["categories_for_dropdown"]}
        if active_filters["kategorija"] and active_filters["kategorija"] not in valid_slugs:
            active_filters["kategorija"] = ""          # IMP-3 invalid-slug normalizacija
        ctx["active_filters"] = active_filters
        ctx["count"] = ctx["paginator"].count          # OOB aria-live announcement
        return ctx
```

**LOCKED klauzule (test-verifikovane):**
- `model=Post`, `context_object_name="posts"`, `paginate_by=10`.
- queryset bazira na **`Post.published`** (NIKAD `Post.objects`) `.select_related("category")` (AC2). **BEZ
  `prefetch_related("tags")`** (IMP-1 — kartica ne renderuje tagove).
- `get_template_names()` → `_post_results.html` ako `request.htmx` else `blog_index.html` (AC5/SM-D5).
- `?kategorija=<slug>` filter `category__slug=<slug>` (AC5); prazan slug → bez filtera.
- `paginate_queryset` override sa `Paginator.get_page()` (AC3 overflow — `?page=999` clamp NE 404; `?page=abc` graceful).
- `get_context_data`: `categories_for_dropdown=Category.objects.order_by("name")` (+1 KONSTANTA — Gotcha BL2-5);
  `active_filters={"kategorija": ...}` sa **invalid-slug normalizacijom na "" (IMP-3)**; `count=paginator.count`.
- `@method_decorator(vary_on_headers("HX-Request"), name="dispatch")` → `Vary: HX-Request` (AC5/SM-D5).

---

## 3. `BlogPostDetailView(DetailView)` placeholder — `apps/blog/views.py` (SM-D11)

```python
class BlogPostDetailView(DetailView):
    model = Post
    context_object_name = "post"                       # 5-3 ugovor (IMP-5)
    template_name = "blog/post_detail.html"

    def get_queryset(self):
        return Post.published.select_related("category")  # draft/future → 404; SAMO category (5-2)
```

**LOCKED klauzule:**
- `model=Post`, `context_object_name="post"`, `template_name="blog/post_detail.html"`.
- `get_queryset()` → `Post.published.select_related("category")` → published-slug detail → 200; **draft/future
  detail → 404** (Post.published; SM-D2). **SAMO `select_related("category")`** (placeholder renderuje
  naslov/datum/telo).
- **FORWARD-NOTE (5-3):** kad 5-3 doda render autora/tagova, MORA proširiti `get_queryset()` sa
  `select_related("author")` / `prefetch_related("tags")` (sprečava 5-3 N+1). 5-2 ih NE dodaje (YAGNI).
- **5-3 OBOGAĆUJE istu klasu** (get_context_data slične-objave + template social/meta/tag linkove) — NE zamenjuje.

---

## 4. URL wiring — `apps/blog/urls.py` + `config/urls.py` (SM-D11 / Gotcha BL2-4)

```python
# apps/blog/urls.py (NOVO)
from django.urls import path
from apps.blog import views

app_name = "blog"

urlpatterns = [
    path("blog/", views.BlogIndexView.as_view(), name="index"),            # PRE slug (Gotcha BL2-4)
    path("blog/<slug:slug>/", views.BlogPostDetailView.as_view(), name="detail"),
]
```

```python
# config/urls.py (EDIT — u i18n_patterns, posle forms include)
path("", include("apps.blog.urls")),  # NOVO Story 5.2 — /sr/blog/ + /sr/blog/<slug>/
```

**LOCKED:**
- `app_name="blog"`; `blog:index` (`blog/`, BEZ slug-a) PRE `blog:detail` (`blog/<slug:slug>/`) — Gotcha BL2-4.
- `reverse("blog:index")` → `/sr/blog/`; `reverse("blog:detail", slug="x")` → `/sr/blog/x/` (i18n_patterns prefiks).
- **`Post.get_absolute_url()` SAD razrešava** na `/sr/blog/<slug>/` (NE NoReverseMatch — SM-D11/SM-D12).
- Mount `path("", include("apps.blog.urls"))` u `i18n_patterns` (NE shadow products/brands/search/pages/forms).

---

## 5. Templates — `templates/blog/`

**`blog_index.html`** (`{% extends "base.html" %}`; mirror `tractor_listing.html`):
- header `<h1>` „Priče sa polja" (pun dijakritik) + lead; `{% block title %}`/`meta_description` statički.
- `{% include "blog/partials/_blog_filter.html" %}`; results sekcija = SAMO `{% include "blog/partials/_post_results.html" %}`
  **BEZ wrapping `id` div-a** (id="blog-results" je U partialu — mirror tractor_listing.html). **NIKAD** `<div id="blog-results">` u parentu (dupli-id bug).

**`partials/_post_results.html`** (HTMX swap target — mirror `_results_grid.html` 1:1):
- Partial SE SAM otvara `<div id="blog-results">` (TAČNO JEDAN id="blog-results", unutar partiala).
- `{% if posts %}` grid (`{% for post in posts %}{% include "blog/partials/_post_card.html" %}{% endfor %}`)
  + paginacija (`{% querystring page=... %}` + `hx-get`/`hx-target="#blog-results"`/`hx-swap="innerHTML"`/`hx-push-url="true"`
  na prev/next linkovima; render SAMO `{% if is_paginated %}`; „Strana X od Y"/„Prethodna"/„Sledeća").
  `{% else %}{% include "blog/partials/_blog_empty_state.html" %}`. Zatim `</div>` zatvara `#blog-results`.
- POSLE zatvaranja id div-a: **guarded `{% if request.htmx %}`** OOB `<div hx-swap-oob="innerHTML:#aria-live">`
  count („Pronađeno N objava", `{% blocktranslate count %}`; OOB IZVAN `#blog-results` jer cilja `#aria-live` singleton).
  **NIKAD OOB u non-HTMX render** (Gotcha BL2-2).

**`partials/_post_card.html`** (mirror coric-product-card u `_results_grid.html`):
- `<a href="{{ post.get_absolute_url }}" data-testid="blog-card-{{ post.slug }}">`.
- `{% if post.main_image %}{% responsive_picture post.main_image alt=post.title sizes="(max-width: 768px) 100vw, 33vw" loading="lazy" %}{% endif %}` (REUSE 2-3; nullable guard).
- `{{ post.published_at|date:"SHORT_DATE_FORMAT" }}` (locale-aware — IMP-2), `{{ post.title }}`, `{{ post.perex }}`, „SAZNAJ VIŠE".
- `{% load i18n media_tags %}`.

**`partials/_blog_filter.html`** (mirror 2-9 `_used_filter_form.html` dropdown — NE 2-8 slider):
- `<form method="get" action="{% url 'blog:index' %}" hx-get="{% url 'blog:index' %}" hx-trigger="change delay:300ms"
  hx-target="#blog-results" hx-swap="innerHTML" hx-push-url="true" hx-indicator="#blog-filter-loading">`.
- `<select name="kategorija">` „Sve kategorije" (value="") + `{% for c in categories_for_dropdown %}<option value="{{ c.slug }}"{% if active_filters.kategorija == c.slug %} selected{% endif %}>{{ c.name }}</option>{% endfor %}`.
- `hx-trigger="change delay:300ms"` SAMO (select-only — NE 2-9 „input changed" varijanta) + htmx-indicator spinner.

**`partials/_blog_empty_state.html`** (DVE grane — IMP-4):
- `{% if active_filters.kategorija %}` → „Nema objava u ovoj kategoriji." + „prikaži sve" link `{% url 'blog:index' %}`.
- `{% else %}` → „Uskoro nove priče sa polja" (epics.md:879) + „POVRATAK NA POČETNU" CTA `{% url 'pages:home' %}`.
- Sve `{% translate %}` pun dijakritik.

**`post_detail.html`** (MINIMALAN placeholder — SM-D11):
- `{% extends "base.html" %}`; `{% block title %}` = post.title; naslov + `{{ post.published_at|date:"SHORT_DATE_FORMAT" }}` + `{{ post.body }}` (plain). NEMA slične-objave/social (5-3).

---

## 6. AC → test traceability

| AC | Test fajl | Pokriva |
|---|---|---|
| AC1 | `test_blog_index_view.py` | reverse blog:index → /sr/blog/; 200 + blog_index.html; context['posts']; naslov dijakritik; **DRAFT/future/None NEVIDLJIVI, PUBLISHED+past VIDLJIV** (SM-D2); najnovije-prvo |
| AC2 | `test_blog_index_n_plus_1.py` | **count-variation lock** (3 == 10 objava); apsolutni gornji budžet ≤ 8 sanity |
| AC3 | `test_blog_index_pagination.py` | paginate_by=10; strana 1=10/2=10/3=5; ?page=999 clamp; ?page=abc graceful; ≤10 no-pagination; **combined ?kategorija&page=2 deep-link (Task 8.6b)** |
| AC4 | `test_blog_index_card.py` | „SAZNAJ VIŠE"; href=get_absolute_url; data-testid; title+perex; **locale-aware datum (SHORT_DATE_FORMAT pod sr)**; main_image guard |
| AC5 | `test_blog_index_filter.py` | ?kategorija filter; prazan=sve; HTMX→partial; **OOB guard (HTMX yes / non-HTMX no)**; OOB count; non-HTMX full+selected; invalid slug normalizovan; Vary header; **TAČNO JEDAN id=blog-results**; filter form hx-attrs |
| AC6 | `test_blog_urls.py` | reverse index/detail; get_absolute_url razrešava; published detail 200 + post_detail.html; context post; **draft 404; future 404** |
| AC7 | `test_blog_index_empty.py` | prazan-blog „Uskoro..." + POVRATAK→pages:home; DRAFT-only→prazan-blog; **validna-kat-0→filter-0 „Nema objava..." + prikaži-sve→blog:index**; filter-0 ne pokazuje Uskoro; no-pagination |
| AC8 | `test_blog_index_i18n.py` | pun dijakritik; nema ćirilice; hu/en smoke 200; ASCII slug; lazy guard; responsive grid hook |
| AC6 (inherited) | `test_get_absolute_url.py` (EDIT) | **Task 8.0** — `NoReverseMatch` → razrešen `/sr/blog/<slug>/` (SM-D12) |

---

## 7. Inherited test update (Task 8.0 / SM-D12) — `apps/blog/tests/test_get_absolute_url.py`

5-2 OWNS ovaj update (5-2 je prvi registrator `blog:detail`). DVE izmene:
- **(a) Asertacija:** `test_get_absolute_url_raises_no_reverse_match()` → `test_get_absolute_url_resolves_blog_detail()`;
  `pytest.raises(NoReverseMatch)` → `with override("sr"): assert post.get_absolute_url() == f"/sr/blog/{post.slug}/"`.
  Uklonjen `from django.urls import NoReverseMatch` import.
- **(b) Docstring/komentar:** „5.3 ažurira ovaj test..." → „5.2 ažurira ovaj test (SM-D12 — 5-2 registruje blog:detail)".

**RED do GREEN:** ovaj test je RED dok Dev ne wire-uje `blog:detail` (NoReverseMatch dotle) — to je deo kontrakta.

---

## 8. RED-phase očekivanje

Pre Dev GREEN: `apps/blog/views.py`/`urls.py`/`templates/blog/` NE postoje; `blog:index`/`blog:detail` nisu registrovani.
NOVI 5-2 testovi MORAJU pasti/error-ovati: `NoReverseMatch` (blog:index/blog:detail), `TemplateDoesNotExist`,
404/200 mismatch. `test_get_absolute_url.py` (EDIT) je RED dok Dev ne registruje URL. Ostali 5-1 testovi
(models/manager/translation/migration/admin/scaffold) MORAJU ostati zeleni. Collection NE sme abort-ovati
(guard-ovani importi UNUTAR funkcija).
