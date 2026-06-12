"""Tests za Story 9.3 — GlitchTip 6 Self-host Setup.

INFRA-VERIFY testovi (needs_e2e=false — NE Playwright/browser). Ovo NIJE Django app —
deliverable-i su CONFIG fajlovi:
  - compose/production.yml       (AKTIVIRA glitchtip + glitchtip-worker + glitchtip-postgres
                                  + glitchtip-redis; ~512m mem limit; retention 30d)
  - config/settings/production.py + staging.py  (DSN-guarded sentry_sdk.init)
  - .env.example                 (GlitchTip placeholderi, svi prazni)
  - pyproject.toml               (sentry-sdk[django] u [project].dependencies)

Test pristup je IMPORT-LIGHT (mirror tests/test_deployment_ssl.py host-runnable obrazac):
  - file-parsing (pathlib + re + yaml) za .env.example / pyproject.toml / raw compose,
  - `docker compose -f compose/production.yml config` SUBPROCESS za rendered YAML
    (BEZ `--quiet` za AC7(f) mem-limit parse; mirror _run_docker_compose_config),
  - SUBPROCESS `python -c "import config.settings.production"` za settings-import sanity
    (svez interpreter — NE trip-uje libmagic u pytest parent procesu; mirror Story 9.3
    Task 6.2/6.3 hint).

NE import-uje Django apps/admin, NE zahteva DB. Zato fajl COLLECT-uje i trci na native
Windows host-u uprkos dokumentovanom libmagic baseline-u (python-magic missing — pre-existing,
NIJE regresija). Docker-zavisni testovi se SKIP-uju ako docker nije na PATH-u (RED OK).

Pokrenuti sa:
    uv run pytest tests/test_glitchtip_monitoring.py -v -p no:cacheprovider

TEA RED faza: SVI implemented-behavior testovi MORAJU pasti/error-ovati dok Dev ne zavrsi
Story 9.3 (nema glitchtip servisa, nema sentry-sdk dep, nema settings init blok, nema .env
kljuceva). Docker-zavisni testovi mogu SKIP ako docker nedostaje — to je OK u RED-u.

Naming convention: srpska latinica + engleski identifikatori; bez cirilice.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

try:
    import yaml as _yaml  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover
    _yaml = None  # type: ignore[assignment]


# =============================================================================
# Konstante (project paths) — mirror test_production_stack.py / test_deployment_ssl.py
# =============================================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

COMPOSE_DIR = PROJECT_ROOT / "compose"
PRODUCTION_YML = COMPOSE_DIR / "production.yml"

ENV_EXAMPLE = PROJECT_ROOT / ".env.example"
PYPROJECT = PROJECT_ROOT / "pyproject.toml"

UV_LOCK = PROJECT_ROOT / "uv.lock"

SETTINGS_DIR = PROJECT_ROOT / "config" / "settings"
PRODUCTION_PY = SETTINGS_DIR / "production.py"
STAGING_PY = SETTINGS_DIR / "staging.py"
BASE_PY = SETTINGS_DIR / "base.py"
DEVELOPMENT_PY = SETTINGS_DIR / "development.py"

# Cetiri glitchtip servisa koja 9.3 aktivira (SM-D2 / G-1).
GLITCHTIP_SERVICES = ("glitchtip", "glitchtip-worker", "glitchtip-postgres", "glitchtip-redis")

# Test vrednosti za settings-import (NISU realni secret-i — samo za test child process).
TEST_SECRET = "test-secret-key-for-tea-9-3-glitchtip-not-real"
TEST_DATABASE_URL = "postgres://coric:coric@localhost:5432/coric_agrar"
# Ne-prazan, SINTAKSNO VALIDAN Sentry DSN (G-17: validan DSN ne sme da baci BadDsn pri init-u).
TEST_GLITCHTIP_DSN = "https://abc123def456@glitchtip.example/42"

# AC7 mem-limit prihvatljiv opseg ~512m (400m–600m u bajtovima).
MEM_MIN_BYTES = 400 * 1024 * 1024
MEM_MAX_BYTES = 600 * 1024 * 1024


# =============================================================================
# Helper funkcije
# =============================================================================


def _read_file(path: Path, owner: str = "Story 9.3") -> str:
    """Procita text fajl. Fail-uje (RED signal) sa jasnom porukom ako ne postoji."""
    if not path.exists():
        pytest.fail(f"Missing required file: {path}\n{owner} Dev ga mora kreirati/azurirati.")
    return path.read_text(encoding="utf-8")


def _docker_bin() -> str | None:
    return shutil.which("docker")


def _python_bin() -> str:
    """Interpreter za subprocess settings-import (isti venv kao test runner)."""
    return sys.executable or "python"


def _run_compose_config(quiet: bool) -> subprocess.CompletedProcess | None:
    """`docker compose -f production.yml config [--quiet]`. None ako docker nije na PATH-u.

    quiet=True → lint-only (exit code provera). quiet=False → rendered YAML na stdout
    (AC7(f) mem-limit parse mora citati rendered output — `--quiet` ne emituje YAML).
    """
    docker = _docker_bin()
    if docker is None:
        return None
    cmd = [docker, "compose", "-f", str(PRODUCTION_YML), "config"]
    if quiet:
        cmd.append("--quiet")
    return subprocess.run(
        cmd,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        shell=False,
        timeout=120,
    )


def _parsed_compose_config() -> dict:
    """Rendered (interpoliran) compose config kao dict. Skip ako docker/pyyaml nedostaje.

    Mirror test_production_stack._parsed_compose_config ali BEZ `--quiet` (treba YAML).
    """
    if not PRODUCTION_YML.exists():
        pytest.fail(f"Missing required file: {PRODUCTION_YML}\nStory 9.3 Task 1 ga aktivira.")
    result = _run_compose_config(quiet=False)
    if result is None:
        pytest.skip("docker CLI nije na PATH-u — preskacem parsed compose config.")
    if result.returncode != 0:
        pytest.fail(
            f"`docker compose -f production.yml config` exit {result.returncode}.\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}\n"
            f"Verovatno YAML schema greska ili nedeklarisan glitchtip volume."
        )
    if _yaml is None:
        pytest.skip("pyyaml nedostaje — ne mogu da parsiram compose config output.")
    return _yaml.safe_load(result.stdout)


def _service_env_map(service: dict) -> dict[str, str]:
    """Normalizuj `environment:` (list ili mapping) u {KEY: value} dict."""
    environment = service.get("environment", {})
    if isinstance(environment, dict):
        return {str(k): ("" if v is None else str(v)) for k, v in environment.items()}
    env_map: dict[str, str] = {}
    for item in environment or []:
        if isinstance(item, str) and "=" in item:
            k, _, v = item.partition("=")
            env_map[k] = v
        elif isinstance(item, str):
            env_map[item] = ""
    return env_map


def _depends_on_keys(service: dict) -> list[str]:
    """Vrati listu servisa na koje `depends_on` pokazuje (lista ili mapping forma)."""
    dep = service.get("depends_on", [])
    if isinstance(dep, dict):
        return list(dep.keys())
    if isinstance(dep, list):
        return [str(d) for d in dep]
    return []


def _parse_mem_to_bytes(value) -> int | None:
    """Parsuj compose memory vrednost (npr. `512m`, `536870912`, `0.5g`) u bajtove.

    Vraca int bajtova ili None ako se ne moze parsirati.
    """
    if value is None:
        return None
    if isinstance(value, int):
        return value
    s = str(value).strip().lower()
    m = re.fullmatch(r"(\d+(?:\.\d+)?)\s*([kmg]?)(b|i?b)?", s)
    if not m:
        # Mozda cist broj kao string
        try:
            return int(float(s))
        except ValueError:
            return None
    num = float(m.group(1))
    unit = m.group(2)
    factor = {"": 1, "k": 1024, "m": 1024**2, "g": 1024**3}[unit]
    return int(num * factor)


def _glitchtip_web_mem_bytes(glitchtip: dict) -> int | None:
    """Izvuci deklarisan memory limit na glitchtip web servisu (deploy.resources.limits.memory
    ILI legacy mem_limit) i parsuj u bajtove. None ako nijedan nije deklarisan."""
    # deploy.resources.limits.memory
    deploy = glitchtip.get("deploy", {}) or {}
    resources = deploy.get("resources", {}) or {}
    limits = resources.get("limits", {}) or {}
    deploy_mem = limits.get("memory")
    if deploy_mem is not None:
        return _parse_mem_to_bytes(deploy_mem)
    # legacy mem_limit
    mem_limit = glitchtip.get("mem_limit")
    if mem_limit is not None:
        return _parse_mem_to_bytes(mem_limit)
    return None


def _rendered_glitchtip_env(service: str) -> dict[str, str] | None:
    """Vrati rendered `environment:` mapping glitchtip servisa kroz `docker compose config`.

    None ako docker/pyyaml nedostaje ILI servis nije u rendered config-u (→ caller pada na
    raw-source fallback). NE skip-uje sam — caller bira (rendered vs raw)."""
    docker = _docker_bin()
    if docker is None or _yaml is None or not PRODUCTION_YML.exists():
        return None
    result = _run_compose_config(quiet=False)
    if result is None or result.returncode != 0:
        return None
    data = _yaml.safe_load(result.stdout)
    svc = data.get("services", {}).get(service)
    if svc is None:
        return None
    return _service_env_map(svc)


def _glitchtip_block_active_mentions(pattern: str) -> bool:
    """True ako AKTIVNA (non-comment) linija production.yml matchuje `pattern`, u opsegu
    POSLE prve linije koja pominje `glitchtip` (da zakomentarisan 9.1 placeholder ili
    nepovezana linija lazno ne zadovolji). Mirror SECRET_KEY raw-fallback strogosti."""
    raw = _read_file(PRODUCTION_YML)
    active = "\n".join(ln for ln in raw.splitlines() if not ln.lstrip().startswith("#"))
    return re.search(pattern, active) is not None


def _import_settings_subprocess(
    module: str, extra_env: dict[str, str], shim_sentry: bool = False
) -> subprocess.CompletedProcess:
    """Spawn svez interpreter koji import-uje `config.settings.<module>`.

    Izolacija: svez interpreter NEMA pre-import-ovan settings singleton (pytest-django) i
    NE trip-uje libmagic u parent procesu (Story 9.3 Host caveat / Task 6.2-6.3).

    shim_sentry=False → cista import sanity (AC3): exit 0 = import uspeo bez crash-a.
    shim_sentry=True  → ubaci fake `sentry_sdk` modul koji hvata init kwargs i printuje
                        `__SENTRY_INIT__<json>` na stdout (AC4/AC5 wiring asercija) BEZ
                        prave Sentry biblioteke/network-a.

    `.env` u repo-u privremeno NE smemo da pustimo da injektuje vrednosti — child dobija
    GLITCHTIP_DSN iskljucivo kroz kontrolisan env (subprocess env). Da bismo bili sigurni
    da prazan-DSN test stvarno vidi prazan DSN i kad postoji repo `.env`, eksplicitno
    setujemo GLITCHTIP_DSN="" u env-u (env ima prednost? — django-environ read_env NE
    override-uje vec postojeci os.environ kljuc: setdefault semantika). Zato je env-set
    deterministican za prazan slucaj.
    """
    if shim_sentry:
        code = textwrap.dedent(
            f"""
            import sys, types, json
            captured = {{}}
            shim = types.ModuleType("sentry_sdk")
            def _init(*args, **kwargs):
                payload = dict(kwargs)
                if args:
                    payload.setdefault("dsn", args[0])
                # Serijalizuj samo JSON-friendly vrednosti
                safe = {{}}
                for k, v in payload.items():
                    try:
                        json.dumps(v)
                        safe[k] = v
                    except TypeError:
                        safe[k] = repr(v)
                captured["init"] = safe
            shim.init = _init
            sys.modules["sentry_sdk"] = shim
            import importlib
            importlib.import_module("config.settings.{module}")
            print("__SENTRY_INIT__" + json.dumps(captured.get("init")))
            """
        )
    else:
        code = textwrap.dedent(
            f"""
            import importlib
            importlib.import_module("config.settings.{module}")
            print("__IMPORT_OK__")
            """
        )

    child_env = os.environ.copy()
    child_env["DJANGO_SECRET_KEY"] = TEST_SECRET
    child_env["DJANGO_ALLOWED_HOSTS"] = "localhost"
    child_env["DATABASE_URL"] = TEST_DATABASE_URL
    child_env["PYTHONPATH"] = str(PROJECT_ROOT) + os.pathsep + child_env.get("PYTHONPATH", "")
    child_env.update(extra_env)

    return subprocess.run(
        [_python_bin(), "-c", code],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        shell=False,
        timeout=120,
        env=child_env,
    )


def _extract_sentry_init(proc: subprocess.CompletedProcess) -> dict | None:
    """Iz child stdout-a izvuci `__SENTRY_INIT__<json>` payload (kwargs dict) ili None
    ako init nije pozvan (payload je JSON null)."""
    for line in proc.stdout.splitlines():
        if line.startswith("__SENTRY_INIT__"):
            raw = line[len("__SENTRY_INIT__"):]
            return json.loads(raw)  # dict ili None
    return None  # marker se nije pojavio → import pao pre print-a


# =============================================================================
# AC1 — glitchtip servisi aktivirani + compose config lint cist
# =============================================================================


def test_ac1_production_yml_config_lints_clean():
    """# AC-1: `docker compose -f compose/production.yml config --quiet` exit 0 sa
    aktiviranim glitchtip servisima (YAML/schema/reference lint cist). [docker-skip]."""
    if not PRODUCTION_YML.exists():
        pytest.fail(f"Missing required file: {PRODUCTION_YML}")
    result = _run_compose_config(quiet=True)
    if result is None:
        pytest.skip("docker CLI nije na PATH-u — preskacem AC1 config lint.")
    assert result.returncode == 0, (
        f"`docker compose -f production.yml config --quiet` exit {result.returncode}.\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}\n"
        f"AC1: aktivirani glitchtip servisi moraju da lint-uju cisto (nedeklarisan "
        f"glitchtip_postgres_data volume / lose interpolacije su cesti uzroci)."
    )


def test_ac1_four_glitchtip_services_present():
    """# AC-1: rendered compose config MORA imati sva 4 glitchtip servisa (web+worker+
    postgres+redis) — G-1/SM-D2: sva cetiri ili nista. [docker-skip]."""
    data = _parsed_compose_config()
    services = data.get("services", {})
    assert isinstance(services, dict), f"`services:` nije mapping: {type(services)}"
    missing = [s for s in GLITCHTIP_SERVICES if s not in services]
    assert not missing, (
        f"compose/production.yml nedostaju glitchtip servisi: {missing}. "
        f"Pronadjeno: {sorted(services.keys())}. "
        f"AC1/SM-D2/G-1: aktiviraj web + worker + glitchtip-postgres + glitchtip-redis."
    )


def test_ac1_existing_services_untouched_regression():
    """# AC-1: postojeci django/postgres/nginx servisi ostaju (regression guard). [docker-skip]."""
    data = _parsed_compose_config()
    services = data.get("services", {})
    missing = [s for s in ("postgres", "django", "nginx") if s not in services]
    assert not missing, (
        f"compose/production.yml izgubio postojece servise: {missing} (regresija!). "
        f"AC1: 9.3 SAMO dodaje glitchtip stack — NE dira django/postgres/nginx."
    )


