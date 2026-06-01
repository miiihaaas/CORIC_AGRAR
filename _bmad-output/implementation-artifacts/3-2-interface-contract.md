---
story-id: "3.2"
story-key: 3-2-o-nama-strana
artifact: interface-contract
created: 2026-06-01
author: TEA / Murat (autonomous RED phase)
purpose: Canonical contract za „O nama" statičku stranu — AboutView(TemplateView) u POSTOJEĆEM
         apps/pages/, URL pages:about (/o-nama/), about.html + 4 section partials, NOVI
         timeline-reveal.js (IntersectionObserver reveal), NOVI about-page.css, REUSE
         GLightbox/lightbox-init.js za masonry galeriju (0 novog lightbox JS), i RAZREŠENJE
         Story 3-1 placeholder-a (home „Saznaj više" CTA + header „O nama" nav wire + :71
         „Pocetna"→„Početna" dijakritik fix). Dev MORA satisfy svaku klauzulu u GREEN phase.
---

# Interface Contract — Story 3.2 „O nama" Strana

Story 3.2 dodaje `class AboutView(TemplateView)` u POSTOJEĆI `apps/pages/views.py` (pored
`HomeView`, NE menja ga), registruje URL `pages:about` → `/<lang>/o-nama/`, renderuje
`templates/pages/about.html` sa 4 sekcije (hero → naša-priča → vremenska-lenta → galerija),
uvodi JEDAN novi JS modul (`static/js/timeline-reveal.js`) + JEDNU novu CSS komponentu
(`static/css/components/about-page.css`), i RAZREŠAVA dva Story 3-1 odložena placeholder-a
(home „Saznaj više" CTA + header „O nama" nav link). Galerija REUSE-uje GLightbox vendor +
`lightbox-init.js` (Story 2-5) — NULA novog lightbox/gallery JS. NEMA modela, migracija, formi,
HTMX. Sadržaj je hardcoded-translatable Lorem Ipsum (CMS je Epic 8 Story 8.8).

Ovaj ugovor enumeriše file-system delta + Python surface + URL surface + template/DOM surface +
CSS klase + JS modul surface + locale .po edits koje TEA RED-phase testovi verifikuju. Dev
GREEN-phase realizuje sve klauzule; bilo koje odstupanje vraća story u `paused`.

> **NAPOMENA O TEST PARSIRANJU (TEA-D1):** Projekat NEMA `beautifulsoup4` u `pyproject.toml`
> (verifikovano live 2026-06-01 — postojeći `apps/pages/tests/test_home_*` koriste **regex**
> parsiranje renderovanog HTML-a, vidi `test_home_template_structure.py:3`). Iako Story Task 9
> nominalno pominje „BeautifulSoup", TEA poštuje POSTOJEĆU konvenciju istog modula i koristi
> **regex** za DOM assertion-e (mirror `test_home_hero.py` / `test_home_template_structure.py`).
> Ovo NE menja kontrakt — samo mehaniku assertion-a.

---

## 1. File-system delta

### Fajlovi koji MORAJU postojati / biti izmenjeni posle GREEN phase (7 NOVO kod + 2 asset grupe + 8 fizičkih EDIT, 0 DELETE, 0 migracija)

