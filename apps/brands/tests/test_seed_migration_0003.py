"""Story 2.10 — Data migracija 0003_seed_jeegee_and_prikljucna_categories tests (RED phase).

Pokriva AC7 — seed Jeegee Brand + 3 mehanizacija Category instance; idempotentnost
kroz get_or_create; reverse callable koji DELETE-uje samo te 4 instance po slug-u.

Test scope (4 tests):
- test_migration_creates_jeegee_brand_with_correct_fields
- test_migration_creates_3_mehanizacija_categories_with_correct_slugs
- test_migration_0003_idempotent_reapply
- test_migration_0003_reverse_callable_removes_seed

Pokrenuti sa:
    docker compose -f compose/local.yml exec django pytest \\
        apps/brands/tests/test_seed_migration_0003.py -v

Refs:
- 2-10-jeegee-prikljucna-mehanizacija-strana.md (AC7)
- 2-10-interface-contract.md (§ 6 Data migracija)
"""

from __future__ import annotations

import pytest

from apps.brands.models import Brand, Category

pytestmark = pytest.mark.django_db


def test_migration_creates_jeegee_brand_with_correct_fields():
    """AC7: pytest-django auto-applies 0003 → Jeegee Brand postoji sa očekivanim poljima.

    Verifikuje:
    - slug='jeegee'
    - name='Jeegee'
    - brand_color='#00A4E9' (uppercase per Story 2-1 hex regex accept-uje [0-9A-Fa-f])
    - is_coming_soon=False (default)
    """
    qs = Brand.objects.filter(slug="jeegee")
    assert qs.exists(), (
        "Jeegee Brand MORA postojati u DB posle pytest-django --create-db (0003 "
        "seed migracija automatski primenjena). Ako migracija ne postoji, Dev "
        "MORA kreirati apps/brands/migrations/0003_seed_jeegee_and_prikljucna_"
        "categories.py per AC7 spec."
    )
    jeegee = qs.get()

    assert jeegee.name == "Jeegee", (
        f"Jeegee Brand.name MORA biti 'Jeegee', dobio {jeegee.name!r}."
    )
    assert jeegee.brand_color == "#00A4E9", (
        f"Jeegee Brand.brand_color MORA biti '#00A4E9' (uppercase per 0003 seed; "
        f"Story 2-1 hex regex `^#[0-9A-Fa-f]{{6}}$` accept-uje uppercase). Dobio "
        f"{jeegee.brand_color!r}."
    )
    assert jeegee.is_coming_soon is False, (
        f"Jeegee Brand.is_coming_soon MORA biti False (default), dobio "
        f"{jeegee.is_coming_soon!r}."
    )


def test_migration_creates_3_mehanizacija_categories_with_correct_slugs():
    """AC7: 3 mehanizacija Category instance sa whitelist slug-ovima + display_order 10/20/30."""
    expected_categories = [
        {"slug": "osnovna-obrada-zemljista", "name": "Osnovna obrada zemljišta", "display_order": 10},
        {"slug": "priprema-zemljista", "name": "Priprema zemljišta", "display_order": 20},
        {"slug": "masine-za-setvu", "name": "Mašine za setvu", "display_order": 30},
    ]

    for expected in expected_categories:
        qs = Category.objects.filter(slug=expected["slug"])
        assert qs.exists(), (
            f"Category slug={expected['slug']!r} MORA postojati u DB posle 0003 "
            f"migracije."
        )
        category = qs.get()
        assert category.is_for == "mehanizacija", (
            f"Category slug={expected['slug']!r} is_for MORA biti 'mehanizacija', "
            f"dobio {category.is_for!r}."
        )
        assert category.name == expected["name"], (
            f"Category slug={expected['slug']!r} name MORA biti "
            f"{expected['name']!r}, dobio {category.name!r}."
        )
        assert category.display_order == expected["display_order"], (
            f"Category slug={expected['slug']!r} display_order MORA biti "
            f"{expected['display_order']}, dobio {category.display_order}."
        )
        assert category.icon == "", (
            f"Category slug={expected['slug']!r} icon MORA biti empty string "
            f"(Bootstrap Icons font deferred per SM-D18), dobio {category.icon!r}."
        )

    # Verifikuj UKUPNO 3 mehanizacija kategorije seed-ovano (whitelist only)
    seeded_slugs = {
        "osnovna-obrada-zemljista",
        "priprema-zemljista",
        "masine-za-setvu",
    }
    actual_mehanizacija_slugs = set(
        Category.objects.filter(
            is_for="mehanizacija",
            slug__in=seeded_slugs,
        ).values_list("slug", flat=True)
    )
    assert actual_mehanizacija_slugs == seeded_slugs, (
        f"Seed migracija MORA kreirati TAČNO 3 mehanizacija kategorije "
        f"{seeded_slugs!r}, dobio {actual_mehanizacija_slugs!r}."
    )


