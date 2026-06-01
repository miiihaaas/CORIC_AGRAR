"""Story 3.3 — AC6 (SM-D8/SM-D4): forward-compat skelet kontakt forme.

4 polja (Ime*/Email*/Telefon/Poruka*) sa vidljivim <label> + {% csrf_token %} PRISUTAN
+ method="post" BEZ action (C1) + SVA polja disabled (a11y silent-data-loss guard) +
submit dugme disabled+aria-disabled + hint povezan preko aria-describedby. NEMA funkcionalan
submit (hx-post/action) — to je Epic 4 (Story 4.2).

RED phase (TEA). Regex parsiranje (projekat nema BeautifulSoup — mirror test_about_*).

RED razlog: pages/contact.html + _contact_form.html ne postoje → GET /sr/kontakt/ je
404 → parsiranje pada na status_code assertion-u.

AC6 — 5 testova:
- test_contact_form_has_csrf_token
- test_contact_form_has_4_labeled_fields
- test_contact_submit_is_disabled
- test_contact_form_inputs_disabled_and_hint_associated
- test_contact_form_has_no_functional_hx_post

Pokrenuti:
    just test apps/pages/tests/test_contact_form_skeleton.py -v
"""

from __future__ import annotations

import re

import pytest
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
        f"{response.status_code} (RED: ContactView/pages/contact.html ne postoji)."
    )
    template_names = [t.name for t in response.templates if t.name]
    assert "pages/contact.html" in template_names, (
        f"Render MORA koristiti 'pages/contact.html', dobio {template_names!r}."
    )
    return response.content.decode("utf-8")


def _form_inner(html: str) -> str:
    m = _FORM_RE.search(html)
    assert m, (
        "Kontakt strana MORA imati <form data-testid=\"contact-form\"> (skelet — AC6/SM-D8)."
    )
    return m.group(1)


def test_contact_form_has_csrf_token(client):
    """AC6/Security#1: {% csrf_token %} render-uje hidden input name=csrfmiddlewaretoken."""
    html = _contact_html(client)
    inner = _form_inner(html)
    assert re.search(
        r"name=[\"']csrfmiddlewaretoken[\"']", inner, re.IGNORECASE
    ), (
        "Form skelet MORA sadržati {% csrf_token %} (hidden input "
        "name=\"csrfmiddlewaretoken\") — project-context.md § Security #1; AC6."
    )


def test_contact_form_has_4_labeled_fields(client):
    """AC6: 4 polja (Ime/Email/Telefon/Poruka) — svako sa <label for> + odgovarajući
    input/textarea sa tim id-jem (vidljiva labela, NE samo placeholder)."""
    html = _contact_html(client)
    inner = _form_inner(html)

    label_fors = _LABEL_FOR_RE.findall(inner)
    assert len(label_fors) >= 4, (
        f"Forma MORA imati bar 4 vidljiva <label for> (Ime/Email/Telefon/Poruka — AC6). "
        f"Pronađeno: {label_fors!r}"
    )

    # Svaki label for MORA referencirati postojeći input/textarea id (asocijacija).
    field_ids = set(re.findall(r"\bid=[\"']([^\"']+)[\"']", inner, re.IGNORECASE))
    for ref in label_fors:
        assert ref in field_ids, (
            f"<label for=\"{ref}\"> MORA referencirati postojeće polje sa id=\"{ref}\" "
            f"(asocijacija label↔input — a11y). Pronađeni id-jevi: {sorted(field_ids)!r}"
        )


def test_contact_submit_is_disabled(client):
    """AC6/SM-D8: submit dugme [data-testid=contact-submit] ima `disabled` + `aria-disabled`."""
    html = _contact_html(client)
    m = _SUBMIT_RE.search(html)
    assert m, (
        "Forma MORA imati submit dugme [data-testid=\"contact-submit\"] (AC6/SM-D8)."
    )
    tag = m.group(0)
    assert re.search(r"\bdisabled\b", tag, re.IGNORECASE), (
        f"Submit dugme MORA imati `disabled` (forward-compat skelet — Story 4.2 ga aktivira). "
        f"Tag: {tag!r}"
    )
    assert re.search(r"aria-disabled=[\"']true[\"']", tag, re.IGNORECASE), (
        f"Submit dugme MORA imati aria-disabled=\"true\" (a11y — AC6/SM-D8). Tag: {tag!r}"
    )


