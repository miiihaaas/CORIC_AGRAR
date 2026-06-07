---
story_id: "7.4"
story-key: 7-4-politika-kolacica-politika-privatnosti-staticke-strane
title: Politika Kolačića + Politika Privatnosti Statičke Strane
status: review
epic: 7
epic_num: 7
epic_title: GDPR & Privacy
module: pages (+ gdpr footer-wiring + config/urls.py include reorder CRITICAL-1)
created: 2026-06-07
last_modified: 2026-06-07
complexity: M
author: Mihas (SM autonomous; ČETVRTA i POSLEDNJA story Epic 7 — GDPR & Privacy. Reconcile epics.md 7.4 AC vs 7-1 SM-D9: epics.md traži generički `apps/pages/models.py:Page` (slug/title/body) + seed OBE strane (privatnost + „ako treba" kolačići), ALI 7-1 SM-D9 je AUTORITATIVNO odlučio da je `gdpr.CookiePolicy` (7-1) JEDINI izvor politike kolačića i da 7.4 NE SME duplirati ni sadržaj ni rutu `/sr/politika-kolacica/`. ODLUKA (SM-D1): 7.4 kreira generički `Page` model u apps/pages (NOVI model — slug/title/body translatable, plain TextField |linebreaks XSS-safe mirror CookiePolicy 7-1 + blog 5-3) + `PageDetailView` (slug-routed GET-only) + `pages:page_detail` URL u i18n_patterns; seed SAMO `slug='politika-privatnosti'` (Lorem Ipsum, _sr-only, fallback sr — mirror 7-1 0002 + pages 0002); footer (templates/partials/footer.html) dobija „pravni" red sa DVA linka: Politika privatnosti → {% url 'pages:page_detail' slug='politika-privatnosti' %} (NOVA ruta) + Politika kolačića → {% url 'gdpr:cookie_policy' %} (POSTOJEĆA 7-1 ruta — NE duplira). 1 schema migracija (0003 CreateModel Page + _sr/hu/en) + 1 data migracija (0004 RunPython reversible seed privacy Lorem) u apps/pages. RISK TIER MEDIUM — NOVI generički model + CreateModel schema migracija (_sr/hu/en) + body XSS render granica (plain |linebreaks autoescape mirror 7-1/5-3) + data-migracija seed (forward+reverse) + JAVNA slug-routed strana + footer EDIT (regression-sensitive — Story 1-8/5-4 vlasništvo). NEMA forme/HTMX/upload/eksternog/auth. ⚠️ Nasleđuje 7-1 RISK-1: plain-text body legalna adekvatnost za pravu politiku privatnosti → Mihas sign-off PRE go-live (isti otvoren rizik kao 7-1).)
depends_on:
  - 7-1-cookiepolicy-model-admin                            # SM-D9 route-ownership (gdpr:cookie_policy AUTORITATIVAN za kolačiće; 7.4 footer linkuje, NE duplira); body-XSS |linebreaks presedan; data-migracija seed (_sr-only + reverse delete) recept; get_absolute_url pattern
  - 7-2-gdpr-banner-sa-consent-management                   # baner „Više info" već linkuje gdpr:cookie_policy; 7-2 forward-dep eksplicitno navodi „7-4 (footer)"
  - 7-3-ga4-fb-pixel-template-tagovi-conditional-render     # 7-3 forward-dep eksplicitno navodi „7-4 (footer privacy linkovi)"; Epic 7 zatvara se ovom story-jem
  - 3-2-o-nama-staticka-strana                              # statička-strana render PATTERN (extends base.html, čist GET-only TemplateView) — Page strana mirror-uje
  - 3-4-sitesettings-model-inicijalni-admin                # apps/pages model + translation.py + migracija struktura (0001/0002 sequence); seed _sr-only + fallback recept (0002_seed_sitesettings)
  - 5-3-blog-post-detail-strana                            # BODY-RENDER XSS presedan (plain |linebreaks autoescape, NIKAD |safe; WYSIWYG DEFER Epic 8.7)
  - 1-4-i18n-setup-sa-locale-url-routing-i-switcher        # i18n_patterns (/sr/politika-privatnosti/ locale-prefiks)
  - 1-8-footer-komponenta                                  # footer VLASNIŠTVO (regression — 7.4 dodaje pravni red, NE lomi postojeće 4 kolone + copyright)
  - 5-4-footer-dinamicki-sadrzaj                           # footer latest_blog_posts context-processor (7.4 NE dira tu logiku — samo dodaje statički pravni red)
---

# Story 7.4: Politika Kolačića + Politika Privatnosti Statičke Strane

Status: review

## Opis

As a **posetilac**,

I want **da pristupim politici privatnosti (NOVA `/sr/politika-privatnosti/` strana kroz generički `Page` model) i politici kolačića (POSTOJEĆA `/sr/politika-kolacica/` iz 7-1), sa linkovima ka obe iz footer-a**,

so that **razumem svoja prava i lako pronađem pravne dokumente sa svake strane sajta**.

Ovo je **ČETVRTA i POSLEDNJA story Epic 7 (GDPR & Privacy)** — ona ZATVARA epik. Uvodi generički `Page` model (apps/pages) za statičke pravne/info strane, javnu slug-routed stranu politike privatnosti, Lorem Ipsum seed za privatnost, i „pravni" footer red sa linkovima ka **obe** politike (privatnost = NOVA ruta; kolačići = POSTOJEĆA `gdpr:cookie_policy` 7-1 ruta — bez dupliranja).

### ⚠️ KRITIČNA reconciliation odluka (SM-D1 — pročitaj PRE implementacije)

`epics.md` Story 7.4 AC (linije 1043–1048) traži: kreiraj `apps/pages/models.py:Page` (slug/title/body rich text) + admin + **2 default Page instance** (`slug='politika-privatnosti'` **i ako treba `'politika-kolacica'`**) + footer linkove + Lorem Ipsum seed za **obe**.

ALI **Story 7-1 SM-D9 je AUTORITATIVNO** odlučio (i to je već implementirano + done): `gdpr.CookiePolicy` (dedicated singleton model + dedicated `gdpr:cookie_policy` ruta na `/sr/politika-kolacica/`) je **JEDINI izvor istine za politiku kolačića**. 7-1 OUT-OF-SCOPE eksplicitno zabranjuje da 7.4 kreira `Page` instancu/rutu na slug-u `politika-kolacica` (URL kolizija / dva izvora istine).

**RECONCILIATION (SM-D1):** „ako treba" iz epics.md (1045) je **NE treba** — 7-1 već daje politiku kolačića. Zato 7.4:
- **KREIRA** generički `Page` model + `PageDetailView` + `pages:page_detail` slug-routed URL.
- **SEED-uje SAMO `slug='politika-privatnosti'`** (Lorem Ipsum). **NE seed-uje** `politika-kolacica` Page instancu.
- **Footer** dobija pravni red sa **2 linka**: privatnost → `{% url 'pages:page_detail' slug='politika-privatnosti' %}` (NOVA ruta); kolačići → `{% url 'gdpr:cookie_policy' %}` (POSTOJEĆA 7-1 ruta).
- **GUARD (G-1):** `PageDetailView` NE SME servirati `slug='politika-kolacica'` čak i ako bi neko ručno kreirao takav Page red (route-collision zaštita — vidi G-1).

### IN SCOPE (šta ova story isporučuje)

1. **`Page` generički model** (apps/pages/models.py; SM-D2) — nasleđuje `TimestampedModel`: `slug` (`SlugField`, unique, db_index — ASCII), `title` (CharField translatable), `body` (TextField translatable — plain-text, render `|linebreaks` XSS-safe SM-D4). `get_absolute_url()` → `reverse("pages:page_detail", kwargs={"slug": self.slug})`. `Meta.verbose_name=_("Statička strana")`. `__str__` → `self.title or self.slug`. **NIJE singleton** (više Page redova — privatnost sad, „O nama"/„Servis" CMS-ifikacija u Epic 8.8).
2. **`apps/pages/translation.py` EDIT** (SM-D6) — dodaj `@register(Page)` `fields=("title", "body")` PORED postojećeg `SiteSettings` registra. Generiše `title_sr/_hu/_en` + `body_sr/_hu/_en` kolone.
3. **Schema migracija `0003`** (CreateModel Page + `_sr/_hu/_en` kolone) — `makemigrations pages`, manuelno reviewovana. `slug`/timestamp-ovi jezik-neutralni.
4. **Data seed migracija `0004`** (RunPython reverzibilan; SM-D5) — `get_or_create(slug="politika-privatnosti", defaults={title_sr, body_sr})` Lorem Ipsum (SAMO `_sr` pune dijakritike; hu/en fallback na sr). Idempotentan. `reverse` → `filter(slug="politika-privatnosti").delete()`. Mirror 7-1 0002 + pages 0002.
5. **`apps/pages/admin.py` EDIT** (SM-D7) — `@admin.register(Page) class PageAdmin(TranslationAdmin)`: `list_display=("title", "slug", "updated_at")`, `prepopulated_fields={"slug": ("title",)}` (admin UX), `search_fields=("title", "slug")`. NIJE singleton (ima add/delete — više Page redova). Per-locale title/body tabovi auto.
6. **`apps/pages/views.py:PageDetailView` EDIT** (dodaj klasu; SM-D3) — `DetailView` (ili `TemplateView` sa `get_object`), GET-only (`http_method_names=["get","head","options"]` mirror ContactView), `slug_field="slug"`, `model=Page`, `context_object_name="page"`, `template_name="pages/page-detail.html"`. **G-1 guard:** ako `slug == "politika-kolacica"` → `Http404` (route-collision zaštita; gdpr je vlasnik).
7. **`apps/pages/urls.py` EDIT** (dodaj rutu; SM-D3) — `path("<slug:slug>/", PageDetailView.as_view(), name="page_detail")` **NA KRAJU** urlpatterns liste (catch-all slug — MORA biti POSLEDNJI UNUTAR pages.urls da ne shadow-uje `o-nama/`, `kontakt/`, `servis/` itd.; vidi G-3). **NIJE DOVOLJNO SAMO ovo** — vidi tačku 11 (config/urls.py reorder) jer je within-file ordering NEDOVOLJAN preko include granica (CRITICAL-1).
8. **`templates/pages/page-detail.html`** (NOVI) — extends `base.html`; `{% block title %}{{ page.title }}{% endblock %}`; `<h1>{{ page.title }}</h1>` + `{{ page.body|linebreaks }}` (XSS-safe; NIKAD `|safe` SM-D4) + sekundarni „Poslednja izmena" `{{ page.updated_at }}` (mirror 7-1 cookie_policy.html). Mirror `gdpr/cookie_policy.html` strukture.
9. **`templates/partials/footer.html` EDIT** (SM-D8) — dodaj „pravni" red (npr. unutar `coric-footer__bottom` pored copyright-a) sa 2 linka: `{% url 'pages:page_detail' slug='politika-privatnosti' %}` („Politika privatnosti") + `{% url 'gdpr:cookie_policy' %}` („Politika kolačića"). Pune dijakritike u link tekstu. NE dira postojeće 4 kolone ni `latest_blog_posts` logiku (5-4).
10. **NEMA novog dep-a** (TimestampedModel/modeltranslation/TranslationAdmin prisutni; body=plain TextField → NEMA bleach/nh3/WYSIWYG).
11. **`config/urls.py` EDIT (CRITICAL-1 — OBAVEZNO; SM-D11)** — **PREMESTI** `path("", include("apps.pages.urls"))` da bude **POSLEDNJI** unutar `i18n_patterns(...)` bloka (POSLE `apps.gdpr.urls` :49 i svih ostalih include-ova). Razlog: Django resolver je first-match-wins **preko svih include-ova** (top-to-bottom), pa pages catch-all `<slug:slug>/` (1-segment matcher) inače hvata `/sr/politika-kolacica/` (gdpr :49) i `/sr/blog/` (blog :48) PRE nego što se ti include-ovi uopšte dosegnu → cookie policy (7-1) i blog index postaju TRAJNO 404. Premeštanje pages include-a na KRAJ je bezbedno: pages.urls poseduje root `path("", HomeView, name="home")`, a prazan path matchuje TAČNO prazan path — nijedan drugi include (brands/products/search/forms/blog/gdpr) ne polaže pravo na goli `""` (svi definišu SAMO prefiksovane rute → verifikovano). Vidi G-3/SM-D11/AC10.

### OUT OF SCOPE (eksplicitno — granice)

- **`politika-kolacica` Page instanca / Page ruta na slug-u `politika-kolacica`** = **ZABRANJENO** (7-1 SM-D9 / SM-D1 ovde). `gdpr.CookiePolicy` (7-1) je AUTORITATIVAN; footer linkuje na `gdpr:cookie_policy`. `PageDetailView` G-1 guard baca `Http404` na taj slug.
- **Migracija `politika-kolacica` sadržaja u Page** — NE. 7-1 sadržaj ostaje u CookiePolicy. Bez dupliranja.
- **CMS-ifikacija „O nama"/„Servis"/„Kontakt" (hero_image, sections JSON, gallery M2M, TimelineEvent inline)** = **Story 8.8** (epics.md:1154 eksplicitno „Page model iz Epic 7 7.4" + dodatna polja). 7.4 daje SAMO bazni generički Page (slug/title/body). 8.8 PROŠIRUJE. 7.4 NE migrira postojeće `pages:about`/`pages:contact`/`pages:service` TemplateView-ove u Page model.
- **WYSIWYG / rich-HTML body + HTML sanitizacija (bleach/nh3)** = **Epic 8.7** (isti presedan kao blog 5-3 SM-D1 + CookiePolicy 7-1 SM-D3). 7.4 body je plain TextField, render `|linebreaks`. Headings/liste/rich-struktura = deferred 8.x. NEMA `rich text` widget-a (epics.md kaže „body rich text" ALI to je deferred 8.7 — isti reconciliation kao 7-1).
- **SeoMeta inline na PageAdmin / per-page SEO meta** — OPCIONO, NE u 7.4 (OQ-2). Page IMA `get_absolute_url` → kvalifikuje se za SeoMeta GFK inline (6-1 pattern), ALI strana i bez njega dobija `<title>`/meta kroz base.html + globalni `{% seo_head %}` site-level fallback (6-3). Deferral dokumentovan.
- **Header/navigacija linkovi ka politikama** — NE. AC traži SAMO footer linkove (epics.md:1047). Header nav = statički v1 (8.9).
- **Singleton ponašanje na Page** — NE. Page je OBIČAN model (više redova). NEMA `save()` pk=1 / `load()` / `delete()` raise (to je CookiePolicy/SiteSettings singleton recept — NE primenjuje se na generički Page).
- **Defensive validacija za nemoguće slučajeve** (project-context.md:358) — NE. G-1 slug-collision guard NIJE „defensive nad internim kodom"; to je javno-routed boundary (korisnik kontroliše `<slug>` u URL-u) → legitimna boundary validacija.

### Princip

Jedan NOVI generički model (`Page`) kroz `apps.core.TimestampedModel` (REUSE) — NIJE singleton (više pravnih/info strana) + modeltranslation registracija (title/body → `_sr/_hu/_en`, EDIT postojećeg apps/pages/translation.py) + slug-routed GET-only `PageDetailView` (mirror statička-strana pattern 3-2) sa G-1 collision guard (`politika-kolacica` → Http404, gdpr je vlasnik) + catch-all `<slug:slug>/` ruta POSLEDNJA u urls.py (G-3) + template koji renderuje body `|linebreaks` (XSS-safe autoescape, NIKAD `|safe` — mirror 7-1/5-3) + dve migracije (0003 CreateModel + 0004 RunPython Lorem seed SAMO privatnost, reverzibilan) + TranslationAdmin (NIJE singleton — ima add/delete + prepopulated slug) + footer pravni red sa 2 linka (privatnost NOVA ruta + kolačići POSTOJEĆA 7-1 ruta, BEZ dupliranja). Pune dijakritike (č/ć/ž/š/đ) u UI/seed-u; slug `politika-privatnosti` ASCII. NEMA WYSIWYG (8.7). NEMA `politika-kolacica` Page dupliranja (SM-D1/G-1). NEMA novog dep-a. NEMA singleton recepta na Page. NEMA defensive validacije osim boundary slug guard-a. ČETVRTA story ZATVARA Epic 7.

### Strukturna arhitektura — repository delta

**1 NOVI model + 1 NOVI template + 7 EDIT (models/translation/admin/views/urls u apps/pages + footer + config/urls.py) + 2 NOVE migracije + 0 DELETE.**

> ⚠️ **CRITICAL-1 (verifikovano):** Catch-all `<slug:slug>/` POSLEDNJI UNUTAR pages.urls NIJE dovoljan — Django resolver radi preko include granica. Pošto je `apps.pages.urls` uključen na config/urls.py :46 (PRE blog :48 i gdpr :49), pages catch-all bi uhvatio `/sr/politika-kolacica/` i `/sr/blog/` PRE nego što ti include-ovi budu dosegnuti → 7-1 cookie policy + blog index TRAJNO 404. REŠENJE: pages include MORA biti POSLEDNJI preko CELOG i18n_patterns bloka (SM-D11). Zato je `config/urls.py` sada EDIT (ne više NETAKNUTO).

| Path | Tip | Razlog |
|---|---|---|
| `apps/pages/models.py` | EDIT | Dodaj `class Page(TimestampedModel)` PORED postojećeg `SiteSettings`: `slug` (`SlugField(_("Slug"), max_length=255, unique=True, db_index=True)` — ASCII, project-context.md:165), `title` (`CharField(_("Naslov"), max_length=255)` translatable), `body` (`TextField(_("Sadržaj"), blank=True)` translatable — plain-text render `|linebreaks` SM-D4). `get_absolute_url()` → `reverse("pages:page_detail", kwargs={"slug": self.slug})`. `Meta.verbose_name=_("Statička strana")`, `verbose_name_plural=_("Statičke strane")`, `Meta.ordering=("title",)`. `__str__` → `self.title or self.slug`. **NIJE singleton** (NEMA save()/load()/delete() override). `gettext_lazy as _`; `reverse` iz `django.urls`. (vidi AC1.) |
| `apps/pages/translation.py` | EDIT | Dodaj `@register(Page)` `TranslationOptions` `fields=("title", "body")` PORED postojećeg `SiteSettingsTranslationOptions`. `slug`/timestamp-ovi NISU translatable (slug je ASCII jezik-neutralan; jedan slug po Page redu). import `Page` iz `apps.pages.models`. (vidi AC4.) |
| `apps/pages/admin.py` | EDIT | Dodaj `@admin.register(Page) class PageAdmin(TranslationAdmin)` PORED `SiteSettingsAdmin`: `list_display=("title", "slug", "updated_at")`, `search_fields=("title", "slug")`, `prepopulated_fields={"slug": ("title",)}` (admin UX — auto-slug iz naslova; NAPOMENA G-5: TranslationAdmin + prepopulated_fields radi na default-locale title polju). NIJE singleton (ima add/delete — više Page redova; NE override-uj has_add/has_delete). import `Page`. (vidi AC6.) |
| `apps/pages/views.py` | EDIT | Dodaj `class PageDetailView(DetailView)`: `model=Page`, `slug_field="slug"`, `slug_url_kwarg="slug"`, `context_object_name="page"`, `template_name="pages/page-detail.html"`, `http_method_names=["get","head","options"]` (GET-only mirror ContactView views.py:130). **G-1 collision guard:** override `get_object` (ili `get_queryset`) da `slug=="politika-kolacica"` → `Http404(...)` (gdpr:cookie_policy je vlasnik tog dokumenta; SM-D1). import `DetailView` iz `django.views.generic`, `Http404` iz `django.http`, `Page`. (vidi AC3/AC7.) |
| `apps/pages/urls.py` | EDIT | Dodaj `path("<slug:slug>/", PageDetailView.as_view(), name="page_detail")` **NA KRAJ** `urlpatterns` liste (POSLE `servis/rezervni-delovi/` — catch-all slug MORA biti POSLEDNJI UNUTAR fajla da ne shadow-uje statičke rute `o-nama/`/`kontakt/`/`servis/`; G-3). import `PageDetailView`. ⚠️ Within-file ordering JE NEOPHODAN ALI NE I DOVOLJAN — vidi config/urls.py red (CRITICAL-1). (vidi AC3/AC7/G-3.) |
| `config/urls.py` | EDIT (CRITICAL-1) | **PREMESTI** `path("", include("apps.pages.urls"))` (trenutno :46) da bude **POSLEDNJI** include unutar `i18n_patterns(...)` (POSLE `apps.gdpr.urls` :49). Razlog: resolver je first-match-wins PREKO include-ova; pages catch-all `<slug:slug>/` inače hvata `/sr/politika-kolacica/` (gdpr) i `/sr/blog/` (blog) PRE tih include-ova → 7-1/blog TRAJNO 404. Bezbedno: pages.urls poseduje root `path("", HomeView, name="home")` ali prazan path matchuje TAČNO prazan path; nijedan drugi include (brands/products/search/forms/blog/gdpr) ne polaže pravo na goli `""` — svi imaju SAMO prefiksovane rute (verifikovano čitanjem svake urls.py). `admin/` ostaje gde jeste (nije pri kraju, ali je eksplicitan prefiks pa nije ugrožen). (vidi AC3/AC10/G-3/SM-D11.) |
| `templates/pages/page-detail.html` | NOVO | `{% extends "base.html" %}`; `{% load i18n %}`; `{% block title %}{{ page.title }}{% endblock %}`; `{% block content %}` → `<article data-testid="static-page" aria-labelledby="page-title"><h1 id="page-title">{{ page.title }}</h1>` + `<p class="text-muted small">{% translate "Poslednja izmena" %}: {{ page.updated_at|date:"SHORT_DATE_FORMAT" }}</p>` + `<div class="coric-static-page__body">{{ page.body|linebreaks }}</div></article>`. **NIKAD `|safe` na body** (SM-D4 — stored-XSS granica; mirror gdpr/cookie_policy.html:15-16 + blog post_detail.html komentar). (vidi AC7/AC8.) |
| `apps/pages/migrations/0003_page.py` | GENERISANO + MANUAL REVIEW | `makemigrations pages` — `CreateModel("Page")` + `slug`/`title`/`body` + **`title_sr/_hu/_en`, `body_sr/_hu/_en`** (kroz translation.py — G-7 translation PRE makemigrations) + `created_at`/`updated_at`. Dev MANUELNO reviewuje (project-context.md:221). `slug`/timestamp-ovi NEMAJU `_sr/hu/en`. NEMA data seed ovde. (Stvarno ime fajla može varirati — `makemigrations` auto-imenuje; depend na `0002_seed_sitesettings`.) |
| `apps/pages/migrations/0004_seed_privacy_policy.py` | NOVO (RunPython) | Data migracija (SM-D5). `forward`: `Page = apps.get_model("pages","Page"); Page.objects.get_or_create(slug="politika-privatnosti", defaults={"title_sr": "Politika privatnosti", "body_sr": <Lorem Ipsum sr pune dijakritike>})` — seed-uje SAMO `_sr` (OQ-1 — hu/en fallback na sr; NE seed lažni prevod). `reverse`: `Page.objects.filter(slug="politika-privatnosti").delete()`. `dependencies=[("pages","0003_page")]`. **G-2:** historical model — popuni `title_sr`/`body_sr` DIREKTNO (NE goli `title`/`body` accessor; mirror pages 0002 + brands 0003). **G-8:** `get_or_create` na `slug` (unique) je idempotentan; NEMA singleton pk=1 ovde (Page nije singleton). (vidi AC5.) |
| `templates/partials/footer.html` | EDIT | Dodaj „pravni" red (npr. u `coric-footer__bottom` div pre/posle copyright `<p>`): `<ul class="coric-footer__legal">` ili inline linkovi: `<a href="{% url 'pages:page_detail' slug='politika-privatnosti' %}">{% translate "Politika privatnosti" %}</a>` + `<a href="{% url 'gdpr:cookie_policy' %}">{% translate "Politika kolačića" %}</a>`. Pune dijakritike. NE menja postojeće 4 kolone (`coric-footer__top`) ni `latest_blog_posts` for-loop (5-4) ni copyright. (vidi AC9; G-4 regression.) |
| `static/css/...` (footer) | OPCIONO EDIT | Ako pravni red treba styling → `.coric-footer__legal` u postojećem footer CSS-u (BEM + `var(--...)` tokeni; project-context.md:312-322). Ako Bootstrap utility klase dovoljne → bez novog CSS-a. NIKAD inline style (G-6). |
| `apps/pages/tests/*` | NOVO (TEA) | RED-phase testovi (vidi Testing). **CRITICAL-1: MORA uključiti cross-include asercije** — GET `/sr/politika-kolacica/`→200 (gdpr nije shadow-ovan), GET `/sr/blog/`→200 (blog nije shadow-ovan), `/sr/pretraga/` resolve (AC10). |
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | EDIT | `7-4-...` → `ready-for-dev`. SM handoff tracking (NIJE deliverable). |

**NETAKNUTO (regression guards):** `apps/core/models.py` (TimestampedModel REUSE — NE menja se); `apps/gdpr/*` (CookiePolicy/cookie_policy ruta/baner/tracking — 7.4 NE dira gdpr kod, SAMO footer linkuje na postojeću `gdpr:cookie_policy` rutu); `apps/pages/models.py:SiteSettings` (NE menja se — Page se DODAJE pored); postojeći `pages:home`/`about`/`contact`/`service`/`part_request` view-ovi + rute (NE migriraju se u Page — 8.8); `templates/partials/footer.html` 4 kolone + `latest_blog_posts` (5-4) + copyright (1-8) — SAMO se DODAJE pravni red; `pyproject.toml` (NEMA novog dep). ⚠️ **`config/urls.py` JE SADA EDIT (NIJE više NETAKNUTO) — CRITICAL-1:** pages include se PREMEŠTA na KRAJ i18n_patterns bloka (POSLE gdpr :49); SAMA promena redosleda include-a, BEZ ikakvih drugih izmena (nijedan postojeći include se ne briše/dodaje, samo se redni broj pages reda menja). Razlog dokumentovan u delta tabeli + SM-D11 + AC10. **KRITIČNO:** `makemigrations` posle Page modela sme dotaknuti SAMO `pages/0003` (+ ručno pisan `pages/0004`); `makemigrations --check --dry-run` → „No changes detected" za sve ostale app-ove.

**Route ownership (nasleđeno iz 7-1 SM-D9 — POŠTUJ):**

| URL / ruta | Vlasnik | Pravilo |
|---|---|---|
| `/sr/politika-kolacica/` (`gdpr:cookie_policy`) | **Story 7.1 (gdpr.CookiePolicy)** | 7.4 footer linkuje `{% url 'gdpr:cookie_policy' %}` (postojeća ruta); NE kreira Page instancu/rutu na tom slug-u. `PageDetailView` G-1 guard baca Http404 na `politika-kolacica`. |
| `/sr/politika-privatnosti/` (`pages:page_detail` slug=politika-privatnosti) | **Story 7.4 (pages.Page)** | NOVA ruta + Page model + seed. |
| `<slug:slug>/` catch-all | **Story 7.4 (pages.Page)** | MORA biti POSLEDNJA UNUTAR pages.urls (G-3) da ne shadow-uje statičke rute pages-a; **I** pages include MORA biti POSLEDNJI u config/urls.py i18n_patterns (POSLE gdpr :49) da catch-all ne shadow-uje `/sr/blog/` ni `/sr/politika-kolacica/` preko include granica (CRITICAL-1/SM-D11). |
| `/sr/blog/` (`blog:index`) + sve blog rute | **Story 5.2/5.3 (apps.blog)** | NE sme biti shadow-ovana pages catch-all-om. Lock: pages include POSLE blog :48 (SM-D11). AC10 verifikuje GET `/sr/blog/` → 200. |
| `/sr/pretraga/` (`search`), `/sr/proizvodi/`, brands, forms | **Story 2.x/3.x/4.x** | Prefiksovane 1+-segment rute uključene PRE pages-a; AC10 verifikuje da bar `/sr/pretraga/` nije shadow-ovana (regression lock). |

## Kriterijumi prihvatanja

**AC1 — `Page` generički model u `apps/pages/models.py`; nasleđuje `TimestampedModel`; translatable title/body + unique ASCII slug; NIJE singleton; `system check` čist (SM-D2/D4)**

- **Given** `apps.core.TimestampedModel` (REUSE); postojeći `SiteSettings` u istom modulu (NE dira se)
- **When** dodam `class Page(TimestampedModel)` u `apps/pages/models.py`
- **Then** `Page` MORA imati TAČNO ova polja:
  - `slug` — `SlugField(_("Slug"), max_length=255, unique=True, db_index=True)` (ASCII; project-context.md:165)
  - `title` — `CharField(_("Naslov"), max_length=255)` (**translatable** — AC4)
  - `body` — `TextField(_("Sadržaj"), blank=True)` (**translatable** — AC4; plain-text render `|linebreaks` AC7; SM-D4)
  - nasleđeni `created_at`/`updated_at` iz TimestampedModel (NE redefinisati)
- **And** `Meta.verbose_name=_("Statička strana")`, `verbose_name_plural=_("Statičke strane")`, `Meta.ordering=("title",)`; `__str__` → `self.title or self.slug`
- **And** `get_absolute_url()` → `reverse("pages:page_detail", kwargs={"slug": self.slug})`
- **And** **NIJE singleton** — NEMA `save()` pk=1 / `load()` / `delete()` RAISE override (Page je običan model, više redova)
- **And** NEMA `clean()` defensive validacije (project-context.md:358)
- **And** `uv run python manage.py check` exit 0

**AC2 — RECONCILIATION: `politika-kolacica` se NE duplira u Page (SM-D1; 7-1 SM-D9)**

- **Given** `gdpr.CookiePolicy` (7-1) + `gdpr:cookie_policy` ruta postoje i AUTORITATIVNI su za politiku kolačića
- **When** implementiram 7.4
- **Then**:
  - Data seed (0004) kreira SAMO `Page(slug="politika-privatnosti")` — **NE** kreira `Page(slug="politika-kolacica")`
  - Footer link „Politika kolačića" koristi `{% url 'gdpr:cookie_policy' %}` (POSTOJEĆA ruta), NE Page rutu
  - `PageDetailView` baca `Http404` ako `slug=="politika-kolacica"` (G-1 collision guard) — čak i ako bi neko ručno kreirao takav Page red
- **And** NEMA URL kolizije / dva izvora istine za politiku kolačića

**AC3 — `PageDetailView` slug-routed GET-only + `pages:page_detail` URL u i18n_patterns + catch-all POSLEDNJI UNUTAR pages.urls I pages include POSLEDNJI u config/urls.py (SM-D3/SM-D11/G-3; CRITICAL-1)**

- **Given** AC1; postojeći apps/pages/urls.py (home/about/contact/service/part_request) + config/urls.py i18n_patterns sa include redosledom brands(:43)/products(:44)/search(:45)/**pages(:46)**/forms(:47)/**blog(:48)**/**gdpr(:49)**
- **When** dodam `PageDetailView` + `path("<slug:slug>/", ..., name="page_detail")` I premestim pages include na kraj
- **Then**:
  - `path("<slug:slug>/", PageDetailView.as_view(), name="page_detail")` je **POSLEDNJI** u pages `urlpatterns` (POSLE `servis/rezervni-delovi/`) — catch-all slug ne sme shadow-ovati statičke rute UNUTAR pages-a (G-3)
  - **`path("", include("apps.pages.urls"))` je PREMEŠTEN da bude POSLEDNJI include u `i18n_patterns(...)` (POSLE `apps.gdpr.urls`)** — jer je within-file ordering NEDOVOLJAN preko include granica; bez premeštanja pages catch-all hvata `/sr/politika-kolacica/` i `/sr/blog/` PRE gdpr/blog include-ova (CRITICAL-1/SM-D11)
  - `reverse("pages:page_detail", kwargs={"slug": "politika-privatnosti"})` daje `/sr/politika-privatnosti/` (locale-prefiks kroz i18n_patterns)
  - postojeće rute `o-nama/`/`kontakt/`/`servis/`/`servis/rezervni-delovi/` i dalje resolve-uju na svoje view-ove (NISU shadow-ovane)
  - root `/sr/` i dalje resolve-uje na `pages:home` (prazan path matchuje tačno prazan path — premeštanje include-a ne lomi home)
  - `PageDetailView.http_method_names=["get","head","options"]` → POST/PUT/DELETE → HTTP 405
  - nepostojeći slug (slug bez Page reda) — GET `/sr/nepostojeca-strana/` → HTTP 404 (DetailView default; eksplicitno verifikovano i u AC7/Task 5.5)
- **And** `uv run python manage.py check` exit 0
- **And** verifikacija cross-include neshadow-ovanja je u AC10

**AC4 — `apps/pages/translation.py` registruje `Page.title`/`body` → `_sr/_hu/_en` (SM-D6)**

- **Given** AC1; modeltranslation auto-discovery; LANGUAGES [sr,hu,en]
- **When** dodam `@register(Page)` PORED postojećeg `SiteSettings` registra
- **Then**:
  - `@register(Page)` `TranslationOptions` `fields=("title", "body")`
  - modeltranslation generiše `title_sr/_hu/_en`, `body_sr/_hu/_en` → DB kolone u 0003 (AC5)
  - `slug`/`created_at`/`updated_at` NISU translatable
  - Pristup `page.title` bez aktivnog jezičkog konteksta → sr fallback (`MODELTRANSLATION_FALLBACK_LANGUAGES=("sr",)`)
- **And** postojeći `SiteSettingsTranslationOptions` registar i dalje radi (NE polomljen)
- **And** `uv run python manage.py check` exit 0

**AC5 — Dve migracije: `0003` (CreateModel Page + `_sr/_hu/_en`) + `0004` data seed privacy Lorem (RunPython reverzibilan); manuelno reviewovane (SM-D5)**

- **Given** AC1, AC4 (translation registrovan PRE makemigrations — G-7)
- **When** `uv run python manage.py makemigrations pages` (→ 0003) + ručno napišem `0004_seed_privacy_policy`
- **Then**:
  - `0003`: `CreateModel("Page")` sa `slug`/`title`/`body` + **`title_sr/_hu/_en`, `body_sr/_hu/_en`** + `created_at`/`updated_at`. NEMA data seed. `depend` na `0002_seed_sitesettings`.
  - `0004_seed_privacy_policy`: `RunPython(forward, reverse)`, `dependencies=[("pages","0003_page")]`. `forward` → `get_or_create(slug="politika-privatnosti", defaults={title_sr, body_sr})` Lorem Ipsum (SAMO `_sr` pune dijakritike — OQ-1; hu/en fallback). `reverse` → `filter(slug="politika-privatnosti").delete()`.
  - **`forward` popunjava `_sr` kolone DIREKTNO** (`title_sr`/`body_sr` — historical model; mirror pages 0002 + brands 0003; G-2)
  - **`forward` NE seed-uje `politika-kolacica`** (SM-D1/AC2)
  - **`forward` `body_sr` sadrži eksplicitan PLACEHOLDER/TODO marker** (NE goli Lorem Ipsum) + `# TODO(RISK-1)` komentar u migraciji — sprečava deploy placeholder-a kao prave politike (G-15 / RISK-1)
  - **`makemigrations` ne sme dotaknuti nijednu POSTOJEĆU app migraciju** — `makemigrations --check --dry-run` → „No changes detected"
  - Dev MANUELNO reviewuje oba (project-context.md:221); `migrate --plan` prikazuje plan
  - `migrate pages` primeni; `migrate pages 0003` reverzuje seed (0004 reverse delete-uje privacy red)
- **And** posle `migrate`, `Page.objects.filter(slug="politika-privatnosti").exists()` je `True` („postoji pre prvog deploy-a", epics.md:1048)
- **And** migracije + model promene commit-uju se ZAJEDNO (atomic; project-context.md:223)

**AC6 — `PageAdmin(TranslationAdmin)` — per-locale edit + prepopulated slug; NIJE singleton (ima add/delete) (SM-D7)**

- **Given** AC1; postojeći `SiteSettingsAdmin` (NE dira se)
- **When** dodam `@admin.register(Page) class PageAdmin(TranslationAdmin)`
- **Then**:
  - `TranslationAdmin` (NE plain ModelAdmin) → modeltranslation auto-grupiše `title`/`body` po jeziku (sr/hu/en tabovi)
  - `list_display=("title", "slug", "updated_at")`, `search_fields=("title", "slug")`
  - `prepopulated_fields={"slug": ("title",)}` (admin UX — auto-slug; G-5: radi na default-locale title polju)
  - **NIJE singleton** — NE override-uj `has_add_permission`/`has_delete_permission` (Marijana može da kreira/briše Page redove)
  - admin add/change-view → 200 za superuser-a (TranslationAdmin renderuje per-locale title/body bez greške)
- **And** `run_checks()` bez admin.E* grešaka

**AC7 — Javna strana `/sr/politika-privatnosti/` renderuje sadržaj iz Page (title + body |linebreaks XSS-safe) per locale (SM-D3/D4)**

- **Given** AC5 (seed postoji); `PageDetailView` + `pages:page_detail` URL
- **And Given** `MODELTRANSLATION_FALLBACK_LANGUAGES=("sr",)` JE konfigurisan (settings — 1-2/1-4 baseline; preduslov za hu/en→sr fallback aserciju ispod; bez njega prazno `_hu/_en` ne bi vratilo sr sadržaj)
- **When** GET `/sr/politika-privatnosti/`
- **Then**:
  - HTTP 200; template `pages/page-detail.html` korišćen
  - `<title>` = `page.title` (kroz `{% block title %}`)
  - `<h1>` sadrži `page.title`; telo sadrži `page.body` renderovan kroz `|linebreaks`
  - **`body` se renderuje `{{ page.body|linebreaks }}` — NIKAD `{{ page.body|safe }}`** (SM-D4 — autoescape; mirror gdpr/cookie_policy.html:15-16)
  - `/hu/politika-privatnosti/` i `/en/politika-privatnosti/` → 200; pošto seed popunjava SAMO `_sr`, hu/en prikazuju **sr fallback sadržaj** dok biznis ne unese prevod
  - GET-only: POST → HTTP 405
  - nepostojeći slug (npr. `/sr/nepostojeca-strana/`) → HTTP 404
- **And** `get_absolute_url()` → `reverse("pages:page_detail", kwargs={"slug": ...})` daje aktivni-locale prefiks

**AC8 — XSS granica: malicozni HTML u `body` se renderuje kao tekst, NE izvršava (SM-D4)**

- **Given** AC7; `Page.body` koji sadrži npr. `<script>alert(1)</script>` ili `<img src=x onerror=...>`
- **When** GET strana renderuje body
- **Then**:
  - Renderovan HTML SADRŽI ESCAPE-ovan tekst (`&lt;script&gt;...`) — NE sirov `<script>` tag
  - `body` NIKAD ne prolazi kroz `|safe` filter ni `mark_safe()`
  - **Napomena:** `|linebreaks` SAM auto-escape-uje pre dodavanja `<br>`/`<p>` (Django built-in) — tačno ponašanje za plain-text body (v1). Rich-HTML body (sa namernim tagovima) = Epic 8.7 (sanitizacija), NE 7.4.

**AC9 — Footer linkuje obe politike (privatnost NOVA ruta + kolačići POSTOJEĆA 7-1 ruta); postojeći footer NETAKNUT (SM-D8/G-4)**

- **Given** AC3 (`pages:page_detail`) + postojeća `gdpr:cookie_policy` (7-1); `templates/partials/footer.html`
- **When** dodam pravni red u footer
- **Then**:
  - Footer sadrži link „Politika privatnosti" → `{% url 'pages:page_detail' slug='politika-privatnosti' %}`
  - Footer sadrži link „Politika kolačića" → `{% url 'gdpr:cookie_policy' %}` (POSTOJEĆA 7-1 ruta — NE Page ruta)
  - Link tekst koristi pune dijakritike (`{% translate %}` — „Politika privatnosti"/„Politika kolačića")
  - postojeće 4 footer kolone (`coric-footer__top`), `latest_blog_posts` for-loop (5-4) i copyright (1-8) i dalje renderuju nepromenjeno (G-4 regression)
  - footer se renderuje na SVAKOJ strani (uključen kroz base.html) → linkovi dostupni site-wide
  - **(IMP) Šišana-latinica fix (G-13):** dve postojeće šišane string-ove u footer-u su ispravljene — `Pocetna` → `Početna` (:9 aria-label) i `Sva prava zadrzana.` → `Sva prava zadržana.` (:80 copyright); pošto su `{% translate %}` msgid-ovi, `.po` je regenerisan (`makemessages`) tako da novi (pun-dijakritik) ključ ne ostane neprevodljiv
- **And** NEMA inline style-a; ako treba styling → `.coric-footer__legal` BEM + `var(--...)` tokeni (G-6)

**AC10 — CROSS-INCLUDE neshadow-ovanje: pages catch-all NE sme oboriti susedne include-ove (CRITICAL-1 regression lock; SM-D11/G-3)**

- **Given** AC3 (catch-all `<slug:slug>/` + pages include premešten na kraj i18n_patterns); 7-1 `gdpr:cookie_policy` (`/sr/politika-kolacica/`), 5-2 `blog:index` (`/sr/blog/`), search (`/sr/pretraga/`) sve POSTOJE i bile su funkcionalne PRE 7.4
- **When** GET-ujem susedne rute koje su 1-segment (potencijalno hvatljive pages catch-all-om) posle 7.4 izmena
- **Then** (ovo je JEDINI pouzdan lock protiv regresije — within-file ordering ga ne pokriva):
  - GET `/sr/politika-kolacica/` → **HTTP 200** (7-1 cookie policy I DALJE dostupna; NIJE 404) — footer „Politika kolačića" link + 7-2 baner „Više info" link + 7-3 privacy linkovi rade
  - GET `/sr/blog/` → **HTTP 200** (5-2 blog index I DALJE dostupan; NIJE 404 ni Page-404)
  - GET `/sr/pretraga/` (ili druga search ruta) → resolve-uje na search view (NIJE shadow-ovana pages catch-all-om)
  - `resolve("/sr/politika-kolacica/").func` / view pripada `apps.gdpr` (NE `pages.PageDetailView`); `resolve("/sr/blog/")` pripada `apps.blog`
  - GET `/sr/politika-privatnosti/` → HTTP 200 (NOVA pages ruta i dalje radi — premeštanje include-a je ne lomi)
- **And** ovi GET-ovi MORAJU postojati kao test asercije (RED-phase TEA) — bez njih regresija prolazi nezapaženo; within-pages-file ordering test (AC3) NE detektuje cross-include shadow

## Testing

**TEA piše testove (RED phase) PRE Dev implementacije (project-context.md:294). Dev NIKAD ne piše testove.** pytest-django; `@pytest.mark.django_db`. Ova sekcija KOMPLEMENTIRA AC10 (ne duplira ga — AC10 cross-include lock se NAVODI ovde radi vidljivosti, ali ostaje merodavan u AC10). Mirror format 7-1 Testing sekcije.

### Model (apps/pages/tests/test_page_model.py)
- `test_page_inherits_timestamped` — Page ima `created_at`/`updated_at` (TimestampedModel REUSE)
- `test_page_fields` — `slug` (unique/db_index), `title`, `body` (blank) postoje
- `test_get_absolute_url` — `page.get_absolute_url()` == `reverse("pages:page_detail", kwargs={"slug": page.slug})`
- `test_str_returns_title_or_slug` — `__str__` vraća `title` kad postoji, inače `slug`
- `test_page_is_not_singleton` — može se kreirati VIŠE Page redova (2× create različit slug → count()==2); NEMA save() pk=1 prisile

### Translation (apps/pages/tests/test_page_translation.py)
- `test_translated_fields_exist` — `title_sr/_hu/_en`, `body_sr/_hu/_en` postoje (hasattr)
- `test_slug_not_translatable` — NEMA `slug_sr`/`slug_hu`/`slug_en` (slug je ASCII jezik-neutralan)
- `test_per_locale_values` — setuj title_sr/hu/en, čitaj sa `translation.override`
- `test_fallback_to_sr` — `title_hu`/`body_hu` prazan → pod hu context-om vraća `_sr` vrednost (preduslov `MODELTRANSLATION_FALLBACK_LANGUAGES=("sr",)` — AC7)

### Migracije (apps/pages/tests/test_page_migrations.py)
- `test_0003_creates_page_with_translated_columns` — tabela `pages_page` + `title_sr/_hu/_en`, `body_sr/_hu/_en` kolone (introspection); `slug`/timestamp-ovi BEZ `_sr/hu/en`
- `test_0004_seed_creates_privacy_page` — posle migrate, `Page.objects.filter(slug="politika-privatnosti").exists()` True; `title_sr`/`body_sr` popunjeni
- `test_0004_seed_does_NOT_create_cookie_policy_page` — `Page.objects.filter(slug="politika-kolacica").exists()` False (SM-D1/AC2 — NE seed-uje kolačiće)
- `test_0004_reverse_deletes_privacy_page` — `migrate pages 0003` → privacy red obrisan
- `test_0004_seed_idempotent` — ponovno pokretanje forward-a (get_or_create) ne kreira duplikat

### View (apps/pages/tests/test_page_detail_view.py)
- `test_privacy_page_200_sr` / `_hu` / `_en` — GET `/sr|/hu|/en/politika-privatnosti/` → 200
- `test_post_returns_405` — POST `/sr/politika-privatnosti/` → 405 (GET-only http_method_names)
- `test_nonexistent_slug_404` — GET `/sr/nepostojeca-strana/` → 404 (nema Page reda)
- `test_g1_cookie_policy_slug_404` — GET na pages rutu za `politika-kolacica` slug → 404 (G-1 collision guard; gdpr je vlasnik) — čak i ako se ručno kreira `Page(slug="politika-kolacica")` red
- `test_body_rendered_via_linebreaks` — body sadržaj prisutan, prelomljen kroz `|linebreaks`

### Admin (apps/pages/tests/test_page_admin.py)
- `test_page_admin_changelist_200` — superuser GET `reverse("admin:pages_page_changelist")` → 200
- `test_page_admin_add_200` — superuser GET add-view → 200 (TranslationAdmin renderuje per-locale title/body bez greške)
- `test_page_admin_change_200` — superuser GET change-view za seed red → 200
- `test_page_admin_not_singleton` — `has_add_permission`/`has_delete_permission` True (NIJE singleton; RAZLIKA od 7-1/3-4)

### Template / XSS (apps/pages/tests/test_page_template_xss.py)
- `test_script_in_body_escaped` — `Page(body="<script>alert(1)</script>")` → render sadrži `&lt;script&gt;`, NE sirov `<script>` (AC8)
- `test_body_never_safe` — verifikacija da template NE koristi `|safe`/`mark_safe` na body (stored-XSS granica; mirror gdpr/cookie_policy.html)

### Footer (apps/pages/tests/test_footer_legal.py — ili proširenje postojećih footer testova, G-4)
- `test_footer_privacy_link_resolves` — footer sadrži `{% url 'pages:page_detail' slug='politika-privatnosti' %}`
- `test_footer_cookie_link_resolves` — footer sadrži `{% url 'gdpr:cookie_policy' %}` (POSTOJEĆA ruta, NE pages slug — G-11)
- `test_footer_regression_intact` — 4 kolone (`coric-footer__top`) + `latest_blog_posts` for-loop (5-4) + copyright (1-8) i dalje renderuju (G-4)
- `test_footer_no_sisana_latinica` (IMP) — footer NE sadrži `Pocetna`/`Sva prava zadrzana.`; sadrži `Početna`/`Sva prava zadržana.` (G-13)

### Cross-include lock (AC10 — NAVEDENO ovde radi vidljivosti; merodavno u AC10)
- `test_cookie_policy_still_200` — GET `/sr/politika-kolacica/` → 200 (gdpr nije shadow-ovan pages catch-all-om)
- `test_blog_index_still_200` — GET `/sr/blog/` → 200 (blog nije shadow-ovan)
- `test_search_still_resolves` — `/sr/pretraga/` resolve-uje na search view (NIJE shadow-ovana)
- `test_resolve_ownership` — `resolve("/sr/politika-kolacica/")` pripada `apps.gdpr`; `resolve("/sr/blog/")` pripada `apps.blog`

## Tasks / Zadaci

- [x] **Task 1 — `Page` generički model** (AC1, AC2)
  - [x] 1.1 `apps/pages/models.py`: dodaj `class Page(TimestampedModel)` sa `slug` (unique/db_index, ASCII) + `title`/`body` (translatable) — PORED `SiteSettings` (NE dira SiteSettings)
  - [x] 1.2 `get_absolute_url()` → `reverse("pages:page_detail", kwargs={"slug": self.slug})` + `__str__` (`title or slug`) + `Meta` (verbose_name/ordering)
  - [x] 1.3 VERIFIKUJ: NIJE singleton (NEMA save()/load()/delete() override) + NEMA clean() defensive validacije
  - [x] 1.4 `uv run python manage.py check` exit 0

- [x] **Task 2 — modeltranslation registracija (EDIT)** (AC4)
  - [x] 2.1 `apps/pages/translation.py`: dodaj `@register(Page)` `fields=("title","body")` PORED `SiteSettingsTranslationOptions`
  - [x] 2.2 `uv run python manage.py check` exit 0 (translation reg ne baca; SiteSettings registar i dalje radi)

- [x] **Task 3 — Schema migracija `0003`** (AC5)
  - [x] 3.1 VERIFIKUJ translation.py registrovan PRE makemigrations (G-7) → `uv run python manage.py makemigrations pages`
  - [x] 3.2 MANUAL REVIEW: `CreateModel("Page")` + `title_sr/hu/en` + `body_sr/hu/en` + slug/timestamp-ovi (slug/timestamp BEZ _sr/hu/en); `depend` na 0002
  - [x] 3.3 `migrate --plan` + `migrate pages` apply; `makemigrations --check --dry-run` → „No changes detected" za sve app-ove

- [x] **Task 4 — Data seed migracija `0004` (SAMO privatnost)** (AC5, AC2)
  - [x] 4.1 Ručno napiši `RunPython(forward, reverse)`, `dependencies=[("pages","0003_...")]`. **NAPOMENA (G-14):** posle `makemigrations pages` PROVERI STVARNO generisano ime 0003 fajla (`makemigrations` auto-imenuje — može biti `0003_page` ALI i `0003_<auto>`; NE pretpostavljaj `0003_page`) i USKLADI `dependencies` u ručno pisanom 0004 sa TIM stvarnim imenom (pogrešan dependency string → `migrate` baca `NodeNotFoundError`)
  - [x] 4.2 `forward`: `get_or_create(slug="politika-privatnosti", defaults={title_sr, body_sr})` (SAMO `_sr`, sr pune dijakritike — OQ-1); popuni `_sr` kolone DIREKTNO (G-2); **NE seed-uj `politika-kolacica`** (SM-D1/AC2). **PLACEHOLDER marker (OBAVEZNO; G-15 / RISK-1):** `body_sr` NE sme biti goli Lorem Ipsum — MORA početi jasnim markerom da niko ne deploy-uje placeholder kao pravu politiku, npr. modul-level konstanta `_BODY_SR = "[PLACEHOLDER — pravni tekst MORA uneti biznis/pravnik pre go-live (RISK-1, Mihas sign-off)]\n\n" + <Lorem Ipsum>`; doda i `# TODO(RISK-1): placeholder privacy text — zameniti pravim pre go-live` komentar u migraciji (mirror pages 0002 `# TODO(OQ-1): placeholder` konvencija). `title_sr="Politika privatnosti"` (ostaje pravi naslov).
  - [x] 4.3 `reverse`: `filter(slug="politika-privatnosti").delete()`
  - [x] 4.4 `migrate pages` (seed kreiran) + `migrate pages 0003` (seed obrisan) + `migrate pages` ponovo — reverzibilnost OK

- [x] **Task 5 — `PageDetailView` + URL (EDIT) sa G-1 guard + G-3 ordering + config/urls.py reorder (CRITICAL-1)** (AC3, AC7, AC10)
  - [x] 5.1 `apps/pages/views.py`: dodaj `PageDetailView(DetailView)` GET-only (`http_method_names` mirror ContactView), `slug_field`/`context_object_name`/`template_name`
  - [x] 5.2 G-1 collision guard: `slug=="politika-kolacica"` → `Http404` (gdpr je vlasnik; SM-D1)
  - [x] 5.3 `apps/pages/urls.py`: dodaj `path("<slug:slug>/", PageDetailView.as_view(), name="page_detail")` **NA KRAJ** liste (G-3 — POSLE statičkih ruta)
  - [x] 5.4 **CRITICAL-1: `config/urls.py` — PREMESTI `path("", include("apps.pages.urls"))` da bude POSLEDNJI include u `i18n_patterns(...)` (POSLE `apps.gdpr.urls`).** SAMO promena redosleda; ne briši/dodaj druge include-ove. Verifikuj komentarom razlog (catch-all cross-include). (SM-D11)
  - [x] 5.5 Verifikuj `/sr/`,`/hu/`,`/en/politika-privatnosti/` → 200; POST → 405; **nepostojeći slug bez Page reda — GET `/sr/nepostojeca-strana/` → 404 (eksplicitno; AC7)**; G-1 `politika-kolacica` pages slug → 404; `o-nama/`/`kontakt/`/`servis/` i dalje resolve-uju (NISU shadow-ovane); `/sr/` home → 200
  - [x] 5.6 **CRITICAL-1 cross-include lock: GET `/sr/politika-kolacica/` → 200 (gdpr); GET `/sr/blog/` → 200 (blog); GET `/sr/pretraga/` resolve-uje na search — NIJEDAN nije shadow-ovan pages catch-all-om** (AC10)

- [x] **Task 6 — `PageAdmin` (EDIT, NIJE singleton)** (AC6)
  - [x] 6.1 `apps/pages/admin.py`: dodaj `@admin.register(Page) class PageAdmin(TranslationAdmin)` PORED `SiteSettingsAdmin`
  - [x] 6.2 `list_display` + `search_fields` + `prepopulated_fields={"slug":("title",)}` (G-5); NE override has_add/has_delete (NIJE singleton)
  - [x] 6.3 Verifikuj add/change-view 200 za superuser-a

- [x] **Task 7 — Template (XSS-safe body render)** (AC7, AC8)
  - [x] 7.1 `templates/pages/page-detail.html`: extends base.html; `{% block title %}{{ page.title }}{% endblock %}`; `<h1>` + „Poslednja izmena" (`page.updated_at`) + `{{ page.body|linebreaks }}`. Mirror gdpr/cookie_policy.html
  - [x] 7.2 VERIFIKUJ: NIKAD `|safe`/`mark_safe` na body (XSS granica; mirror gdpr/cookie_policy.html:15-16)
  - [x] 7.3 Pune dijakritike u UI string-ovima (`{% translate %}`); slug `politika-privatnosti` ASCII

- [x] **Task 8 — Footer pravni red (EDIT)** (AC9)
  - [x] 8.1 `templates/partials/footer.html`: dodaj pravni red sa 2 linka — privatnost `{% url 'pages:page_detail' slug='politika-privatnosti' %}` + kolačići `{% url 'gdpr:cookie_policy' %}` (POSTOJEĆA 7-1 ruta, NE duplira)
  - [x] 8.2 Pune dijakritike u link tekstu (`{% translate "Politika privatnosti" %}`/„Politika kolačića"); ako treba styling → `.coric-footer__legal` BEM + tokeni (G-6, NIKAD inline style)
  - [x] 8.3 VERIFIKUJ regression: postojeće 4 kolone + latest_blog_posts (5-4) + copyright (1-8) nepromenjeni (G-4)
  - [x] 8.4 **Šišana-latinica fix (IMP — pošto već diraš footer.html):** ispravi DVE postojeće msgid string-ove bez dijakritike (project-context.md zabranjuje šišanu latinicu u UI; G-13): `templates/partials/footer.html:9` `{% translate "Pocetna" %}` → `{% translate "Početna" %}` (aria-label logo linka) I `templates/partials/footer.html:80` `{% translate "Sva prava zadrzana." %}` → `{% translate "Sva prava zadržana." %}` (copyright). NE menja markup/strukturu — SAMO tekst string-ova. NAPOMENA: ovo su `{% translate %}` msgid-ovi → posle izmene regeneriši `.po` (`uv run python manage.py makemessages -l sr -l hu -l en`) jer se menja msgid ključ; proveri da postojeći prevodi/fallback ne ostanu na starom (šišanom) ključu. Ako nema prevedenih unosa za te string-ove → makemessages samo ažurira msgid, bez gubitka.

- [x] **Task 9 — Lint + finalna verifikacija**
  - [x] 9.1 `just lint` clean (ruff + djade)
  - [x] 9.2 `just test` — pages testovi + **ŠIRI suite (gdpr + blog + search)** GREEN (TEA piše testove RED phase pre Dev-a; Dev GREEN). ⚠️ CRITICAL-1: OBAVEZNO pokreni gdpr + blog suite (NE samo pages) da uhvatiš cross-include shadow regresiju (`/sr/politika-kolacica/`, `/sr/blog/` → 200; AC10) — query-budget-drift lekcija iz Epic 6: pokreni širi a ne app-specifičan suite.
  - [x] 9.3 VERIFIKUJ Epic 7 zatvoren (sve 7-1..7-4 done posle review-a)

## Dev Notes

### RECONCILIATION SM-D1 — pročitaj PRE koda (epics.md vs 7-1 SM-D9)

epics.md 7.4 traži „2 default Page instance (politika-privatnosti **i ako treba** politika-kolacica)". 7-1 SM-D9 (AUTORITATIVNO, već done) zabranjuje dupliranje politike kolačića. **ODLUKA:** „ako treba" = NE treba. Seed SAMO privatnost; footer kolačići-link na `gdpr:cookie_policy`; `PageDetailView` G-1 baca Http404 na `politika-kolacica`. Bez dva izvora istine, bez URL kolizije.

### Page NIJE singleton (RAZLIKA od CookiePolicy/SiteSettings)

CookiePolicy (7-1) i SiteSettings (3-4) su singleton-i (jedan red, save() pk=1 + load() + delete() raise). **Page je OBIČAN model** — više redova (privatnost sad; „O nama"/„Servis"/itd. CMS-ifikacija u 8.8). NE primenjuj singleton recept na Page: NEMA save() pk=1, NEMA load(), NEMA delete() raise, admin IMA add/delete. Seed koristi `get_or_create(slug=...)` (NE pk=1).

### BODY XSS render — 7-1 SM-D3 / blog 5-3 SM-D1 presedan (security-critical)

`body` plain TextField, render `{{ page.body|linebreaks }}`. `|linebreaks` SAM auto-escape-uje (Django built-in) → XSS-safe za plain-text. **NIKAD `|safe`/`mark_safe`** (stored-XSS — admin nalog kompromitovan = injection vektor). epics.md kaže „body rich text" ALI rich-HTML + WYSIWYG + bleach/nh3 sanitizacija = Epic 8.7 (isti deferral kao 7-1/5-3). v1 = plain |linebreaks. Mirror gdpr/cookie_policy.html:15-16.

### Catch-all slug ruta MORA biti POSLEDNJA — UNUTAR fajla I PREKO include-ova (G-3 / CRITICAL-1 — najlakše promašiti)

`path("<slug:slug>/", ...)` matchuje BILO KOJI single-segment path. Django URL resolver je first-match-wins, top-to-bottom, **i to PREKO svih `include()`-ova** (resolver ne „resetuje" prioritet po include-u — gradi jednu sploštenu listu pattern-a redosledom kojim su include-ovi navedeni). Dve granice:

1. **Unutar pages.urls (G-3):** ako catch-all ide PRE `o-nama/`/`kontakt/`/`servis/`, shadow-uje ih (Page 404 umesto AboutView). MORA biti POSLEDNJI u pages `urlpatterns`. (`servis/rezervni-delovi/` je 2-segment pa ga `<slug:slug>/` ne hvata; `""` home je prazan path pa ga slug ne hvata; eksplicitne 1-segment rute JESU rizik.)

2. **Preko include-ova (CRITICAL-1 — within-file ordering NIJE dovoljan!):** `apps.pages.urls` je u config/urls.py uključen na :46 — PRE blog (:48) i gdpr (:49), svi mount-ovani na praznom prefiksu `""`. To znači da pages catch-all `<slug:slug>/` (1-segment) hvata `/sr/politika-kolacica/` (gdpr) i `/sr/blog/` (blog) PRE nego što se ti include-ovi uopšte dosegnu → cookie policy (7-1) i blog index TRAJNO 404 (a za `politika-kolacica` onda G-1 guard baca Http404). **REŠENJE:** premesti `path("", include("apps.pages.urls"))` da bude POSLEDNJI include u i18n_patterns (POSLE gdpr :49) — SM-D11. Bezbedno jer prazan path (`pages:home`) matchuje TAČNO prazan path i nijedan drugi include ne polaže pravo na goli `""`.

⚠️ **UPOZORENJE za budućnost:** SVAKA buduća 1-segment ruta (`<slug:slug>/`, `<int:pk>/`, ili gola `nesto/`) dodata u app uključen PRE pages-a bi takođe bila shadow-ovana pages catch-all-om. Zbog toga pages include MORA OSTATI POSLEDNJI u i18n_patterns; ako se ikad doda novi app sa 1-segment rutama, on ide PRE pages include-a.

### Footer je deljeno vlasništvo (G-4 — regression-sensitive)

`templates/partials/footer.html` su dirale Story 1-8 (komponenta) + 5-4 (latest_blog_posts dinamički). 7.4 SAMO DODAJE pravni red — NE menja 4 kolone, NE dira `latest_blog_posts` for-loop, NE menja copyright. Test-ownership lekcija (Epic 5 memory): kad story menja tuđi markup, pazi da ne polomiš postojeće footer testove (1-8/5-4). Dodaj pravni red NEINVAZIVNO (npr. u `coric-footer__bottom` pored copyright-a).

### Data migracija (NE fixture) — „postoji pre prvog deploy-a"

AC (epics.md:1048) traži Lorem Ipsum baseline pre prvog deploy-a. Data migracija (RunPython) pouzdanija od fixture jer `migrate` je deploy step (project-context.md:453) — auto-primenjena. Mirror pages 0002_seed_sitesettings + brands 0003 + gdpr 7-1 0002. Reverzibilan (`reverse_code` — project-context.md:227). Seed _sr-only (OQ-1 — hu/en fallback na sr; NE lažan prevod).

### G-1 collision guard NIJE defensive-over-internal

project-context.md:358 zabranjuje defensive validaciju nad internim pozivima. G-1 (`slug=="politika-kolacica"` → Http404) NIJE to — `<slug>` je JAVNI URL segment koji KORISNIK kontroliše (boundary). Legitimna boundary zaštita protiv route-collision / dva izvora istine. Trust internal, validate boundary.

### Project Structure Notes

- `Page` model + view + admin + translation idu u POSTOJEĆI apps/pages (EDIT — NE novi app). Migracije 0003/0004 nastavljaju pages sekvencu (0001/0002).
- `pages:page_detail` ruta UNUTAR apps/pages/urls.py (config/urls.py uključuje apps.pages.urls u i18n_patterns → ruta dobija /sr/ prefiks automatski). ⚠️ **CRITICAL-1/SM-D11: config/urls.py JESTE EDIT** — pages include se PREMEŠTA na KRAJ i18n_patterns (POSLE gdpr :49) jer catch-all `<slug:slug>/` inače shadow-uje blog/gdpr rute preko include granica. (Ranija tvrdnja „NE diraj config/urls.py" je bila pogrešna i CRITICAL-1 je ispravlja.)
- slug `politika-privatnosti` ASCII (project-context.md:165); UI/seed pune dijakritike.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 7.4 (linije 1037-1048)] (Page model slug/title/body + admin + 2 instance „ako treba" + footer linkovi + /sr/politika-privatnosti/ + Lorem Ipsum)
- [Source: _bmad-output/implementation-artifacts/7-1-cookiepolicy-model-admin.md SM-D9 + OUT-OF-SCOPE route-ownership] (CookiePolicy AUTORITATIVAN za kolačiće; 7.4 NE duplira; footer linkuje gdpr:cookie_policy)
- [Source: apps/gdpr/models.py:99-101 + templates/gdpr/cookie_policy.html:15-16] (get_absolute_url + body |linebreaks NIKAD |safe — MIRROR)
- [Source: apps/pages/models.py:28-131 + translation.py + admin.py] (apps/pages struktura; SiteSettings PORED kog Page ide; translation.py EDIT pattern; SiteSettingsAdmin TranslationAdmin pattern)
- [Source: apps/pages/views.py:103-130 (AboutView/ContactView)] (statička-strana GET-only http_method_names PATTERN)
- [Source: apps/pages/urls.py] (urlpatterns — catch-all slug ide NA KRAJ; G-3)
- [Source: config/urls.py:41-51 (i18n_patterns include redosled brands:43/products:44/search:45/pages:46/forms:47/blog:48/gdpr:49)] (CRITICAL-1/SM-D11 — pages include se PREMEŠTA na KRAJ; resolver first-match-wins preko include granica)
- [Source: apps/blog/urls.py:19 (blog:index `/sr/blog/`) + apps/gdpr/urls.py:14 (gdpr:cookie_policy `/sr/politika-kolacica/`)] (rute koje pages catch-all NE sme da shadow-uje; AC10 lock)
- [Source: apps/pages/migrations/0002_seed_sitesettings.py] (data-migracija RunPython reversible + _sr-only seed + reverse delete — MIRROR za 0004)
- [Source: templates/partials/footer.html] (footer 4 kolone + latest_blog_posts 5-4 + copyright 1-8 — DODAJ pravni red NEINVAZIVNO, G-4)
- [Source: _bmad-output/implementation-artifacts/5-3-blog-post-detail-strana.md] (body-render XSS decision; WYSIWYG defer Epic 8.7)
- [Source: _bmad-output/implementation-artifacts/5-1-blogpost-category-tag-modeli-admin-stub.md Gotcha BL-2 + Task 7.2] (PRESEDAN: prepopulated_fields + modeltranslation razrešen sa TranslationAdmin opcija (a), prepopulated ZADRŽAN — G-5)
- [Source: apps/core/models.py:15-22] (TimestampedModel REUSE)
- [Source: _bmad-output/project-context.md] (dijakritike, ASCII slug, migrations discipline, XSS no-|safe, no defensive validation, YAGNI)

## SM Decision Log

- **SM-D1 — RECONCILIATION: 7.4 NE duplira politiku kolačića; seed SAMO privatnost.** epics.md 7.4 (1045) traži „2 instance (privatnost i **ako treba** kolačići)". 7-1 SM-D9 (AUTORITATIVNO, done) je odlučio da je gdpr.CookiePolicy JEDINI izvor kolačića. ODLUKA: „ako treba" = NE treba. 7.4 kreira generički Page + seed SAMO `politika-privatnosti`; footer kolačići-link → `gdpr:cookie_policy`; `PageDetailView` G-1 → Http404 na `politika-kolacica`. Bez dva izvora istine / URL kolizije.
- **SM-D2 — Generički `Page` model (NIJE singleton).** epics.md traži `Page` (slug/title/body). Page je OBIČAN model (više redova — privatnost sad, „O nama"/„Servis" CMS u 8.8). NE singleton recept (NEMA save() pk=1/load()/delete() raise — to je CookiePolicy/SiteSettings). slug unique+db_index ASCII; title/body translatable. Nasleđuje TimestampedModel (REUSE).
- **SM-D3 — `PageDetailView` slug-routed GET-only + catch-all ruta POSLEDNJA.** DetailView, slug_field="slug", GET-only (http_method_names mirror ContactView). `path("<slug:slug>/", ...)` NA KRAJ urls.py (G-3 — first-match-wins; ne sme shadow-ovati `o-nama/`/`kontakt/`/`servis/`). G-1 collision guard (politika-kolacica → Http404).
- **SM-D4 — body = plain TextField, render `|linebreaks` autoescape, NIKAD `|safe`; WYSIWYG DEFER Epic 8.7.** Mirror 7-1 SM-D3 + blog 5-3 SM-D1. epics.md kaže „rich text" ALI rich-HTML + sanitizacija = 8.7. v1 plain |linebreaks. NEMA bleach/nh3 dep.
- **SM-D5 — Dve migracije: 0003 schema (CreateModel) + 0004 data seed privacy Lorem (RunPython reverzibilan), NE fixture.** „Postoji pre prvog deploy-a" (epics.md:1048) → data migracija (migrate=deploy step). Mirror pages 0002 + gdpr 7-1 0002 + brands 0003. _sr-only seed (OQ-1 — hu/en fallback). reverse delete privacy red. ODVOJENA schema/data. **Seed `body_sr` MORA imati eksplicitan PLACEHOLDER/TODO marker (NE goli Lorem Ipsum) — G-15 / RISK-1:** marker na vrhu body teksta + `# TODO(RISK-1)` komentar u migraciji da niko ne pomeša placeholder sa pravom politikom privatnosti (vezano za nasleđeni RISK-1 — Mihas legal sign-off PRE go-live). Konvencija mirror pages 0002 (`# TODO(OQ-1): placeholder`).
- **SM-D6 — translation.py EDIT: dodaj Page registar PORED SiteSettings.** `@register(Page)` `fields=("title","body")` → `_sr/_hu/_en`. slug/timestamp jezik-neutralni. NE diraj postojeći SiteSettingsTranslationOptions.
- **SM-D7 — PageAdmin(TranslationAdmin), NIJE singleton (ima add/delete + prepopulated slug).** Per-locale title/body tabovi auto. `prepopulated_fields={"slug":("title",)}` admin UX. NE override has_add/has_delete (Marijana kreira/briše Page redove — RAZLIKA od singleton admin-a 7-1/3-4).
- **SM-D8 — Footer pravni red sa 2 linka (privatnost NOVA + kolačići POSTOJEĆA ruta).** privatnost → `{% url 'pages:page_detail' slug='politika-privatnosti' %}`; kolačići → `{% url 'gdpr:cookie_policy' %}` (7-1 ruta, NE duplira). DODAJ NEINVAZIVNO (G-4 — footer 1-8/5-4 vlasništvo). Pune dijakritike.
- **SM-D9 — SeoMeta inline na PageAdmin DEFER (OQ-2).** Page ima get_absolute_url → kvalifikuje se za SeoMeta GFK inline (6-1), ALI strana dobija <title>/meta kroz base.html + globalni {% seo_head %} fallback (6-3). Inline = dodatni wiring; deferred.
- **SM-D11 — CRITICAL-1: pages include PREMEŠTEN na KRAJ config/urls.py i18n_patterns (config/urls.py je EDIT, NE NETAKNUTO).** Catch-all `<slug:slug>/` POSLEDNJI UNUTAR pages.urls je NEOPHODAN ALI NE I DOVOLJAN — Django resolver je first-match-wins PREKO include granica (jedna sploštena lista pattern-a redosledom include-a). Pošto je `apps.pages.urls` uključen na :46 PRE blog (:48) i gdpr (:49) — svi na praznom prefiksu `""` — pages catch-all bi uhvatio `/sr/politika-kolacica/` i `/sr/blog/` PRE tih include-ova → 7-1 cookie policy + blog index TRAJNO 404 (footer/baner/SEO linkovi mrtvi). ODLUKA: premesti `path("", include("apps.pages.urls"))` da bude POSLEDNJI include u i18n_patterns (POSLE gdpr). Verifikovano da je bezbedno: pages.urls poseduje root `path("", HomeView, name="home")`, ali prazan path matchuje TAČNO prazan path, a nijedan drugi include (brands/products/search/forms/blog/gdpr) ne polaže pravo na goli `""` — svaki definiše SAMO prefiksovane rute (pročitana svaka urls.py). `admin/` ostaje na svom mestu (eksplicitan prefiks, neugrožen). AC10 + Task 5.4/5.6 zaključavaju regresiju GET-ovima `/sr/politika-kolacica/`→200, `/sr/blog/`→200, `/sr/pretraga/` resolve. Ovo zamenjuje raniju (pogrešnu) tvrdnju „config/urls.py NETAKNUTO".
- **SM-D10 — Postojeći about/contact/service view-ovi se NE migriraju u Page (8.8).** 7.4 daje SAMO bazni Page + privacy strana. CMS-ifikacija postojećih statičkih strana (hero_image/sections/gallery/TimelineEvent) = Story 8.8 (epics.md:1154 „Page model iz Epic 7 7.4" — 8.8 PROŠIRUJE).

## Gotchas

- **G-1 (slug collision guard — politika-kolacica → Http404):** `PageDetailView` MORA baciti `Http404` za `slug=="politika-kolacica"` — taj dokument je vlasništvo `gdpr:cookie_policy` (7-1 SM-D9). Bez guard-a, neko ko ručno kreira `Page(slug="politika-kolacica")` red bi napravio drugi izvor istine. NIJE defensive-over-internal (slug je javni boundary). **NAPOMENA (posle CRITICAL-1/SM-D11):** kad je pages include premešten na KRAJ i18n_patterns, `/sr/politika-kolacica/` se sada DOSEGNE u gdpr include-u PRE pages catch-all-a → cookie policy radi normalno (200). G-1 guard ostaje VALIDAN i POTREBAN kao zaštita SAMO za scenario ručno-kreiranog `Page(slug="politika-kolacica")` reda (drugi izvor istine), NE kao primarni mehanizam routinga — taj posao sad radi redosled include-a.
- **G-2 (data migracija — popuni `_sr` kolone direktno):** `0004` `forward` koristi historical model (`apps.get_model`) → postavi `title_sr`/`body_sr` EKSPLICITNO (NE goli `title`/`body` accessor). Bar `_sr` MORA biti popunjen da fallback (MODELTRANSLATION_FALLBACK_LANGUAGES=("sr",)) vrati srpski. Mirror pages 0002 + brands 0003.
- **G-3 (catch-all slug ruta POSLEDNJA — UNUTAR fajla I PREKO include-ova; CRITICAL-1):** `path("<slug:slug>/", ...)` matchuje bilo koji 1-segment path. Django resolver first-match-wins top-to-bottom **PREKO svih include-ova** (jedna sploštena lista). DVA uslova: (1) catch-all POSLEDNJI u pages `urlpatterns` (POSLE `o-nama/`/`kontakt/`/`servis/`) inače shadow-uje pages statičke rute; (2) **`apps.pages.urls` include POSLEDNJI u config/urls.py i18n_patterns (POSLE gdpr :49)** inače catch-all shadow-uje `/sr/blog/` (blog :48) i `/sr/politika-kolacica/` (gdpr :49) → 7-1/blog TRAJNO 404. **Within-file ordering SAM NIJE dovoljan** — to je suština CRITICAL-1. Vidi SM-D11 + AC10. Budući rizik: svaka 1-segment ruta dodata u app PRE pages-a biva shadow-ovana → pages mora ostati poslednji include.
- **G-4 (footer regression — deljeno vlasništvo 1-8/5-4):** `footer.html` su dirale 1-8 (komponenta) + 5-4 (latest_blog_posts). DODAJ pravni red NEINVAZIVNO; NE menjaj 4 kolone, latest_blog_posts for-loop, copyright. Pazi na postojeće footer testove (test-ownership lekcija Epic 5).
- **G-5 (TranslationAdmin + prepopulated_fields — PRESEDAN: blog Story 5-1 BL-2):** `prepopulated_fields={"slug":("title",)}` radi na DEFAULT-locale `title` polju (modeltranslation registruje virtuelna `title_sr/hu/en`; prepopulated gleda goli `title` = default-locale accessor). **KONKRETAN PRESEDAN:** Story 5-1 (`5-1-blogpost-category-tag-modeli-admin-stub.md`, Gotcha BL-2, Task 7.2) je naišao na TAČNO ovu interakciju — `prepopulated_fields` na modeltranslation-registrovanom polju može baciti `admin.E030` („refers to 'title' which is not in Model._meta.fields"). 5-1 je razrešio opcijom (a): registrovao `PostAdmin(TranslationAdmin)` iz `modeltranslation.admin` (koja handluje prevedena polja) i **ZADRŽAO `prepopulated_fields`** — NIJE ga uklonio. 7.4 već specificira `PageAdmin(TranslationAdmin)` (SM-D7) → ista provereno-radeća kombinacija; Dev NE treba da otkriva ovo iznova. BL-2 fallback opcije ako ipak pukne na `check`: (b) usmeri prepopulated na base field ako modeltranslation verzija podržava, ili (c) ukloni `prepopulated_fields` (slug se unosi ručno) i dokumentuj — minorno. Verifikuj na `manage.py check` (Task 6.2/6.3).
- **G-6 (footer styling — NIKAD inline style):** ako pravni red treba styling → `.coric-footer__legal` BEM + `var(--...)` tokeni (project-context.md:312-322). Bootstrap utility klase OK. NIKAD `style="..."` magic vrednosti.
- **G-7 (modeltranslation reg PRE makemigrations):** `@register(Page)` u translation.py MORA postojati PRE `makemigrations pages` da `_sr/_hu/_en` kolone uđu u 0003.
- **G-8 (Page NIJE singleton — get_or_create na slug):** seed koristi `get_or_create(slug="politika-privatnosti")` (NE pk=1). Page ima više redova; slug je unique business key. NEMA save() pk=1 override (RAZLIKA od CookiePolicy/SiteSettings).
- **G-9 (makemigrations ne sme dotaknuti druge app-ove):** posle `makemigrations pages` → `makemigrations --check --dry-run` → „No changes detected" za sve ostale app-ove. Dodavanje Page modela menja SAMO pages migracije.
- **G-10 (slug ASCII / UI dijakritike):** slug `politika-privatnosti` (NE `politika-privatnošti`) ASCII (project-context.md:165). title/body/footer-link-tekst = pune dijakritike (Politika privatnosti / Politika kolačića).
- **G-11 (footer link kolačići → gdpr:cookie_policy NE pages:page_detail):** footer „Politika kolačića" MORA koristiti `{% url 'gdpr:cookie_policy' %}` (7-1 ruta). NE `{% url 'pages:page_detail' slug='politika-kolacica' %}` (taj slug → Http404 zbog G-1; i nema seed Page reda za njega).
- **G-12 (GET-only → POST 405):** `PageDetailView.http_method_names=["get","head","options"]` → POST/PUT/DELETE → HTTP 405 (mirror ContactView views.py:130).
- **G-13 (IMP — postojeća šišana latinica u footer.html):** `templates/partials/footer.html` ima DVE postojeće šišane string-ove (preddatiraju 7.4): `:9` `{% translate "Pocetna" %}` (aria-label) i `:80` `{% translate "Sva prava zadrzana." %}` (copyright). Project-context.md zabranjuje šišanu latinicu u UI. Pošto 7.4 ionako EDIT-uje footer (pravni red), ispravi i ove: `Pocetna`→`Početna`, `Sva prava zadrzana.`→`Sva prava zadržana.` (Task 8.4). Ovo su `{% translate %}` msgid-ovi → posle izmene `makemessages` (regeneracija `.po`) jer se menja msgid ključ. NE menjaj markup — SAMO tekst.
- **G-14 (0004 dependency = STVARNO ime 0003):** posle `makemigrations pages` proveri stvarno generisano ime 0003 fajla (`makemigrations` auto-imenuje; može biti `0003_page` ili `0003_<auto>`); uskladi `dependencies=[("pages","0003_...")]` u ručno pisanom 0004 sa TIM imenom. Pogrešan string → `NodeNotFoundError` pri `migrate`. (Task 4.1.)
- **G-15 (seed PLACEHOLDER marker — RISK-1 mitigacija):** 0004 `body_sr` NE sme biti goli Lorem Ipsum — MORA početi eksplicitnim `[PLACEHOLDER — pravni tekst MORA uneti biznis/pravnik pre go-live (RISK-1)]` markerom + `# TODO(RISK-1)` komentarom u migraciji (konvencija mirror pages 0002 `# TODO(OQ-1): placeholder`). Sprečava da neko deploy-uje Lorem placeholder kao pravu politiku privatnosti. Vezano za nasleđeni RISK-1 (Mihas legal sign-off pre go-live). (Task 4.2 / SM-D5 / AC5.)

## Open Questions

- **OQ-1 (RESOLVED) — hu/en seed jezici:** seed popunjava SAMO `_sr` (Lorem Ipsum pune dijakritike). hu/en se NE seed-uju → fallback na sr (MODELTRANSLATION_FALLBACK_LANGUAGES). Biznis unosi prave prevode kroz admin. Mirror 7-1 OQ-1 + pages 0002.
- **OQ-2 (DEFER) — SeoMeta inline na PageAdmin:** Page ima get_absolute_url → kvalifikuje se za SeoMeta GFK inline (6-1), ALI deferred (strana dobija <title>/meta kroz base.html + globalni {% seo_head %} fallback). Razmotriti u 8.8 (CMS-ifikacija) ili zasebnoj SEO closure story.
- **OQ-3 (DEFER) — verzionisanje politike privatnosti (audit istorija):** kao 7-1 OQ-3 — bez verzionisanja u v1. Page čuva trenutnu verziju; `updated_at` je jedini istorijski signal.
- **⚠️ RISK-1 (NASLEĐEN iz 7-1, OTVOREN — Mihas sign-off PRE go-live):** plain-text `body` (|linebreaks) možda legalno NEDOVOLJAN za pravu politiku privatnosti (treba strukturisani sadržaj: prikupljani podaci, pravni osnov, prava korisnika, kontakt DPO, period čuvanja). v1 odluka = plain-text (konzistentno blog/7-1 presedan + no-dep). Opcija B (sanitized rich HTML + bleach/nh3) ili rich-text → 8.7 čeka Mihas odluku. Seed body je PLACEHOLDER — pravni tekst MORA uneti biznis/pravnik pre go-live. **Mitigacija (G-15):** 0004 seed `body_sr` MORA sadržati eksplicitan `[PLACEHOLDER — ...pre go-live]` marker + `# TODO(RISK-1)` komentar (Task 4.2 / SM-D5) tako da je placeholder vizuelno očigledan i u admin-u i na javnoj strani — sprečava slučajan deploy Lorem teksta kao prave politike.
- **OQ-4 (DEFER) — migracija postojećih about/contact/service u Page:** 7.4 NE migrira (8.8 scope). Razmotriti da li „O nama"/„Servis"/„Kontakt" treba da postanu Page redovi (CMS-editable) u 8.8 — to je veći refactor (hero/sections/gallery/TimelineEvent polja + template rewiring).
