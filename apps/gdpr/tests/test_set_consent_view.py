"""Story 7.2 — AC2/AC3/AC4/AC5: `SetConsentView` (TEA RED phase).

Pokriva AC2-AC5 + SM-D1/D3/D5/D6/D7/D9 + Gotcha G-2..G-6b/G-12/G-15:
- accept_all → {necessary,analytical,marketing} svi True; reject_all → samo
  necessary; save per-checkbox; save bez checkbox-a → default-deny.
- `necessary` SERVER-FORCED True (NE čita iz POST-a; G-3) — čak i kad POST
  pokuša `necessary=false`.
- nepoznata/nedostajuća `action` → default-deny (NE crash/KeyError; G-15).
- kolačić atributi: max_age==60*60*24*365, samesite=="Lax", path=="/",
  httponly==False, secure==settings.SESSION_COOKIE_SECURE (SM-D5).
- 303 redirect-back na same-origin `next`; open-redirect blokiran (G-5/SM-D9);
  bez next/referer → fallback reverse("pages:home").
- GET → 405 (G-12); POST bez CSRF (enforce_csrf_checks) → 403 (G-2/CRITICAL-1).
- ratelimit: 11. POST u minuti → 429 (NE 403; G-6/G-6b/CRITICAL-2) — REALNO
  okida limit (NE samo proverava dekorator); cache.clear() preko autouse fixture.

RED razlog: `SetConsentView` + url `gdpr:set_consent` NE postoje →
NoReverseMatch / 404 → asercije padaju.

⚠️ COLLECTION-SAFETY: reverse/URL literalno + importi UNUTAR funkcija.

Pokrenuti:
    docker compose -f compose/local.yml run --rm django \
        uv run pytest apps/gdpr/tests/test_set_consent_view.py -v

Refs: 7-2 AC2-AC5 + SM-D1/D3/D5/D6/D7/D9 + Gotcha G-2..G-6b/G-12/G-15;
7-2-interface-contract § 2 (SetConsentView) + § 3 (URL).
"""

from __future__ import annotations

import json

import pytest
from django.conf import settings
from django.urls import reverse
from django.utils.translation import override

from .conftest import SET_CONSENT_PATH_SR

pytestmark = pytest.mark.django_db

CONSENT_MAX_AGE = 60 * 60 * 24 * 365  # 365 dana (SM-D1)


def _consent_url():
    with override("sr"):
        return reverse("gdpr:set_consent")


def _cookie_json(response):
    """Parsiraj `consent_state` kolačić sa response-a u dict (FAIL ako odsutan)."""
    assert "consent_state" in response.cookies, (
        "Response MORA postaviti `consent_state` kolačić (AC2/SM-D3). "
        f"Cookies: {list(response.cookies.keys())!r}"
    )
    return json.loads(response.cookies["consent_state"].value)


# AC2: POST accept_all → kolačić {necessary,analytical,marketing} svi True
def test_accept_all_sets_all_true(client):
    response = client.post(_consent_url(), {"action": "accept_all"})
    consent = _cookie_json(response)
    assert consent == {"necessary": True, "analytical": True, "marketing": True}, (
        f"accept_all MORA dati sve True (AC2), dobio {consent!r}."
    )


# AC3: POST reject_all → samo necessary True (default-deny)
def test_reject_all_only_necessary(client):
    response = client.post(_consent_url(), {"action": "reject_all"})
    consent = _cookie_json(response)
    assert consent == {"necessary": True, "analytical": False, "marketing": False}, (
        f"reject_all MORA dati samo necessary=True (default-deny; AC3), dobio {consent!r}."
    )


# AC3: POST save SA analytical (bez marketing) → per-checkbox
def test_save_per_category(client):
    response = client.post(
        _consent_url(), {"action": "save", "analytical": "on"}
    )
    consent = _cookie_json(response)
    assert consent == {"necessary": True, "analytical": True, "marketing": False}, (
        "save MORA reflektovati prisustvo checkbox imena u request.POST "
        f"(`\"analytical\" in request.POST`; AC3), dobio {consent!r}."
    )


# AC3/OQ-4: POST save BEZ ijednog checkbox-a → default-deny (== reject_all stanje)
def test_save_no_checkboxes_default_deny(client):
    response = client.post(_consent_url(), {"action": "save"})
    consent = _cookie_json(response)
    assert consent == {"necessary": True, "analytical": False, "marketing": False}, (
        f"save bez checkbox-a MORA dati samo necessary=True (OQ-4/AC3), dobio {consent!r}."
    )


# AC3/G-3: necessary je UVEK True (SERVER-FORCED) — čak i kad POST pokuša necessary=false
def test_necessary_always_true_even_when_post_tampers(client):
    # reject_all + pokušaj da se „necessary" iskljuci kroz POST → server ignoriše
    response = client.post(
        _consent_url(), {"action": "reject_all", "necessary": "false"}
    )
    consent = _cookie_json(response)
    assert consent["necessary"] is True, (
        "necessary MORA biti SERVER-FORCED True — NE čita se iz POST-a (G-3). "
        f"POST je pokusao necessary=false ali server forsira True. Dobio {consent!r}."
    )


