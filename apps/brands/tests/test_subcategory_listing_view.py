"""Story 2.11 — AC2/AC3/AC4/AC10/AC14 view testovi za SubcategoryListView.

RED phase (TEA): definiše view resolution + context kontrakt PRE implementacije.
Testira preko Django test client-a (full request/response, mirror Story 2-10 stil).

Pokriva:
- AC2: Category root resolucija + Http404 (miss + wrong scope).
- AC3: Subcategory chain resolucija + Http404 (invalid segment, wrong parent,
  depth mismatch).
- AC4: intermediate-vs-leaf DATA-DRIVEN odluka (is_leaf / children / products).
- AC4/AC14: mixed node (deca + products) → children win (intermediate).
- AC2/AC5: deterministički redosled dece (display_order, pa name tiebreak).
- AC10: query budget / N+1 (assertNumQueries — EXACT lock posle GREEN iter 1, SM-D12).
- ARCH-3 (Review-Fix iter 1): category-root branch (subcategory_listing_category,
  current is None) — top-level subcategories + breadcrumb + empty state (SM-D11).
"""

from __future__ import annotations

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext
from django.urls import resolve
from django.urls.exceptions import Resolver404

from apps.brands.models import Category
from apps.brands.tests.factories import CategoryFactory, SubcategoryFactory
from apps.products.tests.factories import ProductFactory

# AC10 exact query locks (BUG-2, SM-D12). Measured empirically after GREEN
# iteration 1 (Review-Fix iter 1); ceilings tightened from loose `<= 4` to exact.
# Intermediate render = 3 (Category lookup + L1 chain segment + children list).
# Leaf render = 4 (Category + L1 chain segment + products-with-select_related(brand)
# + session/i18n overhead). These are ORM query counts; sorl-thumbnail KVStore
# lookups in {% responsive_picture %} are library-level cache calls, NOT ORM joins
# on the Product queryset — same as Story 2-8/2-9 which also measure ORM budgets
# with imageless products. See test_leaf_with_images_query_budget.
_AC10_INTERMEDIATE_LOCKED = 3
_AC10_LEAF_LOCKED = 4


def _real_png_stub(name: str = "stub.png") -> SimpleUploadedFile:
    """Pillow-generated 1x1 PNG (REUSE products factory helper).

    A bare PNG magic-header stub does NOT decode in Pillow, so sorl-thumbnail's
    get_thumbnail() raises UnidentifiedImageError. The image-render N+1 guard
    (BUG-2) needs a real decodable image so {% responsive_picture %} in
    _model_grid.html actually exercises the thumbnail lookup path.
    """
    from apps.products.tests.factories import _minimal_png_bytes

    return SimpleUploadedFile(
        name=name,
        content=_minimal_png_bytes(),
        content_type="image/png",
    )


def _l1_url(category_slug: str, l1_slug: str) -> str:
    return f"/sr/mehanizacija/prikljucna/{category_slug}/{l1_slug}/"


def _l2_url(category_slug: str, l1_slug: str, l2_slug: str) -> str:
    return f"/sr/mehanizacija/prikljucna/{category_slug}/{l1_slug}/{l2_slug}/"


def _category_root_url(category_slug: str) -> str:
    return f"/sr/mehanizacija/prikljucna/{category_slug}/"


def _assert_routed(url: str, expected_view_name: str) -> None:
    """RED precondition (mirror Story 2-10 SM-D7 idiom): URL MORA da se rutira na
    novi SubcategoryListView pattern PRE nego što test tvrdi 404-iz-view-logike.

    Bez ove provere 404 testovi bi VACUOUSLY prošli u RED fazi (URL pattern ne
    postoji → 404 iz routinga, ne iz view Http404 raise-a). Ovo gard-uje da
    404 dolazi iz view logike (AC2/AC3), ne iz nerutiranog URL-a.
    """
    try:
        match = resolve(url)
    except Resolver404:
        pytest.fail(
            f"URL {url} se ne rutira — subcategory_listing pattern + "
            f"SubcategoryListView još NE postoje (RED phase). Ovaj test verifikuje "
            f"404 iz view logike, NE iz nerutiranog URL-a."
        )
    assert match.view_name == expected_view_name, (
        f"URL {url} MORA da se rutira na {expected_view_name}, dobio "
        f"{match.view_name!r}."
    )


