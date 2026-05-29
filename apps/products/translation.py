"""Story 2.2 — modeltranslation registracija za apps.products.

modeltranslation auto-discovery (per Story 2.1 Decision D2) skenira sve
INSTALLED_APPS pri Django startup-u i učitava `<app>/translation.py`.
Registracija ovde generiše virtuelna polja `name_sr`, `name_hu`, `name_en`, ...
koja se materijalizuju kao stvarne DB kolone kroz `makemigrations products`.

Translation scope (PR-D7): 6 entiteta / 11 polja — expansion of epics.md
4-model spec (added ProductImage.alt_text za a11y; ProductVariant.name +
ProductVariant.description za multi-locale variant rendering u Story 2.7).
ProductSimilar IZUZET — čisto relational entity, nema translatable polja.

LANGUAGES iz config/settings/base.py (Story 1.4) DEFINIŠE suffix-e:
    [("sr", "Srpski"), ("hu", "Magyar"), ("en", "English")]
"""

from modeltranslation.translator import TranslationOptions, register

from apps.products.models import (
    Product,
    ProductBrochure,
    ProductImage,
    ProductSpecification,
    ProductTestimonial,
    ProductVariant,
)


@register(Product)
class ProductTranslationOptions(TranslationOptions):
    fields = ("name", "description", "key_features")


@register(ProductImage)
class ProductImageTranslationOptions(TranslationOptions):
    fields = ("alt_text",)


@register(ProductVariant)
class ProductVariantTranslationOptions(TranslationOptions):
    fields = ("name", "description")


@register(ProductSpecification)
class ProductSpecificationTranslationOptions(TranslationOptions):
    fields = ("key", "value")


@register(ProductBrochure)
class ProductBrochureTranslationOptions(TranslationOptions):
    fields = ("title",)


@register(ProductTestimonial)
class ProductTestimonialTranslationOptions(TranslationOptions):
    fields = ("quote", "location")