def test_migration_0003_idempotent_reapply():
    """AC7: re-running seed callable NE baca IntegrityError + ne kreira duplikate.

    Direktno poziva migration callable funkciju 2 puta zaredom; verifikuje:
    - NEMA IntegrityError (idempotent get_or_create discipline)
    - Broj Brand + Category instance NEPROMENJEN
    """
    # Direktan import migration callable (zaobilazi MigrationExecutor — testira
    # `seed_jeegee_and_categories` funkciju sa apps.get_model() pattern-om)
    from importlib import import_module

    try:
        migration_module = import_module(
            "apps.brands.migrations.0003_seed_jeegee_and_prikljucna_categories"
        )
    except ImportError:
        pytest.fail(
            "Migration modul "
            "'apps.brands.migrations.0003_seed_jeegee_and_prikljucna_categories' "
            "nije pronađen. Dev MORA kreirati ovu migraciju per AC7 spec."
        )

    # Inicialno stanje (posle prvog automatic apply-a)
    initial_brand_count = Brand.objects.filter(slug="jeegee").count()
    initial_category_count = Category.objects.filter(
        slug__in=[
            "osnovna-obrada-zemljista",
            "priprema-zemljista",
            "masine-za-setvu",
        ]
    ).count()
    assert initial_brand_count == 1
    assert initial_category_count == 3

    # Re-apply seed callable manualno (simulira double-run scenario)
    from django.apps import apps as django_apps

    # Wrapper imitating Django migration framework — passes apps registry (historical
    # snapshot via test stub).
    class _StubSchemaEditor:
        pass

    try:
        migration_module.seed_jeegee_and_categories(django_apps, _StubSchemaEditor())
    except Exception as exc:
        pytest.fail(
            f"Re-pokretanje seed callable funkcije NE SME bacati exception "
            f"(idempotent get_or_create discipline). Dobijen: {exc!r}"
        )

    # Posle re-run-a, BROJ instance NEPROMENJEN
    assert Brand.objects.filter(slug="jeegee").count() == initial_brand_count, (
        "Re-running seed callable NE SME kreirati duplikate Brand-a."
    )
    assert (
        Category.objects.filter(
            slug__in=[
                "osnovna-obrada-zemljista",
                "priprema-zemljista",
                "masine-za-setvu",
            ]
        ).count()
        == initial_category_count
    ), "Re-running seed callable NE SME kreirati duplikate Category-ja."


def test_migration_0003_reverse_callable_removes_seed():
    """AC7: reverse_seed callable obrisi sva 4 instance (Jeegee Brand + 3 Category).

    Direktno poziva `reverse_seed` funkciju; verifikuje:
    - Jeegee Brand obrisan
    - 3 mehanizacija Category obrisane
    - Druge Brand/Category instance OSTAJU netaknute (slug-based filter discipline)
    """
    from importlib import import_module

    try:
        migration_module = import_module(
            "apps.brands.migrations.0003_seed_jeegee_and_prikljucna_categories"
        )
    except ImportError:
        pytest.fail(
            "Migration modul 0003 nije pronađen — Dev MORA kreirati per AC7 spec."
        )

    # Kreiraj non-seeded brand + category koji NE SME biti obrisan reverse-om
    # (DB side-effect je sustina testa; binding se ne koristi — kasnije se proverava slug filterom)
    Brand.objects.create(name="Other Brand", slug="other-brand", brand_color="")
    Category.objects.create(
        name="Other Category",
        slug="other-category",
        is_for=Category.CategoryScope.TRAKTORI,
        display_order=0,
    )

    # Reverse seed
    from django.apps import apps as django_apps

    class _StubSchemaEditor:
        pass

    migration_module.reverse_seed(django_apps, _StubSchemaEditor())

    # Jeegee + 3 Category obrisane
    assert not Brand.objects.filter(slug="jeegee").exists(), (
        "Reverse migracija MORA obrisati Jeegee Brand."
    )
    assert (
        not Category.objects.filter(
            slug__in=[
                "osnovna-obrada-zemljista",
                "priprema-zemljista",
                "masine-za-setvu",
            ]
        ).exists()
    ), "Reverse migracija MORA obrisati svih 3 seeded mehanizacija Category-ja."

    # Druge instance OSTAJU netaknute (slug-based filter discipline)
    assert Brand.objects.filter(slug="other-brand").exists(), (
        "Reverse migracija NE SME obrisati Brand-ove koji NISU seeded."
    )
    assert Category.objects.filter(slug="other-category").exists(), (
        "Reverse migracija NE SME obrisati Category-je koji NISU seeded."
    )
