"""Story 6.6 — {% hreflang_links %} HTML hreflang tagovi (TEA RED phase).

PRVI hreflang-HTML deliverable Epic 6 (ZATVARA epic). NOVI
`apps/seo/templatetags/hreflang.py` sa `{% hreflang_links %}` simple_tag(takes_context=True)
koji za TRENUTNI `request.path` emituje TAČNO 4 `<link rel="alternate" hreflang="...">`
taga: sr, hu, en, x-default (x-default href == sr href). URL generacija kroz
`translate_url(request.path, lang)` + `request.build_absolute_uri(...)` (SM-D1);
prefix_default_language=True → svi href-ovi su `/sr|hu|en/`-prefiksovani (SM-D1/G3).

⚠️ RED razlog: `{% load hreflang %}` → TemplateSyntaxError ("'hreflang' is not a
registered tag library") dok Dev ne kreira `apps/seo/templatetags/hreflang.py`. Svaki
`{% load hreflang %}` je UNUTAR test body-ja / helper-a (lazy) → čist per-test FAIL,
NE collection-abort. Count/equality/param-free asercije su sekundarni RED guard-ovi.

Head-count ownership (Testing #9, SM-D5/C1): 6-6 OWNS verifikaciju da dodavanje 4
globalna `<link rel="alternate" hreflang>` u base.html NE lomi postojeće 6-1/6-3
head-count invariante (1 <title> / 1 <meta description> / 1 <link rel=canonical>).
Reconcile sa test_head_integration.py: njegov _HARNESS extends base.html ali NE
override-uje {% block hreflang %} → posle Dev edita on TAKOĐE emituje 4 hreflang
linka; ali ti testovi broje <title>/description/canonical (NE rel="alternate") →
ostaju zeleni. Ovde dodajemo EKSPLICITAN hreflang-count lock na full base.html render
+ re-lock 1×title/1×description/1×canonical na ISTOM render-u.

Refs:
- 6-6-...-locale-aware-slug-ovi.md AC1-AC6 + Testing #1..#9 + SM-D1..D9 + G1..G9
- apps/seo/templatetags/seo_meta.py (6-3 format_html/mark_safe/request-guard pattern)
- apps/seo/tests/test_sitemap_hreflang.py (6-2 bare sr/hu/en kodovi — match)
- config/urls.py:49 prefix_default_language=True / config/settings/base.py:148 LANGUAGES
"""

from __future__ import annotations

import re

import pytest

pytestmark = pytest.mark.django_db

# Bare kodovi — match LANGUAGES (base.py:148) + 6-2 sitemap alternates (SM-D4).
EXPECTED_HREFLANGS = {"sr", "hu", "en", "x-default"}

# regex za parsiranje hreflang link tagova (NO BeautifulSoup — project-context).
# Hvata SAMO <link rel="alternate" hreflang="X" ...> (NE canonical, NE OG).
_HREFLANG_LINK_RE = re.compile(
    r'<link\b[^>]*\brel="alternate"[^>]*\bhreflang="([^"]+)"[^>]*\bhref="([^"]*)"[^>]*>',
    re.IGNORECASE,
)


def _parse_hreflangs(html: str) -> dict[str, str]:
    """Vrati {hreflang_code: href} iz svih <link rel=alternate hreflang> tagova."""
    return {m.group(1): m.group(2) for m in _HREFLANG_LINK_RE.finditer(html)}


def _count_hreflang_links(html: str) -> int:
    return len(_HREFLANG_LINK_RE.findall(html))


def _active_lang_for_path(path: str) -> str | None:
    """Locale koju bi LocaleMiddleware aktivirao za dati URL prefiks (/hu/.. → hu).

    KRITIČNO (production-fidelity): `translate_url` interno radi `resolve(path)` koji
    pod i18n_patterns matchuje SAMO prefiks AKTIVNE locale. U produkciji LocaleMiddleware
    aktivira locale iz URL prefiksa PRE render-a; RequestFactory NEMA middleware → moramo
    sami aktivirati matching locale, inače `resolve('/hu/..')` pod ambient sr padne na
    Resolver404 → translate_url degradira (vrati original /hu/ za SVE jezike) → testovi
    bi merili degradaciju umesto stvarnog prefix-swap-a. Vraća kod iz LANGUAGES ili None.
    """
    from django.conf import settings

    segments = path.lstrip("/").split("/", 1)
    prefix = segments[0] if segments else ""
    codes = {code for code, _ in settings.LANGUAGES}
    return prefix if prefix in codes else None


