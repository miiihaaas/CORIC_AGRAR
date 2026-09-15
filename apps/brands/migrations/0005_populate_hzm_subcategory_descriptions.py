"""Data migracija — popuni description za HZM radne-mašine potkategorije.

0004 ih je seed-ovao sa description="" (sadržaj odložen). Homepage _home_radne_masine.html
uslovno renderuje <p class="coric-category-card__description"> SAMO kad sub.description
postoji — sa praznim poljem taj blok se u potpunosti ne prikazuje (HIDE-WHEN-EMPTY, isti
obrazac kao social linkovi). Ovde upisujemo kratke generičke opise (bez konkretnih
tehničkih specifikacija koje bi zahtevale biznis potvrdu — mirror OQ-4 oprez iz 0004).
Idempotentna: update_or_create po (category, slug) paru; reverse vraća na "".
"""

from django.db import migrations

_DESCRIPTIONS = {
    "mini-utovarivaci": (
        "Kompaktni i okretni utovarivači za rad u skučenim prostorima, sa širokim "
        "izborom priključaka za svaki zadatak na imanju."
    ),
    "utovarivaci-bez-teleskopa": (
        "Snažni utovarivači fiksne konstrukcije za svakodnevni utovar i transport "
        "materijala na farmi i gradilištu."
    ),
    "teleskopski-utovarivaci": (
        "Teleskopska ruka omogućava veći domet i visinu dizanja — idealno za utovar, "
        "slaganje i rad na visini."
    ),
    "telehendleri": (
        "Višenamenske mašine koje spajaju utovarivač, dizalicu i viljuškar u jednom — "
        "za utovar, transport i rad na visini."
    ),
}


def populate_descriptions(apps, schema_editor):
    Subcategory = apps.get_model("brands", "Subcategory")
    for slug, text in _DESCRIPTIONS.items():
        Subcategory.objects.filter(
            category__slug="radne-masine", slug=slug
        ).update(description=text, description_sr=text)


def reverse_descriptions(apps, schema_editor):
    Subcategory = apps.get_model("brands", "Subcategory")
    Subcategory.objects.filter(
        category__slug="radne-masine", slug__in=_DESCRIPTIONS.keys()
    ).update(description="", description_sr="")


class Migration(migrations.Migration):
    dependencies = [
        ("brands", "0004_seed_hzm_tulip_brands"),
    ]

    operations = [
        migrations.RunPython(populate_descriptions, reverse_code=reverse_descriptions),
    ]
