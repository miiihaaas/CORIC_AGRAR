"""Story 2.13 — AC2 search_vector field + GIN indeks + migration ordering (TEA RED).

⚠️ AC2 JE STRUKTURNA (schema introspection), NE runtime (AC2 fix u story):
Ovi testovi dokazuju SAMO da `search_vector` kolona + `products_search_gin` GIN indeks
+ unaccent/pg_trgm extension POSTOJE u schemi i da je migration dependency lanac
0003 → 0004a → 0004. AC2 NE dokazuje da runtime upit koristi kolonu (kolona je UVEK
NULL u v1; runtime ide kroz annotation alias — vidi test_search_query.py AC3/AC4 + SM-D8).

Pokrenuti sa:
    docker compose -f compose/local.yml exec django uv run pytest \\
        apps/search/tests/test_migrations.py -v

Refs:
- 2-13-global-search-sa-postgresql-fts.md AC2 + Task 2 + SM-D7/D8/D20
- 2-13-interface-contract.md § 2 (models.py) + § 3 (Migration surface)
"""

from __future__ import annotations

import pytest

# DB-introspekcija testovi (pg_indexes/information_schema/pg_extension cursor + makemigrations
# --check) zahtevaju DB pristup → django_db mark uz requires_postgres. Bez django_db-a pytest
# diže RuntimeError "Database access not allowed" (genuine test bug — TEA RED je propustio mark).
pytestmark = [pytest.mark.requires_postgres, pytest.mark.django_db]


# AC2: search_vector field postoji na Product (SearchVectorField, null=True, editable=False)
def test_product_has_search_vector_field():
    from django.contrib.postgres.search import SearchVectorField

    from apps.products.models import Product

    field = Product._meta.get_field("search_vector")
    assert isinstance(field, SearchVectorField), (
        f"Product.search_vector MORA biti SearchVectorField, dobio {type(field).__name__}."
    )
    assert field.null is True, "search_vector MORA biti null=True (SM-D8 — nematerijalizovan u v1)."
    assert field.editable is False, "search_vector MORA biti editable=False (ne u admin formi)."


# AC2: GIN indeks `products_search_gin` postoji na Product.Meta.indexes (ime ≤30 char, SM-D20/C1)
def test_product_has_products_search_gin_index():
    from django.contrib.postgres.indexes import GinIndex

    from apps.products.models import Product

    gin_indexes = [
        idx for idx in Product._meta.indexes
        if idx.name == "products_search_gin"
    ]
    assert gin_indexes, (
        "Product.Meta.indexes MORA sadržati indeks po imenu 'products_search_gin' "
        f"(SM-D20). Pronađeni indeksi: {[i.name for i in Product._meta.indexes]}."
    )
    gin = gin_indexes[0]
    assert isinstance(gin, GinIndex), (
        f"'products_search_gin' MORA biti GinIndex (NE models.Index), dobio "
        f"{type(gin).__name__} (SM-D20 — NE _ProductIndex subclass)."
    )
    assert gin.fields == ["search_vector"], (
        f"GIN indeks MORA pokrivati ['search_vector'], dobio {gin.fields}."
    )


# AC2/SM-D20: GIN ime ≤ Django Index.max_name_length = 30 char (NE products_product_search_gin)
def test_gin_index_name_within_django_max_name_length():
    """Stvarni GIN indeks na modelu MORA imati ime ≤30 char (SM-D20).

    Deriva ime iz Product._meta (ne hardcoded literal) — genuinely fails u RED dok
    search_vector GIN indeks ne postoji; štiti od regresije ka predugačkom imenu
    (products_product_search_gin = 34 char → models.E033).
    """
    from django.contrib.postgres.indexes import GinIndex

    from apps.products.models import Product

    gin = next(
        (idx for idx in Product._meta.indexes if isinstance(idx, GinIndex)),
        None,
    )
    assert gin is not None, (
        "Product.Meta.indexes MORA sadržati GinIndex (search_vector). Nije pronađen — "
        "search_vector GIN indeks još ne postoji (RED)."
    )
    assert len(gin.name) <= 30, (
        f"GIN ime {gin.name!r} ({len(gin.name)} char) MORA biti ≤30 (Django "
        "Index.max_name_length). NE 'products_product_search_gin' (34 char → models.E033)."
    )
    assert gin.name == "products_search_gin", (
        f"Autoritativno GIN ime je 'products_search_gin' (SM-D20), dobio {gin.name!r}."
    )


