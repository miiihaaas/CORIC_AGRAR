---
story_id: "6.3"
story-key: 6-3-robots-txt-open-graph-twitter-card-meta
title: "Interface Contract — Robots.txt + Open Graph + Twitter Card Meta"
phase: RED (TEA authored; Dev MUST satisfy)
author: TEA (Murat)
created: 2026-06-06
---

# 6.3 Interface Contract — exact signatures Dev implements (GREEN phase)

> RED tests are written and confirmed failing for the RIGHT reason (feature absent).
> This contract is the canonical surface Dev MUST implement so the RED suite goes GREEN
> without weakening any assertion. 0 migrations, 0 model changes, 0 new deps.

## 1. `apps/seo/views.py` (NEW — first view in apps.seo)

```python
from django.shortcuts import render
from django.urls import reverse


def robots_txt(request):
    sitemap_url = request.build_absolute_uri(
        reverse("django.contrib.sitemaps.views.sitemap")
    )
    return render(
        request,
        "seo/robots.txt",
        {"sitemap_url": sitemap_url},
        content_type="text/plain",
    )
```

- MUST return `Content-Type` starting with `text/plain`.
- `sitemap_url` MUST be absolute (`build_absolute_uri`) AND reverse-based (NOT hardcoded path).
- Do NOT add caching/middleware (YAGNI).

## 2. `templates/seo/robots.txt` (NEW)

```
User-agent: *
Allow: /
Disallow: */admin/
Disallow: */htmx/
Sitemap: {{ sitemap_url }}
```

- `Disallow: */admin/` glob covers `/sr/admin/` + `/hu/admin/` + `/en/admin/` (admin is under i18n_patterns). Alternative accepted by tests: 3 explicit per-locale lines (`/sr/admin/`, `/hu/admin/`, `/en/admin/`).
- `Disallow: */htmx/` glob (htmx is under i18n_patterns → `/sr/htmx/...`; root `/htmx/` would be a no-op — C3/SEO3-12).
- `Sitemap:` line MUST contain the absolute `/sitemap.xml` URL (test asserts `http://testserver/sitemap.xml`).

## 3. `config/urls.py` (EDIT — NO-PREFIX block)

```python
from apps.seo.views import robots_txt
# inside the NON-prefixed `urlpatterns` list (next to i18n/setlang + sitemap.xml):
path("robots.txt", robots_txt, name="robots_txt"),
```

- MUST be OUTSIDE `i18n_patterns` → `reverse("robots_txt") == "/robots.txt"`, and `/sr/robots.txt` → 404 (SEO3-7).

## 4. `apps/seo/templatetags/seo_meta.py` (EXTEND)

### 4a. `_canonical_url(obj, request)` helper (NEW — ARCH-3/SM-D7 extraction; canonical + og:url share)

```python
def _canonical_url(obj, request):
    if obj is None:
        return request.build_absolute_uri(request.path) if request is not None else None
    try:
        url = obj.get_absolute_url()
    except (AttributeError, NoReverseMatch):
        return None
    return request.build_absolute_uri(url) if request is not None else url
```

- Returns `None` when request absent AND obj=None, or obj has no resolvable `get_absolute_url`.

### 4b. `_og_type(obj)` helper (NEW — duck-type; SM-D5/SEO3-8)

```python
def _og_type(obj):
    return "article" if getattr(obj, "published_at", None) else "website"
```

- NO `isinstance` / NO `import Post` (low-coupling, mirror `_display_title`). `obj=None` → `"website"`.

### 4c. `seo_head(context, obj=None)` (CHANGE signature → obj-optional; EXTEND output)

Emits, in order, each via `format_html` (autoescape — SM-D8; NEVER `|safe` on raw values), joined with `\n` then `mark_safe(...)`:

| Tag | Value (obj set) | Value (obj=None, site-level) |
|---|---|---|
| `<link rel="canonical" href="{}">` | `_canonical_url(obj, request)` — **emit only when not None** | `_canonical_url(None, request)` = request path abs — emit only when not None |
| `<meta property="og:title" content="{}">` | `seo_title(context, obj)` logic (SeoMeta.meta_title OR `_display_title \| company`) | `_company_name(context)` |
| `<meta property="og:description" content="{}">` | `seo_meta_description(context, obj)` logic | `_load_site_settings(context).slogan or ""` |
| `<meta property="og:image" content="{}">` | `request.build_absolute_uri(seo.og_image.url)` if `seo and seo.og_image` ELSE `request.build_absolute_uri(static("img/og-default.jpg"))` — **ALWAYS present** | `request.build_absolute_uri(static("img/og-default.jpg"))` |
| `<meta property="og:type" content="{}">` | `_og_type(obj)` | `"website"` |
| `<meta property="og:url" content="{}">` | `_canonical_url(obj, request)` — **emit only when not None (same condition as canonical — C7)** | request path abs — emit when not None |
| `<meta property="og:site_name" content="{}">` | `_company_name(context)` | `_company_name(context)` |
| `<meta name="twitter:card" content="summary_large_image">` | static literal | static literal |
| `<meta name="twitter:title" content="{}">` | mirror og:title | mirror og:title |
| `<meta name="twitter:description" content="{}">` | mirror og:description | mirror og:description |
| `<meta name="twitter:image" content="{}">` | mirror og:image | mirror og:image |

