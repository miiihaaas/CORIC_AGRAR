---
story-id: 4-5-rezervni-delovi-form
epic: 4
title: "Rezervni Delovi Form"
status: ready-for-dev
module: forms
base-branch: master
created: 2026-06-04
author: SM (Scrum Master, 📋)
complexity: H
depends-on:
  - 4-1-lead-model-smtp-setup            # Lead model (FormType.PART_REQUEST VEĆ postoji) + send_lead_email + LeadAttachment model (4-4) + _resolve_recipient PART_REQUEST→PARTS_EMAIL_TO VEĆ mapiran (DONE)
  - 4-2-opsta-kontakt-forma-fr-5         # kanonski HTMX form pattern (ratelimit block=False→429, OOB aria-live, partials, save-before-send, locmem CACHES, conftest) (DONE)
  - 4-3-model-inquiry-form-sa-auto-popunjenim-modelom   # drugi HTMX form precedent; subject-iz-data precedent (_build_subject MODEL_INQUIRY izmena — MIRROR za PART_REQUEST subject) (DONE)
  - 4-4-servisni-zahtev-form-sa-foto-upload-om   # file-upload mašinerija: LeadAttachment model (VEĆ postoji — REUSE, NEMA nove migracije), clean_photos all-or-nothing + validate_image_mime, send_lead_email attach-loop, ServiceView/pages-page mount, LeadAttachmentInline (DONE)
  - 2-3-image-pipeline-sa-sorl-thumbnail-responsive-srcset   # apps/media_pipeline/utils.py:validate_image_mime (MIME signature + Pillow verify + size) — REUSE (DONE)
  - 3-3-kontakt-strana-sa-formom-i-mapom # ContactView/pages-page precedent (dedikovana strana mount + container partial) (DONE)
forward-dep:
  - 4-6-htmx-form-patterns-aria-live-oob-rate-limiting   # standardizuje HTMX/ratelimit pattern (shared mixin/decorator) kroz forme 4.2-4.5
---

# Story 4.5 — Rezervni Delovi Form

## Opis / Description

As a **kupac**, I want **da poručim rezervni deo preko forme sa detaljima i opcijama plaćanja i preuzimanja**, so that **dobijam tačnu ponudu bez telefoniranja i ponavljanja**.

Ovo je **ČETVRTA (poslednja sadržajna) forma story** Epic 4 i **DRUGA forma sa file/foto upload-om** (posle 4.4 servisne). Story 4.1 (Lead model + `send_lead_email`), 4.2 (kanonski HTMX form pattern), 4.3 (subject-iz-`data` precedent), i 4.4 (file-upload mašinerija: `LeadAttachment` + `clean_photos` all-or-nothing + email attach-loop + `pages` strana mount) su DONE i čine kompletan temelj. 4.5 **REUSE-uje sve postojeće obrasce 1:1** i ne uvodi NIJEDAN novi pattern — samo nove forme/view/partials/stranu + **JEDNU izmenu `_build_subject`**.

Forma se renderuje na **NOVOJ `/servis/rezervni-delovi/` strani** (FR-23 „Stranica Rezervni delovi sa formom") koju ova story kreira u `apps/pages` (mirror `ServiceView` iz 4.4). Polja (epics.md:829): **Model traktora\***, **Rezervni deo\***, **Dodatni opis** (opc.), **Slika** (opc., **max 1**), **Ime\***, **Telefon\***, **E-pošta\***, **Način plaćanja\*** (dropdown: pouzeće / predračun), **Način preuzimanja\*** (dropdown: dostava / lično), **Napomena** (opc.). Submit ide preko HTMX (`hx-post` na `forms:part_request_submit` → `/sr/htmx/forme/rezervni-delovi/`). Lead se perzistira sa `form_type='part_request'`, svi form-specific podaci u `Lead.data` JSON (epics.md:830 „svi specifični podaci u Lead.data JSON"), a opciona slika kroz **postojeći `LeadAttachment` child model** (4.4 — REUSE, **NEMA nove migracije za model**). Posle save-a, `send_lead_email(lead)` (4.4 attach-loop VEĆ attach-uje `lead.attachments`) šalje email na `PARTS_EMAIL_TO`.

**Email subject (epics.md:831): „[Ćorić Agrar] Upit za rezervni deo: {part_name} ({tractor_model})".** Ovo je RAZLIKA od trenutne implementacije — `_build_subject` PART_REQUEST grana trenutno vraća `lead.name` (4.1 placeholder); **ova story je menja da gradi subject iz `lead.data["part_name"]` i `lead.data["tractor_model"]`** (MIRROR 4.3 MODEL_INQUIRY izmene gde je subject prešao sa `lead.name` na `lead.data["product_name"]`). Vidi SM-D5.

**Granica scope-a (KRITIČNO):**
- **`Lead.FormType.PART_REQUEST = "part_request"` VEĆ POSTOJI** (`apps/forms/models.py:35`, iz 4.1). **NEMA promene `Lead` modela, NEMA FormType member dodatka.**
- **`LeadAttachment` model VEĆ POSTOJI** (`apps/forms/models.py:68`, iz 4.4 migracija `0002`). **NEMA nove migracije za model** (4.5 REUSE postojeći `LeadAttachment` za max-1 sliku). **0 migracija u 4.5.**
- **`_resolve_recipient` VEĆ mapira** `PART_REQUEST → PARTS_EMAIL_TO` (`notifications.py:52-53`) — **NE menja se** (SM-D6).
- **`_build_subject` PART_REQUEST grana SE MENJA** (`notifications.py:39-40`) — sa `lead.name` na `part_name (tractor_model)` iz `lead.data` (SM-D5). Ovo je JEDINA `notifications.py` izmena; `send_lead_email` potpis NETAKNUT, C1 failure contract NETAKNUT, attach-loop (4.4) NETAKNUT.
- **NE menja** `ContactForm`/`ModelInquiryForm`/`ServiceRequestForm` ni postojeće view-ove/partials (4.2/4.3/4.4 vlasništvo). DODAJE `PartRequestForm` + `part_request_submit` + nove partial-e + `/servis/rezervni-delovi/` stranu + `PartRequestView`.
- **Story 4.6** kasnije standardizuje HTMX form pattern (reusable mixin/decorator) + ujednačava rate-limit. 4.5 implementira ratelimit + OOB aria-live **inline** (per project-context.md security/a11y must-have); **NE** graditi prerano apstrakciju (YAGNI).
- **`PartRequest` zaseban model = NE.** epics.md (AUTHORITATIVE) koristi JEDAN `Lead` + `form_type` discriminator + `data` JSON (4.1 SM-D3). Slika ide kroz postojeći `LeadAttachment`.
- **Product/part referenca = NE FK, NE slug, NEMA cross-app import.** „Model traktora" i „Rezervni deo" su **free text** (kao 4.4 `brand_model`) — kupac upisuje proizvoljan model/deo. `part_request_submit` **NE importuje `apps.products`** (za razliku od 4.3). Dep boundary forms→core (+ media_pipeline util) only. Vidi SM-D7.

---

## Kontekst iz postojećeg koda (REAL reference — istraženo, NE pretpostavke)

> **Napomena o brojevima linija:** `fajl:NN` ref-ovi su INDIKATIVNI (orijentiši se po imenu simbola, ne po tačnom broju linije).

### Lead model (`apps/forms/models.py` — Story 4.1, NETAKNUT)
- `Lead(TimestampedModel)`; **`FormType.PART_REQUEST = "part_request"` VEĆ deklarisan** (`:35`, DB vrednost LOWERCASE, LOCKED). Label „Upit za rezervni deo".
- Polja: `form_type`, `name` (CharField 200, obavezno), `email` (EmailField), `phone` (CharField 50, **`blank=True` na modelu**), `message` (TextField, blank=True), `data` (JSONField default=dict), `ip_address`, `locale`. **NEMA `photo`, NEMA FK, NEMA `get_absolute_url`.**
- **`data` shape za `part_request` (DEFINIŠE OVA STORY — vidi SM-D2):** `{"tractor_model": "<free text>", "part_name": "<free text>", "extra_description": "<opc>", "payment_method": "<choice>", "delivery_method": "<choice>"}`. „Napomena" (opc.) ide u `Lead.message` (core polje, semantički „glavna poruka" leada — mirror 4.4 gde `description`→`message`). `name`/`phone`/`email` su core Lead polja.

### LeadAttachment model (`apps/forms/models.py` — Story 4.4, VEĆ POSTOJI — REUSE)
- `class LeadAttachment(models.Model)` (`:68`): `lead = FK(Lead, on_delete=CASCADE, related_name="attachments")`, `file = FileField(upload_to="leads/attachments/%Y/%m/")`. NE nasleđuje `TimestampedModel`. `Meta.verbose_name=_("Prilog")`/`_plural=_("Prilozi")`.
- **REUSE 1:1** — max-1 slika u 4.5 je samo `lead.attachments.count() <= 1` (1 `LeadAttachment` red ili 0). **NEMA nove migracije za model** (`0002` iz 4.4 već kreirala `LeadAttachment`).

