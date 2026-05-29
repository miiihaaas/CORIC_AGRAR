"""Story 2.2 — apps/products/models.py testovi (RED phase TDD).

Pokriva AC1-AC13 — Product, ProductImage, ProductVariant, ProductSpecification,
ProductBrochure, ProductTestimonial, ProductSimilar modeli + modeltranslation
registracija + cross-app FK chain + settings delta.

Test scope (per story spec AC13 "Testovi MORAJU pokrivati" list):
- Foundation: apps.products u INSTALLED_APPS, ProductsConfig.name, MODELTRANSLATION_FALLBACK_LANGUAGES
- __str__ za svih 7 modela
- FK + related_name access pattern-i (brand.products, product.images, outgoing/incoming_similars, ...)
- Slug constraints na Product (global unique, save() auto-gen, full_clean() auto-gen, ASCII transliteration)
- PROTECT delete behavior (Brand/Series/Subcategory)
- CASCADE delete behavior (Product → 6 child entiteta)
- Nullable series + subcategory (uključujući both-NULL edge case PR-D2+D3)
- ConditionChoice + StatusChoice TextChoices values
- key_features JSON validation (max 3, list-of-str, empty list ok) — base + sr/hu/en variants
- ProductSpecification SpecSection TextChoices + ordering excludes "section" field
- ProductBrochure __str__ fallback kroz gettext_lazy printf format
- ProductSimilar: clean() blokira self-reference (full_clean path) + DB CheckConstraint
  (objects.create path) + UniqueConstraint na (product, related_product) + directional
  asymmetric (reciprocal pair allowed)
- Translation: 6 modela registrovana, ProductSimilar IZUZET; introspection na _meta.get_fields()
- modeltranslation fallback to sr when active lang empty
- Migration smoke (7 tables exist, 33 translation columns present)

Naming convention: srpska latinica + engleski code identifiers (per project-context.md).
TEA RED phase: svi testovi MORAJU pasti (ImportError) dok Dev ne implementira modele.

Pokrenuti sa:
    uv run pytest apps/products/tests/test_models.py -v --no-header

Refs:
- 2-2-product-i-related-modeli.md (story spec, AC1-AC13)
- 2-2-interface-contract.md (TEA canonical contract — Dev MUST satisfy)
- 2-1-brand-series-category-subcategory-modeli.md (precedent pattern reference)
- apps/brands/tests/test_models.py (test style reference)
"""

from __future__ import annotations

import pytest
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from django.db.models import ProtectedError

# Svi testovi u ovom modulu koriste DB (modeltranslation registracija + ORM)
pytestmark = pytest.mark.django_db


# =============================================================================
# Fixtures + helpers
# =============================================================================


@pytest.fixture(autouse=True)
def _media_root_isolated(tmp_path, settings):
    """Per-test MEDIA_ROOT isolation — file-stub uploads ne curi između testova."""
    settings.MEDIA_ROOT = tmp_path


def _create_brand(**overrides):
    """Helper: kreira Brand sa default validnim poljima (mirror 2.1 _make_brand)."""
    from apps.brands.models import Brand

    defaults = {
        "name": "Test Brand",
        "brand_color": "",
        "statistics": [],
    }
    defaults.update(overrides)
    return Brand.objects.create(**defaults)


def _create_category(**overrides):
    from apps.brands.models import Category

    defaults = {
        "name": "Test Category",
        "is_for": "mehanizacija",
    }
    defaults.update(overrides)
    return Category.objects.create(**defaults)


def _create_series(brand=None, **overrides):
    from apps.brands.models import Series

    if brand is None:
        brand = _create_brand()
    defaults = {
        "brand": brand,
        "name": "Test Series",
    }
    defaults.update(overrides)
    return Series.objects.create(**defaults)


def _create_subcategory(category=None, **overrides):
    from apps.brands.models import Subcategory

    if category is None:
        category = _create_category()
    defaults = {
        "category": category,
        "name": "Test Subcategory",
    }
    defaults.update(overrides)
    return Subcategory.objects.create(**defaults)


def _create_product(brand=None, **overrides):
    """Helper: kreira minimal Product sa svim required poljima."""
    from apps.products.models import Product

    if brand is None:
        brand = _create_brand()
    defaults = {
        "brand": brand,
        "name": "Test Product",
    }
    defaults.update(overrides)
    return Product.objects.create(**defaults)


def _image_stub(name: str = "stub.jpg"):
    """Minimal PNG magic header stub za REQUIRED ImageField polja.

    Per story spec "TEA fixture patterns za required file fields" Dev Note —
    Pillow MIME validacija je Story 2.3 scope, NE 2.2; minimal magic header
    stub je dovoljan za save() validation u 2.2.
    """
    return SimpleUploadedFile(
        name=name,
        content=b"\x89PNG\r\n\x1a\n",
        content_type="image/png",
    )


def _pdf_stub(name: str = "stub.pdf"):
    """Minimal PDF magic header stub za REQUIRED FileField polja.

    Per story spec "TEA fixture patterns za required file fields" — python-magic
    MIME validacija je Story 2.4 scope, NE 2.2.
    """
    return ContentFile(b"%PDF-1.4 stub", name=name)


# =============================================================================
# AC1 — Foundation / structural / settings tests
# =============================================================================


def test_apps_products_in_installed_apps():
    """AC1: 'apps.products' MORA biti registrovan u INSTALLED_APPS POSLE 'apps.brands'."""
    assert "apps.products" in settings.INSTALLED_APPS, (
        "'apps.products' nije u INSTALLED_APPS. "
        "Dev mora apendovati '\"apps.products\",' POSLE '\"apps.brands\",' "
        "u config/settings/base.py per Decision PR-D1."
    )
    # Verifikuj dep order — products dolazi POSLE brands
    brands_idx = settings.INSTALLED_APPS.index("apps.brands")
    products_idx = settings.INSTALLED_APPS.index("apps.products")
    assert products_idx > brands_idx, (
        f"'apps.products' (idx {products_idx}) MORA biti POSLE 'apps.brands' "
        f"(idx {brands_idx}) per Decision PR-D1 (jednosmerna zavisnost)."
    )


def test_products_app_config_name_is_dotted():
    """AC1 / Gotcha PR-1: ProductsConfig.name == 'apps.products' (sa apps. prefiksom)."""
    from apps.products.apps import ProductsConfig

    assert ProductsConfig.name == "apps.products", (
        f"ProductsConfig.name mora biti 'apps.products' (sa apps. prefiksom), "
        f"dobio: {ProductsConfig.name!r}. Vidi Gotcha PR-1."
    )


def test_products_app_config_default_auto_field_is_bigautofield():
    """AC1: ProductsConfig.default_auto_field == BigAutoField."""
    from apps.products.apps import ProductsConfig

    assert ProductsConfig.default_auto_field == "django.db.models.BigAutoField"


