"""Story 7.1 → RECONCILED za 7.5 — XSS granica na CookiePolicy.body render (TEA RED).

⚠️ RECONCILIACIJA 7.5 (SM-D7): render granica je prebačena sa `{{ body|linebreaks }}`
(auto-ESCAPE sveg HTML-a) na `{{ body|legal_html }}` (nh3 SANITIZE → mark_safe SAMO
posle sanitizacije). nh3 STRIPUJE opasne node-ove (uklanja ceo tag), NE escape-uje ih.

Posledica za asercije (STRIP ≠ ESCAPE):
- staro: `&lt;script&gt;` PRISUTAN (escape) — VIŠE NE VAŽI (node nestaje).
- novo: `<script` ODSUTAN I `&lt;script&gt;` ODSUTAN (node uklonjen, NE escape-ovan).
- XSS garancija je JAČA, NE slabija: `<script>alert` i `onerror=` i dalje ODSUTNI.
- NIKAD asertuj `alert(1) not in html` — nh3 može ostaviti goli tekst posle strip-a
  (korektna implementacija bi pala na toj asertaciji).

⚠️ COLLECTION-SAFETY: apps.gdpr importi UNUTAR funkcija.

Refs:
- 7-5-...-nh3.md AC5/AC6 + SM-D2/SM-D4/SM-D7 + STRIP-vs-ESCAPE tabela + G-3/G-8
- 7-1-...-admin.md AC8 (originalni escape lock — sad SUPERSEDED za pravne strane)
"""

from __future__ import annotations

import pytest

from .conftest import COOKIE_POLICY_PATH_SR

pytestmark = pytest.mark.django_db

RICH_BODY = (
    "<h2>Kolačići</h2>"
    "<table><thead><tr><th>Naziv</th><th>Svrha</th></tr></thead>"
    "<tbody><tr><td>_ga</td><td>Analitika</td></tr></tbody></table>"
    '<p>Vidi <a href="https://policies.google.com/privacy">GA4 politiku</a>.</p>'
    "<script>alert(1)</script>"
)


def _seed_body(body):
    from apps.gdpr.models import CookiePolicy

    obj = CookiePolicy.load()
    obj.title_sr = "Politika kolačića"
    obj.body_sr = body
    obj.save()
    return obj


def _body_fragment(html):
    """Izvuci SAMO sanitizovan cookie body region (coric-cookie-policy__body).

    ⚠️ base.html chrome legitimno ima `<script src=...>` (htmx/bootstrap/gdpr-banner),
    `<img>` (logo) i `<div>` (layout) → `"<script"/"<img"/"<div" not in html` nad CELOM
    stranom je UNSATISFIABLE (korektan GREEN bi pao). XSS strip-asercije targetiraju
    SAMO body region gde živi sanitizovan `body`.
    """
    marker = 'class="coric-cookie-policy__body"'
    start = html.find(marker)
    assert start != -1, "Cookie body region MORA postojati u renderu (AC5)."
    end = html.find("</article>", start)
    return html[start : end if end != -1 else len(html)]


# AC6 RECONCILE (escape→strip): <script> u body → STRIP-ovan (NE escape), izvršiv tag ODSUTAN
def test_body_script_is_stripped_not_executed(client):
    _seed_body("<script>alert(1)</script>")

    response = client.get(COOKIE_POLICY_PATH_SR, HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")
    body = _body_fragment(html)

    assert "<script" not in body, (
        "SIROV `<script` NE SME biti u body-u — nh3 STRIP-uje node (XSS lock; AC6/SM-D7)."
    )
    assert "&lt;script&gt;" not in html, (
        "`<script>` NE sme biti ESCAPE-ovan u tekst — nh3 UKLANJA node (STRIP ≠ ESCAPE; "
        "garancija JAČA od starog |linebreaks escape-a; AC6/SM-D7)."
    )
    assert "<script>alert" not in html, (
        "Izvršiv `<script>alert` MORA ostati ODSUTAN (XSS garancija NE sme oslabiti; AC6)."
    )


# AC6 RECONCILE: <img onerror> → ceo <img> node STRIP (img van allowlist-a), onerror ODSUTAN
def test_body_img_onerror_is_stripped(client):
    _seed_body('<img src=x onerror="alert(1)">')

    response = client.get(COOKIE_POLICY_PATH_SR, HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")
    body = _body_fragment(html)

    assert "onerror=" not in html, (
        "`onerror=` DOM event handler MORA biti STRIP-ovan (nh3; AC6/G-8)."
    )
    # `<img` se scope-uje na body — chrome (header/footer logo) legitimno ima <img>.
    assert "<img" not in body, (
        "<img> je van allowlist-a → ceo node STRIP-ovan iz body-a (AC6/G-8)."
    )
    assert "&lt;img" not in html, (
        "<img> NE sme biti escape-ovan u tekst — STRIP, ne escape (AC6/SM-D7)."
    )


# AC5 NOVI: strukturisan HTML (table + link) PROLAZI sanitizaciju; XSS strip; per-locale sr
def test_body_table_and_links_rendered(client):
    _seed_body(RICH_BODY)

    response = client.get(COOKIE_POLICY_PATH_SR, HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")
    body = _body_fragment(html)

    for frag in ("<table", "<thead", "<tr", "<th", "<td", "<h2"):
        assert frag in body, f"Struktura {frag!r} MORA proći sanitizaciju (AC5)."
    assert '<a href="https://policies.google.com/privacy"' in body, (
        "Link ka GA4 politici MORA biti zadržan (AC5)."
    )
    assert 'rel="noopener noreferrer"' in body, "Emitovani <a> MORA imati forsiran rel (AC5/G-7)."
    assert "<script" not in body and "&lt;script&gt;" not in html, (
        "`<script>` MORA biti STRIP-ovan (NE escape) i u rich renderu (AC5/SM-D7)."
    )


# AC6: template KORISTI |legal_html, NE |linebreaks, NE |safe/mark_safe na sirov body
def test_body_never_safe_filter():
    from pathlib import Path

    from django.conf import settings

    template_path = Path(settings.BASE_DIR) / "templates" / "gdpr" / "cookie_policy.html"
    assert template_path.exists(), f"{template_path} MORA postojati (AC4)."
    text = template_path.read_text(encoding="utf-8")
    compact = text.replace(" ", "")

    assert "policy.body|legal_html" in compact, (
        "Template MORA renderovati body kroz |legal_html (sanitizovan rich-HTML; AC4/AC6/SM-D4)."
    )
    assert "policy.body|linebreaks" not in compact, (
        "Template NE SME više koristiti |linebreaks (dev ne sme ostaviti OBA filtera; AC6)."
    )
    assert "body|safe" not in compact and "mark_safe" not in compact, (
        "Template NE SME |safe / mark_safe na SIROV body (mark_safe živi u legal_html filteru; "
        "AC6/G-6)."
    )
