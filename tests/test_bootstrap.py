"""Smoke testovi za Story 1.1 - Project Bootstrap sa uv i Django.

Verifikuje filesystem state i command outputs nakon bootstrap-a:
- AC1: uv project init, .python-version, pyproject.toml, uv.lock
- AC2: 14 core production dependency-ja u [project].dependencies
- AC3: Django project skeleton (config/ + manage.py) i `manage.py check`
- AC4: 7 dev dependency-ja u [dependency-groups].dev (PEP 735)
- AC5: justfile sa receptima dev/test/lint/migrate/messages
- AC6: .gitignore preservation (BMad baseline), .python-version sadrzaj, README.md

Pokrenuti sa:
    python -m pytest tests/test_bootstrap.py -v

Sve testove je TEA napisala u RED fazi TDD-a PRE nego sto Dev pocne
implementaciju. Svi testovi MORAJU pasti dok Dev ne zavrsi Story 1.1.

Naming convention: srpska latinica + engleski; bez cirilice.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

# Python 3.11+ stdlib tomllib; pre-3.11 fallback nije potreban (pin je 3.13).
try:
    import tomllib
except ImportError:  # pragma: no cover
    tomllib = None  # type: ignore[assignment]


# =============================================================================
# Konstante (project paths)
# =============================================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PYPROJECT_PATH = PROJECT_ROOT / "pyproject.toml"
UV_LOCK_PATH = PROJECT_ROOT / "uv.lock"
PYTHON_VERSION_PATH = PROJECT_ROOT / ".python-version"
GITIGNORE_PATH = PROJECT_ROOT / ".gitignore"
README_PATH = PROJECT_ROOT / "README.md"
JUSTFILE_PATH = PROJECT_ROOT / "justfile"
MANAGE_PY_PATH = PROJECT_ROOT / "manage.py"
CONFIG_DIR = PROJECT_ROOT / "config"


# Lista 14 core production deps iz AC2
CORE_DEPENDENCIES = [
    "django",
    "psycopg",
    "django-modeltranslation",
    "django-htmx",
    "django-template-partials",
    "django-bootstrap5",
    "django-environ",
    "django-anymail",
    "django-ratelimit",
    "django-axes",
    "django-csp",
    "sorl-thumbnail",
    "pdf2image",
    "python-magic",
]

# Lista 7 dev deps iz AC4
DEV_DEPENDENCIES = [
    "pytest",
    "pytest-django",
    "ruff",
    "djade",
    "pre-commit",
    "playwright",
    "django-debug-toolbar",
]

# BMad carve-out gitignore pravila koja moraju da prezive `uv init`
BMAD_GITIGNORE_PATTERNS = [
    "docs/Dizajn/",
    ".claude/skills/",
    "_bmad/bmm/",
    "bmad-orchestrators-bundle/",
]


# =============================================================================
# Helper funkcije
# =============================================================================


def _load_pyproject() -> dict:
    """Load pyproject.toml. Raises if it doesn't exist or tomllib not available."""
    if tomllib is None:
        pytest.skip("tomllib nije dostupan (Python < 3.11)")
    if not PYPROJECT_PATH.exists():
        pytest.fail(f"pyproject.toml ne postoji na {PYPROJECT_PATH}")
    with PYPROJECT_PATH.open("rb") as f:
        return tomllib.load(f)


def _extract_package_names(dep_list: list[str]) -> set[str]:
    """Iz liste PEP 508 dep specifikacija ('django>=5.2', 'psycopg[binary]')
    izvuci samo package name-ove u lowercase."""
    names: set[str] = set()
    for spec in dep_list:
        # Skini whitespace, normalize na lowercase
        spec = spec.strip().lower()
        # Package name je sve do prvog [ ili < ili > ili = ili ; ili space
        match = re.match(r"^([a-z0-9_\-\.]+)", spec)
        if match:
            names.add(match.group(1))
    return names