# AC3/G-3: čak i accept sa POST necessary=false → necessary ostaje True (tamper guard)
def test_necessary_forced_true_on_accept_tamper(client):
    response = client.post(
        _consent_url(), {"action": "accept_all", "necessary": "false"}
    )
    consent = _cookie_json(response)
    assert consent["necessary"] is True, (
        "Tamper-otporno: server UVEK forsira necessary=True bez obzira na POST (G-3). "
        f"Dobio {consent!r}."
    )


# AC3/G-15: nepoznata `action` → default-deny (NE crash, NE accept-all)
def test_unknown_action_default_deny(client):
    response = client.post(_consent_url(), {"action": "garbage-action-value"})
    assert response.status_code in (302, 303), (
        "Nepoznata `action` NE SME crash-ovati (500/KeyError) — default-deny + redirect "
        f"(G-15), dobio {response.status_code}."
    )
    consent = _cookie_json(response)
    assert consent == {"necessary": True, "analytical": False, "marketing": False}, (
        f"Nepoznata `action` → default-deny (kao reject_all; G-15), dobio {consent!r}."
    )


# AC3/G-15: nedostajuća `action` → default-deny (NE KeyError)
def test_missing_action_default_deny(client):
    response = client.post(_consent_url(), {})  # bez `action` polja
    assert response.status_code in (302, 303), (
        "Nedostajuća `action` NE SME crash-ovati (KeyError) — default-deny + redirect "
        f"(G-15), dobio {response.status_code}."
    )
    consent = _cookie_json(response)
    assert consent == {"necessary": True, "analytical": False, "marketing": False}, (
        f"Nedostajuća `action` → default-deny (G-15), dobio {consent!r}."
    )


# AC2/SM-D5: kolačić atributi (max_age, samesite, path, httponly, secure)
def test_cookie_attributes(client):
    response = client.post(_consent_url(), {"action": "accept_all"})
    morsel = response.cookies["consent_state"]

    assert int(morsel["max-age"]) == CONSENT_MAX_AGE, (
        f"max_age MORA biti {CONSENT_MAX_AGE} (365 dana; SM-D1/AC2), dobio {morsel['max-age']!r}."
    )
    assert str(morsel["samesite"]).lower() == "lax", (
        f"SameSite MORA biti Lax (SM-D5), dobio {morsel['samesite']!r}."
    )
    assert morsel["path"] == "/", (
        f"path MORA biti '/' (site-wide; SM-D5), dobio {morsel['path']!r}."
    )
    # httponly=False (SM-D5 — buduca client-side manage-consent re-open OQ-2).
    # Django Morsel: httponly atribut je prazan/odsutan kad httponly=False.
    assert not morsel["httponly"], (
        "httponly MORA biti False (SM-D5 — consent NIJE sensitive PII; buduce "
        f"client-side citanje OQ-2). Dobio httponly={morsel['httponly']!r}."
    )
    # secure prati settings.SESSION_COOKIE_SECURE (False u dev/test, True u prod).
    expected_secure = bool(getattr(settings, "SESSION_COOKIE_SECURE", False))
    actual_secure = bool(morsel["secure"])
    assert actual_secure == expected_secure, (
        "secure MORA pratiti settings.SESSION_COOKIE_SECURE (settings-driven; SM-D5). "
        f"settings={expected_secure!r}, kolačić secure={actual_secure!r}."
    )


# AC2/SM-D3: response je 303 redirect (POST→GET semantika)
def test_post_returns_303_redirect(client):
    response = client.post(_consent_url(), {"action": "accept_all"})
    assert response.status_code == 303, (
        "POST MORA vratiti HTTP 303 See Other (POST→GET redirect-back semantika; "
        f"SM-D3), dobio {response.status_code}."
    )


# AC4: redirect-back na same-origin `next`
def test_redirect_back_same_origin(client):
    response = client.post(
        _consent_url(), {"action": "accept_all", "next": "/sr/proizvodi/"}
    )
    assert response.status_code in (302, 303)
    assert response["Location"] == "/sr/proizvodi/", (
        "POST sa same-origin `next` MORA redirektovati na taj path (AC4/SM-D9), "
        f"dobio Location={response.get('Location')!r}."
    )
    # kolačić se i dalje postavlja na redirect response-u
    assert "consent_state" in response.cookies, (
        "Kolačić MORA biti postavljen na redirect response-u (AC4)."
    )


# AC4/G-5/SM-D9: OPEN-REDIRECT — next=https://evil.com → NE redirektuje na evil.com
def test_redirect_open_redirect_blocked(client):
    response = client.post(
        _consent_url(),
        {"action": "accept_all", "next": "https://evil.com/"},
        HTTP_HOST="testserver",
    )
    assert response.status_code in (302, 303)
    location = response["Location"]
    assert "evil.com" not in location, (
        "OPEN-REDIRECT: cross-origin `next` MORA biti odbijen (url_has_allowed_host_"
        "and_scheme guard; G-5/SM-D9) → fallback referer/pages:home, NIKAD evil.com. "
        f"Dobio Location={location!r}."
    )


