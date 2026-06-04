"""Story 5.1 — apps/blog/migrations/0001_initial schema migracija (TEA RED phase).

Pokriva AC2 (IMP-7: PREFERIRA introspekciju operations liste NAD migrate-zero
round-trip-om u pytest sesiji — round-trip može poremetiti deljeno test-DB stanje):
  - 0001_initial postoji
  - CreateModel Category + Tag PRE Post (IMP-6 — Post FK-uje Category, M2M-uje Tag)
  - M2M post_tags through-tabela (kroz Post.tags)
  - modeltranslation _sr/_hu/_en kolone za translatable polja (title/perex/body/name/description)
  - index blog_post_status_pub_idx
  - status max_length>=9 ("published")
  - swappable_dependency(AUTH_USER_MODEL) za author FK
  - REGRESSION: makemigrations --check → no changes (DB-level state validacija kroz ORM)

⚠️ GUARD: apps.blog importi UNUTAR funkcija (collection-safety).

TEA RED phase: SVI testovi MORAJU pasti — apps.blog NE postoji (migracija ne postoji).

Refs:
- 5-1-...-admin-stub.md AC2 + Task 8.6 + SM-D4 + IMP-6/IMP-7
- 5-1-interface-contract.md § 5 (migracija)
- apps/forms/tests/test_lead_migrations.py (round-trip precedent)
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.django_db


# AC2: 0001_initial postoji i učitava se (Migration klasa prisutna)
def test_initial_migration_exists():
    import importlib

    module = importlib.import_module("apps.blog.migrations.0001_initial")
    assert hasattr(module, "Migration"), (
        "apps/blog/migrations/0001_initial.py MORA imati Migration klasu — AC2."
    )


# AC2 / IMP-6: CreateModel Category + Tag PRE CreateModel Post
def test_create_model_order_category_tag_before_post():
    import importlib

    from django.db import migrations

    module = importlib.import_module("apps.blog.migrations.0001_initial")
    create_order = [
        op.name
        for op in module.Migration.operations
        if isinstance(op, migrations.CreateModel)
    ]
    assert {"Category", "Tag", "Post"}.issubset(set(create_order)), (
        f"0001 MORA imati CreateModel za Category/Tag/Post, dobio {create_order}."
    )
    assert create_order.index("Category") < create_order.index("Post"), (
        f"CreateModel('Category') MORA biti PRE CreateModel('Post') (Post FK-uje Category; "
        f"IMP-6), dobio redosled {create_order}."
    )
    assert create_order.index("Tag") < create_order.index("Post"), (
        f"CreateModel('Tag') MORA biti PRE CreateModel('Post') (Post M2M-uje Tag; IMP-6), "
        f"dobio redosled {create_order}."
    )


# AC2: swappable_dependency(AUTH_USER_MODEL) prisutan u dependencies (author FK)
def test_swappable_dependency_for_auth_user():
    import importlib

    from django.conf import settings

    module = importlib.import_module("apps.blog.migrations.0001_initial")
    deps = module.Migration.dependencies
    # swappable_dependency vraća tuple ('__setting__', 'AUTH_USER_MODEL') ili (app, mig)
    app_label = settings.AUTH_USER_MODEL.split(".")[0]
    has_user_dep = any(
        (dep[0] == app_label) or (dep[0] == "__setting__" and "AUTH_USER_MODEL" in str(dep[1]))
        for dep in deps
    )
    assert has_user_dep, (
        f"0001 dependencies MORA sadržati swappable_dependency(AUTH_USER_MODEL) za author FK "
        f"(IMP-6), dobio {deps}."
    )


# AC2: status kolona max_length >= 9 (pokriva "published"; round-trip iz DB)
def test_status_column_holds_published_value():
    from apps.blog.models import Post

    post = Post.objects.create(
        title="Žetva pšenice 2026",
        status=Post.Status.PUBLISHED,
    )
    refetched = Post.objects.get(pk=post.pk)
    assert refetched.status == "published", (
        f"status DB round-trip MORA vratiti 'published' (max_length pokriva 9 znakova), "
        f"dobio {refetched.status!r}."
    )


# AC2: modeltranslation _sr/_hu/_en kolone materijalizovane u DB (round-trip set/get)
def test_translation_columns_persist_in_db():
    from apps.blog.models import Post

    post = Post.objects.create(title="Žetva pšenice 2026")
    post.title_hu = "Búza aratás 2026"
    post.body_en = "Wheat harvest body."
    post.save()
    refetched = Post.objects.get(pk=post.pk)
    assert refetched.title_hu == "Búza aratás 2026", (
        "title_hu DB kolona MORA persistirati (modeltranslation _hu kolona u 0001) — AC2."
    )
    assert refetched.body_en == "Wheat harvest body.", (
        "body_en DB kolona MORA persistirati (modeltranslation _en kolona u 0001) — AC2."
    )


# AC2: M2M post_tags through-tabela radi (round-trip set/get)
def test_m2m_post_tags_through_table():
    from apps.blog.models import Post, Tag

    post = Post.objects.create(title="Žetva pšenice 2026")
    tag = Tag.objects.create(name="Pšenica")
    post.tags.add(tag)
    refetched = Post.objects.get(pk=post.pk)
    assert list(refetched.tags.all()) == [tag], (
        "Post.tags M2M (post_tags through-tabela) MORA persistirati — AC2."
    )
    # related_name "posts" round-trip
    assert list(tag.posts.all()) == [post], (
        "Tag.posts (M2M related_name) MORA vratiti povezan Post — AC1/AC2."
    )


# AC2: index blog_post_status_pub_idx prisutan u migraciji (AddIndex ILI Meta.indexes)
def test_index_present_in_migration_or_meta():
    from apps.blog.models import Post

    names = {idx.name for idx in Post._meta.indexes}
    assert "blog_post_status_pub_idx" in names, (
        f"blog_post_status_pub_idx MORA biti u Post.Meta.indexes (materijalizovan u 0001) — AC2. "
        f"Pronađeni: {names}."
    )


# AC2 / REGRESSION: makemigrations --check → no changes (blog/0001 finalan; nijedan
# drugi app nije dotaknut dodavanjem apps.blog)
def test_no_pending_migrations():
    from io import StringIO

    from django.core.management import call_command

    out = StringIO()
    # --check exit kod ≠ 0 ako ima pending migracija; SystemExit hvatamo kao FAIL signal
    try:
        call_command("makemigrations", "--check", "--dry-run", stdout=out, stderr=out)
    except SystemExit as exc:  # pragma: no cover - GREEN faza: ne sme se desiti
        pytest.fail(
            f"makemigrations --check MORA biti čist (blog/0001 finalan; nijedan postojeći "
            f"app NE dobija novu migraciju dodavanjem apps.blog) — AC2 REGRESSION. "
            f"Pending output:\n{out.getvalue()}\nexit={exc.code}"
        )


# AC2: NEMA data seed — blog startuje PRAZAN (count==0 na čistoj test bazi)
def test_no_data_seed_blog_starts_empty():
    from apps.blog.models import Category, Post, Tag

    assert Post.objects.count() == 0, "Post MORA startovati PRAZAN (NEMA data seed — SM-D4)."
    assert Category.objects.count() == 0, "Category MORA startovati PRAZAN (SM-D4)."
    assert Tag.objects.count() == 0, "Tag MORA startovati PRAZAN (SM-D4)."
