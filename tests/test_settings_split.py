"""Tests za Story 1.2 - Multi-environment Settings Split sa django-environ.

Verifikuje refactor `config/settings.py` (single file) -> `config/settings/`
package sa `base.py`, `development.py`, `staging.py`, `production.py` modulima
+ `.env.example` template + django-environ integracija.

Organizacija (po AC):
- AC1: Package structure (config/settings/ paket, brisanje starog single-file-a,
       manage.py check passes za development)
- AC2: base.py sadrzaj + django-environ integracija (env, env.bool, env.list,
       env.db, env.email_url, BASE_DIR sa 3 parenta)
- AC3: Per-env override moduli (development/staging/production sa expected
       attribute-ima)
- AC4: .env.example template sa svim required env kljucevima
- AC5: manage.py / wsgi.py / asgi.py imaju default DJANGO_SETTINGS_MODULE
       postavljen na `config.settings.development`
- Edge / negative / security: fail-fast bez SECRET_KEY, nema hardkodovanog
                              django-insecure secret-a u base.py

Pokrenuti sa:
    uv run pytest tests/test_settings_split.py -v

TEA RED faza: svi testovi MORAJU pasti dok Dev ne zavrsi Story 1.2.
Naming convention: srpska latinica + engleski; bez cirilice.
"""

from __future__ import annotations

import importlib
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

# =============================================================================
# Konstante (project paths)
# =============================================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
SETTINGS_PKG_DIR = CONFIG_DIR / "settings"
SETTINGS_INIT = SETTINGS_PKG_DIR / "__init__.py"
SETTINGS_BASE = SETTINGS_PKG_DIR / "base.py"
SETTINGS_DEV = SETTINGS_PKG_DIR / "development.py"
SETTINGS_STAGING = SETTINGS_PKG_DIR / "staging.py"
SETTINGS_PROD = SETTINGS_PKG_DIR / "production.py"
OLD_SETTINGS_FILE = CONFIG_DIR / "settings.py"
CONFIG_INIT = CONFIG_DIR / "__init__.py"
MANAGE_PY = PROJECT_ROOT / "manage.py"
WSGI_PY = CONFIG_DIR / "wsgi.py"
ASGI_PY = CONFIG_DIR / "asgi.py"
ENV_EXAMPLE = PROJECT_ROOT / ".env.example"
GITIGNORE = PROJECT_ROOT / ".gitignore"

# Test SECRET_KEY za import (NIJE realan secret — samo za test imports)
TEST_SECRET = "test-secret-key-for-tea-imports-not-a-real-secret"


# =============================================================================
# Helper funkcije
# =============================================================================


def _read_settings_source(module_name: str) -> str:
    """Procita `config/settings/<module_name>.py` source. Fail-uje ako ne postoji.

    Koristi se za regex/substring proveru sadrzaja BEZ importovanja modula
    (vazno za pattern checks gde import moze imati side effects / da padne).
    """
    path = SETTINGS_PKG_DIR / f"{module_name}.py"
    if not path.exists():
        pytest.fail(f"config/settings/{module_name}.py ne postoji na {path}")
    return path.read_text(encoding="utf-8")


def _load_settings_module(module_name: str):
    """Importuje `config.settings.<module_name>` posle setovanja test
    DJANGO_SECRET_KEY env vara (jer base.py fail-fast-uje bez nje).

    Uvek reload-uje modul da pokupi sveze env var promene. Brise i base modul
    iz sys.modules-a da bi `from .base import *` re-executed (fresh state).
    """
    # Setdefault — ne overriduje ako je test vec set-ovao drugu vrednost
    os.environ.setdefault("DJANGO_SECRET_KEY", TEST_SECRET)
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    full_name = f"config.settings.{module_name}"
    # Force fresh import: obrisi target modul i SVE config.settings.* iz sys.modules
    # (bitno jer per-env moduli rade `from .base import *` — base mora biti svez).
    for mod_key in list(sys.modules.keys()):
        if (
            mod_key == full_name
            or mod_key.startswith(f"{full_name}.")
            or mod_key.startswith("config.settings.")
        ):
            del sys.modules[mod_key]
    return importlib.import_module(full_name)


def _run(
    cmd: list[str], env: dict[str, str] | None = None, cwd: Path | None = None
) -> subprocess.CompletedProcess:
    """Subprocess wrapper. env=None znaci nasledjuje os.environ."""
    full_env = os.environ.copy()
    if env:
        full_env.update(env)
    return subprocess.run(
        cmd,
        cwd=cwd or PROJECT_ROOT,
        capture_output=True,
        text=True,
        shell=False,
        timeout=120,
        env=full_env,
    )


