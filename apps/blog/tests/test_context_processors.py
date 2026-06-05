"""Story 5.4 — `apps.blog.context_processors.latest_blog_posts` — TEA RED phase.

Pokriva AC1/AC2/AC3/AC4/AC7(shape) + AC8(i18n shape) za NOVI context processor
`latest_blog_posts(request)` koji exposes ≤3 NAJNOVIJE PUBLISHED objave svim
template-ima, umotano u `SimpleLazyObject` (upit puca SAMO na iteraciji — SM-D2).

Render-level lock-ovi (footer markup, 0/1-query lazy, link href, empty placeholder)
su u `test_footer_news.py`. Ovaj fajl testira VREDNOST koju processor exposes
(kroz `response.context["latest_blog_posts"]` ILI direktan poziv funkcije).

⚠️ GUARD IMPORTS (collection-safety): `apps.blog.context_processors` se NIKAD ne
importuje na module-top-level (modul NE postoji u RED fazi → top-level import bi
oborio collection CELE suite). Pristup ide kroz:
  - `client.get(reverse("pages:home"))` → `response.context["latest_blog_posts"]`
    (RequestContext → context processor radi); ili
  - lazy import UNUTAR test funkcije.
Tako missing modul / nedostajuća registracija daje čist per-test FAIL (KeyError /
ImportError UNUTAR test body-ja), NE collection abort.

RED razlog: (a) `apps/blog/context_processors.py` modul NE postoji; (b) NIJE
registrovan u `config/settings/base.py` context_processors listi → ključ
`latest_blog_posts` NIJE u `response.context` → KeyError / assertion FAIL.

Pokrenuti sa:  just test apps/blog/tests/test_context_processors.py

Refs:
- 5-4-...-kolona.md AC1-AC4/AC7/AC8 + SM-D1/SM-D2/SM-D3 + Task 5.1-5.5
- 5-4-interface-contract.md § latest_blog_posts
- apps/blog/tests/conftest.py (make_post / make_category factory helpers — REUSE)
"""

from __future__ import annotations

import pytest
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import activate

pytestmark = pytest.mark.django_db


# ── Seed helpers (DISTINCT timestamps — SM-D1 anti-flaky; NIKAD same-timestamp) ──


def _published(make_post, *, days_ago_published, days_ago_created=None, **overrides):
    """PUBLISHED objava sa EKSPLICITNIM distinct published_at/created_at.

    `created_at` je auto_now_add → postavlja se posle create() kroz update() da
    bismo dobili DETERMINISTIČKE, distinct timestamp-e (auto_now_add može dati
    identičan timestamp u brzom seed-u → flaky ordering; SM-D1 NIT).
    """
    from apps.blog.models import Post

    now = timezone.now()
    defaults = {
        "status": "published",
        "published_at": now - timezone.timedelta(days=days_ago_published),
    }
    defaults.update(overrides)
    post = make_post(**defaults)
    if days_ago_created is not None:
        created = now - timezone.timedelta(days=days_ago_created)
        # auto_now_add polje — zaobiđi kroz queryset .update() (ne okida save()).
        Post.objects.filter(pk=post.pk).update(created_at=created)
        post.refresh_from_db()
    return post


def _home_context_posts(client):
    """Render full page (pages:home → base.html → footer) i vrati materijalizovanu
    listu iz `latest_blog_posts`.

    KRITIČNO: koristi `client.get` (pravi RequestContext → context processor radi).
    NE koristi render_to_string (bypass-uje context processore — LAŽNO prazan).
    """
    response = client.get(reverse("pages:home"), HTTP_HOST="localhost")
    assert response.status_code == 200
    assert "latest_blog_posts" in response.context, (
        "Ključ 'latest_blog_posts' MORA biti u response.context "
        "(context processor `apps.blog.context_processors.latest_blog_posts` "
        "registrovan u config/settings/base.py)."
    )
    # SimpleLazyObject → materijalizuj u listu (iteracija razrešava lazy)
    return list(response.context["latest_blog_posts"])


# ── AC1 — ≤3 PUBLISHED (Post.published; SimpleLazyObject) ─────────────────────


# AC1: 5 published → tačno 3 (najnovije 3)
def test_latest_blog_posts_caps_at_three(client, make_post):
    activate("sr")
    for i in range(5):
        _published(make_post, title=f"Objava broj {i}", days_ago_published=i + 1)

    posts = _home_context_posts(client)

    assert len(posts) == 3, (
        f"latest_blog_posts MORA biti ograničen na ≤3 (LIMIT [:3]). "
        f"5 published → dobili {len(posts)} objava."
    )


