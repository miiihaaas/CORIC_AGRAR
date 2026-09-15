"""Story 5.2 — Empty state (AC7) — TEA RED phase.

Category filter je UKLONJEN (post-launch odluka) — „filter-0 grana" (validna
kategorija sa 0 objava) testovi obrisani s njim. Ta grana i dalje postoji u
`_blog_empty_state.html` (`{% if is_archive %}`), sad isključivo za tag arhivu
(vidi test_blog_archives.py) — BlogIndexView više nema nikakav filter.

Pokriva AC7 (SM-D9): prazan-blog grana (0 published na indeksu): „Uskoro nove
priče sa polja" + „POVRATAK NA POČETNU" → pages:home; DRAFT-only blog → ista
grana; NEMA paginacije.

⚠️ GUARD: apps.blog importi UNUTAR funkcija. REUSE conftest make_post.

Refs:
- 5-2-...-filter.md AC7 + Task 8.8 + SM-D9 + IMP-4/OQ-5
"""

from __future__ import annotations

import pytest
from django.urls import reverse
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


# AC7: empty state → NEMA paginacije
def test_empty_state_no_pagination(client):
    activate("sr")

    response = client.get("/sr/blog/", HTTP_HOST="localhost")

    assert response.status_code == 200
    assert response.context.get("is_paginated") is False, (
        "Empty state NE SME imati paginaciju (is_paginated False)."
    )
