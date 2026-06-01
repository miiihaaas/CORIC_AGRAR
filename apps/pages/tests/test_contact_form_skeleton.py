"""Story 4.2 — INVERTOVANI skeleton anti-testovi (Task 4.2, TEA RED).

Story 3.3 je scaffold-ovao DISABLED skelet kontakt forme (polja/submit disabled, BEZ
hx-post, „uskoro aktivna" hint). Story 4.2 (AC8/Task 8) OŽIVLJAVA tu formu: polja
aktivna, hx-post dodat, hint uklonjen. Ovih 5 testova je INVERTOVANO na POST-4.2
realnost (project-context.md:296 — testovi NE smeju ostati crveni posle GREEN faze).

Ovo je TEA posao (project-context.md:294 — „Dev NIKAD ne piše testove"); Dev NE dira
ovaj fajl. Poznat TDD milestone: skeleton anti-testovi se flip-uju kad story oživi skelet.

RED razlog (sada): skelet je još disabled + bez hx-post → INVERTOVANE asercije padaju
dok Dev (GREEN, Task 8) ne oživi formu.

OČUVANO (validno i u skeletu i u aktivnoj formi):
- test_contact_form_has_csrf_token
- test_contact_form_has_4_labeled_fields

INVERTOVANO (skelet → aktivna forma):
- test_contact_submit_is_disabled        → test_contact_submit_is_enabled
- test_contact_form_inputs_disabled...   → test_contact_form_inputs_enabled_and_uskoro_hint_removed
- test_contact_form_has_no_functional_hx_post → test_contact_form_has_functional_hx_post

Pokrenuti:
    just test apps/pages/tests/test_contact_form_skeleton.py -v
"""

from __future__ import annotations

import re

import pytest
from django.urls import reverse
from django.utils.translation import activate

pytestmark = pytest.mark.django_db

_FORM_RE = re.compile(
    r"<form\b[^>]*data-testid=[\"']contact-form[\"'][^>]*>(.*?)</form>",
    re.IGNORECASE | re.DOTALL,
)
_FORM_OPEN_RE = re.compile(
    r"<form\b[^>]*data-testid=[\"']contact-form[\"'][^>]*>",
    re.IGNORECASE,
)
_SUBMIT_RE = re.compile(
    r"<button\b[^>]*data-testid=[\"']contact-submit[\"'][^>]*>",
    re.IGNORECASE,
)
_LABEL_FOR_RE = re.compile(r"<label\b[^>]*for=[\"']([^\"']+)[\"'][^>]*>", re.IGNORECASE)


def _contact_html(client, lang: str = "sr") -> str:
    activate(lang)
    response = client.get(f"/{lang}/kontakt/")
    assert response.status_code == 200, (
        f"GET /{lang}/kontakt/ MORA biti 200 da bi se HTML parsirao, dobio "
        f"{response.status_code}."
    )
    template_names = [t.name for t in response.templates if t.name]
    assert "pages/contact.html" in template_names, (
        f"Render MORA koristiti 'pages/contact.html', dobio {template_names!r}."
    )
    return response.content.decode("utf-8")


def _form_inner(html: str) -> str:
    m = _FORM_RE.search(html)
    assert m, (
        "Kontakt strana MORA imati <form data-testid=\"contact-form\">."
    )
    return m.group(1)


# OČUVAN — CSRF token (validno i u aktivnoj formi, Security#1)
def test_contact_form_has_csrf_token(client):
    """{% csrf_token %} render-uje hidden input name=csrfmiddlewaretoken (Security#1)."""
    html = _contact_html(client)
    inner = _form_inner(html)
    assert re.search(
        r"name=[\"']csrfmiddlewaretoken[\"']", inner, re.IGNORECASE
    ), (
        "Forma MORA sadržati {% csrf_token %} (hidden input name=\"csrfmiddlewaretoken\") "
        "— project-context.md § Security #1."
    )


