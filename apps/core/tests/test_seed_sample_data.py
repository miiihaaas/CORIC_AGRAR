"""Story 9-7 — RED-phase tests for the ``seed_sample_data`` management command.

TEA writes the SPECIFICATION (RED); Dev writes the command (GREEN). Every test here is
a contract requirement.

These tests MUST FAIL initially: the command
``apps/core/management/commands/seed_sample_data.py`` does not exist yet, so
``call_command("seed_sample_data")`` raises ``CommandError: Unknown command``.

All numbers/slugs copied verbatim from the story manifest
(``_bmad-output/implementation-artifacts/9-7-sample-seed-data-fixtures.md``) and its
interface contract.

HOST CAVEAT: native Windows pytest collection fails on libmagic (documented baseline,
NOT a regression). Run through Docker (Postgres):
    docker compose -f compose/local.yml run --rm django \
        uv run pytest apps/core/tests/test_seed_sample_data.py -v

Pokrenuti pojedinačno:
    uv run pytest apps/core/tests/test_seed_sample_data.py -v
"""

from __future__ import annotations

import re
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings
from django.utils import timezone

from apps.blog.models import Category as BlogCategory
from apps.blog.models import Post
from apps.blog.models import Tag as BlogTag
from apps.brands.models import Brand
from apps.brands.models import Category as BrandCategory
from apps.pages.models import SiteSettings
from apps.products.models import Product, ProductSpecification

_ASCII_SLUG_RE = re.compile(r"^[a-z0-9-]+$")
_VALID_SPEC_SECTIONS = {"motor", "transmisija", "hidraulika", "ostalo"}
_DIACRITICS = set("čćžšđČĆŽŠĐ")

# Manifest — NEW tractors (condition="new", is_published=True, status="published")
_NEW_TRACTORS = {
    "agri-tracking-tb804": {"hp": 80, "year": 2024, "price": Decimal("28500.00")},
    "wuzheng-wz504": {"hp": 50, "year": 2023, "price": Decimal("19900.00")},
    "saillong-sl904": {"hp": 90, "year": 2025, "price": Decimal("32400.00")},
}

# Manifest — USED machines (condition="used", all year <= 2022)
_USED_MACHINES = {
    "polovni-traktor-agri-tracking-tb804": {"hp": 75, "year": 2022, "price": Decimal("18500.00")},
    "polovni-tulip-mix-6m3": {"hp": 35, "year": 2018, "price": Decimal("4200.00")},
    "polovni-hzm-utovarivac": {"hp": 65, "year": 2020, "price": Decimal("15900.00")},
    "polovni-wuzheng-wz504": {"hp": 45, "year": 2019, "price": Decimal("9800.00")},
    "polovni-saillong-sl904": {"hp": 55, "year": 2021, "price": Decimal("13400.00")},
}

_TRACTOR_BRAND_SLUGS = ["wuzheng", "agri-tracking", "saillong"]
_EXISTING_BRAND_SLUGS = ["jeegee", "hzm", "tulip"]
_EXISTING_MEHANIZACIJA_CATEGORY_SLUGS = [
    "osnovna-obrada-zemljista",
    "priprema-zemljista",
    "masine-za-setvu",
    "radne-masine",
]


# =============================================================================
# AC1 — command runs without error on the migration-seeded test DB
# =============================================================================


@pytest.mark.django_db
def test_command_runs_without_error():
    # AC-1
    call_command("seed_sample_data")


# =============================================================================
# AC6 — TRAKTORI taxonomy: Category + 3 tractor brands
# =============================================================================


@pytest.mark.django_db
def test_traktori_category_exists():
    # AC-6
    call_command("seed_sample_data")
    assert BrandCategory.objects.filter(slug="traktori", is_for="traktori").exists()


@pytest.mark.django_db
def test_traktori_category_name_is_traktori():
    # AC-6
    call_command("seed_sample_data")
    cat = BrandCategory.objects.get(slug="traktori")
    assert cat.name == "Traktori"


@pytest.mark.django_db
def test_three_tractor_brands_exist():
    # AC-6
    call_command("seed_sample_data")
    for slug in _TRACTOR_BRAND_SLUGS:
        assert Brand.objects.filter(slug=slug).count() == 1, f"brend {slug} mora postojati tačno 1×"


# =============================================================================
# AC6a — NEW tractors with exact horse_power/year/price + publish flags
# =============================================================================


