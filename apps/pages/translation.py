"""Story 3.4 — modeltranslation registracija za apps.pages.

modeltranslation auto-discovery skenira sve INSTALLED_APPS pri Django startup-u i
učitava `<app>/translation.py`. Registracija ovde generiše virtuelna polja
`slogan_sr/hu/en`, `address_sr/hu/en`, `working_hours_sr/hu/en` koja se
materijalizuju kao stvarne DB kolone kroz `makemigrations pages` (MORA postojati
PRE makemigrations da kolone uđu u 0001_initial).

Mirror apps/brands/translation.py pattern. LANGUAGES iz config/settings/base.py
(Story 1.4): [("sr", "Srpski"), ("hu", "Magyar"), ("en", "English")].
"""

from modeltranslation.translator import TranslationOptions, register

from apps.pages.models import SiteSettings


@register(SiteSettings)
class SiteSettingsTranslationOptions(TranslationOptions):
    fields = ("slogan", "address", "working_hours")
