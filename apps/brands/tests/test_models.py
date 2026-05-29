"""Story 2.1 — apps/brands/models.py testovi (RED phase TDD).

Pokriva AC2-AC5, AC11 — Brand, Series, Category, Subcategory modeli.

Test scope:
- __str__ za sva 4 modela
- FK on_delete (PROTECT za Series.brand; CASCADE za Subcategory.category/parent)
- save() auto-slug pattern (CRIT-2 iter-2 fix)
- save() slug ASCII transliteration (BR-14 regression guard)
- Subcategory depth validation (3 OK, 4 raises ValidationError)
- Brand brand_color hex validation (CRIT-3: empty passes)
- Brand statistics list-of-dict soft validation (IMP-10)
- get_absolute_url() — Brand (skipped, URL not in 2.1) + Subcategory (NotImplementedError)

Naming: srpska latinica + engleski code identifiers.
TEA RED phase: svi testovi MORAJU pasti dok Dev ne implementira modele.

Pokrenuti sa:
    uv run pytest apps/brands/tests/test_models.py -v
"""

from __future__ import annotations

import pytest
from django.core.exceptions import ValidationError
from django.db.models import ProtectedError

# Svi testovi u ovom modulu koriste DB
pytestmark = pytest.mark.django_db


# =============================================================================
# Helpers
# =============================================================================


def _make_brand(**overrides):
    """Factory za Brand sa default validnim poljima."""
    from apps.brands.models import Brand

    defaults = {
        "name": "Test Brand",
        "brand_color": "",
        "statistics": [],
    }
    defaults.update(overrides)
    return Brand.objects.create(**defaults)


def _make_category(**overrides):
    from apps.brands.models import Category

    defaults = {
        "name": "Test Category",
        "is_for": "mehanizacija",
    }
    defaults.update(overrides)
    return Category.objects.create(**defaults)


# =============================================================================
# AC2 — Brand __str__
# =============================================================================


def test_brand_str_returns_name():
    """Brand.__str__ vraća self.name."""
    brand = _make_brand(name="John Deere")
    assert str(brand) == "John Deere"


# =============================================================================
# AC3 — Series __str__
# =============================================================================


def test_series_str_returns_brand_name_em_dash_series_name():
    """Series.__str__ vraća '<brand_name> — <series_name>' (em-dash)."""
    from apps.brands.models import Series

    brand = _make_brand(name="John Deere")
    series = Series.objects.create(brand=brand, name="TB-Serija")
    assert str(series) == "John Deere — TB-Serija"


# =============================================================================
# AC4 — Category __str__
# =============================================================================


def test_category_str_returns_scope_em_dash_name():
    """Category.__str__ vraća '<is_for_display> — <name>'."""
    category = _make_category(name="Priključna mehanizacija", is_for="mehanizacija")
    # get_is_for_display() vraća labelu, koja je translatable
    result = str(category)
    assert "—" in result, f"Category __str__ mora sadržati em-dash, dobio: {result!r}"
    assert "Priključna mehanizacija" in result


# =============================================================================
# AC5 — Subcategory __str__
# =============================================================================


def test_subcategory_str_returns_name():
    """Subcategory.__str__ vraća self.name (BEZ category prefix)."""
    from apps.brands.models import Subcategory

    cat = _make_category()
    sub = Subcategory.objects.create(category=cat, name="Osnovna obrada")
    assert str(sub) == "Osnovna obrada"


# =============================================================================
# AC3 — Series.brand on_delete=PROTECT
# =============================================================================


def test_series_brand_protect_on_delete():
    """Brisanje Brand-a sa Series mora raise-ovati ProtectedError."""
    from apps.brands.models import Series

    brand = _make_brand()
    Series.objects.create(brand=brand, name="Test Series")

    with pytest.raises(ProtectedError):
        brand.delete()


# =============================================================================
# AC5 — Subcategory.category on_delete=CASCADE
# =============================================================================


