---
story_id: "4.1"
story-key: 4-1-lead-model-smtp-setup
title: Lead Model + SMTP/Email Setup
status: ready-for-dev
epic: 4
epic_num: 4
epic_title: Lead-gen Forms & Email Delivery
module: forms
created: 2026-06-01
last_modified: 2026-06-01
complexity: H
author: Mihas (SM autonomous; PRVA story Epic 4 — Lead-gen Forms & Email Delivery. INFRASTRUKTURA: uvodi NOVI app `apps/forms/` (mirror apps/search 2-13 scaffolding: AppConfig + INSTALLED_APPS reg), `Lead` model (TEMELJ za forme 4-2…4-5), email-sending plumbing (`apps/forms/notifications.py:send_lead_email`), email backend konfiguraciju (dev console VEĆ set; staging/prod anymail Resend), email template-ove (`templates/emails/`), i osnovni LeadAdmin (read-mostly listing). SM-D1 PLACEMENT: NOVI `apps/forms/` (architecture.md:594-600 EKSPLICITNO mapira `forms/ models.py # Lead`, `forms/ notifications.py # send_lead_email helper (sync)`, `forms/ admin.py # LeadAdmin`; epics.md:772 „kreiram apps/forms/models.py sa Lead"). Dep boundary (architecture.md:725/739, project-context.md:665): `forms` je SAMOSTALAN, koristi SAMO `apps/core` utilities; NIKAD ne importuje catalog/blog/products direktno — product context se pass-uje „kroz form fields" (architecture.md:739) → Lead.data JSON drži {„product_slug": ...} (epics.md:802), NEMA FK na products.Product (SM-D3a). SM-D2 ANYMAIL: VEĆ dep (pyproject.toml:8 `django-anymail>=15.0`) — NEMA `uv add`. SM-D3 LEAD FIELDS: form_type (choices KONTAKT/MODEL_INQUIRY/SERVICE_REQUEST/PART_REQUEST — discriminator za sve 4 forme + Epic 8.3 segmentaciju), name, email, phone, message, data (JSONField, form-specific polja), photo (FileField nullable — forward-compat za 4-4 servis), ip_address (GenericIPAddressField), locale (CharField — za lokalizovan subject), nasleđuje TimestampedModel (created_at REUSE; epics.md navodi created_at — POKRIVENO bazom). NEMA translatable polja (lead je raw user-submitted, NE site content). SM-D4 MIGRACIJA: SAMO schema CreateModel (0001_initial) — NEMA data seed (Lead-ovi se kreiraju runtime kroz forme). Indeksi na (form_type, created_at) za Epic 8.3 segmentovan count. SM-D5 EMAIL MEHANIZAM: REUSABLE SERVICE `send_lead_email(lead)` u `apps/forms/notifications.py` (sync — NO Celery, project-context.md:84/127). TRIGGER = VIEW-CALLED (NE post_save signal) — architecture.md:829 data-flow EKSPLICITNO „Save Lead → notifications.send_lead_email()" iz view-a; save-before-send redosled re-grounded na architecture.md:829 + FR-5/PRD:775 reliability (NE na PRD:692 — vidi C2 ispravku); view ORKESTRIRA save+send sinhrono (signal bi vezao email za svaki Lead.create uključujući test/admin/seed = neželjeno). send_lead_email obavija provider-send u try/except + GlitchTip log + vraća bool (C1 failure contract); lead OSTAJE sačuvan na fail-u. 4-2…4-5 view-ovi zovu service eksplicitno. SM-D6 BACKEND: dev=console (development.py:15 VEĆ set); staging/prod=anymail.backends.resend.EmailBackend (epics.md:773). SM-D7 RECIPIENTS: per-segment env (.env.example VEĆ ima CONTACT_EMAIL_TO/SERVICE_EMAIL_TO/PARTS_EMAIL_TO placeholdere); service bira recipient po lead.form_type. SM-D8 ADMIN: read-mostly LeadAdmin (list_display/list_filter form_type+created_at/search_fields) na POSTOJEĆI admin.site (kroz i18n_patterns → /sr/admin/...); puni dashboard sa segmentovanim count = Epic 8.3 (van scope). SM-D9 EMAIL TEMPLATES: `templates/emails/base_email.html` + `lead_received.html` (epics.md:775; Django i18n; subject lokalizovan po lead.locale, epics.md:776). SCOPE BOUNDARY: 4-1 = model + migracija + service + email config + email template-ovi + admin reg + testovi. NEMA forme/view/URL/template-strane/ratelimit/HTMX (4-2…4-6). RISK TIER: HIGH — CreateModel migracija + NOVA external email surface (anymail/Resend) + PII (ime/email/telefon/IP — GDPR-relevantni lični podaci u DB i email-u).)
depends_on:
  - 1-2-multi-environment-settings-split-sa-django-environ  # INSTALLED_APPS; EMAIL_URL env (base.py:97 consolemail default); .env.example email placeholderi; settings split (development.py:15 console backend VEĆ set; staging/production.py email override mesto)
  - 2-1-brand-series-category-subcategory-modeli             # apps/core/models.py TimestampedModel (REUSE base klasa); admin.site.register PATTERN (apps/brands/admin.py); migrations discipline PRECEDENT (manual review + reverse_code)
  - 2-13-global-search-sa-postgresql-fts                     # NOVI-app scaffolding PATTERN (apps/search/: AppConfig SearchConfig name="apps.search" + INSTALLED_APPS reg + tests/ layout) — mirror za apps/forms/
  - 3-3-kontakt-strana-sa-formom-i-mapom                     # `_contact_form.html` forward-compat DISABLED skelet sa „TODO Story 4.2 (Epic 4)" markerom (4-1 polaže Lead+email TEMELJ; 4-2 žica funkcionalnu formu — 4-1 NE dira taj template)
  - 3-4-sitesettings-model-inicijalni-admin                  # MODEL+MIGRACIJA+ADMIN konvencije (TimestampedModel nasleđe; CreateModel migracija manual review; admin pod i18n_patterns → reverse("admin:...") NIKAD hardkodovan /admin/ put; admin recipient izvor OQ-1: SiteSettings vs env)
---

# Story 4.1: Lead Model + SMTP/Email Setup

Status: ready-for-dev

## Opis

As a **dev (koji gradi lead-gen forme u 4-2…4-5)**,

I want **NOVI `apps/forms/` app sa `Lead` modelom (jedinstveno DB skladište za sve 4 vrste formi), reusable `send_lead_email(lead)` email service (sync, kroz `django-anymail`), email backend konfiguraciju (console u dev, Resend u staging/prod), lokalizovane email template-ove, i osnovni read-mostly `LeadAdmin`**,

so that **sve forme (opšti kontakt 4-2, upit za model 4-3, servisni zahtev 4-4, rezervni delovi 4-5) imaju JEDNO mesto za perzistenciju lead-a i JEDAN provereni put za slanje email-a administratoru — pre nego što ijedna funkcionalna forma bude napisana**.

Ovo je **PRVA story Epic 4 (Lead-gen Forms & Email Delivery)** i čista **INFRASTRUKTURA**: TEMELJ na koji se 4-2…4-5 oslanjaju. **U OVOJ STORY NEMA NIJEDNE FORME, VIEW-A, URL-A, NI TEMPLATE-STRANE** — to su 4-2…4-6. Lead-gen tok je teza celog produkta (PRD §1 + PRD:775 „forme moraju da rade od prvog dana") → ovaj temelj mora biti besprekoran i testiran.

### IN SCOPE (šta ova story isporučuje)

1. **NOVI `apps/forms/` app** (SM-D1) — AppConfig (`FormsConfig` `name="apps.forms"`) + registracija u `INSTALLED_APPS` (mirror apps/search 2-13 scaffolding). Dep boundary: `forms` koristi SAMO `apps/core`; NIKAD products/catalog/blog (SM-D3a).
2. **`Lead` model** u `apps/forms/models.py` (SM-D3) — nasleđuje `TimestampedModel` (REUSE `apps/core/models.py`); polja: `form_type` (choices discriminator), `name` (`blank=False` — obavezno za sve form_type-ove), `email`, `phone`, `message`, `data` (JSONField — `data` shape ugovor po form_type, vidi SM-D13), `ip_address`, `locale`. **NEMA `photo` polja u 4-1** — service-request attachment-i (do 3 slike, multi-upload, epics.md:814) su scope Story 4-4 kroz dedikovan `LeadAttachment` child model (FK→Lead, `on_delete=CASCADE`, `related_name="attachments"`) + MIME validacija; jedan `FileField` fizički ne može držati 3 fajla → 4-1 NE nosi foto polje (SM-D14). NEMA FK na druge app-ove (`data` JSON drži product context), NEMA translatable polja.
3. **Schema migracija** `apps/forms/migrations/0001_initial.py` (CreateModel — manuelno reviewovana, SM-D4) sa indeksom na `(form_type, created_at)` (Epic 8.3 segmentovan count). **NEMA data seed.**
4. **Email service** `apps/forms/notifications.py:send_lead_email(lead)` (SM-D5) — sync; bira recipient po `lead.form_type` (lowercase DB vrednosti); rendera lokalizovan subject (po `lead.locale`) + telo iz template-a; šalje kroz konfigurisani `EMAIL_BACKEND` (anymail u prod). View-called (NE signal). **Failure contract (C1): provider send u try/except + GlitchTip-capturable log + vraća `bool`; prima VEĆ sačuvanu Lead instancu (save-before-send ugovor za 4-2+).**
5. **Email template-ovi** (SM-D9) — `templates/emails/base_email.html` + `templates/emails/lead_received.html` (Django i18n; epics.md:775).
6. **Email backend + settings/env** (SM-D6/SM-D7) — staging/prod `EMAIL_BACKEND = "anymail.backends.resend.EmailBackend"` + `ANYMAIL` config; env-vars `ANYMAIL_RESEND_API_KEY`, `DEFAULT_FROM_EMAIL`, per-segment recipienti (`CONTACT_EMAIL_TO`/`SERVICE_EMAIL_TO`/`PARTS_EMAIL_TO` VEĆ u .env.example; dodati eventualno chybějící + `ANYMAIL_RESEND_API_KEY`/`DEFAULT_FROM_EMAIL`). Dev ostaje console (development.py:15 VEĆ set — NE dira se).
7. **Osnovni `LeadAdmin`** `apps/forms/admin.py` (SM-D8) — read-mostly registracija na POSTOJEĆI `admin.site` (`list_display`, `list_filter`, `search_fields`).

### OUT OF SCOPE (eksplicitno — granice)

- **NIJEDNA forma, view, URL, template-strana, ratelimit, ni HTMX** — `ContactForm`/`ModelInquiryForm`/`ServiceRequestForm`/`PartRequestForm`, `apps/forms/views.py`, `apps/forms/urls.py`, `apps/forms/forms.py`, `templates/forms/partials/*`, `@ratelimit` dekoratori, `hx-post` endpoint-i, success/error partials = **Story 4-2 (opšti kontakt FR-5), 4-3 (model inquiry), 4-4 (servis + foto upload), 4-5 (rezervni delovi), 4-6 (HTMX pattern + aria-live OOB + ratelimit)**. 4-1 SAMO polaže model+email temelj. (Mirror 3-4 boundary: model story NE žica forme/view-ove.)
- **`_contact_form.html` (3-3 disabled skelet)** — NE dira se u 4-1. Njegov `{# TODO Story 4.2 (Epic 4) #}` marker razrešava **Story 4-2** (žica funkcionalan `ContactForm` + `hx-post` + ratelimit). 4-1 NE uklanja `disabled`, NE žica submit.
- **Admin Dashboard sa segmentovanim lead-count-om** = **Epic 8 Story 8.3** (`apps/admin_ext/views.py:DashboardView` + `apps/admin_ext/stats.py:get_lead_stats()`; epics.md:1084-1097). 4-1 daje SAMO osnovni `LeadAdmin` changelist (read-mostly listing + filter); NE pravi dashboard, NE `stats.py`. `list_filter`/`search_fields` ovde su za ručni admin pregled, ne za dashboard agregaciju.
- **`/admin-coric/` custom admin URL slug + django-axes login hardening** = **Epic 8 Story 8.1**. Admin je danas mount-ovan na `path("admin/", admin.site.urls)` UNUTAR `i18n_patterns` → stvarni URL je `/sr/admin/...` (NE bare `/admin/...`). 4-1 registruje `Lead` na taj POSTOJEĆI `admin.site` (mirror 3-4 SM-D6); testovi/smoke koriste `reverse("admin:forms_lead_changelist")` (NIKAD hardkodovan put).
- **`ServiceRequest` / `PartRequest` zasebni modeli** (architecture.md:595 nabraja „Lead (sa form_type discriminator), ServiceRequest, PartRequest") — **NAMERNO IZOSTAVLJENI u v1.** epics.md:772 (AUTHORITATIVE story spec) eksplicitno koristi JEDAN `Lead` model sa `form_type` discriminatorom + `data` JSONField za form-specific polja (epics.md:802/830 „svi specifični podaci u Lead.data JSON"). Zasebni `ServiceRequest`/`PartRequest` modeli bili bi premature abstrakcija (project-context.md:357) — `Lead.data` JSON pokriva sve 4 shape-a. Ako future scale traži normalizovane tabele, dodaje se kasnije (NE blokira v1). Vidi SM-D3.
- **Foto/attachment polje + `LeadAttachment` child model** = **Story 4-4 (servisni zahtev).** epics.md:814 traži multi-upload do 3 slike + email „sa attach-ovanim slikama" (epics.md:818) — JEDAN `FileField` fizički ne može držati 3 fajla, pa 4-1 NE uvodi `photo` polje uopšte (izbegava pogrešan single-file field + mid-sprint migraciju u 4-4). 4-4 vlasnik je attachment modela: dedikovan `LeadAttachment` (FK→Lead `on_delete=CASCADE`, `related_name="attachments"`, `file = FileField(upload_to="leads/attachments/")`) + MIME/veličina validacija (Image MIME iz 2.3, max 5MB/fajl, do 3) + proširenje `send_lead_email` da attach-uje slike. Pošto Lead model još NE postoji, NEMA migracionog troška sada (SM-D14). Vidi „Story 4-4 precondition" niže.
- **Product FK na Lead** — NE. Product context (4-3 model inquiry) ide kroz `Lead.data = {"product_slug": ...}` (epics.md:802), NE FK. RAZLOG: architecture.md:739 „forms NIKAD ne sme importovati catalog/blog direktno; context pass-uje se kroz form fields" + dep boundary (forms je samostalan, koristi samo core) → FK na products.Product bi uveo zabranjenu cross-app zavisnost. Vidi SM-D3a + OQ-3.
- **`SiteSettings`-bazirano admin podešavanje recipient-a** — v1 koristi env baseline (SM-D7; epics.md:773 „env baseline"). Admin-editable recipient (SiteSettings polje) = potencijalno Epic 8 8.9 (OQ-1). 4-1 čita recipient iz settings/env.
- **Real Resend API ključ / verifikovan sender domen** = biznis/ops zadatak (OQ-4). 4-1 daje env-var placeholder; dev/test NE šalje pravi email (console/locmem).
- **Celery / async email queue** — NE (project-context.md:84/127 — bez Celery/Redis u v1; email send je SYNC).
- **GDPR PII retencija / pravo na zaborav / anonimizacija** = **Epic 7 (GDPR & Privacy)** (SM-D12). `Lead` skladišti PII (`name`/`email`/`phone`/`ip_address`; attachment-i kroz 4-4 `LeadAttachment`); data-retention politika, right-to-erasure i anonimizacija su Epic 7 — 4-1 SAMO uvodi durabilno DB skladište (SM-D11), NE retention/erasure logiku. `ip_address` se u v1 čuva neograničeno do Epic 7. (Mirror admin-editable recipient deferral u Epic 8.9.)

### Princip

Jedan NOVI app + jedan model + jedna schema migracija (NEMA data seed) + jedan email service (sync, view-called) + 2 email template-a + email backend/env config + osnovni admin. Model nasleđuje `TimestampedModel` (REUSE). NEMA FK (product context kroz `Lead.data` JSON — dep boundary). NEMA translatable polja (lead je raw user input, NE site content). NEMA novog dep-a (`django-anymail` VEĆ u pyproject.toml). NEMA forme/view/URL/HTMX (4-2…4-6). Email subject lokalizovan po `lead.locale` kroz `gettext` runtime (project-context.md:136). Testovi koriste Django `locmem` backend + `mailoutbox` fixture — NIKAD pravi send (project-context.md:267-271). Pune dijakritike (č/ć/ž/š/đ) u verbose_name-ovima i email subject/telu. NEMA defensive validacije (project-context.md:358), NEMA premature abstrakcije (jedan Lead model, NE ServiceRequest/PartRequest split).

### Strukturna arhitektura — repository delta

**NOVI app `apps/forms/` (7 fizičkih fajlova) + 2 email template-a + settings/env EDIT + 1 INSTALLED_APPS EDIT + 0 DELETE + 0 CSS + 0 JS + 0 forme/view/URL.**

| Path | Tip | Razlog |
|---|---|---|
| `apps/forms/__init__.py` | NOVO | Python package marker. |
| `apps/forms/apps.py` | NOVO | `class FormsConfig(AppConfig)` `default_auto_field="django.db.models.BigAutoField"` `name="apps.forms"` (mirror `apps/search/apps.py` SearchConfig). |
| `apps/forms/models.py` | NOVO | `class Lead(TimestampedModel)` (import `TimestampedModel` iz `apps.core.models`) — polja iz AC1; `form_type` choices (`TextChoices`); `name` CharField(`blank=False`); `data` JSONField default=dict (shape ugovor SM-D13); `ip_address` GenericIPAddressField(null=True, blank=True); `locale` CharField(max_length=10, default="sr", blank=True); `__str__` → npr. „{get_form_type_display()}: {name} ({created_at})"; `Meta.verbose_name`/`_plural` puni dijakritik + `Meta.ordering=["-created_at"]` + `Meta.indexes` na `(form_type, created_at)`. **NEMA `photo` polja** (attachment-i = 4-4 `LeadAttachment` child model — SM-D14). NEMA FK; NEMA get_absolute_url (lead nije content sa javnom stranom — izuzetak od project-context.md:158, isto kao 3-4 SiteSettings). |
| `apps/forms/notifications.py` | NOVO | `send_lead_email(lead)` (sync — SM-D5): rezolvuje recipient po `lead.form_type` (DB vrednosti: `"contact"`→CONTACT_EMAIL_TO, `"service_request"`→SERVICE_EMAIL_TO, `"part_request"`→PARTS_EMAIL_TO, `"model_inquiry"`→CONTACT_EMAIL_TO; vidi SM-D7 — mapiranje koristi `Lead.FormType` member-e, NE sirove stringove), rendera subject (lokalizovan po `lead.locale` kroz `gettext` runtime + `translation.override(lead.locale)`) + telo iz `templates/emails/lead_received.html`, šalje kroz Django `django.core.mail.EmailMultiAlternatives` / `send_mail` (anymail backend transparentno u prod; from=`DEFAULT_FROM_EMAIL`). **Provider send je obavijen `try/except` + GlitchTip-capturable log + jasna success/failure povratna semantika (vidi AC4 C1 ugovor).** VIEW-CALLED (NE signal). 4-4 dodaje attach slika (kroz `LeadAttachment` child model — SM-D14): to je 4-4 proširenje `send_lead_email` (`email.attach(...)` po vezanom attachment-u); 4-1 service podržava SAMO telo+subject (NEMA attach hook u 4-1). |
| `apps/forms/admin.py` | NOVO | `@admin.register(Lead)` read-mostly `ModelAdmin` (`list_display=("form_type","name","email","phone","created_at")`, `list_filter=("form_type","created_at")`, `search_fields=("name","email","message")`; opciono `readonly_fields`/`date_hierarchy`). Registracija na POSTOJEĆI `admin.site` (mirror `apps/brands/admin.py`). NE dashboard (Epic 8.3). |
| `apps/forms/migrations/__init__.py` | NOVO | Package marker (migrations dir ne postoji — NOVI app). |
| `apps/forms/migrations/0001_initial.py` | GENERISANO + MANUAL REVIEW | `makemigrations forms` — CreateModel `Lead` + index `(form_type, created_at)`. Dev MANUELNO reviewuje (project-context.md:221). NEMA modeltranslation kolona (nema translatable polja). |
| `templates/emails/base_email.html` | NOVO | Bazni email layout (epics.md:775 — `{% extends "emails/base_email.html" %}`); minimalan HTML skelet + `{% block content %}`; Django i18n (`{% load i18n %}`). NEMA inline CSS magic (ali email HTML je izuzetak gde inline stil JESTE norma za email klijente — dokumentovano u SM-D9; ipak držati minimalno). |
| `templates/emails/lead_received.html` | NOVO | `{% extends "emails/base_email.html" %}`; rendera lead polja (ime, email, telefon, poruka, form_type, data JSON ključevi); Django i18n `{% translate %}`. Pune dijakritike. |
| `config/settings/base.py` | EDIT | `apps.forms` u `INSTALLED_APPS` (POSLE `apps.pages`/domain app-ova — forms je samostalan top-level). DODATI baseline email setting-e ako fale: `DEFAULT_FROM_EMAIL`, `SERVER_EMAIL`, per-segment recipient setting-e iz env (`CONTACT_EMAIL_TO`/`SERVICE_EMAIL_TO`/`PARTS_EMAIL_TO` kroz `env(...)`), i `ANYMAIL` dict (`{"RESEND_API_KEY": env("ANYMAIL_RESEND_API_KEY", default="")}`). NE dirati postojeći `EMAIL_URL`/`consolemail` default (dev path ostaje; SM-D6). |
| `config/settings/staging.py` + `config/settings/production.py` | EDIT | `EMAIL_BACKEND = "anymail.backends.resend.EmailBackend"` (override consolemail; epics.md:773). (Dev `development.py:15` console backend OSTAJE — NE dira se.) |
| `.env.example` | EDIT | DODATI `ANYMAIL_RESEND_API_KEY=`, `DEFAULT_FROM_EMAIL=` (npr. `no-reply@coricagrar.rs`); `CONTACT_EMAIL_TO`/`SERVICE_EMAIL_TO`/`PARTS_EMAIL_TO` VEĆ postoje (`:63-65`) — eventualno popuniti komentar/default. NON-FINAL placeholder marker (mirror 3-4 SM-D11). |
| `apps/forms/tests/*` | NOVO (TEA) | RED-phase testovi (vidi Testing). Dev NE piše testove. `apps/forms/tests/__init__.py` + `conftest.py` + test fajlovi (mirror apps/search/tests layout). |
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | EDIT | `4-1-lead-model-smtp-setup` → `ready-for-dev`. SM handoff tracking (NIJE deliverable). |

**NETAKNUTO (regression guards):** `apps/core/models.py` (TimestampedModel REUSE — NE menja se); `config/settings/development.py` (console backend `:15` OSTAJE — dev NE šalje pravi email; SM-D6); `templates/pages/partials/_contact_form.html` (3-3 disabled skelet — 4-2 ga žica, NE 4-1); `pyproject.toml` (NEMA novog dep — `django-anymail>=15.0` VEĆ `:8`; SM-D2); `config/urls.py` (NEMA novih URL-ova — forms urls.py dolazi u 4-2); sve postojeće app-ove (`brands/products/search/pages/media_pipeline/core`); sve CSS/JS (0 novih, 0 izmena); sve postojeće template-strane.

## Kriterijumi prihvatanja

**AC1 — `Lead` model u `apps/forms/models.py`; nasleđuje `TimestampedModel`; tačna polja; `__str__`; `system check` čist (SM-D3)**

- **Given** `apps/core/models.py` `TimestampedModel` (Story 2.1, REUSE); NOVI `apps/forms/` app registrovan (AC7); dep boundary forms→core only (SM-D3a)
- **When** kreiram `class Lead(TimestampedModel)` u `apps/forms/models.py`
- **Then** model MORA imati TAČNO ova polja (sva plain — NEMA translatable):
  - `form_type` — `CharField(max_length=20, choices=...)` sa `choices` iz nested `TextChoices`. **DB vrednosti MORAJU biti TAČNO lowercase stringovi koje nizvodne story-je query-uju** (epics.md:791 `Lead.form_type = 'contact'`; epics.md:802 `Lead.form_type = 'model_inquiry'`; 4-2/4-3/4-4/4-5 + Epic 8.3 segmentacija filtriraju/broje po `'contact'`/`'model_inquiry'`/`'service_request'`/`'part_request'`). Python member imena ostaju uppercase (čitljivost), ali DB vrednost = lowercase string, a `label` puni dijakritik kroz `gettext_lazy`:
    ```python
    class FormType(models.TextChoices):
        KONTAKT = "contact", _("Opšti kontakt")
        MODEL_INQUIRY = "model_inquiry", _("Upit za model")
        SERVICE_REQUEST = "service_request", _("Servisni zahtev")
        PART_REQUEST = "part_request", _("Upit za rezervni deo")
    ```
    Mapira epics.md:772 choice listu [contact/model_inquiry/service_request/part_request] 1:1. **DB vrednosti (lowercase) su stabilan ugovor za 4-2…4-5 + Epic 8.3** — NE menjati posle. `max_length` MORA pokriti najduži DB string `"service_request"` (15 znakova) — koristi `max_length=20` (sigurna margina).
  - `name` — `CharField(max_length=200)` — **`blank=False` (obavezno za sve form_type-ove: kontakt/model_inquiry/service_request/part_request — svaka forma traži ime; epics.md:801/814/829 sve liste „Ime *")**
  - `email` — `EmailField`
  - `phone` — `CharField` (npr. max_length=50; `blank=True` — neki form_type-ovi telefon ne traže kao obavezan, npr. opšti kontakt)
  - `message` — `TextField` (`blank=True` — npr. model_inquiry poruka opciona)
  - `data` — `JSONField(default=dict, blank=True)` — form-specific polja po `form_type` (**shape ugovor — vidi SM-D13**: `contact` → `{}`; `model_inquiry` → `{"product_slug": "<slug>", "product_name": "<display>"}` (locked — 4-3 zavisi); `service_request`/`part_request` → form-specifični ključevi finalizovani u svojoj consumer story-ji). NIKAD `default={}` mutable (koristi `default=dict`).
  - `ip_address` — `GenericIPAddressField(null=True, blank=True)` (epics.md:772 `ip_address`; popunjava ga view u 4-2+ iz `request`)
  - `locale` — `CharField(max_length=10, default="sr", blank=True)` — lokala submit-a; koristi se za lokalizovan email subject (epics.md:776). `blank=True` je safety valve (view UVEK postavlja `locale` iz `request`, ali polje ne sme blokirati validaciju ako izostane); `default="sr"` je fallback.
  - (nasleđeno iz `TimestampedModel`: `created_at`, `updated_at` — epics.md:772 navodi `created_at`, POKRIVENO bazom)
- **And** `__str__` vraća informativan string (npr. `f"{self.get_form_type_display()}: {self.name}"`)
- **And** `Meta.verbose_name = "Lead"`, `verbose_name_plural = "Lead-ovi"` (ili „Upiti" — puni dijakritik); `Meta.ordering = ["-created_at"]`
- **And** `data` JSON poštuje shape ugovor po `form_type` (SM-D13; `model_inquiry.data["product_slug"]` je locked za 4-3); **NEMA `photo`/attachment polja na Lead-u** (attachment-i = 4-4 `LeadAttachment` child model — SM-D14)
- **And** NEMA FK (product context ide kroz `data` JSON — SM-D3a); NEMA `get_absolute_url` (lead nije content sa javnom stranom — izuzetak od project-context.md:158, isto kao 3-4 SiteSettings); NEMA translatable polja (NEMA `apps/forms/translation.py`)
- **And** `uv run python manage.py check` exit 0; NEMA defensive validacije (project-context.md:358)

**AC2 — Schema migracija `0001_initial` (CreateModel) + index `(form_type, created_at)`; manuelno reviewovana; reverzibilna; NEMA data seed (SM-D4)**

- **Given** AC1; NOVI `apps/forms/` u INSTALLED_APPS (AC7)
- **When** pokrenem `uv run python manage.py makemigrations forms`
- **Then**:
  - Generiše se `apps/forms/migrations/0001_initial.py` sa `CreateModel("Lead", ...)` + `apps/forms/migrations/__init__.py` (package marker)
  - Migracija sadrži `models.Index(fields=["form_type", "created_at"], name="...")` (Epic 8.3 segmentovan count po form_type za current month — index ubrzava filter+count; SM-D4)
  - **`form_type` kolona `max_length` MORA pokriti najduži DB string `"service_request"` (15 znakova)** — review-checklist tačka: potvrdi `max_length >= 15` (story koristi `max_length=20`); kraći `max_length` bi tiho odsekao/odbio `"service_request"`/`"part_request"` vrednosti i polomio nizvodni query (SM-D3, C3)
  - NEMA modeltranslation `_sr/_hu/_en` kolona (Lead nema translatable polja)
  - **NEMA data seed migracije** — Lead-ovi se kreiraju runtime kroz forme (4-2+); za razliku od 3-4 SiteSettings (koji je seed-ovan), Lead startuje prazan (SM-D4)
  - Dev MANUELNO reviewuje fajl (project-context.md:221); `uv run python manage.py migrate --plan` prikazuje plan
  - `uv run python manage.py migrate forms` primeni; `migrate forms zero` reverzuje čisto (CreateModel auto-reverzibilan)
- **And** migracija + model promene se commit-uju ZAJEDNO (atomic; project-context.md:223); NIJE editovana posle apply-a (project-context.md:226)

**AC3 — NOVI `apps/forms/` app scaffolding + INSTALLED_APPS registracija (SM-D1)**

- **Given** apps/search 2-13 NOVI-app PATTERN (`SearchConfig`); dep boundary forms→core only (architecture.md:725/739)
- **When** kreiram `apps/forms/` app
- **Then**:
  - `apps/forms/__init__.py` + `apps/forms/apps.py` (`class FormsConfig(AppConfig)`, `default_auto_field="django.db.models.BigAutoField"`, `name="apps.forms"`) postoje (mirror `apps/search/apps.py`)
  - `apps.forms` dodat u `INSTALLED_APPS` (config/settings/base.py) — POSLE domain app-ova (forms je samostalan top-level; redosled ne uvodi cross-app reg problem jer forms nema modeltranslation)
  - **Dep boundary verifikovan:** `apps/forms/` NIGDE ne importuje `apps.products`/`apps.brands`/`apps.search`/hipotetički `catalog`/`blog` (project-context.md:665; architecture.md:739). Importuje SAMO `apps.core` (TimestampedModel) + Django + anymail.
- **And** `uv run python manage.py check` exit 0; app se pojavljuje u `manage.py showmigrations forms`

**AC4 — Email service `send_lead_email(lead)` (`apps/forms/notifications.py`) — sync, view-called; lokalizovan subject; recipient po form_type; FAILURE CONTRACT (try/except + GlitchTip log + return bool); save-before-send ugovor (SM-D5/SM-D7)**

- **Given** AC1 (Lead instanca); EMAIL_BACKEND konfigurisan (AC6); recipient env (SM-D7)
- **When** kreiram `apps/forms/notifications.py:send_lead_email(lead)` i pozovem ga sa sačuvanom Lead instancom
- **Then**:
  - Funkcija je SYNC (`def`, NE `async`; NO Celery — project-context.md:84/127)
  - Rezolvuje RECIPIENT po `lead.form_type` (SM-D7; poredi sa `Lead.FormType` member-ima, NE sirovim literalima): `FormType.SERVICE_REQUEST` (DB `"service_request"`) → `SERVICE_EMAIL_TO`, `FormType.PART_REQUEST` (DB `"part_request"`) → `PARTS_EMAIL_TO`, `FormType.KONTAKT` (DB `"contact"`) / `FormType.MODEL_INQUIRY` (DB `"model_inquiry"`) → `CONTACT_EMAIL_TO` (model_inquiry ide na isti kontakt/prodaja recipient kao opšti kontakt — epics.md ne specifikuje zaseban model-inquiry recipient; OQ-2 ako biznis traži razdvajanje)
  - SUBJECT je lokalizovan po `lead.locale` (epics.md:776) — koristi `django.utils.translation.override(lead.locale)` + `gettext` runtime (project-context.md:136 „email subjects: gettext runtime"). Format mapira epics.md:790/803/831 (npr. „[Ćorić Agrar] Novi kontakt: {name}", „[Ćorić Agrar] Upit za model: {...}") — pune dijakritike.
  - TELO se rendera iz `templates/emails/lead_received.html` (AC5) — `render_to_string` sa lead context-om
  - FROM = `settings.DEFAULT_FROM_EMAIL`
  - Šalje kroz Django mail API (`EmailMultiAlternatives` / `send_mail`) → backend-agnostično (console u dev, anymail/Resend u prod). NE poziva Resend API direktno (anymail apstrakcija — architecture.md:783).
  - **TRIGGER = VIEW-CALLED (NE post_save signal):** funkcija je pozvana EKSPLICITNO iz form view-a u 4-2…4-5 (architecture.md:829 „Save Lead → notifications.send_lead_email()"). 4-1 NE registruje `post_save` signal na Lead (signal bi okinuo email na SVAKI Lead.create — uključujući testove, admin ručni unos, buduće seed/import — neželjeno). NEMA `apps/forms/signals.py`, NEMA `signal` wiring u `apps.py`.
  - **PERSISTENCE ORDER (ugovor za 4-2+):** Lead MORA biti perzistiran (`lead.save()` / `Lead.objects.create(...)`) u DB PRE nego što se pokuša email send. View u 4-2…4-5 vlasnik je redosleda **save-then-send** (architecture.md:829 „Save Lead → notifications.send_lead_email()") → fail provider-a NIKADA ne sme izgubiti lead. 4-1 zaključava ovaj ugovor; `send_lead_email(lead)` prima VEĆ sačuvanu instancu (sa `lead.pk`). **Svaki 4-2…4-5 view MORA posle `lead.save()` pozvati `send_lead_email(lead)` i obraditi `bool` rezultat (SM-D15 guardrail); 4-2 MORA imati test koji asertuje da view zove `send_lead_email`.**
  - **FAILURE CONTRACT (provider send može pasti — to je NAJVEROVATNIJI prod-fail, NE nemoguć slučaj):** eksterni provider fail (Resend 500 / timeout / loš/prazan API key / neverifikovan sender / prazan recipient) MORA biti obrađen. `send_lead_email(lead)` **MORA obaviti SAM provider-send poziv u `try/except`** (specifičan exception, NE bare `except:` — project-context.md:121), **LOGOVATI fail kroz `logger.exception(...)`** (GlitchTip-capturable — project-context.md:125 „sve unhandled exceptions → GlitchTip capture"; eksplicitan `logger.exception` čini failed send observable i kad ga uhvatimo), i **VRATITI `bool`** (`True` = send uspeo, `False` = send pao). **Zaključana semantika: catch + log + return bool** (NE re-raise) — view u 4-2 reaguje na povratnu vrednost (npr. uvek prikaže success korisniku jer je lead sačuvan, a admin dobija GlitchTip alert o failed send-u; ili prikaže degradiran success — odluka prezentacije je 4-2). Lead OSTAJE sačuvan u oba slučaja (save je prethodio send-u; `except` NE briše/rollback-uje red).
  - **PRAZAN/NEDOSTAJUĆI RECIPIENT:** ako je rezolvovani recipient prazan (env nije popunjen — realan dev/staging slučaj pre OQ-4), `send_lead_email` NE sme da baci neuhvaćeno; tretira se kao failed send (log `logger.exception`/`logger.error` + return `False`) — lead ostaje sačuvan, fail je observable. (Ovo je deo C1 send-failure puta, NE opšta defensive validacija.)
- **And** logika obrade fail-a (try/except + log + return bool) pokriva SAMO eksterni provider-send put; pravilo „NEMA defensive validacije za nemoguće slučajeve" (project-context.md:358) i dalje važi za interne nemoguće slučajeve (npr. NE validiraj da je `lead` instanca, NE proveravaj polja koja je model već garantovao). Eksterni email send NIJE nemoguć slučaj — on je boundary ka third-party servisu i MORA se obraditi.

**AC5 — Email template-ovi `base_email.html` + `lead_received.html` (Django i18n; pune dijakritike) (SM-D9)**

- **Given** AC4 (service rendera telo); epics.md:775 (`{% extends "emails/base_email.html" %}`)
- **When** kreiram `templates/emails/base_email.html` + `templates/emails/lead_received.html`
- **Then**:
  - `templates/emails/base_email.html` — minimalan email HTML skelet sa `{% block content %}`; `{% load i18n %}`
  - `templates/emails/lead_received.html` — `{% extends "emails/base_email.html" %}`; rendera lead polja (ime, email, telefon, poruka, prikaz form_type kroz `get_form_type_display`, relevantni `data` ključevi); sve labele kroz `{% translate %}` — pune dijakritike (č/ć/ž/š/đ); NEMA ćirilice, NEMA šišane latinice
  - Render NE baca pri `render_to_string` sa Lead context-om (AC4)
- **And** email HTML SME imati inline stil (email klijenti zahtevaju inline CSS — dokumentovan izuzetak od project-context.md:317 koji se odnosi na web template-e; držati minimalno, bez magic-value web tokena)

**AC6 — Email backend konfiguracija (dev console; staging/prod anymail Resend) + ANYMAIL/env settings (SM-D6/SM-D2)**

- **Given** `django-anymail>=15.0` VEĆ dep (pyproject.toml:8 — NEMA `uv add`; SM-D2); dev console backend VEĆ set (development.py:15); base.py `EMAIL_URL` consolemail default (`:97`)
- **When** konfigurišem email backend per environment
- **Then**:
  - **Dev:** `config/settings/development.py:15` (`EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"`) OSTAJE NETAKNUT — dev email ide u konzolu (NE šalje pravi email)
  - **Staging + Production:** `EMAIL_BACKEND = "anymail.backends.resend.EmailBackend"` (epics.md:773) — EKSPLICITAN assignment POSLE `from .base import *` ISPRAVNO override-uje base `vars().update(EMAIL_CONFIG)` consolemail vrednost (kasniji modul-level assignment pobeđuje; vidi Project Structure Notes). **NE uklanjati `EMAIL_URL`/`vars().update` iz base.py.**
  - `config/settings/base.py` ima: `DEFAULT_FROM_EMAIL` (iz env, default npr. `"no-reply@coricagrar.rs"`), `SERVER_EMAIL`, `ANYMAIL = {"RESEND_API_KEY": env("ANYMAIL_RESEND_API_KEY", default="")}`, i per-segment recipient setting-e (`CONTACT_EMAIL_TO`/`SERVICE_EMAIL_TO`/`PARTS_EMAIL_TO` iz env sa bezbednim default-om za dev)
  - `.env.example` ima `ANYMAIL_RESEND_API_KEY=`, `DEFAULT_FROM_EMAIL=`; postojeći `CONTACT_EMAIL_TO`/`SERVICE_EMAIL_TO`/`PARTS_EMAIL_TO` (`:63-65`) zadržani; NON-FINAL placeholder marker (mirror 3-4 SM-D11 — real key/recipient = OQ-4 biznis input)
- **And** `uv run python manage.py check` exit 0 u svim env-ovima; NEMA `uv add` (SM-D2)
- **And** TEST env koristi Django `locmem` backend (pytest-django override) — NIKAD pravi send (project-context.md:267)

**AC7 — Osnovni read-mostly `LeadAdmin` (`apps/forms/admin.py`) na POSTOJEĆI `admin.site`; list_display/list_filter/search_fields (SM-D8)**

- **Given** AC1; `apps/brands/admin.py` registracija PATTERN; admin mount-ovan UNUTAR `i18n_patterns` (stvarni URL `/sr/admin/...`, 3-4 SM-D6)
- **When** kreiram `apps/forms/admin.py` sa `ModelAdmin` za `Lead`
- **Then**:
  - `Lead` registrovan na `admin.site` (`@admin.register(Lead)`) — pojavljuje se u admin app listi
  - `list_display = ("form_type", "name", "email", "phone", "created_at")` (project-context.md:200)
  - `list_filter = ("form_type", "created_at")` (segmentacija po vrsti — temelj za ručni pregled; PUNI dashboard count = Epic 8.3)
  - `search_fields = ("name", "email", "message")` (project-context.md:200)
  - Read-mostly: opciono `readonly_fields` (created_at/updated_at/ip_address) + `date_hierarchy = "created_at"` (lead je primljen podatak, ne admin-kreiran content)
  - URL-ovi se razrešavaju kroz `reverse("admin:forms_lead_changelist")` / `reverse("admin:forms_lead_change", args=[obj.pk])` (admin pod `i18n_patterns` — NIKAD hardkodovan `/admin/...` ni `/sr/admin/...`; 3-4 SM-D6)
- **And** NIJE dashboard (Epic 8.3), NIJE custom admin slug/axes (Epic 8.1) — dokumentovano (SM-D8)
- **And** superuser klijent → `reverse("admin:forms_lead_changelist")` GET → HTTP 200

**AC8 — Email integracioni put: `Lead.objects.create(...)` + `send_lead_email(lead)` radi end-to-end u test/dev (epics.md:774)**

- **Given** AC1-AC6; `locmem` email backend u testu (`mailoutbox` fixture — project-context.md:271)
- **When** u testu (ili `manage.py shell` u dev sa console backend) kreiram `Lead.objects.create(form_type=Lead.FormType.KONTAKT, name="Marko Marković", email="marko@example.com", phone="+381...", message="...", locale="sr")` i pozovem `send_lead_email(lead)`
- **Then**:
  - Lead je perzistiran PRE send-a (`Lead.objects.count() == 1`; save-before-send ugovor AC4)
  - `send_lead_email(lead)` vraća `True` (uspešan send — failure contract AC4 vraća `False` na provider fail)
  - TAČNO JEDAN email u `mailoutbox` (`len(mailoutbox) == 1`)
  - `mailoutbox[0].to` = ispravan recipient po form_type (SM-D7)
  - `mailoutbox[0].from_email` = `settings.DEFAULT_FROM_EMAIL`
  - `mailoutbox[0].subject` sadrži lokalizovan, pun-dijakritik string (npr. „[Ćorić Agrar] Novi kontakt: ...") — po `lead.locale`
  - `mailoutbox[0].body` (ili alternatives) sadrži lead podatke (ime/email/poruka)
  - Sync ponašanje: email je poslat NAKON `send_lead_email(lead)` poziva, u istom request/thread-u (NE odloženo — NO Celery)
- **And** NIKAD pravi network send (locmem u testu; console u dev — project-context.md:267)

**AC9 — i18n: email subject lokalizovan po `lead.locale`; nema hardcoded ćirilice/šišane latinice (epics.md:776)**

- **Given** AC4 (subject po locale); LANGUAGES [sr,hu,en]
- **When** pozovem `send_lead_email(lead)` za lead-ove sa `locale="sr"`, `locale="hu"`, `locale="en"`
- **Then**:
  - Subject + telo se renderuju u odgovarajućoj lokali (kroz `translation.override(lead.locale)`); sr je default/fallback (`MODELTRANSLATION_FALLBACK_LANGUAGES=("sr",)` — ali za UI gettext fallback je `LANGUAGE_CODE="sr"`)
  - sr render → pune dijakritike (č/ć/ž/š/đ); NEMA ćirilice, NEMA šišane latinice
  - hu/en stringovi prevedeni kroz `gettext` (msgid u .po; ako prevod fali → fallback sr — prihvatljivo, isto kao 3-4 AC10 politika)
  - **Novi email msgid-ovi (subject format-i + telo labele) su dodati u `.po` i kompajlirani kroz `just messages` (makemessages + compilemessages — Task 6.4)**; hu/en smeju ostati prazni (fallback sr). TEA subject-locale test (8.6) asertuje protiv tih konkretnih msgid-ova.
- **And** sav user-facing email tekst prolazi kroz `{% translate %}`/`gettext` (project-context.md:135-136); NIKAD hardkodovan literal

## Tasks / Subtasks

> **Konvencija:** `[TEA-RED]` = Test Architect piše test PRE implementacije (mora FAIL). `[DEV-GREEN]` = Developer implementira da test prođe. **Dev NIKAD ne piše testove.** Migracije (makemigrations + MANUAL REVIEW + migrate) i `uv add` su DEV task-ovi (project-context.md:218-227). `django-anymail` JE VEĆ dep → NEMA `uv add` (SM-D2).

- [x] **Task 1 — NOVI `apps/forms/` app scaffolding (AC3)** `[DEV-GREEN]`
  - [x] 1.1 Kreiraj `apps/forms/__init__.py` + `apps/forms/apps.py` (`class FormsConfig(AppConfig)`, `default_auto_field`, `name="apps.forms"` — mirror `apps/search/apps.py`).
  - [x] 1.2 Dodaj `"apps.forms"` u `INSTALLED_APPS` (config/settings/base.py) — POSLE domain app-ova.
  - [x] 1.3 `uv run python manage.py check` exit 0. Verifikuj dep boundary: `apps/forms/` ne importuje products/brands/search/catalog/blog (SM-D3a).

- [x] **Task 2 — `Lead` model (AC1)** `[DEV-GREEN]`
  - [x] 2.1 Kreiraj `apps/forms/models.py`: `class Lead(TimestampedModel)` (import `TimestampedModel` iz `apps.core.models`) sa poljima iz AC1; `form_type` kao nested `TextChoices` (ASCII vrednosti, `gettext_lazy` labele pun-dijakritik).
  - [x] 2.2 `name = CharField(max_length=200)` (`blank=False`); `data = JSONField(default=dict, blank=True)` (NIKAD mutable `default={}`; shape ugovor SM-D13); `ip_address = GenericIPAddressField(null=True, blank=True)`; `locale = CharField(max_length=10, default="sr", blank=True)`. **NEMA `photo` polja** (attachment-i = 4-4 `LeadAttachment` — SM-D14).
  - [x] 2.3 `__str__`, `Meta.verbose_name`/`_plural` (pun dijakritik), `Meta.ordering=["-created_at"]`, `Meta.indexes` na `(form_type, created_at)`. NEMA FK; NEMA get_absolute_url; NEMA translatable polja. NEMA defensive validacije.
  - [x] 2.4 `uv run python manage.py check` exit 0.

- [x] **Task 3 — Schema migracija (AC2)** `[DEV-GREEN]`
  - [x] 3.1 `uv run python manage.py makemigrations forms` → `0001_initial.py` (+ `migrations/__init__.py`).
  - [x] 3.2 **MANUAL REVIEW** `0001_initial.py` (CreateModel Lead + index `(form_type, created_at)` + nasleđena created_at/updated_at; NEMA `_sr/_hu/_en` kolona; project-context.md:221).
  - [x] 3.3 `uv run python manage.py migrate --plan` → `migrate forms`. Verifikuj reverz: `migrate forms zero` čist. **NEMA data seed migracije** (SM-D4).

- [x] **Task 4 — Email backend + settings/env config (AC6)** `[DEV-GREEN]`
  - [x] 4.1 `config/settings/base.py`: dodaj `DEFAULT_FROM_EMAIL`, `SERVER_EMAIL`, `ANYMAIL` dict (`RESEND_API_KEY` iz env), per-segment recipient setting-e (`CONTACT_EMAIL_TO`/`SERVICE_EMAIL_TO`/`PARTS_EMAIL_TO` iz env sa dev default-om). NE dirati `EMAIL_URL`/consolemail default.
  - [x] 4.2 `config/settings/staging.py` + `config/settings/production.py`: `EMAIL_BACKEND = "anymail.backends.resend.EmailBackend"`. (NE dirati `development.py:15` console backend.)
  - [x] 4.3 `.env.example`: dodaj `ANYMAIL_RESEND_API_KEY=` + `DEFAULT_FROM_EMAIL=` (NON-FINAL placeholder marker, mirror 3-4 SM-D11); zadrži postojeće CONTACT/SERVICE/PARTS_EMAIL_TO.
  - [x] 4.4 `uv run python manage.py check` exit 0 (verifikuj bar development + jedan prod-like settings modul). **NEMA `uv add`** (anymail VEĆ dep — SM-D2).

- [x] **Task 5 — Email template-ovi (AC5)** `[DEV-GREEN]`
  - [x] 5.1 Kreiraj `templates/emails/base_email.html` (`{% load i18n %}` + `{% block content %}`).
  - [x] 5.2 Kreiraj `templates/emails/lead_received.html` (`{% extends "emails/base_email.html" %}`; lead polja; `{% translate %}` labele; pune dijakritike; NEMA ćirilice/šišane latinice).

- [x] **Task 6 — Email service `send_lead_email` (AC4, AC9)** `[DEV-GREEN]`
  - [x] 6.1 Kreiraj `apps/forms/notifications.py:send_lead_email(lead)` (sync): recipient po `lead.form_type` (SM-D7 mapiranje kroz `Lead.FormType` member-e; DB vrednosti lowercase); subject lokalizovan po `lead.locale` (`translation.override` + `gettext` runtime, pun-dijakritik format epics.md:790/803/831); telo iz `lead_received.html` (`render_to_string`); from=`DEFAULT_FROM_EMAIL`; send kroz Django mail API (`EmailMultiAlternatives`/`send_mail` — backend-agnostično).
  - [x] 6.2 **FAILURE CONTRACT (C1):** obavij SAM provider-send poziv u `try/except` (specifičan exception, NE bare `except:`); na fail `logger.exception(...)` (GlitchTip-capturable, project-context.md:125) i **vrati `bool`** (`True`=poslat, `False`=pao). Prazan/nedostajući recipient → tretiraj kao failed send (log + `False`). `send_lead_email` prima VEĆ sačuvanu instancu (save-before-send ugovor za 4-2+ view; `except` NE rollback-uje Lead). Funkcija vraća `True` na uspeh.
  - [x] 6.3 **NEMA `post_save` signal** (SM-D5 — view-called; NEMA `apps/forms/signals.py`, NEMA signal wiring u apps.py). NEMA defensive validacije za interne nemoguće slučajeve (ali eksterni provider-send fail SE obrađuje — vidi 6.2, to NIJE defensive validacija).
  - [x] 6.4 **i18n msgid-ovi + `just messages` (AC9):** dodaj nove email subject/telo msgid-ove (subject format-i iz epics.md:790/803/831 — pun-dijakritik sr; subject/telo labele u `lead_received.html`/`base_email.html` kroz `gettext`/`{% translate %}`), pokreni `just messages` (makemessages + compilemessages) da regeneriše/kompajlira `.po`/`.mo` za sr/hu/en. **hu/en prevodi smeju ostati prazni → fallback na sr (prihvatljivo, isto kao 3-4 AC10 politika).** Obezbedi da TEA subject-locale test (8.6) ima konkretne msgid-ove protiv kojih asertuje.

- [x] **Task 7 — Osnovni `LeadAdmin` (AC7)** `[DEV-GREEN]`
  - [x] 7.1 Kreiraj `apps/forms/admin.py`: `@admin.register(Lead)` `ModelAdmin` sa `list_display`/`list_filter`/`search_fields` (+ opciono `readonly_fields`/`date_hierarchy`); registracija na POSTOJEĆI `admin.site` (mirror `apps/brands/admin.py`). NE dashboard.
  - [x] 7.2 Smoke: superuser otvori `reverse("admin:forms_lead_changelist")` → 200 (NE hardkoduj `/admin/` ni `/sr/admin/` — admin pod `i18n_patterns`; 3-4 SM-D6).

- [x] **Task 8 — RED-phase testovi (AC1-AC9)** `[TEA-RED]`
  - [x] 8.1 `apps/forms/tests/__init__.py` + `conftest.py` (mirror apps/search/tests). Email testovi koriste `mailoutbox` fixture (locmem; project-context.md:271).
  - [x] 8.2 `test_lead_model.py` — polja postoje + tipovi; `form_type` choices (4 vrednosti, ASCII); `TimestampedModel` nasleđe (created_at/updated_at); `data` default=dict (mutable-safe); `name` `blank=False`; `locale` default `"sr"`; **NEMA `photo` polja na Lead-u (assert da atribut ne postoji — attachment-i su 4-4 `LeadAttachment`)**; `__str__`; NEMA FK; NEMA get_absolute_url; NEMA translatable polja.
  - [x] 8.3 `test_lead_migrations.py` — 0001 CreateModel; index `(form_type, created_at)` postoji; NEMA `_sr/_hu/_en` kolona; reverz čist (introspect ili `call_command('migrate')`).
  - [x] 8.4 `test_app_config.py` — `FormsConfig` `name=="apps.forms"`; app u INSTALLED_APPS; dep boundary (apps/forms ne importuje products/brands/catalog/blog — npr. AST/import grep ili modul-level assert).
  - [x] 8.5 `test_send_lead_email.py` (AC4/AC8) — `Lead.objects.create(...)` + `send_lead_email(lead)` → `len(mailoutbox)==1`; `to` ispravan po form_type (parametrizuj 4 form_type-a → CONTACT/SERVICE/PARTS recipient SM-D7); `from_email==DEFAULT_FROM_EMAIL`; subject sadrži „[Ćorić Agrar]" + pun-dijakritik; body sadrži lead podatke; sync (email u outbox odmah posle poziva). NIKAD pravi send.
  - [x] 8.5b `test_send_lead_email_provider_failure.py` (AC4 C1) — patch-uj mail backend / `send`/`EmailMultiAlternatives.send` da baci provider exception (npr. `monkeypatch`/`mock` raises `Exception`); kreiraj + sačuvaj Lead PRE poziva; pozovi `send_lead_email(lead)` → assert: (a) fail je obrađen po zaključanoj semantici — `send_lead_email` VRAĆA `False` (NE propušta exception) i logguje (`caplog`/`logger.exception` zapis prisutan); (b) **perzistirani Lead red i dalje postoji** (`Lead.objects.filter(pk=lead.pk).exists()` — NIJE rollback-ovan). Dodatni slučaj: prazan/nedostajući recipient (env recipient `""`) → `send_lead_email` vraća `False` + log + Lead ostaje. Happy-path (`True`) pokriven u 8.5.
  - [x] 8.6 `test_email_subject_locale.py` (AC9) — subject lokalizovan po `lead.locale` (sr default pun-dijakritik; hu/en kroz gettext, fallback sr ako prevod fali); nema ćirilice/šišane latinice na sr.
  - [x] 8.7 `test_no_signal_on_create.py` (SM-D5) — `Lead.objects.create(...)` BEZ poziva `send_lead_email` → `len(mailoutbox)==0` (potvrđuje da NEMA post_save signala koji auto-šalje; email je view-orchestrated).
  - [x] 8.8 `test_lead_admin.py` (AC7) — `Lead` registrovan na admin.site; `list_display`/`list_filter`/`search_fields` definisani; superuser GET `reverse("admin:forms_lead_changelist")` → 200 (NE hardkodovan put — 3-4 SM-D6).
  - [x] 8.9 `test_email_backend_config.py` (AC6) — test settings koristi locmem (NE console/anymail u testu); `DEFAULT_FROM_EMAIL` set; `ANYMAIL` dict prisutan u base; staging/production modul ima `EMAIL_BACKEND` anymail Resend — **introspektuj TAČAN modul (`import config.settings.staging`/`production` i čitaj `EMAIL_BACKEND` atribut), NE `django.conf.settings`** (koji u testu pokazuje na development/locmem; aktivni `EMAIL_CONFIG`+`vars().update` u base bi inače maskirao prod override).

- [x] **Task 9 — Dev manual gate (NE pytest) (AC8)** `[DEV-GREEN]`
  - [x] 9.1 `uv run python manage.py check` + `migrate --plan` čisti.
  - [x] 9.2 Dev shell smoke (epics.md:774): `Lead.objects.create(...)` + `send_lead_email(lead)` u dev (console backend) → email se ispiše u konzolu sa ispravnim subject/to/from. (Staging Resend test = OQ-4 posle real key — NE blokira story.)
  - [x] 9.3 Commit model + migracija + app scaffold + settings/env + notifications + admin + email template-ovi ZAJEDNO (atomic; project-context.md:223). `just lint` clean.

## Dev Notes

### SM Decisions (SM-D log)

**SM-D1 — PLACEMENT: NOVI `apps/forms/` app.** architecture.md:594-600 EKSPLICITNO mapira `apps/forms/`: `models.py # Lead (sa form_type discriminator)`, `notifications.py # send_lead_email helper (sync)`, `admin.py # LeadAdmin (read-only listing po form_type)`. epics.md:772 „kreiram `apps/forms/models.py` sa `Lead`". Scaffolding mirror-uje apps/search (Story 2.13 NOVI app): `apps/search/apps.py` `class SearchConfig(AppConfig): name="apps.search"` + INSTALLED_APPS reg → identičan obrazac za `FormsConfig`. forms je TOP-LEVEL samostalan app (architecture.md:725 „forms ← samostalan, koristi core utilities"; :729 dep graf), ide u INSTALLED_APPS POSLE domain app-ova. **Postavlja se u `apps/forms/` (NE `apps/leads/`) jer i architecture.md i epics.md AUTHORITATIVELY koriste ime `forms`** (task hint je dozvolio `apps/leads/` kao alt — ali epic/arch su jasni: `forms`).

**SM-D2 — ANYMAIL VEĆ DEP (NEMA `uv add`).** `pyproject.toml:8` ima `django-anymail>=15.0` (verifikovano live). architecture.md:191 „Email helper: django-anymail — abstraction nad providerima"; :1034 anymail je deo bootstrap `uv add` liste. project-context.md:36 navodi anymail kao production dep. → 4-1 NE dodaje dep; SAMO konfiguriše backend. Provider: Resend primarni (architecture.md:190 „Resend ima najlepši DX"), Brevo alt — v1 koristi Resend backend (`anymail.backends.resend.EmailBackend`, epics.md:773). NIJE Django SMTP backend (anymail je odabran u arhitekturi; dev console je samo dev-convenience, ne SMTP fallback strategija).

**SM-D3 — LEAD FIELDS + JEDAN model (NE ServiceRequest/PartRequest split).** Polja iz epics.md:772 (AUTHORITATIVE): `form_type` (choices [contact/model_inquiry/service_request/part_request]), `name` (`blank=False`), `email`, `phone`, `message`, `data` (JSONField za form-specific polja — shape ugovor SM-D13), `created_at` (POKRIVENO TimestampedModel), `ip_address`, `locale`. **JEDAN `Lead` model sa `form_type` discriminatorom** — iako architecture.md:595 nabraja i `ServiceRequest`/`PartRequest`, epics.md:772/802/830 KONZISTENTNO koristi JEDAN Lead + `data` JSON za form-specific polja („svi specifični podaci u Lead.data JSON" :830). Zaseban ServiceRequest/PartRequest = premature abstrakcija (project-context.md:357 YAGNI) — JSON `data` pokriva 4 različita shape-a bez 3 tabele. Epic 8.3 segmentuje po `form_type` (jedan model, filter+count). **`photo` polje je IZOSTAVLJENO u 4-1** (epics.md:772 ga pominje kao single FileField, ALI epics.md:814 traži multi-upload do 3 slike — single FileField fizički ne može držati 3 fajla; vidi SM-D14): attachment-i pripadaju 4-4 `LeadAttachment` child modelu, ne 4-1 Lead-u. `data default=dict` (NIKAD mutable `{}`). NEMA translatable polja — lead je RAW user-submitted podatak, NE site content (modeltranslation je za content; project-context.md:154). `__str__` informativan; NEMA get_absolute_url (lead nije content sa javnom stranom — isti izuzetak kao 3-4 SiteSettings, project-context.md:158 važi za content modele).

**SM-D3a — NEMA Product FK (context kroz `data` JSON).** 4-3 (model inquiry) auto-popunjava model — ali ne kroz FK na `products.Product`, već kroz `Lead.data = {"product_slug": "agri-tracking-tb804"}` (epics.md:802). RAZLOG (NON-NEGOTIABLE): architecture.md:739 „`forms` NIKAD ne sme importovati `catalog`/`blog` direktno; context pass-uje se kroz form fields"; dep boundary (architecture.md:725 forms samostalan; project-context.md:665 „forms ne sme importovati catalog/blog"). FK `Lead.product → products.Product` bi uveo cross-app model zavisnost forms→products što KRŠI invariantu. `product_slug` string u JSON je dovoljan (4-3 view parsira `request.path`, stavlja slug u `data`; admin/email prikazuje slug; ako treba link, gradi se kroz `reverse` u prezentaciji, NE FK). Vidi OQ-3. (Napomena: architecture.md:723 `products ← ... forms` znači products je *zavistan od* / referenciran — ALI dep pravilo :739 + :725 jasno zabranjuju forms→catalog/blog import; products-slug-u-JSON je usklađen sa „context kroz form fields".)

**SM-D4 — MIGRACIJA: SAMO schema (0001), NEMA data seed.** Za razliku od 3-4 SiteSettings (singleton seed-ovan data migracijom jer mora postojati 1 red da sajt renderuje), `Lead` startuje PRAZAN — lead-ovi se kreiraju runtime kroz forme (4-2+). → SAMO `0001_initial` CreateModel, BEZ `0002_seed`. Index `models.Index(fields=["form_type", "created_at"])` jer Epic 8.3 (epics.md:1092) radi segmentovan count po `form_type` za current month — composite index ubrzava `filter(created_at__gte=...).values("form_type").annotate(count)`. Manual review (project-context.md:221) + reverzibilnost (CreateModel auto-reverzibilan; nema RunPython pa nema potrebe za reverse_code).

**SM-D5 — EMAIL MEHANIZAM: reusable SYNC service `send_lead_email(lead)`, VIEW-CALLED (NE post_save signal).** Service u `apps/forms/notifications.py` (architecture.md:600 „notifications.py # send_lead_email helper (sync)"; :783 „SMTP single point — django-anymail apstrakcija"). SYNC — project-context.md:84/127 (NO Celery/Redis v1; email send je sync, „idu u signals ILI direktno u view"). **TRIGGER ODLUKA = VIEW-CALLED, ne signal:** architecture.md:829 data-flow EKSPLICITNO „If valid: Save Lead → notifications.send_lead_email() → django-anymail → Resend" — view orkestrira save+send sekvencijalno. **SAVE-BEFORE-SEND RATIONALE (re-grounded — C2):** redosled „prvo save, pa send" sledi iz architecture.md:829 (AUTHORITATIVE data-flow za implementaciju) + FR-5/PRD:775 reliability („forme moraju da rade od prvog dana" → provider fail ne sme izgubiti lead). **NAPOMENA (ispravka ranije mis-citacije):** PRD §6.1:692 („forme čuvaju polja samo dok email ne bude uspešno poslat administratoru — daljinska perzistencija (ticket sistem) nije u v1") NE znači „lead ne sme biti izgubljen" niti „ne čuvaj u DB" — to je GDPR data-minimization framing koji isključuje IZGRADNJU remote/3rd-party ticket sistema u v1, NE lokalno DB skladištenje. Lokalna DB perzistencija lead-a JESTE u v1 (vidi C2 / SM-D11). **Zašto NE post_save signal:** signal bi okinuo email na SVAKI `Lead.create` — uključujući TEA testove (koji kreiraju Lead-ove za druge assertione), admin ručni unos, i buduće seed/import (Epic 9 9-7) → spam/neželjeni send-ovi + sprega test setup-a sa email-om. View-called drži email eksplicitnim i kontrolisanim. → 4-1 NEMA `apps/forms/signals.py`, NEMA signal registracije u `FormsConfig.ready()`. 4-2…4-5 view-ovi POZIVAJU `send_lead_email(lead)` posle `lead.save()` (architecture.md:829). (Task hint je predlagao „prefer signal" — ali AUTHORITATIVE architecture data-flow + PRD persistence semantika + test-pollution rizik → view-called pobeđuje; dokumentovano decisively.)

**SM-D6 — BACKEND per-env: dev console (VEĆ set), staging/prod anymail Resend.** `config/settings/development.py:15` VEĆ ima `EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"` (verifikovano live — dev email u konzolu, NE pravi send) → 4-1 NE dira dev. `staging.py` + `production.py` dobijaju `EMAIL_BACKEND = "anymail.backends.resend.EmailBackend"` (epics.md:773). base.py `EMAIL_URL`/consolemail default (`:97`) OSTAJE kao base fallback (env-driven; staging/prod override-uju eksplicitnim anymail backend-om). `ANYMAIL = {"RESEND_API_KEY": env("ANYMAIL_RESEND_API_KEY", default="")}` u base.py. TEST: pytest-django automatski koristi `locmem` backend (ili eksplicitan override u conftest) — `mailoutbox` fixture hvata email-ove BEZ network-a (project-context.md:267-271). Brevo alt backend NIJE konfigurisan u v1 (Resend primarni; swap je trivijalan kasnije zahvaljujući anymail apstrakciji).

**SM-D7 — RECIPIENTS: per-segment env baseline.** epics.md:773 „`LEAD_EMAIL_RECIPIENT` (admin podešavanje, env baseline)"; epics.md:818 „`SERVICE_EMAIL_RECIPIENT`"; epics.md:790 „`LEAD_EMAIL_RECIPIENT`". PRD §7.1 + FR-22/FR-23 „admin konfiguriše" recipient. `.env.example:61-65` VEĆ ima `CONTACT_EMAIL_TO`/`SERVICE_EMAIL_TO`/`PARTS_EMAIL_TO` placeholdere (Epic 4 marker). **ODLUKA:** `send_lead_email` bira recipient po `lead.form_type`: `SERVICE_REQUEST` → `SERVICE_EMAIL_TO`, `PART_REQUEST` → `PARTS_EMAIL_TO`, `KONTAKT` + `MODEL_INQUIRY` → `CONTACT_EMAIL_TO` (model_inquiry deli kontakt/prodaja recipient — epics.md ne traži zaseban; OQ-2 ako biznis razdvaja). Setting-i se čitaju iz env u base.py (env baseline; admin-editable recipient kroz SiteSettings = potencijalno Epic 8 8.9, OQ-1). Real adrese = OQ-4 biznis input; dev/test koristi bezbedan default.

**SM-D8 — ADMIN: osnovni read-mostly `LeadAdmin` (NE dashboard).** Registracija na POSTOJEĆI `admin.site` (mirror `apps/brands/admin.py` `admin.site.register`; admin pod `i18n_patterns` → stvarni URL `/sr/admin/forms/lead/`, 3-4 SM-D6 — testovi koriste `reverse("admin:forms_lead_*")`, NIKAD hardkodovan put). `list_display`/`list_filter`/`search_fields` (project-context.md:200) — `list_filter` na `form_type`+`created_at` omogućava ručni segmentovan pregled. **PUNI Admin Dashboard sa segmentovanim lead-count-om = Epic 8 Story 8.3** (`apps/admin_ext/views.py:DashboardView` + `apps/admin_ext/stats.py:get_lead_stats()` koja vraća {contact, model_inquiry, service_request, part_request, total} za current month; epics.md:1084-1097) — VAN scope-a 4-1. `/admin-coric/` slug + django-axes = Epic 8.1. Lead je read-mostly u adminu (primljen podatak, ne admin-kreiran content) → opciono `readonly_fields` + `date_hierarchy`.

**SM-D9 — EMAIL TEMPLATES: `base_email.html` + `lead_received.html` (Django i18n).** epics.md:775 „Email template `templates/emails/lead_received.html` koristi `{% extends "emails/base_email.html" %}` i Django i18n". architecture.md:797 mapira `templates/emails/`. `templates/emails/` dir NE postoji danas (verifikovano live) — 4-1 ga uvodi. Subject lokalizovan po `lead.locale` (epics.md:776) kroz `translation.override(lead.locale)` + `gettext` runtime (project-context.md:136 „email subjects: gettext runtime jer subject zavisi od lokala primaoca"). Email HTML SME imati inline stil (email klijenti — Outlook/Gmail — ne podržavaju `<link>`/eksterni CSS pouzdano; inline je email-industrijska norma) → dokumentovan izuzetak od project-context.md:317 (koji se odnosi na WEB template-e); držati minimalno, čitljivo. Pune dijakritike, NEMA ćirilice/šišane latinice.

**SM-D10 — base klasa: `TimestampedModel` (REUSE; NE PublishableModel/SluggedModel).** Lead nasleđuje `TimestampedModel` (`created_at`/`updated_at`) iz `apps/core/models.py` (verifikovano live — postoje SAMO TimestampedModel + SluggedModel `abstract=True`; PublishableModel se pominje u project-context.md:152 ali NE postoji). `created_at` iz epics.md:772 je POKRIVEN nasleđem. `SluggedModel` se NE koristi (lead nema slug/URL). `PublishableModel` se NE koristi (lead nema publish state).

**SM-D11 — PERZISTENCIJA MODEL: Lead je DURABILNO sačuvan u lokalnoj DB (reconciliacija sa PRD §6.1:692) — C2.** **v1 ODLUKA (locked):** `Lead` se perzistira durabilno u lokalnoj PostgreSQL DB. **architecture.md:829 je AUTHORITATIVE za implementaciju** (data-flow „Save Lead → send_lead_email()"; DB je skladište) + Epic 8.3 admin lead-lista (epics.md:1084-1097) zahteva da lead-ovi POSTOJE u DB da bi se segmentovano brojali → DB perzistencija je nužna. **Razrešenje prividne kontradikcije sa PRD §6.1:692:** PRD:692 („Forme čuvaju polja samo dok email ne bude uspešno poslat administratoru — daljinska perzistencija (npr. ticket sistem) nije u v1") je GDPR data-minimization iskaz koji znači „NE gradimo remote/3rd-party ticket sistem u v1" (email JE primarni delivery), a NE „zabranjeno je lokalno DB skladištenje" niti (ispravka ranije SM-D5 mis-citacije) „lead ne sme biti izgubljen". Lokalna DB perzistencija + admin pregled (Epic 8.3) JESU u v1. Save-before-send rationale (AC4) se oslanja na architecture.md:829 + FR-5/PRD:775 reliability, NE na PRD:692.

**SM-D12 — GDPR/PII RETENCIJA = Epic 7 (van scope-a 4-1) — C2.** `Lead` čuva PII: `name`, `email`, `phone`, `ip_address` (GenericIPAddressField); attachment-i (4-4 `LeadAttachment` slike) su takođe PII. **Data-retention politika, pravo na zaborav (right-to-erasure), anonimizacija i retention TTL su Epic 7 (GDPR & Privacy) — NISU u 4-1** (mirror načina na koji je admin-editable recipient deferred u Epic 8.9, OQ-1). 4-1 SAMO uvodi model + skladište; NE implementira erasure/anonimizaciju/retention job. **`ip_address` je posebno PII koji se u v1 čuva neograničeno** (do Epic 7) — view u 4-2+ ga puni iz `request`; svaka politika brisanja/retention TTL-a za `ip_address` (i ostatak PII-a) je Epic 7. (Vidi OUT OF SCOPE cross-ref.)

**SM-D13 — `Lead.data` JSONField SHAPE UGOVOR po form_type (IMPROVEMENT).** `data` JSON nosi form-specific polja; da bi 4-2…4-5 + email template mogli pouzdano da računaju na strukturu, key-schema po `form_type` je:
- `contact` → `{}` (koristi SAMO core polja: `name`/`email`/`phone`/`message`)
- `model_inquiry` → `{"product_slug": "<slug>", "product_name": "<display>"}` — **`data["product_slug"]` je LOCKED ugovor koji 4-3 zavisi (epics.md:802); `product_name` je display string za email subject** (epics.md:803 „Upit za model: Agri Tracking TB804")
- `service_request` → form-specifični ključevi (npr. `{"machine_type": "...", "brand_model": "...", "issue": "..."}`) — finalizuje 4-4
- `part_request` → form-specifični ključevi (npr. `{"tractor_model": "...", "part_name": "...", "payment": "...", "delivery": "..."}`) — finalizuje 4-5

Email template (`lead_received.html`) rendera `data` GENERIČKI (loop kroz `lead.data.items()`) tako da nove non-core ključeve ne treba menjati template po story-ji. Tačni non-core ključevi za service/part su finalizovani u svojoj consumer story-ji; SAMO `model_inquiry.data["product_slug"]` je zaključan u 4-1 kao cross-story ugovor. **NEMA FK** (dep boundary forms→products — SM-D3a); product context ostaje slug-u-JSON.

**SM-D14 — PHOTO/ATTACHMENT IZOSTAVLJEN iz 4-1; `LeadAttachment` child model je 4-4 (IMPROVEMENT — resolve single-FileField vs multi-upload konflikt).** epics.md:772 pominje `photo` kao single `FileField`, ALI epics.md:814 (Story 4-4) zahteva „Foto (opciono, multi-upload **do 3 slike**)" + epics.md:818 „Email sa **attach-ovanim slikama** (plural)". **Jedan `FileField` fizički ne može držati 3 fajla** → da je 4-1 uveo single `photo` FileField, 4-4 bi morala mid-sprint migraciju (drop single field + add child model). **ODLUKA (locked):** 4-1 NE uvodi `photo` polje uopšte. Service-request attachment-i se rešavaju u **Story 4-4 kroz dedikovan `LeadAttachment` child model**: `class LeadAttachment(TimestampedModel)` sa `lead = ForeignKey(Lead, on_delete=models.CASCADE, related_name="attachments")` + `file = FileField(upload_to="leads/attachments/")`, MIME/veličina validacija (Image MIME iz 2.3; max 5MB/fajl; max 3 instance po Lead-u — form-layer constraint), i proširenje `send_lead_email` da `email.attach()` svaki vezani fajl. Pošto Lead model još NE postoji u repo-u, NEMA migracionog troška sada (čist Lead u 4-1; child model + svoja migracija dolaze u 4-4). 4-1 `send_lead_email` šalje SAMO telo+subject (NEMA attach hook). **(ALTERNATIVA razmotrena i odbačena:** `data` JSON sa listom file path-ova — odbačeno jer FileField/upload lifecycle, MIME validacija i admin inline pregled traže pravi model, ne raw path-ove u JSON-u.)

**SM-D15 — SAVE+SEND VIEW UGOVOR za 4-2…4-5 (IMPROVEMENT guardrail).** Pošto je email VIEW-CALLED (NE signal — SM-D5), postoji „zaboravljen send" footgun. **ZAKLJUČAN UGOVOR (svaki lead-form view u 4-2…4-5 MORA):** posle `lead.save()` (ili `Lead.objects.create(...)`) POZVATI `send_lead_email(lead)` i obraditi njegovu `bool` povratnu vrednost (C1 failure contract):
- `True` → success partial korisniku
- `False` → korisniku se prikaže poruka „Vaš upit je sačuvan, ali email obaveštenje nije poslato — pozovite nas na <telefon>" (degradiran success; lead OSTAJE sačuvan jer je save prethodio send-u), a admin dobija GlitchTip alert (logger.exception iz `send_lead_email`)
- Lead se NIKAD ne gubi na email-fail-u (save-before-send — AC4)

**4-2 (prva forma) MORA imati test koji asertuje da view ZOVE `send_lead_email`** (npr. `mock`/`monkeypatch` spy na `notifications.send_lead_email` + assert called-once sa sačuvanim lead-om) — taj test zaključava guardrail za sve naredne forme. (4-1 samo dokumentuje ugovor; ne piše view ni 4-2 test.)

### Story 4-4 precondition (attachment model)

- **Story 4-4 MORA uvesti `LeadAttachment` child model** (FK→Lead `on_delete=CASCADE`, `related_name="attachments"`, `file = FileField`) + svoju migraciju + MIME/veličina validaciju (do 3 slike, max 5MB/fajl) + proširenje `send_lead_email` za `email.attach()`. 4-1 NAMERNO ne nosi `photo` polje (SM-D14) → 4-4 počinje od čistog Lead-a, bez naslednog single-FileField-a koji bi trebalo ukloniti.

### Project Structure Notes

- `apps/forms/` je NOVI app (mirror apps/search 2-13): `__init__.py`, `apps.py` (FormsConfig), `models.py`, `notifications.py`, `admin.py`, `migrations/`, `tests/`. NEMA `views.py`/`urls.py`/`forms.py`/`signals.py`/`translation.py` u 4-1 (views/urls/forms = 4-2…4-6; NEMA signal jer view-called SM-D5; NEMA translation jer nema translatable polja).
- `templates/emails/` je NOVI template dir (uz postojeće brands/products/pages/search/partials). `apps/forms/` NEMA app-level `templates/forms/` u 4-1 (form partials = 4-2+).
- Dep boundary: `apps/forms/` importuje SAMO `apps.core` (TimestampedModel) + Django/anymail. NIKAD products/brands/search/catalog/blog (architecture.md:739; project-context.md:665). Product context (4-3) ide kroz `Lead.data` JSON slug, NE FK (SM-D3a).
- Email backend: dev console (`development.py:15` NETAKNUT), staging/prod anymail Resend, test locmem (pytest-django + `mailoutbox`). base.py `EMAIL_URL`/consolemail default ostaje fallback.
- **base.py `EMAIL_BACKEND` override mehanika (verifikovano live, `base.py:97-101`):** base.py koristi `EMAIL_CONFIG = env.email_url("EMAIL_URL", default="consolemail://")` + `vars().update(EMAIL_CONFIG)` (+ `del EMAIL_CONFIG`) — taj `vars().update` POSTAVLJA `EMAIL_BACKEND` (consolemail po defaultu). `staging.py`/`production.py` EKSPLICITNO postavljaju `EMAIL_BACKEND = "anymail.backends.resend.EmailBackend"` POSLE `from .base import *`, što ISPRAVNO override-uje base vrednost (kasniji modul-level assignment pobeđuje). **NE uklanjati `EMAIL_URL`/`vars().update` iz base.py** (dev/test path zavisi). AC6 backend test MORA introspektovati TAČAN settings modul (importuj `config.settings.staging`/`production` i čitaj `EMAIL_BACKEND`, NE pretpostavljaj iz `django.conf.settings` koji u testu pokazuje na development/locmem).

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-4.1] (`:765-776`) — Lead polja (form_type/name/email/phone/message/data JSON/photo nullable/created_at/ip_address/locale), `notifications.py:send_lead_email` kroz anymail, EMAIL_BACKEND anymail.backends.resend, env-vars (ANYMAIL_RESEND_API_KEY/DEFAULT_FROM_EMAIL/LEAD_EMAIL_RECIPIENT), shell test, email template + i18n subject po locale
- [Source: _bmad-output/planning-artifacts/epics.md#Story-4.2..4.5] (`:778-831`) — downstream konzumenti: form_type vrednosti (contact/model_inquiry/service_request/part_request), `Lead.data={"product_slug"}` (4.3), photo upload (4.4 → `LeadAttachment`, SM-D14), data JSON (4.5), subject formati, SERVICE_EMAIL_RECIPIENT
- **ENV-VAR NAMING reconciliation (epics.md vs story — IMPROVEMENT):** epics.md:773/790 koristi generički placeholder `LEAD_EMAIL_RECIPIENT` (i `:818` `SERVICE_EMAIL_RECIPIENT`); v1 implementacija koristi TRI segmentovana env-vara koji VEĆ postoje u `.env.example:63-65` — `CONTACT_EMAIL_TO`/`SERVICE_EMAIL_TO`/`PARTS_EMAIL_TO`. **Mapiranje (da 4-2 implementeri ne budu zbunjeni):** epics.md `LEAD_EMAIL_RECIPIENT` je generički placeholder, NE doslovno ime env-vara; `CONTACT_EMAIL_TO` je kanonski recipient za KONTAKT + MODEL_INQUIRY, `SERVICE_EMAIL_TO` za SERVICE_REQUEST, `PARTS_EMAIL_TO` za PART_REQUEST (SM-D7). NEMA `LEAD_EMAIL_RECIPIENT` env-vara u v1 — segmentovana tri su izvor istine.
- [Source: _bmad-output/planning-artifacts/epics.md#Story-8.3] (`:1084-1097`) — Admin Dashboard segmentovan lead-count = Epic 8 boundary (SM-D8)
- [Source: _bmad-output/planning-artifacts/architecture.md:594-600] — `apps/forms/` struktura (models Lead, notifications send_lead_email sync, admin LeadAdmin); :191/190 anymail + Resend/Brevo; :725/739 forms dep boundary (samostalan, NE catalog/blog); :783 SMTP single point; :829 data-flow (Save Lead → send_lead_email — view-called; AUTHORITATIVE save-before-send + durabilna DB perzistencija, SM-D11/C2)
- [Source: _bmad-output/planning-artifacts/prds/prd-CORIC_AGRAR-2026-05-27/prd.md §6.1:692] — GDPR data-minimization (remote/ticket-sistem perzistencija van v1; NE zabrana lokalnog DB skladištenja — reconciliacija SM-D11/C2); §10.1:775 (FR-5 reliability — „forme moraju da rade od prvog dana" → save-before-send rationale, C1)
- [Source: _bmad-output/planning-artifacts/epics.md:791,802] — form_type DB vrednosti LOWERCASE (`'contact'`/`'model_inquiry'`/`'service_request'`/`'part_request'`) — downstream query ugovor (C3); Epic 7 (GDPR & Privacy) — PII retencija/erasure deferral (SM-D12)
- [Source: _bmad-output/project-context.md:121,125] — specifični exceptions (NE bare except); sve unhandled exceptions → GlitchTip capture (`logger.exception` failure-log, C1)
- [Source: _bmad-output/project-context.md:84,127] — NO Celery, email send SYNC; :135-136 gettext (email subject runtime); :148-158 model base/FK/no get_absolute_url-na-config; :200-201 admin list_display/list_filter/search_fields; :218-227 migrations discipline; :267-271 mock samo external + mailoutbox; :357-358 YAGNI/no defensive; :595 NEVER import User direct (settings.AUTH_USER_MODEL — N/A ovde, Lead nema user FK); :665 forms ne importuje catalog/blog
- [Source: apps/core/models.py] — `TimestampedModel` (REUSE; NEMA PublishableModel)
- [Source: apps/search/apps.py] — NOVI-app AppConfig PATTERN (mirror za FormsConfig)
- [Source: apps/brands/admin.py] — `admin.site.register` PATTERN
- [Source: config/settings/base.py:94-101] — `EMAIL_URL`/consolemail default; :28-51 INSTALLED_APPS (dodati apps.forms); :115-130 LANGUAGES/i18n
- [Source: config/settings/development.py:15] — console backend (NETAKNUT — dev); staging.py/production.py — anymail override mesto
- [Source: .env.example:45-65] — EMAIL_URL + CONTACT/SERVICE/PARTS_EMAIL_TO placeholderi (dodati ANYMAIL_RESEND_API_KEY + DEFAULT_FROM_EMAIL)
- [Source: pyproject.toml:8] — `django-anymail>=15.0` VEĆ dep (NEMA uv add — SM-D2)
- [Source: templates/pages/partials/_contact_form.html:2,16] — 3-3 disabled skelet + „TODO Story 4.2" marker (4-2 ga žica, NE 4-1)

### Open Questions (OQ)

- **OQ-1 (recipient izvor — env vs SiteSettings):** v1 čita recipiente iz env baseline (SM-D7; epics.md:773 „env baseline"). Da li biznis želi admin-editable recipient (Marijana menja adresu kroz admin bez deploy-a)? Ako da → SiteSettings polje (`lead_email_recipient`/`service_email_recipient`) u Epic 8 8.9, i `send_lead_email` čita iz SiteSettings sa env fallback-om. Default v1: env. NE blokira 4-1.
- **OQ-2 (model_inquiry zaseban recipient):** 4-1 šalje `MODEL_INQUIRY` na `CONTACT_EMAIL_TO` (deli sa opštim kontaktom — epics.md ne traži zaseban). Ako prodaja želi razdvojen inbox za model-upite → dodati `MODEL_INQUIRY_EMAIL_TO` env (trivijalno proširenje SM-D7 mapiranja). Default v1: kontakt/prodaja recipient.
- **OQ-3 (Product context: JSON slug vs FK) — RAZREŠENO (locked):** `Lead.data={"product_slug": ...}` (epics.md:802), NEMA FK na products.Product. RAZLOG: dep boundary forms→products zabranjen (architecture.md:739; project-context.md:665). Slug u JSON je dovoljan za 4-3 (auto-popuna iz request.path) + admin/email prikaz. Ako future scale traži join/integritet → reevaluacija (NE v1). Vidi SM-D3a.
- **OQ-4 (real Resend API key + verifikovan sender domen + recipient adrese — biznis/ops):** `ANYMAIL_RESEND_API_KEY`, `DEFAULT_FROM_EMAIL` (verifikovan domen na Resend), i `CONTACT/SERVICE/PARTS_EMAIL_TO` su biznis/ops input. 4-1 daje env placeholdere + NON-FINAL marker (mirror 3-4 SM-D11). Dev/test NE šalje pravi email (console/locmem). Staging Resend test (epics.md:774) izvodi se posle real key — NE blokira 4-1 implementaciju ni testove.

### Testing notes (šta TEA pokriva — RED phase)

- **Model (AC1):** sva polja + tipovi; `form_type` 4 choices (ASCII vrednosti + pun-dijakritik labele); `TimestampedModel` nasleđe (created_at/updated_at); `data` default=dict (mutable-safe — dve instance ne dele isti dict); `name` `blank=False`; `ip_address` nullable; `locale` default `"sr"` (`blank=True`); **NEMA `photo` polja (attachment-i = 4-4 `LeadAttachment`)**; `__str__`; NEMA FK; NEMA get_absolute_url; NEMA translatable polja.
- **Migracija (AC2):** 0001 CreateModel Lead; composite index `(form_type, created_at)` postoji; NEMA `_sr/_hu/_en` kolona; reverz čist; NEMA data seed migracije.
- **App scaffold (AC3):** `FormsConfig.name=="apps.forms"`; u INSTALLED_APPS; **dep boundary** — `apps/forms/` ne importuje products/brands/search/catalog/blog (import-graph/AST provera).
- **Email service (AC4/AC8):** `Lead.objects.create(...)` + `send_lead_email(lead)` → vraća `True`; `len(mailoutbox)==1`; `to` ispravan po form_type (parametrizuj 4 form_type-a — `"contact"`/`"model_inquiry"`→CONTACT, `"service_request"`→SERVICE, `"part_request"`→PARTS recipient; lowercase DB vrednosti); `from_email==DEFAULT_FROM_EMAIL`; subject sadrži „[Ćorić Agrar]" + pun-dijakritik; body sadrži lead podatke; SYNC (email odmah posle poziva). Koristi `mailoutbox` (locmem) — NIKAD pravi send.
- **Email service FAILURE (AC4/C1):** patch backend send da baci → `send_lead_email(lead)` vraća `False` (NE propušta exception) + log zapisan (`logger.exception`/`caplog`) + perzistirani Lead red i dalje postoji (NIJE rollback-ovan). Prazan/nedostajući recipient → isto (`False` + log + Lead ostaje). (Task 8.5b.)
- **Subject locale (AC9):** subject po `lead.locale` (sr pun-dijakritik default; hu/en gettext, fallback sr); nema ćirilice/šišane latinice na sr.
- **NO-signal (SM-D5):** `Lead.objects.create(...)` SAM (bez `send_lead_email`) → `len(mailoutbox)==0` (potvrđuje da NEMA auto-send post_save signala; email je view-orchestrated).
- **Admin (AC7):** registrovan na admin.site; `list_display`/`list_filter`/`search_fields` definisani; superuser GET `reverse("admin:forms_lead_changelist")` → 200 (NIKAD hardkodovan `/admin/` put — 3-4 SM-D6).
- **Email config (AC6):** test koristi locmem (NE console/anymail u testu); `DEFAULT_FROM_EMAIL` set; `ANYMAIL` dict u base; staging/production `EMAIL_BACKEND` je anymail Resend (introspect).
- **TEA email policy:** `mailoutbox` fixture (Django/pytest-django built-in; project-context.md:271) za SVE email assertione. Mock SAMO external (project-context.md:267) — ovde locmem zamenjuje pravi SMTP. NIKAD network send. `@pytest.mark.django_db` na svaki test koji dira DB (Lead.create). NEMA `unittest.TestCase` (pytest-django; project-context.md:233).
- **Test data — BEZ `factory_boy`:** `factory_boy` NIJE u `pyproject.toml` dev deps (verifikovano live; project-context.md:250 ga pominje kao „dodati kad zatreba" — nije dodat). Lead test podaci se prave inline kroz `Lead.objects.create(...)` u svakom testu/fixture-u — **NEMA `factory_boy`, NEMA `factories.py` stub-a** u 4-1. (Ako future story uvede factory_boy kroz `uv add --dev`, refaktorisanje je opciono — NE blokira 4-1.)

## Risk-Tier Self-Assessment

**TIER: HIGH.**

**Obrazloženje:** PRVA story Epic 4 koja uspostavlja lead-gen + email TEMELJ (PRD teza — „forme moraju da rade od prvog dana", PRD:775). Kombinuje više state-bearing + external-surface + PII rizik faktora:
1. **CreateModel schema migracija** — irreverzibilna DB šema promena; composite index `(form_type, created_at)` mora biti ispravan za Epic 8.3 count performanse; pogrešan `form_type` choice ugovor lomi sve nizvodne forme (4-2…4-5) + dashboard.
2. **NOVA external email surface (anymail/Resend)** — prvi put da projekat šalje email kroz third-party provider; pogrešna backend/env konfiguracija → tihi fail (email ne stiže administratoru = izgubljen biznis lead, kritično po FR-5/PRD:775 reliability). **Mitigacija je AC4 failure contract (C1):** lead se save-uje PRE send-a (architecture.md:829), provider fail se hvata + GlitchTip-loguje + vraća `False` → lead NIJE izgubljen, fail je observable. Sync send blokira request → mora biti pouzdano.
3. **PII (GDPR-relevantni lični podaci)** — Lead DURABILNO čuva ime/email/telefon/IP/poruku + foto u DB (SM-D11) i ti podaci ulaze u email telo. Pogrešno rukovanje (logovanje, leak u email) je privacy rizik. **Data-retention, right-to-erasure, anonimizacija i `ip_address` retention TTL = Epic 7 (van scope-a 4-1; SM-D12)** — 4-1 SAMO uvodi skladište, NE retention/erasure politiku; `ip_address` se čuva neograničeno do Epic 7.
4. **NOVI app + INSTALLED_APPS + dep boundary** — pogrešan import (forms→products FK) krši arhitektonsku invariantu; novi app reg pogrešnim redosledom može uvesti suptilne probleme.
5. **Email mehanizam odluka (view-called vs signal)** — pogrešan izbor (signal) bi spamovao na svaki Lead.create uključujući testove/seed; view-called je svesna odluka koja mora biti konzistentno primenjena u 4-2+.

NIJE MEDIUM: schema migracija + nova external integracija (email/Resend) + PII + novi app boundary zajedno prelaze prag. Mitigacija: model je mali (bez FK), NEMA data seed (prazan start), email service je tanak (Django mail API + anymail apstrakcija), testovi koriste locmem (zero network rizik), dev ostaje console (NE šalje pravi email dok ops ne obezbedi key — OQ-4).

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
