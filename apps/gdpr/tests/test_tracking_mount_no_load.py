"""Story 7.3 — AC5/AC6: base.html mount + no-tracker-before-consent (TEA RED, integration).

Pokriva AC5/AC6 + SM-D7/D8 + Gotcha G-1/G-3/G-4/G-14 + CRITICAL-1/2/3:
- `{% ga_pixel %}`/`{% fb_pixel %}` mount-ovani u base.html `<head>` → SVAKA strana
  koja extend-uje base.html render-uje pixel SAMO uz consent + ID; inace NEMA tracker.
- PRIVACY-CRITICAL: bez consent / prazan ID → response NE sadrzi tracker-specificne
  tokene (NIJEDAN tracker network request pre consent-a).
- Posle consent + ID set (override_settings) → response SADRZI tracker (server-rendered
  „page refresh activates pixel"); status 200 (NE 500 — CRITICAL-1).
- malformed/forged kolacic → DEFAULT-DENY → NEMA tracker (G-2/CRITICAL-2).
- G-14: NIKAD out-of-gate preconnect/dns-prefetch/preload ka tracker domenima.

⚠️ CRITICAL-3: asertuje ODSUSTVO SAMO tracker-loading tokena (`googletagmanager.com/
gtag/js`, `gtag(`, `connect.facebook.net`, `facebook.com/tr`, `fbq(`) — NIKAD bare
`facebook`/`google` (SiteSettings.social_facebook URL je legitimno site-wide prisutan
u footer/OG → bare-token asercija bi false-fail-ovala).

INTEGRACIJSKA STRANA: `/sr/o-nama/` (pages:about AboutView — staticka TemplateView
BEZ DB fixtura; home `/sr/` trazi product/brand seed-ove → izbegnut). Isti izbor kao 7-2.

RED razlog: base.html JOS NE mount-uje `{% ga_pixel %}`/`{% fb_pixel %}` + `tracking`
nije u `{% load %}` → cim Dev doda, tag mora postojati. Do tada: positive-render
testovi (consent+ID) ne nadju tracker token → FAIL.

Pokrenuti:
    docker compose -f compose/local.yml run --rm django \
        uv run pytest apps/gdpr/tests/test_tracking_mount_no_load.py -v

Refs: 7-3 AC5/AC6 + SM-D7/D8 + Gotcha G-1/G-3/G-4/G-14 + CRITICAL-1/2/3;
      7-3-interface-contract § mount. base.html `/sr/o-nama/` mirror 7-2 test_banner_mount.
"""

from __future__ import annotations

import re

import pytest
from django.test import override_settings
from django.utils.translation import activate

pytestmark = pytest.mark.django_db

# Staticka strana koja extend-uje base.html, BEZ DB fixtura (AboutView; mirror 7-2).
MOUNT_PAGE_SR = "/sr/o-nama/"

# TRACKER-SPECIFICNI tokeni (CRITICAL-3) — NIKAD bare `facebook`/`google`.
TRACKER_TOKENS = [
    "googletagmanager.com/gtag/js",
    "gtag(",
    "connect.facebook.net",
    "facebook.com/tr",
    "fbq(",
]


def _content(response) -> str:
    return response.content.decode("utf-8")


def _assert_no_tracker(html, where):
    found = [t for t in TRACKER_TOKENS if t in html]
    assert not found, (
        f"{where}: response NE sme sadrzati tracker-specificne tokene (CRITICAL-3 / "
        f"AC6 — NIJEDAN tracker pre consent-a). Pronadjeno: {found!r}"
    )


# AC6/G-4/CRITICAL-3: bez consent kolacica (ID set) → NEMA tracker-specificnih tokena
@override_settings(GA_MEASUREMENT_ID="G-TEST", FB_PIXEL_ID="123456")
def test_no_tracker_when_consent_absent(client):
    activate("sr")
    response = client.get(MOUNT_PAGE_SR)
    assert response.status_code == 200, (
        f"GET {MOUNT_PAGE_SR} MORA biti 200 (AboutView), dobio {response.status_code}."
    )
    _assert_no_tracker(_content(response), "bez consent kolacica (ID set)")


# AC6/G-2/CRITICAL-2/CRITICAL-3: malformed kolacic (garbage) → DEFAULT-DENY → NEMA tracker
@override_settings(GA_MEASUREMENT_ID="G-TEST", FB_PIXEL_ID="123456")
def test_malformed_cookie_no_tracker(client):
    activate("sr")
    client.cookies["consent_state"] = "garbage-not-json"
    response = client.get(MOUNT_PAGE_SR)
    assert response.status_code == 200, (
        f"Malformed kolacic NE sme 500 (G-2). Dobio {response.status_code}."
    )
    _assert_no_tracker(_content(response), "malformed kolacic (garbage)")


