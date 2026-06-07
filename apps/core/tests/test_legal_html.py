"""Story 7.5 — Sanitized Rich-Text za pravne strane (nh3) — TEA RED phase.

XSS-KRITIČNA sanitizacija. Pokriva ## Testing listu iz story-je:
- sanitizer `apps.core.sanitize.sanitize_legal_html` (allowlist + STRIP-ne-ESCAPE)
- filter `{{ value|legal_html }}` (mark_safe SAMO posle sanitizacije)
- render integracija (gdpr cookie + pages privacy strane; per-locale)
- dep + 0-migration smoke

⚠️ COLLECTION-SAFETY (G-9): `nh3` JOŠ NIJE instaliran i `apps/core/sanitize.py` /
`apps/core/templatetags/legal_html.py` JOŠ NE postoje (RED faza). SVI importi
(`sanitize_legal_html`, filter, `nh3`) su UNUTAR test funkcija → missing dep/modul
daje per-test FAIL (ModuleNotFoundError/ImportError), NE collection-abort cele suite.
NIJEDAN import na modul-nivou ne sme dirati nh3/sanitize/legal_html.

⚠️ STRIP ≠ ESCAPE (SM-D7, AC5 — KRITIČNO za asercije): nh3 UKLANJA `<script>`/`<img>`
NODE (ne pretvara u `&lt;...&gt;`), ali MOŽE zadržati unutrašnji tekst (`alert(1)`
kao goli tekst). Zato asercija MORA biti `"<script" not in html` I
`"&lt;script&gt;" not in html`; NIKAD `"alert(1)" not in html` (korektna
implementacija bi pala na toj asertaciji — vidi STRIP-vs-ESCAPE tabelu u 7-5 story).

Refs:
- 7-5-sanitized-rich-text-pravne-strane-nh3.md AC1-AC8 + SM-D1..D9 + G-1..G-11 + Testing
- 7-5-interface-contract.md (kanonski ugovor — Dev GREEN MORA satisfy)
"""

from __future__ import annotations

import pytest

# Render-integracija putanje (i18n_patterns; slug ASCII).
COOKIE_PATH_SR = "/sr/politika-kolacica/"
COOKIE_PATH_HU = "/hu/politika-kolacica/"
COOKIE_PATH_EN = "/en/politika-kolacica/"
PRIVACY_PATH_SR = "/sr/politika-privatnosti/"
PRIVACY_PATH_HU = "/hu/politika-privatnosti/"
PRIVACY_PATH_EN = "/en/politika-privatnosti/"

# Reprezentativan rich-HTML body sa tabelom kolačića + linkom + XSS payload-om.
RICH_BODY = (
    "<h2>Kolačići</h2>"
    "<table><thead><tr><th>Naziv</th><th>Svrha</th></tr></thead>"
    "<tbody><tr><td>_ga</td><td>Analitika</td></tr></tbody></table>"
    "<ul><li>stavka</li></ul>"
    '<p>Vidi <a href="https://policies.google.com/privacy">GA4 politiku</a>.</p>'
    "<script>alert(1)</script>"
)


def _sanitize(raw):
    """Lazy import — RED: nh3 nije instaliran + sanitize.py ne postoji."""
    from apps.core.sanitize import sanitize_legal_html

    return sanitize_legal_html(raw)


def _legal_html(value):
    """Lazy import filtera — RED: legal_html.py ne postoji."""
    from apps.core.templatetags.legal_html import legal_html

    return legal_html(value)