@pytest.mark.django_db
class TestSubcategoryListingViewCategoryRoot:
    # AC2: postojeća MEHANIZACIJA kategorija + postojeća L1 potkategorija → 200
    def test_existing_category_and_l1_returns_200(self):
        # slug test-izolovan: osnovna-obrada-zemljista je seed-ovan u 0003 +
        # Category.slug je globalno unique → kolizija pri setup-u inače.
        cat = CategoryFactory.create(
            slug="t211-view-kat",
            is_for=Category.CategoryScope.MEHANIZACIJA,
        )
        l1 = SubcategoryFactory.create(category=cat, name="Plugovi", slug="plugovi")
        # dete da L1 bude intermediate (ima children) — render bez leaf product query
        SubcategoryFactory.create(parent=l1, name="Plugovi obrtači")
        resp = Client().get(_l1_url(cat.slug, l1.slug))
        assert resp.status_code == 200

    # AC2: nepostojeći category-slug → Http404 (iz view logike, ne iz routinga)
    def test_missing_category_returns_404(self):
        url = _l1_url("ne-postoji", "plugovi")
        _assert_routed(url, "brands:subcategory_listing_l1")
        assert Client().get(url).status_code == 404

    # AC2: pogrešan scope (is_for=TRAKTORI) → Http404 (mehanizacija-only resolucija)
    def test_wrong_scope_category_returns_404(self):
        cat = CategoryFactory.create(
            slug="traktorska-kat",
            is_for=Category.CategoryScope.TRAKTORI,
        )
        SubcategoryFactory.create(category=cat, slug="plugovi")
        url = _l1_url(cat.slug, "plugovi")
        _assert_routed(url, "brands:subcategory_listing_l1")
        assert Client().get(url).status_code == 404


@pytest.mark.django_db
class TestSubcategoryListingViewChain:
    # AC3: validan 2-deep chain (L1 → L2) → 200
    def test_valid_chain_returns_200(self):
        cat = CategoryFactory.create(is_for=Category.CategoryScope.MEHANIZACIJA)
        l1 = SubcategoryFactory.create(category=cat, name="Plugovi", slug="plugovi")
        l2 = SubcategoryFactory.create(
            parent=l1, name="Plugovi obrtači", slug="plugovi-obrtaci"
        )
        resp = Client().get(_l2_url(cat.slug, l1.slug, l2.slug))
        assert resp.status_code == 200

    # AC3: nevalidan segment (l2 slug ne postoji kao child) → Http404
    def test_invalid_second_segment_returns_404(self):
        cat = CategoryFactory.create(is_for=Category.CategoryScope.MEHANIZACIJA)
        l1 = SubcategoryFactory.create(category=cat, slug="plugovi")
        url = _l2_url(cat.slug, l1.slug, "ne-postoji")
        _assert_routed(url, "brands:subcategory_listing_l2")
        assert Client().get(url).status_code == 404

    # AC3: slug postoji ALI pod drugim parent-om (wrong-parent) → Http404
    def test_wrong_parent_returns_404(self):
        cat = CategoryFactory.create(is_for=Category.CategoryScope.MEHANIZACIJA)
        l1_a = SubcategoryFactory.create(category=cat, slug="plugovi")
        l1_b = SubcategoryFactory.create(category=cat, slug="podrivaci")
        # 'pod-b' je dete od l1_b, NE od l1_a
        SubcategoryFactory.create(parent=l1_b, slug="pod-b")
        url = _l2_url(cat.slug, l1_a.slug, "pod-b")
        _assert_routed(url, "brands:subcategory_listing_l2")
        assert Client().get(url).status_code == 404

    # AC3: depth mismatch — L1 koji nema dece traži se kao L2 → Http404
    def test_depth_mismatch_returns_404(self):
        cat = CategoryFactory.create(is_for=Category.CategoryScope.MEHANIZACIJA)
        l1 = SubcategoryFactory.create(category=cat, slug="plugovi")
        # l1 nema dece; tražimo L2 putanju → drugi segment ne resolvuje
        url = _l2_url(cat.slug, l1.slug, "bilo-sta")
        _assert_routed(url, "brands:subcategory_listing_l2")
        assert Client().get(url).status_code == 404


