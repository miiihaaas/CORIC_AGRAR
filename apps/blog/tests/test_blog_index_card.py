"""Story 5.2 — Blog kartica (AC4) — TEA RED phase.

Pokriva AC4 (SM-D7 / IMP-2): `_post_card.html` renderuje:
  - main_image (responsive_picture srcset / sorl-thumbnail) sa {% if %} guard (nullable)
  - published_at via |date:"SHORT_DATE_FORMAT" — locale-aware (pod activate("sr") → DD.MM.YYYY.)
  - title + perex
  - CTA „SAZNAJ VIŠE" → <a href> = post.get_absolute_url() == /sr/blog/<slug>/
  - data-testid="blog-card-<slug>"

Datum: NE asertujemo literalni format string, već LOCALE-RENDEROVAN izlaz —
računamo očekivani datum kroz Django `date` filter sa SHORT_DATE_FORMAT pod sr
locale-om i tražimo ga u HTML-u (robusno na format varijacije).

⚠️ GUARD: apps.blog importi UNUTAR funkcija. REUSE conftest make_post.

Refs:
- 5-2-...-filter.md AC4 + Task 8.5 + SM-D7 + IMP-2/OQ-1
"""

from __future__ import annotations

import pytest
from django.template.defaultfilters import date as date_filter
from django.utils import timezone
from django.utils.translation import activate

pytestmark = pytest.mark.django_db


def _published(make_post, **overrides):
    defaults = {
        "status": "published",
        "published_at": timezone.now() - timezone.timedelta(days=3),
    }
    defaults.update(overrides)
    return make_post(**defaults)


# AC4: CTA „SAZNAJ VIŠE" prisutan na kartici
def test_card_has_saznaj_vise_cta(client, make_post):
    activate("sr")
    _published(make_post, title="Žetva pšenice 2026")

    response = client.get("/sr/blog/", HTTP_HOST="localhost")

    assert response.status_code == 200
    html = response.content.decode("utf-8")
    assert "SAZNAJ VIŠE" in html, (
        "Kartica MORA imati CTA 'SAZNAJ VIŠE' (pun dijakritik - epics.md:874)."
    )


# AC4: kartica linkuje na post.get_absolute_url() == /sr/blog/<slug>/
def test_card_links_to_get_absolute_url(client, make_post):
    activate("sr")
    post = _published(make_post, title="Žetva pšenice 2026")

    response = client.get("/sr/blog/", HTTP_HOST="localhost")

    assert response.status_code == 200
    html = response.content.decode("utf-8")
    expected_href = f"/sr/blog/{post.slug}/"
    assert f'href="{expected_href}"' in html, (
        f"Kartica MORA imati <a href=\"{expected_href}\"> (post.get_absolute_url; "
        f"epics.md:877). HTML ne sadrži taj href."
    )


# AC4: data-testid="blog-card-<slug>"
def test_card_has_data_testid(client, make_post):
    activate("sr")
    post = _published(make_post, title="Žetva pšenice 2026")

    response = client.get("/sr/blog/", HTTP_HOST="localhost")

    assert response.status_code == 200
    html = response.content.decode("utf-8")
    assert f'data-testid="blog-card-{post.slug}"' in html, (
        f"Kartica MORA imati data-testid=\"blog-card-{post.slug}\" (E2E selektor)."
    )


# AC4: title + perex renderovani
def test_card_renders_title_and_perex(client, make_post):
    activate("sr")
    _published(
        make_post,
        title="Đubrenje ozime pšenice",
        perex="Kratak vodič kroz prihranu azotom.",
    )

    response = client.get("/sr/blog/", HTTP_HOST="localhost")

    assert response.status_code == 200
    html = response.content.decode("utf-8")
    assert "Đubrenje ozime pšenice" in html, "Kartica MORA renderovati title."
    assert "Kratak vodič kroz prihranu azotom." in html, (
        "Kartica MORA renderovati perex."
    )


# AC4 / IMP-2: published_at via |date:"SHORT_DATE_FORMAT" — locale-aware (sr)
def test_card_renders_locale_aware_date(client, make_post):
    activate("sr")
    pub = timezone.now() - timezone.timedelta(days=3)
    _published(make_post, title="Žetva pšenice 2026", published_at=pub)

    response = client.get("/sr/blog/", HTTP_HOST="localhost")

    assert response.status_code == 200
    html = response.content.decode("utf-8")

    # Očekivani izlaz = isti `date` filter + SHORT_DATE_FORMAT pod sr locale-om
    # (NE literalni format string — robusno na locale format varijacije; IMP-2).
    expected_date = date_filter(timezone.localtime(pub), "SHORT_DATE_FORMAT")
    assert expected_date, "SHORT_DATE_FORMAT render NE SME biti prazan (sanity)."
    assert expected_date in html, (
        f"Kartica MORA renderovati published_at kroz |date:\"SHORT_DATE_FORMAT\" "
        f"(locale-aware — IMP-2). Pod activate('sr') očekivano {expected_date!r}, "
        f"nije nađeno u HTML-u."
    )


# AC4: main_image {% if %} guard — kartica bez slike render-uje BEZ greške (200)
def test_card_without_main_image_renders_ok(client, make_post):
    activate("sr")
    # make_post default NEMA main_image (nullable) → guard mora sprečiti render greške
    _published(make_post, title="Priča bez slike")

    response = client.get("/sr/blog/", HTTP_HOST="localhost")

    assert response.status_code == 200, (
        "Kartica BEZ main_image MORA render-ovati 200 ({% if post.main_image %} guard — "
        "main_image je nullable iz 5-1)."
    )
    html = response.content.decode("utf-8")
    assert "Priča bez slike" in html
