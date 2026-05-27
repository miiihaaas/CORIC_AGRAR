# Spine Pair Review — CORIC_AGRAR

## Overall verdict

The spine pair is a **strong, downstream-ready contract** for a solo-dev internal build. DESIGN.md tokens are dense, cross-resolving, and grounded in evidence from the HTML prototype and JPG mockups; EXPERIENCE.md covers all three UJs end-to-end with named protagonists, climax beats, and edge cases. The two main weaknesses are (a) **zero visual-reference inline links** despite three high-fidelity JPG mockups and an HTML prototype existing as sources, and (b) a small set of **token leaks and naming inconsistencies** (`section`/`section-mobile` under `spacing.scale` referenced inconsistently, `repeating-element` referenced in prose with localized name `Ponavljajući element` but not by token path, missing `shadow` tokens despite shadow values used in component specs). None of the findings are critical enough to block architecture phase consumption — but resolving the visual-reference orphans is a 15-minute task with outsized payoff for the architect.

## 1. Flow coverage — strong

Source frontmatter lists PRD with 3 UJs (UJ-1 Marko, UJ-2 Stojan, UJ-3 Marijana). EXPERIENCE.md § Key Flows covers all 3 in order with named protagonists, numbered surfaces, explicit climax beats, edge cases, and cross-spine references. UJ-2 and UJ-3 even have surface-specific UX subsections ("Mobile-specific UX", "Admin-specific UX") which is bonus rigor for downstream stories.

### Findings
- **low** Flow 3 has *two* climax beats labeled "Climax 1" and "Climax 2" (§ Key Flows → Flow 3, steps 8 and 10). The rubric expects a single climax beat. This is defensible (status flip + publish are distinct moments) but mildly nonstandard. *Fix:* either accept as-is (climax = the publish-toast at step 10, with step 8 reframed as setup) or note explicitly that admin flows have a save→publish two-beat climax pattern.

## 2. Token completeness — adequate

DESIGN.md frontmatter defines colors (4 brand greens + 2 accents + jeegee + 5 neutrals + 6 semantic), typography (family, weight, scale 7 levels, line-height 3, tracking 2), rounded (6 levels), spacing scale (9 numeric + section/section-mobile/container), and 7 component groups. All colors have hex. EXPERIENCE.md references to DESIGN tokens (e.g. `{colors.brand.green-800}`, `{components.accordion.default-open}`, `{colors.neutral.gray-700}`, `{colors.brand.green-400}`, `{colors.semantic.text-muted}`) resolve cleanly to the frontmatter. Contrast targets are stated for load-bearing pairs (§ Accessibility Floor lists 4 computed ratios).

### Findings
- **medium** **Shadow tokens are defined inline only, not in frontmatter.** DESIGN.md § Elevation & Depth specifies four shadow values (card base, hero overlay = none, modal backdrop, sticky nav shrunk) and `components.card.base.shadow` carries a literal hex-rgba string `"0 2px 8px rgba(31,63,47,0.06)"`. There is no `shadows` or `elevation` frontmatter group. Downstream code will either duplicate magic strings or invent its own token names. *Fix:* add `shadows: { card-base, sticky-nav, modal-backdrop, ... }` to frontmatter and have card component reference `{shadows.card-base}`.
- **medium** **`repeating-element` component cross-reference name is fuzzy.** EXPERIENCE.md § IA → Početna step 5 says "koristi *Ponavljajući element* kao vizuelni motiv" with no token path; DESIGN.md frontmatter has `components.repeating-element` but localized Serbian name "Ponavljajući element" is used in prose. The Glossary identity-check still works because both spines and the PRD use the same Serbian phrase, but architecture/dev consuming this needs to be told the token path is `components.repeating-element` (English kebab-case). *Fix:* either pin the convention in a one-line note ("Token paths use English kebab-case even when prose uses localized names") or rename the token to `ponavljajuci-element`.
- **low** **Spacing token `section` / `section-mobile`** live under `spacing.scale` in frontmatter but are referenced in DESIGN.md prose as "section = 80px desktop, 48px mobile" without the `{spacing.scale.section}` form. Self-referential, not a resolution failure, but inconsistent with how `{rounded.pill}` etc. are used. *Fix:* either reference by token in prose or move to a sibling `spacing.section` group.
- **low** **Lime-500 contrast is flagged as a "Rizik" in § Accessibility Floor but no rule is committed.** "verovatno ne koristi za body text" is hedged. *Fix:* commit — "Use lime-500 only on `green-900` background or as hover-only tint, never as a text color on white."
- **low** **Form input `outline-offset shadow (2px ring green-400 opacity 0.3)`** in DESIGN.md § Components → Form input is described in prose but not modeled as a component token (no `components.form-input.focus-ring`). Same pattern as the shadow issue. *Fix:* lift focus-ring values into a token.

