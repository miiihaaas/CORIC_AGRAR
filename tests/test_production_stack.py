"""Tests za Story 9.1 — Production Docker Compose + Nginx Config.

INFRA-VERIFY testovi (needs_e2e=false — NE Playwright/browser E2E). Deliverable-i
ove story-je su CONFIG fajlovi (compose/production.yml, compose/nginx/nginx.conf,
compose/nginx/Dockerfile, compose/django/start.sh, prod Dockerfile put,
production.py env-param) + 1 nova runtime dep (gunicorn) — NE Django app kod.

Pokrivenost po AC:
- AC1/AC3/AC6: `docker compose -f compose/production.yml config` exit-0 + parsed
  servisi (postgres/django/nginx) + named volumes + DJANGO_SETTINGS_MODULE +
  glitchtip placeholder + bez host port-a na django/postgres + bez `coric:coric`.
- AC2/AC4: nginx.conf grep-lock (proxy_pass django:8000, X-Forwarded-Proto,
  location /static/ + /media/, gzip on, 3× add_header ... always).
- AC5/SM-D2/G-10: start.sh (gunicorn config.wsgi:application, workers, --timeout,
  --bind, NE migrate, LF) + production.yml django `entrypoint: ["/start.sh"]`.
- AC7: gunicorn u pyproject [project].dependencies + uv.lock; 0 migracija.
- AC6/AC8/SM-D7: prod-settings import sanity (env-driven SECURE_SSL_REDIRECT +
  CSRF_TRUSTED_ORIGINS env.list + EXTEND verify Whitenoise/proxy/HSTS).
- AC3/AC4/AC8: MANDATORY runnable container smoke (@pytest.mark.docker) — diže
  pravi prod stack, collectstatic seed, curl -I → 200 + 3 headera, static → 200,
  down -v cleanup.

Pokrenuti sa:
    uv run pytest tests/test_production_stack.py -v
    uv run pytest tests/test_production_stack.py -v -m "not docker"   # bez smoke-a
    uv run pytest tests/test_production_stack.py -v -m docker          # samo smoke

TEA RED faza: svi non-smoke testovi MORAJU pasti dok Dev ne završi Story 9.1
(FileNotFoundError / pytest.fail / assertion / ImportError jer artefakti ne
postoje). Smoke (@pytest.mark.docker) može ERROR/FAIL/skip — to je OK u RED-u.

Naming convention: srpska latinica + engleski; bez ćirilice.
"""

from __future__ import annotations

import importlib
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

try:
    import yaml as _yaml  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover
    _yaml = None  # type: ignore[assignment]


# =============================================================================
# Konstante (project paths)
# =============================================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

COMPOSE_DIR = PROJECT_ROOT / "compose"
COMPOSE_DJANGO_DIR = COMPOSE_DIR / "django"
COMPOSE_NGINX_DIR = COMPOSE_DIR / "nginx"

PRODUCTION_YML = COMPOSE_DIR / "production.yml"
LOCAL_YML = COMPOSE_DIR / "local.yml"
NGINX_CONF = COMPOSE_NGINX_DIR / "nginx.conf"
NGINX_DOCKERFILE = COMPOSE_NGINX_DIR / "Dockerfile"
START_SH = COMPOSE_DJANGO_DIR / "start.sh"
ENTRYPOINT_SH = COMPOSE_DJANGO_DIR / "entrypoint.sh"

PYPROJECT = PROJECT_ROOT / "pyproject.toml"
UV_LOCK = PROJECT_ROOT / "uv.lock"
PRODUCTION_PY = PROJECT_ROOT / "config" / "settings" / "production.py"

# Test SECRET_KEY za import (NIJE realan secret — samo za test imports)
TEST_SECRET = "test-secret-key-for-tea-9-1-prod-stack-not-real"
TEST_DATABASE_URL = "postgres://coric:coric@localhost:5432/coric_agrar"


# =============================================================================
# Helper funkcije (mirror tests/test_docker_compose.py + test_settings_split.py)
# =============================================================================


def _read_file(path: Path) -> str:
    """Pročita text fajl. Fail-uje (RED signal) ako ne postoji."""
    if not path.exists():
        pytest.fail(f"Fajl ne postoji (Story 9.1 ga kreira): {path}")
    return path.read_text(encoding="utf-8")


def _read_binary(path: Path) -> bytes:
    if not path.exists():
        pytest.fail(f"Fajl ne postoji (Story 9.1 ga kreira): {path}")
    return path.read_bytes()


def _has_lf_only(path: Path) -> bool:
    """True ako fajl ima isključivo LF (\\n) — bez CRLF (\\r\\n) (G-1)."""
    return b"\r\n" not in _read_binary(path)


def _parse_yaml(path: Path) -> dict:
    """Parse YAML kroz pyyaml (transitivan dev dep). Skip ako pyyaml nedostaje."""
    if _yaml is None:
        pytest.skip(
            "pyyaml nije dostupan — `uv run pytest` ga ima transitivno kroz "
            "pre-commit. Ako baš nedostaje: `uv add --dev pyyaml`."
        )
    if not path.exists():
        pytest.fail(f"YAML fajl ne postoji (Story 9.1 ga kreira): {path}")
    with path.open("r", encoding="utf-8") as f:
        return _yaml.safe_load(f)


def _docker_bin() -> str | None:
    return shutil.which("docker")


def _run_compose_config(
    yml_path: Path, extra: list[str] | None = None
) -> subprocess.CompletedProcess | None:
    """`docker compose -f <yml> config [extra]`. None ako docker nije na PATH-u."""
    docker = _docker_bin()
    if docker is None:
        return None
    cmd = [docker, "compose", "-f", str(yml_path), "config"]
    if extra:
        cmd += extra
    return subprocess.run(
        cmd,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        shell=False,
        timeout=120,
    )


