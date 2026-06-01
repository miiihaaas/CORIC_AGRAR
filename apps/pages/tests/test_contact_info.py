"""Story 3.3 — AC4: Kontakt-info sekcija (adresa + telefoni prodaja/servis + email +
radno vreme + social), hardcoded-translatable, puni-dijakritik adresa, semantic + a11y.

RED phase (TEA). Regex parsiranje (projekat nema BeautifulSoup — mirror test_about_*).

RED razlog: pages/contact.html + _contact_info.html ne postoje → GET /sr/kontakt/ je
404 → parsiranje pada na status_code assertion-u.

NAPOMENA (AC8/SM-D5/OQ-6): adresa MORA biti puni-dijakritik „Vojvođanska 1, Basaid,
Srbija" (NE šišana „Vojvodjanska" koju top-header/footer nasleđuju). Tel/email VREDNOSTI
nisu prevodive — REUSE iste vrednosti kao top-header/footer (konzistentnost).

AC4 — testovi:
- test_contact_info_has_address          (<address> sa puni-dijakritik „Vojvođanska")
- test_contact_info_has_sales_and_service_phones  (>=2 tel: linka — prodaja+servis odvojeno)
- test_contact_info_has_email_mailto     (mailto: link)
- test_contact_info_has_working_hours    (radno vreme — semantic element dl/ul/table)
- test_contact_info_social_links_have_aria_label  (svaki social <a> ima neprazan aria-label)

Pokrenuti:
    just test apps/pages/tests/test_contact_info.py -v
"""

from __future__ import annotations

import re

import pytest
from django.utils.translation import activate

pytestmark = pytest.mark.django_db

_ADDRESS_RE = re.compile(r"<address\b[^>]*>(.*?)</address>", re.IGNORECASE | re.DOTALL)
_TEL_RE = re.compile(r"href=[\"']tel:([^\"']+)[\"']", re.IGNORECASE)
_MAILTO_RE = re.compile(r"href=[\"']mailto:([^\"']+)[\"']", re.IGNORECASE)
# Social <a> linkovi nose BEM klasu coric-contact-info__social-link (Facebook/Instagram).
_SOCIAL_LINK_RE = re.compile(
    r"<a\b[^>]*class=[\"'][^\"']*coric-contact-info__social-link[^\"']*[\"'][^>]*>",
    re.IGNORECASE,
)
_ARIA_LABEL_RE = re.compile(r"aria-label=[\"']([^\"']*)[\"']", re.IGNORECASE)


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


def test_contact_info_has_address(client):
    """AC4/AC8/SM-D5: <address> element sa PUNI-dijakritik adresom „Vojvođanska 1, Basaid, Srbija".

    Kontakt strana NE sme da nasledi šišanu „Vojvodjanska" (OQ-6 known debt top-header/footer).
    """
    html = _contact_html(client)
    m = _ADDRESS_RE.search(html)
    assert m, "Kontakt-info MORA imati <address> element sa adresom firme (AC4)."
    address_text = m.group(1)
    assert "Vojvođanska" in address_text, (
        "Adresa MORA biti puni-dijakritik Vojvodjanska-sa-dijakriticima (AC8/SM-D5/OQ-6, "
        f"NE sisana latinica). <address> sadrzaj: {address_text!r}"
    )
    assert "Vojvodjanska" not in address_text, (
        "Adresa NE SME koristiti sisanu latinicu (puni dijakritici "
        "obavezni na ovoj NOVOJ strani; AC8/OQ-6)."
    )


def test_contact_info_has_sales_and_service_phones(client):
    """AC4/FR-5: >=2 `tel:` linka — telefon prodaje i telefon servisa ODVOJENO."""
    html = _contact_html(client)
    tels = _TEL_RE.findall(html)
    distinct = set(tels)
    assert len(distinct) >= 2, (
        "Kontakt-info MORA imati bar 2 ODVOJENA `tel:` linka (telefon prodaje + telefon "
        f"servisa — FR-5). Pronađeni tel: brojevi: {tels!r}"
    )


def test_contact_info_has_email_mailto(client):
    """AC4: email kao `mailto:` link (REUSE prodaja@coricagrar.rs kao footer)."""
    html = _contact_html(client)
    mailtos = _MAILTO_RE.findall(html)
    assert mailtos, "Kontakt-info MORA imati bar 1 `mailto:` link (email firme — AC4)."


def test_contact_info_has_working_hours(client):
    """AC4: radno vreme prisutno u semantičkom elementu (<dl> ILI <ul> ILI <table>).

    Dev bira semantic element; test prihvata bilo koji od dozvoljenih (čitljiv AT-u).
    """
    html = _contact_html(client)
    has_semantic = re.search(r"<(dl|ul|ol|table)\b", html, re.IGNORECASE)
    assert has_semantic, (
        "Kontakt-info MORA renderovati radno vreme u semantičkom elementu "
        "(<dl>/<ul>/<table> — čitljiv AT-u; AC4/SM-D5)."
    )


def test_contact_info_social_links_have_aria_label(client):
    """AC4/a11y: svaki social <a> (Facebook/Instagram) ima NEPRAZAN aria-label.

    Social linkovi nose samo SVG ikonu (aria-hidden), pa accessible naziv MORA doći
    iz aria-label-a — inače je link nedostupan za screen reader (WCAG 2.1 AA).
    """
    html = _contact_html(client)
    social_links = _SOCIAL_LINK_RE.findall(html)
    assert social_links, (
        "Kontakt-info MORA imati social linkove sa klasom "
        "'coric-contact-info__social-link' (Facebook/Instagram — AC4)."
    )
    for link_tag in social_links:
        m = _ARIA_LABEL_RE.search(link_tag)
        assert m and m.group(1).strip(), (
            "Svaki social <a> MORA imati NEPRAZAN aria-label (ikona je aria-hidden, "
            f"naziv nosi aria-label; AC4/WCAG). Link tag bez aria-label-a: {link_tag!r}"
        )
