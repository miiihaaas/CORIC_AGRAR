---
story-id: 4-4-servisni-zahtev-form-sa-foto-upload-om
epic: 4
title: "Servisni Zahtev Form sa Foto Upload-om"
status: ready-for-dev
module: forms
base-branch: master
created: 2026-06-04
author: SM (Scrum Master, 📋)
complexity: H
depends-on:
  - 4-1-lead-model-smtp-setup            # Lead model (FormType.SERVICE_REQUEST VEĆ postoji) + send_lead_email + LeadAttachment precondition (SM-D14) (DONE)
  - 4-2-opsta-kontakt-forma-fr-5         # kanonski HTMX form pattern (ratelimit block=False→429, OOB aria-live, partials, save-before-send) (DONE)
  - 4-3-model-inquiry-form-sa-auto-popunjenim-modelom   # drugi HTMX form precedent; notifications._build_subject grananje (DONE)
  - 2-3-image-pipeline-sa-sorl-thumbnail-responsive-srcset   # apps/media_pipeline/utils.py:validate_image_mime (MIME signature + Pillow verify + size) — REUSE (DONE)
  - 3-3-kontakt-strana-sa-formom-i-mapom # ContactView/pages-page precedent (dedikovana strana mount + _page_form.html container partial) (DONE)
forward-dep:
  - 4-6-htmx-form-patterns-aria-live-oob-rate-limiting   # standardizuje HTMX/ratelimit pattern (shared mixin/decorator) kroz forme 4.2-4.5
---

# Story 4.4 — Servisni Zahtev Form sa Foto Upload-om

## Opis / Description

As a **Stojan (operater sa terena)**, I want **da prijavim servisni kvar sa fotografijom sa mobilnog telefona**, so that **servis ima sve informacije (vrsta mehanizacije, brend/model, opis kvara, slike) pre nego što me pozove — bez ponavljanja**.

Ovo je **TREĆA forma story** Epic 4 i **PRVA forma sa file/foto upload-om**. Story 4.1 (Lead model + `send_lead_email`), 4.2 (kanonski HTMX form pattern), i 4.3 (drugi form precedent) su DONE i čine temelj. 4.4 **REUSE-uje 4.2/4.3 HTMX obrazac 1:1** (Django `forms.Form`, HTMX `hx-post` na zaseban `apps/forms` endpoint, ratelimit `block=False`→429, dve a11y regije, partials u `templates/forms/partials/`, save-before-send) i **REUSE-uje `apps/media_pipeline/utils.py:validate_image_mime`** (Story 2.3 — MIME signature + Pillow `verify()` + size limit) za obavezni file-upload double-check.

