---
story-id: "4.1"
story-key: 4-1-lead-model-smtp-setup
artifact: interface-contract
created: 2026-06-01
author: TEA / Murat (autonomous RED phase)
purpose: Canonical contract za PRVU story Epic 4 — NOVI `apps/forms/` app sa `Lead`
         singleton-store modelom (form_type discriminator, DB vrednosti LOWERCASE,
         BEZ photo polja), `0001_initial` schema migracija (CreateModel + composite
         index (form_type, created_at), NEMA data seed), reusable SYNC email service
         `send_lead_email(lead)` (view-called, NE signal; save-before-send ugovor;
         try/except + logger.exception + return bool failure contract; recipient po
         form_type iz env), 2 email template-a (`templates/emails/base_email.html` +
         `lead_received.html`, Django i18n, pune dijakritike), email backend/env config
         (dev console NETAKNUT; staging/prod anymail Resend; ANYMAIL dict + DEFAULT_FROM_EMAIL
         + 3 recipient env-vara u base), i osnovni read-mostly `LeadAdmin`. 1 model,
         1 migracija, 0 view/URL/forme, 0 CSS, 0 JS, 0 signal, 0 translation.py.
         Dev MORA satisfy svaku klauzulu u GREEN.
---

# Interface Contract — Story 4.1 „Lead Model + SMTP/Email Setup"

Story 4.1 uvodi NOVI `apps/forms/` app (mirror apps/search 2-13 scaffolding) sa:

- `class Lead(TimestampedModel)` u `apps/forms/models.py` — jedinstveno DB skladište za sve 4 forme;
  `form_type` discriminator (nested `TextChoices`, **DB vrednosti LOWERCASE** za nizvodni query
  ugovor), plain polja (`name`/`email`/`phone`/`message`/`data` JSON/`ip_address`/`locale`),
  nasleđen `created_at`/`updated_at`. **NEMA `photo`/attachment polja** (= 4-4 `LeadAttachment`),
  NEMA FK, NEMA `get_absolute_url`, NEMA translatable polja.
- `0001_initial` CreateModel migracija + composite index `(form_type, created_at)` (NEMA data seed).
- `send_lead_email(lead)` u `apps/forms/notifications.py` — SYNC, view-called (NE post_save signal),
  save-before-send ugovor, recipient po `form_type`, lokalizovan subject po `lead.locale`, telo iz
  template-a, **try/except + `logger.exception` + return `bool`** failure contract.
- 2 email template-a (`templates/emails/base_email.html` + `lead_received.html`).
- Email backend/env config: dev console NETAKNUT; staging/prod `anymail.backends.resend.EmailBackend`;
  base.py `DEFAULT_FROM_EMAIL` + `ANYMAIL` dict + per-segment recipient env-vari.
- Read-mostly `LeadAdmin` registrovan na POSTOJEĆI `admin.site`.

Ovaj ugovor enumeriše file-system delta + model surface + migracija + `send_lead_email` potpis i
failure/bool/empty-recipient semantiku + recipient rezoluciju po form_type + email template putanje +
admin contract (reverse() pravilo) + settings/env touchpoint-e + `Lead.data` JSON shape po form_type,
koje TEA RED-phase testovi verifikuju. Dev GREEN realizuje sve klauzule; bilo koje odstupanje vraća
story u `paused`.

> **NAPOMENA O EMAIL TEST POLITICI (TEA-D1):** Email testovi koriste Django `mailoutbox` fixture
> (pytest-django auto-postavlja `locmem` backend kad je fixture zatražen — `django.core.mail.outbox`).
> NIKAD pravi network send. Mock SAMO eksterni provider-send put (`monkeypatch`/`mock.patch` na
> `EmailMultiAlternatives.send`/`send_mail`) za failure-contract testove (project-context.md:267-271).
> `@pytest.mark.django_db` na svaki test koji dira DB (`Lead.objects.create`). NEMA `factory_boy`
> (nije dep) — Lead test data inline kroz `Lead.objects.create(...)`.

