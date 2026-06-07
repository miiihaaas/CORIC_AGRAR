---
story_id: "7.5"
story-key: 7-5-sanitized-rich-text-pravne-strane-nh3
title: Sanitized Rich-Text za Pravne Strane (nh3)
status: review
epic: 7
epic_num: 7
epic_title: GDPR & Privacy
module: core (+ gdpr template-render-swap + pages template-render-swap)
created: 2026-06-07
last_modified: 2026-06-07
complexity: M
author: Mihas (SM autonomous; PETA Epic 7 story — REOTVARA epik (7-1..7-4 done, ali RISK-1 ostaje OTVOREN). NIJE u epics.md — novodefinisana da reši open RISK-1 iz 7-1/7-4. ODLUKA Mihas = Opcija B: prebaci render `body` na PRAVNIM stranama sa plain `{{ body|linebreaks }}` (auto-escape SVEG HTML-a → admin ne može uneti tabelu kolačića / naslove / liste / linkove ka GA4/Meta procesorima) na SANITIZOVAN rich HTML preko `nh3` (moderni Rust sanitizer; NE bleach koji je EOL). WYSIWYG editor (8.7) ostaje kasnija UX nicety; ova story isporučuje security-critical sanitizaciju SADA. NOVI dep `nh3` (uv add nh3). NOVI apps/core/sanitize.py:sanitize_legal_html(raw)→nh3.clean EKSPLICITNA ALLOWLIST (p/br/h2/h3/h4/ul/ol/li/a/strong/em/b/i + table/thead/tbody/tr/th/td; a→href/title/rel/target; th/td→colspan/rowspan; STRIP script/style/on*/javascript:/data:; link_rel="noopener noreferrer"; safe scheme allowlist http/https/mailto) + apps/core/templatetags/legal_html.py:{{ body|legal_html }} (sanitizuje NA RENDER-u + mark_safe SAMO posle sanitizacije — render-time je PRIMARNA XSS granica, NIKAD ne veruj stored). SWAP 2 template-a: templates/gdpr/cookie_policy.html + templates/pages/page-detail.html |linebreaks→|legal_html. body ostaje TextField (sad HTML). 0 schema migracija (body ostaje TextField); seed-ovi 0002/0004 ostaju kakvi jesu (plain text prolazi kroz sanitizer NEPROMENJEN — escape-uje se kao tekst). RECONCILIATION 5 postojećih testova (gdpr/test_xss.py 2× + pages/test_7_4_static_pages.py test_script_in_body_escaped/test_template_body_never_safe/test_body_rendered_through_linebreaks): oni tvrde `&lt;script&gt;` PRISUTAN (escape) i `page.body|linebreaks` u templatu — sa nh3 `<script>` se STRIPUJE (NE escape-uje) i template koristi |legal_html → ti testovi MORAJU se preformulisati na „sanitizovan/stripovan, NE escape-ovan" BEZ slabljenja XSS garancije (`<script>alert` i dalje ODSUTAN; nova garancija JAČA). RISK TIER HIGH — NOVI dep + XSS-critical sanitizacija pipeline + menja render 2 VEĆ-DONE modela. CSP-forward: nh3 stripuje inline on* handlere → komponuje se sa Epic 9 CSP. NEMA WYSIWYG (8.7). NEMA model/schema promene.)
depends_on:
  - 7-1-cookiepolicy-model-admin                            # gdpr.CookiePolicy.body render granica koju MENJAMO (SM-D3 |linebreaks→|legal_html); templates/gdpr/cookie_policy.html; gdpr/test_xss.py reconciliacija
  - 7-4-politika-kolacica-politika-privatnosti-staticke-strane  # pages.Page.body render granica koju MENJAMO (SM-D4 |linebreaks→|legal_html); templates/pages/page-detail.html; pages/test_7_4_static_pages.py reconciliacija; RISK-1 nasleđen
  - 1-1-project-bootstrap-sa-uv-i-django                     # uv add nh3 (dependency discipline — pyproject.toml [project].dependencies; project-context.md:56)
  - 2-1-brand-series-category-subcategory-modeli             # apps.core REUSE lokacija (sanitize.py + templatetags/ pored postojećih utils.py/i18n_fallback.py/htmx_aria.py)
---

# Story 7.5: Sanitized Rich-Text za Pravne Strane (nh3)

Status: review

## Opis

As a **admin (sadržaj pravnih dokumenata)**,

I want **da u `body` polje politike kolačića (`gdpr.CookiePolicy`) i statičkih pravnih strana (`pages.Page`, npr. politika privatnosti) unesem STRUKTURISAN sadržaj — tabelu kolačića (naziv/svrha/provajder/trajanje), naslove, liste i linkove ka GA4/Meta procesorima — koji se renderuje kao BEZBEDAN HTML (sanitizovan kroz allowlist), a ne kao escape-ovan tekst**,

so that **pravne strane mogu da prikažu sadržaj koji prava politika zahteva (tabela + linkovi + struktura) BEZ otvaranja XSS rupe, i bez čekanja punog WYSIWYG editora (8.7)**.

Ovo je **PETA Epic 7 story** i ona **REOTVARA Epic 7** (7-1..7-4 su `done`, ali otvoren **RISK-1** — „plain-text body možda legalno nedovoljan; treba tabela kolačića/linkovi ka GA4/FB procesorima; Mihas legal sign-off PRE go-live") — Mihas je odlučio **Opciju B**: prebaci render pravnih `body` polja na **sanitizovan rich HTML kroz `nh3`**, kao zasebnu story-ju PRE go-live. Ova story je **security-critical** — uvodi NOVI dep i menja render granicu na DVA već-done modela.

### ⚠️ KONTEKST — zašto ova story postoji (RISK-1)

Stories **7-1** (`gdpr.CookiePolicy`) i **7-4** (`pages.Page`) renderuju `body` kroz `{{ body|linebreaks }}` što **auto-escape-uje SAV HTML** (XSS-safe, ali admin NE MOŽE da unese strukturisan pravni sadržaj — tabelu, naslove, liste, linkove). RISK-1 je logovan kao „Mihas legal sign-off PRE go-live". Mihas je odlučio: **Opcija B** — sanitizovan rich HTML kroz `nh3` (moderni Rust sanitizer; **NE bleach** koji je EOL/unmaintained). WYSIWYG editor (8.7) ostaje kasnija UX nicety; **ova story isporučuje security-kritičnu sanitizaciju SADA** (admin za sada kuca HTML ručno / lepi iz pripremljenog snippet-a; editor dolazi u 8.7).

> **⚠️ RISK-1 SCOPE (KRITIČNO — 7.5 UNBLOCK-uje, NE CLOSE-uje):** Story 7.5 rešava **MEHANIZAM** (rich sanitizovan render — admin SADA MOŽE da unese tabelu kolačića / linkove / strukturu bezbedno), ali **NE i SADRŽAJ**. RISK-1 OSTAJE OTVOREN posle 7.5: pravi pravni tekst (tabela kolačića, linkovi ka procesorima, prava subjekta podataka, DPO, retencija) i dalje mora da **autorizuje biznis** i da ga **Mihas sign-off-uje PRE go-live**; seed-ovi ostaju Lorem **PLACEHOLDER**. **7.5 UNBLOCK-uje RISK-1 (mehanizam spreman), ali ga NE ZATVARA (sadržaj + legal sign-off su odvojeni, naknadni korak).**

### IN SCOPE (šta ova story isporučuje)

1. **NOVI dep `nh3`** (SM-D1) — `uv add nh3` → uđe u `pyproject.toml` `[project].dependencies`. Verifikovano: `nh3` NIJE prisutan (deps imaju django-* + pillow/psycopg/sorl/whitenoise/python-magic; nema sanitizera). `bleach` se NE koristi (EOL).
2. **NOVI `apps/core/sanitize.py:sanitize_legal_html(raw: str) -> str`** (SM-D2) — jedan deljen helper koji zove `nh3.clean(...)` sa **EKSPLICITNOM ALLOWLIST-om** prikladnom za pravne dokumente:
   - **tags:** `p, br, h2, h3, h4, ul, ol, li, a, strong, em, b, i, table, thead, tbody, tr, th, td`
   - **attributes:** `a → {href, title, rel, target}`; `th → {colspan, rowspan}`; `td → {colspan, rowspan}`
   - **url_schemes:** `{http, https, mailto}` (STRIP `javascript:`, `data:`)
   - **link_rel:** `"noopener noreferrer"` (nh3 forsira `rel` na sve `<a>` → tabnabbing/leak zaštita; `target="_blank"` postaje bezbedan)
   - STRIP sve ostalo: `script, style, on*` handleri, nedozvoljeni tagovi/atributi/scheme.
   - `None`/non-str ulaz → vrati `""` (graceful; helper se zove iz filtera i potencijalno save()).
   - **Forward-reuse (SM-D2):** isti helper će kasnije koristiti **8.7 blog WYSIWYG** (blog `Post.body`); zato je u `apps/core` (deljiv), NE u `apps/gdpr`/`apps/pages`. Ova story ga primenjuje SAMO na pravne strane (gdpr+pages), NE na blog (5-3 ostaje `|linebreaks` do 8.7).
3. **NOVI `apps/core/templatetags/legal_html.py:{{ body|legal_html }}`** (SM-D3) — template filter koji **sanitizuje NA RENDER-u** (`sanitize_legal_html(value)`) i vraća `mark_safe(...)` SAMO POSLE sanitizacije. **Render-time sanitizacija je PRIMARNA XSS granica** (sigurnije od oslanjanja samo na save-time — nikad ne veruj stored vrednosti; admin-kompromis ili direktan DB upis ne sme proći). `@register.filter(name="legal_html")`. `None`/prazno → `""`.
4. **SWAP render boundary na DVA pravna template-a** (SM-D4):
   - `templates/gdpr/cookie_policy.html`: `{{ policy.body|linebreaks }}` → `{{ policy.body|legal_html }}` (+ `{% load legal_html %}`).
   - `templates/pages/page-detail.html`: `{{ page.body|linebreaks }}` → `{{ page.body|legal_html }}` (+ `{% load legal_html %}`).
   - `body` ostaje `TextField` (sad sadrži HTML). Komentar iznad render-linije ažuriran (više nije „NIKAD |safe" plain-text presedan — sad je „sanitizovan kroz nh3 allowlist, mark_safe SAMO posle sanitizacije").
   - **⚠️ BLAST-RADIUS (SM-D4):** `templates/pages/page-detail.html` je GENERIČKI `Page` template (Page NIJE singleton — 7-4 napomena). Swap render-a utiče na SVE buduće `Page` redove (Epic 8.8 „O nama"/„Servis"/itd.), NE samo na politiku privatnosti. Posledica: 8.8 Page sadržaj MORA koristiti HTML markup (eksplicitne `<p>`/`<ul>`/`<table>`), a G-3 (plain `\n` više NE→`<br>`) važi za SVAKI Page renderovan kroz ovaj template. Ovo je PRIHVATLJIVO (pravne/CMS strane koriste strukturisan HTML) ali se EKSPLICITNO navodi, ne skriva.
5. **OPCIONO defense-in-depth — sanitize-on-save (SM-D5; PREPORUKA: NE u v1):** render filter MORA da sanitizuje **bez obzira** (primarna granica). Sanitizacija u `model.clean()`/`save()` (da stored podatak bude čist) je OPCIONA. **SM odluka: NE u v1** — sanitize-on-save bi uneo skriveno mutiranje admin unosa (admin kuca `<table>`, save tiho prepravi → konfuzija), i nije neophodno jer je render-time granica autoritativna. (Ako QA/Security panel insistira, može se dodati kao odvojen IMPROVEMENT — ali render filter ostaje merodavan.)
6. **0 SCHEMA migracija** (SM-D6) — `body` ostaje `TextField`; nema model promene → `makemigrations --check --dry-run` MORA reći „No changes detected" za sve app-ove. Postojeći plain-text seed-ovi (`gdpr/0002` Lorem + `pages/0004` privacy Lorem placeholder) **renderuju se bezbedno NEPROMENJENO** — plain tekst prolazi kroz sanitizer netaknut (nh3 ostavlja text node-ove; eventualni `<`/`>` u plain tekstu se tretiraju kao tekst, ne tagovi). **NE diramo seed-ove** (SM-D6 — minimalan blast-radius; RISK-1 placeholder marker u `pages/0004` ostaje; biznis/pravnik unosi pravi strukturisan HTML kroz admin).
7. **RECONCILIACIJA 5 postojećih testova** (SM-D7 — KRITIČNO; vidi AC6 + Testing). Postojeći 7-1/7-4 testovi tvrde **escape** ponašanje (`&lt;script&gt;` PRISUTAN) i `|linebreaks` u templatu. Sa `nh3` `<script>` se **STRIPUJE** (uklanja ceo node — NE escape-uje), i template koristi `|legal_html`. Ti testovi se **preformulišu na „sanitizovan/uklonjen, NE izvršen"** BEZ slabljenja XSS garancije (`<script>alert(` i `onerror=` i dalje ODSUTNI; garancija je JAČA — node nestaje umesto da postoji kao escape-ovan tekst). TEA RED preformuliše (Dev NE piše testove).
8. **CSP-forward napomena** (SM-D8) — sanitizovan inline sadržaj je u redu; nh3 stripuje inline event handlere (`on*`) i `javascript:`/`data:` scheme → render `body`-a se **komponuje sa budućim Epic 9 CSP** (nema inline event handlera koje bi CSP blokirao; emitovani `<a>`/`<table>` su statički markup bez inline JS). Dokumentovano, NE implementira CSP.

### OUT OF SCOPE (eksplicitno — granice)

- **WYSIWYG / rich-text editor widget** = **Epic 8.7** (blog CRUD sa WYSIWYG + isti `sanitize_legal_html` helper). Ova story daje SAMO sanitizacioni pipeline + render granicu; admin za sada kuca/lepi HTML ručno u `body` TextField. 8.7 dodaje editor UX (i REUSE-uje `apps/core/sanitize.py`).
- **Primena `legal_html` na blog `Post.body`** = NE u 7.5. Blog 5-3 ostaje `|linebreaks` (plain-text presedan) do 8.7 (kad WYSIWYG + sanitizacija dolaze zajedno za blog). 7.5 sanitizuje SAMO pravne strane (gdpr.CookiePolicy + pages.Page) jer je RISK-1 specifičan za njih. (`apps/core/sanitize.py` je deljiv za FORWARD reuse, ali 7.5 ga NE wire-uje u blog.)
- **Sanitize-on-save / model.clean() mutiranje** = OPCIONO, **NE u v1** (SM-D5). Render-time je primarna i dovoljna granica.
- **Schema migracija / promena `body` u zaseban HTML field tip** = NE. `body` ostaje `TextField`. 0 migracija (SM-D6).
- **Izmena seed migracija (`gdpr/0002`, `pages/0004`) u strukturisan-HTML placeholder** = OPCIONO, **NE u v1** (SM-D6). Postojeći plain Lorem renderuje se bezbedno; menjanje seed-a bi proširilo blast-radius i diralo applied migracije (NIKAD edit applied — nova bi bila potrebna). Ostavljamo kako jeste; pravi sadržaj unosi biznis kroz admin. (RISK-1 placeholder marker u `pages/0004` ostaje validan.)
- **CSP konfiguracija (CspMiddleware/CSP_*)** = **Epic 9** (django-csp je u deps ali NIJE konfigurisan — verifikovano 7-3). 7.5 SAMO dokumentuje kompatibilnost.
- **`SiteSettings.working_hours` ili druga TextField polja** = NE. Samo `body` na pravnim modelima (kolačići + statičke strane). `working_hours` ostaje `|linebreaks` (nije rich pravni dokument).
- **Defensive validacija za nemoguće slučajeve** (project-context.md:356) — NE. `sanitize_legal_html(None)→""` guard je legitiman (filter prima neproverene vrednosti), NIJE „defensive nad internim kodom".

### Princip

Jedan NOVI dep (`nh3` — Rust sanitizer, NE EOL bleach) + jedan deljen helper `apps/core/sanitize.py:sanitize_legal_html(raw)` (EKSPLICITNA allowlist: pravni tagovi p/h2-4/ul/ol/li/a/strong/em/b/i + table porodica; a→href/title/rel/target; th/td→colspan/rowspan; url_schemes http/https/mailto; link_rel="noopener noreferrer"; STRIP script/style/on*/javascript:/data:; None→"") + jedan template filter `apps/core/templatetags/legal_html.py:{{ body|legal_html }}` (sanitizuj NA RENDER-u → mark_safe SAMO posle sanitizacije; PRIMARNA XSS granica, NIKAD ne veruj stored) + SWAP `|linebreaks`→`|legal_html` na TAČNO 2 pravna template-a (gdpr/cookie_policy.html + pages/page-detail.html). `body` ostaje TextField; 0 schema migracija; seed-ovi netaknuti (plain tekst → sanitizer netaknut). Reconciliacija 5 postojećih escape-testova → sanitizacija-testovi (stripovan NE escape-ovan; XSS garancija JAČA, NE slabija). Helper deljiv → 8.7 blog WYSIWYG REUSE (forward). nh3 stripuje on*/javascript: → CSP-forward kompatibilno (Epic 9). Pune dijakritike u UI/komentarima; allowlist tagovi/scheme ASCII. NEMA WYSIWYG (8.7). NEMA sanitize-on-save v1 (SM-D5). NEMA primene na blog (do 8.7). NEMA model/schema promene. NEMA seed izmene. PETA story REOTVARA Epic 7 (rešava RISK-1 PRE go-live).

### Strukturna arhitektura — repository delta

**2 NOVA fajla (sanitize.py + templatetags/legal_html.py) + 1 EDIT (pyproject.toml dep) + 2 EDIT template-a (render swap) + reconciliacija postojećih testova + 0 migracija + 0 model promene + 0 DELETE.**

| Path | Tip | Razlog |
|---|---|---|
| `pyproject.toml` | EDIT | `uv add nh3` → dodaje `nh3>=0.2.0,<1` u `[project].dependencies` (API stabilan od `0.2.0`; `0.1.x` NEMA `url_schemes` kwarg). `uv add nh3` povlači tekuću `0.3.x` (cp38-abi3 wheel pokriva Python 3.13). `uv.lock` se regeneriše (commit ZAJEDNO). NOVI prod dep (SM-D1). |
| `apps/core/sanitize.py` | NOVO | `sanitize_legal_html(raw: str) -> str`: `if not raw: return ""` (None/prazno guard); `if not isinstance(raw, str): raw = str(raw)`; `return nh3.clean(raw, tags={...}, attributes={...}, url_schemes={...}, link_rel="noopener noreferrer")`. Modul-level konstante za ALLOWLIST (`_ALLOWED_TAGS`/`_ALLOWED_ATTRIBUTES`/`_ALLOWED_SCHEMES`) sa docstring-om koji dokumentuje SVAKU dozvolu + zašto. import `nh3`. Docstring: deljiv helper (forward-reuse 8.7 blog). (vidi AC2.) |
| `apps/core/templatetags/__init__.py` | POSTOJI | Već postoji (htmx_aria.py/i18n_fallback.py žive ovde) — NE kreira se. |
| `apps/core/templatetags/legal_html.py` | NOVO | `from django import template`; `from django.utils.safestring import mark_safe`; `from apps.core.sanitize import sanitize_legal_html`; `register = template.Library()`; `@register.filter(name="legal_html") def legal_html(value): return mark_safe(sanitize_legal_html(value))`. `is_safe`/autoescape razmatranje: filter UVEK vraća mark_safe(sanitizovano) — sanitizacija je granica, NE oslanja se na template autoescape. (vidi AC3.) |
| `templates/gdpr/cookie_policy.html` | EDIT | Linija 2: dodaj `{% load legal_html %}` (pored `{% load i18n %}`). Linija 16: `{{ policy.body|linebreaks }}` → `{{ policy.body|legal_html }}`. Komentar :15 ažuriran: body sad sanitizovan rich-HTML kroz nh3 allowlist (`{{ body|legal_html }}`) — mark_safe SAMO posle sanitizacije; WYSIWYG editor=8.7 (REUSE istog helpera). (vidi AC4.) |
| `templates/pages/page-detail.html` | EDIT | Linija 2: dodaj `{% load legal_html %}`. Linija 13: `{{ page.body|linebreaks }}` → `{{ page.body|legal_html }}`. Komentar :12 ažuriran (isto kao gdpr). (vidi AC4.) |
| `apps/gdpr/tests/test_xss.py` | EDIT (TEA reconcile) | Preformuliši `test_body_script_is_escaped_not_executed` + `test_body_img_onerror_is_escaped`: sa nh3 `<script>` se STRIPUJE (NE escape) — asercija `&lt;script&gt;` više NE važi; NOVE asercije: `<script>` (sirov) ODSUTAN **I** `&lt;script&gt;` ODSUTAN (node uklonjen, NE escape-ovan) **I** `alert(1)` možda ostaje kao goli tekst (sadržaj script-a) ALI bez izvršivog tag-a — verifikuj `<script` (otvarajući tag) ODSUTAN; `onerror` atribut ODSUTAN. DODAJ pozitivne sanitizacija-testove (vidi AC5/Testing). XSS garancija JAČA, NE slabija (SM-D7). (vidi AC6.) |
| `apps/pages/tests/test_7_4_static_pages.py` | EDIT (TEA reconcile) | Preformuliši `test_script_in_body_escaped` (:675 — escape→strip), `test_template_body_never_safe` (:691 — sad template KORISTI controlled mark_safe kroz `|legal_html`; asercija „body|safe NE u template" OSTAJE TAČNA jer `|safe` ≠ `|legal_html`, ali „mora |linebreaks" → „mora |legal_html"), `test_body_rendered_through_linebreaks` (:400 — preimenovati/preformulisati: dvolinijski plain body sad ide kroz nh3 → \n NE postaje `<br>` automatski; nh3 ne dodaje `<br>` na plain \n. Vidi G-3 — ovo je SEMANTIČKA promena ponašanja: plain-text sa \n više se NE prelama u `<br>`; ako biznis želi prelome mora koristiti `<br>`/`<p>` u HTML-u. Test se preformuliše da verifikuje sanitizovan-HTML render, NE |linebreaks \n→<br>). (vidi AC6/G-3.) |
| `apps/core/tests/test_sanitize.py` | NOVO (TEA) | RED-phase unit testovi za `sanitize_legal_html` allowlist (vidi Testing). |
| `apps/core/tests/test_legal_html_filter.py` | NOVO (TEA) | RED-phase testovi za `{{ ...|legal_html }}` filter (mark-safe-only-after-sanitize). |
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | EDIT | `epic-7` → `in-progress` (REOTVOREN); dodaj `7-5-sanitized-rich-text-pravne-strane-nh3: ready-for-dev`. SM handoff tracking (NIJE deliverable). |

**NETAKNUTO (regression guards):** `apps/gdpr/models.py` (CookiePolicy — `body` ostaje TextField, NE menja se; 0 migracija); `apps/pages/models.py` (Page + SiteSettings — `body`/`working_hours` TextField, NE menjaju se); `apps/blog/*` (Post.body ostaje `|linebreaks` do 8.7 — 7.5 NE dira blog); sve postojeće migracije (0 nove; `makemigrations --check` clean); `apps/core/utils.py`/`i18n_fallback.py`/`htmx_aria.py` (NE diraju se — `sanitize.py`+`legal_html.py` se DODAJU pored); `config/settings/*` (nh3 NIJE Django app — NE ide u INSTALLED_APPS; SM-D1); CSP/django-csp (Epic 9 — NE konfiguriše se). **KRITIČNO:** `nh3` je čista Python/Rust biblioteka (NE Django app) → SAMO `pyproject.toml`/`uv.lock`, NIKAD `INSTALLED_APPS`.

**Render-boundary ownership (granica):**

| Render granica | Vlasnik | Pravilo |
|---|---|---|
| `gdpr.CookiePolicy.body` render (`templates/gdpr/cookie_policy.html`) | **7-5** (menja 7-1 presedan) | `{{ policy.body|legal_html }}` (sanitizovan rich-HTML). 7-1 SM-D3 `|linebreaks` presedan je SUPERSEDED za pravne strane. |
| `pages.Page.body` render (`templates/pages/page-detail.html`) | **7-5** (menja 7-4 presedan) | `{{ page.body|legal_html }}`. 7-4 SM-D4 `|linebreaks` presedan SUPERSEDED. |
| `blog.Post.body` render (`templates/blog/post_detail.html`) | **5-3 / 8.7** | OSTAJE `|linebreaks` do 8.7 (WYSIWYG + sanitizacija zajedno za blog). 7.5 NE dira. |
| `sanitize_legal_html` helper | **7-5 (apps/core)** | Deljiv; 8.7 blog WYSIWYG REUSE (forward). |

## Kriterijumi prihvatanja

**AC1 — NOVI dep `nh3` dodat kroz `uv add`; NIJE Django app (SM-D1)**

- **Given** `nh3` NIJE prisutan u `pyproject.toml` (verifikovano — deps nemaju sanitizer; bleach se ne koristi)
- **When** pokrenem `uv add nh3`
- **Then**:
  - `nh3` se pojavljuje u `pyproject.toml` `[project].dependencies` sa version constraint-om `>=0.2.0,<1` (API stabilan od 0.2.0; 0.1.x nema `url_schemes`); `uv add` povlači tekuću 0.3.x
  - `uv.lock` regenerisan; oba commit-uju se ZAJEDNO
  - `nh3` se NE dodaje u `INSTALLED_APPS` (čista biblioteka, NE Django app — G-1)
  - `import nh3` radi u `uv run python -c "import nh3"` (exit 0)
- **And** `uv run python manage.py check` exit 0 (dep ne lomi startup)

**AC2 — `apps/core/sanitize.py:sanitize_legal_html(raw)` sa EKSPLICITNOM allowlist-om (SM-D2)**

- **Given** AC1 (`nh3` dostupan); `apps/core` kao deljena lokacija (pored utils.py)
- **When** kreiram `sanitize_legal_html(raw: str) -> str`
- **Then** helper MORA da:
  - DOZVOLI tagove: `p, br, h2, h3, h4, ul, ol, li, a, strong, em, b, i, table, thead, tbody, tr, th, td` (i ZADRŽI ih u izlazu sa svojim tekstom)
  - DOZVOLI atribute: `a → {href, title, rel, target}`; `th → {colspan, rowspan}`; `td → {colspan, rowspan}`
  - DOZVOLI url scheme samo: `http, https, mailto` (a `href="javascript:..."` i `href="data:..."` STRIP-ovani)
  - forsira `link_rel="noopener noreferrer"` na svaki `<a>` (nh3 dodaje/normalizuje `rel` → tabnabbing zaštita; `target="_blank"` bezbedan)
  - STRIP-uje: `<script>`, `<style>`, `on*` inline handlere (npr. `onerror`/`onclick`), sve nedozvoljene tagove (`<iframe>`/`<object>`/`<form>`/`<h1>`/`<div>`...) i atribute (`style`/`class`/`id`/`onerror`)
  - vrati `""` za `None`/prazan ulaz; coerce ne-str na str pre clean-a
- **And** funkcija je ČISTA (bez side-efekata, bez DB) i deljiva (docstring navodi forward-reuse 8.7 blog)
- **And** `uv run python manage.py check` exit 0

**AC3 — `{{ body|legal_html }}` filter sanitizuje NA RENDER-u + mark_safe SAMO posle sanitizacije (SM-D3 — PRIMARNA XSS granica)**

- **Given** AC2; `apps/core/templatetags/legal_html.py`
- **When** registrujem `@register.filter(name="legal_html")`
- **Then**:
  - `legal_html(value)` vraća `mark_safe(sanitize_legal_html(value))` — `mark_safe` se primenjuje SAMO na već-sanitizovan string (NIKAD na sirov `value`)
  - render-time sanitizacija je PRIMARNA granica: čak i ako bi stored `body` sadržao `<script>` (admin-kompromis / direktan DB upis / nesanitizovan save), render ga STRIP-uje (NIKAD ne veruj stored — SM-D3/SM-D5)
  - `None`/prazno → `""` (bez crash-a)
  - filter se može `{% load legal_html %}` u template-u
- **And** NIGDE u kodu `mark_safe`/`|safe` na SIROV `body` (samo na izlaz `sanitize_legal_html`)
- **And** `uv run python manage.py check` exit 0

**AC4 — SWAP render na DVA pravna template-a: `|linebreaks` → `|legal_html` (SM-D4)**

- **Given** AC3; `templates/gdpr/cookie_policy.html` (7-1) + `templates/pages/page-detail.html` (7-4)
- **When** zamenim render filter
- **Then**:
  - `templates/gdpr/cookie_policy.html`: `{% load legal_html %}` prisutan; `{{ policy.body|legal_html }}` (NE `|linebreaks`, NE `|safe`)
  - `templates/pages/page-detail.html`: `{% load legal_html %}` prisutan; `{{ page.body|legal_html }}` (NE `|linebreaks`, NE `|safe`)
  - komentar iznad render-linije ažuriran (sanitizovan rich-HTML kroz nh3; mark_safe samo posle sanitizacije; WYSIWYG=8.7)
  - ostatak template-a netaknut (title block, h1, „Poslednja izmena"/`updated_at`, „Važi od"/`effective_date` guard na cookie_policy — sve OSTAJE)
- **And** `body` ostaje `TextField` (0 model/schema promene — AC7)

**AC5 — Sanitizovan rich render: tabela/linkovi/struktura PROLAZE, XSS se STRIP-uje (per-locale) (SM-D2/D4)**

- **Given** AC4; seed/admin postavi `CookiePolicy.body_sr` i `Page.body_sr` na strukturisan HTML (npr. `<h2>Kolačići</h2><table><thead><tr><th>Naziv</th><th>Svrha</th></tr></thead><tbody><tr><td>_ga</td><td>Analitika</td></tr></tbody></table><ul><li>stavka</li></ul><p>Vidi <a href="https://policies.google.com/privacy">GA4 politiku</a>.</p><script>alert(1)</script>`)
- **When** GET `/sr/politika-kolacica/` i GET `/sr/politika-privatnosti/`
- **Then**:
  - HTTP 200; renderovan HTML SADRŽI: `<table`, `<thead`, `<tr`, `<th`, `<td`, `<ul`, `<li`, `<h2`, `<a href="https://policies.google.com/privacy"` (struktura ZADRŽANA, NE escape-ovana)
  - emitovani `<a>` ima `rel="noopener noreferrer"` (link_rel forsiran)
  - renderovan HTML NE SADRŽI: `<script` (otvarajući tag UKLONJEN — STRIP) **NITI** `&lt;script&gt;` (NIJE escape-ovan u tekst — node nestaje), `onerror=`, `<iframe`, `style=`, `<div`
  - **⚠️ STRIP ≠ ESCAPE (KRITIČNO za asercije):** nh3 uklanja `<script>`/`<img>` **NODE** ali MOŽE zadržati unutrašnji tekst (npr. `alert(1)` kao goli tekst, ne kao izvršiv kod). Zato asercija MORA biti `"<script" not in html` **I** `"&lt;script&gt;" not in html` (tag nestao, NIJE escape-ovan), a **NE** `"alert(1)" not in html` (goli tekst može legitimno ostati i korektna implementacija bi pala na takvoj asertaciji). Vidi strip-vs-escape tabelu u Dev Notes („Reconciliacija postojećih testova").
  - `/hu/` i `/en/` → 200 sa sr-fallback sadržajem (modeltranslation `MODELTRANSLATION_FALLBACK_LANGUAGES=("sr",)`); isti sanitizovan render
- **And** plain-text body (bez tagova, npr. iz postojećeg seed-a) renderuje se kao bezbedan tekst (nh3 ostavlja text node-ove netaknute)

**AC6 — RECONCILIACIJA 5 postojećih 7-1/7-4 testova: escape→sanitizacija BEZ slabljenja XSS garancije (SM-D7)**

- **Given** postojeći testovi tvrde **escape** ponašanje:
  - `apps/gdpr/tests/test_xss.py`: `test_body_script_is_escaped_not_executed` (tvrdi `&lt;script&gt;` PRISUTAN), `test_body_img_onerror_is_escaped` (tvrdi `&lt;img` PRISUTAN)
  - `apps/pages/tests/test_7_4_static_pages.py`: `test_script_in_body_escaped` (:675, tvrdi `&lt;script&gt;` PRISUTAN), `test_template_body_never_safe` (:691, tvrdi template ima `page.body|linebreaks`), `test_body_rendered_through_linebreaks` (:400, tvrdi `\n→<br>`)
- **When** template koristi `|legal_html` (nh3 STRIPUJE `<script>`/`<img onerror>`, NE escape-uje; `|linebreaks` više se NE koristi)
- **Then** TEA preformuliše (Dev NE piše testove) — nova ponašanja:
  - `<script>alert(1)</script>` u body → render NE SADRŽI `<script` (otvarajući tag) **NITI** `&lt;script&gt;` (node UKLONJEN, NE escape-ovan); ovo je JAČA garancija (SM-D7)
  - `<img src=x onerror="alert(1)">` → render NE SADRŽI `onerror=` niti `<img` sa onerror (img nije u allowlist-u → ceo tag strip)
  - `test_template_body_never_safe` ekvivalent: template MORA imati `|legal_html` **I** NE sme imati `|linebreaks` (dev ne sme ostaviti OBA filtera) **I** NE `{{ body|safe }}`/`mark_safe` na sirov body. Asercija „body|safe NE u template-u" OSTAJE; „mora |linebreaks" → „mora |legal_html". (Stari static guard „mark_safe NIJE u template-u" postaje IRELEVANTAN — `mark_safe` sad živi u `legal_html.py` filteru → zamenjuje ga novi guard test `test_marksafe_wraps_only_sanitized_output` koji proverava da `mark_safe` obavija SAMO `sanitize_legal_html(...)` izlaz, NIKAD sirov value.)
  - `test_body_rendered_through_linebreaks` ekvivalent: preformulisan — plain `\n` se VIŠE NE prelama u `<br>` (nh3 ne dodaje br na plain newline; G-3 semantička promena); test verifikuje da sanitizovan HTML (npr. `<p>`/`<br>` ako su u izvoru) PROLAZI, a plain `\n` ostaje plain (dokumentovana promena ponašanja)
- **And** NIJEDNA reconciliacija NE sme oslabiti XSS garanciju — `<script>alert(`/`onerror=`/`javascript:` MORAJU ostati ODSUTNI u svakom preformulisanom testu
- **And** cela `apps` test suite GREEN posle reconciliacije (nula regresija van namernih 5 reconcile-ovanih testova)

**AC7 — 0 schema migracija; `body` ostaje TextField; seed-ovi netaknuti renderuju bezbedno (SM-D6)**

- **Given** AC4 (template swap); 0 model promene
- **When** pokrenem `uv run python manage.py makemigrations --check --dry-run`
- **Then**:
  - „No changes detected" za SVE app-ove (`body` ostaje `TextField` na `CookiePolicy` i `Page` — render granica je template-only)
  - postojeće migracije `gdpr/0002_seed_cookie_policy` (Lorem) i `pages/0004_seed_privacy_policy` (privacy Lorem placeholder) NISU dirane
  - seed-ovan plain-text body renderuje se kroz `|legal_html` bez greške (plain tekst → sanitizer netaknut; nema XSS, nema crash)
- **And** RISK-1 placeholder marker u `pages/0004` ostaje validan (biznis unosi pravi strukturisan HTML kroz admin; seed je i dalje placeholder)
- **And** `uv run python manage.py check` exit 0

**AC8 — CSP-forward kompatibilnost dokumentovana (SM-D8)**

- **Given** AC2 (nh3 stripuje `on*` + `javascript:`/`data:`)
- **When** dokumentujem CSP implikaciju
- **Then**:
  - sanitizovan `body` NE sadrži inline event handlere (`onerror`/`onclick`...) → nema inline-JS koji bi budući Epic 9 CSP (`script-src`) blokirao
  - emitovani markup (`<a>`/`<table>`/`<ul>`...) je statički — kompatibilan sa strogim CSP-om bez `nonce`/`hash` za `body` sadržaj
  - dokumentovano u SM Decision Log (SM-D8) + Gotchas (G-5); CSP se NE konfiguriše (Epic 9)
- **And** ovo je dokumentaciona AC (nema koda osim render-a iz AC4) — verifikuje se kroz AC5 (`onerror=` ODSUTAN u renderu)

## Tasks / Zadaci

- [x] **Task 1 — NOVI dep `nh3`** (AC1)
  - [x] 1.1 `uv add nh3` (verifikuj da NIJE već prisutan PRE — nije)
  - [x] 1.2 Verifikuj `pyproject.toml` `[project].dependencies` ima `nh3`; `uv.lock` regenerisan
  - [x] 1.3 `nh3` NE u `INSTALLED_APPS` (G-1)
  - [x] 1.4 `uv run python -c "import nh3"` exit 0; `uv run python manage.py check` exit 0
  - [x] 1.5 **Docker rebuild + in-container verifikacija (P1, SM-D9/G-10):** rebuild Docker image; `import nh3; print(nh3.__version__)` → 0.3.5 u kontejneru (abi3 manylinux wheel instaliran bez source-build)

- [x] **Task 2 — `apps/core/sanitize.py:sanitize_legal_html`** (AC2)
  - [x] 2.1 Modul-level konstante `_ALLOWED_TAGS`/`_ALLOWED_ATTRIBUTES`/`_ALLOWED_SCHEMES` (eksplicitne, dokumentovane). ⚠️ G-11 EMPIRIJSKI: nh3 0.3.5 DIŽE ValueError ako je `rel` u `a` attrs dok je `link_rel` postavljen → `rel` IZOSTAVLJEN (link_rel SAM forsira rel="noopener noreferrer"); `th`/`td` → `colspan`/`rowspan`
  - [x] 2.2 `sanitize_legal_html(raw)`: None/prazno→""; coerce non-str; `nh3.clean(raw, tags=, attributes=, url_schemes=, link_rel="noopener noreferrer")`
  - [x] 2.3 Docstring: deljiv helper, forward-reuse 8.7 blog; svaka allowlist stavka objašnjena
  - [x] 2.4 `manage.py check` exit 0

- [x] **Task 3 — `apps/core/templatetags/legal_html.py` filter** (AC3)
  - [x] 3.1 `@register.filter(name="legal_html")` → `mark_safe(sanitize_legal_html(value))` (mark_safe SAMO posle sanitizacije)
  - [x] 3.2 None/prazno→"" graceful
  - [x] 3.3 Verifikuj `{% load legal_html %}` radi u template-u

- [x] **Task 4 — SWAP render na 2 pravna template-a** (AC4)
  - [x] 4.1 `templates/gdpr/cookie_policy.html`: `{% load legal_html %}` + `{{ policy.body|legal_html }}` (zameni `|linebreaks`); ažuriraj komentar
  - [x] 4.2 `templates/pages/page-detail.html`: `{% load legal_html %}` + `{{ page.body|legal_html }}` (zameni `|linebreaks`); ažuriraj komentar
  - [x] 4.3 Verifikuj GET `/sr/politika-kolacica/` + `/sr/politika-privatnosti/` → 200; strukturisan HTML prolazi, XSS strip (AC5)

- [x] **Task 5 — Reconciliacija postojećih testova (TEA RED)** (AC6) — TEA već reconcile-ovao test fajlove; Dev verifikovao GREEN, 0 test-mods
  - [x] 5.1 `apps/gdpr/tests/test_xss.py`: 2 testa reconcile-ovana (escape→strip) — PASS
  - [x] 5.2 `apps/pages/tests/test_7_4_static_pages.py`: reconcile-ovani (|legal_html; G-3 \n→NE<br>) — PASS
  - [x] 5.3 `apps/core/tests/test_legal_html.py` (allowlist + filter + render) — PASS
  - [x] 5.4 Verifikovano: NIJEDAN reconcile NE slabi garanciju (`<script>alert(`/`onerror=`/`javascript:` ODSUTNI)

- [x] **Task 6 — Verifikacija 0 migracija + finalna provera** (AC7, AC8)
  - [x] 6.1 `makemigrations --check --dry-run` → „No changes detected"
  - [x] 6.2 Seed-ovi netaknuti (gdpr/0002 + pages/0004) — plain body renderuje bezbedno
  - [x] 6.3 CSP-forward dokumentovan (SM-D8/G-5)
  - [x] 6.4 lint clean (ruff + djade na touched); touched suite 429 passed + full apps 1905 passed/0 failed GREEN

## Dev Notes

### nh3 — moderni Rust sanitizer (NE bleach EOL)

`nh3` je Python binding za `ammonia` (Rust HTML sanitizer) — održavan, brz, sigurniji default-i od bleach-a (koji je **EOL/unmaintained**, project-context-konzistentno izbegavamo). API: `nh3.clean(html, tags=set, attributes=dict, url_schemes=set, link_rel=str, ...)`. Bitno:
- `tags` je **set** stringova; `attributes` je **dict** `tag→set(atributa)`; `url_schemes` **set**.
- `link_rel="noopener noreferrer"` forsira `rel` na sve `<a>` (tabnabbing/leak zaštita; default nh3 je `"noopener noreferrer"` — eksplicitno postavi radi jasnoće).
- nh3 podrazumevano STRIPUJE komentare, `on*` handlere, i tagove/atribute van allowlist-a; STRIP ≠ escape (node nestaje, NE pretvara se u `&lt;...&gt;`).
- Verifikuj tačan kwarg naziv protiv instalirane verzije (`nh3.clean` signature) — Dev čita `import nh3; help(nh3.clean)` PRE pisanja allowlist-a (Gotcha G-2).

### Render-time sanitizacija = PRIMARNA granica (SM-D3/D5)

Sanitizuj **na render-u** (`|legal_html` filter), NE samo na save-u. Razlog: nikad ne veruj stored vrednosti — admin-kompromis, direktan DB upis, ili buduća migracija mogu ubaciti nesanitizovan HTML; render granica ga UVEK čisti. Sanitize-on-save (model.clean/save) je OPCIONO defense-in-depth — **NE u v1** (SM-D5): tiho mutiranje admin unosa zbunjuje (admin kuca `<table>`, save prepravi), a render granica je dovoljna i autoritativna. `mark_safe` se primenjuje SAMO na izlaz `sanitize_legal_html` (NIKAD na sirov body).

### Postojeća XSS pravila (project-context.md:15 „NIKAD |safe")

Pravilo „NIKAD |safe bez sanitizacije" se POŠTUJE: `|legal_html` interno radi `mark_safe(sanitize_legal_html(...))` — `mark_safe` POSLE sanitizacije je dozvoljen presedan (mirror 6-1/6-3/6-5/6-6 gde `mark_safe`/`format_html` markira VEĆ-escape-ovan/sklopljen sadržaj). Razlika od `|safe`: `|safe` markira SIROV body (zabranjeno); `|legal_html` markira SANITIZOVAN body (dozvoljeno — to JE sanitizacija koju je 7-1/7-4/blog presedan odlagao na „Epic 8.7").

### Reconciliacija postojećih testova — escape→strip (SM-D7, KRITIČNO)

5 postojećih testova tvrde **escape** (`&lt;script&gt;` PRISUTAN). Sa nh3 `<script>` se **STRIPUJE** (node uklonjen) → `&lt;script&gt;` više NIJE prisutan, ali `<script>alert` takođe nije → garancija je **JAČA**, NE slabija.

**STRIP vs ESCAPE — tabela ponašanja (autoritativna za TEA asercije; AC5):**

| Ulaz (`body`) | `|linebreaks` (staro, ESCAPE) | `|legal_html` / nh3 (novo, STRIP) | Korektna asercija (novo) |
|---|---|---|---|
| `<script>alert(1)</script>` | `&lt;script&gt;alert(1)&lt;/script&gt;` | tag NODE uklonjen; `alert(1)` MOŽE ostati kao goli tekst | `"<script" not in html` **I** `"&lt;script&gt;" not in html`; **NE** `"alert(1)" not in html` |
| `<img src=x onerror="alert(1)">` | `&lt;img ... onerror=...&gt;` | ceo `<img>` NODE uklonjen (van allowlist-a) | `"<img" not in html` **I** `"onerror=" not in html` |
| `<a href="javascript:...">x</a>` | `&lt;a href=...&gt;x&lt;/a&gt;` | `<a>` zadržan ALI `href` uklonjen (scheme van allowlist-a); tekst `x` ostaje | `"javascript:" not in html` |
| `<p>tekst</p>` | `&lt;p&gt;tekst&lt;/p&gt;` | `<p>tekst</p>` (zadržan — dozvoljen) | `"<p>" in html` |

⚠️ **TEA hazard:** asercija `"alert(1)" not in html` bi pala na KOREKTNOJ implementaciji (nh3 ostavlja goli tekst posle strip-a). Asertuj odsustvo **TAG-a/handler-a/scheme-a**, NE odsustvo golog teksta payload-a. TEA preformuliše asercije na „node stripovan, NE escape-ovan; izvršiv tag/handler ODSUTAN". `test_body_rendered_through_linebreaks` ima SEMANTIČKU promenu (G-3): plain `\n` se VIŠE ne prelama u `<br>` (nh3 ne dodaje br na newline; `|linebreaks` je to radio). Ovo je prihvatljiv trade-off — pravni dokument koristi eksplicitne `<p>`/`<br>`/`<ul>` umesto plain newline-ova. Dokumentuj u test docstring-u + G-3.

### Forward-reuse: 8.7 blog WYSIWYG (SM-D2)

`apps/core/sanitize.py` je u `core` (NE gdpr/pages) jer 8.7 (blog CRUD + WYSIWYG) REUSE-uje isti helper za `Post.body`. 7.5 ga NE wire-uje u blog (5-3 ostaje `|linebreaks` do 8.7). Helper je čist/deljiv.

### Project Structure Notes

- `apps/core/sanitize.py` prati per-app fajl konvenciju (project-context.md:103 — pored `utils.py`); `templatetags/legal_html.py` pored postojećih `i18n_fallback.py`/`htmx_aria.py`.
- `nh3` je čista biblioteka (NE Django app) → SAMO `pyproject.toml`/`uv.lock`, NIKAD `INSTALLED_APPS` (G-1).
- 0 migracija (body ostaje TextField); `makemigrations --check` clean (G-4).

### References

- [Source: _bmad-output/implementation-artifacts/7-1-cookiepolicy-model-admin.md] (SM-D3 body `|linebreaks` presedan koji SUPERSEDE-ujemo za pravne strane; „WYSIWYG+bleach/nh3 DEFER Epic 8.7" → sad delimično povučeno: sanitizacija SADA, editor 8.7)
- [Source: _bmad-output/implementation-artifacts/7-4-...-staticke-strane.md] (SM-D4 Page.body `|linebreaks`; RISK-1 nasleđen; placeholder seed)
- [Source: apps/gdpr/models.py:38-41] (CookiePolicy.body TextField — NE menja se)
- [Source: apps/pages/models.py:154-157] (Page.body TextField — NE menja se)
- [Source: templates/gdpr/cookie_policy.html:15-16] (render swap target)
- [Source: templates/pages/page-detail.html:12-13] (render swap target)
- [Source: apps/gdpr/tests/test_xss.py] (reconcile: escape→strip)
- [Source: apps/pages/tests/test_7_4_static_pages.py:400,675,691] (reconcile: 3 testa)
- [Source: apps/core/] (sanitize.py + templatetags/legal_html.py lokacija; pored utils.py/i18n_fallback.py)
- [Source: pyproject.toml:6-23] (deps — nh3 NIJE prisutan; bleach se ne koristi)
- [Source: _bmad-output/implementation-artifacts/sprint-status.yaml:129-133] (RISK-1 OTVOREN na 7-1+7-4; epic-7 done→reopen)
- [Source: _bmad-output/project-context.md:15,56,103,294,356] (XSS NIKAD |safe bez sanitizacije; uv add; per-app fajlovi; TEA RED; YAGNI)

## SM Decision Log

- **SM-D1 — NOVI dep `nh3` (NE bleach EOL), preko `uv add`; NIJE Django app.** Mihas Opcija B = sanitizovan rich HTML. `nh3` (Rust ammonia binding) je održavan, brz, sigurni default-i; `bleach` je EOL → izbegavamo. `uv add nh3` (project-context.md:56). Čista biblioteka → SAMO pyproject/uv.lock, NIKAD INSTALLED_APPS (G-1). Verifikovano: nh3 nije prisutan, bleach se ne koristi.
- **SM-D2 — Jedan deljen helper `apps/core/sanitize.py:sanitize_legal_html` sa EKSPLICITNOM allowlist-om.** Tagovi (p/h2-4/ul/ol/li/a/strong/em/b/i + table/thead/tbody/tr/th/td) i atributi (a→href/title/rel/target; th/td→colspan/rowspan) precizno za pravne dokumente (tabela kolačića + linkovi + struktura). url_schemes={http,https,mailto}; link_rel="noopener noreferrer". U `core` (NE gdpr/pages) za FORWARD-reuse 8.7 blog WYSIWYG. None→"".
- **SM-D3 — Render-time sanitizacija je PRIMARNA XSS granica (`|legal_html` filter).** Sanitizuj NA RENDER-u, mark_safe SAMO posle sanitizacije, NIKAD ne veruj stored. Sigurnije od save-only (stored može biti zagađen). `mark_safe(sanitize_legal_html(value))` poštuje „NIKAD |safe bez sanitizacije" (mark_safe POSLE sanitizacije = dozvoljen presedan mirror 6-x).
- **SM-D4 — SWAP `|linebreaks`→`|legal_html` na TAČNO 2 pravna template-a (gdpr/cookie_policy.html + pages/page-detail.html).** body ostaje TextField. 7-1 SM-D3 / 7-4 SM-D4 `|linebreaks` presedan je SUPERSEDED SAMO za pravne strane. Blog 5-3 ostaje `|linebreaks` do 8.7. **BLAST-RADIUS:** `page-detail.html` je GENERIČKI Page template (Page nije singleton) → swap utiče na SVE buduće Page redove (Epic 8.8 „O nama"/„Servis"/itd.), ne samo privacy. 8.8 sadržaj MORA biti HTML markup; G-3 (\n NE→<br>) važi za svaki Page kroz ovaj template. Prihvatljivo (CMS/pravne strane = strukturisan HTML), ali eksplicitno dokumentovano.
- **SM-D5 — Sanitize-on-save = OPCIONO, NE u v1.** Render filter MORA sanitizovati bez obzira (primarna granica). model.clean/save mutiranje bi tiho menjalo admin unos (konfuzija) i nije neophodno. Render-time je dovoljan i autoritativan. (Ako Security panel insistira → odvojen IMPROVEMENT; render ostaje merodavan.)
- **SM-D6 — 0 schema migracija; seed-ovi netaknuti.** body ostaje TextField → nema model promene. Postojeći plain Lorem seed-ovi (gdpr/0002 + pages/0004) renderuju se bezbedno NEPROMENJENI (plain tekst → sanitizer netaknut). NE menjamo seed-ove (minimalan blast-radius; NIKAD edit applied migracije; RISK-1 placeholder ostaje — biznis unosi pravi HTML kroz admin).
- **SM-D7 — Reconciliacija 5 postojećih testova: escape→sanitizacija, garancija JAČA.** nh3 STRIPUJE `<script>`/`<img onerror>` (node uklonjen, NE escape). `&lt;script&gt;` više nije prisutan ALI ni `<script>alert` → JAČA garancija. TEA preformuliše (Dev NE piše testove); NIJEDAN reconcile NE sme oslabiti garanciju. `test_body_rendered_through_linebreaks` ima G-3 semantičku promenu (\n više NE→<br>).
- **SM-D8 — CSP-forward kompatibilnost (Epic 9).** nh3 stripuje inline `on*` handlere + `javascript:`/`data:` scheme → render `body`-a nema inline-JS koji bi CSP `script-src` blokirao; statički markup kompatibilan bez nonce/hash. Dokumentovano; CSP se NE konfiguriše (Epic 9).
- **SM-D9 — `nh3` je kompajliran (Rust/abi3) wheel → Docker rebuild + in-container verifikacija OBAVEZNA (P1).** Za razliku od čistih-Python dep-ova, `nh3` je binarni wheel. Deploy radi `uv sync --frozen` u Docker image-u → image se MORA rebuild-ovati posle `uv add nh3`. Dev MORA verifikovati `import nh3` UNUTAR kontejnera (`docker compose -f compose/local.yml run --rm django uv run python -c "import nh3; print(nh3.__version__)"`), NE samo na host-u. Potvrdi manylinux/musllinux wheel za deploy base image — slim image bez Rust toolchain-a bi pao na source build-u. (Vidi G-10 + Task 1.5.)

## Gotchas

- **G-1 (nh3 NIJE Django app):** `nh3` je čista Python/Rust biblioteka → SAMO `pyproject.toml`/`uv.lock`, NIKAD `INSTALLED_APPS`. Dodavanje u INSTALLED_APPS bi srušilo startup (nema AppConfig).
- **G-2 (verifikuj nh3.clean signature):** tačni kwarg nazivi (`tags`/`attributes`/`url_schemes`/`link_rel`) i tipovi (set vs dict) MORAJU se proveriti protiv instalirane verzije (`help(nh3.clean)`) PRE pisanja allowlist-a — API se razlikuje od bleach-a (`tags` set NE lista; `attributes` dict tag→set).
- **G-3 (SEMANTIČKA promena: plain `\n` više NE→`<br>`):** `|linebreaks` je pretvarao plain newline u `<br>`/`<p>`; nh3 NE dodaje `<br>` na plain `\n` (sanitizuje postojeći HTML, ne formatira plain tekst). Posledica: postojeći plain-text seed-ovi/admin-unosi sa golim newline-ovima renderuju se kao jedan blok bez preloma. Pravni dokument koristi EKSPLICITNE `<p>`/`<br>`/`<ul>`. Ovo lomi `test_body_rendered_through_linebreaks` (:400) → preformulisati (AC6). Dokumentovati u admin help_text-u opciono (OQ-2).
- **G-4 (0 migracija — makemigrations --check):** posle template swap-a `makemigrations --check --dry-run` MORA reći „No changes detected" (body ostaje TextField; render je template-only). Ako iskoči migracija — neko je slučajno dirao model.
- **G-5 (CSP-forward):** nh3 stripuje `on*`/`javascript:`/`data:` → kompatibilno sa Epic 9 CSP. NE konfiguriši CSP u 7.5 (van scope-a).
- **G-6 (mark_safe SAMO posle sanitizacije):** `legal_html` filter sme `mark_safe` SAMO na izlaz `sanitize_legal_html`. NIKAD `mark_safe(value)` na sirov body. Razlika od zabranjenog `|safe` (koji markira sirov body) — `|legal_html` JESTE sanitizacija koju je presedan tražio.
- **G-7 (link_rel + target):** `link_rel="noopener noreferrer"` forsiran → `target="_blank"` linkovi su bezbedni (nema tabnabbing/window.opener leak). Ako allowlist NE bi imao `rel` u `a` atributima, nh3 svejedno dodaje rel kroz `link_rel` — eksplicitno dozvoli `rel` u `a` atributima radi konzistentnosti.
- **G-8 (allowlist NE uključuje h1/div/img/iframe/form/style):** `<h1>` je rezervisan za stranicu (template `<h1>{{ title }}</h1>`) → body koristi h2-h4. `<img>`/`<iframe>`/`<form>`/`<div>`/`style=` NISU dozvoljeni (XSS/layout-break/embed rizik) — strip. Tabele/liste/linkovi su dovoljni za pravni v1.
- **G-10 (nh3 je COMPILED Rust/abi3 wheel — Docker rebuild OBAVEZAN):** `nh3` NIJE čist-Python — to je kompajliran (Rust, abi3) wheel. Posle `uv add nh3`, Docker image se MORA rebuild-ovati (deploy radi `uv sync --frozen`). Dev MORA da verifikuje da `import nh3` radi UNUTAR docker kontejnera: `docker compose -f compose/local.yml run --rm django uv run python -c "import nh3; print(nh3.__version__)"`. Potvrdi da postoji manylinux/musllinux wheel za deploy base image (slim image NEMA Rust toolchain → source build bi PAO). Vidi SM-D9 + Task 1.5.
- **G-11 (`rel`/`link_rel` interakcija — verifikuj na instaliranoj verziji):** nh3 0.3.4+ VALIDIRA `rel` vs `link_rel` (ako je `rel` u `a` atributima a `link_rel` postavljen, ponašanje zavisi od verzije). Dev MORA pokrenuti `help(nh3.clean)` POSLE instalacije da potvrdi tačnu interakciju na instaliranoj verziji PRE pisanja allowlist-a (mirror G-2). Cilj: emitovani `<a>` UVEK ima `rel="noopener noreferrer"` (reverse-tabnabbing neutralisan) — vidi REQUIRED negativan test u ## Testing.
- **G-9 (test collection-safety):** novi core testovi importuju `sanitize_legal_html`/filter UNUTAR funkcija ili na vrhu modula (čist import, nema Django setup race) — mirror postojećih gdpr/pages test konvencija (apps importi UNUTAR funkcija gde treba django_db).

## Open Questions

- **OQ-1 (allowlist proširenje — `<hr>`/`<blockquote>`/`<code>`?):** v1 allowlist je fokusiran (tabela+liste+linkovi+naslovi+inline emphasis). Ako pravni tekst zahteva `<hr>`/`<blockquote>` → trivijalno dodati u `_ALLOWED_TAGS`. DEFER do biznis sadržaja; YAGNI v1.
- **OQ-2 (admin help za HTML body — 0-migracija alternativa):** admin za sada kuca HTML ručno (do 8.7 WYSIWYG). Da li dati admin-u smernice o dozvoljenim tagovima? Model-field `help_text` bi tražio MIGRACIJU (krši SM-D6 0-migracija) → DEFER. **0-migracija alternativa (OPCIONO, sad):** smernice kroz `ModelAdmin` (NE model polje) — npr. `formfield_overrides` / `help_texts` u admin `ModelForm`, ili readonly napomena/`fieldsets` description (npr. „Dozvoljen ograničen HTML: naslovi h2-h4, liste, tabele, linkovi"). Admin-level promena NE generiše migraciju → kompatibilno sa SM-D6. Drži kao OQ/opciono; Mihas može override (sad u 7.5 admin-level, ili sve u 8.7 uz editor).
- **OQ-3 (sanitize-on-save defense-in-depth):** SM-D5 odlaže save-time sanitizaciju. Ako Security panel zatraži → dodati u zaseban IMPROVEMENT (render ostaje primarna granica). DEFER.
- **OQ-4 (primena na blog Post.body sad ili 8.7):** `sanitize_legal_html` je deljiv; blog bi mogao odmah dobiti `|legal_html`. Ali 8.7 nosi WYSIWYG za blog → konzistentnije primeniti zajedno. DEFER blog na 8.7 (7.5 = SAMO pravne strane, RISK-1 scope).

## Testing

**TEA piše testove (RED phase) PRE Dev implementacije (project-context.md:294). Dev NIKAD ne piše testove.** pytest-django; `@pytest.mark.django_db` gde treba (helper testovi su čisti, bez DB; render testovi sa DB). Mirror format 7-1/7-4 Testing sekcije. **Collection-safety:** apps importi UNUTAR funkcija gde treba (G-9).

### Sanitizer helper (apps/core/tests/test_sanitize.py) — čist, bez DB
- `test_allowed_tags_kept` — `<p>/<h2>/<h3>/<h4>/<ul>/<ol>/<li>/<a>/<strong>/<em>/<b>/<i>/<table>/<thead>/<tbody>/<tr>/<th>/<td>` PROLAZE (prisutni u izlazu)
- `test_script_stripped` — `<script>alert(1)</script>` → izlaz NE sadrži `<script` NITI `&lt;script&gt;` (STRIP, ne escape)
- `test_style_stripped` — `<style>...</style>` strip
- `test_on_handlers_stripped` — `<a href="..." onclick="x">` → `onclick` ODSUTAN; `<img onerror=...>` → ceo tag strip
- `test_javascript_scheme_stripped` — `<a href="javascript:alert(1)">` → href strip/sanitizovan (NE `javascript:`)
- `test_data_scheme_stripped` — `<a href="data:text/html,...">` → strip
- `test_disallowed_tags_stripped` — `<iframe>/<object>/<form>/<div>/<h1>/<img>` strip
- `test_disallowed_attributes_stripped` — `style=`/`class=`/`id=` na dozvoljenom tagu → ODSUTNI
- `test_a_allowed_attributes` — `<a href title rel target>` zadržava href/title/rel/target
- `test_th_td_colspan_rowspan` — `colspan`/`rowspan` na th/td zadržani
- `test_link_rel_forced` — emitovani `<a>` ima `rel="noopener noreferrer"`
- **`test_rel_opener_overridden_to_noopener` (REQUIRED, negativan — reverse-tabnabbing; G-11):** ulaz `<a href="https://x" target="_blank" rel="opener">` → izlaz MORA forsirati `rel="noopener noreferrer"` (`'rel="noopener noreferrer"' in out`) **I** NE sme sadržati `rel="opener"` (`'rel="opener"' not in out`). Dokazuje da je reverse-tabnabbing NEUTRALISAN (a NE samo da „neki rel postoji"). Verifikuj interakciju `rel` vs `link_rel` na instaliranoj verziji (`help(nh3.clean)`, G-11) PRE pisanja allowlist-a.
- `test_none_returns_empty` — `sanitize_legal_html(None) == ""`; `("") == ""`
- `test_plain_text_passthrough` — plain tekst bez tagova → vraćen kao tekst (bezbedan), `<`/`>` u tekstu escape-ovani kao tekst (ne tag)
- `test_diacritics_preserved` — sadržaj sa č/ć/ž/š/đ prolazi netaknut
- `test_empty_body_returns_empty` — `sanitize_legal_html("") == ""` (prazan ulaz → prazan izlaz)
- `test_only_disallowed_tag_keeps_text` — `<div>tekst</div>` → `<div>` STRIPOVAN, tekst `"tekst"` ZADRŽAN (`"tekst" in out` AND `"<div" not in out`)
- `test_svg_onload_stripped` — `<svg onload=alert(1)>` → ceo node STRIPOVAN (`"<svg" not in out` AND `"onload" not in out`)
- `test_html_comment_stripped` — `<!-- x -->` → uklonjen (`"<!--" not in out`)
- `test_bare_angle_brackets_in_plain_text_safe` (G-2 — verifikuj na instaliranoj nh3 verziji) — plain tekst sa golim `<`/`>` (npr. `"cena < 5 i > 3"`) renderuje se bezbedno (bez izvršivog markup-a); ovo je ponašanje koje treba POTVRDITI protiv instalirane nh3 verzije (`help(nh3.clean)` / brzi REPL probe), ne pretpostaviti

### Filter (apps/core/tests/test_legal_html_filter.py)
- `test_filter_returns_safestring` — `legal_html("<p>x</p>")` je `SafeString` (mark_safe primenjen)
- `test_filter_sanitizes_before_marksafe` — `legal_html("<script>x</script>")` → SafeString koji NE sadrži `<script` (mark_safe SAMO posle sanitizacije; nikad sirov)
- `test_filter_none_empty` — `legal_html(None)`/`("")` → `""` (SafeString prazan)
- `test_filter_registered` — `{% load legal_html %}{{ x|legal_html }}` render radi (template Engine)
- **`test_marksafe_wraps_only_sanitized_output` (guard — zamenjuje stari template `mark_safe`-not-in-template static guard):** statička provera `apps/core/templatetags/legal_html.py` izvora — `mark_safe(...)` sme da obavija ISKLJUČIVO `sanitize_legal_html(...)` izlaz, NIKAD sirov `value` (npr. assert da izvor sadrži `mark_safe(sanitize_legal_html` i NE sadrži `mark_safe(value`). Pošto `mark_safe` sad živi u filter fajlu (ne u template-u), ovaj guard preuzima ulogu starog „mark_safe NE u template" static guard-a.

### Render — gdpr (apps/gdpr/tests/test_xss.py — RECONCILE + dodatak)
- `test_body_script_is_stripped_not_executed` (RECONCILE od escaped) — `<script>alert(1)</script>` u body → render NE sadrži `<script` NITI `&lt;script&gt;`; `<script>alert` ODSUTAN (garancija JAČA)
- `test_body_img_onerror_is_stripped` (RECONCILE) — `<img src=x onerror="alert(1)">` → `onerror=` i `<img` ODSUTNI (img van allowlist-a)
- `test_body_table_and_links_rendered` (NOVI) — strukturisan HTML (table+a) → `<table`/`<a href="https://...`/`rel="noopener` PRISUTNI; `<script` ODSUTAN; per-locale sr
- `test_body_never_safe_filter` (zadrži/ojačaj) — template NE koristi `{{ policy.body|safe }}` ni `mark_safe` na sirov body; KORISTI `|legal_html`

### Render — pages (apps/pages/tests/test_7_4_static_pages.py — RECONCILE)
- `test_script_in_body_stripped` (RECONCILE :675) — `<script>` strip (NE `&lt;script&gt;`); `<script>alert` ODSUTAN
- `test_template_body_uses_legal_html_not_safe` (RECONCILE :691) — template MORA sadržati `|legal_html` (`"|legal_html" in template_source`) **I** NE sme sadržati `|linebreaks` (`"|linebreaks" not in template_source` — dev ne sme slučajno ostaviti OBA filtera) **I** NE `body|safe`/`mark_safe` na sirov body. (Stari static-guard „`mark_safe` NIJE u template-u" je sad IRELEVANTAN — `mark_safe` živi u `legal_html.py` filteru, ne u template-u; vidi novi guard test ispod.)
- **`test_stale_linebreaks_comment_updated` ILI ručna napomena (:380):** `test_privacy_page_200_sr` (:380) i dalje PROLAZI, ali komentar/docstring `"body |linebreaks"` je STALE → ažurirati na `|legal_html` (čista reconciliacija; nije funkcionalna promena testa)
- `test_body_structured_html_rendered` (RECONCILE :400 `_through_linebreaks`) — strukturisan HTML (`<p>`/`<ul>`/`<table>`) PROLAZI sanitizaciju; plain `\n` se VIŠE NE prelama u `<br>` (G-3 dokumentovana promena); XSS strip
- `test_body_table_links_rendered` (NOVI) — privacy page sa table+linkovima → struktura PRISUTNA, XSS strip, per-locale fallback

### Dep + migracije (apps/core/tests/ ili postojeći)
- `test_nh3_importable` — `import nh3` radi (smoke)
- `test_no_new_migrations` — `makemigrations --check --dry-run` → „No changes detected" (0 schema promene; AC7) — mirror postojećih no-migration testova (gdpr 7-2/7-3)

### Regresija (broader)
- cela `apps` suite GREEN posle reconciliacije (7-1 cookie page 200, 7-4 privacy page 200, blog ostaje |linebreaks netaknut, sve ostalo nepromenjeno)
- NIJEDAN reconcile NE slabi XSS garanciju (`<script>alert(`/`onerror=`/`javascript:` ODSUTNI u svim render testovima)
