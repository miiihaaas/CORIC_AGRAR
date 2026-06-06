"""Story 7.3 — AC1: `consent_state(request)` context_processor (TEA RED phase).

Pokriva AC1 + SM-D1/D2/D10 + Gotcha G-2 + Boundary 7-2↔7-3:
- NOVI `apps/gdpr/context_processors.py:consent_state(request)` cita
  `request.COOKIES.get("consent_state")`, `json.loads` u try/except → vraca
  `{"consent_state": {"necessary": True, "analytical": bool, "marketing": bool}}`.
- DEFAULT-DENY na ODSUTAN / MALFORMED / NE-dict / NEDOSTAJUCI-kljuc kolacic;
  NIKAD crash, NIKAD default-allow.
- STRIKTAN `is True` (CRITICAL-2/SM-D10): SAMO pravi JSON `true` prolazi; off-tip
  truthy (`"yes"`/`1`/`"true"`-string) → False (forged → DENY).
- `necessary` UVEK True (server-forced).
- vraceni dict je dict-key-lookupabilan u template-u (`{{ consent_state.analytical }}`).

RED razlog: `apps/gdpr/context_processors.py` NE postoji → import UNUTAR test
funkcija baca ImportError/ModuleNotFoundError (per-test FAIL, NE collection-abort).

⚠️ COLLECTION-SAFETY: import `consent_state` je UNUTAR svake test funkcije (lazy).

Pokrenuti:
    docker compose -f compose/local.yml run --rm django \
        uv run pytest apps/gdpr/tests/test_consent_state_context_processor.py -v

Refs: 7-3 AC1 + SM-D1/D2/D10 + Gotcha G-2; 7-3-interface-contract § context_processor.
"""

from __future__ import annotations

import pytest
from django.template import Context, Template
from django.test import RequestFactory

# context_processor unit testovi NE traze DB (cist parse RequestFactory request-a).

DENY = {"necessary": True, "analytical": False, "marketing": False}


def _run(cookie_value=None):
    """Pozovi consent_state(request) sa (opcionim) `consent_state` kolacicem.

    Vraca SIROV context dict koji context_processor vrati (`{"consent_state": ...}`).
    """
    from apps.gdpr.context_processors import consent_state

    request = RequestFactory().get("/sr/")
    if cookie_value is not None:
        request.COOKIES["consent_state"] = cookie_value
    return consent_state(request)


# AC1: kolacic ODSUTAN → DEFAULT-DENY {"consent_state": {nec:True, an:False, mk:False}}
def test_absent_cookie_default_deny():
    result = _run(cookie_value=None)
    assert result == {"consent_state": DENY}, (
        "Kad `consent_state` kolacic ODSUTAN, context_processor MORA vratiti pun "
        f"DEFAULT-DENY (necessary True, analytical/marketing False; AC1). Dobio: {result!r}"
    )


# AC1: validan JSON {analytical:true, marketing:false} → analytical is True, marketing is False
def test_valid_cookie_analytical_true():
    result = _run('{"necessary": true, "analytical": true, "marketing": false}')
    cs = result["consent_state"]
    assert cs["analytical"] is True, (
        f"Pravi JSON `analytical:true` MORA dati `analytical is True`. Dobio: {cs!r}"
    )
    assert cs["marketing"] is False, (
        f"`marketing:false` MORA dati `marketing is False`. Dobio: {cs!r}"
    )


# AC1: validan JSON sa marketing:true → marketing is True
def test_valid_cookie_marketing_true():
    result = _run('{"necessary": true, "analytical": false, "marketing": true}')
    cs = result["consent_state"]
    assert cs["marketing"] is True, (
        f"Pravi JSON `marketing:true` MORA dati `marketing is True`. Dobio: {cs!r}"
    )
    assert cs["analytical"] is False, (
        f"`analytical:false` MORA dati `analytical is False`. Dobio: {cs!r}"
    )


# AC1: oba false → oba False
def test_valid_cookie_both_false():
    result = _run('{"necessary": true, "analytical": false, "marketing": false}')
    cs = result["consent_state"]
    assert cs["analytical"] is False and cs["marketing"] is False, (
        f"`analytical:false`/`marketing:false` → oba False. Dobio: {cs!r}"
    )


# AC1/G-2: MALFORMED JSON (garbage) → NE crash → DEFAULT-DENY (KRITICAN — 7-2 contract)
def test_malformed_json_default_deny():
    result = _run("garbage-not-json")
    assert result == {"consent_state": DENY}, (
        "MALFORMED `consent_state` (neispravan JSON) → `json.loads` baca "
        "ValueError/JSONDecodeError; context_processor MORA hvatati u try/except → "
        f"DEFAULT-DENY, NIKAD 500 (G-2/Boundary). Dobio: {result!r}"
    )


# AC1: validan JSON ali NE-dict (`[]`) → DEFAULT-DENY
def test_non_dict_list_default_deny():
    result = _run("[]")
    assert result == {"consent_state": DENY}, (
        "Validan-JSON-ali-ne-dict (`[]`) → isinstance(data, dict) False → tretira "
        f"se kao prazno → DEFAULT-DENY. Dobio: {result!r}"
    )


