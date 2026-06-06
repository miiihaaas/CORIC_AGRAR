---
story_id: "6.6"
story-key: 6-6-seo-hreflang-html-tagovi-locale-aware-slug-ovi
title: SEO Hreflang HTML Tagovi + Locale-aware Slug-ovi
status: review
epic: 6
epic_num: 6
epic_title: SEO & Discoverability
module: seo
created: 2026-06-06
last_modified: 2026-06-06
complexity: M
author: Mihas (SM autonomous; ŠESTA i POSLEDNJA story Epic 6 — SEO & Discoverability → ZATVARA epic. NOVI presentation/SEO-head deliverable u apps.seo: HTML-`<head>` hreflang link tagovi koji crawler-u (Google/Bing) navode SVE jezičke alternative trenutne strane → sprečava duplicate-content penalizaciju kroz sr/hu/en verzije. **JEDAN glavni artefakt + 1 verifikacioni:** (1) NOVI `apps/seo/templatetags/hreflang.py` sa `{% hreflang_links %}` simple_tag(takes_context=True) koji emituje TAČNO 4 `<link rel="alternate" hreflang="...">` (sr, hu, en, x-default→sr); (2) VERIFIKACIJA da slug-ovi koriste ASCII transliteraciju (Ć→c) kroz postojeći `apps/core/utils.py:slugify_ascii` (NE `safe_slugify` — vidi SM-D7/G1 ime-reconciliacija; NEMA novog slug koda/migracije). **GLAVNA odluka (SM-D1) — URL GENERACIJA (CRUX): `django.urls.translate_url(request.path, lang)` wrapped u `request.build_absolute_uri(...)`.** translate_url resolve-uje trenutni path → reverse-uje pod `override(lang)` → vraća ekvivalentnu URL u tom jeziku sa zamenjenim locale prefiksom (`/sr/proizvod/x/` → `/hu/proizvod/x/`); ako resolve padne (Resolver404) ILI reverse padne (NoReverseMatch) → translate_url GRACEFULNO vraća original URL (NE raise) → tag NIKAD ne 500-uje. **prefix_default_language=True (config/urls.py:49 — VERIFIKOVANO):** sr DOBIJA `/sr/` prefiks (root `/`→`/sr/` redirect) → SVE 4 href-a su prefiksovane (`/sr/`, `/hu/`, `/en/`), nema „prefix-less sr" izuzetka. **SM-D2 x-default→sr:** 4. link je `<link rel="alternate" hreflang="x-default" href="{sr_url}">` (ISTI href kao sr link — Google preporuka za default/jezik-selektor stranu; sr je LANGUAGE_CODE). **SM-D3 self-referencing (best practice):** SVAKA strana lista SVE verzije UKLJUČUJUĆI sebe (sr strana emituje sr+hu+en+x-default; ne samo „druge" jezike) — Google zahteva reciprocitet + self-reference. **SM-D4 hreflang kod = bare sr/hu/en (NE region/script subtag):** match LANGUAGES ključeve (base.py:148-152) I 6-2 sitemap `alternates=True` koji emituje `hreflang="sr|hu|en"` (Django izvodi iz LANGUAGES) → HTML hreflang MORA biti KONZISTENTAN sa sitemap alternates (isti skup, isti kodovi). **SM-D5 mount point — NOVI `{% block hreflang %}` u base.html `<head>`:** `{% block hreflang %}{% hreflang_links %}{% endblock %}` POSLE `{% block social_meta %}` (6-3) / oko canonical → svaka strana koja extend-uje base dobija hreflang; non-extending strane (robots.txt/sitemap.xml — text/xml, BEZ `<head>`) NE crash-uju (ne extend-uju base). Zaseban block (NE unutar social_meta) → buduće strane mogu override-ovati/disable-ovati hreflang nezavisno (npr. noindex coming-soon). **SM-D6 KONZISTENTNOST sa 6-2/6-3:** hreflang HTML = isti skup jezika + isti URL-shape kao 6-2 sitemap `<xhtml:link>` alternates; canonical (6-3) ostaje SELF-referencijalan na trenutnu-locale URL, hreflang DODAJE alternate set (NE kontradiktuje canonical — canonical=ova strana, hreflang=sve verzije ove strane). **SECURITY (SM-D8):** href-ovi građeni kroz translate_url + build_absolute_uri (host bounded ALLOWED_HOSTS); emisija kroz `format_html` autoescape (mirror 6-1/6-3 head-injection-safe); NIKAD `|safe` na sirovoj URL. translate_url vraća već-reverse-ovan internal path (ne user-controlled), ali href ide kroz autoescape svejedno (defense + `&` u query → `&amp;`). **SM-D9 query string:** href-ovi su INHERENTNO param-free jer tag gradi URL iz `request.path` (koji u Django NIKAD ne sadrži query — query je u QUERY_STRING/request.GET), NE iz `get_full_path()` → hreflang href-ovi NEMAJU `?...` čak i kad request ima `?page=2`. ISPRAVNO/željeno: konzistentno sa 6-3 canonical (takođe param-free, iz obj.get_absolute_url()) + Google smernica (hreflang → kanonski, param-stripovani URL). NE prebacuj na get_full_path(); nema strip logike jer request.path je već param-free (YAGNI). **SM-D7 slug verifikacija (druga polovina AC, NE novi kod):** AC990 traži „verifikovati kroz safe_slugify" — `safe_slugify` NE POSTOJI (G1: stvarna funkcija je `apps/core/utils.py:slugify_ascii`, Story 2.1; ima dedikovan `apps/core/tests/test_utils.py`). Odluka: ovo je VERIFIKACIONI task (TEA test asertuje `slugify_ascii('Ćorić Agrar')=='coric-agrar'` + Č/Š/Ž/Đ→c/s/z/d + digrafovi Dž/Lj/Nj), NE novi slug_sr/hu/en kolone, NE migracija. Slug-ovi su DELJENI-ASCII kroz locale (JEDAN slug po objektu; locale se razlikuje SAMO po URL prefiksu /sr//hu//en/ — VERIFIKOVANO: SluggedModel slug NIJE translatable, products/blog translation.py ne registruju slug). Per-locale slug-ovi = DEFER (v1: single ASCII slug). **0 MIGRACIJA, 0 model promene, 0 novih dep-ova, 0 novih asseta.** RISK TIER: MEDIUM — (a) NOVI template tag sa netrivijalnom URL-generacijom (translate_url resolve/reverse semantika + graceful fallback je crux — pogrešno = 500 ili pogrešni href-ovi); (b) GLOBALNI `<head>` injection na SVAKU stranu = security surface (autoescape MORA biti tačan) + count-disciplina (TAČNO 4 linka, nema duplikata); (c) KONZISTENTNOST sa 6-2 sitemap + 6-3 canonical (ne sme kontradiktovati). NEMA migracije/auth/forme/HTMX/eksternog poziva — čist render tag + verifikacioni test. ZATVARA Epic 6.)
depends_on:
  - 1-4-i18n-setup-sa-locale-url-routing-i-switcher          # i18n_patterns(prefix_default_language=True) (config/urls.py:49 VERIFIKOVANO) — sr DOBIJA /sr/ prefiks → sve 4 href-a prefiksovane; LANGUAGES=[sr,hu,en] (base.py:148-152) + LANGUAGE_CODE="sr" → hreflang kodovi + x-default target; LocaleMiddleware aktivira locale (translate_url override); set_language switcher već koristi „ekvivalentna-URL-u-novoj-lokali" semantiku (config/urls.py:5-9) — translate_url je ISTI mehanizam
  - 6-3-robots-txt-open-graph-twitter-card-meta              # base.html {% block social_meta %}{% seo_head %}{% endblock %} (head injection point + format_html SAFE pattern + _canonical_url self-referencijalni canonical koji hreflang DOPUNJUJE, NE kontradiktuje — SM-D6); {% load seo_meta %} u base.html (hreflang dodaje {% load hreflang %})
  - 6-2-sitemap-auto-generation-sa-hreflang                  # sitemap već emituje <xhtml:link rel=alternate hreflang=sr|hu|en> kroz i18n=True/alternates=True (Django LANGUAGES-derived) → HTML hreflang MORA biti KONZISTENTAN (isti skup jezika + bare sr/hu/en kodovi + isti URL-shape; SM-D4/SM-D6); 6-2 NE emituje x-default (sitemap nema x-default koncept) — HTML hreflang DODAJE x-default (SM-D2; razlika dokumentovana)
  - 2-1-brand-series-category-subcategory-modeli             # apps/core/utils.py:slugify_ascii (Story 2.1 — STVARNO ime, NE safe_slugify; G1) + SluggedModel slug NIJE translatable (deljeni-ASCII slug kroz locale; SM-D7); apps/core/tests/test_utils.py (postojeći slug testovi — 6-6 verifikacija ih DOPUNJUJE/referencira)
  - 1-7-reusable-visual-komponente                           # base.html <head> struktura (gde se mount-uje {% block hreflang %})
