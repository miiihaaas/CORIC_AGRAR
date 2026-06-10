---
story-id: 8-9-sitesettings-navigation-menu-admin
story_key: 8-9-sitesettings-navigation-menu-admin
story_id_dotted: 8.9
epic: 8
module: pages (apps/pages)
title: "SiteSettings + Navigation Menu Admin"
status: review
risk_tier: LOW
language: Srpski (latinica)
created: 2026-06-10
created_by: SM (autonomous, YOLO)
depends_on:
  - 3-4    # SiteSettings singleton model + SiteSettingsAdmin (TranslationAdmin) + site_setting tag — IZVOR (VEĆ radi)
  - 8-1    # admin na /admin-coric/ (axes lockout)
  - 8-2    # RBAC: pages.sitesettings EKSPLICITNO IZOSTAVLJEN iz EDITOR_CONTENT_MODELS (Superadmin-only)
  - 7-1    # CookiePolicy singleton (gdpr) — NE dira se
  - 7-2    # GDPR consent banner (templates/gdpr/_consent_banner.html, hardcoded {% translate %}) — RECONCILE izvor banner teksta
  - 8-8    # prethodna pages story (PageAdmin) — isti fajl apps/pages/admin.py; PageAdmin NETAKNUT
forward_dep: []
migrations: 0
new_dependencies: 0
---

# Story 8.9: SiteSettings + Navigation Menu Admin

Status: ready-for-dev

## Story

As a **Marijana** (sadržaj-urednik / admin),
I want **da kroz admin menjam opšta podešavanja sajta (naziv firme, kontakt, social, radno vreme — per locale za translatable polja) i da znam gde se nalazi navigacioni meni**,
so that **kontakt informacije i podešavanja ostaju ažurni bez dev intervencije, a promene se odmah vide na svim stranama**.

## Opis

