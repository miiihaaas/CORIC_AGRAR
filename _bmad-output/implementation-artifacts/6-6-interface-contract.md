# Story 6.6 — Interface Contract: SEO Hreflang HTML Tagovi + Locale-aware Slug-ovi

**Status:** TEA RED phase complete — failing tests committed; Dev implements GREEN.
**Module:** `apps/seo`
**Authoritative source:** `_bmad-output/implementation-artifacts/6-6-seo-hreflang-html-tagovi-locale-aware-slug-ovi.md` (AC1–AC6, SM-D1..D9, G1..G9).

Ovaj dokument je UGOVOR koji Dev MORA satisfy da TEA testovi pređu u GREEN. NE re-derivirati — interfejs je niže fiksiran.

---

## 1. Tag signature

NOVI fajl: `apps/seo/templatetags/hreflang.py` (DRUGI tag-modul u `apps.seo`, uz `seo_meta.py`).

```python
from django import template
from django.urls import translate_url
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.conf import settings

register = template.Library()

@register.simple_tag(takes_context=True)
def hreflang_links(context):
    ...
```

- `simple_tag(takes_context=True)` — uzima `context`, čita `request = context.get("request")`.
- Vraća `mark_safe`-ovan HTML string (već-`format_html`-escaped delovi spojeni `"\n".join(...)`), ILI prazan string `""` kad `request is None`.

---

## 2. Per-locale URL algoritam (CRUX — SM-D1)

Za SVAKI `(lang_code, _label)` u `settings.LANGUAGES` (sr, hu, en — NE hardkoduj, čitaj settings; G7):

```
lang_url = request.build_absolute_uri(translate_url(request.path, lang_code))
```

- `translate_url(request.path, lang_code)` → `resolve()` trenutni path → `reverse()` pod `override(lang_code)` → ekvivalentna URL sa zamenjenim locale prefiksom (`/sr/proizvod/x/` → `/hu/proizvod/x/`).
- `request.build_absolute_uri(...)` → apsolutizuje (scheme + host iz request-a, ograničen `ALLOWED_HOSTS`).
- **`request.path` (NE `get_full_path()`)** — inherentno param-free; `?page=2` NIKAD ne curi u href (SM-D9). NE dodaji strip logiku (YAGNI — nema šta da se strip-uje).
- **Graceful:** `translate_url` SAM hvata `Resolver404`/`NoReverseMatch` i vraća ORIGINAL url → tag NIKAD ne 500-uje. **NE dodaji try/except** (G2 — defensive boilerplate; trust Django contract).
- **prefix_default_language=True** (config/urls.py:49 — VERIFIKOVANO): sr DOBIJA `/sr/` prefiks → SVE href-ove su prefiksovane (`/sr/`, `/hu/`, `/en/`). NEMA prefix-less sr (G3).
- **⚠️ TEST-FIDELITY (TEA review-fix; NIJE production-kod zahtev):** `translate_url` interno radi `resolve(path)` koji pod i18n_patterns matchuje SAMO prefiks AKTIVNE locale. U PRODUKCIJI `LocaleMiddleware` aktivira locale iz URL prefiksa PRE render-a (npr. `/hu/..` → aktivan `hu`) → `translate_url` ispravno swap-uje prefiks. TEA testovi koriste `RequestFactory` (BEZ middleware) → `_render_tag`/`_render_full_page` SADA aktiviraju locale matching path-prefiksu (`translation.override(_active_lang_for_path(path))`) da verno mirror-uju produkciju; bez toga `resolve('/hu/..')` pod ambient sr padne → `translate_url` degradira (vrati `/hu/` za SVE jezike) → reciprocitet test bi merio degradaciju umesto stvarnog swap-a. **Dev NE menja ništa u tagu zbog ovoga** — tag i dalje samo `translate_url(request.path, lang)`; u runtime-u middleware obezbeđuje aktivnu locale.

---

## 3. 4-link x-default set (SM-D2/D3)

Emituje TAČNO 4 `<link rel="alternate" hreflang="...">`:

| # | hreflang | href |
|---|----------|------|
| 1 | `sr` | `http://host/sr/<path>/` |
| 2 | `hu` | `http://host/hu/<path>/` |
| 3 | `en` | `http://host/en/<path>/` |
| 4 | `x-default` | **== sr href** (SM-D2; sr je `LANGUAGE_CODE`) |