## 3. Component coverage — strong

Components named in either spine: **button (3 variants), card (2 variants), repeating-element, accordion, pill-badge, wave-divider, form input, statistika medaljon, brošura card, lightbox, slider, sticky nav, search**. All have a row in DESIGN.md.Components (visual) *and* a behavioral rule in EXPERIENCE.md.Component Patterns. The Component Patterns section even includes a dedicated subsection ("Akordion specifikacije VS Akordion brand stranica") that resolves a non-obvious state divergence between FR-8 and FR-17 — that is exactly the kind of judgment call architecture phase cannot derive from tokens alone.

### Findings
- **low** **`statistika medaljon` and `brošura card` use Serbian-localized names** with no English token-path equivalent. They appear in DESIGN.md § Components prose but are not in `components.*` frontmatter, so EXPERIENCE.md cannot token-reference them. *Fix:* add `components.stat-medallion` and `components.brochure-card` frontmatter entries (or note that prose-only components are visual-spec-only by design).
- **low** **Lightbox, Slider, Sticky nav, Search** appear in EXPERIENCE.md § Component Patterns with rich behavior but have no DESIGN.md frontmatter token row and no DESIGN.md § Components visual-spec row. They have *some* visual values mentioned in DESIGN.md § Elevation & Depth (modal backdrop, sticky nav shadow), but nothing for slider chrome or search field. *Fix:* add at minimum a one-line entry in DESIGN.md § Components for each, even if it points back to base button/card/form tokens.

## 4. State coverage — strong

§ State Patterns is exemplary — 9 states (Default/Hover/Focus/Active/Disabled/Loading/Error/Empty/Selected) with token references and triggering conditions, plus a dedicated § Empty states sub-table with 5 context-specific copy patterns. § Accessibility Floor and § Interaction Primitives also cover reduced-motion, focus rings, ARIA. Forms cover validation, submit, success, error, loading. Lightbox covers focus-trap, Esc, click-out, focus restoration.

### Findings
- **low** **No "offline" / "no network" state pattern** beyond the single Network timeout sentence in § Interaction Primitives. The site has no PWA/offline goal in PRD, so this is fine — but if HTMX is the sole interactivity, a "network failed" state on filters / search dropdowns / form submits could use one shared pattern note. *Fix:* one line — "On HTMX network error: keep current UI state, surface inline error toast at top of affected region, retry available."
- **low** **No "permission denied" / 401 / 403 state** for admin surfaces. Admin login is mentioned, but if a session expires mid-form during Flow 3 there is no defined behavior. *Fix:* one line in § Key Flows → Flow 3 Edge cases or § State Patterns: "Session expiry on admin form save → redirect to /admin/login, preserve draft in localStorage."

## 5. Visual reference coverage — broken

