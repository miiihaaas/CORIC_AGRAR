# PRD Quality Review — CORIC_AGRAR

## Overall verdict

This is a substantive, downstream-ready PRD for a solo-dev internal context: 47 FRs grounded in a real client brief, a load-bearing Glossary, and three named UJs that touch the climax of every major form. What holds up well is decision-readiness on scope (Non-Goals is honest and specific) and Glossary discipline. What's at risk is **strategic coherence around the thesis** (the "lead-gen over traffic" claim in §11 is the most interesting bet in the doc but never propagates into feature prioritization), and **a few testability gaps in Search, fallback markers, and the Comparison table** that downstream stories will trip on.

## Decision-readiness — adequate

Decisions are mostly stated as decisions, not buried. The Non-Goals list (§9) is unusually concrete and confidently exclusionary — "Inventory tracking", "AI / preporuke proizvoda izvan FR-20", "Mašinski prevod sadržaja" are real choices with downside acknowledged. FR-20 ("admin override **u celini zamenjuje** auto-suggestions") and FR-32 ("Fallback je polje-po-polje a ne strane-po-strane") are exactly the kind of decisions an engineer can act on without a callback.

Where it gets thin: there are no `[NOTE FOR PM]` callouts at real tensions, only two at safe places (newsletter signup, visitor profile in §10.2). The interesting tension — "lead-gen kanal" in §1 vs §11's "page-views nije cilj, leads jesu" — is asserted in Vision and Counter-metrics but never surfaces as a callout where it would force a feature decision (e.g., why does Hero FR-1 not have a primary lead CTA above the fold?). Open Questions §12 is well-organized and routed (`→ Architecture`, `→ UX`), but several entries are pseudo-open: Q15 ("politika privatnosti — Lorem Ipsum baseline") and Q17 ("email adrese — env-default baseline") already have decided answers in the same line.

### Findings
- **medium** No PM callouts at real product tensions (§1 / §11 / §4.1) — Lead-gen-first thesis is asserted but never tested against feature decisions like "should hero have a lead CTA?" or "should homepage rank brands by lead conversion?". *Fix:* add one or two `[NOTE FOR PM]` callouts where the thesis bites, e.g., in §4.1 FR-1 or in the SM section.
- **low** Pseudo-open questions in §12 (Q15, Q17) — Have answers in their own statement. *Fix:* either move to Assumptions Index with the chosen baseline, or sharpen into a real open question (e.g., "Q15: can we use a Serbian SaaS policy generator template instead of Lorem?").

## Substance over theater — strong

Very low theater for a 47-FR PRD. The Glossary is doing real work: terms like *Ponavljajući element*, *Statistike brenda*, *Slični modeli* are referenced verbatim in FRs and carry visual/behavioral semantics that the architect and UX will need. No persona inflation — three UJs, each with a named protagonist (Marko, Stojan, Marijana) and each tied to a specific climax FR (FR-19, FR-22, FR-36). The "Iz prve ruke" / "Zadovoljni kupci" distinction in §3 is the kind of detail you only write because Discovery surfaced it, not because the template asked.

NFRs in §5 mostly avoid boilerplate by either pinning a concrete bound or honestly deferring with `[OPEN → arhitektura]` (e.g., §5.1 LCP/TTFB). §5.2 Accessibility flags green-on-dark contrast as a real risk, which is a substantive note rather than "system must be accessible."

The closest thing to furniture is §2.1 Jobs To Be Done — listed in bullet form per persona type, but the bullets don't drive any FR not already implied. JTBD is cheap furniture here, not harmful, but it adds shelf weight without earning it.

### Findings
- **low** §2.1 JTBD bullets are decorative — every JTBD is satisfied by an FR that exists for other reasons (UJ-1/2/3 and Glossary already carry the load). *Fix:* either compress JTBD into one paragraph per role, or drop and let UJs carry intent.

## Strategic coherence — thin

This is the weakest dimension. The PRD has an *implicit* thesis ("lead-gen catalog, not e-commerce, not content site") but doesn't earn it. The thesis surfaces in three places — §1 Vision ("online katalog + lead-gen kanal"), §9 Non-Goals (no e-commerce, no user accounts), and §11 Counter-metrics ("Broj page-view-a sam po sebi — nije cilj; cilj su leads") — but the feature prioritization in §4 doesn't visibly follow from it.