| Path | Status | Vlasništvo |
|---|---|---|
| `apps/pages/views.py` | EDIT (Dev) | ADD `class AboutView(TemplateView)` (`template_name="pages/about.html"`); NE menja `HomeView`; NE importuje domain modele za AboutView |
| `apps/pages/urls.py` | EDIT (Dev) | ADD `path("o-nama/", AboutView.as_view(), name="about")` POSLE home path; import `AboutView` |
| `templates/pages/about.html` | NOVO (Dev) | `{% extends "base.html" %}` + title/meta_description + 4 `{% include %}` REDOM + `{% block scripts %}{{ block.super }}` + timeline-reveal.js `defer` |
| `templates/pages/partials/_about_hero.html` | NOVO (Dev) | Hero — dekorativna foto-pozadina `<img>` (alt="" aria-hidden) + hero_overlay_card `variant="green"` (h1); `<section aria-label>` |
| `templates/pages/partials/_about_story.html` | NOVO (Dev) | „Naša priča" — bela pozadina + dekorativni watermark logo `<img aria-hidden>` + Section Eyebrow + `<h2 id>` + ≥2 `<p>` translatable |
| `templates/pages/partials/_about_timeline.html` | NOVO (Dev) | Vremenska lenta — Section Eyebrow + `<h2 id>` + `<ol data-timeline>` sa ≥3 `<li data-timeline-segment>` (godina+h3+opis); dekorativni SVG/CSS `aria-hidden` |
| `templates/pages/partials/_about_gallery.html` | NOVO (Dev) | Masonry galerija — Section Eyebrow + `<h2 id>` + 6-9 `<a class="glightbox" data-gallery="o-nama-galerija"><img alt loading="lazy">` |
| `static/js/timeline-reveal.js` | NOVO (Dev) | Vanilla IIFE — IntersectionObserver reveal; mirror `statistic-counter.js`; `coric-js` marker, reduced-motion instant, threshold 0.3, unobserve, IO fallback |
| `static/css/components/about-page.css` | NOVO (Dev) | `coric-about-hero/story/timeline/gallery` BEM; SVE `var(--token)`; reveal transition 800ms; reduced-motion guard; gejtovan hidden state |
| `static/css/main.css` | EDIT (Dev) | +1 `@import url('./components/about-page.css');` POSLE home-page.css |
| `templates/pages/partials/_home_about_intro.html` | EDIT (Dev) | RAZREŠI placeholder: `href="#"`→`{% url 'pages:about' %}`; UKLONI `aria-disabled`/`tabindex="-1"`/`role="button"`/TODO; ZADRŽI `data-testid="home-about-cta"` |
| `templates/partials/header.html` | EDIT (Dev) | `:95` „O nama" `href="#"`→`{% url 'pages:about' %}`; `:71` `{% translate "Pocetna" %}`→`{% translate "Početna" %}` (dijakritik fix) |
| `locale/sr/LC_MESSAGES/django.po` | EDIT (Dev) | sr msgstr za nove msgid + „Početna" |
| `locale/hu/LC_MESSAGES/django.po` | EDIT (Dev) | hu prevodi |
| `locale/en/LC_MESSAGES/django.po` | EDIT (Dev) | en prevodi |
| `static/img/about/hero-o-nama.jpg` | NOVO asset (Dev) | Hero foto-pozadina placeholder ≤300KB ~1920px (OQ-2 production blocker) |
| `static/img/about/gallery/*.jpg` | NOVO asset grupa (Dev) | 6-9 placeholder galerijskih slika različitih dimenzija (OQ-2) |
| `apps/pages/tests/test_about_url.py` | NOVO (TEA) | AC1 |
| `apps/pages/tests/test_about_home_cta_wired.py` | NOVO (TEA) | AC2 (Story 3-1 razrešenje) |
| `apps/pages/tests/test_about_template_structure.py` | NOVO (TEA) | AC3 + AC9 |
| `apps/pages/tests/test_about_hero_story.py` | NOVO (TEA) | AC4 + AC5 |
| `apps/pages/tests/test_about_timeline.py` | NOVO (TEA) | AC6 |
| `apps/pages/tests/test_about_gallery.py` | NOVO (TEA) | AC7 |
| `apps/pages/tests/test_about_page_css.py` | NOVO (TEA) | AC8 (KOLOKOVANO uz app, NE root tests/) |

**NETAKNUTO (regression guards):** `apps/pages/views.py` `HomeView`; `templates/pages/home.html` + svi `_home_*` osim `_home_about_intro.html`; `templates/base.html`; `static/js/lightbox-init.js`; `static/js/statistic-counter.js`; `static/css/components/lightbox.css`; `static/vendor/glightbox/*`; `templates/partials/{hero_overlay_card,section_eyebrow,repeating_element,wave_divider}.html`; `static/css/tokens.css`; `config/settings/base.py`; `config/urls.py`; `apps/{brands,products,core}/*`. **`footer.html` NEMA „O nama" link** (verifikovano live — SM-D3c je no-op).

---

## 2. Python surface

### `apps/pages/views.py` — `AboutView`

