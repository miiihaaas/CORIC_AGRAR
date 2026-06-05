"""Story 6.1 — `SeoMeta` model (PRVA GenericForeignKey u projektu).

GENERIC-META FOUNDATION: jedan model `SeoMeta(TimestampedModel)` koji nosi
per-objekat SEO meta (meta_title/meta_description translatable, og_image,
exclude_from_sitemap flag) vezan za bilo koji objekat kroz GenericForeignKey
(content_type FK→ContentType + object_id + content_object GFK).

UniqueConstraint(content_type, object_id) = jedan SeoMeta po objektu + služi
kao composite indeks za GFK forward lookup (SM-D4).

NEMA defensive `clean()` (YAGNI; soft warning je admin advisory — SM-D5).
`__str__` NE poziva content_object (izbegava dodatni query / None za obrisan
objekat — Gotcha SEO1-1).
"""

from django.contrib.contenttypes.fields import GenericForeignKey
from django.db import models
from django.db.models import UniqueConstraint
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimestampedModel


class SeoMeta(TimestampedModel):
    content_type = models.ForeignKey(
        "contenttypes.ContentType",
        on_delete=models.CASCADE,
        verbose_name=_("Tip sadržaja"),
    )
    object_id = models.PositiveIntegerField(
        db_index=True, verbose_name=_("ID objekta")
    )
    content_object = GenericForeignKey("content_type", "object_id")  # NIJE DB kolona

    meta_title = models.CharField(
        _("Meta naslov"), max_length=255, blank=True
    )  # translatable
    meta_description = models.TextField(_("Meta opis"), blank=True)  # translatable
    og_image = models.ImageField(
        _("OG slika"),
        upload_to="seo/og/",
        max_length=255,
        null=True,
        blank=True,
    )
    exclude_from_sitemap = models.BooleanField(
        _("Izostavi iz sitemap-a"), default=False, db_index=True
    )

    class Meta:
        verbose_name = _("SEO meta")
        verbose_name_plural = _("SEO meta")
        ordering = ["-updated_at"]
        constraints = [
            UniqueConstraint(
                fields=["content_type", "object_id"],
                name="seo_seometa_ct_obj_uniq",
            ),
        ]

    def __str__(self):
        return f"SeoMeta<{self.content_type} #{self.object_id}>"  # NE poziva content_object
