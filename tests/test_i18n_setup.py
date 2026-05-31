"""Tests za Story 1.4 - i18n setup, URL routing, language switcher, locale dirs.

Pokriva:
- AC2: config/settings/base.py modifikacije (LANGUAGE_CODE, LANGUAGES, LOCALE_PATHS,
       MIDDLEWARE order, TEMPLATES DIRS + i18n context processor, INSTALLED_APPS)
- AC5: config/urls.py — i18n_patterns + set_language registracija + HTTP behavior
- AC6: templates/base.html — minimalan layout sa <html lang>, {% load i18n %}, blocks
- AC7: templates/partials/language_switcher.html — POST forma sa csrf + 3 opcije
- AC8: locale/{sr,hu,en}/LC_MESSAGES/ direktorijumi + justfile messages recept
- Negative / regression: bez cirilice, bez hardcoded user-facing stringova, admin URL ostaje
- pyproject.toml: pytest-django konfigurisan u [tool.pytest.ini_options]

Pokrenuti sa:
    uv run pytest tests/test_i18n_setup.py -v

TEA RED faza: svi testovi MORAJU pasti ili biti skip-ovani dok Dev ne zavrsi Story 1.4.
Naming convention: srpska latinica + engleski; bez cirilice.
"""

from __future__ import annotations

import importlib
import os
import re
import sys
from pathlib import Path

import pytest

try:
    import tomllib
except ImportError:  # pragma: no cover
    tomllib = None  # type: ignore[assignment]

# =============================================================================
# Konstante (project paths)
# =============================================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
SETTINGS_PKG_DIR = CONFIG_DIR / "settings"
SETTINGS_BASE = SETTINGS_PKG_DIR / "base.py"
URLS_PY = CONFIG_DIR / "urls.py"
PYPROJECT_PATH = PROJECT_ROOT / "pyproject.toml"
JUSTFILE_PATH = PROJECT_ROOT / "justfile"

TEMPLATES_DIR = PROJECT_ROOT / "templates"
BASE_HTML = TEMPLATES_DIR / "base.html"
SWITCHER_HTML = TEMPLATES_DIR / "partials" / "language_switcher.html"

LOCALE_DIR = PROJECT_ROOT / "locale"
LOCALE_SR = LOCALE_DIR / "sr" / "LC_MESSAGES"
LOCALE_HU = LOCALE_DIR / "hu" / "LC_MESSAGES"
LOCALE_EN = LOCALE_DIR / "en" / "LC_MESSAGES"

APPS_DIR = PROJECT_ROOT / "apps"
CORE_VIEWS_PY = APPS_DIR / "core" / "views.py"

TEST_SECRET = "test-secret-key-for-tea-story-1-4-i18n-not-real"


# =============================================================================
# Helper funkcije
# =============================================================================


def _ensure_sys_path():
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))


def _read_base_source() -> str:
    """Procita config/settings/base.py. Fail-uje ako ne postoji."""
    if not SETTINGS_BASE.exists():
        pytest.fail(f"config/settings/base.py ne postoji na {SETTINGS_BASE}")
    return SETTINGS_BASE.read_text(encoding="utf-8")


def _read_urls_source() -> str:
    """Procita config/urls.py. Fail-uje ako ne postoji."""
    if not URLS_PY.exists():
        pytest.fail(f"config/urls.py ne postoji na {URLS_PY}")
    return URLS_PY.read_text(encoding="utf-8")


def _load_base_settings():
    """Importuje config.settings.base sa DJANGO_SECRET_KEY env varom + fresh reload.

    Reload je vazan jer testovi u istoj sesiji mogu pokvariti modul state.
    """
    _ensure_sys_path()
    os.environ.setdefault("DJANGO_SECRET_KEY", TEST_SECRET)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
    for mod_key in list(sys.modules.keys()):
        if mod_key.startswith("config.settings"):
            del sys.modules[mod_key]
    try:
        return importlib.import_module("config.settings.base")
    except Exception as exc:
        pytest.fail(
            f"Ne mogu importovati config.settings.base: {type(exc).__name__}: {exc}"
        )


def _load_pyproject() -> dict:
    if tomllib is None:
        pytest.skip("tomllib nije dostupan (Python < 3.11)")
    if not PYPROJECT_PATH.exists():
        pytest.fail(f"pyproject.toml ne postoji na {PYPROJECT_PATH}")
    with PYPROJECT_PATH.open("rb") as f:
        return tomllib.load(f)


def _setup_django():
    """Bootstrap Django + django.setup() za testove koji koriste Client/RequestFactory."""
    _ensure_sys_path()
    os.environ.setdefault("DJANGO_SECRET_KEY", TEST_SECRET)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
    try:
        import django
    except ImportError:  # pragma: no cover
        pytest.fail("Django nije instaliran.")
    if not getattr(django, "_setup_done", False):
        try:
            django.setup()
        except Exception as exc:
            pytest.skip(
                f"django.setup() pada: {type(exc).__name__}: {exc}. "
                f"Verovatno Story 1.4 jos nije implementirana (apps.core nije registrovan)."
            )
        django._setup_done = True  # type: ignore[attr-defined]


def _get_test_client():
    """Vrati Django test Client ili skip ako pytest-django + Django setup nije moguce.

    NAPOMENA: Client mora koristiti `SERVER_NAME='localhost'` (preko HTTP_HOST extra)
    jer development.py `ALLOWED_HOSTS = ['localhost', '127.0.0.1', '[::1]']` NE sadrzi
    Django default `testserver`. Bez ovog override-a sve HTTP behavior testove vracaju
    400 (DisallowedHost) cak i posle pravilne Dev implementacije.

    Alternativa bi bila override-ovati ALLOWED_HOSTS sa pytest fixture-om, ali to
    bi zahtevalo settings mutation za svaki test; explicit HTTP_HOST u Client-u je
    cleaner i ne dira production-ready settings.
    """
    _setup_django()
    try:
        from django.test import Client
    except ImportError:
        pytest.skip("Django test Client nedostupan (pytest-django nije konfigurisan?).")
    return Client(HTTP_HOST="localhost")


# =============================================================================
# AC2 — config/settings/base.py modifications
# =============================================================================


