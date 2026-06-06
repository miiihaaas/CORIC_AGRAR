"""Story 7.1 — AC4: modeltranslation registracija title/body → _sr/_hu/_en (TEA RED).

Pokriva:
- CookiePolicy registrovan u modeltranslation translator (@register translation.py).
- title/body → virtuelna polja title_sr/_hu/_en + body_sr/_hu/_en postoje na modelu.
- effective_date/created_at/updated_at NISU translatable (jezik-neutralni).
- set title_hu + read pod hu → vraća hu; prazan hu → sr fallback
  (MODELTRANSLATION_FALLBACK_LANGUAGES=("sr",) base.py:157).

⚠️ COLLECTION-SAFETY: apps.gdpr importi UNUTAR funkcija (apps.gdpr NE postoji → RED).

Refs:
- 7-1-...-admin.md AC4 + SM-D8
- apps/seo/tests/test_seometa_translation.py (mirror)
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.django_db


# AC4: CookiePolicy registrovan u modeltranslation translator
def test_cookiepolicy_registered_in_translator():
    from modeltranslation.translator import translator

    from apps.gdpr.models import CookiePolicy

    registered = set(translator.get_registered_models())
    assert CookiePolicy in registered, (
        "CookiePolicy MORA biti registrovan u modeltranslation (@register u "
        "apps/gdpr/translation.py, fields=('title','body')) — AC4/SM-D8."
    )


# AC4: title/body → _sr/_hu/_en virtuelna polja postoje
def test_translation_fields_exist():
    from apps.gdpr.models import CookiePolicy

    field_names = {f.name for f in CookiePolicy._meta.get_fields()}
    expected = {
        f"{base}_{lang}"
        for base in ("title", "body")
        for lang in ("sr", "hu", "en")
    }
    missing = expected - field_names
    assert not missing, (
        f"CookiePolicy modeltranslation polja nedostaju: {missing}. "
        f"@register(CookiePolicy) fields=('title','body') — AC4."
    )


# AC4: effective_date/timestamp-ovi NISU translatable (jezik-neutralni)
def test_non_translatable_fields_have_no_locale_variants():
    from apps.gdpr.models import CookiePolicy

    field_names = {f.name for f in CookiePolicy._meta.get_fields()}
    for base in ("effective_date", "created_at", "updated_at"):
        variants = {
            n
            for n in field_names
            if n.startswith(f"{base}_") and n[-3:] in ("_sr", "_hu", "_en")
        }
        assert variants == set(), (
            f"{base} NE SME biti translatable (jezik-neutralan — AC4), pronađeno: {variants}."
        )


# AC4: set title_hu + read pod hu → vraća hu vrednost
def test_active_lang_returns_own_value():
    from django.utils import translation as django_translation

    from apps.gdpr.models import CookiePolicy

    obj = CookiePolicy.load()
    obj.title_sr = "Politika kolačića"
    obj.title_hu = "Süti szabályzat"
    obj.save()

    with django_translation.override("hu"):
        obj.refresh_from_db()
        assert obj.title == "Süti szabályzat", (
            "Base accessor sa active hu + popunjen title_hu MORA vratiti hu vrednost — AC4."
        )


# AC4: prazan title_hu → sr fallback (MODELTRANSLATION_FALLBACK_LANGUAGES=("sr",))
def test_sr_fallback_when_active_lang_empty():
    from django.utils import translation as django_translation

    from apps.gdpr.models import CookiePolicy

    obj = CookiePolicy.load()
    obj.title_sr = "Politika kolačića"
    obj.title_hu = ""
    obj.body_sr = "Srpski tekst politike kolačića."
    obj.body_hu = ""
    obj.save()

    with django_translation.override("hu"):
        obj.refresh_from_db()
        assert obj.title == "Politika kolačića", (
            "active hu + prazan title_hu MORA fallback-ovati na title_sr "
            "(MODELTRANSLATION_FALLBACK_LANGUAGES=('sr',)) — AC4."
        )
        assert obj.body == "Srpski tekst politike kolačića.", (
            "active hu + prazan body_hu MORA fallback-ovati na body_sr — AC4."
        )