def _render_tag(path: str = "/sr/", *, with_request: bool = True) -> str:
    """Render IZOLOVAN {% hreflang_links %} sa request iz RequestFactory(path).

    SERVER_NAME=testserver → build_absolute_uri daje http://testserver/... apsolutni
    host. with_request=False → context BEZ request (request=None guard test).
    Aktivira locale matching path-prefiksu (mirror LocaleMiddleware; vidi
    _active_lang_for_path) tako da translate_url stvarno swap-uje prefiks.
    """
    from django.template import Context, Template
    from django.test import RequestFactory
    from django.utils.translation import override

    template = Template("{% load hreflang %}{% hreflang_links %}")
    if with_request:
        request = RequestFactory().get(path)
        ctx = Context({"request": request})
    else:
        ctx = Context({})
    with override(_active_lang_for_path(path)):
        return template.render(ctx)


# Full base.html render harness za head-count ownership (#9). Mirror
# test_head_integration.py _HARNESS ali dodaje {% load hreflang %} + seo_head obj
# (canonical) → omogućava hreflang-self == canonical lock i head-count re-lock na
# JEDNOM full-page render-u.
_FULL_HARNESS = (
    "{% extends 'base.html' %}\n"
    "{% load seo_meta %}\n"
    "{% block title %}{% seo_title obj %}{% endblock %}\n"
    "{% block meta_description %}{% seo_meta_description obj %}{% endblock %}\n"
    "{% block social_meta %}{% seo_head obj %}{% endblock %}\n"
)


def _render_full_page(obj, path: str = "/sr/"):
    """Render full base.html stranu (obj za seo_head canonical) na datom path-u.

    Aktivira locale matching path-prefiksu (mirror LocaleMiddleware) — i da bi
    translate_url u hreflang tag-u swap-ovao prefiks I da bi seo_head canonical
    (obj.get_absolute_url() reverse) bio pod istom locale → hreflang-self==canonical.
    """
    from django.template import Context, Template
    from django.test import RequestFactory
    from django.utils.translation import override

    request = RequestFactory().get(path)
    with override(_active_lang_for_path(path)):
        return Template(_FULL_HARNESS).render(Context({"obj": obj, "request": request}))


# =============================================================================
# AC2 — Count lock: TAČNO 4 hreflang linka (Testing #1)
# =============================================================================


# AC-2: tačno 4 <link rel=alternate hreflang> (sr/hu/en/x-default; NE 3, NE 6)
def test_emits_exactly_four_hreflang_links():
    html = _render_tag("/sr/")
    count = _count_hreflang_links(html)
    assert count == 4, (
        f"{{% hreflang_links %}} MORA emitovati TAČNO 4 <link rel=\"alternate\" "
        f"hreflang> (sr/hu/en/x-default; SM-D2/D3/D4); pronađeno {count}."
    )


# AC-2: hreflang vrednosti su TAČNO {sr, hu, en, x-default} (bare kodovi — SM-D4)
def test_hreflang_codes_are_exactly_sr_hu_en_xdefault():
    html = _render_tag("/sr/")
    found = set(_parse_hreflangs(html).keys())
    assert found == EXPECTED_HREFLANGS, (
        f"hreflang kodovi MORAJU biti TAČNO {EXPECTED_HREFLANGS} (bare sr/hu/en + "
        f"x-default — NE sr-Latn/region subtag; SM-D4); dobijeno: {found}."
    )


# AC-2: nema region/script subtag-a (sr-Latn / sr-RS / en-US) — match 6-2 sitemap
def test_no_region_or_script_subtags_in_codes():
    html = _render_tag("/sr/")
    codes = set(_parse_hreflangs(html).keys())
    for code in codes:
        if code == "x-default":
            continue
        assert "-" not in code, (
            f"hreflang kod '{code}' NE SME imati region/script subtag (bare sr/hu/en; "
            "SM-D4 — desinhronizovalo bi sa 6-2 sitemap)."
        )


# =============================================================================
# AC2/AC3 — x-default == sr (Testing #1/#2, SM-D2)
# =============================================================================


# AC-2: x-default href je IDENTIČAN sr href-u (SM-D2 — sr je LANGUAGE_CODE/default)
def test_x_default_href_equals_sr_href():
    links = _parse_hreflangs(_render_tag("/sr/"))
    assert "sr" in links and "x-default" in links, (
        "MORAJU postojati i 'sr' i 'x-default' linkovi (SM-D2/D3)."
    )
    assert links["x-default"] == links["sr"], (
        f"x-default href MORA biti IDENTIČAN sr href-u (SM-D2); "
        f"x-default={links['x-default']!r} sr={links['sr']!r}."
    )


