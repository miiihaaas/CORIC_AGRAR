---
story-id: 4-6-htmx-form-patterns-aria-live-oob-rate-limiting
epic: 4
title: "HTMX Form Patterns + aria-live OOB + Rate Limiting (STANDARDIZACIJA)"
status: ready-for-dev
module: forms
base-branch: master
created: 2026-06-04
author: SM (Scrum Master, 📋)
complexity: H
type: standardization-refactor
depends-on:
  - 4-1-lead-model-smtp-setup
  - 4-2-opsta-kontakt-forma-fr-5
  - 4-3-model-inquiry-form-sa-auto-popunjenim-modelom
  - 4-4-servisni-zahtev-form-sa-foto-upload-om
  - 4-5-rezervni-delovi-form
---

# Story 4-6: HTMX Form Patterns + aria-live OOB + Rate Limiting (STANDARDIZACIJA)

- **Story ID:** 4-6
- **Epic:** 4 — Lead-gen Forms & Email Delivery (POSLEDNJA story Epic-a 4)
- **Module:** `apps/forms` (cross-cutting refactor zajedničke HTMX-form mašinerije)
- **Status:** ready-for-dev
- **Tip:** STANDARDIZACIJA / REFACTOR — **NIJE** novi feature
- **Base branch:** master (radno stablo čisto; 4-1..4-5 sve komitovano)
- **Risk tier:** **HIGH** (cross-cutting refactor produkcijskog koda javnih formi; dodiruje security-relevantni ratelimit + subject-injection odbranu + file upload putanju)

---

## Opis (Description)

Konsoliduj dokazani HTMX-form pattern koji su Story-ji 4.2–4.5 već uspostavili
preko četiri submit endpointa (`contact_submit`, `model_inquiry_submit`,
`service_request_submit`, `part_request_submit`) u **zajedničku, ponovo
upotrebljivu apstrakciju** — bez ijedne promene posmatranog ponašanja.

