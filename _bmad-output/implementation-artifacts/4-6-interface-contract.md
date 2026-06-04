---
story-id: 4-6-htmx-form-patterns-aria-live-oob-rate-limiting
artifact: interface-contract
phase: TEA-RED
module: forms
author: Test Architect (🧪)
created: 2026-06-04
status: red-tests-written
type: standardization-refactor (behavior-preserving)
---

# Story 4-6 — Interface Contract (TEA RED → Dev GREEN ugovor)

Ovaj dokument je **ugovor** koji TEA testovi specifikuju (RED) i koji Dev implementira (GREEN).
4-6 je **BEHAVIOR-PRESERVING standardizacija** zajedničke HTMX-form mašinerije — **NIJE feature**.
Dev menja STRUKTURU (dekorator + `{% include %}` + konstanta), NE posmatrano ponašanje.
**0 migracija. notifications.py NETAKNUT. forms.py NETAKNUT. Regija #1 (in-form assertive) NETAKNUTA.**

**Gate (AC1, tri uslova — NE puna bajt-identičnost CELOG HTTP odgovora):**
1. SVE postojeće `apps/forms` + `apps/pages` asercije ostaju zelene BEZ izmene;
2. NOVI `_oob_aria_live.html` je BAJT-identičan trenutnom inline OOB stringu (snapshot);
3. per-forma OOB poruke ostaju NEPROMENJENE.

---

## § 1 — Regression-lock net (POSTOJI kao test PRE refaktora — green now + after)

Fajl: `apps/forms/tests/test_form_endpoints_contract.py` (parametrizovano preko 4 endpointa:
`contact_submit`, `model_inquiry_submit`, `service_request_submit`, `part_request_submit`).
**30 testova, SVIH 30 GREEN protiv trenutnog (un-refaktorisanog) koda.** Ako ijedan padne POSLE
refaktora → refaktor je promenio ponašanje (regresija). Lockovani invarijanti (Task 1.2 a-h):

