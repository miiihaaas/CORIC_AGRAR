"""Story 2.3 — apps/media_pipeline/templatetags/media_tags.py testovi (RED phase TDD).

Pokriva AC4 + AC10 — `{% responsive_picture %}` inclusion_tag za `<picture>` element
sa srcset varijantama 400w/800w/1600w + `format` kwarg za PNG transparency preservation.

Test scope (10 scenarija):
- 4 render structure: `<picture>` element, srcset string, alt tekst, accept image kao positional/keyword arg
- 2 graceful degradation: None image, empty ImageFieldFile (oba renderuju prazno)
- 2 attribute behavior: css_class, loading lazy/eager
- 2 format kwarg (AC10): PNG preserve alpha, JPEG default loses alpha

KRITIČNO test setup:
- Koristi `Product` model iz apps.products (Story 2.2) jer ima `main_image` ImageField
- `Brand` model iz apps.brands (Story 2.1) za PNG transparency test (logo ImageField)
- Per-test MEDIA_ROOT isolation kroz `temp_media_root` fixture
- pytest.mark.django_db (real DB integration — sorl-thumbnail KVStore radi nad ORM-om)

Pokrenuti kroz Docker (libmagic SEGFAULT na Windows host-u per Decision MP-D6):
    docker compose -f compose/local.yml run --rm django uv run pytest apps/media_pipeline/tests/test_templatetags.py -v

Refs:
- 2-3-image-pipeline-sa-sorl-thumbnail-responsive-srcset.md (story spec, AC4 + AC10)
- 2-3-interface-contract.md (TEA canonical contract)
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from django.conf import settings as django_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.template import Context, Template
from PIL import Image

pytestmark = pytest.mark.django_db


def _first_srcset_url(html: str) -> str:
    """Iz <picture><img srcset="..."> izvuci prvi URL u srcset listi.

    Format: `srcset="/media/thumbnails/foo_400.png 400w, /media/thumbnails/foo_800.png 800w, ..."`.
    Vraća prvi URL pre prvog razmaka u srcset stringu.
    """
    match = re.search(r'srcset="([^"]+)"', html)
    if not match:
        raise AssertionError(f"Rendered HTML nema srcset atribut:\n{html}")
    srcset = match.group(1)
    # Prvi token u srcset listi je "URL widthW" → split po space
    first_pair = srcset.split(",")[0].strip()
    return first_pair.split(" ")[0]


def _url_to_filesystem_path(url: str) -> Path:
    """Pretvori MEDIA_URL putanju (e.g. `/media/thumbnails/cache/x.png`) u file system path.

    Strip MEDIA_URL prefix i pripoji MEDIA_ROOT.
    """
    media_url = django_settings.MEDIA_URL.rstrip("/")
    relative = url[len(media_url) :].lstrip("/")
    return Path(django_settings.MEDIA_ROOT) / relative


# =============================================================================
# Helpers — kreiraju Product/Brand sa real image upload-om za render testove
# =============================================================================


def _create_brand_with_logo(image_bytes: bytes, *, filename: str = "logo.png"):
    """Kreira Brand sa upload-ovanim logo-om (real file na disk-u kroz ImageField)."""
    from apps.brands.models import Brand

    brand = Brand.objects.create(
        name="Test Brand",
        brand_color="",
        statistics=[],
    )
    brand.logo = SimpleUploadedFile(filename, image_bytes, content_type="image/png")
    brand.save()
    return brand


def _create_product_with_image(image_bytes: bytes, *, filename: str = "main.jpg"):
    """Kreira Product sa upload-ovanom main_image (real file na disk-u)."""
    from apps.brands.models import Brand
    from apps.products.models import Product

    brand = Brand.objects.create(
        name="Test Brand",
        brand_color="",
        statistics=[],
    )
    product = Product(
        brand=brand,
        name="Test Product",
        condition=Product.ConditionChoice.NEW,
        status=Product.StatusChoice.DRAFT,
    )
    product.main_image = SimpleUploadedFile(
        filename, image_bytes, content_type="image/jpeg"
    )
    product.save()
    return product


def _render(template_str: str, context: dict) -> str:
    """Helper: render Django template string sa contextom."""
    t = Template(template_str)
    return t.render(Context(context))


# =============================================================================
# AC4 — Render structure: <picture> element, srcset varijante, alt tekst
# =============================================================================


def test_responsive_picture_renders_picture_element_with_srcset(
    temp_media_root, realistic_source_image_bytes
):
    """AC4: Tag renderuje `<picture>` element sa srcset koji sadrži 400w/800w/1600w varijante.

    Realistic source (2400×1800, ~500KB-1MB) je potreban da sorl-thumbnail može da
    generiše sve tri varijante (manje od 400px source bi se downscale-ovao samo deo).
    """
    product = _create_product_with_image(realistic_source_image_bytes)

    html = _render(
        "{% load media_tags %}{% responsive_picture product.main_image alt='Test Slika' %}",
        {"product": product},
    )

    assert "<picture>" in html, (
        f"Tag mora renderovati <picture> element; dobio:\n{html}"
    )
    assert "</picture>" in html, f"Tag mora zatvoriti <picture> element; dobio:\n{html}"
    assert " 400w" in html, f"Srcset mora sadržati 400w varijantu; dobio:\n{html}"
    assert " 800w" in html, f"Srcset mora sadržati 800w varijantu; dobio:\n{html}"
    assert " 1600w" in html, f"Srcset mora sadržati 1600w varijantu; dobio:\n{html}"


def test_responsive_picture_accepts_positional_image_arg(
    temp_media_root, realistic_source_image_bytes
):
    """AC4 / Gotcha MP-8: Tag prima image kao prvi positional arg.

    `{% responsive_picture product.main_image alt='X' %}` (image kao positional).
    Default invocation pattern u svim Story 2.6/2.7 template-ima.
    """
    product = _create_product_with_image(realistic_source_image_bytes)

    html = _render(
        "{% load media_tags %}{% responsive_picture product.main_image alt='Test' %}",
        {"product": product},
    )

    assert "<picture>" in html, "Positional image arg mora raditi"


def test_responsive_picture_with_empty_image_field_renders_nothing(temp_media_root):
    """AC4: ImageFieldFile bez `.name` (no upload) → graceful empty render.

    Defensive guard na boundary: caller (template) ne mora wrap-ovati
    `{% if product.main_image %}` jer helper sam handle-uje empty case.
    """
    from apps.brands.models import Brand
    from apps.products.models import Product

    brand = Brand.objects.create(name="X", brand_color="", statistics=[])
    product = Product.objects.create(
        brand=brand,
        name="No Image Product",
        condition=Product.ConditionChoice.NEW,
        status=Product.StatusChoice.DRAFT,
    )
    # product.main_image je prazan ImageFieldFile (blank=True, null=True na Product modelu)

    html = _render(
        "{% load media_tags %}{% responsive_picture product.main_image alt='X' %}",
        {"product": product},
    )

    assert "<picture>" not in html, (
        f"Prazan ImageField mora gracefully renderovati ništa; dobio:\n{html!r}"
    )


def test_responsive_picture_with_none_image_renders_nothing(temp_media_root):
    """AC4: Eksplicitni None image → graceful empty render (no AttributeError).

    Test scenario: caller prosleđuje `None` direktno (npr. `{% responsive_picture None alt='x' %}`).
    Helper MORA gracefully degrade — ne raise AttributeError, ne render `<picture>` tag.
    """
    html = _render(
        "{% load media_tags %}{% responsive_picture image alt='X' %}",
        {"image": None},
    )

    assert "<picture>" not in html, (
        f"None image mora gracefully renderovati ništa; dobio:\n{html!r}"
    )


def test_responsive_picture_applies_css_class(
    temp_media_root, realistic_source_image_bytes
):
    """AC4: `css_class` kwarg dodaje `class="..."` atribut na `<img>` tag."""
    product = _create_product_with_image(realistic_source_image_bytes)

    html = _render(
        "{% load media_tags %}"
        "{% responsive_picture product.main_image alt='X' css_class='product-card-img' %}",
        {"product": product},
    )

    assert 'class="product-card-img"' in html, (
        f"css_class kwarg mora postaviti class atribut; dobio:\n{html}"
    )


def test_responsive_picture_respects_loading_lazy_default(
    temp_media_root, realistic_source_image_bytes
):
    """AC4: Default `loading="lazy"` na svim slikama ispod fold-a.

    Per project-context.md § Performance must-haves: "loading='lazy' atribut na slikama
    ispod fold-a". Default je lazy; caller eksplicitno override-uje na eager za hero slike.
    """
    product = _create_product_with_image(realistic_source_image_bytes)

    html = _render(
        "{% load media_tags %}{% responsive_picture product.main_image alt='X' %}",
        {"product": product},
    )

    assert 'loading="lazy"' in html, f"Default loading mora biti 'lazy'; dobio:\n{html}"


def test_responsive_picture_respects_loading_eager_override(
    temp_media_root, realistic_source_image_bytes
):
    """AC4: Eksplicitni `loading="eager"` kwarg override-uje default.

    Above-the-fold hero slike (Story 3.1 Home) MUST koristiti `loading='eager'`
    radi LCP optimizacije (lazy loading hero slike → CLS i delayed LCP).
    """
    product = _create_product_with_image(realistic_source_image_bytes)

    html = _render(
        "{% load media_tags %}"
        "{% responsive_picture product.main_image alt='X' loading='eager' %}",
        {"product": product},
    )

    assert 'loading="eager"' in html, (
        f"loading='eager' override mora biti reflected; dobio:\n{html}"
    )


def test_responsive_picture_includes_alt_text(
    temp_media_root, realistic_source_image_bytes
):
    """AC4: `alt` kwarg dodaje `alt="..."` atribut na `<img>` tag (a11y MUST).

    Accessibility requirement per WCAG 2.1 — sve image-i moraju imati alt tekst.
    Helper requires alt explicitly; bez njega bi a11y check failover-ao.
    """
    product = _create_product_with_image(realistic_source_image_bytes)

    html = _render(
        "{% load media_tags %}{% responsive_picture product.main_image alt='Specifičan Alt' %}",
        {"product": product},
    )

    assert 'alt="Specifičan Alt"' in html, (
        f"alt kwarg mora postaviti alt atribut; dobio:\n{html}"
    )


# =============================================================================
# AC10 — format kwarg: PNG preserve alpha, JPEG default loses alpha
# =============================================================================


def test_responsive_picture_width_from_fallback_thumb(
    temp_media_root, realistic_source_image_bytes
):
    """FIX-8 PERFORMANCE regression guard: Tag mora expose-ovati `default_width`/`default_height`
    iz LARGEST generisanog thumbnail-a (ne hardcoded 1600).

    Browser CLS kalkulacija depend-uje na accurate img width atributu. Ako bi se
    media_tags.py vratio na hardcoded vrednost (npr. `default_width = 1600` bez obzira
    na thumb.width), ovaj test bi failnuo.

    Setup: 2400×1800 realistic source. sorl generiše fallback 1600w varijantu →
    default_width = 1600 (downscaled), NE 2400 (source) i NE neki hardcoded value.
    """
    product = _create_product_with_image(realistic_source_image_bytes)

    html = _render(
        "{% load media_tags %}{% responsive_picture product.main_image alt='Test' %}",
        {"product": product},
    )

    width_match = re.search(r'width="(\d+)"', html)
    assert width_match is not None, (
        f"Rendered <img> MORA imati width atribut; dobio:\n{html}"
    )
    width = int(width_match.group(1))

    # Fallback je najveća varijanta — za 2400px source sorl 1600w geometry → 1600px wide
    assert width == 1600, (
        f"Expected width=1600 (largest variant), got width={width}. "
        f"Ako je 2400, znači da je hardcoded fallback umesto thumb.width propagation. "
        f"Ako je 1600 hardcoded literal, test prolazi accidentalno — proveri media_tags.py FIX-8."
    )

    # Negative regression check: width NE sme biti source dimension
    assert width != 2400, (
        "Width MORA biti sorl-thumbnailed value (1600), NE source dimension (2400)"
    )


def test_responsive_picture_format_jpeg_default_loses_alpha(
    temp_media_root, large_png_with_alpha_bytes
):
    """AC10: Default `format='JPEG'` konvertuje PNG-RGBA source u JPG (gubi alpha).

    FIX-5 (TEA BUG#2 + #3): koristi LARGE PNG with alpha (1000×800) jer sorl ne
    upscale-uje 10×10 → 400/800/1600w (smal source generiše samo source-width
    thumbnail). I, kritičnije, ovaj test sad zaista verifikuje da je Pillow mod
    `RGB` ili `L` (alpha izgubljena), a ne samo da je ekstenzija `.jpg`.

    Brand.logo upload-ovan kao PNG RGBA → bez `format='PNG'` kwarg-a, thumbnail mora biti
    JPEG sa `mode in ("RGB", "L")` (alpha channel removed per Decision MP-D5).
    """
    brand = _create_brand_with_logo(large_png_with_alpha_bytes, filename="logo.png")

    html = _render(
        "{% load media_tags %}{% responsive_picture brand.logo alt='Brand' %}",
        {"brand": brand},
    )

    # Step 1: ekstenzija check (regression guard za prethodnu implementaciju)
    assert ".jpg" in html, (
        f"Default format='JPEG' mora generisati .jpg thumbnail-ove; dobio:\n{html}"
    )

    # Step 2: stvarni Pillow mode check — kanonski AC10 contract verifikacija
    first_url = _first_srcset_url(html)
    thumb_path = _url_to_filesystem_path(first_url)
    assert thumb_path.exists(), (
        f"Generisani thumbnail nije nađen na file system-u: {thumb_path} (URL: {first_url})"
    )
    with Image.open(thumb_path) as thumb:
        assert thumb.mode in ("RGB", "L"), (
            f"AC10 contract: format='JPEG' MORA gubiti alpha (mode RGB/L); "
            f"dobio mode={thumb.mode} u {thumb_path}"
        )


def test_responsive_picture_format_png_preserves_alpha(
    temp_media_root, large_png_with_alpha_bytes
):
    """AC10: Eksplicitni `format='PNG'` preserve-uje alpha channel u output thumbnail-u.

    FIX-5 (TEA BUG#2): prethodno je test bio tautološki — proveravao samo da `.png`
    string postoji u HTML-u, što bi proslo cak i kad bi se ulazni `logo.png` echo-ovao
    kao fallback. Sad otvara stvarni thumbnail kroz Pillow i verifikuje da je mode
    `RGBA` ili `LA` (alpha channel preserved per AC10 contract).

    Story 2.6 (Brand Listing) MUST koristiti `{% responsive_picture brand.logo
    alt=brand.name format='PNG' %}` da brand logo zadrži transparent background.
    """
    brand = _create_brand_with_logo(large_png_with_alpha_bytes, filename="logo.png")

    html = _render(
        "{% load media_tags %}{% responsive_picture brand.logo alt='Brand' format='PNG' %}",
        {"brand": brand},
    )

    # Step 1: ekstenzija check
    assert ".png" in html, (
        f"format='PNG' override mora generisati .png thumbnail-ove; dobio:\n{html}"
    )

    # Step 2: kanonski AC10 contract verifikacija — Pillow mode mora biti RGBA/LA
    first_url = _first_srcset_url(html)
    thumb_path = _url_to_filesystem_path(first_url)
    assert thumb_path.exists(), (
        f"Generisani thumbnail nije nađen na file system-u: {thumb_path} (URL: {first_url})"
    )
    with Image.open(thumb_path) as thumb:
        assert thumb.mode in ("RGBA", "LA"), (
            f"AC10 contract: format='PNG' MORA preserve-ovati alpha (mode RGBA/LA); "
            f"dobio mode={thumb.mode} u {thumb_path}"
        )
