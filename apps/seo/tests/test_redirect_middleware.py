"""Story 6.4 — RedirectMiddleware end-to-end (TEA RED phase, AC2/AC4/AC6/AC7).

Django test `client.get()` prolazi kroz CEO middleware lanac (RedirectMiddleware
PRE Locale). Pokriva:
- AC2: aktivno pravilo → 301 + Location == new_path.
- AC4: is_active=False → passthrough (NIJE 301); aktiviraj → 301.
- AC2/SM-D3: admin path (`/sr/admin/...`) skip — NIJE naš 301; forward-safe
  `/sr/admin-coric/...` (Epic 8 slug) TAKOĐE skip (CRITICAL-2 lock).
- AC6/SM-D7: `/hu/stara/` NE matchuje `/sr/stara/` rule (raw-path razlika).
- AC7/SM-D4: query-budget — `CaptureQueriesContext` filtriran na `seo_redirect`:
  static path → 0 Redirect upita; normalan path → TAČNO 1 Redirect upit.

⚠️ Pravila kreiramo kroz `Redirect.objects.create(...)` (save()-validirano). Za
admin-skip pravila (old_path pod /sr/admin/) NEMA open-redirect problema jer je
new_path site-internal.

Refs:
- 6-4-redirect-manager-301.md AC2/AC4/AC6/AC7 + Task 3/6.3 + SM-D1/D3/D4/D5/D7
- 6-4-interface-contract.md § 2. Middleware
"""

from __future__ import annotations

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

pytestmark = pytest.mark.django_db


def _redirect_queries(ctx):
    """Filtriraj uhvaćene upite na one koji pominju `seo_redirect` tabelu (Redirect lookup).

    NE meri session/auth/contenttype/csp upite — skip-budget se odnosi ISKLJUČIVO
    na Redirect model lookup (AC7/SM-D4). NIKAD bare assertNumQueries na ceo request.
    """
    return [q for q in ctx.captured_queries if "seo_redirect" in q["sql"]]


# AC2: aktivno pravilo → 301 + Location == new_path
def test_active_rule_returns_301_with_location():
    from apps.seo.models import Redirect

    Redirect.objects.create(old_path="/sr/stara/", new_path="/sr/nova/", is_active=True)

    from django.test import Client

    response = Client().get("/sr/stara/")
    assert response.status_code == 301, (
        f"Aktivno pravilo /sr/stara/ MORA dati 301, dobio {response.status_code} "
        "(HttpResponsePermanentRedirect — AC2/SM-D5)."
    )
    assert response["Location"] == "/sr/nova/", (
        f"Location MORA biti new_path '/sr/nova/', dobio {response.get('Location')!r} (AC2)."
    )


# AC4: is_active=False → passthrough (NIJE 301); aktiviraj → 301
def test_inactive_rule_not_applied_then_activated():
    from apps.seo.models import Redirect
    from django.test import Client

    r = Redirect.objects.create(old_path="/sr/x/", new_path="/sr/y/", is_active=False)

    response = Client().get("/sr/x/")
    assert response.status_code != 301, (
        "is_active=False pravilo NE SME redirektovati (filter is_active=True → no match — AC4)."
    )

    r.is_active = True
    r.save()
    response2 = Client().get("/sr/x/")
    assert response2.status_code == 301 and response2["Location"] == "/sr/y/", (
        "Posle aktivacije (is_active=True) GET /sr/x/ MORA dati 301 → /sr/y/ (AC4)."
    )


# AC2: no-match path → NIJE 301 (passthrough)
def test_no_match_passthrough():
    from django.test import Client

    response = Client().get("/sr/ne-postoji-pravilo/")
    assert response.status_code != 301, (
        "Path bez matchujućeg pravila NE SME biti 301 (no-match passthrough — AC2)."
    )


# AC2/SM-D3: admin path skip — pravilo pod /sr/admin/ NE proizvodi naš 301
def test_admin_path_skipped():
    from apps.seo.models import Redirect
    from django.test import Client

    Redirect.objects.create(old_path="/sr/admin/secret/", new_path="/sr/nova/", is_active=True)

    response = Client().get("/sr/admin/secret/")
    # admin može vratiti 302-na-login ILI 200/404, ALI NE NAŠ 301-na-new_path
    is_our_301 = response.status_code == 301 and response.get("Location") == "/sr/nova/"
    assert not is_our_301, (
        "Middleware MORA preskočiti admin path (/sr/admin/...) PRE DB lookup-a — "
        "NE sme vratiti naš 301-na-new_path (SM-D3/SEO4-4)."
    )


