---
story-id: "1.1"
story-key: 1-1-project-bootstrap-sa-uv-i-django
artifact: interface-contract
phase: RED (TDD)
author: TEA (autonomous)
created: 2026-05-27
---

# Interface Contract — Story 1.1 (Project Bootstrap sa uv i Django)

Ovaj dokument definiše **machine-verifiable** post-bootstrap stanje koje implementacija mora da zadovolji. Svaki AC iz story spec fajla mapira se na konkretne assertion-e u `tests/test_bootstrap.py`. Dev (implementator) **NE** smije menjati testove — mora promeniti filesystem/dependencies tako da svi testovi budu green.

---

## 1. Filesystem state (post-bootstrap)

### 1.1 Fajlovi koji MORAJU postojati u root-u projekta (`C:/Programming/dev-bmad/CORIC_AGRAR/`)

| Path | Opis | Izvor (story AC) |
|---|---|---|
| `pyproject.toml` | uv-managed config sa `[project]` + `[dependency-groups]` tabelama | AC1, AC2, AC4 |
| `uv.lock` | Lock fajl sa resolved verzijama (committable artifact) | AC1, AC2 |
| `.python-version` | Sadržaj počinje sa `3.13` (može `3.13`, `3.13.0`, `3.13.1`…) | AC1, AC6 |
| `.gitignore` | Postojeći BMad baseline preserved + dodati Python/Django/uv pattern-i | AC6 |
| `README.md` | Naslov + opis + Quickstart sekcija sa `uv sync` i `manage.py runserver` | AC6 |
| `justfile` | Sadrži recepte `dev`, `test`, `lint`, `migrate`, `messages` | AC5 |
| `manage.py` | Django entry point (generisan kroz `django-admin startproject config .`) | AC3 |
| `config/__init__.py` | Django settings package marker | AC3 |
| `config/settings.py` | Single-file settings (split dolazi u Story 1.2 — NE diraj u 1.1) | AC3 |
| `config/urls.py` | Default Django URL conf | AC3 |
| `config/wsgi.py` | WSGI entry point | AC3 |
| `config/asgi.py` | ASGI entry point | AC3 |

### 1.2 Fajlovi koji NE smeju postojati (out-of-scope za Story 1.1)

| Path | Razlog | Test |
|---|---|---|
| `main.py`, `hello.py` | Auto-generated od `uv init`, mora biti obrisan (Task 1.5) | `test_ac3_uv_init_placeholder_files_removed` |
| `src/` | Samo ako je `--lib` flag korišćen — kod nas NIJE |
| `.env`, `.env.example` | Story 1.2 |
| `apps/`, `templates/`, `static/`, `locale/`, `media/`, `compose/` | Kasnije story-je |
| `Dockerfile`, `.pre-commit-config.yaml`, `.github/` | Story 1.3 / 1.9 |
| `config/settings/` (folder) | Settings split dolazi u Story 1.2 — sad single-file `config/settings.py` |

---

## 2. `pyproject.toml` struktura (PEP 621 + PEP 735)

### 2.1 `[project]` tabela — `dependencies` lista (14 paketa, AC2)

`dependencies = [...]` mora sadržati (provera po **package name prefiks-u**, version pin može varirati):

| # | Package name | Min. version constraint |
|---|---|---|
| 1 | `django` | `>=5.2` |
| 2 | `psycopg` | sa `[binary]` extras |
| 3 | `django-modeltranslation` | latest |
| 4 | `django-htmx` | latest |
| 5 | `django-template-partials` | latest |
| 6 | `django-bootstrap5` | latest |
| 7 | `django-environ` | latest |
| 8 | `django-anymail` | latest |
| 9 | `django-ratelimit` | latest |
| 10 | `django-axes` | latest |
| 11 | `django-csp` | latest |
| 12 | `sorl-thumbnail` | latest |
| 13 | `pdf2image` | latest |
| 14 | `python-magic` | latest |

### 2.2 `[dependency-groups]` tabela — `dev` lista (7 paketa, AC4 / PEP 735)

`[dependency-groups]` mora postojati i sadrži:

**KRITICNO:** `[tool.uv.dev-dependencies]` legacy tabela NE sme postojati. Test `test_ac4_no_legacy_uv_dev_dependencies_table` direktno proverava ovo. Ako postoje OBE tabele (mesane), test pada — ukloni legacy.

Sadrzaj `dev` liste:

| # | Package name |
|---|---|
| 1 | `pytest` |
| 2 | `pytest-django` |
| 3 | `ruff` |
| 4 | `djade` |
| 5 | `pre-commit` |
| 6 | `playwright` |
| 7 | `django-debug-toolbar` |

### 2.3 Separacija glavnih i dev deps (AC4)

Glavni `[project].dependencies` ne sme sadržati nijedan dev paket (npr. `pytest`, `ruff`, `djade`, `pre-commit`, `playwright`, `django-debug-toolbar` nisu u glavnoj listi).

---

## 3. `justfile` recepti (AC5)

`justfile` u root-u mora definisati **najmanje** sledeće recepte (definicija = `<naziv>:` na početku reda, bez indentacije):

| Recipe | Tipičan sadržaj |
|---|---|
| `dev` | `uv run python manage.py runserver` (placeholder za Story 1.3) |
| `test` | `uv run pytest` |
| `lint` | `uv run ruff check .` (+ opciono `djade --check templates/`) |
| `migrate` | `uv run python manage.py migrate` |
| `messages` | `uv run python manage.py makemessages -a` + `compilemessages` |

