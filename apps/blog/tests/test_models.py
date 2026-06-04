"""Story 5.1 — apps/blog/models.py Category/Tag/Post modeli (TEA RED phase).

Pokriva AC1: 3 modela nasleđuju SluggedModel+TimestampedModel; tačna polja+tipovi;
FK category SET_NULL related_name="posts"; M2M tags related_name="posts"; FK author
→ settings.AUTH_USER_MODEL SET_NULL null=True related_name="blog_posts"; status
TextChoices DRAFT="draft"/PUBLISHED="published" default DRAFT; published_at nullable;
slug auto-gen iz title/name kroz slugify_ascii; slug unique (kolizija → IntegrityError);
__str__; Meta.ordering/verbose_name/indexes (blog_post_status_pub_idx).

DB-value lock (IMP-3): Post.Status.PUBLISHED.value == "published" (zaključava DB string
na koji PublishedManager + 5.2/5.3/5.4 query-i ciljaju).

⚠️ GUARD: apps.blog importi su UNUTAR test funkcija (collection-safety — missing
apps.blog daje per-test FAIL, NE collection abort).

TEA RED phase: SVI testovi MORAJU pasti — apps.blog NE postoji.

Refs:
- 5-1-...-admin-stub.md AC1 + Task 8.2
- 5-1-interface-contract.md § 2 (modeli)
- apps/products/models.py (Product PATTERN 1:1)
"""

from __future__ import annotations

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, models

from apps.core.models import SluggedModel, TimestampedModel

pytestmark = pytest.mark.django_db


# =============================================================================
# AC1 — Inheritance (SluggedModel + TimestampedModel)
# =============================================================================


# AC1: sva 3 modela nasleđuju SluggedModel + TimestampedModel
def test_models_inherit_slugged_and_timestamped():
    from apps.blog.models import Category, Post, Tag

    for model in (Category, Tag, Post):
        assert issubclass(model, SluggedModel), (
            f"{model.__name__} MORA nasleđivati SluggedModel (slug globally unique — AC1)."
        )
        assert issubclass(model, TimestampedModel), (
            f"{model.__name__} MORA nasleđivati TimestampedModel (created_at/updated_at — AC1)."
        )


# AC1: nasleđena polja slug(unique,db_index,max_length=140) + created_at + updated_at
def test_inherited_slug_and_timestamp_fields():
    from apps.blog.models import Post

    slug_field = Post._meta.get_field("slug")
    assert slug_field.unique is True, "slug MORA biti unique (SluggedModel — AC1)."
    assert slug_field.db_index is True, "slug MORA biti db_index (SluggedModel — AC1)."
    assert slug_field.max_length == 140, (
        f"slug max_length MORA biti 140 (SluggedModel), dobio {slug_field.max_length}."
    )
    assert Post._meta.get_field("created_at") is not None
    assert Post._meta.get_field("updated_at") is not None


# =============================================================================
# AC1 — Category
# =============================================================================


# AC1: Category polja + tipovi (name CharField 200, description TextField blank)
def test_category_fields():
    from apps.blog.models import Category

    name = Category._meta.get_field("name")
    assert isinstance(name, models.CharField) and name.max_length == 200, (
        "Category.name MORA biti CharField(max_length=200) — AC1."
    )
    description = Category._meta.get_field("description")
    assert isinstance(description, models.TextField) and description.blank is True, (
        "Category.description MORA biti TextField(blank=True) — AC1."
    )


# AC1: Category slug auto-gen iz name + __str__ + Meta.ordering
def test_category_slug_autogen_and_str_and_ordering():
    from apps.blog.models import Category

    cat = Category.objects.create(name="Ratarstvo i Đubrenje")
    assert cat.slug == "ratarstvo-i-dubrenje", (
        f"Category.slug MORA auto-gen iz name kroz slugify_ascii (Đ→D), dobio {cat.slug!r}."
    )
    assert str(cat) == cat.name, "Category.__str__ MORA vraćati name."
    assert list(Category._meta.ordering) == ["name"], (
        f"Category.Meta.ordering MORA biti ['name'], dobio {Category._meta.ordering}."
    )


# =============================================================================
# AC1 — Tag
# =============================================================================


# AC1: Tag polja (name CharField 100) + slug auto-gen + __str__ + ordering
def test_tag_fields_and_slug_and_str():
    from apps.blog.models import Tag

    name = Tag._meta.get_field("name")
    assert isinstance(name, models.CharField) and name.max_length == 100, (
        "Tag.name MORA biti CharField(max_length=100) — AC1."
    )
    tag = Tag.objects.create(name="Žetva")
    assert tag.slug == "zetva", (
        f"Tag.slug MORA auto-gen iz name kroz slugify_ascii (Ž→z), dobio {tag.slug!r}."
    )
    assert str(tag) == tag.name, "Tag.__str__ MORA vraćati name."
    assert list(Tag._meta.ordering) == ["name"], (
        f"Tag.Meta.ordering MORA biti ['name'], dobio {Tag._meta.ordering}."
    )


