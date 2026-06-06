# Story 7.1 — Interface Contract (TEA canonical)

NOVI app `apps/gdpr/` — `CookiePolicy` singleton model + translation + 2 migracije
(schema + Lorem-Ipsum seed) + singleton-friendly admin + javna strana
`/sr/politika-kolacica/`. TEA RED-phase tests u `apps/gdpr/tests/` definišu ovaj
kontrakt; Dev MORA da ga zadovolji (GREEN). Ovaj dokument je AUTORITATIVAN izvor
interfejsa — Dev ga ne re-derivira iz priče.

Refs: `7-1-cookiepolicy-model-admin.md` (AC1-AC8, SM-D1..D10, Gotcha G-1..G-12).
Mirror izvori: `apps/pages/models.py` (SiteSettings singleton), `apps/pages/admin.py`
(SiteSettingsAdmin), `apps/brands/migrations/0003_*` (RunPython seed),
`templates/blog/post_detail.html` (body |linebreaks XSS-safe).

---

## 1. Model — `apps.gdpr.models.CookiePolicy(TimestampedModel)`

| Polje | Tip | Napomena |
|---|---|---|
| `title` | `CharField(_("Naslov"), max_length=255, blank=True)` | **translatable** → `title_sr/_hu/_en` |
| `body` | `TextField(_("Sadržaj"), blank=True)` | **translatable** → `body_sr/_hu/_en`; render `\|linebreaks` (NIKAD `\|safe`) |
| `effective_date` | `DateField(_("Važi od"), null=True, blank=True, help_text=...)` | jezik-neutralan; pravni „važi od"; ODVOJEN od `updated_at`; help_text = staleness mitigacija (G-10) |
| `created_at` / `updated_at` | nasleđeni iz `TimestampedModel` | NE redefinisati |

- `Meta.verbose_name = _("Politika kolačića")`, `verbose_name_plural = _("Politika kolačića")`
- `__str__` → `"Politika kolačića"` (puni dijakritik)
- NEMA `clean()` (no defensive validacija — project-context.md:358)

### Singleton API (1:1 mirror SiteSettings — KOPIRAJ `apps/pages/models.py:92-130`)

- `save(*args, **kwargs)` — forsira `self.pk = 1`. **MORA rešiti `created_at` auto_now_add
  gotcha** (G-4): na UPDATE-u (pk postoji) preuzmi postojeći `created_at`, ukloni
  `force_insert`/`force_update`; na INSERT-u (pk ne postoji) postavi `force_insert=True` i
  ukloni `update_fields`. Naivni `self.pk=1; super().save()` ruši NOT NULL na created_at.
- `delete(*args, **kwargs)` — RAISE `PermissionDenied(_("CookiePolicy singleton ne sme da se briše."))`
- `@classmethod load(cls)` → `get_or_create(pk=1)` → vraća instancu (lazy; siguran PRE seed-a)
- `get_absolute_url()` → `reverse("gdpr:cookie_policy")` (SM-D7)
- **GRANICA (NIJE bug):** instance `delete()` NE pokriva `QuerySet.delete()`/`loaddata`/`bulk_create`.

## 2. Translation — `apps.gdpr.translation.py`

- `@register(CookiePolicy)` `TranslationOptions` `fields = ("title", "body")` (mirror `apps/pages/translation.py`)
- generiše `title_sr/_hu/_en`, `body_sr/_hu/_en` DB kolone
- `effective_date`/timestamp-ovi NISU translatable
- prazna lokala → sr fallback (`MODELTRANSLATION_FALLBACK_LANGUAGES=("sr",)`)
- **G-9:** `translation.py` MORA postojati PRE `makemigrations gdpr`

## 3. Migracije

### `0001_initial` (GENERISANO + manual review)
- `initial = True`; `CreateModel("CookiePolicy")` sa `title`/`body` + `title_sr/_hu/_en`,
  `body_sr/_hu/_en` + `effective_date` + `created_at`/`updated_at`
- `effective_date`/timestamp NEMAJU `_sr/_hu/_en` (jezik-neutralni)
- `makemigrations --check --dry-run` posle apply → „No changes detected" za SVE app-ove (G-8)

### `0002_seed_cookie_policy` (ručno, RunPython reverzibilan)
- `dependencies = [("gdpr", "0001_initial")]`
- `forward(apps, schema_editor)`: `CookiePolicy = apps.get_model("gdpr","CookiePolicy")`;
  `get_or_create(pk=1, defaults={"title_sr": <Lorem>, "body_sr": <Lorem>})` — **EKSPLICITAN
  pk=1** (G-2, historical model NEMA save() override) + **`_sr` kolone DIREKTNO** (G-3, bar
  `_sr` da fallback vrati srpski; puni dijakritik). **`effective_date` se NE postavlja → None**
  (G-11, bez fake pravnog datuma). **hu/en se NE seed-uju** (OQ-1, sr fallback).
