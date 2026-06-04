"""Story 5.1 — TEA RED phase conftest za apps/blog/ test suite.

PRVA story Epic 5 (Blog „Priče sa polja"). MODEL FOUNDATION: NOVI app apps/blog/
sa 3 modela (Category/Tag/Post) + modeltranslation + PublishedManager + admin stub
+ schema migracija. NEMA views/urls/templates u 5-1 (5-2…5-4 scope).

RED phase: apps.blog NE postoji (NIJE u INSTALLED_APPS) → svaki test koji importuje
`apps.blog.*` MORA pasti čisto (ModuleNotFoundError / ImportError / assertion).

⚠️ GUARD IMPORTS (collection-safety): NIJEDAN test modul NE importuje apps.blog na
module-top-level — importi su UNUTAR test funkcija/fixtura. Tako missing apps.blog
daje per-test FAIL (RED), NE collection abort koji bi oborio CELU suite (ostali
app-ovi moraju ostati zeleni).

Test data inline kroz `*.objects.create(...)` (factory helpers ispod) — factory_boy
NIJE blog dep (mirror 4-1). PUNE srpske dijakritike (č/ć/ž/š/đ) u test podacima
(project-context anti-šišana-latinica).

Refs:
- 5-1-blogpost-category-tag-modeli-admin-stub.md Task 8 + AC1-AC6
- 5-1-interface-contract.md (TEA canonical contract — Dev MORA satisfy)
- apps/forms/tests/conftest.py + apps/products/tests/test_models.py (style precedent)
"""

from __future__ import annotations

import pytest


# ── Media isolation (Post.main_image ImageField — file-stub uploads ne curi) ──


@pytest.fixture(autouse=True)
def _isolate_media_root(settings, tmp_path):
    """Per-test MEDIA_ROOT izolacija (established project pattern — products/forms)."""
    settings.MEDIA_ROOT = str(tmp_path)


# ── Superuser za admin smoke (AC6) ────────────────────────────────────────────


@pytest.fixture
def superuser(django_user_model):
    """Superuser za admin changelist smoke testove (AC6).

    `django_user_model` = settings.AUTH_USER_MODEL kroz get_user_model() —
    NIKAD direktan `from django.contrib.auth.models import User` (project-context.md:595).
    """
    return django_user_model.objects.create_superuser(
        username="blog_admin_tea",
        email="blog-admin@example.com",
        password="tea-pass-12345",
    )


@pytest.fixture
def author_user(django_user_model):
    """Običan korisnik koji služi kao Post.author (FK → settings.AUTH_USER_MODEL)."""
    return django_user_model.objects.create_user(
        username="urednik_djordje",
        email="djordje@example.com",
        password="tea-pass-12345",
    )


# ── Factory helpers (Category / Tag / Post) — inline, pune dijakritike ────────


@pytest.fixture
def make_category():
    """Helper: kreira Category (slug auto-gen iz name). Pune dijakritike default.

    Default name „Ratarstvo"; override kroz `make_category(name="Žetva i Đubrenje")`.
    """

    def _make(**overrides):
        from apps.blog.models import Category

        defaults = {"name": "Ratarstvo", "description": "Priče sa njive."}
        defaults.update(overrides)
        return Category.objects.create(**defaults)

    return _make


@pytest.fixture
def make_tag():
    """Helper: kreira Tag (slug auto-gen iz name)."""

    def _make(**overrides):
        from apps.blog.models import Tag

        defaults = {"name": "Pšenica"}
        defaults.update(overrides)
        return Tag.objects.create(**defaults)

    return _make


@pytest.fixture
def make_post():
    """Helper: kreira Post (slug auto-gen iz title). Pune dijakritike default.

    Default DRAFT + published_at=None. Override status/published_at per-test:
        make_post(status="published", published_at=timezone.now())
    `category`/`author`/`tags` opciono prosleđeni (FK/M2M).
    """

    def _make(*, tags=None, **overrides):
        from apps.blog.models import Post

        defaults = {
            "title": "Žetva pšenice 2026",
            "perex": "Kratak uvod u žetvu.",
            "body": "Detaljan tekst o žetvi pšenice na đubrenom polju.",
        }
        defaults.update(overrides)
        post = Post.objects.create(**defaults)
        if tags:
            post.tags.set(tags)
        return post

    return _make
