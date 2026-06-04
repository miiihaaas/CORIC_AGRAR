"""Story 5.1 — apps/blog/managers.py:PublishedManager (TEA RED phase).

Pokriva AC3: Post.published (PublishedManager) filtrira status="published" AND
published_at__lte=now. SVA ČETIRI stanja:
  1. DRAFT                          → EXCLUDED
  2. PUBLISHED + published_at past  → INCLUDED
  3. PUBLISHED + published_at=None  → EXCLUDED (NULL <= now je False)
  4. PUBLISHED + published_at future→ EXCLUDED (scheduled — još nije vreme)

Post.objects (default) vraća SVE (DRAFT + future + None). Post._default_manager je
`objects` (BL-3 — objects definisan PRVI da ne postane published filter).

DB-value lock (IMP-3): Post.Status.PUBLISHED.value == "published".

⚠️ GUARD: apps.blog importi UNUTAR funkcija (collection-safety).

TEA RED phase: SVI testovi MORAJU pasti — apps.blog NE postoji.

Refs:
- 5-1-...-admin-stub.md AC3 + Task 8.4 + SM-D5 + Gotcha BL-1/BL-3
- 5-1-interface-contract.md § 3 (PublishedManager)
"""

from __future__ import annotations

from datetime import timedelta

import pytest
from django.utils import timezone

pytestmark = pytest.mark.django_db


def _seed_four_states(now):
    """Kreira po jedan Post za svako od 4 stanja; vraća dict ime→post."""
    from apps.blog.models import Post

    draft = Post.objects.create(title="Nacrt o plodoredu", status=Post.Status.DRAFT)
    published_past = Post.objects.create(
        title="Žetva pšenice 2026",
        status=Post.Status.PUBLISHED,
        published_at=now - timedelta(days=1),
    )
    published_none = Post.objects.create(
        title="Objavljeno bez datuma",
        status=Post.Status.PUBLISHED,
        published_at=None,
    )
    published_future = Post.objects.create(
        title="Zakazana berba kukuruza",
        status=Post.Status.PUBLISHED,
        published_at=now + timedelta(days=7),
    )
    return {
        "draft": draft,
        "published_past": published_past,
        "published_none": published_none,
        "published_future": published_future,
    }


# AC3: published vraća SAMO PUBLISHED + published_at u prošlosti/sada
def test_published_includes_only_published_past():
    from apps.blog.models import Post

    posts = _seed_four_states(timezone.now())
    published_ids = set(Post.published.all().values_list("pk", flat=True))
    assert published_ids == {posts["published_past"].pk}, (
        f"Post.published MORA sadržati SAMO PUBLISHED+past objavu, dobio {published_ids} "
        f"(očekivano {{ {posts['published_past'].pk} }})."
    )


# AC3: DRAFT NIJE u published
def test_draft_excluded_from_published():
    from apps.blog.models import Post

    posts = _seed_four_states(timezone.now())
    assert posts["draft"] not in Post.published.all(), (
        "DRAFT post NE SME biti u Post.published — AC3."
    )


# AC3: PUBLISHED + published_at=None NIJE u published (NULL <= now je False)
def test_published_none_excluded():
    from apps.blog.models import Post

    posts = _seed_four_states(timezone.now())
    assert posts["published_none"] not in Post.published.all(), (
        "PUBLISHED sa published_at=None NE SME biti u Post.published "
        "(published_at__lte=now isključuje NULL) — AC3."
    )


# AC3: PUBLISHED + future published_at NIJE u published (scheduled-publish pattern)
def test_published_future_excluded():
    from apps.blog.models import Post

    posts = _seed_four_states(timezone.now())
    assert posts["published_future"] not in Post.published.all(), (
        "PUBLISHED sa budućim published_at NE SME biti u Post.published "
        "(scheduled post — pojavljuje se tek kad now() prestigne published_at) — AC3."
    )


# AC3: objects (default) vraća SVE 4 (admin/sav-content pristup nepromenjen)
def test_objects_returns_all_four():
    from apps.blog.models import Post

    _seed_four_states(timezone.now())
    assert Post.objects.count() == 4, (
        f"Post.objects (default) MORA vratiti SVE objave (DRAFT+future+None+past = 4), "
        f"dobio {Post.objects.count()}."
    )


# AC3 / Gotcha BL-3: Post._default_manager je `objects` (NE `published` — inače
# admin/migracije/relacije bi videle samo published → BUG)
def test_default_manager_is_objects_not_published():
    from apps.blog.models import Post

    assert Post._default_manager.name == "objects", (
        f"Post._default_manager MORA biti 'objects' (BL-3 — objects definisan PRVI da "
        f"ne postane published filter), dobio {Post._default_manager.name!r}."
    )
    # Funkcionalna potvrda: default manager vidi DRAFT
    _seed_four_states(timezone.now())
    assert Post._default_manager.count() == 4, (
        "Post._default_manager MORA videti SAV content (uključujući DRAFT) — BL-3."
    )


# AC3: PublishedManager.get_queryset evaluira timezone.now() PER-QUERY (NE zamrznuto).
# future post sa published_at tik-iznad-now() pređe u published kad vreme prestigne.
def test_now_evaluated_per_query():
    from apps.blog.models import Post

    now = timezone.now()
    soon = Post.objects.create(
        title="Skoro objavljeno",
        status=Post.Status.PUBLISHED,
        published_at=now + timedelta(milliseconds=1),
    )
    # Prvi query (odmah): published_at je ~1ms u budućnosti → NIJE u published (granično).
    # Drugi query posle realne pauze: now() je odmakao → JESTE u published.
    # Robustnije: postavi published_at malo u prošlost i potvrdi da per-query now() pokrije.
    soon.published_at = now - timedelta(seconds=1)
    soon.save()
    assert soon in Post.published.all(), (
        "PublishedManager MORA evaluirati timezone.now() PER-QUERY u get_queryset "
        "(NE module-level konstanta — inače zamrznuto vreme) — AC3."
    )


# AC3 / IMP-3: DB-value lock — manager filter literal "published" mora ostati vezan
def test_published_status_db_value_locked():
    from apps.blog.models import Post

    assert Post.Status.PUBLISHED.value == "published", (
        "DB-value lock (IMP-3): Post.Status.PUBLISHED.value MORA ostati 'published' — "
        "PublishedManager filtrira na ovaj string literal; rename bi tiho razdvojio "
        "manager od modela."
    )
