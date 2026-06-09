# Interface Contract — Story 8.8 Statičke Strane CRUD

**Story:** `8-8-staticke-strane-crud` · **Module:** `apps/pages` · **Risk:** LOW · **Migrations:** 0

TEA-authored contract (RED phase). Dev (GREEN) MUST satisfy this exactly. This is the
SPECIFICATION the failing tests in `apps/pages/tests/test_8_8_page_admin.py` encode.

---

## Scope

8.8 upgrades the EXISTING `apps/pages/admin.py:PageAdmin` (a 7-4 stub) into a full
multi-locale CRUD admin over the generic `Page` model, reusing the 8-7 WYSIWYG hook for
`Page.body`. It is admin-only: 0 migrations, `Page.body` stays a plain `TextField`, NO
upload/MIME/bomb-guard, NO publish-gate, NO `SeoMetaInline`. The template
(`templates/pages/page-detail.html`) is NOT touched (render-time `legal_html` sanitization
already exists from 7-5).

`SiteSettingsAdmin` (same file, singleton) is UNTOUCHED — that is 8.9 scope.

---

## `PageAdmin` shape (the only deliverable)

```python
# apps/pages/admin.py

_WYSIWYG_BODY_FIELDS = ("body_sr", "body_hu", "body_en")

def _wire_wysiwyg_widgets(fields):  # mirror apps/blog/admin.py — `wysiwyg` class + data-wysiwyg
    ...

@admin.register(Page)
class PageAdmin(TranslationAdmin):           # AC1 — stays TranslationAdmin (NO SeoWarningAdminMixin)
    list_display = ("title", "slug", "updated_at")     # virtual `title` OK in list_display
    search_fields = ("title_sr", "slug")               # AC2 — REAL column (G-1 fix; was ("title","slug"))
    prepopulated_fields = {"slug": ("title",)}         # AC5 — kept (TranslationAdmin → title_sr)

    class Media:
        js = ("js/wysiwyg.js",)                         # AC3 — REUSE 8-7 GRANA B vanilla-JS

    def formfield_for_dbfield(self, db_field, request, **kwargs):  # AC3 — body_<locale> WYSIWYG hook
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        if formfield is not None and db_field.name in _WYSIWYG_BODY_FIELDS:
            _wire_wysiwyg_widgets({db_field.name: formfield})
        return formfield
```

### Contract details

| Attribute | Required value | AC | Rationale |
|---|---|---|---|
| base class | `TranslationAdmin` (NOT `SeoWarningAdminMixin`) | AC1, SM-D6 | Page has no SeoMeta GFK; keep 7-4 shape |
| `search_fields` | `("title_sr", "slug")` | AC2, SM-D4, G-1 | virtual `title` → runtime `FieldError` on changelist `?q=`; `title_sr`/`slug` are real columns |
| `list_display` | `("title", "slug", "updated_at")` (kept) | AC2 | virtual `title` is CORRECT in `list_display` (per-locale render), only WRONG in `search_fields` |
| `prepopulated_fields` | `{"slug": ("title",)}` (kept; TranslationAdmin rewrites to `title_sr`) | AC5, G-2 | add-time JS UX; uniqueness enforced server-side |
| WYSIWYG hook | `body_sr`/`body_hu`/`body_en` widgets carry `wysiwyg` class + `data-wysiwyg` attr | AC3, G-9 | body-only (NOT title); `Media.js=("js/wysiwyg.js",)` |
| `inlines` | none | SM-D6, G-3 | Page is not a SeoMeta receiver |
| `view_on_site` | default (NOT `False`) | AC7, SM-D7 | `Page.get_absolute_url`/`pages:page_detail` resolves |
| `has_add_permission` / `has_delete_permission` | NOT overridden (default `True`) | AC6, SM-D9 | Page is NOT singleton (unlike `SiteSettingsAdmin`) |
| custom form | **NO** (option A) | SM-D3 | no upload/publish-gate → no reason for `PageAdminForm`; mirror 8.5 |
| `Page.body` | stays plain `TextField` | AC10, SM-D2 | WYSIWYG is a form-widget, 0 migration |
| migrations | 0 (`makemigrations pages --check` = No changes) | AC10, SM-D1 | model untouched; epics:1161-1164 model expansions REJECTED/DEFER |
| `title_sr` | stays required (NOT relaxed) | AC9, G-6 | modeltranslation required-promotion; empty → graceful 200 form-error |

---

## WYSIWYG hook mechanism (REUSE 8-7)

- File: `static/js/wysiwyg.js` (already in repo from 8-7 GRANA B; vanilla-JS, 0 dep). DO NOT
  copy or rewrite.
- Hook: each `body_<locale>` Textarea widget gets `class` containing `wysiwyg` +
  `data-wysiwyg="true"`. Wired via `formfield_for_dbfield` so the admin-built form's
  `base_fields["body_sr"].widget` carries the marker (the assertion surface).
- Progressive enhancement: `Page.body` stays a plain `TextField`/`Textarea`; if JS fails, the
  textarea still works.
- `title` (CharField, single-line) gets NO marker (G-9).

---

## Security boundary (AC4 regression + AC12 new-surface lock)

- `templates/pages/page-detail.html:13` stays `{{ page.body|legal_html }}` (7-5 nh3 strip-not-escape).
  8.8 does NOT touch the template (SM-D5). This keeps the 7-4 lock
  `test_template_body_uses_legal_html_not_safe` green.
- AC12: the WYSIWYG editor is admin form input (UNTRUSTED — Marijana may paste HTML).
  Sanitization is at RENDER, not input. 8.8 MUST NOT introduce ANY new raw/`|safe`/`|linebreaks`
  render path for `page.body`. The ONLY render path stays the sanitized `legal_html` filter.
  Locked by a template-grep test + an end-to-end strip test against the rendered body fragment.

---

## What 8.8 does NOT do (anti-cargo-cult — G-3)

- NO `validate_image_mime` / decompression-bomb / MIME constants (no upload field on Page).
- NO `save_related` publish-gate / `QuerySet.update()` revert / `published_at` (Page is not publishable).
- NO `SeoMetaInline` / `SeoWarningAdminMixin` (Page not a SeoMeta receiver).
- NO `view_on_site = False` (Page URL resolves).
- NO `PageAdminForm` custom ModelForm (option A; no upload/gate need). If Dev nevertheless
  adds one, it MUST reuse `apps/core/admin_forms.relax_base_translation_fields` (title_sr stays
  required) — do NOT re-implement a relax shim.
- NO RBAC re-grant — `EDITOR_CONTENT_MODELS` already has `("pages","page")` (verify only).
- NO model change — `Page` model and migrations untouched.

---

## Test file

`apps/pages/tests/test_8_8_page_admin.py` — ~18 tests covering AC1-AC12. Two load-bearing
NEW locks: **AC2** (`?q=` changelist → 200 not FieldError) and **AC12** (no new unsanitized
render path for `page.body`).

interface_contract_summary:
- admin_class: `PageAdmin(TranslationAdmin)` (no mixin, no inlines)
- wysiwyg_hook: `formfield_for_dbfield` marks `body_sr/_hu/_en` widgets `wysiwyg`+`data-wysiwyg`; `Media.js=("js/wysiwyg.js",)`
- search_fields_fix: `("title","slug")` → `("title_sr","slug")`
- custom_form: no
- migrations: 0
