---
story-id: 4-2-opsta-kontakt-forma-fr-5
phase: TEA-RED
author: Test Architect (🧪)
created: 2026-06-01
purpose: >
  Interface contract koji TEA testovi (RED) asertuju i koji Dev (GREEN) MORA implementirati.
  Sve potpise/putanje/dekoratore izveden iz story AC1-AC9 + Task 5-9 + SM-D6/D9/D10/D12.
---

# Interface Contract — Story 4.2 (Opšta Kontakt Forma, FR-5)

Ovaj dokument je SPECIFIKACIJA koju Dev (GREEN faza) implementira da bi TEA testovi prošli.
Testovi su SOT za ponašanje; ovaj contract je njihova čitljiva projekcija. NIČIM se ne sme
odstupiti bez SM odluke.

---

## 1. `apps/forms/forms.py` — `ContactForm`

```python
class ContactForm(forms.Form):  # ILI forms.ModelForm(Lead, fields=["name","email","phone","message"])
    name    = forms.CharField(required=True)      # label _("Ime i prezime")
    email   = forms.EmailField(required=True)     # label _("E-pošta")
    phone   = forms.CharField(required=False)     # label _("Telefon")  — OPCIONO
    message = forms.CharField(required=True, widget=forms.Textarea)  # label _("Poruka")
```

- **`message` je `required=True` NA FORMI** iako je `Lead.message` `blank=True` na modelu (AC1).
  Dev NE menja model. Forma je validacioni source-of-truth (ulazna kapija).
- Sve labele + error poruke kroz `gettext_lazy` — pune dijakritike (č/ć/ž/š/đ), NIKAD ćirilica,
  NIKAD šišana latinica (AC9).
- HTML5 widget atributi (`type="email"`, `required`) su SAMO UX sloj; server je SOT.

**Field-required matrica (asertovano test_contact_form.py):**

| polje    | required | prazno → invalid? |
|----------|----------|-------------------|
| name     | ✓        | ✓                 |
| email    | ✓        | ✓ (+ loš format)  |
| phone    | ✗        | ne (prazno = OK)  |
| message  | ✓        | ✓                 |

---

## 2. `apps/forms/views.py` — `contact_submit`

```python
from django.http import HttpResponse
from django.shortcuts import render
from django.utils.translation import get_language
from django.views.decorators.http import require_POST
from django_ratelimit.decorators import ratelimit

from apps.forms.forms import ContactForm
from apps.forms.models import Lead
from apps.forms.notifications import send_lead_email


@require_POST
@ratelimit(key="ip", rate="5/m", block=False)   # KRITIČNO: block=False (NE block=True → 403)
def contact_submit(request):
    if getattr(request, "limited", False):       # NA VRHU TELA, PRE bind-a forme i PRE Lead.create
        return HttpResponse(status=429)          # HTTP 429 (SM-D9), NE 403
    form = ContactForm(request.POST)
    if not form.is_valid():
        # error rerender, HTTP 200, NIJEDAN Lead, NIJEDAN email
        return render(request, "<error/fields partial>", {"form": form}, status=200)
    lead = Lead.objects.create(
        form_type=Lead.FormType.KONTAKT,
        name=form.cleaned_data["name"],
        email=form.cleaned_data["email"],
        phone=form.cleaned_data["phone"],
        message=form.cleaned_data["message"],
        locale=get_language(),
        ip_address=request.META.get("REMOTE_ADDR"),
        data={},
    )
    send_lead_email(lead)                         # save-before-send; povratak se NE rollback-uje (AC5)
    return render(request, "forms/partials/contact_success.html", {...})
```

**Ponašanje (asertovano):**
- `@require_POST` → GET vraća **405** (AC2).
- `block=False` + `request.limited` check → 6. zahtev sa istog IP-a u 1 min vraća **429** (NE 403) (AC7).
- Success: kreira TAČNO 1 `Lead` (`form_type="contact"`, `data={}`, `locale="sr"`, `ip_address` set),
  poziva `send_lead_email(lead)` (1 mail u mailoutbox, subject „[Ćorić Agrar] Novi kontakt: {name}",
  `to == [settings.CONTACT_EMAIL_TO]`) (AC3).
- Error: HTTP 200, `Lead.objects.count() == 0`, `mailoutbox` prazan, error rerender (AC4).
- Email-failure: `send_lead_email → False` → Lead OSTAJE, posetilac dobija success partial (AC5).
- Klijent IP: goli `request.META["REMOTE_ADDR"]` (trust-proxy van scope-a — OQ-3).

---

## 3. `apps/forms/urls.py`

```python
from django.urls import path
from apps.forms import views

app_name = "forms"

urlpatterns = [
    path("htmx/forme/kontakt/", views.contact_submit, name="contact_submit"),
]
```