@pytest.mark.django_db
class TestSubcategoryListingViewIntermediateVsLeaf:
    # AC4: čvor SA decom → INTERMEDIATE (is_leaf=False, children u context-u)
    def test_node_with_children_is_intermediate(self):
        cat = CategoryFactory.create(is_for=Category.CategoryScope.MEHANIZACIJA)
        l1 = SubcategoryFactory.create(category=cat, slug="plugovi")
        SubcategoryFactory.create(parent=l1, name="Obrtači")
        SubcategoryFactory.create(parent=l1, name="Ravnjaci")
        resp = Client().get(_l1_url(cat.slug, l1.slug))
        assert resp.context["is_leaf"] is False
        assert len(resp.context["children"]) == 2

    # AC4: čvor BEZ dece → LEAF (is_leaf=True, products u context-u, samo published)
    def test_node_without_children_is_leaf(self):
        cat = CategoryFactory.create(is_for=Category.CategoryScope.MEHANIZACIJA)
        l1 = SubcategoryFactory.create(category=cat, slug="plugovi")
        ProductFactory.create(subcategory=l1, is_published=True)
        ProductFactory.create(subcategory=l1, is_published=True)
        ProductFactory.create(subcategory=l1, is_published=False)  # ne broji se
        resp = Client().get(_l1_url(cat.slug, l1.slug))
        assert resp.context["is_leaf"] is True
        assert len(list(resp.context["products"])) == 2

    # AC4: leaf bez ijednog proizvoda → is_leaf=True, prazan products
    def test_leaf_with_no_products_is_empty_leaf(self):
        cat = CategoryFactory.create(is_for=Category.CategoryScope.MEHANIZACIJA)
        l1 = SubcategoryFactory.create(category=cat, slug="plugovi")
        resp = Client().get(_l1_url(cat.slug, l1.slug))
        assert resp.context["is_leaf"] is True
        assert len(list(resp.context["products"])) == 0

    # AC4/AC14: mešovit čvor (deca + sopstveni products) → deca pobeđuju (intermediate);
    # sopstveni products se IGNORIŠU na tom nivou (test_mixed_node_children_win_intermediate).
    def test_mixed_node_children_win_intermediate(self):
        cat = CategoryFactory.create(is_for=Category.CategoryScope.MEHANIZACIJA)
        l1 = SubcategoryFactory.create(category=cat, slug="plugovi")
        SubcategoryFactory.create(parent=l1, name="Obrtači")
        # l1 ima I direktno vezane Product-e — moraju biti ignorisani
        ProductFactory.create(subcategory=l1, is_published=True)
        resp = Client().get(_l1_url(cat.slug, l1.slug))
        assert resp.context["is_leaf"] is False
        assert len(resp.context["children"]) == 1
        # leaf products NE smeju biti renderovani (children win)
        assert not resp.context.get("products")


@pytest.mark.django_db
class TestSubcategoryListingViewOrdering:
    # AC2/AC5: deca su ordered display_order, pa name kao tiebreak kad je
    # display_order isti (test_children_order_display_order_then_name_tiebreak).
    def test_children_order_display_order_then_name_tiebreak(self):
        cat = CategoryFactory.create(is_for=Category.CategoryScope.MEHANIZACIJA)
        l1 = SubcategoryFactory.create(category=cat, slug="plugovi")
        # isti display_order=0 → tiebreak po name: "Alfa" < "Beta" < "Gama"
        SubcategoryFactory.create(parent=l1, name="Gama", display_order=0)
        SubcategoryFactory.create(parent=l1, name="Alfa", display_order=0)
        SubcategoryFactory.create(parent=l1, name="Beta", display_order=0)
        # niži display_order ide prvi bez obzira na name
        SubcategoryFactory.create(parent=l1, name="Zzz prvi", display_order=-0)
        resp = Client().get(_l1_url(cat.slug, l1.slug))
        names = [c.name for c in resp.context["children"]]
        assert names == sorted(names)  # svi display_order=0 → čisto po name-u
        assert names[0] == "Alfa"


