"""AppConfig za apps.brands — Brand, Series, Category, Subcategory taksonomija.

Domain app uveden u Story 2.1 (Epic 2). Prvi konzument django-modeltranslation
paketa u projektu (Decision D2 — modeltranslation auto-discovery skenira
sve INSTALLED_APPS na startup-u i učitava `<app>/translation.py`).
"""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class BrandsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.brands"
    verbose_name = _("Brendovi")