# =============================================================================
# AC1 — Post fields
# =============================================================================


# AC1: Post skalarna polja (title/perex/body/main_image/published_at) + tipovi
def test_post_scalar_fields():
    from apps.blog.models import Post

    title = Post._meta.get_field("title")
    assert isinstance(title, models.CharField) and title.max_length == 200, (
        "Post.title MORA biti CharField(max_length=200) — AC1."
    )
    perex = Post._meta.get_field("perex")
    assert isinstance(perex, models.TextField) and perex.blank is True, (
        "Post.perex MORA biti TextField(blank=True) — AC1."
    )
    body = Post._meta.get_field("body")
    assert isinstance(body, models.TextField) and body.blank is True, (
        "Post.body MORA biti TextField(blank=True) — plain (NE WYSIWYG; SM-D10) — AC1."
    )
    main_image = Post._meta.get_field("main_image")
    assert isinstance(main_image, models.ImageField), (
        "Post.main_image MORA biti ImageField — AC1."
    )
    assert main_image.null is True and main_image.blank is True, (
        "Post.main_image MORA biti null=True, blank=True — AC1."
    )
    # Storage-path lock (TEST_GAP-2): upload_to + max_length zaključavaju lokaciju
    # media fajla — tihi rename upload_to-a / smanjenje max_length-a se hvata.
    assert main_image.upload_to == "blog/main/", (
        f"Post.main_image upload_to MORA biti 'blog/main/' (storage-path lock), "
        f"dobio {main_image.upload_to!r}."
    )
    assert main_image.max_length == 255, (
        f"Post.main_image max_length MORA biti 255, dobio {main_image.max_length}."
    )
    published_at = Post._meta.get_field("published_at")
    assert isinstance(published_at, models.DateTimeField), (
        "Post.published_at MORA biti DateTimeField — AC1."
    )
    assert published_at.null is True and published_at.blank is True, (
        "Post.published_at MORA biti null=True, blank=True — AC1."
    )


# AC1: Post.category FK → blog.Category, on_delete=SET_NULL, related_name="posts", null/blank
def test_post_category_fk():
    from apps.blog.models import Category, Post

    field = Post._meta.get_field("category")
    assert isinstance(field, models.ForeignKey), "Post.category MORA biti ForeignKey — AC1."
    assert field.related_model is Category, "Post.category MORA referencirati blog.Category."
    assert field.remote_field.on_delete is models.SET_NULL, (
        "Post.category on_delete MORA biti SET_NULL (brisanje kategorije NE briše objave) — AC1."
    )
    assert field.null is True and field.blank is True, (
        "Post.category MORA biti null=True, blank=True — AC1."
    )
    assert field.remote_field.related_name == "posts", (
        f"Post.category related_name MORA biti 'posts', dobio {field.remote_field.related_name!r}."
    )


# AC1: Post.tags M2M → blog.Tag, related_name="posts", blank
def test_post_tags_m2m():
    from apps.blog.models import Post, Tag

    field = Post._meta.get_field("tags")
    assert isinstance(field, models.ManyToManyField), "Post.tags MORA biti ManyToManyField — AC1."
    assert field.related_model is Tag, "Post.tags MORA referencirati blog.Tag."
    assert field.blank is True, "Post.tags MORA biti blank=True — AC1."
    assert field.remote_field.related_name == "posts", (
        f"Post.tags related_name MORA biti 'posts', dobio {field.remote_field.related_name!r}."
    )


# AC1 / SM-D3: Post.author FK → settings.AUTH_USER_MODEL (NIKAD direktan User import),
# on_delete=SET_NULL, related_name="blog_posts", null/blank
def test_post_author_fk_uses_auth_user_model():
    from apps.blog.models import Post

    field = Post._meta.get_field("author")
    assert isinstance(field, models.ForeignKey), "Post.author MORA biti ForeignKey — AC1."
    assert field.related_model is get_user_model(), (
        "Post.author MORA referencirati settings.AUTH_USER_MODEL (kroz get_user_model()), "
        "NIKAD direktan `from django.contrib.auth.models import User` (project-context.md:595 / SM-D3)."
    )
    assert field.remote_field.on_delete is models.SET_NULL, (
        "Post.author on_delete MORA biti SET_NULL (brisanje autora NE briše objavljen content) — SM-D3."
    )
    assert field.null is True and field.blank is True, (
        "Post.author MORA biti null=True, blank=True — SM-D3."
    )
    assert field.remote_field.related_name == "blog_posts", (
        f"Post.author related_name MORA biti 'blog_posts', dobio {field.remote_field.related_name!r}."
    )


