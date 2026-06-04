"""Story 4.6 — REGRESSION-LOCK endpoint contract (TEA, Task 1.2).

═══════════════════════════════════════════════════════════════════════════════
REGRESSION-LOCK (must pass BEFORE AND AFTER the 4.6 refactor).
═══════════════════════════════════════════════════════════════════════════════

4.6 je BEHAVIOR-PRESERVING standardizacija zajedničke HTMX-form mašinerije
(ratelimit→429 prefiks → dekorator; OOB aria-live blok → `{% include %}`; rate →
konstanta). Ovaj modul je ZLATNA MREŽA: konsoliduje rasute aria/ratelimit asercije
preko sva 4 endpointa (`contact_submit`, `model_inquiry_submit`,
`service_request_submit`, `part_request_submit`) u jedan tabelarni lock invarijanti
koje refaktor MORA očuvati. Ako ijedan padne POSLE refaktora → refaktor je promenio
posmatrano ponašanje (regresija).

Pokriveni invarijanti (AC1/AC2/AC4/AC5; Task 1.2 a-h):
- (a) GET → 405 (`@require_POST` najspoljašnjiji);
- (b) 6. POST istog IP-a → 429, NIKAD 403 (block=False + request.limited);
- (c) success → 200 + TAČAN per-forma OOB success marker u
  `hx-swap-oob="innerHTML:#aria-live"`;
- (d) error → 200 + in-form role="alert" aria-live="assertive" (regija #1) + OOB
  (regija #2) sa „Greška pri slanju, proverite polja.";
- (e) non-HTMX POST → NEMA `hx-swap-oob`;
- (f) 405-pre-429 precedencija: GET kad je IP VEĆ limitovan i dalje 405;
- (g) GET NE troši rate budžet: 5× GET (svaki 405) PA validan POST → 200, NIJE 429;
- (h) (= b) 6. POST → 429, NIKAD 403.

KRITIČNO (model_inquiry divergencija): model_inquiry zadržava tro-ishodni OOB
(product_not_found / form.errors / ništa). Ovde se lockuje i product_not_found
OOB najava „Proizvod nije pronađen." (regija #2) da refaktor ne sme nečujno da je
izbriše (dopuna `test_model_inquiry_aria_live.test_product_not_found_has_both_aria_regions`).

Refs: 4-6 AC1/AC2/AC4/AC5 + Task 1.2 (a-h); 4-6-interface-contract § 1.
"""

from __future__ import annotations

import re

import pytest

pytestmark = pytest.mark.django_db

# Cache pinning + clear (locmem, 5-ok/6-ti-429 determinizam) dolazi iz autouse
# `_pin_and_clear_ratelimit_cache` fixture-a u conftest.py — NE duplirati ovde.

# Per-forma OOB success marker (TAČAN string iz *_success.html — verifikovano
# protiv templates/forms/partials/*_success.html). Asertujemo EKSAKTNO da refaktor
# koji zameni poruke MEĐU formama bude uhvaćen.
SUCCESS_OOB = {
    "contact": "Upit je poslat.",
    "model_inquiry": "Upit za model je poslat.",
    "service": "Servisni zahtev je poslat.",
    "part_request": "Upit za rezervni deo je poslat.",
}
ERROR_OOB = "Greška pri slanju, proverite polja."


def _build_case(request, key):
    """Resolve per-forma (url, valid_payload, invalid_payload) za dati endpoint.

    Vraća payload-e tek pošto su fixtures rešeni — model_inquiry/part_request
    zahtevaju produkt/dodatna polja. Vraćeni `valid_payload` je validan submit;
    `invalid_payload` forsira form.errors (prazno obavezno polje).
    """
    if key == "contact":
        url = request.getfixturevalue("contact_submit_url")
        valid = request.getfixturevalue("valid_contact_payload")
    elif key == "model_inquiry":
        url = request.getfixturevalue("model_inquiry_submit_url")
        product = request.getfixturevalue("published_product")
        base = request.getfixturevalue("model_inquiry_payload")
        valid = {**base, "product_slug": product.slug}
    elif key == "service":
        url = request.getfixturevalue("service_request_submit_url")
        valid = request.getfixturevalue("service_request_payload")
    elif key == "part_request":
        url = request.getfixturevalue("part_request_submit_url")
        valid = request.getfixturevalue("part_request_payload")
    else:  # pragma: no cover - guard
        raise AssertionError(f"Nepoznat endpoint key: {key}")
    invalid = {**valid, "name": ""}  # prazno obavezno `name` → form.errors svuda
    return url, valid, invalid


ENDPOINTS = ["contact", "model_inquiry", "service", "part_request"]


# ── (a) GET → 405 (require_POST) ──────────────────────────────────────────────
@pytest.mark.parametrize("key", ENDPOINTS)
def test_get_returns_405(request, client, recipient_env, key):
    """REGRESSION-LOCK: GET na submit endpoint → 405 (require_POST najspoljašnjiji)."""
    url, _valid, _invalid = _build_case(request, key)
    response = client.get(url, REMOTE_ADDR="203.0.113.40")
    assert response.status_code == 405, (
        f"[{key}] GET MORA biti 405 (@require_POST), dobio {response.status_code}."
    )


