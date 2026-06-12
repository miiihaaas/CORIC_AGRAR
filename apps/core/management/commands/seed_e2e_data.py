"""Story 9-8 — DEV-only idempotentan E2E data-setup command (Playwright fixtures).

Ovaj command je GREEN data-setup koji ``tests/e2e/conftest.py`` ``e2e_data`` fixtura
poziva (``python manage.py seed_e2e_data --force``). Razdvojen je od 9-7
``seed_sample_data`` jer pokriva REALAN GAP koji E2E razotkriva (AC12): 9-7 seed pravi
traktore sa ``subcategory=None`` (NULL JOIN ISKLJUČUJE ih iz ``TractorListView``) i
``0 ProductImage`` (galerija ``{% if product.images.all %}`` se NIKAD ne renderuje) →
UJ-1 je bez remedijacije strukturno nemoguć.

ŠTA RADI (sve idempotentno, DEV/staging only):
  1. Pozove ``seed_sample_data`` (force) — referencira/kreira deterministički content.
  2. (a) Listing-visibility: ``get_or_create`` ``traktori`` Subcategory pod Category
     ``slug="traktori"`` + dodeli je trima NOVIM traktorima
     (agri-tracking-tb804, wuzheng-wz504, saillong-sl904) → postaju vidljivi u
     ``TractorListView`` (filter ``subcategory__category__is_for="traktori"``).
  3. (b) Galerija: ``get_or_create`` ≥1 ``ProductImage`` za ``agri-tracking-tb804``
     (dev asset ``tests/e2e/assets/sample.png``) → galerija/Lightbox se renderuje.
  4. (c) UJ-3 idempotentnost (I-3): obriše eventualne prethodne ``e2e-test-produkt`` i
     ``e2e-test-produkt-gate`` (CASCADE briše inline ProductImage/ProductSpecification)
     → ponovljeni admin-create run-ovi su čisti (nema unique-slug kolizije).

PRODUCTION GUARD (SM-D2 mirror): odbija ``DEBUG=False`` bez ``--force``. NE auto-run u
entrypoint-u / prod-u. ``--reset-axes`` opcija flush-uje django-axes ``AccessAttempt``
(mirror ``axes_reset``) — može se koristiti umesto zasebnog ``axes_reset`` poziva.

ARHITEKTURNA GRANICA: kao i ``seed_sample_data``, ovo je operativni/management
(data-bootstrap) sloj, pa je direktni import domain modela svestan dozvoljen izuzetak.
"""

from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.brands.models import Category as BrandCategory
from apps.brands.models import Subcategory
from apps.products.models import Product, ProductImage

# Deterministički slug-ovi (mirror tests/e2e/conftest.py konstanti).
TRAKTORI_CATEGORY_SLUG = "traktori"
TRAKTORI_SUBCATEGORY_SLUG = "traktori"
TRAKTORI_SUBCATEGORY_NAME = "Traktori"

NEW_TRACTOR_SLUGS = [
    "agri-tracking-tb804",
    "wuzheng-wz504",
    "saillong-sl904",
]
GALLERY_TRACTOR_SLUG = "agri-tracking-tb804"

# UJ-3 fiksni slug-ovi koje admin-create testovi prave (happy-path + publish-gate edge).
# Moraju se očistiti PRE testova (I-3 idempotentnost).
E2E_PRODUCT_SLUGS = ["e2e-test-produkt", "e2e-test-produkt-gate"]

# Dev test asset (commit-ovan validan PNG) za galeriju.
SAMPLE_IMAGE = Path(settings.BASE_DIR) / "tests" / "e2e" / "assets" / "sample.png"