---

# Story 6.6: SEO Hreflang HTML Tagovi + Locale-aware Slug-ovi

Status: review

## Opis

As a **search engine (Googlebot/Bingbot crawler)**,

I want **hreflang HTML `<link rel="alternate">` tagove u `<head>` svake strane koji navode sve jezičke alternative (sr/hu/en) + `x-default`**,

so that **vidim sve jezičke verzije iste strane, serviram pravu verziju pravom korisniku, i NE penalizujem sajt za duplicate content kroz tri lokalizovane verzije iste URL-e**.

Ovo je **ŠESTA i POSLEDNJA story Epic 6 (SEO & Discoverability)** — njenim završetkom Epic 6 je kompletan. Ima **DVA deliverable-a**:

1. **HTML hreflang link tagovi** — NOVI `apps/seo/templatetags/hreflang.py` sa `{% hreflang_links %}` template tag-om koji za TRENUTNU stranu emituje TAČNO 4 `<link rel="alternate" hreflang="...">` taga u `<head>`: po jedan za `sr`, `hu`, `en`, plus `x-default` (koji ukazuje na `sr` verziju). Tag se mount-uje GLOBALNO u `base.html` kroz NOVI `{% block hreflang %}` → svaka strana koja extend-uje base dobija hreflang.

2. **Locale-aware slug verifikacija** — VERIFIKACIJA (NE novi kod) da slug-ovi koriste ASCII transliteraciju (`Ć → c`) kroz postojeći `apps/core/utils.py:slugify_ascii` (Story 2.1). Slug-ovi su DELJENI-ASCII kroz sve locale (jedan slug po objektu; lokal se razlikuje SAMO po URL prefiksu).

> **GLAVNA odluka (SM-D1) — URL GENERACIJA JE CRUX.** Tag mora za trenutni `request.path` da proizvede ekvivalentnu URL-u u svakom od sr/hu/en. Idiomatski Django alat je `django.urls.translate_url(url, lang_code)` (VERIFIKOVANO u `django/urls/base.py`): ono `resolve()`-uje path → `reverse()`-uje pod `override(lang_code)` → vraća istu rutu sa zamenjenim locale prefiksom. Wrapuj ga u `request.build_absolute_uri(...)` da dobiješ apsolutnu URL. **Graceful by design:** ako `resolve()` padne (`Resolver404` — npr. nepostojeći path) ILI `reverse()` padne (`NoReverseMatch`), `translate_url` vraća ORIGINAL URL (NE raise) → tag NIKAD ne 500-uje, u najgorem slučaju emituje trenutni path za sve jezike (degradacija, ne pad).

> **prefix_default_language=True (SM-D1, KRITIČNO):** `config/urls.py:49` eksplicitno postavlja `prefix_default_language=True` — to znači da `sr` (default) DOBIJA `/sr/` prefiks (root `/` redirektuje na `/sr/`). Dakle SVE 4 href-a su locale-prefiksovane: `/sr/...`, `/hu/...`, `/en/...`. NEMA „prefix-less sr" izuzetka — ne tretiraj sr kao goli path bez prefiksa.

### IN SCOPE (šta ova story isporučuje)

1. **NOVI `apps/seo/templatetags/hreflang.py`** (AC1/AC2/AC3) — DRUGI tag-modul u apps.seo (uz `seo_meta.py`). Sadrži:
   - `@register.simple_tag(takes_context=True)` `hreflang_links(context)` — vraća safe HTML: TAČNO 4 `<link rel="alternate" hreflang="...">` taga (sr, hu, en, x-default).
   - URL generacija kroz `translate_url(request.path, lang)` + `request.build_absolute_uri(...)` po jeziku (SM-D1).
   - x-default link sa istim href-om kao sr (SM-D2).
   - SVE href-ove kroz `format_html` autoescape (SM-D8 — NIKAD `|safe` na URL).
   - Graceful: `request is None` (izolovan render bez HTTP konteksta) → vrati prazan string (NE 500; mirror 6-1/6-3 `if request is not None` guard).
2. **`templates/base.html` EDIT** (AC1, SM-D5) — `{% load hreflang %}` (vrh, uz `{% load seo_meta %}`) + NOVI `{% block hreflang %}{% hreflang_links %}{% endblock %}` u `<head>` (POSLE `{% block social_meta %}`).
3. **Slug verifikacioni test** (AC4, SM-D7) — TEA dodaje/proširuje test koji asertuje `slugify_ascii` ASCII transliteraciju (`Ćorić Agrar`→`coric-agrar`; Č/Ć/Š/Ž/Đ→c/c/s/z/d; digrafovi Dž/Lj/Nj) — VERIFIKACIJA postojećeg ponašanja, NE novi kod. (Ako `apps/core/tests/test_utils.py` već pokriva sve → 6-6 SAMO referencira/dopunjuje gap-ove; NE duplira.)

### OUT OF SCOPE (eksplicitno — granice)

