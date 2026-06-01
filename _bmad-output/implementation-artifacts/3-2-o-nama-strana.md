---
story_id: "3.2"
story-key: 3-2-o-nama-strana
title: O nama Strana
status: ready-for-dev
epic: 3
epic_num: 3
epic_title: Home & Static Pages
module: pages
created: 2026-06-01
last_modified: 2026-06-01
complexity: M
author: Mihas (SM autonomous; DRUGA story Epic 3. „O nama" je STATIČKA read-only strana na `/o-nama/` (sr) — `AboutView(TemplateView)` u POSTOJEĆEM `apps/pages/` (mirror Story 3-1 HomeView pattern). Renderuje 4 sekcije iz EXPERIENCE.md + epics.md AC: (1) full-screen hero sa slikom/sloganom preko (REUSE hero_overlay_card variant="green"); (2) duži tekst o kompaniji na BELOJ pozadini sa transparentnim uvećanim logom kao DEKORATIVNIM watermark-om; (3) interaktivna SVG vremenska lenta sa min 3 događaja (godina+naslov+opis), reveal animirana pri scroll-into-view kroz IntersectionObserver (800ms ease-in-out po segmentu, instant ako prefers-reduced-motion); (4) masonry galerija fotografija (različite visine, zbijene), klik otvara GLightbox sa navigacijom (REUSE postojeći GLightbox vendor + lightbox-init.js — `.glightbox` selektor, NULA novog lightbox JS). Sadržaj je hardcoded-translatable Lorem Ipsum dok CMS (Page model) ne stigne Epic 8 Story 8.8. NOVI JS: SAMO `timeline-reveal.js` (IntersectionObserver, IIFE, reduced-motion guard — architecture.md:670 eksplicitno mapira). NEMA HTMX, NEMA forma, NEMA migracija, NEMA modela (apps/pages BEZ modela do Story 3-4). REŠAVA Story 3-1 odloženi placeholder: `pages:about` URL postaje stvaran → `_home_about_intro.html` „Saznaj više" CTA + header.html „O nama" nav link se WIRE-uju na `pages:about`.)
depends_on:
  - 1-6-base-templates-sa-bootstrap-5-htmx-setup        # base.html block content/title/meta_description/extra_head/scripts; GLightbox vendor + lightbox-init.js + glightbox.min.css već učitani site-wide
  - 1-7-reusable-visual-komponente                       # hero_overlay_card, section_eyebrow, repeating_element partials + coric-button BEM
  - 1-8-sticky-nav-top-header-footer-language-switcher-partial  # header.html „O nama" nav link (:95 href="#" → WIRE na pages:about); footer landmark
  - 2-5-product-galerija-lightbox                         # GLightbox 3.x vendor + lightbox-init.js (`.glightbox` selektor, prefers-reduced-motion, htmx:afterSwap re-init) + lightbox.css (backdrop rgba(15,15,15,0.85)) — REUSE 1:1 za masonry galeriju
  - 3-1-home-strana-sa-svim-sekcijama                     # apps/pages/ app scaffold (PagesConfig + INSTALLED_APPS + urls.py app_name="pages"); pages:home; HomeView TemplateView pattern (mirror za AboutView); _home_about_intro.html „Saznaj više" placeholder CTA (SM-D11/SM-D14) koji OVA story razrešava
---

# Story 3.2: O nama Strana

Status: ready-for-dev

## Opis

As a **posetilac (Marko — poljoprivrednik koji pre kontakta želi da proceni da li je Ćorić Agrar ozbiljan, dugovečan partner; Đorđe — Mihasov klijent koji testira tastaturom + NVDA na 375px mobilnom; SEO bot koji indeksira „O nama" stranu)**,

I want **da otvorim `/sr/o-nama/` i pročitam priču kompanije kroz 4 sekcije: (1) full-screen hero sa fotografijom/sloganom preko; (2) duži tekst o kompaniji na beloj pozadini sa transparentnim uvećanim logom kao dekorativnim elementom u pozadini; (3) interaktivnu SVG vremensku lentu sa najmanje 3 događaja (godina + naslov + opis) koja se animira pri ulasku u vidno polje (800ms ease-in-out po segmentu, ili instant ako imam uključen `prefers-reduced-motion: reduce`); (4) masonry galeriju fotografija različitih visina koja se klikom otvara u lightbox-u sa navigacijom (prev/next, Esc, swipe)**,

so that **gradim poverenje pre nego što kontaktiram firmu, strana je potpuno responzivna (mobile stack → desktop), zadovoljava single-h1 pravilo, koristi semantic HTML5 + ARIA landmarks, sve dekorativne SVG elemente (vremenska lenta, watermark logo, wave) označava `aria-hidden="true"`, prolazi Lighthouse a11y ≥ 95 (UX-DR-13 + NFR-2), i REUSE-uje SVE postojeće vizuelne komponente (hero_overlay_card, section_eyebrow, GLightbox/lightbox-init.js) uz SAMO JEDAN novi JS modul (`timeline-reveal.js`) i minimalan novi CSS**.

Ovo je **druga story Epic 3 (Home & Static Pages)** i prva čisto statička strana sajta. „O nama" NE definiše nove modele, NE menja postojeće, NE uvodi forme ni HTMX. Sadržaj (tekst, događaji vremenske lente, slike galerije) je **hardcoded-translatable Lorem Ipsum** dok CMS (`Page` model + admin) ne stigne Epic 8 Story 8.8 (epics.md:1156-1163 + AC „Sadržaj se uređuje kroz admin — pravi Epic 8 8.8, za sada Lorem Ipsum"). Strana je „izlog priče" — gradi poverenje, ima JEDAN izlazni link (logo/nav vode na home, hero može imati CTA ka kontaktu — opciono).

**SM ODLUKA — `AboutView` ŽIVI u POSTOJEĆEM `apps/pages/` (mirror Story 3-1 HomeView) — SM-D1:** „O nama" je statička strana koju architecture.md EKSPLICITNO mapira u `apps/pages/` (architecture.md:587-593 dir struktura `pages/ … views.py # HomeView, AboutView, ContactView`; :894 „FR-1..FR-5 (Početna + statičke strane) | `apps/pages/`"; FR-4 „Stranica O nama"). `apps/pages/` app VEĆ postoji (Story 3-1 ga je kreirao — `PagesConfig`, `INSTALLED_APPS`, `apps/pages/urls.py` `app_name="pages"`). **Lock:** „O nama" se implementira kao `class AboutView(TemplateView)` u POSTOJEĆEM `apps/pages/views.py` (DODAJE se klasa, NE menja `HomeView`); `template_name = "pages/about.html"`. CBV `TemplateView` (NE FBV) — mirror Story 3-1 SM-D1 obrazloženje (idiomatičan Django izbor za read-only render stranu sa hardcoded kontekstom; project-context.md § Django views dozvoljava CBV za standardne render strane). U v1 `AboutView.get_context_data()` NE agregira domain modele — sadržaj je hardcoded-translatable u template-u (Lorem Ipsum do Story 8.8 CMS), pa view NE importuje `Brand`/`Product` (za razliku od HomeView; ako Step-02 odluči da se događaji lente/galerija stave u context-listu radi DRY iteracije, to je čista Python lista literala u view-u — NE DB query). Vidi SM-D1 + SM-D5.

**SM ODLUKA — URL `/o-nama/` + ime `pages:about` — SM-D2:** URL je `/<lang>/o-nama/` kroz `i18n_patterns()` (project-context.md:161 „URL paths: kebab-case ili srpske reči → `/o-nama/`"; EXPERIENCE.md:82 sitemap `/o-nama`; epics.md AC „posetim `/sr/o-nama/`"). URL ime je `pages:about` (namespace `pages` iz `apps/pages/urls.py` `app_name="pages"`; mirror `pages:home`). **Lock:** dodaj `path("o-nama/", AboutView.as_view(), name="about")` u POSTOJEĆI `apps/pages/urls.py` `urlpatterns` (POSLE `path("", HomeView.as_view(), name="home")`). hu/en lokali: `i18n_patterns()` dodaje `/hu/o-nama/` + `/en/o-nama/` — URL PATH SEGMENT (`o-nama`) ostaje ISTI za sve lokale u v1 (NEMA per-locale slug prevod URL-a; `django.utils.translation.gettext_lazy` na URL pattern-u NIJE u scope-u — mirror Story 2-x landing strane koje koriste fiksne slug segmente). Vidi SM-D2 + OQ-1.

**SM ODLUKA — RAZREŠENJE Story 3-1 odloženog placeholder-a (`pages:about` → stvaran) — SM-D3 (KRITIČNA, blokira ovu story DoD):** Story 3-1 je ostavio DVA placeholder-a koja čekaju OVU story:
1. `templates/pages/partials/_home_about_intro.html:13-20` — „Saznaj više" CTA je trenutno KANONSKI PLACEHOLDER-CTA (Story 3-1 SM-D14): `<a href="#" role="button" aria-disabled="true" tabindex="-1" data-testid="home-about-cta">` + TODO komentar `{# TODO Story 3-2: zameni href="#"+aria-disabled sa {% url 'pages:about' %} (ukloni aria-disabled/tabindex) #}`.
2. `templates/partials/header.html:95` — „O nama" nav link je `<a class="nav-link coric-nav__link" href="#">{% translate "O nama" %}</a>` (mrtav placeholder iz Story 1-8).

**Lock (SM-D3):** kada `pages:about` postane stvaran (ova story), Dev MORA:
- (a) U `_home_about_intro.html`: zameniti `href="#"` → `href="{% url 'pages:about' %}"`; UKLONITI `aria-disabled="true"` + `tabindex="-1"` + TODO komentar; ostaviti `data-testid="home-about-cta"` (regresijski selektor); CTA postaje funkcionalan tab-abilan link.
- (b) U `header.html:95`: zameniti `href="#"` → `href="{% url 'pages:about' %}"`. NAV nema aktivno-stranica pattern (verifikovano live — ni „Početna" `:71` ni ostali linkovi nemaju `aria-current`/active markup), pa SAMO wire-uj URL; `aria-current="page"` je OPCIONO/van scope-a. USPUTNO: `:71` „Početna" link je trenutno `{% translate "Pocetna" %}` (šišana latinica) → promeni u `{% translate "Početna" %}` (pune dijakritike — project-context.md).
- (c) Footer.html — AKO footer ima „O nama" link (verifikuj live), isto wire-uj. (Story 3-1 File List ne navodi footer „O nama" link — verifikuj `Select-String "O nama" templates/partials/footer.html`; ako postoji `href="#"`, wire-uj.)

Ovo razrešenje je DEO DoD ove story — bez njega Story 3-1 placeholder ostaje mrtav. Vidi SM-D3.

**REUSE fokus (1 novi JS modul — `timeline-reveal.js`; 1 nova CSS komponenta — `about-page.css`; 0 novih lightbox/galerija JS — REUSE Story 2-5):**

- **`AboutView(TemplateView)`** (`apps/pages/views.py`, DODAJE se klasa u POSTOJEĆI fajl) — `template_name = "pages/about.html"`; `get_context_data()` (opciono — ako se događaji lente / slike galerije drže kao Python liste literala radi DRY; NE DB query u v1). Mirror `HomeView` struktura.
- **`templates/partials/hero_overlay_card.html`** (Story 1-7) — REUSE za „O nama" hero; prima `title` (slogan/naslov strane), `brand_logo`, `brand_logo_alt`, `variant="green"` (SM-D6), `bullets=""`. Renderuje h1.
- **`templates/partials/section_eyebrow.html`** (Story 1-7) — UPPERCASE eyebrow iznad svake sekcije (npr. „O NAMA", „NAŠA PRIČA", „GALERIJA").
- **`templates/partials/repeating_element.html`** (Story 1-7) — INDIREKTNO kroz hero_overlay_card watermark. `variant="green"` (SM-D6 — CSS ima SAMO `--green` + `--jeegee`; NE izmišljati nove variant-e).
- **GLightbox 3.x vendor + `static/js/lightbox-init.js`** (Story 2-5) — REUSE 1:1 za masonry galeriju. `lightbox-init.js` je VEĆ učitan site-wide u `base.html:39-40` i inicijalizuje SVE `.glightbox` selektore na `DOMContentLoaded`. Galerija samo treba `<a class="glightbox" href="<full-img>" data-gallery="o-nama-galerija">` markup → lightbox „samo radi" BEZ novog JS. `lightbox.css` (backdrop rgba(15,15,15,0.85) + reduced-motion) takođe REUSE.
- **`coric-button` + `coric-button--primary`** (Story 1-7 `pill-button.css`) — REUSE za eventualni hero CTA (opciono — ka kontaktu).
- **`{% responsive_picture %}`** (Story 2-3, `media_tags`) — za hero foto-pozadinu (hero je `<img>`, NE responsive_picture wrapper — vidi AC4 token-test razlog; ostaje plain `<img loading="eager">`). Galerijski thumb-ovi: srcset WAIVED u v1 (plain `<img loading="lazy">` — SM-D8/AC7; GLightbox href na punu rezoluciju).
- **CSS tokens** (`static/css/tokens.css`, Story 1-5): `--color-brand-green-900/800/600/400`, `--color-accent-gold-500`, `--color-neutral-white/cream/gray-700/gray-500`, `--color-semantic-focus-ring`, `--spacing-scale-*`, `--rounded-md/sm/pill`, `--shadow-md`, `--typography-scale-h1/h2/h3/body/caption`.
- **`base.html`** (Story 1-6) — `{% extends "base.html" %}`; `{% block title %}`, `{% block meta_description %}`, `{% block content %}`, `{% block scripts %}` (za `timeline-reveal.js`). header + footer + single `<main id="main-content">` + aria-live VEĆ prisutni (NE dupliraj).

**Hero content + tekst + lenta + galerija — HARDCODED-TRANSLATABLE LOREM IPSUM (SM-D5 — KRITIČNA odluka, mirror Story 3-1 SM-D10):** CMS (`Page` model: hero_image, hero_video, sections JSON, gallery_images M2M; `AboutTimelineEvent`; `GalleryImage`) je Epic 8 Story 8.8 (epics.md:1156-1163; sprint-status backlog) + Story 3-4 SiteSettings. **Lock (SM-D5):** sav sadržaj „O nama" strane je u v1 hardcoded-translatable (kroz `{% translate %}` / `{% blocktranslate %}`):
- **Hero foto-pozadina:** static asset `static/img/about/hero-o-nama.jpg` (Dev dodaje optimizovanu placeholder/stock sliku ≤300KB ~1920px; OQ-2 PRODUCTION BLOCKER — realna slika pre produkcije). EXPERIENCE.md pominje „video ili slika" — v1 koristi SLIKU (video je CMS/Story 8.8 scope; NE embed video u v1).
- **Tekst o kompaniji:** 2-3 paragrafa Lorem Ipsum-ish translatable copy.
- **Vremenska lenta:** TAČNO 3 hardcoded događaja (godina + naslov + opis), translatable. Min 3 po epics.md AC. Reprezentativne godine (npr. 2008/2015/2024 — Dev/biznis usaglašava stvarne; placeholder OK za v1).
- **Galerija:** 6-9 placeholder slika iz `static/img/about/gallery/` (Dev dodaje placeholder slike različitih dimenzija za masonry efekat; OQ-2). Ako stock slike nedostupne, Dev koristi solid-color placeholder + TODO marker.

Kada Story 8.8 (CMS) stigne, sadržaj prelazi na `Page`/`AboutTimelineEvent`/`GalleryImage` modele (NE blokira ovu story; forward-compat — view može kasnije popuniti context iz baze, template grana ostaje ista). Vidi SM-D5.

**Vremenska lenta — SVG + IntersectionObserver reveal — `timeline-reveal.js` (SM-D7 — JEDINI novi JS):** epics.md AC zahteva „interaktivna SVG vremenska lenta … animirana pri scroll-into-view kroz `IntersectionObserver` (800ms ease-in-out po segmentu, instant ako `prefers-reduced-motion: reduce`)". DESIGN.md:267 + architecture.md:203 + :670 (`timeline-reveal.js # SVG timeline animation`) sve potvrđuju. **Lock (SM-D7):**
- Lenta je **inline SVG/CSS** struktura (NE raster, NE external lib — architecture.md:203 „SVG inline + CSS + IntersectionObserver za reveal … minimal weight").
- Reveal animacija je CSS (`opacity` + `transform` transition 800ms ease-in-out po segmentu/događaju), TRIGGER kroz NOVI `static/js/timeline-reveal.js` (vanilla JS IIFE, `coric:` namespace, `prefers-reduced-motion: reduce` guard, `IntersectionObserver` fallback — MIRROR `statistic-counter.js` pattern 1:1: `data-*` atributi, threshold 0.3, `unobserve` posle reveal-a).
- `prefers-reduced-motion: reduce` → segmenti se prikazuju INSTANT (final state, bez transition — mirror `statistic-counter.js:29-32` instant set + `lightbox.css:27` reduced-motion guard).
- Dekorativni SVG elementi lente (linije, krugovi-čvorovi BEZ teksta) imaju `aria-hidden="true"` (epics.md AC „Vremenska lenta i galerija imaju `aria-hidden=\"true\"` na dekorativnim SVG elementima"); TEKSTUALNI sadržaj (godina/naslov/opis) je SEMANTIČKI HTML (NE u SVG `<text>` — čitljiv AT-u), strukturiran kao `<ol>`/`<li>` ili `<article>` po događaju.
- `timeline-reveal.js` se učitava SAMO na about strani kroz `{% block scripts %}` u `about.html` (NE site-wide u base.html — strana-specifičan modul; mirror tractor-filters.js per-page loading). Vidi SM-D7.

**Masonry galerija + GLightbox — NULA novog JS (SM-D8 — REUSE Story 2-5):** epics.md AC zahteva „masonry galerija fotografija (različite visine, zbijene), klik otvara GLightbox sa navigacijom". **Lock (SM-D8):**
- GLightbox vendor + `lightbox-init.js` su VEĆ učitani site-wide (`base.html:39-40`). `lightbox-init.js` inicijalizuje SVE `.glightbox` linkove na `DOMContentLoaded` + respektuje `prefers-reduced-motion` + emit-uje `coric:lightbox-open/close`. Galerija samo treba ispravan markup → lightbox radi BEZ ijedne linije novog JS.
- Markup po slici: `<a class="glightbox" href="{% static 'img/about/gallery/foto-N.jpg' %}" data-gallery="o-nama-galerija" data-glightbox="title: ..."><img src="<thumb>" alt="<opisni alt>" loading="lazy"></a>`. `data-gallery` grupiše slike za prev/next navigaciju (GLightbox grupisanje). `alt` je OPISNI (NE prazan — galerija je INFORMATIVNA, ne dekorativna; ali sam lightbox-link wrapper nije dekorativan).
- **Masonry layout je ČIST CSS** (NE Masonry.js, NE external lib — DESIGN.md/architecture.md NE pominju masonry biblioteku). Lock: CSS `columns` (`column-count` responsive 1/2/3 + `break-inside: avoid` na karticama) ILI CSS Grid `grid-auto-rows` masonry approxiamcija. Dev bira CSS-only pristup; NULA novog JS za layout.
- Galerija kao celina je `<section aria-labelledby="about-galerija-title">`; svaki lightbox-link ima accessible naziv (alt na img ili aria-label na `<a>`). Vidi SM-D8.

**Princip:** Pure server-side rendering, **NEMA HTMX**, **NEMA forma**, **NEMA admin promena**, **NEMA migracije**, **NEMA modela** (`apps/pages` ostaje bez modela do Story 3-4; čista statička strana). JEDAN novi JS modul (`timeline-reveal.js`, per architecture.md:670 plan). JEDNA nova CSS komponenta (`about-page.css`). REUSE GLightbox/lightbox-init.js (Story 2-5) za galeriju — NULA novog lightbox JS. CSS BEM sa `coric-` prefiksom + isključivo `var(--token)`. Sve user-facing string-ove kroz `{% translate %}` / `{% blocktranslate %}`. Slug ASCII (`o-nama`); pune dijakritike (č/ć/ž/š/đ) u svemu renderovanom.

**Strukturna arhitektura — repository delta:** **6 NEW fizičkih fajlova (+ 2 asset grupe) + 6 EDIT + 0 DELETE + 0 migracija.**

| Path | Tip | Razlog |
|---|---|---|
| `apps/pages/views.py` | EDIT | DODAJ `class AboutView(TemplateView)` (`template_name = "pages/about.html"`; opcioni `get_context_data()` sa hardcoded Python listama događaja/slika ILI prazan — SM-D1/SM-D5). NE menjaj `HomeView`. NE dodavati domain import za AboutView (v1 hardcoded sadržaj). |
| `apps/pages/urls.py` | EDIT | DODAJ `path("o-nama/", AboutView.as_view(), name="about")` u POSTOJEĆI `urlpatterns` (POSLE `path("", HomeView.as_view(), name="home")`); import `AboutView`. → `pages:about`. |
| `templates/pages/about.html` | NOVO | Glavni template — `{% extends "base.html" %}`; `{% block title %}`, `{% block meta_description %}`, `{% block content %}` koji uključuje 4 sekcije REDOM (SM-D4): hero → tekst-o-kompaniji → vremenska-lenta → galerija; `{% block scripts %}{{ block.super }}<script src="{% static 'js/timeline-reveal.js' %}" defer></script>{% endblock %}`. JEDAN `<h1>` (kroz hero_overlay_card). single `<main>` iz base.html. Svaka sekcija `<section>` sa aria landmark. |
| `templates/pages/partials/_about_hero.html` | NOVO | Hero — full-screen foto-pozadina (static `img/about/hero-o-nama.jpg` kroz `{% static %}`, SM-D5) + `coric-about-hero__overlay` koji include-uje `partials/hero_overlay_card.html` sa `title=_("O nama")` (ILI slogan — SM-D9), `brand_logo` (Ćorić Agrar static logo), `variant="green"` (SM-D6), `bullets=""`. h1 iz hero_overlay_card. `aria-label` na `<section>` (h1 u partial-u nema id). |
| `templates/pages/partials/_about_story.html` | NOVO | „Naša priča" tekst blok — BELA pozadina + transparentni uvećani logo kao DEKORATIVNI watermark (`aria-hidden="true"`, EXPERIENCE.md/epics.md AC „transparentnim uvećanim logom kao dekorativnim elementom"); Section Eyebrow + h2 + 2-3 paragrafa translatable Lorem Ipsum (SM-D5). |
| `templates/pages/partials/_about_timeline.html` | NOVO | Vremenska lenta — Section Eyebrow + h2 + inline SVG/CSS lenta sa 3 događaja (SM-D7). Svaki događaj: SEMANTIČKI `<li>`/`<article>` (godina+naslov+opis translatable) + dekorativni SVG čvor/linija (`aria-hidden="true"`). `data-timeline` root + `data-timeline-segment` po događaju (za `timeline-reveal.js`). Reveal CSS klase (početno `opacity:0` + transform; `.is-revealed` final). |
| `templates/pages/partials/_about_gallery.html` | NOVO | Masonry galerija — Section Eyebrow + h2 + `coric-about-gallery` (CSS masonry) sa 6-9 `<a class="glightbox" data-gallery="o-nama-galerija">` linkova (SM-D8, REUSE GLightbox). Svaki `<img>` opisni `alt` + `loading="lazy"`. NULA novog JS (lightbox-init.js već učitan). |
| `static/js/timeline-reveal.js` | NOVO | Vanilla JS IIFE — IntersectionObserver reveal vremenske lente (SM-D7). MIRROR `statistic-counter.js`: `data-timeline` root, threshold 0.3, `unobserve` posle reveal-a, `prefers-reduced-motion: reduce` → instant `.is-revealed`, `IntersectionObserver` fallback (sve odmah revealed). `coric:` namespace ako emit-uje event. NE global pollution. architecture.md:670. |
| `static/css/components/about-page.css` | NOVO | `coric-about-hero`, `coric-about-story` (+ watermark logo), `coric-about-timeline` (+ segment reveal transition 800ms ease-in-out + `prefers-reduced-motion` guard), `coric-about-gallery` (CSS masonry — column-count responsive) BEM. Sve `var(--token)`. JEDINA nova CSS komponenta. REUSE lightbox.css (NEMA dupliranja). |
| `static/css/main.css` | EDIT | DODAJ TAČNO 1 `@import url('./components/about-page.css');` POSLE poslednje `@import` linije (`home-page.css`, Story 3-1). |
| `templates/pages/partials/_home_about_intro.html` | EDIT | SM-D3: zameni placeholder „Saznaj više" CTA — `href="#"` → `href="{% url 'pages:about' %}"`; UKLONI `aria-disabled="true"` + `tabindex="-1"` + TODO komentar (linije 11-12,16-17); ostavi `data-testid="home-about-cta"`. CTA postaje funkcionalan tab-abilan link. |
| `templates/partials/header.html` | EDIT | SM-D3: `:95` „O nama" nav link — `href="#"` → `href="{% url 'pages:about' %}"` (NAV bez aktivno-stranica pattern-a — `aria-current` OPCIONO/van scope-a). USPUTNO: `:71` `{% translate "Pocetna" %}` → `{% translate "Početna" %}` (šišana latinica fix). |
| `locale/sr/LC_MESSAGES/django.po`, `locale/hu/LC_MESSAGES/django.po`, `locale/en/LC_MESSAGES/django.po` | EDIT (×3) | Popuni msgstr za nove msgid (page title + meta description, hero slogan/naslov, eyebrow tekstovi, h2 naslovi, „Naša priča" paragrafi, 3 događaja lente godina/naslov/opis, galerija slika alt tekstovi/title, eventualni hero CTA). Pune dijakritike. |
| `static/img/about/hero-o-nama.jpg` | NOVO (asset) | Hero foto-pozadina placeholder/stock (OQ-2; ≤300KB ~1920px). Ako nedostupna → solid green-800 fallback + TODO. |
| `static/img/about/gallery/*.jpg` | NOVO (asset grupa) | 6-9 placeholder galerijskih slika različitih dimenzija za masonry (OQ-2). Ako nedostupne → solid-color placeholder + TODO. |
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | EDIT | Postavi `3-2-o-nama-strana` → `ready-for-dev`. SM handoff tracking (NIJE deliverable). |

**Brojanje (KANONSKO — single source of truth):** **6 NEW fizičkih fajlova (kod/template/js/css) + 2 asset grupe + 6 logičkih EDIT lokacija + 0 migracija + 0 modela.**

Razlaganje:
- **6 NEW:** `pages/about.html` + 4 partials (`_about_hero`, `_about_story`, `_about_timeline`, `_about_gallery`) + `timeline-reveal.js` + `about-page.css` = wait, to je 7 — preciznije: `about.html` (1) + 4 partials (5) + `timeline-reveal.js` (6) + `about-page.css` (7) = **7 NEW kod/template/asset-koda fajlova.** (Ispravka brojanja: 7 NEW, NE 6.)
- **Asset grupe (2):** `static/img/about/hero-o-nama.jpg` + `static/img/about/gallery/*.jpg` (6-9 slika) — Dev dodaje, brojeno odvojeno od koda.
- **6 logičkih EDIT:** `apps/pages/views.py` (+AboutView) + `apps/pages/urls.py` (+about path) + `static/css/main.css` (+1 @import) + `_home_about_intro.html` (SM-D3 wire) + `header.html` (SM-D3 wire) + `locale ×3` (1 logička „locale" stavka) = 6 logičkih (8 fizičkih: 5 kod/template + 3 .po).
- **0 migracija** (`apps/pages` bez modela; čista statička strana).
- **0 DELETE.**

(NAPOMENA: gornja tabela navodi 7 NEW kod/template/js/css fajlova — `about.html`, 4 partials, `timeline-reveal.js`, `about-page.css`. IMP-1 lock: Dev kreira svih 7 NEW + asset grupe.)

Postojeći fajlovi koji ostaju **NETAKNUTI** (regression guards): `apps/pages/views.py` `HomeView` (NE menja se — DODAJE se AboutView pored), `templates/pages/home.html` + ostali `_home_*` partials (osim `_home_about_intro.html` koji se EDIT-uje), `templates/base.html` (REUSE — GLightbox vendor + lightbox-init.js već učitani; NE dupliraj main/header/footer/aria-live; NE dodavati timeline-reveal.js u base.html — per-page kroz about.html scripts blok), `static/js/lightbox-init.js` (REUSE 1:1 — galerija koristi `.glightbox` selektor; NE edit), `static/js/statistic-counter.js` (REFERENCA za timeline-reveal.js pattern — NE edit), `static/css/components/lightbox.css` (REUSE — backdrop + reduced-motion; NE edit), `static/vendor/glightbox/*` (REUSE; NEMA novih vendor-a), `templates/partials/{hero_overlay_card,section_eyebrow,repeating_element,wave_divider}.html` (Story 1-7 — REUSE 1:1 bez izmena), `static/css/tokens.css`, sve `apps/brands/` + `apps/products/` + `apps/core/` (NETAKNUTI — about strana ne dira domain), `pyproject.toml`, `config/settings/base.py` (`apps.pages` već u INSTALLED_APPS iz Story 3-1; NEMA promene), `config/urls.py` (`apps.pages.urls` već include-ovan iz Story 3-1; NEMA promene — novi about path je UNUTAR `apps/pages/urls.py`).

## Kriterijumi prihvatanja

**AC1 — `AboutView` u `apps/pages/`; URL `/<lang>/o-nama/` rezolvuje `pages:about`; HTTP 200 za sva 3 locale; renderuje `templates/pages/about.html`**

- **Given** `apps/pages/` app postoji (Story 3-1 — `PagesConfig` + `INSTALLED_APPS` + `apps/pages/urls.py` `app_name="pages"` + `path("", HomeView.as_view(), name="home")`); `i18n_patterns()` aktivan (Story 1-4); `config/urls.py` već include-uje `apps.pages.urls`
- **When** dodam `class AboutView(TemplateView)` (`template_name = "pages/about.html"`) u `apps/pages/views.py` i `path("o-nama/", AboutView.as_view(), name="about")` u `apps/pages/urls.py`
- **Then**:
  - `reverse("pages:about")` → `/sr/o-nama/` (analogno `/hu/o-nama/`, `/en/o-nama/`)
  - GET `/sr/o-nama/` → HTTP 200; GET `/hu/o-nama/` → 200; GET `/en/o-nama/` → 200
  - Renderovani template je `pages/about.html` — `assertTemplateUsed(response, "pages/about.html")`
  - `AboutView` je CBV (`AboutView.as_view()` u urls.py)
  - `HomeView` + `pages:home` NETAKNUTI (regresija — GET `/sr/` i dalje 200, koristi `pages/home.html`)
  - `uv run python manage.py check` exit 0
- **And** smoke verifikacija:
  ```bash
  uv run python manage.py shell -c "from django.urls import reverse; \
    from django.utils.translation import activate; activate('sr'); \
    print(reverse('pages:about'))"
  ```
  Očekivan output: `/sr/o-nama/`

**AC2 — Story 3-1 placeholder RAZREŠEN: `_home_about_intro.html` „Saznaj više" CTA + `header.html` „O nama" nav link WIRE-ovani na `pages:about` (SM-D3)**

- **Given** AC1 (`pages:about` postoji); Story 3-1 `_home_about_intro.html:13-20` placeholder CTA (`href="#"` + `aria-disabled="true"` + `tabindex="-1"`); `header.html:95` „O nama" nav link `href="#"`
- **When** wire-ujem oba na `pages:about`
- **Then**:
  - `_home_about_intro.html`: „Saznaj više" CTA je `<a href="{% url 'pages:about' %}" class="coric-button coric-button--primary coric-home-about__cta" data-testid="home-about-cta">{% translate "Saznaj više" %}</a>` — BEZ `aria-disabled`, BEZ `tabindex="-1"`, BEZ `role="button"` placeholder atributa, BEZ TODO komentara; `data-testid="home-about-cta"` ZADRŽAN
  - `header.html:95`: „O nama" nav link je `href="{% url 'pages:about' %}"` (NE `href="#"`)
  - GET `/sr/` → home „Saznaj više" CTA `href` rezolvuje `/sr/o-nama/` (NE `#`); CTA je tab-abilan (NEMA `tabindex="-1"`)
  - Klik na header „O nama" → `/sr/o-nama/` (HTTP 200)
- **And** regresijski smoke — NEMA preostalog `aria-disabled` placeholder-a za about CTA:
  ```powershell
  Select-String -Pattern "aria-disabled" -Path templates/pages/partials/_home_about_intro.html
  ```
  Očekivano: 0 rezultata (placeholder uklonjen)
- **And** verifikuj footer „O nama" link (ako postoji `href="#"` u `footer.html`) takođe wire-ovan na `pages:about` (SM-D3c)

**AC3 — `templates/pages/about.html`: 4 sekcije u TAČNOM redu (hero → naša-priča → vremenska-lenta → galerija); JEDAN h1; single main (iz base.html); semantic HTML5 + ARIA landmarks**

- **Given** AC1; base.html (Story 1-6 — `{% block content %}`, `{% block scripts %}`, single `<main>`, header, footer, aria-live)
- **When** kreiram `about.html` + 4 section partials
- **Then** `about.html` MORA imati strukturu:
  ```django
  {% extends "base.html" %}
  {% load i18n static %}

  {% block title %}{% translate "O nama — Ćorić Agrar" %}{% endblock %}

  {% block meta_description %}{% translate "Priča kompanije Ćorić Agrar — porodična firma posvećena poljoprivrednoj mehanizaciji. Upoznajte naš put i tim." %}{% endblock %}

  {% block content %}
    {% include "pages/partials/_about_hero.html" %}
    {% include "pages/partials/_about_story.html" %}
    {% include "pages/partials/_about_timeline.html" %}
    {% include "pages/partials/_about_gallery.html" %}
  {% endblock %}

  {% block scripts %}{{ block.super }}
    <script src="{% static 'js/timeline-reveal.js' %}" defer></script>
  {% endblock %}
  ```
- **NAPOMENA (skeleton je REFERENCA):** tačan tekst `meta_description` (i `title`) u gornjem skeleton-u je PRIMER copy-ja — obavezujući zahtev je da string PROLAZI kroz `{% translate %}` (ne tačan literal). TEA NE piše brittle literal string-match test na tačan tekst meta opisa; testira da `<meta name="description">` postoji + da je sadržaj neprazan/translatable. Finalni copy je biznis/8.8 CMS input.
- **Then** redosled sekcija MORA biti: (1) Hero, (2) Naša priča (tekst), (3) Vremenska lenta, (4) Galerija. Footer iz base.html (NE dupliraj)
- **And** semantic HTML5:
  - TAČNO 1 `<h1>` (kroz `hero_overlay_card` partial u hero sekciji)
  - Svaka od 4 sekcija je `<section>` sa `aria-labelledby` (referencira lokalni h2 id) ILI `aria-label` (hero — h1 u hero_overlay_card nema id, mirror Story 3-1 SM-D8)
  - h2 po sekciji (Naša priča, Vremenska lenta, Galerija) → h3 za pod-elemente (događaji lente naslov)
  - Heading hijerarhija h1 → h2 → h3 (NEMA preskoka)
  - **Single `<main>`** (iz base.html — `about.html` NE dodaje drugi `<main>`)
- **And** `{% block scripts %}` koristi `{{ block.super }}` da NE pregazi site-wide skripte iz base.html (lightbox-init.js itd. ostaju)
- **And** `<html lang="{{ LANGUAGE_CODE }}">` automatski (base.html, Story 1-4)
- **And** NEMA hardcoded srpski (sve `{% translate %}`); NEMA ćirilice; pune dijakritike

**AC4 — Hero sekcija: full-screen foto-pozadina + `green-800` overlay card sa naslovom/sloganom + brand lockup + Repeating Element watermark (REUSE hero_overlay_card, variant="green")**

- **Given** AC3; `hero_overlay_card.html` (Story 1-7 — title/brand_logo/brand_logo_alt/variant/bullets); SM-D5 (hero copy hardcoded-translatable, foto-pozadina static asset); SM-D9 (naslov vs slogan)
- **When** kreiram `templates/pages/partials/_about_hero.html`
- **Then** hero MORA:
  - `<section>` sa `aria-label` (NE aria-labelledby — h1 u hero_overlay_card nema id; mirror Story 3-1 SM-D8)
  - Full-screen foto-pozadina `static/img/about/hero-o-nama.jpg` — renderovana kao `<img class="coric-about-hero__bg" alt="" aria-hidden="true" loading="eager">` (above-fold LCP; dekorativna; **NE CSS `background-image: url(...)`** — mirror Story 3-1 Completion Note: AC CSS token-test regex tretira `.jpg` u `url()` kao class selektor → koristi `<img>`, CSS drži samo `object-fit: cover` + green-800 fallback)
  - `{% include "partials/hero_overlay_card.html" with title=_("O nama") brand_logo=... brand_logo_alt=_("Ćorić Agrar logo") variant="green" bullets="" %}` (title: vidi SM-D9 — „O nama" naslov ILI slogan)
  - hero_overlay_card renderuje h1 + brand lockup (Ćorić Agrar static logo, mirror `_home_hero.html:12` `coric-agrar-logo-transp-light-200.png`) + Repeating Element watermark (`variant="green"` — SM-D6)
  - Hero visina responzivna: ~60vh mobile / full-screen ~90vh desktop (EXPERIENCE.md „full-screen hero"; konzistentno sa home ~60/80vh skalom — SM-D11)
- **And** `variant="green"` (NE „home"/druga vrednost — repeating-element.css ima SAMO `--green` + `--jeegee`; SM-D6 mirror Story 3-1 SM-D9 — izbegava unstyled watermark)
- **And** hero foto-pozadina dekorativna (`alt=""` + `aria-hidden="true"`)

**AC5 — „Naša priča" tekst sekcija: bela pozadina + transparentni uvećani logo kao DEKORATIVNI watermark + Section Eyebrow + h2 + 2-3 paragrafa translatable teksta**

- **Given** AC3; `section_eyebrow.html` (Story 1-7); SM-D5 (Lorem Ipsum translatable copy); epics.md AC „duži tekst o kompaniji na beloj pozadini sa transparentnim uvećanim logom kao dekorativnim elementom"
- **When** kreiram `templates/pages/partials/_about_story.html`
- **Then** sekcija MORA:
  - `<section aria-labelledby="about-story-title">` sa BELOM pozadinom (`var(--color-neutral-white)`)
  - Transparentni uvećani Ćorić Agrar logo kao DEKORATIVNI watermark u pozadini teksta — renderovan kao `<img class="coric-about-story__watermark" alt="" aria-hidden="true">` (**NE CSS `background-image: url('...logo.png')`** — mirror hero foto-pozadine odluke AC4). Razlog: AC8 CSS token-test (`apps/pages/tests/test_about_page_css.py`, mirror `apps/pages/tests/test_home_page_css.py:63-76`) skenira class selektore regexom `\.(-?[A-Za-z_][\w-]*)` koji tretira `.png`/`.jpg` unutar `url('...logo.png')` kao class selektor BEZ `coric-` prefiksa → test FAIL. `<img>` izbegava `url()` u CSS-u; `about-page.css` drži SAMO `opacity` (low) + `position`/`z-index` (iza teksta) kroz `var(--token)`. Logo je veliki, transparentan, iza teksta.
  - Section Eyebrow (`{% include "partials/section_eyebrow.html" with text=_("NAŠA PRIČA") tag="div" %}` — ILI „O NAMA"; SM-D9)
  - `<h2 id="about-story-title">` + 2-3 `<p>` paragrafa translatable copy (`{% translate %}` ili `{% blocktranslate %}` po paragrafu; Lorem Ipsum-ish do CMS Story 8.8)
- **And** tekst je čitljiv preko watermark logo-a (kontrast ≥ 4.5:1 — watermark je dovoljno transparentan / iza teksta; project-context.md a11y)
- **And** watermark logo NIJE u tab-redu, NIJE accessible nazivan (čisto dekorativan)

**AC6 — Vremenska lenta: inline SVG/CSS lenta sa min 3 događaja (godina+naslov+opis); reveal animacija pri scroll-into-view kroz `timeline-reveal.js` (IntersectionObserver, 800ms ease-in-out po segmentu, instant ako prefers-reduced-motion); dekorativni SVG elementi aria-hidden**

- **Given** AC3; `statistic-counter.js` (Story 2-6 — IntersectionObserver + reduced-motion REFERENCA pattern); SM-D7 (timeline-reveal.js JEDINI novi JS); architecture.md:203,670; DESIGN.md:267 (800ms ease-in-out)
- **When** kreiram `templates/pages/partials/_about_timeline.html` + `static/js/timeline-reveal.js`
- **Then** template MORA:
  - `<section aria-labelledby="about-timeline-title">` + Section Eyebrow + `<h2 id="about-timeline-title">`
  - Inline SVG/CSS lenta: SEMANTIČKA struktura `<ol class="coric-about-timeline" data-timeline>` sa MIN 3 `<li data-timeline-segment>` (svaki: godina + h3 naslov + `<p>` opis — translatable). Dekorativni SVG/CSS čvorovi + linija lente imaju `aria-hidden="true"` (epics.md AC)
  - TEKSTUALNI sadržaj (godina/naslov/opis) je SEMANTIČKI HTML (NE SVG `<text>` — čitljiv AT-u)
  - Reveal CSS: početno `opacity:0` + `transform` (npr. `translateY`); `.is-revealed` klasa → final state sa `transition: opacity 800ms ease-in-out, transform 800ms ease-in-out` (DESIGN.md:267)
  - **NO-JS / observer-never-fires FALLBACK (KRITIČNO — sadržaj MORA ostati vidljiv bez JS):** početno skriveno stanje (`opacity:0` + `transform`) MORA biti gejtovano JS-markerom, NE bezuslovno na segmentu. Lock: `timeline-reveal.js` na init dodaje marker klasu `coric-js` na `[data-timeline]` root; `about-page.css` skriva segmente SAMO pod tim markerom: `.coric-js .coric-about-timeline__segment { opacity: 0; transform: ...; }`. Bez JS (ili ako se modul ne učita) marker se NE dodaje → segmenti su PUNO vidljivi (graceful degradation, mirror statistic-counter koji degradira na statički broj). Ovo pokriva i „observer-never-fires" rub jer fallback grana (`if (!('IntersectionObserver' in window))`) i prefers-reduced-motion grana SVE odmah `.is-revealed`.
- **Then** `timeline-reveal.js` MORA (MIRROR `statistic-counter.js` 1:1):
  - Vanilla JS IIFE; `'use strict'`; defensive `typeof window/document` guard; bail ako nema `[data-timeline]` root
  - Na init (PRE observe/reveal) dodaj marker klasu `coric-js` na `[data-timeline]` root (gejtuje CSS hidden stanje — bez JS marker se ne dodaje → segmenti vidljivi; vidi AC6 NO-JS fallback)
  - `prefers-reduced-motion: reduce` → odmah dodaj `.is-revealed` SVIM segmentima (INSTANT, bez transition — mirror statistic-counter.js:29-32)
  - `IntersectionObserver` (threshold 0.3) → kad root uđe u vidno polje, dodaj `.is-revealed` segmentima; `observer.unobserve(root)` posle reveal-a
  - **Stagger po segmentu (epics.md „800ms ease-in-out po segmentu") je PREPORUČEN ENHANCEMENT, NE GREEN-bar zahtev:** minimum GREEN je SIMULTANI reveal svih segmenata (svi dobiju `.is-revealed` odjednom) sa 800ms transition; staggered (per-segment delay) je vizuelni plus. TEA NE piše assertion koji zahteva stagger (izbegava blokiranje GREEN-a na enhancement-u).
  - `IntersectionObserver` fallback (`if (!('IntersectionObserver' in window))`) → svi segmenti odmah `.is-revealed`
  - NE global pollution (osim eventualnog `coric:` namespaced event-a); NE legacy DOM lib
- **And** `timeline-reveal.js` učitan SAMO na about strani (`{% block scripts %}` u about.html, NE base.html — SM-D7)
- **And** `prefers-reduced-motion: reduce` CSS guard u `about-page.css` (`transition: none` na `.coric-about-timeline__segment` — defensive, mirror lightbox.css:27)
- **And** lenta ima MIN 3 događaja (epics.md AC „min 3 događaja")

**AC7 — Masonry galerija: CSS masonry layout (različite visine, zbijene) + klik otvara GLightbox sa navigacijom (REUSE Story 2-5 — NULA novog JS); thumbnail-i lazy; svaki link accessible nazivan**

- **Given** AC3; GLightbox vendor + `lightbox-init.js` (Story 2-5 — već učitani site-wide `base.html:39-40`; `.glightbox` selektor; prefers-reduced-motion; data-gallery grupisanje); `lightbox.css` (backdrop); SM-D8 (NULA novog JS)
- **When** kreiram `templates/pages/partials/_about_gallery.html`
- **Then** galerija MORA:
  - `<section aria-labelledby="about-galerija-title">` + Section Eyebrow + `<h2 id="about-galerija-title">`
  - `coric-about-gallery` kontejner sa CSS masonry (`column-count` responsive: 1 mobile / 2 tablet / 3 desktop + `break-inside: avoid` na stavkama — SM-D8 CSS-only, NEMA Masonry.js)
  - 6-9 stavki, svaka: `<a class="glightbox" href="{% static 'img/about/gallery/foto-N.jpg' %}" data-gallery="o-nama-galerija"><img src="..." alt="<opisni alt>" loading="lazy" class="coric-about-gallery__img"></a>`
  - `data-gallery="o-nama-galerija"` na SVIM linkovima (grupiše za GLightbox prev/next navigaciju)
  - Svaki `<img>` ima OPISNI `alt` (galerija INFORMATIVNA — NE prazan alt; translatable)
- **And** klik na sliku otvara GLightbox (lightbox-init.js već inicijalizuje `.glightbox` na DOMContentLoaded — NULA novog JS; verifikuj galerija slike imaju `.glightbox` klasu)
- **And** GLightbox navigacija (prev/next strelice, Esc zatvara, swipe touch) radi kroz vendor (Story 2-5 kontrakt)
- **And** thumbnail-i `loading="lazy"` (ispod fold-a). **WAIVER (SM-D8) — `{% responsive_picture %}`/srcset se NE primenjuje na galerijske thumbnail-e u v1; koristi se prost `<img src="..." loading="lazy">`.** Obrazloženje: project-context.md § Performance pravilo 2 traži srcset na user-facing slikama, ALI GLightbox zahteva da `<a class="glightbox" href="...">` pokazuje na PUNU rezoluciju slike; `responsive_picture` wrapper oko thumb-a komplikuje `href`/markup za marginalan dobitak (thumbnail je već mali, ispod fold-a, `loading="lazy"`). Plain `<img>` za thumb je prihvatljiv kompromis — sprečava code-review spor. Kad Story 8.8 CMS donese `GalleryImage` model + sorl-thumbnail pipeline, srcset se može uvesti tada (forward-compat, NE blokira ovu story).
- **And** NULA novih JS modula za galeriju (REUSE lightbox-init.js; NE pisati novi gallery JS)

**AC8 — `about-page.css`: BEM `coric-` prefiks; responsive (mobile stack → desktop); SVE vrednosti kroz `var(--token)`; reduced-motion guard; uvezen u main.css**

- **Given** AC4-AC7; `tokens.css` (Story 1-5); main.css (Story 3-1 zadnji @import home-page.css)
- **When** kreiram `static/css/components/about-page.css` + EDIT main.css
- **Then**:
  - BEM blokovi: `coric-about-hero`, `coric-about-story`, `coric-about-timeline`, `coric-about-gallery` (+ `__element` / `--modifier`); SVE klase `coric-` prefiks
  - Responsive: hero ~60vh mobile / ~90vh desktop (`@media (min-width: 768px)`); galerija `column-count` 1/2/3; lenta vertikalna stack mobile → horizontalna ILI vertikalna sa většom širinom desktop
  - SVE boje/spacing/radius kroz `var(--token)` (NEMA magic hex/px osim whitelist: `transparent`/`none`/`0` + dozvoljeni `%`/`vh`/`px` za layout dimenzije koje nemaju token — mirror Story 3-1 AC9 test toleranca)
  - Timeline reveal: hidden stanje gejtovano JS-markerom — `.coric-js .coric-about-timeline__segment { opacity:0; transform:...; }` (BEZ markera segmenti vidljivi — NO-JS fallback, AC6); `.is-revealed` final + `transition: ... 800ms ease-in-out`; `@media (prefers-reduced-motion: reduce) { transition: none }` guard
  - Watermark logo (AC5): renderovan kao `<img>` (NE CSS `background-image: url(...)` — token-test regex tretira `.png`/`.jpg` u `url()` kao non-`coric-` class selektor → FAIL; vidi AC5); `about-page.css` stiluje SAMO `opacity` (low) + `position`/`z-index` (iza teksta) kroz `var(--token)` — NULA `url()` u CSS-u
- **And** EDIT main.css: +1 `@import url('./components/about-page.css');` POSLE home-page.css
- **And** NEMA CDN; REUSE lightbox.css (NE dupliraj backdrop); NEMA dupliranja hero_overlay_card/section_eyebrow CSS-a (REUSE postojeće komponente)

**AC9 — i18n: sve user-facing string kroz `{% translate %}`/`{% blocktranslate %}`; .po fajlovi (sr/hu/en) popunjeni; pune dijakritike; NEMA ćirilice; strana se renderuje na sva 3 locale**

- **Given** AC1-AC8; postojeći `locale/{sr,hu,en}/LC_MESSAGES/django.po`
- **When** dodam nove msgid + `makemessages` + popunim msgstr + `compilemessages`
- **Then**:
  - SVI novi user-facing string-ovi kroz `{% translate %}` / `{% blocktranslate %}` (page title, meta description, hero naslov/slogan, eyebrow tekstovi „NAŠA PRIČA"/„VREMENSKA LENTA"/„GALERIJA", h2 naslovi, 2-3 paragrafa „Naša priča", 3 događaja lente (godina je broj — NE prevodi se; naslov+opis se prevode), galerija slika alt/title, eventualni hero CTA)
  - `locale/sr/` msgstr popunjen za SVE nove msgid (pune dijakritike č/ć/ž/š/đ; NEMA ćirilice; NEMA šišane latinice)
  - `locale/hu/` + `locale/en/` prevodi popunjeni
  - GET `/sr/o-nama/`, `/hu/o-nama/`, `/en/o-nama/` renderuju lokalizovan sadržaj (sr primaran)
- **And** smoke — 0 empty msgstr za nove msgid (sr); NEMA ćirilice u renderovanom HTML-u
  ```powershell
  Select-String -Pattern "[Ѐ-ӿ]" -Path templates/pages/about.html,templates/pages/partials/_about_*.html
  ```
  Očekivano: 0 rezultata (NEMA ćirilice)

**AC10 — A11y + smoke: dekorativni SVG/watermark aria-hidden; keyboard nav (galerija linkovi + lightbox); single h1/main; reduced-motion; Lighthouse a11y ≥ 95**

- **Given** AC3-AC9; project-context.md a11y must-haves; NFR-2 + UX-DR-13
- **When** Dev pokrene manuelni smoke + Lighthouse
- **Then**:
  - Single h1 (hero) + single main (base.html) + svaka sekcija aria landmark (AC3)
  - Dekorativni elementi `aria-hidden="true"`: hero foto-pozadina (AC4), watermark logo (AC5), SVG čvorovi/linije lente (AC6), eventualni wave divider
  - Tekstualni sadržaj lente čitljiv AT-u (NE u SVG `<text>` — AC6)
  - Keyboard: galerija `.glightbox` linkovi tab-abilni; Tab/strelice/Esc rade u lightbox-u (Story 2-5 focus trap + restoration); fokus outline vidljiv (`:focus-visible` `var(--color-semantic-focus-ring)`)
  - `prefers-reduced-motion: reduce` → lenta instant reveal (AC6) + lightbox instant (lightbox.css)
  - Touch mete ≥ 44×44px (galerija thumbnail linkovi, hero CTA — project-context.md / DESIGN.md:255)
  - Kontrast ≥ 4.5:1 (tekst preko watermark; hero overlay tekst)
- **And** Lighthouse (mobile, CLI) — A11y ≥ 95 + Performance ≥ 80 (hero LCP — NAPOMENA OQ-2: placeholder hero slika → LCP nije reprezentativan za produkciju; finalni gate sa realnom slikom); citiraj skor-ove u Completion Notes PRE review

## Tasks / Subtasks

- [x] **Task 1: `AboutView` + URL `pages:about` (AC1)**
  - [x] Subtask 1.1: DODAJ `class AboutView(TemplateView)` u `apps/pages/views.py` (POSLE `HomeView`): `template_name = "pages/about.html"`. Opcioni `get_context_data()` — ako se događaji lente / galerija drže kao Python liste literala radi DRY iteracije (SM-D1/SM-D5); inače prazan (TemplateView default). NE importovati domain modele za AboutView (v1 hardcoded). NE menjati `HomeView`
  - [x] Subtask 1.2: DODAJ `path("o-nama/", AboutView.as_view(), name="about")` u POSTOJEĆI `apps/pages/urls.py` `urlpatterns` (POSLE home path); import `AboutView`
  - [x] Subtask 1.3: Smoke — `manage.py check` exit 0; `reverse("pages:about")` → `/sr/o-nama/`; GET `/sr/o-nama/`,`/hu/o-nama/`,`/en/o-nama/` → 200; `pages:home` regresija (GET `/sr/` → 200, `pages/home.html`)

- [x] **Task 2: RAZREŠI Story 3-1 placeholder — wire `pages:about` (AC2, SM-D3)**
  - [x] Subtask 2.1: EDIT `templates/pages/partials/_home_about_intro.html`: zameni `href="#"` → `href="{% url 'pages:about' %}"`; UKLONI `aria-disabled="true"`, `tabindex="-1"`, `role="button"` placeholder atribute, TODO komentare (linije ~11-12,16-17); ZADRŽI `data-testid="home-about-cta"`; CTA = funkcionalan tab-abilan `coric-button coric-button--primary` link
  - [x] Subtask 2.2: EDIT `templates/partials/header.html`: (a) `:95` „O nama" nav link `href="#"` → `href="{% url 'pages:about' %}"`. (b) USPUTNA POPRAVKA šišane latinice: `:71` „Početna" nav link trenutno je `{% translate "Pocetna" %}` (šišana latinica — verifikovano live) → promeni u `{% translate "Početna" %}` (pune dijakritike; project-context.md zabranjuje šišanu latinicu u user-facing tekstu). NAPOMENA: u nav-u NE postoji nikakav aktivno-stranica pattern (`aria-current`/active klasa) ni na jednom linku (verifikovano live — `:71` „Početna" nema active markup) → dodavanje `aria-current="page"` je OPCIONO/van scope-a ove story; samo wire-uj URL, NE pokušavaj mirror-ovati nepostojeći pattern
  - [x] Subtask 2.3: Verifikuj `footer.html` — AKO „O nama" link `href="#"` postoji, wire na `pages:about` (SM-D3c; `Select-String "O nama" templates/partials/footer.html`)
  - [x] Subtask 2.4: Smoke — home „Saznaj više" CTA href = `/sr/o-nama/` (NE `#`), NEMA `aria-disabled`; header „O nama" → `/sr/o-nama/` 200; regresijski grep `aria-disabled` u `_home_about_intro.html` → 0

- [x] **Task 3: `about.html` + hero + naša-priča (AC3, AC4, AC5)**
  - [x] Subtask 3.1: Kreiraj `templates/pages/about.html` per AC3 skeleton (`{% extends "base.html" %}` + 4 `{% include %}` REDOM + title/meta_description + `{% block scripts %}{{ block.super }}` + timeline-reveal.js)
  - [x] Subtask 3.2: Kreiraj `templates/pages/partials/_about_hero.html` per AC4 (foto-pozadina `<img>` static eager dekorativna + hero_overlay_card `variant="green"` SM-D6, title `{% translate %}`, brand lockup; `aria-label` na section)
  - [x] Subtask 3.3: Kreiraj `templates/pages/partials/_about_story.html` per AC5 (bela pozadina + transparentni watermark logo `aria-hidden` + Section Eyebrow + h2 + 2-3 `{% translate %}` paragrafa)
  - [x] Subtask 3.4: Verifikuj TAČNO 1 h1 (hero) + single main (base.html) + svaka sekcija `<section>` sa aria landmark + heading hijerarhija h1→h2→h3

- [x] **Task 4: Vremenska lenta + `timeline-reveal.js` (AC6)**
  - [x] Subtask 4.1: Kreiraj `templates/pages/partials/_about_timeline.html` per AC6 (Section Eyebrow + h2 + `<ol data-timeline>` sa MIN 3 `<li data-timeline-segment>`: godina+h3 naslov+opis translatable; dekorativni SVG/CSS čvorovi/linija `aria-hidden="true"`; reveal CSS klase `opacity:0`+transform, `.is-revealed`)
  - [x] Subtask 4.2: Kreiraj `static/js/timeline-reveal.js` per AC6 — MIRROR `statistic-counter.js` 1:1: IIFE, `'use strict'`, `typeof window/document` guard, bail ako nema `[data-timeline]`; na init dodaj `coric-js` marker na root (gejtuje CSS hidden stanje — NO-JS fallback); `prefers-reduced-motion` → instant `.is-revealed`; IntersectionObserver threshold 0.3 + unobserve; IntersectionObserver fallback (svi odmah revealed); NE global pollution
  - [x] Subtask 4.3: Verifikuj tekstualni sadržaj NIJE u SVG `<text>` (čitljiv AT); dekorativni SVG `aria-hidden`; lenta MIN 3 događaja; timeline-reveal.js učitan SAMO na about strani (NE base.html)

- [x] **Task 5: Masonry galerija — REUSE GLightbox (AC7, SM-D8)**
  - [x] Subtask 5.1: Kreiraj `templates/pages/partials/_about_gallery.html` per AC7 (Section Eyebrow + h2 + `coric-about-gallery` CSS masonry sa 6-9 `<a class="glightbox" data-gallery="o-nama-galerija"><img alt loading="lazy"></a>`)
  - [x] Subtask 5.2: Verifikuj NULA novog lightbox JS — galerija koristi postojeći `lightbox-init.js` (`.glightbox` selektor već inicijalizovan site-wide; NE pisati novi gallery JS)
  - [x] Subtask 5.3: Verifikuj svaki `<img>` opisni `alt` (NE prazan — informativna galerija); `data-gallery` na svim linkovima (grupisanje); `loading="lazy"`

- [x] **Task 6: `about-page.css` + main.css EDIT (AC8)**
  - [x] Subtask 6.1: Kreiraj `static/css/components/about-page.css` per AC8 (4 BEM blokova `coric-` prefiks; responsive hero vh + galerija column-count; SVE `var(--token)`; timeline reveal transition 800ms ease-in-out + `prefers-reduced-motion` guard; watermark logo opacity/z-index)
  - [x] Subtask 6.2: Token verifikacija — svaki `var(--token)` postoji u tokens.css; ako nedostaje, ekvivalent + dokumentuj
  - [x] Subtask 6.3: EDIT `static/css/main.css` +1 `@import url('./components/about-page.css');` POSLE home-page.css
  - [x] Subtask 6.4: Verifikuj NEMA CDN; REUSE lightbox.css (NE dupliraj); hero/gallery assets dodati (`static/img/about/hero-o-nama.jpg` + `gallery/*.jpg`; ili solid fallback + TODO)

- [x] **Task 7: i18n .po update (AC9)**
  - [x] Subtask 7.1: `uv run python manage.py makemessages -l sr -l hu -l en` (Docker container)
  - [x] Subtask 7.2: `locale/sr/LC_MESSAGES/django.po` — popuni msgstr za sve nove msgid (pune dijakritike)
  - [x] Subtask 7.3: `locale/hu/` + `locale/en/` prevodi
  - [x] Subtask 7.4: `uv run python manage.py compilemessages -l sr -l hu -l en`
  - [x] Subtask 7.5: Smoke — 0 empty msgstr za nove msgid (sr); NEMA ćirilice

- [x] **Task 8: Manuelni Dev smoke + Lighthouse (AC10)**
  - [ ] Subtask 8.1: `just dev`; GET `/sr/o-nama/` — 4 sekcije REDOM + footer; hero overlay/watermark; tekst preko transparentnog logo-a; lenta reveal pri scroll; galerija masonry + lightbox otvara/navigacija
  - [ ] Subtask 8.2: Responsive (375px stack / 1200px desktop; hero vh; galerija column-count 1/2/3)
  - [ ] Subtask 8.3: `prefers-reduced-motion: reduce` — lenta instant reveal + lightbox instant
  - [ ] Subtask 8.4: Keyboard nav — galerija linkovi tab-abilni; lightbox Tab/strelice/Esc + focus restoration; fokus outline vidljiv
  - [x] Subtask 8.5: Verifikuj home „Saznaj više" CTA + header „O nama" → `/o-nama/` (SM-D3 razrešenje radi)
  - [ ] Subtask 8.6: Lighthouse CLI (`3-2-about-lighthouse-*.json`); A11y ≥ 95 + Performance ≥ 80; citiraj skor-ove u Completion Notes PRE review (OQ-2 LCP napomena)

- [ ] **Task 9: TEA-deliverable — testovi (RED phase, NIJE Dev scope)** _(TEA agent piše testove PRE Dev GREEN; Dev NIKAD ne piše testove — project-context.md § Test discipline)_
  - **Minimum test count (≈26 testova — TEA potvrđuje tačan broj u RED fazi):** 9.1=4 (AC1) + 9.2=4 (AC2 — Story 3-1 razrešenje) + 9.3=6 (AC3 struktura+AC9 i18n) + 9.4=4 (AC4+AC5 hero+priča) + 9.5=4 (AC6 lenta) + 9.6=4 (AC7 galerija) + 9.7=3 (AC8 CSS) = **≈26 navedenih.** JS modul `timeline-reveal.js` testira se kroz template markup (data-timeline atributi prisutni) + manuelni smoke (IntersectionObserver behavior — JS unit testovi van Django pytest scope-a, mirror statistic-counter.js bez JS unit testa).
  - [ ] Subtask 9.1: `apps/pages/tests/test_about_url.py` — **AC1: 4 tests**
    - `test_about_url_resolves_sr/hu/en` (3 lokala HTTP 200)
    - `test_about_uses_pages_about_template` (`assertTemplateUsed(response, "pages/about.html")`)
    - `test_pages_about_reverse_resolves` (`reverse("pages:about")` → `/sr/o-nama/`)
    - `test_home_view_still_works` (regresija — GET `/sr/` 200, `pages/home.html` — AboutView NE pokvario HomeView)
  - [ ] Subtask 9.2: `apps/pages/tests/test_about_home_cta_wired.py` — **AC2 (Story 3-1 razrešenje): 4 tests** (BeautifulSoup)
    - `test_home_about_cta_links_to_pages_about` (GET `/sr/` → `[data-testid=home-about-cta]` href = `/sr/o-nama/`, NE `#`)
    - `test_home_about_cta_no_longer_aria_disabled` (CTA NEMA `aria-disabled`/`tabindex=-1` — placeholder uklonjen)
    - `test_header_o_nama_link_wired` (GET bilo koje strane → header „O nama" nav link href = `pages:about`, NE `#`)
    - `test_home_about_cta_is_tabbable` (NEMA `tabindex="-1"` — keyboard dostupan)
  - [ ] Subtask 9.3: `apps/pages/tests/test_about_template_structure.py` — **AC3 + AC9: ~6 tests** (BeautifulSoup)
    - `test_about_renders_exactly_one_h1`
    - `test_about_renders_exactly_one_main` (iz base.html — NE dupliran)
    - `test_about_renders_4_sections_in_order` (hero → naša-priča → vremenska-lenta → galerija — DOM redosled)
    - `test_about_each_section_has_aria_landmark`
    - `test_about_no_cirillic_in_rendered_html`
    - `test_about_heading_hierarchy_no_skip` (h1→h2→h3)
  - [ ] Subtask 9.4: `apps/pages/tests/test_about_hero_story.py` — **AC4 + AC5: 4 tests** (BeautifulSoup)
    - `test_about_hero_includes_overlay_card_green_variant` (hero_overlay_card variant=green; h1 prisutan)
    - `test_about_hero_bg_image_is_decorative` (foto-pozadina `alt=""` + `aria-hidden`)
    - `test_about_story_has_decorative_watermark_logo_aria_hidden` (watermark logo `aria-hidden` / nije accessible)
    - `test_about_story_section_has_text_paragraphs` (≥2 `<p>` u naša-priča sekciji)
  - [ ] Subtask 9.5: `apps/pages/tests/test_about_timeline.py` — **AC6: 4 tests** (BeautifulSoup)
    - `test_timeline_renders_min_3_events` (≥3 `[data-timeline-segment]`)
    - `test_timeline_event_has_year_title_description` (svaki segment: godina + h3 + opis)
    - `test_timeline_decorative_svg_aria_hidden` (SVG čvorovi/linija `aria-hidden="true"`)
    - `test_timeline_text_content_not_in_svg_text` (godina/naslov/opis u semantic HTML, NE SVG `<text>`)
  - [ ] Subtask 9.6: `apps/pages/tests/test_about_gallery.py` — **AC7: 4 tests** (BeautifulSoup)
    - `test_gallery_renders_min_6_glightbox_links` (≥6 `a.glightbox`)
    - `test_gallery_links_share_data_gallery_group` (svi `data-gallery="o-nama-galerija"`)
    - `test_gallery_images_have_descriptive_alt` (img alt NIJE prazan)
    - `test_gallery_images_lazy_loaded` (`loading="lazy"`)
  - [ ] Subtask 9.7: `apps/pages/tests/test_about_page_css.py` — **AC8: 3 tests** (kolokovano uz app — mirror Story 3-1 `apps/pages/tests/test_home_page_css.py`; project-context.md § Test organization: unit testovi u `apps/<app>/tests/`. NE root `tests/`.)
    - `test_about_page_css_imported_in_main_css`
    - `test_about_page_css_uses_only_var_tokens` (0 magic hex; whitelist white/transparent/none + layout px/vh/%)
    - `test_about_page_css_has_coric_prefix_on_all_classes`
  - [ ] Subtask 9.8: TEA verifikuje RED phase (testovi padaju pre Dev GREEN); commit test fajlove PRE Dev (`test(pages): Story 3.2 RED-phase tests — AboutView + 4 sekcije + vremenska lenta + masonry galerija + pages:about wire`)

## Dev Notes

### `apps/pages/` struktura — AboutView se DODAJE (live verifikovano 2026-06-01)

`apps/pages/` app VEĆ postoji (Story 3-1). AboutView se DODAJE pored HomeView:
```
apps/pages/
├── __init__.py        (postoji)
├── apps.py            (PagesConfig — name="apps.pages"; NETAKNUTO)
├── views.py           (HomeView — NETAKNUTO; DODAJ AboutView(TemplateView))
├── urls.py            (app_name="pages"; path("", HomeView..., name="home") — DODAJ path("o-nama/", AboutView..., name="about"))
└── tests/             (test_home_*.py postoje; DODAJ test_about_*.py)
```
- `apps/pages/views.py:43` — `class HomeView(TemplateView)` (REFERENCA pattern za AboutView — `template_name`, `get_context_data`)
- `apps/pages/urls.py:9-11` — `urlpatterns = [path("", HomeView.as_view(), name="home")]` (DODAJ about path)
- `config/settings/base.py` — `apps.pages` već u INSTALLED_APPS (Story 3-1; NEMA promene)
- `config/urls.py` — `apps.pages.urls` već include-ovan (Story 3-1; novi about path je UNUTAR pages/urls.py, NEMA config/urls.py promene)

### Kritični REUSE pointeri (live verifikovani 2026-06-01)

- `templates/pages/partials/_home_hero.html:6-14` — hero foto-pozadina `<img>` (NE CSS bg — AC token-test razlog) + hero_overlay_card include pattern `variant="green"` + brand_logo `{% static 'img/coric-agrar-logo-transp-light-200.png' %}` (MIRROR za `_about_hero.html`)
- `templates/pages/partials/_home_about_intro.html:11-20` — placeholder „Saznaj više" CTA (SM-D3 RAZREŠENJE: ukloni aria-disabled/tabindex, wire `{% url 'pages:about' %}`)
- `templates/partials/header.html:95` — „O nama" nav link `href="#"` (SM-D3 WIRE na pages:about); `:71` nav link je `{% translate "Pocetna" %}` (šišana latinica — SM-D3 USPUTNA popravka → `{% translate "Početna" %}`). NAV nema `aria-current`/active markup ni na jednom linku (verifikovano live) → aktivno-stranica markup van scope-a ove story
- `templates/partials/hero_overlay_card.html` (Story 1-7) — `title`/`brand_logo`/`brand_logo_alt`/`variant`/`bullets`; renderuje h1
- `templates/partials/section_eyebrow.html` (Story 1-7) — `text`/`tag` (default „div"); UPPERCASE eyebrow
- `templates/partials/repeating_element.html` (Story 1-7) — `variant="green"`/`"jeegee"` SAMO (SM-D6 — indirekt kroz hero_overlay_card watermark)
- `static/js/lightbox-init.js` (Story 2-5) — VEĆ učitan `base.html:39-40`; inicijalizuje `.glightbox` na DOMContentLoaded; prefers-reduced-motion; data-gallery grupisanje; htmx:afterSwap re-init. REUSE 1:1 za galeriju — NULA novog JS
- `static/js/statistic-counter.js` (Story 2-6) — IntersectionObserver + prefers-reduced-motion + data-* + threshold 0.3 + unobserve + IO fallback (MIRROR 1:1 za `timeline-reveal.js`). NAPOMENA: učitan SITE-WIDE u `base.html:41` (defer) — NE re-dodavati u about.html `{% block scripts %}` (izbegni dvostruko učitavanje); about.html scripts blok dodaje SAMO `timeline-reveal.js` (uz `{{ block.super }}` da zadrži site-wide skripte)
- `static/css/components/lightbox.css` (Story 2-5) — backdrop rgba(15,15,15,0.85) + reduced-motion guard (REUSE — NE edit)
- `base.html:39-40` — GLightbox vendor + lightbox-init.js (REUSE); `:44 {% block scripts %}` (timeline-reveal.js per-page); `:13` glightbox.min.css link
- `static/css/main.css` — zadnji `@import` je home-page.css (Story 3-1; DODAJ about-page.css posle)
- `static/css/tokens.css:84-165` — `--color-brand-green-900/800/600/400` (:84-87), `--color-accent-gold-500` (:90), `--color-neutral-white/cream/gray-700/gray-500` (:97-102), `--color-semantic-focus-ring` (:112), `--typography-scale-h1/h2/h3/body/caption` (:123-129), `--rounded-sm/md/pill` (:142-145), `--shadow-md` (:151), `--spacing-scale-*` (:157-165)
- `templates/base.html` — single `<main id="main-content">` + `{% block content %}` + `{% block scripts %}` + header/footer/aria-live (NE dupliraj)
- epics.md:724-734 (Story 3.2 AC), :34 (FR-4), :240 (UX-DR-28), :1156-1163 (Epic 8 8.8 CMS — content edit defer)
- EXPERIENCE.md:82 (sitemap `/o-nama`), :267 (lenta 800ms ease-in-out), DESIGN.md:267,293-299 (wave selektivno), architecture.md:203,587-593,670,894

### SM Decisions log

- **SM-D1** — **`AboutView(TemplateView)` u POSTOJEĆEM `apps/pages/views.py` (mirror Story 3-1 HomeView):** „O nama" je statička strana koju architecture.md mapira u `apps/pages/` (:587-593 `views.py # HomeView, AboutView, ContactView`; :894 FR-1..FR-5 apps/pages/; FR-4 O nama). `apps/pages/` app postoji (Story 3-1). Lock: DODAJ `class AboutView(TemplateView)` (`template_name = "pages/about.html"`) pored HomeView. CBV TemplateView (NE FBV) — mirror Story 3-1 SM-D1 (idiomatičan za read-only render). v1: NE importuje domain modele (sadržaj hardcoded-translatable; za razliku od HomeView koji agregira). Opcioni `get_context_data()` SAMO ako se događaji lente/galerija drže kao Python liste literala radi DRY iteracije (čista lista, NE DB query).
- **SM-D2** — **URL `/o-nama/` + ime `pages:about`:** `path("o-nama/", AboutView.as_view(), name="about")` u `apps/pages/urls.py` (POSLE home path). `i18n_patterns()` daje `/sr|hu|en/o-nama/`. Slug segment `o-nama` ASCII, ISTI za sve lokale u v1 (NEMA per-locale URL slug prevod — mirror Story 2-x fiksne slug segmente; gettext_lazy na URL pattern van scope-a). project-context.md:161 (`/o-nama/`), EXPERIENCE.md:82 sitemap, epics.md AC `/sr/o-nama/`.
- **SM-D3** — **RAZREŠENJE Story 3-1 placeholder (`pages:about` postaje stvaran) — DEO DoD:** Story 3-1 ostavio 2 mrtva placeholder-a (+eventualno footer): (1) `_home_about_intro.html` „Saznaj više" CTA (KANONSKI PLACEHOLDER-CTA `href="#"`+`aria-disabled`+`tabindex="-1"`+TODO); (2) `header.html:95` „O nama" nav `href="#"`. Lock: kada `pages:about` postoji → (a) `_home_about_intro.html`: `href="{% url 'pages:about' %}"`, UKLONI aria-disabled/tabindex/role placeholder/TODO, ZADRŽI data-testid; (b) `header.html:95`: `href="{% url 'pages:about' %}"` (NAV nema aktivno-stranica pattern — verifikovano live; `aria-current` OPCIONO/van scope-a, samo wire URL) + USPUTNA popravka `:71` `{% translate "Pocetna" %}` → `{% translate "Početna" %}` (pune dijakritike); (c) footer „O nama" link AKO postoji `href="#"`. Bez ovog placeholder ostaje mrtav — DEO DoD ove story.
- **SM-D4** — **4 sekcije TAČAN red (epics.md AC + EXPERIENCE.md):** hero → naša-priča (tekst+watermark logo) → vremenska-lenta → galerija. Footer iz base.html. Red normativan (epics.md:732 redosled „full-screen hero … duži tekst … interaktivna SVG vremenska lenta … masonry galerija").
- **SM-D5** — **Sadržaj hardcoded-translatable Lorem Ipsum (CMS = Epic 8 Story 8.8; mirror Story 3-1 SM-D10):** CMS (`Page`/`AboutTimelineEvent`/`GalleryImage` modeli + admin WYSIWYG + galerija inline) je Story 8.8 (epics.md:1156-1163) + SiteSettings Story 3-4. v1: sav sadržaj hardcoded-translatable kroz `{% translate %}`/`{% blocktranslate %}` — hero foto-pozadina static `img/about/hero-o-nama.jpg`; tekst 2-3 paragrafa Lorem Ipsum; lenta 3 hardcoded događaja (godina+naslov+opis); galerija 6-9 placeholder slika `img/about/gallery/`. epics.md AC eksplicitno „za sada Lorem Ipsum". Forward-compat: kad Story 8.8 stigne, view popuni context iz baze, template grana ista. NE fake Page model, NE migracija, NE admin. EXPERIENCE.md „video ili slika" → v1 SLIKA (video je CMS scope).
- **SM-D6** — **`variant="green"` za hero + Repeating Element watermark (mirror Story 3-1 SM-D9):** repeating-element.css ima SAMO `--green`+`--jeegee`. About hero koristi `variant="green"`. NE izmišljati `variant="about"`/`"home"` (unstyled watermark bug).
- **SM-D7** — **Vremenska lenta = inline SVG/CSS + `timeline-reveal.js` (JEDINI novi JS; architecture.md:670):** lenta inline SVG/CSS (architecture.md:203 „SVG inline + CSS + IntersectionObserver"). Reveal CSS transition 800ms ease-in-out (DESIGN.md:267) trigger kroz NOVI `timeline-reveal.js` (vanilla IIFE, MIRROR statistic-counter.js: data-* atributi, threshold 0.3, unobserve, prefers-reduced-motion instant, IO fallback, coric: namespace). reduced-motion → instant reveal. NO-JS/observer-never-fires fallback: hidden stanje (`opacity:0`) gejtovano `coric-js` markerom koji JS dodaje na init → bez JS segmenti su PUNO vidljivi (graceful degradation, mirror statistic-counter; vidi AC6). Dekorativni SVG čvorovi/linija `aria-hidden="true"` (epics.md AC); TEKST u semantic HTML (NE SVG `<text>` — AT čitljiv). `timeline-reveal.js` per-page (about.html `{% block scripts %}{{ block.super }}`, NE base.html).
- **SM-D8** — **Masonry galerija = CSS-only layout + REUSE GLightbox (NULA novog JS):** GLightbox vendor + lightbox-init.js već site-wide (`base.html:39-40`; `.glightbox` selektor; prefers-reduced-motion; data-gallery grupisanje). Galerija markup `<a class="glightbox" data-gallery="o-nama-galerija"><img alt loading="lazy"></a>` → lightbox radi BEZ novog JS. Masonry layout ČIST CSS (`column-count` responsive + `break-inside: avoid`; NE Masonry.js — DESIGN.md/architecture.md ne pominju lib). lightbox.css REUSE (backdrop+reduced-motion). img `alt` OPISNI (informativna galerija). **srcset WAIVER:** `{% responsive_picture %}`/srcset se NE primenjuje na galerijske thumb-ove u v1 (plain `<img loading="lazy">`) — GLightbox `href` mora na punu rezoluciju, responsive_picture wrapper komplikuje markup za marginalan dobitak; izričito odstupanje od project-context.md § Performance pravilo 2 za galerijske thumb-ove (vidi AC7). Srcset moguć u Story 8.8 CMS (GalleryImage + sorl-thumbnail).
- **SM-D9** — **Hero title — „O nama" naslov ILI slogan (Dev/Step-02 bira; v1 default „O nama"):** EXPERIENCE.md hero „slogan preko". home hero koristi slogan „Prijatelj koji razume zemlju!". About hero može: (a) „O nama" kao h1 (jasno za stranu), ILI (b) ponoviti slogan, ILI (c) about-specifičan podnaslov. v1 lock: `title=_("O nama")` (semantički h1 strane; SEO + a11y „page title" jasnoća). Ako biznis želi slogan/drugi naslov, trivijalna izmena (NE blokira). Vidi OQ-3.
- **SM-D10** — **Galerija slika `alt` OPISNE, NE prazne:** galerija je INFORMATIVNA (fotografije firme/tima/mašina), NE dekorativna → img `alt` je opisan translatable tekst (project-context.md a11y; razlikuje se od hero foto-pozadine koja je dekorativna `alt=""`). lightbox-link wrapper `<a>` dobija accessible naziv iz img alt.
- **SM-D11** — **Responsive hero vh (mirror Story 3-1 SM-D12):** hero ~60vh mobile / ~90vh desktop (epics „full-screen hero"; konzistentno sa home ~60/80vh skalom kroz `@media (min-width: 768px)`). Galerija `column-count` 1 mobile / 2 tablet / 3 desktop.
- **SM-D12** — Sprint-status.yaml update je SM handoff tracking (NIJE deliverable; epic-3 već in-progress iz Story 3-1).

### Open Questions

- **OQ-1 (per-locale URL slug — `/o-nama/` vs `/rolunk/` vs `/about/`):** v1 lock (SM-D2): slug segment `o-nama` ISTI za sva 3 locale (i18n_patterns daje samo `/sr|hu|en/` prefix). Per-locale slug prevod (`django.utils.translation.gettext_lazy` na URL pattern → `/hu/rolunk/`, `/en/about/`) je MOGUĆ Django feature ali van scope-a v1 (konzistentno sa Story 2-x landing slug-ovima koji su fiksni). Status: OTVORENO — fiksan `o-nama` OK za v1; per-locale slug razmotriti u Step-02 ako SEO zahteva (verovatno NE — interni sajt, 1 tržište).
- **OQ-2 (Hero + galerija asset-i — ⛔ PRODUCTION BLOCKER, mirror Story 3-1 OQ-1):** AC4/AC7/SM-D5 zahtevaju `static/img/about/hero-o-nama.jpg` + 6-9 `gallery/*.jpg`. Dev dodaje optimizovane placeholder/stock slike (hero ≤300KB ~1920px; galerija različite dimenzije za masonry). Ako stock nedostupne pre Dev GREEN → solid-color fallback + TODO (ISKLJUČIVO dev/smoke, NIJE produkcija). **⛔ PRODUKCIONI BLOKER:** realne fotografije firme/tima MORAJU pre production publish-a (vlasništvo: Mihas/biznis; Story 9.x asset checklist). Hero je above-fold LCP → bez realne slike AC10 Performance ≥ 80 LCP nije reprezentativan za produkciju. Status: OTVORENO — placeholder OK za Dev/smoke; realne slike BLOCKING za produkciju.
- **OQ-3 (Hero title — „O nama" vs slogan vs podnaslov):** v1 lock (SM-D9): `title=_("O nama")` (h1 = page title, SEO/a11y jasnoća). Alternativa: ponoviti slogan „Prijatelj koji razume zemlju!" (vizuelni kontinuitet sa home) ILI about-specifičan podnaslov. Status: OTVORENO — „O nama" OK za v1; biznis copy razmotriti u Step-02/8.8 CMS.
- **OQ-4 (Vremenska lenta sadržaj — stvarne godine/događaji):** v1 lock (SM-D5): 3 placeholder događaja (npr. 2008 osnivanje / 2015 širenje / 2024 partnerstva). Stvarni datumi/događaji = biznis input (Mihas/klijent). Status: OTVORENO — placeholder OK za v1; stvarni sadržaj kroz 8.8 CMS ili Dev/biznis usaglašavanje pre produkcije.

### Project Context Reference

Sva pravila iz `_bmad-output/project-context.md` se primenjuju. Posebno kritično:
- Srpski latinica pune dijakritike (č/ć/ž/š/đ) u svemu renderovanom; ASCII u static putanjama + URL slug (`o-nama`)
- Sve UI string kroz `{% translate %}` / `{% blocktranslate %}`
- CSS `var(--token)` (NEMA magic hex/px); `coric-` BEM prefiks
- JS: vanilla IIFE, `coric:` namespace, NE global pollution, prefers-reduced-motion guard (timeline-reveal.js mirror statistic-counter.js)
- NEMA migracije (`apps/pages` bez modela u v1); NEMA forma; NEMA HTMX; SAMO 1 novi JS (timeline-reveal.js); REUSE GLightbox (0 novog lightbox JS)
- A11y must-haves: single h1, single main (base.html), aria landmarks, accessible naziv na klik zonama (galerija linkovi), focus-visible, contrast ≥ 4.5:1, prefers-reduced-motion (lenta + lightbox), aria-hidden na dekorativnim (hero bg, watermark logo, SVG lente čvorovi)
- Performance: hero LCP above-fold eager; galerija thumb `loading="lazy"`; srcset WAIVED za galerijske thumb-ove u v1 (plain `<img>` — GLightbox href na punu rezoluciju; SM-D8/AC7)

### References

- [Source: _bmad-output/planning-artifacts/epics.md:724-734 (Story 3.2 O nama AC); :34 (FR-4); :240 (UX-DR-28 O nama intro→/o-nama); :1156-1163 (Epic 8 Story 8.8 CMS content edit defer)]
- [Source: _bmad-output/planning-artifacts/ux-designs/ux-CORIC_AGRAR-2026-05-27/EXPERIENCE.md:82 (sitemap /o-nama); :267 (vremenska lenta 800ms ease-in-out scroll-into-view IntersectionObserver); :168-172 (Lightbox backdrop+navigacija+Esc+focus restoration)]
- [Source: _bmad-output/planning-artifacts/ux-designs/ux-CORIC_AGRAR-2026-05-27/DESIGN.md:267 (lenta animacija); :287 (modal backdrop rgba 15,15,15,0.85); :293-299 (wave selektivno); :255 (touch meta 44px)]
- [Source: _bmad-output/planning-artifacts/architecture.md:202-204 (GLightbox 3.x + SVG lenta inline+CSS+IntersectionObserver + animacije bez external lib); :587-593 (apps/pages/ dir HomeView/AboutView/ContactView); :668-670 (lightbox-init.js/statistic-counter.js/timeline-reveal.js); :894 (FR-1..FR-5 apps/pages/)]
- [Source: _bmad-output/implementation-artifacts/3-1-home-strana-sa-svim-sekcijama.md — apps/pages/ scaffold, HomeView TemplateView pattern, SM-D10 hardcoded-translatable hero, SM-D14 placeholder CTA (RAZREŠEN ovde), _home_hero.html img bg pattern, SM-D9 variant green]
- [Source: apps/pages/views.py:43 HomeView (REFERENCA AboutView); apps/pages/urls.py:9-11 urlpatterns (DODAJ about)]
- [Source: templates/pages/partials/_home_about_intro.html:11-20 placeholder „Saznaj više" CTA (SM-D3 RAZREŠENJE); templates/partials/header.html:95 „O nama" nav (SM-D3 WIRE), :71 Početna nav (aktivno markup ref)]
- [Source: static/js/statistic-counter.js (IntersectionObserver+reduced-motion+data-* MIRROR za timeline-reveal.js); static/js/lightbox-init.js (.glightbox REUSE galerija); static/css/components/lightbox.css (backdrop+reduced-motion REUSE)]
- [Source: templates/base.html:13,39-40,44 (glightbox.min.css + GLightbox vendor + lightbox-init.js + {% block scripts %})]
- [Source: static/css/tokens.css:84-165 (boje/typography/rounded/shadow/spacing tokeni)]
- [Source: _bmad-output/project-context.md — sva pravila]

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
