"""Story 6.1 — i18n: meta lokalizacija + canonical locale-prefiks + company_name invarijant (AC9).

Pokriva AC9 (C-D ispravka):
- meta_title/meta_description render u AKTIVNOJ lokali (modeltranslation virtuelni atribut).
- canonical href je locale-prefiksovan (/hu/... na hu) kroz i18n_patterns.
- company_name NIJE locale-aware (jedan string „Ćorić Agrar" za sve lokale —
  NIJE registrovan u apps/pages/translation.py).

⚠️ {% load seo_meta %} UNUTAR test body-ja (lazy RED).

Refs:
- 6-1-...-admin.md AC9 + SM-D1 (C-D) + OQ-5
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.django_db


def _render(template_string: str, context: dict) -> str:
    from django.template import Context, Template
    from django.test import RequestFactory

    request = RequestFactory().get("/")
    return Template(template_string).render(Context({**context, "request": request}))


# AC9: meta_description render u aktivnoj lokali (hu)
def test_meta_description_renders_active_locale(product):
    from django.utils.translation import activate

    from apps.seo.models import SeoMeta

    seo = SeoMeta.objects.create(content_object=product)
    seo.meta_description_sr = "Srpski opis"
    seo.meta_description_hu = "Magyar leírás"
    seo.save()

    activate("hu")
    try:
        out = _render(
            "{% load seo_meta %}{% seo_meta_description product %}", {"product": product}
        )
        assert "Magyar leírás" in out, (
            "{% seo_meta_description %} MORA render-ovati u aktivnoj (hu) lokali (AC9)."
        )
    finally:
        activate("sr")


# AC9 C-D: company_name NIJE locale-aware (isti string u sr i hu)
def test_company_name_not_locale_aware(product):
    from django.utils.translation import activate

    from apps.pages.models import SiteSettings

    settings_obj = SiteSettings.load()
    settings_obj.company_name = "Ćorić Agrar"
    settings_obj.save()

    activate("sr")
    out_sr = _render("{% load seo_meta %}{% seo_title product %}", {"product": product})
    activate("hu")
    try:
        out_hu = _render("{% load seo_meta %}{% seo_title product %}", {"product": product})
    finally:
        activate("sr")

    assert "Ćorić Agrar" in out_sr, "sr fallback title MORA sadržati company_name."
    assert "Ćorić Agrar" in out_hu, (
        "company_name MORA biti ISTI 'Ćorić Agrar' u hu (NIJE locale-aware - C-D/OQ-5; AC9)."
    )


# AC9: canonical /sr/ u sr kontekstu (locale-prefiks kroz i18n_patterns)
def test_canonical_sr_prefix_in_sr_context(post):
    from django.utils.translation import activate

    activate("sr")
    out = _render("{% load seo_meta %}{% seo_head post %}", {"post": post})
    assert "/sr/" in out, (
        "canonical MORA biti /sr/-prefiksovan u sr kontekstu (i18n_patterns — AC9)."
    )
