"""Tests za Story 9.6 — Django Logging Konfiguracija (LOGGING dict).

Verifikuje da `config/settings/base.py` definiše `LOGGING` dict (console→stdout,
`disable_existing_loggers=False`, žičani django/django.request/django.security/apps
loggeri, propagate=True svuda) koji koegzistira sa 9-3 sentry-sdk LoggingIntegration
BEZ double-report-a i BEZ Sentry-starvation-a, sa per-env tightening-om
(production tiši, development verbose).

Organizacija (po AC):
- AC1: logging.config.dictConfig(settings.LOGGING) NE baca (SUBPROCESS izolacija — G-4)
- AC2: console handler → ext://sys.stdout (NE stderr — G-2)
- AC3: konkretni prod nivoi (django=WARNING, django.request=ERROR, django.security=ERROR/WARNING, apps=INFO)
- AC4: disable_existing_loggers is False (G-1)
- AC5: prod nivo != dev nivo (NUMERIČKO poređenje)
- AC6: format string bez PII/secret token-a + nema mail_admins/AdminEmailHandler + django.server odsutan
- AC7: nema sentry/glitchtip handler-a u LOGGING + propagate-starvation guard + sentry init netaknut
- AC8: base-vs-per-env split (base SOT, per-env override) + cross-env kontaminacija guard (G-7)
- AC9 negativni: base.py NE sadrži LOGGING_CONFIG = None (G-3) + root/console level <= INFO (G-13)

Pokrenuti sa:
    uv run pytest tests/test_logging_config.py -v

TEA RED faza: svi testovi MORAJU pasti dok Dev ne doda `LOGGING` dict.
Host caveat (G-9): native Windows pytest collect pada na libmagic (pre-existing
baseline Epic 9). Ovi testovi su IMPORT-LIGHT: _read_settings_source (čist file read),
_load_settings_module (import-uje SAMO config.settings.<env> — bez admin autodiscover),
subprocess `uv run python -c` za živi dictConfig (NE zagađuje pytest logging state — G-4).

Naming convention: srpska latinica + engleski; bez cirilice.
"""

from __future__ import annotations

import importlib
import logging
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

# =============================================================================
# Konstante (project paths) — mirror tests/test_settings_split.py
# =============================================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
SETTINGS_PKG_DIR = CONFIG_DIR / "settings"

# Test SECRET_KEY za import (NIJE realan secret — samo za test imports)
TEST_SECRET = "test-secret-key-for-tea-imports-not-a-real-secret"

# Zabranjeni PII/secret token-i u format string-u (AC6, case-insensitive scan).
# Story AC6 eksplicitna lista: `request` (pun request objekat), `password`, `secret`,
# `cookie`, `authorization`, `token`, `body`. Word-boundary regex (\b...\b) hvata bare
# `request`/`body` (npr. "{request}" / "{body}" leaky formatter) BEZ false-positive-a na
# kanonske metadata token-e ({levelname}/{asctime}/{name}/{module}/{process}/{thread}/{message}
# — nijedan ne sadrži `request` ni `body` kao podstring). Bez ovoga bi formatter koji
# loguje pun request objekat ("{levelname} {request} {message}") PROŠAO guard (PII leak).
FORBIDDEN_FORMAT_TOKENS = (
    "password",
    "passwd",
    "secret",
    "token",
    "authorization",
    "cookie",
    "request",
    "body",
    "csrf",
)


# =============================================================================
# Helper funkcije — mirror tests/test_settings_split.py
# =============================================================================


def _read_settings_source(module_name: str) -> str:
    """Procita `config/settings/<module_name>.py` source za regex/substring proveru
    BEZ importovanja modula (bezbedno za pattern check na host-u — G-9)."""
    path = SETTINGS_PKG_DIR / f"{module_name}.py"
    if not path.exists():
        pytest.fail(f"config/settings/{module_name}.py ne postoji na {path}")
    return path.read_text(encoding="utf-8")