# AC1: validan JSON ali NE-dict (`42`) → DEFAULT-DENY
def test_non_dict_number_default_deny():
    result = _run("42")
    assert result == {"consent_state": DENY}, (
        f"Validan-JSON-ali-ne-dict (`42`) → DEFAULT-DENY. Dobio: {result!r}"
    )


# AC1: validan JSON ali NE-dict (`"true"` string) → DEFAULT-DENY
def test_non_dict_string_default_deny():
    result = _run('"true"')
    assert result == {"consent_state": DENY}, (
        f"Validan-JSON-ali-ne-dict (`\"true\"` string) → DEFAULT-DENY. Dobio: {result!r}"
    )


# AC1: dict ali NEDOSTAJU kljucevi (`{}`) → per-kljuc deny (analytical/marketing False)
def test_missing_keys_deny():
    result = _run("{}")
    cs = result["consent_state"]
    assert cs == DENY, (
        "Dict bez analytical/marketing → `.get(...)` None → `None is True` False → "
        f"per-kljuc DENY; necessary server-forced True. Dobio: {cs!r}"
    )


# AC1: dict sa SAMO necessary → analytical/marketing False
def test_only_necessary_key_denies_others():
    result = _run('{"necessary": true}')
    cs = result["consent_state"]
    assert cs["analytical"] is False and cs["marketing"] is False, (
        f"Nedostajuci analytical/marketing kljuc → False (per-kljuc deny). Dobio: {cs!r}"
    )


# AC1/CRITICAL-2/SM-D10: STRIKTAN is True — string-truthy "yes" → analytical False
def test_off_type_truthy_string_yes_denies():
    result = _run('{"analytical": "yes", "marketing": "yes"}')
    cs = result["consent_state"]
    assert cs["analytical"] is False, (
        "STRIKTAN `is True` (SM-D10/CRITICAL-2): off-tip truthy `\"yes\"` (string) → "
        f"`\"yes\" is True` == False → analytical DENY (forged → DENY). Dobio: {cs!r}"
    )
    assert cs["marketing"] is False, (
        f"`marketing:\"yes\"` (string) → marketing DENY. Dobio: {cs!r}"
    )


# AC1/CRITICAL-2/SM-D10: STRIKTAN is True — int 1 → analytical False
def test_off_type_truthy_int_one_denies():
    result = _run('{"analytical": 1, "marketing": 1}')
    cs = result["consent_state"]
    assert cs["analytical"] is False and cs["marketing"] is False, (
        "STRIKTAN `is True`: `1 is True` == False → DENY (NE truthy-coercion / NE "
        f"`bool(...)` koji bi primio 1 kao consent). Dobio: {cs!r}"
    )


# AC1/CRITICAL-2/SM-D10: STRIKTAN is True — string "true" → analytical False
def test_off_type_truthy_string_true_denies():
    result = _run('{"analytical": "true", "marketing": "true"}')
    cs = result["consent_state"]
    assert cs["analytical"] is False and cs["marketing"] is False, (
        "STRIKTAN `is True`: `\"true\"` (STRING, NE bool) → `\"true\" is True` == "
        f"False → DENY. SAMO pravi JSON `true` (Python True) prolazi. Dobio: {cs!r}"
    )


# AC1: `necessary` je UVEK True bez obzira na ulaz (server-forced)
@pytest.mark.parametrize(
    "cookie",
    [
        None,
        "garbage",
        "[]",
        "{}",
        '{"necessary": false, "analytical": true, "marketing": true}',
        '{"analytical": "yes"}',
    ],
)
def test_necessary_always_true(cookie):
    result = _run(cookie)
    assert result["consent_state"]["necessary"] is True, (
        "`necessary` MORA biti UVEK `True` (server-forced; ne cita se kao kolacic "
        f"vrednost). Ulaz {cookie!r} dao: {result['consent_state']!r}"
    )


# AC1/fail-safe: NIKAD default-allow — odsutan/malformed/forged NIKAD daje analytical/marketing True
@pytest.mark.parametrize(
    "cookie",
    [
        None,
        "garbage-not-json",
        "[]",
        "42",
        "{}",
        '{"analytical": "yes", "marketing": 1}',
        '{"analytical": "true"}',
    ],
)
def test_never_default_allow(cookie):
    cs = _run(cookie)["consent_state"]
    assert cs["analytical"] is False and cs["marketing"] is False, (
        "FAIL-SAFE (consent-safety): odsutan/malformed/forged kolacic NIKAD ne sme "
        f"dati analytical/marketing True. Ulaz {cookie!r} dao: {cs!r}"
    )


# AC1/G-11: vraceni dict je dict-key-lookupabilan u template-u (`{{ consent_state.analytical }}`)
def test_consent_state_dict_key_lookup_in_template():
    ctx = _run('{"necessary": true, "analytical": true, "marketing": false}')
    tpl = Template("{{ consent_state.analytical }}|{{ consent_state.marketing }}")
    rendered = tpl.render(Context(ctx))
    assert rendered == "True|False", (
        "Django `.` operator MORA rezolvovati dict-key (`consent_state[\"analytical\"]`) "
        f"za `{{{{ consent_state.analytical }}}}` (G-11, obican dict). Dobio: {rendered!r}"
    )