def test_modeltranslation_fallback_languages_setting():
    """AC1 / Task 1.4b: MODELTRANSLATION_FALLBACK_LANGUAGES == ('sr',).

    Architecture-defensive setting per project-context.md § i18n locale fallback —
    bez njega pristup translated polju bez aktivnog language context-a može vratiti
    None umesto sr fallback vrednosti. NIJE FR-32 mapiranje (Story 6.5).
    """
    fallback = getattr(settings, "MODELTRANSLATION_FALLBACK_LANGUAGES", None)
    assert fallback == ("sr",), (
        f"MODELTRANSLATION_FALLBACK_LANGUAGES mora biti tuple ('sr',), "
        f"dobio: {fallback!r}. Dev mora dodati setting u config/settings/base.py "
        f"POSLE LANGUAGES = [...] bloka (Story 1.4 lokacija) per Task 1.4b."
    )


# =============================================================================
# AC2 — Product model
# =============================================================================


def test_product_inheritance_from_slugged_and_timestamped_mixins():
    """AC2: Product MORA naslediti SluggedModel + TimestampedModel iz apps.core.models.

    Prvi konzument 2.1 D3 foundation. Order: SluggedModel pre TimestampedModel
    (Python MRO; oba abstract = True).
    """
    from apps.core.models import SluggedModel, TimestampedModel
    from apps.products.models import Product

    bases = Product.__mro__
    assert SluggedModel in bases, (
        f"Product mora naslediti SluggedModel iz apps.core.models; "
        f"MRO: {[c.__name__ for c in bases]}"
    )
    assert TimestampedModel in bases, (
        f"Product mora naslediti TimestampedModel iz apps.core.models; "
        f"MRO: {[c.__name__ for c in bases]}"
    )


def test_product_str_returns_brand_and_name():
    """AC2: Product.__str__ vraća '<brand.name> — <product.name>' (em-dash)."""
    brand = _create_brand(name="John Deere")
    product = _create_product(brand=brand, name="TB-804")
    assert str(product) == "John Deere — TB-804", (
        f"Product.__str__ mora vratiti 'John Deere — TB-804', dobio: {str(product)!r}"
    )


@pytest.mark.skip(reason="URLs come in Story 2.7 (Gotcha PR-5 + PR-12)")
def test_product_get_absolute_url_returns_proizvod_path():
    """AC2: Product.get_absolute_url() koristi reverse('products:detail', ...).

    URL pattern NE POSTOJI u 2.2 — `apps/products/urls.py` se kreira u 2.7.
    Test je @pytest.mark.skip per prescribed Gotcha PR-5 pattern.
    """
    from apps.products.models import Product

    product = Product(slug="test-product")
    url = product.get_absolute_url()
    assert isinstance(url, str)


def test_product_get_absolute_url_method_exists():
    """AC2: Product MORA imati get_absolute_url() metodu (callable check — zero-cost)."""
    from apps.products.models import Product

    assert callable(getattr(Product, "get_absolute_url", None)), (
        "Product MORA imati get_absolute_url() metodu (per AC2)."
    )


def test_product_slug_auto_gen_from_name_via_save_override():
    """AC2: Product.save() auto-generiše slug iz name (2.1 Pattern A iter-2 fix)."""
    from apps.products.models import Product

    brand = _create_brand()
    product = Product(brand=brand, name="TB-Traktor 805")
    product.save()
    assert product.slug == "tb-traktor-805", (
        f"Auto-generated slug mora biti 'tb-traktor-805', dobio: {product.slug!r}"
    )


def test_product_slug_auto_gen_via_full_clean_override():
    """AC2: Product.full_clean() poziva slug auto-gen PRE Django field-level validation.

    2.1 Pattern A defensive guard — omogućava caller-u da pozove full_clean() na
    unsaved Product bez slug-a (umesto ValidationError za slug.blank=False).
    """
    from apps.products.models import Product

    brand = _create_brand()
    product = Product(brand=brand, name="TB-Traktor 806")
    # full_clean() NE sme raise-ovati zbog slug.blank=False — auto-gen ga popunjava
    product.full_clean()
    assert product.slug == "tb-traktor-806", (
        f"full_clean() override mora auto-gen slug iz name; dobio: {product.slug!r}"
    )


def test_product_slug_preserve_explicit_value():
    """AC2: Eksplicitni slug se NE overwrite-uje u save()."""
    from apps.products.models import Product

    brand = _create_brand()
    product = Product(brand=brand, name="Whatever", slug="custom-product-slug")
    product.save()
    assert product.slug == "custom-product-slug"


def test_product_slug_ascii_transliteration_of_serbian_diacritics():
    """AC2: Srpska dijakritica (Č/Ž/Š/Đ/Ć) → ASCII slug.

    Inherits Story 2.1 slugify_ascii helper iz apps.core.utils.
    Verifies dva-stage replacement (BR-14 regression guard).
    """
    brand = _create_brand()
    product = _create_product(brand=brand, name="Čorić TB-804 Žuti Šargarepa Đak")
    assert product.slug == "coric-tb-804-zuti-sargarepa-dak", (
        f"Slug mora biti ASCII transliteration, dobio: {product.slug!r}"
    )


def test_product_slug_globally_unique_raises_on_collision():
    """AC2: Product.slug je globally unique (SluggedModel mixin unique=True).

    save() override poziva full_clean() pa ValidationError; raw DB INSERT bi
    raised IntegrityError. Oba su acceptable signal — koristimo OR.
    """
    from apps.products.models import Product

    brand = _create_brand()
    _create_product(brand=brand, name="Same Name")
    with pytest.raises((ValidationError, IntegrityError)):
        Product.objects.create(brand=brand, name="Same Name Mirror", slug="same-name")


def test_product_brand_protect_blocks_deletion_with_products():
    """AC2: Product.brand on_delete=PROTECT — brisanje Brand-a sa Product-ima raise."""
    brand = _create_brand()
    _create_product(brand=brand)
    with pytest.raises(ProtectedError):
        brand.delete()


def test_product_series_protect_blocks_deletion_with_products():
    """AC2: Product.series on_delete=PROTECT — brisanje Series-a sa Product-ima raise."""
    brand = _create_brand()
    series = _create_series(brand=brand)
    _create_product(brand=brand, series=series)
    with pytest.raises(ProtectedError):
        series.delete()


def test_product_subcategory_protect_blocks_deletion_with_products():
    """AC2: Product.subcategory on_delete=PROTECT — brisanje Subcategory-e sa Product-ima raise."""
    brand = _create_brand()
    subcategory = _create_subcategory()
    _create_product(brand=brand, subcategory=subcategory)
    with pytest.raises(ProtectedError):
        subcategory.delete()


def test_product_series_nullable_allows_orphan_product():
    """AC2 / PR-D2: Product.series is nullable — Product može imati series=None."""
    brand = _create_brand()
    product = _create_product(brand=brand, series=None)
    assert product.series is None
    # Sanity: refetch iz DB
    product.refresh_from_db()
    assert product.series is None


def test_product_subcategory_nullable_allows_orphan_product():
    """AC2 / PR-D3: Product.subcategory is nullable — Product može imati subcategory=None."""
    brand = _create_brand()
    product = _create_product(brand=brand, subcategory=None)
    assert product.subcategory is None
    product.refresh_from_db()
    assert product.subcategory is None


