---
story-id: "1.3"
story-key: 1-3-docker-compose-za-local-environment
artifact: interface-contract
phase: RED (TDD)
author: TEA (autonomous)
created: 2026-05-28
---

# Interface Contract — Story 1.3 (Docker Compose za Local Environment)

Ovaj dokument definiše **machine-verifiable** post-implementation stanje za Story 1.3. Dev (implementator) **NE SME** menjati `tests/test_docker_compose.py` — mora menjati filesystem/source code tako da svi testovi pređu sa RED na GREEN.

Testovi su organizovani po AC: `tests/test_docker_compose.py`. Pokretanje:
```
uv run pytest tests/test_docker_compose.py -v
```
(iz `C:\Programming\dev-bmad\CORIC_AGRAR`)

> Napomena: Testovi su **filesystem + static-analysis** nivoa. **NE** pokreću `docker compose up` (sporо, fragile, port collision risk). Pokreću samo `docker compose -f compose/local.yml config` za YAML/schema validaciju (fast static check). Ako `docker` CLI nije na PATH-u, ti testovi se **skip**-uju sa jasnom porukom.

---

## 1. Filesystem state — fajlovi koji MORAJU postojati nakon implementacije

| Path | Tip | Opis | AC |
|---|---|---|---|
| `compose/` | dir | Novi direktorijum u root-u | AC1 |
| `compose/django/` | dir | Sub-direktorijum za Django image | AC1 |
| `compose/local.yml` | file | Docker Compose definicija sa `django` + `db` servisima | AC1, AC4 |
| `compose/django/Dockerfile` | file | Multi-stage `uv` build (builder + runtime) | AC1, AC2 |
| `compose/django/entrypoint.sh` | file | Wait-for-db → migrate → exec CMD; **LF endings** | AC1, AC3 |
| `.dockerignore` | file | Slim build context, isključuje secrets/.venv/tests | AC5 |
| `.gitattributes` | file | Narrow LF enforcement za `*.sh` + eksplicitno `entrypoint.sh`; **bez** `* text=auto eol=lf` (iter-1 fix) | AC1 |

### 1.1 Fajlovi koji se MODIFIKUJU (postojeći)

| Path | Promene | AC |
|---|---|---|
| `justfile` | `dev:` recept rewired na `docker compose -f compose/local.yml up`; novi `dev-build`, `dev-down`, `dev-logs`, `dev-shell`, `dev-manage` recepti dodati. `test`, `lint`, `migrate`, `messages` ostaju nepromenjeni. | AC6 |
| `.env.example` | `DATABASE_URL=postgres://coric:coric@db:5432/coric_agrar` (`@db:`, NE `@localhost:`); ukloniti komentar "Story 1.2 default je SQLite". | AC7 |

### 1.2 Fajlovi koji se NE diraju (regression guard)

| Path | Razlog |
|---|---|
| `pyproject.toml`, `uv.lock` | Nema deps promena u Story 1.3 |
| `manage.py`, `config/wsgi.py`, `config/asgi.py` | Story 1.2 ih je već postavio na `config.settings.development` |
| `config/settings/{base,development,staging,production}.py` | Story 1.2 SOT |
| `.gitignore` | Story 1.1 baseline (Docker pravila već prisutna) |

---

## 2. `compose/django/Dockerfile` — multi-stage uv build kontrakt

| Zahtev | Pattern (regex/text check) | Test |
|---|---|---|
| Multi-stage build | `FROM ... AS builder` + `FROM ... AS runtime` | `test_ac2_dockerfile_is_multi_stage` |
| `uv sync --frozen` u builder stage-u | source contains `uv sync --frozen` (sa `--no-install-project --no-dev`) | `test_ac2_dockerfile_uses_uv_sync_frozen` |
| Python 3.13 base | runtime image `python:3.13-slim` | `test_ac2_dockerfile_python_313` |
| System deps u runtime-u | apt installs `libmagic1`, `poppler-utils`, `postgresql-client` (gettext optional ali story spec ga uključuje) | `test_ac2_dockerfile_system_deps_present` |
| COPY venv iz builder-a | `COPY --from=builder /app/.venv /app/.venv` | `test_ac2_dockerfile_copies_venv_from_builder` |
| ENTRYPOINT set | `ENTRYPOINT` linija referencira `entrypoint.sh` (apsolutna putanja `/entrypoint.sh`) | `test_ac2_dockerfile_sets_entrypoint` |
| Nema baked-in secrets | `ENV DJANGO_SECRET_KEY=` NE postoji | `test_dockerfile_no_secrets_baked_in` |

---

## 3. `compose/django/entrypoint.sh` — startup orchestration kontrakt

| Zahtev | Pattern | Test |
|---|---|---|
| LF line endings (NE CRLF) | binary read: `b"\r\n" not in content` | `test_ac3_entrypoint_has_lf_line_endings` |
| Shebang `#!/usr/bin/env bash` | prva linija | (covered by `set -euo pipefail` test indirectly) |
| Strict mode | `set -euo pipefail` u prvih par linija | `test_ac3_entrypoint_has_set_euo_pipefail` |
| Wait-for-db loop | `pg_isready` poziv u skripti | `test_ac3_entrypoint_has_pg_isready_wait_loop` |
| Migracije run | `manage.py migrate` poziv | `test_ac3_entrypoint_runs_migrate` |
| Signal propagation | poslednja non-empty / non-komentar linija je `exec "$@"` | `test_ac3_entrypoint_ends_with_exec_dollar_at` |