> **NAPOMENA O DB BACKEND-u (TEA-D2):** Lead testovi koriste običan PostgreSQL (NEMA FTS) — NE traže
> `requires_postgres` marker (za razliku od 2-13 search testova). `just test` pokreće Docker
> PostgreSQL test bazu; `@pytest.mark.django_db` migrira `0001_initial` u test bazi automatski.

> **NAPOMENA O TEST PARSIRANJU (TEA-D3):** Projekat NEMA `beautifulsoup4` — admin/template assertion-i
> koriste `reverse()` + status code i `render_to_string` + substring/regex (mirror apps/search/tests
> i apps/pages/tests konvencija). NIKAD hardkodovan `/admin/` ni `/sr/admin/` put.

---

## 1. File-system delta

| Path | Status | Vlasništvo |
|---|---|---|
| `apps/forms/__init__.py` | NOVO (Dev) | Python package marker. |
| `apps/forms/apps.py` | NOVO (Dev) | `class FormsConfig(AppConfig)`, `default_auto_field="django.db.models.BigAutoField"`, `name="apps.forms"` (mirror `apps/search/apps.py` SearchConfig). |
| `apps/forms/models.py` | NOVO (Dev) | `class Lead(TimestampedModel)` (import `TimestampedModel` iz `apps.core.models`) — vidi §2. NEMA `photo` polja, NEMA FK, NEMA `get_absolute_url`, NEMA translatable polja. |
| `apps/forms/notifications.py` | NOVO (Dev) | `def send_lead_email(lead) -> bool` (SYNC) — vidi §4. View-called, NE signal. |
| `apps/forms/admin.py` | NOVO (Dev) | `@admin.register(Lead)` read-mostly `ModelAdmin` — vidi §6. Registracija na POSTOJEĆI `admin.site`. |
| `apps/forms/migrations/__init__.py` | NOVO (Dev) | Package marker (NOVI app — migrations dir ne postoji). |
| `apps/forms/migrations/0001_initial.py` | GENERISANO + MANUAL REVIEW (Dev) | `makemigrations forms` — CreateModel `Lead` + composite index `(form_type, created_at)` + nasleđena `created_at`/`updated_at`. NEMA `_sr/_hu/_en` kolona. NEMA data seed. CreateModel auto-reverzibilan. |
| `templates/emails/base_email.html` | NOVO (Dev) | Bazni email layout (`{% load i18n %}` + `{% block content %}`). Inline stil dozvoljen (email izuzetak SM-D9). |
| `templates/emails/lead_received.html` | NOVO (Dev) | `{% extends "emails/base_email.html" %}`; rendera lead polja (ime/email/telefon/poruka/`get_form_type_display`/`data` ključevi); `{% translate %}` labele; pune dijakritike, NEMA ćirilice/šišane latinice. |
| `config/settings/base.py` | EDIT (Dev) | `"apps.forms"` u `INSTALLED_APPS` (POSLE domain app-ova); `DEFAULT_FROM_EMAIL`, `SERVER_EMAIL`, `ANYMAIL={"RESEND_API_KEY": env("ANYMAIL_RESEND_API_KEY", default="")}`, per-segment recipient setting-i (`CONTACT_EMAIL_TO`/`SERVICE_EMAIL_TO`/`PARTS_EMAIL_TO` iz env). NE dirati `EMAIL_URL`/`vars().update` consolemail default. |
| `config/settings/staging.py` + `config/settings/production.py` | EDIT (Dev) | `EMAIL_BACKEND = "anymail.backends.resend.EmailBackend"` (override consolemail POSLE `from .base import *`). |
| `config/settings/development.py` | NETAKNUT | `:15` console backend OSTAJE — dev NE šalje pravi email. |
| `.env.example` | EDIT (Dev) | DODATI `ANYMAIL_RESEND_API_KEY=`, `DEFAULT_FROM_EMAIL=`; zadržati postojeće `CONTACT_EMAIL_TO`/`SERVICE_EMAIL_TO`/`PARTS_EMAIL_TO` (`:63-65`). NON-FINAL placeholder marker. |
| `apps/forms/tests/__init__.py` | NOVO (TEA) | Package marker. |
| `apps/forms/tests/conftest.py` | NOVO (TEA) | `superuser` + `lead_kwargs` fixture-i; recipient env-override fixture. |
| `apps/forms/tests/test_lead_model.py` | NOVO (TEA) | AC1 (Task 8.2) |
| `apps/forms/tests/test_lead_migrations.py` | NOVO (TEA) | AC2 (Task 8.3) |
| `apps/forms/tests/test_app_config.py` | NOVO (TEA) | AC3 (Task 8.4) |
| `apps/forms/tests/test_send_lead_email.py` | NOVO (TEA) | AC4/AC8 happy-path (Task 8.5) |
| `apps/forms/tests/test_send_lead_email_provider_failure.py` | NOVO (TEA) | AC4/C1 failure + empty recipient (Task 8.5b) |
| `apps/forms/tests/test_email_subject_locale.py` | NOVO (TEA) | AC9 (Task 8.6) |
| `apps/forms/tests/test_no_signal_on_create.py` | NOVO (TEA) | SM-D5 no-signal (Task 8.7) |
| `apps/forms/tests/test_lead_admin.py` | NOVO (TEA) | AC7 (Task 8.8) |
| `apps/forms/tests/test_email_backend_config.py` | NOVO (TEA) | AC6 (Task 8.9) |
| `apps/forms/tests/test_email_templates.py` | NOVO (TEA) | AC5 (template render — base + lead_received) |

