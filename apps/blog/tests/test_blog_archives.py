"""Story 5.3 — Tag arhiva + URL ordering (AC4/AC5/AC9) — TEA RED phase.

Category (BlogCategoryView, `blog:category` ruta, AC3) je UKLONJEN (post-launch
odluka) — svi kategorija-arhiva testovi obrisani s njim.

Pokriva:
  - AC4: BlogTagView `/sr/blog/tag/<slug>/` — Post.published-tag, `.distinct()` M2M-guard,
    404 bad slug, arhiva-prikladan empty, draft-not-leaked
  - AC5: URL ordering — arhiva (2-segment) registrovana PRE catch-all detail (1-segment);
    resolve(...).func.view_class lockovi
  - AC9: draft-not-leaked na arhivi

⚠️ GUARD: apps.blog importi UNUTAR funkcija. REUSE conftest make_post/make_tag.

Refs:
- 5-3-blog-post-detail-strana.md AC4/AC5/AC9 + Task 9.7/9.8/9.12
  + SM-D3/D4 + IMP-1/IMP-5/IMP-6a + Gotcha BL3-4/BL3-6
"""

from __future__ import annotations

import pytest
from django.urls import resolve, reverse
from django.utils import timezone
from django.utils.translation import activate, override

pytestmark = pytest.mark.django_db


def _published(make_post, **overrides):
    defaults = {
        "status": "published",
        "published_at": timezone.now() - timezone.timedelta(days=1),
    }
    defaults.update(overrides)
    return make_post(**defaults)


# ─────────────────────────────────────────────────────────────────────────────
# AC5 (9.8) — URL ordering / reverse / resolve (KLJUČNO — SM-D3)
# ─────────────────────────────────────────────────────────────────────────────


def test_reverse_archive_urls():
    with override("sr"):
        assert reverse("blog:tag", kwargs={"slug": "x"}) == "/sr/blog/tag/x/", (
            "reverse('blog:tag', slug='x') MORA biti /sr/blog/tag/x/ (5-3)."
        )
        # 5-2 detail catch-all i dalje radi (regression)
        assert reverse("blog:detail", kwargs={"slug": "x"}) == "/sr/blog/x/"


def test_resolve_tag_url_to_tag_view():
    from apps.blog.views import BlogTagView

    with override("sr"):
        match = resolve("/sr/blog/tag/psenica/")
    assert match.func.view_class is BlogTagView, (
        "/sr/blog/tag/x/ MORA razrešiti na BlogTagView (AC5)."
    )


def test_resolve_single_segment_still_detail():
    from apps.blog.views import BlogPostDetailView

    with override("sr"):
        match = resolve("/sr/blog/neki-post/")
    assert match.func.view_class is BlogPostDetailView, (
        "1-segment /sr/blog/<slug>/ MORA i dalje razrešiti na BlogPostDetailView "
        "(catch-all radi; 2-segment arhiva strukturno NE shadow-uje 1-segment — AC5/IMP-5)."
    )


# ─────────────────────────────────────────────────────────────────────────────
# AC4 (9.7) — BlogTagView arhiva + .distinct() M2M-guard
# ─────────────────────────────────────────────────────────────────────────────


def test_tag_archive_lists_published_with_tag(client, make_post, make_tag):
    activate("sr")
    t = make_tag(name="Pšenica")
    other = make_tag(name="Kukuruz")
    with_t = _published(make_post, title="Sa tagom T", tags=[t])
    without_t = _published(make_post, title="Sa drugim tagom", tags=[other])

    response = client.get(f"/sr/blog/tag/{t.slug}/", HTTP_HOST="localhost")

    assert response.status_code == 200, (
        f"GET /sr/blog/tag/{t.slug}/ MORA biti 200 (BlogTagView — AC4; RED)."
    )
    pks = {p.pk for p in response.context["posts"]}
    assert with_t.pk in pks
    assert without_t.pk not in pks, "Objava bez taga T NE SME biti u tag-arhivi."


