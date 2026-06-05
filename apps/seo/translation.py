"""Story 6.1 — modeltranslation registracija za apps.seo.

modeltranslation auto-discovery (apps.seo POSLE `modeltranslation` u
INSTALLED_APPS) skenira INSTALLED_APPS pri startup-u i učitava translation.py.
Registracija generiše virtuelna polja `meta_title_sr/_hu/_en` +
`meta_description_sr/_hu/_en` → materijalizuju se kao DB kolone kroz
`makemigrations seo` (Gotcha SEO1-5; mirror apps/blog/translation.py).

og_image / exclude_from_sitemap / GFK polja NISU translatable (jezik-neutralni).
sr fallback kroz MODELTRANSLATION_FALLBACK_LANGUAGES=("sr",) (base.py).
"""

from modeltranslation.translator import TranslationOptions, register

from apps.seo.models import SeoMeta


@register(SeoMeta)
class SeoMetaTranslationOptions(TranslationOptions):
    fields = ("meta_title", "meta_description")
