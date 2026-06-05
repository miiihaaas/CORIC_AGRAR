"""Story 5.2 — Category filter + HTMX (AC5) — TEA RED phase.

Pokriva AC5 (SM-D4/SM-D5 / Gotcha BL2-2 / IMP-3):
  - ?kategorija=<slug> → SAMO objave te kategorije (category__slug filter)
  - „Sve kategorije" (prazan slug) → sve published
  - HTMX request (HX-Request: true) → _post_results.html partial (NE full page chrome)
  - guarded OOB aria-live count („Pronađeno N objava") SAMO na HTMX (Gotcha BL2-2)
  - non-HTMX → full page + selected dropdown (deep-link)
  - invalid ?kategorija=nepostoji → 0 rezultata + empty (NE 404); active_filters normalizovan na "" (IMP-3)
  - vary_on_headers("HX-Request") → Vary: HX-Request u response
  - TAČNO JEDAN id="blog-results" (unutar partiala)

Simulacija HTMX: client.get(..., HTTP_HX_REQUEST="true") → django-htmx middleware
postavlja request.htmx=True.

⚠️ GUARD: apps.blog importi UNUTAR funkcija. REUSE conftest make_post/make_category.

Refs:
- 5-2-...-filter.md AC5 + Task 8.6 + SM-D4/D5 + Gotcha BL2-2 + IMP-3
- apps/products/tests/test_used_machinery_htmx.py (HTMX test precedent)
"""

from __future__ import annotations

import re

import pytest
from django.utils import timezone
from django.utils.translation import activate

pytestmark = pytest.mark.django_db


def _published(make_post, **overrides):
    defaults = {
        "status": "published",
        "published_at": timezone.now() - timezone.timedelta(days=1),
    }
    defaults.update(overrides)
    return make_post(**defaults)


# AC5: ?kategorija=<slug> filtrira na tu kategoriju
def test_filter_by_category_slug(client, make_post, make_category):
    activate("sr")
    ratarstvo = make_category(name="Ratarstvo")
    stocarstvo = make_category(name="Stočarstvo")

    in_cat = _published(make_post, title="Ratarska priča", category=ratarstvo)
    out_cat = _published(make_post, title="Stočarska priča", category=stocarstvo)

    response = client.get(
        f"/sr/blog/?kategorija={ratarstvo.slug}", HTTP_HOST="localhost"
    )

    assert response.status_code == 200
    pks = {p.pk for p in response.context["posts"]}
    assert in_cat.pk in pks, (
        f"Objava u kategoriji {ratarstvo.slug!r} (pk={in_cat.pk}) MORA biti u listi."
    )
    assert out_cat.pk not in pks, (
        f"Objava DRUGE kategorije (pk={out_cat.pk}) NE SME biti u filtriranoj listi."
    )


# AC5 / SM-D2 / Gotcha BL2-1: DRAFT-NOT-LEAKED na FILTRIRANOJ putanji
# Dokazuje da category filter chain-uje OFF Post.published — draft u FILTRIRANOJ
# kategoriji ostaje skriven (filter NE „otključava" draft). Root-queryset 4-state
# je u test_blog_index_view.py; ovde eksplicitno na filtriranoj grani (security).
def test_filter_does_not_leak_draft_in_filtered_category(
    client, make_post, make_category
):
    activate("sr")
    ratarstvo = make_category(name="Ratarstvo")

    published = _published(
        make_post, title="Objavljena žetva pšenice", category=ratarstvo
    )
    draft = make_post(
        title="Nacrt o đubrenju njive",
        status="draft",
        published_at=None,
        category=ratarstvo,
    )

    response = client.get(
        f"/sr/blog/?kategorija={ratarstvo.slug}", HTTP_HOST="localhost"
    )

    assert response.status_code == 200
    pks = {p.pk for p in response.context["posts"]}
    assert published.pk in pks, (
        f"PUBLISHED objava u filtriranoj kategoriji {ratarstvo.slug!r} "
        f"(pk={published.pk}) MORA biti vidljiva."
    )
    assert draft.pk not in pks, (
        f"DRAFT u ISTOJ filtriranoj kategoriji (pk={draft.pk}) NE SME procuriti — "
        f"category filter chain-uje OFF Post.published (NE Post.objects; SM-D2). "
        f"Dobili: {pks!r}."
    )
    # Existence-oracle guard: draft title/slug NE SME biti u rendered response body
    html = response.content.decode("utf-8")
    assert draft.title not in html, (
        f"DRAFT naslov {draft.title!r} NE SME biti renderovan u filtriranom response-u."
    )
    assert f"/blog/{draft.slug}/" not in html, (
        f"DRAFT slug {draft.slug!r} NE SME biti renderovan (link) u filtriranom response-u."
    )


