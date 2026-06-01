---
story-id: 4-2-opsta-kontakt-forma-fr-5
epic: 4
title: "Opšta Kontakt Forma (FR-5)"
status: ready-for-dev
module: forms
base-branch: master
created: 2026-06-01
author: SM (Scrum Master, 📋)
depends-on:
  - 4-1-lead-model-smtp-setup   # Lead model + send_lead_email service (DONE)
  - 3-3-kontakt-strana-sa-formom-i-mapom   # Kontakt strana + forward-compat forma skelet (DONE)
forward-dep:
  - 4-6-htmx-form-patterns-aria-live-oob-rate-limiting   # standardizuje HTMX/ratelimit pattern kroz forme 4.2-4.5
---

# Story 4.2 — Opšta Kontakt Forma (FR-5)

## Opis / Description

As a **posetilac**, I want **da pošaljem opšti upit preko forme na Kontakt strani**, so that **mogu da kontaktiram firmu bez telefoniranja**.

Ovo je **PRVA forma story** Epic 4. Story 4.1 (Lead model + `send_lead_email` servis + SMTP/Resend config) je DONE i čini temelj na kome se gradi. Story 3.3 je već scaffold-ovao Kontakt stranu (`/sr/kontakt/`) sa **forward-compat skeletom forme** (`templates/pages/partials/_contact_form.html` — vizuelni markup polja + `{% csrf_token %}`, ali sva polja `disabled` i submit `disabled`, BEZ funkcionalnog endpoint-a). Ova story **OŽIVLJAVA** taj skelet: uvodi `ContactForm` (Django form), HTMX `POST` endpoint (`apps/forms/views.py` + `apps/forms/urls.py`), žica ih u postojeću Kontakt stranu i wire-uje `apps.forms.urls` u `config/urls.py`.

