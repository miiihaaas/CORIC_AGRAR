"""Story 6.1 — default fallback (display title + company_name) (TEA RED phase).

Pokriva AC7 (SM-D1): kad NEMA SeoMeta za objekat:
- seo_title → _display_title(name→title→str) + " | " + company_name
- seo_meta_description → perex → description → (sopstveni) slogan → display_title →
  SiteSettings.slogan → "" (CRIT-1: display_title rung PRE site-wide slogana).

⚠️ CRIT-1 LOCK: Post sa perex="" i NO SeoMeta → seo_meta_description vraća post.title
(display_title rung). Mirror test_blog_post_detail.py:410 semantike.

⚠️ {% load seo_meta %} UNUTAR test body-ja (lazy RED).

Refs:
- 6-1-...-admin.md AC7 + Task 7.6 + SM-D1 + CRIT-1
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.django_db


def _render(template_string: str, context: dict) -> str:
    from django.template import Context, Template
    from django.test import RequestFactory

    request = RequestFactory().get("/")
    return Template(template_string).render(Context({**context, "request": request}))


# AC7: Product bez SeoMeta → "<product.name> | Ćorić Agrar" (.name fallback)
def test_title_fallback_product_uses_name(product):
    from django.utils.translation import activate

    activate("sr")
    out = _render("{% load seo_meta %}{% seo_title product %}", {"product": product})
    assert product.name in out, "Fallback title MORA sadržati product.name (SM-D1)."
    assert "Ćorić Agrar" in out, "Fallback title MORA sadržati company_name (SM-D1)."
    assert "|" in out, "Fallback format MORA biti '<display> | <company>' (AC7)."


# AC7: Post bez SeoMeta → "<post.title> | Ćorić Agrar" (Post ima `title` NE `name`)
def test_title_fallback_post_uses_title(post):
    from django.utils.translation import activate

    activate("sr")
    out = _render("{% load seo_meta %}{% seo_title post %}", {"post": post})
    assert post.title in out, (
        "Fallback title za Post MORA koristiti post.title (getattr chain name→title — SM-D1)."
    )
    assert "Ćorić Agrar" in out


# AC7: company_name dolazi iz SiteSettings.load() (default „Ćorić Agrar")
def test_company_name_from_sitesettings(product):
    from apps.pages.models import SiteSettings

    settings_obj = SiteSettings.load()
    settings_obj.company_name = "Test Firma DOO"
    settings_obj.save()

    out = _render("{% load seo_meta %}{% seo_title product %}", {"product": product})
    assert "Test Firma DOO" in out, (
        "company_name MORA dolaziti iz SiteSettings.load().company_name (SM-D1)."
    )


# AC7 CRIT-1 REGRESSION-LOCK: prazan-perex Post bez SeoMeta → meta description == post.title
def test_description_fallback_empty_perex_post_returns_title(make_post):
    from django.utils.translation import activate

    activate("sr")
    post = make_post(title="Naslov bez perexa", perex="")

    out = _render(
        "{% load seo_meta %}{% seo_meta_description post %}", {"post": post}
    )
    assert "Naslov bez perexa" in out, (
        "CRIT-1: prazan-perex Post → meta description == post.title (display_title rung "
        "PRE SiteSettings.slogan; čuva test_blog_post_detail.py:410 semantiku — SM-D1)."
    )


# AC7: Post sa perex → meta description == perex (prvi rung u chain-u)
def test_description_fallback_post_uses_perex(make_post):
    from django.utils.translation import activate

    activate("sr")
    post = make_post(title="Naslov", perex="Konkretan perex tekst za opis.")
    out = _render(
        "{% load seo_meta %}{% seo_meta_description post %}", {"post": post}
    )
    assert "Konkretan perex tekst za opis." in out, (
        "Description fallback MORA koristiti post.perex kad postoji (prvi rung — AC7)."
    )


# AC7: Product description rung (Product nema perex; ima description)
def test_description_fallback_product_uses_description(product):
    from django.utils.translation import activate

    product.description = "Opis traktora za SEO meta description."
    product.save()

    activate("sr")
    out = _render(
        "{% load seo_meta %}{% seo_meta_description product %}", {"product": product}
    )
    assert "Opis traktora za SEO meta description." in out, (
        "Description fallback MORA koristiti product.description (rung — AC7)."
    )


# AC7: SeoMeta POSTOJI ali meta_title prazan (blank) → fallback se koristi
def test_blank_meta_title_falls_back_to_display(product):
    from django.utils.translation import activate

    from apps.seo.models import SeoMeta

    activate("sr")
    SeoMeta.objects.create(content_object=product, meta_title_sr="")  # prazan

    out = _render("{% load seo_meta %}{% seo_title product %}", {"product": product})
    assert product.name in out and "Ćorić Agrar" in out, (
        "Prazan meta_title NIJE override → fallback (display + company) se koristi (AC7)."
    )