# AC1: NEMA cross-app FK osim AUTH_USER_MODEL (blog je samostalan content app —
# NE FK na products/brands)
def test_post_no_cross_app_fk_except_auth_user():
    from apps.blog.models import Category, Post

    user_model = get_user_model()
    for field in Post._meta.get_fields():
        if isinstance(field, models.ForeignKey):
            allowed = (Category, user_model)
            assert field.related_model in allowed, (
                f"Post.{field.name} FK ka {field.related_model} NIJE dozvoljen — blog je "
                f"samostalan content app (samo blog.Category + AUTH_USER_MODEL; NE products/brands)."
            )


# =============================================================================
# AC1 — Post.Status TextChoices (DB-value lock IMP-3)
# =============================================================================


# AC1 / IMP-3: Status TextChoices DRAFT="draft"/PUBLISHED="published"; DB-value lock
def test_post_status_textchoices_db_values():
    from apps.blog.models import Post

    assert Post.Status.DRAFT.value == "draft", (
        f"Post.Status.DRAFT.value MORA biti 'draft', dobio {Post.Status.DRAFT.value!r}."
    )
    # DB-value lock (IMP-3): PublishedManager filtrira na literal "published".
    assert Post.Status.PUBLISHED.value == "published", (
        f"Post.Status.PUBLISHED.value MORA biti 'published' (STABILAN DB ugovor — "
        f"PublishedManager + 5.2/5.3/5.4 query-i ciljaju ovaj string; IMP-3), "
        f"dobio {Post.Status.PUBLISHED.value!r}."
    )


# AC1: status CharField sa default=DRAFT; status lookup pokriven composite indeksom
def test_post_status_field_default_draft_db_index():
    from apps.blog.models import Post

    field = Post._meta.get_field("status")
    assert isinstance(field, models.CharField), "Post.status MORA biti CharField — AC1."
    assert field.max_length >= 9, (
        f"Post.status max_length MORA pokriti 'published' (9), dobio {field.max_length}."
    )
    # PERFORMANCE (Code Review M / NOTE I4): status NEMA standalone db_index=True —
    # composite `blog_post_status_pub_idx` ima status kao leftmost field, pa B-tree
    # leftmost-prefix scan već pokriva single-column status lookup-e. Eksplicitni
    # db_index bi kreirao REDUNDANTAN indeks (mirror apps/products/models.py NOTE I4).
    assert field.db_index is False, (
        "Post.status NE SME imati standalone db_index=True — composite "
        "blog_post_status_pub_idx (status leftmost) već pokriva status lookup-e (NOTE I4)."
    )
    composite = next(
        (idx for idx in Post._meta.indexes if idx.name == "blog_post_status_pub_idx"),
        None,
    )
    assert composite is not None and composite.fields[0] == "status", (
        "Composite blog_post_status_pub_idx MORA postojati sa status kao leftmost "
        "field (pokriva leftmost-prefix scan za status lookup-e)."
    )
    assert field.default == Post.Status.DRAFT, (
        "Post.status default MORA biti Status.DRAFT (novi Post NIJE published) — AC1."
    )


# AC1: novi Post (bez eksplicitnog status-a) ima status DRAFT (NIJE published)
def test_new_post_defaults_to_draft():
    from apps.blog.models import Post

    post = Post.objects.create(title="Nacrt o navodnjavanju")
    assert post.status == Post.Status.DRAFT == "draft", (
        f"Novi Post MORA biti DRAFT po defaultu (NIJE objavljen), dobio {post.status!r}."
    )


# =============================================================================
# AC1 — Post slug auto-gen + collision + __str__ + Meta
# =============================================================================


# AC1: Post.slug auto-gen iz title kroz slugify_ascii (dijakritik → ASCII)
def test_post_slug_autogen_from_title():
    from apps.blog.models import Post

    post = Post.objects.create(title="Žetva pšenice 2026")
    assert post.slug == "zetva-psenice-2026", (
        f"Post.slug MORA auto-gen iz title kroz slugify_ascii (Ž→z, š→s), dobio {post.slug!r}."
    )


# AC1: Post.__str__ vraća title
def test_post_str_returns_title():
    from apps.blog.models import Post

    post = Post.objects.create(title="Berba kukuruza")
    assert str(post) == "Berba kukuruza", "Post.__str__ MORA vraćati title — AC1."


