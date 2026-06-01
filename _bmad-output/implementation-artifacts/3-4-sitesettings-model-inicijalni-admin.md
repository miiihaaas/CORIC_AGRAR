---
story_id: "3.4"
story-key: 3-4-sitesettings-model-inicijalni-admin
title: SiteSettings Model + Inicijalni Admin
status: ready-for-dev
epic: 3
epic_num: 3
epic_title: Home & Static Pages
module: pages
created: 2026-06-01
last_modified: 2026-06-01
complexity: H
author: Mihas (SM autonomous; ČETVRTA i POSLEDNJA story Epic 3 — i PRVA story Epic 3 koja uvodi MODEL + MIGRACIJU + ADMIN. SiteSettings je site-wide singleton config model koji centralizuje kontakt podatke (adresa, telefon prodaje, telefon servisa, e-pošta, radno vreme, social URL-ovi) koji su trenutno HARDKODOVANI-TRANSLATABLE na više mesta (kontakt strana `_contact_info.html` SM-D5/IMP-SiteSettings marker, footer kontakt kolona, top-header IMP-4 servis-telefon placeholder). SM-D1 PLACEMENT: model živi u `apps/pages/models.py` (NE apps/core) — architecture.md:587-593 EKSPLICITNO mapira `pages/ models.py # ... SiteSettings` + `pages/ templatetags/site_settings.py`; epics.md:755-757 isto. RAZLOG: `apps/core` NE sme da bude DB-bearing content app (drži samo abstract base klase + utils + middleware; verifikovano live — core/models.py ima SAMO TimestampedModel+SluggedModel abstract); `apps/pages` je VEĆ instaliran, VEĆ je top-level „izlog" app, i do sada NEMA modela/migracija (PagesConfig.apps.py kaže „SiteSettings dolazi tek Story 3.4 → NEMA migracija") — ova story uvodi PRVU `apps/pages/migrations/`. SM-D2 SINGLETON: SELF-ROLLED (django-solo NIJE u pyproject.toml — NE dodaje se dep; YAGNI). Override `save()` → `self.pk = 1` + `classmethod load()` (get_or_create pk=1) + blokiran `delete()`. SM-D3 FIELDS: company_name, slogan (translatable), address (translatable), phone_sales, phone_service, email, working_hours (translatable), social_facebook (URLField), social_instagram (URLField) — DERIVAT iz onoga što `_contact_info.html`/footer/top-header danas renderuju. logo/favicon/hero_image_default ODLOŽENI na Epic 8 8.9 (SM-D7 wiring boundary; FR-45 logo/favicon/hero su admin-asset polja vezana za Epic 8 CMS). SM-D4 MIGRACIJE: schema CreateModel (0001) + DATA seed migracija (0002 RunPython sa reverse_code) koja kreira jedinu SiteSettings(pk=1) instancu sa TRENUTNIM hardkodovanim vrednostima (adresa „Vojvođanska 1, Basaid, Srbija" PUNI-dijakritik, +381 230 468 168, servis placeholder, prodaja@coricagrar.rs, radno vreme, social href="#" → prazni URL) tako da sajt nastavi da renderuje bez ručnog koraka. SM-D5 ACCESS: TEMPLATE TAG `{% site_setting "phone_sales" %}` (`apps/pages/templatetags/site_settings.py`) — NE context processor; epics.md:757 + architecture.md:593 EKSPLICITNO traže template tag; tag radi get-or-create lazy load i podržava translatable polja kroz aktivnu lokalu. SM-D6 ADMIN: registracija na POSTOJEĆI `admin.site` (mount-ovan kroz `path("admin/", admin.site.urls)` UNUTAR `i18n_patterns`, config/urls.py:25-31 → stvarni URL je locale-prefiksovan `/sr/admin/...`, NE bare `/admin/...`; testovi/smoke koriste `reverse("admin:pages_sitesettings_*")`; `/admin-coric/` custom slug je Epic 8 8.1, NE ova story) sa singleton-friendly ModelAdmin (has_add_permission False kad instanca postoji, has_delete_permission False, list_display/search_fields); modeltranslation auto-tabovi za translatable polja kroz translation.py. django-axes login hardening = Epic 8 8.1 (van scope-a). SM-D7 WIRING (KRITIČNA, mirror 3-3 boundary): WIRE-NOW kontakt-info + footer (epics.md:758 AC EKSPLICITNO „Footer i Kontakt strana koriste site_setting template tag umesto hard-coded vrednosti" — to JE deliverable ove story; RAZREŠAVA `_contact_info.html` IMP-SiteSettings marker iz 3-3 + footer kontakt kolonu). Top-header IMP-4 servis-telefon TAKOĐE wire (prirodno mesto). Home hero slogan NE wire (3-1 SM-D10 eksplicitno „slogan NE deferuje" — slogan ostaje hardcoded-translatable; logo/favicon/hero polja NISU na modelu u v1 → Epic 8). RISK TIER: HIGH — PRVA CreateModel migracija + DATA migracija (RunPython) + admin registracija u Epic 3; migracija je irreverzibilna state promena DB šeme; modeltranslation generiše _sr/_hu/_en kolone (3 polja × 3 lokala = 9 dodatnih kolona) što multiplikuje schema površinu; singleton invarijanta (tačno 1 red) je nova runtime garancija; wiring 3 template lokacije rizikuje regresiju renderovanja kontakt podataka. NIJE MEDIUM jer state-bearing migracija + data seed + admin + cross-template wiring zajedno prelaze prag.)
depends_on:
  - 1-2-multi-environment-settings-split-sa-django-environ  # INSTALLED_APPS (apps.pages već registrovan); modeltranslation PRE django.contrib.admin; MODELTRANSLATION_FALLBACK_LANGUAGES=("sr",)
  - 1-4-i18n-setup-sa-locale-url-routing-i-switcher          # LANGUAGES [sr,hu,en] → modeltranslation suffix-i; {% translate %}; LocaleMiddleware
  - 2-1-brand-series-category-subcategory-modeli             # apps/core/models.py TimestampedModel (REUSE base klasa); modeltranslation translation.py PATTERN (apps/brands/translation.py); admin.site.register PATTERN (apps/brands/admin.py); migrations discipline PRECEDENT
  - 3-1-home-strana-sa-svim-sekcijama                        # apps/pages/ app scaffold (PagesConfig + INSTALLED_APPS + urls.py app_name="pages"); home hero slogan (SM-D10 NE deferuje — NE wire); top-header IMP-4 servis placeholder kontekst
  - 3-3-kontakt-strana-sa-formom-i-mapom                     # `_contact_info.html` SM-D5 hardcoded-translatable + IMP-SiteSettings(Story 3-4) marker (OVA story razrešava); kontakt vrednosti (adresa/telefoni/email/radno vreme/social) = seed source; ContactView GET-only (NE menja se)
---

# Story 3.4: SiteSettings Model + Inicijalni Admin

Status: ready-for-dev

## Opis

As a **dev (koji gradi sajt) i Marijana (admin korisnik koji posle Epic 8 menja kontakt podatke)**,

I want **`SiteSettings` singleton model u `apps/pages/` koji centralizuje globalna podešavanja sajta (kontakt-info: adresa, telefon prodaje, telefon servisa, e-pošta, radno vreme; social: Facebook + Instagram URL), sa inicijalnim Django admin-om za uređivanje jedne jedine instance i `{% site_setting "..." %}` template tag-om**,

so that **kontakt strana, footer i top-header čitaju kontakt podatke iz JEDNE autoritativne lokacije (umesto hardkodovanih vrednosti raspršenih po template-ima), tako da promena telefona/adrese na jednom mestu propagira svuda — i razrešava se `IMP-SiteSettings(Story 3-4)` marker iz Story 3-3**.

Ovo je **ČETVRTA i POSLEDNJA story Epic 3 (Home & Static Pages)** i **PRVA story Epic 3 koja uvodi MODEL + MIGRACIJU + ADMIN** (Story 3-1/3-2/3-3 su bile čisto template/view strane bez modela). Do sada `apps/pages` NEMA nijedan model — ova story uvodi PRVU `apps/pages/migrations/`.

### IN SCOPE (šta ova story isporučuje)

1. **`SiteSettings` singleton model** u `apps/pages/models.py` (SM-D1/SM-D2/SM-D3) — nasleđuje `TimestampedModel` (REUSE `apps/core/models.py`); self-rolled singleton (pk=1 + `load()` classmethod).
2. **Schema migracija** `apps/pages/migrations/0001_initial.py` (CreateModel — manuelno reviewovana, SM-D4).
3. **DATA seed migracija** `0002_seed_sitesettings.py` (RunPython sa `reverse_code`, SM-D4) — kreira jedinu instancu sa TRENUTNIM hardkodovanim vrednostima tako da sajt renderuje bez ručnog admin koraka.
4. **modeltranslation registracija** `apps/pages/translation.py` (SM-D6) — `slogan`, `address`, `working_hours` postaju `_sr`/`_hu`/`_en` (auto-generisane kolone).
5. **`{% site_setting "field" %}` template tag** `apps/pages/templatetags/site_settings.py` (SM-D5) — lazy get-or-create, locale-aware za translatable polja. **PLUS** `|splitlines` filter (isti modul, SM-D10) za render `working_hours` kao `<ul>`/`<li>`.
6. **Singleton-friendly admin** `apps/pages/admin.py` (SM-D6) — registracija na POSTOJEĆI `admin.site`; `has_add_permission`/`has_delete_permission` guardovi; `list_display`; modeltranslation auto-tabovi.
7. **WIRING (SM-D7 — wire-now):** `_contact_info.html` (razrešava IMP-SiteSettings marker), `templates/partials/footer.html` kontakt kolona, i `templates/partials/header.html` top-header (IMP-4 servis placeholder) čitaju kroz `{% site_setting %}` umesto hardkodovanih literala.

### OUT OF SCOPE (eksplicitno — granice)

- **`/admin-coric/` custom admin URL slug + django-axes login hardening** = **Epic 8 Story 8.1** (`8-1-custom-admin-login-sa-rate-limiting`). Admin je danas mount-ovan na `path("admin/", admin.site.urls)` ALI UNUTAR `i18n_patterns` (config/urls.py:25-31, default `admin.site`) → stvarni URL je locale-prefiksovan `/sr/admin/...` (NE bare `/admin/...`; SM-D6). Ova story registruje `SiteSettings` na taj POSTOJEĆI `admin.site` — kad 8.1 promeni slug/login, registracija ide automatski (SM-D6). NE konfigurišemo custom admin site, NE django-axes.
- **`logo`, `favicon`, `hero_image_default` polja** (FR-45 „logotip, favicon, hero pozadine") = **Epic 8 Story 8.9** (`8-9-sitesettings-navigation-menu-admin`). epics.md:1174 EKSPLICITNO stavlja proširenje modela (logo/favicon/hero + `gdpr_banner_title`/`gdpr_banner_body` + `navigation` JSON) u 8.9. Ova story uvodi SAMO kontakt+social polja koja template-i DANAS koriste. NE dodajemo asset/image polja u v1 (YAGNI — nema template koji ih čita; home hero koristi static asset koji ne deferuje — 3-1 SM-D10). Vidi SM-D3/SM-D7 + OQ-2.
- **`social_youtube` polje** — NAMERNO IZOSTAVLJENO u v1. epics.md:755 nabraja `social_youtube` među SiteSettings poljima, ALI nijedan trenutni template (`footer.html`/`header.html`/`_contact_info.html`) NE renderuje YouTube link (verifikovano live — grep `youtube` ne vraća nijedan template hit). Dodavanje polja sad = YAGNI (nema čitača). Dodaje se u Epic 8 8.9 AKO biznis obezbedi YouTube kanal (OQ-1 kandidat). NE dodavati `social_youtube` u v1 (vidi SM-D3 + OQ-1).
- **GDPR baner polja / navigacioni meni JSON** = Epic 8 8.9 (+ Epic 7). Van scope-a.
- **Cache invalidation na save signal** (epics.md:1177) = Epic 8 8.9. Ova story NEMA caching (template tag radi prost query po request-u; ~1 red, trivijalno).
- **Home hero slogan** — NE wire na SiteSettings (3-1 SM-D10 lock: „slogan NE deferuje"; slogan ostaje hardcoded-translatable u `_home_hero.html`). `slogan` polje POSTOJI na modelu (epics.md:755 implicitno + buduća upotreba), ali se v1 NE čita iz template-a (forward-compat admin polje). Vidi SM-D7.
- **`Page`, `HomeSection`, `AboutTimelineEvent`, `GalleryImage` modeli** (architecture.md:588) = Epic 7/8 (CMS za O nama/statičke strane). Ova story uvodi SAMO `SiteSettings`.
- **Funkcionalna kontakt forma / Lead model** = Epic 4 (već van scope-a po 3-3).

### Princip

Jedan singleton model + 2 migracije (schema + data seed) + translation.py + template tag + singleton admin + wiring 3 template lokacije. NEMA novog CSS-a, NEMA novog JS-a, NEMA novih URL-ova/view-ova, NEMA forme. Model nasleđuje `TimestampedModel` (REUSE). Sva user-facing UI ostaje translatable; translatable model polja kroz modeltranslation. Slug/ASCII pravila se NE tiču (nema URL-a). Pune dijakritike (č/ć/ž/š/đ) u seed vrednostima i admin verbose_name-ovima. NEMA defensive validacije (project-context.md:358), NEMA premature abstrakcije (NE django-solo dep za jedan singleton).

### Strukturna arhitektura — repository delta

**5 NEW fizičkih fajlova + 3 WIRING EDIT (template) + 1 docstring EDIT (`apps/pages/apps.py`) + 1 INSTALLED_APPS no-op (verifikacija) + 0 DELETE + 0 CSS + 0 JS.**

| Path | Tip | Razlog |
|---|---|---|
| `apps/pages/models.py` | NOVO | `class SiteSettings(TimestampedModel)` — singleton (pk=1 override `save()` + `load()` classmethod + `delete()` koji RAISE-uje, NE silent no-op — SM-D2/AC2); polja: company_name, slogan, address, phone_sales, phone_service, email, working_hours, social_facebook (URLField), social_instagram (URLField); `__str__` → „Podešavanja sajta"; `Meta.verbose_name`/`verbose_name_plural`. NE FK (nema relacija); NE `get_absolute_url` (config model, nije content sa stranom — vidi SM-D3 napomenu). |
| `apps/pages/translation.py` | NOVO | modeltranslation `@register(SiteSettings)` `TranslationOptions(fields=("slogan", "address", "working_hours"))` — mirror `apps/brands/translation.py` pattern. Generiše `slogan_sr/hu/en`, `address_sr/hu/en`, `working_hours_sr/hu/en` pri makemigrations. |
| `apps/pages/admin.py` | NOVO | `@admin.register(SiteSettings)` singleton-friendly `ModelAdmin` (`has_add_permission` → False kad red postoji; `has_delete_permission` → False; `list_display=("company_name", "phone_sales", "email", "updated_at")`; `search_fields`; `changelist_view` override → redirect na change-view jedinog objekta kroz `reverse()` — SM-D6/AC6). modeltranslation auto-tabovi (NE dodaj ručno). Mirror `apps/brands/admin.py` registracija stil (ali sa singleton guardovima). |
| `apps/pages/templatetags/__init__.py` | NOVO | Prazan — Python package marker za templatetags (apps/pages NEMA templatetags dir danas — verifikovano live). |
| `apps/pages/templatetags/site_settings.py` | NOVO | `register = template.Library()`; `@register.simple_tag def site_setting(field_name)` → `SiteSettings.load()` + `getattr(obj, field_name)` (locale-aware za translatable polja jer modeltranslation virtuelni atribut čita aktivnu lokalu). **PLUS** `@register.filter splitlines` (SM-D10) → vraća listu nepraznih `.strip()`-ovanih linija (za render `working_hours` kao `<ul>`/`<li>`). |
| `apps/pages/migrations/__init__.py` | NOVO | Python package marker (migrations dir ne postoji danas — verifikovano live). |
| `apps/pages/migrations/0001_initial.py` | GENERISANO + MANUAL REVIEW | `makemigrations pages` — CreateModel `SiteSettings` sa SVIM poljima UKLJUČUJUĆI modeltranslation `_sr/_hu/_en` kolone (jer translation.py je registrovan PRE makemigrations). Dev MANUELNO reviewuje (project-context.md:221). |
| `apps/pages/migrations/0002_seed_sitesettings.py` | NOVO (ručno pisan) | RunPython data migracija sa `reverse_code` — kreira `SiteSettings(pk=1)` sa trenutnim vrednostima (vidi SM-D4 seed tabela). reverse_code briše pk=1 red. |
| `templates/pages/partials/_contact_info.html` | EDIT (WIRING) | Razreši `IMP-SiteSettings(Story 3-4)` marker: zameni hardkodovane vrednosti (adresa, tel prodaja, tel servis, email, social href) sa `{% site_setting "..." %}`. **Radno vreme:** stari 3-redni `<dl>` (`:46-59`) → `<ul>` koji loopuje preko `working_hours|splitlines` (SM-D10). `{% load site_settings %}`. Adresa/radno vreme su translatable (čitaju aktivnu lokalu). Ukloni IMP marker (ili promeni u „RESOLVED"). |
| `templates/partials/footer.html` | EDIT (WIRING) | Footer kontakt kolona (`:45` tel, `:46` mailto, `:48` address, `:52`/`:57` social) → `{% site_setting %}`. epics.md:758 AC EKSPLICITNO „Footer ... koristi site_setting". `{% load site_settings %}`. NAPOMENA: footer adresa danas šišana „Vojvodjanska" → posle wiring-a čita iz seed-a koji je PUNI-dijakritik „Vojvođanska" (popravlja OQ-6 dug iz 3-3 kao nuspojavu). |
| `templates/partials/header.html` | EDIT (WIRING) | Top-header IMP-4 servis placeholder (`:25-29`) + prodaja tel (`:21-24`) + adresa (`:18-20`) + social (`:31`/`:36`) → `{% site_setting %}`. `{% load site_settings %}`. Razreši IMP-4 marker. NAPOMENA: header adresa takođe šišana → seed je PUNI-dijakritik. NE diraj nav/logo/search delove header-a (van scope-a). |
| `apps/pages/apps.py` | EDIT (docstring) | Ažuriraj zastareli docstring „NEMA modela u v1 … → NEMA migracija" — NETAČNO posle ove story (uvodi `SiteSettings` + migracije). Prepiši da odražava stvarno stanje (project-context.md:351 — nema lažnih komentara). NE menjaj `PagesConfig` klasu/`name`/`verbose_name`. |
| `apps/pages/tests/*` | NOVO (TEA) | RED-phase testovi (vidi Testing). Dev NE piše testove. |
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | EDIT | `3-4-sitesettings-model-inicijalni-admin` → `ready-for-dev`. SM handoff tracking (NIJE deliverable). |

**NETAKNUTO (regression guards):** `apps/core/models.py` (TimestampedModel REUSE — NE menja se); `apps/pages/views.py` (`HomeView`/`AboutView`/`ContactView` — NE čitaju SiteSettings u v1; ostaju netaknuti — SM-D5 template tag radi bez view context-a); `apps/pages/urls.py` (nema novih URL-ova); `config/settings/*` (apps.pages VEĆ u INSTALLED_APPS; modeltranslation VEĆ konfigurisan — NEMA settings izmene); `config/urls.py` (admin VEĆ mount-ovan na `/admin/`; NEMA promene — SM-D6); `pyproject.toml` (NEMA novog dep — NE django-solo; SM-D2); `templates/pages/partials/_home_hero.html` (slogan NE wire — 3-1 SM-D10; SM-D7); sve ostale `_home_*`/`_about_*`/`_contact_form`/`_contact_map` partials; sve CSS/JS (0 novih, 0 izmena); `apps/{brands,products,search,media_pipeline}/*`.

## Kriterijumi prihvatanja

**AC1 — `SiteSettings` model u `apps/pages/models.py`; nasleđuje `TimestampedModel`; tačna polja; `__str__`; `system check` čist**

- **Given** `apps/core/models.py` `TimestampedModel` (Story 2.1, REUSE base klasa); `apps/pages` app registrovan (Story 3.1); modeltranslation u INSTALLED_APPS PRE admin (Story 1.2/2.1)
- **When** kreiram `class SiteSettings(TimestampedModel)` u `apps/pages/models.py`
- **Then** model MORA imati TAČNO ova polja (plain osim gde je označeno translatable):
  - `company_name` — `CharField` (npr. max_length=200), default „Ćorić Agrar"
  - `slogan` — `CharField` (max_length=255), **TRANSLATABLE** (modeltranslation; forward-compat admin polje — NE čita se u template v1, SM-D7)
  - `address` — `CharField`/`TextField`, **TRANSLATABLE**
  - `phone_sales` — `CharField` (telefon prodaje, plain)
  - `phone_service` — `CharField` (telefon servisa, plain, blank dozvoljen jer je placeholder); `help_text` flag-uje non-final placeholder dok biznis ne unese realni broj (SM-D11; `gettext_lazy`)
  - `email` — `EmailField`
  - `working_hours` — `TextField`, **TRANSLATABLE** (multi-line plain text, jedan „Dan: vreme" red po liniji; render kao `<ul>`/`<li>` kroz `|splitlines` filter — SM-D10)
  - `social_facebook` — `URLField(blank=True)` (prazno = link se SAKRIVA, SM-D8a; seed prazan jer danas href="#"); `help_text` flag-uje non-final placeholder (SM-D11; `gettext_lazy`)
  - `social_instagram` — `URLField(blank=True)` (prazno = link se SAKRIVA, SM-D8a); `help_text` flag-uje non-final placeholder (SM-D11)
  - (nasleđeno iz `TimestampedModel`: `created_at`, `updated_at`)
- **And** `__str__` vraća stabilan string (npr. „Podešavanja sajta") — NE per-instance dinamičan (singleton)
- **And** `Meta.verbose_name = "Podešavanja sajta"`, `Meta.verbose_name_plural = "Podešavanja sajta"` (puni dijakritik; singleton — plural isto)
- **And** NEMA FK (model nema relacija); NEMA `get_absolute_url` (config model, nije content sa javnom stranom — izuzetak od project-context.md:158 „get_absolute_url na content modelima"; SiteSettings nije content model)
- **And** `uv run python manage.py check` exit 0; NEMA defensive validacije (project-context.md:358)

**AC2 — Singleton invarijanta: tačno jedan red (pk=1); `save()` forsira pk=1; `load()` classmethod; `delete()` RAISE-uje (SM-D2)**

- **Given** AC1; django-solo NIJE dep (pyproject.toml verifikovano — self-rolled singleton; SM-D2)
- **When** implementiram singleton pattern bez dodavanja dependency-ja
- **Then**:
  - `save()` je override-ovan tako da UVEK postavi `self.pk = 1` pre `super().save()` → ne mogu postojati 2 reda
  - `classmethod load()` vraća jedinu instancu kroz `get_or_create(pk=1)` (lazy — kreira sa default vrednostima ako ne postoji; bezbedno za template tag pre nego što seed migracija prođe u test bazi)
  - **`delete()` je override-ovan da RAISE-uje** (NE silent no-op — silent no-op je footgun: poziv tiho ne uradi ništa pa caller misli da je obrisano). Konkretno: instance `delete()` baca jasan izuzetak — preporuka `django.core.exceptions.PermissionDenied` ILI namenski `SiteSettings.objects.exists()`-aware exception sa porukom da se singleton ne briše. Singleton se ne briše kroz app kod; admin delete je odvojeno blokiran AC6.
  - **CAVEAT (invariant boundary — KRITIČNO za Epic 9 9-7 sample-seed fixtures):** override instance `.delete()` NE pokriva `QuerySet.delete()` (`SiteSettings.objects.all().delete()`), `loaddata`, ni `bulk_create` — ti putevi zaobilaze instance metode i save() override. Singleton garancija (tačno 1 red) na nivou app koda počiva na: (1) `save()` pk=1 force, (2) instance `delete()` raise, (3) admin `has_delete_permission=False` kao UI guard. Ako Epic 9 9-7 fixture/seed ubaci 2. red kroz `loaddata`/`bulk_create`, to NIJE pokriveno ovim override-om — fixture MORA targetirati pk=1 (`update_or_create` ili eksplicitan `pk=1`) da ne ubaci 2. red. Dokumentovano da Dev/9-7 zna granicu.
  - Dva uzastopna `SiteSettings(...).save()` rezultuju u `SiteSettings.objects.count() == 1` (drugi update-uje pk=1, NE kreira pk=2)
- **And** `SiteSettings.load()` na praznoj bazi vraća instancu (get_or_create) — NE baca `DoesNotExist`

**AC3 — Schema migracija `0001_initial` (CreateModel) + modeltranslation `_sr/_hu/_en` kolone; manuelno reviewovana; reverzibilna (SM-D4)**

- **Given** AC1 + `apps/pages/translation.py` registrovan (AC5) PRE `makemigrations`
- **When** pokrenem `uv run python manage.py makemigrations pages`
- **Then**:
  - Generiše se `apps/pages/migrations/0001_initial.py` sa `CreateModel("SiteSettings", ...)`
  - Migracija UKLJUČUJE modeltranslation kolone: `slogan_sr`, `slogan_hu`, `slogan_en`, `address_sr/hu/en`, `working_hours_sr/hu/en` (jer translation.py registruje translatable polja PRE makemigrations — Story 2.1 D2 pattern)
  - `apps/pages/migrations/__init__.py` postoji (package marker)
  - Dev MANUELNO reviewuje fajl (project-context.md:221 — manual review PRE commit-a); `uv run python manage.py migrate --plan` prikazuje plan
  - `uv run python manage.py migrate pages 0001` primeni, `migrate pages zero` reverzuje čisto (CreateModel je auto-reverzibilan)
- **And** migracija + model promene se commit-uju ZAJEDNO (atomic; project-context.md:223)
- **And** NIJE editovana posle apply-a (project-context.md:226 — nova migracija za korekcije)

**AC4 — DATA seed migracija `0002_seed_sitesettings` (RunPython sa `reverse_code`) — kreira jedinu instancu sa trenutnim vrednostima (SM-D4)**

- **Given** AC3 (0001 šema postoji); SM-D4 seed tabela (trenutne hardkodovane vrednosti iz `_contact_info.html`/footer/top-header)
- **When** kreiram `apps/pages/migrations/0002_seed_sitesettings.py` kao RunPython data migraciju
- **Then**:
  - `dependencies = [("pages", "0001_initial")]`
  - `forward` funkcija (kroz `apps.get_model("pages", "SiteSettings")` — NE direktan import; migration-safe) `update_or_create(pk=1, defaults={...})` sa vrednostima iz SM-D4 seed tabele (PUNE dijakritike na `_sr` poljima; `_hu`/`_en` SMEJU ostati prazni — fallback na sr, vidi AC10 seed politika; `address_hu`/`address_en` mogu biti identični sr jer je adresa ista u svim lokalima)
  - **`reverse_code`** definisan (project-context.md:227) — briše `pk=1` red (`filter(pk=1).delete()`)
  - Posle `migrate` → `SiteSettings.objects.count() == 1` i `SiteSettings.load().phone_sales == "+381 230 468 168"`
  - `migrate pages 0001` (reverz na pre-seed) ukloni red bez greške
- **And** seed adresa je PUNI-dijakritik „Vojvođanska 1, Basaid, Srbija" (NE šišana — popravlja OQ-6 dug; sr lokala)
- **And** social URL-ovi seed-uju kao PRAZNI (`""`) jer template-i danas koriste `href="#"` placeholder (OQ-1 realni URL-ovi biznis input)
- **And** **NON-FINAL placeholder marker (production-readiness, FR-5):** placeholder seed vrednosti (`phone_service = "+381 XXX XXX XXX"`, prazni social URL-ovi, placeholder `working_hours`) MORAJU nositi grep-abilan marker da se ne otpreme tiho u produkciju. Konkretno: u `0002_seed_sitesettings.py` dodaj komentar `# TODO(OQ-1): placeholder — biznis popunjava realne vrednosti pre go-live` iznad tih polja u `defaults` dict-u, I/ILI dodaj `help_text` na ta model polja (`phone_service`, `social_facebook`, `social_instagram`) koji flag-uje da su placeholder dok ih biznis ne unese kroz admin. (Ovo je dozvoljen WHY-komentar po project-context.md:351 — flag-uje non-final stanje pending biznis input, nije „added for issue" tip.) Marker omogućava grep pre go-live deploy-a.

**AC5 — modeltranslation registracija `apps/pages/translation.py` — `slogan`/`address`/`working_hours` translatable (SM-D6)**

- **Given** AC1; `apps/brands/translation.py` PATTERN (Story 2.1); LANGUAGES [sr,hu,en]
- **When** kreiram `apps/pages/translation.py` sa `@register(SiteSettings) class SiteSettingsTranslationOptions(TranslationOptions): fields = ("slogan", "address", "working_hours")`
- **Then**:
  - Posle `makemigrations` (AC3) model ima virtuelna polja `slogan_sr/hu/en`, `address_sr/hu/en`, `working_hours_sr/hu/en`
  - `{{ site_settings.address }}` u aktivnoj `sr` lokali vraća `address_sr`; u `hu` → `address_hu` (sa fallback na sr po `MODELTRANSLATION_FALLBACK_LANGUAGES`)
  - plain polja (phone_sales, phone_service, email, social_*, company_name) NISU translatable (jedna vrednost za sve lokale)
- **And** mirror `apps/brands/translation.py` strukture (import iz `apps.pages.models`)

**AC6 — Singleton-friendly admin (`apps/pages/admin.py`) na POSTOJEĆI `admin.site`; modeltranslation auto-tabovi; nema add kad red postoji; nema delete (SM-D6)**

- **Given** AC1-AC5; `apps/brands/admin.py` registracija PATTERN; admin mount-ovan UNUTAR `i18n_patterns` (config/urls.py:25-26 — `path("admin/", admin.site.urls)` je INSIDE `i18n_patterns(...)`, pa su stvarni admin URL-ovi locale-prefiksovani: `/sr/admin/pages/sitesettings/...`, NE bare `/admin/...`; `/admin-coric/` custom slug je Epic 8 8.1, van scope-a)
- **When** kreiram `apps/pages/admin.py` sa `ModelAdmin` za `SiteSettings`
- **Then**:
  - `SiteSettings` je registrovan na `admin.site` (`@admin.register(SiteSettings)` ili `admin.site.register`) — pojavljuje se u admin app listi
  - `has_add_permission(request)` → `False` kad `SiteSettings.objects.exists()` (singleton — nema „Add another"; posle seed-a uvek True postoji → add skriven)
  - `has_delete_permission(request, obj=None)` → `False` (singleton se ne briše)
  - `list_display` = npr. `("company_name", "phone_sales", "email", "updated_at")` (project-context.md:200 — list_display obavezan); `search_fields` definisan (project-context.md:200)
  - modeltranslation AUTOMATSKI rendera jezičke tabove za `slogan`/`address`/`working_hours` (NE dodavati ručno — project-context.md:201)
  - URL-ovi se razrešavaju kroz Django `reverse("admin:pages_sitesettings_changelist")` i `reverse("admin:pages_sitesettings_change", args=[obj.pk])` (locale-resolution-safe — NE hardkodovati `/admin/...` ni `/sr/admin/...` jer je admin pod `i18n_patterns`)
  - **changelist REDIREKTUJE na change-view jedinog objekta** (standard singleton-admin UX — locked, NE „ILI 1 red"): override `changelist_view(request, extra_context=None)` koji, kad `SiteSettings.objects.exists()`, vraća `HttpResponseRedirect(reverse("admin:pages_sitesettings_change", args=[SiteSettings.load().pk]))` (koristi `reverse()` po C1 fix-u — NIKAD hardkodovan put). Korisnik nikad ne vidi 1-redni changelist; klik na „Podešavanja sajta" vodi direktno na edit formu. change-view → HTTP 200 za superuser.
- **And** django-axes login hardening + `/admin-coric/` slug NISU u scope-u (Epic 8 8.1 — dokumentovano; SM-D6)
- **And** `verbose_name` „Podešavanja sajta" se prikazuje u admin app listi (puni dijakritik)

**AC7 — `{% site_setting "field" %}` template tag (`apps/pages/templatetags/site_settings.py`) — locale-aware lazy load (SM-D5)**

- **Given** AC1-AC2 (`load()`); epics.md:757 + architecture.md:593 (template tag, NE context processor — SM-D5)
- **When** kreiram `apps/pages/templatetags/site_settings.py` (+ `__init__.py` package marker)
- **Then**:
  - `register = template.Library()`; `@register.simple_tag def site_setting(field_name): return getattr(SiteSettings.load(), field_name)`
  - `{% load site_settings %}{% site_setting "phone_sales" %}` u template-u renderuje `+381 230 468 168`
  - Za translatable polje: `{% site_setting "address" %}` u `sr` lokali → sr vrednost; u `hu` → hu (fallback sr) — jer `getattr(obj, "address")` čita aktivnu lokalu kroz modeltranslation
  - Tag radi BEZ view context-a (ne zahteva da view stavi `site_settings` u context — SM-D5; zato view-ovi ostaju netaknuti)
  - Tag radi i kad seed nije primenjen u test bazi (`load()` get_or_create vraća default instancu — AC2)
- **And** NEMA context processor-a u `TEMPLATES` (SM-D5 — settings se NE menjaju)

**AC8 — WIRING: `_contact_info.html` razrešava IMP-SiteSettings marker; čita kroz `{% site_setting %}`; render identičan/bolji (SM-D7)**

- **Given** AC7 (tag radi); `templates/pages/partials/_contact_info.html` (Story 3-3) sa `{# IMP-SiteSettings(Story 3-4) #}` markerom (verifikovano live `:3`); seed (AC4)
- **When** wire-ujem `_contact_info.html` na `{% site_setting %}`
- **Then**:
  - `{% load site_settings %}` na vrhu
  - Adresa → `{% site_setting "address" %}` (translatable, PUNI-dijakritik iz seed-a)
  - Telefon prodaje: vidljiv tekst i `tel:` href čitaju iz `phone_sales`. **LOCKED PATTERN (SM-D8):** seed drži čitljivu vrednost SA razmacima („+381 230 468 168"); vidljiv tekst je renderuje takvu, a `tel:` href koristi Django built-in `|cut:" "` filter da skine razmake — npr. `{% site_setting "phone_sales" as ps %}<a href="tel:{{ ps|cut:" " }}">{{ ps }}</a>`. ZERO extra util (YAGNI — `cut` je ugrađen filter). Isto i za `phone_service`.
  - Telefon servisa → `phone_service`
  - E-pošta → `email` (`mailto:` + tekst)
  - Radno vreme → `working_hours` (translatable) — render kao `<ul class="coric-contact-info__hours-list">` gde je SVAKI neprazan red vrednosti jedan `<li>` (SM-D10). Konkretno: `{% site_setting "working_hours" as wh %}{% for line in wh|splitlines %}<li>{{ line }}</li>{% endfor %}` (filter `splitlines` iz `apps/pages/templatetags/site_settings.py` — SM-D10). Postojeći 3-redni `<dl>` (Ponedeljak–Petak / Subota / Nedelja) se ZAMENJUJE ovim `<ul>`-om. ⛔ NEMA `|safe`/raw HTML u polju (auto-escape; XSS-safe); `<ul>` ostaje semantički element (zadovoljava postojeći 3-3 test — vidi Task 9 napomenu).
  - Social Facebook/Instagram href → `social_facebook`/`social_instagram`. **LOCKED PATTERN (SM-D8a — HIDE WHEN EMPTY):** prazan `URLField` u `href="{% site_setting 'social_facebook' %}"` daje `href=""` (gore od trenutnog `href="#"`), pa se link SAKRIVA kad je polje prazno: `{% site_setting "social_facebook" as fb %}{% if fb %}<a href="{{ fb }}">…</a>{% endif %}`. Isto za `social_instagram`. Seed je prazan (OQ-1) → ikone se NE renderuju dok biznis ne unese URL kroz admin. NE renderovati `href=""` ni `href="#"`.
  - `IMP-SiteSettings(Story 3-4)` marker je UKLONJEN ili promenjen u „RESOLVED Story 3-4" (machine-findable da je dug zatvoren)
  - GET `/sr/kontakt/` → HTTP 200; kontakt-info sekcija renderuje iste/ispravne vrednosti
- **And** sve UI labele (h3 „Adresa"/„Telefon prodaje"/...) OSTAJU `{% translate %}` (samo VREDNOSTI prelaze na site_setting; labele su statične UI)
- **And** ćirilice NEMA; sr pune dijakritike

**AC9 — WIRING: footer + top-header čitaju iz `{% site_setting %}` (epics.md:758 AC; SM-D7)**

- **Given** AC7; `templates/partials/footer.html` kontakt kolona (`:45-48`, social `:52/57`); `templates/partials/header.html` top-header (`:18-29`, social `:31/36`, IMP-4 servis `:25`)
- **When** wire-ujem footer + top-header
- **Then**:
  - Footer: `{% load site_settings %}`; tel prodaja → `phone_sales` (`tel:` href kroz `|cut:" "` — SM-D8), mailto → `email`, address → `address` (PUNI-dijakritik iz seed-a — popravlja šišanu „Vojvodjanska"), social href → `social_*` (HIDE WHEN EMPTY — SM-D8a; prazan seed → ikone se ne renderuju)
  - Top-header: `{% load site_settings %}`; adresa → `address`, prodaja tel → `phone_sales` (`tel:` href kroz `|cut:" "`), **servis tel IMP-4 placeholder → `phone_service`** (razreši IMP-4 marker `header.html:25`), social href → `social_*` (HIDE WHEN EMPTY — SM-D8a)
  - IMP-4 marker je uklonjen/„RESOLVED"
  - GET `/sr/` (home, koji uključuje header+footer) → HTTP 200; header+footer renderuju kontakt podatke iz SiteSettings
  - NE diraj nav linkove/logo/search/language-switcher delove header-a/footer-a (van scope-a — samo kontakt VREDNOSTI)
- **And** home hero slogan u `_home_hero.html` NIJE menjan (3-1 SM-D10 — slogan NE deferuje; SM-D7)
- **And** regresija: `pages:home`/`pages:contact`/`pages:about` i dalje HTTP 200 sva 3 locale

**AC10 — i18n/lokalizacija: translatable polja render-uju po lokali; nema hardcoded ćirilice; sva 3 locale HTTP 200**

- **Given** AC5 (translatable polja) + AC8/AC9 (wiring)
- **When** posetim `/sr/kontakt/`, `/hu/kontakt/`, `/en/kontakt/` (i `/sr|hu|en/` home)
- **Then**:
  - Sva 3 locale → HTTP 200
  - `address`/`working_hours` render-uju lokalizovanu vrednost iz odgovarajuće `_<lang>` kolone (fallback sr ako prazno — `MODELTRANSLATION_FALLBACK_LANGUAGES=("sr",)`, verifikovano live `config/settings/base.py:124`)
  - **SEED POLITIKA (locked, SM-D4):** seed MORA popuniti `_sr` (puni dijakritik). `_hu`/`_en` SMEJU ostati prazni — prazna hu/en kolona NE ruši render jer modeltranslation fallback-uje na sr (`MODELTRANSLATION_FALLBACK_LANGUAGES=("sr",)`). Tj. uslov je „NEMA prazne kolone koja RUŠI render", a NE „nijedna kolona ne sme biti prazna"; prazna hu/en je PRIHVATLJIVA jer pada na sr fallback. (Za `address` hu/en vrednost je ionako identična sr — adresa je ista u svim lokalima; vidi SM-D4.)
- **And** NEMA ćirilice, NEMA šišane latinice na sr renderovanim vrednostima
- **And** plain polja (telefoni/email/social) ISTI u svim lokalima

## Tasks / Subtasks

> **Konvencija:** `[TEA-RED]` = Test Architect piše test PRE implementacije (mora FAIL). `[DEV-GREEN]` = Developer implementira da test prođe. **Dev NIKAD ne piše testove.** Migracije: makemigrations + MANUAL REVIEW + migrate je DEV task (project-context.md:218-227).

- [x] **Task 1 — `SiteSettings` model (AC1, AC2)** `[DEV-GREEN]`
  - [x] 1.1 Kreiraj `apps/pages/models.py`: `class SiteSettings(TimestampedModel)` (import `TimestampedModel` iz `apps.core.models`) sa poljima iz AC1.
  - [x] 1.2 `__str__` → „Podešavanja sajta"; `Meta.verbose_name`/`verbose_name_plural` = „Podešavanja sajta" (puni dijakritik).
  - [x] 1.3 Singleton: override `save()` (`self.pk = 1; super().save(...)`); `@classmethod load()` (`get_or_create(pk=1)[0]`); override `delete()` koji **RAISE-uje** (preporuka `PermissionDenied`, NE silent no-op — SM-D2/AC2). NEMA defensive validacije.
  - [x] 1.4 `uv run python manage.py check` exit 0.
  - [x] 1.5 Ažuriraj `apps/pages/apps.py` docstring — trenutno tvrdi „NEMA modela u v1 (SiteSettings dolazi tek Story 3.4) → NEMA migracija", što je NETAČNO posle ove story (uvodi `SiteSettings` model + migracije). Prepiši rečenicu da odražava stvarno stanje (npr. „Sadrži `SiteSettings` singleton model (Story 3.4) + migracije."). project-context.md:351 — nema lažnih/zastarelih komentara.

- [x] **Task 2 — modeltranslation registracija (AC5)** `[DEV-GREEN]`
  - [x] 2.1 Kreiraj `apps/pages/translation.py`: `@register(SiteSettings)` `TranslationOptions(fields=("slogan", "address", "working_hours"))` (mirror `apps/brands/translation.py`).

- [x] **Task 3 — Schema migracija (AC3)** `[DEV-GREEN]`
  - [x] 3.1 `uv run python manage.py makemigrations pages` → `0001_initial.py` (+ `__init__.py` package marker). Translation.py MORA biti gotov (Task 2) PRE ovog koraka da kolone `_sr/_hu/_en` uđu u 0001.
  - [x] 3.2 **MANUAL REVIEW** `0001_initial.py` (verifikuj CreateModel + 9 modeltranslation kolona + nasleđena created_at/updated_at; project-context.md:221).
  - [x] 3.3 `uv run python manage.py migrate --plan` (provera) → `migrate pages`.

- [x] **Task 4 — DATA seed migracija (AC4)** `[DEV-GREEN]`
  - [x] 4.1 Ručno napiši `apps/pages/migrations/0002_seed_sitesettings.py` — RunPython `forward` (`apps.get_model` + `update_or_create(pk=1, defaults=SM-D4 seed)`) + `reverse_code` (delete pk=1). `dependencies=[("pages","0001_initial")]`. **Dodaj NON-FINAL placeholder marker** (AC4/SM-D11): `# TODO(OQ-1): placeholder — biznis popunjava realne vrednosti pre go-live` iznad placeholder polja (`phone_service`, social URL-ovi, `working_hours`) u `defaults`. I/ILI `help_text` na ta model polja (Task 1.1) koji flag-uje placeholder.
  - [x] 4.2 **MANUAL REVIEW** + `migrate pages` → `SiteSettings.load().phone_sales` popunjen; `count()==1`.
  - [x] 4.3 Verifikuj reverz: `migrate pages 0001` ukloni red, `migrate pages 0002` ga vrati (idempotent update_or_create).

- [x] **Task 5 — Template tag (AC7) + `splitlines` filter (SM-D10)** `[DEV-GREEN]`
  - [x] 5.1 Kreiraj `apps/pages/templatetags/__init__.py` (prazan) + `site_settings.py` (`simple_tag site_setting` → `SiteSettings.load()` + getattr).
  - [x] 5.2 U istom modulu dodaj `@register.filter splitlines` (SM-D10): prima string, vraća listu nepraznih `.strip()`-ovanih linija (`[ln.strip() for ln in (value or "").splitlines() if ln.strip()]`). Koristi se za render `working_hours` kao `<ul>`/`<li>` (Task 7.2).

- [x] **Task 6 — Singleton admin (AC6)** `[DEV-GREEN]`
  - [x] 6.1 Kreiraj `apps/pages/admin.py`: `@admin.register(SiteSettings)` `ModelAdmin` sa `has_add_permission`/`has_delete_permission` guardovima + `list_display` + `search_fields` (mirror `apps/brands/admin.py` registracija; singleton guardovi novi).
  - [x] 6.1a Override `changelist_view` da REDIREKTUJE na change-view jedinog objekta (singleton UX — AC6): kad `SiteSettings.objects.exists()` → `HttpResponseRedirect(reverse("admin:pages_sitesettings_change", args=[SiteSettings.load().pk]))`. Koristi `reverse()` (NE hardkodovan `/admin/...` put — C1 fix/SM-D6).
  - [x] 6.2 Smoke: prijavi se kao superuser i otvori admin kroz `reverse("admin:pages_sitesettings_changelist")` (i `..._change` za jedini objekat) → 200; modeltranslation tabovi prisutni. NE hardkoduj `/admin/...` ni `/sr/admin/...` (admin je pod `i18n_patterns`; SM-D6).

- [x] **Task 7 — WIRING `_contact_info.html` (AC8)** `[DEV-GREEN]`
  - [x] 7.1 `{% load site_settings %}`; zameni adresa/tel-prodaja/tel-servis/email/social vrednosti `{% site_setting %}` tagom; `tel:` href koristi built-in `|cut:" "` (SM-D8 locked: čitljiv tekst SA razmacima, href BEZ razmaka); social hide-when-empty (SM-D8a/AC8); ukloni/„RESOLVED" IMP-SiteSettings marker. Labele ostaju `{% translate %}`.
  - [x] 7.2 **Radno vreme (SM-D10):** zameni postojeći 3-redni `<dl>` (`:46-59`) sa `<ul class="coric-contact-info__hours-list">` koji loopuje preko `{% site_setting "working_hours" as wh %}{% for line in wh|splitlines %}<li>{{ line }}</li>{% endfor %}`. Filter `splitlines` se dodaje u `apps/pages/templatetags/site_settings.py` (Task 5.2). ⛔ NEMA `|safe`. `<ul>` zadovoljava postojeći 3-3 test (Task 9 napomena).

- [x] **Task 8 — WIRING footer + top-header (AC9)** `[DEV-GREEN]`
  - [x] 8.1 `footer.html` kontakt kolona → `{% site_setting %}` (`{% load %}`; tel/email/address/social).
  - [x] 8.2 `header.html` top-header → `{% site_setting %}` (adresa/prodaja/servis IMP-4/social); ukloni/„RESOLVED" IMP-4 marker. NE diraj nav/logo/search.
  - [x] 8.3 NE menjaj `_home_hero.html` (slogan — 3-1 SM-D10).

- [x] **Task 9 — RED-phase testovi (AC1-AC10)** `[TEA-RED]`
  - [x] 9.1 `test_sitesettings_model.py` — polja postoje, `__str__`, TimestampedModel nasleđe, NE FK.
  - [x] 9.2 `test_sitesettings_singleton.py` — `save()` forsira pk=1 (count==1 posle 2 save), `load()` get_or_create, `delete()` **RAISE-uje izabrani izuzetak** (`pytest.raises(PermissionDenied)` ili izabran izuzetak — NE silent no-op; AC2/SM-D2), i red OSTAJE (count==1 posle pokušaja delete).
  - [x] 9.3 `test_sitesettings_migrations.py` — 0001 CreateModel + `_sr/_hu/_en` kolone postoje; 0002 seed popunjava pk=1; reverz čist (migracija reverzibilnost — `call_command('migrate')` u test ILI introspect).
  - [x] 9.4 `test_sitesettings_translation.py` — `slogan`/`address`/`working_hours` translatable (postoje `address_sr/hu/en`); plain polja nisu translatable.
  - [x] 9.5 `test_site_setting_tag.py` — `{% site_setting %}` renderuje vrednost; locale-aware za address; radi bez view context-a; radi na load() default.
  - [x] 9.6 `test_sitesettings_admin.py` — registrovan na admin.site; has_add False kad red postoji; has_delete False; list_display definisan. Admin URL-ovi MORAJU se graditi kroz `reverse("admin:pages_sitesettings_changelist")` i `reverse("admin:pages_sitesettings_change", args=[obj.pk])` (admin je pod `i18n_patterns` — hardkodovan `/admin/...` ili `/sr/admin/...` je ZABRANJEN; SM-D6); superuser klijent → changelist REDIREKTUJE (302) na change-view jedinog objekta (singleton UX — AC6/SM-D6); change-view 200.
  - [x] 9.7 `test_contact_info_wired.py` — `_contact_info.html` koristi site_setting (NE hardkodovan literal); IMP marker uklonjen; `/sr/kontakt/` 200. **Radno vreme (SM-D10):** verifikuj da je render `<ul>` sa `<li>` po liniji iz `working_hours` (NE više `<dl>`); filter `splitlines` daje neprazne linije; auto-escape (NEMA `|safe`).
  - [x] 9.7a **REGRESIJA — postojeći 3-3 test (SM-D10):** `test_contact_info_has_working_hours` (`apps/pages/tests/test_contact_info.py:95-105`) traži `<(dl|ul|ol|table)\b` — novi `<ul>` render ga ZADOVOLJAVA, pa TEA NE menja taj test (ostaje green). TEA samo potvrdi da i dalje prolazi posle wiring-a. (Story 3-4 OWNS contact-info re-wiring i SMELA bi da ga menja, ali pošto `<ul>` već zadovoljava očekivanje semantičkog elementa, izmena NIJE potrebna.)
  - [x] 9.8 `test_footer_header_wired.py` — footer+top-header koriste site_setting; IMP-4 uklonjen; `/sr/` 200; `_home_hero.html` slogan NETAKNUT (regresija). **Empty-social branch (SM-D8a):** sa praznim `social_facebook`/`social_instagram` (seed default), render NE sadrži `href=""` ni `href="#"` social link (link skriven); sa popunjenim URL-om → link renderovan. `tel:` href BEZ razmaka (`|cut:" "` — SM-D8).
  - [x] 9.9 `test_locale_render.py` — sva 3 locale 200; translatable polja render po lokali; nema ćirilice.

- [x] **Task 10 — Dev manual gate (NE pytest)** `[DEV-GREEN]`
  - [x] 10.1 `uv run python manage.py check` + `migrate --plan` čisti.
  - [x] 10.2 Vizuelni smoke: `/sr/kontakt/` + `/sr/` renderuju kontakt podatke; admin change strana (kroz `reverse("admin:pages_sitesettings_change", ...)`; faktički `/sr/admin/pages/sitesettings/...` jer je admin pod `i18n_patterns`) editabilna; promena telefona u admin-u → propagira na kontakt+footer+header (manual potvrda DRY autoritativnosti).
  - [x] 10.3 Commit model + obe migracije + translation.py ZAJEDNO (atomic; project-context.md:223).

## Dev Notes

### SM Decisions (SM-D log)

**SM-D1 — PLACEMENT: `apps/pages/models.py` (NE `apps/core`).** architecture.md:587-593 EKSPLICITNO mapira `pages/ models.py # ... SiteSettings` + `pages/ templatetags/site_settings.py`; epics.md:755 isto („kreiram `apps/pages/models.py` sa `SiteSettings`"). `apps/core` drži SAMO abstract base klase + utils + middleware (verifikovano live — `core/models.py` ima isključivo `TimestampedModel`+`SluggedModel` `abstract=True`; project-context.md:105 „shared base klase … uvek prvi instaliran"). `apps/core` NE sme da bude DB-bearing content/config app (cross-app import pravilo + „uvek prvi instaliran" → ne sme zavisiti od ničega). `apps/pages` je VEĆ top-level „izlog" app (3-1 SM-D6), VEĆ instaliran, do sada BEZ modela — ova story uvodi PRVU `apps/pages/migrations/`. **Task hint je predlagao apps/core kao „najverovatnije" — ali AUTHORITATIVE epics.md+architecture.md kažu apps/pages; sledi se epic.**

**SM-D2 — SINGLETON: SELF-ROLLED (NE django-solo).** `pyproject.toml` NEMA `django-solo` (verifikovano live — dependencies su django/anymail/axes/bootstrap5/csp/environ/htmx/modeltranslation/ratelimit/template-partials/pdf2image/pillow/psycopg/python-magic/sorl/whitenoise). project-context.md zabranjuje dodavanje dep-a osim ako već postoji + „no premature abstraction" (435). Za JEDAN singleton model, self-rolled pattern je trivijalan i idiomatičan: override `save()` (`self.pk = 1`), `classmethod load()` (`get_or_create(pk=1)`), `delete()` koji **RAISE-uje** (NE silent no-op — silent no-op je footgun: caller misli da je obrisano). Preporuka: `delete()` baca `django.core.exceptions.PermissionDenied` sa jasnom porukom. NE dodavati django-solo. **GRANICA (invariant boundary):** instance `delete()` override NE pokriva `QuerySet.delete()`/`loaddata`/`bulk_create` (ti putevi zaobilaze instance metode i save() override). Singleton garancija počiva na save() pk=1 + instance delete() raise + admin `has_delete_permission=False` (UI guard). Relevantno za Epic 9 9-7 sample-seed fixtures — fixture MORA targetirati pk=1 (`update_or_create`/eksplicitan pk=1) da ne ubaci 2. red; vidi AC2 caveat.

**SM-D3 — FIELDS: kontakt+social SAMO (logo/favicon/hero ODLOŽENI Epic 8 8.9).** Polja DERIVAT iz onoga što `_contact_info.html` (3-3) + footer + top-header DANAS renderuju: company_name, slogan (translatable, forward-compat), address (translatable), phone_sales, phone_service, email, working_hours (translatable), social_facebook (URLField), social_instagram (URLField). **logo/favicon/hero_image_default su FR-45 polja koja epics.md:1174 EKSPLICITNO stavlja u Story 8.9** (admin asset/image polja vezana za Epic 8 CMS); home hero koristi static asset koji 3-1 SM-D10 NE deferuje. Dodavanje image polja sad = YAGNI (nema template koji ih čita). **`social_youtube` (epics.md:755) je TAKOĐE namerno izostavljen u v1** — nijedan trenutni template (footer/header/`_contact_info.html`) ne renderuje YouTube link (verifikovano live), pa nema čitača; dodaje se u Epic 8 8.9 ako biznis obezbedi kanal (OQ-1 kandidat). `get_absolute_url` se NE implementira (SiteSettings je config, ne content sa javnom stranom — izuzetak od project-context.md:158 koje važi za content modele; dokumentovano). NEMA FK (model nema relacija).

**SM-D4 — MIGRACIJE: schema (0001) + DATA seed (0002 RunPython + reverse_code).** epics.md:759 „Pre prvog deploy-a, postoji fixture sa default SiteSettings instancom" → realizujemo kao DATA migraciju (NE odvojen JSON fixture; data migracija je auto-primenjena na deploy `migrate` step, project-context.md:224 — pouzdanije od ručnog loaddata). RunPython `forward` kroz `apps.get_model` (migration-safe, NE direktan import) + `reverse_code` (delete pk=1; project-context.md:227 obavezan reverse_code za data migracije).

**SM-D4 seed tabela (trenutne vrednosti — single source za migraciju 0002):**

> **SEED POLITIKA hu/en (locked):** seed popunjava SAMO `_sr`. `_hu`/`_en` translatable kolone SMEJU ostati prazne — modeltranslation fallback-uje na sr (`MODELTRANSLATION_FALLBACK_LANGUAGES=("sr",)`, verifikovano `config/settings/base.py:124`), pa prazna hu/en kolona NE ruši render (vidi AC10). NE izmišljati lažne prevode (YAGNI). Izuzetak: `address_hu`/`address_en` SMEJU biti identični sr (adresa je ista u svim lokalima — nije „lažan prevod"). Biznis kasnije popunjava realne hu/en kroz admin (OQ-4).

| Polje | Vrednost (sr) | hu / en | Izvor |
|---|---|---|---|
| `company_name` | Ćorić Agrar | (isto, plain) | brand |
| `slogan` (transl.) | Prijatelj koji razume zemlju! | prazno (fallback sr) | `_home_hero.html:13` (forward-compat; NE čita se v1) |
| `address` (transl.) | Vojvođanska 1, Basaid, Srbija | identično sr (adresa ista) ili prazno (fallback sr) | `_contact_info.html:15` PUNI-dijakritik (NE šišana — popravlja OQ-6) |
| `phone_sales` | +381 230 468 168 | (plain) | `_contact_info.html:23` / footer:45 / header:23 |
| `phone_service` | +381 XXX XXX XXX (placeholder) | (plain) | `_contact_info.html:31` / header:28 IMP-4 (OQ-1 realni broj) |
| `email` | prodaja@coricagrar.rs | (plain) | `_contact_info.html:39` / footer:46 |
| `working_hours` (transl.) | multi-line, jedan red po liniji (newline `\n`-separated): `Ponedeljak–Petak: 08–16h` / `Subota: 08–13h` / `Nedelja: zatvoreno` (3 linije; PUNE dijakritike; render kao `<ul>`/`<li>` kroz `|splitlines` — SM-D10) | prazno (fallback sr; biznis prevodi kroz admin — OQ-4) | `_contact_info.html:46-58` (zamenjuje stari `<dl>`) |
| `social_facebook` | „" (prazno) | (plain) | footer/header `href="#"` (OQ-1 realni URL) |
| `social_instagram` | „" (prazno) | (plain) | isto |

**SM-D5 — ACCESS: TEMPLATE TAG `{% site_setting "field" %}` (NE context processor).** epics.md:757 EKSPLICITNO „kreiram `apps/pages/templatetags/site_settings.py` sa `{% site_setting "phone_sales" %}` template tag-om"; architecture.md:593 `templatetags/site_settings.py`. **Justifikacija (zašto tag, ne context processor):** (1) epic AUTHORITATIVELY traži tag; (2) tag drži view-ove NETAKNUTIM (HomeView/ContactView ne moraju ubaciti `site_settings` u context — manje izmena, manje regresije; context processor bi tražio settings izmenu `TEMPLATES` + svaki render bi platio query čak i strane bez kontakt podataka); (3) `simple_tag` + `load()` get-or-create je lazy i locale-aware za modeltranslation polja (getattr čita aktivnu lokalu). **NE menjamo `config/settings/*` `TEMPLATES` context_processors** (verifikovano live — samo django default + i18n + auth + messages).

**SM-D6 — ADMIN: POSTOJEĆI `admin.site` (locale-prefiksovan kroz `i18n_patterns`); singleton guardovi; modeltranslation auto-tabovi.** Admin je mount-ovan na `path("admin/", admin.site.urls)` ALI UNUTAR `i18n_patterns(...)` (config/urls.py:25-31 — verifikovano live; default `admin.site`, NE custom AdminSite). **POSLEDICA (KRITIČNO za testove/smoke):** stvarni admin URL-ovi su LOCALE-PREFIKSOVANI — `/sr/admin/pages/sitesettings/`, NE bare `/admin/pages/sitesettings/`. Bare `/admin/...` put bi vratio 404. Zato je u admin testovima i smoke koraku **hardkodovanje admin putanje ZABRANJENO** (ni `/admin/...` ni `/sr/admin/...`); MORA se koristiti Django `reverse()` sa admin URL imenima koja su locale-resolution-safe: `reverse("admin:pages_sitesettings_changelist")` i `reverse("admin:pages_sitesettings_change", args=[obj.pk])`. `/admin-coric/` custom slug + django-axes login lockout su **Epic 8 Story 8.1** (`8-1-custom-admin-login-sa-rate-limiting`; sprint-status backlog). Ova story registruje na POSTOJEĆI `admin.site` (mirror `apps/brands/admin.py` koji koristi `admin.site.register`) — kad 8.1 promeni slug/AdminSite, registracija ide automatski (`reverse()` ostaje validan jer je vezan za URL ime, ne putanju). Singleton guardovi: `has_add_permission` → False kad red postoji, `has_delete_permission` → False. **`changelist_view` override REDIREKTUJE na change-view jedinog objekta** (standard singleton-admin UX; korisnik ide pravo na edit formu, ne na 1-redni changelist) kroz `reverse("admin:pages_sitesettings_change", args=[SiteSettings.load().pk])` (NIKAD hardkodovan put — C1/SM-D6). modeltranslation auto-rendera jezičke tabove (project-context.md:201 — NE ručno). `list_display`/`search_fields` obavezni (project-context.md:200).

**SM-D7 — WIRING SCOPE: WIRE-NOW kontakt-info + footer + top-header servis (slogan/logo/favicon/hero NE).** epics.md:758 Story 3.4 AC EKSPLICITNO: „**Then** Footer i Kontakt strana koriste site_setting template tag umesto hard-coded vrednosti" → wiring JE deliverable ove story (mirror kako su 3-2/3-3 razrešili prethodne placeholder-e u istoj story koja ih „odgovara"). Ovo je PRIRODNO mesto da se razreši `IMP-SiteSettings(Story 3-4)` marker (`_contact_info.html:3`) + IMP-4 servis placeholder (`header.html:25`). **WIRE:** `_contact_info.html`, `footer.html` kontakt kolona, `header.html` top-header (adresa/prodaja/servis/social). **NE WIRE:** home hero slogan (`_home_hero.html` — 3-1 SM-D10 lock „slogan NE deferuje"; `slogan` polje postoji na modelu kao forward-compat admin polje ali se v1 NE čita iz template-a); logo/favicon/hero (nisu polja u v1 — SM-D3, Epic 8 8.9). Footer/header adrese danas šišana „Vojvodjanska" → posle wiring-a čitaju PUNI-dijakritik seed → popravlja OQ-6 dug kao nuspojavu.

**SM-D8 — `tel:` href format (LOCKED — NE „Dev bira").** `_contact_info.html`/footer/header danas drže `href="tel:+381230468168"` (BEZ razmaka) ali vidljiv tekst „+381 230 468 168" (SA razmacima). Seed `phone_sales`/`phone_service` drže JEDNU čitljivu vrednost SA razmacima. **ODLUKA (locked):** seed `phone_sales = "+381 230 468 168"` (čitljivo, za vidljiv tekst), a u `tel:` href koristi Django **built-in `|cut:" "` filter** da skine razmake: `{% site_setting "phone_sales" as ps %}<a href="tel:{{ ps|cut:" " }}">{{ ps }}</a>`. `cut` je ugrađen Django template filter — ZERO extra util (YAGNI), NE telefon-parser. Isto i za `phone_service`. Bitno: render čitljiv tekst SA razmacima + klikabilan `tel:` link BEZ razmaka.

**SM-D8a — prazan social URL: HIDE WHEN EMPTY (LOCKED).** `social_facebook`/`social_instagram` seed-uju kao prazni (`""`, OQ-1 — realni URL biznis input). Prost render `href="{% site_setting 'social_facebook' %}"` na praznom polju daje `href=""` što je GORE od trenutnog `href="#"` (prazan href referencira tekuću stranu). **ODLUKA (locked):** SAKRIJ link kad je polje prazno umesto da renderuješ broken href — `{% site_setting "social_facebook" as fb %}{% if fb %}<a href="{{ fb }}">…</a>{% endif %}`. Isto za `social_instagram`. Posledica: dok biznis ne unese realne URL-ove kroz admin (OQ-1), social ikone se NE renderuju (čistije od mrtvog `href="#"`/`href=""`). Primeni u `_contact_info.html` + footer + header (AC8/AC9). NE renderovati `href=""` ni `href="#"`.

**SM-D9 — base klasa: `TimestampedModel` (REUSE; NE `PublishableModel`).** Model nasleđuje `TimestampedModel` (`created_at`/`updated_at`) iz `apps/core/models.py`. `PublishableModel` se pominje u project-context.md:152 ali NE POSTOJI u `apps/core/models.py` (verifikovano live — samo Timestamped+Slugged) i ne bi imao smisla za singleton config (nema publish state). `SluggedModel` se NE koristi (config nema slug/URL).

**SM-D10 — `working_hours` RENDER (KRITIČNA — single-field → `<ul>` kroz `splitlines` filter).** PROBLEM: `_contact_info.html` (3-3) danas renderuje radno vreme kao 3-redni `<dl>` (Ponedeljak–Petak / Subota / Nedelja, svaki `<dt>`/`<dd>`), a model ima JEDNO `working_hours` translatable polje. ODLUKA (decisive, locked): **`working_hours` je multi-line plain-text `TextField`** — JEDAN „Dan: vreme" red po liniji, newline-separated, PUNE dijakritike. Render: **`<ul>` gde je svaki neprazan red jedan `<li>`**, kroz TINY custom filter dodat u `apps/pages/templatetags/site_settings.py` (isti modul kao `site_setting` tag — Task 5):
- **Filter ime:** `splitlines`. **Modul:** `apps/pages/templatetags/site_settings.py` (`@register.filter`). **Ponašanje:** prima string, vraća listu nepraznih, `.strip()`-ovanih linija (`[ln.strip() for ln in value.splitlines() if ln.strip()]`); na `None`/prazno vraća praznu listu.
- **Template upotreba** (u `_contact_info.html`, Task 7): `{% site_setting "working_hours" as wh %}<ul class="coric-contact-info__hours-list">{% for line in wh|splitlines %}<li>{{ line }}</li>{% endfor %}</ul>`.
- **Zašto `<ul>` a ne `<dl>`:** Django template ne može `.split("\n")` nativno; `|linebreaksbr` ne daje listu (daje `<br>` blob). Jedno translatable polje ne nosi strukturu para `<dt>/<dd>` bez parsiranja delimitera (krhko, i18n-fragilno). `<ul>` od linija je najjednostavniji semantički render (YAGNI), auto-escape (⛔ NIKAD `|safe` — XSS), locale-aware (modeltranslation getattr čita aktivnu lokalu), i ostaje JEDAN od dozvoljenih semantičkih elemenata.
- **REGRESIJA — postojeći 3-3 test `test_contact_info_has_working_hours` (`apps/pages/tests/test_contact_info.py:95-105`):** taj test traži `<(dl|ul|ol|table)\b` — `<ul>` ga ZADOVOLJAVA, NE treba ga menjati. (Story 3-4 legitimno OWNS contact-info re-wiring, pa BI smela da ga menja, ali pošto `<ul>` već prolazi, test ostaje NETAKNUT — manje regresije.)
- **Seed (SM-D4):** `working_hours` vrednost mora biti newline-separated multi-line format (vidi ažuriranu SM-D4 seed tabelu).

**SM-D11 — NON-FINAL placeholder marker (production-readiness, FR-5).** Seed vrednosti `phone_service = "+381 XXX XXX XXX"`, prazni `social_facebook`/`social_instagram`, i placeholder `working_hours` su BIZNIS-INPUT-PENDING (OQ-1) — nisu finalne. Da se ne otpreme tiho u produkciju, ZAHTEVA se grep-abilan marker: (1) komentar `# TODO(OQ-1): placeholder — biznis popunjava realne vrednosti pre go-live` u `0002_seed_sitesettings.py` iznad tih polja, I/ILI (2) `help_text` na model poljima (`phone_service`, `social_facebook`, `social_instagram`) koji flag-uje non-final stanje (help_text je vidljiv Marijani u adminu → prirodan poziv na akciju). Ovo je dozvoljen WHY-komentar (project-context.md:351 — flag-uje skriveno ograničenje „placeholder pending biznis input", NE „added for issue #" tip koji je zabranjen). Cilj: pre go-live deploy-a grep `TODO(OQ-1)` / pregled help_text-a otkriva nepopunjena polja. (Napomena: project-context.md:352 zabranjuje generičke `# TODO: refactor` komentare — ovaj je specifičan, traceable na OQ-1, i flag-uje production-readiness blocker, pa je opravdan izuzetak.)

### Project Structure Notes

- `apps/pages/` dobija PRVI put: `models.py`, `admin.py`, `translation.py`, `migrations/`, `templatetags/` (do sada samo `apps.py`/`urls.py`/`views.py`/`tests/`).
- modeltranslation auto-discovery učitava `apps/pages/translation.py` pri startup-u (jer `apps.pages` u INSTALLED_APPS PRE django.contrib.admin — base.py:34/48 verifikovano). 9 dodatnih `_sr/_hu/_en` kolona ulazi u 0001 jer translation.py prethodi makemigrations.
- Admin je mount-ovan UNUTAR `i18n_patterns` (config/urls.py:25-31), pa su stvarni admin URL-ovi locale-prefiksovani (`/sr/admin/pages/sitesettings/`), NE bare `/admin/...` (taj bi 404). `/admin-coric/` custom slug je Epic 8 8.1. Test/smoke MORA koristiti `reverse("admin:pages_sitesettings_changelist")` / `reverse("admin:pages_sitesettings_change", args=[obj.pk])` (NE hardkodovan put — SM-D6).

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-3.4] — model fields, template tag, „Footer i Kontakt koriste site_setting", fixture
- [Source: _bmad-output/planning-artifacts/epics.md#Story-8.9] — logo/favicon/hero/GDPR/navigation = Epic 8 boundary (SM-D3/SM-D7)
- [Source: _bmad-output/planning-artifacts/architecture.md:587-593] — `apps/pages/models.py SiteSettings` + `templatetags/site_settings.py` placement (SM-D1)
- [Source: _bmad-output/planning-artifacts/architecture.md:179] — `/admin-coric/` custom slug (aspirational; Epic 8)
- [Source: _bmad-output/project-context.md:148-158] — model base klase, FK, modeltranslation; :196-202 admin; :218-227 migrations discipline; :358 no defensive
- [Source: apps/core/models.py] — `TimestampedModel` (REUSE; NEMA PublishableModel)
- [Source: apps/brands/translation.py] — modeltranslation PATTERN; [Source: apps/brands/admin.py] — register PATTERN
- [Source: config/settings/base.py:28-51,69-83,113-130] — INSTALLED_APPS, TEMPLATES (no extra context processor), LANGUAGES, MODELTRANSLATION_FALLBACK
- [Source: config/urls.py:25-31] — admin mount `path("admin/", admin.site.urls)` UNUTAR `i18n_patterns` → stvarni URL je locale-prefiksovan `/sr/admin/...` (NE bare `/admin/...`); testovi koriste `reverse("admin:pages_sitesettings_*")` (SM-D6)
- [Source: templates/pages/partials/_contact_info.html:3,15-74] — IMP-SiteSettings marker + seed vrednosti
- [Source: templates/partials/header.html:18-41] — top-header IMP-4 servis + adresa + social; [Source: templates/partials/footer.html:45-57] — footer kontakt kolona
- [Source: templates/pages/partials/_home_hero.html:13] — slogan (NE wire; 3-1 SM-D10)
- [Source: pyproject.toml:6-22] — NEMA django-solo (SM-D2)

### Open Questions (OQ)

- **OQ-1 (biznis sadržaj — seed vrednosti):** Realni `phone_service` (servis telefon — danas placeholder `+381 XXX XXX XXX`), realni `social_facebook`/`social_instagram` URL-ovi (danas prazno/`href="#"`), i finalno `working_hours` (placeholder radno vreme). Seed koristi placeholder/prazne vrednosti; biznis (Marijana) popunjava kroz admin posle deploy-a (zato i postoji admin). NE blokira story — seed je bezbedan placeholder. **Production-readiness guard (SM-D11):** ta placeholder polja nose grep-abilan marker (`# TODO(OQ-1)` u 0002 migraciji + `help_text` flag) da se ne otpreme tiho u produkciju — pre go-live deploy-a grep/help_text otkriva nepopunjena polja.
- **OQ-2 (logo/favicon/hero polja — Epic 8 8.9 boundary):** Da li biznis želi logo/favicon/hero upravljanje kroz SiteSettings ranije od Epic 8? Default: NE u v1 (epics.md:1174 stavlja ih u 8.9; YAGNI — nema template koji ih čita; home hero static asset ne deferuje). Ako se traži, to je correct-course za 8.9, ne ova story.
- **OQ-3 (telefon format — SM-D8) — RAZREŠENO (locked):** Seed telefon SA razmacima (čitljivo) za vidljiv tekst; `tel:` href skida razmake kroz built-in `|cut:" "` filter (`tel:{{ ps|cut:" " }}`). NE parser util (YAGNI). Vidi SM-D8 + AC8.
- **OQ-4 (hu/en prevodi translatable seed-a) — RAZREŠENO (fallback politika):** Seed popunjava SAMO `_sr`. `_hu`/`_en` ostaju prazni — modeltranslation fallback-uje na sr (`MODELTRANSLATION_FALLBACK_LANGUAGES=("sr",)`, verifikovano `config/settings/base.py:124`), pa prazna hu/en NE ruši render (AC10). NE izmišljaju se lažni prevodi (YAGNI). Jedini izuzetak: `address_hu`/`address_en` SMEJU biti identični sr (adresa je ista u svim lokalima). Biznis popunjava realne hu/en kroz admin posle deploy-a. Vidi SM-D4 seed politika + AC10.

### Testing notes (šta TEA pokriva — RED phase)

- **Model:** polja postoje + tipovi; `TimestampedModel` nasleđe (`created_at`/`updated_at`); `__str__` stabilan; NEMA FK; NEMA get_absolute_url.
- **Singleton (SM-D2):** `save()` forsira pk=1 (count==1 posle 2 instance save); `load()` get_or_create vraća instancu na praznoj bazi; `delete()` RAISE-uje (NE silent no-op) i red ostaje. Napomena: instance `delete()` override NE pokriva `QuerySet.delete()`/`loaddata`/`bulk_create` (invariant boundary — vidi AC2 caveat; relevantno za Epic 9 9-7).
- **Migracije (SM-D4):** 0001 CreateModel ima `_sr/_hu/_en` kolone (`address_sr` itd.); 0002 seed popunjava pk=1 (`load().phone_sales`); reverz čist (RunPython reverse_code briše red); migracija reverzibilnost.
- **modeltranslation (AC5):** `slogan`/`address`/`working_hours` translatable; plain polja nisu.
- **Template tag (AC7):** `{% site_setting %}` renderuje vrednost; locale-aware za address (sr vs hu); radi bez view context-a; radi na load() default (pre seed-a u test bazi).
- **Admin (AC6):** registrovan na admin.site; `has_add_permission` False kad red postoji; `has_delete_permission` False; `list_display` definisan; changelist REDIREKTUJE (302) na change-view jedinog objekta (singleton UX), change-view 200 za superuser kroz `reverse("admin:pages_sitesettings_changelist")` / `reverse("admin:pages_sitesettings_change", args=[obj.pk])` (admin je pod `i18n_patterns` → NIKAD hardkodovan `/admin/...` put; SM-D6).
- **Wiring (AC8/AC9):** `_contact_info.html` + footer + top-header koriste `{% site_setting %}` (NE hardkodovan literal); radno vreme render `<ul>`/`<li>` kroz `working_hours|splitlines` (SM-D10 — zadovoljava postojeći 3-3 `test_contact_info_has_working_hours` koji ostaje NETAKNUT); IMP-SiteSettings + IMP-4 markeri uklonjeni; `_home_hero.html` slogan NETAKNUT (regresija); `/sr/kontakt/` + `/sr/` 200.
- **i18n (AC10):** sva 3 locale 200; translatable polja render po lokali; nema ćirilice/šišane latinice na sr.
- **TEA test DB:** modeltranslation kolone zahtevaju migracije primenjene; seed migracija (0002) se primenjuje u test setup-u — TEA verifikuje seed kroz migraciju ILI kroz `load()` default (oba puta). Telefon/email VREDNOSTI nisu prevodive.

## Risk-Tier Self-Assessment

**TIER: HIGH.**

**Obrazloženje:** Ovo je PRVA story u Epic 3 (i prva posle Epic 2 domain modela) koja kombinuje VIŠE state-bearing rizik faktora odjednom:
1. **CreateModel schema migracija** — irreverzibilna DB šema promena; modeltranslation multiplikuje površinu (3 translatable polja × 3 lokala = 9 dodatnih kolona u 0001).
2. **DATA seed migracija (RunPython)** — runtime data promena sa reverse_code; mora biti idempotentna (update_or_create) i migration-safe (`apps.get_model`, NE direktan import).
3. **Singleton invarijanta** — nova runtime garancija (tačno 1 red); pogrešan save() override → duplikati ili broken admin.
4. **Admin registracija** — singleton permission guardovi; pogrešan guard → admin nedostupan ili omogućava delete singleton-a.
5. **Cross-template WIRING (3 lokacije)** — `_contact_info.html` + footer + top-header; regresija renderovanja kontakt podataka vidljiva na home + kontakt + svakoj strani (header/footer su global).

NIJE MEDIUM: za razliku od 3-1/3-2/3-3 (0 migracija, 0 modela), ova story uvodi šemu + podatke + admin + globalni template wiring zajedno. Migration discipline (manual review, reverse_code), singleton testovi, i wiring regresija su obavezni gate-ovi. Mitigacija: model je mali (9 polja, bez FK), singleton pattern je well-known, seed je placeholder (nema osetljivih podataka), wiring je vrednost-zamena (ne strukturna).

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
