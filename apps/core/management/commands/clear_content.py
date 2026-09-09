"""DEV/staging komanda za brisanje demo sadrzaja — NIKAD produkcija.

Prati `seed_sample_data`: seed puni demo sadrzaj, ova komanda ga sklanja da bi
prezentacija mogla da krene iz cistog stanja. Par je zamisljen da se vrti vise puta.

ZASTO ORM, A NE `flush` / DROP
------------------------------
`manage.py flush` TRUNCATE-uje SVE tabele, ukljucujuci `auth_user` — panel login bi
nestao. Ova komanda ide iskljucivo kroz ORM nad EKSPLICITNOM listom modela, pa
`django_migrations`, `auth_user`, `auth_group`, `auth_permission` i
`django_content_type` nikad nisu ni dotaknuti. Login je bezbedan PO KONSTRUKCIJI,
ne po paznji onoga ko pokrece komandu.

STA SE BRISE
------------
- Product (+ CASCADE: ProductImage/Variant/Specification/Brochure/Testimonial/Similar)
- Blog: Post, Category, Tag
- SeoMeta redovi koji su pokazivali na gore obrisane objekte (GFK NEMA cascade —
  bez ovoga ostaju siroci koji vise ni na sta ne pokazuju)

STA SE CUVA (i zasto)
---------------------
- Korisnici, grupe, permisije, content types — panel login i RBAC.
- Lead + LeadAttachment — upiti pravih ljudi iz kontakt forme (licni podaci;
  brisanje je poslovna/GDPR odluka, ne uzgredni efekat ciscenja demo sadrzaja).
- Brand, Series, Category, Subcategory — KRITICNO: Jeegee, HZM, Tulip i priključne
  kategorije prave DATA MIGRACIJE (brands/0003, brands/0004). Django ih vodi kao
  primenjene, pa se posle brisanja NE VRACAJU — sajt bi ostao bez kategorija bez
  ocitog nacina da se poprave. `seed_sample_data` pravi samo 3 traktor brenda,
  ne i te.
- SiteSettings, CookiePolicy, Page (pravne strane), Redirect — konfiguracija sajta.
- Proizvodi tulip-mix-6m3 / tulip-mix-8m3 — takodje ih pravi migracija 0004 (sa
  specifikacijama) i pune stranu /sr/mehanizacija/mix-prikolice/. Vidi
  MIGRATION_SEEDED_PRODUCT_SLUGS.

MEDIA
-----
Brisanje `ProductImage` reda NE brise fajl sa diska. Komanda prijavi koliko je
redova obrisano da se zna da u `media/` ostaje smece, ali fajlove NE dira —
brisanje fajlova je nepovratno i ne sme biti uzgredni efekat.
"""

from __future__ import annotations

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.blog.models import Category as BlogCategory
from apps.blog.models import Post
from apps.blog.models import Tag as BlogTag
from apps.products.models import Product
from apps.seo.models import SeoMeta

# Potvrda koju korisnik mora doslovno da otkuca u interaktivnom rezimu.
_CONFIRM_WORD = "OBRISI"

# Proizvodi koje pravi DATA MIGRACIJA brands/0004_seed_hzm_tulip_brands (uz njihove
# ProductSpecification redove). Django tu migraciju vodi kao primenjenu, pa se posle
# brisanja NE VRACAJU — a pune stranu /sr/mehanizacija/mix-prikolice/. Seed komanda ih
# NE pravi (pravi samo `polovni-*` varijante), pa moraju biti izuzeti od brisanja.
# Ako migracija ikad dobije nove modele, dopuni ovu listu (test to zakljucava).
MIGRATION_SEEDED_PRODUCT_SLUGS = ("tulip-mix-6m3", "tulip-mix-8m3")

# Modeli koji se brisu, redom. Blog kategorija/tag idu POSLE Post-a (FK zavisnost).
# Proizvodi imaju filter (izuzimanje migracijskih), ostali brisu sve.
_PURGE_MODELS = (
    ("proizvodi", Product),
    ("blog objave", Post),
    ("blog kategorije", BlogCategory),
    ("blog tagovi", BlogTag),
)


def _purge_qs(model):
    """QuerySet koji se brise za dati model (Product izuzima migracijske slug-ove)."""
    if model is Product:
        return Product.objects.exclude(slug__in=MIGRATION_SEEDED_PRODUCT_SLUGS)
    return model.objects.all()


