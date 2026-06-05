"""Story 5.2 — URL wiring + placeholder DetailView (AC6) — TEA RED phase.

Pokriva AC6 (SM-D11):
  - apps/blog/urls.py: app_name="blog"
  - reverse("blog:index") → /sr/blog/
  - reverse("blog:detail", slug="x") → /sr/blog/x/ (RESOLVES — NE NoReverseMatch)
  - Post.get_absolute_url() razrešava na /sr/blog/<slug>/
  - BlogPostDetailView placeholder: model=Post, queryset Post.published,
    context_object_name="post", template blog/post_detail.html
  - GET /sr/blog/<published-slug>/ → 200; GET /sr/blog/<draft-slug>/ → 404 (Post.published)

NAPOMENA: inherited-test update test_get_absolute_url.py je u Task 8.0 (zaseban fajl),
NE dupliran ovde.

⚠️ GUARD: apps.blog importi UNUTAR funkcija. REUSE conftest make_post.

Refs:
- 5-2-...-filter.md AC6 + Task 8.7 + SM-D11 + Gotcha BL2-4
"""

from __future__ import annotations

import pytest
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import activate, override

pytestmark = pytest.mark.django_db


# AC6: app_name="blog" + reverse("blog:index") → /sr/blog/
def test_reverse_blog_index():
    with override("sr"):
        assert reverse("blog:index") == "/sr/blog/", (
            "reverse('blog:index') MORA biti /sr/blog/ (app_name='blog', i18n_patterns)."
        )


# AC6: reverse("blog:detail", slug=...) → /sr/blog/x/ (RESOLVES — NE NoReverseMatch)
def test_reverse_blog_detail():
    with override("sr"):
        assert reverse("blog:detail", kwargs={"slug": "x"}) == "/sr/blog/x/", (
            "reverse('blog:detail', slug='x') MORA biti /sr/blog/x/ (registrovan u 5-2)."
        )


# AC6 / SM-D11: Post.get_absolute_url() razrešava (NE NoReverseMatch)
def test_post_get_absolute_url_resolves(make_post):
    with override("sr"):
        post = make_post(title="Žetva pšenice 2026")
        assert post.get_absolute_url() == f"/sr/blog/{post.slug}/", (
            "Post.get_absolute_url() MORA razrešavati na /sr/blog/<slug>/ "
            "(blog:detail registrovan — SM-D11)."
        )


# AC6 / SM-D11: GET /sr/blog/<published-slug>/ → 200 (placeholder detail)
def test_detail_published_post_200(client, make_post):
    activate("sr")
    post = make_post(
        title="Objavljena priča",
        status="published",
        published_at=timezone.now() - timezone.timedelta(days=1),
    )

    response = client.get(f"/sr/blog/{post.slug}/", HTTP_HOST="localhost")

    assert response.status_code == 200, (
        f"GET /sr/blog/{post.slug}/ (published) MORA biti 200 (placeholder detail)."
    )
    templates = {t.name for t in response.templates if t.name}
    assert "blog/post_detail.html" in templates, (
        f"Detail MORA koristiti blog/post_detail.html. Korišćeni: {templates!r}."
    )


# AC6 / SM-D11: context_object_name == "post" (5-3 ugovor)
def test_detail_context_object_name_is_post(client, make_post):
    activate("sr")
    post = make_post(
        title="Priča sa kontekstom",
        status="published",
        published_at=timezone.now() - timezone.timedelta(days=1),
    )

    response = client.get(f"/sr/blog/{post.slug}/", HTTP_HOST="localhost")

    assert response.status_code == 200
    assert response.context.get("post") is not None, (
        "BlogPostDetailView MORA postaviti context_object_name='post' (5-3 ugovor — SM-D11)."
    )
    assert response.context["post"].pk == post.pk