def test_subcategory_category_cascade_on_delete():
    """Brisanje Category mora kaskadno obrisati Subcategory pod njom."""
    from apps.brands.models import Subcategory

    cat = _make_category()
    Subcategory.objects.create(category=cat, name="Plugovi")

    cat.delete()
    assert Subcategory.objects.count() == 0, (
        "Subcategory mora biti CASCADE obrisana sa Category."
    )


def test_subcategory_parent_cascade_on_delete():
    """Brisanje parent Subcategory kaskadno briše children chain."""
    from apps.brands.models import Subcategory

    cat = _make_category()
    l1 = Subcategory.objects.create(category=cat, name="L1")
    l2 = Subcategory.objects.create(category=cat, parent=l1, name="L2")
    Subcategory.objects.create(category=cat, parent=l2, name="L3")

    assert Subcategory.objects.count() == 3
    l1.delete()
    assert Subcategory.objects.count() == 0, (
        "Brisanje parent Subcategory mora CASCADE obrisati ceo subtree."
    )


# =============================================================================
# save() auto-slug pattern (CRIT-2 iter-2)
# =============================================================================


def test_brand_save_auto_generates_slug_from_name():
    """Brand bez explicit slug → save() auto-generiše slug iz name."""
    from apps.brands.models import Brand

    brand = Brand(name="John Deere", brand_color="", statistics=[])
    brand.save()
    assert brand.slug == "john-deere", (
        f"Auto-generated slug mora biti 'john-deere', dobio: {brand.slug!r}"
    )


def test_brand_save_preserves_explicit_slug():
    """Eksplicitni slug se ne overwrite-uje u save()."""
    from apps.brands.models import Brand

    brand = Brand(
        name="Whatever",
        slug="custom-slug",
        brand_color="",
        statistics=[],
    )
    brand.save()
    assert brand.slug == "custom-slug", (
        f"Explicit slug mora biti preserved, dobio: {brand.slug!r}"
    )


def test_series_save_auto_generates_slug_from_name():
    """Series bez explicit slug → auto-generiše iz name."""
    from apps.brands.models import Series

    brand = _make_brand()
    series = Series(brand=brand, name="TB-Serija")
    series.save()
    assert series.slug == "tb-serija"


def test_category_save_auto_generates_slug_from_name():
    """Category bez explicit slug → auto-generiše iz name."""
    from apps.brands.models import Category

    cat = Category(name="Priključna mehanizacija", is_for="mehanizacija")
    cat.save()
    assert cat.slug == "prikljucna-mehanizacija"


def test_subcategory_save_auto_generates_slug_from_name():
    """Subcategory bez explicit slug → auto-generiše iz name."""
    from apps.brands.models import Subcategory

    cat = _make_category()
    sub = Subcategory(category=cat, name="Osnovna obrada")
    sub.save()
    assert sub.slug == "osnovna-obrada"


# =============================================================================
# save() slug ASCII transliteration (BR-14 regression guard)
# =============================================================================


def test_brand_save_slugifies_diakritici():
    """Srpska dijakritici u name → ASCII slug."""
    brand = _make_brand(name="Čorić Agrar")
    assert brand.slug == "coric-agrar", (
        f"Dijakritici moraju biti transliterisani, slug={brand.slug!r}"
    )


def test_category_save_slugifies_digraphs():
    """Digrafovi (Dž/Lj/Nj) u name → ASCII slug."""
    cat = _make_category(name="Plugovi Đak Džon")
    # "Plugovi Đak Džon" → "plugovi dak dzon" → "plugovi-dak-dzon"
    assert cat.slug == "plugovi-dak-dzon", (
        f"Digrafovi moraju biti transliterisani, slug={cat.slug!r}"
    )


# =============================================================================
# AC5 — Subcategory depth validation (Decision D4)
# =============================================================================


