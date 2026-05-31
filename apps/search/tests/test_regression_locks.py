"""Story 2.13 — Review-phase regression locks (Dev Batch Fix, NON-MANDATORY ITEM-3).

Fokus regresioni testovi koji zaključavaju ponašanje otkriveno/popravljeno tokom
code-review-a (PERF + SM-D18 ordering + import-path + NoReverseMatch graceful degrade):

- PERF-A: dropdown/FTS upit NE N+1-uje na brand (`select_related("brand")` na snazi) —
  broj upita NE skalira sa brojem proizvoda.
- PERF-B: too_short (< 2 znaka) grana izvršava NULA product/category/brand SQL upita
  (SM-D13 — guard PRE bilo kakvog query-ja, uklj. empty-state CTA).
- SM-D18: empty-state `popular_categories` su poređane po `display_order`.
- IMPORT-PATH: `apps.search.search.Unaccent` JESTE klasa iz `django.contrib.postgres.lookups`
  (lock protiv budućeg „fix"-a nazad na `...search` koji baca ImportError na Django 5.2).
- NOREVERSE-GRACEFUL: `_category_link` preskače kategoriju čiji `get_absolute_url()` baca
  `NoReverseMatch` (pre-existing apps/brands debt — ITEM-6) umesto 500.

⚠️ requires_postgres na FTS-zavisnim testovima (Task 8.0/IMP-2) mirror ostatka suite-a.

Pokrenuti sa:
    docker compose -f compose/local.yml exec django uv run pytest \\
        apps/search/tests/test_regression_locks.py -v

Refs:
- 2-13-interface-contract.md § 2 (search.py select_related/import) + § 10
- 2-13-global-search-sa-postgresql-fts.md SM-D9/D13/D18
"""

from __future__ import annotations

import pytest
from django.urls import NoReverseMatch
from django.utils.translation import activate

from apps.search.tests.factories import SearchProductFactory

pytestmark = [pytest.mark.django_db, pytest.mark.requires_postgres]


# PERF-A (select_related("brand")): broj upita za izgradnju+evaluaciju rezultata NE
# skalira sa brojem proizvoda. Bez select_related, pristup `product.brand` u render-u
# bi N+1-ovao. Reuse istog vektora + select_related drži broj upita konstantnim.
def test_dropdown_query_does_not_n_plus_one_on_brand(django_assert_num_queries):
    from apps.search.search import build_product_search_qs

    activate("sr")

    def _count_for(n: int) -> int:
        from django.test.utils import CaptureQueriesContext
        from django.db import connection

        for i in range(n):
            SearchProductFactory.create(name_sr=f"Berba brend lock {i}")
        with CaptureQueriesContext(connection) as ctx:
            # materijalizuj rezultate + dotakni brand (render path)
            results = list(build_product_search_qs("berba", "sr"))
            for p in results:
                _ = p.brand.name
        return len(ctx.captured_queries)

    queries_small = _count_for(3)
    queries_large = _count_for(3)  # +3 → ukupno 6 proizvoda matchuje

    assert queries_large == queries_small, (
        "Broj SQL upita MORA biti konstantan bez obzira na broj proizvoda — "
        "`select_related('brand')` sprečava N+1 na brand pristup u render-u. "
        f"3 proizvoda: {queries_small} upita; 6 proizvoda: {queries_large} upita."
    )


# PERF-B (SM-D13): too_short grana NE izvršava NIJEDAN SQL upit (ni product, ni
# category/brand empty-state CTA). _build_search_context se zove direktno (bez client/
# session) da broj upita reflektuje SAMO view logiku.
def test_too_short_path_executes_zero_sql(django_assert_num_queries):
    from apps.search.views import _build_search_context

    activate("sr")
    # Postoje podaci u DB — guard MORA da ih ignoriše (NE query-uje).
    SearchProductFactory.create(name_sr="Berba postoji")

    with django_assert_num_queries(0):
        context = _build_search_context("a")  # 1 znak → too_short

    assert context["too_short"] is True
    assert context["suggestion_count"] == 0