def _parsed_compose_config(yml_path: Path) -> dict:
    """Vrati PARSIRAN (interpoliran) compose config kao dict.

    `docker compose config` resolve-uje env_file/interpolaciju → pouzdaniji od
    sirovog YAML parse-a za env asercije. Skip ako docker ili pyyaml nedostaju.
    """
    if not yml_path.exists():
        pytest.fail(f"{yml_path} ne postoji (Story 9.1 ga kreira).")
    result = _run_compose_config(yml_path)
    if result is None:
        pytest.skip("docker CLI nije na PATH-u — preskačem parsed compose config.")
    if result.returncode != 0:
        pytest.fail(
            f"`docker compose -f {yml_path.name} config` exit {result.returncode}.\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
    if _yaml is None:
        pytest.skip("pyyaml nedostaje — ne mogu da parsiram compose config output.")
    return _yaml.safe_load(result.stdout)


def _load_production_settings(extra_env: dict[str, str]):
    """Importuje `config.settings.production` sa kontrolisanim env-om.

    Mirror test_settings_split._load_settings_module: čisti config.settings.*
    iz sys.modules (zbog `from .base import *`) pa reload. extra_env se aplicira
    na os.environ PRE import-a; caller restore-uje (vidi _settings_env fixture).
    """
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    for k, v in extra_env.items():
        os.environ[k] = v
    for mod_key in list(sys.modules.keys()):
        if mod_key.startswith("config.settings"):
            del sys.modules[mod_key]
    return importlib.import_module("config.settings.production")


@pytest.fixture
def settings_env():
    """Kontekst-menadžer fixture: postavi env vars, vrati loader, restore na kraju.

    Snapshot-uje relevantne env vars, dozvoljava testu da load-uje production
    settings sa proizvoljnim env-om, pa restore-uje originalni os.environ state
    (i sys.modules cache za config.settings.*).
    """
    tracked = [
        "DJANGO_SECRET_KEY",
        "DJANGO_ALLOWED_HOSTS",
        "DATABASE_URL",
        "DJANGO_SECURE_SSL_REDIRECT",
        "DJANGO_CSRF_TRUSTED_ORIGINS",
        "DJANGO_DEBUG",
    ]
    snapshot = {k: os.environ.get(k) for k in tracked}
    # `.env` u repo-u može da injektuje vrednosti kroz environ.Env.read_env;
    # privremeno ga sklonimo da test kontroliše env deterministički.
    env_file = PROJECT_ROOT / ".env"
    env_backup = PROJECT_ROOT / ".env.tea-9-1-backup-tmp"
    moved = False
    if env_file.exists():
        env_file.rename(env_backup)
        moved = True

    def _loader(extra_env: dict[str, str]):
        base = {
            "DJANGO_SECRET_KEY": TEST_SECRET,
            "DJANGO_ALLOWED_HOSTS": "localhost",
            "DATABASE_URL": TEST_DATABASE_URL,
        }
        base.update(extra_env)
        return _load_production_settings(base)

    try:
        yield _loader
    finally:
        for k, v in snapshot.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        for mod_key in list(sys.modules.keys()):
            if mod_key.startswith("config.settings"):
                del sys.modules[mod_key]
        if moved and env_backup.exists():
            env_backup.rename(env_file)


# =============================================================================
# AC1 / AC3 / AC6 — compose/production.yml config lint + parsed asercije
# =============================================================================


def test_ac1_production_yml_exists():
    """AC1: `compose/production.yml` MORA postojati."""
    assert PRODUCTION_YML.exists(), (
        f"compose/production.yml ne postoji na {PRODUCTION_YML}. "
        f"Story 9.1 Task 4 ga kreira (mirror compose/local.yml struktura)."
    )


def test_ac1_production_yml_config_exit_zero():
    """AC1/AC3: `docker compose -f compose/production.yml config` exit 0 (validan).

    Static schema/reference validacija — NE diže kontejnere. Skip ako docker
    nije na PATH-u.
    """
    if not PRODUCTION_YML.exists():
        pytest.fail("compose/production.yml ne postoji (Story 9.1 Task 4).")
    result = _run_compose_config(PRODUCTION_YML, extra=["--quiet"])
    if result is None:
        pytest.skip("docker CLI nije na PATH-u — preskačem config validaciju.")
    assert result.returncode == 0, (
        f"`docker compose -f compose/production.yml config` exit {result.returncode}.\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}\n"
        f"Verovatno YAML schema greška, nedeklarisan volume (media!), ili "
        f"pogrešna build/env_file referenca."
    )


def test_ac1_production_has_postgres_django_nginx_services():
    """AC1/AC3: parsed compose config MORA imati postgres + django + nginx servise."""
    data = _parsed_compose_config(PRODUCTION_YML)
    services = data.get("services", {})
    assert isinstance(services, dict), (
        f"compose/production.yml `services:` nije mapping: {type(services)}"
    )
    missing = [s for s in ("postgres", "django", "nginx") if s not in services]
    assert not missing, (
        f"compose/production.yml nedostaju servisi: {missing}. "
        f"Pronađeno: {list(services.keys())}. "
        f"AC1 zahteva postgres + django (Gunicorn) + nginx."
    )


def test_ac1_glitchtip_is_not_active_service():
    """AC1: `glitchtip` je PLACEHOLDER/zakomentarisan — NE aktivan parsiran servis.

    epics:1190 „glitchtip (Epic 9.3)" → 9.1 sme samo zakomentarisan placeholder.
    `docker compose config` ne sme da ga prikaže kao aktivan servis.
    """
    data = _parsed_compose_config(PRODUCTION_YML)
    services = data.get("services", {})
    assert "glitchtip" not in services, (
        "compose/production.yml ima AKTIVAN `glitchtip` servis u parsed config-u. "
        "SM-D4: GlitchTip realno wiring je Epic 9.3 — u 9.1 MORA biti zakomentarisan "
        "placeholder (sa `# Epic 9.3` markerom), NE aktivan servis."
    )
    # Defenzivno: raw fajl bi trebalo da pomene glitchtip u komentaru (placeholder marker).
    raw = _read_file(PRODUCTION_YML)
    assert "glitchtip" in raw.lower(), (
        "compose/production.yml uopšte ne pominje glitchtip. AC1/Task 4.4 traži "
        "ZAKOMENTARISAN placeholder blok sa `# Epic 9.3` markerom."
    )


def test_ac6_django_env_has_production_settings_module():
    """AC6: django servis env MORA imati DJANGO_SETTINGS_MODULE=config.settings.production."""
    data = _parsed_compose_config(PRODUCTION_YML)
    django = data.get("services", {}).get("django", {})
    environment = django.get("environment", {})
    # parsed config normalizuje environment u mapping
    if isinstance(environment, list):
        env_map = {}
        for item in environment:
            if isinstance(item, str) and "=" in item:
                k, _, v = item.partition("=")
                env_map[k] = v
        environment = env_map
    assert environment.get("DJANGO_SETTINGS_MODULE") == "config.settings.production", (
        f"django servis DJANGO_SETTINGS_MODULE = "
        f"{environment.get('DJANGO_SETTINGS_MODULE')!r}, očekivano "
        f"'config.settings.production' (AC6). Prod NE sme da se oslanja na "
        f"manage.py default (development)."
    )


def test_ac1_named_volumes_declared():
    """AC1/Task 4.5: top-level volumes MORA deklarisati postgres_data + staticfiles + media.

    `media` MORA biti deklarisan jer nginx `location /media/` referencira mount —
    bez deklaracije `docker compose config` baca grešku za referenciran-nedeklarisan
    volume.
    """
    data = _parsed_compose_config(PRODUCTION_YML)
    volumes = data.get("volumes", {})
    assert isinstance(volumes, dict), (
        f"compose/production.yml top-level `volumes:` nije mapping: {type(volumes)}"
    )
    missing = [
        v for v in ("postgres_data", "staticfiles", "media") if v not in volumes
    ]
    assert not missing, (
        f"compose/production.yml nedostaju named volume-i: {missing}. "
        f"Pronađeno: {list(volumes.keys())}. "
        f"AC1/Task 4.5: postgres_data + staticfiles (django↔nginx) + media."
    )


def test_ac1_django_and_postgres_have_no_published_host_port():
    """AC1: django i postgres NE smeju da publish-uju host port (nginx je jedini ulaz).

    Prod razlika od local.yml: django nema `8000:8000`, postgres nema host port —
    samo interni Docker DNS. Nginx je jedini izložen (publishes 80).
    """
    data = _parsed_compose_config(PRODUCTION_YML)
    services = data.get("services", {})
    for svc in ("django", "postgres"):
        ports = services.get(svc, {}).get("ports", [])
        # parsed config: ports je lista (string `host:container` ili long-form dict
        # sa `published` ključem). published host port = leak.
        published = []
        for p in ports or []:
            if isinstance(p, dict):
                if p.get("published"):
                    published.append(p)
            elif isinstance(p, str):
                # "8000:8000" / "127.0.0.1:8000:8000" → ima host port
                if ":" in p:
                    published.append(p)
        assert not published, (
            f"`{svc}` servis publish-uje host port: {published}. "
            f"AC1: prod NE izlaže django/postgres na host (samo nginx publishes 80). "
            f"Ukloni `ports:` sa {svc} (interni Docker DNS je dovoljan)."
        )


def test_ac1_nginx_publishes_port_80():
    """AC1/AC3: nginx servis MORA publish-ovati port 80 (jedini izložen ulaz)."""
    data = _parsed_compose_config(PRODUCTION_YML)
    nginx = data.get("services", {}).get("nginx", {})
    ports = nginx.get("ports", [])
    blob = []
    for p in ports or []:
        if isinstance(p, dict):
            blob.append(str(p.get("published", "")) + ":" + str(p.get("target", "")))
        else:
            blob.append(str(p))
    joined = " ".join(blob)
    assert re.search(r"(^|\D)80(\D|$)", joined), (
        f"nginx servis ne publish-uje port 80. Pronađeno ports: {ports}. "
        f"AC1/AC3: nginx je jedini izložen ulaz (`ports: \"80:80\"`)."
    )


def test_g5_no_inline_coric_coric_credentials():
    """AC1/G-5 SECURITY: production.yml NE SME hardkodovan `coric:coric` / inline DB password.

    local.yml ima `POSTGRES_PASSWORD: coric` INLINE (LOCAL ONLY). Kopiranje u prod
    = security leak. Prod credentials kroz env_file/secrets.
    """
    raw = _read_file(PRODUCTION_YML)
    # Negativni grep: inline POSTGRES_PASSWORD: coric (bez interpolacije ${...})
    bad_inline_pw = re.search(
        r"^\s*POSTGRES_PASSWORD\s*:\s*coric\s*$", raw, re.MULTILINE
    )
    assert not bad_inline_pw, (
        "compose/production.yml ima INLINE `POSTGRES_PASSWORD: coric` (kopirano iz "
        "local.yml). G-5: prod credentials MORAJU kroz env_file/secrets, NIKAD "
        "hardkodovan password. Koristi `${POSTGRES_PASSWORD}` ili env_file."
    )
    # Negativni grep: `coric:coric@` (inline DATABASE_URL sa hardkodovanim creds)
    bad_dburl = re.search(r"coric:coric@", raw)
    assert not bad_dburl, (
        "compose/production.yml ima inline `coric:coric@` (hardkodovan DATABASE_URL "
        "credentials). G-5: secrets kroz env_file/secrets, ne inline."
    )


# =============================================================================
# AC2 / AC4 — nginx.conf grep-lock
# =============================================================================


def test_ac2_nginx_conf_exists():
    """AC2: `compose/nginx/nginx.conf` MORA postojati."""
    assert NGINX_CONF.exists(), (
        f"compose/nginx/nginx.conf ne postoji na {NGINX_CONF}. "
        f"Story 9.1 Task 3.2 ga kreira."
    )


def test_ac2_nginx_dockerfile_exists():
    """AC2/Task 3.1: `compose/nginx/Dockerfile` MORA postojati (nginx:alpine + COPY nginx.conf)."""
    assert NGINX_DOCKERFILE.exists(), (
        f"compose/nginx/Dockerfile ne postoji na {NGINX_DOCKERFILE}. "
        f"Story 9.1 Task 3.1: `nginx:1.27-alpine` + COPY nginx.conf."
    )
    content = _read_file(NGINX_DOCKERFILE)
    assert re.search(r"FROM\s+nginx:[\w.\-]+", content, re.IGNORECASE), (
        "compose/nginx/Dockerfile nema `FROM nginx:...` baznu sliku. "
        "Task 3.1: `FROM nginx:1.27-alpine` (ili stable)."
    )


def test_ac2_nginx_proxy_pass_to_django_8000():
    """AC2/AC4: nginx.conf MORA proxy-ovati na django:8000 (Docker DNS ime servisa)."""
    content = _read_file(NGINX_CONF)
    # Prihvati `upstream django { server django:8000; }` ILI direktan `proxy_pass`.
    upstream = re.search(r"upstream\s+django\b", content) and re.search(
        r"server\s+django:8000", content
    )
    direct = re.search(r"proxy_pass\s+http://django(:8000)?\b", content)
    assert upstream or direct, (
        "nginx.conf ne proxy-uje na `django:8000`. AC2/AC4: ili "
        "`upstream django { server django:8000; }` + `proxy_pass http://django` "
        "ili direktan `proxy_pass http://django:8000`."
    )


def test_ac2_nginx_forwards_x_forwarded_proto():
    """AC2/G-3 KRITIČNO: nginx.conf MORA `proxy_set_header X-Forwarded-Proto $scheme`.

    Bez ovoga production.py SECURE_PROXY_SSL_HEADER + SECURE_SSL_REDIRECT → beskonačan
    301 redirect loop.
    """
    content = _read_file(NGINX_CONF)
    pattern = r"proxy_set_header\s+X-Forwarded-Proto\s+\$scheme\s*;"
    assert re.search(pattern, content), (
        "nginx.conf ne sadrži `proxy_set_header X-Forwarded-Proto $scheme;`. "
        "G-3: bez ovoga Django misli da je request HTTP → SECURE_SSL_REDIRECT → "
        "beskonačan 301 loop."
    )


def test_ac4_nginx_serves_static_directly():
    """AC4: nginx.conf MORA imati `location /static/` blok (direktan static serving)."""
    content = _read_file(NGINX_CONF)
    assert re.search(r"location\s+/static/", content), (
        "nginx.conf nema `location /static/` blok. AC4: Nginx servira static "
        "direktno iz staticfiles volume-a (NE proxy na Django)."
    )


def test_ac4_nginx_serves_media_directly():
    """AC4/Task 3.2: nginx.conf MORA imati `location /media/` blok."""
    content = _read_file(NGINX_CONF)
    assert re.search(r"location\s+/media/", content), (
        "nginx.conf nema `location /media/` blok. Task 3.2: direktan media serving."
    )


def test_ac2_nginx_gzip_on():
    """AC2: nginx.conf MORA imati `gzip on;`."""
    content = _read_file(NGINX_CONF)
    assert re.search(r"^\s*gzip\s+on\s*;", content, re.MULTILINE), (
        "nginx.conf ne sadrži `gzip on;`. AC2: gzip kompresija obavezna."
    )


def test_ac2_nginx_three_security_headers_with_always():
    """AC2/G-7: nginx.conf MORA emitovati 3 security headera, SVAKI sa `always` flagom.

    `always` emituje header i na 4xx/5xx (ne samo 2xx). Vrednosti usaglašene sa
    production.py: DENY / nosniff / same-origin.
    """
    content = _read_file(NGINX_CONF)
    expected = {
        "X-Frame-Options": r'add_header\s+X-Frame-Options\s+["\']?DENY["\']?\s+always\s*;',
        "X-Content-Type-Options": r'add_header\s+X-Content-Type-Options\s+["\']?nosniff["\']?\s+always\s*;',
        "Referrer-Policy": r'add_header\s+Referrer-Policy\s+["\']?same-origin["\']?\s+always\s*;',
    }
    missing = [name for name, pat in expected.items() if not re.search(pat, content)]
    assert not missing, (
        f"nginx.conf nedostaju security headeri (sa `always` flagom): {missing}. "
        f"AC2/G-7: sva 3 — `add_header X-Frame-Options \"DENY\" always;`, "
        f"`add_header X-Content-Type-Options \"nosniff\" always;`, "
        f"`add_header Referrer-Policy \"same-origin\" always;`."
    )


# =============================================================================
# AC5 / SM-D2 / G-10 — start.sh + production.yml entrypoint wiring
# =============================================================================


def test_ac5_start_sh_exists():
    """AC5/Task 2.1: `compose/django/start.sh` MORA postojati."""
    assert START_SH.exists(), (
        f"compose/django/start.sh ne postoji na {START_SH}. "
        f"Story 9.1 Task 2.1 ga kreira (wait-for-db + exec gunicorn; BEZ migrate)."
    )


def test_ac5_start_sh_lf_line_endings():
    """AC5/G-1: start.sh MORA imati LF line endings (NE CRLF).

    Bash u Linux kontejneru ne tolerira CRLF → `exec format error`/bad interpreter.
    """
    if not START_SH.exists():
        pytest.fail("compose/django/start.sh ne postoji (Story 9.1 Task 2.1).")
    assert _has_lf_only(START_SH), (
        "compose/django/start.sh ima CRLF line endings (\\r\\n pronađeno). "
        "G-1: bash u Linux kontejneru crash-uje. Konvertuj u LF (VS Code CRLF→LF / "
        "dos2unix / .gitattributes `*.sh text eol=lf`)."
    )


def test_ac5_start_sh_runs_gunicorn_wsgi():
    """AC5/SM-D2: start.sh MORA pokretati `gunicorn config.wsgi:application`."""
    content = _read_file(START_SH)
    assert re.search(r"gunicorn\s+[^\n]*config\.wsgi:application", content), (
        "start.sh ne pokreće `gunicorn config.wsgi:application`. "
        "AC5/Task 2.1: `exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 ...`."
    )


def test_ac5_start_sh_has_bind_workers_timeout():
    """AC5: start.sh MORA imati `--bind 0.0.0.0:8000` + workers + `--timeout`.

    Workers: `--workers ${WEB_CONCURRENCY:-5}` ILI `WEB_CONCURRENCY` env ILI literal 5
    (2*CPU+1 za 2vCPU). Timeout eksplicitan (npr. 60s).
    """
    content = _read_file(START_SH)
    assert re.search(r"--bind\s+0\.0\.0\.0:8000", content), (
        "start.sh nema `--bind 0.0.0.0:8000`. AC5: Gunicorn mora slušati na svim "
        "interfejsima port 8000 (Nginx proxy target)."
    )
    workers_ok = (
        re.search(r"--workers\s+", content)
        or "WEB_CONCURRENCY" in content
    )
    assert workers_ok, (
        "start.sh nema workers konfiguraciju (`--workers ...` ili `WEB_CONCURRENCY`). "
        "AC5: `2*CPU+1=5` za 2vCPU (env-parametrizovano, default 5)."
    )
    assert re.search(r"--timeout\s+", content), (
        "start.sh nema `--timeout` flag. AC5: eksplicitan Gunicorn timeout (npr. 60s)."
    )


def test_ac5_start_sh_workers_formula_documented():
    """AC5: start.sh komentar MORA dokumentovati `2*CPU+1` formulu / vrednost 5 za 2vCPU."""
    content = _read_file(START_SH)
    # Tolerantno: `2*CPU+1`, `2 * CPU + 1`, `2*vCPU+1`, ili pomen `2 vCPU`/`2-vCPU`/`2vCPU`.
    formula = re.search(r"2\s*\*\s*(v?CPU|cpu)\s*\+\s*1", content, re.IGNORECASE) or re.search(
        r"2[\s\-]*v?CPU", content, re.IGNORECASE
    )
    assert formula, (
        "start.sh ne dokumentuje workers formulu (`2*CPU+1=5` za 2vCPU). "
        "AC5: komentar sa formulom je obavezan."
    )


def test_ac5_start_sh_does_not_migrate():
    """AC5/SM-D2/G-6/project-context:478 NEGATIVE: start.sh NE SME pokretati `migrate`.

    Migrate je deploy-step (9.2), NE app-startup. Prod start.sh samo wait-for-db +
    gunicorn.
    """
    content = _read_file(START_SH)
    # Tražimo `manage.py migrate` (ne npr. komentar koji pominje migrate).
    non_comment = "\n".join(
        ln for ln in content.splitlines() if not ln.lstrip().startswith("#")
    )
    assert not re.search(r"manage\.py\s+migrate", non_comment), (
        "compose/django/start.sh poziva `manage.py migrate` u izvršnoj liniji. "
        "G-6/project-context:478: migrate je deploy-time (Story 9.2), NE app-startup. "
        "Prod start.sh = SAMO wait-for-db + exec gunicorn."
    )


def test_g10_production_yml_django_uses_entrypoint_not_command_only():
    """AC5/SM-D2/G-10: production.yml django servis MORA imati `entrypoint:` → /start.sh.

    Dockerfile ENTRYPOINT je `/entrypoint.sh` (koji migrate-uje). `command:`-only
    override NE menja ENTRYPOINT → migrate i dalje radi → krši project-context:478.
    Zato MORA `entrypoint: ["/start.sh"]` (zameni ceo ENTRYPOINT).
    """
    data = _parsed_compose_config(PRODUCTION_YML)
    django = data.get("services", {}).get("django", {})
    entrypoint = django.get("entrypoint")
    assert entrypoint is not None, (
        "production.yml django servis NEMA `entrypoint:`. G-10: `command:`-only "
        "override NE menja Dockerfile ENTRYPOINT (entrypoint.sh-migrate i dalje radi). "
        "MORA `entrypoint: [\"/start.sh\"]`."
    )
    # entrypoint može biti string ili lista — normalizuj u string blob.
    if isinstance(entrypoint, list):
        ep_blob = " ".join(str(x) for x in entrypoint)
    else:
        ep_blob = str(entrypoint)
    assert "start.sh" in ep_blob, (
        f"production.yml django `entrypoint:` ne pokazuje na start.sh. "
        f"Dobijeno: {entrypoint!r}. G-10/Task 2.2: `entrypoint: [\"/start.sh\"]`."
    )


# =============================================================================
# AC7 — gunicorn dep + 0 migracija
# =============================================================================


def test_ac7_gunicorn_in_project_dependencies():
    """AC7/SM-D1: `gunicorn` u pyproject.toml [project].dependencies (NE dev grupa).

    Runtime WSGI server — mora u prod `--no-dev` venv. NE [dependency-groups].dev.
    """
    content = _read_file(PYPROJECT)
    # Izvuci [project].dependencies blok (do sledeće `[` sekcije na početku linije).
    proj_match = re.search(
        r"^\[project\]\s*\n(.*?)(?=^\[)", content, re.MULTILINE | re.DOTALL
    )
    assert proj_match, "pyproject.toml nema [project] sekciju (neočekivano)."
    proj_block = proj_match.group(1)
    deps_match = re.search(
        r"dependencies\s*=\s*\[(.*?)\]", proj_block, re.DOTALL
    )
    assert deps_match, "pyproject.toml [project].dependencies blok nije pronađen."
    deps_blob = deps_match.group(1)
    assert re.search(r"['\"]gunicorn[>=~]", deps_blob), (
        "pyproject.toml [project].dependencies NEMA `gunicorn`. "
        "AC7/SM-D1: dodaj `gunicorn>=23.0` u runtime deps (NE [dependency-groups].dev — "
        "runtime WSGI server mora u prod --no-dev venv)."
    )
    # Verzija >=23 (izbegava CVE-2024-1135 u <22)
    assert re.search(r"['\"]gunicorn>=2[3-9]", deps_blob), (
        "pyproject.toml gunicorn verzija nije `>=23` (SM-D1: 23.x stabilan + bez "
        "request-smuggling CVE). Dobijeni deps blob: " + deps_blob.strip()
    )


def test_ac7_gunicorn_not_in_dev_group():
    """AC7 NEGATIVE: gunicorn NE SME biti u [dependency-groups].dev."""
    content = _read_file(PYPROJECT)
    dev_match = re.search(
        r"^\[dependency-groups\]\s*\n(.*?)(?=^\[|\Z)",
        content,
        re.MULTILINE | re.DOTALL,
    )
    if dev_match:
        dev_blob = dev_match.group(1)
        assert "gunicorn" not in dev_blob, (
            "gunicorn je u [dependency-groups].dev — pogrešna grupa (runtime WSGI "
            "mora u [project].dependencies da uđe u prod --no-dev venv). SM-D1."
        )


def test_ac7_gunicorn_in_uv_lock():
    """AC7: `gunicorn` MORA biti u uv.lock (regenerisan posle `uv add gunicorn`)."""
    content = _read_file(UV_LOCK)
    assert re.search(r'name\s*=\s*"gunicorn"', content), (
        "uv.lock NEMA gunicorn paket. AC7/Task 1.1: posle `uv add gunicorn` "
        "regeneriši lock (`uv lock`). Verifikuj `gunicorn` u uv.lock."
    )


def test_ac7_zero_new_migrations():
    """AC7: `makemigrations --check` = No changes (9.1 ne dira modele → 0 migracija).

    Pokreće makemigrations --check --dry-run kroz dev settings. Skip ako uv nije
    na PATH-u. Exit 0 = nema pending migracija.
    """
    uv_bin = shutil.which("uv")
    if uv_bin is None:
        pytest.skip("uv binary nije u PATH-u — preskačem makemigrations --check.")
    result = subprocess.run(
        [
            uv_bin,
            "run",
            "python",
            "manage.py",
            "makemigrations",
            "--check",
            "--dry-run",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        shell=False,
        timeout=180,
        env={**os.environ, "DJANGO_SECRET_KEY": TEST_SECRET},
    )
    assert result.returncode == 0, (
        f"`makemigrations --check` exit {result.returncode} (pending migracije!). "
        f"AC7: 9.1 NE dira modele → 0 migracija očekivano.\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )


# =============================================================================
# AC6 / AC8 / SM-D7 — production.py prod-settings import sanity
# =============================================================================


def test_ac6_production_settings_import_succeeds(settings_env):
    """AC6/AC8: production settings se importuju bez greške sa smoke env-om."""
    prod = settings_env(
        {
            "DJANGO_SECURE_SSL_REDIRECT": "False",
            "DJANGO_CSRF_TRUSTED_ORIGINS": "http://localhost",
        }
    )
    assert prod.DEBUG is False, (
        f"production.DEBUG = {prod.DEBUG!r}, očekivano False (defense-in-depth)."
    )


def test_sm_d7_secure_ssl_redirect_is_env_driven_false(settings_env):
    """SM-D7/OQ-3: sa DJANGO_SECURE_SSL_REDIRECT=False → settings.SECURE_SSL_REDIRECT is False.

    Trenutno production.py:14 ima hardkodovan `SECURE_SSL_REDIRECT = True` → ovaj
    test PADA dok Dev ne env-parametrizuje (Task 5.1). Bez ovoga lokalni HTTP smoke
    daje 301 (G-11).
    """
    prod = settings_env({"DJANGO_SECURE_SSL_REDIRECT": "False"})
    assert prod.SECURE_SSL_REDIRECT is False, (
        f"production.SECURE_SSL_REDIRECT = {prod.SECURE_SSL_REDIRECT!r} sa "
        f"DJANGO_SECURE_SSL_REDIRECT=False u env-u. SM-D7/Task 5.1: zameni "
        f"hardkodovan `SECURE_SSL_REDIRECT = True` sa "
        f"`env.bool('DJANGO_SECURE_SSL_REDIRECT', default=True)`. Bez ovoga "
        f"lokalni HTTP smoke daje 301 (G-11), ne 200."
    )


def test_sm_d7_secure_ssl_redirect_defaults_true(settings_env):
    """SM-D7: BEZ DJANGO_SECURE_SSL_REDIRECT env vara → default True (prod hardening očuvan)."""
    # Eksplicitno ukloni var iz okruženja pre load-a (fixture restore-uje posle).
    os.environ.pop("DJANGO_SECURE_SSL_REDIRECT", None)
    prod = settings_env({})
    assert prod.SECURE_SSL_REDIRECT is True, (
        f"production.SECURE_SSL_REDIRECT = {prod.SECURE_SSL_REDIRECT!r} BEZ env var-a. "
        f"SM-D7: default MORA biti True (env.bool(..., default=True)) — prod hardening "
        f"se ne sme oslabiti."
    )


def test_sm_d7_csrf_trusted_origins_env_list(settings_env):
    """SM-D7/G-9: sa DJANGO_CSRF_TRUSTED_ORIGINS=http://localhost → CSRF_TRUSTED_ORIGINS == ['http://localhost'].

    Trenutno production.py NEMA CSRF_TRUSTED_ORIGINS → ovaj test PADA (AttributeError
    ili default []) dok Dev ne doda (Task 5.1b). Bez ovoga 403 na svaki cross-origin POST.
    """
    prod = settings_env({"DJANGO_CSRF_TRUSTED_ORIGINS": "http://localhost"})
    assert hasattr(prod, "CSRF_TRUSTED_ORIGINS"), (
        "production.py NEMA `CSRF_TRUSTED_ORIGINS`. SM-D7/G-9/Task 5.1b: dodaj "
        "`CSRF_TRUSTED_ORIGINS = env.list('DJANGO_CSRF_TRUSTED_ORIGINS', default=[])`. "
        "Bez ovoga Django 4+ vraća 403 na svaki cross-origin POST (admin login, lead forme)."
    )
    assert prod.CSRF_TRUSTED_ORIGINS == ["http://localhost"], (
        f"production.CSRF_TRUSTED_ORIGINS = {prod.CSRF_TRUSTED_ORIGINS!r}, "
        f"očekivano ['http://localhost'] (env.list parse). Task 5.1b."
    )


def test_sm_d7_csrf_trusted_origins_defaults_empty(settings_env):
    """SM-D7: BEZ DJANGO_CSRF_TRUSTED_ORIGINS env vara → default [] (env.list default)."""
    os.environ.pop("DJANGO_CSRF_TRUSTED_ORIGINS", None)
    prod = settings_env({})
    assert hasattr(prod, "CSRF_TRUSTED_ORIGINS"), (
        "production.py NEMA `CSRF_TRUSTED_ORIGINS` (Task 5.1b)."
    )
    assert prod.CSRF_TRUSTED_ORIGINS == [], (
        f"production.CSRF_TRUSTED_ORIGINS = {prod.CSRF_TRUSTED_ORIGINS!r} bez env-a, "
        f"očekivano [] (env.list default)."
    )


def test_ac8_production_hardening_preserved_extend_not_overwrite(settings_env):
    """AC8/SM-D7: izmene su EXTEND — postojeći HTTPS hardening NETAKNUT.

    Whitenoise manifest storage, SECURE_PROXY_SSL_HEADER, HSTS, X_FRAME_OPTIONS,
    SECURE_REFERRER_POLICY i dalje prisutni (Dev NE sme da ih prepiše).
    """
    prod = settings_env(
        {
            "DJANGO_SECURE_SSL_REDIRECT": "False",
            "DJANGO_CSRF_TRUSTED_ORIGINS": "http://localhost",
        }
    )
    # SECURE_PROXY_SSL_HEADER netaknut (KLJUČAN za Nginx→Gunicorn proxy)
    assert prod.SECURE_PROXY_SSL_HEADER == ("HTTP_X_FORWARDED_PROTO", "https"), (
        f"production.SECURE_PROXY_SSL_HEADER = {prod.SECURE_PROXY_SSL_HEADER!r}, "
        f"očekivano ('HTTP_X_FORWARDED_PROTO', 'https'). EXTEND — ne prepisuj."
    )
    # Whitenoise manifest storage netaknut
    staticfiles_backend = prod.STORAGES["staticfiles"]["BACKEND"]
    assert "whitenoise" in staticfiles_backend.lower(), (
        f"production.STORAGES['staticfiles']['BACKEND'] = {staticfiles_backend!r}, "
        f"očekivano Whitenoise CompressedManifestStaticFilesStorage. EXTEND — ne prepisuj."
    )
    # HSTS + headeri netaknuti
    assert prod.SECURE_HSTS_SECONDS >= 31536000, (
        f"production.SECURE_HSTS_SECONDS = {prod.SECURE_HSTS_SECONDS}, očekivano "
        f">= 31536000 (1y). EXTEND — HSTS ne sme oslabiti."
    )
    assert prod.X_FRAME_OPTIONS == "DENY", (
        f"production.X_FRAME_OPTIONS = {prod.X_FRAME_OPTIONS!r}, očekivano 'DENY'."
    )
    assert prod.SECURE_REFERRER_POLICY == "same-origin", (
        f"production.SECURE_REFERRER_POLICY = {prod.SECURE_REFERRER_POLICY!r}, "
        f"očekivano 'same-origin'."
    )


# =============================================================================
# AC7 / AC8 — regresija: lokalni dev stack NETAKNUT
# =============================================================================


def test_regression_local_yml_still_valid():
    """AC7/AC8 regresija: compose/local.yml config i dalje validan (9.1 ga NE dira)."""
    if not LOCAL_YML.exists():
        pytest.fail("compose/local.yml ne postoji (regresija — Story 1.3 baseline).")
    result = _run_compose_config(LOCAL_YML, extra=["--quiet"])
    if result is None:
        pytest.skip("docker CLI nije na PATH-u — preskačem local.yml regresiju.")
    assert result.returncode == 0, (
        f"`docker compose -f compose/local.yml config` exit {result.returncode} "
        f"(regresija!). 9.1 NE sme da razbije lokalni dev stack.\n"
        f"stderr: {result.stderr}"
    )


def test_regression_entrypoint_sh_still_migrates():
    """AC7/AC8 regresija: compose/django/entrypoint.sh (dev) NETAKNUT — i dalje migrate-uje.

    SM-D2: lokalni entrypoint.sh ostaje DEV UX (migrate na startup). Prod ga zaobilazi
    kroz start.sh. Ako Dev slučajno ukloni migrate iz entrypoint.sh → dev regresija.
    """
    content = _read_file(ENTRYPOINT_SH)
    assert re.search(r"manage\.py\s+migrate", content), (
        "compose/django/entrypoint.sh više NE migrate-uje (dev regresija!). "
        "SM-D2: lokalni entrypoint.sh ostaje NETAKNUT (migrate = dev UX). Prod "
        "koristi zaseban start.sh BEZ migrate, ne dira entrypoint.sh."
    )


def test_regression_dockerfile_dev_path_keeps_dev_deps():
    """AC7/G-4 regresija: dev put u compose/django/Dockerfile NE sadrži `--no-dev`
    u izvršnoj instrukciji (pytest/ruff moraju ostati za `just test`).

    Prod `--no-dev` je ZASEBAN build target/arg — komentari su OK, ali izvršni
    `RUN uv sync ... --no-dev` u DEV putu bi razbio `just test` (Docker-backed).
    Story 9.1 dodaje prod put kroz separate stage/arg; dev linija 23 NETAKNUTA.
    """
    content = _read_file(COMPOSE_DJANGO_DIR / "Dockerfile")
    # Dozvoli `--no-dev` ali SAMO u kontekstu uslovnog/arg-gated prod stage-a.
    # Regression guard: postojeći dev `RUN uv sync --frozen --no-install-project`
    # (bez --no-dev) MORA i dalje postojati.
    assert re.search(
        r"RUN\s+uv\s+sync\s+--frozen\s+--no-install-project(?!\s+--no-dev)",
        content,
    ), (
        "compose/django/Dockerfile dev put (`RUN uv sync --frozen "
        "--no-install-project` BEZ --no-dev) više ne postoji — G-4 regresija. "
        "Dev put (pytest/ruff za `just test`) mora ostati; prod `--no-dev` ide u "
        "ZASEBAN build target/arg."
    )


# =============================================================================
# AC3 / AC4 / AC8 — MANDATORY runnable container smoke (Docker dostupan)
# =============================================================================


def _wait_for_http_200(url: str, timeout_s: int = 90) -> subprocess.CompletedProcess:
    """Poll `curl -I <url>` dok ne vrati response (ili timeout). Vrati zadnji curl
    CompletedProcess. Retry loop sa kratkim pauzama (stack treba vremena da se digne).
    """
    curl = shutil.which("curl")
    if curl is None:
        pytest.skip("curl nije na PATH-u — preskačem HTTP smoke.")
    deadline = time.monotonic() + timeout_s
    last = None
    while time.monotonic() < deadline:
        last = subprocess.run(
            [curl, "-sS", "-I", url],
            capture_output=True,
            text=True,
            shell=False,
            timeout=20,
        )
        # curl exit 0 + ima status liniju → server odgovara (ma koji status)
        if last.returncode == 0 and "HTTP/" in last.stdout:
            return last
        time.sleep(3)
    return last  # type: ignore[return-value]


@pytest.mark.docker
def test_ac8_container_smoke_http_200_and_security_headers():
    """AC3/AC4/AC8 MANDATORY container smoke — diže pravi prod stack.

    TEST-OWNERSHIP: ovaj test je SVESNO PREUZET od Story 9.2 (AC7/AC12/SM-D6 + M7) i
    azuriran da reflektuje 9.2 ponasanje. Story 9.2 je aktivirala nginx :80 blok da radi
    BEZUSLOVAN `return 301 https://` (OSIM ACME challenge-a). Redirect se desava na NGINX
    sloju (NE Django SECURE_SSL_REDIRECT) → `GET http://localhost/sr/` daje 301 sa
    `Location: https://...`, ne 200. Bez cert-a u smoke-u ne mozemo da pratimo redirect do
    443 (cert ne postoji), pa tvrdimo:
      (a) :80 /sr/ → 301 sa `Location` koji pocinje `https://`,
      (b) sva 3 security headera prisutna na 301 odgovoru (nginx `always` emituje i na 3xx),
      (c) `GET /.well-known/acme-challenge/<probe>` NE redirect-uje (200/404, NIKAD 301) —
          inace certbot webroot validacija puca.

    M1: production.yml nginx bind-mount cilja `compose/nginx/.active-default.conf` (swappable,
    gitignored). Smoke ga seed-uje iz nginx.conf-a PRE `up` (steady-state put = pun 443 conf;
    :80 redirect aktivan). M2: production.yml django `image:` je GHCR-pathed, ali `build:`
    blok ostaje → `docker compose up --build` gradi i tag-uje lokalno, pa up koristi lokalni
    build (offline OK; `pull` nije pozvan u smoke-u).

    Koraci:
      1. seed .active-default.conf <- nginx.conf (M1 — bind-mount target mora postojati).
      2. up -d --build sa smoke env-om.
      3. migrate + collectstatic seed (volume prazan).
      4. curl -I http://localhost/sr/ → 301 https:// + 3 security headera (M7).
      5. curl http://localhost/.well-known/acme-challenge/<probe> → NE 301 (M7).
      6. down -v cleanup (try/finally — uvek se izvrši).

    Deselect: `pytest -m "not docker"`.
    """
    docker = _docker_bin()
    if docker is None:
        pytest.skip("docker CLI nije na PATH-u — preskačem container smoke.")
    if not PRODUCTION_YML.exists():
        pytest.fail("compose/production.yml ne postoji (Story 9.1 Task 4).")
    if not NGINX_CONF.exists():
        pytest.fail("compose/nginx/nginx.conf ne postoji (Story 9.1/9.2).")

    # M1: bind-mount cilja .active-default.conf (gitignored, runtime swap). Seed ga punim
    # nginx.conf-om (steady-state) pre `up` da nginx servira 443 conf sa :80 301 redirect-om.
    active_conf = COMPOSE_NGINX_DIR / ".active-default.conf"
    active_conf.write_text(NGINX_CONF.read_text(encoding="utf-8"), encoding="utf-8")

    compose = [docker, "compose", "-f", str(PRODUCTION_YML)]
    smoke_env = {
        **os.environ,
        "DJANGO_SECRET_KEY": TEST_SECRET,
        "DJANGO_ALLOWED_HOSTS": "localhost,127.0.0.1",
        # SSL_REDIRECT irelevantan za :80 → /sr/ jer nginx radi 301 PRE Django-a (M7).
        "DJANGO_SECURE_SSL_REDIRECT": "False",
        "DJANGO_CSRF_TRUSTED_ORIGINS": "http://localhost",
        # M2: GHCR-pathed image; build: fallback gradi+tag-uje lokalno (up koristi lokalni
        # build, pull se NE poziva u smoke-u). Default-i iz production.yml su dovoljni.
        "GHCR_IMAGE": "miiihaaas/coric_agrar",
        "IMAGE_TAG": "smoke",
        # POSTGRES_* / DATABASE_URL — prod compose očekuje kroz env_file/secrets;
        # smoke ih daje kroz env (Dev: production.yml mora konzumirati ove varijable).
        "POSTGRES_DB": "coric_agrar",
        "POSTGRES_USER": "coric",
        "POSTGRES_PASSWORD": "coric_smoke_pw",
        "DATABASE_URL": "postgres://coric:coric_smoke_pw@postgres:5432/coric_agrar",
    }

    def _compose(args: list[str], timeout: int = 300) -> subprocess.CompletedProcess:
        return subprocess.run(
            compose + args,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            shell=False,
            timeout=timeout,
            env=smoke_env,
        )

    try:
        up = _compose(["up", "-d", "--build"], timeout=600)
        assert up.returncode == 0, (
            f"`docker compose -f production.yml up -d` exit {up.returncode}.\n"
            f"stdout: {up.stdout}\nstderr: {up.stderr}"
        )

        # Seed DB schema (prod start.sh NE migrira — project-context:478/G-6; migrate je
        # deploy-step 9.2, ovde test fixture — isto kao collectstatic ispod). Bez ovoga
        # GET /sr/ → 500 (RedirectMiddleware query-uje seo_redirect tabelu koja ne postoji).
        # NE menja prod artefakte: start.sh ostaje migrate-free (test_ac5_start_sh_does_not_migrate).
        migrate = _compose(
            ["run", "--rm", "django", "python", "manage.py", "migrate", "--noinput"],
            timeout=300,
        )
        assert migrate.returncode == 0, (
            f"migrate seed exit {migrate.returncode}.\n"
            f"stdout: {migrate.stdout}\nstderr: {migrate.stderr}"
        )

        # Seed static (volume prazan u 9.1; collectstatic je deploy-step, ovde test fixture)
        seed = _compose(
            ["run", "--rm", "django", "python", "manage.py", "collectstatic", "--noinput"],
            timeout=300,
        )
        assert seed.returncode == 0, (
            f"collectstatic seed exit {seed.returncode}.\n"
            f"stdout: {seed.stdout}\nstderr: {seed.stderr}"
        )

        # M7: App endpoint kroz Nginx :80 → BEZUSLOVAN 301 na https:// (NE 200; redirect je
        # na nginx sloju, ne Django SECURE_SSL_REDIRECT). _wait_for_http_200 vraca na BILO
        # koji HTTP odgovor (uklj. 301) — proverava da nginx slusa i odgovara.
        resp = _wait_for_http_200("http://localhost/sr/", timeout_s=90)
        assert resp is not None and resp.returncode == 0, (
            f"curl http://localhost/sr/ nije uspeo (Nginx ne odgovara).\n"
            f"stdout: {getattr(resp, 'stdout', '')}\nstderr: {getattr(resp, 'stderr', '')}"
        )
        headers = resp.stdout
        status_line = headers.splitlines()[0] if headers.splitlines() else ""
        # M7: 9.2 nginx :80 radi 301 https:// za /sr/ (NE 200, NE 502). 502 = upstream down.
        assert " 301" in status_line, (
            f"GET :80 /sr/ status nije 301. Status linija: {status_line!r}.\n"
            f"M7/AC7/SM-D6: 9.2 nginx :80 radi BEZUSLOVAN `return 301 https://` (redirect na "
            f"nginx sloju). 502 = Gunicorn upstream down.\nPun header:\n{headers}"
        )
        hlow = headers.lower()
        # M7: Location MORA pocinjati `https://` (HTTP→HTTPS redirect korektnost).
        assert re.search(r"location:\s*https://", hlow), (
            f"GET :80 /sr/ 301 nema `Location: https://...`.\n"
            f"M7/AC7: redirect mora da vodi na HTTPS.\nHeaders:\n{headers}"
        )
        # M7: 3 security headera prisutna i na 301 (nginx `always` emituje i na 3xx).
        for name, val in (
            ("x-frame-options", "deny"),
            ("x-content-type-options", "nosniff"),
            ("referrer-policy", "same-origin"),
        ):
            assert name in hlow and val in hlow, (
                f"Response header `{name}: {val}` nedostaje na 301 odgovoru.\n"
                f"AC8/M7: sva 3 security headera (`always`) prisutna i na redirect-u.\n"
                f"Headers:\n{headers}"
            )

        # M7: ACME challenge putanja NE SME da se redirect-uje (mora 200/404, NIKAD 301) —
        # inace certbot webroot validacija puca. Probe nepostojeci challenge fajl.
        acme_resp = subprocess.run(
            [
                shutil.which("curl") or "curl", "-sS", "-I",
                "http://localhost/.well-known/acme-challenge/smoke-probe-12345",
            ],
            capture_output=True, text=True, shell=False, timeout=20,
        )
        acme_status = (
            acme_resp.stdout.splitlines()[0] if acme_resp.stdout.splitlines() else ""
        )
        assert " 301" not in acme_status, (
            f"GET /.well-known/acme-challenge/<probe> se REDIRECT-uje (301): {acme_status!r}.\n"
            f"M7/AC7/SM-D6: ACME location MORA ostati 200/404 (servira webroot), NIKAD 301 — "
            f"inace certbot --webroot validacija FAIL-uje.\nPun output:\n{acme_resp.stdout}"
        )
        assert (" 404" in acme_status or " 200" in acme_status), (
            f"GET /.well-known/acme-challenge/<probe> status nije 200/404: {acme_status!r}.\n"
            f"M7: ACME location servira webroot (nepostojeci probe → 404; postojeci → 200)."
        )

        # M7: static na :80 takodje hvata bezuslovan 301 → https:// (9.2: SAV :80 saobracaj
        # OSIM ACME-a se redirect-uje; direktno static serving je sada u 443 bloku, koji se
        # ne moze testirati bez cert-a u smoke-u). Tvrdimo 301 (NE 200) — konzistentno sa M7.
        static_resp = subprocess.run(
            [shutil.which("curl") or "curl", "-sS", "-I", "http://localhost/static/admin/css/base.css"],
            capture_output=True,
            text=True,
            shell=False,
            timeout=20,
        )
        static_status = (
            static_resp.stdout.splitlines()[0] if static_resp.stdout.splitlines() else ""
        )
        assert " 301" in static_status, (
            f"GET :80 /static/admin/css/base.css nije 301. Status: {static_status!r}.\n"
            f"M7/AC7: 9.2 nginx :80 redirect-uje SAV saobracaj (osim ACME) na https://; "
            f"direktno static serving je u 443 bloku (ne testabilno bez cert-a u smoke-u).\n"
            f"Pun output:\n{static_resp.stdout}\n{static_resp.stderr}"
        )
    finally:
        # Cleanup UVEK (try/finally) — down -v briše volume-e (čist state).
        subprocess.run(
            compose + ["down", "-v"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            shell=False,
            timeout=120,
            env=smoke_env,
        )
        # M1: ukloni runtime swap conf seed (gitignored, ne ostavljaj artefakt).
        try:
            active_conf.unlink(missing_ok=True)
        except OSError:
            pass
