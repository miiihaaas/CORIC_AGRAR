"""Story 9.4 — `/healthz/` health-check endpoint (UptimeRobot liveness probe).

TEA RED faza: SVI testovi MORAJU PASTI dok Dev ne implementira `healthz` FBV u
`apps/core/views.py` i ne ožiči `path("healthz/", ...)` u NON-i18n bloku
`config/urls.py`. Trenutno `apps/core/views.py` je prazan i `/healthz/` nije
ožičen → ImportError na `healthz`, NoReverseMatch na `reverse("healthz")`,
404 na `GET /healthz/`.

Pokreni (targetiran modul, izbegava libmagic baseline collect na host-u):
    uv run pytest apps/core/tests/test_healthz.py -p no:cacheprovider -v

Pokriva AC1-AC6 (AC7/AC8 = manual go-live runbook gate, NIJE automatizovan).
Naming convention: srpska latinica + engleski; bez ćirilice.
"""

from __future__ import annotations

from pathlib import Path

from django.test import RequestFactory, TestCase
from django.urls import resolve, reverse

from apps.core.views import healthz

PROJECT_ROOT = Path(__file__).resolve().parents[3]
VIEWS_PY = PROJECT_ROOT / "apps" / "core" / "views.py"


def _views_source() -> str:
    """Procitaj sirov izvor apps/core/views.py (static guard za dekoratore/import-e)."""
    return VIEWS_PY.read_text(encoding="utf-8")


# =============================================================================
# AC1 — GET /healthz/ → 200 + keyword "ok" + text/plain + info-empty body
# =============================================================================


class HealthzResponseTests(TestCase):
    """AC1/AC2/AC5 — request/response ponasanje kroz Django test client."""

    def test_get_healthz_returns_200(self):
        # AC1 — GET /healthz/ vraca HTTP 200
        response = self.client.get("/healthz/")
        self.assertEqual(response.status_code, 200)

    def test_body_contains_ok_keyword(self):
        # AC1 — body sadrzi stabilan keyword "ok" (UptimeRobot keyword-monitor)
        response = self.client.get("/healthz/")
        self.assertIn(b"ok", response.content)

    def test_content_type_is_text_plain(self):
        # AC1 — Content-Type je text/plain
        response = self.client.get("/healthz/")
        self.assertTrue(
            response["Content-Type"].startswith("text/plain"),
            f"ocekivan text/plain, dobijen: {response['Content-Type']!r}",
        )

    def test_body_is_exactly_ok_no_info_leak(self):
        # AC1 / SM-D6 / G-7 — body je TACNO b"ok"; NE curi env/secret/version/hostname.
        # Stroga asercija: bilo kakav dodatni sadrzaj je info-leak regresija.
        response = self.client.get("/healthz/")
        self.assertEqual(response.content, b"ok")

    def test_body_has_no_sensitive_patterns(self):
        # AC1 / SM-D6 — defenzivni guard: body ne sme sadrzati osetljive marker-e.
        response = self.client.get("/healthz/")
        lowered = response.content.lower()
        for needle in (b"secret", b"version", b"django", b"sql", b"traceback", b"password"):
            self.assertNotIn(needle, lowered, f"info-leak: body sadrzi {needle!r}")

    # =========================================================================
    # AC2 — anoniman klijent → 200 (NE 302-na-login, NE 403)
    # =========================================================================

    def test_anonymous_client_gets_200_not_login_redirect(self):
        # AC2 — default test client je anoniman (bez session/Authorization).
        # assertEqual(200) je najjaca asercija: 200 implicitno iskljucuje 302-na-login i 403.
        response = self.client.get("/healthz/")
        self.assertEqual(response.status_code, 200)

    def test_no_auth_decorator_in_view_source(self):
        # AC2 — view source nema @login_required / permission dekorator (regression guard)
        source = _views_source()
        self.assertNotIn("login_required", source)
        self.assertNotIn("permission_required", source)

    # =========================================================================
    # AC5 — GET /healthz/ → 200 direktno, NE 301/302 (no-redirect)
    # =========================================================================

    def test_healthz_is_not_redirected(self):
        # AC5 / G-4 — pod development settings (SECURE_SSL_REDIRECT default False)
        # endpoint vraca 200 direktno, nikad 301/302.
        response = self.client.get("/healthz/")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(response.status_code, (301, 302))

    # =========================================================================
    # AC4 (a) — funkcionalni burst: 20+ rapid GET → svi 200, nijedan 429
    # =========================================================================

    def test_burst_requests_all_return_200_none_429(self):
        # AC4 (a) — UptimeRobot + vise monitora + retry burst NE sme da pogodi
        # ratelimit (429 bi UptimeRobot procitao kao "down").
        for i in range(25):
            response = self.client.get("/healthz/")
            self.assertEqual(response.status_code, 200, f"burst zahtev #{i} != 200")
            self.assertNotEqual(response.status_code, 429, f"burst zahtev #{i} == 429 (ratelimit!)")

    # =========================================================================
    # G-13 — HEAD vs GET (dokumentacioni test, NE failure trap)
    # =========================================================================

    def test_head_request_responds_200(self):
        # G-13 — Django servira HEAD (200, prazan body je OK). Dokumentuje da
        # endpoint odgovara na HEAD, ALI UptimeRobot keyword monitor MORA koristiti
        # GET (HEAD strip-uje body → keyword "ok" se ne bi nasao). Dokumentacioni.
        response = self.client.head("/healthz/")
        self.assertEqual(response.status_code, 200)


