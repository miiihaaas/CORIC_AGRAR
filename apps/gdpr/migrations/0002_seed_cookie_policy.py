"""Story 7.1 — data seed migracija (RunPython reverzibilan) za CookiePolicy.

Kreira singleton red (pk=1) sa Lorem Ipsum placeholder sadržajem PRE prvog deploy-a
(`migrate` je deploy step → pouzdanije od fixture-a; SM-D5). Idempotentno kroz
`get_or_create(pk=1)` — re-run NE kreira pk=2.

VAŽNO (G-2): historical model (`apps.get_model`) NEMA `save()` pk=1 override →
EKSPLICITAN `pk=1` u `get_or_create` kwargs.
VAŽNO (G-3): popuni `_sr` kolone DIREKTNO (`title_sr`/`body_sr`) — modeltranslation
accessor (goli `title=`) nije pouzdan u historical kontekstu; bar `_sr` MORA biti
popunjen da fallback (MODELTRANSLATION_FALLBACK_LANGUAGES=("sr",)) vrati srpski.
VAŽNO (G-11/OQ-1): `effective_date` se NE postavlja → ostaje None (bez fake pravnog
datuma); hu/en se NE seed-uju → oslanjaju se na sr fallback dok biznis ne unese
prevod kroz admin.
"""

from django.db import migrations

# Lorem Ipsum placeholder (sr, pune dijakritike) — biznis menja kroz admin pre/posle deploy-a.
_TITLE_SR = "Politika kolačića"
_BODY_SR = (
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Ova stranica je "
    "privremeni rezervisani sadržaj politike kolačića (placeholder) i biće "
    "zamenjena stvarnim pravnim tekstom kroz administraciju sajta.\n\n"
    "Naš sajt koristi kolačiće (cookies) radi pravilnog funkcionisanja, analitike "
    "i poboljšanja korisničkog iskustva. Pojedinosti o vrstama kolačića, njihovoj "
    "svrsi i načinu upravljanja saglasnošću biće detaljno opisane ovde."
)


def seed_cookie_policy(apps, schema_editor):
    CookiePolicy = apps.get_model("gdpr", "CookiePolicy")
    # G-2: eksplicitan pk=1 (historical model NEMA save() pk=1 override).
    # G-3: popuni _sr kolone DIREKTNO (fallback vraća srpski). G-11: effective_date None.
    CookiePolicy.objects.get_or_create(
        pk=1,
        defaults={
            "title_sr": _TITLE_SR,
            "body_sr": _BODY_SR,
        },
    )


def reverse_seed(apps, schema_editor):
    # QuerySet.delete() — historical model NEMA instance delete() override, pa reverz radi.
    CookiePolicy = apps.get_model("gdpr", "CookiePolicy")
    CookiePolicy.objects.filter(pk=1).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("gdpr", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_cookie_policy, reverse_code=reverse_seed),
    ]
