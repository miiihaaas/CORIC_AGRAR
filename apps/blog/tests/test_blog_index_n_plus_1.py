"""Story 5.2 — N+1 lock (AC2) — TEA RED phase.

Pokriva AC2 (SM-D6 / Gotcha BL2-5): `BlogIndexView.get_queryset()` MORA imati
`.select_related("category")` (FK — kartica/filter ne sme per-post category N+1).
Count-variation lock: query broj je KONSTANTAN bez obzira na broj objava na strani
(3 objave == 10 objava). Bez `select_related("category")`, broj bi rastao po objavi.

`categories_for_dropdown` (Category.order_by) je +1 KONSTANTA (Gotcha BL2-5) — NE
per-post; ulazi u fiksni budžet ali ne varira s brojem objava.

IMP-1: NE testira `prefetch_related("tags")` — kartica NE renderuje tagove; 5-2
queryset je `Post.published.select_related("category")` SAMO (tags prefetch je 5-3).

⚠️ Empirical query count NIJE moguć pre Dev impl-a. Koristimo COUNT-VARIATION lock
(robusnije od magic broja): isti budžet za 3 vs 10 objava. Apsolutni budžet je
labav gornji prag (≤ 8) — Dev/TEA zaključavaju tačan broj u GREEN ako se želi.

⚠️ GUARD: apps.blog importi UNUTAR funkcija.

Refs:
- 5-2-...-filter.md AC2 + Task 8.3 + SM-D6 + Gotcha BL2-5 + IMP-1
"""

from __future__ import annotations

import pytest
from django.test.utils import CaptureQueriesContext
from django.db import connection
from django.utils import timezone
from django.utils.translation import activate

pytestmark = pytest.mark.django_db


def _seed_published(make_post, make_category, n, *, category=None, start=0):
    """Seed n PUBLISHED+past objava, svaka sa category FK (per-post category lookup).

    `start` offset drži title/slug jedinstvenim kroz uzastopne seed pozive
    (Post.slug je globalno unique bez auto-dedup — 5-1 IMP-5; bez offset-a drugi
    batch bi reciklirao title-ove prvog → slug kolizija ValidationError).
    """
    cat = category or make_category(name="Ratarstvo")
    now = timezone.now()
    for i in range(start, start + n):
        make_post(
            title=f"Žetva pšenice broj {i}",
            status="published",
            published_at=now - timezone.timedelta(days=i + 1),
            category=cat,
        )
    return cat


def _count_queries(client, url):
    with CaptureQueriesContext(connection) as ctx:
        response = client.get(url, HTTP_HOST="localhost")
        assert response.status_code == 200
    return len(ctx.captured_queries)


# AC2: count-variation lock — 3 objave == 10 objava (select_related drži category JOIN
# konstantnim; bez njega broj raste po objavi).
def test_blog_index_query_count_constant_across_post_count(
    client, make_post, make_category
):
    activate("sr")

    cat = _seed_published(make_post, make_category, 3)
    queries_3 = _count_queries(client, "/sr/blog/")

    # Dodaj još 7 objava (ukupno 10) u ISTU kategoriju (start=3 → jedinstveni slug-ovi)
    _seed_published(make_post, make_category, 7, category=cat, start=3)
    queries_10 = _count_queries(client, "/sr/blog/")

    assert queries_3 == queries_10, (
        f"Query broj MORA biti KONSTANTAN bez obzira na broj objava "
        f"(3 objave → {queries_3} upita; 10 objava → {queries_10} upita). "
        f"Razlika znači per-post N+1 — `BlogIndexView.get_queryset()` MORA imati "
        f".select_related('category') (SM-D6/AC2). Razlika = "
        f"{queries_10 - queries_3} dodatnih upita."
    )


# AC2: apsolutni gornji budžet (labav prag — sanity guard, ne magic-broj lock).
def test_blog_index_query_budget_upper_bound(client, make_post, make_category):
    activate("sr")
    _seed_published(make_post, make_category, 10)

    queries = _count_queries(client, "/sr/blog/")

    # Labav gornji prag: Post count + Post slice (select_related category) +
    # categories_for_dropdown + SiteSettings chrome + paginator. Tačan broj se
    # zaključava u GREEN; ovde samo sanity da nema runaway N+1.
    assert queries <= 8, (
        f"Query budžet za /sr/blog/ sa 10 objava MORA biti ≤ 8 (sanity gornji prag — "
        f"select_related('category') + categories_for_dropdown konstanta). "
        f"Dobili {queries} upita — verovatno N+1 (proveri select_related)."
    )
