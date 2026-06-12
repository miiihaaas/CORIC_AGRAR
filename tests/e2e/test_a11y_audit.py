"""Story 9.9 — A11y audit spec (axe-core) = RED-faza AUDIT-GATE kontrakt.

SPECIJALNA story: deliverable je AUDIT/QUALITY TOOLING, NE Django app/feature i NE
novi user-journey. Ovaj spec NIJE 4. user-journey — to je `axe` audit-gate koji
skenira ključne strane na WCAG 2.1 AA violacije. Markiran ZASEBNIM `a11y` markerom
(NE `e2e`) da `just test` / `just e2e` / `just a11y` budu tri nezavisne suite
(`needs_e2e=false`, `e2e_count=0`; SM-D8 / AC1 / AC9).

REUSE 9-8 harness (NE reimplementira): `tests/e2e/conftest.py` fixtures (`base_url`,
`e2e_data`/`seed_e2e_data`, `dev_superuser`) + page objects (`TraktoriListingPage`,
`AdminProductPage`). Audit cilja iste determinističke 9-7 seed slug-ove
(`agri-tracking-tb804`, traktori listing, blog post `pet-saveta-za-prolecnu-setvu`,
kontakt forma, `/admin-coric/`) — SM-D9.

------------------------------------------------------------------------------------
RED SIGNAL (OČEKIVANO — NE „green na ovom hostu"):
------------------------------------------------------------------------------------
Ovaj spec NAMERNO NE prolazi na native Windows host-u jer:
  1. axe runner dep (`axe-playwright-python`) NIJE instaliran još (Dev: `uv add --dev`).
  2. Playwright browser binarije + libmagic baseline (dokumentovan kroz Epik 9) se NE
     izvršavaju na Win hostu.
Import `from axe_playwright_python.sync_playwright import Axe` baca ModuleNotFoundError
pri collect-u → collection ERROR. To JE očekivani RED signal (struktura validna, dep
nedostaje). GREEN je CI/staging posao (AC11): Dev instalira dep + ožiči lighthouse.yml
self-contained job tako da `axe.run()` vrati realan result objekat bar jednom.
Fabrikovan green je ZABRANJEN — iskrenost iznad zelene (AC8).

CAVEAT OČUVAN: ovo je CI-job zahtev, NE Win-host zahtev. Autoritativno a11y merenje je
staging/CI (OQ-1..OQ-4). Win host (libmagic + browser) NE pokreće — i to je by design.
"""

from __future__ import annotations

import pytest

# --- axe runner (RED: dep NIJE instaliran još → ModuleNotFoundError pri collect-u) ---
# `axe-playwright-python` izlaže `Axe().run(page)` koji injektuje axe.min.js i poziva
# axe.run() (vraća rezultat sa .response = { violations, passes, incomplete, inapplicable }).
# Dev (Task 1.1): `uv add --dev axe-playwright-python` + `uv lock --native-tls`.
# Fallback (Dev Notes): `npm i -D axe-core` → vendor node_modules/axe-core/axe.min.js u
# tests/e2e/assets/ + page.add_script_tag(path=...) + page.evaluate("axe.run(...)").
from axe_playwright_python.sync_playwright import Axe  # noqa: E402

from playwright.sync_api import expect  # noqa: E402

# TraktoriListingPage je import-ovan za DOKUMENTOVANU AC2b traktori-filter alternativu
# (copy-paste-ready snippet niže) — nije aktivno korišćen → eksplicitan noqa F401.
from tests.e2e.page_objects import (  # noqa: E402
    AdminProductPage,
    TraktoriListingPage,  # noqa: F401
)

# AC1 — ZASEBAN `a11y` marker (NE `e2e`). Registruje se u pyproject.toml
# [tool.pytest.ini_options].markers (Dev — Task 1.2); addopts → `-m 'not e2e and not a11y'`.
pytestmark = pytest.mark.a11y


# =============================================================================
# WCAG 2.1 AA konfiguracija + impact gate
# =============================================================================
# AC2 — axe se konfiguriše na WCAG 2.1 AA tagove (4 taga). Filter `violations` po
# impact-u: `critical`+`serious` = gate (fail); `moderate`/`minor` = loguj, NE fail
# (SM-D2 baseline pragmatizam → AUDIT-REPORT remediation Issue).
WCAG_21_AA_TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]
GATE_IMPACTS = {"critical", "serious"}

# AC2-e — TAČAN deterministički blog slug (9-7 seed `_BLOG_POSTS[0].slug`). 404 (pogrešan
# slug) = false-pass (axe ne nađe violation jer nema sadržaja) → MORA gađati ovaj URL.
BLOG_POST_SLUG = "pet-saveta-za-prolecnu-setvu"
PRODUCT_SLUG = "agri-tracking-tb804"


