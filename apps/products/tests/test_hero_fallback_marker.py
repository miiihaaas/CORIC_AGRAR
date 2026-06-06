"""Story 6.5 — Product hero H1 i18n fallback marker integration (TEA RED).

Cross-app integration: renderuje CELU product detail stranu preko i18n URL routing-a
(`/hu/proizvod/<slug>/`) sa LocaleMiddleware → verifikuje da hero H1
(`coric-hero-overlay-card__title`) sadrži `coric-fallback-marker` kad je `name_hu`
prazan (epics:976 — THE acceptance scenario), i NE sadrži kad je `name_hu` popunjen.

Takođe lock-uje zero-regression (#14c): include-ovanje hero_overlay_card.html BEZ
`fallback_obj` param-a → plain `{{ title }}`, NEMA markera (SM-D7 opcija A — opt-in
backward-compatible; postojeći pozivaoci netaknuti).

Wiring koji ovi testovi zaključavaju (Dev mora implementirati):
- templates/partials/hero_overlay_card.html: `{% if fallback_obj %}{% translated_field
  fallback_obj fallback_field %}{% else %}{{ title }}{% endif %}`
- templates/products/partials/_hero_section.html: prosleđuje `fallback_obj=product
  fallback_field='name'`

HTML parsing: regex (NIKAD BeautifulSoup). Product reachable preko is_published=True;
URL = `/hu/proizvod/<slug>/` (potvrđeno test_views_product_detail.py).

Refs:
- 6-5-i18n-fallback-marker-tooltip.md AC6 + Testing #14b/#14c + SM-D7 + G6
- apps/products/tests/test_views_product_detail.py (URL/render precedent)
"""

from __future__ import annotations

import re

import pytest
from django.utils.translation import activate

from apps.products.tests.factories import ProductFactory

pytestmark = pytest.mark.django_db


_MARKER_CLASS = 'class="coric-fallback-marker"'


def _detail_html(client, product, locale: str) -> str:
    """GET /<locale>/proizvod/<slug>/ → decoded response HTML."""
    activate(locale)
    try:
        resp = client.get(
            f"/{locale}/proizvod/{product.slug}/", HTTP_HOST="localhost"
        )
        assert resp.status_code == 200, (
            f"Product detail /{locale}/proizvod/{product.slug}/ MORA vratiti 200 "
            f"(reachable fixture) — dobio {resp.status_code}."
        )
        return resp.content.decode("utf-8")
    finally:
        activate("sr")


# AC6 / Testing #14b — THE acceptance scenario (epics:976)
def test_product_hero_h1_fallback_marker_when_name_hu_empty(client):
    """#14b — /hu/proizvod/<slug>/ sa name_hu="" → hero H1 sadrži coric-fallback-marker.

    Potvrđuje SM-D7 opcija A wiring (fallback_obj=product fallback_field='name') +
    end-to-end fallback detekciju kroz realni Product + LocaleMiddleware + URL reverse.
    """
    activate("sr")
    product = ProductFactory.create(name="Agri-Tracking TB804", is_published=True)
    # name_sr popunjen (iz name=), name_hu eksplicitno prazan → fallback na /hu/
    product.name_sr = "Agri-Tracking TB804"
    product.name_hu = ""
    product.save()

    html = _detail_html(client, product, "hu")

    # Hero H1 (coric-hero-overlay-card__title) MORA sadržati marker
    hero_h1 = re.search(
        r'<h1[^>]*class="[^"]*coric-hero-overlay-card__title[^"]*"[^>]*>(.*?)</h1>',
        html,
        re.DOTALL,
    )
    assert hero_h1, (
        "Product detail strana MORA imati hero H1 sa klasom "
        "coric-hero-overlay-card__title (hero_overlay_card.html)."
    )
    h1_inner = hero_h1.group(1)
    assert "coric-fallback-marker" in h1_inner, (
        "Hero H1 MORA sadržati coric-fallback-marker kad je name_hu prazan "
        "(/hu/proizvod/... — epics:976 THE acceptance scenario; AC6/#14b). "
        f"H1 sadržaj: {h1_inner!r}"
    )
    assert "Agri-Tracking TB804" in h1_inner, (
        "Marker MORA nositi sr naziv proizvoda (name_sr; AC6)."
    )
    assert 'lang="sr"' in h1_inner, (
        'Fallback tekst MORA imati lang="sr" (WCAG 3.1.2; AC2/AC6).'
    )
    assert "<svg" in h1_inner, "Marker MORA imati inline <svg> ⓘ ikonu (SM-D5/AC6)."


