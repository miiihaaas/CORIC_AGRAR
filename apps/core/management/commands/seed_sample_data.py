"""Story 9-7 — DEV-only idempotentan seed command za demo content (traktori + mehanizacija + blog).

Puni bazu realnim demo sadržajem tako da lokalni dev / staging demo ima realan content i da
Story 9-8 Playwright E2E može da cilja determinističke, unapred poznate slug-ove.

KARAKTERISTIKE:
- DEV-only (TVRD production guard, SM-D2): odbija izvršavanje sa ``DEBUG=False`` bez ``--force``.
- Aditivan (SM-D5): referencira postojeće migration-seed-ovane brendove/kategorije/proizvode kroz
  ``get_or_create`` — NE duplira ih.
- Idempotentan (SM-D3): svaki objekat kroz ``get_or_create`` po EKSPLICITNOM ``slug`` (ili ``pk=1``
  za ``SiteSettings``) lookup ključu; ``slug`` se NIKAD ne izvodi auto-derivacijom unutar ``defaults``.
- Modeltranslation (SM-D4): postavlja i bazni accessor i ``_sr`` kolonu u ISTOM ``defaults`` dict-u;
  pune srpske dijakritike u svim user-facing string-ovima; ASCII slug-ovi.
- Atomicity: seeding je u ``transaction.atomic()``; SUCCESS sažetak na stdout TEK posle commit-a.

ADMIN / KREDENCIJALI (SM-D7, CRITICAL): ovaj command NE seed-uje nikakve kredencijale i NE pravi
superusera. Story 9-8 MORA da provisionuje svog SOPSTVENOG DEV-only superusera kroz
``python manage.py createsuperuser --noinput`` (env-driven ``DJANGO_SUPERUSER_*``).
**Admin login putanja je ``/admin-coric/``** (NE ``/admin/``; Story 8-1 premestila admin van i18n).

ARHITEKTURNA GRANICA: ``apps/core`` po pravilu ne importuje domain app-ove — ALI ovo je
operativni/management (data-bootstrap) sloj, NE runtime core kod, pa direktni import domain modela je
svestan i dozvoljen izuzetak (mirror data-migration seed-ova u ``apps/brands/migrations``). SM-D1.
"""

from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.blog.models import Category as BlogCategory
from apps.blog.models import Post
from apps.blog.models import Tag as BlogTag
from apps.brands.models import Brand
from apps.brands.models import Category as BrandCategory
from apps.pages.models import SiteSettings
from apps.products.models import Product, ProductSpecification

# =============================================================================
# Seed manifest (FINALNE vrednosti — verbatim iz story manifesta + interface contract)
# =============================================================================

_TRAKTORI_CATEGORY = {
    "slug": "traktori",
    "name": "Traktori",
    "is_for": "traktori",
    "display_order": 10,
    "description": "Poljoprivredni traktori — nova i polovna mehanizacija za sve veličine gazdinstva.",
}

_TRACTOR_BRANDS = [
    {
        "slug": "wuzheng",
        "name": "Wuzheng",
        "description": "Pouzdani traktori za male i srednje poljoprivredne posede.",
        "slogan": "Snaga koja traje.",
    },
    {
        "slug": "agri-tracking",
        "name": "Agri Tracking",
        "description": "Moderni traktori sa naprednom hidraulikom i klimatizovanom kabinom.",
        "slogan": "Tehnologija u službi zemlje.",
    },
    {
        "slug": "saillong",
        "name": "Saillong",
        "description": "Robusni traktori velike snage za zahtevne ratarske radove.",
        "slogan": "Stvoreni za teren.",
    },
]

