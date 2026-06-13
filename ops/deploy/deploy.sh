#!/usr/bin/env bash
# CORIC_AGRAR — Deploy orkestracija na Hetzner VPS (Story 9.2).
#
# Ordered, IDEMPOTENTAN deploy: ponovno pokretanje istog deploy-a NE menja stanje
# i NE pada (AC3). Sve komande su neinteraktivne (collectstatic --noinput,
# uv sync --frozen, migrate je inherentno idempotentan, compilemessages overwrite .mo).
#
# SOT za ORDERING (project-context:447-454 + SM-D5; M3 reconciliation):
#   git pull -> docker compose pull (NOVI GHCR image PRE migrate/collectstatic;
#   frozen deps su BAKED u taj image — NE `uv sync --frozen` na host-u, vidi M3)
#   -> collectstatic --noinput -> migrate --plan -> migrate
#   -> compilemessages -> up -d django (re-create) -> up -d nginx (reload bind-mount conf)
#   -> healthcheck UNUTAR django kontejnera (interni :8000; M4) (POSLE re-create-a).
#
# KRITICNI ordering invariants (test-locked, AC2):
#   - docker compose pull STRIKTNO PRE migrate/collectstatic (inace stari image — SM-D5).
#   - migrate (apply) STRIKTNO PRE up -d django re-create-a (novi kod NE sme udariti
#     u staru semu).
#   - migrate --plan (pre-check) PRE migrate (apply).
#   - collectstatic PRE re-create-a (static volume svez kad nginx servira).
#   - healthcheck POSLE re-create-a (verifikuje NOVE kontejnere).
#
# NIKAD force push (AC4) — rollback ide kroz git checkout/revert (rollback.sh).

set -euo pipefail

# Naming convention: srpska latinica + engleski identifikatori; bez cirilice.

# ── CWD guard (M6) ─────────────────────────────────────────────────────────────
# Resolvuj repo root iz lokacije skripte (ops/deploy/deploy.sh -> ../.. = repo root)
# i cd-uj tamo da relativne compose/ops putanje resolve-uju bez obzira odakle se
# skripta poziva (cron/SSH/manual iz proizvoljnog dir-a). Bez ovoga `compose/...`
# putanje fail-uju van repo root-a.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${REPO_ROOT}"

COMPOSE_FILE="compose/production.yml"

# ── .env za Compose interpolaciju (KRITICNO — G-5 fix) ─────────────────────────
# `docker compose --env-file "${ENV_FILE}" -f compose/production.yml` (sa -f) ne ucitava repo-root `.env` za
# `${...}` interpolaciju automatski (Compose interpolation .env se trazi u project dir =
# compose/, NE repo root). Bez `--env-file`, IMAGE_TAG/POSTGRES_PASSWORD/DJANGO_SECRET_KEY
# bi resolve-ovali na PRAZNE default-e (postgres bez password-a, django prazan secret, image
# :latest umesto :production) -> slomljen deploy. Eksplicitan --env-file resava interpolaciju.
# (env_file: ../.env u servisu puni samo django KONTEJNER; `environment:` blok ga override-uje
# interpolacijom — zato interpolacija MORA da nadje .env.)
ENV_FILE="${REPO_ROOT}/.env"
if [[ ! -f "${ENV_FILE}" ]]; then
    echo "[DEPLOY ERROR] ${ENV_FILE} ne postoji. Compose interpolacija (image tag, DB password, secret) bi bila prazna -> slomljen deploy. Kreiraj .env na boxu pre deploy-a (vidi ops/secrets/README.md)." >&2
    exit 1
fi

# Argument $1 = environment (staging|production). Fail-loud usage ako nedostaje.
ENVIRONMENT="${1:-}"
if [[ -z "${ENVIRONMENT}" ]]; then
    echo "Usage: ops/deploy/deploy.sh <staging|production>" >&2
    exit 2
fi
if [[ "${ENVIRONMENT}" != "staging" && "${ENVIRONMENT}" != "production" ]]; then
    echo "[DEPLOY ERROR] Nepoznat environment: '${ENVIRONMENT}' (ocekivano: staging|production)." >&2
    exit 2
