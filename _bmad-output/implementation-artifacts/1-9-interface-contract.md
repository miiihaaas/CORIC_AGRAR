---
story-id: "1.9"
story-key: 1-9-github-actions-ci-pipeline
title: Interface Contract — GitHub Actions CI Pipeline (lint + test + build) + pre-commit hooks
status: contract
created: 2026-05-29
last_modified: 2026-05-29
author: TEA (RED phase)
---

# Story 1.9 — Interface Contract

This contract is the canonical specification for Story 1.9 artifacts. The TEA RED-phase test
suite `tests/test_ci_workflow_config.py` directly encodes the assertions defined here. Dev
MUST satisfy this contract to ship Story 1.9 GREEN.

Story 1.9 is **infra-only / cross-cutting** — NO Django app, NO models, NO views, NO
templates, NO CSS, NO JS, NO new Python deps. Only two new config files (plus optional
justfile recipe + Dev Notes documentation). Tests validate YAML structure of the two new
config files.

## 1. Artifact inventory

### 1.1 New configuration files (2 — required)
| Path | Purpose |
|---|---|
| `.github/workflows/ci.yml` | GitHub Actions CI workflow — three jobs (`lint`, `test`, `build`) triggered on push/PR to master + workflow_dispatch. Authoritative CI gate. |
| `.pre-commit-config.yaml` | Local pre-commit hooks — `ruff` + `djade` lint hooks (1:1 sync with CI lint job) + standard `pre-commit-hooks` baseline (trailing-whitespace, end-of-file-fixer, check-yaml, check-merge-conflict). NO pytest hook (Decision D11 — pytest is CI-only). |

### 1.2 New directories (1)
| Path | Note |
|---|---|
| `.github/workflows/` | First time created in this repo (Story 1.9 is the first consumer of `.github/`). |

### 1.3 Modified files (0 required, 1 optional)
| Path | Modifications |
|---|---|
| `justfile` (OPTIONAL — Task 4, gold-plate) | Add `precommit-install` recipe that runs `uv run pre-commit install`. NOT a Story 1.9 blocker; acceptable scope deviation if skipped. |

### 1.4 NOT created in Story 1.9
- NO `deploy.yml` (deferred to Story 9.2 — Hetzner deployment script + SSL).
- NO `docker/login-action` step in `ci.yml` (IMP-6 — GHCR login deferred to Story 9.2).
- NO `staging`/`main` branch triggers (those branches do not exist in Epic 1).
- NO `yamllint` dev dep (Decision D9 — GitHub Actions parser is sufficient).
- NO `manage.py check --deploy` step (IMP-IT2-1 — deferred to Story 9.6 after switching to `settings.production`).
- NO Docker container test runtime (Decision D1 — pytest runs in `uv` venv on runner).
- NO PostgreSQL `services:` block in test job (Decision D12 + CRIT-IT2-1 — `base.py:78` defaults DATABASES to `sqlite:///db.sqlite3`).
- NO new Python dependency in `pyproject.toml` (all dev deps already present from Story 1.1).

## 2. `.github/workflows/ci.yml` structural contract

### 2.1 Root-level keys (mandatory)
| Key | Expected value / type | Rationale |
|---|---|---|
| `name` | `CI` (exact string) | AC1 — workflow display name. |
| `on` | mapping with `push`, `pull_request`, `workflow_dispatch` keys | AC1 — three triggers. |
| `on.push.branches` | list containing `master` | AC1 — push trigger only on default branch. |
| `on.pull_request.branches` | list containing `master` | AC1 — PR gate. |
| `on.workflow_dispatch` | present (may be `null`/empty mapping) | IMP-IT2-4 — enables manual pre-merge dry-run. |
| `permissions.contents` | `read` (string) | IMP-1 — workflow-level least-privilege; no workflow-level `packages: write`. |
| `concurrency.group` | string referencing `${{ github.ref }}` (template syntax preserved by YAML parser) | IMP-3 — per-branch concurrency. |
| `concurrency.cancel-in-progress` | `true` (boolean) | IMP-3 — cancel stale runs to save GHA free minutes. |
| `jobs` | mapping with exactly 3 keys: `lint`, `test`, `build` | AC1. |

