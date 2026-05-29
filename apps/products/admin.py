"""Story 2.2 — stub admin registracije za svih 7 modela.

Bare `admin.site.register()` (mirror 2.1 pattern — verifikovano u apps/brands/admin.py).
modeltranslation sr/hu/en tabovi se NE renderuju ovde — pun TranslationAdmin sa
color picker, image preview, inlines, i tab UI je Story 8.6 (Product CRUD) scope.
Vidi Gotcha PR-11 za detaljan trap explanation.
"""

from django.contrib import admin

from apps.products.models import (
    Product,
    ProductBrochure,
    ProductImage,
    ProductSimilar,
    ProductSpecification,
    ProductTestimonial,
    ProductVariant,
)

admin.site.register(Product)
admin.site.register(ProductImage)
admin.site.register(ProductVariant)
admin.site.register(ProductSpecification)
admin.site.register(ProductBrochure)
admin.site.register(ProductTestimonial)
admin.site.register(ProductSimilar)
