# Reconciliation — PRD vs Visual Mockups

## Coverage summary

PRD §4 Features covers the major page structures shown in mockups (Početna, Stranica brenda, Stranica proizvoda) with strong fidelity on form behaviors, accordion structure, and brand-color theming. However, several visible structural/visual elements are not explicitly described — most notably the dedicated "O nama" homepage section, the contact info hero card on brand pages, the comparison row composition on the brand page, and product-page layout details (PDF brošura preview card composition, "Imate pitanja?" form sitting within the product page rather than as a separate section).

## Početna 4.0 — observations

- **Top header** (FR-1 / FR-29): Mockup shows address ("Vojvođanska 1, Bačaršl, Srbija") + phone + search icon in a slim top bar above main nav with logo on the left — matches PRD; confirm green-tinted top header color.
- **Section ordering** (FR-2): Mockup ordering on home is **Hero → O NAMA (intro section) → TRAKTORI → PRIKLJUČNA MEHANIZACIJA → RADNE MAŠINE → POLOVNA MEHANIZACIJA → PRIČE SA POLJA → Footer**. PRD FR-2 enumerates Traktori / Priključna / Radne mašine / Polovna but does **not** mention an "O nama" intro/teaser block on the home page above the category sections. **Gap**.
- **TRAKTORI block** (FR-2): Mockup shows 3 brand cards in a row (logos + representative model image), with two pill buttons below ("OPSIRNIJE" and what looks like a secondary CTA labeled like "USKORO" or a brand label). PRD captures logo+model+brand-page link but not the second CTA / "see more brands" affordance pattern.
- **Priče sa polja preview** (FR-3): Mockup confirms two cards over a textured/green field background, but the **"zatalasana gornja ivica"** (wavy top edge) described in FR-3 is visible as a curved/wave divider — confirmed. The cards visible appear to carry only text + CTA (no thumbnail), matching FR-3.
- **Footer** (FR-30): Centered logo above column nav with green gradient — matches FR-30. Mockup shows 4 columns: KONTAKT / PROIZVODI / O NAMA / NAJNOVIJE VESTI. PRD lists "Proizvodi / O nama / Najnovije vesti" plus contact — order/labels confirmed; the "NAJNOVIJE VESTI" column with auto-populated latest-post links is an implementation detail PRD does not specify (does footer render latest 4-5 blog post titles dynamically?).

## Stranica brenda 4.0 — observations

- **Brand hero with "Ponavljajući element"** (FR-8): Mockup shows the green rectangular card with concentric white quarter-arcs in corner, brand logo + headline ("SNAGA KOJA TRAJE DAN ZA DANOM") + descriptive paragraph, overlaid on a full-width field photo. Confirms FR-8 + Glossary definition. Confirm: card sits **bottom-left** over hero, not centered.
- **Statistike brenda** (FR-8 / Glossary): Mockup shows **4 circular icon badges** (green-filled circle with white line icon) above big numbers (1500 / 100 / 13 / 15) and labels. PRD says "4 numeričke vrednosti (ikona + broj) sa count-up animacijom" — confirmed; mockup adds that **icons sit inside large filled circles** (visual style note for UX).
- **Brand quote/banner strip** (FR-8): Mockup shows a **dark banner with brand-tinted quote** ("Agri Tracking traktori pružaju snagu, pouzdanost i udobnost...") with a tractor photo on the right side bleeding into the banner. PRD FR-8 mentions "citat/banner" generically but does not describe the **two-column layout (text left, photo right) with dark background**. **Gap — capture this layout.**
- **Modeli grupisani po seriji** (FR-8): Mockup shows series labels **TB MODELI / TD MODELI / TC MODELI** as centered headings with a thin gold divider rule. PRD says "grupisani po seriji" but the **visual treatment (series label as banner with rule)** is undocumented.
- **Model rows mismatch with FR-8**: FR-8 says "svaki model je prikazan u 1 redu sa krupnom slikom levo i akordionom specifikacija desno". The mockup actually shows **TWO model cards side-by-side per row** for TB/TD series (Agri Tracking 804 + 504; 1104 + 1304) — each card is a tile (image + name + short text + OPSIRNIJE CTA), NOT a row with accordion. Only the **TC MODELI** section shows the **single-row layout with image-left + accordion-right** that FR-8 describes. **Gap — FR-8 conflates two distinct layouts: grid cards for non-flagship series, single-row+accordion for flagship/lead model.**
- **Zadovoljni kupci slider** (FR-8): Mockup shows photo-left + quote-right slider with 3 dot indicators — confirmed.
- **Preuzmi katalog banner** (FR-8): Mockup shows a wide dark-green banner with brand catalog cover image + CTA "PREUZMI" — confirmed; **the visual specifics (gradient background, fan of PDF covers, copy "PREUZMITE SVOJ KATALOG i budite u toku")** are mockup-only.
- **Closing field-photo section**: Mockup ends brand page with a **full-width photo of a tractor in a field with subtle white wave divider above** before the footer. PRD does not mention this transitional visual. **Minor gap.**

