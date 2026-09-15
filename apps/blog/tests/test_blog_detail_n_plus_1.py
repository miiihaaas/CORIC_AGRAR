"""Story 5.3 — N+1 lock: detail (author/tags) + tag arhiva (AC8) — TEA RED phase.

Category i „Slične objave" (100% category-bazirane) su UKLONJENI (post-launch
odluka) — pripadajući testovi/varijacije obrisani s njim.

Pokriva AC8 (SM-D2 / Gotcha BL3-3):
  - detail query broj KONSTANTAN bez obzira na broj tagova (post sa 2 taga ==
    post sa 5 tagova) → dokazuje `select_related("author")` + `prefetch_related("tags")`
  - tag arhiva count-variation (3 objave == 10 objava)

⚠️ Empirical query count NIJE moguć pre Dev impl-a → COUNT/COMPOSITION-VARIATION lock
(robusnije od magic broja): isti budžet za varijaciju ulaza.

⚠️ GUARD: apps.blog importi UNUTAR funkcija (REUSE conftest).

Refs:
- 5-3-blog-post-detail-strana.md AC8 + Task 9.11 + SM-D2 + Gotcha BL3-3
- apps/blog/tests/test_blog_index_n_plus_1.py (count-variation precedent)
"""

from __future__ import annotations

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
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


def _count_queries(client, url):
    with CaptureQueriesContext(connection) as ctx:
        response = client.get(url, HTTP_HOST="localhost")
        assert response.status_code == 200
    return len(ctx.captured_queries)


# AC8 / SM-D2: get_queryset() MORA select_related("author") + prefetch_related("tags").
def test_detail_queryset_has_author_select_and_tags_prefetch(
    client, make_post, make_tag, author_user
):
    activate("sr")
    t = make_tag(name="Pšenica")
    post = _published(
        make_post, title="Queryset shape priča", author=author_user, tags=[t]
    )

    # Renderuj detail i pokupi finalni queryset koji je view koristio
    response = client.get(f"/sr/blog/{post.slug}/", HTTP_HOST="localhost")
    assert response.status_code == 200

    from apps.blog.views import BlogPostDetailView

    qs = BlogPostDetailView().get_queryset()
    assert "author" in qs.query.select_related, (
        "get_queryset() MORA select_related('author') (autor meta render N+1 lock)."
    )
    # prefetch_related('tags') — M2M tag-link render N+1 lock
    assert "tags" in qs._prefetch_related_lookups, (
        f"get_queryset() MORA prefetch_related('tags') (tag linkovi render N+1 lock). "
        f"Trenutni prefetch lookups: {qs._prefetch_related_lookups!r}."
    )


# AC8: detail query broj KONSTANTAN — composition-variation (2 taga vs 5 tagova)
def test_detail_query_count_constant_across_tags(
    client, make_post, make_tag, author_user
):
    activate("sr")

    tags_a = [make_tag(name=f"TagA{i}") for i in range(2)]
    post_a = _published(
        make_post, title="Glavna A", author=author_user, tags=tags_a
    )
    queries_a = _count_queries(client, f"/sr/blog/{post_a.slug}/")

    tags_b = [make_tag(name=f"TagB{i}") for i in range(5)]
    post_b = _published(
        make_post, title="Glavna B", author=author_user, tags=tags_b
    )
    queries_b = _count_queries(client, f"/sr/blog/{post_b.slug}/")

    assert queries_a == queries_b, (
        f"Detail query broj MORA biti KONSTANTAN bez obzira na broj tagova "
        f"(2 taga → {queries_a} upita; 5 tagova → {queries_b} upita). "
        f"Razlika znači N+1 — `get_queryset()` MORA select_related('author') "
        f"+ prefetch_related('tags') (SM-D2). Razlika = {queries_b - queries_a} upita."
    )


# AC8: tag-arhiva count-variation (3 objave == 10 objava)
def test_tag_archive_query_count_constant(client, make_post, make_tag):
    activate("sr")
    t = make_tag(name="Pšenica")
    now = timezone.now()

    for i in range(3):
        make_post(
            title=f"Arhiva tag {i}",
            status="published",
            published_at=now - timezone.timedelta(hours=i + 1),
            tags=[t],
        )
    q3 = _count_queries(client, f"/sr/blog/tag/{t.slug}/")

    for i in range(3, 10):
        make_post(
            title=f"Arhiva tag {i}",
            status="published",
            published_at=now - timezone.timedelta(hours=i + 1),
            tags=[t],
        )
    q10 = _count_queries(client, f"/sr/blog/tag/{t.slug}/")

    assert q3 == q10, (
        f"Tag-arhiva query broj MORA biti KONSTANTAN (3 objave → {q3}; "
        f"10 objava → {q10}). Razlika = per-post N+1. Razlika = {q10 - q3} upita."
    )