def test_product_without_series_and_subcategory_allowed():
    """AC2 / PR-D2+D3 combined edge case (I9): Product može imati OBA NULL istovremeno.

    Orphan product attached samo na Brand (npr. corporate demo unit, "uskoro"
    placeholder). NIJE dodatno protected — no CHECK constraint koji zahteva barem
    jedno od dvoga. Story 2.7 breadcrumb mora handle-ovati ovaj edge case.
    """
    brand = _create_brand()
    product = _create_product(brand=brand, series=None, subcategory=None)
    assert product.series is None
    assert product.subcategory is None
    # Sanity: full_clean() ne raise-uje
    product.full_clean()


def test_product_condition_choice_text_choices_match_spec():
    """AC2: ConditionChoice mora imati NEW='new' i USED='used'."""
    from apps.products.models import Product

    assert Product.ConditionChoice.NEW == "new"
    assert Product.ConditionChoice.USED == "used"


def test_product_condition_default_is_new():
    """AC2: Product.condition default = ConditionChoice.NEW."""
    from apps.products.models import Product

    field = Product._meta.get_field("condition")
    assert field.default == Product.ConditionChoice.NEW


def test_product_condition_invalid_value_raises():
    """AC2 / AC13: invalid condition value raise-uje ValidationError u full_clean().

    Per AC13 spec line 772: 'test_product_condition_choice_required —
    Product.condition ima default NEW; invalid value → ValidationError'.
    Mirror test_product_status_invalid_value_raises pattern.
    """
    from apps.products.models import Product

    brand = _create_brand()
    product = Product(brand=brand, name="X", condition="invalid_condition")
    with pytest.raises(ValidationError):
        product.full_clean()


def test_product_status_choice_text_choices_match_spec():
    """AC2: StatusChoice mora imati DRAFT/PUBLISHED/ARCHIVED."""
    from apps.products.models import Product

    assert Product.StatusChoice.DRAFT == "draft"
    assert Product.StatusChoice.PUBLISHED == "published"
    assert Product.StatusChoice.ARCHIVED == "archived"


def test_product_status_default_is_draft():
    """AC2: Product.status default = StatusChoice.DRAFT."""
    from apps.products.models import Product

    field = Product._meta.get_field("status")
    assert field.default == Product.StatusChoice.DRAFT


def test_product_status_invalid_value_raises():
    """AC2: invalid status value raise-uje ValidationError u full_clean()."""
    from apps.products.models import Product

    brand = _create_brand()
    product = Product(brand=brand, name="X", status="invalid_state")
    with pytest.raises(ValidationError):
        product.full_clean()


def test_product_is_published_default_false():
    """AC2: Product.is_published default = False."""
    from apps.products.models import Product

    field = Product._meta.get_field("is_published")
    assert field.default is False


def test_product_meta_indexes_named_per_convention():
    """AC2: Product.Meta.indexes ima 3 imena po `products_product_*_idx` konvenciji."""
    from apps.products.models import Product

    index_names = {idx.name for idx in Product._meta.indexes}
    expected = {
        "products_product_pub_created_idx",
        "products_product_brand_status_idx",
        "products_product_condition_pub_idx",
    }
    missing = expected - index_names
    assert not missing, (
        f"Product.Meta.indexes nedostaju: {missing}. Sva imena moraju pratiti "
        f"products_product_<columns>_idx konvenciju per Story 2.1 Pattern C."
    )


def test_product_meta_ordering_descending_created_at():
    """AC2: Product.Meta.ordering == ['-created_at']."""
    from apps.products.models import Product

    assert Product._meta.ordering == ["-created_at"]


def test_product_brand_related_name_is_products():
    """AC2: Product.brand.related_name == 'products' → brand.products.all()."""
    brand = _create_brand()
    _create_product(brand=brand, name="P1")
    _create_product(brand=brand, name="P2")
    assert brand.products.count() == 2


def test_product_series_related_name_is_products():
    """AC2: Product.series.related_name == 'products' → series.products.all()."""
    brand = _create_brand()
    series = _create_series(brand=brand)
    _create_product(brand=brand, series=series, name="P1")
    _create_product(brand=brand, series=series, name="P2")
    assert series.products.count() == 2


def test_product_subcategory_related_name_is_products():
    """AC2: Product.subcategory.related_name == 'products' → subcategory.products.all()."""
    brand = _create_brand()
    subcategory = _create_subcategory()
    _create_product(brand=brand, subcategory=subcategory, name="P1")
    _create_product(brand=brand, subcategory=subcategory, name="P2")
    assert subcategory.products.count() == 2


# =============================================================================
# AC2 — Product.key_features JSON validation
# =============================================================================


def test_product_key_features_empty_list_passes_clean():
    """AC2: key_features=[] passes validation (default value)."""
    from apps.products.models import Product

    brand = _create_brand()
    product = Product(brand=brand, name="X", key_features=[])
    product.full_clean()  # NE sme raise-ovati


def test_product_key_features_three_items_passes_clean():
    """AC2: tačno 3 stavki passes validation (boundary)."""
    from apps.products.models import Product

    brand = _create_brand()
    product = Product(brand=brand, name="X", key_features=["a", "b", "c"])
    product.full_clean()


def test_product_key_features_four_items_raises_validation_error():
    """AC2: 4 stavki raise-uje ValidationError; ključ JE 'key_features' (base) ili 'key_features_<lang>' (translated active)."""
    from apps.products.models import Product

    brand = _create_brand()
    product = Product(brand=brand, name="X", key_features=["a", "b", "c", "d"])
    with pytest.raises(ValidationError) as exc_info:
        product.full_clean()

    # Per I-iter3-5 Dev Note: belt-and-suspenders dizajn može generisati dual-key
    # entry u message_dict (base + translated active variant). Membership assertion.
    message_dict = exc_info.value.message_dict
    has_key_features_key = any(
        k == "key_features" or k.startswith("key_features_")
        for k in message_dict.keys()
    )
    assert has_key_features_key, (
        f"ValidationError message_dict mora sadržati 'key_features' ili "
        f"'key_features_<lang>' key, dobio keys: {list(message_dict.keys())}"
    )


def test_product_key_features_non_list_string_raises_validation_error():
    """AC2: key_features='string' (NE list) raise-uje ValidationError."""
    from apps.products.models import Product

    brand = _create_brand()
    product = Product(brand=brand, name="X", key_features="not a list")
    with pytest.raises(ValidationError):
        product.full_clean()


def test_product_key_features_non_list_dict_raises_validation_error():
    """AC2: key_features={} (dict, NE list) raise-uje ValidationError."""
    from apps.products.models import Product

    brand = _create_brand()
    product = Product(brand=brand, name="X", key_features={"a": 1})
    with pytest.raises(ValidationError):
        product.full_clean()


def test_product_key_features_non_string_items_raise_validation_error():
    """AC2: lista sa non-string stavkom (int, dict, None) raise-uje ValidationError."""
    from apps.products.models import Product

    brand = _create_brand()
    # int item
    product = Product(brand=brand, name="X", key_features=[1, 2, 3])
    with pytest.raises(ValidationError):
        product.full_clean()