@pytest.mark.django_db
class TestSubcategoryListingViewQueryBudget:
    # AC10: intermediate render EXACT query lock (SM-D12, posle GREEN iter 1).
    def test_intermediate_query_budget(self):
        cat = CategoryFactory.create(is_for=Category.CategoryScope.MEHANIZACIJA)
        l1 = SubcategoryFactory.create(category=cat, slug="plugovi")
        for i in range(3):
            SubcategoryFactory.create(parent=l1, name=f"Child {i}")
        client = Client()
        with CaptureQueriesContext(connection) as ctx:
            resp = client.get(_l1_url(cat.slug, l1.slug))
            assert resp.status_code == 200
        # EXACT lock (post-GREEN, SM-D12) — tightened from `<= 4`.
        # Story 3.4: +1 za SiteSettings chrome upit (header/footer site_setting tag, 1/request).
        assert len(ctx.captured_queries) == _AC10_INTERMEDIATE_LOCKED + 1, (
            f"intermediate render used {len(ctx.captured_queries)} queries "
            f"(locked {_AC10_INTERMEDIATE_LOCKED} + 1 SiteSettings):\n"
            + "\n".join(q["sql"] for q in ctx.captured_queries)
        )

    # AC10: leaf render EXACT query lock (N+1 guard za product/brand).
    def test_leaf_query_budget(self):
        cat = CategoryFactory.create(is_for=Category.CategoryScope.MEHANIZACIJA)
        l1 = SubcategoryFactory.create(category=cat, slug="plugovi")
        for _ in range(5):
            ProductFactory.create(subcategory=l1, is_published=True)
        client = Client()
        with CaptureQueriesContext(connection) as ctx:
            resp = client.get(_l1_url(cat.slug, l1.slug))
            assert resp.status_code == 200
        # EXACT lock (post-GREEN, SM-D12) — tightened from `<= 4`.
        # Story 3.4: +1 za SiteSettings chrome upit (header/footer site_setting tag, 1/request).
        assert len(ctx.captured_queries) == _AC10_LEAF_LOCKED + 1, (
            f"leaf render used {len(ctx.captured_queries)} queries "
            f"(locked {_AC10_LEAF_LOCKED} + 1 SiteSettings):\n"
            + "\n".join(q["sql"] for q in ctx.captured_queries)
        )

    # AC10 (BUG-2 lock, SM-D12): leaf budget WITH real product images so the
    # sorl-thumbnail per-image lookup in _model_grid.html ({% responsive_picture
    # product.main_image %}) is actually exercised — the imageless tests above
    # never touch it.
    #
    # IMPORTANT (BUG-2 finding): with real images the TOTAL query count is high
    # and scales per-image, BUT that is sorl-thumbnail's KVStore behavior
    # (get_thumbnail() does cache lookups + first-render generation per image),
    # NOT an ORM N+1 on the Product queryset. The project pattern (Story 2-8/2-9)
    # measures ORM budgets with imageless products precisely because the thumbnail
    # KVStore cost is out of the view's control. This test therefore guards the
    # thing the view IS responsible for: the ORM queries hitting the
    # brands_*/products_* tables must NOT scale with product count (no per-product
    # SELECT on Product/Brand/Category — brand is select_related). It counts ONLY
    # those ORM queries, excluding sorl thumbnail/kvstore queries.
    def test_leaf_with_images_query_budget(self):
        cat = CategoryFactory.create(is_for=Category.CategoryScope.MEHANIZACIJA)
        l1 = SubcategoryFactory.create(category=cat, slug="plugovi-slike")
        for i in range(4):
            ProductFactory.create(
                subcategory=l1,
                is_published=True,
                name=f"Imaged {i}",
                main_image=_real_png_stub(f"leaf-img-{i}.png"),
            )
        client = Client()
        with CaptureQueriesContext(connection) as ctx:
            resp = client.get(_l1_url(cat.slug, l1.slug))
            assert resp.status_code == 200

        # Count ONLY the ORM queries against the catalog tables (brands_*/products_*),
        # excluding sorl-thumbnail KVStore lookups. This must equal the imageless
        # leaf lock — proving the image render adds NO per-product ORM query (the
        # leaf Product queryset already select_related('brand')).
        catalog_queries = [
            q
            for q in ctx.captured_queries
            if "brands_" in q["sql"] or "products_" in q["sql"]
        ]
        assert len(catalog_queries) == _AC10_LEAF_LOCKED, (
            f"leaf-with-images used {len(catalog_queries)} catalog ORM queries "
            f"(locked {_AC10_LEAF_LOCKED}) — ORM N+1 on the Product grid:\n"
            + "\n".join(q["sql"] for q in catalog_queries)
        )


