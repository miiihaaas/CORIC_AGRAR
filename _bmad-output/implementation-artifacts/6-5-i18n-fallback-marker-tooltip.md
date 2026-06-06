---
story_id: "6.5"
story-key: 6-5-i18n-fallback-marker-tooltip
title: i18n Fallback Marker (ⓘ Tooltip)
status: ready-for-dev
epic: 6
epic_num: 6
epic_title: SEO & Discoverability
module: core
created: 2026-06-06
last_modified: 2026-06-06
complexity: M
author: Mihas (SM autonomous; PETA story Epic 6 — SEO & Discoverability. NOVI presentation-layer deliverable u apps.core: diskretan ⓘ marker + tooltip kad se translated polje NE prevede za aktivnu locale i tiho padne na sr (FR-32 view-layer marker — base.py:153-156 ga eksplicitno imenuje „view-layer marker u Story 6.5"). **JEDAN artefakt:** NOVI `apps/core/templatetags/i18n_fallback.py` sa `{% translated_field obj 'name' %}` simple_tag(takes_context=True). **GLAVNA odluka (SM-D1) — CRUX: FALLBACK SE NE MOŽE DETEKTOVATI KROZ `obj.name`.** `MODELTRANSLATION_FALLBACK_LANGUAGES=("sr",)` (base.py:157) znači da `obj.name` na `/hu/` VEĆ tiho vraća sr vrednost kad je `name_hu` prazan (silent fallback — to je cela poenta fallback chain-a). Zato tag NE sme da poredi `obj.name` (uvek vraća rešenu vrednost) — mora da čita SIROVI per-locale accessor `getattr(obj, f"{field}_{get_language()}", _UNSET)` i testira da li je TA vrednost prazna/blank. Algoritam (SM-D1): (1) `lang = get_language()`; ako `lang == "sr"` (ili `lang is None`) → NIKAD marker (sr je izvor, nema fallback-a) → vrati plain escaped `obj.<field>`. (2) `current = getattr(obj, f"{field}_{lang}", _UNSET)`; ako accessor ne postoji (ne-translated polje / pogrešno ime) → tretiraj kao „popunjeno" (no marker, graceful — NE 500). (3) ako `current` truthy (popunjeno) → no marker → plain escaped vrednost. (4) ako `current` prazno/blank → FALLBACK → `sr_val = getattr(obj, f"{field}_sr", None)`; ako `sr_val` prazan → još uvek bez fallback teksta → plain escaped rešena vrednost bez markera (nema šta da se markira); inače → renderuj MARKER span sa sr tekstom + `lang="sr"`. **TAG TIP (SM-D2):** `simple_tag(takes_context=True)` (treba `get_language()` koji LocaleMiddleware aktivira po request-u; takes_context za jedinstveni id counter per-request preko `request`); vraća `format_html`/`mark_safe` — VREDNOST POLJA UVEK autoescaped (NIKAD `|safe` na obj content — XSS granica, mirror 6-1/6-3 SAFE pattern). **TOOLTIP (SM-D3): CSS-only, BEZ JS.** `aria-describedby` ↔ visually-hidden `<span role="tooltip" id="fallback-tooltip-N">` otkriven na `:hover`/`:focus-within` (CSS), `tabindex="0"` čini marker keyboard-focusable; `prefers-reduced-motion` respect; NE Bootstrap JS tooltip (project-context: vanilla JS preferred, no build pipeline, NIKAD jQuery; CSS-only je a11y-friendly + 0 JS init). Unique id per-marker kroz per-request brojač (`request` atribut counter) → deterministički `fallback-tooltip-1/2/...`. **TOOLTIP TEKST (SM-D4):** `gettext("Sadržaj na srpskom — još nije preveden")` (pune dijakritike) — runtime-evaluiran (NE `gettext_lazy` cache-ovan na import) → prikazuje se u VISITOR locale (hu/en/sr); mark-for-translation u .po (hu/en prevodi = TEA/Dev dodaju msgid + fuzzy ili follow-up OQ-2). **IKONA (SM-D5) — DEPENDENCY: Bootstrap Icons NIJE vendirana** (static/vendor/ ima samo bootstrap-5.3.3 CSS/JS-bundle BEZ icons font, glightbox, htmx, nouislider; `bi-info-circle` se NIGDE ne učitava → epics:975 `<i class="bi-info-circle">` bi bio NEVIDLJIV prazan `<i>`). Odluka: INLINE SVG ⓘ (info-circle path, `aria-hidden="true"`, `focusable="false"`, `fill="currentColor"`, width/height kroz CSS `em`) — NE vendiraj ceo Bootstrap Icons font (~100KB+ za JEDNU ikonu = anti-perf; project-context perf budget). SVG je 1 path, 0 novih asseta, currentColor nasleđuje marker boju. (epics:975 `bi-info-circle` je ilustrativan — IN-SCOPE realnost je inline SVG; AC dokumentuje.) **CSS (SM-D6):** NOVI `static/css/components/i18n-fallback-marker.css` @import u main.css (mirror per-component @import pattern); `.coric-fallback-marker` + `__icon` + `__tooltip` BEM, SAMO `var(--...)` tokeni (NE magic vrednosti — color-semantic-text-muted/focus-ring, spacing, rounded, shadow, typography-scale-caption za tooltip), kontrast 4.5:1, focus-visible outline, prefers-reduced-motion. **ADOPCIJA (SM-D7):** tag je site-wide dostupan; v1 FOKUSIRANO usvajanje na detail H1/naziv — `templates/partials/hero_overlay_card.html` (product/brand hero title — `title=product.name`/`brand.name`) + `templates/blog/post_detail.html` H1 (`{{ post.title }}`). Ostali šabloni = inkrementalno (out of scope v1). **0 MIGRACIJA, 0 model promene, 0 novih dep-ova, 0 vendiranih asseta.** RISK TIER: MEDIUM — (a) NOVI template tag sa NETRIVIJALNOM business logikom (fallback-detekcija je crux — pogrešno čitanje `obj.name` umesto per-locale accessora = marker NIKAD ne radi ILI radi pogrešno); (b) presentation/a11y surface (tabindex/aria-describedby/lang/tooltip — WCAG); (c) NOVI CSS (tokeni + prefers-reduced-motion + kontrast); (d) DEPENDENCY: bi-info-circle nije učitana → inline SVG odluka. NEMA migracije/auth/forme/HTMX/eksternog poziva — čist render tag + CSS.)
depends_on:
  - 1-4-i18n-setup-sa-locale-url-routing-i-switcher          # MODELTRANSLATION_FALLBACK_LANGUAGES=("sr",) (base.py:157) — SRŽ: `obj.name` VEĆ tiho pada na sr, zato tag MORA čitati per-locale accessor `name_<lang>` (SM-D1); LANGUAGE_CODE="sr"/LANGUAGES=[sr,hu,en] (base.py:148-158) → `get_language()` vraća aktivnu locale (LocaleMiddleware); i18n_patterns /hu/proizvod/... putanja (AC primer)
  - 2-2-product-i-related-modeli                              # Product.name/.description/.key_features translatable (apps/products/translation.py) → `name_sr/_hu/_en` virtuelna polja koje tag čita; primarni adopcija target (product hero title)
  - 5-1-blogpost-category-tag-modeli-admin-stub              # Post.title/.perex/.body translatable (apps/blog/translation.py) → `title_sr/_hu/_en`; blog post_detail H1 adopcija target (post.title)
  - 1-7-reusable-visual-komponente                           # templates/partials/hero_overlay_card.html (product+brand hero `title=` param) — adopcija target (SM-D7); per-component CSS @import pattern u main.css; `coric-` BEM prefiks; var(--...) token disciplina
  - 1-5-self-hosted-roboto-design-md-tokens-kao-css-custom-properties  # static/css/tokens.css :root tokeni (color-semantic-text-muted/focus-ring, spacing-scale, rounded, shadow, typography-scale-caption) → marker/tooltip CSS konzumira SAMO ove (SM-D6, NE magic vrednosti); main.css @import struktura
---

# Story 6.5: i18n Fallback Marker (ⓘ Tooltip)

Status: ready-for-dev

## Opis

As a **posetilac (na hu/en verziji sajta)**,

I want **da vidim diskretan ⓘ indikator (sa tooltip-om) pored teksta koji je fallback na srpski jer prevod za moju locale još ne postoji**,

so that **razumem zašto je taj deo teksta na srpskom dok je ostatak strane na mom jeziku — umesto da pomislim da je sajt pokvaren ili nedosledan**.

Ovo je **PETA story Epic 6 (SEO & Discoverability)** i ima **JEDAN deliverable**: NOVI `apps/core/templatetags/i18n_fallback.py` sa `{% translated_field obj 'name' %}` template tag-om koji DETEKTUJE da li translated polje koristi sr-fallback za aktivnu locale i — ako koristi — renderuje diskretan `coric-fallback-marker` span (sr tekst + inline ⓘ SVG + CSS-only tooltip „Sadržaj na srpskom — još nije preveden", lokalizovan), sa `lang="sr"` atributom na fallback tekstu.

> **GLAVNA odluka (SM-D1) — CRUX: FALLBACK SE NE MOŽE DETEKTOVATI KROZ `obj.name`.** Projekt ima `MODELTRANSLATION_FALLBACK_LANGUAGES = ("sr",)` (base.py:157). To znači: kad je `name_hu` prazan, `obj.name` na `/hu/` **VEĆ tiho vraća `name_sr`** (silent fallback — to je svrha fallback chain-a, Story 1.4/2.2). Zato tag koji bi poredio `obj.name` protiv nečega NE BI MOGAO da detektuje fallback — `obj.name` UVEK vraća rešenu (možda već fallback-ovanu) vrednost. **Rešenje:** tag čita **SIROVI per-locale accessor** `getattr(obj, f"{field}_{get_language()}")` i testira da li je TA konkretna kolona prazna. Prazna `name_hu` + neprazna `name_sr` = FALLBACK → marker. (Vidi AC1/Task 2 za precizan algoritam i sve edge-case-ove.)

> **A11y + DEPENDENCY napomena (SM-D3/SM-D5):** Tooltip je **CSS-only** (`aria-describedby` ↔ visually-hidden clip-pattern `role="tooltip"` span — **DETE markera**, otkriven DESCENDANT selektorom na `.coric-fallback-marker:hover`/`:focus`/`:focus-within`; `tabindex="0"` za keyboard fokus) — NE Bootstrap JS tooltip (project-context: vanilla JS preferred, no build pipeline, NIKAD jQuery). Ikona je **inline SVG ⓘ** jer **Bootstrap Icons NIJE vendirana** u `static/vendor/` (samo bootstrap-5.3.3, glightbox, htmx, nouislider) — `bi-info-circle` klasa iz epics:975 bi renderovala NEVIDLJIV prazan `<i>`. Vendiranje celog icon font-a (~100KB+) za jednu ikonu = anti-perf → inline SVG path (0 novih asseta, `currentColor`).

### IN SCOPE (šta ova story isporučuje)

1. **NOVI `apps/core/templatetags/i18n_fallback.py`** (AC1/AC2/AC3/AC4) — DRUGI tag-modul u apps.core (uz `htmx_aria.py`). Sadrži:
   - `@register.simple_tag(takes_context=True)` `translated_field(context, obj, field)` — vraća safe HTML: ili plain escaped vrednost polja (no fallback), ili `coric-fallback-marker` span (fallback) (SM-D1/SM-D2).
   - `_FALLBACK_TOOLTIP_TEXT` runtime tooltip tekst kroz `gettext("Sadržaj na srpskom — još nije preveden")` (SM-D4 — pune dijakritike; runtime, NE lazy-cache, da se prevodi po visitor locale).
   - Pomoćna detekcija (može inline ili helper `_is_fallback(obj, field, lang)`): per-locale accessor čitanje + prazno-test (SM-D1).
   - Per-request id counter za jedinstveni `fallback-tooltip-N` ↔ `aria-describedby` par (SM-D3 — atribut `request._coric_fallback_counter`; request=None → modul-level `itertools.count(1)` fallback, NIKAD statična string-konstanta).
   - `format_html`/`mark_safe` emisija sa autoescaped vrednošću polja + inline SVG ⓘ (SM-D5).
2. **NOVI `static/css/components/i18n-fallback-marker.css`** (AC5, SM-D6) — `.coric-fallback-marker` + `__icon` + `__tooltip` BEM, SAMO `var(--...)` tokeni, focus-visible, kontrast 4.5:1, prefers-reduced-motion.
3. **`static/css/main.css` EDIT** (SM-D6) — `@import url('./components/i18n-fallback-marker.css');` (mirror postojeći per-component @import).
4. **Adopcija u v1 fokusirani set šablona** (AC6, SM-D7):
   - `templates/partials/hero_overlay_card.html` — H1 postaje `{% if fallback_obj %}{% translated_field fallback_obj fallback_field %}{% else %}{{ title }}{% endif %}` (SM-D7 opcija A — backward-compatible opt-in; `fallback_obj`/`fallback_field` OPCIONI). `products/_hero_section.html` prosleđuje `fallback_obj=product fallback_field='name'`; `brands/_hero_section.html` prosleđuje `fallback_obj=brand fallback_field='name'`. Pozivaoci bez `fallback_obj` (home/listing/about/brand-specific) → `{{ title }}` identično kao pre (zero blast-radius).
   - `templates/blog/post_detail.html:19` — `<h1 ...>{{ post.title }}</h1>` → `<h1 ...>{% translated_field post 'title' %}</h1>`.
5. **i18n prevod tooltip-a** (SM-D4, required-for-done) — `gettext` tooltip msgid registrovan; `makemessages` pokupi ga; **hu i en .po prevodi DODATI u ovoj story** (hu „A tartalom szerb nyelven — még nincs lefordítva", en „Content in Serbian — not yet translated") + `compilemessages`. Task 6.

### OUT OF SCOPE (eksplicitno — granice)

- **hreflang HTML `<link rel="alternate">` tagovi + locale-aware slug-ovi** = **Story 6.6** (`apps/seo/templatetags/hreflang.py`). 6.5 NE dodaje hreflang. (6.5 je VIDLJIV per-polje marker za posetioca; 6.6 je MAŠINSKI hreflang za crawler.)
- **Bootstrap Icons font vendiranje** = **NE** (SM-D5 — inline SVG za JEDNU ikonu; ceo font je anti-perf; ako budući epic uvede 10+ bi-ikona, vendiranje je tada opravdano — OQ-3).
- **Bootstrap JS tooltip (`data-bs-toggle="tooltip"` + JS init)** = **NE** (SM-D3 — CSS-only; no-build-pipeline + a11y `:focus-within`; bootstrap.bundle.js JE učitan ali tooltip zahteva eksplicitan `new bootstrap.Tooltip()` init JS = nepotreban JS surface).
- **Auto-adopcija tag-a na SVE translated polja site-wide** = **NE** (SM-D7 — v1 je FOKUSIRAN na detail naziv/naslov; description/perex/key_features/spec-ovi = inkrementalno, buduća polish story; OQ-1). Tag je dostupan, ali NE forsiramo sveobuhvatnu zamenu `{{ obj.field }}` u v1.
- **Model promene / migracije** = **NE** (0-migration; tag SAMO ČITA postojeća `_sr/_hu/_en` polja; `makemigrations --check` mora ostati čist).
- **Admin badge / „X polja neprevedeno" indikator u admin-u** = **NE** (to je content-editor UX, Epic 8.6 multi-locale CRUD; 6.5 je PUBLIC-facing visitor marker).
- **hu/en stvarni prevodi tooltip msgid-a** = **IN SCOPE (required-for-done, Task 6.2):** hu „A tartalom szerb nyelven — még nincs lefordítva" + en „Content in Serbian — not yet translated" se DODAJU u ovoj story (ne defer) — i18n-fallback marker sa ne-prevedenim tooltip-om bi bio ironičan. Bez prevoda tooltip BI radio (sr msgid fallback), ali to nije prihvatljivo done-stanje za hu/en posetioca.
- **Marker na ne-translated polja (`slug`, brojevi, FK)** = N/A — tag na ne-translated/nepostojeći accessor → graceful no-marker (plain vrednost), NE 500 (SM-D1 edge-case).

### Princip

JEDAN tanak presentation tag + jedan CSS fajl, oba LOW-COUPLING. Tag duck-tipuje (NE import-uje modeltranslation interne / NE isinstance — mirror `seo_meta._display_title` pattern): čita per-locale accessor `getattr(obj, f"{field}_{get_language()}")` (jedini pouzdan signal jer `obj.field` već fallback-uje). `lang == "sr"` → nikad marker (sr je izvor). Vrednost UVEK kroz `format_html` autoescape (XSS granica — NIKAD `|safe`; mirror 6-1/6-3). Tooltip CSS-only (0 JS), inline SVG ⓘ (0 vendor asseta). `lang="sr"` na fallback tekstu (screen-reader prebacuje izgovor; WCAG 3.1.2 Language of Parts). `aria-describedby` ↔ jedinstveni per-request id. CSS SAMO var(--...) tokeni + prefers-reduced-motion + focus-visible. 0 migracija, 0 model promene, 0 novih dep-ova. NEMA defensive boilerplate-a; NEMA premature site-wide adopcije (fokusiran v1 set).

### Strukturna arhitektura — repository delta

**2 NOVA fajla (`apps/core/templatetags/i18n_fallback.py` + `static/css/components/i18n-fallback-marker.css`) + 3 EDIT (`static/css/main.css` @import + 2 šablona adopcija) + (opciono) .po mark-for-translation + 0 MIGRACIJA + 0 model promene + 0 novih dep-ova + 0 vendiranih asseta.**

| Path | Tip | Razlog |
|---|---|---|
| `apps/core/templatetags/i18n_fallback.py` | NOVO | `{% translated_field obj field %}` `simple_tag(takes_context=True)`: fallback-detekcija kroz per-locale accessor (SM-D1) + marker span (sr tekst + inline SVG ⓘ + tabindex/aria-describedby/lang="sr") + CSS-only tooltip ref + per-request id counter (SM-D3) + `gettext` tooltip tekst (SM-D4) + `format_html` autoescape (SM-D2). DRUGI tag u apps.core (uz htmx_aria.py). (AC1-AC4) |
| `static/css/components/i18n-fallback-marker.css` | NOVO | `.coric-fallback-marker`/`__icon`/`__tooltip` BEM, SAMO var(--...) tokeni (color-semantic-text-muted/focus-ring, spacing-scale, rounded, shadow, typography-scale-caption), focus-visible outline, kontrast 4.5:1, prefers-reduced-motion (SM-D6/AC5). |
| `static/css/main.css` | EDIT | `@import url('./components/i18n-fallback-marker.css');` (per-component @import pattern; SM-D6). |
| `templates/blog/post_detail.html` | EDIT | `:19` `<h1 ...>{{ post.title }}</h1>` → `<h1 ...>{% translated_field post 'title' %}</h1>` + `{% load i18n_fallback %}` (vrh). Adopcija (SM-D7/AC6). |
| `templates/partials/hero_overlay_card.html` | EDIT (SM-D7 opcija A) | `{% load i18n_fallback %}` + H1 postaje `{% if fallback_obj %}{% translated_field fallback_obj fallback_field %}{% else %}{{ title }}{% endif %}`. **OPCIONI** `fallback_obj`/`fallback_field` param-i → pozivaoci koji ih ne prosleđuju (home/listing/about/brand-specific hero) padaju na `{{ title }}` IDENTIČNO kao pre (zero blast-radius). (Task 5.2a) |
| `templates/products/partials/_hero_section.html` | EDIT (SM-D7 opcija A) | Include dobija `fallback_obj=product fallback_field='name'` (uz postojeći `title=product.name`). Product hero `/hu/proizvod/...` ⓘ marker (epics:976). (Task 5.2b) |
| `templates/brands/partials/_hero_section.html` | EDIT (SM-D7 opcija A) | Sva 4 include-a dobijaju `fallback_obj=brand fallback_field='name'`. Brand hero ⓘ marker. (Task 5.2c) |
| `locale/hu/LC_MESSAGES/django.po` + `locale/en/LC_MESSAGES/django.po` (+ `.mo`) | EDIT (REQUIRED, SM-D4) | tooltip msgid „Sadržaj na srpskom — još nije preveden" mark-for-translation (`makemessages`) + OBAVEZAN hu prevod „A tartalom szerb nyelven — még nincs lefordítva" + en „Content in Serbian — not yet translated" + `compilemessages` (.mo). Task 6.2. |
| `apps/core/tests/test_i18n_fallback.py` | NOVO (TEA) | RED-phase testovi (vidi Testing). Dev NE piše testove. |
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | EDIT | `6-5-i18n-fallback-marker-tooltip` → `ready-for-dev`. SM handoff tracking (NIJE deliverable). |

**NETAKNUTO (regression guards):** SVI modeli + migracije (`makemigrations --check --dry-run` mora reći „No changes detected" — 6.5 SAMO čita `_sr/_hu/_en` polja); `config/settings/base.py` (MODELTRANSLATION_FALLBACK_LANGUAGES/LANGUAGES — 6.5 ČITA fallback config, NE menja ga); `apps/core/templatetags/htmx_aria.py` (postojeći tag — NE dira; i18n_fallback je NOVI fajl uz njega); `apps/seo/templatetags/seo_meta.py` (6-1/6-3 — `_display_title` je referentni pattern, NE menja se); `static/css/tokens.css` (SAMO konzumira tokene); `pyproject.toml` (0 novih dep-ova — `get_language`/`gettext`/`format_html`/`mark_safe` su Django core); SVE postojeće CSS komponente (NOVI @import na kraj liste, NE menja postojeće); `templates/base.html` (NE dira; marker je inline u content šablonima, NE u head/chrome).

## Kriterijumi prihvatanja

**AC1 — `{% translated_field obj 'name' %}` tag detektuje fallback kroz per-locale accessor, NE kroz `obj.name` (SM-D1, CRUX)**

- **Given** `MODELTRANSLATION_FALLBACK_LANGUAGES=("sr",)` (base.py:157) — `obj.name` VEĆ tiho fallback-uje na sr kad je `name_<lang>` prazan
- **When** kreiram `apps/core/templatetags/i18n_fallback.py:translated_field(context, obj, field)` koji:
  - **NORMALIZUJ locale na osnovni jezik (BCP-47):** `lang = (get_language() or "sr").split("-")[0]`. `get_language()` može vratiti region subtag (`"en-us"`, `"sr-latn"`); modeltranslation kolone su `name_en`/`name_sr` (BEZ subtag-a) → bez normalizacije `getattr(obj, "name_en-us")` UVEK promaši → marker se TIHO nikad ne pojavi za engleski (silent-failure). `.split("-")[0]` mapira `en-us`→`en`, `sr-latn`→`sr`. Koristi `lang` (normalizovan) i za accessor i za `lang == "sr"` proveru.
  - ako `lang == "sr"` (uključuje normalizovani `sr-latn` i izvorni `None`→`"sr"`) → vrati plain escaped `getattr(obj, field)` (NIKAD marker — sr je izvorni jezik, nema fallback-a)
  - inače `current = getattr(obj, f"{field}_{lang}", _UNSET)`:
    - ako `current is _UNSET` (accessor ne postoji — ne-translated polje / pogrešno ime) → plain escaped `getattr(obj, field, "")` (graceful, NE 500)
    - ako `current` truthy (popunjeno za ovu locale) → plain escaped `current` (NEMA fallback-a)
    - ako `current` prazno/blank (None ili `""` ili samo whitespace) → `sr_val = getattr(obj, f"{field}_sr", None)`; ako `sr_val` truthy → **MARKER** (vidi AC2) sa `sr_val` tekstom; ako `sr_val` takođe prazan → plain escaped rešena vrednost (nema teksta za markiranje)
- **Then**:
  - Na `/hu/` sa `Product(name_sr="Agri-Tracking TB804", name_hu="")` → tag detektuje fallback (čita `name_hu==""`, NE `obj.name` koji bi vratio sr) → renderuje marker
  - Na `/hu/` sa `Product(name_sr="X", name_hu="Y")` → `name_hu` popunjen → NO marker → plain „Y"
  - Na `/sr/` (bilo koji objekat) → NIKAD marker (lang==sr)
- **And** tag NIGDE ne poredi `obj.name` (rešenu vrednost) protiv sr — koristi ISKLJUČIVO per-locale accessor `name_<lang>` (jer `obj.name` već fallback-uje → beskorisno za detekciju)

**AC2 — Fallback render: marker span sa sr tekstom + inline SVG ⓘ + a11y atributi + lang="sr" (epics:975, SM-D2/D3/D5)**

- **Given** detektovan fallback (AC1) sa `sr_val = "Agri-Tracking TB804"`
- **When** tag renderuje
- **Then** izlaz je (semantički ekvivalent — tačan markup Dev odlučuje u granicama). **KRITIČNO — tooltip `<span>` je DETE (child) `.coric-fallback-marker` span-a (UNUTAR njega, posle teksta+ikone), NE adjacent sibling:**
  ```html
  <span class="coric-fallback-marker" tabindex="0" aria-describedby="fallback-tooltip-1" lang="sr">Agri-Tracking TB804 <svg class="coric-fallback-marker__icon" aria-hidden="true" focusable="false" ...>...</svg><span class="coric-fallback-marker__tooltip" id="fallback-tooltip-1" role="tooltip">Sadržaj na srpskom — još nije preveden</span></span>
  ```
  - `class="coric-fallback-marker"` + `tabindex="0"` (keyboard-focusable) + `aria-describedby="fallback-tooltip-N"`
  - **tooltip span je UNUTAR `.coric-fallback-marker` (poslednje dete, posle teksta i SVG ikone)** — ovo čini reveal CLEAN DESCENDANT selektor (`.coric-fallback-marker:hover .coric-fallback-marker__tooltip` / `:focus .coric-fallback-marker__tooltip`); NIJE adjacent sibling (sibling-combinator NE bi matchovao descendant selektor → tooltip se NIKAD ne bi otkrio na hover/focus). `aria-describedby` na markeru referencira `id` tooltip-deteta — to radi BEZ obzira na DOM ugnježdenje (id-referenca nije DOM-pozicija).
  - `lang="sr"` na elementu koji sadrži sr fallback tekst (epics:978 — WCAG 3.1.2 Language of Parts)
  - sr tekst je AUTOESCAPED (kroz `format_html` — NE `|safe`)
  - inline SVG ⓘ sa `aria-hidden="true"` + `focusable="false"` (dekorativna; SM-D5 — NE `bi-info-circle` klasa jer Bootstrap Icons nije vendirana). **epics:975 `bi-info-circle` je ILUSTRATIVAN — Bootstrap Icons NIJE vendirana u `static/vendor/` → inline SVG (stvarni `info-circle` path, vidi Task 1.4) je JEDINI ispravan render; `<i class="bi-info-circle">` bi bio nevidljiv prazan `<i>`.** **SVG konstanta MORA biti `mark_safe`-ovana** da bi je `format_html` propustio kao SafeString (inače `format_html`/`conditional_escape` escape-uje SVG u literal `&lt;svg&gt;`); `conditional_escape` preskače `SafeString` → `format_html("…{}…", _INFO_ICON_SVG)` je ispravno SAMO ako je `_INFO_ICON_SVG = mark_safe("<svg…>")` (statički markup, NE user input — bezbedno).
  - tooltip `<span role="tooltip" id="fallback-tooltip-N">` (dete markera) sa lokalizovanim tekstom (AC4)
- **And** `aria-describedby` vrednost TAČNO matchuje tooltip `id` (par; AC3)
- **And** tooltip je u DEFAULT stanju VISUALLY-HIDDEN clip pattern-om (vidi AC5: `position:absolute; width:1px; height:1px; clip-path:inset(50%); overflow:hidden; white-space:nowrap;`) — ostaje u a11y stablu za `aria-describedby` asocijaciju; otkriva se SAMO na `:hover`/`:focus` markera (descendant selektor)

**AC3 — Jedinstveni `fallback-tooltip-N` id po markeru (aria-describedby ↔ tooltip id par) (SM-D3)**

- **Given** strana sa VIŠE fallback markera (npr. naslov + opis oba fallback-uju)
- **When** renderujem stranu
- **Then** svaki marker dobija JEDINSTVEN `id` (`fallback-tooltip-1`, `fallback-tooltip-2`, ...) preko per-request brojača (atribut `request._coric_fallback_counter` na `context["request"]`, inkrementiran po markeru)
- **And** `aria-describedby` svakog markera == `id` njegovog tooltip-a (NEMA kolizije id-eva → screen-reader pravilno pridružuje tooltip)
- **And** PRIMARNA putanja je per-request brojač (`request._coric_fallback_counter`) koji se resetuje svaki request → deterministički `-1/-2/...`. (Modul-level `itertools.count(1)` NIJE primaran — koristi se SAMO kao fallback kad `request` nije u context-u; vidi sledeći bullet i G5. NE čitaj ovo kao zabranu `itertools.count` — modul-level brojač JE ispravan request=None fallback, konzistentno sa Task 3.1.)
- **And** kad `request` NIJE u context-u (shell / management / test render bez HTTP konteksta) → id se generiše iz **modul-level monotonog brojača** (`itertools.count(1)`) tako da id-evi OSTANU JEDINSTVENI unutar render-a (prihvatamo cross-request ne-determinizam u toj degenerisanoj putanji). **ZABRANJENO je vraćati statičnu string-konstantu (`"fallback-tooltip-x"`)** — to bi dalo SVIM markerima ISTI id → `aria-describedby` bi vezao sve markere za PRVI tooltip (slomljena a11y asocijacija). NE 500.
- **And** testovi asertuju JEDINSTVENOST id-eva + `fallback-tooltip-…` PATTERN (+ `aria-describedby`↔`id` match), **NE tačnu hardkodiranu vrednost** (modul-level fallback putanja čini tačnu vrednost ne-determinističkom → hardkodiran assert bi bio brittle)

**AC4 — Tooltip tekst lokalizovan po VISITOR locale „Sadržaj na srpskom — još nije preveden" (SM-D4)**

- **Given** marker se renderuje
- **When** posetilac je na `/hu/` vs `/en/` vs `/sr/`
- **Then** tooltip tekst je rezultat `gettext("Sadržaj na srpskom — još nije preveden")` evaluiran u VISITOR locale (hu prevod ako postoji, inače sr msgid fallback)
- **And** msgid koristi PUNE dijakritike („Sadržaj", „srpskom", „još", „preveden" — č/š/đ gde treba; project-context NIKAD šišana latinica)
- **And** tekst je runtime-evaluiran (`gettext`, NE `gettext_lazy` keširan na import-u) → reaguje na aktivnu locale po request-u
- **And** msgid je mark-for-translation (`makemessages` ga pokupi); **hu i en prevod su DODATI u ovoj story** (Task 6.2, required-for-done): hu „A tartalom szerb nyelven — még nincs lefordítva", en „Content in Serbian — not yet translated"; `compilemessages` regeneriše `.mo` → `/hu/` prikazuje hu, `/en/` en tooltip (bez prevoda bi prikazao sr msgid — graceful, ali NIJE done-stanje za ovu story)

**AC5 — `.coric-fallback-marker` CSS: BEM + var(--...) tokeni + CSS-only tooltip + a11y (SM-D6)**

- **Given** NOVI `static/css/components/i18n-fallback-marker.css` @import-ovan u main.css; tooltip span je DETE `.coric-fallback-marker` span-a (AC2)
- **When** marker se renderuje
- **Then**:
  - `.coric-fallback-marker__tooltip` je u DEFAULT stanju VISUALLY-HIDDEN clip pattern-om (mirror Bootstrap `.visually-hidden` koji projekt već koristi u `templates/blog/post_detail.html:23`): `position:absolute; width:1px; height:1px; clip-path:inset(50%); overflow:hidden; white-space:nowrap;` — **NE `display:none`, NE `visibility:hidden`, NE bare `opacity:0`** (display/visibility uklanjaju element iz a11y stabla → lome `aria-describedby`; bare opacity ostavlja layout/AT-tree dvosmislenost). Tooltip OSTAJE u a11y stablu za `aria-describedby` asocijaciju.
  - tooltip se otkriva DESCENDANT selektorom **`.coric-fallback-marker:hover .coric-fallback-marker__tooltip`** I **`.coric-fallback-marker:focus .coric-fallback-marker__tooltip`** (ili `:focus-within`) — prebacuje u vidljivo pozicionirano stanje: `position:absolute; width:auto; height:auto; clip-path:none; overflow:visible; white-space:normal;` + placement uz marker (npr. ispod/iznad, u praznom prostoru — WCAG 1.4.13/G10), `z-index` iznad sadržaja, `max-width` (token), **`background: var(--color-brand-green-800)` (PINNED) + `color: var(--color-semantic-text-on-dark)` → ~11.5:1 (≥4.5:1)**. (CSS-only — 0 JS; SM-D3. **Descendant selektor radi SAMO jer je tooltip dete markera — AC2 markup restrukturiran; adjacent-sibling NE bi matchovao.**)
  - SVE vrednosti su `var(--...)` tokeni (boja=`--color-semantic-text-muted`/`--color-semantic-focus-ring`; razmak=`--spacing-scale-*`; radius=`--rounded-*`; senka=`--shadow-*`; tooltip font=`--typography-scale-caption`) — NIJEDNA magic vrednost (project-context); izuzetak su clip-pattern primitivi (`1px`, `inset(50%)`, `auto`, `none`) koji su deo a11y idioma, NE dizajn-magic.
  - kontrast teksta/ikone/tooltip-a ≥ 4.5:1 (WCAG 2.1 AA; project-context)
  - `tabindex="0"` marker ima vidljiv `:focus-visible` outline (keyboard fokus)
  - `@media (prefers-reduced-motion: reduce)` — tooltip reveal bez tranzicije/animacije (instant; project-context A11y #7)
  - **WCAG 1.4.13 „Content on Hover or Focus" (Dismissable/Hoverable/Persistent):** (a) **Hoverable/Persistent** — descendant reveal je vezan za `.coric-fallback-marker:hover`/`:focus`/`:focus-within`, pa tooltip OSTAJE vidljiv dok je marker hover-ovan ILI fokusiran (ne nestaje na pokušaj prelaska miša preko njega jer je tooltip DETE markera → hover ostaje na markeru). (b) **Dismissable** — keyboard korisnik gasi tooltip blur-om (Tab dalje). Pure-CSS tooltip NE može Esc-to-dismiss (nema JS); to je PRIHVATLJIVO po 1.4.13 SAMO ako tooltip NE zaklanja drugi esencijalni sadržaj — zato placement mora biti tako da NE prekriva kritičnu UI (npr. ispod naslova u praznom prostoru, ne preko susednog dugmeta/linka). (c) **max-width token** ograničava širinu; near-viewport-edge overflow (tooltip isečen na ivici ekrana) je PRIHVATLJIVO v1 ograničenje (CSS-only, bez JS reposition-a) — placement bira stranu sa više prostora gde je trivijalno.
  - **Print stylesheet:** tooltip je interaktivni hover/focus element — bez posebnog `@media print` pravila tooltip ostaje clip-hidden u print-u (prihvatljivo: marker tekst + ikona se štampaju, tooltip ne). Ako se doda `@media print`, marker NE sme biti skriven (sr fallback tekst MORA ostati u štampi). v1: nema posebnog print pravila (default clip-hidden tooltip je OK za print).
- **And** ikona je `em`-skalirana (prati font-size naslova) + `currentColor` (nasleđuje marker boju)

**AC6 — Adopcija u v1 fokusirani set + site-wide dostupnost (SM-D7)**

- **Given** tag registrovan u `apps/core/templatetags/i18n_fallback.py`
- **When** Dev usvoji tag u v1 set
- **Then**:
  - `templates/blog/post_detail.html` H1 koristi `{% translated_field post 'title' %}` (sa `{% load i18n_fallback %}`)
  - **Product I Brand hero naslov koriste opt-in adopciju (SM-D7 opcija A — USVOJENA):** `hero_overlay_card.html` H1 render je `{% if fallback_obj %}{% translated_field fallback_obj fallback_field %}{% else %}{{ title }}{% endif %}` (sa `{% load i18n_fallback %}` u partialu); `products/partials/_hero_section.html` prosleđuje `fallback_obj=product fallback_field='name'`, `brands/partials/_hero_section.html` prosleđuje `fallback_obj=brand fallback_field='name'`
- **And** posetilac na `/hu/proizvod/agri-tracking-tb804/` (gde `name_hu` prazan) vidi sr naziv sa ⓘ markerom u hero H1 (epics:976 — THE acceptance scenario; pokriven integration testom — vidi Testing #14b)
- **And** postojeći pozivaoci `hero_overlay_card.html` koji NE prosleđuju `fallback_obj` (home `_home_hero.html`, listing, about, brand-specific hero partials) renderuju H1 TAČNO kao pre (`{{ title }}`) — **zero blast-radius / zero regresija** na deljeni partial
- **And** tag je dostupan svim šablonima (site-wide load); NE forsira se sveobuhvatna zamena svih `{{ obj.field }}` u v1 (description/perex/spec-ovi = inkrementalno, OQ-1)

**AC7 — Security: vrednost polja autoescaped (NEMA XSS); graceful na edge-case (SM-D1/D2)**

- **Given** `Product(name_sr="<script>alert(1)</script>", name_hu="")` na `/hu/`
- **When** tag renderuje marker
- **Then** sr tekst je HTML-escaped u izlazu (`&lt;script&gt;...` — kroz `format_html`); NE izvršava se, NE probija span
- **And** NIGDE se ne koristi `|safe` / `mark_safe` na sirovoj vrednosti polja (mark_safe sme SAMO na već-`format_html`-escaped sklopljenom HTML-u — mirror 6-1/6-3 SAFE pattern)
- **And** edge-case graceful (NE 500): `obj=None` → prazan/plain string; nepostojeće polje (`getattr` _UNSET) → plain ili prazan; ne-translated polje (nema `_<lang>` accessor) → plain `obj.field`; objekat bez `_<lang>` ali sa `field` (npr. plain mock) → plain `getattr(obj, field, "")`

## Tasks / Subtasks

> **Konvencija:** `[TEA-RED]` = Test Architect piše test PRE implementacije (mora FAIL). `[DEV-GREEN]` = Developer implementira da test prođe. **Dev NIKAD ne piše testove.** **NEMA migracije** (6.5 je 0-migration; tag SAMO čita postojeća `_sr/_hu/_en` polja; `makemigrations --check` mora ostati čist). **NEMA `uv add`** (`get_language`/`gettext`/`format_html`/`mark_safe`/`escape` su Django core; SVG je inline string).

- [x] **Task 1 — `apps/core/templatetags/i18n_fallback.py` skelet + registracija (AC1)** `[DEV-GREEN]`
  - [x] 1.1 Kreiraj `apps/core/templatetags/i18n_fallback.py`. Importi: `from django import template`, `from django.utils.translation import get_language, gettext`, `from django.utils.html import format_html`, `from django.utils.safestring import mark_safe`. `register = template.Library()`. Module docstring (srpski, dijakritike) objašnjava CRUX (per-locale accessor, NE `obj.field` — SM-D1).
  - [x] 1.2 `_UNSET = object()` sentinel (razlikuje „accessor ne postoji" od „accessor vraća None/prazno").
  - [x] 1.3 `_FALLBACK_TOOLTIP_TEXT` — NE modul-level konstanta sa `gettext` (to bi se evaluiralo na import u default locale). Umesto toga pozovi `gettext("Sadržaj na srpskom — još nije preveden")` UNUTAR tag funkcije (runtime, per-request locale; SM-D4). (Mark-for-translation: `makemessages` skenira `gettext(...)` poziv u .py.)
  - [x] 1.4 Inline SVG ⓘ kao modul-level konstanta `_INFO_ICON_SVG` — STVARNI Bootstrap Icons `info-circle` (MIT-licenciran; inline SVG, NE vendiranje font-a; `viewBox="0 0 16 16"`, TRI `<path>`-a: krug + tačka `i` + stub `i`). SM-D5. **`mark_safe` je OBAVEZAN** (statički markup, NE user input → bezbedno): bez njega `format_html`/`conditional_escape` escape-uje SVG u literal `&lt;svg&gt;` (vidljiv tekst umesto ikone). `conditional_escape` preskače SAMO `SafeString`, pa konstanta mora biti `mark_safe`-ovana pre nego što uđe u `format_html` placeholder (Task 3.2). **Tačan SVG (kopiraj doslovno, NE pogađaj `d=...`):**
    ```python
    _INFO_ICON_SVG = mark_safe(
        '<svg class="coric-fallback-marker__icon" xmlns="http://www.w3.org/2000/svg"'
        ' width="1em" height="1em" viewBox="0 0 16 16" fill="currentColor"'
        ' aria-hidden="true" focusable="false">'
        '<path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/>'
        '<path d="m8.93 6.588-2.29.287-.082.38.45.083c.294.07.352.176.288.469l-.738 3.468c-.194.897.105 1.319.808 1.319.545 0 1.178-.252 1.465-.598l.088-.416c-.2.176-.492.246-.686.246-.275 0-.375-.193-.304-.533L8.93 6.588zM9 4.5a1 1 0 1 1-2 0 1 1 0 0 1 2 0z"/>'
        '</svg>'
    )
    ```
    (Bootstrap Icons `info-circle.svg`, MIT — autoritativni path data; Dev kopira bez izmena. NB: ovo su DVA `<path>`-a u zvaničnom `info-circle` SVG-u — spoljni krug + glif `i` (tačka i stub spojeni u jedan `d`); ne dodaj treći prazan path.)

- [x] **Task 2 — Fallback-detekcija algoritam (AC1, CRUX, SM-D1)** `[DEV-GREEN]`
  - [x] 2.1 U `translated_field(context, obj, field)`:
    - `if obj is None: return ""` (graceful).
    - **`lang = (get_language() or "sr").split("-")[0]`** (BCP-47 normalizacija — `en-us`→`en`, `sr-latn`→`sr`; bez ovoga `name_en-us` accessor uvek promaši → marker se tiho nikad ne pojavi za en/region-locale; AC1).
    - **`if lang == "sr":`** → `return format_html("{}", str(getattr(obj, field, "") or ""))` (plain escaped; sr = izvor, NIKAD marker; normalizovan `lang` već pokriva `None`→`sr` i `sr-latn`→`sr`). (`format_html("{}", val)` autoescape-uje `val`; `str(...)` coercion konzistentno sa detekcijom — Item 2.)
    - `current = getattr(obj, f"{field}_{lang}", _UNSET)`.
    - **`if current is _UNSET:`** → accessor ne postoji (ne-translated polje / pogrešno ime) → `return format_html("{}", str(getattr(obj, field, "") or ""))` (graceful plain, NE 500).
    - **`if current and str(current).strip():`** → popunjeno za ovu locale → `return format_html("{}", str(current))` (NO fallback).
    - **else (prazno/blank current = FALLBACK):** `sr_val = getattr(obj, f"{field}_sr", None)`; **`if not (sr_val and str(sr_val).strip()):`** → ni sr nema vrednost → `return format_html("{}", str(getattr(obj, field, "") or ""))` (nema teksta za markirati). Inače → `return _render_marker(context, sr_val)` (Task 3).
  - [x] 2.1a **`str()` coercion konzistentnost (Item 2):** svaki plain-return put koristi `format_html("{}", str(... or ""))` — isti `str()` izraz koji detekcija već koristi (`str(current).strip()`), da ne-string vrednost polja ne iznenadi (`format_html` bi je svakako stringifikovao, ali eksplicitan `str()` je čitljiviji i konzistentan). **SCOPE NAPOMENA:** tag cilja TEKSTUALNA translated polja (CharField/TextField — `name`/`title`/`description`/`perex`/`body`). Na ne-tekstualna/ne-translated polja (brojevi/FK/`slug`) tag radi graceful (plain vrednost), ali NIJE namenjen za njih (SM-D1 edge-case; AC7).
  - [x] 2.2 **⚠️ NE koristiti `obj.field` (rešenu vrednost) za detekciju** — `MODELTRANSLATION_FALLBACK_LANGUAGES=("sr",)` čini da `obj.name` već vrati sr kad je `name_hu` prazan; poređenje `obj.name == obj.name_sr` bi bilo UVEK True na fallback-u ALI i kad je hu == sr slučajno → lažni marker. JEDINI pouzdan signal je „da li je `name_<lang>` kolona PRAZNA". (Dokumentuj ovo komentarom u kodu.)
  - [x] 2.3 `whitespace-only` se tretira kao prazno (`str(current).strip()` — admin može uneti samo space; to NIJE validan prevod → fallback).

- [x] **Task 3 — Marker render + per-request id counter + a11y atributi (AC2/AC3, SM-D2/D3)** `[DEV-GREEN]`
  - [x] 3.1 `_next_tooltip_id(context)` helper. Modul-level: `import itertools` + `_FALLBACK_ID_FALLBACK_COUNTER = itertools.count(1)`. Telo:
    - `request = context.get("request")`.
    - **Ako `request` postoji** (normalan HTTP render): `n = getattr(request, "_coric_fallback_counter", 0) + 1; setattr(request, "_coric_fallback_counter", n); return f"fallback-tooltip-{n}"`. (Per-request → resetuje se svaki request; AC3.)
    - **Ako `request` is None** (shell / management / izolovan test render bez HTTP konteksta): `return f"fallback-tooltip-{next(_FALLBACK_ID_FALLBACK_COUNTER)}"` — modul-level monotoni brojač čuva JEDINSTVENOST id-eva unutar render-a (cross-request ne-determinizam je prihvatljiv u ovoj degenerisanoj putanji).
    - **⚠️ ZABRANJENO:** statična string-konstanta tipa `return "fallback-tooltip-x"` — dala bi SVIM markerima ISTI id (slomljena `aria-describedby` uniqueness; AT vezuje sve markere za prvi tooltip). NE 500 ni u jednoj putanji.
  - [x] 3.2 `_render_marker(context, sr_text)`:
    - `tooltip_id = _next_tooltip_id(context)`.
    - `tooltip_text = gettext("Sadržaj na srpskom — još nije preveden")` (runtime; SM-D4).
    - **Tooltip span je DETE markera (UNUTAR `.coric-fallback-marker`, posle teksta+ikone) — NE adjacent sibling (CRITICAL; vidi AC2/AC5/Task 4):**
      `format_html('<span class="coric-fallback-marker" tabindex="0" aria-describedby="{}" lang="sr">{} {}<span class="coric-fallback-marker__tooltip" id="{}" role="tooltip">{}</span></span>', tooltip_id, sr_text, _INFO_ICON_SVG, tooltip_id, tooltip_text)`.
    - **⚠️ `sr_text` i `tooltip_text` su `{}` placeholder-i u `format_html` → AUTOESCAPED** (AC7). `_INFO_ICON_SVG` je pre-`mark_safe`-ovan statički markup → `format_html` ga propušta kao `SafeString` (`conditional_escape` preskače `SafeString`, pa SVG NE postaje literal `&lt;svg&gt;`). NIKAD ne sklapaj string ručno + `mark_safe` na celinu sa sirovim `sr_text`.
  - [x] 3.3 Verifikuj `aria-describedby` vrednost == tooltip `id` (isti `tooltip_id` u oba — AC3 par). `aria-describedby` radi BEZ obzira na to što je tooltip dete markera (id-referenca, ne DOM-pozicija).

- [x] **Task 4 — `static/css/components/i18n-fallback-marker.css` + main.css @import (AC5, SM-D6)** `[DEV-GREEN]`
  - [x] 4.1 Kreiraj `static/css/components/i18n-fallback-marker.css`. Header komentar (mirror postojećih komponenti). Pravila:
    - `.coric-fallback-marker` — `position: relative` (za tooltip pozicioniranje), `cursor: help`, boja ikone kroz `color: var(--color-semantic-text-muted)` (diskretno), `text-decoration` opciono dotted underline.
    - `.coric-fallback-marker__icon` — `width: 1em; height: 1em; vertical-align: baseline` (ili `-0.1em` fine-tune), `color` nasleđen (currentColor u SVG).
    - `.coric-fallback-marker__tooltip` (DETE markera; AC2 markup) — **DEFAULT = visually-hidden clip pattern** (mirror Bootstrap `.visually-hidden`): `position:absolute; width:1px; height:1px; clip-path:inset(50%); overflow:hidden; white-space:nowrap;` — **NE `display:none`, NE `visibility:hidden`, NE bare `opacity:0`** (display/visibility uklanjaju iz a11y stabla → lome `aria-describedby`; bare opacity = AT-tree dvosmislenost). Tooltip OSTAJE u a11y stablu (screen-reader ga čita preko `aria-describedby`).
    - **Reveal = DESCENDANT selektor `.coric-fallback-marker:hover .coric-fallback-marker__tooltip`, `.coric-fallback-marker:focus .coric-fallback-marker__tooltip`** (ili `:focus-within`) — prebacuje u vidljivo pozicionirano stanje: `position:absolute; width:auto; height:auto; clip-path:none; overflow:visible; white-space:normal;` + placement uz marker, `z-index` iznad sadržaja, `max-width` (token). **Descendant selektor radi SAMO jer je tooltip dete markera (NE adjacent sibling — sibling-combinator NE bi matchovao → tooltip nikad ne bi izašao iz clip-a).** Stil tooltip-a: **`background: var(--color-brand-green-800)` (PINNED — #25402f; NE „Dev bira green-800 ili black")** sa `color: var(--color-semantic-text-on-dark)` (#ffffff) → kontrast ~11.5:1 (≥4.5:1 ✓, verifikovano protiv tokens.css vrednosti), `padding: var(--spacing-scale-2) var(--spacing-scale-3)`, `border-radius: var(--rounded-sm)`, `box-shadow: var(--shadow-md)`, `font-size: var(--typography-scale-caption)`, `max-width` (token; vidi 4.2), `z-index` iznad sadržaja. Placement: ispod/iznad markera u praznom prostoru (WCAG 1.4.13 / G10 — NE preko susedne kritične UI).
    - `.coric-fallback-marker:focus-visible` — vidljiv outline `var(--color-semantic-focus-ring)` (keyboard fokus; AC5).
    - **kontrast ≥ 4.5:1** — tooltip text-on-dark na green-800/black pozadini (tokeni već prošli DESIGN.md kontrast; verifikuj).
    - `@media (prefers-reduced-motion: reduce)` — ukloni opacity/transform tranziciju (instant reveal; AC5).
  - [x] 4.2 **NIJEDNA magic vrednost** — sve boje/razmaci/radius/senka/font kroz `var(--...)` (project-context). Ako neki token fali (npr. tooltip max-width) → koristi postojeći spacing token, NE hardkoduj px.
  - [x] 4.3 `static/css/main.css`: dodaj `@import url('./components/i18n-fallback-marker.css');` (na kraj liste ili u logičnu sekciju; mirror postojeći @import).

- [x] **Task 5 — Adopcija u v1 šablone (AC6, SM-D7)** `[DEV-GREEN]`
  - [x] 5.1 `templates/blog/post_detail.html`: dodaj `{% load i18n_fallback %}` (vrh, uz postojeće load-ove); `:19` `<h1 id="blog-detail-title" class="coric-blog-detail__title">{{ post.title }}</h1>` → `... >{% translated_field post 'title' %}</h1>`. (post ima `title_sr/_hu/_en` iz 5-1.)
  - [x] 5.2 **Product/Brand hero — SM-D7 opcija A (USVOJENA — backward-compatible opt-in):**
    - **5.2a** `templates/partials/hero_overlay_card.html`: dodaj `{% load i18n_fallback %}` (vrh). Zameni `<h1 class="coric-hero-overlay-card__title">{{ title }}</h1>` sa:
      `<h1 class="coric-hero-overlay-card__title">{% if fallback_obj %}{% translated_field fallback_obj fallback_field %}{% else %}{{ title }}{% endif %}</h1>`.
      **`fallback_obj`/`fallback_field` su OPCIONI include param-i** — pozivaoci koji ih ne prosleđuju (home `_home_hero.html`, listing, about, brand-specific `_jeegee/_hzm/_tulip_hero.html`) padaju na `{{ title }}` → renderuju IDENTIČNO kao pre (zero blast-radius). NE menjaj nijedan postojeći `{% include %}` koji NE usvaja marker.
    - **5.2b** `templates/products/partials/_hero_section.html`: u postojeći include dodaj `fallback_obj=product fallback_field='name'` (uz postojeći `title=product.name ...`). `title=product.name` ostaje kao graceful fallback ako `fallback_obj` ikad bude prazan.
    - **5.2c** `templates/brands/partials/_hero_section.html`: u SVA ČETIRI `{% include "partials/hero_overlay_card.html" with title=brand.name ... %}` (blue/green × logo/no-logo grane) dodaj `fallback_obj=brand fallback_field='name'`.
    - **Zero-regresija guard:** `_home_hero.html`/`_about_hero.html`/listing/`_jeegee_hero.html`/`_hzm_hero.html`/`_tulip_hero.html` koji takođe include-uju `hero_overlay_card.html` sa string `title=` ostaju NETAKNUTI → `{% else %}{{ title }}{% endif %}` grana → identičan render (test #14c).
  - [x] 5.3 `uv run python manage.py check` exit 0; `uv run python manage.py makemigrations --check --dry-run` → „No changes detected" (0 model promene).

- [x] **Task 6 — i18n prevod tooltip-a (REQUIRED-for-done; AC4, SM-D4)** `[DEV-GREEN]` — **NE više opciono:** tooltip „Sadržaj na srpskom — još nije preveden" prikazan hu/en posetiocu koji NE čita srpski mora biti na NJEGOVOM jeziku (ironično bi bilo da i18n-fallback marker sam ima ne-prevedeni tooltip).
  - [x] 6.1 `uv run python manage.py makemessages -l hu -l en -l sr` (ili projektni makemessages flow) → tooltip msgid „Sadržaj na srpskom — još nije preveden" se pojavi u .po fajlovima.
  - [x] 6.2 **OBAVEZNO dodaj prevode (ne ostavljaj prazno):**
    - `locale/hu/LC_MESSAGES/django.po` → `msgstr "A tartalom szerb nyelven — még nincs lefordítva"`
    - `locale/en/LC_MESSAGES/django.po` → `msgstr "Content in Serbian — not yet translated"`
    - (sr je izvorni msgid — `locale/sr` msgstr prazan = msgid fallback, što je tačno na sr.) Ako je `#, fuzzy` flag dodat od `makemessages`, ukloni ga da prevod stupi na snagu.
  - [x] 6.3 `uv run python manage.py compilemessages` (regeneriše `.mo`; projekt commit-uje `.mo` — vidi prethodne i18n story-je za flow). Verifikuj da `/hu/` render prikaže hu tooltip, `/en/` en tooltip.

- [x] **Task 7 — Verifikacija (svi AC)** `[DEV-GREEN]`
  - [x] 7.1 `uv run python manage.py check` + `makemigrations --check` čisti.
  - [x] 7.2 Manual: render `/hu/blog/<slug>/` gde `title_hu` prazan → marker vidljiv, hover/focus → tooltip (hu prevod tooltip-a); `/sr/blog/<slug>/` → bez markera; `/hu/blog/<slug>/` gde `title_hu` popunjen → bez markera. **Takođe `/hu/proizvod/agri-tracking-tb804/` gde `name_hu` prazan → hero H1 marker (epics:976); `/en/...` → tooltip na engleskom.** Verifikuj da home/listing hero (bez `fallback_obj`) renderuje naslov BEZ markera (zero-regresija).
  - [x] 7.3 `ruff` clean; TEA test suite GREEN.

## Dev Notes

### CRUX — zašto per-locale accessor (SM-D1, NAJVAŽNIJE)

`MODELTRANSLATION_FALLBACK_LANGUAGES = ("sr",)` (verifikovano `config/settings/base.py:157`) konfiguriše modeltranslation da kad je `name_<aktivna_locale>` prazan, `obj.name` (deskriptor) **tiho vrati `name_sr`**. To je NAMERNO (Story 1.4/2.2 — sajt nikad ne pokazuje prazno polje). POSLEDICA za 6.5: `obj.name` NIKAD ne otkriva da je fallback nastupio — vraća već-rešenu vrednost. **Jedini pouzdan signal je čitanje SIROVE per-locale kolone** `getattr(obj, f"{field}_{get_language()}")` i provera da li je prazna. Ovo je cela poenta story-ja; pogrešno čitanje `obj.field` = tag NE RADI (marker se nikad / uvek pogrešno pojavljuje).

base.py:153-156 komentar EKSPLICITNO imenuje ovu story: *„NIJE FR-32 mapiranje — FR-32 je view-layer marker u Story 6.5"* — fallback chain je infra, 6.5 je vidljivi marker iznad njega.

### Referentni pattern — duck-typing (NE import modeltranslation interne)

`apps/seo/templatetags/seo_meta.py:_display_title` (6-1) je kanonski low-coupling pattern: `getattr(obj, "name", None) or getattr(obj, "title", None) or str(obj)`. 6.5 tag analogno duck-tipuje — NE import-uje `modeltranslation.utils` / NE `isinstance` / NE pristupa `_meta.fields`. `getattr(obj, f"{field}_{lang}", _UNSET)` radi na BILO kom objektu sa tom kolonom (Product/Post/Brand/Category/Tag — svi imaju `_sr/_hu/_en` iz svojih translation.py); graceful `_UNSET` na ostalima.

### Security (mirror 6-1/6-3 SAFE pattern)

`format_html("{}", value)` autoescape-uje `value` (XSS-safe). `mark_safe` SME samo na: (a) statički `_INFO_ICON_SVG` (nema user input), (b) već-`format_html`-sklopljen rezultat. NIKAD ručno `"<span>" + sr_text + "</span>"` + `mark_safe` (to bi propustilo XSS iz admin-unetog `name_sr`). Vidi 6-1 sprint-status: *„head injection ALL SAFE autoescaped, no |safe"*.

### A11y (WCAG 2.1 AA — project-context:731-739)

- `lang="sr"` na fallback tekstu = WCAG 3.1.2 Language of Parts (screen-reader prebacuje sr izgovor usred hu/en strane).
- `tabindex="0"` = keyboard fokus (tooltip dostupan bez miša; `:focus-within` reveal).
- `aria-describedby` ↔ `role="tooltip"` id par = SR najavljuje tooltip kao opis markera.
- ikona `aria-hidden="true"` + `focusable="false"` = dekorativna, ne duplira se SR-u.
- `prefers-reduced-motion` na tooltip reveal (project-context A11y #7).
- kontrast 4.5:1 (project-context A11y #5).

### Project Structure Notes

- NOVI tag je DRUGI u `apps/core/templatetags/` (uz `htmx_aria.py`); `__init__.py` već postoji (templatetags je package). NEMA `coric_format.py` — project-context referenca na `{% locale_date %}` ne odgovara stvarnom stanju (ne postoji); ne oslanjaj se na nju.
- CSS @import per-component pattern (main.css ima ~25 `@import url('./components/...')`); NOVI fajl prati `coric-` BEM + token disciplinu (verifikovano `static/css/tokens.css` :root 63 tokena).
- `hero_overlay_card.html` prima `title=` kao STRING (`{% include ... with title=product.name %}`) — ovo je KLJUČNA prepreka za product/brand hero adopciju; SM-D7 nudi opciju B (defer, post_detail-only v1) kao sigurnu default.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 6.5] — AC, markup `coric-fallback-marker`/tabindex/aria-describedby/lang="sr", tooltip tekst, `/hu/proizvod/...` scenario
- [Source: config/settings/base.py:153-158] — MODELTRANSLATION_FALLBACK_LANGUAGES=("sr",), LANGUAGES, FR-32/Story 6.5 view-layer marker komentar (CRUX)
- [Source: apps/seo/templatetags/seo_meta.py:86-125] — `_display_title`/`_og_type` duck-typing referentni pattern (low-coupling getattr chain)
- [Source: apps/core/templatetags/htmx_aria.py] — postojeći core tag pattern (register/simple_tag/mark_safe)
- [Source: static/css/tokens.css:82-180] — :root tokeni koje marker CSS konzumira
- [Source: static/css/main.css:5-59] — per-component @import pattern
- [Source: templates/blog/post_detail.html:19] — H1 adopcija target; [templates/partials/hero_overlay_card.html:3] — title= string param (SM-D7 prepreka)
- [Source: _bmad-output/project-context.md:18,500-515,731-739] — pune dijakritike/NIKAD šišana latinica; WCAG 2.1 AA must-haves; prefers-reduced-motion; vanilla JS/no jQuery/no build pipeline

## Decision Log (SM-Dx)

- **SM-D1 (CRUX) — Fallback se detektuje per-locale accessorom, NE `obj.field`.** `MODELTRANSLATION_FALLBACK_LANGUAGES=("sr",)` čini da `obj.field` već fallback-uje na sr → beskorisno za detekciju. Algoritam: `lang==sr`→nikad marker; čitaj `getattr(obj,f"{field}_{lang}",_UNSET)`; `_UNSET`/prazno-i-sr-prazno→plain; popunjeno→plain; prazno-a-sr-popunjeno→MARKER. whitespace-only=prazno. Sve graceful (obj=None/nepostojeće polje→no 500).
- **SM-D2 — `simple_tag(takes_context=True)`, autoescape, NIKAD `|safe` na obj content.** takes_context jer treba `get_language()` (runtime) + `request` za per-request id counter. `format_html("{}",val)` escape-uje vrednost; `mark_safe` samo na statičkom SVG / sklopljenom rezultatu. Vraća marker-span (fallback) ili plain escaped (no fallback).
- **SM-D3 — CSS-only tooltip (0 JS), per-request jedinstveni id, tooltip je DETE markera.** Tooltip `role="tooltip"` span je DETE `.coric-fallback-marker` (UNUTAR njega) → reveal je DESCENDANT selektor `.coric-fallback-marker:hover/:focus .coric-fallback-marker__tooltip` (NE adjacent sibling — sibling-combinator ne bi matchovao). Default = visually-hidden clip pattern (`position:absolute;width:1px;height:1px;clip-path:inset(50%);overflow:hidden;white-space:nowrap;`) — ostaje u a11y stablu za `aria-describedby`; NE `display:none`/`visibility:hidden`/bare-`opacity:0`. `tabindex="0"` keyboard fokus; `prefers-reduced-motion`. NE Bootstrap JS tooltip (no-build-pipeline, no jQuery, a11y `:focus` dovoljan). id kroz per-request counter (`request._coric_fallback_counter`) → `fallback-tooltip-N`, resetuje se po request-u; request=None → modul-level `itertools.count(1)` (jedinstven id, NE statična string-konstanta). HTMX swap re-render counter-a od 1 = known constraint (G5b) → v1 non-HTMX adopcija.
- **SM-D4 — Tooltip tekst runtime `gettext` (NE lazy).** `gettext("Sadržaj na srpskom — još nije preveden")` UNUTAR tag funkcije → po-request locale (hu/en/sr); pune dijakritike. Mark-for-translation; hu/en .po prevodi opciono (OQ-2) — bez njih sr msgid fallback (graceful).
- **SM-D5 — Inline SVG ⓘ (NE Bootstrap Icons font).** `bi-info-circle` (epics:975) NIJE dostupna — `static/vendor/` nema bootstrap-icons (samo bootstrap-5.3.3/glightbox/htmx/nouislider). Vendiranje celog font-a za 1 ikonu = anti-perf. Inline SVG path (`currentColor`, `aria-hidden`, `em`-skaliran) = 0 asseta, 0 dep. epics:975 markup je ilustrativan; AC2 dokumentuje SVG realnost.
- **SM-D6 — NOVI per-component CSS, SAMO var(--...) tokeni.** `static/css/components/i18n-fallback-marker.css` @import u main.css; `.coric-fallback-marker`/`__icon`/`__tooltip` BEM; tokeni za boju/razmak/radius/senku/font; focus-visible; kontrast 4.5:1; prefers-reduced-motion. 0 magic vrednosti.
- **SM-D7 (REVIDIRANO) — v1 adopcija: post_detail H1 + product/brand hero kroz BACKWARD-COMPATIBLE opt-in.** Tag site-wide dostupan. v1 usvaja: (1) post_detail H1 (direktan `post` obj); (2) **product I brand hero naslov** kroz `hero_overlay_card.html` koji prima `title=` STRING (deljen sa home/listing). **Reconciliacija = opcija A (USVOJENA, NE više „Dev bira"):** dodaj OPCIONE include param-e `fallback_obj` + `fallback_field` u `hero_overlay_card.html`; H1 render postaje `{% if fallback_obj %}{% translated_field fallback_obj fallback_field %}{% else %}{{ title }}{% endif %}`. Postojeći pozivaoci (home/listing) koji NE prosleđuju `fallback_obj` → padaju na `{{ title }}` — renderuju TAČNO kao pre (zero blast-radius). Product `_hero_section.html` i brand `_hero_section.html` proslede `fallback_obj=product fallback_field='name'` / `fallback_obj=brand fallback_field='name'`. Razlog za usvajanje (NE defer): epics:976 imenuje `/hu/proizvod/agri-tracking-tb804/` kao THE acceptance scenario — defer bi ga ostavio samo unit-test-pokrivenim; opt-in je one-sprint-sized i bez blast-radius-a na deljeni partial. NE forsiraj site-wide zamenu svih `{{obj.field}}` u v1 (description/perex/spec-ovi = inkrementalno, OQ-1).

## Gotchas

- **G1 (CRUX) — `obj.name == obj.name_sr` je LAŽNI test.** Zbog fallback chain-a `obj.name` već vraća sr kad je hu prazan, pa bi to poređenje bilo True na fallback-u; ALI bilo bi True i kad je `name_hu` slučajno identičan `name_sr` (validan prevod koji je isti kao sr) → lažni marker. JEDINI ispravan signal: `name_<lang>` kolona PRAZNA. (SM-D1/Task 2.2)
- **G2 — `gettext` NE na modul-level.** `_TEXT = gettext("...")` na vrhu fajla evaluira se na import-u u tada-aktivnoj (default/sr) locale i keširan zauvek → tooltip uvek sr. MORA biti `gettext(...)` poziv UNUTAR funkcije (runtime) ILI `gettext_lazy` koji se reši pri render-u. Preferiraj runtime `gettext` u funkciji (SM-D4/Task 1.3).
- **G3 — `bi-info-circle` bez Bootstrap Icons = nevidljiv prazan `<i>`.** Ako Dev kopira epics:975 markup doslovno, `<i class="bi-info-circle">` ne renderuje ništa (font nije učitan) → marker bez ikone. Inline SVG (SM-D5).
- **G3b — SVG konstanta MORA biti `mark_safe`-ovana pre `format_html`.** `_INFO_ICON_SVG` ulazi u `format_html` kao `{}` placeholder; `format_html` poziva `conditional_escape` na svaki argument, a `conditional_escape` escape-uje sve OSIM `SafeString`. Ako `_INFO_ICON_SVG` nije `mark_safe`-ovan → SVG markup postaje literal `&lt;svg&gt;...` (vidljiv tekst, NE ikona). Rešenje: `_INFO_ICON_SVG = mark_safe("<svg…>")` (statički markup, NE user input → bezbedno). NB: ovo se NE kosi sa XSS pravilom — `mark_safe` je dozvoljen na statičkoj ikoni, NIKAD na `sr_text`/`tooltip_text` (oni ostaju autoescaped `{}` placeholder-i). (Task 1.4/Task 3.2/AC2/AC7)
- **G4 (CRITICAL) — tooltip MORA biti DETE markera + clip-hidden, inače se NIKAD ne otkriva i/ili lomi SR.** (a) **Struktura:** tooltip `<span>` je DETE `.coric-fallback-marker` (UNUTAR njega, posle teksta+ikone), NE adjacent sibling. Reveal je DESCENDANT selektor `.coric-fallback-marker:hover .coric-fallback-marker__tooltip` / `:focus .coric-fallback-marker__tooltip`; descendant selektor NE matchuje sibling → da je tooltip sibling, ostao bi TRAJNO skriven na hover/focus (samo SR `aria-describedby` bi radio). (b) **Hidden state:** visually-hidden tooltip MORA ostati u a11y stablu (`aria-describedby` ga referencira). NE `display:none`/`visibility:hidden` (uklanja iz SR), NE bare `opacity:0` (AT-tree dvosmislenost). Koristi clip pattern `position:absolute; width:1px; height:1px; clip-path:inset(50%); overflow:hidden; white-space:nowrap;` (mirror Bootstrap `.visually-hidden` koji projekt već koristi — `templates/blog/post_detail.html:23`). (SM-D3/AC2/AC5/Task 3.2/Task 4.1)
- **G5 — id scheme: per-request counter primarno; modul-level monotoni counter SAMO kao fallback kad request=None; NIKAD statična string-konstanta.** Primarna putanja je per-request `request._coric_fallback_counter` (resetuje se svaki request → deterministički `-1/-2/...`; AC3). Kad `request` nije u context-u (shell/management/izolovan test render) fallback je modul-level `itertools.count(1)` → JEDINSTVENI ali ne-deterministički id-evi (rastu kroz proces). **NIKAD statična `"fallback-tooltip-x"`** — to bi dalo svim markerima isti id i slomilo `aria-describedby` uniqueness. Testovi zato asertuju JEDINSTVENOST + PATTERN `fallback-tooltip-…` + `aria-describedby`↔`id` match, NE tačnu vrednost (modul-level putanja čini tačnu vrednost brittle).
- **G5b (KNOWN CONSTRAINT) — HTMX partial swap re-renderuje counter od 1 → moguća kolizija sa već-prisutnim DOM markerima.** HTMX swap je ZASEBAN request → `request._coric_fallback_counter` kreće od 1, pa swap-ovani fragment može generisati `fallback-tooltip-1` koji se već nalazi u živom DOM-u (iz inicijalnog full-page render-a) → duplikat id. Zbog toga je v1 adopcija targetovana na NON-HTMX full-page render-e (post_detail H1; product/brand hero ako se usvoji). HTMX-context adopcija traži swap-safe id strategiju (npr. prefiks iz `HX-Target`/timestamp/uuid segment) — DEFERRED (van scope-a v1; vidi i OQ-4 inkrementalna adopcija).
- **G6 — `{% include with title=... %}` prosleđuje STRING, ne obj → REŠENO opcijom A.** hero_overlay_card ne može da pozove `translated_field` na `title` (već je `product.name` string sa fallback-om rešenim). Rešenje (SM-D7 opcija A, USVOJENO): proslediti OPCIONI `fallback_obj`+`fallback_field` u include i renderovati `{% if fallback_obj %}{% translated_field fallback_obj fallback_field %}{% else %}{{ title }}{% endif %}`. Pozivaoci bez `fallback_obj` → `{{ title }}` (zero blast-radius). **NE smeš ostaviti i `title=` i `fallback_obj` da oba renderuju — `{% if/else %}` bira tačno jedan** (kad je `fallback_obj` prisutan, `title` se ignoriše).
- **G7 — whitespace-only prevod = prazno.** Admin može uneti `name_hu="   "` (slučajno) → `str(current).strip()` ga tretira kao prazno → fallback (ispravno; „   " nije validan prevod).
- **G8 — modeltranslation `getattr(obj, "name_hu")` je virtuelno polje.** Postoji kao DB kolona (iz makemigrations 2.2/5.1); `getattr` radi normalno. Za objekat učitan sa `.only()` bez te kolone → deferred load (extra query) ili `_UNSET` ako polje nije u modelu — graceful pokriva oba.
- **G9 — `get_language()` može vratiti region/script subtag (BCP-47) → silent miss bez normalizacije.** `get_language()` ume vratiti `"en-us"`/`"sr-latn"` (ne samo `"en"`/`"sr"`), a modeltranslation kolone su `name_en`/`name_sr` (BEZ subtag-a). `getattr(obj, "name_en-us", _UNSET)` → `_UNSET` → tag tretira kao „popunjeno" → **marker se TIHO nikad ne pojavi za engleski** (najgora vrsta bug-a: izgleda kao da radi, ali AC ne ispunjava). FIX: `lang = (get_language() or "sr").split("-")[0]` PRE svake upotrebe (accessor + `lang=="sr"` provera). Test #4b pokriva `en-us`→`en`. (AC1/Task 2.1)
- **G10 — WCAG 1.4.13 tooltip ne sme da zaklanja esencijalni sadržaj (Dismissable izuzetak).** Pure-CSS tooltip nema Esc-to-dismiss (nema JS). To je dozvoljeno po 1.4.13 SAMO ako tooltip NE prekriva drugu kritičnu UI. Placement (Task 4.1) mora birati prazan prostor (ispod/iznad naslova), `z-index` iznad sadržaja ali `max-width` (token) da ne pokrije ceo viewport; near-edge clipping je prihvatljivo v1 (bez JS reposition-a). Hoverable/Persistent je zadovoljeno jer je tooltip DETE markera (hover ostaje aktivan). (AC5)

## Open Questions

- **OQ-1 (RAZREŠENO za hero; otvoreno za ostala polja) — Adopcija na ne-naslov polja?** Product/Brand hero naslov JE u v1 (SM-D7 opcija A — backward-compatible opt-in, epics:976 zahtevani scenario). Ostaje otvoreno samo: inkrementalna adopcija na `description`/`perex`/`key_features`/spec-ove (multi-line/rich polja — UX placement markera nejasan, vidi OQ-4) = buduća polish story, NE v1.
- **OQ-2 (RAZREŠENO) — hu/en tooltip prevodi su IN SCOPE.** Odlučeno: hu „A tartalom szerb nyelven — még nincs lefordítva" + en „Content in Serbian — not yet translated" se dodaju u Task 6.2 (required-for-done) + `compilemessages`. Biznis sme finalizovati TAČNU formulaciju, ali prevod NE sme ostati prazan u ovoj story (i18n marker bez prevedenog tooltip-a = ironija).
- **OQ-3 — Bootstrap Icons vendiranje za buduće ikone?** 6.5 koristi inline SVG (1 ikona). Ako Epic 7/8 uvede 10+ bi-ikona (admin dashboard?), vendiranje icon font-a/subset-a je tada opravdano. Za sada NE (YAGNI/perf). Re-evaluirati u Epic 8.
- **OQ-4 — Marker na multi-line/rich polja (perex/body/description)?** v1 cilja kratke inline naslove (name/title). Za `body` (rich text, |linebreaks) marker uz ceo blok teksta je UX upitno (gde staviti ⓘ?). Verovatno marker na nivou sekcije/heading-a, ne inline u telu. Defer dok se ne zatraži (OQ-1 inkrementalna adopcija).

## Testing

> **TEA piše RED-phase testove PRE implementacije** (`apps/core/tests/test_i18n_fallback.py`). Dev NE piše testove. Fokus na tag-render unit + fallback-detekciju + XSS + a11y atribute.
>
> **LOKACIJA testova:** core unit/render testovi (tag pozvan direktno sa Product/Post/Brand objektom + `activate(locale)`) idu u `apps/core/tests/test_i18n_fallback.py`. **Cross-app integration testovi (#14/#14b/#14c)** koji renderuju cele strane preko i18n URL routing-a (npr. `/hu/proizvod/...` zahteva Product fixture + `LocaleMiddleware` + URL reverse) MOGU živeti u `apps/products/tests/`/`apps/blog/tests/` ili zasebnom integration suite-u — NE moraju u core unit fajlu (cross-app coupling: Product/Post fixture + i18n routing). TEA bira raspodelu.

**Test surface (enumeracija — TEA finalizuje):**

1. **`test_no_marker_on_sr_locale`** — `activate("sr")`, objekat sa praznim `name_hu` → tag vraća plain `name_sr`, NEMA `coric-fallback-marker` (sr je izvor; AC1).
2. **`test_marker_when_locale_field_empty`** — `activate("hu")`, `Product(name_sr="Agri-Tracking TB804", name_hu="")` → izlaz sadrži `class="coric-fallback-marker"` + sr tekst + `lang="sr"` + inline `<svg` (AC1/AC2).
3. **`test_no_marker_when_locale_field_populated`** — `activate("hu")`, `name_hu="Traktor"` → plain „Traktor", NEMA markera (AC1).
4. **`test_detection_uses_per_locale_accessor_not_resolved`** — KONKLUZIVAN dokaz da algoritam čita `name_<lang>` accessor, NE `obj.name==name_sr`. Tri komplementarna slučaja u istom testu (ili parametrizovano) na `/hu/`:
   - (a) `name_sr="X", name_hu="X"` (oba popunjena, slučajno identična) → **NEMA markera** (`name_hu` popunjen iako == sr; da test poredi `obj.name==name_sr` LAŽNO bi markirao).
   - (b) `name_sr="X", name_hu=""` (sr popunjen, hu prazan) → **MARKER** (per-locale kolona prazna = fallback).
   - Par (a)+(b) zajedno dokazuje da je signal „je li `name_hu` PRAZNA", NE „je li `obj.name == name_sr`" (jer u (a) `obj.name`==`name_sr`==`name_hu`, a markera NEMA). (AC1/G1)
4b. **`test_bcp47_region_locale_resolves_to_base`** — `activate("en-us")` (ili monkeypatch `get_language` da vrati `"en-us"`), `Product(name_sr="X", name_en="")` → tag normalizuje `en-us`→`en`, čita `name_en` (prazan) → **MARKER** (bez normalizacije `name_en-us` accessor bi promašio → marker se TIHO ne bi pojavio za engleski; AC1/G9).
5. **`test_whitespace_only_treated_as_empty`** — `name_hu="   "` na `/hu/` → marker (whitespace nije validan prevod; G7).
6. **`test_xss_field_value_escaped`** — `name_sr="<script>alert(1)</script>"`, `name_hu=""` na `/hu/` → izlaz sadrži `&lt;script&gt;`, NE izvršni `<script>` (AC7).
7. **`test_aria_describedby_matches_tooltip_id`** — marker render → `aria-describedby` vrednost == tooltip `id` (isti string; asertuj PARNOST + `fallback-tooltip-…` PATTERN, NE hardkodiranu vrednost — AC3).
8. **`test_unique_ids_for_multiple_markers`** — dva fallback render-a u istom request-u → RAZLIČITI id-evi (asertuj jedinstvenost + `fallback-tooltip-\d+` pattern, NE tačne `-1`/`-2` vrednosti — modul-level fallback putanja čini tačnu vrednost brittle); counter per-request reset (AC3).
9. **`test_tooltip_text_localized`** — `activate("hu")` (sa hu .po prevodom ako postoji) → tooltip tekst je hu prevod; bez prevoda → sr msgid „Sadržaj na srpskom — još nije preveden" (AC4). Verifikuj pune dijakritike u sr msgid.
10. **`test_graceful_obj_none`** — `translated_field(ctx, None, "name")` → prazan/plain string, NE 500 (AC7).
11. **`test_graceful_nonexistent_field`** — objekat bez `slug_hu` accessora (ne-translated polje) → plain `obj.slug` ili prazno, NE 500 (AC1/AC7).
12. **`test_graceful_no_sr_value`** — `name_sr=""` i `name_hu=""` na `/hu/` → plain (nema teksta za markirati), NEMA markera (AC1).
13. **`test_icon_is_inline_svg_not_bootstrap_class`** — izlaz sadrži `<svg` sa `aria-hidden="true"` + `focusable="false"`, NE `class="bi-info-circle"` (SM-D5).
14. **`test_post_detail_h1_adoption`** — render `/hu/blog/<slug>/` sa praznim `title_hu` → H1 sadrži marker; sa popunjenim `title_hu` → bez markera (AC6, integration).
14b. **`test_product_hero_h1_fallback_marker`** — render `/hu/proizvod/agri-tracking-tb804/` (epics:976 THE acceptance scenario) sa `Product(name_sr="Agri-Tracking TB804", name_hu="")` → hero H1 (`coric-hero-overlay-card__title`) sadrži `class="coric-fallback-marker"` + sr naziv + `lang="sr"` + `<svg`; sa popunjenim `name_hu` → bez markera. (AC6, integration; potvrđuje SM-D7 opciju A wiring — `fallback_obj=product fallback_field='name'`.)
14c. **`test_hero_card_zero_regression_no_fallback_obj`** — render šablona koji include-uje `hero_overlay_card.html` BEZ `fallback_obj` (npr. home `_home_hero.html` ili direktan include sa samo `title="Tekst"`) → H1 sadrži plain `Tekst`, NEMA `coric-fallback-marker` (dokaz da opt-in NE menja postojeće pozivaoce; AC6 zero-blast-radius).
15. **`test_makemigrations_clean`** — `makemigrations --check --dry-run` → „No changes detected" (0 model promene; regression guard).
16. **(opciono) `test_marker_tooltip_has_role`** — tooltip span ima `role="tooltip"` (AC2/a11y).

**Regression guards:** postojeći core/products/blog testovi GREEN (tag je NOVI fajl + aditivna adopcija u post_detail H1 — NE menja postojeću logiku); `htmx_aria` testovi netaknuti; `seo_meta` testovi netaknuti.

## Dev Agent Record

### Agent Model Used

Opus 4.8 (1M context) — senior Django Dev (GREEN phase).

### Debug Log References

- `docker compose -f compose/local.yml run --rm django uv run pytest apps/core/tests/test_i18n_fallback.py apps/products/tests/test_hero_fallback_marker.py apps/blog/tests/test_post_detail_fallback_marker.py -v` → 24 passed.
- Broader suite `apps/core/tests apps/products/tests apps/blog/tests` → 529 passed, 1 skipped, 3 xfailed, **3 failed** (pre-existing query-budget tests, NOT 6.5 regressions — verified by stashing 6.5 template edits and re-running: identical failures at baseline). Failing: `test_used_machinery_view::test_ac1_assertNumQueries_initial_render_under_budget`, `test_views_product_detail::test_assert_num_queries_exactly_7`, `test_views_tractor_list::test_tractor_list_query_budget` (extra queries from Story 6.4 RedirectMiddleware + footer latest-posts context processor; product/brand objects load full `_sr/_hu/_en` columns so the new tag adds 0 queries).
- `ruff check apps/core/` clean; `manage.py check` 0 issues; `makemigrations --check --dry-run` → No changes detected; `djade --check` → 4 files already formatted.

### Completion Notes List

- NEW `apps/core/templatetags/i18n_fallback.py` — `{% translated_field obj field %}` `simple_tag(takes_context=True)`; per-locale-accessor detection (CRUX), BCP-47 normalize, `_UNSET` sentinel, runtime `gettext`, `format_html` autoescape, `mark_safe`'d inline info-circle SVG, per-request `_coric_fallback_counter` id scheme + module-level `itertools.count` fallback.
- NEW `static/css/components/i18n-fallback-marker.css` (BEM, var(--...) tokens, clip-hidden tooltip + descendant reveal, focus-visible, prefers-reduced-motion); `@import` added to `main.css`.
- Adopted in `blog/post_detail.html` H1, `partials/hero_overlay_card.html` (opt-in `fallback_obj`/`fallback_field`), `products/partials/_hero_section.html` + `brands/partials/_hero_section.html` (×4).
- i18n: tooltip msgid registered via makemessages; hu + en msgstr added; compilemessages run (.mo regenerated).

### File List

**Created:** `apps/core/templatetags/i18n_fallback.py`, `static/css/components/i18n-fallback-marker.css`
**Modified:** `static/css/main.css`, `templates/blog/post_detail.html`, `templates/partials/hero_overlay_card.html`, `templates/products/partials/_hero_section.html`, `templates/brands/partials/_hero_section.html`, `locale/hu/LC_MESSAGES/django.po`(+.mo), `locale/en/LC_MESSAGES/django.po`(+.mo), `locale/sr/LC_MESSAGES/django.po`(+.mo), `_bmad-output/implementation-artifacts/sprint-status.yaml`