Three high-quality JPG mockups exist (`docs/Dizajn/_Prikazi strana/Ćorić Agrar - Početna 4.0.jpg`, `Stranica brenda - 4.0.jpg`, `Stranica proizvoda 1.0.jpg`) and a working HTML prototype (`docs/Dizajn/_HTML/index.html`, `traktori.html`). Both spines list these in `sources` frontmatter and the decision log extracts decisions from them. **Neither spine links to any of these inline at the section they illustrate, and neither states the spines-win-on-conflict rule with a citation to a specific mockup file.** This is the single largest gap. The downstream architect cannot tell, when reading § IA → Početna, that `Početna 4.0.jpg` is the authoritative mockup; cannot tell, when reading § Components → Brošura card, that `Stranica proizvoda 1.0.jpg` confirms the outlined-card layout. The information is in `.decision-log.md` and `.working/extract-mockup-decisions.md` but those are scaffolding, not spine.

### Findings
- **high** **No inline visual-reference links from spine prose to source mockups.** *Fix:* add inline links at minimum to:
  - DESIGN.md § Components → Hero overlay → cite `_Prikazi strana/Ćorić Agrar - Početna 4.0.jpg` (hero card pattern) and `Stranica brenda - 4.0.jpg` (brand-page hero variant)
  - DESIGN.md § Components → Brošura card → cite `Stranica proizvoda 1.0.jpg` (confirmed outlined layout)
  - DESIGN.md § Components → Statistika medaljon → cite `Početna 4.0.jpg` and `Stranica brenda - 4.0.jpg`
  - EXPERIENCE.md § IA → Početna sekcijski raspored → cite `Početna 4.0.jpg`
  - EXPERIENCE.md § Key Flows → Flow 1 step 4 → cite `Stranica proizvoda 1.0.jpg`
- **medium** **Spines-win-on-conflict is stated** (DESIGN.md line 138, EXPERIENCE.md line 17) but the three known PRD-vs-mockup contradictions resolved in `.decision-log.md` (gradient footer, brand-specific UI chrome, search-as-icon) are not recorded in the spines themselves. A downstream consumer reading just the spines + PRD would not know these conflicts have been resolved. The DESIGN.md § Colors → Don'ts line "PRD §4.8 ažurira se" is the only hint. *Fix:* add a `## Conflicts resolved` section to one or both spines (or a separate `conflicts.md`) summarizing the three resolutions.

## 6. Bloat & overspecification — adequate

DESIGN.md carries appropriate editorial voice ("dostojanstveno, nikad veselo", "agrarni sektor je prizemljen", "senzualan agrarni feel"). EXPERIENCE.md prose is mostly behavioral and table-driven; no decorative narrative. No persona/FR/PRD restatement detected. Tables used appropriately (Voice and Tone mikrokopija, State Patterns, Animacije, Anti-patterns) instead of prose lists. Token references are used freely instead of duplicating values. The spines are dense without being long.

### Findings
- **low** **Some pixel specs sit alongside tokens where a pure-token form would be cleaner.** Examples: DESIGN.md § Components → Statistika medaljon `120px (desktop) / 80px (mobile)`, Brošura card `max-width 120px`, `3deg rotate`. These could either become `components.stat-medallion.size-desktop` tokens or stay literal — the call is fine for an internal solo-dev spec, just noting the inconsistency. *Fix:* none required; flag for future spec hygiene.
- **low** **Anti-patterns table** (EXPERIENCE.md § Inspiration & Anti-patterns) restates Don'ts that overlap with DESIGN.md § Do's and Don'ts (no auto-play with sound, no NOVO! pulsing badges). Overlap is small and reinforces, not bloats — defensible. *Fix:* none.

## 7. Inheritance discipline — adequate

`sources` frontmatter in both spines lists 4 paths each, identical between spines. UJ names verified verbatim: UJ-1 Marko, UJ-2 Stojan, UJ-3 Marijana — all match PRD § 2.3. Glossary terms used consistently: *Ponavljajući element*, *Priče sa polja*, *Brošura card*. Component names match across DESIGN.md frontmatter, DESIGN.md § Components prose, and EXPERIENCE.md § Component Patterns — except for the localized-name issue flagged in §2 and §3. EXPERIENCE.md token references all resolve to DESIGN.md frontmatter (verified spot-checks: `{colors.brand.green-800}`, `{colors.brand.green-400}`, `{colors.neutral.gray-700}`, `{components.accordion.default-open}`, `{colors.semantic.text-muted}` — all resolve).