# AC4 / Gotcha BL3-4 / IMP-6a: .distinct() M2M-guard — post sa 2 taga, filter po 1
# → post se pojavljuje TAČNO JEDNOM (kanonski M2M join-dup guard).
def test_tag_archive_distinct_no_m2m_duplicates(client, make_post, make_tag):
    activate("sr")
    t1 = make_tag(name="Pšenica")
    t2 = make_tag(name="Žetva")
    # post sa OBA taga; filtriramo po JEDNOM (t1) — bez .distinct() M2M join može duplirati
    post = _published(make_post, title="Post sa dva taga", tags=[t1, t2])

    response = client.get(f"/sr/blog/tag/{t1.slug}/", HTTP_HOST="localhost")

    assert response.status_code == 200
    pks = [p.pk for p in response.context["posts"]]
    assert pks.count(post.pk) == 1, (
        f"Post sa 2 taga filtriran po 1 tagu MORA se pojaviti TAČNO JEDNOM "
        f"(`.distinct()` kanonski M2M-guard — IMP-6a/Gotcha BL3-4). "
        f"Dobili {pks.count(post.pk)} pojavljivanja. pks={pks!r}."
    )


def test_tag_archive_bad_slug_404(client, make_post, make_tag):
    activate("sr")
    t = make_tag(name="Pšenica")
    _published(make_post, title="Kontrola tag objava", tags=[t])
    control = client.get(f"/sr/blog/tag/{t.slug}/", HTTP_HOST="localhost")
    assert control.status_code == 200, (
        "KONTROLA: validan tag MORA biti 200 (ruta registrovana)."
    )

    response = client.get("/sr/blog/tag/ne-postoji/", HTTP_HOST="localhost")
    assert response.status_code == 404, (
        "Nepostojeći tag slug MORA biti 404 (get_object_or_404(Tag) — SM-D4)."
    )


def test_tag_archive_draft_not_leaked(client, make_post, make_tag):
    activate("sr")
    t = make_tag(name="Pšenica")
    published = _published(make_post, title="Objavljena sa tagom", tags=[t])
    draft = make_post(
        title="Draft sa tagom", status="draft", published_at=None, tags=[t]
    )

    response = client.get(f"/sr/blog/tag/{t.slug}/", HTTP_HOST="localhost")

    assert response.status_code == 200
    pks = {p.pk for p in response.context["posts"]}
    assert published.pk in pks
    assert draft.pk not in pks, (
        "DRAFT sa tagom T NE SME procuriti u tag-arhivi (Post.published; AC9)."
    )


def test_tag_archive_empty_uses_filter_copy(client, make_post, make_tag):
    activate("sr")
    t = make_tag(name="Prazan tag")
    make_post(title="Samo draft sa tagom", status="draft", published_at=None, tags=[t])

    response = client.get(f"/sr/blog/tag/{t.slug}/", HTTP_HOST="localhost")

    assert response.status_code == 200, (
        "Validan tag sa 0 published MORA biti 200 + empty state."
    )
    html = response.content.decode("utf-8")
    assert 'data-testid="blog-empty-filter"' in html, (
        "Tag-arhiva-empty MORA renderovati FILTER-prikladnu kopiju (IMP-1)."
    )
    assert 'data-testid="blog-empty-home"' not in html, (
        "Tag-arhiva-empty NE SME renderovati generičku home granu (IMP-1)."
    )


def test_tag_archive_heading_shows_tag_name(client, make_post, make_tag):
    activate("sr")
    t = make_tag(name="Pšenica")
    _published(make_post, title="Heading tag priča", tags=[t])

    response = client.get(f"/sr/blog/tag/{t.slug}/", HTTP_HOST="localhost")

    assert response.status_code == 200
    html = response.content.decode("utf-8")
    assert t.name in html, (
        "Tag-arhiva heading MORA prikazati ime taga (archive_object — AC4)."
    )


# ─────────────────────────────────────────────────────────────────────────────
# AC9 / SM-D2 — future-dated (scheduled) exclusion na arhivi (TEA F-01)
# Post.published filtrira `published_at__lte=now` → scheduled (budući) post
# NE SME procuriti u arhivu (draft-not-leaked druga polovina granice).
# ─────────────────────────────────────────────────────────────────────────────


def test_tag_archive_future_published_excluded(client, make_post, make_tag):
    activate("sr")
    t = make_tag(name="Pšenica")
    past = _published(make_post, title="Prošla objava sa tagom", tags=[t])
    future = make_post(
        title="Zakazana objava sa tagom",
        status="published",
        published_at=timezone.now() + timezone.timedelta(days=7),
        tags=[t],
    )

    response = client.get(f"/sr/blog/tag/{t.slug}/", HTTP_HOST="localhost")

    assert response.status_code == 200
    pks = {p.pk for p in response.context["posts"]}
    assert past.pk in pks, "Prošla published objava sa tagom MORA biti u arhivi."
    assert future.pk not in pks, (
        "FUTURE-dated (scheduled) objava NE SME procuriti u tag-arhivi "
        "(Post.published filtrira published_at__lte=now — AC9/SM-D2)."
    )