class Command(BaseCommand):
    help = (
        "DEV-only idempotentan E2E data-setup (Story 9.8 Playwright). Poziva "
        "seed_sample_data, pa AC12 remedijaciju (traktori Subcategory + dodela 3 "
        "traktora + ≥1 ProductImage za agri-tracking-tb804) i čisti UJ-3 fiksne "
        "slug-ove. Odbija DEBUG=False bez --force (SM-D2). NE auto-run u prod-u."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            default=False,
            help="Zaobiđi production guard i izvrši čak i sa DEBUG=False (DEV/staging samo).",
        )
        parser.add_argument(
            "--reset-axes",
            action="store_true",
            default=False,
            help="Flush django-axes AccessAttempt (mirror axes_reset) PRE E2E admin login-a.",
        )

    def handle(self, *args, **options):
        # SM-D2: production guard PRVO, PRE bilo kakvog DB write-a.
        if not settings.DEBUG and not options["force"]:
            raise CommandError(
                "seed_e2e_data je DEV-only; odbijam izvršavanje sa DEBUG=False bez --force"
            )

        # 1) 9-7 seed (idempotentan) — prosledi force da staging/CI (DEBUG=False) prođe.
        call_command("seed_sample_data", force=options["force"])

        with transaction.atomic():
            sub = self._ensure_traktori_subcategory()
            assigned = self._assign_tractors_to_subcategory(sub)
            gallery_created = self._ensure_gallery_image()
            cleaned = self._cleanup_e2e_products()

        if options["reset_axes"]:
            # django-axes built-in command (idempotentan; čisti AccessAttempt + cache).
            call_command("axes_reset")
            self.stdout.write("  axes: AccessAttempt flush-ovan (lockout reset).")

        self.stdout.write(
            self.style.SUCCESS("seed_e2e_data završen — E2E fixtures spremne.")
        )
        self.stdout.write(f"  traktori Subcategory: pk={sub.pk}")
        self.stdout.write(f"  traktora dodeljeno Subcategory-ju: {assigned}")
        self.stdout.write(
            f"  galerija slika ({GALLERY_TRACTOR_SLUG}): "
            f"{'kreirana' if gallery_created else 'već postojala'}"
        )
        self.stdout.write(f"  E2E test proizvoda očišćeno (I-3): {cleaned}")

    # -- internal helpers -----------------------------------------------------

    def _ensure_traktori_subcategory(self) -> Subcategory:
        """get_or_create traktori Subcategory pod Category slug='traktori'.

        Subcategory unique constraint je (category, parent, slug) → lookup po
        (category, slug, parent=None) je idempotentan.
        """
        category = BrandCategory.objects.get(slug=TRAKTORI_CATEGORY_SLUG)
        sub, _created = Subcategory.objects.get_or_create(
            category=category,
            slug=TRAKTORI_SUBCATEGORY_SLUG,
            parent=None,
            defaults={
                "name": TRAKTORI_SUBCATEGORY_NAME,
                "name_sr": TRAKTORI_SUBCATEGORY_NAME,
                "display_order": 0,
            },
        )
        return sub

    def _assign_tractors_to_subcategory(self, sub: Subcategory) -> int:
        """Dodeli traktori Subcategory trima NOVIM traktorima → vidljivi u listing-u.

        .update() na nullable subcategory FK je validan (PR-D3). Vrati broj reda.
        """
        return Product.objects.filter(slug__in=NEW_TRACTOR_SLUGS).update(subcategory=sub)

    def _ensure_gallery_image(self) -> bool:
        """get_or_create ≥1 ProductImage za agri-tracking-tb804 (idempotentno po (product, order=0))."""
        if not SAMPLE_IMAGE.exists():
            raise CommandError(
                f"E2E test asset nedostaje: {SAMPLE_IMAGE}. "
                "Dodaj mali validan PNG/JPG (tests/e2e/assets/sample.png)."
            )
        product = Product.objects.get(slug=GALLERY_TRACTOR_SLUG)
        # get_or_create na (product, order=0) je atomski idempotentan — ProductImage NEMA
        # unique constraint na (product, order), pa check-then-act (filter().first()) može
        # u teoriji da napravi 2 reda na double-run; get_or_create koristi jedan upsert-style
        # lookup. FileField se NE može seed-ovati u `defaults` (image.save mora pozvati storage),
        # pa fajl prilažemo TEK kad je instanca created (prvi run) — re-run ne dira fajl.
        obj, created = ProductImage.objects.get_or_create(
            product=product,
            order=0,
            defaults={"alt_text": "Agri Tracking TB804 — galerija (E2E)"},
        )
        if created:
            with SAMPLE_IMAGE.open("rb") as fh:
                obj.image.save("e2e-tb804-sample.png", File(fh), save=True)
        return created

    def _cleanup_e2e_products(self) -> int:
        """Obriši prethodne UJ-3 test proizvode (CASCADE inline images/specs) — I-3."""
        deleted, _detail = Product.objects.filter(slug__in=E2E_PRODUCT_SLUGS).delete()
        return deleted
