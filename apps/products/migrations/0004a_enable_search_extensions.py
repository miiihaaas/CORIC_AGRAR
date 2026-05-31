"""Story 2.13 — Omogući PostgreSQL extension-e za FTS (SM-D7).

PRETHODI 0004 (AddField search_vector + AddIndex GIN) — GIN indeks na
SearchVectorField i `unaccent()`/`pg_trgm` u upitima zahtevaju da extension
VEĆ postoji. Razdvojeno u zasebnu migraciju radi idempotentnosti + reverzibilnosti
nezavisno od schema promene.

UnaccentExtension/TrigramExtension su Django-native (imaju reverse) i interno
izvršavaju `CREATE EXTENSION IF NOT EXISTS`. Zahtevaju da migration DB rola sme
da kreira extension (lokal + Docker postgres:16-alpine superuser → radi; managed
PG: DBA pre-grant pre migrate-a — vidi IMP-9).
"""

from __future__ import annotations

from django.contrib.postgres.operations import TrigramExtension, UnaccentExtension
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0003_alter_productvariant_description_and_more"),
    ]

    operations = [
        UnaccentExtension(),
        TrigramExtension(),
    ]