class Command(BaseCommand):
    help = (
        "Obriši demo sadržaj (proizvodi + blog). Čuva korisnike, lead-ove, "
        "brendove/kategorije i podešavanja sajta. Zabranjeno na produkciji."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--noinput",
            "--no-input",
            action="store_false",
            dest="interactive",
            default=True,
            help="Preskoči interaktivnu potvrdu (za skripte/CI).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="Samo prikaži šta bi bilo obrisano — ništa ne menja.",
        )

    def handle(self, *args, **options):
        # PRVA stvar, pre bilo kakvog citanja/pisanja: produkcija je zabranjena.
        # DEBUG NE razlikuje okruženja — staging takođe ima DEBUG=False (staging.py:8),
        # pa se gleda ime settings modula.
        self._refuse_on_production()

        dry_run = options["dry_run"]
        counts = {label: _purge_qs(model).count() for label, model in _PURGE_MODELS}
        orphan_seo = self._orphan_seometa_qs().count()

        self._print_plan(counts, orphan_seo, dry_run)

        if dry_run:
            self.stdout.write(self.style.WARNING("--dry-run: ništa nije obrisano."))
            return

        if not any(counts.values()) and not orphan_seo:
            self.stdout.write("Nema šta da se briše — sadržaj je već prazan.")
            return

        if options["interactive"] and not self._confirmed():
            raise CommandError("Prekinuto — potvrda nije data. Ništa nije obrisano.")

        deleted = {}
        with transaction.atomic():
            # SeoMeta PRE sadržaja: posle brisanja Product/Post redova GFK više ne
            # razrešava, pa se siročići ne bi mogli pronaći istim upitom.
            deleted["SEO meta"], _ = self._orphan_seometa_qs().delete()
            for label, model in _PURGE_MODELS:
                total, _detail = _purge_qs(model).delete()
                deleted[label] = total

        self.stdout.write(self.style.SUCCESS("clear_content završen."))
        for label, total in deleted.items():
            if total:
                self.stdout.write(f"  {label}: {total} obrisano (uključujući vezane redove)")
        self.stdout.write(
            self.style.WARNING(
                "  NAPOMENA: fajlovi u media/ NISU obrisani — redovi jesu. "
                "Očisti ih ručno ako je disk problem."
            )
        )

    # -- internal helpers -----------------------------------------------------

    def _refuse_on_production(self):
        settings_module = getattr(settings, "SETTINGS_MODULE", "") or ""
        if settings_module.endswith(".production"):
            raise CommandError(
                "clear_content je zabranjen na produkciji "
                f"(DJANGO_SETTINGS_MODULE={settings_module}). "
                "Dozvoljeni su samo lokal i staging — nema --force prekidača."
            )

    def _orphan_seometa_qs(self):
        """SeoMeta redovi vezani za modele koje ova komanda briše.

        GenericForeignKey nema cascade: brisanje Product/Post reda ostavlja SeoMeta
        red koji pokazuje na nepostojeći objekat.
        """
        content_types = ContentType.objects.get_for_models(
            *(model for _label, model in _PURGE_MODELS)
        ).values()
        qs = SeoMeta.objects.filter(content_type__in=list(content_types))
        # Migracijski proizvodi prezivljavaju — njihov SeoMeta NIJE siroce.
        survivor_ids = list(
            Product.objects.filter(slug__in=MIGRATION_SEEDED_PRODUCT_SLUGS).values_list(
                "pk", flat=True
            )
        )
        if survivor_ids:
            product_ct = ContentType.objects.get_for_model(Product)
            qs = qs.exclude(content_type=product_ct, object_id__in=survivor_ids)
        return qs

    def _print_plan(self, counts, orphan_seo, dry_run):
        header = "Plan brisanja (dry-run)" if dry_run else "Biće obrisano"
        self.stdout.write(self.style.WARNING(f"{header}:"))
        for label, total in counts.items():
            self.stdout.write(f"  {label}: {total}")
        self.stdout.write(f"  SEO meta (siročići): {orphan_seo}")
        self.stdout.write("Ostaje netaknuto: korisnici, lead-ovi, brendovi/kategorije, podešavanja.")

    def _confirmed(self) -> bool:
        self.stdout.write(
            self.style.WARNING(f"Za potvrdu otkucaj {_CONFIRM_WORD} (bilo šta drugo prekida): ")
        )
        return input().strip() == _CONFIRM_WORD
