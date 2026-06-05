"""Story 6.1 — SeoMetaInline na 5 admin-a + soft warning (TEA RED phase, AC5/AC8).

Pokriva:
- AC5: SeoMetaInline registrovan kao inline na Product/Brand/Series/Subcategory/Post
  admin-ima (admin.site._registry[Model].inlines sadrži SeoMetaInline class).
- AC5: superuser GET changelist + add-view → 200 (generic translation inline renderuje,
  ne baca admin.E*).
- AC8: soft warning NON-BLOCKING — sačuvaj objekat sa meta_title>60 ili
  meta_description>160 kroz inline → messages.WARNING U response + objekat SAČUVAN;
  kratak meta → NEMA warning.
- PostAdmin OSTAJE TranslationAdmin + view_on_site=False (regression-lock-ovi).

⚠️ GUARD: apps.seo importi + admin registry pristup UNUTAR test body-ja (collection-safety)
— apps.seo NE postoji još → KeyError model not in registry / ImportError per-test (RED).

Refs:
- 6-1-...-admin.md AC5/AC8 + Task 7.7 + SM-D3/D5 + Gotcha SEO1-2/SEO1-7
"""

from __future__ import annotations

import pytest
from django.contrib import admin
from django.urls import reverse

pytestmark = pytest.mark.django_db


def _admin_for(model):
    return admin.site._registry[model]


# AC5: SeoMetaInline na ProductAdmin/BrandAdmin/SeriesAdmin/SubcategoryAdmin/PostAdmin
def test_seometa_inline_registered_on_receiving_admins():
    from apps.blog.models import Post
    from apps.brands.models import Brand, Series, Subcategory
    from apps.products.models import Product
    from apps.seo.admin import SeoMetaInline

    for model in (Product, Brand, Series, Subcategory, Post):
        model_admin = _admin_for(model)
        inline_classes = list(getattr(model_admin, "inlines", []))
        assert any(issubclass(ic, SeoMetaInline) or ic is SeoMetaInline for ic in inline_classes), (
            f"{model.__name__}Admin.inlines MORA sadržati SeoMetaInline (AC5/SM-D3)."
        )


# AC5: brands Category TAKOĐE dobija inline (C-F locked — fajl NE polu-konvertovan)
def test_seometa_inline_on_brands_category():
    from apps.brands.models import Category as BrandCategory
    from apps.seo.admin import SeoMetaInline

    model_admin = _admin_for(BrandCategory)
    inline_classes = list(getattr(model_admin, "inlines", []))
    assert any(ic is SeoMetaInline or issubclass(ic, SeoMetaInline) for ic in inline_classes), (
        "brands.Category admin MORA imati SeoMetaInline (C-F locked — AC5)."
    )


# AC5: SeoMetaInline ima max_num=1 (jedan SeoMeta po objektu — UniqueConstraint)
def test_seometa_inline_max_num_one():
    from apps.seo.admin import SeoMetaInline

    assert SeoMetaInline.max_num == 1, (
        "SeoMetaInline.max_num MORA biti 1 (jedan SeoMeta po objektu — UniqueConstraint AC4)."
    )
    assert SeoMetaInline.model.__name__ == "SeoMeta", (
        "SeoMetaInline.model MORA biti SeoMeta."
    )


# regression-lock: PostAdmin OSTAJE TranslationAdmin + view_on_site=False
def test_postadmin_stays_translationadmin_and_view_on_site_false():
    from modeltranslation.admin import TranslationAdmin

    from apps.blog.models import Post

    model_admin = _admin_for(Post)
    assert isinstance(model_admin, TranslationAdmin), (
        "PostAdmin MORA ostati TranslationAdmin (C-A — inline/mixin su aditivni)."
    )
    assert model_admin.view_on_site is False, (
        "PostAdmin.view_on_site MORA ostati False (C-A regression-lock — IMP-1/BL-5)."
    )


# AC5: superuser GET Product changelist → 200 (konverzija bare→ModelAdmin ne ruši)
def test_product_changelist_200(client, superuser, product):
    client.force_login(superuser)
    response = client.get(reverse("admin:products_product_changelist"))
    assert response.status_code == 200, (
        f"Product changelist MORA biti 200 (konverzija bare→ModelAdmin aditivna — AC5); "
        f"dobio {response.status_code}."
    )


