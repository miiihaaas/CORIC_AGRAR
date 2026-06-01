"""Story 4.1 — AC6 email backend + ANYMAIL/env settings (TEA RED phase).

Pokriva AC6:
- TEST env koristi locmem (NE console/anymail u testu) — pytest-django override + mailoutbox.
- base.py ima DEFAULT_FROM_EMAIL set; ANYMAIL dict; per-segment recipient setting-i.
- staging.py + production.py: EMAIL_BACKEND == "anymail.backends.resend.EmailBackend"
  — INTROSPEKTUJ TAČAN modul (`import config.settings.staging`/`production`), NE
  `django.conf.settings` (koji u testu pokazuje na development/locmem).
- development.py console backend NETAKNUT (dokumentovan regresija-lock — NE dira se).

NAPOMENA RED: locmem + console-NETAKNUT sub-asserti MOGU proći samostalno (već tačno);
ali DEFAULT_FROM_EMAIL/ANYMAIL/staging-anymail asserti PADAJU (settings ih još nema) →
test fajl kao celina je RED.

Refs:
- 4-1-lead-model-smtp-setup.md AC6 + Task 8.9 + SM-D2/D6/D7 + Project Structure Notes
- 4-1-interface-contract.md § 8 (Settings touchpoints)
"""

from __future__ import annotations

import importlib

from django.conf import settings


# AC6: test env koristi locmem (NE console/anymail u testu) — pytest-django override
def test_test_backend_is_locmem():
    assert settings.EMAIL_BACKEND == "django.core.mail.backends.locmem.EmailBackend", (
        f"TEST env MORA koristiti locmem backend (mailoutbox), dobio {settings.EMAIL_BACKEND!r}. "
        "Email testovi NIKAD ne šalju pravi email (project-context.md:267)."
    )


# AC6: DEFAULT_FROM_EMAIL eksplicitno postavljen u base (NE Django default „webmaster@localhost")
def test_default_from_email_is_set():
    value = getattr(settings, "DEFAULT_FROM_EMAIL", "")
    assert value and "@" in value, (
        f"DEFAULT_FROM_EMAIL MORA biti postavljen, dobio {value!r}."
    )
    # Django default je „webmaster@localhost" — MORA biti eksplicitno override-ovan (npr.
    # no-reply@coricagrar.rs). Bez ove provere test bi trivijalno prošao na Django default-u.
    assert value != "webmaster@localhost", (
        f"DEFAULT_FROM_EMAIL MORA biti EKSPLICITNO postavljen u base (NE Django default "
        f"'webmaster@localhost'; npr. no-reply@coricagrar.rs — SM-D6), dobio {value!r}."
    )


# AC6: ANYMAIL dict prisutan u base (RESEND_API_KEY iz env) — SM-D2
def test_anymail_config_present():
    anymail = getattr(settings, "ANYMAIL", None)
    assert isinstance(anymail, dict), (
        f"settings.ANYMAIL MORA biti dict (RESEND_API_KEY iz env — SM-D2), dobio {anymail!r}."
    )
    assert "RESEND_API_KEY" in anymail, (
        f"ANYMAIL MORA imati ključ 'RESEND_API_KEY', dobio {list(anymail)!r}."
    )


# AC6: per-segment recipient setting-i prisutni u base (iz env) — SM-D7
def test_recipient_settings_present():
    for attr in ("CONTACT_EMAIL_TO", "SERVICE_EMAIL_TO", "PARTS_EMAIL_TO"):
        assert hasattr(settings, attr), (
            f"settings.{attr} MORA biti definisan (per-segment recipient iz env — SM-D7)."
        )


# AC6: staging.py EMAIL_BACKEND == anymail Resend (introspektuj TAČAN modul, NE active settings)
def test_staging_email_backend_is_anymail_resend():
    staging = importlib.import_module("config.settings.staging")
    assert getattr(staging, "EMAIL_BACKEND", None) == "anymail.backends.resend.EmailBackend", (
        "config.settings.staging.EMAIL_BACKEND MORA biti 'anymail.backends.resend.EmailBackend' "
        f"(epics.md:773), dobio {getattr(staging, 'EMAIL_BACKEND', None)!r}. Introspektuj modul "
        "direktno — NE django.conf.settings (pokazuje na development/locmem u testu)."
    )


# AC6: production.py EMAIL_BACKEND == anymail Resend (introspektuj TAČAN modul)
def test_production_email_backend_is_anymail_resend():
    production = importlib.import_module("config.settings.production")
    assert getattr(production, "EMAIL_BACKEND", None) == "anymail.backends.resend.EmailBackend", (
        "config.settings.production.EMAIL_BACKEND MORA biti 'anymail.backends.resend.EmailBackend' "
        f"(epics.md:773), dobio {getattr(production, 'EMAIL_BACKEND', None)!r}."
    )


# AC6: development.py console backend NETAKNUT (dokumentovan regresija-lock — SM-D6)
# NAPOMENA: ovo JE već tačno danas → može proći samostalno u RED fazi (namera: dev se NE dira).
def test_development_console_backend_untouched():
    development = importlib.import_module("config.settings.development")
    assert getattr(development, "EMAIL_BACKEND", None) == (
        "django.core.mail.backends.console.EmailBackend"
    ), (
        "config.settings.development.EMAIL_BACKEND MORA OSTATI console backend (NETAKNUT — SM-D6), "
        f"dobio {getattr(development, 'EMAIL_BACKEND', None)!r}."
    )