### Email servis (`apps/forms/notifications.py` — Story 4.1/4.4) — ⚠️ JEDNA IZMENA (subject)
- `def send_lead_email(lead) -> bool` — SYNC, VIEW-CALLED, save-before-send. **Potpis NETAKNUT.**
- `_resolve_recipient` (`:48`) **VEĆ mapira** `PART_REQUEST → PARTS_EMAIL_TO` (`:52-53`) — **Dev NE menja recipient logiku** (SM-D6).
- `_build_subject` (`:36`) za `PART_REQUEST` (`:39-40`) **trenutno vraća** „[Ćorić Agrar] Upit za rezervni deo: %(name)s" % {"name": lead.name}. **⚠️ EPICS.md:831 traži „{part_name} ({tractor_model})" — NE `name`.** Ova story menja PART_REQUEST granu da vraća subject iz `lead.data` (MIRROR MODEL_INQUIRY grane `:41-44` koja koristi `lead.data.get("product_name", lead.name)`). Vidi SM-D5 + AC5.
- Attach-loop (4.4 SM-D5, `:101-106`) iterira `lead.attachments.all()` PRE `message.send()` — **VEĆ attach-uje slike za BILO KOJI lead sa attachment-ima** → part-request lead sa 1 slikom automatski dobija attach (NEMA izmene attach-loop-a; samo subject). Lead bez slike → prazan queryset → no-op.
- Telo iz `templates/emails/lead_received.html` (4.1) — multipart `EmailMultiAlternatives`. Provider-send u try/except (C1 NETAKNUT).