## Stranica proizvoda 1.0 — observations

- **Hero** (FR-14): Mockup shows full-width photo (sunset wheat-field with tractor) with the **Ponavljajući element card bottom-left** containing brand logo + product name (AGRI TRACKING TB504) + 3 bullet characteristics. Matches FR-14. Confirm green card variant (brand-specific color from FR-37) applies here.
- **Sekcija Opis proizvoda "Lorem Ipsum"** (FR-15): Mockup shows a paragraph block with the heading "Lorem ipsum". The heading is **literal "Lorem ipsum"** — clearly placeholder copy, but PRD does not specify whether this description section has its own heading rendered ("Opis", "Više o modelu" etc.) or just runs as body text. **Minor gap — clarify if Opis section has a label.**
- **Galerija** (FR-16): Mockup shows a **horizontal strip of 6 thumbnails** (no visible arrows or pagination dots in the static mockup). PRD says "karusel sa swipe + Lightbox" — confirmed; mockup confirms thumbnail-strip presentation rather than a featured-image+strip layout.
- **Tehnički podaci tabela** (FR-17): Mockup shows **MOTOR section already expanded** as a default open accordion with a 6-row table (Tip motora / Nominalna snaga / Broj cilindara / Zapremina motora / Nominalni broj obrtaja / Rezervoar za gorivo). TRANSMISIJA / HIDRAULIKA / OSTALO are collapsed below with a `+` indicator. PRD FR-17 does not state **which section opens by default** (Motor) nor that the **`+` indicator style** is used. **Gap — capture default-open behavior + indicator iconography.**
- **PDF brošura preview card** (FR-18): Mockup shows a **distinct presentation**: a green outlined card containing (a) a stylized PDF cover thumbnail with brand colors, (b) headline "Brošura", (c) line "AGRI TRACKING TB504", (d) "2.8 MB, PDF", (e) green pill CTA "PREUZMI". PRD FR-18 says "minijatura naslovne strane + dugme PREUZMI" but does not specify file-size display, the **card outline treatment**, or the layout (thumbnail-left, meta-right). **Gap — flesh out FR-18 spec.**
- **Iz prve ruke testimonijal** (FR-21): Mockup shows photo-left + quote-right (light gray background panel) with 3 dot pagination indicators. Confirms FR-21.
- **Slični modeli** (FR-20): Mockup shows **2 cards side-by-side** (image + brand logo + model name + short text + green DETALJNIJE CTA). PRD FR-20 says "2-4 modela" — mockup is at the low end. Confirm. **Note**: the cards show the **brand logo inside the card** which is not specified in FR-20.
- **"Imate pitanja?" form** (FR-19): Mockup shows the form **embedded on the product page** with two columns: **left** = headline + descriptive paragraph + contact email + contact phone; **right** = 4 form fields (Vaše ime i prezime / Vaša email adresa / Vaša poruka / POŠALJI CTA). PRD FR-19 specifies fields including "Model (auto-popunjen, readonly)" — but **the mockup form has NO visible Model field**. **Gap / inconsistency — either the model auto-fill is hidden, or the mockup omits it, or it goes into a hidden form field and only the model name shows up in the email subject.** Clarify in UX phase.
- **Form fields scope** (FR-19): PRD lists "Ime *, Email *, Telefon, Model, Poruka" (5 fields). Mockup shows **only 3 input fields (Ime, Email, Poruka) — no Telefon, no Model**. **Gap — PRD and mockup diverge on field count.**

