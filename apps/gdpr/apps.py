"""AppConfig za apps.gdpr — GDPR & Privacy content layer (Story 7.1).

PRVA story Epic 7 (GDPR & Privacy). NOVI domain-neutralan content app:
importuje SAMO apps.core (TimestampedModel) + Django (reverse/PermissionDenied/
generic views/admin) + modeltranslation. NE importuje domain app-ove
(products/brands/blog/pages/seo) — dep boundary AC5/SM-D1.
"""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class GdprConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.gdpr"  # KRITIČNO — sa apps. prefiksom (Gotcha G-1)
    verbose_name = _("GDPR i privatnost")
