"""JEDNOKRATNA pomocna skripta — cita lokalnu bazu i generise profile2.py + seed asset-e.

NIJE deo runtime aplikacije i NIJE Django management command (namerno — nema potrebe da
zivi u INSTALLED_APPS command discovery-ju). Pokrece se RUCNO, po potrebi, kad lokalni
sadrzaj (proizvodi/slike/blog) naraste ili se promeni i profil 2 treba osveziti.

STA RADI
--------
1. Cita SVE "rucno" unete entitete iz baze (Brand/Series/Category/Subcategory/Product/
   ProductImage/ProductSpecification/ProductBrochure/ProductTestimonial/ProductSimilar/blog)
   — ISKLJUCUJE sve sto su napravile data migracije brands/0003 i brands/0004
   (MIGRATION_* konstante ispod - mirror clear_content.py MIGRATION_SEEDED_PRODUCT_SLUGS).
2. Kopira STVARNO REFERENCIRANE media fajlove u
   apps/core/management/commands/_seed_profiles/assets/, uz resize+recompress (Pillow) da
   ne nosimo desetine MB neoptimizovanih fotografija u git.
3. Ispisuje apps/core/management/commands/_seed_profiles/profile2.py — CIST PODATAK u
   PROFILE_2 shape-u koji seed_sample_data.py ocekuje (vidi taj fajl za seed logiku).

STA NE RADI
-----------
Ne dira bazu (read-only osim sto Pillow cita fajlove sa diska). Ne brise stare asset-e
(ako promenis/obrises proizvod lokalno, stari fajl u assets/ ostaje sirotan — rucno
proveri `git status` posle pokretanja i obrisi rucno ako treba).

POKRETANJE (unutar django kontejnera — repo je bind-mount na /app, pa pisanje ovde
pise direktno u host repo):
    docker compose -f compose/local.yml exec django python ops/seed/generate_profile2_manifest.py

Bezbedno je pokrenuti vise puta — get_or_create/idempotent seed dole je briga
seed_sample_data.py; ova skripta samo REGENERISE profile2.py + assets/ iz trenutnog
stanja baze (overwrite).
"""

from __future__ import annotations

import os
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

import django  # noqa: E402

django.setup()

from PIL import Image  # noqa: E402

from apps.blog.models import Post  # noqa: E402
from apps.blog.models import Tag as BlogTag  # noqa: E402
from apps.brands.models import Brand, Category, Series, Subcategory  # noqa: E402
from apps.products.models import (  # noqa: E402
    Product,
    ProductBrochure,
    ProductSimilar,
    ProductTestimonial,
)

# =============================================================================
# Migracijski sadrzaj — ISKLJUCEN iz profila 2 (referenciramo ga po slugu, ne pravimo)
# Mirror apps/brands/migrations/0003_*.py + 0004_*.py + clear_content.py.
# =============================================================================
MIGRATION_BRAND_SLUGS = {"jeegee", "hzm", "tulip"}
MIGRATION_CATEGORY_SLUGS = {
    "osnovna-obrada-zemljista",
    "priprema-zemljista",
    "masine-za-setvu",
    "radne-masine",
}
MIGRATION_SUBCATEGORY_SLUGS = {
    "mini-utovarivaci",
    "utovarivaci-bez-teleskopa",
    "teleskopski-utovarivaci",
    "telehendleri",
}
MIGRATION_PRODUCT_SLUGS = {"tulip-mix-6m3", "tulip-mix-8m3"}

REPO_ROOT = Path(__file__).resolve().parents[2]
ASSETS_DIR = (
    REPO_ROOT
    / "apps"
    / "core"
    / "management"
    / "commands"
    / "_seed_profiles"
    / "assets"
)
PROFILE2_PATH = (
    REPO_ROOT
    / "apps"
    / "core"
    / "management"
    / "commands"
    / "_seed_profiles"
    / "profile2.py"
)

# Resize ciljevi (max dimenzija u px) + JPEG kvalitet — dovoljno za web prikaz,
# drasticno manje od originala (2000x1274 ~150-200KB -> ~1400px ~40-70KB).
_RESIZE_TARGETS = {
    "gallery": (1200, 72),
    "main": (1200, 72),
    "testimonials": (450, 75),
    "brand_hero": (1400, 72),
    "brand_logo": (400, 82),
}

_missing_assets: list[str] = []


def _optimize_and_copy(src_path: Path, dest_path: Path, target_key: str) -> bool:
    """Resize+recompress sliku iz src_path u dest_path. Vrati True ako je uspelo."""
    if not src_path.exists():
        _missing_assets.append(str(src_path))
        return False
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    max_dim, quality = _RESIZE_TARGETS[target_key]
    with Image.open(src_path) as im:
        im = im.convert("RGB")
        im.thumbnail((max_dim, max_dim), Image.LANCZOS)
        im.save(dest_path, "JPEG", quality=quality, optimize=True)
    return True


