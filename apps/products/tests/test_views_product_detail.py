"""Story 2.7 — ProductDetailView tests (RED phase TDD).

Pokriva AC2 — CBV DetailView sa optimizovanim query plan (TAČNO 7 SQL upita za manual
ProductSimilar path), context surface (product + similar_products + similar_source +
brochures_list), FR-20 hibrid logika (manual override > auto fallback), is_published
sole gate (SM-D20 parametrized), brochures_list defensive size handling (SM-D26
broadened scope: 4 exception paths).

EMPIRICAL QUERY COUNT (verifikovano 2026-05-30 per Subtask 1.5(d) probe — SM-D28):
- Manual ProductSimilar path: 7 queries (lock literal)
- Auto fallback path: 8 queries (manual SELECT returns empty + auto SELECT executes)

Test `test_assert_num_queries_exactly_7` MORA construct fixture sa ProductSimilar entry
da hit-uje manual path. Auto fallback testovi NE koriste assertNumQueries(7).

Pokrenuti sa:
    docker compose -f compose/local.yml exec django uv run pytest \\
        apps/products/tests/test_views_product_detail.py -v

Refs:
- 2-7-product-detail-strana.md (story spec, AC2 + Subtask 12.2 + SM-D19/D20/D21/D24/D26/D28)
- 2-7-interface-contract.md (view + context canonical contract)
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from django.utils.translation import activate

from apps.brands.tests.factories import BrandFactory
from apps.products.tests.factories import (
    ProductBrochureFactory,
    ProductFactory,
    ProductSimilarFactory,
)

pytestmark = pytest.mark.django_db


# =============================================================================
# AC2 — Context contract: product + similar_products + similar_source + brochures_list
# =============================================================================


def test_context_contains_product(client):
    """AC2: context sadrži `product` ključ (DetailView default + context_object_name='product').

    NEMA odvojenih ključeva `gallery_images`/`variants`/`specifications`/`testimonials` —
    template pristupa kroz `product.<relation>.all` (prefetched relations).
    `brochures_list` je izuzetak (view pre-computes za size handling per SM-D26).
    """
    activate("sr")
    product = ProductFactory.create(name="TB-804", is_published=True)
    url = f"/sr/proizvod/{product.slug}/"

    response = client.get(url, HTTP_HOST="localhost")

    assert response.status_code == 200
    ctx = response.context
    assert "product" in ctx, (
        "Context MORA sadržati 'product' ključ (DetailView default + context_object_name='product')."
    )
    assert ctx["product"].pk == product.pk, (
        f"Context['product'].pk={ctx['product'].pk!r} ne matchuje očekivan product.pk={product.pk!r}."
    )
    # Anti-spec keys: NE smiju biti u context-u (per SM-D + AC2 § context surface minimization)
    for forbidden_key in ("gallery_images", "variants", "specifications", "testimonials"):
        assert forbidden_key not in ctx, (
            f"Context NE SME sadržati '{forbidden_key}' ključ — template MORA pristupati "
            f"kroz product.{forbidden_key}.all (prefetched relation)."
        )
    # similar_products + brochures_list MORAJU biti u context-u (always — može biti prazan)
    assert "similar_products" in ctx, "Context MORA sadržati 'similar_products' (može biti [])."
    assert "brochures_list" in ctx, "Context MORA sadržati 'brochures_list' (može biti [])."
    assert "similar_source" in ctx, (
        "Context MORA sadržati 'similar_source' debug/analytics flag "
        "('manual' / 'auto' / 'none' per SM-D + AC2)."
    )


def test_assert_num_queries_exactly_7(client, django_assert_num_queries):
    """AC2 (SM-D21/D28): pun render strane = TAČNO 7 SQL upita za MANUAL ProductSimilar path.

    EMPIRICAL (2026-05-30, Subtask 1.5(d) probe):
    1. Product DetailView get_object (sa select_related brand+series+subcategory)
    2. Prefetch ProductImage (ordered)
    3. Prefetch ProductVariant (ordered)
    4. Prefetch ProductSpecification (annotated sa Case/When + ordered)
    5. Prefetch ProductBrochure (ordered)
    6. Prefetch ProductTestimonial (ordered)
    7. ProductSimilar manual override (SQL is_published=True filter na related_product)

    Auto fallback path = 8 queries (manual SELECT returns empty + auto SELECT executes).
    Ovaj test MORA construct ProductSimilar fixture da hit-uje manual path.
    """
    activate("sr")
    brand = BrandFactory.create(name="Test Brand")
    product = ProductFactory.create(brand=brand, name="Main Product", is_published=True)
    # Manual similar entry — hit-uje manual path (7 queries) instead of auto fallback (8 queries)
    other = ProductFactory.create(brand=brand, name="Similar Product", is_published=True)
    ProductSimilarFactory.create(product=product, related_product=other)

    url = f"/sr/proizvod/{product.slug}/"

    # ContentType.get_for_model (SEO head 6.1) je process-level keširan (NE per-request),
    # pa njegova prva-poziv cena curi između testova ovisno o redosledu izvršavanja.
    # Warm-ujemo keš ovde da budget meri DETERMINISTIČKU per-request cenu (order-independent).
    from django.contrib.contenttypes.models import ContentType

    from apps.products.models import Product

    ContentType.objects.get_for_model(Product)

    # Query budget: 11 = 7 view upita (manual ProductSimilar path, gore nabrojano)
    #   + SiteSettings chrome (3.4)
    #   + SEO head SeoMeta forward-lookup (6.1; ContentType resolve je warm-ovan iznad)
    #   + RedirectMiddleware seo_redirect lookup (6-4)
    #   + footer latest_blog_posts blog_post LIMIT 3 (5-4).
    # Test name `..._exactly_7` je istorijski (7 = SAMO view upiti za manual path); ostatak
    # je site-wide chrome konstantan po request-u (indeksiran, ne skalira sa brojem
    # prefetched relacija). Real N+1 u view-u i dalje obara ovaj exact budget.
    with django_assert_num_queries(11):
        response = client.get(url, HTTP_HOST="localhost")
        assert response.status_code == 200


def test_similar_products_manual_override_path(client):
    """AC2 + AC6: ako ProductSimilar entry postoji sa published related_product,
    `similar_products` lista koristi te entries (NE auto fallback); similar_source='manual'."""
    activate("sr")
    brand = BrandFactory.create(name="Manual Brand")
    product = ProductFactory.create(brand=brand, name="Source Product", is_published=True)
    chosen_similar = ProductFactory.create(brand=brand, name="Manually Chosen", is_published=True)
    # Drugi published product u istom brendu — auto fallback bi ga uzeo, ali manual mora trumpovati
    ProductFactory.create(brand=brand, name="Auto Candidate", is_published=True)
    ProductSimilarFactory.create(product=product, related_product=chosen_similar)

    url = f"/sr/proizvod/{product.slug}/"
    response = client.get(url, HTTP_HOST="localhost")

    assert response.status_code == 200
    ctx = response.context
    assert ctx["similar_source"] == "manual", (
        f"similar_source treba biti 'manual' (postoji ProductSimilar entry sa published related), "
        f"dobio {ctx['similar_source']!r}."
    )
    similar_pks = [p.pk for p in ctx["similar_products"]]
    assert chosen_similar.pk in similar_pks, (
        f"Manually chosen Product (pk={chosen_similar.pk}) MORA biti u similar_products. "
        f"Dobili PK-ovi: {similar_pks!r}."
    )


def test_similar_products_auto_fallback_path(client):
    """AC2 + AC6: ako nema ProductSimilar entry-ja, auto fallback uzima istog brenda
    published proizvode; similar_source='auto'."""
    activate("sr")
    brand = BrandFactory.create(name="Auto Fallback Brand")
    product = ProductFactory.create(brand=brand, name="Main Product", is_published=True)
    other = ProductFactory.create(brand=brand, name="Auto Similar", is_published=True)

    url = f"/sr/proizvod/{product.slug}/"
    response = client.get(url, HTTP_HOST="localhost")

    assert response.status_code == 200
    ctx = response.context
    assert ctx["similar_source"] == "auto", (
        f"similar_source treba biti 'auto' (nema ProductSimilar; ima drugi published u brendu), "
        f"dobio {ctx['similar_source']!r}."
    )
    similar_pks = [p.pk for p in ctx["similar_products"]]
    assert other.pk in similar_pks, (
        f"Auto fallback MORA uključiti `{other.name}` (pk={other.pk}), dobili: {similar_pks!r}."
    )
    assert product.pk not in similar_pks, (
        "Auto fallback MORA exclude trenutni proizvod (.exclude(pk=self.object.pk))."
    )


def test_similar_products_empty_state(client):
    """AC2 + AC6: ako ni manual ni auto ne daju rezultate, similar_products=[],
    similar_source='none'.

    Setup: izolovan brand sa SAMO ovim jednim proizvodom; bez ProductSimilar entry-ja.
    """
    activate("sr")
    brand = BrandFactory.create(name="Isolated Brand")
    product = ProductFactory.create(brand=brand, name="Lone Product", is_published=True)

    url = f"/sr/proizvod/{product.slug}/"
    response = client.get(url, HTTP_HOST="localhost")

    assert response.status_code == 200
    ctx = response.context
    assert ctx["similar_products"] == [], (
        f"similar_products treba biti prazna lista, dobio {ctx['similar_products']!r}."
    )
    assert ctx["similar_source"] == "none", (
        f"similar_source treba biti 'none', dobio {ctx['similar_source']!r}."
    )


def test_manual_similars_with_unpublished_filtered_at_sql_level(client):
    """AC2 + AC6 (SM-D19): manual ProductSimilar entries sa unpublished related_product
    MORAJU biti filtirani na SQL nivou (WHERE clause), NE Python post-filter na sliced list.

    Edge case: admin postavi 4 manual similars od kojih su 2 published + 2 unpublished.
    Očekivano (per SM-D19 SQL filter):
    - similar_products lista ima 2 entries (oba published)
    - similar_source == 'manual' (lista NIJE prazna)
    - auto fallback SE NE okida (admin override intent je još uvek "manual")
    """
    activate("sr")
    brand = BrandFactory.create(name="Mixed Brand")
    product = ProductFactory.create(brand=brand, name="Main", is_published=True)
    pub_a = ProductFactory.create(brand=brand, name="Pub A", is_published=True)
    pub_b = ProductFactory.create(brand=brand, name="Pub B", is_published=True)
    unpub_a = ProductFactory.create_unpublished(brand=brand, name="Unpub A")
    unpub_b = ProductFactory.create_unpublished(brand=brand, name="Unpub B")
    ProductSimilarFactory.create(product=product, related_product=pub_a, order=0)
    ProductSimilarFactory.create(product=product, related_product=unpub_a, order=1)
    ProductSimilarFactory.create(product=product, related_product=pub_b, order=2)
    ProductSimilarFactory.create(product=product, related_product=unpub_b, order=3)

    url = f"/sr/proizvod/{product.slug}/"
    response = client.get(url, HTTP_HOST="localhost")

    assert response.status_code == 200
    ctx = response.context
    similar_pks = [p.pk for p in ctx["similar_products"]]
    assert len(similar_pks) == 2, (
        f"similar_products MORA imati 2 entries (samo published), dobio {len(similar_pks)}: {similar_pks!r}. "
        "SQL-level is_published=True filter (SM-D19) MORA biti na queryset-u PRE slice-a."
    )
    assert pub_a.pk in similar_pks and pub_b.pk in similar_pks, (
        f"Published similars MORAJU biti u listi; unpublished NE SME. Dobio: {similar_pks!r}."
    )
    assert unpub_a.pk not in similar_pks and unpub_b.pk not in similar_pks, (
        f"Unpublished similars NE SMIJU biti u listi (SM-D19 SQL filter). Dobio: {similar_pks!r}."
    )
    assert ctx["similar_source"] == "manual", (
        f"similar_source treba ostati 'manual' (lista NIJE prazna), dobio {ctx['similar_source']!r}. "
        "Auto fallback NE SME firingu (admin intent je manual override sa 4 entries; "
        "rezultantna lista je manja samo zbog publish state-a)."
    )


@pytest.mark.parametrize("status_value", ["draft", "published", "archived"])
def test_unpublished_product_returns_404_regardless_of_status(client, status_value):
    """AC1 + AC2 (SM-D20): is_published=False uvek daje 404, regardless of status enum.

    SM-D20: `is_published` (boolean) je SOLE public-visibility gate. `Product.status`
    (TextChoices: draft/published/archived) je admin-only workflow metadata.
    `is_published=False` + bilo koji status = HTTP 404.
    """
    activate("sr")
    product = ProductFactory.create(
        name=f"Unpub {status_value}",
        is_published=False,
        status=status_value,
    )
    url = f"/sr/proizvod/{product.slug}/"

    response = client.get(url, HTTP_HOST="localhost")

    assert response.status_code == 404, (
        f"GET {url} (is_published=False, status={status_value!r}) treba HTTP 404, "
        f"dobio {response.status_code}. is_published je SOLE gate (SM-D20)."
    )


@pytest.mark.parametrize("status_value", ["draft", "published", "archived"])
def test_published_product_renders_regardless_of_status(client, status_value):
    """AC1 + AC2 (SM-D20): is_published=True uvek daje 200, regardless of status enum.

    is_published=True + status='draft' je validan intermediate state (admin priprema content
    kao draft → preview kroz is_published=True → finalizuje status='published' nakon QA-a).
    is_published=True + status='archived' je admin oversight; treba UI guard u Story 8.6,
    ali NE javni 404 trigger (regression risk za već-objavljene proizvode).
    """
    activate("sr")
    product = ProductFactory.create(
        name=f"Pub {status_value}",
        is_published=True,
        status=status_value,
    )
    url = f"/sr/proizvod/{product.slug}/"

    response = client.get(url, HTTP_HOST="localhost")

    assert response.status_code == 200, (
        f"GET {url} (is_published=True, status={status_value!r}) treba HTTP 200, "
        f"dobio {response.status_code}. is_published je SOLE gate (SM-D20); status ne "
        "filtruje na public view."
    )


# =============================================================================
# AC2 + AC7 — brochures_list defensive size handling (SM-D26 broadened scope)
# =============================================================================


def test_brochures_list_pre_computed_with_size_bytes(client):
    """AC2 + AC7 (SM-D26/I8): brochures_list je lista dict-ova {'brochure': ..., 'size_bytes': int}.

    View-layer pre-computes size_bytes (NE template-side `pdf_file.size`) za defensive
    handling u slučaju FileSystem errors (per SM-D26 broadened scope iter 2).
    """
    activate("sr")
    product = ProductFactory.create(name="Brochured Product", is_published=True)
    ProductBrochureFactory.create(product=product, title="Brošura 1")
    ProductBrochureFactory.create(product=product, title="Brošura 2")

    url = f"/sr/proizvod/{product.slug}/"
    response = client.get(url, HTTP_HOST="localhost")

    assert response.status_code == 200
    ctx = response.context
    brochures_list = ctx["brochures_list"]
    assert isinstance(brochures_list, list), (
        f"brochures_list MORA biti list, dobio {type(brochures_list).__name__}."
    )
    assert len(brochures_list) == 2, (
        f"brochures_list treba imati 2 entries, dobio {len(brochures_list)}."
    )
    for entry in brochures_list:
        assert isinstance(entry, dict), (
            f"Svaki entry MORA biti dict, dobio {type(entry).__name__}: {entry!r}."
        )
        assert "brochure" in entry, f"Entry MORA imati 'brochure' ključ; entry: {entry!r}."
        assert "size_bytes" in entry, f"Entry MORA imati 'size_bytes' ključ; entry: {entry!r}."
        assert isinstance(entry["size_bytes"], int), (
            f"entry['size_bytes'] MORA biti int, dobio {type(entry['size_bytes']).__name__}."
        )


@pytest.mark.parametrize(
    "exc_class,exc_msg",
    [
        (FileNotFoundError, "file missing"),
        (OSError, "permission denied"),
        (ValueError, "no name"),
        # SuspiciousFileOperation: koristimo eksplicitan import-time fallback class kroz patch_target
        ("django.core.exceptions.SuspiciousFileOperation", "path traversal"),
    ],
)
def test_brochures_list_handles_file_errors_gracefully(client, exc_class, exc_msg):
    """AC2 + AC7 (SM-D26 broadened scope, I-iter2-4): brochures_list view-layer try/except
    MORA hvatati 4 documented exception path-ova oko `pdf_file.size`:

    - FileNotFoundError (file missing on disk)
    - OSError (permission denied, disk corruption)
    - ValueError (FieldFile.name None or unsaved instance)
    - SuspiciousFileOperation (Django storage path traversal guard)

    Sve 4 putanje → graceful degradation (size_bytes=0), NO 500 error.

    Mock pattern: patch `pdf_file.size` property (FieldFile.size) da raise mock exception.
    """
    activate("sr")
    product = ProductFactory.create(name="Faulty Brochure Product", is_published=True)
    ProductBrochureFactory.create(product=product, title="Faulty Brošura")

    # Resolve actual exception class (string vs class)
    if isinstance(exc_class, str):
        from django.core.exceptions import SuspiciousFileOperation as _SFO

        actual_exc = _SFO
    else:
        actual_exc = exc_class

    url = f"/sr/proizvod/{product.slug}/"
    # Patch FieldFile.size property to raise the exception
    with patch(
        "django.db.models.fields.files.FieldFile.size",
        new_callable=lambda: property(lambda self: (_ for _ in ()).throw(actual_exc(exc_msg))),
    ):
        response = client.get(url, HTTP_HOST="localhost")

    assert response.status_code == 200, (
        f"View MORA vratiti 200 (graceful) iako pdf_file.size raise-uje {actual_exc.__name__}; "
        f"dobio {response.status_code}. View-layer try/except (SM-D26 broadened) catches "
        "(FileNotFoundError, OSError, ValueError, SuspiciousFileOperation)."
    )
    ctx = response.context
    brochures_list = ctx["brochures_list"]
    assert len(brochures_list) == 1
    assert brochures_list[0]["size_bytes"] == 0, (
        f"size_bytes MORA biti 0 fallback kad pdf_file.size raise-uje exception; "
        f"dobio {brochures_list[0]['size_bytes']!r}."
    )


def test_brochures_list_capped_at_5(client):
    """AC2 + AC7 (SM-D24/I1): brochures_list je capped na 5 entries (slice [:5] u view).

    Admin može uneti više od 5 brochures u DB, ali template renderuje samo top 5
    (cap je defensive guard protiv UX katastrofe + Lighthouse Performance hit).
    """
    activate("sr")
    product = ProductFactory.create(name="Many Brochures", is_published=True)
    # Kreiraj 7 brochures
    for i in range(7):
        ProductBrochureFactory.create(product=product, title=f"Brošura {i}")

    url = f"/sr/proizvod/{product.slug}/"
    response = client.get(url, HTTP_HOST="localhost")

    assert response.status_code == 200
    brochures_list = response.context["brochures_list"]
    assert len(brochures_list) == 5, (
        f"brochures_list MORA biti capped na 5 entries (SM-D24/I1); dobio {len(brochures_list)}. "
        "View-layer slice `product.brochures.all()[:5]` enforced cap."
    )
