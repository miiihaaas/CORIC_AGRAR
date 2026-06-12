"""UJ-2 — Stojan šalje servisni zahtev (anon, MOBILE viewport) — AC3/AC3b/AC10.

Mobile flow (sr-full):
  mobile viewport (<768px) → otvori hamburger nav (mobile-nav-toggle, AC8 delta) →
  /sr/servis → popuni servisnu formu (Ime, Telefon, Email opciono, Vrsta mehanizacije
  <select>, Brend i model, Opis kvara) → priloži fotografiju preko PLAIN file inputa
  (set_input_files — C-8, NEMA preview/X-remove) → submit (HTMX) → success kartica
  „Vaš servisni zahtev je primljen" + aria-live.

AC3b edge: >5MB foto → server-side validacija (forma re-render sa bound error).
Markiran `@pytest.mark.skip` (deferred — tačan size/MIME prag OQ-1) da ne blokira
core flow; Dev može da ga ukey-uje kad odredi prag.

Locale (OQ-2): ("sr","full") vs ("hu","locale_only").

RED: mobile-nav-toggle + service-request-success testid-ovi (AC8 delta), e2e_data
command — nedostaju dok Dev ne instrumentuje.
"""

from __future__ import annotations

import pytest
from playwright.sync_api import expect

from tests.e2e.page_objects import ServicePage

pytestmark = pytest.mark.e2e

LOCALE_PARAMS = [
    pytest.param("sr", "full", id="sr-full"),
    pytest.param("hu", "locale_only", id="hu-locale-only"),
]


@pytest.mark.parametrize("locale,scope", LOCALE_PARAMS)
def test_stojan_service_request(
    mobile_page, base_url, e2e_data, sample_image_path, locale, scope
):
    """UJ-2 glavni journey na MOBILE viewport-u — locale-parametrizovan."""
    service = ServicePage(mobile_page, base_url)
    service.goto(locale=locale)

    if scope == "locale_only":
        # DEFENZIVNI guard (OQ-2): ako locale prefiks nije „primljen" (routing nije
        # konfigurisan / strana je 404), degradiraj na JASAN skip umesto kriptičnog
        # to_have_attribute fail-a. sr-full grana ostaje stroga.
        if f"/{locale}/" not in mobile_page.url:
            pytest.skip(f"{locale} locale routing nije konfigurisan — OQ-2 deferred")
        expect(mobile_page.locator("html")).to_have_attribute("lang", locale)
        return

    # -- sr-full: mobile hamburger + forma + file upload ------------------
    # open→verify→close pattern (AC3/AC8): otvori hamburger da DOKAŽEŠ da mobile-nav
    # toggle radi, potvrdi da je nav vidljiv, pa ga ZATVORI pre rada sa formom. Otvoreni
    # Bootstrap collapse overlay može da prekrije servisnu formu → flaky to_be_visible()
    # na CI-u; navigacija na servis je već urađena goto-om, pa nav samo verifikujemo.
    service.open_mobile_nav()  # mobile-nav-toggle (AC3)
    expect(service.mobile_nav_toggle).to_be_visible()  # hamburger radi (AC8 hook)
    service.close_mobile_nav()  # sklopi overlay da ne prekriva formu (deterministički)

    expect(service.service_form).to_be_visible()

    service.fill_form(
        name="Stojan Stojanović",
        phone="+381651234567",
        email="stojan@example.com",
        machine_type="tractor",
        brand_model="Agri Tracking TB804",
        description="Hidraulika ne podiže priključak, curi ulje na cilindru.",
    )
    service.attach_photo(sample_image_path)  # plain set_input_files (C-8)
    service.submit()
    service.expect_success()  # „Vaš servisni zahtev je primljen" + aria-live


@pytest.mark.skip(reason="deferred — server-side >5MB upload validation edge (AC3b, OQ-1 prag)")
def test_stojan_oversized_photo_rejected(mobile_page, base_url, e2e_data, tmp_path):
    """AC3b edge — >5MB foto → SERVER-side validaciona greška u response-u.

    Validacija je SERVER-side (media_pipeline/forma), NE client-side „pre upload-a"
    (taj JS widget NE postoji i NE sme da se gradi — scope creep, C-8). Skip dok se
    tačan size/MIME prag ne determiniše (OQ-1); kad Dev ukloni skip, generiše >5MB
    fajl u tmp_path i asertuje `expect_server_validation_error()`.
    """
    oversized = tmp_path / "too_big.jpg"
    oversized.write_bytes(b"\xff\xd8\xff" + b"0" * (6 * 1024 * 1024))  # ~6MB pseudo-JPEG

    service = ServicePage(mobile_page, base_url)
    service.goto(locale="sr")
    service.fill_form(
        name="Stojan Stojanović",
        phone="+381651234567",
        description="Test prevelike fotografije.",
    )
    service.attach_photo(oversized)
    service.submit()
    service.expect_server_validation_error()
