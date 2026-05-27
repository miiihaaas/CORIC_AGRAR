---
stepsCompleted: [1, 2, 3, 4]
completedAt: '2026-05-27'
inputDocuments:
  - _bmad-output/planning-artifacts/prds/prd-CORIC_AGRAR-2026-05-27/prd.md
  - _bmad-output/planning-artifacts/architecture.md
  - _bmad-output/planning-artifacts/ux-designs/ux-CORIC_AGRAR-2026-05-27/DESIGN.md
  - _bmad-output/planning-artifacts/ux-designs/ux-CORIC_AGRAR-2026-05-27/EXPERIENCE.md
  - _bmad-output/planning-artifacts/briefs/brief-CORIC_AGRAR-2026-05-27/brief.md
  - _bmad-output/planning-artifacts/briefs/brief-CORIC_AGRAR-2026-05-27/addendum.md
project_name: CORIC_AGRAR
status: complete
mode: fast-path
language: srpski-latinica
---

# CORIC_AGRAR — Epic Breakdown

## Overview

Ovaj dokument razlaže PRD funkcionalne i nefunkcionalne zahteve, UX dizajn specifikaciju, i arhitektonske odluke u implementable epike i user stories za solo dev (Mihas). Sve story ID-ovi prate `<epic>.<story>` konvenciju (npr. 1.3, 5.2). Svaki FR i UX-DR je mapiran na barem jednu story u § FR Coverage Map.

## Requirements Inventory

### Functional Requirements

Izvučeno iz PRD § 4 (48 FR-ova, FR-1 do FR-48).

**Početna i statičke strane (4.1-4.2):**

- FR-1: Hero sekcija sa pretragom i top headerom
- FR-2: Sekcije Traktori / Priključna mehanizacija / Radne mašine / Polovna mehanizacija
- FR-3: Sekcija Priče sa polja preview (2 najnovije objave)
- FR-4: Stranica O nama (hero, tekst, vremenska lenta, masonry galerija)
- FR-5: Stranica Kontakt sa informacijama, formom, Google Maps

**Katalog traktora (4.3):**

- FR-6: Listing modela sa HTMX filterima (konjska snaga, godište, cena)
- FR-7: Logotipi brendova kao navigacija
- FR-8: Stranica brenda (hero, statistike, serije sa Grid/Extended layout, testimonijali, katalog CTA)

**Katalog mehanizacije (4.4):**

- FR-9: Stranica Priključna mehanizacija (Jeegee) sa 3 kategorije
- FR-10: Potkategorije priključne mehanizacije (4-nivoa hijerarhija)
- FR-11: Stranica Radne mašine (HZM) sa 4 potkategorije
- FR-12: Stranica MIX prikolice (Tulip) sa 2 modela
- FR-13: Stranica Polovna mehanizacija sa filterima (kategorija, brend, cena, godina, stanje)

**Stranica pojedinačnog proizvoda (4.5):**

- FR-14: Hero proizvoda sa ključnim karakteristikama
- FR-15: Sekcija Opis proizvoda
- FR-16: Galerija proizvoda sa Lightbox-om
- FR-17: Tabela tehničkih specifikacija u akordionu (Motor default-open)
- FR-18: Preuzimanje PDF brošure
- FR-19: Forma „Upit za model" sa auto-popunjenim modelom (5 polja)
- FR-20: Slični modeli (hibrid auto + admin override)
- FR-21: Sekcija Iz prve ruke (testimonijali za proizvod)
- FR-48: Variant selektor proizvoda (puna/rešetkasta daska, dupli/kembridž rotor)

**Servis (4.6):**

- FR-22: Stranica Servisna podrška sa formom (foto upload)
- FR-23: Stranica Rezervni delovi sa formom

**Blog Priče sa polja (4.7):**

- FR-24: Indeks blog objava (paginacija 10/strani, filter po kategoriji)
- FR-25: Stranica pojedinačne objave
- FR-26: Kategorije i tagovi bloga

**Pretraga i navigacija (4.8):**

