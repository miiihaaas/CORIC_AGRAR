"""Story 2.13 — AddField search_vector + AddIndex GIN (SM-D8/D20).

PRETHODI joj 0004a (extension migracija) — `dependencies` eksplicitno na 0004a
da extension postoji PRE GIN indeksa (SM-D7). search_vector ostaje UVEK NULL u
v1 (annotation-at-query-time); GIN indeks je forward-compat no-op (SM-D8).

Reverzibilna (AddField/AddIndex imaju automatski reverse). Manually reviewed
(project-context.md § Migrations discipline): IF chain 0003 → 0004a → 0004.
"""

import django.contrib.postgres.indexes
import django.contrib.postgres.search
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0004a_enable_search_extensions"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="search_vector",
            field=django.contrib.postgres.search.SearchVectorField(
                editable=False, null=True, verbose_name="Search vektor"
            ),
        ),
        migrations.AddIndex(
            model_name="product",
            index=django.contrib.postgres.indexes.GinIndex(
                fields=["search_vector"], name="products_search_gin"
            ),
        ),
    ]