def test_ac2_language_code_is_sr():
    """AC2: LANGUAGE_CODE = 'sr' (NIJE 'en-us' / 'sr-latn' / 'sr_RS').

    Gotcha #4: vrednost MORA matchovati key iz LANGUAGES tuple-a (sr).
    Story 1.4 odluka: koristimo 'sr' (NE 'sr-latn'); ako sr-latn zatreba kasnije,
    dodaje se u Story 6.5+ paralelno sa LANGUAGES update-om.
    """
    src = _read_base_source()
    # Eksplicitno matchovanje: LANGUAGE_CODE = "sr" (single ili double quote)
    pattern = r'^\s*LANGUAGE_CODE\s*=\s*["\']sr["\']\s*$'
    assert re.search(pattern, src, re.MULTILINE), (
        'config/settings/base.py NE sadrzi `LANGUAGE_CODE = "sr"`. '
        "Story 1.4 AC2 zahteva tacno tu vrednost (NE 'en-us' / 'sr-latn' / 'sr_RS')."
    )


def test_ac2_languages_tuple_correct():
    """AC2: LANGUAGES tuple sa tacno 3 stavke i tacnim endonim labelama.

    Tacan redosled: sr, hu, en. Tacne labele: 'Srpski', 'Magyar', 'English'.
    """
    src = _read_base_source()
    # Tolerantno na whitespace + multi-line formatting
    # Pattern hvata: LANGUAGES = [("sr", "Srpski"), ("hu", "Magyar"), ("en", "English")]
    # ili LANGUAGES = [ ... ] multi-line
    assert "LANGUAGES" in src, "config/settings/base.py ne sadrzi LANGUAGES."
    # Strict: tri specifična para moraju biti prisutna
    pairs = [
        (r'["\']sr["\']\s*,\s*["\']Srpski["\']', "('sr', 'Srpski')"),
        (r'["\']hu["\']\s*,\s*["\']Magyar["\']', "('hu', 'Magyar')"),
        (r'["\']en["\']\s*,\s*["\']English["\']', "('en', 'English')"),
    ]
    missing = []
    for pattern, label in pairs:
        if not re.search(pattern, src):
            missing.append(label)
    assert not missing, (
        f"LANGUAGES tuple ne sadrzi sve pare: nedostaje {missing}. "
        f"Story 1.4 AC2: LANGUAGES = [('sr', 'Srpski'), ('hu', 'Magyar'), ('en', 'English')]."
    )


def test_ac2_locale_paths_defined():
    """AC2: LOCALE_PATHS = [BASE_DIR / "locale"].

    Bez ovog setting-a, makemessages ne zna gde da pise .po fajlove,
    a LocaleMiddleware ne pronalazi prevode.
    """
    src = _read_base_source()
    assert "LOCALE_PATHS" in src, (
        "config/settings/base.py ne sadrzi LOCALE_PATHS. "
        "Story 1.4 AC2 zahteva `LOCALE_PATHS = [BASE_DIR / 'locale']`."
    )
    # Mora referencirati BASE_DIR / "locale"
    pattern = r'BASE_DIR\s*/\s*["\']locale["\']'
    assert re.search(pattern, src), (
        'LOCALE_PATHS ne koristi `BASE_DIR / "locale"` pattern. '
        "Mora biti `LOCALE_PATHS = [BASE_DIR / 'locale']` (lista, NE string, NE tuple)."
    )


def test_ac2_use_i18n_true():
    """AC2: USE_I18N mora ostati True (vec postoji iz Story 1.2; regression guard)."""
    base = _load_base_settings()
    assert getattr(base, "USE_I18N", None) is True, (
        f"USE_I18N = {getattr(base, 'USE_I18N', None)!r}, ocekivano True. "
        f"Story 1.2 ga je vec postavio — Story 1.4 ga ne sme menjati / brisati."
    )


def test_ac2_locale_middleware_position_correct():
    """AC2 / Gotcha #1: MIDDLEWARE order MORA biti:
    SessionMiddleware (idx N) → LocaleMiddleware (N+1) → CommonMiddleware (N+2).

    Wrong order razbija URL routing (LocaleMiddleware mora biti PRE CommonMiddleware
    da bi URL prefix bio resolovan pre 404).
    """
    base = _load_base_settings()
    mw = list(getattr(base, "MIDDLEWARE", []))
    if not mw:
        pytest.fail("MIDDLEWARE je prazan ili nedostaje.")
    # Pronadji indices
    try:
        idx_session = mw.index("django.contrib.sessions.middleware.SessionMiddleware")
    except ValueError:
        pytest.fail("SessionMiddleware nije u MIDDLEWARE-u (regression iz Story 1.2).")
    try:
        idx_locale = mw.index("django.middleware.locale.LocaleMiddleware")
    except ValueError:
        pytest.fail(
            "LocaleMiddleware ('django.middleware.locale.LocaleMiddleware') "
            "NIJE u MIDDLEWARE-u. Story 1.4 AC2 zahteva ubacivanje."
        )
    try:
        idx_common = mw.index("django.middleware.common.CommonMiddleware")
    except ValueError:
        pytest.fail("CommonMiddleware nije u MIDDLEWARE-u (regression iz Story 1.2).")

    assert idx_session < idx_locale < idx_common, (
        f"MIDDLEWARE order pogresan: SessionMiddleware (idx {idx_session}) → "
        f"LocaleMiddleware (idx {idx_locale}) → CommonMiddleware (idx {idx_common}). "
        f"Story 1.4 AC2 zahteva STRIKTAN redosled (Gotcha #1): "
        f"Session < Locale < Common."
    )


def test_ac2_locale_switcher_middleware_registered():
    """AC2: apps.core.middleware.LocaleSwitcherMiddleware mora biti u MIDDLEWARE listi.

    Po konvenciji (Gotcha #1) ide POSLEDNJI — posle svih Django built-in middleware-a.
    """
    base = _load_base_settings()
    mw = list(getattr(base, "MIDDLEWARE", []))
    target = "apps.core.middleware.LocaleSwitcherMiddleware"
    assert target in mw, (
        f"MIDDLEWARE ne sadrzi `{target}`. Story 1.4 AC2 zahteva registraciju "
        f"custom middleware-a. Trenutni MIDDLEWARE: {mw}."
    )
    # Po konvenciji posljednji
    assert mw[-1] == target, (
        f"LocaleSwitcherMiddleware NIJE poslednji u MIDDLEWARE-u "
        f"(pozicija: {mw.index(target)}, ukupno: {len(mw)}). "
        f"Gotcha #1: custom middleware ide POSLEDNJI da bi Django built-in "
        f"(URL routing + session) zavrsili pre custom logike."
    )