# AC1: vrednost je SimpleLazyObject (lazy wrapper — SM-D2)
def test_latest_blog_posts_is_simple_lazy_object(client, make_post):
    activate("sr")
    _published(make_post, title="Jedina objava", days_ago_published=1)

    response = client.get(reverse("pages:home"), HTTP_HOST="localhost")
    assert response.status_code == 200
    assert "latest_blog_posts" in response.context, (
        "Ključ 'latest_blog_posts' MORA biti u response.context (registrovan processor)."
    )

    from django.utils.functional import SimpleLazyObject

    value = response.context["latest_blog_posts"]
    assert isinstance(value, SimpleLazyObject), (
        f"latest_blog_posts MORA biti SimpleLazyObject (SM-D2 — upit SAMO na "
        f"iteraciji). Dobili tip {type(value)!r}."
    )


# AC1: unit shape — direktan poziv funkcije vraća dict sa ključem latest_blog_posts
def test_latest_blog_posts_callable_returns_dict_shape(make_post):
    activate("sr")
    _published(make_post, title="Shape objava", days_ago_published=1)

    # Lazy import UNUTAR funkcije (modul ne postoji u RED → čist ImportError ovde,
    # NE collection abort).
    from django.test import RequestFactory

    from apps.blog.context_processors import latest_blog_posts

    result = latest_blog_posts(RequestFactory().get("/"))

    assert isinstance(result, dict), (
        "latest_blog_posts(request) MORA vratiti dict."
    )
    assert "latest_blog_posts" in result, (
        "Vraćeni dict MORA imati ključ 'latest_blog_posts'."
    )
    materialized = list(result["latest_blog_posts"])
    assert len(materialized) == 1


# ── AC2 — Najnovije-prvo po published_at (NE created_at — SM-D1 LOAD-BEARING) ──


def test_ordering_is_published_at_first_not_created_at(client, make_post):
    """SM-D1 LOAD-BEARING: objava A (created_at STAR, published_at DANAS) MORA
    biti PRE objave B (created_at SKORIJI, published_at JUČE).

    Pod `created_at`-prvo ordering B bi bio prvi → POGREŠNO. Test dokazuje
    EKSPLICITAN `.order_by("-published_at", "-created_at")` (published_at primarni).
    """
    activate("sr")

    # A: dugo-draftovana (created pre 90d), objavljena DANAS (published 0d ago)
    post_a = _published(
        make_post,
        title="Dugo draftovana objavljena danas",
        days_ago_published=0,
        days_ago_created=90,
    )
    # B: skoro kreirana (created pre 1d), objavljena JUČE (published 1d ago)
    post_b = _published(
        make_post,
        title="Skoro kreirana objavljena juce",
        days_ago_published=1,
        days_ago_created=1,
    )

    posts = _home_context_posts(client)
    ordered_pks = [p.pk for p in posts]

    assert post_a.pk in ordered_pks and post_b.pk in ordered_pks, (
        f"Obe objave MORAJU biti prisutne. Dobili: {ordered_pks!r}."
    )
    assert ordered_pks.index(post_a.pk) < ordered_pks.index(post_b.pk), (
        f"Objava A (published DANAS, created STAR, pk={post_a.pk}) MORA biti PRE "
        f"objave B (published JUČE, created SKORIJI, pk={post_b.pk}) — dokazuje "
        f"published_at-PRVO ordering (NE created_at; SM-D1). Dobili redosled: "
        f"{ordered_pks!r}. (Pod created_at-prvo bi B bio prvi → POGREŠNO.)"
    )


# AC2: opšti newest-first (sve published_at distinct)
def test_ordering_newest_published_first(client, make_post):
    activate("sr")
    oldest = _published(make_post, title="Najstarija", days_ago_published=30)
    middle = _published(make_post, title="Srednja", days_ago_published=10)
    newest = _published(make_post, title="Najnovija", days_ago_published=1)

    posts = _home_context_posts(client)
    ordered_pks = [p.pk for p in posts]

    assert ordered_pks == [newest.pk, middle.pk, oldest.pk], (
        f"Redosled MORA biti najnovije-objavljeno-prvo "
        f"[{newest.pk}, {middle.pk}, {oldest.pk}]. Dobili: {ordered_pks!r}."
    )


# ── AC3 — draft-not-leaked: draft + future EXCLUDED (SM-D3) ───────────────────


