---
story_id: 8.3
story_key: 8-3-admin-dashboard-sa-segmentovanim-lead-count-om
epic: 8
title: Admin Dashboard sa Segmentovanim Lead Count-om
status: ready-for-dev
risk_tier: MEDIUM
base_branch: master
language: Srpski (latinica)
depends_on:
  - 8-1   # admin na bare /admin-coric/ (admin.site.urls VAN i18n_patterns)
  - 8-2   # IsSuperadminMixin / IsEditorMixin (apps/accounts/permissions.py) + RBAC grupe
  - 4-1   # forms.Lead model (form_type discriminator + created_at) — IZVOR lead count-a
  - 2-2   # products.Product (is_published) — broj objavljenih proizvoda
  - 5-1   # blog.Post (Post.published manager) — broj objavljenih objava
forward_dep:
  - 8-4   # ..8-9 CRUD admini koriste iste mixine; dashboard linkuje njihove add view-ove
migrations: 0
new_dependencies: 0
---

# Story 8.3: Admin Dashboard sa Segmentovanim Lead Count-om

Status: ready-for-dev

## Opis

Kao **Marijana** (admin/Superadmin), želim **dashboard sa statistikama i brzim akcijama**, da bih **odmah posle login-a videla stanje sajta** (koliko lead-ova je stiglo ovog meseca po tipu forme, koliko ima objavljenih proizvoda i blog objava) i jednim klikom dodala novi sadržaj.

Ovo je **TREĆA** Epic 8 story i PRVA koja STVARNO PRIMENJUJE RBAC mixine iz 8.2 (8.2 ih je samo kreirao kao forward-dep). Story **zamenjuje default Django admin index** stranu (`/admin-coric/`) prilagođenim dashboard-om koji prikazuje:

