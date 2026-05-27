# CORIC_AGRAR — justfile (task runner)
# Pokrenuti `just --list` za listu svih recepata.

# Default recept — prikazuje listu kad se pokrene `just` bez argumenata
default:
    @just --list

# Pokrece dev server (bice rewired na docker compose u Story 1.3)
dev:
    uv run python manage.py runserver

# Pokrece test suite
test:
    uv run pytest

# Lint (read-only check, ne menja kod)
lint:
    uv run ruff check .
    uv run djade --check templates/ || echo "djade: templates/ folder ne postoji jos (OK za Story 1.1)"

# Apply DB migrations
migrate:
    uv run python manage.py migrate

# i18n message handling
messages:
    uv run python manage.py makemessages -a
    uv run python manage.py compilemessages
