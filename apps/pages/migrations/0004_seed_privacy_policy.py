"""Story 7.4 — DATA seed migracija: kreira `Page(slug="politika-privatnosti")`.

„Postoji pre prvog deploy-a" (epics.md:1048) → data migracija (migrate = deploy
step). Seed-uje SAMO `_sr` (pune dijakritike); `_hu/_en` ostaju prazni →
modeltranslation fallback na sr (MODELTRANSLATION_FALLBACK_LANGUAGES=("sr",)).

⚠️ NE seed-uje `politika-kolacica` (SM-D1/AC2) — gdpr.CookiePolicy (7-1) je
AUTORITATIVAN za politiku kolačića (drugi izvor istine = zabranjeno).

Idempotentno kroz get_or_create(slug=...) (NIJE singleton pk=1 — Page je običan
model; G-8). reverse_code briše privacy red (project-context.md:227).

⚠️ RISK-1 (NASLEĐEN iz 7-1) — `body_sr` je PLACEHOLDER (G-15): pravi pravni
tekst MORA uneti biznis/pravnik PRE go-live (Mihas legal sign-off). Marker
sprečava da neko deploy-uje Lorem Ipsum kao pravu politiku privatnosti.
"""

from django.db import migrations

# TODO(RISK-1): placeholder privatnost tekst — zameniti pravim pravnim tekstom
# (biznis/pravnik) PRE go-live; Mihas legal sign-off (nasleđeno iz 7-1).
_BODY_SR = (
    "[PLACEHOLDER — pravni tekst MORA uneti biznis/pravnik pre go-live "
    "(RISK-1, Mihas sign-off)]\n\n"
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Ova politika "
    "privatnosti je privremeni rezervisani sadržaj. Ovde će biti opisani podaci "
    "koje prikupljamo, pravni osnov obrade, prava korisnika, period čuvanja "
    "podataka i kontakt zadužen za zaštitu podataka.\n\n"
    "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Konačan "
    "tekst zameniće ovaj placeholder pre puštanja sajta u rad."
)


def seed_privacy_policy(apps, schema_editor):
    Page = apps.get_model("pages", "Page")
    # G-2: popuni _sr kolone DIREKTNO (historical model nema goli accessor logiku).
    Page.objects.get_or_create(
        slug="politika-privatnosti",
        defaults={
            "title": "Politika privatnosti",
            "title_sr": "Politika privatnosti",
            "body": _BODY_SR,
            "body_sr": _BODY_SR,
        },
    )


def reverse_seed(apps, schema_editor):
    Page = apps.get_model("pages", "Page")
    Page.objects.filter(slug="politika-privatnosti").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("pages", "0003_page"),
    ]

    operations = [
        migrations.RunPython(seed_privacy_policy, reverse_code=reverse_seed),
    ]
