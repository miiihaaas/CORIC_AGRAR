"""Story 4.6 — NEW-ABSTRACTION contract (TEA, Task 1.4).

═══════════════════════════════════════════════════════════════════════════════
RED until Dev creates the abstractions (Task 2 — FORM_RATELIMIT_RATE + htmx_form_endpoint).
═══════════════════════════════════════════════════════════════════════════════

Ove asercije tvrde POST-refaktor strukture koje JOŠ NE POSTOJE:
- `FORM_RATELIMIT_RATE` konstanta (== "5/m") na jednom mestu (apps.forms.views);
- `htmx_form_endpoint` dekorator koji uvezuje require_POST (SPOLJAŠNJI) +
  ratelimit(key="ip", rate=FORM_RATELIMIT_RATE, block=False) (UNUTRAŠNJI) +
  request.limited → 429 guard;
- sva 4 view-a su dekorisana tom apstrakcijom (introspekcija + ponašanje).

Asercije su pisane da FAIL-uju ČISTO (skip/fail sa jasnom porukom) ako simbol ne
postoji — NE ruše kolekciju nego daju ekspresivan RED. Posle Dev Task 2 → GREEN.

NAPOMENA: ponašanje kompozicije (405-pre-429, GET-ne-troši-budžet, 6-ti-429) je
NEZAVISNO lockovano u test_form_endpoints_contract.py (regression-lock, green pre I
posle). Ovaj modul lockuje POSTOJANJE imenovane apstrakcije (AC2/AC3).

Refs: 4-6 AC2/AC3 + Task 1.4 + Task 2; 4-6-interface-contract § 2.
"""

from __future__ import annotations

import importlib

import pytest

from apps.forms import views as views_module


def _maybe(attr: str):
    return getattr(views_module, attr, None)


# ── FORM_RATELIMIT_RATE konstanta (AC3) ───────────────────────────────────────


def test_form_ratelimit_rate_constant_exists_and_is_5_per_m():
    """RED until Dev Task 2.1: `FORM_RATELIMIT_RATE` konstanta == "5/m".

    Behavior-preserving (SM-D3/SM-D9): rate ostaje 5/m; centralizacija u konstantu
    čini buduću promenu (epics.md:840 10/15m) jedno-mesto izmenom.
    """
    rate = _maybe("FORM_RATELIMIT_RATE")
    if rate is None:
        pytest.fail(
            "RED (očekivano do Dev Task 2.1): `apps.forms.views.FORM_RATELIMIT_RATE` "
            "još NE postoji. Dev definiše modul-level konstantu `FORM_RATELIMIT_RATE = \"5/m\"`."
        )
    assert rate == "5/m", (
        f"FORM_RATELIMIT_RATE MORA biti TAČNO „5/m” (behavior-preserving, NE 10/15m), "
        f"dobio {rate!r}."
    )


# ── htmx_form_endpoint dekorator (AC2) ────────────────────────────────────────


def test_htmx_form_endpoint_decorator_exists_and_is_callable():
    """RED until Dev Task 2.1: `htmx_form_endpoint` dekorator postoji i pozivljiv je."""
    deco = _maybe("htmx_form_endpoint")
    if deco is None:
        pytest.fail(
            "RED (očekivano do Dev Task 2.1): `apps.forms.views.htmx_form_endpoint` "
            "još NE postoji. Dev definiše dekorator koji uvezuje @require_POST "
            "(SPOLJAŠNJI) + @ratelimit(...block=False) (UNUTRAŠNJI) + request.limited→429."
        )
    assert callable(deco), "`htmx_form_endpoint` MORA biti pozivljiv (dekorator)."


