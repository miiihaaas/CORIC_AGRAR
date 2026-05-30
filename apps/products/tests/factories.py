"""Story 2.6+2.7 — Factory Boy-style helper factories za Product + related.

Projekat trenutno NEMA `factory_boy` u `pyproject.toml` (verifikovano live 2026-05-30).
Ovi factory-ji koriste **plain classmethod create()** koji mirror Factory Boy public
surface tako da buduća migracija ka factory_boy bude trivial rename.

Korišćenje:

    from apps.products.tests.factories import (
        ProductFactory,
        ProductSpecificationFactory,
        ProductTestimonialFactory,
        ProductImageFactory,
        ProductBrochureFactory,
        ProductVariantFactory,
        ProductSimilarFactory,
    )

    product = ProductFactory.create()                         # default valid Product (is_published=True)
    product = ProductFactory.create_unpublished()             # is_published=False
    spec = ProductSpecificationFactory.create(product=product, section="motor")
    testimonial = ProductTestimonialFactory.create(product=product)
    image = ProductImageFactory.create(product=product, order=0)
    brochure = ProductBrochureFactory.create(product=product)
    variant = ProductVariantFactory.create(product=product, name="Sa kabinom")
    similar = ProductSimilarFactory.create(product=product, related_product=other)

Sve helpers respektuju Story 2.2 model invariante (slug auto-gen iz name kroz
SluggedModel save() pattern; not-null FK ka Brand uvek auto-create).

Story 2.7 EXTEND: dodaje ProductImageFactory, ProductBrochureFactory,
ProductVariantFactory, ProductSimilarFactory (sve za product detail strana tests).
"""

from __future__ import annotations

from io import BytesIO
from typing import Any


class ProductFactory:
    """Helper factory za apps.products.models.Product.

    Default-i: name='Test Product', is_published=True, condition='new', status='draft'.
    Slug se auto-generiše iz name kroz Product.save() (SluggedModel mixin).
    Brand se kreira automatski kroz BrandFactory ako caller ne prosledi `brand=`.
    """

    _counter = 0

    @classmethod
    def _next_name(cls) -> str:
        cls._counter += 1
        return f"Test Product {cls._counter}"

    @classmethod
    def create(cls, brand=None, series=None, **overrides: Any):
        from apps.products.models import Product

        if brand is None:
            from apps.brands.tests.factories import BrandFactory

            brand = BrandFactory.create()
        defaults = {
            "brand": brand,
            "series": series,
            "name": cls._next_name(),
            "is_published": True,
            "condition": Product.ConditionChoice.NEW,
            "status": Product.StatusChoice.DRAFT,
        }
        defaults.update(overrides)
        return Product.objects.create(**defaults)

    @classmethod
    def create_published(cls, **overrides: Any):
        overrides.setdefault("is_published", True)
        return cls.create(**overrides)

    @classmethod
    def create_unpublished(cls, **overrides: Any):
        overrides["is_published"] = False
        return cls.create(**overrides)


class ProductSpecificationFactory:
    """Helper factory za apps.products.models.ProductSpecification.

    Default-i: section='motor', key='Snaga motora', value='100 KS', order=0.
    Product se kreira automatski kroz ProductFactory ako caller ne prosledi `product=`.
    """

    _counter = 0

    @classmethod
    def _next_key(cls) -> str:
        cls._counter += 1
        return f"Spec {cls._counter}"

    @classmethod
    def create(cls, product=None, section: str = "motor", **overrides: Any):
        from apps.products.models import ProductSpecification

        if product is None:
            product = ProductFactory.create()
        defaults = {
            "product": product,
            "section": section,
            "key": cls._next_key(),
            "value": "Test Value",
            "order": 0,
        }
        defaults.update(overrides)
        return ProductSpecification.objects.create(**defaults)


class ProductTestimonialFactory:
    """Helper factory za apps.products.models.ProductTestimonial.

    Default-i: quote='Odlični traktor.', author_name='Marko Petrović',
    location='Novi Sad', order=0.
    Product se kreira automatski kroz ProductFactory ako caller ne prosledi `product=`.
    photo polje OSTAJE PRAZNO po default-u (testovi koji testiraju photo branching
    moraju ga eksplicitno setovati).
    """

    _counter = 0

    @classmethod
    def _next_quote(cls) -> str:
        cls._counter += 1
        return f"Test citat {cls._counter} — odlični traktor, preporučujem svima."

    @classmethod
    def create(cls, product=None, **overrides: Any):
        from apps.products.models import ProductTestimonial

        if product is None:
            product = ProductFactory.create()
        defaults = {
            "product": product,
            "quote": cls._next_quote(),
            "author_name": "Marko Petrović",
            "location": "Novi Sad",
            "order": 0,
        }
        defaults.update(overrides)
        return ProductTestimonial.objects.create(**defaults)