# SM-D18: empty-state popular_categories poređane po display_order (unutar istog is_for
# scope-a — ordering je ("is_for", "display_order")). Monkeypatch-ujemo get_absolute_url
# da resolve-uje (pre-existing brands debt ga inače baca → kategorije se preskaču).
def test_empty_state_popular_categories_ordered_by_display_order(monkeypatch):
    from apps.brands.models import Category
    from apps.brands.tests.factories import CategoryFactory
    from apps.search.views import _empty_state_cta_context

    activate("sr")
    # Očisti seed/migracija kategorije (data migracije 0003/0004) da ordering asercija
    # bude deterministička — transakcija se rollback-uje posle testa.
    Category.objects.all().delete()
    scope = Category.CategoryScope.MEHANIZACIJA
    # Kreiraj van-reda da dokažemo da ordering NIJE insertion-order.
    c_third = CategoryFactory.create(name="Treća", is_for=scope, display_order=30)
    c_first = CategoryFactory.create(name="Prva", is_for=scope, display_order=10)
    c_second = CategoryFactory.create(name="Druga", is_for=scope, display_order=20)

    # get_absolute_url resolve-uje na poznat URL (zaobiđi brands NoReverseMatch debt).
    monkeypatch.setattr(
        Category, "get_absolute_url", lambda self: f"/mehanizacija/{self.slug}/"
    )

    context = _empty_state_cta_context()
    ordered_names = [c["name"] for c in context["popular_categories"]]

    assert ordered_names == ["Prva", "Druga", "Treća"], (
        "popular_categories MORAJU biti poređane po display_order (SM-D18), "
        f"dobio redosled: {ordered_names}."
    )
    # Sanity — koristimo sve 3 kreirane reference (lint: ne ostavljaj unused).
    assert {c_first.pk, c_second.pk, c_third.pk}


# IMPORT-PATH lock: Unaccent korišćen u apps/search/search.py MORA biti klasa iz
# django.contrib.postgres.lookups (NE ...search — to baca ImportError na Django 5.2).
# Hvata budući pogrešan „fix" nazad na .search.
@pytest.mark.parametrize("_noop", [None])  # drži stil parametrizacije konzistentnim
def test_unaccent_import_path_is_lookups(_noop):
    from django.contrib.postgres.lookups import Unaccent as LookupsUnaccent

    from apps.search import search as search_module

    assert search_module.Unaccent is LookupsUnaccent, (
        "apps.search.search.Unaccent MORA biti django.contrib.postgres.lookups.Unaccent. "
        "Na Django 5.2 `from django.contrib.postgres.search import Unaccent` baca "
        "ImportError — NE vraćaj import nazad na `...search`."
    )
    assert LookupsUnaccent.__module__ == "django.contrib.postgres.lookups"


# NOREVERSE-GRACEFUL (ITEM-3e / SM-D18 + ITEM-6): kategorija čiji get_absolute_url()
# baca NoReverseMatch (pre-existing brands debt) se TIHO preskače — empty-state CTA NE
# pukne (NE 500). _category_link vraća None za takvu kategoriju.
def test_category_link_skips_on_noreverse(monkeypatch):
    from apps.brands.models import Category
    from apps.brands.tests.factories import CategoryFactory
    from apps.search.views import _category_link, _empty_state_cta_context

    activate("sr")
    cat = CategoryFactory.create(name="Nerezolvabilna", display_order=1)

    def _raise(self):
        raise NoReverseMatch("brands:category_x ne postoji (test debt simulacija)")

    monkeypatch.setattr(Category, "get_absolute_url", _raise)

    # Direktan helper: NoReverseMatch → None (preskoči, NE propagiraj).
    assert _category_link(cat) is None, (
        "_category_link MORA vratiti None kad get_absolute_url() baca NoReverseMatch "
        "(graceful degrade — ITEM-6 brands debt), NE propagirati izuzetak."
    )

    # Full context: kategorija se preskače, CTA i dalje vraća validnu strukturu (NE 500).
    context = _empty_state_cta_context()
    assert context["popular_categories"] == [], (
        "Sve kategorije nereresolve-able → popular_categories prazna lista, "
        "empty-state se gradi bez izuzetka."
    )
