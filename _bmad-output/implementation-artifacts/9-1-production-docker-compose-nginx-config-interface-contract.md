# Interface Contract — Story 9.1: Production Docker Compose + Nginx Config

**Status:** RED phase (TEA). Definiše tačno šta Dev MORA isporučiti da TEA INFRA-VERIFY testovi
(`tests/test_production_stack.py`) prođu. Ovo je SPECIFIKACIJA, ne implementacija.

**Story:** `9-1-production-docker-compose-nginx-config` (risk_tier MEDIUM, needs_e2e=false, migrations=0,
new_dependencies=1 → gunicorn). Test fajl: `tests/test_production_stack.py`.

---

## 1. Fajlovi koje Dev MORA da kreira/izmeni

| Putanja | NEW/UPDATE | Svrha |
|---|---|---|
| `compose/production.yml` | NEW | Prod stack (postgres + django/Gunicorn + nginx + glitchtip placeholder) |
| `compose/nginx/nginx.conf` | NEW | Reverse proxy + gzip + direktan static/media + 3 security headera |
| `compose/nginx/Dockerfile` | NEW | `nginx:1.27-alpine` + COPY nginx.conf |
| `compose/django/start.sh` | NEW (LF!) | wait-for-db + `exec gunicorn ...` (BEZ migrate) |
| `compose/django/Dockerfile` | UPDATE | Prod `--no-dev` build put + COPY start.sh + chmod (dev put NETAKNUT) |
| `config/settings/production.py` | UPDATE | env-driven `SECURE_SSL_REDIRECT` + dodaj `CSRF_TRUSTED_ORIGINS` (EXTEND) |
| `pyproject.toml` | UPDATE | `gunicorn>=23.0` u `[project].dependencies` (NE dev grupa) |
| `uv.lock` | UPDATE | regenerisan (`uv lock`) — sadrži gunicorn |
| `justfile` | UPDATE (opc) | `prod-config`/`prod-build`/`prod-up`/`prod-down` (NE diraj `dev-*`) |
| `.env.example` | UPDATE (opc) | prod var komentari (WEB_CONCURRENCY, DJANGO_SECURE_SSL_REDIRECT, DJANGO_CSRF_TRUSTED_ORIGINS) |

**Negative scope (NE diraj):** `compose/local.yml`, `compose/django/entrypoint.sh`, dev put u
`compose/django/Dockerfile` (linija 23 `uv sync --frozen --no-install-project`), postojeći HTTPS hardening
u `production.py` (HSTS/PROXY_SSL_HEADER/STORAGES/X_FRAME).

---

## 2. `compose/production.yml` kontrakt

- **`name: coric_agrar_production`** (prod-scoped projekat ime).
- **`docker compose -f compose/production.yml config` → exit 0** (validan Compose schema; `.env` postoji u repo-u
  za env-file rezoluciju).
- **Servisi (`services:`):**
  - `postgres` — `postgres:16-alpine`, `healthcheck` sa `pg_isready`, mount `postgres_data` named volume,
    **BEZ host port expose** (interni Docker DNS samo), credentials kroz `env_file`/secrets — **NIKAD inline
    `coric:coric`** (G-5).
  - `django` — build iz `compose/django/Dockerfile` (prod `--no-dev` put), `environment:` postavlja
    **`DJANGO_SETTINGS_MODULE: config.settings.production`** (AC6), **`entrypoint: ["/start.sh"]` EKSPLICITNO**
    (G-10/SM-D2 — override-uje Dockerfile ENTRYPOINT da migrate NE radi; NE `command:`-only),
    `depends_on: postgres service_healthy`, **BEZ host port expose** (interno :8000 samo), mount `staticfiles`
    + `media` named volume (read-write).
  - `nginx` — build iz `compose/nginx/Dockerfile`, **`ports: "80:80"`** (jedini izložen ulaz; +443 za prod TLS),
    `depends_on: django`, mount `staticfiles` + `media` **read-only (`:ro`)**.
  - `glitchtip` — **PLACEHOLDER/zakomentarisan** (sa `# Epic 9.3` markerom) — NIJE aktivan parsiran servis.
    `docker compose config` NE sme da ga prikaže kao aktivan servis.
- **`volumes:` (top-level):** `postgres_data`, `staticfiles`, `media` — sva tri DEKLARISANA named volume-a
  (prod-scoped imena). `media` MORA biti deklarisan jer nginx `location /media/` referencira mount.

**Compose service names:** `postgres`, `django`, `nginx` (+ `glitchtip` placeholder/zakomentarisan).
**Named volumes:** `postgres_data`, `staticfiles`, `media`.

---

## 3. `compose/nginx/nginx.conf` kontrakt (grep-lock direktive)

MORA sadržati (grep-asercije):
- `upstream django { server django:8000; }` **ILI** `proxy_pass http://django` + `server django:8000`
  (Docker DNS ime servisa, port 8000).
- `proxy_set_header X-Forwarded-Proto $scheme` (G-3 — KLJUČNO da `SECURE_PROXY_SSL_HEADER` radi bez redirect loop-a).
  + `proxy_set_header Host`, `X-Real-IP`, `X-Forwarded-For` (preporuka).
