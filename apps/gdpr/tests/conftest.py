"""Story 7.1 — TEA RED phase conftest za apps/gdpr/ test suite.

PRVA story Epic 7 (GDPR & Privacy). CONTENT FOUNDATION: NOVI app apps/gdpr/ sa
JEDNIM SINGLETON modelom (`CookiePolicy`) — translatable title/body (`_sr/_hu/_en`),
pravni effective_date, singleton-friendly TranslationAdmin, javna strana
`/sr/politika-kolacica/`, i Lorem Ipsum data-seed (0002) pre prvog deploy-a.

RED phase: apps.gdpr NE postoji (NIJE u INSTALLED_APPS, NEMA models/admin/views/urls/
migrations) → svaki test koji importuje `apps.gdpr.*` MORA pasti čisto.

⚠️ COLLECTION-SAFETY: apps.gdpr NEMA module-level import nijednog test modula —
importi su UNUTAR test funkcija/fixtura. Tako missing apps.gdpr daje per-test FAIL
(RED), NE collection-abort koji bi oborio CELU suite.

Superuser kroz `django_user_model` (NIKAD direktan User import — project-context.md).

Refs:
- 7-1-cookiepolicy-model-admin.md AC1-AC8 + SM-D1..D10 + Gotcha G-1..G-12
- 7-1-interface-contract.md (TEA canonical contract — Dev MORA satisfy)
- apps/pages/tests/conftest.py + apps/seo/tests/conftest.py (style precedent)
"""

from __future__ import annotations

import pytest

# Public URL pod i18n_patterns (slug ASCII — Gotcha G-6).
COOKIE_POLICY_PATH_SR = "/sr/politika-kolacica/"
COOKIE_POLICY_PATH_HU = "/hu/politika-kolacica/"
COOKIE_POLICY_PATH_EN = "/en/politika-kolacica/"


@pytest.fixture
def superuser(django_user_model):
    """Superuser za admin changelist/change-view smoke (AC6).

    `django_user_model` = settings.AUTH_USER_MODEL kroz get_user_model() —
    NIKAD direktan `from django.contrib.auth.models import User`.
    """
    return django_user_model.objects.create_superuser(
        username="gdpr_admin_tea",
        email="gdpr-admin@example.com",
        password="tea-pass-12345",
    )
