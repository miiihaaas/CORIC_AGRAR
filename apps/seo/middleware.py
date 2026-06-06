"""Story 6.4 — `RedirectMiddleware` (admin-upravljani 301 redirect).

Trči na SVAKOM request-u PRE LocaleMiddleware (SM-D1 — raw-path match SA locale
prefiksom, short-circuit PRE APPEND_SLASH/locale-redirect interakcija). Skip-uje
admin/static/media PRE DB lookup-a (SM-D3/SEO4-4 — dostupnost admin-a). Na match
vraća HttpResponsePermanentRedirect (301 — SM-D5).

Redosled definicija: module-level konstante → `_is_skipped` helper → klasa
(helper definisan PRE klase koja ga koristi u `__call__`).
"""

from __future__ import annotations

import re

from django.http import HttpResponsePermanentRedirect

from apps.seo.models import Redirect

_SKIP_PREFIXES = ("/static/", "/media/")
# 2-slovni locale prefiks (i18n_patterns) + admin base (tekući `admin` ili
# budući Epic 8 `admin-coric` slug) — forward-safe, NE krhki '/admin/' substring.
_ADMIN_RE = re.compile(r"^/[a-z]{2}/admin(-coric)?/")


def _is_skipped(path):
    return path.startswith(_SKIP_PREFIXES) or bool(_ADMIN_RE.match(path))


class RedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        if not _is_skipped(path):
            redirect = (
                Redirect.objects.filter(old_path=path, is_active=True).first()
            )
            if redirect is not None:
                return HttpResponsePermanentRedirect(redirect.new_path)
        return self.get_response(request)