def _body_fragment(html, css_class):
    """Izvuci SAMO sanitizovan body region iz pune strane.

    ⚠️ KRITIČNO (zašto NE asertovati protiv CELE strane): base.html chrome
    legitimno renderuje `<script src=...>` (htmx/bootstrap/gdpr-banner — 9 tagova),
    `<img>` (header/footer logo) i `<div>` (layout). Negativna asercija
    `"<script" not in html` nad CELOM stranom je UNSATISFIABLE — korektan GREEN
    render bi je oborio (chrome ima script/img/div). Zato XSS strip-asercije
    targetiraju SAMO body `<div class="...__body">...</div>` region (tu živi
    sanitizovan `body`), gde `<script`/`<img`/`<div` NE smeju da se pojave.
    """
    marker = f'class="{css_class}"'
    start = html.find(marker)
    assert start != -1, f"Body region {css_class!r} MORA postojati u renderu (AC5)."
    # Od markera do kraja <article> (body je poslednji blok u <article>).
    end = html.find("</article>", start)
    return html[start : end if end != -1 else len(html)]


# ─────────────────────────────────────────────────────────────────────────────
# Dep smoke (AC1)
# ─────────────────────────────────────────────────────────────────────────────


# AC1: nh3 importabilan (smoke — RED dok `uv add nh3` ne odradi Dev/orkestrator)
def test_nh3_importable():
    try:
        import nh3  # noqa: F401
    except ImportError as exc:  # pragma: no cover - RED dok dep ne uđe
        pytest.fail(f"`nh3` MORA biti instaliran (`uv add nh3`; AC1/SM-D1) — {exc!r}.")


# ─────────────────────────────────────────────────────────────────────────────
# Sanitizer — allowlist (AC2) — čist, bez DB
# ─────────────────────────────────────────────────────────────────────────────


# AC2: svi dozvoljeni tagovi ZADRŽANI u izlazu
def test_allowed_tags_kept():
    src = (
        "<p>p</p><h2>h2</h2><h3>h3</h3><h4>h4</h4>"
        "<ul><li>li</li></ul><ol><li>oli</li></ol>"
        "<strong>s</strong><em>e</em><b>b</b><i>i</i>"
        '<a href="https://x.test">a</a>'
        "<table><thead><tr><th>th</th></tr></thead>"
        "<tbody><tr><td>td</td></tr></tbody></table>"
    )
    out = _sanitize(src)
    for tag in (
        "<p>", "<h2>", "<h3>", "<h4>", "<ul>", "<ol>", "<li>",
        "<strong>", "<em>", "<b>", "<i>", "<a ",
        "<table>", "<thead>", "<tbody>", "<tr>", "<th>", "<td>",
    ):
        assert tag in out, f"Dozvoljen tag {tag!r} MORA biti zadržan (AC2), izlaz: {out!r}."


# AC2: <script> STRIP (node uklonjen, NE escape)
def test_script_stripped():
    out = _sanitize("<script>alert(1)</script>")
    assert "<script" not in out, "<script> MORA biti STRIP-ovan (AC2/SM-D7)."
    assert "&lt;script&gt;" not in out, (
        "nh3 STRIPUJE node (NE escape-uje) — `&lt;script&gt;` NE SME postojati (SM-D7)."
    )


# AC2: <style> STRIP
def test_style_tag_stripped():
    out = _sanitize("<style>body{color:red}</style><p>x</p>")
    assert "<style" not in out and "&lt;style&gt;" not in out, (
        "<style> MORA biti STRIP-ovan (AC2)."
    )


# AC2: on* inline handlere STRIP (na dozvoljenom tagu atribut nestaje; van allowlist-a ceo tag)
def test_on_handlers_stripped():
    out_a = _sanitize('<a href="https://x.test" onclick="x()">link</a>')
    assert "onclick" not in out_a, "`onclick` na <a> MORA biti STRIP-ovan (AC2)."
    out_img = _sanitize('<img src="x" onerror="alert(1)">')
    assert "onerror" not in out_img and "<img" not in out_img, (
        "<img onerror> ceo tag (van allowlist-a) MORA biti STRIP-ovan (AC2)."
    )


# AC2: href="javascript:..." → scheme STRIP (NE `javascript:` u izlazu)
def test_javascript_scheme_stripped():
    out = _sanitize('<a href="javascript:alert(1)">x</a>')
    assert "javascript:" not in out, (
        "`javascript:` scheme MORA biti STRIP-ovan (url_schemes={http,https,mailto}; AC2)."
    )