```python
class AboutView(TemplateView):
    template_name = "pages/about.html"
    # get_context_data() OPCIONO — samo Python liste literala (događaji/galerija) radi DRY;
    # NE DB query, NE domain import (v1 hardcoded-translatable; SM-D1/SM-D5).
```

- CBV `TemplateView` (NE FBV). `as_view()` u urls.py.
- `HomeView` ostaje NETAKNUT (regresija).

### `apps/pages/urls.py`

```python
app_name = "pages"
urlpatterns = [
    path("", HomeView.as_view(), name="home"),       # POSTOJEĆI — netaknut
    path("o-nama/", AboutView.as_view(), name="about"),  # NOVO
]
```

---

## 3. URL surface

| Name | Pattern (kroz i18n_patterns) | View | Reverse (sr) |
|---|---|---|---|
| `pages:home` | `/<lang>/` | `HomeView` | `/sr/` (regresija — netaknut) |
| `pages:about` | `/<lang>/o-nama/` | `AboutView` | `/sr/o-nama/` |

- Slug `o-nama` ASCII, ISTI za sva 3 locale (`/sr/o-nama/`, `/hu/o-nama/`, `/en/o-nama/`) — NEMA per-locale URL slug prevod (SM-D2/OQ-1).
- GET sva 3 locale → HTTP 200; `assertTemplateUsed(response, "pages/about.html")`.

---

## 4. Template / DOM surface

### `templates/pages/about.html`
- `{% extends "base.html" %}`; `{% load i18n static %}`.
- `{% block title %}` + `{% block meta_description %}` — OBA kroz `{% translate %}` (TEA NE asertira tačan literal meta teksta — samo da `<meta name="description">` postoji + neprazan + translatable; vidi AC3 NAPOMENA).
- `{% block content %}` uključuje 4 partials TAČNIM redom:
  1. `pages/partials/_about_hero.html`
  2. `pages/partials/_about_story.html`
  3. `pages/partials/_about_timeline.html`
  4. `pages/partials/_about_gallery.html`
- `{% block scripts %}{{ block.super }}<script src="{% static 'js/timeline-reveal.js' %}" defer></script>{% endblock %}` — `{{ block.super }}` ZADRŽAVA site-wide skripte (lightbox-init.js, statistic-counter.js).
- TAČNO 1 `<h1>` (kroz hero_overlay_card). Single `<main>` iz base.html (NE dupliran).
- Svaka od 4 sekcija je `<section>` sa `aria-labelledby` (referencira lokalni h2 id) ILI `aria-label` (hero).
- Heading hijerarhija h1 → h2 → h3 (bez preskoka). NEMA ćirilice; pune dijakritike.

### `_about_hero.html`
- `<section aria-label="...">` (h1 u hero_overlay_card nema id → aria-label).
- Dekorativna foto-pozadina: `<img class="coric-about-hero__bg" alt="" aria-hidden="true" loading="eager">` referencira `{% static 'img/about/hero-o-nama.jpg' %}`. **NE CSS `background-image: url(...)`** (token-test regex tretira `.jpg` u `url()` kao class selektor → FAIL).
- `{% include "partials/hero_overlay_card.html" with title=_("O nama") brand_logo=... brand_logo_alt=_("Ćorić Agrar logo") variant="green" bullets="" %}`.
- Renderuje `coric-hero-overlay-card` + `coric-repeating-element--green` (variant=green watermark — SM-D6).

### `_about_story.html`
- `<section aria-labelledby="about-story-title">`, bela pozadina (`var(--color-neutral-white)`).
- Dekorativni watermark logo: `<img class="coric-about-story__watermark" alt="" aria-hidden="true">` (NE CSS bg-url — isti razlog kao hero).
- Section Eyebrow (`coric-section-eyebrow`) + `<h2 id="about-story-title">` + ≥2 `<p>` translatable copy.