def test_ac2_templates_dirs_includes_project_templates():
    """AC2 / Gotcha #11: TEMPLATES[0]['DIRS'] MORA sadrzati BASE_DIR / "templates"."""
    base = _load_base_settings()
    templates = getattr(base, "TEMPLATES", None)
    assert templates and isinstance(templates, list), (
        "TEMPLATES setting nedostaje ili nije lista."
    )
    dirs = templates[0].get("DIRS", [])
    assert dirs, (
        "TEMPLATES[0]['DIRS'] je prazan. Story 1.4 AC2 zahteva "
        "`[BASE_DIR / 'templates']` da bi Django pronasao project-level templates/."
    )
    # Konvertuj svaki u Path radi tolerantnosti (BASE_DIR / 'templates' = Path)
    str_dirs = [str(d) for d in dirs]
    expected = str((base.BASE_DIR / "templates").resolve())
    found = any(str(Path(d).resolve()) == expected for d in str_dirs)
    assert found, (
        f"TEMPLATES[0]['DIRS'] ne sadrzi `BASE_DIR / 'templates'`. "
        f"DIRS = {str_dirs!r}; ocekivan path: {expected!r}."
    )


def test_ac2_i18n_context_processor_registered():
    """AC2 / Gotcha #13: context_processors mora sadrzati 'django.template.context_processors.i18n'.

    Bez njega `{{ LANGUAGE_CODE }}` u template-u je prazan — <html lang=""> je
    broken HTML + a11y problem. KRITICNO za AC6.
    """
    base = _load_base_settings()
    templates = getattr(base, "TEMPLATES", None)
    assert templates, "TEMPLATES nedostaje."
    ctx_processors = templates[0].get("OPTIONS", {}).get("context_processors", [])
    assert "django.template.context_processors.i18n" in ctx_processors, (
        "TEMPLATES[0]['OPTIONS']['context_processors'] ne sadrzi "
        "'django.template.context_processors.i18n'. "
        "Gotcha #13: bez njega `{{ LANGUAGE_CODE }}` u template-u je prazan. "
        f"Trenutni context_processors: {ctx_processors}."
    )


def test_ac2_apps_core_in_installed_apps_source():
    """AC2: base.py source MORA sadrzati 'apps.core' u INSTALLED_APPS.

    Source-level test (regex) — komplementaran runtime test-u u
    apps/core/tests/test_apps.py::test_ac2_apps_core_in_installed_apps_runtime.
    """
    src = _read_base_source()
    assert re.search(r'["\']apps\.core["\']', src), (
        "config/settings/base.py source ne sadrzi `'apps.core'`. "
        "Story 1.4 AC2 zahteva dodavanje u INSTALLED_APPS."
    )


def test_ac2_apps_core_is_last_in_installed_apps():
    """AC2 / Interface contract § 2.1: 'apps.core' MORA biti registrovan POSLE Django core/contrib.

    Konvencija: domain app-ovi idu posle Django core/contrib app-ova (Gotcha #6).

    NAPOMENA: Story 2.1 NAMERNO dodaje 'apps.brands' POSLE 'apps.core' — invariant
    "apps.core last" iz Story 1.4 superseded (isti pattern kao Story 1.6 amendment).
    Sada se proverava da je apps.core registrovan POSLE Django/3rd-party app-ova,
    NE više da je poslednji element.
    """
    base = _load_base_settings()
    apps = list(getattr(base, "INSTALLED_APPS", []))
    assert apps, "INSTALLED_APPS je prazan ili nedostaje."
    assert "apps.core" in apps, (
        f"'apps.core' nije u INSTALLED_APPS. Trenutni: {apps}. "
        f"AC2: mora biti dodat (posle Django core/contrib + 3rd-party)."
    )
    # apps.core mora biti posle svih Django core/contrib app-ova
    apps_core_idx = apps.index("apps.core")
    django_contrib_apps = [a for a in apps if a.startswith("django.contrib")]
    if django_contrib_apps:
        max_django_idx = max(apps.index(a) for a in django_contrib_apps)
        assert apps_core_idx > max_django_idx, (
            f"'apps.core' MORA biti POSLE svih django.contrib app-ova. "
            f"apps.core idx={apps_core_idx}, last django.contrib idx={max_django_idx}, lista: {apps}."
        )


def test_ac2_use_l10n_true():
    """AC2: USE_L10N = True (deklarativno, no-op u Django 5.x).

    Interface contract § 2.1: NOVO setting. Iako je Django 5.x ignorise, project-context.md
    propisuje da se postavi radi dokumentacije i kompatibilnosti sa Django 4.x reference-ima.
    """
    base = _load_base_settings()
    use_l10n = getattr(base, "USE_L10N", None)
    assert use_l10n is True, (
        f"USE_L10N = {use_l10n!r}, ocekivano True. "
        f"Story 1.4 AC2 / Interface contract § 2.1 zahteva eksplicitno postavljanje "
        f"(no-op u Django 5.x ali deklarativno per project-context.md § i18n)."
    )


# =============================================================================
# AC5 — config/urls.py: i18n_patterns + set_language
# =============================================================================


def test_ac5_urls_uses_i18n_patterns():
    """AC5: config/urls.py MORA pozivati `i18n_patterns(...)`."""
    src = _read_urls_source()
    assert "i18n_patterns(" in src, (
        "config/urls.py ne poziva `i18n_patterns(...)`. "
        "Story 1.4 AC5 zahteva URL routing sa locale prefiksom."
    )
    # Mora importovati i18n_patterns
    assert "from django.conf.urls.i18n import i18n_patterns" in src or re.search(
        r"from\s+django\.conf\.urls\.i18n\s+import\s+i18n_patterns", src
    ), "config/urls.py ne importuje i18n_patterns iz django.conf.urls.i18n."
    # prefix_default_language=True eksplicitno
    assert re.search(r"prefix_default_language\s*=\s*True", src), (
        "config/urls.py ne postavlja `prefix_default_language=True` eksplicitno. "
        "AC5 zahteva eksplicitnu vrednost (Django default, ali story trazi citljivost)."
    )