# AC2: href="data:..." → scheme STRIP
def test_data_scheme_stripped():
    out = _sanitize('<a href="data:text/html,<script>alert(1)</script>">x</a>')
    assert "data:text/html" not in out, "`data:` scheme MORA biti STRIP-ovan (AC2)."


# AC2: nedozvoljeni tagovi STRIP (iframe/object/form/div/h1)
def test_disallowed_tags_stripped():
    src = (
        "<iframe src='x'></iframe><object data='x'></object>"
        "<form action='x'></form><div>d</div><h1>h1</h1>"
    )
    out = _sanitize(src)
    for tag in ("<iframe", "<object", "<form", "<div", "<h1"):
        assert tag not in out, f"Nedozvoljen tag {tag!r} MORA biti STRIP-ovan (AC2/G-8)."


# AC2: nedozvoljeni atributi (style/class/id) na dozvoljenom tagu STRIP
def test_disallowed_attributes_stripped():
    out = _sanitize('<p style="color:red" class="x" id="y">tekst</p>')
    assert "<p>" in out, "Dozvoljen <p> MORA ostati (AC2)."
    assert "style=" not in out and 'class="x"' not in out and 'id="y"' not in out, (
        "style/class/id na <p> MORA biti STRIP-ovan (AC2)."
    )


# AC2: <a> zadržava dozvoljene atribute href/title/target (rel se forsira posebno)
def test_a_allowed_attributes_kept():
    out = _sanitize('<a href="https://x.test" title="t" target="_blank">x</a>')
    assert 'href="https://x.test"' in out, "<a href> MORA biti zadržan (AC2)."
    assert 'title="t"' in out, "<a title> MORA biti zadržan (AC2)."
    assert 'target="_blank"' in out, "<a target> MORA biti zadržan (AC2)."


# AC2: th/td zadržavaju colspan/rowspan
def test_th_td_colspan_rowspan_kept():
    out = _sanitize(
        "<table><tbody><tr>"
        '<th colspan="2">h</th><td rowspan="3">d</td>'
        "</tr></tbody></table>"
    )
    assert 'colspan="2"' in out, "th colspan MORA biti zadržan (AC2)."
    assert 'rowspan="3"' in out, "td rowspan MORA biti zadržan (AC2)."


# AC2: link_rel forsiran — svaki <a> dobija rel="noopener noreferrer"
def test_link_rel_forced():
    out = _sanitize('<a href="https://x.test">x</a>')
    assert 'rel="noopener noreferrer"' in out, (
        'link_rel="noopener noreferrer" MORA biti forsiran na svaki <a> (AC2/G-7).'
    )


# AC2 NEGATIVAN (REQUIRED — reverse-tabnabbing; G-11): rel="opener" → forsiran noopener
def test_rel_opener_overridden_to_noopener():
    out = _sanitize('<a href="https://x.test" target="_blank" rel="opener">x</a>')
    assert 'rel="noopener noreferrer"' in out, (
        'Ulaz rel="opener" MORA biti PREPISAN na rel="noopener noreferrer" '
        "(reverse-tabnabbing neutralizovan; G-11/AC2)."
    )
    assert 'rel="opener"' not in out, (
        'rel="opener" NE SME ostati u izlazu (dokazuje da je tabnabbing neutralizovan, '
        "NE samo da neki rel postoji; G-11)."
    )


# AC2: None/prazno → ""
def test_none_returns_empty():
    assert _sanitize(None) == "", "sanitize_legal_html(None) MORA biti '' (AC2)."