def test_subcategory_3_levels_allowed():
    """L1 → L2 → L3 chain — sva 3 save() bez ValidationError."""
    from apps.brands.models import Subcategory

    cat = _make_category()
    l1 = Subcategory.objects.create(category=cat, name="L1")
    l2 = Subcategory.objects.create(category=cat, parent=l1, name="L2")
    l3 = Subcategory.objects.create(category=cat, parent=l2, name="L3")

    # Eksplicitni full_clean() na L3 ne sme raise-ovati
    l3.full_clean()


def test_subcategory_4th_level_raises_validation_error():
    """L1 → L2 → L3 → L4 — 4. nivo mora raise-ovati ValidationError."""
    from apps.brands.models import Subcategory

    cat = _make_category()
    l1 = Subcategory.objects.create(category=cat, name="L1")
    l2 = Subcategory.objects.create(category=cat, parent=l1, name="L2")
    l3 = Subcategory.objects.create(category=cat, parent=l2, name="L3")

    with pytest.raises(ValidationError):
        Subcategory.objects.create(category=cat, parent=l3, name="L4")


# =============================================================================
# AC2 — Brand.brand_color validation
# =============================================================================


def test_brand_color_valid_hex_passes():
    """Validan hex (#RRGGBB) ne raise-uje ValidationError."""
    brand = _make_brand(brand_color="#25402F")
    # save() poziva full_clean() pa ako prošlo — OK
    brand.full_clean()


def test_brand_color_invalid_format_raises():
    """Non-hex value raise-uje ValidationError u clean()."""
    from apps.brands.models import Brand

    brand = Brand(name="X", brand_color="abc123", statistics=[])
    with pytest.raises(ValidationError):
        brand.full_clean()


def test_brand_color_empty_passes_validation():
    """blank=True mora biti honored — empty string ne raise-uje (CRIT-3 fix)."""
    from apps.brands.models import Brand

    brand = Brand(name="X", brand_color="", statistics=[])
    # full_clean() mora proći — blank=True honor
    brand.full_clean()


# =============================================================================
# AC2 — Brand.statistics list-of-dict validation (IMP-10)
# =============================================================================


def test_brand_statistics_list_of_dict_passes():
    """Valid list of dict-a ne raise-uje."""
    from apps.brands.models import Brand

    brand = Brand(
        name="X",
        brand_color="",
        statistics=[
            {"icon": "tractor", "value": 5000, "label": "Prodatih"},
            {"icon": "users", "value": 1000, "label": "Klijenata"},
        ],
    )
    brand.full_clean()


def test_brand_statistics_non_list_raises():
    """Non-list statistics → ValidationError."""
    from apps.brands.models import Brand

    brand = Brand(name="X", brand_color="", statistics="not a list")
    with pytest.raises(ValidationError):
        brand.full_clean()


def test_brand_statistics_non_dict_items_raises():
    """List sa non-dict stavkom → ValidationError."""
    from apps.brands.models import Brand

    brand = Brand(
        name="X",
        brand_color="",
        statistics=[{"icon": "tractor"}, "not a dict"],
    )
    with pytest.raises(ValidationError):
        brand.full_clean()


# =============================================================================
# get_absolute_url() — Gotcha BR-4 / BR-12
# =============================================================================


@pytest.mark.skip(reason="URLs come in Story 2.6 — placeholder validates method exists")
def test_brand_get_absolute_url_returns_path():
    """Brand.get_absolute_url() vraća string path.

    Skip dok URL pattern ne postoji (Story 2.6).
    """
    brand = _make_brand()
    url = brand.get_absolute_url()
    assert isinstance(url, str)


def test_subcategory_get_absolute_url_raises_not_implemented():
    """Subcategory.get_absolute_url() raise-uje NotImplementedError u 2.1 (BR-12)."""
    from apps.brands.models import Subcategory

    cat = _make_category()
    sub = Subcategory.objects.create(category=cat, name="Test")

    with pytest.raises(NotImplementedError):
        sub.get_absolute_url()


# =============================================================================
# AC11 — Subcategory helper metode get_depth() i get_ancestors_chain()
# =============================================================================