---

## 4. `compose/local.yml` — Docker Compose strukturni kontrakt

| Zahtev | Provera | Test |
|---|---|---|
| Validna YAML schema + referencije | `docker compose -f compose/local.yml config --quiet` exit 0 (skip ako docker CLI nije na PATH-u) | `test_ac4_compose_yaml_is_valid`, `test_ac8_compose_config_validation_passes` |
| `services` ima `django` i `db` ključeve | YAML parse | `test_ac4_compose_has_django_and_db_services` |
| Top-level `volumes:` ima `postgres_data` i `django_venv` | YAML parse | `test_ac4_compose_has_named_volumes` |
| `db` servis ima `healthcheck` blok | YAML parse | `test_ac4_compose_db_has_healthcheck` |
| `django` servis ima `depends_on.db.condition: service_healthy` | YAML parse | `test_ac4_compose_django_depends_on_db_healthy` |
| `db.image` pinovan na PostgreSQL 16 (`postgres:16-alpine` ili `postgres:16`); NE `:latest` | YAML parse | `test_ac4_compose_postgres_image_pinned_16` |
| `django.env_file` referencira `../.env` (relativni put do root-a) | YAML parse | `test_ac4_compose_django_uses_env_file_from_root` |
| `django.build.context` je `../` (root repo-a; Gotcha #11) | YAML parse | `test_ac4_compose_django_build_context_is_repo_root` |
| `django.volumes` ima BOTH bind mount source + named volume `django_venv:/app/.venv` (Gotcha #1 overlay zaštita) | YAML parse | `test_ac4_compose_django_named_volume_overlays_dot_venv` |
| Nema inline secrets (samo placeholder `coric` password) | regex za 30+ char random-looking strings | `test_no_inline_secrets_in_compose` |

---

## 5. `.dockerignore` — slim build context

| Zahtev | Test |
|---|---|
| Fajl postoji u root-u | `test_ac5_dockerignore_exists` |
| Sadrži obavezne exclude pattern-e: `.venv`, `__pycache__`, `_bmad-output`, `_bmad`, `.git`, `.env` | `test_ac5_dockerignore_excludes_critical_paths` |
| **NE** ignoriše `.env.example` (potreban runtime kao template; iako u image-u nije nužan, ne sme biti ignorisan na nivou pattern-a) | `test_ac5_dockerignore_excludes_critical_paths` (negative substring check) |

---

## 6. `justfile` — task runner kontrakt

| Zahtev | Test |
|---|---|
| `dev:` recept telo koristi `docker compose -f compose/local.yml up` | `test_ac6_justfile_dev_recipe_uses_docker_compose` |
| Bar jedan od `dev-build`, `dev-down`, `dev-logs`, `dev-shell`, `dev-manage` recepata postoji (story Task 7 traži svih 5) | `test_ac6_justfile_has_dev_helpers` |
| `test`, `lint`, `migrate`, `messages` recepti i dalje postoje (regression guard) | `test_ac6_justfile_preserves_story_1_1_recipes` |

---

## 7. `.env.example` — DATABASE_URL update kontrakt

| Zahtev | Test |
|---|---|
| `DATABASE_URL=postgres://coric:coric@db:5432/coric_agrar` linija prisutna (host `db`, NE `localhost`) | `test_ac7_env_example_database_url_uses_docker_hostname` |
| Komentar "Story 1.2 default je SQLite" UKLONJEN | `test_ac7_env_example_dropped_sqlite_default_comment` |

---

## 8. `.gitattributes` — narrow scope kontrakt (iter-1 fix)

| Zahtev | Test |
|---|---|
| Fajl postoji u root-u | `test_ac1_gitattributes_exists_with_narrow_scope` |
| Sadrži `*.sh text eol=lf` i `compose/django/entrypoint.sh text eol=lf` | `test_ac1_gitattributes_exists_with_narrow_scope` |
| **NE** sadrži bare `* text=auto eol=lf` (whole-file diff churn risk) | `test_ac1_gitattributes_exists_with_narrow_scope` |

---

## 9. Smoke validacija — static prereqs (no docker up)

| Zahtev | Test |
|---|---|
| `docker compose -f compose/local.yml config --quiet` exit 0 (skip ako docker nije instaliran) | `test_ac8_compose_config_validation_passes` |
| Dockerfile syntax sanity (svaka linija počinje validnom Dockerfile instrukcijom ili komentarom ili je prazna) | `test_ac8_dockerfile_can_be_lex_parsed` |

---

## 10. Out-of-scope za Story 1.3 (NE testirati)

- Stvarni `docker compose up` runtime (slow, fragile, port collisions) — manual smoke u Task 11.x story-ja
- Browser smoke (`http://localhost:8000`) — Task 11.7 story-ja, manual
- Hot-reload provera — Task 11.10, manual
- Volume persistence stvarno testiranje — Task 11.9, manual
- Staging/production compose fajlovi — Story 9.1
- Nginx servis — Story 9.1
- `start.sh` (gunicorn launcher) — Story 9.1
