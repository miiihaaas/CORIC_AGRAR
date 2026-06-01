---
story-id: "3.3"
story-key: 3-3-kontakt-strana-sa-formom-i-mapom
artifact: interface-contract
created: 2026-06-01
author: TEA / Murat (autonomous RED phase)
purpose: Canonical contract za „Kontakt" statičku stranu — ContactView(TemplateView) u
         POSTOJEĆEM apps/pages/, URL pages:contact (/kontakt/), contact.html + 3 section
         partials (info → forma → mapa), Google Maps static iframe + C2 fallback,
         forward-compat skelet forme (disabled polja + CSRF + aria-describedby, BEZ
         funkcionalnog submit-a), NOVI contact-page.css, RAZREŠENJE header „Kontakt" nav
         placeholder-a (header.html:96 href="#" → pages:contact). 0 modela, 0 migracija,
         0 funkcionalne forme, 0 HTMX, 0 novih JS. Dev MORA satisfy svaku klauzulu u GREEN.
---

# Interface Contract — Story 3.3 „Kontakt" Strana

Story 3.3 dodaje `class ContactView(TemplateView)` u POSTOJEĆI `apps/pages/views.py` (pored
`HomeView`/`AboutView`, NE menja ih), registruje URL `pages:contact` → `/<lang>/kontakt/`,
renderuje `templates/pages/contact.html` sa 3 bloka u NORMATIVNOM DOM redu (**info → forma →
mapa**), uvodi JEDNU novu CSS komponentu (`static/css/components/contact-page.css`), i
RAZREŠAVA POSLEDNJI mrtav header nav placeholder (`header.html:96` „Kontakt" `href="#"` →
`pages:contact`). NEMA modela, migracija, funkcionalne forme, HTMX, novih JS modula. Mapa je
static Google Maps `<iframe>` (NULA JS) + tekstualni fallback. Forma je forward-compat skelet
(disabled polja + `{% csrf_token %}` + disabled submit + TODO Story 4.2 marker). Kontakt-info i
forma su hardcoded-translatable do Story 3-4 (SiteSettings) / Epic 4 (funkcionalna forma).

Ovaj ugovor enumeriše file-system delta + Python surface + URL surface + template/DOM surface +
forma/mapa contract + CSS klase + locale .po edits koje TEA RED-phase testovi verifikuju. Dev
GREEN-phase realizuje sve klauzule; bilo koje odstupanje vraća story u `paused`.

> **NAPOMENA O TEST PARSIRANJU (TEA-D1):** Projekat NEMA `beautifulsoup4` u `pyproject.toml`
> (verifikovano live — postojeći `apps/pages/tests/test_home_*` + `test_about_*` koriste
> **regex** parsiranje renderovanog HTML-a). Iako Story Task 9 nominalno pominje
> „BeautifulSoup", TEA poštuje POSTOJEĆU konvenciju istog modula i koristi **regex** za DOM
> assertion-e (mirror `test_about_template_structure.py`). Ovo NE menja kontrakt — samo
> mehaniku assertion-a.

---

## 1. File-system delta

