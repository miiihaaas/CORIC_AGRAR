"""Story 5.1 — apps/blog/translation.py modeltranslation registracija (TEA RED phase).

Pokriva AC4: Post(title/perex/body) + Category(name/description) + Tag(name)
registrovani u modeltranslation → virtuelna polja _sr/_hu/_en postoje na modelu;
slug NIJE translatable; sr fallback (MODELTRANSLATION_FALLBACK_LANGUAGES=("sr",)).

⚠️ GUARD: apps.blog importi UNUTAR funkcija (collection-safety).

TEA RED phase: SVI testovi MORAJU pasti — apps.blog NE postoji.

Refs:
- 5-1-...-admin-stub.md AC4 + Task 8.5 + SM-D7
- 5-1-interface-contract.md § 4 (translation.py)
- apps/products/tests/test_models.py (translation introspection precedent)
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.django_db


# AC4: sva 3 modela registrovana u modeltranslation translator
def test_blog_models_registered_in_translator():
    from modeltranslation.translator import translator

    from apps.blog.models import Category, Post, Tag

    registered = set(translator.get_registered_models())
    for model in (Post, Category, Tag):
        assert model in registered, (
            f"{model.__name__} MORA biti registrovan u modeltranslation "
            f"(@register u apps/blog/translation.py) — AC4."
        )


# AC4: Post translatable polja → title/perex/body × _sr/_hu/_en
def test_post_translation_fields():
    from apps.blog.models import Post

    field_names = {f.name for f in Post._meta.get_fields()}
    expected = {
        f"{base}_{lang}"
        for base in ("title", "perex", "body")
        for lang in ("sr", "hu", "en")
    }
    missing = expected - field_names
    assert not missing, (
        f"Post modeltranslation polja nedostaju: {missing}. "
        f"@register(Post) fields=('title','perex','body') — AC4."
    )


# AC4: Category translatable polja → name/description × _sr/_hu/_en
def test_category_translation_fields():
    from apps.blog.models import Category

    field_names = {f.name for f in Category._meta.get_fields()}
    expected = {
        f"{base}_{lang}"
        for base in ("name", "description")
        for lang in ("sr", "hu", "en")
    }
    missing = expected - field_names
    assert not missing, (
        f"Category modeltranslation polja nedostaju: {missing}. "
        f"@register(Category) fields=('name','description') — AC4."
    )


# AC4: Tag translatable polja → name × _sr/_hu/_en
def test_tag_translation_fields():
    from apps.blog.models import Tag

    field_names = {f.name for f in Tag._meta.get_fields()}
    expected = {f"name_{lang}" for lang in ("sr", "hu", "en")}
    missing = expected - field_names
    assert not missing, (
        f"Tag modeltranslation polja nedostaju: {missing}. "
        f"@register(Tag) fields=('name',) — AC4."
    )


# AC4: slug NIJE translatable (jezik-neutralan ASCII; mirror products)
def test_slug_not_translatable():
    from apps.blog.models import Category, Post, Tag

    for model in (Post, Category, Tag):
        field_names = {f.name for f in model._meta.get_fields()}
        slug_translated = {n for n in field_names if n.startswith("slug_")}
        assert slug_translated == set(), (
            f"{model.__name__}.slug NE SME biti translatable (jezik-neutralan ASCII slug; "
            f"SM-D7), pronađeno: {slug_translated}."
        )


# AC4: sr fallback — prazna hu varijanta pada nazad na sr (FALLBACK_LANGUAGES=('sr',))
def test_sr_fallback_when_active_lang_empty():
    from django.utils import translation as django_translation

    from apps.blog.models import Post

    post = Post.objects.create(title="Žetva pšenice 2026")
    post.title_sr = "Žetva pšenice 2026"
    post.title_hu = ""
    post.save()

    with django_translation.override("hu"):
        post.refresh_from_db()
        assert post.title == "Žetva pšenice 2026", (
            f"Base accessor sa active hu + prazan title_hu MORA fallback-ovati na "
            f"title_sr (MODELTRANSLATION_FALLBACK_LANGUAGES=('sr',)), dobio {post.title!r}."
        )
