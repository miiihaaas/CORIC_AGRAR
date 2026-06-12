"""Views za apps.core.

Story 3.1 (C1): `home` stub je UKLONJEN — home view se preselio u
`apps/pages/views.py` (`HomeView`). `apps/core` ostaje leaf — NE sme
importovati domain apps (architecture.md).

Story 9.4: `/healthz/` liveness probe za UptimeRobot. Jedini view ovde —
Django stdlib only (`HttpResponse`), 0 domain importa → leaf čistoća očuvana.
"""

from django.http import HttpResponse


def healthz(request):
    """Liveness probe za UptimeRobot (Story 9.4). Plain 200, bez auth, bez DB.

    NE dira bazu (SM-D4): uptime monitor NE sme da flap-uje na DB hiccup — DB
    problemi se page-uju kroz GlitchTip (9.3 error tracking), NE kroz uptime
    monitor. Body je STROGO `ok` i informaciono prazan (SM-D6 / G-7) — NIKAD
    env / secret / version / hostname / git-sha leak (javan endpoint bez auth).

    Bez auth dekoratora (AC2), bez rate-limit dekoratora (AC4/SM-D7), bez DB
    query-ja (AC6), bez domain importa (G-3 leaf). UptimeRobot keyword-monitor
    traži keyword `ok` (vidi ops/monitoring/uptimerobot.md).
    """
    return HttpResponse("ok", content_type="text/plain")
