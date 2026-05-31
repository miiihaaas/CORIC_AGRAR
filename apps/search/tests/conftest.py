"""Story 2.13 — TEA RED phase conftest za apps/search/ test suite.

Definiše `requires_postgres` mehanizam (Task 8.0 / IMP-2 / OQ-1) koji **FAILA**
(NE skip-uje) kad test DB backend NIJE PostgreSQL.

⚠️ ZAŠTO HARD FAIL (NE skipif):
PostgreSQL FTS (`SearchVector`/`SearchQuery`/`SearchRank`/`unaccent`/GIN) NE radi na
SQLite. Ako bismo koristili `@pytest.mark.skipif`, 4 od ~7 test fajlova (test_migrations,
test_search_query + FTS delovi test_views/test_templates) bi TIHO prošli na SQLite →
false green. project-context.md § Database tests: „NIKAD mock Django ORM ili PostgreSQL
— koristi real test DB"; projektna test DB JESTE PostgreSQL (Docker compose,
DJANGO_SETTINGS_MODULE=config.settings.development). Marker MORA proći lokalno i u CI;
ako ne prođe, to je infra drift koji MORA da pukne GLASNO.

Korišćenje u test fajlu:
    pytestmark = [pytest.mark.django_db, pytest.mark.requires_postgres]
ili per-test:
    @pytest.mark.requires_postgres

Refs:
- 2-13-global-search-sa-postgresql-fts.md Task 8.0 (IMP-2, BLOKER — NIJE skipif)
- 2-13-interface-contract.md § 10 (PG-DB fix)
"""

from __future__ import annotations

import pytest
from django.db import connection


@pytest.fixture(autouse=True)
def _enforce_postgres(request) -> None:
    """Auto-use fixture koji HARD-FAILA kad je test markiran `requires_postgres`
    a DB backend NIJE PostgreSQL.

    NE koristi `pytest.skip` — skip = tihi false green. `assert` je namerno tvrd:
    loš backend = glasan fail = infra drift signal (Task 8.0 / IMP-2).
    """
    if request.node.get_closest_marker("requires_postgres") is None:
        return
    assert connection.vendor == "postgresql", (
        "FTS testovi zahtevaju PostgreSQL test DB (NE SQLite) — vidi OQ-1/IMP-2. "
        f"connection.vendor == {connection.vendor!r}. Pokreni kroz `just test` "
        "(Docker PostgreSQL), NE direktno na SQLite. Ovo je HARD FAIL namerno "
        "(NE skipif): skip = tihi false green."
    )


def pytest_configure(config) -> None:
    """Registruj `requires_postgres` marker da pytest ne emituje PytestUnknownMarkWarning."""
    config.addinivalue_line(
        "markers",
        "requires_postgres: test zahteva PostgreSQL backend (FTS); HARD-FAILA na SQLite (IMP-2).",
    )