| inv | asercija (svi endpointi) |
|-----|--------------------------|
| (a) | GET → **405** (`@require_POST` SPOLJAŠNJI) |
| (b)/(h) | 6. POST istog IP-a → **429**, NIJEDAN status == 403 (block=False + request.limited) |
| (c) | success → **200** + EKSAKTAN per-forma OOB success marker UNUTAR `hx-swap-oob="innerHTML:#aria-live"` |
| (d) | error → **200** + in-form `role="alert" aria-live="assertive"` (regija #1) + OOB „Greška pri slanju, proverite polja." (regija #2) |
| (e) | non-HTMX POST → **NEMA** `hx-swap-oob` |
| (f) | 405-pre-429: GET na VEĆ rate-limitovanom IP-u → i dalje **405** |
| (g) | GET NE troši budžet: 5× GET (405) → validan POST → **200** (NIJE 429) |

Plus 2 model_inquiry divergencija locka:
- `test_model_inquiry_product_not_found_oob_preserved` — valid forma + nepostojeći slug → OOB
  „Proizvod nije pronađen." (regija #2) MORA ostati;
- `test_model_inquiry_error_oob_is_field_error_message` — invalid forma (validan slug) → OOB
  „Greška pri slanju, proverite polja." (NE product_not_found) → dokaz da tro-ishodni guard
  razlikuje dva error ishoda.

**Per-forma OOB success marker (LOCKED — TAČAN string):**
contact → „Upit je poslat." · model_inquiry → „Upit za model je poslat." ·
service → „Servisni zahtev je poslat." · part_request → „Upit za rezervni deo je poslat."

---

## § 2 — `htmx_form_endpoint` dekorator + `FORM_RATELIMIT_RATE` konstanta (AC2/AC3)

**Lokacija:** `apps/forms/views.py` (modul-level; dokumentovan u modul docstring-u — AC8). Dozvoljeno
je i `apps/forms/decorators.py` ako Dev preferira, ALI test introspekcija očekuje da su `FORM_RATELIMIT_RATE`
i `htmx_form_endpoint` **importabilni iz `apps.forms.views`** (re-export je u redu ako žive drugde).

```python
# apps/forms/views.py
FORM_RATELIMIT_RATE = "5/m"   # AC3 — behavior-preserving (SM-D3/SM-D9). epics.md:840 10/15m = OQ-1 PRODUKT odluka, NE primenjuje se.


def htmx_form_endpoint(view_func):
    """Zajednički HTMX-form meta-prefiks (AC2). Kanonski pattern (AC8) za buduće forme.

    Kompozicija (EKSPLICITNO — NE menjati redosled):
        require_POST( ratelimit(key="ip", rate=FORM_RATELIMIT_RATE, block=False)( guarded ) )
    → require_POST je NAJSPOLJAŠNJIJI; ratelimit je UNUTRAŠNJI; request.limited→429 guard
      se izvršava UNUTAR (posle) ratelimit wrappera.
    """
    @ratelimit(key="ip", rate=FORM_RATELIMIT_RATE, block=False)
    def _guarded(request, *args, **kwargs):
        if getattr(request, "limited", False):
            return HttpResponse(status=429)        # NE 403 (block=False — SM-D9)
        return view_func(request, *args, **kwargs)

    return require_POST(_guarded)
```

**EKSPLICITAN redosled kompozicije (CRITICAL — gate za AC2, ovaj redosled je LOCKED testovima):**
- `require_POST` **OUTERMOST** → GET vraća **405 PRE** nego django_ratelimit pozove
  `is_ratelimited(increment=True)` → GET **NE troši** 5/m budžet (lock (g)) i 405 precedira 429 (lock (f)).
- `@ratelimit(...block=False)` **INNER** → postavlja `request.limited` PRE nego in-dekorator guard čita flag.
- Pogrešan redosled bi ILI obrnuo 405-vs-429 ILI nečujno isključio rate limiting (security regresija).

Dekorator **enkapsulira** `if getattr(request, "limited", False): return HttpResponse(status=429)` —
iz sva 4 view-a se uklanja taj duplirani prefiks; telo (bind/invalid/valid/create/atomic/email) ostaje
NETAKNUTO (NE ekstrahovati telo — anti-YAGNI; telo divergira: atomic vs ne, FILES vs ne, product re-validacija).

**Primena (AC2):** sva 4 view-a dekorisana sa `@htmx_form_endpoint` umesto trenutnog
`@require_POST` + `@ratelimit(...)` para. Javni nazivi view-ova (`contact_submit` itd.) NETAKNUTI
(URLConf zavisi od njih).

**Test:** `apps/forms/tests/test_form_pattern_abstractions.py` — konstanta == "5/m"; dekorator postoji,
pozivljiv, i ponašanjem dokazuje kompoziciju (probe-view: GET→405, 5×GET-ne-troši-budžet, 6.POST→429,
NIJEDAN 403). **RED do Dev Task 2.** (`test_all_four_views_use_the_decorator` već je GREEN — tvrdi da
view-ovi i dalje postoje/pozivljivi POSLE refaktora.)

**Fallback (OQ-3):** ako kompozicija NE može da očuva (f)/(g)/(b) → prihvatljiv minimalan refaktor =
`FORM_RATELIMIT_RATE` konstanta + OOB include SAMO, ostavljajući `@require_POST`/`@ratelimit` kao
postojeće ulančane per-view dekoratore. U tom slučaju dekorator-specifični testovi se brišu/xfail-uju
uz SM odobrenje; regression-lock (§ 1) ostaje merodavan.

---

## § 3 — `_oob_aria_live.html` partial (AC4 — EKSPLICITAN per-forma recept)

**Kreiraj** `templates/forms/partials/_oob_aria_live.html` — guard `{% if request.htmx %}` je
**INTERNI**, partial prima `message`:

```django
{% if request.htmx %}<div hx-swap-oob="innerHTML:#aria-live">{{ message }}</div>{% endif %}
```

**BAJT-identičnost (LOCKED, Task 3.4):** renderovan partial (request.htmx aktivan) MORA biti `.strip()`-ovan
TAČNO jednak `<div hx-swap-oob="innerHTML:#aria-live">{message}</div>` za svaku poruku. non-HTMX →
prazan render (bez `hx-swap-oob`). Test: `test_oob_aria_live_contract.py::test_new_oob_partial_*`
(**RED do Dev Task 3.1**; pisani da FAIL-uju ČISTO — `pytest.fail` na `TemplateDoesNotExist`, NE ruše kolekciju).

### Per-forma include recept (Dev NE SME odstupiti)

| partial | uključuje `_oob_aria_live.html`? | recept |
|---------|----------------------------------|--------|
| `contact_success.html` | DA | `{% include "forms/partials/_oob_aria_live.html" with message=_("Upit je poslat.") %}` (BEZ spoljašnjeg uslova) |
| `model_inquiry_success.html` | DA | `... with message=_("Upit za model je poslat.") %}` |
| `service_request_success.html` | DA | `... with message=_("Servisni zahtev je poslat.") %}` |
| `part_request_success.html` | DA | `... with message=_("Upit za rezervni deo je poslat.") %}` |
| `_contact_form_fields.html` | DA | pod `{% if request.htmx and form.errors %}` … `{% endif %}`, `message=_("Greška pri slanju, proverite polja.")` |
| `_service_request_form_fields.html` | DA | isto kao gore |
| `_part_request_form_fields.html` | DA | isto kao gore |
| **`_model_inquiry_form_fields.html`** | **NE — KEEP INLINE** | vidi izuzetak ↓ |

### KEEP-INLINE izuzetak (`_model_inquiry_form_fields.html` — SM-D8, CRITICAL-1)

OOB blok OSTAJE DOSLOVNO 3-granski INLINE (NE forsiraj include — YAGNI + regression-safety > uniformnost):

```django
{% if request.htmx and product_not_found %}
  <div hx-swap-oob="innerHTML:#aria-live">{% translate "Proizvod nije pronađen." %}</div>
{% elif request.htmx and form.errors %}
  <div hx-swap-oob="innerHTML:#aria-live">{% translate "Greška pri slanju, proverite polja." %}</div>
{% endif %}
```

OBE OOB najave ostaju funkcionalne. `test_product_not_found_has_both_aria_regions` (4-3) +
`test_model_inquiry_product_not_found_oob_preserved` (4-6) MORAJU ostati zeleni. (Alternativa sa
dva include-poziva dozvoljena SAMO ako je bajt-identičnost dokazana; keep-inline je preferiran.)

---

## § 4 — Golden/contract OOB net (POSTOJI kao test PRE refaktora — green now + after)

Fajl: `apps/forms/tests/test_oob_aria_live_contract.py` (klasa 1 — GOLDEN/CONTRACT, **17 testova GREEN**).
Renderuje POSTOJEĆE partial-e direktno (bound forma + `request.htmx` stub) i tvrdi:
- (1) success (sve 4) → per-forma poruka u OOB;
- (2) error (sve 4) → „Greška pri slanju, proverite polja." u OOB;
- (3) product_not_found (model_inquiry) → „Proizvod nije pronađen." u OOB (+ NE „Greška…”);
- (4) non-HTMX (sve 4, success I error) → NEMA `hx-swap-oob`.

Ovaj net hvata svaku regresiju OOB izlaza (uključujući brisanje model_inquiry product_not_found
najave) NEZAVISNO od HTTP nivoa.

---

## § 5 — DO-NOT (granica refaktora)

- **notifications.py NETAKNUT** (AC6): `_no_crlf` + `BadHeaderError` subject-injection odbrana je
  security-critical i van opsega. send/subject ponašanje ostaje bajt-identično (postojeći
  `_xss`/`_email_failure`/subject testovi su regression net).
- **forms.py NETAKNUT** (SM-D7): widget id/required-set divergira — ekstrakcija bi bila spekulativna.
- **Regija #1 (in-form `role="alert" aria-live="assertive"` error summary) NETAKNUTA** (AC5 / IMP-C):
  ekstrahuj ISKLJUČIVO OOB „rep" (regija #2). Regija #1 takođe divergira (model_inquiry ima dodatnu
  product_not_found granu i tu) → VAN opsega.
- **Rate ostaje `5/m`** (AC3): NE 10/15m (to bi oborilo ~8 ratelimit testova). epics.md:840 10/15m +
  epics.md:842 429-body „Probajte ponovo kasnije" = OQ-1/OQ-1b PRODUKT follow-up (epic-closure integritet).
- **0 migracija** (AC9): `makemigrations --check --dry-run` ne sme generisati migraciju.
- **gettext msgid-jevi NEPROMENJENI** (AC4/Task 3.3): isti literali → catalog se ne menja.

---

## § 6 — Bajt-identičnost: precizna formulacija

- **Gate** = (§ 1 + § 4 substring asercije zelene) **I** (§ 3 `_oob_aria_live.html` `.strip()`-snapshot
  bajt-identičan inline stringu) **I** (per-forma poruke neizmenjene).
- **NIJE gate:** puna bajt-identičnost CELOG HTTP odgovora — `{% include %}` može uvesti trivijalne
  whitespace/newline razlike koje djade normalizuje (bila bi lažno-krhka).