def test_ac1_glitchtip_postgres_separate_named_volume():
    """# AC-1/G-7: glitchtip-postgres koristi ZASEBAN named volume `glitchtip_postgres_data`
    (NE deli `postgres_data`). [docker-skip]."""
    data = _parsed_compose_config()
    volumes = data.get("volumes", {})
    assert isinstance(volumes, dict), f"top-level `volumes:` nije mapping: {type(volumes)}"
    assert "glitchtip_postgres_data" in volumes, (
        f"compose/production.yml nema top-level `glitchtip_postgres_data` volume. "
        f"Pronadjeno: {sorted(volumes.keys())}. "
        f"AC1/G-7: GlitchTip postgres MORA imati zaseban named volume (NE deli app DB volume)."
    )


# =============================================================================
# AC2 — sentry-sdk[django] u pyproject [project].dependencies
# =============================================================================


def test_ac2_sentry_sdk_django_extra_in_dependencies():
    """# AC-2/G-12: pyproject.toml [project].dependencies sadrzi `sentry-sdk[django]`
    (specificno `[django]` extra, NE bare `sentry-sdk`)."""
    content = _read_file(PYPROJECT)
    proj_match = re.search(
        r"^\[project\]\s*\n(.*?)(?=^\[)", content, re.MULTILINE | re.DOTALL
    )
    assert proj_match, "pyproject.toml nema [project] sekciju (neocekivano)."
    deps_match = re.search(
        r"dependencies\s*=\s*\[(.*?)^\]", proj_match.group(1), re.DOTALL | re.MULTILINE
    )
    assert deps_match, "pyproject.toml [project].dependencies blok nije pronadjen."
    deps_blob = deps_match.group(1)
    # MUST: `sentry-sdk[django]` (extra eksplicitno). Tolerantno na verziju posle `]`.
    assert re.search(r"['\"]sentry-sdk\[django\]", deps_blob), (
        "pyproject.toml [project].dependencies NEMA `sentry-sdk[django]` (sa `[django]` "
        "extra-om). AC2/G-12: bare `sentry-sdk` nije dovoljan — `[django]` extra obezbedjuje "
        "DjangoIntegration auto-discovery. Pokreni `uv add 'sentry-sdk[django]'`.\n"
        f"deps blob: {deps_blob.strip()}"
    )


