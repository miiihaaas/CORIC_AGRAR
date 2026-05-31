"""Story 2.13 — AC3/AC4/AC8 FTS query helper `build_product_search_qs` (TEA RED).

Pokriva PostgreSQL FTS ponašanje:
- AC3: diacritic-insensitive OBA smera (IMP-1), case-insensitive, is_published filter,
  annotation-alias path (NE NULL kolona — SM-D8/C3).
- AC4: rank name(weight A) > description(weight B); tie-break -created_at.
- AC8: locale isolation (sr/hu/en), region-suffix normalizacija ("sr-latn" → _sr).
- Negative/edge: tsquery meta-char safety (search_type="plain"), NULL translated polje.

⚠️ HARD requires_postgres (Task 8.0 / IMP-2): FTS NE radi na SQLite — conftest FAILA
(NE skip) ako backend nije PostgreSQL.

⚠️ ANNOT-NOT-COL (SM-D8/C3): da ovi testovi VRAĆAJU >0 redova dokazuje da upit ide
kroz annotation alias `search`, NE kroz UVEK-NULL `search_vector` kolonu. Ako Dev
greškom filtrira `.filter(search_vector=...)`, svi ovi testovi vraćaju 0 → fail.

Pokrenuti sa:
    docker compose -f compose/local.yml exec django uv run pytest \\
        apps/search/tests/test_search_query.py -v

Refs:
- 2-13-global-search-sa-postgresql-fts.md AC3/AC4/AC8 + Task 3 + SM-D8/D9/D10
- 2-13-interface-contract.md § 2 (search.py signature) + § 10 (DIACRITIC/RANK/LOCALE-ISO/TSQUERY-SAFE)
"""

from __future__ import annotations

import pytest

from apps.search.tests.factories import SearchProductFactory

pytestmark = [pytest.mark.django_db, pytest.mark.requires_postgres]


def _slugs(qs):
    return {p.slug for p in qs}


# AC3 (IMP-1): diacritic-insensitive — query "berba" nalazi name "Bérba" (query→accent)
def test_diacritic_insensitive_query_to_accented_name():
    from apps.search.search import build_product_search_qs

    p = SearchProductFactory.create(name_sr="Bérba mašina")

    qs = build_product_search_qs("berba", "sr")
    assert p.slug in _slugs(qs), (
        "Query 'berba' (bez akcenta) MORA naći proizvod čiji name_sr je 'Bérba mašina' "
        "(Unaccent na koloni + query — IMP-1). Ako 0 redova: ili unaccent nije na obe "
        "strane, ili upit filtrira po NULL search_vector koloni (SM-D8/C3)."
    )


# AC3 (IMP-1): diacritic-insensitive OBRNUTI smer — query "Bérba" nalazi name "berba"
def test_diacritic_insensitive_accented_query_to_plain_name():
    from apps.search.search import build_product_search_qs

    p = SearchProductFactory.create(name_sr="berba kombajn")

    qs = build_product_search_qs("Bérba", "sr")
    assert p.slug in _slugs(qs), (
        "Query 'Bérba' (sa akcentom) MORA naći proizvod čiji name_sr je 'berba kombajn' "
        "(diacritic-insensitive OBA smera — IMP-1). Jednosmerni unaccent NE zadovoljava AC3."
    )


# AC3: case-insensitive ("TB804" i "tb804" daju iste rezultate — tsvector lowercasuje)
def test_case_insensitive_search():
    from apps.search.search import build_product_search_qs

    p = SearchProductFactory.create(name_sr="Traktor TB804")

    upper = _slugs(build_product_search_qs("TB804", "sr"))
    lower = _slugs(build_product_search_qs("tb804", "sr"))
    assert p.slug in upper and p.slug in lower, (
        "Search MORA biti case-insensitive — 'TB804' i 'tb804' nalaze isti proizvod "
        "(PostgreSQL to_tsvector case-folding)."
    )


# AC3: is_published filter — draft/unpublished proizvodi se NE vraćaju
def test_only_published_products_returned():
    from apps.search.search import build_product_search_qs

    published = SearchProductFactory.create(name_sr="Vidljiva berba")
    draft = SearchProductFactory.create_unpublished(name_sr="Skrivena berba")

    slugs = _slugs(build_product_search_qs("berba", "sr"))
    assert published.slug in slugs, "Published proizvod MORA biti u rezultatu."
    assert draft.slug not in slugs, (
        "Unpublished (is_published=False) proizvod NE SME biti u rezultatu (AC3 filter)."
    )


# AC4 + SM-D10: rank — match u name (weight A) iznad match samo u description (weight B)
def test_rank_name_match_above_description_match():
    from apps.search.search import build_product_search_qs

    in_name = SearchProductFactory.create(
        name_sr="Berba kombajn", description_sr="Opis bez kljucne reci ovde."
    )
    in_desc = SearchProductFactory.create(
        name_sr="Univerzalna masina", description_sr="Idealna za berba sezonu."
    )

    results = list(build_product_search_qs("berba", "sr"))
    result_slugs = [p.slug for p in results]
    assert in_name.slug in result_slugs and in_desc.slug in result_slugs, (
        "Oba proizvoda (name match + description match) MORAJU biti u rezultatu."
    )
    assert result_slugs.index(in_name.slug) < result_slugs.index(in_desc.slug), (
        "Proizvod sa match u name (weight A) MORA rangirati IZNAD proizvoda sa match "
        "samo u description (weight B) — SearchRank weight A > B (SM-D10)."
    )