| Path | Status | Vlasništvo |
|---|---|---|
| `apps/pages/views.py` | EDIT (Dev) | ADD `class ContactView(TemplateView)` POSLE `AboutView`: `template_name="pages/contact.html"` + `http_method_names = ["get", "head", "options"]` (C3 GET-only). NE menja `HomeView`/`AboutView`; NE importuje domain modele; NE dodaje `post()`. Opcioni `get_context_data()` SAMO za hardcoded kontakt-info literale (NE DB query). |
| `apps/pages/urls.py` | EDIT (Dev) | ADD `path("kontakt/", ContactView.as_view(), name="contact")` POSLE about path; import `ContactView`. |
| `templates/pages/contact.html` | NOVO (Dev) | `{% extends "base.html" %}` + title/meta_description + 3 `{% include %}` u NORMATIVNOM redu **info → forma → mapa**; NEMA `{% block scripts %}` dodatka (0 JS). |
| `templates/pages/partials/_contact_info.html` | NOVO (Dev) | `<section aria-labelledby="contact-info-title">` + Eyebrow + `<h2 id="contact-info-title">` + `<address>` (PUNI-dijakritik „Vojvođanska 1, Basaid, Srbija") + tel prodaja + tel servis (≥2 `tel:` linka) + email `mailto:` + radno vreme (`<dl>`/`<ul>`/`<table>`) + social (`aria-label`). Grep-abilni `{# IMP-SiteSettings(Story 3-4): ... #}` marker. Sve `{% translate %}`. |
| `templates/pages/partials/_contact_form.html` | NOVO (Dev) | `<section aria-labelledby="contact-form-title">` + Eyebrow + `<h2 id="contact-form-title">` + `<form method="post" aria-describedby="contact-form-hint" data-testid="contact-form">` (BEZ `action`/`hx-post`) + 4 polja (Ime*/Email*/Telefon/Poruka*) SVA `disabled` + vidljive `<label for>` + `{% csrf_token %}` + hint `id="contact-form-hint"` + submit `disabled aria-disabled data-testid="contact-submit"` + TODO Story 4.2 marker. |
| `templates/pages/partials/_contact_map.html` | NOVO (Dev) | `<section aria-labelledby="contact-map-title">` + Eyebrow + `<h2 id="contact-map-title">` + responsive aspect-ratio wrapper sa static `<iframe title="..." loading="lazy" referrerpolicy="...">` (literalni placeholder Maps Embed `src` — BEZ env-var) + C2 fallback (`<a rel="noopener noreferrer" target="_blank" href="https://maps.google.com/?q=...">` opisni tekst). Grep-abilni `{# CSP-NOTE(Epic 9): ... #}`. NULA JS. |
| `static/css/components/contact-page.css` | NOVO (Dev) | `coric-contact`/`coric-contact-info`/`coric-contact-form`/`coric-contact-map` BEM (+ `__el`/`--mod`). SVE `var(--token)`; layout vrednosti (aspect-ratio/px/%) dozvoljene; whitelist hex `#fff`/`#000`. NEMA url(). Responsive: mobile stack → desktop 2-kolone (`@media min-width: 768px`); map aspect-ratio; focus-visible; disabled stil. |
| `static/css/main.css` | EDIT (Dev) | +1 `@import url('./components/contact-page.css');` POSLE `about-page.css` (`main.css:50`). |
| `templates/partials/header.html` | EDIT (Dev) | `:96` „Kontakt" nav link `href="#"` → `href="{% url 'pages:contact' %}"` (SAMO wire URL; `aria-current` van scope-a). |
| `locale/{sr,hu,en}/LC_MESSAGES/django.po` | EDIT ×3 (Dev) | msgstr za nove msgid (title/meta, eyebrow-i, h2-ovi, radno vreme, form labele/hint, iframe title, social aria-label). sr pune dijakritike, NEMA ćirilice/šišane latinice. |
| `apps/pages/tests/test_contact_url.py` | NOVO (TEA) | AC1 (4) |
| `apps/pages/tests/test_contact_header_wired.py` | NOVO (TEA) | AC2 (2) |
| `apps/pages/tests/test_contact_template_structure.py` | NOVO (TEA) | AC3 + AC8 (5 core + 3 ekstra smoke) |
| `apps/pages/tests/test_contact_info.py` | NOVO (TEA) | AC4 (4) |
| `apps/pages/tests/test_contact_map.py` | NOVO (TEA) | AC5 (4) |
| `apps/pages/tests/test_contact_form_skeleton.py` | NOVO (TEA) | AC6 (5) |
| `apps/pages/tests/test_contact_page_css.py` | NOVO (TEA) | AC7 (3) |

**NETAKNUTO (regression guards):** `apps/pages/views.py` `HomeView`+`AboutView`;
`templates/pages/home.html`+`about.html` + svi `_home_*`/`_about_*` partials; `templates/base.html`;
`templates/partials/footer.html` (footer NEMA „Kontakt" nav link — SM-D3b no-op; NE diraj);
`header.html` osim `:96`; `static/css/tokens.css`; svi postojeći JS moduli (0 novog JS);
`config/settings/*` (NEMA CSP config — SM-D6/OQ-3); `config/urls.py`; `pyproject.toml`;
`apps/{brands,products,core,search,media_pipeline}/*`. **0 migracija, 0 modela, 0 asset-a**
(mapa je remote iframe).

---

## 2. Python surface — `apps/pages/views.py` `ContactView`

```python
class ContactView(TemplateView):
    template_name = "pages/contact.html"
    http_method_names = ["get", "head", "options"]   # C3 — deterministički GET-only
    # get_context_data() OPCIONO — SAMO hardcoded kontakt-info literali (radno vreme/telefoni);
    # NE DB query, NE domain import (v1 hardcoded-translatable; SM-D1/SM-D5).
```

- CBV `TemplateView` (NE FBV). `as_view()` u urls.py.
- **GET-only DETERMINISTIČKI:** `http_method_names` izostavlja `post` → Django `View.dispatch`
  vraća **HTTP 405** za POST `/sr/kontakt/`. NE dodavati `post()` metod (forma je skelet;
  funkcionalan submit ide na ZASEBAN `apps/forms` endpoint `/htmx/forme/kontakt/` u Story 4.2).
- `HomeView`/`AboutView` ostaju NETAKNUTI (regresija).

### `apps/pages/urls.py`

```python
app_name = "pages"
urlpatterns = [
    path("", HomeView.as_view(), name="home"),            # POSTOJEĆI — netaknut
    path("o-nama/", AboutView.as_view(), name="about"),   # POSTOJEĆI — netaknut
    path("kontakt/", ContactView.as_view(), name="contact"),  # NOVO
]
```

---

## 3. URL surface

| Name | Pattern (kroz i18n_patterns) | View | Reverse (sr) | POST |
|---|---|---|---|---|
| `pages:home` | `/<lang>/` | `HomeView` | `/sr/` (regresija) | — |
| `pages:about` | `/<lang>/o-nama/` | `AboutView` | `/sr/o-nama/` (regresija) | — |
| `pages:contact` | `/<lang>/kontakt/` | `ContactView` | `/sr/kontakt/` | **405** (GET-only) |

- Slug `kontakt` ASCII, ISTI za sva 3 locale (`/sr|hu|en/kontakt/`) — NEMA per-locale slug
  prevod (SM-D2/OQ-2).
- GET sva 3 locale → HTTP 200; `assertTemplateUsed(response, "pages/contact.html")`.
- POST `/sr/kontakt/` → **TAČNO 405** (deterministički — `http_method_names` bez `post`).

---

## 4. Template / DOM surface

### `templates/pages/contact.html`
- `{% extends "base.html" %}`; `{% load i18n static %}`.
- `{% block title %}` + `{% block meta_description %}` — OBA kroz `{% translate %}` (TEA NE
  asertira tačan literal — samo `<meta name="description">` postoji + neprazan/translatable).
- `{% block content %}` uključuje 3 partials TAČNIM (NORMATIVNIM) redom — **SM-D9 LOCK**:
  1. `pages/partials/_contact_info.html`
  2. `pages/partials/_contact_form.html`
  3. `pages/partials/_contact_map.html`
- **NEMA `{% block scripts %}` dodatka** (0 novog JS — SM-D7; mapa je static iframe, forma skelet).
- TAČNO 1 `<h1>` (page title — „Kontakt"/„Kontaktirajte nas"; SM-D10). Single `<main>` iz
  base.html (NE dupliran). Heading hijerarhija h1→h2(→h3) bez preskoka. NEMA ćirilice; pune dijakritike.
- DOM redosled testira se preko marker id-jeva: `contact-info-title` < `contact-form-title` < `contact-map-title`.

### `_contact_info.html` (AC4 / SM-D5)
- `<section aria-labelledby="contact-info-title">` + Section Eyebrow + `<h2 id="contact-info-title">`.
- **`<address>`** sa PUNI-dijakritik „Vojvođanska 1, Basaid, Srbija" (NE šišana „Vojvodjanska" —
  AC8/OQ-6; kontakt strana NE nasleđuje top-header/footer defekt).
- **Telefon prodaje:** `<a href="tel:+381230468168">` (+ `aria-label`) — REUSE top-header/footer.
- **Telefon servisa:** `<a href="tel:+381000000000">` placeholder „+381 XXX XXX XXX" (+ `aria-label`).
  → **≥2 ODVOJENA `tel:` linka** (FR-5 prodaja+servis).
- **Email:** `<a href="mailto:prodaja@coricagrar.rs">` — REUSE footer.
- **Radno vreme:** semantički `<dl>`/`<ul>`/`<table>` (Dev bira), hardcoded-translatable placeholder.
- **Social:** Facebook + Instagram (`href="#"` placeholder), translatable `aria-label` na svakom `<a>`.
- Grep-abilni marker: `{# IMP-SiteSettings(Story 3-4): zameni hardkodovane kontakt vrednosti {% site_setting %} tagom kad 3-4 stigne #}`.
- Sve UI labele/aria kroz `{% translate %}`; tel/email VREDNOSTI nisu prevodive.

### `_contact_form.html` (AC6 / SM-D8 — FORWARD-COMPAT SKELET)
- `<section aria-labelledby="contact-form-title">` + Section Eyebrow + `<h2 id="contact-form-title">`.
- `<form method="post" aria-describedby="contact-form-hint" data-testid="contact-form">` —
  EKSPLICITNO `method="post"`, **BEZ `action`** (C1), **BEZ `hx-post`** (Epic 4 scope).
- 4 polja — **SVA `disabled` u v1** (a11y silent-data-loss guard; van tab-reda):
  - Ime i prezime * — `<input type="text" id="..." required aria-required="true" disabled>` + `<label for>`
  - Email * — `<input type="email" ... required aria-required="true" disabled>` + `<label for>`
  - Telefon — `<input type="tel" ... disabled>` + `<label for>` (opciono)
  - Poruka * — `<textarea ... required aria-required="true" disabled>` + `<label for>`
  - Svaki `<label for="X">` referencira postojeći `id="X"` polja (asocijacija).
- **`{% csrf_token %}` PRISUTAN** (render-uje hidden `name="csrfmiddlewaretoken"`).
- **Hint:** vidljiv element `id="contact-form-hint"`, povezan preko `<form aria-describedby="contact-form-hint">`;
  copy preusmerava na tel/e-poštu („Forma će uskoro biti dostupna. Do tada nas kontaktirajte
  telefonom ili e-poštom.").
- **Submit:** `<button type="submit" class="coric-button coric-button--primary" data-testid="contact-submit" disabled aria-disabled="true">`.
- TODO marker: `{# TODO Story 4.2 (Epic 4): wire funkcionalan ContactForm + hx-post="/htmx/forme/kontakt/" + django-ratelimit + uspeh/greška HTMX pattern (Story 4.6). Ukloni disabled/aria-disabled. #}`.

### `_contact_map.html` (AC5 / SM-D6 — STATIC iframe + C2 fallback)
- `<section aria-labelledby="contact-map-title">` + Section Eyebrow + `<h2 id="contact-map-title">`.
- Responsive aspect-ratio wrapper sa static `<iframe>`:
  - `src` = LITERALNI placeholder Google Maps Embed URL ka Basaid (BEZ env-var — YAGNI; prost
    Embed nema secret/API ključ).
  - **`title` atribut** translatable + NEPRAZAN (WCAG a11y — NVDA accessible naziv).
  - **`loading="lazy"`** (performance).
  - `referrerpolicy="no-referrer-when-downgrade"`.
  - NULA JavaScript-a / Maps JS API / lib.
- **C2 FALLBACK** (uvek u DOM-u, čist HTML/CSS): adresa „Vojvođanska 1, Basaid, Srbija" (pune
  dijakritike) + `<a rel="noopener noreferrer" target="_blank" href="https://maps.google.com/?q=...">`
  sa OPISNIM prevodivim tekstom („Otvori lokaciju u Google Mapama" — NE goli URL).
- Grep-abilni: `{# CSP-NOTE(Epic 9): when django-csp enabled, add frame-src https://www.google.com + img-src *.google.com *.gstatic.com *.googleapis.com #}`.

### data-testid / marker surface (regresijski selektori)
| Selektor | Lokacija | Svrha |
|---|---|---|
| `[data-testid="contact-form"]` | `_contact_form.html` `<form>` | Form skelet + Story 4.2 wire verifikacija |
| `[data-testid="contact-submit"]` | `_contact_form.html` `<button>` | Submit disabled-state |
| `id="contact-info-title"` / `contact-form-title` / `contact-map-title` | h2 po bloku | DOM redosled lock (SM-D9) + aria-labelledby |
| `id="contact-form-hint"` | hint element | `aria-describedby` asocijacija |

---

## 5. CSS surface — `static/css/components/contact-page.css`

- BEM blokovi (SVI `coric-` prefiks): `coric-contact` (wrapper), `coric-contact-info`,
  `coric-contact-form`, `coric-contact-map` (+ `__element` / `--modifier`).
- SVE boje/spacing/radius kroz `var(--token)` (tokens.css). Whitelist hex: `#fff`/`#000`
  (+8-cifrene). Layout vrednosti (aspect-ratio `16 / 9`, px/%/vh/fr) su dozvoljene (nisu boje).
  NEMA url() (mapa je iframe, NE CSS bg).
- Responsive: info+forma 2-kolone desktop / stack mobile (`@media (min-width: 768px)`); map
  wrapper `aspect-ratio` + `iframe { width:100%; height:100%; border:0; }`; touch mete ≥ 44px.
- Disabled polja/dugme vizuelno prigušeno (`opacity` token/whitelist) + `cursor: not-allowed`;
  `:focus-visible` outline `var(--color-semantic-focus-ring)`.
- AKO Dev doda bilo koji `transition` → MORA `@media (prefers-reduced-motion: reduce)` guard
  (default: strana nema animacija, 0 JS).
- `static/css/main.css`: +1 `@import url('./components/contact-page.css');` POSLE `about-page.css`.

---

## 6. Locale .po surface (AC8)

- Novi msgid (sr/hu/en): page title, meta description, Section Eyebrow tekstovi
  („KONTAKTIRAJTE NAS"/„NAŠA LOKACIJA"/„POŠALJITE UPIT" ili sl.), 3 h2 naslova, „Telefon
  prodaje"/„Telefon servisa" aria-label, radno vreme labela+vrednosti, adresa, form labele
  (Ime i prezime/Email/Telefon/Poruka) + submit dugme tekst + hint copy, iframe `title`,
  fallback link tekst, social aria-label (Facebook/Instagram).
- Tel/email VREDNOSTI (`+381...`, `prodaja@...`) NISU prevodive — SAMO labele/aria.
- sr: pune dijakritike (č/ć/ž/š/đ); NEMA ćirilice; NEMA šišane latinice. 0 empty msgstr.
- hu + en prevodi popunjeni. Sva 3 locale render 200.

---

## 7. AC → test traceability

| AC | Test fajl | Testovi |
|---|---|---|
| AC1 | `test_contact_url.py` | resolves sr/hu/en (200), template used, reverse → /sr/kontakt/, home+about regresija |
| AC2 | `test_contact_header_wired.py` | header „Kontakt" href = /sr/kontakt/ (NE #); POST /sr/kontakt/ → TAČNO 405 (GET-only) |
| AC3+AC8 | `test_contact_template_structure.py` | 1 h1, 1 main, 3 bloka u redu info→forma→mapa, aria landmark, no ćirilica, heading hijerarhija, meta description, 1 h1 per-locale |
| AC4 | `test_contact_info.py` | `<address>` puni-dijakritik „Vojvođanska", ≥2 tel: (prodaja+servis), mailto:, radno vreme semantic |
| AC5 | `test_contact_map.py` | iframe prisutan, neprazan title, loading=lazy, C2 fallback link (maps.google + opisni tekst + noopener) |
| AC6 | `test_contact_form_skeleton.py` | csrf_token, 4 labeled fields (label↔id), submit disabled+aria-disabled, sva polja disabled + aria-describedby↔hint, no hx-post/action |
| AC7 | `test_contact_page_css.py` | @import u main.css, samo var(--token), coric- prefiks na svim klasama |

> **AC9 (A11y proxy) + AC9/AC10 Lighthouse (a11y ≥ 95 / Performance ≥ 80)** je MANUELNI Dev
> gate (Task 8) — NE automatizuje se u pytest-u. Automatizovani a11y proxy-ji (single h1/main,
> aria landmarks, iframe title, vidljive form labele + aria-required + disabled, fallback link,
> CSRF, focus-visible CSS) su pokriveni gore. Google Maps iframe behavior se NE unit-testira.

**Test count:** AC1=4, AC2=2, AC3+AC8=8 (5 core + heading-hierarchy + meta + per-locale h1×3
parametrizovano kao 1 fn → 3 case), AC4=4, AC5=4, AC6=5, AC7=3. Narativni minimum (27) je
pokriven; TEA je dodao 3 ekstra structure smoke testa (heading-hierarchy, meta-description,
per-locale-h1) mirror Story 3-2 obrasca.

---

## 8. RED-phase očekivanje

Pre Dev GREEN: `ContactView`/`pages:contact` NE postoje, `contact.html` + 3 partials NE
postoje, header „Kontakt" je još `href="#"`, `contact-page.css` NE postoji. Svi testovi
MORAJU pasti — NoReverseMatch (reverse) / 404→200 mismatch (GET) / 404≠405 (POST) /
TemplateDoesNotExist / `pages/contact.html` ne u renderu / fajl ne postoji / assertion (header
još `#`). **JEDINI dozvoljen PASS u RED fazi** je regresija-lock
`test_home_and_about_views_still_work` (Home + About i dalje 200 — verifikuje da ContactView
NE kvari postojeće strane; passuje jer Home/About već postoje). Bilo koji DRUGI PASS znači
preslab test.