- `location /static/` blok (direktan static serving iz volume-a, NE proxy na Django).
- `location /media/` blok (direktan media).
- `gzip on;` (+ `gzip_types`).
- **3 security headera, svaki sa `always` flagom** (G-7):
  - `add_header X-Frame-Options "DENY" always;`
  - `add_header X-Content-Type-Options "nosniff" always;`
  - `add_header Referrer-Policy "same-origin" always;`
- HTTP `server { listen 80; }` blok FUNKCIONALAN (smoke radi bez cert-a). HTTPS/443 blok placeholder/zakomentarisan
  cert putanje (SM-D5; 9.2 certbot popunjava).

---

## 4. `compose/django/start.sh` kontrakt

- **LF line endings** (G-1 — NE CRLF; binary-check `\r\n` odsutan).
- Sadrži **`gunicorn config.wsgi:application`**.
- `--bind 0.0.0.0:8000`.
- Workers token: `--workers ${WEB_CONCURRENCY:-5}` (ILI `WEB_CONCURRENCY` env / `2*CPU+1=5` formula u komentaru) (AC5).
- `--timeout` (npr. `${GUNICORN_TIMEOUT:-60}`).
- **NE sadrži `migrate`** (negativni grep — project-context:478; migrate je 9.2 deploy-step).
- wait-for-db (`pg_isready`) reuse iz entrypoint logike, ALI BEZ migrate.
- `exec gunicorn ...` (signal propagacija).

---

## 5. `config/settings/production.py` kontrakt (EXTEND, NE prepisuj)

- **`SECURE_SSL_REDIRECT = env.bool("DJANGO_SECURE_SSL_REDIRECT", default=True)`** (SM-D7/OQ-3) —
  env-driven; default `True` čuva prod hardening; smoke override `False` → realan 200 round-trip (G-11).
- **`CSRF_TRUSTED_ORIGINS = env.list("DJANGO_CSRF_TRUSTED_ORIGINS", default=[])`** (G-9/Adversarial #2) —
  bez ovoga 403 na svaki cross-origin POST sa `CSRF_COOKIE_SECURE=True`.
- **EXTEND verify (NETAKNUTO):** `SECURE_PROXY_SSL_HEADER == ("HTTP_X_FORWARDED_PROTO","https")`,
  `STORAGES["staticfiles"]` = Whitenoise `CompressedManifestStaticFilesStorage`, `SECURE_HSTS_SECONDS`,
  `X_FRAME_OPTIONS == "DENY"`, `SECURE_REFERRER_POLICY == "same-origin"`, `DEBUG is False`.

**Settings keys (verifikuju se):** `SECURE_SSL_REDIRECT` (env-driven), `CSRF_TRUSTED_ORIGINS` (env.list),
`SECURE_PROXY_SSL_HEADER`, `STORAGES`, `SECURE_HSTS_SECONDS`, `X_FRAME_OPTIONS`, `SECURE_REFERRER_POLICY`, `DEBUG`.

---

## 6. `pyproject.toml` + `uv.lock` kontrakt

- `gunicorn>=23.0` (ili `>=23`) u **`[project].dependencies`** (runtime WSGI — NE `[dependency-groups].dev`).
- `gunicorn` prisutan u `uv.lock`.
- `makemigrations --check` = „No changes" (0 migracija — 9.1 ne dira modele) / nema novih migration fajlova.

---

## 7. Smoke (MANDATORY container) kontrakt — Docker dostupan (v29.1.3 / compose v2.40)

- Marker: `@pytest.mark.docker` (registrovan u `pyproject.toml [tool.pytest.ini_options].markers` od strane TEA test fajla / select-deselect kroz `-m "not docker"`).
- Env: `DJANGO_SECURE_SSL_REDIRECT=False`, `DJANGO_CSRF_TRUSTED_ORIGINS=http://localhost`,
  `DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1`, `DJANGO_SECRET_KEY`, `DATABASE_URL`.
- `up -d` → seed `run --rm django collectstatic --noinput` → `curl -I http://localhost/sr/` → **200** (NE 502/301)
  + 3 security headera → `curl -I http://localhost/static/<fajl>` → 200 → `down -v` (try/finally cleanup).

---

## Sažetak (machine-readable)

- **files:** `compose/production.yml`, `compose/nginx/nginx.conf`, `compose/nginx/Dockerfile`,
  `compose/django/start.sh`, `compose/django/Dockerfile`, `config/settings/production.py`, `pyproject.toml`,
  `uv.lock`, `justfile`, `.env.example`
- **services:** `postgres`, `django`, `nginx`, `glitchtip` (placeholder/zakomentarisan)
- **volumes:** `postgres_data`, `staticfiles`, `media`
- **nginx_directives:** `upstream django` / `server django:8000`, `proxy_pass http://django`,
  `proxy_set_header X-Forwarded-Proto $scheme`, `location /static/`, `location /media/`, `gzip on`,
  `add_header X-Frame-Options "DENY" always`, `add_header X-Content-Type-Options "nosniff" always`,
  `add_header Referrer-Policy "same-origin" always`
- **settings_keys:** `SECURE_SSL_REDIRECT` (env.bool default True), `CSRF_TRUSTED_ORIGINS` (env.list default []),
  `SECURE_PROXY_SSL_HEADER`, `STORAGES`, `SECURE_HSTS_SECONDS`, `X_FRAME_OPTIONS`, `SECURE_REFERRER_POLICY`, `DEBUG`
