"""Tests za Story 1.4 - AC3: LocaleSwitcherMiddleware (signature + behavior).

Verifikuje:
- AC3: middleware klasa importable iz apps.core.middleware
- AC3: __init__(get_response) + __call__(request) signature (Django middleware contract)
- AC3 (CRITICAL anti-regression): NE referencira translation.LANGUAGE_SESSION_KEY
  (uklonjeno u Django 4.0 — AttributeError na prvi ?lang=sr request)
- AC3: cookie-only persistencija (settings.LANGUAGE_COOKIE_NAME, NE hardcoded string)
- AC3: behavior — ?lang=hu aktivira hu lokal + set cookie; ?lang=de (unsupported) ignoriše

Pokrenuti sa:
    uv run pytest apps/core/tests/test_middleware.py -v

TEA RED faza: svi testovi MORAJU pasti dok Dev ne zavrsi Story 1.4.
Naming convention: srpska latinica + engleski; bez cirilice.
"""

from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

import pytest

# =============================================================================
# Konstante (project paths)
# =============================================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
MIDDLEWARE_PY = PROJECT_ROOT / "apps" / "core" / "middleware.py"

TEST_SECRET = "test-secret-key-for-tea-story-1-4-middleware-not-real"


# =============================================================================
# Helper funkcije
# =============================================================================


def _ensure_sys_path():
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))


def _setup_django():
    """Bootstrap Django (settings configured) sa DJANGO_SECRET_KEY env varom."""
    _ensure_sys_path()
    os.environ.setdefault("DJANGO_SECRET_KEY", TEST_SECRET)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
    try:
        import django
    except ImportError:  # pragma: no cover
        pytest.fail("Django nije instaliran (uv sync prvo).")
    if not getattr(django, "_setup_done", False):
        django.setup()
        django._setup_done = True  # type: ignore[attr-defined]


def _read_middleware_source() -> str:
    """Procita apps/core/middleware.py source. Fail-uje ako ne postoji."""
    if not MIDDLEWARE_PY.exists():
        pytest.fail(
            f"apps/core/middleware.py ne postoji na {MIDDLEWARE_PY}. "
            f"Story 1.4 AC3 zahteva LocaleSwitcherMiddleware klasu."
        )
    return MIDDLEWARE_PY.read_text(encoding="utf-8")


def _import_middleware_class():
    """Importuje LocaleSwitcherMiddleware. Fail-uje sa jasnom porukom ako ne ide."""
    _ensure_sys_path()
    # Force fresh import
    for mod_key in list(sys.modules.keys()):
        if mod_key.startswith("apps.core.middleware"):
            del sys.modules[mod_key]
    try:
        module = importlib.import_module("apps.core.middleware")
    except ImportError as exc:
        pytest.fail(
            f"Ne mogu importovati apps.core.middleware: {exc}. "
            f"Verovatno fajl ne postoji ili ima sintaksne greske."
        )
    if not hasattr(module, "LocaleSwitcherMiddleware"):
        pytest.fail(
            "apps.core.middleware ne eksponuje klasu LocaleSwitcherMiddleware. "
            "Mora biti definisana sa __init__(get_response) + __call__(request) signature."
        )
    return module.LocaleSwitcherMiddleware


# =============================================================================
# AC3 — Class importability + signature
# =============================================================================


def test_ac3_middleware_class_importable():
    """AC3: `from apps.core.middleware import LocaleSwitcherMiddleware` mora raditi."""
    cls = _import_middleware_class()
    assert cls is not None
    assert cls.__name__ == "LocaleSwitcherMiddleware", (
        f"Klasa ima neocekivano ime: {cls.__name__!r}, ocekivano 'LocaleSwitcherMiddleware'."
    )


def test_ac3_middleware_init_signature():
    """AC3 / Gotcha #2: middleware MORA imati __init__(self, get_response).

    Django middleware contract (od 1.10 SOT): NE process_request/process_response
    (deprecated MIDDLEWARE_CLASSES style — uklonjeno u Django 4.x).
    """
    cls = _import_middleware_class()
    # Instantirati sa dummy get_response — ne sme baciti exception
    try:
        instance = cls(lambda request: None)
    except TypeError as exc:
        pytest.fail(
            f"LocaleSwitcherMiddleware(get_response) baca TypeError: {exc}. "
            f"Verovatno __init__ ima pogresan signature. "
            f"Mora biti `def __init__(self, get_response):` (Django middleware contract)."
        )
    assert hasattr(instance, "get_response"), (
        "LocaleSwitcherMiddleware instanca ne cuva self.get_response. "
        "Mora postojati `self.get_response = get_response` u __init__."
    )
    # __call__ mora postojati
    assert callable(instance), (
        "LocaleSwitcherMiddleware instanca nije callable — nedostaje __call__(request) metod."
    )


# =============================================================================
# AC3 — CRITICAL anti-regression (LANGUAGE_SESSION_KEY uklonjen u Django 4.0)
# =============================================================================


