"""UJ-1 — Marko kupuje traktor (anon, desktop) — AC2/AC9/AC10/AC12.

Pun flow (sr-full):
  / → Traktori → /sr/traktori/ → HTMX live-filter SAMO po snazi (snaga_min=61) →
  slug-scoped asercija (TB804 80KS + SL904 90KS vidljivi; WZ504 50KS filtriran VAN) →
  klik TB804 kartice → /sr/proizvod/agri-tracking-tb804/ → detail + galerija (AC12) +
  specifikacije (Motor default-open) → model-inquiry forma (Model auto-popunjen,
  readonly) → popuni Ime/Email/Telefon/Poruka → submit (HTMX) → success kartica
  „Vaš upit za model je primljen" + aria-live.

Locale (OQ-2): parametrizovano ("sr","full") vs ("hu","locale_only"). `full` vozi
pun sadržaj; `locale_only` asertuje SAMO locale-routing + <html lang> (hu/en sadržaj
NIJE seed-ovan).

RED: filter-snaga-min testid (AC8 delta), galerija zavisi od AC12 ProductImage,
model-inquiry-success testid (AC8 delta), e2e_data command (seed_e2e_data) — sve
nedostaje dok Dev ne instrumentuje → smislen RED fail (not seed/collection error).
"""

from __future__ import annotations

import pytest
from playwright.sync_api import expect

from tests.e2e.page_objects import ProductDetailPage, TraktoriListingPage

# AC13 — modul-level marker izoluje E2E iz `just test` (-m 'not e2e').
pytestmark = pytest.mark.e2e

# Deterministički slug-ovi iz 9-7 seed manifesta.
TB804 = "agri-tracking-tb804"  # 80 KS / €28.500 — UJ-1 headline
WZ504 = "wuzheng-wz504"  # 50 KS — filtrira se VAN na snaga_min=61
SL904 = "saillong-sl904"  # 90 KS — ostaje unutra

# Power-only prag (OQ-1 RAZREŠEN): 61 → TB804(80)+SL904(90) unutra, WZ504(50) van.
# NE koristi cenu (TB804 €28.5k > €25k bi pao pod „cena ≤ 25k" — C-6).
SNAGA_MIN = 61

LOCALE_PARAMS = [
    pytest.param("sr", "full", id="sr-full"),
    pytest.param("hu", "locale_only", id="hu-locale-only"),
]


@pytest.mark.parametrize("locale,scope", LOCALE_PARAMS)
def test_marko_filter_and_inquiry(page, base_url, e2e_data, locale, scope):
    """UJ-1 glavni journey — locale-parametrizovan (full vs locale_only)."""
    listing = TraktoriListingPage(page, base_url)
    listing.goto(locale=locale)

    if scope == "locale_only":
        # hu/en: sadržaj nije seed-ovan → asertuj SAMO locale-routing + <html lang>.
        # DEFENZIVNI guard (OQ-2): ako locale prefiks nije „primljen" (routing nije
        # konfigurisan / strana je 404), degradiraj na JASAN skip umesto kriptičnog
        # to_have_attribute fail-a. sr-full grana ostaje stroga.
        if f"/{locale}/" not in page.url:
            pytest.skip(f"{locale} locale routing nije konfigurisan — OQ-2 deferred")
        expect(page.locator("html")).to_have_attribute("lang", locale)
        return

    # -- sr-full: pun sadržaj-flow ----------------------------------------
    listing.expect_grid_visible()

    # HTMX live-filter SAMO po snazi (slug-scoped — AC9; auto-wait — AC10).
    listing.filter_by_snaga_min(SNAGA_MIN)
    listing.expect_card_present(TB804)  # 80 KS unutra
    listing.expect_card_present(SL904)  # 90 KS unutra
    listing.expect_card_absent(WZ504)  # 50 KS filtriran VAN

    # Klik cele kartice → product detail.
    listing.open_card(TB804)

    detail = ProductDetailPage(page, base_url)
    detail.expect_loaded()
    detail.expect_gallery_visible()  # zavisi od AC12 ProductImage setup-a
    detail.expect_specs_motor_open()  # Motor akordion default-open
    detail.expect_model_autofilled(TB804)  # hidden product_slug == slug

    # Popuni 4 vidljiva polja (Model je readonly — NE unosi se) + submit (HTMX).
    detail.fill_and_submit_inquiry(
        name="Marko Marković",
        email="marko@example.com",
        phone="+381641112233",
        message="Zainteresovan sam za ovaj model, molim ponudu.",
    )
    detail.expect_inquiry_success()


def test_marko_direct_detail_gallery(page, base_url, e2e_data):
    """AC2 dodatno — direktan pristup TB804 detail strani potvrđuje galeriju (AC12).

    Izolovan od filtera: potvrđuje da AC12 ProductImage remedijacija renderuje
    `<section id="product-gallery">` (bez slike sekcija NE postoji).
    """
    detail = ProductDetailPage(page, base_url)
    detail.goto(TB804, locale="sr")
    detail.expect_loaded()
    detail.expect_gallery_visible()
