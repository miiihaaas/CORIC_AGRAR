"""Story 2.3 — apps/media_pipeline/apps.py MediaPipelineConfig smoke test (RED phase).

Pokriva AC1 / Gotcha MP-1 — `MediaPipelineConfig.name` MORA biti "apps.media_pipeline"
(sa `apps.` prefiksom; matches INSTALLED_APPS entry per project-context.md).

Regression guard (mirror 2.1 BR-1 / 2.2 PR-1 pattern, ali STRONGER assertion):
- Koristi `apps.get_app_config()` umesto direktnog `MediaPipelineConfig.name == "..."`.
- Django app registry resolve testira label kako treba — uhvati i `LookupError` slučaj
  ako label nije konzistentan sa INSTALLED_APPS entry-jem.

TEA RED phase: test MORA pasti dok Dev ne kreira apps/media_pipeline/apps.py + registruje
u INSTALLED_APPS.

Pokrenuti kroz Docker (libmagic SEGFAULT na Windows host-u):
    docker compose -f compose/local.yml run --rm django uv run pytest apps/media_pipeline/tests/test_apps.py -v
"""

from __future__ import annotations


def test_media_pipeline_config_name_has_apps_prefix():
    """MediaPipelineConfig.name mora biti 'apps.media_pipeline' (Gotcha MP-1 regression guard).

    STRONGER assertion: koristi `apps.get_app_config("media_pipeline")` umesto direktnog
    `MediaPipelineConfig.name` — testira da Django app registry resolve-uje label kako treba.
    Bez `apps.` prefiksa, INSTALLED_APPS resolve fail-uje sa LookupError pri prvom model
    reference-u (npr. kroz sorl-thumbnail KVStore migraciju).
    """
    from django.apps import apps

    config = apps.get_app_config("media_pipeline")
    assert config.name == "apps.media_pipeline", (
        f"MediaPipelineConfig.name mora biti 'apps.media_pipeline' (sa apps. prefiksom), "
        f"dobio: {config.name!r}. Vidi Gotcha MP-1."
    )


def test_media_pipeline_config_default_auto_field_is_bigautofield():
    """MediaPipelineConfig.default_auto_field mora biti BigAutoField (AC1)."""
    from django.apps import apps

    config = apps.get_app_config("media_pipeline")
    assert config.default_auto_field == "django.db.models.BigAutoField", (
        f"MediaPipelineConfig.default_auto_field mora biti BigAutoField, "
        f"dobio: {config.default_auto_field!r}"
    )
