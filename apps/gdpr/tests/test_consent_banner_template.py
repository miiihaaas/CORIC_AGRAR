"""Story 7.2 — AC6/AC10: baner partial a11y + GDPR equal-prominence (TEA RED).

Pokriva AC6 + AC10 + SM-D4/D13 + Gotcha G-13:
- root: role="dialog", aria-modal="false", aria-labelledby koji rezolvuje na
  POSTOJECI id u markup-u, data-coric-gdpr-banner hook, tabindex="-1".
- forma: method=post, action==reverse("gdpr:set_consent"), {% csrf_token %}.
- 3 kategorije: Neophodan (checked+disabled), Analitički (name=analytical,
  BEZ checked), Marketing (name=marketing, BEZ checked).
- 3 submit dugmeta: name=action values accept_all/reject_all/save.
- AC10/CRITICAL-3: „Odbij sve" i „Prihvati sve" oba `<button type="submit">` i
  dele istu osnovnu button-komponentnu klasu (jednaka prominentnost); „Odbij sve"
  NIJE faint `<a>`/link.
- AC10: opcioni checkbox-i (Analitički/Marketing) BEZ `checked`.
- UI string-ovi pune dijakritike.

RED razlog: `templates/gdpr/_consent_banner.html` ne postoji →
render_to_string baca TemplateDoesNotExist (ili reverse('gdpr:set_consent')
NoReverseMatch unutar partial-a).

⚠️ HTML parsing kroz `re` (NO BeautifulSoup — project-context.md).

Pokrenuti:
    docker compose -f compose/local.yml run --rm django \
        uv run pytest apps/gdpr/tests/test_consent_banner_template.py -v

Refs: 7-2 AC6/AC10 + SM-D4/D13 + Gotcha G-13; 7-2-interface-contract § 4.
"""

from __future__ import annotations

import re

import pytest
from django.template.loader import render_to_string
from django.test import RequestFactory
from django.utils.translation import override

pytestmark = pytest.mark.django_db

BANNER_TEMPLATE = "gdpr/_consent_banner.html"


def _render_banner(path="/sr/"):
    """Renderuj baner partial sa request-om (csrf_token/{% url %}/{% translate %})."""
    request = RequestFactory().get(path)
    return render_to_string(
        BANNER_TEMPLATE, {"next": request.get_full_path()}, request=request
    )


# AC6: root ima role="dialog" + aria-modal="false" (NON-blokirajuci)
def test_role_dialog_and_aria_modal_false():
    with override("sr"):
        html = _render_banner()
    assert 'role="dialog"' in html, (
        f"Baner root MORA imati role=\"dialog\" (AC6/SM-D4). Dobio: {html!r}"
    )
    assert 'aria-modal="false"' in html, (
        "Baner root MORA imati aria-modal=\"false\" (NON-blokirajuci; NE focus-trap; "
        f"AC6/SM-D4). Dobio: {html!r}"
    )


# AC6: aria-labelledby vrednost == id postojeceg heading elementa u markup-u
def test_aria_labelledby_resolves():
    with override("sr"):
        html = _render_banner()
    m = re.search(r'aria-labelledby=["\']([^"\']+)["\']', html)
    assert m, f"Baner MORA imati aria-labelledby (AC6). Dobio: {html!r}"
    target_id = m.group(1)
    assert re.search(rf'id=["\']{re.escape(target_id)}["\']', html), (
        f"aria-labelledby=\"{target_id}\" MORA pokazivati na POSTOJECI id u markup-u "
        f"(heading; AC6/SM-D4). Nijedan element nema id=\"{target_id}\". Dobio: {html!r}"
    )