### 2.2 `jobs.lint` (job structure)
| Field | Expected | Rationale |
|---|---|---|
| `runs-on` | `ubuntu-latest` | Standard runner. |
| `timeout-minutes` | integer `<= 10` | IMP-4 — prevent infinite hang. |
| `env.DJANGO_SECRET_KEY` | non-empty string (dummy value, e.g. `ci-test-secret-key-not-for-prod-50chars-padding`) | CRIT-2 + Gotcha CI-1 — 0-cost insurance against future djade/lint hook settings load. |
| `steps[*].uses` includes | `actions/checkout@v<N>` (N ≥ 4) | AC9 — pinned major. |
| `steps[*].uses` includes | `astral-sh/setup-uv@v<N>` (N ≥ 3) | AC9 — pinned major. |
| step with `uses: astral-sh/setup-uv@v<N>` has `with.python-version` | `'3.13'` (string) | IMP-9 — matches `pyproject.toml` `requires-python = ">=3.13"`. |
| `steps[*].run` contains | substring `ruff check` | AC2 — lint command. |
| `steps[*].run` contains | substring `djade --check` (or `djade --check templates/`) | AC2 — template format check. |

### 2.3 `jobs.test` (job structure)
| Field | Expected | Rationale |
|---|---|---|
| `runs-on` | `ubuntu-latest` | Standard runner. |
| `timeout-minutes` | integer `<= 10` | IMP-4. |
| `env.DJANGO_SECRET_KEY` | non-empty string | CRIT-1 — without this, `pytest-django` loads settings → `ImproperlyConfigured`. |
| `env.DATABASE_URL` | **MUST NOT BE SET** (no key in env block, OR key absent) | CRIT-IT2-1 + Gotcha CI-7 — `base.py:78` defaults to SQLite; redundant override masks real behavior. |
| `steps[*].run` contains | substring `pytest` (typically `uv run pytest`) | AC3. |
| `steps[*].run` MUST NOT contain | substring `manage.py check --deploy` | IMP-IT2-1 + Decision D13 — deferred to Story 9.6. |

### 2.4 `jobs.build` (job structure)
| Field | Expected | Rationale |
|---|---|---|
| `runs-on` | `ubuntu-latest` | Standard runner. |
| `timeout-minutes` | integer `<= 15` | IMP-4 — Docker build is slower. |
| `needs` | list containing both `lint` and `test` | AC1 — build runs after lint+test pass. |
| `permissions.packages` | `write` (string) | IMP-1 — job-level least-privilege; placeholder for Story 9.2 push. |
| `steps[*].uses` includes | `docker/setup-buildx-action@v<N>` (N ≥ 3) | AC4 — Buildx setup is prerequisite for multi-stage Dockerfile + GHA cache. |
| `steps[*].uses` includes | `docker/build-push-action@v<N>` (N ≥ 6) | AC4 + AC9. |
| `docker/build-push-action` step `with.push` | `false` (boolean) | AC4 — Story 1.9 does NOT push; Story 9.2 owns push. |
| `steps[*].uses` MUST NOT include | `docker/login-action@*` | IMP-6 — GHCR login deferred to Story 9.2. |

### 2.5 Cross-cutting `ci.yml` invariants (workflow-level)
1. **No `@latest` or `@main`** in any `uses:` reference (AC9 anti-pattern).
2. **No hardcoded secret values** (e.g., real GitHub PATs `ghp_*`, real passwords). All secret references go through `${{ secrets.* }}` or `${{ github.token }}`. The dummy `DJANGO_SECRET_KEY` literal (`ci-test-secret-key-not-for-prod-50chars-padding`) is acceptable because it is NOT a real secret — string literally signals dummy intent.
3. **No `continue-on-error: true`** on any step (IMP-IT2-1 — anti-pattern in Story 1.9).
4. **No Cyrillic characters** anywhere in the file (regex `[Ѐ-ӿ]`).
5. All actions are from official sources: `actions/*`, `astral-sh/*`, `docker/*`.
6. **All three jobs (`lint`, `test`, `build`) MUST use `actions/checkout@v<N>` (N ≥ 4)** — first step in every job; required for both source-code-reading jobs (lint/test) and Dockerfile-reading job (build).

## 3. `.pre-commit-config.yaml` structural contract

### 3.1 Root-level structure
| Key | Expected | Rationale |
|---|---|---|
| `repos` | list of 3 repo entries | AC6 + IMP-5. |

