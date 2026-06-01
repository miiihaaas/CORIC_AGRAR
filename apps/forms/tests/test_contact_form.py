"""Story 4.2 — AC1: ContactForm (server-side validation SOT) — TEA RED phase.

Pokriva AC1: polja postoje (name/email/phone/message); name/email/message obavezni;
phone opciono; nevalidan email → invalid; validan payload → valid; message je
`required=True` NA FORMI iako je Lead.message blank=True na modelu (forma je ulazna
kapija, model je storage); labele/error poruke kroz gettext (pune dijakritike, NEMA
ćirilice/šišane latinice).

RED razlog: `apps.forms.forms` ne postoji → ImportError (svi testovi padaju u import-u).

Pokrenuti:
    just test apps/forms/tests/test_contact_form.py -v

Refs: 4-2-opsta-kontakt-forma-fr-5.md AC1 + Task 1.2; interface-contract § 1.
"""

from __future__ import annotations

from django.utils.translation import activate


# AC-1: forma ima TAČNO 4 polja name/email/phone/message
def test_contact_form_has_expected_fields():
    from apps.forms.forms import ContactForm

    form = ContactForm()
    assert set(form.fields) == {"name", "email", "phone", "message"}, (
        f"ContactForm MORA imati polja name/email/phone/message, dobio {set(form.fields)!r}."
    )


# AC-1: validan kompletan payload → is_valid() True
def test_contact_form_valid_payload(valid_contact_payload):
    from apps.forms.forms import ContactForm

    form = ContactForm(data=valid_contact_payload)
    assert form.is_valid(), (
        f"Kompletan validan payload MORA biti validan, errors={form.errors!r}."
    )


# AC-1: prazno name → invalid sa per-field greškom
def test_contact_form_name_required(valid_contact_payload):
    from apps.forms.forms import ContactForm

    payload = {**valid_contact_payload, "name": ""}
    form = ContactForm(data=payload)
    assert not form.is_valid(), "Prazno `name` MORA učiniti formu nevalidnom (AC1)."
    assert "name" in form.errors, "Greška MORA biti per-field na `name`."


# AC-1: prazno email → invalid
def test_contact_form_email_required(valid_contact_payload):
    from apps.forms.forms import ContactForm

    payload = {**valid_contact_payload, "email": ""}
    form = ContactForm(data=payload)
    assert not form.is_valid(), "Prazno `email` MORA učiniti formu nevalidnom (AC1)."
    assert "email" in form.errors, "Greška MORA biti per-field na `email`."


# AC-1: nevalidan email format → invalid
def test_contact_form_email_format_invalid(valid_contact_payload):
    from apps.forms.forms import ContactForm

    payload = {**valid_contact_payload, "email": "ovo-nije-email"}
    form = ContactForm(data=payload)
    assert not form.is_valid(), "Nevalidan email format MORA biti odbijen (AC1)."
    assert "email" in form.errors, "Greška MORA biti per-field na `email`."


# AC-1: message je required NA FORMI (iako Lead.message blank=True na modelu)
def test_contact_form_message_required(valid_contact_payload):
    from apps.forms.forms import ContactForm

    payload = {**valid_contact_payload, "message": ""}
    form = ContactForm(data=payload)
    assert not form.is_valid(), (
        "Prazno `message` MORA biti nevalidno NA FORMI (AC1 — forma je SOT, model je "
        "samo storage; Lead.message blank=True se NE menja)."
    )
    assert "message" in form.errors, "Greška MORA biti per-field na `message`."


# AC-1: phone je OPCIONO — prazno phone + ostala validna polja → valid
def test_contact_form_phone_optional(valid_contact_payload):
    from apps.forms.forms import ContactForm

    payload = {**valid_contact_payload, "phone": ""}
    form = ContactForm(data=payload)
    assert form.is_valid(), (
        f"Prazno `phone` (opciono) NE SME učiniti formu nevalidnom, errors={form.errors!r}."
    )


# AC-1/AC-9: labele kroz gettext — pune dijakritike, NIKAD ćirilica/šišana latinica
def test_contact_form_labels_full_diacritics_no_cyrillic():
    from apps.forms.forms import ContactForm

    activate("sr")
    labels = " ".join(str(f.label) for f in ContactForm().fields.values())

    # Bar jedna dijakritika prisutna (E-pošta / Poruka koriste š, a UI je sr-latinica)
    assert any(ch in labels for ch in "čćžšđ"), (
        f"Labela mora koristiti pune dijakritike (č/ć/ž/š/đ) — sr latinica. Labele: {labels!r}."
    )
    # NIKAD ćirilica u UI string-ovima (project-context anti-pattern)
    cyrillic = [ch for ch in labels if "Ѐ" <= ch <= "ӿ"]
    assert not cyrillic, f"Labele NE SMEJU sadržati ćirilicu, pronađeno: {cyrillic!r}."


# AC-9 (TEST_GAP/TEA): error poruke su TAKOĐE user-facing — pune dijakritike, NEMA ćirilice.
# Asertuje SAMO poruke koje ContactForm EKSPLICITNO definiše preko gettext-a (required/invalid),
# tj. one koje renderuje na nevalidan submit. (Django built-in default poruke se ovde NE testiraju
# — njihov sr prevod je ćirilica iz Django bundle-a, što forma override-uje gde je user-facing.)
def test_contact_form_error_messages_full_diacritics_no_cyrillic():
    from apps.forms.forms import ContactForm

    activate("sr")
    form = ContactForm()
    # Skupi TAČNO gettext-ovane poruke definisane na formi (required za name/email/message,
    # invalid za email) — to su poruke prikazane korisniku na nevalidnom unosu.
    rendered = " ".join(
        str(form.fields[name].error_messages[key])
        for name, key in (
            ("name", "required"),
            ("email", "required"),
            ("email", "invalid"),
            ("message", "required"),
        )
    )

    # Bar jedna dijakritika prisutna (poruke koriste š u „e-pošta")
    assert any(ch in rendered for ch in "čćžšđ"), (
        f"Form error poruke moraju koristiti pune dijakritike (č/ć/ž/š/đ). Poruke: {rendered!r}."
    )
    # NIKAD ćirilica u user-facing error porukama koje forma definiše
    cyrillic = [ch for ch in rendered if "Ѐ" <= ch <= "ӿ"]
    assert not cyrillic, f"Form error poruke NE SMEJU sadržati ćirilicu, pronađeno: {cyrillic!r}."
