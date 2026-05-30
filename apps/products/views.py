"""Product views — Story 2.7 ProductDetailView + Story 2.8 TractorListView.

Story 2.7 — server-side product detail rendering (ProductDetailView).
Story 2.8 — Tractor listing strana sa HTMX filterima (TractorListView).

Query optimizacija (SM-D21/D28): TAČNO 7 SQL upita za pun render kada manual
ProductSimilar override postoji (auto fallback je 8 queries).
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

from django.core.exceptions import SuspiciousFileOperation
from django.db.models import Case, CharField, IntegerField, Prefetch, Value, When
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.decorators.vary import vary_on_headers
from django.views.generic import DetailView, ListView

from apps.brands.models import Brand
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
_PRODUCTS_PER_PAGE = 24  # Story 2.8 SM-D8


def _parse_int(raw, *, min_value=0, max_value=10_000):
    """Story 2.8 SM-D11 defensive parser — vraća None za invalid/out-of-range input."""
    if raw is None:
        return None
    try:
        value = int(raw)
    except (ValueError, TypeError):
        return None
    if value < min_value or value > max_value:
        return None
    return value


def _parse_decimal(raw, *, min_value=Decimal("0"), max_value=Decimal("10000000")):
    """Story 2.8 SM-D11 defensive parser — vraća None za invalid/out-of-range input."""
    if raw is None:
        return None
    try:
        value = Decimal(raw)
    except (InvalidOperation, ValueError, TypeError):
        return None
    if value < min_value or value > max_value:
        return None
    return value


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


@method_decorator(vary_on_headers("HX-Request"), name="dispatch")
class TractorListView(ListView):
    """Tractor listing strana sa HTMX filterima — Story 2.8.

    PRVA HTMX story u Epic 2. Single-view sa get_template_names() branching
    (SM-D3): full page render za non-HTMX request; partial render za HTMX request
    (request.htmx == True kroz django-htmx middleware).

    Query budget: ≤ 5 SQL upita (Brand list + Product count + Product slice +
    sessions/middleware overhead). Empirijski lock-uje se u GREEN fix iter 1.

    SM-D24 (review iter 1 cache poisoning defense): @vary_on_headers("HX-Request")
    sprečava cache poisoning kada CDN/Nginx cache (Story 9.x) — isti URL vraća
    full-page response za non-HTMX i partial fragment za HTMX request; Vary header
    govori cache layer-ima da odvojeno cache-uju 2 representation-a.
    """

    model = Product
    context_object_name = "products"
    paginate_by = _PRODUCTS_PER_PAGE

    def get_template_names(self):
        if getattr(self.request, "htmx", False):
            return ["products/partials/_results_grid.html"]
        return ["products/tractor_listing.html"]

    def get_queryset(self):
        # SM-D7 traktori scope: subcategory.category.is_for == 'traktori'.
        # Product.subcategory je nullable (PR-D3) — proizvodi bez subcategory ne
        # match-uju (JOIN na NULL = no match); tractor admins MORAJU postaviti
        # subcategory za listing visibility.
        qs = (
            Product.objects.filter(
                is_published=True,
                subcategory__category__is_for="traktori",
            )
            .select_related("brand", "series", "subcategory")
            .order_by("-created_at")
        )
        snaga_min = _parse_int(self.request.GET.get("snaga_min"))
        snaga_max = _parse_int(self.request.GET.get("snaga_max"))
        cena_min = _parse_decimal(self.request.GET.get("cena_min"))
        cena_max = _parse_decimal(self.request.GET.get("cena_max"))
        if snaga_min is not None:
            qs = qs.filter(horse_power__gte=snaga_min)
        if snaga_max is not None:
            qs = qs.filter(horse_power__lte=snaga_max)
        if cena_min is not None:
            qs = qs.filter(price_eur__gte=cena_min)
        if cena_max is not None:
            qs = qs.filter(price_eur__lte=cena_max)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["brands_for_header"] = Brand.objects.filter(
            is_coming_soon=False
        ).order_by("name")
        ctx["active_filters"] = {
            "snaga_min": self.request.GET.get("snaga_min", ""),
            "snaga_max": self.request.GET.get("snaga_max", ""),
            "cena_min": self.request.GET.get("cena_min", ""),
            "cena_max": self.request.GET.get("cena_max", ""),
        }
        paginator = ctx.get("paginator")
        if paginator is not None:
            ctx["count"] = paginator.count
        else:
            ctx["count"] = self.get_queryset().count()
        return ctx