Forma se renderuje na **NOVOJ `/servis/` strani** (FR-22 „Stranica Servisna podrška sa formom") koju ova story kreira u `apps/pages` (mirror `ContactView` iz 3.3). Polja: **Ime\***, **Telefon\***, E-pošta, **Vrsta mehanizacije\*** (dropdown: Traktor / Priključna mehanizacija / Radna mašina / Ostalo), **Brend i model** (free text), **Opis kvara\***, **Foto** (opciono, multi-upload **do 3 slike**, JPG/PNG, **max 5 MB po fajlu**, MIME double-check). Submit ide preko HTMX (`hx-post` na `forms:service_request_submit` → `/sr/htmx/forme/servis/`). Lead se perzistira sa `form_type='service_request'`, form-specific polja u `Lead.data` JSON, a slike kroz **`LeadAttachment` child model** (FK→Lead, `on_delete=CASCADE`, `related_name="attachments"`) — JEDAN `FileField` fizički ne može držati 3 fajla, pa 4.1 SM-D14 namerno odložio attachment model na ovu story. Posle save-a, `send_lead_email(lead)` se proširuje da **attach-uje slike** na email koji stiže na `SERVICE_EMAIL_TO`. Email subject „[Ćorić Agrar] Novi servisni zahtev: {name}" (VEĆ implementiran u 4.1 `_build_subject` SERVICE_REQUEST grani — NE menja se).

**Granica scope-a (KRITIČNO):**
- **`Lead.FormType.SERVICE_REQUEST = "service_request"` VEĆ POSTOJI** (`apps/forms/models.py:34`, iz 4.1). **NEMA promene `Lead` modela, NEMA FormType member dodatka.** AC zahteva NOVI `LeadAttachment` model → **JEDNA NOVA migracija `0002`** (CreateModel LeadAttachment; SM-D1).
- **Story 4.6** kasnije standardizuje HTMX form pattern (reusable mixin/decorator) + ujednačava rate-limit kroz forme 4.2-4.5. 4.4 implementira ratelimit + OOB aria-live **inline** (per project-context.md security/a11y must-have); **NE** graditi prerano apstrakciju (YAGNI).
- **NE menja** `ContactForm`/`contact_submit` (4.2 vlasništvo), `ModelInquiryForm`/`model_inquiry_submit` (4.3 vlasništvo). DODAJE `ServiceRequestForm` + `service_request_submit` + nove partial-e + `/servis/` stranu.
- **`send_lead_email` potpis NETAKNUT** (`def send_lead_email(lead) -> bool`) — proširuje se SAMO unutrašnjost (attach `lead.attachments` slika PRE `message.send()`). `_build_subject` SERVICE_REQUEST grana je VEĆ tačna (`lead.name`) — **NE menja se** (za razliku od 4.3 MODEL_INQUIRY izmene; vidi SM-D7).
- **`ServiceRequest` zaseban model = NE.** epics.md (AUTHORITATIVE) koristi JEDAN `Lead` + `form_type` discriminator + `data` JSON (4.1 SM-D3). Attachment-i su jedini razlog za child model (multi-file).

---

## Kontekst iz postojećeg koda (REAL reference — istraženo, NE pretpostavke)

> **Napomena o brojevima linija:** `fajl:NN` ref-ovi su INDIKATIVNI (orijentiši se po imenu simbola, ne po tačnom broju linije).

### Lead model (`apps/forms/models.py` — Story 4.1, NETAKNUT u pogledu Lead-a)
- `Lead(TimestampedModel)`; **`FormType.SERVICE_REQUEST = "service_request"` VEĆ deklarisan** (`:34`, DB vrednost LOWERCASE, LOCKED). Label „Servisni zahtev".
- Polja: `form_type`, `name` (CharField 200, obavezno), `email` (EmailField), `phone` (CharField 50, **`blank=True` na modelu**), `message` (TextField, blank=True), `data` (JSONField default=dict), `ip_address`, `locale`. **NEMA `photo`, NEMA FK, NEMA `get_absolute_url`** (SM-D14 — attachment-i = ova story).
- **`data` shape za `service_request` (DEFINIŠE OVA STORY — vidi SM-D2):** `{"machine_type": "<choice-vrednost>", "brand_model": "<free text>"}`. `description` (opis kvara) ide u `Lead.message` (NE u `data`); `name`/`phone`/`email` su core Lead polja.

### Email servis (`apps/forms/notifications.py` — Story 4.1) — ⚠️ JEDNA IZMENA (attach slika)
- `def send_lead_email(lead) -> bool` — SYNC, VIEW-CALLED, save-before-send. **Potpis NETAKNUT.**
- `_resolve_recipient` (`:46`) **VEĆ mapira** `SERVICE_REQUEST → SERVICE_EMAIL_TO` (`:48-49`) — **Dev NE menja recipient logiku** (SM-D6).
- `_build_subject` (`:34`) za `SERVICE_REQUEST` (`:35-36`) **VEĆ vraća** „[Ćorić Agrar] Novi servisni zahtev: %(name)s" % {"name": lead.name} — **TAČNO per epics.md, NE menja se** (SM-D7).
- Telo se rendera iz `templates/emails/lead_received.html` (4.1) — multipart `EmailMultiAlternatives` (plain `strip_tags` + html alternative). **IZMENA (SM-D5):** PRE `message.send()`, ako lead ima attachment-e (`lead.attachments.all()`), za svaki uradi `message.attach(name, content, mimetype)` (čita `attachment.file`). Provider-send ostaje u try/except (C1 failure contract NETAKNUT).

### HTMX form pattern (`apps/forms/{forms,views,urls}.py` + `templates/forms/partials/` — Story 4.2/4.3, REUSE 1:1)
- `apps/forms/forms.py` → `ContactForm`/`ModelInquiryForm` (`forms.Form`); labele/error kroz `gettext_lazy`, HTML5 widget atributi. **REUSE kao šablon za `ServiceRequestForm`** (dodaje dropdown `machine_type` ChoiceField + free-text `brand_model` + multi-file `photos`).
- `apps/forms/views.py` → `contact_submit`/`model_inquiry_submit` FBV: `@require_POST` + `@ratelimit(key="ip", rate="5/m", block=False)`; na vrhu `if getattr(request, "limited", False): return HttpResponse(status=429)`; bind forme → invalid renderuje error partial (200), valid radi `Lead.objects.create(...)` PA `send_lead_email(lead)` PA success partial. **REUSE 1:1 struktura za `service_request_submit`** (uz `request.FILES` bind + attachment persist PRE send-a).
- `apps/forms/urls.py` → `app_name="forms"`; `htmx/forme/kontakt/`, `htmx/forme/upit-za-model/`. **Dodati** `path("htmx/forme/servis/", views.service_request_submit, name="service_request_submit")`.
- `config/urls.py` → `apps.forms.urls` VEĆ mount-ovan u `i18n_patterns` (4.2). **NEMA promene config/urls.py.**
- `templates/forms/partials/_contact_form_fields.html` → SIROVI `<input>`/`<textarea>` + `value="{{ form.X.value|default:'' }}"` idiom; ROOT `<section id="...">` swap target; in-form `role="alert"`/`aria-live="assertive"` error summary (regija #1); `{% csrf_token %}` + `hx-post`/`hx-target`/`hx-swap="outerHTML"`/`htmx-indicator`; ODVOJEN `{% if request.htmx and form.errors %}` OOB polite blok (regija #2). **Šablon za `_service_request_form_fields.html`** (uz `enctype="multipart/form-data"` + `<input type="file" multiple>` + `hx-encoding="multipart/form-data"`).
- `templates/forms/partials/contact_success.html` → ROOT `<section id="...">` koji čisto zamenjuje formu (`hx-swap="outerHTML"`); `{% if request.htmx %}` OOB polite najava. **Šablon za `service_request_success.html`.**
- `apps/forms/tests/conftest.py` → REUSE `recipient_env` (postavlja `SERVICE_EMAIL_TO`), `htmx_post` (fiksan `ip="203.0.113.7"`, `HTTP_HX_REQUEST="true"`), `superuser`, autouse `_pin_and_clear_ratelimit_cache` (locmem CACHES + `cache.clear()`). **PROŠIRITI** sa `service_request_payload` + `service_request_submit_url` + image-upload fixture-ima (validna mala JPG/PNG kroz Pillow in-memory; prevelika; ne-slika). `htmx_post` već prosleđuje `data` u `client.post` → multipart radi sa `SimpleUploadedFile` kao value (Django test client auto-multipart kad `data` sadrži file).
- `config/settings/base.py` → `CACHES` (locmem) VEĆ dodat (4.2). **NE re-add** (SM-D8). `SERVICE_EMAIL_TO` VEĆ čitan iz env (4.1).

### File-upload double-check (`apps/media_pipeline/utils.py` — Story 2.3, REUSE)
- `validate_image_mime(upload, *, allowed_mimes=ALLOWED_IMAGE_MIME_TYPES, max_size_bytes=MAX_UPLOAD_SIZE_BYTES) -> None` — raise-uje `ValidationError` (locale-aware) ako: prazan upload, > size limit, MIME signature van `allowed_mimes` (`image/jpeg`/`image/png`/`image/webp`), ILI Pillow `verify()` padne (corrupt/decompression bomb). Resetuje `upload.seek(0)` na ulazu/izlazu. **REUSE u `ServiceRequestForm.clean_photos`** — per fajl: pozovi `validate_image_mime(f, allowed_mimes=("image/jpeg","image/png"), max_size_bytes=5*1024*1024)` (epics.md: JPG/PNG, 5 MB; **NE** webp, **NE** default 10 MB).
- `MAX_UPLOAD_SIZE_BYTES` default je 10 MB; **ova story prosleđuje EKSPLICITAN `5*1024*1024`** (epics.md:815). `ALLOWED_IMAGE_MIME_TYPES` uključuje webp; **ova story prosleđuje EKSPLICITAN `("image/jpeg","image/png")`** (epics.md:815 — samo JPG/PNG).

### Dedikovana strana mount (`apps/pages` — Story 3.3 `ContactView` precedent)
- `apps/pages/views.py` → `ContactView(TemplateView)`, `template_name="pages/contact.html"`, **`http_method_names=["get","head","options"]`** (POST → 405; submit ide na ZASEBAN `apps/forms` endpoint, NE na page view). **MIRROR za `ServiceView`.**
- `apps/pages/urls.py` → `app_name="pages"`; `kontakt/` → `pages:contact`. **Dodati** `servis/` → `pages:service`.
- `templates/pages/contact.html` → `{% include "pages/partials/_contact_form.html" %}` (tanak container) → `{% include "forms/partials/_contact_form_fields.html" %}`. **MIRROR:** NOVI `templates/pages/service.html` + `templates/pages/partials/_service_form.html` container → `{% include "forms/partials/_service_request_form_fields.html" %}`.
- `apps` može importovati domain (pages SM-D6) — ali `ServiceView` je čista TemplateView (NE agregira modele; `machine_type` choices žive na formi).

### CSS (REUSE — `static/css/components/contact-page.css`)
- `coric-contact-form__*` BEM (input/textarea/error/alert/success/submit/field/label/required/indicator). **REUSE klase za servisnu formu**; novi `coric-service-form__*` ili proširenje SAMO ako file-input/dropdown/mobile-full-width layout traži (preferiraj reuse, YAGNI). Mobile UX (AC8): polja stack-ovana, submit full-width, loading state vidljiv — kroz postojeće responsive tokene.

---

## Acceptance Criteria

**AC1 — `LeadAttachment` child model (NOVI; FK→Lead CASCADE; file polje) + migracija `0002`.**
**Given** `Lead` model (4.1, NETAKNUT) + 4.1 SM-D14 precondition (attachment model = ova story)
**When** dodam `class LeadAttachment(models.Model)` u `apps/forms/models.py`
**Then** model ima:
- `lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name="attachments", verbose_name=_("Lead"))` — **`CASCADE`** (brisanje Lead-a briše attachment-e; SM-D3)
- `file = models.FileField(upload_to="leads/attachments/%Y/%m/", verbose_name=_("Datoteka"))` — **NIJE `ImageField`** (validacija je u formi kroz `validate_image_mime`; `upload_to` per godina/mesec da media dir ne eksplodira u jedan folder)
- (opciono) `created_at` ako se NE nasleđuje `TimestampedModel` — **odluka SM-D3: NE nasleđuje `TimestampedModel`** (attachment je satelit Lead-a; `lead.created_at` je dovoljan timestamp; YAGNI). Ako ipak treba: `created_at = models.DateTimeField(auto_now_add=True)` — Dev NE dodaje osim ako test traži.
- `__str__` → npr. `f"Prilog uz {self.lead_id}: {self.file.name}"`
- `Meta.verbose_name = _("Prilog")`, `verbose_name_plural = _("Prilozi")` (pune dijakritike)
**And** `uv run python manage.py makemigrations forms` generiše `apps/forms/migrations/0002_*.py` sa `CreateModel("LeadAttachment", ...)` (FK na Lead) — Dev MANUELNO reviewuje (project-context.md:221); `migrate --plan` prikazuje plan; reverzibilno (`migrate forms 0001` čisto)
**And** `Lead` model NIJE izmenjen ovom migracijom (NEMA AlterField na Lead — samo NOVI model); migracija + model promene commit-uju se ZAJEDNO (atomic)
**And** **NEMA `photo` polja dodatog na `Lead`** (multi-file zahteva child model — 4.1 SM-D14 razlog); NEMA translatable polja; `uv run python manage.py check` exit 0.

**AC2 — `ServiceRequestForm` (server-side validation SOT; polja + dropdown + multi-file).**
**Given** Lead model (FormType.SERVICE_REQUEST VEĆ postoji) + `validate_image_mime` (2.3)
**When** kreiram `ServiceRequestForm` u `apps/forms/forms.py` (Django `forms.Form`) sa poljima:
- `name` — CharField(max_length=200), **required=True** (mirror Contact)
- `phone` — CharField(max_length=50), **required=True** (epics.md:814 „Telefon *" — OBAVEZNO; NAPOMENA: razlika od ContactForm gde je phone opciono — vidi SM-D9)
- `email` — EmailField, **required=False** (epics.md:814 „Email" bez zvezdice — opciono)
- `machine_type` — ChoiceField sa `choices` iz nested `MachineType(TextChoices)` (vrednosti `tractor`/`attachment`/`work_machine`/`other`; labele „Traktor"/„Priključna mehanizacija"/„Radna mašina"/„Ostalo" kroz `gettext_lazy`), **required=True**, `widget=forms.Select`
- `brand_model` — CharField(max_length=200), **required=False** (epics.md:814 „Brend+model (free text)" bez zvezdice)
- `description` — CharField (Textarea widget), **required=True** (epics.md:814 „Opis kvara *")
- `photos` — multi-file polje (vidi SM-D4 implementacioni izbor), **required=False** (epics.md:814 „Foto (opciono...)")
**Then** sva user-facing labela/error poruka prolazi kroz `gettext_lazy` (pune dijakritike č/ć/ž/š/đ; „E-pošta", „Priključna" sa š/č; NIKAD ćirilica/šišana latinica)
**And** prazno `name`/`phone`/`machine_type`/`description` → `is_valid()` je `False` sa per-field greškama; nevalidan `machine_type` (van choices) → `False`; validan kompletan payload (sa ILI bez slika) → `True`
**And** `description` je `required=True` na FORMI iako je `Lead.message` `blank=True` na modelu (forma je validacioni SOT — mirror 4.2 AC1).

**AC3 — Foto upload double-check (MIME signature + Pillow + size + count) u `clean_photos` (KRITIČNO — security must-have).**
**Given** `ServiceRequestForm` iz AC2 + `validate_image_mime` (2.3)
**When** forma primi fajlove kroz `request.FILES.getlist("photos")`
**Then** `clean_photos` (ILI ekvivalentna clean metoda po SM-D4) MORA:
- **Brojati fajlove:** ako > **3** → `ValidationError(_("Možete priložiti najviše 3 slike."))` (epics.md:814 „do 3 slike")
- **Per fajl:** pozvati `validate_image_mime(f, allowed_mimes=("image/jpeg", "image/png"), max_size_bytes=5*1024*1024)` — MIME signature (NE samo ekstenzija) + Pillow `verify()` + size limit
- **Size error poruka konkretna** (epics.md:816 „Slika je veća od 5 MB. Probajte manju."): `validate_image_mime` već vraća locale-aware „Slika je veća od %(limit)d MB..." sa `limit=5` (jer prosleđujemo `5*1024*1024`) — **prihvatljivo** (ekvivalentna poruka sa konkretnim limitom); ako epics.md tačan string je obavezan, Dev hvata `ValidationError` iz utila i re-raise sa „Slika je veća od 5 MB. Probajte manju." (SM-D4 — Dev bira; oba zadovoljavaju AC „konkretan limit"). **TEST asertuje da poruka sadrži substring „5 MB".**
- **Nedozvoljen tip** (npr. PDF/GIF/`<script>`-renamed-`.jpg`): `validate_image_mime` MIME-signature check odbija → `ValidationError`; `Lead` se NE kreira
**And** **all-or-nothing semantika (KRITIČNO — NIKAD partial-accept):** BILO KOJI pojedinačni nevalidan fajl (loš MIME / > 5 MB / batch > 3 / corrupt) → **CEO submit se odbija**: `is_valid()` je `False`, **NIJEDAN `Lead` ni `LeadAttachment` se NE kreira** (čak ni za validne fajlove iz istog batch-a). `clean_photos` **RAISE-uje `ValidationError` na PRVOM nevalidnom fajlu** (`validate_image_mime` već raise-uje — Dev je NE sme „swallow"-ovati / hvatati-i-nastaviti); **NEMA „filter-and-return-only-valid" putanje.** (Vidi AC7 mixed-batch ugovor i SM-D4.)
**And** **double-check je OBAVEZAN** (project-context.md anti-pattern „File upload bez double-check") — NIKAD oslanjanje samo na Django `FileField`/`ImageField` ekstenziju
**And** validacija ne menja stanje (čist `clean` — bez side-effect-a save-a; save je u view-u posle `is_valid()`).

**AC4 — HTMX POST endpoint (multipart) + URL wiring.**
**Given** `ServiceRequestForm` iz AC2
**When** dodam `service_request_submit` FBV u `apps/forms/views.py` + `path("htmx/forme/servis/", views.service_request_submit, name="service_request_submit")` u `apps/forms/urls.py`
**Then** `reverse("forms:service_request_submit")` (uz aktivan `sr` locale) rezolvuje na `/sr/htmx/forme/servis/` (i18n-prefiksovan; `config/urls.py` NETAKNUT)
**And** endpoint prihvata SAMO POST (GET → 405, `@require_POST`)
**And** view bind-uje formu sa **`ServiceRequestForm(request.POST, request.FILES)`** (multipart — file-ovi su u `request.FILES`)
**And** view radi save-before-send redosled: (1) `Lead.objects.create(form_type=Lead.FormType.SERVICE_REQUEST, name=..., phone=..., email=..., message=<description>, locale=get_language(), ip_address=<REMOTE_ADDR>, data={"machine_type": ..., "brand_model": ...})`; (2) za svaki validan upload `LeadAttachment.objects.create(lead=lead, file=f)`; (3) TEK ONDA `send_lead_email(lead)`.

**AC5 — Uspešan submit (success partial + Lead + Lead.data + attachment-i + email sa attach-om).**
**Given** endpoint iz AC4 + `recipient_env` (`SERVICE_EMAIL_TO` postavljen)
**When** pošaljem validan multipart POST sa `name`/`phone`/`machine_type`/`description` (+ opciono `email`/`brand_model`) + 1-3 validne JPG/PNG slike
**Then** kreira se TAČNO 1 `Lead` red sa `form_type == "service_request"`, `name`/`phone`/`email` iz payload-a, `message == <description>`, `locale`, `ip_address` popunjen, i **`data == {"machine_type": "<vrednost>", "brand_model": "<text>"}`** (SM-D2 shape)
**And** kreira se po 1 `LeadAttachment` red po priloženoj slici (`lead.attachments.count() == broj_slika`); fajlovi sačuvani pod `leads/attachments/...`
**And** view vraća success partial (`templates/forms/partials/service_request_success.html`) — forma se HTMX-swap-uje; response NIJE full HTML page
**And** `send_lead_email(lead)` je pozvan (1 email u `mailoutbox`); **subject sadrži „[Ćorić Agrar] Novi servisni zahtev: {name}"**; `to == [settings.SERVICE_EMAIL_TO]`; **`len(mailoutbox[0].attachments) == broj_priloženih_slika`** (slike attach-ovane na email — epics.md:818).

**AC6 — Submit BEZ slika (foto je opciono).**
**Given** endpoint iz AC4
**When** pošaljem validan POST BEZ ijednog fajla (`photos` prazno)
**Then** `Lead` se kreira normalno (`form_type='service_request'`); `lead.attachments.count() == 0`; success partial; `len(mailoutbox) == 1`; `len(mailoutbox[0].attachments) == 0` (email bez priloga). Foto je opciono (epics.md:814) — odsustvo NE blokira submit.

**AC7 — Neuspešan submit (error rerender + dve a11y regije; preveliki/nevalidan fajl PRE kreiranja Lead-a).**
**Given** endpoint iz AC4
**When** pošaljem nevalidan POST (prazno `name`/`phone`/`machine_type`/`description`, ILI > 3 slike, ILI slika > 5 MB, ILI ne-slika fajl)
**Then** view vraća form partial rerender (bound form sa `form.errors`), **HTTP 200** (NE 4xx — HTMX swap error UI)
**And** rerender sadrži **U-FORMI** `<div role="alert" aria-live="assertive">` error summary (regija #1) sa per-field greškama (REUSE 4.2 obrazac); za file greške poruka sadrži konkretan limit („5 MB" / „najviše 3 slike")
**And** **NIJEDAN `Lead` red NIJE kreiran, NIJEDAN `LeadAttachment` NIJE kreiran, NIJEDAN email NIJE poslat** (`Lead.objects.count() == 0`, `LeadAttachment.objects.count() == 0`, `mailoutbox` prazan) — validacija (uključujući foto double-check) se dešava PRE `Lead.objects.create` (epics.md:816 „greška PRE slanja")
**And** **MIXED-BATCH all-or-nothing (KRITIČNO):** POST sa **1 validna JPG + 1 nevalidna** (ne-slika ILI > 5 MB) → `is_valid()` je `False` i submit se ODBIJA U CELOSTI: `Lead.objects.count() == 0`, `LeadAttachment.objects.count() == 0` (validna slika iz istog batch-a se NE perzistira), `mailoutbox` prazan, error poruka prisutna. NIKAD se ne sme sačuvati „samo dobre slike" iz batch-a koji sadrži ijedan loš fajl (vidi AC3 all-or-nothing + SM-D4).
**And** rerender ČUVA tekstualna polja (`name`/`phone`/`description`/`brand_model`/`machine_type`) tako da korisnik ne gubi unos (file polja se NE mogu re-popuniti — browser security; prihvatljivo).

> **Dve ODVOJENE a11y regije (KRITIČNO — REUSE 4.2 SM-D12):** error odgovor MORA imati OBE: (1) **in-form** `role="alert"`/`aria-live="assertive"` summary UNUTAR form partial-a, I (2) **ODVOJEN** `hx-swap-oob="innerHTML:#aria-live"` blok ka `base.html` `aria-live="polite"` singletonu. Singleton OSTAJE `polite`. Success odgovor sadrži SAMO OOB polite najavu.

**AC8 — Mobile-specific UX (epics.md:819).**
**Given** success/form partial iz AC5/AC7
**When** strana se renderuje na mobile viewport-u (<768px)
**Then** form polja su stack-ovana (1 kolona); submit dugme je full-width; loading state (`htmx-indicator` spinner) vidljiv tokom upload-a (slike mogu biti spore na 4G)
**And** file input dozvoljava izbor sa kamere/galerije (`<input type="file" accept="image/jpeg,image/png" multiple>` — `accept` aktivira mobilnu kameru/galeriju; `multiple` za do 3 slike)
**And** layout koristi `var(--token)` (NE inline magic) — REUSE/proširenje `contact-page.css` responsive pravila.

**AC9 — OOB aria-live announcement (HTMX a11y).**
**Given** HTMX response patterns (project-context.md:184-194; REUSE 4.2/4.3 AC7)
**When** success ILI error response se vrati na HTMX zahtev
**Then** response uključuje `hx-swap-oob="innerHTML:#aria-live"` element ciljajući `base.html` `{% aria_live %}` singleton sa kratkom porukom (success: „Servisni zahtev je poslat."; error: „Greška pri slanju, proverite polja.") kroz `{% translate %}`
**And** OOB blok je guarded `{% if request.htmx %}` (REUSE — ne curi u non-HTMX render).

**AC10 — Security must-haves (CSRF + ratelimit → HTTP 429; multipart; REUSE 4.2/4.3).**
**Given** project-context.md security must-have
**When** wire-ujem formu
**Then** form template sadrži `{% csrf_token %}` (HTMX šalje CSRF header); forma ima `enctype="multipart/form-data"` + `hx-encoding="multipart/form-data"` (HTMX file upload zahteva eksplicitan encoding)
**And** `service_request_submit` ima `@ratelimit(key="ip", rate="5/m", block=False)` — **EKSPLICITNO `block=False`** (NE `block=True` → 403; vidi 4.2 SM-D9)
**And** na VRHU tela (PRE bind-a forme i PRE `Lead.objects.create`): `if getattr(request, "limited", False): return HttpResponse(status=429)`
**And** 6. uzastopni submit sa istog IP-a u 1 minuti → **HTTP 429** (5 prvih prolazi, 6. blokiran)
**And** ratelimit koristi Django `default` cache (locmem `CACHES` VEĆ u `config/settings/base.py` — 4.2; NE re-add); test pinuje cache + `cache.clear()` (REUSE autouse `_pin_and_clear_ratelimit_cache`).

**AC11 — NOVA `/servis/` strana (FR-22) + mount forme (NE duplira ContactView).**
**Given** `ContactView` precedent (3.3) + `pages` app
**When** kreiram `ServiceView` u `apps/pages/views.py` + `path("servis/", ServiceView.as_view(), name="service")` u `apps/pages/urls.py` + `templates/pages/service.html` + `templates/pages/partials/_service_form.html`
**Then** `reverse("pages:service")` (uz `sr`) → `/sr/servis/`; GET `/sr/servis/` → **200** sa aktivnom (NE disabled) servisnom formom
**And** `ServiceView` je **GET-only** (`http_method_names=["get","head","options"]`) → POST na `pages:service` vraća **405** (submit ide na ZASEBAN `forms:service_request_submit`, NE na page view — mirror ContactView/SM)
**And** strana renderuje servisnu formu kroz container partial → `{% include "forms/partials/_service_request_form_fields.html" %}`; CSRF token prisutan u renderovanoj formi; `hx-post` ka `forms:service_request_submit`
**And** strana sadrži minimalan kontekst „Servisna podrška" (naslov + kratak opis + forma) kroz `{% translate %}` (puni dijakritik); SiteSettings telefon/kontakt = hardkodovan-translatable placeholder + TODO (3-4/8-9 — NE blokira; SM-D11). **Hitni `tel:` pozivi CTA** (mirror 4.3 success — Stojan je sa terena) kroz klikabilan `tel:` link.

**AC12 — i18n + dijakritike + lint.**
**Given** project-context.md i18n + anti-pattern pravila
**When** dodam sve nove stringove
**Then** SVE user-facing strings (labele, dropdown opcije, error/success/aria poruke, page copy, telefon) idu kroz `gettext_lazy`/`{% translate %}` sa punim dijakritikama; NIKAD ćirilica, NIKAD šišana latinica
**And** novi `.po` msgid-ovi dodati i kompajlirani kroz `just messages` (makemessages + compilemessages za sr/hu/en); hu/en smeju ostati prazni (fallback sr — isto kao 4.1 AC9 / 4.3 politika)
**And** `just lint` (ruff + djade) clean; `just test` (novi forms + pages + media_pipeline regresija) prolazi.

**AC13 — `LeadAttachment` u admin-u (read-mostly inline na LeadAdmin).**
**Given** `LeadAdmin` (4.1) + NOVI `LeadAttachment` (AC1)
**When** proširim `apps/forms/admin.py`
**Then** `LeadAttachment` je vidljiv kroz `TabularInline`/`StackedInline` na `LeadAdmin` (admin može da vidi/preuzme priložene slike za servisni lead — project-context.md:202 inline pattern)
**And** inline je read-mostly (admin NE kreira lead-ove ručno; opciono `readonly_fields`); registracija na POSTOJEĆI `admin.site` (mirror 4.1 SM-D8 — NE custom slug/axes, to je Epic 8.1)
**And** `reverse("admin:forms_lead_changelist")` GET (superuser) → 200 (regression — postojeći LeadAdmin radi sa novim inline-om).

---

## Tasks / Subtasks (TDD-ordered: TEA RED → Dev GREEN)

> **Disciplina (project-context.md:293-298):** TEA agent piše testove (RED phase) PRVI; Dev agent piše implementaciju (GREEN); **Dev NIKAD ne piše testove.** Testovi se commit-uju pre implementacije. Migracije (makemigrations + MANUAL REVIEW + migrate) su DEV task-ovi. Ako TEA testovi failuju u Dev fazi → story `paused`, ne maskirati greške.
>
> **Test konvencija (REUSE 4.2/4.3):** SVI service POST testovi koriste `htmx_post` fixture (fiksan IP `203.0.113.7`, `HTTP_HX_REQUEST="true"`) — NE sirov `client.post` (osim deliberate non-HTMX test). Multipart: prosledi file-ove kao `SimpleUploadedFile` u `data` dict-u (Django test client auto-multipart). Image fixture-i kroz Pillow in-memory (`Image.new("RGB",(10,10))` → `BytesIO` → `SimpleUploadedFile(..., content_type="image/jpeg")`). Email testovi REUSE `mailoutbox` + `recipient_env`. NIKAD pravi send.

### Task 1 — (TEA, RED) Fixtures + LeadAttachment model + migracija testovi
- [ ] 1.1 Proširi `apps/forms/tests/conftest.py` (REUSE `recipient_env`/`htmx_post`/`superuser`/autouse cache) sa: `service_request_payload` (`{"name": "Stojan Stojanović", "phone": "+381641234567", "email": "stojan@example.com", "machine_type": "tractor", "brand_model": "Agri Tracking TB804", "description": "Curi ulje iz hidraulike."}` — pun dijakritik); `service_request_submit_url` (`activate("sr")` + `reverse("forms:service_request_submit")`); `valid_image_jpeg` / `valid_image_png` (Pillow → `SimpleUploadedFile`, ~mali, validan); `valid_image_webp` (validan WEBP kroz Pillow → `SimpleUploadedFile(..., content_type="image/webp")` — za „webp odbijen jer nije u allowed_mimes" assertion u Task 2.2; `allowed_mimes` pinovan na jpeg/png); `oversized_image` (**VALIDNA mala JPEG slika kroz Pillow čiji je `.size` atribut monkeypatched/forsiran preko 5*1024*1024**, NE sirov `BytesIO` zeroes). **RATIONALE (provereno protiv `apps/media_pipeline/utils.py`):** `validate_image_mime` proverava `upload.size` u size-grani, ALI sirov 5 MB `BytesIO` nula NIJE validna slika → pao bi PRVO na MIME-signature / Pillow `verify()` grani i raise-ovao POGREŠNU grešku (NE „5 MB" size poruku). Samo validna mala slika sa naduvanim `.size` pouzdano okida size-limit granu i „5 MB" poruku. `non_image_file` (`SimpleUploadedFile("x.pdf", b"%PDF-1.4...", content_type="application/pdf")` — MIME-signature mismatch). Image fixture-i u `tests/fixtures/` ili in-memory generisani.
- [ ] 1.2 `apps/forms/tests/test_lead_attachment_model.py` (AC1): `LeadAttachment` ima `lead` FK (`on_delete=CASCADE`, `related_name="attachments"`), `file` FileField; brisanje `Lead`-a kaskadno briše `LeadAttachment` (`lead.delete()` → `LeadAttachment.objects.count()==0`); `__str__` informativan; `Meta.verbose_name` pun dijakritik („Prilog"/„Prilozi"). **Asertuj `LeadAttachment._meta.get_field("lead").remote_field.on_delete is models.CASCADE`** i `related_name=="attachments"`. **Asertuj da NEMA `created_at` polja** (SM-D3 — NE nasleđuje `TimestampedModel`): `assert "created_at" not in {f.name for f in LeadAttachment._meta.get_fields()}` (sprečava da Dev tiho doda timestamp).
- [ ] 1.3 `apps/forms/tests/test_lead_attachment_migration.py` (AC1): migracija `0002` postoji; `migrate forms` primeni bez greške; `makemigrations forms --check --dry-run` ne traži NOVE migracije posle (model i migracija sinhronizovani); `Lead` tabela NIJE izmenjena (samo NOVI `LeadAttachment` model — NEMA `photo` kolone na Lead-u).

### Task 2 — (TEA, RED) ServiceRequestForm validacija + foto double-check
- [ ] 2.1 `apps/forms/tests/test_service_request_form.py` (AC2): polja postoje (`name`/`phone`/`email`/`machine_type`/`brand_model`/`description`/`photos`); **obavezni:** `name`/`phone`/`machine_type`/`description`; **opcioni:** `email`/`brand_model`/`photos`; `machine_type` choices == {tractor, attachment, work_machine, other}; nevalidan `machine_type` → invalid; labele/error kroz gettext (substring pune dijakritike „Priključna"/„E-pošta"; NEMA ćirilice); validan payload (sa i bez slika) → valid.
- [ ] 2.2 `apps/forms/tests/test_service_request_photo_validation.py` (AC3 — KRITIČNO): 
  - **> 3 slike** → `is_valid()` False; greška sadrži „najviše 3" (ILI ekvivalent sa „3").
  - **> 5 MB slika** → False; greška sadrži substring „5 MB".
  - **ne-slika fajl** (PDF sa lažnom `.jpg` ekstenzijom ILI pravi PDF content-type) → False (MIME signature odbija); greška „Nedozvoljen tip" ILI ekvivalent.
  - **corrupt „slika"** (random bytes sa `image/jpeg` content_type ali Pillow `verify()` padne) → False.
  - **3 validne slike** → valid (granica je inkluzivna do 3).
  - **0 slika** → valid (opciono).
  - **MIXED-BATCH (all-or-nothing — KRITIČNO):** 1 validna `valid_image_jpeg` + 1 nevalidna (`non_image_file` ILI `oversized_image`) → `is_valid()` je `False` (cela forma invalid), greška prisutna. Ovaj test forsira ispravnu all-or-nothing implementaciju (NE sme proći filter-and-keep-good).
  - **webp je odbijen** jer NIJE u `allowed_mimes` (pinovan na jpeg/png): validan `valid_image_webp` upload → `is_valid()` False.
  - **Asertuj da forma poziva `validate_image_mime` sa `allowed_mimes=("image/jpeg","image/png")` i `max_size_bytes=5*1024*1024`** (mock/spy ILI behavior assertion — webp se odbija jer NIJE u allowed).

### Task 3 — (TEA, RED) HTMX endpoint: success + Lead.data + attachments + email attach
- [ ] 3.1 `apps/forms/tests/test_service_request_view.py` (AC4/AC5):
  - `reverse("forms:service_request_submit")` rezolvuje pod `activate("sr")` → `/sr/htmx/forme/servis/` (RED dok URL ne postoji).
  - GET → 405.
  - **Success sa VIŠE slika (multi-file idiom — KRITIČNO):** POST data MORA proslediti LISTU pod jednim ključem da bi se `getlist` multi-file putanja stvarno izvršila, npr. `htmx_post(service_request_submit_url, {**service_request_payload, "photos": [valid_image_jpeg, valid_image_png]})`. **Django 5.2 test client kodira list-vrednost kao više file part-ova pod istim imenom polja → `request.FILES.getlist("photos")` vraća sve.** Single-file test (`"photos": f1`) NE izvršava multi-file putanju i NE sme biti jedino pokriće.
  - **Success sa slikama:** validan HTMX multipart POST sa 2 JPG (lista, vidi gore) → 200; `Lead.objects.count()==1`; `lead.form_type==Lead.FormType.SERVICE_REQUEST`; `lead.message=="<description>"`; `lead.data=={"machine_type":"tractor","brand_model":"Agri Tracking TB804"}`; `lead.locale=="sr"`; `lead.ip_address` popunjen; `lead.attachments.count()==2`; success partial korišćen; `len(mailoutbox)==1`; `mailoutbox[0].subject` sadrži „[Ćorić Agrar] Novi servisni zahtev: Stojan Stojanović"; `mailoutbox[0].to==[settings.SERVICE_EMAIL_TO]`; **`len(mailoutbox[0].attachments)==2`** (slike attach-ovane).
- [ ] 3.2 (AC6) **Success bez slika:** validan POST bez file-ova → `Lead` kreiran; `lead.attachments.count()==0`; `len(mailoutbox)==1`; `len(mailoutbox[0].attachments)==0`. **Prazan `brand_model` data-shape (SM-D2 lock):** varijanta gde je `brand_model` izostavljen/prazan → asertuj `lead.data == {"machine_type": "tractor", "brand_model": ""}` (ključ `brand_model` PRISUTAN sa praznim stringom, NE izostavljen) — zaključava SM-D2 shape za prazan opcioni-field slučaj.
- [ ] 3.3 (AC5 partial): success response NIJE full page (NE sadrži `<html`/`<head>`). **Simetrično:** error response je takođe partial.
- [ ] 3.4 (AC5 subject regression — notifications.py): `send_lead_email` za `SERVICE_REQUEST` lead → subject sadrži „Novi servisni zahtev: {name}" (`lead.name`, NE menja se — SM-D7); recipient `SERVICE_EMAIL_TO` (`_resolve_recipient` NETAKNUT — SM-D6). **Direktan test attach mehanizma (SM-D5):** lead sa 1 `LeadAttachment` → `send_lead_email(lead)` → `mailoutbox[0].attachments` ima 1 stavku sa imenom fajla; **asertuj i mimetype tuple-a:** `name, content, mimetype = mailoutbox[0].attachments[0]; assert mimetype in ("image/jpeg", "image/png")` (sprečava da Dev prosledi `None` mimetype i prođe green); lead BEZ attachment-a → `attachments` prazno (regression — postojeći 4.1 `test_send_lead_email` ostaje zelen).

### Task 4 — (TEA, RED) Error rerender + dve a11y regije + OOB + ratelimit + email-failure
- [ ] 4.1 `apps/forms/tests/test_service_request_errors.py` (AC7): nevalidan POST (prazno `name`) → 200 (NE 4xx); `Lead.objects.count()==0`; `LeadAttachment.objects.count()==0`; `len(mailoutbox)==0`; rerender sadrži `role="alert"` + `aria-live="assertive"` + error tekst; rerender ČUVA tekstualna polja (`name`/`description` value-i prisutni). **File-reject PRE Lead-a:** POST sa 4 slike (validna ostala polja) → 0 Lead, 0 attachment, 0 email, error poruka „najviše 3"; POST sa >5MB slikom → 0 Lead, error „5 MB". **MIXED-BATCH endpoint (all-or-nothing — KRITIČNO):** HTMX multipart POST sa `{**service_request_payload, "photos": [valid_image_jpeg, non_image_file]}` (1 validna + 1 nevalidna) → 200, `Lead.objects.count()==0`, `LeadAttachment.objects.count()==0` (validna slika se NE perzistira), `len(mailoutbox)==0`, error poruka prisutna. Ovo je test koji forsira ispravnu all-or-nothing implementaciju na endpoint nivou.
- [ ] 4.2 `apps/forms/tests/test_service_request_aria_live.py` (AC9 + AC7 dve regije): success response → `hx-swap-oob="innerHTML:#aria-live"` + „Servisni zahtev je poslat." (SAMO OOB polite); error response → OBE regije (in-form assertive + ODVOJEN OOB polite „Greška pri slanju, proverite polja."); OOB guarded `{% if request.htmx %}` (non-HTMX POST → NEMA `hx-swap-oob`); singleton ostaje `polite`.
- [ ] 4.3 `apps/forms/tests/test_service_request_xss.py` (AC7 XSS — javna unauth forma; auto-escape u OBA konteksta): **(1) ERROR partial:** nevalidan POST (npr. nedostaje obavezni `phone`/`machine_type`) SA `<script>alert(1)</script>` u `name` → error rerender auto-escape (`&lt;script&gt;`, NIKAD sirov `<script>`). **(2) SUCCESS partial / bilo koja response površina gde se echo-uje uneto `name`/`description`:** validan submit SA `<script>` u `name` → ako se ime/opis prikazuju u success response-u, escape-ovani su (`&lt;script&gt;`), NIKAD sirovi. Asertuj odsustvo sirovog `<script>` u OBA slučaja.
- [ ] 4.4 `apps/forms/tests/test_service_request_email_failure.py` (4.2 SM-D5 obrazac): `mock.patch` na `apps.forms.views.send_lead_email` → `False`; validan submit → Lead i attachment-i i dalje postoje (count-ovi tačni); posetilac i dalje dobija success partial. (Mock SAMO servis-povratnu vrednost, NE ORM.)
- [ ] 4.5 `apps/forms/tests/test_service_request_ratelimit.py` (AC10): 5 submit-a OK; 6. submit sa istog IP-a u istom minutu → `status_code==429` (NE 403). REUSE autouse `_pin_and_clear_ratelimit_cache` + `htmx_post`.

### Task 5 — (TEA, RED) `/servis/` strana + mount (a11y/regression)
- [ ] 5.1 `apps/pages/tests/test_service_url.py` (AC11): `reverse("pages:service")` pod `sr` → `/sr/servis/`; GET → 200; POST na `pages:service` → **405** (GET-only); template `pages/service.html` korišćen.
- [ ] 5.2 `apps/pages/tests/test_service_form_wired.py` (AC11): plain `client.get("/sr/servis/")` → 200; renderovana strana sadrži servisnu formu (NEMA `disabled` na poljima/submit-u); `hx-post` ka `forms:service_request_submit`; `enctype="multipart/form-data"`; `<input type="file"` sa `multiple` + `accept`; **CSRF token prisutan** (`csrfmiddlewaretoken`); `tel:` hitni-pozivi CTA prisutan. (Forma se renderuje BEZ bound `form` na GET — `ServiceView` je TemplateView, NE prosleđuje `form`; partial mora biti None-safe — sirov-`<input>` idiom mirror 4.2/4.3.)

### Task 6 — (TEA, RED) Admin inline
- [ ] 6.1 `apps/forms/tests/test_lead_admin_attachment.py` (AC13): `LeadAttachment` inline registrovan na `LeadAdmin`; superuser GET `reverse("admin:forms_lead_changelist")` → 200; superuser GET change-view lead-a sa attachment-ima → 200 (inline se renderuje). (Regression — postojeći 4.1 LeadAdmin smoke ostaje zelen.)

### Task 7 — (Dev, GREEN) `LeadAttachment` model + migracija
- [x] 7.1 Dodaj `class LeadAttachment(models.Model)` u `apps/forms/models.py` (NE diraj `Lead`): `lead` FK (CASCADE, related_name="attachments"), `file = FileField(upload_to="leads/attachments/%Y/%m/")`, `__str__`, `Meta.verbose_name`/`_plural` (pune dijakritike „Prilog"/„Prilozi"). **NE nasleđuje `TimestampedModel`** (SM-D3 — YAGNI; osim ako Task 1.2 traži `created_at`).
- [x] 7.2 `uv run python manage.py makemigrations forms` → `0002_*.py`; **MANUAL REVIEW** (project-context.md:221 — potvrdi samo `CreateModel("LeadAttachment")`, FK na Lead, NEMA AlterField na Lead, NEMA `photo` kolone); `migrate --plan`; `migrate forms`. Commit model + migracija ZAJEDNO.

### Task 8 — (Dev, GREEN) `ServiceRequestForm` + foto double-check
- [x] 8.1 Dodaj `ServiceRequestForm(forms.Form)` u `apps/forms/forms.py` (NE diraj `ContactForm`/`ModelInquiryForm`): `name`/`phone`/`machine_type`/`description` obavezni; `email`/`brand_model`/`photos` opcioni; `machine_type` ChoiceField + nested `MachineType(TextChoices)` (tractor/attachment/work_machine/other; labele kroz `gettext_lazy`); `photos` multi-file (SM-D4 — kanonski Django 5.x idiom: custom `MultipleFileInput(forms.ClearableFileInput)` sa `allow_multiple_selected=True` + custom `MultipleFileField(forms.FileField)` koji override-uje `clean` da iterira listu; **NE** `MultipleHiddenInput` — to je za multi-value hidden TEXT inpute, pogrešno za file upload). Labele/error kroz `gettext_lazy` (pune dijakritike). HTML5 widget atributi (`type=tel`, `required`, `accept`) = UX sloj.
- [x] 8.2 `clean_photos` (ILI `clean` za file listu — SM-D4): čita `self.files.getlist("photos")`; ako > 3 → `ValidationError(_("Možete priložiti najviše 3 slike."))`; per fajl `validate_image_mime(f, allowed_mimes=("image/jpeg","image/png"), max_size_bytes=5*1024*1024)` (REUSE `apps.media_pipeline.utils`); size error obezbeđuje substring „5 MB" (Dev re-raise sa epics.md stringom ako util poruka nije dovoljna — SM-D4). **All-or-nothing semantika (NIKAD partial-accept):** clean iterira; na PRVOM neuspehu PROPAGIRA `ValidationError` (cela forma invalid → view NE kreira ni Lead ni LeadAttachment); na uspehu (SVI fajlovi validni) vraća **punu validiranu listu** (sve fajlove). NE filtrirati nevalidne i vraćati samo validne — takve putanje NEMA.

### Task 9 — (Dev, GREEN) `service_request_submit` view + URL
- [x] 9.1 `apps/forms/views.py`: dodaj `service_request_submit` FBV (REUSE `contact_submit` struktura) — `@require_POST` + `@ratelimit(key="ip", rate="5/m", block=False)`; top `if getattr(request,"limited",False): return HttpResponse(status=429)`; bind **`ServiceRequestForm(request.POST, request.FILES)`**; invalid → render error partial (200, bound form); valid → `lead = Lead.objects.create(form_type=Lead.FormType.SERVICE_REQUEST, name=..., phone=..., email=..., message=form.cleaned_data["description"], locale=get_language(), ip_address=request.META.get("REMOTE_ADDR"), data={"machine_type": form.cleaned_data["machine_type"], "brand_model": form.cleaned_data["brand_model"]})`; za svaki fajl iz `form.cleaned_data["photos"]` → `LeadAttachment.objects.create(lead=lead, file=f)`; `send_lead_email(lead)`; render success partial. **NEMA cross-app import-a** (forms→products NIJE potreban ovde — servis nema product context).
- [x] 9.2 `apps/forms/urls.py`: dodaj `path("htmx/forme/servis/", views.service_request_submit, name="service_request_submit")` (POSLE postojećih). `config/urls.py` NETAKNUT.

### Task 10 — (Dev, GREEN) `notifications.py` — attach slika
- [x] 10.1 `apps/forms/notifications.py` `send_lead_email`: PRE `message.send()` dodaj — za svaki `attachment in lead.attachments.all()` čitaj sadržaj kroz **context manager** (izbegava handle-leak na grešci): `with attachment.file.open("rb") as f: content = f.read()` (NE bare open/read/close). Ime fajla: `name = attachment.file.name.split("/")[-1]`. **Mimetype sa eksplicitnim fallback-om:** `mimetype = mimetypes.guess_type(name)[0] or "application/octet-stream"` (`guess_type` može vratiti `None` → part bez Content-Type — fallback to sprečava). Potom `message.attach(name, content, mimetype)`. **`_build_subject` SERVICE_REQUEST grana NETAKNUTA** (VEĆ tačna — SM-D7); `_resolve_recipient` NETAKNUT (SM-D6). Provider-send ostaje u try/except (C1 NETAKNUT). **Lead bez `attachments` → no-op** (prazan queryset; postojeći kontakt/model-inquiry lead-ovi rade isto kao pre — regression).

### Task 11 — (Dev, GREEN) Forms partials (fields + success)
- [x] 11.1 `templates/forms/partials/_service_request_form_fields.html` (REUSE `_contact_form_fields.html` struktura): ROOT `<section id="service-form-section">` (swap target); **`<form ... enctype="multipart/form-data" hx-encoding="multipart/form-data">`** (HTMX file upload); SIROVI `<input>`/`<select>`/`<textarea>` + `value="{{ form.X.value|default:'' }}"` idiom (None-safe za GET bez bound form); polja: `name`/`phone`/`email`/`machine_type` (`<select>` sa opcijama kroz `{% translate %}`)/`brand_model`/`description` (textarea) + **`<input type="file" name="photos" accept="image/jpeg,image/png" multiple>`** (AC8); per-field greške + in-form `role="alert"`/`aria-live="assertive"` error summary (regija #1) + `{% csrf_token %}` + `hx-post="{% url 'forms:service_request_submit' %}"`/`hx-target="#service-form-section"`/`hx-swap="outerHTML"`/`htmx-indicator` + ODVOJEN `{% if request.htmx and form.errors %}` OOB polite blok (regija #2). Standalone-renderable.
- [x] 11.2 `templates/forms/partials/service_request_success.html` (REUSE `contact_success.html`): ROOT `<section id="service-form-section">` (čisto zamenjuje formu); poruka zahvalnosti (`{% translate %}`) + **`tel:` hitni-pozivi CTA** (hardkodovan-translatable placeholder + TODO ka SiteSettings 3-4/8-9 ILI `{% site_setting %}` ako dostupan — SM-D11); `{% if request.htmx %}` OOB polite „Servisni zahtev je poslat.".

### Task 12 — (Dev, GREEN) `/servis/` strana (pages app)
- [x] 12.1 `apps/pages/views.py`: dodaj `ServiceView(TemplateView)` (mirror `ContactView`) — `template_name="pages/service.html"`, `http_method_names=["get","head","options"]` (POST → 405; submit ide na forms endpoint). `apps/pages/urls.py`: `path("servis/", ServiceView.as_view(), name="service")`.
- [x] 12.2 `templates/pages/service.html` (mirror `pages/contact.html`): naslov „Servisna podrška" + kratak opis (`{% translate %}`, puni dijakritik) + `{% include "pages/partials/_service_form.html" %}` + hitni `tel:` CTA. `templates/pages/partials/_service_form.html` (tanak container, mirror `_contact_form.html`): `{% include "forms/partials/_service_request_form_fields.html" %}`.
- [x] 12.3 (inspekcija OBAVEZNA, wiring uslovan) Dev MORA pregledati `templates/partials/header.html` za Epic 4/5 „Servis" TODO slot (commit 7b1464f). AKO „Servis" slot/TODO postoji → wire `href` na `{% url 'pages:service' %}` (zameni `href="#"`). AKO ne postoji → NE dodavati (nav admin = Epic 8.9; YAGNI). Inspekcija je obavezna; rezultat (wired ILI „nema slot-a") dokumentovati u oba slučaja.

### Task 13 — (Dev, GREEN) Admin inline
- [x] 13.1 `apps/forms/admin.py`: dodaj `class LeadAttachmentInline(admin.TabularInline)` (`model=LeadAttachment`, `extra=0`, opciono `readonly_fields`); dodaj `inlines=[LeadAttachmentInline]` na `LeadAdmin`. Registracija na POSTOJEĆI `admin.site` (NE custom slug/axes — Epic 8.1).

### Task 14 — (Dev, GREEN) CSS + i18n + lint + verifikacija
- [x] 14.1 REUSE `coric-contact-form__*` BEM iz `static/css/components/contact-page.css` za servisnu formu. Ako file-input/dropdown/mobile-full-width layout traži → proširi `contact-page.css` ILI nova `service-form.css` `@import` u `main.css`; `var(--token)` umesto magic vrednosti; NIKAD inline style. AC8 mobile: stack + full-width submit + vidljiv `htmx-indicator`.
- [x] 14.2 `just messages` (makemessages + compilemessages za sr/hu/en) za nove `{% translate %}`/`gettext_lazy` stringove (page copy, dropdown opcije, file error poruke, success/aria, tel CTA).
- [x] 14.3 `just lint` (ruff + djade) clean; `just test` (forms + pages + media_pipeline regresija) zelen. Self-review checklist (project-context.md:425): CSRF+ratelimit ✓, **file upload double-check (MIME+Pillow+size+count) ✓**, aria-live OOB ✓, gettext sve ✓, no inline style ✓, no defensive validation na internim pozivima ✓, migracija manually reviewed ✓.

---

## SM Decisions (log)

- **SM-D1 (JEDNA nova migracija — `LeadAttachment` CreateModel) — KRITIČNO:** `Lead.FormType.SERVICE_REQUEST` VEĆ postoji (4.1) → **0 izmena `Lead` modela, 0 FormType dodataka.** Ali AC zahteva multi-file attachment, što JEDAN `FileField` na Lead-u ne može (3 fajla). 4.1 SM-D14 je EKSPLICITNO odložio attachment model na ovu story (da izbegne pogrešan single-file field + mid-sprint migraciju). Rešenje: NOVI `LeadAttachment` child model (FK→Lead) + migracija `0002` (CreateModel — NE AlterField na Lead). Ovo je JEDINA migracija u 4.4.
- **SM-D2 (`Lead.data` shape za `service_request`) — DEFINIŠE OVA STORY:** `data = {"machine_type": "<choice>", "brand_model": "<free text>"}`. `description` (opis kvara) ide u `Lead.message` (core polje, semantički „glavna poruka" leada — mirror kontakt forme gde poruka = message). `name`/`phone`/`email` su core Lead polja. Shape je locked za Epic 8.3 admin prikaz + potencijalni future export. (Mirror 4.3 `model_inquiry` data shape lock.)
- **SM-D3 (`LeadAttachment` dizajn):** `FileField` (NE `ImageField` — validacija je u formi kroz `validate_image_mime`; `ImageField` bi duplirao Pillow check ali sa slabijom MIME-signature proverom). `on_delete=CASCADE` (attachment je satelit Lead-a; brisanje lead-a u admin-u/GDPR-u briše slike — Epic 7 retencija). `related_name="attachments"` (view koristi `lead.attachments`, notifications `lead.attachments.all()`). `upload_to="leads/attachments/%Y/%m/"` (godina/mesec particionisanje — media dir ne eksplodira). **NE nasleđuje `TimestampedModel`** (YAGNI — `lead.created_at` je dovoljan; attachment nema nezavisan lifecycle).
- **SM-D4 (multi-file Django idiom + foto validacija) — implementacioni izbor:** Django stock `forms.FileField` NE podržava `multiple` bez custom widget/field-a. **Kanonski Django 5.x idiom (JEDINI — NE koristiti `MultipleHiddenInput`, koji je za multi-value hidden TEXT inpute, NE za file upload):** custom `MultipleFileInput(forms.ClearableFileInput)` sa `allow_multiple_selected=True` + custom `MultipleFileField(forms.FileField)` koji override-uje `clean` da iterira listu (Django docs „Uploading multiple files"). Dev implementira taj idiom ILI ekvivalent. **Validacija (AC3) — all-or-nothing (NIKAD partial-accept):** clean iterira fajlove, broji (> 3 → `ValidationError`); per fajl poziva `validate_image_mime(f, allowed_mimes=("image/jpeg","image/png"), max_size_bytes=5*1024*1024)` (REUSE 2.3 util — NE re-implementirati MIME/Pillow check). **Na PRVOM nevalidnom fajlu clean PROPAGIRA `ValidationError` (cela forma postaje invalid — `is_valid()` False) → NIJEDAN Lead/LeadAttachment se NE kreira (ni za validne fajlove iz istog batch-a).** `validate_image_mime` već raise-uje — Dev je NE sme uhvatiti-i-nastaviti niti filtrirati-i-vratiti-samo-validne. Tek ako su SVI fajlovi validni, clean vraća punu validiranu listu (svi fajlovi prošli). **NEMA partial-accept putanje** (vidi AC3/AC7 mixed-batch). Util-ova size poruka već sadrži konkretan limit (5 MB) jer prosleđujemo `5*1024*1024`; ako epics.md tačan string („Slika je veća od 5 MB. Probajte manju.") je obavezan, Dev hvata `ValidationError` iz utila SAMO da re-raise-uje sa tim stringom (i dalje raise — NE swallow). Test asertuje samo substring „5 MB" + „3 slike".
- **SM-D5 (email attach — JEDINA notifications.py izmena):** `send_lead_email` proširuje se da attach-uje `lead.attachments.all()` slike PRE `message.send()` (epics.md:818). Potpis NETAKNUT (`-> bool`); C1 failure contract (try/except provider send) NETAKNUT. Lead BEZ attachment-a (kontakt/model_inquiry/part_request/service-bez-slika) → prazan queryset → no-op (regression: postojeći 4.1/4.2/4.3 email-ovi rade identično). FieldFile čitanje kroz **context manager** (handle-safe): `with attachment.file.open("rb") as f: content = f.read()` (NE bare open/read/close — sprečava leak na grešci) + `message.attach(name, content, mimetype)`; **mimetype sa fallback-om:** `mimetypes.guess_type(name)[0] or "application/octet-stream"` (`guess_type` može vratiti `None`; fallback sprečava part bez Content-Type). Default jpeg/png su jedini mogući jer forma odbija ostalo.
- **SM-D6 (recipient NETAKNUT):** `_resolve_recipient` VEĆ mapira `SERVICE_REQUEST → SERVICE_EMAIL_TO` (4.1 `:48-49`). Dev NE menja recipient logiku. (Za razliku od potencijalne potrebe — ovde je VEĆ tačno.)
- **SM-D7 (subject NETAKNUT — RAZLIKA od 4.3):** `_build_subject` SERVICE_REQUEST grana (`:35-36`) VEĆ vraća „[Ćorić Agrar] Novi servisni zahtev: %(name)s" % {"name": lead.name} — TAČNO per epics.md (servisni subject koristi IME OSOBE, NE naziv proizvoda; servis nema product context). **Za razliku od 4.3** (gde je MODEL_INQUIRY morao da pređe sa `lead.name` na `lead.data["product_name"]`), **SERVICE_REQUEST NE zahteva izmenu** — `lead.name` je ispravan izvor. Dakle 4.4 NE menja `_build_subject`. (Ovo je eksplicitno provereno protiv epics.md:818 koji ne specifikuje drugačiji subject.)
- **SM-D8 (CACHES NE re-add):** `config/settings/base.py` VEĆ ima locmem `CACHES` (4.2 / SM-D10). 4.4 NE re-add. Test REUSE autouse `_pin_and_clear_ratelimit_cache`.
- **SM-D9 (phone OBAVEZAN na servisnoj formi — RAZLIKA od ContactForm):** epics.md:814 „Telefon *" (zvezdica = obavezno) na servisnoj formi, dok je na opštoj kontakt formi (4.2) telefon opciono. `ServiceRequestForm.phone` je `required=True` (Stojan očekuje poziv nazad — telefon je primarni kanal). `email` je OPCIONO (epics.md:814 bez zvezdice). `Lead.phone` model polje ostaje `blank=True` (model je deljen storage; forma je validacioni SOT — mirror 4.2 message razlike). **Napomena (email prazno perzistira):** `Lead.objects.create(email="")` se uredno čuva jer `objects.create()` zaobilazi model `full_clean()` (Lead je storage; forma je validacioni SOT — mirror 4.2). NEMA promene modela; ovo je uspostavljen pattern, NE bug.
- **SM-D10 (REUSE 4.2/4.3 1:1):** ratelimit `block=False`→429, dve a11y regije (in-form assertive + OOB polite guarded), partials u `templates/forms/partials/`, save-before-send, gettext + pune dijakritike, CSRF, `htmx-indicator` min 200ms, sirov-`<input>` None-safe idiom — sve REUSE. 4.4 NE uvodi novi pattern OSIM file-upload specifičnosti (multipart enctype + `hx-encoding` + `validate_image_mime` + `LeadAttachment`). Story 4.6 standardizuje shared mixin/decorator (NE sada — YAGNI).
- **SM-D11 (telefon za hitne pozive + page copy izvor):** AC11/success traže hitni `tel:` CTA + page copy. Default: **hardkodovan-translatable placeholder** (`{% translate %}` + `tel:` link) sa TODO ka SiteSettings (3-4 model postoji; dinamičko vezivanje = 8-9). Dev SME upotrebiti `{% site_setting "phone" %}` ako je već dostupan na strani (dokumentovati). Default = hardkodovan-translatable da 4.4 NE blokira (YAGNI; mirror 4.3 SM-D9).
- **SM-D12 (`/servis/` strana u `pages`, NE `forms`):** Servisna podrška strana (FR-22) je statička support strana → živi u `apps/pages` (mirror `ContactView` 3.3). `forms` app vlasnik je SAMO render-a forme (fields partial) + submit endpoint-a; `pages` mount-uje formu kroz container partial (mirror `_contact_form.html`). Razlog: `forms` je samostalan app bez „strana" (samo HTMX endpoint-i); page-rendering CBV-ovi žive u `pages` (koji SME importovati domain/forms render). `ServiceView` je GET-only TemplateView (POST → forms endpoint, NE page view).
- **SM-D13 (NEMA cross-app product import u 4.4):** Za razliku od 4.3 (koji importuje `Product` za model-inquiry re-validaciju), servisna forma NEMA product context (`brand_model` je free text, NE FK/slug). `service_request_submit` NE importuje `apps.products`. Dep boundary forms→core (+ media_pipeline util) only.
- **SM-D14 (GDPR PII + slike):** Servisni lead skladišti PII (`name`/`phone`/`email`/`ip_address`) + **slike kvara** (potencijalno lokacijski/lični metapodaci u EXIF-u). Data-retencija, right-to-erasure, EXIF-stripping = Epic 7 (GDPR & Privacy). 4.4 SAMO uvodi durabilno skladište (Lead + LeadAttachment); CASCADE FK omogućava da Epic 7 erasure obriše slike sa lead-om. EXIF-stripping NIJE scope 4.4 (forward → Epic 7 ILI media_pipeline post-process). Flag-ovano kao OQ-3.
- **SM-D15 (media storage — local dev, validate-before-save):** Slike se čuvaju kroz Django `FileField` u `MEDIA_ROOT` (local dev / Docker volume staging-prod — AR-28, no S3 v1). Validacija (MIME+Pillow+size+count) se dešava u `form.clean_photos` PRE `LeadAttachment.objects.create` → **nevalidan fajl NIKAD ne dotakne disk kao attachment** (forma odbija pre view save-a; epics.md:816 „greška PRE slanja"). Nginx servira media (AR-13); attachment-i NISU javno linkovani (samo admin pristup kroz LeadAdmin inline).

## Open Questions

- **OQ-1 (SM-D4 multi-file idiom) — SUŽENO/REŠENO:** Multi-file idiom je sada pinovan u SM-D4 + Task 8.1 (kanonski Django 5.x `MultipleFileInput`/`MultipleFileField`, NE `MultipleHiddenInput`) + literalni test-client multi-file idiom u Task 3.1 (`"photos": [f1, f2]` lista → `getlist` putanja). All-or-nothing semantika pinovana u AC3/AC7/SM-D4/Task 8.2 (NIKAD partial-accept). Test asertuje ponašanje (do 3, MIME/size, mixed-batch), NE konkretnu klasu. Ambiguitet zatvoren; ostaje samo finalna implementaciona sloboda u izboru ekvivalentne klase.
- **OQ-2 (SM-D4 size error string) — SUŽENO:** util-ova poruka (sadrži konkretan limit „5 MB") je default; test asertuje samo substring „5 MB". `oversized_image` fixture tehnika je sada pinovana u Task 1.1 (validna mala JPEG sa naduvanim `.size` — NE sirov `BytesIO` zeroes, koji bi pao na pogrešnoj grani). Ako biznis traži tačan epics string, Dev re-raise (trivijalno; i dalje raise — NE swallow). Ostaje otvoreno samo pitanje biznis-zahteva za TAČAN string (default: ne).
- **OQ-3 (SM-D14 EXIF/GDPR):** slike kvara mogu nositi EXIF GPS/lične metapodatke. EXIF-stripping + retencija = Epic 7. Da li 4.4 treba minimalan EXIF-strip pri save-u (Pillow `image.getdata()` re-save bez EXIF)? Default: NE (Epic 7 scope; YAGNI za v1). Flag za Epic 7 planiranje.
- **OQ-4 (SM-D11 telefon izvor):** hitni `tel:` CTA — hardkodovan-translatable placeholder vs `{% site_setting "phone" %}` (3-4). Default: hardkodovan-translatable + TODO (NE blokira na SiteSettings wiring-u). Dev SME upotrebiti `site_setting` ako je dostupan.
- **OQ-5 (Task 12.3 nav wiring):** da li header nav VEĆ ima „Servis" placeholder slot (7b1464f TODO marker) koji 4.4 treba da wire-uje na `pages:service`? Dev proverava `templates/partials/header.html`; ako postoji slot → wire; ako ne → NE dodavati (nav admin = Epic 8.9). Step-02 može potvrditi.
- **OQ-6 (`recipient_env` SERVICE_EMAIL_TO):** postojeći `recipient_env` fixture (4.1 conftest) VEĆ postavlja `SERVICE_EMAIL_TO="servis@coricagrar.rs"` — service testovi REUSE direktno (NEMA novog recipient fixture-a). Potvrđeno čitanjem conftest-a; zatvoreno.
