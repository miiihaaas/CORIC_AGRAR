---
title: DESIGN — Ćorić Agrar
status: final
created: 2026-05-27
updated: 2026-05-27
project: CORIC_AGRAR
sources:
  - ../../prds/prd-CORIC_AGRAR-2026-05-27/prd.md
  - ../../briefs/brief-CORIC_AGRAR-2026-05-27/brief.md
  - docs/Dizajn/_HTML/index.html
  - docs/Dizajn/_HTML/traktori.html
  - docs/Dizajn/_HTML/css/
  - docs/Dizajn/_Prikazi strana/Ćorić Agrar - Početna 4.0.jpg
  - docs/Dizajn/_Prikazi strana/Stranica brenda - 4.0.jpg
  - docs/Dizajn/_Prikazi strana/Stranica proizvoda 1.0.jpg
colors:
  brand:
    green-900: "#1f3f2f"     # najtamniji — card bg, footer
    green-800: "#25402f"     # primarni — hero card, nav, dugmadi
    green-600: "#395f48"     # srednji — outlines, secondary surfaces
    green-400: "#4d7e60"     # svetliji — hover states, badges
  accent:
    gold-500: "#e7af12"      # eyebrows, statistike outline, hero naslovi
    lime-500: "#c8d32c"      # hover state, highlights
  brand-specific:
    jeegee-blue: "#00A4E9"   # samo za Ponavljajući element na Jeegee hero
  neutral:
    cream: "#f5f1e8"         # warm surface background
    white: "#ffffff"
    gray-100: "#f4f4f4"
    gray-300: "#d1d1d1"      # dividers only — fail 3:1 vs white, ne za input borders
    gray-500: "#8a8a8a"      # input borders na svetlim pozadinama (3.0:1+ vs white)
    gray-700: "#4a4a4a"
    black: "#0f0f0f"
  semantic:
    text-primary: "#1f3f2f"
    text-on-dark: "#ffffff"
    text-muted: "#4a4a4a"
    border: "#395f48"
    error: "#c0392b"          # text only on light bg (white/cream) — ne na green
    success: "#2d6b2d"        # ~5.2:1 na white (AA pass za normal text)
    focus-ring: "#5a8a6e"     # 3:1+ na green-800/900 i na svetlim pozadinama
typography:
  family:
    primary: "Roboto"        # Google Fonts, 300/400/700
  weight:
    light: 300
    regular: 400
    bold: 700
  scale:                     # rem values (1rem = 16px)
    h1: 3.5                  # ~56px
    h2: 2.5                  # ~40px
    h3: 1.75                 # ~28px
    h4: 1.25                 # ~20px
    body: 1.25               # ~20px (override Bootstrap default)
    small: 1                 # ~16px
    caption: 0.875           # ~14px
  line-height:
    tight: 1.2
    base: 1.5
    relaxed: 1.7
  tracking:
    normal: 0
    wide: 0.05em             # uppercase eyebrows i CTA dugmad
rounded:
  none: "0"
  sm: "6px"
  md: "8px"
  lg: "10px"
  pill: "999px"              # CTA dugmad
  full: "50%"                # avatari, ikonski medaljoni
shadows:
  none: "none"
  sm: "0 1px 3px rgba(31,63,47,0.06)"
  md: "0 2px 8px rgba(31,63,47,0.06)"
  lg: "0 4px 12px rgba(31,63,47,0.08)"
  nav-shrunk: "0 2px 4px rgba(0,0,0,0.1)"
spacing:
  base: "4px"
  scale:                     # Bootstrap-aligned + custom
    "1": "4px"
    "2": "8px"
    "3": "12px"
    "4": "16px"
    "5": "24px"
    "6": "32px"
    "8": "48px"
    "10": "64px"
    "12": "96px"
    section: "80px"          # default vertikalni razmak između sekcija (desktop)
    section-mobile: "48px"
  container:
    max-width: "1200px"
    gutter-desktop: "24px"
    gutter-mobile: "16px"
