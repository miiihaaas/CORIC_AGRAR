# Reconciliation — PRD vs Projektni zadatak

## Coverage summary

PRD captures the structural and functional core of the Projektni zadatak very well — all major pages, forms, admin modules, integrations, and the trojezičnost/GDPR/SEO concerns are represented as FRs. However, the PRD systematically loses **qualitative/visual/tonal cues** that are scattered throughout the source (decorative transparent logo, font character "tanki i elegantni", color palette, slogans, "Lemken referentni dizajn", decorative wave below brand pages), and the **full product hierarchy with specific model identifiers** (Wuzheng, Saillong by Maki, KJ-tip plows, 1LF-LKX450, HZM 1100, JMA300, Vega 9/12, Hermes H255, SKS combinator, 2BG-250 seeders, etc.) is collapsed into the abstract FR-10 "3-level hierarchy" without naming these as in-scope content.

## Gaps (substantive — must consider)

- **Brand list incomplete in PRD.** Source §2.1.3 lists three tractor brands explicitly: **Wuzheng, Agri Tracking, Saillong by Maki**. PRD Glossary §3 names "Wuzheng, Agri Tracking, Jeegee, HZM, Tulip" but drops **Saillong by Maki** entirely. Source §2.1.3.3 dedicates a section to Saillong; PRD has no acknowledgment. → Update §3 Glossary brand list and FR-8 examples.

- **Specific model catalog missing.** Source §2.1.4.1 — §2.1.4.3 enumerates ~30 specific Jeegee, HZM, and Tulip model identifiers (1LF-KP331, 1LF-435C, 1LF-L450F, 1LF-L350, 1LF-LKX450, 1LF-LKX550A, JMA300, KX300, KX350, Vega 9 short tanjirača 250/300, 1BYQ tanjirača 330/380/430/530/630, Vega 9/12 tanjirače 400/500/600, Hermes H255-15.7m / H255-12.4m, SKS 300/400/500, 2BG-250, 2BG-300, HZM 1100, HZM925, HZM 810T/812T/816T/825T, HZM 7335, Tulip MIX 6/8 kubika). PRD §10 In Scope says "all of §4" but never enumerates these as the content that must exist at launch; the "100 proizvoda" cap is mentioned only in the brief's tech section. → Add a product hierarchy appendix or table; the dev needs this for fixtures and the admin needs it as the initial data load.

- **Plug "izbor daske" (moldboard choice) UI element.** Source §2.1.4.1.1 specifies that on individual plough product pages there must be a **selector/preview of moldboard type (puna i rešetkasta — full and slatted), illustrative image with code + name, plus space for adding a third variant**. PRD FR-14/15/17 (product page) has no concept of variant selectors or product-internal sub-component galleries. → Either add to FR-17 (extended product spec) or new FR.

- **Tanjirača rotor preview.** Source §2.1.4.1.2 specifies that on each tanjirača product page, a **side-by-side preview of two rotor types (dupli cevasti vs Cambridge valjak)** with side-view images is required. Same gap as moldboard — not in PRD. → Add to product-page FR or document as content-config admin field.

- **"Uskoro" label on partial models.** Source §2.1.3 says some brands carry the *Uskoro* label. PRD FR-2 / FR-7 cover this at brand level. Source §2.1.4.1.1 also implies a "label koliko ima modela" on Tanjirača 630 — a **per-model count label** which has no PRD equivalent.

- **Tonal/voice direction lost.** Source §2.1.1 specifies the hero slogan **"Prijatelj koji razume zemlju!"** and §2.1.1 hero meni description "**fontovi tanki i elegantni**" + "**meni transparentan**". PRD FR-1 mentions transparent menu (in FR-28) but loses the actual slogan string and the *elegantna typography* directive. → Add slogan to Glossary or to FR-1 consequences; mention typography direction.

- **Decorative transparent logo motif.** Source §2.1.1 ("O nama" section of homepage) and §2.1.2 ("Tekst o kompaniji") explicitly describe **a transparent enlarged Ćorić Agrar logo as a background decorative element** appearing on both Home and About. PRD FR-1 and FR-4 have no mention of this brand decorative motif. → Should be in Glossary (visual motifs) or in FR consequences.

- **Color palette direction lost.** Source §2 opening: "**zelena i tamna paleta boja karakteristična za agrarni sektor**" plus per-brand color hints (Agri Tracking *zelena*, Jeegee *plava*, HZM color, etc.). PRD §3 Glossary mentions "*boja varira po brendu*" but never anchors the primary palette as **green + dark**. Footer (FR-30) does say "zeleni gradijent". → Add a §6 "Brand & Visual Guardrails" subsection or move palette into a constraint.

