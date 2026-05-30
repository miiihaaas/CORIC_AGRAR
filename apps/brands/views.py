"""Brand listing strana — Story 2.6 (Epic 2 Public Catalog).

Server-side rendering only; HTMX filteri su Story 2.8 scope.
Query optimizacija: prefetch_related za serije + per-series prefetch za
products + per-product prefetch za specifications.

Cross-boundary import izuzetak (vidi Decision SM-D16 + project-context.md
§ Cross-boundary import "Exception" note): BrandDetailView agregira products
grupisane po brendu. View-layer-only coupling, no model dependency.
"""

from __future__ import annotations

from django.db.models import Case, CharField, IntegerField, Prefetch, Value, When
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView

from apps.brands.models import Brand, Series
from apps.products.models import Product, ProductSpecification, ProductTestimonial


class BrandDetailView(DetailView):
    model = Brand
    context_object_name = "brand"

    def get_queryset(self):
        # KRITIČNO (SM-D20): Case/When sa Value(_(...)) MORA biti definisan
        # UNUTAR get_queryset() per-request, NE na module level — inače locale
        # za prvi request "zamrzne" labels za sve buduće requeste.
        section_order = Case(
            When(section="motor", then=Value(1)),
            When(section="transmisija", then=Value(2)),
            When(section="hidraulika", then=Value(3)),
            When(section="ostalo", then=Value(4)),
            default=Value(99),
            output_field=IntegerField(),
        )
        # str() coerces lazy gettext proxy to current-locale string AT REQUEST TIME
        # (psycopg cannot adapt __proxy__ types directly — must evaluate per-request).
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

        published_products = Product.objects.filter(is_published=True).prefetch_related(
            Prefetch("specifications", queryset=specs_qs)
        )
        series_qs = Series.objects.order_by("display_order", "name").prefetch_related(
            Prefetch("products", queryset=published_products)
        )
        return Brand.objects.prefetch_related(Prefetch("series", queryset=series_qs))

    def get_template_names(self):
        if getattr(self, "object", None) is not None and self.object.is_coming_soon:
            return ["brands/brand_coming_soon.html"]
        return ["brands/brand_detail.html"]

    def get(self, request, *args, **kwargs):
        # SM-D19: set self.object PRE template selection / context build.
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.object.is_coming_soon:
            return ctx
        ctx["testimonials"] = (
            ProductTestimonial.objects.filter(
                product__brand=self.object,
                product__is_published=True,
            )
            .select_related("product")
            .order_by("order", "-created_at")[:10]
        )
        return ctx