# AC6/CRITICAL-2/CRITICAL-3: off-tip truthy forged kolacic → DEFAULT-DENY → NEMA tracker
@override_settings(GA_MEASUREMENT_ID="G-TEST", FB_PIXEL_ID="123456")
def test_forged_truthy_cookie_no_tracker(client):
    activate("sr")
    client.cookies["consent_state"] = '{"analytical": "yes", "marketing": 1}'
    response = client.get(MOUNT_PAGE_SR)
    assert response.status_code == 200
    _assert_no_tracker(_content(response), "forged off-tip truthy kolacic")


# AC5/AC6/G-3/CRITICAL-3: consent kolacic ALI prazan ID (dev/test default) → NEMA tracker
def test_no_tracker_in_dev_default(client):
    # BEZ override_settings → GA_MEASUREMENT_ID/FB_PIXEL_ID prazni default → no-ID grana.
    activate("sr")
    client.cookies["consent_state"] = (
        '{"necessary": true, "analytical": true, "marketing": true}'
    )
    response = client.get(MOUNT_PAGE_SR)
    assert response.status_code == 200
    _assert_no_tracker(_content(response), "consent ALI prazan ID (dev default)")


# AC6/CRITICAL-1: posle analytical consent + ID → 200 + response SADRZI GA gtag (server-rendered)
@override_settings(GA_MEASUREMENT_ID="G-TEST")
def test_ga_loads_after_consent(client):
    activate("sr")
    client.cookies["consent_state"] = (
        '{"necessary": true, "analytical": true, "marketing": false}'
    )
    response = client.get(MOUNT_PAGE_SR)
    assert response.status_code == 200, (
        "Posle consent+ID render MORA biti 200, NE 500 (CRITICAL-1 — brace-heavy JS "
        f"kroz mark_safe, NE format_html format-string). Dobio {response.status_code}."
    )
    html = _content(response)
    assert "googletagmanager.com/gtag/js" in html, (
        "Posle analytical consent + GA_MEASUREMENT_ID -> response MORA sadrzati GA gtag "
        "script (page refresh activates pixel; epics.md:1035, server-rendered). "
        "Nedostaje gtag.js."
    )
    assert "function gtag(){dataLayer.push(arguments);}" in html, (
        "Render-ovan gtag snippet MORA imati LITERALNO brace-heavy telo (jednostruke "
        "`{`/`}`; CRITICAL-1). Nedostaje ili udvojeno."
    )


# AC6: posle marketing consent + ID → 200 + response sadrzi fbq( init
@override_settings(FB_PIXEL_ID="123456")
def test_fb_loads_after_marketing_consent(client):
    activate("sr")
    client.cookies["consent_state"] = (
        '{"necessary": true, "analytical": false, "marketing": true}'
    )
    response = client.get(MOUNT_PAGE_SR)
    assert response.status_code == 200
    html = _content(response)
    assert "fbq(" in html and "fbq('init', '123456')" in html, (
        "Posle marketing consent + FB_PIXEL_ID → response MORA sadrzati fbq init. "
        "Nedostaje fbq."
    )


# AC5/SM-D7: pixel-i mount-ovani UNUTAR <head> (consent+ID render → tracker u head sekciji)
@override_settings(GA_MEASUREMENT_ID="G-TEST", FB_PIXEL_ID="123456")
def test_pixels_mounted_in_head(client):
    activate("sr")
    client.cookies["consent_state"] = (
        '{"necessary": true, "analytical": true, "marketing": true}'
    )
    response = client.get(MOUNT_PAGE_SR)
    assert response.status_code == 200
    html = _content(response)
    head_match = re.search(r"<head\b.*?</head>", html, re.IGNORECASE | re.DOTALL)
    assert head_match, "base.html MORA imati <head>...</head>."
    head = head_match.group(0)
    assert "googletagmanager.com/gtag/js" in head, (
        "`{% ga_pixel %}` MORA biti mount-ovan UNUTAR <head> (SM-D7); gtag.js nije u head-u."
    )
    assert "fbq('init', '123456')" in head, (
        "`{% fb_pixel %}` MORA biti mount-ovan UNUTAR <head> (SM-D7); fbq init nije u head-u."
    )


# AC6/G-14: NIKAD out-of-gate resource hint ka tracker domenima (bez consent → <head> cist)
def test_no_out_of_gate_resource_hint(client):
    activate("sr")
    response = client.get(MOUNT_PAGE_SR)  # bez consent, prazan ID
    assert response.status_code == 200
    html = _content(response)
    head_match = re.search(r"<head\b.*?</head>", html, re.IGNORECASE | re.DOTALL)
    head = head_match.group(0) if head_match else html
    hints = re.findall(
        r'<link[^>]*rel=["\'](?:preconnect|dns-prefetch|preload)["\'][^>]*>',
        head,
        re.IGNORECASE,
    )
    offenders = [
        h
        for h in hints
        if re.search(
            r"googletagmanager|connect\.facebook|google-analytics|facebook\.net",
            h,
            re.IGNORECASE,
        )
    ]
    assert not offenders, (
        "G-14: NIKAD preconnect/dns-prefetch/preload ka tracker domenima u <head> "
        "izvan consent-gated tag izlaza (otvorio bi mreznu konekciju pre consent-a). "
        f"Pronadjeno: {offenders!r}"
    )
