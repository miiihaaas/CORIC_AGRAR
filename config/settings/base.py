"""Common settings (base). Inherited by development.py, staging.py, production.py."""

from datetime import timedelta
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
    "axes",  # NOVO Story 8.1 — brute-force lockout (POSLE django.contrib.auth + contenttypes; G-16)
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
    "apps.gdpr",  # NOVO Story 7.1 — GDPR & Privacy (CookiePolicy singleton; POSLE modeltranslation + domain app-ova; gdpr nema cross-app dep, SM-D1)
    "apps.accounts",  # NOVO Story 8.1 — admin auth hardening (AdminLoginForm wiring; POSLE domain app-ova, SM-D10)
    "apps.admin_ext",  # NOVO Story 8.3 — admin dashboard override (POSLE accounts; mora POSLE django.contrib.admin, G-3)
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # POSLE Security, PRE Session (Whitenoise docs)
    "django.contrib.sessions.middleware.SessionMiddleware",
    "apps.seo.middleware.RedirectMiddleware",  # NOVO Story 6.4 — PRE LocaleMiddleware (raw-path match SA locale prefiksom; SM-D1)
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_htmx.middleware.HtmxMiddleware",  # NOVO Story 1.6 — postavlja request.htmx
    "apps.core.middleware.LocaleSwitcherMiddleware",
    "axes.middleware.AxesMiddleware",  # NOVO Story 8.1 — MORA biti POSLEDNJI (posle AuthenticationMiddleware; G-2/SM-D17)
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
                "apps.gdpr.context_processors.consent_state",  # NOVO Story 7.3 — consent-gated tracking (POSLE blog-a, G-9)
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

# ── Tracking (Epic 7, Story 7.3) ─────────────────────────────────────────────
# GA4 / Facebook Pixel ID-jevi — env-driven (per-environment infra config NE
# editorial; SiteSettings nema ID polja). Prazan default → dev/test render NIŠTA
# (no-tracker fail-safe; {% ga_pixel %}/{% fb_pixel %} no-ID grana). Staging/prod
# set-uje realne ID-jeve kroz env (Hetzner secrets). Mirror ANYMAIL pattern.
GA_MEASUREMENT_ID = env("GA_MEASUREMENT_ID", default="")
FB_PIXEL_ID = env("FB_PIXEL_ID", default="")

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
# Story 8.1 (G-1): base.py ranije NIJE imao AUTHENTICATION_BACKENDS (Django default
# = ModelBackend). django-axes ZAHTEVA eksplicitan backends sa AxesStandaloneBackend
# PRVIM; ModelBackend MORA ostati (bez njega niko se ne loguje).
AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesStandaloneBackend",  # PRVI — v8 standalone (G-4)
    "django.contrib.auth.backends.ModelBackend",  # OBAVEZAN
]

# ── django-axes (Story 8.1 — admin brute-force lockout) ──────────────────────
# 5 kumulativnih neuspelih pokušaja (IP) → 1h lockout (SM-D16/SM-D19). Off-by-one:
# axes zaključava NA limitu → 5. neuspeli pokušaj SAM triggeruje lockout (429).
# Prod proxy-IP rezolucija (AXES_IPWARE_PROXY_COUNT) je DEFER na Epic 9 (SM-D18/OQ-5).
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = timedelta(hours=1)  # lockout DURATION (1h)
AXES_RESET_ON_SUCCESS = True  # uspešan login resetuje brojač
AXES_LOCKOUT_PARAMETERS = [["ip_address"]]  # v8 IP-based lockout (SM-D16)
AXES_LOCKOUT_TEMPLATE = "accounts/lockout.html"  # STANDALONE strana (SM-D11)
AXES_HTTP_RESPONSE_CODE = 429  # lockout status (AC4)

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ── Session (Story 8.1 — admin session timeout) ──────────────────────────────
# 4h apsolutni session timeout (epics 8.1 / arch:178 / NFR-3). SESSION_COOKIE_HTTPONLY
# ostaje Django default True; SESSION_EXPIRE_AT_BROWSER_CLOSE ostaje False (G-10/G-16).
SESSION_COOKIE_AGE = 14400  # 4h = 14400s

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