def test_ac2_sentry_sdk_not_in_dev_group():
    """# AC-2 NEGATIVE: sentry-sdk NE SME biti u [dependency-groups].dev (runtime dep,
    mora u prod --no-dev venv)."""
    content = _read_file(PYPROJECT)
    dev_match = re.search(
        r"^\[dependency-groups\]\s*\n(.*?)(?=^\[|\Z)", content, re.MULTILINE | re.DOTALL
    )
    if dev_match:
        assert "sentry-sdk" not in dev_match.group(1), (
            "sentry-sdk je u [dependency-groups].dev — pogresna grupa. AC2/Task 2.1: "
            "runtime error-tracking dep mora u [project].dependencies (prod --no-dev venv)."
        )


def test_ac2_sentry_sdk_resolved_in_uv_lock():
    """# AC-2 lockfile guard: uv.lock MORA imati resolved `sentry-sdk` package entry.

    pyproject.toml deklarise `sentry-sdk[django]`, ali rucna pyproject izmena moze da desync-uje
    lock (zaboravljen `uv lock`/`uv sync`). Prod `uv sync --no-dev --frozen` build install-uje
    iz uv.lock — ako tamo nema sentry-sdk, error-tracking nikad ne stigne u image uprkos
    "zelenom" pyproject testu. Import-light: cist file-read + regex, bez Django/uv subprocess-a.

    GREEN regression guard (uv.lock vec ima sentry-sdk v2.62.0) — NE RED test."""
    content = _read_file(UV_LOCK)
    # uv.lock je TOML: svaki paket je `[[package]]` tabela sa `name = "<paket>"` linijom.
    assert re.search(r'^\s*name\s*=\s*"sentry-sdk"\s*$', content, re.MULTILINE), (
        "uv.lock NEMA resolved `name = \"sentry-sdk\"` package entry. "
        "AC2 lockfile desync: pyproject.toml deklarise sentry-sdk[django] ali lock nije "
        "regenerisan. Pokreni `uv lock` (ili `uv add 'sentry-sdk[django]'`) da resolved verzija "
        "udje u uv.lock — inace prod `uv sync --frozen` ne install-uje SDK."
    )