### 3.2 Required repos (3 in order)
| Repo URL substring | Required hook IDs | Rationale |
|---|---|---|
| `pre-commit/pre-commit-hooks` | `trailing-whitespace`, `end-of-file-fixer`, `check-yaml`, `check-merge-conflict` | IMP-5 — standard hygiene hooks. |
| `astral-sh/ruff-pre-commit` (or `ruff-pre-commit`) | `ruff-check` (with `args: [--fix]`), `ruff-format` | AC6 — 1:1 lint sync with CI lint job. |
| `adamchainz/djade-pre-commit` (or `djade-pre-commit`) | `djade` (with `args: [--target-version, "5.2"]`) | AC6 — 1:1 lint sync with CI lint job. |

### 3.3 Pre-commit revision pinning rules (AC9 + IMP-IT2-2)
- Every `repos[*].rev` MUST be a pinned version string.
- Forbidden rev values: `main`, `master`, `latest`, `HEAD` (no auto-update / no floating ref).
- Recommended minimum acceptable versions (verified 2026-05-29 — Dev may upgrade to higher stable major if released):
  - `pre-commit/pre-commit-hooks`: `v4.6.0` MINIMUM (verify latest stable major on GitHub Releases).
  - `astral-sh/ruff-pre-commit`: `v0.15.14` MINIMUM (matches `pyproject.toml` `ruff>=0.15.14`).
  - `adamchainz/djade-pre-commit`: `1.9.0` MINIMUM (matches `pyproject.toml` `djade>=1.9.0`).

### 3.4 Pre-commit anti-patterns (NOT present)
1. NO pytest hook (Decision D11 — pytest budget exceeds <5s pre-commit budget; CI-only gate).
2. NO `--no-verify` instruction anywhere in Dev Notes (per project-context.md Anti-pattern §).
3. NO Cyrillic characters anywhere in the file (regex `[Ѐ-ӿ]`).

## 4. Environment variables contract (CI workflow scope)

### 4.1 `DJANGO_SECRET_KEY` (both `lint` and `test` jobs)
- **Required:** YES — explicitly set in `env:` block of both `lint` and `test` jobs.
- **Value pattern:** non-empty string, sufficient length (≥ 50 chars recommended) to satisfy Django's internal sanity checks if any future hook validates.
- **Reference value:** `ci-test-secret-key-not-for-prod-50chars-padding`. The substring `not-for-prod` makes provenance unambiguous in audit logs.
- **Why required (CRIT-1 + CRIT-2 + Gotcha CI-1):** `config/settings/base.py:17` calls `env("DJANGO_SECRET_KEY")` WITHOUT default; without the env, `pytest-django` settings load raises `ImproperlyConfigured` before pytest collects tests.

### 4.2 `DATABASE_URL` (test job)
- **Required:** NO — MUST NOT be set in `test` job `env:` block.
- **Rationale (CRIT-IT2-1 + Gotcha CI-7):** `config/settings/base.py:78` already defaults DATABASES to `sqlite:///db.sqlite3`. Setting an explicit `DATABASE_URL=sqlite:///test.db` creates a DB at a non-default path and masks real default behavior. Existing tests do not use `@pytest.mark.django_db` so they never touch DB anyway.

### 4.3 GHCR / image-name env (build job, runtime-set by step)
- `IMAGE_NAME` — set at runtime by lowercase-transformation step from `${{ github.repository }}` (IMP-2 + Gotcha CI-2). Test contract does NOT enforce this in YAML structure (it appears only in `run:` shell script content), but recommended for narrative consistency.

## 5. Required GitHub Action version pins (minimum acceptable on 2026-05-29)

Verified versions Dev MUST pin in `ci.yml` (per AC9 + CRIT-4); higher stable majors may be substituted if available at implementation time:

| Action | Minimum pin | Used in |
|---|---|---|
| `actions/checkout` | `@v4` | All three jobs (`lint`, `test`, `build`). |
| `astral-sh/setup-uv` | `@v3` | `lint` + `test` jobs. |
| `docker/setup-buildx-action` | `@v3` | `build` job. |
| `docker/build-push-action` | `@v6` | `build` job. |

**Pin format:** `@v<MAJOR>` (e.g., `@v5`). NOT `@latest`, NOT `@main`. SHA pinning is optional supply-chain hardening (not enforced in tests).

## 6. File path expectations (absolute paths from repo root)

| Path | Existence | Type |
|---|---|---|
| `.github/` | MUST exist | directory (NEW in Story 1.9). |
| `.github/workflows/` | MUST exist | directory (NEW in Story 1.9). |
| `.github/workflows/ci.yml` | MUST exist | file (NEW in Story 1.9). |
| `.pre-commit-config.yaml` | MUST exist | file at repo root (NEW in Story 1.9). |
| `justfile` `precommit-install` recipe | OPTIONAL | gold-plate Task 4 — acceptable to skip. |

