"""Story 2.1 — modeltranslation registracija za apps.brands.

modeltranslation auto-discovery (per Decision D2) skenira sve INSTALLED_APPS
pri Django startup-u i učitava `<app>/translation.py`. Registracija ovde
generiše virtuelna polja `name_sr`, `name_hu`, `name_en`, ... koja se
materijalizuju kao stvarne DB kolone kroz `makemigrations brands`.

LANGUAGES iz config/settings/base.py (Story 1.4) DEFINIŠE suffix-e:
    [("sr", "Srpski"), ("hu", "Magyar"), ("en", "English")]
"""

from modeltranslation.translator import TranslationOptions, register

from apps.brands.models import Brand, Category, Series, Subcategory


@register(Brand)
class BrandTranslationOptions(TranslationOptions):
    fields = ("name", "description", "slogan")


@register(Series)
class SeriesTranslationOptions(TranslationOptions):
    fields = ("name", "description")


@register(Category)
class CategoryTranslationOptions(TranslationOptions):
    fields = ("name", "description")


@register(Subcategory)
class SubcategoryTranslationOptions(TranslationOptions):
    fields = ("name", "description")