# AC1 / IMP-5: slug kolizija — dve objave sa istim title-om → drugi save odbijen.
# save() poziva full_clean() (mirror Product 2-2) pa validate_unique() raise-uje
# ValidationError NA Python nivou PRE DB INSERT-a; raw DB INSERT (full_clean bypass)
# bi raised IntegrityError. OBA su validan kolizija-signal — koristimo OR tuple
# (IDENTIČAN Product presedan: test_product_slug_globally_unique_raises_on_collision).
# NEMA auto-de-dup u 5-1 — YAGNI (matches Product, IMP-5).
def test_post_slug_collision_raises_on_duplicate():
    from apps.blog.models import Post

    Post.objects.create(title="Žetva")
    with pytest.raises((ValidationError, IntegrityError)):
        # Drugi „Žetva" → isti slug „zetva" → unique kolizija → ValidationError
        # (full_clean validate_unique) ILI IntegrityError (DB constraint).
        Post.objects.create(title="Žetva")


# AC1: Post.Meta.ordering == ["-published_at", "-created_at"]
def test_post_meta_ordering():
    from apps.blog.models import Post

    assert list(Post._meta.ordering) == ["-published_at", "-created_at"], (
        f"Post.Meta.ordering MORA biti ['-published_at', '-created_at'], "
        f"dobio {Post._meta.ordering}."
    )


# AC1: Post.Meta.indexes sadrži imenovan index blog_post_status_pub_idx na (status, -published_at)
def test_post_meta_index_named_status_pub():
    from apps.blog.models import Post

    matching = [
        idx
        for idx in Post._meta.indexes
        if idx.name == "blog_post_status_pub_idx"
    ]
    assert matching, (
        f"Post.Meta.indexes MORA sadržati index imenovan 'blog_post_status_pub_idx' — AC1. "
        f"Pronađeni: {[(i.name, list(i.fields)) for i in Post._meta.indexes]}."
    )
    assert list(matching[0].fields) == ["status", "-published_at"], (
        f"Index 'blog_post_status_pub_idx' MORA biti na (status, -published_at), "
        f"dobio {list(matching[0].fields)}."
    )


# AC1: Post ima objects (default Manager) + published (PublishedManager) atribute
def test_post_has_objects_and_published_managers():
    from apps.blog.managers import PublishedManager
    from apps.blog.models import Post

    assert isinstance(Post.objects, models.Manager), (
        "Post.objects MORA biti models.Manager (default) — AC1/AC3."
    )
    assert isinstance(Post.published, PublishedManager), (
        "Post.published MORA biti PublishedManager instanca — AC3."
    )


# AC1: verbose_name-ovi sa punim dijakritikom (Objava/Objave; Kategorija/Kategorije)
def test_verbose_names_full_diacritics():
    from apps.blog.models import Category, Post, Tag

    assert str(Post._meta.verbose_name) == "Objava", (
        f"Post.Meta.verbose_name MORA biti 'Objava', dobio {Post._meta.verbose_name!r}."
    )
    assert str(Post._meta.verbose_name_plural) == "Objave", (
        f"Post.Meta.verbose_name_plural MORA biti 'Objave', dobio {Post._meta.verbose_name_plural!r}."
    )
    assert str(Category._meta.verbose_name) == "Kategorija", (
        f"Category.Meta.verbose_name MORA biti 'Kategorija', dobio {Category._meta.verbose_name!r}."
    )
    # TEST_GAP-1: dopuna verbose_name pokrivenosti (Category plural + Tag oba) —
    # tihi rename bilo kog verbose_name-a se sad hvata.
    assert str(Category._meta.verbose_name_plural) == "Kategorije", (
        f"Category.Meta.verbose_name_plural MORA biti 'Kategorije', "
        f"dobio {Category._meta.verbose_name_plural!r}."
    )
    assert str(Tag._meta.verbose_name) == "Tag", (
        f"Tag.Meta.verbose_name MORA biti 'Tag', dobio {Tag._meta.verbose_name!r}."
    )
    assert str(Tag._meta.verbose_name_plural) == "Tagovi", (
        f"Tag.Meta.verbose_name_plural MORA biti 'Tagovi', "
        f"dobio {Tag._meta.verbose_name_plural!r}."
    )


# AC1: settings.AUTH_USER_MODEL je definisan (FK target preduslov — SM-D3 sanity)
def test_auth_user_model_setting_present():
    assert getattr(settings, "AUTH_USER_MODEL", None), (
        "settings.AUTH_USER_MODEL MORA biti definisan (Post.author FK target — SM-D3)."
    )
