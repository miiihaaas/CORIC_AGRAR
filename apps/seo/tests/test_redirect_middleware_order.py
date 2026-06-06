"""Story 6.4 — MIDDLEWARE ORDER lock (TEA RED phase, AC2/SM-D1).

Najjeftiniji a najvredniji test: zaključava SM-D1 glavnu odluku —
`apps.seo.middleware.RedirectMiddleware` MORA biti u settings.MIDDLEWARE
PRE `django.middleware.locale.LocaleMiddleware` (raw-path match SA locale
prefiksom; short-circuit PRE APPEND_SLASH/locale-redirect interakcije — SEO4-1).
Ako iko premesti middleware POSLE Locale → test RED.

NE zahteva DB (čista settings introspekcija) — bez @pytest.mark.django_db.

Refs:
- 6-4-redirect-manager-301.md AC2 + Task 4/6.4 + SM-D1 + Gotcha SEO4-1
- 6-4-interface-contract.md § 2. Middleware Order
"""

from __future__ import annotations

from django.conf import settings

_REDIRECT_MW = "apps.seo.middleware.RedirectMiddleware"
_LOCALE_MW = "django.middleware.locale.LocaleMiddleware"


# AC2/SM-D1: RedirectMiddleware je registrovan u MIDDLEWARE
def test_redirect_middleware_registered():
    assert _REDIRECT_MW in settings.MIDDLEWARE, (
        f"{_REDIRECT_MW} MORA biti registrovan u settings.MIDDLEWARE (AC2/SM-D1)."
    )


# AC2/SM-D1: RedirectMiddleware PRE LocaleMiddleware (index < index)
def test_redirect_middleware_before_locale():
    mw = list(settings.MIDDLEWARE)
    assert _REDIRECT_MW in mw, f"{_REDIRECT_MW} nije u MIDDLEWARE (AC2/SM-D1)."
    assert _LOCALE_MW in mw, f"{_LOCALE_MW} nije u MIDDLEWARE (baseline)."
    assert mw.index(_REDIRECT_MW) < mw.index(_LOCALE_MW), (
        "RedirectMiddleware MORA biti PRE LocaleMiddleware u MIDDLEWARE "
        f"(index({mw.index(_REDIRECT_MW)}) < index({mw.index(_LOCALE_MW)})) — "
        "raw-path match SA locale prefiksom; short-circuit PRE APPEND_SLASH (SM-D1/SEO4-1)."
    )


# SM-D1: pozicioniran POSLE SessionMiddleware (insert između Session i Locale)
def test_redirect_middleware_after_session():
    mw = list(settings.MIDDLEWARE)
    session_mw = "django.contrib.sessions.middleware.SessionMiddleware"
    assert session_mw in mw, f"{session_mw} nije u MIDDLEWARE (baseline)."
    assert mw.index(session_mw) < mw.index(_REDIRECT_MW), (
        "RedirectMiddleware ide POSLE SessionMiddleware (insert između Session i Locale — SM-D1)."
    )