# =============================================================================
# AC3 — empty-DSN import sanity (production + staging) — SUBPROCESS, #1 behavior
# =============================================================================


@pytest.mark.parametrize("module", ["production", "staging"], ids=["production", "staging"])
def test_ac3_empty_dsn_import_succeeds(module):
    """# AC-3 (KRITICNO/G-2): `config.settings.<module>` ima DSN-guarded init blok I import-uje
    se BEZ crash-a kad je GLITCHTIP_DSN PRAZAN (sentry no-op).

    Dve asercije:
      (1) SOURCE MORA imati guarded init (`if GLITCHTIP_DSN:` + `sentry_sdk.init`) — RED dok
          Dev ne doda blok (empty-DSN-no-crash je inace trivijalno zadovoljen i bez bloka, pa
          source-guard daje RED zub i obezbedjuje da #1 behavior bude STVARNO implementiran).
      (2) SUBPROCESS import (svez interpreter — ne trip-uje libmagic u pytest parent) exit 0 sa
          praznim DSN-om: guard grana je False → init NIJE pozvan → Django se DIZE."""
    src = _read_file(PRODUCTION_PY if module == "production" else STAGING_PY)
    assert re.search(r"if\s+GLITCHTIP_DSN\s*:", src), (
        f"config/settings/{module}.py nema `if GLITCHTIP_DSN:` guard. "
        f"AC3/SM-D3/G-2/Task 3.1: dodaj DSN-guarded `sentry_sdk.init` blok. "
        f"Empty-DSN-no-crash je inace trivijalno tacan i bez bloka — guard MORA postojati."
    )
    assert re.search(r"sentry_sdk\.init\s*\(", src), (
        f"config/settings/{module}.py nema `sentry_sdk.init(...)` poziv. AC3/Task 3.1."
    )
    proc = _import_settings_subprocess(module, {"GLITCHTIP_DSN": ""})
    assert proc.returncode == 0, (
        f"`python -c import config.settings.{module}` (GLITCHTIP_DSN='') exit "
        f"{proc.returncode} — settings import PAO sa praznim DSN-om.\n"
        f"stdout: {proc.stdout}\nstderr: {proc.stderr}\n"
        f"AC3/SM-D3/G-2: prazan/odsutan GLITCHTIP_DSN MORA biti no-op (`if GLITCHTIP_DSN:` "
        f"guard False), Django se DIZE bez izuzetka."
    )
    assert "__IMPORT_OK__" in proc.stdout, (
        f"settings.{module} import nije stigao do kraja modula (marker nedostaje).\n"
        f"stdout: {proc.stdout}\nstderr: {proc.stderr}"
    )


# =============================================================================
# AC4 — set-DSN wiring (production) — SUBPROCESS sa fake sentry_sdk shim-om
# =============================================================================


def test_ac4_set_dsn_calls_init_with_production_kwargs():
    """# AC-4: sa setovanim GLITCHTIP_DSN, production settings poziva sentry_sdk.init sa
    dsn=<vrednost> + environment='production' + send_default_pii=False + traces_sample_rate.
    SUBPROCESS sa shim-ovanim sentry_sdk (hvata kwargs; bez prave biblioteke/network-a)."""
    proc = _import_settings_subprocess(
        "production", {"GLITCHTIP_DSN": TEST_GLITCHTIP_DSN}, shim_sentry=True
    )
    assert proc.returncode == 0, (
        f"production settings import sa setovanim DSN-om exit {proc.returncode}.\n"
        f"stdout: {proc.stdout}\nstderr: {proc.stderr}\n"
        f"AC4: ocekivano da `if GLITCHTIP_DSN:` grana pozove sentry_sdk.init."
    )
    init = _extract_sentry_init(proc)
    assert init is not None, (
        "sentry_sdk.init NIJE pozvan iako je GLITCHTIP_DSN setovan (payload None).\n"
        f"stdout: {proc.stdout}\nstderr: {proc.stderr}\n"
        "AC4/Task 3.1: production.py MORA imati `if GLITCHTIP_DSN: sentry_sdk.init(...)`."
    )
    assert init.get("dsn") == TEST_GLITCHTIP_DSN, (
        f"sentry_sdk.init dsn = {init.get('dsn')!r}, ocekivano {TEST_GLITCHTIP_DSN!r} "
        f"(env var GLITCHTIP_DSN, NE SENTRY_DSN — usaglaseno sa production.py:70 hook-om)."
    )
    assert init.get("environment") == "production", (
        f"sentry_sdk.init environment = {init.get('environment')!r}, ocekivano 'production'. "
        f"AC4/SM-D4: environment tag razdvaja prod/staging event-e u GlitchTip UI."
    )
    assert init.get("send_default_pii") is False, (
        f"sentry_sdk.init send_default_pii = {init.get('send_default_pii')!r}, ocekivano "
        f"False. AC4/SM-D4: GDPR — NIKAD PII (Epic 7 projekt je GDPR-osetljiv)."
    )
    assert "traces_sample_rate" in init, (
        "sentry_sdk.init NEMA traces_sample_rate kwarg. AC4/SM-D4: "
        "`traces_sample_rate=env.float('SENTRY_TRACES_SAMPLE_RATE', default=0.0)`."
    )
    assert isinstance(init["traces_sample_rate"], (int, float)), (
        f"traces_sample_rate nije broj: {init['traces_sample_rate']!r} (env.float parse)."
    )


# =============================================================================
# AC5 — dev/base NE init-uju; staging pozitivna wiring parity + `from .base import env`
# =============================================================================