# AC2 (coerce grana — sanitize.py `raw = str(raw)`): ne-str truthy ulaz → coerce-ovan, ne raise
def test_non_str_input_coerced():
    out = _sanitize(42)
    assert isinstance(out, str), (
        "sanitize_legal_html(42) MORA vratiti str (coerce grana `raw = str(raw)`; AC2)."
    )
    assert "42" in out, "Coerce-ovan ne-str ulaz MORA zadržati svoju tekstualnu vrednost (AC2)."
    # falsy 0 ide u `not raw` granu → "" (pokriva razliku coerce vs falsy-guard).
    assert _sanitize(0) == "", "Falsy ne-str (0) MORA pasti u `not raw` granu → '' (AC2)."


def test_empty_body_returns_empty():
    assert _sanitize("") == "", "sanitize_legal_html('') MORA biti '' (AC2)."


# AC2: plain tekst bez tagova → vraćen kao bezbedan tekst
def test_plain_text_passthrough():
    out = _sanitize("Samo običan tekst bez tagova.")
    assert "Samo običan tekst bez tagova." in out, (
        "Plain tekst MORA proći netaknut (nh3 ostavlja text node-ove; AC2/AC7)."
    )
    assert "<script" not in out, "Plain tekst NE sme uvesti markup (AC2)."


# AC2: dijakritike očuvane kroz sanitizaciju
def test_diacritics_preserved():
    out = _sanitize("<p>Čačak žuri kroz šumu — đak ćuti.</p>")
    assert "Čačak žuri kroz šumu — đak ćuti." in out, (
        "Pune dijakritike (č/ć/ž/š/đ) MORAJU proći netaknute (project-context.md; AC2)."
    )


# AC2: nedozvoljen tag stripovan ALI unutrašnji tekst ZADRŽAN (STRIP ≠ obriši tekst)
def test_only_disallowed_tag_keeps_inner_text():
    out = _sanitize("<div>tekst u div-u</div>")
    assert "<div" not in out, "<div> MORA biti STRIP-ovan (AC2/G-8)."
    assert "tekst u div-u" in out, (
        "STRIP uklanja NODE ali zadržava unutrašnji tekst — `tekst u div-u` MORA ostati (AC2)."
    )


# AC2: <svg onload=...> ceo node STRIP
def test_svg_onload_stripped():
    out = _sanitize("<svg onload=alert(1)>x</svg>")
    assert "<svg" not in out, "<svg> (van allowlist-a) MORA biti STRIP-ovan (AC2)."
    assert "onload" not in out, "`onload` handler MORA biti STRIP-ovan (AC2)."


# AC2: HTML komentar STRIP (nh3 default uklanja komentare)
def test_html_comment_stripped():
    out = _sanitize("<!-- tajni komentar --><p>x</p>")
    assert "<!--" not in out, "HTML komentar MORA biti STRIP-ovan (AC2)."


# AC2 (G-2 — verifikuj na instaliranoj verziji): goli `<`/`>` u plain tekstu bezbedan
def test_bare_angle_brackets_in_plain_text_safe():
    out = _sanitize("cena < 5 i > 3 evra")
    assert "<script" not in out and "<img" not in out, (
        "Goli `<`/`>` u plain tekstu NE sme proizvesti izvršiv markup (AC2/G-2)."
    )
    # Ostatak teksta (brojevi/reči) mora preživeti — bez panike/crasha.
    assert "cena" in out and "evra" in out, "Plain tekst oko golih `<`/`>` MORA ostati (G-2)."


# ─────────────────────────────────────────────────────────────────────────────
# Filter — {{ value|legal_html }} (AC3) — mark_safe SAMO posle sanitizacije
# ─────────────────────────────────────────────────────────────────────────────


# AC3: filter vraća SafeString (mark_safe primenjen)
def test_filter_returns_safestring():
    from django.utils.safestring import SafeString

    out = _legal_html("<p>x</p>")
    assert isinstance(out, SafeString), (
        "legal_html MORA vratiti SafeString (mark_safe; AC3/SM-D3)."
    )


