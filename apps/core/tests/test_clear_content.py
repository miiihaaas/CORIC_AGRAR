"""Ugovor za ``clear_content`` — brisanje demo sadrzaja bez rusenja panel login-a.

Komanda je par za ``seed_sample_data``: seed puni demo sadrzaj, ova ga sklanja da
prezentacija krene iz cistog stanja.

NAJVAZNIJI TEST U FAJLU je ``test_users_survive_clear`` — cela poenta dizajna
(ORM nad eksplicitnom listom modela umesto ``flush``) je da panel login prezivi.
Ako taj test padne, komanda je opasna bez obzira sto sve ostalo prolazi.

HOST CAVEAT: pokretati kroz Docker (libmagic baseline na Windows host-u):
    docker compose -f compose/local.yml run --rm django \
        uv run pytest apps/core/tests/test_clear_content.py -v
"""

from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings

from apps.core.management.commands.clear_content import MIGRATION_SEEDED_PRODUCT_SLUGS
from apps.blog.models import Category as BlogCategory
from apps.blog.models import Post
from apps.blog.models import Tag as BlogTag
from apps.brands.models import Brand
from apps.brands.models import Category as BrandCategory
from apps.forms.models import Lead
from apps.gdpr.models import CookiePolicy
from apps.pages.models import Page, SiteSettings
from apps.products.models import Product, ProductImage, ProductSpecification
from apps.seo.models import Redirect, SeoMeta

pytestmark = pytest.mark.django_db


def _seed(**kwargs):
    """Napuni demo sadrzaj (profil 1) — polazno stanje za brisanje."""
    call_command("seed_sample_data", force=True, **kwargs)


def _clear(**kwargs):
    call_command("clear_content", interactive=False, **kwargs)


# =============================================================================
# Ono sto MORA nestati
# =============================================================================


def test_products_are_deleted():
    _seed()
    assert Product.objects.exclude(slug__in=MIGRATION_SEEDED_PRODUCT_SLUGS).exists()
    _clear()
    assert not Product.objects.exclude(slug__in=MIGRATION_SEEDED_PRODUCT_SLUGS).exists()


def test_migration_seeded_products_survive():
    """Migracija brands/0004 pravi tulip-mix-* proizvode; brisanje bi ih trajno unistilo.

    Django tu migraciju vodi kao primenjenu -> nema je ko vratiti, a pune stranu
    /sr/mehanizacija/mix-prikolice/. Seed komanda ih NE pravi.
    """
    _seed()
    assert set(MIGRATION_SEEDED_PRODUCT_SLUGS) <= set(
        Product.objects.values_list("slug", flat=True)
    ), "Preduslov: migracija je napravila ove proizvode."
    _clear()
    survivors = set(Product.objects.values_list("slug", flat=True))
    assert set(MIGRATION_SEEDED_PRODUCT_SLUGS) <= survivors


def test_product_related_rows_cascade():
    """ProductSpecification/ProductImage nestaju sa proizvodom (CASCADE)."""
    _seed()
    product = Product.objects.get(slug="agri-tracking-tb804")
    ProductImage.objects.create(product=product, image="demo/x.jpg", order=0)
    assert ProductSpecification.objects.filter(product=product).exists()
    _clear()
    # Scope na OBRISAN proizvod: tulip-mix-* prezivljavaju sa svojim specifikacijama
    # (migracijski), pa globalni `not exists()` ovde ne bi bio tacan.
    assert not ProductSpecification.objects.filter(product__slug="agri-tracking-tb804").exists()
    assert not ProductImage.objects.exists()


def test_blog_is_deleted():
    """Blog se brise (eksplicitna odluka, za razliku od lead-ova)."""
    _seed()
    assert Post.objects.exists()
    _clear()
    assert not Post.objects.exists()
    assert not BlogCategory.objects.exists()
    assert not BlogTag.objects.exists()