def _run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    """Run subprocess sa shell=False. Returns CompletedProcess (no raise)."""
    return subprocess.run(
        cmd,
        cwd=cwd or PROJECT_ROOT,
        capture_output=True,
        text=True,
        shell=False,
        timeout=120,
    )


# =============================================================================
# AC1 - Bootstrap uv projekta
# =============================================================================


# AC-1: pyproject.toml mora biti kreiran u root-u projekta
def test_ac1_pyproject_toml_exists():
    """AC1: pyproject.toml mora postojati u root-u projekta posle `uv init`."""
    assert PYPROJECT_PATH.exists(), (
        f"pyproject.toml nedostaje na {PYPROJECT_PATH}. "
        f"Pokreni `uv init --python 3.13 --no-readme` u root-u."
    )


# AC-1: .python-version mora postojati i sadrzaj pocinje sa "3.13"
def test_ac1_python_version_file_exists_and_starts_with_3_13():
    """AC1: .python-version pin na Python 3.13.x (moze 3.13, 3.13.0, 3.13.1, ...)."""
    assert PYTHON_VERSION_PATH.exists(), (
        f".python-version nedostaje na {PYTHON_VERSION_PATH}"
    )
    content = PYTHON_VERSION_PATH.read_text(encoding="utf-8").strip()
    assert content.startswith("3.13"), (
        f".python-version mora poceti sa '3.13' (dobijeno: {content!r})"
    )


# AC-1: uv.lock fajl mora postojati (kreira se posle prvog `uv add`)
def test_ac1_uv_lock_exists():
    """AC1: uv.lock je commitable artifact - mora postojati posle `uv add`."""
    assert UV_LOCK_PATH.exists(), (
        f"uv.lock nedostaje na {UV_LOCK_PATH}. "
        f"Trebao bi biti kreiran kao rezultat `uv add` komande."
    )


# AC-1: uv binary mora biti instaliran i verzija >= 0.5 (PEP 735 zahtev)
def test_ac1_uv_version_at_least_0_5():
    """AC1: `uv --version` mora reportovati >= 0.5 (PEP 735 dependency-groups)."""
    uv_bin = shutil.which("uv")
    if uv_bin is None:
        pytest.fail("uv binary nije u PATH-u. Instaliraj uv >= 0.5 prvo.")
    result = _run([uv_bin, "--version"])
    assert result.returncode == 0, (
        f"`uv --version` exit code {result.returncode}, stderr={result.stderr!r}"
    )
    # Output je tipa "uv 0.5.x" ili "uv 1.0.0"
    match = re.search(r"uv\s+(\d+)\.(\d+)", result.stdout)
    assert match, f"Nije parsiranje verzije iz: {result.stdout!r}"
    major, minor = int(match.group(1)), int(match.group(2))
    assert (major, minor) >= (0, 5), (
        f"uv verzija mora biti >= 0.5 (dobijeno: {major}.{minor}). "
        f"PEP 735 [dependency-groups] zahteva uv 0.5+."
    )


# =============================================================================
# AC2 - Instalacija core dependency-ja (14 paketa)
# =============================================================================


# AC-2: Django + psycopg (database stack) prisutni u glavnoj dependencies listi
def test_ac2_django_and_psycopg_in_dependencies():
    """AC2: django>=5.2 i psycopg[binary] u [project].dependencies."""
    pyproject = _load_pyproject()
    deps = pyproject.get("project", {}).get("dependencies", [])
    assert isinstance(deps, list), (
        "[project].dependencies mora biti lista (PEP 621 format)."
    )
    names = _extract_package_names(deps)
    assert "django" in names, (
        f"`django` nedostaje u dependencies. Dobijeno: {sorted(names)}"
    )
    assert "psycopg" in names, (
        f"`psycopg` nedostaje u dependencies. Dobijeno: {sorted(names)}"
    )
    # Django version constraint provera - mora biti >= 5.2
    django_spec = next((d for d in deps if d.strip().lower().startswith("django")), "")
    assert ">=5.2" in django_spec.replace(" ", "") or ">=5" in django_spec.replace(
        " ", ""
    ), f"Django constraint nije >=5.2 (spec: {django_spec!r})"
    # psycopg mora biti pinovan sa [binary] extras (interface contract sec 2.1 row 2)
    psycopg_spec = next(
        (d for d in deps if d.strip().lower().startswith("psycopg")), ""
    )
    assert "[binary]" in psycopg_spec.replace(" ", "").lower(), (
        f"psycopg mora imati [binary] extras (spec: {psycopg_spec!r}). "
        f"Pokreni: uv add 'psycopg[binary]'"
    )


