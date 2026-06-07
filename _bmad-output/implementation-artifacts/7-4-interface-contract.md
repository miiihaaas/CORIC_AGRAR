# Story 7.4 — Interface Contract (TEA, RED phase)

**Story:** 7.4 Politika Kolačića + Politika Privatnosti Statičke Strane
**Module:** `apps/pages` (+ `templates/partials/footer.html` wiring + `config/urls.py` include reorder CRITICAL-1)
**Autoritet:** Ovaj ugovor je kanonski. Dev (GREEN faza) MORA zadovoljiti TAČNO ove potpise. TEA testovi (`apps/pages/tests/test_7_4_static_pages.py`) zaključavaju ga.

> Reconciliation SM-D1: 7.4 NE duplira politiku kolačića. `gdpr.CookiePolicy` (7-1) je AUTORITATIVAN za kolačiće. 7.4 kreira generički `Page` model + seed SAMO `politika-privatnosti`; footer linkuje `gdpr:cookie_policy` (postojeća ruta). `PageDetailView` G-1 guard baca `Http404` na slug `politika-kolacica`.

---

## 1. Model — `apps/pages/models.py` (EDIT — dodaj PORED `SiteSettings`)

```python
class Page(TimestampedModel):
    slug  = SlugField(_("Slug"), max_length=255, unique=True, db_index=True)   # ASCII; jezik-neutralan
    title = CharField(_("Naslov"), max_length=255)                             # translatable (AC4)
    body  = TextField(_("Sadržaj"), blank=True)                                # translatable (AC4); plain-text |linebreaks (AC7/AC8)
    # created_at / updated_at NASLEĐENI iz TimestampedModel (NE redefinisati)

    class Meta:
        verbose_name = _("Statička strana")
        verbose_name_plural = _("Statičke strane")
        ordering = ("title",)

    def __str__(self):
        return self.title or self.slug

    def get_absolute_url(self):
        return reverse("pages:page_detail", kwargs={"slug": self.slug})
```

- **NIJE singleton** — NEMA `save()` pk=1 / `load()` / `delete()` RAISE override (RAZLIKA od `SiteSettings`/`CookiePolicy`).
- NEMA `clean()` defensive validacije (project-context.md:358).
- `reverse` iz `django.urls`; `gettext_lazy as _`.

## 2. Translation — `apps/pages/translation.py` (EDIT — dodaj PORED `SiteSettingsTranslationOptions`)

```python
@register(Page)
class PageTranslationOptions(TranslationOptions):
    fields = ("title", "body")
```

- Generiše `title_sr/_hu/_en`, `body_sr/_hu/_en` kolone (u migraciji 0003).
- `slug`/`created_at`/`updated_at` NISU translatable.
- Fallback: `MODELTRANSLATION_FALLBACK_LANGUAGES=("sr",)` → prazno `_hu/_en` čita `_sr` (preduslov AC7).

## 3. View — `apps/pages/views.py` (EDIT — dodaj klasu)

```python
class PageDetailView(DetailView):
    model = Page
    slug_field = "slug"
    slug_url_kwarg = "slug"
    context_object_name = "page"
    template_name = "pages/page-detail.html"
    http_method_names = ["get", "head", "options"]   # GET-only → POST/PUT/DELETE = 405

    # G-1 collision guard (override get_object ILI get_queryset):
    #   ako kwargs slug == "politika-kolacica" → raise Http404 (gdpr je vlasnik)
```

- `Http404` iz `django.http`; `DetailView` iz `django.views.generic`.
- Nepostojeći slug (nema Page reda) → 404 (DetailView default).

## 4. URLs

### `apps/pages/urls.py` (EDIT — dodaj catch-all NA KRAJ)

```python
urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("o-nama/", AboutView.as_view(), name="about"),
    path("kontakt/", ContactView.as_view(), name="contact"),
    path("servis/", ServiceView.as_view(), name="service"),
    path("servis/rezervni-delovi/", PartRequestView.as_view(), name="part_request"),
    path("<slug:slug>/", PageDetailView.as_view(), name="page_detail"),   # POSLEDNJI (G-3)
]
```

- `pages:page_detail` = `<slug:slug>/` → MORA biti POSLEDNJI unutar pages `urlpatterns`.
- `reverse("pages:page_detail", kwargs={"slug": "politika-privatnosti"})` (pod sr) == `/sr/politika-privatnosti/`.

### `config/urls.py` (EDIT — CRITICAL-1 / SM-D11)

**PREMESTI** `path("", include("apps.pages.urls"))` da bude **POSLEDNJI** include u `i18n_patterns(...)` (POSLE `apps.gdpr.urls`). SAMO promena redosleda — nijedan include se ne briše/dodaje.

```python
urlpatterns += i18n_patterns(
    path("admin/", admin.site.urls),
    path("", include("apps.brands.urls")),
    path("", include("apps.products.urls")),
    path("", include("apps.search.urls")),
    path("", include("apps.forms.urls")),
    path("", include("apps.blog.urls")),
    path("", include("apps.gdpr.urls")),
    path("", include("apps.pages.urls")),   # PREMEŠTEN NA KRAJ (CRITICAL-1)
    prefix_default_language=True,
)
```

- Razlog: resolver je first-match-wins PREKO include granica; pages catch-all `<slug:slug>/` inače hvata `/sr/politika-kolacica/` (gdpr) i `/sr/blog/` (blog) → 7-1/blog TRAJNO 404.