# =============================================================================
# AC3 — Per-locale prefiks + apsolutni href + ista ruta (Testing #2 — DETAIL)
# =============================================================================


# AC-3: na /sr/proizvod/<slug>/ — sr/hu/en href-ovi razlikuju se SAMO po prefiksu
def test_detail_per_locale_prefix_same_route(product):
    path = product.get_absolute_url()  # /sr/proizvod/<slug>/
    links = _parse_hreflangs(_render_tag(path))

    slug = product.slug
    assert links.get("sr") == f"http://testserver/sr/proizvod/{slug}/", (
        f"sr href MORA biti apsolutan + /sr/ prefiks; dobijeno: {links.get('sr')!r}."
    )
    assert links.get("hu") == f"http://testserver/hu/proizvod/{slug}/", (
        f"hu href MORA biti apsolutan + /hu/ prefiks ISTA ruta; dobijeno: {links.get('hu')!r}."
    )
    assert links.get("en") == f"http://testserver/en/proizvod/{slug}/", (
        f"en href MORA biti apsolutan + /en/ prefiks ISTA ruta; dobijeno: {links.get('en')!r}."
    )
    assert links.get("x-default") == links.get("sr"), (
        "x-default == sr na detail strani (SM-D2)."
    )


# AC-3: svaki href je APSOLUTAN (scheme + host kroz build_absolute_uri)
def test_all_hrefs_are_absolute(product):
    links = _parse_hreflangs(_render_tag(product.get_absolute_url()))
    assert links, "MORA postojati bar jedan hreflang link (AC3)."
    for code, href in links.items():
        assert href.startswith("http://testserver/"), (
            f"hreflang={code} href MORA biti APSOLUTAN (http://testserver/...; "
            f"build_absolute_uri — SM-D1); dobijeno: {href!r}."
        )


# AC-3: sr je PREFIKSOVAN (/sr/), NE prefix-less (prefix_default_language=True; G3)
def test_sr_href_is_prefixed_not_prefixless(product):
    links = _parse_hreflangs(_render_tag(product.get_absolute_url()))
    assert "/sr/" in links.get("sr", ""), (
        f"sr href MORA imati /sr/ prefiks (prefix_default_language=True — NEMA "
        f"prefix-less sr; G3/SM-D1); dobijeno: {links.get('sr')!r}."
    )


# =============================================================================
# AC3 — Reciprocitet / self-referencing (Testing #3, SM-D3)
# =============================================================================


# AC-3: GET /hu/proizvod/<slug>/ daje IDENTIČAN set 4 linka kao /sr/... (reciprocitet)
def test_reciprocity_identical_set_from_hu_locale(product):
    sr_path = product.get_absolute_url()  # /sr/proizvod/<slug>/
    hu_path = sr_path.replace("/sr/", "/hu/", 1)

    from_sr = _parse_hreflangs(_render_tag(sr_path))
    from_hu = _parse_hreflangs(_render_tag(hu_path))

    assert from_sr == from_hu, (
        "Set hreflang linkova MORA biti IDENTIČAN sa /sr/ i /hu/ ulaza "
        "(self-referencing — hreflang nezavisan od aktivne locale; SM-D3); "
        f"sr={from_sr!r} hu={from_hu!r}."
    )


# AC-3: hu strana TAKOĐE emituje hu link (self-reference — lista SVE verzije)
def test_hu_page_includes_self_hu_link(product):
    hu_path = product.get_absolute_url().replace("/sr/", "/hu/", 1)
    links = _parse_hreflangs(_render_tag(hu_path))
    assert "hu" in links, (
        "hu strana MORA listati SVOJ hu link (self-referencing reciprocitet; SM-D3)."
    )
    assert "/hu/" in links["hu"], "Self hu link MORA imati /hu/ prefiks."


# =============================================================================
# AC3 — LISTING + param-free (Testing #4, SM-D9 — Adversarial)
# =============================================================================


# AC-3: listing ruta (/sr/traktori/) — per-locale prefiksovani href-ovi i na listingu
def test_listing_path_produces_per_locale_prefixed_hrefs():
    links = _parse_hreflangs(_render_tag("/sr/traktori/"))
    assert links.get("sr") == "http://testserver/sr/traktori/"
    assert links.get("hu") == "http://testserver/hu/traktori/"
    assert links.get("en") == "http://testserver/en/traktori/", (
        "translate_url MORA proizvesti per-locale prefiksovane href-ove i na LISTING "
        f"ruti (ne samo detail; Testing #4); dobijeno: {links!r}."
    )