def _copy_pdf(src_path: Path, dest_path: Path) -> bool:
    if not src_path.exists():
        _missing_assets.append(str(src_path))
        return False
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    dest_path.write_bytes(src_path.read_bytes())
    return True


def _py_repr(value, indent=0) -> str:
    """Minimalan pretty-printer — dict/list/Decimal/str sa punim dijakritikama (ensure_ascii=False)."""
    pad = "    " * indent
    pad_in = "    " * (indent + 1)
    if isinstance(value, Decimal):
        return f'Decimal("{value}")'
    if value is None:
        return "None"
    if isinstance(value, bool):
        return "True" if value else "False"
    if isinstance(value, (int, float)):
        return repr(value)
    if isinstance(value, str):
        return repr(value)
    if isinstance(value, dict):
        if not value:
            return "{}"
        lines = [f"{pad_in}{k!r}: {_py_repr(v, indent + 1)}," for k, v in value.items()]
        return "{\n" + "\n".join(lines) + f"\n{pad}}}"
    if isinstance(value, (list, tuple)):
        if not value:
            return "[]" if isinstance(value, list) else "()"
        lines = [f"{pad_in}{_py_repr(v, indent + 1)}," for v in value]
        open_c, close_c = ("[", "]") if isinstance(value, list) else ("(", ")")
        return f"{open_c}\n" + "\n".join(lines) + f"\n{pad}{close_c}"
    raise TypeError(f"Ne znam da serijalizujem {type(value)}: {value!r}")


