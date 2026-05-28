"""Tests za Story 1.3 - Docker Compose za Local Environment.

Verifikuje filesystem state + static analysis za Docker Compose setup:
- AC1: compose/ folder struktura + .gitattributes (narrow scope LF za *.sh)
- AC2: compose/django/Dockerfile multi-stage uv build
- AC3: compose/django/entrypoint.sh (LF endings, pg_isready, migrate, exec $@)
- AC4: compose/local.yml (django + db servisi, named volumes, healthcheck)
- AC5: .dockerignore u root-u
- AC6: justfile dev recept rewired + dev-* helperi
- AC7: .env.example DATABASE_URL koristi `@db:` (Docker servis ime)
- AC8: docker compose config validacija (static check, NE up)
- Edge: bez baked-in secrets u Dockerfile/compose

Pokrenuti sa:
    uv run pytest tests/test_docker_compose.py -v

TEA RED faza: svi testovi MORAJU pasti dok Dev ne zavrsi Story 1.3.
Testovi su FILESYSTEM + STATIC ANALYSIS — NE pokrecu `docker compose up`
(slow, fragile, port collision risk). Pokrecu samo `docker compose config`
za fast YAML/schema validaciju. Ako docker CLI nije na PATH-u, ti testovi
se skip-uju sa jasnom porukom.

YAML parsing: koristi pyyaml ako je dostupan (transitivna dep iz pre-commit
u dev grupi); fallback na regex/text matching da test fajl ne pretpostavlja
direct dep. Ako pyyaml nije instaliran, testovi koji ga zahtevaju se skip-uju
sa porukom (Dev neka stavi pyyaml u dev grupu ili obezbedi transitivno).

Naming convention: srpska latinica + engleski; bez cirilice.
"""

from __future__ import annotations

import re
import shutil
import subprocess
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

# Compose
COMPOSE_DIR = PROJECT_ROOT / "compose"
COMPOSE_DJANGO_DIR = COMPOSE_DIR / "django"
COMPOSE_LOCAL_YML = COMPOSE_DIR / "local.yml"
DOCKERFILE = COMPOSE_DJANGO_DIR / "Dockerfile"
ENTRYPOINT_SH = COMPOSE_DJANGO_DIR / "entrypoint.sh"

# Repo-root files
DOCKERIGNORE = PROJECT_ROOT / ".dockerignore"
GITATTRIBUTES = PROJECT_ROOT / ".gitattributes"
JUSTFILE = PROJECT_ROOT / "justfile"
ENV_EXAMPLE = PROJECT_ROOT / ".env.example"


# =============================================================================
# Helper funkcije
# =============================================================================


def _read_file(path: Path) -> str:
    """Pročita text fajl. Fail-uje ako ne postoji."""
    if not path.exists():
        pytest.fail(f"Fajl ne postoji: {path}")
    return path.read_text(encoding="utf-8")


def _read_binary(path: Path) -> bytes:
    """Pročita fajl u binary mode (za LF/CRLF detekciju)."""
    if not path.exists():
        pytest.fail(f"Fajl ne postoji: {path}")
    return path.read_bytes()


def _parse_yaml(path: Path) -> dict:
    """Parse YAML fajl koristeći pyyaml. Skip ako pyyaml nije dostupan.

    Story 1.3 ne dodaje pyyaml kao novi dep — ali pre-commit/playwright donose
    ga tranzitivno. Ako test runner nema pyyaml, skip sa jasnom porukom.
    """
    if _yaml is None:
        pytest.skip(
            "pyyaml nije dostupan u env-u — `uv run pytest` bi trebalo da ga ima "
            "tranzitivno kroz pre-commit. Ako baš nedostaje, dodaj `pyyaml` u "
            "dev grupu (`uv add --dev pyyaml`) ili instaliraj `uv sync`."
        )
    if not path.exists():
        pytest.fail(f"YAML fajl ne postoji: {path}")
    with path.open("r", encoding="utf-8") as f:
        return _yaml.safe_load(f)