# AC-2: HTMX/template/bootstrap deps prisutni
def test_ac2_htmx_and_template_deps_in_dependencies():
    """AC2: django-htmx, django-template-partials, django-bootstrap5, django-modeltranslation u deps."""
    pyproject = _load_pyproject()
    deps = pyproject.get("project", {}).get("dependencies", [])
    names = _extract_package_names(deps)
    required = {
        "django-modeltranslation",
        "django-htmx",
        "django-template-partials",
        "django-bootstrap5",
    }
    missing = required - names
    assert not missing, (
        f"Nedostaju HTMX/template/i18n paketi: {sorted(missing)}. "
        f"Pronadjeno: {sorted(names)}"
    )


# AC-2: Image/security/email deps prisutni
def test_ac2_image_security_email_deps_in_dependencies():
    """AC2: django-environ, django-anymail, django-ratelimit, django-axes, django-csp,
    sorl-thumbnail, pdf2image, python-magic u deps."""
    pyproject = _load_pyproject()
    deps = pyproject.get("project", {}).get("dependencies", [])
    names = _extract_package_names(deps)
    required = {
        "django-environ",
        "django-anymail",
        "django-ratelimit",
        "django-axes",
        "django-csp",
        "sorl-thumbnail",
        "pdf2image",
        "python-magic",
    }
    missing = required - names
    assert not missing, (
        f"Nedostaju image/security/email paketi: {sorted(missing)}. "
        f"Pronadjeno: {sorted(names)}"
    )


# =============================================================================
# AC3 - Django project skeleton
# =============================================================================


# AC-3 (negative): uv init placeholder fajlovi MORAJU biti obrisani (Task 1.5)
def test_ac3_uv_init_placeholder_files_removed():
    """AC3 / Task 1.5: `uv init` generise main.py ili hello.py placeholder fajlove
    koji NE pripadaju Django strukturi. Moraju biti obrisani pre commit-a.

    Interface contract sec 1.2 explicitno propisuje da ovi ne smeju postojati.
    """
    forbidden = [
        PROJECT_ROOT / "main.py",
        PROJECT_ROOT / "hello.py",
    ]
    present = [str(p.relative_to(PROJECT_ROOT)) for p in forbidden if p.exists()]
    assert not present, (
        f"uv init placeholder fajlovi nisu obrisani: {present}. "
        f"Obrisi ih (Task 1.5) — Django dobija sopstvenu strukturu kroz manage.py."
    )