# ── (b)/(h) 6. POST istog IP-a → 429, NIKAD 403 ───────────────────────────────
@pytest.mark.parametrize("key", ENDPOINTS)
def test_sixth_post_returns_429_never_403(
    request, htmx_post, recipient_env, mailoutbox, key
):
    """REGRESSION-LOCK: 6. POST istog IP-a → 429 (block=False), NIJEDAN 403."""
    url, valid, _invalid = _build_case(request, key)
    statuses = [
        htmx_post(url, valid, ip="198.51.100.66").status_code for _ in range(6)
    ]
    assert statuses[-1] == 429, (
        f"[{key}] 6. POST istog IP-a MORA biti 429 (block=False + request.limited), "
        f"dobio statuse {statuses!r}."
    )
    assert 403 not in statuses, (
        f"[{key}] NIJEDAN POST NE SME biti 403 (to bi značilo block=True). "
        f"Statusi: {statuses!r}."
    )


# ── (c) success → 200 + TAČAN per-forma OOB success marker ─────────────────────
@pytest.mark.parametrize("key", ENDPOINTS)
def test_success_has_exact_per_form_oob_marker(
    request, htmx_post, recipient_env, mailoutbox, key
):
    """REGRESSION-LOCK: success → 200 + EKSAKTAN per-forma OOB success string."""
    url, valid, _invalid = _build_case(request, key)
    response = htmx_post(url, valid, ip="198.51.100.10")
    assert response.status_code == 200, (
        f"[{key}] success POST MORA biti 200, dobio {response.status_code}."
    )
    html = response.content.decode("utf-8")
    assert 'hx-swap-oob="innerHTML:#aria-live"' in html, (
        f"[{key}] success MORA imati OOB `hx-swap-oob=\"innerHTML:#aria-live\"` (regija #2)."
    )
    expected = SUCCESS_OOB[key]
    assert expected in html, (
        f"[{key}] success OOB marker MORA biti TAČNO „{expected}” (pun dijakritik). "
        f"Sadržaj: {html[:400]}"
    )
    # Marker MORA biti UNUTAR OOB bloka (ne slučajno drugde u telu).
    oob = re.search(
        r'<[^>]*hx-swap-oob="innerHTML:#aria-live"[^>]*>(.*?)</',
        html,
        re.IGNORECASE | re.DOTALL,
    )
    assert oob and expected in oob.group(1), (
        f"[{key}] success OOB blok MORA SADRŽATI „{expected}”. OOB: "
        f"{oob.group(1) if oob else None!r}"
    )


# ── (d) error → 200 + OBE a11y regije + error OOB ─────────────────────────────
@pytest.mark.parametrize("key", ENDPOINTS)
def test_error_has_both_aria_regions(
    request, htmx_post, recipient_env, mailoutbox, key
):
    """REGRESSION-LOCK: error → 200 + in-form assertive (regija #1) + OOB error (regija #2)."""
    url, _valid, invalid = _build_case(request, key)
    response = htmx_post(url, invalid, ip="198.51.100.11")
    assert response.status_code == 200, (
        f"[{key}] error POST MORA biti 200 (re-render forme), dobio {response.status_code}."
    )
    html = response.content.decode("utf-8")
    assert 'role="alert"' in html and 'aria-live="assertive"' in html, (
        f"[{key}] error MORA imati in-form role=\"alert\" + aria-live=\"assertive\" (regija #1)."
    )
    assert 'hx-swap-oob="innerHTML:#aria-live"' in html, (
        f"[{key}] error MORA imati ODVOJEN OOB (regija #2)."
    )
    assert ERROR_OOB in html, (
        f"[{key}] error OOB najava MORA biti TAČNO „{ERROR_OOB}” (pun dijakritik š)."
    )
    oob = re.search(
        r'<[^>]*hx-swap-oob="innerHTML:#aria-live"[^>]*>(.*?)</',
        html,
        re.IGNORECASE | re.DOTALL,
    )
    assert oob and ERROR_OOB in oob.group(1), (
        f"[{key}] error OOB blok MORA SADRŽATI „{ERROR_OOB}”. OOB: "
        f"{oob.group(1) if oob else None!r}"
    )


# ── (e) non-HTMX POST → NEMA hx-swap-oob ──────────────────────────────────────
@pytest.mark.parametrize("key", ENDPOINTS)
def test_non_htmx_post_has_no_oob(request, client, recipient_env, mailoutbox, key):
    """REGRESSION-LOCK: non-HTMX POST (bez HX-Request) → guard isključen → NEMA OOB."""
    url, valid, _invalid = _build_case(request, key)
    response = client.post(url, valid, REMOTE_ADDR="203.0.113.41")
    html = response.content.decode("utf-8")
    assert "hx-swap-oob" not in html, (
        f"[{key}] non-HTMX POST NE SME sadržati OOB div (guard {{% if request.htmx %}} "
        f"isključuje OOB kad request.htmx False — sprečava plain-text leak)."
    )