**NETAKNUTO (regression guards):** `apps/core/models.py` `TimestampedModel` (REUSE — NE menja se);
`config/settings/development.py:15` console backend (dev NE šalje pravi email; SM-D6);
`config/settings/base.py` `EMAIL_URL`/`vars().update` consolemail default (dev/test path zavisi);
`templates/pages/partials/_contact_form.html` (3-3 disabled skelet — 4-2 ga žica); `pyproject.toml`
(NEMA novog dep — `django-anymail>=15.0` VEĆ `:8`); `config/urls.py` (NEMA novih URL-ova — forms
urls.py = 4-2); svi postojeći app-ovi (`brands/products/search/pages/media_pipeline/core`); sve CSS/JS.
**0 view/URL/forme/HTMX, 0 signal, 0 translation.py, 0 CSS, 0 JS.**

---

## 2. Model surface — `apps/forms/models.py` `Lead`

```python
class Lead(TimestampedModel):                       # REUSE apps.core.models.TimestampedModel
    class FormType(models.TextChoices):
        KONTAKT         = "contact",         _("Opšti kontakt")
        MODEL_INQUIRY   = "model_inquiry",   _("Upit za model")
        SERVICE_REQUEST = "service_request", _("Servisni zahtev")
        PART_REQUEST    = "part_request",    _("Upit za rezervni deo")

    form_type   = CharField(max_length=20, choices=FormType.choices)  # DB value LOWERCASE
    name        = CharField(max_length=200)                # blank=False (obavezno)
    email       = EmailField()
    phone       = CharField(max_length=50, blank=True)
    message     = TextField(blank=True)
    data        = JSONField(default=dict, blank=True)      # NIKAD mutable default={}
    ip_address  = GenericIPAddressField(null=True, blank=True)
    locale      = CharField(max_length=10, default="sr", blank=True)
    # nasleđeno: created_at, updated_at (TimestampedModel)

    def __str__(self): return f"{self.get_form_type_display()}: {self.name}"

    class Meta:
        verbose_name = "Lead"
        verbose_name_plural = "Lead-ovi"            # ili „Upiti" — puni dijakritik
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["form_type", "created_at"])]
```

**Polja (TAČNO 8 deklarisanih + 2 nasleđena):**

