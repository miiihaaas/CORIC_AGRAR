"""Story 2.1 — stub admin registracije za sva 4 modela.

Pun admin sa color picker (brand_color), hero image preview, statistics
inline editor, tree widget za Subcategory hierarchy stiže u Story 8.4/8.5.
"""

from django.contrib import admin

from apps.brands.models import Brand, Category, Series, Subcategory

admin.site.register(Brand)
admin.site.register(Series)
admin.site.register(Category)
admin.site.register(Subcategory)
