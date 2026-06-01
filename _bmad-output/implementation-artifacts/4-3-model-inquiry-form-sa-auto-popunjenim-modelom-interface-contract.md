---
story-id: 4-3-model-inquiry-form-sa-auto-popunjenim-modelom
artifact: interface-contract
phase: TEA-RED
module: forms
author: Test Architect (🧪)
created: 2026-06-01
status: red-tests-written
---

# Story 4.3 — Interface Contract (TEA RED → Dev GREEN ugovor)

Ovaj dokument je **ugovor** koji TEA testovi specifikuju (RED) i koji Dev implementira (GREEN).
Sve potpise, putanje i string vrednosti su LOCKED testovima — Dev menja IMPLEMENTACIJU, NE ugovor.
REUSE 4.2 1:1 (SM-D10); jedina notifications.py izmena je `_build_subject` MODEL_INQUIRY grana (SM-D3).

---

## § 1 — Forms (`apps/forms/forms.py`)

DODAJ `ModelInquiryForm(forms.Form)` (NE diraj `ContactForm` — SM-D12). Polja:

| polje          | tip                     | required | widget                 | napomena |
|----------------|-------------------------|----------|------------------------|----------|
| `name`         | `forms.CharField(max_length=200)` | True  | TextInput              | mirror ContactForm; error `_("Unesite ime i prezime.")` |
| `email`        | `forms.EmailField`      | True     | EmailInput             | mirror ContactForm; error required+invalid |
| `phone`        | `forms.CharField(max_length=50)` | False | TextInput type=tel    | opciono |
| `message`      | `forms.CharField`       | True     | Textarea               | required=True NA FORMI (validacioni SOT), iako `Lead.message` blank=True |
| `product_slug` | `forms.SlugField(max_length=140)` | True | **`forms.HiddenInput`** | **`max_length=140`** (LOCK — poklapa `SluggedModel.slug`; Django SlugField default 50 bi odbio legitiman dug slug PRE view DB lookupa) |

- **Polja set je TAČNO** `{name, email, phone, message, product_slug}` — **NEMA** `model`/`product_name`
  data field (model display je readonly UX iz `{{ product.name }}` u template-u, NIJE izvor istine — SM-D2).
