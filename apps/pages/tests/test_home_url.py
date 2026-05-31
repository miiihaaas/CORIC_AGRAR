"""Story 3.1 — AC1: NOVI apps/pages app + pages:home URL + core:home regression lock.

RED phase (TEA): definiše URL/app kontrakt PRE Dev GREEN. SVI testovi MORAJU pasti
dok Dev ne kreira apps/pages (PagesConfig, INSTALLED_APPS, HomeView, pages:home URL)
i ne ukloni core:home.

AC1 — 5 testova:
- test_home_url_resolves_sr / hu / en   (3 lokala HTTP 200)
- test_home_uses_pages_home_template     (assertTemplateUsed pages/home.html)
- test_pages_home_reverse_resolves        (reverse('pages:home') -> /sr/)
- test_core_home_no_longer_reverses       (reverse('core:home') -> NoReverseMatch; C1 lock)

NAPOMENA (TEA, RED razlog): u trenutku pisanja apps/pages NIJE u INSTALLED_APPS,
HomeView ne postoji, pages:home se NE rezolvuje, a core:home JOŠ postoji (Dev ga
uklanja u GREEN). Zato:
- pages:home testovi padaju (NoReverseMatch / 404 / pogrešan template),
- core:home regression test pada (reverse JOŠ uspeva — pada dok Dev ne ukloni core:home).

Pokrenuti:
    docker compose -f compose/local.yml exec django python -m pytest \\
        apps/pages/tests/test_home_url.py -v
"""

from __future__ import annotations

import pytest
from django.urls import NoReverseMatch, reverse
from django.utils.translation import activate

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    ("lang", "expected_prefix"),
    [
        ("sr", "/sr/"),
        ("hu", "/hu/"),
        ("en", "/en/"),
    ],
)
def test_home_url_resolves(client, lang, expected_prefix):
    """AC1: GET /<lang>/ -> HTTP 200 za sva 3 locale (pages:home renderuje home)."""
    activate(lang)
    response = client.get(expected_prefix)
    assert response.status_code == 200, (
        f"GET {expected_prefix} MORA vratiti HTTP 200 (pages:home HomeView). "
        f"Dobio {response.status_code}. RED: apps/pages/HomeView još ne postoji."
    )
    # RED-guard: stari core:home stub vraća 200 ali renderuje base.html — render MORA
    # biti pages/home.html (HomeView), inače je 200 vacuous.
    template_names = [t.name for t in response.templates if t.name]
    assert "pages/home.html" in template_names, (
        f"GET {expected_prefix} MORA renderovati 'pages/home.html', dobio {template_names!r}."
    )


def test_home_uses_pages_home_template(client):
    """AC1: render koristi 'pages/home.html' (NE base.html direktno)."""
    activate("sr")
    response = client.get("/sr/")
    assert response.status_code == 200
    template_names = [t.name for t in response.templates if t.name]
    assert "pages/home.html" in template_names, (
        "Home MORA renderovati 'pages/home.html' (HomeView.template_name). "
        f"Renderovani template-i: {template_names!r}"
    )


def test_pages_home_reverse_resolves():
    """AC1: reverse('pages:home') -> '/sr/' za sr locale (app_name='pages', name='home')."""
    activate("sr")
    url = reverse("pages:home")
    assert url == "/sr/", (
        f"reverse('pages:home') MORA dati '/sr/' (i18n_patterns root path), dobio {url!r}."
    )


def test_core_home_no_longer_reverses():
    """AC1 (C1 regression lock): core:home je UKLONJEN -> reverse baca NoReverseMatch.

    Ovo zaključava da je relokacija home view-a iz apps/core u apps/pages stvarno
    izvršena (Dev GREEN). RED: core:home JOŠ postoji pa reverse uspeva -> test pada.
    """
    activate("sr")
    with pytest.raises(NoReverseMatch):
        reverse("core:home")