@pytest.mark.parametrize("lang", ["sr", "hu", "en"])
def test_product_key_features_max_3_enforced_on_translated_variant(lang):
    """AC2 / C3 / I-iter3-5: key_features_<lang> sa 4 stavki MORA raise-ovati ValidationError.

    Belt-and-suspenders: Product.clean() iterira kroz settings.LANGUAGES i validira
    SVAKU translated varijantu. Bez ovog testa, admin može save-ovati key_features_hu=[5 stavki]
    bez ikakve provere ako se validacija primeni samo na base accessor.

    Membership assertion (NE equality) — base accessor + translated varijanta mogu
    generisati dual-key u message_dict.
    """
    from apps.products.models import Product

    brand = _create_brand()
    product = Product(brand=brand, name="X", key_features=[])
    setattr(product, f"key_features_{lang}", ["a", "b", "c", "d"])

    with pytest.raises(ValidationError) as exc_info:
        product.full_clean()

    expected_key = f"key_features_{lang}"
    assert expected_key in exc_info.value.message_dict, (
        f"ValidationError message_dict MORA sadržati ključ {expected_key!r} "
        f"(membership), dobio keys: {list(exc_info.value.message_dict.keys())}"
    )


@pytest.mark.parametrize("lang", ["sr", "hu", "en"])
def test_product_key_features_non_list_raises_on_translated_variant(lang):
    """AC2 / C3: key_features_<lang>='string' raise-uje ValidationError sa <lang> key."""
    from apps.products.models import Product

    brand = _create_brand()
    product = Product(brand=brand, name="X", key_features=[])
    setattr(product, f"key_features_{lang}", "not a list")

    with pytest.raises(ValidationError) as exc_info:
        product.full_clean()

    expected_key = f"key_features_{lang}"
    assert expected_key in exc_info.value.message_dict, (
        f"ValidationError message_dict MORA sadržati {expected_key!r}, "
        f"dobio: {list(exc_info.value.message_dict.keys())}"
    )


# =============================================================================
# AC3 — ProductImage model
# =============================================================================


def test_product_image_str_returns_product_and_order():
    """AC3: ProductImage.__str__ vraća '<product.name> — slika <order>'."""
    from apps.products.models import ProductImage

    brand = _create_brand()
    product = _create_product(brand=brand, name="TB-804")
    pi = ProductImage.objects.create(
        product=product, image=_image_stub(), order=2, alt_text="Alt"
    )
    assert str(pi) == "TB-804 — slika 2"


def test_product_image_order_default_zero():
    """AC3: ProductImage.order default = 0."""
    from apps.products.models import ProductImage

    field = ProductImage._meta.get_field("order")
    assert field.default == 0


def test_product_image_cascades_when_product_deleted():
    """AC3: ProductImage.product on_delete=CASCADE."""
    from apps.products.models import ProductImage

    brand = _create_brand()
    product = _create_product(brand=brand)
    ProductImage.objects.create(product=product, image=_image_stub("a.jpg"), order=0)
    ProductImage.objects.create(product=product, image=_image_stub("b.jpg"), order=1)
    assert ProductImage.objects.count() == 2

    product.delete()
    assert ProductImage.objects.count() == 0, (
        "ProductImage mora biti CASCADE obrisana sa Product."
    )


def test_product_images_related_name_access():
    """AC3: ProductImage.product.related_name == 'images' → product.images.all()."""
    from apps.products.models import ProductImage

    brand = _create_brand()
    product = _create_product(brand=brand)
    ProductImage.objects.create(product=product, image=_image_stub("a.jpg"), order=0)
    ProductImage.objects.create(product=product, image=_image_stub("b.jpg"), order=1)
    assert product.images.count() == 2


# =============================================================================
# AC4 — ProductVariant model
# =============================================================================


def test_product_variant_str_returns_name():
    """AC4: ProductVariant.__str__ vraća self.name (locale-aware kroz modeltranslation)."""
    from apps.products.models import ProductVariant

    brand = _create_brand()
    product = _create_product(brand=brand)
    variant = ProductVariant.objects.create(
        product=product, name="Sa kabinom", code="TB804-CAB"
    )
    assert str(variant) == "Sa kabinom"


def test_product_variant_cascades_when_product_deleted():
    """AC4: ProductVariant.product on_delete=CASCADE."""
    from apps.products.models import ProductVariant

    brand = _create_brand()
    product = _create_product(brand=brand)
    ProductVariant.objects.create(product=product, name="V1")
    ProductVariant.objects.create(product=product, name="V2")
    assert ProductVariant.objects.count() == 2

    product.delete()
    assert ProductVariant.objects.count() == 0


def test_product_variants_related_name_access():
    """AC4: ProductVariant.product.related_name == 'variants' → product.variants.all()."""
    from apps.products.models import ProductVariant

    brand = _create_brand()
    product = _create_product(brand=brand)
    ProductVariant.objects.create(product=product, name="V1")
    ProductVariant.objects.create(product=product, name="V2")
    assert product.variants.count() == 2


def test_product_variant_description_has_max_length_validator():
    """L1 (Code Review iter-2): belt-and-suspenders consistency with Product.description."""
    from django.core.validators import MaxLengthValidator

    from apps.products.models import ProductVariant

    validators = ProductVariant._meta.get_field("description").validators
    assert any(
        isinstance(v, MaxLengthValidator) and v.limit_value == 50000 for v in validators
    )


# =============================================================================
# AC5 — ProductSpecification model
# =============================================================================


def test_product_specification_str_format():
    """AC5: ProductSpecification.__str__ vraća '<section_display>: <key> = <value>'."""
    from apps.products.models import ProductSpecification

    brand = _create_brand()
    product = _create_product(brand=brand)
    spec = ProductSpecification.objects.create(
        product=product, section="motor", key="Snaga", value="80 KS"
    )
    result = str(spec)
    # get_section_display() vraća labelu (translatable proxy) → string konverzija
    assert "Snaga = 80 KS" in result, (
        f"ProductSpecification.__str__ mora sadržati 'Snaga = 80 KS', dobio: {result!r}"
    )


def test_product_specification_section_choices_match_spec():
    """AC5: SpecSection mora imati MOTOR/TRANSMISIJA/HIDRAULIKA/OSTALO."""
    from apps.products.models import ProductSpecification

    SpecSection = ProductSpecification.SpecSection
    assert SpecSection.MOTOR == "motor"
    assert SpecSection.TRANSMISIJA == "transmisija"
    assert SpecSection.HIDRAULIKA == "hidraulika"
    assert SpecSection.OSTALO == "ostalo"


def test_product_specification_section_default_is_ostalo():
    """AC5: ProductSpecification.section default = SpecSection.OSTALO."""
    from apps.products.models import ProductSpecification

    field = ProductSpecification._meta.get_field("section")
    assert field.default == ProductSpecification.SpecSection.OSTALO


