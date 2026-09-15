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

PROFIL 2 PROŠIRENJE (2026-09-09): manifest shape je proširen (Series, više Category/Subcategory,
po-proizvod ``subcategory_slug``/``series_slug``/``images``/``specs``, ProductBrochure,
ProductTestimonial, ProductSimilar) da profil 2 (kurirani "1:1 snapshot lokalne baze" manifest,
vidi ``_seed_profiles/profile2.py``) može da referencira/pravi sve entitete koje baza sadrži.
Svako novo polje je OPCIONO (``.get()`` sa fallback-om na staro ponašanje) — PROFILE_1 shape i
DB pozivi ostaju bit-za-bit identični (E2E cilja tačne slugove, ne sme da se pomeri). Fajlovi
(slike/PDF) se NIKAD ne pišu u ``defaults`` dict get_or_create-a (FileField.save() mora da pozove
storage). Brand.logo/hero_image i Product.main_image se prilažu i na VEĆ POSTOJEĆEM redu (kad je
polje prazno — ``_attach_file_if_missing``), jer profil 1 taj red kreira BEZ tih polja; profil 2
mora da ih dopuni na istom redu, ne samo na novokreiranom (isti red se deli između profila,
npr. ``agri-tracking``/``agri-tracking-tb804``). Ostali fajlovi (galerija, brošure, testimonial
foto) prilažu se TEK kad je red NOVO kreiran (``_attach_file``) — ti redovi ne postoje u profilu 1,
pa "postojeći red bez fajla" scenario tu ne nastaje.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.blog.models import Post
from apps.blog.models import Tag as BlogTag
from apps.brands.models import Brand
from apps.brands.models import Category as BrandCategory
from apps.brands.models import Series, Subcategory
from apps.pages.models import SiteSettings
from apps.products.models import (
    Product,
    ProductBrochure,
    ProductImage,
    ProductSimilar,
    ProductSpecification,
    ProductTestimonial,
)

# Profil 2 seed asset-i (slike/PDF stvarno referencirani iz baze, optimizovani, commit-ovani u repo).
# Vidi ``_seed_profiles/assets/`` i ``ops/seed/generate_profile2_manifest.py`` (generator).
_SEED_ASSETS_DIR = Path(__file__).resolve().parent / "_seed_profiles" / "assets"

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
    {
        "section": "hidraulika",
        "key": "Nosivost dizalice",
        "value": "2600 kg",
        "order": 2,
    },
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
        "key_features": [
            "Zapremina 6 m³",
            "Pocinkovano kućište",
            "Robusna konstrukcija",
        ],
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


# =============================================================================
# Profili (2026-09-08) — `--profile` bira KOJI manifest se seed-uje.
# =============================================================================
# Profil 1 je ISTORIJSKI manifest (Story 9-7) i mora ostati funkcionalno nepromenjen:
# `seed_e2e_data` + Playwright E2E ciljaju tacne slug-ove (agri-tracking-tb804,
# wuzheng-wz504, saillong-sl904). Profil 2 je kurirani demo sadrzaj koji se puni
# odvojeno (vidi _seed_profiles/profile2.py) da ovaj fajl ne raste.
#
# Manifest je CIST PODATAK — seed logika (get_or_create po eksplicitnom slug-u,
# modeltranslation _sr kolone, counters) je zajednicka za sve profile.
PROFILE_1 = {
    "tractor_brands": _TRACTOR_BRANDS,
    # Migration-seed-ovani brendovi koje polovne masine referenciraju (AC2 — NE dupliraj).
    "referenced_brand_slugs": ("tulip", "hzm"),
    "traktori_category": _TRAKTORI_CATEGORY,
    "new_tractors": _NEW_TRACTORS,
    "used_machines": _USED_MACHINES,
    "headline_specs": {
        "product_slug": "agri-tracking-tb804",
        "specs": _HEADLINE_SPECS,
    },
    "blog": {
        "tag": _BLOG_TAG,
        "posts": _BLOG_POSTS,
    },
}


