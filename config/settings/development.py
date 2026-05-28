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
