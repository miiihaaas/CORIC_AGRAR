"""Story 6.1 — TEA RED phase conftest za apps/seo/ test suite.

PRVA story Epic 6 (SEO & Discoverability). GENERIC-META FOUNDATION: NOVI app
apps/seo/ sa JEDNIM modelom (`SeoMeta`) + PRVA `GenericForeignKey` u projektu +
modeltranslation (meta_title/meta_description → `_sr/_hu/_en`) + generic admin
inline žičan na 5 postojećih admin-a + `{% seo_meta %}` template tag-ovi sa
fallback-om.

RED phase: apps.seo NE postoji (NIJE u INSTALLED_APPS) → svaki test koji importuje
`apps.seo.*` MORA pasti čisto. ⚠️ apps.seo NEMA module-level import nijednog test
modula (collection-safety) — importi su UNUTAR test funkcija/fixtura. Tako missing
apps.seo daje per-test FAIL (RED), NE collection-abort koji bi oborio CELU suite.

Receiving instance (Product/Brand/Post) za GFK su realni — kreiraju se kroz
postojeće factory-je (apps.products / apps.brands) ili inline create (apps.blog).
Superuser kroz `django_user_model` (NIKAD direktan User import — project-context.md:595).

Refs:
- 6-1-seometa-model-per-page-admin.md Task 7 + AC1-AC9 + SM-D1..D9 + Gotcha SEO1-1..7
- 6-1-interface-contract.md (TEA canonical contract — Dev MORA satisfy)
- apps/blog/tests/conftest.py + apps/products/tests/factories.py (style precedent)
"""

from __future__ import annotations

import pytest


# ── Media isolation (og_image ImageField — file-stub uploads ne curi) ─────────


@pytest.fixture(autouse=True)
def _isolate_media_root(settings, tmp_path):
    """Per-test MEDIA_ROOT izolacija (established project pattern — products/blog)."""
    settings.MEDIA_ROOT = str(tmp_path)


# ── Superuser za admin smoke (AC5/AC8) ────────────────────────────────────────


@pytest.fixture
def superuser(django_user_model):
    """Superuser za admin changelist/add-view smoke (AC5/AC8).

    `django_user_model` = settings.AUTH_USER_MODEL kroz get_user_model() —
    NIKAD direktan `from django.contrib.auth.models import User`.
    """
    return django_user_model.objects.create_superuser(
        username="seo_admin_tea",
        email="seo-admin@example.com",
        password="tea-pass-12345",
    )


# ── Receiving objekti (GFK target) — realni Product / Brand / Post ────────────


@pytest.fixture
def product():
    """Realni Product (ima `.name` + get_absolute_url) — GFK target + .name fallback."""
    from apps.products.tests.factories import ProductFactory

    return ProductFactory.create(name="Traktor Ćorić 5000")


@pytest.fixture
def brand():
    """Realni Brand (ima `.name` + `.slogan` + get_absolute_url) — GFK target."""
    from apps.brands.tests.factories import BrandFactory

    return BrandFactory.create(name="Đuro Đaković")


@pytest.fixture
def make_post():
    """Helper: kreira blog Post (ima `.title` NE `.name` + `.perex` + get_absolute_url).

    Mirror apps/blog/tests/conftest.py make_post. Default DRAFT; override
    status/published_at per-test. Pune dijakritike default.
    """

    def _make(*, tags=None, **overrides):
        from apps.blog.models import Post

        defaults = {
            "title": "Žetva pšenice na vreme",
            "perex": "Kratak uvod u žetvu pšenice.",
            "body": "Detaljan tekst o žetvi na đubrenom polju.",
        }
        defaults.update(overrides)
        post = Post.objects.create(**defaults)
        if tags:
            post.tags.set(tags)
        return post

    return _make


@pytest.fixture
def post(make_post):
    """Realni published Post za GFK / fallback testove."""
    from django.utils import timezone

    return make_post(
        title="Žetva pšenice na vreme",
        status="published",
        published_at=timezone.now(),
    )


# ── PNG stub za og_image ImageField ───────────────────────────────────────────


@pytest.fixture
def png_upload():
    """SimpleUploadedFile sa Pillow-generated 1×1 PNG (validan za ImageField)."""

    def _make(name="og_test.png"):
        from io import BytesIO

        from django.core.files.uploadedfile import SimpleUploadedFile
        from PIL import Image

        buf = BytesIO()
        Image.new("RGB", (1, 1), color="blue").save(buf, format="PNG")
        return SimpleUploadedFile(name, buf.getvalue(), content_type="image/png")

    return _make
