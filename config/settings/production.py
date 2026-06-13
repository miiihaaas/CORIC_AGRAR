"""Production settings — deployed to coricagrar.example (Hetzner CX32)."""

import copy

from .base import *  # noqa: F401, F403
from .base import (
    LOGGING,
    env,
)  # eksplicitno za env.int() + LOGGING tightening (izbegava F405 star-import warning)

# Eksplicitno False (defense-in-depth — base već default-uje na False)
DEBUG = False

# ALLOWED_HOSTS inherited from base (env-driven, MORA biti set u prod env)

# ── HTTPS hardening ──────────────────────────────────────────────────────────
# Story 9.1 (SM-D7/OQ-3): env-parametrizovan radi lokalnog smoke-a. Default True
# čuva prod hardening; lokalni HTTP/80 smoke override-uje na False (inače 301 loop,
# G-11). NE slabi prod — samo omogućava realan 200 round-trip bez cert-a.
SECURE_SSL_REDIRECT = env.bool("DJANGO_SECURE_SSL_REDIRECT", default=True)
# Env-parametrizovani (default True = prod hardening) radi PRELAZNE HTTP/IP faze pre
# domena+SSL-a: Let's Encrypt ne izdaje cert za golu IP, pa se sajt privremeno servira
# preko HTTP-a. Secure-cookie zastavica nad HTTP-om znaci da browser NE salje cookie →
# admin login + CSRF forme padaju. Override na False SAMO na boxu (.env) za HTTP fazu;
# vrati na True (ukloni override) cim domen+SSL profunkcionišu. Default True → CI/test/prod
# ostaju zakljucani na secure (test_settings_split test_ac3_production_* i dalje prolazi).
SESSION_COOKIE_SECURE = env.bool("DJANGO_SESSION_COOKIE_SECURE", default=True)
CSRF_COOKIE_SECURE = env.bool("DJANGO_CSRF_COOKIE_SECURE", default=True)
LANGUAGE_COOKIE_SECURE = env.bool("DJANGO_LANGUAGE_COOKIE_SECURE", default=True)  # defense-in-depth (Story 1.4 / Dev-B SEC review)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Story 9.1 (G-9/SM-D7): bez ovoga, sa CSRF_COOKIE_SECURE=True + HTTPS reverse-proxy,
# Django 4+ vraća 403 na svaki cross-origin POST (admin-coric login, lead forme) jer
# Origin/Referer ne matchuje. Prod set-uje kroz env (npr. https://coricagrar.rs).
CSRF_TRUSTED_ORIGINS = env.list("DJANGO_CSRF_TRUSTED_ORIGINS", default=[])

# HSTS (1 year default; override-able preko env)
SECURE_HSTS_SECONDS = env.int("DJANGO_SECURE_HSTS_SECONDS", default=31536000)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Additional headers
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"

# ── Logging — per-env tightening (Story 9.6) ─────────────────────────────────
# base.py drži CEO LOGGING dict (SOT); ovde SAMO tighten nivoe (SM-D6). deepcopy da
# NE mutiramo deljenu base nested referencu (G-7 cross-env kontaminacija). NE diramo
# propagate (ostaje True — G-12) niti root/console level (ostaje ≤ INFO — G-13 breadcrumb).
# Retencija/rotacija = HOST-level (journald/Docker log-opt; SM-D7), NE Django.
LOGGING = copy.deepcopy(LOGGING)
LOGGING["loggers"]["django"]["level"] = "WARNING"  # tiši — GlitchTip hvata ERROR+
LOGGING["loggers"]["django.request"]["level"] = "ERROR"
LOGGING["loggers"]["django.security"]["level"] = "ERROR"
LOGGING["loggers"]["apps"]["level"] = "INFO"

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

# ── Error tracking — GlitchTip / Sentry SDK (Story 9.3) ──────────────────────
# DSN-guarded init (SM-D3/G-2): prazan/odsutan GLITCHTIP_DSN → no-op, Django se DIŽE
# bez crash-a (#1 testabilni behavior). Setovan DSN → init sa GDPR-safe kwargs-ima.
# `import sentry_sdk` je pure-python, bez side-effect-a na import (G-3); `init()` je
# guarded. environment="production" razdvaja prod/staging event-e u GlitchTip UI (G-4).
# LOGGING dict živi u base.py (9.6); ovde samo per-env tightening (gore). sentry-sdk
# default LoggingIntegration jaše sama (NE dodajemo Sentry handler u LOGGING — SM-D3/D9).
import sentry_sdk  # noqa: E402

GLITCHTIP_DSN = env("GLITCHTIP_DSN", default="")
if GLITCHTIP_DSN:
    sentry_sdk.init(
        dsn=GLITCHTIP_DSN,
        traces_sample_rate=env.float("SENTRY_TRACES_SAMPLE_RATE", default=0.0),
        send_default_pii=False,  # GDPR (Epic 7) — NIKAD PII (IP/user/cookie/headeri)
        environment="production",
        # SM-D7: release tag SAMO ako IMAGE_TAG netrivijalan (NE git subprocess u settings).
        release=env("IMAGE_TAG", default="") or None,
    )
