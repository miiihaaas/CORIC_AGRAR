"""Story 7.2 — AC9: base.html mount + no-tracker (TEA RED phase, integration).

Pokriva AC9 + SM-D8/D12 + Gotcha G-7/G-10:
- `{% gdpr_banner %}` mount-ovan u base.html → SVAKA strana koja extend-uje
  base.html prikazuje baner kad `consent_state` kolačić ODSUTAN; NE kad prisutan.
- 7-2 NE ucitava NIJEDAN tracker (response NE sadrzi gtag/fbq/google-analytics/
  googletagmanager/facebook) — tracking je 7-3 (G-10, security granica).
- gdpr-banner.js je EKSTERNI <script src=... defer> u base.html (NE inline; G-7).

INTEGRACIJSKI STRANICA: koristi `/sr/o-nama/` (AboutView — cista staticka
TemplateView BEZ DB fixtura/heavy konteksta) da dokaze site-wide mount BEZ
potrebe za seed-om proizvoda/brendova (home `/sr/` zahteva domain fixtures).
Cilj je dokazati mount, NE render home-a.

RED razlog: base.html JOS NE mount-uje `{% gdpr_banner %}` (tag ne postoji →
TemplateSyntaxError ce pasti cim Dev doda `{% load gdpr_banner %}`; do tada
baner markup prosto NIJE u response-u → asercija prisustva pada).

Pokrenuti:
    docker compose -f compose/local.yml run --rm django \
        uv run pytest apps/gdpr/tests/test_banner_mount.py -v

Refs: 7-2 AC9 + SM-D8/D12 + Gotcha G-7/G-10; 7-2-interface-contract § 6 (mount).
"""

from __future__ import annotations

import re

import pytest
from django.utils.translation import activate

pytestmark = pytest.mark.django_db

# Lagana staticka strana koja extend-uje base.html (AboutView — bez DB fixtura).
MOUNT_PAGE_SR = "/sr/o-nama/"

# Tracker reference koje 7-2 NIKAD ne sme uvesti (security granica; G-10).
TRACKER_SIGNATURES = [
    "googletagmanager",
    "google-analytics",
    "gtag(",
    "fbq(",
    "facebook.net",
    "connect.facebook",
]


# AC9: GET strana BEZ consent kolačića → response sadrzi baner (role="dialog")
def test_banner_visible_on_any_page_when_cookie_absent(client):
    activate("sr")
    response = client.get(MOUNT_PAGE_SR)
    assert response.status_code == 200, (
        f"GET {MOUNT_PAGE_SR} MORA biti 200 (AboutView staticka strana), "
        f"dobio {response.status_code}."
    )
    html = response.content.decode("utf-8")
    assert 'role="dialog"' in html and "data-coric-gdpr-banner" in html, (
        "Strana koja extend-uje base.html MORA prikazati GDPR baner kad `consent_state` "
        "kolačić ODSUTAN — `{% gdpr_banner %}` mount-ovan u base.html (AC9/SM-D12). "
        "Baner markup nije u response-u."
    )


# AC9/AC1: GET strana SA consent kolačićem → response NE sadrzi baner
def test_banner_absent_when_cookie_present(client):
    activate("sr")
    client.cookies["consent_state"] = (
        '{"necessary": true, "analytical": false, "marketing": false}'
    )
    response = client.get(MOUNT_PAGE_SR)
    assert response.status_code == 200
    html = response.content.decode("utf-8")
    assert "data-coric-gdpr-banner" not in html, (
        "Kad je `consent_state` kolačić PRISUTAN, baner NE SME biti renderovan "
        "(`{% gdpr_banner %}` vraca \"\"; AC1/AC9). Baner markup je u response-u."
    )


# AC9/G-10: 7-2 NE ucitava NIJEDAN tracker (security granica — tracking je 7-3)
def test_no_tracker_loaded_by_72(client):
    activate("sr")
    response = client.get(MOUNT_PAGE_SR)
    assert response.status_code == 200
    html = response.content.decode("utf-8").lower()
    found = [sig for sig in TRACKER_SIGNATURES if sig.lower() in html]
    assert not found, (
        "7-2 NE SME uvesti NIJEDAN tracker (GA4/FB pixel) — to je 7-3 (security "
        f"granica; G-10/SM-D8). Pronadjene tracker reference: {found!r}."
    )


# AC9/G-7: gdpr-banner.js je EKSTERNI <script src=... defer> (NE inline)
def test_gdpr_banner_js_external_script_present(client):
    activate("sr")
    response = client.get(MOUNT_PAGE_SR)
    assert response.status_code == 200
    html = response.content.decode("utf-8")
    m = re.search(
        r'<script[^>]*src=["\'][^"\']*gdpr-banner\.js["\'][^>]*>', html, re.IGNORECASE
    )
    assert m, (
        "base.html MORA ucitati gdpr-banner.js kao EKSTERNI <script src=...> "
        "(NE inline; G-7/SM-D10). Dobio: nijedan gdpr-banner.js script tag."
    )
    assert "defer" in m.group(0).lower(), (
        "gdpr-banner.js MORA biti ucitan sa `defer` (mirror sticky-nav.js; SM-D12). "
        f"Dobio: {m.group(0)!r}"
    )