- `reverse(apps, schema_editor)`: `CookiePolicy.objects.filter(pk=1).delete()` (QuerySet path)
- idempotentan (get_or_create) — re-run NE kreira pk=2

## 4. Admin — `apps.gdpr.admin.CookiePolicyAdmin(TranslationAdmin)` (mirror SiteSettingsAdmin)

- `@admin.register(CookiePolicy)`; `TranslationAdmin` (NE plain ModelAdmin) → per-locale
  title/body tabovi
- `list_display = ("__str__", "effective_date", "updated_at")`
- `has_add_permission(request)` → `not CookiePolicy.objects.exists()` (False kad red postoji, True kad prazno)
- `has_delete_permission(request, obj=None)` → `False`
- `changelist_view(request, extra_context=None)` →
  `HttpResponseRedirect(reverse("admin:gdpr_cookiepolicy_change", args=[CookiePolicy.load().pk]))`
  (kreira pk=1 kroz load() ako prazno, pa 302 redirect)
- admin URL realnost (SM-D10): registrovan na POSTOJEĆI `admin.site` (`/sr/admin/...`); testovi
  koriste `reverse("admin:gdpr_cookiepolicy_*")`, NIKAD hardkodovan slug

## 5. View / URL / Template

- `apps.gdpr.views.CookiePolicyView(TemplateView)`:
  - `template_name = "gdpr/cookie_policy.html"`
  - `http_method_names = ["get", "head", "options"]` (GET-only → POST 405; mirror ContactView)
  - `get_context_data` → `context["policy"] = CookiePolicy.load()`
- `apps.gdpr.urls.py`: `app_name = "gdpr"`;
  `urlpatterns = [path("politika-kolacica/", CookiePolicyView.as_view(), name="cookie_policy")]`
  (slug ASCII — G-6)
- `config/urls.py`: `path("", include("apps.gdpr.urls"))` u `i18n_patterns(...)` blok (G-5) →
  `/sr/`, `/hu/`, `/en/politika-kolacica/`
- `templates/gdpr/cookie_policy.html` (`{% extends "base.html" %}`, `{% load i18n %}`):
  - `{% block title %}{{ policy.title }}{% endblock %}`
  - `<h1>{{ policy.title }}</h1>` (plain `{{ policy.title }}`, BEZ `{% translated_field %}` markera — OQ-4)
  - `{% if policy.effective_date %}<p>{% translate "Važi od" %}: {{ policy.effective_date|date:"SHORT_DATE_FORMAT" }}</p>{% endif %}`
  - `<p class="text-muted small">{% translate "Poslednja izmena" %}: {{ policy.updated_at|date:"SHORT_DATE_FORMAT" }}</p>` (UVEK)
  - `<div>{{ policy.body|linebreaks }}</div>` — **NIKAD `|safe`/`mark_safe`** (AC8/G-7/SM-D3)

## 6. Settings / Scaffold

- `apps/gdpr/__init__.py` (postoji — TEA package marker)
- `apps/gdpr/apps.py`: `class GdprConfig(AppConfig)` — `default_auto_field="django.db.models.BigAutoField"`,
  `name="apps.gdpr"` (apps. prefiks — G-1), `verbose_name=_("GDPR i privatnost")`
- `apps/gdpr/migrations/__init__.py` (package marker)
- `config/settings/base.py`: `"apps.gdpr"` u `INSTALLED_APPS` — POSLE `modeltranslation` i POSLE
  domain app-ova (posle `apps.seo`)
- dep boundary: gdpr importuje SAMO `apps.core` + Django + modeltranslation; NE domain app-ove

## 7. Files Dev kreira / edituje

**NOVO (Dev kreira):**
- `apps/gdpr/apps.py`
- `apps/gdpr/models.py`
- `apps/gdpr/translation.py`
- `apps/gdpr/admin.py`
- `apps/gdpr/views.py`
- `apps/gdpr/urls.py`
- `apps/gdpr/migrations/__init__.py`
- `apps/gdpr/migrations/0001_initial.py` (makemigrations + manual review)
- `apps/gdpr/migrations/0002_seed_cookie_policy.py` (ručno)
- `templates/gdpr/cookie_policy.html`

**EDIT (Dev):**
- `config/settings/base.py` (`"apps.gdpr"` u INSTALLED_APPS)
- `config/urls.py` (include u i18n_patterns)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (status tracking)

**VEĆ POSTOJI (TEA):**
- `apps/gdpr/__init__.py`, `apps/gdpr/tests/__init__.py`, `apps/gdpr/tests/conftest.py`
- `apps/gdpr/tests/test_models.py`, `test_translation.py`, `test_migration.py`,
  `test_data_migration.py`, `test_admin.py`, `test_views.py`, `test_xss.py`

**NETAKNUTO (regression guards):** `apps/core/models.py`, `apps/pages/*` (mirror izvor),
`templates/base.html`, `apps/seo/*` (NE SeoMeta inline — OQ-2), `templates/partials/footer.html`
(7.4 scope), `pyproject.toml` (NEMA novog dep), sve postojeće migracije.
