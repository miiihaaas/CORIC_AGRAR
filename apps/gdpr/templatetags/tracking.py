"""Story 7.3 — `{% ga_pixel %}` + `{% fb_pixel %}` consent-gated tracking tagovi.

CONSUMER strana consent boundary-ja: čitaju `context["consent_state"]` (iz NOVOG
`apps/gdpr/context_processors.py:consent_state`) + env-driven settings ID
(`GA_MEASUREMENT_ID`/`FB_PIXEL_ID`). Render GA4/FB script SAMO uz odgovarajući
consent flag I neprazan ID; inače `""` (NIJEDAN tracker network request pre
consent-a — server-rendered conditional).

Guard (kanonska forma; ekvivalentno striktnom `is True` jer context_processor
čuva SAMO bool-ove — SM-D10/CRITICAL-2): `if not consent.get(...) or not id: return ""`.
`consent = context.get("consent_state", DEFAULT_DENY)` → privacy-fail-safe (G-1):
ako context_processor nije registrovan ILI manual Context render bez ključa →
default-deny → render "" (NIKAD tracker, NIKAD KeyError/500). Mis-registracija je
pokrivena dedikovanim registration testom (test_consent_state_context_processor_registered)
→ fail-loud bi dodao 0 detekcije; .get(DEFAULT_DENY) je decoupled + fail-safe izbor.

CRITICAL-1 / SM-D11 (brace-safe build — mirror `seo_meta.py:seo_head`): brace-heavy
JS telo (`function gtag(){...}`, `!function(f,b,e,v,n,t,s){...}(...)`) je STATIČKI
`mark_safe(...)` string — NIKAD ne prolazi kroz `format_html` format-string
(literalne `{`/`}` → `str.format()` → KeyError/ValueError/IndexError → 500). SAMO
ID ide kroz `format_html` na BRACE-FREE fragmente (defense-in-depth escape; ID je
trusted settings, NE user input — NIKAD `mark_safe(f"...{id}...")` na neescapiranom
ID-u, G-5). Spaja se `mark_safe("\n".join(parts))`.

CSP-forward (G-7/OQ-1): inline gtag/fbq config je dozvoljen DANAS (django-csp NIJE
konfigurisan); Epic 9 CSP traži nonce/hash + script-src za tracker domene.
"""

from __future__ import annotations

from django import template
from django.conf import settings
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from apps.gdpr.context_processors import DEFAULT_DENY

register = template.Library()

# Brace-heavy JS telo je STATIČKO → mark_safe (NIKAD kroz format_html format-string).
_GA_INLINE_BODY = mark_safe(
    "window.dataLayer = window.dataLayer || [];"
    "function gtag(){dataLayer.push(arguments);}"
    "gtag('js', new Date());"
)

# fbq IIFE je STATIČKO → mark_safe (literalne `{`/`}` lome str.format()).
_FB_INLINE_IIFE = mark_safe(
    "!function(f,b,e,v,n,t,s)"
    "{if(f.fbq)return;n=f.fbq=function(){n.callMethod?"
    "n.callMethod.apply(n,arguments):n.queue.push(arguments)};"
    "if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';"
    "n.queue=[];t=b.createElement(e);t.async=!0;"
    "t.src=v;s=b.getElementsByTagName(e)[0];"
    "s.parentNode.insertBefore(t,s)}(window, document,'script',"
    "'https://connect.facebook.net/en_US/fbevents.js');"
)


@register.simple_tag(takes_context=True)
def ga_pixel(context):
    """Render GA4 gtag SAMO uz analytical consent + neprazan GA_MEASUREMENT_ID."""
    consent = context.get("consent_state", DEFAULT_DENY)  # privacy-fail-safe (G-1)
    gid = settings.GA_MEASUREMENT_ID
    if not consent.get("analytical") or not gid:
        return ""

    parts = [
        # ID kroz format_html na BRACE-FREE fragment (escaped; CRITICAL-1).
        format_html(
            '<script async src="https://www.googletagmanager.com/gtag/js?id={}"></script>',
            gid,
        ),
        "<script>",
        _GA_INLINE_BODY,  # STATIČKO brace-heavy telo (mark_safe)
        format_html("gtag('config', '{}');", gid),  # brace-free + escaped ID
        "</script>",
    ]
    return mark_safe("\n".join(parts))


@register.simple_tag(takes_context=True)
def fb_pixel(context):
    """Render FB Pixel SAMO uz marketing consent + neprazan FB_PIXEL_ID."""
    consent = context.get("consent_state", DEFAULT_DENY)  # privacy-fail-safe (G-1)
    pid = settings.FB_PIXEL_ID
    if not consent.get("marketing") or not pid:
        return ""

    parts = [
        "<script>",
        _FB_INLINE_IIFE,  # STATIČKO brace-heavy IIFE (mark_safe)
        format_html("fbq('init', '{}');", pid),  # brace-free + escaped ID
        "fbq('track', 'PageView');",
        "</script>",
        # noscript fallback je TAKOĐE gated consent-om (G-6; deo render izlaza).
        format_html(
            '<noscript><img height="1" width="1" style="display:none" '
            'src="https://www.facebook.com/tr?id={}&amp;ev=PageView&amp;noscript=1"/>'
            "</noscript>",
            pid,
        ),
    ]
    return mark_safe("\n".join(parts))