# AC3: filter sanitizuje PRE mark_safe (SafeString NE sadrži <script>)
def test_filter_sanitizes_before_marksafe():
    out = _legal_html("<script>alert(1)</script><p>ok</p>")
    assert "<script" not in out and "&lt;script&gt;" not in out, (
        "Filter MORA sanitizovati PRE mark_safe — `<script>` STRIP-ovan, NE markiran-safe "
        "kao sirov (AC3/SM-D3/G-6)."
    )
    assert "<p>ok</p>" in out, "Dozvoljen sadržaj MORA proći (AC3)."


# AC3: None/prazno → prazan SafeString
def test_filter_none_empty():
    from django.utils.safestring import SafeString

    out_none = _legal_html(None)
    out_empty = _legal_html("")
    assert out_none == "" and out_empty == "", "legal_html(None)/('') MORA biti '' (AC3)."
    assert isinstance(out_none, SafeString), "Prazan rezultat MORA i dalje biti SafeString (AC3)."


# AC3: filter registrovan — {% load legal_html %}{{ x|legal_html }} render radi
def test_filter_registered_and_renders():
    from django.template import Context, Template

    tpl = Template("{% load legal_html %}{{ body|legal_html }}")
    rendered = tpl.render(Context({"body": "<p>Bezbedan</p><script>alert(1)</script>"}))
    assert "<p>Bezbedan</p>" in rendered, "Filter MORA biti učitan i renderovati allowlist (AC3)."
    assert "<script" not in rendered and "&lt;script&gt;" not in rendered, (
        "Render kroz filter MORA STRIP-ovati `<script>` (AC3/SM-D7)."
    )


# AC3 GUARD (zamenjuje stari template `mark_safe`-not-in-template static guard):
# mark_safe sme da obavija ISKLJUČIVO sanitize_legal_html(...) izlaz, NIKAD sirov value.
def test_marksafe_wraps_only_sanitized_output():
    from pathlib import Path

    from django.conf import settings

    src_path = (
        Path(settings.BASE_DIR) / "apps" / "core" / "templatetags" / "legal_html.py"
    )
    assert src_path.exists(), (
        f"{src_path} MORA postojati (AC3). RED: filter modul još ne postoji."
    )
    src = src_path.read_text(encoding="utf-8").replace(" ", "")
    assert "mark_safe(sanitize_legal_html(" in src, (
        "legal_html.py MORA `mark_safe(sanitize_legal_html(...))` — mark_safe SAMO posle "
        "sanitizacije (G-6/AC3)."
    )
    assert "mark_safe(value" not in src, (
        "legal_html.py NE SME `mark_safe(value)` na SIROV body (stored-XSS; G-6/AC3)."
    )


# ─────────────────────────────────────────────────────────────────────────────
# Render integracija — gdpr cookie policy (AC5) — sa DB
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def _seed_cookie_rich():
    from apps.gdpr.models import CookiePolicy

    obj = CookiePolicy.load()
    obj.title_sr = "Politika kolačića"
    obj.body_sr = RICH_BODY
    obj.save()
    return obj


@pytest.mark.django_db
def test_cookie_rich_structure_rendered_and_xss_stripped(client, _seed_cookie_rich):
    response = client.get(COOKIE_PATH_SR, HTTP_HOST="localhost")
    assert response.status_code == 200, f"GET {COOKIE_PATH_SR} MORA biti 200 (AC5)."
    html = response.content.decode("utf-8")
    body = _body_fragment(html, "coric-cookie-policy__body")
    for frag in ("<table", "<thead", "<tr", "<th", "<td", "<ul", "<li", "<h2"):
        assert frag in body, f"Struktura {frag!r} MORA biti zadržana, NE escape-ovana (AC5)."
    assert '<a href="https://policies.google.com/privacy"' in body, (
        "Link ka GA4 politici MORA biti zadržan (AC5)."
    )
    assert 'rel="noopener noreferrer"' in body, "Emitovani <a> MORA imati forsiran rel (AC5/G-7)."
    # XSS strip — asercije SAMO nad body regionom (chrome legitimno ima <script src=).
    assert "<script" not in body, "`<script` MORA biti STRIP-ovan iz body-a (AC5/SM-D7)."
    assert "&lt;script&gt;" not in html, "`<script>` NE sme biti escape-ovan u tekst (AC5/SM-D7)."
    assert "onerror=" not in body and "<iframe" not in body and "style=" not in body, (
        "XSS/embed/inline-style vektori MORAJU biti odsutni iz body-a (AC5)."
    )