Trenutno se kroz sva četiri view-a **doslovno ponavlja** sledeći oblik (vidi
„Kontekst iz postojećeg koda"):

```python
@require_POST
@ratelimit(key="ip", rate="5/m", block=False)
def <forma>_submit(request):
    if getattr(request, "limited", False):
        return HttpResponse(status=429)
    form = <Forma>(request.POST[, request.FILES])
    if not form.is_valid():
        return render(request, "<error_partial>", {...})
    ...  # Lead.objects.create(...) [+ atomic LeadAttachment] + send_lead_email + success partial
```

Ponavljaju se i template-i. **PRECIZNO (NE „svi identični" — ispravka rane pretpostavke):**
TRI forme — `_contact_form_fields.html`, `_service_request_form_fields.html`,
`_part_request_form_fields.html` — dele JEDNOSTAVAN **dvo-ishodni** guarded OOB blok
(samo `form.errors` ili ništa):

```django
{% if request.htmx and form.errors %}
  <div hx-swap-oob="innerHTML:#aria-live">{% translate "Greška pri slanju, proverite polja." %}</div>
{% endif %}
```

ALI `_model_inquiry_form_fields.html` **DIVERGIRA** — ima **tro-ishodni** OOB guard
(product_not_found / form.errors / ništa), jer 4-3 dodaje server-side product
re-validaciju:

```django
{% if request.htmx and product_not_found %}
  <div hx-swap-oob="innerHTML:#aria-live">{% translate "Proizvod nije pronađen." %}</div>
{% elif request.htmx and form.errors %}
  <div hx-swap-oob="innerHTML:#aria-live">{% translate "Greška pri slanju, proverite polja." %}</div>
{% endif %}
```

→ **Refaktor MORA OČUVATI ovu divergenciju.** model_inquiry zadržava OBA OOB ishoda
(product_not_found + form.errors); ne sme se naivno „izravnati" na dvo-ishodni guard
(to bi nečujno izbrisalo „Proizvod nije pronađen." najavu i oborilo postojeći test
`test_product_not_found_has_both_aria_regions`). Vidi SM-D8 i AC4 za eksplicitan
per-forma include recept.

Takođe se ponavlja i **in-form** `role="alert" aria-live="assertive"` error-summary blok
(regija #1) — ali i taj divergira: model_inquiry ima DODATNU `product_not_found` granu i
tu (vidi IMP-C / Task 3 DO-NOT). Regija #1 je VAN opsega ekstrakcije (AC5 je čuva as-is).

a svaki `*_success.html` deli identičan, guarded OOB blok sa per-forma porukom.

**Cilj:** ekstrahovati samo ono što je istinski duplirano 4× (ratelimit→429 guard
kao dekorator; OOB aria-live blok kao `{% include %}` parametrizovan porukom;
rate kao imenovana konstanta) i dokumentovati pattern u `apps/forms/views.py`,
**uz garanciju da svi postojeći testovi 4-1..4-5 ostaju zeleni i da je izlaz
sva četiri endpointa bajt-identičan** (isti status kodovi, isti partial-i, isti
`Lead.data` oblici, isti email subject-i/recipijenti, isto 429 ponašanje, isti
dvo-regioni aria-live HTML).

**OVO NIJE PROŠIRENJE OPSEGA.** Ako se tokom rada utvrdi da je apstrakcija
rizičnija od vrednosti koju donosi, prihvatljiv ishod je tanja konsolidacija
(samo konstanta za rate + OOB `{% include %}`) + regression-lock. YAGNI prevladava
(project-context.md:356-360).

---

## Kontekst iz postojećeg koda (REAL reference — pročitano, ne pretpostavljeno)

### Views — `apps/forms/views.py` (4 endpointa)
Sva četiri dele tačno isti prefiks: `@require_POST` + `@ratelimit(key="ip",
rate="5/m", block=False)` + na vrhu tela `if getattr(request, "limited", False):
return HttpResponse(status=429)` (4-2:38-42, 4-3:64-68, 4-4:112-116, 4-5:148-155).
- `contact_submit` (38-61): bind `ContactForm(request.POST)`; invalid → render
  `_contact_form_fields.html` (200); valid → `Lead.objects.create(... data={})` +
  `send_lead_email(lead)` + `contact_success.html`. **NEMA** `transaction.atomic`,
  **NEMA** `request.FILES`.
- `model_inquiry_submit` (64-109): bind `ModelInquiryForm`; SERVER-SIDE product
  re-validacija iz trusted `product_slug` (`Product.objects.filter(is_published=True,
  slug=...)`); nepostojeći/unpublished → error partial 200, **NE** Lead, **NE** email
  (SM-D2/SM-D8 iz 4-3); `data={"product_slug", "product_name"}` UVEK iz `Product` (DB),
  NIKAD iz POST stringa. **Ima granu sa dodatnim context-om** (`product`,
  `product_not_found`) — divergira od ostalih.
- `service_request_submit` (112-145): bind `ServiceRequestForm(request.POST,
  request.FILES)`; **`transaction.atomic`** oko `Lead.objects.create(...)` +
  `for f in cleaned_data["photos"]: LeadAttachment.objects.create(...)`;
  `send_lead_email(lead)` **IZVAN** atomic (C1/SM-D5 — email fail NE rollback-uje lead).
- `part_request_submit` (148-186): mirror 4-4; `transaction.atomic` oko Lead +
  opciona jedna slika (`photo = cleaned_data.get("photo")`); `send_lead_email` izvan atomic.

**Zapažanje za dizajn:** ratelimit→429 guard + `@require_POST` su IDENTIČNI 4×
(čista meta). Telo (bind → invalid/valid → create → email) divergira (atomic vs ne;
FILES vs ne; product re-validacija; per-forma data oblik). → **Ekstrahuj samo
zajednički meta-prefiks, NE telo** (telo bi tražilo callback-hell koji smanjuje
čitljivost — anti-YAGNI).

### Forms — `apps/forms/forms.py`
`ContactForm`/`ModelInquiryForm`/`ServiceRequestForm`/`PartRequestForm` — sve
`forms.Form` (NE ModelForm). Widget atributi, `gettext_lazy` labele/error poruke,
`id` konvencija (`contact-`/`inquiry-`/`service-`/`part-`) variraju po formi.
`clean_photos`/`clean_photo` rade foto double-check kroz `validate_image_mime`.
**Nema zajedničkog widget pattern-a koji se isplati ekstrahovati** (id-ovi i
required-set se razlikuju per forma; ekstrakcija bi bila spekulativna — NE dirati forme).

### Notifications — `apps/forms/notifications.py` (SECURITY — PRESERVE)
- `send_lead_email(lead)` (76-139): SYNC, view-called, save-before-send; C1
  failure contract — try/except `(AnymailError, smtplib.SMTPException, OSError,
  BadHeaderError)` → `logger.exception` + `return False`, NIKAD re-raise.
- `_build_subject` (47-63): per form_type subject sa `[Ćorić Agrar]`; sve user
  vrednosti kroz `_no_crlf(...)`.
- `_no_crlf` (35-43): **subject-injection odbrana** — strip CR/LF iz user-supplied
  Subject vrednosti (4-5 security). **Standardizacija NE SME dodirnuti ovaj fajl.**
- `_resolve_recipient` (66-73): recipient po form_type (CONTACT+MODEL_INQUIRY dele
  `CONTACT_EMAIL_TO`; SERVICE → `SERVICE_EMAIL_TO`; PART → `PARTS_EMAIL_TO`).

### Templates — `templates/forms/partials/` (8 fajlova)
- 4× `_<forma>_form_fields.html` — **NISU svi uniformni** (vidi SM-D8 / AC4 / AC5):
  - **3× jednostavne** (`_contact`/`_service_request`/`_part_request_form_fields.html`)
    dele **dvo-ishodni** OOB error blok na dnu (`form.errors` ili ništa):
    `{% if request.htmx and form.errors %}<div hx-swap-oob="innerHTML:#aria-live">
    {% translate "Greška pri slanju, proverite polja." %}</div>{% endif %}`.
  - **`_model_inquiry_form_fields.html` DIVERGIRA** — ima **tro-ishodni** OOB blok
    (`product_not_found` → „Proizvod nije pronađen." / `form.errors` → „Greška pri slanju,
    proverite polja." / ništa), jer 4-3 dodaje server-side product re-validaciju.
    Refaktor ČUVA ovu divergenciju (OOB blok OSTAJE INLINE — vidi AC4/SM-D8).
  - In-form `role="alert" aria-live="assertive"` summary blok (regija #1) je sličan kroz
    sve 4 forme ALI i on DIVERGIRA za model_inquiry (dodatna `product_not_found` grana i
    tu) → regija #1 je **VAN opsega ekstrakcije** (AC5 / Task 3 DO-NOT je čuva as-is).
  Sirovi `<input value="{{ form.X.value|default:'' }}">` None-safe idiom; `htmx-indicator`
  spinner; service/part imaju `enctype`/`hx-encoding="multipart/form-data"`.
- 4× `<forma>_success.html`: identičan guarded OOB blok sa **per-forma porukom**:
  - contact: „Upit je poslat."
  - model_inquiry: „Upit za model je poslat."
  - service: „Servisni zahtev je poslat."
  - part: „Upit za rezervni deo je poslat."

### Singleton — `templates/base.html:29` + `apps/core/templatetags/htmx_aria.py`
`{% aria_live %}` renderuje `<div id="aria-live" class="visually-hidden"
aria-live="polite" aria-atomic="true"></div>` (singleton). OOB blokovi ciljaju
`innerHTML:#aria-live` i **NE smeju** menjati `polite` na `assertive` (4-5 AC8).

### Settings — `config/settings/base.py:123-129`
`CACHES` = locmem `default` (ratelimit backend). Komentar VEĆ kaže: „prod
skaliranje (shared cache) je Epic 9\\4.6 odluka — NE Redis sada (YAGNI)". →
per-worker locmem nije bug za v1; **DEFER na Epic 9** (vidi OQ-2).

### Tests — `apps/forms/tests/` (regression ugovor koji MORA ostati zelen)
- `conftest.py`: autouse `_pin_and_clear_ratelimit_cache` (pinuje locmem +
  `cache.clear()` pre/posle); `htmx_post` helper (fiksni IP `203.0.113.7`,
  `HX-Request` header); per-forma payload/url fixtures; `published_product`.
- `test_*_ratelimit.py` (4×): tvrde 5-ok / 6-ti-429 granicu + „403 NIKAD" (block=False).
- `test_*_aria_live.py` (4×): tvrde dvo-regionsku strukturu (in-form assertive +
  OOB polite), per-forma success poruku, guard `{% if request.htmx %}`, singleton-ostaje-polite.
- `test_*_view.py` / `_errors.py` / `_email_failure.py` / `_xss.py` / `_security.py`:
  status kodovi, Lead.data oblici, email subject/recipient, C1 ponašanje.

**KRITIČNO (rate divergencija):** epics.md:840 piše `rate='10/15m'`; NFR-3
(epics.md:119) piše „10/15min IP". ALI 4-2..4-5 su shipovani sa **`5/m`** (SM-D9
locked, sa testovima koji tvrde 5-ok/6-ti-429). Promena rate-a na 10/15m bi
**promenila ponašanje i oborila ~8 postojećih ratelimit testova** → krši
behavior-preserving mandat ove story-je. → **Zadrži `5/m`** u refaktoru; rate→10/15m
je odvojena PRODUKT odluka (vidi OQ-1). Standardizacija centralizuje rate u
KONSTANTU tako da buduća promena bude jedno-mesto.

---

## Acceptance Criteria

**AC1 (REGRESSION-SAFETY — najvažniji).** Svi pre-postojeći `apps/forms` i `apps/pages`
testovi ostaju zeleni BEZ izmene assertion-a. Ponašanje sva četiri submit endpointa je
**SEMANTIČKI identično** pre i posle refaktora — gate je: (1) SVE postojeće asercije
(substring-bazirane) ostaju zelene; (2) `_oob_aria_live.html` partial je **BAJT-identičan**
trenutnom inline OOB stringu (snapshot, vidi Task 1.3/Task 3); (3) per-forma OOB poruke
ostaju NEPROMENJENE. Napomena: ekstrakcija `{% include %}`-a može uvesti trivijalne
whitespace/newline razlike koje djade normalizuje → **puna bajt-identičnost CELOG
HTTP odgovora NIJE gate** (bila bi lažno-krhka); gate je gore navedena tri uslova.
Pokriveno: isti HTTP status kodovi (200 success/error, 429 ratelimit, 405 GET, NIKAD 403),
isti renderovani partial-i, isti `Lead.data` oblici po form_type, isti email subject-i i
recipijenti, isto 429 ponašanje (block=False + `request.limited`), isti dvo-regionski
aria-live izlaz (uključujući model_inquiry tro-ishodni OOB). Dozvoljeno je DODATI nove
regression-lock testove, ali NIJE menjati postojeće. **Ovo je centralni / prvi
regression-safety AC.**

**AC2 (ratelimit→429 standardizacija).** Zajednički meta-prefiks (`@require_POST` +
`@ratelimit(key="ip", rate=<KONSTANTA>, block=False)` + `request.limited` → 429 guard)
ekstrahovan je u JEDNU ponovo upotrebljivu apstrakciju (dekorator) primenjenu na sva
četiri view-a. Rate je definisan kao imenovana konstanta (npr. `FORM_RATELIMIT_RATE = "5/m"`)
na jednom mestu. Posle ekstrakcije sva četiri view-a koriste identičan guard; 6. submit
sa istog IP-a → HTTP 429; različiti IP-ovi se broje odvojeno; NIKAD 403.

**AC3 (rate = `5/m`, NE promena ponašanja).** Rate ostaje `5/m` (behavior-preserving;
SM-D9 locked). Konstanta dokumentuje epics.md:840/NFR-3 `10/15m` divergenciju kao
odloženu PRODUKT odluku (OQ-1); refaktor je NE primenjuje.

**AC4 (OOB aria-live standardizacija — EKSPLICITAN per-forma include recept).**
Guarded OOB aria-live blok ekstrahovan je u JEDAN reusable partial
`forms/partials/_oob_aria_live.html`. **Izabrani pristup (locked, SM-D4):** partial
nosi `{% if request.htmx %}` guard **INTERNO** i prima `message` parametar:

```django
{# _oob_aria_live.html #}
{% if request.htmx %}<div hx-swap-oob="innerHTML:#aria-live">{{ message }}</div>{% endif %}
```

Pozivalac obezbeđuje SPOLJAŠNJI uslov (npr. `form.errors`) oko `{% include %}`. Renderovani
HTML je BAJT-identičan trenutnom inline bloku (isti string, isti guard, singleton ostaje
`polite`). **Per-forma include recept (Dev NE SME odstupiti):**

- **4× `*_success.html`:** JEDAN include sa per-forma success porukom (BEZ spoljašnjeg
  uslova — success se renderuje samo na success path-u):
  `{% include "forms/partials/_oob_aria_live.html" with message=_("Upit je poslat.") %}`
  i analogno „Upit za model je poslat." / „Servisni zahtev je poslat." / „Upit za rezervni
  deo je poslat." — ČUVAJU SE NEPROMENJENE.
- **3× jednostavne error forme** (`_contact`/`_service_request`/`_part_request_form_fields.html`):
  JEDAN include pod spoljašnjim `{% if request.htmx and form.errors %}` … `{% endif %}`
  uslovom, sa porukom „Greška pri slanju, proverite polja.".
- **`_model_inquiry_form_fields.html` (IZUZETAK — MORA zadržati OBA OOB ishoda):**
  **IZABRANI PRISTUP = OSTAVI POSTOJEĆI 3-granski OOB blok INLINE** (NE forsiraj include na
  ovaj jedan partial — YAGNI + regression-safety > uniformnost). Inline blok ostaje DOSLOVNO:
  ```django
  {% if request.htmx and product_not_found %}
    <div hx-swap-oob="innerHTML:#aria-live">{% translate "Proizvod nije pronađen." %}</div>
  {% elif request.htmx and form.errors %}
    <div hx-swap-oob="innerHTML:#aria-live">{% translate "Greška pri slanju, proverite polja." %}</div>
  {% endif %}
  ```
  → OBE OOB najave (product_not_found „Proizvod nije pronađen." + form.errors „Greška pri
  slanju, proverite polja.") ostaju funkcionalne. Postojeći test
  `test_product_not_found_has_both_aria_regions` MORA ostati zelen. (SM-D8 dokumentuje ovaj
  izuzetak.) Alternativa sa DVA include-poziva (jedan pod `{% if request.htmx and
  product_not_found %}` sa „Proizvod nije pronađen.", jedan pod `{% elif request.htmx and
  form.errors %}` sa „Greška pri slanju, proverite polja.") je dozvoljena samo ako je
  bajt-identičnost dokazana — ali keep-inline je preferiran zbog niže regresione površine.

**AC5 (dvo-regionska a11y struktura očuvana).** Posle svakog success-a screen
reader najavi (OOB polite, regija #2); posle svake greške najavi „Greška pri slanju,
proverite polja." (OOB polite) + in-form `role="alert" aria-live="assertive"` summary
(regija #1). Obe regije rade identično kao u 4-2..4-5; OOB NE postavlja `assertive`
na singleton.

**AC6 (subject-injection odbrana očuvana).** `_no_crlf` + `BadHeaderError` u C1
try/except ostaju netaknuti i funkcionalni; `apps/forms/notifications.py` se NE menja
(osim eventualnog dokumentacionog komentara, ako uopšte). Postojeći
`_xss`/`_email_failure`/subject testovi ostaju zeleni.

**AC7 (CSRF + i18n + file upload očuvani).** `{% csrf_token %}` prisutan u svim
formama (uključujući kroz refaktorisane partial-e); sve user-facing poruke kroz
`gettext`/`{% translate %}` sa punim dijakritikama (č/ć/ž/š/đ — NIKAD ćirilica/šišana);
`enctype`/`hx-encoding="multipart/form-data"` očuvani na service/part formama;
`transaction.atomic` granice oko Lead+LeadAttachment očuvane (send_lead_email IZVAN atomic).

**AC8 (pattern dokumentovan).** Reusable apstrakcija je dokumentovana u
`apps/forms/views.py` (docstring dekoratora + modul docstring) kao kanonski HTMX-form
pattern koji buduće forme (npr. epics.md:746 — kontakt strana „prati HTMX pattern iz
Story 4.6") REUSE-uju. Bez novih migracija.

**AC9 (lint/format/no-migrations).** `just lint` (ruff + djade) clean; `just test`
zelen; `python manage.py makemigrations --check --dry-run` NE generiše migraciju
(refaktor ne dira modele).

---

## Tasks / Subtasks (TDD-ordered: TEA-RED → Dev-GREEN)

> Disciplina (project-context.md:293-298): **TEA piše testove (RED), Dev piše kod
> (GREEN). Dev NIKAD ne piše testove.** Testovi se komituju PRE implementacije.

### Task 1 — TEA: Regression-lock baseline (RED, pre ikakvog refaktora)
- 1.1 Potvrdi da SVI postojeći `apps/forms` testovi prolaze na `master` PRE rada
  (`just test apps/forms`) — to je zlatna baseline. Zabeleži broj testova.
- 1.2 Dodaj **regression-lock** test (`test_form_endpoints_contract.py`) koji
  parametrizovano preko sva 4 endpointa tvrdi invariante koje refaktor MORA očuvati:
  (a) GET → 405 (`@require_POST`); (b) 6. submit istog IP-a → 429, NIKAD 403;
  (c) success → 200 + **TAČAN per-forma OOB success marker** u
  `hx-swap-oob="innerHTML:#aria-live"` (asertuj EKSAKTNI string po formi, da refaktor
  koji zameni poruke između formi BUDE uhvaćen): contact → „Upit je poslat."; model_inquiry
  → „Upit za model je poslat."; service → „Servisni zahtev je poslat."; part_request →
  „Upit za rezervni deo je poslat." (verifikovano protiv stvarnih
  `templates/forms/partials/*_success.html`); (d) error → 200 + in-form
  `role="alert"` + OOB `hx-swap-oob="innerHTML:#aria-live"`; (e) non-HTMX POST →
  NEMA `hx-swap-oob`. (Konsoliduje rasute aria/ratelimit asercije u jedan tabelarni lock.)
  **Dodatni dekorator-redosled lockovi (CRITICAL-3 — gate za AC2):**
  (f) **405-pre-429 precedencija:** GET kad je IP VEĆ rate-limitovan i dalje vraća 405
  (require_POST je SPOLJAŠNJI → 405 pre nego ratelimit wrapper uopšte odluči o 429);
  (g) **GET NE troši rate budžet:** 5× GET (svaki 405) PA ZATIM validan POST → POST
  uspeva (200), NIJE 429 — dokaz da require_POST kratko-spaja GET PRE nego
  django_ratelimit pozove `is_ratelimited(increment=True)`; (h) (već u (b)) 6. POST
  istog IP-a → 429, NIKAD 403. Ovi lockovi MORAJU ostati zeleni i pre i posle refaktora.
- 1.3 **CONTRACT/golden test protiv TRENUTNOG inline OOB izlaza** (NE snapshot
  još-nepostojećeg `_oob_aria_live.html` — taj bi dizao `TemplateDoesNotExist` i ne bi
  čisto pao RED). Renderuj POSTOJEĆE `*_form_fields.html` + `*_success.html` partial-e sa
  bound kontekstom i tvrdi TAČNE OOB substring-ove za SVE guard/poruka kombinacije koje
  net MORA uhvatiti:
  - (1) **success** → `{% if request.htmx %}` aktivan + per-forma success poruka
    („Upit je poslat." / „Upit za model je poslat." / „Servisni zahtev je poslat." /
    „Upit za rezervni deo je poslat.") u OOB `hx-swap-oob="innerHTML:#aria-live"`;
  - (2) **error** (sve 4 forme) → `{% if request.htmx and form.errors %}` aktivan + OOB
    sadrži „Greška pri slanju, proverite polja.";
  - (3) **product_not_found** (SAMO model_inquiry) → `{% if request.htmx and
    product_not_found %}` aktivan + OOB sadrži „Proizvod nije pronađen.";
  - (4) **non-HTMX POST** (bez `HX-Request`) → NEMA `hx-swap-oob` u izlazu (guard
    isključen).
  Ovaj golden test je deo PRE-refaktor baseline-a (lovi svaku regresiju OOB izlaza).
  **ODVOJENO** (NE deo pre-refaktor baseline-a): bajt-identičnost snapshot novog
  `_oob_aria_live.html` partiala dodaje se TEK POSLE njegovog kreiranja u Task 3
  (vidi Task 3.4).
- 1.4 Dodaj test koji tvrdi da je rate KONSTANTA = `"5/m"` (import iz views modula) i
  da je dekorator primenjen na sva 4 view-a (introspekcija — npr. dekorisani view ima
  ratelimit wrapper; 6-ti-429 i dalje stoji).

### Task 2 — Dev: Ekstrahuj ratelimit→429 dekorator (GREEN)
- 2.1 U `apps/forms/views.py` definiši `FORM_RATELIMIT_RATE = "5/m"` (modul-level
  konstanta) + dekorator `htmx_form_endpoint` (ili ekvivalent) koji uvezuje
  `@require_POST` + `@ratelimit(key="ip", rate=FORM_RATELIMIT_RATE, block=False)` +
  `request.limited` → `HttpResponse(status=429)` guard. Docstring sa C1/SM-D9 ref-om.
  **EKSPLICITAN redosled kompozicije (CRITICAL — gate za AC2):** dekorator MORA primeniti
  wrappere tako da je `require_POST` **NAJSPOLJAŠNJIJI** (OUTERMOST), a `@ratelimit(key="ip",
  rate=FORM_RATELIMIT_RATE, block=False)` **UNUTRAŠNJI** (INNER), tačno preslikavajući
  trenutni stack-redosled `@require_POST` (gore) / `@ratelimit` (ispod). Guard
  `if getattr(request, "limited", False): return HttpResponse(status=429)` izvršava se
  UNUTAR (posle) ratelimit wrappera. **RAZLOG (NE menjati redosled):**
  (1) require_POST se izvršava PRVI → GET vraća 405 PRE nego django_ratelimit wrapper
  uopšte izvrši `is_ratelimited(increment=True)` → GET NE troši 5/m budžet;
  (2) `request.limited` flag MORA biti postavljen od strane ratelimit wrappera PRE nego
  in-dekorator guard `if getattr(request,"limited",False)` pročita taj flag.
  Pogrešan redosled bi ILI obrnuo 405-vs-429 precedenciju ILI nečujno isključio rate
  limiting (security regresija). Konkretno: ako koristiš `@require_POST` pa
  `@ratelimit(...)` kao dva ulančana dekoratora unutar `htmx_form_endpoint`-a, primeni ih
  u istom redosledu kao trenutni stack (require_POST najgornji = primenjen poslednji =
  najspoljašnjiji wrapper).
- 2.2 Primeni dekorator na sva 4 view-a; ukloni dupliranu `if getattr(request,
  "limited", False)` granu iz tela. Telo (bind/invalid/valid/create/atomic/email)
  ostaje NETAKNUTO — NE pokušavaj ekstrahovati telo (anti-YAGNI; telo divergira).
- 2.3 Potvrdi (kroz Task 1.2 (f)/(g)/(h) lockove) da kompozicija iz 2.1 očuvava: (i)
  405-pre-429 precedenciju; (ii) GET NE troši rate budžet; (iii) `request.limited`
  timing (ratelimit wrapper postavi flag PRE nego guard čita). Replikuj postojeći
  redosled TAČNO (vidi 2.1). **Ako ijedan od ovih lockova padne** → fallback po OQ-3
  (tanja konsolidacija bez dekoratora).

### Task 3 — Dev: Ekstrahuj OOB aria-live partial (GREEN)
- 3.1 Kreiraj `templates/forms/partials/_oob_aria_live.html` — guard `{% if request.htmx %}`
  je INTERNI, partial prima `message` parametar (vidi AC4 izabrani pristup):
  `{% if request.htmx %}<div hx-swap-oob="innerHTML:#aria-live">{{ message }}</div>{% endif %}`.
  Bajt-identičan izlaz trenutnom inline OOB stringu.
- 3.2 Zameni inline OOB blok PO RECEPTU iz AC4 (NE naivno izravnati):
  - **4× `*_success.html`:** jedan include sa per-forma success porukom (bez spoljašnjeg uslova).
  - **3× jednostavne** (`_contact`/`_service_request`/`_part_request_form_fields.html`):
    include pod spoljašnjim `{% if request.htmx and form.errors %}` sa „Greška pri slanju,
    proverite polja.".
  - **`_model_inquiry_form_fields.html`: NE menjaj OOB blok — OSTAJE 3-granski INLINE**
    (izabrani keep-inline pristup, SM-D8). OBA ishoda (product_not_found „Proizvod nije
    pronađen." + form.errors „Greška pri slanju, proverite polja.") ostaju DOSLOVNO. Test
    `test_product_not_found_has_both_aria_regions` MORA ostati zelen.
  - **DO-NOT (IMP-C / AC5 granica):** ekstrahuj ISKLJUČIVO OOB aria-live „rep" (regija #2).
    NE ekstrahuj i NE diraj in-form `role="alert" aria-live="assertive"` error-summary
    (regija #1) — i ona je ne-uniformna (model_inquiry ima dodatnu product_not_found granu
    i tu) i VAN je opsega ekstrakcije.
- 3.3 Potvrdi djade format + da `{% translate %}` poruke ostaju iste literale (gettext
  catalog se NE menja — iste msgid-jeve).
- 3.4 **POSLE kreiranja partiala** (NE deo pre-refaktor baseline-a): dodaj snapshot test
  koji tvrdi da `_oob_aria_live.html` renderuje BAJT-identičan string trenutnom inline OOB
  bloku (per `message` vrednost). Ovo je odvojena asercija od golden testa iz Task 1.3.

### Task 4 — Dev: Dokumentuj pattern + verifikuj no-migration (GREEN)
- 4.1 Ažuriraj modul docstring `apps/forms/views.py` da opisuje kanonski reusable
  HTMX-form pattern (dekorator + OOB include) za buduće forme (AC8 / epics.md:746).
- 4.2 `python manage.py makemigrations --check --dry-run` → NEMA migracije.

### Task 5 — TEA + Dev: Zeleni pregled (GREEN)
- 5.1 `just test apps/forms apps/pages` — SVE zeleno (baseline broj iz 1.1 + novi
  lock testovi). Nijedan postojeći assertion izmenjen.
- 5.2 `just lint` (ruff + djade) clean.
- 5.3 **SUPLEMENTARNO (NE primarni gate):** Manuelni diff renderovanog izlaza pre/posle za
  1 success + 1 error po formi kao sanity-check. **PRIMARNI regression gate je AUTOMATIZOVAN**
  lock: Task 1.2 contract test + Task 1.3 OOB golden/contract test + Task 3.4 snapshot +
  svi legacy testovi 4-1..4-5 ostaju zeleni. Ovaj manuelni diff NIJE autoritativni
  bajt-identičnost gate (poravnato sa AC1 — vidi IMP-A reformulaciju AC1).

---

## SM Decisions (log)

- **SM-D1 (scope = tanak refaktor + lock, NE prepisivanje tela).** epics.md:845
  eksplicitno traži „Pattern dokumentovan kao reusable mixin/decorator". Genuino
  je duplirano 4×: (a) ratelimit→429 meta-prefiks, (b) OOB aria-live blok, (c) rate
  literal. Ekstrahuj TAČNO ta tri. Telo view-a (bind/create/atomic/email) divergira
  po formi (atomic vs ne, FILES vs ne, product re-validacija) → NE ekstrahovati (callback
  apstrakcija bi smanjila čitljivost — anti-YAGNI, project-context.md:356-360).
- **SM-D2 (dekorator, NE mixin).** View-ovi su FBV (ne CBV) → dekorator je idiomatska
  apstrakcija (mixin bi tražio CBV konverziju = veliki, rizičan refaktor van opsega).
  epics.md kaže „mixin/decorator" (ILI) → biramo dekorator.
- **SM-D3 (rate = `5/m`, behavior-preserving).** epics.md:840/NFR-3 piše `10/15m`,
  ali 4-2..4-5 shipovali `5/m` (SM-D9 locked, sa testovima). Behavior-preserving
  mandat ove story-je nadjačava → zadrži `5/m`; centralizuj u konstantu da promena
  bude jedno-mesto. Rate→10/15m je odvojena PRODUKT odluka (OQ-1).
- **SM-D4 (OOB kao `{% include %}`, NE custom tag).** `{% aria_live %}` tag VEĆ
  postoji za singleton (htmx_aria.py); OOB announce blok je čisto template fragment
  sa parametrom-porukom → `{% include %}` je dovoljan (custom tag bi bio over-engineering).
- **SM-D5 (notifications.py NETAKNUT).** Subject-injection odbrana (`_no_crlf` +
  `BadHeaderError`) je security-critical i van opsega standardizacije HTMX patterna.
  NE dirati osim eventualnog komentara.
- **SM-D6 (per-worker locmem cache → DEFER Epic 9).** base.py:125-126 komentar VEĆ
  flaguje shared-cache kao Epic 9 odluku. Refaktor NE rešava prod multi-worker
  ratelimit (YAGNI v1) — samo flaguj (OQ-2).
- **SM-D7 (forms.py NETAKNUT).** Widget id/required-set divergira po formi; ekstrakcija
  bi bila spekulativna. NE dirati forme.
- **SM-D8 (model_inquiry granjanje + OOB izuzetak očuvani).** `model_inquiry_submit` ima
  dodatni `product`/`product_not_found` context i server-side product re-validaciju (4-3
  SM-D2/D8); dekorator pokriva SAMO meta-prefiks, telo (uključujući tu granu) ostaje
  doslovno. **OOB IZUZETAK (CRITICAL-1):** dok tri jednostavne forme imaju dvo-ishodni OOB
  guard (`form.errors` ili ništa), `_model_inquiry_form_fields.html` ima **tro-ishodni**
  OOB guard (`product_not_found` → „Proizvod nije pronađen." / `form.errors` → „Greška pri
  slanju, proverite polja." / ništa). Refaktor ČUVA ovu divergenciju: model_inquiry OOB blok
  **OSTAJE INLINE 3-granski** (NE forsira se `{% include %}` na njega — YAGNI +
  regression-safety > uniformnost). Naivno izravnavanje na dvo-ishodni guard bi nečujno
  izbrisalo „Proizvod nije pronađen." najavu i oborilo postojeći test
  `test_product_not_found_has_both_aria_regions` (koji tvrdi taj substring u OOB regiji).
  Tri jednostavne forme + 4 success partiala koriste novi `_oob_aria_live.html` include
  (vidi AC4 recept).

---

## Open Questions

- **OQ-1 (PRODUKT — rate 5/m vs 10/15m).** epics.md:840 + NFR-3 traže `10/15m`;
  shipovano je `5/m`. Ova story zadržava `5/m` (behavior-preserving). Da li biznis
  želi `10/15m`? Ako da → ZASEBNA story (menja ponašanje + ratelimit testove); ova
  centralizuje rate u konstantu da ta promena bude trivijalna. **Step-02 / produkt
  sign-off.** ⚠️ **EPIC-CLOSURE INTEGRITET (IMP-B):** 4-6 je POSLEDNJA story Epic-a 4 →
  OQ-1 (rate 5/m vs epics 10/15m) MORA biti eksplicitno rutiran ka produktu / praćen kao
  follow-up, da Epic 4 NE zatvori sa nečujno-neispunjenim epic-level AC-om (epics.md:840/842).
- **OQ-1b (429 BODY poruka — DEFER + epic-closure).** epics.md:842 specificira 429 BODY
  poruku „Probajte ponovo kasnije", ali shipovani kod vraća `HttpResponse(status=429)` sa
  **PRAZNIM telom**. Ova story je behavior-preserving → ZADRŽAVA prazno 429 telo i DEFERUJE
  poruku. ⚠️ Pošto je 4-6 poslednja story Epic-a 4, i ova 429-body divergencija MORA biti
  rutirana ka produktu / praćena kao follow-up (isti razlog kao OQ-1).
- **OQ-2 (prod multi-worker ratelimit cache).** locmem je per-process → u prod-u sa
  N gunicorn worker-a stvarni rate je ~N×5/m. Shared cache (Redis/DB) → **DEFER Epic 9**
  (base.py:125 već flaguje). Potvrditi da je Epic 9 vlasnik.
- **OQ-3 (obim ekstrakcije — eksplicitan fallback).** Ako TEA baseline + Task 1.2
  lockovi (f)/(g)/(h) pokažu da dekorator-kompozicija NE može da očuva `request.limited`
  timing ILI 405-vs-429 precedenciju ILI GET-ne-troši-budžet ILI ruši ijedan postojeći
  ratelimit test → prihvatljiv minimalni refaktor je **`FORM_RATELIMIT_RATE` konstanta +
  OOB include SAMO**, ostavljajući `@require_POST` i `@ratelimit` kao postojeće ULANČANE
  per-view dekoratore (ZERO rizik po ratelimit semantiku). **Dev gate u Task 2.3.**
- **OQ-4 (epics.md:746 zavisnost).** Kontakt strana (Story 3-3) „prati HTMX pattern
  iz Story 4.6" — VEĆ je done i koristi `_contact_form_fields.html`. Refaktor mora
  očuvati taj include-ugovor (pages testovi u AC1 scope-u).
- **OQ-5 (DOC inkonzistentnost u project-context.md — DEFER, NE rešavati u ovoj story-ji).**
  `project-context.md` (~linije 608-615) prikazuje ratelimit primer sa `block=True` kao
  „✅ UVEK" ispravan pattern, što je **INKONZISTENTNO** sa odlukom sprovedenom kroz 4-2..4-6
  (`block=False` + `request.limited` → 429). To može zbuniti Dev-a koji čita project-context.md.
  Ispravka je DOC fix u **DRUGOM fajlu** (`project-context.md`), VAN opsega ove story `.md` →
  NE menjati project-context.md iz ovog taska. Flag-ovano kao poznata doc-inkonzistentnost
  za zasebnu korekciju (SM note).