def build_manifest() -> dict:
    manifest: dict = {}

    # -- Brands ---------------------------------------------------------------
    tractor_brands = []
    referenced_brand_slugs = set()
    for brand in Brand.objects.exclude(slug__in=MIGRATION_BRAND_SLUGS).order_by("slug"):
        entry = {
            "slug": brand.slug,
            "name": brand.name_sr,
            "description": brand.description_sr or "",
            "slogan": brand.slogan_sr or "",
        }
        if brand.brand_color:
            entry["brand_color"] = brand.brand_color
        if brand.statistics:
            entry["statistics"] = brand.statistics
        if brand.logo:
            asset_name = f"{brand.slug}-logo.jpg"
            if _optimize_and_copy(
                Path(brand.logo.path), ASSETS_DIR / "brands" / asset_name, "brand_logo"
            ):
                entry["logo_asset"] = asset_name
        if brand.hero_image:
            asset_name = f"{brand.slug}-hero.jpg"
            if _optimize_and_copy(
                Path(brand.hero_image.path),
                ASSETS_DIR / "brands" / asset_name,
                "brand_hero",
            ):
                entry["hero_image_asset"] = asset_name
        tractor_brands.append(entry)
    manifest["tractor_brands"] = tractor_brands

    for product in Product.objects.exclude(
        slug__in=MIGRATION_PRODUCT_SLUGS
    ).select_related("brand"):
        if product.brand.slug in MIGRATION_BRAND_SLUGS:
            referenced_brand_slugs.add(product.brand.slug)
    manifest["referenced_brand_slugs"] = tuple(sorted(referenced_brand_slugs))

    # -- Categories -------------------------------------------------------------
    manual_categories = list(
        Category.objects.exclude(slug__in=MIGRATION_CATEGORY_SLUGS)
    )
    if len(manual_categories) > 1:
        raise SystemExit(
            "Vise od 1 rucne Category — profil2 shape (traktori_category singular) "
            "ne podrzava vise; prosiri manifest/generator na 'categories' listu pre nego "
            f"sto nastavis. Nadjeno: {[c.slug for c in manual_categories]}"
        )
    traktori_category = None
    if manual_categories:
        c = manual_categories[0]
        traktori_category = {
            "slug": c.slug,
            "name": c.name_sr,
            "is_for": c.is_for,
            "display_order": c.display_order,
            "description": c.description_sr or "",
        }
    manifest["traktori_category"] = traktori_category

    referenced_category_slugs = set(
        Subcategory.objects.filter(
            category__slug__in=MIGRATION_CATEGORY_SLUGS
        ).values_list("category__slug", flat=True)
    )
    manifest["referenced_category_slugs"] = tuple(sorted(referenced_category_slugs))

    # -- Subcategories (manuelne + referencirane migracijske, sve koje se koriste) --
    subcategories = []
    for sub in (
        Subcategory.objects.all()
        .select_related("category", "parent")
        .order_by("category__slug", "slug")
    ):
        entry = {
            "slug": sub.slug,
            "category_slug": sub.category.slug,
            "name": sub.name_sr,
            "description": sub.description_sr or "",
            "icon": sub.icon or "",
            "display_order": sub.display_order,
        }
        if sub.parent_id:
            entry["parent_slug"] = sub.parent.slug
        subcategories.append(entry)
    manifest["subcategories"] = subcategories

    # -- Series -------------------------------------------------------------------
    series_list = []
    for s in (
        Series.objects.all().select_related("brand").order_by("brand__slug", "slug")
    ):
        series_list.append(
            {
                "brand_slug": s.brand.slug,
                "slug": s.slug,
                "name": s.name_sr,
                "description": s.description_sr or "",
                "layout_mode": s.layout_mode,
                "display_order": s.display_order,
            }
        )
    manifest["series"] = series_list

    # -- Products (new/used) -------------------------------------------------------
    new_tractors = []
    used_machines = []
    products = (
        Product.objects.exclude(slug__in=MIGRATION_PRODUCT_SLUGS)
        .select_related("brand", "subcategory", "series")
        .order_by("slug")
    )
    for p in products:
        entry = {
            "slug": p.slug,
            "brand_slug": p.brand.slug,
            "name": p.name_sr,
            "description": p.description_sr or "",
            "key_features": list(p.key_features_sr or []),
            "horse_power": p.horse_power,
            "year": p.year,
            "price_eur": p.price_eur,
        }
        if p.subcategory_id:
            entry["subcategory_slug"] = p.subcategory.slug
        if p.series_id:
            entry["series_slug"] = p.series.slug

        if p.main_image:
            asset_name = f"{p.slug}-main.jpg"
            if _optimize_and_copy(
                Path(p.main_image.path),
                ASSETS_DIR / "products" / "main" / asset_name,
                "main",
            ):
                entry["main_image_asset"] = asset_name

        images = []
        for img in p.images.all().order_by("order"):
            src = Path(img.image.path)
            asset_name = src.name
            if _optimize_and_copy(
                src, ASSETS_DIR / "products" / "gallery" / asset_name, "gallery"
            ):
                images.append(
                    {
                        "asset": asset_name,
                        "order": img.order,
                        "alt_text": img.alt_text_sr or "",
                    }
                )
        if images:
            entry["images"] = images

        specs = []
        for spec in p.specifications.all().order_by("section", "order", "id"):
            specs.append(
                {
                    "section": spec.section,
                    "key": spec.key_sr,
                    "value": spec.value_sr,
                    "order": spec.order,
                }
            )
        if specs:
            entry["specs"] = specs

        if p.condition == Product.ConditionChoice.NEW:
            new_tractors.append(entry)
        else:
            used_machines.append(entry)
    manifest["new_tractors"] = new_tractors
    manifest["used_machines"] = used_machines
    manifest["headline_specs"] = None

    # -- Brochures ------------------------------------------------------------------
    brochures = []
    for b in (
        ProductBrochure.objects.all()
        .select_related("product")
        .order_by("product__slug")
    ):
        entry = {"product_slug": b.product.slug, "title": b.title_sr or ""}
        if b.pdf_file:
            src_name = Path(b.pdf_file.name).name
            asset_name = (
                src_name
                if src_name.startswith(b.product.slug)
                else f"{b.product.slug}-{src_name}"
            )
            if _copy_pdf(
                Path(b.pdf_file.path),
                ASSETS_DIR / "products" / "brochures" / asset_name,
            ):
                entry["pdf_asset"] = asset_name
        if b.cover_thumbnail_image:
            asset_name = f"{b.product.slug}-cover.jpg"
            if _optimize_and_copy(
                Path(b.cover_thumbnail_image.path),
                ASSETS_DIR / "products" / "brochure_covers" / asset_name,
                "gallery",
            ):
                entry["cover_thumbnail_asset"] = asset_name
        brochures.append(entry)
    manifest["brochures"] = brochures

    # -- Testimonials -----------------------------------------------------------------
    testimonials = []
    for t in (
        ProductTestimonial.objects.all()
        .select_related("product")
        .order_by("product__slug", "order", "id")
    ):
        entry = {
            "product_slug": t.product.slug,
            "author_name": t.author_name,
            "location": t.location_sr or "",
            "quote": t.quote_sr or "",
            "order": t.order,
        }
        if t.photo:
            asset_name = Path(t.photo.name).name
            if _optimize_and_copy(
                Path(t.photo.path),
                ASSETS_DIR / "products" / "testimonials" / asset_name,
                "testimonials",
            ):
                entry["photo_asset"] = asset_name
        testimonials.append(entry)
    manifest["testimonials"] = testimonials

    # -- Similar ------------------------------------------------------------------------
    similar = []
    for s in (
        ProductSimilar.objects.all()
        .select_related("product", "related_product")
        .order_by("product__slug", "order")
    ):
        similar.append(
            {
                "product_slug": s.product.slug,
                "related_product_slug": s.related_product.slug,
                "order": s.order,
            }
        )
    manifest["similar"] = similar

    # -- Blog (Category je uklonjen — post-launch odluka; samo Tag + Post) ------------------
    blog = None
    blog_posts = list(Post.objects.all().order_by("slug"))
    if blog_posts:
        tags = list(BlogTag.objects.all())
        if len(tags) > 1:
            raise SystemExit(
                f"Vise od 1 BlogTag — prosiri manifest. Nadjeno: {[t.slug for t in tags]}"
            )
        tag = tags[0] if tags else None
        posts = []
        for post in blog_posts:
            posts.append(
                {
                    "slug": post.slug,
                    "title": post.title_sr,
                    "perex": post.perex_sr or "",
                    "body": post.body_sr or "",
                }
            )
        blog = {
            "tag": {"slug": tag.slug, "name": tag.name_sr} if tag else None,
            "posts": posts,
        }
    manifest["blog"] = blog

    return manifest