- `reverse("forms:contact_submit")` pod aktivnim `sr` locale → **`/sr/htmx/forme/kontakt/`** (AC2).
- i18n_patterns obmotava 3 jezika → i `/hu/...` i `/en/...` rezolvuju.

---

## 4. `config/urls.py` — mount

Dodati UNUTAR `i18n_patterns(...)`, POSLE `pages` include-a:

```python
path("", include("apps.forms.urls")),  # Story 4.2 — htmx/forme/kontakt/
```

Empty-prefix include; `htmx/forme/kontakt/` je konkretan segment → ne sudara se sa `pages` root.

---

## 5. Partial templates (`templates/forms/partials/`)

| putanja                                            | uloga | sadržaj (asertovano) |
|----------------------------------------------------|-------|----------------------|
| `templates/forms/partials/contact_success.html`    | success swap | poruka „Hvala! Vaš upit je primljen." (`{% translate %}`); standalone; `{% if request.htmx %}` OOB `hx-swap-oob="innerHTML:#aria-live"` sa „Upit je poslat."; ROOT element čisto zamenjuje `<section id="contact-form-section">`; NIJE full page (NEMA `<html`/`<head`) |
| `templates/forms/partials/_contact_form_fields.html` (ILI rerender `_contact_form.html`) | error rerender | bound `ContactForm` polja + per-field greške; **in-form** `<div role="alert" aria-live="assertive">` error summary (regija #1); `{% csrf_token %}`; `hx-post`/`hx-target`/`hx-swap`/`htmx-indicator`; **ODVOJEN** `{% if request.htmx %}` OOB `hx-swap-oob="innerHTML:#aria-live"` sa „Greška pri slanju, proverite polja." (regija #2, polite); NIJE full page |

**Dve ODVOJENE a11y regije (KRITIČNO):**
- Regija #1 — **in-form** `role="alert"` + `aria-live="assertive"` (samo na ERROR, unutar form partial-a).
- Regija #2 — **OOB** `hx-swap-oob="innerHTML:#aria-live"` ka `base.html` `polite` singletonu (success I error).
- Singleton OSTAJE `aria-live="polite"` — OOB blok NE postavlja `assertive` na `#aria-live`.
- Success odgovor → SAMO regija #2 (polite). Error odgovor → OBE.

---

## 6. `config/settings/base.py` — `CACHES` (Task 6.0, SM-D10)

```python
CACHES = {
    "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
}
```

django-ratelimit koristi `default` cache za brojanje po IP-u. locmem dovoljan za v1 (YAGNI, NE Redis).
Test (test_contact_view_ratelimit.py) pinuje cache preko `@override_settings(CACHES=...)` + `cache.clear()`
između testova → deterministična 5-ok/6-ti-429 granica.

---

## 7. Wiring u `templates/pages/partials/_contact_form.html` (AC8 / Task 8.1)

Skelet → funkcionalna HTMX forma:
- Ukloni `disabled`/`aria-disabled` sa svih polja + submit-a.
- Na obuhvatajućoj `<section class="coric-contact-form" aria-labelledby="contact-form-title">` dodaj
  **`id="contact-form-section"`** (swap target — SM-D6 PINNED).
- Na `<form>` dodaj: `hx-post="{% url 'forms:contact_submit' %}"`, `hx-target="#contact-form-section"`,
  `hx-swap="outerHTML"`, `htmx-indicator` loading element.
- Ukloni „Forma će uskoro biti dostupna" hint (`#contact-form-hint`) + TODO Story 4.2 komentar.
- Zadrži: BEM klase `coric-contact-form__*`, `data-testid="contact-form"`/`"contact-submit"`,
  label↔input asocijacije (`for`), CSRF token, **`method="post"` na `<form>`** (C1 no-JS
  fallback guard — test `test_contact_form_has_functional_hx_post` asertuje OBE: `method="post"`
  I `hx-post`).
- `ContactView` (pages) OSTAJE GET-only NETAKNUT → POST na `pages:contact` i dalje 405.

---

## 8. Sažetak (struktura)

- **forms:** `apps/forms/forms.py::ContactForm` (name*/email*/phone/message* — message required na formi).
- **views:** `apps/forms/views.py::contact_submit` — `@require_POST` + `@ratelimit(key="ip", rate="5/m", block=False)` + `if request.limited → HttpResponse(429)`; save-before-send; success/error partial.
- **urls:** `apps/forms/urls.py` (`app_name="forms"`, `htmx/forme/kontakt/`); mount u `config/urls.py` (`path("", include("apps.forms.urls"))`).
- **templates:** `templates/forms/partials/contact_success.html` + `_contact_form_fields.html` (error rerender); wire `templates/pages/partials/_contact_form.html` (swap target `#contact-form-section`, `hx-swap=outerHTML`).
- **settings:** `config/settings/base.py` — eksplicitan `CACHES` (locmem default) za ratelimit backend.
