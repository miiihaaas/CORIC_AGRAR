"""Story 9-7 — pytest fixtures lokalni za apps/core/tests.

``seed_sample_data`` production guard (SM-D2) odbija izvršavanje sa ``DEBUG=False`` bez
``--force``. pytest-django prinudno postavlja ``settings.DEBUG=False`` tokom testova (vidi
config/settings/development.py komentar), pa bi guard blokirao i default-path testove koji
NE prosleđuju ``--force``.

Globalni ``django_debug_mode = "keep"`` u pyproject.toml bi rešio to, ALI bi DEBUG=True
procurio u CEO suite i polomio testove koji zavise od produkcijskog 404/500 ponašanja (npr.
``apps/blog/tests/test_blog_urls.py::test_draft_and_nonexistent_slug_both_404_no_oracle`` —
Django technical-404 echo-uje requested path kad je DEBUG=True → existence-oracle leak).

Zato fix SKOPIRAMO samo na ``test_seed_sample_data`` modul: autouse fixture postavlja ambient
``DEBUG=True`` za te testove. Testovi koji eksplicitno traže ``@override_settings(DEBUG=False)``
i dalje lokalno forsiraju False unutar svog scope-a (override_settings ima prednost nad ovim
fixture-om jer se primenjuje bliže testu), pa guard-block putanja ostaje testabilna.
"""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _seed_sample_data_debug_true(request, settings):
    """Za test_seed_sample_data modul: ambient DEBUG=True (mirror dev-a, ne pytest False).

    @override_settings(DEBUG=False) na pojedinačnim testovima i dalje forsira False lokalno.
    """
    if request.module.__name__.endswith("test_seed_sample_data"):
        settings.DEBUG = True
