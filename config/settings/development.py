"""Development settings — used locally via `manage.py runserver` and `just dev`."""

from .base import *  # noqa: F401, F403

# Dev convenience override (overrides base default of False)
DEBUG = True

# Dev hosts only
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "[::1]"]

# django-debug-toolbar requires this in dev
INTERNAL_IPS = ["127.0.0.1"]

# Email goes to console in dev (no SMTP needed)
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
