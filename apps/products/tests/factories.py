"""Story 2.6 — Factory Boy-style helper factories za Product + related.

Projekat trenutno NEMA `factory_boy` u `pyproject.toml` (verifikovano live 2026-05-30).
Ovi factory-ji koriste **plain classmethod create()** koji mirror Factory Boy public
surface tako da buduća migracija ka factory_boy bude trivial rename.

Korišćenje:

    from apps.products.tests.factories import (
        ProductFactory,
        ProductSpecificationFactory,
        ProductTestimonialFactory,
    )

    product = ProductFactory.create()                         # default valid Product (is_published=True)
    product = ProductFactory.create_unpublished()             # is_published=False
    spec = ProductSpecificationFactory.create(product=product, section="motor")
    testimonial = ProductTestimonialFactory.create(product=product)

Sve helpers respektuju Story 2.2 model invariante (slug auto-gen iz name kroz
SluggedModel save() pattern; not-null FK ka Brand uvek auto-create).
"""

from __future__ import annotations

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