# AC-3 / SM-D9: ?page=2 NE curi u nijedan hreflang href (param-free — request.path)
def test_hrefs_are_param_free_when_query_present():
    # RequestFactory().get(path, {"page": "2"}) → request.path je /sr/traktori/ (param-free),
    # request.GET ima page=2. Tag gradi iz request.path → href-ovi NEMAJU query.
    from django.template import Context, Template
    from django.test import RequestFactory

    request = RequestFactory().get("/sr/traktori/", {"page": "2"})
    out = Template("{% load hreflang %}{% hreflang_links %}").render(
        Context({"request": request})
    )
    links = _parse_hreflangs(out)
    assert links, "MORA postojati hreflang link (AC3)."
    for code, href in links.items():
        assert "?" not in href and "page=2" not in href, (
            f"hreflang={code} href NE SME sadržati query string (?page=2) — gradi se iz "
            f"request.path koji je INHERENTNO param-free (SM-D9; NE get_full_path); "
            f"dobijeno: {href!r}."
        )


# =============================================================================
# AC3/AC6 — hreflang-self == 6-3 canonical (Testing #5 — Adversarial lock)
# =============================================================================


# AC-3 / AC-6: href hreflang AKTIVNOG jezika == href <link rel="canonical"> (6-3)
def test_hreflang_self_equals_canonical(product):
    # override("sr") (context manager) — deterministički aktivira sr za OBA reverse-a
    # (path=get_absolute_url() arg + seo_head canonical), pa VRAĆA prethodno locale
    # stanje na izlazu (NE leak-uje activate u naredne testove; isolation/flaky-fix).
    from django.utils.translation import override

    with override("sr"):
        path = product.get_absolute_url()  # /sr/proizvod/<slug>/ pod override(sr)
        html = _render_full_page(product, path=path)

    # canonical href (6-3 seo_head)
    canon = re.search(r'<link\b[^>]*\brel="canonical"[^>]*\bhref="([^"]*)"', html, re.IGNORECASE)
    assert canon is not None, (
        "Full-page render MORA imati <link rel=\"canonical\"> (6-3 seo_head)."
    )
    canonical_href = canon.group(1)

    links = _parse_hreflangs(html)
    assert links.get("sr") == canonical_href, (
        "hreflang AKTIVNOG (sr) jezika MORA biti JEDNAK canonical href-u (oba iz "
        "build_absolute_uri obrasca, oba param-free; Testing #5/AC6); "
        f"hreflang-sr={links.get('sr')!r} canonical={canonical_href!r}."
    )


# =============================================================================
# AC5 — Security: autoescape (Testing #6, SM-D8)
# =============================================================================


# AC-5: href-ovi emitovani kroz format_html autoescape — nema sirovog probijanja
def test_hrefs_are_html_escaped_no_attribute_breakout(product):
    html = _render_tag(product.get_absolute_url())
    # Nijedan hreflang link ne sme imati prelomljen atribut (nezatvoren <link>,
    # sirov < unutar href). Svi 4 linka moraju biti dobro-formirani <link ...>.
    links = _parse_hreflangs(html)
    assert len(links) == 4, (
        "Svi 4 hreflang linka MORAJU se parsirati kao dobro-formirani <link> tagovi "
        f"(format_html autoescape — atribut se ne probija; SM-D8); dobijeno {len(links)}."
    )
    for code, href in links.items():
        assert "<" not in href and ">" not in href, (
            f"hreflang={code} href NE SME sadržati sirov <,> (autoescape; SM-D8); {href!r}."
        )


# AC-5/SM-D8: izlaz je mark_safe SAMO na već-format_html-escaped delovima — `&` → `&amp;`
def test_ampersand_in_path_is_escaped():
    # Path sa & — translate_url može vratiti original (ne-rutiran) path; bitno je da
    # `&` u href-u NIKAD ne sme izaći neeskejpovan (format_html autoescape; SM-D8).
    html = _render_tag("/sr/a&b/")
    # Ako neeskejpovan `&` (ne praćen entitetom) postoji — security fail.
    raw_amp = re.findall(r"&(?!amp;|lt;|gt;|quot;|#)", html)
    assert not raw_amp, (
        "Neeskejpovan '&' u hreflang href-u — MORA proći kroz format_html autoescape "
        f"(&→&amp;; SM-D8); pronađeno {len(raw_amp)} sirovih ampersand-a."
    )


# =============================================================================
# AC5 — Graceful guard-ovi (Testing #7/#8, SM-D1)
# =============================================================================


