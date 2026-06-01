---
story-id: 4-3-model-inquiry-form-sa-auto-popunjenim-modelom
epic: 4
title: "Model Inquiry Form sa Auto-popunjenim Modelom"
status: ready-for-dev
module: forms
base-branch: master
created: 2026-06-01
author: SM (Scrum Master, 📋)
depends-on:
  - 4-1-lead-model-smtp-setup            # Lead model (FormType.MODEL_INQUIRY VEĆ postoji) + send_lead_email (DONE)
  - 4-2-opsta-kontakt-forma-fr-5         # kanonski HTMX form pattern (ratelimit block=False→429, OOB aria-live, partials) (DONE)
  - 2-7-product-detail-strana            # ProductDetailView + product_detail.html + {% block product_detail_inquiry %} (DONE)
forward-dep:
  - 4-6-htmx-form-patterns-aria-live-oob-rate-limiting   # standardizuje HTMX/ratelimit pattern kroz forme 4.2-4.5
---

# Story 4.3 — Model Inquiry Form sa Auto-popunjenim Modelom

## Opis / Description

As a **Marko**, I want **da pošaljem upit za konkretan model direktno sa stranice proizvoda, sa model poljem već popunjenim**, so that **brzo dobijam ponudu bez ponavljanja podataka o proizvodu**.

Ovo je **DRUGA forma story** Epic 4 i prvi put kad lead-forma renderuje NA POSTOJEĆOJ content strani (product detail iz Story 2.7), a ne na dedikovanoj Kontakt strani. Story 4.1 (Lead model + `send_lead_email`) i Story 4.2 (kanonski HTMX form pattern) su DONE i čine temelj — 4.3 **REUSE-uje 4.2 obrazac 1:1** (Django `forms.Form`, HTMX `hx-post` na zaseban `apps/forms` endpoint, ratelimit `block=False`→429, dve a11y regije, partials u `templates/forms/partials/`, save-before-send), a NE gradi ništa novo osim onoga što „auto-popunjen model" i „product strana mount" zahtevaju.