def test_ac3_middleware_no_language_session_key_reference():
    """AC3 / Gotcha #7 KRITICNO: source NE SME sadrzati `LANGUAGE_SESSION_KEY`.

    `django.utils.translation.LANGUAGE_SESSION_KEY` je UKLONJEN u Django 4.0
    (NIJE deprecated, NIJE alias). Pokusaj `translation.LANGUAGE_SESSION_KEY`
    baca AttributeError na prvi ?lang=sr request.

    Ovaj anti-regression test sprecava Dev (ili future copy-paste od stale Django
    docs) da uvede session-based persistenciju koja BREAKS u Django 5.2.

    Iteration-1 lesson: ovaj attribut je tiho falio u prvoj implementaciji —
    smoke test prosao, ali production-level switcher dropdown padao.
    """
    src = _read_middleware_source()
    # Stripuj komentare i docstring-ove da bi se izbeglo lazno pozitivno hvatanje
    # NAPOMENA: docstring smije pominjati `LANGUAGE_SESSION_KEY` u napomeni
    # (informativno), ali u izvrsnom kodu NE SME. Heuristika: trazimo string van
    # # komentara i van trostrukih navodnika.
    bad_lines = []
    in_docstring = False
    docstring_delim = None
    for raw in src.splitlines():
        line = raw.strip()
        # Preskoci komentare
        if line.startswith("#"):
            continue
        # Detektuj ulaz/izlaz iz docstring blokova (heuristicki — '''...''' ili """..."""):
        for delim in ('"""', "'''"):
            if delim in line:
                # Broj pojavljivanja - parno znaci da se sve zatvara u istoj liniji
                count = line.count(delim)
                if count % 2 == 1:
                    if not in_docstring:
                        in_docstring = True
                        docstring_delim = delim
                    elif docstring_delim == delim:
                        in_docstring = False
                        docstring_delim = None
                break
        if in_docstring:
            continue
        if "LANGUAGE_SESSION_KEY" in line:
            bad_lines.append(raw)
    assert not bad_lines, (
        f"apps/core/middleware.py izvrsni kod sadrzi `LANGUAGE_SESSION_KEY` "
        f"reference: {bad_lines}. "
        f"Gotcha #7: atribut je UKLONJEN u Django 4.0 — pokusaj baca AttributeError. "
        f"Koristi cookie-only mehanizam: `translation.activate(lang)` + "
        f"`response.set_cookie(settings.LANGUAGE_COOKIE_NAME, lang, ...)`."
    )


def test_ac3_middleware_cookie_only_persistence():
    """AC3: middleware koristi `response.set_cookie(...)` sa `settings.LANGUAGE_COOKIE_NAME`.

    Cookie name MORA doci iz settings-a (NE hardcoded 'django_language') —
    Django moze override-ovati ime u project settings-u (npr. 'coric_lang').
    """
    src = _read_middleware_source()
    assert "response.set_cookie(" in src, (
        "apps/core/middleware.py ne sadrzi `response.set_cookie(...)` poziv. "
        "Story 1.4 AC3 zahteva cookie persistenciju lokala."
    )
    assert "settings.LANGUAGE_COOKIE_NAME" in src, (
        "apps/core/middleware.py ne koristi `settings.LANGUAGE_COOKIE_NAME` za cookie ime. "
        "NE hardcoded string ('django_language') — Django dozvoljava override "
        "u project settings-u, middleware mora postovati."
    )


# =============================================================================
# AC3 — Behavior (RequestFactory + manual middleware invocation)
# =============================================================================