# NOVI traktori (condition="new", is_published=True, status="published")
_NEW_TRACTORS = [
    {
        "slug": "agri-tracking-tb804",
        "brand_slug": "agri-tracking",
        "name": "Agri Tracking TB804",
        "description": "Univerzalni traktor od 80 KS sa klimatizovanom kabinom i hidrauličnom dizalicom.",
        "key_features": [
            "Klimatizovana kabina",
            "Hidraulična dizalica",
            "Robusna konstrukcija",
        ],
        "horse_power": 80,
        "year": 2024,
        "price_eur": Decimal("28500.00"),
    },
    {
        "slug": "wuzheng-wz504",
        "brand_slug": "wuzheng",
        "name": "Wuzheng WZ504",
        "description": "Kompaktan traktor od 50 KS, idealan za voćnjake i manja gazdinstva.",
        "key_features": [
            "Štedljiv motor",
            "Laka upravljivost",
            "Pristupačna cena",
        ],
        "horse_power": 50,
        "year": 2023,
        "price_eur": Decimal("19900.00"),
    },
    {
        "slug": "saillong-sl904",
        "brand_slug": "saillong",
        "name": "Saillong SL904",
        "description": "Snažan traktor od 90 KS za najzahtevnije ratarske i transportne radove.",
        "key_features": [
            "Velika vučna snaga",
            "Ojačana transmisija",
            "Komforna kabina",
        ],
        "horse_power": 90,
        "year": 2025,
        "price_eur": Decimal("32400.00"),
    },
]

# Specifikacije za headline traktor (obogaćuju UJ-1 detail stranu)
_HEADLINE_SPECS = [
    {"section": "motor", "key": "Snaga motora", "value": "80 KS", "order": 0},
    {"section": "transmisija", "key": "Broj brzina", "value": "16+8", "order": 1},
    {"section": "hidraulika", "key": "Nosivost dizalice", "value": "2600 kg", "order": 2},
]

# POLOVNE mašine (condition="used", is_published=True, status="published"); sve year <= 2022
_USED_MACHINES = [
    {
        "slug": "polovni-traktor-agri-tracking-tb804",
        "brand_slug": "agri-tracking",
        "name": "Polovni traktor Agri Tracking TB804",
        "description": "Očuvan polovni traktor od 75 KS sa redovno servisiranim motorom.",
        "key_features": ["Redovno servisiran", "Očuvana kabina", "Spreman za rad"],
        "horse_power": 75,
        "year": 2022,
        "price_eur": Decimal("18500.00"),
    },
    {
        "slug": "polovni-tulip-mix-6m3",
        "brand_slug": "tulip",
        "name": "Polovni Tulip MIX 6 m³",
        "description": "Polovni rasipač stajnjaka zapremine 6 m³ u dobrom stanju.",
        "key_features": ["Zapremina 6 m³", "Pocinkovano kućište", "Robusna konstrukcija"],
        "horse_power": 35,
        "year": 2018,
        "price_eur": Decimal("4200.00"),
    },
    {
        "slug": "polovni-hzm-utovarivac",
        "brand_slug": "hzm",
        "name": "Polovni HZM utovarivač",
        "description": "Polovni čeoni utovarivač od 65 KS sa očuvanom hidraulikom.",
        "key_features": ["Očuvana hidraulika", "Snažan motor", "Pouzdan rad"],
        "horse_power": 65,
        "year": 2020,
        "price_eur": Decimal("15900.00"),
    },
    {
        "slug": "polovni-wuzheng-wz504",
        "brand_slug": "wuzheng",
        "name": "Polovni Wuzheng WZ504",
        "description": "Kompaktan polovni traktor od 45 KS, štedljiv i jednostavan za održavanje.",
        "key_features": ["Štedljiv motor", "Niski sati rada", "Jeftino održavanje"],
        "horse_power": 45,
        "year": 2019,
        "price_eur": Decimal("9800.00"),
    },
    {
        "slug": "polovni-saillong-sl904",
        "brand_slug": "saillong",
        "name": "Polovni Saillong SL904",
        "description": "Polovni traktor od 55 KS, dobro održavan i spreman za sezonu.",
        "key_features": ["Dobro održavan", "Ojačana šasija", "Komforna kabina"],
        "horse_power": 55,
        "year": 2021,
        "price_eur": Decimal("13400.00"),
    },
]

_BLOG_CATEGORY = {
    "slug": "ratarstvo",
    "name": "Ratarstvo",
    "description": "Saveti i novosti iz oblasti ratarske proizvodnje i obrade zemljišta.",
}