def _run_docker_compose_config(yml_path: Path) -> subprocess.CompletedProcess | None:
    """Pokreni `docker compose -f <yml_path> config --quiet`. Vraća
    CompletedProcess (no raise) ili None ako docker CLI nije na PATH-u.

    Static schema/references validacija — NE pokreće kontejnere.
    """
    docker_bin = shutil.which("docker")
    if docker_bin is None:
        return None
    return subprocess.run(
        [docker_bin, "compose", "-f", str(yml_path), "config", "--quiet"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        shell=False,
        timeout=60,
    )


def _has_lf_only(path: Path) -> bool:
    """True ako fajl ima isključivo LF (\\n) line endings — bez CRLF (\\r\\n).

    Critical za entrypoint.sh — Linux bash u kontejneru ne tolerira CRLF
    (`/usr/bin/env: 'bash\\r': No such file or directory`).
    """
    content = _read_binary(path)
    return b"\r\n" not in content


# =============================================================================
# AC1 — compose/ folder struktura + .gitattributes (narrow scope)
# =============================================================================


def test_ac1_compose_directory_exists():
    """AC1: `compose/` i `compose/django/` direktorijumi MORAJU postojati."""
    assert COMPOSE_DIR.exists(), (
        f"compose/ direktorijum ne postoji na {COMPOSE_DIR}. "
        f"Kreiraj: New-Item -ItemType Directory compose/django"
    )
    assert COMPOSE_DIR.is_dir(), (
        f"compose/ postoji ali NIJE direktorijum (verovatno fajl)."
    )
    assert COMPOSE_DJANGO_DIR.exists(), (
        f"compose/django/ ne postoji na {COMPOSE_DJANGO_DIR}."
    )
    assert COMPOSE_DJANGO_DIR.is_dir(), (
        f"compose/django/ postoji ali NIJE direktorijum."
    )


def test_ac1_gitattributes_exists_with_narrow_scope():
    """AC1 / Gotcha #5: `.gitattributes` u root-u sa NARROW scope pravilima.

    MORA sadržati:
      - `*.sh text eol=lf` (sve shell skripte LF)
      - `compose/django/entrypoint.sh text eol=lf` (eksplicitno)

    NE SME sadržati bare `* text=auto eol=lf` (Gotcha #5 / iter-1 fix:
    forsiranje eol=lf na sve text fajlove izaziva whole-file diff churn
    na Windows-u kad git renormalizuje CRLF iz editora).
    """
    assert GITATTRIBUTES.exists(), (
        f".gitattributes ne postoji na {GITATTRIBUTES}. Story Task 9 ga kreira."
    )
    content = _read_file(GITATTRIBUTES)

    # MUST: *.sh LF rule
    sh_pattern = r"^\s*\*\.sh\s+text\s+eol=lf\s*$"
    assert re.search(sh_pattern, content, re.MULTILINE), (
        ".gitattributes ne sadrži `*.sh text eol=lf` pravilo. "
        "Bash u Linux kontejneru ne tolerira CRLF — vidi Gotcha #5."
    )

    # MUST: eksplicitno entrypoint.sh LF rule (defenzivno)
    explicit_pattern = (
        r"^\s*compose/django/entrypoint\.sh\s+text\s+eol=lf\s*$"
    )
    assert re.search(explicit_pattern, content, re.MULTILINE), (
        ".gitattributes ne sadrži eksplicitno `compose/django/entrypoint.sh text eol=lf`. "
        "Defenzivno dvostruko pravilo (osim `*.sh`) traženo u story Task 9."
    )

    # MUST NOT: bare `* text=auto eol=lf` (whole-file diff churn)
    bad_pattern = r"^\s*\*\s+text=auto\s+eol=lf\s*$"
    assert not re.search(bad_pattern, content, re.MULTILINE), (
        ".gitattributes sadrži bare `* text=auto eol=lf` — to izaziva whole-file "
        "diff churn na Windows-u (Gotcha #5 / iter-1 fix). Koristi samo `* text=auto` "
        "(bez eol=lf) za default."
    )


def test_ac1_compose_django_directory_files_listed():
    """AC1: `compose/django/` MORA sadržati Dockerfile + entrypoint.sh.

    Negative scope: NE sme da postoji `start.sh` (gunicorn launcher) — to je
    Story 9.1 prod.
    """
    assert DOCKERFILE.exists(), (
        f"compose/django/Dockerfile ne postoji na {DOCKERFILE}."
    )
    assert ENTRYPOINT_SH.exists(), (
        f"compose/django/entrypoint.sh ne postoji na {ENTRYPOINT_SH}."
    )
    # Negative: start.sh je out-of-scope za Story 1.3 (Story 9.1 ga uvodi)
    start_sh = COMPOSE_DJANGO_DIR / "start.sh"
    assert not start_sh.exists(), (
        f"compose/django/start.sh postoji — to je Story 9.1 prod-only artifact. "
        f"Story 1.3 koristi runserver kroz CMD u Dockerfile-u, ne start.sh."
    )


# =============================================================================
# AC2 — compose/django/Dockerfile multi-stage uv build
# =============================================================================


def test_ac2_dockerfile_exists():
    """AC2: `compose/django/Dockerfile` MORA postojati."""
    assert DOCKERFILE.exists(), (
        f"compose/django/Dockerfile ne postoji na {DOCKERFILE}. "
        f"Vidi Dev Notes § Dockerfile Template za sadržaj."
    )


def test_ac2_dockerfile_is_multi_stage():
    """AC2: Dockerfile MORA imati dve `FROM ... AS <stage>` linije (builder + runtime).

    Multi-stage je optimizacija: builder instalira deps kroz uv, runtime
    samo COPY-uje `.venv` (bez uv binary u runtime image-u → manji image).
    """
    content = _read_file(DOCKERFILE)
    # Match "FROM <image> AS <stage>" (case-insensitive za AS keyword)
    pattern = r"^\s*FROM\s+\S+\s+AS\s+(\S+)"
    matches = re.findall(pattern, content, re.MULTILINE | re.IGNORECASE)
    assert len(matches) >= 2, (
        f"Dockerfile MORA imati barem 2 `FROM ... AS <stage>` linije "
        f"(multi-stage build). Pronađeno stage-ova: {matches}. "
        f"Story Dev Notes Template ima `builder` + `runtime`."
    )
    # Provera za canonical stage imena iz Dev Notes Template-a
    stages_lower = {s.lower() for s in matches}
    assert "builder" in stages_lower, (
        f"Dockerfile nema `builder` stage. Story template: `FROM ghcr.io/astral-sh/uv:python3.13-... AS builder`. "
        f"Pronađeno: {matches}"
    )
    assert "runtime" in stages_lower, (
        f"Dockerfile nema `runtime` stage. Story template: `FROM python:3.13-slim AS runtime`. "
        f"Pronađeno: {matches}"
    )


def test_ac2_dockerfile_uses_uv_sync_frozen():
    """AC2 / Gotcha #7: builder stage MORA pozivati `uv sync --frozen` sa
    `--no-install-project --no-dev` flag-ovima.

    - `--frozen`: koristi tačno uv.lock verzije (reproducible)
    - `--no-install-project`: ne pokušava da instalira `coric-agrar` paket
    - `--no-dev`: dev grupa (pytest, ruff, ...) NE ulazi u runtime image
    """
    content = _read_file(DOCKERFILE)
    # `uv sync` MORA imati `--frozen` flag
    assert re.search(r"uv\s+sync\s+[^\n]*--frozen", content), (
        "Dockerfile ne sadrži `uv sync --frozen` poziv. "
        "Story Gotcha #7: --frozen je kritičan za reproducible builds."
    )
    # MORA imati --no-install-project
    assert re.search(r"uv\s+sync\s+[^\n]*--no-install-project", content), (
        "Dockerfile `uv sync` poziv NEMA `--no-install-project` flag. "
        "Story Gotcha #7: bez ovog flag-a uv pokušava da instalira coric-agrar "
        "kao paket — failuje jer nemamo [build-system]."
    )
    # MORA imati --no-dev
    assert re.search(r"uv\s+sync\s+[^\n]*--no-dev", content), (
        "Dockerfile `uv sync` poziv NEMA `--no-dev` flag. "
        "Bez njega dev grupa (pytest, ruff, ...) ulazi u runtime image — bloat + "
        "potencijalni security surface."
    )


def test_ac2_dockerfile_python_313():
    """AC2: Dockerfile MORA koristiti Python 3.13 base image (matchuje .python-version).

    Builder može biti `ghcr.io/astral-sh/uv:python3.13-bookworm-slim` (canonical)
    ili manual install u 3.13-slim. Runtime MORA biti `python:3.13-slim`.
    """
    content = _read_file(DOCKERFILE)
    # Mora imati referencu na python3.13 ili python:3.13 negde u FROM linijama
    assert re.search(r"python[:\-]?3\.13", content), (
        "Dockerfile ne referencira Python 3.13 base image. "
        "Story tech stack: pin na 3.13 iz .python-version. "
        "Builder: `ghcr.io/astral-sh/uv:python3.13-bookworm-slim`, "
        "Runtime: `python:3.13-slim`."
    )
    # Runtime stage MORA biti `python:3.13-slim` (slim varijanta — manji image)
    runtime_pattern = (
        r"FROM\s+python:3\.13-slim\s+AS\s+runtime"
    )
    assert re.search(runtime_pattern, content, re.IGNORECASE), (
        "Dockerfile runtime stage NIJE `FROM python:3.13-slim AS runtime`. "
        "Story Dev Notes Template eksplicitno koristi slim varijantu za manji image."
    )


def test_ac2_dockerfile_system_deps_present():
    """AC2: runtime stage MORA instalirati system deps:
    `libmagic1`, `poppler-utils`, `postgresql-client`.

    `gettext` je takođe u Dev Notes Template (Story 1.4 prep), ali strogo gledano
    je opciono za AC2 — ovaj test ga proverava i traži ga (defenzivno).
    """
    content = _read_file(DOCKERFILE)
    required_packages = [
        "libmagic1",       # python-magic MIME validacija
        "poppler-utils",   # pdf2image PDF cover-thumbnail
        "postgresql-client",  # pg_isready za entrypoint wait-for-db
        "gettext",         # django compilemessages (Story 1.4+, prep)
    ]
    missing = [pkg for pkg in required_packages if pkg not in content]
    assert not missing, (
        f"Dockerfile nedostaju system deps: {missing}. "
        f"Story Dev Notes Template § Dockerfile runtime stage navodi sve 4. "
        f"libmagic1 i poppler-utils SU OBAVEZNI za python-magic / pdf2image."
    )


def test_ac2_dockerfile_copies_venv_from_builder():
    """AC2: runtime stage MORA da COPY --from=builder .venv (preuzima Python
    deps iz builder-a; bez uv binary u runtime image-u).
    """
    content = _read_file(DOCKERFILE)
    # Match: COPY --from=builder /app/.venv /app/.venv (or similar /app/.venv path)
    pattern = r"COPY\s+--from=builder\s+/app/\.venv\s+/app/\.venv"
    assert re.search(pattern, content), (
        "Dockerfile runtime stage nema `COPY --from=builder /app/.venv /app/.venv`. "
        "Bez tog COPY runtime image nema instalirane Python deps. "
        "Vidi Dev Notes § Dockerfile Template."
    )


def test_ac2_dockerfile_sets_entrypoint():
    """AC2: Dockerfile MORA imati `ENTRYPOINT` koji referencira `entrypoint.sh`.

    Canonical pattern: `ENTRYPOINT ["/entrypoint.sh"]` (sa apsolutnom putanjom
    u image-u jer Dockerfile COPY-uje skriptu na `/entrypoint.sh`).
    """
    content = _read_file(DOCKERFILE)
    # Match ENTRYPOINT linija koja referencira entrypoint.sh (apsolutna putanja
    # ili relativna — fleksibilno)
    pattern = r"ENTRYPOINT\s*\[?[^]\n]*entrypoint\.sh"
    assert re.search(pattern, content), (
        "Dockerfile ne sadrži `ENTRYPOINT` koji referencira entrypoint.sh. "
        "Story Dev Notes Template: `ENTRYPOINT [\"/entrypoint.sh\"]`."
    )


# =============================================================================
# AC3 — compose/django/entrypoint.sh
# =============================================================================


def test_ac3_entrypoint_exists():
    """AC3: `compose/django/entrypoint.sh` MORA postojati."""
    assert ENTRYPOINT_SH.exists(), (
        f"compose/django/entrypoint.sh ne postoji na {ENTRYPOINT_SH}. "
        f"Vidi Dev Notes § entrypoint.sh Template za sadržaj."
    )


def test_ac3_entrypoint_has_lf_line_endings():
    """AC3 / Gotcha #5: entrypoint.sh MORA imati LF line endings (NE CRLF).

    Bash u Linux kontejneru ne tolerira CRLF:
    `/usr/bin/env: 'bash\\r': No such file or directory` → container crash.

    NAPOMENA: Test čita fajl u binary mode i traži `\\r\\n` sekvence.
    Na Windows-u, default Python text mode bi tiho konvertovao CRLF u LF
    pri čitanju — zato MORA binary read. Defenzivno dvostruko zaštićeno
    kroz `.gitattributes` (test ac1) ali ovo enforce-uje na disku.
    """
    assert ENTRYPOINT_SH.exists(), (
        "entrypoint.sh ne postoji (videti prethodni test)."
    )
    assert _has_lf_only(ENTRYPOINT_SH), (
        f"entrypoint.sh ima CRLF line endings (\\r\\n sekvence pronađene). "
        f"Bash u Linux kontejneru će crash-ovati sa `/usr/bin/env: 'bash\\r': "
        f"No such file or directory`. "
        f"Rešenje: VS Code status bar dugme `CRLF` → klik → `LF` → Save, "
        f"ILI `dos2unix compose/django/entrypoint.sh`, "
        f"ILI git renormalize: `git rm --cached compose/django/entrypoint.sh && "
        f"git add compose/django/entrypoint.sh` (uz .gitattributes pravilo iz AC1)."
    )


def test_ac3_entrypoint_has_pg_isready_wait_loop():
    """AC3: entrypoint.sh MORA sadržati `pg_isready` poziv (wait-for-db loop).

    pg_isready dolazi iz `postgresql-client` apt paketa (Dockerfile runtime stage,
    AC2). Bez wait loop-a, Django migrate može startovati pre DB inicijalizacije
    → konekcija failuje.
    """
    content = _read_file(ENTRYPOINT_SH)
    assert "pg_isready" in content, (
        "entrypoint.sh ne sadrži `pg_isready` poziv. "
        "Story Dev Notes Template: `until pg_isready -h ... -p ... -U ...; do ... done`. "
        "Bez wait loop-a Django može pokušati migrate pre nego što je Postgres ready."
    )


def test_ac3_entrypoint_runs_migrate():
    """AC3: entrypoint.sh MORA pozivati `manage.py migrate` (idempotent u dev-u)."""
    content = _read_file(ENTRYPOINT_SH)
    # Match: `python manage.py migrate` ili `manage.py migrate`
    pattern = r"manage\.py\s+migrate"
    assert re.search(pattern, content), (
        "entrypoint.sh ne poziva `manage.py migrate`. "
        "Story Dev Notes Template: `python manage.py migrate --noinput`. "
        "Bez ovog poziva svaki novi container ostaje sa unapplied migracijama."
    )


def test_ac3_entrypoint_ends_with_exec_dollar_at():
    """AC3 / Gotcha #2 KRITIČNO: entrypoint.sh MORA imati `exec "$@"` kao
    POSLEDNJU non-empty / non-comment liniju.

    `exec` zamenjuje shell process-om CMD-a — to znači signali (SIGTERM od
    `docker stop`) idu direktno Django runserver-u (graceful shutdown). Bez
    `exec`, Django runuje kao bash-ov child → SIGTERM ide bash-u (koji ne
    propagira default-no) → posle 10s Docker SIGKILL-uje sve.
    """
    content = _read_file(ENTRYPOINT_SH)
    # Skini prazne linije i komentare sa kraja, pronađi poslednju "stvarnu" liniju
    lines = content.splitlines()
    last_real_line = None
    for line in reversed(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        last_real_line = stripped
        break
    assert last_real_line is not None, (
        "entrypoint.sh nema nijednu non-empty/non-comment liniju."
    )
    # Tolerantno na razmake: `exec "$@"` ili `exec $@` (single/double quotes/no quotes)
    pattern = r'^exec\s+["\']?\$@["\']?\s*$'
    assert re.match(pattern, last_real_line), (
        f"entrypoint.sh POSLEDNJA non-empty/non-comment linija MORA biti `exec \"$@\"`. "
        f"Dobijeno: {last_real_line!r}. "
        f"Story Gotcha #2: bez `exec` signali se ne propagiraju Django-u → "
        f"graceful shutdown je broken, Docker SIGKILL-uje posle 10s."
    )


def test_ac3_entrypoint_has_set_euo_pipefail():
    """AC3: entrypoint.sh MORA imati `set -euo pipefail` (bash strict mode).

    - `-e`: exit on bilo kojoj komandnoj grešci
    - `-u`: greška na undefined varijable
    - `-o pipefail`: greška u pipe-u propagira kroz cevovod

    Fail-fast je esencijalan u entrypoint skriptama — ako migrate padne,
    ne želimo da `exec runserver` ipak startuje na pola-broken state-u.
    """
    content = _read_file(ENTRYPOINT_SH)
    # Tolerantno: dozvoli redosled flag-ova (`-eu o pipefail`, `-euo pipefail`, ...)
    # Minimum: mora postojati `set -e` + `pipefail`. Strict: `set -euo pipefail`.
    assert "set -euo pipefail" in content, (
        "entrypoint.sh ne sadrži `set -euo pipefail`. "
        "Story Dev Notes Template eksplicitno traži tu liniju (bash strict mode). "
        "Fail-fast je obavezan u entrypoint-u."
    )


# =============================================================================
# AC4 — compose/local.yml
# =============================================================================


def test_ac4_compose_yaml_exists():
    """AC4: `compose/local.yml` MORA postojati."""
    assert COMPOSE_LOCAL_YML.exists(), (
        f"compose/local.yml ne postoji na {COMPOSE_LOCAL_YML}. "
        f"Vidi Dev Notes § compose/local.yml Template za sadržaj."
    )


def test_ac4_compose_yaml_is_valid():
    """AC4: `docker compose -f compose/local.yml config --quiet` exit code 0.

    To je fast static validacija — proverava YAML schema, env_file path
    rezoluciju, build context path, depends_on reference. NE pokreće
    kontejnere. Ako docker CLI nije na PATH-u, test se skip-uje (test okruženje
    bez Docker-a — npr. CI runner bez Docker Engine-a).
    """
    if not COMPOSE_LOCAL_YML.exists():
        pytest.fail("compose/local.yml ne postoji (videti prethodni test).")
    result = _run_docker_compose_config(COMPOSE_LOCAL_YML)
    if result is None:
        pytest.skip(
            "docker CLI nije na PATH-u — preskačem static config validaciju. "
            "Instaliraj Docker Desktop (Win) / Docker Engine (Linux) da se test "
            "izvrši."
        )
    assert result.returncode == 0, (
        f"`docker compose -f compose/local.yml config` exit code {result.returncode}.\n"
        f"stdout: {result.stdout}\n"
        f"stderr: {result.stderr}\n"
        f"Verovatno YAML schema/syntax greška, ili pogrešna env_file/build path "
        f"referenca. Vidi `docker compose config` output za detalje."
    )


def test_ac4_compose_has_django_and_db_services():
    """AC4: `services:` sekcija MORA imati `django` i `db` ključeve."""
    data = _parse_yaml(COMPOSE_LOCAL_YML)
    services = data.get("services", {})
    assert isinstance(services, dict), (
        f"compose/local.yml `services:` nije mapping. Dobijeno: {type(services)}"
    )
    missing = [s for s in ("django", "db") if s not in services]
    assert not missing, (
        f"compose/local.yml `services:` nedostaju ključevi: {missing}. "
        f"Pronađeno: {list(services.keys())}. "
        f"AC4 zahteva tačno dva servisa: `django` i `db`."
    )


def test_ac4_compose_has_named_volumes():
    """AC4: top-level `volumes:` MORA deklarisati `postgres_data` i `django_venv`.

    - `postgres_data`: DB data persistency između `docker compose down`/`up`
    - `django_venv`: sprečava bind mount od overwrite-ovanja /app/.venv (Gotcha #1)
    """
    data = _parse_yaml(COMPOSE_LOCAL_YML)
    volumes = data.get("volumes", {})
    assert isinstance(volumes, dict), (
        f"compose/local.yml `volumes:` top-level nije mapping. "
        f"Dobijeno: {type(volumes)}. AC4 zahteva top-level volume deklaracije."
    )
    missing = [v for v in ("postgres_data", "django_venv") if v not in volumes]
    assert not missing, (
        f"compose/local.yml top-level `volumes:` nedostaju: {missing}. "
        f"Pronađeno: {list(volumes.keys())}. "
        f"AC4 + Gotcha #1: `postgres_data` (DB persist) + `django_venv` "
        f"(zaštita /app/.venv od bind mount overlay-a)."
    )


def test_ac4_compose_db_has_healthcheck():
    """AC4: `services.db.healthcheck` MORA biti definisan (test command +
    interval/timeout/retries).
    """
    data = _parse_yaml(COMPOSE_LOCAL_YML)
    db = data.get("services", {}).get("db", {})
    healthcheck = db.get("healthcheck")
    assert healthcheck is not None, (
        "compose/local.yml `services.db.healthcheck:` ne postoji. "
        "AC4 zahteva healthcheck (`pg_isready -U coric -d coric_agrar`). "
        "Bez njega `depends_on: condition: service_healthy` ne radi."
    )
    assert isinstance(healthcheck, dict), (
        f"`services.db.healthcheck` nije mapping. Dobijeno: {type(healthcheck)}"
    )
    # Mora imati `test` ključ (komanda)
    assert "test" in healthcheck, (
        "`services.db.healthcheck.test` nedostaje. "
        "AC4 template: `test: [\"CMD-SHELL\", \"pg_isready -U coric -d coric_agrar\"]`."
    )


def test_ac4_compose_django_depends_on_db_healthy():
    """AC4: `services.django.depends_on.db.condition` MORA biti `service_healthy`.

    Bez ovog condition-a, Compose čeka samo da `db` kontejner starts (PID 1
    živ) ne i da je Postgres ready. To može razbiti entrypoint wait-loop u
    edge slučajevima — defense-in-depth dual gate.
    """
    data = _parse_yaml(COMPOSE_LOCAL_YML)
    django = data.get("services", {}).get("django", {})
    depends_on = django.get("depends_on", {})
    # Compose V2 dozvoljava: `depends_on: [db]` (lista) ili `depends_on: {db: {condition: ...}}` (mapping)
    # AC4 explicitly zahteva mapping formu sa `condition: service_healthy`.
    assert isinstance(depends_on, dict), (
        f"`services.django.depends_on` MORA biti mapping forma (ne lista). "
        f"Dobijeno: {type(depends_on)}. "
        f"AC4 template: `depends_on: {{db: {{condition: service_healthy}}}}`."
    )
    db_dep = depends_on.get("db", {})
    assert isinstance(db_dep, dict), (
        f"`services.django.depends_on.db` MORA biti mapping sa `condition`. "
        f"Dobijeno: {type(db_dep)}"
    )
    assert db_dep.get("condition") == "service_healthy", (
        f"`services.django.depends_on.db.condition` = {db_dep.get('condition')!r}, "
        f"očekivano `service_healthy`. AC4 zahtev (Gotcha #8 razlog)."
    )


def test_ac4_compose_postgres_image_pinned_16():
    """AC4: `services.db.image` MORA biti pinovan na PostgreSQL 16
    (`postgres:16-alpine` ili `postgres:16` Debian-based). NE `:latest`.

    project-context.md § Core runtime preporučuje "16+"; Story koristi 16-alpine
    radi manjeg image-a.
    """
    data = _parse_yaml(COMPOSE_LOCAL_YML)
    db_image = data.get("services", {}).get("db", {}).get("image", "")
    assert db_image, (
        "`services.db.image` ne postoji. AC4 zahteva pinovan postgres:16 image."
    )
    # Match `postgres:16` ili `postgres:16-<variant>` (alpine, bookworm, ...)
    assert re.match(r"^postgres:16(\-\w+)?$", db_image), (
        f"`services.db.image` = {db_image!r}, očekivano `postgres:16` ili "
        f"`postgres:16-<variant>` (e.g. `postgres:16-alpine`). "
        f"NE koristi `:latest` ili nepinovanu verziju — project-context.md zahteva 16+."
    )


def test_ac4_compose_django_uses_env_file_from_root():
    """AC4 / Gotcha #3: `services.django.env_file` MORA referencirati `../.env`
    (relativni path do root-a repo-a, jer je `compose/local.yml` u `compose/`
    subdirektorijumu).

    Bez `env_file`, secrets (DJANGO_SECRET_KEY itd.) NE bi došli u kontejner →
    fail-fast crash na `python manage.py migrate` (Gotcha #21).
    Inline `environment:` MORA biti rezervisan za non-secret config; sve
    secrets dolaze kroz `env_file`.
    """
    data = _parse_yaml(COMPOSE_LOCAL_YML)
    django = data.get("services", {}).get("django", {})
    env_file = django.get("env_file")
    assert env_file is not None, (
        "compose/local.yml `services.django.env_file:` ne postoji. "
        "AC4 zahteva `env_file: ../.env` (relativni path do root-a). "
        "Bez njega DJANGO_SECRET_KEY ne ulazi u kontejner."
    )
    # env_file može biti string ili lista (Compose dozvoljava oba)
    if isinstance(env_file, str):
        env_file_values = [env_file]
    elif isinstance(env_file, list):
        # Lista može biti list[str] ili list[dict{path: ..., required: ...}]
        env_file_values = [
            ef if isinstance(ef, str) else ef.get("path", "")
            for ef in env_file
        ]
    else:
        pytest.fail(
            f"`services.django.env_file` mora biti string ili lista. "
            f"Dobijeno: {type(env_file)}"
        )
    assert any("../.env" in v or "../../.env" == v for v in env_file_values), (
        f"`services.django.env_file` ne referencira `../.env`. "
        f"Pronađeno: {env_file_values}. "
        f"AC4 template: `env_file: - ../.env`."
    )


def test_ac4_compose_django_build_context_is_repo_root():
    """AC4 / Gotcha #11: `services.django.build.context` MORA biti `../` (root
    repo-a), NE `compose/` ili `.`.

    Razlog: Dockerfile mora pristupiti `pyproject.toml`/`uv.lock`/`manage.py`/
    `config/` koji su u root-u. Build context određuje i lokaciju
    `.dockerignore` fajla — `.dockerignore` se traži u root-u (NE u `compose/`).
    """
    data = _parse_yaml(COMPOSE_LOCAL_YML)
    django = data.get("services", {}).get("django", {})
    build = django.get("build")
    assert build is not None, (
        "compose/local.yml `services.django.build:` ne postoji. "
        "AC4 template: `build: context: ../, dockerfile: compose/django/Dockerfile`."
    )
    # build može biti string (samo context path) ili mapping
    if isinstance(build, str):
        context = build
    elif isinstance(build, dict):
        context = build.get("context", "")
    else:
        pytest.fail(
            f"`services.django.build` mora biti string ili mapping. "
            f"Dobijeno: {type(build)}"
        )
    # Normalize trailing slashes — `../` ili `..`
    normalized = context.rstrip("/")
    assert normalized == "..", (
        f"`services.django.build.context` = {context!r}, očekivano `../` "
        f"(root repo-a). Gotcha #11: Dockerfile mora videti pyproject.toml/"
        f"uv.lock/manage.py u root-u, ne u compose/."
    )


def test_ac4_compose_django_named_volume_overlays_dot_venv():
    """AC4 / Gotcha #1 KRITIČNO: `services.django.volumes` MORA imati BOTH:
      - bind mount source code (`../:/app:cached` ili sl.)
      - named volume `django_venv:/app/.venv` (overlay zaštita)

    Razlog (Gotcha #1): bind mount `../:/app` overlay-uje host repo na
    `/app` u kontejneru — uključujući host-ov `.venv` (ako postoji) preko
    image-ovog `.venv`. Linux kontejner NE može da koristi Windows-built venv
    → ImportError ili crash. Named volume `django_venv:/app/.venv` se montuje
    POSLE bind mount-a i sadrži kopiju image-ovog `.venv` (pri prvom up-u),
    pa kontejner ima Linux venv unutar Linux runtime-a.

    Bez OBA mount-a (samo named volume bez bind mount-a, ili samo bind mount
    bez named volume-a) Story 1.3 hot-reload je broken.
    """
    data = _parse_yaml(COMPOSE_LOCAL_YML)
    django = data.get("services", {}).get("django", {})
    volumes = django.get("volumes", [])
    assert isinstance(volumes, list), (
        f"`services.django.volumes` mora biti lista mount specifikacija. "
        f"Dobijeno: {type(volumes)}"
    )
    # Each mount može biti string (`source:target[:mode]`) ili dict
    # (long-form: `{type: bind, source: ..., target: ...}`).
    mount_strings = []
    for m in volumes:
        if isinstance(m, str):
            mount_strings.append(m)
        elif isinstance(m, dict):
            # Long-form normalize: source + target
            src = m.get("source", "")
            tgt = m.get("target", "")
            mount_strings.append(f"{src}:{tgt}")
    joined = "\n".join(mount_strings)

    # MUST: named volume `django_venv` mounted at /app/.venv
    venv_mount_pattern = r"django_venv\s*:\s*/app/\.venv"
    assert re.search(venv_mount_pattern, joined), (
        f"`services.django.volumes` nema mount `django_venv:/app/.venv`. "
        f"Pronađeno: {mount_strings}. "
        f"Gotcha #1 KRITIČNO: bez named volume overlay-a, host `.venv` "
        f"prepisuje image `.venv` u kontejneru → Python deps neuporeztabilne."
    )
    # MUST: bind mount source code (any path → /app, sa ili bez `:cached`)
    # Tolerantno: traži bilo koji mount koji završava sa `:/app` ili `:/app:cached`
    bind_mount_pattern = r":/app(:[a-z]+)?(\s|$)"
    bind_found = any(
        re.search(bind_mount_pattern, m) and "django_venv" not in m and "postgres_data" not in m
        for m in mount_strings
    )
    assert bind_found, (
        f"`services.django.volumes` nema bind mount source code-a u `/app`. "
        f"Pronađeno: {mount_strings}. "
        f"AC4 template: `- ../:/app:cached` za hot-reload (Django autoreload "
        f"prati host fajl-sistem kroz bind mount)."
    )


# =============================================================================
# AC5 — .dockerignore
# =============================================================================


def test_ac5_dockerignore_exists():
    """AC5: `.dockerignore` MORA postojati u root-u repo-a (NE u compose/)."""
    assert DOCKERIGNORE.exists(), (
        f".dockerignore ne postoji na {DOCKERIGNORE}. "
        f"Story Gotcha #11: build context je root (`build.context: ../`), "
        f"pa .dockerignore traži se u root-u."
    )


def test_ac5_dockerignore_excludes_critical_paths():
    """AC5: `.dockerignore` MORA sadržati exclude pattern-e za:
    `.venv`, `__pycache__`, `_bmad-output`, `_bmad`, `.git`, `.env`.

    Negative: `.env.example` NE sme biti eksplicitno u .dockerignore-u (jer je
    template fajl koji može biti reference; iako image ga ne treba, ne treba ni
    da bude ignored kao greška).
    """
    content = _read_file(DOCKERIGNORE)
    required = [
        ".venv",         # host venv ne ide u image
        "__pycache__",   # bytecode
        "_bmad-output",  # planning artifacts
        "_bmad",         # BMad installer
        ".git",          # git history
        ".env",          # secrets MORA biti ignored
    ]
    missing = [pat for pat in required if pat not in content]
    assert not missing, (
        f".dockerignore nedostaju kritični pattern-i: {missing}. "
        f"Story AC5 template eksplicitno navodi sve ove."
    )
    # Negative: `.env.example` ne sme biti direktno listed (bez negacije)
    # Provera: linije koje su tačno `.env.example` ili `*.env.example` bez `!` prefix-a.
    bad_lines = []
    for raw in content.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("!"):
            continue  # negacija (whitelist) je OK
        if line == ".env.example" or line == "/.env.example":
            bad_lines.append(raw)
    assert not bad_lines, (
        f".dockerignore eksplicitno ignoriše .env.example: {bad_lines}. "
        f".env.example je committable template — ne treba ga ignorisati. "
        f"Ukloni te linije."
    )


# =============================================================================
# AC6 — justfile dev recept rewired + dev-* helperi
# =============================================================================


def test_ac6_justfile_dev_recipe_uses_docker_compose():
    """AC6: `justfile` `dev:` recept MORA pokrenuti docker compose.

    Stari (Story 1.1) recept: `uv run python manage.py runserver`
    Novi (Story 1.3): `docker compose -f compose/local.yml up`
    """
    content = _read_file(JUSTFILE)
    # Pronađi blok `dev:` recepta — linija "dev:" + sledeća indented linija
    # Tolerantno na komentare iznad.
    dev_recipe_pattern = re.compile(
        r"^dev\s*:\s*\n((?:\s+[^\n]*\n?)+)",
        re.MULTILINE,
    )
    match = dev_recipe_pattern.search(content)
    assert match, (
        "justfile nema `dev:` recept (linija koja počinje sa `dev:`). "
        "Story Task 7.2 traži update postojećeg dev recepta."
    )
    recipe_body = match.group(1)
    assert "docker compose" in recipe_body, (
        f"`dev:` recept telo NE sadrži `docker compose`. "
        f"Pronađeno telo:\n{recipe_body}\n"
        f"Story Task 7.2: zameni telo sa `docker compose -f compose/local.yml up`."
    )
    # Mora referencirati compose/local.yml path
    assert "compose/local.yml" in recipe_body, (
        f"`dev:` recept telo ne referencira `compose/local.yml`. "
        f"Pronađeno: {recipe_body!r}. "
        f"Mora biti `docker compose -f compose/local.yml up`."
    )


def test_ac6_justfile_has_dev_helpers():
    """AC6: justfile MORA dodati barem jedan od dev-* helper recepata.

    Story Task 7.4 traži svih 5: dev-build, dev-down, dev-logs, dev-shell,
    dev-manage. Ovaj test traži minimum jedan (defenzivno tolerantno), ali
    poruka navodi sve 5 da Dev zna scope.
    """
    content = _read_file(JUSTFILE)
    helpers = ["dev-build", "dev-down", "dev-logs", "dev-shell", "dev-manage"]
    # Match line koji počinje sa `<helper>:` ili `<helper> *ARGS:` (with-args sintaksa)
    found = []
    for helper in helpers:
        pattern = rf"^{re.escape(helper)}\s*(?:\*?[a-zA-Z_].*)?:\s*$"
        if re.search(pattern, content, re.MULTILINE):
            found.append(helper)
    assert len(found) >= 1, (
        f"justfile nema nijedan dev-* helper recept. "
        f"Story Task 7.4 traži svih 5: {helpers}. "
        f"Story Dev Notes § justfile snippet ima template."
    )
    # Strict: traži se barem 3 da story task spec ne bude pola-implementiran
    assert len(found) >= 3, (
        f"justfile ima samo {len(found)} dev-* helpera: {found}. "
        f"Story Task 7.4 traži svih 5: {helpers}. "
        f"Implementuj nedostajuće."
    )


def test_ac6_justfile_preserves_story_1_1_recipes():
    """AC6 regression guard: justfile MORA i dalje imati `test`, `lint`,
    `migrate`, `messages` recepte (Story 1.1 baseline).

    Story 1.3 NE menja te recepte (Gotcha #9: testovi i lint na host-u, ne u
    kontejneru). Ako Dev slučajno obriše bilo koji od njih → regression.
    """
    content = _read_file(JUSTFILE)
    required = ["test", "lint", "migrate", "messages"]
    missing = []
    for recipe in required:
        # Match line koji počinje sa `<recipe>:` (no args)
        pattern = rf"^{re.escape(recipe)}\s*:"
        if not re.search(pattern, content, re.MULTILINE):
            missing.append(recipe)
    assert not missing, (
        f"justfile nedostaju Story 1.1 recepti: {missing}. "
        f"Story 1.3 ih NE menja (Gotcha #9 — testovi/lint ostaju na host-u). "
        f"Ako su slučajno obrisani: restore iz Story 1.1 baseline-a."
    )


# =============================================================================
# AC7 — .env.example DATABASE_URL update
# =============================================================================


def test_ac7_env_example_database_url_uses_docker_hostname():
    """AC7: `.env.example` `DATABASE_URL=` linija MORA koristiti `@db:` host
    (NE `@localhost:`).

    `db` je Docker Compose servis ime — rezolvuje se kroz Docker DNS unutar
    compose network-a. Story 1.2 je imao samo `DATABASE_URL=` (prazno);
    Story 1.3 popunjava placeholder sa Docker servis ime-om.
    """
    assert ENV_EXAMPLE.exists(), (
        f".env.example ne postoji na {ENV_EXAMPLE}."
    )
    content = _read_file(ENV_EXAMPLE)
    # Match: DATABASE_URL=postgres://coric:coric@db:5432/coric_agrar
    pattern = (
        r"^DATABASE_URL\s*=\s*postgres://coric:coric@db:5432/coric_agrar\s*$"
    )
    assert re.search(pattern, content, re.MULTILINE), (
        f".env.example `DATABASE_URL=` linija ne matchuje očekivani format. "
        f"AC7 traži: `DATABASE_URL=postgres://coric:coric@db:5432/coric_agrar` "
        f"(host `db`, NE `localhost`). "
        f"Vidi Story AC7 / Dev Notes § `.env.example` snippet."
    )


def test_ac7_env_example_dropped_sqlite_default_comment():
    """AC7: `.env.example` NE SME više sadržati komentar "Story 1.2 default je SQLite".

    Story 1.2 stari komentar je sugerisao SQLite kao fallback default — to više
    nije primarno (PostgreSQL kroz Docker je sad default). Ostavi pominjanje
    SQLite-a samo ako je u kontekstu "alt za van-Docker", ne kao "Story 1.2
    default".
    """
    content = _read_file(ENV_EXAMPLE)
    forbidden_phrase = "Story 1.2 default je SQLite"
    assert forbidden_phrase not in content, (
        f".env.example još sadrži zastareli komentar `{forbidden_phrase!r}`. "
        f"AC7: ukloni taj komentar — PostgreSQL kroz Docker Compose je sad "
        f"primarni default. Vidi Dev Notes § `.env.example` replacement snippet."
    )


# =============================================================================
# AC8 — Smoke validation prereqs (static checks, NE actual docker up)
# =============================================================================


def test_ac8_compose_config_validation_passes():
    """AC8: `docker compose -f compose/local.yml config --quiet` exit 0.

    Najjača static validacija — proverava:
    - YAML schema validity (Compose spec V2)
    - env_file path resolution (`../.env` mora postojati ILI biti `env_file: required: false`)
    - build context path resolution (`../` mora biti valid dir)
    - depends_on cross-reference (svi servisi navedeni postoje)
    - top-level volumes referenced from services postoje na top-level

    NE pokreće kontejnere — fast (~200ms). Ako docker nije na PATH-u, skip.

    NAPOMENA: Ovaj test može padati zbog nedostatka `.env` fajla (env_file
    referenca). Story Task 10 kreira `.env` lokalno (NE komituje). Ako test
    failuje sa `env file ... not found`, Dev neka uradi `Copy-Item .env.example .env`.
    """
    if not COMPOSE_LOCAL_YML.exists():
        pytest.fail("compose/local.yml ne postoji.")
    result = _run_docker_compose_config(COMPOSE_LOCAL_YML)
    if result is None:
        pytest.skip(
            "docker CLI nije na PATH-u — preskačem AC8 config validaciju."
        )
    # Tolerantno: ako stderr pominje samo `.env not found` (Task 10 lokalni step),
    # ipak fail-uj (Dev mora da kopira .env iz .env.example). U bilo kom drugom
    # slučaju jasno reportuj exit code + stderr.
    assert result.returncode == 0, (
        f"`docker compose config` exit code {result.returncode}.\n"
        f"stdout: {result.stdout}\n"
        f"stderr: {result.stderr}\n"
        f"Možda treba `Copy-Item .env.example .env` (Task 10.1) pre nego što "
        f"test prođe. Ili je pravi YAML/path bug — pogledaj stderr."
    )


def test_ac8_dockerfile_can_be_lex_parsed():
    """AC8: lightweight Dockerfile syntax sanity — svaka non-empty / non-comment
    linija MORA početi validnom Dockerfile instrukcijom ili biti continuation
    (`\\` na prethodnoj liniji).

    Validne instrukcije (case-insensitive): FROM, RUN, CMD, ENTRYPOINT, COPY,
    ADD, ENV, ARG, EXPOSE, WORKDIR, USER, VOLUME, LABEL, ONBUILD, STOPSIGNAL,
    HEALTHCHECK, SHELL, MAINTAINER.

    NIJE pun Dockerfile parser — samo eyeball check da nije bezvezni tekst.
    """
    if not DOCKERFILE.exists():
        pytest.fail("compose/django/Dockerfile ne postoji.")
    content = _read_file(DOCKERFILE)
    valid_instructions = {
        "FROM", "RUN", "CMD", "ENTRYPOINT", "COPY", "ADD", "ENV", "ARG",
        "EXPOSE", "WORKDIR", "USER", "VOLUME", "LABEL", "ONBUILD",
        "STOPSIGNAL", "HEALTHCHECK", "SHELL", "MAINTAINER",
    }
    bad_lines: list[tuple[int, str]] = []
    in_continuation = False
    for lineno, raw in enumerate(content.splitlines(), start=1):
        line = raw.strip()
        # Prazne linije i komentari (uključujući `# syntax=` directive) — OK
        if not line or line.startswith("#"):
            in_continuation = False
            continue
        if in_continuation:
            # Ova linija je continuation prethodne — proveri samo continuation flag
            in_continuation = line.endswith("\\")
            continue
        # Prva reč linije mora biti validna instrukcija
        first_word = line.split(None, 1)[0].upper()
        if first_word not in valid_instructions:
            bad_lines.append((lineno, raw))
        # Postavi continuation flag za sledeću liniju
        in_continuation = line.endswith("\\")

    assert not bad_lines, (
        f"Dockerfile sadrži linije sa nevalidnim Dockerfile instrukcijama:\n"
        + "\n".join(f"  line {ln}: {raw!r}" for ln, raw in bad_lines[:10])
        + (f"\n  ... ({len(bad_lines) - 10} more)" if len(bad_lines) > 10 else "")
        + f"\nValidne instrukcije: {sorted(valid_instructions)}"
    )


# =============================================================================
# Edge cases / negative tests / security guardrails
# =============================================================================


def test_no_inline_secrets_in_compose():
    """SECURITY: `compose/local.yml` NE SME sadržati realne secret-e.

    `POSTGRES_PASSWORD: coric` je acceptable kao local-only placeholder
    (Story Gotcha #3 explicit). Ali bilo koji 30+ char random-looking
    alphanumeric/base64 string ukazuje na pravi secret (npr. neko zalepio
    `DJANGO_SECRET_KEY` ili `EMAIL_HOST_PASSWORD`).
    """
    if not COMPOSE_LOCAL_YML.exists():
        pytest.fail("compose/local.yml ne postoji.")
    content = _read_file(COMPOSE_LOCAL_YML)
    # Match: 30+ char string koji izgleda kao secret (base64-ish, no spaces).
    # Tolerantno: 30 chars sa mix slova/brojeva (skipnemo URL pattern-e tipa
    # `https://hub.docker.com/_/postgres` koji nisu secret).
    # Pattern: linija koja sadrži 30+ chars consecutive [A-Za-z0-9+/=_-] (no spaces)
    # i NIJE čisti URL.
    suspicious_lines = []
    for lineno, raw in enumerate(content.splitlines(), start=1):
        stripped = raw.strip()
        # Skip komentare i prazne linije
        if not stripped or stripped.startswith("#"):
            continue
        # Skip linije koje su čiste URL/image reference (sadrže `:` i nemaju vrednost-token tipa)
        # Match 30+ char "secret-looking" token: alfanumerik + base64 chars, bez whitespace
        for match in re.finditer(r"[A-Za-z0-9+/=_-]{30,}", stripped):
            token = match.group(0)
            # Eliminate false positives:
            # - URL paths (slash u kontekstu)
            # - Image reference (sadrži tag separator `:` ili registry slash)
            # - Volume name "coric_agrar_postgres_data" (32 chars ali nije secret)
            if "coric_agrar" in token:
                continue
            if "/" in stripped[max(0, match.start() - 3):match.end() + 3]:
                # Looks like URL fragment
                continue
            suspicious_lines.append((lineno, raw.strip(), token))

    assert not suspicious_lines, (
        f"compose/local.yml ima sumnjivo dugačke string-token-e (potencijalno "
        f"baked-in secrets):\n"
        + "\n".join(
            f"  line {ln}: {raw!r}  (token: {token!r})"
            for ln, raw, token in suspicious_lines[:5]
        )
        + "\nStory Gotcha #3: secrets MORAJU dolaziti kroz env_file: ../.env, "
        "NIKAD inline u local.yml. Acceptable je samo local placeholder "
        "`POSTGRES_PASSWORD: coric` (kratak, nije pravi secret)."
    )


def test_dockerfile_no_secrets_baked_in():
    """SECURITY / Gotcha #3: `Dockerfile` NE SME imati `ENV DJANGO_SECRET_KEY=...`
    ili sličnu baked-in secret env var.

    Secrets u Dockerfile `ENV` postaju deo image-a → vidljivi u `docker history`
    i image layer-ima zauvek. SOT za secrets je `.env` (runtime mount kroz
    `env_file:` u compose).
    """
    if not DOCKERFILE.exists():
        pytest.fail("Dockerfile ne postoji.")
    content = _read_file(DOCKERFILE)
    # Forbidden ENV var key-evi (može biti `ENV KEY=val` ili `ENV KEY val`)
    forbidden_keys = [
        "DJANGO_SECRET_KEY",
        "SECRET_KEY",
        "DATABASE_URL",   # ne sme baked-in jer sadrži password
        "EMAIL_HOST_PASSWORD",
        "EMAIL_URL",      # može sadržati SMTP password
        "POSTGRES_PASSWORD",
    ]
    bad = []
    for key in forbidden_keys:
        # Match: `ENV <KEY>=...` ili `ENV <KEY> ...` (case-insensitive ENV)
        pattern = rf"^\s*ENV\s+{re.escape(key)}[\s=]"
        if re.search(pattern, content, re.MULTILINE | re.IGNORECASE):
            bad.append(key)
    assert not bad, (
        f"Dockerfile sadrži `ENV` direktive za secrets: {bad}. "
        f"Story Gotcha #3: secrets se NIKAD ne pišu u Dockerfile (postaju deo "
        f"image-a). Sve secrets dolaze kroz `env_file: ../.env` u compose-u."
    )
