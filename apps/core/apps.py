"""AppConfig za apps.core — prvi Django app u projektu.

Sadrži shared base klase, middleware-e, mixins i utilities koje koriste svi
ostali domain app-ovi (brands, products, catalog, forms, blog, itd.).
"""

from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"
    verbose_name = "Core"
