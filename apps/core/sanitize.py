"""Story 7.5 — Sanitizacija rich-text pravnog `body`-a kroz nh3 allowlist.

Deljiv helper (`apps.core` — NE gdpr/pages) jer ga FORWARD-reuse koristi 8.7 blog
WYSIWYG (`Post.body`). 7.5 ga primenjuje SAMO na pravne strane
(`gdpr.CookiePolicy.body` + `pages.Page.body`); blog ostaje `|linebreaks` do 8.7.

`nh3` je Python binding za `ammonia` (Rust HTML sanitizer) — održavan, brz,
sigurni default-i; `bleach` je EOL → izbegnut (SM-D1). nh3 STRIPUJE node-ove van
allowlist-a (uklanja ceo tag), NE escape-uje ih (STRIP ≠ ESCAPE; SM-D7).

Render-time sanitizacija je PRIMARNA XSS granica (SM-D3): `legal_html` filter zove
ovaj helper na svakom renderu — NIKAD se ne veruje stored vrednosti (admin-kompromis
/ direktan DB upis / migracija mogu ubaciti nesanitizovan HTML; render ga UVEK čisti).

WHY allowlist (pravni dokument = tabela kolačića + naslovi + liste + linkovi):
- tagovi: strukturni blok (p/h2-h4/ul/ol/li/table-porodica) + inline emphasis
  (strong/em/b/i) + link (a). `<h1>` IZOSTAVLJEN — rezervisan za stranicu
  (`<h1>{{ title }}</h1>` u template-u); body koristi h2-h4 (G-8).
  `<img>/<iframe>/<form>/<div>/<svg>/<object>` STRIP — XSS/embed/layout rizik.
- atributi: `a → href/title/rel/target` (link sa tooltip-om/novim tab-om);
  `rel` EKSPLICITNO dozvoljen radi konzistentnosti sa `link_rel` forsiranjem (G-7);
  `th/td → colspan/rowspan` (tabela kolačića). `style/class/id` STRIP.
- url_schemes: `http/https/mailto` — `javascript:`/`data:` STRIP (XSS).
- link_rel="noopener noreferrer": forsiran na svaki `<a>` → reverse-tabnabbing
  neutralizovan; `target="_blank"` postaje bezbedan (G-7/G-11).
"""

from __future__ import annotations

import nh3

# Dozvoljeni tagovi (set stringova; nh3 API). Pravni v1: struktura + emphasis + link.
_ALLOWED_TAGS: set[str] = {
    "p",
    "br",
    "h2",
    "h3",
    "h4",
    "ul",
    "ol",
    "li",
    "a",
    "strong",
    "em",
    "b",
    "i",
    "table",
    "thead",
    "tbody",
    "tr",
    "th",
    "td",
}

# Dozvoljeni atributi (dict tag→set); th/td span.
#
# ⚠️ G-11 (verifikovano na instaliranoj nh3 0.3.5): `rel` NE SME biti u `a`
# atributima dok je `link_rel` postavljen — nh3 0.3.x DIŽE `ValueError`
# ("rel attribute is not allowed for tag a when link_rel is set; pass
# link_rel=None to manage the rel attribute directly"). `link_rel` SAM upravlja
# `rel`-om: forsira `rel="noopener noreferrer"` na svaki <a> i PREPISUJE bilo
# koji ulazni `rel` (npr. `rel="opener"` → `noopener noreferrer`; reverse-
# tabnabbing neutralizovan). Zato `rel` IZOSTAVLJEN iz allowlist-a (G-7 namera —
# „rel uvek noopener noreferrer" — ispunjena kroz link_rel, NE kroz attr allow).
_ALLOWED_ATTRIBUTES: dict[str, set[str]] = {
    "a": {"href", "title", "target"},
    "th": {"colspan", "rowspan"},
    "td": {"colspan", "rowspan"},
}

# Dozvoljene URL scheme — javascript:/data: STRIP (XSS).
# NAPOMENA (accepted LOW): protokol-relativni href (`//evil.com`) PREŽIVLJAVA —
# po dizajnu (admin sme da upiše eksterne https linkove). To je navigacija/phishing
# rizik, NE XSS (nema izvršenja skripte). Svestan trade-off, ne bug.
_ALLOWED_SCHEMES: set[str] = {"http", "https", "mailto"}


def sanitize_legal_html(raw: str) -> str:
    """Sanitizuj rich-text pravnog body-a kroz nh3 allowlist → bezbedan HTML string.

    Deljiv helper (forward-reuse: 8.7 blog WYSIWYG za Post.body). Čist (bez DB,
    bez side-efekata). None/prazno → "". Render-time je PRIMARNA XSS granica.
    """
    if not raw:
        return ""
    if not isinstance(raw, str):
        raw = str(raw)
    return nh3.clean(
        raw,
        tags=_ALLOWED_TAGS,
        attributes=_ALLOWED_ATTRIBUTES,
        url_schemes=_ALLOWED_SCHEMES,
        link_rel="noopener noreferrer",
    )