def test_ac5_set_language_route_registered():
    """AC5 / Gotcha #14: set_language URL MORA biti registrovan VAN i18n_patterns.

    Path: 'i18n/setlang/', name: 'set_language'. Ako je unutar i18n_patterns,
    URL postaje '/sr/i18n/setlang/' sto pravi infinite redirect (Gotcha #14).
    """
    src = _read_urls_source()
    # Mora importovati set_language view
    assert re.search(r"from\s+django\.views\.i18n\s+import\s+set_language", src), (
        "config/urls.py ne importuje set_language iz django.views.i18n."
    )
    # Path mora biti registrovan
    assert re.search(r'[\'"]i18n/setlang/[\'"]', src), (
        "config/urls.py ne registruje 'i18n/setlang/' path. "
        "AC5: `path('i18n/setlang/', set_language, name='set_language')`."
    )
    # name='set_language'
    assert re.search(r'name\s*=\s*[\'"]set_language[\'"]', src), (
        "config/urls.py path nema `name='set_language'`. "
        "AC5 / AC7 (switcher form) referencira `{% url 'set_language' %}`."
    )


def test_ac5_root_redirects_to_default_lang():
    """AC5 / AC9.7: GET / mora 302 redirektovati na /sr/.

    `prefix_default_language=True` znaci da default lang ima eksplicitan prefix.
    Bez njega root / bi serv-ovao sadrzaj direktno (i SEO bi imao duplikate /).
    """
    client = _get_test_client()
    response = client.get("/")
    assert response.status_code in (301, 302), (
        f"GET / status {response.status_code}, ocekivano 302 redirect. "
        f"AC5: root mora redirektovati na /sr/."
    )
    location = response.headers.get("Location", "")
    assert location.startswith("/sr/") or location == "/sr/", (
        f"GET / redirektuje na {location!r}, ocekivano '/sr/'."
    )


@pytest.mark.django_db  # Story 3.1: root `/` sada renderuje DB-backed HomeView (pages:home)
def test_ac5_sr_hu_en_routes_200():
    """AC5 / AC9.8-10: GET /sr/, /hu/, /en/ moraju vratiti 200."""
    client = _get_test_client()
    for code in ("sr", "hu", "en"):
        response = client.get(f"/{code}/")
        assert response.status_code == 200, (
            f"GET /{code}/ status {response.status_code}, ocekivano 200. "
            f"AC5: svi 3 jezika moraju biti dostupni."
        )


def test_ac5_de_route_404():
    """AC5 / AC9.11: GET /de/ mora vratiti 404 (de NIJE u LANGUAGES)."""
    client = _get_test_client()
    response = client.get("/de/")
    assert response.status_code == 404, (
        f"GET /de/ status {response.status_code}, ocekivano 404. "
        f"AC5 / AC9.11: /de/ nije language prefix (de nije u LANGUAGES) "
        f"i nema plain URL pattern koji ga matchuje."
    )


def test_ac5_set_language_outside_i18n_patterns():
    """AC5 / Gotcha #14: `i18n/setlang/` MORA biti VAN `i18n_patterns()`.

    Ako se path stavi unutar i18n_patterns, URL postaje `/sr/i18n/setlang/`, a Django
    set_language view rewrite-uje redirect na isti URL — infinite redirect loop.

    Heuristika: u source-u traz `set_language` referencu i verifikuj da je
    `path("i18n/setlang/", set_language, ...)` PRE prvog `i18n_patterns(` poziva.
    """
    src = _read_urls_source()
    # Pronadji poziciju path('i18n/setlang/', ...)
    setlang_match = re.search(r'path\s*\(\s*[\'"]i18n/setlang/[\'"]', src)
    assert setlang_match, (
        "config/urls.py ne sadrzi `path('i18n/setlang/', ...)`. "
        "AC5 zahteva registraciju set_language view-a."
    )
    # Pronadji prvi poziv i18n_patterns(
    patterns_match = re.search(r"i18n_patterns\s*\(", src)
    assert patterns_match, "config/urls.py ne poziva `i18n_patterns(...)`."
    assert setlang_match.start() < patterns_match.start(), (
        f"Path `i18n/setlang/` (pozicija {setlang_match.start()}) JE definisan POSLE "
        f"`i18n_patterns(` (pozicija {patterns_match.start()}) u config/urls.py. "
        f"Gotcha #14: set_language MORA biti registrovan PRE i18n_patterns() — "
        f"unutar `urlpatterns = [...]` liste, NE unutar `i18n_patterns(...)` poziva. "
        f"Stavljanje unutar i18n_patterns pravi infinite redirect (/sr/i18n/setlang/)."
    )


def test_ac5_admin_inside_i18n_patterns():
    """AC5 / Interface contract § 3.5: `path('admin/', ...)` MORA biti UNUTAR
    `i18n_patterns()` (admin se lokalizuje preko URL prefiksa).

    Heuristika: u source-u trazi `admin.site.urls` referencu i verifikuj da je
    POSLE `i18n_patterns(` poziva ali PRE zatvarajuce `)` (tj. unutar argument liste).
    """
    src = _read_urls_source()
    admin_match = re.search(r"admin\.site\.urls", src)
    assert admin_match, (
        "config/urls.py ne sadrzi `admin.site.urls`. "
        "AC5 zahteva ukljucivanje admin URL-a unutar i18n_patterns()."
    )
    patterns_match = re.search(r"i18n_patterns\s*\(", src)
    assert patterns_match, "config/urls.py ne poziva i18n_patterns()."
    assert admin_match.start() > patterns_match.start(), (
        "`admin.site.urls` je referenciran PRE `i18n_patterns(` u config/urls.py. "
        "AC5 / Interface contract § 3.5: admin MORA biti unutar i18n_patterns() "
        "(admin UI se prevodi prema URL locale prefiksu)."
    )


def test_ac5_apps_pages_urls_included():
    """AC5 / Story 3.1 (C1 migracija): root path (home view) se uključuje kroz
    `include('apps.pages.urls')` UNUTAR `i18n_patterns()`.

    Story 3.1 je relocirao home view iz `apps.core` u `apps.pages` (HomeView) i
    uklonio `apps.core.urls` include (core više nema URL-ova) — root `/` sada
    rezolvuje `pages:home`.
    """
    src = _read_urls_source()
    assert re.search(r'include\s*\(\s*[\'"]apps\.pages\.urls[\'"]', src), (
        "config/urls.py ne sadrzi `include('apps.pages.urls')`. "
        "AC5 / Story 3.1: root URL (home) se uključuje kroz apps.pages.urls (pages:home)."
    )