def test_ac3_middleware_lang_query_param_handling():
    """AC3: behavior test sa RequestFactory + manual middleware invocation.

    Verifikuje:
    - ?lang=hu (supported): vraca 302 redirect (translate_url) + postavlja cookie
    - ?lang=de (unsupported): pass-through (dummy_view zvani), ne postavlja cookie
    - bez ?lang: pass-through, ne postavlja cookie

    NAPOMENA (refactor post Story 1.4 review): middleware vise NE poziva
    `translation.activate(lang)` u-place + forward — umesto toga vraca 302 na
    prevedenu URL putanju (sledi `django.views.i18n.set_language` pattern).
    Razlog: aktivacija lokala PRE URL resolvera ne pomaze jer resolver matchuje
    `i18n_patterns()` prefix prema URL-u (npr. `/sr/...?lang=hu` daje 404).
    """
    try:
        _setup_django()
    except Exception as exc:
        pytest.skip(f"Django setup nije moguc (pytest-django nije konfigurisan?): {exc}")

    try:
        from django.conf import settings
        from django.http import HttpResponse, HttpResponseRedirect
        from django.test import RequestFactory
        from django.utils import translation
    except ImportError as exc:
        pytest.skip(f"Django Client/RequestFactory nedostupan: {exc}")

    cls = _import_middleware_class()

    # Dummy view (poziva se SAMO kad middleware ne presretne request-om sa ?lang=).
    captured = {"called": False}

    def dummy_view(request):
        captured["called"] = True
        return HttpResponse("")

    middleware = cls(dummy_view)
    rf = RequestFactory()

    # --- Test 1: ?lang=hu (supported) — vraca 302 redirect + set cookie ---
    translation.activate("sr")
    captured["called"] = False
    request = rf.get("/?lang=hu")
    response = middleware(request)
    cookie_name = settings.LANGUAGE_COOKIE_NAME
    assert response.status_code == 302, (
        f"Posle ?lang=hu request-a, response status = {response.status_code}, ocekivano 302. "
        f"Middleware MORA vratiti redirect (sledi set_language pattern)."
    )
    assert isinstance(response, HttpResponseRedirect), (
        f"Response tip = {type(response).__name__}, ocekivano HttpResponseRedirect."
    )
    assert not captured["called"], (
        "Dummy view JE pozvan iako je middleware trebalo da presretne sa redirect-om."
    )
    assert cookie_name in response.cookies, (
        f"Posle ?lang=hu request-a, response NEMA `{cookie_name}` cookie. "
        f"Middleware mora pozvati `response.set_cookie(settings.LANGUAGE_COOKIE_NAME, 'hu', ...)`."
    )
    assert response.cookies[cookie_name].value == "hu", (
        f"Cookie `{cookie_name}` value = {response.cookies[cookie_name].value!r}, "
        f"ocekivano 'hu'."
    )

    # --- Test 2: ?lang=de (unsupported) — pass-through, NE postavlja cookie ---
    translation.activate("sr")
    captured["called"] = False
    request = rf.get("/?lang=de")
    try:
        response = middleware(request)
    except Exception as exc:  # pragma: no cover
        pytest.fail(
            f"?lang=de (unsupported) MORA biti tiho ignorisan, a middleware baca: {exc}. "
            f"Trust-but-verify pattern (AC3): NE raise-ovati exception za invalid lokal."
        )
    assert captured["called"], (
        "Dummy view NIJE pozvan za ?lang=de — middleware mora pass-through-ovati "
        "unsupported lokal kodove."
    )
    assert response.status_code == 200, (
        f"?lang=de pass-through status = {response.status_code}, ocekivano 200 (dummy_view)."
    )
    assert cookie_name not in response.cookies, (
        f"Posle ?lang=de (unsupported) request-a, cookie `{cookie_name}` JE postavljen. "
        f"Middleware mora ignorisati nepoznate lokale (AC3 trust-but-verify)."
    )

    # --- Test 3: bez ?lang param — pass-through, ne menja stanje ---
    translation.activate("sr")
    captured["called"] = False
    request = rf.get("/")
    response = middleware(request)
    assert captured["called"], (
        "Dummy view NIJE pozvan bez ?lang — middleware mora pass-through-ovati."
    )
    assert cookie_name not in response.cookies, (
        f"Request bez `?lang` query parametra je postavio `{cookie_name}` cookie. "
        f"Middleware sme postaviti cookie SAMO kada se lokal eksplicitno menja."
    )


def test_ac3_middleware_cross_prefix_lang_redirects():
    """AC3 regression: `?lang=hu` na `/sr/...` putanji MORA dati 302 na `/hu/...`.

    Empirically verified bug (pre-fix): `GET /sr/?lang=hu` vracao 404 jer je
    middleware bio registrovan POSLEDNJI i `translation.activate(hu)` PRE URL
    resolvera nije pomagao — resolver matchuje URL prefix `/sr/` pa pod `hu`
    lokal-om nema patterna. Fix: middleware sada vraca 302 na translate_url().
    """
    try:
        _setup_django()
    except Exception as exc:
        pytest.skip(f"Django setup nije moguc: {exc}")

    try:
        from django.http import HttpResponse, HttpResponseRedirect
        from django.test import RequestFactory
    except ImportError as exc:
        pytest.skip(f"Django RequestFactory nedostupan: {exc}")

    cls = _import_middleware_class()

    def dummy_view(request):  # pragma: no cover — middleware presrece, ne bi smelo da bude pozvano
        return HttpResponse("")

    middleware = cls(dummy_view)
    rf = RequestFactory()
    # Simuliramo request na /sr/ putanji sa ?lang=hu — middleware mora redirektovati na /hu/
    request = rf.get("/sr/?lang=hu")
    response = middleware(request)

    assert response.status_code == 302, (
        f"GET /sr/?lang=hu vraca status {response.status_code}, ocekivano 302 redirect. "
        f"Cross-prefix redirect je fix za 404 bug iz Story 1.4 review (Dev-B BUG HIGH)."
    )
    assert isinstance(response, HttpResponseRedirect), (
        f"Response tip = {type(response).__name__}, ocekivano HttpResponseRedirect."
    )
    location = response.headers.get("Location", "") or response.get("Location", "")
    assert location.startswith("/hu/") or location == "/hu/", (
        f"Redirect Location = {location!r}, ocekivano da pocinje sa '/hu/'. "
        f"translate_url() mora prepisati locale prefix `/sr/` u `/hu/`."
    )