@pytest.mark.parametrize("module", ["development", "base"], ids=["development", "base"])
def test_ac5_dev_and_base_do_not_init_even_with_dsn(module):
    """# AC-5/SM-D5/G-8: development.py i base.py NE pozivaju sentry_sdk.init cak ni kad je
    GLITCHTIP_DSN setovan (nema error egress u dev-u). SUBPROCESS shim hvata init."""
    proc = _import_settings_subprocess(
        module, {"GLITCHTIP_DSN": TEST_GLITCHTIP_DSN}, shim_sentry=True
    )
    assert proc.returncode == 0, (
        f"settings.{module} import sa setovanim DSN-om exit {proc.returncode}.\n"
        f"stdout: {proc.stdout}\nstderr: {proc.stderr}"
    )
    init = _extract_sentry_init(proc)
    assert init is None, (
        f"settings.{module} POZVAO sentry_sdk.init (kwargs: {init!r}) iako NE sme. "
        f"AC5/SM-D5/G-8: init je SAMO u production/staging — dev/base ostaju cisti "
        f"(nema double-report, nema dev error egress-a)."
    )


def test_ac5_staging_inits_with_staging_environment():
    """# AC-5: staging.py wiring parity — sa setovanim GLITCHTIP_DSN poziva sentry_sdk.init
    sa IDENTICNIM kwargs-ima kao production ALI environment='staging' (G-4)."""
    proc = _import_settings_subprocess(
        "staging", {"GLITCHTIP_DSN": TEST_GLITCHTIP_DSN}, shim_sentry=True
    )
    assert proc.returncode == 0, (
        f"staging settings import sa setovanim DSN-om exit {proc.returncode}.\n"
        f"stdout: {proc.stdout}\nstderr: {proc.stderr}"
    )
    init = _extract_sentry_init(proc)
    assert init is not None, (
        "staging.py NIJE pozvao sentry_sdk.init iako je GLITCHTIP_DSN setovan. "
        "AC5/Task 4.1: staging dobija ISTI guarded init blok kao production."
    )
    assert init.get("environment") == "staging", (
        f"staging sentry_sdk.init environment = {init.get('environment')!r}, ocekivano "
        f"'staging' (NE 'production'). G-4: lako je copy-paste-ovati production blok i "
        f"zaboraviti environment override."
    )
    assert init.get("send_default_pii") is False, (
        f"staging send_default_pii = {init.get('send_default_pii')!r}, ocekivano False (GDPR parity)."
    )
    assert init.get("dsn") == TEST_GLITCHTIP_DSN, (
        f"staging dsn = {init.get('dsn')!r}, ocekivano {TEST_GLITCHTIP_DSN!r}."
    )
    # AC5 parity: staging koristi IDENTICNE kwargs kao production osim environment — wiring
    # MORA ukljuciti traces_sample_rate (mirror AC4 production asercije L497-503).
    assert "traces_sample_rate" in init, (
        "staging sentry_sdk.init NEMA traces_sample_rate kwarg. AC5/SM-D4: staging dobija ISTI "
        "guarded init blok kao production (`traces_sample_rate=env.float('SENTRY_TRACES_SAMPLE_RATE', "
        "default=0.0)`) — samo environment='staging' se razlikuje."
    )
    assert isinstance(init["traces_sample_rate"], (int, float)), (
        f"staging traces_sample_rate nije broj: {init['traces_sample_rate']!r} (env.float parse)."
    )


def test_ac5_staging_has_explicit_env_import():
    """# AC-5/Task 4.2: staging.py MORA imati eksplicitan `from .base import env` (sprecava
    ruff F405 jer init blok koristi env(...)/env.float(...))."""
    content = _read_file(STAGING_PY)
    assert re.search(r"from\s+\.base\s+import\s+\(?\s*[^)\n]*\benv\b", content), (
        "config/settings/staging.py nema eksplicitan `from .base import env`. "
        "AC5/Task 4.2: novi init blok koristi env(...)/env.float(...) — bez eksplicitnog "
        "import-a ruff baca F405 ('env may be undefined from star import') na `just lint`. "
        "Mirror production.py L4-6."
    )


def test_ac5_base_and_development_source_have_no_sentry_init():
    """# AC-5 NEGATIVE (static): base.py i development.py SOURCE ne sadrze `sentry_sdk.init`
    (regression — ostaju cisti)."""
    for path in (BASE_PY, DEVELOPMENT_PY):
        content = _read_file(path)
        non_comment = "\n".join(
            ln for ln in content.splitlines() if not ln.lstrip().startswith("#")
        )
        assert "sentry_sdk.init" not in non_comment, (
            f"{path.name} sadrzi `sentry_sdk.init` u izvrsnoj liniji. "
            f"AC5/SM-D5/G-8: init je SAMO u production/staging. base/development ostaju cisti."
        )


# =============================================================================
# AC6 — .env.example GlitchTip placeholderi (svi prazni)
# =============================================================================


def test_ac6_env_example_has_all_glitchtip_keys():
    """# AC-6: .env.example sadrzi sve required GlitchTip placeholder kljuceve."""
    content = _read_file(ENV_EXAMPLE)
    required_keys = [
        "GLITCHTIP_DSN",
        "GLITCHTIP_SECRET_KEY",
        "GLITCHTIP_DATABASE_URL",
        "GLITCHTIP_REDIS_URL",
        "GLITCHTIP_DOMAIN",
        "GLITCHTIP_MAX_EVENT_LIFE_DAYS",
        "GLITCHTIP_EMAIL_URL",
    ]
    missing = [
        k for k in required_keys
        if not re.search(rf"^\s*{re.escape(k)}\s*=", content, re.MULTILINE)
    ]
    assert not missing, (
        f".env.example nedostaju GlitchTip kljucevi: {missing}. "
        f"AC6/Task 5.1: dodaj sve kao placeholdere u 'Error tracking' sekciju."
    )


def test_ac6_glitchtip_secrets_are_empty_placeholders():
    """# AC-6: secret/DSN/URL kljucevi su PRAZNI placeholderi (nista posle `=`) — NIJEDAN
    realan secret. (GLITCHTIP_MAX_EVENT_LIFE_DAYS=30 je non-secret default, izuzet.)"""
    content = _read_file(ENV_EXAMPLE)
    must_be_empty = [
        "GLITCHTIP_DSN",
        "GLITCHTIP_SECRET_KEY",
        "GLITCHTIP_DATABASE_URL",
        "GLITCHTIP_REDIS_URL",
        "GLITCHTIP_DOMAIN",
        "GLITCHTIP_EMAIL_URL",
    ]
    non_empty = []
    for key in must_be_empty:
        m = re.search(rf"^\s*{re.escape(key)}\s*=(.*)$", content, re.MULTILINE)
        if m and m.group(1).strip():
            non_empty.append((key, m.group(1).strip()))
    assert not non_empty, (
        f".env.example GlitchTip secret/URL kljucevi imaju ne-prazne vrednosti: {non_empty}. "
        f"AC6/SM-D10: svi secret-i ostaju PRAZNI placeholderi (vrednost se daje kroz Hetzner "
        f"secrets / box .env, NIKAD u repo)."
    )