# AC2: GIN kolona stvarno postoji u DB schemi (PostgreSQL introspekcija)
def test_products_search_gin_index_exists_in_db_schema():
    from django.db import connection

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT indexname FROM pg_indexes "
            "WHERE tablename = %s AND indexname = %s;",
            ["products_product", "products_search_gin"],
        )
        row = cursor.fetchone()
    assert row is not None, (
        "GIN indeks 'products_search_gin' MORA postojati u pg_indexes na tabeli "
        "products_product (AddIndex u migraciji 0004)."
    )


# AC2: search_vector kolona postoji u DB schemi
def test_search_vector_column_exists_in_db_schema():
    from django.db import connection

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = %s AND column_name = %s;",
            ["products_product", "search_vector"],
        )
        row = cursor.fetchone()
    assert row is not None, (
        "Kolona 'search_vector' MORA postojati u products_product tabeli (AddField 0004)."
    )


# AC2: unaccent + pg_trgm extension enabled (0004a CREATE EXTENSION)
@pytest.mark.parametrize("extension", ["unaccent", "pg_trgm"])
def test_postgres_extension_enabled(extension):
    from django.db import connection

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT 1 FROM pg_extension WHERE extname = %s;", [extension]
        )
        row = cursor.fetchone()
    assert row is not None, (
        f"PostgreSQL extension '{extension}' MORA biti enabled (migracija 0004a — "
        "CREATE EXTENSION / UnaccentExtension/TrigramExtension)."
    )


# AC2/SM-D7: migration dependency lanac 0003 → 0004a → 0004 (extension PRE AddIndex)
def test_migration_dependency_chain_0003_0004a_0004():
    from django.db.migrations.loader import MigrationLoader

    loader = MigrationLoader(connection=None, ignore_no_migrations=True)
    keys = {key for key in loader.disk_migrations if key[0] == "products"}
    names = {name for (_app, name) in keys}

    # 0004a (extension) MORA postojati
    a_names = [n for n in names if n.startswith("0004a")]
    assert a_names, (
        "Extension migracija 0004a_* MORA postojati (SM-D7). Pronađene products migracije: "
        f"{sorted(names)}."
    )
    a_name = a_names[0]

    # 0004 schema migracija (AddField + AddIndex) MORA postojati
    schema_names = [
        n for n in names if n.startswith("0004") and not n.startswith("0004a")
    ]
    assert schema_names, (
        f"Schema migracija 0004_* (AddField search_vector + AddIndex GIN) MORA postojati. "
        f"Pronađene: {sorted(names)}."
    )
    schema_name = schema_names[0]

    # 0004a MORA zavisiti od 0003
    a_deps = loader.disk_migrations[("products", a_name)].dependencies
    assert ("products", "0003_alter_productvariant_description_and_more") in a_deps, (
        f"{a_name} MORA imati dependency na products.0003_alter_productvariant_description_and_more "
        f"(SM-D7). Dobio: {a_deps}."
    )

    # 0004 MORA zavisiti od 0004a (extension PRE AddField/AddIndex)
    schema_deps = loader.disk_migrations[("products", schema_name)].dependencies
    assert ("products", a_name) in schema_deps, (
        f"{schema_name} MORA imati dependency na {a_name} (extension PRE AddField/AddIndex — "
        f"SM-D7). Dobio: {schema_deps}."
    )


# AC2: makemigrations --check clean (nema missing migrations posle implementacije)
def test_no_missing_migrations_for_products():
    """`makemigrations --check --dry-run` ne sme prijaviti nedostajuće migracije."""
    from io import StringIO

    from django.core.management import call_command

    out = StringIO()
    try:
        call_command(
            "makemigrations", "products", "--check", "--dry-run", stdout=out, stderr=out
        )
    except SystemExit as exc:
        pytest.fail(
            f"makemigrations products --check prijavio missing migrations (exit {exc.code}). "
            f"Model i migracije nisu sinhronizovani. Output: {out.getvalue()!r}."
        )
