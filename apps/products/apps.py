"""AppConfig za apps.products — Product i related modeli content layer.

Domain app uveden u Story 2.2 (Epic 2). Drugi konzument django-modeltranslation
paketa (posle apps.brands u Story 2.1). Jednosmerna zavisnost: products → brands.
"""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ProductsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.products"  # KRITIČNO — sa apps. prefiksom (Gotcha PR-1)
    verbose_name = _("Proizvodi")
