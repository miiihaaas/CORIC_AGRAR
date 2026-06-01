"""Production settings — deployed to coricagrar.example (Hetzner CX32)."""

from .base import *  # noqa: F401, F403
from .base import (
    env,
)  # eksplicitno za env.int() niže (izbegava F405 star-import warning)

# Eksplicitno False (defense-in-depth — base već default-uje na False)
DEBUG = False

# ALLOWED_HOSTS inherited from base (env-driven, MORA biti set u prod env)

# ── HTTPS hardening ──────────────────────────────────────────────────────────
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
LANGUAGE_COOKIE_SECURE = True  # defense-in-depth (Story 1.4 / Dev-B SEC review)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# HSTS (1 year default; override-able preko env)
SECURE_HSTS_SECONDS = env.int("DJANGO_SECURE_HSTS_SECONDS", default=31536000)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Additional headers
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"

# ── Email backend override (Story 4.1) ──────────────────────────────────────
# Eksplicitan assignment POSLE `from .base import *` override-uje base consolemail
# default (EMAIL_CONFIG/vars().update). anymail Resend (ANYMAIL dict u base; SM-D6).
EMAIL_BACKEND = "anymail.backends.resend.EmailBackend"

# ── Static files storage override za prod ────────────────────────────────────
# Prod koristi Whitenoise CompressedManifestStaticFilesStorage:
# - hash u filename (tokens.<hash>.css) → cache-busting + max-age=1y
# - automatski .gz + .br kompresovane varijante
# Zahteva collectstatic --noinput kao deploy step (PRE prvog request-a).
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
    },
}

# ── Bootstrap 5 (production override) ────────────────────────────────────────
# Production: lokalni vendor fajlovi (GDPR + CSP-readiness).
# Story 1.6 Task 4 prepares static/vendor/bootstrap-5.3.3/ for ovaj override.
BOOTSTRAP5 = {
    "css_url": {
        "url": "/static/vendor/bootstrap-5.3.3/css/bootstrap.min.css",
        "integrity": None,
    },
    "javascript_url": {
        "url": "/static/vendor/bootstrap-5.3.3/js/bootstrap.bundle.min.js",
        "integrity": None,
    },
    "javascript_in_head": False,
    "include_jquery": False,
}

# Story 9.3 doda: import sentry_sdk; sentry_sdk.init(dsn=env("GLITCHTIP_DSN"), ...)