### HTMX form pattern (`apps/forms/{forms,views,urls}.py` + `templates/forms/partials/` — Story 4.2/4.3/4.4, REUSE 1:1)
- `apps/forms/forms.py` → `ContactForm`/`ModelInquiryForm`/`ServiceRequestForm` (`forms.Form`); labele/error kroz `gettext_lazy`, HTML5 widget atributi. **`ServiceRequestForm` je NAJBLIŽI šablon za `PartRequestForm`** (ima `ChoiceField` dropdown `machine_type` + multi-file `photos` + `clean_photos`). 4.5 dodaje DVA `ChoiceField`-a (`payment_method`, `delivery_method`) + free-text polja + **single-file `photo`** (NE multi — vidi SM-D4).
- `MultipleFileInput`/`MultipleFileField` (4.4, `:154-167`) postoje za MULTI-file — **4.5 NE koristi** (max 1 slika → stock `forms.ImageField`/`FileField` single; vidi SM-D4).
- `apps/forms/views.py` → `service_request_submit` FBV (4.4, `:107-140`): `@require_POST` + `@ratelimit(key="ip", rate="5/m", block=False)`; top `if getattr(request,"limited",False): return HttpResponse(status=429)`; bind `Form(request.POST, request.FILES)`; invalid → error partial (200); valid → `with transaction.atomic(): Lead.objects.create(...) + LeadAttachment loop`; `send_lead_email(lead)` IZVAN atomic; success partial. **REUSE 1:1 struktura za `part_request_submit`** (uz single-file persist — 0 ili 1 `LeadAttachment`).
- `apps/forms/urls.py` → `app_name="forms"`; `htmx/forme/kontakt/`, `htmx/forme/upit-za-model/`, `htmx/forme/servis/`. **Dodati** `path("htmx/forme/rezervni-delovi/", views.part_request_submit, name="part_request_submit")`.
- `config/urls.py` → `apps.forms.urls` VEĆ mount-ovan u `i18n_patterns`. **NEMA promene config/urls.py.**
- `templates/forms/partials/_service_request_form_fields.html` (4.4) → SIROVI `<input>`/`<select>`/`<textarea>` + `value="{{ form.X.value|default:'' }}"` idiom (None-safe za GET bez bound form); ROOT `<section id="...">` swap target; `enctype="multipart/form-data"` + `hx-encoding="multipart/form-data"`; in-form `role="alert"`/`aria-live="assertive"` error summary (regija #1); `{% csrf_token %}` + `hx-post`/`hx-target`/`hx-swap="outerHTML"`/`htmx-indicator`; ODVOJEN `{% if request.htmx and form.errors %}` OOB polite blok (regija #2). **NAJBLIŽI šablon za `_part_request_form_fields.html`** (2 dropdown-a umesto 1, single file input).
- `templates/forms/partials/service_request_success.html` (4.4) → ROOT `<section id="...">` čisto zamenjuje formu (`hx-swap="outerHTML"`); zahvalnost + `tel:` hitni-pozivi CTA; `{% if request.htmx %}` OOB polite najava. **Šablon za `part_request_success.html`.**
- `apps/forms/tests/conftest.py` → REUSE `recipient_env` (postavlja **`PARTS_EMAIL_TO="delovi@coricagrar.rs"`** — `:70`, VEĆ TU), `htmx_post` (fiksan `ip="203.0.113.7"`, `HTTP_HX_REQUEST="true"`), `superuser`, autouse `_pin_and_clear_ratelimit_cache` (locmem CACHES + `cache.clear()`), autouse `_isolate_media_root` (per-test `tmp_path` MEDIA_ROOT — KRITIČNO za file-upload testove, REUSE 4.4), `valid_image_jpeg`/`valid_image_png`/`oversized_image`/`oversized_image_real`/`non_image_file` (4.4 Pillow in-memory fixture-i — REUSE za part-request foto testove). **PROŠIRITI** sa `part_request_payload` + `part_request_submit_url`.
- `config/settings/base.py` → `CACHES` (locmem) VEĆ dodat (4.2). **NE re-add** (SM-D8). `PARTS_EMAIL_TO` VEĆ čitan iz env (4.1).

### File-upload double-check (`apps/media_pipeline/utils.py` — Story 2.3, REUSE)
- `validate_image_mime(upload, *, allowed_mimes=ALLOWED_IMAGE_MIME_TYPES, max_size_bytes=MAX_UPLOAD_SIZE_BYTES) -> None` — raise-uje `ValidationError` (locale-aware) ako: prazan upload, > size limit, MIME signature van `allowed_mimes`, ILI Pillow `verify()` padne. Resetuje `upload.seek(0)`. **REUSE u `PartRequestForm.clean_photo`** — pozovi `validate_image_mime(photo, allowed_mimes=("image/jpeg","image/png"), max_size_bytes=5*1024*1024)`. (epics.md ne navodi eksplicitan limit za 4.5 sliku; **MIRROR 4.4: JPG/PNG, 5 MB** — konzistentnost forme, SM-D4.)
- `MAX_UPLOAD_SIZE_BYTES` default je 10 MB; ova story prosleđuje EKSPLICITAN `5*1024*1024`. `ALLOWED_IMAGE_MIME_TYPES` uključuje webp; ova story prosleđuje EKSPLICITAN `("image/jpeg","image/png")`.

### Dedikovana strana mount (`apps/pages` — Story 4.4 `ServiceView` precedent)
- `apps/pages/views.py` → `ServiceView(TemplateView)` (4.4, `:133`), `template_name="pages/service.html"`, **`http_method_names=["get","head","options"]`** (POST → 405; submit ide na ZASEBAN `apps/forms` endpoint). **MIRROR za `PartRequestView`.**
- `apps/pages/urls.py` → `app_name="pages"`; `servis/` → `pages:service` (`:13`). **Dodati** `servis/rezervni-delovi/` → `pages:part_request` (NESTED pod servis prefiksom — epics.md:828 `/sr/servis/rezervni-delovi/`).
- `templates/pages/service.html` (4.4) → naslov + intro + `tel:` CTA + `{% include "pages/partials/_service_form.html" %}` (tanak container → `{% include "forms/partials/_service_request_form_fields.html" %}`). **MIRROR:** NOVI `templates/pages/part-request.html` + `templates/pages/partials/_part_request_form.html` container → `{% include "forms/partials/_part_request_form_fields.html" %}`.
- `apps` SME importovati domain/forms (pages SM-D6) — ali `PartRequestView` je čista TemplateView (NE agregira modele; choices žive na formi).

### CSS (REUSE — `static/css/components/contact-page.css`)
- `coric-contact-form__*` BEM (input/textarea/error/alert/success/submit/field/label/required/indicator) + `coric-service-form__file` (4.4) + `coric-model-inquiry__emergency`/`__emergency-link` (4.3 `tel:` CTA). **REUSE klase za rezervni-delovi formu**; novi `coric-` proširenje SAMO ako 2-dropdown/single-file layout traži (preferiraj reuse, YAGNI).

### Admin (`apps/forms/admin.py` — Story 4.1/4.4, NETAKNUT)
- `LeadAdmin` + `LeadAttachmentInline` (4.4) VEĆ prikazuju attachment-e za BILO KOJI lead. **part-request lead sa slikom automatski se prikazuje kroz postojeći inline** — **NEMA admin izmene u 4.5** (regression-only; vidi AC10).

---

## Acceptance Criteria

**AC1 — `PartRequestForm` (server-side validation SOT; free-text polja + 2 dropdown-a + single-file).**
**Given** Lead model (FormType.PART_REQUEST VEĆ postoji) + `validate_image_mime` (2.3) + `LeadAttachment` (4.4)
**When** kreiram `PartRequestForm` u `apps/forms/forms.py` (Django `forms.Form`) sa poljima (epics.md:829):
- `tractor_model` — CharField(max_length=200), **required=True** („Model traktora *")
- `part_name` — CharField(max_length=200), **required=True** („Rezervni deo *")
- `extra_description` — CharField(Textarea), **required=False** („Dodatni opis (opc.)")
- `photo` — single-file slika polje (SM-D4 — stock `forms.ImageField` ILI `FileField`, **NE** multi-file), **required=False** („Slika (opc., max 1)")
- `name` — CharField(max_length=200), **required=True** („Ime *")
- `phone` — CharField(max_length=50), **required=True** („Telefon *")
- `email` — EmailField, **required=True** („Email *" — zvezdica; **RAZLIKA od servisne forme** gde je email opciono; vidi SM-D3)
- `payment_method` — ChoiceField sa `choices` iz nested `PaymentMethod(TextChoices)` (vrednosti `cod`/`proforma`; labele „Pouzeće"/„Predračun" kroz `gettext_lazy`), **required=True** („Način plaćanja (dropdown: pouzeće / predračun)"), `widget=forms.Select`
- `delivery_method` — ChoiceField sa `choices` iz nested `DeliveryMethod(TextChoices)` (vrednosti `delivery`/`pickup`; labele „Dostava"/„Lično preuzimanje" kroz `gettext_lazy`), **required=True** („Način preuzimanja (dropdown: dostava / lično)"), `widget=forms.Select`
- `note` — CharField(Textarea), **required=False** („Napomena (opc.)")
**Then** sva user-facing labela/error poruka prolazi kroz `gettext_lazy` (pune dijakritike č/ć/ž/š/đ; „E-pošta", „Pouzeće", „Lično"; NIKAD ćirilica/šišana latinica)
**And** prazno `tractor_model`/`part_name`/`name`/`phone`/`email`/`payment_method`/`delivery_method` → `is_valid()` je `False` sa per-field greškama; nevalidan `payment_method`/`delivery_method` (van choices) → `False`; validan kompletan payload (sa ILI bez slike) → `True`
**And** opcioni `extra_description`/`photo`/`note` smeju biti prazni bez invalidacije forme.

**AC2 — Foto upload double-check (MIME signature + Pillow + size) u `clean_photo` (KRITIČNO — security must-have).**
**Given** `PartRequestForm` iz AC1 + `validate_image_mime` (2.3)
**When** forma primi sliku kroz `request.FILES["photo"]`
**Then** `clean_photo`:
- ako je `photo` prazno (opciono) → vraća `None`/prazno bez greške (NE poziva util na praznom)
- ako je `photo` prisutno → PRVO radi **sopstvenu strukturnu size pre-proveru** (`if photo and getattr(photo, "size", 0) > 5*1024*1024: raise ValidationError(_("Slika je veća od 5 MB. Probajte manju."))`) PRE poziva util-a (MIRROR 4.4 — `clean_photo` NE zavisi od util-ove poruke za konkretan „5 MB" string; buduća promena util/locale poruke ne sme tiho da izgubi konkretan limit), PA TEK ONDA pozove `validate_image_mime(photo, allowed_mimes=("image/jpeg", "image/png"), max_size_bytes=5*1024*1024)` — MIME signature (NE samo ekstenzija) + Pillow `verify()` (+ util-ova sopstvena size provera, belt-and-suspenders) (REUSE 2.3 util — NE re-implementirati)
- **Nedozvoljen tip** (PDF/GIF/corrupt/`<script>`-renamed-`.jpg`) → `ValidationError`; `Lead` se NE kreira
- **> 5 MB** → `ValidationError` sa konkretnim limitom (sopstvena strukturna provera obezbeđuje „5 MB"; util takođe sadrži „5 MB" jer prosleđujemo `5*1024*1024`); **TEST asertuje substring „5 MB"**
**And** **double-check je OBAVEZAN** (project-context.md anti-pattern „File upload bez double-check") — NIKAD oslanjanje samo na Django `FileField`/`ImageField` ekstenziju
**And** **max 1 slika (epics.md:829 „Slika (opc., max 1)"):** forma prima JEDNO `photo` polje (NE listu) → struktura forme garantuje max 1 (single `forms.FileField`, NE `MultipleFileField`); ako klijent pošalje više `photo` part-ova, server uzima jedan (Django `request.FILES["photo"]` semantika) — NE multi-file (SM-D4)
**And** validacija ne menja stanje (čist `clean` — save je u view-u posle `is_valid()`).

**AC3 — HTMX POST endpoint (multipart) + URL wiring.**
**Given** `PartRequestForm` iz AC1
**When** dodam `part_request_submit` FBV u `apps/forms/views.py` + `path("htmx/forme/rezervni-delovi/", views.part_request_submit, name="part_request_submit")` u `apps/forms/urls.py`
**Then** `reverse("forms:part_request_submit")` (uz aktivan `sr` locale) rezolvuje na `/sr/htmx/forme/rezervni-delovi/` (i18n-prefiksovan; `config/urls.py` NETAKNUT)
**And** endpoint prihvata SAMO POST (GET → 405, `@require_POST`)
**And** view bind-uje formu sa **`PartRequestForm(request.POST, request.FILES)`** (multipart — fajl je u `request.FILES`)
**And** view radi save-before-send redosled UNUTAR `transaction.atomic()` (mirror 4.4): (1) `Lead.objects.create(form_type=Lead.FormType.PART_REQUEST, name=..., phone=..., email=..., message=form.cleaned_data["note"], locale=get_language(), ip_address=<REMOTE_ADDR>, data={"tractor_model":..., "part_name":..., "extra_description":..., "payment_method":..., "delivery_method":...})`; (2) ako je `photo` prisutno → `LeadAttachment.objects.create(lead=lead, file=photo)`; (3) `send_lead_email(lead)` IZVAN atomic bloka (email failure NE rollback-uje sačuvan lead — C1).
**And** **NEMA cross-app import-a** (`part_request_submit` NE importuje `apps.products` — model/deo su free text; SM-D7).

**AC4 — Uspešan submit (success partial + Lead + Lead.data + opciona slika + email).**
**Given** endpoint iz AC3 + `recipient_env` (`PARTS_EMAIL_TO` postavljen)
**When** pošaljem validan multipart POST sa svim obaveznim poljima (+ opciono `extra_description`/`note`/1 validna JPG/PNG slika)
**Then** kreira se TAČNO 1 `Lead` red sa `form_type == "part_request"`, `name`/`phone`/`email` iz payload-a, `message == <note>` (prazan note → `""`), `locale`, `ip_address` popunjen, i **`data == {"tractor_model": "...", "part_name": "...", "extra_description": "...", "payment_method": "<choice>", "delivery_method": "<choice>"}`** (SM-D2 shape — SVI ključevi PRISUTNI; prazan opcioni `extra_description` → `""`, NE izostavljen)
**And** ako je priložena slika → kreira se 1 `LeadAttachment` red (`lead.attachments.count() == 1`); fajl sačuvan pod `leads/attachments/...`
**And** view vraća success partial (`templates/forms/partials/part_request_success.html`) — forma se HTMX-swap-uje; response NIJE full HTML page
**And** `send_lead_email(lead)` je pozvan (1 email u `mailoutbox`); **subject je „[Ćorić Agrar] Upit za rezervni deo: {part_name} ({tractor_model})"** (iz `lead.data` — vidi AC5); `to == [settings.PARTS_EMAIL_TO]`; ako je priložena slika → **`len(mailoutbox[0].attachments) == 1`** (attach-loop 4.4 VEĆ attach-uje).

**AC5 — Email subject iz `lead.data` (⚠️ `_build_subject` PART_REQUEST grana SE MENJA — MIRROR 4.3).**
**Given** `notifications._build_subject` PART_REQUEST grana (4.1 — trenutno `lead.name`)
**When** izmenim PART_REQUEST granu da gradi subject iz `lead.data`
**Then** za `PART_REQUEST` lead: `subject == "[Ćorić Agrar] Upit za rezervni deo: %(part)s (%(model)s)" % {"part": lead.data.get("part_name", ...), "model": lead.data.get("tractor_model", ...)}` (puni dijakritik; runtime `gettext` lokalizovan po `lead.locale` — REUSE `translation.override` blok)
**And** subject sadrži ime DELA i model TRAKTORA iz `data` (NE `lead.name` — epics.md:831), npr. „[Ćorić Agrar] Upit za rezervni deo: Filter ulja (Agri Tracking TB804)"
**And** fallback ako `data` nema ključeve (defenzivno SAMO na boundary subject-build-a) je ZAKLJUČAN (RESOLVED OQ-6): `lead.data.get("part_name", lead.name)` (default na `lead.name`) i `lead.data.get("tractor_model", "")` (default prazan string) — TAČNO kao Task 9.1; tako prazni `data` lead NE crash-uje send i subject OSTAJE informativan (sadrži bar `lead.name`, NIKAD „...: ()"). Vidi SM-D5
**And** ostale grane (`KONTAKT`/`MODEL_INQUIRY`/`SERVICE_REQUEST`) `_build_subject` NETAKNUTE (regression — postojeći subject testovi 4.1/4.3/4.4 ostaju zeleni); `_resolve_recipient` PART_REQUEST → `PARTS_EMAIL_TO` NETAKNUT (SM-D6).

**AC6 — Submit BEZ slike (foto je opciono).**
**Given** endpoint iz AC3
**When** pošaljem validan POST BEZ slike (`photo` prazno)
**Then** `Lead` se kreira normalno (`form_type='part_request'`); `lead.attachments.count() == 0`; success partial; `len(mailoutbox) == 1`; `len(mailoutbox[0].attachments) == 0` (email bez priloga). Foto je opciono (epics.md:829) — odsustvo NE blokira submit.

**AC7 — Neuspešan submit (error rerender + dve a11y regije; nevalidan fajl PRE kreiranja Lead-a).**
**Given** endpoint iz AC3
**When** pošaljem nevalidan POST (prazno obavezno polje, ILI nevalidan `payment_method`/`delivery_method`, ILI slika > 5 MB, ILI ne-slika fajl)
**Then** view vraća form partial rerender (bound form sa `form.errors`), **HTTP 200** (NE 4xx — HTMX swap error UI)
**And** rerender sadrži **U-FORMI** `<div role="alert" aria-live="assertive">` error summary (regija #1) sa per-field greškama (REUSE 4.4 obrazac); za file greške poruka sadrži konkretan limit („5 MB")
**And** **NIJEDAN `Lead` red NIJE kreiran, NIJEDAN `LeadAttachment` NIJE kreiran, NIJEDAN email NIJE poslat** (`Lead.objects.count() == 0`, `LeadAttachment.objects.count() == 0`, `mailoutbox` prazan) — validacija (uključujući foto double-check) se dešava PRE `Lead.objects.create`
**And** rerender ČUVA tekstualna/select polja (`tractor_model`/`part_name`/`extra_description`/`name`/`phone`/`email`/`payment_method`/`delivery_method`/`note`) tako da korisnik ne gubi unos (file polje se NE može re-popuniti — browser security; prihvatljivo).

> **Dve ODVOJENE a11y regije (KRITIČNO — REUSE 4.2/4.4):** error odgovor MORA imati OBE: (1) **in-form** `role="alert"`/`aria-live="assertive"` summary UNUTAR form partial-a, I (2) **ODVOJEN** `hx-swap-oob="innerHTML:#aria-live"` blok ka `base.html` `aria-live="polite"` singletonu. Singleton OSTAJE `polite`. Success odgovor sadrži SAMO OOB polite najavu.

**AC8 — OOB aria-live announcement (HTMX a11y).**
**Given** HTMX response patterns (project-context.md:184-194; REUSE 4.2/4.3/4.4)
**When** success ILI error response se vrati na HTMX zahtev
**Then** response uključuje `hx-swap-oob="innerHTML:#aria-live"` element ciljajući `base.html` `{% aria_live %}` singleton sa kratkom porukom (success: „Upit za rezervni deo je poslat."; error: „Greška pri slanju, proverite polja.") kroz `{% translate %}`
**And** OOB blok je guarded `{% if request.htmx %}` (REUSE — ne curi u non-HTMX render).

**AC9 — Security must-haves (CSRF + ratelimit → HTTP 429; multipart; REUSE 4.2/4.4).**
**Given** project-context.md security must-have
**When** wire-ujem formu
**Then** form template sadrži `{% csrf_token %}` (HTMX šalje CSRF header); forma ima `enctype="multipart/form-data"` + `hx-encoding="multipart/form-data"` (HTMX file upload zahteva eksplicitan encoding)
**And** `part_request_submit` ima `@ratelimit(key="ip", rate="5/m", block=False)` — **EKSPLICITNO `block=False`** (NE `block=True` → 403; vidi 4.2 SM-D9)
**And** na VRHU tela (PRE bind-a forme i PRE `Lead.objects.create`): `if getattr(request, "limited", False): return HttpResponse(status=429)`
**And** 6. uzastopni submit sa istog IP-a u 1 minuti → **HTTP 429** (5 prvih prolazi, 6. blokiran)
**And** ratelimit koristi Django `default` cache (locmem `CACHES` VEĆ u `config/settings/base.py`; NE re-add); test pinuje cache + `cache.clear()` (REUSE autouse `_pin_and_clear_ratelimit_cache`).

**AC10 — NOVA `/servis/rezervni-delovi/` strana (FR-23) + mount forme (NE duplira ServiceView).**
**Given** `ServiceView` precedent (4.4) + `pages` app
**When** kreiram `PartRequestView` u `apps/pages/views.py` + `path("servis/rezervni-delovi/", PartRequestView.as_view(), name="part_request")` u `apps/pages/urls.py` + `templates/pages/part-request.html` + `templates/pages/partials/_part_request_form.html`
**Then** `reverse("pages:part_request")` (uz `sr`) → `/sr/servis/rezervni-delovi/` (epics.md:828); GET `/sr/servis/rezervni-delovi/` → **200** sa aktivnom (NE disabled) formom za rezervne delove
**And** `PartRequestView` je **GET-only** (`http_method_names=["get","head","options"]`) → POST na `pages:part_request` vraća **405** (submit ide na ZASEBAN `forms:part_request_submit`, NE na page view — mirror ServiceView/SM-D12)
**And** strana renderuje formu kroz container partial → `{% include "forms/partials/_part_request_form_fields.html" %}`; CSRF token prisutan u renderovanoj formi; `hx-post` ka `forms:part_request_submit`
**And** strana sadrži minimalan kontekst „Rezervni delovi" (naslov + kratak opis + forma) kroz `{% translate %}` (puni dijakritik); SiteSettings telefon/kontakt = hardkodovan-translatable placeholder + TODO (3-4/8-9 — NE blokira; SM-D11). **Hitni `tel:` pozivi CTA** (REUSE 4.3/4.4 `coric-model-inquiry__emergency`) kroz klikabilan `tel:` link.
**And** **NEMA admin izmene** — postojeći `LeadAdmin` + `LeadAttachmentInline` (4.1/4.4) automatski prikazuju part-request lead + njegovu sliku (regression-only; AC11 pokriva smoke).

**AC11 — Admin regression (part-request lead + slika kroz postojeći inline).**
**Given** `LeadAdmin` + `LeadAttachmentInline` (4.1/4.4, NETAKNUTI)
**When** part-request lead sa 1 `LeadAttachment` postoji
**Then** superuser GET `reverse("admin:forms_lead_changelist")` → 200; change-view part-request lead-a sa slikom → 200 (postojeći inline renderuje prilog); `form_type` filter prikazuje „Upit za rezervni deo" opciju.
**And** **NEMA izmene `apps/forms/admin.py`** (regression — inline je form-type-agnostičan).

**AC12 — i18n + dijakritike + lint.**
**Given** project-context.md i18n + anti-pattern pravila
**When** dodam sve nove stringove
**Then** SVE user-facing strings (labele, dropdown opcije „Pouzeće"/„Predračun"/„Dostava"/„Lično preuzimanje", error/success/aria poruke, page copy, subject delovi, telefon CTA) idu kroz `gettext_lazy`/`{% translate %}`/runtime `gettext` (subject) sa punim dijakritikama; NIKAD ćirilica, NIKAD šišana latinica
**And** novi `.po` msgid-ovi dodati i kompajlirani kroz `just messages` (makemessages + compilemessages za sr/hu/en); hu/en smeju ostati prazni (fallback sr — isto kao 4.1 AC9 / 4.3/4.4 politika)
**And** `just lint` (ruff + djade) clean; `just test` (novi forms + pages + notifications/email regresija) prolazi.

**AC13 — Mobile-responsive UX (parity sa 4.4 AC8; testabilno na nivou atributa/klasa).**
**Given** rezervni-delovi forma renderovana na `/servis/rezervni-delovi/` strani (mobile viewport)
**When** korisnik otvori formu na uređaju < 768px
**Then** file input dozvoljava izbor iz kamere/galerije: `<input type="file"` ima `accept="image/jpeg,image/png"` i **NEMA `multiple`** (max 1 — SM-D4)
**And** form polja se slažu u 1 kolonu na < 768px; submit dugme je full-width; `htmx-indicator` spinner vidljiv tokom upload-a (REUSE 4.4 responsive obrazac)
**And** layout kroz `var(--token)` (NEMA inline magic CSS — project-context.md anti-pattern; REUSE `coric-contact-form__*`/`coric-service-form__file` BEM)
**And** **testabilni deo (Task 5.2/5.3):** rendered HTML asertuje da `<input type="file"` ima `accept` i NEMA `multiple`, te da submit/sekcija koristi očekivane `coric-` BEM klase. **Čisto vizuelno/responsive CSS ponašanje (breakpoint stacking, full-width render) je VAN scope-a automatizovanog testa** — asertuje se na nivou prisustva klase/atributa, konzistentno sa projektnom CSS-testing strategijom iz 4.4.

---

## Tasks / Subtasks (TDD-ordered: TEA RED → Dev GREEN)

> **Disciplina (project-context.md:293-298):** TEA agent piše testove (RED phase) PRVI; Dev agent piše implementaciju (GREEN); **Dev NIKAD ne piše testove.** Testovi se commit-uju pre implementacije. Ako TEA testovi failuju u Dev fazi → story `paused`, ne maskirati greške.
>
> **Test konvencija (REUSE 4.2/4.3/4.4):** SVI part-request POST testovi koriste `htmx_post` fixture (fiksan IP `203.0.113.7`, `HTTP_HX_REQUEST="true"`) — NE sirov `client.post` (osim deliberate non-HTMX test). Multipart: prosledi fajl kao `SimpleUploadedFile` u `data` dict-u (Django test client auto-multipart). Image fixture-i kroz 4.4 Pillow in-memory (`valid_image_jpeg`/`oversized_image_real`/`non_image_file` — REUSE iz conftest-a). Email testovi REUSE `mailoutbox` + `recipient_env` (`PARTS_EMAIL_TO`). NIKAD pravi send. **0 migracija** (Lead + LeadAttachment VEĆ postoje).

### Task 1 — (TEA, RED) Fixtures
- [ ] 1.1 Proširi `apps/forms/tests/conftest.py` (REUSE `recipient_env`/`htmx_post`/`superuser`/autouse cache + media-root + 4.4 image fixtures) sa: `part_request_payload` (`{"tractor_model": "Agri Tracking TB804", "part_name": "Filter ulja", "extra_description": "Original deo.", "name": "Marko Marković", "phone": "+381641234567", "email": "marko@example.com", "payment_method": "cod", "delivery_method": "delivery", "note": "Pozovite popodne."}` — pun dijakritik); `part_request_submit_url` (`activate("sr")` + `reverse("forms:part_request_submit")`). **NE re-definisati** image fixture-e ni `recipient_env` (VEĆ postoje u conftest-u iz 4.1/4.4 — REUSE direktno).

### Task 2 — (TEA, RED) PartRequestForm validacija + foto double-check
- [ ] 2.1 `apps/forms/tests/test_part_request_form.py` (AC1): polja postoje (`tractor_model`/`part_name`/`extra_description`/`photo`/`name`/`phone`/`email`/`payment_method`/`delivery_method`/`note`); **obavezni:** `tractor_model`/`part_name`/`name`/`phone`/`email`/`payment_method`/`delivery_method`; **opcioni:** `extra_description`/`photo`/`note`; `payment_method` choices == {cod, proforma}; `delivery_method` choices == {delivery, pickup}; nevalidan `payment_method`/`delivery_method` → invalid; labele/error kroz gettext (substring pune dijakritike „E-pošta"/„Pouzeće"/„Lično"; NEMA ćirilice); validan payload (sa i bez slike) → valid. **Email OBAVEZAN** (prazan `email` → invalid — RAZLIKA od servisne forme; SM-D3).
- [ ] 2.2 `apps/forms/tests/test_part_request_photo_validation.py` (AC2 — KRITIČNO):
  - **0 slika** → valid (opciono; `clean_photo` vraća prazno bez poziva util-a).
  - **1 validna JPG/PNG** → valid.
  - **> 5 MB slika** (`oversized_image_real`) → `is_valid()` False; greška sadrži substring „5 MB".
  - **ne-slika fajl** (`non_image_file` — PDF) → False (MIME signature odbija); `Lead` se NE kreira.
  - **corrupt „slika"** (random bytes sa `image/jpeg` content_type, Pillow `verify()` padne) → False.
  - **webp odbijen** jer NIJE u `allowed_mimes` (pinovan na jpeg/png): `valid_image_webp` upload → False. **Napomena za Dev:** webp je STRUKTURNO validna slika koja PROLAZI MIME-signature proveru + Pillow `verify()` — odbija se ISKLJUČIVO jer nije u pinovanom skupu `("image/jpeg","image/png")` (allowed_mimes EXCLUSION). NE meša se sa Pillow/MIME-signature padom (corrupt/ne-slika test pokriva taj put).
  - **Asertuj da forma poziva `validate_image_mime` sa `allowed_mimes=("image/jpeg","image/png")` i `max_size_bytes=5*1024*1024`** (mock/spy ILI behavior assertion — webp se odbija jer NIJE u allowed; size „5 MB" deterministički vezan za `5*1024*1024`).

### Task 3 — (TEA, RED) HTMX endpoint: success + Lead.data + opciona slika + subject
- [ ] 3.1 `apps/forms/tests/test_part_request_view.py` (AC3/AC4):
  - `reverse("forms:part_request_submit")` rezolvuje pod `activate("sr")` → `/sr/htmx/forme/rezervni-delovi/` (RED dok URL ne postoji).
  - GET → 405.
  - **Success SA slikom:** validan HTMX multipart POST sa `{**part_request_payload, "photo": valid_image_jpeg}` → 200; `Lead.objects.count()==1`; `lead.form_type==Lead.FormType.PART_REQUEST`; `lead.name`/`lead.phone`/`lead.email` iz payload-a; `lead.message=="Pozovite popodne."` (note→message); `lead.data == {"tractor_model":"Agri Tracking TB804","part_name":"Filter ulja","extra_description":"Original deo.","payment_method":"cod","delivery_method":"delivery"}`; `lead.locale=="sr"`; `lead.ip_address` popunjen; `lead.attachments.count()==1`; success partial korišćen; `len(mailoutbox)==1`; `mailoutbox[0].to==[settings.PARTS_EMAIL_TO]`; `len(mailoutbox[0].attachments)==1`.
  - **Subject (AC5 — KRITIČNO):** `mailoutbox[0].subject` sadrži „[Ćorić Agrar] Upit za rezervni deo: Filter ulja (Agri Tracking TB804)" (iz `lead.data`, NE `lead.name`). Ovaj test forsira `_build_subject` izmenu.
- [ ] 3.2 (AC6) **Success BEZ slike:** validan POST bez `photo` → `Lead` kreiran; `lead.attachments.count()==0`; `len(mailoutbox)==1`; `len(mailoutbox[0].attachments)==0`. **Prazan opcioni-field data-shape (SM-D2 lock):** varijanta gde su `extra_description`/`note` izostavljeni/prazni → asertuj `lead.data["extra_description"]==""` (ključ PRISUTAN sa praznim stringom, NE izostavljen) i `lead.message==""`.
- [ ] 3.3 (AC4 partial): success response NIJE full page (NE sadrži `<html`/`<head>`). **Simetrično:** error response je takođe partial.
- [ ] 3.4 (AC5 subject — notifications.py direktan unit test): `Lead.objects.create(form_type=PART_REQUEST, data={"part_name":"Filter ulja","tractor_model":"Agri Tracking TB804"}, ...)` → `send_lead_email(lead)` (sa `recipient_env`) → `mailoutbox[0].subject` sadrži „Upit za rezervni deo: Filter ulja (Agri Tracking TB804)". **Fallback (OQ-6 RESOLVED):** part-request lead sa PRAZNIM `data` (`{}`) i postavljenim `name` (npr. „Marko Marković") → `send_lead_email` NE crash-uje I `mailoutbox[0].subject` SADRŽI `lead.name` (part_name default-uje na `lead.name`, tractor_model na `""`) — subject je smislen, NIKAD „...: ()" (SM-D5). **Regression:** postojeći `KONTAKT`/`MODEL_INQUIRY`/`SERVICE_REQUEST` subject testovi (4.1/4.3/4.4) ostaju zeleni (NE menjaju se te grane).

### Task 4 — (TEA, RED) Error rerender + dve a11y regije + OOB + ratelimit + email-failure
- [ ] 4.1 `apps/forms/tests/test_part_request_errors.py` (AC7): nevalidan POST (prazno `tractor_model` ILI `payment_method` van choices) → 200 (NE 4xx); `Lead.objects.count()==0`; `LeadAttachment.objects.count()==0`; `len(mailoutbox)==0`; rerender sadrži `role="alert"` + `aria-live="assertive"` + error tekst; rerender ČUVA tekstualna/select polja (`tractor_model`/`part_name`/`payment_method`/`delivery_method` value-i prisutni). **File-reject PRE Lead-a:** POST sa >5MB slikom (`oversized_image_real`) → 0 Lead, 0 attachment, 0 email, error „5 MB"; POST sa ne-slikom (`non_image_file`) → 0 Lead, error prisutan.
- [ ] 4.2 `apps/forms/tests/test_part_request_aria_live.py` (AC8 + AC7 dve regije): success response → `hx-swap-oob="innerHTML:#aria-live"` + „Upit za rezervni deo je poslat." (SAMO OOB polite); error response → OBE regije (in-form assertive + ODVOJEN OOB polite „Greška pri slanju, proverite polja."); OOB guarded `{% if request.htmx %}` (non-HTMX POST → NEMA `hx-swap-oob`); singleton ostaje `polite`.
- [ ] 4.3 `apps/forms/tests/test_part_request_xss.py` (AC7 XSS — javna unauth forma; auto-escape u OBA konteksta): **(1) ERROR partial:** nevalidan POST (npr. nedostaje obavezni `payment_method`) SA `<script>alert(1)</script>` u `tractor_model`/`name` → error rerender auto-escape (`&lt;script&gt;`, NIKAD sirov `<script>`). **(2) SUCCESS partial:** ako success echo-uje uneto polje → escape-ovano. Asertuj odsustvo sirovog `<script>` u OBA slučaja.
- [ ] 4.4 `apps/forms/tests/test_part_request_email_failure.py` (4.2/4.4 SM-D5 obrazac): `mock.patch` na `apps.forms.views.send_lead_email` → `False`; validan submit → Lead i (opc.) attachment i dalje postoje (count-ovi tačni); posetilac i dalje dobija success partial. (Mock SAMO servis-povratnu vrednost, NE ORM.)
- [ ] 4.5 `apps/forms/tests/test_part_request_ratelimit.py` (AC9): 5 submit-a OK; 6. submit sa istog IP-a u istom minutu → `status_code==429` (NE 403). REUSE autouse `_pin_and_clear_ratelimit_cache` + `htmx_post`.

### Task 5 — (TEA, RED) `/servis/rezervni-delovi/` strana + mount (a11y/regression)
- [ ] 5.1 `apps/pages/tests/test_part_request_url.py` (AC10): `reverse("pages:part_request")` pod `sr` → `/sr/servis/rezervni-delovi/`; GET → 200; POST na `pages:part_request` → **405** (GET-only); template `pages/part-request.html` korišćen.
- [ ] 5.2 `apps/pages/tests/test_part_request_form_wired.py` (AC10): plain `client.get("/sr/servis/rezervni-delovi/")` → 200; renderovana strana sadrži formu (NEMA `disabled` na poljima/submit-u); `hx-post` ka `forms:part_request_submit`; `enctype="multipart/form-data"`; `<input type="file"` (NEMA `multiple` — max 1; SM-D4) sa `accept`; oba `<select>` (`payment_method`/`delivery_method`) sa svim opcijama; **CSRF token prisutan** (`csrfmiddlewaretoken`); `tel:` hitni-pozivi CTA prisutan. (Forma se renderuje BEZ bound `form` na GET — `PartRequestView` je TemplateView; partial mora biti None-safe — sirov-`<input>` idiom mirror 4.4.)
- [ ] 5.3 `apps/pages/tests/test_part_request_mobile_ux.py` (AC13 — parity sa 4.4 AC8): u renderovanom HTML-u (`client.get("/sr/servis/rezervni-delovi/")` → 200) asertuj testabilne delove mobile UX-a: `<input type="file"` ima `accept` (kamera/galerija na mobilnom) i **NE sadrži `multiple`** (max 1; SM-D4); submit/sekcija koristi očekivane `coric-` BEM klase (npr. `coric-contact-form__submit`/`coric-contact-form__indicator`/`coric-service-form__file` — REUSE 4.4); `htmx-indicator` klasa prisutna. **Napomena:** čisto vizuelno/responsive ponašanje (breakpoint stacking < 768px, full-width render) se asertuje SAMO na nivou prisustva klase/atributa — vizuelni CSS render je VAN scope-a automatizovanog testa, konzistentno sa projektnom CSS-testing strategijom iz 4.4.

### Task 6 — (TEA, RED) Admin regression
- [ ] 6.1 `apps/forms/tests/test_part_request_admin.py` (AC11): part-request `Lead` + 1 `LeadAttachment` → superuser GET `reverse("admin:forms_lead_changelist")` → 200; change-view tog lead-a → 200 (postojeći inline prikazuje prilog). (Regression — `apps/forms/admin.py` NETAKNUT; postojeći 4.1/4.4 admin smoke ostaju zeleni.)

### Task 7 — (Dev, GREEN) `PartRequestForm` + foto double-check
- [x] 7.1 Dodaj `PartRequestForm(forms.Form)` u `apps/forms/forms.py` (NE diraj `ContactForm`/`ModelInquiryForm`/`ServiceRequestForm`): `tractor_model`/`part_name`/`name`/`phone`/`email`/`payment_method`/`delivery_method` obavezni; `extra_description`/`photo`/`note` opcioni; `payment_method` ChoiceField + nested `PaymentMethod(TextChoices)` (`cod`/`proforma`; labele „Pouzeće"/„Predračun" kroz `gettext_lazy`); `delivery_method` ChoiceField + nested `DeliveryMethod(TextChoices)` (`delivery`/`pickup`; labele „Dostava"/„Lično preuzimanje"); `photo` = **stock single-file `forms.FileField`** (PREPORUKA — RESOLVED OQ-1; NE `forms.ImageField` jer `ImageField` poziva Pillow u `to_python()` što duplira i može da poremeti `seek()` poziciju koju `validate_image_mime` interno koristi — `validate_image_mime` u `clean_photo` je JEDINI autoritativni gate), **NE** `MultipleFileField` — SM-D4. Labele/error kroz `gettext_lazy` (pune dijakritike). HTML5 widget atributi (`type=tel`, `type=email`, `required`, `accept`) = UX sloj; widget `id` konvencija `part-<field>` (mirror `contact-`/`service-`).
- [x] 7.2 `clean_photo`: ako je `photo` prazno → vrati ga (None/prazno) bez poziva util-a; ako prisutno → PRVO **sopstvena strukturna size pre-provera** (`if photo and getattr(photo, "size", 0) > 5*1024*1024: raise ValidationError(_("Slika je veća od 5 MB. Probajte manju."))`) PRE util-a (MIRROR 4.4 — deliberatno NE zavisiti od util-ove poruke za konkretan „5 MB" string; buduća promena util/locale poruke ne sme tiho da izgubi limit), PA TEK ONDA `validate_image_mime(photo, allowed_mimes=("image/jpeg","image/png"), max_size_bytes=5*1024*1024)` (REUSE `apps.media_pipeline.utils`) za MIME-signature + Pillow `verify()` (+ util-ova sopstvena size provera, belt-and-suspenders). All-or-nothing: `validate_image_mime` raise-uje `ValidationError` na nevalidnom → cela forma invalid (view NE kreira Lead ni LeadAttachment); prazan `photo` → preskače OBE provere. Čist `clean` (bez save side-effect-a).

### Task 8 — (Dev, GREEN) `part_request_submit` view + URL
- [x] 8.1 `apps/forms/views.py`: dodaj `part_request_submit` FBV (REUSE `service_request_submit` struktura) — `@require_POST` + `@ratelimit(key="ip", rate="5/m", block=False)`; top `if getattr(request,"limited",False): return HttpResponse(status=429)`; bind **`PartRequestForm(request.POST, request.FILES)`**; invalid → render error partial (200, bound form); valid → `with transaction.atomic(): lead = Lead.objects.create(form_type=Lead.FormType.PART_REQUEST, name=..., phone=..., email=..., message=form.cleaned_data["note"], locale=get_language(), ip_address=request.META.get("REMOTE_ADDR"), data={"tractor_model": form.cleaned_data["tractor_model"], "part_name": form.cleaned_data["part_name"], "extra_description": form.cleaned_data["extra_description"], "payment_method": form.cleaned_data["payment_method"], "delivery_method": form.cleaned_data["delivery_method"]}); photo = form.cleaned_data.get("photo"); if photo: LeadAttachment.objects.create(lead=lead, file=photo)`; `send_lead_email(lead)` IZVAN atomic; render success partial. **NEMA cross-app import-a** (forms→products NIJE potreban — model/deo su free text; SM-D7).
- [x] 8.2 `apps/forms/urls.py`: dodaj `path("htmx/forme/rezervni-delovi/", views.part_request_submit, name="part_request_submit")` (POSLE postojećih). `config/urls.py` NETAKNUT.

### Task 9 — (Dev, GREEN) `notifications.py` — PART_REQUEST subject iz `data`
- [x] 9.1 `apps/forms/notifications.py` `_build_subject`: izmeni PART_REQUEST granu (`:39-40`) da vraća `_("[Ćorić Agrar] Upit za rezervni deo: %(part)s (%(model)s)") % {"part": lead.data.get("part_name", lead.name), "model": lead.data.get("tractor_model", "")}` (puni dijakritik; runtime `gettext` — ostaje UNUTAR `translation.override(lead.locale)` bloka koji već okružuje `_build_subject` poziv). Fallback `lead.data.get(..., default)` osigurava da prazan `data` NE crash-uje send (SM-D5). **Ostale grane NETAKNUTE** (`KONTAKT`/`MODEL_INQUIRY`/`SERVICE_REQUEST`). `_resolve_recipient` NETAKNUT (PART_REQUEST→PARTS_EMAIL_TO VEĆ tačno — SM-D6). Attach-loop (4.4) NETAKNUT (automatski attach-uje part-request sliku). C1 try/except NETAKNUT.

### Task 10 — (Dev, GREEN) Forms partials (fields + success)
- [x] 10.1 `templates/forms/partials/_part_request_form_fields.html` (REUSE `_service_request_form_fields.html` struktura): ROOT `<section id="part-request-form-section">` (swap target); **`<form ... enctype="multipart/form-data" hx-encoding="multipart/form-data">`**; SIROVI `<input>`/`<select>`/`<textarea>` + `value="{{ form.X.value|default:'' }}"` idiom (None-safe za GET); polja REDOM (epics.md:829): `tractor_model`/`part_name`/`extra_description` (textarea)/**`<input type="file" name="photo" accept="image/jpeg,image/png">`** (NEMA `multiple` — max 1; SM-D4)/`name`/`phone`/`email`/`payment_method` (`<select>` sa „Pouzeće"/„Predračun")/`delivery_method` (`<select>` sa „Dostava"/„Lično preuzimanje")/`note` (textarea); per-field greške + in-form `role="alert"`/`aria-live="assertive"` error summary (regija #1) + `{% csrf_token %}` + `hx-post="{% url 'forms:part_request_submit' %}"`/`hx-target="#part-request-form-section"`/`hx-swap="outerHTML"`/`htmx-indicator` + ODVOJEN `{% if request.htmx and form.errors %}` OOB polite blok (regija #2). Select-i imaju prazan placeholder opciju + per-value `{% if form.X.value == "..." %}selected{% endif %}` (mirror 4.4 machine_type). Standalone-renderable; NIJE full page.
- [x] 10.2 `templates/forms/partials/part_request_success.html` (REUSE `service_request_success.html`): ROOT `<section id="part-request-form-section">` (čisto zamenjuje formu); poruka zahvalnosti (`{% translate %}`, npr. „Hvala! Vaš upit za rezervni deo je primljen. Javićemo vam se uskoro.") + **`tel:` hitni-pozivi CTA** (REUSE `coric-model-inquiry__emergency` + TODO ka SiteSettings 3-4/8-9 — SM-D11); `{% if request.htmx %}` OOB polite „Upit za rezervni deo je poslat.".

### Task 11 — (Dev, GREEN) `/servis/rezervni-delovi/` strana (pages app)
- [x] 11.1 `apps/pages/views.py`: dodaj `PartRequestView(TemplateView)` (mirror `ServiceView`) — `template_name="pages/part-request.html"`, `http_method_names=["get","head","options"]` (POST → 405; submit ide na forms endpoint). `apps/pages/urls.py`: `path("servis/rezervni-delovi/", PartRequestView.as_view(), name="part_request")` (POSLE `servis/`). NE diraj `ServiceView`/`ContactView`/`HomeView`.
- [x] 11.2 `templates/pages/part-request.html` (mirror `pages/service.html`): naslov „Rezervni delovi" + kratak opis (`{% translate %}`, puni dijakritik) + `tel:` hitni CTA + `{% include "pages/partials/_part_request_form.html" %}`. `templates/pages/partials/_part_request_form.html` (tanak container, mirror `_service_form.html`): `{% include "forms/partials/_part_request_form_fields.html" %}`.
- [x] 11.3 (inspekcija OBAVEZNA, wiring uslovan) Dev MORA pregledati `templates/partials/header.html` za Epic 4/5 „Rezervni delovi"/„Servis" TODO slot (commit 7b1464f). AKO „Rezervni delovi" slot/TODO postoji → wire `href` na `{% url 'pages:part_request' %}`. AKO ne postoji → NE dodavati (nav admin = Epic 8.9; YAGNI). Inspekcija obavezna; rezultat (wired ILI „nema slot-a") dokumentovati.

### Task 12 — (Dev, GREEN) CSS + i18n + lint + verifikacija
- [x] 12.1 REUSE `coric-contact-form__*` + `coric-service-form__file` + `coric-model-inquiry__emergency` BEM iz `static/css/components/contact-page.css` za rezervni-delovi formu. Ako 2-dropdown/single-file layout traži → proširi `contact-page.css`; `var(--token)` umesto magic vrednosti; NIKAD inline style. Mobile (REUSE 4.4 responsive): stack + full-width submit + vidljiv `htmx-indicator`.
- [x] 12.2 `just messages` (makemessages + compilemessages za sr/hu/en) za nove `{% translate %}`/`gettext_lazy`/runtime-`gettext` stringove (page copy, dropdown opcije, subject delovi, success/aria, tel CTA). hu/en smeju ostati prazni (fallback sr).
- [x] 12.3 `just lint` (ruff + djade) clean; `just test` (forms + pages + notifications/email regresija) zelen. Self-review checklist (project-context.md:425): CSRF+ratelimit ✓, **file upload double-check (MIME+Pillow+size) ✓**, aria-live OOB ✓, gettext sve ✓, no inline style ✓, no defensive validation na internim pozivima ✓, **0 migracija (Lead+LeadAttachment VEĆ postoje) ✓**, NEMA cross-app product import ✓.

---

## SM Decisions (log)

- **SM-D1 (NULA migracija — KRITIČNO):** `Lead.FormType.PART_REQUEST = "part_request"` VEĆ postoji (4.1, `models.py:35`) → **0 izmena `Lead` modela, 0 FormType dodataka.** `LeadAttachment` model VEĆ postoji (4.4 migracija `0002`, `models.py:68`) → **0 nove migracije za attachment** (4.5 REUSE postojeći model za max-1 sliku; 1 `LeadAttachment` red ili 0). **4.5 NE generiše NIJEDNU migraciju.** (Najveća razlika od 4.4 koja je uvela `LeadAttachment` — sada je tu.)
- **SM-D2 (`Lead.data` shape za `part_request`) — DEFINIŠE OVA STORY:** `data = {"tractor_model": "<free text>", "part_name": "<free text>", "extra_description": "<opc>", "payment_method": "<choice cod/proforma>", "delivery_method": "<choice delivery/pickup>"}`. „Napomena" (opc.) ide u `Lead.message` (core polje, semantički „glavna poruka" — mirror 4.4 gde `description`→`message`). `name`/`phone`/`email` su core Lead polja. **SVI `data` ključevi UVEK PRISUTNI** (prazan opcioni `extra_description` → `""`, NE izostavljen — zaključano Task 3.2). Shape locked za Epic 8.3 admin prikaz + future export. (Mirror 4.3/4.4 data shape lock.)
- **SM-D3 (email OBAVEZAN na rezervni-delovi formi — RAZLIKA od kontakt/servis):** epics.md:829 „Email *" (zvezdica) → `PartRequestForm.email` je `required=True`. **Za razliku od ContactForm (4.2, email opciono SA porukom)** i **ServiceRequestForm (4.4, email opciono jer phone primaran)**. Rationale: ponuda za rezervni deo (sa cenom/predračunom) prirodno ide na email → email je primarni kanal isporuke ponude. `phone` je TAKOĐE obavezan (epics.md:829 „Telefon *"). `Lead.email`/`Lead.phone` model polja ostaju kakva jesu (model je deljen storage; forma je validacioni SOT — mirror 4.2/4.4). **Napomena (Lead.email blank):** `Lead.email` je `EmailField` BEZ eksplicitnog `blank=True` na nivou modela, ali to je OK jer: (a) `PartRequestForm.email` je `required=True` → view nikad ne prosleđuje prazan email; (b) `Lead.objects.create()` NE poziva `full_clean()`, a PostgreSQL VARCHAR ionako prihvata prazne stringove (ustaljen obrazac iz 4.2/4.4). **NEMA promene modela.**
- **SM-D4 (single-file `photo`, NE multi-file — RAZLIKA od 4.4):** epics.md:829 „Slika (opc., max 1)" → JEDNA slika max. 4.5 koristi **stock Django single-file polje** (`forms.ImageField` ILI `forms.FileField`), **NE** 4.4 `MultipleFileField`/`MultipleFileInput` (taj idiom je za multi-file; ovde bi bio over-engineering). Struktura forme (single `photo` polje) garantuje max-1 — NEMA potrebe za count-validacijom (za razliku od 4.4 „> 3"). Validacija je `clean_photo` (single), NE `clean_photos` (lista): ako prazno → vrati prazno; ako prisutno → `validate_image_mime(photo, allowed_mimes=("image/jpeg","image/png"), max_size_bytes=5*1024*1024)` (REUSE 2.3; MIRROR 4.4 limit — epics.md ne navodi eksplicitan limit za 4.5, biramo konzistentan 5 MB JPG/PNG). Template: `<input type="file" accept="...">` BEZ `multiple`.
- **SM-D5 (`_build_subject` PART_REQUEST grana SE MENJA — JEDINA notifications.py izmena; MIRROR 4.3):** epics.md:831 „[Ćorić Agrar] Upit za rezervni deo: {part_name} ({tractor_model})". Trenutna 4.1 PART_REQUEST grana (`:39-40`) vraća `lead.name` (placeholder — 4.1 nije imao `data` polja za part). **Ova story je menja** da gradi subject iz `lead.data.get("part_name", ...)` + `lead.data.get("tractor_model", ...)` — TAČNO kao što je 4.3 promenio MODEL_INQUIRY granu sa `lead.name` na `lead.data.get("product_name", lead.name)`. **`.get(..., default)` fallback** (defenzivno SAMO na subject-build boundary) osigurava da part-request lead sa praznim `data` (ručno kreiran u shell-u / migracija) NE crash-uje send. Subject je runtime `gettext` UNUTAR postojećeg `translation.override(lead.locale)` bloka (lokalizovan). Potpis `send_lead_email` NETAKNUT; C1 NETAKNUT; attach-loop (4.4) NETAKNUT (automatski attach-uje part-request sliku). Ostale `_build_subject` grane NETAKNUTE (regression — 4.1/4.3/4.4 subject testovi zeleni).
- **SM-D6 (recipient NETAKNUT):** `_resolve_recipient` VEĆ mapira `PART_REQUEST → PARTS_EMAIL_TO` (4.1 `:52-53`). Dev NE menja recipient logiku. `recipient_env` fixture (4.1 conftest `:70`) VEĆ postavlja `PARTS_EMAIL_TO="delovi@coricagrar.rs"` — part-request testovi REUSE direktno.
- **SM-D7 (NEMA cross-app product import u 4.5 — RAZLIKA od 4.3):** „Model traktora" i „Rezervni deo" su **free text** (epics.md:829 ih ne vezuje za `Product` model/slug — kupac upisuje proizvoljan model/deo, uključujući one kojih nema u katalogu). `part_request_submit` **NE importuje `apps.products`** (za razliku od 4.3 model-inquiry re-validacije). Dep boundary forms→core (+ media_pipeline util) only. (Mirror 4.4 SM-D13 — servisna forma takođe ima free-text brand/model bez product import-a.) Subject/`data` koriste user-uneti string, NE DB lookup — ali kako je to NE-spoofable surface (subject ide adminu na PARTS_EMAIL_TO, ne korisniku), nema security re-validacije kao u 4.3 (gde je product spoofing menjao prikaz). Auto-escape u partial-ima (Task 4.3) štiti od XSS u rerender-u.
- **SM-D8 (CACHES NE re-add):** `config/settings/base.py` VEĆ ima locmem `CACHES` (4.2). 4.5 NE re-add. Test REUSE autouse `_pin_and_clear_ratelimit_cache`.
- **SM-D9 (REUSE 4.2/4.4 1:1):** ratelimit `block=False`→429, dve a11y regije (in-form assertive + OOB polite guarded), partials u `templates/forms/partials/`, save-before-send sa `transaction.atomic()` (mirror 4.4 jer ima attachment), gettext + pune dijakritike, CSRF, `htmx-indicator`, multipart `enctype`+`hx-encoding`, sirov-`<input>` None-safe idiom, `validate_image_mime` foto double-check — sve REUSE. 4.5 NE uvodi NIJEDAN novi pattern (čak ni novi model — za razliku od 4.4). Story 4.6 standardizuje shared mixin/decorator (NE sada — YAGNI).
- **SM-D9b (`transaction.atomic` — razrešenje „1:1 REUSE" dvosmislenosti):** Opis kaže „REUSE 1:1 `service_request_submit` (4.4)" — što može da zbuni Dev-a jer 4.4 STORY spec tekst NIJE pominjao `transaction.atomic`. **Realnost: AKTUELNI 4.4 KOD** `apps/forms/views.py::service_request_submit` VEĆ koristi `with transaction.atomic():` oko `Lead.objects.create` + `LeadAttachment.objects.create`, sa `send_lead_email(lead)` IZVAN atomic bloka (atomic je dodat tokom 4.4 code review-a). `part_request_submit` (4.5) MIRROR-uje taj AKTUELNI kod: `with transaction.atomic():` obavija `Lead.objects.create` + opcioni `LeadAttachment.objects.create` (0 ili 1), a `send_lead_email(lead)` je IZVAN atomic bloka. **AC3/Task 8.1 to VEĆ zahtevaju.** Rationale: jedan Lead + do-1 LeadAttachment MORAJU biti atomic (storage greška na attachment-u rollback-uje orphan Lead); email IZVAN atomic-a čuva C1 graceful-failure kontrakt (email failure NE SME da rollback-uje sačuvan lead). Time „1:1 REUSE" više nije dvosmisleno: REUSE = mirror AKTUELNOG 4.4 koda (sa atomic), NE 4.4 spec proze.
- **SM-D10 (`/servis/rezervni-delovi/` strana u `pages`, NESTED pod servis):** Rezervni delovi strana (FR-23) je statička support strana → živi u `apps/pages` (mirror `ServiceView` 4.4). URL `servis/rezervni-delovi/` (epics.md:828) je NESTED pod servis prefiksom (logički podpodručje servisa) — ali je ZASEBAN `path()` (NE child URLconf; YAGNI). `forms` app vlasnik je SAMO render-a forme (fields partial) + submit endpoint-a; `pages` mount-uje formu kroz container partial (mirror `_service_form.html`). `PartRequestView` je GET-only TemplateView (POST → forms endpoint, NE page view).
- **SM-D11 (telefon za hitne pozive + page copy izvor):** AC10/success traže `tel:` CTA + page copy. Default: **hardkodovan-translatable placeholder** (`{% translate %}` + `tel:` link, REUSE `coric-model-inquiry__emergency` iz 4.3/4.4) sa TODO ka SiteSettings (3-4 model postoji; dinamičko vezivanje = 8-9). Dev SME upotrebiti `{% site_setting "phone" %}` ako je dostupan (dokumentovati). Default = hardkodovan da 4.5 NE blokira (mirror 4.3/4.4 SM-D11).
- **SM-D12 (NEMA admin izmene — regression-only):** `LeadAdmin` + `LeadAttachmentInline` (4.1/4.4) su form-type-agnostični → part-request lead + njegova slika automatski se prikazuju kroz postojeći inline. **`apps/forms/admin.py` NETAKNUT** (za razliku od 4.4 koja je dodala inline). AC11 je čist regression smoke (changelist + change-view 200).
- **SM-D13 (GDPR PII + slika):** part-request lead skladišti PII (`name`/`phone`/`email`/`ip_address`) + opciona slika dela (potencijalno EXIF metapodaci). Data-retencija, right-to-erasure, EXIF-stripping = Epic 7 (GDPR). 4.5 SAMO koristi postojeće durabilno skladište (Lead + LeadAttachment); CASCADE FK (4.4) omogućava da Epic 7 erasure obriše sliku sa lead-om. EXIF-stripping NIJE scope 4.5 (forward → Epic 7). Flag OQ-3.
- **SM-D14 (single-file count NE treba validaciju):** Za razliku od 4.4 (multi-file, „> 3" count provera u `clean_photos`), 4.5 single `photo` polje strukturno garantuje max-1 (Django `request.FILES["photo"]` je jedan fajl). NEMA count-validacije. Ako klijent zlonamerno pošalje 2 `photo` part-a, Django uzima poslednji/jedan (NE crash, NE multi-persist). `clean_photo` validira TAJ jedan fajl.

## Open Questions

- **OQ-1 (single vs multi file polje) — RESOLVED: `forms.FileField`.** Preporuka je stock single-file `forms.FileField` (NE `forms.ImageField` — `ImageField` poziva Pillow u `to_python()` što duplira i može da poremeti `seek()` poziciju koju `validate_image_mime` interno koristi; `validate_image_mime` u `clean_photo` je JEDINI autoritativni gate). Test asertuje PONAŠANJE (validna slika prolazi, > 5 MB/ne-slika/webp padaju), NE konkretnu klasu — ali preporučena klasa je `forms.FileField` (Task 7.1).
- **OQ-2 (SM-D4 foto limit 5 MB):** epics.md:829 NE navodi eksplicitan size limit ni dozvoljene tipove za 4.5 sliku (za razliku od 4.4:815 koja eksplicitno kaže JPG/PNG, 5 MB). SM-D4 bira **konzistentan 5 MB JPG/PNG** (mirror 4.4) radi UX konzistentnosti kroz forme. Ako biznis traži drugačiji limit (npr. 1 slika dela može biti veća/manja) → trivijalna izmena `max_size_bytes`. Default: 5 MB JPG/PNG. Flag za biznis sign-off (nije blokirajuće).
- **OQ-3 (SM-D13 EXIF/GDPR):** slika dela može nositi EXIF metapodatke. EXIF-stripping + retencija = Epic 7. Da li 4.5 treba minimalan EXIF-strip pri save-u? Default: NE (Epic 7 scope; YAGNI za v1; mirror 4.4 OQ-3). Flag za Epic 7 planiranje.
- **OQ-4 (SM-D11 telefon izvor):** hitni `tel:` CTA — hardkodovan-translatable placeholder vs `{% site_setting "phone" %}` (3-4). Default: hardkodovan-translatable + TODO (NE blokira). Dev SME upotrebiti `site_setting` ako je dostupan.
- **OQ-5 (Task 11.3 nav wiring):** da li header nav VEĆ ima „Rezervni delovi" placeholder slot (7b1464f TODO marker) koji 4.5 treba da wire-uje na `pages:part_request`? Dev proverava `templates/partials/header.html`; ako postoji slot → wire; ako ne → NE dodavati (nav admin = Epic 8.9). Step-02 može potvrditi.
- **OQ-6 (subject fallback vrednost) — RESOLVED.** Kada part-request lead ima prazan `data` (npr. ručno kreiran), subject fallback je ZAKLJUČAN: `lead.data.get("part_name", lead.name)` (default na `lead.name`) i `lead.data.get("tractor_model", "")` (default prazan string) — TAČNO kao Task 9.1. Subject ostaje renderabilan i informativan (sadrži bar `lead.name`, NIKAD „...: ()"). Test (Task 3.4) asertuje da prazan `data` NE crash-uje send I da subject SADRŽI `lead.name`.
