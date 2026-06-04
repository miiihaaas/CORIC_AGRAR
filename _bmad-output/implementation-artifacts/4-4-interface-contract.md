---
story-id: 4-4-servisni-zahtev-form-sa-foto-upload-om
artifact: interface-contract
phase: TEA-RED
module: forms
author: Test Architect (🧪)
created: 2026-06-04
status: red-tests-written
---

# Story 4.4 — Interface Contract (TEA RED → Dev GREEN ugovor)

Ovaj dokument je **ugovor** koji TEA testovi specifikuju (RED) i koji Dev implementira (GREEN).
Sve potpise, putanje i string vrednosti su LOCKED testovima — Dev menja IMPLEMENTACIJU, NE ugovor.
REUSE 4.2/4.3 1:1 (SM-D10); jedina razlika je file-upload (multipart enctype + `hx-encoding` +
`validate_image_mime` double-check + `LeadAttachment` child model + email attach). `_build_subject`
SERVICE_REQUEST grana je VEĆ tačna (`lead.name`) — **NE menja se** (SM-D7); `_resolve_recipient` NETAKNUT (SM-D6).

---

## § 1 — Model (`apps/forms/models.py`)

DODAJ `class LeadAttachment(models.Model)` (NE diraj `Lead` — SM-D1; NEMA `photo` polja na Lead-u, NEMA FormType dodatka):

| polje    | tip / opcije                                                                                  | napomena |
|----------|-----------------------------------------------------------------------------------------------|----------|
| `lead`   | `models.ForeignKey(Lead, on_delete=models.CASCADE, related_name="attachments", verbose_name=_("Lead"))` | **CASCADE** (brisanje Lead-a briše attachment-e); `related_name="attachments"` (view + notifications koriste `lead.attachments`) |
| `file`   | `models.FileField(upload_to="leads/attachments/%Y/%m/", verbose_name=_("Datoteka"))`          | **NIJE `ImageField`** (validacija je u formi kroz `validate_image_mime`); `upload_to` per godina/mesec |

- **NE nasleđuje `TimestampedModel`** (SM-D3 — YAGNI; `lead.created_at` je dovoljan). **NEMA `created_at` polja.**
  Test-lock: `assert "created_at" not in {f.name for f in LeadAttachment._meta.get_fields()}`.
- `__str__` → npr. `f"Prilog uz {self.lead_id}: {self.file.name}"` (informativan; sadrži „Prilog" + file name).
- `Meta.verbose_name = _("Prilog")`, `verbose_name_plural = _("Prilozi")` (pune dijakritike).
- **Asercija lock (test):** `LeadAttachment._meta.get_field("lead").remote_field.on_delete is models.CASCADE`;
  `LeadAttachment._meta.get_field("lead").remote_field.related_name == "attachments"`;
  `isinstance(LeadAttachment._meta.get_field("file"), models.FileField)`.

### Migracija `0002` (Dev GREEN — Task 7.2)
- `uv run python manage.py makemigrations forms` → `apps/forms/migrations/0002_*.py` sa **SAMO** `CreateModel("LeadAttachment", ...)`.
- **NEMA `AlterField` na Lead, NEMA `AddField` (`photo`) na Lead** (test-lock).
- Posle migracije: `makemigrations forms --check --dry-run` NE traži nove migracije (model + migracija sinhronizovani).
- Reverzibilno (`migrate forms 0001` čisto). Commit model + migracija ZAJEDNO (atomic).

---

## § 2 — Forms (`apps/forms/forms.py`)

DODAJ `ServiceRequestForm(forms.Form)` (NE diraj `ContactForm`/`ModelInquiryForm`). Polja:

| polje         | tip                                       | required | widget                | napomena |
|---------------|-------------------------------------------|----------|-----------------------|----------|
| `name`        | `forms.CharField(max_length=200)`         | **True** | TextInput             | mirror Contact |
| `phone`       | `forms.CharField(max_length=50)`          | **True** | TextInput type=tel    | **RAZLIKA od ContactForm** (phone OBAVEZAN — SM-D9) |
| `email`       | `forms.EmailField`                        | **False**| EmailInput            | OPCIONO (epics.md:814 bez zvezdice) |
| `machine_type`| `forms.ChoiceField(choices=MachineType.choices)` | **True** | `forms.Select`  | nested `MachineType(TextChoices)` |
| `brand_model` | `forms.CharField(max_length=200)`         | **False**| TextInput             | free text, OPCIONO |
| `description` | `forms.CharField(widget=forms.Textarea)`  | **True** | Textarea              | required=True NA FORMI iako `Lead.message` blank=True |
| `photos`      | `MultipleFileField(required=False)`       | **False**| `MultipleFileInput(attrs={"multiple": True, "accept": "image/jpeg,image/png"})` | multi-file (SM-D4) |

### `MachineType(TextChoices)` — vrednosti/labele LOCKED

```python
class MachineType(models.TextChoices):
    TRACTOR = "tractor", _("Traktor")
    ATTACHMENT = "attachment", _("Priključna mehanizacija")
    WORK_MACHINE = "work_machine", _("Radna mašina")
    OTHER = "other", _("Ostalo")
```

- Choice set (DB vrednosti) je TAČNO `{tractor, attachment, work_machine, other}` (test-lock).
- Labele kroz `gettext_lazy` (pun dijakritik — „Priključna" sa č; „mašina" sa š); NIKAD ćirilica.
- `(models` je `from django.db import models` ILI `from django.forms import ...` — bilo `forms.ChoiceField` sa
  `django.db.models.TextChoices`; Dev bira ekvivalent. Test asertuje samo choice VREDNOSTI/labele.)

