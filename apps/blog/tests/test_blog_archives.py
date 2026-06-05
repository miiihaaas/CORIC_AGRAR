"""Story 5.3 — Kategorija/Tag arhive + URL ordering (AC3/AC4/AC5/AC9) — TEA RED phase.

Pokriva:
  - AC3: BlogCategoryView `/sr/blog/kategorija/<slug>/` — Post.published-K, paginacija,
    404 bad slug, arhiva-prikladan empty (active_filters → blog-empty-filter), NEMA
    filter dropdown, HTMX branching
  - AC4: BlogTagView `/sr/blog/tag/<slug>/` — Post.published-tag, `.distinct()` M2M-guard,
    404 bad slug, arhiva-prikladan empty, draft-not-leaked
  - AC5: URL ordering — arhive (2-segment) registrovane PRE catch-all detail (1-segment);
    resolve(...).func.view_class lockovi
  - AC9: draft-not-leaked na obe arhive

⚠️ RED-faza: BlogCategoryView/BlogTagView + `blog:category`/`blog:tag` URL-ovi JOŠ NE
postoje → testovi padaju na FEATURE odsustvu (NoReverseMatch UNUTAR test tela; 404 gde
se očekuje 200; resolve mismatch). NE collection errori — apps.blog/view importi su
UNUTAR funkcija; `reverse()`/`resolve()` UNUTAR test tela.

⚠️ GUARD: apps.blog importi UNUTAR funkcija. REUSE conftest make_post/make_category/make_tag.

Refs:
- 5-3-blog-post-detail-strana.md AC3/AC4/AC5/AC9 + Task 9.6/9.7/9.8/9.12
  + SM-D3/D4 + IMP-1/IMP-5/IMP-6a/IMP-6c + Gotcha BL3-4/BL3-6
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
        assert reverse("blog:category", kwargs={"slug": "x"}) == "/sr/blog/kategorija/x/", (
            "reverse('blog:category', slug='x') MORA biti /sr/blog/kategorija/x/ (5-3)."
        )
        assert reverse("blog:tag", kwargs={"slug": "x"}) == "/sr/blog/tag/x/", (
            "reverse('blog:tag', slug='x') MORA biti /sr/blog/tag/x/ (5-3)."
        )
        # 5-2 detail catch-all i dalje radi (regression)
        assert reverse("blog:detail", kwargs={"slug": "x"}) == "/sr/blog/x/"


def test_resolve_category_url_to_category_view():
    from apps.blog.views import BlogCategoryView

    with override("sr"):
        match = resolve("/sr/blog/kategorija/ratarstvo/")
    assert match.func.view_class is BlogCategoryView, (
        "/sr/blog/kategorija/x/ MORA razrešiti na BlogCategoryView "
        "(2-segment arhiva — NE BlogPostDetailView; resolver-order lock AC5)."
    )


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
# AC3 (9.6) — BlogCategoryView arhiva
# ─────────────────────────────────────────────────────────────────────────────


def test_category_archive_lists_published_in_category(
    client, make_post, make_category
):
    activate("sr")
    k = make_category(name="Ratarstvo")
    other = make_category(name="Stočarstvo")
    in_k = _published(make_post, title="U kategoriji K", category=k)
    out_k = _published(make_post, title="Druga kategorija", category=other)

    response = client.get(f"/sr/blog/kategorija/{k.slug}/", HTTP_HOST="localhost")

    assert response.status_code == 200, (
        f"GET /sr/blog/kategorija/{k.slug}/ MORA biti 200 (BlogCategoryView — AC3; RED)."
    )
    templates = {t.name for t in response.templates if t.name}
    assert "blog/blog_archive.html" in templates, (
        f"Arhiva MORA koristiti blog/blog_archive.html. Korišćeni: {templates!r}."
    )
    pks = {p.pk for p in response.context["posts"]}
    assert in_k.pk in pks, "Objava kategorije K MORA biti u arhivi."
    assert out_k.pk not in pks, "Objava DRUGE kategorije NE SME biti u arhivi K."


def test_category_archive_draft_not_leaked(client, make_post, make_category):
    activate("sr")
    k = make_category(name="Ratarstvo")
    published = _published(make_post, title="Objavljena u K", category=k)
    draft = make_post(
        title="Draft u K", status="draft", published_at=None, category=k
    )

    response = client.get(f"/sr/blog/kategorija/{k.slug}/", HTTP_HOST="localhost")

    assert response.status_code == 200
    pks = {p.pk for p in response.context["posts"]}
    assert published.pk in pks
    assert draft.pk not in pks, (
        "DRAFT u kategoriji K NE SME procuriti u arhivi (Post.published; AC9)."
    )
    html = response.content.decode("utf-8")
    assert draft.title not in html, "DRAFT naslov NE SME biti renderovan u arhivi."


def test_category_archive_pagination(client, make_post, make_category):
    activate("sr")
    k = make_category(name="Ratarstvo")
    now = timezone.now()
    for i in range(25):
        make_post(
            title=f"Objava K broj {i}",
            status="published",
            published_at=now - timezone.timedelta(hours=i + 1),
            category=k,
        )

    resp1 = client.get(f"/sr/blog/kategorija/{k.slug}/", HTTP_HOST="localhost")
    assert resp1.status_code == 200
    assert len(resp1.context["posts"]) == 10, (
        "Arhiva strana 1 MORA imati 10 objava (paginate_by=10 — mirror BlogIndexView)."
    )

    # overflow clamp — ?page=999 → poslednja strana (NE 404)
    resp_of = client.get(
        f"/sr/blog/kategorija/{k.slug}/?page=999", HTTP_HOST="localhost"
    )
    assert resp_of.status_code == 200, (
        "?page=999 overflow MORA clamp-ovati na poslednju stranu (Paginator.get_page() — NE 404)."
    )


def test_category_archive_bad_slug_404(client, make_post, make_category):
    activate("sr")
    # kontrola: validna kategorija postoji (dokazuje da je ruta registrovana)
    k = make_category(name="Ratarstvo")
    _published(make_post, title="Kontrola objava", category=k)
    control = client.get(
        f"/sr/blog/kategorija/{k.slug}/", HTTP_HOST="localhost"
    )
    assert control.status_code == 200, (
        "KONTROLA: validna kategorija MORA biti 200 (ruta registrovana)."
    )

    response = client.get(
        "/sr/blog/kategorija/ne-postoji/", HTTP_HOST="localhost"
    )
    assert response.status_code == 404, (
        "Nepostojeća kategorija slug MORA biti 404 (get_object_or_404 — SM-D4)."
    )


def test_category_archive_htmx_returns_partial(client, make_post, make_category):
    activate("sr")
    k = make_category(name="Ratarstvo")
    _published(make_post, title="HTMX arhiva priča", category=k)

    response = client.get(
        f"/sr/blog/kategorija/{k.slug}/",
        HTTP_HOST="localhost",
        HTTP_HX_REQUEST="true",
    )

    assert response.status_code == 200
    html = response.content.decode("utf-8")
    assert "<!DOCTYPE" not in html and "<html" not in html.lower(), (
        "HTMX arhiva response MORA biti partial (_post_results.html), NE full page."
    )
    assert 'id="blog-results"' in html, (
        "HTMX arhiva MORA sadržati `id=\"blog-results\"` (REUSE _post_results.html)."
    )


def test_category_archive_empty_uses_filter_copy_not_home(
    client, make_post, make_category
):
    activate("sr")
    # validna kategorija postoji ali ima SAMO draft (0 published)
    k = make_category(name="Prazna kategorija")
    make_post(title="Samo draft u K", status="draft", published_at=None, category=k)

    response = client.get(f"/sr/blog/kategorija/{k.slug}/", HTTP_HOST="localhost")

    assert response.status_code == 200, (
        "Validna kategorija sa 0 published MORA biti 200 + empty state (resurs postoji)."
    )
    html = response.content.decode("utf-8")
    assert 'data-testid="blog-empty-filter"' in html, (
        "Arhiva-empty MORA renderovati FILTER-prikladnu kopiju "
        "(`data-testid=\"blog-empty-filter\"` — view prosleđuje active_filters; IMP-1)."
    )
    assert 'data-testid="blog-empty-home"' not in html, (
        "Arhiva-empty NE SME renderovati generičku home granu "
        "(`blog-empty-home` — to je index-empty kopija; IMP-1)."
    )
    # „prikaži sve" vodi na blog:index
    with override("sr"):
        index_url = reverse("blog:index")
    assert index_url in html, (
        "Arhiva-empty MORA imati 'prikazi sve' link na blog:index (IMP-1)."
    )


def test_category_archive_has_no_filter_dropdown(client, make_post, make_category):
    activate("sr")
    k = make_category(name="Ratarstvo")
    _published(make_post, title="Arhiva bez dropdowna", category=k)

    response = client.get(f"/sr/blog/kategorija/{k.slug}/", HTTP_HOST="localhost")

    assert response.status_code == 200
    html = response.content.decode("utf-8")
    assert '<select name="kategorija"' not in html, (
        "Arhiva je VEĆ filtrirana → NE SME imati filter dropdown "
        "(`<select name=\"kategorija\">` odsutan — IMP-6c/SM-D4)."
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
# AC9 / SM-D2 — future-dated (scheduled) exclusion na OBE arhive (TEA F-01)
# Post.published filtrira `published_at__lte=now` → scheduled (budući) post
# NE SME procuriti u arhivu (draft-not-leaked druga polovina granice).
# ─────────────────────────────────────────────────────────────────────────────


def test_category_archive_future_published_excluded(client, make_post, make_category):
    activate("sr")
    k = make_category(name="Ratarstvo")
    past = _published(make_post, title="Prošla objava u K", category=k)
    future = make_post(
        title="Zakazana objava u K",
        status="published",
        published_at=timezone.now() + timezone.timedelta(days=7),
        category=k,
    )

    response = client.get(f"/sr/blog/kategorija/{k.slug}/", HTTP_HOST="localhost")

    assert response.status_code == 200
    pks = {p.pk for p in response.context["posts"]}
    assert past.pk in pks, "Prošla published objava MORA biti u arhivi."
    assert future.pk not in pks, (
        "FUTURE-dated (scheduled) objava NE SME procuriti u kategorija-arhivi "
        "(Post.published filtrira published_at__lte=now — AC9/SM-D2)."
    )


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