def test_ac6_glitchtip_email_url_key_not_bare_email_url():
    """# AC-6/G-16: GlitchTip email kanal koristi DISTINKTAN kljuc `GLITCHTIP_EMAIL_URL`
    (NE drugi bare `EMAIL_URL` — Django app vec ima `EMAIL_URL=consolemail://`)."""
    content = _read_file(ENV_EXAMPLE)
    # Mora postojati GLITCHTIP_EMAIL_URL (potvrdjeno gornjim testom); ovde: NE sme postojati
    # DRUGI bare EMAIL_URL= key (osim postojeceg Django consolemail jednog).
    bare_email_url_lines = [
        ln for ln in content.splitlines()
        if re.match(r"^\s*EMAIL_URL\s*=", ln) and not ln.lstrip().startswith("#")
    ]
    assert len(bare_email_url_lines) <= 1, (
        f".env.example ima vise od jedne bare `EMAIL_URL=` linije: {bare_email_url_lines}. "
        f"G-16: GlitchTip email kanal MORA biti `GLITCHTIP_EMAIL_URL=` (distinktan kljuc); "
        f"dupli `EMAIL_URL` = operator konfuzija. Compose mapira GLITCHTIP_EMAIL_URL u "
        f"GlitchTip interni EMAIL_URL."
    )


def test_ac6_sentry_traces_sample_rate_placeholder_present():
    """# AC-6: SENTRY_TRACES_SAMPLE_RATE placeholder/komentar prisutan (opciono override;
    SDK-tuning var zadrzava SENTRY_ prefiks, SM-D4)."""
    content = _read_file(ENV_EXAMPLE)
    assert re.search(r"SENTRY_TRACES_SAMPLE_RATE", content), (
        ".env.example nema `SENTRY_TRACES_SAMPLE_RATE` placeholder/komentar. "
        "AC6/SM-D4: opciono override (default 0.0); SDK-tuning var zadrzava SENTRY_ prefiks."
    )


# =============================================================================
# AC7 / AC9(f) — masinski-verifikabilan ~512MB mem limit na glitchtip web + retention
# =============================================================================


def test_ac7_glitchtip_web_declares_memory_limit_512m():
    """# AC-7/AC9(f): glitchtip web servis MORA deklarisati memory limit (~512m) kroz Compose
    konstrukt (deploy.resources.limits.memory ILI mem_limit) u RENDERED `docker compose config`.
    Slobodan `# ~512MB` komentar FAIL-uje (ne prezivi render). [docker-skip]."""
    data = _parsed_compose_config()
    glitchtip = data.get("services", {}).get("glitchtip")
    assert glitchtip is not None, (
        "compose/production.yml nema `glitchtip` web servis u rendered config-u (AC1 RED)."
    )
    mem_bytes = _glitchtip_web_mem_bytes(glitchtip)
    assert mem_bytes is not None, (
        "glitchtip web servis NE deklarise memory limit u rendered compose config-u. "
        "AC7/AC9(f)/Task 1.5: MORA `deploy.resources.limits.memory: 512m` ILI `mem_limit: 512m`. "
        "Slobodan `# ~512MB` komentar NE prolazi (ne prezivi `docker compose config` render).\n"
        f"glitchtip keys: {sorted(glitchtip.keys())}"
    )
    assert MEM_MIN_BYTES <= mem_bytes <= MEM_MAX_BYTES, (
        f"glitchtip web memory limit = {mem_bytes} bajtova (~{mem_bytes / 1024 / 1024:.0f}MiB), "
        f"van prihvatljivog ~512MB opsega [{MEM_MIN_BYTES}–{MEM_MAX_BYTES}] (400m–600m). "
        f"AC7/AR-19: kapiraj web na ~512m (epics.md:162 + architecture.md:221 budzet)."
    )


def test_ac7_retention_30_days_declared():
    """# AC-7: retention=30d deklarisan (`GLITCHTIP_MAX_EVENT_LIFE_DAYS=30`) u .env.example
    (disk guard na ~512MB box-u, G-11)."""
    content = _read_file(ENV_EXAMPLE)
    m = re.search(r"^\s*GLITCHTIP_MAX_EVENT_LIFE_DAYS\s*=\s*(\S+)", content, re.MULTILINE)
    assert m is not None, (
        ".env.example nema `GLITCHTIP_MAX_EVENT_LIFE_DAYS=` retention kljuc. "
        "AC7/G-11: event-i stariji od 30 dana se brisu (disk guard)."
    )
    assert m.group(1).strip() == "30", (
        f"GLITCHTIP_MAX_EVENT_LIFE_DAYS = {m.group(1)!r}, ocekivano '30'. "
        f"AC7: retention 30 dana (~512MB box disk guard)."
    )