def test_draft_and_future_excluded(client, make_post):
    """Mix: published(past) + draft + future(published+future) →
    SAMO published(past); draft NIJE; future NIJE. Ista granica kao 5-2/5-3.
    """
    activate("sr")
    now = timezone.now()

    visible = _published(
        make_post, title="Vidljiva objavljena", days_ago_published=1
    )
    draft = make_post(
        title="Nacrt o đubrenju", status="draft", published_at=None
    )
    future = make_post(
        title="Buduća zakazana",
        status="published",
        published_at=now + timezone.timedelta(days=7),
    )

    posts = _home_context_posts(client)
    pks = {p.pk for p in posts}

    assert visible.pk in pks, (
        f"PUBLISHED+past (pk={visible.pk}) MORA biti prisutan. Dobili: {pks!r}."
    )
    assert draft.pk not in pks, (
        f"DRAFT (pk={draft.pk}) NE SME procuriti u footer (sajt-wide leak; "
        f"koristi Post.published, NE Post.objects — SM-D3). Dobili: {pks!r}."
    )
    assert future.pk not in pks, (
        f"FUTURE (published+future, pk={future.pk}) NE SME biti vidljiv "
        f"(scheduled — published_at__lte=now granica). Dobili: {pks!r}."
    )
    # TEA N3: EXACT-set lock — vraćeni skup je TAČNO {visible} (ni jedan curenje
    # ne sme da se sakrije iza co-witness pojedinačnih in/not-in asercija).
    assert pks == {visible.pk}, (
        f"latest_blog_posts MORA sadržati TAČNO {{visible.pk={visible.pk}}} — "
        f"NI draft (pk={draft.pk}) NI future (pk={future.pk}) NE smeju curiti. "
        f"Dobili: {pks!r}."
    )


# ── AC4 — <3 → renderuje koliko ima (NE padding, NE None) ─────────────────────


def test_two_published_yields_two(client, make_post):
    activate("sr")
    _published(make_post, title="Prva", days_ago_published=2)
    _published(make_post, title="Druga", days_ago_published=1)

    posts = _home_context_posts(client)

    assert len(posts) == 2, (
        f"2 published → latest_blog_posts MORA imati TAČNO 2 (NE padding na 3, "
        f"NE None). Dobili {len(posts)}."
    )


def test_one_published_yields_one(client, make_post):
    activate("sr")
    _published(make_post, title="Jedina", days_ago_published=1)

    posts = _home_context_posts(client)

    assert len(posts) == 1, (
        f"1 published → latest_blog_posts MORA imati TAČNO 1. Dobili {len(posts)}."
    )


def test_zero_published_yields_empty_list(client, make_post):
    """0 published (samo draft + future) → prazna lista (NE None, NE crash)."""
    activate("sr")
    now = timezone.now()
    make_post(title="Samo nacrt", status="draft", published_at=None)
    make_post(
        title="Samo buduca",
        status="published",
        published_at=now + timezone.timedelta(days=3),
    )

    posts = _home_context_posts(client)

    assert posts == [], (
        f"0 PUBLISHED (samo draft/future) → latest_blog_posts MORA biti prazna "
        f"lista (empty-state placeholder grana). Dobili: {posts!r}."
    )


# ── AC8 — i18n: post.title u aktivnoj lokali (modeltranslation shape) ─────────


def test_title_reflects_active_locale(client, make_post):
    """post.title je modeltranslation virtuelni atribut → /hu/ → title_hu,
    /sr/ → title_sr. Smoke kroz context vrednost (render-link assert je u
    test_footer_news.py).
    """
    activate("sr")

    now = timezone.now()
    post = make_post(
        title="Žetva pšenice 2026",
        status="published",
        published_at=now - timezone.timedelta(days=1),
    )
    post.title_hu = "Búza aratás 2026"
    post.save()

    # sr lokala
    response_sr = client.get("/sr/", HTTP_HOST="localhost")
    assert response_sr.status_code == 200
    assert "latest_blog_posts" in response_sr.context, (
        "latest_blog_posts MORA biti u context-u (registrovan processor)."
    )
    sr_titles = [p.title for p in response_sr.context["latest_blog_posts"]]
    assert "Žetva pšenice 2026" in sr_titles, (
        f"sr lokala → title_sr 'Žetva pšenice 2026'. Dobili: {sr_titles!r}."
    )

    # hu lokala
    response_hu = client.get("/hu/", HTTP_HOST="localhost")
    assert response_hu.status_code == 200
    hu_titles = [p.title for p in response_hu.context["latest_blog_posts"]]
    assert "Búza aratás 2026" in hu_titles, (
        f"hu lokala → title_hu 'Búza aratás 2026' (modeltranslation aktivna "
        f"lokala). Dobili: {hu_titles!r}. (pk={post.pk})"
    )