def test_product_specification_default_ordering_excludes_section_field():
    """AC5 (I3 critical): Meta.ordering MORA biti ['product', 'order', 'id'] (BEZ 'section').

    Alphabetical sort po section bi dao hidraulika → motor → ostalo → transmisija,
    što je SUPROTNO traženom display order-u. Display order se primenjuje u
    view-layer-u Story 2.7 kroz Case/When annotation.
    """
    from apps.products.models import ProductSpecification

    ordering = list(ProductSpecification._meta.ordering)
    assert ordering == ["product", "order", "id"], (
        f"ProductSpecification.Meta.ordering MORA biti ['product', 'order', 'id'] "
        f"(BEZ 'section'); dobio: {ordering}. Vidi AC5 I3 NOTE."
    )
    assert "section" not in ordering, (
        "section field MORA biti isključen iz default ordering — vidi AC5 I3 NOTE."
    )


def test_product_specification_cascades_when_product_deleted():
    """AC5: ProductSpecification.product on_delete=CASCADE."""
    from apps.products.models import ProductSpecification

    brand = _create_brand()
    product = _create_product(brand=brand)
    ProductSpecification.objects.create(
        product=product, section="motor", key="K", value="V"
    )
    ProductSpecification.objects.create(
        product=product, section="ostalo", key="K2", value="V2"
    )
    assert ProductSpecification.objects.count() == 2

    product.delete()
    assert ProductSpecification.objects.count() == 0


def test_product_specifications_related_name_access():
    """AC5: ProductSpecification.product.related_name == 'specifications'."""
    from apps.products.models import ProductSpecification

    brand = _create_brand()
    product = _create_product(brand=brand)
    ProductSpecification.objects.create(
        product=product, section="motor", key="K", value="V"
    )
    assert product.specifications.count() == 1


# =============================================================================
# AC6 — ProductBrochure model
# =============================================================================


def test_product_brochure_str_returns_title_when_present():
    """AC6: ProductBrochure.__str__ vraća self.title kada postoji."""
    from apps.products.models import ProductBrochure

    brand = _create_brand()
    product = _create_product(brand=brand)
    brochure = ProductBrochure.objects.create(
        product=product, pdf_file=_pdf_stub(), title="Tehnička specifikacija"
    )
    assert str(brochure) == "Tehnička specifikacija"


def test_product_brochure_str_fallback_uses_gettext_lazy_printf_format():
    """AC6 / I-iter3-6: Bez title-a, ProductBrochure.__str__ vraća locale-aware fallback.

    Fallback MORA biti `_("Brošura — %(name)s") % {"name": self.product.name}`
    (gettext_lazy printf format), NE f-string (eager-evaluates lazy proxy).
    """
    from apps.products.models import ProductBrochure

    brand = _create_brand()
    product = _create_product(brand=brand, name="TB-804")
    brochure = ProductBrochure.objects.create(
        product=product, pdf_file=_pdf_stub(), title=""
    )
    result = str(brochure)
    # Format mora sadržati product.name + 'Brošura' substring
    assert "TB-804" in result, (
        f"ProductBrochure.__str__ fallback mora sadržati product.name 'TB-804', "
        f"dobio: {result!r}"
    )
    assert "Brošura" in result, (
        f"ProductBrochure.__str__ fallback mora sadržati 'Brošura' label, dobio: {result!r}"
    )


def test_product_brochure_cascades_when_product_deleted():
    """AC6: ProductBrochure.product on_delete=CASCADE.

    Koristi ContentFile PDF stub (pdf_file je REQUIRED FileField).
    """
    from apps.products.models import ProductBrochure

    brand = _create_brand()
    product = _create_product(brand=brand)
    ProductBrochure.objects.create(product=product, pdf_file=_pdf_stub("a.pdf"))
    ProductBrochure.objects.create(product=product, pdf_file=_pdf_stub("b.pdf"))
    assert ProductBrochure.objects.count() == 2

    product.delete()
    assert ProductBrochure.objects.count() == 0


def test_product_brochures_related_name_access():
    """AC6: ProductBrochure.product.related_name == 'brochures'."""
    from apps.products.models import ProductBrochure

    brand = _create_brand()
    product = _create_product(brand=brand)
    ProductBrochure.objects.create(product=product, pdf_file=_pdf_stub())
    assert product.brochures.count() == 1


# =============================================================================
# AC7 — ProductTestimonial model
# =============================================================================


def test_product_testimonial_str_returns_author_and_product():
    """AC7: ProductTestimonial.__str__ vraća '<author_name> — <product.name>'."""
    from apps.products.models import ProductTestimonial

    brand = _create_brand()
    product = _create_product(brand=brand, name="TB-804")
    testimonial = ProductTestimonial.objects.create(
        product=product, quote="Odličan!", author_name="Marko Marković"
    )
    assert str(testimonial) == "Marko Marković — TB-804"


def test_product_testimonial_cascades_when_product_deleted():
    """AC7: ProductTestimonial.product on_delete=CASCADE."""
    from apps.products.models import ProductTestimonial

    brand = _create_brand()
    product = _create_product(brand=brand)
    ProductTestimonial.objects.create(product=product, quote="Q1", author_name="A1")
    ProductTestimonial.objects.create(product=product, quote="Q2", author_name="A2")
    assert ProductTestimonial.objects.count() == 2

    product.delete()
    assert ProductTestimonial.objects.count() == 0


def test_product_testimonials_related_name_access():
    """AC7: ProductTestimonial.product.related_name == 'testimonials'."""
    from apps.products.models import ProductTestimonial

    brand = _create_brand()
    product = _create_product(brand=brand)
    ProductTestimonial.objects.create(product=product, quote="Q", author_name="A")
    assert product.testimonials.count() == 1


# =============================================================================
# AC8 — ProductSimilar model (CRITICAL — two distinct paths per IMP-iter4-4)
# =============================================================================


def test_product_similar_str_returns_arrow_format():
    """AC8: ProductSimilar.__str__ vraća '<product.name> → <related_product.name>'."""
    from apps.products.models import ProductSimilar

    brand = _create_brand()
    p1 = _create_product(brand=brand, name="P1")
    p2 = _create_product(brand=brand, name="P2")
    similar = ProductSimilar.objects.create(product=p1, related_product=p2)
    assert str(similar) == "P1 → P2"


def test_product_similar_clean_blocks_self_reference_when_full_clean_invoked():
    """AC8 / IMP-iter4-4 path 1: clean() raise-uje ValidationError za self-reference.

    Pattern: ProductSimilar(product=p, related_product=p).full_clean() — clean()
    se aktivira eksplicitno (Django default save() ga NE poziva). ValidationError
    bez polja → poruka pod __all__ key u message_dict.
    """
    from apps.products.models import ProductSimilar

    brand = _create_brand()
    product = _create_product(brand=brand)

    sim = ProductSimilar(product=product, related_product=product)
    with pytest.raises(ValidationError) as exc_info:
        sim.full_clean()

    # Per Dev Note "ProductSimilar save() bez full_clean() — dva test path-a":
    # membership assertion (NE equality)
    assert "__all__" in exc_info.value.message_dict, (
        f"ValidationError za self-reference MORA imati '__all__' key u message_dict "
        f"(ValidationError(_('...')) bez polja → Django stavlja pod __all__); "
        f"dobio keys: {list(exc_info.value.message_dict.keys())}"
    )