Submit ide preko HTMX (`hx-post` na `forms:contact_submit` → `/sr/htmx/forme/kontakt/`). Server-side validacija (Django `ContactForm`) je source-of-truth; client-side HTML5 (`required`, `type="email"`) je samo UX sloj. Na uspeh forma se zameni success partial-om („Hvala! Vaš upit je primljen."); na grešku se rerender-uje sa poljima u error stanju + `aria-live="assertive"` summary. Lead se perzistira (`form_type='contact'`) PRE poziva `send_lead_email(lead)` (save-before-send ugovor iz 4.1). Email stiže na `CONTACT_EMAIL_TO` recipient sa subject „[Ćorić Agrar] Novi kontakt: {name}".

**Granica scope-a (KRITIČNO):**
- Ova story je **self-contained**, ali Story 4.6 će kasnije standardizovati HTMX form pattern (reusable mixin/decorator) + rate limiting kroz forme 4.2-4.5. Zato 4.2 implementira ratelimit i OOB aria-live **inline** (per project-context.md security/a11y must-have), a 4.6 će refaktorisati u zajednički pattern. **NE** graditi prerano apstrakciju u 4.2 (YAGNI).
- `ContactView` u `apps/pages/views.py` OSTAJE GET-only (`http_method_names = ["get", "head", "options"]`, vraća 405 na POST) — submit ide na ZASEBAN `apps/forms` endpoint, NE na ContactView. **NE dodavati `post()` na ContactView.**
- Forma koristi SAMO core Lead polja (`name`/`email`/`phone`/`message`); `Lead.data` ostaje prazan `{}` za `form_type='contact'` (4-1-interface-contract.md § 7).

---

## Kontekst iz postojećeg koda (REAL reference — istraženo, NE pretpostavke)

### Lead model (`apps/forms/models.py` — Story 4.1, NETAKNUT)
- `Lead(TimestampedModel)`, `FormType.KONTAKT = "contact"` (DB vrednost LOWERCASE, LOCKED).
- Polja: `form_type`, `name` (CharField 200, obavezno), `email` (EmailField), `phone` (CharField 50, blank=True), `message` (TextField, blank=True), `data` (JSONField default=dict), `ip_address` (GenericIPAddressField null/blank), `locale` (CharField default „sr").
- **NEMA `photo` polja, NEMA FK, NEMA `get_absolute_url`.**

### Email servis (`apps/forms/notifications.py` — Story 4.1, NETAKNUT)
- `def send_lead_email(lead) -> bool` — SYNC, **VIEW-CALLED** (NE signal), **save-before-send** (prima već sačuvanu instancu sa `lead.pk`).
- Recipient za `FormType.KONTAKT` → `settings.CONTACT_EMAIL_TO` (`_resolve_recipient`).
- Subject za kontakt: `_("[Ćorić Agrar] Novi kontakt: %(name)s") % {"name": lead.name}` (`_build_subject`) — **VEĆ TAČNO** matchuje AC. Lokalizovan po `lead.locale`.
- Vraća `True` na uspeh; `False` na provider fail ILI prazan recipient (NE re-raise, NE rollback Lead-a).

### Settings (`config/settings/base.py` — Story 4.1, NETAKNUT)
- `DEFAULT_FROM_EMAIL` (`:108`), `CONTACT_EMAIL_TO`/`SERVICE_EMAIL_TO`/`PARTS_EMAIL_TO` iz env (`:119-121`), `ANYMAIL` dict.
- Dev: console backend (`development.py:15`) — dev NE šalje pravi email. Test: pytest-django `mailoutbox` → locmem.

### Kontakt strana (Story 3.3 — žica se, NE duplira)
- `apps/pages/views.py` → `ContactView(TemplateView)` GET-only, `template_name = "pages/contact.html"`. **OSTAJE NETAKNUT** (NE dodavati POST).
- `apps/pages/urls.py` → `pages:contact` na `kontakt/`.
- `templates/pages/contact.html` → `{% include "pages/partials/_contact_info.html" %}` + `{% include "pages/partials/_contact_form.html" %}` + `_contact_map.html`.
- `templates/pages/partials/_contact_form.html` → **forward-compat skelet** koji se OŽIVLJAVA: polja `name`/`email`/`phone`/`message` (id-ovi `contact-name`/`contact-email`/`contact-phone`/`contact-message`), `data-testid="contact-form"`/`"contact-submit"`, BEM klase `coric-contact-form__*`. TODO komentar (`:16`) eksplicitno upućuje na ovu story.

### URL wiring (`config/urls.py` — EDIT)
- `apps.forms` trenutno NEMA `urls.py` ni mount u `config/urls.py`. Postojeći mount-ovi u `i18n_patterns(...)`: `brands`, `products`, `search`, `pages`. Dodati `path("", include("apps.forms.urls"))`.
- HTMX prefix konvencija (iz `apps/search/urls.py`): `path("htmx/forme/kontakt/", ...)` → sa i18n prefiksom postaje `/sr/htmx/forme/kontakt/`.

### HTMX OOB aria-live pattern (REUSE — `apps/core/templatetags/htmx_aria.py` + search/products partials)
- `base.html` renderuje singleton `{% aria_live %}` → `<div id="aria-live" class="visually-hidden" aria-live="polite" aria-atomic="true"></div>`.
- OOB najava: `<div hx-swap-oob="innerHTML:#aria-live">{% translate "..." %}</div>`, guarded sa `{% if request.htmx %}` (SM-D14 iz 2-13 — sprečava plain-text render u non-HTMX fallback-u).
- `htmx-indicator` klasa + Bootstrap spinner za loading; min 200ms (project-context.md:193).

---

## Acceptance Criteria

**AC1 — ContactForm (server-side validation SOT).**
**Given** Lead model iz Story 4.1
**When** kreiram `apps/forms/forms.py` sa `ContactForm` (Django `forms.Form` ili `ModelForm` za `Lead`) sa poljima `name` (obavezno), `email` (obavezno, EmailField), `phone` (opciono), `message` (obavezno)
**Then** sva user-facing labela/error poruka prolazi kroz `gettext_lazy` (pune dijakritike č/ć/ž/š/đ, NIKAD ćirilica/šišana latinica)
**And** prazno `name`/`email`/`message` → `form.is_valid()` je `False` sa per-field greškama
**And** nevalidan email format → `False`; validan kompletan payload → `True`
**And** `ContactForm.message` je `required=True` IAKO je `Lead.message` `blank=True` na modelu — FORMA je validacioni source-of-truth (ulazna kapija), model je samo storage (4.1 je namerno ostavio `message` blank=True jer druge forme/segmenti mogu imati prazan `message`). Dev NE menja `Lead.message` na modelu; obaveznost se nameće NA FORMI.

**AC2 — HTMX POST endpoint + URL wiring.**
**Given** ContactForm iz AC1
**When** kreiram `apps/forms/views.py` (`contact_submit` FBV) + `apps/forms/urls.py` (`app_name = "forms"`, `path("htmx/forme/kontakt/", views.contact_submit, name="contact_submit")`) i wire-ujem `path("", include("apps.forms.urls"))` u `config/urls.py` unutar `i18n_patterns`
**Then** `reverse("forms:contact_submit")` rezolvuje na `/sr/htmx/forme/kontakt/` (locale-prefiksovan)
**And** endpoint prihvata SAMO POST (GET → 405, npr. `require_POST`)
**And** view radi save-before-send: `lead = Lead.objects.create(form_type=Lead.FormType.KONTAKT, name=..., email=..., phone=..., message=..., locale=<aktivni jezik>, ip_address=<iz request>, data={})` PA TEK ONDA `send_lead_email(lead)`.

**AC3 — Uspešan submit (success partial).**
**Given** endpoint iz AC2
**When** pošaljem validan POST sa `name`/`email`/`phone`/`message`
**Then** kreira se TAČNO 1 `Lead` red sa `form_type == "contact"` i poljima iz payload-a, `data == {}`
**And** view vraća success partial (`templates/forms/partials/contact_success.html`) sa porukom „Hvala! Vaš upit je primljen." (kroz `{% translate %}`) — forma se HTMX-swap-uje ovim partial-om
**And** response NIJE full HTML page (project-context.md:194 — HTMX uvek partial)
**And** `send_lead_email(lead)` je pozvan (1 email u `mailoutbox`), subject sadrži „[Ćorić Agrar] Novi kontakt: " + `name`, `to == [CONTACT_EMAIL_TO]`.

**AC4 — Neuspešan submit (error rerender + aria-live assertive).**
**Given** endpoint iz AC2
**When** pošaljem nevalidan POST (npr. prazno `name`/`email`/`message` ili loš email)
**Then** view vraća form partial rerender-ovan sa poljima u `error` stanju (bound form sa `form.errors`), HTTP 200 (NE 4xx — HTMX swap error UI-a)
**And** rerender sadrži **U-FORMI** error summary `<div role="alert" aria-live="assertive">` (vidljiv + trenutna SR najava) sa per-field greškama — ovo je PRVA od dve a11y regije i živi UNUTAR rerender-ovanog form partial-a (vidi AC6 za drugu)
**And** NIJEDAN `Lead` red NIJE kreiran i NIJEDAN email NIJE poslat (`mailoutbox` prazan).

> **Dve ODVOJENE a11y regije (KRITIČNO — ne mešati):** Error odgovor MORA imati OBE: (1) **in-form** `<div role="alert" aria-live="assertive">` error summary UNUTAR rerender-ovanog form partial-a (trenutna, snažna najava field grešaka — AC4), I (2) **ODVOJEN** `hx-swap-oob="innerHTML:#aria-live"` blok koji cilja postojeći `base.html` singleton koji je `aria-live="polite"` (kratak status, AC6). Singleton OSTAJE `polite` — NE prepravljati ga na `assertive`. Implementiraj OBE, ne samo jednu.

**AC5 — Email failure ne ruši UX (graceful degradation).**
**Given** `send_lead_email` vraća `bool` (4.1 failure contract)
**When** validan submit prođe ali `send_lead_email(lead)` vrati `False` (provider fail ILI prazan recipient)
**Then** Lead OSTAJE sačuvan (NIJE rollback)
**And** posetilac i dalje vidi success partial (lead je primljen u DB; email retry je interni problem) — **ILI** dokumentovana SM odluka (SM-D5) ako se bira drugačiji UX; default: success partial + interni `logger` zapis kroz već-postojeći 4.1 log.

**AC6 — OOB aria-live announcement (HTMX a11y).**
**Given** HTMX response patterns (project-context.md:184-194)
**When** submit success ILI error response se vrati na HTMX zahtev
**Then** response uključuje `hx-swap-oob` element ciljajući `#aria-live` singleton (`base.html` `{% aria_live %}`) sa kratkom porukom (success: „Upit je poslat."; error: „Greška pri slanju, proverite polja.") kroz `{% translate %}`
**And** OOB blok je guarded sa `{% if request.htmx %}` (REUSE SM-D14 pattern — ne curi u non-HTMX render)
**And** OVA OOB regija (`#aria-live` singleton, `aria-live="polite"`) je ODVOJENA od in-form `role="alert"`/`aria-live="assertive"` error summary regije iz AC4 — error odgovor sadrži OBE; success odgovor sadrži SAMO OOB polite najavu. Singleton ostaje `polite` (NE `assertive`).

**AC7 — Security must-haves (CSRF + ratelimit → HTTP 429).**
**Given** project-context.md security must-have (CSRF + ratelimit na javnim formama)
**When** wire-ujem formu
**Then** form template sadrži `{% csrf_token %}` (HTMX šalje CSRF header preko django-htmx propagacije)
**And** `contact_submit` view ima `@ratelimit(key='ip', rate='5/m', block=False)` dekorator iz `django_ratelimit` — **EKSPLICITNO `block=False`** (NE `block=True`)
**And** `contact_submit` na VRHU tela (PRE binda forme i PRE bilo kakvog `Lead.objects.create`) proverava `if getattr(request, "limited", False): return HttpResponse(status=429)` — vraća **HTTP 429** „previše zahteva" odgovor (SM-D9)
**And** 6. uzastopni submit sa istog IP-a u 1 minuti → **HTTP 429** (rate limit aktivira; 5 prvih prolazi, 6. blokiran)
**And** ratelimit koristi Django `default` cache backend (locmem) — eksplicitno definisan `CACHES` u `config/settings/base.py` (SM-D10), a Task 3.3 test pinuje cache preko `@override_settings(CACHES=...)` + clears cache između testova (deterministična 5-ok/6-ti-429 granica).

> **Zašto NE `block=True`:** `@ratelimit(..., block=True)` raise-uje `django_ratelimit.exceptions.Ratelimited`, koji subklasira `PermissionDenied` → Django renderuje **HTTP 403**, NE 429. U repo-u NEMA `handler403`/`handler429`/`RATELIMIT_VIEW`/`Ratelimited`-catch (grep-verifikovano), pa bi test koji asertuje `status_code == 429` PAO. Zato 4.2 koristi `block=False` + eksplicitan `request.limited` check koji vraća tačno 429 bez potrebe za projekt-globalnim handler-om (self-contained, SM-D9).

**AC8 — Wire u postojeću Kontakt stranu (NE duplira).**
**Given** Story 3.3 skelet `_contact_form.html` + `pages/contact.html`
**When** oživim formu
**Then** `_contact_form.html` se konvertuje iz disabled-skeleta u funkcionalnu HTMX formu: ukloni `disabled`/`aria-disabled` sa svih polja i submit-a; dodaj `hx-post="{% url 'forms:contact_submit' %}"` (na `<form>`), `hx-target="#contact-form-section"` + `hx-swap="outerHTML"` (target je obuhvatajuća `<section class="coric-contact-form">` kojoj se dodaje `id="contact-form-section"` — SM-D6 PINNED), `htmx-indicator` loading; ukloni „Forma će uskoro biti dostupna" hint (`#contact-form-hint`) ili ga zameni funkcionalnim hintom; ukloni TODO Story 4.2 komentar
**And** `ContactView` OSTAJE GET-only NETAKNUT; `pages/contact.html` include-ovi se NE menjaju strukturno (forma i dalje renderuje u `_contact_form.html`)
**And** GET `/sr/kontakt/` (200) i dalje prikazuje stranu sa SADA aktivnom formom (polja NISU disabled).

**AC9 — i18n + dijakritike + lint.**
**Given** project-context.md i18n + anti-pattern pravila
**When** dodam sve nove stringove
**Then** SVE user-facing strings (labele, error poruke, success/aria poruke) idu kroz `gettext_lazy`/`{% translate %}` sa punim dijakritikama; NIKAD ćirilica, NIKAD šišana latinica
**And** `just lint` (ruff + djade) je clean; `just test` (novi forms testovi) prolazi
**And** ako novi `.po` stringovi → `just messages` (makemessages + compilemessages).

---

## Tasks / Subtasks (TDD-ordered: TEA RED → Dev GREEN)

> **Disciplina (project-context.md:293-298):** TEA agent piše testove (RED phase) PRVI; Dev agent piše implementaciju (GREEN); Dev NIKAD ne piše testove. Testovi se commit-uju pre implementacije. Ako TEA testovi failuju u Dev fazi → story `paused`, ne maskirati greške.

### Task 1 — (TEA, RED) Test skelet + fixtures za forms view/form suite
- [ ] 1.1 Proširi `apps/forms/tests/conftest.py` (REUSE postojeći `recipient_env` + `superuser` fixtures iz 4.1) sa `valid_contact_payload` fixture (`{"name": "Marko Marković", "email": "marko@example.com", "phone": "+381641234567", "message": "Zanima me traktor."}`) i `htmx_post` helper (client POST sa `HTTP_HX_REQUEST="true"` header da `request.htmx` bude True).
- [ ] 1.2 Novi `apps/forms/tests/test_contact_form.py` (AC1): polja postoje; `name`/`email`/`message` obavezni; `phone` opciono; nevalidan email → invalid; validan payload → valid; labele/errori kroz gettext (substring pune dijakritike, NEMA ćirilice).

### Task 2 — (TEA, RED) Test HTMX endpoint + URL wiring
- [ ] 2.1 Novi `apps/forms/tests/test_contact_view.py` (AC2/AC3/AC4):
  - `reverse("forms:contact_submit")` rezolvuje (NoReverseMatch RED dok URL ne postoji); URL je `/sr/htmx/forme/kontakt/` (i18n-prefiksovan). **VAŽNO:** pošto je URL pod `i18n_patterns`, AKTIVIRAJ locale PRE asercije na tačan string — `from django.utils.translation import activate; activate("sr")` (ili `with translation.override("sr"):`). Bez aktivnog locale-a `reverse()` vraća URL BEZ `/sr/` prefiksa i asercija je krhka/pada.
    - **(low) i18n routing sva 3 jezika:** opciono potvrdi da i `/hu/htmx/forme/kontakt/` i `/en/htmx/forme/kontakt/` rezolvuju (i18n_patterns obmotava sva 3 jezika — project-context.md:263). Drži proporcionalno (jedan parametrizovan test ili `translation.override("hu")`/`("en")` + reverse() asercija).
  - GET → 405 (`require_POST`).
  - **Success (AC3):** validan HTMX POST → 200; `Lead.objects.count() == 1`; `lead.form_type == Lead.FormType.KONTAKT`; polja iz payload-a; `lead.data == {}`; `lead.locale == "sr"`; `lead.ip_address` popunjen; success partial template korišćen (`templates/forms/partials/contact_success.html`) + sadrži „Hvala"; `len(mailoutbox) == 1`; subject sadrži „[Ćorić Agrar] Novi kontakt: Marko Marković"; `mailoutbox[0].to == [settings.CONTACT_EMAIL_TO]` (sa `recipient_env`).
  - **Error (AC4):** nevalidan POST (prazno `name`) → 200 (NE 4xx); `Lead.objects.count() == 0`; `len(mailoutbox) == 0`; rerender sadrži `role="alert"` + `aria-live="assertive"` + error tekst za polje.
- [ ] 2.2 Test (AC2): response na success NIJE full page (NE sadrži `<html`/`<head>` — partial check, mirror apps/search test konvencija substring/`render_to_string`). **Simetrično:** i ERROR response (nevalidan POST) je takođe partial — asertuj da NE sadrži `<html`/`<head>` (oba odgovora moraju ostati partial-i, project-context.md:194).
- [ ] 2.3 Test (AC4, XSS insurance — javna unauth forma): nevalidan POST sa `name`/`message` koji sadrži `<script>alert(1)</script>` → error rerender bound forme auto-escape-uje payload (Django default escaping) — asertuj da response NE sadrži sirov `<script>` već escaped `&lt;script&gt;`. Jeftina osiguravajuća asercija.

### Task 3 — (TEA, RED) Test OOB aria-live + email-failure + security
- [ ] 3.1 `test_contact_view_aria_live.py` (AC6 + AC4 dve regije): success response sadrži `hx-swap-oob="innerHTML:#aria-live"` + success najavu (SAMO OOB polite regija); error response sadrži OBE — (a) in-form `role="alert"` + `aria-live="assertive"` summary I (b) ODVOJEN `hx-swap-oob="innerHTML:#aria-live"` polite najavu; OOB se NE pojavljuje u non-HTMX render-u (guard `{% if request.htmx %}`); singleton ostaje `polite` (asertuj da OOB blok NE postavlja `assertive` na `#aria-live`).
  - **(low) Non-HTMX POST edge:** validan POST BEZ `HX-Request` header-a (običan client POST, NE `htmx_post` helper) → response NE sadrži `hx-swap-oob` (guard `{% if request.htmx %}` radi i kad `request.htmx` je False). Potvrđuje da OOB ne curi u non-HTMX putanju.
- [ ] 3.2 `test_contact_view_email_failure.py` (AC5): `monkeypatch`/`mock.patch` na `apps.forms.views.send_lead_email` da vrati `False`; validan submit → Lead i dalje postoji (count==1); posetilac i dalje dobija success partial (per SM-D5 default). (Mock SAMO servis-povratnu vrednost, NE Django ORM — project-context.md:267.)
- [ ] 3.3 `test_contact_view_ratelimit.py` (AC7): 5 submit-a OK (status NIJE 429); 6. submit sa istog IP-a u istom minutu → `status_code == 429` (NE 403 — Dev koristi `block=False` + `request.limited` → `HttpResponse(status=429)` mehanizam, SM-D9; ako test vidi 403, story je u RED dok Dev ne ispravi decorator). Pinuj cache eksplicitno preko `@override_settings(CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}})` na test klasi/funkciji **I** clear cache pre/posle svakog testa (`from django.core.cache import cache; cache.clear()` u fixture-u ili `autouse` fixture) da 5-ok/6-ti-429 granica bude deterministična i da ratelimit brojač ne curi između testova. CSRF token prisutan u renderovanoj formi (GET `/sr/kontakt/` sadrži `csrfmiddlewaretoken` ili HTMX csrf header propagacija dokumentovana).

### Task 4 — (TEA, RED) Test wiring u Kontakt stranu (a11y/regression)
- [ ] 4.1 `apps/pages/tests/` ILI `apps/forms/tests/test_contact_page_wired.py` (AC8): GET `/sr/kontakt/` → 200; renderovani `_contact_form.html` SADA NEMA `disabled` atribut na poljima/submit-u; sadrži `hx-post` ka `forms:contact_submit`; više NE sadrži „Forma će uskoro biti dostupna"; `data-testid="contact-form"`/`"contact-submit"` očuvani. **Regression:** POST na `pages:contact` (ContactView) i dalje vraća 405 (ContactView NETAKNUT).
- [ ] 4.2 **(TEA, RED — OBAVEZNO: skeleton anti-testovi se INVERTUJU)** Ažuriraj postojeći `apps/pages/tests/test_contact_form_skeleton.py` (Story 3.3, 5 testova) tako da asertuje POST-4.2 realnost. Ti testovi trenutno asertuju **suprotno** od onoga što AC8/Task 8 sada zahteva (skelet → funkcionalna forma), pa će posle Dev GREEN faze PASTI i blokirati `just test` ako se ne ažuriraju (project-context.md:296 — testovi NE smeju ostati crveni). Ovo je **poznat TDD milestone**: skeleton anti-testovi se flip-uju kad story oživi formu. Updating testova je TEA posao (project-context.md:294 „Dev NIKAD ne piše testove") — Dev NE dira ovaj fajl. Konkretne inverzije (verifikovano čitanjem trenutnog fajla):
  - `test_contact_submit_is_disabled` → submit dugme [data-testid="contact-submit"] VIŠE NEMA `disabled` ni `aria-disabled="true"` (forma je aktivna). Preimenuj/reformuliši u npr. `test_contact_submit_is_enabled`.
  - `test_contact_form_inputs_disabled_and_hint_associated` → user input/textarea polja VIŠE NEMAJU `disabled` (polja su u tab-redu, aktivna). „Uskoro aktivna" hint (`#contact-form-hint`) je uklonjen — odgovarajuća `aria-describedby` asercija se ažurira (ukloni ILI repointuj na funkcionalan hint ako Dev zadrži jedan; uskladi sa Task 8.1).
  - `test_contact_form_has_no_functional_hx_post` → forma SADA IMA `hx-post` ka `forms:contact_submit`. Invertuj aserciju: forma MORA imati `hx-post` (više se ne sme asertovati da `hx-post` NE postoji). Zadrži/ažuriraj `method="post"` ↔ `action` proveru prema finalnom markup-u iz Task 8.1.
  - `test_contact_form_has_csrf_token` i `test_contact_form_has_4_labeled_fields` OSTAJU validni (CSRF token + 4 labelirana polja se zadržavaju i u aktivnoj formi) — proveri da i dalje prolaze, ne brisati.
  - **Očuvaj:** `data-testid="contact-form"`/`"contact-submit"` hook-ovi i label↔input asocijacije ostaju (a11y). NE brisati ceo fajl — refaktorisati asercije na novu realnost. (Moguće je i preseliti ažurirane testove u `test_contact_page_wired.py` i obrisati duplikate iz skeleton fajla — ali NE ostavljati nijedan crveni anti-test za stari skelet.)

### Task 5 — (Dev, GREEN) `apps/forms/forms.py` — ContactForm
- [x] 5.1 Kreiraj `ContactForm` (`forms.Form` ili `forms.ModelForm` za `Lead` sa `fields = ["name", "email", "phone", "message"]`); `name`/`email`/`message` `required=True`, `phone` `required=False`; labele/error poruke kroz `gettext_lazy` (pune dijakritike); HTML5 widget atributi (`type="email"`, `required`) za client-side UX sloj (server je SOT).

### Task 6 — (Dev, GREEN) `apps/forms/views.py` + `apps/forms/urls.py` + URL wiring + CACHES
- [x] 6.0 `config/settings/base.py`: dodaj eksplicitan `CACHES` dict tako da ratelimit backend bude deterministički (NE oslanjati se na Django implicitni default). Minimalno (SM-D10, YAGNI — NE Redis, NE django-redis per project-context.md:84):
  ```python
  # ── Cache (ratelimit backend) ─────────────────────────────────────────────
  # django-ratelimit koristi Django `default` cache za brojanje zahteva po IP-u.
  # locmem je dovoljan za v1 (single-process dev/test); prod skaliranje (shared
  # cache) je Epic 9/4.6 odluka — NE Redis sada (YAGNI, project-context.md).
  CACHES = {
      "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
  }
  ```
- [x] 6.1 `apps/forms/views.py`: `contact_submit` FBV — `@require_POST` + `@ratelimit(key="ip", rate="5/m", block=False)` (**`block=False`, NE `block=True`** — vidi AC7 obrazloženje + SM-D9). Na VRHU tela (PRE bind-a forme i PRE `Lead.objects.create`): `if getattr(request, "limited", False): return HttpResponse(status=429)` (opciono render tanak „previše zahteva" partial sa istim 429 status-om; `from django.http import HttpResponse`). Zatim bind `ContactForm(request.POST)`; ako invalid → render error partial (200) sa bound form + OOB aria-live error; ako valid → `Lead.objects.create(form_type=Lead.FormType.KONTAKT, **cleaned, locale=get_language(), ip_address=<client IP>, data={})`, pozovi `send_lead_email(lead)`, render success partial + OOB aria-live success. Klijent IP iz `request.META` (REMOTE_ADDR; trust-proxy van scope-a — 4.6/9.x).
- [x] 6.2 `apps/forms/urls.py`: `app_name = "forms"`; `path("htmx/forme/kontakt/", views.contact_submit, name="contact_submit")` (mirror `apps/search/urls.py` HTMX prefix konvencija).
- [x] 6.3 `config/urls.py`: dodaj `path("", include("apps.forms.urls"))` unutar `i18n_patterns(...)` POSLE postojećeg `pages` include-a (verifikovano: trenutni redosled je `brands` → `products` → `search` → `pages`, svi sa praznim prefiksom). Empty-prefix include-ovi se rezolvuju po specifičnosti path-a: `htmx/forme/kontakt/` je konkretan segment pa se ne sudara sa `pages` root `/` rutom — mirror obrasca već primenjenog za `brands`/`products`/`search`. Nizak rizik; samo dodati na kraj.

### Task 7 — (Dev, GREEN) Forms partials (success + error)
- [x] 7.1 `templates/forms/partials/contact_success.html`: poruka „Hvala! Vaš upit je primljen." (`{% translate %}`); standalone-renderable; `{% if request.htmx %}` OOB `hx-swap-oob="innerHTML:#aria-live"` success najava.
- [x] 7.2 `templates/forms/partials/_contact_form_fields.html` (ILI rerender postojećeg `_contact_form.html` kao partial): renderuje bound `ContactForm` polja + per-field greške + **U-FORMI** `<div role="alert" aria-live="assertive">` error summary kad `form.errors` (regija #1); `{% csrf_token %}`; `hx-post`/`hx-target`/`hx-swap`/`htmx-indicator`; **ODVOJEN** `{% if request.htmx %}` `hx-swap-oob="innerHTML:#aria-live"` blok koji cilja `base.html` `aria-live="polite"` singleton (regija #2). **OBE regije su obavezne na error-u** (vidi AC4/AC6); NE prepravljati singleton na `assertive`, NE implementirati samo jednu od dve. **Odluka (SM-D6):** odluči da li success/error partial-i žive u `templates/forms/partials/` (forms app vlasnik) ILI se reuse-uje `templates/pages/partials/_contact_form.html` kao container — preporuka: forms partials za fields/success/error, a `_contact_form.html` postaje tanak include koji mount-uje forms fields partial + `hx-` atribute (forma logički pripada `forms` app-u, ali render-uje na pages strani).

### Task 8 — (Dev, GREEN) Wire u Kontakt stranu
- [x] 8.1 Konvertuj `templates/pages/partials/_contact_form.html`: ukloni `disabled`/`aria-disabled` sa polja i submit-a; na obuhvatajućoj `<section class="coric-contact-form" ...>` dodaj `id="contact-form-section"` (target za swap — SM-D6 PINNED); na `<form>` dodaj `hx-post="{% url 'forms:contact_submit' %}"`, `hx-target="#contact-form-section"`, `hx-swap="outerHTML"`, `htmx-indicator` loading element; ukloni „Forma će uskoro biti dostupna" hint + TODO Story 4.2 komentar; zadrži BEM klase + `data-testid` hookove + a11y atribute (label `for`, `aria-required`). (Success partial iz Task 7.1 mora renderovati ROOT element koji čisto zamenjuje `<section id="contact-form-section">` — npr. ista sekcija/`<div>` sa porukom „Hvala".)
- [x] 8.2 Potvrdi `pages/contact.html` include strukturu (forma se i dalje renderuje kroz `_contact_form.html`); `ContactView` NETAKNUT (GET-only).

### Task 9 — (Dev, GREEN) CSS + i18n + lint + verifikacija
- [x] 9.1 Ako treba dodatni CSS (error stanje polja, success partial, spinner) → proširi `static/css/components/contact-page.css` (REUSE postojeći `coric-contact-form__*` BEM; `var(--token)` umesto magic vrednosti; NIKAD inline style); ako nova komponenta — `@import` u `main.css`.
- [x] 9.2 `just messages` ako su dodati novi `{% translate %}`/`gettext_lazy` stringovi (makemessages + compilemessages za sr/hu/en).
- [x] 9.3 `just lint` (ruff + djade) clean; `just test` (forms + pages contact regresija) zelen. Self-review checklist (project-context.md:425): CSRF+ratelimit ✓, aria-live OOB ✓, gettext sve ✓, no inline style ✓, no defensive validation ✓.

---

## SM Decisions (log)

- **SM-D1 (scope):** 4.2 je PRVA forma — uvodi `apps/forms/{forms,views,urls}.py` (Story 4.1 imala 0 view/URL/forme). Ratelimit + OOB aria-live implementirani INLINE per security/a11y must-have; Story 4.6 kasnije refaktoriše u reusable mixin/decorator. NE graditi prerano apstrakciju u 4.2 (YAGNI / project-context.md:356).
- **SM-D2 (ne-duplikat):** WIRE u postojeći Story 3.3 `_contact_form.html` skelet + `pages/contact.html`, NE rebuild strane. `ContactView` OSTAJE GET-only NETAKNUT (405 na POST). Submit ide na ZASEBAN `forms:contact_submit` endpoint (`/sr/htmx/forme/kontakt/`).
- **SM-D3 (subject već tačan):** `send_lead_email._build_subject` već vraća „[Ćorić Agrar] Novi kontakt: {name}" za `FormType.KONTAKT` — Dev NE menja notifications.py; samo poziva `send_lead_email(lead)`.
- **SM-D4 (recipient mapping):** kontakt → `CONTACT_EMAIL_TO` (4.1 `_resolve_recipient`). Epics.md pominje `LEAD_EMAIL_RECIPIENT` (generičko ime iz 4.1 spec-a); 4.1 interface-contract finalizovao per-segment imena (`CONTACT_EMAIL_TO`) — koristi `CONTACT_EMAIL_TO` (autoritativno).
- **SM-D5 (email-failure UX) — OQ:** ako `send_lead_email` vrati `False`, default je success partial za posetioca (lead JE u DB; email retry je interni problem, već logovan u 4.1). Alternativa: degradirani success sa fallback „pozovite nas" porukom. **Default = čist success.** Step-02 validacija / Mihas može override-ovati.
- **SM-D6 (partial vlasništvo + swap target PINNED):** success/error/fields partial-i žive u `templates/forms/partials/` (forms app vlasnik). `_contact_form.html` (pages) postaje tanak container koji mount-uje forms fields partial + `hx-` atribute. Dev finalizuje tačnu dekompoziciju u GREEN; success/error su standalone-renderable. **Swap target PINNED (više nije „Dev finalizuje"):** HTMX swap target je obuhvatajući `<section class="coric-contact-form" aria-labelledby="contact-form-title">` element (verifikovano čitanjem `templates/pages/partials/_contact_form.html` — sekcija NEMA `id`, identifikuje se preko klase `coric-contact-form` + `aria-labelledby="contact-form-title"`; `<form>` ima `data-testid="contact-form"`). `hx-target` = ta `<section>`, `hx-swap="outerHTML"` → success partial čisto zamenjuje celu sekciju, a error partial rerenderuje formu unutar iste sekcije. **`hx-` atributi idu na `<form>`** (HTMX hvata native submit), a `hx-target` referencira obuhvatajuću sekciju — pošto sekcija nema `id`, Dev ili (a) dodaje `id="contact-form-section"` na `<section>` i cilja `hx-target="#contact-form-section"`, ILI (b) koristi `hx-target="closest section"` sa `<form>`. Preporuka: (a) eksplicitan `id` (čitljivije, testabilnije). OOB `#aria-live` je ZASEBAN target (postojeći `base.html` singleton) — NIJE potreban `HX-Retarget` header.
- **SM-D7 (data JSON):** `form_type='contact'` → `Lead.data = {}` (4-1-interface-contract.md § 7 — kontakt koristi SAMO core polja).
- **SM-D8 (ratelimit rate):** 4.2 koristi `5/m` (project-context.md security must-have „5/m na IP" za kontakt formu). Epics.md Story 4.6 pominje `10/15m` standardizovan rate — 4.6 će uskladiti; 4.2 startuje sa `5/m` per project-context.md. Ako Step-02 traži `10/15m` već sada, lako menjati.
- **SM-D9 (ratelimit → HTTP 429 mehanizam) — RESOLVED (Iteration 1 CRIT-1):** Decorator je `@ratelimit(key="ip", rate="5/m", block=False)` (**NE `block=True`**). Sa `block=True`, `django_ratelimit` raise-uje `Ratelimited(PermissionDenied)` → Django renderuje **403**, a u repo-u NEMA `handler403`/`handler429`/`RATELIMIT_VIEW`/`Ratelimited`-catch (grep-verifikovano u config/ + apps/). To bi srušilo AC7 test koji asertuje 429. Rešenje (self-contained, bez projekt-globalnog handler-a): `block=False` postavlja `request.limited = True` kad je limit pređen; view na vrhu tela proverava `if getattr(request, "limited", False): return HttpResponse(status=429)`. Tako AC7 tačka „6. uzastopni submit → HTTP 429" ostaje i SADA je ostvariva. Story 4.6 može refaktorisati u zajednički decorator/handler kad standardizuje pattern (NE sada).
- **SM-D10 (ratelimit cache backend) — RESOLVED (Iteration 1 CRIT-1b):** Repo NEMA definisan `CACHES` (Django bi pao na implicitni LocMemCache — radi, ali nedeterministički za prod). 4.2 dodaje EKSPLICITAN `CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}` u `config/settings/base.py` (Task 6.0) da ratelimit brojač ima deterministički backend. YAGNI: locmem je dovoljan za v1 single-process — NE Redis/django-redis (project-context.md:84 „Bez Celery/Redis u v1"); shared cache za multi-worker prod je Epic 9/4.6 odluka. Test (Task 3.3) pinuje cache preko `@override_settings(CACHES=...)` + `cache.clear()` između testova da 5-ok/6-ti-429 granica bude pouzdana.
- **SM-D11 (skeleton anti-testovi se invertuju) — RESOLVED (Iteration 1 CRIT-2):** Story 3.3 `apps/pages/tests/test_contact_form_skeleton.py` (5 testova) asertuje disabled polja/submit, NEMA `hx-post`, „uskoro" hint prisutan. AC8/Task 8 INVERTUJU sve to (polja aktivna, `hx-post` dodat, hint uklonjen) → ti testovi PADAJU posle GREEN faze i blokiraju `just test`. TEA (NE Dev — project-context.md:294) ažurira tih 5 asercija na POST-4.2 realnost u Task 4.2; ovo je poznat TDD milestone (anti-testovi se flip-uju kad story oživi skelet) i NE smeju ostati crveni (project-context.md:296).
- **SM-D12 (swap target PINNED + dve a11y regije) — RESOLVED (Improvement pass):** (a) HTMX swap target je obuhvatajuća `<section class="coric-contact-form" aria-labelledby="contact-form-title">` (dodaje joj se `id="contact-form-section"`), `hx-swap="outerHTML"` (vidi SM-D6, više nije „Dev finalizuje"). (b) Error odgovor MORA imati DVE ODVOJENE a11y regije: in-form `role="alert"`/`aria-live="assertive"` summary (regija #1, AC4) I zaseban `hx-swap-oob` ka `#aria-live` `polite` singletonu (regija #2, AC6) — NE prepravljati singleton na `assertive`, NE implementirati samo jednu. Razrešeno u improvement pass-u (svi validatori konsenzus).
- **SM-D13 (double-submit / idempotency) — KNOWN MINOR (v1, forward → 4.6):** brz dvostruki klik (double-click pre nego što HTMX swap-uje formu) može kreirati 2 `Lead` reda — NEMA idempotency tokena ni server-side dedup u 4.2. Za v1 je prihvatljivo (lead duplikat je benigan, admin vidi oba). NE dodavati idempotency mašineriju u 4.2 (YAGNI / izvan scope-a) — forward na Story 4.6 kad standardizuje HTMX form pattern (može uvesti `hx-disabled-elt` na submit dugme + opcioni server-side dedup). Samo LOGOVANO ovde, NE rešavano.

## Open Questions
- **OQ-1 (SM-D5):** email-failure UX — čist success vs degradirani success? Default: čist success. Potvrda Step-02/Mihas.
- **OQ-2 (SM-D8):** ratelimit rate `5/m` (project-context) vs `10/15m` (epics 4.6) — kojim startovati? Default `5/m`.
- **OQ-3:** klijent IP rezolucija — goli `REMOTE_ADDR` (4.2) je dovoljan; trust-proxy/X-Forwarded-For header parsiranje defer na Epic 9 (nginx prod). Potvrda.
- **OQ-4 (SM-D6):** tačna partial dekompozicija (forms vs pages vlasništvo) — Dev finalizuje u GREEN; preporuka forms partials + tanak pages container.
- **OQ-5 (SM-D9) — RESOLVED:** ratelimit → 429 mehanizam: `block=False` + `request.limited` check (NE `block=True` koji daje 403). Razrešeno u Iteration 1 (CRIT-1). Story 4.6 može centralizovati handler.
- **OQ-6 (SM-D10) — RESOLVED:** ratelimit cache backend: eksplicitan locmem `CACHES` u base.py (NE Redis — YAGNI). Razrešeno u Iteration 1 (CRIT-1b). Prod shared cache = Epic 9/4.6.
- **OQ-7 (SM-D11) — RESOLVED:** skeleton anti-testovi (`test_contact_form_skeleton.py`) se invertuju u Task 4.2 (TEA posao). Razrešeno u Iteration 1 (CRIT-2).
- **OQ-8 (SM-D6/SM-D12) — RESOLVED:** swap target više nije „Dev finalizuje" — PINNED na `<section class="coric-contact-form">` sa dodatim `id="contact-form-section"`, `hx-swap="outerHTML"`. Razrešeno u improvement pass-u.
- **OQ-9 (SM-D13) — KNOWN MINOR:** double-submit (dvostruki klik → 2 Lead-a) — prihvaćeno za v1, forward na 4.6. NE rešavati u 4.2.