def _run_axe(page) -> object:
    """Injektuj axe + pokreni WCAG 2.1 AA analizu na TRENUTNOM DOM-u → vrati result.

    `axe.run(page, options=...)` injektuje axe.min.js u stranicu i izvrši axe.run() sa
    `runOnly` tag filterom. Vraća `AxeResults` čiji `.response` nosi standardni axe
    payload ({ violations, passes, incomplete, inapplicable }). AC11(b): ovo VRAĆA
    realan result objekat (NE fabrikovano „prošlo").

    NB (axe-playwright-python 0.1.7 API): `run(page, context=None, options=...)`.
    Prosleđivanjem `options={"runOnly": ...}` NAMERNO override-ujemo built-in
    `DEFAULT_OPTIONS={"resultTypes":["violations"]}` — bez `resultTypes`, axe-core vraća
    PUN result (sve 4 sekcije: violations/passes/incomplete/inapplicable), tačno objekat
    koji AC11(b) zahteva. Filter na impact (critical/serious) radimo mi u _gate_violations.
    """
    axe = Axe()
    return axe.run(
        page,
        options={"runOnly": {"type": "tag", "values": WCAG_21_AA_TAGS}},
    )


def _gate_violations(result) -> list:
    """Izdvoji SAMO `critical`+`serious` impact violacije (gate set; SM-D2)."""
    violations = result.response.get("violations", [])
    return [v for v in violations if v.get("impact") in GATE_IMPACTS]


def _format_report(result) -> str:
    """Čitljiv izveštaj za assert poruku (strana + rule id + impact + WCAG tagovi).

    Daje Dev-u/audit-report-u konkretne nalaze umesto golog count-a. `moderate`/`minor`
    se OVDE logују (vidljivi u fail outputu / -v), ali NE ulaze u gate (_gate_violations).
    """
    lines = []
    for v in result.response.get("violations", []):
        lines.append(
            f"  [{v.get('impact')}] {v.get('id')} — {v.get('help')} "
            f"(tagovi: {','.join(v.get('tags', []))}; nodes: {len(v.get('nodes', []))})"
        )
    return "\n".join(lines) if lines else "  (nema violacija)"


def _assert_no_gate_violations(result, page_label: str) -> None:
    """AC2 gate: 0 `critical`/`serious` violacija na strani.

    Poruka uvek štampa PUN izveštaj (uklj. moderate/minor — log, ne fail) da nalazi
    odu u AUDIT-REPORT, a fail signal ostane na critical/serious.
    """
    gate = _gate_violations(result)
    assert not gate, (
        f"A11y gate FAIL na '{page_label}': "
        f"{len(gate)} critical/serious WCAG 2.1 AA violacija.\n"
        f"Pun axe izveštaj (moderate/minor se LOGUJU, NE fail-uju — SM-D2):\n"
        f"{_format_report(result)}"
    )


# =============================================================================
# AC2 (a–e) — STATIČKI axe sken JAVNIH ključnih strana (parametrize po URL-u)
# =============================================================================
# Svaka strana = zaseban parametrize case (test-izolacija; jedan fail ne maskira drugi).
# Admin (f) je ODVOJEN test (login-gated → dev_superuser fixture; SM-D3).
PUBLIC_AUDIT_PAGES = [
    # 9.9 review fix: kanonski `/sr/` (NE `/` koje radi 302→/sr/ via prefix_default_language)
    # — izbegava redirect-latency u TTFB merenju + konzistentno sa ostalim /sr/ URL-ovima.
    pytest.param("/sr/", id="home"),
    pytest.param("/sr/traktori/", id="traktori-listing"),
    pytest.param(f"/sr/proizvod/{PRODUCT_SLUG}/", id="product-detail-tb804"),
    pytest.param("/sr/kontakt/", id="kontakt-forma"),
    pytest.param(f"/sr/blog/{BLOG_POST_SLUG}/", id="blog-post-detail"),
]


@pytest.mark.parametrize("path", PUBLIC_AUDIT_PAGES)
def test_a11y_public_page(page, base_url, e2e_data, path):
    """AC2 (a–e) — statički axe WCAG 2.1 AA sken javnih strana, 0 critical/serious gate.

    Blog case gađa TAČAN deterministički slug (NE „npr."): 404 bi dao false-pass.
    """
    page.goto(base_url + path)
    result = _run_axe(page)
    _assert_no_gate_violations(result, page_label=path)


