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
    # NAPOMENA: modeltranslation MORA biti PRE django.contrib.admin
    # (per django-modeltranslation docs § Configuration — admin integration
    # patch-uje admin pri AppConfig.ready() i mora imati referenciu na
    # admin pre nego što admin registruje own widget-e). Vidi Story 2.1
    # Decision D2 + Gotcha BR-2.
    "modeltranslation",  # NOVO Story 2.1 — MORA PRE django.contrib.admin
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",  # NOVO Story 2.13 — SearchVectorField + GinIndex system checks (SM-D6)
    "django.contrib.sitemaps",  # NOVO Story 6.2 — sitemap.xml framework (0-migration; NE django.contrib.sites — SM-D2)
    "django_htmx",  # NOVO Story 1.6 — request.htmx detection
    "django_bootstrap5",  # NOVO Story 1.6 — {% bootstrap_css %} / {% bootstrap_javascript %} template tags
    "apps.core",
    "apps.brands",  # NOVO Story 2.1 — Brand/Series/Category/Subcategory domain app
    "apps.products",  # NOVO Story 2.2 — Product i related modeli (POSLE brands per dep rule)
    "apps.search",  # NOVO Story 2.13 — site-wide search (POSLE products; search → products dep, SM-D2)
    "apps.pages",  # NOVO Story 3.1 — top-level app (Home/About/Contact); READ-ONLY agregacija domain modela (POSLE products)
    "sorl.thumbnail",  # NOVO Story 2.3 — third-party paket POSLE domain app-ova (utility lib)
    "apps.media_pipeline",  # NOVO Story 2.3 — utility app POSLE sorl.thumbnail (koristi njegove template tags)
    "apps.forms",  # NOVO Story 4.1 — lead-gen forms app (samostalan top-level; POSLE domain app-ova, SM-D1)
    "apps.blog",  # NOVO Story 5.1 — Blog „Priče sa polja" content app (samostalan; POSLE modeltranslation + domain app-ova, SM-D1)
    "apps.seo",  # NOVO Story 6.1 — SEO & Discoverability (SeoMeta GFK; POSLE modeltranslation + domain app-ova + apps.blog jer generic inline žičan na njihove admin-e, SM-D9)
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
                "apps.blog.context_processors.latest_blog_posts",  # NOVO Story 5.4 — footer Najnovije vesti
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

# ── Email — Story 4.1 (lead-gen forme) ───────────────────────────────────────
# DEFAULT_FROM_EMAIL: eksplicitan sender (NE Django default „webmaster@localhost").
# Staging/prod šalje kroz anymail Resend backend (EMAIL_BACKEND override u tim modulima);
# real key/verifikovan sender domen = OQ-4 (biznis/ops input).
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="no-reply@coricagrar.rs")
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# Sync send timeout (sekunde) — hung Resend/SMTP konekcija NE sme blokirati worker.
EMAIL_TIMEOUT = 10

# django-anymail (Resend) — RESEND_API_KEY iz env (prazan default u dev/test; SM-D2).
ANYMAIL = {"RESEND_API_KEY": env("ANYMAIL_RESEND_API_KEY", default="")}

# Per-segment recipient-i (send_lead_email bira po lead.form_type — SM-D7).
# Bezbedan prazan default za dev/test (prazan recipient → service tretira kao failed send, C1).
CONTACT_EMAIL_TO = env("CONTACT_EMAIL_TO", default="")
SERVICE_EMAIL_TO = env("SERVICE_EMAIL_TO", default="")
PARTS_EMAIL_TO = env("PARTS_EMAIL_TO", default="")

# ── Cache (ratelimit backend) — Story 4.2 (SM-D10) ───────────────────────────
# django-ratelimit koristi Django `default` cache za brojanje zahteva po IP-u.
# locmem je dovoljan za v1 (single-process dev/test); prod skaliranje (shared
# cache) je Epic 9/4.6 odluka — NE Redis sada (YAGNI, project-context.md:84).
CACHES = {
    "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
}

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
# Story 2.2 — architecture-defensive locale fallback chain (NIJE FR-32 mapiranje —
# FR-32 je view-layer marker u Story 6.5). Modeltranslation zahteva deterministički
# fallback chain ka sr da bi pristup translated polju bez aktivnog language context-a
# vratio sr fallback umesto None. Vidi project-context.md § i18n locale fallback.
MODELTRANSLATION_FALLBACK_LANGUAGES = ("sr",)
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

# ── Media ────────────────────────────────────────────────────────────────────
# MEDIA_URL ima leading slash radi i18n_patterns kompatibilnosti (matches STATIC_URL).
# MEDIA_ROOT je BASE_DIR/media (development); production override može menjati za
# Nginx serving direktno iz disk-a.
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# FIX-4 (Security MEDIUM-1) — Django upload limits sinhronizovani sa
# apps/media_pipeline/utils.MAX_UPLOAD_SIZE_BYTES (10 MB). Default Django limit
# je 2.5 MB što bi za uploads između 2.5–10 MB spool-ovao na disk (file pointer
# umesto in-memory), čineći helper limit nejednoznačnim. Drži 1 MB buffer iznad
# helper limita kao defense-in-depth (helper raise-uje pre Django parse).
DATA_UPLOAD_MAX_MEMORY_SIZE = 11 * 1024 * 1024  # 11 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10 MB

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# ── sorl-thumbnail (Story 2.3) ───────────────────────────────────────────────
# Image pipeline za responsive srcset (400w/800w/1600w varijante) na svim
# Product/Brand/ProductImage/ProductVariant/ProductTestimonial image poljima.
# Lazy generation: thumbnail-ovi se kreiraju on-demand pri prvom HTTP GET-u
# na URL slike, NE post-save signal. KVStore cache-uje (image_path, geometry)
# → thumbnail URL mapping za fast hit drugi render.
# Vidi project-context.md § Media pipeline + architecture.md § Image processing.
THUMBNAIL_BACKEND = "sorl.thumbnail.base.ThumbnailBackend"
THUMBNAIL_KVSTORE = "sorl.thumbnail.kvstores.cached_db_kvstore.KVStore"
THUMBNAIL_FORMAT = "JPEG"
THUMBNAIL_QUALITY = 85
THUMBNAIL_PRESERVE_FORMAT = False  # per-call override via `format='PNG'` u {% responsive_picture %} (Decision MP-D5)
# NAPOMENA: sorl-thumbnail koristi THUMBNAIL_PREFIX (sa trailing slash) kao subdirektorijum
# unutar MEDIA_ROOT za sve thumbnail-ove. Story 2.3 spec je referencirao THUMBNAIL_DIRNAME
# (ne postoji kao sorl setting) — kanonski naziv je THUMBNAIL_PREFIX.
THUMBNAIL_PREFIX = "thumbnails/"
# FIX-3 (Security HIGH-2) — THUMBNAIL_DEBUG je hardcoded False u svim env-ovima.
# Kad je True, sorl-thumbnail u template render-u vraća stack trace sa Pillow verzijom
# i MEDIA_ROOT putanjom — info leak rizik ako DEBUG=True curne u staging.
# Per story 2.3 AC2 + interface contract (Decision MP-D7 dodaje rename na PREFIX).
# Dev-only override (npr. dev investigation): postaviti u development.py.
THUMBNAIL_DEBUG = False

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
