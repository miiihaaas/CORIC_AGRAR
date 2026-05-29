"""Media pipeline template tags — responsive srcset helper za `<picture>` element.

Story 2.3 (Epic 2). Konzumiran od:
- Story 2.6 (Brand Listing) — brand.logo + product.main_image
- Story 2.7 (Product Detail) — main image, galerija, varijante, testimonijali
- Story 2.8/2.9 (Tractor/Used Listing) — product.main_image u HTMX partial
- Epic 3 (Home strana) — featured carousel + brand grid
- Epic 5 (Blog) — blog_post.cover_image

sorl-thumbnail lazy generation: thumbnail-ovi se kreiraju on-demand
pri prvom HTTP GET-u na URL slike, NE post-save signal. KVStore (cached_db)
cuva mapping {field+geometry -> thumbnail_url} za fast cache hit.
"""

from __future__ import annotations

from django import template
from django.conf import settings
from django.db.models.fields.files import ImageFieldFile
from sorl.thumbnail import get_thumbnail

register = template.Library()

# Standardni breakpoint-i (DESIGN.md responsive grid):
# 400w   — mobilni viewport (max 480px)
# 800w   — tablet / small desktop (481-1024px)
# 1600w  — large desktop / retina (>1024px)
RESPONSIVE_WIDTHS: tuple[int, ...] = (400, 800, 1600)


@register.inclusion_tag("media_pipeline/responsive_picture.html")
def responsive_picture(
    image: ImageFieldFile | None,
    alt: str = "",
    sizes: str = "(max-width: 768px) 100vw, 50vw",
    loading: str = "lazy",
    css_class: str = "",
    crop: str = "center",
    format: str = "JPEG",
) -> dict:
    """Render `<picture>` element sa srcset varijantama 400w/800w/1600w."""
    if not image or not getattr(image, "name", ""):
        return {"image": None, "alt": alt, "css_class": css_class}

    quality = getattr(settings, "THUMBNAIL_QUALITY", 85)

    variants = []
    fallback_thumb = None
    for width in RESPONSIVE_WIDTHS:
        thumb = get_thumbnail(
            image, f"{width}", crop=crop, quality=quality, format=format
        )
        variants.append({"url": thumb.url, "width": width})
        fallback_thumb = thumb  # poslednji generisan = najveća varijanta = fallback

    fallback = variants[-1]
    srcset_str = ", ".join(f"{v['url']} {v['width']}w" for v in variants)

    # FIX-8 (Dev B PERFORMANCE): width/height moraju biti REAL dimenzije fallback
    # thumbnail-a (a ne hardcoded 1600). Ako source < 1600px, sorl ne upscale-uje pa
    # je stvarna širina manja → browser CLS kalkulacija bi bila pogrešna sa hardcoded
    # vrednošću. `thumb.width`/`thumb.height` su sorl ImageFile properties (loaded iz
    # KVStore meta-a, no extra Pillow open).
    default_width = (
        fallback_thumb.width if fallback_thumb is not None else fallback["width"]
    )
    default_height = fallback_thumb.height if fallback_thumb is not None else None

    return {
        "image": image,
        "alt": alt,
        "sizes": sizes,
        "loading": loading,
        "css_class": css_class,
        "fallback_url": fallback["url"],
        "srcset": srcset_str,
        "default_width": default_width,
        "default_height": default_height,
    }
