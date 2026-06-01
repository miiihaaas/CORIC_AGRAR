"""Story 3.3 — AC5: Google Maps static iframe (NULA JS) + a11y title + lazy + C2 fallback link.

RED phase (TEA). Regex parsiranje (projekat nema BeautifulSoup — mirror test_about_*).

RED razlog: pages/contact.html + _contact_map.html ne postoje → GET /sr/kontakt/ je
404 → parsiranje pada na status_code assertion-u.

AC5 — testovi:
- test_contact_map_has_iframe              (<iframe> prisutan)
- test_contact_map_iframe_has_title        (neprazan title atribut — WCAG a11y)
- test_contact_map_iframe_lazy_loaded      (loading="lazy")
- test_contact_map_iframe_has_referrerpolicy  (referrerpolicy atribut — SM-D6 lock)
- test_contact_map_has_fallback_link       (C2 — fallback <a> ka Google Mapama, opisni tekst,
                                            rel=noopener noreferrer)

Pokrenuti:
    just test apps/pages/tests/test_contact_map.py -v
"""

from __future__ import annotations

import re

import pytest
from django.utils.translation import activate

pytestmark = pytest.mark.django_db

_IFRAME_RE = re.compile(r"<iframe\b[^>]*>", re.IGNORECASE)
# Fallback <a> ka Google Mapama (maps.google.com / google.com/maps) sa tekstom.
_MAPS_LINK_RE = re.compile(
    r"<a\b[^>]*href=[\"'][^\"']*maps\.google[^\"']*[\"'][^>]*>(.*?)</a>",
    re.IGNORECASE | re.DOTALL,
)


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


def _attr_of(tag: str, attr: str) -> str | None:
    m = re.search(rf"{attr}=[\"']([^\"']*)[\"']", tag, re.IGNORECASE)
    return m.group(1) if m else None


def test_contact_map_has_iframe(client):
    """AC5/SM-D6: static <iframe> Google Maps embed prisutan (NULA JS)."""
    html = _contact_html(client)
    iframes = _IFRAME_RE.findall(html)
    assert iframes, (
        "Mapa sekcija MORA imati <iframe> (Google Maps static embed — AC5/SM-D6)."
    )


def test_contact_map_iframe_has_title(client):
    """AC5/a11y (KRITIČNO): <iframe> ima NEPRAZAN `title` atribut (NVDA accessible naziv)."""
    html = _contact_html(client)
    iframes = _IFRAME_RE.findall(html)
    assert iframes, "Mapa MORA imati <iframe> (AC5)."
    iframe = iframes[0]
    title = _attr_of(iframe, "title")
    assert title is not None and title.strip(), (
        "Google Maps <iframe> MORA imati neprazan `title` atribut (WCAG 2.1 AA — bez "
        f"title-a iframe je nedostupan za NVDA). Iframe tag: {iframe!r}"
    )


def test_contact_map_iframe_lazy_loaded(client):
    """AC5/perf: <iframe> ima loading="lazy" (ispod fold-a; third-party performance)."""
    html = _contact_html(client)
    iframes = _IFRAME_RE.findall(html)
    assert iframes, "Mapa MORA imati <iframe> (AC5)."
    iframe = iframes[0]
    loading = _attr_of(iframe, "loading")
    assert loading is not None and loading.lower() == "lazy", (
        'Google Maps <iframe> MORA imati loading="lazy" (AC5 — performance). '
        f"Iframe tag: {iframe!r}"
    )


def test_contact_map_iframe_has_referrerpolicy(client):
    """AC5/SM-D6: <iframe> ima `referrerpolicy` atribut (kontrakt/SM-D6 lock; defense-in-depth).

    Asertira PRISUSTVO (neprazan) atributa, NE specifičnu vrednost — tako test ostaje
    konzistentan i ako se vrednost zaoštri (npr. strict-origin-when-cross-origin).
    """
    html = _contact_html(client)
    iframes = _IFRAME_RE.findall(html)
    assert iframes, "Mapa MORA imati <iframe> (AC5)."
    iframe = iframes[0]
    referrerpolicy = _attr_of(iframe, "referrerpolicy")
    assert referrerpolicy is not None and referrerpolicy.strip(), (
        "Google Maps <iframe> MORA imati neprazan `referrerpolicy` atribut "
        f"(SM-D6 lock — standardni Google embed atribut). Iframe tag: {iframe!r}"
    )


def test_contact_map_has_fallback_link(client):
    """AC5/C2 (KRITIČNO — EDGE-CASE iframe blokiran): map wrapper sadrži vidljiv fallback
    `<a>` ka Google Mapama sa NEPRAZNIM opisnim tekstom linka (NE goli URL).

    Fallback je čist HTML/CSS (NULA JS) — korisnik dođe do lokacije i kad iframe ne radi
    (privacy/tracker blocker, firewall, buduća CSP frame-src).
    """
    html = _contact_html(client)
    m = _MAPS_LINK_RE.search(html)
    assert m, (
        "Mapa wrapper MORA imati fallback <a href=...maps.google...> link "
        "(C2 - iframe blokiran scenario; pristup lokaciji bez iframe-a)."
    )
    link_tag = m.group(0)
    # Opisni tekst linka (NE goli URL) — strip tagova iz unutrašnjosti.
    inner_text = re.sub(r"<[^>]+>", "", m.group(1)).strip()
    assert inner_text, (
        "Fallback Google Maps link MORA imati NEPRAZAN opisni tekst (npr. Otvori "
        "lokaciju u Google Mapama; NE goli URL; accessible naziv linka; C2/AC5)."
    )
    # rel/target su deo C2 kontrakta (rel="noopener noreferrer" + target="_blank").
    link_tag_lower = link_tag.lower()
    assert "noopener" in link_tag_lower, (
        "Fallback link MORA imati rel sa noopener (target=_blank sigurnost; C2). "
        f"Link tag: {link_tag!r}"
    )
    assert "noreferrer" in link_tag_lower, (
        'Fallback link MORA imati rel sa noreferrer (kontrakt lock rel="noopener '
        f'noreferrer"; privacy — ne curi referrer ka Google Mapama; C2). Link tag: {link_tag!r}'
    )
