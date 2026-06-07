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

from apps.pages.models import Page, SiteSettings


@register(SiteSettings)
class SiteSettingsTranslationOptions(TranslationOptions):
    fields = ("slogan", "address", "working_hours")


@register(Page)
class PageTranslationOptions(TranslationOptions):
    # Story 7.4 — title/body → title_sr/hu/en, body_sr/hu/en (kolone u 0003).
    # slug/created_at/updated_at NISU translatable (jezik-neutralni).
    fields = ("title", "body")
