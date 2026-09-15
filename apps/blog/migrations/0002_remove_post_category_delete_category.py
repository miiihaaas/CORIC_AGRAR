"""Uklanjanje blog kategorija (post-launch odluka) — objave se više ne kategorišu.

Brise `Post.category` FK i `Category` model (uklj. modeltranslation `name_*`/
`description_*` kolone koje su bile deo tog modela). NEPOVRATNO na produkciji
nakon deploy-a — svaka postojeca kategorizacija objava se gubi (kategorija
ostaje samo kao istorijski podatak u DB backup-u, ne u aplikaciji)."""

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("blog", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="post",
            name="category",
        ),
        migrations.DeleteModel(
            name="Category",
        ),
    ]
