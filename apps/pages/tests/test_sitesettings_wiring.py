"""Story 3.4 — AC8+AC9+AC10: WIRING contact-info + footer + top-header (Task 9.7/9.8/9.9).

RED phase (TEA). Regex parsiranje (projekat nema BeautifulSoup — mirror test_contact_info.py).

Verifikuje da vrednosti DOLAZE iz SiteSettings (NE hardkodovani literali):
- contact-info: adresa puni-dijakritik iz seed-a; radno vreme render kao <ul>/<li> (NE <dl>)
  preko working_hours|splitlines; IMP-SiteSettings marker uklonjen/RESOLVED; auto-escape (NE |safe)
- footer + top-header: koriste site_setting; IMP-4 servis placeholder razrešen
- social HIDE-WHEN-EMPTY (SM-D8a): prazan seed → NEMA href=""/href="#" social link; popunjen URL → renderovan
- tel: href BEZ razmaka (|cut:" "); vidljiv tekst SA razmacima
- _home_hero.html slogan NETAKNUT (3-1 SM-D10 regresija)
- sva 3 locale (sr/hu/en) 200 za /kontakt/ i /; nema ćirilice na sr renderu

RED razlog: site_settings tag library ne postoji → {% load site_settings %} u wired template-ima
baca TemplateSyntaxError → GET /sr/kontakt/ i /sr/ 500/render error → status != 200. Dok template
NIJE wired, working_hours je još <dl> (NE <ul> iz splitlines) i IMP markeri su prisutni.

Dev NE piše testove. Pokrenuti:
    just test apps/pages/tests/test_sitesettings_wiring.py -v
"""

from __future__ import annotations

import re

import pytest
from django.utils.translation import activate

pytestmark = pytest.mark.django_db

_HOURS_UL_RE = re.compile(
    r"<ul\b[^>]*coric-contact-info__hours-list[^>]*>(.*?)</ul>",
    re.IGNORECASE | re.DOTALL,
)
_LI_RE = re.compile(r"<li\b[^>]*>(.*?)</li>", re.IGNORECASE | re.DOTALL)
_TEL_RE = re.compile(r"href=[\"']tel:([^\"']+)[\"']", re.IGNORECASE)
# Cirilica (osnovni opseg)
_CYRILLIC_RE = re.compile(r"[Ѐ-ӿ]")


def _get(client, path: str, lang: str = "sr") -> str:
    activate(lang)
    response = client.get(path)
    assert response.status_code == 200, (
        f"GET {path} MORA biti 200 da bi se HTML parsirao, dobio {response.status_code} "
        f"(RED: {{% load site_settings %}} u wired template-u baca TemplateSyntaxError "
        f"dok templatetags/site_settings.py ne postoji)."
    )
    return response.content.decode("utf-8")


# ============================================================================
# AC8 — contact-info wiring
# ============================================================================


def test_contact_info_address_from_seed_full_diacritic(client):
    """AC8: kontakt-info adresa je puni-dijakritik iz seed-a (čita se kroz site_setting).

    OJAČAN (TEA review): rendered-value provera je VACUOUS u RED-u (hardkodovani
    `{% translate "Vojvođanska…" %}` literal već daje 'Vojvođanska'). Da test PADNE u
    RED-u i dokaže da vrednost DOLAZI iz SiteSettings (NE hardkodovan literal),
    dodatno verifikujemo template IZVOR: adresa MORA biti wired kroz
    `{% site_setting "address" %}` (NE hardkodovan `{% translate "Vojvođanska" %}`).
    NAPOMENA: IMP-marker komentar (`:3`) sadrži bare `{% site_setting %}` BEZ arg-a,
    pa tražimo specifično `site_setting "address"` da ne uhvatimo komentar.
    """
    import pathlib

    contact_info = pathlib.Path(
        "templates/pages/partials/_contact_info.html"
    ).read_text(encoding="utf-8")
    assert re.search(r"site_setting\s+[\"']address[\"']", contact_info), (
        "Kontakt-info adresa MORA biti wired kroz {% site_setting \"address\" %} "
        "(NE hardkodovan {% translate \"Vojvođanska…\" %} literal; AC8/SM-D7). RED: "
        "template još drži hardkodovan literal."
    )
    assert not re.search(
        r"{%\s*translate\s+[\"']Vojvo[^\"']*[\"']\s*%}", contact_info
    ), (
        "Posle wiring-a adresa NE SME ostati hardkodovan {% translate \"Vojvo…\" %} "
        "literal — MORA se čitati iz SiteSettings (AC8)."
    )

    html = _get(client, "/sr/kontakt/")
    m = re.search(r"<address\b[^>]*>(.*?)</address>", html, re.IGNORECASE | re.DOTALL)
    assert m, "Kontakt-info MORA imati <address> element."
    assert "Vojvođanska" in m.group(1), (
        f"Kontakt-info adresa MORA biti puni-dijakritik iz SiteSettings seed-a "
        f"('Vojvođanska'; AC8), dobio {m.group(1)!r}."
    )