## 7. Story 1.9 hardcoded constants (reference — story file lines ~644-663)

| Name | Value | Location | Rationale |
|---|---|---|---|
| `RUNNER_OS` | `ubuntu-latest` | `ci.yml` all three jobs | Standard GHA runner. |
| `PYTHON_VERSION` | `3.13` | `ci.yml` `setup-uv` step `with.python-version` | Matches `pyproject.toml` `requires-python = ">=3.13"`. |
| `RUFF_VERSION_PIN` | `v0.15.14` (MIN) | `.pre-commit-config.yaml` `rev:` | Matches `pyproject.toml` `ruff>=0.15.14`. |
| `DJADE_VERSION_PIN` | `1.9.0` (MIN) | `.pre-commit-config.yaml` `rev:` | Matches `pyproject.toml` `djade>=1.9.0`. |
| `PRE_COMMIT_HOOKS_REV` | `v4.6.0` (MIN) | `.pre-commit-config.yaml` `rev:` | Standard baseline. |
| `DJADE_TARGET_VERSION` | `5.2` | `.pre-commit-config.yaml` `djade` hook `args` | Matches `pyproject.toml` `django>=5.2,<6.0`. |
| `GHCR_REGISTRY` | `ghcr.io` | `ci.yml` build job tag template | GitHub Container Registry. |
| `CHECKOUT_VERSION` | `v4` (MIN) | `ci.yml` all jobs | Latest stable major (2026-05-29). |
| `SETUP_UV_VERSION` | `v3` (MIN) | `ci.yml` lint + test jobs | Latest stable major (2026-05-29). |
| `BUILDX_VERSION` | `v3` (MIN) | `ci.yml` build job | Latest stable major (2026-05-29). |
| `BUILD_PUSH_ACTION_VERSION` | `v6` (MIN) | `ci.yml` build job | Latest stable major (v6 supports GHA cache). |

## 8. Key decisions reference (Story 1.9 lines ~407-423)

- **D1** — pytest runs in `uv` venv on runner, NOT in Docker container (speed + no live-DB requirement for Story 1.1-1.8 tests).
- **D2** — Use `astral-sh/setup-uv@v3` (official) + verify latest stable major on GitHub Releases pre-commit.
- **D11** — Pre-commit runs ONLY fast lint hooks (ruff + djade + std hooks); pytest is CI-only.
- **D12** — First CI run is post-merge push (GitHub Actions fundamental constraint: `pull_request` trigger does not work for workflow files not in default branch); test job uses SQLite default from `base.py:78` (no `DATABASE_URL` override).
- **D13** — `manage.py check --deploy` step REMOVED from Story 1.9 (development settings have `DEBUG=True`; step is placebo with `continue-on-error: true`); deferred to Story 9.6. `workflow_dispatch:` trigger ADDED to enable pre-merge dry-run on throwaway branch.

## 9. Test contract summary

Test file: `tests/test_ci_workflow_config.py` (NEW in Story 1.9 RED phase).
- 37 tests covering AC1-AC9 [MUST] scenarios (workflow structure + pre-commit config structure + security/anti-pattern guards).
  - 34 tests authored in TEA 3.1 (RED) phase.
  - 3 additional tests added in TEA review iteration (2026-05-29): `test_pre_commit_config_no_cyrillic_characters`, `test_ci_all_jobs_use_actions_checkout_v4_or_higher`, `test_ci_build_job_uses_setup_buildx_action` — close coverage gaps in contract sections 2.4, 2.5, 3.4 + 5.
- Tests are pure YAML structure validation — parse `.github/workflows/ci.yml` and `.pre-commit-config.yaml` with `yaml.safe_load()` and assert key/value contracts.
- NO Django involvement (no `@pytest.mark.django_db`, no settings import).
- NO Docker / network calls (tests are deterministic filesystem reads).
- All tests MUST FAIL in RED phase (`pytest.fail("Missing required file: ...")` raised by fixtures because `.github/workflows/ci.yml` and `.pre-commit-config.yaml` do not yet exist).
- AC5, AC7, AC8 are intentionally untested (documentation-only / manual sign-off — per story Testing section).

---

**End of Story 1.9 Interface Contract**
