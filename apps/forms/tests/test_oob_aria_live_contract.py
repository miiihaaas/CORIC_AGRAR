"""Story 4.6 — OOB aria-live golden/contract + new-partial snapshot (TEA, Task 1.3 + 3.4).

Ovaj modul nosi DVE klase asercija sa RAZLIČITIM RED-stanjem:

═══════════════════════════════════════════════════════════════════════════════
1) GOLDEN/CONTRACT (REGRESSION-LOCK — must pass BEFORE AND AFTER refaktora).
═══════════════════════════════════════════════════════════════════════════════
Renderuje POSTOJEĆE `*_form_fields.html` + `*_success.html` partial-e sa bound
kontekstom i tvrdi TAČNE OOB substring-ove za SVE guard/poruka kombinacije koje
mreža MORA uhvatiti (Task 1.3 (1)-(4)):
- (1) success → `{% if request.htmx %}` aktivan + per-forma success poruka u OOB;
- (2) error (sve 4) → `{% if request.htmx and form.errors %}` aktivan + „Greška…”;
- (3) product_not_found (SAMO model_inquiry) → „Proizvod nije pronađen.” u OOB;
- (4) non-HTMX → NEMA `hx-swap-oob` (guard isključen).
Ovo je net protiv svake regresije OOB izlaza posle refaktora (uključujući brisanje
model_inquiry product_not_found najave).

═══════════════════════════════════════════════════════════════════════════════
2) NEW-ABSTRACTION SNAPSHOT (RED until Dev creates `_oob_aria_live.html` — Task 3.4).
═══════════════════════════════════════════════════════════════════════════════
Tvrdi da NOVI `forms/partials/_oob_aria_live.html` renderuje BAJT-IDENTIČAN string
trenutnom inline OOB bloku (per `message` vrednost). Partial NE POSTOJI još → ove
asercije FAIL-uju ČISTO (guard hvata `TemplateDoesNotExist` i radi `pytest.fail`,
NE ruši kolekciju). Posle Dev Task 3.1 → GREEN.

Refs: 4-6 AC1 (2)/(3) + AC4 + Task 1.3 + Task 3.4; 4-6-interface-contract § 3.
"""

from __future__ import annotations

import re

import pytest
from django.template import TemplateDoesNotExist
from django.template.loader import render_to_string
from django.test import RequestFactory
from django.utils.translation import activate

from apps.forms.forms import (
    ContactForm,
    ModelInquiryForm,
    PartRequestForm,
    ServiceRequestForm,
)

pytestmark = pytest.mark.django_db


# ── helpers ───────────────────────────────────────────────────────────────────


class _Htmx:
    """Minimalan stub koji oponaša `request.htmx` truthiness (django_htmx HtmxDetails)."""

    def __init__(self, *, is_htmx: bool):
        self._is = is_htmx

    def __bool__(self):
        return self._is


def _request(*, htmx: bool):
    activate("sr")
    req = RequestFactory().get("/")
    req.htmx = _Htmx(is_htmx=htmx)
    return req


def _bound_invalid(form_cls):
    """Vrati bound (invalid) formu — prazan POST → form.errors popunjen."""
    form = form_cls(data={})
    form.is_valid()  # trigeruje validaciju → form.errors
    assert form.errors, "Fixture očekuje invalid formu (form.errors popunjen)."
    return form


def _oob_inner(html: str) -> str | None:
    m = re.search(
        r'<[^>]*hx-swap-oob="innerHTML:#aria-live"[^>]*>(.*?)</',
        html,
        re.IGNORECASE | re.DOTALL,
    )
    return m.group(1) if m else None


# Per-forma (form_fields_template, form_cls, success_template, success_msg, error)
FORMS = {
    "contact": (
        "forms/partials/_contact_form_fields.html",
        ContactForm,
        "forms/partials/contact_success.html",
        "Upit je poslat.",
    ),
    "service": (
        "forms/partials/_service_request_form_fields.html",
        ServiceRequestForm,
        "forms/partials/service_request_success.html",
        "Servisni zahtev je poslat.",
    ),
    "part_request": (
        "forms/partials/_part_request_form_fields.html",
        PartRequestForm,
        "forms/partials/part_request_success.html",
        "Upit za rezervni deo je poslat.",
    ),
    "model_inquiry": (
        "forms/partials/_model_inquiry_form_fields.html",
        ModelInquiryForm,
        "forms/partials/model_inquiry_success.html",
        "Upit za model je poslat.",
    ),
}

