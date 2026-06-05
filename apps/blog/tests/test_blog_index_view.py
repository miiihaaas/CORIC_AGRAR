"""Story 5.2 — BlogIndexView (AC1) — TEA RED phase.

Pokriva AC1: javna `/sr/blog/` index strana koja listira `Post.published`
(NIKAD `Post.objects`) kao kartice, najnovije prvo. KLJUČNA draft-not-leaked
granica (SM-D2 / Gotcha BL2-1):
  - DRAFT post → NEVIDLJIV
  - PUBLISHED + future published_at → NEVIDLJIV (scheduled)
  - PUBLISHED + published_at=None → NEVIDLJIV (NULL <= now je False)
  - PUBLISHED + past published_at → VIDLJIV

`reverse("blog:index")` pod activate("sr") → `/sr/blog/`. Template
`blog/blog_index.html` (non-HTMX); `<h1>` naslov „Priče sa polja" (pun dijakritik).

⚠️ GUARD IMPORTS (collection-safety): apps.blog importi UNUTAR funkcija/fixtura,
NIKAD module-top-level — missing view/url daje per-test FAIL (RED), NE collection
abort. REUSE 5-1 conftest factory helpers (make_post / make_category).

RED phase: views.py / urls.py / templates NE postoje → 200/template asercije
FAIL (NoReverseMatch za blog:index, TemplateDoesNotExist).

Pokrenuti sa:  just test apps/blog/tests/test_blog_index_view.py

Refs:
- 5-2-...-filter.md AC1 + Task 8.2 + SM-D2 + Gotcha BL2-1
- 5-2-interface-contract.md § BlogIndexView
"""

from __future__ import annotations

import pytest
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import activate, override

pytestmark = pytest.mark.django_db


def _published_past(make_post, **overrides):
    """Helper: PUBLISHED objava sa published_at u prošlosti (vidljiva javno)."""
    defaults = {
        "status": "published",
        "published_at": timezone.now() - timezone.timedelta(days=1),
    }
    defaults.update(overrides)
    return make_post(**defaults)


# AC1: reverse("blog:index") pod activate("sr") → /sr/blog/
def test_blog_index_reverse_resolves_sr_prefix():
    with override("sr"):
        assert reverse("blog:index") == "/sr/blog/", (
            "reverse('blog:index') MORA razrešavati na /sr/blog/ (i18n_patterns)."
        )


# AC1: GET /sr/blog/ → 200, template blog/blog_index.html, context['posts']
def test_blog_index_get_200_and_template(client, make_post):
    activate("sr")
    _published_past(make_post, title="Žetva pšenice 2026")

    response = client.get("/sr/blog/", HTTP_HOST="localhost")

    assert response.status_code == 200
    templates = {t.name for t in response.templates if t.name}
    assert "blog/blog_index.html" in templates, (
        f"Non-HTMX GET /sr/blog/ MORA koristiti blog/blog_index.html. "
        f"Korišćeni template-i: {templates!r}."
    )
    assert "posts" in response.context, (
        "context['posts'] MORA postojati (context_object_name='posts')."
    )


# AC1: context_object_name == "posts"
def test_blog_index_context_object_name_is_posts(client, make_post):
    activate("sr")
    _published_past(make_post)

    response = client.get("/sr/blog/", HTTP_HOST="localhost")

    assert response.status_code == 200
    assert response.context.get("posts") is not None, (
        "context['posts'] MORA biti postavljen (context_object_name='posts')."
    )


# AC1: naslov „Priče sa polja" pun dijakritik u HTML
def test_blog_index_renders_title_full_diacritics(client, make_post):
    activate("sr")
    _published_past(make_post)

    response = client.get("/sr/blog/", HTTP_HOST="localhost")

    assert response.status_code == 200
    html = response.content.decode("utf-8")
    assert "Priče sa polja" in html, (
        "Index strana MORA renderovati naslov 'Priče sa polja' "
        "(pun dijakritik - NE sisana latinica)."
    )


# AC1 / SM-D2 / Gotcha BL2-1: DRAFT-NOT-LEAKED — samo PUBLISHED+past vidljiv
def test_blog_index_only_published_past_visible(client, make_post):
    """Četiri stanja: DRAFT, PUBLISHED+future, PUBLISHED+None, PUBLISHED+past.
    SAMO PUBLISHED+past sme biti u context['posts'] (Post.published manager).
    """
    activate("sr")
    now = timezone.now()

    draft = make_post(title="Nacrt o đubrenju", status="draft", published_at=None)
    future = make_post(
        title="Buduća žetva",
        status="published",
        published_at=now + timezone.timedelta(days=7),
    )
    published_none = make_post(
        title="Objavljena bez datuma",
        status="published",
        published_at=None,
    )
    past = make_post(
        title="Prošla žetva pšenice",
        status="published",
        published_at=now - timezone.timedelta(days=2),
    )

    response = client.get("/sr/blog/", HTTP_HOST="localhost")

    assert response.status_code == 200
    pks = {p.pk for p in response.context["posts"]}

    assert past.pk in pks, (
        f"PUBLISHED+past (pk={past.pk}) MORA biti vidljiv. Dobili: {pks!r}."
    )
    assert draft.pk not in pks, (
        f"DRAFT (pk={draft.pk}) NE SME procuriti javno — koristi Post.published, "
        f"NE Post.objects (SM-D2/Gotcha BL2-1). Dobili: {pks!r}."
    )
    assert future.pk not in pks, (
        f"PUBLISHED+future (pk={future.pk}) NE SME biti vidljiv (scheduled). "
        f"Dobili: {pks!r}."
    )
    assert published_none.pk not in pks, (
        f"PUBLISHED+published_at=None (pk={published_none.pk}) NE SME biti vidljiv "
        f"(NULL <= now je False). Dobili: {pks!r}."
    )


# AC1: najnovije prvo (Meta.ordering = ["-published_at", "-created_at"])
def test_blog_index_newest_first(client, make_post):
    activate("sr")
    now = timezone.now()

    older = make_post(
        title="Starija priča",
        status="published",
        published_at=now - timezone.timedelta(days=10),
    )
    newer = make_post(
        title="Novija priča",
        status="published",
        published_at=now - timezone.timedelta(days=1),
    )

    response = client.get("/sr/blog/", HTTP_HOST="localhost")

    assert response.status_code == 200
    ordered_pks = [p.pk for p in response.context["posts"]]
    assert ordered_pks.index(newer.pk) < ordered_pks.index(older.pk), (
        f"Najnovija objava (pk={newer.pk}) MORA biti PRE starije (pk={older.pk}) "
        f"— Meta.ordering najnovije-prvo. Dobili redosled: {ordered_pks!r}."
    )