_BLOG_TAG = {
    "slug": "zetva",
    "name": "Žetva",
}

_BLOG_POSTS = [
    {
        "slug": "pet-saveta-za-prolecnu-setvu",
        "title": "Pet saveta za prolećnu setvu",
        "perex": "Kako da pripremite njivu i mašine za uspešnu prolećnu setvu.",
        "body": (
            "Prolećna setva zahteva pažljivu pripremu zemljišta i ispravno podešene mašine. "
            "U ovom tekstu donosimo pet praktičnih saveta koji će vam pomoći da povećate prinos."
        ),
    },
    {
        "slug": "kako-odabrati-traktor",
        "title": "Kako odabrati traktor za vaše gazdinstvo",
        "perex": "Snaga, transmisija i hidraulika — na šta obratiti pažnju pri kupovini.",
        "body": (
            "Odabir pravog traktora zavisi od veličine poseda i vrste radova. "
            "Objašnjavamo razliku u konjskim snagama i zašto je kvalitetna hidraulika ključna."
        ),
    },
    {
        "slug": "odrzavanje-mehanizacije-pred-zetvu",
        "title": "Održavanje mehanizacije pred žetvu",
        "perex": "Redovan servis pred sezonu štedi vreme i sprečava skupe kvarove.",
        "body": (
            "Pred žetvu je neophodno proveriti remenje, ležajeve i hidraulične vodove. "
            "Donosimo kratku čeklistu održavanja koja produžava vek vaše mehanizacije."
        ),
    },
]


def _set_translatable(defaults, **fields):
    """Postavi i bazni accessor i ``_sr`` kolonu u ISTI defaults dict (SM-D4 / mirror 0004)."""
    for key, value in fields.items():
        defaults[key] = value
        defaults[f"{key}_sr"] = value
    return defaults


