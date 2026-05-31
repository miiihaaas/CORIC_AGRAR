"""Story 2.10 data migracija — seed Jeegee Brand + 3 mehanizacija kategorije.

Idempotentna kroz get_or_create. Reverse delete-uje tačno te 4 instance po slug-u.
NEMA modeltranslation hu/en prevode za Category.name u v1 (per SM-D14 — Story 8-5
admin populacija planirana kasnije).
"""

from django.db import migrations

# NOTE (modeltranslation): `name`/`description` su registrovana translated polja
# (apps/brands/translation.py); accessor `instance.name` čita default-locale kolonu
# `name_sr`. Seed MORA popuniti i `_sr` kolone da fallback vrati srpski naziv.
_JEEGEE_BRAND_DATA = {
    "slug": "jeegee",
    "name": "Jeegee",
    "name_sr": "Jeegee",
    "brand_color": "#00A4E9",
    "is_coming_soon": False,
    "description": "",
    "description_sr": "",
    "slogan": "",
    "slogan_sr": "",
    "statistics": [],
}

_PRIKLJUCNA_CATEGORIES = [
    {
        "slug": "osnovna-obrada-zemljista",
        "name": "Osnovna obrada zemljišta",
        "name_sr": "Osnovna obrada zemljišta",
        "is_for": "mehanizacija",
        "display_order": 10,
        "description": "Plugovi, podrivači, gruberi za primarnu obradu zemljišta.",
        "description_sr": "Plugovi, podrivači, gruberi za primarnu obradu zemljišta.",
        "icon": "",
    },
    {
        "slug": "priprema-zemljista",
        "name": "Priprema zemljišta",
        "name_sr": "Priprema zemljišta",
        "is_for": "mehanizacija",
        "display_order": 20,
        "description": "Tanjirače, drljače, valjci za sekundarnu pripremu zemljišta.",
        "description_sr": "Tanjirače, drljače, valjci za sekundarnu pripremu zemljišta.",
        "icon": "",
    },
    {
        "slug": "masine-za-setvu",
        "name": "Mašine za setvu",
        "name_sr": "Mašine za setvu",
        "is_for": "mehanizacija",
        "display_order": 30,
        "description": "Sejalice i mašine za setvu strnih žita i okopavinskih kultura.",
        "description_sr": "Sejalice i mašine za setvu strnih žita i okopavinskih kultura.",
        "icon": "",
    },
]


def seed_jeegee_and_categories(apps, schema_editor):
    Brand = apps.get_model("brands", "Brand")
    Category = apps.get_model("brands", "Category")

    Brand.objects.get_or_create(
        slug=_JEEGEE_BRAND_DATA["slug"],
        defaults=_JEEGEE_BRAND_DATA,
    )

    for cat_data in _PRIKLJUCNA_CATEGORIES:
        Category.objects.get_or_create(
            slug=cat_data["slug"],
            defaults=cat_data,
        )


def reverse_seed(apps, schema_editor):
    Brand = apps.get_model("brands", "Brand")
    Category = apps.get_model("brands", "Category")

    Brand.objects.filter(slug=_JEEGEE_BRAND_DATA["slug"]).delete()
    Category.objects.filter(
        slug__in=[c["slug"] for c in _PRIKLJUCNA_CATEGORIES]
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("brands", "0002_alter_brand_created_at"),
    ]

    operations = [
        migrations.RunPython(seed_jeegee_and_categories, reverse_code=reverse_seed),
    ]
