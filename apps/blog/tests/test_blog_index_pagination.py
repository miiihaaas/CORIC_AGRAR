"""Story 5.2 — Paginacija + overflow safety (AC3) — TEA RED phase.

Pokriva AC3 (SM-D3 / SM-D25 / Task 8.6b):
  - paginate_by=10 (epics.md:875 — TAČNO 10/strani)
  - 25 published → strana 1 = 10, ?page=2 = 10, ?page=3 = 5
  - ?page=999 (overflow) → clamp na poslednju stranu (NE 404 EmptyPage) — Paginator.get_page()
  - ?page=abc (invalid) → strana 1 (graceful)
  - is_paginated=True kad >10 objava
  - KOMBINOVANI deep-link (Task 8.6b): non-HTMX ?kategorija=<slug>&page=2 → full page,
    dropdown pre-selektovan, strana-2 TE kategorije, filter sačuvan kroz paginaciju

⚠️ GUARD: apps.blog importi UNUTAR funkcija (REUSE conftest make_post/make_category).

Refs:
- 5-2-...-filter.md AC3 + Task 8.4 + 8.6b + SM-D3/SM-D25
"""

from __future__ import annotations

import pytest
from django.utils import timezone
from django.utils.translation import activate

pytestmark = pytest.mark.django_db


def _seed(make_post, n, *, category=None, title_prefix="Objava"):
    now = timezone.now()
    posts = []
    for i in range(n):
        posts.append(
            make_post(
                title=f"{title_prefix} žetve broj {i}",
                status="published",
                # raspoređeni datumi → deterministični ordering za page-slice provere
                published_at=now - timezone.timedelta(hours=i + 1),
                category=category,
            )
        )
    return posts


# AC3: paginate_by=10 — strana 1 = 10, is_paginated=True (25 objava)
def test_pagination_first_page_has_10(client, make_post):
    activate("sr")
    _seed(make_post, 25)

    response = client.get("/sr/blog/", HTTP_HOST="localhost")

    assert response.status_code == 200
    assert len(response.context["posts"]) == 10, (
        f"Strana 1 MORA prikazati TAČNO 10 objava (paginate_by=10), "
        f"dobili {len(response.context['posts'])}."
    )
    assert response.context.get("is_paginated") is True, (
        "is_paginated MORA biti True kad >10 objava."
    )


# AC3: ?page=2 = 10, ?page=3 = 5 (25 objava → 3 strane)
def test_pagination_page_2_and_3(client, make_post):
    activate("sr")
    _seed(make_post, 25)

    resp2 = client.get("/sr/blog/?page=2", HTTP_HOST="localhost")
    resp3 = client.get("/sr/blog/?page=3", HTTP_HOST="localhost")

    assert resp2.status_code == 200
    assert len(resp2.context["posts"]) == 10, (
        f"Strana 2 MORA imati 10 objava, dobili {len(resp2.context['posts'])}."
    )
    assert resp3.status_code == 200
    assert len(resp3.context["posts"]) == 5, (
        f"Strana 3 (od 25) MORA imati 5 objava, dobili {len(resp3.context['posts'])}."
    )


# AC3 / SM-D25: ?page=999 overflow → clamp na poslednju stranu (NE 404)
def test_pagination_overflow_clamps_to_last_page(client, make_post):
    activate("sr")
    _seed(make_post, 25)

    response = client.get("/sr/blog/?page=999", HTTP_HOST="localhost")

    assert response.status_code == 200, (
        f"?page=999 (overflow) MORA biti clamp-ovan na poslednju stranu (200), "
        f"NE 404 EmptyPage (Paginator.get_page() override — SM-D25). "
        f"Dobili {response.status_code}."
    )
    page_obj = response.context["page_obj"]
    assert page_obj.number == page_obj.paginator.num_pages, (
        f"?page=999 MORA clamp-ovati na poslednju stranu "
        f"({page_obj.paginator.num_pages}), dobili stranu {page_obj.number}."
    )
    assert len(response.context["posts"]) == 5, (
        "Poslednja strana (od 25 objava) MORA prikazati 5 objava."
    )


