"""Story 7.1 — i18n/dijakritik + ASCII-slug konvencije (test-hardening, Story 7-1 spec).

Project-context non-negotiable pravila:
- UI-facing srpski stringovi koriste PUNE dijakritike (č/ć/ž/š/đ) — NIKAD shorn
  latinica (npr. „kolacica" kao vidljiva UI reč). Slug je IZUZETAK: legitimno ASCII.
- URL slug je ASCII transliteracija (slugify_ascii / G-6).

Mirror static-analiza/render presedan:
- apps/gdpr/tests/test_migration.py::test_dep_boundary_* (statički obrazac)
- apps/blog/tests/test_blog_index_i18n.py::test_slug_in_href_is_ascii (ASCII slug)
"""

from __future__ import annotations

import pytest
from django.urls import reverse
from django.utils.translation import override

from .conftest import COOKIE_POLICY_PATH_SR

pytestmark = pytest.mark.django_db

# Dijakritički karakteri koje UI srpski MORA umeti da prikaže.
SERBIAN_DIACRITICS = ("č", "ć", "ž", "š", "đ")


def _seed_sr(title="Politika kolačića", body="Mi koristimo kolačiće na sajtu."):
    """Postavi sr sadržaj na singleton (test-determinizam, NE oslanja se na data seed)."""
    from apps.gdpr.models import CookiePolicy

    obj = CookiePolicy.load()
    obj.title_sr = title
    obj.body_sr = body
    obj.effective_date = None
    obj.save()
    return obj


# Project-context: UI-facing srpski koristi PUNE dijakritike (ne shorn latinica)
def test_ui_strings_use_full_diacritics(client):
    """UI tekst (verbose_name + renderovani title/body) koristi pune dijakritike;
    shorn forma „kolacica" NE SME se pojaviti kao vidljiva UI reč (slug je izuzet)."""
    from apps.gdpr.models import CookiePolicy

    # 1) Model-nivo verbose_name + __str__ — stabilan token, NE oslanja se na Lorem.
    verbose = str(CookiePolicy._meta.verbose_name)
    assert verbose == "Politika kolačića", (
        f"verbose_name MORA biti 'Politika kolačića' sa punim dijakritikom (č/ć), "
        f"dobio {verbose!r}."
    )
    assert "č" in verbose and "ć" in verbose, (
        "verbose_name MORA sadržati pune dijakritike č i ć (NE shorn 'kolacica')."
    )
    assert "kolacica" not in verbose, (
        "verbose_name NE SME koristiti shorn latinicu 'kolacica' — UI MORA pune "
        "dijakritike."
    )

    # 2) Renderovana javna strana — title + body kroz markup.
    _seed_sr()
    response = client.get(COOKIE_POLICY_PATH_SR, HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    assert "kolačića" in html, (
        "Renderovani UI tekst MORA sadržati 'kolačića' sa punim dijakritikom (č/ć)."
    )
    assert any(d in html for d in SERBIAN_DIACRITICS), (
        f"Renderovana strana MORA sadržati bar jedan srpski dijakritik {SERBIAN_DIACRITICS}."
    )

    # 3) Shorn forma NE SME biti vidljiva UI reč. Slug („politika-kolacica") JESTE
    #    ASCII i legitiman — pa izolujemo URL/href pre provere UI teksta.
    visible = html.replace(COOKIE_POLICY_PATH_SR, "").replace("politika-kolacica", "")
    assert "kolacica" not in visible, (
        "Shorn latinica 'kolacica' NE SME se pojaviti kao vidljiva UI reč u telu/title-u "
        "(slug izuzet — proverava se samo ne-URL tekst)."
    )


# G-6: URL slug za gdpr:cookie_policy je čist ASCII (slugify_ascii presedan)
def test_slug_is_ascii():
    """reverse('gdpr:cookie_policy') daje ASCII path sa 'politika-kolacica' slug-om."""
    with override("sr"):
        url = reverse("gdpr:cookie_policy")

    assert "politika-kolacica" in url, (
        f"URL MORA sadržati ASCII slug 'politika-kolacica' (G-6), dobio {url!r}."
    )
    assert url.isascii(), (
        f"URL path MORA biti čist ASCII (slug bez dijakritika — G-6), dobio {url!r}."
    )
    assert url == COOKIE_POLICY_PATH_SR, (
        f"reverse pod sr MORA biti {COOKIE_POLICY_PATH_SR!r}, dobio {url!r}."
    )