@pytest.mark.parametrize(
    "service", ["glitchtip", "glitchtip-worker"], ids=["web", "worker"]
)
def test_ac7_retention_env_on_glitchtip_service(service):
    """# AC-7/Task 1.2: glitchtip (web+worker) servis MORA imati `GLITCHTIP_MAX_EVENT_LIFE_DAYS`
    u svom `environment:` bloku (interpoliran `${GLITCHTIP_MAX_EVENT_LIFE_DAYS:-30}`). Retention
    env na .env.example samom NE konfiguriše kontejner — servis mora primiti var. [docker-skip→raw]."""
    rendered = _rendered_glitchtip_env(service)
    if rendered is not None:
        assert "GLITCHTIP_MAX_EVENT_LIFE_DAYS" in rendered, (
            f"`{service}` servis nema `GLITCHTIP_MAX_EVENT_LIFE_DAYS` u rendered environment "
            f"bloku. AC7/Task 1.2: `GLITCHTIP_MAX_EVENT_LIFE_DAYS: ${{GLITCHTIP_MAX_EVENT_LIFE_DAYS:-30}}`. "
            f"Pronadjeni env kljucevi: {sorted(rendered.keys())}."
        )
        # default 30 mora preziveti interpolaciju (prazan env → `:-30` fallback = '30').
        val = rendered.get("GLITCHTIP_MAX_EVENT_LIFE_DAYS", "")
        assert val in ("30", ""), (
            f"`{service}` GLITCHTIP_MAX_EVENT_LIFE_DAYS rendered = {val!r}; ocekivano '30' "
            f"(`:-30` default) ili prazno (ako Dev ne stavi compose default). AC7."
        )
        return
    # Fallback: raw active-line grep da glitchtip blok pominje retention env.
    assert _glitchtip_block_active_mentions(r"GLITCHTIP_MAX_EVENT_LIFE_DAYS"), (
        "compose/production.yml glitchtip blok NE pominje `GLITCHTIP_MAX_EVENT_LIFE_DAYS` u "
        "AKTIVNOJ liniji (samo zakomentarisan placeholder). AC7/Task 1.2: retention env MORA "
        "biti na glitchtip servisu (`${GLITCHTIP_MAX_EVENT_LIFE_DAYS:-30}`)."
    )


# =============================================================================
# AC8 — email alerting kanal: glitchtip servis mapira EMAIL_URL iz GLITCHTIP_EMAIL_URL
# =============================================================================


def test_ac8_glitchtip_maps_email_url_from_distinct_key():
    """# AC-8/SM-D6/G-16: glitchtip servis mapira `EMAIL_URL: ${GLITCHTIP_EMAIL_URL:-}` —
    GlitchTip kontejner interno cita `EMAIL_URL`, ali .env.example kljuc je DISTINKTAN
    `GLITCHTIP_EMAIL_URL` (izbegava duplikat sa Django `EMAIL_URL=consolemail://`).

    Dve asercije (mirror SECRET_KEY dual pristup):
      (1) rendered glitchtip env MORA imati `EMAIL_URL` kljuc (interpolacija da '' sa praznim env-om je OK);
      (2) raw AKTIVNA linija MORA referencirati `${GLITCHTIP_EMAIL_URL` (dokaz da je izvor distinktan
          GLITCHTIP_ kljuc, NE goli EMAIL_URL/Django DJANGO secret). [docker-skip→raw]."""
    rendered = _rendered_glitchtip_env("glitchtip")
    if rendered is not None:
        assert "EMAIL_URL" in rendered, (
            "glitchtip web servis nema `EMAIL_URL` u rendered environment bloku. "
            "AC8/SM-D6: `EMAIL_URL: ${GLITCHTIP_EMAIL_URL:-}` (GlitchTip interni EMAIL_URL "
            f"mapiran iz distinktnog kljuca). Pronadjeni env kljucevi: {sorted(rendered.keys())}."
        )
    # Raw source: izvor MORA biti ${GLITCHTIP_EMAIL_URL (NE goli ${EMAIL_URL}/Django secret).
    assert _glitchtip_block_active_mentions(r"\$\{GLITCHTIP_EMAIL_URL"), (
        "compose/production.yml glitchtip blok NE mapira `EMAIL_URL: ${GLITCHTIP_EMAIL_URL...}` u "
        "AKTIVNOJ liniji (samo zakomentarisan placeholder). AC8/SM-D6/G-16: GlitchTip email kanal "
        "ide kroz distinktan GLITCHTIP_EMAIL_URL kljuc mapiran u GlitchTip interni EMAIL_URL "
        "(izbegava duplikat sa Django EMAIL_URL=consolemail://)."
    )


# =============================================================================
# depends_on hygiene (G-15) — glitchtip NE depends_on app postgres
# =============================================================================


@pytest.mark.parametrize(
    "service", ["glitchtip", "glitchtip-worker"], ids=["web", "worker"]
)
def test_g15_glitchtip_depends_on_excludes_app_postgres(service):
    """# AC-1/G-15/SM-D2: glitchtip (web+worker) `depends_on` ISKLJUCIVO svoje servise —
    NE app `postgres` (separate-DB mandat). [docker-skip]."""
    data = _parsed_compose_config()
    svc = data.get("services", {}).get(service)
    if svc is None:
        pytest.fail(
            f"compose/production.yml nema `{service}` servis (AC1 RED). G-15 depends_on "
            f"hygiene asercija ne moze da se izvrsi dok servis ne postoji."
        )
    deps = _depends_on_keys(svc)
    assert "postgres" not in deps, (
        f"`{service}` servis `depends_on` ukljucuje app `postgres`: {deps}. "
        f"G-15/SM-D2: zakomentarisan placeholder je imao `depends_on: - postgres` (APP DB) — "
        f"NE prenosi to. GlitchTip MORA depends_on samo glitchtip-postgres + glitchtip-redis."
    )
    # Pozitivno: bar jedan od sopstvenih servisa je u depends_on (sanity).
    assert any(d in deps for d in ("glitchtip-postgres", "glitchtip-redis")), (
        f"`{service}` `depends_on` ne pokazuje na sopstvene servise: {deps}. "
        f"SM-D2/Task 1.3: depends_on glitchtip-postgres + glitchtip-redis."
    )


# =============================================================================
# env_file hygiene (G-14) — glitchtip/worker NEMAJU env_file: ../.env
# =============================================================================


@pytest.mark.parametrize(
    "service", ["glitchtip", "glitchtip-worker"], ids=["web", "worker"]
)
def test_g14_glitchtip_has_no_app_env_file(service):
    """# AC-1/G-14: glitchtip (web+worker) NEMA `env_file: ../.env` (kopiranje django template-a
    bi procurilo Django secret-e — DJANGO_SECRET_KEY/ANYMAIL_RESEND_API_KEY — u GlitchTip
    kontejner). Samo django servis ima env_file. [docker-skip]."""
    data = _parsed_compose_config()
    svc = data.get("services", {}).get(service)
    if svc is None:
        pytest.fail(
            f"compose/production.yml nema `{service}` servis (AC1 RED). G-14 env_file hygiene "
            f"asercija ne moze da se izvrsi dok servis ne postoji."
        )
    env_file = svc.get("env_file")
    if env_file is None:
        return  # cist — nema env_file uopste
    if isinstance(env_file, str):
        values = [env_file]
    elif isinstance(env_file, list):
        values = [ef if isinstance(ef, str) else str(ef.get("path", "")) for ef in env_file]
    else:
        values = [str(env_file)]
    leaks = [v for v in values if ".env" in v]
    assert not leaks, (
        f"`{service}` servis ima `env_file` koji ukljucuje app .env: {leaks}. "
        f"G-14/Fix-2/SM-D10: glitchtip web+worker koriste SAMO inline `environment:` blok — "
        f"NIKAD `env_file: ../.env` (procureli bi Django secret-i u GlitchTip kontejner)."
    )


