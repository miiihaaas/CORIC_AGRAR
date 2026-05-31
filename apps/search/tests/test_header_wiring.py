"""Story 2.13 — AC5/AC9 header.html search-toggle wiring (TEA RED phase).

Pokriva AC5 + AC9 (static markup contract — NE JS runtime):
- search button (Story 1.8 deferred IMP-3) dobija aria-expanded="false" +
  aria-controls="coric-search-panel" + data-search-toggle,
- regression: NE ukloni postojeći aria-label / SVG,
- panel mount #coric-search-panel sa <form hx-get> + <input type=search minlength=2>
  + #coric-search-results target (testid search-results-container) + htmx-indicator,
- GET-only (NEMA csrf_token u search formi, SM-D17).

⚠️ JS-runtime ponašanje (Esc-to-close, focus return, click-outside, listbox keyboard nav,
slide-in animacija, prefers-reduced-motion) je MANUAL smoke / Playwright Story 9.8 —
VAN pytest scope-a (interface-contract § 9). Ovde se asertuje SAMO statički ARIA markup.

NE markirano requires_postgres — ovaj test renderuje samo header partial (nema FTS),
ali zahteva da je apps.search instaliran (URL reverse za hx-get) → pada u RED fazi.

Pokrenuti sa:
    docker compose -f compose/local.yml exec django uv run pytest \\
        apps/search/tests/test_header_wiring.py -v

Refs:
- 2-13-global-search-sa-postgresql-fts.md AC5/AC9 + Task 6 + SM-D12
- 2-13-interface-contract.md § 4 (header.html) + § 5 (JS surface) + § 10 (HDR-WIRE)
"""

from __future__ import annotations

import re

import pytest
from django.template.loader import render_to_string
from django.test import RequestFactory
from django.utils.translation import activate

pytestmark = pytest.mark.django_db


def _render_header():
    """Renderuje header partial sa minimalnim request context-om (LocaleMiddleware-style)."""
    activate("sr")
    request = RequestFactory().get("/sr/")
    return render_to_string("partials/header.html", request=request)


def _search_toggle_button(html: str) -> str:
    """Izoluje SAMO <button class="...coric-nav__search-toggle..."> element.

    KRITIČNO: header već ima DRUGE button-e sa aria-expanded (top-header mobile
    toggle, hamburger, mehanizacija dropdown). Substring check na celom HTML-u bi
    lažno prošao. Asercije moraju biti scope-ovane na search-toggle button TAG.
    """
    match = re.search(
        r"<button\b[^>]*coric-nav__search-toggle[^>]*>", html, re.IGNORECASE | re.DOTALL
    )
    assert match, "header.html MORA sadržati <button class='...coric-nav__search-toggle...'>."
    return match.group(0)


# AC5/SM-D12: search button dobija data-search-toggle atribut
def test_search_toggle_button_has_data_attribute():
    button = _search_toggle_button(_render_header())
    assert "data-search-toggle" in button, (
        "search-toggle button MORA dobiti `data-search-toggle` atribut (SM-D12). "
        f"Button tag: {button!r}."
    )


# AC5/SM-D12: search button dobija aria-expanded="false" (initial)
def test_search_toggle_button_has_aria_expanded():
    button = _search_toggle_button(_render_header())
    # Scope na search-toggle button TAG — Story 1.8 IMP-3 ga NIJE imao (drugi button-i jesu).
    assert 'aria-expanded="false"' in button, (
        "search-toggle button MORA dobiti aria-expanded=\"false\" (AC5/SM-D12). "
        "Story 1.8 IMP-3 ga je NAMERNO ostavio bez wiring-a — Story 2.13 wire. "
        f"Button tag: {button!r}."
    )


# AC5/SM-D12: aria-controls="coric-search-panel"
def test_search_toggle_button_has_aria_controls():
    button = _search_toggle_button(_render_header())
    assert 'aria-controls="coric-search-panel"' in button, (
        "search-toggle button MORA imati aria-controls=\"coric-search-panel\" (SM-D12). "
        f"Button tag: {button!r}."
    )