components:
  button:
    primary:
      bg: "{colors.brand.green-800}"
      text: "{colors.semantic.text-on-dark}"
      radius: "{rounded.pill}"
      padding: "{spacing.scale.3} {spacing.scale.6}"
      tracking: "{typography.tracking.wide}"
      weight: "{typography.weight.bold}"
    secondary:
      bg: "transparent"
      text: "{colors.brand.green-800}"
      border: "2px solid {colors.brand.green-800}"
      radius: "{rounded.pill}"
    cta-light:
      bg: "{colors.accent.gold-500}"
      text: "{colors.brand.green-900}"
      radius: "{rounded.pill}"
  card:
    base:
      bg: "{colors.neutral.white}"
      radius: "{rounded.md}"
      padding: "{spacing.scale.5}"
      shadow: "0 2px 8px rgba(31,63,47,0.06)"
    hero-overlay:
      bg: "{colors.brand.green-800}"
      text: "{colors.semantic.text-on-dark}"
      radius: "{rounded.md}"
      padding: "{spacing.scale.6}"
  repeating-element:           # "Ponavljajući element" iz Glossary
    width-to-height-ratio: "3:2"
    radius: "{rounded.md}"
    corner-lines:
      style: "thin white concentric circles, top-right corner"
      stroke: "1px"
      opacity: 0.5
    bg-default: "{colors.brand.green-800}"
    bg-jeegee: "{colors.brand-specific.jeegee-blue}"
  accordion:
    bg: "transparent"
    border-bottom: "1px solid {colors.brand.green-600}"
    icon: "plus-minus toggle (+/−)"
    default-open: "first section only (Motor)"
  pill-badge:
    bg: "{colors.accent.gold-500}"
    text: "{colors.brand.green-900}"
    radius: "{rounded.pill}"
  wave-divider:
    use: "selective — only 'Priče sa polja' top edge i 'Preuzmi katalog' bottom"
    color: "{colors.brand.green-800}"
  brochure-card:
    bg: "{colors.neutral.white}"
    border: "1px solid {colors.neutral.gray-300}"
    radius: "{rounded.md}"
    padding: "{spacing.scale.5}"
    cover-rotation: "3deg"
    cta: "{components.button.cta-light}"
  stat-medallion:
    size-desktop: "120px"
    size-mobile: "80px"
    outline: "2px solid {colors.accent.gold-500}"
    bg: "transparent (used on green-800 surfaces only)"
    digit-color: "{colors.accent.gold-500}"
    digit-size: "{typography.scale.h1}"
    parent-surface-required: "dark (green-800 or green-900)"
---

# DESIGN — Ćorić Agrar

DESIGN.md je peer-spine sa EXPERIENCE.md. Oba dokumenta imaju prednost u sukobu sa bilo kojim mockup-om ili HTML prototipom.

## Brand & Style

**Ime brenda:** Ćorić Agrar — uvoznik traktora i poljoprivredne mehanizacije za srpsko i regionalno tržište.

**Slogan:** *„Prijatelj koji razume zemlju!"* — pojavljuje se u hero-u Početne strane. Ozbiljan, topao ton — komunicira poverenje između firme i poljoprivrednika.

**Estetika:** Ozbiljna agrarna, prizemljena, ali sa savremenim digitalnim osećajem. Inspiracija — **www.lemken.com** za organizaciju kategorija, vizuelnu hijerarhiju i tipografski pristup (veliki bold naslovi, ozbiljan ton); naša interpretacija je jednostavnija i manje gusta. Vizuelna metafora: **brazda i točak** — koncentrične linije u uglu *Ponavljajućeg elementa* sažimaju oba motiva u jedan grafem.

**Tone of voice (vizuelno):** dostojanstveno, nikad veselo. Bez sjajnih površina, bez gradijenata u UI chrome-u (osim zlatne podloge na CTA), bez stock 3D ikona.

## Colors

Paleta je **mono-zelena sa zlatnim akcentom**, uz kremastu toplu površinu za odmor oka između tamnih sekcija.

### Brand greens
Definišu sve tamne površine, CTA, footer i nav.

- `green-900` `#1f3f2f` — najtamniji, pozadine kartica i footer
- `green-800` `#25402f` — primarni, hero overlay card, nav background, dugmad
- `green-600` `#395f48` — okviri, sekundarne površine, accordion divider
- `green-400` `#4d7e60` — hover stanja, soft badges

### Accents
- `gold-500` `#e7af12` — section eyebrows (linije oko UPPERCASE naslova), outline statističkih medaljona i hero ekstra-istaknuti naslov
- `lime-500` `#c8d32c` — hover na linkovima i highlights u akordionu

### Color usage rules — surface constraints (WCAG AA)

Akcenti moraju da poštuju pravila površina kako bi prošli WCAG AA 1.4.3 (kontrast teksta):