# =============================================================================
# Story 2.7 — Helper: minimal binary stubs za ImageField / FileField
# =============================================================================


def _minimal_png_bytes() -> bytes:
    """Pillow-generated 1×1 RGB PNG za ImageField test stub-ove.

    Razlog (mirror media_pipeline/tests/conftest.py § valid_png_bytes):
    Hardcoded fake PNG bytes ne prolaze Pillow Image.verify() jer Django
    ImageField interno poziva verify() pri upload validaciji.
    """
    try:
        from PIL import Image
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "PIL/Pillow is required for image factories — install via uv sync"
        ) from exc

    img = Image.new("RGB", (1, 1), color="red")
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# Minimal validan 1-page PDF struct (per Story 2.4 PDF-D5 + media_pipeline conftest).
# Padded sa PDF comment-om (% prefix) tako da total veličina >= 1024 bytes — Django
# filesizeformat pod sr locale-om vraća Cyrillic "бајтова" za < 1KB, ali Latinica
# "X,X KB" za >= 1KB; realistic brochures su uvek >= 1KB.
_MINIMAL_PDF_BYTES = (
    b"%PDF-1.4\n"
    b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
    b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
    b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
    b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n"
    b"4 0 obj\n<< /Length 44 >>\nstream\nBT /F1 24 Tf 100 700 Td (Hello PDF!) Tj ET\nendstream\nendobj\n"
    b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
    b"xref\n0 6\n0000000000 65535 f\n"
    b"0000000009 00000 n\n0000000058 00000 n\n0000000111 00000 n\n"
    b"0000000212 00000 n\n0000000293 00000 n\n"
    b"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n358\n%%EOF\n"
    + b"%" + b"x" * 600 + b"\n"  # PDF comment padding -> total >= 1024 bytes
)


# =============================================================================
# Story 2.7 — ProductImageFactory (AC4 galerija)
# =============================================================================


class ProductImageFactory:
    """Helper factory za apps.products.models.ProductImage.

    Default-i: order=0, alt_text='Test slika {counter}'.
    Image polje se popunjava sa SimpleUploadedFile koji sadrži minimal validan PNG bytes
    (Pillow-generated 1×1 red).
    """

    _counter = 0

    @classmethod
    def _next_alt(cls) -> str:
        cls._counter += 1
        return f"Test slika {cls._counter}"

    @classmethod
    def create(cls, product=None, order: int = 0, alt_text: str = "", image=None, **overrides: Any):
        from django.core.files.uploadedfile import SimpleUploadedFile

        from apps.products.models import ProductImage

        if product is None:
            product = ProductFactory.create()
        if image is None:
            image = SimpleUploadedFile(
                name=f"test_image_{cls._counter + 1}.png",
                content=_minimal_png_bytes(),
                content_type="image/png",
            )
        defaults = {
            "product": product,
            "image": image,
            "order": order,
            "alt_text": alt_text or cls._next_alt(),
        }
        defaults.update(overrides)
        return ProductImage.objects.create(**defaults)


# =============================================================================
# Story 2.7 — ProductBrochureFactory (AC7)
# =============================================================================


class ProductBrochureFactory:
    """Helper factory za apps.products.models.ProductBrochure.

    Default-i: title='Test Brošura {counter}', pdf_file = minimal PDF struct.
    cover_thumbnail_image OSTAJE PRAZNO po default-u (testovi koji testiraju cover branching
    eksplicitno setuju ili mock-uju). Razlog: Story 2.4 post_save signal auto-generiše
    cover thumbnail iz pdf_file, ali signal može biti disabled u test environment-u —
    eksplicitno postavljanje je predvidljivo.
    """

    _counter = 0

    @classmethod
    def _next_title(cls) -> str:
        cls._counter += 1
        return f"Test Brošura {cls._counter}"

    @classmethod
    def create(
        cls,
        product=None,
        title: str = "",
        pdf_file=None,
        cover_thumbnail_image=None,
        **overrides: Any,
    ):
        from django.core.files.uploadedfile import SimpleUploadedFile

        from apps.products.models import ProductBrochure

        if product is None:
            product = ProductFactory.create()
        if pdf_file is None:
            pdf_file = SimpleUploadedFile(
                name=f"test_brochure_{cls._counter + 1}.pdf",
                content=_MINIMAL_PDF_BYTES,
                content_type="application/pdf",
            )
        defaults = {
            "product": product,
            "pdf_file": pdf_file,
            "title": title or cls._next_title(),
        }
        if cover_thumbnail_image is not None:
            defaults["cover_thumbnail_image"] = cover_thumbnail_image
        defaults.update(overrides)
        return ProductBrochure.objects.create(**defaults)

    @classmethod
    def create_with_cover(cls, product=None, **overrides: Any):
        """Convenience: brochure sa popunjenim cover_thumbnail_image (PNG stub)."""
        from django.core.files.uploadedfile import SimpleUploadedFile

        cover = SimpleUploadedFile(
            name="test_cover.png",
            content=_minimal_png_bytes(),
            content_type="image/png",
        )
        return cls.create(product=product, cover_thumbnail_image=cover, **overrides)