- Sve labele/error poruke kroz `gettext_lazy` (pune dijakritike č/ć/ž/š/đ; „E-pošta" sa š; NIKAD ćirilica/šišana latinica).
- HTML5 widget atributi = UX sloj.
- **Asercija lock (test):** `ModelInquiryForm().fields["product_slug"].max_length == 140` i
  `isinstance(widget, forms.HiddenInput)`.

---

## § 2 — Views (`apps/forms/views.py`)

DODAJ `model_inquiry_submit` FBV (REUSE `contact_submit` struktura; NE diraj `contact_submit`).

```
@require_POST
@ratelimit(key="ip", rate="5/m", block=False)
def model_inquiry_submit(request):
    if getattr(request, "limited", False):
        return HttpResponse(status=429)          # NE 403 (block=False — SM-D9)

    form = ModelInquiryForm(request.POST)
    if not form.is_valid():
        return render(request, "forms/partials/_model_inquiry_form_fields.html", {"form": form})   # 200

    product = Product.objects.filter(
        is_published=True, slug=form.cleaned_data["product_slug"]
    ).first()
    if product is None:
        # error partial 200 sa „Proizvod nije pronađen." (SM-D8); NE Lead, NE email
        return render(request, "forms/partials/_model_inquiry_form_fields.html",
                      {"form": form, "product_not_found": True})   # ILI ekvivalent koji nosi poruku

    lead = Lead.objects.create(
        form_type=Lead.FormType.MODEL_INQUIRY,
        name=form.cleaned_data["name"],
        email=form.cleaned_data["email"],
        phone=form.cleaned_data["phone"],
        message=form.cleaned_data["message"],
        locale=get_language(),
        ip_address=request.META.get("REMOTE_ADDR"),
        data={"product_slug": product.slug, "product_name": product.name},   # iz DB, NE POST
    )
    send_lead_email(lead)                          # save-before-send; povratak se NE rollback-uje
    return render(request, "forms/partials/model_inquiry_success.html",
                  {"lead": lead, "product": product})
```

- **Import (SM-D6, AUTORIZOVAN):** `from apps.products.models import Product` — READ-ONLY query
  (`.filter().first()`); NEMA `.save`/`.create` na Product, NEMA FK. Dokumentovan izuzetak
  forms→products u project-context.md.
- **429 mehanizam:** `block=False` + top-of-body `if getattr(request, "limited", False): return HttpResponse(status=429)`.
  Test asertuje 6. submit == 429, NIJEDAN 403.
- **Server slug re-validacija (SECURITY):** product se rezolvuje SAMO iz `cleaned_data["product_slug"]`
  lookupom na `is_published=True` queryset. Nepostojeći/unpublished → error partial 200, 0 Lead, 0 email.
  `data["product_name"]` + subject UVEK iz `product.name` (DB), NIKAD iz POST `product_name`/`model` polja (spoofing).
- **Invalid-product UX poruka:** error odgovor MORA sadržati string `„Proizvod nije pronađen."`
  (kroz `{% translate %}`; SM-D8 default). Dev bira kako se poruka nosi (kontekst flag / non_field_error /
  zaseban partial) — test asertuje samo da je string u response-u uz 0 Lead / 0 email.
- Save-before-send + email-failure: ako `send_lead_email` vrati False, Lead OSTAJE (count==1), success partial.

---

## § 3 — URLs (`apps/forms/urls.py`)

DODAJ (POSLE `contact_submit`):

```python
path("htmx/forme/upit-za-model/", views.model_inquiry_submit, name="model_inquiry_submit"),
```

- `config/urls.py` NETAKNUT (`apps.forms.urls` VEĆ mount-ovan u `i18n_patterns`).
- `reverse("forms:model_inquiry_submit")` pod `activate("sr")` → `/sr/htmx/forme/upit-za-model/`
  (hu → `/hu/...`, en → `/en/...`).
- GET → 405 (`@require_POST`).

---

## § 4 — Notifications (`apps/forms/notifications.py`) — JEDINA izmena

`_build_subject`, grana `MODEL_INQUIRY` (`:39-40`):

```python
# PRE:
if lead.form_type == Lead.FormType.MODEL_INQUIRY:
    return _("[Ćorić Agrar] Upit za model: %(name)s") % {"name": lead.name}
# POSLE (SM-D3):
if lead.form_type == Lead.FormType.MODEL_INQUIRY:
    return _("[Ćorić Agrar] Upit za model: %(name)s") % {
        "name": lead.data.get("product_name", lead.name)   # defensive fallback na lead.name
    }
```

- Subject string format ostaje isti; menja se SAMO IZVOR vrednosti (`lead.data["product_name"]` → Product.name).
- **Fallback grana (test-locked):** `data={}` (bez `product_name`) → `lead.data.get(..., lead.name)` →
  pada na `lead.name` BEZ `KeyError`/exception (OQ-5).
- `_resolve_recipient` NETAKNUT (MODEL_INQUIRY → CONTACT_EMAIL_TO VEĆ tačno — SM-D4).
- **Cross-story (4-1) regresija:** postojeći `test_email_subject_locale.py[model_inquiry]` (kreira Lead
  sa praznim data → fallback → lead.name → i dalje sadrži „[Ćorić Agrar]") i `test_send_lead_email.py[MODEL_INQUIRY]`
  (proverava SAMO recipient) OSTAJU ZELENI. NE menjati ih.

---

## § 5 — Templates / Partials (`templates/forms/partials/`)

### `_model_inquiry_form_fields.html` (REUSE `_contact_form_fields.html`)
- ROOT `<section id="product-inquiry">` (swap target — SM-D5; `hx-target="#product-inquiry"`, `hx-swap="outerHTML"`).
- **SVA polja kroz SIROVI `<input>`/`<textarea>` + `value="{{ form.X.value|default:'' }}"` idiom** (NIKAD
  `{{ form.X }}` field rendering — na product-page GET-u NEMA bound `form`, `{{ form.product_slug }}` bi izazvao
  AttributeError). Renderuje: `name`/`email`/`phone`/`message` (sirov input/textarea).
- **hidden `product_slug`:** `<input type="hidden" name="product_slug" value="{{ form.product_slug.value|default:product.slug }}">`
  (GET → fallback `product.slug`; **EKSPLICITNO ZABRANJENO** `{{ form.product_slug }}`).
- **readonly model display:** `{{ product.name }}` (div ILI readonly input `aria-readonly="true"`) — UX, NE source.
- **Regija #1 (in-form):** `{% if form.errors %}` → `<div role="alert" aria-live="assertive">` error summary
  sa per-field greškama.
- `{% csrf_token %}` + `hx-post="{% url 'forms:model_inquiry_submit' %}"` + `hx-target="#product-inquiry"` +
  `hx-swap="outerHTML"` + `htmx-indicator`.
- **Regija #2 (OOB, ODVOJEN):** `{% if request.htmx and form.errors %}` →
  `<div hx-swap-oob="innerHTML:#aria-live">{% translate "Greška pri slanju, proverite polja." %}</div>`.
- Standalone-renderable (None-safe za GET bez bound form).

### `model_inquiry_success.html` (REUSE `contact_success.html`)
- ROOT `<section id="product-inquiry">` (čisto zamenjuje formu).
- Poruka zahvalnosti kroz `{% translate %}`.
- **Telefon za hitne pozive (AC6):** `<a href="tel:+381...">` klikabilan, kroz `{% translate %}`, pun dijakritik;
  hardkodovan-translatable placeholder + TODO ka SiteSettings (3-4/8-9) ILI `{% site_setting %}` (SM-D9).
- **OOB polite (SAMO success):** `{% if request.htmx %}` →
  `<div hx-swap-oob="innerHTML:#aria-live">{% translate "Upit za model je poslat." %}</div>`.

**LOCKED OOB string vrednosti (testovi assertuju TAČAN tekst):**
- success: `Upit za model je poslat.`
- error: `Greška pri slanju, proverite polja.`
- invalid product: `Proizvod nije pronađen.`

---

## § 6 — Ratelimit / Cache (REUSE 4.2 — NE re-add)

- `config/settings/base.py` `CACHES` (locmem `default`) VEĆ postoji (Story 4.2 / SM-D7). NE re-add.
- Test REUSE autouse `_pin_and_clear_ratelimit_cache` (locmem + `cache.clear()` pre/posle) iz forms conftest-a.
- 5/m po IP-u; 6. submit istog IP-a u 1 min → 429.

---

## § 7 — Product detail wiring (`templates/products/product_detail.html`)

Popuni `{% block product_detail_inquiry %}` (`:57`, blok je U SAMOM `product_detail.html` — popuni-in-place,
NE „override"):

```django
{% block product_detail_inquiry %}
  <section id="product-inquiry" ...>
    {% include "forms/partials/_model_inquiry_form_fields.html" %}
  </section>
{% endblock %}
```

- `product`/`product.slug`/`product.name` dolaze iz `ProductDetailView` `context_object_name="product"`
  (nasleđuje se kroz `{% include %}`). `ProductDetailView` NETAKNUT (GET-only; NE prosleđuje `form`).
- Anchor `id="product-inquiry"` na obuhvatajućoj sekciji (swap target + skroluj-do-forme).
- **Vidljiv CTA (Task 10.2, OBAVEZAN):** `<a href="#product-inquiry">{% translate "Pošalji upit" %}</a>`
  (minimalan anchor button; YAGNI — bez dodatne logike).
- **Swap target sekcija:** `section#product-inquiry` — success/error partial-i imaju isti ROOT id.

**Regression (test-locked):** POST na `products:detail` → 405 (ProductDetailView NETAKNUT); GET unpublished → 404.

---

## § 8 — Test fixtures (`apps/forms/tests/conftest.py`)

PROŠIRENO (REUSE postojećih `recipient_env`/`htmx_post`/`superuser`/autouse `_pin_and_clear_ratelimit_cache`):
- `model_inquiry_payload` — `{name, email, phone, message}` (BEZ `product_slug`; popunjava se per-test iz
  `product.slug`). Pun dijakritik u `name`/`message`.
- `model_inquiry_submit_url` — `activate("sr")` + `reverse("forms:model_inquiry_submit")`.

**Test konvencija:** SVI model_inquiry POST testovi koriste `htmx_post` fixture (fiksan IP `203.0.113.7`,
`HTTP_HX_REQUEST="true"`) — izuzetak je deliberate non-HTMX test (sirov `client.post`).
Product data kroz `ProductFactory.create(name="Agri Tracking TB804")` / `create_unpublished(...)`.