class Command(BaseCommand):
    help = (
        "DEV-only idempotentan seed demo sadržaja (TRAKTORI strana + polovne mašine + blog). "
        "Odbija izvršavanje sa DEBUG=False bez --force (SM-D2). NE seed-uje kredencijale i NE "
        "pravi superusera (SM-D7) — 9-8 provisionuje svog DEV-only usera kroz "
        "`createsuperuser --noinput`. Admin login je na /admin-coric/."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            default=False,
            help="Zaobiđi production guard i izvrši seed čak i sa DEBUG=False (DEV/staging samo).",
        )

    def handle(self, *args, **options):
        # SM-D2: production guard je PRVO što handle() radi, PRE bilo kakvog DB write-a.
        if not settings.DEBUG and not options["force"]:
            raise CommandError(
                "seed_sample_data je DEV-only; odbijam izvršavanje sa DEBUG=False bez --force"
            )

        counters: dict[str, int] = {}

        with transaction.atomic():
            self._seed(counters)

        # Sažetak TEK posle uspešnog commit-a (Atomicity Dev Note).
        self.stdout.write(self.style.SUCCESS("seed_sample_data završen — demo content spreman."))
        created_any = False
        for label, count in counters.items():
            if count:
                self.stdout.write(f"  {label}: {count} kreirano (postojeći preskočeni)")
                created_any = True
        if not created_any:
            self.stdout.write("  ništa novo — svi objekti su već postojali (idempotentno).")

    # -- internal helpers -----------------------------------------------------

    def _seed(self, counters):
        brands = self._seed_brands(counters)
        self._seed_traktori_category(counters)
        self._seed_products(_NEW_TRACTORS, "new", brands, counters, "novi traktori")
        self._seed_products(_USED_MACHINES, "used", brands, counters, "polovne mašine")
        self._seed_specs(counters)
        self._seed_blog(counters)
        self._seed_sitesettings(counters)

    def _bump(self, counters, label, created):
        counters.setdefault(label, 0)
        if created:
            counters[label] += 1

    def _seed_brands(self, counters):
        """Vrati mapu slug -> Brand za sve traktor brendove + referencirane postojeće brendove."""
        brands: dict[str, Brand] = {}
        for data in _TRACTOR_BRANDS:
            defaults = _set_translatable(
                {"is_coming_soon": False, "statistics": []},
                name=data["name"],
                description=data["description"],
                slogan=data["slogan"],
            )
            brand, created = Brand.objects.get_or_create(slug=data["slug"], defaults=defaults)
            self._bump(counters, "brendovi", created)
            brands[data["slug"]] = brand

        # Postojeći migration-seed-ovani brendovi koje polovne mašine referenciraju (AC2 — NE dupliraj).
        for slug in ("tulip", "hzm"):
            brand, created = Brand.objects.get_or_create(
                slug=slug,
                defaults=_set_translatable({}, name=slug.upper()),
            )
            self._bump(counters, "brendovi", created)
            brands[slug] = brand
        return brands

    def _seed_traktori_category(self, counters):
        defaults = _set_translatable(
            {
                "is_for": _TRAKTORI_CATEGORY["is_for"],
                "display_order": _TRAKTORI_CATEGORY["display_order"],
            },
            name=_TRAKTORI_CATEGORY["name"],
            description=_TRAKTORI_CATEGORY["description"],
        )
        _, created = BrandCategory.objects.get_or_create(
            slug=_TRAKTORI_CATEGORY["slug"], defaults=defaults
        )
        self._bump(counters, "kategorije", created)

    def _seed_products(self, items, condition, brands, counters, label):
        for data in items:
            defaults = _set_translatable(
                {
                    "brand": brands[data["brand_slug"]],
                    "subcategory": None,
                    "horse_power": data["horse_power"],
                    "year": data["year"],
                    "price_eur": data["price_eur"],
                    "condition": condition,
                    "status": "published",
                    "is_published": True,
                },
                name=data["name"],
                description=data["description"],
                key_features=data["key_features"],
            )
            _, created = Product.objects.get_or_create(slug=data["slug"], defaults=defaults)
            self._bump(counters, label, created)

    def _seed_specs(self, counters):
        product = Product.objects.get(slug="agri-tracking-tb804")
        for spec in _HEADLINE_SPECS:
            # ``key`` je lookup ključ (vidi get_or_create ispod) — ne dupliraj ga u defaults.
            # Bazni ``key`` accessor već čita ``key_sr`` (modeltranslation); postavi samo ``key_sr``.
            defaults = _set_translatable(
                {"order": spec["order"], "key_sr": spec["key"]},
                value=spec["value"],
            )
            _, created = ProductSpecification.objects.get_or_create(
                product=product,
                section=spec["section"],
                key=spec["key"],
                defaults=defaults,
            )
            self._bump(counters, "specifikacije", created)

    def _seed_blog(self, counters):
        cat_defaults = _set_translatable(
            {},
            name=_BLOG_CATEGORY["name"],
            description=_BLOG_CATEGORY["description"],
        )
        category, created = BlogCategory.objects.get_or_create(
            slug=_BLOG_CATEGORY["slug"], defaults=cat_defaults
        )
        self._bump(counters, "blog kategorije", created)

        tag, created = BlogTag.objects.get_or_create(
            slug=_BLOG_TAG["slug"],
            defaults=_set_translatable({}, name=_BLOG_TAG["name"]),
        )
        self._bump(counters, "blog tagovi", created)

        for data in _BLOG_POSTS:
            defaults = _set_translatable(
                {
                    "category": category,
                    "status": "published",
                    "published_at": timezone.now(),
                    "author": None,
                },
                title=data["title"],
                perex=data["perex"],
                body=data["body"],
            )
            post, created = Post.objects.get_or_create(slug=data["slug"], defaults=defaults)
            self._bump(counters, "blog objave", created)
            # G-3: M2M tek posle save() (post sad ima PK).
            post.tags.add(tag)

    def _seed_sitesettings(self, counters):
        # SM-D8: defanzivno osiguraj singleton; NE dupliraj pages/0002 auto-seed.
        _, created = SiteSettings.objects.get_or_create(pk=1)
        self._bump(counters, "site settings", created)
