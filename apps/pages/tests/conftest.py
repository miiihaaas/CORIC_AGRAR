"""Story 3.1 — Zajednički fixtures + helperi za Home strana RED-phase testove (TEA).

Ovaj conftest NE definiše produkcioni kod. Samo test scaffolding:
- `home_url` fixture: rezolvuje `pages:home` ili pada na hardcoded `/sr/` (RED faza:
  `pages:home` NE postoji još → reverse baca NoReverseMatch; tada koristimo `/sr/`
  tako da testovi mogu da urade `client.get()` i padnu na ASSERTION-u, NE na fixture
  setup-u — što daje čitljiviji RED razlog).
- Traktori brand seed helperi (REUSE postojećih factory-ja iz apps/brands + apps/products).
- HZM kategorija helper (seed-ovana kroz migraciju 0004 — get_or_create defensive).

Pune dijakritike (č/ć/ž/š/đ) u svim Srpskim string-ovima; ASCII u identifikatorima.
"""

from __future__ import annotations

from io import BytesIO

import pytest


def _real_png_bytes() -> bytes:
    """1×1 validan PNG (Pillow) — sorl-thumbnail/ImageField verify() ga prihvata."""
    from PIL import Image

    buf = BytesIO()
    Image.new("RGB", (1, 1), color="green").save(buf, format="PNG")
    return buf.getvalue()


def png_upload(name: str = "img.png"):
    """SimpleUploadedFile sa validnim PNG sadržajem (za main_image / logo polja)."""
    from django.core.files.uploadedfile import SimpleUploadedFile

    return SimpleUploadedFile(name, _real_png_bytes(), content_type="image/png")


@pytest.fixture
def home_url() -> str:
    """URL Home strane za aktivan locale.

    RED faza: `reverse('pages:home')` baca NoReverseMatch dok Dev ne kreira app/URL.
    Fixture tada vrati hardcoded `/sr/` da test stigne do svoje ASSERTION-e (gde
    pada iz pravog razloga — pogrešan template / nedostaje context ključ), umesto da
    pukne u setup-u. View-level testovi POSEBNO proveravaju da render koristi
    `pages/home.html` (vidi `assert_home_template`) tako da ne prolaze vacuously protiv
    starog `core:home` base.html stub-a.
    """
    from django.urls import NoReverseMatch, reverse

    try:
        return reverse("pages:home")
    except NoReverseMatch:
        return "/sr/"


def assert_home_template(response) -> None:
    """RED-guard: render MORA koristiti 'pages/home.html'.

    U RED fazi stari `core:home` stub renderuje `base.html` (NE pages/home.html) pa
    ovaj assert pada — sprečava lažne (vacuous) PASS-ove strukturnih/render testova
    dok HomeView + pages/home.html ne postoje (Dev GREEN).
    """
    template_names = [t.name for t in response.templates if t.name]
    assert "pages/home.html" in template_names, (
        "Render MORA koristiti 'pages/home.html' (HomeView.template_name). "
        f"Renderovani template-i: {template_names!r} (RED: HomeView/pages/home.html "
        "još ne postoje — stari core:home stub renderuje base.html)."
    )


def make_traktori_brand(*, name: str, is_coming_soon: bool = False, with_image: bool = True):
    """Kreira Brand koji KVALIFIKUJE za Traktori sekciju (SM-D4):
    bar 1 objavljen `condition=NEW` Product. Vraća (brand, product).

    REUSE: BrandFactory + ProductFactory (apps/brands + apps/products).
    """
    from apps.brands.tests.factories import BrandFactory
    from apps.products.tests.factories import ProductFactory

    brand = BrandFactory.create(name=name, is_coming_soon=is_coming_soon)
    product_kwargs = {
        "brand": brand,
        "is_published": True,
    }
    if with_image:
        product_kwargs["main_image"] = png_upload(f"{brand.slug}-main.png")
    # ProductFactory default condition == NEW (verifikovano apps/products/tests/factories.py).
    product = ProductFactory.create(**product_kwargs)
    return brand, product


def make_mehanizacija_brand(*, name: str):
    """Kreira Brand koji NE SME ući u Traktori sekciju (SM-D4): nema condition=NEW
    objavljen proizvod. Daje mu samo USED proizvod (mehanizacija scenario).
    """
    from apps.brands.tests.factories import BrandFactory
    from apps.products.models import Product
    from apps.products.tests.factories import ProductFactory

    brand = BrandFactory.create(name=name)
    ProductFactory.create(
        brand=brand,
        is_published=True,
        condition=Product.ConditionChoice.USED,
    )
    return brand


def get_hzm_category():
    """Vrati HZM `radne-masine` Category (seed migracija 0004). None ako ne postoji."""
    from apps.brands.models import Category

    return Category.objects.filter(
        slug="radne-masine",
        is_for=Category.CategoryScope.MEHANIZACIJA,
    ).first()
