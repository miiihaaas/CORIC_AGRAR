"""Page Object — Django admin Product CRUD (/admin-coric/) — UJ-3, AC5.

Admin je na `/admin-coric/` (Epic 8-1 hardening, VAN i18n prefiksa). Koristi
STABILNE Django admin selektore (`#id_*` polja, `.messagelist`, `.errornote`) —
NE dodajemo data-testid u admin osim ako se markup pokaže nestabilnim (Task 6 NAPOMENA).

Product je TranslationAdmin → SR polja su `id_name_sr` / `id_description_sr`.
Status: `id_status` (<select>, choices draft/published/archived) + `id_is_published`.
Inline galerija: `id_images-0-image` (ProductImage formset, prefix `images`).
Inline spec: `id_specifications-0-section` / `-key` / `-value` (prefix `specifications`).

Publish-gate (Epic 8-6, AC4/AC4b): status `Objavljeno` BEZ (SR Naziv ∨ ≥1 slika
∨ ≥1 spec) → `save_related` emituje `messages.error("Za objavljivanje je potrebno…")`
+ `QuerySet.update()` revert na Skicu. NEMA „je objavljen" toast (C-2).

RED zavisnost: dev_superuser fixture (createsuperuser --noinput, env-driven) NE
postoji još → login pada. Bez axes-flush (Task 2.4) login može flap-ovati lockout.
"""

from __future__ import annotations

from pathlib import Path

from playwright.sync_api import Page, expect

# Publish-gate error substring (REALNO, AC4b — `save_related` messages.error).
PUBLISH_GATE_ERROR_SUBSTRING = "Za objavljivanje je potrebno"
# OPCIONO + LOCALE-FRAGILE: stock Django admin „...successfully" substring. Pada pod
# srpski-lokalizovanim admin-om (msgstr nije „successfully"). Koristi se SAMO u
# komentarisanoj opcionoj aserciji (expect_admin_changed_message) — PRIMARNI AC4
# signal je appears-on-public (test_marijana_*), koji je locale-robustan i aktivan.
ADMIN_CHANGED_SUBSTRING = "successfully"

STATUS_DRAFT = "draft"
STATUS_PUBLISHED = "published"

# Determinističan seed brend (9-7 seed_sample_data: slug="agri-tracking", name="Agri
# Tracking"). Brend <select> renderuje opcije po Brand.__str__ == name, pa biramo po
# labeli — otporno na dodate brendove (NE order-dependent index).
SEED_BRAND_LABEL = "Agri Tracking"