# ── Logging (Story 9.6) ──────────────────────────────────────────────────────
# LEAN, zero-dep Django-native LOGGING dict (SOT u base.py — per-env moduli SAMO
# tighten/loosen nivoe; SM-D6). Console handler → stdout (12-factor; Docker/journald
# capture-uje, SM-D1). NEMA in-container file handler-a, NEMA python-json-logger (SM-D2).
#
# Sentry/GlitchTip koegzistencija (9-3): NIJEDAN sentry handler u LOGGING — sentry-sdk
# LoggingIntegration jaše sama na ROOT loggeru i hvata record-e kad PROPAGIRAJU naviše
# (SM-D3). KANONSKI OBRAZAC: console handler SAMO na `root`, žičani loggeri propagate=True
# bez sopstvenog handler-a → istovremeno gasi dupli red (G-6) I čuva Sentry propagaciju
# (G-12). root/console level ≤ INFO da INFO+→breadcrumb radi (G-13).
#
# Log retencija/rotacija = HOST-level (journald `SystemMaxUse`/Docker `--log-opt
# max-size/max-file`), NE Django (SM-D7; mirror 9-5 host-cron). NE pišemo logrotate config.
#
# `disable_existing_loggers: False` je OBAVEZAN (G-1) — dictConfig default je True što
# bi UGASILO Django interne + sentry-sdk loggere.
#
# PII UPOZORENJE (dev-guidance): sam TEKST log poruke stiže u GlitchTip kao breadcrumb/event
# preko sentry-sdk LoggingIntegration BEZ OBZIRA na send_default_pii=False (taj flag skida samo
# SDK-auto PII: IP/user/cookie/header) — NIKAD ne logujte secret/PII u string poruke.

# Env-gated nivo (SM-D9) — operativna fleksibilnost bez redeploy-a. Production-safe
# default (INFO, NE DEBUG — DEBUG bi log-ovao osetljive detalje + noise; G-8/G-13).
DJANGO_LOG_LEVEL = env("DJANGO_LOG_LEVEL", default="INFO")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,  # OBAVEZNO False (G-1/AC4)
    "formatters": {
        "verbose": {
            # Zero-dep Django-native (SM-D2). SAMO logging metapodaci — NEMA PII/secret
            # token-a (AC6): level/timestamp/logger/module/process/thread/message.
            "format": (
                "{levelname} {asctime} {name} {module} "
                "{process:d} {thread:d} {message}"
            ),
            "style": "{",  # {} placeholderi → style "{" (G-10)
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",  # STDOUT, NE stderr default (G-2/AC2)
            "formatter": "verbose",
            "level": "DEBUG",  # handler propušta sve; loggeri/root filtriraju nivoom
        },
    },
    "root": {
        "handlers": ["console"],  # console SAMO na root (kanonski obrazac SM-D8)
        "level": DJANGO_LOG_LEVEL,  # ≤ INFO (G-13 — Sentry breadcrumb-ovi)
    },
    "loggers": {
        # Žičani loggeri NEMAJU sopstveni handler; propagate=True → record stiže do root
        # console handler-a I do sentry-sdk root-attached capture handler-a. Per-logger
        # tiše = preko `level`, NIKAD propagate=False + sopstveni handler (G-12).
        "django": {"level": "INFO", "propagate": True},
        "django.request": {"level": "ERROR", "propagate": True},
        "django.security": {"level": "ERROR", "propagate": True},
        "apps": {"level": "INFO", "propagate": True},  # project logger — hvata sve apps.*
        # NE žičamo: django.db.backends (SQL noise/PII — G-8), django.server (request-line leak).
    },
}

# ── Default ─────────────────────────────────────────────────────────────────
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
