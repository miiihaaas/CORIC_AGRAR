"""Story 5.2 — N+1 lock (AC2) — TEA RED phase.

Category je UKLONJEN (post-launch odluka) — queryset više nema `.select_related
("category")` niti `categories_for_dropdown`; testovi ažurirani da i dalje
zaključavaju count-variation invarijantu (konstantan broj upita bez obzira na
broj objava), samo bez category FK JOIN-a.

IMP-1: NE testira `prefetch_related("tags")` — kartica NE renderuje tagove; 5-2
queryset je `Post.published.all()` SAMO (tags prefetch je 5-3).

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


def _seed_published(make_post, n, *, start=0):
    """Seed n PUBLISHED+past objava.

    `start` offset drži title/slug jedinstvenim kroz uzastopne seed pozive
    (Post.slug je globalno unique bez auto-dedup — 5-1 IMP-5; bez offset-a drugi
    batch bi reciklirao title-ove prvog → slug kolizija ValidationError).
    """
    now = timezone.now()
    for i in range(start, start + n):
        make_post(
            title=f"Žetva pšenice broj {i}",
            status="published",
            published_at=now - timezone.timedelta(days=i + 1),
        )


def _count_queries(client, url):
    with CaptureQueriesContext(connection) as ctx:
        response = client.get(url, HTTP_HOST="localhost")
        assert response.status_code == 200
    return len(ctx.captured_queries)


# AC2: count-variation lock — 3 objave == 10 objava (nema per-post N+1).
def test_blog_index_query_count_constant_across_post_count(client, make_post):
    activate("sr")

    _seed_published(make_post, 3)
    queries_3 = _count_queries(client, "/sr/blog/")

    # Dodaj još 7 objava (ukupno 10; start=3 → jedinstveni slug-ovi)
    _seed_published(make_post, 7, start=3)
    queries_10 = _count_queries(client, "/sr/blog/")

    assert queries_3 == queries_10, (
        f"Query broj MORA biti KONSTANTAN bez obzira na broj objava "
        f"(3 objave → {queries_3} upita; 10 objava → {queries_10} upita). "
        f"Razlika znači per-post N+1. Razlika = {queries_10 - queries_3} dodatnih upita."
    )


# AC2: apsolutni gornji budžet (labav prag — sanity guard, ne magic-broj lock).
def test_blog_index_query_budget_upper_bound(client, make_post):
    activate("sr")
    _seed_published(make_post, 10)

    queries = _count_queries(client, "/sr/blog/")

    # Labav gornji prag: Post count + Post slice + SiteSettings chrome + paginator.
    # Tačan broj se zaključava u GREEN; ovde samo sanity da nema runaway N+1.
    assert queries <= 8, (
        f"Query budžet za /sr/blog/ sa 10 objava MORA biti ≤ 8 (sanity gornji prag). "
        f"Dobili {queries} upita — verovatno N+1."
    )