@pytest.mark.django_db(transaction=True)
def test_product_similar_db_check_constraint_blocks_self_reference_via_objects_create():
    """AC8 / IMP-iter4-4 path 2: DB-level CheckConstraint blokira self-reference.

    Pattern: ProductSimilar.objects.create(product=p, related_product=p) — bypass-uje
    clean() (Django default save() NE poziva full_clean()) i hita DB-level
    CheckConstraint `products_similar_no_self_reference` → IntegrityError.

    KRITIČNO: @pytest.mark.django_db(transaction=True) — bez ovog flag-a, IntegrityError
    može biti odložen do commit-a koji se nikad ne desi unutar test transaction wrapper-a.
    """
    from apps.products.models import ProductSimilar

    brand = _create_brand()
    product = _create_product(brand=brand)

    with pytest.raises(IntegrityError):
        ProductSimilar.objects.create(product=product, related_product=product)


@pytest.mark.django_db(transaction=True)
def test_product_similar_unique_constraint_blocks_duplicate_pair():
    """AC8: UniqueConstraint(product, related_product) blokira duplikat pair.

    Story spec: `products_similar_pair_unique` constraint.
    Drugi entry sa istim (product, related_product) → IntegrityError.
    """
    from apps.products.models import ProductSimilar

    brand = _create_brand()
    p1 = _create_product(brand=brand, name="P1")
    p2 = _create_product(brand=brand, name="P2")
    ProductSimilar.objects.create(product=p1, related_product=p2)

    with pytest.raises(IntegrityError):
        ProductSimilar.objects.create(product=p1, related_product=p2)


def test_product_similar_directional_allows_reciprocal_pair():
    """AC8 / PR-D5: relacija je directional (NE auto-simetrična).

    (A → B) i (B → A) su DVA odvojena entry-ja, NIJEDNO ne raise-uje.
    Admin u 8.6 može kreirati DVA entry-ja za simetričnu preporuku; model layer
    ne automatski reciprocates.
    """
    from apps.products.models import ProductSimilar

    brand = _create_brand()
    p1 = _create_product(brand=brand, name="P1")
    p2 = _create_product(brand=brand, name="P2")

    ProductSimilar.objects.create(product=p1, related_product=p2)
    ProductSimilar.objects.create(product=p2, related_product=p1)  # reciprocal — OK

    assert ProductSimilar.objects.count() == 2


def test_product_similar_outgoing_related_name_works():
    """AC8 / PR-D5: product.outgoing_similars.all() vraća rows gde je product=this.

    Semantika: "similar entry-ji KOJI POLAZE OD ovog proizvoda" (source).
    """
    from apps.products.models import ProductSimilar

    brand = _create_brand()
    p1 = _create_product(brand=brand, name="P1")
    p2 = _create_product(brand=brand, name="P2")
    p3 = _create_product(brand=brand, name="P3")
    ProductSimilar.objects.create(product=p1, related_product=p2)
    ProductSimilar.objects.create(product=p1, related_product=p3)
    ProductSimilar.objects.create(product=p2, related_product=p3)  # ne u p1.outgoing

    assert p1.outgoing_similars.count() == 2, (
        "p1.outgoing_similars mora vratiti rows gde je p1 source (2 entry-ja)."
    )


def test_product_similar_incoming_related_name_works():
    """AC8 / PR-D5: product.incoming_similars.all() vraća rows gde je related_product=this.

    Semantika: "similar entry-ji KOJI POKAZUJU NA ovog proizvoda" (target).
    """
    from apps.products.models import ProductSimilar

    brand = _create_brand()
    p1 = _create_product(brand=brand, name="P1")
    p2 = _create_product(brand=brand, name="P2")
    p3 = _create_product(brand=brand, name="P3")
    ProductSimilar.objects.create(product=p1, related_product=p3)
    ProductSimilar.objects.create(product=p2, related_product=p3)
    ProductSimilar.objects.create(product=p1, related_product=p2)  # ne u p3.incoming

    assert p3.incoming_similars.count() == 2, (
        "p3.incoming_similars mora vratiti rows gde je p3 target (2 entry-ja)."
    )


def test_product_similar_cascades_when_source_product_deleted():
    """AC8: brisanje source Product-a (product FK) briše outgoing_similars rows."""
    from apps.products.models import ProductSimilar

    brand = _create_brand()
    p1 = _create_product(brand=brand, name="P1")
    p2 = _create_product(brand=brand, name="P2")
    ProductSimilar.objects.create(product=p1, related_product=p2)
    assert ProductSimilar.objects.count() == 1

    p1.delete()
    assert ProductSimilar.objects.count() == 0, (
        "Brisanje p1 (source) mora CASCADE obrisati outgoing_similars rows."
    )


def test_product_similar_cascades_when_related_product_deleted():
    """AC8: brisanje target Product-a (related_product FK) briše incoming_similars rows."""
    from apps.products.models import ProductSimilar

    brand = _create_brand()
    p1 = _create_product(brand=brand, name="P1")
    p2 = _create_product(brand=brand, name="P2")
    ProductSimilar.objects.create(product=p1, related_product=p2)
    assert ProductSimilar.objects.count() == 1

    p2.delete()
    assert ProductSimilar.objects.count() == 0, (
        "Brisanje p2 (target) mora CASCADE obrisati incoming_similars rows."
    )


# =============================================================================
# AC9 — Translation registrations (6 modela; ProductSimilar IZUZET)
# =============================================================================


def test_translation_registrations_apply_to_six_models_excluding_product_similar():
    """AC9: translator.get_registered_models() uključuje 6 Product*-models; IZUZIMA ProductSimilar."""
    from modeltranslation.translator import translator

    from apps.products.models import (
        Product,
        ProductBrochure,
        ProductImage,
        ProductSimilar,
        ProductSpecification,
        ProductTestimonial,
        ProductVariant,
    )

    registered = set(translator.get_registered_models())

    expected_registered = {
        Product,
        ProductImage,
        ProductVariant,
        ProductSpecification,
        ProductBrochure,
        ProductTestimonial,
    }
    missing = expected_registered - registered
    assert not missing, (
        f"modeltranslation registracija nedostaje za: {missing}. Dev mora dodati "
        f"@register dekorator za sva 6 modela u apps/products/translation.py per AC9."
    )

    assert ProductSimilar not in registered, (
        "ProductSimilar NE SME biti registrovan u modeltranslation — nema "
        "translatable polja (per AC9 + PR-D7)."
    )


def test_product_translation_fields_include_name_description_key_features():
    """AC9: Product mora imati name_sr/hu/en, description_sr/hu/en, key_features_sr/hu/en."""
    from apps.products.models import Product

    field_names = {f.name for f in Product._meta.get_fields()}
    expected = set()
    for base in ("name", "description", "key_features"):
        for lang in ("sr", "hu", "en"):
            expected.add(f"{base}_{lang}")

    missing = expected - field_names
    assert not missing, (
        f"Product modeltranslation polja nedostaju: {missing}. Verifikuj da je "
        f"@register(Product) sa fields=('name', 'description', 'key_features') "
        f"u apps/products/translation.py per AC9."
    )