# OČUVAN — 4 labelirana polja (zadržavaju se u aktivnoj formi, a11y)
def test_contact_form_has_4_labeled_fields(client):
    """4 polja (Ime/Email/Telefon/Poruka) — svako sa <label for> + odgovarajući input/textarea."""
    html = _contact_html(client)
    inner = _form_inner(html)

    label_fors = _LABEL_FOR_RE.findall(inner)
    assert len(label_fors) >= 4, (
        f"Forma MORA imati bar 4 vidljiva <label for> (Ime/Email/Telefon/Poruka). "
        f"Pronađeno: {label_fors!r}"
    )

    field_ids = set(re.findall(r"\bid=[\"']([^\"']+)[\"']", inner, re.IGNORECASE))
    for ref in label_fors:
        assert ref in field_ids, (
            f"<label for=\"{ref}\"> MORA referencirati postojeće polje sa id=\"{ref}\" "
            f"(asocijacija label↔input — a11y). Pronađeni id-jevi: {sorted(field_ids)!r}"
        )


# INVERTOVAN — submit dugme je SADA ENABLED (forma aktivna, AC8)
def test_contact_submit_is_enabled(client):
    """AC8: submit dugme [data-testid=contact-submit] VIŠE NEMA `disabled` ni `aria-disabled`."""
    html = _contact_html(client)
    m = _SUBMIT_RE.search(html)
    assert m, (
        "Forma MORA imati submit dugme [data-testid=\"contact-submit\"]."
    )
    tag = m.group(0)
    assert not re.search(r"\bdisabled\b", tag, re.IGNORECASE), (
        f"Submit dugme VIŠE NE SME imati `disabled` (Story 4.2 ga aktivira, AC8). Tag: {tag!r}"
    )
    assert not re.search(r"aria-disabled=[\"']true[\"']", tag, re.IGNORECASE), (
        f"Submit dugme VIŠE NE SME imati aria-disabled=\"true\" (AC8). Tag: {tag!r}"
    )


# INVERTOVAN — polja SADA aktivna + „uskoro" hint uklonjen (AC8)
def test_contact_form_inputs_enabled_and_uskoro_hint_removed(client):
    """AC8: SVA user input/textarea polja VIŠE NEMAJU `disabled`; „uskoro aktivna" hint uklonjen."""
    html = _contact_html(client)
    inner = _form_inner(html)

    field_tags = re.findall(r"<(?:input|textarea)\b[^>]*>", inner, re.IGNORECASE)
    user_fields = [
        t for t in field_tags
        if "csrfmiddlewaretoken" not in t.lower() and 'type="hidden"' not in t.lower()
    ]
    assert user_fields, "Forma MORA imati input/textarea polja."
    for t in user_fields:
        assert not re.search(r"\bdisabled\b", t, re.IGNORECASE), (
            f"User polje VIŠE NE SME biti `disabled` — forma je aktivna (AC8). Tag: {t!r}"
        )

    assert "uskoro biti dostupna" not in html, (
        "Hint „Forma ce uskoro biti dostupna...” MORA biti uklonjen (forma aktivna, AC8)."
    )


# INVERTOVAN — forma SADA ima funkcionalan hx-post (AC8)
def test_contact_form_has_functional_hx_post(client):
    """AC8: forma SADA IMA `hx-post` ka forms:contact_submit (oživljen skelet)."""
    html = _contact_html(client)
    form_open = _FORM_OPEN_RE.search(html)
    assert form_open, "Forma <form data-testid=\"contact-form\"> mora postojati."
    tag = form_open.group(0)

    assert re.search(r"method=[\"']post[\"']", tag, re.IGNORECASE), (
        f"<form> MORA imati method=\"post\" (C1 — sprečava GET-default URL leak). Tag: {tag!r}"
    )
    assert re.search(r"hx-post=", tag, re.IGNORECASE), (
        f"<form> SADA MORA imati `hx-post` (HTMX submit — Story 4.2, AC8). Tag: {tag!r}"
    )
    submit_url = reverse("forms:contact_submit")
    assert submit_url in html, (
        f"`hx-post` MORA ciljati forms:contact_submit ({submit_url}), AC8."
    )
