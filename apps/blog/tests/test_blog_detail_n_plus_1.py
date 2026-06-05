"""Story 5.3 — N+1 lock: detail (author/tags/Slične) + arhive (AC8) — TEA RED phase.

Pokriva AC8 (SM-D2/SM-D8 / Gotcha BL3-3):
  - detail query broj KONSTANTAN bez obzira na broj tagova/sličnih-objava
    (post 2 taga + 4 slične == post 5 tagova + 4 slične) → dokazuje
    `select_related("category","author")` + `prefetch_related("tags")` + bounded
    similar query
  - arhive count-variation (3 objave == 10 objava) → `select_related("category")`

⚠️ Empirical query count NIJE moguć pre Dev impl-a → COUNT/COMPOSITION-VARIATION lock
(robusnije od magic broja): isti budžet za varijaciju ulaza. U RED-u ovi testovi padaju
jer 5-3 view još NE postoji (detail 5-2 placeholder NEMA prefetch tags → per-render
tag/similar N+1; arhive view ne postoji → 404 → assert fail).

⚠️ GUARD: apps.blog importi UNUTAR funkcija (REUSE conftest).

Refs:
- 5-3-blog-post-detail-strana.md AC8 + Task 9.11 + SM-D2/D8 + Gotcha BL3-3
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


# AC8 / SM-D2: get_queryset() MORA proširiti 5-2 na select_related("author") +
# prefetch_related("tags"). RED: 5-2 placeholder ima SAMO select_related("category")
# (bez author/tags) → ovaj test pada dok 5-3 ne proširi queryset. Composition-variation
# lock (ispod) trivijalno prolazi na placeholder-u (ništa se ne renderuje), pa je OVO
# eksplicitan feature-absence guard za prefetch/select_related setup (SM-D2 / IMP-5).
def test_detail_queryset_has_author_select_and_tags_prefetch(
    client, make_post, make_category, make_tag, author_user
):
    activate("sr")
    k = make_category(name="Ratarstvo")
    t = make_tag(name="Pšenica")
    post = _published(
        make_post, title="Queryset shape priča", category=k, author=author_user, tags=[t]
    )

    # Renderuj detail i pokupi finalni queryset koji je view koristio
    response = client.get(f"/sr/blog/{post.slug}/", HTTP_HOST="localhost")
    assert response.status_code == 200

    from apps.blog.views import BlogPostDetailView

    qs = BlogPostDetailView().get_queryset()
    # select_related (FK JOIN) — mora uključivati i category i author
    assert "author" in qs.query.select_related, (
        "get_queryset() MORA select_related('author') (autor meta render N+1 lock; "
        "5-2 placeholder ima SAMO category — SM-D2/IMP-5; RED dok 5-3 ne proširi)."
    )
    assert "category" in qs.query.select_related, (
        "get_queryset() MORA zadržati select_related('category') (5-2 ugovor)."
    )
    # prefetch_related('tags') — M2M tag-link render N+1 lock
    assert "tags" in qs._prefetch_related_lookups, (
        f"get_queryset() MORA prefetch_related('tags') (tag linkovi render N+1 lock; "
        f"5-2 placeholder NEMA prefetch — SM-D2/IMP-5; RED). "
        f"Trenutni prefetch lookups: {qs._prefetch_related_lookups!r}."
    )


# AC8: detail query broj KONSTANTAN — composition-variation (2 taga+4 slične vs 5 tagova+4 slične)
def test_detail_query_count_constant_across_tags_and_similar(
    client, make_post, make_category, make_tag, author_user
):
    activate("sr")

    # ── Scenario A: post sa 2 taga + 4 slične u istoj kategoriji ──
    ka = make_category(name="Ratarstvo")
    tags_a = [make_tag(name=f"TagA{i}") for i in range(2)]
    post_a = _published(
        make_post, title="Glavna A", category=ka, author=author_user, tags=tags_a
    )
    for i in range(4):
        _published(make_post, title=f"Slična A {i}", category=ka)
    queries_a = _count_queries(client, f"/sr/blog/{post_a.slug}/")

    # ── Scenario B: post sa 5 tagova + 4 slične ──
    kb = make_category(name="Stočarstvo")
    tags_b = [make_tag(name=f"TagB{i}") for i in range(5)]
    post_b = _published(
        make_post, title="Glavna B", category=kb, author=author_user, tags=tags_b
    )
    for i in range(4):
        _published(make_post, title=f"Slična B {i}", category=kb)
    queries_b = _count_queries(client, f"/sr/blog/{post_b.slug}/")

    assert queries_a == queries_b, (
        f"Detail query broj MORA biti KONSTANTAN bez obzira na broj tagova/sličnih "
        f"(2 taga+4 slične → {queries_a} upita; 5 tagova+4 slične → {queries_b} upita). "
        f"Razlika znači N+1 — `get_queryset()` MORA select_related('category','author') "
        f"+ prefetch_related('tags'); similar query bounded (SM-D2/SM-D8). "
        f"Razlika = {queries_b - queries_a} upita."
    )


# AC8: kategorija-arhiva count-variation (3 objave == 10 objava) → select_related('category')
def test_category_archive_query_count_constant(client, make_post, make_category):
    activate("sr")
    k = make_category(name="Ratarstvo")
    now = timezone.now()

    for i in range(3):
        make_post(
            title=f"Arhiva K {i}",
            status="published",
            published_at=now - timezone.timedelta(hours=i + 1),
            category=k,
        )
    q3 = _count_queries(client, f"/sr/blog/kategorija/{k.slug}/")

    for i in range(3, 10):
        make_post(
            title=f"Arhiva K {i}",
            status="published",
            published_at=now - timezone.timedelta(hours=i + 1),
            category=k,
        )
    q10 = _count_queries(client, f"/sr/blog/kategorija/{k.slug}/")

    assert q3 == q10, (
        f"Kategorija-arhiva query broj MORA biti KONSTANTAN (3 objave → {q3}; "
        f"10 objava → {q10}). Razlika = per-post N+1 — MORA select_related('category') "
        f"(mirror BlogIndexView AC2). Razlika = {q10 - q3} upita."
    )


# AC8: tag-arhiva count-variation (3 objave == 10 objava) → select_related('category')
def test_tag_archive_query_count_constant(client, make_post, make_tag, make_category):
    activate("sr")
    t = make_tag(name="Pšenica")
    k = make_category(name="Ratarstvo")
    now = timezone.now()

    for i in range(3):
        make_post(
            title=f"Arhiva tag {i}",
            status="published",
            published_at=now - timezone.timedelta(hours=i + 1),
            category=k,
            tags=[t],
        )
    q3 = _count_queries(client, f"/sr/blog/tag/{t.slug}/")

    for i in range(3, 10):
        make_post(
            title=f"Arhiva tag {i}",
            status="published",
            published_at=now - timezone.timedelta(hours=i + 1),
            category=k,
            tags=[t],
        )
    q10 = _count_queries(client, f"/sr/blog/tag/{t.slug}/")

    assert q3 == q10, (
        f"Tag-arhiva query broj MORA biti KONSTANTAN (3 objave → {q3}; "
        f"10 objava → {q10}). select_related('category') N+1 lock. "
        f"Razlika = {q10 - q3} upita."
    )


# AC8 / SM-D8 / Gotcha BL3-3: similar_posts CARD N+1 — 0-vs-4 slične u kategoriji.
# Drži sve što NIJE pod testom jednako (autor + tagovi na glavnom postu). Razlika u
# broju upita = per-card N+1 na similar_posts → similar queryset MORA select_related
# da pokrije šta _post_card.html renderuje per slična objava (trenutno: get_absolute_url
# /main_image[storage]/published_at/title/perex/slug — NE tags/author, pa 0 == 4).
def test_detail_query_count_constant_zero_vs_four_similar(
    client, make_post, make_category, make_tag, author_user
):
    activate("sr")

    # ── Scenario A: post SAM u svojoj kategoriji (0 sličnih) ──
    ka = make_category(name="Ratarstvo")
    tags_a = [make_tag(name=f"TagA{i}") for i in range(2)]
    post_a = _published(
        make_post, title="Glavna A sama", category=ka, author=author_user, tags=tags_a
    )
    queries_a = _count_queries(client, f"/sr/blog/{post_a.slug}/")

    # ── Scenario B: post + 4 published slične u istoj kategoriji ──
    kb = make_category(name="Stočarstvo")
    tags_b = [make_tag(name=f"TagB{i}") for i in range(2)]
    post_b = _published(
        make_post, title="Glavna B sa 4 slične", category=kb, author=author_user, tags=tags_b
    )
    for i in range(4):
        _published(make_post, title=f"Slična B {i}", category=kb)
    queries_b = _count_queries(client, f"/sr/blog/{post_b.slug}/")

    assert queries_a == queries_b, (
        f"Detail query broj MORA biti KONSTANTAN bez obzira na broj sličnih objava "
        f"(0 sličnih → {queries_a} upita; 4 slične → {queries_b} upita). "
        f"Razlika = per-card N+1 na similar_posts — similar queryset "
        f"`Post.published.filter(category=...).select_related('category')[:4]` MORA "
        f"pokriti sve što _post_card.html renderuje per slična objava (SM-D8). "
        f"Razlika = {queries_b - queries_a} upita."
    )
