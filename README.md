# Coric Agrar — Korporativni Sajt

Trojezican (sr/hu/en) Django sajt za poljoprivredni biznis Coric Agrar — katalog brendova/proizvoda, blog "Price sa polja", lead-gen forme i SEO-spreman public-facing site.

## Tech Stack

- Python 3.13 + Django 5.2 LTS
- PostgreSQL + django-modeltranslation
- HTMX + Bootstrap 5 + django-template-partials
- uv (paket menadzer) + just (task runner)

## Quickstart

```bash
# Instaliraj sve dep-ove
uv sync

# Migracije (kad PostgreSQL bude konfigurisan — Story 1.2/1.3)
uv run python manage.py migrate

# Dev server
uv run python manage.py runserver
# ili: just dev
```

## Vise

Dokumentacija u `_bmad-output/planning-artifacts/`.
