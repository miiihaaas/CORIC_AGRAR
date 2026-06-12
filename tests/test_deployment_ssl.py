"""Tests za Story 9.2 — Hetzner Deployment Script + SSL.

INFRA-VERIFY testovi (needs_e2e=false — NE Playwright/browser). Deliverable-i
ove story-je su OPERATIVNI fajlovi:
  - ops/deploy/deploy.sh        (deploy orkestracija; ordered koraci)
  - ops/deploy/rollback.sh      (checkout prev tag + svesno migrate-down)
  - ops/nginx/nginx-init.sh     (certbot webroot + bootstrap + auto-renewal)
  - compose/nginx/nginx.bootstrap.conf  (HTTP-only first-deploy conf)
  - compose/nginx/nginx.conf    (UPDATE: 443 ssl aktiviran + ACME + redirect)
  - compose/production.yml       (UPDATE: nginx cert/webroot/conf bind-mounts)
  - .github/workflows/deploy.yml (NOVI SSH deploy workflow)
  - .github/workflows/ci.yml     (UPDATE: GHCR login + push: true)
  - .env.example                 (UPDATE: deploy placeholderi)
  - ops/secrets/README.md        (NOVI: GH secrets + SSH least-privilege)

Test pristup je CISTO file-parsing: pathlib + re + yaml SAMO. NEMA Django
settings load, NEMA libmagic, NEMA app importa, NEMA subprocess shellcheck
(shellcheck/bats NISU na host-u). Ovo cini fajl IMPORT-LIGHT — trci i na
native Windows host-u (gde pun suite ne moze da collect-uje zbog libmagic
baseline-a) I u Docker/CI. Vidi Task 9.6.

PyYAML quirk: `on:` u workflow-u parsira se kao Python boolean `True`
(YAML 1.1 — `on`/`off`/`yes`/`no` rezervisane reci). Pristup trigger bloku
kroz `_get_on_block` helper (pokriva `True` i string `"on"`).

Pokrenuti sa (host-friendly — conftest.py je import-light, bez Django):
    uv run pytest tests/test_deployment_ssl.py -v -p no:cacheprovider

TEA RED faza: svi testovi MORAJU pasti dok Dev ne kreira/azurira artefakte.
Fixtures koriste `pytest.fail("Missing required file: ...")` kad artefakt ne
postoji → svaki test fail-uje sa jasnom RED porukom (mirror
test_production_stack.py / test_ci_workflow_config.py RED ponasanja).

Naming convention: srpska latinica + engleski identifikatori; bez cirilice.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

# =============================================================================
# Konstante (project paths) — mirror REPO_ROOT pattern iz test_ci_workflow_config.py
# =============================================================================

REPO_ROOT = Path(__file__).resolve().parent.parent

OPS_DIR = REPO_ROOT / "ops"
DEPLOY_SH = OPS_DIR / "deploy" / "deploy.sh"
ROLLBACK_SH = OPS_DIR / "deploy" / "rollback.sh"
NGINX_INIT_SH = OPS_DIR / "nginx" / "nginx-init.sh"
SECRETS_README = OPS_DIR / "secrets" / "README.md"

COMPOSE_DIR = REPO_ROOT / "compose"
NGINX_CONF = COMPOSE_DIR / "nginx" / "nginx.conf"
NGINX_BOOTSTRAP_CONF = COMPOSE_DIR / "nginx" / "nginx.bootstrap.conf"
PRODUCTION_YML = COMPOSE_DIR / "production.yml"

DEPLOY_YML = REPO_ROOT / ".github" / "workflows" / "deploy.yml"
CI_YML = REPO_ROOT / ".github" / "workflows" / "ci.yml"
ENV_EXAMPLE = REPO_ROOT / ".env.example"

# Path-contract (AC13/SM-D4) — KONKRETAN webroot na 3 mesta.
ACME_WEBROOT = "/var/www/certbot"

# Branch naming koji story LOCK-uje (SM-D1/OQ-1). Tolerancija: ili planning naming
# `{staging, main}` ili repo-realnost `{master}` (Mihas razresava OQ-1 pre deploy-a).
EXPECTED_DEPLOY_BRANCHES = {"staging", "main"}
TOLERATED_DEPLOY_BRANCHES = {"master"}


# =============================================================================
# Helper funkcije (mirror _read_file / grep-lock stil iz test_production_stack.py)
# =============================================================================


def _read_file(path: Path, owner: str = "Story 9.2") -> str:
    """Procita text fajl. Fail-uje (RED signal) sa jasnom porukom ako ne postoji."""
    if not path.exists():
        pytest.fail(f"Missing required file: {path}\n{owner} Dev ga mora kreirati/azurirati.")
    return path.read_text(encoding="utf-8")


def _read_binary(path: Path) -> bytes:
    if not path.exists():
        pytest.fail(f"Missing required file: {path}\nStory 9.2 Dev ga mora kreirati.")
    return path.read_bytes()


def _has_lf_only(path: Path) -> bool:
    """True ako fajl ima iskljucivo LF (bez CRLF) — G-1 (bash u Linux ne tolerise CRLF)."""
    return b"\r\n" not in _read_binary(path)


def _strip_comments(content: str) -> str:
    """Vrati samo izvrsne linije shell skripte (bez `#`-komentar linija).

    Za ORDERING/negative grep-ove koji NE smeju da matchuju komentar-marker tekst.
    Cuva inline-trailing komentare kratko (re.search na celu liniju je dovoljan za
    nase pattern-e koji ciljaju komande, ne komentar-prozu).
    """
    return "\n".join(
        ln for ln in content.splitlines() if not ln.lstrip().startswith("#")
    )


def _index_of(pattern: str, text: str, flags: int = 0) -> int:
    """Vrati start indeks PRVOG matcha pattern-a u tekstu, ili -1 ako nema."""
    m = re.search(pattern, text, flags)
    return m.start() if m else -1


def _active_lines(content: str) -> str:
    """Vrati samo non-comment (aktivne) linije nginx conf-a (drop `#`-prefiks linije)."""
    return "\n".join(ln for ln in content.splitlines() if not ln.lstrip().startswith("#"))


def _extract_443_server_block(content: str) -> str | None:
    """Izvuci telo `server { ... }` bloka koji sadrzi `listen 443 ssl` (brace-balansirano).

    Radi SAMO na aktivnim (non-comment) linijama tako da zakomentarisan 9.1 placeholder
    NE moze lazno da zadovolji 443-scoped asercije. Vraca telo bloka (string izmedju
    spoljnih viticastih zagrada) ili None ako aktivan 443 server blok ne postoji.

    Mehanizam: nadji svaki `server {` u aktivnom sadrzaju, balansiraj zagrade do
    odgovarajuce `}`, pa proveri da li telo sadrzi `listen 443 ssl`.
    """
    active = _active_lines(content)
    for m in re.finditer(r"server\s*\{", active):
        depth = 0
        start = m.end() - 1  # pozicija otvorene `{`
        for i in range(start, len(active)):
            ch = active[i]
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    body = active[start + 1 : i]
                    if re.search(r"listen\s+443\s+ssl", body):
                        return body
                    break
    return None


def _get_on_block(workflow: dict) -> dict:
    """Vrati `on:` block (PyYAML parsira nepokvotovani `on` kao boolean True)."""
    if True in workflow:
        return workflow[True]
    if "on" in workflow:
        return workflow["on"]
    pytest.fail("workflow nema `on:` block (ni boolean True ni string 'on').")
    return {}  # unreachable


def _parse_yaml(path: Path) -> dict:
    """Parse YAML kroz pyyaml; fail (RED) ako fajl ne postoji."""
    if not path.exists():
        pytest.fail(f"Missing required file: {path}\nStory 9.2 Dev ga mora kreirati.")
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _flatten_yaml_strings(node) -> list[str]:
    """Rekurzivno skupi sve string vrednosti+kljuceve iz parsiranog YAML-a (za grep)."""
    out: list[str] = []
    if isinstance(node, dict):
        for k, v in node.items():
            if isinstance(k, str):
                out.append(k)
            out.extend(_flatten_yaml_strings(v))
    elif isinstance(node, list):
        for item in node:
            out.extend(_flatten_yaml_strings(item))
    elif isinstance(node, str):
        out.append(node)
    return out


# Forbidden secret-leak pattern-i (AC5) — provera RAW sadrzaja novih fajlova.
_SECRET_LEAK_PATTERNS = [
    (r"BEGIN [A-Z ]*PRIVATE KEY", "PEM private key block"),
    (r"^\s*POSTGRES_PASSWORD\s*[:=]\s*(?!\s*$)(?!\$\{)(?!['\"]?\s*$)\S", "hardkodovan ne-prazan POSTGRES_PASSWORD"),
    (r"ghp_[A-Za-z0-9]{20,}", "GitHub Personal Access Token"),
    (r"github_pat_[A-Za-z0-9_]{20,}", "GitHub Fine-grained PAT"),
]


# =============================================================================
# AC1 — ops/deploy/deploy.sh postoji + deploy koraci + set -euo pipefail + LF
# =============================================================================


def test_ac1_deploy_sh_exists():
    """AC1/Task 2.2: `ops/deploy/deploy.sh` MORA postojati."""
    assert DEPLOY_SH.exists(), (
        f"Missing required file: {DEPLOY_SH}\n"
        f"AC1/Task 2.2: deploy orkestracija (git pull -> compose pull -> migrate -> up -d)."
    )


def test_ac1_deploy_sh_set_euo_pipefail():
    """AC1: deploy.sh MORA poceti sa `set -euo pipefail` (fail-fast)."""
    content = _read_file(DEPLOY_SH)
    assert re.search(r"set\s+-euo\s+pipefail", content), (
        "ops/deploy/deploy.sh nema `set -euo pipefail`. AC1: fail-fast je obavezan."
    )


def test_ac1_deploy_sh_lf_line_endings():
    """AC1/G-1: deploy.sh MORA imati LF line endings (bash u Linux crash-uje na CRLF)."""
    if not DEPLOY_SH.exists():
        pytest.fail(f"Missing required file: {DEPLOY_SH}")
    assert _has_lf_only(DEPLOY_SH), (
        "ops/deploy/deploy.sh ima CRLF line endings. G-1: bash u Linux kontejneru/boxu "
        "ne tolerise CRLF. `.gitattributes:8` `*.sh text eol=lf` mora vaziti."
    )


def test_ac1_deploy_sh_has_core_deploy_steps():
    """AC1: deploy.sh MORA sadrzati sve core korake (git pull, compose pull, uv sync,
    collectstatic, migrate, compilemessages, up -d)."""
    content = _read_file(DEPLOY_SH)
    # M3: `uv sync --frozen` UKLONJEN sa host-a (deps su BAKED u GHCR image — vidi
    # test_ac1_deploy_sh_uv_sync_frozen_is_image_baked). NE listamo ga ovde kao required korak.
    required = {
        "git pull": r"git\s+pull",
        "docker compose pull": r"docker\s+compose\s+.*\bpull\b",
        "collectstatic --noinput": r"collectstatic\s+--noinput",
        "migrate (apply)": r"manage\.py\s+migrate(?!\s+--plan)",
        "compilemessages": r"manage\.py\s+compilemessages",
        "up -d": r"docker\s+compose\s+.*\bup\s+-d\b",
    }
    missing = [name for name, pat in required.items() if not re.search(pat, content)]
    assert not missing, (
        f"ops/deploy/deploy.sh nedostaju koraci: {missing}. "
        f"AC1: git pull -> docker compose pull -> collectstatic "
        f"-> migrate -> compilemessages -> up -d django/nginx."
    )


def test_ac1_deploy_sh_collectstatic_noinput_present():
    """AC1/AC3: deploy.sh `collectstatic` MORA biti `--noinput` (neinteraktivno = idempotent)."""
    content = _read_file(DEPLOY_SH)
    assert re.search(r"collectstatic\s+--noinput", content), (
        "ops/deploy/deploy.sh nema `collectstatic --noinput`. AC1/AC3: mora biti "
        "neinteraktivno (idempotency)."
    )


def test_ac1_deploy_sh_uv_sync_frozen_is_image_baked():
    """AC1/AC3 (M3): deploy.sh NE SME pokretati BARE `uv sync --frozen` na host-u — stack je
    Docker-image-SOT (prod image vec radi `uv sync --frozen --no-dev` u build vremenu, pa su
    frozen deps zapecene u GHCR image koji se povlaci u koraku 2). Bare host `uv sync` bi
    fail-ovao (uv mozda nije na boxu) ILI bio besmislen (deps zive u kontejneru).

    Lock: nijedna IZVRSNA (non-comment) linija ne sme biti bare `uv sync --frozen` (van
    `docker compose run/exec` konteksta). Komentar-marker objasnjava image-baked odluku.
    """
    content = _read_file(DEPLOY_SH)
    # Image-baked decision dokumentovana komentarom (grep-lock na reconciliation).
    assert re.search(r"image[- ]baked|BAKED u", content, re.IGNORECASE), (
        "ops/deploy/deploy.sh ne dokumentuje da su frozen deps image-baked (M3). "
        "Komentar-marker (frozen deps BAKED u GHCR image) je obavezan za reconciliation "
        "sa project-context koji lista `uv sync --frozen`."
    )
    # Negative: nema BARE host `uv sync --frozen` u izvrsnoj liniji (van compose run/exec).
    exec_lines = _strip_comments(content)
    for ln in exec_lines.splitlines():
        if re.search(r"\buv\s+sync\s+--frozen", ln):
            assert re.search(r"docker\s+compose\s+.*\b(run|exec)\b", ln), (
                f"ops/deploy/deploy.sh ima BARE host `uv sync --frozen`: {ln!r}. M3: deps su "
                f"image-baked; ako se uopste poziva, MORA biti kroz `docker compose run/exec`, "
                f"ne na host venv-u."
            )


def test_ac1_deploy_sh_migrate_plan_precheck_present():
    """AC1/AC2: deploy.sh MORA imati `migrate --plan` pre-check korak."""
    content = _read_file(DEPLOY_SH)
    assert re.search(r"manage\.py\s+migrate\s+--plan", content), (
        "ops/deploy/deploy.sh nema `migrate --plan` pre-check korak. "
        "AC1/AC2: --plan je assertion/pre-check PRE apply migrate-a."
    )


def test_ac1_deploy_sh_compilemessages_present():
    """AC1: deploy.sh MORA imati `compilemessages` (sr/hu/en .mo build)."""
    content = _read_file(DEPLOY_SH)
    assert re.search(r"manage\.py\s+compilemessages", content), (
        "ops/deploy/deploy.sh nema `compilemessages`. AC1: i18n .mo fajlovi se build-uju "
        "deploy-time."
    )


# =============================================================================
# AC2 — ORDERING LOCK: pull < migrate < up -d; --plan < migrate; collectstatic < up -d
# =============================================================================


def test_ac2_ordering_docker_pull_before_migrate_and_collectstatic():
    """AC2/AC9/Task 9.1a: `docker compose pull` STRIKTNO PRE migrate/collectstatic.

    Bez ovoga migrate/collectstatic teku kroz STARI image posle GHCR push-a (SM-D5).
    """
    content = _strip_comments(_read_file(DEPLOY_SH))
    pull_idx = _index_of(r"docker\s+compose\s+.*\bpull\b", content)
    migrate_idx = _index_of(r"manage\.py\s+migrate(?!\s+--plan)", content)
    collect_idx = _index_of(r"collectstatic\s+--noinput", content)
    assert pull_idx != -1, "deploy.sh nema `docker compose pull` (AC9 image refresh)."
    assert migrate_idx != -1, "deploy.sh nema `migrate` (apply)."
    assert collect_idx != -1, "deploy.sh nema `collectstatic --noinput`."
    assert pull_idx < migrate_idx, (
        f"ORDERING LOCK PAO: `docker compose pull` (idx {pull_idx}) NIJE pre `migrate` "
        f"(idx {migrate_idx}). AC2/SM-D5: migrate mora teci kroz NOVI pull-ovan image."
    )
    assert pull_idx < collect_idx, (
        f"ORDERING LOCK PAO: `docker compose pull` (idx {pull_idx}) NIJE pre "
        f"`collectstatic` (idx {collect_idx}). AC2/SM-D5: collectstatic kroz novi image."
    )


def test_ac2_ordering_migrate_before_django_restart():
    """AC2 ORDERING LOCK (KRITICNO): `migrate` apply STRIKTNO PRE `up -d django` re-create.

    Sema baze mora biti migrirana pre nego novi Gunicorn worker-i pocnu da sluze
    (inace novi kod udara u staru semu). Inherentni deploy ugovor (forward-dep iz 9.1).
    """
    content = _strip_comments(_read_file(DEPLOY_SH))
    migrate_idx = _index_of(r"manage\.py\s+migrate(?!\s+--plan)", content)
    # `up -d django` (re-create); tolerantno i na `restart django`.
    restart_idx = _index_of(
        r"docker\s+compose\s+.*\bup\s+-d\b[^\n]*\bdjango\b|restart\s+django", content
    )
    assert migrate_idx != -1, "deploy.sh nema `migrate` (apply)."
    assert restart_idx != -1, (
        "deploy.sh nema `up -d django`/`restart django` re-create korak."
    )
    assert migrate_idx < restart_idx, (
        f"ORDERING LOCK PAO: `migrate` (idx {migrate_idx}) NIJE pre `up -d django` "
        f"(idx {restart_idx}). AC2: migrate MORA biti pre re-create-a Gunicorn-a "
        f"(inace novi kod udara u staru semu)."
    )


def test_ac2_ordering_migrate_plan_before_migrate_apply():
    """AC2: `migrate --plan` (pre-check) STRIKTNO PRE `migrate` (apply)."""
    content = _strip_comments(_read_file(DEPLOY_SH))
    plan_idx = _index_of(r"manage\.py\s+migrate\s+--plan", content)
    apply_idx = _index_of(r"manage\.py\s+migrate(?!\s+--plan)", content)
    assert plan_idx != -1, "deploy.sh nema `migrate --plan`."
    assert apply_idx != -1, "deploy.sh nema `migrate` (apply)."
    assert plan_idx < apply_idx, (
        f"ORDERING PAO: `migrate --plan` (idx {plan_idx}) NIJE pre `migrate` apply "
        f"(idx {apply_idx}). AC2: --plan je pre-check pre apply-a."
    )


def test_ac2_ordering_collectstatic_before_restart():
    """AC2: `collectstatic` STRIKTNO PRE re-create-a (static volume svez kad nginx servira)."""
    content = _strip_comments(_read_file(DEPLOY_SH))
    collect_idx = _index_of(r"collectstatic\s+--noinput", content)
    restart_idx = _index_of(
        r"docker\s+compose\s+.*\bup\s+-d\b[^\n]*\bdjango\b|restart\s+django", content
    )
    assert collect_idx != -1, "deploy.sh nema `collectstatic --noinput`."
    assert restart_idx != -1, "deploy.sh nema `up -d django` re-create."
    assert collect_idx < restart_idx, (
        f"ORDERING PAO: `collectstatic` (idx {collect_idx}) NIJE pre re-create-a "
        f"(idx {restart_idx}). AC2: static mora biti svez kad nginx pocne da servira."
    )


# =============================================================================
# AC10 — HEALTHCHECK posle re-create-a (forward-dep iz 9.1)
# =============================================================================


def test_ac10_deploy_sh_has_healthcheck_step():
    """AC10/Task 2.5: deploy.sh MORA imati post-restart healthcheck korak.

    Prihvata `curl -fsS <url>` (retry-loop) ILI `manage.py check --deploy` ILI
    `compose exec django ... check`. Bez healthcheck-a deploy ne fail-uje kad app
    ne odgovori posle re-create-a (tih broken deploy).
    """
    content = _strip_comments(_read_file(DEPLOY_SH))
    health = (
        re.search(r"curl\s+-[A-Za-z]*f[A-Za-z]*[sS]?", content)
        or re.search(r"curl\s+[^\n]*--fail", content)
        or re.search(r"manage\.py\s+check\s+--deploy", content)
        # M4: prod image nema curl → Python urllib urlopen unutar kontejnera je validan healthcheck.
        or re.search(r"urllib\.request\.urlopen|urlopen\(", content)
    )
    assert health, (
        "ops/deploy/deploy.sh nema post-restart healthcheck (`curl -fsS <url>` retry-loop, "
        "`python -c urlopen(...)`, ILI `manage.py check --deploy`). AC10/Task 2.5: deploy MORA "
        "fail-ovati (non-zero exit) ako app ne odgovori posle re-create-a."
    )


def test_ac10_deploy_sh_healthcheck_runs_inside_container():
    """AC10 (M4): healthcheck MORA pogadjati DOSTIZAN target. production.yml NE izlaze django
    :8000 na host (nginx je jedini izlozen ulaz) → bare host `curl 127.0.0.1:8000` = connection
    refused → deploy uvek fail-uje. M4 fix: healthcheck trci UNUTAR django kontejnera
    (`docker compose exec -T django curl ...` ILI `... python -c urlopen`), gde interni :8000
    Gunicorn radi (zaobilazi nginx 301 + cert).

    Lock: linija sa healthcheck curl-om na :8000 (ili check --deploy) MORA biti u
    `docker compose ... exec` kontekstu, NE bare host curl.
    """
    content = _strip_comments(_read_file(DEPLOY_SH))
    # Pronadji healthcheck mehanizam: exec django curl/urlopen ILI check --deploy.
    exec_health = re.search(
        r"docker\s+compose\s+.*\bexec\b[^\n]*\bdjango\b[^\n]*"
        r"(curl|urllib|urlopen|check\s+--deploy)",
        content,
    )
    # Multi-line exec: `docker compose ... exec -T django \` pa curl u sledecoj liniji.
    exec_multiline = re.search(
        r"docker\s+compose\s+.*\bexec\b[^\n]*\bdjango\b[\s\\]*\n\s*"
        r"(curl|python[^\n]*urlopen)",
        content,
    )
    check_deploy = re.search(r"manage\.py\s+check\s+--deploy", content)
    assert exec_health or exec_multiline or check_deploy, (
        "ops/deploy/deploy.sh healthcheck NE trci unutar kontejnera (M4). production.yml NE "
        "izlaze :8000 na host → bare host `curl 127.0.0.1:8000` = connection refused → deploy "
        "uvek fail-uje. Koristi `docker compose exec -T django curl -fsS http://127.0.0.1:8000/sr/` "
        "ILI `... python -c urlopen` ILI `manage.py check --deploy`."
    )


def test_ac10_deploy_sh_healthcheck_after_recreate():
    """AC10 (KRITICNO — positional ordering): healthcheck dolazi POSLE re-create-a
    django/nginx (NE pre).

    Healthcheck pre re-create-a bi testirao STARI kontejner — besmislen. Ovaj test
    parsira pozicije i tvrdi healthcheck STRIKTNO PRE-poslednji (posle `up -d django`).
    """
    content = _strip_comments(_read_file(DEPLOY_SH))
    # Indeks re-create-a django/nginx (poslednji `up -d` re-create korak).
    recreate_matches = list(
        re.finditer(
            r"docker\s+compose\s+.*\bup\s+-d\b[^\n]*\b(django|nginx)\b", content
        )
    )
    health_m = (
        re.search(r"curl\s+-[A-Za-z]*f[A-Za-z]*[sS]?", content)
        or re.search(r"curl\s+[^\n]*--fail", content)
        or re.search(r"manage\.py\s+check\s+--deploy", content)
        # M4: Python urlopen unutar kontejnera (prod image nema curl).
        or re.search(r"urllib\.request\.urlopen|urlopen\(", content)
    )
    assert recreate_matches, (
        "deploy.sh nema `up -d django`/`up -d nginx` re-create korak (AC10 ordering anchor)."
    )
    assert health_m is not None, (
        "deploy.sh nema healthcheck korak (`curl -fsS`/`urlopen`/`check --deploy`). AC10/Task 2.5."
    )
    # Healthcheck mora biti POSLE PRVOG re-create-a (django) — koristi prvi re-create indeks
    # kao donju granicu (healthcheck sleti posle servisa koji se re-kreira).
    first_recreate_idx = recreate_matches[0].start()
    assert health_m.start() > first_recreate_idx, (
        f"ORDERING LOCK PAO: healthcheck (idx {health_m.start()}) NIJE posle re-create-a "
        f"(idx {first_recreate_idx}). AC10: healthcheck verifikuje NOVE kontejnere — mora "
        f"da dodje POSLE `up -d django`/`up -d nginx`, ne pre."
    )


# =============================================================================
# AC3 — IDEMPOTENCY: marker komentar + neinteraktivne komande
# =============================================================================


def test_ac3_deploy_sh_idempotency_marker_comment():
    """AC3: deploy.sh MORA dokumentovati idempotency invariantu komentarom (grep-lock)."""
    content = _read_file(DEPLOY_SH)
    assert re.search(r"idempoten", content, re.IGNORECASE), (
        "ops/deploy/deploy.sh ne dokumentuje idempotency invariantu. "
        "AC3/Task 2.6: komentar-marker (`# idempotentn...`) je obavezan."
    )


def test_ac3_deploy_sh_dirty_tree_and_concurrency_guard():
    """Task 2.4a/2.4b/9.1c (IMPROVEMENT): deploy.sh MORA imati dirty-tree guard
    (`git status --porcelain` ILI `git diff --quiet`) I concurrency lock (`flock`/lockfile).

    Dirty-tree guard sprecava tih polu-deploy na boxu sa nekomitovanim izmenama;
    flock sprecava CI+manual interleave. Oba su imenovana u interface-contract-u —
    best-effort lock (ako Dev guard ugradi, test ga zakljucava).
    """
    content = _strip_comments(_read_file(DEPLOY_SH))
    dirty_guard = re.search(r"git\s+status\s+--porcelain", content) or re.search(
        r"git\s+diff\s+--quiet", content
    )
    concurrency = re.search(r"\bflock\b", content) or re.search(
        r"/var/lock/|\.lock\b|lockfile", content
    )
    assert dirty_guard, (
        "ops/deploy/deploy.sh nema dirty-tree guard (`git status --porcelain` ILI "
        "`git diff --quiet`) PRE `git pull`. Task 2.4a: fail-loud na prljav tree, "
        "NE `git stash`-uj-pa-nastavi."
    )
    assert concurrency, (
        "ops/deploy/deploy.sh nema concurrency lock (`flock`/lockfile). Task 2.4b: "
        "on-box guard protiv CI+manual interleave-a (`exec 200>/var/lock/...; flock -n 200`)."
    )


# =============================================================================
# AC4 — NO FORCE-PUSH (deploy.sh + rollback.sh) — negative grep
# =============================================================================


@pytest.mark.parametrize("script_path", [DEPLOY_SH, ROLLBACK_SH], ids=["deploy", "rollback"])
def test_ac4_no_force_push(script_path):
    """AC4: ni deploy.sh ni rollback.sh ne smeju `push --force`/`-f`/`--force-with-lease`
    / `reset --hard origin`."""
    content = _read_file(script_path)
    forbidden = [
        r"push\s+.*--force\b",
        r"push\s+.*\s-f\b",
        r"--force-with-lease",
        r"reset\s+--hard\s+origin",
    ]
    hits = [pat for pat in forbidden if re.search(pat, content)]
    assert not hits, (
        f"{script_path.name} sadrzi force-push/destruktivan pattern: {hits}. "
        f"AC4/project-context:456: NIKAD force push na deljeni branch — koristi "
        f"`git checkout <tag>` / `git revert`."
    )


# =============================================================================
# AC5 — SECRET INJECTION: nijedan novi fajl ne sadrzi plaintext secret
# =============================================================================


@pytest.mark.parametrize(
    "artifact",
    [DEPLOY_SH, ROLLBACK_SH, NGINX_INIT_SH, DEPLOY_YML, ENV_EXAMPLE, SECRETS_README],
    ids=["deploy_sh", "rollback_sh", "nginx_init_sh", "deploy_yml", "env_example", "secrets_readme"],
)
def test_ac5_no_plaintext_secret_in_new_files(artifact):
    """AC5 NEGATIVE: nijedan novi/azuriran 9.2 fajl NE SME sadrzati plaintext secret
    (PEM private key, hardkodovan ne-prazan POSTGRES_PASSWORD, GitHub PAT)."""
    content = _read_file(artifact)
    found = []
    for pat, desc in _SECRET_LEAK_PATTERNS:
        if re.search(pat, content, re.MULTILINE):
            found.append(desc)
    assert not found, (
        f"{artifact.name} sadrzi sumnjiv plaintext secret pattern: {found}. "
        f"AC5: secrets idu kroz GH secrets / box .env (van repo-a), NIKAD u repo fajl."
    )


def test_ac5_env_example_has_deploy_placeholders():
    """AC5/Task 7.1: `.env.example` MORA imati deploy placeholdere (ACME_EMAIL + domen),
    sa praznim vrednostima (NE realan secret)."""
    content = _read_file(ENV_EXAMPLE)
    assert re.search(r"ACME_EMAIL", content), (
        ".env.example nema `ACME_EMAIL` placeholder. AC5/Task 7.1."
    )
    assert re.search(r"DEPLOY_DOMAIN|DOMAIN", content), (
        ".env.example nema deploy domen placeholder (`DEPLOY_DOMAIN`/`DOMAIN`). Task 7.1."
    )


# =============================================================================
# AC6 — CERT PROVISIONING + AUTO-RENEWAL: nginx-init.sh
# =============================================================================


def test_ac6_nginx_init_sh_exists():
    """AC6/Task 4: `ops/nginx/nginx-init.sh` MORA postojati."""
    assert NGINX_INIT_SH.exists(), (
        f"Missing required file: {NGINX_INIT_SH}\n"
        f"AC6/Task 4: certbot webroot + bootstrap + auto-renewal."
    )


def test_ac6_nginx_init_sh_set_euo_pipefail_and_lf():
    """AC6/G-1: nginx-init.sh `set -euo pipefail` + LF."""
    content = _read_file(NGINX_INIT_SH)
    assert re.search(r"set\s+-euo\s+pipefail", content), (
        "ops/nginx/nginx-init.sh nema `set -euo pipefail`."
    )
    assert _has_lf_only(NGINX_INIT_SH), (
        "ops/nginx/nginx-init.sh ima CRLF (G-1: bash u Linux ne tolerise CRLF)."
    )


def test_ac6_nginx_init_sh_certbot_certonly_webroot():
    """AC6: nginx-init.sh MORA pozivati `certbot certonly --webroot -w /var/www/certbot`."""
    content = _read_file(NGINX_INIT_SH)
    assert re.search(r"certbot\s+certonly", content), (
        "ops/nginx/nginx-init.sh ne poziva `certbot certonly`. AC6: Let's Encrypt issuance."
    )
    assert re.search(r"--webroot", content), (
        "ops/nginx/nginx-init.sh nema `--webroot` metod (AC6/AC13 webroot challenge)."
    )
    assert re.search(rf"-w\s+{re.escape(ACME_WEBROOT)}", content), (
        f"ops/nginx/nginx-init.sh certbot `-w` putanja nije `{ACME_WEBROOT}`. "
        f"AC13/SM-D4: webroot path je KONKRETAN i usklađen sa nginx ACME root + bind-mount."
    )


def test_ac6_nginx_init_sh_auto_renewal():
    """AC6/Task 4.5: nginx-init.sh MORA registrovati auto-renewal (cron `certbot renew`
    ILI systemd timer) sa deploy-hook reload."""
    content = _read_file(NGINX_INIT_SH)
    renewal = re.search(r"certbot\s+renew", content) or re.search(
        r"systemd|\.timer|OnCalendar", content
    )
    assert renewal, (
        "ops/nginx/nginx-init.sh nema auto-renewal (cron `certbot renew` ili systemd timer). "
        "AC6/Task 4.5: cert se obnavlja ~1x mesecno."
    )
    assert re.search(r"--deploy-hook|nginx\s+-s\s+reload", content), (
        "ops/nginx/nginx-init.sh nema `--deploy-hook`/`nginx -s reload` u renewal-u. "
        "AC6/Task 4.5: posle obnove nginx mora reload-ovati cert."
    )


def test_ac6_nginx_init_sh_renewal_failure_visibility():
    """AC6/Task 4.5a: renewal neuspeh MORA biti VIDLJIV (|| echo ... >&2 ILI systemd OnFailure).

    Tihi neuspeh = istekao cert = sajt nedostupan 60-90 dana kasnije.
    """
    content = _read_file(NGINX_INIT_SH)
    # Tightened: failure-vidljivost MORA biti vezana za `certbot renew` (ne bilo koji `>&2`
    # bilo gde). Prihvata: (a) renew red sa `|| ... >&2` (cron/inline failure surface),
    # (b) `--deploy-hook` failure path, ili (c) systemd `OnFailure=` uz renew timer.
    # `[\s\S]*?` dozvoljava da `certbot renew` i `|| ... >&2` budu na istoj logickoj liniji
    # (cron CRON_LINE) ili u bliskom bloku, ali zahteva da par zaista postoji.
    renew_then_stderr = re.search(
        r"certbot\s+renew[\s\S]{0,400}?\|\|[\s\S]{0,120}?>&2", content
    )
    onfailure = re.search(r"OnFailure=", content)
    assert renew_then_stderr or onfailure, (
        "ops/nginx/nginx-init.sh nema renewal-failure vidljivost VEZANU za `certbot renew`. "
        "Task 4.5a: `certbot renew ... || echo 'CERT RENEWAL FAILED' >&2` ILI systemd "
        "`OnFailure=` (tih neuspeh = istekao cert = sajt down 60-90 dana)."
    )


def test_ac6_nginx_init_sh_idempotency_guard():
    """AC6/AC15: nginx-init.sh MORA imati idempotency guard (preskoci ako cert vec postoji)."""
    content = _read_file(NGINX_INIT_SH)
    assert re.search(r"fullchain\.pem", content), (
        "ops/nginx/nginx-init.sh nema cert-existence referencu (`fullchain.pem`). "
        "AC6/AC15: idempotency guard preskace izdavanje ako "
        "`/etc/letsencrypt/live/<domen>/fullchain.pem` postoji."
    )


def test_ac6_nginx_init_sh_domain_email_parametrized():
    """AC6/Task 4.2: DOMAIN + ACME_EMAIL parametrizovani (env/arg, ne hardkodovani gde razumno)."""
    content = _read_file(NGINX_INIT_SH)
    assert re.search(r"\$\{?DOMAIN", content) or re.search(r"\$\{?DEPLOY_DOMAIN", content), (
        "ops/nginx/nginx-init.sh ne parametrizuje DOMAIN (env var). AC6/SM-D2/Task 4.2."
    )
    assert re.search(r"\$\{?ACME_EMAIL", content), (
        "ops/nginx/nginx-init.sh ne parametrizuje ACME_EMAIL (env var). AC6/Task 4.2."
    )


# =============================================================================
# AC7 — NGINX 443/HTTPS EXTENSION: nginx.conf aktivan 443 blok
# =============================================================================


def test_ac7_nginx_conf_listen_443_ssl_active():
    """AC7: nginx.conf MORA imati AKTIVAN (ne zakomentarisan) `listen 443 ssl;` blok."""
    content = _read_file(NGINX_CONF)
    active = [
        ln for ln in content.splitlines()
        if re.search(r"listen\s+443\s+ssl", ln) and not ln.lstrip().startswith("#")
    ]
    assert active, (
        "compose/nginx/nginx.conf nema AKTIVAN `listen 443 ssl;` (samo zakomentarisan "
        "placeholder iz 9.1). AC7: 9.2 odkomentarisava + aktivira 443 blok."
    )


def test_ac7_nginx_conf_ssl_certificate_paths():
    """AC7: nginx.conf MORA imati AKTIVNE `ssl_certificate` + `ssl_certificate_key`
    (Let's Encrypt putanje)."""
    content = _read_file(NGINX_CONF)
    cert = [
        ln for ln in content.splitlines()
        if re.search(r"ssl_certificate\s+\S", ln) and not ln.lstrip().startswith("#")
    ]
    key = [
        ln for ln in content.splitlines()
        if re.search(r"ssl_certificate_key\s+\S", ln) and not ln.lstrip().startswith("#")
    ]
    assert cert, "nginx.conf nema aktivan `ssl_certificate`. AC7."
    assert key, "nginx.conf nema aktivan `ssl_certificate_key`. AC7."
    assert re.search(r"/etc/letsencrypt/live/[^/]+/fullchain\.pem", content), (
        "nginx.conf ssl_certificate ne pokazuje na `/etc/letsencrypt/live/<domen>/"
        "fullchain.pem`. AC7/AC13."
    )


def test_ac7_nginx_conf_acme_location_root_webroot():
    """AC7/AC13: nginx.conf MORA imati `location /.well-known/acme-challenge/` sa
    `root /var/www/certbot;`."""
    content = _read_file(NGINX_CONF)
    assert re.search(r"location\s+/\.well-known/acme-challenge/", content), (
        "nginx.conf nema `location /.well-known/acme-challenge/`. AC7: ACME challenge "
        "servira certbot webroot."
    )
    assert re.search(rf"root\s+{re.escape(ACME_WEBROOT)}\s*;", content), (
        f"nginx.conf ACME location nema `root {ACME_WEBROOT};`. AC7/AC13/SM-D4: "
        f"path mora biti KONKRETAN i usklađen sa certbot `-w`."
    )


def test_ac7_nginx_conf_http_to_https_301_redirect():
    """AC7: nginx.conf :80 blok MORA imati `return 301 https://...` (HTTP->HTTPS redirect)."""
    content = _read_file(NGINX_CONF)
    redirect = [
        ln for ln in content.splitlines()
        if re.search(r"return\s+301\s+https://", ln) and not ln.lstrip().startswith("#")
    ]
    assert redirect, (
        "nginx.conf nema aktivan `return 301 https://$host$request_uri;`. "
        "AC7/SM-D6: bezuslovan HTTP->HTTPS redirect za sav saobracaj OSIM ACME-a."
    )


def test_ac7_acme_location_not_redirected():
    """AC7 (KRITICNO): ACME challenge location NE SME imati `return 301` (challenge mora
    da se servira 200/404, ne redirect).

    Scope-ovano NA AKTIVNE (non-comment) linije nginx conf-a — zakomentarisan `return 301`
    NE sme lazno da fail-uje test, niti sme da se pokupi 443-block ACME location. Ekstrakcija
    tela ide kroz _active_lines + DOTALL na realnom (izvrsnom) sadrzaju.
    """
    content = _active_lines(_read_file(NGINX_CONF))
    # Izvuci ACME location blok (iz aktivnih linija) i proveri da unutra nema return 301.
    m = re.search(
        r"location\s+/\.well-known/acme-challenge/\s*\{(.*?)\}",
        content,
        re.DOTALL,
    )
    assert m is not None, (
        "nginx.conf nema parsabilan `location /.well-known/acme-challenge/ { ... }` blok "
        "(potreban za AC7 not-redirected proveru)."
    )
    acme_body = m.group(1)
    assert not re.search(r"return\s+301", acme_body), (
        "nginx.conf ACME location SADRZI `return 301` — challenge se redirect-uje na HTTPS, "
        "sto LOMI certbot validaciju. AC7/SM-D6: ACME location ostaje 200/404, NIKAD 301."
    )


def test_ac7_nginx_conf_443_security_headers():
    """AC7 (KRITICNO): AKTIVAN 443 blok MORA re-emitovati sva 3 security headera (`always`).

    Scope-ovano NA 443 server blok (NE globalno na sve aktivne linije) — inace 9.1
    :80 blok (koji vec ima 3 headera) lazno zadovoljava 9.2 443-kontrakt (premature
    satisfaction). Ovaj test MORA biti RED dok Dev ne aktivira 443 blok sa headerima.
    """
    content = _read_file(NGINX_CONF)
    block = _extract_443_server_block(content)
    assert block is not None, (
        "compose/nginx/nginx.conf nema AKTIVAN `server { ... listen 443 ssl ... }` blok "
        "(samo zakomentarisan 9.1 placeholder). AC7: 9.2 aktivira 443 blok. "
        "Security-header asercija je scope-ovana NA 443 blok da 9.1 :80 headeri NE "
        "zadovolje 9.2 kontrakt lazno."
    )
    expected = {
        "X-Frame-Options": r'add_header\s+X-Frame-Options\s+["\']?DENY["\']?\s+always',
        "X-Content-Type-Options": r'add_header\s+X-Content-Type-Options\s+["\']?nosniff["\']?\s+always',
        "Referrer-Policy": r'add_header\s+Referrer-Policy\s+["\']?same-origin["\']?\s+always',
    }
    missing = [name for name, pat in expected.items() if not re.search(pat, block)]
    assert not missing, (
        f"nginx.conf 443 server blok nema security headere: {missing}. "
        f"AC7: 443 blok re-emituje sva 3 headera sa `always` (re-emit jer nginx "
        f"location add_header DROPUJE nasledjene)."
    )


def test_ac7_nginx_conf_443_ssl_protocols_hardened():
    """AC7 (TLS HARDENING): AKTIVAN 443 server blok MORA imati `ssl_protocols` sa SAMO
    TLSv1.2 + TLSv1.3 (i NE legacy TLSv1.0/TLSv1.1).

    Scope-ovano NA 443 blok (reuse _extract_443_server_block) — bez ovog lock-a dev moze
    tiho izbaciti TLS hardening i ostali AC7 testovi i dalje prolaze (gap).
    """
    content = _read_file(NGINX_CONF)
    block = _extract_443_server_block(content)
    assert block is not None, (
        "compose/nginx/nginx.conf nema AKTIVAN 443 server blok (samo zakomentarisan "
        "9.1 placeholder). AC7: ssl_protocols asercija je scope-ovana na 443."
    )
    m = re.search(r"ssl_protocols\s+([^;]+);", block)
    assert m is not None, (
        "nginx.conf 443 blok nema `ssl_protocols ...;`. AC7: TLS hardening je obavezan "
        "(`ssl_protocols TLSv1.2 TLSv1.3;`)."
    )
    protocols = m.group(1).split()
    assert "TLSv1.2" in protocols and "TLSv1.3" in protocols, (
        f"nginx.conf 443 `ssl_protocols` = {protocols!r}, mora sadrzati TLSv1.2 + TLSv1.3. AC7."
    )
    legacy = [p for p in protocols if p in ("TLSv1", "TLSv1.0", "TLSv1.1", "SSLv2", "SSLv3")]
    assert not legacy, (
        f"nginx.conf 443 `ssl_protocols` sadrzi legacy/nesigurne protokole: {legacy}. "
        f"AC7: dozvoljeni su SAMO TLSv1.2 + TLSv1.3."
    )


def test_ac7_nginx_conf_x_forwarded_proto_present():
    """AC7/G-3 (KRITICNO): 443 blok MORA imati `proxy_set_header X-Forwarded-Proto $scheme`.

    Scope-ovano NA 443 blok — 9.1 :80 blok vec ima ovaj header, pa globalni grep bi
    lazno prosao na pre-9.2 stanju (premature satisfaction). RED dok Dev ne aktivira 443.
    """
    content = _read_file(NGINX_CONF)
    block = _extract_443_server_block(content)
    assert block is not None, (
        "compose/nginx/nginx.conf nema AKTIVAN 443 server blok (samo zakomentarisan "
        "9.1 placeholder). AC7/G-3: X-Forwarded-Proto asercija je scope-ovana na 443."
    )
    assert re.search(r"proxy_set_header\s+X-Forwarded-Proto\s+\$scheme\s*;", block), (
        "nginx.conf 443 blok nema `proxy_set_header X-Forwarded-Proto $scheme;`. "
        "G-3: bez ovoga Django (SECURE_SSL_REDIRECT) ulazi u 301 redirect loop."
    )


def test_ac7_regression_http_static_media_still_present():
    """AC7/AC12 REGRESSION: 9.1 HTTP/80 `location /static/` + `/media/` ostaju (aktivni)."""
    content = "\n".join(
        ln for ln in _read_file(NGINX_CONF).splitlines() if not ln.lstrip().startswith("#")
    )
    assert re.search(r"location\s+/static/", content), (
        "nginx.conf vise nema aktivan `location /static/` (9.1 regresija). AC7/AC12."
    )
    assert re.search(r"location\s+/media/", content), (
        "nginx.conf vise nema aktivan `location /media/` (9.1 regresija). AC7/AC12."
    )


# =============================================================================
# AC15 — FIRST-DEPLOY BOOTSTRAP: nginx.bootstrap.conf (HTTP-only, NO 443)
# =============================================================================


def test_ac15_bootstrap_conf_exists():
    """AC15/Task 9.2b: `compose/nginx/nginx.bootstrap.conf` MORA postojati."""
    assert NGINX_BOOTSTRAP_CONF.exists(), (
        f"Missing required file: {NGINX_BOOTSTRAP_CONF}\n"
        f"AC15/SM-D10: HTTP-only bootstrap conf za first-deploy (resava chicken-and-egg)."
    )


def test_ac15_bootstrap_conf_has_acme_location():
    """AC15: bootstrap conf MORA imati :80 ACME location (`root /var/www/certbot`)."""
    content = _read_file(NGINX_BOOTSTRAP_CONF)
    assert re.search(r"location\s+/\.well-known/acme-challenge/", content), (
        "nginx.bootstrap.conf nema `location /.well-known/acme-challenge/`. "
        "AC15: bootstrap :80 mora servirati ACME challenge da certbot izda cert."
    )
    assert re.search(rf"root\s+{re.escape(ACME_WEBROOT)}", content), (
        f"nginx.bootstrap.conf ACME location nema `root {ACME_WEBROOT}`. AC13/AC15."
    )


def test_ac15_bootstrap_conf_has_no_443_ssl():
    """AC15/Task 9.2b (KRITICNO): bootstrap conf NEMA nijedan `listen 443 ssl`.

    Na svezem boxu nginx sa 443 koji referencira nepostojeci cert FAIL-uje da starta.
    """
    content = _read_file(NGINX_BOOTSTRAP_CONF)
    active_443 = [
        ln for ln in content.splitlines()
        if re.search(r"listen\s+443\s+ssl", ln) and not ln.lstrip().startswith("#")
    ]
    assert not active_443, (
        f"nginx.bootstrap.conf SADRZI `listen 443 ssl`: {active_443}. AC15/SM-D10: "
        f"bootstrap je HTTP-only (nginx mora startati BEZ cert-a za prvi ACME challenge)."
    )


# =============================================================================
# AC13 — CERT-PATH CONTRACT: certbot -w == nginx ACME root == /var/www/certbot
# =============================================================================


def test_ac13_cert_path_contract_webroot_identical():
    """AC13/Task 9.3a (PATH-CONSISTENCY LOCK): certbot `-w` putanja iz nginx-init.sh
    == nginx.conf ACME `root` putanja == /var/www/certbot."""
    init_content = _read_file(NGINX_INIT_SH)
    conf_content = _read_file(NGINX_CONF)

    # Robustno izvuci certbot webroot iz IZVRSNIH (non-comment) linija, usidreno uz
    # `--webroot`/`certbot` kontekst — da `re.search(-w \S+)` na sirovom sadrzaju ne pokupi
    # komentar-marker ili continuation backslash umesto realnog `-w <path>` flag-a.
    init_exec = _strip_comments(init_content)
    init_w = (
        re.search(r"--webroot\s+-w\s+(\S+)", init_exec)
        or re.search(r"certbot\b[^\n]*\s-w\s+(\S+)", init_exec)
        or re.search(r"(?<!\S)-w\s+(\S+)", init_exec)
    )
    assert init_w is not None, (
        "nginx-init.sh nema certbot `-w <path>` u izvrsnoj liniji. AC13: webroot path je obavezan."
    )
    init_path = init_w.group(1).strip("\"'")

    conf_root = re.search(
        r"location\s+/\.well-known/acme-challenge/\s*\{[^}]*?root\s+(\S+?)\s*;",
        conf_content,
        re.DOTALL,
    )
    assert conf_root is not None, (
        "nginx.conf ACME location nema `root <path>;`. AC13."
    )
    conf_path = conf_root.group(1)

    assert init_path == conf_path == ACME_WEBROOT, (
        f"CERT-PATH CONTRACT PAO: certbot -w = {init_path!r}, nginx ACME root = "
        f"{conf_path!r}, ocekivano oba = {ACME_WEBROOT!r}. AC13/SM-D4: ako se ne "
        f"poklapaju, ACME validacija FAIL-uje (challenge nedostupan)."
    )


def test_ac13_production_yml_nginx_has_cert_and_webroot_bind_mounts():
    """AC13/Task 9.3a: production.yml nginx servis MORA imati oba bind-mount-a
    (`/etc/letsencrypt:ro` + `/var/www/certbot:ro`)."""
    data = _parse_yaml(PRODUCTION_YML)
    nginx = data.get("services", {}).get("nginx", {})
    volumes = nginx.get("volumes", []) or []
    vol_blob = "\n".join(str(v) for v in volumes)
    assert re.search(r"/etc/letsencrypt:/etc/letsencrypt:ro", vol_blob), (
        f"production.yml nginx servis nema `/etc/letsencrypt:/etc/letsencrypt:ro` "
        f"bind-mount. AC13: cert read-only za nginx (ssl_certificate resolve). "
        f"Pronadjeno volumes: {volumes}"
    )
    assert re.search(rf"{re.escape(ACME_WEBROOT)}:{re.escape(ACME_WEBROOT)}:ro", vol_blob), (
        f"production.yml nginx servis nema `{ACME_WEBROOT}:{ACME_WEBROOT}:ro` bind-mount. "
        f"AC13: ACME webroot read-only za nginx. Pronadjeno volumes: {volumes}"
    )


# =============================================================================
# AC14 — NGINX.CONF REACHABILITY: bind-mount + deploy reload
# =============================================================================


def test_ac14_production_yml_nginx_conf_bind_mount():
    """AC14/Task 9.2a (MEHANIZAM LOCK + M1): production.yml nginx servis MORA bind-mount-ovati
    SWAP fajl `.active-default.conf -> /etc/nginx/conf.d/default.conf` (NE direktno nginx.conf).

    M1 (CRITICAL): bind-mount mora ciljati SWAPPABLE fajl koji nginx-init.sh popunjava
    (bootstrap conf PRE certbot-a, pun nginx.conf POSLE). Da je mount-ovan direktno
    nginx.conf, bootstrap swap u nginx-init.sh bi bio INERTAN (nista ne mount-uje
    .active-default.conf) → na svezem boxu nginx starta sa 443 + nepostojeci cert → fail →
    certbot ACME nikad ne moze da se servira → prvi cert se nikad ne izda (AC15 mrtav).
    """
    data = _parse_yaml(PRODUCTION_YML)
    nginx = data.get("services", {}).get("nginx", {})
    volumes = nginx.get("volumes", []) or []
    vol_blob = "\n".join(str(v) for v in volumes)
    assert re.search(
        r"\./nginx/\.active-default\.conf:/etc/nginx/conf\.d/default\.conf:ro", vol_blob
    ), (
        f"production.yml nginx servis nema bind-mount `./nginx/.active-default.conf:"
        f"/etc/nginx/conf.d/default.conf:ro` (M1 swappable conf). Bez swappable target-a "
        f"bootstrap swap u nginx-init.sh je INERTAN → prvi cert se nikad ne izda (AC15). "
        f"Pronadjeno volumes: {volumes}"
    )
    # Negative: NE sme direktno mount-ovati nginx.conf (M1 — to bi ucinilo swap inertnim).
    assert not re.search(
        r"\./nginx/nginx\.conf:/etc/nginx/conf\.d/default\.conf", vol_blob
    ), (
        "production.yml nginx servis mount-uje direktno `./nginx/nginx.conf` umesto "
        "`.active-default.conf` (M1): bootstrap swap bi bio inertan. Mount swappable fajl."
    )


def test_ac14_production_yml_still_valid_yaml():
    """AC14/AC12: production.yml mora ostati validan YAML sa django/postgres/nginx servisima
    (EXTEND ne lomi 9.1 strukturu)."""
    data = _parse_yaml(PRODUCTION_YML)
    services = data.get("services", {})
    missing = [s for s in ("postgres", "django", "nginx") if s not in services]
    assert not missing, (
        f"production.yml nedostaju servisi posle 9.2 EXTEND-a: {missing}. "
        f"AC12: 9.2 dodaje SAMO nginx bind-mount-ove, NE dira postgres/django."
    )


def test_ac14_deploy_sh_nginx_reload_step():
    """AC14/Task 9.1b (NGINX-RELOAD LOCK): deploy.sh MORA imati nginx re-create/reload korak
    (`up -d nginx` ILI `exec nginx ... -s reload`), NE samo `restart django`."""
    content = _strip_comments(_read_file(DEPLOY_SH))
    reload_step = (
        re.search(r"docker\s+compose\s+.*\bup\s+-d\b[^\n]*\bnginx\b", content)
        or re.search(r"exec\s+nginx[^\n]*nginx\s+-s\s+reload", content)
        or re.search(r"nginx\s+-s\s+reload", content)
    )
    assert reload_step, (
        "ops/deploy/deploy.sh nema nginx re-create/reload korak. AC14/SM-D9: "
        "`up -d nginx` ILI `exec nginx nginx -s reload` (bind-mount conf pokupi). "
        "Goli `restart django` NE dostize nginx.conf izmenu."
    )


# =============================================================================
# AC15 — bootstrap-before-certbot ordering u nginx-init.sh
# =============================================================================


def test_ac15_nginx_init_bootstrap_before_certbot_swap_after():
    """AC15/Task 9.3 (BOOTSTRAP ORDERING + M1 swap-after): nginx-init.sh kopira bootstrap
    conf u .active-default.conf PRE certbot poziva, pa kopira pun nginx.conf u
    .active-default.conf POSLE certbot poziva.

    M1: TEA je flag-ovao da swap-after assertion nedostaje. Sada eksplicitno tvrdimo:
      idx(cp bootstrap -> .active-default.conf) < idx(certbot) < idx(cp nginx.conf -> .active-default.conf)
    Bez full-conf-swap-a POSLE certbot-a, nginx bi ostao na HTTP-only bootstrap-u i 443
    nikad ne bi startovao (cert postoji ali se ne servira).
    """
    content = _strip_comments(_read_file(NGINX_INIT_SH))
    bootstrap_idx = _index_of(r"nginx\.bootstrap\.conf", content)
    certbot_idx = _index_of(r"certbot\s+certonly", content)
    assert bootstrap_idx != -1, (
        "nginx-init.sh ne referencira `nginx.bootstrap.conf`. AC15: bootstrap faza."
    )
    assert certbot_idx != -1, (
        "nginx-init.sh nema `certbot certonly` poziv. AC15."
    )
    assert bootstrap_idx < certbot_idx, (
        f"BOOTSTRAP ORDERING PAO: `nginx.bootstrap.conf` (idx {bootstrap_idx}) NIJE pre "
        f"`certbot certonly` (idx {certbot_idx}). AC15/SM-D10: HTTP-only bootstrap mora "
        f"da digne nginx PRE certbot challenge-a."
    )

    # M1: swap na PUN nginx.conf POSLE certbot-a — `cp ...nginx.conf ...active-default`.
    # Nadji prvi `cp <nginx.conf> -> .active-default.conf` posle certbot indeksa.
    full_swap_iter = list(
        re.finditer(
            r"cp\s+\S*nginx\.conf\s+\S*\.active-default\.conf|"
            r"cp\s+\S*nginx\.conf\s+\"?\$\{?ACTIVE_CONF",
            content,
        )
    )
    full_swap_after = [m for m in full_swap_iter if m.start() > certbot_idx]
    assert full_swap_after, (
        "nginx-init.sh ne kopira PUN nginx.conf u .active-default.conf POSLE certbot-a "
        "(M1 swap-after). Bez ovoga nginx ostaje na HTTP-only bootstrap-u i 443 ne starta. "
        "Ocekivano: `cp compose/nginx/nginx.conf \"${ACTIVE_CONF}\"` posle certbot poziva."
    )

    # I bootstrap conf se kopira u .active-default.conf PRE certbot-a (M1 mount-real).
    bootstrap_swap_iter = list(
        re.finditer(
            r"cp\s+\S*nginx\.bootstrap\.conf\s+\S*\.active-default\.conf|"
            r"cp\s+\"?\$\{?BOOTSTRAP_CONF[^\n]*\.active-default\.conf|"
            r"cp\s+\"?\$\{?BOOTSTRAP_CONF[^\n]*ACTIVE_CONF",
            content,
        )
    )
    bootstrap_swap_before = [m for m in bootstrap_swap_iter if m.start() < certbot_idx]
    assert bootstrap_swap_before, (
        "nginx-init.sh ne kopira bootstrap conf u .active-default.conf PRE certbot-a (M1). "
        "Bind-mount cilja .active-default.conf — bootstrap mora biti kopiran TAMO da nginx "
        "stvarno servira HTTP-only conf tokom ACME challenge-a."
    )


# =============================================================================
# AC11 — ROLLBACK: ops/deploy/rollback.sh
# =============================================================================


def test_ac11_rollback_sh_exists():
    """AC11/Task 3: `ops/deploy/rollback.sh` MORA postojati."""
    assert ROLLBACK_SH.exists(), (
        f"Missing required file: {ROLLBACK_SH}\n"
        f"AC11/Task 3: checkout prethodnog tag-a/commit-a + redeploy."
    )


def test_ac11_rollback_sh_set_euo_pipefail_and_lf():
    """AC11: rollback.sh `set -euo pipefail` + LF."""
    content = _read_file(ROLLBACK_SH)
    assert re.search(r"set\s+-euo\s+pipefail", content), (
        "ops/deploy/rollback.sh nema `set -euo pipefail`. AC11."
    )
    assert _has_lf_only(ROLLBACK_SH), (
        "ops/deploy/rollback.sh ima CRLF (G-1)."
    )


def test_ac11_rollback_sh_git_checkout_previous():
    """AC11: rollback.sh MORA `git checkout <tag/commit>` (revert na prethodni)."""
    content = _read_file(ROLLBACK_SH)
    assert re.search(r"git\s+checkout", content), (
        "ops/deploy/rollback.sh nema `git checkout`. AC11/Task 3.3: checkout prethodnog "
        "tag-a/commit-a, NE force-rewrite istorije."
    )


def test_ac11_rollback_sh_irreversible_migration_warning():
    """AC11/Task 3.4a: rollback.sh MORA GLASNO upozoriti na ireverzibilnu migraciju
    (stderr) PRE redeploy-a (svestan migrate-down tretman, SM-D3)."""
    content = _read_file(ROLLBACK_SH)
    has_warning = (
        re.search(r">&2", content)
        and re.search(r"migrac|migration|migrate", content, re.IGNORECASE)
    )
    assert has_warning, (
        "ops/deploy/rollback.sh nema irreversible-migration upozorenje na stderr. "
        "AC11/Task 3.4a/SM-D3: GLASNO warn (`echo ... >&2`) da auto migrate-down "
        "NIJE uradjen (data-loss rizik) — rucna DBA intervencija ako je sema "
        "nereverzibilna."
    )


def test_ac11_rollback_sh_no_auto_migrate_down_by_default():
    """AC11/SM-D3: rollback.sh NE SME imati bezuslovan auto `migrate <app> <prev>` u
    izvrsnoj liniji (data-loss). Migrate-down je SVESTAN/opcioni, ne default."""
    content = _strip_comments(_read_file(ROLLBACK_SH))
    # Trazi izvrsni migrate sa eksplicitnom ciljnom (prethodnom) migracijom: `migrate app 0001`.
    # Tolerisemo guard-ovan/uslovni (npr. unutar `if [ -n "$2" ]`) jer SM-D3 dozvoljava
    # opcioni argument — ali bezuslovan literal `migrate app <number>` na top-level je leak.
    bad = re.search(r"^\s*[^#\n]*manage\.py\s+migrate\s+\w+\s+\d{4}", content, re.MULTILINE)
    assert not bad, (
        "ops/deploy/rollback.sh ima bezuslovan auto migrate-down (`migrate <app> <num>`). "
        "AC11/SM-D3: default NE sme auto-migrate-down (data-loss); samo opcioni/guard-ovan."
    )


# =============================================================================
# AC8 — DEPLOY.YML SSH: .github/workflows/deploy.yml
# =============================================================================


def test_ac8_deploy_yml_exists():
    """AC8/Task 6: `.github/workflows/deploy.yml` MORA postojati."""
    assert DEPLOY_YML.exists(), (
        f"Missing required file: {DEPLOY_YML}\n"
        f"AC8/Task 6: SSH deploy workflow na Hetzner."
    )


def test_ac8_deploy_yml_valid_yaml():
    """AC8: deploy.yml mora biti validan YAML sa `jobs:` blokom."""
    data = _parse_yaml(DEPLOY_YML)
    assert isinstance(data, dict) and "jobs" in data, (
        "deploy.yml nije validan workflow YAML (nema `jobs:`). AC8."
    )


def test_ac8_deploy_yml_trigger_branches_locked():
    """AC8/SM-D1/OQ-1: deploy.yml `on.push.branches` MORA matchovati story-locked vrednost
    `{staging, main}` (sa tolerancijom za `{master}` ako Mihas zadrzi default)."""
    data = _parse_yaml(DEPLOY_YML)
    on_block = _get_on_block(data)
    branches = on_block.get("push", {}).get("branches", [])
    branch_set = set(branches) if isinstance(branches, list) else {branches}
    ok = branch_set == EXPECTED_DEPLOY_BRANCHES or branch_set == TOLERATED_DEPLOY_BRANCHES or (
        branch_set and branch_set <= (EXPECTED_DEPLOY_BRANCHES | TOLERATED_DEPLOY_BRANCHES)
    )
    assert ok and branch_set, (
        f"deploy.yml `on.push.branches` = {branches!r}. SM-D1: story LOCK-uje "
        f"{sorted(EXPECTED_DEPLOY_BRANCHES)} (ili tolerantno {sorted(TOLERATED_DEPLOY_BRANCHES)} "
        f"po OQ-1). Trigger ne sme biti prazan/hardkodovan na pogresno."
    )


def test_ac8_deploy_yml_ssh_via_secrets_no_hardcoded_key():
    """AC8: deploy.yml MORA koristiti SSH kroz `${{ secrets.* }}` (key/host/user),
    NIKAD hardkodovan privatni kljuc."""
    raw = _read_file(DEPLOY_YML)
    assert re.search(r"secrets\.", raw), (
        "deploy.yml ne referencira `${{ secrets.* }}` (SSH key/host/user). AC8: "
        "kredencijali idu kroz GH secrets, ne inline."
    )
    # Negative: nema PEM private key bloka (vec pokriveno AC5 parametrize, dupli lock ovde).
    assert not re.search(r"BEGIN [A-Z ]*PRIVATE KEY", raw), (
        "deploy.yml sadrzi inline PEM private key. AC8: NIKAD hardkodovan kljuc."
    )


def test_ac8_deploy_yml_calls_deploy_sh():
    """AC8: deploy.yml remote komanda MORA pozivati `ops/deploy/deploy.sh`."""
    raw = _read_file(DEPLOY_YML)
    assert re.search(r"ops/deploy/deploy\.sh", raw), (
        "deploy.yml ne poziva `ops/deploy/deploy.sh`. AC8: remote SSH komanda pokrece "
        "deploy skriptu sa env argumentom."
    )


def test_ac8_deploy_yml_least_privilege_permissions():
    """AC8: deploy.yml MORA imati `permissions: contents: read` (least-privilege)."""
    data = _parse_yaml(DEPLOY_YML)
    permissions = data.get("permissions", {})
    # Tolerantno: workflow-level ILI job-level contents:read.
    has_wf = isinstance(permissions, dict) and permissions.get("contents") == "read"
    has_job = False
    for job in (data.get("jobs", {}) or {}).values():
        if isinstance(job, dict):
            jp = job.get("permissions", {})
            if isinstance(jp, dict) and jp.get("contents") == "read":
                has_job = True
    assert has_wf or has_job, (
        f"deploy.yml nema `permissions: contents: read` (workflow ili job nivo). "
        f"AC8/Task 6.1: least-privilege. Workflow-level: {permissions!r}."
    )


def test_ac8_deploy_yml_does_not_build_push_image():
    """AC8/AC9/SM-D7: deploy.yml NE SME graditi/push-ovati image (`build-push-action`).
    GHCR push je KANONSKI u ci.yml (izbegava dupli build)."""
    raw = _read_file(DEPLOY_YML)
    assert not re.search(r"docker/build-push-action", raw), (
        "deploy.yml sadrzi `docker/build-push-action`. SM-D7: deploy.yml SAMO SSH-uje + "
        "pokrece deploy.sh; GHCR build+push je u ci.yml build job-u (KANONSKA lokacija)."
    )


# =============================================================================
# AC9 — GHCR LOGIN + PUSH u ci.yml build job (deferred iz 9.1 aktiviran)
# =============================================================================


def test_ac9_production_yml_django_image_is_ghcr_pathed():
    """AC9 (M2): production.yml django servis `image:` MORA biti GHCR-pathed (`ghcr.io/...`)
    sa deterministickim/env-parametrizovanim tag-om — inace `docker compose pull` NE moze da
    resolve-uje lokalno ime (`coric_agrar_django_production`) na GHCR → box nikad ne pokrene
    CI-zgradjen image (AC9 konzumacija slomljena).

    build: blok ostaje (lokalni fallback), ali image: MORA biti GHCR putanja da `pull` radi.
    """
    data = _parse_yaml(PRODUCTION_YML)
    django = data.get("services", {}).get("django", {})
    image = django.get("image", "")
    assert isinstance(image, str) and image.startswith("ghcr.io/"), (
        f"production.yml django `image:` = {image!r}, ocekivano da pocinje sa `ghcr.io/`. "
        f"M2: lokalno ime se ne moze `pull`-ovati sa GHCR → box pokrece STARI image posle "
        f"CI push-a. Koristi `ghcr.io/${{GHCR_IMAGE:-...}}:${{IMAGE_TAG:-latest}}`."
    )


def test_ac9_ci_yml_build_pushes_stable_tag():
    """AC9 (M2): ci.yml build-push MORA push-ovati STABILAN per-branch tag (ne samo
    :ci-<sha>) koji deploy.sh `docker compose pull` resolve-uje. production.yml default-uje
    na :latest, pa CI mora push-ovati bar jedan stabilan tag pored immutable :ci-<sha>."""
    data = _parse_yaml(CI_YML)
    build = data.get("jobs", {}).get("build", {})
    push_step = None
    for step in build.get("steps", []) or []:
        if isinstance(step, dict) and "docker/build-push-action@" in str(step.get("uses", "")):
            push_step = step
            break
    assert push_step is not None, "ci.yml build job nema `docker/build-push-action` step."
    tags = str(push_step.get("with", {}).get("tags", ""))
    # Stabilan tag: env STABLE_TAG (master->latest/...) ILI literal :latest/:staging/:production.
    assert re.search(r"STABLE_TAG|:latest|:staging|:production", tags), (
        f"ci.yml build-push `tags` = {tags!r} nema stabilan per-branch tag (M2). deploy.sh "
        f"`pull` povlaci stabilan tag (production.yml default :latest), ne :ci-<sha>."
    )


def test_ac9_ci_yml_build_job_has_login_action():
    """AC9/SM-D7: ci.yml build job MORA imati `docker/login-action` (GHCR login)."""
    data = _parse_yaml(CI_YML)
    build = data.get("jobs", {}).get("build", {})
    uses = [
        s.get("uses") for s in (build.get("steps", []) or [])
        if isinstance(s, dict) and "uses" in s
    ]
    login = [u for u in uses if isinstance(u, str) and u.startswith("docker/login-action@")]
    assert login, (
        f"ci.yml build job nema `docker/login-action@vN`. AC9/SM-D7: GHCR login "
        f"(registry ghcr.io, secrets.GITHUB_TOKEN) je aktiviran iz 9.1 deferred placeholder-a. "
        f"Pronadjeno uses: {uses}"
    )


def test_ac9_ci_yml_build_push_true():
    """AC9/SM-D7: ci.yml `docker/build-push-action` MORA imati `push: true`
    (bilo `false` u 9.1 — deferred push aktiviran)."""
    data = _parse_yaml(CI_YML)
    build = data.get("jobs", {}).get("build", {})
    push_step = None
    for step in build.get("steps", []) or []:
        if isinstance(step, dict) and "docker/build-push-action@" in str(step.get("uses", "")):
            push_step = step
            break
    assert push_step is not None, (
        "ci.yml build job nema `docker/build-push-action` step. AC9 regresija."
    )
    push_value = push_step.get("with", {}).get("push")
    assert push_value is True, (
        f"ci.yml `docker/build-push-action` `with.push` = {push_value!r}, ocekivano True. "
        f"AC9/SM-D7: 9.2 aktivira deferred GHCR push (`push: false`->`true`)."
    )


def test_ac9_ci_yml_build_needs_lint_test_regression():
    """AC9/AC12 REGRESSION: ci.yml build job `needs: [lint, test]` redosled NETAKNUT."""
    data = _parse_yaml(CI_YML)
    build = data.get("jobs", {}).get("build", {})
    needs = build.get("needs", [])
    if isinstance(needs, str):
        needs = [needs]
    assert "lint" in needs and "test" in needs, (
        f"ci.yml build `needs` = {needs!r}, mora sadrzati lint + test. AC9/AC12: "
        f"9.2 GHCR push NE sme da razbije lint/test/build redosled."
    )


# =============================================================================
# AC5 (dop) — ops/secrets/README.md
# =============================================================================


def test_secrets_readme_exists():
    """AC5/Task 7.2: `ops/secrets/README.md` MORA postojati."""
    assert SECRETS_README.exists(), (
        f"Missing required file: {SECRETS_README}\n"
        f"AC5/Task 7.2: lista zahtevanih GH secrets + SSH least-privilege guidance."
    )


def test_secrets_readme_lists_required_gh_secrets():
    """AC5/Task 7.2: README MORA listati zahtevane GH secrets (DEPLOY_SSH_KEY/HOST/USER)."""
    content = _read_file(SECRETS_README)
    required = ["DEPLOY_SSH_KEY", "DEPLOY_HOST", "DEPLOY_USER"]
    missing = [s for s in required if s not in content]
    assert not missing, (
        f"ops/secrets/README.md ne listira GH secrets: {missing}. AC5/Task 7.2: "
        f"dokumentuj sve zahtevane secrets (vrednosti van repo-a)."
    )


def test_secrets_readme_lists_deploy_app_dir():
    """M5: README MORA listati `DEPLOY_APP_DIR` (deploy.yml `cd "$DEPLOY_APP_DIR"`).
    Bez ga deployer ne postavi → `cd ""` → pogresan CWD → broken deploy."""
    content = _read_file(SECRETS_README)
    assert "DEPLOY_APP_DIR" in content, (
        "ops/secrets/README.md ne listira `DEPLOY_APP_DIR`. M5: deploy.yml `cd`-uje u njega; "
        "bez dokumentacije deployer ga ne postavi → pogresan CWD."
    )


def test_deploy_yml_app_dir_guard():
    """M5: deploy.yml MORA fail-loud ako je DEPLOY_APP_DIR prazan (NE tih `cd ""`)."""
    raw = _read_file(DEPLOY_YML)
    assert "DEPLOY_APP_DIR" in raw, (
        "deploy.yml ne referencira `DEPLOY_APP_DIR`. M5."
    )
    # Guard: `-z` test ILI `test -n` na APP_DIR pre cd-a.
    assert re.search(r"-z\s+\"?\$\{?APP_DIR|test\s+-n\s+\"?\$\{?APP_DIR", raw), (
        "deploy.yml nema fail-loud guard za prazan DEPLOY_APP_DIR (M5). Dodaj "
        "`if [ -z \"${APP_DIR}\" ]; then ... exit 1; fi` pre `cd`."
    )


def test_deploy_yml_host_key_fingerprint_pinning():
    """M8 (SECURITY): deploy.yml ssh-action MORA pinovati host key (fingerprint) protiv MITM-a."""
    raw = _read_file(DEPLOY_YML)
    assert re.search(r"fingerprint:\s*\$\{\{\s*secrets\.DEPLOY_HOST_FINGERPRINT", raw), (
        "deploy.yml ssh-action nema `fingerprint: ${{ secrets.DEPLOY_HOST_FINGERPRINT }}` "
        "(M8): bez host-key pinning-a ssh-action prihvata bilo koji host key (MITM rizik)."
    )


def test_deploy_yml_ssh_action_sha_pinned():
    """M8 (SECURITY): SECURITY-sensitive appleboy/ssh-action (rukuje DEPLOY_SSH_KEY) MORA biti
    PIN-ovan na commit SHA, NE mutable major tag (supply-chain hardening)."""
    raw = _read_file(DEPLOY_YML)
    # Cilja `uses:` liniju (ne komentar) — `uses:` prefiks razlikuje od `# appleboy/...@v1.2.2`.
    m = re.search(r"uses:\s*appleboy/ssh-action@([0-9a-f]{40}|v[\d.]+)", raw)
    assert m is not None, "deploy.yml `uses: appleboy/ssh-action@...` nije pronadjen. M8."
    ref = m.group(1)
    assert re.fullmatch(r"[0-9a-f]{40}", ref), (
        f"deploy.yml appleboy/ssh-action je pinovan na `{ref}` (mutable tag), ne 40-char "
        f"commit SHA. M8: SSH akcija rukuje privatnim kljucem → SHA-pin protiv supply-chain "
        f"napada (komentar uz pin navodi verziju)."
    )


def test_secrets_readme_ssh_least_privilege_guidance():
    """AC5/Task 7.2a: README MORA imati SSH least-privilege guidance (forced-command,
    no-pty, non-root deploy user)."""
    content = _read_file(SECRETS_README)
    has_guidance = (
        re.search(r'command="', content)
        or re.search(r"no-pty", content)
        or re.search(r"forced-command|least.priv|non-root|blast.radius", content, re.IGNORECASE)
    )
    assert has_guidance, (
        "ops/secrets/README.md nema SSH least-privilege guidance (Task 7.2a): "
        "`command=\"...\"` forced-command / `no-pty` / non-root deploy user."
    )