Evidence:
- 47 FRs cover Početna → Statičke → Katalog → Mehanizacija → Proizvod → Servis → Blog → Pretraga → Trojezičnost → 4 Admin subsections. That's a complete site map, not a thesis. A lead-gen-first PRD would prioritize FR-19/FR-22/FR-23 (the forms), Dashboard analytics (FR-35), and conversion-relevant elements (FR-14 hero, FR-18 brochure download) — but they sit equal among 47 features.
- §10 MVP Scope says "sve odjednom — jedan launch" with everything from §4 in scope. That's coherent with the brief's "single launch" framing but it neutralizes prioritization entirely. A lead-gen thesis at minimum has a "build catalog stub → forms → polish blog later" sequencing.
- §11 Success Metrics is `[DEFERRED]` with "Brief je ovo eksplicitno označio kao nebitno". Fair for internal stakes, but combined with no prioritization and 47 equal-weight FRs, there's no way to test the thesis against feature shape during Epics. Counter-metrics ("bolji lead je lead u 30 sekundi") is sharp — the rest doesn't echo it.

The product brief addendum reportedly fixes tech stack; if it also fixes feature sequencing, this is fine, but the PRD should at minimum *point at* that sequencing.

### Findings
- **high** Thesis declared but not propagated (§1 / §11 vs §4 / §10) — "Lead-gen, ne traffic" is the most interesting bet in the PRD but feature prioritization and MVP scope treat 47 FRs as equal-weight. *Fix:* either add a 1-paragraph "Feature priority arc" subsection in §4 mapping FRs to thesis (forms + catalog spine first; blog/admin polish second), or acknowledge in §10 that sequencing is owned by Epics phase and add a `[NOTE FOR PM]` flag.
- **medium** SMs deferred without lightweight tracer (§11) — Even an internal solo-dev PRD benefits from one binary lead-gen tracer ("at least one lead-relevant form submitted within 30 days of launch"). Counter-metric is good but unbalanced without a primary. *Fix:* promote one of the "Funkcionalni (binary)" items as the launch tracer (e.g., "FR-19/22/23 each receive ≥1 production submission within 30 days").
- **low** §10 MVP Scope is a tautology ("sve iz §4 + §5 + §7") — Adds no information. *Fix:* either delete §10.1 or use it to declare phasing within the single launch (e.g., catalog spine + forms = vertical 1, admin polish + blog = vertical 2).

## Done-ness clarity — adequate

For the majority of FRs, the "Consequences (testable)" block carries clear acceptance bounds. Good examples: FR-17 ("Prazne sekcije se ne prikazuju (ako *Hidraulika* nema unete podatke, sekcija se sakriva)"), FR-20 ("admin override **u celini zamenjuje** auto-suggestions"), FR-32 ("Fallback je polje-po-polje a ne strane-po-strane"), FR-36 validation rule ("sr verzija mora imati naziv, sliku galerije, i barem jednu sekciju specifikacija"). These are story-ready.

Where it slips into adjectives:
- **FR-27 Globalna pretraga** — "Pretraga obuhvata: nazive proizvoda, opise proizvoda, naslove blog objava, perex i telo blog objava" is in scope, but there's no testable consequence for ranking, partial-match behavior, diacritic handling (čćšž — critical for Serbian/Hungarian), or empty-results state. This is the single biggest done-ness gap.
- **FR-1** "Hero zauzima minimalno 70% visine viewporta na desktop-u" is testable, but "Polje za pretragu je locirano na desnom kraju glavnog menija" begs the question — on mobile? In hamburger? Not specified.
- **FR-12** "Comparison table dva modela (dimenzije) je prikazana na stranici" — singular line, no fields listed, no behavior when there are >2 models added later.
- **FR-32** Fallback marker — Consequence #2 says "diskretni vizuelni marker (badge ili tooltip — UX odluka)" which correctly defers visual but doesn't bound *what triggers* the marker (per field? per page? on hover only?). Story can't be written without that.
- **FR-35 Dashboard** — "Statistike prikazane: posete za 7/30 dana (iz GA), broj poruka u tekućem mesecu..." — these are listed but no specification for how lead-count is segmented by form type (FR-19 vs FR-22 vs FR-23). Given the lead-gen thesis, this is a substantive miss.
- **§5.1 Performance** — "u realističnom vremenom na 4G mobilnoj vezi" is exactly the "reasonable performance" anti-pattern the rubric flags. The `[OPEN → arhitektura]` defers it correctly, but the consequence text still uses an adjective.

