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
from django.http import Http404
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, TemplateView

from apps.brands.models import Brand, Category, Series, Subcategory
from apps.products.models import Product, ProductSpecification, ProductTestimonial

# Story 2.10 — Jeegee priključna mehanizacija landing strana
_JEEGEE_BRAND_SLUG = "jeegee"
_PRIKLJUCNA_CATEGORY_SLUGS = (
    "osnovna-obrada-zemljista",
    "priprema-zemljista",
    "masine-za-setvu",
)


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


class JeegeePrikljucnaView(DetailView):
    """Jeegee priključna mehanizacija landing strana — Story 2.10.

    Statička landing strana sa 3-card category showcase grid. NEMA HTMX,
    NEMA filtera, NEMA paginacije. View NE query-uje Product — samo Brand + Category.

    get_object() hardcoduje Jeegee Brand lookup (slug='jeegee') jer URL je
    statički bez slug kwarg-a (SM-D3); raise Http404 ako brand nije seed-ovan
    (SM-D7). get_template_names() koristi brand_coming_soon.html ako
    is_coming_soon=True (REUSE Story 2-6 SM-D19 pattern).
    """

    model = Brand
    context_object_name = "brand"

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()
        try:
            return queryset.get(slug=_JEEGEE_BRAND_SLUG)
        except Brand.DoesNotExist as exc:
            raise Http404(_("Jeegee brand nije konfigurisan u sistemu.")) from exc

    def get_template_names(self):
        if getattr(self, "object", None) is not None and self.object.is_coming_soon:
            return ["brands/brand_coming_soon.html"]
        return ["brands/jeegee_prikljucna.html"]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.object.is_coming_soon:
            return ctx
        ctx["categories"] = list(
            Category.objects.filter(
                is_for=Category.CategoryScope.MEHANIZACIJA,
                slug__in=_PRIKLJUCNA_CATEGORY_SLUGS,
            ).order_by("display_order", "name")
        )
        return ctx


class SubcategoryListView(TemplateView):
    """Subcategory drill-down listing — Story 2.11.

    Varijabilan-depth path (L1/L2/L3) → Category root + Subcategory chain.
    Intermediate vs leaf je data-driven (children win, SM-D3/AC14). Cross-boundary
    Product read za leaf model grid (SM-D13, read-only).
    """

    template_name = "brands/subcategory_listing.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        category_slug = kwargs["category_slug"]
        subcat_slugs = [
            kwargs[key]
            for key in ("l1_slug", "l2_slug", "l3_slug")
            if kwargs.get(key) is not None
        ]

        try:
            category = Category.objects.get(
                slug=category_slug,
                is_for=Category.CategoryScope.MEHANIZACIJA,
            )
        except Category.DoesNotExist as exc:
            raise Http404(_("Kategorija nije pronađena.")) from exc

        current = self._resolve_chain(category, subcat_slugs)

        if current is None:
            children = list(
                category.subcategories.filter(parent=None).order_by(
                    "display_order", "name"
                )
            )
            for child in children:
                child.category = category
                child.parent = None
            ctx["current_title"] = category.name
            # REFACTOR-4: single breadcrumb builder handles current is None
            # (category-root) branch internally.
            ctx["breadcrumb_items"] = self._build_breadcrumb(category, None)
            ctx["is_leaf"] = False
            ctx["children"] = children
            return ctx

        ctx["current_title"] = current.name
        ctx["breadcrumb_items"] = self._build_breadcrumb(category, current)

        children = list(current.children.order_by("display_order", "name"))
        if children:
            for child in children:
                child.category = category
                child.parent = current
            ctx["is_leaf"] = False
            ctx["children"] = children
        else:
            ctx["is_leaf"] = True
            ctx["products"] = list(
                Product.objects.filter(
                    subcategory=current,
                    is_published=True,
                ).select_related("brand")
            )
        return ctx

    def _resolve_chain(self, category, subcat_slugs):
        current = None
        for index, slug in enumerate(subcat_slugs):
            try:
                if index == 0:
                    current = Subcategory.objects.select_related(
                        "category", "parent"
                    ).get(
                        category=category,
                        parent=None,
                        slug=slug,
                    )
                else:
                    current = Subcategory.objects.select_related(
                        "category", "parent"
                    ).get(
                        parent=current,
                        slug=slug,
                    )
            except Subcategory.DoesNotExist as exc:
                raise Http404(_("Potkategorija nije pronađena.")) from exc
        return current

    def _build_breadcrumb(self, category, current):
        """Build the root-first breadcrumb trail (SM-D9).

        REFACTOR-4 (Review-Fix iter 1): single builder for both the
        category-root case (``current is None`` — reached via
        ``subcategory_listing_category``; the Category itself is the current
        non-link tail) and the intermediate/leaf cases (walk the resolved
        Subcategory ancestor chain). The first two fixed items (Početna,
        Priključna mehanizacija) are shared by both — single source of truth,
        collapsing the previous ``_build_category_breadcrumb`` duplicate.
        """
        items = [
            {
                "label": _("Početna"),
                "url": reverse("core:home"),
                "is_current": False,
            },
            {
                "label": _("Priključna mehanizacija"),
                "url": reverse("brands:jeegee_prikljucna"),
                "is_current": False,
            },
        ]

        if current is None:
            # Category root → the Category itself is the current (non-link) item.
            items.append({"label": category.name, "url": None, "is_current": True})
            return items

        # Intermediate/leaf: Category is a link, then each Subcategory ancestor,
        # then the current node as the non-link tail.
        items.append(
            {
                "label": category.name,
                "url": self._category_breadcrumb_url(category, current),
                "is_current": False,
            }
        )
        for ancestor in current.get_ancestors_chain():
            items.append(
                {
                    "label": ancestor.name,
                    "url": ancestor.get_absolute_url(),
                    "is_current": False,
                }
            )
        items.append({"label": current.name, "url": None, "is_current": True})
        return items

    @staticmethod
    def _category_breadcrumb_url(category, current):
        ancestors = current.get_ancestors_chain()
        root = ancestors[0] if ancestors else current
        return reverse(
            "brands:subcategory_listing_l1",
            kwargs={"category_slug": category.slug, "l1_slug": root.slug},
        )
