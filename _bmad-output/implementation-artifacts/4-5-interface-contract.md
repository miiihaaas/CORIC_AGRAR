---
story-id: 4-5-rezervni-delovi-form
artifact: interface-contract
phase: TEA-RED
module: forms + pages
author: Test Architect (🧪)
created: 2026-06-04
status: red-tests-written
---

# Story 4.5 — Interface Contract (TEA RED → Dev GREEN ugovor)

Ovaj dokument je **ugovor** koji TEA testovi specifikuju (RED) i koji Dev implementira (GREEN).
Sve potpise, putanje i string vrednosti su LOCKED testovima — Dev menja IMPLEMENTACIJU, NE ugovor.
4.5 je **1:1 REUSE 4.4 mašinerije** (single-file umesto multi-file); **0 migracija** (`Lead` +
`LeadAttachment` VEĆ postoje). JEDINA `notifications.py` izmena je **`_build_subject` PART_REQUEST
grana** (sa `lead.name` na `lead.data["part_name"] (lead.data["tractor_model"])` — MIRROR 4.3
MODEL_INQUIRY). **NEMA admin izmene** (regression-only — SM-D12). **NEMA cross-app product import** (SM-D7).

---

## § 1 — Models (`apps/forms/models.py`) — NETAKNUT

- `Lead.FormType.PART_REQUEST = "part_request"` VEĆ postoji (4.1). **0 izmena Lead modela.**
- `LeadAttachment` VEĆ postoji (4.4 migracija `0002`). **0 nove migracije.** 4.5 REUSE-uje
  `LeadAttachment` za max-1 sliku (0 ili 1 red po lead-u).
- **`makemigrations forms --check --dry-run` NE sme tražiti nove migracije** (test-lock van scope-a, ali Dev verify).

---

## § 2 — Forms (`apps/forms/forms.py`)

DODAJ `PartRequestForm(forms.Form)` (NE diraj `ContactForm`/`ModelInquiryForm`/`ServiceRequestForm`/
`MultipleFileField`/`MultipleFileInput`). Polja TAČNO (test-lock `set(fields)`):

| polje               | tip                                              | required | widget / napomena |
|---------------------|--------------------------------------------------|----------|-------------------|
| `tractor_model`     | `forms.CharField(max_length=200)`                | **True** | TextInput; „Model traktora *"; free text |
| `part_name`         | `forms.CharField(max_length=200)`                | **True** | TextInput; „Rezervni deo *"; free text |
| `extra_description` | `forms.CharField(widget=forms.Textarea)`         | **False**| Textarea; „Dodatni opis (opc.)" |
| `photo`             | `forms.FileField` (single-file — OQ-1)           | **False**| `FileInput(attrs={"accept": "image/jpeg,image/png"})`; „Slika (opc., max 1)"; **NE `MultipleFileField`, NE `ImageField`** |
| `name`              | `forms.CharField(max_length=200)`                | **True** | TextInput; „Ime *" |
| `phone`             | `forms.CharField(max_length=50)`                 | **True** | TextInput type=tel; „Telefon *" |
| `email`             | `forms.EmailField`                               | **True** | EmailInput; „E-pošta *" — **OBAVEZAN (SM-D3 — RAZLIKA od 4.4)** |
| `payment_method`    | `forms.ChoiceField(choices=PaymentMethod.choices)` | **True** | `forms.Select`; „Način plaćanja *" |
| `delivery_method`   | `forms.ChoiceField(choices=DeliveryMethod.choices)`| **True** | `forms.Select`; „Način preuzimanja *" |
| `note`              | `forms.CharField(widget=forms.Textarea)`         | **False**| Textarea; „Napomena (opc.)" |

- Sve labele/error poruke kroz `gettext_lazy` (pune dijakritike č/ć/ž/š/đ). HTML5 widget atributi
  (`type=tel`, `required`, `accept`) = UX sloj. Widget `id` konvencija `part-<field>` (mirror `service-`).