### Findings
- **high** FR-27 Search underspecified — No bounds on diacritics (sr/hu), ranking, partial match, empty-state, locale filtering precedence. Search is the single hardest FR to story without these. *Fix:* add 4-5 testable consequences: case-insensitive, diacritic-insensitive for sr/hu, prefix+substring match, results grouped by type with type-counts, "no results" view with suggested alternatives.
- **high** FR-35 Dashboard doesn't segment lead types — Given the lead-gen thesis, dashboard needs per-form-type counts (Upit za model / Servisni zahtev / Upit za rezervni deo / Kontakt), not just "broj poruka". *Fix:* enumerate per-form counters; consider weekly trend.
- **medium** FR-32 fallback marker trigger underspecified — Marker visibility rules not bound. *Fix:* add "marker se prikazuje kad god se polje renderuje iz sr lokala dok je posetilac na hu/en" and "marker je inline uz polje, ne na page-level".
- **medium** FR-12 Comparison table fields not specified — Just "(dimenzije)". *Fix:* enumerate the comparison rows (kubatura, dimenzije D×Š×V, težina, ...) or defer with explicit `[OPEN → UX]`.
- **medium** §5.1 Performance still uses "realističnom vremenom" — Adjective. *Fix:* either pin a placeholder LCP target with `[ASSUMPTION]` (e.g., LCP < 2.5s on 4G, to validate in arch) or drop the bullet entirely and rely on `[OPEN → arhitektura]`.
- **low** FR-1 Search field on mobile not specified — Hamburger? Below header? *Fix:* add one consequence for mobile search field placement.

## Scope honesty — strong

§9 Non-Goals is the strongest section in the PRD. Eleven explicit exclusions, several with the *reasoning* baked in ("Migracija sa starog sajta — ne postoji stari sajt; 301 redirects, URL preserving, bekap pre migracije **otpadaju**"). Inline `[ASSUMPTION]` tags are used at 17 places and roundtrip cleanly to §13 Assumptions Index (I checked: every inline tag appears in the index, with section refs).

§14 Assumptions Index pulls together 17 items with explicit section refs — this is exactly the shape downstream phases need.

The two `[NOTE FOR PM]` callouts in §10.2 are honest deferrals ("bez ovoga je samo 'fire and forget'" for visitor profile is exactly the right kind of self-aware framing).

Open-items density is medium (17 assumptions + 8 open arch questions + 6 UX questions + 3 client/content questions = ~34 deferrals across 47 FRs). For an internal solo-dev PRD that explicitly defers performance budget and SMs to later phases, this is calibrated correctly. None of the deferrals would block an Architecture pass.

### Findings
*(no findings — section earns its verdict)*

## Downstream usability — strong

Glossary is the linchpin and it holds up: I spot-checked *Proizvod*, *Brend*, *Serija*, *Ponavljajući element*, *Slični modeli*, *Lightbox*, *Fallback*, *Locale*, *Editor* — all used verbatim in FRs where they appear. The Glossary itself flags one cross-reference ambiguity ("Priče sa polja — vizuelno različito od termina 'Blog' u admin panelu zbog jasnoće") which is exactly the kind of self-aware glossary discipline downstream artifacts need.

FR IDs FR-1 through FR-47 are contiguous (I counted: 47 distinct IDs, no gaps, no duplicates). Cross-references resolve: FR-5 → "Kontakt forma opisana u FR-19" (✓), FR-20 → "vidi Glossary" (✓), FR-26 → "vidi FR-44 Blog admin" — wait, FR-44 is Redirect manager, not blog admin. The correct reference is **FR-39** (CRUD blog objava). This is an active broken cross-reference.

