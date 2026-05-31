"""Story 2.13 — search_dropdown (HTMX) + search_results (full strana) FBV-ovi (SM-D5).

- search_dropdown: HTMX dropdown endpoint — grouped FTS rezultati + OOB aria-live (guarded).
- search_results: non-HTMX /pretraga/ full strana („Vidi sve" target, SM-D16).

Ključne odluke:
- grouped dict UVEK ima `objave: []` (SM-D3 forward-compat); view NE query-uje Post.
- min-2-char server-side guard (SM-D13) — NE izvršava SQL ispod 2 znaka.
- query-length cap 100 (SM-D17) — DoS guard, truncate (NEMA 400).
- suggestion_count = total PRE slice (SM-D11) — tačna aria-live najava.
- empty-state CTA: popularne kategorije (display_order) + brendovi (is_coming_soon=False, SM-D18).
- GET-only (SM-D17 + Addendum B.3) kroz @require_GET.

Refs:
- 2-13-interface-contract.md § 2 (views.py + Context surface)
- 2-13-global-search-sa-postgresql-fts.md AC3/AC5/AC6/AC7/AC8 + SM-D3/D11/D13/D16/D17/D18
"""

from __future__ import annotations

from django.shortcuts import render
from django.urls import NoReverseMatch
from django.utils.translation import get_language
from django.views.decorators.http import require_GET

from apps.brands.models import Brand, Category
from apps.search.search import build_product_search_qs

_MIN_QUERY_LEN = 2  # SM-D13
_MAX_QUERY_LEN = 100  # SM-D17
_PER_GROUP = 5  # SM-D11
_CTA_CATEGORIES_LIMIT = 6  # SM-D18 empty-state CTA
_CTA_BRANDS_LIMIT = 8  # SM-D18 empty-state CTA


def _category_link(category: Category) -> dict | None:
    """Vraća {name, url} za kategoriju ili None ako URL nije resolve-able.

    NAPOMENA (Dev/GREEN): `Category.get_absolute_url()` (apps/brands/models.py) reverse-uje
    `brands:category_mehanizacija`/`category_traktori` URL imena koja NE postoje u
    apps/brands/urls.py (Story 2.9-2.11 su koristili druga imena — latentni bug van scope-a
    Story 2.13, brands/models.py je NETAKNUTI regression guard). URL resolve se obmotava
    try/except NoReverseMatch u Python-u (template ne može try/except) da empty-state CTA
    ne pukne na seed-ovanim kategorijama; nereresolve-able kategorija se tiho preskače.
    """
    try:
        url = category.get_absolute_url()
    except NoReverseMatch:
        return None
    return {"name": category.name, "url": url}


def _empty_state_cta_context() -> dict:
    """Empty-state CTA data (SM-D18) — popularne kategorije + vidljivi brendovi."""
    categories = Category.objects.order_by("is_for", "display_order")[
        :_CTA_CATEGORIES_LIMIT
    ]
    popular_categories = [
        link for c in categories if (link := _category_link(c)) is not None
    ]
    return {
        "popular_categories": popular_categories,
        "header_brands": Brand.objects.filter(is_coming_soon=False).order_by("name")[
            :_CTA_BRANDS_LIMIT
        ],
    }


def _build_search_context(query: str, *, capped: bool = True) -> dict:
    """Zajednički kontekst za dropdown + full stranu (grouped dict, count, too_short).

    `capped=True` (dropdown) slice-uje proizvode na _PER_GROUP (SM-D11); `capped=False`
    (full „Vidi sve" strana, SM-D16) vraća punu listu.
    """
    if len(query) < _MIN_QUERY_LEN:
        # SM-D13 — NE izvršava SQL ispod 2 znaka. Template _search_empty.html NE
        # renderuje CTA blok u too_short grani (samo hint), pa _empty_state_cta_context()
        # (Category + Brand SQL) NE SME da se poziva ovde — perf + DoS guard (PERF-B).
        return {
            "query": query,
            "grouped": {"proizvodi": [], "objave": []},
            "suggestion_count": 0,
            "too_short": True,
        }

    qs = build_product_search_qs(query, get_language())
    suggestion_count = qs.count()  # PRE slice — SM-D11
    proizvodi = list(qs[:_PER_GROUP]) if capped else list(qs)
    grouped = {"proizvodi": proizvodi, "objave": []}  # SM-D3 forward-compat

    context = {
        "query": query,
        "grouped": grouped,
        "suggestion_count": suggestion_count,
        "too_short": False,
    }
    if suggestion_count == 0:
        context.update(_empty_state_cta_context())
    return context


@require_GET
def search_dropdown(request):
    """HTMX dropdown endpoint — grouped FTS rezultati + OOB aria-live (SM-D14)."""
    query = request.GET.get("q", "").strip()[:_MAX_QUERY_LEN]
    context = _build_search_context(query)

    if context["too_short"] or context["suggestion_count"] == 0:
        return render(request, "search/partials/_search_empty.html", context)
    return render(request, "search/partials/_search_dropdown.html", context)


@require_GET
def search_results(request):
    """Non-HTMX /pretraga/ full strana — „Vidi sve" target (SM-D16)."""
    query = request.GET.get("q", "").strip()[:_MAX_QUERY_LEN]
    context = _build_search_context(query, capped=False)
    return render(request, "search/search_results.html", context)
