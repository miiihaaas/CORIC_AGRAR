"""Story 5.1 — STUB apps/blog/admin.py (TEA RED phase).

Pokriva AC6: Category/Tag/Post registrovani na admin.site; superuser GET changelist
za sva 3 → 200; PostAdmin.view_on_site is False (IMP-1 — sprečava „View on site" →
get_absolute_url → NoReverseMatch → 500 jer blog URL-ovi NE postoje do 5.2/5.3);
smoke NE sme triggerovati Post.get_absolute_url.

Tolerantno prema BL-2 fragilnosti (prepopulated_fields/search_fields + modeltranslation):
asertujemo da admin PROĐE manage.py check + changelist 200, NE specifičnu prepopulated
konfiguraciju (Dev bira TranslationAdmin / sr-suffiks / suženo — što prolazi check).

⛔ reverse() PRAVILO: admin pod i18n_patterns → NIKAD hardkodovan /admin/ ni /sr/admin/.

⚠️ GUARD: apps.blog importi UNUTAR funkcija (collection-safety).

TEA RED phase: SVI testovi MORAJU pasti — apps.blog NE postoji →
NoReverseMatch("admin:blog_post_changelist") / LookupError / ImportError.

Refs:
- 5-1-...-admin-stub.md AC6 + Task 8.8 + SM-D8 + Gotcha BL-2/BL-5 + IMP-1
- 5-1-interface-contract.md § 6 (admin)
- apps/forms/tests/test_lead_admin.py (admin smoke precedent)
"""

from __future__ import annotations

import pytest
from django.contrib import admin
from django.urls import reverse

pytestmark = pytest.mark.django_db


# AC6: Category/Tag/Post registrovani na admin.site
def test_blog_models_registered_in_admin():
    from apps.blog.models import Category, Post, Tag

    for model in (Post, Category, Tag):
        assert admin.site.is_registered(model), (
            f"{model.__name__} MORA biti registrovan na admin.site "
            f"(@admin.register u apps/blog/admin.py) — AC6."
        )


# 8.7 SM-D8: PostAdmin.view_on_site RE-ENABLED — 5-3 registrovao blog:detail (G-16 test-ownership)
def test_post_admin_view_on_site_false():
    from apps.blog.models import Post

    model_admin = admin.site._registry[Post]
    # 5-1 view_on_site=False (IMP-1/BL-5) je NAMERNO uklonjen u 8.7: blog:detail JE registrovan
    # (5-3), Post.get_absolute_url radi za published (draft → 404 NE 500). „View on site" je
    # korisna preview affordance za Marijanu (SM-D8/AC8).
    assert model_admin.view_on_site is not False, (
        "PostAdmin.view_on_site MORA biti RE-ENABLED (NIJE False) — 5-3 registrovao blog:detail "
        "→ „View on site“ radi (SM-D8); 5-1 view_on_site=False se NAMERNO menja u 8.7."
    )


# AC6: superuser GET Post changelist → 200 (NE hardkodovan put; smoke NE triggeruje
# get_absolute_url jer view_on_site=False)
def test_post_changelist_200_for_superuser(client, superuser, make_post, author_user):
    # Kreira jedan Post da changelist render-uje red (potvrđuje da view_on_site=False
    # sprečava get_absolute_url poziv → bez NoReverseMatch/500).
    make_post(author=author_user)
    url = reverse("admin:blog_post_changelist")
    client.force_login(superuser)
    response = client.get(url)
    assert response.status_code == 200, (
        f"superuser GET {url!r} MORA vratiti 200 (admin stub PROLAZI check + render); "
        f"dobio {response.status_code}. Ako 500 → verovatno get_absolute_url/NoReverseMatch "
        f"(view_on_site mora biti False — IMP-1)."
    )


# AC6: superuser GET Category changelist → 200
def test_category_changelist_200_for_superuser(client, superuser, make_category):
    make_category()
    url = reverse("admin:blog_category_changelist")
    client.force_login(superuser)
    response = client.get(url)
    assert response.status_code == 200, (
        f"superuser GET {url!r} MORA vratiti 200, dobio {response.status_code}."
    )


# AC6: superuser GET Tag changelist → 200
def test_tag_changelist_200_for_superuser(client, superuser, make_tag):
    make_tag()
    url = reverse("admin:blog_tag_changelist")
    client.force_login(superuser)
    response = client.get(url)
    assert response.status_code == 200, (
        f"superuser GET {url!r} MORA vratiti 200, dobio {response.status_code}."
    )


# AC6: Post add-view → 200 (potvrđuje prepopulated_fields/search_fields PROLAZE check;
# BL-2 fragilnost rešena — Dev bira TranslationAdmin/sr-suffiks/suženo)
def test_post_add_view_200_for_superuser(client, superuser):
    url = reverse("admin:blog_post_add")
    client.force_login(superuser)
    response = client.get(url)
    assert response.status_code == 200, (
        f"superuser GET {url!r} (add-view) MORA vratiti 200 — potvrđuje da admin opcije "
        f"(prepopulated_fields/search_fields sa modeltranslation; BL-2) PROLAZE render. "
        f"dobio {response.status_code}."
    )


# AC6: admin sistemska provera čista (run_checks za admin tag — BL-2 admin.E030/FieldError guard)
def test_admin_system_checks_clean():
    from django.core.checks import run_checks

    # Pokreće SVE system check-ove (uključujući admin) — admin.E030/E116/FieldError
    # bi se pojavili ovde ako su prepopulated_fields/search_fields loše konfigurisani.
    errors = [e for e in run_checks() if e.is_serious()]
    assert errors == [], (
        f"manage.py check (system checks) MORA biti čist — admin stub mora PROĆI "
        f"(BL-2: prepopulated_fields/search_fields + modeltranslation ne smeju baciti "
        f"admin.E030/FieldError). Greške: {errors}."
    )