### `_about_timeline.html`
- `<section aria-labelledby="about-timeline-title">` + Section Eyebrow + `<h2 id="about-timeline-title">`.
- `<ol class="coric-about-timeline" data-timeline>` sa ≥3 `<li ... data-timeline-segment>`.
- Svaki segment: godina (broj — NE prevodi) + `<h3>` naslov (translatable) + `<p>` opis (translatable) — sve SEMANTIČKI HTML (NE u SVG `<text>`).
- Dekorativni čvorovi + linija lente (inline `<svg>` ILI ČIST CSS `<span>`/`<div>` — SVG NIJE obavezan, CSS-only validan; mirror SM-D8 masonry): bar jedan dekorativni element `aria-hidden="true"`; AKO postoji `<svg>`, MORA biti `aria-hidden`.
- Reveal CSS klase: početno hidden gejtovano `.coric-js` markerom; `.coric-is-revealed` final.

### `_about_gallery.html`
- `<section aria-labelledby="about-galerija-title">` + Section Eyebrow + `<h2 id="about-galerija-title">`.
- `coric-about-gallery` kontejner (CSS masonry — `column-count`).
- 6-9 stavki: `<a class="glightbox" href="{% static 'img/about/gallery/foto-N.jpg' %}" data-gallery="o-nama-galerija"><img src="..." alt="<opisni translatable>" loading="lazy" class="coric-about-gallery__img"></a>`.
- SVI linkovi imaju `data-gallery="o-nama-galerija"` (GLightbox grupisanje prev/next). Svaki `<img>` OPISNI `alt` (NE prazan — informativna galerija, SM-D10).

### Story 3-1 placeholder RAZREŠENJE (AC2)
- `_home_about_intro.html`: `<a href="{% url 'pages:about' %}" class="coric-button coric-button--primary coric-home-about__cta" data-testid="home-about-cta">{% translate "Saznaj više" %}</a>` — BEZ `aria-disabled`/`tabindex="-1"`/`role="button"` placeholder atributa/TODO; `data-testid="home-about-cta"` ZADRŽAN.
- `header.html:95`: „O nama" nav `href="{% url 'pages:about' %}"`. `:71`: `{% translate "Početna" %}` (pune dijakritike).

### data-testid / data-* surface (regresijski selektori)
| Selektor | Lokacija | Svrha |
|---|---|---|
| `[data-testid="home-about-cta"]` | `_home_about_intro.html` | Home „Saznaj više" CTA (ZADRŽAN) |
| `[data-timeline]` | `_about_timeline.html` `<ol>` | timeline-reveal.js root |
| `[data-timeline-segment]` | `_about_timeline.html` `<li>` | reveal po događaju |
| `[data-gallery="o-nama-galerija"]` | `_about_gallery.html` `<a>` | GLightbox grupisanje |

---

## 5. CSS surface — `static/css/components/about-page.css`

- BEM blokovi (SVI `coric-` prefiks): `coric-about-hero`, `coric-about-story`, `coric-about-timeline`, `coric-about-gallery` (+ `__element` / `--modifier`).
- SVE boje/spacing/radius kroz `var(--token)` (tokens.css). Whitelist: `#fff`/`#ffffff`/`#000`/`#000000` + `transparent`/`none`/`0` + layout `px`/`vh`/`%`. NEMA `url()` (watermark/hero su `<img>`, NE CSS bg).
- Timeline reveal: hidden gejtovano JS-markerom — `.coric-js .coric-about-timeline__segment { opacity: 0; transform: ...; }`; `.coric-is-revealed` final + `transition: opacity 800ms ease-in-out, transform 800ms ease-in-out`; `@media (prefers-reduced-motion: reduce) { transition: none; }`.
- Responsive: hero ~60vh mobile / ~90vh desktop; galerija `column-count` 1/2/3.
- `static/css/main.css`: +1 `@import url('./components/about-page.css');` POSLE home-page.css. REUSE lightbox.css (NE dupliraj).

---

## 6. JS modul surface — `static/js/timeline-reveal.js`

