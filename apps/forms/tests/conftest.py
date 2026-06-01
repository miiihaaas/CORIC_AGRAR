"""Story 4.1 — TEA RED phase conftest za apps/forms/ test suite.

Email testovi koriste pytest-django `mailoutbox` fixture (auto-postavlja Django
`locmem` backend → `django.core.mail.outbox`). NIKAD pravi network send
(project-context.md:267-271). DB testovi koriste real PostgreSQL test bazu
(`@pytest.mark.django_db`); NEMA `requires_postgres` marker (Lead NEMA FTS,
za razliku od 2-13 search).

Test data inline kroz `Lead.objects.create(...)` — NEMA `factory_boy` (nije dep).

Refs:
- 4-1-lead-model-smtp-setup.md Task 8 + AC1-AC9
- 4-1-interface-contract.md § 1 (tests) + TEA-D1/TEA-D2
"""

from __future__ import annotations

import pytest
from django.core.cache import cache
from django.urls import reverse
from django.utils.translation import activate

_LOCMEM_CACHES = {
    "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
}


@pytest.fixture(autouse=True)
def _pin_and_clear_ratelimit_cache(settings):
    """Pinuje locmem `default` cache (deterministični django-ratelimit backend) i čisti
    brojač PRE i POSLE svakog forms testa.

    KRITIČNO za izolaciju: `htmx_post` koristi FIKSAN default IP (`203.0.113.7`), a
    LocMemCache je process-global → bez ovog clear-a ratelimit brojač za taj IP curi
    KROZ testove (success/error testovi u test_contact_view.py / _aria_live.py /
    _email_failure.py dele isti IP, ukupno >5 POST-ova u istom minutu → spurious 429 u
    GREEN fazi). Autouse na nivou forms conftest-a garantuje svežu 5/m kvotu po testu
    (SM-D10 / Task 3.3). Ratelimit-specifični test dodatno potvrđuje 5-ok/6-ti-429 granicu.
    """
    settings.CACHES = _LOCMEM_CACHES
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def recipient_env(settings):
    """Popunjava per-segment recipient settings tako da rezolucija po form_type ima
    ne-prazan recipient (inače service tretira prazan recipient kao failed send — C1).

    Override-uje TAČNE settings atribute koje `send_lead_email` čita (SM-D7).
    """
    settings.CONTACT_EMAIL_TO = "kontakt@coricagrar.rs"
    settings.SERVICE_EMAIL_TO = "servis@coricagrar.rs"
    settings.PARTS_EMAIL_TO = "delovi@coricagrar.rs"
    settings.DEFAULT_FROM_EMAIL = "no-reply@coricagrar.rs"
    return settings


@pytest.fixture
def superuser(django_user_model):
    """Superuser za admin smoke testove."""
    return django_user_model.objects.create_superuser(
        username="admin_tea",
        email="admin@example.com",
        password="tea-pass-12345",
    )


# ── Story 4.2 (Opšta kontakt forma) — RED phase fixtures ─────────────────────


@pytest.fixture
def valid_contact_payload() -> dict:
    """Validan POST payload za ContactForm (Task 1.1). Puni dijakritik u `name`."""
    return {
        "name": "Marko Marković",
        "email": "marko@example.com",
        "phone": "+381641234567",
        "message": "Zanima me traktor.",
    }


@pytest.fixture
def contact_submit_url() -> str:
    """Reverse `forms:contact_submit` pod aktivnim `sr` (i18n_patterns prefiks /sr/).

    Hoist-ovan iz 4 test fajla (_submit_url duplikacija) — jedinstven izvor URL-a.
    """
    activate("sr")
    return reverse("forms:contact_submit")


@pytest.fixture
def htmx_post(client):
    """Helper: HTMX POST sa `HX-Request` header-om da `request.htmx` bude True.

    Django test client `HTTP_HX_REQUEST="true"` → django_htmx HtmxMiddleware postavlja
    `request.htmx`. REMOTE_ADDR fiksiran (ratelimit key='ip' stabilnost).
    """

    def _post(url: str, data: dict, *, ip: str = "203.0.113.7", **extra):
        return client.post(
            url,
            data,
            HTTP_HX_REQUEST="true",
            REMOTE_ADDR=ip,
            **extra,
        )

    return _post


# ── Story 4.3 (Model Inquiry forma) — RED phase fixtures ─────────────────────


@pytest.fixture
def model_inquiry_payload() -> dict:
    """Validan POST payload za ModelInquiryForm (Task 1.1) BEZ `product_slug`.

    `product_slug` se popunjava per-test iz fixture product-a (`{**model_inquiry_payload,
    "product_slug": product.slug}`) jer slug zavisi od kreiranog Product-a u svakom testu.
    Puni dijakritik u `name`/`message` (project-context anti-šišana-latinica).
    """
    return {
        "name": "Marko Marković",
        "email": "marko@example.com",
        "phone": "+381641234567",
        "message": "Zanima me ovaj model.",
    }


@pytest.fixture
def model_inquiry_submit_url() -> str:
    """Reverse `forms:model_inquiry_submit` pod aktivnim `sr` (i18n_patterns prefiks /sr/)."""
    activate("sr")
    return reverse("forms:model_inquiry_submit")


@pytest.fixture
def published_product(db):
    """Objavljen Product „Agri Tracking TB804" — kanonski model-inquiry fixture.

    Hoist-ovan iz ~25 inline `ProductFactory.create(name="Agri Tracking TB804")` poziva
    kroz 4.3 test fajlove (TEA cleanup). `db` zavisnost jer factory dira DB.
    """
    from apps.products.tests.factories import ProductFactory

    return ProductFactory.create(name="Agri Tracking TB804")