def test_orphan_seometa_is_deleted():
    """GFK NEMA cascade — SeoMeta na obrisan Product bi ostao siroce."""
    _seed()
    product = Product.objects.get(slug="agri-tracking-tb804")
    SeoMeta.objects.create(
        content_type=ContentType.objects.get_for_model(Product),
        object_id=product.pk,
        meta_title="Demo",
    )
    _clear()
    assert not SeoMeta.objects.filter(
        content_type=ContentType.objects.get_for_model(Product)
    ).exists()


# =============================================================================
# Ono sto MORA prezivet
# =============================================================================


def test_users_survive_clear():
    """KLJUCNI UGOVOR: panel login prezivljava brisanje.

    Zbog ovoga komanda ide kroz ORM nad eksplicitnom listom modela umesto
    ``manage.py flush`` (koji TRUNCATE-uje i auth_user).
    """
    User = get_user_model()
    admin = User.objects.create_superuser(
        username="demo-admin", email="admin@example.com", password="tajna-lozinka-123"
    )
    _seed()
    _clear()
    admin.refresh_from_db()
    assert User.objects.filter(pk=admin.pk).exists()
    assert admin.is_superuser
    assert admin.check_password("tajna-lozinka-123"), "Lozinka mora ostati upotrebljiva."


def test_leads_survive_clear():
    """Lead-ovi su upiti pravih ljudi (licni podaci) — brisanje je posebna odluka."""
    _seed()
    lead = Lead.objects.create(
        form_type="contact", name="Petar Petrović", email="petar@example.com"
    )
    _clear()
    assert Lead.objects.filter(pk=lead.pk).exists()


def test_migration_seeded_brands_and_categories_survive():
    """Brendovi/kategorije iz data migracija se NE VRACAJU ako se obrisu."""
    _seed()
    brands_before = set(Brand.objects.values_list("slug", flat=True))
    categories_before = set(BrandCategory.objects.values_list("slug", flat=True))
    assert brands_before, "Preduslov: migracije/seed su napravile brendove."
    _clear()
    assert set(Brand.objects.values_list("slug", flat=True)) == brands_before
    assert set(BrandCategory.objects.values_list("slug", flat=True)) == categories_before


def test_site_configuration_survives():
    """SiteSettings/CookiePolicy/Page/Redirect su konfiguracija, ne demo sadrzaj."""
    _seed()
    Redirect.objects.create(old_path="/staro/", new_path="/novo/")
    pages_before = Page.objects.count()
    _clear()
    assert SiteSettings.objects.filter(pk=1).exists()
    assert CookiePolicy.objects.exists()
    assert Page.objects.count() == pages_before
    assert Redirect.objects.filter(old_path="/staro/").exists()


# =============================================================================
# Brane i ponasanje
# =============================================================================


@override_settings(SETTINGS_MODULE="config.settings.production")
def test_refuses_on_production_settings():
    """Mandat je lokal + staging. Nema --force prekidaca za produkciju."""
    _seed()
    with pytest.raises(CommandError, match="produkciji"):
        _clear()
    assert Product.objects.exists(), "Ništa se ne sme obrisati kad brana odbije."


@override_settings(SETTINGS_MODULE="config.settings.staging")
def test_allowed_on_staging():
    """Staging ima DEBUG=False kao i produkcija — zato brana gleda ime modula."""
    _seed()
    _clear()
    assert not Product.objects.exclude(slug__in=MIGRATION_SEEDED_PRODUCT_SLUGS).exists()


def test_dry_run_changes_nothing():
    _seed()
    count_before = Product.objects.count()
    _clear(dry_run=True)
    assert Product.objects.count() == count_before


def test_is_idempotent():
    """Drugo pokretanje nad praznim sadrzajem ne sme da pukne."""
    _seed()
    _clear()
    _clear()
    assert not Product.objects.exclude(slug__in=MIGRATION_SEEDED_PRODUCT_SLUGS).exists()