| Color | Dozvoljene površine | Zabranjene površine | Kontrast |
|---|---|---|---|
| `gold-500` (#e7af12) | `green-800`, `green-900` | `white`, `cream`, `gray-100` | 5.8:1 na green-900 ✓ ; 1.99:1 na white ✗ |
| `lime-500` (#c8d32c) | `green-800`, `green-900` | `white`, `cream` | 6.4:1 na green-900 ✓ ; 1.45:1 na cream ✗ |
| `jeegee-blue` (#00A4E9) | **Samo dekorativno** — *Ponavljajući element* fill, ne za tekst, ikone ili okvire | Bilo gde za tekst | 2.80:1 — fail za tekst, OK kao decorative fill |

Za body koristi `text-primary`; za headings na svetlim površinama `green-800`.

### Brand-specific
- `jeegee-blue` `#00A4E9` — **samo za `repeating-element` na Jeegee hero-u**. UI chrome (nav, footer, dashboard, dugmad) ostaje ujednačen `green-800` kroz ceo sajt. Brand identitet se primenjuje vrlo selektivno.

### Neutrals
- `cream` `#f5f1e8` — topla pozadina za sekcije sa svetlim sadržajem (O nama tekstu, blog telu)
- `white` `#ffffff` — bazna pozadina kartica
- `gray-100/300/700` — neutralne podele, captions i muted text
- `black` `#0f0f0f` — vrlo retko; rezervisano za maksimalni kontrast

### Semantic mapping
- `text-primary` = `green-900` (na svetlim pozadinama)
- `text-on-dark` = `white`
- `text-muted` = `gray-700`
- `border` = `green-600`
- `error` = `#c0392b` (samo tekst na svetloj pozadini — ne na zelenim površinama)
- `success` = `#2d6b2d` (~5.2:1 na white — AA pass za normal text)
- `focus-ring` = `#5a8a6e` (3:1+ kontrast; koristi se za fokus indikatore umesto green-400)

### Do's
- Koristi `green-800` za sve primarne CTA, a ne `green-900`
- `gold-500` u malim dozama — eyebrows, dugme na *Preuzmi katalog* CTA banneru i outline statistike
- Pune zelene boje u UI chrome-u (footer, nav)

### Don'ts
- ❌ Nemoj koristiti gradijent zeleni→zeleni u footer-u (mockup pokazuje solid; PRD §4.8 se ažurira)
- ❌ Nemoj koristiti brand-specific boju u UI chrome-u — samo na *Ponavljajući element* u hero pozicijama
- ❌ Bez zelenog teksta na zelenoj pozadini — kontrast će biti ispod WCAG AA

## Typography

**Jedna familija — Roboto** (Google Fonts, weights 300/400/700). Bez posebnog display fonta. Odgovara zahtevu *„tanki i elegantni"* iz Projektnog zadatka kroz Roboto Light (300).

### Hijerarhija
- **h1** — `3.5rem` / Roboto Light (300) / line-height `1.2` — glavni hero naslov. Često u zlatnoj boji (`gold-500`) za ekstra istaknut tekst (npr. cifra u statistici).
- **h2** — `2.5rem` / Roboto Bold (700) / `1.2` — naslov sekcije (npr. „Traktori", „O nama")
- **h3** — `1.75rem` / Roboto Bold (700) / `1.3` — naslov kartice (naziv modela na karticama)
- **h4** — `1.25rem` / Roboto Bold (700) / `1.4` — accordion header i podsekcija
- **body** — `1.25rem` (20px) / Roboto Regular (400) / `1.5` — pasus, opisi
- **small** — `1rem` (16px) / Roboto Regular (400) — caption, helper text, veličina fajla
- **caption** — `0.875rem` (14px) / Roboto Regular (400) — meta informacije (datum objave, oznaka)

### Section eyebrow
Mockup-i pokazuju ponavljajući pattern: pre h2 naslova sekcije stoji mala UPPERCASE oznaka (`caption` veličina) u Roboto Light + tracking `0.05em`, opcionalno okružena kratkim **zlatnim tankim linijama** sa obe strane (kao „lente"). Komunicira pre-naslov ili kategoriju.

### CTA dugmad
Uvek **UPPERCASE**, Roboto Bold (700), tracking `0.05em`, `small` size (16px). Primeri: *PREUZMI BROŠURU*, *SAZNAJ VIŠE*, *OPŠIRNIJE*.

### Do's
- Koristi Roboto Light (300) za hero h1 — daje „tanki elegantni" osećaj iz zadatka
- Uppercase eyebrow + h2 = ozbiljan agrarni ton
- Tracking `wide` (0.05em) samo na uppercase elementima

### Don'ts
- ❌ Nemoj uvoditi drugu familiju fontova (Playfair, Lora, itd.) — Roboto-only je odluka
- ❌ Bez italic za brend (Roboto Italic je OK za citate testimonijala, ali ne za UI)
- ❌ Nemoj nigde koristiti body veličinu manju od 16px

## Layout & Spacing

### Container
- Max-width: **1200px** (centriran)
- Padding (gutter): 24px desktop / 16px mobile

### Breakpoints (Bootstrap 5.3 aligned)
- **mobile:** < 768px
- **tablet:** 768px – 1199px
- **desktop:** ≥ 1200px

### Spacing skala (baza 4px)
1=4, 2=8, 3=12, 4=16, 5=24, 6=32, 8=48, 10=64, 12=96.

Vertikalni ritam između sekcija: `section` = **80px desktop**, **48px mobile**. Ne menja se globalno.

### Grid
Bootstrap 5 grid (12 kolona), ali sa **`row { margin: 0 }`** override (iz prototipa) — koristi `gap` umesto negativnih margina. Gutter unutar redova: 24px desktop / 16px mobile.

## Elevation & Depth

Sajt je **flat sa selektivnom dubinom**. Bez ambijentalnih box-shadow-a posvuda.

- **Card base shadow:** `{shadows.md}` (0 2px 8px rgba(31,63,47,0.06)) — mekana, jedva primetna. Samo na svetlim karticama (blog, brošura card).
- **Hero overlay card:** bez senke; pozicioniran preko foto-pozadine, koristi punu `green-800` pozadinu za izolaciju.
- **Modal / Lightbox:** backdrop `rgba(15,15,15,0.85)`; modal bez dodatne senke.
- **Sticky nav (shrunk state):** `{shadows.nav-shrunk}` — tek pri skrolu nadole.

## Shapes

- **Pravougaonici** su podrazumevani oblik — kartice, dugmad (pill oblik) i polja formi.
- **Krug** — statistike medaljoni (sa zlatnim okvirom), avatari testimonijala i ikonski badge-ovi.
- **Pill** (`999px`) — sva CTA dugmad. Pun radius za topao agrarni doživljaj.
- ***Ponavljajući element*** — pravougaonik **3:2 aspect ratio** (širi nego viši), `radius: 8px`, sa tankim belim koncentričnim lukovima u **gornjem desnom uglu** (1px stroke, opacity 0.5). Simbolika **točka + brazde**.
- **Wave divider** — koristi se selektivno:
  - Gornja ivica sekcije *Priče sa polja* (talasi nad slikom pozadine)
  - Ispod *Preuzmi katalog* CTA banera
  - **Nigde drugde** — predstavljao bi vizuelnu buku.

## Components

Vizuelne specifikacije; ponašanja su u `EXPERIENCE.md § Component Patterns`.

### Button
- **Primary** — `green-800` bg, beli tekst, pill radius, padding `12px 32px`, tracking wide, weight bold, uppercase. Hover: `lime-500` (tranzicija zelena → lime).
- **Secondary** — transparent bg, `green-800` border (2px), `green-800` tekst, pill radius. Hover: bg → `green-800`, tekst → beli.
- **CTA-light** — `gold-500` bg, `green-900` tekst, pill radius. Koristi se na *Preuzmi katalog* baneru (zlatni naglasak na zelenoj sekciji).

### Card
- **Base** — bela pozadina, radius 8px, padding 24px, mekana senka. Koristi se za product kartice (Grid layout), blog kartice i brošura card.
- **Hero overlay** — `green-800` bg, beli tekst, radius 8px, padding 32px, **bez senke**, pozicioniran preko hero foto-pozadine (uobičajeno dole levo). Sadrži: brand logo lockup gore, h1 naslov, do 3 bullet stavke i watermark *Ponavljajući element* dole desno.

### Repeating Element (*Ponavljajući element*)
Geometrija i boje su u YAML-u (`components.repeating-element`). Upotreba:
- Kao pozadina hero overlay kartice (svaki brand, svaki proizvod)
- Kao watermark u uglu većih sekcija (suptilno)
- **Ne** kao samostalan dekorativan element bez teksta

### Accordion
- Transparentna pozadina, donja granica `green-600` (1px solid) na svakoj sekciji
- Header: h4 weight bold + plus/minus ikona desno (`+` zatvoreno, `−` otvoreno). Ikona se rotira ili menja kroz mekanu tranziciju od 200ms.
- **Podrazumevano otvoreno:** samo prva sekcija (Motor); ostale (Transmisija, Hidraulika, Ostalo) su zatvorene.
- Sadržaj sekcije: tabela ključ-vrednost u Roboto Regular.

### Pill badge
- `gold-500` bg, `green-900` tekst, pill radius, padding `4px 12px`, caption veličina. Koristi se za oznake tipa *Uskoro* i *Novo*, kao i za status badge u admin-u.

### Form input
- Bela pozadina, `{colors.neutral.gray-500}` border (1px), radius 6px, padding `12px 16px`, body veličina teksta. Focus: border → `green-800`, 2px ring `{colors.semantic.focus-ring}` (postiže 3:1 vs surface).
- Label: `caption` veličina, uppercase, weight bold, `gray-700` tekst, margin-bottom `4px`.
- Error stanje: border → `error`, helper text u `error` boji.

### Statistika medaljon
- Krug 120px (desktop) / 80px (mobile), `gold-500` outline (2px), na tamnozelenoj parent površini (vidi YAML `parent-surface-required`). Unutra je centriran broj h1 veličine u `gold-500` boji (count-up animacija pri scroll-into-view).
- Ispod kruga: oznaka `caption` veličine, `gray-700`.

### Brošura card
- `{colors.neutral.white}` bg, radius 8px, padding 24px, `{components.brochure-card.border}` (umesto senke — outlined varijanta)
- Levo: cover-thumbnail (renderovana prva strana PDF-a), max-width 120px, sa malim ukošenim efektom (3deg rotate `[ASSUMPTION]`)
- Desno: h4 naslov brošure, `caption` meta („2.8 MB, PDF") i CTA-light pill dugme *PREUZMI*.

### Wave divider
- Inline SVG, sa fill bojom `green-800`, visine ~80px desktop / 48px mobile.
- Talasi: 3-4 vrha, mekane bezier krive; nije agresivno cik-cak.

## Do's and Don'ts (cross-cutting)

**Do:**
- Drži UI chrome (nav, footer, primarne CTA) **ujednačeno zelen** kroz ceo sajt
- Koristi *Ponavljajući element* u hero pozicijama kao brand-specific akcenat
- Roboto Light (300) za hero h1; Roboto Bold (700) za sve ostale naslove
- Zlatni akcenat (gold-500) u malim, retkim dozama — eyebrows, jedna CTA po stranici i outline statistike

**Don't:**
- ❌ Nemoj uvoditi nove fontove ili nove primarne boje bez unosa u decision log
- ❌ Bez gradient pozadina (chrome ostaje pun)
- ❌ Bez 3D ikona, sjajnih površina ili neon highlight-a — agrarni sektor je prizemljen
- ❌ Bez wave-ova svuda — samo dve namenske pozicije (vidi `wave-divider`)
- ❌ Bez fiksiranih badge-ova „NOVO!" na karticama u stilu e-commerce sajtova
- ❌ Bez auto-play videa sa zvukom

## Conflicts resolved (PRD vs visual sources)

Dokumentovano za buduću referencu. PRD će se ažurirati u sledećoj iteraciji.

| Konflikt | PRD specifikacija | Vizuelni izvor | Rešenje |
|---|---|---|---|
| Pozadina footer-a | §4.8 FR-30: zeleni gradijent | JPG mockup: pun green-800 | **Pun** (mockup ima prednost) |
| Pretraga u nav-u | §4.1 FR-1: inline polje | JPG + HTML: ikona koja se proširuje | **Ikona → expand** (mockup ima prednost) |
| Brand-specific UI chrome | §3 Glossary: boja varira po brendu | JPG: ujednačen zeleni chrome | **Ujednačen zeleni chrome**; brand boja samo na *Ponavljajući element* u hero pozicijama |
| FR-19 polja forme | §4.5 FR-19: 5 polja | JPG: 3 polja | **5 polja** (PRD ima prednost, mockup se ažurira u UX fazi) |

## Open Decisions

- **`[ASSUMPTION]`** Radijus skala je unifikovana u 4 koraka (sm/md/lg/pill). Iz prototipa: 5/6/8/10 — preslikava se u sm=6, md=8, lg=10.
- **`[ASSUMPTION]`** Brošura card cover-thumbnail `3deg rotate` efekat — vizuelni potpis. Potvrditi u dev-u; lako se uklanja ako ne odgovara.
- **`[OPEN]`** Konkretna hover stanja za sve linkove i kartice — u prototipu ih nema (samo `outline`). Definisati u dev-u na osnovu osnovne palete.
- **`[OPEN]`** Print stylesheet — da li podržavamo print formatiranje (specifikacije proizvoda, brošura preview)? `→ defer`.
