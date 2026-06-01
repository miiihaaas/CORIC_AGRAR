---
story_id: "3.3"
story-key: 3-3-kontakt-strana-sa-formom-i-mapom
title: Kontakt Strana sa Formom i Mapom
status: ready-for-dev
epic: 3
epic_num: 3
epic_title: Home & Static Pages
module: pages
created: 2026-06-01
last_modified: 2026-06-01
complexity: M
author: Mihas (SM autonomous; TREĆA story Epic 3. „Kontakt" je STATIČKA read-only strana na `/kontakt/` (sr) — `ContactView(TemplateView)` u POSTOJEĆEM `apps/pages/` (mirror Story 3-1 HomeView + Story 3-2 AboutView). Renderuje 3 bloka iz FR-5 + epics.md AC: (1) kontakt-info sekcija (adresa, telefon prodaja, telefon servis, email, radno vreme, social linkovi) — hardcoded-translatable do Story 3-4 SiteSettings/Epic 4; (2) Google Maps iframe embed sa pin-om lokacije firme (static iframe, NULA JS, EXPERIENCE.md/architecture.md:786 „inline iframe, no JS dep"); (3) FORWARD-COMPAT KONTAKT FORMA SKELET — vizuelni markup polja (Ime, Email, Telefon, Poruka) sa CSRF tokenom, ALI bez funkcionalnog submit-a (`disabled`/placeholder dugme + aria-disabled + TODO marker) jer Lead model + SMTP + HTMX submit pripadaju Epic 4 (Story 4.1/4.2/4.6 — SVE backlog). KRITIČNA SM-D4 — interpretacija (A): 3-3 isporučuje STRANU + MAPU + skelet forme; FUNKCIONALNA forma (Lead/email/ratelimit/HTMX) dolazi iz Epic 4 (epics.md:744 „forma povezana sa Story 4.2 ContactForm", :746 „Forma prati HTMX pattern iz Story 4.6"). Sadržaj hardcoded-translatable (mirror 3-2 SM-D5; SiteSettings = Story 3-4 backlog, dolazi POSLE ove story). REŠAVA placeholder: `pages:contact` URL postaje stvaran → header.html:96 „Kontakt" nav link `href="#"` se WIRE-uje na `pages:contact` (mirror kako je 3-2 wire-ovao „O nama"). NEMA HTMX, NEMA Lead modela, NEMA SMTP, NEMA migracija, NEMA `apps/forms` app-a, NEMA funkcionalnog submit-a. 0 novih JS modula. 1 nova CSS komponenta `contact-page.css`. RISK: MEDIUM — third-party Google Maps iframe embed + CSP forward-compat (django-csp dep prisutan ali CSP JOŠ NIJE konfigurisan u settings → iframe radi danas; frame-src/img-src allowance je forward-compat OQ za Epic 9 hardening) + forma-skelet a11y (CSRF token + labele) bez funkcionalnosti. NIJE HIGH jer NEMA modela/migracije/funkcionalne forme/user-input procesiranja u v1.)
depends_on:
  - 1-4-i18n-setup-sa-locale-url-routing-i-switcher       # i18n_patterns() → /<lang>/kontakt/; LANGUAGE_CODE; {% translate %}
  - 1-6-base-templates-sa-bootstrap-5-htmx-setup          # base.html blokovi content/title/meta_description/extra_head/scripts; single <main>; aria-live; {% csrf_token %} dostupan
  - 1-7-reusable-visual-komponente                         # section_eyebrow, hero_overlay_card (opciono hero), coric-button BEM
  - 1-8-sticky-nav-top-header-footer-language-switcher-partial  # header.html:96 „Kontakt" nav link (href="#" → WIRE na pages:contact); top-header + footer već imaju kontakt info (REUSE referenca, NE dupliraj)
  - 3-1-home-strana-sa-svim-sekcijama                      # apps/pages/ app scaffold (PagesConfig + INSTALLED_APPS + urls.py app_name="pages"); pages:home; HomeView TemplateView pattern
  - 3-2-o-nama-strana                                      # AboutView(TemplateView) pattern (mirror za ContactView); pages:about wire obrazac (mirror za pages:contact header wire); about-page.css = poslednji main.css @import (contact-page.css ide POSLE); hardcoded-translatable Lorem Ipsum obrazac (SM-D5); header:96 „Kontakt" je SLEDEĆI mrtav nav placeholder
---

# Story 3.3: Kontakt Strana sa Formom i Mapom

Status: ready-for-dev

## Opis

