"""Story 3.4 — AC5: modeltranslation registracija (Task 9.4) — RED phase (TEA).

Verifikuje da `apps/pages/translation.py` registruje slogan/address/working_hours kao
translatable → model dobija virtuelna polja `_sr/_hu/_en`; plain polja NISU translatable.

Test pattern: introspection na Model._meta polja (mirror apps/brands/tests/test_translation.py).

RED razlog: apps.pages.models.SiteSettings ne postoji → ImportError; čak i kad model nastane
ali translation.py NE postoji, `_sr/hu/en` polja nedostaju → assertion fail.

Dev NE piše testove. Pokrenuti:
    just test apps/pages/tests/test_sitesettings_translation.py -v
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.django_db


def _get_model():
    from apps.pages.models import SiteSettings

    return SiteSettings


def test_translatable_fields_have_locale_variants():
    """AC5: slogan/address/working_hours imaju _sr/_hu/_en posle modeltranslation registracije."""
    SiteSettings = _get_model()
    field_names = {f.name for f in SiteSettings._meta.get_fields()}

    expected = {
        "slogan_sr", "slogan_hu", "slogan_en",
        "address_sr", "address_hu", "address_en",
        "working_hours_sr", "working_hours_hu", "working_hours_en",
    }
    missing = expected - field_names
    assert not missing, (
        f"SiteSettings modeltranslation polja nedostaju: {missing}. Verifikuj da "
        f"apps/pages/translation.py registruje SiteSettings sa "
        f"fields=('slogan','address','working_hours') i da je modeltranslation u "
        f"INSTALLED_APPS PRE django.contrib.admin (AC5/SM-D6)."
    )


def test_plain_fields_are_not_translatable():
    """AC5: plain polja (phone_*/email/social_*/company_name) NEMAJU _sr/hu/en varijante."""
    SiteSettings = _get_model()
    field_names = {f.name for f in SiteSettings._meta.get_fields()}

    must_not_exist = {
        "company_name_sr", "company_name_hu", "company_name_en",
        "phone_sales_sr", "phone_service_sr", "email_sr",
        "social_facebook_sr", "social_instagram_sr",
    }
    leaked = must_not_exist & field_names
    assert not leaked, (
        f"Plain polja NE SMEJU imati translation varijante (jedna vrednost za sve "
        f"lokale; AC5), pronađeno: {leaked!r}. Samo slogan/address/working_hours su "
        f"translatable."
    )
