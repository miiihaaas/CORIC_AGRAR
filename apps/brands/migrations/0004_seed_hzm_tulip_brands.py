"""Story 2.12 data migracija — seed HZM + Tulip brendove, kategorije, modele, specifikacije.

Idempotentna kroz get_or_create. Reverse delete-uje tačno seed-ovane instance po slug-u
(FK-safe: specs → products → tulip brand → subcategories → category → hzm brand).
NEMA modeltranslation hu/en prevode za name polja u v1 (per Story 2-10 SM-D — Story 8-5
admin populacija planirana kasnije).

Cross-app: Product/ProductSpecification kroz apps.get_model("products", ...) — depends_on
products 0003 (SM-D8) da historical modeli postoje.
"""

from decimal import Decimal

from django.db import migrations

_HZM_BRAND_DATA = {
    "slug": "hzm",
    "name": "HZM",
    "name_sr": "HZM",
    "brand_color": "",
    "is_coming_soon": False,
    "description": "",
    "description_sr": "",
    "slogan": "",
    "slogan_sr": "",
    "statistics": [],
}

_HZM_CATEGORY_DATA = {
    "slug": "radne-masine",
    "name": "Radne mašine",
    "name_sr": "Radne mašine",
    "is_for": "mehanizacija",
    "display_order": 40,
    "description": "Utovarivači i telehendleri za sve poljoprivredne i industrijske potrebe.",
    "description_sr": "Utovarivači i telehendleri za sve poljoprivredne i industrijske potrebe.",
    "icon": "",
}

_HZM_SUBCATEGORIES = [
    {"slug": "mini-utovarivaci", "name": "Mini utovarivači", "display_order": 10},
    {
        "slug": "utovarivaci-bez-teleskopa",
        "name": "Utovarivači bez teleskopa",
        "display_order": 20,
    },
    {
        "slug": "teleskopski-utovarivaci",
        "name": "Teleskopski utovarivači",
        "display_order": 30,
    },
    {"slug": "telehendleri", "name": "Telehendleri", "display_order": 40},
]

_TULIP_BRAND_DATA = {
    "slug": "tulip",
    "name": "Tulip",
    "name_sr": "Tulip",
    "brand_color": "",
    "is_coming_soon": False,
    "description": "",
    "description_sr": "",
    "slogan": "",
    "slogan_sr": "",
    "statistics": [],
}

_TULIP_PRODUCTS = [
    {
        "slug": "tulip-mix-6m3",
        "name": "Tulip MIX 6 m³",
        "price_eur": Decimal("6500.00"),
        "key_features": [
            "Zapremina 6 m³",
            "Robusna konstrukcija",
            "Pocinkovano kućište",
        ],
    },
    {
        "slug": "tulip-mix-8m3",
        "name": "Tulip MIX 8 m³",
        "price_eur": Decimal("8200.00"),
        "key_features": [
            "Zapremina 8 m³",
            "Robusna konstrukcija",
            "Pocinkovano kućište",
        ],
    },
]

# DEMO/PLACEHOLDER — realne dimenzije (Dužina/Širina/Nosivost) čekaju biznis potvrdu
# (Mihas), vidi OQ-4. Renderuju se u public uporednoj tabeli pa izgledaju realno; PRE
# produkcije zahtevaju potvrdu. "Zapremina" (6/8 m³) je jedina pouzdana (iz naziva modela).
_TULIP_SPECS = {
    "tulip-mix-6m3": [
        {"key": "Zapremina", "value": "6 m³", "order": 0},
        {"key": "Dužina", "value": "4035 mm", "order": 1},
        {"key": "Širina", "value": "2100 mm", "order": 2},
        {"key": "Nosivost", "value": "6000 kg", "order": 3},
    ],
    "tulip-mix-8m3": [
        {"key": "Zapremina", "value": "8 m³", "order": 0},
        {"key": "Dužina", "value": "4500 mm", "order": 1},
        {"key": "Širina", "value": "2300 mm", "order": 2},
        {"key": "Nosivost", "value": "8000 kg", "order": 3},
    ],
}


def seed_hzm_and_tulip(apps, schema_editor):
    Brand = apps.get_model("brands", "Brand")
    Category = apps.get_model("brands", "Category")
    Subcategory = apps.get_model("brands", "Subcategory")
    Product = apps.get_model("products", "Product")
    ProductSpecification = apps.get_model("products", "ProductSpecification")

    Brand.objects.get_or_create(slug=_HZM_BRAND_DATA["slug"], defaults=_HZM_BRAND_DATA)

    category, _ = Category.objects.get_or_create(
        slug=_HZM_CATEGORY_DATA["slug"], defaults=_HZM_CATEGORY_DATA
    )

    for sub in _HZM_SUBCATEGORIES:
        Subcategory.objects.get_or_create(
            category=category,
            parent=None,
            slug=sub["slug"],
            defaults={
                "name": sub["name"],
                "name_sr": sub["name"],
                "display_order": sub["display_order"],
                "description": "",
                "icon": "",
            },
        )

    tulip, _ = Brand.objects.get_or_create(
        slug=_TULIP_BRAND_DATA["slug"], defaults=_TULIP_BRAND_DATA
    )

    for prod in _TULIP_PRODUCTS:
        product, _ = Product.objects.get_or_create(
            slug=prod["slug"],
            defaults={
                "brand": tulip,
                "name": prod["name"],
                "name_sr": prod["name"],
                "is_published": True,
                "status": "published",
                "price_eur": prod["price_eur"],
                "key_features": prod["key_features"],
                "key_features_sr": prod["key_features"],
                "description": "",
            },
        )
        for spec in _TULIP_SPECS[prod["slug"]]:
            ProductSpecification.objects.get_or_create(
                product=product,
                section="ostalo",
                key=spec["key"],
                defaults={
                    "key_sr": spec["key"],
                    "value": spec["value"],
                    "value_sr": spec["value"],
                    "order": spec["order"],
                },
            )


def reverse_seed(apps, schema_editor):
    Brand = apps.get_model("brands", "Brand")
    Category = apps.get_model("brands", "Category")
    Subcategory = apps.get_model("brands", "Subcategory")
    Product = apps.get_model("products", "Product")
    ProductSpecification = apps.get_model("products", "ProductSpecification")

    tulip_slugs = [p["slug"] for p in _TULIP_PRODUCTS]
    ProductSpecification.objects.filter(product__slug__in=tulip_slugs).delete()
    Product.objects.filter(slug__in=tulip_slugs).delete()
    Brand.objects.filter(slug=_TULIP_BRAND_DATA["slug"]).delete()
    Subcategory.objects.filter(category__slug=_HZM_CATEGORY_DATA["slug"]).delete()
    Category.objects.filter(slug=_HZM_CATEGORY_DATA["slug"]).delete()
    Brand.objects.filter(slug=_HZM_BRAND_DATA["slug"]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("brands", "0003_seed_jeegee_and_prikljucna_categories"),
        ("products", "0003_alter_productvariant_description_and_more"),
    ]

    operations = [
        migrations.RunPython(seed_hzm_and_tulip, reverse_code=reverse_seed),
    ]
