"""Story 3.4 — DATA seed migracija: kreira jedinu SiteSettings(pk=1) instancu.

Seed-uje TRENUTNE hardkodovane vrednosti (iz _contact_info.html/footer/top-header) tako
da sajt nastavi da renderuje bez ručnog admin koraka posle deploy-a (epics.md:759 fixture).

Seed politika (SM-D4): popunjava SAMO _sr (puni dijakritik). _hu/_en SMEJU ostati prazni —
modeltranslation fallback-uje na sr (MODELTRANSLATION_FALLBACK_LANGUAGES=("sr",)). Adresa
hu/en su identični sr (adresa je ista u svim lokalima — nije lažan prevod).

Idempotentno kroz update_or_create(pk=1). reverse_code briše pk=1 (project-context.md:227).
"""

from django.db import migrations

# Čitljiv multi-line format — render kao <ul>/<li> kroz |splitlines filter (SM-D10).
_WORKING_HOURS = "Ponedeljak–Petak: 08–16h\nSubota: 08–13h\nNedelja: zatvoreno"


def seed_sitesettings(apps, schema_editor):
    SiteSettings = apps.get_model("pages", "SiteSettings")
    SiteSettings.objects.update_or_create(
        pk=1,
        defaults={
            "company_name": "Ćorić Agrar",
            "slogan": "Prijatelj koji razume zemlju!",
            "slogan_sr": "Prijatelj koji razume zemlju!",
            "address": "Vojvođanska 1, Basaid, Srbija",
            "address_sr": "Vojvođanska 1, Basaid, Srbija",
            "address_hu": "Vojvođanska 1, Basaid, Srbija",
            "address_en": "Vojvođanska 1, Basaid, Srbija",
            "phone_sales": "+381 230 468 168",
            # TODO(OQ-1): placeholder — biznis popunjava realne vrednosti pre go-live
            "phone_service": "+381 XXX XXX XXX",
            "email": "prodaja@coricagrar.rs",
            "working_hours": _WORKING_HOURS,
            "working_hours_sr": _WORKING_HOURS,
            # TODO(OQ-1): placeholder — biznis popunjava realne vrednosti pre go-live
            "social_facebook": "",
            "social_instagram": "",
        },
    )


def reverse_seed(apps, schema_editor):
    SiteSettings = apps.get_model("pages", "SiteSettings")
    SiteSettings.objects.filter(pk=1).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("pages", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_sitesettings, reverse_code=reverse_seed),
    ]
