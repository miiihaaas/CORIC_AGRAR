"""Abstract base modeli za cross-app reuse.

Story 2.1 — uvodi `TimestampedModel` i `SluggedModel` (oboje `abstract = True`)
kao FOUNDATION za Story 2.2+ (Product, BlogPost) gde je slug globalno unique.

Brand/Series/Category/Subcategory u Story 2.1 NE nasleđuju ove mixine —
definišu polja eksplicitno (per Decision D3). Razlog: Series i Subcategory
imaju per-scope unique slug (UniqueConstraint), što je nekompatibilno
sa `SluggedModel.slug.unique=True`.
"""

from django.db import models


class TimestampedModel(models.Model):
    """Abstract model sa `created_at` + `updated_at` timestamp-ovima."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SluggedModel(models.Model):
    """Abstract model koji dodaje globally-unique `slug` polje.

    Reuse u Story 2.2+ za Product (slug globalno unique). Brand u 2.1 ne
    koristi ovaj mixin jer ima dodatno polje (logo, hero_image, itd.) i
    drugačiju Meta strukturu.
    """

    slug = models.SlugField(max_length=140, unique=True, db_index=True)

    class Meta:
        abstract = True
