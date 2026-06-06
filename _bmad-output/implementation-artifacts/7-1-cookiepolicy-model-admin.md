---
story_id: "7.1"
story-key: 7-1-cookiepolicy-model-admin
title: CookiePolicy Model + Admin
status: ready-for-dev
epic: 7
epic_num: 7
epic_title: GDPR & Privacy
module: gdpr
created: 2026-06-06
last_modified: 2026-06-06
complexity: M
author: Mihas (SM autonomous; PRVA story Epic 7 — GDPR & Privacy. NOVI app `apps/gdpr/` (mirror apps/blog 5-1 + apps/seo 6-1 scaffolding: AppConfig name="apps.gdpr" + INSTALLED_APPS reg POSLE modeltranslation + domain app-ova). JEDAN model — `CookiePolicy` (nasleđuje TimestampedModel; SINGLETON mirror apps/pages SiteSettings 3-4: save() pk=1 + load() get_or_create(pk=1) + delete() RAISE PermissionDenied; `title`/`body` translatable → `_sr/_hu/_en`; body=plain TextField rendered |linebreaks autoescape NIKAD |safe — XSS granica mirror blog 5-3 SM-D1; effective_date editable DateField = AC „last_updated" pravni datum, ODVOJENO od TimestampedModel.updated_at; get_absolute_url=reverse('gdpr:cookie_policy') za 7.2 banner+7.4+SeoMeta link). `apps/gdpr/translation.py` registruje title/body. `apps/gdpr/admin.py:CookiePolicyAdmin(TranslationAdmin)` singleton-friendly (has_add/has_delete_permission=False + changelist_view redirect na change jedinog reda — mirror SiteSettingsAdmin). `apps/gdpr/views.py:CookiePolicyView` (TemplateView, get_context_data → CookiePolicy.load()) + `apps/gdpr/urls.py` (app_name="gdpr", path="politika-kolacica/" name="cookie_policy") mount-ovan u config/urls.py i18n_patterns → /sr/politika-kolacica/. `templates/gdpr/cookie_policy.html` extends base.html (title/body |linebreaks). 2 migracije: 0001_initial CreateModel CookiePolicy (_sr/_hu/_en kolone) + 0002 data migracija RunPython (reversible) seed Lorem Ipsum singleton pre prvog deploy-a (SM-D5 — data migracija NE fixture: pouzdano „postoji pre prvog deploy-a"). RISK TIER: MEDIUM — NOVI app + CreateModel schema migracija (_sr/_hu/_en) + body XSS render granica (legalni dokument editorom kontrolisan — plain |linebreaks autoescape) + data-migracija seed (forward+reverse) + JAVNA strana (/sr/politika-kolacica/). NEMA forme/HTMX/upload/eksternog/auth.)
depends_on:
  - 1-2-multi-environment-settings-split-sa-django-environ  # INSTALLED_APPS (modeltranslation reg order); LANGUAGES/MODELTRANSLATION_FALLBACK_LANGUAGES (_sr/_hu/_en suffix + sr fallback)
  - 1-4-i18n-setup-sa-locale-url-routing-i-switcher          # i18n_patterns (/sr/politika-kolacica/ dobija locale prefiks); set_language switcher
  - 2-1-brand-series-category-subcategory-modeli             # apps.core.TimestampedModel REUSE PATTERN; translation.py PATTERN
  - 3-4-sitesettings-model-inicijalni-admin                  # SINGLETON PATTERN (save() pk=1 + load() get_or_create + delete() RAISE + singleton admin has_add/has_delete + changelist_view redirect) — 1:1 mirror izvor
  - 5-1-blogpost-category-tag-modeli-admin-stub             # NOVI-app scaffolding PATTERN (AppConfig name="apps.gdpr" + INSTALLED_APPS); translation.py mirror; TranslationAdmin
  - 5-3-blog-post-detail-strana                              # BODY-RENDER XSS PRESEDAN (SM-D1: plain |linebreaks autoescape, DEFER WYSIWYG na Epic 8, NIKAD raw |safe)
  - 6-1-seometa-model-per-page-admin                         # get_absolute_url → SeoMeta GFK + {% seo_title/seo_head %} fallback PATTERN (CookiePolicy ima get_absolute_url → kvalifikuje se za SeoMeta inline kasnije)
---

# Story 7.1: CookiePolicy Model + Admin

Status: ready-for-dev

## Opis

As a **admin**,

I want **da uredim sadržaj politike kolačića kroz UI (NOVI `apps/gdpr/` app sa `CookiePolicy` singleton modelom — translatable `title`/`body`, pravni `effective_date`, modeltranslation `_sr/_hu/_en`, singleton-friendly admin, javna strana `/sr/politika-kolacica/`, i Lorem Ipsum seed pre prvog deploy-a)**,

so that **mogu da održavam pravni dokument bez code change-a, per locale, a stranica postoji i renderuje sadržaj odmah po deploy-u**.

