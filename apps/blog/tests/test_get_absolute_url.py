"""Story 5.1 — Post.get_absolute_url (TEA RED phase).

Pokriva AC1 (SM-D6 / Gotcha PR-5 precedent): Post.get_absolute_url() poziva
reverse("blog:detail", kwargs={"slug": ...}) i raise-uje NoReverseMatch u 5-1
(blog URL-ovi NE postoje do 5.2/5.3). Potvrđuje da je reverse-based, NE hardkodovan
„/blog/..." string. 5.3 ažurira ovaj test da asertuje stvarni /sr/blog/<slug>/.

⚠️ GUARD: apps.blog importi UNUTAR funkcija (collection-safety).

TEA RED phase: SVI testovi MORAJU pasti — apps.blog NE postoji.

Refs:
- 5-1-...-admin-stub.md AC1 + Task 8.3 + SM-D6 + Gotcha PR-5
- apps/products/models.py:278-280 (Product.get_absolute_url precedent)
"""

from __future__ import annotations

import pytest
from django.urls import NoReverseMatch

pytestmark = pytest.mark.django_db


# AC1 / SM-D6: get_absolute_url raise NoReverseMatch dok blog:detail ne postoji (5.2/5.3)
def test_get_absolute_url_raises_no_reverse_match():
    from apps.blog.models import Post

    post = Post.objects.create(title="Žetva pšenice 2026")
    with pytest.raises(NoReverseMatch):
        # reverse("blog:detail", ...) — URL pattern dolazi u 5.2/5.3 (Gotcha PR-5).
        # NoReverseMatch potvrđuje reverse-based ugovor (NE hardkodovan string).
        post.get_absolute_url()


# AC1: get_absolute_url je definisan na Post (callable) — NE pukim atributom
def test_get_absolute_url_is_defined():
    from apps.blog.models import Post

    assert callable(getattr(Post, "get_absolute_url", None)), (
        "Post.get_absolute_url MORA biti definisan (reverse('blog:detail') — SM-D6)."
    )
