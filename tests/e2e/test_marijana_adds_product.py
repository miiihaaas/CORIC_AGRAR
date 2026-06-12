"""UJ-3 — Marijana dodaje proizvod u admin (auth) — AC4/AC4b/AC10/AC11.

Admin flow (sr):
  /admin-coric/ login (env-driven dev_superuser + axes-flush) → DODAJ PROIZVOD →
  Naziv „E2E Test Produkt" (FIKSAN slug e2e-test-produkt — I-3) + brend + ≥1 inline
  spec + ≥1 inline galerija slika, SR samo (HU/EN prazno) → status Objavljeno →
  Sačuvaj → PRIMARNA ASERCIJA: public /sr/proizvod/e2e-test-produkt/ je dostupan
  (HTTP 200 + product-detail-page vidljiv) — cross-surface potvrda objave.
  Opciono: admin „...successfully" substring. NE asertuj nepostojeći „je objavljen" toast (C-2).

AC4b edge: status Objavljeno BEZ kompletnog SR sadržaja (prazan Naziv) → Sačuvaj →
messages.error „Za objavljivanje je potrebno…" + status revert na Skicu (NE „link na polja").

RED: dev_superuser fixture (createsuperuser --noinput env-driven) + axes-flush + e2e_data
command nedostaju dok Dev ne instrumentuje → login/setup pada smisleno (NE collection error).

Idempotentnost (I-3): GREEN conftest mora obrisati/get_or_create-guard-ovati prethodni
`e2e-test-produkt` PRE testa (dokumentovano u interface contract-u — `seed_e2e_data`
ILI dedikovan cleanup u dev_superuser/e2e_data scope-u).
"""

from __future__ import annotations

import pytest
from playwright.sync_api import expect

from tests.e2e.conftest import (
    E2E_PRODUCT_NAME,
    E2E_PRODUCT_NAME_GATE,
    E2E_PRODUCT_SLUG,
    E2E_PRODUCT_SLUG_GATE,
)
from tests.e2e.page_objects import AdminProductPage, ProductDetailPage
from tests.e2e.page_objects.admin_product_page import STATUS_DRAFT, STATUS_PUBLISHED

pytestmark = pytest.mark.e2e


def _login(page, base_url, dev_superuser) -> AdminProductPage:
    admin = AdminProductPage(page, base_url)
    admin.login(dev_superuser["username"], dev_superuser["password"])
    return admin


def test_marijana_creates_and_publishes_product(
    page, base_url, dev_superuser, sample_image_path
):
    """UJ-3 happy path — kreiraj + objavi + appears-on-public (PRIMARNA asercija, AC4)."""
    admin = _login(page, base_url, dev_superuser)

    admin.goto_add()
    admin.fill_core_sr(name_sr=E2E_PRODUCT_NAME, slug=E2E_PRODUCT_SLUG)
    admin.add_inline_specification(section="motor", key="Snaga motora", value="85 KS")
    # Koristi `sample_image_path` fixturu (asertuje da asset postoji → jasan rani fail)
    # umesto direktnog SAMPLE_IMAGE importa koji zaobilazi tu garanciju.
    admin.add_inline_image(sample_image_path)
    admin.set_status(STATUS_PUBLISHED)
    admin.save()
    admin.expect_saved()

    # PRIMARNA ASERCIJA (poslovni signal): proizvod je objavljen i dostupan public-no.
    detail = ProductDetailPage(page, base_url)
    detail.goto(E2E_PRODUCT_SLUG, locale="sr")
    detail.expect_loaded()  # HTTP 200 + product-detail-page vidljiv

    # OPCIONO (AC4) — stock Django admin success poruka (NE „je objavljen" toast).
    # admin.expect_admin_changed_message()  # ostavljeno opciono; primarni signal je iznad


def test_marijana_publish_gate_reverts_to_draft(page, base_url, dev_superuser):
    """UJ-3 edge (AC4b) — Objavljeno bez kompletne galerije/spec → error + revert na Skicu.

    KRITIČNO (interface-contract C-2 realnost): publish-gate u `save_related` fire-uje
    SAMO kad glavna forma validira (super().save_related() se izvrši PRVI). `name_sr` je
    BEZUSLOVNO required na admin formi (ProductAdminForm relax NE relaksira name_sr) — prazan
    name_sr bi pao na FIELD-level required grešku (Django stock errornote) PRE save_related,
    pa „Za objavljivanje je potrebno" NIKAD ne bi bio emitovan i NE bi bilo revert-a.
    Zato edge daje VALIDAN name_sr + slug + brend, ali IZOSTAVLJA inline sliku galerije I
    inline specifikaciju → `save_related` gate puca na `images.count()==0`/`specifications.count()==0`
    → messages.error + QuerySet.update revert OBA flag-a na Skicu (AC4b realno ponašanje).
    """
    admin = _login(page, base_url, dev_superuser)

    admin.goto_add()
    # VALIDAN SR Naziv + ZASEBAN slug (unique=True; happy-path drži `e2e-test-produkt`)
    # + brend (forma validira) — ali BEZ inline slike/spec → gate u save_related puca.
    admin.fill_core_sr(name_sr=E2E_PRODUCT_NAME_GATE, slug=E2E_PRODUCT_SLUG_GATE)
    admin.set_status(STATUS_PUBLISHED)
    admin.save()

    # (a) messages.error substring „Za objavljivanje je potrebno".
    admin.expect_publish_gate_error()
    # (b) save-a revert-ovan na neobjavljeno (re-open forme: status=draft + is_published unchecked).
    # Prosleđujemo IME proizvoda (E2E_PRODUCT_NAME_GATE) jer changelist link tekst je
    # Product.__str__ = name, NE slug (reopen_and_expect_status traži po imenu).
    admin.reopen_and_expect_status(E2E_PRODUCT_NAME_GATE, STATUS_DRAFT)


@pytest.mark.parametrize("locale_tab", ["hu", "en"], ids=["hu-empty", "en-empty"])
def test_marijana_locale_tabs_present(page, base_url, dev_superuser, locale_tab):
    """UJ-3 locale sample (OQ-2) — admin add forma ima per-locale tabove; HU/EN ostaju prazni.

    TranslationAdmin renderuje per-locale polja (name_sr/name_hu/name_en). Sample
    asertuje da HU/EN polje postoji i da je SR primarni unos (locale-only scope —
    NE pun re-publish flow)."""
    admin = _login(page, base_url, dev_superuser)
    admin.goto_add()
    # Per-locale polje za izabrani tab postoji (TranslationAdmin auto-ekspanzija).
    expect(page.locator(f"#id_name_{locale_tab}")).to_have_count(1)
    # SR polje je primarni unos kanal.
    expect(page.locator("#id_name_sr")).to_be_visible()