@pytest.mark.django_db
def test_new_tractors_exist_with_exact_manifest_values():
    # AC-6a
    call_command("seed_sample_data")
    for slug, vals in _NEW_TRACTORS.items():
        product = Product.objects.get(slug=slug)
        assert product.condition == "new"
        assert product.status == "published"
        assert product.is_published is True
        assert product.horse_power == vals["hp"]
        assert product.year == vals["year"]
        assert product.price_eur == vals["price"]


@pytest.mark.django_db
def test_headline_tractor_resolves_via_published_filter():
    # AC-6a — UJ-2 model-inquiry re-validation path
    call_command("seed_sample_data")
    assert Product.objects.filter(
        slug="agri-tracking-tb804", is_published=True, condition="new"
    ).exists()


@pytest.mark.django_db
def test_year_gte_2024_filter_returns_exactly_two_new_tractors():
    # AC-6a — FILTER DETERMINIZAM (TVRD za UJ-1)
    call_command("seed_sample_data")
    slugs = set(
        Product.objects.filter(year__gte=2024, is_published=True, condition="new").values_list(
            "slug", flat=True
        )
    )
    assert slugs == {"agri-tracking-tb804", "saillong-sl904"}


@pytest.mark.django_db
def test_horse_power_lt_60_new_scope_returns_only_wuzheng():
    # AC-6a — horse_power<60 MORA scope-ovati na condition="new"
    call_command("seed_sample_data")
    slugs = set(
        Product.objects.filter(horse_power__lt=60, condition="new", is_published=True).values_list(
            "slug", flat=True
        )
    )
    assert slugs == {"wuzheng-wz504"}


@pytest.mark.django_db
def test_price_lte_20000_new_scope_returns_only_wuzheng():
    # AC-6a — price_eur<=20000 → samo wuzheng-wz504 (scope na NOVE traktore iz manifesta;
    # migration-seed-ovani tulip-mix-6m3/8m3 su takođe condition="new"+published sa cenom
    # < 20000 i NE smeju se dirati per AC2, pa filter scope-ujemo na seed-ovani traktor set
    # — isti princip kao year__gte=2024 determinizam "tačno 2 NOVA traktora").
    call_command("seed_sample_data")
    slugs = set(
        Product.objects.filter(
            slug__in=list(_NEW_TRACTORS),
            price_eur__lte=Decimal("20000"),
            condition="new",
            is_published=True,
        ).values_list("slug", flat=True)
    )
    assert slugs == {"wuzheng-wz504"}


@pytest.mark.django_db
def test_headline_tractor_specifications_exist_and_readable():
    # AC-6a — behavioral coverage of the _seed_specs code path (not just code-coverage).
    call_command("seed_sample_data")
    specs = ProductSpecification.objects.filter(product__slug="agri-tracking-tb804")
    assert specs.exists()
    assert specs.count() >= 3
    for spec in specs:
        assert spec.section in _VALID_SPEC_SECTIONS, (
            f"section {spec.section!r} mora biti u {_VALID_SPEC_SECTIONS}"
        )
        assert spec.key, "spec key mora biti popunjen"
        assert spec.key_sr, "spec key_sr (modeltranslation) mora biti popunjen"
        assert spec.value, "spec value mora biti popunjen"


# =============================================================================
# AC6b — USED machines: exactly 5, all year <= 2022, none in new-tractor buckets
# =============================================================================


@pytest.mark.django_db
def test_five_used_machines_exist_with_exact_values():
    # AC-6b
    call_command("seed_sample_data")
    for slug, vals in _USED_MACHINES.items():
        product = Product.objects.get(slug=slug)
        assert product.condition == "used"
        assert product.is_published is True
        assert product.status == "published"
        assert product.horse_power == vals["hp"]
        assert product.year == vals["year"]
        assert product.price_eur == vals["price"]


@pytest.mark.django_db
def test_used_machine_count_is_exactly_five():
    # AC-6b
    call_command("seed_sample_data")
    assert Product.objects.filter(slug__in=list(_USED_MACHINES)).count() == 5


@pytest.mark.django_db
def test_no_used_machine_has_year_gte_2024():
    # AC-6b — DETERMINIZAM GRANICA: polovne NIKAD ne upadaju u year>=2024 bucket
    call_command("seed_sample_data")
    used_qs = Product.objects.filter(slug__in=list(_USED_MACHINES))
    assert not used_qs.filter(year__gte=2024).exists()
    assert used_qs.filter(year__lte=2022).count() == 5


# =============================================================================
# AC7 — Blog posts published + Category + Tag
# =============================================================================


