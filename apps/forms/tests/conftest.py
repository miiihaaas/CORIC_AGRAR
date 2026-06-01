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
