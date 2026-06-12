"""Staging settings — production-like, deployed to staging.coricagrar.example (Hetzner CX22)."""

from .base import *  # noqa: F401, F403
from .base import (
    env,
)  # eksplicitno za GlitchTip init blok niže (izbegava F405 star-import warning)

DEBUG = False

# ALLOWED_HOSTS inherited from base (env-driven). Override only ako treba dodatne hosts.

# Security — staging mora biti production-like za realan test
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
LANGUAGE_COOKIE_SECURE = True  # defense-in-depth (Story 1.4 / Dev-B SEC review)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Bez HSTS na staging-u (HSTS pin-uje host na HTTPS — ne želiš to na staging domenu)

# ── Email backend override (Story 4.1) ──────────────────────────────────────
# Eksplicitan assignment POSLE `from .base import *` override-uje base consolemail
# default (EMAIL_CONFIG/vars().update). anymail Resend (ANYMAIL dict u base; SM-D6).
EMAIL_BACKEND = "anymail.backends.resend.EmailBackend"

# ── Static files storage override za staging ─────────────────────────────────
# Staging je production-like — manifest se koristi za realan test cache-busting-a.
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
    },
}

# ── Error tracking — GlitchTip / Sentry SDK (Story 9.3) ──────────────────────
# Identičan guarded init kao production.py (SM-D5), RAZLIKA samo environment="staging"
# (G-4 — razdvaja staging event-e od prod-a u GlitchTip UI). Empty-DSN → no-op.
import sentry_sdk  # noqa: E402

GLITCHTIP_DSN = env("GLITCHTIP_DSN", default="")
if GLITCHTIP_DSN:
    sentry_sdk.init(
        dsn=GLITCHTIP_DSN,
        traces_sample_rate=env.float("SENTRY_TRACES_SAMPLE_RATE", default=0.0),
        send_default_pii=False,  # GDPR (Epic 7) — NIKAD PII
        environment="staging",
        release=env("IMAGE_TAG", default="") or None,
    )
