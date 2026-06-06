---
story_id: "6.4"
story-key: 6-4-redirect-manager-301
title: Redirect Manager (301) — Interface Contract (TEA canonical)
epic: 6
module: seo
phase: RED (TEA writes failing tests; Dev implements to GREEN)
author: TEA (Test Architect)
created: 2026-06-06
---

# Story 6.4 — Interface Contract (TEA canonical; Dev MUST satisfy)

This contract is the authoritative, machine-checkable surface the RED tests assert against.
Dev implements production code to make every test pass WITHOUT modifying the tests.
Derived from `6-4-redirect-manager-301.md` (ACs + Tasks + SM-D1..D9 + Gotchas SEO4-1..10).

---

## 1. Model — `apps.seo.models.Redirect(TimestampedModel)`

Added to `apps/seo/models.py` ALONGSIDE existing `SeoMeta` (SeoMeta untouched).

### Fields

| Field        | Type                               | Constraints                                  |
|--------------|------------------------------------|----------------------------------------------|
| `old_path`   | `CharField(max_length=255)`        | `unique=True`, `db_index=True`               |
| `new_path`   | `CharField(max_length=255)`        | —                                            |
| `is_active`  | `BooleanField`                     | `default=True`, `db_index=True`              |
| `created_at` | inherited `TimestampedModel`       | `auto_now_add=True`                          |
| `updated_at` | inherited `TimestampedModel`       | `auto_now=True`                              |

- Verbose labels are Serbian-with-diacritics (`_("Stari put")` / `_("Novi put")` / `_("Aktivno")`),
  but VALUES are ASCII URL paths (NOT translatable; `translation.py` UNTOUCHED — SM-D6/SEO4-5).
- `old_path`/`new_path` are `CharField` (NOT `URLField` — internal paths have no scheme/host; SEO4-6).

### Meta
- `verbose_name = _("Preusmerenje")`, `verbose_name_plural = _("Preusmerenja")`.
- `ordering = ["old_path"]`.

### `__str__`
- Returns `f"{self.old_path} → {self.new_path}"` (literal arrow `→`).

### `clean()` — open-redirect + self-loop + leading-slash guard (MANDATORY; SM-D2/AC5)
Raises `django.core.exceptions.ValidationError` keyed to the offending field:
1. **Open-redirect on `new_path`**: if NOT
   `django.utils.http.url_has_allowed_host_and_scheme(url=self.new_path, allowed_hosts=None)`
   → `ValidationError({"new_path": ...})`. Rejects absolute `http(s)://`, scheme-relative `//evil.com`,
   backslash bypass `/\evil.com`, `javascript:`, `ftp://`, encoded variants. (NO hand-rolled `startswith`.)
2. **Self-loop**: if `self.old_path == self.new_path` → `ValidationError({"new_path": ...})`.
3. **old_path leading-slash**: if `not self.old_path.startswith("/")`
   → `ValidationError({"old_path": ...})` (prevents silently-dead rule from admin typo `sr/stara/`).

### `save()` — MANDATORY override (SM-D2/SEO4-2/AC5)
```python
def save(self, *args, **kwargs):
    self.full_clean()   # enforce clean() guard on .save()/.create()/shell/migrations
    super().save(*args, **kwargs)
```
- Enforcement is NOT admin-only: programmatic `Redirect.objects.create(...)` / `.save()` with an
  invalid `new_path` MUST raise `ValidationError`.
- Known/accepted limitation: `bulk_create` bypasses `save()` (out of scope).

---

## 2. Middleware — `apps.seo.middleware.RedirectMiddleware`

NEW file `apps/seo/middleware.py`. Callable-class style:
```python
def __init__(self, get_response): self.get_response = get_response
def __call__(self, request): ...
```

### Skip BEFORE DB lookup (SM-D3/SEO4-4)
- Static/media: `request.path` starts with `/static/` or `/media/`.
- Admin: forward-safe segment-aware match. Recommended regex `^/[a-z]{2}/admin(-coric)?/`
  (covers `/sr/`, `/hu/`, `/en/` locale prefix + current `admin/` slug AND future Epic 8
  `admin-coric/` slug). NOT the brittle `'/admin/' in path` substring; NOT a hard-coded
  `/admin-coric/` prefix. Equivalent `reverse('admin:index')`-derived skip is acceptable
  if it covers both slugs and all locales.

### Lookup (SM-D4)
- Exactly ONE indexed query on a non-skipped path:
  `Redirect.objects.filter(old_path=request.path, is_active=True).first()`.
- `.first()` (NOT `.get()` — no DoesNotExist/MultipleObjectsReturned in hot path; SEO4-7).
- `None` → passthrough (`return self.get_response(request)`).

### Redirect (SM-D5)
- On match: `return HttpResponsePermanentRedirect(redirect.new_path)` — HTTP **301**,
  `Location: new_path`. 301 ONLY (no 302, no configurable type).

### Order (SM-D1/AC2)
- Registered in `settings.MIDDLEWARE` BEFORE `django.middleware.locale.LocaleMiddleware`:
  `index(RedirectMiddleware) < index(LocaleMiddleware)`.
- Concrete insertion: between `SessionMiddleware` and `LocaleMiddleware`
  (current SessionMiddleware idx 2, LocaleMiddleware idx 3 → insert at idx 3).
- Sees RAW `request.path` WITH locale prefix (`/sr/stari/`); rules are locale-specific (SM-D7).

---

## 3. Admin — `apps.seo.admin.RedirectAdmin`

`@admin.register(Redirect)` standalone `ModelAdmin` (NOT inline; does NOT use SeoWarningAdminMixin):
- `list_display = ("old_path", "new_path", "is_active", "created_at")`.
- `list_filter = ("is_active",)`.
- `search_fields = ("old_path", "new_path")`.
- `list_editable = ("is_active",)` (changelist toggle deactivation; `old_path` stays the clickable link).
- Admin ModelForm triggers `full_clean()` → `clean()` guard fires on add/edit
  (invalid `new_path` → form error, no save).

---

## 4. Migration — `apps/seo/migrations/0002_redirect.py`

- `CreateModel("Redirect", ...)`: `old_path`(CharField 255, unique, db_index),
  `new_path`(CharField 255), `is_active`(BooleanField default True, db_index),
  `created_at`(auto_now_add), `updated_at`(auto_now), `id` BigAutoField.
- `dependencies = [("seo", "0001_initial")]`.
- NO alter to SeoMeta. NO `_sr/_hu/_en` columns (Redirect not in translation.py).
- `makemigrations --check --dry-run` → "No changes detected" after commit.

---

## Out of scope (locked by story; tests do NOT assert these)
- regex/wildcard/prefix rules, 302/configurable type, `django.contrib.redirects`/sites,
  translatable paths, hit-logging, query-string match, bulk import.

## Notes for Dev
- Real admin slug is `admin/` → live path `/sr/admin/` (config/urls.py:42 under i18n_patterns).
  Skip MUST be forward-safe for BOTH `admin/` and future `admin-coric/` (Epic 8) — locked by test.
- MIDDLEWARE insertion index 3 (between SessionMiddleware @2 and LocaleMiddleware @3).
- 0 new dependencies (HttpResponsePermanentRedirect / ValidationError / url_has_allowed_host_and_scheme
  are Django core).
