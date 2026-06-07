"""Story 8.3 — GA Reporting API graceful stub (AC5 / SM-D6).

v1: GA Reporting API NIJE konfigurisan (nema service-account kredencijala, nema
`google-analytics-data` lib-a, nema `GA_PROPERTY_ID`-a u settings). Funkcija vraća
None-ove BEZ mrežnog poziva i BEZ izuzetka. Uključiva kasnije (Epic 9 / OQ-1) kroz
`getattr(settings, "GA_PROPERTY_ID", "")`.

Postojeći `GA_MEASUREMENT_ID` (base.py) je client-side GA4 measurement ID (tracking
pixel, 7.3) — NIJE Reporting API property → ne koristi se ovde.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def get_ga_visits() -> dict[str, int | None]:
    """Vrati posete za 7/30 dana iz GA Reporting API-ja (v1 stub — None-ovi).

    Vraća {"last_7": <int|None>, "last_30": <int|None>}. U v1 (nekonfigurisan GA)
    → {"last_7": None, "last_30": None} BEZ mrežnog poziva i BEZ izuzetka (SM-D6).
    """
    from django.conf import settings

    property_id = getattr(settings, "GA_PROPERTY_ID", "")
    if not property_id:
        # GA Reporting API nije konfigurisan u v1 → graceful None-ovi (Epic 9 / OQ-1).
        return {"last_7": None, "last_30": None}

    # Mesto za pravu integraciju (Epic 9). Do tada nedostižno — fail-safe None-ovi.
    return {"last_7": None, "last_30": None}