ERROR_OOB = "Greška pri slanju, proverite polja."


# ═══════════════ GOLDEN/CONTRACT — REGRESSION-LOCK (green now + after) ═════════


# (1) success → htmx guard aktivan + per-forma poruka u OOB
@pytest.mark.parametrize("key", list(FORMS))
def test_golden_success_oob_message(key):
    """REGRESSION-LOCK: *_success.html (request.htmx) → OOB sa TAČNOM per-forma porukom."""
    _fields, _cls, success_tpl, success_msg = FORMS[key]
    html = render_to_string(success_tpl, {}, request=_request(htmx=True))
    assert 'hx-swap-oob="innerHTML:#aria-live"' in html, (
        f"[{key}] success partial MORA imati OOB div (request.htmx aktivan)."
    )
    inner = _oob_inner(html)
    assert inner and success_msg in inner, (
        f"[{key}] success OOB MORA sadržati „{success_msg}”. OOB: {inner!r}"
    )


# (2) error (sve 4) → htmx+form.errors guard aktivan + „Greška…”
@pytest.mark.parametrize("key", list(FORMS))
def test_golden_error_oob_message(key):
    """REGRESSION-LOCK: *_form_fields.html (request.htmx + form.errors) → OOB „Greška…”."""
    fields_tpl, form_cls, _s, _m = FORMS[key]
    form = _bound_invalid(form_cls)
    ctx = {"form": form}
    if key == "model_inquiry":
        ctx["product"] = None  # invalid-grana best-effort lookup → None
    html = render_to_string(fields_tpl, ctx, request=_request(htmx=True))
    assert 'hx-swap-oob="innerHTML:#aria-live"' in html, (
        f"[{key}] error partial MORA imati OOB div (request.htmx + form.errors)."
    )
    inner = _oob_inner(html)
    assert inner and ERROR_OOB in inner, (
        f"[{key}] error OOB MORA sadržati „{ERROR_OOB}”. OOB: {inner!r}"
    )


# (3) product_not_found (SAMO model_inquiry) → „Proizvod nije pronađen.” u OOB
def test_golden_model_inquiry_product_not_found_oob():
    """REGRESSION-LOCK (model_inquiry IZUZETAK): tro-ishodni OOB — product_not_found grana."""
    fields_tpl = FORMS["model_inquiry"][0]
    # Validan slug-input ali nepostojeći produkt → view postavlja product_not_found=True,
    # forma JE valid (form.errors prazan) → grana product_not_found mora fire-ovati.
    form = ModelInquiryForm(
        data={
            "name": "Marko Marković",
            "email": "marko@example.com",
            "phone": "+381641234567",
            "message": "Zanima me ovaj model.",
            "product_slug": "ne-postoji",
        }
    )
    form.is_valid()
    html = render_to_string(
        fields_tpl,
        {"form": form, "product": None, "product_not_found": True},
        request=_request(htmx=True),
    )
    inner = _oob_inner(html)
    assert inner and "Proizvod nije pronađen." in inner, (
        f"model_inquiry product_not_found OOB MORA sadržati „Proizvod nije pronađen.” "
        f"(đ). OOB: {inner!r}"
    )
    assert ERROR_OOB not in (inner or ""), (
        "product_not_found grana NE SME emitovati „Greška…” (elif granjanje)."
    )