def test_ac5_set_language_post_redirects():
    """AC5 / Story Testing § AC7 behavior: POST /i18n/setlang/ sa language=hu&next=/sr/
    MORA 302 redirektovati na /hu/ + setovati cookie `django_language=hu`.

    Iter-1 lesson: Switcher dropdown bukvalno mora da radi end-to-end; samo source-level
    `set_language` registracija nije dovoljna garancija da Django translate_url() i CSRF
    rade kako ocekujemo.
    """
    client = _get_test_client()
    # POST sa language=hu + next=/sr/ — Django ce uz translate_url() prebaciti na /hu/
    response = client.post(
        "/i18n/setlang/",
        data={"language": "hu", "next": "/sr/"},
    )
    assert response.status_code in (301, 302), (
        f"POST /i18n/setlang/ status {response.status_code}, ocekivano 302 redirect. "
        f"AC5: set_language view MORA odgovoriti redirekcijom na ekvivalentnu putanju u novom jeziku."
    )
    location = response.headers.get("Location", "")
    assert location.startswith("/hu/") or location == "/hu/", (
        f"POST /i18n/setlang/ redirektuje na {location!r}, ocekivano '/hu/'. "
        f"Django set_language interno koristi translate_url() koji rewrite-uje locale prefix."
    )
    # Cookie `django_language=hu` mora biti set
    try:
        from django.conf import settings
    except ImportError:
        pytest.skip("Django nedostupan.")
    cookie_name = settings.LANGUAGE_COOKIE_NAME
    assert cookie_name in response.cookies, (
        f"POST /i18n/setlang/ ne postavlja `{cookie_name}` cookie. "
        f"Bez cookie-a, sledeci GET request bi vratio na default lokal."
    )
    assert response.cookies[cookie_name].value == "hu", (
        f"Cookie `{cookie_name}` value = {response.cookies[cookie_name].value!r}, "
        f"ocekivano 'hu'."
    )


# =============================================================================
# AC6 — templates/base.html
# =============================================================================


def test_ac6_base_html_exists():
    """AC6: templates/base.html MORA postojati."""
    assert BASE_HTML.exists(), (
        f"templates/base.html ne postoji na {BASE_HTML}. "
        f"Story 1.4 AC6 zahteva minimalan layout."
    )


def test_ac6_base_html_uses_language_code():
    """AC6 / Gotcha #13: <html lang="{{ LANGUAGE_CODE }}"> mora postojati."""
    if not BASE_HTML.exists():
        pytest.fail("templates/base.html ne postoji.")
    src = BASE_HTML.read_text(encoding="utf-8")
    pattern = r"<html\s+lang\s*=\s*['\"]\{\{\s*LANGUAGE_CODE\s*\}\}['\"]"
    assert re.search(pattern, src), (
        'templates/base.html ne sadrzi `<html lang="{{ LANGUAGE_CODE }}">`. '
        "Gotcha #13 / AC6: vrednost MORA biti template variable, NE hardcoded 'sr'."
    )


def test_ac6_base_html_loads_i18n():
    """AC6 / Gotcha #10: {% load i18n %} mora biti prisutan."""
    if not BASE_HTML.exists():
        pytest.fail("templates/base.html ne postoji.")
    src = BASE_HTML.read_text(encoding="utf-8")
    assert "{% load i18n %}" in src, (
        "templates/base.html ne sadrzi `{% load i18n %}`. "
        "Bez njega `{% translate %}` / `{% blocktranslate %}` baca TemplateSyntaxError."
    )


def test_ac6_base_html_default_content():
    """AC6: default sadrzaj 'Ćorić Agrar' header + {% translate "Dobrodošli." %}."""
    if not BASE_HTML.exists():
        pytest.fail("templates/base.html ne postoji.")
    src = BASE_HTML.read_text(encoding="utf-8")
    assert "Ćorić Agrar" in src, (
        "templates/base.html ne sadrzi 'Ćorić Agrar' brand string. "
        "AC6 default content: <h1>Ćorić Agrar</h1>."
    )
    # Pattern za {% translate "Dobrodošli." %} tolerantan na single/double quotes
    pattern = r'\{%\s*translate\s+["\']Dobrodošli\.["\']\s*%\}'
    assert re.search(pattern, src), (
        'templates/base.html ne sadrzi `{% translate "Dobrodošli." %}` u default block-u. '
        "AC6 default content propisuje translatable welcome string."
    )


@pytest.mark.django_db  # Story 3.1: root `/` sada renderuje DB-backed HomeView (pages:home)
def test_ac6_render_html_lang_matches_url_locale():
    """AC6: rendered HTML <html lang> matchuje URL locale prefix.

    GET /sr/ → <html lang="sr">; GET /hu/ → <html lang="hu">; GET /en/ → <html lang="en">.

    NAPOMENA: Pre-implementation, base.html ne postoji — `pytest.skip` bi sakrio
    nedostatak templata. RED phase: ako template/route nije implementiran, test PADA
    (ne skip-uje). Drugi AC6 testovi (test_ac6_base_html_exists) hvataju filesystem
    odsustvo eksplicitno; ovaj test verifikuje runtime render integraciju.
    """
    # Pre-flight: ako base.html ne postoji, ovaj test ne moze raditi i druge AC6
    # testove vec hvataju odsustvo. Skipuj samo u tom konkretnom slucaju.
    if not BASE_HTML.exists():
        pytest.skip(
            "templates/base.html ne postoji — drugi AC6 testovi hvataju odsustvo. "
            "Ovaj test verifikuje runtime render (post-implementation)."
        )
    client = _get_test_client()
    for code in ("sr", "hu", "en"):
        response = client.get(f"/{code}/")
        assert response.status_code == 200, (
            f"GET /{code}/ vraca {response.status_code}, ocekivano 200. "
            f"AC5/AC6: route mora renderovati base.html sa locale prefiksom."
        )
        content = response.content.decode("utf-8", errors="replace")
        assert f'<html lang="{code}"' in content or f"<html lang='{code}'" in content, (
            f'GET /{code}/ rendered HTML ne sadrzi `<html lang="{code}">`. '
            f"Verifikuj context processor `django.template.context_processors.i18n` "
            f"u TEMPLATES OPTIONS (Gotcha #13). Bez njega `{{{{ LANGUAGE_CODE }}}}` "
            f'je prazan string i <html lang=""> je broken HTML.'
        )