Key rules:
- `from django.templatetags.static import static` (Python import, NOT `{% static %}`). `static()` returns relative; `request.build_absolute_uri(...)` absolutizes (SEO3-10).
- canonical `<link>` AND `og:url` are emitted TOGETHER iff `_canonical_url` is not None; otherwise BOTH skipped (C7/SEO3-5). NEVER emit empty `og:url content=""`.
- Compute title/description/image ONCE; reuse for og + twitter (SEO3-11).
- If `request is None` (isolated unit render): canonical/og:url skip; other og tags still emit; og:image may emit relative `static()` URL (no build_absolute_uri) — graceful, no 500 (Task 4.5).
- `seo_title` / `seo_meta_description` / `_resolve_seometa` / `_display_title` / `_display_description` / `_company_name` / `_load_site_settings` UNCHANGED (reuse).

## 5. `templates/base.html` (EDIT)

- Add `{% load seo_meta %}` at top (with other loads).
- Add `{% block social_meta %}{% seo_head %}{% endblock %}` in `<head>` (after `<title>` line, around `{% block extra_head %}`). Site-level OG default (obj=None) on EVERY page.
- `{% block extra_head %}` STAYS (other per-page head needs). Line-count budget: base.html stays within `40 <= n <= 80` (test_base_template length guard).

## 6. The 3 detail templates (EDIT — MOVE seo_head, DELETE+ADD, NOT just ADD — C2/SEO3-9)

For each: DELETE `{% block extra_head %}{% seo_head <obj> %}{% endblock %}` (line 8) AND ADD `{% block social_meta %}{% seo_head <obj> %}{% endblock %}`.

- `templates/products/product_detail.html`: obj = `product`
- `templates/brands/brand_detail.html`: obj = `brand`
- `templates/blog/post_detail.html`: obj = `post` (has published_at → og:type=article)

`{% block title %}{% seo_title <obj> %}` and `{% block meta_description %}{% seo_meta_description <obj> %}` blocks UNCHANGED.

## 7. `static/img/og-default.jpg` (NEW placeholder — Task 7 BLOCKING)

- Valid placeholder JPG (1200×630). MUST physically exist before ship.
- Reason (C6/SEO3-4): prod + staging use `CompressedManifestStaticFilesStorage` → `static("img/og-default.jpg")` for a missing file raises `ValueError: Missing staticfiles manifest entry` at REQUEST time → site-wide 500 on EVERY page (global social_meta). Dev/test plain storage masks this (tests pass without the file).
- GREEN verification: confirm file on disk; ideally `collectstatic --noinput` smoke under `DJANGO_SETTINGS_MODULE=config.settings.staging`.

## 8. Data the RED tests assert (per AC)

- **AC1** (`test_robots_txt.py`): 200; `text/plain`; `User-agent: *`; `Allow: /`; admin Disallow (`*/admin/` or 3 per-locale); `Sitemap:` containing `http://testserver/sitemap.xml`; `reverse("robots_txt") == "/robots.txt"`; `/sr/robots.txt` → 404.
- **AC2/AC8** (`test_open_graph.py`): detail head has og:title/description/image/type/url; og:title contains SeoMeta.meta_title when set, else contains `_display_title` (product.name); og:description contains SeoMeta.meta_description when set; og:url contains get_absolute_url path.
- **AC3** (`test_twitter_card.py`): twitter:card=`summary_large_image`; twitter:title/description/image present; twitter values mirror og values.
- **AC2/AC5** (`test_og_every_page.py`): home `/sr/` (obj=None) has og:title=company_name, og:description, og:image (og-default), og:type=`website`, og:url=current path. obj-optional every-page lock.
- **AC4** (`test_og_fallback.py`): no SeoMeta.og_image → og:image contains `og-default`; with og_image → og:image contains upload path AND NOT og-default.
- **AC6** (`test_og_no_duplicate.py`): full detail page → `count('property="og:title"')==1`, `count('rel="canonical"')==1`, `count("<title")==1`, `count('property="og:image"')==1` (product + post). NO-DUPLICATE lock.
- **AC7** (`test_og_type.py`): post→`article`; product/brand/obj=None→`website`.
- **AC9** (`test_og_security.py`): SeoMeta.meta_title/meta_description = `"><script>alert(1)</script>` → og:title/og:description content attribute is HTML-escaped (`&lt;script&gt;`); raw `<script>` NOT in head. Head-injection lock.
- **AC10 owned rewrites**: see §9.

## 9. Owned regression test rewrites (TEA, in existing files)

- `apps/blog/tests/test_blog_post_detail.py`: `test_meta_no_open_graph_yet` → `test_meta_has_open_graph` (asserts `property="og:title"` + `property="og:image"` PRESENT). RED until 6.3 OG implemented.
- `apps/seo/tests/test_seo_meta_tag.py`: `test_seo_head_no_og_image_when_unset` → `test_seo_head_og_image_falls_back_to_default` (asserts og:image PRESENT + `og-default`). `test_seo_head_emits_og_image_when_set` STRENGTHENED (`"hero" in out and "og-default" not in out`) — stays GREEN.
- `apps/seo/tests/test_head_integration.py`: `_HARNESS` updated `extra_head` → `social_meta` block. `test_canonical_present_once_in_full_head` RED until Dev adds `{% block social_meta %}` to base.html (assertion `==1` unchanged). `test_exactly_one_title_tag` + `test_exactly_one_meta_description_tag` STAY GREEN (confirmed).
