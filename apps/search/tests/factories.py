"""Story 2.13 — TEA RED phase factory helper za search FTS testove.

Wrapper oko postojećeg `apps.products.tests.factories.ProductFactory` koji postavlja
modeltranslation kolone (`name_sr/_hu/_en`, `description_sr/_hu/_en`) direktno, jer
`build_product_search_qs(query, language_code)` gradi SearchVector NAD per-locale
kolonama (SM-D9). Postojeći ProductFactory postavlja samo base `name`/`description`
(što modeltranslation mapira na aktivni locale) — za locale-isolation + diacritic
testove treba EKSPLICITNA kontrola po-jeziku.

Konvencija mirror-uje plain-classmethod factory pattern iz apps/products/tests/factories.py
(projekat NEMA factory_boy — verifikovano 2026-05-30).

Korišćenje:
    from apps.search.tests.factories import SearchProductFactory

    # eksplicitni per-locale nazivi:
    p = SearchProductFactory.create(
        name_sr="Bérba mašina", name_hu="Szedő gép", name_en="Harvester",
        description_sr="Opis na srpskom", is_published=True,
    )

Refs:
- 2-13-interface-contract.md § 1 (factories.py NOVO TEA) + § 2 (search.py per-locale kolone)
- apps/products/tests/factories.py (postojeća ProductFactory konvencija)
"""

from __future__ import annotations

from typing import Any


class SearchProductFactory:
    """Kreira published Product sa eksplicitnim per-locale name/description kolonama.

    Default: published, sve 3 locale name kolone popunjene istom vrednošću ako caller
    ne prosledi `name_<lang>`. Caller PREPISUJE pojedinačne `name_sr`/`name_hu`/`name_en`
    /`description_sr`/... kwargs za locale-isolation + diacritic + rank testove.
    """

    _counter = 0
    _slug_counter = 0

    @classmethod
    def _next_name(cls) -> str:
        cls._counter += 1
        return f"Search Test Product {cls._counter}"

    @classmethod
    def _next_slug(cls) -> str:
        cls._slug_counter += 1
        return f"search-test-product-{cls._slug_counter}"

    @classmethod
    def create(cls, brand=None, **overrides: Any):
        from apps.products.models import Product

        if brand is None:
            from apps.brands.tests.factories import BrandFactory

            brand = BrandFactory.create()

        base_name = overrides.pop("name", None) or cls._next_name()
        slug = overrides.pop("slug", None) or cls._next_slug()

        # Postavi base + sva 3 locale name polja ako caller nije eksplicitno dao.
        # NAPOMENA (genuine factory fix): rank/tie-break testovi NAMERNO kreiraju
        # više proizvoda sa ISTIM name_sr (npr. „Berba alfa") — slug auto-gen iz
        # name bi tada kolidirao (UniqueConstraint). Postavljamo eksplicitan unikatan
        # slug iz internog counter-a osim ako caller eksplicitno prosledi slug.
        defaults: dict[str, Any] = {
            "brand": brand,
            "name": base_name,
            "slug": slug,
            "is_published": True,
            "condition": Product.ConditionChoice.NEW,
            "status": Product.StatusChoice.PUBLISHED,
        }
        defaults.update(overrides)

        product = Product.objects.create(**defaults)

        # modeltranslation: ako caller NIJE eksplicitno setovao per-locale name kolone,
        # popuni ih iz base_name tako da search nešto nađe na svim jezicima.
        to_update: dict[str, Any] = {}
        for lang in ("sr", "hu", "en"):
            attr = f"name_{lang}"
            if attr not in overrides and not getattr(product, attr, None):
                setattr(product, attr, base_name)
                to_update[attr] = base_name
        if to_update:
            # QuerySet.update() (NE product.save()) — Product.save() override UVEK poziva
            # full_clean() (per-locale backfill bi bio nepotrebno spor + re-trigger slug
            # logike). .update() piše SAMO locale kolone direktno u DB, bez validacije.
            Product.objects.filter(pk=product.pk).update(**to_update)

        return product

    @classmethod
    def create_unpublished(cls, brand=None, **overrides: Any):
        overrides["is_published"] = False
        overrides.setdefault("status", "draft")
        return cls.create(brand=brand, **overrides)