| Polje | Tip | Napomena |
|---|---|---|
| `form_type` | CharField(max_length=20, choices) | nested `TextChoices`; **DB vrednost LOWERCASE** (`max_length >= 15` za `"service_request"`) |
| `name` | CharField(200) | `blank=False` (obavezno za sve form_type-ove) |
| `email` | EmailField | |
| `phone` | CharField(blank=True) | opciono |
| `message` | TextField(blank=True) | opciono |
| `data` | JSONField(`default=dict`, blank=True) | form-specific shape po form_type (§7); NIKAD mutable `{}` |
| `ip_address` | GenericIPAddressField(null=True, blank=True) | view puni iz request (4-2+) |
| `locale` | CharField(max_length=10, default="sr", blank=True) | za lokalizovan email subject |
| `created_at` | DateTimeField(auto_now_add) | nasleđeno TimestampedModel |
| `updated_at` | DateTimeField(auto_now) | nasleđeno TimestampedModel |

**`FormType` DB vrednosti (LOWERCASE — STABILAN cross-story ugovor, NE menjati):**

| Member (uppercase, čitljivost) | DB vrednost (lowercase) | Label (gettext_lazy, puni dijakritik) |
|---|---|---|
| `FormType.KONTAKT` | `"contact"` | „Opšti kontakt" |
| `FormType.MODEL_INQUIRY` | `"model_inquiry"` | „Upit za model" |
| `FormType.SERVICE_REQUEST` | `"service_request"` | „Servisni zahtev" |
| `FormType.PART_REQUEST` | `"part_request"` | „Upit za rezervni deo" |

**NEMA:**
- `photo`/attachment polja (= 4-4 `LeadAttachment` child model; SM-D14) — `Lead` NEMA `photo` atribut.
- FK / relacija (product context kroz `data` JSON slug — SM-D3a).
- `get_absolute_url` (lead nije content sa javnom stranom — isti izuzetak kao 3-4 SiteSettings).
- translatable polja (lead je raw user-submitted, NE site content) → NEMA `apps/forms/translation.py`.
- defensive validacije (project-context.md:358).

---

## 3. Migracija — `apps/forms/migrations/0001_initial.py`

- `makemigrations forms` → `CreateModel("Lead", ...)` sa SVIM poljima (§2) + nasleđena
  `created_at`/`updated_at` + composite `models.Index(fields=["form_type", "created_at"])`.
- `apps/forms/migrations/__init__.py` package marker.
- **NEMA `_sr/_hu/_en` modeltranslation kolona** (Lead nema translatable polja).
- **NEMA data seed migracije** — Lead startuje PRAZAN (lead-ovi se kreiraju runtime kroz forme 4-2+);
  za razliku od 3-4 SiteSettings (seed-ovan), NEMA `0002_seed`.
- `form_type` kolona `max_length >= 15` (pokriva `"service_request"`).
- MANUAL REVIEW (project-context.md:221). CreateModel auto-reverzibilan (`migrate forms zero`).
- pytest-django primenjuje `0001_initial` u test bazi automatski → Lead red se može kreirati i
  round-trip-ovati (`Lead.objects.create(...)` + refetch iz DB).

---

## 4. Email service — `apps/forms/notifications.py` `send_lead_email`

```python
def send_lead_email(lead) -> bool:
    """SYNC; prima VEĆ sačuvanu Lead instancu (save-before-send). View-called (NE signal).
    Vraća True na uspeh, False na fail (provider exception ILI prazan recipient).
    NE re-raise; NE rollback Lead-a."""
```

**Potpis + semantika (LOCKED):**

- **SYNC** (`def`, NE `async`; NO Celery — project-context.md:84/127).
- **VIEW-CALLED, NE post_save signal** — NEMA `apps/forms/signals.py`, NEMA signal wiring u
  `FormsConfig.ready()`. `Lead.objects.create(...)` SAM NE šalje email (no-signal test, §9).
- **SAVE-BEFORE-SEND ugovor (za 4-2+):** prima VEĆ perzistiranu instancu (sa `lead.pk`). View u 4-2…4-5
  vlasnik je redosleda `lead.save()` → `send_lead_email(lead)`. `except` NE briše/rollback-uje red.
