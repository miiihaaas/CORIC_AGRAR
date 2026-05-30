"""Story 2.6 — Factory Boy-style helper factories za Brand + Series.

Projekat trenutno NEMA `factory_boy` u `pyproject.toml` (verifikovano live 2026-05-30).
Ovi factory-ji koriste **plain classmethod create()** koji mirror Factory Boy public
surface (`Factory.create()`, `Factory.create_batch(N)` ako zatreba kasnije) tako da
buduća migracija ka factory_boy bude trivial rename.

Korišćenje (mirror factory_boy idiom):

    from apps.brands.tests.factories import BrandFactory, SeriesFactory

    brand = BrandFactory.create()                              # default valid Brand
    brand = BrandFactory.create(name="John Deere", slug="jd")  # override fields
    brand = BrandFactory.create_coming_soon(name="Future Brand")
    brand = BrandFactory.create_with_statistics()              # 4 statistike entries

    series = SeriesFactory.create_grid(brand=brand, name="8R Serija")
    series = SeriesFactory.create_extended(brand=brand, name="9R Serija")

Sve helpers respektuju Story 2.1 model invariante (slug auto-gen iz name kroz model
`save()`; ne treba eksplicitno postavljati slug). Sve `**overrides` propagiraju u
`Model.objects.create(**defaults)` poziv.
"""

from __future__ import annotations

from typing import Any


class BrandFactory:
    """Helper factory za apps.brands.models.Brand.

    Default-i: name='Test Brand', brand_color='', statistics=[], is_coming_soon=False.
    Slug se auto-generiše iz name kroz Brand.save() (Story 2.1 CRIT-2 pattern).
    """

    _counter = 0

    @classmethod
    def _next_name(cls) -> str:
        cls._counter += 1
        return f"Test Brand {cls._counter}"

    @classmethod
    def create(cls, **overrides: Any):
        from apps.brands.models import Brand

        defaults = {
            "name": cls._next_name(),
            "brand_color": "",
            "statistics": [],
            "is_coming_soon": False,
        }
        defaults.update(overrides)
        return Brand.objects.create(**defaults)

    @classmethod
    def create_coming_soon(cls, **overrides: Any):
        overrides.setdefault("is_coming_soon", True)
        return cls.create(**overrides)

    @classmethod
    def create_with_statistics(cls, stats=None, **overrides: Any):
        if stats is None:
            stats = [
                {"value": 5000, "label": "Prodatih traktora"},
                {"value": 25, "label": "Godina iskustva"},
                {"value": 12, "label": "Modela u ponudi"},
                {"value": 98, "label": "Zadovoljnih kupaca"},
            ]
        overrides.setdefault("statistics", stats)
        return cls.create(**overrides)

    @classmethod
    def create_with_catalog_pdf(cls, **overrides: Any):
        """Brand sa minimalnim PDF stub-om u catalog_pdf polju (za AC3 CTA test)."""
        from django.core.files.base import ContentFile

        brand = cls.create(**overrides)
        brand.catalog_pdf.save(
            "stub.pdf",
            ContentFile(b"%PDF-1.4 stub"),
            save=True,
        )
        return brand


class SeriesFactory:
    """Helper factory za apps.brands.models.Series.

    Default-i: name='Test Series', layout_mode='grid', display_order=0.
    Slug se auto-generiše iz name kroz Series.save() (Story 2.1 CRIT-2 pattern).
    Brand se kreira automatski kroz BrandFactory ako caller ne prosledi `brand=`.
    """

    _counter = 0

    @classmethod
    def _next_name(cls) -> str:
        cls._counter += 1
        return f"Test Series {cls._counter}"

    @classmethod
    def create(cls, brand=None, **overrides: Any):
        from apps.brands.models import Series

        if brand is None:
            brand = BrandFactory.create()
        defaults = {
            "brand": brand,
            "name": cls._next_name(),
            "layout_mode": Series.LayoutMode.GRID,
            "display_order": 0,
        }
        defaults.update(overrides)
        return Series.objects.create(**defaults)

    @classmethod
    def create_grid(cls, brand=None, **overrides: Any):
        from apps.brands.models import Series

        overrides.setdefault("layout_mode", Series.LayoutMode.GRID)
        return cls.create(brand=brand, **overrides)

    @classmethod
    def create_extended(cls, brand=None, **overrides: Any):
        from apps.brands.models import Series

        overrides.setdefault("layout_mode", Series.LayoutMode.EXTENDED)
        return cls.create(brand=brand, **overrides)