fi

echo "[DEPLOY] Pokrecem deploy za environment=${ENVIRONMENT} ($(date -u +%Y-%m-%dT%H:%M:%SZ))"

# ── Concurrency lock (Task 2.4b) ───────────────────────────────────────────────
# On-box flock guard protiv CI+manual interleave-a (GH Actions concurrency stiti
# SAMO CI-side). Ako je deploy vec u toku, fail-loud umesto isprepletanja koraka.
# Osiguraj da lock direktorijum postoji (M6 — /var/lock moze faliti na nekim sistemima).
mkdir -p /var/lock 2>/dev/null || true
LOCKFILE="/var/lock/coric-deploy.lock"
exec 200>"${LOCKFILE}"
if ! flock -n 200; then
    echo "[DEPLOY ERROR] Deploy je vec u toku (lockfile ${LOCKFILE}). Prekidam." >&2
    exit 1
fi

# ── Dirty-tree guard (Task 2.4a) ───────────────────────────────────────────────
# PRE git pull: fail-loud ako je working tree prljav (nekomitovane izmene). NE
# git stash-uj-pa-nastavi (stash moze tiho odbaciti izmene / konfliktovati pri pop-u).
if [[ -n "$(git status --porcelain)" ]]; then
    echo "[DEPLOY ERROR] Git tree je prljav (nekomitovane izmene na boxu)." >&2
    echo "  Resi rucno (commit/revert/clean) PRE deploy-a — NE radim git stash automatski." >&2
    git status --porcelain >&2
    exit 1
fi

# ── 1. git pull ────────────────────────────────────────────────────────────────
echo "[DEPLOY] git pull"
git pull

# ── 2. docker compose pull (OBAVEZNO PRE migrate/collectstatic — SM-D5/AC9) ─────
# Povuci NOVI GHCR image PRE migrate/collectstatic (koji teku KROZ taj image) i PRE
# re-create-a. Goli restart bi zadrzao stari image i deploy ne bi povukao novi kod.
echo "[DEPLOY] docker compose pull (novi GHCR image)"
docker compose --env-file "${ENV_FILE}" -f compose/production.yml pull

# ── 3. Frozen deps su BAKED u GHCR image (M3 — NE `uv sync --frozen` na host-u) ─
# Stack je Docker-image-SOT: prod image (compose/django/Dockerfile prod-builder stage)
# vec radi `uv sync --frozen --no-dev` u build vremenu, pa su frozen deps zapecene u
# image koji je povucen u koraku 2 (docker compose pull). Bare `uv sync --frozen` na
# Hetzner host-u bi fail-ovao (uv mozda nije instaliran na boxu) ILI bio besmislen
# (deps zive u kontejneru, ne na host venv-u). Reconciliation sa project-context koji
# lista `uv sync --frozen`: taj korak pretpostavlja non-Docker/hibridni model; za OVAJ
# Docker-image-SOT deploy frozen deps dolaze kroz image (idempotentno, deterministicki
# iz uv.lock). Marker za grep-lock: uv-sync-frozen-image-baked.

# ── 4. collectstatic --noinput (PRE re-create-a; neinteraktivno = idempotentno) ─
echo "[DEPLOY] collectstatic --noinput"
docker compose --env-file "${ENV_FILE}" -f compose/production.yml run --rm django python manage.py collectstatic --noinput

# ── 5. migrate --plan (assertion/pre-check PRE apply-a) ─────────────────────────
echo "[DEPLOY] migrate --plan (pre-check)"
docker compose --env-file "${ENV_FILE}" -f compose/production.yml run --rm django python manage.py migrate --plan

# ── 6. migrate (apply) — STRIKTNO PRE up -d django re-create-a (AC2) ────────────
# Sema baze mora biti migrirana PRE nego novi Gunicorn worker-i pocnu da sluze
# (inace novi kod udara u staru semu). INHERENTNI deploy ugovor (forward-dep iz 9.1).
echo "[DEPLOY] migrate (apply)"
docker compose --env-file "${ENV_FILE}" -f compose/production.yml run --rm django python manage.py migrate

