"""AppConfig za apps.seo — SEO & Discoverability (Epic 6).

PRVA story Epic 6 (Story 6.1). NOVI app: SeoMeta model (PRVA GenericForeignKey
u projektu) + modeltranslation (meta_title/meta_description → _sr/_hu/_en) +
generic admin inline žičan na receiving admin-e + {% seo_meta %} template tag-ovi.

Mirror apps/blog/apps.py (5-1 NOVI-app scaffolding pattern). Importuje SAMO
apps.core (TimestampedModel) + Django (contenttypes) + modeltranslation +
apps.pages.SiteSettings (company_name fallback). GFK je loose — NEMA hard FK na
receiving modele (SeoMeta FK-uje SAMO ContentType).
"""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class SeoConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.seo"  # KRITIČNO — sa apps. prefiksom (Gotcha PR-1)
    verbose_name = _("SEO")