- **RECIPIENT rezolucija po `lead.form_type`** (poredi sa `Lead.FormType` member-ima, NE sirovim
  literalima):

  | `form_type` (DB vrednost) | Settings recipient |
  |---|---|
  | `FormType.SERVICE_REQUEST` (`"service_request"`) | `SERVICE_EMAIL_TO` |
  | `FormType.PART_REQUEST` (`"part_request"`) | `PARTS_EMAIL_TO` |
  | `FormType.KONTAKT` (`"contact"`) | `CONTACT_EMAIL_TO` |
  | `FormType.MODEL_INQUIRY` (`"model_inquiry"`) | `CONTACT_EMAIL_TO` (deli sa kontaktom; OQ-2) |

- **SUBJECT** lokalizovan po `lead.locale` (`django.utils.translation.override(lead.locale)` + `gettext`
  runtime; project-context.md:136). Format mapira epics.md:790/803/831 — sadrži `"[Ćorić Agrar]"` + puni
  dijakritik (npr. „[Ćorić Agrar] Novi kontakt: {name}").
- **TELO** iz `templates/emails/lead_received.html` (`render_to_string` sa lead context-om).
- **FROM** = `settings.DEFAULT_FROM_EMAIL`.
- **SEND** kroz Django mail API (`EmailMultiAlternatives` / `send_mail`) — backend-agnostično (console
  dev, anymail/Resend prod, locmem test). NE poziva Resend API direktno (anymail apstrakcija).
- **FAILURE CONTRACT (C1 — LOCKED):** SAM provider-send poziv obavijen u `try/except` (specifičan
  exception, NE bare `except:`); na fail → `logger.exception(...)` (GlitchTip-capturable;
  project-context.md:125) + **return `False`** (NE re-raise). Lead OSTAJE sačuvan.
- **PRAZAN/NEDOSTAJUĆI RECIPIENT:** rezolvovani recipient prazan (`""`/None — env nepopunjen) → tretira
  se kao failed send (`logger.exception`/`logger.error` + return `False`), NE baca neuhvaćeno, Lead ostaje.
- **Povratna vrednost:** `True` = send uspeo; `False` = provider fail ILI prazan recipient.

---

## 5. Email template-ovi — `templates/emails/`

| Template | Sadržaj |
|---|---|
| `templates/emails/base_email.html` | `{% load i18n %}` + minimalan HTML skelet + `{% block content %}`. Inline stil dozvoljen (email klijenti — izuzetak od project-context.md:317; SM-D9). |
| `templates/emails/lead_received.html` | `{% extends "emails/base_email.html" %}`; rendera lead polja (ime, email, telefon, poruka, `get_form_type_display`, relevantni `data` ključevi — GENERIČKI loop kroz `lead.data.items()`); sve labele kroz `{% translate %}`; pune dijakritike (č/ć/ž/š/đ); NEMA ćirilice, NEMA šišane latinice. `render_to_string` sa Lead context-om NE baca. |

---

## 6. Admin contract — `apps/forms/admin.py`

- `@admin.register(Lead)` na POSTOJEĆI `admin.site` (mirror `apps/brands/admin.py`) — pojavljuje se u
  admin app listi.
- `list_display = ("form_type", "name", "email", "phone", "created_at")` (project-context.md:200).
- `list_filter = ("form_type", "created_at")` (segmentacija; PUNI dashboard count = Epic 8.3).
- `search_fields = ("name", "email", "message")` (project-context.md:200).
- Read-mostly: opciono `readonly_fields` (created_at/updated_at/ip_address) + `date_hierarchy = "created_at"`.
- NIJE dashboard (Epic 8.3), NIJE custom slug/axes (Epic 8.1).

**⛔ reverse() PRAVILO (SM-D6/3-4 — LOCKED):** admin je mount-ovan UNUTAR `i18n_patterns` → stvarni URL
je locale-prefiksovan (`/sr/admin/forms/lead/...`). Test/smoke MORA koristiti
`reverse("admin:forms_lead_changelist")` i `reverse("admin:forms_lead_change", args=[obj.pk])`.
**NIKAD** hardkodovan `/admin/...` ni `/sr/admin/...` (bare put → 404). Superuser GET changelist → **200**.

---

## 7. `Lead.data` JSON shape ugovor po form_type (SM-D13)

`data` JSON nosi form-specific polja; key-schema po `form_type`:

| `form_type` | `data` shape | Locked? |
|---|---|---|
| `contact` | `{}` (koristi SAMO core polja name/email/phone/message) | — |
| `model_inquiry` | `{"product_slug": "<slug>", "product_name": "<display>"}` | **`product_slug` LOCKED (4-3 zavisi; epics.md:802); `product_name` display string za subject** |
| `service_request` | form-specifični ključevi (npr. `{"machine_type", "brand_model", "issue"}`) | finalizuje 4-4 |
| `part_request` | form-specifični ključevi (npr. `{"tractor_model", "part_name", "payment", "delivery"}`) | finalizuje 4-5 |

`lead_received.html` rendera `data` GENERIČKI (loop kroz `lead.data.items()`) → nove non-core ključeve
ne treba menjati template po story-ji. **NEMA FK** (dep boundary forms→products — SM-D3a); product
context ostaje slug-u-JSON.

---

## 8. Settings / env touchpoints

**`config/settings/base.py` (EDIT):**
- `INSTALLED_APPS` += `"apps.forms"` (POSLE domain app-ova — forms je samostalan top-level).
- `DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="no-reply@coricagrar.rs")`.
- `SERVER_EMAIL` (npr. = `DEFAULT_FROM_EMAIL`).
- `ANYMAIL = {"RESEND_API_KEY": env("ANYMAIL_RESEND_API_KEY", default="")}`.
- `CONTACT_EMAIL_TO` / `SERVICE_EMAIL_TO` / `PARTS_EMAIL_TO` iz `env(...)` sa bezbednim dev default-om.
- **NE dirati** `EMAIL_URL`/`vars().update(EMAIL_CONFIG)` consolemail default (`:97-101`).

**`config/settings/staging.py` + `config/settings/production.py` (EDIT):**
- `EMAIL_BACKEND = "anymail.backends.resend.EmailBackend"` (override consolemail POSLE `from .base import *`).

**`config/settings/development.py` (NETAKNUT):** `:15` console backend OSTAJE.

**`.env.example` (EDIT):** DODATI `ANYMAIL_RESEND_API_KEY=`, `DEFAULT_FROM_EMAIL=`; zadržati postojeće
`CONTACT_EMAIL_TO`/`SERVICE_EMAIL_TO`/`PARTS_EMAIL_TO` (`:63-65`). NON-FINAL placeholder marker (OQ-4).

**`pyproject.toml` (NETAKNUT):** `django-anymail>=15.0` VEĆ dep — NEMA `uv add` (SM-D2).

**TEST env:** pytest-django override-uje `EMAIL_BACKEND` na `locmem` kad je `mailoutbox` fixture
zatražen. AC6 backend test **introspektuje TAČAN settings modul** (`import config.settings.staging`/
`production` i čita `EMAIL_BACKEND` atribut), NE `django.conf.settings` (koji u testu pokazuje na
development/locmem; aktivni `EMAIL_CONFIG`+`vars().update` u base bi maskirao prod override).

---

## 9. AC → test traceability

| AC | Test fajl | Testovi (br.) |
|---|---|---|
| AC1 | `test_lead_model.py` | polja postoje+tipovi (form_type/name/email/phone/message/data/ip_address/locale); form_type 4 DB vrednosti LOWERCASE; name blank=False; data default=dict (mutable-safe); locale default „sr"; TimestampedModel nasleđe (created_at/updated_at); NEMA `photo` atributa; `__str__`; NEMA FK; NEMA get_absolute_url; verbose_name | 12 |
| AC2 | `test_lead_migrations.py` | 0001 CreateModel Lead aplicirana (round-trip create+refetch); composite index (form_type, created_at) postoji; NEMA `_sr/_hu/_en` kolona; NEMA data seed (count==0 na čistoj bazi) | 4 |
| AC3 | `test_app_config.py` | FormsConfig.name=="apps.forms"; default_auto_field BigAutoField; u INSTALLED_APPS; POSLE domain app-ova; dep boundary (ne importuje products/brands/search/catalog/blog) | 5 |
| AC4/AC8 | `test_send_lead_email.py` | save-before-send (count==1 pre poziva); vraća True; len(mailoutbox)==1; `to` po form_type (parametrizovano 4 form_type-a); from_email==DEFAULT_FROM_EMAIL; subject sadrži „[Ćorić Agrar]" + dijakritik; body sadrži lead podatke | 4 (1 parametrizovan × 4 = 7 logičkih) |
| AC4/C1 | `test_send_lead_email_provider_failure.py` | provider raise → vraća False (NE propušta); log zapisan (caplog); Lead red i dalje postoji (NIJE rollback); prazan recipient → False + log + Lead ostaje | 4 |
| AC9 | `test_email_subject_locale.py` | subject po lead.locale (sr/hu/en — parametrizovano); sr pun-dijakritik; nema ćirilice/šišane latinice na sr | 2 (1 parametrizovan × 3) |
| SM-D5 | `test_no_signal_on_create.py` | `Lead.objects.create(...)` BEZ poziva → len(mailoutbox)==0 (no post_save signal); FormsConfig.ready ne registruje signal | 2 |
| AC7 | `test_lead_admin.py` | registrovan na admin.site; list_display/list_filter/search_fields definisani; superuser GET reverse("admin:forms_lead_changelist") → 200 | 4 |
| AC6 | `test_email_backend_config.py` | DEFAULT_FROM_EMAIL set; ANYMAIL dict prisutan; recipient setting-i prisutni; test backend locmem (NE console/anymail); staging modul EMAIL_BACKEND anymail Resend (introspect); production modul isto | 6 |
| AC5 | `test_email_templates.py` | base_email.html render bez greške; lead_received.html render sa Lead context-om bez greške; render sadrži lead polja; nema ćirilice na sr | 3 |

**Test count (TEA RED phase):** model=12, migration=4, app_config=5, service_success=7 (parametrizovano),
service_failure=4, subject_locale=2, no_signal=2, admin=4, settings=6, templates=3.
**Ukupno ≈ 49 test funkcija/parametara (≈ 33 test-funkcije pre parametrizacije).**

---

## 10. RED-phase očekivanje

Pre Dev GREEN: `apps/forms/` NE postoji (app, model, migracija, notifications, admin); `templates/emails/`
NE postoji; `apps.forms` NIJE u INSTALLED_APPS; `DEFAULT_FROM_EMAIL`/`ANYMAIL`/recipient setting-i nisu u
base; staging/production NE postavljaju anymail backend. Svi NOVI testovi MORAJU pasti:
`ModuleNotFoundError: No module named 'apps.forms'` / `ImportError` (`apps.forms.models`/`notifications`/
`admin`) / `NoReverseMatch` (`admin:forms_lead_*`) / `AttributeError` (settings nema `ANYMAIL`/
`DEFAULT_FROM_EMAIL`) / `TemplateDoesNotExist` (`emails/lead_received.html`) / assertion.

**JEDINI dozvoljeni PASS u RED fazi** je regresija-lock koji NE zavisi od `apps.forms`:
- AC6 sub-assert „test backend je locmem" (pytest-django VEĆ postavlja locmem kad se `mailoutbox` koristi)
  — to JESTE već tačno → može proći samostalno; ali isti test fajl asertuje i `DEFAULT_FROM_EMAIL`/
  `ANYMAIL`/anymail staging backend koji NE postoje → test fajl kao celina pada.
- AC6 sub-assert „development.py console backend NETAKNUT" — console JE već set; ako se ekstrahuje kao
  zaseban test, prolazi (dokumentovan regresija-lock — to je namera: dev backend se NE dira).

Bilo koji DRUGI neočekivani PASS znači preslab test → istraži/ojačaj.