UJs each have named protagonists (Marko / Stojan / Marijana) and each carries enough context inline that a UX designer could pull a UJ out alone. UJ-1 explicitly names the climax FRs (FR-19), UJ-2 ties to FR-22, UJ-3 to FR-36. Edge cases are called out per UJ — this is unusually high quality for UJ writing.

Sections are mostly extract-able alone. The only "see above" style reference I noticed is "Struktura analogna FR-9 (Jeegee), boja brenda primenjuje se na *Ponavljajući element*" in FR-11. That's a borderline call: the structure cross-ref is fine because the entity differs (HZM vs Jeegee), but if FR-9 changes shape, FR-11 silently drifts.

### Findings
- **high** Broken cross-reference in FR-26 — "vidi FR-44 Blog admin" but FR-44 is Redirect manager. Correct target is FR-39. *Fix:* change "FR-44 Blog admin" to "FR-39 CRUD blog objava sa WYSIWYG editorom".
- **low** FR-11 "Struktura analogna FR-9 (Jeegee)" — Implicit copy of FR-9 testable consequences without restating them. Brittle. *Fix:* either inline the 2-3 key consequences explicitly, or replace with "ista struktura kao FR-9" + mention specific deltas.

## Shape fit — strong

This is a multi-stakeholder consumer/B2B-lean web product (visitors browse, leads convert, admins author). The PRD shape matches: UJs are load-bearing (Marko/Stojan/Marijana cover the three load-bearing journeys), Glossary is heavy because domain nouns are heavy (Brend/Serija/Model/Kategorija/Potkategorija hierarchy is non-trivial), and the FRs are user-facing-feature-shaped rather than capability-shaped.

It's not over-formalized for solo-dev internal use. There's no enterprise rigor (no RACI, no detailed personas, no extensive compliance traceability), and there's no `[ASSUMPTION]` inflation. It's not under-formalized either — the multi-language fallback (FR-32), per-locale validation in FR-36, and GDPR cookie segmentation (FR-47) are exactly the substantive bits an internal-but-real-product PRD needs.

The form factor (chain-top, feeding UX → Architecture → Epics → Stories) is the right shape for the rubric: downstream usability matters more, which is why the broken cross-ref in FR-26 and the FR-27 Search underspec are real findings rather than nits.

### Findings
*(no findings — shape fit is correct)*

## Mechanical notes

- **Glossary drift:** Spot-checked 8 terms across FRs — no drift detected. Glossary uses Serbian latinica consistently. The *Model* / *Proizvod* synonym is explicitly called out in Glossary ("Model — sinonim za Proizvod u kontekstu navigacije; tehnički isti entitet") which is correct discipline.
- **ID continuity:** FR-1 through FR-47 are contiguous and unique. No UJ ID gaps (UJ-1, UJ-2, UJ-3). No SM IDs (deferred §11, which is correct).
- **Broken cross-refs:** One. FR-26 says "vidi FR-44 Blog admin"; FR-44 is Redirect manager. Should be FR-39. (Repeated above as a downstream-usability finding because it actively misroutes Epic creation.)
- **Assumptions Index roundtrip:** Checked all 17 inline `[ASSUMPTION]` tags against §13. All roundtrip. §13 also includes one assumption (Newsletter signup deferred) that's tagged `[NOTE FOR PM]` inline rather than `[ASSUMPTION]` — a minor classification inconsistency but it's correctly indexed.
- **UJ protagonist naming:** All three UJs have named protagonists (Marko, Stojan, Marijana) with context inline (30ha gazdinstvo / postojeći kupac / sadržaj-admin). No floating UJs.
- **Required sections:** §0 Document Purpose, §1 Vision, §2 Target User (+ JTBD + Non-Users + UJs), §3 Glossary, §4 Features, §5 NFRs, §6 Constraints, §7 Integration, §8 Operational, §9 Non-Goals, §10 MVP Scope, §11 SMs (deferred with reasoning), §12 Open Questions, §13 Assumptions Index — all present and proportionate to stakes.
- **Minor:** "Vezani fajlovi" at footer mentions `addendum.md` ("kreira se naknadno ako bude trebao") — informational, harmless.