### Findings
- **medium** **Source path `docs/Dizajn/_HTML/`** in both spines' frontmatter is a directory, not a file. The spec is permissive on this, but downstream graphify-style extraction tools usually want file-level paths. The HTML prototype is two files: `index.html` and `traktori.html`. *Fix:* expand to explicit file paths in `sources`.
- **low** **`sources` path `../../prds/prd-CORIC_AGRAR-2026-05-27/prd.md`** is correctly relative — verified the file exists at the resolved path. No fix.
- **low** **EXPERIENCE.md § Key Flows → Flow 1 Cross-spine references** lists `{components.brošura card}` with a Serbian space-separated name. The frontmatter has no such token; the prose-only "Brošura card" component is referenced. Same root cause as §3 finding. *Fix:* covered by §3 fix.

## 8. Shape fit — strong

**DESIGN.md sections in canonical order:** Brand & Style → Colors → Typography → Layout & Spacing → Elevation & Depth → Shapes → Components → Do's and Don'ts → Open Decisions. The first 8 are spec-canonical and in order. "Open Decisions" is an invented section but earns its place (centralizes `[ASSUMPTION]` / `[OPEN]` tags for downstream).

**EXPERIENCE.md required defaults:** Foundation ✓, IA ✓, Voice and Tone ✓, Component Patterns ✓, State Patterns ✓, Interaction Primitives ✓, Accessibility Floor ✓, Key Flows ✓. **Required-when-applicable:** Inspiration ✓ (sources/log mention Lemken as reference and explicit anti-patterns — both triggers met), Responsive ✓ (multi-surface web is the form factor). Invented section: "Open Decisions" — earns its place same way DESIGN.md does.

### Findings
- None at high or medium. The shape is clean.

## Mechanical notes

- **Frontmatter completeness:** Both spines have `title`, `status`, `created`, `updated`, `project`, `sources`. EXPERIENCE.md additionally has `design_spine: ./DESIGN.md` (good, makes pair-resolution explicit). Neither spine has an `owner` or `version` field; not required by the spec.
- **Mermaid syntax:** No Mermaid diagrams used (the sitemap and navigation tree are text-based). Defensible — text is more diff-friendly for internal solo-dev.
- **Markdown:** Clean. Tables render. Code fences used for sitemap. Headings nest correctly (h1 → h2 → h3 → h4) in both files.
- **Glossary cross-reference:** "Ponavljajući element" appears in DESIGN.md prose, EXPERIENCE.md prose, and PRD § 3 Glossary — all consistent localized phrasing.
- **Naming inconsistencies:**
  - `repeating-element` (frontmatter token) vs. *Ponavljajući element* (prose) vs. `Brošura card` (prose-only) vs. `statistika medaljon` (prose-only) — three different naming conventions in play. Pick one (recommend: English kebab-case for token paths, localized for prose, with a one-line convention note).
- **`[ASSUMPTION]` tags load-bearing check (Fast-path expectation):**
  - 8 `[ASSUMPTION]` and 2 `[OPEN]` tags total, all surfaced in dedicated § Open Decisions sections. Owner is implicit (solo-dev Mihas). None are load-bearing-without-owner — the spec format itself owns them. The brošura-card `3deg rotate` assumption is the only purely-aesthetic one; the rest are concrete numeric defaults a downstream developer can safely pick (5MB upload, 10s timeout, 6s slider). All defensible to leave open.
- **Cross-references verified resolving:**
  - `{colors.brand.green-800}` → frontmatter ✓
  - `{colors.brand.green-400}` → frontmatter ✓
  - `{colors.neutral.gray-700}` → frontmatter ✓
  - `{colors.semantic.text-muted}` → frontmatter ✓
  - `{components.accordion.default-open}` → frontmatter ✓
  - `{components.brošura card}` → **does not resolve** (no such token; prose component name)