# =============================================================================
# Story 2.7 — ProductVariantFactory (AC8)
# =============================================================================


class ProductVariantFactory:
    """Helper factory za apps.products.models.ProductVariant.

    Default-i: name='Test Varijanta {counter}', code='', image=None, description='', order=0.
    Variant bez slike je validan use-case (test_variant_card_no_image_renders_plain_div).
    """

    _counter = 0

    @classmethod
    def _next_name(cls) -> str:
        cls._counter += 1
        return f"Test Varijanta {cls._counter}"

    @classmethod
    def create(
        cls,
        product=None,
        name: str = "",
        code: str = "",
        image=None,
        description: str = "",
        order: int = 0,
        **overrides: Any,
    ):
        from apps.products.models import ProductVariant

        if product is None:
            product = ProductFactory.create()
        defaults = {
            "product": product,
            "name": name or cls._next_name(),
            "code": code,
            "description": description,
            "order": order,
        }
        if image is not None:
            defaults["image"] = image
        defaults.update(overrides)
        return ProductVariant.objects.create(**defaults)

    @classmethod
    def create_with_image(cls, product=None, **overrides: Any):
        """Convenience: variant sa popunjenom image (PNG stub) — za GLightbox test."""
        from django.core.files.uploadedfile import SimpleUploadedFile

        img = SimpleUploadedFile(
            name="test_variant.png",
            content=_minimal_png_bytes(),
            content_type="image/png",
        )
        return cls.create(product=product, image=img, **overrides)


# =============================================================================
# Story 2.7 — ProductSimilarFactory (AC6 FR-20 manual override)
# =============================================================================


class ProductSimilarFactory:
    """Helper factory za apps.products.models.ProductSimilar.

    Direktan FK pair (product, related_product) sa unique constraint + no-self-reference
    check. Order default=0.
    """

    @classmethod
    def create(cls, product=None, related_product=None, order: int = 0, **overrides: Any):
        from apps.products.models import ProductSimilar

        if product is None:
            product = ProductFactory.create()
        if related_product is None:
            # Kreiraj novi product u istom brendu kao default
            related_product = ProductFactory.create(brand=product.brand)
        defaults = {
            "product": product,
            "related_product": related_product,
            "order": order,
        }
        defaults.update(overrides)
        return ProductSimilar.objects.create(**defaults)


# =============================================================================
# Story 2.8 — TractorProductFactory (kreira Product u traktori scope-u)
# =============================================================================


class TractorProductFactory:
    """Helper koji kreira Product unutar traktori Category.is_for scope-a.

    Story 2.8 TractorListView filter:
        Product.objects.filter(
            is_published=True,
            subcategory__category__is_for='traktori',
        )

    ProductFactory default-i NE postavljaju subcategory (Story 2.7 mu ne treba pa
    je nullable per PR-D3); ovo bi diskvalifikovalo Product-e za tractor listing
    queryset. TractorProductFactory get_or_create-uje shared Category(is_for='traktori')
    + Subcategory + delegira na ProductFactory.create() sa subcategory= override.

    Korišćenje:
        product = TractorProductFactory.create(horse_power=100, price_eur=15000)
        product = TractorProductFactory.create_unpublished()
        product = TractorProductFactory.create(brand=my_brand, name="JD 6120")
    """

    _SHARED_CATEGORY_SLUG = "tea-traktori-default"
    _SHARED_SUBCATEGORY_SLUG = "tea-default-subcat"

    @classmethod
    def _get_or_create_subcategory(cls):
        from apps.brands.models import Category, Subcategory

        category, _ = Category.objects.get_or_create(
            slug=cls._SHARED_CATEGORY_SLUG,
            defaults={"name": "TEA Traktori Default", "is_for": "traktori"},
        )
        subcategory, _ = Subcategory.objects.get_or_create(
            category=category,
            slug=cls._SHARED_SUBCATEGORY_SLUG,
            parent=None,
            defaults={"name": "TEA Default Subcat"},
        )
        return subcategory

    @classmethod
    def create(cls, brand=None, **overrides: Any):
        subcategory = cls._get_or_create_subcategory()
        overrides.setdefault("subcategory", subcategory)
        return ProductFactory.create(brand=brand, **overrides)

    @classmethod
    def create_unpublished(cls, brand=None, **overrides: Any):
        overrides["is_published"] = False
        return cls.create(brand=brand, **overrides)