## 5. Admin — `apps/pages/admin.py` (EDIT — dodaj PORED `SiteSettingsAdmin`)

```python
@admin.register(Page)
class PageAdmin(TranslationAdmin):
    list_display = ("title", "slug", "updated_at")
    search_fields = ("title", "slug")
    prepopulated_fields = {"slug": ("title",)}   # G-5: radi na default-locale title
    # NIJE singleton — NE override-uj has_add_permission / has_delete_permission
```

- `TranslationAdmin` (modeltranslation) — per-locale title/body tabovi auto.
- `has_add_permission`/`has_delete_permission` → True (NIJE singleton; RAZLIKA od 7-1/3-4).

## 6. Migracije — `apps/pages/migrations/`

### `0003_page.py` (GENERISANO `makemigrations pages` + MANUAL REVIEW)
- `CreateModel("Page")` sa `slug`/`title`/`body` + `title_sr/_hu/_en`, `body_sr/_hu/_en` + `created_at`/`updated_at`.
- `slug`/timestamp-ovi BEZ `_sr/hu/en`.
- `dependencies=[("pages","0002_seed_sitesettings")]`.
- NEMA data seed ovde.

### `0004_seed_privacy_policy.py` (NOVO — RunPython reverzibilan)
- `forward`: `Page.objects.get_or_create(slug="politika-privatnosti", defaults={"title_sr": "Politika privatnosti", "body_sr": _BODY_SR})`.
- Popuni `_sr` kolone DIREKTNO (historical model; G-2). Seed SAMO `_sr` (hu/en fallback; OQ-1).
- **NE seed-uje `politika-kolacica`** (SM-D1/AC2).
- **`body_sr` MORA početi PLACEHOLDER markerom** + `# TODO(RISK-1)` komentar u migraciji (G-15), npr. `_BODY_SR = "[PLACEHOLDER — pravni tekst MORA uneti biznis/pravnik pre go-live (RISK-1)]\n\n" + <Lorem Ipsum>`.
- `reverse`: `Page.objects.filter(slug="politika-privatnosti").delete()`.
- `dependencies=[("pages","0003_page")]` (uskladi sa STVARNIM imenom 0003 — G-14).
- Idempotentan (`get_or_create` na unique slug; G-8).

> `makemigrations --check --dry-run` → „No changes detected" za sve ostale app-ove (G-9).

## 7. Template — `templates/pages/page-detail.html` (NOVO)

```django
{% extends "base.html" %}
{% load i18n %}
{% block title %}{{ page.title }}{% endblock %}
{% block content %}
  <article data-testid="static-page" aria-labelledby="page-title">
    <h1 id="page-title">{{ page.title }}</h1>
    <p class="text-muted small">{% translate "Poslednja izmena" %}: {{ page.updated_at|date:"SHORT_DATE_FORMAT" }}</p>
    <div class="coric-static-page__body">{{ page.body|linebreaks }}</div>
  </article>
{% endblock content %}
```

- **NIKAD `|safe` / `mark_safe` na body** (SM-D4 — stored-XSS granica; mirror `gdpr/cookie_policy.html:15-16`).

## 8. Footer — `templates/partials/footer.html` (EDIT — pravni red, NEINVAZIVNO)

- Dodaj pravni red (npr. u `coric-footer__bottom`) sa 2 linka:
  - `<a href="{% url 'pages:page_detail' slug='politika-privatnosti' %}">{% translate "Politika privatnosti" %}</a>`
  - `<a href="{% url 'gdpr:cookie_policy' %}">{% translate "Politika kolačića" %}</a>` (POSTOJEĆA 7-1 ruta — NE `pages:page_detail` slug; G-11)
- Pune dijakritike. Ako styling → `.coric-footer__legal` BEM + `var(--...)` (G-6, NIKAD inline style).
- NE menja 4 kolone (`coric-footer__top`), `latest_blog_posts` for-loop (5-4), copyright (1-8) — G-4.
- **Šišana-latinica fix (G-13):** `"Pocetna"` → `"Početna"` (:9 aria-label); `"Sva prava zadrzana."` → `"Sva prava zadržana."` (:80 copyright); regeneriši `.po`.

---

## Sažetak (za RETURN)

| Kategorija | Vrednost |
|---|---|
| **urls** | `pages:page_detail` = `<slug:slug>/` (POSLEDNJI u pages.urls); `config/urls.py` pages-include PREMEŠTEN na KRAJ i18n_patterns (CRITICAL-1) |
| **views** | `PageDetailView(DetailView)` GET-only, slug-routed, `context_object_name="page"`, G-1 guard (`politika-kolacica` → Http404) |
| **models** | `Page(TimestampedModel)` slug/title/body, `get_absolute_url`, `__str__`=title-or-slug, NIJE singleton |
| **admin** | `PageAdmin(TranslationAdmin)` list_display/search_fields/prepopulated_fields, NIJE singleton (add+delete) |
| **migrations** | `0003_page` (CreateModel + `_sr/hu/en`); `0004_seed_privacy_policy` (RunPython reversible, SAMO privatnost, PLACEHOLDER marker) |
| **templates** | `templates/pages/page-detail.html` (NOVO, body `|linebreaks` no-`|safe`); `templates/partials/footer.html` (EDIT pravni red + G-13 fix) |
