"""Story 2.1 — apps/brands/translation.py modeltranslation registracija (RED phase).

Pokriva AC6 — modeltranslation auto-discovery generiše _sr/_hu/_en suffix polja.

Test pattern: introspection na Model._meta.get_field("name_sr") — ako field
postoji, modeltranslation je uspešno registrovan i migracija je apply-ovana.

Pokrenuti sa:
    uv run pytest apps/brands/tests/test_translation.py -v

TEA RED phase: testovi MORAJU pasti dok Dev ne kreira translation.py + migraciju.
"""

from __future__ import annotations

import pytest

# Translation testovi se oslanjaju na Django setup (model registry); DB nije
# striktno potreban ali pytest-django ga automatski wrap-uje. Koristimo
# django_db mark zbog konzistencije sa drugim brands testovima.
pytestmark = pytest.mark.django_db


# =============================================================================
# AC6 — Brand translation fields
# =============================================================================


def test_brand_has_translation_fields_after_modeltranslation_registration():
    """Brand mora imati name_sr, name_hu, name_en, description_sr, slogan_sr posle modeltranslation registracije."""
    from apps.brands.models import Brand

    field_names = {f.name for f in Brand._meta.get_fields()}

    expected_translation_fields = {
        "name_sr",
        "name_hu",
        "name_en",
        "description_sr",
        "description_hu",
        "description_en",
        "slogan_sr",
        "slogan_hu",
        "slogan_en",
    }

    missing = expected_translation_fields - field_names
    assert not missing, (
        f"Brand modeltranslation polja nedostaju: {missing}. "
        f"Verifikuj da je modeltranslation u INSTALLED_APPS PRE apps.brands "
        f"i da apps/brands/translation.py registruje Brand."
    )


# =============================================================================
# AC6 — Series translation fields
# =============================================================================


def test_series_has_translation_fields():
    """Series mora imati name_sr/hu/en i description_sr/hu/en."""
    from apps.brands.models import Series

    field_names = {f.name for f in Series._meta.get_fields()}
    expected = {
        "name_sr", "name_hu", "name_en",
        "description_sr", "description_hu", "description_en",
    }
    missing = expected - field_names
    assert not missing, f"Series modeltranslation polja nedostaju: {missing}"


# =============================================================================
# AC6 — Category translation fields
# =============================================================================


def test_category_has_translation_fields():
    """Category mora imati name_sr/hu/en i description_sr/hu/en."""
    from apps.brands.models import Category

    field_names = {f.name for f in Category._meta.get_fields()}
    expected = {
        "name_sr", "name_hu", "name_en",
        "description_sr", "description_hu", "description_en",
    }
    missing = expected - field_names
    assert not missing, f"Category modeltranslation polja nedostaju: {missing}"


# =============================================================================
# AC6 — Subcategory translation fields
# =============================================================================


def test_subcategory_has_translation_fields():
    """Subcategory mora imati name_sr/hu/en i description_sr/hu/en."""
    from apps.brands.models import Subcategory

    field_names = {f.name for f in Subcategory._meta.get_fields()}
    expected = {
        "name_sr", "name_hu", "name_en",
        "description_sr", "description_hu", "description_en",
    }
    missing = expected - field_names
    assert not missing, f"Subcategory modeltranslation polja nedostaju: {missing}"
