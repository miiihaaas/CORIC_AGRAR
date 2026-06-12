"""Story 9.8 — Playwright E2E conftest (fixtures = GREEN contract).

Ovo je RED faza: fixtures definišu KONTRAKT koji Dev mora ispuniti. Neke reference
(management command `seed_e2e_data`, dev superuser env vars) NAMERNO ne postoje još —
to je ono što čini suite RED dok Dev ne instrumentuje app.

E2E se vozi protiv POKRENUTE app (Docker `compose/local.yml` ili CI self-contained
Postgres+Django) — Playwright kuca HTTP protiv `E2E_BASE_URL`. Data-setup fixtures
NE diraju test DB kroz pytest-django (E2E nije unit) — one pozivaju app-ov ORM kroz
management command (server-side), pa MORAJU da se izvrše u istom procesu kao app
(CI step) ILI kroz `manage.py` subprocess. Ovaj conftest dokumentuje OBE opcije i
default-uje na management-command kontrakt.

Fixtures:
- `base_url`            — env E2E_BASE_URL (default http://localhost:8000).
- `e2e_data`            — garancija seed_sample_data + AC12 listing-visibility setup
                          (traktori Subcategory + 3 traktora + ≥1 ProductImage za TB804).
                          GREEN: Dev pravi `manage.py seed_e2e_data` (ili ORM helper).
- `dev_superuser`       — env-driven createsuperuser (NIKAD hardkodovan password) +
                          MANDATORY django-axes flush (AC1d / Task 2.4).
- `sample_image_path`   — putanja do tests/e2e/assets/sample.png (file upload fixtura).
- `mobile_context_args` / browser_context_args override — mobile viewport za UJ-2.

Marker: svaki spec nosi `pytestmark = pytest.mark.e2e` (AC13). `e2e` marker se
registruje u pyproject.toml `[tool.pytest.ini_options].markers` (Dev — Task 1.3).
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

# Asset folder (file-upload fixture za UJ-2 + AC12 ProductImage).
ASSETS_DIR = Path(__file__).parent / "assets"
SAMPLE_IMAGE = ASSETS_DIR / "sample.png"

# Repo root (manage.py lokacija) — za subprocess management-command kontrakt.
REPO_ROOT = Path(__file__).resolve().parents[2]

# Fiksan deterministički slug koji UJ-3 happy-path admin test kreira (I-3 idempotentnost).
E2E_PRODUCT_SLUG = "e2e-test-produkt"
E2E_PRODUCT_NAME = "E2E Test Produkt"

# ZASEBAN fiksan slug za UJ-3 publish-gate edge test (AC4b). MORA biti različit od
# E2E_PRODUCT_SLUG jer Product.slug je unique=True — happy-path test kreira
# `e2e-test-produkt` (published), pa bi edge test sa ISTIM slug-om pao na unique-slug
# koliziju PRE nego što publish-gate u save_related-u fire-uje (test-izolacija, I-3).
# GREEN conftest/`seed_e2e_data` mora obrisati/guard-ovati OBA slug-a PRE UJ-3 testova.
E2E_PRODUCT_SLUG_GATE = "e2e-test-produkt-gate"
E2E_PRODUCT_NAME_GATE = "E2E Test Produkt Gate"


# =============================================================================
# base_url (AC1a)
# =============================================================================
@pytest.fixture(scope="session")
def base_url() -> str:
    """E2E_BASE_URL (default http://localhost:8000). Sve page.goto su relativne na ovo."""
    return os.environ.get("E2E_BASE_URL", "http://localhost:8000").rstrip("/")


# =============================================================================
# Management-command kontrakt helper
# =============================================================================
def _run_manage(*args: str) -> subprocess.CompletedProcess:
    """Pozovi `python manage.py <args>` u repo root-u.

    GREEN kontrakt: koristi se za seed + AC12 remedijaciju + superuser provisioning.
    U CI self-contained job-u app i E2E dele isti checkout → manage.py je dostupan.
    Kada E2E gađa REMOTE staging URL, data-setup se radi kao ZASEBAN CI step na boxu,
    a ovaj subprocess se preskače (vidi `_E2E_SKIP_DATA_SETUP`).
    """
    return subprocess.run(
        [sys.executable, "manage.py", *args],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=True,
    )


_SKIP_DATA_SETUP = os.environ.get("E2E_SKIP_DATA_SETUP", "").lower() in {"1", "true", "yes"}


# =============================================================================
# e2e_data — seed + AC12 listing-visibility + galerija (AC1b / AC12)
# =============================================================================
@pytest.fixture(scope="session")
def e2e_data():
    """Garantuje seed_sample_data + AC12 listing-visibility setup PRE E2E run-a.

    AC12 (KRITIČNO — UJ-1 je bez ovoga strukturno nemoguć):
      (a) `traktori` Subcategory pod Category slug="traktori" (is_for="traktori"),
          dodeljena trima traktorima (agri-tracking-tb804, wuzheng-wz504,
          saillong-sl904) → postaju vidljivi u TractorListView (NULL-JOIN fix);
      (b) ≥1 ProductImage za agri-tracking-tb804 (dev asset iz tests/e2e/assets/)
          → galerija/Lightbox se renderuje (`{% if product.images.all %}`).

    GREEN KONTRAKT (Dev bira jedno):
      OPCIJA A (preporučeno): novi idempotentni management command
        `manage.py seed_e2e_data` koji (1) zove seed_sample_data, (2) radi AC12
        get_or_create Subcategory + assign + ProductImage, (3) DEV-only guard
        (DEBUG ili --force, mirror seed_sample_data SM-D2). Tada ovaj fixture samo:
            _run_manage("seed_e2e_data", "--force")
      OPCIJA B: ovaj fixture poziva seed_sample_data, pa AC12 ORM helper kroz
        `manage.py shell -c "<helper>"` ili dedikovan command.

    RED: `seed_e2e_data` NE postoji još → CalledProcessError (smislen RED signal:
    „Unknown command: 'seed_e2e_data'"). Ovo je očekivano dok Dev ne napravi command.

    Idempotentno: get_or_create po slug / (product, order) → re-run ne duplira.
    """
    if _SKIP_DATA_SETUP:
        # Remote-staging mod: data-setup je odrađen kao zaseban CI step na boxu.
        yield
        return

    # GREEN: zameni jednom linijom kad command postoji. RED: ovo baca CalledProcessError.
    _run_manage("seed_e2e_data", "--force")
    yield


# =============================================================================
# dev_superuser — env-driven createsuperuser + MANDATORY axes flush (AC1c/AC1d/AC11)
# =============================================================================
@pytest.fixture(scope="session")
def dev_superuser(e2e_data):
    """Provizionira DEV-only superusera iz env-a (NIKAD hardkodovan password — AC11).

    Env (CI secrets / .env): DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_EMAIL,
    DJANGO_SUPERUSER_PASSWORD. Fail-loud ako PASSWORD nije postavljen (NE izmišljaj default).

    MANDATORY axes-flush (AC1d / Task 2.4): PRE login fixture-a, conftest MORA očistiti
    django-axes stanje (AccessAttempt.objects.all().delete() + cache flush) da Epic 8-1
    lockout iz prethodnih/paralelnih run-ova NE flap-uje admin login. GREEN KONTRAKT:
    Dev pravi `manage.py axes_reset` poziv ILI dedikovani `seed_e2e_data --reset-axes`.
    `django-axes` isporučuje `axes_reset` management command out-of-the-box.

    Vraća dict {username, password} za AdminProductPage.login().

    RED: ako env vars nisu postavljene → pytest.fail (jasna poruka). createsuperuser
    --noinput sa već-postojećim username-om je idempotentan kroz get_or_create kontrakt
    (Dev: koristi `--skip-checks` + tolerate „already exists", ili custom command).
    """
    username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "e2e_admin")
    email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "e2e_admin@example.com")
    password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")
    if not password:
        pytest.fail(
            "DJANGO_SUPERUSER_PASSWORD nije postavljen u env-u — E2E admin (UJ-3) "
            "zahteva env-driven kredencijale (AC11; NIKAD hardkodovan password). "
            "Postavi DJANGO_SUPERUSER_PASSWORD u CI secrets / .env pre E2E run-a.",
            pytrace=False,
        )

    if not _SKIP_DATA_SETUP:
        # 1) MANDATORY axes-flush PRE login-a (AC1d) — django-axes built-in command.
        _run_manage("axes_reset")
        # 2) Idempotentno provisioning superusera. createsuperuser --noinput čita
        #    DJANGO_SUPERUSER_* iz env-a; postavi ih eksplicitno za subprocess.
        env_overlay = {
            **os.environ,
            "DJANGO_SUPERUSER_USERNAME": username,
            "DJANGO_SUPERUSER_EMAIL": email,
            "DJANGO_SUPERUSER_PASSWORD": password,
        }
        subprocess.run(
            [sys.executable, "manage.py", "createsuperuser", "--noinput"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            env=env_overlay,
            # NE check=True: već-postojeći user vraća non-zero; idempotentno toleriraj.
            check=False,
        )

    return {"username": username, "email": email, "password": password}


# =============================================================================
# Upload asset fixtura
# =============================================================================
@pytest.fixture(scope="session")
def sample_image_path() -> Path:
    """Putanja do malog validnog PNG-a za file-upload (UJ-2 + AC12).

    RED-safe: fajl je commit-ovan u repo (tests/e2e/assets/sample.png). Ako Dev hoće
    realniji JPG ~10KB, može ga zameniti — testovi referenciraju ovu fixturu, ne ime.
    """
    assert SAMPLE_IMAGE.exists(), (
        f"Nedostaje E2E test asset: {SAMPLE_IMAGE}. Dodaj mali validan PNG/JPG."
    )
    return SAMPLE_IMAGE


# =============================================================================
# Mobile viewport (UJ-2 — AC3)
# =============================================================================
@pytest.fixture
def mobile_context_args() -> dict:
    """Mobile context kwargs (<768px) za UJ-2 — koristi se da napravi novi mobilni context."""
    return {
        "viewport": {"width": 390, "height": 844},  # iPhone 12 logical px (<768)
        "is_mobile": True,
        "has_touch": True,
    }


@pytest.fixture
def mobile_page(browser, mobile_context_args):
    """Mobilna `page` (zaseban context sa <768px viewport-om) — UJ-2.

    Ne preklapa default `page` fixturu (desktop) — UJ-1/UJ-3 koriste standardni `page`.
    """
    context = browser.new_context(**mobile_context_args)
    page = context.new_page()
    yield page
    context.close()