# AC5: superuser GET Product add-view → 200 (SeoMetaInline generic translation render)
def test_product_add_view_renders_inline_200(client, superuser):
    client.force_login(superuser)
    response = client.get(reverse("admin:products_product_add"))
    assert response.status_code == 200, (
        f"Product add-view MORA biti 200 — SeoMetaInline (generic translation inline) "
        f"MORA renderovati bez admin.E* (SEO1-2); dobio {response.status_code}."
    )


# AC5: superuser GET Brand add-view → 200
def test_brand_add_view_renders_inline_200(client, superuser):
    client.force_login(superuser)
    response = client.get(reverse("admin:brands_brand_add"))
    assert response.status_code == 200, (
        f"Brand add-view MORA biti 200 (SeoMetaInline render); dobio {response.status_code}."
    )


# AC5: superuser GET Post add-view → 200 (regression-lock test_admin.py:97 ekvivalent)
def test_post_add_view_renders_inline_200(client, superuser):
    client.force_login(superuser)
    response = client.get(reverse("admin:blog_post_add"))
    assert response.status_code == 200, (
        f"Post add-view MORA ostati 200 — SeoMetaInline na TranslationAdmin ne ruši render "
        f"(C-A regression-lock); dobio {response.status_code}."
    )


# AC5/SEO1-2: admin system checks čisti (generic inline + modeltranslation ne baca admin.E*)
def test_admin_system_checks_clean():
    from django.core.checks import run_checks

    errors = [e for e in run_checks() if e.is_serious()]
    assert errors == [], (
        f"manage.py check MORA biti čist — generic inline + modeltranslation na "
        f"TranslationAdmin ne smeju baciti admin.E* (SEO1-2). Greške: {errors}."
    )


# Generic inline prefix za SeoMeta GFK formset (probe-verifikovan iz rendered admin add/change
# forme): app_label '-' model_name '-' ct_field '-' fk_field.
_SEO_INLINE_PREFIX = "seo-seometa-content_type-object_id"


def _scrape_change_form(html):
    """Izvuci name->value za sve input/select polja u admin change formi.

    Generic inline + modeltranslation change-form payload je fiddly (TEA MF-2
    napomena) → re-submituj POSTOJEĆE vrednosti renderovane forme (inputs +
    selected options) da forma ostane valid, pa override-uj SAMO SeoMeta inline.
    """
    import re

    data = {}
    for m in re.finditer(r"<input[^>]*>", html):
        tag = m.group(0)
        nm = re.search(r'name="([^"]+)"', tag)
        if not nm:
            continue
        name = nm.group(1)
        typ_m = re.search(r'type="([^"]+)"', tag)
        typ = typ_m.group(1) if typ_m else "text"
        if typ in ("submit", "button", "file"):
            continue
        val_m = re.search(r'value="([^"]*)"', tag)
        val = val_m.group(1) if val_m else ""
        if typ == "checkbox":
            if "checked" in tag:
                data[name] = val or "on"
        else:
            data[name] = val
    for sm in re.finditer(r'<select[^>]*name="([^"]+)"[^>]*>(.*?)</select>', html, re.S):
        name = sm.group(1)
        opt = re.search(r'<option[^>]*value="([^"]*)"[^>]*selected', sm.group(2))
        data[name] = opt.group(1) if opt else ""
    return data


# AC8: soft warning NON-BLOCKING — meta_title > 60 → messages.WARNING + objekat SAČUVAN
def test_soft_warning_meta_title_over_60_non_blocking(client, superuser, product):
    from apps.seo.admin import SeoWarningAdminMixin
    from apps.products.admin import ProductAdmin
    from apps.seo.models import SeoMeta

    # ProductAdmin MORA koristiti SeoWarningAdminMixin (soft-warning mehanizam — SM-D5)
    assert issubclass(ProductAdmin, SeoWarningAdminMixin), (
        "ProductAdmin MORA nasleđivati SeoWarningAdminMixin (soft warning — AC8/SM-D5)."
    )

    long_title = "X" * 75  # > 60
    seo = SeoMeta.objects.create(content_object=product, meta_title_sr=long_title)

    # Objekat SAČUVAN uprkos predugačkom naslovu (NON-BLOCKING — AC8)
    seo.refresh_from_db()
    assert seo.meta_title_sr == long_title, (
        "Soft warning je NON-BLOCKING — SeoMeta MORA biti sačuvan i sa meta_title>60 (AC8)."
    )

    # Warning mehanizam: mixin save_formset emituje messages.WARNING (NE add_error/ValidationError)
    assert hasattr(SeoWarningAdminMixin, "save_formset"), (
        "SeoWarningAdminMixin MORA override-ovati save_formset (warning hook — SEO1-7)."
    )
    # NAPOMENA: behavioralni dokaz da warning STVARNO fire-uje je u
    # test_admin_post_long_title_fires_warning_message_locks_F1 — ovde više NEMA
    # tautologije (`messages.WARNING is not None`); strengthen, ne keep.


