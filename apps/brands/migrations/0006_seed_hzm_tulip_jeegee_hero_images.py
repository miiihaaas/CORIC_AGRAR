"""Data migracija — prilaži hero_image (HZM/Tulip/Jeegee) i logo (Tulip) sa static/img izvora.

0004/0003 su te brendove kreirali BEZ hero_image (polje nije postojalo u seed dict-u —
isti "brand kreiran bez ovog polja" slučaj kao Agri Tracking/Saillong/Wuzheng u
seed_sample_data.py). Bez hero_image, `_hzm_hero.html`/`_tulip_hero.html`/
`_jeegee_hero.html` degradiraju na golu zelenu karticu bez foto pozadine. Tulip logo
je isti slučaj — 0004 ga nikad nije setovao (samo lokalno ručno okačen preko admina,
nikad na produkciji).

Izvorne slike (`static/img/...`) su deo repo-a (COPY . /app u Docker image-u — vidi
compose/django/Dockerfile), pa su dostupne na svakom environment-u u trenutku `migrate`
bez ručnog seed koraka. Idempotentna: prilaže SAMO ako je odgovarajuće polje trenutno
prazno (ne re-upload-uje, ne dupli storage-hash-suffix fajl na ponovljeni migrate; NE
overwrite-uje logo koji je neko već ručno okačio preko admina).

Reverse briše fajlove sa storage-a i prazni polja.
"""

from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.db import migrations

_HERO_ASSETS = {
    "hzm": "hzm-hero-baner.jpg",
    "tulip": "tulip-hero-baner.jpg",
    "jeegee": "jeegee-hero-baner.jpg",
}

_LOGO_ASSETS = {
    "tulip": "tulip-logo.png",
}


def _attach_if_missing(brand, field_name, filename):
    if getattr(brand, field_name):
        return
    path = Path(settings.BASE_DIR) / "static" / "img" / filename
    with path.open("rb") as fh:
        getattr(brand, field_name).save(filename, File(fh), save=True)


def attach_brand_assets(apps, schema_editor):
    Brand = apps.get_model("brands", "Brand")
    for slug, filename in _HERO_ASSETS.items():
        try:
            brand = Brand.objects.get(slug=slug)
        except Brand.DoesNotExist:
            continue
        _attach_if_missing(brand, "hero_image", filename)
    for slug, filename in _LOGO_ASSETS.items():
        try:
            brand = Brand.objects.get(slug=slug)
        except Brand.DoesNotExist:
            continue
        _attach_if_missing(brand, "logo", filename)


def reverse_brand_assets(apps, schema_editor):
    Brand = apps.get_model("brands", "Brand")
    Brand.objects.filter(slug__in=_HERO_ASSETS.keys()).update(hero_image="")
    Brand.objects.filter(slug__in=_LOGO_ASSETS.keys()).update(logo="")


class Migration(migrations.Migration):
    dependencies = [
        ("brands", "0005_populate_hzm_subcategory_descriptions"),
    ]

    operations = [
        migrations.RunPython(attach_brand_assets, reverse_code=reverse_brand_assets),
    ]
