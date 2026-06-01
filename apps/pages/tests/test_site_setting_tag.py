"""Story 3.4 — AC7: {% site_setting %} tag + |splitlines filter (Task 9.5) — RED phase (TEA).

Verifikuje `apps/pages/templatetags/site_settings.py`:
- {% site_setting "phone_sales" %} renderuje vrednost (iz load() — bez view context-a)
- locale-aware za translatable polje (address sr vs hu fallback)
- radi na load() default (i kad seed nije primenjen)
- |splitlines daje listu nepraznih linija; prazno/None → []

Render testovi koriste Template().render() direktno (NE view) da dokažu da tag NE zahteva
view context (SM-D5 — view-ovi ostaju netaknuti).

RED razlog: templatetags/site_settings.py ne postoji → TemplateSyntaxError
('site_settings' is not a registered tag library) ILI ImportError (model).

Dev NE piše testove. Pokrenuti:
    just test apps/pages/tests/test_site_setting_tag.py -v
"""

from __future__ import annotations

import pytest
from django.template import Context, Template
from django.utils.translation import activate, override

pytestmark = pytest.mark.django_db


def _render(template_str: str, context: dict | None = None) -> str:
    """Render bez view-a — dokazuje da tag radi bez view context-a (SM-D5)."""
    return Template(template_str).render(Context(context or {}))


def test_site_setting_tag_renders_value():
    """AC7: {% site_setting "phone_sales" %} renderuje seed vrednost (bez view context-a)."""
    activate("sr")
    out = _render('{% load site_settings %}{% site_setting "phone_sales" %}')
    assert "+381 230 468 168" in out, (
        f"{{% site_setting 'phone_sales' %}} MORA renderovati seed vrednost "
        f"'+381 230 468 168' (AC7), dobio {out!r}."
    )


def test_site_setting_tag_works_without_view_context():
    """AC7/SM-D5: tag radi u praznom Context-u (NE zahteva da view ubaci site_settings)."""
    activate("sr")
    out = _render('{% load site_settings %}{% site_setting "email" %}', context={})
    assert "prodaja@coricagrar.rs" in out, (
        f"Tag MORA raditi BEZ view context-a (load() lazy get_or_create; SM-D5), "
        f"dobio {out!r}."
    )


def test_site_setting_tag_works_on_load_default():
    """AC7/AC2: tag radi i kad red ne postoji — load() get_or_create vraća default instancu."""
    from apps.pages.models import SiteSettings

    SiteSettings.objects.all().delete()  # ukloni seed (QuerySet path)
    activate("sr")
    # NE sme baciti DoesNotExist — load() get_or_create kreira pk=1 sa default-ima
    out = _render('{% load site_settings %}{% site_setting "company_name" %}')
    assert out is not None, "Tag MORA raditi na load() default (NE bacati DoesNotExist; AC7/AC2)."
    assert SiteSettings.objects.filter(pk=1).exists(), (
        "Tag-trigger load() MORA materijalizovati pk=1 default red."
    )


def test_site_setting_tag_is_locale_aware_for_address():
    """AC7/AC5: address je translatable → tag čita aktivnu lokalu (sr vrednost u sr)."""
    with override("sr"):
        out_sr = _render('{% load site_settings %}{% site_setting "address" %}')
    assert "Vojvođanska" in out_sr, (
        f"{{% site_setting 'address' %}} u sr lokali MORA renderovati sr (puni-dijakritik) "
        f"vrednost iz address_sr (AC7/AC5), dobio {out_sr!r}."
    )
    # hu lokala: prazna address_hu → fallback na sr (MODELTRANSLATION_FALLBACK_LANGUAGES);
    # ne ruši render (render NIJE prazan).
    with override("hu"):
        out_hu = _render('{% load site_settings %}{% site_setting "address" %}')
    assert out_hu.strip(), (
        "address u hu lokali MORA renderovati neprazno (fallback na sr kad je hu prazan; "
        f"AC10), dobio {out_hu!r}."
    )


def test_splitlines_filter_returns_nonempty_lines():
    """SM-D10: |splitlines daje listu nepraznih .strip()-ovanih linija (za working_hours <ul>)."""
    out = _render(
        '{% load site_settings %}'
        '{% for line in value|splitlines %}<li>{{ line }}</li>{% endfor %}',
        context={"value": "  Ponedeljak–Petak: 08–16h \n\n Subota: 08–13h \n"},
    )
    assert out.count("<li>") == 2, (
        f"|splitlines MORA preskočiti prazne linije i .strip()-ovati (SM-D10) → 2 <li> "
        f"za 2 neprazna reda, dobio {out!r}."
    )
    assert "<li>Ponedeljak–Petak: 08–16h</li>" in out, (
        f"|splitlines MORA .strip()-ovati linije (NE voditi/pratiti razmak), dobio {out!r}."
    )


def test_splitlines_filter_handles_empty():
    """SM-D10: |splitlines na praznom/None vraća praznu listu (0 <li>)."""
    out_empty = _render(
        '{% load site_settings %}'
        '{% for line in value|splitlines %}<li>{{ line }}</li>{% endfor %}',
        context={"value": ""},
    )
    assert "<li>" not in out_empty, (
        f"|splitlines na praznom stringu MORA dati 0 linija (SM-D10), dobio {out_empty!r}."
    )


def test_tag_issues_single_sitesettings_query_per_request(client):
    """AC7/SM-D5: per-request keš → TAČNO 1 SiteSettings upit po strani.

    Kontakt strana zove {% site_setting %} VIŠE puta (header + footer + contact-info
    sekcija), ali per-request keš na `request` objektu garantuje da se SiteSettings učita
    SAMO jednom po response-u. Zaključava +1 query budžet na koji se chrome oslanja.

    Filtriramo CaptureQueriesContext na `pages_sitesettings` tabelu (regex/ORM, NE
    BeautifulSoup) jer strana radi i druge upite (proizvodi/brendovi/sesija).
    """
    from django.db import connection
    from django.test.utils import CaptureQueriesContext
    from django.urls import reverse

    activate("sr")
    contact_url = reverse("pages:contact")

    with CaptureQueriesContext(connection) as ctx:
        response = client.get(contact_url)

    assert response.status_code == 200, (
        f"GET {contact_url} MORA biti 200, dobio {response.status_code}."
    )
    sitesettings_queries = [
        q for q in ctx.captured_queries if "pages_sitesettings" in q["sql"].lower()
    ]
    assert len(sitesettings_queries) == 1, (
        f"Chrome (header+footer+contact-info) zove {{% site_setting %}} više puta ali "
        f"MORA platiti TAČNO 1 SiteSettings upit po request-u (per-request keš; SM-D5), "
        f"dobio {len(sitesettings_queries)}: "
        f"{[q['sql'] for q in sitesettings_queries]!r}."
    )
