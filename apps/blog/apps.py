"""AppConfig za apps.blog — Blog „Priče sa polja" content layer.

NOVI domain app uveden u Story 5.1 (Epic 5 — Blog). Drugi/treći konzument
django-modeltranslation paketa (posle apps.brands/apps.products). Samostalan
content app: importuje SAMO apps.core (SluggedModel/TimestampedModel/slugify_ascii)
+ Django + modeltranslation + settings.AUTH_USER_MODEL. NE importuje
products/brands/search/pages/forms (SM-D1).
"""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class BlogConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.blog"  # KRITIČNO — sa apps. prefiksom (Gotcha PR-1)
    verbose_name = _("Blog")