_HEADER = '''"""Profil 2 — kurirani demo sadrzaj (1:1 snapshot lokalne baze), AUTO-GENERISAN.

NE UREDJUJ RUCNO — regenerisi kroz ``ops/seed/generate_profile2_manifest.py`` (cita
lokalnu bazu, kopira+optimizuje seed asset-e, ispisuje ovaj fajl). Rucne izmene ce biti
pregazene na sledecem pokretanju generatora.

Ovaj modul je CIST PODATAK. Seed logika (get_or_create po eksplicitnom slug-u,
modeltranslation `_sr` kolone, counters, atomicity, production guard, FileField attach-after-
create) zivi u ``seed_sample_data.py`` i deli se sa profilom 1 — ovde se NE pise logika.

Migracijski sadrzaj (brands/0003, brands/0004 — Jeegee/HZM/Tulip brend + prikljucne
kategorije/potkategorije + tulip-mix-6m3/8m3 proizvodi) je ISKLJUCEN — referenciran je kroz
``referenced_brand_slugs`` / ``referenced_category_slugs`` / ``subcategory_slug`` /
``brand_slug``, NE ponovo kreiran.

Pokretanje: ``just dev-manage seed_sample_data --profile=2``
"""

from __future__ import annotations

from decimal import Decimal

'''


def render_profile2(manifest: dict) -> str:
    lines = [_HEADER, "PROFILE_2: dict = "]
    lines.append(_py_repr(manifest))
    lines.append("\n")
    return "".join(lines)


def main():
    manifest = build_manifest()
    content = render_profile2(manifest)
    PROFILE2_PATH.write_text(content, encoding="utf-8")
    print(f"Napisano: {PROFILE2_PATH.relative_to(REPO_ROOT)} ({len(content)} bytes)")
    print(
        f"Brendovi: {len(manifest['tractor_brands'])} (+ referenced: {manifest['referenced_brand_slugs']})"
    )
    print(
        f"Kategorije (referenced migracijske): {manifest['referenced_category_slugs']}"
    )
    print(f"Potkategorije: {len(manifest['subcategories'])}")
    print(f"Series: {len(manifest['series'])}")
    print(f"Novi proizvodi: {len(manifest['new_tractors'])}")
    print(f"Polovni proizvodi: {len(manifest['used_machines'])}")
    n_images = sum(
        len(p.get("images", []))
        for p in manifest["new_tractors"] + manifest["used_machines"]
    )
    n_specs = sum(
        len(p.get("specs", []))
        for p in manifest["new_tractors"] + manifest["used_machines"]
    )
    print(f"ProductImage redova u manifestu: {n_images}")
    print(f"ProductSpecification redova u manifestu: {n_specs}")
    print(f"Brošure: {len(manifest['brochures'])}")
    print(f"Testimonijali: {len(manifest['testimonials'])}")
    print(f"Slični proizvodi: {len(manifest['similar'])}")
    print(f"Blog: {'DA' if manifest['blog'] else 'NE'}")
    if _missing_assets:
        print()
        print(
            f"UPOZORENJE — {len(_missing_assets)} fajl(ova) nije preneto (izostavljeno iz manifesta):"
        )
        for m in _missing_assets:
            print(f"  - {m}")


if __name__ == "__main__":
    main()
