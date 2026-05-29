"""Staging settings — production-like, deployed to staging.coricagrar.example (Hetzner CX22)."""

from .base import *  # noqa: F401, F403

DEBUG = False

# ALLOWED_HOSTS inherited from base (env-driven). Override only ako treba dodatne hosts.

# Security — staging mora biti production-like za realan test
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
LANGUAGE_COOKIE_SECURE = True  # defense-in-depth (Story 1.4 / Dev-B SEC review)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Bez HSTS na staging-u (HSTS pin-uje host na HTTPS — ne želiš to na staging domenu)

# ── Static files storage override za staging ─────────────────────────────────
# Staging je production-like — manifest se koristi za realan test cache-busting-a.
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
    },
}