def test_working_hours_rendered_as_ul_from_splitlines(client):
    """AC8/SM-D10: radno vreme render kao <ul> sa <li> po liniji (NE više 3-redni <dl>).

    Ovaj test FAIL-uje dok je template još <dl> (RED) — dokazuje da working_hours dolazi
    iz SiteSettings.working_hours|splitlines, NE iz hardkodovanog <dl> bloka.
    """
    html = _get(client, "/sr/kontakt/")
    m = _HOURS_UL_RE.search(html)
    assert m, (
        "Radno vreme MORA biti renderovano kao <ul class='coric-contact-info__hours-list'> "
        "(zamenjuje stari <dl>; SM-D10). Verifikuj working_hours|splitlines petlju."
    )
    li_items = _LI_RE.findall(m.group(1))
    assert len(li_items) >= 2, (
        f"Radno vreme <ul> MORA imati ≥2 <li> (jedan po liniji working_hours seed-a; "
        f"SM-D10), dobio {len(li_items)}: {li_items!r}."
    )
    # auto-escape — NEMA |safe → tekst je escaped (npr. & ne sme proći kao raw HTML).
    # Provera da je render čist tekst (bez ugnježdenih tagova u <li>).
    for item in li_items:
        assert "<" not in item.strip(), (
            f"<li> sadržaj MORA biti čist tekst (NEMA |safe / raw HTML; SM-D10), dobio "
            f"{item!r}."
        )


def test_imp_sitesettings_marker_resolved(client):
    """AC8: IMP-SiteSettings(Story 3-4) marker je UKLONJEN ili promenjen u RESOLVED."""
    # Smoke: stranica se renderuje bez greske (binding se ne koristi — proverava se izvor template-a)
    _get(client, "/sr/kontakt/")
    # Render NE bi smeo nositi otvoren (nerešen) IMP-SiteSettings marker. Template komentari
    # se NE renderuju, pa proveravamo izvor template-a direktno.
    import pathlib

    contact_info = pathlib.Path(
        "templates/pages/partials/_contact_info.html"
    ).read_text(encoding="utf-8")
    # Dozvoljeno „RESOLVED"; zabranjeno nerešen marker bez RESOLVED oznake.
    open_markers = [
        ln
        for ln in contact_info.splitlines()
        if "IMP-SiteSettings" in ln and "RESOLVED" not in ln
    ]
    assert not open_markers, (
        f"IMP-SiteSettings(Story 3-4) marker MORA biti uklonjen ili označen 'RESOLVED' "
        f"posle wiring-a (AC8), pronađeno otvoreno: {open_markers!r}."
    )


def test_contact_tel_href_has_no_spaces(client):
    """AC8/SM-D8: tel: href BEZ razmaka (|cut:" "), vidljiv tekst SA razmacima ostaje.

    OJAČAN (TEA review): „href bez razmaka" je VACUOUS u RED-u (hardkodovani
    `href="tel:+381230468168"` literal već nema razmake). Da test PADNE u RED-u i
    dokaže da je href GENERISAN iz SiteSettings kroz `|cut:" "` (NE hardkodovan),
    dodatno verifikujemo template IZVOR: hardkodovan `tel:+381230468168` literal MORA
    biti uklonjen, a `|cut:" "` filter prisutan na phone vrednosti.
    """
    import pathlib

    contact_info = pathlib.Path(
        "templates/pages/partials/_contact_info.html"
    ).read_text(encoding="utf-8")
    assert "tel:+381230468168" not in contact_info, (
        "Posle wiring-a hardkodovan href=\"tel:+381230468168\" MORA biti uklonjen — "
        "href se GENERIŠE iz {% site_setting %} kroz |cut:\" \" (SM-D8). RED: literal "
        "još prisutan."
    )
    assert 'cut:" "' in contact_info or "cut:' '" in contact_info, (
        "tel: href MORA koristiti Django built-in |cut:\" \" filter da skine razmake "
        "(SM-D8 locked pattern). RED: filter nije primenjen."
    )

    html = _get(client, "/sr/kontakt/")
    tels = _TEL_RE.findall(html)
    assert tels, "Kontakt-info MORA imati bar 1 tel: link."
    for tel in tels:
        assert " " not in tel, (
            f"tel: href NE SME sadržati razmake (|cut:' '; SM-D8), dobio tel:{tel!r}."
        )
    # Vidljiv tekst SA razmacima i dalje prisutan (čitljiv broj)
    assert "+381 230 468 168" in html, (
        "Vidljiv tekst telefona MORA ostati SA razmacima ('+381 230 468 168'; SM-D8)."
    )


# ============================================================================
# AC9 — footer + top-header wiring
# ============================================================================