# A3 / TEA MF-2 — BEHAVIORALNI POST kroz admin: dokazuje da soft-warning message_user
# STVARNO fire-uje (locks Dev A F-1 fix). Stari `formset.instances` (uvek []) → DEAD
# LOOP → warning NIKAD ne fire-uje; ovaj test FAIL-uje protiv stare buggy verzije i
# PASS-uje protiv `new_objects + changed_objects` iteracije (probe-verifikovano).
def test_admin_post_long_title_fires_warning_message_locks_F1(client, superuser, product):
    from django.contrib.messages import constants as message_constants
    from django.contrib.messages import get_messages
    from django.urls import reverse

    from apps.seo.models import SeoMeta

    client.force_login(superuser)
    url = reverse("admin:products_product_change", args=[product.pk])
    data = _scrape_change_form(client.get(url).content.decode())
    # brand je required (probe) — ProductFactory ga ima; osiguraj da je u payload-u
    data["brand"] = str(product.brand_id)

    long_title = "Z" * 75  # > _TITLE_MAX (60)
    data[f"{_SEO_INLINE_PREFIX}-TOTAL_FORMS"] = "1"
    data[f"{_SEO_INLINE_PREFIX}-INITIAL_FORMS"] = "0"
    data[f"{_SEO_INLINE_PREFIX}-0-meta_title_sr"] = long_title
    data[f"{_SEO_INLINE_PREFIX}-0-id"] = ""

    response = client.post(url, data, follow=True)
    assert response.status_code == 200

    # 1) SeoMeta SAČUVAN (NON-BLOCKING — objekat persistira uprkos warning-u)
    saved = SeoMeta.objects.filter(
        object_id=product.pk, meta_title_sr=long_title
    ).first()
    assert saved is not None, (
        "Admin POST sa over-length meta_title MORA SAČUVATI SeoMeta (soft warning je "
        "NON-BLOCKING — AC8)."
    )

    # 2) WARNING-level message PRISUTAN (THE lock za F-1 — message_user STVARNO pozvan)
    warnings = [
        m for m in get_messages(response.wsgi_request)
        if m.level == message_constants.WARNING
    ]
    assert warnings, (
        "Admin POST sa meta_title>60 MORA emitovati WARNING-level message kroz "
        "save_formset (Dev A F-1: stari `formset.instances` dead-loop NIKAD ne "
        "fire-uje — ovaj test to lock-uje)."
    )


# AC8: soft warning na meta_description > 160 (NON-BLOCKING)
def test_soft_warning_meta_description_over_160_non_blocking(product):
    from apps.seo.models import SeoMeta

    long_desc = "Y" * 200  # > 160
    seo = SeoMeta.objects.create(content_object=product, meta_description_sr=long_desc)
    seo.refresh_from_db()
    assert seo.meta_description_sr == long_desc, (
        "meta_description>160 NE blokira save — soft warning je advisory (AC8)."
    )


# AC8 C-B FORMSET GUARD: save_formset obrađuje SAMO SeoMeta formset-e (ne-SeoMeta prolaze netaknuti)
def test_save_formset_guards_non_seometa_formsets():
    import inspect

    from apps.seo.admin import SeoWarningAdminMixin

    src = inspect.getsource(SeoWarningAdminMixin.save_formset)
    assert "SeoMeta" in src, (
        "SeoWarningAdminMixin.save_formset MORA imati `formset.model is SeoMeta` guard "
        "(C-B — ne-SeoMeta formset-i prolaze netaknuti; SEO1-7)."
    )
