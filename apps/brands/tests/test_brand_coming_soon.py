"""Story 2.6 — `brand_coming_soon.html` minimal template tests (RED phase TDD).

Pokriva AC2.5 (C6 fix) — minimal "Uskoro" stanje za brendove sa is_coming_soon=True.

Test scope (4 tests):
- test_coming_soon_template_used — get_template_names() override vraća brand_coming_soon.html
- test_coming_soon_renders_single_h1_with_brand_name — TAČNO 1 <h1> sa brand.name
- test_coming_soon_renders_pill_badge_uskoro — <span class="coric-pill-badge--coming-soon" role="status">
- test_coming_soon_renders_nazad_na_home_cta — <a href="{% url 'core:home' %}">

Pokrenuti sa:
    docker compose -f compose/local.yml exec django uv run pytest \\
        apps/brands/tests/test_brand_coming_soon.py -v

Refs:
- 2-6-brand-listing-strana-sa-grid-extended-layout-om.md (AC2.5)
- 2-6-interface-contract.md (§ 4 brand_coming_soon.html spec)
"""

from __future__ import annotations

import re

import pytest
from django.utils.translation import activate

from apps.brands.tests.factories import BrandFactory

pytestmark = pytest.mark.django_db


def test_coming_soon_template_used(client):
    """AC2.5: is_coming_soon=True triggers brand_coming_soon.html (NE brand_detail.html)."""
    activate("sr")
    brand = BrandFactory.create_coming_soon(name="Future Brand")

    url = f"/sr/traktori/{brand.slug}/"
    response = client.get(url)

    assert response.status_code == 200, (
        f"Coming-soon brand treba HTTP 200 (SM-D4 — NE 404), dobio {response.status_code}."
    )
    template_names = [t.name for t in response.templates if t.name]
    assert "brands/brand_coming_soon.html" in template_names, (
        f"is_coming_soon=True MORA renderovati 'brands/brand_coming_soon.html' "
        f"(BrandDetailView.get_template_names() override per SM-D19). "
        f"Renderovani template-i: {template_names!r}"
    )


def test_coming_soon_renders_single_h1_with_brand_name(client):
    """AC2.5: TAČNO 1 <h1> element koji sadrži brand.name."""
    activate("sr")
    brand = BrandFactory.create_coming_soon(name="Future Brand XYZ")

    url = f"/sr/traktori/{brand.slug}/"
    response = client.get(url)
    html = response.content.decode("utf-8")

    h1_pattern = re.compile(r"<h1\b[^>]*>(.*?)</h1>", re.IGNORECASE | re.DOTALL)
    h1_matches = h1_pattern.findall(html)
    assert len(h1_matches) == 1, (
        f"Coming-soon template MORA imati TAČNO 1 <h1>, pronađeno {len(h1_matches)}. "
        f"H1 contents: {h1_matches!r}"
    )
    # Sadržaj <h1> mora sadržati brand.name
    h1_text = h1_matches[0]
    assert "Future Brand XYZ" in h1_text, (
        f"<h1> MORA sadržati brand.name='Future Brand XYZ', dobio: {h1_text!r}."
    )


def test_coming_soon_renders_pill_badge_uskoro(client):
    """AC2.5: pill-badge sa klasom coric-pill-badge--coming-soon i role='status'."""
    activate("sr")
    brand = BrandFactory.create_coming_soon(name="Future Brand")

    url = f"/sr/traktori/{brand.slug}/"
    response = client.get(url)
    html = response.content.decode("utf-8")

    # Pill badge mora imati klasu i role
    assert "coric-pill-badge--coming-soon" in html, (
        "Coming-soon template MORA imati pill-badge sa klasom 'coric-pill-badge--coming-soon' "
        "(AC2.5 + AC8 brand-listing.css selektor enumeracija)."
    )
    # role='status' (live region announcement)
    badge_pattern = re.compile(
        r'<span[^>]*coric-pill-badge--coming-soon[^>]*role="status"',
        re.IGNORECASE,
    )
    badge_pattern2 = re.compile(
        r'<span[^>]*role="status"[^>]*coric-pill-badge--coming-soon',
        re.IGNORECASE,
    )
    assert badge_pattern.search(html) or badge_pattern2.search(html), (
        "Pill badge MORA imati role='status' (a11y live region announcement)."
    )
    # Tekst "Uskoro" mora biti render-ovan
    assert "Uskoro" in html, "Pill badge tekst 'Uskoro' MORA biti render-ovan."