**DEVETA i POSLEDNJA Epic 8 story** — zatvara admin-CRUD niz (8.4 Brand → 8.5 Category/Subcategory → 8.6 Product → 8.7 Post → 8.8 Page → **8.9 SiteSettings + navigacija marker**). Nadograđuje POSTOJEĆI `apps/pages/admin.py:SiteSettingsAdmin` (3-4 — singleton `TranslationAdmin`, VEĆ pun funkcionalan; vidi „Postojeće stanje").

**REAL-CODE-WINS RECONCILIATION (KRITIČNO — epics:1167–1177 napisan PRE implementacije, sadrži 3 faktički netačne premise vs živi kod):**

1. **`SiteSettings` admin VEĆ POSTOJI i pun je (3-4).** Singleton `TranslationAdmin` sa `has_add_permission`/`has_delete_permission` guardovima + `changelist_view` redirect na change. Sva kontakt polja (`company_name`, `slogan`, `address`, `phone_sales`, `phone_service`, `email`, `working_hours`, `social_facebook`, `social_instagram`) VEĆ editabilna; `slogan`/`address`/`working_hours` translatable (sr/hu/en tabovi auto). **Epics:1173 „Story 3.4 dodaje admin za SiteSettings" je VEĆ ISPUNJENO** → 8.9 NIJE „napravi admin", nego „verifikuj/zaključaj postojeći + reši reconciliation razlike".

2. **`SiteSettings` NEMA `logo`/`favicon`/`hero pozadine` polja (epics:1175 ih traži, ALI ona NE postoje).** Logo je HARDKODOVAN static asset u `templates/partials/header.html:61` (`{% static 'img/coric-agrar-logo-transp-200.png' %}`). Nema `favicon` polja na modelu; nema `hero_image` na `SiteSettings`. **Dodavanje ovih polja = upload polja (ImageField) + MIME/decompression-bomb validacija + template-rewiring + model migracija** — direktno protiv „admin-only 0-migracija" teme 8.4–8.8 i uvodi upload-security površinu. **ODBIJENO za v1 → DEFER (SM-D1/OQ-1).**

3. **GDPR baner tekst (`gdpr_banner_title`/`gdpr_banner_body`) NIJE SiteSettings-backed.** Baner tekst je HARDKODOVAN `{% translate %}` u `templates/gdpr/_consent_banner.html` (title:20 `{% translate "Poštujemo vašu privatnost" %}`, body:23) (gdpr app vlasništvo; `apps/gdpr/templatetags/gdpr_banner.py` mount + `apps/gdpr/tests/test_consent_banner_template.py` lock). Epics:1174/1175 traži `gdpr_banner_title`/`gdpr_banner_body` na `pages.SiteSettings`. **Wiring banner teksta na SiteSettings = (a) 2 nove translatable polja (`AddField` migracije) + (b) cross-app coupling gdpr→pages (gdpr template čita `pages.SiteSettings` — krši jednosmernu app-dependency invariantu iz project-context:654) + (c) rewriting gdpr banner template + (d) diranje gdpr test-lock-ova + (e) makemessages/.po promene (postojeći `{% translate %}` stringovi izlaze iz prevoda).** Ovo je SADRŽAJ-izvor-istine odluka (mirror 7-4 SM-D1 „jedan izvor istine"), biznis-vidljiva (Marijana hoće da menja baner tekst), i NE pripada „admin-polish" story-ju. **DEFER → OQ-1 (TVRD Mihas go-live gate, mirror 8.8 OQ-1 obrazac).**

4. **Navigacioni meni je v1 STATIČKI** (`templates/partials/header.html` — `{% url %}` linkovi hardkodovani). Epics:1176 eksplicitno: v1 statički + `[NOTE FOR DEV]` za v1.1 `NavigationItem` model. **8.9 dodaje SAMO `[NOTE FOR DEV]` komentar marker u header template** (ili Dev Notes referencu) — NE gradi dinamičku navigaciju (to bi bio nov model + view-context + migracija = van scope-a).

5. **Cache invalidation (epics:1177) — AC TRIVIJALNO ZADOVOLJEN (nema cross-request keša za invalidaciju).** `site_setting` simple_tag (`apps/pages/templatetags/site_settings.py`) kešira SAMO per-request (`request._coric_site_settings` atribut) — NEMA `cache.set()`/Django cache framework sloja. Svaki NOVI request re-učita `SiteSettings.load()` → promena u adminu se ODMAH vidi na sledećem page load-u (nema stale cache). **„Cache invalidation na save signal" je već-zadovoljeno svojstvo: nema keša → nema invalidacije → uvek sveže (SM-D2).** NE izmišljati post_save signal + `cache.delete()` za keš koji ne postoji (YAGNI, project-context:84 „Bez Celery/Redis v1").

**ŠTA 8.9 STVARNO ISPORUČUJE (v1, honest minimal scope):**
- **Verifikacija/regression-lock postojećeg `SiteSettingsAdmin`** (3-4 testovi zeleni; singleton guardovi netaknuti).
- **`search_fields` realna-kolona provera** — `SiteSettingsAdmin.search_fields=("company_name","phone_sales","email")`: SVA tri su REALNE ne-translatable kolone (CharField/EmailField, NISU registrovane u translation.py) → NEMA G-1 FieldError rizika (RAZLIKA od 8.4–8.8 gde je `name`/`title` bilo virtuelno). **VERIFIKUJ da nijedno translatable polje (`slogan`/`address`/`working_hours`) NIJE u `search_fields`** (ako jeste — FieldError; trenutno NIJE → OK; lock test).
- **`[NOTE FOR DEV]` navigacija marker** u `templates/partials/header.html` (v1.1 `NavigationItem` migracija forward-pointer).
- **Cache AC dokumentaciono zatvoren** (SM-D2 — nema keša, uvek sveže; lock test: izmena SiteSettings → sledeći request vidi novu vrednost).
- **DEFER OQ-1** (logo/favicon/hero polja + GDPR-banner-na-SiteSettings + dinamička navigacija) — Mihas go-live scope-gate.

**SCOPE GRANICA (SM-D1):** 8.9 dira SAMO `apps/pages/admin.py:SiteSettingsAdmin` (verify/lock; možda kozmetski fieldsets) + `templates/partials/header.html` (SAMO `[NOTE FOR DEV]` komentar). `PageAdmin` (isti fajl, 8.8 DONE) NETAKNUT. `apps/pages/models.py` NE menja (0 migracija — osim ako Mihas razreši OQ-1 ka „banner-fields-in-v1", što je ZASEBAN story, NE 8.9 proširenje). gdpr `CookiePolicy`/`_consent_banner.html`/`gdpr_banner.py` NETAKNUTI (7-1/7-2; cross-app). `apps/accounts/permissions.py` NE dira (`pages.sitesettings` ostaje Superadmin-only — SM-D5/8.2). `config/urls.py`/`pyproject.toml` NETAKNUTI (0 dep).

## Postojeće stanje (READ pre izmene — obavezno)

`apps/pages/admin.py:SiteSettingsAdmin` (3-4, trenutno):
```python
@admin.register(SiteSettings)
class SiteSettingsAdmin(TranslationAdmin):
    list_display = ("company_name", "phone_sales", "email", "updated_at")
    search_fields = ("company_name", "phone_sales", "email")
    def has_add_permission(self, request): return not SiteSettings.objects.exists()
    def has_delete_permission(self, request, obj=None): return False
    def changelist_view(self, request, extra_context=None):
        obj = SiteSettings.load()
        return HttpResponseRedirect(reverse("admin:pages_sitesettings_change", args=[obj.pk]))
```
Šta MORA ostati (regression — `apps/pages/tests/test_sitesettings_admin.py` lock):
- `SiteSettings in admin.site._registry`; `has_add_permission` False kad red postoji; `has_delete_permission` False (i za `obj=None`); `list_display` + `search_fields` definisani; `changelist_view` → 302 redirect na change; change-view 200 za superuser.

`SiteSettings` model polja (`apps/pages/models.py:29–131`) — IZVOR istine:
- non-translatable: `company_name` (default „Ćorić Agrar"), `phone_sales`, `phone_service`, `email`
- translatable (`_sr/_hu/_en`; `translation.py` registruje `("slogan","address","working_hours")`): `slogan`, `address`, `working_hours`
- social: `social_facebook`, `social_instagram` (URLField, blank)
- **NEMA `logo`/`favicon`/`hero_image`/`gdpr_banner_*`** (epics:1175 pretpostavka FALSE — SM-D1)
- singleton: `save()` forsira pk=1; `delete()` raise `PermissionDenied`; `load()` get_or_create pk=1
- **NIJE PublishableModel/SluggedModel** — samo `TimestampedModel` (created_at/updated_at)

`apps/pages/templatetags/site_settings.py` (3-4) — `{% site_setting "field" %}` tag: per-request keš (`request._coric_site_settings`), locale-aware getattr, fallback uncached `load()` kad nema request-a. **NEMA Django `cache` framework — per-request samo (SM-D2).**

`templates/partials/header.html` (1.x/2.13/3-4/4-4) — STATIČKI nav: hardkodovan logo `{% static %}`, `{% site_setting %}` za kontakt (address/phone_sales/phone_service/social_*), `{% url %}` nav linkovi. **8.9 dodaje SAMO `[NOTE FOR DEV]` komentar (v1.1 NavigationItem).**

`templates/gdpr/_consent_banner.html` (7-2, **NE DIRATI**) — hardkodovan `{% translate %}` baner tekst (title:20 `{% translate "Poštujemo vašu privatnost" %}`, body:23). gdpr app vlasništvo. `apps/gdpr/tests/test_consent_banner_template.py` lock. Wiring na SiteSettings = OQ-1 DEFER.

## Acceptance Criteria

1. **AC1 — `SiteSettingsAdmin` ostaje pun funkcionalan singleton `TranslationAdmin` (REGRESSION LOCK; 3-4).** `SiteSettingsAdmin` ostaje `TranslationAdmin` (NE plain ModelAdmin) — modeltranslation AUTO-renderuje sr/hu/en tabove za `slogan`/`address`/`working_hours`. Singleton guardovi ZADRŽANI: `has_add_permission` → False kad red postoji; `has_delete_permission` → False (i `obj=None`); `changelist_view` → 302 redirect na change-view jedinog objekta (kroz `reverse("admin:pages_sitesettings_change")` — NIKAD hardkodovan put); change-view → 200 za superuser. SVI postojeći `apps/pages/tests/test_sitesettings_admin.py` testovi OSTAJU ZELENI. `fieldsets` (ako se dodaju radi grupisanja — opciono, kozmetika) koriste BAZNA imena translatable polja (`slogan`/`address`/`working_hours` — auto-ekspanzija per-locale; G-1), NE `_sr/_hu/_en` ručno.

2. **AC2 — Sva opšta-podešavanja polja editabilna kroz admin (per locale za translatable).** Marijana kroz change-view može da menja: `company_name`, `slogan` (sr/hu/en), `address` (sr/hu/en), `phone_sales`, `phone_service`, `email`, `working_hours` (sr/hu/en), `social_facebook`, `social_instagram`. Change-view sa POST validnih vrednosti → save prolazi (302) **I round-trip verifikacija: `SiteSettings.load()` posle POST-a ima NOVE vrednosti** (NE samo status-kod assert). POST MORA biti PUN modeltranslation form (SVA `_sr/_hu/_en` varijantna polja za `slogan`/`address`/`working_hours` + sva required ne-translatable polja) — partial POST (npr. samo `_sr` ili izostavljeno required polje) tiho vraća **200 redisplay sa form errors** (NE 302), pa bi assert samo na status-kodu lažno prošao/promašio. Change-view GET → 200 prikazuje sva polja sa per-locale tabovima za translatable. (Ovo je VEĆ funkcionalno 3-4 — AC zaključava da 8.9 NE razbije; novi smoke test POST-save round-trip.)

3. **AC3 — `search_fields` su REALNE ne-translatable kolone (NEMA G-1 FieldError; verify-lock).** `SiteSettingsAdmin.search_fields=("company_name","phone_sales","email")` — SVA TRI su realne ne-translatable DB kolone (CharField/EmailField; NISU u `translation.py` registraciji `("slogan","address","working_hours")`). Changelist-search nad njima NE baca `FieldError` (RAZLIKA od 8.4–8.8 gde je virtuelni `name`/`title` bio bug). **AC zaključava (DEFENSE-IN-DEPTH LOCK — OBAVEZAN bez obzira na redirect masking): nijedno TRANSLATABLE polje (`slogan`/`address`/`working_hours`) NIJE u `search_fields`** (dodavanje translatable polja bez `_sr` sufiksa → runtime FieldError; G-1). Lock test je MANDATORNA komponenta AC3 — Dev/TEA ga NE deprioritizuje niti preskače. NAPOMENA: singleton `changelist_view` redirektuje (302) PRE nego što se search izvrši, što FieldError rizik u ovom konkretnom singleton runtime-u praktično maskira — ALI to maskiranje je slučajno (zavisi od singleton redirect ponašanja koje budući refaktor može ukloniti), pa lock test svejedno OBAVEZNO verifikuje da `search_fields` ne sadrži sirovo translatable ime (defense-in-depth guard protiv budućeg refaktora + dokumentaciona jasnoća; G-1).

4. **AC4 — Promena SiteSettings reflektuje se ODMAH (cache AC — već-zadovoljen; SM-D2).** Nema cross-request keša (`site_setting` tag kešira SAMO per-request na `request` objektu; NEMA Django `cache.set()`). Izmena `SiteSettings` u adminu → SLEDEĆI request (novi `request` objekat) re-učita `SiteSettings.load()` → nova vrednost se vidi na svim stranama. **NE uvoditi post_save signal + `cache.delete()`** (keš koji ne postoji se ne invalidira — YAGNI; SM-D2). Test: izmeni `company_name` (npr. kroz `obj.company_name="X"; obj.save()`) → render template sa `{% site_setting "company_name" %}` u NOVOM request-u → vidi „X" (NE staru vrednost).

5. **AC5 — RBAC: `SiteSettings` je Superadmin-only (NE re-grant; verify).** `pages.sitesettings` je EKSPLICITNO IZOSTAVLJEN iz `EDITOR_CONTENT_MODELS` (8.2 SM-D15 — Editor NE sme da menja globalna podešavanja v1; mirror `gdpr.cookiepolicy`). 8.9 NE dira `apps/accounts/permissions.py` i NE dodaje `pages.sitesettings` u editor allowlist. Verify: Editor → GET `admin:pages_sitesettings_change` → 403 (ili nema link u app_list); Superadmin → 200. (8.2 RBAC lock OSTAJE zelen; NE re-grant.)

6. **AC6 — `[NOTE FOR DEV]` navigacija marker (v1 statički; v1.1 forward-pointer).** Navigacioni meni je v1 STATIČKI kodiran u `templates/partials/header.html` (epics:1176). 8.9 dodaje `{# [NOTE FOR DEV] v1.1: dinamička navigacija kroz NavigationItem model — trenutno (v1) statički {% url %} linkovi #}` komentar uz SPOLJNI nav element `<nav class="coric-nav navbar navbar-expand-md" ...>` (multi-class, NE samo `coric-nav`; linija ~55 u `templates/partials/header.html`) — NE uz unutrašnji `<div class="collapse navbar-collapse" id="coricMainNav">` (~linija 76). (Ili ekvivalentan Django `{# #}` komentar uz isti spoljni nav.) **NE gradi dinamičku navigaciju** (nov model + migracija + view-context = van scope-a). Marker je SAMO dokumentaciona forward-referenca. (Render header-a → 200 nepromenjen; komentar ne menja izlaz.)

7. **AC7 — 0 migracija + 0 dep (admin/verify/marker-only).** 8.9 NE menja `SiteSettings` model → `makemigrations pages --check` = „No changes" (0 migracija). 0 novih dep (`uv add`). **Ako Dev (pogrešno) implementira epics:1175 polja (`logo`/`favicon`/`hero`/`gdpr_banner_*`) → to bi generisalo migracije → STOP, van scope-a (SM-D1/OQ-1).** `PageAdmin` (isti fajl, 8.8) NETAKNUT.

8. **AC8 — `manage.py check` čist + ŠIRI suite regression zelen.** `manage.py check` (admin.E*) = 0 serious errors. Postojeći lock-ovi ZELENI: `apps/pages/tests/test_sitesettings_admin.py` (singleton/registry/changelist-redirect/change-200), `test_sitesettings_*` (model/translation/wiring/migration_seed/singleton), `apps/pages/tests/test_site_setting_tag.py` (tag keš), `test_contact_info.py` (header wiring), `apps/gdpr/tests/test_consent_banner_template.py` (banner NETAKNUT — verify da 8.9 NIJE diralo). ŠIRI suite (apps/pages + apps/accounts RBAC + apps/gdpr banner regression) zelen. `ruff check` + `djade` clean. Sve user-facing poruke srpski latinica pune dijakritike (č/ć/ž/š/đ).

## Tasks / Zadaci

- [x] **Task 1 — Verifikacija (PRE koda; sve REUSE iz 3-4 — NEMA Web Intelligence).** (AC1, AC3, AC5)
  - [x] 1.1 Potvrdi `apps/pages/admin.py:SiteSettingsAdmin` postoji i pun je (3-4 — singleton `TranslationAdmin` + guardovi + changelist redirect). Potvrdi `apps/pages/tests/test_sitesettings_admin.py` lock-ovi zeleni PRE izmene (baseline).
  - [x] 1.2 Potvrdi `SiteSettings` model NEMA `logo`/`favicon`/`hero_image`/`gdpr_banner_*` (verifikovano: samo kontakt/social + timestamps) → epics:1175 polja NE postoje → SM-D1 DEFER (NE dodavati).
  - [x] 1.3 Potvrdi `search_fields=("company_name","phone_sales","email")` su SVA realne ne-translatable kolone (NISU u `translation.py` `("slogan","address","working_hours")`) → NEMA G-1 FieldError. Potvrdi nijedno translatable polje NIJE u `search_fields`.
  - [x] 1.4 Potvrdi `pages.sitesettings` NIJE u `EDITOR_CONTENT_MODELS` (`apps/accounts/permissions.py` — Superadmin-only, 8.2) → RBAC NE re-grant (AC5).
  - [x] 1.5 Potvrdi GDPR baner tekst je hardkodovan `{% translate %}` u `templates/gdpr/_consent_banner.html` (NE SiteSettings) i `site_setting` tag NEMA Django `cache` (per-request samo) → OQ-1 DEFER (banner-fields) + SM-D2 (cache already-fresh).

- [x] **Task 2 — SiteSettingsAdmin verify/lock + opciono fieldsets (AC1, AC2, AC3).**
  - [x] 2.1 Zadrži `SiteSettingsAdmin(TranslationAdmin)` + singleton guardove NEPROMENJENE (3-4 — NE diraj logiku; samo regression-lock). `PageAdmin` (isti fajl) NETAKNUT.
  - [x] 2.2 (Opciono — kozmetika; PREPORUKA: preskoči osim ako Dev hoće čitljiviju formu) `fieldsets` PRESKOČEN po preporuci story-ja — forma već radi 3-4; `apps/pages/admin.py` NETAKNUT (0 izmena). G-2 ne primenjuje (nema timestamp polja u fieldsets-u).
  - [x] 2.3 NE menjati `search_fields` (već realne kolone — AC3). NE dodavati translatable polje u `search_fields` (G-1). Defense-in-depth assertion (`slogan`/`address`/`working_hours` NISU u `search_fields`) pokrivena u novom `test_8_9_sitesettings_admin.py::test_ac3_no_translatable_field_in_search_fields` — zelen.

- [x] **Task 3 — Navigacija `[NOTE FOR DEV]` marker (AC6).**
  - [x] 3.1 Dodat Django `{# [NOTE FOR DEV] v1.1: dinamička navigacija kroz NavigationItem model — trenutno (v1) statički {% url %} linkovi #}` komentar NEPOSREDNO IZNAD SPOLJNOG `<nav class="coric-nav navbar navbar-expand-md">` (header.html — uz spoljni `<nav>`, NE uz unutrašnji collapse div). Nav markup/linkovi NEPROMENJENI. `djade --check` clean posle.

- [x] **Task 4 — RBAC + cache + banner verify (AC4, AC5, AC8) — NE menjati izvore.**
  - [x] 4.1 Verify RBAC (NE re-grant): Editor → `admin:pages_sitesettings_change` → 403; Superadmin → 200. `apps/accounts/permissions.py` NETAKNUT.
  - [x] 4.2 Verify cache-AC (SM-D2): izmena SiteSettings → NOVI request vidi novu vrednost kroz `{% site_setting %}` (nema stale keš). NE uveden post_save signal/`cache.delete()`.
  - [x] 4.3 Verify gdpr banner NETAKNUT: `templates/gdpr/_consent_banner.html` + `apps/gdpr/tests/test_consent_banner_template.py` zeleni (8.9 NIJE diralo gdpr).

- [x] **Task 5 — Smoke + ŠIRI suite regression (AC7, AC8).**
  - [x] 5.1 `manage.py check` 0 issues (admin.E*). `makemigrations pages --check` = „No changes detected in app 'pages'" (AC7 — 0 migracija; model NETAKNUT).
  - [x] 5.2 ŠIRI suite: `apps/pages` + `apps/accounts` (RBAC) + `apps/gdpr` (banner regression) = 534 passed. `ruff check` (touched files) + `djade --check header.html` clean.

## Dev Notes

### Trenutno stanje fajlova koji se DIRAJU (pročitano — obavezno)

- **`apps/pages/admin.py` (UPDATE — minimalan; verify/lock + opciono fieldsets):** sadrži `SiteSettingsAdmin` (singleton — DIRA SE samo regression-lock + opciono fieldsets) i `PageAdmin` (8.8 — **NE DIRATI**). NE menjati singleton guardove ni `changelist_view` (3-4 namerni). NE menjati `search_fields` (već realne kolone).
- **`templates/partials/header.html` (UPDATE — SAMO `{# [NOTE FOR DEV] #}` komentar uz nav):** statički nav. NE menjati linkove/markup; samo dodati v1.1 NavigationItem forward-pointer komentar (AC6). `{% load i18n site_settings static %}` na vrhu (NE dirati).
- **`apps/pages/models.py` (NE menjati — admin/verify-only):** `SiteSettings` singleton. NEMA `logo`/`favicon`/`hero`/`gdpr_banner_*` (epics:1175 FALSE premisa — SM-D1). 0 migracija.
- **`apps/pages/templatetags/site_settings.py` (NE menjati — verify cache-AC):** per-request keš samo (NEMA Django `cache`). Cache-AC already-satisfied (SM-D2).
- **`templates/gdpr/_consent_banner.html` (NE menjati — cross-app gdpr; OQ-1 DEFER):** hardkodovan `{% translate %}` baner tekst. Wiring na SiteSettings = zaseban story (cross-app coupling + migracije + gdpr-test-ownership).
- **`apps/accounts/permissions.py` (NE menjati — verify):** `EDITOR_CONTENT_MODELS` IZOSTAVLJA `pages.sitesettings` (Superadmin-only; 8.2 SM-D15). NE re-grant (AC5).
- **`apps/pages/tests/test_sitesettings_admin.py` (REGRESSION LOCK — verifikuj zeleni, NE prepravljati):** singleton/registry/changelist-redirect/change-200 lock-ovi.

### Latest tech information

NEMA Web Intelligence ulaz — sve REUSE iz 3-4 (SiteSettings + admin + tag VEĆ izgrađeni). 0 nova dep, 0 `uv add`. `django-modeltranslation` (translatable tabovi) + Django admin (singleton guardovi) VEĆ u upotrebi.

## SM Decisions (Odluke)

- **SM-D1 — SCOPE: epics:1175 model-proširenja (`logo`/`favicon`/`hero pozadine`) + GDPR-banner-na-SiteSettings ODBIJENA za v1 (real-code-wins + YAGNI + cross-app invarianta).** (a) `SiteSettings` NEMA `logo`/`favicon`/`hero_image` — logo je hardkodovan static asset (`header.html:61`); dodavanje = upload polja (ImageField + MIME/bomb validacija — `validate_image_mime` reuse) + template-rewiring + migracija → protiv „admin-only 0-migracija" teme 8.4–8.8 i uvodi upload-security površinu. (b) GDPR baner tekst je hardkodovan `{% translate %}` u gdpr app-u (`_consent_banner.html`); wiring na `pages.SiteSettings` = cross-app coupling gdpr→pages (krši jednosmernu app-dependency invariantu, project-context:654) + 2 `AddField` migracije + gdpr template/test rewrite + makemessages/.po promene. **ODLUKA: 8.9 = verify/lock postojećeg SiteSettings admin-a + navigacija marker + cache-AC zatvaranje. Logo/favicon/hero polja I banner-fields-na-SiteSettings = DEFER (OQ-1, Mihas go-live scope-gate). Dev NE implementira model-promene u 8.9; ako biznis traži editabilan baner/logo za v1 → ZASEBAN aditivan story (model + template-rewrite + migracija), NE 8.9 proširenje.** Mirror 8.8 SM-D1 (SM sme odbiti epics-model-proširenje uz obrazloženje; OQ za Mihas ako biznis-vidljivo).
- **SM-D2 — Cache-AC (epics:1177) JE VEĆ-ZADOVOLJEN (nema cross-request keša za invalidaciju).** `site_setting` tag kešira SAMO per-request (`request._coric_site_settings`); NEMA Django `cache.set()`/Redis (project-context:84 „Bez Celery/Redis v1"). Svaki NOVI request re-učita `SiteSettings.load()` → promena u adminu se ODMAH vidi na sledećem page load-u (zero stale). **ODLUKA: „Cache invalidation na save signal" je already-satisfied svojstvo — NEMA keša → NEMA invalidacije → uvek sveže. NE uvoditi post_save signal + `cache.delete()` za nepostojeći keš (YAGNI).** AC4 lock test: izmena → novi request vidi novu vrednost.
- **SM-D3 — `SiteSettings` admin JE VEĆ izgrađen (3-4) — 8.9 NIJE „napravi admin".** epics:1173 „Story 3.4 dodaje admin za SiteSettings" je VEĆ ISPUNJENO (`SiteSettingsAdmin` singleton TranslationAdmin radi). 8.9 = verify/regression-lock + reconciliation (epics:1175 FALSE polja DEFER + navigacija marker + cache zatvaranje). **ODLUKA: NAJTANJA Epic-8 story (admin već postoji; 8.9 je verify+marker). Honest scope > epics-prose copy.**
- **SM-D4 — Navigacija v1 STATIČKI + `[NOTE FOR DEV]` marker (epics:1176 eksplicitno).** epics:1176 sam kaže v1 statički + v1.1 NavigationItem. **ODLUKA: 8.9 dodaje SAMO Django `{# [NOTE FOR DEV] #}` komentar u header.html; NE gradi dinamičku navigaciju (nov model + view-context + migracija = van scope-a, v1.1).**
- **SM-D5 — RBAC NE re-grant (`pages.sitesettings` Superadmin-only; 8.2).** `EDITOR_CONTENT_MODELS` IZOSTAVLJA `pages.sitesettings` (8.2 SM-D15 — Editor NE menja globalna podešavanja v1; mirror `gdpr.cookiepolicy`). **ODLUKA: AC5 samo verify (Editor→403, Superadmin→200); NE dodavati u editor allowlist.** Marijana-kao-Superadmin menja SiteSettings (NE Editor rola).
- **SM-D6 — `search_fields` su VEĆ realne kolone (NEMA G-1 fix potreban; RAZLIKA od 8.4–8.8).** `("company_name","phone_sales","email")` su SVA ne-translatable (CharField/EmailField; NISU u translation.py). RAZLIKA od 8.4–8.8 gde je `name`/`title` bilo virtuelno → trebao `_sr` fix. **ODLUKA: NE menjati `search_fields`; samo lock-test da nijedno translatable polje (`slogan`/`address`/`working_hours`) NIJE dodato (defense-in-depth G-1).**

## Gotchas

- **G-1 — `search_fields` na translatable polju → runtime `FieldError`.** `slogan`/`address`/`working_hours` su modeltranslation-virtuelni → dodavanje sirovog imena u `search_fields` baca `FieldError` (runtime, NE `manage.py check`). **TRENUTNO `search_fields` NEMA taj problem** (sve realne kolone) — 8.9 NE sme da uvede regresiju dodavanjem translatable polja bez `_sr` sufiksa. `list_display` na virtuelnom je OK (render per-locale). `fieldsets` koriste BAZNA imena (auto-ekspanzija). (5-1 BL-2 / 8.4–8.8 G-1.) NAPOMENA: singleton `changelist_view` redirektuje PRE search-a → FieldError praktično maskiran, ali lock svejedno (jasnoća + budući refaktor guard).
- **G-2 — Ako `fieldsets` uključuje `created_at`/`updated_at` → MORAŠ `readonly_fields=("created_at","updated_at")`** (inače `admin.E005` na startup-u — non-editable polje u fieldsets bez readonly). Lako previđeno na „opcionalnom" fieldsets task-u. Ako fieldsets NIJE dodat (preporuka — forma radi i bez) → G-2 ne primenjuje. (Mirror 8.8 G-12.)
- **G-3 — `PageAdmin` (isti fajl, 8.8) NE DIRATI.** `apps/pages/admin.py` sadrži DVA admin-a: `SiteSettingsAdmin` (singleton — 8.9 scope) i `PageAdmin` (NIJE singleton — 8.8 DONE). Lako pomešati guardove. 8.9 dira SAMO `SiteSettingsAdmin` (verify/lock). NE kopirati Page WYSIWYG/search-fix na SiteSettings (SiteSettings nema body rich-text).
- **G-4 — gdpr `_consent_banner.html` je CROSS-APP (gdpr vlasništvo) — NE DIRATI.** Wiring banner teksta na `pages.SiteSettings` (epics:1174/1175) = cross-app coupling gdpr→pages + migracije + gdpr test-ownership. DEFER (OQ-1). 8.9 ostavlja hardkodovan `{% translate %}` baner netaknut.
- **G-5 — Cache AC: NE izmišljati keš da bi ga invalidirao.** `site_setting` tag = per-request keš samo (NEMA Django `cache`). „Cache invalidation na save" je already-satisfied (nema stale). NE dodavati post_save signal + `cache.delete()` (YAGNI; SM-D2). Lock: izmena → novi request vidi novo.
- **G-6 — singleton `changelist_view` redirektuje (302), NE renderuje 1-redni changelist.** 3-4 namerni singleton UX. 8.9 NE menja (regression-lock `test_changelist_redirects_to_change_view`). NE „popravljati" u običan changelist.

## Open Questions (OQ)

- **OQ-1 — ⚠️ TVRD Mihas go-live SCOPE-GATE (mora se potvrditi PRE nego što se 8-9 i Epic 8 zatvore — mirror 8.8 OQ-1 obrazac):** epics:1174/1175 traži `gdpr_banner_title`/`gdpr_banner_body` (per-locale editabilan baner tekst) + `logo`/`favicon`/`hero pozadine` na `SiteSettings`. SM-D1 ODBIJA za v1 (cross-app coupling + upload-security + migracije + template/test rewrite — van „admin-polish" teme). **PITANJE ZA MIHAS-a (SCOPE, NE kod-gate): da li je za go-live prihvatljivo da (a) GDPR baner tekst ostane hardkodovan `{% translate %}` (menja se kroz .po prevod + redeploy, NE admin), (b) logo/favicon ostanu hardkodovani static asseti (menjaju se zamenom fajla + redeploy), (c) navigacija ostane statička? ILI je editabilan-baner/logo-kroz-admin go-live blocker?** Ako blocker → ZASEBAN aditivan story (SiteSettings model-proširenje `gdpr_banner_*` translatable + opciono `logo`/`favicon` ImageField sa `validate_image_mime` reuse + rewiring `_consent_banner.html`/`header.html` + cross-app coupling odluka + makemessages migracija postojećih `{% translate %}` stringova + gdpr test-ownership), NE 8.9 proširenje. **Dev NE implementira ova proširenja u 8.9 bez obzira na ishod (SM-D1). Preporuka SM-a: deferral je razuman za v1 (mirror 8.8 OQ-1 koji je Mihas prihvatio 2026-06-09 — „v1 bez CMS"), ali biznis-vidljivost (urednik hoće da menja baner) traži eksplicitnu Mihas potvrdu.**
- **OQ-2 — Dinamička navigacija (`NavigationItem` model) — DEFER v1.1 (epics:1176 eksplicitno).** v1 statički nav + `[NOTE FOR DEV]` marker (AC6). v1.1: `NavigationItem` model (label per-locale + url/url_name + parent FK za dropdown + display_order) + context-processor + header-template-rewrite. Van 8.9 (nov model + migracija). Marker postavljen da se ne zaboravi.
- **OQ-3 — `favicon` hardkodovan? (verify pre go-live).** Logo je `header.html:61` static. Favicon (ako postoji) verovatno u `base.html` `<link rel="icon">` static — nije SiteSettings-backed. Ako biznis hoće favicon kroz admin → deo OQ-1 model-proširenja (ImageField + base.html rewiring). v1: zamena static fajla + redeploy. NE blokira 8.9.

## Definicija završenosti (DoD)

- [x] AC1–AC8 implementirani i pokriveni TEA testovima (RED→GREEN). 25/25 zeleno.
- [x] `SiteSettingsAdmin` ostaje pun singleton `TranslationAdmin` (3-4 lock-ovi zeleni); `PageAdmin` (isti fajl) NETAKNUT.
- [x] `SiteSettings` model NEMA novih polja (`makemigrations pages --check`=No changes; 0 migracija; epics:1175 polja DEFER — SM-D1/OQ-1).
- [x] Sva opšta-podešavanja polja editabilna (per-locale za `slogan`/`address`/`working_hours`); change-view POST round-trip 200/302.
- [x] `search_fields` realne kolone (nijedno translatable polje; G-1 lock).
- [x] Cache-AC zatvoren: izmena → novi request vidi novu vrednost (NEMA post_save signal/`cache.delete()`; SM-D2).
- [x] RBAC verify: Editor→403, Superadmin→200 na `admin:pages_sitesettings_change` (NE re-grant; SM-D5).
- [x] `[NOTE FOR DEV]` v1.1 NavigationItem marker u `header.html` (nav markup NEPROMENJEN; AC6).
- [x] gdpr `_consent_banner.html` + gdpr banner testovi NETAKNUTI/zeleni (cross-app; G-4).
- [x] `manage.py check` 0 issues; ŠIRI suite (pages/accounts/gdpr) zelen (534 passed); `ruff`(touched)+`djade` clean.
- [x] Sve user-facing/komentar poruke srpski latinica pune dijakritike (č/ć/ž/š/đ).
- [x] epics:1175 model-proširenja (logo/favicon/hero/gdpr_banner_*) + dinamička navigacija NISU implementirana (SM-D1/OQ-1/OQ-2 DEFER — 0 novih modela/migracija).

## Testing

TEA piše testove (RED→GREEN). Pokrivenost po AC:

- **Admin registracija/singleton (regression — 3-4):** `SiteSettingsAdmin` je `TranslationAdmin`; `has_add_permission` False kad red postoji; `has_delete_permission` False (i `obj=None`); `changelist_view` → 302 redirect na change; change-view 200 superuser (AC1). Postojeći `test_sitesettings_admin.py` zeleni.
- **Polja editabilna (AC2):** change-view GET 200 prikazuje sva polja + per-locale tabove za `slogan`/`address`/`working_hours`; POST validnih vrednosti → save (302) + round-trip (`SiteSettings.load()` ima nove vrednosti). POST kroz REALAN admin (`force_login` superuser; `reverse("admin:pages_sitesettings_change", args=[obj.pk])`).
- **search_fields realne kolone (AC3/G-1):** `SiteSettingsAdmin.search_fields == ("company_name","phone_sales","email")`; nijedno translatable ime (`slogan`/`address`/`working_hours`) NIJE u `search_fields`. **Ova „nijedno translatable polje" assertion mora biti NAPISANA u novom `test_8_9_sitesettings_admin.py` — postojeći `test_sitesettings_admin.py` proverava samo da je `search_fields` definisan/neprazan, NE ovaj negativni invariant.**
- **cache already-fresh (AC4/SM-D2):** izmeni `company_name` → render template `{% site_setting "company_name" %}` u NOVOM request-u (novi `RequestFactory` request) → vidi novu vrednost (NE staru). NEMA post_save signal/`cache.delete()` u kodu.
- **RBAC (AC5):** Editor (8.2 grupa, is_staff) → `admin:pages_sitesettings_change` 403; Superadmin → 200; anon → 302 login. `pages.sitesettings` NIJE u `EDITOR_CONTENT_MODELS` (verify, NE menjaj).
- **navigacija marker (AC6):** `header.html` sadrži `[NOTE FOR DEV]` komentar uz nav; render header → 200; nav linkovi NEPROMENJENI (komentar ne menja izlaz).
- **0 migracija (AC7):** `makemigrations pages --check` No changes.
- **Uslovni fieldsets put (Task 2.2 / G-2 — SAMO ako se opciona `fieldsets` kozmetika uzme):** `manage.py check` mora proći bez `admin.E005`; `readonly_fields=("created_at","updated_at")` je OBAVEZNO ako su `created_at`/`updated_at` polja u `fieldsets` (inače `admin.E005` non-editable-u-fieldsets-bez-readonly). Ako se `fieldsets` NE uzme (preporuka — forma već radi) → ovaj uslovni put se ne primenjuje.
- **ŠIRI suite (AC8):** pages (sitesettings*/tag/contact_info/8.8 PageAdmin) + accounts (RBAC) + gdpr (banner regression `test_consent_banner_template.py` — verify NETAKNUT) zeleni.

## Dev Agent Record

### Agent Model Used

claude-fable-5 (Dev GREEN)

### Completion Notes List

- **NAJTANJA Epic-8 story potvrđena (SM-D3):** jedina kod-izmena = JEDAN Django `{# #}` komentar u `header.html`. `apps/pages/admin.py` NETAKNUT (fieldsets PRESKOČEN po preporuci Task 2.2 — forma već radi 3-4; nema G-2 admin.E005 rizika jer nema timestamp fieldsets-a).
- **RED→GREEN:** 23 regression-lock testa već zelena (zaključavaju 3-4 ponašanje); 2 AC6 marker testa (`test_ac6_header_has_note_for_dev_marker`, `test_ac6_marker_is_on_outer_nav_not_inner_collapse`) bili crveni → sada zeleni. Finalno 25/25.
- **Marker pozicija (AC6):** komentar dodat NEPOSREDNO IZNAD spoljnog `<nav class="coric-nav navbar navbar-expand-md">` (iznad reda 55, ispod postojeća dva `{# #}` komentara), UNUTAR <250 znakova od spoljnog `<nav>` (test_ac6_marker_is_on_outer_nav_not_inner_collapse PASS). NE uz unutrašnji collapse div. `{# #}` (NE HTML `<!-- -->`) → ne emituje se u render (test_ac6_header_renders_200_and_comment_not_emitted PASS). Pune dijakritike (dinamička/statički/linkovi).
- **0 migracija (AC7):** `makemigrations pages --check` = „No changes detected in app 'pages'". `SiteSettings` model NETAKNUT — epics:1175 polja (logo/favicon/hero/gdpr_banner_*) DEFER (SM-D1/OQ-1), gdpr `_consent_banner.html`/permissions/site_setting tag NETAKNUTI.
- **OQ-1 napomena:** već razrešen 2026-06-09 (Mihas prihvatio deferral — v1 bez CMS); Epic 8 se može zatvoriti.
- **Lint:** `ruff check` na touched fajlovima (admin.py, test_8_9) = All checks passed; `djade --check header.html` = already formatted. 16 ruff F401/F541/F841 grešaka postoje u NEDIRANIM test fajlovima (brands/products + 3-4 test_sitesettings_wiring.py) — pre-existing, van scope-a 8.9, nisu uvedene ovom story-jem.

### File List

- `templates/partials/header.html` (UPDATE — SAMO `{# [NOTE FOR DEV] #}` nav marker; nav markup/linkovi nepromenjeni)
- `apps/pages/tests/test_8_9_sitesettings_admin.py` (NEW — TEA RED phase; 25 testova AC1-AC8)
- `_bmad-output/implementation-artifacts/8-9-sitesettings-navigation-menu-admin.md` (story checkboxes + Dev Agent Record)
- 0 migracija, 0 model-promena, 0 `apps/pages/admin.py` izmena, 0 gdpr-dodira, 0 novih dep