1. **Segmentovan lead count za tekući mesec** — 4 segmenta (`contact`, `model_inquiry`, `service_request`, `part_request`) + `total` iznad njih, agregirano iz `forms.Lead` (Epic 4).
2. **Broj objavljenih proizvoda + objavljenih blog objava** (`products.Product.is_published=True` + `blog.Post.published`).
3. **Posete za 7/30 dana** kroz `analytics.py:get_ga_visits()` — sa GRACEFUL fallback-om (GA Reporting API NIJE konfigurisan u v1 → prikazuje „Posete: N/D — uskoro / Epic 9" bez crash-a; AC poslednji red eksplicitno traži da se dashboard učita i kad GA padne/timeout-uje).
4. **Brze akcije** — „Dodaj proizvod" + „Dodaj blog objavu" linkovi koji vode direktno na admin add view (`reverse("admin:products_product_add")` / `reverse("admin:blog_post_add")`).

**NOVI app `apps/admin_ext/`** (arch:622-625; project-context:199) — top-level admin-customization app koji proširuje admin, ali ga **nijedan domain app ne sme importovati** (project-context:674 / arch:740). `admin_ext` SME da čita domain modele READ-ONLY (agregacija — isti dokumentovani izuzetak kao pages 3-1 cross-boundary čitanje).

**SCOPE GRANICA (KRITIČNO):** 8.3 isporučuje SAMO dashboard (read-only statistika + brze-akcije linkovi). Per-model CRUD admini (Brand 8.4, Category 8.5, Product 8.6, Blog 8.7, Page 8.8, SiteSettings/Navigation 8.9), Lead detail strane i grafikoni/JS vizualizacije su VAN scope-a.

## Kriterijumi prihvatanja

Iz epics.md:1084-1097 (Story 8.3), reconcilovano sa stvarnim modelima i 8.1/8.2 infrastrukturom.

1. **AC1 — Dashboard zamenjuje admin index.** Pristup `/admin-coric/` (root admin URL, ulogovan staff korisnik) renderuje prilagođen dashboard template (NE default Django „Site administration" listu app-ova). Default app/model lista MOŽE ostati ispod dashboard sekcije (Django `app_list` se zadržava — vidi SM-D2), ali dashboard statistika sekcija je iznad i vidljiva odmah.

2. **AC2 — Segmentovan lead count za tekući mesec.** `apps/admin_ext/stats.py:get_lead_stats()` vraća dict tačno sa ključevima `{"contact": int, "model_inquiry": int, "service_request": int, "part_request": int, "total": int}` gde je svaki broj `Lead` zapisa tog `form_type`-a kreiranih u TEKUĆEM kalendarskom mesecu, a `total` je zbir 4 segmenta. Dashboard prikazuje 4 segmenta sa brojevima + `total` istaknut iznad.
   - **TZ-aware granica meseca (eksplicitno):** `month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)` (USE_TZ=True → aware vrednost), pa filter `created_at__gte=month_start`. ZABRANJENO `created_at__month=N` samostalno (ignoriše godinu — vidi G-4); ako se baš koristi mesec/godina komponentno, MORA biti `__year=` + `__month=` ZAJEDNO.
   - **`total` semantika (single-source):** `total` = ZBIR 4 FormType segmenta (jedini validni izvor tipa) i po dizajnu jednak je svim lead-ovima meseca jer je `form_type` choice-constrained (`Lead.FormType` su jedine dozvoljene vrednosti) — DB zapis sa `form_type` van 4 enum člana se NE očekuje. TEA NE sme pisati kontradiktornu tvrdnju oblika `total == Lead.objects.filter(<mesec>).count()` kao zaseban izvor (može odstupiti samo na korumpiranim/legacy podacima van šeme); `total` je definisan kao zbir segmenata, tačka.

3. **AC3 — Segmenti koriste STABILNE DB vrednosti `form_type`.** Ključevi/agregacija koriste `Lead.FormType` member-e (`.value`: `"contact"`/`"model_inquiry"`/`"service_request"`/`"part_request"`) — NE hardkodovane string-ove razbacane po kodu (single-source iz `Lead.FormType`). Ako neki `form_type` nema lead-ova ovog meseca, vrednost je `0` (svi 4 ključa UVEK prisutni).

4. **AC4 — Broj objavljenih proizvoda + objavljenih blog objava.** Dashboard prikazuje ukupan broj `products.Product.objects.filter(is_published=True).count()` i `blog.Post.published.count()` (Post.published manager = `status="published" AND published_at__lte=now`). Draft/nepubliкоvani se NE broje.

5. **AC5 — Posete 7/30 dana sa GRACEFUL GA fallback-om.** `apps/admin_ext/analytics.py:get_ga_visits()` vraća dict `{"last_7": <int|None>, "last_30": <int|None>}`. U v1 (GA Reporting API NIJE konfigurisan — nema kredencijala/lib-a) funkcija vraća `{"last_7": None, "last_30": None}` BEZ podizanja izuzetka. Dashboard tada prikazuje jasan placeholder koji signalizira „još nije aktivirano" — npr. „Posete: N/D — uskoro / Epic 9" (NE goli „N/D" koji zbunjuje UX; vezano za OQ-1). Dashboard se UVEK uspešno učita (HTTP 200) čak i ako `get_ga_visits()` baci bilo koji izuzetak (timeout, network, auth) — poziv je obavijen `try/except Exception` (fail-safe granica — NE goli `except:`, project-context zabranjuje bare except) koji loguje WARNING (BEZ PII) i vraća None-ove (AC poslednji red epics:1097).

6. **AC6 — Brze akcije linkuju admin add view-ove.** Dashboard prikazuje 2 dugmeta/linka: „Dodaj proizvod" → `reverse("admin:products_product_add")` i „Dodaj blog objavu" → `reverse("admin:blog_post_add")`. Linkovi su funkcionalni (klik vodi na admin add formu odgovarajućeg modela).

7. **AC7 — Dashboard je RBAC-gejtovan (login + staff).** Dashboard je deo admin sajta (`/admin-coric/` index) → vidi ga SAMO autentifikovan `is_staff` korisnik; anoniman pristup → admin login redirect (302). Editor I Superadmin (oba imaju `is_staff`) VIDE dashboard sa statistikom (lead podaci su agregat/count, NE sirovi PII → dostupno obema admin ulogama; vidi SM-D5). Pojedinačni Lead zapis (sirovi PII) ostaje u `forms` admin changelist-u, NIJE na dashboard-u.

8. **AC8 — Bez N+1 / efikasna agregacija.** Cela dashboard statistika izvršava se u OGRANIČENOM, malom broju upita: lead count = JEDAN agregacioni upit (`.values("form_type").annotate(Count("id"))` ili 1 `aggregate` sa conditional `Count`/`Q`), proizvodi = 1 `count()`, objave = 1 `count()`. NEMA per-segment petlje sa zasebnim upitom (NE 4 odvojena `.filter().count()`). Query budget zaključan `assertNumQueries` testom (TEA).
   - **Opseg `assertNumQueries(1)` (eksplicitno):** lock od TAČNO 1 upita važi za IZOLOVAN poziv `get_lead_stats()` (jedan `.values().annotate(Count)` agregat) — NE za ceo dashboard view. View dodatno izvršava Django admin `get_app_list()` permission/ContentType upite (chrome cena, ne N+1) → njegov ukupan broj upita NIJE 1. Za pun `/admin-coric/` GET koristiti zaseban, LABAVIJI integracioni budžet (gornja granica), uz warm-ovanje ContentType keša u `setUp()` da se eliminiše order-dependent drift (lekcija Epic 6 query-budget). Dva test opsega su EKSPLICITNO razdvojena: (1) izolovani stats lock = 1; (2) integracioni view budžet = labaviji, dokumentovan.

9. **AC9 — Bez sirovog PII na dashboard-u i u logovima.** Dashboard prikazuje ISKLJUČIVO brojeve/agregате — NIJEDNO ime/email/telefon/poruka iz `Lead`-a se NE renderuje. GA fallback WARNING log NE sadrži PII (project-context:358 / no-PII-in-logs).

## Tasks / Zadaci

- [x] **Task 1 — Web Intelligence: verifikuj PINOVAN admin-index override mehanizam (Django 5.2).** (AC1)
  - [x] **MEHANIZAM JE PINOVAN (jedan, ne „ILI...ILI"):** wrap-uj `admin.site.index` metodu da injektuje stats kroz `extra_context`, delegiraj na SAČUVAN original (`app_list` se zadržava jer ga gradi original `index()`), I postavi `admin.site.index_template` na ZASEBAN template (`admin_ext/dashboard.html`) koji `{% extends "admin/index.html" %}`. Verifikovano protiv `django/contrib/admin/sites.py` (Django 5.2.10): `AdminSite.index()` sam gradi `context = {**each_context, "app_list": get_app_list(...), **(extra_context or {})}` i renderuje `self.index_template or "admin/index.html"`. Posledice koje se MORAJU ispoštovati:
    - (a) `index_template`-SAM je NEDOVOLJAN: `index()` gradi SVOJ context i NEMA stats → mora se wrap-ovati `index` da prosledi `extra_context` sa stats.
    - (b) wrap MORA zvati SAČUVANI original (`_original_index = admin.site.index` UHVAĆEN PRE reassignment-a), NE `admin.site.index(...)` (koji je sada wrapper → beskonačna METODNA rekurzija — vidi G-12).
    - (c) dashboard template EXTENDUJE `admin/index.html` (Django ugrađeni) → `app_list` + admin chrome zadržani; stats blok se renderuje iznad/oko `{{ block.super }}`.
  - [x] Potvrdi da NEMA potrebe za custom `AdminSite` subclass-om (default `admin.site` ostaje — vidi SM-D1) → `config/urls.py` mount `admin.site.urls` NETAKNUT (0 blast-radius na 8.1/8.2 i sve `reverse("admin:...")` testove).

- [x] **Task 2 — Kreiraj `apps/admin_ext/` app skeleton.** (AC1)
  - [x] NOVI `apps/admin_ext/__init__.py`, `apps/admin_ext/apps.py` (`AdminExtConfig`, `name="apps.admin_ext"`, `verbose_name`), prazan `apps/admin_ext/models.py` (NEMA modela — 0 migracija; SM-D3), `apps/admin_ext/migrations/__init__.py`.
  - [x] EDIT `config/settings/base.py` INSTALLED_APPS — dodaj `"apps.admin_ext"` POSLE `"apps.accounts"` (admin-customization sloj ide poslednji; mora biti POSLE `django.contrib.admin` da bi wiring radio).

- [x] **Task 3 — `apps/admin_ext/stats.py:get_lead_stats()`.** (AC2, AC3, AC8, AC9)
  - [x] Lokalan import `from apps.forms.models import Lead` UNUTAR funkcije (admin_ext → forms READ-ONLY cross-boundary; SM-D4). Izračunaj početak tekućeg meseca TZ-aware: `month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)` (USE_TZ=True).
  - [x] JEDAN agregacioni upit: `Lead.objects.filter(created_at__gte=month_start).values("form_type").annotate(c=Count("id"))` → mapiraj u dict sa svih 4 `Lead.FormType` ključa (default 0) + `total` (= zbir 4 segmenta; vidi AC2 total-semantika). Koristi `Lead.FormType.<MEMBER>.value` za ključeve (AC3).

- [x] **Task 4 — `apps/admin_ext/stats.py:get_content_stats()` (ili u istom modulu).** (AC4, AC8)
  - [x] `products.Product.objects.filter(is_published=True).count()` + `blog.Post.published.count()` (lokalni importi). Vrati `{"published_products": int, "published_posts": int}`.

- [x] **Task 5 — `apps/admin_ext/analytics.py:get_ga_visits()` (graceful stub).** (AC5, AC9)
  - [x] Vrati `{"last_7": None, "last_30": None}` u v1 (GA Reporting API nije konfigurisan — nema lib-a/kredencijala; SM-D6). Implementiraj kao funkciju koja je „uključiva" kasnije (čita npr. `getattr(settings, "GA_PROPERTY_ID", "")` → ako prazno, odmah None-ovi; NAPOMENA: `GA_PROPERTY_ID` NE postoji u `config/settings/base.py` — postoji samo `GA_MEASUREMENT_ID` koji je client-side GA4 ID, NE Reporting API property; `getattr` default prazno → None-ovi; NE pravi mrežni poziv u v1).
  - [x] Dashboard placeholder za None-ove signalizira „još nije aktivirano": npr. „Posete: N/D — uskoro / Epic 9" (NE goli „N/D"; vezano za OQ-1).
  - [x] Cela funkcija + njen poziv iz view-a obavijeni u `try/except Exception` (fail-safe granica — NE goli `except:`, project-context zabranjuje bare except) → na BILO KOJI izuzetak loguj `logger.warning` (BEZ PII) i vrati None-ove (dashboard se UVEK učita).

- [x] **Task 6 — `dashboard_index` wrapper koji delegira na SAČUVAN original `admin.site.index`.** (AC1, AC7, AC8)
  - [x] Wrapper (može živeti u `apps/admin_ext/apps.py` ili malom `apps/admin_ext/dashboard.py` — odluči; `views.py` zadrži SAMO ako je potreban) poziva `get_lead_stats()`, `get_content_stats()`, `get_ga_visits()` (`try/except Exception` wrap), sastavi `ctx`, pa delegira na SAČUVAN original (NE na `admin.site.index` koji je sada wrapper → rekurzija G-12). PINOVAN obrazac:
    ```python
    # apps/admin_ext/apps.py ready() (ili admin_ext/dashboard.py + poziv iz ready())
    from django.contrib import admin
    _original_index = admin.site.index            # SAČUVAJ PRE reassignment-a (recursion guard)
    def dashboard_index(request, extra_context=None):
        ctx = {**(extra_context or {}), **get_dashboard_stats()}
        return _original_index(request, extra_context=ctx)   # delegira na ORIGINAL → app_list zadržan
    admin.site.index = dashboard_index
    admin.site.index_template = "admin_ext/dashboard.html"    # extends admin/index.html, renderuje stats iz context-a
    ```
    (`get_dashboard_stats()` je agregator helper koji spaja lead/content/ga statistiku — testabilna jedinica; alternativno spoj `get_lead_stats()`+`get_content_stats()`+`get_ga_visits()` inline). RBAC: pristup ide kroz standardni admin `is_staff` gate (AC7) — NE treba dodatni mixin jer wrapper delegira na admin index unutar admin sajta (SM-D5).
  - [x] N+1 budžet: svi count-ovi su agregati (AC8). `get_lead_stats()` izolovano = `assertNumQueries(1)`; ceo view = labaviji integracioni budžet (AC8).

- [x] **Task 7 — Template `templates/admin_ext/dashboard.html` (dashboard) + wiring u `apps/admin_ext/apps.py:ready()`.** (AC1, AC2, AC4, AC5, AC6)
  - [x] NOVI `templates/admin_ext/dashboard.html` (PINOVANO ime — na njega pokazuje `admin.site.index_template`; SM-D2): `{% extends "admin/index.html" %}` (Django ugrađeni → `app_list` + admin chrome zadržani; G-1), override `{% block content %}` da renderuje statistiku blok (lead segmenti + total, broj proizvoda/objava, GA posete sa „Posete: N/D — uskoro / Epic 9" fallback-om, 2 brze-akcije linka) pa `{{ block.super }}` da zadrži default `app_list` ispod.
  - [x] U `apps/admin_ext/apps.py:ready()` ožiči PINOVAN override (vidi Task 6 kod): sačuvaj `_original_index = admin.site.index`, postavi `admin.site.index = dashboard_index` (wrapper koji delegira na `_original_index` sa stats `extra_context`) I `admin.site.index_template = "admin_ext/dashboard.html"`. Import UNUTAR `ready()` (circular-safe, mirror accounts/apps.py 8.1/8.2 pattern).
  - [x] Sav user-facing tekst srpski latinica sa punim dijakriticima (gettext gde primereno).

- [x] **Task 8 — Regression + suite verifikacija.** (AC1, AC7, AC8)
  - [x] Pokreni ŠIRI suite (admin index override je sajt-wide admin blast-radius — lekcija Epic 6 query-budget drift / 8.1 broad-apps): potvrdi da postojeći admin testovi (accounts/blog/gdpr/pages `test_admin` koji koriste `reverse("admin:...")`) OSTAJU zeleni i da `/admin-coric/` i dalje vraća 200 za staff, 302 za anon.
  - [x] `ruff` + `makemigrations --check` (očekivano: No changes — 0 migracija).

## Testing

**Dev NE piše testove** — TEA generiše RED testove, Dev implementira do GREEN (mirror 8.1/8.2). Pokrivenost koju TEA treba da specifikuje:

- **stats.py:** `get_lead_stats()` — tačni brojevi po segmentu za tekući mesec; prošlomesečni lead-ovi se NE broje (granica meseca, TZ-aware `month_start`); `total` == zbir 4 segmenta (NE pisati kontradiktornu `total == Lead.objects.filter(<mesec>).count()` kao zaseban izvor — AC2 total-semantika); svi 4 ključa prisutni i kad je 0; **`assertNumQueries(1)` SAMO za IZOLOVAN `get_lead_stats()` poziv** (jedan agregat), NE za ceo view (AC8).
- **content stats:** samo `is_published=True` proizvodi i `Post.published` objave se broje; draft/future-dated objave izostavljene.
- **analytics.py:** `get_ga_visits()` vraća None-ove u v1 (nekonfigurisan); kad podigne izuzetak → view ga proguta (`except Exception`, ne bare), dashboard 200, log WARNING bez PII.
- **view/integration:** `/admin-coric/` staff → 200 sa dashboard markup-om (segmenti + total + brze akcije); anon → 302 login; **Editor (8.2 grupa, `is_staff`) → 200 vidi dashboard** I **Superadmin (`is_superuser`, takođe `is_staff`) → 200 vidi dashboard** (eksplicitna SIMETRIJA — oba prolaze kroz `is_staff` gate; TEA pokriva OBE uloge); default `app_list` i dalje prisutan; brze-akcije href-ovi rezolvuju na `admin:products_product_add` / `admin:blog_post_add`.
- **view query budget (zaseban, labaviji):** pun `/admin-coric/` GET ima LABAVIJI integracioni budžet (gornja granica, NE 1 — view pokreće admin `get_app_list` permission/ContentType upite); warm-uj ContentType keš u `setUp()` da se izbegne order-dependent drift (Epic 6 lekcija). Dva opsega EKSPLICITNO razdvojena od izolovanog stats lock-a.
- **regression:** postojeći `reverse("admin:...")` admin testovi zeleni (override ne lomi default admin).
- **PII guard:** dashboard HTML NE sadrži nijedno ime/email iz seed Lead-ova (AC9).

## SM Decision Log

- **SM-D1 — Admin index override BEZ custom AdminSite (0 blast-radius mount), PINOVAN mehanizam.** epics:1091 kaže „override `AdminSite.index`". Custom `AdminSite` subclass bi zahtevao izmenu `config/urls.py` mount-a (`admin.site.urls` → `my_site.urls`) → lomi svaki `reverse("admin:...")` osim ako se kopira registry, i ruši 8.1 (login_form) + 8.2 (UserAdmin unregister/register na `admin.site`). **ODLUKA (jedan mehanizam, NE „ILI...ILI"):** zadrži DEFAULT `admin.site`; iz `admin_ext/apps.py:ready()` (1) SAČUVAJ `_original_index = admin.site.index` PRE reassignment-a, (2) postavi `admin.site.index = dashboard_index` (wrapper koji injektuje stats u `extra_context` i delegira na `_original_index` → `app_list` zadržan), (3) postavi `admin.site.index_template = "admin_ext/dashboard.html"`. `index_template`-SAM je NEDOVOLJAN (verifikovano protiv `django/contrib/admin/sites.py` 5.2.10: `index()` gradi SVOJ context bez stats) → wrap je OBAVEZAN. `config/urls.py` NETAKNUT. Sva 8.1/8.2 wiring + svi admin reverse-ovi netaknuti.
- **SM-D2 — Zadrži default `app_list` ispod dashboard-a (extra_context, NE zamena).** Dashboard je „statistika IZNAD, standardni admin app-list ISPOD" — Marijana i dalje treba pristup CRUD changelist-ovima (8.4-8.9). Postiže se kroz wrapper koji zove `_original_index(request, extra_context={...})` (original gradi `app_list`) + `templates/admin_ext/dashboard.html` koji `{% extends "admin/index.html" %}` i renderuje stats u `{% block content %}` pre `{{ block.super }}` (default app-list blok). NE praviti potpuno samostalan dashboard koji sakriva navigaciju.
- **SM-D3 — 0 migracija / 0 modela u admin_ext.** Dashboard je čisto read-only agregacija postojećih modela. `admin_ext/models.py` prazan. `makemigrations --check` = No changes (AC regression). Indeks `forms_lead_type_created_idx` (form_type, created_at) VEĆ postoji na Lead-u (4-1, models.py:61 — eksplicitno za „Epic 8.3 segmentovan count") → agregacija je već indeksom podržana, NE treba nova migracija.
- **SM-D4 — Cross-boundary čitanje: admin_ext → domain READ-ONLY, lokalni importi.** project-context:674 zabranjuje da DOMAIN app importuje admin_ext; OBRNUTO (admin_ext čita domain modele) je dozvoljeni, dokumentovani izuzetak (arch:740 „admin_ext proširuje sve admin-e"; mirror pages 3-1 cross-boundary read). Importi `Lead`/`Product`/`Post` UNUTAR funkcija (izbegava import-order/circular probleme; samo `.objects`/count — NIKAD `.save`/`.create`).
- **SM-D5 — Dashboard vidljiv Editoru I Superadmin-u (agregat, ne PII).** epics:1080 Editor „vidi admin panel". Dashboard prikazuje SAMO brojeve/count-ove (ne sirovi lead PII), pa nije razlog za superadmin-only. Pošto je dashboard mountovan kao admin index, standardni admin `is_staff` gate je dovoljan (i Editor i Superadmin su `is_staff`). NE treba dodatni `IsSuperadminMixin`. (Ako bi se ubuduće na dashboard dodali osetljivi podaci, gejtovati `IsSuperadminMixin` iz 8.2.)
- **SM-D6 — GA Reporting API: graceful stub u v1 (NE live integracija).** Postojeći `GA_MEASUREMENT_ID` (base.py:133) je GA4 *client-side measurement ID* za tracking pixel (7.3) — NIJE Reporting API property ID + service-account kredencijali. Nema `google-analytics-data` lib-a u pyproject (verifikovano). Live GA Reporting API zahteva novu dep + GCP service account + property ID = van 8.3 scope-a i van „0 novih dep". **ODLUKA:** `get_ga_visits()` vraća `{"last_7": None, "last_30": None}` (uključiva kasnije kroz `GA_PROPERTY_ID` env + Epic 9 infra); dashboard prikazuje „N/D". AC5 „graceful fallback ako GA timeout" je TIME ispoštovan (fallback je default ponašanje v1). Live GA = OQ-1 (Epic 9).
- **SM-D7 — Lead count = TEKUĆI kalendarski mesec, TZ-aware.** epics:1092 „for current month". Računaj početak meseca iz `timezone.now()` (TIME_ZONE-aware, NE naivni `datetime.now()`), filter `created_at__gte=mesec_start`. Indeks (form_type, created_at) pokriva (G — leftmost form_type, ali range na created_at + group-by je i dalje efikasan).
- **SM-D8 — Single-source segment ključeva iz `Lead.FormType`.** NE hardkoduj `"contact"`/`"model_inquiry"`/... po template-u i stats-u nezavisno. Stats vraća dict ključevан `Lead.FormType.<X>.value`; template iterira poznate segmente sa human-readable labelama (`Lead.FormType.<X>.label` / `get_<>_display`). Sprečava drift kad se doda 5. tip forme.

## Gotchas

- **G-1 — Rekurzivni TEMPLATE extend (distinktno od G-12 metodne rekurzije).** `templates/admin/index.html` koji radi `{% extends "admin/index.html" %}` je BESKONAČNA rekurzija (override fajl postaje i parent). **PINOVANO REŠENJE:** template se zove `templates/admin_ext/dashboard.html` (drugačije ime) i radi `{% extends "admin/index.html" %}` (parent je sad Django-ov ugrađeni, NE samog sebe); `admin.site.index_template = "admin_ext/dashboard.html"`. Task 1 verifikuje.
- **G-12 — Rekurzivni METOD wrap (distinktno od G-1 template rekurzije).** Reassignment `admin.site.index = wrapper` gde wrapper poziva `admin.site.index(...)` je BESKONAČNA METODNA rekurzija (wrapper zove samog sebe). **REŠENJE:** uhvati SAČUVANU referencu PRE reassignment-a (`_original_index = admin.site.index`) i wrapper zove `_original_index(...)` (ILI `AdminSite.index(admin.site, ...)`). G-1 pokriva TEMPLATE rekurziju, G-12 METODNU — dve odvojene zamke; PINOVAN mehanizam (SM-D1/Task 6) izbegava OBE.
- **G-2 — Gubitak `app_list`.** Ako wrapper ne delegira na original ili template ne renderuje app-list, Marijana gubi svu admin navigaciju. Delegiraj na SAČUVAN `_original_index(request, extra_context=...)` (original gradi `app_list`) + template `{{ block.super }}` — SM-D2/G-12.
- **G-3 — INSTALLED_APPS redosled.** `apps.admin_ext` MORA biti POSLE `django.contrib.admin` (već je — admin je u Django blok pre apps.*) i logično POSLE `apps.accounts` (admin wiring sloj). `ready()` override `admin.site` mora se izvršiti pošto je admin app spreman.
- **G-4 — `created_at` granica meseca.** `created_at__month=N` filter IGNORIŠE godinu → lead iz istog meseca prošle godine bi se brojao. Koristi `created_at__gte=<početak_tekućeg_meseca>` (i opciono `__lt=<početak_sledećeg>`), ili `__year=` + `__month=` ZAJEDNO. TZ-aware (SM-D7).
- **G-5 — Naivni `datetime.now()`.** USE `django.utils.timezone.now()` (USE_TZ=True). Naivni datetime → pogrešna granica meseca u zoru/sumrak + warning.
- **G-6 — N+1 zamka: petlja po segmentima.** NE radi `for ft in FormType: Lead.objects.filter(form_type=ft).count()` (4 upita). Jedan `.values("form_type").annotate(Count("id"))` (AC8). Zaključaj `assertNumQueries`.
- **G-7 — Blog `Post.published` manager, NE `Post.objects`.** `blog.Post.objects` vraća SVE (uklj. draft); objavljene su `Post.published` (manager, 5-1 SM-D5 = `status="published" AND published_at__lte=now`). Proizvodi koriste `is_published=True` BooleanField (NEMA published manager-a na Product — verifikovano; products/views.py koristi `.filter(is_published=True)`).
- **G-8 — `reverse("admin:...")` u template-u, ne hardkod URL.** Brze akcije: `{% url 'admin:products_product_add' %}` / `{% url 'admin:blog_post_add' %}` (NE `/admin-coric/products/product/add/` — slug je 8.1 security-through-obscurity, hardkod bi se slomio).
- **G-9 — GA poziv MORA biti fail-safe.** Ako `get_ga_visits()` ikad postane pravi mrežni poziv, BEZ try/except dashboard pada na svaki GA timeout (AC5 prekršen). Wrap je obavezan ČAK i za v1 stub (defensivno).
- **G-10 — PII u logovima.** GA fallback WARNING + bilo koji log NE sme sadržati lead email/ime (project-context:358). Loguj samo poruku tipa „GA visits unavailable".
- **G-11 — Override `admin.site` u testovima.** Pošto `ready()` mutira globalni `admin.site`, override je aktivan u CELOM test suite-u. Potvrdi (Task 8) da postojeći admin testovi (koji očekuju default index) i dalje prolaze (app_list zadržan → trebalo bi da prolaze).

## Open Questions

- **OQ-1 — Live GA Reporting API (Epic 9 forward).** Kad se obezbedi GCP service account + GA4 property ID (`GA_PROPERTY_ID` env, trenutno NE postoji u base.py) + `google-analytics-data` dep, `get_ga_visits()` se „uključuje" (čita real podatke, cache-uje 1h da ne zove API na svaki dashboard load). Defer Epic 9 infra. Do tada dashboard prikazuje signalizirajući placeholder „Posete: N/D — uskoro / Epic 9" (NE goli „N/D" — jasno korisniku da je feature planiran, ne pokvaren; AC5/SM-D6). Biznis treba da potvrdi da li su posete uopšte prioritet za v1.
- **OQ-2 — Dodatne dashboard kartice.** Da li Marijana želi i: nepročitani/novi lead-ovi (status flag — Lead trenutno NEMA status/handled polje, 4-1), poslednjih N lead-ova preview (PII — namerno izostavljeno AC9), trend prošli-vs-tekući mesec. Defer dok klijent ne zatraži (YAGNI).
- **OQ-3 — Brze akcije: koji modeli.** epics traži „Dodaj proizvod" + „Dodaj blog objavu". Da li dodati i „Dodaj brend"/„Dodaj stranicu"? Trenutno tačno 2 (epics literal). Lako proširivo.
- **OQ-4 — Lead status/handled workflow.** Ako se ubuduće doda `Lead.status` (new/handled), dashboard može segmentovati i po statusu. Van 4-1 šeme; defer.

## Dev Notes

### Izvori (cite)

- [Source: epics.md#Story-8.3] (linije 1084-1097) — AC izvor (segmenti, total, GA 7/30, brze akcije, graceful fallback).
- [Source: architecture.md#admin_ext] (622-625) — `admin_ext/{views.py DashboardView, analytics.py GA client, stats.py lead count}`; ova 8.3 PINUJE mehanizam na `index`-wrapper iz `apps.py:ready()` + `stats.py`/`analytics.py` helpere (DashboardView CBV nije potreban jer override ide kroz admin index — SM-D1); (731/740) app-boundary: nijedan domain app ne importuje admin_ext.
- [Source: project-context.md] (199) admin_ext zamenjuje default admin index; (674) domain ne importuje admin_ext; (358) no-PII-in-logs.
- [Source: apps/forms/models.py] — `Lead.FormType` (DB vrednosti `contact`/`model_inquiry`/`service_request`/`part_request`); `created_at` (TimestampedModel); indeks `forms_lead_type_created_idx (form_type, created_at)` eksplicitno za 8.3.
- [Source: apps/accounts/permissions.py] — `IsSuperadminMixin`/`IsEditorMixin` (8.2) na raspolaganju ako dashboard ide kao zaseban CBV (vidi SM-D1/D5 — izabran admin-index override umesto toga).
- [Source: config/urls.py] — admin na bare `/admin-coric/` (8.1), `admin.site.urls` VAN i18n_patterns; NE diraj mount (SM-D1).
- [Source: apps/accounts/apps.py] — `ready()` admin-wiring pattern (login_form 8.1 + post_migrate 8.2) za mirror u admin_ext/apps.py.
- [Source: config/settings/base.py:133] — `GA_MEASUREMENT_ID` = client-side GA4 ID (7.3), NIJE Reporting API kredencijal (SM-D6).

### Project Structure Notes

- NOVI: `apps/admin_ext/{__init__.py, apps.py, models.py (prazan), stats.py, analytics.py, migrations/__init__.py, tests/}` + `templates/admin_ext/dashboard.html` (PINOVANO ime, `{% extends "admin/index.html" %}`). `dashboard_index` wrapper živi u `apps.py` (ili malom `admin_ext/dashboard.py`); `views.py` SAMO ako zatreba — `get_dashboard_stats()`/`get_lead_stats()` u `stats.py` je testabilna jedinica.
- EDIT: `config/settings/base.py` (INSTALLED_APPS += `apps.admin_ext`). `config/urls.py` NETAKNUT (SM-D1). `pyproject.toml` NETAKNUT (0 dep).
- Migracije: **0**. Nove dep: **0**.

### Risk

**RISK TIER: MEDIUM.** Argumentacija (zašto NE HIGH): nema migracija, nema modela, nema state-change POST/forme/HTMX, nema eksternog mrežnog poziva u v1 (GA je stub), nema sirovog PII rendera (samo count-ovi), RBAC se oslanja na već-isporučen 8.1 admin gate (ne uvodi novu auth granicu). Glavni rizici koji ga drže na MEDIUM (ne LOW): (a) override globalnog `admin.site` index-a = sajt-wide admin blast-radius (mitigirano SM-D1 zadržavanjem default site-a + Task 8 broad regression); (b) cross-app READ agregacija (mitigirano lokalnim read-only importima SM-D4); (c) N+1 zamka na segmentaciji (mitigirano AC8 + assertNumQueries); (d) PII-adjacent lead podaci (mitigirano AC9 — samo agregati). NIJE HIGH jer nedostaju svi HIGH okidači prethodnih Epic 8 story-ja (auth backend/middleware blast 8.1, permisije/post_migrate 8.2).

## Dev Agent Record

### Agent Model Used

claude-opus-4-8 (1M context) — Dev (GREEN-phase implementer).

### Debug Log References

- `pytest apps/admin_ext -v` → 24/24 passed.
- `pytest apps -q` → 2015 passed, 2 skipped, 4 xfailed, 0 failed (broad admin-override regression clean).
- `makemigrations admin_ext --check --dry-run` → „No changes detected" (0 migracija; SM-D3).
- `ruff check apps/admin_ext config/settings/base.py` → All checks passed.
- `djade templates/admin_ext/dashboard.html` → formatted ({% trans %}→{% translate %}, {% endblock content %}).

### Completion Notes List

- PINOVAN override implementiran tačno per SM-D1/G-1/G-12: `dashboard.py` hvata
  `_original_index = admin.site.index` na import-u (PRE reassignment-a u
  `apps.py:ready()`) → bez metodne rekurzije; template `admin_ext/dashboard.html`
  `{% extends "admin/index.html" %}` → bez template rekurzije; `{{ block.super }}`
  zadržava `app_list`.
- `get_dashboard_stats()` importuje `get_ga_visits` u `stats` namespace i obavija
  poziv `try/except Exception` (NE bare) → test `test_dashboard_loads_when_ga_raises`
  (monkeypatch na `stats_mod.get_ga_visits`) prolazi (dashboard 200 i kad GA baci).
- `get_lead_stats()` = JEDAN `.values().annotate(Count)` agregat → `assertNumQueries(1)`.
- Segmenti renderovani kao pre-labeled `lead_segments` lista (label iz
  `Lead.FormType.label`, count iz `lead_stats[value]`) — bez `get_item` filtera
  (koji ne postoji u projektu) i bez hardkodovanih stringova (SM-D8).
- **TEST_MODIFICATION (1, genuine bug):** `test_get_content_stats_counts_only_published_products`
  hardkodovao `== 2`, ali brands migracija `0004_seed_hzm_tulip_brands` seed-uje 2
  objavljena Tulip proizvoda u SVAKI test-DB → realan count je 4. Prešao na
  `baseline + 2` deltu; AC4/G-7 invarijanta (unpublished isključen) i dalje TAČNO
  verifikovana. Production `get_content_stats()` je korektan po AC4 — nije menjan.

### File List

NOVI:
- apps/admin_ext/__init__.py
- apps/admin_ext/apps.py
- apps/admin_ext/models.py (prazan — 0 migracija)
- apps/admin_ext/migrations/__init__.py
- apps/admin_ext/stats.py
- apps/admin_ext/analytics.py
- apps/admin_ext/dashboard.py
- templates/admin_ext/dashboard.html

EDIT:
- config/settings/base.py (INSTALLED_APPS += "apps.admin_ext" posle "apps.accounts")
- apps/admin_ext/tests/test_dashboard.py (1 TEST_MODIFICATION — vidi Completion Notes)