# AC6 / SM-D2/SM-D11: GET /sr/blog/<draft-slug>/ → 404 (Post.published queryset)
# LOAD-BEARING PAIRING (TEA-flag): co-create published post i asertuj 200 u ISTOM
# testu → dokazuje da je 404 zbog Post.published filtera, NE zbog neregistrovane
# rute (inače draft-404 prolazi incidentno u RED dok ruta ne postoji). Ako Dev
# wire-uje detail sa Post.objects, published-200 prolazi ALI draft-404 puca → leak
# uhvaćen.
def test_detail_draft_post_404(client, make_post):
    activate("sr")
    published = make_post(
        title="Objavljena za kontrast",
        status="published",
        published_at=timezone.now() - timezone.timedelta(days=1),
    )
    draft = make_post(title="Nacrt priča", status="draft", published_at=None)

    published_resp = client.get(
        f"/sr/blog/{published.slug}/", HTTP_HOST="localhost"
    )
    assert published_resp.status_code == 200, (
        f"KONTROLA: GET /sr/blog/{published.slug}/ (published) MORA biti 200 — "
        f"dokazuje da je ruta registrovana (404 ispod je zbog Post.published "
        f"filtera, NE neregistrovane rute). Dobili {published_resp.status_code}."
    )

    response = client.get(f"/sr/blog/{draft.slug}/", HTTP_HOST="localhost")

    assert response.status_code == 404, (
        f"GET /sr/blog/{draft.slug}/ (DRAFT) MORA biti 404 — BlogPostDetailView "
        f"queryset = Post.published (draft-not-leaked; SM-D2). Dobili {response.status_code}."
    )


# AC6: GET future-published detail → 404 (scheduled nije javno dostupan)
# LOAD-BEARING PAIRING (TEA-flag): co-create past-published post i asertuj 200 →
# dokazuje da je future-404 zbog published_at__lte=now filtera, NE neregistrovane rute.
def test_detail_future_published_404(client, make_post):
    activate("sr")
    published = make_post(
        title="Prošla za kontrast",
        status="published",
        published_at=timezone.now() - timezone.timedelta(days=1),
    )
    future = make_post(
        title="Buduća priča",
        status="published",
        published_at=timezone.now() + timezone.timedelta(days=7),
    )

    published_resp = client.get(
        f"/sr/blog/{published.slug}/", HTTP_HOST="localhost"
    )
    assert published_resp.status_code == 200, (
        f"KONTROLA: GET /sr/blog/{published.slug}/ (past-published) MORA biti 200 — "
        f"dokazuje da je ruta registrovana (404 ispod je zbog published_at__lte=now "
        f"filtera, NE neregistrovane rute). Dobili {published_resp.status_code}."
    )

    response = client.get(f"/sr/blog/{future.slug}/", HTTP_HOST="localhost")

    assert response.status_code == 404, (
        "GET future-published detail MORA biti 404 (Post.published filtrira "
        "published_at__lte=now — scheduled detail nije javno dostupan)."
    )


# AC6 / Security: ENUMERATION-SAFE — draft slug i nepostojeći slug daju ISTI 404
# (404-equivalence, NEMA existence-oracle). Trajno zaključava enumeration-safe
# svojstvo koje je Security reviewer verifikovao ad-hoc: napadač NE može razlikovati
# „postoji ali je draft" od „ne postoji" — draft slug/title se NE echo-uje u 404 body.
def test_draft_and_nonexistent_slug_both_404_no_oracle(client, make_post):
    activate("sr")
    draft = make_post(
        title="Tajni nacrt o đubrenju",
        status="draft",
        published_at=None,
    )

    draft_resp = client.get(f"/sr/blog/{draft.slug}/", HTTP_HOST="localhost")
    nonexistent_resp = client.get(
        "/sr/blog/ova-objava-ne-postoji/", HTTP_HOST="localhost"
    )

    # Oba 404 — draft i nepostojeći se NE razlikuju statusom (no existence oracle)
    assert draft_resp.status_code == 404, (
        f"DRAFT slug {draft.slug!r} MORA biti 404 (Post.published queryset; SM-D2). "
        f"Dobili {draft_resp.status_code}."
    )
    assert nonexistent_resp.status_code == 404, (
        "Nepostojeći slug MORA biti 404. "
        f"Dobili {nonexistent_resp.status_code}."
    )

    # Draft slug/title se NE echo-uje u 404 response body (no existence oracle)
    draft_body = draft_resp.content.decode("utf-8")
    assert draft.slug not in draft_body, (
        f"DRAFT slug {draft.slug!r} NE SME biti echo-ovan u 404 body "
        f"(existence-oracle leak — napadač bi razlikovao draft od nepostojećeg)."
    )
    assert draft.title not in draft_body, (
        f"DRAFT naslov {draft.title!r} NE SME biti echo-ovan u 404 body "
        f"(existence-oracle leak)."
    )
