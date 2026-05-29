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
# NAPOMENA: Story 1.2 zadržava default Django INSTALLED_APPS. Story 1.6 dodaje
# django_htmx + django_bootstrap5 (template tag discovery + middleware reg).
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_htmx",  # NOVO Story 1.6 — request.htmx detection
    "django_bootstrap5",  # NOVO Story 1.6 — {% bootstrap_css %} / {% bootstrap_javascript %} template tags
    "apps.core",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # POSLE Security, PRE Session (Whitenoise docs)
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_htmx.middleware.HtmxMiddleware",  # NOVO Story 1.6 — postavlja request.htmx
    "apps.core.middleware.LocaleSwitcherMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.template.context_processors.i18n",
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
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ── i18n / l10n ──────────────────────────────────────────────────────────────
# i18n configured for sr (Srpski, primary), hu (Magyar), en (English).
LANGUAGES = [
    ("sr", "Srpski"),
    ("hu", "Magyar"),
    ("en", "English"),
]
LANGUAGE_CODE = "sr"
LOCALE_PATHS = [BASE_DIR / "locale"]
TIME_ZONE = "UTC"
USE_I18N = True
USE_L10N = True
USE_TZ = True

# ── Static ───────────────────────────────────────────────────────────────────
# base.py definiše osnovni STORAGES dict sa plain StaticFilesStorage (Django default).
# Env-specific settings override-uju STORAGES["staticfiles"]:
#   - development.py: plain StaticFilesStorage (no manifest, no collectstatic needed)
#   - production.py / staging.py: Whitenoise CompressedManifestStaticFilesStorage
#     (gzip + brotli + hash cache-busting; zahteva collectstatic deploy step)
# STATIC_URL ima leading slash radi i18n_patterns kompatibilnosti — bez slash-a
# {% static %} resolve uvodi current locale prefix (/sr/static/...) → 404. Vidi Gotcha #29.
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# ── Bootstrap 5 ──────────────────────────────────────────────────────────────
# django-bootstrap5 konfiguracija. base.py = DEV variant (CDN jsDelivr) per
# project-context.md § Frontend frameworks line 67 ("Bootstrap 5.3 — CDN u dev,
# local u prod"). production.py override-uje na local /static/vendor/.
# Verzija pinned na 5.3.3 (latest stable 5.x kao 2026-05).
# `integrity: None` eksplicitno suprimira django-bootstrap5 default SRI check
# (vidi Gotcha #19 — bez ovoga, override css_url bez SRI hash-a baca
# SubresourceIntegrityError).
BOOTSTRAP5 = {
    "css_url": {
        "url": "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css",
        "integrity": None,
    },
    "javascript_url": {
        "url": "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js",
        "integrity": None,
    },
    "javascript_in_head": False,
    "include_jquery": False,
}

# ── Default ─────────────────────────────────────────────────────────────────
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