MIRROR `statistic-counter.js` 1:1:
- Vanilla JS IIFE; `'use strict'`; `typeof window/document` guard; bail ako nema `[data-timeline]` root.
- Na init (PRE observe): dodaj `coric-js` marker klasu na `[data-timeline]` root (gejtuje CSS hidden — NO-JS fallback → bez JS segmenti vidljivi).
- `prefers-reduced-motion: reduce` → odmah `.coric-is-revealed` SVIM segmentima (instant).
- `IntersectionObserver` threshold 0.3 → kad root uđe u vidno polje, dodaj `.coric-is-revealed`; `unobserve` posle reveal-a.
- `IntersectionObserver` fallback (`if (!('IntersectionObserver' in window))`) → svi odmah `.coric-is-revealed`.
- NE global pollution (osim eventualnog `coric:` namespaced event-a). Stagger po segmentu je PREPORUČEN enhancement, NE GREEN zahtev (TEA NE asertira stagger).
- Učitan SAMO na about strani (about.html `{% block scripts %}`, NE base.html — SM-D7).

> **JS unit testovi van scope-a:** IntersectionObserver behavior se NE unit-testira u Django pytest-u (mirror statistic-counter.js). TEA verifikuje JS kontrakt KROZ template markup (`data-timeline` / `data-timeline-segment` prisutni) + da se modul učitava per-page; NO-JS fallback se verifikuje time da hidden state NIJE bezuslovno na segmentu (gejtovan `coric-js`).

---

## 7. Locale .po surface (AC9)

- Novi msgid (sr/hu/en): page title, hero title („O nama"), Section Eyebrow tekstovi („NAŠA PRIČA"/„VREMENSKA LENTA"/„GALERIJA"), h2 naslovi, 2-3 „Naša priča" paragrafa, 3 događaja lente (naslov+opis; godina je broj — NE prevodi), galerija alt tekstovi, „Ćorić Agrar logo".
- USPUTNO: header `:71` „Početna" (zamenjuje šišanu „Pocetna").
- `meta_description` ide kroz `{% translate %}` (literal nije obavezujući — biznis/8.8 copy).
- sr: pune dijakritike (č/ć/ž/š/đ); NEMA ćirilice; NEMA šišane latinice. 0 empty msgstr za nove msgid.

---

## 8. AC → test traceability

| AC | Test fajl | Testovi |
|---|---|---|
| AC1 | `test_about_url.py` | resolves sr/hu/en (200), template used, reverse, home regresija |
| AC2 | `test_about_home_cta_wired.py` | home CTA href, no aria-disabled, header „O nama" wire, CTA tabbable |
| AC3+AC9 | `test_about_template_structure.py` | 1 h1, 1 main, 4 sekcije redom, aria landmark, no ćirilica, heading hijerarhija, meta description, scripts block.super |
| AC4+AC5 | `test_about_hero_story.py` | hero overlay green, hero bg dekorativna, watermark aria-hidden, story ≥2 paragrafa |
| AC6 | `test_about_timeline.py` | ≥3 segmenta, godina+h3+opis, dekorativni SVG/CSS čvor aria-hidden (SVG NIJE obavezan — CSS-only validan), tekst NIJE u SVG text, timeline-reveal.js učitan per-page |
| AC6 (NO-JS fallback) | `test_about_page_css.py` | hidden stanje (opacity:0) timeline segmenta gejtovano `.coric-js` markerom (NE bezuslovno — bez JS segmenti vidljivi) |
| AC7 | `test_about_gallery.py` | ≥6 glightbox linkova, deljen data-gallery, opisni alt, lazy |
| AC8 | `test_about_page_css.py` | @import u main.css, samo var(--token), coric- prefiks na svim klasama, NO-JS fallback gejtovanje (4 testa) |

> **AC10 (Lighthouse a11y ≥95 / Performance ≥80 / responsive / keyboard / reduced-motion smoke)** je MANUELNI Dev gate (Task 8) — NE automatizuje se u pytest-u. Automatizovani a11y proxy-ji (single h1/main, aria landmarks, aria-hidden na dekorativnim, opisni alt, tab-able CTA) su pokriveni gore.

---

## 9. RED-phase očekivanje

Pre Dev GREEN: `AboutView`/`pages:about` NE postoje, `about.html` NE postoji, placeholder NIJE
razrešen, `about-page.css` NE postoji. Svi testovi MORAJU pasti — NoReverseMatch (reverse) /
404→200 mismatch / TemplateDoesNotExist / `pages/about.html` ne u renderu / fajl ne postoji /
assertion (placeholder još `aria-disabled`). Bilo koji PASS u RED fazi znači preslab test.
