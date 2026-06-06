"""Story 6.2 — Sitemap auto-generation sa hreflang (READ-ONLY agregator).

5 Django `Sitemap` podklase (NEMA Series/Category — CRIT-2/SM-D6: njihov
get_absolute_url RAISE NoReverseMatch jer rute ne postoje → uključenje bi oborilo
CEO /sitemap.xml u HTTP 500). SVE klase: ``i18n = True`` + ``alternates = True`` →
Django auto-emit ``<xhtml:link rel="alternate" hreflang="sr|hu|en">`` per LANGUAGES
(SM-D1; NIKAD hand-rolled XML).

DRAFT-NOT-LEAKED (SECURITY BOUNDARY — SM-D3): svaka items() vraća SAMO javne
objekte (Product is_published=True / Brand is_coming_soon=False / Subcategory .all()
/ Post.published). Jedan nacrt u sitemap-u = curenje u Google indeks.

exclude_from_sitemap (SM-D4): GFK exclusion-set preko ``_excluded_pks(model)``
(JEDAN query po klasi; NEMA join jer SeoMeta nema GenericRelation — ARCH-2/OQ-4
iz 6-1). items() = ``public_qs.exclude(pk__in=_excluded_pks(Model))``.

Modul se importuje LAZY kroz config/urls.py (NIKAD u models.py/apps.ready) da se
izbegne kružni import.
"""

from django.contrib.contenttypes.models import ContentType
from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from apps.blog.models import Post
from apps.brands.models import Brand, Subcategory  # NE Series/Category (CRIT-2)
from apps.products.models import Product
from apps.seo.models import SeoMeta


def _excluded_pks(model):
    """Skup pk-jeva sa exclude_from_sitemap=True za dati model (JEDAN query, NEMA join)."""
    ct = ContentType.objects.get_for_model(model)
    return set(
        SeoMeta.objects.filter(
            content_type=ct, exclude_from_sitemap=True
        ).values_list("object_id", flat=True)
    )


class ProductSitemap(Sitemap):
    i18n = True
    alternates = True

    def items(self):
        return Product.objects.filter(is_published=True).exclude(
            pk__in=_excluded_pks(Product)
        )

    def lastmod(self, obj):
        return obj.updated_at


class BrandSitemap(Sitemap):
    i18n = True
    alternates = True

    def items(self):
        return Brand.objects.filter(is_coming_soon=False).exclude(
            pk__in=_excluded_pks(Brand)
        )

    def lastmod(self, obj):
        return obj.updated_at


class SubcategorySitemap(Sitemap):
    i18n = True
    alternates = True

    def items(self):
        # GAP-1: get_absolute_url() traverzira ancestor chain × 3 jezika →
        # select_related izbegava N+1 na parent/category lookup-ima.
        return Subcategory.objects.select_related(
            "category", "parent", "parent__parent"
        ).exclude(pk__in=_excluded_pks(Subcategory))

    def lastmod(self, obj):
        return obj.updated_at


class BlogPostSitemap(Sitemap):
    i18n = True
    alternates = True

    def items(self):
        # Post.published = status=published AND published_at<=now (draft + scheduled izostaju).
        return Post.published.all().exclude(pk__in=_excluded_pks(Post))

    def lastmod(self, obj):
        return obj.updated_at


class PageSitemap(Sitemap):
    i18n = True
    alternates = True

    def items(self):
        return ["pages:home", "pages:about", "pages:contact"]

    def location(self, item):
        return reverse(item)

    # NEMA lastmod (statičke strane bez updated_at; Django izostavi <lastmod> — SM-D7/SM2-7).


sitemaps = {
    "products": ProductSitemap,
    "brands": BrandSitemap,
    "subcategories": SubcategorySitemap,
    "blog": BlogPostSitemap,
    "pages": PageSitemap,
}
