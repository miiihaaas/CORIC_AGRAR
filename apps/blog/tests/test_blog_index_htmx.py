"""Story 5.2 — Blog index HTMX response shape (AC5) — TEA RED phase.

Category filter (i ceo filter form) je UKLONJEN (post-launch odluka) — svi
category-specific testovi (`?kategorija=<slug>` filtriranje, dropdown restore,
OOB count po kategoriji) obrisani s njim. Preostaju generički HTMX-shape
lock-ovi koji ne zavise od filtera:
  - vary_on_headers("HX-Request") → Vary: HX-Request u response
  - TAČNO JEDAN id="blog-results" (unutar partiala)

⚠️ GUARD: apps.blog importi UNUTAR funkcija. REUSE conftest make_post.

Refs:
- 5-2-...-filter.md AC5 + SM-D5
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