@pytest.mark.django_db
def test_blog_category_ratarstvo_and_tag_zetva_exist():
    # AC-7
    call_command("seed_sample_data")
    assert BlogCategory.objects.filter(slug="ratarstvo").exists()
    assert BlogTag.objects.filter(slug="zetva").exists()


@pytest.mark.django_db
def test_at_least_three_published_posts_via_published_manager():
    # AC-7
    call_command("seed_sample_data")
    published = Post.published.all()
    assert published.count() >= 3
    for post in published:
        assert post.status == "published"
        assert post.published_at is not None
        assert post.published_at <= timezone.now()


@pytest.mark.django_db
def test_headline_post_slug_exists_and_published():
    # AC-7
    call_command("seed_sample_data")
    assert Post.published.filter(slug="pet-saveta-za-prolecnu-setvu").exists()


@pytest.mark.django_db
def test_published_posts_have_category_and_tag():
    # AC-7
    call_command("seed_sample_data")
    post = Post.published.get(slug="pet-saveta-za-prolecnu-setvu")
    assert post.category is not None
    assert post.tags.exists()


# =============================================================================
# AC8 — SiteSettings singleton present (pk=1, exactly one row)
# =============================================================================


@pytest.mark.django_db
def test_sitesettings_singleton_present():
    # AC-8
    call_command("seed_sample_data")
    assert SiteSettings.objects.filter(pk=1).exists()
    assert SiteSettings.objects.count() == 1


# =============================================================================
# AC3 — Idempotency: run twice → identical counts + exact slug resolution
# =============================================================================


@pytest.mark.django_db
def test_idempotent_run_twice_no_exception_and_stable_counts():
    # AC-3
    call_command("seed_sample_data")
    new_count_1 = Product.objects.filter(slug__in=list(_NEW_TRACTORS)).count()
    used_count_1 = Product.objects.filter(slug__in=list(_USED_MACHINES)).count()
    post_count_1 = Post.objects.count()
    brand_count_1 = Brand.objects.count()
    spec_count_1 = ProductSpecification.objects.filter(
        product__slug="agri-tracking-tb804"
    ).count()

    call_command("seed_sample_data")  # second run MUST NOT raise

    assert Product.objects.filter(slug__in=list(_NEW_TRACTORS)).count() == new_count_1
    assert Product.objects.filter(slug__in=list(_USED_MACHINES)).count() == used_count_1
    assert Post.objects.count() == post_count_1
    assert Brand.objects.count() == brand_count_1
    # _seed_specs get_or_create keyed on (product, section, key) MUST NOT double rows.
    assert (
        ProductSpecification.objects.filter(product__slug="agri-tracking-tb804").count()
        == spec_count_1
    )


@pytest.mark.django_db
def test_idempotent_exact_slug_still_resolves_after_second_run():
    # AC-3 — catches delete-and-recreate-with-different-PK (counts stable, identity changed)
    call_command("seed_sample_data")
    call_command("seed_sample_data")
    headline = Product.objects.get(slug="agri-tracking-tb804")
    assert headline.is_published is True
    assert headline.condition == "new"
    # exactly one row per manifest slug (no duplicate created on 2nd run)
    for slug in list(_NEW_TRACTORS) + list(_USED_MACHINES):
        assert Product.objects.filter(slug=slug).count() == 1


# =============================================================================
# AC4 — Modeltranslation _sr + diacritics + ASCII slugs
# =============================================================================


@pytest.mark.django_db
def test_modeltranslation_sr_column_populated_and_base_accessor_matches():
    # AC-4
    call_command("seed_sample_data")
    product = Product.objects.get(slug="agri-tracking-tb804")
    assert product.name_sr, "name_sr mora biti popunjen"
    assert product.name == product.name_sr, "bazni accessor čita _sr kolonu"

    cat = BrandCategory.objects.get(slug="traktori")
    assert cat.name_sr
    assert cat.name == cat.name_sr


@pytest.mark.django_db
def test_headline_post_title_sr_populated_and_base_accessor_matches():
    # AC-4 — pin title_sr per-field (analogno product name_sr), ne samo collective _sr korpus.
    call_command("seed_sample_data")
    post = Post.objects.get(slug="pet-saveta-za-prolecnu-setvu")
    assert post.title_sr, "title_sr mora biti popunjen"
    assert post.title == post.title_sr, "bazni title accessor čita _sr kolonu"


