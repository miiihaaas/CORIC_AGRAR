---
story_id: "7.5"
story-key: 7-5-sanitized-rich-text-pravne-strane-nh3
title: Interface Contract — Sanitized Rich-Text za Pravne Strane (nh3)
artifact: interface-contract
phase: RED (TEA — kanonski ugovor; Dev GREEN MORA satisfy)
created: 2026-06-07
---

# Interface Contract — Story 7.5 (Sanitized Rich-Text, nh3)

Ovo je **kanonski ugovor** koji Dev (GREEN faza) MORA da implementira tačno
kako je ovde specifikovano. TEA RED testovi (`apps/core/tests/test_legal_html.py`
+ reconcile-ovani postojeći testovi) verifikuju OVAJ ugovor. Sve tekstualne poruke
su srpski (latinica, pune dijakritike); allowlist tagovi/scheme su ASCII.

---

## 1. NOVI dep `nh3` (AC1, SM-D1)

- `uv add nh3` → ulazi u `pyproject.toml` `[project].dependencies` sa constraint-om
  `nh3>=0.2.0,<1` (API stabilan od 0.2.0; 0.1.x NEMA `url_schemes` kwarg).
- `uv.lock` se regeneriše; commit ZAJEDNO sa `pyproject.toml`.
- `nh3` je **čista Python/Rust biblioteka** — NIKAD u `INSTALLED_APPS` (G-1).
- `nh3` je **kompajliran abi3 wheel** → Docker image se MORA rebuild-ovati posle
  `uv add` (deploy radi `uv sync --frozen`); verifikuj `import nh3` UNUTAR kontejnera
  (SM-D9 / G-10).

---

## 2. `apps/core/sanitize.py:sanitize_legal_html(raw: str) -> str` (AC2, SM-D2)

```python
def sanitize_legal_html(raw: str) -> str:
    """Sanitizuj rich-text pravnog body-a kroz nh3 allowlist → bezbedan HTML string.

    Deljiv helper (forward-reuse: 8.7 blog WYSIWYG za Post.body). Čist (bez DB,
    bez side-efekata). None/prazno → "". Render-time je PRIMARNA XSS granica.
    """
```

Ponašanje (MORA):

| Ulaz | Izlaz |
|---|---|
| `None` / `""` / falsy | `""` |
| ne-`str` | coerce `str(raw)` pa clean |
| validan rich-HTML | `nh3.clean(...)` sa allowlist-om ispod |

**Modul-level konstante (eksplicitne, dokumentovane docstring/komentarom WHY):**

- `_ALLOWED_TAGS` = `{p, br, h2, h3, h4, ul, ol, li, a, strong, em, b, i,
  table, thead, tbody, tr, th, td}` (set stringova).