- **"Lemken referentni dizajn" reference.** Source §2.1.4 names **lemken.com as the reference design** for the Mehanizacija category organization. PRD silently drops this — it is a load-bearing input for the UX phase. → Should appear in §12 Open Questions for UX, or in §7 Integration/Reference.

- **Hero element below Preuzmi katalog (decorative wave).** Source §2.1.3.1 closes the brand page with "**slika sa zatalasanom gornjom ivicom koja se nadovezuje na futer**". PRD FR-8 closes at "preuzmi katalog CTA" — no mention of the decorative bridge to footer. Similar pattern is in FR-3 (Priče sa polja preview has wavy top edge — captured) but missing on brand pages. → Add to FR-8 consequences.

- **Tulip comparison table.** Source §2.1.4.3 includes a **full 10-row comparison table** (Kapacitet, Dužina, Širina, Visina, Težina, Broj mešača, Broj noževa, Obrtaji spirale, Debljina dna, Potrebna snaga). PRD FR-12 says "comparison table dva modela (dimenzije)" — captured but vague; the dev/admin will not know it has 10 rows of mechanical specs, not just dimensions. → Tighten FR-12 wording from "dimenzije" to "mechanical specs (10 rows: kapacitet, dimenzije, težina, broj mešača/noževa, obrtaji, debljina zidova, potrebna snaga)".

- **"Slika sa zatalasanom gornjom ivicom" as recurring visual motif.** Source uses this pattern multiple times (homepage Priče sekcija, brand pages preuzmi katalog footer-bridge). PRD captures it once (FR-3) but it's a **recurring motif** that should be in Glossary as a named visual element. → Add to Glossary §3 Specifični elementi.

- **Forma "Imate pitanja?" naziv.** Source §2.1.5 names the product-page form **"Imate pitanja?"**. PRD FR-19 names it "Upit za model". Source naming is what users will see in admin/UX; PRD term is internal. → Reconcile: Glossary should list both, with "Imate pitanja?" as the UI-visible label and "Upit za model" as the internal model name.

- **"Nazvana je Priče sa polja u skladu sa brendingom" rationale.** Source §2.1.1 explains the naming as deliberate branding distinct from "blog". PRD §3 Glossary captures the term but loses the rationale. Minor but worth noting in brand guardrails.

## Gaps (minor — may be intentional drops)

- **"Marijana@kipetrol.rs treba da dostavi tekst" placeholders** — source has ~15 of these for client-supplied copy (homepage O nama text, Priključna baner text, Radne mašine text, Polovna baner text, About text, Timeline data, Gallery photos, Service text, Service email, Blog initial posts, Blog categories, Contact info, Contact email). PRD §12 §15-17 Open Questions captures *some* of this ("politika privatnosti", "blog kategorije", "email adrese"), but the larger pattern — **15+ pieces of content the client owes** — is not registered as a launch dependency. → Add to §12 Open Questions or as a §13 supplementary "Content Dependencies" list.

- **"Bekap trenutnog sajta pre migracije".** Source §1.2 tech list says "Bekap trenutnog sajta pre migracije". PRD §9 Non-Goals explicitly says "Migracija sa starog sajta — ne postoji stari sajt; … bekap pre migracije otpadaju." This is a **contradiction with source**. Either source is outdated or PRD is wrong; the brief addendum may clarify. → Confirm: is there or isn't there an existing site?

- **"Zadržavanje ili preusmerenje postojećih URL adresa (301 redirect)".** Source §1.2 lists this; PRD captures redirect manager (FR-44) for future use but, consistent with the above contradiction, drops "preserving existing URLs". Same root cause — clarify existing-site status.

- **"Iznad menija nalazi se top heder sa informacijama o adresi i kontakt telefonu"** — captured in FR-29.

- **"Slogan kompanije over hero video" on O nama** — source §2.1.2; PRD FR-4 doesn't mention slogan overlay on hero (covered loosely). Minor.

- **"Ikonice tankih linija bele, na zelenoj pozadini"** for brand statistics — source §2.1.3.1; PRD FR-8 says "ikona + broj" but loses styling direction (white thin-line icons on green). UX phase will surface it but worth noting.

- **WYSIWYG editor podržava video embed** — source §3.4; PRD FR-39 captures "video embed" — covered.