# =============================================================================
# AC1 — `config/settings/` package structure
# =============================================================================


def test_ac1_settings_package_directory_exists():
    """AC1: `config/settings/` mora biti direktorijum (ne fajl)."""
    assert SETTINGS_PKG_DIR.exists(), (
        f"config/settings/ direktorijum ne postoji na {SETTINGS_PKG_DIR}. "
        f"Kreiraj paket sa __init__.py."
    )
    assert SETTINGS_PKG_DIR.is_dir(), (
        "config/settings/ postoji ali NIJE direktorijum (verovatno je fajl). "
        "Refactor zahteva paket strukturu."
    )


def test_ac1_settings_init_module_exists():
    """AC1: `config/settings/__init__.py` mora postojati (package marker)."""
    assert SETTINGS_INIT.exists(), (
        f"config/settings/__init__.py ne postoji na {SETTINGS_INIT}. "
        f"Bez njega `config.settings` nije validan Python paket."
    )


def test_ac1_base_dev_staging_production_modules_exist():
    """AC1: sva 4 settings modula moraju postojati (base/development/staging/production)."""
    required = [SETTINGS_BASE, SETTINGS_DEV, SETTINGS_STAGING, SETTINGS_PROD]
    missing = [str(p.relative_to(PROJECT_ROOT)) for p in required if not p.exists()]
    assert not missing, (
        f"Settings package nedostaju moduli: {missing}. "
        f"Svaki environment mora imati svoj `.py` fajl."
    )


def test_ac1_old_single_settings_py_removed():
    """AC1 / Gotcha #1 KRITICNO: `config/settings.py` (single file) MORA biti obrisan.

    Ako oba postoje (`config/settings.py` AND `config/settings/`), Python module
    resolution moze favorizovati single file, sto tiho razbija sve subsequent
    `manage.py check` komande. Task 5 u story-ji je MUST do.
    """
    assert not OLD_SETTINGS_FILE.exists(), (
        f"STARI single-file `config/settings.py` JOS POSTOJI na {OLD_SETTINGS_FILE}. "
        f"MORA biti obrisan posto je `config/settings/` paket kreiran "
        f"(inace Python module resolution moze koegzistencijom tiho razbiti import-e). "
        f"Pokreni: `Remove-Item config/settings.py` (PowerShell) ili `rm config/settings.py` (bash)."
    )


def test_ac1_config_package_init_preserved():
    """AC1 / Gotcha #9: `config/__init__.py` ostaje (NIJE config/settings/__init__.py).

    Dva razlicita package marker-a: jedan za `config` package, jedan za
    `config.settings` package. Lako ih je pobrkati pri refactor-u.
    """
    assert CONFIG_INIT.exists(), (
        f"config/__init__.py ne postoji na {CONFIG_INIT}. "
        f"To je config/ package marker iz Story 1.1 — ne sme se obrisati."
    )


