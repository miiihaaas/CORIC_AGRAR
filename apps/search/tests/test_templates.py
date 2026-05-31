"""Story 2.13 — AC6/AC7/AC9 templates (dropdown/empty/results) markup (TEA RED).

Pokriva:
- AC6: role=listbox / role=option ARIA, group heading, „Vidi sve" per-grupa testid
  (search-see-all-{group_key}, IMP-6), OOB aria-live guarded {% if request.htmx %} (SM-D14),
  aria-live plural „{n} predloga".
- AC7: empty-state CTA blok, too_short NON-plural poruka (IMP-4), reflected XSS auto-escape
  na FULL search_results.html (title + h1 + href, IMP-5).
- AC9 (static ARIA only): role=listbox/option markup, aria-expanded/aria-controls na toggle
  (vidi test_header_wiring.py), aria-live region. JS-runtime ponašanje (Esc, focus return,
  listbox keyboard nav, slide-in) je MANUAL/Playwright gate — VAN pytest scope-a (§ 9).

⚠️ requires_postgres na testovima koji izvršavaju FTS (rendering rezultata). Pure-markup
empty/too_short/XSS testovi takođe markirani radi konzistentne PG test DB.

Pokrenuti sa:
    docker compose -f compose/local.yml exec django uv run pytest \\
        apps/search/tests/test_templates.py -v

Refs:
- 2-13-global-search-sa-postgresql-fts.md AC6/AC7/AC9 + Task 5 + SM-D3/D14/D16/D18 + IMP-4/5/6
- 2-13-interface-contract.md § 4 (Template surface) + § 7 (data-testid) + § 10 (OOB-GUARD/XSS-REFLECT)
"""

from __future__ import annotations

import pytest
from django.urls import reverse
from django.utils.translation import activate

from apps.search.tests.factories import SearchProductFactory

pytestmark = [pytest.mark.django_db, pytest.mark.requires_postgres]


def _dropdown_url():
    activate("sr")
    return reverse("search:dropdown")


# AC6: dropdown ima <ul role="listbox"> sa testid search-dropdown-list
def test_dropdown_has_listbox_role(client):
    activate("sr")
    SearchProductFactory.create(name_sr="Berba listbox")

    response = client.get(
        _dropdown_url(), {"q": "berba"}, HTTP_HOST="localhost", HTTP_HX_REQUEST="true"
    )
    html = response.content.decode("utf-8")
    assert 'role="listbox"' in html, "Dropdown MORA imati <ul role=\"listbox\"> (AC6)."
    assert 'data-testid="search-dropdown-list"' in html, (
        "Dropdown <ul> MORA imati data-testid=\"search-dropdown-list\" (§7 contract)."
    )


# AC6: svaki rezultat je <li role="option"> sa testid search-option-{slug}
def test_dropdown_options_have_option_role_and_testid(client):
    activate("sr")
    p = SearchProductFactory.create(name_sr="Berba opcija")

    response = client.get(
        _dropdown_url(), {"q": "berba"}, HTTP_HOST="localhost", HTTP_HX_REQUEST="true"
    )
    html = response.content.decode("utf-8")
    assert 'role="option"' in html, "Rezultati MORAJU biti <li role=\"option\"> (AC6/AC9)."
    assert f'data-testid="search-option-{p.slug}"' in html, (
        f"Rezultat MORA imati data-testid=\"search-option-{p.slug}\" (§7 contract)."
    )
    assert p.get_absolute_url() in html, (
        "Option MORA linkovati na product.get_absolute_url()."
    )


# AC6/SM-D16/IMP-6: „Vidi sve" link per-grupa testid search-see-all-proizvodi
def test_see_all_link_per_group_testid(client):
    activate("sr")
    SearchProductFactory.create(name_sr="Berba vidi sve")

    response = client.get(
        _dropdown_url(), {"q": "berba"}, HTTP_HOST="localhost", HTTP_HX_REQUEST="true"
    )
    html = response.content.decode("utf-8")
    assert 'data-testid="search-see-all-proizvodi"' in html, (
        "'Vidi sve' link MORA imati per-grupa testid 'search-see-all-proizvodi' "
        "(IMP-6/SM-D3 forward-compat - NE hardcoded). Epic 5 dodaje search-see-all-objave."
    )
    results_url = reverse("search:results")
    assert results_url in html, (
        "'Vidi sve' MORA voditi ka search:results sa ?q= (SM-D16)."
    )


# AC6/SM-D14: OOB aria-live RENDEROVAN za HTMX request sa pluralnom porukom „N predloga"
def test_oob_aria_live_rendered_for_htmx_with_plural(client):
    activate("sr")
    for i in range(3):
        SearchProductFactory.create(name_sr=f"Berba {i}")

    response = client.get(
        _dropdown_url(), {"q": "berba"}, HTTP_HOST="localhost", HTTP_HX_REQUEST="true"
    )
    html = response.content.decode("utf-8")
    assert "hx-swap-oob" in html, "HTMX dropdown MORA imati OOB div (SM-D14)."
    assert "#aria-live" in html, "OOB div MORA targetovati #aria-live singleton."
    assert "predloga" in html, (
        "OOB aria-live MORA najaviti pluralnu poruku 'N predloga.' (blocktranslate count)."
    )


