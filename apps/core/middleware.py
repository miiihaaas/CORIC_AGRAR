"""Custom middleware-i za apps.core.

LocaleSwitcherMiddleware: query-param override za locale (`?lang=sr`). Radi POSLE
Django built-in `LocaleMiddleware` (koji handluje URL-prefix detekciju) — služi kao
escape hatch za switcher dropdown i programatske locale promene.
"""

from django.conf import settings
from django.http import HttpResponseRedirect
from django.urls import translate_url


class LocaleSwitcherMiddleware:
    """Middleware koji omogućuje promenu lokala kroz `?lang=<code>` query parametar.

    Implementacija prati `django.views.i18n.set_language` pattern:
    - Kada se detektuje validan `?lang=X`, vraćamo 302 redirect na `translate_url(path, X)`
      sa postavljenim cookie-jem.
    - Razlog: `translation.activate(lang)` PRE URL resolvera nije dovoljno — Django
      resolver matchuje `i18n_patterns()` prefix prema URL putanji (npr. `/sr/`),
      pa `?lang=hu` na `/sr/...` putanji ne menja URL i bez redirect-a daje 404.
    - Cookie persistuje izbor između requesta (Django LocaleMiddleware čita cookie
      sa imenom `settings.LANGUAGE_COOKIE_NAME`).

    Unsupported lokal kodovi (`?lang=de`) se tiho ignorišu — request prolazi normalno.

    NAPOMENA: session storage namerno izostavljen — bivši
    `translation.LANGUAGE_SESSION_KEY` je UKLONJEN u Django 4.0 (NIJE alias). Cookie
    + Django's `LocaleMiddleware` (koji čita cookie sa imenom
    settings.LANGUAGE_COOKIE_NAME) dovoljni su za persistenciju lokala između
    requesta i sesija.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.supported = set(dict(settings.LANGUAGES).keys())

    def __call__(self, request):
        requested = request.GET.get("lang")
        if requested and requested in self.supported:
            # Redirect na prevedenu URL putanju (translate_url prepiše locale prefix)
            new_url = translate_url(request.path, requested)
            # Sačuvaj ostale query parametre osim `lang`
            qs = request.GET.copy()
            qs.pop("lang", None)
            if qs:
                new_url = f"{new_url}?{qs.urlencode()}"
            response = HttpResponseRedirect(new_url)
            response.set_cookie(
                settings.LANGUAGE_COOKIE_NAME,
                requested,
                max_age=getattr(settings, "LANGUAGE_COOKIE_AGE", None)
                or 60 * 60 * 24 * 365,
                path=settings.LANGUAGE_COOKIE_PATH,
                domain=settings.LANGUAGE_COOKIE_DOMAIN,
                secure=settings.LANGUAGE_COOKIE_SECURE,
                httponly=settings.LANGUAGE_COOKIE_HTTPONLY,
                samesite=settings.LANGUAGE_COOKIE_SAMESITE,
            )
            return response
        return self.get_response(request)
