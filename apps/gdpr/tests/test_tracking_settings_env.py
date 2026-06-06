"""Story 7.3 — AC4: env-driven GA/FB ID settings (TEA RED phase, light).

Pokriva AC4 + SM-D5/D6:
- `GA_MEASUREMENT_ID = env("GA_MEASUREMENT_ID", default="")` i
  `FB_PIXEL_ID = env("FB_PIXEL_ID", default="")` POSTOJE kao settings.
- Prazan default u dev/test → `settings.GA_MEASUREMENT_ID == ""` (no-tracker fail-safe;
  tagovi render NISTA, testovi NE pogadjaju realne trackere).
- ID-jevi su settings (env), NE SiteSettings model polja.

RED razlog: settings JOS NEMAJU GA_MEASUREMENT_ID/FB_PIXEL_ID → AttributeError.

Pokrenuti:
    docker compose -f compose/local.yml run --rm django \
        uv run pytest apps/gdpr/tests/test_tracking_settings_env.py -v

Refs: 7-3 AC4 + SM-D5/D6; config/settings/base.py:120-127 (ANYMAIL env pattern).
"""

from __future__ import annotations

from django.conf import settings

# DB nije potreban — cisto settings introspection.


# AC4: GA_MEASUREMENT_ID postoji kao setting + prazan default u test env
def test_ga_measurement_id_setting_exists_empty_default():
    assert hasattr(settings, "GA_MEASUREMENT_ID"), (
        "settings MORA imati `GA_MEASUREMENT_ID = env(\"GA_MEASUREMENT_ID\", default=\"\")` "
        "(AC4/SM-D5/D6)."
    )
    assert settings.GA_MEASUREMENT_ID == "", (
        "U dev/test env GA_MEASUREMENT_ID MORA biti prazan default (\"\") → no-tracker "
        f"fail-safe. Dobio: {settings.GA_MEASUREMENT_ID!r}"
    )


# AC4: FB_PIXEL_ID postoji kao setting + prazan default u test env
def test_fb_pixel_id_setting_exists_empty_default():
    assert hasattr(settings, "FB_PIXEL_ID"), (
        "settings MORA imati `FB_PIXEL_ID = env(\"FB_PIXEL_ID\", default=\"\")` "
        "(AC4/SM-D5/D6)."
    )
    assert settings.FB_PIXEL_ID == "", (
        "U dev/test env FB_PIXEL_ID MORA biti prazan default (\"\"). "
        f"Dobio: {settings.FB_PIXEL_ID!r}"
    )


# AC1/G-9: consent_state context_processor registrovan u TEMPLATES (POSLE blog-a)
def test_consent_state_context_processor_registered():
    processors = settings.TEMPLATES[0]["OPTIONS"]["context_processors"]
    assert "apps.gdpr.context_processors.consent_state" in processors, (
        "`apps.gdpr.context_processors.consent_state` MORA biti registrovan u "
        f"TEMPLATES context_processors (AC1/G-1/G-9). Dobio: {processors!r}"
    )
    # G-9: POSLE apps.blog.context_processors.latest_blog_posts (deterministicki redosled).
    blog_cp = "apps.blog.context_processors.latest_blog_posts"
    gdpr_cp = "apps.gdpr.context_processors.consent_state"
    assert blog_cp in processors and processors.index(gdpr_cp) > processors.index(
        blog_cp
    ), (
        "consent_state MORA biti registrovan POSLE latest_blog_posts (G-9; "
        f"deterministicki redosled). Dobio: {processors!r}"
    )
