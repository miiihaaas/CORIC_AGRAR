"""AppConfig za apps.pages (Story 3.1).

`pages` je top-level app KOJEM je dozvoljeno da importuje domain modele
(`brands`/`products`) READ-ONLY — agregacijski sloj za Home + statičke strane
(architecture.md: HomeView/AboutView/ContactView). NEMA modela u v1
(SiteSettings dolazi tek Story 3.4) → NEMA migracija.
"""

from django.apps import AppConfig


class PagesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.pages"
    verbose_name = "Stranice"