# =============================================================================
# AC7 — templates/partials/language_switcher.html
# =============================================================================


def test_ac7_switcher_exists():
    """AC7: templates/partials/language_switcher.html MORA postojati."""
    assert SWITCHER_HTML.exists(), (
        f"templates/partials/language_switcher.html ne postoji na {SWITCHER_HTML}. "
        f"Story 1.4 AC7 zahteva POST forma sa 3 jezicke opcije."
    )


def test_ac7_switcher_posts_to_set_language():
    """AC7: forma MORA biti POST na {% url 'set_language' %}."""
    if not SWITCHER_HTML.exists():
        pytest.fail("templates/partials/language_switcher.html ne postoji.")
    src = SWITCHER_HTML.read_text(encoding="utf-8")
    # action="{% url 'set_language' %}" + method="post"
    assert re.search(
        r'action\s*=\s*["\']\{%\s*url\s+["\']set_language["\']\s*%\}["\']', src
    ), (
        "language_switcher.html `action` nije `{% url 'set_language' %}`. "
        "AC7: forma mora referencirati Django set_language view (NE hardcoded URL)."
    )
    assert re.search(r'method\s*=\s*["\']post["\']', src, re.IGNORECASE), (
        'language_switcher.html forma nema `method="post"`. '
        "Gotcha #8: set_language je @require_POST decorated; GET vraca 405."
    )


def test_ac7_switcher_next_uses_request_path():
    """AC7 / iter-1 lesson: `next` polje MORA koristiti `{{ request.path }}` (kanonsko).

    NE smije biti `{{ request.path|slice:'3:' }}` (iter-1 bug) ili
    `{{ redirect_to|default:request.path }}` (over-engineered) — Django
    set_language interno koristi translate_url() koji handluje locale prefix.
    """
    if not SWITCHER_HTML.exists():
        pytest.fail("templates/partials/language_switcher.html ne postoji.")
    src = SWITCHER_HTML.read_text(encoding="utf-8")
    pattern = r'name\s*=\s*["\']next["\'][^>]*value\s*=\s*["\']\{\{\s*request\.path\s*\}\}["\']'
    pattern_reverse = r'value\s*=\s*["\']\{\{\s*request\.path\s*\}\}["\'][^>]*name\s*=\s*["\']next["\']'
    has_canonical = re.search(pattern, src) or re.search(pattern_reverse, src)
    assert has_canonical, (
        "language_switcher.html `next` polje nije kanonsko `{{ request.path }}`. "
        "Iter-1 lesson: koristio `|slice:'3:'` filter sto je razbijalo deep-link "
        "po stranama. Kanonska forma (iz Story 1.4 spec § Dev Notes): "
        '<input type="hidden" name="next" value="{{ request.path }}">. '
        "Django set_language interno koristi translate_url() koji handluje prefix."
    )
    # Negative: ne sme imati |slice ili |default filter na request.path
    bad_patterns = [
        (r"request\.path\s*\|\s*slice", "request.path|slice (iter-1 bug)"),
        (r"redirect_to\s*\|\s*default", "redirect_to|default (over-engineered)"),
        (r"request\.get_full_path", "request.get_full_path (uvodi query string noise)"),
    ]
    for pat, label in bad_patterns:
        assert not re.search(pat, src), (
            f"language_switcher.html sadrzi anti-pattern: {label}. "
            f"Koristi `{{{{ request.path }}}}` bez filtera."
        )


def test_ac7_switcher_has_csrf():
    """AC7 / Gotcha #15: {% csrf_token %} mora biti unutar form-e.

    Django set_language ima CSRF check; bez tokena POST → 403 Forbidden.
    """
    if not SWITCHER_HTML.exists():
        pytest.fail("templates/partials/language_switcher.html ne postoji.")
    src = SWITCHER_HTML.read_text(encoding="utf-8")
    assert "{% csrf_token %}" in src, (
        "language_switcher.html ne sadrzi `{% csrf_token %}`. "
        "Gotcha #15: bez tokena Django set_language POST → 403 Forbidden."
    )


def test_ac7_switcher_has_three_options():
    """AC7: <select> ima tacno 3 <option> tagova sa sr/hu/en value-ima."""
    if not SWITCHER_HTML.exists():
        pytest.fail("templates/partials/language_switcher.html ne postoji.")
    src = SWITCHER_HTML.read_text(encoding="utf-8")
    options = re.findall(r"<option\s+[^>]*value\s*=\s*['\"]([a-z]{2})['\"]", src)
    assert set(options) == {"sr", "hu", "en"}, (
        f"language_switcher.html <option> vrednosti = {options}. "
        f"AC7 zahteva tacno 3 opcije: sr, hu, en. "
        f"Story 1.4 spec lista 'Srpski' / 'Magyar' / 'English' endonim labele."
    )


def test_ac7_switcher_has_noscript_fallback():
    """AC7: <noscript> fallback sa <button type="submit">."""
    if not SWITCHER_HTML.exists():
        pytest.fail("templates/partials/language_switcher.html ne postoji.")
    src = SWITCHER_HTML.read_text(encoding="utf-8")
    assert "<noscript>" in src and "</noscript>" in src, (
        "language_switcher.html nema <noscript> fallback blok. "
        "AC7: JS submit-on-change je progressive enhancement; "
        "<noscript> dugme je a11y fallback."
    )


# =============================================================================
# AC8 — locale/ direktorijumi + justfile messages recept
# =============================================================================


def test_ac8_locale_subdirs_exist():
    """AC8: locale/{sr,hu,en}/LC_MESSAGES/ direktorijumi MORAJU postojati."""
    missing = []
    for subdir in (LOCALE_SR, LOCALE_HU, LOCALE_EN):
        if not subdir.exists() or not subdir.is_dir():
            missing.append(str(subdir.relative_to(PROJECT_ROOT)))
    assert not missing, (
        f"Locale direktorijumi nedostaju: {missing}. "
        f"Story 1.4 AC8 zahteva: locale/sr/LC_MESSAGES/, locale/hu/LC_MESSAGES/, "
        f"locale/en/LC_MESSAGES/."
    )


