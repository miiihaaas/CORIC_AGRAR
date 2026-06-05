# Story 5.3 — Interface Contract (TEA RED → Dev GREEN)

**Story:** 5-3 Blog Post Detail Strana
**Phase:** RED complete — Dev implements GREEN against the signatures below.
**Principle:** 5-3 **ENRICHES** the 5-2 `BlogPostDetailView` placeholder ADDITIVELY (never rewrites). The 5-2 `test_blog_urls.py` detail tests (200 / draft-404 / future-404 / context_object_name=post / no-oracle) MUST STAY GREEN.

⚠️ NO model change, NO migration, NO new Python dep. `makemigrations --check --dry-run` MUST report "No changes detected".

---

## 1. `apps/blog/views.py` (EDIT)

### 1a. Module constant
```python
_SIMILAR_POSTS_LIMIT = 4  # epics.md:889 (2-4); mirror 2-7 _SIMILAR_PRODUCTS_LIMIT
```

### 1b. `BlogPostDetailView` — ENRICH (do NOT change model / context_object_name / template_name / draft-404)

**`get_queryset()`** — extend the 5-2 `Post.published.select_related("category")` to:
```python
def get_queryset(self):
    return Post.published.select_related("category", "author").prefetch_related("tags")
```
- `"author"` added to `select_related` (author meta render — N+1 lock).
- `"tags"` added via `prefetch_related` (tag links render — N+1 lock).
- Base stays `Post.published` (draft/future → 404; 5-2 contract).
- Test lock: `test_blog_detail_n_plus_1.py::test_detail_queryset_has_author_select_and_tags_prefetch` asserts `"author"` and `"category"` in `qs.query.select_related` and `"tags"` in `qs._prefetch_related_lookups`.

**`get_context_data(self, **kwargs)`** — NEW; must set two keys:
```python
ctx = super().get_context_data(**kwargs)
post = self.object
if post.category_id:
    similar = (
        Post.published
        .filter(category=post.category)
        .exclude(pk=post.pk)
        .select_related("category")[:_SIMILAR_POSTS_LIMIT]
    )
    ctx["similar_posts"] = list(similar)
else:
    ctx["similar_posts"] = []
ctx["share_url"] = self.request.build_absolute_uri(post.get_absolute_url())
return ctx
```
- `similar_posts`: published-only (draft-not-leaked), SAME category, exclude self, `select_related("category")`, ordered by `Meta.ordering` (newest first), bounded `[:_SIMILAR_POSTS_LIMIT]`. `post.category is None` → empty list (NO crash, NOT "all posts").
- `share_url`: absolute URL computed in the VIEW (template `{{ share_url }}`; `{{ }}` cannot pass an arg to a method — IMP-2).

### 1c. `BlogCategoryView(ListView)` — NEW (mirror `BlogIndexView`)
```python
@method_decorator(vary_on_headers("HX-Request"), name="dispatch")
class BlogCategoryView(ListView):
    model = Post
    context_object_name = "posts"
    paginate_by = _POSTS_PER_PAGE  # 10

    def get_template_names(self):
        if getattr(self.request, "htmx", False):
            return ["blog/partials/_post_results.html"]
        return ["blog/blog_archive.html"]

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.archive_object = get_object_or_404(Category, slug=kwargs["slug"])  # 404 bad slug

    def get_queryset(self):
        return Post.published.select_related("category").filter(category__slug=self.kwargs["slug"])

    def paginate_queryset(self, queryset, page_size):
        ...  # REUSE BlogIndexView Paginator.get_page() overflow override

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["archive_object"] = self.archive_object
        ctx["archive_kind"] = "category"
        ctx["count"] = ctx["paginator"].count                      # OOB aria-live
        ctx["active_filters"] = {"kategorija": self.kwargs["slug"]}  # IMP-1 — fires _blog_empty_state filter-0 branch
        return ctx
```
- 404 on non-existent category slug via `get_object_or_404(Category, slug=...)` in `setup()`.
- `active_filters={"kategorija": slug}` is LOAD-BEARING: the reused `_blog_empty_state.html` branches on `{% if active_filters.kategorija %}` → renders the archive-appropriate `data-testid="blog-empty-filter"` copy + "prikaži sve" → `blog:index`. Without it the empty state renders the wrong generic home CTA (`blog-empty-home`).