# AC4 + SM-D10: tie-break -created_at (najnoviji prvi) kad je rank jednak
def test_tiebreak_by_created_at_desc():
    from apps.search.search import build_product_search_qs
    from apps.products.models import Product

    older = SearchProductFactory.create(name_sr="Berba alfa")
    newer = SearchProductFactory.create(name_sr="Berba alfa")
    # Osiguraj deterministički created_at redosled (auto_now_add može biti isti tick).
    Product.objects.filter(pk=older.pk).update(
        created_at=newer.created_at.replace(year=newer.created_at.year - 1)
    )

    results = [p.slug for p in build_product_search_qs("berba alfa", "sr")]
    assert results.index(newer.slug) < results.index(older.slug), (
        "Pri jednakom rank-u tie-break je -created_at (najnoviji prvi) — SM-D10. "
        f"Dobijen redosled: {results}."
    )


# AC8: locale isolation — hu term nalazi na /hu/, NE na /sr/
@pytest.mark.parametrize(
    "lang,query,should_match",
    [
        ("sr", "berac", True),
        ("hu", "szedo", True),
        ("en", "harvester", True),
        ("sr", "szedo", False),   # hu term ne sme naći na sr
        ("hu", "berac", False),   # sr term ne sme naći na hu
        ("en", "berac", False),   # sr term ne sme naći na en
    ],
)
def test_locale_isolation(lang, query, should_match):
    from apps.search.search import build_product_search_qs

    p = SearchProductFactory.create(
        name_sr="Berac", name_hu="Szedo", name_en="Harvester"
    )

    slugs = _slugs(build_product_search_qs(query, lang))
    if should_match:
        assert p.slug in slugs, (
            f"Query {query!r} na locale {lang!r} MORA naći proizvod (name_{lang} kolona, SM-D9)."
        )
    else:
        assert p.slug not in slugs, (
            f"Query {query!r} na locale {lang!r} NE SME naći proizvod (locale isolation — "
            f"pretražuje se samo name_{lang}/description_{lang} kolona, AC8)."
        )


# AC8 (IMP-3): region-suffix "sr-latn"/"sr-Latn" normalizuje na _sr kolone (NE slep fallback)
@pytest.mark.parametrize("region_locale", ["sr-latn", "sr-Latn"])
def test_locale_region_suffix_normalizes_to_sr(region_locale):
    from apps.search.search import build_product_search_qs

    p = SearchProductFactory.create(
        name_sr="Berac regionalni", name_hu="Szedo regio", name_en="Harvester regio"
    )

    slugs = _slugs(build_product_search_qs("berac", region_locale))
    assert p.slug in slugs, (
        f"language_code {region_locale!r} MORA se normalizovati na 'sr' (split('-')[0].lower()) "
        "PRE biranja kolone → pretražuje name_sr (IMP-3)."
    )


# AC8 (SM-D9): locale van LANGUAGES → fallback na _sr kolone
def test_unknown_locale_falls_back_to_sr():
    from apps.search.search import build_product_search_qs

    p = SearchProductFactory.create(name_sr="Berac fallback")

    slugs = _slugs(build_product_search_qs("berac", "de"))  # 'de' nije u LANGUAGES
    assert p.slug in slugs, (
        "Nepoznat locale ('de' van LANGUAGES) MORA fallback-ovati na _sr kolone "
        "(MODELTRANSLATION_FALLBACK_LANGUAGES=('sr',), SM-D9)."
    )


# NEGATIVE (IMP-10): tsquery meta-znaci (& | ! : *) NE bacaju SyntaxError (search_type="plain")
@pytest.mark.parametrize("meta_query", ["berba & masina", "a | b", "!negacija", "x:y", "prefix*"])
def test_tsquery_meta_chars_do_not_raise(meta_query):
    from apps.search.search import build_product_search_qs

    SearchProductFactory.create(name_sr="Obican proizvod")
    # search_type="plain" MORA tretirati meta-znake doslovno — NE raw to_tsquery →
    # evaluacija QuerySet-a NE sme baciti psycopg/ProgrammingError (SyntaxError).
    qs = build_product_search_qs(meta_query, "sr")
    result = list(qs)  # forsira SQL izvršenje
    assert isinstance(result, list), (
        f"Query sa tsquery meta-znacima {meta_query!r} NE SME baciti SyntaxError — "
        "search_type='plain' tretira input kao plain tekst (IMP-10)."
    )


# EDGE: product sa NULL translated name/description ne ruši upit
def test_product_with_null_translated_name_does_not_break_query():
    from apps.search.search import build_product_search_qs

    # Eksplicitno NULL name_hu/description (caller daje samo sr).
    SearchProductFactory.create(name_sr="Validan", name_hu=None, name_en=None, description_sr="")

    # Upit na hu (gde je name_hu NULL) ne sme baciti — vraća prazan/list bez greške.
    qs = build_product_search_qs("bilo", "hu")
    result = list(qs)
    assert isinstance(result, list), (
        "Upit nad proizvodom sa NULL translated kolonom NE SME baciti (COALESCE/null-safe FTS)."
    )