@pytest.mark.django_db
@pytest.mark.parametrize("path", [COOKIE_PATH_HU, COOKIE_PATH_EN])
def test_cookie_rich_per_locale_fallback(client, _seed_cookie_rich, path):
    response = client.get(path, HTTP_HOST="localhost")
    assert response.status_code == 200, f"GET {path} MORA biti 200 sa sr-fallback (AC5)."
    html = response.content.decode("utf-8")
    body = _body_fragment(html, "coric-cookie-policy__body")
    assert "<table" in body, f"{path}: sr-fallback rich body MORA biti renderovan (AC5)."
    assert "<script" not in body and "&lt;script&gt;" not in html, (
        f"{path}: `<script>` MORA biti STRIP-ovan i u fallback renderu (AC5/SM-D7)."
    )


# ─────────────────────────────────────────────────────────────────────────────
# Render integracija — pages privacy strana (AC5) — sa DB
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def _seed_privacy_rich():
    from apps.pages.models import Page

    page, _created = Page.objects.update_or_create(
        slug="politika-privatnosti",
        defaults={"title_sr": "Politika privatnosti", "body_sr": RICH_BODY},
    )
    return page


@pytest.mark.django_db
def test_privacy_rich_structure_rendered_and_xss_stripped(client, _seed_privacy_rich):
    response = client.get(PRIVACY_PATH_SR, HTTP_HOST="localhost")
    assert response.status_code == 200, f"GET {PRIVACY_PATH_SR} MORA biti 200 (AC5)."
    html = response.content.decode("utf-8")
    body = _body_fragment(html, "coric-static-page__body")
    for frag in ("<table", "<thead", "<tr", "<th", "<td", "<ul", "<li", "<h2"):
        assert frag in body, f"Struktura {frag!r} MORA biti zadržana (AC5)."
    assert '<a href="https://policies.google.com/privacy"' in body, (
        "Link u privacy body-u MORA biti zadržan (AC5)."
    )
    assert 'rel="noopener noreferrer"' in body, "Emitovani <a> MORA imati forsiran rel (AC5/G-7)."
    # XSS strip — SAMO nad body regionom (chrome legitimno ima <script src=/<img>/<div>).
    assert "<script" not in body, "`<script` MORA biti STRIP-ovan iz body-a (AC5/SM-D7)."
    assert "&lt;script&gt;" not in html, "`<script>` NE sme biti escape-ovan (AC5/SM-D7)."
    assert "onerror=" not in body and "<iframe" not in body and "<div" not in body, (
        "XSS/embed/div vektori MORAJU biti odsutni iz body-a (AC5)."
    )