# (4) non-HTMX → NEMA hx-swap-oob (guard isključen)
@pytest.mark.parametrize("key", list(FORMS))
def test_golden_non_htmx_no_oob(key):
    """REGRESSION-LOCK: bez request.htmx → guard isključuje OOB (success I error)."""
    fields_tpl, form_cls, success_tpl, _m = FORMS[key]
    # success path
    s_html = render_to_string(success_tpl, {}, request=_request(htmx=False))
    assert "hx-swap-oob" not in s_html, (
        f"[{key}] non-HTMX success NE SME imati OOB (guard {{% if request.htmx %}})."
    )
    # error path
    form = _bound_invalid(form_cls)
    ctx = {"form": form}
    if key == "model_inquiry":
        ctx["product"] = None
    e_html = render_to_string(fields_tpl, ctx, request=_request(htmx=False))
    assert "hx-swap-oob" not in e_html, (
        f"[{key}] non-HTMX error NE SME imati OOB (guard {{% if request.htmx %}})."
    )


# ═══════════════ NEW-ABSTRACTION SNAPSHOT — RED until Dev Task 3.1 ═════════════


def _render_new_oob_partial(message: str, *, htmx: bool) -> str:
    """Renderuj NOVI `_oob_aria_live.html` partial; čist FAIL ako ne postoji (RED)."""
    try:
        return render_to_string(
            "forms/partials/_oob_aria_live.html",
            {"message": message},
            request=_request(htmx=htmx),
        )
    except TemplateDoesNotExist:
        pytest.fail(
            "RED (očekivano do Dev Task 3.1): `forms/partials/_oob_aria_live.html` "
            "još NE postoji. Dev kreira partial sa INTERNIM {% if request.htmx %} "
            "guard-om + `message` parametrom; tada ovaj snapshot postaje GREEN."
        )


@pytest.mark.parametrize(
    ("message"),
    [
        "Upit je poslat.",
        "Upit za model je poslat.",
        "Servisni zahtev je poslat.",
        "Upit za rezervni deo je poslat.",
        "Greška pri slanju, proverite polja.",
    ],
)
def test_new_oob_partial_byte_identical_to_inline(message):
    """RED until Dev creates `_oob_aria_live.html` (Task 3.4).

    Tvrdi da NOVI partial (request.htmx aktivan) renderuje BAJT-IDENTIČAN string
    trenutnom inline OOB bloku za datu poruku. Inline literal (iz svih *_form_fields
    /*_success.html):
        <div hx-swap-oob="innerHTML:#aria-live">{message}</div>
    """
    expected = f'<div hx-swap-oob="innerHTML:#aria-live">{message}</div>'
    rendered = _render_new_oob_partial(message, htmx=True).strip()
    assert rendered == expected, (
        "NOVI _oob_aria_live.html MORA renderovati BAJT-IDENTIČAN inline OOB string.\n"
        f"  očekivano: {expected!r}\n  dobijeno:  {rendered!r}"
    )


def test_new_oob_partial_guarded_non_htmx():
    """RED until Dev creates `_oob_aria_live.html` (Task 3.4).

    Bez request.htmx → INTERNI guard isključuje OOB → prazan render (NEMA hx-swap-oob).
    """
    rendered = _render_new_oob_partial("Upit je poslat.", htmx=False)
    assert "hx-swap-oob" not in rendered, (
        "NOVI _oob_aria_live.html MORA nositi INTERNI {% if request.htmx %} guard → "
        "non-HTMX render je prazan (bez OOB div-a)."
    )


def test_new_oob_partial_non_htmx_renders_truly_empty():
    """Regression-guard (zero visible bytes): non-HTMX render MORA biti PRAZAN.

    Jača od `hx-swap-oob not in rendered`: tvrdi da `rendered.strip() == ""` — nula
    vidljivih bajtova. Trenutni partial nosi interni `{% comment %}…{% endcomment %}`
    (template-level, briše se pri renderu). Ako bi budući refaktor pretvorio taj
    `{% comment %}` u HTML komentar `<!-- … -->`, on bi PROCURIO u non-HTMX render
    (ostao u izlazu i kad guard ne emituje OOB div) — ovaj guard to hvata.
    """
    rendered = _render_new_oob_partial("Upit je poslat.", htmx=False)
    assert rendered.strip() == "", (
        "NOVI _oob_aria_live.html non-HTMX render MORA biti PRAZAN (rendered.strip() == "
        "\"\", nula vidljivih bajtova). Procureli `<!-- -->` HTML komentar bi pao ovde.\n"
        f"  dobijeno: {rendered!r}"
    )
