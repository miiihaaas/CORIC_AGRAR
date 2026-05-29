"""Story 2.3 — sorl-thumbnail integration testovi (RED phase TDD).

Pokriva AC6 — Thumbnail-ovi se generišu lazy on-demand u `media/thumbnails/` direktorijumu
sa KVStore cache mappingom. Verifikuje da:
- Prvi render `{% responsive_picture %}` kreira fajlove u media/thumbnails/
- Drugi render istog tag-a hituje KVStore cache (no nova fajla)
- Thumbnail format je JPEG bez obzira na source format (PNG → JPG bez format kwarg-a)
- Thumbnail file size < source file size (na realističnom 2400×1800 noise source-u)

Test discipline (per project-context.md § Mock policy):
- NEMA mock-a sorl.thumbnail — real KVStore + real file system write u tmp_path
- NEMA mock-a Pillow — real image generation kroz fixture-e
- `temp_media_root` fixture override-uje MEDIA_ROOT na tmp_path (per-test isolation)
- pytest.mark.django_db (KVStore tabela ima ORM operacije)

Pokrenuti kroz Docker (libmagic SEGFAULT na Windows host-u per Decision MP-D6):
    docker compose -f compose/local.yml run --rm django uv run pytest apps/media_pipeline/tests/test_thumbnails.py -v

Refs:
- 2-3-image-pipeline-sa-sorl-thumbnail-responsive-srcset.md (story spec, AC6)
- 2-3-interface-contract.md (TEA canonical contract)
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.template import Context, Template
from PIL import Image

pytestmark = pytest.mark.django_db


# =============================================================================
# Helpers — kreiraju Product sa real image upload-om za sorl-thumbnail integraciju
# =============================================================================


def _create_product_with_image(image_bytes: bytes, *, filename: str = "main.jpg"):
    """Kreira Product sa upload-ovanom main_image (real file na disk-u kroz ImageField)."""
    from apps.brands.models import Brand
    from apps.products.models import Product

    brand = Brand.objects.create(name="Test Brand", brand_color="", statistics=[])
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


def _render_responsive_picture(product) -> str:
    """Helper: render `{% responsive_picture product.main_image alt='T' %}`."""
    t = Template(
        "{% load media_tags %}{% responsive_picture product.main_image alt='T' %}"
    )
    return t.render(Context({"product": product}))


# =============================================================================
# AC6 — Thumbnail lazy generation + KVStore caching
# =============================================================================


def test_thumbnail_400w_generated_lazy_on_first_render(
    temp_media_root, realistic_source_image_bytes
):
    """AC6: Prvi render `{% responsive_picture %}` kreira thumbnail fajl(ove) u media/thumbnails/.

    Lazy generation: sorl-thumbnail NE kreira thumbnail pri Product.save() —
    samo pri prvom HTTP GET-u (render template-a koji poziva `{% thumbnail %}`).

    FIX-7 (Dev B + Architect): prethodno je test postavljao `settings.THUMBNAIL_DIRNAME`
    što je no-op — sorl koristi `THUMBNAIL_PREFIX` (kanonski naziv), set u base.py.
    Test se i dalje oslanja na `media/thumbnails/` putanju definisanu kroz
    `THUMBNAIL_PREFIX = 'thumbnails/'`.
    """
    product = _create_product_with_image(realistic_source_image_bytes)

    thumbnails_dir = Path(temp_media_root) / "thumbnails"

    # Pre render-a: nema thumbnail fajlova
    assert not thumbnails_dir.exists() or not any(thumbnails_dir.rglob("*")), (
        "Pre render-a media/thumbnails/ mora biti prazan ili ne-postojeći"
    )

    # Prvi render trigger-uje thumbnail generation
    _render_responsive_picture(product)

    # Posle render-a: thumbnails dir postoji i sadrži fajlove
    assert thumbnails_dir.exists(), (
        f"Posle render-a media/thumbnails/ mora postojati u {thumbnails_dir}"
    )
    thumb_files = list(thumbnails_dir.rglob("*.*"))
    # FIX-11 (TEA TEST_GAP#6): exact count — `>=3` bi prošao i da bug duplira thumbnail-ove.
    # Tag generiše tačno 3 varijante (400/800/1600w); više od 3 znači regression.
    assert len(thumb_files) == 3, (
        f"Expected exactly 3 thumbnails (400/800/1600), got {len(thumb_files)}: "
        f"{[t.name for t in thumb_files]}"
    )


def test_thumbnail_cached_on_second_render(
    temp_media_root, realistic_source_image_bytes
):
    """AC6: Drugi render istog `{% responsive_picture %}` koristi KVStore cache hit.

    Posle prvog render-a, KVStore mapira (image_path, geometry) → thumbnail_url.
    Drugi render NE kreira nove fajlove — koristi postojeće preko cache hit.
    """
    product = _create_product_with_image(realistic_source_image_bytes)
    thumbnails_dir = Path(temp_media_root) / "thumbnails"

    # Prvi render
    _render_responsive_picture(product)
    files_after_first = sorted(p.name for p in thumbnails_dir.rglob("*.*"))

    # Drugi render
    _render_responsive_picture(product)
    files_after_second = sorted(p.name for p in thumbnails_dir.rglob("*.*"))

    assert files_after_first == files_after_second, (
        f"Drugi render mora hit-ovati KVStore cache; "
        f"pre={files_after_first}, posle={files_after_second}"
    )
    assert len(files_after_second) == 3, (
        "Cache hit ne sme menjati broj thumbnail fajlova (mora ostati 3)"
    )


def test_thumbnail_size_smaller_than_source(
    temp_media_root, realistic_source_image_bytes
):
    """AC6: Generated thumbnails (400w/800w/1600w) MUST biti smaller than source u file bytes.

    Validacija ima smisao SAMO na realističnom source image-u (≥2000px wide, high-entropy
    noise per `realistic_source_image_bytes` fixture). Solid-color slike kompresuju do
    ~5-10KB i thumbnail bi mogao biti veći zbog header overhead-a — NIJE valid test source.
    """
    source_size = len(realistic_source_image_bytes)
    # Sanity check fixture-a: realistic source MORA biti ≥100KB (high-entropy noise)
    assert source_size >= 100 * 1024, (
        f"Fixture realistic_source_image_bytes je previše mali ({source_size} bytes) — "
        f"verifikuj Image.effect_noise generacija u conftest.py"
    )

    product = _create_product_with_image(realistic_source_image_bytes)
    thumbnails_dir = Path(temp_media_root) / "thumbnails"

    _render_responsive_picture(product)

    thumb_files = list(thumbnails_dir.rglob("*.*"))
    assert len(thumb_files) == 3, (
        f"Mora imati tačno 3 thumbnail-a, dobio: {len(thumb_files)}"
    )

    for thumb in thumb_files:
        thumb_size = thumb.stat().st_size
        assert thumb_size < source_size, (
            f"Thumbnail {thumb.name} ({thumb_size} bytes) MORA biti manji od source-a "
            f"({source_size} bytes) — heuristika za realistic high-entropy source"
        )


def test_thumbnail_format_is_jpeg_regardless_of_source(temp_media_root, valid_png_bytes):
    """AC6: PNG source → JPEG output (per THUMBNAIL_FORMAT='JPEG' setting + default format kwarg).

    Story 2.3 default je JPEG za bandwidth optimizaciju (Decision MP-D5). PNG source ulazi
    u `get_thumbnail(image, "400", format="JPEG")` → output je `.jpg` bez obzira na source.

    Caller mora eksplicitno `format='PNG'` da preserve PNG (testirano u test_templatetags.py).

    NOTE: ovaj test koristi sample PNG (10×10) — NIJE realistic source. Fokus testa je
    format konverzija, NE size ratio.
    """
    # Generišemo veći PNG (1000×800) jer sorl-thumbnail neće upscale-ovati 10×10 na 400w
    img = Image.new("RGB", (1000, 800), color="blue")
    buf = BytesIO()
    img.save(buf, format="PNG")
    png_bytes = buf.getvalue()

    product = _create_product_with_image(png_bytes, filename="source.png")
    thumbnails_dir = Path(temp_media_root) / "thumbnails"

    _render_responsive_picture(product)

    thumb_files = list(thumbnails_dir.rglob("*.*"))
    assert len(thumb_files) >= 1, f"Mora imati ≥1 thumbnail; dobio: {len(thumb_files)}"

    jpeg_thumbs = [t for t in thumb_files if t.suffix.lower() in (".jpg", ".jpeg")]
    assert len(jpeg_thumbs) == len(thumb_files), (
        f"Sve thumbnail-ove MORAJU biti .jpg/.jpeg (PNG source → JPEG output per "
        f"THUMBNAIL_FORMAT='JPEG'); dobio sa drugačijim ekstenzijama: "
        f"{[t.name for t in thumb_files if t not in jpeg_thumbs]}"
    )
