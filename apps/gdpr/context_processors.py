"""Story 7.3 — `consent_state` context_processor (CONSUMER strana consent boundary-ja).

Čita `consent_state` JSON kolačić koji 7-2 `SetConsentView` postavlja
(`json.dumps({"necessary":bool,"analytical":bool,"marketing":bool})`) i izlaže
parsiran consent SVAKOM template-u kao `{"consent_state": dict}`.

DEFAULT-DENY (SM-D1/D2/D8, 7-2↔7-3 boundary contract): na SVAKI od — kolačić
odsutan / `json.loads` greška (malformed/garbage/forged) / rezultat NIJE dict /
nedostajući ključ — vraća pun deny (`{"necessary":True,"analytical":False,
"marketing":False}`). **NIKAD crash, NIKAD default-allow.** Kolačić je untrusted
client input.

STRIKTAN `is True` (CRITICAL-2/SM-D10): SAMO pravi JSON `true` (Python `True`)
prolazi kao consent. Off-tip truthy (`"yes"`, `1`, `"true"`-string) → `False`
(off-šema vrednost u validnom dict-u JE forged → DENY). NIKAD `bool(...)`.

`necessary` je UVEK `True` (server-forsiran; neophodni kolačići se ne čitaju
kao gate).
"""

from __future__ import annotations

import json

# Jedini izvor istine za default-deny shape (7-2↔7-3 boundary contract). Reuse-uje
# ga ovde (absent/malformed/non-dict path) I tracking.py tag-ovi (.get fallback —
# privacy-fail-safe ako context_processor nije registrovan / manual Context render).
DEFAULT_DENY = {"necessary": True, "analytical": False, "marketing": False}


def consent_state(request) -> dict:
    """Parsira `consent_state` kolačić → `{"consent_state": dict}`; DEFAULT-DENY."""
    raw = request.COOKIES.get("consent_state")
    if raw is None:
        data: dict = {}
    else:
        # json.JSONDecodeError je ValueError podklasa; TypeError za ne-str ulaz.
        try:
            data = json.loads(raw)
        except (ValueError, TypeError):
            data = {}
        if not isinstance(data, dict):
            data = {}

    # DEFAULT_DENY je single source of truth za shape; absent/malformed/non-dict
    # path (data == {}) daje TAČNO DEFAULT_DENY vrednosti. necessary UVEK True
    # (server-forsiran, nikad iz kolačića); analytical/marketing STRIKTAN is True.
    return {
        "consent_state": {
            **DEFAULT_DENY,
            "analytical": data.get("analytical") is True,  # STRIKTAN is True
            "marketing": data.get("marketing") is True,
        }
    }