Ovo je **PRVA story Epic 7 (GDPR & Privacy)** i čisti **CONTENT FOUNDATION**: TEMELJ na koji se **7.2** (GDPR baner — „Više info" link vodi na `/sr/politika-kolacica/`), **7.3** (tracking pixeli) i **7.4** (statičke privacy strane) oslanjaju. 7.1 uvodi NOVI app, jedan singleton model, translation, dve migracije (schema + data seed), singleton admin, view + URL + template.

### IN SCOPE (šta ova story isporučuje)

1. **NOVI `apps/gdpr/` app** (SM-D1) — `GdprConfig` (`name="apps.gdpr"` + `verbose_name=_("GDPR i privatnost")`) + registracija u `INSTALLED_APPS` (mirror apps/blog 5-1 + apps/seo 6-1 scaffolding).
2. **`CookiePolicy` SINGLETON model** (TimestampedModel) — `title` (CharField translatable), `body` (TextField translatable, plain-text-render SM-D3), `effective_date` (DateField, editable — pravni „važi od"; SM-D4 = AC „last_updated"). SINGLETON garancija mirror SiteSettings 3-4 (SM-D2): `save()` forsira `pk=1`, `load()` classmethod `get_or_create(pk=1)`, instance `delete()` RAISE `PermissionDenied`. `get_absolute_url()` → `reverse("gdpr:cookie_policy")` (SM-D7 — za 7.2 baner + 7.4 + budući SeoMeta link).
3. **`apps/gdpr/translation.py`** (SM-D8) — `@register(CookiePolicy)` `fields=("title", "body")`. Generiše `title_sr/_hu/_en` + `body_sr/_hu/_en` DB kolone.
4. **Schema migracija** `0001_initial` (CreateModel CookiePolicy + `_sr/_hu/_en` kolone) — manuelno reviewovana, reverzibilna. **`effective_date`/timestamp kolone su jezik-neutralne** (NISU translatable).
5. **Data seed migracija** `0002_seed_cookie_policy` (SM-D5) — `RunPython` (reverzibilan) koji kreira singleton red (pk=1) sa **Lorem Ipsum** `title_sr`/`body_sr` SAMO (sr pune dijakritike; OQ-1 RESOLVED — hu/en NE seed-uju se, oslanjaju se na `MODELTRANSLATION_FALLBACK_LANGUAGES=("sr",)` → prikazuju sr sadržaj) + `effective_date = None` (NULL — OQ-3/Adversarial #3 RESOLVED: placeholder seed NE postavlja fake/zavaravajući pravni datum; template `{% if policy.effective_date %}` guard ne prikazuje „Važi od" dok pravi admin ne postavi datum). Idempotentan kroz `get_or_create(pk=1)`. Data migracija (NE fixture) garantuje „postoji pre prvog deploy-a" jer `migrate` je deploy step (project-context.md:453).
6. **`apps/gdpr/admin.py:CookiePolicyAdmin(TranslationAdmin)`** (SM-D6) — singleton-friendly: `has_add_permission=False` kad red postoji, `has_delete_permission=False`, `changelist_view` REDIREKTUJE na change-view jedinog reda (mirror `SiteSettingsAdmin`). modeltranslation auto-rendera jezičke tabove za title/body.
7. **`apps/gdpr/views.py:CookiePolicyView`** (TemplateView, GET-only) + **`apps/gdpr/urls.py`** (`app_name="gdpr"`, `path("politika-kolacica/", ..., name="cookie_policy")`) mount-ovan u `config/urls.py` `i18n_patterns` → `/sr/politika-kolacica/`, `/hu/politika-kolacica/`, `/en/politika-kolacica/`.
8. **`templates/gdpr/cookie_policy.html`** — extends `base.html`; renderuje `title` (`<h1>`) + `body` (`|linebreaks` — XSS-safe autoescape; SM-D3) + `effective_date`.
9. **NEMA novog dep-a** (TimestampedModel/modeltranslation prisutni; body=plain TextField → NEMA bleach/nh3/WYSIWYG lib).

### OUT OF SCOPE (eksplicitno — granice)

- **GDPR baner + consent management (`apps/gdpr/templatetags/gdpr_banner.py` + `SetConsentView` + `consent_state` cookie)** = **Story 7.2** (epics.md:1009). 7.1 SAMO daje stranicu na koju baner „Više info" link vodi. 7.1 NE kreira baner ni template tag ni consent view.
- **GA4 + FB Pixel template tagovi + context_processor (`tracking.py` / `context_processors.consent_state`)** = **Story 7.3** (epics.md:1024). 7.1 NE dira tracking.
- **`Page` model + Politika privatnosti strana (`/sr/politika-privatnosti/`) + footer linkovi** = **Story 7.4** (epics.md:1037). 7.4 kreira `apps/pages/models.py:Page` (zaseban generički model) i SVOJ seed; 7.1 NE kreira Page model, NE dira footer. **Napomena (SM-D9):** 7.4 razmatra i `slug='politika-kolacica'` Page instancu — ALI 7.1 je AUTORITATIVNI izvor za politiku kolačića (dedicated CookiePolicy model + dedicated URL). 7.4 footer linkuje na POSTOJEĆU `gdpr:cookie_policy` rutu, NE duplira sadržaj.
- **⚠️ URL/route ownership granica za 7.4 (SM-D9 — eksplicitno za 7.4 dev-a):** **Story 7.4 NE SME da kreira `Page` instancu/`PageDetailView` rutu na slug-u `politika-kolacica` (`/sr/politika-kolacica/`) — taj URL je VLASNIŠTVO `gdpr:cookie_policy` (7.1).** Dupliranje rute bi izazvalo URL koliziju / dva izvora istine za isti dokument. 7.4 footer link MORA da koristi `{% url 'gdpr:cookie_policy' %}` (postojeća ruta), NE novu Page rutu na istom slug-u. (Vidi i „NETAKNUTO" tabelu — route-ownership red.)
- **WYSIWYG / rich-HTML body editor + HTML sanitizacija (bleach/nh3)** = **Epic 8.7** (blog CRUD sa WYSIWYG; isti presedan kao blog 5-3 SM-D1). 7.1 body je plain TextField, render `|linebreaks` (osnovno paragrafsko formatiranje je dovoljno za v1 legalni tekst). Headings/liste/rich-struktura = deferred 8.x.
- **SeoMeta inline na CookiePolicyAdmin / per-page SEO meta** — OPCIONO, NE u 7.1 (OQ-2). CookiePolicy IMA `get_absolute_url` → kvalifikuje se za SeoMeta GFK inline (6-1 pattern), ALI dodavanje inline-a je dodatni admin wiring; stranica i bez njega dobija `<title>`/meta kroz base.html blokove + globalni `{% seo_head %}` site-level fallback (6-3). Dokumentuj deferral.
- **Multi-singleton / više politika dokumenata** — NE. CookiePolicy je JEDAN dokument (singleton). Verzionisanje politike (audit istorija) = deferred (OQ-3).
- **Defensive validacija za nemoguće slučajeve** (project-context.md:358) — NE. Singleton garancija počiva na `save()` pk=1 + instance `delete()` raise + admin guard (mirror SiteSettings GRANICA: `QuerySet.delete()`/`loaddata`/`bulk_create` zaobilaze instance metode — to NIJE bug, to je dokumentovana granica).

### Princip

Jedan NOVI app + JEDAN SINGLETON model (`CookiePolicy`) kroz `apps.core.TimestampedModel` (REUSE) + SINGLETON pattern 1:1 mirror SiteSettings 3-4 (`save()` pk=1 + `load()` get_or_create(pk=1) + `delete()` RAISE PermissionDenied) + modeltranslation registracija (title/body → `_sr/_hu/_en`) + editable `effective_date` (pravni datum, ODVOJENO od `updated_at`) + singleton-friendly TranslationAdmin (has_add/has_delete False + changelist redirect) + GET-only TemplateView + `gdpr:cookie_policy` URL u `i18n_patterns` (`/sr/politika-kolacica/`) + template koji renderuje body `|linebreaks` (XSS-safe autoescape, NIKAD `|safe`) + dve migracije (0001 CreateModel + 0002 RunPython Lorem Ipsum seed reverzibilan). `get_absolute_url` → `reverse("gdpr:cookie_policy")` (7.2 baner + 7.4 + SeoMeta). Pune dijakritike (č/ć/ž/š/đ) u verbose_name-ovima, labelama, UI tekstu i seed sadržaju; slug `politika-kolacica` ASCII. NEMA baner/tracking/Page modela (7.2/7.3/7.4). NEMA novog dep-a. NEMA WYSIWYG (8.7). NEMA defensive validacije. NEMA premature abstrakcije.

### Strukturna arhitektura — repository delta

**NOVI app `apps/gdpr/` (10 fizičkih fajlova uklj. 2 migracije) + 1 INSTALLED_APPS EDIT + 1 config/urls.py EDIT + 1 NOVI template + 0 DELETE.**

| Path | Tip | Razlog |
|---|---|---|
| `apps/gdpr/__init__.py` | NOVO | Python package marker. |
| `apps/gdpr/apps.py` | NOVO | `class GdprConfig(AppConfig)`: `default_auto_field="django.db.models.BigAutoField"`, `name="apps.gdpr"` (sa `apps.` prefiksom — Gotcha PR-1), `verbose_name=_("GDPR i privatnost")` (mirror `apps/blog/apps.py`). |
| `apps/gdpr/models.py` | NOVO | `CookiePolicy(TimestampedModel)`: `title` (`CharField(_("Naslov"), max_length=255, blank=True)` translatable), `body` (`TextField(_("Sadržaj"), blank=True)` translatable — plain-text, render `|linebreaks` SM-D3), `effective_date` (`DateField(_("Važi od"), null=True, blank=True, help_text=_("Pravni datum stupanja na snagu. Ažurirajte ga kad menjate sadržaj politike — ne ažurira se automatski."))` SM-D4 — help_text mitigacija staleness-a, vidi Gotcha G-10). SINGLETON (SM-D2 mirror SiteSettings): `save()` forsira `pk=1` (preuzmi `created_at` na UPDATE-u — auto_now_add gotcha, vidi SiteSettings:92-120), `delete()` RAISE `PermissionDenied(_("CookiePolicy singleton ne sme da se briše."))`, `@classmethod load()` → `get_or_create(pk=1)`. `get_absolute_url()` → `reverse("gdpr:cookie_policy")` (SM-D7). `Meta.verbose_name=_("Politika kolačića")`, `verbose_name_plural=_("Politika kolačića")` (vidi STYLE napomenu uz SM-D6 — plural može da čudno čita u admin breadcrumbs, ali changelist redirect to maskira; harmless). `__str__` → `"Politika kolačića"`. `gettext_lazy as _`; import `PermissionDenied` iz `django.core.exceptions`; import `TimestampedModel` iz `apps.core.models`. (vidi AC1/AC2.) |
| `apps/gdpr/translation.py` | NOVO | `@register(CookiePolicy)` `TranslationOptions` `fields=("title", "body")` (mirror `apps/pages/translation.py` + `apps/blog/translation.py`). `effective_date`/timestamp-ovi NISU translatable. modeltranslation auto-discovery (apps.gdpr POSLE `modeltranslation`). |
| `apps/gdpr/admin.py` | NOVO | `@admin.register(CookiePolicy) class CookiePolicyAdmin(TranslationAdmin)` (SM-D6, mirror `SiteSettingsAdmin`): `list_display=("__str__", "effective_date", "updated_at")`, `has_add_permission=lambda → not CookiePolicy.objects.exists()`, `has_delete_permission → False`, `changelist_view` → `HttpResponseRedirect(reverse("admin:gdpr_cookiepolicy_change", args=[CookiePolicy.load().pk]))`. import `TranslationAdmin` iz `modeltranslation.admin`. (vidi AC6.) |
| `apps/gdpr/views.py` | NOVO | `class CookiePolicyView(TemplateView)`: `template_name="gdpr/cookie_policy.html"`, `http_method_names=["get","head","options"]` (GET-only mirror `pages.ContactView`), `get_context_data` → `context["policy"] = CookiePolicy.load()`. (vidi AC7.) |
| `apps/gdpr/urls.py` | NOVO | `app_name="gdpr"`; `urlpatterns=[path("politika-kolacica/", CookiePolicyView.as_view(), name="cookie_policy")]`. Slug `politika-kolacica` ASCII (project-context.md:165). |
| `apps/gdpr/migrations/__init__.py` | NOVO | Package marker (NOVI app). |
| `apps/gdpr/migrations/0001_initial.py` | GENERISANO + MANUAL REVIEW | `makemigrations gdpr` — `CreateModel("CookiePolicy")` + `title`/`body` + `_sr/_hu/_en` kolone (kroz translation.py) + `effective_date` + `created_at`/`updated_at`. Dev MANUELNO reviewuje (project-context.md:221). NEMA data seed ovde. |
| `apps/gdpr/migrations/0002_seed_cookie_policy.py` | NOVO (RunPython) | Data migracija (SM-D5). `forward(apps, schema_editor)`: `CookiePolicy = apps.get_model("gdpr","CookiePolicy"); CookiePolicy.objects.get_or_create(pk=1, defaults={"title_sr": ..., "body_sr": ...})` — seed-uje SAMO `title_sr`/`body_sr` (Lorem Ipsum pune dijakritike sr; OQ-1 RESOLVED — hu/en se NE seed-uju, fallback na sr) i `effective_date` se NE postavlja → ostaje `None`/NULL (Adversarial #3 RESOLVED — placeholder seed bez fake pravnog datuma; vidi Gotcha G-11). `reverse(apps, schema_editor)`: `CookiePolicy.objects.filter(pk=1).delete()` (`QuerySet.delete` — historical model NEMA instance delete() override, pa reverse radi). `dependencies=[("gdpr","0001_initial")]`. **VAŽNO (Gotcha G-2):** historical model u data migraciji NEMA `save()` pk=1 override — koristi `get_or_create(pk=1)` EKSPLICITNO sa pk u kwargs. **VAŽNO (Gotcha G-3):** popuni `_sr` kolone DIREKTNO (`title_sr`/`body_sr`), NE goli `title`/`body` (accessor; mirror brands 0003 seed komentar). |
| `templates/gdpr/cookie_policy.html` | NOVO | `{% extends "base.html" %}`; `{% load i18n %}` (OQ-4 RESOLVED — v1 koristi plain `{{ policy.title }}`, BEZ `{% translated_field %}` markera; vidi OQ-4); `{% block title %}{{ policy.title }}{% endblock %}`; `{% block content %}` → `<article>` sa `<h1>{{ policy.title }}</h1>` + `effective_date` GUARDED: `{% if policy.effective_date %}<p>{% translate "Važi od" %}: {{ policy.effective_date|date:"SHORT_DATE_FORMAT" }}</p>{% endif %}` (ne prikazuje se dok admin ne postavi datum — seed ga ostavlja None, Adversarial #3) + sekundarni „Poslednja izmena" signal: `<p class="text-muted small">{% translate "Poslednja izmena" %}: {{ policy.updated_at|date:"SHORT_DATE_FORMAT" }}</p>` (uvek prisutan auto-timestamp — mitigacija stale `effective_date`, vidi G-10) + `<div>{{ policy.body|linebreaks }}</div>`. **NIKAD `|safe` na `body`** (SM-D3 — stored-XSS granica; mirror blog post_detail.html:44-45 komentar). |
| `config/settings/base.py` | EDIT | `"apps.gdpr"` u `INSTALLED_APPS` — POSLE `modeltranslation` (translatable model; base.py:34) i POSLE domain app-ova (mirror apps.blog/apps.seo placement; SM-D1). gdpr NE importuje domain modele → može ići posle apps.seo. |
| `config/urls.py` | EDIT | Dodaj `path("", include("apps.gdpr.urls"))` u `i18n_patterns(...)` blok (mirror `apps.pages.urls` inclusion :46) → `/sr/politika-kolacica/` itd. (NE u non-prefixed blok — strana MORA biti locale-prefiksovana). |
| `apps/gdpr/tests/*` | NOVO (TEA) | RED-phase testovi (vidi Testing). `apps/gdpr/tests/__init__.py` + `conftest.py` + test fajlovi. |
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | EDIT | `7-1-cookiepolicy-model-admin` → `ready-for-dev`; `epic-7` → `in-progress` (PRVA story epika). SM handoff tracking (NIJE deliverable). |

**NETAKNUTO (regression guards):** `apps/core/models.py` (TimestampedModel REUSE — NE menja se); `apps/pages/models.py` (SiteSettings — IZVOR singleton pattern-a; NE menja se, samo se MIRROR-uje); `templates/base.html` (CookiePolicy strana KORISTI postojeće `{% block title %}`/`{% block content %}` + globalni `{% seo_head %}` site-level fallback — base.html SE NE MENJA); `apps/seo/*` (NE dodaje se SeoMeta inline u 7.1 — OQ-2); `templates/partials/footer.html` (footer linkovi = 7.4 scope, NE 7.1); `pyproject.toml` (NEMA novog dep); sve postojeće migracije (`makemigrations` mora dotaknuti SAMO `gdpr/0001` + ručno pisan `gdpr/0002` — `makemigrations --check --dry-run` posle apply potvrđuje „No changes detected" za sve ostale app-ove). **KRITIČNO:** dodavanje `apps.gdpr` ne sme generisati izmene u POSTOJEĆIM app migracijama.

**Route ownership (granica za buduće story-je — eksplicitno):**

| URL / ruta | Vlasnik | Pravilo |
|---|---|---|
| `/sr/politika-kolacica/` (`gdpr:cookie_policy`) | **Story 7.1 (gdpr.CookiePolicy)** | **Story 7.4 NE SME** da kreira `Page`/`PageDetailView` rutu na slug-u `politika-kolacica` — taj URL je vlasništvo 7.1. 7.4 footer link koristi `{% url 'gdpr:cookie_policy' %}` (postojeća ruta), NE duplira sadržaj/rutu (SM-D9). |

## Kriterijumi prihvatanja

**AC1 — `CookiePolicy` model u `apps/gdpr/models.py`; nasleđuje `TimestampedModel`; translatable title/body + effective_date; `system check` čist (SM-D1/D3/D4)**

- **Given** `apps.core.TimestampedModel` (REUSE); NOVI `apps/gdpr/` app registrovan (AC5)
- **When** kreiram `CookiePolicy(TimestampedModel)` u `apps/gdpr/models.py`
- **Then** `CookiePolicy` MORA imati TAČNO ova polja:
  - `title` — `CharField(_("Naslov"), max_length=255, blank=True)` (**translatable** — AC4)
  - `body` — `TextField(_("Sadržaj"), blank=True)` (**translatable** — AC4; plain-text, render `|linebreaks` AC7; SM-D3)
  - `effective_date` — `DateField(_("Važi od"), null=True, blank=True, help_text=_("Pravni datum stupanja na snagu. Ažurirajte ga kad menjate sadržaj politike — ne ažurira se automatski."))` (SM-D4 — pravni „last_updated"; NIJE translatable; ODVOJENO od TimestampedModel.updated_at; help_text = staleness mitigacija G-10)
  - nasleđeni `created_at`/`updated_at` iz TimestampedModel (NE redefinisati)
- **And** `Meta.verbose_name=_("Politika kolačića")`, `verbose_name_plural=_("Politika kolačića")`; `__str__` → `"Politika kolačića"`
- **And** `get_absolute_url()` → `reverse("gdpr:cookie_policy")` (SM-D7)
- **And** NEMA `clean()` defensive validacije (project-context.md:358)
- **And** `uv run python manage.py check` exit 0

**AC2 — SINGLETON garancija: `save()` pk=1 + `load()` get_or_create(pk=1) + `delete()` RAISE (SM-D2, mirror SiteSettings 3-4)**

- **Given** AC1; `apps/pages/models.py:SiteSettings` kao referentni singleton (save()/load()/delete() pattern, models.py:92-130)
- **When** koristim CookiePolicy singleton metode
- **Then**:
  - `CookiePolicy().save()` forsira `pk=1` — drugi `save()` UPDATE-uje ISTI red (NE pravi pk=2). MORA rešiti `created_at` auto_now_add gotcha na UPDATE-u (preuzmi postojeći `created_at` ili `force_insert` kad red ne postoji — KOPIRAJ SiteSettings.save() logiku models.py:92-120)
  - `CookiePolicy.load()` (classmethod) → `get_or_create(pk=1)` vraća jedinu instancu (lazy; siguran pre seed-a)
  - instance `cookie_policy.delete()` RAISE `PermissionDenied(_("CookiePolicy singleton ne sme da se briše."))`
  - **GRANICA (dokumentovana, NIJE bug — mirror SiteSettings):** instance `delete()` NE pokriva `QuerySet.delete()`/`loaddata`/`bulk_create` (zaobilaze instance metode). Singleton garancija = `save()` pk=1 + instance `delete()` raise + admin guard (AC6).
- **And** posle 2 `save()` poziva, `CookiePolicy.objects.count() == 1`
- **And** `uv run python manage.py check` exit 0

**AC3 — Dve migracije: `0001_initial` (CreateModel + `_sr/_hu/_en`) + `0002` data seed Lorem Ipsum (RunPython reverzibilan); manuelno reviewovane (SM-D5)**

- **Given** AC1, AC4 (translation registrovan); NOVI `apps/gdpr/` u INSTALLED_APPS (AC5)
- **When** pokrenem `uv run python manage.py makemigrations gdpr` (→ 0001) + ručno napišem `0002_seed_cookie_policy`
- **Then**:
  - `0001_initial.py`: `CreateModel("CookiePolicy")` sa `title`/`body` + **`title_sr/_hu/_en`, `body_sr/_hu/_en`** (modeltranslation — AC4) + `effective_date` + `created_at`/`updated_at`. NEMA data seed.
  - `0002_seed_cookie_policy.py`: `RunPython(forward, reverse)`, `dependencies=[("gdpr","0001_initial")]`. `forward` → `get_or_create(pk=1, defaults={title_sr, body_sr})` Lorem Ipsum (SAMO `_sr`, pune dijakritike — OQ-1 RESOLVED; hu/en NE seed-uju se → sr fallback); `effective_date` se NE postavlja → ostaje None/NULL (Adversarial #3 RESOLVED — bez fake pravnog datuma). `reverse` → `filter(pk=1).delete()`.
  - **`forward` popunjava `_sr` kolone DIREKTNO** (`title_sr`/`body_sr`) — historical model NEMA modeltranslation accessor fallback magic na isti način; goli `title=` bi popunio default-locale kolonu ali EKSPLICITNO postavi `title_sr`/`body_sr`/`title_hu`/`body_hu`/`title_en`/`body_en` (mirror brands 0003 seed komentar) — bar `_sr` MORA biti popunjen da fallback vrati srpski (Gotcha G-3)
  - **`forward` koristi `get_or_create(pk=1)` EKSPLICITNO** (historical model NEMA `save()` pk=1 override — Gotcha G-2)
  - **`makemigrations` ne sme dotaknuti nijednu POSTOJEĆU app migraciju** — `makemigrations --check --dry-run` posle apply → „No changes detected"
  - Dev MANUELNO reviewuje oba fajla (project-context.md:221); `migrate --plan` prikazuje plan
  - `uv run python manage.py migrate gdpr` primeni; `migrate gdpr 0001` reverzuje seed (0002 reverse delete-uje pk=1); `migrate gdpr zero` reverzuje sve čisto
- **And** posle `migrate`, `CookiePolicy.objects.filter(pk=1).exists()` je `True` (seed ga je kreirao — „postoji pre prvog deploy-a", AC epics.md:1007)
- **And** migracije + model promene commit-uju se ZAJEDNO (atomic; project-context.md:223)

**AC4 — `apps/gdpr/translation.py` registruje `title`/`body` → `_sr/_hu/_en` (SM-D8)**

- **Given** AC1; modeltranslation auto-discovery (apps.gdpr POSLE modeltranslation u INSTALLED_APPS); LANGUAGES [sr,hu,en] (base.py:148)
- **When** kreiram `apps/gdpr/translation.py` (mirror `apps/pages/translation.py`)
- **Then**:
  - `@register(CookiePolicy)` `TranslationOptions` `fields=("title", "body")`
  - modeltranslation generiše `title_sr/_hu/_en`, `body_sr/_hu/_en` → DB kolone u 0001 (AC3)
  - `effective_date`/`created_at`/`updated_at` NISU translatable
  - Pristup `policy.title` bez aktivnog language context-a → sr fallback (`MODELTRANSLATION_FALLBACK_LANGUAGES=("sr",)` base.py:157)
- **And** `uv run python manage.py check` exit 0

**AC5 — NOVI `apps/gdpr/` app scaffolding + INSTALLED_APPS registracija (SM-D1)**

- **Given** apps/blog 5-1 + apps/seo 6-1 NOVI-app PATTERN; modeltranslation reg order (base.py:34)
- **When** kreiram `apps/gdpr/` app
- **Then**:
  - `apps/gdpr/__init__.py` + `apps/gdpr/apps.py` (`class GdprConfig(AppConfig)`, `default_auto_field="django.db.models.BigAutoField"`, `name="apps.gdpr"`, `verbose_name=_("GDPR i privatnost")`) postoje (mirror `apps/blog/apps.py`)
  - `"apps.gdpr"` dodat u `INSTALLED_APPS` (config/settings/base.py) — POSLE `modeltranslation` (KRITIČNO za translatable model; base.py:34) i POSLE domain app-ova (mirror apps.blog/apps.seo; SM-D1)
  - gdpr importuje SAMO `apps.core` (TimestampedModel) + Django (`reverse`, `PermissionDenied`, generic views/admin) + modeltranslation; NE importuje domain app-ove (products/brands/blog/pages/seo)
- **And** `uv run python manage.py check` exit 0; app se pojavljuje u `manage.py showmigrations gdpr`

**AC6 — Singleton-friendly admin: per-locale edit + `has_add`/`has_delete` guard + changelist redirect (SM-D6, mirror SiteSettingsAdmin)**

- **Given** AC2 (singleton); `apps/pages/admin.py:SiteSettingsAdmin` kao referent (admin.py:19-40)
- **When** registrujem `CookiePolicyAdmin(TranslationAdmin)`
- **Then**:
  - `TranslationAdmin` (NE plain ModelAdmin) → modeltranslation auto-grupiše `title`/`body` po jeziku (sr/hu/en tabovi) umesto 6 ungrouped polja
  - `has_add_permission(request)` → `not CookiePolicy.objects.exists()` (nema „Add another" kad red postoji)
  - `has_delete_permission(request, obj=None)` → `False`
  - `changelist_view` → `HttpResponseRedirect(reverse("admin:gdpr_cookiepolicy_change", args=[CookiePolicy.load().pk]))` (singleton UX — vodi pravo na change jedinog reda; `load()` get_or_create pk=1 siguran)
  - Admin je registrovan na POSTOJEĆI `admin.site` (mount-ovan u `i18n_patterns` → stvarni URL je `/sr/admin/...`; **NAPOMENA SM-D10:** project-context.md:197 navodi `/admin-coric/`, ALI to NIJE implementirano — config/urls.py:42 koristi `admin/` u i18n_patterns; `/admin-coric/` je Epic 8.1 scope; testovi koriste `reverse("admin:gdpr_cookiepolicy_*")`, NIKAD hardkodovan slug)
- **And** admin add/change-view → 200 za superuser-a (TranslationAdmin renderuje per-locale title/body bez greške)
- **And** `run_checks()` bez admin.E* grešaka

**AC7 — Javna strana `/sr/politika-kolacica/` renderuje sadržaj iz CookiePolicy (title + body |linebreaks XSS-safe) per locale (SM-D3/D7)**

- **Given** AC2 (load()) + AC3 (seed postoji); `CookiePolicyView` + `gdpr:cookie_policy` URL u i18n_patterns
- **When** GET `/sr/politika-kolacica/`
- **Then**:
  - HTTP 200; template `gdpr/cookie_policy.html` korišćen
  - `<title>` = `policy.title` (kroz `{% block title %}`)
  - `<h1>` sadrži `policy.title`; telo sadrži `policy.body` renderovan kroz `|linebreaks`
  - **`body` se renderuje `{{ policy.body|linebreaks }}` — NIKAD `{{ policy.body|safe }}`** (SM-D3 — autoescape; `<script>` u body se ESCAPE-uje, NE izvršava; mirror blog post_detail.html:44-45)
  - `/hu/politika-kolacica/` i `/en/politika-kolacica/` → 200; pošto seed popunjava SAMO `_sr` (OQ-1 RESOLVED), hu/en prikazuju **sr fallback sadržaj** (`MODELTRANSLATION_FALLBACK_LANGUAGES=("sr",)`) dok biznis ne unese prevod kroz admin
  - `effective_date` se prikazuje SAMO ako je postavljen (`{% if policy.effective_date %}` guard) — seed ga ostavlja None pa „Važi od" NIJE prikazan na placeholder politici (Adversarial #3); sekundarni „Poslednja izmena" (`updated_at`) je UVEK prikazan (mitigacija stale effective_date — G-10)
  - GET-only: POST → HTTP 405 (`http_method_names` izostavlja `post` — mirror ContactView)
- **And** `get_absolute_url()` → `reverse("gdpr:cookie_policy")` daje aktivni-locale prefiks (`/sr/politika-kolacica/` pod sr context-om)

**AC8 — XSS granica: malicozni HTML u `body` se renderuje kao tekst, NE izvršava (SM-D3)**

- **Given** AC7; `CookiePolicy.body` koji sadrži npr. `<script>alert(1)</script>` ili `<img src=x onerror=...>`
- **When** GET strana renderuje body
- **Then**:
  - Renderovan HTML SADRŽI ESCAPE-ovan tekst (`&lt;script&gt;...`) — NE sirov `<script>` tag
  - `body` NIKAD ne prolazi kroz `|safe` filter ni `mark_safe()`
  - **Napomena:** `|linebreaks` SAM auto-escape-uje sadržaj pre dodavanja `<br>`/`<p>` (Django built-in) — to je tačno ponašanje za plain-text body (v1). Rich-HTML body (sa namernim tagovima) = Epic 8.7 (sanitizacija pipeline), NE 7.1.

## Tasks / Zadaci

- [x] **Task 1 — NOVI `apps/gdpr/` app scaffolding** (AC5)
  - [x] 1.1 Kreiraj `apps/gdpr/__init__.py` + `apps/gdpr/apps.py` (`GdprConfig`, `name="apps.gdpr"`, `verbose_name=_("GDPR i privatnost")`) — mirror `apps/blog/apps.py`
  - [x] 1.2 Kreiraj `apps/gdpr/migrations/__init__.py` (package marker)
  - [x] 1.3 Dodaj `"apps.gdpr"` u `INSTALLED_APPS` (config/settings/base.py) — POSLE modeltranslation + domain app-ova (posle apps.seo)
  - [x] 1.4 `uv run python manage.py check` exit 0

- [x] **Task 2 — `CookiePolicy` SINGLETON model** (AC1, AC2)
  - [x] 2.1 `apps/gdpr/models.py`: `CookiePolicy(TimestampedModel)` sa `title`/`body` (translatable) + `effective_date` (DateField null/blank)
  - [x] 2.2 Singleton `save()` (pk=1 + created_at auto_now_add gotcha — KOPIRAJ SiteSettings.save() models.py:92-120)
  - [x] 2.3 `delete()` RAISE PermissionDenied + `@classmethod load()` get_or_create(pk=1)
  - [x] 2.4 `get_absolute_url()` → `reverse("gdpr:cookie_policy")` + `__str__` + `Meta.verbose_name`

- [x] **Task 3 — modeltranslation registracija** (AC4)
  - [x] 3.1 `apps/gdpr/translation.py`: `@register(CookiePolicy)` `fields=("title","body")` (mirror apps/pages/translation.py)
  - [x] 3.2 `uv run python manage.py check` exit 0 (translation reg ne baca)

- [x] **Task 4 — Schema migracija `0001_initial`** (AC3)
  - [x] 4.1 `uv run python manage.py makemigrations gdpr`
  - [x] 4.2 MANUAL REVIEW: CreateModel + `title_sr/hu/en` + `body_sr/hu/en` + effective_date + timestamp-ovi; NEMA `effective_date`/timestamp _sr/hu/en (jezik-neutralni)
  - [x] 4.3 `migrate --plan` + `migrate gdpr` apply; `makemigrations --check --dry-run` → „No changes detected" za sve app-ove

- [x] **Task 5 — Data seed migracija `0002_seed_cookie_policy`** (AC3)
  - [x] 5.1 Ručno napiši `RunPython(forward, reverse)`, `dependencies=[("gdpr","0001_initial")]`
  - [x] 5.2 `forward`: `get_or_create(pk=1, defaults={title_sr, body_sr})` Lorem Ipsum (SAMO `_sr`, sr pune dijakritike — OQ-1 RESOLVED, hu/en fallback na sr); `effective_date` se NE postavlja → ostaje None (Adversarial #3, Gotcha G-11); popuni `_sr` kolone DIREKTNO (Gotcha G-3); EKSPLICITAN pk=1 (Gotcha G-2)
  - [x] 5.3 `reverse`: `filter(pk=1).delete()`
  - [x] 5.4 `migrate gdpr` (seed kreiran) + `migrate gdpr 0001` (seed obrisan) + `migrate gdpr` ponovo — reverzibilnost OK

- [x] **Task 6 — Singleton-friendly admin** (AC6)
  - [x] 6.1 `apps/gdpr/admin.py`: `@admin.register(CookiePolicy) class CookiePolicyAdmin(TranslationAdmin)` — mirror SiteSettingsAdmin
  - [x] 6.2 `has_add_permission` (not exists) + `has_delete_permission` (False) + `changelist_view` redirect na change jedinog reda (kroz `reverse`, NIKAD hardkodovan put)
  - [x] 6.3 `list_display` + verifikuj add/change-view 200 za superuser-a

- [x] **Task 7 — View + URL + config/urls.py wiring** (AC7)
  - [x] 7.1 `apps/gdpr/views.py`: `CookiePolicyView(TemplateView)` GET-only, `get_context_data` → `policy=CookiePolicy.load()`
  - [x] 7.2 `apps/gdpr/urls.py`: `app_name="gdpr"`, `path("politika-kolacica/", ..., name="cookie_policy")`
  - [x] 7.3 `config/urls.py`: `path("", include("apps.gdpr.urls"))` u i18n_patterns blok (mirror apps.pages.urls)
  - [x] 7.4 Verifikuj `/sr/`, `/hu/`, `/en/politika-kolacica/` → 200; POST → 405

- [x] **Task 8 — Template (XSS-safe body render)** (AC7, AC8)
  - [x] 8.1 `templates/gdpr/cookie_policy.html`: extends base.html; `{% block title %}{{ policy.title }}{% endblock %}`; `<h1>` + `{% if policy.effective_date %}`„Važi od"`{% endif %}` GUARD + sekundarni „Poslednja izmena" (`policy.updated_at`, uvek prikazan — G-10) + `{{ policy.body|linebreaks }}`. Plain `{{ policy.title }}` BEZ `{% translated_field %}` markera (OQ-4 RESOLVED)
  - [x] 8.2 VERIFIKUJ: NIKAD `|safe`/`mark_safe` na body (XSS granica; mirror blog post_detail.html:44-45 komentar)
  - [x] 8.3 Pune dijakritike u svim UI string-ovima (`{% translate %}`); slug `politika-kolacica` ASCII

- [x] **Task 9 — Lint + finalna verifikacija**
  - [x] 9.1 `just lint` clean (ruff + djade)
  - [x] 9.2 `just test` — gdpr testovi + broader suite GREEN (TEA piše testove RED phase pre Dev-a; Dev GREEN)

## Dev Notes

### SINGLETON pattern — KOPIRAJ SiteSettings (apps/pages/models.py:92-130)

CookiePolicy je singleton (jedan pravni dokument). MIRROR SiteSettings 1:1:
- `save()` forsira `pk=1` + rešava `created_at` auto_now_add gotcha (na UPDATE-u auto_now_add NE puni created_at → preuzmi postojeći ili `force_insert` kad red ne postoji — vidi SiteSettings.save() models.py:92-120 za TAČAN recept; ne reimplementiraj naivno `self.pk=1; super().save()` jer ruši NOT NULL na created_at).
- `load()` classmethod → `get_or_create(pk=1)` (lazy; siguran u view PRE seed-a).
- `delete()` RAISE `PermissionDenied` (NE silent no-op).
- **GRANICA (dokumentovana, NIJE bug):** `QuerySet.delete()`/`loaddata`/`bulk_create` zaobilaze instance metode — to je ista granica koju SiteSettings dokumentuje (models.py:13-16). Reverse data migracije KORISTI `QuerySet.delete()` namerno (historical model nema instance override).

### BODY XSS render — blog 5-3 SM-D1 presedan (security-critical)

`body` je plain TextField, render `{{ policy.body|linebreaks }}`. `|linebreaks` SAM auto-escape-uje (Django built-in) pre dodavanja `<p>`/`<br>` → XSS-safe za plain-text. **NIKAD `|safe`/`mark_safe`** (stored-XSS — legalni dokument editorom kontrolisan, ali admin nalog kompromitovan = injection vektor). Rich-HTML body (WYSIWYG + bleach/nh3 sanitizacija) = Epic 8.7 (isti deferral kao blog). Mirror komentar iz blog post_detail.html:44.

### get_absolute_url + forward-deps (7.2 / 7.4 / SeoMeta)

`get_absolute_url()` → `reverse("gdpr:cookie_policy")` MORA postojati u 7.1 jer:
- **7.2** GDPR baner „Više info" link → `/sr/politika-kolacica/` (epics.md:1022)
- **7.4** footer link ka politici kolačića (linkuje na POSTOJEĆU rutu, NE duplira)
- **6.1 SeoMeta** GFK + `{% seo_title policy %}` fallback duck-typing (`name`→`title`→`str`) — CookiePolicy ima `title` → fallback radi i bez eksplicitnog SeoMeta inline-a (OQ-2 deferral bezbedan)

### Data migracija (NE fixture) — „postoji pre prvog deploy-a"

AC (epics.md:1007) traži default pre prvog deploy-a. Data migracija (RunPython) je pouzdanija od fixture jer `migrate` je deploy step (project-context.md:453) — automatski se primeni; fixture bi tražio ručni `loaddata` korak. Mirror brands 0003/0004 data-migracija pattern. Reverzibilan (`reverse_code` definisan — project-context.md:227).

### Admin URL realnost (SM-D10)

config/urls.py:42 mount-uje `admin.site.urls` na `admin/` UNUTAR `i18n_patterns` → stvarni admin URL je `/sr/admin/...` (locale-prefiksovan). project-context.md:197 navodi `/admin-coric/` ALI to NIJE implementirano (Epic 8.1 scope). Admin testovi KORISTE `reverse("admin:gdpr_cookiepolicy_changelist"/"_change")`, NIKAD hardkodovan put — forward-safe kad 8.1 promeni slug.

### Project Structure Notes

- NOVI app `apps/gdpr/` prati per-app strukturu (project-context.md:103): models/admin/views/urls/translation/migrations/tests. `apps.` prefiks u AppConfig.name (Gotcha PR-1).
- INSTALLED_APPS: POSLE modeltranslation (base.py:34 — KRITIČNO za translatable model) + posle domain app-ova (gdpr nema cross-app dep → posle apps.seo bezbedno).
- URL u `i18n_patterns` (NE non-prefixed blok) — strana mora biti locale-prefiksovana; slug `politika-kolacica` ASCII (project-context.md:165).

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 7.1] (CookiePolicy title/body/last_updated + admin + translation + /sr/politika-kolacica/ + Lorem Ipsum fixture)
- [Source: apps/pages/models.py:28-131] (SiteSettings SINGLETON: save() pk=1 + created_at gotcha + load() + delete() RAISE — KOPIRAJ)
- [Source: apps/pages/admin.py:19-40] (SiteSettingsAdmin singleton-friendly: has_add/has_delete + changelist_view redirect — MIRROR)
- [Source: apps/pages/translation.py] (TranslationOptions PATTERN)
- [Source: templates/blog/post_detail.html:43-45] (body |linebreaks NIKAD |safe — XSS presedan)
- [Source: _bmad-output/implementation-artifacts/5-3-blog-post-detail-strana.md] (SM-D1 body-render XSS decision; WYSIWYG defer Epic 8.7)
- [Source: apps/blog/apps.py + _bmad-output/implementation-artifacts/5-1-*.md] (NOVI-app scaffolding PATTERN)
- [Source: _bmad-output/implementation-artifacts/6-1-seometa-model-per-page-admin.md] (NOVI-app + model + translation + migration structural mirror; SeoMeta fallback duck-typing)
- [Source: apps/brands/migrations/0003_seed_jeegee_and_prikljucna_categories.py] (data-migracija RunPython reversible + popuni _sr kolone direktno)
- [Source: config/urls.py:41-50] (i18n_patterns include pattern; admin mount realnost)
- [Source: apps/core/models.py:15-22] (TimestampedModel REUSE)
- [Source: _bmad-output/project-context.md] (i18n dijakritike, ASCII slug, migrations discipline, no User import, XSS no-|safe)

## SM Decision Log

- **SM-D1 — NOVI `apps/gdpr/` app + INSTALLED_APPS placement.** NOVI app (epics.md:1003 eksplicitno `apps/gdpr/models.py`). Scaffolding mirror apps/blog 5-1 + apps/seo 6-1. INSTALLED_APPS POSLE modeltranslation (translatable model) + posle domain app-ova (gdpr nema cross-app dep — placement posle apps.seo bezbedan, konzistentan sa redosledom).
- **SM-D2 — SINGLETON pattern = 1:1 mirror SiteSettings 3-4 (NE django-solo dep).** CookiePolicy je jedan pravni dokument → singleton. `save()` pk=1 (sa created_at auto_now_add gotcha rešenjem KOPIRANIM iz SiteSettings.save()), `load()` get_or_create(pk=1), instance `delete()` RAISE PermissionDenied. Self-rolled (NE novi dep — mirror SiteSettings SM-D2). Granica (QuerySet.delete/loaddata bypass) dokumentovana, NIJE bug.
- **SM-D3 — body = plain TextField, render `|linebreaks` autoescape, NIKAD `|safe`; WYSIWYG DEFER Epic 8.7.** Mirror blog 5-3 SM-D1. Legalni dokument editorom kontrolisan, ali admin-kompromis = stored-XSS vektor → autoescape obavezan. Osnovno paragrafsko formatiranje (|linebreaks) dovoljno za v1. Rich struktura (headings/liste/sanitizacija) deferred 8.x. NEMA bleach/nh3 dep.
- **SM-D4 — `effective_date` (editable DateField) ≠ `updated_at`.** AC traži „last_updated". Pravni „važi od" datum je SEMANTIČKI ODVOJEN od row `updated_at` (admin može da edituje copy bez menjanja pravnog datuma stupanja na snagu, i obrnuto — sitna ispravka tipfelera ne pomera „važi od"). `effective_date` je editable DateField (admin postavlja), `updated_at` ostaje auto row-timestamp. Razdvajanje je pravno korektnije; `null/blank=True` jer seed/admin može ostaviti prazno.
- **SM-D5 — Data migracija (RunPython reverzibilan) za Lorem Ipsum seed, NE fixture.** „Postoji pre prvog deploy-a" (epics.md:1007) → data migracija je pouzdanija jer `migrate` je deploy step (auto-primenjena); fixture bi tražio ručni loaddata. Mirror brands 0003/0004. ODVOJENA migracija (0002) od schema (0001) — čisto razdvajanje schema/data; idempotentna get_or_create(pk=1); reverzibilna (reverse delete pk=1).
- **SM-D6 — Singleton-friendly TranslationAdmin (mirror SiteSettingsAdmin).** `TranslationAdmin` (per-locale title/body tabovi), `has_add_permission=not exists`, `has_delete_permission=False`, `changelist_view` redirect na change jedinog reda kroz `reverse()`. Admin samo EDITUJE singleton (NE add/delete). **STYLE napomena (Adversarial #4, minor):** `verbose_name_plural` je isti string kao `verbose_name` („Politika kolačića") → admin breadcrumbs/changelist plural može da čita malo čudno; harmless jer changelist redirect maskira (vidi G-12). Opciono diferenciraj plural — NIJE obavezno.
- **SM-D7 — `get_absolute_url()` → `reverse("gdpr:cookie_policy")`.** Za 7.2 baner „Više info" + 7.4 footer + 6.1 SeoMeta GFK link. Mount u i18n_patterns daje locale-prefiks aktivne lokale.
- **SM-D8 — translation.py registruje title + body → `_sr/_hu/_en`.** Mirror apps/pages/translation.py. effective_date/timestamp-ovi jezik-neutralni (NISU translatable).
- **SM-D9 — CookiePolicy je AUTORITATIVNI izvor politike kolačića; 7.4 Page NE duplira.** 7.4 razmatra `slug='politika-kolacica'` Page instancu (epics.md:1045 „i ako treba"), ALI 7.1 daje dedicated CookiePolicy model + dedicated `gdpr:cookie_policy` rutu. 7.4 footer link ide na POSTOJEĆU rutu. Politika privatnosti (zaseban dokument) = 7.4 Page model. Granica jasna: kolačići → gdpr.CookiePolicy (7.1); privatnost → pages.Page (7.4).
- **SM-D10 — Admin URL = realni `/sr/admin/` (NE `/admin-coric/`).** project-context.md:197 navodi `/admin-coric/` ali config/urls.py:42 koristi `admin/` u i18n_patterns; `/admin-coric/` je Epic 8.1. Admin testovi koriste `reverse("admin:gdpr_cookiepolicy_*")` (forward-safe).

## Gotchas

- **G-1 (AppConfig.name prefiks):** `name="apps.gdpr"` SA `apps.` prefiksom (mirror Gotcha PR-1 / apps/blog/apps.py:16) — bez prefiksa modeltranslation auto-discovery + INSTALLED_APPS reg lome.
- **G-2 (data migracija — historical model NEMA singleton save()):** `0002` `forward` koristi historical model (`apps.get_model`) koji NEMA `save()` pk=1 override → MORA `get_or_create(pk=1, defaults={...})` sa EKSPLICITNIM pk=1 u kwargs. Naivni `CookiePolicy().save()` u migraciji NE bi forsirao pk=1.
- **G-3 (seed MORA popuniti `_sr` kolone direktno):** `forward` postavlja `title_sr`/`body_sr` (+ opciono hu/en) EKSPLICITNO. modeltranslation accessor `title` u historical kontekstu nije pouzdan; bar `_sr` MORA biti popunjen da fallback (MODELTRANSLATION_FALLBACK_LANGUAGES=("sr",)) vrati srpski. Mirror brands 0003 seed komentar (migrations/0003:10-12).
- **G-4 (created_at auto_now_add na singleton UPDATE-u):** `save()` pk=1 ide u UPDATE put (pk je set), ali `created_at` (auto_now_add) puni se SAMO na INSERT → na UPDATE-u ostaje None → ruši NOT NULL. KOPIRAJ SiteSettings.save() logiku (preuzmi postojeći created_at ili force_insert kad red ne postoji; models.py:92-120). NE reimplementiraj naivno.
- **G-5 (URL u i18n_patterns, NE non-prefixed):** `path("", include("apps.gdpr.urls"))` ide u `i18n_patterns(...)` blok (config/urls.py:41-50), NE u non-prefixed listu (gde su sitemap.xml/robots.txt). Strana mora biti `/sr/`-prefiksovana.
- **G-6 (slug ASCII):** `politika-kolacica` (NE `politika-kolačića`) — ASCII u URL-u (project-context.md:165). UI tekst (title/body/labele) = pune dijakritike.
- **G-7 (body |linebreaks NIKAD |safe):** stored-XSS granica (SM-D3). `|linebreaks` auto-escape-uje; `|safe` bi izložio sirov body. Mirror blog post_detail.html:44.
- **G-8 (makemigrations ne sme dotaknuti druge app-ove):** posle `makemigrations gdpr` pokreni `makemigrations --check --dry-run` → „No changes detected" za sve ostale app-ove (apps.gdpr je izolovan, ne menja postojeće modele).
- **G-9 (modeltranslation reg PRE makemigrations):** `translation.py` MORA postojati PRE `makemigrations gdpr` da `_sr/_hu/_en` kolone uđu u 0001_initial (mirror apps/pages/translation.py:6-10 napomena).
- **G-10 (effective_date staleness hazard):** `effective_date` je editable i ODVOJEN od auto `updated_at` (SM-D4) — admin može da edituje `body` a ZABORAVI da pomeri `effective_date` → korisnici vide STARI pravni datum. Mitigacije (sve tri primenjene): (a) `help_text` na polju podseća admina da ažurira datum (G-10 = AC1); (b) template prikazuje `updated_at` kao sekundarni „Poslednja izmena" signal (uvek tačan auto-timestamp); (c) ova Gotcha dokumentuje hazard. `effective_date` OSTAJE editable (pravni „važi od" je semantički odvojen — sitan typo fix ne pomera datum stupanja na snagu).
- **G-11 (seed effective_date = None, NE fake datum):** `0002` seed NE postavlja `effective_date` → ostaje None/NULL. Placeholder politika NE sme da prikaže zavaravajući/lažan pravni datum (Adversarial #3). Template `{% if policy.effective_date %}` guard ne prikazuje „Važi od" dok pravi admin ne unese stvarni datum. (Sekundarni „Poslednja izmena"/`updated_at` se i dalje prikazuje — to je tačan tehnički timestamp seed-a, ne pravna tvrdnja.)
- **G-12 (STYLE — verbose_name_plural breadcrumb):** `verbose_name`="Politika kolačića" / `verbose_name_plural`="Politika kolačića" → u admin breadcrumbs/changelist naslovu plural može da čita malo čudno (isti string kao singular). Harmless: singleton `changelist_view` redirect (AC6) maskira changelist pa korisnik retko vidi plural. Opciono se može diferencirati plural (npr. „Politike kolačića") — minorno, NIJE obavezno; ostaviti isto je prihvatljivo.

## Open Questions

- **⚠️ RISK-1 / OQ-LEGAL — Pravna adekvatnost plain-text `body` zahteva STAKEHOLDER (Mihas) sign-off (HIGH):** Realna politika kolačića pravno često traži **tabelu kolačića** (ime / svrha / provajder / trajanje) + **linkove ka procesorima** (GA4, Facebook). ALI v1 `body` je plain TextField rendovan `|linebreaks` koji **ESCAPE-uje HTML** → admin u v1 NE MOŽE da unese tabele/liste/linkove. Ovo je dokument koji grounduje ceo GDPR epic (7.3 nabraja baš te kolačiće). **Ovo NIJE silent deferral — eksplicitno traži sign-off pre/tokom Epic 7.** Opcije:
  - **Opcija A (PREPORUKA za konzistentnost, trenutna v1 odluka):** prihvati plain-text v1 (`|linebreaks`, BEZ novog dep-a — isti presedan kao blog 5-3 SM-D1) + dodaj rich-text/tabelu u **Epic 8.7** (WYSIWYG + bleach/nh3 sanitizacija). Mihas potpisuje da je plain-text legalno DOVOLJAN za v1 lansiranje (npr. opisni paragraf + URL-ovi kao goli tekst).
  - **Opcija B:** povuci unapred SADA sanitizovan safe-HTML podskup (tabele/liste/linkovi) — **zahteva NOVI dep (bleach/nh3)** + sanitizacioni pipeline; menja SM-D3 odluku i risk tier.
  - **AKCIJA:** Mihas mora da odluči A ili B PRE produkcionog lansiranja GDPR epika. 7.1 implementacija ostaje Opcija A (plain-text) dok sign-off ne kaže drugačije — `body` render i dep se NE menjaju u 7.1 ovim OQ-om; ovo je dokumentovani rizik za odluku, NE promena implementacije.
- **OQ-1 — Lorem Ipsum seed sadržaj jezici → RESOLVED:** Seed popunjava **SAMO `_sr`** (`title_sr`/`body_sr` — fallback baza). hu/en kolone se NE seed-uju → `/hu/` i `/en/` prikazuju sr sadržaj kroz `MODELTRANSLATION_FALLBACK_LANGUAGES=("sr",)`. (RESOLVED: sr-only seed + fallback; jednostavnije od dupliranog placeholder-a u 3 jezika; biznis unosi prave prevode kroz admin. Test `test_per_locale_hu_en` asertuje da GET `/hu/politika-kolacica/` renderuje sr fallback sadržaj.)
- **OQ-2 — SeoMeta inline na CookiePolicyAdmin:** CookiePolicy ima `get_absolute_url` → kvalifikuje se za 6-1 SeoMeta GFK inline. Dodati `inlines=[SeoMetaInline]` u 7.1 ILI defer? PREDLOG: DEFER (stranica dobija `<title>`/meta kroz base.html blokove + globalni `{% seo_head %}` site-level fallback; SeoMeta inline je polish — Epic 8 ili kad biznis traži custom SEO meta za ovu stranicu). Ako TEA/Step-02 smatra da treba — aditivno, mirror 6-1 wiring.
- **OQ-3 — Verzionisanje politike (audit istorija):** Pravni dokumenti ponekad traže istoriju verzija (kad se šta menjalo). 7.1 je singleton (jedna verzija). Verzionisanje = deferred (YAGNI v1; dodati zaseban model ako legal traži audit trail).
- **OQ-4 — `{% translated_field %}` i18n-fallback marker na title (6-5) → RESOLVED (defer marker):** v1 renderuje plain `{{ policy.title }}` BEZ `{% translated_field %}` markera. Cela strana je jedan fallback dokument (sr-only seed) → per-field ⓘ marker bi bio buka; fallback je očekivan dok biznis ne prevede. Per-field marker = deferred. (RESOLVED: plain title render, defer marker — eliminiše dev coin-flip.)

## Testing

**TEA piše testove (RED phase) PRE Dev implementacije (project-context.md:294). Dev NIKAD ne piše testove.** pytest-django; `@pytest.mark.django_db`.

### Model (apps/gdpr/tests/test_models.py)
- `test_cookie_policy_inherits_timestamped` — ima created_at/updated_at
- `test_singleton_save_forces_pk_1` — `CookiePolicy().save()` → pk==1
- `test_singleton_second_save_updates_same_row` — 2× save() → count()==1, isti pk
- `test_singleton_created_at_preserved_on_update` — created_at NE None posle UPDATE-a (auto_now_add gotcha — G-4)
- `test_load_returns_single_instance` — `load()` get_or_create pk=1; 2× load() → ista instanca, count()==1
- `test_load_safe_before_seed` — `load()` na praznoj tabeli kreira `pk == 1` i `title_sr == ""` (blank, NE crash; asertuj pk i blank title eksplicitno)
- `test_instance_delete_raises_permission_denied` — `policy.delete()` → PermissionDenied
- `test_effective_date_editable_separate_from_updated_at` — effective_date se može setovati nezavisno; NIJE auto
- `test_get_absolute_url` — `reverse("gdpr:cookie_policy")`
- `test_str` — `"Politika kolačića"`

### Translation (apps/gdpr/tests/test_translation.py)
- `test_translated_fields_exist` — `title_sr/_hu/_en`, `body_sr/_hu/_en` postoje (hasattr)
- `test_effective_date_not_translatable` — NEMA `effective_date_sr`
- `test_per_locale_values` — setuj title_sr/title_hu/title_en, čitaj sa `translation.override`
- `test_fallback_to_sr` — title_hu prazan → `policy.title` pod hu context-om vraća title_sr

### Migracije (apps/gdpr/tests/test_migrations.py)
- `test_0001_creates_cookiepolicy_with_translated_columns` — tabela + `_sr/_hu/_en` kolone (introspection)
- `test_0002_seed_creates_singleton` — posle migrate, pk=1 postoji, title_sr/body_sr popunjeni
- `test_0002_reverse_deletes_singleton` — `migrate gdpr 0001` → pk=1 obrisan
- `test_0002_idempotent` — re-run forward NE pravi duplikat: asertuj `CookiePolicy.objects.count() == 1` I `CookiePolicy.objects.first().pk == 1` (NE samo „bez exception-a")
- `test_0002_seed_effective_date_is_none` — posle migrate, `CookiePolicy.objects.get(pk=1).effective_date is None` (seed ne postavlja fake pravni datum — G-11)
- `test_no_pending_migrations` — `makemigrations --check --dry-run` clean (G-8)

### Admin (apps/gdpr/tests/test_admin.py)
- `test_admin_registered_as_translation_admin` — CookiePolicyAdmin instanceof TranslationAdmin
- `test_has_add_permission_false_when_exists` — red postoji → add disabled; prazna tabela → enabled
- `test_has_delete_permission_false`
- `test_changelist_redirects_to_change` — GET changelist → 302 na change jedinog reda
- `test_changelist_creates_pk1_when_table_empty` — GET changelist PRE seed-a (prazna tabela) → `changelist_view` poziva `load()` koji kreira `pk=1` + redirektuje na change jedinog reda (NE crash kad red ne postoji)
- `test_change_view_200_for_superuser` — per-locale title/body render bez greške
- `test_admin_system_checks_clean` — `run_checks()` bez admin.E*

### View (apps/gdpr/tests/test_views.py)
- `test_cookie_policy_200_sr` — GET `/sr/politika-kolacica/` → 200, template `gdpr/cookie_policy.html`
- `test_renders_title_and_body` — body sadrži policy.title (h1) + policy.body
- `test_per_locale_hu_en_renders_sr_fallback` — GET `/hu/politika-kolacica/` I `/en/politika-kolacica/` → 200 I `response.content` sadrži sr seed sadržaj (`title_sr`/`body_sr`), jer seed popunjava SAMO `_sr` → fallback (OQ-1 RESOLVED)
- `test_post_returns_405` — POST → 405 (GET-only)
- `test_title_in_title_tag` — `<title>` sadrži policy.title
- `test_effective_date_hidden_when_none` — `effective_date=None` (seed default) → „Važi od" NIJE u `response.content` (`{% if %}` guard — G-11)
- `test_effective_date_rendered_when_set` — admin postavi `effective_date` → prikazan formatiran u `response.content`
- `test_updated_at_rendered_as_last_modified` — „Poslednja izmena" (`updated_at`) UVEK prisutan u `response.content` (sekundarni signal — G-10)

### XSS (apps/gdpr/tests/test_xss.py — security-critical)
- `test_body_script_escaped_not_executed` — body=`<script>alert(1)</script>`, GET strana → asertuj na RENDEROVAN `response.content`: `&lt;script&gt;` PRISUTAN I sirov `<script>` ODSUTAN (NE template-source grep — pravi render assertion)
- `test_body_img_onerror_escaped` — body=`<img src=x onerror=alert(1)>` → na `response.content` escaped (`&lt;img` prisutan, sirov `<img` odsutan)
- `test_template_renders_body_escaped_not_safe` — postavi `body` sa HTML tagom, GET strana, asertuj da `response.content` sadrži ESCAPE-ovanu verziju (NE sirov tag) → dokazuje da body ide kroz `|linebreaks` (autoescape), NE kroz `|safe` (mirror blog 5-3 lock; render-assertion, NE grep template izvora)

### i18n / dijakritike
- `test_ui_strings_use_full_diacritics` — verbose_name/labele/seed sr koriste č/ć/ž/š/đ
- `test_slug_is_ascii` — URL `/politika-kolacica/` (NE Unicode)

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