Dodatni recepti (`default`, `lint-fix`, `shell`, itd.) su DOZVOLJENI ali NISU obavezni.

---

## 4. `.gitignore` preservation pravila (AC6)

Postojeći BMad baseline `.gitignore` ima kritična carve-out pravila koja moraju da prežive `uv init` korak. Test verifikuje da sledeći pattern-i ostaju u `.gitignore`-u:

| Pattern (substring match) | Razlog |
|---|---|
| `docs/Dizajn/` | 1.3 GB design assets — ne sme ući u git |
| `.claude/skills/` | BMad installer carve-out |
| `_bmad/bmm/` | BMad installer carve-out |
| `bmad-orchestrators-bundle/` | Portable orchestrator bundle (duplikat) |
| `.env` | Tajne — secret-safe |
| `__pycache__/` | Python bytecode |
| `.venv/` | Virtual environment |

---

## 5. Komandni outputi (smoke testovi)

### 5.1 `uv --version` (AC1)

```
$ uv --version
uv 0.5.x (ili viša verzija)
```

Verifikacija: parse-uj prvi numerički token posle "uv " — major mora biti `0` a minor `>= 5`, ILI major `>= 1`.

### 5.2 `uv run python manage.py check` (AC3)

```
$ uv run python manage.py check
System check identified no issues (0 silenced).
```

Exit code: `0`. Output sadrži substring `0 silenced` ILI `no issues`.

### 5.3 Django version probe (AC3)

```
$ uv run python -c "import django; print(django.__version__)"
5.2.x (ili viša verzija)
```

Verifikacija: parse-uj string `<major>.<minor>...` — `major >= 5` i (`major > 5` ili `minor >= 2`).

### 5.4 `uv run pytest --version` (AC4)

Mora se izvršiti sa exit code `0` i ispisati verziju (substring `pytest`).

### 5.5 `uv run ruff --version` (AC4)

Mora se izvršiti sa exit code `0` i ispisati verziju (substring `ruff`).

---

## 6. Validacioni testovi — pytest fajl

Definicija testova: `C:/Programming/dev-bmad/CORIC_AGRAR/tests/test_bootstrap.py`.

Kategorije i target broj testova:

| AC | Test count (target) | Šta testira |
|---|---|---|
| AC1 | 4 | pyproject.toml exists, .python-version starts with 3.13, uv.lock exists, uv >= 0.5 |
| AC2 | 3 | django+psycopg (+ `[binary]` extras), htmx-related (4 paketa), image/security (8 paketa) — svih 14 mora biti present |
| AC3 | 4 | config/ skeleton fajlovi, manage.py exists, `manage.py check` exits 0, `uv init` placeholders (main.py/hello.py) obrisani |
| AC4 | 3 | 7 dev deps prisutni u `[dependency-groups].dev`, separation (no dev pkg u glavnim deps), legacy `[tool.uv.dev-dependencies]` ODSUTAN |
| AC5 | 2 | justfile exists, ima recepte dev/test/lint/migrate/messages |
| AC6 | 4 | BMad gitignore pravila preserved, Python/Django pattern-i prisutni, .python-version NIJE gitignored, README.md exists sa Quickstart sekcijom |

**Total:** 20 testova.

**Napomena za Dev (.python-version):** Postojeci BMad baseline `.gitignore` (linija ~36) IGNORISE `.python-version`. Story 1.1 zahteva da bude **commitable**. Dev MORA ukloniti tu liniju iz `.gitignore`-a (samo tu liniju, NE ceo `uv` blok). Test `test_ac6_python_version_not_gitignored` proverava ovo.

---

## 7. Dev konvencije (informacionalno, ne testirano)

- Sav code/comment u srpskoj latinici ili engleskom (no ćirilica).
- `uv.lock` se KOMITUJE (kao npm package-lock.json).
- `.env` se NE KOMITUJE (samo `.env.example` posle Story 1.2).
- Postojeći BMad baseline `.gitignore` ima backup u `.gitignore.bmad-baseline` (radi rollback-a ako `uv init` overwrite-uje).

---

## 8. Out-of-scope (NE testirati u Story 1.1)

- Database connectivity (PostgreSQL kontejneri → Story 1.3)
- Settings split (`config/settings/base.py` itd. → Story 1.2)
- `.env` / `.env.example` (Story 1.2)
- Docker (Story 1.3)
- i18n routing (Story 1.4)
- CSS/Fontovi (Story 1.5)
- `apps/` Django app-ovi (Epic 2+)
- pre-commit konfiguracija (Story 1.9)
- GitHub Actions (Story 1.9)
- Playwright browser binaries (Story 9.8)
- Functional tests (Epic 2 story 2.1)

---

## 9. Pass criteria (Dev-ovo "definition of done")

Kad Dev završi implementaciju, sledeće mora da bude tačno:

1. Svih ~17 testova u `tests/test_bootstrap.py` prolazi (`pytest tests/test_bootstrap.py -v` → 0 failed).
2. Manual smoke: `uv run python manage.py check` prijavljuje 0 issues.
3. Manual smoke: `uv run pytest --collect-only` exit code 0 (no tests collected je OK — potvrđuje da pytest-django plugin radi).
4. `.gitignore` zadržava sve BMad baseline pattern-e.
5. `uv.lock` je commitovan.

---

**Kraj interface contract-a. Story 1.1 Dev odgovorni za satisfaction svih navedenih obavezivanja.**