# =============================================================================
# AC3 — /healthz/ rezolvira BEZ locale prefiksa (non-i18n blok)
# =============================================================================


class HealthzUrlResolutionTests(TestCase):
    """AC3 — reverse/resolve bez locale prefiksa + negativni /sr/ guard.

    TestCase (NE SimpleTestCase): negativni guard `GET /sr/healthz/` prolazi kroz
    pages catch-all `<slug:slug>/` koji radi DB lookup (Page slug) pre 404 → potreban
    DB pristup. reverse/resolve testovi su cisto URL-resolver, ali deli ih klasa.
    """

    def test_reverse_has_no_locale_prefix(self):
        # AC3 / SM-D2 — reverse("healthz") == "/healthz/" (NE "/sr/healthz/")
        self.assertEqual(reverse("healthz"), "/healthz/")

    def test_resolve_maps_to_healthz_view(self):
        # AC3 — resolve("/healthz/") mapira na healthz callable, url_name "healthz"
        match = resolve("/healthz/")
        self.assertEqual(match.url_name, "healthz")
        self.assertIs(match.func, healthz)

    def test_sr_prefixed_path_does_not_resolve_to_healthz(self):
        # AC3 (negative guard): /sr/healthz/ must NOT resolve to healthz
        # healthz je ozicen VAN i18n_patterns (goli /healthz/). Locale-prefiksovana
        # putanja /sr/healthz/ ide kroz i18n_patterns; nijedan include je ne matchuje
        # i pages catch-all <slug:slug>/ ne nalazi Page slug "healthz" → 404.
        # Regresioni lock: ako neko premesti healthz U i18n_patterns, ovo pada.
        self.assertEqual(self.client.get("/sr/healthz/").status_code, 404)


# =============================================================================
# AC4 (b) — regression guard: view source bez @ratelimit dekoratora
# AC6 — view emituje 0 query-ja (RequestFactory direktan poziv) + leaf cleanliness
# =============================================================================


class HealthzViewStaticAndQueryTests(TestCase):
    """AC4(b)/AC6 — staticki guard nad source-om + direktan view-callable query count."""

    def test_view_source_has_no_ratelimit_decorator(self):
        # AC4 (b) — regression guard: @ratelimit NE sme biti na health view-u (SM-D7)
        source = _views_source()
        self.assertNotIn("ratelimit", source.lower())

    def test_view_source_has_no_domain_model_imports(self):
        # AC6 / G-3 — apps.core je LEAF: view NE importuje domain apps
        source = _views_source()
        for forbidden in (
            "from apps.products",
            "from apps.brands",
            "from apps.blog",
            "from apps.pages",
            "import apps.products",
            "import apps.brands",
            "import apps.blog",
            "import apps.pages",
        ):
            self.assertNotIn(forbidden, source, f"leaf prekrsaj: {forbidden!r}")

    def test_direct_view_call_emits_zero_queries(self):
        # AC6 (KANONSKI, G-9) — assertNumQueries(0) oko DIREKTNOG view-callable poziva
        # (RequestFactory zaobilazi middleware stack; client.get bi okinuo
        # RedirectMiddleware DB lookup → NE asertujemo query count kroz client).
        request = RequestFactory().get("/healthz/")
        with self.assertNumQueries(0):
            response = healthz(request)
        self.assertEqual(response.status_code, 200)

    def test_direct_view_call_body_is_ok(self):
        # AC6 — direktan poziv vraca body b"ok" (bez middleware-a)
        request = RequestFactory().get("/healthz/")
        response = healthz(request)
        self.assertEqual(response.content, b"ok")