def _load_settings_module(module_name: str):
    """Importuje `config.settings.<module_name>` posle setovanja test DJANGO_SECRET_KEY.

    Force fresh import: brise target + SVE config.settings.* iz sys.modules (bitno jer
    per-env moduli rade `from .base import *` — base mora biti svez za G-7 cross-env test).
    Import-uje SAMO settings modul (NE triggeruje admin autodiscover / libmagic — G-9).
    """
    os.environ.setdefault("DJANGO_SECRET_KEY", TEST_SECRET)
    # FLAKY guard: pop DJANGO_LOG_LEVEL pre import-a da stray env var (set drugim
    # testom/run-om) NE iskrivi AC5/AC8 numeričko poređenje nivoa — root level u base.py
    # čita DJANGO_LOG_LEVEL iz env-a. Mirror `setdefault` opreza za SECRET_KEY.
    os.environ.pop("DJANGO_LOG_LEVEL", None)
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    full_name = f"config.settings.{module_name}"
    for mod_key in list(sys.modules.keys()):
        if (
            mod_key == full_name
            or mod_key.startswith(f"{full_name}.")
            or mod_key.startswith("config.settings.")
        ):
            del sys.modules[mod_key]
    return importlib.import_module(full_name)


def _run(cmd, env=None, cwd=None) -> subprocess.CompletedProcess:
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


def _level_int(level) -> int:
    """Normalizuje logging level (str ili int) u int za numeričko poređenje (AC5).

    `logging.getLevelName("WARNING")` → 30; `logging.getLevelName(30)` → "WARNING".
    Ako je već int, vrati ga; ako je str, mapiraj kroz getLevelName.
    """
    if isinstance(level, int):
        return level
    mapped = logging.getLevelName(str(level).upper())
    assert isinstance(mapped, int), (
        f"Logging level {level!r} nije validan (getLevelName vratio {mapped!r}). "
        f"Očekivano DEBUG/INFO/WARNING/ERROR/CRITICAL."
    )
    return mapped


def _dictconfig_subprocess(settings_module: str) -> subprocess.CompletedProcess:
    """Pozove logging.config.dictConfig(settings.LOGGING) u IZOLOVANOM subprocess-u (G-4).

    dictConfig mutira globalni logging registry; izolacija sprečava zagađenje
    pytest log capture-a. Set-uje DJANGO_SETTINGS_MODULE + DJANGO_SECRET_KEY,
    import-uje settings modul, poziva dictConfig, print-uje OK. Exit 0 = valid dict.
    """
    uv_bin = shutil.which("uv")
    if uv_bin is None:
        pytest.fail("uv binary nije u PATH-u. Instaliraj uv prvo.")
    code = (
        "import sys, logging.config; "
        f"sys.path.insert(0, r'{PROJECT_ROOT}'); "
        f"import importlib; settings = importlib.import_module('{settings_module}'); "
        "assert hasattr(settings, 'LOGGING'), 'NEMA LOGGING dict u settings modulu'; "
        "logging.config.dictConfig(settings.LOGGING); "
        "print('DICTCONFIG_OK')"
    )
    return _run(
        [uv_bin, "run", "python", "-c", code],
        env={
            "DJANGO_SETTINGS_MODULE": settings_module,
            "DJANGO_SECRET_KEY": TEST_SECRET,
        },
    )


# =============================================================================
# AC1 — LOGGING dict postoji + logging.config.dictConfig ga prihvata (SUBPROCESS)
# =============================================================================


def test_ac1_logging_dict_exists_in_base():
    # AC1: base.py eksponuje LOGGING kao dict sa version == 1.
    base = _load_settings_module("base")
    assert hasattr(base, "LOGGING"), (
        "`config.settings.base` ne eksponuje `LOGGING`. Story 9.6 dodaje LOGGING dict u base.py."
    )
    assert isinstance(base.LOGGING, dict), (
        f"`base.LOGGING` mora biti dict, dobijeno: {type(base.LOGGING)}"
    )
    assert base.LOGGING.get("version") == 1, (
        f"`base.LOGGING['version']` mora biti 1 (dictConfig schema), dobijeno: "
        f"{base.LOGGING.get('version')!r}"
    )