def test_product_image_translation_fields_include_alt_text():
    """AC9 / PR-D7: ProductImage mora imati alt_text_sr/hu/en."""
    from apps.products.models import ProductImage

    field_names = {f.name for f in ProductImage._meta.get_fields()}
    expected = {"alt_text_sr", "alt_text_hu", "alt_text_en"}
    missing = expected - field_names
    assert not missing, (
        f"ProductImage modeltranslation polja nedostaju: {missing}. Per PR-D7 "
        f"alt_text MORA biti translatable (a11y must-have)."
    )


def test_product_variant_translation_fields_include_name_and_description():
    """AC9 / PR-D7: ProductVariant mora imati name_sr/hu/en, description_sr/hu/en."""
    from apps.products.models import ProductVariant

    field_names = {f.name for f in ProductVariant._meta.get_fields()}
    expected = set()
    for base in ("name", "description"):
        for lang in ("sr", "hu", "en"):
            expected.add(f"{base}_{lang}")
    missing = expected - field_names
    assert not missing, f"ProductVariant modeltranslation polja nedostaju: {missing}"


def test_product_specification_translation_fields_include_key_and_value():
    """AC9: ProductSpecification mora imati key_sr/hu/en, value_sr/hu/en."""
    from apps.products.models import ProductSpecification

    field_names = {f.name for f in ProductSpecification._meta.get_fields()}
    expected = set()
    for base in ("key", "value"):
        for lang in ("sr", "hu", "en"):
            expected.add(f"{base}_{lang}")
    missing = expected - field_names
    assert not missing, (
        f"ProductSpecification modeltranslation polja nedostaju: {missing}"
    )


def test_product_brochure_translation_fields_include_title():
    """AC9: ProductBrochure mora imati title_sr/hu/en."""
    from apps.products.models import ProductBrochure

    field_names = {f.name for f in ProductBrochure._meta.get_fields()}
    expected = {"title_sr", "title_hu", "title_en"}
    missing = expected - field_names
    assert not missing, f"ProductBrochure modeltranslation polja nedostaju: {missing}"


def test_product_testimonial_translation_fields_include_quote_and_location():
    """AC9: ProductTestimonial mora imati quote_sr/hu/en, location_sr/hu/en."""
    from apps.products.models import ProductTestimonial

    field_names = {f.name for f in ProductTestimonial._meta.get_fields()}
    expected = set()
    for base in ("quote", "location"):
        for lang in ("sr", "hu", "en"):
            expected.add(f"{base}_{lang}")
    missing = expected - field_names
    assert not missing, (
        f"ProductTestimonial modeltranslation polja nedostaju: {missing}"
    )


def test_modeltranslation_fallback_to_sr_when_active_lang_empty():
    """AC9 / Task 1.4b / C3: pristup translated polju u praznoj 'hu' varijanti pada nazad na sr.

    Setup: name_sr='Original SR', name_hu='' (prazna varijanta). Sa aktivnim hu jezikom,
    pristup `product.name` (base accessor) MORA vratiti 'Original SR' kroz fallback chain
    (MODELTRANSLATION_FALLBACK_LANGUAGES=('sr',)), NE prazan string.
    """
    from django.utils import translation as django_translation

    brand = _create_brand()
    product = _create_product(brand=brand, name="Original SR")
    # Postavi sr varijantu eksplicitno, hu praznu
    product.name_sr = "Original SR"
    product.name_hu = ""
    product.save()

    with django_translation.override("hu"):
        # Base accessor sa active 'hu' bi vratilo name_hu (prazan) bez fallback-a;
        # MODELTRANSLATION_FALLBACK_LANGUAGES=('sr',) garantuje fallback na name_sr.
        product.refresh_from_db()
        assert product.name == "Original SR", (
            f"Base accessor sa active hu + prazan name_hu mora fallback-ovati na "
            f"name_sr='Original SR' (per MODELTRANSLATION_FALLBACK_LANGUAGES setting); "
            f"dobio: {product.name!r}."
        )


# =============================================================================
# AC10 — Migration smoke tests (table existence + translation columns)
# =============================================================================


def test_initial_migration_creates_seven_product_models():
    """AC10: Sva 7 modela su pristupačna preko ORM-a (tabele postoje, count() == 0)."""
    from apps.products.models import (
        Product,
        ProductBrochure,
        ProductImage,
        ProductSimilar,
        ProductSpecification,
        ProductTestimonial,
        ProductVariant,
    )

    # Sve count() pozive moraju proći bez OperationalError (table missing)
    assert Product.objects.count() == 0
    assert ProductImage.objects.count() == 0
    assert ProductVariant.objects.count() == 0
    assert ProductSpecification.objects.count() == 0
    assert ProductBrochure.objects.count() == 0
    assert ProductTestimonial.objects.count() == 0
    assert ProductSimilar.objects.count() == 0


def test_initial_migration_creates_translation_columns_for_eleven_fields_per_three_langs():
    """AC10 / PR-D7: Sva 11 translatable polja MORA imati _sr/_hu/_en variants u DB shemi.

    Aggregate sanity check protiv _meta.get_fields() across 6 modela.
    Expected: 33 dodatne translation kolone (11 polja × 3 jezika).
    """
    from apps.products.models import (
        Product,
        ProductBrochure,
        ProductImage,
        ProductSpecification,
        ProductTestimonial,
        ProductVariant,
    )

    translation_spec = {
        Product: ("name", "description", "key_features"),
        ProductImage: ("alt_text",),
        ProductVariant: ("name", "description"),
        ProductSpecification: ("key", "value"),
        ProductBrochure: ("title",),
        ProductTestimonial: ("quote", "location"),
    }

    total_polja = sum(len(fields) for fields in translation_spec.values())
    assert total_polja == 11, (
        f"PR-D7 spec definiše 11 translatable polja; test koverage: {total_polja}"
    )

    missing_columns: list[str] = []
    for model, fields in translation_spec.items():
        field_names = {f.name for f in model._meta.get_fields()}
        for base in fields:
            for lang in ("sr", "hu", "en"):
                col = f"{base}_{lang}"
                if col not in field_names:
                    missing_columns.append(f"{model.__name__}.{col}")

    assert not missing_columns, (
        f"Sledeće translation kolone nedostaju (Dev mora apply-ovati 0001_initial.py "
        f"posle translation.py registracije): {missing_columns}"
    )


# =============================================================================
# Krajnji smoke — orchestrated chain test
# =============================================================================