# AC2/SM-D3 CRITICAL-2: forward-safe admin slug — /sr/admin-coric/ (Epic 8) TAKOĐE skip
def test_future_admin_coric_path_skipped():
    from apps.seo.models import Redirect
    from django.test import Client

    Redirect.objects.create(
        old_path="/sr/admin-coric/secret/", new_path="/sr/nova/", is_active=True
    )

    response = Client().get("/sr/admin-coric/secret/")
    is_our_301 = response.status_code == 301 and response.get("Location") == "/sr/nova/"
    assert not is_our_301, (
        "Forward-safe admin skip MORA pokriti i budući `admin-coric` slug (Epic 8) — "
        "dokazuje da skip NIJE krhki '/admin/' substring (CRITICAL-2/SM-D3/SEO4-4)."
    )


# AC6/SM-D7: /hu/stara/ NE matchuje /sr/stara/ rule (raw-path razlika)
def test_locale_specific_rule_does_not_cross_match():
    from apps.seo.models import Redirect
    from django.test import Client

    Redirect.objects.create(old_path="/sr/stara/", new_path="/sr/nova/", is_active=True)

    response = Client().get("/hu/stara/")
    is_our_301 = response.status_code == 301 and response.get("Location") == "/sr/nova/"
    assert not is_our_301, (
        "/hu/stara/ NE SME matchovati /sr/stara/ rule (locale-specifični raw-path — AC6/SM-D7)."
    )


# AC7/SM-D4: static path → ZERO Redirect upita (skip PRE DB lookup)
def test_static_path_zero_redirect_queries():
    # Kreiraj pravilo koje BI matchovalo static path da skip ne radi — dokazuje da
    # je skip PRE lookup-a, ne samo „nema pravila". (Import Redirect → RED dok model
    # ne postoji.)
    from apps.seo.models import Redirect
    from django.test import Client

    Redirect.objects.create(old_path="/static/css/app.css", new_path="/sr/x/", is_active=True)

    with CaptureQueriesContext(connection) as ctx:
        Client().get("/static/css/app.css")
    redirect_q = _redirect_queries(ctx)
    assert len(redirect_q) == 0, (
        "static path (/static/...) NE SME praviti NIJEDAN Redirect upit (skip PRE lookup — "
        f"AC7/SM-D4). Uhvaćeni Redirect upiti: {[q['sql'] for q in redirect_q]}"
    )


# AC7/SM-D4: media path → ZERO Redirect upita (skip PRE DB lookup — simetrično static-u)
def test_media_path_zero_redirect_queries():
    # Kreiraj pravilo koje BI matchovalo media path da skip ne radi — dokazuje da
    # je skip PRE lookup-a, ne samo „nema pravila". `/media/` je u _SKIP_PREFIXES
    # zajedno sa `/static/` (mirror test_static_path_zero_redirect_queries).
    from apps.seo.models import Redirect
    from django.test import Client

    Redirect.objects.create(
        old_path="/media/uploads/file.pdf", new_path="/sr/x/", is_active=True
    )

    with CaptureQueriesContext(connection) as ctx:
        Client().get("/media/uploads/file.pdf")
    redirect_q = _redirect_queries(ctx)
    assert len(redirect_q) == 0, (
        "media path (/media/...) NE SME praviti NIJEDAN Redirect upit (skip PRE lookup — "
        f"AC7/SM-D4). Uhvaćeni Redirect upiti: {[q['sql'] for q in redirect_q]}"
    )


# AC7/SM-D4: admin path → ZERO Redirect upita (skip PRE DB lookup — dostupnost admin-a)
def test_admin_path_zero_redirect_queries():
    # Pravilo koje BI matchovalo admin path da skip ne radi (dokazuje skip-PRE-lookup).
    from apps.seo.models import Redirect
    from django.test import Client

    Redirect.objects.create(old_path="/sr/admin/", new_path="/sr/x/", is_active=True)

    with CaptureQueriesContext(connection) as ctx:
        Client().get("/sr/admin/")
    redirect_q = _redirect_queries(ctx)
    assert len(redirect_q) == 0, (
        "admin path NE SME praviti Redirect upit (skip PRE lookup — dostupnost admin-a; "
        f"AC7/SM-D4/SEO4-4). Uhvaćeni Redirect upiti: {[q['sql'] for q in redirect_q]}"
    )


# AC7/SM-D4: normalan path → TAČNO 1 Redirect upit (indeksiran exact lookup)
def test_normal_path_exactly_one_redirect_query():
    from django.test import Client

    with CaptureQueriesContext(connection) as ctx:
        Client().get("/sr/neki-normalan-put/")
    redirect_q = _redirect_queries(ctx)
    assert len(redirect_q) == 1, (
        "Normalan (ne-skip) path MORA praviti TAČNO 1 Redirect upit (indeksiran "
        f"filter(old_path=..., is_active=True).first() — AC7/SM-D4). "
        f"Dobio {len(redirect_q)}: {[q['sql'] for q in redirect_q]}"
    )