# AC4/G-5: scheme-relative //evil.com takođe odbijen
def test_redirect_scheme_relative_blocked(client):
    response = client.post(
        _consent_url(),
        {"action": "accept_all", "next": "//evil.com/"},
        HTTP_HOST="testserver",
    )
    assert response.status_code in (302, 303)
    assert "evil.com" not in response["Location"], (
        "Scheme-relative `//evil.com` MORA biti odbijen (G-5/SM-D9), "
        f"dobio Location={response['Location']!r}."
    )


# AC4: bez next i bez referer → fallback reverse("pages:home")
def test_redirect_no_next_fallback_home(client):
    response = client.post(_consent_url(), {"action": "accept_all"})
    assert response.status_code in (302, 303)
    with override("sr"):
        home = reverse("pages:home")
    assert response["Location"] == home, (
        "POST bez `next` i bez referer-a MORA redirektovati na reverse('pages:home') "
        f"(AC4/SM-D9), dobio Location={response['Location']!r} (ocekivano {home!r})."
    )


# AC4/G-12: GET na set_consent → 405 (POST-only)
def test_get_returns_405(client):
    response = client.get(_consent_url())
    assert response.status_code == 405, (
        "SetConsentView je POST-only (http_method_names=['post']) → GET MORA biti 405 "
        f"(sprecava da link/prefetch postavi consent; G-12), dobio {response.status_code}."
    )


# AC4/G-2/CRITICAL-1: POST bez CSRF tokena (enforce_csrf_checks) → 403
def test_post_without_csrf_403(csrf_client):
    # csrf_client = Client(enforce_csrf_checks=True) — default `client` ISKLJUCUJE
    # CSRF i dao bi LAZNO-zeleno (CRITICAL-1). Bez `{% csrf_token %}` → 403.
    response = csrf_client.post(_consent_url(), {"action": "accept_all"})
    assert response.status_code == 403, (
        "POST bez CSRF tokena (Client(enforce_csrf_checks=True)) MORA biti 403 — "
        "dokaz da CsrfViewMiddleware + `{% csrf_token %}` stite endpoint (G-2/CRITICAL-1). "
        f"Dobio {response.status_code}."
    )


# AC4/G-6/G-6b/CRITICAL-2: 11. POST u minuti → 429 (NE 403) — REALNO okida limit
# Nema @override_settings(CACHES=...) — base.py vec konfiguriše locmem; override bi
# stvorio NOVI cache objekat koji autouse cache.clear() (conftest) NE bi ocistio,
# sto uzrokuje flakiness u full-suite run-u (brojac curi izmedju fixture instances).
# Autouse `_pin_and_clear_ratelimit_cache` + unique IP (REMOTE_ADDR="203.0.113.77")
# daju deterministicnu 10-ok/11-ti-429 granicu bez @override_settings.
def test_ratelimit_429_after_limit(client):
    # cache.clear() dolazi iz autouse `_pin_and_clear_ratelimit_cache` (conftest) →
    # deterministicna 10-ok/11-ti-429 granica, brojač NE curi između testova.
    url = _consent_url()
    statuses = [
        client.post(
            url, {"action": "accept_all"}, REMOTE_ADDR="203.0.113.77"
        ).status_code
        for _ in range(11)
    ]
    assert statuses[-1] == 429, (
        "rate=10/m: 11. POST sa istog IP-a u 1 min MORA biti 429 (block=False + "
        "request.limited → HttpResponse(status=429); G-6). Test REALNO okida limit "
        "(NE samo proverava dekorator) → hvata silent no-op ako `@ratelimit` nije "
        "vezan kroz `@method_decorator(..., name='dispatch')` na CBV (G-6b/CRITICAL-2). "
        f"Dobio statuse {statuses!r}."
    )
    assert 403 not in statuses, (
        "NIJEDAN POST NE SME vratiti 403 — to znaci block=True umesto block=False (G-6). "
        f"Dobio statuse {statuses!r}."
    )


# AC5: reverse("gdpr:set_consent") == /sr/htmx/gdpr/consent/
def test_set_consent_url_reverse():
    with override("sr"):
        url = reverse("gdpr:set_consent")
    assert url == SET_CONSENT_PATH_SR, (
        f"reverse('gdpr:set_consent') pod sr MORA biti {SET_CONSENT_PATH_SR!r} "
        f"(i18n_patterns + htmx/ ASCII prefiks; SM-D6/AC5), dobio {url!r}."
    )


# AC5/G-11: consent slug je ASCII (NEMA dijakritika u URL-u)
def test_consent_slug_is_ascii():
    with override("sr"):
        url = reverse("gdpr:set_consent")
    assert url.isascii(), (
        f"consent URL MORA biti ASCII (slug konvencija; G-11), dobio {url!r}."
    )