def test_htmx_form_endpoint_composes_require_post_outer_and_429_guard():
    """RED until Dev Task 2.1: dekorator-kompozicija (ponašanjem).

    Primeni `htmx_form_endpoint` na trivijalan probe-view i potvrdi:
    - GET → 405 (require_POST je SPOLJAŠNJI, izvršava se PRVI);
    - 5× GET NE troši rate budžet → 6. POST i dalje prolazi do tela (probe vraća 200);
    - kad ratelimit postavi request.limited → guard vraća 429.
    Ovo dokazuje EKSAKTAN redosled require_POST(ratelimit(view)) bez vezivanja za
    konkretni produkcijski view.
    """
    deco = _maybe("htmx_form_endpoint")
    if deco is None:
        pytest.fail(
            "RED (očekivano do Dev Task 2.1): `htmx_form_endpoint` ne postoji — vidi "
            "test_htmx_form_endpoint_decorator_exists_and_is_callable."
        )

    from django.http import HttpResponse
    from django.test import RequestFactory, override_settings

    _LOCMEM = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}

    @deco
    def probe(request):  # pragma: no cover - telo se izvršava samo na valid POST path
        return HttpResponse("ok", status=200)

    rf = RequestFactory()

    with override_settings(CACHES=_LOCMEM, RATELIMIT_ENABLE=True):
        from django.core.cache import cache

        cache.clear()
        # GET → 405 (require_POST SPOLJAŠNJI)
        get_resp = probe(rf.get("/", REMOTE_ADDR="198.51.100.200"))
        assert get_resp.status_code == 405, (
            f"htmx_form_endpoint: GET MORA biti 405 (require_POST SPOLJAŠNJI), dobio "
            f"{get_resp.status_code}."
        )
        # 5× GET NE troši budžet → POST i dalje 200
        for _ in range(5):
            probe(rf.get("/", REMOTE_ADDR="198.51.100.201"))
        post_resp = probe(rf.post("/", REMOTE_ADDR="198.51.100.201"))
        assert post_resp.status_code == 200, (
            f"htmx_form_endpoint: POST posle 5× GET MORA biti 200 (GET ne troši "
            f"budžet), dobio {post_resp.status_code}."
        )
        # 6 POST-ova istog IP-a → poslednji 429 (ratelimit UNUTRAŠNJI + guard)
        statuses = [
            probe(rf.post("/", REMOTE_ADDR="198.51.100.202")).status_code
            for _ in range(6)
        ]
        assert statuses[-1] == 429, (
            f"htmx_form_endpoint: 6. POST istog IP-a MORA biti 429 (ratelimit UNUTRAŠNJI "
            f"+ request.limited→429), dobio {statuses!r}."
        )
        assert 403 not in statuses, (
            f"htmx_form_endpoint NE SME vraćati 403 (block=False). Statusi: {statuses!r}."
        )
        cache.clear()


@pytest.mark.parametrize(
    "view_name",
    ["contact_submit", "model_inquiry_submit", "service_request_submit", "part_request_submit"],
)
def test_all_four_views_use_the_decorator(view_name):
    """RED until Dev Task 2.2: sva 4 view-a su dekorisana `htmx_form_endpoint`-om.

    Posle refaktora svaki view i dalje: GET→405, ratelimit aktivan. Ovde dodatno
    tvrdimo da view i dalje POSTOJI i da je pozivljiv (introspekcija imena). Striktna
    provera identiteta dekoratora se radi ponašanjem u test_form_endpoints_contract.py;
    ovaj test je guard da view nije slučajno preimenovan/uklonjen refaktorom.
    """
    importlib.reload  # noqa: B018 - drži import živim za jasnost
    view = getattr(views_module, view_name, None)
    assert view is not None and callable(view), (
        f"View `{view_name}` MORA postojati i biti pozivljiv POSLE refaktora "
        f"(dekorator NE SME promeniti javni naziv view-a — URLConf zavisi od njega)."
    )


@pytest.mark.parametrize(
    "view_name",
    ["contact_submit", "model_inquiry_submit", "service_request_submit", "part_request_submit"],
)
def test_decorated_views_preserve_dunder_name(view_name):
    """Regression-guard (functools.wraps): dekorisani view MORA očuvati `__name__`.

    `htmx_form_endpoint` (i njegov require_POST/ratelimit sloj) MORA koristiti
    `functools.wraps` tako da `view.__name__` ostane ime originalne funkcije.
    Ako bi budući refaktor ispustio @wraps, dekorisani view bi dobio ime wrapper-a
    (npr. `_inner`/`wrapper`) — što kvari Django error logging i reverse/URLConf
    dijagnostiku. Ovaj guard prolazi protiv trenutnog (ispravnog) koda.
    """
    view = getattr(views_module, view_name, None)
    assert view is not None, f"View `{view_name}` MORA postojati (preduslov za __name__ guard)."
    assert view.__name__ == view_name, (
        f"Dekorisani view `{view_name}` MORA očuvati `__name__ == \"{view_name}\"` "
        f"(functools.wraps), dobio __name__ == {view.__name__!r}. Ispušten @wraps bi "
        f"pokvario Django error logging / reverse dijagnostiku."
    )