### 1d. `BlogTagView(ListView)` — NEW (mirror `BlogCategoryView`)
Same shape, except:
```python
self.archive_object = get_object_or_404(Tag, slug=kwargs["slug"])
...
def get_queryset(self):
    return (
        Post.published.select_related("category")
        .filter(tags__slug=self.kwargs["slug"])
        .distinct()   # IMP-6a — canonical M2M join-dup guard (Gotcha BL3-4)
    )
...
ctx["archive_kind"] = "tag"
ctx["active_filters"] = {"kategorija": self.kwargs["slug"]}  # IMP-1 — same empty-state mechanism
```
- `.distinct()` is REQUIRED (test: post with 2 tags filtered by 1 → appears EXACTLY once).

**Optional (SM-D9):** extract a `BlogListingMixin` (`paginate_queryset` + `get_template_names`) if the 3-copy duplication (Index+Category+Tag) feels worth it. Inline copy is acceptable. Dev decision; not blocking.

**New imports needed:** `from django.shortcuts import get_object_or_404`; `from apps.blog.models import Tag`.

---

## 2. `apps/blog/urls.py` (EDIT) — archives BEFORE catch-all (SM-D3)

```python
urlpatterns = [
    path("blog/", views.BlogIndexView.as_view(), name="index"),
    path("blog/kategorija/<slug:slug>/", views.BlogCategoryView.as_view(), name="category"),  # 5-3
    path("blog/tag/<slug:slug>/", views.BlogTagView.as_view(), name="tag"),                   # 5-3
    path("blog/<slug:slug>/", views.BlogPostDetailView.as_view(), name="detail"),  # catch-all LAST
]
```
- `reverse("blog:category", slug="x")` → `/sr/blog/kategorija/x/`; `reverse("blog:tag", slug="x")` → `/sr/blog/tag/x/`.
- Ordering is canonical hygiene (2-segment archives cannot structurally shadow the 1-segment detail; IMP-5). Post with slug exactly "kategorija"/"tag" stays reachable at 1-segment `/sr/blog/kategorija/`.
- Test lock: `resolve("/sr/blog/kategorija/x/").func.view_class is BlogCategoryView`, `…/tag/x/` → `BlogTagView`, `…/neki-post/` → `BlogPostDetailView`.

---

## 3. Templates

### 3a. `templates/blog/post_detail.html` (EDIT — placeholder → full detail)
Tests assert the following on rendered HTML / context:

| Element | Spec | Test |
|---|---|---|
| Main image | `{% if post.main_image %}{% responsive_picture post.main_image alt=post.title sizes="100vw" %}{% endif %}` (REUSE 2-3) — no crash without image | `test_detail_no_main_image_renders_without_crash` |
| Date | `{{ post.published_at|date:"SHORT_DATE_FORMAT" }}` (existing) | — |
| Author | `{% if post.author %}…{{ post.author.get_full_name|default:post.author.username }}…{% endif %}` (SM-D5/IMP-6b) — None omits line; empty name → username | `test_detail_author_none_omits_author_line`, `…_full_name`, `…_empty_name_falls_back_to_username` |
| Category link | `{% if post.category %}<a href="{% url 'blog:category' slug=post.category.slug %}">{{ post.category.name }}</a>{% endif %}` | `test_detail_renders_category_link` |
| Title | `<h1 id="blog-detail-title">{{ post.title }}</h1>` (existing) | — |
| Body | `{{ post.body|linebreaks }}` — **NEVER `|safe`** (SM-D1; XSS lock) | `test_detail_body_escapes_script_no_safe_filter` (asserts `&lt;script&gt;` present, raw `<script>` absent) |
| Tag links | `{% for tag in post.tags.all %}<a href="{% url 'blog:tag' slug=tag.slug %}">{{ tag.name }}</a>{% endfor %}` | `test_detail_renders_tag_links` |
| Similar posts | `{% if similar_posts %}{% include "blog/partials/_similar_posts.html" %}{% endif %}` | AC2 cluster |
| Social share | `{% include "blog/partials/_social_share.html" %}` | AC6 cluster |
| `{% block title %}` | `{{ post.title }} | Ćorić Agrar` (existing) | `test_meta_title_and_description_from_post` |
| `{% block meta_description %}` | `{{ post.perex|default:post.title }}` (IMP-4 — never empty) | `test_meta_description_falls_back_to_title_when_perex_empty` |
| NO Open Graph | no `property="og:` (Epic 6) | `test_meta_no_open_graph_yet` |

