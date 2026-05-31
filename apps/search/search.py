"""Story 2.13 — PostgreSQL FTS query helper-i za global search (SM-D8/D9/D10).

`build_product_search_qs(query, language_code)` gradi annotated + ranked QuerySet[Product]:

- locale-aware kolone: `name_<lang>` (weight A) + `description_<lang>` (weight B), SM-D9
- region-suffix normalizacija (IMP-3): "sr-latn"/"sr-Latn" → split("-")[0].lower() → "sr"
- locale van LANGUAGES (posle normalizacije) → fallback "sr" (MODELTRANSLATION_FALLBACK_LANGUAGES)
- diacritic-insensitive OBA smera (IMP-1): Unaccent obmotan na OBE strane (kolone + query)
- search_type="plain" (IMP-10): tsquery meta-znaci (& | ! : *) se tretiraju doslovno, NE SyntaxError
- Value() obmotava literal query string (IMP-8)
- vektor je ANNOTATION ALIAS — filtrira se po aliasu, NE po `search_vector` koloni (C3/SM-D8;
  kolona je UVEK NULL u v1, GIN indeks na njoj je no-op forward-compat skelet)
- .filter(is_published=True)
- .order_by("-rank", "-created_at") (SM-D10)

Refs:
- 2-13-interface-contract.md § 2 (search.py) + § 3
- 2-13-global-search-sa-postgresql-fts.md SM-D8/D9/D10
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.conf import settings

# NAPOMENA (Dev/GREEN): U Django 5.2 `Unaccent` živi u `django.contrib.postgres.lookups`
# (NE u `...search` kako je interface-contract § 2 C2 pretpostavio — verifikovano live
# protiv instalirane Django 5.2.14: `from django.contrib.postgres.search import Unaccent`
# baca ImportError). `SearchVector`/`SearchQuery`/`SearchRank` su u `...search`.
from django.contrib.postgres.lookups import Unaccent
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.db.models import Value

from apps.products.models import Product

if TYPE_CHECKING:
    from django.db.models import QuerySet

# Baseline text search config (SM-D9/OQ-5): sr/hu nemaju ugrađen PG stemmer config —
# 'simple' + Unaccent je bezbedan default (exact token + diacritic-insensitive).
_SEARCH_CONFIG = "simple"

# Fallback locale za kolone van LANGUAGES (SM-D9 — MODELTRANSLATION_FALLBACK_LANGUAGES).
_FALLBACK_LANGUAGE = "sr"


def _normalize_language_code(language_code: str) -> str:
    """Normalizuje region/script suffiks i fallback-uje na 'sr' van LANGUAGES (SM-D9/IMP-3).

    "sr-latn"/"sr-Latn" → "sr"; nepoznat locale ("de") → "sr".
    """
    normalized = (language_code or "").split("-")[0].lower()
    valid = {code for code, _label in settings.LANGUAGES}
    if normalized not in valid:
        return _FALLBACK_LANGUAGE
    return normalized


def build_product_search_qs(query: str, language_code: str) -> "QuerySet[Product]":
    """FTS upit nad Product — locale-aware kolone, unaccent diacritic-insensitive, ranked.

    Vraća annotated QuerySet (BEZ slice — view radi slice + count, SM-D11).
    """
    lang = _normalize_language_code(language_code)
    name_col = f"name_{lang}"
    description_col = f"description_{lang}"

    # IMP-1: Unaccent na OBE strane (kolone + query) — inače diacritic radi samo u jednom smeru.
    # IMP-8: Value() obmotava literal query string (Django idiom za literal argument).
    # IMP-10: search_type="plain" tretira user input kao plain tekst — meta-znaci ne bacaju SyntaxError.
    search_query = SearchQuery(
        Unaccent(Value(query)), config=_SEARCH_CONFIG, search_type="plain"
    )
    # KRITIČNO (rank weights): SearchRank MORA dobiti sam SearchVector EXPRESSION objekat,
    # NE annotation-alias string. Prosleđivanje aliasa ("search") natera Django da re-wrap-uje
    # vektor kroz `to_tsvector((...)::text)` što ODBACUJE setweight(A/B) labele → name (A) i
    # description (B) match dobiju IDENTIČAN rank (SM-D10 prekršen). Reuse istog vektor objekta
    # u .annotate() i SearchRank() čuva weight-ove.
    search_vector = SearchVector(
        Unaccent(name_col), weight="A", config=_SEARCH_CONFIG
    ) + SearchVector(Unaccent(description_col), weight="B", config=_SEARCH_CONFIG)
    return (
        Product.objects.filter(is_published=True)
        .select_related("brand")
        .annotate(search=search_vector)
        .annotate(rank=SearchRank(search_vector, search_query))
        .filter(search=search_query)
        .order_by("-rank", "-created_at")
    )