### Multi-file idiom (SM-D4 — KANONSKI Django 5.x; NE `MultipleHiddenInput`)

```python
class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single = super().clean
        if isinstance(data, (list, tuple)):
            return [single(d, initial) for d in data]
        return [single(data, initial)] if data else []
```

### `clean_photos` — foto double-check + all-or-nothing (AC3, KRITIČNO)

- Čita listu fajlova (iz `self.cleaned_data["photos"]` ILI `self.files.getlist("photos")` — Dev bira; vidi SM-D4).
- **Count:** ako `len(files) > 3` → `raise ValidationError(_("Možete priložiti najviše 3 slike."))` (substring „najviše 3" test-lock).
- **Per fajl:** `validate_image_mime(f, allowed_mimes=("image/jpeg", "image/png"), max_size_bytes=5 * 1024 * 1024)`
  (REUSE `apps.media_pipeline.utils` — MIME signature + Pillow `verify()` + size). **EKSPLICITNO** `("image/jpeg","image/png")`
  (NE default koji uključuje webp) i **EKSPLICITNO** `5 * 1024 * 1024` (NE default 10 MB).
- **Size poruka:** util-ova poruka već sadrži „5 MB" (jer `limit=5`). Test asertuje samo substring „5 MB"
  (Dev SME re-raise sa epics.md stringom „Slika je veća od 5 MB. Probajte manju." — i dalje raise, NE swallow).
- **All-or-nothing (NIKAD partial-accept):** clean iterira; na **PRVOM** nevalidnom fajlu PROPAGIRA `ValidationError`
  (cela forma invalid → view NE kreira ni Lead ni LeadAttachment). NA uspehu (SVI fajlovi validni) vraća **punu listu**.
  NEMA „filter-and-keep-good" putanje. `validate_image_mime` već raise-uje — NE hvatati-i-nastaviti.
- **webp je odbijen** jer NIJE u `allowed_mimes` (pinovan jpeg/png) — behavior-lock za `allowed_mimes` argument.
- Clean je čist (bez save side-effect-a; save je u view-u posle `is_valid()`).
- Sve labele/error poruke kroz `gettext_lazy` (pune dijakritike); HTML5 widget atributi = UX sloj.

---

## § 3 — Views (`apps/forms/views.py`)

DODAJ `service_request_submit` FBV (REUSE `contact_submit` struktura; NE diraj postojeće view-ove; **NEMA cross-app product import** — SM-D13).

```python
@require_POST
@ratelimit(key="ip", rate="5/m", block=False)
def service_request_submit(request):
    if getattr(request, "limited", False):
        return HttpResponse(status=429)          # NE 403 (block=False — SM-D9)

    form = ServiceRequestForm(request.POST, request.FILES)   # multipart — fajlovi u request.FILES
    if not form.is_valid():
        return render(request, "forms/partials/_service_request_form_fields.html", {"form": form})   # 200

    lead = Lead.objects.create(
        form_type=Lead.FormType.SERVICE_REQUEST,
        name=form.cleaned_data["name"],
        phone=form.cleaned_data["phone"],
        email=form.cleaned_data["email"],
        message=form.cleaned_data["description"],       # opis kvara → Lead.message (SM-D2)
        locale=get_language(),
        ip_address=request.META.get("REMOTE_ADDR"),
        data={
            "machine_type": form.cleaned_data["machine_type"],
            "brand_model": form.cleaned_data["brand_model"],   # prazan opcioni → "" (ključ PRISUTAN)
        },
    )
    for f in form.cleaned_data["photos"]:               # prazna lista ako bez slika
        LeadAttachment.objects.create(lead=lead, file=f)
    send_lead_email(lead)                               # save-before-send; povratak se NE rollback-uje
    return render(request, "forms/partials/service_request_success.html", {"lead": lead})
```

- **Save-before-send redosled (LOCKED):** (1) `Lead.objects.create`, (2) `LeadAttachment.objects.create` po fajlu, (3) `send_lead_email`.
- **`Lead.data` shape (SM-D2, LOCKED):** `{"machine_type": "<choice>", "brand_model": "<text ili prazan string>"}` —
  `brand_model` ključ je UVEK prisutan (prazan opcioni field → `""`, NE izostavljen).
- **429 mehanizam:** `block=False` + top-of-body `if getattr(request, "limited", False): return HttpResponse(status=429)`.
  Test asertuje 6. submit == 429, NIJEDAN 403.
- **All-or-nothing na endpointu:** ako `clean_photos` raise-uje (loš MIME / > 5 MB / > 3 / mixed-batch) → `form.is_valid()`
  je False → error partial 200, 0 Lead, 0 LeadAttachment, 0 email. Validacija (uklj. foto double-check) je PRE `Lead.objects.create`.
- **Email-failure:** ako `send_lead_email` vrati False, Lead + attachment-i OSTAJU, posetilac dobija success partial.

---

## § 4 — URLs (`apps/forms/urls.py`)

DODAJ (POSLE `model_inquiry_submit`):

```python
path("htmx/forme/servis/", views.service_request_submit, name="service_request_submit"),
```

- `config/urls.py` NETAKNUT (`apps.forms.urls` VEĆ mount-ovan u `i18n_patterns`).
- `reverse("forms:service_request_submit")` pod `activate("sr")` → `/sr/htmx/forme/servis/` (hu/en → `/hu|en/...`).
- GET → 405 (`@require_POST`).

---

## § 5 — Notifications (`apps/forms/notifications.py`) — JEDINA izmena (attach slika, SM-D5)

`send_lead_email`, PRE `message.send()` (potpis `-> bool` NETAKNUT; C1 try/except NETAKNUT):

```python
import mimetypes
...
    message.attach_alternative(html_body, "text/html")

    for attachment in lead.attachments.all():           # prazan queryset → no-op (regression)
        with attachment.file.open("rb") as f:           # context manager (handle-safe)
            content = f.read()
        name = attachment.file.name.split("/")[-1]
        mimetype = mimetypes.guess_type(name)[0] or "application/octet-stream"   # fallback (None guard)
        message.attach(name, content, mimetype)

    try:
        message.send()
    ...
```

- **`_build_subject` SERVICE_REQUEST grana NETAKNUTA** (`:35-36` VEĆ vraća „[Ćorić Agrar] Novi servisni zahtev: {lead.name}"
  — TAČNO; RAZLIKA od 4.3 — SM-D7). **`_resolve_recipient` NETAKNUT** (SERVICE_REQUEST → SERVICE_EMAIL_TO VEĆ tačno — SM-D6).
- **Mimetype fallback:** `guess_type` može vratiti `None` → fallback `"application/octet-stream"` (test asertuje mimetype
  u attachment tuple-u je NE-`None`; za jpeg/png biće `"image/jpeg"`/`"image/png"`).
- **Lead bez attachment-a** (kontakt/model_inquiry/part/service-bez-slika) → prazan queryset → no-op. Postojeći
  4-1/4-2/4-3 email-ovi rade identično (regression — `test_send_lead_email.py` ostaje zelen).
- **Attachment tuple lock (test):** `name, content, mimetype = mailoutbox[0].attachments[0]; assert mimetype in ("image/jpeg","image/png")`.

---

## § 6 — Templates / Partials (`templates/forms/partials/`)

### `_service_request_form_fields.html` (REUSE `_contact_form_fields.html`)
- ROOT `<section id="service-form-section">` (swap target; `hx-target="#service-form-section"`, `hx-swap="outerHTML"`).
- `<form method="post" enctype="multipart/form-data" hx-post="{% url 'forms:service_request_submit' %}"
  hx-target="#service-form-section" hx-swap="outerHTML" hx-encoding="multipart/form-data" data-testid="service-form">`.
- **SVA polja kroz SIROVI `<input>`/`<select>`/`<textarea>` + `value="{{ form.X.value|default:'' }}"` idiom**
  (None-safe za GET bez bound form — `ServiceView` je TemplateView, NE prosleđuje `form`).
  - `name`/`phone`/`email`/`brand_model` (sirov `<input>`); `description` (sirov `<textarea>`).
  - `machine_type` → `<select name="machine_type">` sa opcijama kroz `{% translate %}` (Traktor / Priključna mehanizacija /
    Radna mašina / Ostalo).
  - `photos` → `<input type="file" name="photos" accept="image/jpeg,image/png" multiple>` (AC8 — `accept` + `multiple`).
- **Regija #1 (in-form):** `{% if form.errors %}` → `<div role="alert" aria-live="assertive">` error summary sa per-field greškama.
- `{% csrf_token %}` + `htmx-indicator` spinner.
- **Regija #2 (OOB, ODVOJEN):** `{% if request.htmx and form.errors %}` →
  `<div hx-swap-oob="innerHTML:#aria-live">{% translate "Greška pri slanju, proverite polja." %}</div>`.
- Standalone-renderable (None-safe za GET bez bound form).

### `service_request_success.html` (REUSE `contact_success.html`)
- ROOT `<section id="service-form-section">` (čisto zamenjuje formu).
- Poruka zahvalnosti kroz `{% translate %}`.
- **Hitni `tel:` CTA (AC11 — Stojan je sa terena):** `<a href="tel:+381...">` klikabilan, kroz `{% translate %}`,
  pun dijakritik; hardkodovan-translatable placeholder + TODO ka SiteSettings (3-4/8-9) ILI `{% site_setting %}` (SM-D11).
- **OOB polite (SAMO success):** `{% if request.htmx %}` →
  `<div hx-swap-oob="innerHTML:#aria-live">{% translate "Servisni zahtev je poslat." %}</div>`.

**LOCKED OOB / success string vrednosti (testovi assertuju TAČAN tekst):**
- success OOB: `Servisni zahtev je poslat.`
- error OOB: `Greška pri slanju, proverite polja.`

---

## § 7 — `/servis/` strana (`apps/pages`)

### `apps/pages/views.py` — `ServiceView` (mirror `ContactView`, GET-only)

```python
class ServiceView(TemplateView):
    template_name = "pages/service.html"
    http_method_names = ["get", "head", "options"]   # POST → 405 (submit ide na forms endpoint)
```

### `apps/pages/urls.py`

```python
path("servis/", ServiceView.as_view(), name="service"),
```

- `reverse("pages:service")` pod `sr` → `/sr/servis/`; GET → 200; POST → **405** (GET-only).
- Template `pages/service.html` (mirror `pages/contact.html`): naslov „Servisna podrška" + kratak opis (`{% translate %}`,
  pun dijakritik) + `{% include "pages/partials/_service_form.html" %}` + hitni `tel:` CTA.
- `templates/pages/partials/_service_form.html` (tanak container, mirror `_contact_form.html`):
  `{% include "forms/partials/_service_request_form_fields.html" %}`.
- Renderovana forma: NIJE disabled; `hx-post` ka `forms:service_request_submit`; `enctype="multipart/form-data"`;
  `<input type="file" multiple accept>`; `{% csrf_token %}` prisutan; partial None-safe na GET (sirov-`<input>` idiom).

---

## § 8 — Admin (`apps/forms/admin.py`)

DODAJ `LeadAttachmentInline` na `LeadAdmin` (NE diraj postojeće `LeadAdmin` opcije):

```python
class LeadAttachmentInline(admin.TabularInline):
    model = LeadAttachment
    extra = 0
    # opciono readonly_fields

class LeadAdmin(admin.ModelAdmin):
    ...
    inlines = [LeadAttachmentInline]
```

- Registracija na POSTOJEĆI `admin.site` (NE custom slug/axes — Epic 8.1).
- `reverse("admin:forms_lead_changelist")` GET (superuser) → 200 (regression); change-view sa attachment-ima → 200.

---

## § 9 — Ratelimit / Cache (REUSE 4.2 — NE re-add)

- `config/settings/base.py` `CACHES` (locmem `default`) VEĆ postoji (4.2 / SM-D8). NE re-add.
- Test REUSE autouse `_pin_and_clear_ratelimit_cache` (locmem + `cache.clear()` pre/posle) iz forms conftest-a.
- 5/m po IP-u; 6. submit istog IP-a u 1 min → 429 (NE 403).

---

## § 10 — Test fixtures (`apps/forms/tests/conftest.py`)

PROŠIRENO (REUSE postojećih `recipient_env`/`htmx_post`/`superuser`/autouse `_pin_and_clear_ratelimit_cache`):
- `service_request_payload` — `{name, phone, email, machine_type, brand_model, description}` (pun dijakritik).
- `service_request_submit_url` — `activate("sr")` + `reverse("forms:service_request_submit")`.
- `valid_image_jpeg` / `valid_image_png` / `valid_image_webp` — Pillow in-memory → `SimpleUploadedFile`
  (validne male slike; webp za „webp odbijen jer nije u allowed_mimes" assertion).
- `oversized_image` — **VALIDNA mala JPEG sa monkeypatch-ovanim `.size` > 5 MB** (NE sirov BytesIO blob;
  rationale Task 1.1 — sirov 5 MB blob bi pao na MIME/Pillow grani, NE size grani). KORISTI SE SAMO za
  FORM-nivo testove (direktan bind, bez HTTP round-trip-a — forsiran `.size` se očuva).
- `oversized_image_real` — **VALIDNA JPEG sa STVARNIH > 5 MB bajtova** (random-noise 2600×2600, ~12 MB;
  6.76M px < `Image.MAX_IMAGE_PIXELS` 50M guard). KORISTI SE za ENDPOINT-nivo oversized test
  (`htmx_post` round-trip): Django test client `encode_file` serijalizuje fajl kroz `file.read()`, pa se
  forsiran `.size` iz `oversized_image` NE prenosi preko HTTP granice — server bi video stvaran (mali) size
  i kreirao Lead. Samo fajl sa stvarno > 5 MB sadržajem pouzdano okida size granu posle round-trip-a.
- `non_image_file` — `SimpleUploadedFile("x.pdf", b"%PDF-1.4...", content_type="application/pdf")` (MIME mismatch).

**Test konvencija:** SVI service POST testovi koriste `htmx_post` (fiksan IP `203.0.113.7`, `HTTP_HX_REQUEST="true"`);
multi-file idiom: `htmx_post(url, {**service_request_payload, "photos": [valid_image_jpeg, valid_image_png]})`
(lista pod jednim ključem → Django test client kodira više file part-ova → `request.FILES.getlist("photos")` vraća sve).