- 3 iz iteracije po `settings.LANGUAGES` + 1 eksplicitan x-default = 4.
- **Self-referencing (SM-D3):** SVAKA strana lista SVE 4 uključujući SVOJU aktivnu locale (NE „other languages"). Iteracija po LANGUAGES to garantuje.
- **x-default href:** izračunaj sr URL JEDNOM (`request.build_absolute_uri(translate_url(request.path, settings.LANGUAGE_CODE))`) i reuse za x-default link.
- Ako se LANGUAGES promeni → broj prati (N+1); count test broji `len(LANGUAGES)+1 == 4` za trenutne 3 jezika.

---

## 4. Kodovi (SM-D4)

Bare `sr` / `hu` / `en` / `x-default` — NE `sr-Latn`/`sr-RS`/`en-US` region/script subtag. Match `LANGUAGES` ključeve + 6-2 sitemap `alternates=True` emisiju (konzistentnost HTML ↔ sitemap).

---

## 5. Emisija / security (SM-D8)

```python
parts = []
for lang_code, _ in settings.LANGUAGES:
    lang_url = request.build_absolute_uri(translate_url(request.path, lang_code))
    parts.append(format_html('<link rel="alternate" hreflang="{}" href="{}">', lang_code, lang_url))
parts.append(format_html('<link rel="alternate" hreflang="x-default" href="{}">', default_url))
return mark_safe("\n".join(parts))
```

- SVAKI href kroz `format_html` autoescape (`&` → `&amp;`; head-injection-safe).
- `mark_safe` SAMO na join-u već-escaped delova — NIKAD `|safe` na sirovoj URL vrednosti (mirror `seo_head` `mark_safe("\n".join(parts))`).

---

## 6. request=None guard (SM-D8/G5)

```python
request = context.get("request")
if request is None:
    return ""
```

MORA biti PRVA linija (pre svakog `build_absolute_uri`/`translate_url`). Izolovan unit-render bez HTTP konteksta → prazan string, NE 500.

---

## 7. base.html block mount (SM-D5)

`templates/base.html`:

1. Dodaj `{% load hreflang %}` u vrh (uz postojeći `{% load seo_meta %}`, linija ~6).
2. Dodaj NOVI block u `<head>` **POSLE** linije 13 `{% block social_meta %}{% seo_head %}{% endblock %}`:

```django
{% block social_meta %}{% seo_head %}{% endblock %}
{% block hreflang %}{% hreflang_links %}{% endblock %}
```

- ZASEBAN block (NE unutar social_meta) → buduće strane (npr. coming-soon noindex) mogu override-ovati `{% block hreflang %}{% endblock %}` BEZ promene taga (G9).
- `{% block hreflang %}` MORA biti NOVI (verifikuj da ne postoji već; G8).
- Non-extending strane (robots.txt/sitemap.xml — bez `<head>`) NE crash-uju (ne extend-uju base; AC1).

**EXACT mount line (Dev — dodaj odmah ispod social_meta):**
```
  {% block hreflang %}{% hreflang_links %}{% endblock %}
```

---

## 8. Slug verifikacioni target (AC4, SM-D7, G1)

- `apps/core/utils.py:slugify_ascii` (Story 2.1) — STVARNO ime (NE `safe_slugify` — AC990 greška, G1). **NE kreiraj alias, NE menjaj funkciju, NE migracija.**
- VERIFIKACIONI test (TEA, dodat): `apps/core/tests/test_utils.py::test_slugify_ascii_coric_agrar_example` → `slugify_ascii('Ćorić Agrar') == 'coric-agrar'` (+ `.isascii()`).
- Dijakritici (Č/Š/Ž/Đ→c/s/z/d) + digrafovi (Dž/Lj/Nj) su VEĆ pokriveni postojećim test_utils.py testovima → 6.6 NE duplira, samo dodaje tačan AC4 literal.
- Slug = DELJENI-ASCII kroz locale (jedan slug po objektu; locale = SAMO URL prefiks /sr//hu//en/; SluggedModel slug NIJE translatable). Per-locale slug kolone = DEFER (OQ-1). **0 migracija.**

---

## 9. Files Dev creates/edits

| Path | Tip | Akcija |
|---|---|---|
| `apps/seo/templatetags/hreflang.py` | NOVO | Dev kreira `hreflang_links` tag (sekcije 1–6). |
| `templates/base.html` | EDIT | Dev dodaje `{% load hreflang %}` + `{% block hreflang %}{% hreflang_links %}{% endblock %}` (sekcija 7). |
| `apps/seo/tests/test_hreflang.py` | NOVO (TEA) | VEĆ napisan (RED). Dev NE dira. |
| `apps/core/tests/test_utils.py` | EDIT (TEA) | AC4 primer VEĆ dodat (GREEN guard). Dev NE dira. |

**0 migracija** (`makemigrations --check --dry-run` → „No changes detected"). **0 model promene. 0 novih dep-ova** (`translate_url`/`build_absolute_uri`/`format_html`/`mark_safe` su Django core). **0 novih asseta.**

**NETAKNUTO (regression):** `apps/core/utils.py` (verifikacija, NE promena); `apps/seo/templatetags/seo_meta.py` (6-1/6-3 canonical/OG); `apps/seo/sitemaps.py` (6-2); `config/urls.py` + `config/settings/base.py` (ČITA, NE menja); postojeći base.html blokovi.

---

## 10. Test → AC mapiranje (RED status)

| Test | AC | Tip |
|---|---|---|
| `test_emits_exactly_four_hreflang_links` | AC2 | count |
| `test_hreflang_codes_are_exactly_sr_hu_en_xdefault` | AC2 | codes |
| `test_no_region_or_script_subtags_in_codes` | AC2 | codes |
| `test_x_default_href_equals_sr_href` | AC2 | x-default |
| `test_detail_per_locale_prefix_same_route` | AC3 | prefix/absolute |
| `test_all_hrefs_are_absolute` | AC3 | absolute |
| `test_sr_href_is_prefixed_not_prefixless` | AC3 | prefix |
| `test_reciprocity_identical_set_from_hu_locale` | AC3 | reciprocitet |
| `test_hu_page_includes_self_hu_link` | AC3 | self-ref |
| `test_listing_path_produces_per_locale_prefixed_hrefs` | AC3 | listing |
| `test_hrefs_are_param_free_when_query_present` | AC3/SM-D9 | param-free |
| `test_hreflang_self_equals_canonical` | AC3/AC6 | canonical-eq |
| `test_hrefs_are_html_escaped_no_attribute_breakout` | AC5 | security |
| `test_ampersand_in_path_is_escaped` | AC5 | security |
| `test_request_none_returns_empty_string` | AC5 | guard |
| `test_non_resolving_path_degrades_gracefully` | AC5/G2 | graceful |
| `test_renders_on_home_path` | AC1 | integration |
| `test_renders_on_detail_path` | AC1 | integration |
| `test_renders_on_listing_path` | AC1 | integration |
| `test_full_base_page_has_exactly_four_hreflang_links` | AC1/#9 | head-count |
| `test_hreflang_does_not_break_existing_head_counts` | AC1/#9 | head-count (GREEN guard) |
| `test_hreflang_links_are_not_counted_as_canonical` | AC1/#9 | head-count |
| `apps/core/tests/test_utils.py::test_slugify_ascii_coric_agrar_example` | AC4 | slug (GREEN guard) |

**RED status (pre Dev impl) — VERIFIKOVANO TEA review-om (21 FAIL / 11 PASS na `test_hreflang.py`+`test_utils.py`+`test_head_integration.py`):** 21 hreflang testova u `test_hreflang.py` FAIL — izolovani `{% load hreflang %}` testovi padaju sa `'hreflang' is not a registered tag library`; full-base.html head-count testovi (`test_full_base_page_has_exactly_four_hreflang_links`, `test_hreflang_links_are_not_counted_as_canonical`) padaju sa `count 0 != 4` jer base.html još NEMA `{% block hreflang %}` mount. **DVA by-design GREEN guard-a prolaze ODMAH:** (1) `test_slugify_ascii_coric_agrar_example` (AC4 — slugify_ascii radi od Story 2.1); (2) `test_hreflang_does_not_break_existing_head_counts` (head-count invariant lock 1×title/1×desc/1×canonical — već važi; ostaje zelen i posle Dev block-a jer hreflang je `rel="alternate"`, ne title/desc/canonical). Postojeći `test_head_integration.py` (3 testa) OSTAJE zelen kroz ceo RED→GREEN. **TEA review-fix:** `_render_tag`/`_render_full_page` sada aktiviraju locale matching path-prefiksu (`override(_active_lang_for_path(path))`) — bez toga `test_reciprocity_identical_set_from_hu_locale` je bio NEPROLAZAN AS-WRITTEN (translate_url degradira pod ambient sr za `/hu/` path; vidi sekciju 2 TEST-FIDELITY).

**Posle Dev impl (očekivano GREEN):** sva 22 hreflang+slug testa zelena; postojeći `test_head_integration.py` (17 testova) OSTAJE zelen — njegov `_HARNESS` extends base.html i nasleđuje `{% load hreflang %}` + `{% block hreflang %}` (emituje 4 hreflang linka), ali broji `<title>`/`description`/`canonical` (NE `rel="alternate"`) → count NEPROMENJEN.