# AC-3: manage.py i config/ skeleton fajlovi
def test_ac3_django_skeleton_files_exist():
    """AC3: manage.py + config/__init__.py + settings (package ili single file) + urls.py + wsgi.py + asgi.py.

    NAPOMENA: Story 1.2 refactor je `config/settings.py` (single file) zamenio sa
    `config/settings/` paketom. Ovaj test prihvata oba state-a (single file ili paket)
    radi backwards-kompatibilnosti.
    """
    required_files = [
        MANAGE_PY_PATH,
        CONFIG_DIR / "__init__.py",
        CONFIG_DIR / "urls.py",
        CONFIG_DIR / "wsgi.py",
        CONFIG_DIR / "asgi.py",
    ]
    missing = [
        str(p.relative_to(PROJECT_ROOT)) for p in required_files if not p.exists()
    ]
    # Settings: prihvata ili single file (config/settings.py) ili paket (config/settings/)
    settings_single = CONFIG_DIR / "settings.py"
    settings_pkg = CONFIG_DIR / "settings"
    if not (
        settings_single.exists() or (settings_pkg.exists() and settings_pkg.is_dir())
    ):
        missing.append("config/settings.py or config/settings/ (package)")
    assert not missing, (
        f"Django skeleton fajlovi nedostaju: {missing}. "
        f"Pokreni `uv run django-admin startproject config .` (zavrsna tacka KRITICNA)."
    )


# AC-3: manage.py mora imati shebang/main glavnu strukturu
def test_ac3_manage_py_is_executable_django_script():
    """AC3: manage.py sadrzi Django bootstrap kod."""
    assert MANAGE_PY_PATH.exists(), f"manage.py nedostaje na {MANAGE_PY_PATH}"
    content = MANAGE_PY_PATH.read_text(encoding="utf-8")
    # Standardni django-admin startproject manage.py sadrzi "django.core.management"
    assert "django.core.management" in content, (
        "manage.py ne sadrzi Django bootstrap. "
        "Mozda je rucno editovan ili kreiran pogresnom komandom?"
    )
    # I sadrzi referencu na config.settings (DJANGO_SETTINGS_MODULE)
    assert "config.settings" in content, (
        "manage.py ne pokazuje na 'config.settings' DJANGO_SETTINGS_MODULE. "
        "Verovatno startproject je startovan sa pogresnim imenom."
    )