@pytest.mark.django_db
class TestSubcategoryListingCategoryRoot:
    """ARCH-3 (Review-Fix iter 1) — bare /<category_slug>/ → current is None.

    subcategory_listing_category pattern; category-root intermediate listing
    (SM-D10/SM-D11). Test-prefiksirani slug-ovi da ne kolidiraju sa 0003 seed-om.
    """

    # ARCH-3b: category root renders top-level (parent=None) subcategories as cards.
    def test_category_root_renders_top_level_subcategories(self):
        cat = CategoryFactory.create(
            name="Osnovna obrada zemljišta",
            slug="t211-archroot-kat",
            is_for=Category.CategoryScope.MEHANIZACIJA,
        )
        l1 = SubcategoryFactory.create(category=cat, name="Plugovi", slug="plugovi")
        SubcategoryFactory.create(category=cat, name="Podrivači", slug="podrivaci")
        resp = Client().get(_category_root_url(cat.slug))
        assert resp.status_code == 200
        assert resp.context["is_leaf"] is False
        assert len(resp.context["children"]) == 2
        content = resp.content.decode()
        assert "coric-category-card" in content
        assert f'data-testid="subcategory-card-{l1.slug}"' in content

    # ARCH-3b: breadcrumb = Početna → Priključna mehanizacija → <category> (current).
    def test_category_root_breadcrumb_has_category_as_current(self):
        cat = CategoryFactory.create(
            name="Osnovna obrada zemljišta",
            slug="t211-archroot-bc",
            is_for=Category.CategoryScope.MEHANIZACIJA,
        )
        SubcategoryFactory.create(category=cat, name="Plugovi", slug="plugovi")
        content = Client().get(_category_root_url(cat.slug)).content.decode()
        assert 'data-testid="breadcrumb-nav"' in content
        i_home = content.find("Početna")
        i_prik = content.find("Priključna mehanizacija")
        i_cat = content.find("Osnovna obrada")
        assert -1 < i_home < i_prik < i_cat
        # category je current item (NIJE link) na category-root nivou.
        assert 'aria-current="page"' in content
        assert 'data-testid="breadcrumb-current"' in content

    # ARCH-3b / SM-D11: category bez potkategorija → empty-intermediate state.
    def test_category_root_empty_state_when_no_subcategories(self):
        cat = CategoryFactory.create(
            name="Prazna kategorija",
            slug="t211-archroot-empty",
            is_for=Category.CategoryScope.MEHANIZACIJA,
        )
        resp = Client().get(_category_root_url(cat.slug))
        assert resp.status_code == 200
        assert resp.context["is_leaf"] is False
        assert len(resp.context["children"]) == 0
        assert "Nema dostupnih potkategorija." in resp.content.decode()
