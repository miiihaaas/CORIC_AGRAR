"""Story 8.3 — PINOVAN admin-index override wrapper (SM-D1 / G-1 / G-12).

`admin.site.index` se zamenjuje wrapper-om koji injektuje dashboard statistiku kroz
`extra_context` i DELEGIRA na SAČUVAN original. `make_dashboard_index(original)` se
poziva iz `apps.py:ready()` SA originalom uhvaćenim PRE reassignment-a → bez metodne
rekurzije (G-12); original gradi `app_list` → navigacija zadržana (SM-D2/G-2).
`index_template` se postavlja u `apps.py:ready()` na zaseban fajl koji
`{% extends "admin/index.html" %}` (parent = Django ugrađeni, NE samog sebe → bez
template rekurzije, G-1).

RBAC: pristup ide kroz standardni admin `is_staff` gate (AC7/SM-D5) — bez dodatnog
mixina jer wrapper delegira na admin index unutar admin sajta.
"""

from __future__ import annotations

from collections.abc import Callable


def make_dashboard_index(original_index: Callable) -> Callable:
    """Vraća wrapper koji injektuje stats u `extra_context` i delegira na ORIGINAL.

    `original_index` se hvata u `ready()` PRE reassignment-a `admin.site.index`
    (recursion guard — G-12), pa se predaje ovde kroz closure.
    """

    def dashboard_index(request, extra_context=None):
        # Lazy import — stats čita domain modele (SM-D4); izbegava import-order probleme.
        from apps.admin_ext.stats import get_dashboard_stats

        ctx = {**(extra_context or {}), **get_dashboard_stats()}
        return original_index(request, extra_context=ctx)

    return dashboard_index
