"""Page Object — Traktori listing strana (/sr/traktori/) — AC5.

Enkapsulira HTMX live-filter mehanizam: filter ide preko HIDDEN inputa
(`name="snaga_min"` / `name="snaga_max"`) koje puni custom JS range-slider
(`data-range-slider`). NEMA native `<input type=range>`. Page object popunjava
hidden input + dispatch-uje `change` event → HTMX re-fetch `#tractor-results`.

Slug-scoped asercije (AC9): testira prisustvo/odsustvo KONKRETNIH
`tractor-card-<slug>` lokatora, NIKAD puki grid count.

RED zavisnost: hidden inputi NEMAJU još `data-testid="filter-snaga-min/max"`
(AC8 delta) → `get_by_test_id("filter-snaga-min")` ne pronalazi element dok Dev
ne instrumentuje `_filter_form.html`.
"""

from __future__ import annotations

from playwright.sync_api import Page, expect


class TraktoriListingPage:
    """Listing + HTMX live-filter po snazi (KS)."""

    # Locale-aware path segment je `traktori` na svim locale-ima v1 (sr-only sadržaj — OQ-2).
    PATH = "/{locale}/traktori/"

    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url

    # -- navigacija -----------------------------------------------------------

    def goto(self, locale: str = "sr") -> "TraktoriListingPage":
        self.page.goto(self.base_url + self.PATH.format(locale=locale))
        return self

    # -- lokatori -------------------------------------------------------------

    @property
    def filter_form(self):
        return self.page.get_by_test_id("tractor-filter-form")

    @property
    def results_grid(self):
        return self.page.get_by_test_id("tractor-results-grid")

    @property
    def snaga_min_input(self):
        # AC8 delta — hidden input dobija data-testid="filter-snaga-min".
        return self.page.get_by_test_id("filter-snaga-min")

    @property
    def snaga_max_input(self):
        return self.page.get_by_test_id("filter-snaga-max")

    def tractor_card(self, slug: str):
        # Postojeći hook `tractor-card-<slug>` (NE diramo — Epic 5/6 markup-lock).
        return self.page.get_by_test_id(f"tractor-card-{slug}")

    # -- akcije ---------------------------------------------------------------

    def filter_by_snaga_min(self, value: int) -> "TraktoriListingPage":
        """Postavi snaga_min preko hidden inputa + dispatch `change` → HTMX swap.

        `fill()` ne triggeruje JS slider event sam — eksplicitno dispatch-ujemo
        `change` (forma hx-trigger="... change delay:300ms") da HTMX re-fetch-uje
        `#tractor-results`. Auto-waiting (AC10) hvata swap; NEMA sleep.
        """
        loc = self.snaga_min_input
        loc.fill(str(value))
        loc.dispatch_event("change")
        return self

    def expect_grid_visible(self) -> None:
        expect(self.results_grid).to_be_visible()

    def expect_card_present(self, slug: str) -> None:
        expect(self.tractor_card(slug)).to_be_visible()

    def expect_card_absent(self, slug: str) -> None:
        # Posle filtera, kartica filtrirana VAN ne sme biti u DOM-u (HTMX innerHTML swap).
        expect(self.tractor_card(slug)).to_have_count(0)

    def open_card(self, slug: str) -> None:
        """Cela kartica je `<a>` — klik vodi na /sr/proizvod/<slug>/."""
        self.tractor_card(slug).click()