### 3b. `templates/blog/partials/_social_share.html` (NEW — SM-D6)
Tests assert these substrings/attributes on rendered HTML:
- Facebook: `https://www.facebook.com/sharer/sharer.php?u={{ share_url|urlencode }}` (`target="_blank" rel="noopener"`) → `facebook.com/sharer/sharer.php?u=`
- WhatsApp: `https://wa.me/?text={{ share_url|urlencode }}` (or `api.whatsapp.com/send?text=`) → `wa.me/?text=`
- Viber: `viber://forward?text={{ share_url|urlencode }}` → `viber://forward?text=`
- Copy-link: `<button data-share-copy data-copy-url="{{ share_url }}" …>` — `data-share-copy` present AND `data-copy-url="{{ share_url }}"` == context `share_url`
- `{% translate %}` aria-label/title full diacritics; `data-testid` on each button.
- Tests: `test_social_share_buttons_present_with_exact_hrefs`, `test_copy_link_carries_share_url`, `test_share_url_is_absolute_post_url`.

### 3c. `templates/blog/partials/_similar_posts.html` (NEW)
- Heading "Slične objave" + `{% for post in similar_posts %}{% include "blog/partials/_post_card.html" %}{% endfor %}` (mirror 2-7). Rendered only when `{% if similar_posts %}` (from parent).

### 3d. `templates/blog/blog_archive.html` (NEW)
- `{% extends "base.html" %}`; heading from `archive_object`/`archive_kind` ("Objave u kategoriji: <ime>" / "Objave sa tagom: <ime>") — `archive_object.name` must appear in HTML (`test_tag_archive_heading_shows_tag_name`).
- `{% include "blog/partials/_post_results.html" %}` (REUSE 5-2 grid + pagination + empty state). The empty branch renders `blog-empty-filter` because the view passes `active_filters`.
- **NO filter dropdown** — must NOT include `<select name="kategorija">` (IMP-6c; `test_category_archive_has_no_filter_dropdown`).
- `{% block title %}` / `{% block meta_description %}`.

### 3e. `static/js/blog-share-copy.js` (NEW) + `static/css/components/blog-detail.css` (NEW/EDIT)
- Copy-link: vanilla `navigator.clipboard.writeText(...)` on `[data-share-copy]`; aria-live "Link kopiran". NO jQuery.
- CSS: social-share sticky-left desktop / below-title mobile; `var(--token)`. `@import` in main.css if a new file. (No automated test asserts CSS/JS behavior in this RED batch beyond `data-share-copy` presence.)

---

## 4. body `|linebreaks`-never-`|safe` boundary (forward-note to Epic 8.7)
Body MUST render via `{{ post.body|linebreaks }}` (auto-escape — XSS-safe). When 8.7 introduces the WYSIWYG editor + sanitization, replace `|linebreaks` with a sanitized render (bleach/nh3 allowlist + `|safe`). NEVER raw `|safe` without sanitization (stored-XSS). `test_detail_body_escapes_script_no_safe_filter` permanently locks this.

---

## 5. i18n
New user-facing strings via `{% translate %}`/`{% blocktranslate %}` full diacritics ("Slične objave", "Autor", "Kategorija", "Objave u kategoriji:", "Objave sa tagom:", social-share labels, "Link kopiran"). `just messages` → sr/hu/en `.po`.