def test_ac8_locale_dirs_have_tracked_content():
    """AC8 / Gotcha #16: locale/{sr,hu,en}/LC_MESSAGES/ MORAJU imati barem jedan fajl
    (`.gitkeep` ili `django.po`) jer Git ne tracku-je prazne foldere.

    Bez bar jednog fajla, direktorijumi se ne komituju i CI cisti repo nece imati
    locale strukturu (LocaleMiddleware bi bacao runtime warning).
    """
    missing = []
    for subdir in (LOCALE_SR, LOCALE_HU, LOCALE_EN):
        if not subdir.exists():
            continue  # Drugi test ce uhvatiti
        # Mora imati barem jedan fajl (gitkeep ili .po)
        files = [f for f in subdir.iterdir() if f.is_file()]
        if not files:
            missing.append(str(subdir.relative_to(PROJECT_ROOT)))
    assert not missing, (
        f"Locale direktorijumi nemaju nijedan fajl: {missing}. "
        f"AC8 / Gotcha #16: Git ne tracku-je prazne foldere. Dodaj `.gitkeep` "
        f"(prazan fajl) ili pokreni `just dev-manage makemessages -a` da se generisu .po."
    )


def test_ac8_just_messages_recipe_present():
    """AC8: justfile MORA imati `messages` recept (vec postoji iz Story 1.1; regression guard).

    Story 1.4 ne menja recept — samo verifikuje da nije slucajno obrisan.
    """
    if not JUSTFILE_PATH.exists():
        pytest.fail(f"justfile ne postoji na {JUSTFILE_PATH}.")
    content = JUSTFILE_PATH.read_text(encoding="utf-8")
    # Recept = linija "messages:" (no indent)
    pattern = r"^messages\s*(?:[a-zA-Z_].*)?:"
    assert re.search(pattern, content, re.MULTILINE), (
        "justfile ne sadrzi `messages:` recept (regression iz Story 1.1)."
    )
    # Mora imati makemessages + compilemessages komande
    assert "makemessages" in content, (
        "justfile `messages` recept ne sadrzi `makemessages` komandu."
    )
    assert "compilemessages" in content, (
        "justfile `messages` recept ne sadrzi `compilemessages` komandu."
    )


# =============================================================================
# Negative / regression / cross-cutting checks
# =============================================================================


def test_no_hardcoded_serbian_strings_in_views():
    """Anti-pattern (project-context.md § Hardcoded user-facing string):
    apps/core/views.py NE SME imati hardcoded srpske stringove van `_(...)` / `gettext(...)`.

    Story 1.4 views.py je minimalan (home view koji renderuje base.html — bez stringova).
    Ovaj test sprecava da Dev doda hardcoded 'Dobrodošli' / 'Pretraga' / itd. u kod.
    """
    if not CORE_VIEWS_PY.exists():
        pytest.fail(
            "apps/core/views.py ne postoji. Story 1.4 AC1 zahteva minimalan home view."
        )
    src = CORE_VIEWS_PY.read_text(encoding="utf-8")
    # Heuristika: trazimo stringove sa srpskim diakritickim slovima (š/č/ć/ž/đ)
    # u izvrsnom kodu (van komentara/docstring-a)
    bad_strings = []
    in_docstring = False
    docstring_delim = None
    for raw in src.splitlines():
        line = raw.strip()
        if line.startswith("#"):
            continue
        for delim in ('"""', "'''"):
            if delim in line:
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
        # Trazi srpska diakritika unutar quoted stringa (single/double)
        # Pattern: 'sadržaj' ili "sadržaj" sa š/č/ć/ž/đ
        if re.search(r"['\"][^'\"]*[šŠčČćĆžŽđĐ][^'\"]*['\"]", line):
            # Ali da nije unutar _( ... ) ili gettext( ... )
            if "_(" not in line and "gettext" not in line:
                bad_strings.append(raw)
    assert not bad_strings, (
        f"apps/core/views.py sadrzi hardcoded srpske stringove van _()/gettext(): "
        f"{bad_strings}. "
        f"Anti-pattern: sve user-facing stringove pakuj kroz gettext/_()."
    )


def test_no_cirillic_anywhere_in_new_files():
    """Anti-pattern (project-context.md § Ćirilica): nijedan novi Story 1.4 fajl
    NE SME sadrzati ćirilicna slova.

    Skenira: apps/core/*.py, templates/base.html, templates/partials/language_switcher.html.
    Range ćirilice: U+0400-U+04FF (basic Cyrillic + supplement).
    """
    files_to_check = [
        APPS_DIR / "core" / "apps.py",
        APPS_DIR / "core" / "middleware.py",
        APPS_DIR / "core" / "translation.py",
        APPS_DIR / "core" / "views.py",
        APPS_DIR / "core" / "urls.py",
        BASE_HTML,
        SWITCHER_HTML,
    ]
    cirillic_pattern = re.compile(r"[Ѐ-ӿ]")
    bad_files = []
    for path in files_to_check:
        if not path.exists():
            continue  # Drugi test ce uhvatiti nedostatak
        content = path.read_text(encoding="utf-8")
        match = cirillic_pattern.search(content)
        if match:
            line_no = content[: match.start()].count("\n") + 1
            bad_files.append(
                f"{path.relative_to(PROJECT_ROOT)}:{line_no} (znak: {match.group()!r})"
            )
    assert not bad_files, (
        f"Ćirilicna slova pronadjena u novim Story 1.4 fajlovima: {bad_files}. "
        f"Project rule: latinica only (NIKAD ćirilica)."
    )


def test_admin_url_still_admin_not_admin_coric():
    """Gotcha #25: admin URL ostaje `admin/` u Story 1.4 — promena na `admin-coric/`
    je deferred ka Story 8.1 (Custom admin login + rate limiting).

    Sprecava da Dev preempt-uje Story 8.1 i razbije test churn.
    """
    src = _read_urls_source()
    # Admin path mora biti tacno 'admin/'
    assert re.search(r"['\"]admin/['\"]", src), (
        "config/urls.py ne registruje 'admin/' path. "
        "Gotcha #25: Story 1.4 zadrzava 'admin/' — promena na 'admin-coric/' je u Story 8.1."
    )
    # Admin path NE SME biti `admin-coric/`
    assert not re.search(r"['\"]admin-coric/['\"]", src), (
        "config/urls.py JE prelaze na 'admin-coric/' u Story 1.4. "
        "Gotcha #25: ta migracija je rezervisana za Story 8.1 (Custom admin login)."
    )