def _load_manifest(profile: str) -> dict:
    """Vrati manifest za dati profil. Profil 2 se importuje LENJO (fail-loud ako fali)."""
    if profile == "1":
        return PROFILE_1
    from ._seed_profiles.profile2 import PROFILE_2

    return PROFILE_2


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
        parser.add_argument(
            "--profile",
            choices=["1", "2"],
            default="1",
            help=(
                "Koji manifest demo sadržaja seed-ovati. 1 = istorijski Story 9-7 manifest "
                "(default; E2E zavisi od njega). 2 = kurirani demo sadržaj."
            ),
        )

    def handle(self, *args, **options):
        # SM-D2: production guard je PRVO što handle() radi, PRE bilo kakvog DB write-a.
        if not settings.DEBUG and not options["force"]:
            raise CommandError(
                "seed_sample_data je DEV-only; odbijam izvršavanje sa DEBUG=False bez --force"
            )

        manifest = _load_manifest(options["profile"])
        counters: dict[str, int] = {}

        with transaction.atomic():
            self._seed(counters, manifest)

        # Sažetak TEK posle uspešnog commit-a (Atomicity Dev Note).
        self.stdout.write(
            self.style.SUCCESS("seed_sample_data završen — demo content spreman.")
        )
        created_any = False
        for label, count in counters.items():
            if count:
                self.stdout.write(f"  {label}: {count} kreirano (postojeći preskočeni)")
                created_any = True
        if not created_any:
            self.stdout.write(
                "  ništa novo — svi objekti su već postojali (idempotentno)."
            )

    # -- internal helpers -----------------------------------------------------

    def _seed(self, counters, manifest):
        # Prazna sekcija = profil je ne pokriva -> preskoci je bez greske. Bez ovoga bi
        # delimicno popunjen profil (npr. proizvodi bez bloga) rusio ceo seed.
        brands = self._seed_brands(counters, manifest)
        categories = self._seed_categories(counters, manifest)
        subcategories = self._seed_subcategories(counters, manifest, categories)
        series_map = self._seed_series(counters, manifest, brands)
        self._seed_products(
            manifest.get("new_tractors", []),
            "new",
            brands,
            counters,
            "novi traktori",
            subcategories=subcategories,
            series_map=series_map,
        )
        self._seed_products(
            manifest.get("used_machines", []),
            "used",
            brands,
            counters,
            "polovne mašine",
            subcategories=subcategories,
            series_map=series_map,
        )
        self._seed_specs(counters, manifest.get("headline_specs"))
        self._seed_brochures(counters, manifest.get("brochures", []))
        self._seed_testimonials(counters, manifest.get("testimonials", []))
        self._seed_similar(counters, manifest.get("similar", []))
        self._seed_blog(counters, manifest.get("blog"))
        self._seed_sitesettings(counters)

    def _bump(self, counters, label, created):
        counters.setdefault(label, 0)
        if created:
            counters[label] += 1

    def _seed_brands(self, counters, manifest):
        """Vrati mapu slug -> Brand za sve traktor brendove + referencirane postojeće brendove."""
        brands: dict[str, Brand] = {}
        for data in manifest.get("tractor_brands", []):
            base = {"is_coming_soon": False, "statistics": data.get("statistics", [])}
            if data.get("brand_color"):
                base["brand_color"] = data["brand_color"]
            defaults = _set_translatable(
                base,
                name=data["name"],
                description=data["description"],
                slogan=data["slogan"],
            )
            brand, created = Brand.objects.get_or_create(
                slug=data["slug"], defaults=defaults
            )
            self._bump(counters, "brendovi", created)
            if not created:
                # get_or_create ignoriše `defaults` na već postojećem redu (isti "profil 1
                # kreirao BEZ ovog polja, profil 2 dopunjuje" slučaj kao logo/hero_image —
                # vidi _attach_file_if_missing docstring). `statistics`/`brand_color` su
                # JSON/char polja (ne FileField), pa se ovde backfill-uju direktno umesto
                # kroz storage .save().
                update_fields = []
                if data.get("statistics") and not brand.statistics:
                    brand.statistics = data["statistics"]
                    update_fields.append("statistics")
                if data.get("brand_color") and not brand.brand_color:
                    brand.brand_color = data["brand_color"]
                    update_fields.append("brand_color")
                if update_fields:
                    brand.save(update_fields=update_fields)
            if data.get("logo_asset"):
                self._attach_file_if_missing(
                    brand, "logo", ("brands", data["logo_asset"])
                )
            if data.get("hero_image_asset"):
                self._attach_file_if_missing(
                    brand, "hero_image", ("brands", data["hero_image_asset"])
                )
            if data.get("catalog_pdf_asset"):
                self._attach_file_if_missing(
                    brand, "catalog_pdf", ("brands", data["catalog_pdf_asset"])
                )
            brands[data["slug"]] = brand

        # Postojeći migration-seed-ovani brendovi koje polovne mašine referenciraju (AC2 — NE dupliraj).
        for slug in manifest.get("referenced_brand_slugs", ()):
            brand, created = Brand.objects.get_or_create(
                slug=slug,
                defaults=_set_translatable({}, name=slug.upper()),
            )
            self._bump(counters, "brendovi", created)
            brands[slug] = brand
        return brands

    def _seed_categories(self, counters, manifest):
        """Vrati mapu slug -> Category: manuelna traktori kategorija + referencirane migracijske.

        Zamenjuje stari ``_seed_traktori_category`` (koji nije vraćao ništa) — profil 2 mora da
        razreši ``subcategory_slug`` FK-ove i za migracijske kategorije (mehanizacija), pa metoda
        vraća mapu umesto da samo kreira. Ponašanje za profil 1 (samo ``traktori_category``,
        bez ``referenced_category_slugs``) je funkcionalno identično starom kodu.
        """
        categories: dict[str, BrandCategory] = {}
        category = manifest.get("traktori_category")
        if category:
            defaults = _set_translatable(
                {
                    "is_for": category["is_for"],
                    "display_order": category["display_order"],
                },
                name=category["name"],
                description=category["description"],
            )
            obj, created = BrandCategory.objects.get_or_create(
                slug=category["slug"], defaults=defaults
            )
            self._bump(counters, "kategorije", created)
            categories[category["slug"]] = obj

        # Postojeće migration-seed-ovane kategorije (mehanizacija) koje profil 2 proizvodi
        # referenciraju kroz subcategory_slug — NE dupliraj (mirror referenced_brand_slugs).
        for slug in manifest.get("referenced_category_slugs", ()):
            obj, created = BrandCategory.objects.get_or_create(
                slug=slug,
                defaults=_set_translatable({"is_for": "mehanizacija"}, name=slug),
            )
            self._bump(counters, "kategorije", created)
            categories[slug] = obj
        return categories

    def _seed_subcategories(self, counters, manifest, categories):
        """Vrati mapu slug -> Subcategory. Podržava i manuelne i referencirane (migracijske).

        NAPOMENA: mapa je flat po ``slug`` (ne po (category, slug) paru) — dovoljno za trenutni
        manifest jer su svi subcategory slug-ovi globalno distinktni. Lista MORA imati parent-e
        pre dece (top-down redosled) ako ikad naraste iznad 1 nivoa dubine.
        """
        subcategories: dict[str, Subcategory] = {}
        for data in manifest.get("subcategories", []):
            category = categories[data["category_slug"]]
            parent = (
                subcategories.get(data["parent_slug"])
                if data.get("parent_slug")
                else None
            )
            defaults = _set_translatable(
                {
                    "icon": data.get("icon", ""),
                    "display_order": data.get("display_order", 0),
                },
                name=data["name"],
                description=data.get("description", ""),
            )
            obj, created = Subcategory.objects.get_or_create(
                category=category, parent=parent, slug=data["slug"], defaults=defaults
            )
            self._bump(counters, "potkategorije", created)
            subcategories[data["slug"]] = obj
        return subcategories

    def _seed_series(self, counters, manifest, brands):
        """Vrati mapu (brand_slug, slug) -> Series."""
        series_map: dict[tuple[str, str], Series] = {}
        for data in manifest.get("series", []):
            brand = brands[data["brand_slug"]]
            defaults = _set_translatable(
                {
                    "layout_mode": data.get("layout_mode", Series.LayoutMode.GRID),
                    "display_order": data.get("display_order", 0),
                },
                name=data["name"],
                description=data.get("description", ""),
            )
            obj, created = Series.objects.get_or_create(
                brand=brand, slug=data["slug"], defaults=defaults
            )
            self._bump(counters, "serije", created)
            series_map[(data["brand_slug"], data["slug"])] = obj
        return series_map

    def _seed_products(
        self,
        items,
        condition,
        brands,
        counters,
        label,
        subcategories=None,
        series_map=None,
    ):
        subcategories = subcategories or {}
        series_map = series_map or {}
        for data in items:
            subcategory_slug = data.get("subcategory_slug")
            series_slug = data.get("series_slug")
            defaults = _set_translatable(
                {
                    "brand": brands[data["brand_slug"]],
                    "subcategory": subcategories[subcategory_slug]
                    if subcategory_slug
                    else None,
                    "series": series_map[(data["brand_slug"], series_slug)]
                    if series_slug
                    else None,
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
            product, created = Product.objects.get_or_create(
                slug=data["slug"], defaults=defaults
            )
            self._bump(counters, label, created)
            if data.get("main_image_asset"):
                self._attach_file_if_missing(
                    product,
                    "main_image",
                    ("products", "main", data["main_image_asset"]),
                )
            for img in data.get("images", []):
                self._seed_product_image(counters, product, img)
            for spec in data.get("specs", []):
                self._seed_product_spec(counters, product, spec)

    def _seed_product_image(self, counters, product, img):
        obj, created = ProductImage.objects.get_or_create(
            product=product,
            order=img["order"],
            defaults=_set_translatable({}, alt_text=img.get("alt_text", "")),
        )
        self._bump(counters, "slike proizvoda", created)
        if created:
            self._attach_file(obj, "image", ("products", "gallery", img["asset"]))

    def _seed_product_spec(self, counters, product, spec):
        # ``key`` je lookup ključ (isti pattern kao ``_seed_specs`` headline specs ispod).
        defaults = _set_translatable(
            {"order": spec.get("order", 0), "key_sr": spec["key"]},
            value=spec["value"],
        )
        _, created = ProductSpecification.objects.get_or_create(
            product=product,
            section=spec["section"],
            key=spec["key"],
            defaults=defaults,
        )
        self._bump(counters, "specifikacije", created)

    def _seed_brochures(self, counters, brochures):
        for data in brochures:
            product = Product.objects.get(slug=data["product_slug"])
            title = data.get("title", "")
            obj, created = ProductBrochure.objects.get_or_create(
                product=product,
                title=title,
                defaults={"title_sr": title},
            )
            self._bump(counters, "brošure", created)
            if created:
                if data.get("pdf_asset"):
                    self._attach_file(
                        obj, "pdf_file", ("products", "brochures", data["pdf_asset"])
                    )
                if data.get("cover_thumbnail_asset"):
                    self._attach_file(
                        obj,
                        "cover_thumbnail_image",
                        ("products", "brochure_covers", data["cover_thumbnail_asset"]),
                    )

    def _seed_testimonials(self, counters, testimonials):
        for data in testimonials:
            product = Product.objects.get(slug=data["product_slug"])
            # ``author_name`` je lookup ključ (NIJE translatable — vidi translation.py) — ne
            # dupliraj ga u defaults, isti pattern kao ``key`` u _seed_product_spec.
            defaults = _set_translatable(
                {"order": data.get("order", 0)},
                quote=data["quote"],
                location=data.get("location", ""),
            )
            obj, created = ProductTestimonial.objects.get_or_create(
                product=product,
                author_name=data["author_name"],
                defaults=defaults,
            )
            self._bump(counters, "testimonijali", created)
            if created and data.get("photo_asset"):
                self._attach_file(
                    obj, "photo", ("products", "testimonials", data["photo_asset"])
                )

    def _seed_similar(self, counters, similar):
        for data in similar:
            product = Product.objects.get(slug=data["product_slug"])
            related = Product.objects.get(slug=data["related_product_slug"])
            _, created = ProductSimilar.objects.get_or_create(
                product=product,
                related_product=related,
                defaults={"order": data.get("order", 0)},
            )
            self._bump(counters, "slični proizvodi", created)

    def _attach_file(self, instance, field_name, path_parts):
        """Prilaži seed asset fajl na FileField/ImageField NAKON što je red kreiran.

        FileField.save() radi svoj storage upis + poziva model.save() — MORA da se desi POSLE
        get_or_create() kreacije (isti razlog kao ``seed_e2e_data._ensure_gallery_image``:
        FileField se ne može seed-ovati kroz ``defaults`` dict).
        """
        path = _SEED_ASSETS_DIR.joinpath(*path_parts)
        if not path.exists():
            raise CommandError(
                f"Seed asset nedostaje: {path} — manifest referencira fajl koji ne postoji u "
                "repou (_seed_profiles/assets/). Pokreni ops/seed/generate_profile2_manifest.py."
            )
        with path.open("rb") as fh:
            getattr(instance, field_name).save(path.name, File(fh), save=True)

    def _attach_file_if_missing(self, instance, field_name, path_parts):
        """Isto kao ``_attach_file``, ali i na POSTOJEĆEM redu (ne samo novokreiranom).

        Brand/Product redovi mogu već postojati iz profila 1 (koji ovo polje nikad nije
        setovao — nije bilo u ``defaults``), pa je ``if created:`` gate praznio profil 2
        reseed na već-postojećoj bazi: get_or_create nađe stari red (created=False) i
        prilaganje se tiho preskoči. Ovde umesto ``created`` proveravamo da li je POLJE
        prazno — idempotentno (ne re-upload-uje ako je već setovano), a ipak dopunjuje
        postojeći red kad profil 2 prvi put donosi asset koji profil 1 nije imao.
        """
        if getattr(instance, field_name):
            return
        self._attach_file(instance, field_name, path_parts)

    def _seed_specs(self, counters, headline_specs):
        if not headline_specs:
            return
        # `get` (ne `filter().first()`) je namerno fail-loud: profil koji trazi
        # specifikacije za slug koji nije seed-ovan je greska u manifestu, ne tiha rupa.
        product = Product.objects.get(slug=headline_specs["product_slug"])
        for spec in headline_specs["specs"]:
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

    def _seed_blog(self, counters, blog):
        if not blog:
            return
        tag, created = BlogTag.objects.get_or_create(
            slug=blog["tag"]["slug"],
            defaults=_set_translatable({}, name=blog["tag"]["name"]),
        )
        self._bump(counters, "blog tagovi", created)

        for data in blog["posts"]:
            defaults = _set_translatable(
                {
                    "status": "published",
                    "published_at": timezone.now(),
                    "author": None,
                },
                title=data["title"],
                perex=data["perex"],
                body=data["body"],
            )
            post, created = Post.objects.get_or_create(
                slug=data["slug"], defaults=defaults
            )
            self._bump(counters, "blog objave", created)
            # G-3: M2M tek posle save() (post sad ima PK).
            post.tags.add(tag)

    def _seed_sitesettings(self, counters):
        # SM-D8: defanzivno osiguraj singleton; NE dupliraj pages/0002 auto-seed.
        _, created = SiteSettings.objects.get_or_create(pk=1)
        self._bump(counters, "site settings", created)