# AC5 regression: postojeći aria-label NE sme biti uklonjen — MORA koegzistirati sa wiring-om
def test_search_toggle_button_keeps_aria_label():
    button = _search_toggle_button(_render_header())
    # Asertuj da SAME button tag ima i postojeći aria-label I novi data-search-toggle —
    # genuinely fails u RED (data-search-toggle ne postoji još), a štiti aria-label od
    # uklanjanja u GREEN (HDR-WIRE regression).
    assert "Otvori pretragu" in button, (
        "Postojeci aria-label 'Otvori pretragu' (Story 1.8) NE SME biti uklonjen sa "
        f"search-toggle button-a (HDR-WIRE regression). Button tag: {button!r}."
    )
    assert "data-search-toggle" in button, (
        "Isti search-toggle button MORA imati i novi data-search-toggle hook (koegzistencija "
        f"sa aria-label, ne zamena). Button tag: {button!r}."
    )


# AC5/SM-D12: panel mount #coric-search-panel sa hidden atributom
def test_search_panel_mount_exists_hidden():
    html = _render_header()
    assert 'id="coric-search-panel"' in html, (
        "header.html MORA dodati panel mount <div id=\"coric-search-panel\"> (SM-D12)."
    )
    assert "hidden" in html, "Panel MORA biti inicijalno hidden (SM-D12)."


# AC5/SM-D12: form ima hx-get + hx-trigger debounce 300ms + hx-target #coric-search-results
def test_search_form_htmx_attributes():
    html = _render_header()
    assert "hx-get" in html, "Search forma MORA imati hx-get (SM-D12)."
    assert "keyup changed delay:300ms" in html, (
        "Search forma MORA imati hx-trigger=\"keyup changed delay:300ms\" (debounce, SM-D15)."
    )
    assert 'hx-target="#coric-search-results"' in html, (
        "Search forma MORA imati hx-target=\"#coric-search-results\" (SM-D12)."
    )


# AC5/SM-D12: input type=search name=q minlength=2 autocomplete=off
def test_search_input_attributes():
    html = _render_header()
    assert 'type="search"' in html, "Input MORA biti type=\"search\" (SM-D12)."
    assert 'name="q"' in html, "Input MORA imati name=\"q\" (SM-D12)."
    assert 'minlength="2"' in html, "Input MORA imati minlength=\"2\" (SM-D13 UX layer)."
    assert 'autocomplete="off"' in html, "Input MORA imati autocomplete=\"off\" (SM-D12)."


# AC6/SM-D12: dropdown target #coric-search-results (testid search-results-container)
def test_search_results_target_exists():
    html = _render_header()
    assert 'id="coric-search-results"' in html, (
        "HTMX target <div id=\"coric-search-results\"> MORA postojati u header.html (SM-D12)."
    )
    assert 'data-testid="search-results-container"' in html, (
        "HTMX target MORA imati data-testid=\"search-results-container\" (§7 contract)."
    )


# AC5/SM-D17: GET-only — search forma NEMA csrf_token (read-only query)
def test_search_form_has_no_csrf_token():
    html = _render_header()
    # KRITIČNO (mirror _search_toggle_button scoping): header VEĆ sadrži legitiman
    # csrf_token iz language_switcher_nav.html (Story 1.8 set_language POST forma).
    # Substring check na celom HTML-u bi lažno pao. Scope na #coric-search-panel
    # mount (SM-D12) — TU search GET forma ne sme imati csrf_token (SM-D17).
    match = re.search(
        r'<div\b[^>]*id="coric-search-panel".*?</div>\s*</li>',
        html,
        re.IGNORECASE | re.DOTALL,
    )
    assert match, "header.html MORA sadržati #coric-search-panel mount (SM-D12)."
    panel = match.group(0)
    assert "csrfmiddlewaretoken" not in panel, (
        "Search forma je GET (read-only) — NEMA {% csrf_token %} (SM-D17)."
    )