# AC6/AC7: root ima data-coric-gdpr-banner hook + tabindex="-1" (za JS root-focus)
def test_root_has_js_hook_and_tabindex():
    with override("sr"):
        html = _render_banner()
    assert "data-coric-gdpr-banner" in html, (
        f"Baner root MORA imati data-coric-gdpr-banner JS hook (AC6/AC7). Dobio: {html!r}"
    )
    # tabindex="-1" da JS `.focus()` na root radi (pinovan root-focus; AC7/SM-D10)
    m = re.search(r'data-coric-gdpr-banner[^>]*tabindex=["\']-1["\']', html)
    if not m:
        m = re.search(r'tabindex=["\']-1["\'][^>]*data-coric-gdpr-banner', html)
    assert m, (
        "Baner root (data-coric-gdpr-banner) MORA imati tabindex=\"-1\" da JS "
        f".focus() na root radi (AC7/SM-D10). Dobio: {html!r}"
    )


# AC6: forma method=post + action==reverse("gdpr:set_consent")
def test_form_action_is_set_consent():
    from django.urls import reverse

    with override("sr"):
        html = _render_banner()
        action_url = reverse("gdpr:set_consent")
    m = re.search(r"<form[^>]*>", html, re.IGNORECASE)
    assert m, f"Baner MORA imati <form> (AC6). Dobio: {html!r}"
    form_tag = m.group(0)
    assert re.search(r'method=["\']post["\']', form_tag, re.IGNORECASE), (
        f"Baner forma MORA biti method=post (AC6). Dobio: {form_tag!r}"
    )
    assert action_url in form_tag, (
        f"Baner forma action MORA biti reverse('gdpr:set_consent') (={action_url!r}; AC6). "
        f"Dobio: {form_tag!r}"
    )


# AC6/G-2: forma sadrži {% csrf_token %}
def test_form_has_csrf_token():
    with override("sr"):
        html = _render_banner()
    assert re.search(r'name=["\']csrfmiddlewaretoken["\']', html, re.IGNORECASE), (
        f"Baner forma MORA sadržati {{% csrf_token %}} (G-2). Dobio: {html!r}"
    )


# AC6: Neophodan checkbox = checked + disabled (uvek-ukljucen)
def test_necessary_checkbox_checked_and_disabled():
    with override("sr"):
        html = _render_banner()
    # nadji checkbox input-e; Neophodan je jedini checked + disabled
    necessary = re.findall(
        r'<input[^>]*type=["\']checkbox["\'][^>]*>', html, re.IGNORECASE
    )
    assert necessary, f"Baner MORA imati checkbox kategorije (AC6). Dobio: {html!r}"
    # bar jedan checkbox MORA biti checked I disabled (Neophodan)
    checked_disabled = [
        c for c in necessary if "checked" in c.lower() and "disabled" in c.lower()
    ]
    assert checked_disabled, (
        "Neophodan checkbox MORA biti `checked` + `disabled` (uvek-ukljucen, "
        f"ne moze da se iskljuci; AC6/AC10). Checkbox-i: {necessary!r}"
    )


# AC6/AC10/G-13: Analitički + Marketing checkbox-i BEZ `checked` (default ODČEKIRANI)
def test_optional_checkboxes_default_unchecked():
    with override("sr"):
        html = _render_banner()
    for name in ("analytical", "marketing"):
        m = re.search(
            rf'<input[^>]*name=["\']{name}["\'][^>]*>', html, re.IGNORECASE
        )
        assert m, (
            f"Baner MORA imati checkbox name=\"{name}\" (AC6). Dobio: {html!r}"
        )
        tag = m.group(0)
        assert "checked" not in tag.lower(), (
            f"{name} checkbox MORA biti podrazumevano ODCEKIRAN (BEZ `checked` "
            "atributa) — GDPR nema pre-ticked ne-neophodnih kategorija (AC10/"
            f"CRITICAL-3/G-13). Dobio: {tag!r}"
        )