# AC5: „Sve kategorije" (prazan slug) → sve published
def test_filter_empty_slug_shows_all(client, make_post, make_category):
    activate("sr")
    ratarstvo = make_category(name="Ratarstvo")
    stocarstvo = make_category(name="Stočarstvo")
    a = _published(make_post, title="A priča", category=ratarstvo)
    b = _published(make_post, title="B priča", category=stocarstvo)

    response = client.get("/sr/blog/?kategorija=", HTTP_HOST="localhost")

    assert response.status_code == 200
    pks = {p.pk for p in response.context["posts"]}
    assert a.pk in pks and b.pk in pks, (
        "Prazan ?kategorija= (Sve kategorije) MORA prikazati sve published objave."
    )


# AC5 / SM-D5: HTMX request → _post_results.html partial (NE full page chrome)
def test_htmx_request_returns_partial(client, make_post, make_category):
    activate("sr")
    cat = make_category(name="Ratarstvo")
    _published(make_post, title="HTMX priča", category=cat)

    response = client.get(
        f"/sr/blog/?kategorija={cat.slug}",
        HTTP_HOST="localhost",
        HTTP_HX_REQUEST="true",
    )

    assert response.status_code == 200
    html = response.content.decode("utf-8")
    assert "<!DOCTYPE" not in html and "<html" not in html.lower(), (
        "HTMX response MORA biti partial (_post_results.html) — NEMA full page chrome "
        f"(<html>/<head>/<body>). Response starts: {html[:200]!r}."
    )
    assert 'id="blog-results"' in html, (
        "HTMX response MORA sadržati `<div id=\"blog-results\">` wrapper "
        "(get_template_names() → _post_results.html)."
    )


# AC5 / SM-D3: non-HTMX request → full page chrome + selected dropdown
def test_non_htmx_request_returns_full_page(client, make_post, make_category):
    activate("sr")
    cat = make_category(name="Ratarstvo")
    _published(make_post, title="Full page priča", category=cat)

    response = client.get(
        f"/sr/blog/?kategorija={cat.slug}", HTTP_HOST="localhost"
    )

    assert response.status_code == 200
    html = response.content.decode("utf-8")
    assert "<html" in html.lower() and "<body" in html.lower(), (
        "Non-HTMX response MORA biti full page (base.html chrome)."
    )
    # dropdown pre-selektovan na slug (deep-link restore)
    assert response.context["active_filters"]["kategorija"] == cat.slug, (
        "non-HTMX deep-link MORA pre-selektovati dropdown (active_filters.kategorija)."
    )


# AC5 / Gotcha BL2-2: OOB aria-live SAMO na HTMX response
def test_oob_aria_live_present_only_on_htmx(client, make_post, make_category):
    activate("sr")
    cat = make_category(name="Ratarstvo")
    _published(make_post, title="OOB priča", category=cat)

    htmx_resp = client.get(
        f"/sr/blog/?kategorija={cat.slug}",
        HTTP_HOST="localhost",
        HTTP_HX_REQUEST="true",
    )
    full_resp = client.get(
        f"/sr/blog/?kategorija={cat.slug}", HTTP_HOST="localhost"
    )

    assert htmx_resp.status_code == 200
    assert full_resp.status_code == 200
    htmx_html = htmx_resp.content.decode("utf-8")
    full_html = full_resp.content.decode("utf-8")

    # HTMX: OOB div sa hx-swap-oob na #aria-live (co-location — oba atributa na istom div-u)
    oob_pattern = re.compile(
        r'<div[^>]*hx-swap-oob=["\']innerHTML:#aria-live["\']',
        re.IGNORECASE,
    )
    assert oob_pattern.search(htmx_html), (
        "HTMX response MORA sadržati `<div hx-swap-oob=\"innerHTML:#aria-live\">` "
        "OOB aria-live count announcement (mirror 2-8 SM-D23)."
    )
    # Non-HTMX: NEMA OOB markup (guard {% if request.htmx %} — Gotcha BL2-2)
    assert "hx-swap-oob" not in full_html, (
        "Non-HTMX (full page) response NE SME sadržati `hx-swap-oob` "
        "(guard `{% if request.htmx %}` — sprečava plain-text OOB render; Gotcha BL2-2)."
    )