# AC6 / Testing #14b — popunjen name_hu → NEMA markera (zero false-positive)
def test_product_hero_h1_no_marker_when_name_hu_populated(client):
    """#14b (negativ) — /hu/ sa popunjenim name_hu → hero H1 BEZ markera."""
    activate("sr")
    product = ProductFactory.create(name="Agri-Tracking TB804", is_published=True)
    product.name_sr = "Agri-Tracking TB804"
    product.name_hu = "Agri-Követés TB804"
    product.save()

    html = _detail_html(client, product, "hu")
    hero_h1 = re.search(
        r'<h1[^>]*class="[^"]*coric-hero-overlay-card__title[^"]*"[^>]*>(.*?)</h1>',
        html,
        re.DOTALL,
    )
    assert hero_h1, "Hero H1 mora postojati."
    h1_inner = hero_h1.group(1)
    assert "coric-fallback-marker" not in h1_inner, (
        "Sa popunjenim name_hu → hero H1 NE sme imati marker (NEMA fallback-a; AC6/#14b)."
    )
    assert "Agri-Követés TB804" in h1_inner, (
        "Hero H1 MORA prikazati hu naziv kad je name_hu popunjen (AC6)."
    )


# AC6 / Testing #14b — /en/ → tooltip na engleskom (lokalizacija po visitor locale)
def test_product_hero_marker_on_en_locale(client):
    """#14b (en) — /en/proizvod/<slug>/ sa name_en="" → marker (en visitor locale)."""
    activate("sr")
    product = ProductFactory.create(name="Agri-Tracking TB804", is_published=True)
    product.name_sr = "Agri-Tracking TB804"
    product.name_en = ""
    product.save()

    html = _detail_html(client, product, "en")
    hero_h1 = re.search(
        r'<h1[^>]*class="[^"]*coric-hero-overlay-card__title[^"]*"[^>]*>(.*?)</h1>',
        html,
        re.DOTALL,
    )
    assert hero_h1, (
        "Product detail strana MORA imati hero H1 sa klasom "
        "coric-hero-overlay-card__title."
    )
    h1_inner = hero_h1.group(1)
    assert "coric-fallback-marker" in h1_inner, (
        "/en/proizvod/... sa praznim name_en → marker MORA biti UNUTAR hero H1 "
        f"(NE samo negde na strani; en→en normalizacija; AC6). H1 sadržaj: {h1_inner!r}"
    )


# AC6 / Testing #14c — zero-regression: include BEZ fallback_obj → plain title, NEMA markera
def test_hero_card_zero_regression_no_fallback_obj():
    """#14c — render hero_overlay_card.html BEZ fallback_obj → plain title, NEMA markera.

    Dokaz da je SM-D7 opcija A backward-compatible: postojeći pozivaoci (home/listing/
    about/brand-specific hero) koji prosleđuju samo `title=` STRING padaju na
    `{% else %}{{ title }}{% endif %}` granu → renderuju IDENTIČNO kao pre (zero
    blast-radius; AC6/#14c).
    """
    from django.template import Context, Template
    from django.test import RequestFactory

    activate("hu")  # čak i na hu — bez fallback_obj NE sme biti markera
    try:
        request = RequestFactory().get("/")
        out = Template(
            '{% include "partials/hero_overlay_card.html" '
            'with title="Naslovni tekst bez markera" %}'
        ).render(Context({"request": request}))
    finally:
        activate("sr")

    assert "Naslovni tekst bez markera" in out, (
        "hero_overlay_card.html bez fallback_obj MORA renderovati plain title "
        "({{ title }} grana; AC6/#14c)."
    )
    assert "coric-fallback-marker" not in out, (
        "Bez fallback_obj param-a → NIKAD marker (opt-in backward-compat; zero "
        "blast-radius; AC6/#14c)."
    )
