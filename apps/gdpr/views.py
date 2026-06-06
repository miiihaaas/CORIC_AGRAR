"""Story 7.1/7.2 — apps.gdpr views.

7.1: `CookiePolicyView` — javna READ-ONLY strana politike kolačića.
7.2: `SetConsentView` — POST-only state-change view koja postavlja `consent_state`
kolačić (365d) iz consent izbora i redirect-uje nazad (303 See Other) na
same-origin `next`/referer sa open-redirect guard-om.
"""

from __future__ import annotations

import json

from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View
from django.views.generic import TemplateView
from django_ratelimit.decorators import ratelimit

from apps.gdpr.models import CookiePolicy

CONSENT_MAX_AGE = 60 * 60 * 24 * 365  # 365 dana (SM-D1)


class CookiePolicyView(TemplateView):
    """„Politika kolačića" javna strana (/sr/politika-kolacica/)."""

    template_name = "gdpr/cookie_policy.html"
    http_method_names = ["get", "head", "options"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["policy"] = CookiePolicy.load()
        return context


def _build_consent(request) -> dict:
    """Izgradi consent dict iz POST-a. `necessary` UVEK True (SERVER-FORCED; G-3).

    Nepoznata ILI nedostajuća `action` → default-deny (== reject_all; G-15).
    """
    action = request.POST.get("action")
    if action == "accept_all":
        return {"necessary": True, "analytical": True, "marketing": True}
    if action == "save":
        return {
            "necessary": True,
            "analytical": "analytical" in request.POST,
            "marketing": "marketing" in request.POST,
        }
    # reject_all + nepoznata/nedostajuća action → default-deny.
    return {"necessary": True, "analytical": False, "marketing": False}


def _safe_redirect_target(request) -> str:
    """Open-redirect guard (mirror 6-4 / seo/models.py:98). Same-origin only.

    next (POST) → HTTP_REFERER → reverse("pages:home") fallback. Odbija
    https://evil.com, //evil.com itd. kroz url_has_allowed_host_and_scheme.
    """
    allowed_hosts = {request.get_host()}
    require_https = request.is_secure()
    for candidate in (
        request.POST.get("next"),
        request.META.get("HTTP_REFERER", ""),
    ):
        if candidate and url_has_allowed_host_and_scheme(
            url=candidate, allowed_hosts=allowed_hosts, require_https=require_https
        ):
            return candidate
    return reverse("pages:home")


@method_decorator(
    ratelimit(key="ip", rate="10/m", block=False), name="dispatch"
)
class SetConsentView(View):
    """POST-only consent-setter (CSRF mandatory, ratelimit 10/m; SM-D3/D7/D9)."""

    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        if getattr(request, "limited", False):
            return HttpResponse(status=429)

        consent = _build_consent(request)
        target = _safe_redirect_target(request)

        response = HttpResponseRedirect(target)
        response.status_code = 303  # See Other — POST→GET semantika (SM-D3)
        response.set_cookie(
            "consent_state",
            json.dumps(consent),
            max_age=CONSENT_MAX_AGE,
            samesite="Lax",
            secure=settings.SESSION_COOKIE_SECURE,
            httponly=False,
            path="/",
        )
        return response