def test_contact_form_inputs_disabled_and_hint_associated(client):
    """AC6/SM-D8 (a11y silent-data-loss guard): SVA input/textarea polja imaju `disabled`;
    <form> ima aria-describedby koji referencira `id` postojećeg hint elementa.
    """
    html = _contact_html(client)
    inner = _form_inner(html)

    # Sva input/textarea polja (osim CSRF hidden inputa) MORAJU biti disabled.
    field_tags = re.findall(r"<(?:input|textarea)\b[^>]*>", inner, re.IGNORECASE)
    user_fields = [
        t for t in field_tags
        if "csrfmiddlewaretoken" not in t.lower() and 'type="hidden"' not in t.lower()
    ]
    assert user_fields, "Forma MORA imati input/textarea polja (AC6)."
    for t in user_fields:
        assert re.search(r"\bdisabled\b", t, re.IGNORECASE), (
            "SVA user input/textarea polja MORAJU biti `disabled` u v1 (a11y — sprečava "
            f"silent-data-loss; polja van tab-reda — SM-D8). Nedostaje disabled: {t!r}"
        )

    # <form> aria-describedby referencira id postojećeg hint elementa.
    form_open = _FORM_OPEN_RE.search(html)
    assert form_open, "Form open tag nije pronađen."
    m = re.search(
        r"aria-describedby=[\"']([^\"']+)[\"']", form_open.group(0), re.IGNORECASE
    )
    assert m, (
        "<form> MORA imati aria-describedby koji povezuje hint (a11y — AT objavljuje "
        "status forme; SM-D8). Form tag: " + repr(form_open.group(0))
    )
    hint_id = m.group(1).strip()
    assert hint_id, "aria-describedby vrednost ne sme biti prazna."
    assert re.search(
        rf"id=[\"']{re.escape(hint_id)}[\"']", html, re.IGNORECASE
    ), (
        f"aria-describedby=\"{hint_id}\" MORA referencirati postojeći element sa "
        f"id=\"{hint_id}\" (hint sa 'uskoro aktivna' copy-jem; SM-D8)."
    )


def test_contact_form_has_no_functional_hx_post(client):
    """AC6/SM-D8/SM-D4: forma NEMA funkcionalan submit — bez `hx-post` i bez `action`.

    method="post" BEZ action (C1) je dozvoljen (submit ide na GET-only ContactView → 405).
    Funkcionalan endpoint (/htmx/forme/kontakt/) + ContactForm su Epic 4 (Story 4.2).
    """
    html = _contact_html(client)
    form_open = _FORM_OPEN_RE.search(html)
    assert form_open, (
        "Forma <form data-testid=\"contact-form\"> mora postojati (AC6)."
    )
    tag = form_open.group(0)

    # method="post" obavezan (C1 — sprečava GET-default leak unosa u URL).
    assert re.search(r"method=[\"']post[\"']", tag, re.IGNORECASE), (
        f"<form> MORA imati method=\"post\" (C1 — sprečava GET-default URL leak). Tag: {tag!r}"
    )
    # NEMA action atributa (C1 — submit ide na ISTU GET-only putanju → 405).
    assert not re.search(r"\baction=", tag, re.IGNORECASE), (
        f"<form> NE SME imati `action` atribut u v1 (C1 — funkcionalan endpoint je Epic 4 "
        f"Story 4.2). Tag: {tag!r}"
    )
    # NEMA hx-post (HTMX funkcionalnost je Epic 4 Story 4.2/4.6).
    assert not re.search(r"hx-post=", tag, re.IGNORECASE), (
        f"<form> NE SME imati `hx-post` u v1 (HTMX submit je Epic 4 Story 4.2/4.6 — SM-D8). "
        f"Tag: {tag!r}"
    )