# =============================================================================
# image pin (SM-D11) — glitchtip image NIJE :latest
# =============================================================================


@pytest.mark.parametrize(
    "service", ["glitchtip", "glitchtip-worker"], ids=["web", "worker"]
)
def test_sm_d11_glitchtip_image_is_pinned_not_latest(service):
    """# AC-1/SM-D11: glitchtip (web+worker) image MORA biti pin-ovan na konkretan GlitchTip 6
    tag — NE `:latest` (mirror postgres:16-alpine determinizam). [docker-skip]."""
    data = _parsed_compose_config()
    svc = data.get("services", {}).get(service)
    if svc is None:
        pytest.fail(
            f"compose/production.yml nema `{service}` servis (AC1 RED). SM-D11 image-pin "
            f"asercija ne moze da se izvrsi dok servis ne postoji."
        )
    image = str(svc.get("image", ""))
    assert image, f"`{service}` servis nema `image:`. SM-D11/Task 1.1: pin-uj GlitchTip 6 tag."
    assert not image.endswith(":latest"), (
        f"`{service}` image = {image!r} koristi `:latest`. SM-D11/OQ-5: pin-uj na konkretan "
        f"GlitchTip 6 version tag (nedeterministicki `:latest` je ODLUCENO = NE koristi se)."
    )
    # Defenzivno: image MORA imati eksplicitan tag (`repo:tag`), ne untagged.
    assert ":" in image.rsplit("/", 1)[-1], (
        f"`{service}` image = {image!r} nema eksplicitan `:tag` (untagged = implicitni latest). "
        f"SM-D11: pin-uj konkretan GlitchTip 6 tag."
    )


# =============================================================================
# secrets hygiene (G-5/G-6) — ${...} interpolacija, distinktan SECRET_KEY, no real secrets
# =============================================================================


def test_security_no_inline_secrets_in_glitchtip_block():
    """# AC-1/G-5 SECURITY: raw compose/production.yml NE SME imati realan secret literal u
    glitchtip bloku — secret-i kroz `${...}` interpolaciju (mirror 9-1 test_no_inline_secrets)."""
    raw = _read_file(PRODUCTION_YML)
    suspicious = []
    for lineno, rawline in enumerate(raw.splitlines(), start=1):
        stripped = rawline.strip()
        if not stripped or stripped.startswith("#"):
            continue
        # Linije sa ${...} interpolacijom su OK (to je trazeni pattern).
        if "${" in stripped:
            continue
        for match in re.finditer(r"[A-Za-z0-9+/=_-]{30,}", stripped):
            token = match.group(0)
            if "coric_agrar" in token:  # named volume — nije secret
                continue
            # URL/image fragment (slash u blizini) — nije secret
            if "/" in stripped[max(0, match.start() - 3): match.end() + 3]:
                continue
            suspicious.append((lineno, stripped, token))
    assert not suspicious, (
        "compose/production.yml ima sumnjivo dugacke token-e u glitchtip kontekstu "
        "(potencijalni baked-in secret):\n"
        + "\n".join(f"  line {ln}: {raw!r} (token: {tok!r})" for ln, raw, tok in suspicious[:5])
        + "\nG-5/SM-D10: GlitchTip secret-i (SECRET_KEY, DB password, DSN) MORAJU kroz "
        "`${...}` env interpolaciju, NIKAD inline literal."
    )


def test_security_glitchtip_secret_key_uses_env_interpolation_distinct_from_django():
    """# AC-1/G-5/G-6: glitchtip web `SECRET_KEY` koristi `${GLITCHTIP_SECRET_KEY...}`
    interpolaciju (DISTINKTAN od Django DJANGO_SECRET_KEY). Citamo rendered env mapping; ako
    docker nedostaje, fallback na raw grep ${GLITCHTIP_SECRET_KEY}. [docker-skip→raw]."""
    docker = _docker_bin()
    if docker is not None and _yaml is not None and PRODUCTION_YML.exists():
        result = _run_compose_config(quiet=False)
        if result is not None and result.returncode == 0:
            data = _yaml.safe_load(result.stdout)
            glitchtip = data.get("services", {}).get("glitchtip")
            if glitchtip is not None:
                env_map = _service_env_map(glitchtip)
                assert "SECRET_KEY" in env_map, (
                    "glitchtip web servis nema `SECRET_KEY` u environment bloku. "
                    "Task 1.2: `SECRET_KEY: ${GLITCHTIP_SECRET_KEY:-}`."
                )
                # SECRET_KEY NE sme da bude Django secret. U rendered config-u sa praznim env-om
                # vrednost je prazna (interpolacija ${GLITCHTIP_SECRET_KEY:-} → ''); to je OK.
                assert "DJANGO_SECRET_KEY" not in str(env_map.get("SECRET_KEY", "")), (
                    "glitchtip SECRET_KEY referencira Django DJANGO_SECRET_KEY. G-6: distinktan "
                    "GLITCHTIP_SECRET_KEY (deljenje spaja crypto domene dve aplikacije)."
                )
                return
    # Fallback (docker/pyyaml nedostaje): raw grep na AKTIVNIM (non-comment) linijama da
    # glitchtip blok koristi GLITCHTIP_SECRET_KEY. Zakomentarisan 9.1 placeholder (koji vec
    # pominje ${GLITCHTIP_SECRET_KEY} u komentaru) NE sme lazno da zadovolji ovaj test.
    raw = _read_file(PRODUCTION_YML)
    active = "\n".join(ln for ln in raw.splitlines() if not ln.lstrip().startswith("#"))
    assert re.search(r"\$\{GLITCHTIP_SECRET_KEY", active), (
        "compose/production.yml glitchtip blok NE koristi `${GLITCHTIP_SECRET_KEY...}` "
        "interpolaciju u AKTIVNOJ liniji (samo zakomentarisan placeholder). G-5/G-6: GlitchTip "
        "SECRET_KEY je distinktan env var (NE Django DJANGO_SECRET_KEY), citan kroz env "
        "interpolaciju."
    )
