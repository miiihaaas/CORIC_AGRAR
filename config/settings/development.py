"""Development settings — used locally via `manage.py runserver` and `just dev`."""

import copy

from .base import *  # noqa: F401, F403
from .base import LOGGING  # eksplicitno za LOGGING loosen (izbegava F405 star-import warning)

# Dev convenience override (overrides base default of False)
DEBUG = True

# Dev hosts only
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "[::1]"]

# django-debug-toolbar requires this in dev
INTERNAL_IPS = ["127.0.0.1"]

# Email goes to console in dev (no SMTP needed)
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Static files storage override za dev.
# Dev koristi plain StaticFilesStorage (NO manifest).
# CompressedManifestStaticFilesStorage zahteva staticfiles.json (generisan posle
# collectstatic-a) — bez njega {% static %} baca ValueError pri prvom render-u.
# Dev server čita direktno iz STATICFILES_DIRS preko Whitenoise middleware-a.
# Vidi Gotcha #28.
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

# Whitenoise: serve static files iz STATICFILES_DIRS via finders (bez collectstatic-a).
# Default Whitenoise ponašanje je `use_finders = settings.DEBUG`, ali pytest-django
# automatski postavlja DEBUG=False — bez explicit override-a, Whitenoise pokušava
# da servira iz STATIC_ROOT-a (koji ne postoji u dev/test-u). Explicit True osigurava
# da i pytest Client GET-ovi rade bez prethodnog collectstatic-a.
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = True

# ── Logging — per-env loosen (Story 9.6) ─────────────────────────────────────
# Dev verbose vs prod tiši (AC5). deepcopy da NE mutiramo deljenu base referencu (G-7).
# Numerički niži nivoi od prod-a: apps DEBUG(10) < INFO(20), django INFO(20) < WARNING(30).
# console ostaje stdout; propagate ostaje True (G-12); root/console level ≤ INFO (G-13).
LOGGING = copy.deepcopy(LOGGING)
LOGGING["loggers"]["apps"]["level"] = "DEBUG"  # verbose dev app log
LOGGING["loggers"]["django"]["level"] = "INFO"  # niži (verbose-niji) od prod WARNING
