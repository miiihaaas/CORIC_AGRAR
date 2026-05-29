"""AppConfig za apps.media_pipeline — image + PDF utility (cross-cutting).

Story 2.3 (Epic 2) — utility app bez modela. Konzumiran od domain app-ova
(brands, products, blog) kroz template tagove i helper-e.
Jednosmerna zavisnost: media_pipeline NE SME uvoziti apps.products / apps.brands.

Story 2.4 proširuje ovaj app sa post_save signal handler-om za ProductBrochure
(`signals.py`) i registracijom kroz `ready()` hook — Story 2.3 NEMA ready() hook.
"""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class MediaPipelineConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.media_pipeline"
    verbose_name = _("Media pipeline")