# AC5: OOB count announcement sadrži broj filtriranih objava
def test_oob_announcement_contains_count(client, make_post, make_category):
    activate("sr")
    cat = make_category(name="Ratarstvo")
    for i in range(3):
        _published(make_post, title=f"Ratarska {i}", category=cat)

    response = client.get(
        f"/sr/blog/?kategorija={cat.slug}",
        HTTP_HOST="localhost",
        HTTP_HX_REQUEST="true",
    )

    assert response.status_code == 200
    html = response.content.decode("utf-8")
    # OOB announcement „Pronađeno N objava" — broj 3 mora biti prisutan
    oob_match = re.search(
        r'<div[^>]*hx-swap-oob=["\']innerHTML:#aria-live["\'][^>]*>(.*?)</div>',
        html,
        re.IGNORECASE | re.DOTALL,
    )
    assert oob_match, "OOB div MORA postojati u HTMX response-u."
    assert "3" in oob_match.group(1), (
        f"OOB announcement MORA sadržati broj filtriranih objava (3). "
        f"OOB sadržaj: {oob_match.group(1)!r}."
    )


# AC5 / IMP-3: invalid kategorija slug → 0 rezultata + empty (NE 404), normalizovan
def test_invalid_category_slug_normalized(client, make_post, make_category):
    activate("sr")
    cat = make_category(name="Ratarstvo")
    _published(make_post, title="Validna priča", category=cat)

    response = client.get(
        "/sr/blog/?kategorija=nepostoji-kategorija", HTTP_HOST="localhost"
    )

    assert response.status_code == 200, (
        "Invalid kategorija slug MORA biti 200 (empty state), NE 404 (IMP-3)."
    )
    # 0 rezultata (slug ne match-uje nijednu kategoriju)
    assert len(response.context["posts"]) == 0, (
        "Invalid kategorija → 0 rezultata (category__slug ne match-uje)."
    )
    # active_filters normalizovan na "" za dropdown koherenciju (IMP-3)
    assert response.context["active_filters"]["kategorija"] == "", (
        "Invalid slug → active_filters.kategorija normalizovan na \"\" "
        "(dropdown koherencija — mirror 2-9 IMP-3)."
    )


# AC5 / SM-D5: vary_on_headers("HX-Request") → Vary header sadrži HX-Request
def test_vary_header_includes_hx_request(client, make_post):
    activate("sr")
    _published(make_post, title="Vary priča")

    response = client.get("/sr/blog/", HTTP_HOST="localhost")

    assert response.status_code == 200
    vary = response.headers.get("Vary", "")
    assert "HX-Request" in vary, (
        f"Response Vary header MORA sadržati 'HX-Request' "
        f"(@vary_on_headers cache-poisoning defense — SM-D5). Vary: {vary!r}."
    )


# AC5 / dupli-id guard: TAČNO JEDAN id="blog-results" (unutar partiala) na full page
def test_exactly_one_blog_results_id_on_full_page(client, make_post):
    activate("sr")
    _published(make_post, title="Single id priča")

    response = client.get("/sr/blog/", HTTP_HOST="localhost")

    assert response.status_code == 200
    html = response.content.decode("utf-8")
    occurrences = len(re.findall(r'id="blog-results"', html))
    assert occurrences == 1, (
        f"MORA postojati TAČNO JEDAN id=\"blog-results\" (unutar _post_results.html "
        f"partiala; NIKAD i u parentu — dupli-id HTMX/DOM bug). Dobili {occurrences}."
    )


# AC5: filter form ima hx-get / hx-target=#blog-results / hx-push-url
def test_filter_form_htmx_attributes(client, make_post):
    activate("sr")
    _published(make_post, title="Filter form priča")

    response = client.get("/sr/blog/", HTTP_HOST="localhost")

    assert response.status_code == 200
    html = response.content.decode("utf-8")
    # select[name=kategorija] postoji + form ima hx-target=#blog-results (HTMX swap)
    assert 'name="kategorija"' in html, (
        "Filter MORA imati <select name=\"kategorija\"> (dropdown — SM-D8)."
    )
    assert 'hx-target="#blog-results"' in html, (
        "Filter form MORA imati hx-target=\"#blog-results\" (HTMX swap target)."
    )
    assert 'hx-push-url="true"' in html, (
        "Filter form MORA imati hx-push-url=\"true\" (deep-linkable filter)."
    )
