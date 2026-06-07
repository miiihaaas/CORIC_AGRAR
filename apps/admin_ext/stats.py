"""Story 8.3 — read-only agregaciona statistika za admin dashboard.

Cross-boundary čitanje domain modela (Lead/Product/Post) je dokumentovani izuzetak
(SM-D4 / arch:740): admin_ext SME da ČITA domain modele (agregacija), ali nijedan
domain app NE sme da importuje admin_ext. Importi domain modela su LOKALNI (unutar
funkcija) — circular-safe + samo `.objects`/`.count`/`.aggregate` (NIKAD `.save`).
"""

from __future__ import annotations

import logging

from django.db.models import Count
from django.utils import timezone

from apps.admin_ext.analytics import get_ga_visits

logger = logging.getLogger(__name__)


def get_lead_stats() -> dict[str, int]:
    """Segmentovan lead count za TEKUĆI kalendarski mesec (TZ-aware; AC2/AC3/AC8).

    Vraća TAČNO ključeve {contact, model_inquiry, service_request, part_request,
    total} gde je svaki broj `Lead` zapisa tog `form_type`-a kreiranih ovog meseca,
    a `total` je ZBIR 4 segmenta (single-source; AC2 total-semantika).

    Jedan agregacioni upit (`.values().annotate(Count)`) — `assertNumQueries(1)`
    na izolovan poziv (AC8/G-6). TZ-aware month_start (G-4/G-5/SM-D7).
    """
    from apps.forms.models import Lead

    month_start = timezone.now().replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    )

    # Single-source ključevi iz Lead.FormType (SM-D8) — svi 4 UVEK prisutni (default 0).
    stats: dict[str, int] = {ft.value: 0 for ft in Lead.FormType}

    # JEDAN agregat (NE per-segment petlja sa 4 .count() — G-6).
    rows = (
        Lead.objects.filter(created_at__gte=month_start)
        .values("form_type")
        .annotate(c=Count("id"))
    )
    for row in rows:
        if row["form_type"] in stats:
            stats[row["form_type"]] = row["c"]

    stats["total"] = sum(stats.values())
    return stats


def get_lead_segments(lead_stats: dict[str, int]) -> list[dict]:
    """(label, count) parovi za render segmenata bez hardkodovanih stringova (SM-D8).

    Single-source labela iz `Lead.FormType` — izbegava dict-lookup-po-promenljivoj-
    ključu u template-u. Lokalni import (cross-boundary; SM-D4).
    """
    from apps.forms.models import Lead

    return [{"label": ft.label, "count": lead_stats[ft.value]} for ft in Lead.FormType]


def get_content_stats() -> dict[str, int]:
    """Broj objavljenih proizvoda + objavljenih blog objava (AC4/AC8).

    - published_products = Product.objects.filter(is_published=True).count()
    - published_posts    = Post.published.count()  (NE Post.objects — G-7;
      manager = status='published' AND published_at <= now)
    """
    from apps.blog.models import Post
    from apps.products.models import Product

    return {
        "published_products": Product.objects.filter(is_published=True).count(),
        "published_posts": Post.published.count(),
    }


def get_dashboard_stats() -> dict:
    """Agregator: spaja lead + content + GA statistiku za `extra_context` (AC1).

    GA poziv obavijen `try/except Exception` (NE bare except — fail-safe granica;
    AC5/G-9). Na BILO KOJI izuzetak loguje WARNING (BEZ PII; AC9/G-10) i vraća
    None-ove → dashboard se UVEK učita (HTTP 200).
    """
    try:
        ga_visits = get_ga_visits()
    except Exception:  # noqa: BLE001 — fail-safe granica; dashboard se UVEK učita (AC5/G-9)
        logger.warning("GA posete nedostupne — fallback na N/D (Epic 9).")
        ga_visits = {"last_7": None, "last_30": None}

    lead_stats = get_lead_stats()

    return {
        "lead_stats": lead_stats,
        "lead_segments": get_lead_segments(lead_stats),
        "content_stats": get_content_stats(),
        "ga_visits": ga_visits,
    }
