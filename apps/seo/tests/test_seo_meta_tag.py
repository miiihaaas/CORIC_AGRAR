"""Story 6.1 — {% seo_title %}/{% seo_meta_description %}/{% seo_head %} tagovi (TEA RED).

Pokriva AC6 (tag rendering: title/desc STRING + seo_head emituje canonical+og:image)
i AC9 (i18n: meta u aktivnoj lokali + canonical locale-prefiksovan).

⚠️ {% load seo_meta %} fail-uje pri render-u sa TemplateSyntaxError ('seo_meta' is
not a registered tag library) dok Dev ne kreira apps/seo/templatetags/seo_meta.py
= TAČAN RED razlog. {% load %} je UNUTAR test body-ja (lazy) → čist per-test FAIL,
NE collection-abort.

Render kroz RequestFactory + Context sa request (build_absolute_uri za canonical).

Refs:
- 6-1-...-admin.md AC6/AC9 + Task 7.5 + SM-D2/D7
- 6-1-interface-contract.md § templatetags/seo_meta.py
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.django_db


def _render(template_string: str, context: dict) -> str:
    """Render template string sa request u contextu (build_absolute_uri)."""
    from django.template import Context, Template
    from django.test import RequestFactory

    request = RequestFactory().get("/")
    ctx = Context({**context, "request": request})
    return Template(template_string).render(ctx)


def _render_shared_request(template_string: str, context: dict):
    """Render uz ISTI request objekat (per-request keš deli stanje kroz sve tagove).

    Vraća (output, request) — pozivalac može meriti query budget na request-u koji
    nosi per-request SeoMeta keš (A5/A6 dele isti request da dokažu po-objekat keš).
    """
    from django.template import Context, Template
    from django.test import RequestFactory

    request = RequestFactory().get("/")
    ctx = Context({**context, "request": request})
    return Template(template_string).render(ctx), request


# AC6: {% seo_title obj %} vraća SeoMeta.meta_title kad postoji (aktivni locale)
def test_seo_title_returns_seometa_value(product):
    from django.utils.translation import activate

    from apps.seo.models import SeoMeta

    activate("sr")
    SeoMeta.objects.create(content_object=product, meta_title_sr="Ručno unet SEO naslov")

    out = _render("{% load seo_meta %}{% seo_title product %}", {"product": product})
    assert "Ručno unet SEO naslov" in out, (
        "{% seo_title %} MORA vratiti SeoMeta.meta_title kad je postavljen (AC6)."
    )
    # Ručno unet naslov je KOMPLETAN — bez ' | company' suffiksa (AC7 napomena)
    assert "| Ćorić Agrar" not in out, (
        "Ručno unet meta_title NE dobija ' | company' suffiks (AC7 napomena)."
    )


# AC6: {% seo_meta_description obj %} vraća SeoMeta.meta_description kad postoji
def test_seo_meta_description_returns_seometa_value(product):
    from django.utils.translation import activate

    from apps.seo.models import SeoMeta

    activate("sr")
    SeoMeta.objects.create(
        content_object=product, meta_description_sr="Ručno unet meta opis za Google."
    )

    out = _render(
        "{% load seo_meta %}{% seo_meta_description product %}", {"product": product}
    )
    assert "Ručno unet meta opis za Google." in out, (
        "{% seo_meta_description %} MORA vratiti SeoMeta.meta_description (AC6)."
    )


# AC6: {% seo_head obj %} emituje <link rel="canonical"> (apsolutni URL)
def test_seo_head_emits_canonical(product):
    out = _render("{% load seo_meta %}{% seo_head product %}", {"product": product})
    assert 'rel="canonical"' in out, (
        "{% seo_head %} MORA emitovati <link rel=\"canonical\"> (AC6/SM-D7)."
    )
    assert "http://" in out or "https://" in out, (
        "canonical href MORA biti APSOLUTNI URL (build_absolute_uri — SM-D7)."
    )


# AC6: {% seo_head obj %} NE emituje <title> ni <meta name="description"> (SM-D2 split)
def test_seo_head_does_not_emit_title_or_description(product):
    from apps.seo.models import SeoMeta

    SeoMeta.objects.create(content_object=product, meta_title_sr="X", meta_description_sr="Y")
    out = _render("{% load seo_meta %}{% seo_head product %}", {"product": product})
    assert "<title" not in out, (
        "{% seo_head %} NE SME emitovati <title> (to je base-ov block — SM-D2 NO-DUPLICATE)."
    )
    assert 'name="description"' not in out, (
        "{% seo_head %} NE SME emitovati <meta name=\"description\"> (base-ov block — SM-D2)."
    )


# AC6: {% seo_head obj %} emituje og:image SAMO kad og_image postoji
def test_seo_head_emits_og_image_when_set(product, png_upload):
    from apps.seo.models import SeoMeta

    seo = SeoMeta.objects.create(content_object=product)
    seo.og_image = png_upload("hero.png")
    seo.save()

    out = _render("{% load seo_meta %}{% seo_head product %}", {"product": product})
    assert 'property="og:image"' in out, (
        "{% seo_head %} MORA emitovati <meta property=\"og:image\"> kad og_image postoji (AC6)."
    )


# AC6: bez og_image → NEMA og:image (regression-lock za test_blog_post_detail.py:435)
def test_seo_head_no_og_image_when_unset(product):
    out = _render("{% load seo_meta %}{% seo_head product %}", {"product": product})
    assert 'property="og:image"' not in out, (
        "Bez og_image → og:image se IZOSTAVLJA (C-E latent tripwire — AC6)."
    )


# AC6/SM-D7: objekat bez get_absolute_url → canonical se IZOSTAVLJA (graceful skip, NE 500)
def test_seo_head_skips_canonical_when_no_get_absolute_url():
    class _NoUrlObj:
        pk = 1
        name = "Objekat bez URL-a"

        def __str__(self):
            return self.name

    out = _render("{% load seo_meta %}{% seo_head obj %}", {"obj": _NoUrlObj()})
    assert 'rel="canonical"' not in out, (
        "Objekat bez get_absolute_url → canonical IZOSTAVLJEN (graceful skip — SM-D7)."
    )


# AC9: meta_title render u aktivnoj lokali (hu) — modeltranslation virtuelni atribut
def test_seo_title_renders_active_locale(product):
    from django.utils.translation import activate

    from apps.seo.models import SeoMeta

    seo = SeoMeta.objects.create(content_object=product)
    seo.meta_title_sr = "Srpski naslov"
    seo.meta_title_hu = "Magyar cím"
    seo.save()

    activate("hu")
    try:
        out = _render("{% load seo_meta %}{% seo_title product %}", {"product": product})
        assert "Magyar cím" in out, (
            "{% seo_title %} MORA vratiti meta_title u AKTIVNOJ (hu) lokali (AC9)."
        )
        assert "Srpski naslov" not in out
    finally:
        activate("sr")


# AC9: canonical je locale-prefiksovan (/hu/...) u hu kontekstu (i18n_patterns)
def test_canonical_is_locale_prefixed(post):
    from django.utils.translation import activate

    activate("hu")
    try:
        out = _render("{% load seo_meta %}{% seo_head post %}", {"post": post})
        assert "/hu/" in out, (
            "canonical MORA biti locale-prefiksovan (/hu/...) u hu kontekstu "
            "(get_absolute_url kroz i18n_patterns — AC9)."
        )
    finally:
        activate("sr")


# A5 / TEA MF-3 — per-request keš NE kolidira između objekata. Stari ključ `id(obj)`
# je memory-address baziran (GC reuse → teoretska kolizija — ARCH-1/N-1). Novi ključ
# (type-name, pk) je content-stable. Render product i post u ISTOM request-u → svaki
# dobija SVOJ keš slot (NE deli SeoMeta vrednost).
def test_per_request_cache_no_collision_between_objects(product, post):
    from django.utils.translation import activate

    from apps.seo.models import SeoMeta

    activate("sr")
    SeoMeta.objects.create(content_object=product, meta_title_sr="Product SEO")
    SeoMeta.objects.create(content_object=post, meta_title_sr="Post SEO")

    out, _request = _render_shared_request(
        "{% load seo_meta %}"
        "P[{% seo_title product %}]"
        "B[{% seo_title post %}]",
        {"product": product, "post": post},
    )

    assert "P[Product SEO]" in out, (
        "Render za product MORA vratiti 'Product SEO' (per-request keš ključ po "
        "(type,pk) — A2/MF-3)."
    )
    assert "B[Post SEO]" in out, (
        "Render za post MORA vratiti 'Post SEO' — keš NE sme vratiti product vrednost "
        "(no-collision — A2/MF-3)."
    )
    # eksplicitno: nijedan ne sme procureti u drugog
    assert "P[Post SEO]" not in out and "B[Product SEO]" not in out, (
        "Per-request keš NE SME kolidirati između product i post (ključ (type,pk), "
        "NE id(obj) — A2/MF-3)."
    )


# A6 / TEA NM-5 — dedikovani seo-tag query lock: 3 taga na 1 objektu = 1 SeoMeta query
# (deljen kroz per-request keš; ContentType je app-cached). Drugi objekat dodaje SVOJ
# bounded lookup (NE N+1). Lock-uje +2-bounded claim nezavisno od detail-page budžeta.
def test_seo_tags_query_budget_one_seometa_lookup_per_object(product, post):
    from django.db import connection
    from django.test.utils import CaptureQueriesContext
    from django.utils.translation import activate

    from apps.seo.models import SeoMeta

    activate("sr")
    SeoMeta.objects.create(
        content_object=product, meta_title_sr="P", meta_description_sr="PD"
    )

    # 3 taga (title + description + head) na ISTOM objektu → 1 SeoMeta SELECT
    # (ContentType app-cached; keš deli lookup kroz sva 3 taga; canonical
    # get_absolute_url NE query-ja).
    three_tags = (
        "{% load seo_meta %}"
        "{% seo_title o %}{% seo_meta_description o %}{% seo_head o %}"
    )
    with CaptureQueriesContext(connection) as ctx:
        _render(three_tags, {"o": product})
    assert len(ctx.captured_queries) == 1, (
        "3 SEO taga na ISTOM objektu MORAJU izvršiti TAČNO 1 SeoMeta query "
        f"(deljen per-request keš; NE 3) — dobio {len(ctx.captured_queries)}: "
        f"{[q['sql'][:60] for q in ctx.captured_queries]}."
    )

    # Drugi objekat dodaje SVOJ bounded lookup (NE N+1): 2 objekta × 1 tag = 2 query
    SeoMeta.objects.create(content_object=post, meta_title_sr="X")
    two_objects = "{% load seo_meta %}{% seo_title a %}{% seo_title b %}"
    with CaptureQueriesContext(connection) as ctx2:
        _render(two_objects, {"a": product, "b": post})
    assert len(ctx2.captured_queries) == 2, (
        "2 različita objekta MORAJU izvršiti 2 odvojena SeoMeta lookup-a (po 1, "
        f"bounded — NE N+1, NE 1 sa kolizijom) — dobio {len(ctx2.captured_queries)}."
    )