# AC5 NOVI (render-integration disallowed-tag + title survival; zatvara unit-only gap TEA #6):
# body sa zabranjenim tagovima (<div>/<h1>/<iframe>) + <a title=...> kroz STVARAN page render
# → zabranjeni tagovi STRIP-ovani u body fragmentu; `title` atribut PREŽIVLJAVA na <a>.
@pytest.mark.django_db
def test_privacy_disallowed_tags_stripped_title_survives(client):
    from apps.pages.models import Page

    Page.objects.update_or_create(
        slug="politika-privatnosti",
        defaults={
            "title_sr": "Politika privatnosti",
            "body_sr": (
                "<div>div-omot</div><h1>h1-naslov</h1>"
                "<iframe src='https://evil.test'></iframe>"
                '<p>Vidi <a href="https://x.test" title="tooltip">link</a>.</p>'
            ),
        },
    )
    response = client.get(PRIVACY_PATH_SR, HTTP_HOST="localhost")
    assert response.status_code == 200, f"GET {PRIVACY_PATH_SR} MORA biti 200 (AC5)."
    html = response.content.decode("utf-8")
    body = _body_fragment(html, "coric-static-page__body")
    # Zabranjeni tagovi STRIP-ovani iz body regiona (chrome legitimno ima <div>/<h1> → scope na body).
    assert "<div" not in body, "<div> MORA biti STRIP-ovan iz body-a (AC5/G-8)."
    assert "<h1" not in body, "<h1> MORA biti STRIP-ovan iz body-a (rezervisan za stranicu; AC5/G-8)."
    assert "<iframe" not in body, "<iframe> MORA biti STRIP-ovan iz body-a (AC5/G-8)."
    # Dozvoljen <a title> PREŽIVLJAVA (title je u allowlist-u za <a>).
    assert 'title="tooltip"' in body, "<a title> MORA preživeti sanitizaciju (AC2/AC5)."
    assert '<a href="https://x.test"' in body, "<a href> MORA biti zadržan (AC5)."


# AC5 NOVI (privacy: tabela + link render — paralela gdpr test_body_table_and_links_rendered):
# table + <a href=https://...> → struktura prisutna; rel="noopener noreferrer" forsiran; <script> STRIP.
@pytest.mark.django_db
def test_body_table_links_rendered(client, _seed_privacy_rich):
    response = client.get(PRIVACY_PATH_SR, HTTP_HOST="localhost")
    assert response.status_code == 200, f"GET {PRIVACY_PATH_SR} MORA biti 200 (AC5)."
    html = response.content.decode("utf-8")
    body = _body_fragment(html, "coric-static-page__body")
    for frag in ("<table", "<thead", "<tr", "<th", "<td"):
        assert frag in body, f"Struktura tabele {frag!r} MORA proći sanitizaciju (AC5)."
    assert '<a href="https://policies.google.com/privacy"' in body, (
        "Link MORA biti zadržan (AC5)."
    )
    assert 'rel="noopener noreferrer"' in body, "Emitovani <a> MORA imati forsiran rel (AC5/G-7)."
    assert "<script" not in body and "&lt;script&gt;" not in html, (
        "`<script>` MORA biti STRIP-ovan (NE escape) i u rich renderu (AC5/SM-D7)."
    )


@pytest.mark.django_db
@pytest.mark.parametrize("path", [PRIVACY_PATH_HU, PRIVACY_PATH_EN])
def test_privacy_rich_per_locale_fallback(client, _seed_privacy_rich, path):
    response = client.get(path, HTTP_HOST="localhost")
    assert response.status_code == 200, f"GET {path} MORA biti 200 sa sr-fallback (AC5)."
    html = response.content.decode("utf-8")
    body = _body_fragment(html, "coric-static-page__body")
    assert "<table" in body, f"{path}: sr-fallback rich body MORA biti renderovan (AC5)."
    assert "<script" not in body and "&lt;script&gt;" not in html, (
        f"{path}: `<script>` MORA biti STRIP-ovan i u fallback renderu (AC5/SM-D7)."
    )


# ─────────────────────────────────────────────────────────────────────────────
# 0 schema migracija (AC7)
# ─────────────────────────────────────────────────────────────────────────────


# AC7: makemigrations --check → No changes detected (body ostaje TextField; render-only)
@pytest.mark.django_db
def test_no_new_migrations():
    from io import StringIO

    from django.core.management import call_command

    out = StringIO()
    try:
        call_command("makemigrations", "--check", "--dry-run", stdout=out, stderr=out)
        exit_code = 0
    except SystemExit as exc:
        exit_code = exc.code or 0
    assert exit_code == 0, (
        "makemigrations --check --dry-run MORA biti čist (No changes detected) — 7.5 je "
        f"render-only swap, 0 schema promene (AC7/SM-D6). Output: {out.getvalue()!r}"
    )