- `_ALLOWED_ATTRIBUTES` = `{"a": {"href", "title", "target"},
  "th": {"colspan", "rowspan"}, "td": {"colspan", "rowspan"}}` (dict tag→set).
  `rel` je **NAMERNO IZOSTAVLJEN** iz `a` atributa: nh3 0.3.5 DIŽE `ValueError`
  ako je `rel` u `attributes["a"]` ISTOVREMENO dok je `link_rel` postavljen
  ("pass link_rel=None to manage the rel attribute directly"). `link_rel=
  "noopener noreferrer"` SAM forsira/prepisuje `rel` na svaki `<a>` (uključujući
  ulazni `rel="opener"` → `noopener noreferrer`; reverse-tabnabbing neutralizovan).
  G-7 namera („rel uvek noopener noreferrer") je ispunjena kroz `link_rel`, NE
  kroz attr allowlist. Verifikovano testom `test_rel_opener_overridden_to_noopener`.
- `_ALLOWED_SCHEMES` = `{http, https, mailto}` (set).

**Poziv:**
`nh3.clean(raw, tags=_ALLOWED_TAGS, attributes=_ALLOWED_ATTRIBUTES,
url_schemes=_ALLOWED_SCHEMES, link_rel="noopener noreferrer")`.

**Garancije (verifikovane testovima):**

- DOZVOLI gornje tagove (zadržani u izlazu sa svojim tekstom).
- STRIP: `<script>`, `<style>`, sve `on*` inline handlere, nedozvoljene tagove
  (`<div>/<img>/<iframe>/<svg>/<object>/<form>/<h1>`), nedozvoljene atribute
  (`style`/`class`/`id`/`onerror`), HTML komentare.
- `href="javascript:..."` / `href="data:..."` → scheme STRIP-ovan (tag može ostati,
  href se uklanja/sanitizuje; `javascript:`/`data:` ne sme biti u izlazu).
- forsira `rel="noopener noreferrer"` na svaki `<a>` (reverse-tabnabbing
  neutralizovan; čak i `rel="opener"` na ulazu mora postati `noopener noreferrer`).
- STRIP ≠ ESCAPE: uklonjen NODE, NE pretvoren u `&lt;...&gt;`. Unutrašnji tekst
  (npr. `alert(1)`) MOŽE legitimno ostati kao goli tekst.

---

## 3. `apps/core/templatetags/legal_html.py:{{ value|legal_html }}` (AC3, SM-D3)

```python
from django import template
from django.utils.safestring import mark_safe

from apps.core.sanitize import sanitize_legal_html

register = template.Library()


@register.filter(name="legal_html")
def legal_html(value):
    return mark_safe(sanitize_legal_html(value))
```

**Garancije:**

- Vraća `SafeString` (`mark_safe`) — ali SAMO POSLE sanitizacije.
- `mark_safe` obavija ISKLJUČIVO `sanitize_legal_html(...)` izlaz, **NIKAD** sirov
  `value` (G-6). Statički guard test proverava izvor: sadrži
  `mark_safe(sanitize_legal_html` i NE sadrži `mark_safe(value`.
- `None`/prazno → prazan `SafeString` (`""`), bez crash-a.
- `{% load legal_html %}` radi u template-u.

---

## 4. Template swap — TAČNO 2 pravna template-a (AC4, SM-D4)

`templates/gdpr/cookie_policy.html`:
- dodaj `{% load legal_html %}` (pored `{% load i18n %}`)
- `{{ policy.body|linebreaks }}` → `{{ policy.body|legal_html }}`
- ažuriraj komentar (više nije plain-text `|linebreaks`; sad sanitizovan rich-HTML
  kroz nh3, mark_safe SAMO posle sanitizacije; WYSIWYG=8.7)

`templates/pages/page-detail.html`:
- dodaj `{% load legal_html %}`
- `{{ page.body|linebreaks }}` → `{{ page.body|legal_html }}`
- ažuriraj komentar (isto)

Ostatak template-a netaknut (title block, `<h1>`, „Poslednja izmena", „Važi od").
`body` ostaje `TextField` → **0 schema migracija** (AC7); seed-ovi netaknuti.

---

## 5. Render garancija (AC5)

GET `/sr/politika-kolacica/` i `/sr/politika-privatnosti/` sa rich-HTML body:
- HTTP 200; SADRŽI `<table`/`<thead`/`<tr`/`<th`/`<td`/`<ul`/`<li`/`<h2`/
  `<a href="https://...`; emitovani `<a>` ima `rel="noopener noreferrer"`.
- NE SADRŽI `<script` NITI `&lt;script&gt;` (STRIP, ne escape), `onerror=`,
  `<iframe`, `style=`, `<div`.
- `/hu/` i `/en/` → 200 sa sr-fallback (MODELTRANSLATION_FALLBACK_LANGUAGES=("sr",)).
- plain-text body renderuje se bezbedno (text node-ovi netaknuti).

**⚠️ STRIP ≠ ESCAPE — asercije:** `"<script" not in html` **I**
`"&lt;script&gt;" not in html`; **NIKAD** `"alert(1)" not in html` (goli tekst
posle strip-a je legitiman; korektna implementacija bi pala na toj asertaciji).

---

## 6. Reconciliacija (AC6, SM-D7)

5 postojećih testova (escape→strip) — vidi `apps/gdpr/tests/test_xss.py` +
`apps/pages/tests/test_7_4_static_pages.py`. NIJEDAN reconcile NE sme oslabiti XSS
garanciju (`<script>alert(` / `onerror=` / `javascript:` ODSUTNI). `|linebreaks`
\n→`<br>` semantika se gubi (G-3): plain `\n` više NE postaje `<br>`.