# AC-5: request is None → PRAZAN string (NE 500; build_absolute_uri zahteva request; G5)
def test_request_none_returns_empty_string():
    out = _render_tag(with_request=False)
    assert out.strip() == "", (
        "Kad request NIJE u contextu → {% hreflang_links %} MORA vratiti PRAZAN string "
        "(NE 500; build_absolute_uri zahteva request — G5/SM-D8)."
    )
    assert _count_hreflang_links(out) == 0, (
        "request=None → 0 hreflang linkova (graceful)."
    )


# AC-5/G2: ne-rutiran path → translate_url GRACEFULNO vraća original → 4 linka, NE 500
def test_non_resolving_path_degrades_gracefully():
    out = _render_tag("/sr/nepostojeci-path-12345/")
    # NE 500 — translate_url sam hvata Resolver404/NoReverseMatch i vraća original.
    count = _count_hreflang_links(out)
    assert count == 4, (
        "Ne-rutiran path → translate_url vraća original path → i dalje 4 linka "
        f"(degradacija, NE 500; G2/SM-D1); pronađeno {count}."
    )


# =============================================================================
# AC1 — Tag renderuje na home/listing/detail (Testing #1)
# =============================================================================


# AC-1: home (/sr/) renderuje 4 hreflang linka
def test_renders_on_home_path():
    assert _count_hreflang_links(_render_tag("/sr/")) == 4


# AC-1: detail (/sr/proizvod/<slug>/) renderuje 4 hreflang linka
def test_renders_on_detail_path(product):
    assert _count_hreflang_links(_render_tag(product.get_absolute_url())) == 4


# AC-1: listing (/sr/traktori/) renderuje 4 hreflang linka
def test_renders_on_listing_path():
    assert _count_hreflang_links(_render_tag("/sr/traktori/")) == 4


# =============================================================================
# AC1 — Head-count ownership (#9, SM-D5/C1) — full base.html render
# =============================================================================


# AC-1 (#9): full base.html strana ima TAČNO 4 hreflang linka (globalni mount lock)
def test_full_base_page_has_exactly_four_hreflang_links(product):
    html = _render_full_page(product, path=product.get_absolute_url())
    count = _count_hreflang_links(html)
    assert count == 4, (
        f"Full base.html strana (extends base) MORA imati TAČNO 4 hreflang linka "
        f"(globalni {{% block hreflang %}} mount; SM-D5/G6); pronađeno {count}."
    )


# AC-1 (#9): dodavanje hreflang NE duplira/lomi 6-1/6-3 head-count invariante.
# Na ISTOM full-page render-u: 1 <title> + 1 <meta description> + 1 canonical OSTAJU.
def test_hreflang_does_not_break_existing_head_counts(product):
    from apps.seo.models import SeoMeta

    SeoMeta.objects.create(
        content_object=product,
        meta_title_sr="SEO naslov head",
        meta_description_sr="SEO opis head",
    )
    html = _render_full_page(product, path=product.get_absolute_url())

    titles = re.findall(r"<title[ >]", html, re.IGNORECASE)
    assert len(titles) == 1, (
        f"Dodavanje hreflang NE SME duplirati <title> — MORA ostati TAČNO 1 "
        f"(6-1/6-3 invarijanta; SM-A/SM-B); pronađeno {len(titles)}."
    )
    descs = re.findall(r'<meta\s+name="description"', html, re.IGNORECASE)
    assert len(descs) == 1, (
        f"<meta name=\"description\"> MORA ostati TAČNO 1 posle hreflang dodavanja; "
        f"pronađeno {len(descs)}."
    )
    canonicals = re.findall(r'rel="canonical"', html, re.IGNORECASE)
    assert len(canonicals) == 1, (
        f"<link rel=\"canonical\"> MORA ostati TAČNO 1 (hreflang ga NE duplira; "
        f"komplementaran NE duplikat — SM-D6); pronađeno {len(canonicals)}."
    )


# AC-1 (#9): hreflang linkovi se NE broje kao canonical (regex izolacija — disjoint)
def test_hreflang_links_are_not_counted_as_canonical(product):
    html = _render_full_page(product, path=product.get_absolute_url())
    # rel="alternate" i rel="canonical" su disjunktni skupovi.
    alternates = re.findall(r'rel="alternate"', html, re.IGNORECASE)
    canonicals = re.findall(r'rel="canonical"', html, re.IGNORECASE)
    assert len(alternates) == 4, (
        f"MORA biti 4 rel=\"alternate\" (hreflang); pronađeno {len(alternates)}."
    )
    assert len(canonicals) == 1, (
        f"rel=\"alternate\" hreflang NE SME povećati canonical count; pronađeno "
        f"{len(canonicals)} canonical-a."
    )