@pytest.mark.django_db
def test_at_least_one_user_facing_field_contains_serbian_diacritic():
    # AC-4 — šišana latinica regression guard
    call_command("seed_sample_data")
    corpus = []
    for product in Product.objects.filter(
        slug__in=list(_NEW_TRACTORS) + list(_USED_MACHINES)
    ):
        corpus.append(product.name_sr or "")
        corpus.append(product.description_sr or "")
        corpus.extend(product.key_features_sr or [])
    corpus.append(BrandCategory.objects.get(slug="traktori").description_sr or "")
    for post in Post.objects.all():
        corpus.append(post.title_sr or "")
        corpus.append(post.perex_sr or "")
        corpus.append(post.body_sr or "")
    blob = " ".join(corpus)
    assert _DIACRITICS & set(blob), (
        "Bar jedno user-facing srpsko polje MORA sadržati punu dijakritiku (č/ć/ž/š/đ)."
    )


@pytest.mark.django_db
def test_all_new_slugs_are_ascii():
    # AC-4
    call_command("seed_sample_data")
    new_slugs = (
        list(_NEW_TRACTORS)
        + list(_USED_MACHINES)
        + _TRACTOR_BRAND_SLUGS
        + ["traktori", "ratarstvo", "zetva", "pet-saveta-za-prolecnu-setvu"]
    )
    for slug in new_slugs:
        assert _ASCII_SLUG_RE.match(slug), f"slug {slug!r} mora biti ASCII ^[a-z0-9-]+$"


# =============================================================================
# AC5 — Production guard (both paths)
# =============================================================================


@pytest.mark.django_db
@override_settings(DEBUG=False)
def test_production_guard_blocks_without_force():
    # AC-5 (negative)
    with pytest.raises(CommandError):
        call_command("seed_sample_data")


@pytest.mark.django_db
@override_settings(DEBUG=False)
def test_force_flag_bypasses_production_guard():
    # AC-5 — DEBUG=False + --force proceeds and creates objects
    call_command("seed_sample_data", force=True)
    assert BrandCategory.objects.filter(slug="traktori").exists()
    assert Product.objects.filter(slug="agri-tracking-tb804").exists()


@pytest.mark.django_db
def test_debug_true_proceeds_without_force():
    # AC-5 — default test settings DEBUG=True → no --force needed
    call_command("seed_sample_data")
    assert Product.objects.filter(slug="agri-tracking-tb804").exists()


# =============================================================================
# AC2 — Additive / no-collision with migration-seeded objects
# =============================================================================


@pytest.mark.django_db
def test_existing_brands_not_duplicated():
    # AC-2
    call_command("seed_sample_data")
    for slug in _EXISTING_BRAND_SLUGS:
        assert Brand.objects.filter(slug=slug).count() == 1, (
            f"postojeći brend {slug} mora ostati tačno 1 instanca"
        )


@pytest.mark.django_db
def test_existing_mehanizacija_categories_unchanged():
    # AC-2
    before = {
        slug: BrandCategory.objects.filter(slug=slug).count()
        for slug in _EXISTING_MEHANIZACIJA_CATEGORY_SLUGS
    }
    call_command("seed_sample_data")
    after = {
        slug: BrandCategory.objects.filter(slug=slug).count()
        for slug in _EXISTING_MEHANIZACIJA_CATEGORY_SLUGS
    }
    assert before == after
    for slug, count in after.items():
        assert count == 1, f"kategorija {slug} mora ostati tačno 1 instanca"


@pytest.mark.django_db
def test_existing_tulip_products_not_duplicated():
    # AC-2
    call_command("seed_sample_data")
    assert Product.objects.filter(slug="tulip-mix-6m3").count() == 1
    assert Product.objects.filter(slug="tulip-mix-8m3").count() == 1


# =============================================================================
# SM-D7 — Credential safety: no seeded superuser / no usable password
# =============================================================================


@pytest.mark.django_db
def test_command_creates_no_new_superuser():
    # SM-D7 (security)
    User = get_user_model()
    before = User.objects.filter(is_superuser=True).count()
    call_command("seed_sample_data")
    after = User.objects.filter(is_superuser=True).count()
    assert after == before, "seed_sample_data NE sme da kreira superusera (SM-D7)"


@pytest.mark.django_db
def test_command_creates_no_user_with_usable_password():
    # SM-D7 (security) — v1 preporuka: command ne pravi usera uopšte
    User = get_user_model()
    before_pks = set(User.objects.values_list("pk", flat=True))
    call_command("seed_sample_data")
    new_users = User.objects.exclude(pk__in=before_pks)
    for user in new_users:
        assert user.has_usable_password() is False, (
            "ako command kreira usera, NE sme imati upotrebljiv password (SM-D7)"
        )
