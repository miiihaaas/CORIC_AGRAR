"""Story 2.1 — apps/core/models.py abstract base klase (RED phase).

Verifikuje:
- AC9: TimestampedModel ima created_at + updated_at polja
- AC9: SluggedModel ima slug polje
- AC9: Obe klase su abstract (Meta.abstract = True) — bez DB tabela

Introspection-based testovi (Model._meta.get_field) — bez DB query-ja
ali zahtevaju Django setup → @pytest.mark.django_db NIJE potreban
(introspection radi na model klasi, ne na instancama).

Pokrenuti sa:
    uv run pytest apps/core/tests/test_models.py -v

TEA RED phase: svi testovi MORAJU pasti dok Dev ne kreira apps/core/models.py.
"""

from __future__ import annotations


# =============================================================================
# TimestampedModel (AC9)
# =============================================================================


def test_timestamped_model_is_abstract():
    """TimestampedModel mora biti abstract (no DB table)."""
    from apps.core.models import TimestampedModel

    assert TimestampedModel._meta.abstract is True, (
        "TimestampedModel.Meta.abstract MORA biti True — bez toga Django generiše "
        "tabelu za base klasu što nije design intent."
    )


def test_timestamped_model_has_created_at_field():
    """TimestampedModel ima created_at = DateTimeField(auto_now_add=True)."""
    from django.db import models

    from apps.core.models import TimestampedModel

    field = TimestampedModel._meta.get_field("created_at")
    assert isinstance(field, models.DateTimeField), (
        f"created_at mora biti DateTimeField, dobijeno: {type(field).__name__}"
    )
    assert field.auto_now_add is True, "created_at mora imati auto_now_add=True"


def test_timestamped_model_has_updated_at_field():
    """TimestampedModel ima updated_at = DateTimeField(auto_now=True)."""
    from django.db import models

    from apps.core.models import TimestampedModel

    field = TimestampedModel._meta.get_field("updated_at")
    assert isinstance(field, models.DateTimeField), (
        f"updated_at mora biti DateTimeField, dobijeno: {type(field).__name__}"
    )
    assert field.auto_now is True, "updated_at mora imati auto_now=True"


# =============================================================================
# SluggedModel (AC9)
# =============================================================================


def test_sluggedmodel_is_abstract():
    """SluggedModel mora biti abstract."""
    from apps.core.models import SluggedModel

    assert SluggedModel._meta.abstract is True, (
        "SluggedModel.Meta.abstract MORA biti True."
    )


def test_sluggedmodel_has_slug_field():
    """SluggedModel ima slug = SlugField(max_length=140, unique=True, db_index=True)."""
    from django.db import models

    from apps.core.models import SluggedModel

    field = SluggedModel._meta.get_field("slug")
    assert isinstance(field, models.SlugField), (
        f"slug mora biti SlugField, dobijeno: {type(field).__name__}"
    )
    assert field.max_length == 140, (
        f"slug.max_length mora biti 140, dobijeno: {field.max_length}"
    )
    assert field.unique is True, "SluggedModel.slug mora biti unique=True (globalno)"