def test_subcategory_get_depth_returns_chain_length():
    """Subcategory.get_depth() vraća dubinu u chain-u; top-level = 1, L3 = 3."""
    from apps.brands.models import Subcategory

    cat = _make_category()
    l1 = Subcategory.objects.create(category=cat, name="L1")
    l2 = Subcategory.objects.create(category=cat, parent=l1, name="L2")
    l3 = Subcategory.objects.create(category=cat, parent=l2, name="L3")

    assert l1.get_depth() == 1, f"Top-level Subcategory depth mora biti 1, dobio: {l1.get_depth()}"
    assert l2.get_depth() == 2, f"L2 depth mora biti 2, dobio: {l2.get_depth()}"
    assert l3.get_depth() == 3, f"L3 depth mora biti 3, dobio: {l3.get_depth()}"


def test_subcategory_get_ancestors_chain_returns_ordered_list():
    """get_ancestors_chain() vraća listu od root-to-direct-parent (BEZ self).

    Za L3 chain (L1 → L2 → L3), L3.get_ancestors_chain() mora vratiti [L1, L2]
    (reverse-chronological — root first, direct parent last).
    """
    from apps.brands.models import Subcategory

    cat = _make_category()
    l1 = Subcategory.objects.create(category=cat, name="L1")
    l2 = Subcategory.objects.create(category=cat, parent=l1, name="L2")
    l3 = Subcategory.objects.create(category=cat, parent=l2, name="L3")

    chain = l3.get_ancestors_chain()
    assert chain == [l1, l2], (
        f"get_ancestors_chain() mora vratiti [L1, L2] (root-first), dobio: {chain!r}"
    )

    # Top-level — chain mora biti prazna lista
    assert l1.get_ancestors_chain() == [], (
        f"Top-level Subcategory.get_ancestors_chain() mora biti [], dobio: {l1.get_ancestors_chain()!r}"
    )


# =============================================================================
# AC2 — Brand.statistics MAX 4 entries (clean() validation)
# =============================================================================


def test_brand_statistics_max_4_entries_passes():
    """List od 4 dict-a u statistics ne raise-uje."""
    from apps.brands.models import Brand

    brand = Brand(
        name="X",
        brand_color="",
        statistics=[
            {"icon": "a", "value": 1, "label": "a"},
            {"icon": "b", "value": 2, "label": "b"},
            {"icon": "c", "value": 3, "label": "c"},
            {"icon": "d", "value": 4, "label": "d"},
        ],
    )
    brand.full_clean()


def test_brand_statistics_5_entries_raises():
    """List od 5+ dict-a u statistics raise-uje ValidationError (AC2)."""
    from apps.brands.models import Brand

    brand = Brand(
        name="X",
        brand_color="",
        statistics=[
            {"icon": "a", "value": 1, "label": "a"},
            {"icon": "b", "value": 2, "label": "b"},
            {"icon": "c", "value": 3, "label": "c"},
            {"icon": "d", "value": 4, "label": "d"},
            {"icon": "e", "value": 5, "label": "e"},
        ],
    )
    with pytest.raises(ValidationError):
        brand.full_clean()


# =============================================================================
# AC5 — Subcategory circular reference guard (visited_ids set)
# =============================================================================


def test_subcategory_circular_reference_raises_validation_error():
    """Manualno postavljanje subcat.parent = subcat raise-uje ValidationError.

    Circular reference može nastati samo manualno (admin ne dozvoljava self-FK
    selekciju na sopstveni record), ali shell + bulk_update mogu zaobići to.
    visited_ids set u clean() detektuje cikličnu referencu i blokira save.
    """
    from apps.brands.models import Subcategory

    cat = _make_category()
    sub = Subcategory.objects.create(category=cat, name="Sub")

    # Manual circular reference: sub.parent = sub
    sub.parent = sub
    with pytest.raises(ValidationError):
        sub.full_clean()