# AC-3: `uv run python manage.py check` mora vratiti 0 issues
def test_ac3_manage_py_check_passes():
    """AC3: `uv run python manage.py check` exits 0 sa output 'no issues' / '0 silenced'.

    NAPOMENA: Story 1.2 uvodi fail-fast za DJANGO_SECRET_KEY (Gotcha #3). Test sada
    eksplicitno setuje DJANGO_SECRET_KEY env var za poziv `manage.py check`.
    """
    import os

    uv_bin = shutil.which("uv")
    if uv_bin is None:
        pytest.fail("uv binary nije u PATH-u. Instaliraj uv >= 0.5 prvo.")
    if not MANAGE_PY_PATH.exists():
        pytest.fail("manage.py nedostaje - Django skeleton nije kreiran.")
    env = os.environ.copy()
    env["DJANGO_SECRET_KEY"] = "test-secret-key-for-bootstrap-smoke-not-a-real-secret"
    result = subprocess.run(
        [uv_bin, "run", "python", "manage.py", "check"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        shell=False,
        timeout=120,
        env=env,
    )
    assert result.returncode == 0, (
        f"`manage.py check` exit code {result.returncode}.\n"
        f"stdout: {result.stdout}\n"
        f"stderr: {result.stderr}"
    )
    output = (result.stdout + result.stderr).lower()
    assert "no issues" in output or "0 silenced" in output, (
        f"`manage.py check` output ne sadrzi expected string.\n"
        f"stdout: {result.stdout}\n"
        f"stderr: {result.stderr}"
    )


# =============================================================================
# AC4 - Dev dependency grupa (PEP 735)
# =============================================================================


# AC-4: [dependency-groups].dev sadrzi svih 7 dev paketa
def test_ac4_dev_dependency_group_contains_all_seven():
    """AC4: [dependency-groups] tabela (PEP 735) sa 'dev' kljucem i svih 7 paketa."""
    pyproject = _load_pyproject()
    dep_groups = pyproject.get("dependency-groups", {})
    assert dep_groups, (
        "[dependency-groups] tabela nedostaje u pyproject.toml. "
        "Mora biti PEP 735 format (NE legacy [tool.uv.dev-dependencies])."
    )
    dev_deps = dep_groups.get("dev", [])
    assert isinstance(dev_deps, list), "[dependency-groups].dev mora biti lista."
    names = _extract_package_names(dev_deps)
    required = set(DEV_DEPENDENCIES)
    missing = required - names
    assert not missing, (
        f"Dev grupa nedostaje pakete: {sorted(missing)}. Pronadjeno: {sorted(names)}"
    )


# AC-4: glavni [project].dependencies NE sme sadrzati dev pakete (separation)
def test_ac4_main_dependencies_do_not_contain_dev_packages():
    """AC4: dev paketi (pytest, ruff, ...) ne smeju biti u glavnoj `dependencies` listi."""
    pyproject = _load_pyproject()
    main_deps = pyproject.get("project", {}).get("dependencies", [])
    main_names = _extract_package_names(main_deps)
    dev_set = set(DEV_DEPENDENCIES)
    leaked = main_names & dev_set
    assert not leaked, (
        f"Dev paketi su procurili u glavnu dependencies listu: {sorted(leaked)}. "
        f"Mora biti razdvojeno - dev paketi idu u [dependency-groups].dev."
    )


# AC-4: legacy [tool.uv.dev-dependencies] format MORA biti odsutan (PEP 735 only)
def test_ac4_no_legacy_uv_dev_dependencies_table():
    """AC4: pyproject.toml NE sme imati [tool.uv.dev-dependencies] (legacy uv pre-0.5).
    Story zahteva PEP 735 [dependency-groups] format."""
    pyproject = _load_pyproject()
    tool_uv = pyproject.get("tool", {}).get("uv", {})
    legacy_dev_deps = tool_uv.get("dev-dependencies")
    assert legacy_dev_deps is None, (
        f"Pronadjen legacy [tool.uv.dev-dependencies] format: {legacy_dev_deps}. "
        f"Story 1.1 zahteva PEP 735 [dependency-groups] format (uv >= 0.5). "
        f"Ukloni [tool.uv.dev-dependencies] iz pyproject.toml."
    )


# =============================================================================
# AC5 - justfile sa task runner receptima
# =============================================================================


# AC-5: justfile mora postojati
def test_ac5_justfile_exists():
    """AC5: justfile mora postojati u root-u."""
    assert JUSTFILE_PATH.exists(), (
        f"justfile nedostaje na {JUSTFILE_PATH}. "
        f"Vidi Dev Notes paragraf 'justfile Template' u story spec-u."
    )


# AC-5: justfile mora sadrzati 5 obaveznih recepata
def test_ac5_justfile_contains_required_recipes():
    """AC5: justfile sadrzi recepte dev/test/lint/migrate/messages."""
    assert JUSTFILE_PATH.exists(), "justfile nedostaje (videti prethodni test)."
    content = JUSTFILE_PATH.read_text(encoding="utf-8")
    required_recipes = ["dev", "test", "lint", "migrate", "messages"]
    # Recept definicija = line koja pocinje sa "<naziv>:" (no indent)
    # Just dozvoljava i "<naziv> arg:" sintaksu, ali za nas su sve bez argumenata.
    missing = []
    for recipe in required_recipes:
        # Match line koji pocinje sa "<recipe>:" ili "<recipe> " (sa argumentima)
        pattern = rf"^{re.escape(recipe)}\s*(?:[a-zA-Z_].*)?:"
        if not re.search(pattern, content, re.MULTILINE):
            missing.append(recipe)
    assert not missing, (
        f"justfile recepti nedostaju: {missing}. Pronadjeni sadrzaj:\n{content[:500]}"
    )


# =============================================================================
# AC6 - Repo hygiene fajlovi
# =============================================================================


# AC-6: .gitignore zadrzava BMad baseline carve-out pravila
def test_ac6_gitignore_preserves_bmad_baseline_rules():
    """AC6: .gitignore mora i dalje sadrzati BMad installer carve-out pravila + design assets exclude."""
    assert GITIGNORE_PATH.exists(), f".gitignore nedostaje na {GITIGNORE_PATH}"
    content = GITIGNORE_PATH.read_text(encoding="utf-8")
    missing = [p for p in BMAD_GITIGNORE_PATTERNS if p not in content]
    assert not missing, (
        f".gitignore je izgubio BMad baseline pravila: {missing}. "
        f"`uv init` je verovatno overwrite-ovao fajl. "
        f"Recovery: `git checkout .gitignore` ili merge iz .gitignore.bmad-baseline."
    )


# AC-6: .gitignore dodatno sadrzi Python/Django/uv pattern-e
def test_ac6_gitignore_contains_python_django_patterns():
    """AC6: .gitignore sadrzi standardne Python/Django/uv ignore pattern-e."""
    assert GITIGNORE_PATH.exists(), f".gitignore nedostaje na {GITIGNORE_PATH}"
    content = GITIGNORE_PATH.read_text(encoding="utf-8")
    required_patterns = [
        "__pycache__/",
        ".venv/",
        ".env",
    ]
    missing = [p for p in required_patterns if p not in content]
    assert not missing, (
        f".gitignore nedostaje osnovne Python/Django pattern-e: {missing}."
    )


# AC-6: .python-version NE sme biti gitignored (story zahteva committable artifact)
def test_ac6_python_version_not_gitignored():
    """AC1+AC6: .python-version je committable artifact (pin runtime za reproducibility).

    Postojeci BMad baseline .gitignore je IGNORISAO .python-version (legacy/pogresno —
    pre nego sto je projekat usvojio uv kao paket menadzer). Story 1.1 sad zahteva
    da .python-version BUDE komitovan.

    Ako pronadjes `.python-version` u .gitignore-u — ukloni ga (ne ceo blok, samo tu liniju).
    """
    assert GITIGNORE_PATH.exists(), f".gitignore nedostaje na {GITIGNORE_PATH}"
    content = GITIGNORE_PATH.read_text(encoding="utf-8")
    # Bare pattern match: linije koje su tacno ".python-version" (bez komentara, bez negacije)
    bad_lines = []
    for raw in content.splitlines():
        line = raw.strip()
        # Preskoci prazne linije i komentare
        if not line or line.startswith("#"):
            continue
        # Preskoci negacije (whitelist) - to NIJE problem
        if line.startswith("!"):
            continue
        if line == ".python-version" or line == "/.python-version":
            bad_lines.append(raw)
    assert not bad_lines, (
        f".python-version je gitignored — sledece linije ga ignorisu: {bad_lines}. "
        f"Story 1.1 (AC1+AC6) zahteva da bude komitovan. "
        f"Ukloni te linije iz .gitignore-a."
    )


# AC-6: README.md postoji sa Quickstart sekcijom
def test_ac6_readme_exists_with_quickstart():
    """AC6: README.md mora postojati i sadrzati Quickstart komande (`uv sync`, `manage.py runserver`)."""
    assert README_PATH.exists(), (
        f"README.md nedostaje na {README_PATH}. "
        f"Vidi Dev Notes 'README.md Template' za sadrzaj."
    )
    content = README_PATH.read_text(encoding="utf-8")
    # Mora imati Quickstart sekciju (case-insensitive) i kljucne komande
    content_lower = content.lower()
    assert "quickstart" in content_lower, "README.md ne sadrzi 'Quickstart' sekciju."
    assert "uv sync" in content_lower, (
        "README.md Quickstart ne sadrzi `uv sync` komandu."
    )
    assert "runserver" in content_lower, (
        "README.md Quickstart ne sadrzi `manage.py runserver` komandu."
    )


# =============================================================================
# AC3 regression - INSTALLED_APPS preserved as startproject default
# =============================================================================


def test_ac3_installed_apps_is_default_django():
    """AC3/Gotcha #8: INSTALLED_APPS sadrzi Django default-e + apps.core + 3rd-party
    app-ove dodate kroz prethodne story-je.

    NAPOMENA: Story 1.2 refactor je `config.settings` (modul) zamenio sa
    `config.settings` (paket); base settings su sada u `config.settings.base`.
    NAPOMENA: Story 1.4 NAMERNO dodaje `apps.core` kao prvi domain app — invariant
    iz Story 1.1 superseded (isti pattern kao Story 1.2 settings split i Story 1.3
    compose dodatak).
    NAPOMENA: Story 1.6 NAMERNO dodaje `django_htmx` i `django_bootstrap5` (template
    tag discovery + HtmxMiddleware) — invariant iz Story 1.4 superseded (isti pattern
    kao Story 1.4 amendment).
    """
    import importlib
    import os

    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    os.environ.setdefault("DJANGO_SECRET_KEY", "test-secret-key-for-bootstrap-not-real")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
    # Ako je settings vec import-ovan iz prethodnog testa, reload da dohvatimo svezi state
    if "config.settings.base" in sys.modules:
        settings = importlib.reload(sys.modules["config.settings.base"])
    else:
        settings = importlib.import_module("config.settings.base")
    apps = list(settings.INSTALLED_APPS)

    expected = {
        "django.contrib.admin",
        "django.contrib.auth",
        "django.contrib.contenttypes",
        "django.contrib.sessions",
        "django.contrib.messages",
        "django.contrib.staticfiles",
        "django_htmx",  # Story 1.6
        "django_bootstrap5",  # Story 1.6
        "apps.core",
    }
    actual = set(apps)

    # MUST be Django defaults + 3rd-party (Story 1.6) + apps.core (Story 1.4)
    assert actual == expected, (
        f"INSTALLED_APPS mora biti Django default + django_htmx + django_bootstrap5 + apps.core "
        f"posle Story 1.6. Extras: {actual - expected}. Missing: {expected - actual}"
    )


# =============================================================================
# Scope hygiene - out-of-scope artifacts must not exist yet
# =============================================================================


def test_no_out_of_scope_artifacts_yet():
    """Story 1.1 ne kreira: static/, .pre-commit-config.yaml, .github/.

    NAPOMENA: Story 1.2 NAMERNO uvodi `.env.example` (AC4) i `config/settings/`
    paket (AC1). Ti artefakti su uklonjeni iz forbidden liste kao legitimna
    Story 1.2 refactor side-effect.

    NAPOMENA: Story 1.3 NAMERNO uvodi: `compose/` (AC1), `compose/django/Dockerfile` (AC2),
    `.env` (Task 10.1, gitignored lokalno). Story 1.1 scope-creep guard azuriran po
    Story 1.2 presedanu.

    NAPOMENA: Story 1.4 NAMERNO uvodi `apps/` (AC1) i `templates/` (AC6). Skinuti
    iz forbidden liste — isti pattern kao Story 1.2 i Story 1.3 amendments.

    NAPOMENA: Story 1.5 NAMERNO uvodi `static/` (AC1 — static/, static/css/,
    static/fonts/roboto/). Skinuti iz forbidden liste — isti pattern kao
    Story 1.2/1.3/1.4 amendments.

    NAPOMENA: Story 1.9 NAMERNO uvodi `.pre-commit-config.yaml` (AC6) i
    `.github/workflows/ci.yml` (AC1). Skinuti iz forbidden liste — isti pattern
    kao Story 1.2/1.3/1.4/1.5 amendments. Story 1.9 je infra-only cross-cutting
    story koja zatvara Epic 1 i postavlja CI gate.
    """
    forbidden: list[str] = []
    existing = []
    for path in forbidden:
        if (PROJECT_ROOT / path).exists():
            existing.append(path)

    assert not existing, f"Out-of-scope artefakti postoje: {existing}"