# =============================================================================
# AC2 (f) — admin strana (login-gated; dev_superuser fixture + AdminProductPage.login)
# =============================================================================
def test_a11y_admin_login_gated(page, base_url, dev_superuser):
    """AC2 (f) — axe sken `/admin-coric/` u AUTENTIKOVANOM kontekstu.

    Login preko POSTOJEĆE `AdminProductPage.login()` (realna metoda, LOGIN_PATH
    `/admin-coric/login/`) — kredencijali iz `dev_superuser` fixture-a (env-driven,
    NIKAD hardkodovan; axes-flush dolazi BESPLATNO kroz fixture — conftest:162).
    Admin JESTE u axe skenu (form labels vrednost), ali VAN Lighthouse perf budgeta
    (SM-D3 — login-gated, tuđi Django admin static markup nije javni LCP target).
    """
    admin = AdminProductPage(page, base_url)
    admin.login(dev_superuser["username"], dev_superuser["password"])
    # Posle login-a smo na admin index-u (#user-tools vidljiv — login() to već asertuje).
    result = _run_axe(page)
    _assert_no_gate_violations(result, page_label="/admin-coric/")


# =============================================================================
# AC2b — axe sken POSLE HTMX swap-a (dinamički DOM, NE samo initial load) — EDGE CASE
# =============================================================================
def test_a11y_after_htmx_swap(page, base_url, e2e_data):
    """AC2b — axe POSLE HTMX form-swap-a (kontakt forma) skenira RE-renderovani DOM.

    RAZLOG (project-context #1 OOB aria-live + #3 focus management posle HTMX swap-a =
    NAJVEĆI a11y rizik projekta): static-load axe NE vidi dinamički ubačen markup, pa
    OOB aria-live regioni + post-swap fragment ostaju nepokriveni ako se skenira samo
    prva boja. Ovaj case obezbeđuje da axe vidi i swap-ovani DOM.

    Tok: `/sr/kontakt/` → popuni + submit kontakt formu (hx-post → #contact-form-section,
    hx-swap=outerHTML) → ČEKAJ HTMX-settled (success kartica `role="status"` vidljiva,
    Playwright auto-wait, NEMA sleep) → axe.run() na POST-SWAP DOM-u.

    Gate je isti (0 critical/serious). Keyboard/fokus-traversal posle swap-a ostaje
    MANUAL (AC6b checklist) — ovaj case hvata STATIČKE post-swap WCAG violacije.
    """
    page.goto(base_url + "/sr/kontakt/")

    # Popuni 3 obavezna polja (name/email/message) — telefon opcioni — i submit.
    page.locator("#contact-name").fill("Ana Anić")
    page.locator("#contact-email").fill("ana@example.com")
    page.locator("#contact-message").fill(
        "Zainteresovana sam za ponudu, molim kontakt."
    )
    page.get_by_test_id("contact-submit").click()

    # ČEKAJ HTMX-settled: success swap zamenjuje #contact-form-section outerHTML success
    # partial-om sa `<p ... role="status">` (contact_success.html). Auto-wait, NEMA sleep.
    expect(page.locator("#contact-form-section .coric-contact-form__success")).to_be_visible()

    # axe SKENIRA dinamički swap-ovani DOM (OOB aria-live + success fragment).
    result = _run_axe(page)
    _assert_no_gate_violations(result, page_label="/sr/kontakt/ (post-HTMX-swap)")


# =============================================================================
# AC2b (alternativa, dokumentovana) — traktori HTMX filter swap
# =============================================================================
# Story dozvoljava AC2b preko traktori filter submit-a ILI forme. Kontakt-forma
# (test iznad) je PRIMARNI AC2b case (deterministična, bez file-upload-a, OOB aria-live
# eksplicitan). Traktori-filter varijanta je dostupna preko `TraktoriListingPage`
# (`filter_by_snaga_min` → HTMX innerHTML swap `#tractor-results`) ako se želi DRUGI
# post-swap DOM; držimo je kao DOKUMENTOVANU opciju (NE drugi aktivan case da se ne
# duplira gate bez dodatne pokrivenosti):
#
#   listing = TraktoriListingPage(page, base_url)
#   listing.goto(locale="sr")
#   listing.filter_by_snaga_min(61)            # HTMX swap #tractor-results
#   listing.expect_card_present("agri-tracking-tb804")  # HTMX-settled guard
#   result = _run_axe(page)
#   _assert_no_gate_violations(result, page_label="/sr/traktori/ (post-filter-swap)")
#
# `TraktoriListingPage` je import-ovan iznad (sa eksplicitnim F401 noqa direktivom na
# import liniji) da ova grana ostane copy-paste-ready za Dev-a bez ruff F401 šuma.