class AdminProductPage:
    LOGIN_PATH = "/admin-coric/login/"
    ADD_PATH = "/admin-coric/products/product/add/"
    CHANGELIST_PATH = "/admin-coric/products/product/"

    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url

    # -- auth -----------------------------------------------------------------

    def login(self, username: str, password: str) -> None:
        """Login na /admin-coric/. Axes-flush (Task 2.4) je conftest odgovornost PRE ovog poziva."""
        self.page.goto(self.base_url + self.LOGIN_PATH)
        # Django admin login: #id_username + #id_password.
        self.page.locator("#id_username").fill(username)
        self.page.locator("#id_password").fill(password)
        self.page.locator('input[type="submit"]').click()
        # Po uspehu — admin index (#user-tools ili #content) vidljiv.
        expect(self.page.locator("#user-tools")).to_be_visible()

    # -- create ---------------------------------------------------------------

    def goto_add(self) -> None:
        self.page.goto(self.base_url + self.ADD_PATH)
        expect(self.page.locator("#product_form")).to_be_visible()

    def fill_core_sr(
        self,
        *,
        name_sr: str,
        slug: str,
        brand_label: str = SEED_BRAND_LABEL,
    ) -> None:
        """Popuni SR Naziv + slug + izaberi brend (HU/EN prazno — AC4)."""
        self.page.locator("#id_name_sr").fill(name_sr)
        # prepopulated_fields {"slug": ("name",)} puni slug iz baznog `name`; mi ga
        # postavljamo EKSPLICITNO da slug bude deterministički `e2e-test-produkt`.
        slug_input = self.page.locator("#id_slug")
        slug_input.fill(slug)
        # Brend je obavezan FK <select id_brand>. Biraj DETERMINISTIČKI po labeli seed
        # brenda (Brand.__str__ == name == "Agri Tracking") umesto po index-u — otporno
        # na dodate brendove koji bi pomerili redosled opcija (NE order-dependent).
        self.page.locator("#id_brand").select_option(label=brand_label)

    def _add_inline_row(self, group_id: str) -> None:
        """Klikni Django admin „Add another" link da materijalizuje inline red 0.

        KRITIČNO: svi Product inline-ovi su `extra = 0` (apps/products/admin.py) →
        add forma NEMA praznih inline redova; `#id_<prefix>-0-*` polja NE postoje dok
        se ne klikne add-row link (Django dynamic inline JS kreira red 0 + ažurira
        TOTAL_FORMS). Tek POSLE ovog klika su `-0-` polja u DOM-u.

        Idempotentno-ish: zovi jednom po redu. `tr.add-row a` je stock Django selektor
        unutar inline grupe `#<prefix>-group` (TabularInline).
        """
        add_link = self.page.locator(f"#{group_id} tr.add-row a")
        add_link.click()

    def add_inline_specification(
        self, *, section: str = "motor", key: str, value: str
    ) -> None:
        """Materijalizuj + popuni prvi ProductSpecification inline red (prefix `specifications`).

        Spec inline je `extra=0` → prvo klikni add-row, pa popuni `-0-` polja.
        `key`/`value` su per-locale (TranslationTabularInline) → `key_sr`/`value_sr`.
        """
        self._add_inline_row("specifications-group")
        self.page.locator("#id_specifications-0-section").select_option(section)
        self.page.locator("#id_specifications-0-key_sr").fill(key)
        self.page.locator("#id_specifications-0-value_sr").fill(value)

    def add_inline_image(self, file_path: Path) -> None:
        """Materijalizuj + priloži ≥1 ProductImage galeriju (prefix `images`, extra=0)."""
        self._add_inline_row("images-group")
        self.page.locator("#id_images-0-image").set_input_files(str(file_path))

    def set_status(self, status: str) -> None:
        """Postavi status select (draft/published). Publish takođe može tražiti is_published."""
        self.page.locator("#id_status").select_option(status)
        if status == STATUS_PUBLISHED:
            checkbox = self.page.locator("#id_is_published")
            if not checkbox.is_checked():
                checkbox.check()

    def save(self) -> None:
        # Standardni admin save dugme.
        self.page.locator('input[name="_save"]').click()

    # -- asercije -------------------------------------------------------------

    def expect_saved(self) -> None:
        """Save uspeo → changelist sa `.messagelist` success porukom."""
        expect(self.page.locator(".messagelist")).to_be_visible()

    def expect_admin_changed_message(self) -> None:
        # OPCIONO + LOCALE-FRAGILE (AC4) — stock Django „...was changed/added successfully".
        # Pada pod srpski-lokalizovanim admin-om; PRIMARNI AC4 signal je appears-on-public.
        # Drži se zbog komentarisane opcione asercije u test_marijana_* (ne aktivira se default).
        expect(self.page.locator(".messagelist")).to_contain_text(ADMIN_CHANGED_SUBSTRING)

    def expect_publish_gate_error(self) -> None:
        """AC4b — messages.error substring „Za objavljivanje je potrebno"."""
        expect(self.page.locator(".messagelist")).to_contain_text(
            PUBLISH_GATE_ERROR_SUBSTRING
        )

    def reopen_and_expect_status(self, name_in_list: str, expected_status: str) -> None:
        """Re-open change forme i potvrdi da je status posle revert-a na očekivanoj vrednosti.

        AC4b: posle neuspele objave revert-ovani su OBA publish flag-a na neobjavljeno:
        `status` → Skica (`draft`) I `is_published` → False (admin save_related dual-revert).

        `name_in_list` je tekst changelist linka — to je IME proizvoda (Product.__str__ =
        name), NE slug. Django changelist renderuje `__str__` kao link, pa get_by_role
        traži po imenu, a NE po slug-u (prosleđivanje slug konstante bi tiho promašilo).
        """
        self.page.goto(self.base_url + self.CHANGELIST_PATH)
        # Klik na changelist link (tekst = ime proizvoda, Product.__str__ = name).
        self.page.get_by_role("link", name=name_in_list).first.click()
        # (a) status select revert-ovan na očekivanu vrednost (draft).
        expect(self.page.locator("#id_status")).to_have_value(expected_status)
        # (b) AC4b dual-revert: is_published checkbox NIJE čekiran (#id_is_published je
        # na change formi — fieldsets „Status i parametri", apps/products/admin.py).
        expect(self.page.locator("#id_is_published")).not_to_be_checked()
