"""Story 2.6 — Factory Boy-style helper factories za Brand + Series + Category + Subcategory.

Projekat trenutno NEMA `factory_boy` u `pyproject.toml` (verifikovano live 2026-05-30).
Ovi factory-ji koriste **plain classmethod create()** koji mirror Factory Boy public
surface (`Factory.create()`, `Factory.create_batch(N)` ako zatreba kasnije) tako da
buduća migracija ka factory_boy bude trivial rename.

POZIVANJE — podržana DVA idioma:
- `BrandFactory.create(**overrides)` (eksplicitno, mirror factory_boy `.create()`).
- `CategoryFactory(**overrides)` (direktan call na klasu — delegira na `.create()` kroz
  `_CallableFactoryMeta`; mirror factory_boy `Factory(...)` instance idiom).

Korišćenje (mirror factory_boy idiom):

    from apps.brands.tests.factories import (
        BrandFactory, SeriesFactory, CategoryFactory, SubcategoryFactory,
    )

    brand = BrandFactory.create()
    cat = CategoryFactory(slug="plugovi")                       # direktan call
    cat = CategoryFactory.create(is_for="traktori")             # .create() idiom
    l1 = SubcategoryFactory(category=cat, slug="jednobrazni")   # top-level (depth 1)
    l2 = SubcategoryFactory(category=cat, parent=l1, slug="lemes")

Sve helpers respektuju Story 2.1 model invariante (slug auto-gen iz name kroz model
`save()`; ne treba eksplicitno postavljati slug). Sve `**overrides` propagiraju u
`Model.objects.create(**defaults)` poziv.
"""

from __future__ import annotations

from typing import Any


class _CallableFactoryMeta(type):
    """Metaklasa koja dozvoljava `Factory(**kwargs)` da delegira na `Factory.create(**kwargs)`.

    Omogućava factory_boy-style direktan-call idiom (`CategoryFactory(slug=...)`)
    na plain-classmethod factory klasama, bez instanciranja same factory klase.
    """

    def __call__(cls, **kwargs: Any):  # noqa: N805
        return cls.create(**kwargs)


class BrandFactory(metaclass=_CallableFactoryMeta):
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


class SeriesFactory(metaclass=_CallableFactoryMeta):
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


class CategoryFactory(metaclass=_CallableFactoryMeta):
    """Helper factory za apps.brands.models.Category (Story 2.10 + 2.11).

    Default-i: name='Test Kategorija {n}', is_for=MEHANIZACIJA, display_order=0.
    Slug se auto-generiše iz name kroz Category.save() ako nije eksplicitan.
    """

    _counter = 0

    @classmethod
    def _next_name(cls) -> str:
        cls._counter += 1
        return f"Test Kategorija {cls._counter}"

    @classmethod
    def create(cls, **overrides: Any):
        from apps.brands.models import Category

        defaults = {
            "name": cls._next_name(),
            "is_for": Category.CategoryScope.MEHANIZACIJA,
            "display_order": 0,
        }
        defaults.update(overrides)
        return Category.objects.create(**defaults)


class SubcategoryFactory(metaclass=_CallableFactoryMeta):
    """Helper factory za apps.brands.models.Subcategory (Story 2.11).

    - Po defaultu pravi top-level (parent=None, depth 1) node u novoj kategoriji.
    - `parent` kwarg dozvoljava lanac (depth-safe <= 3); kada se prosledi `parent`,
      kategorija se nasleđuje od parent-a ako `category` nije eksplicitan.
    - Slug se auto-generiše iz name ako nije eksplicitan (ASCII kroz model save()).
    - DOZVOLJAVA dva subcat-a sa ISTIM slug-om pod RAZLIČITIM parent-ima u istoj
      kategoriji (UniqueConstraint je (category, parent, slug)): testovi koji to žele
      prosleđuju eksplicitan `slug=...` na oba node-a sa različitim `parent`.
    """

    _counter = 0

    @classmethod
    def _next_name(cls) -> str:
        cls._counter += 1
        return f"Test Potkategorija {cls._counter}"

    @classmethod
    def create(cls, category=None, parent=None, **overrides: Any):
        from apps.brands.models import Subcategory

        if category is None:
            category = parent.category if parent is not None else CategoryFactory.create()
        defaults = {
            "category": category,
            "parent": parent,
            "name": cls._next_name(),
            "display_order": 0,
        }
        defaults.update(overrides)
        return Subcategory.objects.create(**defaults)
