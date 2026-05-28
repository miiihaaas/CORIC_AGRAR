"""Per-app `translation.py` — SOT za django-modeltranslation `TranslationOptions`.

Ovaj fajl je centralno mesto gde svaki app registruje koji su mu modeli i polja
prevodiva. django-modeltranslation auto-generiše `_sr`, `_hu`, `_en` suffix kolone
pri sledećoj `makemigrations` (videti `apps/brands/translation.py` u Story 2.1+).

apps.core trenutno nema modele — ovaj fajl je placeholder + dokumentovan primer
za naredne story-je koji uvode content modele sa translatable poljima.
"""

# Primer (Story 2.1+ će koristiti ovaj pattern u apps/brands/translation.py):
#
# from modeltranslation.translator import TranslationOptions, register
# from apps.brands.models import Brand
#
# @register(Brand)
# class BrandTranslationOptions(TranslationOptions):
#     # Story 2.1 Brand model — primer; concrete fields zavise od modela.
#     fields = ("name", "description")
#
# Sa ovom registracijom, posle `makemigrations brands` Brand model dobija polja:
# name_sr, name_hu, name_en, description_sr, description_hu, description_en.
# Django admin automatski rendera tabove po jeziku. Šabloni pristupaju kroz
# {{ brand.name }} (model uzima vrednost iz aktivne lokale automatski).