# =============================================================================
# AC9 — Smoke validacija (subprocess `manage.py check` + apps.core registration)
# =============================================================================


def test_ac9_manage_py_check_passes_with_apps_core_registered():
    """AC9.1 + AC9.4 / Story Testing § AC9: `uv run python manage.py check` exit 0
    I `apps.core` je runtime-registrovan.

    Subprocess test (timeout 60s). Kombinuje dve provere:
    1. `manage.py check` exit 0 (verifikuje da nije pukao baseline Django check)
    2. `manage.py shell -c "from django.apps import apps; apps.get_app_config('core')"` exit 0
       (verifikuje da je apps.core STVARNO u INSTALLED_APPS — `check` sam ovo NE detektuje
       ako Dev kreira skeleton ali zaboravi registraciju)

    NAPOMENA: PRE Story 1.4, `manage.py check` vec prolazi (base.py je default), pa bi
    samostalan check test bio vacuous pass. Drugi pod-test (apps.core registered) je taj
    koji ce pasti dok Dev ne dovrsi AC2 INSTALLED_APPS update.
    """
    import os
    import shutil
    import subprocess

    uv_bin = shutil.which("uv")
    if uv_bin is None:
        pytest.skip("uv binary nije u PATH-u.")
    manage_py = PROJECT_ROOT / "manage.py"
    if not manage_py.exists():
        pytest.fail("manage.py nedostaje — Story 1.1 nije zavrsena.")
    env = os.environ.copy()
    env["DJANGO_SECRET_KEY"] = TEST_SECRET

    # --- 1. manage.py check ---
    check_result = subprocess.run(
        [uv_bin, "run", "python", "manage.py", "check"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        shell=False,
        timeout=60,
        env=env,
    )
    assert check_result.returncode == 0, (
        f"`uv run python manage.py check` exit {check_result.returncode}.\n"
        f"stdout: {check_result.stdout}\n"
        f"stderr: {check_result.stderr}\n"
        f"AC9.1: System check MORA proci posle Story 1.4 implementacije."
    )

    # --- 2. apps.core runtime registration (AC9.4 — kritican test) ---
    registration_result = subprocess.run(
        [
            uv_bin,
            "run",
            "python",
            "manage.py",
            "shell",
            "-c",
            "from django.apps import apps; apps.get_app_config('core'); print('OK')",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        shell=False,
        timeout=60,
        env=env,
    )
    assert registration_result.returncode == 0 and "OK" in registration_result.stdout, (
        f"`apps.get_app_config('core')` ne radi runtime.\n"
        f"exit: {registration_result.returncode}\n"
        f"stdout: {registration_result.stdout}\n"
        f"stderr: {registration_result.stderr}\n"
        f"AC9.4: apps.core MORA biti registrovan u INSTALLED_APPS — `manage.py check` "
        f"sam ovo NE detektuje (orphan app fajlovi prolaze false-positive)."
    )


def test_pytest_django_configured():
    """pytest-django ConfigError: pyproject.toml MORA imati DJANGO_SETTINGS_MODULE
    u [tool.pytest.ini_options].

    Story 1.1 je dodao pytest-django u dev grupu, ali NIJE konfigurisao
    [tool.pytest.ini_options]. Story 1.4 testovi koji koriste Client/RequestFactory
    se ne mogu izvrsiti bez ovog setting-a.

    Dodatno (kriticno za apps/core/tests/ collection): importmode = "importlib"
    je obavezan jer top-level `tests/` paket i `apps/core/tests/` paket dele
    isto ime ("tests") — bez `importmode = importlib`, pytest baca
    `ModuleNotFoundError: No module named 'tests.test_X'` pri collection-u
    (default importmode "prepend" pretpostavlja unique top-level paket imena).
    """
    pyproject = _load_pyproject()
    pytest_config = pyproject.get("tool", {}).get("pytest", {}).get("ini_options", {})
    assert pytest_config, (
        "[tool.pytest.ini_options] tabela nedostaje u pyproject.toml. "
        "Story 1.4 zahteva pytest-django konfiguraciju: "
        '`DJANGO_SETTINGS_MODULE = "config.settings.development"` + '
        '`pythonpath = ["."]` + `importmode = "importlib"`.'
    )
    settings_module = pytest_config.get("DJANGO_SETTINGS_MODULE")
    assert settings_module, (
        "[tool.pytest.ini_options] nema `DJANGO_SETTINGS_MODULE` kljuc. "
        "Mora biti 'config.settings.development' za dev env tests."
    )
    assert settings_module.startswith("config.settings."), (
        f"DJANGO_SETTINGS_MODULE = {settings_module!r}, ocekivano "
        f"'config.settings.<env>' (npr. 'config.settings.development')."
    )
    # Import mode MORA biti "importlib" zbog dual `tests/` paketa.
    # Prihvatamo dve ekvivalentne forme:
    #  - eksplicitan `importmode` kljuc (NIJE validan pytest ini option — generise warning,
    #    drzimo forward-compat ako pytest doda kljuc u buducnosti)
    #  - ili `addopts` koji sadrzi `--import-mode=importlib` (funkcionalni ekvivalent;
    #    pytest ovo aktivno koristi)
    importmode = pytest_config.get("importmode") or pytest_config.get("import_mode")
    addopts = str(pytest_config.get("addopts", ""))
    import_mode_configured = (
        importmode == "importlib" or "--import-mode=importlib" in addopts
    )
    assert import_mode_configured, (
        f"[tool.pytest.ini_options] ne konfigurise import mode 'importlib'. "
        f"importmode = {importmode!r}, addopts = {addopts!r}. "
        f'Mora biti postavljen kroz `addopts = "--import-mode=importlib"` '
        f'(ili explicit `importmode = "importlib"`). Bez njega `apps/core/tests/` '
        f"collection puca jer top-level `tests/` paket i `apps/core/tests/` paket "
        f"dele isto ime."
    )