# AC6: 3 submit dugmeta name=action values accept_all/reject_all/save
def test_three_action_buttons():
    with override("sr"):
        html = _render_banner()
    for value in ("accept_all", "reject_all", "save"):
        m = re.search(
            rf'<button[^>]*name=["\']action["\'][^>]*value=["\']{value}["\']',
            html,
            re.IGNORECASE,
        )
        if not m:
            m = re.search(
                rf'<button[^>]*value=["\']{value}["\'][^>]*name=["\']action["\']',
                html,
                re.IGNORECASE,
            )
        assert m, (
            f"Baner MORA imati <button name=\"action\" value=\"{value}\"> (AC6). "
            f"Dobio: {html!r}"
        )


# AC10/CRITICAL-3/G-13: „Odbij sve" i „Prihvati sve" oba <button type=submit> + ista klasa
def test_reject_equal_prominence_to_accept():
    with override("sr"):
        html = _render_banner()

    def _button_tag(value):
        m = re.search(
            rf'<button[^>]*value=["\']{value}["\'][^>]*>',
            html,
            re.IGNORECASE,
        )
        return m.group(0) if m else None

    accept = _button_tag("accept_all")
    reject = _button_tag("reject_all")
    assert accept and reject, (
        f"Prihvati sve (accept_all) i Odbij sve (reject_all) MORAJU biti "
        f"<button> elementi (AC10/G-13). accept={accept!r} reject={reject!r}"
    )
    # oba MORAJU biti type="submit" (NE faint <a> link)
    assert re.search(r'type=["\']submit["\']', accept, re.IGNORECASE), (
        f"Prihvati sve MORA biti type=\"submit\" (AC10). Dobio: {accept!r}"
    )
    assert re.search(r'type=["\']submit["\']', reject, re.IGNORECASE), (
        "Odbij sve MORA biti <button type=\"submit\">, NE faint <a>/link "
        f"(GDPR equal-prominence; AC10/CRITICAL-3/G-13). Dobio: {reject!r}"
    )

    # oba MORAJU deliti istu osnovnu button-komponentnu klasu (jednaka prominentnost)
    def _classes(tag):
        cm = re.search(r'class=["\']([^"\']*)["\']', tag, re.IGNORECASE)
        return set(cm.group(1).split()) if cm else set()

    accept_classes = _classes(accept)
    reject_classes = _classes(reject)
    shared = accept_classes & reject_classes
    assert shared, (
        "Odbij sve i Prihvati sve MORAJU deliti bar jednu zajednicku button-"
        "komponentnu klasu (npr. `.coric-gdpr-banner__action`) — jednaka "
        "prominentnost (AC10/CRITICAL-3/G-13; razlika sme biti SAMO boja/akcenat). "
        f"accept klase={accept_classes!r}, reject klase={reject_classes!r}."
    )


# AC6: „Više info" href == reverse("gdpr:cookie_policy")
def test_more_info_href():
    from django.urls import reverse

    with override("sr"):
        html = _render_banner()
        policy_url = reverse("gdpr:cookie_policy")
    assert re.search(
        rf'<a[^>]*href=["\']{re.escape(policy_url)}["\']', html, re.IGNORECASE
    ), (
        f"Vise info MORA biti <a href=\"{policy_url}\"> (reverse('gdpr:cookie_policy'); "
        f"AC6). Dobio: {html!r}"
    )


# AC6/G-11: UI string-ovi koriste pune dijakritike (č/ć/ž/š/đ)
def test_ui_strings_use_full_diacritics():
    with override("sr"):
        html = _render_banner()
    # bar nekoliko očekivanih dijakritičnih UI string-ova (Prihvati sve je ASCII —
    # proveravamo one koji NOSE dijakritike: Analitički / Više info / Sačuvaj izbor /
    # Neophodan kolačić itd.)
    expected_any = ["Analitički", "Više info", "Sačuvaj", "kolačić"]
    present = [s for s in expected_any if s in html]
    assert present, (
        "Baner UI MORA koristiti pune dijakritike (č/ć/ž/š/đ) u srpskim string-ovima "
        f"(G-11) — npr. {expected_any!r}. Nijedan nije pronadjen. Dobio: {html!r}"
    )
