"""Page Object — Servisna strana (/sr/servis/) — UJ-2, AC5.

MOBILE viewport (<768px) flow: otvori hamburger nav (mobile-nav-toggle, AC8 delta)
→ /sr/servis → popuni servisnu formu → priloži fotografiju preko PLAIN file inputa
(`<input type="file" name="photos" multiple>` — NEMA preview/X-remove widget-a, C-8)
→ submit (HTMX) → success kartica.

REALNOST forme (`_service_request_form_fields.html`):
- `#service-name` (req), `#service-phone` (req), `#service-email` (opciono),
  `#service-machine-type` (<select name=machine_type>, req), `#service-brand-model`,
  `#service-description` (req), `#service-photos` (file, multiple).
- Forma: data-testid="service-form"; submit: data-testid="service-submit".

RED zavisnost: `mobile-nav-toggle` (header.html) i `service-request-success`
(success partial) su AC8 delta — get_by_test_id pada dok Dev ne instrumentuje.
"""

from __future__ import annotations

from pathlib import Path

from playwright.sync_api import Page, expect

# REALNI success string (verbatim, C-4) — substring assert (AC3).
SERVICE_SUCCESS_SUBSTRING = "Vaš servisni zahtev je primljen"
# OOB aria-live announcement (verbatim iz service_request_success.html include message).
# `#aria-live` je `visually-hidden` singleton — `to_be_visible()` je bezvredan signal;
# asertujemo da je OOB swap UPISAO announcement tekst (deterministička post-swap potvrda — AC3).
SERVICE_ARIA_ANNOUNCEMENT = "Servisni zahtev je poslat."

# Validni machine_type choices iz template select-a.
MACHINE_TYPE_TRACTOR = "tractor"


class ServicePage:
    PATH = "/{locale}/servis/"

    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url

    # -- navigacija -----------------------------------------------------------

    def goto(self, locale: str = "sr") -> "ServicePage":
        self.page.goto(self.base_url + self.PATH.format(locale=locale))
        return self

    # -- lokatori -------------------------------------------------------------

    @property
    def mobile_nav_toggle(self):
        # AC8 delta — .navbar-toggler.coric-nav__hamburger dobija data-testid="mobile-nav-toggle".
        return self.page.get_by_test_id("mobile-nav-toggle")

    @property
    def mobile_nav_panel(self):
        # Bootstrap collapse meta koji hamburger (data-bs-target) otvara/zatvara
        # (templates/partials/header.html: #coricMainNav). Vidljiv tek POSLE toggle-a.
        return self.page.locator("#coricMainNav")

    @property
    def service_form(self):
        return self.page.get_by_test_id("service-form")

    @property
    def photos_input(self):
        # Plain file input — set_input_files (C-8). Već ima stabilan id #service-photos.
        return self.page.locator("#service-photos")

    @property
    def service_submit(self):
        return self.page.get_by_test_id("service-submit")

    @property
    def success_card(self):
        # AC8 delta — data-testid="service-request-success".
        return self.page.get_by_test_id("service-request-success")

    @property
    def aria_live(self):
        return self.page.locator("#aria-live")

    @property
    def form_alert(self):
        # Server-rendered bound error blok (AC3b edge).
        return self.page.locator(".coric-contact-form__alert")

    # -- akcije ---------------------------------------------------------------

    def open_mobile_nav(self) -> None:
        """Otvori hamburger nav na mobile viewport-u (AC3).

        Posle klika ČEKAMO da se collapse panel (#coricMainNav) zaista otvori — tako
        slomljen hamburger pada GLASNO ovde, umesto da `close_mobile_nav` re-klik bude
        vacuous no-op nad nikad-otvorenim nav-om (TEST_GAP guard).
        """
        expect(self.mobile_nav_toggle).to_be_visible()
        self.mobile_nav_toggle.click()
        expect(self.mobile_nav_panel).to_be_visible()

    def close_mobile_nav(self) -> None:
        """Zatvori hamburger nav (re-klik na toggle) — Bootstrap collapse se sklapa.

        Otvoreni nav overlay može da prekrije servisnu formu (occlusion → flaky
        to_be_visible). Pošto nav otvaramo SAMO da verifikujemo da hamburger radi
        (AC8 mobile-nav-toggle hook), a NE da navigiramo, zatvaramo ga pre asercije
        na formu da overlay ne smeta. Re-klik na isti toggler je Bootstrap toggle.
        """
        self.mobile_nav_toggle.click()

    def fill_form(
        self,
        *,
        name: str,
        phone: str,
        email: str = "",
        machine_type: str = MACHINE_TYPE_TRACTOR,
        brand_model: str = "",
        description: str,
    ) -> None:
        self.page.locator("#service-name").fill(name)
        self.page.locator("#service-phone").fill(phone)
        if email:
            self.page.locator("#service-email").fill(email)
        self.page.locator("#service-machine-type").select_option(machine_type)
        if brand_model:
            self.page.locator("#service-brand-model").fill(brand_model)
        self.page.locator("#service-description").fill(description)

    def attach_photo(self, file_path: Path) -> None:
        """Plain multipart file upload (set_input_files — C-8)."""
        self.photos_input.set_input_files(str(file_path))

    def submit(self) -> None:
        self.service_submit.click()

    # -- asercije -------------------------------------------------------------

    def expect_success(self) -> None:
        """Success kartica (testid + REALNI substring) + aria-live najava (AC3/AC10).

        aria-live: asertujemo OOB swap announcement tekst (smislen post-swap signal),
        NE puko `to_be_visible()` (region je uvek u DOM-u, visually-hidden, prazan do swap-a).
        """
        expect(self.success_card).to_be_visible()
        expect(self.success_card).to_contain_text(SERVICE_SUCCESS_SUBSTRING)
        expect(self.aria_live).to_contain_text(SERVICE_ARIA_ANNOUNCEMENT)

    def expect_server_validation_error(self) -> None:
        """AC3b — server-side >5MB foto edge: forma re-render sa bound error."""
        expect(self.form_alert).to_be_visible()
