"""Tests za Story 1.9 - GitHub Actions CI Pipeline + pre-commit config.

Verifikuje YAML strukturu dva nova config fajla:
- `.github/workflows/ci.yml` — CI workflow sa lint + test + build job-ovima
- `.pre-commit-config.yaml` — lokalni pre-commit hooks (ruff + djade + std)

Story 1.9 je INFRA-ONLY (cross-cutting) — nema Django app, model, view ili
template promene. Testovi su pure YAML struktura validacija — parsiraju oba
fajla sa `yaml.safe_load()` i proveravaju key/value kontrakt iz interface
contract-a (`_bmad-output/implementation-artifacts/1-9-interface-contract.md`).

Organizacija (po AC):
- AC1 (workflow structure): name=CI, on triggers, permissions, concurrency,
  jobs structure, timeout-minutes, build needs lint+test, job-level permissions
- AC2 (lint job): env DJANGO_SECRET_KEY, ruff check, djade --check, setup-uv +
  python-version pin
- AC3 (test job): env DJANGO_SECRET_KEY, NO DATABASE_URL, pytest, NO
  manage.py check --deploy
- AC4 (build job): docker/setup-buildx-action, docker/build-push-action sa
  push: false, NO docker/login-action
- AC6 (pre-commit-config): standardni hooks + ruff + djade, sve revs pinned,
  NO pytest hook, NO cirilica
- AC9 (token discipline / security): no @latest / @main, no hardcoded secrets,
  no continue-on-error: true, actions/checkout@v4+ u sva 3 job-a

Pokrenuti sa:
    uv run pytest tests/test_ci_workflow_config.py -v

TEA RED faza: svi testovi MORAJU pasti dok Dev ne kreira fajlove
(`.github/workflows/ci.yml` + `.pre-commit-config.yaml`). Fixtures koriste
`pytest.fail(...)` kad fajl ne postoji — to znaci da svaki test fail-uje
sa istom porukom (Missing required file).

Naming convention: srpska latinica + engleski identifikatori; bez cirilice.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

# =============================================================================
# Konstante (project paths)
# =============================================================================

REPO_ROOT = Path(__file__).resolve().parent.parent
CI_WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "ci.yml"
PRE_COMMIT_CONFIG_PATH = REPO_ROOT / ".pre-commit-config.yaml"


# =============================================================================
# Fixtures (module-scoped — cached parsing per test run)
# =============================================================================


@pytest.fixture(scope="module")
def ci_workflow() -> dict:
    """Parsiran `.github/workflows/ci.yml` kao dict.

    Fail-uje (NE skip) ako fajl ne postoji — Story 1.9 ga MORA kreirati.

    NAPOMENA: PyYAML parsira `on:` kao Python boolean `True` (YAML 1.1 quirk:
    `on`/`off`/`yes`/`no` su rezervisane reci). Konzument koristi `True` kao
    key da bi pristupio on-triggers blocku — to je expected pattern.
    """
    if not CI_WORKFLOW_PATH.exists():
        pytest.fail(
            f"Missing required file: {CI_WORKFLOW_PATH}\n"
            f"Story 1.9 Dev mora kreirati .github/workflows/ci.yml. "
            f"Vidi interface contract za strukturni kontrakt."
        )
    return yaml.safe_load(CI_WORKFLOW_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def ci_workflow_raw() -> str:
    """Raw text content `.github/workflows/ci.yml` (za grep-style proveru).

    Fail-uje ako fajl ne postoji.
    """
    if not CI_WORKFLOW_PATH.exists():
        pytest.fail(
            f"Missing required file: {CI_WORKFLOW_PATH}\n"
            f"Story 1.9 Dev mora kreirati .github/workflows/ci.yml."
        )
    return CI_WORKFLOW_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def pre_commit_config() -> dict:
    """Parsiran `.pre-commit-config.yaml` kao dict.

    Fail-uje ako fajl ne postoji.
    """
    if not PRE_COMMIT_CONFIG_PATH.exists():
        pytest.fail(
            f"Missing required file: {PRE_COMMIT_CONFIG_PATH}\n"
            f"Story 1.9 Dev mora kreirati .pre-commit-config.yaml u repo root-u."
        )
    return yaml.safe_load(PRE_COMMIT_CONFIG_PATH.read_text(encoding="utf-8"))


# TEA Reviewer fix: added raw-text fixture for .pre-commit-config.yaml so we can
# enforce cyrillic-free invariant from interface contract § 3.4 (anti-pattern #3).
@pytest.fixture(scope="module")
def pre_commit_config_raw() -> str:
    """Raw text content `.pre-commit-config.yaml` (za grep-style proveru).

    Fail-uje ako fajl ne postoji.
    """
    if not PRE_COMMIT_CONFIG_PATH.exists():
        pytest.fail(
            f"Missing required file: {PRE_COMMIT_CONFIG_PATH}\n"
            f"Story 1.9 Dev mora kreirati .pre-commit-config.yaml u repo root-u."
        )
    return PRE_COMMIT_CONFIG_PATH.read_text(encoding="utf-8")


# =============================================================================
# Helper funkcije
# =============================================================================


def _get_on_block(workflow: dict) -> dict:
    """Vrati `on:` block iz workflow dict-a.

    PyYAML parsira nepokvotovani `on` kao Python `True` (YAML 1.1 boolean alias).
    Dev moze koristiti string `"on"` (kvotovano) ili boolean key. Ovaj helper
    pokriva oba slucaja defenzivno.
    """
    if True in workflow:
        return workflow[True]
    if "on" in workflow:
        return workflow["on"]
    pytest.fail(
        "ci.yml nema `on:` block (ni kao boolean True ni kao string 'on'). "
        "Workflow MORA imati `on:` sa push + pull_request + workflow_dispatch."
    )
    return {}  # unreachable; pytest.fail raises


def _collect_step_field(job: dict, field: str) -> list:
    """Skupi vrednosti specifičnog field-a iz svih step-ova nekog job-a.

    Vraca listu (preskace step-ove koji nemaju taj field).
    """
    steps = job.get("steps", []) or []
    return [
        step.get(field) for step in steps if isinstance(step, dict) and field in step
    ]


def _job_step_runs(job: dict) -> str:
    """Konkatenacija svih `run:` komandi nekog job-a u jedan string (za substring search)."""
    runs = _collect_step_field(job, "run")
    return "\n".join(r for r in runs if isinstance(r, str))


def _job_step_uses(job: dict) -> list[str]:
    """Lista svih `uses:` referencija u step-ovima job-a."""
    uses = _collect_step_field(job, "uses")
    return [u for u in uses if isinstance(u, str)]


def _action_major_version(uses_ref: str) -> int | None:
    """Vrati major version iz `owner/repo@vN` reference. None ako format nije validan."""
    if "@" not in uses_ref:
        return None
    _, version = uses_ref.rsplit("@", 1)
    if not version.startswith("v"):
        return None
    try:
        # Hvata `v4`, `v4.1.7`, etc. — uzima samo MAJOR
        return int(version[1:].split(".")[0])
    except (ValueError, IndexError):
        return None


# =============================================================================
# AC1 — Workflow structure (file exists, name, triggers, permissions,
# concurrency, jobs, timeout-minutes, build needs)
# =============================================================================


def test_ci_workflow_file_exists():
    """AC1 — `.github/workflows/ci.yml` MORA postojati u repo root-u."""
    assert CI_WORKFLOW_PATH.exists(), (
        f"`.github/workflows/ci.yml` ne postoji na {CI_WORKFLOW_PATH}. "
        f"Story 1.9 Task 1.2: kreiraj fajl sa CI skeleton-om."
    )


def test_ci_workflow_name_is_ci(ci_workflow):
    """AC1 — root-level `name: CI`."""
    assert ci_workflow.get("name") == "CI", (
        f"ci.yml `name:` polje = {ci_workflow.get('name')!r}, ocekivano 'CI'. "
        f"Vidi interface contract § 2.1."
    )


def test_ci_triggers_on_push_master(ci_workflow):
    """AC1 — `on.push.branches` MORA sadržati 'master'."""
    on_block = _get_on_block(ci_workflow)
    push_branches = on_block.get("push", {}).get("branches", [])
    assert "master" in push_branches, (
        f"ci.yml `on.push.branches` = {push_branches!r}, mora sadrzati 'master'. "
        f"AC1 + Decision D12 — `master` je current default branch."
    )


def test_ci_triggers_on_pull_request_master(ci_workflow):
    """AC1 — `on.pull_request.branches` MORA sadržati 'master' (PR gate)."""
    on_block = _get_on_block(ci_workflow)
    pr_branches = on_block.get("pull_request", {}).get("branches", [])
    assert "master" in pr_branches, (
        f"ci.yml `on.pull_request.branches` = {pr_branches!r}, mora sadrzati 'master'. "
        f"AC1 — PR ka master triggeruje CI gate (pocevsi od Story 2.1)."
    )


def test_ci_triggers_on_workflow_dispatch(ci_workflow):
    """AC1 + IMP-IT2-4 — `on.workflow_dispatch` MORA biti prisutan (manual run trigger)."""
    on_block = _get_on_block(ci_workflow)
    assert "workflow_dispatch" in on_block, (
        "ci.yml `on` block nema `workflow_dispatch:` trigger. "
        "IMP-IT2-4 + Decision D13: workflow_dispatch omogucava pre-merge "
        "dry-run iz GitHub Actions UI-ja na throwaway branch."
    )


def test_ci_has_concurrency_block(ci_workflow):
    """AC1 + IMP-3 — `concurrency` block sa per-branch group + cancel-in-progress."""
    concurrency = ci_workflow.get("concurrency")
    assert concurrency is not None, (
        "ci.yml nema `concurrency:` block. IMP-3: bez ovoga, dva push-a brzo "
        "za redom triggeruju dva paralelna CI run-a (waste GHA minute)."
    )
    assert isinstance(concurrency, dict), (
        f"`concurrency:` mora biti mapping, dobijeno {type(concurrency).__name__}."
    )
    group = concurrency.get("group", "")
    assert "github.ref" in group, (
        f"`concurrency.group` = {group!r}, mora referencirati `${{{{ github.ref }}}}` "
        f"za per-branch grupisanje. IMP-3."
    )
    assert concurrency.get("cancel-in-progress") is True, (
        f"`concurrency.cancel-in-progress` = {concurrency.get('cancel-in-progress')!r}, "
        f"mora biti boolean True. IMP-3."
    )


def test_ci_has_three_jobs(ci_workflow):
    """AC1 — `jobs:` MORA imati tačno tri ključa: `lint`, `test`, `build`."""
    jobs = ci_workflow.get("jobs", {})
    assert isinstance(jobs, dict), (
        f"`jobs:` mora biti mapping, dobijeno {type(jobs).__name__}."
    )
    required = {"lint", "test", "build"}
    present = set(jobs.keys())
    missing = required - present
    assert not missing, (
        f"ci.yml `jobs:` nedostaju: {missing}. "
        f"Pronadjeno: {sorted(present)}. AC1 zahteva sve tri."
    )


def test_ci_build_job_depends_on_lint_and_test(ci_workflow):
    """AC1 — `jobs.build.needs` MORA sadržati `lint` i `test` (build runs after both pass)."""
    build = ci_workflow.get("jobs", {}).get("build", {})
    needs = build.get("needs", [])
    # needs može biti string (single dep) ili lista
    if isinstance(needs, str):
        needs = [needs]
    assert isinstance(needs, list), (
        f"`jobs.build.needs` mora biti string ili lista, dobijeno {type(needs).__name__}."
    )
    assert "lint" in needs and "test" in needs, (
        f"`jobs.build.needs` = {needs!r}, mora sadrzati BOTH 'lint' i 'test'. "
        f"AC1: build ne sme da krene pre nego lint i test prodju."
    )


def test_ci_workflow_level_permissions_minimal(ci_workflow):
    """AC1 + IMP-1 — workflow-level `permissions.contents: read`, BEZ packages:write na workflow nivou."""
    permissions = ci_workflow.get("permissions", {})
    assert isinstance(permissions, dict), (
        f"`permissions:` mora biti mapping (least-privilege deklaracija), "
        f"dobijeno {type(permissions).__name__}. IMP-1."
    )
    assert permissions.get("contents") == "read", (
        f"workflow-level `permissions.contents` = {permissions.get('contents')!r}, "
        f"ocekivano 'read'. IMP-1 — least-privilege za checkout."
    )
    # CRITICAL: packages:write NE sme biti workflow-level (preširoko)
    assert "packages" not in permissions, (
        f"workflow-level `permissions.packages` = {permissions.get('packages')!r}. "
        f"IMP-1: `packages: write` MORA biti JOB-LEVEL na build-u, NE workflow-level "
        f"(lint+test ne diraju GHCR)."
    )


def test_ci_build_job_has_packages_write(ci_workflow):
    """AC1 + IMP-1 — `jobs.build.permissions.packages: write` (job-level, placeholder za Story 9.2)."""
    build = ci_workflow.get("jobs", {}).get("build", {})
    permissions = build.get("permissions", {})
    assert isinstance(permissions, dict), (
        f"`jobs.build.permissions` mora biti mapping, dobijeno "
        f"{type(permissions).__name__}. IMP-1: job-level packages:write."
    )
    assert permissions.get("packages") == "write", (
        f"`jobs.build.permissions.packages` = {permissions.get('packages')!r}, "
        f"ocekivano 'write'. IMP-1: placeholder za Story 9.2 GHCR push."
    )


def test_ci_all_jobs_have_timeout_minutes(ci_workflow):
    """AC1 + IMP-4 — svaki job MORA imati `timeout-minutes` (lint+test ≤ 10, build ≤ 15)."""
    jobs = ci_workflow.get("jobs", {})
    expected_max = {"lint": 10, "test": 10, "build": 15}
    for job_name, max_minutes in expected_max.items():
        job = jobs.get(job_name, {})
        timeout = job.get("timeout-minutes")
        assert timeout is not None, (
            f"`jobs.{job_name}.timeout-minutes` nije postavljen. "
            f"IMP-4: sprecava infinite hang scenarije (npr. Docker Hub rate limit)."
        )
        assert isinstance(timeout, int), (
            f"`jobs.{job_name}.timeout-minutes` = {timeout!r}, mora biti integer."
        )
        assert timeout <= max_minutes, (
            f"`jobs.{job_name}.timeout-minutes` = {timeout}, mora biti <= {max_minutes}. "
            f"IMP-4 budget: lint+test 10min, build 15min."
        )


# =============================================================================
# AC2 — Lint job: ruff check, djade --check, DJANGO_SECRET_KEY env,
#                setup-uv@v3 sa python-version 3.13
# =============================================================================


def test_ci_lint_job_runs_ruff_check(ci_workflow):
    """AC2 — `lint` job MORA imati step koji pokrece `ruff check`."""
    lint = ci_workflow.get("jobs", {}).get("lint", {})
    runs = _job_step_runs(lint)
    assert "ruff check" in runs, (
        f"`lint` job nema step sa `ruff check` komandom. "
        f"AC2: Step 4 = `uv run ruff check .`. Pronadjeno run-ova:\n{runs}"
    )


def test_ci_lint_job_runs_djade_check(ci_workflow):
    """AC2 — `lint` job MORA imati step koji pokrece `djade --check`."""
    lint = ci_workflow.get("jobs", {}).get("lint", {})
    runs = _job_step_runs(lint)
    assert "djade --check" in runs, (
        f"`lint` job nema step sa `djade --check` komandom. "
        f"AC2: Step 5 = `uv run djade --check templates/`. Pronadjeno run-ova:\n{runs}"
    )


def test_ci_lint_job_has_django_secret_key_env(ci_workflow):
    """AC2 + CRIT-2 + Gotcha CI-1 — `lint` job MORA imati `env.DJANGO_SECRET_KEY` (0-cost insurance)."""
    lint = ci_workflow.get("jobs", {}).get("lint", {})
    env = lint.get("env", {})
    assert isinstance(env, dict), (
        f"`jobs.lint.env` mora biti mapping, dobijeno {type(env).__name__}. "
        f"CRIT-2: defensive insurance za buduce djade/lint hook settings load."
    )
    secret = env.get("DJANGO_SECRET_KEY")
    assert secret, (
        f"`jobs.lint.env.DJANGO_SECRET_KEY` nije postavljen ({secret!r}). "
        f"CRIT-2 + Gotcha CI-1: 0-cost defensive insurance."
    )
    assert isinstance(secret, str) and len(secret) > 0, (
        f"`DJANGO_SECRET_KEY` mora biti non-empty string, dobijeno {secret!r}."
    )


def test_ci_lint_job_uses_setup_uv_action(ci_workflow):
    """AC2 — `lint` job MORA koristiti `astral-sh/setup-uv@vN` (N >= 3)."""
    lint = ci_workflow.get("jobs", {}).get("lint", {})
    uses_list = _job_step_uses(lint)
    setup_uv_refs = [u for u in uses_list if u.startswith("astral-sh/setup-uv@")]
    assert setup_uv_refs, (
        f"`lint` job nema step sa `astral-sh/setup-uv@vN`. "
        f"AC2 Step 2 + Decision D2. Pronadjeno uses-ova: {uses_list}"
    )
    # Verifikuj da je pin major version (NOT @latest, NOT @main)
    for ref in setup_uv_refs:
        major = _action_major_version(ref)
        assert major is not None and major >= 3, (
            f"`astral-sh/setup-uv` referenca = {ref!r}, mora biti @vN (N >= 3). "
            f"AC9 + CRIT-4: pinned major version, nikad @latest ili @main."
        )


def test_ci_lint_job_pins_python_3_13(ci_workflow):
    """AC2 + IMP-9 — `setup-uv` step MORA imati `with.python-version: '3.13'`."""
    lint = ci_workflow.get("jobs", {}).get("lint", {})
    steps = lint.get("steps", []) or []
    setup_uv_step = None
    for step in steps:
        if isinstance(step, dict) and "astral-sh/setup-uv@" in str(
            step.get("uses", "")
        ):
            setup_uv_step = step
            break
    assert setup_uv_step is not None, (
        "`lint` job nema setup-uv step (videti prethodni test)."
    )
    with_block = setup_uv_step.get("with", {})
    python_version = with_block.get("python-version")
    # Tolerantno: '3.13' (string) ili 3.13 (float — YAML parsing edge case)
    assert str(python_version) == "3.13", (
        f"setup-uv step `with.python-version` = {python_version!r}, ocekivano '3.13'. "
        f"IMP-9: matchuje `pyproject.toml` `requires-python = '>=3.13'`."
    )


# =============================================================================
# AC3 — Test job: pytest, DJANGO_SECRET_KEY env, NO DATABASE_URL,
#                NO manage.py check --deploy
# =============================================================================


def test_ci_test_job_runs_pytest(ci_workflow):
    """AC3 — `test` job MORA imati step koji pokrece `pytest`."""
    test_job = ci_workflow.get("jobs", {}).get("test", {})
    runs = _job_step_runs(test_job)
    assert "pytest" in runs, (
        f"`test` job nema step sa `pytest` komandom. "
        f"AC3: Step 4 = `uv run pytest`. Pronadjeno run-ova:\n{runs}"
    )


def test_ci_test_job_has_django_secret_key_env(ci_workflow):
    """AC3 + CRIT-1 + Gotcha CI-1 — `test` job MORA imati `env.DJANGO_SECRET_KEY`."""
    test_job = ci_workflow.get("jobs", {}).get("test", {})
    env = test_job.get("env", {})
    assert isinstance(env, dict), (
        f"`jobs.test.env` mora biti mapping, dobijeno {type(env).__name__}. "
        f"CRIT-1: bez ovoga pytest-django ucitava settings → ImproperlyConfigured."
    )
    secret = env.get("DJANGO_SECRET_KEY")
    assert secret, (
        f"`jobs.test.env.DJANGO_SECRET_KEY` nije postavljen ({secret!r}). "
        f"CRIT-1 + Gotcha CI-1: bez ovog env-a test job pada 100% pre pytest collect-a."
    )
    assert isinstance(secret, str) and len(secret) > 0, (
        f"`DJANGO_SECRET_KEY` mora biti non-empty string, dobijeno {secret!r}."
    )


def test_ci_test_job_does_not_set_database_url_env(ci_workflow):
    """AC3 + CRIT-IT2-1 + Gotcha CI-7 — `test` job NE SME postaviti `DATABASE_URL` env."""
    test_job = ci_workflow.get("jobs", {}).get("test", {})
    env = test_job.get("env", {}) or {}
    assert "DATABASE_URL" not in env, (
        f"`jobs.test.env.DATABASE_URL` = {env.get('DATABASE_URL')!r} — MORA biti odsutan. "
        f"CRIT-IT2-1 + Gotcha CI-7: `base.py:78` default-uje na sqlite:///db.sqlite3; "
        f"setting `DATABASE_URL=sqlite:///test.db` je redundantno i maskira pravo "
        f"ponasanje (DB na non-default putanji)."
    )


def test_ci_test_job_does_not_run_check_deploy(ci_workflow):
    """AC3 + IMP-IT2-1 + Decision D13 — NEMA `manage.py check --deploy` step-a u test job-u."""
    test_job = ci_workflow.get("jobs", {}).get("test", {})
    runs = _job_step_runs(test_job)
    assert "check --deploy" not in runs, (
        "`test` job sadrzi `check --deploy` komandu u nekom step-u. "
        "IMP-IT2-1 + Decision D13: step UKLONJEN (development settings ima "
        "DEBUG=True; continue-on-error: true bi ucinio step placebo). "
        "Vraca se u Story 9.6 nakon prelaska na settings.production."
    )


# =============================================================================
# AC4 — Build job: docker/build-push-action sa push: false, NO docker/login-action
# =============================================================================


def test_ci_build_job_has_docker_build_step(ci_workflow):
    """AC4 — `build` job MORA imati `docker/build-push-action@vN` step (N >= 6)."""
    build = ci_workflow.get("jobs", {}).get("build", {})
    uses_list = _job_step_uses(build)
    build_push_refs = [
        u for u in uses_list if u.startswith("docker/build-push-action@")
    ]
    assert build_push_refs, (
        f"`build` job nema `docker/build-push-action@vN` step. "
        f"AC4 Step 4. Pronadjeno uses-ova: {uses_list}"
    )
    for ref in build_push_refs:
        major = _action_major_version(ref)
        assert major is not None and major >= 6, (
            f"`docker/build-push-action` referenca = {ref!r}, mora biti @vN (N >= 6). "
            f"AC9 + CRIT-4: v6 minimum (GHA cache support)."
        )


def test_ci_build_job_does_not_push_image(ci_workflow):
    """AC4 — `docker/build-push-action` step `with.push: false` (Story 1.9 NE push-uje)."""
    build = ci_workflow.get("jobs", {}).get("build", {})
    steps = build.get("steps", []) or []
    push_step = None
    for step in steps:
        if isinstance(step, dict) and "docker/build-push-action@" in str(
            step.get("uses", "")
        ):
            push_step = step
            break
    assert push_step is not None, (
        "`build` job nema docker/build-push-action step (videti prethodni test)."
    )
    with_block = push_step.get("with", {})
    push_value = with_block.get("push")
    assert push_value is False, (
        f"`docker/build-push-action` `with.push` = {push_value!r}, mora biti False. "
        f"AC4: Story 1.9 NE push-uje image (smoke test); Story 9.2 dodaje push."
    )


def test_ci_build_job_no_ghcr_login_in_v1(ci_workflow):
    """AC4 + IMP-6 — NEMA `docker/login-action@*` step u Story 1.9 build job-u."""
    build = ci_workflow.get("jobs", {}).get("build", {})
    uses_list = _job_step_uses(build)
    login_refs = [u for u in uses_list if u.startswith("docker/login-action@")]
    assert not login_refs, (
        f"`build` job sadrzi `docker/login-action` step-ove: {login_refs}. "
        f"IMP-6: GHCR login je DEFERRED do Story 9.2 (login + push idu zajedno). "
        f"Story 1.9 build job samo verifikuje Dockerfile buildable."
    )


# =============================================================================
# AC6 — .pre-commit-config.yaml: std hooks + ruff + djade, sve revs pinned,
#                                no pytest hook
# =============================================================================


def test_pre_commit_config_file_exists():
    """AC6 — `.pre-commit-config.yaml` MORA postojati u repo root-u."""
    assert PRE_COMMIT_CONFIG_PATH.exists(), (
        f"`.pre-commit-config.yaml` ne postoji na {PRE_COMMIT_CONFIG_PATH}. "
        f"Story 1.9 Task 2.1: kreiraj fajl u repo root-u."
    )


def test_pre_commit_config_has_pre_commit_hooks_repo(pre_commit_config):
    """AC6 + IMP-5 — `repos:` MORA sadržati `pre-commit/pre-commit-hooks` repo."""
    repos = pre_commit_config.get("repos", [])
    assert isinstance(repos, list), (
        f"`repos:` mora biti lista, dobijeno {type(repos).__name__}."
    )
    repo_urls = [r.get("repo", "") for r in repos if isinstance(r, dict)]
    matching = [u for u in repo_urls if "pre-commit/pre-commit-hooks" in u]
    assert matching, (
        f".pre-commit-config.yaml NEMA `pre-commit/pre-commit-hooks` repo. "
        f"IMP-5: standardni baseline higijenski hooks. Pronadjeno repos: {repo_urls}"
    )


def test_pre_commit_config_has_std_hooks(pre_commit_config):
    """AC6 + IMP-5 — `pre-commit-hooks` repo MORA imati svih 4 standardne hookove."""
    repos = pre_commit_config.get("repos", [])
    target_repo = None
    for r in repos:
        if isinstance(r, dict) and "pre-commit/pre-commit-hooks" in r.get("repo", ""):
            target_repo = r
            break
    assert target_repo is not None, (
        "`pre-commit/pre-commit-hooks` repo nije pronadjen (videti prethodni test)."
    )
    hook_ids = [
        h.get("id") for h in target_repo.get("hooks", []) if isinstance(h, dict)
    ]
    required = {
        "trailing-whitespace",
        "end-of-file-fixer",
        "check-yaml",
        "check-merge-conflict",
    }
    missing = required - set(hook_ids)
    assert not missing, (
        f"`pre-commit-hooks` repo nedostaju hooks: {missing}. "
        f"IMP-5 zahteva svih 4: {sorted(required)}. Pronadjeno: {hook_ids}"
    )


def test_pre_commit_config_has_ruff_repo(pre_commit_config):
    """AC6 — `repos:` MORA sadržati `ruff-pre-commit` repo sa ruff-check + ruff-format hooks."""
    repos = pre_commit_config.get("repos", [])
    target_repo = None
    for r in repos:
        if isinstance(r, dict) and "ruff-pre-commit" in r.get("repo", ""):
            target_repo = r
            break
    assert target_repo is not None, (
        f".pre-commit-config.yaml NEMA `ruff-pre-commit` repo. "
        f"AC6: 1:1 lint sync sa CI lint job-om. "
        f"Pronadjeno repos: {[r.get('repo') for r in repos if isinstance(r, dict)]}"
    )
    hook_ids = [
        h.get("id") for h in target_repo.get("hooks", []) if isinstance(h, dict)
    ]
    assert "ruff-check" in hook_ids, (
        f"`ruff-pre-commit` repo nema `ruff-check` hook. "
        f"AC6 + Decision D11. Pronadjeno hooks: {hook_ids}"
    )
    assert "ruff-format" in hook_ids, (
        "`ruff-pre-commit` repo nema `ruff-format` hook. "
        "AC6: ruff-format je separatan od ruff-check (ekvivalent black-u)."
    )


def test_pre_commit_config_has_djade_repo(pre_commit_config):
    """AC6 — `repos:` MORA sadržati `djade-pre-commit` repo sa `djade` hook + target-version 5.2."""
    repos = pre_commit_config.get("repos", [])
    target_repo = None
    for r in repos:
        if isinstance(r, dict) and "djade-pre-commit" in r.get("repo", ""):
            target_repo = r
            break
    assert target_repo is not None, (
        f".pre-commit-config.yaml NEMA `djade-pre-commit` repo. "
        f"AC6: 1:1 lint sync sa CI lint job-om. "
        f"Pronadjeno repos: {[r.get('repo') for r in repos if isinstance(r, dict)]}"
    )
    hooks = target_repo.get("hooks", [])
    djade_hook = None
    for h in hooks:
        if isinstance(h, dict) and h.get("id") == "djade":
            djade_hook = h
            break
    assert djade_hook is not None, (
        f"`djade-pre-commit` repo nema `djade` hook. "
        f"Pronadjeno hooks: {[h.get('id') for h in hooks if isinstance(h, dict)]}"
    )
    # AC6: args MORA imati --target-version 5.2
    args = djade_hook.get("args", [])
    args_str = " ".join(str(a) for a in args)
    assert "--target-version" in args_str and "5.2" in args_str, (
        f"`djade` hook `args` = {args!r}, mora sadrzati `--target-version` + `5.2`. "
        f"AC6: matchuje `pyproject.toml` `django>=5.2,<6.0`."
    )


def test_pre_commit_config_no_pytest_hook(pre_commit_config):
    """AC6 + Decision D11 — NEMA pytest hook u pre-commit (CI-only gate)."""
    repos = pre_commit_config.get("repos", [])
    suspicious_hooks = []
    for r in repos:
        if not isinstance(r, dict):
            continue
        for h in r.get("hooks", []) or []:
            if not isinstance(h, dict):
                continue
            hook_id = h.get("id", "")
            if "pytest" in hook_id.lower():
                suspicious_hooks.append(hook_id)
    assert not suspicious_hooks, (
        f".pre-commit-config.yaml sadrzi pytest hook(ove): {suspicious_hooks}. "
        f"Decision D11: pytest je CI-only gate (pre-commit budget <5s, pytest 30-60s). "
        f"Vidi Decisions log u Story 1.9 Dev Notes."
    )


def test_pre_commit_config_all_revs_explicit(pre_commit_config):
    """AC6 + AC9 — svaki `repos[*].rev` mora biti pinned (NOT main/master/latest/HEAD)."""
    repos = pre_commit_config.get("repos", [])
    forbidden = {"main", "master", "latest", "head"}
    bad_revs = []
    for r in repos:
        if not isinstance(r, dict):
            continue
        rev = r.get("rev", "")
        repo_url = r.get("repo", "<unknown>")
        if not rev:
            bad_revs.append((repo_url, "<missing rev>"))
            continue
        if (
            str(rev).lower().lstrip("v") in {f.lstrip("v") for f in forbidden}
            or str(rev).lower() in forbidden
        ):
            bad_revs.append((repo_url, rev))
    assert not bad_revs, (
        f".pre-commit-config.yaml sadrzi floating rev-ove: {bad_revs}. "
        f"AC9 + AC6: svaki `rev:` MORA biti pinned (npr. 'v0.15.14'), nikad "
        f"'main', 'master', 'latest', 'HEAD'."
    )


# =============================================================================
# AC9 — Token discipline / security: no @latest, no continue-on-error, no leaks
# =============================================================================


def test_ci_no_at_latest_in_actions(ci_workflow):
    """AC9 — sve `uses:` reference moraju biti pinned (no @latest, no @main, no @master)."""
    jobs = ci_workflow.get("jobs", {})
    bad_refs = []
    for job_name, job in jobs.items():
        if not isinstance(job, dict):
            continue
        for ref in _job_step_uses(job):
            if not isinstance(ref, str) or "@" not in ref:
                continue
            _, version = ref.rsplit("@", 1)
            if version.lower() in ("latest", "main", "master", "head"):
                bad_refs.append((job_name, ref))
    assert not bad_refs, (
        f"ci.yml sadrzi floating action references: {bad_refs}. "
        f"AC9 + CRIT-4: sve action-i MORAJU biti pinned na @vN (npr. @v4). "
        f"Anti-pattern: @latest moze dobiti rogue update; @main pull-uje HEAD bilo "
        f"koje malicious commit-a."
    )


def test_ci_no_continue_on_error_true(ci_workflow):
    """AC9 + IMP-IT2-1 — NEMA `continue-on-error: true` na bilo kom step-u."""
    jobs = ci_workflow.get("jobs", {})
    offenders = []
    for job_name, job in jobs.items():
        if not isinstance(job, dict):
            continue
        for idx, step in enumerate(job.get("steps", []) or []):
            if isinstance(step, dict) and step.get("continue-on-error") is True:
                step_name = step.get("name", f"#{idx}")
                offenders.append((job_name, step_name))
    assert not offenders, (
        f"ci.yml sadrzi step-ove sa `continue-on-error: true`: {offenders}. "
        f"AC9 + IMP-IT2-1 + Decision D13: anti-pattern u Story 1.9. "
        f"Fail mora fail-ovati glasno. `manage.py check --deploy` koji je ranije "
        f"imao ovo, UKLONJEN je iz Story 1.9 v1."
    )


def test_ci_no_hardcoded_secrets(ci_workflow_raw):
    """AC9 — NEMA hardcoded GitHub PAT-ova (ghp_*) ili sl. real secret patterns u raw fajlu.

    Acceptable patterns:
      - `${{ secrets.NAME }}` (GHA secret reference)
      - `${{ github.token }}` ili `${{ secrets.GITHUB_TOKEN }}`
      - Dummy `DJANGO_SECRET_KEY` literal (`ci-test-secret-key-not-for-prod-...`)
        — eksplicitno `not-for-prod` u nazivu označava dummy intent

    Forbidden patterns:
      - `ghp_*` (GitHub Personal Access Token format)
      - `github_pat_*` (Fine-grained PAT format)
      - `gho_*` (OAuth token)
      - `xoxb-*` / `xoxa-*` (Slack tokens, by analogy)
    """
    forbidden_patterns = [
        ("ghp_", "GitHub Personal Access Token (classic)"),
        ("github_pat_", "GitHub Fine-grained PAT"),
        ("gho_", "GitHub OAuth token"),
    ]
    found = []
    for pattern, desc in forbidden_patterns:
        if pattern in ci_workflow_raw:
            found.append((pattern, desc))
    assert not found, (
        f"ci.yml sadrzi sumnjive token pattern-e: {found}. "
        f"AC9: NEMA hardcoded secrets. Koristi `${{{{ secrets.NAME }}}}` ili "
        f"`${{{{ github.token }}}}` umesto literal-a."
    )


def test_ci_no_cyrillic_characters(ci_workflow_raw):
    """AC9 + project-context.md — NEMA cirilicnih karaktera u `ci.yml`.

    Regression: Story 1.7/1.8 testovi vec proveravaju ovo za CSS fajlove;
    Story 1.9 anti-pattern lista eksplicitno zabranjuje cirilicu u config
    fajlovima (per project-context.md UI strings rule).
    """
    import re as _re

    cyrillic_chars = _re.findall(r"[Ѐ-ӿ]", ci_workflow_raw)
    assert not cyrillic_chars, (
        f"ci.yml sadrzi {len(cyrillic_chars)} cirilicnih karaktera "
        f"(prvi nekoliko: {cyrillic_chars[:5]}). "
        f"Project-context.md zabranjuje cirilicu — sve mora biti latinica + engleski."
    )


# TEA Reviewer fix: Interface contract § 3.4 anti-pattern #3 eksplicitno zabranjuje
# cirilicne karaktere u `.pre-commit-config.yaml` — postojeci ci.yml test (gornji)
# nije pokrivao taj fajl. Dodajemo simetricnu proveru.
def test_pre_commit_config_no_cyrillic_characters(pre_commit_config_raw):
    """AC9 + interface contract § 3.4 — NEMA cirilicnih karaktera u `.pre-commit-config.yaml`."""
    import re as _re

    cyrillic_chars = _re.findall(r"[Ѐ-ӿ]", pre_commit_config_raw)
    assert not cyrillic_chars, (
        f".pre-commit-config.yaml sadrzi {len(cyrillic_chars)} cirilicnih karaktera "
        f"(prvi nekoliko: {cyrillic_chars[:5]}). "
        f"Project-context.md + interface contract § 3.4: sve latinica + engleski."
    )


# TEA Reviewer fix: Interface contract § 2.2/2.3/2.4 + § 5 zahtevaju
# `actions/checkout@v<N>` (N >= 4) u sva tri job-a. Postojeci test
# `test_ci_no_at_latest_in_actions` hvata floating refs, ali ne enforce-uje
# da je checkout uopste prisutan + sa minimum major v4. Dodajemo eksplicit test.
def test_ci_all_jobs_use_actions_checkout_v4_or_higher(ci_workflow):
    """AC2/AC3/AC4 + AC9 + interface contract § 5 — sva tri job-a koriste `actions/checkout@vN` (N >= 4)."""
    jobs = ci_workflow.get("jobs", {})
    for job_name in ("lint", "test", "build"):
        job = jobs.get(job_name, {})
        uses_list = _job_step_uses(job)
        checkout_refs = [u for u in uses_list if u.startswith("actions/checkout@")]
        assert checkout_refs, (
            f"`{job_name}` job nema `actions/checkout@vN` step. "
            f"Interface contract § 5: MINIMUM @v4 pin za sva tri job-a. "
            f"Pronadjeno uses-ova: {uses_list}"
        )
        for ref in checkout_refs:
            major = _action_major_version(ref)
            assert major is not None and major >= 4, (
                f"`{job_name}` job ima `actions/checkout` ref {ref!r}; "
                f"mora biti @vN (N >= 4). AC9 + CRIT-4: pinned major; "
                f"Dev moze koristiti viseg majora (v5+) ako je verifikovan."
            )


# TEA Reviewer fix: Interface contract § 5 zahteva `docker/setup-buildx-action@v3`
# u build job-u (preduslov za docker/build-push-action@v6 GHA cache). Tests imaju
# build-push-action ali ne i buildx-setup — dodajemo simetriju.
def test_ci_build_job_uses_setup_buildx_action(ci_workflow):
    """AC4 + interface contract § 5 — `build` job MORA koristiti `docker/setup-buildx-action@vN` (N >= 3)."""
    build = ci_workflow.get("jobs", {}).get("build", {})
    uses_list = _job_step_uses(build)
    buildx_refs = [u for u in uses_list if u.startswith("docker/setup-buildx-action@")]
    assert buildx_refs, (
        f"`build` job nema `docker/setup-buildx-action@vN` step. "
        f"AC4 Step 2 + interface contract § 5: preduslov za GHA cache + multi-stage "
        f"Dockerfile build. Pronadjeno uses-ova: {uses_list}"
    )
    for ref in buildx_refs:
        major = _action_major_version(ref)
        assert major is not None and major >= 3, (
            f"`docker/setup-buildx-action` referenca = {ref!r}, mora biti @vN (N >= 3). "
            f"AC9 + CRIT-4: pinned major; viseg majora (v4+) je dozvoljen ako je verifikovan."
        )