- **OQ-1 (`forms.FileField`, NE `forms.ImageField`):** `ImageField` poziva Pillow u `to_python()` →
  duplira + može poremetiti `seek()` poziciju koju `validate_image_mime` interno koristi.
  `validate_image_mime` u `clean_photo` je JEDINI autoritativni gate.

### `PaymentMethod(TextChoices)` — vrednosti/labele LOCKED (test `{cod, proforma}`)

```python
class PaymentMethod(models.TextChoices):
    COD = "cod", _("Pouzeće")
    PROFORMA = "proforma", _("Predračun")
```

### `DeliveryMethod(TextChoices)` — vrednosti/labele LOCKED (test `{delivery, pickup}`)

```python
class DeliveryMethod(models.TextChoices):
    DELIVERY = "delivery", _("Dostava")
    PICKUP = "pickup", _("Lično preuzimanje")
```

- Choice DB vrednosti su TAČNO `{"cod","proforma"}` i `{"delivery","pickup"}` (test-lock).
- Labele puni dijakritik: „Pouzeće" (ć), „Predračun" (č), „Lično preuzimanje" (č); NIKAD ćirilica.
- `(models` = `from django.db import models` ILI ekvivalent — test asertuje samo VREDNOSTI/labele.

### `clean_photo` — single-file foto double-check (AC2, KRITIČNO)

```python
def clean_photo(self):
    photo = self.cleaned_data.get("photo")
    if not photo:
        return photo                      # prazno → vrati bez double-check-a (NE poziva util)
    if getattr(photo, "size", 0) and photo.size > 5 * 1024 * 1024:
        raise ValidationError(_("Slika je veća od 5 MB. Probajte manju."))   # strukturni „5 MB"
    validate_image_mime(
        photo,
        allowed_mimes=("image/jpeg", "image/png"),   # EXCLUSION webp — pinovan (NE default)
        max_size_bytes=5 * 1024 * 1024,              # EKSPLICITNO (NE default 10 MB)
    )
    return photo
```

- **Strukturna size pre-provera PRE util-a** (MIRROR 4.4 `clean_photos`): clean string „5 MB" je
  deterministički vezan za uzrok; locale/util-message promena ne sme tiho da ukloni limit. Test
  asertuje substring „5 MB" — zadovoljeno iz BILO KOG izvora.
- **`validate_image_mime` raise-uje `ValidationError`** na: ne-slici (PDF MIME-signature mismatch),
  corrupt (Pillow `verify()` fail), **webp** (NIJE u `allowed_mimes` — EXCLUSION, ne Pillow/signature fail),
  > 5 MB. Cela forma invalid → view NE kreira Lead ni LeadAttachment.
- **Spy test-lock:** `validate_image_mime` pozvan sa `allowed_mimes=("image/jpeg","image/png")` +
  `max_size_bytes=5*1024*1024`; prazan `photo` → `call_count == 0`.