# ── 7. compilemessages (sr/hu/en .mo build; overwrite = idempotentno) ──────────
echo "[DEPLOY] compilemessages"
docker compose --env-file "${ENV_FILE}" -f compose/production.yml run --rm django python manage.py compilemessages

# ── 8. up -d django (re-create sa novim image-om; NE goli restart — SM-D5) ──────
echo "[DEPLOY] up -d django (re-create)"
docker compose --env-file "${ENV_FILE}" -f compose/production.yml up -d django

# ── 9. up -d nginx (re-create da pokupi bind-mount-ovan nginx.conf — AC14/SM-D9) ─
# Goli restart django NE dostize nginx.conf izmenu (conf je bind-mount, SM-D9).
# M1 (steady-state swap): production.yml nginx servis bind-mount-uje
# ./nginx/.active-default.conf -> default.conf. U normalnom (ne-prvom) deploy-u
# .active-default.conf MORA biti pun 443 conf, pa ga ovde kopiramo iz nginx.conf-a PRE
# re-create-a. nginx-init.sh radi bootstrap swap (bootstrap->active->certbot->full->active)
# samo pri PRVOM izdavanju cert-a; steady-state deploy uvek servira pun 443 conf.
echo "[DEPLOY] aktiviram pun nginx.conf (.active-default.conf) pre nginx re-create-a"
cp compose/nginx/nginx.conf compose/nginx/.active-default.conf
echo "[DEPLOY] up -d nginx (reload bind-mount conf)"
docker compose --env-file "${ENV_FILE}" -f compose/production.yml up -d nginx

# ── 10. Healthcheck (AC10) — POSLE re-create-a (verifikuje NOVE kontejnere) ──────
# Retry-loop UNUTAR django kontejnera (M4): production.yml NE izlaze :8000 na host (nginx
# je jedini izlozen ulaz). Host `curl 127.0.0.1:8000` bi udario u connection refused.
# `docker compose exec -T django python -c urlopen(...)` pogadja Gunicorn na internom :8000
# (zaobilazi nginx 301 redirect i cert zavisnost). Koristimo Python urllib (NE curl) jer
# prod django image NEMA curl (Dockerfile prod stage instalira samo libmagic/poppler/
# postgresql-client/gettext); Python je garantovan. urlopen raise-uje HTTPError na ne-2xx
# → komanda fail-uje (non-zero) → deploy fail-uje ako app ne odgovori 2xx.
echo "[DEPLOY] healthcheck (post re-create, unutar django kontejnera na internom :8000)"
HEALTH_URL="${HEALTHCHECK_URL:-http://127.0.0.1:8000/sr/}"
# Bounded retry-loop: Django+Postgres cold start na CX22 boxu moze potrajati 90-120s
# (gunicorn boot + DB konekcija + prvi request kompilacija). Default 24 pokusaja x 5s
# = 120s budzet; parametrizovano kroz HEALTHCHECK_RETRIES (uvek bounded — nikad hang).
HEALTHCHECK_RETRIES="${HEALTHCHECK_RETRIES:-24}"
HEALTH_OK=0
for attempt in $(seq 1 "${HEALTHCHECK_RETRIES}"); do
    if docker compose --env-file "${ENV_FILE}" -f compose/production.yml exec -T django \
        python -c "import urllib.request; urllib.request.urlopen('${HEALTH_URL}', timeout=5)"; then
        HEALTH_OK=1
        echo "[DEPLOY] healthcheck OK (pokusaj ${attempt})"
        break
    fi
    echo "[DEPLOY] healthcheck pokusaj ${attempt}/${HEALTHCHECK_RETRIES} nije uspeo; cekam..." >&2
    sleep 5
done
if [[ "${HEALTH_OK}" -ne 1 ]]; then
    echo "[DEPLOY ERROR] Healthcheck NIJE prosao posle re-create-a (${HEALTH_URL})." >&2
    exit 1
fi

echo "[DEPLOY] Deploy uspesno zavrsen za environment=${ENVIRONMENT}."
