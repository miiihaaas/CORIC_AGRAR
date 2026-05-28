"""Production settings — deployed to coricagrar.example (Hetzner CX32)."""

from .base import *  # noqa: F401, F403, F405

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

# Story 9.3 doda: import sentry_sdk; sentry_sdk.init(dsn=env("GLITCHTIP_DSN"), ...)