def test_full_cross_app_chain_creates_subcategory_chain_product_and_relateds():
    """Smoke: kreira full Brand → Series → Category → Subcategory → Product chain
    sa svim related entitetima (mirror Task 7.1 smoke u manual test).

    Verifikuje cross-app FK reachability bez direktnih import-a brands u products.
    """
    from apps.products.models import (
        ProductBrochure,
        ProductImage,
        ProductSimilar,
        ProductSpecification,
        ProductTestimonial,
        ProductVariant,
    )

    brand = _create_brand(name="Smoke Brand")
    series = _create_series(brand=brand, name="Smoke Series")
    category = _create_category(name="Smoke Category", is_for="traktori")
    subcategory = _create_subcategory(category=category, name="Smoke Subcat")

    product = _create_product(
        brand=brand,
        series=series,
        subcategory=subcategory,
        name="Smoke Product",
        key_features=["KF1", "KF2"],
        price_eur="12345.67",
        year=2024,
        horse_power=80,
    )

    # Child rows
    ProductImage.objects.create(product=product, image=_image_stub(), order=0)
    ProductVariant.objects.create(product=product, name="V1")
    ProductSpecification.objects.create(
        product=product, section="motor", key="K", value="V"
    )
    ProductBrochure.objects.create(product=product, pdf_file=_pdf_stub())
    ProductTestimonial.objects.create(product=product, quote="Q", author_name="A")

    # ProductSimilar — kreira drugi product za relaciju
    other = _create_product(brand=brand, name="Other Product")
    ProductSimilar.objects.create(product=product, related_product=other)

    # Verify reverse access kroz related_names
    assert brand.products.count() == 2  # smoke product + other
    assert series.products.count() == 1
    assert subcategory.products.count() == 1
    assert product.images.count() == 1
    assert product.variants.count() == 1
    assert product.specifications.count() == 1
    assert product.brochures.count() == 1
    assert product.testimonials.count() == 1
    assert product.outgoing_similars.count() == 1
    assert other.incoming_similars.count() == 1


# =============================================================================
# Code Review iter-1 follow-ups (R1-R4) — drift-prevention + branch coverage
# =============================================================================


def test_product_key_features_max_constant_is_three():
    """R1 / AC2: Pin _PRODUCT_KEY_FEATURES_MAX konstantu da sprečimo silent drift.

    Spec eksplicitno traži max 3 stavki — ako se constant promeni bez story update-a,
    ovaj test fail-uje i forsira eksplicitnu odluku.
    """
    from apps.products.models import _PRODUCT_KEY_FEATURES_MAX

    assert _PRODUCT_KEY_FEATURES_MAX == 3, (
        f"_PRODUCT_KEY_FEATURES_MAX MORA biti 3 per AC2 spec; "
        f"dobio: {_PRODUCT_KEY_FEATURES_MAX!r}. Bilo kakva promena zahteva story "
        f"spec update + design discussion."
    )


def test_product_meta_indexes_have_correct_field_order():
    """R2 / AC2: Composite index field order — bitan za Postgres leftmost-prefix scan.

    Imena polja (`fields=[...]`) MORA biti tačno u definisanom redosledu jer
    Postgres ne može efikasno scan-ovati composite index ako query filtrira na
    drugi/treći field bez leftmost-a. Test guard-uje protiv silent reorder-a.
    """
    from apps.products.models import Product

    indexes_by_name = {idx.name: idx for idx in Product._meta.indexes}
    assert indexes_by_name["products_product_brand_status_idx"].fields == [
        "brand",
        "status",
    ], (
        "products_product_brand_status_idx fields order MORA biti [brand, status] "
        "(brand leftmost — brand listing query po brendu je najfrekventniji)."
    )
    assert indexes_by_name["products_product_pub_created_idx"].fields == [
        "is_published",
        "-created_at",
    ], (
        "products_product_pub_created_idx fields order MORA biti "
        "[is_published, -created_at] (published filter + recent-first sort)."
    )
    assert indexes_by_name["products_product_condition_pub_idx"].fields == [
        "condition",
        "is_published",
    ], (
        "products_product_condition_pub_idx fields order MORA biti "
        "[condition, is_published] (condition leftmost — Novo/Polovno tab filtri)."
    )


@pytest.mark.parametrize(
    "model_name,expected_singular,expected_plural",
    [
        ("Product", "Proizvod", "Proizvodi"),
        ("ProductImage", "Slika proizvoda", "Slike proizvoda"),
        ("ProductVariant", "Varijanta", "Varijante"),
        ("ProductSpecification", "Specifikacija", "Specifikacije"),
        ("ProductBrochure", "Brošura", "Brošure"),
        ("ProductTestimonial", "Testimonijal", "Testimonijali"),
        ("ProductSimilar", "Sličan proizvod", "Slični proizvodi"),
    ],
)
def test_model_verbose_names_match_spec(model_name, expected_singular, expected_plural):
    """R3 / AC2-AC8: verbose_name + verbose_name_plural su locale-aware gettext_lazy.

    Admin label rendering (Story 2.6/8.6) zavisi od ovih vrednosti — ako neko
    rename-uje "Proizvod" → "Product", admin sidebar label se promeni neočekivano.
    Pin-uj actual vrednosti iz models.py.
    """
    from apps.products import models as products_models

    model = getattr(products_models, model_name)
    assert str(model._meta.verbose_name) == expected_singular, (
        f"{model_name}._meta.verbose_name MORA biti {expected_singular!r}; "
        f"dobio: {str(model._meta.verbose_name)!r}"
    )
    assert str(model._meta.verbose_name_plural) == expected_plural, (
        f"{model_name}._meta.verbose_name_plural MORA biti {expected_plural!r}; "
        f"dobio: {str(model._meta.verbose_name_plural)!r}"
    )


def test_product_clean_base_accessor_branch_is_present_in_source():
    """R4 / AC2: Belt-and-suspenders base accessor grana u Product.clean() postoji.

    EMPIRICAL NOTE (Code Review iter-1 R4 follow-up): pokušaj da se grana izvrši
    kroz `translation.override(None)` + `product.__dict__["key_features"] = ...`
    NE USPEVA jer modeltranslation descriptor uvek preusmerava read na sr-varijantu
    kroz `MODELTRANSLATION_FALLBACK_LANGUAGES = ('sr',)`. Branch je tehnički
    unreachable u produkcijskom Django flow-u (descriptor je transparent proxy).

    Branch ipak ostaje u izvornom kodu kao DEFENSIVE DOC za buduće promene
    (npr. ako se modeltranslation ukloni ili descriptor ponašanje promeni).
    Ovaj test pin-uje granu kao live source kod (AST presence check) kako se
    ne bi tiho izgubila kroz dead-code elimination refactor.
    """
    import inspect

    from apps.products.models import Product

    src = inspect.getsource(Product.clean)
    # Mora postojati base-accessor grana koja koristi self.key_features
    assert "self.key_features or []" in src, (
        "Product.clean() MORA imati base-accessor branch (self.key_features or [])"
        " kao belt-and-suspenders zaštitu. Branch je trenutno unreachable u "
        "produkciji ali ostaje kao defensive doc protiv buduće descriptor promene."
    )
    # Mora postojati ValidationError pod key 'key_features' (bez language suffix-a)
    assert '"key_features"' in src or "'key_features'" in src, (
        "Product.clean() base branch MORA raise ValidationError sa key 'key_features' "
        "(bez language suffix-a)."
    )