As a **posetilac (Marko — poljoprivrednik koji posle pregleda ponude želi da kontaktira Ćorić Agrar telefonom/emailom/formom; Stojan — koji sa mobilnog na 375px traži adresu i telefon servisa za hitan kvar; Đorđe — koji testira tastaturom + NVDA da li su kontakt informacije i forma dostupne; SEO bot koji indeksira „Kontakt" stranu sa lokalnim podacima)**,

I want **da otvorim `/sr/kontakt/` i nađem (1) kontakt informacije (adresa, telefon prodaje, telefon servisa, email, radno vreme, linkovi ka društvenim mrežama); (2) ugrađenu Google Maps mapu sa pin-om na lokaciji firme; (3) kontakt formu sa poljima (ime, email, telefon, poruka)**,

so that **mogu da kontaktiram firmu na način koji mi odgovara — telefonom, emailom, ili formom; strana je potpuno responzivna (mobile stack → desktop), zadovoljava single-h1 pravilo, koristi semantic HTML5 + ARIA landmarks, mapa je ugrađena bez JS zavisnosti, prolazi Lighthouse a11y ≥ 95 (UX-DR-13 + NFR-2), i REUSE-uje postojeće vizuelne komponente (section_eyebrow, coric-button) uz NULA novih JS modula i minimalan novi CSS**.

Ovo je **treća story Epic 3 (Home & Static Pages)** i druga čisto statička strana sajta (posle „O nama" 3-2). „Kontakt" NE definiše nove modele, NE menja postojeće, NE uvodi funkcionalnu formu ni HTMX. Strana je „kontakt izlog" — sve kontakt informacije + lokacija + forma za upit na jednom mestu (UJ-2 entry point; EXPERIENCE.md:100 `/kontakt → Info + forma + Google Maps`).

🔴 **SM ODLUKA — RAZREŠENJE SCOPE-a FORME: interpretacija (A) — STRANA + MAPA + FORWARD-COMPAT SKELET FORME; FUNKCIONALNA FORMA JE EPIC 4 — SM-D4 (KRITIČNA, srce ove story):**

Naziv story-ja kaže „SA FORMOM", ali epics.md Story 3.3 AC EKSPLICITNO veže formu na Epic 4:
- epics.md:742 — **Given** „Forma iz Epic 4 (parallel dev) ili stub iz Story 4.2"
- epics.md:744 — „kontakt forma (FR-5 — **povezana sa Story 4.2 ContactForm**)"
- epics.md:746 — „Forma **prati HTMX pattern iz Story 4.6**"

Cela Epic 4 (Lead-gen Forms & Email Delivery) je BACKLOG: `4-1 Lead model + SMTP`, `4-2 Opšta kontakt forma (FR-5)`, `4-6 HTMX patterns / aria-live OOB / ratelimit` — SVE backlog (sprint-status.yaml:95-101). `Lead` model NE postoji, NEMA SMTP/`django-anymail` config, NEMA `apps/forms` app (verifikovano live — `apps/` sadrži samo brands/core/media_pipeline/pages/products/search; NEMA forms). Takođe: kontakt info dolazi iz `SiteSettings` (epics.md:744 „iz `SiteSettings` modela"), ali `SiteSettings` je **Story 3-4 (SLEDEĆA story, takođe backlog)** — dolazi POSLE ove story.

**Lock (SM-D4) — interpretacija (A):** Story 3-3 isporučuje:
1. **STATIČKU KONTAKT STRANU** — scaffold + layout + a11y + i18n (ContactView TemplateView u `apps/pages/`, mirror AboutView).
2. **KONTAKT-INFO SEKCIJU** — adresa, telefon prodaje, telefon servisa, email, radno vreme, social linkovi — **hardcoded-translatable** (mirror 3-2 SM-D5; forward-compat ka SiteSettings Story 3-4 — view može kasnije popuniti context iz `SiteSettings.objects.get()`, template grana ista). REUSE iste podatke koje top-header/footer već prikazuju (tel `+381230468168`, email `prodaja@coricagrar.rs` — konzistentnost), UZ izuzetak adrese koju kontakt strana renderuje sa PUNIM dijakritikama „Vojvođanska 1, Basaid, Srbija" (top-header/footer šišana „Vojvodjanska" je nasleđeni dug — OQ-6; kontakt strana zadovoljava AC8).
3. **GOOGLE MAPS IFRAME** — static `<iframe>` embed sa pin-om lokacije, NULA JS (architecture.md:786 „inline iframe, no JS dep"; epics.md:745 „embed bez JS dep-a"). Vidi SM-D6 (embed pristup + CSP forward-compat + lazy + a11y title).
4. **FORWARD-COMPAT SKELET KONTAKT FORME** — vizuelni markup polja (Ime *, Email *, Telefon, Poruka *) sa **`{% csrf_token %}` prisutnim**, semantic `<label>` za svako polje, ALI **bez funkcionalnog submit-a**: forma NEMA `action`/`method` POST handler (jer endpoint `/htmx/forme/kontakt/` i ContactForm dolaze iz Story 4.2), submit dugme je `disabled` + `aria-disabled="true"` + vidljiv „uskoro" hint + KANONSKI TODO marker `{# TODO Story 4.2 (Epic 4): wire funkcionalan ContactForm + hx-post="/htmx/forme/kontakt/" + ratelimit + uspeh/greška HTMX pattern (Story 4.6). Ukloni disabled/aria-disabled. #}`. Mirror 3-2 placeholder-CTA obrazac (forward-compat, NE fake funkcionalnost, NE dead-link, NE 404).

**Funkcionalna forma (Lead model, server-side validacija, email send, ratelimit, HTMX submit/aria-live OOB) NIJE u scope-u ove story — isporučuje Epic 4 (Story 4.2 + 4.6).** Ova story NE kreira `Lead` model, NE migraciju, NE `apps/forms` app, NE SMTP config, NE funkcionalan POST handler. Vidi OQ-1 (headline dependency).

**Zašto (A), ne (B):** epics.md AC eksplicitno deli odgovornost (3.3 = strana + mapa + info; 4.2 = ContactForm funkcionalnost; 4.6 = HTMX/ratelimit pattern). Povlačiti Lead+SMTP unapred iz Epic 4 bi bio cross-epic scope-creep koji epic NE traži; AC „stub iz Story 4.2" + „forma povezana sa 4.2" jasno stavlja funkcionalnost u Epic 4. Mirror Story 3-1 SM-D7 + Story 3-2 forward-compat placeholder obrazac (skelet bez fake modela/migracije). Vidi SM-D4 + OQ-1.

**SM ODLUKA — `ContactView` ŽIVI u POSTOJEĆEM `apps/pages/` (mirror Story 3-1 HomeView + 3-2 AboutView) — SM-D1:** „Kontakt" je statička strana koju architecture.md EKSPLICITNO mapira u `apps/pages/` (architecture.md:587-592 dir struktura `pages/ … views.py # HomeView, AboutView, ContactView`; :592 `urls.py # /, /o-nama/, /kontakt/`; :894 „FR-1..FR-5 (Početna + statičke strane) | `apps/pages/`"; FR-5). `apps/pages/` app VEĆ postoji (Story 3-1). **Lock:** „Kontakt" se implementira kao `class ContactView(TemplateView)` u POSTOJEĆEM `apps/pages/views.py` (DODAJE se klasa POSLE `AboutView`; NE menja `HomeView`/`AboutView`); `template_name = "pages/contact.html"`. CBV `TemplateView` (NE FBV) — mirror Story 3-2 SM-D1 obrazloženje (idiomatičan Django izbor za read-only render stranu sa hardcoded kontekstom; project-context.md dozvoljava CBV za standardne render strane). **VAŽNO:** v1 je čisto GET render — NE primamo POST (forma je skelet, submit je `disabled`). Kad Story 4.2 doda funkcionalnu formu, HTMX submit ide na ZASEBAN `apps/forms` endpoint (`/htmx/forme/kontakt/`, architecture.md:598), NE na `ContactView` — `ContactView` ostaje GET-only render strane. v1 `get_context_data()` može držati kontakt-info kao hardcoded Python literale (radno vreme, telefoni) radi DRY ILI sve u template-u; NE DB query (SiteSettings ne postoji). Vidi SM-D1 + SM-D5.

**SM ODLUKA — URL `/kontakt/` + ime `pages:contact` — SM-D2:** URL je `/<lang>/kontakt/` kroz `i18n_patterns()` (project-context.md URL paths kebab-case/srpske reči; architecture.md:592 `/kontakt/`; EXPERIENCE.md:100 sitemap `/kontakt`; epics.md AC „posetim `/sr/kontakt/`"). URL ime je `pages:contact` (namespace `pages` iz `apps/pages/urls.py` `app_name="pages"`; mirror `pages:home`/`pages:about`). **Lock:** dodaj `path("kontakt/", ContactView.as_view(), name="contact")` u POSTOJEĆI `apps/pages/urls.py` `urlpatterns` (POSLE `path("o-nama/", AboutView.as_view(), name="about")`). hu/en lokali: `i18n_patterns()` daje `/hu/kontakt/` + `/en/kontakt/` — URL PATH SEGMENT (`kontakt`) ostaje ISTI za sve lokale u v1 (NEMA per-locale slug prevod URL-a; mirror Story 3-2 SM-D2). Slug ASCII (`kontakt`). Vidi SM-D2 + OQ-2.

**SM ODLUKA — RAZREŠENJE header „Kontakt" nav placeholder-a (`pages:contact` → stvaran) — SM-D3 (DEO DoD):** `templates/partials/header.html:96` „Kontakt" nav link je trenutno mrtav placeholder: `<a class="nav-link coric-nav__link" href="#">{% translate "Kontakt" %}</a>` (iz Story 1-8; verifikovano live 2026-06-01). **Lock (SM-D3):** kada `pages:contact` postane stvaran (ova story), Dev MORA:
- (a) U `header.html:96`: zameniti `href="#"` → `href="{% url 'pages:contact' %}"`. NAV nema aktivno-stranica pattern (verifikovano live — mirror 3-2 SM-D3: ni jedan nav link nema `aria-current`/active markup), pa SAMO wire-uj URL; `aria-current="page"` je OPCIONO/van scope-a.
- (b) Footer: footer NEMA „Kontakt" NAV link (verifikovano live — `templates/partials/footer.html` ima kontakt INFO blok sa `tel:`/`mailto:`/`<address>`, ali NE link ka `/kontakt/` strani). Social linkovi (`href="#"`) i Proizvodi/Vesti linkovi (`href="#"`) su ZASEBNI placeholder-i koji NE pripadaju ovoj story (van scope-a — to su Epic 2/5/7 wire-ovi). **NE diraj footer u ovoj story** osim ako želiš dodati „Kontakt" link u Kontakt kolonu — to je OPCIONO (vidi OQ-5). Default: NE menjaj footer.

Mirror kako je Story 3-2 razrešio „O nama" header placeholder (SM-D3). Bez ovog header „Kontakt" ostaje mrtav. Vidi SM-D3.

**REUSE fokus (0 novih JS modula; 1 nova CSS komponenta `contact-page.css`):**

- **`ContactView(TemplateView)`** (`apps/pages/views.py`, DODAJE se klasa POSLE `AboutView`) — `template_name = "pages/contact.html"`; opcioni `get_context_data()` za hardcoded kontakt-info literale (SM-D5). Mirror `AboutView` struktura (NE importuje domain modele).
- **`templates/partials/section_eyebrow.html`** (Story 1-7) — UPPERCASE eyebrow iznad svake sekcije (npr. „KONTAKTIRAJTE NAS", „NAŠA LOKACIJA", „POŠALJITE UPIT").
- **`coric-button` + `coric-button--primary`** (Story 1-7 `pill-button.css`) — REUSE za submit dugme forme (u v1 `disabled` + `aria-disabled` placeholder; Story 4.2 ga aktivira).
- **`{% csrf_token %}`** (Django, dostupan u svim template-ima sa request kontekstom) — MORA biti u `<form>` skeletu već u v1 (project-context.md § Security must-haves #1: CSRF na svim formama, uključujući HTMX; AC6). Iako forma nema funkcionalan submit u v1, CSRF token je prisutan tako da Story 4.2 samo aktivira submit bez restrukturiranja markup-a.
- **`base.html`** (Story 1-6) — `{% extends "base.html" %}`; `{% block title %}`, `{% block meta_description %}`, `{% block content %}`, `{% block extra_head %}` (opciono, ako mapa zahteva preconnect — vidi SM-D6), single `<main id="main-content">` + aria-live VEĆ prisutni (NE dupliraj). NEMA `{% block scripts %}` dodatka (NULA novog JS — SM-D7).
- **CSS tokens** (`static/css/tokens.css`, Story 1-5): `--color-brand-green-900/800/600`, `--color-accent-gold-500`, `--color-neutral-white/cream/gray-700/gray-500`, `--color-semantic-focus-ring`, `--spacing-scale-*`, `--rounded-md/sm/pill`, `--shadow-md`, `--typography-scale-h1/h2/h3/body/caption`.
- **Top-header + footer kontakt podaci** (Story 1-8) — REUSE iste vrednosti (adresa, telefon prodaja `+381230468168`, email `prodaja@coricagrar.rs`) radi konzistentnosti (NE dupliraj markup; isti translatable string-ovi). NAPOMENA: top-header:26-28 ima `+381 XXX XXX XXX` servis-telefon HARDKODERAN placeholder (IMP-4 marker, SiteSettings Story 3-4 zamenjuje) — kontakt strana koristi ISTI placeholder za servis-telefon (konzistentno; OQ-4 realni servis-telefon biznis input).

**Kontakt-info sadržaj + radno vreme — HARDCODED-TRANSLATABLE (SM-D5 — mirror Story 3-2 SM-D5):** `SiteSettings` model (adrese, phone_sales, phone_service, email, working_hours, social) je Story 3-4 (epics.md:748-759; sprint-status backlog — dolazi POSLE ove story). **Lock (SM-D5):** sav kontakt sadržaj „Kontakt" strane je u v1 hardcoded-translatable (kroz `{% translate %}` / `{% blocktranslate %}`):
- **Adresa:** **„Vojvođanska 1, Basaid, Srbija" sa PUNIM dijakritikama** (renderuj u `<address>` elementu). Top-header:19 + footer:48 koriste šišanu „Vojvodjanska" kroz deljeni msgid — kontakt strana NE nasleđuje taj defekt; koristi puni-dijakritik string (AC8). Popravka deljenog msgid-a = van scope-a (OQ-6 known debt).
- **Telefon prodaje:** `+381 230 468 168` (`tel:+381230468168` — ISTI kao top-header:21-23 + footer:45).
- **Telefon servisa:** placeholder `+381 XXX XXX XXX` (`tel:+381000000000` — ISTI placeholder kao top-header:26-28; OQ-4 realni broj = biznis input, SiteSettings Story 3-4).
- **Email:** `prodaja@coricagrar.rs` (`mailto:` — ISTI kao footer:46).
- **Radno vreme:** hardcoded-translatable (npr. „Ponedeljak–Petak: 08–16h, Subota: 08–13h, Nedelja: zatvoreno" — placeholder; OQ-4 realno radno vreme biznis input). Renderuj semantički (npr. `<dl>` ili `<table>` ili `<ul>` — Dev bira; čitljiv AT-u).
- **Social linkovi:** Facebook + Instagram (`href="#"` placeholder — ISTI kao footer:52/57; realni URL-ovi = biznis/SiteSettings; OQ-4). Social ikone REUSE inline SVG iz footer-a (Facebook/Instagram path-ovi) ILI prost tekstualni link — Dev bira; `aria-label` na svakom.

Kada Story 3-4 (SiteSettings) stigne, sadržaj prelazi na `{% site_setting "phone_sales" %}` template tag (epics.md:757-758; NE blokira ovu story; forward-compat — view/template grana ostaje, samo izvor podataka se menja). NE fake SiteSettings model, NE migracija. Vidi SM-D5 + OQ-1/OQ-4.

**Google Maps iframe embed — static, NULA JS (SM-D6 — KRITIČNA, third-party + CSP forward-compat):** epics.md:744-745 + FR-5 (prd.md:192) + architecture.md:786 zahtevaju „ugrađen Google Maps iframe sa pin-om … embed bez JS dep-a … inline iframe". **Lock (SM-D6):**
- Mapa je **static `<iframe>`** embed (Google Maps Embed iframe), NULA JavaScript-a, NULA Maps JS API-ja, NULA external lib-a (architecture.md:786 „Static embed, no JS dep").
- **Embed pristup (LOCK — literal placeholder `src`, NEMA env-var):** Google Maps Embed iframe (`https://www.google.com/maps/embed?pb=...` standardni „Share → Embed a map" iframe — NE zahteva obavezno API ključ za prost Embed iframe; epics.md:745 pominje „env-var API key", ali standardni Maps **Embed** iframe radi i bez ključa za prost place/pin embed). **Lock:** v1 koristi LITERALNI placeholder Google Maps Embed `src` direktno u template-u (`<iframe src="https://www.google.com/maps/embed?pb=...Basaid...">`), **BEZ env-var** (`GOOGLE_MAPS_EMBED_URL` ili sličan settings/context var) — YAGNI (project-context.md § Code organization: „nemoj graditi za hipotetičke buduće potrebe"). Prost Embed iframe ne traži API ključ, pa nema secret koji bi opravdao env-var. Dev NE hardkoduje API ključ (prost Embed ga ne koristi). Realne koordinate/finalni URL su biznis input (OQ-3); KADA biznis isporuči keyed/branded URL ili tačan pin, tek tada (ako bude tajna/rotacija) razmotriti env-var — NE u v1. v1: literalni placeholder `src` ka Basaid lokaciji.
- **A11y (KRITIČNO):** `<iframe>` MORA imati `title` atribut (npr. `title="{% translate 'Mapa lokacije Ćorić Agrar' %}"` — WCAG 2.1 AA, NVDA čita title kao accessible naziv frame-a; bez title-a iframe je nedostupan). `loading="lazy"` (ispod fold-a; performance). `referrerpolicy="no-referrer-when-downgrade"` (standardni Google embed atribut). Responsive aspect-ratio wrapper (CSS `aspect-ratio` ILI padding-bottom trik — NE fiksna visina koja lomi mobile).
- **FALLBACK kada iframe nije dostupan (C2 — KRITIČNO):** unutar map wrapper-a, PORED `<iframe>`, render-uj vidljiv tekstualni fallback (čist HTML/CSS, NULA JS) za slučaj da iframe ne radi (privacy/tracker blocker, mreža/firewall, buduća CSP). Fallback = prevodiva adresa lokacije sa punim dijakritikama („Vojvođanska 1, Basaid, Srbija") + `<a rel="noopener noreferrer" target="_blank" href="https://maps.google.com/?q=...">` sa OPISNIM prevodivim tekstom linka („Otvori lokaciju u Google Mapama") — accessible (link ima jasan naziv, NE goli URL). Tako korisnik uvek ima put do lokacije čak i bez iframe-a.
- **CSP forward-compat (django-csp):** `django-csp >= 4.0` JE dependency (pyproject.toml:11; project-context.md:39), ALI CSP JOŠ NIJE konfigurisan u settings — **verifikovano live: NEMA `csp.middleware.CSPMiddleware` u `MIDDLEWARE` (config/settings/base.py:53) i NEMA `CONTENT_SECURITY_POLICY`/`CSP_*` direktiva NIGDE u settings.** Posledica: iframe embed RADI danas bez ikakve CSP izmene (nema enforced CSP koji bi blokirao `frame-src`). **X-Frame-Options (VAŽNO za Epic-9 autora — ne meša se sa našim embedom):** `django.middleware.clickjacking.XFrameOptionsMiddleware` JE aktivan i `X_FRAME_OPTIONS=DENY` važi u produkciji, ALI ta direktiva reguliše da li DRUGI smeju da uokvire (frame) OVAJ sajt — ona NE blokira NAŠE ugrađivanje Google Mapa (`X-Frame-Options` je response-header na našem dokumentu, ne ograničenje za naše outbound `<iframe>` izvore). Zato mapa renderuje danas; budući hardening surface za naš embed je ISKLJUČIVO CSP `frame-src`/`img-src` (NE X-Frame-Options). **Lock:** ova story NE konfiguriše CSP (van scope-a — CSP hardening je Epic 9 / dedikovana security story). ALI Dev MORA dokumentovati u Completion Notes + ova story OQ-3 da KADA CSP bude uveden, MORAJU se dodati direktive: `frame-src https://www.google.com` (za Maps Embed iframe) i `img-src` mora dozvoliti Google tile domene (npr. `https://*.google.com https://*.googleapis.com https://*.gstatic.com`) — inače mapa puca pod CSP. Ovo je forward-compat napomena, NE deliverable ove story. Vidi SM-D6 + OQ-3.

**Kontakt forma — FORWARD-COMPAT SKELET sa CSRF, BEZ funkcionalnog submit-a (SM-D8 — mirror SM-D4):** **Lock (SM-D8):**
- `<form>` markup sa poljima: **Ime i prezime *** (`<input type="text" required>`), **Email *** (`<input type="email" required>`), **Telefon** (`<input type="tel">`), **Poruka *** (`<textarea required>`) — 4 polja (FR-5 / epics.md:785 „imenom, emailom, telefonom, porukom").
- Svako polje ima vidljiv `<label for="...">` (NE samo placeholder — project-context.md a11y NFR-2 „vidljive labele"; WCAG). `required` polja označena vizuelno + `aria-required="true"`.
- **`{% csrf_token %}` PRISUTAN** unutar `<form>` (project-context.md § Security #1; AC6) — iako submit nije funkcionalan, token je u markup-u da Story 4.2 samo aktivira submit.
- **Submit dugme: `disabled` + `aria-disabled="true"`** + vidljiv hint (npr. mali tekst ispod „Forma će uskoro biti aktivna" ILI dugme tekst „Pošalji upit" sa disabled stanjem) + KANONSKI TODO marker: `{# TODO Story 4.2 (Epic 4): wire funkcionalan ContactForm + {% csrf_token %} + hx-post="/htmx/forme/kontakt/" + django-ratelimit + uspeh/greška HTMX pattern (Story 4.6 aria-live OOB). Ukloni disabled/aria-disabled sa submit dugmeta. #}`.
- **`<form>` MORA postaviti `method="post"` (BEZ `action`) — C1:** skelet je `<form method="post" data-testid="contact-form">` sa EKSPLICITNIM `method="post"` i BEZ `action` atributa. RAZLOG (C1): `<form>` bez `method` default-uje na GET → slučajan Enter-keypress bi submit-ovao polja kao URL query params (`/sr/kontakt/?name=...`), curi unos u URL/history (loš UX/privacy). `method="post"` bez `action` šalje POST na ISTU `/sr/kontakt/` putanju koja je GET-only (`http_method_names` bez `post`) → čist **HTTP 405**, BEZ podataka u URL-u.
- **Forma NEMA funkcionalan submit endpoint u v1** — NEMA `hx-post`, NEMA `action` atributa koji rezolvuje na funkcionalan handler (jer `/htmx/forme/kontakt/` endpoint + `ContactForm` su Story 4.2). **`ContactView` je GET-only** (`http_method_names = ["get", "head", "options"]`) — NE prima POST (NE dodavati `post()` metod; preuranjen submit → 405). Story 4.2 samo dodaje `hx-post="/htmx/forme/kontakt/"` na ISTI `<form method="post">` (bez restrukturiranja).
- `data-testid="contact-form"` na `<form>` + `data-testid="contact-submit"` na dugmetu (regresijski selektori za TEA + Story 4.2 wire verifikaciju).
- Mirror 3-2 placeholder-CTA obrazac (forward-compat skelet, NE fake funkcionalnost). Vidi SM-D8.

**Princip:** Pure server-side GET render, **NEMA HTMX**, **NEMA funkcionalne forme**, **NEMA Lead modela**, **NEMA SMTP**, **NEMA `apps/forms` app-a**, **NEMA admin promena**, **NEMA migracije**, **NEMA modela** (`apps/pages` ostaje bez modela do Story 3-4 SiteSettings; čista statička strana). **0 novih JS modula** (mapa je static iframe; forma je skelet). JEDNA nova CSS komponenta (`contact-page.css`). Static Google Maps iframe (third-party embed, NULA JS dep, a11y `title`, CSP forward-compat OQ-3). CSS BEM sa `coric-` prefiksom + isključivo `var(--token)`. Sve user-facing string-ove kroz `{% translate %}` / `{% blocktranslate %}`. Slug ASCII (`kontakt`); pune dijakritike (č/ć/ž/š/đ) u svemu renderovanom.

**Strukturna arhitektura — repository delta:** **5 NEW fizičkih fajlova + 4 EDIT + 0 DELETE + 0 migracija + 0 modela + 0 novih JS.**

| Path | Tip | Razlog |
|---|---|---|
| `apps/pages/views.py` | EDIT | DODAJ `class ContactView(TemplateView)` (`template_name = "pages/contact.html"`; opcioni `get_context_data()` sa hardcoded kontakt-info literalima — SM-D1/SM-D5). NE menjaj `HomeView`/`AboutView`. NE importuj domain modele. NE dodavati `post()` (GET-only — SM-D4). |
| `apps/pages/urls.py` | EDIT | DODAJ `path("kontakt/", ContactView.as_view(), name="contact")` u POSTOJEĆI `urlpatterns` (POSLE about path); import `ContactView`. → `pages:contact`. |
| `templates/pages/contact.html` | NOVO | Glavni template — `{% extends "base.html" %}`; `{% block title %}`, `{% block meta_description %}`, `{% block content %}` koji uključuje 3 bloka NORMATIVNIM reading-order-om (SM-D9 lock): `_contact_info` → `_contact_form` → `_contact_map` (info → forma → mapa; vizuelni 2-kolone/stack layout je CSS izbor, NE menja `{% include %}` redosled). Single `<main>` iz base.html. JEDAN `<h1>`. Svaka sekcija `<section>` sa aria landmark. NEMA `{% block scripts %}` dodatka (0 JS). |
| `templates/pages/partials/_contact_info.html` | NOVO | Kontakt-info sekcija — Section Eyebrow + h2 + adresa (`<address>`, PUNI-dijakritik „Vojvođanska") + telefon prodaja (`tel:`) + telefon servisa (`tel:` placeholder) + email (`mailto:`) + radno vreme (semantički `<dl>`/`<ul>`) + social linkovi (Facebook/Instagram, `aria-label`). Sve hardcoded-translatable (SM-D5). REUSE iste vrednosti kao top-header/footer (osim adrese). MORA sadržati grep-abilni IMP marker komentar `{# IMP-SiteSettings(Story 3-4): zameni hardkodovane kontakt vrednosti {% site_setting %} tagom kad 3-4 stigne #}` (mirror top-header IMP-4 pattern). |
| `templates/pages/partials/_contact_map.html` | NOVO | Google Maps iframe — `<section>` aria landmark + Section Eyebrow + h2 + responsive aspect-ratio wrapper sa static `<iframe>` (Maps Embed `src`, `title` translatable, `loading="lazy"`, `referrerpolicy`) + tekstualni fallback (adresa + opisni `<a rel="noopener noreferrer" target="_blank">` ka Google Mapama kad iframe blokiran — C2). NULA JS (SM-D6). CSP forward-compat komentar (OQ-3). |
| `templates/pages/partials/_contact_form.html` | NOVO | Forward-compat skelet forme — `<section>` aria landmark + Section Eyebrow + h2 + `<form method="post" aria-describedby="contact-form-hint" data-testid="contact-form">` (EKSPLICITNO `method="post"`, BEZ `action` — C1) sa 4 polja (Ime*/Email*/Telefon/Poruka*) — **sva polja `disabled` u v1 (a11y silent-data-loss guard)** — + vidljive `<label>` + `{% csrf_token %}` + `disabled aria-disabled` submit dugme (`coric-button coric-button--primary`, `data-testid="contact-submit"`) + vizuelno istaknut „uskoro aktivna" hint (`id="contact-form-hint"`, `aria-describedby` target; usmerava na tel/e-poštu) + KANONSKI TODO Story 4.2 marker (SM-D8). NEMA funkcionalan submit. |
| `static/css/components/contact-page.css` | NOVO | `coric-contact` (wrapper layout), `coric-contact-info`, `coric-contact-map` (responsive aspect-ratio iframe wrapper), `coric-contact-form` BEM. Sve `var(--token)`. JEDINA nova CSS komponenta. Responsive: mobile stack → desktop 2-kolone info+forma (SM-D9). |
| `static/css/main.css` | EDIT | DODAJ TAČNO 1 `@import url('./components/contact-page.css');` POSLE poslednje `@import` linije (`about-page.css`, Story 3-2 — verifikovano live `main.css:50`). |
| `templates/partials/header.html` | EDIT | SM-D3: `:96` „Kontakt" nav link — `href="#"` → `href="{% url 'pages:contact' %}"` (NAV bez aktivno-stranica pattern-a — `aria-current` OPCIONO/van scope-a, verifikovano live). |
| `locale/sr/LC_MESSAGES/django.po`, `locale/hu/LC_MESSAGES/django.po`, `locale/en/LC_MESSAGES/django.po` | EDIT (×3) | Popuni msgstr za nove msgid (page title + meta description, eyebrow tekstovi, h2 naslovi, radno vreme labela/vrednosti, form labele/placeholder/hint, iframe title, social aria-label-i, „uskoro aktivna" hint). Pune dijakritike. |
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | EDIT | Postavi `3-3-kontakt-strana-sa-formom-i-mapom` → `ready-for-dev`. SM handoff tracking (NIJE deliverable). |

**Brojanje (KANONSKO — single source of truth):** **5 NEW fizičkih fajlova (1 template + 3 partials + 1 CSS) + 4 logičke EDIT lokacije (views.py + urls.py + main.css + header.html) + locale ×3 EDIT + 0 migracija + 0 modela + 0 novih JS.**

Razlaganje:
- **5 NEW:** `pages/contact.html` (1) + 3 partials (`_contact_info`, `_contact_map`, `_contact_form` = 4) + `contact-page.css` (5) = **5 NEW.**
- **EDIT:** `apps/pages/views.py` (+ContactView) + `apps/pages/urls.py` (+contact path) + `static/css/main.css` (+1 @import) + `templates/partials/header.html` (SM-D3 wire) + `locale ×3` = 7 fizičkih EDIT (4 kod/template + 3 .po).
- **0 migracija** (`apps/pages` bez modela; SiteSettings = Story 3-4).
- **0 modela, 0 SMTP, 0 funkcionalne forme, 0 novih JS, 0 DELETE.**
- **0 asset-a** (mapa je remote iframe — NEMA static slike; forma/info nemaju slike).

Postojeći fajlovi koji ostaju **NETAKNUTI** (regression guards): `apps/pages/views.py` `HomeView` + `AboutView` (NE menja se — DODAJE se ContactView pored), `templates/pages/home.html` + `templates/pages/about.html` + svi `_home_*`/`_about_*` partials, `templates/base.html` (REUSE — NE dupliraj main/header/footer/aria-live; NE dodavati JS), `templates/partials/footer.html` (NE diraj — footer NEMA „Kontakt" nav link; SM-D3b), `templates/partials/header.html` SAMO `:96` „Kontakt" link se menja (ostalo NETAKNUTO — `:71` „Početna" već fiksiran u 3-2), `static/css/tokens.css`, sve `apps/brands/`+`apps/products/`+`apps/core/`+`apps/search/` (NETAKNUTI — kontakt strana ne dira domain), sve postojeće CSS komponente (REUSE pill-button/section-eyebrow; NE dupliraj), svi postojeći JS moduli (NE diraj — 0 novog JS), `pyproject.toml` (django-csp/anymail/ratelimit VEĆ dependency — NEMA promene; CSP config je van scope-a), `config/settings/*` (apps.pages već u INSTALLED_APPS iz Story 3-1; NEMA CSP config promene — SM-D6/OQ-3), `config/urls.py` (`apps.pages.urls` već include-ovan; novi contact path je UNUTAR `apps/pages/urls.py`).

## Kriterijumi prihvatanja

**AC1 — `ContactView` u `apps/pages/`; URL `/<lang>/kontakt/` rezolvuje `pages:contact`; HTTP 200 za sva 3 locale; renderuje `templates/pages/contact.html`; GET-only (NE prima POST)**

- **Given** `apps/pages/` app postoji (Story 3-1/3-2 — `PagesConfig` + `INSTALLED_APPS` + `apps/pages/urls.py` `app_name="pages"` + `path("", HomeView...)` + `path("o-nama/", AboutView...)`); `i18n_patterns()` aktivan (Story 1-4); `config/urls.py` include-uje `apps.pages.urls`
- **When** dodam `class ContactView(TemplateView)` (`template_name = "pages/contact.html"`; `http_method_names = ["get", "head", "options"]`) u `apps/pages/views.py` i `path("kontakt/", ContactView.as_view(), name="contact")` u `apps/pages/urls.py`
- **Then**:
  - `reverse("pages:contact")` → `/sr/kontakt/` (analogno `/hu/kontakt/`, `/en/kontakt/`)
  - GET `/sr/kontakt/` → HTTP 200; GET `/hu/kontakt/` → 200; GET `/en/kontakt/` → 200
  - Renderovani template je `pages/contact.html` — `assertTemplateUsed(response, "pages/contact.html")`
  - `ContactView` je CBV (`ContactView.as_view()` u urls.py); **GET-only DETERMINISTIČKI**: klasa MORA postaviti `http_method_names = ["get", "head", "options"]` (eksplicitno izostavlja `post`/`put`/`patch`/`delete`). Django `TemplateView` (preko `View.dispatch`) vraća **HTTP 405 Method Not Allowed** za svaki metod koji NIJE u `http_method_names` — dakle POST `/sr/kontakt/` → 405 (deterministički, NE 200; forma je skelet, SM-D4/SM-D1/C3). NE dodavati `post()` metod
  - `HomeView`/`pages:home` + `AboutView`/`pages:about` NETAKNUTI (regresija — GET `/sr/` i `/sr/o-nama/` i dalje 200)
  - `uv run python manage.py check` exit 0
- **And** smoke verifikacija:
  ```bash
  uv run python manage.py shell -c "from django.urls import reverse; \
    from django.utils.translation import activate; activate('sr'); \
    print(reverse('pages:contact'))"
  ```
  Očekivan output: `/sr/kontakt/`

**AC2 — header „Kontakt" nav placeholder RAZREŠEN: `header.html:96` WIRE-ovan na `pages:contact` (SM-D3)**

- **Given** AC1 (`pages:contact` postoji); `header.html:96` „Kontakt" nav link `href="#"` (mrtav placeholder iz Story 1-8)
- **When** wire-ujem na `pages:contact`
- **Then**:
  - `header.html:96`: „Kontakt" nav link je `<a class="nav-link coric-nav__link" href="{% url 'pages:contact' %}">{% translate "Kontakt" %}</a>` (NE `href="#"`)
  - Klik na header „Kontakt" → `/sr/kontakt/` (HTTP 200)
  - NAV nema `aria-current`/active markup (verifikovano live — `aria-current` OPCIONO/van scope-a; SAMO wire URL)
- **And** footer NIJE menjan (SM-D3b — footer nema „Kontakt" NAV link; kontakt info blok + social `href="#"` placeholder-i su van scope-a ove story)
- **And** regresijski smoke — header „Kontakt" više nema `href="#"`:
  ```powershell
  Select-String -Pattern 'pages:contact' -Path templates/partials/header.html
  ```
  Očekivano: ≥1 rezultat (link wire-ovan)

**AC3 — `templates/pages/contact.html`: 3 bloka (kontakt-info + mapa + forma-skelet); JEDAN h1; single main (iz base.html); semantic HTML5 + ARIA landmarks; NEMA `{% block scripts %}` dodatka (0 JS)**

- **Given** AC1; base.html (Story 1-6 — `{% block content %}`, single `<main>`, header, footer, aria-live)
- **When** kreiram `contact.html` + 3 section partials
- **Then** `contact.html` MORA imati strukturu:
  ```django
  {% extends "base.html" %}
  {% load i18n static %}

  {% block title %}{% translate "Kontakt — Ćorić Agrar" %}{% endblock %}

  {% block meta_description %}{% translate "Kontaktirajte Ćorić Agrar — adresa, telefoni prodaje i servisa, email, radno vreme i lokacija na mapi. Pošaljite nam upit." %}{% endblock %}

  {% block content %}
    {% include "pages/partials/_contact_info.html" %}
    {% include "pages/partials/_contact_form.html" %}
    {% include "pages/partials/_contact_map.html" %}
  {% endblock content %}
  ```
- **NAPOMENA (skeleton COPY je REFERENCA; redosled `{% include %}` je NORMATIVAN):** tačan tekst `meta_description`/`title` je PRIMER copy-ja — obavezujući zahtev je da string PROLAZI kroz `{% translate %}` (ne tačan literal). TEA NE piše brittle literal string-match test; testira da `<meta name="description">` postoji + neprazan/translatable. ALI redosled `{% include %}` — **info → forma → mapa** — JESTE obavezujući semantički reading-order (vidi „redosled blokova" ispod).
- **Then** redosled blokova (NORMATIVAN — semantički reading order **info → forma → mapa**, mirror EXPERIENCE.md:100 „Info + forma + Google Maps"): DOM/`{% include %}` redosled MORA biti `_contact_info` → `_contact_form` → `_contact_map`. VIZUELNI layout (CSS) sme da postavi info+formu side-by-side (2-kolone desktop) ili stack — to je Dev/Step-02/SM-D9 izbor — ALI source/reading order ostaje info→forma→mapa (a11y/SEO determinizam). TEA testira: sva 3 bloka prisutna + taj redosled u DOM-u (NE proverava CSS layout). Footer iz base.html (NE dupliraj)
- **And** semantic HTML5:
  - TAČNO 1 `<h1>` (page title — npr. „Kontakt" / „Kontaktirajte nas"; vidi SM-D10)
  - Svaki od 3 blokova je `<section>` sa `aria-labelledby` (referencira lokalni h2 id) ILI `aria-label`
  - h2 po bloku (Kontakt info / Lokacija / Pošaljite upit) → eventualni h3 za pod-elemente
  - Heading hijerarhija h1 → h2 (→ h3) (NEMA preskoka)
  - **Single `<main>`** (iz base.html — `contact.html` NE dodaje drugi `<main>`)
- **And** `contact.html` NE dodaje `{% block scripts %}` (0 novog JS — SM-D7; mapa je static iframe, forma je skelet)
- **And** `<html lang="{{ LANGUAGE_CODE }}">` automatski (base.html, Story 1-4)
- **And** NEMA hardcoded srpski (sve `{% translate %}`); NEMA ćirilice; pune dijakritike

**AC4 — Kontakt-info sekcija: adresa + telefon prodaja + telefon servisa + email + radno vreme + social linkovi; hardcoded-translatable (SM-D5); REUSE iste vrednosti kao top-header/footer; semantic + a11y**

- **Given** AC3; `section_eyebrow.html` (Story 1-7); SM-D5 (hardcoded-translatable, forward-compat SiteSettings Story 3-4); top-header/footer kontakt vrednosti (REUSE referenca)
- **When** kreiram `templates/pages/partials/_contact_info.html`
- **Then** sekcija MORA:
  - `<section aria-labelledby="contact-info-title">` + Section Eyebrow + `<h2 id="contact-info-title">`
  - **Adresa** u `<address>` elementu: **„Vojvođanska 1, Basaid, Srbija" sa PUNIM dijakritikama** (`{% translate %}`; AC8 zahteva pune dijakritike na ovoj NOVOJ strani). NAPOMENA (nasleđeni dug): top-header:19/footer:48 koriste šišanu latinicu „Vojvodjanska" kroz deljeni msgid — kontakt strana NE sme da nasledi taj defekt. Kontakt strana koristi PUNI-dijakritik msgid „Vojvođanska 1, Basaid, Srbija" za SVOJ rendered string (NE reuse šišanog msgid-a). Popravka samog deljenog top-header/footer msgid-a je VAN scope-a ove story (vidi OQ-6 — known debt)
  - **Telefon prodaje** kao `<a href="tel:+381230468168">+381 230 468 168</a>` (ISTI kao top-header:21-23/footer:45) sa `aria-label` (npr. „Telefon prodaje")
  - **Telefon servisa** kao `<a href="tel:+381000000000">` placeholder `+381 XXX XXX XXX` (ISTI placeholder kao top-header:26-28; OQ-4 realni broj) sa `aria-label` „Telefon servisa"
  - **Email** kao `<a href="mailto:prodaja@coricagrar.rs">prodaja@coricagrar.rs</a>` (ISTI kao footer:46)
  - **Radno vreme** semantički (npr. `<dl>` ili `<ul>` — Dev bira; čitljiv AT-u) hardcoded-translatable placeholder (OQ-4 realno radno vreme)
  - **Social linkovi** (Facebook + Instagram) sa **translatable `aria-label`** na svakom `<a>` (`{% translate "Facebook" %}` / `{% translate "Instagram" %}` — moraju u msgid listu, AC8) (`href="#"` placeholder — OQ-4 realni URL-ovi); ikone REUSE inline SVG iz footer-a ILI tekstualni link (Dev bira; ako inline SVG ikona → `aria-hidden="true"` na SVG-u, a accessible naziv nosi `aria-label` na `<a>`)
- **And** sve vrednosti hardcoded-translatable kroz `{% translate %}` (forward-compat ka SiteSettings Story 3-4 — SM-D5)
- **And** `_contact_info.html` sadrži grep-abilni forward-compat IMP marker komentar `{# IMP-SiteSettings(Story 3-4): zameni hardkodovane kontakt vrednosti {% site_setting %} tagom kad 3-4 stigne #}` (mirror top-header IMP-4 pattern; machine-findable obaveza za Story 3-4)
- **And** prodaja/servis telefoni vizuelno/semantički razdvojeni (FR-5 „telefoni prodaja+servis odvojeno")

**AC5 — Google Maps iframe: static embed sa pin-om lokacije, NULA JS; `title` atribut (a11y); `loading="lazy"`; responsive aspect-ratio wrapper; CSP forward-compat dokumentovan (SM-D6)**

- **Given** AC3; architecture.md:786 („inline iframe, no JS dep"); epics.md:745 („embed bez JS dep-a"); FR-5 (prd.md:192); SM-D6 (CSP forward-compat)
- **When** kreiram `templates/pages/partials/_contact_map.html`
- **Then** mapa MORA:
  - `<section aria-labelledby="contact-map-title">` + Section Eyebrow + `<h2 id="contact-map-title">`
  - Static `<iframe>` Google Maps Embed sa LITERALNIM placeholder `src` direktno u template-u (`https://www.google.com/maps/embed?pb=...Basaid...`) — **BEZ env-var** (YAGNI; prost Embed nema secret; SM-D6/OQ-3); OQ-3 finalna lokacija/koordinate biznis sign-off — NULA JavaScript-a, NULA Maps JS API
  - `<iframe>` ima **`title` atribut** translatable (npr. `title="{% translate 'Mapa lokacije Ćorić Agrar' %}"` — WCAG 2.1 AA accessible naziv; KRITIČNO — bez title-a iframe nedostupan)
  - `loading="lazy"` (ispod fold-a; performance)
  - `referrerpolicy="no-referrer-when-downgrade"` (standardni Google embed atribut)
  - Responsive aspect-ratio wrapper (CSS `aspect-ratio` ILI padding-bottom — NE fiksna visina koja lomi mobile)
  - **FALLBACK kada iframe NE uspe da se učita (C2 — KRITIČNO):** unutar map wrapper-a, PORED `<iframe>`, MORA postojati vidljiv tekstualni fallback (čist HTML/CSS, NULA JS) za slučaj da iframe ne radi (privacy/tracker blocker, mreža/firewall, ili buduća CSP koja blokira `frame-src`). Fallback sadrži: (a) adresu lokacije kao prevodiv tekst sa punim dijakritikama — npr. „Vojvođanska 1, Basaid, Srbija" (NAPOMENA: ova fallback adresa koristi pune dijakritike „Vojvođanska", NE „Vojvodjanska"); (b) `<a rel="noopener noreferrer" target="_blank">` link ka Google Maps lokaciji (npr. `href="https://maps.google.com/?q=..."`) sa OPISNIM prevodivim tekstom linka (npr. „Otvori lokaciju u Google Mapama" — NE goli URL; pristupačno AT-u jer link ima jasan accessible naziv). Fallback je uvek u DOM-u (vidljiv ili pozicioniran tako da korisnik ima alternativu i kad iframe ne renderuje) — NE zavisi od JS detekcije
- **And** NULA novog JS (mapa je čist static iframe + statički HTML/CSS fallback — SM-D6/SM-D7)
- **And** CSP forward-compat: template ima grep-abilan komentar sa KANONSKIM prefiksom `CSP-NOTE(Epic 9)` koji dokumentuje da KADA django-csp bude konfigurisan (Epic 9 hardening), MORA se dodati `frame-src https://www.google.com` + `img-src` Google tile domeni — npr. `{# CSP-NOTE(Epic 9): when django-csp enabled, add frame-src https://www.google.com + img-src *.google.com *.gstatic.com *.googleapis.com #}` (OQ-3); v1 NEMA CSP enforced (verifikovano live — NEMA CSPMiddleware/direktiva), pa iframe radi bez izmene settings-a (NAPOMENA: X-Frame-Options NE ulazi u ovaj surface — vidi SM-D6/OQ-3)
- **And** v1 koristi LITERALNI placeholder Embed `src` u template-u, BEZ env-var (YAGNI — SM-D6); Dev NE hardkoduje API ključ (prost Embed iframe ga ne koristi); keyed/branded URL ili env-var razmatra se TEK kad biznis isporuči takav URL (OQ-3), NE u v1

**AC6 — Kontakt forma SKELET: 4 polja (Ime*/Email*/Telefon/Poruka*) sa vidljivim `<label>` + `{% csrf_token %}` PRISUTAN + submit dugme `disabled`/`aria-disabled` (forward-compat) + KANONSKI TODO Story 4.2 marker; NEMA funkcionalan submit (SM-D8/SM-D4)**

- **Given** AC3; `coric-button` (Story 1-7 pill-button.css); SM-D8 (forward-compat skelet); SM-D4 (funkcionalna forma = Epic 4 Story 4.2/4.6); project-context.md § Security #1 (CSRF na svim formama)
- **When** kreiram `templates/pages/partials/_contact_form.html`
- **Then** forma MORA:
  - `<section aria-labelledby="contact-form-title">` + Section Eyebrow + `<h2 id="contact-form-title">`
  - `<form method="post" data-testid="contact-form">` — forma MORA EKSPLICITNO postaviti `method="post"` i NE SME imati `action` atribut (C1). RAZLOG: `<form>` bez `method` default-uje na GET, pa bi slučajan Enter-keypress submit-ovao vrednosti polja kao URL query params (`/sr/kontakt/?name=...&email=...`) — curi korisnički unos u URL/history i pravi zbunjujući UX. Sa `method="post"` (bez `action`, dakle submit ide na ISTU `/sr/kontakt/` putanju) svaki preuranjen submit pogađa GET-only `ContactView` → čist **HTTP 405** (C3 `http_method_names`), BEZ podataka u URL-u. Epic 4 (Story 4.2) samo dodaje `hx-post="/htmx/forme/kontakt/"` na ovaj isti `<form>` — `method="post"` ostaje (nema restrukturiranja markup-a)
  - 4 polja — **SVA polja su `disabled` u v1 (a11y — sprečava silent-data-loss):** korisnik NE sme da uloži trud kucajući u nefunkcionalnu formu, pa su i input/textarea polja `disabled` (NE samo submit dugme). `disabled` polja su izvan tab-reda → keyboard/screen-reader korisnik ne ulazi u „prazninu" bez izlaza. `required`/`aria-required="true"` se ZADRŽAVA kao forward-compat markup (Story 4.2 uklanja `disabled`, validacija postaje aktivna):
    - **Ime i prezime *** — `<input type="text" required aria-required="true" disabled>` + vidljiv `<label for="...">`
    - **Email *** — `<input type="email" required aria-required="true" disabled>` + vidljiv `<label>`
    - **Telefon** — `<input type="tel" disabled>` + vidljiv `<label>` (opciono polje)
    - **Poruka *** — `<textarea required aria-required="true" disabled>` + vidljiv `<label>`
  - **`{% csrf_token %}` PRISUTAN** unutar `<form>` (project-context.md § Security #1; iako submit nije funkcionalan — Story 4.2 ga aktivira)
  - **Hint je programski povezan sa formom (`aria-describedby` — a11y):** hint element ima `id` (npr. `id="contact-form-hint"`) i `<form>` ga referencira preko `aria-describedby="contact-form-hint"` tako da AT objavljuje status forme. Hint je **vizuelno istaknut** (NE sitna caption — npr. obojen alert/notice blok iznad ili na vrhu forme, čitljiv kontrast ≥ 4.5:1), i copy AKTIVNO preusmerava na funkcionalne kanale: „Forma će uskoro biti dostupna. Do tada nas kontaktirajte telefonom ili e-poštom." (translatable; usmerava na tel/email iz kontakt-info sekcije).
  - **Submit dugme `disabled` + `aria-disabled="true"`**: `<button type="submit" class="coric-button coric-button--primary" data-testid="contact-submit" disabled aria-disabled="true">{% translate "Pošalji upit" %}</button>`
  - KANONSKI TODO marker: `{# TODO Story 4.2 (Epic 4): wire funkcionalan ContactForm + hx-post="/htmx/forme/kontakt/" + django-ratelimit (10/15m IP) + uspeh/greška HTMX pattern (Story 4.6 aria-live OOB). Ukloni disabled/aria-disabled sa #contact-submit. #}`
  - `data-testid="contact-form"` na `<form>` + `data-testid="contact-submit"` na dugmetu (regresijski selektori)
- **And** forma NEMA funkcionalan submit u v1: NEMA `hx-post`, NEMA `action` atributa (forma ima `method="post"` ALI bez `action` → submit ide na ISTU `/sr/kontakt/` putanju koja je GET-only → 405; HTMX endpoint `/htmx/forme/kontakt/` + `ContactForm` su Story 4.2); `ContactView` je GET-only sa `http_method_names = ["get", "head", "options"]` (NEMA `post()` — SM-D4/SM-D1/C1/C3)
- **And** svaki `<label>` je VIDLJIV (NE samo placeholder — NFR-2 a11y vidljive labele); `required` polja vizuelno označena (npr. `*`) + `aria-required="true"`
- **And** smoke — CSRF token prisutan u form skeletu:
  ```powershell
  Select-String -Pattern 'csrf' -Path templates/pages/partials/_contact_form.html
  ```
  Očekivano: ≥1 rezultat (`{% csrf_token %}` prisutan)

**AC7 — `contact-page.css`: BEM `coric-` prefiks; responsive (mobile stack → desktop 2-kolone); SVE vrednosti kroz `var(--token)`; map iframe responsive aspect-ratio; uvezen u main.css**

- **Given** AC4-AC6; `tokens.css` (Story 1-5); main.css (Story 3-2 zadnji @import `about-page.css` — verifikovano live `main.css:50`)
- **When** kreiram `static/css/components/contact-page.css` + EDIT main.css
- **Then**:
  - BEM blokovi: `coric-contact` (wrapper), `coric-contact-info`, `coric-contact-map`, `coric-contact-form` (+ `__element` / `--modifier`); SVE klase `coric-` prefiks
  - Responsive: info+forma 2-kolone desktop / stack mobile (`@media (min-width: 768px)`); mapa iframe responsive aspect-ratio (NE fiksna visina); touch mete ≥ 44px (tel/email/social linkovi — DESIGN.md:255)
  - SVE boje/spacing/radius kroz `var(--token)` (NEMA magic hex/px osim whitelist: `transparent`/`none`/`0`/`100%` + dozvoljeni `%`/`vh`/`px`/`fr`/`aspect-ratio` vrednosti za layout dimenzije bez token-a — mirror Story 3-2 AC8 test toleranca; map aspect-ratio npr. `16 / 9` je layout vrednost, dozvoljena)
  - Map wrapper: `aspect-ratio` (npr. `16 / 9`) + `iframe { width: 100%; height: 100%; border: 0; }` — responsive bez JS
  - Forma polja: vidljiv fokus outline (`:focus-visible` `var(--color-semantic-focus-ring)`); disabled dugme/polja vizuelno prigušeno (`opacity` kroz token/whitelist) + `cursor: not-allowed`
  - **Ako se doda bilo koji CSS `transition`** (npr. na focus outline / hover): MORA biti zaštićen `@media (prefers-reduced-motion: reduce)` guardom (project-context.md § A11y #7) — npr. `@media (prefers-reduced-motion: reduce) { * { transition: none; } }` ili per-selektor. Default: strana NEMA animacija (0 JS) — guard je potreban SAMO ako Dev uvede transition
- **And** EDIT main.css: +1 `@import url('./components/contact-page.css');` POSLE `about-page.css` (`main.css:50`)
- **And** NEMA CDN; NEMA dupliranja postojećih komponenti (REUSE pill-button/section-eyebrow CSS)

**AC8 — i18n: sve user-facing string kroz `{% translate %}`/`{% blocktranslate %}`; .po fajlovi (sr/hu/en) popunjeni; pune dijakritike; NEMA ćirilice; strana se renderuje na sva 3 locale**

- **Given** AC1-AC7; postojeći `locale/{sr,hu,en}/LC_MESSAGES/django.po`
- **When** dodam nove msgid + `makemessages` + popunim msgstr + `compilemessages`
- **Then**:
  - SVI novi user-facing string-ovi kroz `{% translate %}` / `{% blocktranslate %}` (page title, meta description, eyebrow tekstovi „KONTAKTIRAJTE NAS"/„NAŠA LOKACIJA"/„POŠALJITE UPIT", h2 naslovi, „Telefon prodaje"/„Telefon servisa" aria-label-i, radno vreme labela+vrednosti, email/adresa, form labele (Ime i prezime/Email/Telefon/Poruka) + submit dugme tekst + „uskoro aktivna" hint, iframe `title`, social aria-label-i). NAPOMENA: telefonski brojevi/email adresa kao VREDNOSTI (`+381...`, `prodaja@...`) NISU prevodive (NE u `{% translate %}`); SAMO labele/aria-label-i se prevode
  - `locale/sr/` msgstr popunjen za SVE nove msgid (pune dijakritike č/ć/ž/š/đ; NEMA ćirilice; NEMA šišane latinice)
  - `locale/hu/` + `locale/en/` prevodi popunjeni
  - GET `/sr/kontakt/`, `/hu/kontakt/`, `/en/kontakt/` renderuju lokalizovan sadržaj (sr primaran)
- **And** smoke — 0 empty msgstr za nove msgid (sr); NEMA ćirilice u renderovanom HTML-u
  ```powershell
  Select-String -Pattern "[Ѐ-ӿ]" -Path templates/pages/contact.html,templates/pages/partials/_contact_*.html
  ```
  Očekivano: 0 rezultata (NEMA ćirilice)

**AC9 — A11y + smoke: single h1/main; iframe `title`; vidljive form labele + CSRF; keyboard nav; reduced-motion (nasleđen); Lighthouse a11y ≥ 95**

- **Given** AC3-AC8; project-context.md a11y must-haves; NFR-2 + UX-DR-13
- **When** Dev pokrene manuelni smoke + Lighthouse
- **Then**:
  - Single h1 (page title) + single main (base.html) + svaki od 3 blokova `<section>` sa aria landmark (AC3)
  - Google Maps `<iframe>` ima `title` atribut (AC5 — NVDA čita; bez title-a iframe nedostupan)
  - **EDGE-CASE — iframe blokiran/ne učita se (C2):** map wrapper ima vidljiv fallback (adresa + opisni `<a rel="noopener noreferrer" target="_blank">` ka Google Mapama) tako da korisnik dođe do lokacije i kad iframe ne radi (privacy blocker/firewall/buduća CSP); fallback je čist HTML/CSS (NULA JS), link ima jasan accessible naziv (AC5)
  - Svako form polje ima vidljiv `<label>` + `aria-required` na obaveznim (AC6); `<form>` ima `method="post"` BEZ `action` (C1); `{% csrf_token %}` prisutan
  - Keyboard: svi tel/email/social linkovi tab-abilni; **form polja + submit dugme su `disabled` u v1 → NISU u tab-redu** (a11y — korisnik ne ulazi u nefunkcionalnu formu; status objavljen preko `aria-describedby` hint-a); fokus outline vidljiv na svim interaktivnim elementima (`:focus-visible` `var(--color-semantic-focus-ring)`)
  - Touch mete ≥ 44×44px (tel/email/social linkovi, form polja — project-context.md / DESIGN.md:255)
  - Kontrast ≥ 4.5:1 (kontakt info tekst, form labele)
  - `prefers-reduced-motion` nasleđen iz base/tokens (NEMA novih animacija na ovoj strani — 0 JS)
- **And** Lighthouse CLI (mobile profil) sa TAČNOM invokacijom (vidi Subtask 8.5: `npx lighthouse http://localhost:8000/sr/kontakt/ --only-categories=accessibility,performance --form-factor=mobile --output=json --output-path=./3-3-contact-lighthouse-sr.json --chrome-flags="--headless --no-sandbox"`) — A11y ≥ 95 + Performance ≥ 80; citiraj skor-ove iz json output-a u Completion Notes PRE review (NAPOMENA: Google Maps iframe je third-party — može uticati na Performance; `loading="lazy"` ublažava)

## Tasks / Subtasks

- [x] **Task 1: `ContactView` + URL `pages:contact` (AC1)**
  - [x] Subtask 1.1: DODAJ `class ContactView(TemplateView)` u `apps/pages/views.py` (POSLE `AboutView`): `template_name = "pages/contact.html"` + `http_method_names = ["get", "head", "options"]` (C3 — deterministički GET-only; Django `dispatch` vraća 405 za nelistovane metode kao POST). Opcioni `get_context_data()` sa hardcoded kontakt-info Python literalima (radno vreme, telefoni — SM-D5) ILI prazan (sve u template-u). NE importovati domain modele. NE dodavati `post()` metod (GET-only — SM-D4/SM-D1/C3). NE menjati `HomeView`/`AboutView`
  - [x] Subtask 1.2: DODAJ `path("kontakt/", ContactView.as_view(), name="contact")` u POSTOJEĆI `apps/pages/urls.py` `urlpatterns` (POSLE about path); import `ContactView`
  - [x] Subtask 1.3: Smoke — `manage.py check` exit 0; `reverse("pages:contact")` → `/sr/kontakt/`; GET `/sr/kontakt/`,`/hu/kontakt/`,`/en/kontakt/` → 200; `pages:home`+`pages:about` regresija (GET `/sr/` i `/sr/o-nama/` → 200)

- [x] **Task 2: RAZREŠI header „Kontakt" placeholder — wire `pages:contact` (AC2, SM-D3)**
  - [x] Subtask 2.1: EDIT `templates/partials/header.html:96`: „Kontakt" nav link `href="#"` → `href="{% url 'pages:contact' %}"` (NAV bez aktivno-stranica pattern-a — `aria-current` van scope-a; SAMO wire URL)
  - [x] Subtask 2.2: Verifikuj footer NIJE menjan (SM-D3b — footer nema „Kontakt" NAV link; social/proizvodi placeholder-i van scope-a)
  - [x] Subtask 2.3: Smoke — header „Kontakt" → `/sr/kontakt/` 200; `Select-String 'pages:contact' header.html` → ≥1 rezultat

- [x] **Task 3: `contact.html` + kontakt-info partial (AC3, AC4)**
  - [x] Subtask 3.1: Kreiraj `templates/pages/contact.html` per AC3 skeleton (`{% extends "base.html" %}` + 3 `{% include %}` + title/meta_description; NEMA `{% block scripts %}` dodatka — 0 JS)
  - [x] Subtask 3.2: Kreiraj `templates/pages/partials/_contact_info.html` per AC4 (Section Eyebrow + h2 + `<address>` PUNI-dijakritik „Vojvođanska" + tel prodaja + tel servis + email + radno vreme `<dl>`/`<ul>` + social `aria-label`; sve `{% translate %}`; REUSE top-header/footer vrednosti osim adrese — SM-D5). DODAJ grep-abilni IMP marker komentar `{# IMP-SiteSettings(Story 3-4): zameni hardkodovane kontakt vrednosti {% site_setting %} tagom kad 3-4 stigne #}` (mirror top-header IMP-4)
  - [x] Subtask 3.3: Verifikuj TAČNO 1 h1 (page title) + single main (base.html) + svaki blok `<section>` sa aria landmark + heading hijerarhija h1→h2

- [x] **Task 4: Google Maps iframe partial (AC5, SM-D6)**
  - [x] Subtask 4.1: Kreiraj `templates/pages/partials/_contact_map.html` per AC5 (Section Eyebrow + h2 + responsive aspect-ratio wrapper sa static `<iframe>` Maps Embed: `title` translatable, `loading="lazy"`, `referrerpolicy`, LITERALNI placeholder `src` ka Basaid u template-u — BEZ env-var, YAGNI; OQ-3 finalna lokacija biznis input)
  - [x] Subtask 4.2: DODAJ fallback (C2) unutar map wrapper-a PORED iframe-a (čist HTML/CSS, NULA JS): prevodiva adresa „Vojvođanska 1, Basaid, Srbija" (pune dijakritike — „Vojvođanska") + `<a rel="noopener noreferrer" target="_blank" href="https://maps.google.com/?q=...">` sa opisnim prevodivim tekstom linka („Otvori lokaciju u Google Mapama" — NE goli URL; accessible). Fallback uvek u DOM-u (radi i kad iframe blokiran: privacy blocker/firewall/buduća CSP)
  - [x] Subtask 4.3: Dodaj CSP forward-compat komentar u template sa KANONSKIM grep-abilnim prefiksom `CSP-NOTE(Epic 9)` — npr. `{# CSP-NOTE(Epic 9): when django-csp enabled, add frame-src https://www.google.com + img-src *.google.com *.gstatic.com *.googleapis.com #}`. NE konfigurisati CSP u settings (van scope-a). NAPOMENA: X-Frame-Options (XFrameOptionsMiddleware/DENY) NE blokira naš embed — NE diraj (SM-D6/OQ-3)
  - [x] Subtask 4.4: Verifikuj NULA JS (čist static iframe + statički fallback); `title` atribut prisutan; fallback link sa opisnim tekstom prisutan (C2); Dev NE hardkoduje API ključ (env-var ako treba; default čist Embed iframe)

- [x] **Task 5: Forward-compat skelet forme (AC6, SM-D8)**
  - [x] Subtask 5.1: Kreiraj `templates/pages/partials/_contact_form.html` per AC6 (Section Eyebrow + h2 + `<form method="post" data-testid="contact-form">` — EKSPLICITNO `method="post"`, BEZ `action` atributa (C1 — sprečava GET-default leak unosa u URL; preuranjen submit → 405 na GET-only ContactView) — sa 4 polja Ime*/Email*/Telefon/Poruka* + vidljive `<label>` + `aria-required` + `{% csrf_token %}` + `disabled aria-disabled` submit dugme `data-testid="contact-submit"` + „uskoro aktivna" hint + KANONSKI TODO Story 4.2 marker)
  - [x] Subtask 5.2: Verifikuj `<form>` ima `method="post"` (BEZ `action` — C1); `{% csrf_token %}` prisutan; submit `disabled`+`aria-disabled`; NEMA `hx-post`/funkcionalan `action`; ContactView ostaje GET-only (`http_method_names` bez `post`)
  - [x] Subtask 5.3: Verifikuj svaki `<label>` VIDLJIV (NE samo placeholder); `required`+`aria-required` na obaveznim poljima

- [x] **Task 6: `contact-page.css` + main.css EDIT (AC7)**
  - [x] Subtask 6.1: Kreiraj `static/css/components/contact-page.css` per AC7 (4 BEM blokova `coric-` prefiks; responsive info+forma 2-kolone/stack + map aspect-ratio wrapper; SVE `var(--token)`; disabled dugme stil; fokus outline)
  - [x] Subtask 6.2: Token verifikacija — svaki `var(--token)` postoji u tokens.css; ako nedostaje, ekvivalent + dokumentuj
  - [x] Subtask 6.3: EDIT `static/css/main.css` +1 `@import url('./components/contact-page.css');` POSLE `about-page.css` (`main.css:50`)
  - [x] Subtask 6.4: Verifikuj NEMA CDN; NEMA dupliranja postojećih komponenti (REUSE pill-button/section-eyebrow)

- [x] **Task 7: i18n .po update (AC8)**
  - [x] Subtask 7.1: `uv run python manage.py makemessages -l sr -l hu -l en` (Docker container)
  - [x] Subtask 7.2: `locale/sr/LC_MESSAGES/django.po` — popuni msgstr za sve nove msgid (pune dijakritike; NE prevodi tel/email vrednosti, SAMO labele/aria)
  - [x] Subtask 7.3: `locale/hu/` + `locale/en/` prevodi
  - [x] Subtask 7.4: `uv run python manage.py compilemessages -l sr -l hu -l en`
  - [x] Subtask 7.5: Smoke — 0 empty msgstr za nove msgid (sr); NEMA ćirilice

- [ ] **Task 8: Manuelni Dev smoke + Lighthouse (AC9)**
  - [ ] Subtask 8.1: `just dev`; GET `/sr/kontakt/` — 3 bloka (info + forma + mapa) + footer; kontakt info čitljiv; mapa se učita (iframe); forma polja vidljiva sa labelama, submit disabled + hint
  - [ ] Subtask 8.2: Responsive (375px stack / 1200px desktop 2-kolone; mapa aspect-ratio ne lomi mobile)
  - [ ] Subtask 8.3: Keyboard nav — tel/email/social linkovi + form polja tab-abilni; disabled submit NIJE u tab-redu; fokus outline vidljiv
  - [ ] Subtask 8.4: Verifikuj header „Kontakt" → `/kontakt/` (SM-D3 razrešenje radi); iframe ima `title`; `{% csrf_token %}` prisutan u formi
  - [ ] Subtask 8.5: Lighthouse CLI — TAČNA invokacija (mobile profil, `/sr/kontakt/` URL, accessibility+performance kategorije, json output) tako da se skor ne može cherry-pick-ovati:
    ```bash
    npx lighthouse http://localhost:8000/sr/kontakt/ \
      --only-categories=accessibility,performance \
      --form-factor=mobile --preset=desktop=false \
      --output=json --output-path=./3-3-contact-lighthouse-sr.json \
      --chrome-flags="--headless --no-sandbox"
    ```
    (mobile je Lighthouse default form-factor; eksplicitno `--form-factor=mobile`). A11y ≥ 95 + Performance ≥ 80; citiraj skor-ove iz `3-3-contact-lighthouse-sr.json` u Completion Notes PRE review (Google Maps iframe third-party — `loading="lazy"` ublažava Performance uticaj)

- [ ] **Task 9: TEA-deliverable — testovi (RED phase, NIJE Dev scope)** _(TEA agent piše testove PRE Dev GREEN; Dev NIKAD ne piše testove — project-context.md § Test discipline)_
  - **Minimum test count (27 testova — TEA potvrđuje tačan broj u RED fazi):** 9.1=4 (AC1) + 9.2=2 (AC2 header wire) + 9.3=5 (AC3 struktura+AC8 i18n) + 9.4=4 (AC4 kontakt-info) + 9.5=4 (AC5 mapa — uklj. C2 fallback link) + 9.6=5 (AC6 forma skelet+CSRF+disabled-polja/aria-describedby) + 9.7=3 (AC7 CSS) = **27 navedenih** (per-subtask zbir = narativni broj). NEMA JS unit testova (0 novog JS); iframe behavior + Lighthouse = manuelni smoke (AC9).
  - [ ] Subtask 9.1: `apps/pages/tests/test_contact_url.py` — **AC1: 4 tests**
    - `test_contact_url_resolves_sr/hu/en` (3 lokala HTTP 200)
    - `test_contact_uses_pages_contact_template` (`assertTemplateUsed(response, "pages/contact.html")`)
    - `test_pages_contact_reverse_resolves` (`reverse("pages:contact")` → `/sr/kontakt/`)
    - `test_home_and_about_views_still_work` (regresija — GET `/sr/` + `/sr/o-nama/` 200; ContactView NE pokvario HomeView/AboutView)
  - [ ] Subtask 9.2: `apps/pages/tests/test_contact_header_wired.py` — **AC2: 2 tests** (BeautifulSoup)
    - `test_header_kontakt_link_wired` (GET bilo koje strane → header „Kontakt" nav link href = `/sr/kontakt/`, NE `#`)
    - `test_contact_view_is_get_only` (POST `/sr/kontakt/` → **TAČNO 405** Method Not Allowed — deterministički assert, BEZ „ILI" alternative; `ContactView.http_method_names = ["get", "head", "options"]` garantuje da Django `dispatch` vraća 405 za POST; forma je skelet — SM-D4/SM-D1/C3)
  - [ ] Subtask 9.3: `apps/pages/tests/test_contact_template_structure.py` — **AC3 + AC8: ~5 tests** (BeautifulSoup)
    - `test_contact_renders_exactly_one_h1`
    - `test_contact_renders_exactly_one_main` (iz base.html — NE dupliran)
    - `test_contact_renders_3_sections_in_order` (kontakt-info + forma + mapa — sva 3 prisutna I u NORMATIVNOM DOM redosledu info → forma → mapa; SM-D9/AC3; ne proverava CSS layout)
    - `test_contact_each_section_has_aria_landmark`
    - `test_contact_no_cirillic_in_rendered_html`
  - [ ] Subtask 9.4: `apps/pages/tests/test_contact_info.py` — **AC4: 4 tests** (BeautifulSoup)
    - `test_contact_info_has_address` (`<address>` sa adresom)
    - `test_contact_info_has_sales_and_service_phones` (≥2 `tel:` linka — prodaja+servis odvojeno)
    - `test_contact_info_has_email_mailto` (`mailto:` link)
    - `test_contact_info_has_working_hours` (radno vreme prisutno — semantic element)
  - [ ] Subtask 9.5: `apps/pages/tests/test_contact_map.py` — **AC5: 4 tests** (BeautifulSoup)
    - `test_contact_map_has_iframe` (`<iframe>` prisutan u mapa sekciji)
    - `test_contact_map_iframe_has_title` (iframe ima neprazan `title` atribut — a11y)
    - `test_contact_map_iframe_lazy_loaded` (`loading="lazy"`)
    - `test_contact_map_has_fallback_link` (C2 — map wrapper sadrži fallback `<a>` ka Google Mapama, npr. `a[href*="maps.google"]`, sa nepraznim opisnim tekstom linka; fallback prisutan kad iframe blokiran)
  - [ ] Subtask 9.6: `apps/pages/tests/test_contact_form_skeleton.py` — **AC6: 5 tests** (BeautifulSoup)
    - `test_contact_form_has_csrf_token` (`input[name=csrfmiddlewaretoken]` prisutan)
    - `test_contact_form_has_4_labeled_fields` (Ime/Email/Telefon/Poruka — svako sa `<label for>`)
    - `test_contact_submit_is_disabled` (`[data-testid=contact-submit]` ima `disabled` + `aria-disabled` — forward-compat skelet)
    - `test_contact_form_inputs_disabled_and_hint_associated` (a11y silent-data-loss guard — sva 4 input/textarea polja imaju `disabled`; `<form>` ima `aria-describedby` koji referencira `id` postojećeg hint elementa — programski povezan status)
    - `test_contact_form_has_no_functional_hx_post` (forma NEMA `hx-post`/funkcionalan POST action — Epic 4 scope; SM-D8)
  - [ ] Subtask 9.7: `apps/pages/tests/test_contact_page_css.py` — **AC7: 3 tests** (kolokovano uz app — mirror Story 3-2 `apps/pages/tests/test_about_page_css.py`)
    - `test_contact_page_css_imported_in_main_css`
    - `test_contact_page_css_uses_only_var_tokens` (0 magic hex; whitelist transparent/none/0/100% + layout px/%/aspect-ratio)
    - `test_contact_page_css_has_coric_prefix_on_all_classes`
  - [ ] Subtask 9.8: TEA verifikuje RED phase (testovi padaju pre Dev GREEN); commit test fajlove PRE Dev (`test(pages): Story 3.3 RED-phase tests — ContactView + kontakt-info + Google Maps iframe + forma skelet + pages:contact wire`)

## Dev Notes

### `apps/pages/` struktura — ContactView se DODAJE (live verifikovano 2026-06-01)

`apps/pages/` app VEĆ postoji (Story 3-1/3-2). ContactView se DODAJE pored HomeView+AboutView:
```
apps/pages/
├── __init__.py        (postoji)
├── apps.py            (PagesConfig — name="apps.pages"; NETAKNUTO)
├── views.py           (HomeView + AboutView — NETAKNUTO; DODAJ ContactView(TemplateView))
├── urls.py            (app_name="pages"; path("", home) + path("o-nama/", about) — DODAJ path("kontakt/", contact))
└── tests/             (test_home_*.py + test_about_*.py postoje; DODAJ test_contact_*.py)
```
- `apps/pages/views.py:43` `HomeView` + `:103` `AboutView` (REFERENCA pattern za ContactView — `template_name`; AboutView NE importuje domain modele = mirror za ContactView)
- `apps/pages/urls.py:9-12` — `urlpatterns = [path("", home), path("o-nama/", about)]` (DODAJ contact path POSLE)
- `config/settings/base.py` — `apps.pages` već u INSTALLED_APPS (Story 3-1; NEMA promene)
- `config/urls.py` — `apps.pages.urls` već include-ovan (novi contact path je UNUTAR pages/urls.py)

### Kritični REUSE pointeri (live verifikovani 2026-06-01)

- `apps/pages/views.py:103-111` — `AboutView(TemplateView)` (REFERENCA pattern: `template_name`, NE importuje domain modele, NE `get_context_data` override obavezan — mirror za ContactView)
- `templates/pages/about.html` (Story 3-2) — `{% extends "base.html" %}` + `{% block title %}`/`{% block meta_description %}`/`{% block content %}` 3-include obrazac (MIRROR za contact.html; ALI contact NEMA `{% block scripts %}` jer 0 JS)
- `templates/partials/header.html:96` — „Kontakt" nav link `href="#"` (SM-D3 WIRE na `pages:contact` — POSLEDNJI mrtav nav placeholder; mirror kako je 3-2 wire-ovao `:95` „O nama"). NAPOMENA: `:71` „Početna" već fiksiran u 3-2 (pune dijakritike); NAV nema `aria-current`/active markup ni na jednom linku
- `templates/partials/header.html:18-29` — top-header kontakt vrednosti: adresa „Vojvodjanska 1, Basaid, Srbija" (`:19`), `tel:+381230468168` prodaja (`:21-23`), `tel:+381000000000` servis placeholder „+381 XXX XXX XXX" (`:26-28`, IMP-4 marker). REUSE iste VREDNOSTI na kontakt strani (SM-D5; konzistentnost)
- `templates/partials/footer.html:44-62` — footer kontakt INFO: `tel:+381230468168` (`:45`), `mailto:prodaja@coricagrar.rs` (`:46`), `<address>Vojvodjanska 1, Basaid, Srbija</address>` (`:48` — ŠIŠANA latinica „Vojvodjanska", nasleđeni dug; kontakt strana renderuje PUNI-dijakritik „Vojvođanska", NE reuse ovog string-a — OQ-6), Facebook+Instagram social `href="#"` SVG (`:52-61`). REUSE iste vrednosti + social SVG path-ovi za kontakt strani (osim adrese — vidi gore). NAPOMENA: footer NEMA „Kontakt" NAV link (SM-D3b — NE diraj footer)
- `templates/partials/section_eyebrow.html` (Story 1-7) — `text`/`tag`/`variant`; UPPERCASE eyebrow (REUSE za sve 3 sekcije)
- `static/css/components/pill-button.css` (Story 1-7) — `coric-button`/`coric-button--primary` (REUSE za submit dugme; v1 disabled)
- `templates/base.html` — single `<main id="main-content">` + `{% block content %}` + `{% block title %}`/`{% block meta_description %}`/`{% block extra_head %}` + aria-live + header/footer; `{% csrf_token %}` dostupan (request kontekst). NE dupliraj
- `static/css/main.css:50` — zadnji `@import` je `about-page.css` (Story 3-2; DODAJ `contact-page.css` POSLE)
- `static/css/tokens.css:84-165` — `--color-brand-green-900/800/600`, `--color-accent-gold-500`, `--color-neutral-white/cream/gray-700/gray-500`, `--color-semantic-focus-ring`, `--typography-scale-h1/h2/h3/body/caption`, `--rounded-sm/md/pill`, `--shadow-md`, `--spacing-scale-*`
- CSP: `django-csp>=4.0` u pyproject.toml:11 ALI JOŠ NIJE konfigurisan — verifikovano live: NEMA `csp.middleware.CSPMiddleware` u `config/settings/base.py:53` MIDDLEWARE; NEMA `CONTENT_SECURITY_POLICY`/`CSP_*` direktiva. Iframe radi bez CSP izmene (SM-D6/OQ-3)
- epics.md:736-746 (Story 3.3 AC), :748-759 (Story 3.4 SiteSettings — POSLE ove story), :763-791 (Epic 4 4.1/4.2 Lead+ContactForm), :833-846 (Story 4.6 HTMX/ratelimit pattern)
- prd.md:185-193 (FR-5 Kontakt), :736-738 (§7.5 Google Maps), :663-664 (CSRF+ratelimit na formama)
- architecture.md:587-592 (apps/pages dir HomeView/AboutView/ContactView + /kontakt/), :786 (Google Maps inline iframe no JS dep), :594-598 (apps/forms /htmx/forme/kontakt/ — Epic 4), :894 (FR-1..FR-5 apps/pages)
- EXPERIENCE.md:100 (sitemap `/kontakt → Info + forma + Google Maps`), :336-356 (UJ-2 Marko kontakt tok)

### SM Decisions log

- **SM-D1** — **`ContactView(TemplateView)` u POSTOJEĆEM `apps/pages/views.py` (mirror Story 3-1 HomeView + 3-2 AboutView):** „Kontakt" je statička strana koju architecture.md mapira u `apps/pages/` (:587-592 `views.py # HomeView, AboutView, ContactView`; :592 `/kontakt/`; :894 FR-1..FR-5; FR-5). `apps/pages/` app postoji. Lock: DODAJ `class ContactView(TemplateView)` (`template_name = "pages/contact.html"`) POSLE AboutView. CBV TemplateView (NE FBV) — mirror 3-2 SM-D1. v1: NE importuje domain modele (mirror AboutView); **GET-only DETERMINISTIČKI (C3): klasa MORA postaviti `http_method_names = ["get", "head", "options"]`.** Django `View.dispatch` vraća **HTTP 405 Method Not Allowed** za svaki metod van `http_method_names` → POST `/sr/kontakt/` → 405 (deterministički). NEMA `post()` metod (forma je skelet, funkcionalan submit ide na ZASEBAN apps/forms endpoint `/htmx/forme/kontakt/` u Story 4.2). Opcioni `get_context_data()` SAMO za hardcoded kontakt-info literale (radno vreme, telefoni — čista Python lista/dict, NE DB query).
- **SM-D2** — **URL `/kontakt/` + ime `pages:contact`:** `path("kontakt/", ContactView.as_view(), name="contact")` u `apps/pages/urls.py` (POSLE about path). `i18n_patterns()` daje `/sr|hu|en/kontakt/`. Slug `kontakt` ASCII, ISTI za sve lokale u v1 (NEMA per-locale URL slug prevod — mirror 3-2 SM-D2). architecture.md:592 `/kontakt/`, EXPERIENCE.md:100 sitemap, epics.md AC `/sr/kontakt/`.
- **SM-D3** — **RAZREŠENJE header „Kontakt" placeholder (`pages:contact` postaje stvaran) — DEO DoD:** `header.html:96` „Kontakt" nav je mrtav `href="#"` (Story 1-8; verifikovano live). Lock: (a) `header.html:96`: `href="{% url 'pages:contact' %}"` (NAV bez aktivno-stranica pattern-a — `aria-current` van scope-a; SAMO wire URL; mirror kako je 3-2 wire-ovao „O nama" `:95`). (b) Footer NE diraj — footer NEMA „Kontakt" NAV link (verifikovano live: footer ima kontakt INFO blok + social `href="#"` placeholder-e koji su Epic 2/5/7 wire-ovi, van scope-a). Bez (a) header „Kontakt" ostaje mrtav — DEO DoD.
- **SM-D4** — 🔴 **SCOPE FORME = interpretacija (A): STRANA + MAPA + FORWARD-COMPAT SKELET; FUNKCIONALNA FORMA = EPIC 4 (KRITIČNA):** epics.md:742/744/746 eksplicitno veže formu na Epic 4 (Given „forma iz Epic 4 ili stub iz 4.2"; „forma povezana sa Story 4.2 ContactForm"; „prati HTMX pattern iz 4.6"). Cela Epic 4 + SiteSettings (3-4) su backlog; `Lead` model + SMTP + `apps/forms` NE postoje. Lock: 3-3 isporučuje (1) statičku stranu (ContactView GET-only); (2) kontakt-info hardcoded-translatable (forward-compat SiteSettings 3-4); (3) Google Maps static iframe; (4) FORWARD-COMPAT skelet forme (markup polja + CSRF token + disabled submit + TODO Story 4.2 marker; BEZ funkcionalnog submit-a/Lead/email/ratelimit/HTMX). NE kreirati Lead model, migraciju, apps/forms, SMTP, funkcionalan POST. Mirror 3-1 SM-D7 + 3-2 forward-compat placeholder obrazac. Funkcionalnost = Story 4.2 (forma) + 4.6 (HTMX/ratelimit pattern). Vidi OQ-1 (headline dependency).
- **SM-D5** — **Kontakt-info hardcoded-translatable (SiteSettings = Story 3-4; mirror 3-2 SM-D5):** `SiteSettings` (adrese/telefoni/email/radno-vreme/social) je Story 3-4 (epics.md:748-759; backlog — POSLE ove story). v1: sav kontakt sadržaj hardcoded-translatable kroz `{% translate %}` — adresa **„Vojvođanska 1, Basaid, Srbija" sa PUNIM dijakritikama** (top-header/footer koriste šišanu „Vojvodjanska" kroz deljeni msgid — kontakt strana NE nasleđuje taj defekt; AC8 zahteva pune dijakritike; vidi OQ-6 known debt), tel prodaja `+381230468168`, tel servis `+381 XXX XXX XXX` placeholder (OQ-4), email `prodaja@coricagrar.rs`, radno vreme placeholder (OQ-4), social `href="#"` (OQ-4). REUSE iste vrednosti kao top-header/footer (konzistentnost) — IZUZEV adrese, gde kontakt strana koristi puni-dijakritik string. Forward-compat: kad Story 3-4 stigne, prelazi na `{% site_setting %}` tag (epics.md:757-758; template grana ista). NE fake SiteSettings model, NE migracija. NAPOMENA: tel/email VREDNOSTI nisu prevodive (NE `{% translate %}`); SAMO labele/aria-label-i.
- **SM-D6** — **Google Maps static iframe — NULA JS + CSP forward-compat (third-party):** architecture.md:786 „inline iframe, no JS dep"; epics.md:745 „embed bez JS dep-a". Lock: static `<iframe>` Google Maps Embed (`src` ka Basaid; OQ-3 koordinate biznis sign-off), NULA JS/Maps-API/lib. A11y: iframe MORA `title` atribut (NVDA accessible naziv; bez njega nedostupan), `loading="lazy"`, `referrerpolicy`, responsive aspect-ratio wrapper. API ključ: standardni Embed iframe radi bez ključa za prost place embed; env-var API ključ OPCIONO/forward-compat (OQ-3); Dev NE hardkoduje ključ. **CSP forward-compat:** django-csp dep postoji ALI CSP NIJE konfigurisan (verifikovano live — NEMA CSPMiddleware/direktiva u settings) → iframe radi danas bez izmene. **X-Frame-Options napomena (za Epic-9 autora):** `XFrameOptionsMiddleware` je aktivan + `X_FRAME_OPTIONS=DENY` (prod), ALI ta direktiva kontroliše ko sme da uokviri NAŠ sajt — NE blokira naš embed Google Mapa; zato mapa renderuje danas. Budući hardening surface za naš embed je ISKLJUČIVO CSP `frame-src`/`img-src` (NE X-Frame-Options). KADA CSP uveden (Epic 9 hardening), MORA `frame-src https://www.google.com` + `img-src` Google tile domeni (`*.google.com`/`*.googleapis.com`/`*.gstatic.com`) — inače mapa puca. Ova story NE konfiguriše CSP (van scope-a); dokumentuje forward-compat u template komentaru + OQ-3.
- **SM-D7** — **0 novih JS modula:** mapa je static iframe (SM-D6, NULA JS); forma je skelet bez funkcionalnog submit-a (SM-D8, NEMA HTMX). Kontakt strana NE dodaje `{% block scripts %}` u contact.html. Site-wide skripte iz base.html (HTMX/Bootstrap/sticky-nav/lightbox/itd.) ostaju nasleđene — NE diraj. Mirror 3-1 (0 JS) vs 3-2 (1 JS timeline-reveal) — kontakt je bliže 3-1 (0 JS).
- **SM-D8** — **Forma = forward-compat skelet sa CSRF, BEZ funkcionalnog submit-a:** Lock (mirror SM-D4): `<form method="post" data-testid="contact-form">` (EKSPLICITNO `method="post"`, BEZ `action` — C1) sa 4 polja (Ime*/Email*/Telefon/Poruka*) + vidljive `<label>` + `aria-required` + **sva polja `disabled` u v1 (a11y — sprečava silent-data-loss: korisnik ne kuca u nefunkcionalnu formu, disabled polja su van tab-reda)** + `{% csrf_token %}` PRISUTAN (project-context.md § Security #1) + submit dugme `disabled aria-disabled` (`coric-button--primary`, `data-testid="contact-submit"`) + **vizuelno istaknut „uskoro aktivna" hint** sa `id`, **povezan sa `<form>` preko `aria-describedby`** (AT objavljuje status; copy aktivno preusmerava: „Do tada nas kontaktirajte telefonom ili e-poštom") + KANONSKI TODO Story 4.2 marker. NEMA `hx-post`/funkcionalan POST action (endpoint `/htmx/forme/kontakt/` + ContactForm = Story 4.2; ratelimit/aria-live OOB = Story 4.6). ContactView GET-only. Story 4.2 samo aktivira submit (ukloni `disabled` sa polja+dugmeta, doda hx-post) BEZ restrukturiranja markup-a.
- **SM-D9** — **Reading order NORMATIVAN (info → forma → mapa); CSS vizuelni layout Dev/Step-02 bira:** EXPERIENCE.md:100 „Info + forma + Google Maps". **DOM/`{% include %}` redosled je LOCK-ovan: `_contact_info` → `_contact_form` → `_contact_map`** (semantički reading-order + SEO/a11y determinizam; AC3 testira ovaj redosled u DOM-u). VIZUELNI raspored je Dev/DESIGN.md izbor preko CSS-a: desktop — kontakt-info + forma side-by-side (2-kolone), mapa puna širina; mobile — sve stack-ovano. CSS sme da repozicionira vizuelno (npr. grid/flex order) ali NE menja source order. Ranija formulacija „Dev bira layout" odnosi se ISKLJUČIVO na CSS prezentaciju, NE na `{% include %}` redosled (uklonjena dvosmislenost sa AC3). NE blokirajući za vizuelni izbor.
- **SM-D10** — **h1 = page title („Kontakt"/„Kontaktirajte nas"; v1 default „Kontakt"):** Single h1 strane (SEO/a11y page title jasnoća; mirror 3-2 SM-D9 „O nama"). v1 lock: h1 „Kontakt" ILI „Kontaktirajte nas" (Dev/biznis copy bira; trivijalna izmena). Eyebrow-i diferenciraju sekcije.
- **SM-D11** — **Responsive (mirror 3-2 SM-D11):** info+forma 2-kolone desktop / stack mobile (`@media (min-width: 768px)`); mapa responsive aspect-ratio (npr. `16/9`); touch mete ≥ 44px (tel/email/social/form polja).
- **SM-D12** — Sprint-status.yaml update je SM handoff tracking (NIJE deliverable; epic-3 već in-progress iz Story 3-1).

### Open Questions

- **OQ-1 (🔴 HEADLINE — Epic 4 funkcionalna forma + Lead/SMTP + SiteSettings dependency):** Ova story isporučuje forma-SKELET (SM-D4/SM-D8), NE funkcionalnu formu. Funkcionalnost zahteva: `Lead` model + SMTP config (Story 4.1), `ContactForm` + HTMX submit + uspeh/greška partial (Story 4.2), ratelimit + aria-live OOB pattern (Story 4.6) — SVE backlog. Dodatno kontakt-info izvor `SiteSettings` (Story 3-4, backlog, POSLE ove story). Status: OTVORENO — skelet forme + hardcoded-translatable info su NAMERNO v1 stanje; Story 4.2 aktivira submit (ukloni disabled, doda hx-post na `/htmx/forme/kontakt/`), Story 3-4 prebacuje info na `{% site_setting %}`. Forward-compat markup tako da kasniji stories ne restrukturiraju. PRODUKCIONI BLOKER: forma MORA raditi pre launch-a (prd.md:775 „FR-5 mora da radi od prvog dana") — to znači Epic 4 Story 4.2 MORA biti gotov pre produkcije; ova story NE završava FR-5 funkcionalno (samo vizuelno).
- **OQ-2 (per-locale URL slug — `/kontakt/` vs `/kapcsolat/` vs `/contact/`):** v1 lock (SM-D2): slug `kontakt` ISTI za sva 3 locale (i18n_patterns daje samo `/sr|hu|en/` prefix). Per-locale slug prevod van scope-a v1 (mirror 3-2 OQ-1). Status: OTVORENO — fiksan `kontakt` OK za v1; per-locale slug razmotriti u Step-02/SEO Epic 6 ako zahteva (verovatno NE).
- **OQ-3 (Google Maps embed — koordinate/lokacija + API ključ + CSP direktive):** SM-D6: v1 koristi LITERALNI placeholder Maps Embed iframe `src` u template-u ka Basaid lokaciji (placeholder koordinate — finalna tačna lokacija/pin = biznis sign-off, Mihas), **BEZ env-var** (YAGNI — prost Embed nema secret). API ključ: prost Embed iframe radi bez ključa, Dev NE hardkoduje. TEK ako biznis isporuči keyed/branded Maps Embed URL (restrikcije/branding/rotacija secret-a) → razmotriti env-var (`GOOGLE_MAPS_EMBED_URL` ili sličan settings/context) u toj budućoj izmeni, NE u v1. **CSP:** django-csp NIJE konfigurisan u v1 (iframe radi); KADA CSP uveden (Epic 9 hardening), MORA `frame-src https://www.google.com` + `img-src` Google domeni — inače mapa puca. **X-Frame-Options ne ulazi u ovaj surface:** `XFrameOptionsMiddleware`/`X_FRAME_OPTIONS=DENY` reguliše ko sme da uokviri naš sajt, NE naš outbound embed Mapa — Epic-9 autor menja SAMO CSP `frame-src`/`img-src`. Status: OTVORENO — placeholder lokacija + bez-ključa Embed OK za v1; tačna lokacija biznis sign-off pre produkcije; CSP direktive = Epic 9 hardening story (dokumentovano forward-compat).
- **OQ-4 (Kontakt podaci — realni servis-telefon, radno vreme, social URL-ovi):** SM-D5: v1 placeholder — servis-tel `+381 XXX XXX XXX` (ISTI kao top-header IMP-4 marker), radno vreme placeholder, social `href="#"`. Realne vrednosti = biznis input (Mihas/klijent), kroz Story 3-4 SiteSettings ILI pre produkcije. Status: OTVORENO — placeholder OK za Dev/smoke; realni podaci BLOCKING za produkciju (kontakt strana mora imati tačne podatke).
- **OQ-5 (footer „Kontakt" link — opciono dodavanje):** SM-D3b: footer trenutno nema NAV link ka `/kontakt/` strani (samo kontakt INFO blok). Opciono: dodati „Kontakt" link u footer Kontakt kolonu ka `pages:contact`. Status: OTVORENO — default NE diraj footer (van scope-a); ako biznis želi footer „Kontakt" link, trivijalno dodati (NE blokira).
- **OQ-6 (nasleđeni šišana-latinica defekt deljenog adresnog msgid-a):** top-header:19 + footer:48 renderuju „Vojvodjanska 1, Basaid, Srbija" (šišana latinica) kroz deljeni msgid — krši pune-dijakritike pravilo (project-context.md). REŠENJE u ovoj story: kontakt strana koristi SVOJ puni-dijakritik string „Vojvođanska 1, Basaid, Srbija" (AC4/AC8 prolaze na ovoj NOVOJ strani). Popravka samog deljenog top-header/footer msgid-a (`Vojvodjanska` → `Vojvođanska`) je VAN scope-a ove story (dodirnula bi Story 1-8 partials + sve strane). Status: OTVORENO — known debt; ispraviti kao zaseban i18n cleanup ILI uz Story 3-4 SiteSettings (kad adresa pređe na `{% site_setting %}` jedan izvor istine). NE blokira ovu story.

### Project Context Reference

Sva pravila iz `_bmad-output/project-context.md` se primenjuju. Posebno kritično:
- Srpski latinica pune dijakritike (č/ć/ž/š/đ) u svemu renderovanom; ASCII u URL slug (`kontakt`)
- Sve UI string kroz `{% translate %}` / `{% blocktranslate %}` (tel/email VREDNOSTI izuzete — samo labele/aria)
- CSS `var(--token)` (NEMA magic hex/px); `coric-` BEM prefiks
- **CSRF token na svim formama** (§ Security #1) — skelet forme MORA imati `{% csrf_token %}` već u v1 (AC6/SM-D8)
- **ratelimit na javnim formama** (§ Security #2) — dolazi sa funkcionalnom formom Story 4.6 (NE u v1 skeletu; forma još ne procesira input)
- **CSP preko django-csp** (§ Security #6) — NIJE konfigurisan u v1; iframe forward-compat (SM-D6/OQ-3); CSP config = Epic 9 hardening
- NEMA migracije (`apps/pages` bez modela u v1); NEMA Lead/SMTP/apps-forms; NEMA funkcionalne forme; NEMA HTMX; 0 novih JS; static Google Maps iframe (third-party, a11y title, lazy)
- A11y must-haves: single h1, single main (base.html), aria landmarks, iframe `title`, vidljive form labele + aria-required, focus-visible, contrast ≥ 4.5:1, touch mete ≥ 44px
- Performance: Google Maps iframe `loading="lazy"` (third-party — ublažava Performance uticaj); 0 novog JS

### References

- [Source: _bmad-output/planning-artifacts/epics.md:736-746 (Story 3.3 Kontakt AC — forma povezana sa Story 4.2, HTMX pattern iz 4.6, Google Maps env-var iframe); :748-759 (Story 3.4 SiteSettings — kontakt info izvor, POSLE ove story); :763-791 (Epic 4 Story 4.1 Lead+SMTP, Story 4.2 Opšta kontakt forma FR-5); :833-846 (Story 4.6 HTMX/aria-live OOB/ratelimit pattern); :331 (Epic 3 FR-1..FR-5)]
- [Source: _bmad-output/planning-artifacts/prds/prd-CORIC_AGRAR-2026-05-27/prd.md:185-193 (FR-5 Kontakt — adresa/telefoni prodaja+servis/email/radno vreme/social/forma FR-19/Google Maps pin); :736-738 (§7.5 Google Maps embed); :663-664 (CSRF + ratelimit na formama); :775 (FR-5 mora raditi od prvog dana — Epic 4 produkcioni bloker)]
- [Source: _bmad-output/planning-artifacts/architecture.md:587-592 (apps/pages dir HomeView/AboutView/ContactView + /, /o-nama/, /kontakt/); :786 (Google Maps templates/pages/contact.html inline iframe, Static embed no JS dep); :594-598 (apps/forms /htmx/forme/kontakt/ — Epic 4 endpoint, NE ContactView); :894 (FR-1..FR-5 apps/pages); :177/182 (django-ratelimit/django-csp)]
- [Source: _bmad-output/planning-artifacts/ux-designs/ux-CORIC_AGRAR-2026-05-27/EXPERIENCE.md:100 (sitemap /kontakt → Info + forma + Google Maps); :336-356 (UJ-2 Marko kontakt tok — forma success kartica = Epic 4); :137/182-183 (forma greška/uspeh state — Epic 4); :41-66 (top-header kontakt info); :255 (touch meta 44px)]
- [Source: _bmad-output/implementation-artifacts/3-2-o-nama-strana.md — AboutView TemplateView pattern (mirror ContactView), pages:about header wire obrazac (mirror pages:contact SM-D3), about-page.css poslednji main.css @import, hardcoded-translatable Lorem Ipsum SM-D5, forward-compat placeholder obrazac]
- [Source: apps/pages/views.py:103-111 AboutView (REFERENCA ContactView); apps/pages/urls.py:9-12 urlpatterns (DODAJ contact)]
- [Source: templates/partials/header.html:96 „Kontakt" nav link href="#" (SM-D3 WIRE); :18-29 top-header kontakt vrednosti (REUSE)]
- [Source: templates/partials/footer.html:44-62 footer kontakt info + social SVG (REUSE vrednosti; NE diraj — nema „Kontakt" nav link SM-D3b)]
- [Source: templates/base.html (single main + block content/title/meta_description/extra_head + csrf dostupan + aria-live; NE dupliraj; NEMA block scripts dodatka)]
- [Source: static/css/main.css:50 about-page.css poslednji @import (DODAJ contact-page.css); static/css/components/{pill-button,section-eyebrow}.css (REUSE)]
- [Source: config/settings/base.py:53 MIDDLEWARE (NEMA CSPMiddleware — CSP NIJE konfigurisan, iframe forward-compat SM-D6/OQ-3); pyproject.toml:11 django-csp>=4.0 (dep prisutan, nekonfigurisan)]
- [Source: _bmad-output/project-context.md — sva pravila; § Security #1 CSRF / #2 ratelimit / #6 CSP; § A11y must-haves]

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