def test_coming_soon_renders_nazad_na_home_cta(client):
    """AC2.5: CTA "Nazad na Home" linkuje na {% url 'core:home' %}."""
    activate("sr")
    brand = BrandFactory.create_coming_soon(name="Future Brand")

    url = f"/sr/traktori/{brand.slug}/"
    response = client.get(url)
    html = response.content.decode("utf-8")

    # Home URL u sr locale — kroz reverse('core:home') / i18n_patterns
    from django.urls import reverse

    home_url = reverse("core:home")  # za aktivan locale (sr), trebao bi biti '/sr/'

    # CTA mora biti <a href="..."> sa "Nazad na Home" tekstom
    cta_pattern = re.compile(
        rf'<a[^>]*href="{re.escape(home_url)}"[^>]*>.*?Nazad na Home.*?</a>',
        re.IGNORECASE | re.DOTALL,
    )
    assert cta_pattern.search(html), (
        f"CTA 'Nazad na Home' MORA biti <a href='{home_url}'> (rezolvuje 'core:home' URL name). "
        f"Verifikuj da je 'core:home' URL name registrovan i da template koristi {{% url 'core:home' %}}."
    )

    # Coming-soon template NE SME renderovati statistike/serije/testimonijale (sve odsutne)
    assert 'id="brand-statistics"' not in html, (
        "Coming-soon template NE SME imati statistike sekciju."
    )
    assert 'id="brand-series"' not in html, "Coming-soon template NE SME imati serije sekciju."
    assert 'id="brand-testimonials"' not in html, (
        "Coming-soon template NE SME imati testimonijali sekciju."
    )


def test_coming_soon_renders_responsive_picture_when_brand_has_logo(client):
    """T4 (code review iter-1): coming-soon sa logo MORA renderovati <picture> element.

    AC2.5 prose: ako brand.logo postoji, sekcija sa logom MORA biti renderovana
    kroz responsive_picture template tag (sorl-thumbnail srcset). Bez logo-a
    sekcija se preskače ({% if brand.logo %} guard u brand_coming_soon.html).
    """
    from io import BytesIO

    from django.core.files.uploadedfile import SimpleUploadedFile
    from PIL import Image

    activate("sr")
    # Real PNG bytes (50×50 transparent) da sorl-thumbnail može generisati thumbnails
    buf = BytesIO()
    Image.new("RGBA", (50, 50), color=(0, 0, 0, 0)).save(buf, format="PNG")
    image_bytes = buf.getvalue()

    brand = BrandFactory.create_coming_soon(name="Brand With Logo")
    brand.logo = SimpleUploadedFile(
        "logo.png", image_bytes, content_type="image/png"
    )
    brand.save()

    url = f"/sr/traktori/{brand.slug}/"
    response = client.get(url)
    html = response.content.decode("utf-8")

    assert "<picture>" in html, (
        "Coming-soon sa brand.logo MORA renderovati <picture> element kroz "
        "responsive_picture template tag (AC2.5 + media_pipeline integration)."
    )


def test_coming_soon_no_nested_main_element(client):
    """AC2.5 (iter-2 adversarial guard): coming-soon template MORA imati TAČNO 1 <main> element.

    base.html provider renderuje JEDAN <main id="main-content"> wrapper. Coming-soon
    template extends base.html i renderuje wrapper UNUTAR {% block content %}. Wrapper
    MORA biti <div class="coric-brand-coming-soon"> (NE drugi <main> jer HTML5 spec
    zabranjuje nested <main> elemente — samo jedan <main> per dokument).

    Paralelan guard sa test_placeholder_uses_semantic_main_landmark (preveniše regression
    u kojoj Dev iz inertia po story prose-u doda dodatni <main role="main"> wrapper).

    Interface contract § 4 specijalizuje story prose AC2.5: wrapper je <div>, reuse
    base.html landmark.
    """
    activate("sr")
    brand = BrandFactory.create_coming_soon(name="Future Brand")

    url = f"/sr/traktori/{brand.slug}/"
    response = client.get(url)
    html = response.content.decode("utf-8")

    main_pattern = re.compile(r"<main\b[^>]*>", re.IGNORECASE)
    main_matches = main_pattern.findall(html)
    assert main_matches, (
        "Coming-soon render MORA imati bar 1 <main> element (base.html provider)."
    )
    assert len(main_matches) == 1, (
        f"Coming-soon render MORA imati TAČNO 1 <main> element (HTML5 spec — "
        f"nested <main> je invalid; iter-1 fix interface contract § 4). "
        f"Pronađeno: {len(main_matches)}: {main_matches!r}. "
        "Coming-soon wrapper MORA biti <div class='coric-brand-coming-soon'> "
        "(NE drugi <main role='main'>)."
    )