def test_footer_address_full_diacritic_from_seed(client):
    """AC9: footer adresa čita iz seed-a → puni-dijakritik (popravlja šišanu 'Vojvodjanska')."""
    html = _get(client, "/sr/")
    # Footer je global → render home sadrži footer. Adresa MORA biti puni-dijakritik.
    assert "Vojvođanska" in html, (
        "Footer (kroz site_setting) MORA renderovati puni-dijakritik adresu 'Vojvođanska' "
        "(AC9 — popravlja šišanu 'Vojvodjanska' iz hardkodovanog footer-a)."
    )
    assert "Vojvodjanska" not in html, (
        "Posle wiring-a NE SME ostati šišana 'Vojvodjanska' (footer/header čitaju puni "
        "seed; AC9/OQ-6)."
    )


def test_imp4_service_placeholder_resolved():
    """AC9: header.html IMP-4 servis placeholder marker je uklonjen/RESOLVED."""
    import pathlib

    header = pathlib.Path("templates/partials/header.html").read_text(encoding="utf-8")
    open_markers = [
        ln for ln in header.splitlines() if "IMP-4" in ln and "RESOLVED" not in ln
    ]
    assert not open_markers, (
        f"IMP-4 servis placeholder marker MORA biti uklonjen/RESOLVED posle wiring-a na "
        f"phone_service (AC9), pronađeno otvoreno: {open_markers!r}."
    )


def test_social_hidden_when_empty(client):
    """AC8/AC9/SM-D8a: prazan social URL (seed default) → NEMA href=""/href="#" social link."""
    # Seed je prazan social → social linkovi se NE renderuju (HIDE-WHEN-EMPTY).
    for path in ("/sr/", "/sr/kontakt/"):
        html = _get(client, path)
        # Nijedan social-link <a> NE sme imati href="" ni href="#".
        empty_social = re.findall(
            r"<a\b[^>]*class=[\"'][^\"']*social-link[^\"']*[\"'][^>]*href=[\"'](#|)[\"']",
            html,
            re.IGNORECASE,
        )
        also_empty = re.findall(
            r"<a\b[^>]*href=[\"'](#|)[\"'][^>]*class=[\"'][^\"']*social-link",
            html,
            re.IGNORECASE,
        )
        assert not empty_social and not also_empty, (
            f"Sa praznim social seed-om, social linkovi MORAJU biti SAKRIVENI (NEMA "
            f"href=''/href='#'; SM-D8a) na {path}, pronađeno: "
            f"{empty_social + also_empty!r}."
        )


def test_social_rendered_when_url_present(client):
    """AC8/SM-D8a: kad je social URL popunjen → link se RENDERUJE sa tim href-om."""
    from apps.pages.models import SiteSettings

    obj = SiteSettings.load()
    obj.social_facebook = "https://facebook.com/coricagrar"
    obj.save()

    html = _get(client, "/sr/kontakt/")
    assert "https://facebook.com/coricagrar" in html, (
        "Kad je social_facebook popunjen, link MORA biti renderovan sa tim href-om "
        "(SM-D8a — HIDE samo kad je prazno)."
    )


def test_home_hero_slogan_untouched():
    """AC9/3-1 SM-D10 regresija: _home_hero.html slogan NIJE wired na site_setting."""
    import pathlib

    hero = pathlib.Path("templates/pages/partials/_home_hero.html").read_text(encoding="utf-8")
    assert "site_setting" not in hero, (
        "_home_hero.html slogan NE SME biti wired na {% site_setting %} (3-1 SM-D10 lock "
        "— slogan ostaje hardcoded-translatable; SM-D7)."
    )


# ============================================================================
# AC10 — i18n / locale
# ============================================================================


@pytest.mark.parametrize("lang", ["sr", "hu", "en"])
def test_contact_page_renders_all_locales(client, lang):
    """AC10: /<lang>/kontakt/ → HTTP 200 za sva 3 locale posle wiring-a."""
    html = _get(client, f"/{lang}/kontakt/", lang=lang)
    assert html, f"GET /{lang}/kontakt/ MORA renderovati neprazan HTML (AC10)."


@pytest.mark.parametrize("lang", ["sr", "hu", "en"])
def test_home_renders_all_locales(client, lang):
    """AC10: /<lang>/ (header+footer kroz site_setting) → HTTP 200 za sva 3 locale."""
    html = _get(client, f"/{lang}/", lang=lang)
    assert html, f"GET /{lang}/ MORA renderovati neprazan HTML (AC10)."


def test_no_cyrillic_on_sr_contact(client):
    """AC10: sr render kontakt strane NEMA ćirilice (puni latinica + dijakritici)."""
    html = _get(client, "/sr/kontakt/")
    # Ukloni <script>/<style> sadržaj da se izbegnu lažni hitovi (nije relevantno ovde,
    # ali bezbedno). Tražimo ćirilicu u celom render-u.
    found = _CYRILLIC_RE.findall(html)
    assert not found, (
        f"sr render kontakt strane NE SME sadržati ćirilicu (puni latinica; AC10), "
        f"pronađeni ćirilični karakteri: {set(found)!r}."
    )
