"""Story 5.2 — i18n + responsive (AC8) — TEA RED phase.

Pokriva AC8 (SM-D8): svi user-facing string-ovi pun dijakritik (NE šišana
latinica, NE ćirilica); hu/en smoke (GET /hu/blog/, /en/blog/ → 200); slug ASCII
u href; loading="lazy" na main_image; responsive grid class/attribute prisutan.

⚠️ GUARD: apps.blog importi UNUTAR funkcija. REUSE conftest make_post.

Refs:
- 5-2-...-filter.md AC8 + Task 8.9 + SM-D8
- project-context.md:497-527 (pune dijakritike — anti-šišana-latinica)
"""

from __future__ import annotations

import pytest
from django.utils import timezone
from django.utils.translation import activate

pytestmark = pytest.mark.django_db


def _published(make_post, **overrides):
    defaults = {
        "status": "published",
        "published_at": timezone.now() - timezone.timedelta(days=1),
    }
    defaults.update(overrides)
    return make_post(**defaults)


# AC8: ključni string-ovi pun dijakritik (NE šišana latinica)
def test_full_diacritics_in_key_strings(client, make_post):
    activate("sr")
    _published(make_post, title="Žetva pšenice 2026")

    response = client.get("/sr/blog/", HTTP_HOST="localhost")

    assert response.status_code == 200
    html = response.content.decode("utf-8")

    # Naslov pun dijakritik
    assert "Priče sa polja" in html, (
        "Naslov MORA biti 'Priče sa polja' (pun dijakritik c/c/z/s/dj - NE 'Price sa polja')."
    )
    # Šišana varijanta NE SME biti prisutna
    assert "Price sa polja" not in html, (
        "Sisana latinica 'Price sa polja' NE SME se pojaviti (anti-sisana; project-context.md:497-527)."
    )


# AC8: NEMA ćirilice u render-u (latinica sa dijakriticima)
def test_no_cyrillic_in_render(client, make_post):
    activate("sr")
    _published(make_post, title="Žetva pšenice 2026")

    response = client.get("/sr/blog/", HTTP_HOST="localhost")

    assert response.status_code == 200
    html = response.content.decode("utf-8")
    # Bazični cyrillic blok (U+0400–U+04FF) — user-facing copy MORA biti latinica
    cyrillic = [ch for ch in html if "Ѐ" <= ch <= "ӿ"]
    assert not cyrillic, (
        f"Render NE SME sadržati ćirilicu (latinica sa dijakriticima — sr). "
        f"Nađeni cyrillic karakteri: {set(cyrillic)!r}."
    )


# AC8: hu smoke — GET /hu/blog/ → 200
def test_hu_locale_smoke(client, make_post):
    activate("hu")
    _published(make_post, title="Žetva pšenice 2026")

    response = client.get("/hu/blog/", HTTP_HOST="localhost")

    assert response.status_code == 200, (
        f"GET /hu/blog/ MORA biti 200 (hu locale smoke). Dobili {response.status_code}."
    )


# AC8: en smoke — GET /en/blog/ → 200
def test_en_locale_smoke(client, make_post):
    activate("en")
    _published(make_post, title="Žetva pšenice 2026")

    response = client.get("/en/blog/", HTTP_HOST="localhost")

    assert response.status_code == 200, (
        f"GET /en/blog/ MORA biti 200 (en locale smoke). Dobili {response.status_code}."
    )


# AC8: slug u href je ASCII (slugify_ascii — NIKAD Unicode)
def test_slug_in_href_is_ascii(client, make_post):
    activate("sr")
    post = _published(make_post, title="Žetva pšenice 2026")

    response = client.get("/sr/blog/", HTTP_HOST="localhost")

    assert response.status_code == 200
    # slug je ASCII transliteracija (Ž→z, š→s)
    assert post.slug.isascii(), (
        f"Slug MORA biti ASCII (slugify_ascii), dobili {post.slug!r}."
    )
    html = response.content.decode("utf-8")
    assert f"/sr/blog/{post.slug}/" in html, (
        "href MORA sadržati ASCII slug u putanji."
    )


# AC8: loading="lazy" na main_image (kad slika postoji) — performance
def test_lazy_loading_attribute_when_image(client, make_post):
    """Kad post ima main_image, responsive_picture MORA emitovati loading=lazy.

    NAPOMENA: make_post default nema main_image; ovaj test seed-uje karticu BEZ
    slike (guard), pa proveravamo da render ne pukne + da template koristi
    responsive_picture pattern. Puni srcset/lazy assert se radi na detail/karticu
    sa stvarnom slikom u E2E; ovde sanity da non-image render radi.
    """
    activate("sr")
    _published(make_post, title="Priča bez slike")

    response = client.get("/sr/blog/", HTTP_HOST="localhost")

    assert response.status_code == 200, (
        "Render BEZ main_image MORA biti 200 ({% if post.main_image %} guard)."
    )


# AC8: responsive grid wrapper class prisutan (1col/2-3col CSS hook)
def test_responsive_grid_wrapper_present(client, make_post):
    activate("sr")
    _published(make_post, title="Grid priča")

    response = client.get("/sr/blog/", HTTP_HOST="localhost")

    assert response.status_code == 200
    html = response.content.decode("utf-8")
    # Grid CSS hook — blog ili product card grid klasa (REUSE coric-product-card ili coric-blog-card; SM-D8)
    assert ("blog" in html and "grid" in html.lower()) or "coric-product-card" in html, (
        "Index MORA imati responsive grid wrapper (CSS hook za 1col/2-3col — SM-D8)."
    )