# AC6/SM-D14: OOB div NIJE renderovan za non-HTMX full render (guard {% if request.htmx %})
def test_oob_not_rendered_on_non_htmx(client):
    activate("sr")
    SearchProductFactory.create(name_sr="Berba non htmx")

    url = reverse("search:results")
    response = client.get(url, {"q": "berba"}, HTTP_HOST="localhost")  # NEMA HX-Request
    html = response.content.decode("utf-8")
    assert "hx-swap-oob" not in html, (
        "Non-HTMX full render NE SME sadržati OOB div (SM-D14 guard {% if request.htmx %}) — "
        "inače bi se renderovao kao plain plutajući tekst."
    )


# AC7: empty-state renderuje poruku „Nema rezultata za ..." + CTA blok
def test_empty_state_message_and_cta(client):
    from apps.brands.tests.factories import BrandFactory, CategoryFactory

    activate("sr")
    CategoryFactory.create(name="Plugovi CTA", display_order=1)
    BrandFactory.create(name="CTA Brend", is_coming_soon=False)

    response = client.get(
        _dropdown_url(), {"q": "nepostojeci"}, HTTP_HOST="localhost", HTTP_HX_REQUEST="true"
    )
    html = response.content.decode("utf-8")
    assert 'data-testid="search-empty-state"' in html, "Empty-state wrapper testid MORA postojati."
    assert "Nema rezultata" in html, "Empty-state MORA prikazati 'Nema rezultata za ...' poruku (AC7)."
    assert "coric-search-empty__cta" in html, "Empty-state MORA imati CTA blok (SM-D18)."


# AC7/IMP-4: too_short slučaj — NON-plural poruka „Unesi makar 2 znaka." BEZ CTA
def test_too_short_non_plural_message_no_cta(client):
    activate("sr")
    response = client.get(
        _dropdown_url(), {"q": "b"}, HTTP_HOST="localhost", HTTP_HX_REQUEST="true"
    )
    html = response.content.decode("utf-8")
    assert "Unesi makar 2 znaka" in html, (
        "too_short MORA prikazati NON-plural 'Unesi makar 2 znaka.' (IMP-4)."
    )
    assert "coric-search-empty__cta" not in html, (
        "too_short slučaj NE SME imati CTA blok (EXPERIENCE.md 248 / IMP-4)."
    )
    assert "predloga" not in html, (
        "too_short NIJE plural count string - NE sme sadrzati 'predloga' (IMP-4 - zaseban msgid)."
    )


# AC7/IMP-5: reflected XSS na FULL search_results.html — title/h1 escaped, href urlencoded
def test_reflected_xss_escaped_on_full_results_page(client):
    activate("sr")
    url = reverse("search:results")
    payload = "<script>alert(1)</script>"

    response = client.get(url, {"q": payload}, HTTP_HOST="localhost")
    html = response.content.decode("utf-8")

    assert "<script>alert(1)</script>" not in html, (
        "Reflected query NE SME biti renderovan kao izvršiv <script> (XSS — IMP-5). "
        "Django auto-escape MORA biti ON; NIKAD |safe na query."
    )
    assert "&lt;script&gt;" in html, (
        "Query MORA biti auto-escaped (&lt;script&gt;) u title/h1 (IMP-5)."
    )


# AC7/IMP-5: reflected XSS — query u HREF kontekstu MORA biti urlencoded (%3Cscript%3E)
def test_reflected_xss_urlencoded_in_href(client):
    activate("sr")
    payload = "<script>x</script>"

    # Full strana echo-uje query u „Vidi sve"/refine href (?q={{ query|urlencode }}).
    # Da href postoji MORA biti ≥1 rezultat — renderuj rezultat čiji name matchuje query
    # token „berba" (payload se reflektuje samo u href, ne u rezultatu).
    SearchProductFactory.create(name_sr="Berba href rezultat")
    full = client.get(
        reverse("search:results"), {"q": f"berba {payload}"}, HTTP_HOST="localhost"
    )
    full_html = full.content.decode("utf-8")
    # Query MORA biti reflektovan u href kao urlencoded token (q=...%3Cscript%3E...),
    # NIKAD golo ni samo HTML-escaped u URL kontekstu (IMP-5 — {{ query|urlencode }}).
    assert "q=" in full_html, (
        "Full results strana MORA echo-ovati query u see-all/refine href (?q=...); "
        "bez href-a IMP-5 urlencode kontekst nije pokriven."
    )
    assert "%3Cscript%3E" in full_html or "%3cscript%3e" in full_html, (
        "Query u HREF/URL kontekstu MORA biti urlencoded (%3Cscript%3E), NE golo "
        "ni samo HTML-escaped (IMP-5 — {{ query|urlencode }})."
    )


# AC3/SM-D16: results strana ima JEDAN <h1> (single-h1 regression guard mirror 2.8)
def test_results_page_single_h1(client):
    activate("sr")
    SearchProductFactory.create(name_sr="Berba h1")

    response = client.get(
        reverse("search:results"), {"q": "berba"}, HTTP_HOST="localhost"
    )
    html = response.content.decode("utf-8").lower()
    assert html.count("<h1") == 1, (
        f"search_results.html MORA imati TAČNO JEDAN <h1> (single-h1 guard), dobio "
        f"{html.count('<h1')}."
    )