- **"Mašine za sejanje" header in source §2.1.4.1.3** — heading text is "MAŠINE ZA SEJANJE" but source §2.1.4.1 lists category as "MAŠINE ZA SETVU". Minor inconsistency in source, irrelevant to PRD.

## Items PRD added beyond source

- **FR-32 fallback marker UX** — PRD specifies a "diskretni vizuelni marker *(automatski prevod nije dostupan — ovo je fallback na sr)*". Source does not specify fallback behavior at all; PRD makes this design call. Reasonable enhancement.

- **FR-33 hreflang x-default → sr** — PRD specifies; source only mentions hreflang generically.

- **FR-36 validation rule** — "pre prelaska u *Objavljeno*, sr verzija mora imati naziv, sliku galerije, i barem jednu sekciju specifikacija". Source has no such validation. Sensible add.

- **FR-2 *Uskoro* labels at category level**, FR-7 inactive nav for *Uskoro* brands — source only mentions Uskoro label loosely; PRD productizes it.

- **§5.3 Rate limiting on forms** (10 req/15min IP), **§5.3 login rate limit** (5/15min), **§5.3 MIME validation on uploads** — none of these are in source; PRD is correctly adding security baselines.

- **§5.2 WCAG 2.1 AA** as accessibility baseline — source does not mention accessibility at all.

- **§9 Explicit Non-Goals list** — strong addition; source is implicit only.

- **FR-13 polovna mehanizacija "no upper bound on items"** — source doesn't constrain; PRD makes the affordance explicit.

- **FR-20 admin override "u celini zamenjuje" auto suggestions** — source just says "označavanje sličnih modela"; PRD picks the all-or-nothing semantics.

- **UJ-1/UJ-2/UJ-3 journey scenarios with edge cases** — source has no journey narratives; PRD added these for UX/dev context.

- **Per-form rate limiting, log retention 14 days, session timeout 4h** — operational baselines absent in source.

## Glossary or naming inconsistencies

- **"Saillong by Maki"** (source §2.1.3 + §2.1.3.3) — **missing entirely from PRD Glossary §3 brand list and from FR-8 examples.** This is the clearest single naming gap.

- **"Imate pitanja?" (source UI label) vs "Upit za model" (PRD internal name)** — both should appear in Glossary; right now only the internal name is documented.

- **"Priče sa polja" vs "Blog"** — PRD handles this well in Glossary; source rationale ("u skladu sa brendingom") could be noted.

- **"Saveti, Vesti, Iskustva kupaca, Agrotehnika"** — source §2.1.7 lists these as example blog categories; PRD FR-26 says "admin definiše šemu naknadno" and Glossary §3 lists only "*Saveti, Vesti, Iskustva kupaca*" (drops *Agrotehnika*). Minor.

- **"Mini utovarivači / Utovarivači bez teleskopa / Teleskopski utovarivači / Telehendleri"** (4 HZM categories) — PRD FR-11 enumerates all four; covered.

- **"Tanjirače: Nošene vs Vučene"** — source distinguishes towed vs mounted tanjirače as a hierarchy level; PRD's generic "3 nivoa duboka" (FR-10) abstracts this. If admin needs to model **Mounted / Towed** as a categorization, FR-10 should call it out explicitly or the example chain in FR-10 should include this.

- **"Plugovi: ravnjaci vs obrtači, then by debljina grede"** — same as above; the depth-of-hierarchy assumption (3 levels) in FR-10 may be insufficient: *Mehanizacija → Priključna → Osnovna obrada → Plugovi → Obrtači → 120×120* is **6 levels deep** if you count from the top menu. PRD says hierarchy is "do 3 nivoa". → **Re-check: 3 levels vs 6 levels.** This is the most concrete structural risk in the PRD.

- **"Kategorija" overloading** — source uses "kategorija" for (a) menu top-level (Traktori/Priključna/Radne/MIX/Polovna), (b) Jeegee 3-grupe (Osnovna obrada / Priprema / Setva), (c) blog kategorije. PRD Glossary disambiguates well but FR-38 ("CRUD kategorija i potkategorija") may not be enough — needs to handle the multi-level depth surfaced above.

- **Brand colors** — source mentions Agri Tracking zelena, Jeegee plava; HZM and Tulip colors are implicit. PRD §3 says "boja varira po brendu" and FR-37 has a "boja brenda" field — covered structurally but no inventory of the actual colors per brand.