# ── (f) 405-pre-429 precedencija: GET kad je IP VEĆ limitovan i dalje 405 ──────
@pytest.mark.parametrize("key", ENDPOINTS)
def test_get_still_405_when_ip_already_rate_limited(
    request, client, htmx_post, recipient_env, mailoutbox, key
):
    """REGRESSION-LOCK: require_POST je SPOLJAŠNJI → GET vraća 405 PRE nego ratelimit
    wrapper odluči o 429, čak i kad je IP već potrošio kvotu sa POST-ovima.
    """
    url, valid, _invalid = _build_case(request, key)
    ip = "198.51.100.77"
    # Iscrpi kvotu sa 6 POST-ova (poslednji već 429).
    for _ in range(6):
        htmx_post(url, valid, ip=ip)
    # GET sa istog (limitovanog) IP-a → i dalje 405, NE 429.
    response = client.get(url, REMOTE_ADDR=ip)
    assert response.status_code == 405, (
        f"[{key}] GET na rate-limitovanom IP-u MORA i dalje biti 405 (require_POST "
        f"SPOLJAŠNJI — 405 pre 429), dobio {response.status_code}."
    )


# ── (g) GET NE troši rate budžet: 5× GET (405) PA validan POST → 200, NIJE 429 ─
@pytest.mark.parametrize("key", ENDPOINTS)
def test_get_does_not_consume_rate_budget(
    request, client, htmx_post, recipient_env, mailoutbox, key
):
    """REGRESSION-LOCK (CRITICAL-3): require_POST kratko-spaja GET PRE nego
    django_ratelimit pozove `is_ratelimited(increment=True)` → GET NE inkrementira
    5/m brojač. 5× GET (svaki 405) zatim validan POST mora proći (200, NIJE 429).
    """
    url, valid, _invalid = _build_case(request, key)
    ip = "198.51.100.88"
    for _ in range(5):
        get_resp = client.get(url, REMOTE_ADDR=ip)
        assert get_resp.status_code == 405, (
            f"[{key}] GET MORA biti 405 (require_POST), dobio {get_resp.status_code}."
        )
    response = htmx_post(url, valid, ip=ip)
    assert response.status_code == 200, (
        f"[{key}] validan POST POSLE 5× GET MORA biti 200, NE 429 — dokaz da GET NE "
        f"troši rate budžet. Dobio {response.status_code}."
    )


# ── (model_inquiry divergencija) product_not_found OOB lock ───────────────────
def test_model_inquiry_product_not_found_oob_preserved(
    htmx_post, model_inquiry_submit_url, model_inquiry_payload, recipient_env, mailoutbox
):
    """REGRESSION-LOCK (model_inquiry IZUZETAK): valid forma + nepostojeći slug →
    tro-ishodni OOB grana product_not_found fire-uje „Proizvod nije pronađen." u OOB
    regiji (regija #2). Refaktor NE SME naivno izravnati na dvo-ishodni guard (to bi
    nečujno izbrisalo ovu najavu). Dopuna postojećeg
    `test_product_not_found_has_both_aria_regions`.
    """
    payload = {**model_inquiry_payload, "product_slug": "ne-postoji-nikako-4-6"}
    response = htmx_post(model_inquiry_submit_url, payload, ip="198.51.100.12")
    assert response.status_code == 200
    html = response.content.decode("utf-8")
    oob = re.search(
        r'<[^>]*hx-swap-oob="innerHTML:#aria-live"[^>]*>(.*?)</',
        html,
        re.IGNORECASE | re.DOTALL,
    )
    assert oob and "Proizvod nije pronađen." in oob.group(1), (
        "model_inquiry product_not_found OOB MORA sadržati „Proizvod nije pronađen.” "
        f"(pun dijakritik đ). OOB: {oob.group(1) if oob else None!r}"
    )


def test_model_inquiry_error_oob_is_field_error_message(
    htmx_post, model_inquiry_submit_url, model_inquiry_payload, published_product,
    recipient_env, mailoutbox,
):
    """REGRESSION-LOCK (model_inquiry IZUZETAK): invalid forma (validan slug, prazno
    `name`) → form.errors grana OOB → „Greška pri slanju, proverite polja." (NE
    product_not_found). Dokazuje da tro-ishodni guard razlikuje dva error ishoda.
    """
    payload = {**model_inquiry_payload, "name": "", "product_slug": published_product.slug}
    response = htmx_post(model_inquiry_submit_url, payload, ip="198.51.100.13")
    html = response.content.decode("utf-8")
    oob = re.search(
        r'<[^>]*hx-swap-oob="innerHTML:#aria-live"[^>]*>(.*?)</',
        html,
        re.IGNORECASE | re.DOTALL,
    )
    assert oob and "Greška pri slanju, proverite polja." in oob.group(1), (
        "model_inquiry form.errors OOB MORA biti „Greška pri slanju, proverite polja.”, "
        f"NE product_not_found. OOB: {oob.group(1) if oob else None!r}"
    )
    assert "Proizvod nije pronađen." not in oob.group(1), (
        "form.errors ishod NE SME emitovati „Proizvod nije pronađen.” u OOB regiji."
    )
