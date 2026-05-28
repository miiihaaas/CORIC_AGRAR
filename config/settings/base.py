"""Common settings (base). Inherited by development.py, staging.py, production.py."""

from pathlib import Path

import environ

# ── Env init ─────────────────────────────────────────────────────────────────
# BASE_DIR je 3 nivoa gore: config/settings/base.py → config/settings/ → config/ → <repo root>
BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
# Učitava .env iz repo root-a ako postoji (no-op u prod-u gde se env vars set-uju kroz Docker/Hetzner)
environ.Env.read_env(BASE_DIR / ".env")

# ── Core ─────────────────────────────────────────────────────────────────────
# SECRET_KEY: NEMA default — fail-fast ako env var nije set
SECRET_KEY = env("DJANGO_SECRET_KEY")

# DEBUG: default False — sigurnosno default-uje na production-safe
DEBUG = env.bool("DJANGO_DEBUG", default=False)

# ALLOWED_HOSTS: csv-list iz env
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=[])

# ── Applications ────────────────────────────────────────────────────────────
# NAPOMENA: Story 1.2 zadržava default Django INSTALLED_APPS. 3rd-party app-ovi
# (django-htmx, django-bootstrap5, modeltranslation) dodaju se u kasnijim story-jama.
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# ── Database ─────────────────────────────────────────────────────────────────
# env.db() parsira DATABASE_URL u Django-ready dict.
# Default je SQLite u repo root-u za Story 1.2 smoke-test; Story 1.3 dodaje PostgreSQL.
DATABASES = {
    "default": env.db("DATABASE_URL", default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}"),
}

# ── Email ────────────────────────────────────────────────────────────────────
# env.email_url() ekspanduje u EMAIL_BACKEND, EMAIL_HOST, EMAIL_PORT, ...
# Default 'consolemail://' (print u konzolu — dev-friendly). Story 4.x postavlja Resend/Brevo URL.
EMAIL_CONFIG = env.email_url("EMAIL_URL", default="consolemail://")
vars().update(EMAIL_CONFIG)
# Cleanup: EMAIL_CONFIG dict je pokupljen kao Django setting (uppercase module attribute)
# nakon vars().update(); brisemo ga da se ne pojavi kao spurious setting.
del EMAIL_CONFIG

# ── Auth ─────────────────────────────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ── i18n / l10n ──────────────────────────────────────────────────────────────
# Story 1.4 menja LANGUAGE_CODE na 'sr-latn' i dodaje LANGUAGES/LOCALE_PATHS.
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ── Static ───────────────────────────────────────────────────────────────────
STATIC_URL = "static/"
# STATIC_ROOT, STATICFILES_DIRS, MEDIA_ROOT — dolaze u Story 1.5/1.6 kad static asset folder bude kreiran

# ── Default ─────────────────────────────────────────────────────────────────
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