- **Max 1 (SM-D4/SM-D14):** single `forms.FileField` strukturno garantuje max-1 (`request.FILES["photo"]`
  je jedan fajl). NEMA count-validacije (za razliku od 4.4 „> 3"). Čist `clean` (bez save side-effect-a).

---

## § 3 — Views (`apps/forms/views.py`)

DODAJ `part_request_submit` FBV (REUSE AKTUELNI `service_request_submit` kod — sa `transaction.atomic`,
SM-D9b; NE diraj postojeće view-ove; **NEMA `apps.products` import** — SM-D7).

```python
@require_POST
@ratelimit(key="ip", rate="5/m", block=False)
def part_request_submit(request):
    if getattr(request, "limited", False):
        return HttpResponse(status=429)          # NE 403 (block=False — SM-D9)

    form = PartRequestForm(request.POST, request.FILES)   # multipart — fajl u request.FILES
    if not form.is_valid():
        return render(request, "forms/partials/_part_request_form_fields.html", {"form": form})  # 200

    with transaction.atomic():
        lead = Lead.objects.create(
            form_type=Lead.FormType.PART_REQUEST,
            name=form.cleaned_data["name"],
            phone=form.cleaned_data["phone"],
            email=form.cleaned_data["email"],
            message=form.cleaned_data["note"],         # Napomena → Lead.message (SM-D2)
            locale=get_language(),
            ip_address=request.META.get("REMOTE_ADDR"),
            data={
                "tractor_model": form.cleaned_data["tractor_model"],
                "part_name": form.cleaned_data["part_name"],
                "extra_description": form.cleaned_data["extra_description"],  # prazan → "" (ključ PRISUTAN)
                "payment_method": form.cleaned_data["payment_method"],
                "delivery_method": form.cleaned_data["delivery_method"],
            },
        )
        photo = form.cleaned_data.get("photo")
        if photo:
            LeadAttachment.objects.create(lead=lead, file=photo)
    send_lead_email(lead)                              # IZVAN atomic — C1 (povratak se NE rollback-uje)
    return render(request, "forms/partials/part_request_success.html", {"lead": lead})
```

- **Save-before-send redosled (LOCKED):** (1) `Lead.objects.create`, (2) opciono `LeadAttachment.objects.create`
  (0 ili 1), oboje UNUTAR `transaction.atomic()`; (3) `send_lead_email` IZVAN atomic.
- **`Lead.data` shape (SM-D2, LOCKED — 5 ključeva UVEK PRISUTNI):** `{"tractor_model","part_name",
  "extra_description","payment_method","delivery_method"}`. Prazan `extra_description` → `""` (NE izostavljen).
  `note` → `Lead.message` (prazan → `""`). `name`/`phone`/`email` = core Lead polja.
- **429:** `block=False` + top-of-body `if getattr(request,"limited",False): return HttpResponse(status=429)`.
  Test asertuje 6. submit == 429, NIJEDAN 403.
- **All-or-nothing:** ako `clean_photo` raise-uje (loš MIME / > 5 MB / webp / corrupt / PDF) →
  `form.is_valid()` False → error partial 200, 0 Lead, 0 LeadAttachment, 0 email (validacija PRE create).
- **Email-failure:** ako `send_lead_email` vrati False → Lead + opciona slika OSTAJU, posetilac dobija
  success partial (mock SAMO `apps.forms.views.send_lead_email` povratnu vrednost).

---

## § 4 — URLs (`apps/forms/urls.py`)

DODAJ (POSLE `service_request_submit`):

```python
path("htmx/forme/rezervni-delovi/", views.part_request_submit, name="part_request_submit"),
```

- `config/urls.py` NETAKNUT (`apps.forms.urls` VEĆ mount-ovan u `i18n_patterns`).
- `reverse("forms:part_request_submit")` pod `activate("sr")` → `/sr/htmx/forme/rezervni-delovi/`
  (hu/en → `/hu|en/...`). GET → 405 (`@require_POST`).

---

## § 5 — Notifications (`apps/forms/notifications.py`) — JEDINA izmena (PART_REQUEST subject, SM-D5)

Izmeni `_build_subject` PART_REQUEST granu (trenutno vraća `lead.name` — 4.1 placeholder):

```python
    if lead.form_type == Lead.FormType.PART_REQUEST:
        return _("[Ćorić Agrar] Upit za rezervni deo: %(part)s (%(model)s)") % {
            "part": lead.data.get("part_name", lead.name),    # fallback na lead.name (OQ-6)
            "model": lead.data.get("tractor_model", ""),      # fallback prazan string
        }
```

- **Subject LOCKED (test):** `mailoutbox[0].subject` sadrži
  `"[Ćorić Agrar] Upit za rezervni deo: Filter ulja (Agri Tracking TB804)"` (iz `lead.data`, **NE** `lead.name`).
  Ovaj test FORSIRA izmenu (trenutni kod vraća `lead.name` → test fail dok Dev ne promeni granu).
- **Fallback (OQ-6 RESOLVED):** prazan `data` (`{}`) + postavljen `name` → subject SADRŽI `lead.name`,
  NE crash-uje send, NIKAD „...: ()". Test-lock: `": ()" not in subject`.
- **Runtime `gettext` UNUTAR `translation.override(lead.locale)`** (subject lokalizovan; postojeći blok).
- **Ostale grane NETAKNUTE** (test-lock — regression): KONTAKT (`lead.name`), SERVICE_REQUEST
  (`lead.name`), MODEL_INQUIRY (`data["product_name"]`). `_resolve_recipient` PART_REQUEST →
  `PARTS_EMAIL_TO` NETAKNUT (SM-D6). Attach-loop (4.4) NETAKNUT — automatski attach-uje part-request
  sliku (1 attachment → `len(mailoutbox[0].attachments)==1`). C1 try/except NETAKNUT. `send_lead_email`
  potpis `-> bool` NETAKNUT.

---

## § 6 — Templates / Partials (`templates/forms/partials/`)

### `_part_request_form_fields.html` (REUSE `_service_request_form_fields.html`)

- ROOT `<section id="part-request-form-section">` (swap target; `hx-target="#part-request-form-section"`,
  `hx-swap="outerHTML"`).
- `<form method="post" enctype="multipart/form-data" hx-post="{% url 'forms:part_request_submit' %}"
  hx-target="#part-request-form-section" hx-swap="outerHTML" hx-encoding="multipart/form-data">`.
- **SVA polja kroz SIROVI `<input>`/`<select>`/`<textarea>` + `value="{{ form.X.value|default:'' }}"` idiom**
  (None-safe za GET bez bound form — `PartRequestView` je TemplateView, NE prosleđuje `form`). Redom (epics.md:829):
  - `tractor_model`/`part_name` (sirov `<input type="text">`); `extra_description` (sirov `<textarea>`).
  - `photo` → `<input type="file" name="photo" accept="image/jpeg,image/png" class="... coric-service-form__file">`
    **BEZ `multiple`** (max 1 — SM-D4).
  - `name`/`phone`/`email` (sirov `<input>`).
  - `payment_method` → `<select name="payment_method">` sa praznim placeholder-om + opcijama
    „Pouzeće"/„Predračun" + per-value `{% if form.payment_method.value == "..." %}selected{% endif %}`.
  - `delivery_method` → `<select name="delivery_method">` sa „Dostava"/„Lično preuzimanje" + selected idiom.
  - `note` (sirov `<textarea>`).
- **Regija #1 (in-form):** `{% if form.errors %}` → `<div ... role="alert" aria-live="assertive">` error
  summary sa per-field greškama (REUSE 4.4 `coric-contact-form__alert`).
- `{% csrf_token %}` + submit dugme `class="... coric-contact-form__submit"` + `htmx-indicator` spinner
  (`class="coric-contact-form__indicator htmx-indicator"`).
- **Regija #2 (OOB, ODVOJEN):** `{% if request.htmx and form.errors %}` →
  `<div hx-swap-oob="innerHTML:#aria-live">{% translate "Greška pri slanju, proverite polja." %}</div>`.
- Standalone-renderable (None-safe za GET bez bound form).

### `part_request_success.html` (REUSE `service_request_success.html`)

- ROOT `<section id="part-request-form-section">` (čisto zamenjuje formu).
- Poruka zahvalnosti kroz `{% translate %}` (puni dijakritik).
- **Hitni `tel:` CTA:** `<a href="tel:+381...">` klikabilan (REUSE `coric-model-inquiry__emergency` +
  TODO ka SiteSettings 3-4/8-9 ILI `{% site_setting %}` — SM-D11).
- **OOB polite (SAMO success):** `{% if request.htmx %}` →
  `<div hx-swap-oob="innerHTML:#aria-live">{% translate "Upit za rezervni deo je poslat." %}</div>`.

**LOCKED OOB / success string vrednosti (testovi asertuju TAČAN tekst):**
- success OOB: `Upit za rezervni deo je poslat.`
- error OOB: `Greška pri slanju, proverite polja.`

---

## § 7 — `/servis/rezervni-delovi/` strana (`apps/pages`)

### `apps/pages/views.py` — `PartRequestView` (mirror `ServiceView`, GET-only)

```python
class PartRequestView(TemplateView):
    template_name = "pages/part-request.html"
    http_method_names = ["get", "head", "options"]   # POST → 405 (submit ide na forms endpoint)
```

### `apps/pages/urls.py` (DODAJ POSLE `servis/`)

```python
path("servis/rezervni-delovi/", PartRequestView.as_view(), name="part_request"),
```

- `reverse("pages:part_request")` pod `sr` → `/sr/servis/rezervni-delovi/`; GET → 200; POST → **405**.
- Regresija: Home/Contact/Service i dalje 200.
- `templates/pages/part-request.html` (mirror `pages/service.html`): naslov „Rezervni delovi" + kratak
  opis (`{% translate %}`, puni dijakritik) + hitni `tel:` CTA + `{% include "pages/partials/_part_request_form.html" %}`.
- `templates/pages/partials/_part_request_form.html` (tanak container, mirror `_service_form.html`):
  `{% include "forms/partials/_part_request_form_fields.html" %}`.
- Renderovana forma: NIJE disabled; `hx-post` ka `forms:part_request_submit`; `enctype="multipart/form-data"`;
  `<input type="file" accept>` **BEZ `multiple`**; oba `<select>` (payment_method/delivery_method) sa opcijama;
  `{% csrf_token %}` prisutan; `tel:` CTA prisutan; partial None-safe na GET (sirov-`<input>` idiom).
- **Task 11.3 (nav wiring — inspekcija obavezna):** Dev pregleda `templates/partials/header.html` za
  „Rezervni delovi" TODO slot; ako postoji → wire na `{% url 'pages:part_request' %}`; ako ne → NE dodavati.

---

## § 8 — Admin (`apps/forms/admin.py`) — NETAKNUT (SM-D12)

- **NEMA izmene.** `LeadAdmin` + `LeadAttachmentInline` (4.1/4.4) su form-type-agnostični → part-request
  lead + slika automatski se prikazuju kroz postojeći inline.
- Test (regression-only): superuser GET `admin:forms_lead_changelist` → 200; change-view part-request
  lead-a sa 1 `LeadAttachment` → 200; `FormType.PART_REQUEST.label == "Upit za rezervni deo"`.

---

## § 9 — Ratelimit / Cache (REUSE 4.2 — NE re-add)

- `config/settings/base.py` `CACHES` (locmem `default`) VEĆ postoji (4.2 / SM-D8). NE re-add.
- Test REUSE autouse `_pin_and_clear_ratelimit_cache` (locmem + `cache.clear()`) iz forms conftest-a.
- 5/m po IP-u; 6. submit istog IP-a u 1 min → 429 (NE 403). Različiti IP-ovi se broje odvojeno.

---

## § 10 — Test fixtures (`apps/forms/tests/conftest.py`)

PROŠIRENO (REUSE postojećih `recipient_env` (`PARTS_EMAIL_TO`)/`htmx_post`/`superuser`/autouse
`_pin_and_clear_ratelimit_cache` + `_isolate_media_root` + 4.4 image fixtures — **NE re-definisati**):
- `part_request_payload` — `{tractor_model, part_name, extra_description, name, phone, email,
  payment_method:"cod", delivery_method:"delivery", note}` (pun dijakritik) BEZ `photo`.
- `part_request_submit_url` — `activate("sr")` + `reverse("forms:part_request_submit")`.

**Test konvencija:** SVI part-request POST testovi koriste `htmx_post` (fiksan IP `203.0.113.7`,
`HTTP_HX_REQUEST="true"`); single-file idiom: `htmx_post(url, {**part_request_payload, "photo": valid_image_jpeg})`
(JEDAN fajl pod ključem `photo` → Django test client → `request.FILES["photo"]`). Form-nivo:
`MultiValueDict({"photo": [upload]})`. ENDPOINT oversized koristi `oversized_image_real` (round-trip safe);
FORM-nivo oversized koristi `oversized_image` (forsiran `.size`).