## Visual elements PRD should capture explicitly

- **"O NAMA" intro section on home page** (above category sections): mockup includes a short company-intro block that PRD §4.1 omits — add as FR-1.5 or amend FR-2.
- **Wave/curve dividers** between full-width sections (visible above "Priče sa polja" and other transitions): add to visual-language notes (UX deliverable) — currently only "zatalasana gornja ivica" on FR-3 mentions it.
- **Brand quote/banner two-column dark strip** on brand page (FR-8): specify layout (text left, brand-tinted; image right with dark overlay).
- **Series label treatment** on brand page (TB MODELI / TD MODELI / TC MODELI as gold-underlined headings): add to FR-8 consequences.
- **Two distinct model-row layouts on brand page** (FR-8 conflict): grid-card layout for early series + featured single-row+accordion layout for flagship/last series. Decompose FR-8 into two sub-requirements.
- **Statistike visual treatment** (FR-8): icons inside large filled green circles, not bare icons.
- **Preuzmi katalog banner** copy & visuals (FR-8): full headline "PREUZMITE SVOJ KATALOG i budite u toku" + fanned-PDF-covers visual.
- **Default-open accordion section** on product page (FR-17): Motor is expanded by default; `+` / `−` indicators visible.
- **PDF brošura card layout** (FR-18): card outline, thumbnail of cover + name + file size + format + PREUZMI CTA in pill button.
- **"Imate pitanja?" form on product page** (FR-19): two-column embed (info left, fields right) — and reconcile field list with mockup (3 vs 5 fields, no visible Model field).
- **Footer "NAJNOVIJE VESTI" column**: clarify whether this is auto-populated with latest blog post titles (4-5 items in mockup).
- **Closing field-photo + wave-divider section** before footer on brand page.

## UX-phase handoff items

- **Decompose FR-8 (Stranica brenda)** into discrete sub-requirements per visible band: hero+card / statistics / quote-banner / series-grid-cards (TB, TD) / series-featured-row-with-accordion (TC) / testimonials slider / catalog banner / closing photo band.
- **Reconcile FR-19 field list with product-page mockup**: PRD lists Ime/Email/Telefon/Model/Poruka — mockup shows Ime/Email/Poruka only. Decide which is canonical: (a) update PRD to drop Telefon + make Model an invisible hidden field appended into email subject, (b) update mockup to add the missing fields. UX should resolve before architecture.
- **Specify accordion default-open state and icon set** (FR-17): Motor open + `+/−` indicators.
- **Specify brošura preview card design tokens** (FR-18): file-size text, card border, thumbnail dimensions.
- **Confirm presence/spec of "O nama" intro on home page** (currently undocumented in FR-1/FR-2): is it a teaser block linking to /o-nama, an inline rich-text block, or just a heading + CTA?
- **Wave/curve divider system**: define as a reusable design-system pattern between full-width sections (used on home, brand page closing, possibly elsewhere) — single SVG asset?
- **Visual style for series labels** (TB MODELI etc.): centered heading + gold underline rule — codify as design-system component.
- **Statistics circle-icon variant** (FR-8): is the green-filled circle treatment per-brand or universal? Confirm tokenization.
- **Footer "Najnovije vesti" column** behavior: static links vs dynamic latest-N blog titles — confirm and add FR or amend FR-30.
- **Top header background color** + mobile-collapse behavior (already open in FR-29): mockups show green-on-green styling — codify.
- **Slični modeli card composition** (FR-20): mockup shows brand logo inside card; PRD doesn't specify — codify.