# AC3 / SM-D25: ?page=abc (invalid) → strana 1 (graceful, NE 404)
def test_pagination_invalid_page_param_graceful(client, make_post):
    activate("sr")
    _seed(make_post, 25)

    response = client.get("/sr/blog/?page=abc", HTTP_HOST="localhost")

    assert response.status_code == 200, (
        f"?page=abc (invalid) MORA biti graceful (200, strana 1 — Paginator.get_page()), "
        f"dobili {response.status_code}."
    )
    assert response.context["page_obj"].number == 1, (
        "?page=abc MORA pasti na stranu 1 (get_page graceful)."
    )


# AC3: ≤10 objava → NEMA paginacije (is_paginated False)
def test_no_pagination_when_under_threshold(client, make_post):
    activate("sr")
    _seed(make_post, 7)

    response = client.get("/sr/blog/", HTTP_HOST="localhost")

    assert response.status_code == 200
    assert response.context.get("is_paginated") is False, (
        "is_paginated MORA biti False kad ≤10 objava (nema paginacije)."
    )


# AC3 + AC5 / Task 8.6b: KOMBINOVANI deep-link ?kategorija=<slug>&page=2 (non-HTMX)
def test_combined_category_and_page_deeplink(client, make_post, make_category):
    """non-HTMX GET /sr/blog/?kategorija=<slug>&page=2 (kategorija sa 11+ objava):
      - full page render (200, blog/blog_index.html)
      - dropdown PRE-SELEKTOVAN na <slug> (active_filters.kategorija == slug)
      - prikazane SAMO objave TE kategorije sa STRANE 2 (NE druge kategorije, NE strana 1)
      - filter sačuvan kroz paginaciju (querystring drži kategorija na page linkovima)
    """
    activate("sr")
    cat = make_category(name="Ratarstvo")  # slug → "ratarstvo"
    other = make_category(name="Stočarstvo")

    # 14 objava u target kategoriji (>10 → 2 strane), + 5 u drugoj (NE smeju procuriti)
    cat_posts = _seed(make_post, 14, category=cat, title_prefix="Ratarstvo priča")
    _seed(make_post, 5, category=other, title_prefix="Stočarstvo priča")

    response = client.get(
        f"/sr/blog/?kategorija={cat.slug}&page=2", HTTP_HOST="localhost"
    )

    assert response.status_code == 200
    templates = {t.name for t in response.templates if t.name}
    assert "blog/blog_index.html" in templates, (
        "Kombinovani deep-link (non-HTMX) MORA renderovati full page blog/blog_index.html."
    )

    # dropdown pre-selektovan
    active = response.context.get("active_filters")
    assert active is not None and active.get("kategorija") == cat.slug, (
        f"active_filters.kategorija MORA biti pre-selektovan na {cat.slug!r} "
        f"(dropdown restore), dobili {active!r}."
    )

    # strana 2 sadrži SAMO objave target kategorije (14 → strana 2 = 4 objave)
    page_posts = list(response.context["posts"])
    cat_pks = {p.pk for p in cat_posts}
    for p in page_posts:
        assert p.pk in cat_pks, (
            f"Strana 2 sme sadržati SAMO objave kategorije {cat.slug!r} "
            f"(pk={p.pk} nije u target kategoriji — filter ne sme procuriti druge)."
        )
    assert len(page_posts) == 4, (
        f"Strana 2 od 14 objava (paginate_by=10) MORA imati 4 objave, "
        f"dobili {len(page_posts)}."
    )

    # filter sačuvan kroz paginaciju — page linkovi nose kategorija param
    html = response.content.decode("utf-8")
    assert f"kategorija={cat.slug}" in html, (
        "Paginacijski linkovi MORAJU sačuvati ?kategorija kroz stranice "
        "({% querystring %} drži kategorija + page)."
    )
