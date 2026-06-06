"""Story 7.2 — `{% gdpr_banner %}` template tag (AC1/SM-D2/G-1).

`simple_tag(takes_context=True)` koji renderuje GDPR baner partial SAMO kad je
`consent_state` kolačić ODSUTAN u `request.COOKIES`; inače vraća "" (prazan
string). Presence-only suppression: BILO koja prisutna vrednost (uključujući
garbage/forged) suzbija baner — tag NE parsira JSON (7-3 parsira; Boundary).

`request=request` kwarg u `render_to_string` je OBAVEZAN (G-1): bez njega
`{% csrf_token %}` / `{% url %}` i18n / `{% translate %}` u partial-u ne rade.
`"request"` se NE dodaje redundantno u dict.
"""

from __future__ import annotations

from django import template
from django.template.loader import render_to_string

register = template.Library()


@register.simple_tag(takes_context=True)
def gdpr_banner(context):
    request = context["request"]
    if "consent_state" in request.COOKIES:
        return ""
    return render_to_string(
        "gdpr/_consent_banner.html",
        {"next": request.get_full_path()},
        request=request,
    )