Forma ima **5 polja**: Ime i prezime\*, E-pošta\*, Telefon, **Model (prikazan readonly/display, NE editabilan kao podatak)**, Poruka\*. Submit ide preko HTMX (`hx-post` na `forms:model_inquiry_submit` → `/sr/htmx/forme/upit-za-model/`). Server **NE veruje** klijentskoj „model" vrednosti — product se rezolvuje server-side iz **trusted slug-a** (hidden `product_slug` polje koje view re-validira lookupom `Product.objects.filter(is_published=True, slug=...)`; 404/invalid → odbij). Lead se perzistira sa `form_type='model_inquiry'`, `data={"product_slug": "<slug>", "product_name": "<Product.name>"}` PRE poziva `send_lead_email(lead)`. Email subject je „[Ćorić Agrar] Upit za model: {Product.name}" (npr. „[Ćorić Agrar] Upit za model: Agri Tracking TB804"). Success state sadrži **telefon broj za hitne pozive**.

**Granica scope-a (KRITIČNO):**
- Self-contained kao 4.2; **Story 4.6** kasnije standardizuje HTMX form pattern (reusable mixin/decorator) + rate-limit kroz forme 4.2-4.5. 4.3 implementira ratelimit + OOB aria-live **inline** (per project-context.md security/a11y must-have); **NE** graditi prerano apstrakciju (YAGNI).
- **`Lead.FormType.MODEL_INQUIRY` VEĆ POSTOJI** (`apps/forms/models.py:34` — „model_inquiry") iz Story 4.1. **NEMA model promene, NEMA nove migracije** (SM-D1).
- `ProductDetailView` (`apps/products/views.py:73`) OSTAJE NETAKNUT (GET-only DetailView). Forma renderuje kroz `{% block product_detail_inquiry %}` (`templates/products/product_detail.html:57`) — submit ide na ZASEBAN `apps/forms` endpoint, NE na ProductDetailView (mirror 4.2 ContactView pravilo).
- **NE menja** `apps/forms/models.py` (Lead), `apps/forms/forms.py` (ContactForm netaknut — dodaje se NOVA `ModelInquiryForm`), `apps/forms/views.py` `contact_submit` (dodaje se NOVI `model_inquiry_submit`).

---

## Kontekst iz postojećeg koda (REAL reference — istraženo, NE pretpostavke)

> **Napomena o brojevima linija:** Svi `fajl:NN` line-ref-ovi u ovoj story-ji su INDIKATIVNI (npr. `models.py:34` za `FormType.MODEL_INQUIRY` je realno na `:33` — off-by-one). Sadržaj/identifikatori su tačni; orijentiši se po imenu simbola, ne po tačnom broju linije. NE jurcati svaki ref — koristi grep/IDE za precizan lokator.

### Lead model (`apps/forms/models.py` — Story 4.1, NETAKNUT)
- `Lead(TimestampedModel)`; **`FormType.MODEL_INQUIRY = "model_inquiry"` VEĆ deklarisan** (`:34`, DB vrednost LOWERCASE, LOCKED). Label: „Upit za model".
- Polja: `form_type`, `name` (CharField 200, obavezno), `email` (EmailField), `phone` (CharField 50, blank=True), `message` (TextField, blank=True), `data` (JSONField default=dict), `ip_address`, `locale` (default „sr"). **NEMA `photo`, NEMA FK, NEMA `get_absolute_url`.**
- **`data` shape ugovor za `model_inquiry`** (4-1-interface-contract.md § 7, LOCKED): `{"product_slug": "<slug>", "product_name": "<display>"}`. `product_slug` LOCKED (epics.md:802 zavisi); `product_name` je display string za subject.

### Email servis (`apps/forms/notifications.py` — Story 4.1) — ⚠️ JEDNA IZMENA POTREBNA
- `def send_lead_email(lead) -> bool` — SYNC, VIEW-CALLED, save-before-send. NETAKNUT potpis/semantika.
- `_resolve_recipient` (`:44`) **VEĆ mapira** `MODEL_INQUIRY → CONTACT_EMAIL_TO` (`:50-51`, deli sa kontaktom) — **Dev NE menja recipient logiku** (SM-D4).
- `_build_subject` (`:34`) trenutno za `MODEL_INQUIRY` (`:39-40`) vraća **`„[Ćorić Agrar] Upit za model: %(name)s" % {"name": lead.name}`** — koristi `lead.name` (IME OSOBE), ali AC zahteva **`Product.name`** (NAZIV MODELA, npr. „Agri Tracking TB804"). **⚠️ OVO JE JEDINA notifications.py izmena u 4.3 (SM-D3 — RESOLVED):** `_build_subject` za `MODEL_INQUIRY` MORA koristiti `lead.data.get("product_name")` umesto `lead.name`. Vidi SM-D3 + AC4.

### HTMX form pattern (`apps/forms/{forms,views,urls}.py` + `templates/forms/partials/` — Story 4.2, REUSE 1:1)
- `apps/forms/forms.py` → `ContactForm(forms.Form)` sa `name`/`email`/`phone`/`message`; labele/error kroz `gettext_lazy`, HTML5 widget atributi. **REUSE kao šablon za `ModelInquiryForm`** (dodaje hidden `product_slug` + readonly „model" display).
- `apps/forms/views.py` → `contact_submit` FBV: `@require_POST` + `@ratelimit(key="ip", rate="5/m", block=False)`; na vrhu `if getattr(request, "limited", False): return HttpResponse(status=429)`; bind forme → invalid renderuje error partial (200), valid radi `Lead.objects.create(...)` PA `send_lead_email(lead)` PA success partial. **REUSE 1:1 struktura za `model_inquiry_submit`.**
- `apps/forms/urls.py` → `app_name="forms"`; `path("htmx/forme/kontakt/", ...)`. **Dodati** `path("htmx/forme/upit-za-model/", views.model_inquiry_submit, name="model_inquiry_submit")`.
- `config/urls.py:31` → `path("", include("apps.forms.urls"))` VEĆ mount-ovan u `i18n_patterns` (Story 4.2). **NEMA promene config/urls.py** (novi path se dodaje samo u `apps/forms/urls.py`).
- `templates/forms/partials/contact_success.html` → ROOT `<section id="contact-form-section">` koji čisto zamenjuje formu (`hx-swap="outerHTML"`); `{% if request.htmx %}` OOB `hx-swap-oob="innerHTML:#aria-live"` polite najava. **Šablon za `model_inquiry_success.html`** (uz dodatak telefona za hitne pozive — AC6).
- `templates/forms/partials/_contact_form_fields.html` → bound form fields + in-form `<div role="alert" aria-live="assertive">` error summary (regija #1) + `{% csrf_token %}` + `hx-post`/`hx-target="#contact-form-section"`/`hx-swap="outerHTML"`/`htmx-indicator` + ODVOJEN `{% if request.htmx and form.errors %}` OOB polite blok (regija #2). **Šablon za `_model_inquiry_form_fields.html`.**
- `apps/forms/tests/conftest.py` → REUSE `recipient_env`, `htmx_post` (fiksan `ip="203.0.113.7"`, `HTTP_HX_REQUEST="true"`), `superuser`, `_pin_and_clear_ratelimit_cache` (autouse — locmem CACHES + `cache.clear()` po testu). **PROŠIRITI** sa `model_inquiry_payload` + `model_inquiry_submit_url` fixture-ima.
- `config/settings/base.py` → `CACHES` (locmem) VEĆ dodat (Story 4.2 Task 6.0). **NE re-add** (SM-D7).

### Product detail (Story 2.7 — žica se, NE duplira)
- `apps/products/views.py:73` → `ProductDetailView(DetailView)`, `model = Product`, `context_object_name = "product"`, `template_name = "products/product_detail.html"`, `get_queryset()` filtrira `is_published=True`. **OSTAJE NETAKNUT** (GET-only).
- `apps/products/urls.py:10` → `products:detail` na `proizvod/<slug:slug>/`.
- `apps/products/models.py` → `Product(SluggedModel, TimestampedModel)`: `name` (`:122`, CharField 200), `slug` (nasleđen iz `SluggedModel`, globally unique, db_index), `get_absolute_url()` (`:278` → `reverse("products:detail", slug=self.slug)`). **`product.slug` + `product.name` su trusted server-side source** (DetailView ih učitava iz DB).
- `templates/products/product_detail.html:57` → **`{% block product_detail_inquiry %}{% endblock %}`** — PRAZAN placeholder; mount point za formu (SM-D5 PINNED). `{{ product }}` je u kontekstu (`context_object_name="product"`).
- Test factory: `apps/products/tests/factories.py` → `ProductFactory.create()` (auto Brand, slug auto-gen iz name, `is_published=True`); `ProductFactory.create_unpublished()` (za 404/odbij test).

### CSS (REUSE — `static/css/components/contact-page.css`)
- `coric-contact-form__*` BEM (17 referenci) — input/textarea/error/alert/success/submit/field/label/required/indicator. **REUSE klase za model-inquiry formu** (ista vizuelna komponenta na product strani; novi `coric-model-inquiry__*` SAMO ako product-context layout traži — preferiraj reuse, YAGNI).

---

## Acceptance Criteria

**AC1 — ModelInquiryForm (server-side validation SOT + trusted slug).**
**Given** Lead model (FormType.MODEL_INQUIRY VEĆ postoji) iz Story 4.1
**When** kreiram `ModelInquiryForm` u `apps/forms/forms.py` (Django `forms.Form`) sa poljima `name` (obavezno), `email` (obavezno, EmailField), `phone` (opciono), `message` (obavezno), **`product_slug` (hidden, obavezno, `max_length=140` — trusted source za server-side product lookup; `max_length=140` se poklapa sa `SluggedModel.slug` da legitiman dug slug (>50 default) NE bude odbijen pre DB lookupa)**
**Then** sva user-facing labela/error poruka prolazi kroz `gettext_lazy` (pune dijakritike č/ć/ž/š/đ; NIKAD ćirilica/šišana latinica)
**And** prazno `name`/`email`/`message`/`product_slug` → `is_valid()` je `False` sa per-field greškama; nevalidan email → `False`; validan kompletan payload → `True`
**And** „model" vrednost koju korisnik vidi je **display-only** (readonly tekst, NIJE form field koji nosi podatak) — JEDINI podatak koji identifikuje proizvod je `product_slug` (hidden), koji server re-validira (AC2). Korisnik NE može da promeni koji se proizvod upituje editovanjem vidljivog readonly polja (security — SM-D2).
**And** `message` je `required=True` na FORMI iako je `Lead.message` `blank=True` na modelu (forma je validacioni SOT — mirror 4.2 AC1).

**AC2 — Server-side product rezolucija (security: NE veruj klijentu).**
**Given** `ModelInquiryForm` iz AC1
**When** view obradi POST
**Then** product se rezolvuje SERVER-SIDE iz `product_slug` (cleaned) lookupom `Product.objects.filter(is_published=True, slug=<slug>).first()` (ILI `get_object_or_404` ekvivalent na published queryset-u)
**And** ako proizvod NE postoji ILI nije published → submit se ODBIJA (NE kreira Lead, NE šalje email); view vraća error odgovor (200 partial sa porukom o nevalidnom proizvodu, ILI 404 — SM-D8 default: error partial 200 sa generičkom porukom „Proizvod nije pronađen.")
**And** `Lead.name`/`subject` koji se odnose na proizvod se NIKAD ne grade iz POST „model" stringa — uvek iz `Product.name` učitanog iz DB (mass-assignment / spoofing zaštita — mirror 4.2 server-sets-data pravilo).

**AC3 — HTMX POST endpoint + URL wiring.**
**Given** `ModelInquiryForm` iz AC1
**When** dodam `model_inquiry_submit` FBV u `apps/forms/views.py` + `path("htmx/forme/upit-za-model/", views.model_inquiry_submit, name="model_inquiry_submit")` u `apps/forms/urls.py`
**Then** `reverse("forms:model_inquiry_submit")` (uz aktivan `sr` locale) rezolvuje na `/sr/htmx/forme/upit-za-model/` (i18n-prefiksovan; `config/urls.py` VEĆ mount-uje `apps.forms.urls` — NEMA promene config/urls.py)
**And** endpoint prihvata SAMO POST (GET → 405, `@require_POST`)
**And** view radi save-before-send: `Lead.objects.create(form_type=Lead.FormType.MODEL_INQUIRY, name=..., email=..., phone=..., message=..., locale=get_language(), ip_address=<REMOTE_ADDR>, data={"product_slug": product.slug, "product_name": product.name})` PA TEK ONDA `send_lead_email(lead)`.

**AC4 — Uspešan submit (success partial + Lead.data + subject = Product.name).**
**Given** endpoint iz AC3 i postojeći published `Product` (npr. name=„Agri Tracking TB804", slug=„agri-tracking-tb804")
**When** pošaljem validan POST sa `name`/`email`/`phone`/`message` + `product_slug="agri-tracking-tb804"`
**Then** kreira se TAČNO 1 `Lead` red sa `form_type == "model_inquiry"`, core polja iz payload-a, i **`data == {"product_slug": "agri-tracking-tb804", "product_name": "Agri Tracking TB804"}`** (`product_slug` LOCKED — 4-1-interface-contract.md § 7)
**And** view vraća success partial (`templates/forms/partials/model_inquiry_success.html`) sa porukom zahvalnosti (kroz `{% translate %}`) — forma se HTMX-swap-uje; response NIJE full HTML page
**And** `send_lead_email(lead)` je pozvan (1 email u `mailoutbox`); **subject sadrži „[Ćorić Agrar] Upit za model: Agri Tracking TB804"** (= `Product.name`, NE ime osobe); `to == [settings.CONTACT_EMAIL_TO]`
**And** **`apps/forms/notifications.py` `_build_subject` za `MODEL_INQUIRY` je izmenjen** da koristi `lead.data.get("product_name", lead.name)` umesto `lead.name` (SM-D3) — ovo je JEDINA notifications.py izmena u 4.3.

**AC5 — Neuspešan submit (error rerender + dve a11y regije).**
**Given** endpoint iz AC3
**When** pošaljem nevalidan POST (prazno `name`/`email`/`message` ILI loš email ILI nepostojeći/unpublished `product_slug`)
**Then** view vraća form partial rerender (bound form sa `form.errors`), HTTP 200 (NE 4xx — HTMX swap error UI-a)
**And** rerender sadrži **U-FORMI** `<div role="alert" aria-live="assertive">` error summary (regija #1) sa per-field greškama (REUSE 4.2 obrazac)
**And** NIJEDAN `Lead` red NIJE kreiran i NIJEDAN email NIJE poslat (`mailoutbox` prazan)
**And** rerender ČUVA `product_slug` (hidden) + readonly model display tako da korisnik vidi isti model posle greške (UX — forma se ne „izgubi").

> **Dve ODVOJENE a11y regije (KRITIČNO — REUSE 4.2 SM-D12):** error odgovor MORA imati OBE: (1) **in-form** `role="alert"`/`aria-live="assertive"` summary UNUTAR form partial-a, I (2) **ODVOJEN** `hx-swap-oob="innerHTML:#aria-live"` blok ka `base.html` `aria-live="polite"` singletonu. Singleton OSTAJE `polite`. Success odgovor sadrži SAMO OOB polite najavu.

**AC6 — Success state sa telefonom za hitne pozive (epics.md 4.3).**
**Given** success partial iz AC4
**When** submit uspe
**Then** success partial prikazuje **telefon broj za hitne pozive** (npr. „Za hitne upite pozovite: +381 ...") kroz `{% translate %}` (puni dijakritik)
**And** telefon broj se renderuje kao klikabilan `tel:` link (mobile-friendly — Marko je sa terena)
**And** izvor broja: hardkodovan-translatable za v1 (SiteSettings dinamički broj je Story 3-4/8-9 — NE blokira 4.3; SM-D9) ILI iz `site_setting` template taga ako je već dostupan (Dev bira; default hardkodovan-translatable placeholder sa TODO ka SiteSettings).

**AC7 — OOB aria-live announcement (HTMX a11y).**
**Given** HTMX response patterns (project-context.md:184-194; REUSE 4.2 AC6)
**When** success ILI error response se vrati na HTMX zahtev
**Then** response uključuje `hx-swap-oob="innerHTML:#aria-live"` element ciljajući `base.html` `{% aria_live %}` singleton sa kratkom porukom (success: „Upit za model je poslat."; error: „Greška pri slanju, proverite polja.") kroz `{% translate %}`
**And** OOB blok je guarded `{% if request.htmx %}` (REUSE SM-D14 — ne curi u non-HTMX render).

**AC8 — Security must-haves (CSRF + ratelimit → HTTP 429; REUSE 4.2).**
**Given** project-context.md security must-have
**When** wire-ujem formu
**Then** form template sadrži `{% csrf_token %}` (HTMX šalje CSRF header)
**And** `model_inquiry_submit` ima `@ratelimit(key="ip", rate="5/m", block=False)` — **EKSPLICITNO `block=False`** (NE `block=True` → 403; vidi 4.2 SM-D9)
**And** na VRHU tela (PRE bind-a forme i PRE `Lead.objects.create`): `if getattr(request, "limited", False): return HttpResponse(status=429)`
**And** 6. uzastopni submit sa istog IP-a u 1 minuti → **HTTP 429** (5 prvih prolazi, 6. blokiran)
**And** ratelimit koristi Django `default` cache (locmem `CACHES` VEĆ u `config/settings/base.py` — Story 4.2; NE re-add); test pinuje cache + `cache.clear()` (REUSE autouse `_pin_and_clear_ratelimit_cache` iz forms conftest-a).

**AC9 — Wire u product detail stranu (NE duplira ProductDetailView).**
**Given** Story 2.7 `product_detail.html` + `{% block product_detail_inquiry %}` (`:57`)
**When** mount-ujem formu
**Then** `{% block product_detail_inquiry %}` se popunjava in-place kroz `{% include %}` forms partial-a (blok je U `product_detail.html` samom — popuni-in-place, NE „override" child template-a) tako da renderuje model-inquiry formu sa `product_slug`=`{{ product.slug }}` (hidden) + readonly model display=`{{ product.name }}`
**And** forma uključuje CTA „Pošalji upit" anchor/sekciju (id koji omogućava „skroluj do forme" — npr. `id="product-inquiry"`) I **vidljiv klikabilan CTA dugme** (postojeće u hero ILI minimalno dodato) sa `href="#product-inquiry"` koji skroluje do forme (epics.md 4.3: „klikne CTA Pošalji upit ILI skroluje do forme") — vidljiv CTA je OBAVEZAN minimalan element (Task 10.2), ne samo scroll anchor
**And** `ProductDetailView` OSTAJE GET-only NETAKNUT; POST na `products:detail` i dalje vraća 405 (regression)
**And** GET `/sr/proizvod/<slug>/` (200) prikazuje stranu sa aktivnom (NE disabled) formom; readonly model polje prikazuje `Product.name`.

**AC10 — i18n + dijakritike + lint.**
**Given** project-context.md i18n + anti-pattern pravila
**When** dodam sve nove stringove
**Then** SVE user-facing strings (labele, error poruke, success/aria/telefon poruke) idu kroz `gettext_lazy`/`{% translate %}` sa punim dijakritikama; NIKAD ćirilica, NIKAD šišana latinica
**And** `just lint` (ruff + djade) clean; `just test` (novi forms + products regresija) prolazi
**And** ako novi `.po` stringovi → `just messages` (makemessages + compilemessages za sr/hu/en).

---

## Tasks / Subtasks (TDD-ordered: TEA RED → Dev GREEN)

> **Disciplina (project-context.md:293-298):** TEA agent piše testove (RED phase) PRVI; Dev agent piše implementaciju (GREEN); Dev NIKAD ne piše testove. Testovi se commit-uju pre implementacije. Ako TEA testovi failuju u Dev fazi → story `paused`, ne maskirati greške.

### Task 1 — (TEA, RED) Fixtures + ModelInquiryForm testovi
- [ ] 1.1 Proširi `apps/forms/tests/conftest.py` (REUSE postojeći `recipient_env`/`htmx_post`/`superuser`/autouse `_pin_and_clear_ratelimit_cache`) sa: `model_inquiry_payload` fixture (`{"name": "Marko Marković", "email": "marko@example.com", "phone": "+381641234567", "message": "Zanima me ovaj model.", "product_slug": "<slug>"}` — slug se popuni iz fixture product-a) i `model_inquiry_submit_url` fixture (`activate("sr")` + `reverse("forms:model_inquiry_submit")`).
- [ ] 1.2 Novi `apps/forms/tests/test_model_inquiry_form.py` (AC1): polja postoje (`name`/`email`/`phone`/`message`/`product_slug`); `name`/`email`/`message`/`product_slug` obavezni; `phone` opciono; `product_slug` je `HiddenInput` (NIJE vidljivo editabilno polje koje korisnik popunjava); **asertuj `form.fields["product_slug"].max_length == 140`** (lock — sprečava regresiju na Django default 50, koji bi odbio legitiman dug slug); nevalidan email → invalid; validan payload → valid; labele/errori kroz gettext (substring pune dijakritike, NEMA ćirilice). **Model display NIJE form field koji nosi podatak** — asertuj da forma NEMA editabilno `model`/`product_name` polje koje bi server čitao kao izvor istine (samo `product_slug` hidden je izvor).

### Task 2 — (TEA, RED) HTMX endpoint: success + Lead.data + subject = Product.name

> **Napomena (Tasks 2/3/4 — ratelimit determinizam):** SVI `model_inquiry` POST testovi MORAJU koristiti `htmx_post` fixture (fiksan IP `203.0.113.7`, `HTTP_HX_REQUEST="true"`) — **NE** sirov `client.post`. Iako autouse `_pin_and_clear_ratelimit_cache` čisti cache po testu, fiksan IP čini per-IP ratelimit brojač deterministićnim (5/m granica se ne troši slučajnim/promenljivim REMOTE_ADDR-om) i garantuje HX-Request header za HTMX-grananje. Jedini izuzetak su EKSPLICITNI non-HTMX testovi (npr. Task 4.1 „non-HTMX POST bez HX-Request") koji namerno koriste sirov `client.post` da provere odsustvo OOB bloka.

- [ ] 2.1 Novi `apps/forms/tests/test_model_inquiry_view.py` (AC3/AC4):
  - `reverse("forms:model_inquiry_submit")` rezolvuje (NoReverseMatch RED dok URL ne postoji); **AKTIVIRAJ locale PRE asercije** (`activate("sr")`/`translation.override("sr")`) → URL je `/sr/htmx/forme/upit-za-model/`. (low) opciono potvrdi `hu`/`en` prefiks.
  - GET → 405 (`@require_POST`).
  - **Success (AC4):** kreiraj published `Product` (`ProductFactory.create(name="Agri Tracking TB804")`); validan HTMX POST sa `product_slug=product.slug` → 200; `Lead.objects.count() == 1`; `lead.form_type == Lead.FormType.MODEL_INQUIRY`; core polja iz payload-a; `lead.data == {"product_slug": product.slug, "product_name": "Agri Tracking TB804"}`; `lead.locale == "sr"`; `lead.ip_address` popunjen; success partial korišćen (`templates/forms/partials/model_inquiry_success.html`); `len(mailoutbox) == 1`; **`mailoutbox[0].subject` sadrži „[Ćorić Agrar] Upit za model: Agri Tracking TB804"** (Product.name, NE „Marko Marković"); `mailoutbox[0].to == [settings.CONTACT_EMAIL_TO]` (sa `recipient_env`).
- [ ] 2.2 Test (AC4 partial): success response NIJE full page (NE sadrži `<html`/`<head>` — substring/`render_to_string` konvencija mirror 4.2). **Simetrično:** error response je takođe partial (NE `<html`/`<head>`).
- [ ] 2.3 Test (AC4 subject regression — notifications.py): direktan unit test `_build_subject` ILI `send_lead_email` za `MODEL_INQUIRY` lead sa `data={"product_name": "Agri Tracking TB804"}` → subject sadrži „Agri Tracking TB804" (NE `lead.name`). **Lock-uje SM-D3 izmenu** (`lead.data.get("product_name", lead.name)`). **EKSPLICITNO uključi i no-`product_name`-key fallback test:** `MODEL_INQUIRY` lead sa `data={}` (ILI `data` bez `product_name` ključa) → subject pada nazad na `lead.name` BEZ `KeyError`/exception-a (defensive fallback grana). Ovo direktno pokriva isti put kao 4-1 `test_email_subject_locale.py[model_inquiry]` (vidi napomenu pod Task 8.1).

### Task 3 — (TEA, RED) Security rezolucija + error rerender + XSS
- [ ] 3.1 `apps/forms/tests/test_model_inquiry_security.py` (AC2 — KRITIČNO):
  - **Nepostojeći slug:** validan POST sa `product_slug="ne-postoji"` → submit ODBIJEN; `Lead.objects.count() == 0`; `len(mailoutbox) == 0`; error odgovor (200 partial sa porukom „Proizvod nije pronađen." per SM-D8 default).
  - **Unpublished product:** `ProductFactory.create_unpublished()` → POST sa tim slug-om → ODBIJEN (isto kao nepostojeći; `is_published=True` filter ne sme da ga vidi); `Lead.objects.count() == 0`.
  - **Spoofing:** POST u kome korisnik pošalje DODATNO polje `product_name`/`model` sa lažnom vrednošću (npr. `"GRATIS PROIZVOD"`) → server IGNORIŠE; `lead.data["product_name"]` i subject su iz `Product.name` (DB), NE iz POST stringa. Asertuj da lažna vrednost NIJE u `lead.data` ni u subject-u.
- [ ] 3.2 `apps/forms/tests/test_model_inquiry_view.py` Error (AC5): nevalidan POST (prazno `name`) sa validnim `product_slug` → 200 (NE 4xx); `Lead.objects.count() == 0`; `len(mailoutbox) == 0`; rerender sadrži `role="alert"` + `aria-live="assertive"` + error tekst; rerender ČUVA `product_slug` (hidden value prisutan) + readonly model display (`Product.name` u rerender-u).
- [ ] 3.3 Test (AC5 XSS insurance — javna unauth forma): nevalidan POST sa `name`/`message` koji sadrži `<script>alert(1)</script>` → error rerender auto-escape-uje (Django default) — asertuj escaped `&lt;script&gt;`, NE sirov `<script>`.

### Task 4 — (TEA, RED) OOB aria-live + email-failure + ratelimit (REUSE 4.2 konvencije)
- [ ] 4.1 `apps/forms/tests/test_model_inquiry_aria_live.py` (AC7 + AC5 dve regije): success response sadrži `hx-swap-oob="innerHTML:#aria-live"` + success najavu (SAMO OOB polite); error response sadrži OBE — (a) in-form `role="alert"`/`aria-live="assertive"` I (b) ODVOJEN `hx-swap-oob` polite; OOB se NE pojavljuje u non-HTMX render-u (guard `{% if request.htmx %}`); singleton ostaje `polite`. (low) Non-HTMX POST (običan client, bez `HX-Request`) → response NE sadrži `hx-swap-oob`.
- [ ] 4.2 `apps/forms/tests/test_model_inquiry_email_failure.py` (AC4/4.2 SM-D5 obrazac): `monkeypatch`/`mock.patch` na `apps.forms.views.send_lead_email` → `False`; validan submit → Lead i dalje postoji (count==1); posetilac i dalje dobija success partial. (Mock SAMO servis-povratnu vrednost, NE ORM.)
- [ ] 4.3 `apps/forms/tests/test_model_inquiry_ratelimit.py` (AC8): 5 submit-a OK (NIJE 429); 6. submit sa istog IP-a u istom minutu → `status_code == 429` (NE 403 — `block=False` + `request.limited`). REUSE autouse `_pin_and_clear_ratelimit_cache` (locmem CACHES + clear) + `htmx_post` fixture (fiksan IP). (CSRF-token-u-renderovanoj-formi asercija je RELOCIRANA u Task 5.1 — zavisi od product-page wiringa, ne od ratelimita; ovaj test ostaje fokusiran SAMO na ratelimit.)

### Task 5 — (TEA, RED) Wire u product detail (a11y/regression)
- [ ] 5.1 `apps/forms/tests/test_model_inquiry_page_wired.py` ILI `apps/products/tests/` (AC9): **plain `client.get(product_url)` BEZ ikakvog `form` injektovanog u kontekst** — `ProductDetailView` NE prosleđuje `form` (GET-only DetailView, NETAKNUT); partial se renderuje korektno kroz Django None-safe rezoluciju varijabli + `{{ product.slug }}`/`{{ product.name }}` fallback-e (sirov-`<input>` idiom, vidi Task 9.1/SM-D5). GET `/sr/proizvod/<slug>/` (published product) → 200; renderovana strana sadrži model-inquiry formu (NEMA `disabled` na poljima/submit-u); sadrži `hx-post` ka `forms:model_inquiry_submit`; hidden `product_slug` value == `product.slug`; readonly model display sadrži `product.name`; anchor/sekcija `id="product-inquiry"` postoji (za „skroluj do forme"); **CSRF token prisutan u renderovanoj formi (`csrfmiddlewaretoken` u GET `/sr/proizvod/<slug>/` HTML-u)** — relociran iz Task 4.3 (zavisi od product-page wiringa, ne od ratelimita). **Regression:** POST na `products:detail` (ProductDetailView) i dalje vraća 405 (NETAKNUT).
- [ ] 5.2 (low, AC9) Test: forma se NE renderuje za unpublished product (ProductDetailView ionako 404-uje unpublished — potvrdi da GET unpublished slug → 404, forma nedostupna).

### Task 6 — (Dev, GREEN) `apps/forms/forms.py` — ModelInquiryForm
- [x] 6.1 Dodaj `ModelInquiryForm(forms.Form)` (NE diraj `ContactForm`): `name`/`email`/`phone`/`message` (mirror ContactForm — `name`/`email`/`message` `required=True`, `phone` `required=False`); **`product_slug = forms.SlugField(max_length=140, required=True, widget=forms.HiddenInput)`** (trusted source — `max_length=140` EKSPLICITNO jer Django `forms.SlugField` default je `max_length=50`, a `Product.slug` (`SluggedModel.slug`) je `max_length=140`; bez ovoga legitiman proizvod sa dugim slug-om (>50) bi bio odbijen na nivou forme PRE view DB lookupa → zbunjujuća lažna greška). Labele/error kroz `gettext_lazy` (pune dijakritike). HTML5 widget atributi (`type=email`, `required`) = UX sloj. Model display NIJE form field (renderuje se u template-u kao readonly tekst iz `{{ product.name }}` — NE kao input čiju vrednost server čita).

### Task 7 — (Dev, GREEN) `apps/forms/views.py` + `apps/forms/urls.py`
- [x] 7.1 `apps/forms/views.py`: dodaj `model_inquiry_submit` FBV (REUSE `contact_submit` struktura) — `@require_POST` + `@ratelimit(key="ip", rate="5/m", block=False)`; na vrhu `if getattr(request, "limited", False): return HttpResponse(status=429)`; bind `ModelInquiryForm(request.POST)`; ako invalid → render error partial (200, bound form); ako valid → **rezolvuj product server-side:** `product = Product.objects.filter(is_published=True, slug=form.cleaned_data["product_slug"]).first()`; ako `product is None` → render error partial (200) sa porukom „Proizvod nije pronađen." (SM-D8; NE kreiraj Lead, NE šalji email); inače `Lead.objects.create(form_type=Lead.FormType.MODEL_INQUIRY, name=..., email=..., phone=..., message=..., locale=get_language(), ip_address=request.META.get("REMOTE_ADDR"), data={"product_slug": product.slug, "product_name": product.name})`; `send_lead_email(lead)`; render success partial (sa product u kontekstu za potencijalan re-render). **Import:** `from apps.products.models import Product` (dep boundary forms→products je READ-ONLY query, dokumentovan SM-D6 — mirror brands→products 2.6 izuzetak; NEMA `.save`/`.create` na Product, NEMA FK).
- [x] 7.2 `apps/forms/urls.py`: dodaj `path("htmx/forme/upit-za-model/", views.model_inquiry_submit, name="model_inquiry_submit")` (POSLE postojećeg `contact_submit`). `config/urls.py` NETAKNUT (`apps.forms.urls` VEĆ mount-ovan).

### Task 8 — (Dev, GREEN) `apps/forms/notifications.py` — subject = Product.name
- [x] 8.1 `apps/forms/notifications.py` `_build_subject` (`:39-40`): za `Lead.FormType.MODEL_INQUIRY` zameni `lead.name` sa `lead.data.get("product_name", lead.name)` (SM-D3 — defensive fallback na `lead.name` ako ključ nedostaje). Subject postaje „[Ćorić Agrar] Upit za model: {product_name}". **JEDINA notifications.py izmena;** `_resolve_recipient` NETAKNUT (MODEL_INQUIRY → CONTACT_EMAIL_TO VEĆ tačno — SM-D4).
  - **Cross-story regresija (4-1) — NE pucaju, ali TEA MORA da ih pokrene da potvrdi zeleno (BEZ izmene tih testova):** postojeći 4-1 testovi `test_email_subject_locale.py[model_inquiry]` i `test_send_lead_email.py[MODEL_INQUIRY]` ostaju zeleni posle ove izmene. Prvi kreira `Lead` sa praznim `data`, pa `lead.data.get("product_name", lead.name)` fallback vraća `lead.name`, a test asertuje samo `"[Ćorić Agrar]" in subject` → i dalje prolazi. Drugi proverava SAMO recipient-a (`to`), koji je NETAKNUT. Nije potrebna nikakva izmena 4-1 testova; samo ih RUN-uj u Dev GREEN da potvrdiš da je `just test` zelen.

### Task 9 — (Dev, GREEN) Forms partials (fields + success)
- [x] 9.1 `templates/forms/partials/_model_inquiry_form_fields.html` (REUSE `_contact_form_fields.html` struktura): ROOT `<section id="product-inquiry">` (swap target — SM-D5); **MANDATORNO: SVA polja se renderuju kao SIROVI `<input>`/`<textarea>` sa `value="{{ form.X.value|default:'' }}"` idiomom (REUSE 4.2 `_contact_form_fields.html`), NIKAD kroz Django field rendering `{{ form.name }}`/`{{ form.as_p }}`** — jer na product-page GET-u NEMA bound `form` instance (SM-D5), pa bi `{{ form.product_slug }}` izazvao AttributeError; sirov `<input>` + `{% if form.errors %}` guard degradira graciozno (`{{ form.X.value|default:'' }}` → prazno kad je `form` odsutan). Renderuje: user polja `name`/`email`/`phone`/`message` (sirov input/textarea) + **hidden `product_slug`** (`<input type="hidden" name="product_slug" value="{{ form.product_slug.value|default:product.slug }}">` — na GET-u `form` odsutan → pada na `product.slug`; **EKSPLICITNO ZABRANJENO** `{{ form.product_slug }}`) + **readonly model display** (`<div>{% translate "Model" %}: {{ product.name }}</div>` ILI readonly input sa `value="{{ product.name }}"` `readonly` `aria-readonly="true"` — NIJE source-of-truth, samo UX) + per-field greške + in-form `<div role="alert" aria-live="assertive">` error summary (regija #1) + `{% csrf_token %}` + `hx-post="{% url 'forms:model_inquiry_submit' %}"`/`hx-target="#product-inquiry"`/`hx-swap="outerHTML"`/`htmx-indicator` + ODVOJEN `{% if request.htmx and form.errors %}` OOB polite blok (regija #2). Standalone-renderable.
- [x] 9.2 `templates/forms/partials/model_inquiry_success.html` (REUSE `contact_success.html`): ROOT `<section id="product-inquiry">` (čisto zamenjuje formu); poruka zahvalnosti (`{% translate %}`) + **telefon za hitne pozive** (AC6 — `<a href="tel:+381...">` klikabilan, kroz `{% translate %}`, puni dijakritik; hardkodovan-translatable placeholder + TODO ka SiteSettings 3-4/8-9 ILI `{% site_setting %}` ako dostupan — SM-D9); `{% if request.htmx %}` OOB polite success najava.

### Task 10 — (Dev, GREEN) Wire u product detail stranu
- [x] 10.1 Popuni `{% block product_detail_inquiry %}` u `templates/products/product_detail.html` (`:57`) — **blok živi U SAMOM `product_detail.html` (nije child template), pa se popuni in-place kroz `{% include %}`, NE „override"** — `{% include "forms/partials/_model_inquiry_form_fields.html" %}` (prosledi `product` u kontekst; `form` se konstruiše u view-u za GET ILI partial sam renderuje praznu formu sa `product.slug`). **Odluka (SM-D5):** product detail GET je `ProductDetailView` (NETAKNUT) — partial NEMA bound `form` na GET-u, pa fields partial mora renderovati prazna polja + hidden `product_slug` iz `{{ product.slug }}` direktno (NE oslanjati se na `form` instancu na GET-u; `form.errors` guard već handluje `form is None` → prazno). Anchor `id="product-inquiry"` na obuhvatajućoj sekciji za „skroluj do forme".
- [x] 10.2 (AC9 — OBAVEZAN minimalan element) Dodaj VIDLJIV CTA „Pošalji upit" anchor dugme sa `href="#product-inquiry"` (skroluje do forme). **NIJE opciono** — epics.md 4.3 intent („klikne CTA Pošalji upit") zahteva vidljiv klikabilan element, ne samo scroll anchor sekciju. Ako hero već ima CTA prostor (hero_overlay_card) — wire tamo; inače minimalan anchor button u hero/postojećoj sekciji. Drži minimalno (YAGNI — jedan `<a href="#product-inquiry">` button, BEZ dodatne logike). `{% translate %}` za labelu (puni dijakritik). `ProductDetailView` NETAKNUT.

### Task 11 — (Dev, GREEN) CSS + i18n + lint + verifikacija
- [x] 11.1 REUSE `coric-contact-form__*` BEM iz `static/css/components/contact-page.css` za model-inquiry formu (ista vizuelna komponenta). Ako product-context layout traži dodatni stil (readonly model polje, telefon CTA, anchor offset za sticky header scroll) → proširi `contact-page.css` ILI nova `model-inquiry.css` `@import` u `main.css`; `var(--token)` umesto magic vrednosti; NIKAD inline style.
- [x] 11.2 `just messages` ako su dodati novi `{% translate %}`/`gettext_lazy` stringovi (makemessages + compilemessages za sr/hu/en).
- [x] 11.3 `just lint` (ruff + djade) clean; `just test` (forms + products regresija) zelen. Self-review checklist (project-context.md:425): CSRF+ratelimit ✓, aria-live OOB ✓, gettext sve ✓, no inline style ✓, no defensive validation na internim pozivima ✓, dep boundary forms→products READ-ONLY dokumentovan ✓.

---

## SM Decisions (log)

- **SM-D1 (NEMA model promene / migracije) — KRITIČNO:** `Lead.FormType.MODEL_INQUIRY = "model_inquiry"` VEĆ POSTOJI (`apps/forms/models.py:34`, dodato u Story 4.1). 4.3 NE menja `Lead` model, NE dodaje FormType member, **NE generiše migraciju.** (Napomena za potpunost: čak i da je trebalo dodati TextChoices member, promena `choices` na CharField-u u modernom Django-u NE menja DB šemu — `makemigrations` bi generisao no-op `AlterField`; ali ovde NIJE ni potreban jer member već postoji.) Dakle 4.3 = 0 model fajl izmena, 0 migracija.
- **SM-D2 (model source-of-truth = SECURITY) — KRITIČNO:** AC (epics.md:801) kaže „Model auto-popunjen iz `request.path` parsiranja, readonly". Readonly HTML polje je i dalje editabilno od strane napadača (DevTools/curl), pa server **NE sme verovati** vidljivoj „model" vrednosti. Rešenje: jedini podatak koji identifikuje proizvod je **hidden `product_slug`**, koji view **re-validira** lookupom `Product.objects.filter(is_published=True, slug=...)` (404/odbij ako ne postoji/unpublished). `Product.name` (za display + subject + `data["product_name"]`) se UVEK čita iz DB, NIKAD iz POST stringa. Mass-assignment zaštita mirror 4.2 (forms.Form, server sets form_type/data/locale/ip). Readonly model display u UI-u je čisto UX (korisnik vidi šta upituje), NE izvor istine.
- **SM-D3 (subject = Product.name, NE lead.name) — RESOLVED (notifications.py izmena):** `_build_subject` (`apps/forms/notifications.py:39-40`) trenutno za `MODEL_INQUIRY` koristi `lead.name` (ime OSOBE) → subject bi bio „Upit za model: Marko Marković". AC4 (epics.md:803) zahteva „Upit za model: Agri Tracking TB804" (NAZIV MODELA). Izmena: `lead.data.get("product_name", lead.name)` (defensive fallback na `lead.name` ako `product_name` ključ nedostaje — npr. legacy lead). **OVO JE JEDINA notifications.py izmena u 4.3.** Subject string format ostaje isti, menja se SAMO izvor vrednosti.
- **SM-D4 (recipient NETAKNUT):** `_resolve_recipient` VEĆ mapira `MODEL_INQUIRY → CONTACT_EMAIL_TO` (`:50-51`, deli sa kontaktom — 4-1 OQ-2). Dev NE menja recipient logiku.
- **SM-D5 (mount point + swap target PINNED):** Forma renderuje kroz `{% block product_detail_inquiry %}` (`templates/products/product_detail.html:57` — PRAZAN placeholder iz Story 2.7). Swap target je obuhvatajuća sekcija `id="product-inquiry"` (success/error partial-i imaju isti ROOT id; `hx-target="#product-inquiry"`, `hx-swap="outerHTML"`). Na GET (ProductDetailView, NETAKNUT) NEMA bound `form` instance → fields partial renderuje prazna polja + hidden `product_slug` direktno iz `{{ product.slug }}`; `{% if form.errors %}` guard handluje `form is None`. **`product`/`product.slug`/`product.name` dolaze iz `ProductDetailView` `context_object_name="product"` i dostupni su u uključenom partial-u kroz nasleđeni kontekst (`{% include %}` nasleđuje parent kontekst).** Fields partial MORA koristiti sirov-`<input>` idiom (NE `{{ form.product_slug }}` field rendering — izazvao bi AttributeError kad je `form` odsutan na GET-u; vidi Task 9.1). `#product-inquiry` anchor omogućava „skroluj do forme" CTA.
- **SM-D6 (dep boundary forms→products READ-ONLY) — RESOLVED (formalno dokumentovan izuzetak):** `apps/forms/views.py` SME importovati `Product` iz `apps.products.models` za READ-ONLY lookup (`Product.objects.filter(...).first()`) — mirror `brands→products` 2.6 SM-D16 izuzetka (view-layer-only, NEMA `.save`/`.create`, NEMA FK iz forms→products). Coupling je query-only i ne krši jednosmernu zavisnost. Product context u Lead-u ostaje slug-u-JSON (`data["product_slug"]`), NE FK (4-1 SM-D3a). **Izuzetak je sada FORMALNO DOKUMENTOVAN** u `_bmad-output/project-context.md` sekciji „🚫 Anti-pattern: Cross-boundary import" (App dependency rules) kao eksplicitan `forms → products` READ-ONLY view-layer izuzetak, paralelan postojećem `brands → products` 2.6 SM-D16 unosu — per pravilo „Ako naletiš na novi pattern koji se ponavlja a nije ovde dokumentovan — update ovaj fajl kao deo svoje story-je". Import je time **AUTORIZOVAN za Dev GREEN** (Task 7.1).
- **SM-D7 (CACHES NE re-add):** `config/settings/base.py` VEĆ ima eksplicitan locmem `CACHES` (Story 4.2 Task 6.0 / SM-D10). 4.3 NE re-add. Test REUSE autouse `_pin_and_clear_ratelimit_cache` iz forms conftest-a (već postoji).
- **SM-D8 (invalid product UX) — OQ:** ako `product_slug` ne rezolvuje (nepostojeći/unpublished), default je **error partial (200)** sa generičkom porukom „Proizvod nije pronađen." (HTMX swap-uje error UI; NE kreira Lead, NE šalje email). Alternativa: `Http404`. Default = error partial 200 (konzistentno sa 4.2 error-UX obrascem — HTMX uvek partial, NE 4xx za swap). Step-02/Mihas može override-ovati.
- **SM-D9 (telefon za hitne pozive — izvor) — OQ:** AC6 zahteva telefon u success state-u. Default: **hardkodovan-translatable placeholder** (`{% translate %}` + `tel:` link) sa TODO komentarom ka SiteSettings (Story 3-4 model postoji; dinamičko vezivanje je 8-9 navigation/contact admin). Alternativa: koristi `{% site_setting "phone" %}` template tag ako je već renderovan na strani (3-4). Default = hardkodovan-translatable da 4.3 NE blokira na SiteSettings wiring-u (YAGNI). Dev bira; ako koristi `site_setting`, dokumentuj.
- **SM-D10 (REUSE 4.2 1:1):** ratelimit `block=False`→429 (SM-D9 iz 4.2), dve a11y regije (in-form assertive + OOB polite guarded), partials u `templates/forms/partials/`, save-before-send, gettext + pune dijakritike, CSRF, `htmx-indicator` min 200ms — sve REUSE iz 4.2. 4.3 NE uvodi novi pattern; Story 4.6 standardizuje shared mixin/decorator (NE sada — YAGNI).
- **SM-D11 (5 polja per epics.md):** epics.md:801 navodi 5 polja (Ime, Email, Telefon, Model, Poruka). „Model" je readonly DISPLAY (NE form-data field) + hidden `product_slug` (data field). Forma ima 4 user-popunjiva polja + 1 hidden + 1 display — vizuelno 5 „polja" za Marka, ali samo `product_slug` (hidden) je product-identitet source.
- **SM-D12 (ContactForm/contact_submit NETAKNUTI):** 4.3 DODAJE `ModelInquiryForm` + `model_inquiry_submit` + nove partial-e; NE menja `ContactForm`, `contact_submit`, `_contact_form_fields.html`, `contact_success.html` (Story 4.2 vlasništvo). Regression: 4.2 testovi ostaju zeleni.
- **SM-D13 (double-submit) — KNOWN MINOR (v1, forward → 4.6):** brz dvostruki klik može kreirati 2 Lead reda (isto kao 4.2 SM-D13). Prihvatljivo za v1; forward na 4.6 (`hx-disabled-elt` + opcioni dedup). Samo logovano, NE rešavano.

## Open Questions
- **OQ-1 (SM-D8) — RESOLVED:** invalid/unpublished `product_slug` UX — error partial 200 vs Http404. **Default PRIHVAĆEN: error partial 200 sa porukom „Proizvod nije pronađen."** (konzistentno sa 4.2 HTMX swap error-UX obrascem; NE kreira Lead, NE šalje email). AC2 već pinuje ovaj default. Zatvoreno.
- **OQ-2 (SM-D9) — RESOLVED:** telefon za hitne pozive — hardkodovan-translatable placeholder vs `{% site_setting %}` (3-4). **Default PRIHVAĆEN: hardkodovan-translatable `tel:` placeholder + TODO komentar ka SiteSettings** (3-4/8-9), da 4.3 NE blokira na SiteSettings wiringu (YAGNI). AC6 već pinuje ovaj default; Dev SME upotrebiti `{% site_setting %}` ako je već dostupan (dokumentovati). Zatvoreno.
- **OQ-3 (SM-D6) — RESOLVED:** dep boundary forms→products READ-ONLY query — izuzetak je formalno dokumentovan u `_bmad-output/project-context.md` (sekcija „🚫 Anti-pattern: Cross-boundary import", eksplicitan `forms → products` READ-ONLY view-layer unos, paralelan `brands → products` 2.6 SM-D16). Import je AUTORIZOVAN za Dev GREEN (view-layer-only, READ-ONLY, NEMA FK/write). Step-02 potvrda zatvorena.
- **OQ-4 (AC9 CTA):** da li product hero VEĆ ima CTA „Pošalji upit" prostor (hero_overlay_card) ili 4.3 dodaje minimalan anchor button? Dev finalizuje u GREEN (Task 10.2); default minimalan `href="#product-inquiry"` anchor ako hero nema slot.
- **OQ-5 (SM-D3 fallback):** `_build_subject` defensive fallback `lead.data.get("product_name", lead.name)` — da li je fallback na `lead.name` poželjan za legacy/malformed lead, ili treba generička „Upit za model" bez naziva? Default: fallback na `lead.name` (graceful, nikad prazan subject).
