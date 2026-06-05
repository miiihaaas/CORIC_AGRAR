"""Story 2.1 — stub admin registracije za sva 4 modela.

Pun admin sa color picker (brand_color), hero image preview, statistics
inline editor, tree widget za Subcategory hierarchy stiže u Story 8.4/8.5.

Story 6.1 — SVA 4 modela (Brand/Series/Category/Subcategory) konvertovana iz
bare-register u ModelAdmin (SeoWarningAdminMixin + SeoMetaInline) za per-page SEO
meta unos. Category UKLJUČEN (C-F locked — ima get_absolute_url + name; fajl NE
ostaje polu-konvertovan). Konverzija je ČISTO ADITIVNA (changelist nepromenjen,
samo +inline).
"""

from django.contrib import admin

from apps.brands.models import Brand, Category, Series, Subcategory
from apps.seo.admin import SeoMetaInline, SeoWarningAdminMixin


@admin.register(Brand)
class BrandAdmin(SeoWarningAdminMixin, admin.ModelAdmin):
    inlines = [SeoMetaInline]


@admin.register(Series)
class SeriesAdmin(SeoWarningAdminMixin, admin.ModelAdmin):
    inlines = [SeoMetaInline]


@admin.register(Category)
class CategoryAdmin(SeoWarningAdminMixin, admin.ModelAdmin):
    inlines = [SeoMetaInline]


@admin.register(Subcategory)
class SubcategoryAdmin(SeoWarningAdminMixin, admin.ModelAdmin):
    inlines = [SeoMetaInline]