- **Per-locale slug kolone (`slug_sr`/`slug_hu`/`slug_en`)** = **NE** (SM-D7 — v1 je JEDAN deljeni-ASCII slug; locale se razlikuje SAMO po URL prefiksu /sr//hu//en/. SluggedModel slug NIJE translatable — VERIFIKOVANO products/blog translation.py ne registruju slug). Per-locale slug-ovi su buduća opcija ako biznis traži lokalizovane slug-ove — DEFER (OQ-1). **0 migracija.**
- **Promena `slugify_ascii` funkcije** = **NE** (SM-D7 — funkcija RADI ispravno za Č/Ć/Š/Ž/Đ + digrafove; 6-6 je VERIFIKUJE, ne menja). Ime u AC990 (`safe_slugify`) je netačno — stvarno ime je `slugify_ascii` (G1; dokumentovano, NE novi alias).
- **`og:locale` / `og:locale:alternate` meta tagovi** = **NE za 6-6** (6-3 OUT-OF-SCOPE ih je defer-ovao na 6-6 kao OQ-5; ALI AC990 traži SAMO `<link rel="alternate" hreflang>` — og:locale je zaseban OG-locale surface. Odluka: og:locale/alternate = DEFER post-Epic-6, NIJE u AC990 — YAGNI; hreflang `<link>` je ono što crawler koristi za jezičko targetiranje). (OQ-2.)
- **Promena 6-2 sitemap hreflang emisije** = **NE** (sitemap već emituje hreflang kroz `i18n=True/alternates=True` — 6-6 HTML hreflang je KONZISTENTAN sa njim, NE menja sitemap; SM-D6).
- **Promena 6-3 canonical/og:url** = **NE** (canonical ostaje self-referencijalan na trenutnu-locale URL; hreflang DOPUNJUJE alternate set — SM-D6; seo_head NETAKNUT).
- **hreflang na HTMX partial response-ima** = **NE** (HTMX fragmenti nemaju `<head>`; hreflang je samo na full-page render-ima koji extend-uju base.html — mirror 6-3 OG-na-htmx OUT-OF-SCOPE).
- **hreflang na non-extending strane (robots.txt/sitemap.xml)** = N/A (text/plain + XML, BEZ `<head>`, NE extend-uju base.html → `{% block hreflang %}` se nikad ne renderuje tamo — nije propust, dizajn).
- **Region/script subtag hreflang kodovi (`sr-Latn`, `sr-RS`, `en-US`)** = **NE** (SM-D4 — bare sr/hu/en match LANGUAGES ključeve + 6-2 sitemap; uvođenje subtag-a bi DESINHRONIZOVALO HTML i sitemap hreflang). (OQ-3 — ako budući SEO zahtev traži sr-Latn distinkciju, to je LANGUAGES-wide promena, NE 6-6.)
- **Query-string strip iz hreflang href-ova** = **NE / N/A** (SM-D9 — href-ovi se grade iz `request.path` koji je INHERENTNO param-free; nema query-ja da se strip-uje. NE koristi `get_full_path()` koji bi uveo query. Konzistentno sa 6-3 param-free canonical + Google smernica.)
- **noindex/disable hreflang na coming-soon/search stranama** = **NE za v1** (block postoji za buduće override; v1 emituje hreflang svuda gde base.html extend-uje — prihvatljivo; LOW-HARM asimetrija sa 6-2 sitemap exclude — dokumentovano G9/OQ-5, NE gradimo noindex-detekciju).

### Princip

JEDAN tanak presentation/SEO-head tag + jedan base.html mount + jedan verifikacioni test, sve LOW-COUPLING. Tag koristi Django ugrađeni `translate_url` (NE hand-rolled prefix-swap string manipulaciju — translate_url resolve/reverse je robustan na sve url-pattern oblike + graceful na ne-resolve-ujuće path-ove). x-default→sr (SM-D2). Self-referencing 4-link set (SM-D3). Bare sr/hu/en kodovi konzistentni sa 6-2 sitemap (SM-D4/SM-D6). NOVI zaseban `{% block hreflang %}` (SM-D5) → globalno, ali nezavisno override-ljivo. SVE href-ove kroz `format_html` autoescape (SM-D8 — head-injection-safe; mirror 6-1/6-3 SAFE pattern; NIKAD `|safe`). `request is None` graceful prazan string. Slug-deo je VERIFIKACIJA postojećeg `slugify_ascii` (SM-D7 — NE novi kod, NE migracija). 0 migracija, 0 model promene, 0 novih dep-ova. NEMA defensive boilerplate-a; NEMA premature per-locale slug kolona.

### Strukturna arhitektura — repository delta

**1 NOVI fajl (`apps/seo/templatetags/hreflang.py`) + 1 EDIT (`templates/base.html`) + 1 verifikacioni test (slug ASCII) + 0 MIGRACIJA + 0 model promene + 0 novih dep-ova + 0 novih asseta.**

| Path | Tip | Razlog |
|---|---|---|
| `apps/seo/templatetags/hreflang.py` | NOVO | `{% hreflang_links %}` `simple_tag(takes_context=True)`: 4 `<link rel="alternate" hreflang="sr\|hu\|en\|x-default">` kroz `translate_url(request.path, lang)` + `build_absolute_uri` (SM-D1) + x-default→sr (SM-D2) + `format_html` autoescape (SM-D8) + `request is None` graceful prazan string. DRUGI tag u apps.seo (uz seo_meta.py). (AC1/AC2/AC3) |
| `templates/base.html` | EDIT | `{% load hreflang %}` (vrh, uz `{% load seo_meta %}`) + `{% block hreflang %}{% hreflang_links %}{% endblock %}` u `<head>` POSLE `{% block social_meta %}{% seo_head %}{% endblock %}` linije (SM-D5). |
| `apps/core/tests/test_utils.py` (DOPUNA) ILI `apps/seo/tests/test_hreflang.py` (slug-verifikacioni deo) | EDIT/NOVO (TEA) | Slug ASCII verifikacioni test: `slugify_ascii('Ćorić Agrar')=='coric-agrar'` + Č/Ć/Š/Ž/Đ→c/c/s/z/d + digrafovi Dž/Lj/Nj (SM-D7/AC4). Ako test_utils.py već pokriva → referenciraj, NE dupliraj. |
| `apps/seo/tests/test_hreflang.py` | NOVO (TEA) | RED-phase testovi za `{% hreflang_links %}` (vidi Testing). Dev NE piše testove. |
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | EDIT | `6-6-seo-hreflang-html-tagovi-locale-aware-slug-ovi` → `ready-for-dev`. SM handoff tracking (NIJE deliverable). |

**NETAKNUTO (regression guards):** SVI modeli + migracije (`makemigrations --check --dry-run` mora reći „No changes detected" — 6-6 je 0-migration; NE dira slug kolone); `apps/core/utils.py:slugify_ascii` (6-6 SAMO VERIFIKUJE — 0 promene; SM-D7); `apps/seo/templatetags/seo_meta.py` (6-1/6-3 — canonical/og ostaje; hreflang je zaseban NOVI fajl; SM-D6); `apps/seo/sitemaps.py` (6-2 — sitemap hreflang NETAKNUT; HTML hreflang je KONZISTENTAN ali NE deli kod; SM-D6); `config/urls.py` (i18n_patterns/prefix_default_language — 6-6 ČITA prefix_default_language ponašanje, NE menja); `config/settings/base.py` (LANGUAGES/LANGUAGE_CODE — ČITA, NE menja); postojeći base.html blokovi `{% block title %}`/`{% block meta_description %}`/`{% block social_meta %}`/`{% block extra_head %}` (hreflang je NOVI block, NE menja postojeće); `pyproject.toml` (0 novih dep-ova — `translate_url`/`build_absolute_uri`/`format_html` su Django core); sav CSS/JS (hreflang je čist `<head>` meta, 0 CSS/JS).

## Kriterijumi prihvatanja

**AC1 — `{% hreflang_links %}` tag + base.html mount → svaka strana ima hreflang u `<head>` (SM-D1/D5)**

- **Given** NOVI `apps/seo/templatetags/hreflang.py:hreflang_links(context)` + `base.html` `{% load hreflang %}` + `{% block hreflang %}{% hreflang_links %}{% endblock %}` u `<head>`
- **When** renderujem BILO KOJU full-page stranu koja extend-uje base.html (home/listing/detail) na bilo kojoj locale
- **Then** `<head>` sadrži `<link rel="alternate" hreflang="...">` tagove (vidi AC2 za tačan skup)
- **And** mount je u `<head>` POSLE `{% block social_meta %}` (uz canonical/OG — SM-D5)
- **And** non-extending strane (robots.txt /robots.txt, sitemap.xml) NE renderuju hreflang (ne extend-uju base; nije propust)

**AC2 — TAČNO 4 hreflang linka: sr, hu, en, x-default (SM-D2/D3/D4)**

- **Given** AC1
- **When** renderujem stranu i prebrojim `<link rel="alternate" hreflang=...>` tagove
- **Then** ima TAČNO 4 linka (NE 3, NE 6):
  - `<link rel="alternate" hreflang="sr" href="{sr_url}">`
  - `<link rel="alternate" hreflang="hu" href="{hu_url}">`
  - `<link rel="alternate" hreflang="en" href="{en_url}">`
  - `<link rel="alternate" hreflang="x-default" href="{sr_url}">`
- **And** hreflang kodovi su bare `sr`/`hu`/`en`/`x-default` (NE `sr-Latn`/`sr-RS`/region subtag — match LANGUAGES ključeve + 6-2 sitemap; SM-D4)
- **And** SVAKA strana lista SVE 4 (self-referencing — sr strana TAKOĐE emituje sr link; SM-D3)

**AC3 — href-ovi su apsolutni + tačan per-locale prefiks + ista strana u svakom jeziku (SM-D1)**

- **Given** zahtev na `/sr/proizvod/agri-tracking-tb804/` (Host: testserver)
- **When** renderujem hreflang linkove
- **Then**:
  - `hreflang="sr"` href = `http://testserver/sr/proizvod/agri-tracking-tb804/` (apsolutna, `/sr/` prefiks — prefix_default_language=True)
  - `hreflang="hu"` href = `http://testserver/hu/proizvod/agri-tracking-tb804/` (`/hu/` prefiks, ISTA strana)
  - `hreflang="en"` href = `http://testserver/en/proizvod/agri-tracking-tb804/` (`/en/` prefiks, ISTA strana)
  - `hreflang="x-default"` href = ISTI kao sr (`http://testserver/sr/...`; SM-D2)
- **And** svaki href je APSOLUTAN (`http(s)://host/...` kroz `request.build_absolute_uri`)
- **And** svaki ne-default-locale href se razlikuje od sr-a SAMO po locale prefiksu (`/hu/` vs `/sr/`) — ISTA ruta/slug (translate_url resolve→reverse; SM-D1)
- **And** zahtev na `/hu/proizvod/...` daje IDENTIČAN set 4 linka (hreflang je nezavisan od trenutne aktivne locale — sve verzije se uvek listaju; reciprocitet/SM-D3)
- **And** na kanonski-rutiranoj strani, href za AKTIVNI jezik (`hreflang="{aktivni}"`) == href 6-3 canonical-a (`<link rel="canonical">`) — oba iz istog build_absolute_uri obrasca, oba param-free (hreflang-self == canonical lock; vidi Testing #5). Caveat: ne-kanonski ulazni path (6-4 301 / APPEND_SLASH) razrešava na kanonski PRVO — očekivano/prihvatljivo.

**AC4 — Slug-ovi koriste ASCII transliteraciju verifikovano kroz `slugify_ascii` (AC990, SM-D7, G1)**

- **Given** `apps/core/utils.py:slugify_ascii` (Story 2.1 — STVARNA funkcija; AC990 ime „safe_slugify" je netačno → G1)
- **When** verifikujem ASCII transliteraciju (test)
- **Then**:
  - `slugify_ascii('Ćorić Agrar') == 'coric-agrar'` (Ć→c, ć→c, razmak→`-`, lowercase)
  - `slugify_ascii('Čačak') == 'cacak'` (Č/č→c)
  - `slugify_ascii('Šabac') == 'sabac'` (Š/š→s); `Žitište`→`zitiste` (Ž/ž→z); `Đorđe`→`dorde` (Đ/đ→d)
  - digrafovi: `Dž`→`dz`, `Lj`→`lj`, `Nj`→`nj` (slugify_ascii.SR_DIGRAPHS)
  - rezultat je `allow_unicode=False` (čist ASCII, kebab-case)
- **And** slug NIGDE ne sadrži Unicode dijakritike (project-context § Slugovi: ASCII u URL-u)
- **And** slug-ovi su DELJENI-ASCII kroz locale (JEDAN slug po objektu; locale se razlikuje SAMO po URL prefiksu /sr//hu//en/ — SluggedModel slug NIJE translatable; SM-D7) — NEMA per-locale slug kolona u v1
- **And** ovo je VERIFIKACIONI test (NE novi slug kod, NE migracija, NE re-implementacija slug logike — `slugify_ascii` već ovako radi od Story 2.1)
- **And** `apps/core/tests/test_utils.py` (Story 2.1) VEĆ pokriva dijakritike (Č/Š/Ž/Đ→c/s/z/d) + digrafove (Dž/Lj/Nj) + mixed kebab-case → 6-6 SAMO REFERENCIRA tu pokrivenost i dodaje ISKLJUČIVO specifičan AC4 primer `slugify_ascii('Ćorić Agrar') == 'coric-agrar'` AKO već nije prisutan (NE duplira postojeće asercije; verifikovano: tačan string „Ćorić Agrar" trenutno NIJE u test_utils.py)

**AC5 — Security: href-ovi autoescaped (NEMA head injection); graceful kad request odsutan (SM-D8)**

- **Given** `{% hreflang_links %}` emituje href-ove kroz `format_html`
- **When** renderujem
- **Then** SVAKI href je emitovan kroz `format_html` autoescape (`&` u href → `&amp;`; nijedna sirova URL ne ide kroz `|safe` na sopstvenoj vrednosti); NE može probiti atribut/`<head>` (mirror 6-1/6-3 SAFE pattern)
- **And** NIGDE se ne koristi `|safe` na pojedinačnoj URL vrednosti (`mark_safe` SME SAMO na već-`format_html`-sklopljenom skupu linkova — mirror seo_head `mark_safe("\n".join(parts))`)
- **And** kad `request is None` (izolovan tag-render bez HTTP konteksta) → tag vraća PRAZAN string (NE 500; build_absolute_uri zahteva request → guard pre poziva)
- **And** kad `translate_url` ne može da resolve-uje path (npr. ne-rutiran path) → translate_url GRACEFULNO vraća original path → tag emituje 4 linka sa istim path-om za sve jezike (degradacija, NE 500; SM-D1 graceful)

**AC6 — KONZISTENTNOST sa 6-2 sitemap + 6-3 canonical (SM-D6)**

- **Given** 6-2 sitemap emituje `<xhtml:link rel="alternate" hreflang="sr|hu|en">` (i18n=True/alternates=True) + 6-3 emituje self-referencijalni `<link rel="canonical">`
- **When** uporedim HTML hreflang (6-6) sa sitemap alternates (6-2) i canonical (6-3)
- **Then** HTML hreflang kodovi (sr/hu/en) su ISTI skup kao sitemap alternates (bare kodovi, ne subtag — SM-D4)
- **And** HTML hreflang URL-shape (apsolutan, locale-prefiksovan) je konzistentan sa sitemap URL-shape
- **And** „konzistentnost" je ograničena na SKUP-JEZIKA + KODOVE + URL-shape — NE na skup STRANA: 6-2 sitemap pokriva SAMO indeksabilne javne strane (npr. `is_coming_soon=False`), dok HTML hreflang `<link>` tag emituje SITE-WIDE (svuda gde base.html extend-uje, uključujući noindex/coming-soon). Ova razlika u domenu strana je OČEKIVANA i prihvatljiva (vidi G9/OQ-5) — AC ne tvrdi 1:1 podudaranje skupa strana sitemap-a i hreflang emisije.
- **And** canonical (6-3, self-referencijalan na trenutnu-locale URL) NIJE u kontradikciji sa hreflang (canonical = OVA strana; hreflang = SVE jezičke verzije ove strane uključujući canonical — komplementarno, NE duplikat)
- **And** HTML hreflang DODAJE `x-default` (koji sitemap NEMA — sitemap nema x-default koncept; razlika je očekivana, SM-D2)

## Tasks / Subtasks

> **Konvencija:** `[TEA-RED]` = Test Architect piše test PRE implementacije (mora FAIL). `[DEV-GREEN]` = Developer implementira da test prođe. **Dev NIKAD ne piše testove.** **NEMA migracije** (6-6 je 0-migration; NE dira slug kolone; `makemigrations --check --dry-run` mora reći „No changes detected"). **NEMA `uv add`** (`translate_url`/`build_absolute_uri`/`format_html`/`mark_safe` su Django core).

- [x] **Task 1 — `apps/seo/templatetags/hreflang.py` skelet + registracija (AC1)** `[DEV-GREEN]`
  - [x] 1.1 Kreiraj `apps/seo/templatetags/hreflang.py`. Importi: `from django import template`, `from django.urls import translate_url`, `from django.utils.html import format_html`, `from django.utils.safestring import mark_safe`, `from django.conf import settings`. `register = template.Library()`. Module docstring (srpski, dijakritike) objašnjava CRUX (translate_url(request.path, lang) + build_absolute_uri; x-default→sr; prefix_default_language=True → svi prefiksovani; SM-D1/D2).
  - [x] 1.2 `apps/seo/templatetags/` već postoji (seo_meta.py iz 6-1) → SAMO dodaj novi fajl; `__init__.py` već prisutan.

- [x] **Task 2 — `hreflang_links` tag: 4 linka kroz translate_url (AC2/AC3/AC5, SM-D1/D2/D3/D4/D8)** `[DEV-GREEN]`
  - [x] 2.1 `@register.simple_tag(takes_context=True)` `def hreflang_links(context):`.
  - [x] 2.2 `request = context.get("request")`. **`if request is None: return ""`** (graceful — build_absolute_uri zahteva request; AC5; mirror 6-1/6-3 guard).
  - [x] 2.3 Za SVAKI jezik iz `settings.LANGUAGES` (sr, hu, en — bare kodovi; SM-D4): `lang_url = request.build_absolute_uri(translate_url(request.path, lang_code))`. (translate_url uzima trenutni path → vraća ekvivalent u `lang_code` sa zamenjenim locale prefiksom; build_absolute_uri ga apsolutizuje. SM-D1.)
  - [x] 2.4 **x-default href = sr href (SM-D2):** izračunaj sr URL JEDNOM (npr. `default_url = request.build_absolute_uri(translate_url(request.path, settings.LANGUAGE_CODE))`) i reuse-uj ga za x-default link. (LANGUAGE_CODE="sr" — base.py:158.)
  - [x] 2.5 Emituj parts redom kroz `format_html` (SM-D8 — SVAKI href autoescaped): za svaki `(lang_code, _)` u LANGUAGES → `format_html('<link rel="alternate" hreflang="{}" href="{}">', lang_code, lang_url)`; zatim x-default → `format_html('<link rel="alternate" hreflang="x-default" href="{}">', default_url)`. `return mark_safe("\n".join(parts))`. (mark_safe SAMO na join-u već-format_html-escaped delova — mirror seo_head; NIKAD `|safe` na sirovoj URL.)
  - [x] 2.6 **TAČNO 4 linka (AC2):** 3 iz LANGUAGES (sr/hu/en) + 1 x-default. Ne dodaj duplikate, ne preskači self-locale (self-referencing — SM-D3). (Iteracija po LANGUAGES garantuje 3 + eksplicitan x-default = 4; ako se LANGUAGES promeni, broj prati — to je željeno, AC test broji prema LANGUAGES+1.)
  - [x] 2.7 **Graceful ne-resolve (AC5):** NE dodaji try/except oko translate_url — translate_url SAM hvata Resolver404/NoReverseMatch i vraća original URL (VERIFIKOVANO u django/urls/base.py). (NE preinastruktiraj — trust Django graceful contract; project-context § no defensive validation.)

- [x] **Task 3 — `base.html` global `{% block hreflang %}` mount (AC1, SM-D5)** `[DEV-GREEN]`
  - [x] 3.1 Dodaj `{% load hreflang %}` u `base.html` (vrh, uz `{% load seo_meta %}` i ostale load-ove). (Djade konsolidovao load-grupu u 1 liniju `{% load django_bootstrap5 hreflang htmx_aria i18n seo_meta static %}` — hreflang uključen.)
  - [x] 3.2 Dodaj `{% block hreflang %}{% hreflang_links %}{% endblock %}` u `<head>` — **POSLE** linije `{% block social_meta %}{% seo_head %}{% endblock %}` (6-3), pre/oko `{% block extra_head %}`. (Zaseban block → buduće strane mogu override-ovati; SM-D5.)
  - [x] 3.3 Verifikuj da je `{% block hreflang %}` NOVI (ne postoji već) i ne kolizira sa postojećim blokovima.

- [x] **Task 4 — Slug ASCII verifikacioni test (AC4, SM-D7, G1)** `[TEA-RED]` (TEA — test VEĆ napisan; Dev verifikovao zelen.)
  - [x] 4.1 Proveri `apps/core/tests/test_utils.py` (postoji — Story 2.1) za postojeću `slugify_ascii` pokrivenost. (`test_slugify_ascii_coric_agrar_example` prisutan i PASS — `slugify_ascii('Ćorić Agrar')=='coric-agrar'`; dijakritici/digrafovi već pokriveni.)
  - [x] 4.2 **NE menjaj `slugify_ascii`** (SM-D7 — funkcija RADI; 6-6 je VERIFIKACIJA). **NE kreiraj `safe_slugify` alias** (G1). (Potvrđeno — `apps/core/utils.py` NETAKNUT.)
  - [x] 4.3 (Opciono) integration assert — N/A; verifikovano da slugify_ascii proizvodi čist ASCII (`.isascii()` assert u testu).

- [x] **Task 5 — Verifikacija + lint (AC1-AC6)** `[DEV-GREEN]`
  - [x] 5.1 `makemigrations --check --dry-run` → „No changes detected" (0-migration guard — POTVRĐENO).
  - [x] 5.2 Manualna provera: tag emituje 4 hreflang linka (sr/hu/en/x-default), x-default==sr href, svi apsolutni + `/sr|hu|en/` prefiksovani (verifikovano kroz test_hreflang.py 21 testova).
  - [x] 5.3 `ruff check apps/seo/` „All checks passed!" + `djade --check templates/base.html` clean (posle djade reformat — load-grupa konsolidovana).
  - [x] 5.4 Svi TEA testovi zeleni (apps/seo/tests/ + test_utils.py = 211 passed); postojeći 6-1/6-2/6-3/6-5 SEO testovi OSTAJU zeleni (regression — 0 fail).
  - [x] 5.5 **Head-count test ownership (6-6 OWNS).** `[TEA-RED]` `apps/seo/tests/test_head_integration.py` OSTAJE zelen posle base.html edita; eksplicitni hreflang-count lock-ovi (`test_full_base_page_has_exactly_four_hreflang_links`, `test_hreflang_links_are_not_counted_as_canonical`, `test_hreflang_does_not_break_existing_head_counts`) zeleni. Nijedan count-test ne hvata `rel="alternate"` kao title/desc/canonical.

## Dev Notes

### Relevantni postojeći pattern-i (REUSE — NE reinventuj)

- **`apps/seo/templatetags/seo_meta.py` (6-1/6-3)** — referentni pattern za apps.seo template tag: `format_html` autoescape SVAKE vrednosti, `mark_safe("\n".join(parts))` na sklopljenom skupu (NIKAD `|safe` na sirovoj vrednosti), `request = context.get("request")` + `if request is not None` guard. `_canonical_url(obj, request)` (6-3) koristi `request.build_absolute_uri(...)` — hreflang koristi ISTI build_absolute_uri obrazac. **hreflang je ZASEBAN fajl** (NE dodaje se u seo_meta.py — SM-D6/odvojena odgovornost).
- **`config/urls.py:49` `prefix_default_language=True`** — VERIFIKOVANO: sr dobija /sr/ prefiks (root /→/sr/). `set_language` view (config/urls.py:5-9) već radi „redirect na ekvivalentnu URL u novoj lokali" — translate_url je ISTI Django mehanizam (resolve→override→reverse).
- **`django.urls.translate_url(url, lang_code)`** — VERIFIKOVANO u `django/urls/base.py`: `resolve(unquote(parsed.path))` → `with override(lang_code): reverse(...)` → `urlunsplit(...)`. (urlunsplit bi sačuvao query/fragment AKO ih ulaz ima — ali ulaz je `request.path` koji ih NIKAD nema → output je inherentno param-free; SM-D9.) Resolver404/NoReverseMatch → vraća ORIGINAL url (graceful, NE raise). **Ovo je idiomatski Django pristup za hreflang** — NE hand-roll prefix-swap string manipulaciju.
- **`apps/core/utils.py:slugify_ascii` (Story 2.1)** — dvostepena transliteracija: SR_DIGRAPHS (Dž/Lj/Nj str.replace) → SR_DIAKRITICI (Ć/Č/Š/Ž/Đ str.translate) → Django `slugify(allow_unicode=False)`. **STVARNO ime — NE `safe_slugify` (AC990 greška, G1).** Ima `apps/core/tests/test_utils.py`.

### Source tree komponente koje se diraju

- NOVO: `apps/seo/templatetags/hreflang.py`
- EDIT: `templates/base.html` (+`{% load hreflang %}` +`{% block hreflang %}`)
- TEA: `apps/seo/tests/test_hreflang.py` (NOVO) + `apps/core/tests/test_utils.py` (dopuna ako gap; AC4)

### Testing standards (sažetak)

pytest-django; testovi kolokovani `apps/seo/tests/test_hreflang.py`. RenderContext sa `request` (RequestFactory ili test client GET) — translate_url + build_absolute_uri zahtevaju request. Parametrizuj po locale (/sr/, /hu/, /en/) da verifikuješ self-referencing reciprocitet (AC3). Count assert (TAČNO 4 linka). i18n test: aktivan LANGUAGE preko `translation.override` ili test client `HTTP_ACCEPT_LANGUAGE`/URL prefiks.

### Testing — eksplicitni slučajevi (TEA piše; RED-phase)

> Konvencija: `[TEA-RED]`. Dev NE piše testove. Svi referenciraju AC iznad.

1. **Count lock — TAČNO 4 hreflang linka (AC2).** Render full-page strane (extends base.html) → prebroj `<link rel="alternate" hreflang=...>` → MORA biti TAČNO 4 (sr/hu/en/x-default). NE 3, NE 6, nema duplikata.
2. **Per-locale prefiks + apsolutni href + ista ruta (AC3) — DETAIL path.** GET `/sr/proizvod/<slug>/` → sr/hu/en href-ovi razlikuju se SAMO po `/sr|hu|en/` prefiksu, svi apsolutni (`http://testserver/...`), x-default == sr href.
3. **Reciprocitet (AC3, SM-D3).** GET `/hu/proizvod/<slug>/` daje IDENTIČAN set 4 linka kao GET `/sr/...` (hreflang nezavisan od aktivne locale; self-referencing).
4. **LISTING / paginated strana (AC3 — Adversarial dopuna).** GET listing rute (npr. lista traktora / polovne mašine / blog index) → `translate_url` proizvodi ispravne per-locale prefiksovane href-ove i NA LISTING ruti (ne samo detail). **Param-free assert (SM-D9):** GET listing sa `?page=2` → hreflang href-ovi NE sadrže `?page=2` ni bilo koji query (grade se iz `request.path` koji je param-free). Lock-uje da paginacija/UTM ne curi u hreflang.
5. **hreflang-self == 6-3 canonical (AC3/AC6 — Adversarial lock).** Na kanonski-rutiranoj strani: href `<link rel="alternate" hreflang="{aktivni_jezik}">` MORA biti JEDNAK href-u `<link rel="canonical">` (6-3). Oba se grade iz istog apsolutni-URL obrasca (build_absolute_uri) i oba su param-free → moraju se slagati. **Poznati caveat (očekivano/prihvatljivo):** ako se strana dosegne preko ne-kanonskog ulaznog path-a (npr. 6-4 301 redirect ili APPEND_SLASH redirect), `request.path` PRE redirect-a može se razlikovati — ali redirect razrešava na kanonski path PRVO, pa finalno-renderovana strana ima usaglašen hreflang-self i canonical. (Ne testira se pre-redirect stanje.)
6. **Security autoescape (AC5, SM-D8).** Svaki href emitovan kroz `format_html` → `&` → `&amp;`; nijedna sirova URL kroz `|safe`; ne probija atribut/`<head>`.
7. **Graceful — `request is None` → prazan string (AC5).** Izolovan tag-render bez request-a vraća `""` (NE 500).
8. **Graceful ne-resolve path (AC5, G2).** Ne-rutiran path → translate_url vraća original → 4 linka sa istim path-om za sve jezike (degradacija, NE 500). NE testirati try/except (translate_url je sam graceful).
9. **Head-count regression OWNERSHIP (AC1 — vidi „Head-count test ownership" niže).** Hreflang-count lock (TAČNO 4 `<link rel=alternate hreflang>`) + verifikacija da postojeći 6-1/6-3 head-count testovi OSTAJU zeleni.
10. **Slug ASCII verifikacija (AC4) — vidi Task 4.** Referenciraj postojeći `apps/core/tests/test_utils.py`; dodaj SAMO AC4 primer `slugify_ascii('Ćorić Agrar') == 'coric-agrar'` ako nije prisutan.

### Head-count test ownership (6-6 OWNS — mirror 6-3 C1)

Dodavanje 4 globalna `<link rel="alternate" hreflang=...>` u base.html `<head>` može da utiče na postojeće SEO head testove → **6-6 EKSPLICITNO OWNS reviziju** sledećih i njihovo lock-ovanje za nove hreflang linkove:

- `apps/seo/tests/test_head_integration.py` (6-1/6-3 — broji `<title>` / `<meta name="description">` / `<link rel="canonical">`).
- Bilo koji `test_og_*` / `test_seo_*` koji broji head elemente.

**Nalaz validatora (verifikovati, ne pretpostaviti):** postojeći count-testovi broje `<title>` / `<meta name="description">` / `<link rel="canonical">` — NE broje `<link rel="alternate">` → verovatno OSTAJU zeleni. TEA MORA: (a) pokrenuti postojeće head testove POSLE base.html edita i potvrditi da su zeleni; (b) dodati EKSPLICITAN hreflang-count lock (TAČNO 4 `<link rel="alternate" hreflang>`) — ne ostavljati implicitno; (c) ako neki count-test koristi širi regex koji slučajno uhvati `rel="alternate"` → ažurirati ga (6-6 ga OWNS). Ovo zatvara SM-A/SM-B (regresija head-count) eksplicitno.

### Project Structure Notes

- hreflang tag u `apps/seo/templatetags/` (mirror seo_meta.py lokacija; arhitektura `architecture.md:614` eksplicitno navodi `templatetags/hreflang.py`). Usklađeno sa unified structure.
- Slug: ASCII u URL-u (project-context § Slugovi + § Anti-pattern Unicode u URL-u); pune dijakritike u UI tekstu (project-context § Šišana latinica) — hreflang tag emituje SAMO URL-ove (ASCII), nema UI teksta.
- 0 migracija — usklađeno sa „NETAKNUTO" regression guards; `makemigrations --check` mora ostati čist.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-6.6] (AC990 — `<link rel="alternate" hreflang="sr|hu|en|x-default">`, 4 linka, x-default→sr, slug ASCII verifikacija; ime `safe_slugify` je netačno → `slugify_ascii`)
- [Source: config/urls.py#49] prefix_default_language=True — sr dobija /sr/ prefiks (CRUX za href korektnost)
- [Source: config/settings/base.py#148-158] LANGUAGES=[sr,hu,en] + LANGUAGE_CODE="sr" (hreflang kodovi + x-default target)
- [Source: django/urls/base.py#translate_url] resolve→override→reverse; graceful Resolver404/NoReverseMatch (SM-D1)
- [Source: apps/seo/templatetags/seo_meta.py#6-3] format_html SAFE pattern + build_absolute_uri + request guard (SM-D8)
- [Source: apps/seo/sitemaps.py#6-2] i18n=True/alternates=True hreflang konzistentnost (SM-D4/SM-D6)
- [Source: apps/core/utils.py#slugify_ascii] STVARNA slug funkcija (SM-D7/G1)
- [Source: _bmad-output/implementation-artifacts/6-3-robots-txt-open-graph-twitter-card-meta.md] base.html social_meta block mount + canonical/og:url komplementarnost (SM-D5/SM-D6)

## SM Decision Log

- **SM-D1 — URL generacija kroz `translate_url(request.path, lang)` + `build_absolute_uri` (CRUX):** Tag mora za trenutni path da proizvede ekvivalent u svakom jeziku. Django `translate_url` (resolve→`override(lang)`→reverse) je idiomatski alat — robustan na sve url-pattern oblike, GRACEFULNO vraća original URL ako resolve/reverse padne (Resolver404/NoReverseMatch → NE raise). (Ulaz je `request.path` → href-ovi inherentno param-free; SM-D9.) `prefix_default_language=True` (config/urls.py:49) znači sr DOBIJA /sr/ prefiks → svi href-ovi prefiksovani (NEMA prefix-less sr). NE hand-roll prefix-swap (krhko na razne url-oblike).
- **SM-D2 — x-default → sr:** 4. link `hreflang="x-default"` href = ISTI kao sr link (LANGUAGE_CODE="sr"). Google preporuka: x-default za jezik-selektor/default stranu; sr je primarni/default jezik projekta. Izračunaj sr URL jednom, reuse za x-default.
- **SM-D3 — Self-referencing (sve verzije na svakoj strani):** SVAKA locale strana emituje SVA 4 linka uključujući SVOJU verziju (sr strana emituje sr+hu+en+x-default). Google zahteva reciprocitet + self-reference; iteracija po LANGUAGES (ne „other languages") to garantuje. AC3 testira identičan set kroz /sr/, /hu/, /en/.
- **SM-D4 — Bare sr/hu/en kodovi (NE region/script subtag):** Match LANGUAGES ključeve (base.py) I 6-2 sitemap koji emituje `hreflang="sr|hu|en"` (Django LANGUAGES-derived). HTML hreflang MORA biti konzistentan sa sitemap (isti skup, isti kodovi) — uvođenje sr-Latn/sr-RS bi desinhronizovalo. (Bare ISO 639-1 kodovi su validni za Google.)
- **SM-D5 — Mount: NOVI `{% block hreflang %}` u base.html `<head>` POSLE social_meta:** Globalno (svaka strana koja extend-uje base), zaseban block (nezavisno override-ljiv buduće — npr. noindex coming-soon). Non-extending strane (robots.txt/sitemap.xml — bez `<head>`) NE crash-uju. Placement uz canonical/OG (6-3).
- **SM-D6 — Konzistentnost sa 6-2 sitemap + 6-3 canonical:** hreflang HTML = isti jezici + URL-shape kao sitemap alternates (NE deli kod — odvojena odgovornost, ali konzistentan output). canonical (self-referencijalan, trenutna-locale URL) je KOMPLEMENTARAN — canonical=ova strana, hreflang=sve verzije ove strane. HTML hreflang DODAJE x-default (sitemap ga nema — očekivana razlika).
- **SM-D7 — Slug = VERIFIKACIJA postojećeg `slugify_ascii` (NE novi kod/migracija):** AC990 traži „verifikovati safe_slugify". `safe_slugify` NE postoji (G1) — stvarna funkcija je `slugify_ascii` (Story 2.1). Ovo je verifikacioni test task (asertuj Ć/Č/Š/Ž/Đ→ASCII + digrafovi). Slug-ovi su DELJENI-ASCII kroz locale (JEDAN slug po objektu; SluggedModel slug NIJE translatable — VERIFIKOVANO; locale = SAMO URL prefiks). Per-locale slug kolone = DEFER (v1: single ASCII slug; OQ-1). 0 migracija, 0 slug koda.
- **SM-D8 — Security: href-ovi kroz format_html autoescape; request=None graceful:** SVAKI href emitovan kroz `format_html` (`&`→`&amp;`, head-injection-safe); `mark_safe` SAMO na join-u već-escaped delova (mirror seo_head); NIKAD `|safe` na sirovoj URL. translate_url vraća internal reverse-ovan path (ne user-controlled) ali autoescape je defense svejedno. `request is None` → prazan string (NE 500).
- **SM-D9 — Query string: href-ovi su INHERENTNO param-free (gradi se od `request.path`, NE `get_full_path()`):** Tag prosleđuje `request.path` u `translate_url`. U Django `request.path` NIKAD ne sadrži query string — query živi u `request.META["QUERY_STRING"]` / `request.GET` (a `request.get_full_path()` bi vratio path+query). Pošto tag koristi `request.path`, hreflang href-ovi su UVEK bez parametara po konstrukciji, čak i kad je zahtev došao sa `?page=2` ili `?utm_*=...`. **Ovo je ISPRAVNO/željeno ponašanje:** (a) hreflang ostaje KONZISTENTAN sa 6-3 canonical-om koji je takođe param-free (gradi se iz `obj.get_absolute_url()`, bez query-ja); (b) prati Google smernicu da hreflang treba da pokazuje na kanonske, parameter-stripovane URL-ove. **NE prebacuj na `get_full_path()`** (uveo bi query u href-ove → desinhronizacija sa canonical + dupliranje parametrizovanih varijanti). NE dodaji ni eksplicitnu strip logiku — `request.path` je već param-free, pa nema šta da se strip-uje (YAGNI). (Dev napomena: ne traži „phantom" query-preservaciju — tag je dizajniran da je nikad nema.)

## Gotchas

- **G1 — `safe_slugify` NE POSTOJI; stvarno ime je `slugify_ascii`:** AC990 referencira `apps/core/utils.py:safe_slugify` — ta funkcija NE postoji u kodu. Stvarna funkcija (Story 2.1) je `slugify_ascii(text)` u `apps/core/utils.py`. **NE kreiraj `safe_slugify` alias** (premature/backwards-compat shim — project-context zabranjuje). Verifikuj/referenciraj `slugify_ascii` direktno. (Grep potvrdio: `safe_slugify` se pojavljuje SAMO u epics.md:990.)
- **G2 — translate_url je VEĆ graceful — NE dodaji try/except:** `translate_url` interno hvata `Resolver404` (resolve fail) i `NoReverseMatch` (reverse fail) i vraća ORIGINAL url. Dodavanje try/except oko njega je defensive boilerplate (project-context § no defensive validation). Trust Django contract.
- **G3 — prefix_default_language=True → sr NIJE prefix-less:** Ne pretpostavljaj da sr ima goli path bez prefiksa. config/urls.py:49 daje sr `/sr/` prefiks. Svi href-ovi (uključujući sr i x-default) su `/sr|hu|en/...`.
- **G4 — translate_url uzima request.path (sa već prisutnim locale prefiksom), NE goli path:** `request.path` na /hu/proizvod/x/ JE `/hu/proizvod/x/`. translate_url ga resolve-uje (resolve radi sa locale prefiksom kroz i18n_patterns) → reverse pod novom locale daje /sr|en/... — ZAMENA prefiksa, ne dupliranje. Ne sklanjaj prefiks ručno pre translate_url.
- **G5 — build_absolute_uri zahteva request → request=None guard PRVI:** Bez request-a nema host-a za apsolutizaciju. `if request is None: return ""` MORA biti pre svakog build_absolute_uri/translate_url poziva (AC5). U produkciji request je uvek prisutan; ovo je unit-render bezbednost (mirror 6-1/6-3).
- **G6 — TAČNO 4 linka, nema duplikata:** social_meta (6-3) je JEDAN block sa child override → 1 OG set; hreflang je zaseban block, default poziv jednom → 4 linka. Detail strane NE override-uju hreflang (za razliku od social_meta) → nema rizika dupliranja. AC2 count-test (==4) lock-uje.
- **G7 — Konzistentnost kodova: ako neko promeni LANGUAGES, hreflang i sitemap moraju ostati u sinhronu:** Oba derivaju iz settings.LANGUAGES (sitemap kroz Django i18n=True; hreflang kroz iteraciju po settings.LANGUAGES — NE hardkoduj sr/hu/en string-liste u tagu; čitaj settings.LANGUAGES da automatski prati promene + ostane konzistentan sa sitemap-om).
- **G8 — `{% block hreflang %}` mora biti NOVI block:** Verifikuj da base.html nema već `hreflang` block. Dodaj posle social_meta. Ne meri ga sa social_meta/extra_head.
- **G9 — noindex/coming-soon emituju hreflang (sitemap ih NE uključuje) — PRIHVAĆENA v1 asimetrija, NE gradi detekciju:** noindex coming-soon strane extend-uju base.html → emituju 4 hreflang linka, dok 6-2 sitemap te strane ISKLJUČUJE (`is_coming_soon=False`). Ovo je LOW-HARM: (a) Google ignoriše hreflang na noindex stranama; (b) self-referencijalan hreflang ne „truje" druge strane. **NE dodaji noindex-detekciju u tag** (YAGNI, van v1 scope) — drži kao DOKUMENTOVANO prihvaćeno ograničenje. Buduća story bi mogla da gate-uje `{% block hreflang %}` kroz template override na noindex stranama (`{% block hreflang %}{% endblock %}` na coming-soon templatu) BEZ promene taga. (Vidi OQ-5; AC6 „konzistentnost" je zato suženo na skup-jezika, NE skup-strana.)

## Open Questions

- **OQ-1 — Per-locale slug kolone (slug_sr/hu/en)?** v1: NE (single deljeni-ASCII slug; SM-D7). Ako biznis želi lokalizovane slug-ove (npr. /hu/termek/<hu-slug>/ vs /sr/proizvod/<sr-slug>/) → buduća story sa slug translatable + migracija + URL pattern promena. Trenutno NIJE traženo.
- **OQ-2 — og:locale / og:locale:alternate meta?** 6-3 ih je defer-ovao na 6-6 (OQ-5), ali AC990 traži SAMO `<link rel="alternate" hreflang>`. Odluka: og:locale/alternate = DEFER post-Epic-6 (nije u AC990; YAGNI). Da li biznis/SEO traži og:locale za Facebook lokalizovani preview? Ako da → mini follow-up (mapiranje sr→sr_RS, hu→hu_HU, en→en_US u seo_head).
- **OQ-3 — Region/script subtag (sr-Latn) u budućnosti?** v1 bare sr/hu/en (SM-D4). Ako Google Search Console signalizira potrebu za sr-Latn distinkcijom (ćirilica vs latinica targeting) → LANGUAGES-wide promena (utiče i na sitemap + URL prefikse), NE izolovana hreflang promena.
- **OQ-4 — hreflang na coming-soon/search/404 stranama?** v1 emituje hreflang svuda gde base.html extend-uje (uključujući coming-soon/search). Da li te strane treba da izostave hreflang (npr. noindex)? Block omogućava buduć override; v1 ne pravi izuzetak (prihvatljivo — hreflang ne nameće indeksiranje).
- **OQ-5 — noindex/coming-soon hreflang vs 6-2 sitemap asimetrija (PRIHVAĆENO v1 ograničenje):** HTML hreflang tag emituje SITE-WIDE dok 6-2 sitemap EXCLUDE-uje coming-soon (`is_coming_soon=False`) → noindex strane imaju hreflang ali nisu u sitemap-u. Procena: LOW-HARM (Google ignoriše hreflang na noindex; self-ref ne truje druge strane) → DEFER suppression. **NE gradimo noindex-detekciju u v1** (G9 — YAGNI). Buduća story: gate `{% block hreflang %}` kroz template override na noindex/coming-soon templatu (bez promene taga). Formalizuje OQ-4 kao prihvaćeno-i-odgođeno.

## Dev Agent Record

### Agent Model Used

claude-opus-4-8 (Dev — GREEN phase)

### Debug Log References

- `docker compose -f compose/local.yml run --rm django uv run pytest apps/seo/tests/ apps/core/tests/test_utils.py -v` → 211 passed
- `ruff check apps/seo/` → All checks passed!
- `djade --check templates/base.html` → clean (posle reformat)
- `makemigrations --check --dry-run` → No changes detected

### Completion Notes List

- NOVI `apps/seo/templatetags/hreflang.py` sa `{% hreflang_links %}` simple_tag(takes_context=True): 4 `<link rel="alternate" hreflang="sr|hu|en|x-default">` kroz `translate_url(request.path, lang)` + `request.build_absolute_uri(...)`; x-default href == sr href; `request is None` → "" guard; format_html autoescape + `mark_safe("\n".join(parts))`; iteracija po `settings.LANGUAGES` (NE hardkoduj); NEMA try/except (translate_url graceful).
- `templates/base.html`: dodat `hreflang` u load-grupu + NOVI `{% block hreflang %}{% hreflang_links %}{% endblock %}` ODMAH posle `{% block social_meta %}`. Djade reformat konsolidovao load-grupu u jednu liniju i dodao `{% endblock content %}` — projektni djade lint gate; hreflang mount netaknut.
- Slug-deo (AC4) = VERIFIKACIJA — `apps/core/utils.py:slugify_ascii` NETAKNUT; `test_slugify_ascii_coric_agrar_example` PASS.
- 0 migracija, 0 model promene, 0 novih dep-ova, 0 novih asseta. Dev NE pisao testove.

### File List

- NOVO: `apps/seo/templatetags/hreflang.py`
- EDIT: `templates/base.html`