- FR-27: Globalna pretraga (diacritic-insensitive, min 2 znaka, ranking, empty state)
- FR-28: Glavni meni sa sticky shrink-on-scroll
- FR-29: Top header (adresa + telefon)
- FR-30: Footer (zeleni, dinamička „Najnovije vesti")

**Trojezičnost (4.9):**

- FR-31: Prebacivanje jezika (sr/hu/en) sa URL prefix
- FR-32: Fallback strategija (graceful → sr sa diskretnim markerom)
- FR-33: SEO hreflang oznake

**Admin panel — sadržaj (4.10):**

- FR-34: Login i autentikacija admin-a (rate limited)
- FR-35: Dashboard (statistike, lead-ovi segmentovani po formi, brze akcije)
- FR-36: CRUD proizvoda (sa galerijom, varijantama, slični modeli, lokalizacija)
- FR-37: CRUD brendova (sa logo, hero, statistike, katalog, brand color)
- FR-38: CRUD kategorija i potkategorija (3-nivoa hijerarhija)
- FR-39: CRUD blog objava sa WYSIWYG editorom
- FR-40: CRUD statičkih strana

**Admin panel — pristup (4.11):**

- FR-41: Upravljanje admin korisnicima (Superadmin / Editor uloge)

**Admin panel — SEO (4.12):**

- FR-42: SEO meta po stranici i proizvodu (title/description per locale)
- FR-43: Upravljanje sitemap-om (auto-gen sa hreflang)
- FR-44: Redirect manager (301 pravila)

**Admin panel — podešavanja (4.13):**

- FR-45: Opšta podešavanja (naziv, kontakt, logotip, favicon, hero pozadine)
- FR-46: Navigacioni meni (admin upravlja stavkama, redosledom, dropdown podstavkama)
- FR-47: GDPR baner i politika kolačića (consent po kategoriji, tracking aktivacija)

### NonFunctional Requirements

Izvučeno iz PRD § 5.

- NFR-1: **Performance** — HTMX filter <500ms na ne-keširane upite; sajt učitava ključne strane realistično na 4G; konkretni targeti LCP <2.5s, TTFB <600ms, total page weight <1.5 MB na 3G/4G; responsive images sa srcset
- NFR-2: **Accessibility** — WCAG 2.1 AA baseline; vidljive labele i ARIA atributi na svim formama; tastaturna navigacija na akordionu i Lightbox-u; aria-live regions za HTMX swap; focus management na modal-close; reduced motion respect
- NFR-3: **Sigurnost** — HTTPS sa auto-redirect; lozinke hash-ovane (bcrypt/argon2); CSRF zaštita na svim formama; rate limiting na forme (10/15min IP) i admin login (5/15min IP); MIME validacija upload-a; session timeout 4h
- NFR-4: **SEO i indeksabilnost** — sve objavljene strane indeksabilne sa validnim title, meta description, hreflang; robots.txt; dinamički sitemap; locale-aware URL slugovi; Open Graph i Twitter Card meta tagovi
- NFR-5: **Pouzdanost** — 24/7 dostupnost sa razumnim uptime target-om; dnevni automatski bekap baze + media (30d retention); SSL Let's Encrypt sa auto-renewal
- NFR-6: **Browser podrška** — najnovije 2 verzije Chrome, Firefox, Safari, Edge; iOS Safari i Android Chrome poslednje 2; IE i legacy Edge nisu podržani
- NFR-7: **Privacy/GDPR** — nepostojanje PII van consent okvira; GDPR baner sa consent management po kategoriji (Neophodan / Analitički / Marketing); tracking pixel (FB) aktivira se samo nakon Marketing consent; GA samo nakon Analitički consent
- NFR-8: **i18n** — srpski (primarni), mađarski, engleski; graceful fallback na sr sa diskretnim markerom; `<html lang>` atribut se ažurira pri promeni jezika; per-field `lang` za fallback content

### Additional Requirements

Iz Architecture dokumenta — tehnički zahtevi koji utiču na implementaciju.

**Project bootstrap & development environment:**

- AR-1: **Starter setup** — Manual `uv init` + `django-admin startproject config .` (NE cookiecutter-django). Pun spisak komandi za Story 1.1 u Architecture § Starter Template Evaluation
- AR-2: Python 3.13+, Django 5.2 LTS, uv kao paket menadžer, pyproject.toml kao single source of truth
- AR-3: Code quality stack: ruff (linter + formatter), djade (Django template formatter), pre-commit hooks na svaki commit
- AR-4: Test stack: pytest-django + playwright za E2E
- AR-5: just task runner (zamenjuje Makefile) sa receptima za init, run, test, lint, deploy, makemessages

**Project structure:**

- AR-6: 12 Django apps organizovano u `apps/` direktorijumu (core, accounts, brands, products, catalog, pages, forms, blog, seo, gdpr, admin_ext, media_pipeline)
- AR-7: Striktna dependency pravila između app-ova (core ← everyone; brands ← products; products ← catalog/forms/blog; itd.) — vidi Architecture § Architectural Boundaries
- AR-8: Config settings split — `config/settings/{base,development,staging,production}.py`
- AR-9: Templates struktura — global `templates/`, per-app `templates/<app>/`, HTMX partials `templates/<app>/partials/<entity>_<action>.html`
- AR-10: Static struktura — `static/css/tokens.css` (single source za CSS Custom Properties), `static/css/components/<component>.css`, self-hosted Roboto subset u `static/fonts/roboto/`
- AR-11: Naming conventions: PascalCase Python klase, snake_case funkcije/varijable, kebab-case templates/CSS/URL, `coric-` prefix za custom CSS klase, slug ASCII transliteration

**Infrastructure & deployment:**

- AR-12: 3 okruženja (lokalno/staging/produkcija) sa Docker Compose (compose/{local,staging,production}.yml)
- AR-13: Hosting Hetzner VPS (CX22 staging, CX32 production), Nginx reverse proxy, Gunicorn WSGI, Let's Encrypt SSL sa auto-renewal
- AR-14: GitHub Actions CI/CD (lint + test + build na push; deploy na main branch)
- AR-15: GitHub Container Registry (GHCR) za Docker images

**Integracije:**

- AR-16: SMTP transport — Resend (primarni) ili Brevo (alt) preko `django-anymail` apstrakcije
- AR-17: Google Analytics 4 + Google Search Console + Facebook Pixel (uslovna aktivacija kroz GDPR consent)
- AR-18: Google Maps embed na Kontakt strani (iframe sa API ključ)

**Monitoring & operations:**

- AR-19: GlitchTip 6 self-host (Docker, ~512MB RAM) za error tracking, Sentry SDK protocol kompatibilan
- AR-20: UptimeRobot free tier za uptime monitoring (50 monitora / 5 min interval)
- AR-21: Django logging → JSON na fajl + `logrotate` 14d retencija
- AR-22: `pg_dump` cron + `restic` + Hetzner Storage Box (encrypted, EU-resident, 30d retention)
- AR-23: Performance budget mora se load test verifikovati posle staging deploy-a

**Database & storage:**

- AR-24: PostgreSQL primarna baza, Django ORM + manual review migracija
- AR-25: `django-modeltranslation` za i18n storage (field suffix `_sr`, `_hu`, `_en`)
- AR-26: PostgreSQL FTS sa `SearchVector` + `SearchRank` za globalnu pretragu
- AR-27: LocMem cache (Django default), DB-backed sesije
- AR-28: Local media storage u dev, Docker volume u staging/prod (no S3/cloud storage u v1)

**Image & PDF pipeline:**

- AR-29: `sorl-thumbnail` 12.10+ za image processing + responsive srcset
- AR-30: `pdf2image` (poppler) sync task pri admin upload-u za PDF cover-thumbnail generation
- AR-31: Pillow `Image.verify()` + `python-magic` za file upload validation

**Frontend deps:**

- AR-32: `django-htmx` middleware za HTMX request detection
- AR-33: `django-template-partials` za reusable HTML fragments (kritično za HTMX response patterns)
- AR-34: `django-bootstrap5` template tags
- AR-35: GLightbox 3.x lokalno hostovan za Lightbox funkcionalnost

**Security middleware:**

- AR-36: `django-ratelimit` na formama, `django-axes` na admin login, `django-csp` za Content-Security-Policy
- AR-37: Admin URL custom prefix `/admin-coric/` (security through obscurity)
- AR-38: HSTS + `SECURE_*` settings u production

### UX Design Requirements

Izvučeno iz DESIGN.md + EXPERIENCE.md. Svaki UX-DR je dovoljno konkretan da generiše story sa testabilnim AC-jevima.

**Design token system & visual identity:**

- UX-DR-1: **CSS token system** — implementiraj DESIGN.md frontmatter tokens (colors, typography, rounded, spacing, shadows) kao CSS Custom Properties u `static/css/tokens.css` (single source); svi custom CSS koriste `var(--token-name)` reference, nikad inline magic values
- UX-DR-2: **Color palette enforcement** — mono-zelena (green-900/800/600/400) + gold-500 + lime-500 + cream + jeegee-blue; surface-constraint pravila iz DESIGN.md § Color usage rules (gold/lime ISKLJUČIVO na dark green parent surface-ima; jeegee-blue samo decorative)
- UX-DR-3: **Typography setup** — self-hosted Roboto subset (latin + latin-ext za sr/hu), `font-display: swap`; weights 300/400/700; 7-step skala (h1 3.5rem do caption 0.875rem); CTA dugmad uppercase + tracking-wide
- UX-DR-4: **Layout & spacing system** — 1200px max container, Bootstrap 5.3 breakpoints (768/1200), 4px base spacing scale, section padding 80px desktop / 48px mobile

**Reusable visual components (custom):**

- UX-DR-5: **Hero overlay card komponenta** — green-800 bg, white text, radius 8px, padding 32px, bez shadow-a; pozicioniran preko foto-pozadine; sadrži brand lockup + h1 + bullets + *Ponavljajući element* watermark
- UX-DR-6: **Ponavljajući element komponenta** — pravougaonik 3:2 aspect, radius 8px, tankim belim koncentričnim lukovima u gornjem desnom uglu (1px stroke, opacity 0.5); bg-default green-800, bg-jeegee variant
- UX-DR-7: **Pill button komponenta** — primary (green-800 bg, white text, pill radius), secondary (transparent + green-800 border), cta-light (gold-500 bg, green-900 text); UPPERCASE + tracking-wide + Roboto Bold
- UX-DR-8: **Stat-medallion komponenta** — krug 120px desktop / 80px mobile, gold-500 outline 2px, gold-500 digit h1 size, count-up animacija via IntersectionObserver; SAMO na dark green parent surfaces
- UX-DR-9: **Brošura card komponenta** — outlined card (white bg + gray-300 border), radius 8px, cover-thumbnail levo (3deg rotate), naslov + file-size („2.8 MB, PDF") + cta-light PREUZMI dugme
- UX-DR-10: **Section eyebrow pattern** — UPPERCASE caption-size label sa zlatnim tankim linijama pre h2 sekcijskog naslova
- UX-DR-11: **Wave divider komponenta** — SVG inline, fill green-800, visine ~80px desktop / 48px mobile; selektivna upotreba (samo „Priče sa polja" top + ispod „Preuzmi katalog")

**Interactive behavioral patterns:**

- UX-DR-12: **Accordion komponenta** — transparent bg, green-600 bottom border, `+`/`−` ikona (sa `aria-hidden="true"`), default-open SAMO za prvu sekciju (Motor) na stranici proizvoda; klik toggle sa 250ms ease animacijom
- UX-DR-13: **Lightbox integracija** — GLightbox 3.x sa focus trap, Esc zatvara, Tab/swipe navigation, ARIA `role="dialog"`, focus restoration na zatvaranje
- UX-DR-14: **Sticky nav sa shrink-on-scroll** — na scroll-down kondenzuje (visina ~60px, manji logo); na scroll-up se proširuje; transform animacija 200ms ease
- UX-DR-15: **Search header expand-on-click** — search ikona u header-u; klik proširi u inline tekstualno polje (slide-in 200ms); min 2 znaka pre HTMX request-a; debounce 300ms; dropdown rezultati grupisani po tipu (Proizvodi/Objave)
- UX-DR-16: **Slider sa keyboard pause/play kontrolom** — auto-advance 6s; hover pauzira; **vidljiv pause/play dugme keyboard fokusabilno** (WCAG 2.2.2); `prefers-reduced-motion: reduce` isključuje auto-advance
- UX-DR-17: **HTMX aria-live OOB pattern** — svaka HTMX izmena šalje partial sa `hx-swap-oob` na `#aria-live` region (npr. „12 rezultata", „Forma poslata", „Greška pri slanju"); `aria-busy="true"` na in-flight elementima
- UX-DR-18: **Vremenska lenta komponenta** — SVG inline + CSS-only; animacija pri scroll-into-view kroz IntersectionObserver (800ms ease-in-out po segmentu)
- UX-DR-19: **Count-up animacija** — Statistika medaljon vrednosti animiraju 1500ms ease-out pri scroll-into-view; `prefers-reduced-motion` instant final
- UX-DR-20: **Card hover pattern** — translateY(-2px) + shadow intensifikacija 200ms ease (desktop only via `@media (hover: hover)`); cela kartica je klikabilna (ne samo CTA)

**Accessibility & i18n details:**

- UX-DR-21: **Focus indicator** — 2px ring `focus-ring` semantic token (achieves 3:1 contrast vs surface); `:focus-visible` na svim interaktivnim metama
- UX-DR-22: **i18n fallback marker** — kad polje koristi sr fallback (hu/en nije popunjeno), prikazuje se `ⓘ` ikon pored teksta sa tooltip „Sadržaj na srpskom — još nije preveden"
- UX-DR-23: **Language switcher** — `aria-label` lokalizovan po jeziku, `aria-current="page"` za trenutni; `<html lang>` se ažurira pri promeni; per-field `lang` atribut za fallback content
- UX-DR-24: **Skip link** „Preskoči na sadržaj" — vidljiv pri Tab focusu, vodi na main content
- UX-DR-25: **Repeating Element decorative aria-hidden** — corner motif uvek `aria-hidden="true"` / `alt=""`
- UX-DR-26: **Empty state pattern** — konzistentan pattern za 4 konteksta (filter no results, search no results, blog empty, polovna empty) — ikona + naslov + opis + CTA ka rešenju

**Footer & home page enhancements:**

- UX-DR-27: **Footer dinamička "Najnovije vesti" kolona** — automatski prikazuje 3 najnovije blog objave po `created_at`
- UX-DR-28: **„O nama" intro blok na Početnoj** — mockup-confirmed pun blok između hero-a i Traktori sekcije; naslov + kratak tekst + CTA *Saznaj više* → `/o-nama` (proširenje FR-1)
- UX-DR-29: **Footer solid bg** — solid green-800 (NE gradient kao što PRD §4.8 inicijalno specifikuje); razrešena kontradikcija u UX fazi
- UX-DR-30: **Search kao ikona u nav-u** — NE inline polje (kao PRD §4.1 inicijalno specifikuje); ikona koja se proširuje; razrešena kontradikcija u UX fazi
- UX-DR-31: **Unified zeleno UI chrome** — nav, footer, dashboard ostaju green-800 kroz ceo sajt; brand boje (Jeegee plava) se primenjuju SAMO na *Ponavljajući element* u hero pozicijama

**Mockup-confirmed visual details:**

- UX-DR-32: **Motor akordion default-open** sa `+`/`−` ikonama (UX-confirmed iz mockup-a)
- UX-DR-33: **Statistike sa zlatno-outlined kružnim medaljonima** + velikim zelenim brojevima (count-up animacija pri scroll-into-view)
- UX-DR-34: **Hero overlay card pattern** — tamno-zeleni floating card sa brand lockup + headline + bullets + *Ponavljajući element* watermark (na brand i product stranama)
- UX-DR-35: **Section eyebrow sa zlatnim linijama** oko UPPERCASE naslova

### FR Coverage Map

Svih 48 FR-ova mapirano na 9 epika. Detalji story-mapping-a popunjavaju se u step-03.

| FR | Epic | Coverage |
|---|---|---|
| FR-1 Hero | Epic 3 | Home page hero |
| FR-2 Brand/category sekcije | Epic 3 | Home page sekcije |
| FR-3 Blog preview na home | Epic 3 | Home page (renderuje iz Blog modela iz Epic 5) |
| FR-4 O nama | Epic 3 | O nama page |
| FR-5 Kontakt strana | Epic 3 | Contact page (forma iz Epic 4) |
| FR-6 Listing modela + filteri | Epic 2 | Tractor listing |
| FR-7 Brand logotipi | Epic 2 | Brand listing |
| FR-8 Stranica brenda | Epic 2 | Brand listing |
| FR-9 Jeegee priključna hero | Epic 2 | Jeegee page |
| FR-10 Potkategorije | Epic 2 | Subcategory listing |
| FR-11 HZM radne mašine | Epic 2 | HZM page |
| FR-12 Tulip MIX | Epic 2 | Tulip page |
| FR-13 Polovna mehanizacija | Epic 2 | Used listing |
| FR-14 Hero proizvoda | Epic 2 | Product detail |
| FR-15 Opis proizvoda | Epic 2 | Product detail |
| FR-16 Galerija + Lightbox | Epic 2 | Product detail + Lightbox integracija |
| FR-17 Akordion specifikacije | Epic 2 | Product detail |
| FR-18 Brošura | Epic 2 | Product detail + PDF cover-thumbnail generator |
| FR-19 Upit za model | Epic 4 | Model inquiry form |
| FR-20 Slični modeli | Epic 2 | Product detail |
| FR-21 Iz prve ruke | Epic 2 | Product detail |
| FR-22 Servisni zahtev | Epic 4 | Service request form |
| FR-23 Rezervni delovi | Epic 4 | Parts request form |
| FR-24 Blog indeks | Epic 5 | Blog index page |
| FR-25 Blog post | Epic 5 | Blog post detail |
| FR-26 Blog kategorije/tagovi | Epic 5 | Blog modeli + filtering views |
| FR-27 Globalna pretraga | Epic 2 | Global search (PostgreSQL FTS) |
| FR-28 Glavni meni | Epic 1 | Header + nav komponente |
| FR-29 Top header | Epic 1 | Header komponente |
| FR-30 Footer | Epic 1 | Footer base + Epic 5 dynamic Najnovije vesti |
| FR-31 Language switcher | Epic 1 | i18n setup + switcher partial |
| FR-32 i18n fallback | Epic 6 | Fallback marker + helper |
| FR-33 SEO hreflang | Epic 6 | Hreflang HTML tags |
| FR-34 Admin login | Epic 8 | Custom admin login |
| FR-35 Dashboard | Epic 8 | Admin dashboard |
| FR-36 CRUD proizvoda | Epic 8 | Product admin |
| FR-37 CRUD brendova | Epic 8 | Brand admin |
| FR-38 CRUD kategorija | Epic 8 | Category admin |
| FR-39 CRUD blog WYSIWYG | Epic 8 | Blog admin |
| FR-40 CRUD statičkih strana | Epic 8 | Static pages admin |
| FR-41 Korisnici i pristup | Epic 8 | RBAC + user accounts |
| FR-42 SEO meta | Epic 6 | SeoMeta model + per-page admin |
| FR-43 Sitemap | Epic 6 | Sitemap auto-gen sa hreflang |
| FR-44 Redirect manager | Epic 6 | 301 redirect manager |
| FR-45 Opšta podešavanja | Epic 8 | SiteSettings admin (+ Epic 3 model creation) |
| FR-46 Navigacioni meni | Epic 8 | Navigation admin |
| FR-47 GDPR baner | Epic 7 | GDPR banner + consent + tracking activation |
| FR-48 Variant selektor | Epic 2 | Product detail |

## Epic List

9 epika ukupno, organizovanih po user value (ne tehničkim slojevima). Svaki epic je standalone i može da bude isporučen nezavisno; svaki nadograđuje na prethodnim ali ne zahteva buduće.

### Epic 1: Project Foundation & Visual Identity

Posetilac otvara sajt i vidi brand-konzistentnu stranu sa pravim jezikom, fontom, paletom i osnovnim chrome elementima (header, footer, language switcher). Posle Epic 1, sajt postoji na sva 3 environment-a, responzivan je, prebacuje jezik, sa placeholder content-om.

**FRs covered:** FR-28, FR-29, FR-30 (footer base), FR-31  
**AR coverage:** AR-1..AR-15, AR-32..AR-38  
**UX-DR coverage:** UX-DR-1, UX-DR-2, UX-DR-3, UX-DR-4, UX-DR-6, UX-DR-7, UX-DR-10, UX-DR-11, UX-DR-14, UX-DR-21, UX-DR-23, UX-DR-24, UX-DR-25, UX-DR-29, UX-DR-30, UX-DR-31

### Epic 2: Public Catalog — Browse Brands & Products

Marko (poljoprivrednik) može da pretraži ceo katalog, filtrira po snazi/godini/ceni, otvori stranicu modela, pogleda specifikacije i galeriju, preuzme PDF brošuru.

**FRs covered:** FR-6, FR-7, FR-8, FR-9, FR-10, FR-11, FR-12, FR-13, FR-14, FR-15, FR-16, FR-17, FR-18, FR-20, FR-21, FR-27, FR-48  
**AR coverage:** AR-24, AR-25, AR-26, AR-29, AR-30, AR-31  
**UX-DR coverage:** UX-DR-5, UX-DR-8, UX-DR-9, UX-DR-12, UX-DR-13, UX-DR-15, UX-DR-17, UX-DR-19, UX-DR-20, UX-DR-32, UX-DR-33, UX-DR-34, UX-DR-35

### Epic 3: Home & Static Pages

Posetilac dolazi na sajt i vidi reprezentativnu Početnu sa svim sekcijama; može da pročita O nama priču i nađe Kontakt informacije.

**FRs covered:** FR-1, FR-2, FR-3, FR-4, FR-5  
**UX-DR coverage:** UX-DR-18, UX-DR-28

### Epic 4: Lead-gen Forms & Email Delivery

Stojan može da podnese servisni zahtev sa foto upload-om; svaki posetilac može da pošalje opšti upit, upit za model, ili upit za rezervni deo — i klijent prima email obaveštenje.

**FRs covered:** FR-19, FR-22, FR-23 (FR-5 forma deo)  
**AR coverage:** AR-16, AR-36

### Epic 5: Blog (Priče sa polja)

Posetilac može da pročita blog objave organizovane po kategorijama i tagovima; footer prikazuje 3 najnovije objave dinamički.

**FRs covered:** FR-24, FR-25, FR-26 (+ dinamička „Najnovije vesti" iz Epic 1 footer-a)  
**UX-DR coverage:** UX-DR-27

### Epic 6: SEO & Discoverability

Sajt je indeksabilan u Google-u; admin može da unese meta podatke po stranici; redirect-i rade za stare URL-ove; i18n fallback je vizuelno označen.

**FRs covered:** FR-32, FR-33, FR-42, FR-43, FR-44  
**UX-DR coverage:** UX-DR-22

### Epic 7: GDPR & Privacy

Posetilac vidi GDPR baner pri prvoj poseti, bira kolačiće po kategoriji; tracking pixel-i (GA, FB) aktiviraju se samo posle saglasnosti.

**FRs covered:** FR-47  
**AR coverage:** AR-17

### Epic 8: Admin Dashboard & Content Management

Marijana (sadržaj-admin) može da loguje u admin panel, vidi statistike (posete, lead-ove po vrsti forme, ukupno content), i samostalno upravlja brendovima, proizvodima, blog objavama, statičkim stranama, podešavanjima sajta, navigacijom.

**FRs covered:** FR-34, FR-35, FR-36, FR-37, FR-38, FR-39, FR-40, FR-41, FR-45, FR-46

### Epic 9: Go-Live Readiness (Production + Quality)

Sajt je deployovan na Hetzner produkciju, dnevni bekap radi, monitoring detektuje pad, performance pokazatelji su verifikovani, accessibility audit prošao, E2E testovi cover-uju 3 ključna UJ-a.

**FRs covered:** — (cross-cutting; pokriva NFR-e i AR-e)  
**NFR coverage:** NFR-1 (performance), NFR-2 (a11y), NFR-5 (reliability), NFR-6 (browser)  
**AR coverage:** AR-12..AR-23  
**UX-DR coverage:** UX-DR-16, UX-DR-26

## Dependency Map

```text
Epic 1 (Foundation)
  ↓
Epic 2 (Public Catalog) ←─── Epic 3 (Home/Static) ─── Epic 4 (Forms)
                ↓                       ↓                     ↓
              Epic 5 (Blog) ←───── (footer dynamic)         Epic 6 (SEO)
                                                              ↓
                                                            Epic 7 (GDPR)
                                                              ↓
                                                            Epic 8 (Admin)
                                                              ↓
                                                            Epic 9 (Go-Live)
```

Svaki epic je standalone — Epic 2 ne treba Epic 3 da bi radio (može se browse-ovati katalog bez Home strane); Epic 3 može renderovati blog preview kao Lorem Ipsum dok Epic 5 nije gotov. Stories unutar epika nemaju zavisnost ka budućim stories-ima istog epica.

---

## Epic 1: Project Foundation & Visual Identity

Posle Epic 1, sajt postoji na sva 3 environment-a, responzivan je, prebacuje jezik, i ima brand-konzistentnu vizuelnu osnovu. Sadržajne strane su placeholder.

### Story 1.1: Project Bootstrap sa uv i Django

As a **dev (Mihas)**, I want **inicijalan Python/Django projekat sa pravom strukturom direktorijuma**, so that **mogu da krenem sa razvojem ostalih story-ja na čvrstoj osnovi**.

**Acceptance Criteria:**

**Given** prazan repo na lokalnoj mašini  
**When** izvršim `uv init coric-agrar --python 3.13`, dodam core deps (django>=5.2, psycopg[binary], django-modeltranslation, django-htmx, django-template-partials, django-bootstrap5, django-environ, django-anymail, django-ratelimit, django-axes, django-csp, sorl-thumbnail, pdf2image, python-magic), i pokrenem `uv run django-admin startproject config .`  
**Then** projekat ima `pyproject.toml`, `uv.lock`, `manage.py`, `config/` direktorijum sa Django settings  
**And** može da pokrene `uv run python manage.py check` bez grešaka  
**And** dev deps (pytest-django, ruff, djade, pre-commit, playwright, django-debug-toolbar) instalirane u dev grupi  
**And** kreiran `justfile` sa receptima: `dev`, `test`, `lint`, `migrate`, `messages`

### Story 1.2: Multi-environment Settings Split sa django-environ

As a **dev**, I want **odvojene settings fajlove po environment-u sa env-driven konfiguracijom**, so that **mogu sigurno da menjam parametre između lokal/staging/prod bez code change-a**.

**Acceptance Criteria:**

**Given** Django project iz Story 1.1  
**When** refaktorišem `config/settings.py` u `config/settings/{base,development,staging,production}.py` sa `django-environ` integracijom  
**Then** svaki settings modul nasleđuje iz `base.py` i overrides samo razlikujuće key-jeve  
**And** postoji `.env.example` sa svim required env vars (`DJANGO_SECRET_KEY`, `DATABASE_URL`, `ALLOWED_HOSTS`, `EMAIL_*`, `SENTRY_DSN`, itd.)  
**And** `.env` je u `.gitignore`  
**And** `DJANGO_SETTINGS_MODULE=config.settings.development` se postavlja kao default u `manage.py`

### Story 1.3: Docker Compose za Local Environment

As a **dev**, I want **Docker compose setup za lokalni razvoj**, so that **PostgreSQL i Django rade bez ručne instalacije**.

**Acceptance Criteria:**

**Given** Project setup iz Story 1.1, 1.2  
**When** kreiram `compose/local.yml`, `compose/django/Dockerfile` (multi-stage uv build), `compose/django/entrypoint.sh`  
**Then** `just dev` pokreće Django + PostgreSQL u Docker-u sa hot-reload  
**And** PostgreSQL podaci persistuju u Docker volume  
**And** browser na `http://localhost:8000` prikazuje Django welcome page  
**And** `compose/django/Dockerfile` koristi `uv sync` za deps instalaciju

### Story 1.4: i18n Setup sa Locale URL Routing i Switcher

As a **posetilac**, I want **da mogu da prebacim jezik na sajtu (sr/hu/en)**, so that **mogu da čitam sadržaj na mom jeziku, sa URL prefix-om koji reflektuje izbor**.

**Acceptance Criteria:**

**Given** Django project sa settings iz Story 1.2  
**When** dodam u `base.py`: `LANGUAGES = [('sr', 'Srpski'), ('hu', 'Magyar'), ('en', 'English')]`, `LANGUAGE_CODE = 'sr'`, `LOCALE_PATHS`, `USE_I18N=True`, `USE_L10N=True`, registrujem `LocaleMiddleware`, i `apps/core/middleware.py:LocaleSwitcherMiddleware`  
**Then** `i18n_patterns()` u `config/urls.py` rendera sve URL-ove sa prefix-om `/sr/`, `/hu/`, `/en/`  
**And** `/` (root bez prefiks-a) redirektuje na `/sr/`  
**And** template `templates/partials/language_switcher.html` ima dropdown sa 3 jezika, klik menja URL prefix čuvajući strukturalnu poziciju  
**And** `<html lang="...">` u `base.html` se ažurira pri promeni  
**And** `apps/core/translation.py` patern je dokumentovan kao primer (`TranslationOptions`)

### Story 1.5: Self-hosted Roboto + DESIGN.md Tokens kao CSS Custom Properties

As a **dev**, I want **CSS token sistem koji 1:1 mapira DESIGN.md tokene**, so that **mogu da koristim `var(--token-name)` umesto magic numbers kroz ceo CSS i da front Roboto bez Google Fonts CDN-a**.

**Acceptance Criteria:**

**Given** Project iz Story 1.3  
**When** preuzmem Roboto subset (latin + latin-ext) u woff2 formatu i smestim u `static/fonts/roboto/`  
**And** kreiram `static/css/tokens.css` sa `@font-face` deklaracijama za Roboto 300/400/700 sa `font-display: swap`, i sa `:root { ... }` koji eksportuje sve tokene iz DESIGN.md frontmatter (colors, typography scale, rounded, spacing, shadows)  
**Then** `var(--color-brand-green-800)` vraća `#25402f` u dev tools  
**And** `var(--typography-scale-h1)` vraća `3.5rem`  
**And** Roboto font loaduje bez network request-a ka googleapis.com (verifikovano u dev tools Network tab)  
**And** `tokens.css` je linkovan u `base.html` pre svih ostalih CSS fajlova

### Story 1.6: Base Templates sa Bootstrap 5 + HTMX Setup

As a **dev**, I want **base template sa kompletnom HTMX + Bootstrap 5 infrastrukturom**, so that **svi child templates nasleđuju iste meta tag-ove, CSS, JS, ARIA strukturu**.

**Acceptance Criteria:**

**Given** Token system iz Story 1.5  
**When** kreiram `templates/base.html` sa: HTML5 doctype, `<html lang>` dinamično iz `{{ LANGUAGE_CODE }}`, viewport meta tag, link na `tokens.css` + Bootstrap 5 + custom CSS, HTMX script (lokalni `static/vendor/htmx.min.js`), `{% block content %}`, ARIA live region (`<div id="aria-live" aria-live="polite" aria-atomic="true"></div>`), skip link „Preskoči na sadržaj"  
**And** kreiram `apps/core/templatetags/htmx_aria.py` sa `{% aria_live %}` template tag-om  
**And** registrujem `django-htmx` middleware u settings  
**Then** child template extends `base.html` i ima pristup ARIA live region target-u  
**And** Bootstrap 5 utility klase (`d-flex`, `gap-3`) rade u svakom child template-u  
**And** HTMX detect (`{% if request.htmx %}`) je dostupan u svim view-ovima  
**And** Lighthouse a11y skor na praznom base template-u ≥ 95

### Story 1.7: Reusable Visual Komponente

As a **dev**, I want **5 reusable vizuelnih komponenti dostupnih kao Django template partials**, so that **mogu da ih reusam kroz sve strane bez kopiranja stila**.

**Acceptance Criteria:**

**Given** Base template iz Story 1.6  
**When** kreiram `templates/partials/repeating_element.html`, `static/css/components/repeating-element.css`, plus partials i CSS za: Pill Button (3 varijante), Wave Divider (SVG inline), Section Eyebrow (sa zlatnim linijama), Hero Overlay Card  
**Then** `{% include "partials/repeating_element.html" with variant="green" %}` rendera 3:2 pravougaonik sa belim koncentričnim lukovima u uglu  
**And** `{% include "partials/repeating_element.html" with variant="jeegee" %}` rendera Jeegee plavu varijantu  
**And** Pill Button koristi `coric-button--primary`, `coric-button--secondary`, `coric-button--cta-light` klase  
**And** Wave Divider SVG ima `aria-hidden="true"` i koristi `var(--color-brand-green-800)`  
**And** sve komponente koriste `var(--...)` tokens, nigde inline magic colors

### Story 1.8: Sticky Nav + Top Header + Footer + Language Switcher Partial

As a **posetilac**, I want **konzistentan header sa sticky shrink-on-scroll i footer sa social linkovima**, so that **navigacija je uvek dostupna i pristupačna**.

**Acceptance Criteria:**

**Given** Komponente iz Story 1.7  
**When** kreiram `templates/partials/header.html` (top header sa adresom i telefonom + glavni nav sa dropdown-om za Mehanizaciju + search ikona + language switcher), `templates/partials/footer.html` (4 kolone: Logo+slogan / Proizvodi / Najnovije vesti placeholder / Kontakt+Social, sa green-800 solid bg, copyright separator), i `static/js/sticky-nav.js` (shrink-on-scroll sa `IntersectionObserver`)  
**Then** scroll down na bilo kojoj strani kondenzuje nav (visina ~60px, manji logo, top header sakriven)  
**And** scroll up vraća nav u full state, 200ms ease transformacija  
**And** language switcher prikazuje 3 jezika sa `aria-current="page"` za trenutni, `aria-label` lokalizovan  
**And** mobile (<768px) prikazuje hamburger meni + kondenzovan top header (samo ikona telefona, klik proširi)  
**And** footer "Najnovije vesti" sekcija renderuje Lorem Ipsum 3 stavke (dinamika dolazi u Epic 5)

### Story 1.9: GitHub Actions CI Pipeline

As a **dev**, I want **automatski CI build koji proverava lint i testove na svaki push**, so that **regression-i ne odlaze u main branch**.

**Acceptance Criteria:**

**Given** Projekat iz Story 1.1-1.8  
**When** kreiram `.github/workflows/ci.yml` sa job-ovima: setup uv, install deps, run `ruff check`, run `djade --check templates/`, run `pytest`  
**Then** PR ka main branch-u pokreće CI sa svih job-ova  
**And** fail na bilo kom step-u blokira PR merge  
**And** GitHub Container Registry (GHCR) je konfigurisan kao secret/login source  
**And** pre-commit hook lokalno (`.pre-commit-config.yaml`) pokreće isti lint pre push-a

---

## Epic 2: Public Catalog — Browse Brands & Products

Posle Epic 2, Marko može da pretraži ceo katalog, filtrira po snazi/godini/ceni, otvori stranicu modela i preuzme PDF brošuru. Admin (Epic 8) još uvek nije ovde — sample data se učitava kroz fixtures (Epic 9 9.7) ili Django shell.

### Story 2.1: Brand, Series, Category, Subcategory Modeli

As a **dev**, I want **modele za organizaciju kataloga (Brand → Series → modeli; Kategorija → Potkategorija)**, so that **mogu da hijerarhijski strukturišem proizvode**.

**Acceptance Criteria:**

**Given** Epic 1 završen  
**When** kreiram `apps/brands/models.py` sa: `Brand` (name, slug, logo, hero_image, description, slogan, statistics JSON, catalog_pdf, brand_color, is_coming_soon flag), `Series` (FK Brand, name, slug, layout_mode choice [Grid/Extended]), `Category` (name, slug, is_for=[traktori, mehanizacija], display_order), `Subcategory` (FK Category, parent FK self, name, slug, icon, display_order)  
**And** dodam `apps/brands/translation.py` sa `TranslationOptions` za name, description, slogan po svakom modelu  
**Then** `python manage.py makemigrations brands` generiše migraciju sa translated polja suffix `_sr`, `_hu`, `_en`  
**And** `python manage.py migrate` kreira tabele bez grešaka  
**And** Subcategory podržava 3 nivoa dubine (potkategorija → pod-potkategorija → grupa-po-atributu)

### Story 2.2: Product i Related Modeli

As a **dev**, I want **Product model sa svim povezanim entitetima**, so that **mogu da prikazujem kompletnu stranicu proizvoda**.

**Acceptance Criteria:**

**Given** Brand modeli iz Story 2.1  
**When** kreiram `apps/products/models.py` sa: `Product` (FK Brand, FK Series, FK Subcategory, slug, name, description, key_features JSON do 3, main_image, year, price_eur, horse_power, condition choice, is_published flag, status choice [draft/published/archived], created_at), `ProductImage` (FK Product, image, order, alt_text), `ProductVariant` (FK Product, name, code, image, description, order), `ProductSpecification` (FK Product, section choice [Motor/Transmisija/Hidraulika/Ostalo], key, value, order), `ProductBrochure` (FK Product, pdf_file, cover_thumbnail_image, title), `ProductTestimonial` (FK Product, photo, quote, author_name, location, order), `ProductSimilar` (FK Product, FK related_Product, order — manual override za FR-20 hibrid)  
**And** dodam `apps/products/translation.py` za name, description, key_features, ProductSpecification.key/value, ProductBrochure.title, ProductTestimonial.quote/location  
**Then** model relationships su jednosmerni (Product → Brand, ne obratno)  
**And** Product ima `get_absolute_url()` koji vraća `/proizvod/<slug>/`  
**And** Migration kreira sve tabele uz `_sr`/`_hu`/`_en` suffix-e

### Story 2.3: Image Pipeline sa sorl-thumbnail + Responsive Srcset

As a **dev**, I want **automatski image pipeline koji generiše responsive varijante**, so that **slike se serviraju u optimal-noj veličini za svaki uređaj**.

**Acceptance Criteria:**

**Given** Product modeli iz Story 2.2  
**When** konfigurišem `sorl-thumbnail` u settings (THUMBNAIL_BACKEND, kee_value backend), i kreiram `apps/media_pipeline/utils.py` sa `validate_image_mime()` koji koristi `python-magic`  
**Then** `{% thumbnail product.main_image "400x300" crop="center" %}` template tag rendera resized image sa cached version-om  
**And** template helper `<picture>` element sa srcset (`400w`, `800w`, `1600w`) rendera tri varijante za responsive  
**And** upload non-image fajla u Product.main_image blokira save sa validation error-om  
**And** thumbnail-ovi se čuvaju u `media/thumbnails/`

### Story 2.4: PDF Cover-thumbnail Generator

As a **dev**, I want **automatski generisan cover thumbnail iz PDF brošure**, so that **brošura card prikazuje preview prve strane bez ručnog rada**.

**Acceptance Criteria:**

**Given** Product modeli iz Story 2.2  
**When** kreiram `apps/media_pipeline/signals.py` sa `post_save` handler-om za `ProductBrochure` koji koristi `pdf2image` (poppler dependency) da render-uje prvu stranu PDF-a kao 240×320px JPG  
**Then** upload PDF brošure automatski generiše `cover_thumbnail_image` polje  
**And** ako PDF nema validnu prvu stranu, signal logu-je warning a save uspe sa praznim cover_thumbnail  
**And** Generated thumbnail je u `media/products/<slug>/brochure-cover.jpg`  
**And** Dockerfile sadrži `apt-get install poppler-utils` u final stage-u

### Story 2.5: GLightbox Integracija

As a **posetilac**, I want **klik na sliku otvara Lightbox sa navigacijom**, so that **mogu detaljno da pregledam slike proizvoda**.

**Acceptance Criteria:**

**Given** Static struktura iz Epic 1  
**When** download-ujem GLightbox 3.x u `static/vendor/glightbox/`, kreiram `static/js/lightbox-init.js` koji inicijalizuje Lightbox za sve `<a class="glightbox" href="image.jpg">` linkove na strani  
**Then** klik na sliku u galeriji otvara Lightbox modal sa swipe support  
**And** Tab/Arrow keys navigiraju prev/next  
**And** Esc zatvara, focus se vraća na element koji je otvorio  
**And** Lightbox ima `role="dialog"` + `aria-modal="true"` + focus trap  
**And** `prefers-reduced-motion: reduce` smanjuje animacije

### Story 2.6: Brand Listing Strana sa Grid/Extended Layout-om

As a **Marko (poljoprivrednik)**, I want **da vidim sve modele jednog brenda grupisane po seriji sa različitim layout-om**, so that **mogu lakše da pregledam i poredim modele**.

**Acceptance Criteria:**

**Given** Modeli iz Story 2.1, 2.2  
**When** posetim `/sr/traktori/agri-tracking/`  
**Then** stranica prikazuje: hero overlay card sa brand logo + slogan + Repeating Element watermark, sekcija sa 4 statistike-medaljona (count-up animacija), citat banner, modeli grupisani po seriji  
**And** ako serija ima `layout_mode="grid"`, modeli se prikazuju kao 2-col kartice sa slikom + nazivom + CTA "OPŠIRNIJE"  
**And** ako serija ima `layout_mode="extended"`, svaki model je u 1 redu sa krupnom slikom levo i akordion-tabelom specifikacija desno  
**And** slider testimonijala (sa pause/play kontrolom) na dnu  
**And** "Preuzmi katalog" CTA banner sa wave divider top  
**And** Lighthouse a11y skor ≥ 95

### Story 2.7: Product Detail Strana

As a **Marko**, I want **kompletnu stranicu modela sa specifikacijama i mogućnošću kontakta**, so that **mogu da donesem informisanu odluku o kupovini**.

**Acceptance Criteria:**

**Given** Product modeli iz Story 2.2 + Image pipeline 2.3 + PDF 2.4 + Lightbox 2.5  
**When** posetim `/sr/proizvod/agri-tracking-tb804/`  
**Then** stranica prikazuje: hero overlay card sa brand logo + naziv modela + do 3 bullet ključnih karakteristika preko Repeating Element-a; sekcija "Opis proizvoda"; karusel galerije (`<picture>` sa srcset) — klik otvara Lightbox; akordion specifikacije (Motor default-open sa `+/-` toggle, ostale zatvorene), prazne sekcije se skrivaju; Brošura card (cover-thumbnail + "X.X MB, PDF" + CTA-light PREUZMI); slični modeli sekcija (FR-20 hibrid logika: ako Product.ProductSimilar set nije prazan koristi manual, inače auto po brendu/seriji); slider testimonijala "Iz prve ruke"  
**And** Variant selektor sekcija renderuje SAMO ako Product ima ≥1 ProductVariant; klik na variant kartu otvara Lightbox zoom (bez side-effects, no state change)  
**And** Empty stanja (no variants → sakriven, no testimonials → sakriven) se poštuju  
**And** Stranica koristi semantic HTML5 (`<article>`, `<section>`, `<aside>` gde odgovara)

### Story 2.8: Tractor Listing Strana sa HTMX Filterima

As a **Marko**, I want **da filtriram traktore po konjskoj snazi i ceni**, so that **brzo nalazim modele koji odgovaraju mojim potrebama**.

**Acceptance Criteria:**

**Given** Brand listing iz Story 2.6 + Product modeli  
**When** posetim `/sr/traktori/`, podesim range slider snage na 60 KS i range slider cene na 25.000 EUR  
**Then** lista modela se ažurira preko HTMX-a bez page reload-a (debounce 300ms)  
**And** aria-live region najavi "Pronađeno X rezultata"  
**And** URL query parametri reflektuju aktivne filtere (deljivo)  
**And** ako 0 rezultata, prikazuje se empty state sa CTA "RESETUJ FILTERE"  
**And** Brendovi su prikazani kao klikabilni logo header iznad liste  
**And** Pri reload-u sa query parametrima, filteri se restore-uju u UI

### Story 2.9: Used Machinery Listing sa Filterima

As a **posetilac**, I want **da pregledam polovnu mehanizaciju sa filterima po kategoriji, brendu, ceni, godini, stanju**, so that **mogu da nađem dostupnu polovnu opremu**.

**Acceptance Criteria:**

**Given** Story 2.8 patern HTMX filtera  
**When** posetim `/sr/mehanizacija/polovna/`  
**Then** filteri: Kategorija (dropdown), Brend (dropdown), Cena (range slider min-max), Godina (range slider), Stanje (dropdown)  
**And** Paginacija 12 stavki/strani  
**And** Default sort: po datumu dodavanja (najnovije prvo); user može da bira: cena asc/desc, godina desc  
**And** URL query parametri reflektuju sort + paginate + filtere  
**And** Empty state pri 0 rezultata: poruka "Trenutno nemamo polovne mehanizacije u ponudi" sa CTA "POGLEDAJ NOVE TRAKTORE"

### Story 2.10: Jeegee Priključna Mehanizacija Strana

As a **posetilac**, I want **da otvorim Jeegee stranu i vidim 3 kategorije priključne mehanizacije**, so that **mogu da navigiram do potrebne kategorije**.

**Acceptance Criteria:**

**Given** Brand modeli iz Story 2.1  
**When** posetim `/sr/mehanizacija/prikljucna/`  
**Then** stranica prikazuje: Jeegee hero overlay card sa **plavom varijantom** Repeating Element-a; 3 kategorije kao kartice (Osnovna obrada zemljišta / Priprema zemljišta / Mašine za setvu) sa ikonom + nazivom + opisom + CTA  
**And** Klik na kategoriju vodi na `/sr/mehanizacija/prikljucna/<kategorija-slug>/`

### Story 2.11: Subcategory Listing (4-nivoa hijerarhija)

As a **posetilac**, I want **da pregledam mašine kategorisane po nameni i debljini grede**, so that **brzo dolazim do tipova koji me zanimaju**.

**Acceptance Criteria:**

**Given** Subcategory modeli iz Story 2.1  
**When** navigiram kroz `/sr/mehanizacija/prikljucna/osnovna-obrada/` → vidi Plugove, Podrivače, Grubere  
**And** `/sr/mehanizacija/prikljucna/osnovna-obrada/plugovi/` → vidi Plugove ravnjake i Plugove obrtače  
**And** `/sr/mehanizacija/prikljucna/osnovna-obrada/plugovi-obrtaci/` → grupisani po debljini grede (90×90, 100×100, 120×120, 140×140, 160×160)  
**Then** Svaki nivo prikazuje modele kao kartice sa slikom, nazivom, ključnim specifikacijama, CTA  
**And** Hijerarhija je do 4 nivoa duboka (Kategorija → Podkategorija → Pod-podkategorija → grupisanje po atributu)  
**And** Breadcrumb navigacija na vrhu

### Story 2.12: HZM Radne Mašine + Tulip MIX Prikolice Strane

As a **posetilac**, I want **da pregledam HZM utovarivače i Tulip prikolice**, so that **vidim ostatak portfolija**.

**Acceptance Criteria:**

**Given** Brand modeli iz Story 2.1  
**When** posetim `/sr/mehanizacija/radne-masine/`  
**Then** HZM hero card + 4 potkategorije (Mini utovarivači, Utovarivači bez teleskopa, Teleskopski utovarivači, Telehendleri)  
**And** Klik na potkategoriju vodi na listing modela u toj potkategoriji  
**When** posetim `/sr/mehanizacija/mix-prikolice/`  
**Then** Tulip hero + 2 modela (6 kubika, 8 kubika) + uporedna dimenziona tabela (DESIGN.md token tabela layout) + sekcija "Zadovoljni kupci" + "Preuzmi katalog" CTA

### Story 2.13: Global Search sa PostgreSQL FTS

As a **posetilac**, I want **da koristim search ikonu u header-u da pronađem proizvod ili objavu po ključnoj reči**, so that **brzo dolazim do željenog sadržaja**.

**Acceptance Criteria:**

**Given** Product modeli iz Story 2.2 (sa search_vector field-om dodatim u migraciji)  
**When** kliknem search ikonu u header-u  
**Then** ikona ekspanduje u inline tekstualno polje (slide-in 200ms)  
**And** Kucanje min 2 znaka pokreće HTMX request sa debounce 300ms  
**And** PostgreSQL FTS upit (`SearchVector` na name + description) + diacritic-insensitive (`unaccent` extension) + case-insensitive  
**And** Rangiranje po relevance: match u name > match u description; tie-break po datumu (najnoviji prvi za blog, po datumu dodavanja za proizvode)  
**And** Dropdown prikazuje max 5 rezultata grupisanih po tipu (Proizvodi / Objave); aria-live najavi "X predloga"  
**And** Empty state: "Nema rezultata za '{query}'" + CTA blok sa popularnim kategorijama + brendovima  
**And** Search je locale-aware (vraća rezultate samo na trenutnom jeziku)  
**And** Esc zatvara search, fokus se vraća na ikonu

---

## Epic 3: Home & Static Pages

### Story 3.1: Home Strana sa Svim Sekcijama

As a **posetilac**, I want **reprezentativnu Početnu sa pregledom kompanije i ponude**, so that **brzo vidim šta Ćorić Agrar nudi**.

**Acceptance Criteria:**

**Given** Komponente iz Epic 1 + modeli iz Epic 2  
**When** posetim `/sr/`  
**Then** strana prikazuje sekcije u redu: Hero (full-width slika traktora sa sloganom „Prijatelj koji razume zemlju!" preko Repeating Element-a + brand lockup); „O nama" intro blok (naslov + kratak tekst + CTA „Saznaj više" → /o-nama); sekcija Traktori (svi aktivni brendovi sa logo + slika + CTA OPŠIRNIJE; brendovi sa `is_coming_soon=True` imaju pill-badge „Uskoro"); sekcija Priključna mehanizacija (Jeegee baner sa CTA); sekcija Radne mašine (HZM kategorije sa Repeating Element po kategoriji); Polovna mehanizacija (baner sa CTA); „Priče sa polja" preview (wave divider top, slika pozadina, 2 najnovije blog kartice — placeholder Lorem Ipsum dok Epic 5 nije gotov); Footer  
**And** Sve sekcije su responzivne (mobile stack, desktop multi-col)  
**And** Klik na brand logo ili sliku vodi na brand stranu (svaka zona klikabilna)

### Story 3.2: O nama Strana

As a **posetilac**, I want **da pročitam priču kompanije sa vremenskom lentom i galerijom**, so that **gradim poverenje pre kontakta**.

**Acceptance Criteria:**

**Given** Komponente iz Epic 1  
**When** posetim `/sr/o-nama/`  
**Then** strana prikazuje: full-screen hero (video ili slika sa sloganom preko); duži tekst o kompaniji na beloj pozadini sa transparentnim uvećanim logom kao dekorativnim elementom; interaktivna SVG vremenska lenta sa min 3 događaja (godina + naslov + opis), animirana pri scroll-into-view kroz `IntersectionObserver` (800ms ease-in-out po segmentu, instant ako `prefers-reduced-motion: reduce`); masonry galerija fotografija (različite visine, zbijene), klik otvara GLightbox sa navigacijom  
**And** Sadržaj se uređuje kroz admin (CMS — pravi Epic 8 8.8, za sada Lorem Ipsum)  
**And** Vremenska lenta i galerija imaju `aria-hidden="true"` na dekorativnim SVG elementima

### Story 3.3: Kontakt Strana sa Formom i Mapom

As a **posetilac**, I want **da nađem kontakt informacije, formu, i lokaciju**, so that **mogu da kontaktiram firmu na način koji mi odgovara**.

**Acceptance Criteria:**

**Given** Forma iz Epic 4 (parallel dev) ili stub iz Story 4.2  
**When** posetim `/sr/kontakt/`  
**Then** strana prikazuje: kontakt info sekciju (adresa, telefoni prodaja+servis, email, radno vreme, social linkovi) iz `SiteSettings` modela; kontakt forma (FR-5 — povezana sa Story 4.2 ContactForm); ugrađen Google Maps iframe sa pin-om  
**And** Google Maps koristi env-var API key, embed bez JS dep-a  
**And** Forma prati HTMX pattern iz Story 4.6

### Story 3.4: SiteSettings Model + Inicijalni Admin

As a **dev**, I want **SiteSettings model za globalna podešavanja (kontakt info, radno vreme, social)**, so that **kontakt strana i footer čitaju iz jedne autoritativne lokacije**.

**Acceptance Criteria:**

**Given** Project iz Epic 1  
**When** kreiram `apps/pages/models.py` sa `SiteSettings` singleton (django-solo ili custom: addresses, phone_sales, phone_service, email, working_hours, social_facebook, social_youtube, social_instagram, logo, favicon, hero_image_default)  
**And** prilagodim Django admin tako da postoji samo jedna SiteSettings instanca (nema dodavanja, samo edit)  
**And** kreiram `apps/pages/templatetags/site_settings.py` sa `{% site_setting "phone_sales" %}` template tag-om  
**Then** Footer i Kontakt strana koriste site_setting template tag umesto hard-coded vrednosti  
**And** Pre prvog deploy-a, postoji fixture sa default SiteSettings instancom

---

## Epic 4: Lead-gen Forms & Email Delivery

### Story 4.1: Lead Model + SMTP Setup

As a **dev**, I want **Lead model i SMTP transport konfiguraciju**, so that **sve forme imaju jedinstveno mesto za skladištenje i email putem provider-a**.

**Acceptance Criteria:**

**Given** Project iz Epic 1  
**When** kreiram `apps/forms/models.py` sa `Lead` (form_type choice [contact/model_inquiry/service_request/part_request], name, email, phone, message, data JSONField za form-specific fields, photo FileField nullable, created_at, ip_address, locale) i `apps/forms/notifications.py` sa `send_lead_email(lead)` helper-om koji koristi `django-anymail`  
**And** konfigurišem u settings: `EMAIL_BACKEND = 'anymail.backends.resend.EmailBackend'`, env-vars `ANYMAIL_RESEND_API_KEY`, `DEFAULT_FROM_EMAIL`, `LEAD_EMAIL_RECIPIENT` (admin podešavanje, env baseline)  
**Then** `python manage.py shell` testira `Lead.objects.create(...)` + `send_lead_email(lead)` u dev (console backend) i u staging (Resend test)  
**And** Email template `templates/emails/lead_received.html` koristi `{% extends "emails/base_email.html" %}` i Django i18n  
**And** Subject email-a je lokalizovan po `lead.locale`

### Story 4.2: Opšta Kontakt Forma (FR-5)

As a **posetilac**, I want **da pošaljem opšti upit preko forme na Kontakt strani**, so that **mogu da kontaktiram firmu bez telefoniranja**.

**Acceptance Criteria:**

**Given** Lead model + SMTP iz Story 4.1  
**When** posetim `/sr/kontakt/` i pošaljem formu sa imenom, emailom, telefonom, porukom  
**Then** Forma submit-uje preko HTMX `hx-post="/sr/htmx/forme/kontakt/"`  
**And** Server-side validation (Django form) + client-side HTML5  
**And** Uspeh: forma se zameni sa partial-om "Hvala! Vaš upit je primljen." (success state)  
**And** Greška: forma se rerender-uje sa polja u `error` stanju + `aria-live="assertive"` summary  
**And** Email stiže na `LEAD_EMAIL_RECIPIENT` sa subject „[Ćorić Agrar] Novi kontakt: {name}"  
**And** Lead.form_type = 'contact' u DB

### Story 4.3: Model Inquiry Form sa Auto-popunjenim Modelom

As a **Marko**, I want **da pošaljem upit za konkretan model direktno sa stranice proizvoda, sa model poljem već popunjenim**, so that **brzo dobijam ponudu bez ponavljanja**.

**Acceptance Criteria:**

**Given** Product detail strana iz Story 2.7  
**When** kliknem CTA „Pošalji upit" ili skroluje do forme na product stranici  
**Then** Forma ima 5 polja: Ime i prezime *, Email *, Telefon, Model (auto-popunjen iz `request.path` parsiranja, readonly), Poruka  
**And** Submit preko HTMX → Lead.form_type = 'model_inquiry', Lead.data = {"product_slug": "agri-tracking-tb804"}  
**And** Email subject „[Ćorić Agrar] Upit za model: Agri Tracking TB804"  
**And** Uspeh state ima telefon broj za hitne pozive

### Story 4.4: Servisni Zahtev Form sa Foto Upload-om

As a **Stojan**, I want **da prijavim servisni kvar sa fotografijom sa mobilnog**, so that **servis ima sve informacije pre nego što me pozove**.

**Acceptance Criteria:**

**Given** Story 4.1, Image validation iz 2.3  
**When** posetim `/sr/servis/` i popunim formu  
**Then** Polja: Ime *, Telefon *, Email, Vrsta mehanizacije (dropdown: Traktor / Priključna / Radna mašina / Ostalo), Brend+model (free text), Opis kvara *, Foto (opciono, multi-upload do 3 slike)  
**And** Foto upload prihvata JPG/PNG, validira MIME pre slanja, max veličina 5MB po fajlu  
**And** Ako file > limit, greška PRE slanja sa konkretnim limitom („Slika je veća od 5 MB. Probajte manju.")  
**And** Form submit → Lead.form_type = 'service_request', photo polje postavljeno  
**And** Email sa attach-ovanim slikama stiže na `SERVICE_EMAIL_RECIPIENT`  
**And** Mobile-specific UX: form polja stack-ovana, submit dugme full-width, loading state vidljiv

### Story 4.5: Rezervni Delovi Form

As a **kupac**, I want **da poručim rezervni deo preko forme sa detaljima i opcijama plaćanja**, so that **dobijam tačnu ponudu**.

**Acceptance Criteria:**

**Given** Story 4.1  
**When** posetim `/sr/servis/rezervni-delovi/` i popunim formu  
**Then** Polja: Model traktora *, Rezervni deo *, Dodatni opis (opc.), Slika (opc., max 1), Ime *, Telefon *, Email *, Način plaćanja (dropdown: pouzeće / predračun), Način preuzimanja (dropdown: dostava / lično), Napomena (opc.)  
**And** Submit → Lead.form_type = 'part_request', svi specifični podaci u Lead.data JSON  
**And** Email subject „[Ćorić Agrar] Upit za rezervni deo: {part_name} ({tractor_model})"

### Story 4.6: HTMX Form Patterns + aria-live OOB + Rate Limiting

As a **dev**, I want **standardizovan HTMX form pattern sa aria-live announcements i rate limit-om**, so that **sve forme imaju konzistentan UX i a11y, i odbrana od abuse-a**.

**Acceptance Criteria:**

**Given** Forme iz 4.2-4.5  
**When** dodam u sve form views: `@ratelimit(key='ip', rate='10/15m')` decorator iz `django-ratelimit`  
**And** sve form response partials imaju `hx-swap-oob` element ciljajući `#aria-live` region sa kratkom porukom  
**Then** 10 pokušaja form submit u 15min sa istog IP-a vraća HTTP 429 sa porukom „Probajte ponovo kasnije"  
**And** Posle svakog success-a, screen reader najavi „Forma poslata"  
**And** Posle svake greške, screen reader najavi „Greška pri slanju, proverite polja"  
**And** Pattern dokumentovan u `apps/forms/views.py` kao reusable mixin/decorator  
**And** CSRF token uvek prisutan u svim formama

---

## Epic 5: Blog (Priče sa polja)

### Story 5.1: BlogPost + Category + Tag Modeli + Admin Stub

As a **dev**, I want **Blog modele za organizaciju objava**, so that **kasniji story-ji mogu da renderuju blog**.

**Acceptance Criteria:**

**Given** Project iz Epic 1  
**When** kreiram `apps/blog/models.py` sa: `Post` (slug, title, perex, body, main_image, FK Category, M2M Tag, FK author, status, published_at, created_at), `Category` (name, slug, description), `Tag` (name, slug)  
**And** dodam `apps/blog/translation.py` za title, perex, body, Category.name/description, Tag.name  
**Then** Migration kreira tabele sa `_sr/_hu/_en` suffixima  
**And** Inicijalni `apps/blog/admin.py` registruje Post/Category/Tag (full CRUD dolazi u Epic 8 8.7)  
**And** `Post.get_absolute_url()` vraća `/blog/<slug>/`  
**And** PublishedManager filtrira `status='published'` i `published_at__lte=now`

### Story 5.2: Blog Index Strana sa Paginacijom + Filter

As a **posetilac**, I want **da listam blog objave i filtriram po kategoriji**, so that **lakše nalazim teme koje me zanimaju**.

**Acceptance Criteria:**

**Given** Modeli iz Story 5.1  
**When** posetim `/sr/blog/`  
**Then** Lista objava (najnovije prvo) kao kartice (naslovna slika, datum, naslov, perex, CTA "SAZNAJ VIŠE")  
**And** Paginacija 10 objava/strani  
**And** Filter po kategoriji (dropdown ili tabovi)  
**And** Klik na karticu vodi na `/sr/blog/<slug>/`  
**And** Mobile: 1 kolona kartica; desktop: 2-3 kolone  
**And** Empty state ako nema objava: „Uskoro nove priče sa polja" + CTA „POVRATAK NA POČETNU"

### Story 5.3: Blog Post Detail Strana

As a **posetilac**, I want **da pročitam pojedinačnu objavu sa slikama, videom u tekstu i social share opcijama**, so that **mogu da podelim korisnu informaciju**.

**Acceptance Criteria:**

**Given** Modeli iz Story 5.1  
**When** posetim `/sr/blog/agrotehnicke-mere-jesenje-setve/`  
**Then** Strana prikazuje: naslovnu sliku, datum + autor + kategorija meta, naslov, telo (rich text sa inline slikama i video embed), sekcija „Slične objave" (2-4 objave iz iste kategorije)  
**And** Social share dugmad (Facebook, Viber, WhatsApp, Copy link) — pozicija sticky leva strana na desktop, ispod naslova na mobile  
**And** Klik na kategoriju vodi na `/sr/blog/kategorija/<slug>/`  
**And** Klik na tag vodi na `/sr/blog/tag/<slug>/`  
**And** Meta title/description popunjeni iz Post.title + Post.perex (override-ovi dolaze u Epic 6)

### Story 5.4: Footer Dynamic „Najnovije vesti" Kolona

As a **posetilac**, I want **da iz footera direktno dođem do najnovijih blog objava**, so that **vidim svežu sadržaj sa bilo koje strane**.

**Acceptance Criteria:**

**Given** Footer iz Story 1.8 + Post modeli iz 5.1  
**When** ažuriram `apps/blog/context_processors.py` da exposes `latest_blog_posts` (3 najnovije objavljene po `created_at`)  
**And** ažuriram `templates/partials/footer.html` da renderuje 3 stavke iz `latest_blog_posts` kao linkove ka post detail-u  
**Then** Footer „Najnovije vesti" kolona prikazuje 3 najnovije objavljene blog objave  
**And** Ako blog ima manje od 3 objave, prikazuje samo koliko ima  
**And** Ako ima 0 objava, kolona renderuje placeholder „Uskoro nove priče"

---

## Epic 6: SEO & Discoverability

### Story 6.1: SeoMeta Model + Per-page Admin

As a **admin**, I want **da unesem meta title i description za svaku stranu i proizvod**, so that **kontrolišem kako se sajt prikazuje u Google rezultatima**.

**Acceptance Criteria:**

**Given** Modeli iz Epic 2, 3, 5  
**When** kreiram `apps/seo/models.py` sa `SeoMeta` (`content_type` + `object_id` Generic FK, meta_title, meta_description, og_image FileField nullable, exclude_from_sitemap flag)  
**And** dodam `apps/seo/translation.py` za meta_title, meta_description  
**Then** Migration kreira tabelu sa _sr/_hu/_en suffixima  
**And** Generic admin inline omogućava unos SeoMeta na Page/Product/Brand/Post admin-u (Epic 8 polish)  
**And** `apps/seo/templatetags/seo_meta.py` sa `{% seo_meta object %}` template tag-om renderuje `<title>`, `<meta name="description">`, `<link rel="canonical">`, `<meta property="og:image">` u `<head>`  
**And** Ako SeoMeta nije unesen, sistem koristi default (`object.name` + naziv firme)  
**And** Soft warning u admin-u kada meta_title > 60 chars ili meta_description > 160 chars

### Story 6.2: Sitemap Auto-generation sa Hreflang

As a **search engine bot**, I want **dinamičan sitemap.xml sa hreflang oznakama**, so that **Google indeksira sve sadržajne tipove i jezičke varijante**.

**Acceptance Criteria:**

**Given** SEO model iz Story 6.1  
**When** kreiram `apps/seo/sitemaps.py` sa Django Sitemap klasama za: Page, Product, Brand, Series, Subcategory, BlogPost — sve klase implementiraju `alternates` za hreflang per locale  
**And** registrujem u `config/urls.py`: `path('sitemap.xml', sitemap, {'sitemaps': sitemaps_dict})`  
**Then** `https://example.com/sitemap.xml` vraća validan XML sa svim objavljenim sadržajem  
**And** Svaka URL stavka ima `<xhtml:link rel="alternate" hreflang="sr|hu|en">` za sve 3 verzije  
**And** Stavke sa `exclude_from_sitemap=True` se NE pojavljuju  
**And** Sitemap je validan po sitemap.org schema (testirati sa external validator-om)

### Story 6.3: Robots.txt + Open Graph + Twitter Card Meta

As a **search engine bot ili social media platforma**, I want **robots.txt i Open Graph meta tagove**, so that **mogu pravilno da indeksiram i renderujem preview**.

**Acceptance Criteria:**

**Given** SEO model iz 6.1  
**When** kreiram `apps/seo/views.py:robots_txt` view koji renderuje statički robots.txt template + sitemap link  
**And** ažuriram `templates/base.html` da uključi Open Graph (`og:title`, `og:description`, `og:image`, `og:type`, `og:url`) i Twitter Card meta tagove iz `{% seo_meta object %}` template tag-a  
**Then** `https://example.com/robots.txt` vraća validan robots format koji dozvoljava ključne strane i navodi sitemap.xml lokaciju  
**And** Svaka strana ima OG i Twitter meta u `<head>`  
**And** OG image fallback je `static/img/og-default.jpg` ako SeoMeta nema unesen og_image

### Story 6.4: Redirect Manager (301)

As a **admin**, I want **da kreiram 301 redirect pravila za stare URL-ove**, so that **mogu da preusmeravam linkove bez gubitka SEO ranking-a**.

**Acceptance Criteria:**

**Given** SEO app  
**When** kreiram `apps/seo/models.py:Redirect` (old_path, new_path, created_at, is_active) i `apps/seo/middleware.py:RedirectMiddleware`  
**And** registrujem middleware ranije od `LocaleMiddleware` u settings  
**Then** Pristup starom path-u vraća HTTP 301 sa novim Location header-om  
**And** Middleware ne procesira admin URL-ove (`/admin-coric/`)  
**And** Admin može da listuje, doda, izmeni, deaktivira redirect pravila

### Story 6.5: i18n Fallback Marker (ⓘ Tooltip)

As a **posetilac**, I want **da vidim diskretan indikator kada čitam sadržaj koji je fallback na srpski**, so that **razumem zašto je tekst na drugom jeziku od ostalog**.

**Acceptance Criteria:**

**Given** i18n iz Story 1.4 + Translated models iz Epic 2/3/5  
**When** kreiram `apps/core/templatetags/i18n_fallback.py` sa `{% translated_field obj 'name' %}` template tag-om koji proverava da li trenutna locale verzija polja postoji ili pada na sr  
**And** ako pada na sr, tag rendera tekst sa `<span class="coric-fallback-marker" tabindex="0" aria-describedby="fallback-tooltip-...">{text} <i class="bi-info-circle" aria-hidden="true"></i></span>`  
**Then** Posetilac na `/hu/proizvod/agri-tracking-tb804/` vidi srpski naziv (jer hu nije popunjen) sa ⓘ ikonom pored  
**And** Hover/click na ikonu otvara tooltip „Sadržaj na srpskom — još nije preveden" (lokalizovano)  
**And** Polje koje koristi fallback ima `lang="sr"` atribut

### Story 6.6: SEO Hreflang HTML Tagovi + Locale-aware Slug-ovi

As a **search engine**, I want **hreflang HTML tagove na svakoj strani**, so that **vidim alternative jezičke verzije i ne penalizujem za duplicate content**.

**Acceptance Criteria:**

**Given** i18n + SEO iz 6.1-6.5  
**When** kreiram `apps/seo/templatetags/hreflang.py` sa `{% hreflang_links %}` template tag-om koji renderuje `<link rel="alternate" hreflang="sr|hu|en|x-default" href="..."/>` u `<head>`  
**Then** Svaka strana ima 4 hreflang link-a (sr, hu, en, x-default → sr)  
**And** `x-default` ukazuje na sr verziju  
**And** Slug-ovi koriste ASCII transliteration (`Ć → c`) — verifikovati kroz `apps/core/utils.py:safe_slugify`

---

## Epic 7: GDPR & Privacy

### Story 7.1: CookiePolicy Model + Admin

As a **admin**, I want **da uredim sadržaj politike kolačića kroz UI**, so that **mogu da održavam pravni dokument bez code change-a**.

**Acceptance Criteria:**

**Given** Project iz Epic 1  
**When** kreiram `apps/gdpr/models.py:CookiePolicy` (title, body rich text, last_updated) i odgovarajući admin  
**And** dodam `apps/gdpr/translation.py` za title, body  
**Then** Admin može da edituje politiku, polje per locale  
**And** Stranica `/sr/politika-kolacica/` renderuje sadržaj iz CookiePolicy modela  
**And** Default fixture pre prvog deploy-a sadrži Lorem Ipsum politiku

### Story 7.2: GDPR Banner sa Consent Management

As a **posetilac**, I want **da se prikazuje GDPR baner sa opcijama prihvatanja**, so that **kontrolišem koje kolačiće dozvoljavam**.

**Acceptance Criteria:**

**Given** CookiePolicy iz Story 7.1  
**When** kreiram `apps/gdpr/templatetags/gdpr_banner.py` sa `{% gdpr_banner %}` template tag-om i `apps/gdpr/views.py:SetConsentView`  
**Then** GDPR baner se prikazuje pri prvoj poseti (ako consent kolačić nije postavljen)  
**And** Posetilac može da: prihvati sve, odbije sve (osim neophodnih), ili podesi po kategoriji (Neophodan / Analitički / Marketing)  
**And** Izbor se čuva u long-lived kolačiću (`consent_state`, 365 dana)  
**And** Baner ima `role="dialog"` + `aria-labelledby` + `aria-modal="false"` (non-blocking)  
**And** Esc dugme = "Odbij sve" akcija  
**And** Klik na "Više info" vodi na `/sr/politika-kolacica/`

### Story 7.3: GA4 + FB Pixel Template Tagovi (Conditional Render)

As a **dev**, I want **conditional rendering tracking pixels-a bazirano na consent stanju**, so that **poštujem GDPR i ne učitavam pixel pre saglasnosti**.

**Acceptance Criteria:**

**Given** Consent state iz Story 7.2  
**When** kreiram `apps/gdpr/templatetags/tracking.py` sa `{% ga_pixel %}` i `{% fb_pixel %}` template tagovima koji čitaju `request.consent_state` (set u `apps/gdpr/context_processors.py:consent_state`)  
**Then** `{% ga_pixel %}` renderuje GA4 script SAMO ako `consent_state.analytical == True`  
**And** `{% fb_pixel %}` renderuje FB Pixel script SAMO ako `consent_state.marketing == True`  
**And** Network request ka googleanalytics.com / facebook.com NE postoji u dev tools pre prihvatanja consent-a  
**And** Posle prihvatanja consent-a, page refresh aktivira pixel-e (verify u Network tab)

### Story 7.4: Politika Kolačića + Politika Privatnosti Statičke Strane

As a **posetilac**, I want **da pristupim politici kolačića i politici privatnosti**, so that **razumem moja prava**.

**Acceptance Criteria:**

**Given** CookiePolicy iz Story 7.1 + Page modeli iz Epic 3 (SiteSettings nije dovoljan, treba PrivacyPolicy ili Page model)  
**When** kreiram `apps/pages/models.py:Page` (slug, title, body rich text)  
**And** dodam admin za uređivanje + 2 default Page instance (slug='politika-privatnosti' i ako treba 'politika-kolacica')  
**Then** `/sr/politika-privatnosti/` renderuje sadržaj  
**And** Footer ima link ka obe stranice  
**And** Pre prvog deploy-a, fixture popunjava obe sa Lorem Ipsum baseline

---

## Epic 8: Admin Dashboard & Content Management

### Story 8.1: Custom Admin Login sa Rate Limiting

As a **admin**, I want **siguran login URL koji nije /admin/**, so that **bot-ovi ne mogu trivijalno da probaju credential-e**.

**Acceptance Criteria:**

**Given** Project iz Epic 1  
**When** ažuriram `config/urls.py` da admin bude na `/admin-coric/` umesto default `/admin/`  
**And** instaliram `django-axes` i konfigurišem 5 failed pokušaja u 15 min IP-blokira na 1h  
**And** kreiram `apps/accounts/forms.py:AdminLoginForm` (email-as-username umesto username)  
**Then** Pristup `/admin/` vraća 404  
**And** Pristup `/admin-coric/` prikazuje login formu  
**And** 6. pokušaj sa pogrešnim password-om vraća error sa lock-out indikatorom  
**And** Pri uspeh login-u, session timeout je 4h (`SESSION_COOKIE_AGE = 14400`)

### Story 8.2: User Accounts + RBAC (Superadmin / Editor Groups)

As a **Superadmin**, I want **da kreiram Editor naloge sa ograničenim permisijama**, so that **content menadžer može da unosi ali ne i da menja korisnike**.

**Acceptance Criteria:**

**Given** Custom login iz Story 8.1  
**When** kreiram `apps/accounts/permissions.py` sa Group definicijama: Superadmin (all permissions), Editor (CRUD na Product, Brand, Category, Post, Page ali NE na User/Group)  
**And** dodam migration koji kreira Groups pri prvom migrate  
**And** kreiram `apps/accounts/admin.py` koji extends Django UserAdmin sa Group dodelom  
**Then** Superadmin može da kreira korisnika, dodeli mu Editor group  
**And** Editor user vidi admin panel ali nema pristup `/admin-coric/auth/user/` (`PermissionDenied`)  
**And** Editor može da CRUD-uje sve content modele  
**And** Promena lozinke je dostupna oba

### Story 8.3: Admin Dashboard sa Segmentovanim Lead Count-om

As a **Marijana**, I want **dashboard sa statistikama i brzim akcijama**, so that **brzo vidim stanje sajta posle login-a**.

**Acceptance Criteria:**

**Given** Lead modeli iz Epic 4, Product/Blog modeli iz Epic 2/5  
**When** kreiram `apps/admin_ext/views.py:DashboardView` (override `AdminSite.index`) sa template-om `admin/index.html`  
**And** dodam `apps/admin_ext/stats.py:get_lead_stats()` koja vraća dict {contact, model_inquiry, service_request, part_request, total} za current month  
**Then** Dashboard prikazuje 4 segmenta sa brojevima + total iznad  
**And** Posete za 7/30 dana iz `apps/admin_ext/analytics.py:get_ga_visits()` (read-only GA Reporting API)  
**And** Ukupan broj objavljenih proizvoda + blog objava  
**And** Brze akcije: "Dodaj proizvod" + "Dodaj blog objavu" (vode direktno na admin add view)  
**And** Dashboard se učitava bez GA API failure-a (graceful fallback ako GA API timeout)

### Story 8.4: Brand CRUD Admin

As a **Marijana**, I want **da unosim/menjam brendove sa svim atributima**, so that **mogu da održavam katalog**.

**Acceptance Criteria:**

**Given** Brand modeli iz Story 2.1  
**When** prilagodim `apps/brands/admin.py:BrandAdmin` da podrži: tabovi po lokalu (sr/hu/en), upload polja (logo, hero_image, catalog_pdf), brand_color picker (DESIGN.md varijante), statistics JSON editor (4 stavke ikona+broj+label), inline `Series` editor  
**Then** Marijana može da unese kompletan Brand u jednoj formi  
**And** Validacija blokira save bez bar 1 lokalizacije (sr je obavezno za publish)  
**And** Status switching (draft/published/coming_soon) je vidljiv  
**And** Listing strana prikazuje brendove sa statusom + display_order

### Story 8.5: Category + Subcategory CRUD sa Hierarchy

As a **Marijana**, I want **da upravljam kategorijama i potkategorijama sa hijerarhijom**, so that **organizacija mehanizacije ima smisla za korisnike**.

**Acceptance Criteria:**

**Given** Category/Subcategory modeli iz Story 2.1  
**When** prilagodim admin sa `mptt` ili `treebeard` ili Django built-in `ModelAdmin` sa parent FK widget-om  
**Then** Marijana može da kreira hijerarhiju do 3 nivoa  
**And** Drag-and-drop ili order field omogućava prerasporedjivanje  
**And** Translacija polja per locale dostupna  
**And** Brisanje parent kategorije briše i child-ove (cascade ili confirmation)

### Story 8.6: Product CRUD Admin sa Multi-locale

As a **Marijana**, I want **da kompletno unesem proizvod sa galerijom, varijantama, specifikacijama**, so that **stranica proizvoda izgleda profesionalno**.

**Acceptance Criteria:**

**Given** Product modeli iz Story 2.2  
**When** prilagodim `apps/products/admin.py:ProductAdmin` sa inline-ovima za ProductImage, ProductSpecification, ProductBrochure, ProductTestimonial, ProductVariant, ProductSimilar  
**And** koristim `django-tinymce` ili `django-ckeditor-5` za description rich text editor  
**And** Drag-and-drop multi-upload za ProductImage (django-multiupload ili custom JS)  
**And** Tabovi za sr/hu/en jezike (django-modeltranslation default)  
**Then** Marijana može da unese ceo proizvod u jednoj formi sa tab-ovima  
**And** Validacija pre prelaska u "Objavljeno": sr verzija mora imati name, bar 1 slika galerije, bar 1 specifikacija  
**And** Konkretna polja koja fale prikazuju se kao error sa link-om

### Story 8.7: Blog CRUD Admin sa WYSIWYG

As a **Marijana**, I want **da pišem blog objave sa rich text editor-om**, so that **mogu da formatiram tekst i ubacim slike/video**.

**Acceptance Criteria:**

**Given** Blog modeli iz Story 5.1  
**When** prilagodim `apps/blog/admin.py:PostAdmin` sa `django-tinymce` WYSIWYG editorom za polje `body`  
**And** dodam inline-ove za Tag (slobodno dodavanje) i FK Category dropdown  
**And** dodam tabove za sr/hu/en  
**Then** Marijana može da napiše post sa: paragraphima, headings, bold/italic, link, lista, slika inline (upload), video embed (YouTube iframe)  
**And** Status workflow: draft → published (validacija: sr verzija ima title + body + main_image + category)  
**And** `published_at` se postavlja automatski ako prazno pri publish-u

### Story 8.8: Statičke Strane CRUD

As a **Marijana**, I want **da uređujem statičke strane (O nama, Servis, itd.)**, so that **klijent može da menja content bez dev intervencije**.

**Acceptance Criteria:**

**Given** Page model iz Epic 7 7.4  
**When** dodam dodatne field-ove na Page: hero_image, hero_video, sections JSON (za fleksibilan sadržaj O nama strane), gallery_images M2M  
**And** prilagodim PageAdmin sa WYSIWYG za body i sa galerije inline za O nama  
**Then** Marijana može da uredi O nama text + masonry galeriju kroz admin  
**And** Vremenska lenta events (TimelineEvent inline na Page) podržava CRUD (godina, naslov, opis)  
**And** Translacija svih polja per locale

### Story 8.9: SiteSettings + Navigation Menu Admin

As a **Marijana**, I want **da menjam opšta podešavanja sajta i navigacioni meni**, so that **kontakt informacije, GDPR baner tekst i meni stavke ostaju ažurni**.

**Acceptance Criteria:**

**Given** SiteSettings model iz Story 3.4  
**When** Story 3.4 dodaje admin za SiteSettings + dodam fields na model: gdpr_banner_title, gdpr_banner_body, navigation u JSON (za sada statički, v1.1 dinamičan)  
**Then** Marijana može u admin-u da menja: naziv sajta, kontakt, logotip, favicon, hero pozadine, GDPR baner tekst per locale  
**And** Navigacioni meni je za v1 statički kodirani (templates/partials/header.html) — `[NOTE FOR DEV]` v1.1 prevođenje u dinamičan kroz NavigationItem model  
**And** Promena SiteSettings reflektuje se odmah na svim stranama (cache invalidation na save signal)

---

## Epic 9: Go-Live Readiness (Production + Quality)

### Story 9.1: Production Docker Compose + Nginx Config

As a **dev**, I want **production Docker compose sa Nginx reverse proxy**, so that **mogu da deploy-ujem na Hetzner sa security-hardened config-om**.

**Acceptance Criteria:**

**Given** Local Docker iz Story 1.3  
**When** kreiram `compose/production.yml` sa servisima: postgres, django (Gunicorn), nginx, glitchtip (Epic 9.3) + `compose/nginx/nginx.conf` sa HTTPS termination, gzip, static fallback, security headers (X-Frame-Options, X-Content-Type-Options, Referrer-Policy)  
**Then** `docker compose -f compose/production.yml up` pokreće ceo stack lokalno za test  
**And** Nginx forwardu-je sve requeste na Django port 8000  
**And** Static fajlovi serviraju direktno Nginx za max performance  
**And** Gunicorn config (workers, timeout) je tune-ovan za 2vCPU VPS  
**And** `DJANGO_SETTINGS_MODULE=config.settings.production` u env-u

### Story 9.2: Hetzner Deployment Script + SSL

As a **dev**, I want **scriptovan deploy proces na Hetzner VPS sa Let's Encrypt SSL**, so that **deploy je reproducibilan i siguran**.

**Acceptance Criteria:**

**Given** Production compose iz Story 9.1  
**When** kreiram `ops/deploy/deploy.sh` (SSH-ovan na Hetzner box, git pull, docker compose pull, docker compose down + up, migrate, collectstatic) + `ops/nginx/nginx-init.sh` sa `certbot` za Let's Encrypt SSL sa auto-renewal cron-om  
**And** prilagodim GitHub Actions deploy.yml da koristi SSH key da pokrene `ops/deploy/deploy.sh` po push-u na main branch  
**Then** Push na `main` triggeruje automatski production deploy  
**And** HTTPS certifikat se izdaje pri prvom deploy-u i obnavlja se 1x mesečno  
**And** Rollback script `ops/deploy/rollback.sh` može da revertuje na prethodni commit + migrate down

### Story 9.3: GlitchTip 6 Self-host Setup

As a **dev**, I want **GlitchTip self-host za error tracking u prod-u**, so that **vidim uncaught exceptions sa stack trace-om bez plaćanja Sentry SaaS**.

**Acceptance Criteria:**

**Given** Production compose iz Story 9.1  
**When** kreiram `ops/monitoring/glitchtip-compose.yml` (GlitchTip web + worker + postgres + redis, ~512MB RAM allocation) + konfigurišem u `config/settings/production.py`: `SENTRY_DSN = env('GLITCHTIP_DSN')`, instaliram `sentry-sdk[django]`  
**Then** GlitchTip UI dostupan na `https://errors.example.com` (subdomena ili port)  
**And** Trigger-ovanjem 500 greške u Django prod-u (simulirano kroz test view), greška se pojavljuje u GlitchTip dashboard-u  
**And** Email alerting konfigurisan za critical errors (Resend SMTP iz Epic 4)  
**And** Retencija ograničena na 30 dana zbog disk-a

### Story 9.4: UptimeRobot Konfiguracija

As a **dev**, I want **uptime monitoring za 3 environment-a**, so that **dobijam alert čim sajt padne**.

**Acceptance Criteria:**

**Given** Deployed staging i production  
**When** registrujem UptimeRobot free account, kreiram monitor-e za: staging URL, production URL, GlitchTip URL — sa 5 min interval-om  
**Then** UptimeRobot šalje email kada sajt vraća non-200 status  
**And** Maintenance window konfigurisan za regular deploy windows  
**And** Public status page (opciono) deli sa stakeholder-ima

### Story 9.5: pg_dump + restic + Hetzner Storage Box Backup

As a **dev**, I want **automatski dnevni encrypted backup baze i media na off-site storage**, so that **mogu da restore-ujem u slučaju katastrofe**.

**Acceptance Criteria:**

**Given** Production deploy iz Story 9.2  
**When** kreiram `ops/backup/pg_backup.sh` (pg_dump + gzip + restic encrypt + push na Hetzner Storage Box via rclone) i `ops/backup/media_backup.sh` (restic snapshot media volume) i instaliram cron timer (3am daily UTC)  
**Then** Backup arhive su prisutne na Storage Box-u, encrypted (restic native)  
**And** Restic policy retain-uje 7 dnevnih + 4 nedeljnih + 3 mesečnih (do 30 dana effective coverage)  
**And** `ops/backup/restore.sh` može da restore-uje konkretan snapshot na lokal za test  
**And** Backup status (sukces/fail) loguje u GlitchTip pri fail-u

### Story 9.6: Django Logging Konfiguracija

As a **dev**, I want **strukturisan logging sa rotation-om**, so that **mogu da debug-ujem post-mortem bez disk-fill-up-a**.

**Acceptance Criteria:**

**Given** Project iz Epic 1  
**When** konfigurišem u `config/settings/production.py`: `LOGGING` dict sa JSON formatter (python-json-logger), file handler u `/var/log/django/app.log`, log-level INFO za common-app, ERROR za django  
**And** instaliram `logrotate` config: dnevna rotacija, 14 dana retencija, compress  
**Then** Logs su JSON-strukturisan u `/var/log/django/app.log`  
**And** `journalctl -u django` ili Docker `logs` prikazuje structured log-ove  
**And** Logrotate compress-uje dnevno i briše posle 14 dana

### Story 9.7: Sample Seed Data Fixtures

As a **dev**, I want **fixture sa sample podatcima**, so that **prod deploy ima realan content za demo / test**.

**Acceptance Criteria:**

**Given** Svi modeli iz Epic 1-8  
**When** kreiram `tests/fixtures/sample_data.json` sa: 3 brenda (Wuzheng, Agri Tracking, Saillong) + 3 serije + 10-15 proizvoda + 5 polovne mehanizacije + 3-5 blog objava + SiteSettings instanca + 1 Superadmin user  
**Then** `python manage.py loaddata tests/fixtures/sample_data.json` puni bazu bez grešaka  
**And** Sajt nakon load-data prikazuje sve sekcije sa pravim content-om (ne placeholder Lorem Ipsum)  
**And** Slike u fixtures-u koriste relativne path-eve ka `static/img/sample/*`

### Story 9.8: Playwright E2E Testovi za 3 UJ-a

As a **dev**, I want **automatizovan E2E test za 3 ključne user journey-ja**, so that **regression-i na critical path-u se detektuju**.

**Acceptance Criteria:**

**Given** Sve epic-i 1-8 završeni + sample seed data 9.7  
**When** kreiram `tests/e2e/conftest.py` (Playwright fixture + page setup) i 3 test fajla:
- `test_marko_buys_traktor.py` (UJ-1: posetilac filtrira traktore, otvara model, šalje upit za model)
- `test_stojan_service_request.py` (UJ-2: posetilac sa mobile viewport otvara servis, popunjava formu sa fotom, šalje)
- `test_marijana_adds_product.py` (UJ-3: admin loguje, otvara dashboard, dodaje novi proizvod sa galerijom i specifikacijama)  
**Then** `just e2e` pokreće Playwright protiv staging URL-a, sva 3 testa prolaze  
**And** Testovi koriste page object pattern (apps/products/page_object.py itd. ili u tests/e2e/page_objects/)  
**And** CI pipeline pokreće E2E na staging branch push (ne na main, suviše sporo)

### Story 9.9: A11y Audit + Performance Load Test

As a **dev**, I want **audit accessibility-a i performance load test-a pre launch-a**, so that **WCAG 2.1 AA i performance budget targeti su verifikovani**.

**Acceptance Criteria:**

**Given** Staging deploy iz Story 9.2  
**When** pokrenem axe-core ili Pa11y automatski test na ključne strane (/, /traktori, /proizvod/<slug>, /kontakt, /admin-coric/) + Lighthouse CI report  
**Then** Audit pokazuje 0 critical a11y issue-a  
**And** Lighthouse a11y skor ≥ 95 na svim strana  
**And** Lighthouse performance LCP < 2.5s, TTFB < 600ms, total page weight < 1.5MB  
**And** Manualan keyboard-only test 3 UJ-a prolazi (Tab navigates everywhere, Esc closes modals)  
**And** Screen reader (NVDA na Windows) test bar 1 UJ prolazi sa razumevanjem  
**And** Sve fail-ovane stavke evidentno u GitHub Issue za remediation

### Story 9.10: WebP/AVIF + Final Lighthouse Pass

As a **posetilac sa modernim browser-om**, I want **slike u WebP/AVIF formatu kad podržano**, so that **strana se učitava brže**.

**Acceptance Criteria:**

**Given** sorl-thumbnail iz Story 2.3  
**When** dodam u sorl-thumbnail backend config `THUMBNAIL_FORMAT_FALLBACK = ['avif', 'webp', 'jpg']`  
**And** ažuriram template-ove da koriste `<picture>` element sa `<source type="image/avif">` i `<source type="image/webp">` fallback-ovima  
**Then** Modern browser learn `.avif` ili `.webp` (provereno u dev tools Network)  
**And** Legacy browser dobija JPG fallback bez grešaka  
**And** Final Lighthouse pass: a11y ≥ 95, performance LCP < 2.5s, best practices ≥ 90, SEO ≥ 95
