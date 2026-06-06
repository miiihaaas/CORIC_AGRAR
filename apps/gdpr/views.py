"""Story 7.1 — javna strana politike kolačića (AC7).

GET-only READ-ONLY render strana (mirror pages.ContactView): `http_method_names`
izostavlja `post` → HTTP 405 za POST. Sadržaj dolazi iz `CookiePolicy.load()`
singleton-a (lazy get_or_create pk=1 — siguran i pre seed-a).
"""

from __future__ import annotations

from django.views.generic import TemplateView

from apps.gdpr.models import CookiePolicy


class CookiePolicyView(TemplateView):
    """„Politika kolačića" javna strana (/sr/politika-kolacica/)."""

    template_name = "gdpr/cookie_policy.html"
    http_method_names = ["get", "head", "options"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["policy"] = CookiePolicy.load()
        return context
