"""Page Object — Product detail strana (/sr/proizvod/<slug>/) — AC5.

Pokriva: detail root, galerija (zavisi od AC12 ProductImage setup-a — bez slike
`<section id="product-gallery">` se NE renderuje, `{% if product.images.all %}`),
specifikacije akordion (Motor sekcija default-open), model-inquiry forma +
success kartica.

REALNOST forme (`_model_inquiry_form_fields.html`):
- Polje *Model* je READONLY auto-popunjeno na `product.name` — NE unosi se.
- Hidden `name="product_slug"` nosi slug (forma submit → /sr/htmx/forme/upit-za-model/).
- Vidljiva polja: `#inquiry-name`, `#inquiry-email`, `#inquiry-phone`, `#inquiry-message`.
- Submit: `data-testid="model-inquiry-submit"`.

RED zavisnost: success kartica (`model_inquiry_success.html`) NEMA još
`data-testid="model-inquiry-success"` (AC8 delta) → success asercija preko
get_by_test_id pada dok Dev ne instrumentuje. Substring je primarni fallback
(REALNI string, C-4).
"""

from __future__ import annotations

from playwright.sync_api import Page, expect

# REALNI success string (verbatim iz template-a, C-4) — substring assert (AC2).
MODEL_INQUIRY_SUCCESS_SUBSTRING = "Vaš upit za model je primljen"
# OOB aria-live announcement (verbatim iz model_inquiry_success.html include message).
# `#aria-live` je `visually-hidden` singleton (htmx_aria.aria_live tag, Story 1-6 lock) —
# `to_be_visible()` na njemu je bezvredan signal (element je UVEK u DOM-u, prazan do swap-a).
# Asertujemo da je OOB swap UPISAO announcement tekst (deterministička post-swap potvrda — AC2).
MODEL_INQUIRY_ARIA_ANNOUNCEMENT = "Upit za model je poslat."


class ProductDetailPage:
    PATH = "/{locale}/proizvod/{slug}/"

    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url

    # -- navigacija -----------------------------------------------------------

    def goto(self, slug: str, locale: str = "sr") -> "ProductDetailPage":
        self.page.goto(self.base_url + self.PATH.format(locale=locale, slug=slug))
        return self

    # -- lokatori -------------------------------------------------------------

    @property
    def detail_root(self):
        return self.page.get_by_test_id("product-detail-page")

    @property
    def gallery(self):
        # Galerija sekcija postoji SAMO ako product.images.all (AC12 ProductImage).
        return self.page.locator("#product-gallery")

    @property
    def specs_section(self):
        return self.page.locator("#product-specs")

    @property
    def motor_accordion(self):
        # `_specs_accordion.html` već generiše data-testid="spec-section-<slug>"; Motor sekcija.
        return self.page.get_by_test_id("spec-section-motor")

    @property
    def model_inquiry_form(self):
        return self.page.get_by_test_id("model-inquiry-form")

    @property
    def model_readonly_field(self):
        # AC8 delta (opciono): data-testid="model-inquiry-model" na readonly Model inputu.
        return self.page.get_by_test_id("model-inquiry-model")

    @property
    def product_slug_hidden(self):
        return self.page.locator('input[name="product_slug"]')

    @property
    def inquiry_submit(self):
        return self.page.get_by_test_id("model-inquiry-submit")

    @property
    def success_card(self):
        # AC8 delta — data-testid="model-inquiry-success" na success partial-u.
        return self.page.get_by_test_id("model-inquiry-success")

    @property
    def aria_live(self):
        # Singleton iz base.html (htmx_aria.aria_live tag); NE diramo (Story 1-6 lock).
        return self.page.locator("#aria-live")

    # -- asercije -------------------------------------------------------------

    def expect_loaded(self) -> None:
        expect(self.detail_root).to_be_visible()

    def expect_gallery_visible(self) -> None:
        # Zavisi od AC12 setup-a (≥1 ProductImage za agri-tracking-tb804).
        expect(self.gallery).to_be_visible()

    def expect_specs_motor_open(self) -> None:
        expect(self.specs_section).to_be_visible()
        # Motor sekcija je `forloop.first` → renderuje `open` atribut (default-open).
        expect(self.motor_accordion).to_have_attribute("open", "")

    def expect_model_autofilled(self, slug: str) -> None:
        # Hidden product_slug nosi slug proizvoda (auto-popunjen iz product.slug).
        expect(self.product_slug_hidden).to_have_value(slug)

    # -- akcije ---------------------------------------------------------------

    def fill_and_submit_inquiry(
        self, *, name: str, email: str, phone: str, message: str
    ) -> None:
        """Skrol do forme + popuni 4 vidljiva polja + submit (HTMX). Model je readonly."""
        self.model_inquiry_form.scroll_into_view_if_needed()
        self.page.locator("#inquiry-name").fill(name)
        self.page.locator("#inquiry-email").fill(email)
        self.page.locator("#inquiry-phone").fill(phone)
        self.page.locator("#inquiry-message").fill(message)
        self.inquiry_submit.click()

    def expect_inquiry_success(self) -> None:
        """Assert success kartica (testid + REALNI substring) + aria-live najava (AC2/AC10).

        aria-live: `#aria-live` je `visually-hidden` singleton — asertujemo da je OOB
        swap UPISAO announcement tekst (smislen post-swap signal), NE puko `to_be_visible()`
        (koje bi prošlo i pre submita jer je region uvek u DOM-u).
        """
        expect(self.success_card).to_be_visible()
        expect(self.success_card).to_contain_text(MODEL_INQUIRY_SUCCESS_SUBSTRING)
        expect(self.aria_live).to_contain_text(MODEL_INQUIRY_ARIA_ANNOUNCEMENT)