def test_ac1_dictconfig_valid_production_subprocess():
    # AC1: logging.config.dictConfig(production.LOGGING) NE baca (izolovan subprocess — G-4).
    result = _dictconfig_subprocess("config.settings.production")
    assert result.returncode == 0 and "DICTCONFIG_OK" in result.stdout, (
        f"logging.config.dictConfig(production.LOGGING) PADA ili LOGGING ne postoji.\n"
        f"exit: {result.returncode}\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )


def test_ac1_dictconfig_valid_development_subprocess():
    # AC1: logging.config.dictConfig(development.LOGGING) NE baca (izolovan subprocess — G-4).
    result = _dictconfig_subprocess("config.settings.development")
    assert result.returncode == 0 and "DICTCONFIG_OK" in result.stdout, (
        f"logging.config.dictConfig(development.LOGGING) PADA ili LOGGING ne postoji.\n"
        f"exit: {result.returncode}\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )


# =============================================================================
# AC2 — Console handler → stdout (NE stderr — G-2)
# =============================================================================


def test_ac2_console_handler_streams_stdout():
    # AC2: handlers.console.stream == "ext://sys.stdout" + class StreamHandler.
    base = _load_settings_module("base")
    handlers = base.LOGGING.get("handlers", {})
    assert "console" in handlers, (
        f"`LOGGING['handlers']` nema `console` handler. Dobijeni handler-i: {list(handlers)}"
    )
    console = handlers["console"]
    assert console.get("class") == "logging.StreamHandler", (
        f"`console` handler class mora biti 'logging.StreamHandler', dobijeno: "
        f"{console.get('class')!r}"
    )
    assert console.get("stream") == "ext://sys.stdout", (
        f"`console` handler stream mora biti 'ext://sys.stdout' (Docker/journald capture, "
        f"12-factor), dobijeno: {console.get('stream')!r}"
    )


def test_ac2_console_handler_not_stderr():
    # AC2 NEGATIVE: console handler NE sme ciljati stderr (G-2 default footgun).
    base = _load_settings_module("base")
    console = base.LOGGING["handlers"]["console"]
    stream = console.get("stream")
    assert stream is not None, (
        "`console` handler NEMA eksplicitan `stream` ključ → default je sys.stderr (G-2). "
        "Mora eksplicitno 'ext://sys.stdout'."
    )
    assert "stderr" not in str(stream).lower(), (
        f"`console` handler stream cilja stderr ({stream!r}) — mora biti stdout (G-2)."
    )


def test_ac2_no_default_file_handler():
    # AC2: NEMA file handler-a na /var/log/django/* kao default (SM-D1 — anti-pattern u kontejneru).
    base = _load_settings_module("base")
    handlers = base.LOGGING.get("handlers", {})
    for name, cfg in handlers.items():
        cls = str(cfg.get("class", "")).lower()
        assert "filehandler" not in cls, (
            f"Handler `{name}` je file handler (class={cfg.get('class')!r}) — SM-D1 "
            f"zabranjuje in-container file handler kao default (gubi se pri restart-u)."
        )
        filename = str(cfg.get("filename", ""))
        assert "/var/log" not in filename, (
            f"Handler `{name}` loguje u {filename!r} — /var/log file handler je SM-D1 anti-pattern."
        )


# =============================================================================
# AC3 — Žičani loggeri + konkretni PRODUCTION nivoi (numerička provera)
# =============================================================================


def test_ac3_wired_loggers_present():
    # AC3: prisutni django / django.request / django.security / apps loggeri.
    base = _load_settings_module("base")
    loggers = base.LOGGING.get("loggers", {})
    for name in ("django", "django.request", "django.security", "apps"):
        assert name in loggers, (
            f"`LOGGING['loggers']` nema žičan logger `{name}`. Dobijeni: {list(loggers)}"
        )


def test_ac3_production_concrete_levels():
    # AC3: production efektivni nivoi KONKRETNI (numerička falsifikacija).
    prod = _load_settings_module("production")
    loggers = prod.LOGGING["loggers"]
    assert _level_int(loggers["django"]["level"]) == logging.WARNING, (
        f"production `django` nivo mora biti WARNING(30), dobijeno: {loggers['django']['level']!r}"
    )
    assert _level_int(loggers["django.request"]["level"]) == logging.ERROR, (
        f"production `django.request` nivo mora biti ERROR(40), dobijeno: "
        f"{loggers['django.request']['level']!r}"
    )
    assert _level_int(loggers["django.security"]["level"]) in (
        logging.ERROR,
        logging.WARNING,
    ), (
        f"production `django.security` nivo mora biti ERROR(40) ili WARNING(30), dobijeno: "
        f"{loggers['django.security']['level']!r}"
    )
    assert _level_int(loggers["apps"]["level"]) == logging.INFO, (
        f"production `apps` nivo mora biti INFO(20), dobijeno: {loggers['apps']['level']!r}"
    )


def test_ac3_django_db_backends_not_wired():
    # AC3: django.db.backends NIJE žičan (SQL noise/PII rizik — G-8/SM-D8).
    base = _load_settings_module("base")
    loggers = base.LOGGING.get("loggers", {})
    assert "django.db.backends" not in loggers, (
        "`django.db.backends` JE žičan u LOGGING — NE sme biti (loguje svaki SQL query "
        "uključujući parametre = noise/PII rizik; G-8/SM-D8)."
    )


# =============================================================================
# AC4 — disable_existing_loggers is False (KRITIČNO — G-1)
# =============================================================================


def test_ac4_disable_existing_loggers_is_false():
    # AC4: disable_existing_loggers is False eksplicitno (NE ubij Django/SDK loggere — G-1).
    base = _load_settings_module("base")
    assert "disable_existing_loggers" in base.LOGGING, (
        "`LOGGING` NEMA `disable_existing_loggers` ključ — dictConfig default je True što "
        "GASI Django/sentry-sdk loggere (G-1). Mora eksplicitno False."
    )
    assert base.LOGGING["disable_existing_loggers"] is False, (
        f"`LOGGING['disable_existing_loggers']` mora biti False (G-1/SM-D4), dobijeno: "
        f"{base.LOGGING['disable_existing_loggers']!r}"
    )


# =============================================================================
# AC5 — Prod nivo != dev nivo (NUMERIČKO poređenje — per-env tightening)
# =============================================================================


def test_ac5_dev_more_verbose_than_prod_numeric():
    # AC5: development verbose-niji (numerički NIŽI nivo) od production na bar jednom logger-u.
    # Učitaj OBA modula; numeričko poređenje (DEBUG=10 < INFO=20 < WARNING=30 < ERROR=40).
    dev = _load_settings_module("development")
    prod = _load_settings_module("production")
    dev_loggers = dev.LOGGING["loggers"]
    prod_loggers = prod.LOGGING["loggers"]

    diffs = []
    for name in ("django", "apps"):
        if name in dev_loggers and name in prod_loggers:
            d = _level_int(dev_loggers[name]["level"])
            p = _level_int(prod_loggers[name]["level"])
            if d < p:
                diffs.append((name, d, p))
    assert diffs, (
        "Nijedan žičani logger nije verbose-niji u dev nego u prod (numerički). "
        f"dev django={dev_loggers.get('django', {}).get('level')!r} apps={dev_loggers.get('apps', {}).get('level')!r}; "
        f"prod django={prod_loggers.get('django', {}).get('level')!r} apps={prod_loggers.get('apps', {}).get('level')!r}. "
        "AC5 zahteva dev_level < prod_level na bar jednom žičanom logger-u."
    )


def test_ac5_both_envs_use_console_stdout():
    # AC5: oba env-a i dalje koriste console→stdout (base nasleđen, NE re-definisan od nule).
    for env_mod in ("development", "production"):
        mod = _load_settings_module(env_mod)
        console = mod.LOGGING["handlers"]["console"]
        assert console.get("stream") == "ext://sys.stdout", (
            f"`{env_mod}` console handler stream nije 'ext://sys.stdout' (base handler "
            f"mora biti nasleđen): {console.get('stream')!r}"
        )


# =============================================================================
# AC6 — Format string bez PII/secret token-a + nema mail_admins + django.server odsutan
# =============================================================================


def test_ac6_all_formatters_no_pii_tokens():
    # AC6: ITERIRA preko SVIH formatter format string-ova — nijedan ne sadrži PII/secret token.
    base = _load_settings_module("base")
    formatters = base.LOGGING.get("formatters", {})
    assert formatters, "`LOGGING['formatters']` je prazan — mora postojati bar `verbose` formatter."
    for fmt_name, cfg in formatters.items():
        fmt = str(cfg.get("format", "")).lower()
        for token in FORBIDDEN_FORMAT_TOKENS:
            # Word-boundary match: hvata bare `request`/`body`/`token` kao zaseban token
            # ("{request}", "{body}") ali NE kao podstring legitimnih metapodataka.
            assert not re.search(rf"\b{re.escape(token.lower())}\b", fmt), (
                f"Formatter `{fmt_name}` format string sadrži zabranjeni PII/secret token "
                f"`{token}`: {cfg.get('format')!r} (AC6/SM-D5)."
            )


def test_ac6_no_mail_admins_or_admin_email_handler():
    # AC6: nijedan handler nije mail_admins / AdminEmailHandler (traceback sa lokalnim vars — SM-D5).
    base = _load_settings_module("base")
    handlers = base.LOGGING.get("handlers", {})
    assert "mail_admins" not in handlers, (
        "`LOGGING['handlers']` ima `mail_admins` — zabranjeno (SM-D5; GlitchTip je error kanal)."
    )
    for name, cfg in handlers.items():
        cls = str(cfg.get("class", ""))
        assert "AdminEmailHandler" not in cls, (
            f"Handler `{name}` je AdminEmailHandler (class={cls!r}) — zabranjeno (SM-D5)."
        )


def test_ac6_django_server_logger_not_wired():
    # AC6: django.server NIJE žičan (request-line leak — PII rizik).
    base = _load_settings_module("base")
    loggers = base.LOGGING.get("loggers", {})
    assert "django.server" not in loggers, (
        "`django.server` JE žičan u LOGGING — NE sme (request-line PII leak; AC6)."
    )


# =============================================================================
# AC7 — Sentry koegzistencija (no double-report, no starvation, init netaknut)
# =============================================================================


def test_ac7_no_sentry_glitchtip_handler_in_logging():
    # AC7: NIJEDAN handler nema class koji sadrži sentry/glitchtip (SDK integracija jaše sama — SM-D3).
    base = _load_settings_module("base")
    handlers = base.LOGGING.get("handlers", {})
    for name, cfg in handlers.items():
        cls = str(cfg.get("class", "")).lower()
        assert "sentry" not in cls and "glitchtip" not in cls, (
            f"Handler `{name}` cilja sentry/glitchtip (class={cfg.get('class')!r}) — "
            f"ZABRANJENO (dupli report; SM-D3). SDK LoggingIntegration jaše sama."
        )


def test_ac7_no_logger_starves_sentry_propagation():
    # AC7/G-12: nijedan žičani logger nema propagate==False UZ neprazan sopstveni handlers
    # (Sentry-starvation: record bi se zaustavio pre root-a → SDK ne bi dobio event/breadcrumb).
    base = _load_settings_module("base")
    loggers = base.LOGGING.get("loggers", {})
    offenders = []
    for name, cfg in loggers.items():
        own_handlers = cfg.get("handlers") or []
        propagate = cfg.get("propagate", True)
        if propagate is False and own_handlers:
            offenders.append((name, own_handlers))
    assert not offenders, (
        f"Logger-i sa propagate=False UZ sopstveni handler (gladuju sentry-sdk — G-12/SM-D3): "
        f"{offenders}. Kanonski obrazac: console SAMO na root, žičani loggeri propagate=True "
        f"bez sopstvenog handler-a."
    )


def test_ac7_wired_loggers_propagate_true():
    # AC7: žičani loggeri imaju propagate True (ili izostavljen = default True) — kanonski obrazac.
    base = _load_settings_module("base")
    loggers = base.LOGGING.get("loggers", {})
    for name in ("django", "django.request", "django.security", "apps"):
        cfg = loggers.get(name, {})
        propagate = cfg.get("propagate", True)
        assert propagate is True, (
            f"Žičani logger `{name}` ima propagate={propagate!r} — kanonski obrazac zahteva "
            f"propagate=True (ili izostavljen) da sentry-sdk root-attached handler dobije record (SM-D8/G-12)."
        )


def test_ac7_production_sentry_init_untouched():
    # AC7: production.py i dalje sadrži sentry_sdk.init blok (regression guard — 9.6 ga NE menja).
    src = _read_settings_source("production")
    assert re.search(r"import\s+sentry_sdk", src), (
        "`production.py` više ne import-uje sentry_sdk — 9.6 NE sme ukloniti 9-3 init (AC7)."
    )
    assert re.search(r"sentry_sdk\.init\s*\(", src), (
        "`production.py` više nema `sentry_sdk.init(...)` — 9.6 NE sme dirati 9-3 blok (AC7 regression)."
    )


def test_ac7_staging_sentry_init_untouched():
    # AC7: staging.py i dalje sadrži sentry_sdk.init (environment="staging") — regression guard.
    src = _read_settings_source("staging")
    assert re.search(r"sentry_sdk\.init\s*\(", src), (
        "`staging.py` više nema `sentry_sdk.init(...)` — 9.6 NE sme dirati staging blok (AC7)."
    )
    assert 'environment="staging"' in src or "environment='staging'" in src, (
        "`staging.py` sentry init više nema `environment=\"staging\"` — regression (AC7)."
    )


def test_ac7_base_and_development_no_sentry_init():
    # AC7: base.py i development.py NEMAJU sentry init (9-3 invariant očuvan).
    for mod in ("base", "development"):
        src = _read_settings_source(mod)
        assert not re.search(r"sentry_sdk\.init\s*\(", src), (
            f"`{mod}.py` ima `sentry_sdk.init(...)` — 9-3 invariant je da sentry init NIJE u {mod} (AC7)."
        )


# =============================================================================
# AC8 — base-vs-per-env split (base SOT, per-env override) + cross-env guard (G-7)
# =============================================================================


def test_ac8_per_env_does_not_redefine_full_logging():
    # AC8: production.py i development.py NE re-definišu ceo LOGGING dict od nule
    # (`LOGGING = {` literal). Base.py je taj koji definiše pun dict.
    base_src = _read_settings_source("base")
    assert re.search(r"^\s*LOGGING\s*=\s*\{", base_src, re.MULTILINE), (
        "`base.py` ne definiše `LOGGING = {` literal — base mora biti SOT dict (SM-D6)."
    )
    for mod in ("production", "development"):
        src = _read_settings_source(mod)
        assert not re.search(r"^\s*LOGGING\s*=\s*\{", src, re.MULTILINE), (
            f"`{mod}.py` re-definiše ceo `LOGGING = {{` dict od nule — SM-D6 zahteva SAMO "
            f"level override (npr. `LOGGING['loggers'][...]['level'] = ...` ili deepcopy + mutate)."
        )


def test_ac8_cross_env_no_contamination():
    # AC8/G-7: učitavanje development PA production (isti proces) mora dati RAZLIČITE nivoe
    # (NE poslednji-pobeđuje bug zbog deljene nested reference). Round-trip oba smera.
    dev = _load_settings_module("development")
    dev_django = _level_int(dev.LOGGING["loggers"]["django"]["level"])
    prod = _load_settings_module("production")
    prod_django = _level_int(prod.LOGGING["loggers"]["django"]["level"])
    # Re-load development ponovo — ne sme pokupiti production vrednost (cross-kontaminacija).
    dev2 = _load_settings_module("development")
    dev2_django = _level_int(dev2.LOGGING["loggers"]["django"]["level"])

    assert prod_django == logging.WARNING, (
        f"production `django` nivo posle dev→prod load = {prod_django}, očekivano WARNING(30)."
    )
    assert dev2_django == dev_django, (
        f"development `django` nivo se promenio posle učitavanja production "
        f"({dev_django} → {dev2_django}) — deljena nested LOGGING referenca cross-kontaminira "
        f"(G-7). Koristi copy.deepcopy(LOGGING) ili re-assign nested key u per-env modulu."
    )
    assert dev2_django != prod_django, (
        f"development i production `django` nivo su jednaki ({dev2_django}) posle round-trip-a "
        f"— per-env tightening nije opstao (G-7 cross-kontaminacija)."
    )


# =============================================================================
# AC9 — Negativni source guard-ovi + breadcrumb level guard
# =============================================================================


def test_ac9_base_no_logging_config_none():
    # AC9/G-3: base.py source NE sme sadržati `LOGGING_CONFIG = None`
    # (to bi reklo Django-u da NE primeni LOGGING dict uopšte).
    src = _read_settings_source("base")
    assert not re.search(r"LOGGING_CONFIG\s*=\s*None", src), (
        "`base.py` sadrži `LOGGING_CONFIG = None` — to onemogućava primenu LOGGING dict-a (G-3). "
        "Drži default LOGGING_CONFIG (NE diraj), samo definiši LOGGING dict."
    )


def test_ac9_base_has_django_log_level_env_var():
    """AC9 / SM-D9: base.py mora citati DJANGO_LOG_LEVEL iz env-a (operativni log-level knob)."""
    src = _read_settings_source("base")
    assert re.search(r'DJANGO_LOG_LEVEL\s*=\s*env\s*\(\s*["\']DJANGO_LOG_LEVEL["\']', src), (
        "base.py nema `DJANGO_LOG_LEVEL = env('DJANGO_LOG_LEVEL', ...)` — SM-D9 operativni mehanizam izostao."
    )


def test_ac9_root_level_le_info_for_breadcrumbs():
    # AC9/G-13: root level <= INFO (numerički) da sentry-sdk INFO+→breadcrumb radi (production).
    prod = _load_settings_module("production")
    root_cfg = prod.LOGGING.get("root", {})
    assert "level" in root_cfg, "`LOGGING['root']` nema `level` ključ."
    assert _level_int(root_cfg["level"]) <= logging.INFO, (
        f"production root level = {root_cfg['level']!r} > INFO(20) — degradira sentry-sdk "
        f"breadcrumb-ove (G-13). Root mora ostati <= INFO; tightening ide PER-LOGGER preko level."
    )


def test_ac9_console_handler_level_le_info_for_breadcrumbs():
    # AC9/G-13: console handler level <= INFO da INFO+ record stigne do SDK breadcrumb handler-a.
    base = _load_settings_module("base")
    console = base.LOGGING["handlers"]["console"]
    # Handler level je opcioni; ako je odsutan default je 0 (NOTSET) = propušta sve → OK.
    level = console.get("level", "NOTSET")
    assert _level_int(level) <= logging.INFO, (
        f"console handler level = {level!r} > INFO(20) — filtrira INFO record-e pre SDK "
        f"breadcrumb handler-a (G-13). Drži <= INFO."
    )


def test_ac9_root_wires_console_handler():
    # AC9/SM-D8: root MORA imati console handler (kanonski obrazac — handler na root).
    base = _load_settings_module("base")
    root_cfg = base.LOGGING.get("root", {})
    assert "console" in (root_cfg.get("handlers") or []), (
        f"`LOGGING['root']['handlers']` ne sadrži 'console' — kanonski obrazac (SM-D8) zahteva "
        f"console handler SAMO na root. Dobijeno: {root_cfg.get('handlers')!r}"
    )
