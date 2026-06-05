"""Story 6.1 — apps/seo/translation.py modeltranslation registracija (TEA RED phase).

Pokriva AC3: SeoMeta(meta_title/meta_description) registrovan u modeltranslation →
virtuelna polja `meta_title_sr/_hu/_en` + `meta_description_sr/_hu/_en` postoje na
modelu; og_image/exclude_from_sitemap/GFK polja NISU translatable; sr fallback
(MODELTRANSLATION_FALLBACK_LANGUAGES=("sr",)).

⚠️ GUARD: apps.seo importi UNUTAR funkcija (collection-safety).
TEA RED phase: SVI testovi MORAJU pasti — apps.seo NE postoji.

Refs:
- 6-1-...-admin.md AC3 + Task 7.3 + SM-D9 + Gotcha SEO1-5
- apps/blog/tests/test_translation.py (introspection precedent)
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.django_db


# AC3: SeoMeta registrovan u modeltranslation translator
def test_seometa_registered_in_translator():
    from modeltranslation.translator import translator

    from apps.seo.models import SeoMeta

    registered = set(translator.get_registered_models())
    assert SeoMeta in registered, (
        "SeoMeta MORA biti registrovan u modeltranslation "
        "(@register u apps/seo/translation.py) — AC3."
    )


# AC3: meta_title/meta_description → _sr/_hu/_en virtuelna polja postoje
def test_seometa_translation_fields_exist():
    from apps.seo.models import SeoMeta

    field_names = {f.name for f in SeoMeta._meta.get_fields()}
    expected = {
        f"{base}_{lang}"
        for base in ("meta_title", "meta_description")
        for lang in ("sr", "hu", "en")
    }
    missing = expected - field_names
    assert not missing, (
        f"SeoMeta modeltranslation polja nedostaju: {missing}. "
        f"@register(SeoMeta) fields=('meta_title','meta_description') — AC3."
    )


# AC3: og_image / exclude_from_sitemap / GFK polja NISU translatable (jezik-neutralni)
def test_non_translatable_fields_have_no_locale_variants():
    from apps.seo.models import SeoMeta

    field_names = {f.name for f in SeoMeta._meta.get_fields()}
    for base in ("og_image", "exclude_from_sitemap", "content_type", "object_id"):
        variants = {n for n in field_names if n.startswith(f"{base}_") and n[-3:] in ("_sr", "_hu", "_en")}
        assert variants == set(), (
            f"{base} NE SME biti translatable (jezik-neutralan — AC3), pronađeno: {variants}."
        )


# AC3: sr fallback — prazna hu varijanta meta_title pada nazad na sr
def test_sr_fallback_when_active_lang_empty(product):
    from django.utils import translation as django_translation

    from apps.seo.models import SeoMeta

    seo = SeoMeta.objects.create(content_object=product)
    seo.meta_title_sr = "SEO naslov srpski"
    seo.meta_title_hu = ""
    seo.save()

    with django_translation.override("hu"):
        seo.refresh_from_db()
        assert seo.meta_title == "SEO naslov srpski", (
            "Base accessor sa active hu + prazan meta_title_hu MORA fallback-ovati na "
            "meta_title_sr (MODELTRANSLATION_FALLBACK_LANGUAGES=('sr',)) — AC3."
        )
