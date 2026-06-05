"""Story 5.2 — Empty state DVE grane (AC7) — TEA RED phase.

Pokriva AC7 (SM-D9 / IMP-4): `_blog_empty_state.html` ima `{% if active_filters.kategorija %}`:
  - prazan-blog grana (active_filters.kategorija prazan): „Uskoro nove priče sa polja"
    + „POVRATAK NA POČETNU" → pages:home
  - filter-0 grana (active_filters.kategorija truthy, validna kategorija sa 0 objava):
    „Nema objava u ovoj kategoriji." + „prikaži sve" → blog:index
  - DRAFT-only blog (svi draft, bez filtera) → prazan-blog grana
  - invalid slug → normalizovan na "" → prazan-blog grana
  - NEMA paginacije u obe grane

⚠️ GUARD: apps.blog importi UNUTAR funkcija. REUSE conftest make_post/make_category.

Refs:
- 5-2-...-filter.md AC7 + Task 8.8 + SM-D9 + IMP-4/OQ-5
"""

from __future__ import annotations

import pytest
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import activate, override

pytestmark = pytest.mark.django_db


# AC7: 0 published (prazan blog) → prazan-blog grana
def test_empty_blog_shows_uskoro_message(client):
    activate("sr")
    # NEMA objava uopšte

    response = client.get("/sr/blog/", HTTP_HOST="localhost")

    assert response.status_code == 200, "Prazan blog NIJE greška (200)."
    html = response.content.decode("utf-8")
    assert "Uskoro nove priče sa polja" in html, (
        "Prazan blog MORA prikazati 'Uskoro nove priče sa polja' (epics.md:879, prazan-blog grana)."
    )


# AC7: prazan-blog grana → „POVRATAK NA POČETNU" link na pages:home
def test_empty_blog_has_home_cta(client):
    activate("sr")

    response = client.get("/sr/blog/", HTTP_HOST="localhost")

    assert response.status_code == 200
    html = response.content.decode("utf-8")
    assert "POVRATAK NA POČETNU" in html, (
        "Prazan-blog grana MORA imati CTA 'POVRATAK NA POČETNU'."
    )
    with override("sr"):
        home_url = reverse("pages:home")
    assert f'href="{home_url}"' in html, (
        f"'POVRATAK NA POČETNU' MORA linkovati na pages:home ({home_url})."
    )


# AC7: DRAFT-only blog (svi draft, bez filtera) → prazan-blog grana
def test_draft_only_blog_shows_uskoro(client, make_post):
    activate("sr")
    make_post(title="Nacrt 1", status="draft", published_at=None)
    make_post(title="Nacrt 2", status="draft", published_at=None)

    response = client.get("/sr/blog/", HTTP_HOST="localhost")

    assert response.status_code == 200
    html = response.content.decode("utf-8")
    assert "Uskoro nove priče sa polja" in html, (
        "DRAFT-only blog (Post.published prazan, active_filters.kategorija prazan) "
        "→ prazan-blog grana 'Uskoro nove priče sa polja'."
    )


# AC7 / IMP-4: validna kategorija sa 0 objava → filter-0 grana
def test_valid_category_zero_posts_shows_filter_empty(client, make_post, make_category):
    activate("sr")
    # Kategorija postoji, ali nema published objava u njoj
    prazna = make_category(name="Stočarstvo")
    # objava postoji ali u DRUGOJ kategoriji (blog NIJE prazan)
    druga = make_category(name="Ratarstvo")
    make_post(
        title="Ratarska priča",
        status="published",
        published_at=timezone.now() - timezone.timedelta(days=1),
        category=druga,
    )

    response = client.get(
        f"/sr/blog/?kategorija={prazna.slug}", HTTP_HOST="localhost"
    )

    assert response.status_code == 200
    html = response.content.decode("utf-8")
    assert "Nema objava u ovoj kategoriji." in html, (
        "Validna kategorija sa 0 objava → filter-0 grana "
        "'Nema objava u ovoj kategoriji.' (IMP-4)."
    )
    # „prikaži sve" link na blog:index (bez ?kategorija)
    with override("sr"):
        index_url = reverse("blog:index")
    assert f'href="{index_url}"' in html, (
        f"filter-0 grana MORA imati 'prikaži sve' link na blog:index ({index_url})."
    )


# AC7: filter-0 grana NE prikazuje prazan-blog poruku (semantika razdvojena)
def test_filter_empty_not_showing_uskoro(client, make_post, make_category):
    activate("sr")
    prazna = make_category(name="Stočarstvo")
    druga = make_category(name="Ratarstvo")
    make_post(
        title="Ratarska priča",
        status="published",
        published_at=timezone.now() - timezone.timedelta(days=1),
        category=druga,
    )

    response = client.get(
        f"/sr/blog/?kategorija={prazna.slug}", HTTP_HOST="localhost"
    )

    assert response.status_code == 200
    html = response.content.decode("utf-8")
    assert "Uskoro nove priče sa polja" not in html, (
        "filter-0 grana NE SME prikazati 'Uskoro nove priče sa polja' "
        "(zavaravajuce - objave POSTOJE, samo ne u toj kategoriji; IMP-4)."
    )


# AC7: empty state → NEMA paginacije
def test_empty_state_no_pagination(client):
    activate("sr")

    response = client.get("/sr/blog/", HTTP_HOST="localhost")

    assert response.status_code == 200
    assert response.context.get("is_paginated") is False, (
        "Empty state NE SME imati paginaciju (is_paginated False)."
    )
