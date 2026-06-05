"""Story 5.1 — Post.get_absolute_url (TEA RED phase) — AŽURIRAN u 5.2 (SM-D12).

Pokriva AC1 (SM-D6 / Gotcha PR-5 precedent): Post.get_absolute_url() poziva
reverse("blog:detail", kwargs={"slug": ...}). U 5-1 je raise-ovao NoReverseMatch
(blog URL-ovi NE postoje). 5.2 ažurira ovaj test (SM-D12 — 5-2 registruje
blog:detail, prvi konzument kartica) i asertuje razrešen /sr/blog/<slug>/.

⚠️ INHERITED-TEST UPDATE (Task 8.0 / Gotcha BL2-3): 5-2 registruje `blog:detail`
URL → `reverse("blog:detail", ...)` više NE raise-uje NoReverseMatch. Stara
asertacija `pytest.raises(NoReverseMatch)` PUKLA bi čim Dev registruje URL u GREEN.
Zato TEA u RED fazi prepisuje asertaciju RANO (PRE blog:detail GREEN wiring) — sad
asertuje razrešen `/sr/blog/<slug>/` put (pod activate("sr")). Ovaj test je RED
dok Dev ne wire-uje `blog:detail` (NoReverseMatch dotle); to je očekivano — test
je deo 5-2 kontrakta.

⚠️ GUARD: apps.blog importi UNUTAR funkcija (collection-safety).

Refs:
- 5-1-...-admin-stub.md AC1 + Task 8.3 + SM-D6 + Gotcha PR-5
- 5-2-blog-index-strana-...-filter.md Task 8.0 + SM-D11/SM-D12 + Gotcha BL2-3
- apps/products/models.py:278-280 (Product.get_absolute_url precedent)
"""

from __future__ import annotations

import pytest
from django.urls import reverse
from django.utils.translation import override

pytestmark = pytest.mark.django_db


# AC6 (5-2) / SM-D12: get_absolute_url razrešava na /sr/blog/<slug>/ kad blog:detail
# registrovan (5-2 OWNS update — prethodno asertovao NoReverseMatch u 5-1).
def test_get_absolute_url_resolves_blog_detail():
    from apps.blog.models import Post

    post = Post.objects.create(title="Žetva pšenice 2026")

    with override("sr"):
        # reverse("blog:detail", ...) — URL pattern registrovan u 5.2
        # (`apps/blog/urls.py` blog:detail). get_absolute_url MORA biti
        # reverse-based (NE hardkodovan string) i razrešavati locale-prefiksovan put.
        expected = f"/sr/blog/{post.slug}/"
        assert reverse("blog:detail", kwargs={"slug": post.slug}) == expected, (
            "reverse('blog:detail', slug=...) MORA razrešavati na /sr/blog/<slug>/ "
            "pod activate('sr') (i18n_patterns locale prefiks)."
        )
        assert post.get_absolute_url() == expected, (
            f"Post.get_absolute_url() MORA razrešavati na {expected!r} "
            "(reverse('blog:detail') — SM-D6/SM-D11; 5-2 registruje URL)."
        )


# AC1: get_absolute_url je definisan na Post (callable) — NE pukim atributom
def test_get_absolute_url_is_defined():
    from apps.blog.models import Post

    assert callable(getattr(Post, "get_absolute_url", None)), (
        "Post.get_absolute_url MORA biti definisan (reverse('blog:detail') — SM-D6)."
    )