def test_ac1_manage_py_check_passes_for_development():
    """AC1: `uv run python manage.py check --settings=config.settings.development`
    mora exit-ovati sa kodom 0.

    To je glavni AC1 acceptance signal — Django self-check potvrdjuje da je
    settings paket validan i konfigurisan korektno."""
    uv_bin = shutil.which("uv")
    if uv_bin is None:
        pytest.fail("uv binary nije u PATH-u. Instaliraj uv prvo.")
    if not MANAGE_PY.exists():
        pytest.fail("manage.py nedostaje — Story 1.1 nije done.")
    result = _run(
        [
            uv_bin,
            "run",
            "python",
            "manage.py",
            "check",
            "--settings=config.settings.development",
        ],
        env={"DJANGO_SECRET_KEY": TEST_SECRET},
    )
    assert result.returncode == 0, (
        f"`manage.py check --settings=config.settings.development` exit code "
        f"{result.returncode}.\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )


# =============================================================================
# AC2 — `base.py` content + django-environ integracija
# =============================================================================


def test_ac2_base_imports_environ():
    """AC2: `base.py` mora imati `import environ` na vrhu."""
    src = _read_settings_source("base")
    assert re.search(r"^\s*import\s+environ\b", src, re.MULTILINE), (
        "`base.py` ne sadrzi `import environ`. django-environ je core dependency "
        "story-ja. Dodaj `import environ` na vrhu fajla."
    )


def test_ac2_base_calls_environ_env_read_env():
    """AC2: `base.py` mora pozivati `environ.Env.read_env(...)`.

    Bez ovog poziva `.env` fajl se ne ucitava u os.environ — sve env varijable
    iz `.env` bi ostale neaktivne.
    """
    src = _read_settings_source("base")
    assert re.search(r"environ\.Env\.read_env\s*\(", src), (
        "`base.py` ne poziva `environ.Env.read_env(...)`. Bez toga `.env` fajl "
        "se ne ucitava. Dodaj `environ.Env.read_env(BASE_DIR / '.env')` posle env init-a."
    )
    # Mora postojati i env = environ.Env() instanca
    assert re.search(r"env\s*=\s*environ\.Env\s*\(", src), (
        "`base.py` ne kreira `env = environ.Env()` instancu. Bez toga env.bool/list/db/email_url "
        "ne moze biti pozvan."
    )


def test_ac2_base_secret_key_uses_env_no_default():
    """AC2 / Gotcha #3: SECRET_KEY se cita iz env-a BEZ default vrednosti (fail-fast).

    Ako env var nije set, env('DJANGO_SECRET_KEY') treba da raise-uje
    ImproperlyConfigured — to sprecava deploy sa unknown/missing secret-om.
    """
    src = _read_settings_source("base")
    # Match: SECRET_KEY = env('DJANGO_SECRET_KEY')   [bez default=]
    # Allow whitespace, single/double quotes.
    pattern = r"SECRET_KEY\s*=\s*env\s*\(\s*['\"]DJANGO_SECRET_KEY['\"]\s*\)"
    assert re.search(pattern, src), (
        "`base.py` ne sadrzi `SECRET_KEY = env('DJANGO_SECRET_KEY')` BEZ default-a. "
        "Fail-fast je security guardrail — env('DJANGO_SECRET_KEY') sa default-om "
        "tiho dozvoljava deploy sa fallback vrednoscu."
    )
    # Negativna provera — ne sme imati default= unutar SECRET_KEY env() poziva
    secret_line_pattern = r"SECRET_KEY\s*=\s*env\s*\([^)]*default\s*="
    assert not re.search(secret_line_pattern, src), (
        "`base.py` SECRET_KEY env() poziv ima `default=` argument. "
        "Story AC2 zahteva fail-fast (NEMA default-a)."
    )


def test_ac2_base_debug_default_false():
    """AC2 / Gotcha #4: DEBUG mora default-ovati na False (production-safe).

    `env.bool('DJANGO_DEBUG', default=False)` znaci: ako env var nije postavljen,
    DEBUG je False. Development.py override-uje na True.
    """
    src = _read_settings_source("base")
    pattern = (
        r"DEBUG\s*=\s*env\.bool\s*\(\s*['\"]DJANGO_DEBUG['\"]\s*,"
        r"\s*default\s*=\s*False\s*\)"
    )
    assert re.search(pattern, src), (
        "`base.py` ne sadrzi `DEBUG = env.bool('DJANGO_DEBUG', default=False)`. "
        "Mora default-ovati na False (Gotcha #4). Ako vidis `default=True` — to je BUG."
    )


def test_ac2_base_dir_three_parents():
    """AC2 / Gotcha #2: BASE_DIR ima 3 parent-a (config/settings/base.py je 3 nivoa
    duboko od root-a). Single-file `config/settings.py` je imao 2 parent-a — to
    razbija paths posle migracije.

    Verifikacija: import-uj `config.settings.base` i proveri da BASE_DIR == PROJECT_ROOT.
    """
    base = _load_settings_module("base")
    assert hasattr(base, "BASE_DIR"), "`base.py` ne eksponuje `BASE_DIR` attribute."
    assert isinstance(base.BASE_DIR, Path), (
        f"BASE_DIR mora biti pathlib.Path, dobijeno: {type(base.BASE_DIR)}"
    )
    # MORA biti repo root
    assert base.BASE_DIR.resolve() == PROJECT_ROOT.resolve(), (
        f"BASE_DIR pokazuje na pogresan direktorijum.\n"
        f"  Dobijeno: {base.BASE_DIR}\n"
        f"  Ocekivano (project root): {PROJECT_ROOT}\n"
        f"Verovatno koristi `parent.parent` umesto `parent.parent.parent` (3 nivoa)."
    )


def test_ac2_base_uses_env_db_for_databases():
    """AC2: `DATABASES['default']` MORA biti konstruisan kroz `env.db(...)`.

    Bez toga DATABASE_URL env var nema efekta — hardkodovani SQLite/PostgreSQL
    dict bi ignorisao prod env.
    """
    src = _read_settings_source("base")
    assert "env.db(" in src, (
        "`base.py` ne koristi `env.db(...)` za DATABASES. To znaci DATABASE_URL "
        "env var nije parsiran. Koristi `DATABASES = {'default': env.db('DATABASE_URL', default=...)}`"
    )
    # Mora referencirati DATABASE_URL env var
    pattern = r"env\.db\s*\(\s*['\"]DATABASE_URL['\"]"
    assert re.search(pattern, src), (
        "`env.db(...)` poziv ne referencira 'DATABASE_URL' env var. "
        "Mora biti `env.db('DATABASE_URL', default=...)`."
    )


# =============================================================================
# AC3 — Per-environment override moduli
# =============================================================================


def test_ac3_development_inherits_from_base():
    """AC3: `development.py` MORA imati `from .base import *` (canonical Django pattern)."""
    src = _read_settings_source("development")
    # Dozvoljen je trailing `# noqa: F401, F403` komentar
    pattern = r"^\s*from\s+\.base\s+import\s+\*"
    assert re.search(pattern, src, re.MULTILINE), (
        "`development.py` ne sadrzi `from .base import *`. To je obavezan canonical "
        "Django pattern — bez njega dev settings ne nasledjuje base konfiguraciju."
    )


def test_ac3_development_debug_true():
    """AC3: development.py override-uje DEBUG na True (dev convenience)."""
    dev = _load_settings_module("development")
    assert hasattr(dev, "DEBUG"), "`development.py` ne eksponuje DEBUG attribute."
    assert dev.DEBUG is True, (
        f"`development.DEBUG` mora biti True (dev convenience override). "
        f"Dobijeno: {dev.DEBUG!r}"
    )


def test_ac3_staging_inherits_from_base():
    """AC3: `staging.py` MORA imati `from .base import *`."""
    src = _read_settings_source("staging")
    pattern = r"^\s*from\s+\.base\s+import\s+\*"
    assert re.search(pattern, src, re.MULTILINE), (
        "`staging.py` ne sadrzi `from .base import *`. Canonical pattern obavezan."
    )


def test_ac3_staging_has_required_secure_settings():
    """AC3: staging.py MORA eksponovati 3 SECURE_* settings-a (production-like,
    bez HSTS pin-a) + SECURE_PROXY_SSL_HEADER (Nginx fronts staging).

    Staging je production-like za realan test, ali NAMERNO bez HSTS — HSTS pin
    na staging domeni moze napraviti trajnu nedostupnost ako se staging premesti.

    SECURE_PROXY_SSL_HEADER je obavezan jer Nginx termira TLS i Django mora
    poverovati X-Forwarded-Proto headeru (inace SECURE_SSL_REDIRECT loop).
    """
    staging = _load_settings_module("staging")
    expected = {
        "SECURE_SSL_REDIRECT": True,
        "SESSION_COOKIE_SECURE": True,
        "CSRF_COOKIE_SECURE": True,
    }
    for attr, expected_val in expected.items():
        assert hasattr(staging, attr), (
            f"`staging.py` ne eksponuje `{attr}`. AC3 explicit lista MUST-have."
        )
        actual = getattr(staging, attr)
        assert actual is expected_val, (
            f"`staging.{attr}` = {actual!r}, ocekivano {expected_val!r}."
        )
    # DEBUG mora biti False
    assert staging.DEBUG is False, (
        f"`staging.DEBUG` mora biti False (production-like). Dobijeno: {staging.DEBUG!r}"
    )
    # SECURE_PROXY_SSL_HEADER — Nginx X-Forwarded-Proto tuple (Dev Notes staging Template)
    assert hasattr(staging, "SECURE_PROXY_SSL_HEADER"), (
        "`staging.py` ne eksponuje `SECURE_PROXY_SSL_HEADER`. Nginx fronts staging "
        "(arhitektura), pa Django mora verovati X-Forwarded-Proto headeru — bez ovog "
        "tuple-a SECURE_SSL_REDIRECT bi pravio redirect loop."
    )
    assert staging.SECURE_PROXY_SSL_HEADER == ("HTTP_X_FORWARDED_PROTO", "https"), (
        f"`staging.SECURE_PROXY_SSL_HEADER` = {staging.SECURE_PROXY_SSL_HEADER!r}, "
        f"ocekivano ('HTTP_X_FORWARDED_PROTO', 'https')."
    )


def test_ac3_staging_does_not_have_hsts():
    """AC3 anti-test: staging.py NAMERNO NE postavlja `SECURE_HSTS_SECONDS`.

    Eksplicitna security odluka iz Dev Notes / Story AC3:
    HSTS pin-uje host na HTTPS (potencijalno preload listom) i pravi trajnu
    nedostupnost ako se staging premesti/ugasi. Pun HSTS set je samo u production.py.

    Ovaj anti-test enforce-uje dizajn odluku — bez njega bi Dev mogao da copy-paste
    HSTS iz prod-a u staging i niko ne bi primetio.
    """
    staging = _load_settings_module("staging")
    assert not hasattr(staging, "SECURE_HSTS_SECONDS"), (
        f"`staging.py` eksponuje `SECURE_HSTS_SECONDS = {getattr(staging, 'SECURE_HSTS_SECONDS', None)!r}` — "
        f"to NIJE u skladu sa AC3 (HSTS na staging-u je risk za preload pin). "
        f"Pun HSTS set ide SAMO u production.py. Ako je copy-paste iz prod-a — ukloni."
    )


def test_ac2_base_uses_env_email_url():
    """AC2 / Gotcha #7: `base.py` MORA koristiti `env.email_url(...)` helper +
    `vars().update(EMAIL_CONFIG)` canonical pattern za EMAIL_* settings.

    `env.email_url()` parsira EMAIL_URL env var i vraca dict sa EMAIL_BACKEND,
    EMAIL_HOST, EMAIL_PORT, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD, EMAIL_USE_TLS.
    `vars().update()` ih splat-uje kao module-level attribute (Django ih ocekuje
    kao top-level settings, ne kao dict).
    """
    src = _read_settings_source("base")
    assert "env.email_url(" in src, (
        "`base.py` ne koristi `env.email_url(...)` helper. Bez njega EMAIL_URL env var "
        "nema efekta, a console/SMTP backend switching kroz env varijable je broken. "
        "Dodaj: `EMAIL_CONFIG = env.email_url('EMAIL_URL', default='consolemail://')`."
    )
    # `env.email_url(` mora referencirati 'EMAIL_URL' env var
    pattern = r"env\.email_url\s*\(\s*['\"]EMAIL_URL['\"]"
    assert re.search(pattern, src), (
        "`env.email_url(...)` poziv ne referencira 'EMAIL_URL' env var. "
        "Mora biti `env.email_url('EMAIL_URL', default=...)`."
    )
    # Gotcha #7: `vars().update(EMAIL_CONFIG)` pattern mora postojati
    assert "vars().update(EMAIL_CONFIG)" in src, (
        "`base.py` ne sadrzi `vars().update(EMAIL_CONFIG)` pattern. "
        "Gotcha #7: env.email_url() vraca dict, a Django ocekuje top-level module "
        "attribute-e. `vars().update()` ih splat-uje (canonical django-environ pattern). "
        "Alternative je verbose manual unpacking — koristi canonical pattern."
    )


def test_ac3_production_debug_forced_false_unconditional():
    """AC3 defense-in-depth: `production.py` MORA FORCE-ovati DEBUG = False
    nezavisno od DJANGO_DEBUG env vara.

    Scenario: dev pogresno postavi `DJANGO_DEBUG=True` u prod env (production
    Hetzner panel). Base.py bi (kroz env.bool) postavio DEBUG=True, ali
    production.py mora override-ovati na False kao defense-in-depth.

    Bez ovog testa, regresija (npr. neko obrise `DEBUG = False` iz production.py)
    bi prosla quietly.
    """
    # Pre-set DJANGO_DEBUG=True PRE load-a production modula
    prior_debug = os.environ.get("DJANGO_DEBUG")
    os.environ["DJANGO_DEBUG"] = "True"
    try:
        prod = _load_settings_module("production")
        assert prod.DEBUG is False, (
            f"`production.DEBUG` = {prod.DEBUG!r} sa DJANGO_DEBUG=True u env-u. "
            f"Production MORA FORCE-ovati False (defense-in-depth) — eksplicitan "
            f"`DEBUG = False` mora preci nakon `from .base import *` (i NE sme zavisiti "
            f"od env vara)."
        )
    finally:
        # Restore prior DJANGO_DEBUG vrednost (ili obrisi ako nije bila set)
        if prior_debug is None:
            os.environ.pop("DJANGO_DEBUG", None)
        else:
            os.environ["DJANGO_DEBUG"] = prior_debug


def test_ac3_production_has_full_hsts_set():
    """AC3: production.py mora eksponovati FULL security hardening set + HSTS.

    Razlika u odnosu na staging: production DODAJE HSTS_SECONDS + HSTS_INCLUDE_SUBDOMAINS
    + HSTS_PRELOAD (jaca varijanta — pin-uje HTTPS na browseru).
    """
    prod = _load_settings_module("production")
    # DEBUG eksplicitno False (defense-in-depth)
    assert prod.DEBUG is False, (
        f"`production.DEBUG` mora biti False (defense-in-depth). Dobijeno: {prod.DEBUG!r}"
    )
    # Core SSL/cookie hardening (isti kao staging)
    bool_true_attrs = [
        "SECURE_SSL_REDIRECT",
        "SECURE_HSTS_INCLUDE_SUBDOMAINS",
        "SECURE_HSTS_PRELOAD",
        "SESSION_COOKIE_SECURE",
        "CSRF_COOKIE_SECURE",
    ]
    for attr in bool_true_attrs:
        assert hasattr(prod, attr), f"`production.py` ne eksponuje `{attr}`."
        actual = getattr(prod, attr)
        assert actual is True, f"`production.{attr}` = {actual!r}, ocekivano True."
    # HSTS seconds — bar 1 godina (31536000)
    assert hasattr(prod, "SECURE_HSTS_SECONDS"), (
        "`production.py` ne eksponuje `SECURE_HSTS_SECONDS`. Mora biti `env.int(..., default=31536000)`."
    )
    assert isinstance(prod.SECURE_HSTS_SECONDS, int), (
        f"`production.SECURE_HSTS_SECONDS` mora biti int. Dobijeno: "
        f"{type(prod.SECURE_HSTS_SECONDS)}"
    )
    assert prod.SECURE_HSTS_SECONDS >= 31536000, (
        f"`production.SECURE_HSTS_SECONDS` = {prod.SECURE_HSTS_SECONDS}, "
        f"mora biti >= 31536000 (1 godina)."
    )


def test_ac3_production_has_additional_security_headers():
    """AC3: production.py MORA eksponovati dodatne security header settings:
    SECURE_PROXY_SSL_HEADER, SECURE_REFERRER_POLICY, X_FRAME_OPTIONS.

    Story AC3 (production.py sekcija) explicit lista ove kao MUST-have:
    - SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https') — Django sluša Nginx
    - SECURE_REFERRER_POLICY = 'same-origin'
    - X_FRAME_OPTIONS = 'DENY'
    """
    prod = _load_settings_module("production")
    # SECURE_PROXY_SSL_HEADER — tuple ('HTTP_X_FORWARDED_PROTO', 'https')
    assert hasattr(prod, "SECURE_PROXY_SSL_HEADER"), (
        "`production.py` ne eksponuje `SECURE_PROXY_SSL_HEADER`. AC3 zahteva "
        "`('HTTP_X_FORWARDED_PROTO', 'https')` (Django sluša Nginx X-Forwarded-Proto)."
    )
    assert prod.SECURE_PROXY_SSL_HEADER == ("HTTP_X_FORWARDED_PROTO", "https"), (
        f"`production.SECURE_PROXY_SSL_HEADER` = {prod.SECURE_PROXY_SSL_HEADER!r}, "
        f"ocekivano ('HTTP_X_FORWARDED_PROTO', 'https')."
    )
    # SECURE_REFERRER_POLICY = 'same-origin'
    assert hasattr(prod, "SECURE_REFERRER_POLICY"), (
        "`production.py` ne eksponuje `SECURE_REFERRER_POLICY`. AC3 zahteva 'same-origin'."
    )
    assert prod.SECURE_REFERRER_POLICY == "same-origin", (
        f"`production.SECURE_REFERRER_POLICY` = {prod.SECURE_REFERRER_POLICY!r}, "
        f"ocekivano 'same-origin'."
    )
    # X_FRAME_OPTIONS = 'DENY'
    assert hasattr(prod, "X_FRAME_OPTIONS"), (
        "`production.py` ne eksponuje `X_FRAME_OPTIONS`. AC3 zahteva 'DENY'."
    )
    assert prod.X_FRAME_OPTIONS == "DENY", (
        f"`production.X_FRAME_OPTIONS` = {prod.X_FRAME_OPTIONS!r}, ocekivano 'DENY'."
    )


# =============================================================================
# AC4 — `.env.example` template
# =============================================================================


def test_ac4_env_example_exists():
    """AC4: `.env.example` MORA postojati u root-u (committable template)."""
    assert ENV_EXAMPLE.exists(), (
        f".env.example ne postoji na {ENV_EXAMPLE}. "
        f"Kreiraj template fajl (vidi Dev Notes § `.env.example` Template)."
    )


def test_ac4_env_example_contains_required_keys():
    """AC4: `.env.example` mora sadrzati sve required env kljuceve sa
    placeholder/empty vrednostima.

    Takodje verifikuje da `DJANGO_SETTINGS_MODULE=` NIJE aktivna linija (Gotcha #16).
    """
    if not ENV_EXAMPLE.exists():
        pytest.fail(".env.example ne postoji (videti prethodni test).")
    content = ENV_EXAMPLE.read_text(encoding="utf-8")

    # Required keys — linije moraju POCETI sa <KEY>= (allow leading whitespace)
    required_keys = [
        "DJANGO_SECRET_KEY",
        "DJANGO_DEBUG",
        "DJANGO_ALLOWED_HOSTS",
        "DATABASE_URL",
        "EMAIL_URL",
        "DJANGO_SECURE_HSTS_SECONDS",
    ]
    missing = []
    for key in required_keys:
        pattern = rf"^\s*{re.escape(key)}\s*="
        if not re.search(pattern, content, re.MULTILINE):
            missing.append(key)
    assert not missing, (
        f".env.example ne sadrzi sledece env kljuceve: {missing}. "
        f"Svaki mora postojati kao `KEY=` linija (vrednost moze biti prazna ili placeholder)."
    )

    # NEGATIVE: `DJANGO_SETTINGS_MODULE=` NE sme biti aktivna linija (only comments allowed)
    # Pattern: linija pocinje sa DJANGO_SETTINGS_MODULE= (bez # prefiksa).
    bad_lines = []
    for raw in content.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if re.match(r"^DJANGO_SETTINGS_MODULE\s*=", line):
            bad_lines.append(raw)
    assert not bad_lines, (
        f".env.example ima AKTIVNU `DJANGO_SETTINGS_MODULE=` liniju: {bad_lines}. "
        f"Gotcha #16: settings modul se odlucuje PRE citanja .env-a, pa postavljanje "
        f"u .env nema efekta. Premesti u comment ili obrisi."
    )


def test_ac4_env_in_gitignore_with_carveout():
    """AC4 / AC5: .gitignore mora i dalje ignorisati `.env` ALI carve-out `!.env.example`
    mora postojati (inace template fajl bi bio gitignored)."""
    assert GITIGNORE.exists(), f".gitignore ne postoji na {GITIGNORE}"
    content = GITIGNORE.read_text(encoding="utf-8")
    # `.env` (real one) MORA biti ignored
    assert re.search(r"^\.env\s*$", content, re.MULTILINE), (
        ".gitignore nema bare `.env` liniju. Story 1.1 ga je dodao — proveri da nije slucajno obrisan."
    )
    # `!.env.example` carve-out MORA postojati
    assert re.search(r"^!\.env\.example\s*$", content, re.MULTILINE), (
        ".gitignore nema `!.env.example` carve-out. Bez njega committable template fajl "
        "bi bio gitignored. Story 1.1 ga je dodao — restore-uj ako je obrisan."
    )


# =============================================================================
# AC5 — manage.py / wsgi.py / asgi.py default DJANGO_SETTINGS_MODULE
# =============================================================================


def test_ac5_manage_py_default_settings_module_updated():
    """AC5: `manage.py` MORA postaviti default `DJANGO_SETTINGS_MODULE` na
    `config.settings.development` (NIJE vise bare `config.settings`).
    """
    assert MANAGE_PY.exists(), f"manage.py ne postoji na {MANAGE_PY}"
    content = MANAGE_PY.read_text(encoding="utf-8")
    # Mora referencirati novi target
    assert "config.settings.development" in content, (
        "`manage.py` ne sadrzi `'config.settings.development'`. "
        "Posle Story 1.2 default-uje na development env (NIJE vise bare 'config.settings'). "
        "Update liniju: `os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')`."
    )
    # NEGATIVE: bare `'config.settings'` (BEZ `.development` suffix-a) ne sme biti
    # u istoj setdefault liniji. Provera kroz regex koji eksplicitno hvata BARE varijantu.
    bad_pattern = r"setdefault\s*\(\s*['\"]DJANGO_SETTINGS_MODULE['\"]\s*,\s*['\"]config\.settings['\"]"
    assert not re.search(bad_pattern, content), (
        "`manage.py` JOS uvek default-uje na bare 'config.settings' (Story 1.1 vrednost). "
        "Mora biti 'config.settings.development'."
    )


def test_ac5_wsgi_py_default_settings_module_updated():
    """AC5: `config/wsgi.py` MORA referencirati `config.settings.development`."""
    assert WSGI_PY.exists(), f"wsgi.py ne postoji na {WSGI_PY}"
    content = WSGI_PY.read_text(encoding="utf-8")
    assert "config.settings.development" in content, (
        "`config/wsgi.py` ne sadrzi 'config.settings.development'. "
        "Update liniju 14: `os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')`."
    )
    bad_pattern = r"setdefault\s*\(\s*['\"]DJANGO_SETTINGS_MODULE['\"]\s*,\s*['\"]config\.settings['\"]"
    assert not re.search(bad_pattern, content), (
        "`config/wsgi.py` JOS uvek default-uje na bare 'config.settings'."
    )


def test_ac5_asgi_py_default_settings_module_updated():
    """AC5: `config/asgi.py` MORA referencirati `config.settings.development`."""
    assert ASGI_PY.exists(), f"asgi.py ne postoji na {ASGI_PY}"
    content = ASGI_PY.read_text(encoding="utf-8")
    assert "config.settings.development" in content, (
        "`config/asgi.py` ne sadrzi 'config.settings.development'. "
        "Update liniju 14: `os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')`."
    )
    bad_pattern = r"setdefault\s*\(\s*['\"]DJANGO_SETTINGS_MODULE['\"]\s*,\s*['\"]config\.settings['\"]"
    assert not re.search(bad_pattern, content), (
        "`config/asgi.py` JOS uvek default-uje na bare 'config.settings'."
    )


# =============================================================================
# Edge cases / negative tests / security guardrails
# =============================================================================


def test_secret_key_fail_fast_when_missing():
    """SECURITY / Gotcha #3: Ako DJANGO_SECRET_KEY env var NIJE set i .env fajl
    ne sadrzi DJANGO_SECRET_KEY, importovanje `config.settings.base` MORA da padne
    sa ImproperlyConfigured-like exception-om.

    Test koristi subprocess sa eksplicitno OBRISANIM DJANGO_SECRET_KEY env varom
    da bi izolovao state-less import.
    """
    uv_bin = shutil.which("uv")
    if uv_bin is None:
        pytest.fail("uv binary nije u PATH-u.")
    # Pripremi cistu env bez DJANGO_SECRET_KEY
    clean_env = {k: v for k, v in os.environ.items() if k != "DJANGO_SECRET_KEY"}
    # Privremeno premesti `.env` fajl ako postoji (da test bude reproducible)
    env_file = PROJECT_ROOT / ".env"
    env_file_backup = PROJECT_ROOT / ".env.tea-backup-tmp"
    moved = False
    if env_file.exists():
        env_file.rename(env_file_backup)
        moved = True
    try:
        # Inline Python: import base settings module
        code = (
            "import sys, os; "
            f"sys.path.insert(0, r'{PROJECT_ROOT}'); "
            "import config.settings.base"
        )
        result = subprocess.run(
            [uv_bin, "run", "python", "-c", code],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            shell=False,
            timeout=60,
            env=clean_env,
        )
        # Import MORA da padne — exit code != 0
        assert result.returncode != 0, (
            f"Importovanje `config.settings.base` BEZ DJANGO_SECRET_KEY env vara "
            f"NIJE padlo (exit 0). Fail-fast guardrail je BROKEN.\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
        # stderr mora pomenuti ImproperlyConfigured ili DJANGO_SECRET_KEY
        combined = (result.stdout + result.stderr).lower()
        assert (
            "improperlyconfigured" in combined
            or "django_secret_key" in combined
            or "secret_key" in combined
        ), (
            f"Greska pri import-u ne pominje SECRET_KEY/ImproperlyConfigured.\n"
            f"stderr: {result.stderr}"
        )
    finally:
        # Vrati `.env` fajl na mesto ako smo ga premestili
        if moved and env_file_backup.exists():
            env_file_backup.rename(env_file)


def test_no_hardcoded_secret_key_in_base():
    """SECURITY: `base.py` NE SME sadrzati hardkodovan `django-insecure-...`
    SECRET_KEY (Django startproject default).

    Story 1.1 `config/settings.py` je imao `SECRET_KEY = 'django-insecure-d2^...'` —
    to NE SME procureti u `base.py` posle migracije.
    """
    src = _read_settings_source("base")
    assert "django-insecure-" not in src, (
        "`base.py` sadrzi hardkodovan 'django-insecure-...' string (Django startproject "
        "default leak). Mora biti uklonjen — SECRET_KEY se cita iz env-a, nije u kodu."
    )
    # Negative — ne sme biti ni literal `SECRET_KEY = "..."` sa hardkodovanom vrednoscu
    # (osim env() poziva). Pattern: SECRET_KEY = 'string-literal' (bez env( poziva u istoj liniji)
    for line in src.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        # Match SECRET_KEY = 'something' BEZ env( ili os.environ
        if re.match(r"^SECRET_KEY\s*=\s*['\"]", stripped):
            pytest.fail(
                f"`base.py` ima hardkodovan SECRET_KEY = '...' (literal string). "
                f"Linija: {stripped!r}. Mora biti `SECRET_KEY = env('DJANGO_SECRET_KEY')`."
            )
