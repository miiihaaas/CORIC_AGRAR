"""Product detail view — Story 2.7 (Epic 2 Public Catalog).

Server-side rendering only; HTMX filteri su Story 2.8 scope. Replaces Story 2.6
`placeholder_view` FBV stub.

Query optimizacija (SM-D21/D28): TAČNO 7 SQL upita za pun render kada manual
ProductSimilar override postoji (auto fallback je 8 queries).
"""

from __future__ import annotations

from django.core.exceptions import SuspiciousFileOperation
from django.db.models import Case, CharField, IntegerField, Prefetch, Value, When
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView

from apps.products.models import (
    Product,
    ProductBrochure,
    ProductImage,
    ProductSimilar,
    ProductSpecification,
    ProductTestimonial,
    ProductVariant,
)

_SIMILAR_PRODUCTS_LIMIT = 4
_BROCHURES_LIMIT = 5


class ProductDetailView(DetailView):
    model = Product
    context_object_name = "product"
    template_name = "products/product_detail.html"

    def get_queryset(self):
        # SM-D14/D20: Case/When sa Value(str(_(...))) MORA biti definisan UNUTAR
        # get_queryset() per-request — module-level konstanta zamrzla bi locale za
        # prvi request. str() coerces lazy gettext proxy → string AT REQUEST TIME
        # (psycopg ne može adapt __proxy__ tip-ove).
        section_order = Case(
            When(section="motor", then=Value(1)),
            When(section="transmisija", then=Value(2)),
            When(section="hidraulika", then=Value(3)),
            When(section="ostalo", then=Value(4)),
            default=Value(99),
            output_field=IntegerField(),
        )
        section_label = Case(
            When(section="motor", then=Value(str(_("Motor")))),
            When(section="transmisija", then=Value(str(_("Transmisija")))),
            When(section="hidraulika", then=Value(str(_("Hidraulika")))),
            When(section="ostalo", then=Value(str(_("Ostalo")))),
            default=Value(str(_("Ostalo"))),
            output_field=CharField(),
        )
        specs_qs = ProductSpecification.objects.annotate(
            section_rank=section_order,
            section_label=section_label,
        ).order_by("section_rank", "order", "id")

        return (
            Product.objects.filter(is_published=True)
            .select_related("brand", "series", "subcategory")
            .prefetch_related(
                Prefetch(
                    "images",
                    queryset=ProductImage.objects.order_by("order", "id"),
                ),
                Prefetch(
                    "variants",
                    queryset=ProductVariant.objects.order_by("order", "id"),
                ),
                Prefetch("specifications", queryset=specs_qs),
                Prefetch(
                    "brochures",
                    queryset=ProductBrochure.objects.order_by("id"),
                ),
                Prefetch(
                    "testimonials",
                    queryset=ProductTestimonial.objects.order_by("order", "-created_at"),
                ),
            )
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        product = self.object

        manual_qs = (
            ProductSimilar.objects.filter(
                product=product,
                related_product__is_published=True,
            )
            .select_related("related_product__brand")
            .order_by("order", "id")[:_SIMILAR_PRODUCTS_LIMIT]
        )
        manual_list = [entry.related_product for entry in manual_qs]

        if manual_list:
            ctx["similar_products"] = manual_list
            ctx["similar_source"] = "manual"
        else:
            auto_list = list(
                Product.objects.filter(brand=product.brand, is_published=True)
                .exclude(pk=product.pk)
                .select_related("brand")
                .order_by("-created_at")[:_SIMILAR_PRODUCTS_LIMIT]
            )
            if auto_list:
                ctx["similar_products"] = auto_list
                ctx["similar_source"] = "auto"
            else:
                ctx["similar_products"] = []
                ctx["similar_source"] = "none"

        brochures_list = []
        for brochure in list(product.brochures.all())[:_BROCHURES_LIMIT]:
            try:
                size_bytes = brochure.pdf_file.size
            except (FileNotFoundError, OSError, ValueError, SuspiciousFileOperation):
                size_bytes = 0
            brochures_list.append({"brochure": brochure, "size_bytes": size_bytes})
        ctx["brochures_list"] = brochures_list

        ctx["hero_variant"] = (
            "blue" if (product.brand.brand_color or "").lower() == "#00a4e9" else "green"
        )
        ctx["hero_brand_logo_url"] = product.brand.logo.url if product.brand.logo else ""

        return ctx