# =============================================================================
# AC12 mandate: slug uniqueness regression tests (Dev Review iter-1 fix)
# =============================================================================


def test_brand_slug_globally_unique():
    """AC2: Brand.slug je globally unique → ValidationError od full_clean() ili IntegrityError od DB."""
    from django.db import IntegrityError

    from apps.brands.models import Brand

    _make_brand(name="John Deere")
    # save() override calls full_clean() first → ValidationError; DB constraint = IntegrityError
    with pytest.raises((ValidationError, IntegrityError)):
        Brand.objects.create(
            name="John Deere Mirror",
            slug="john-deere",
            brand_color="#000000",
            statistics=[],
        )


def test_series_slug_unique_per_brand():
    """AC3: Series.slug je unique PER-brand (UniqueConstraint)."""
    from django.db import IntegrityError

    from apps.brands.models import Series

    b1 = _make_brand(name="Brand1")
    b2 = _make_brand(name="Brand2")
    Series.objects.create(brand=b1, name="Series1", slug="s1", layout_mode="grid")
    # save() override → full_clean() catches UniqueConstraint as ValidationError
    with pytest.raises((ValidationError, IntegrityError)):
        Series.objects.create(brand=b1, name="Series2", slug="s1", layout_mode="grid")
    # Same slug, different brand → OK (no error)
    Series.objects.create(brand=b2, name="Series3", slug="s1", layout_mode="grid")


def test_subcategory_slug_unique_per_category_with_explicit_parent():
    """AC5: Subcategory.slug je unique PER (category, parent) — sa explicit parent (NULL parent
    je Postgres NULL != NULL edge case, dokumentovan u Dev B review B-5).
    """
    from django.db import IntegrityError

    from apps.brands.models import Category, Subcategory

    cat = Category.objects.create(name="Cat1", slug="cat1", is_for="traktori")
    parent = Subcategory.objects.create(category=cat, name="Parent", slug="parent")
    Subcategory.objects.create(category=cat, parent=parent, name="Sub1", slug="s1")
    # save() override → ValidationError; DB → IntegrityError
    with pytest.raises((ValidationError, IntegrityError)):
        Subcategory.objects.create(category=cat, parent=parent, name="Sub2", slug="s1")


def test_category_is_for_invalid_choice_raises():
    """AC4: Category.is_for must be 'traktori' or 'mehanizacija' — invalid → ValidationError."""
    from apps.brands.models import Category

    cat = Category(name="X", slug="x", is_for="invalid")
    with pytest.raises(ValidationError):
        cat.full_clean()


def test_brand_series_related_name_access():
    """AC3: Brand.series related_name accessor returns associated Series."""
    from apps.brands.models import Series

    b = _make_brand(name="Brand1")
    Series.objects.create(brand=b, name="S1", slug="s1", layout_mode="grid")
    Series.objects.create(brand=b, name="S2", slug="s2", layout_mode="grid")
    assert b.series.count() == 2


def test_category_subcategories_related_name_access():
    """AC4/AC5: Category.subcategories related_name accessor."""
    from apps.brands.models import Category, Subcategory

    cat = Category.objects.create(name="Cat1", slug="cat1", is_for="traktori")
    Subcategory.objects.create(category=cat, name="Sub1", slug="s1")
    Subcategory.objects.create(category=cat, name="Sub2", slug="s2")
    assert cat.subcategories.count() == 2


def test_subcategory_children_related_name_access():
    """AC5: Subcategory.children self-FK related_name accessor."""
    from apps.brands.models import Category, Subcategory

    cat = Category.objects.create(name="Cat1", slug="cat1", is_for="traktori")
    parent = Subcategory.objects.create(category=cat, name="Parent", slug="parent")
    Subcategory.objects.create(category=cat, parent=parent, name="Child1", slug="c1")
    Subcategory.objects.create(category=cat, parent=parent, name="Child2", slug="c2")
    assert parent.children.count() == 2
