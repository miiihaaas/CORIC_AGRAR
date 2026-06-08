"""Story 8.6 — Product CRUD Admin sa Multi-locale (TEA RED phase).

DEFINES the contract Dev must satisfy. Maps to the 12 ACs + Testing section of
`8-6-product-crud-admin-sa-multi-locale.md`. Canonical contract:
`8-6-product-crud-admin-sa-multi-locale-interface-contract.md`.

RUN (MUST go through Docker — libmagic/python-magic + Pillow + poppler are NOT on the
Windows host):
    just test apps/products/tests/test_8_6_product_crud_admin.py -v

RED expectation: `apps/products/admin.py` is still the minimal 6.1 stub
(`ProductAdmin(SeoWarningAdminMixin, ModelAdmin)` with `inlines=[SeoMetaInline]`, no
`ProductAdminForm`, no 6 domain inlines, no `MAX_*_UPLOAD_SIZE`, no `save_related`
publish-gate, no `main_image_preview`, no `list_select_related`). So nearly every test
MUST fail/error. EXCEPTIONS (labeled inline as INVARIANT-LOCK — legitimately green today):
- `test_ac2_seometa_inline_still_on_productadmin` — 6.1 already has it.
- `test_ac11_seowarning_mixin_in_mro` — 6.1 already subclasses it.
- `test_ac11_editor_has_change_perm_on_product` — 8.2 already granted it.
- `test_ac12_no_pending_migration_for_products` — admin-only story, 0 schema by design.

────────────────────────────────────────────────────────────────────────────────
COLLECTION-SAFETY: all `apps.products.admin` / `ProductAdminForm` imports are INSIDE
test bodies (lazy) so a missing symbol fails that test individually (true RED), never
aborts collection of the whole file.

AUTH: authenticate with `force_login` (NEVER `client.login` — django-axes from 8.1
pollutes lockout state through authenticate(); established project lesson).

ADMIN URL: always `reverse("admin:products_product_*")` — admin is at bare /admin-coric/
(8.1), never hardcode.

EDITOR USER: `is_staff` + member of `Editor` group. The `Editor` group is created by the
8.2 `sync_rbac_groups` post_migrate handler during test-DB setup, and already carries
products.add/change/delete/view + all 6 related (EDITOR_CONTENT_MODELS). 8.6 does NOT
re-grant (SM-D8).

Refs: 8-6-...md (AC1-AC12, SM-D1..D9, G-1..G-16, Testing) + interface contract +
apps/brands/tests/test_brand_crud_admin.py (canonical pattern this story mirrors).
"""

from __future__ import annotations

import io

import pytest
from django.contrib import admin
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

pytestmark = pytest.mark.django_db


# ──────────────────────────────────────────────────────────────────────────────
# Media isolation + users
# ──────────────────────────────────────────────────────────────────────────────
@pytest.fixture(autouse=True)
def _isolate_media_root(settings, tmp_path):
    """Per-test MEDIA_ROOT isolation (established project pattern)."""
    settings.MEDIA_ROOT = str(tmp_path)


@pytest.fixture
def superuser(django_user_model):
    """Superuser for admin smoke (django_user_model — NEVER direct User import)."""
    return django_user_model.objects.create_superuser(
        username="product_admin_tea",
        email="product-admin@example.com",
        password="tea-pass-12345",
    )


@pytest.fixture
def editor(django_user_model):
    """Editor = is_staff + member of the `Editor` group (8.2 post_migrate created it;
    group already carries products CRUD + 6 related via EDITOR_CONTENT_MODELS — SM-D8)."""
    from django.contrib.auth.models import Group

    user = django_user_model.objects.create_user(
        username="product_editor_tea",
        email="product-editor@example.com",
        password="tea-pass-12345",
        is_staff=True,
        is_superuser=False,
    )
    user.groups.add(Group.objects.get(name="Editor"))
    return user


@pytest.fixture
def brand():
    from apps.brands.tests.factories import BrandFactory

    return BrandFactory.create(name="John Deere")


# ──────────────────────────────────────────────────────────────────────────────
# Upload fixtures (Pillow + raw bytes — mirror apps/brands/tests/test_brand_crud_admin.py)
# ──────────────────────────────────────────────────────────────────────────────
def _pillow_upload(fmt, content_type, filename):
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (10, 10), color=(34, 64, 47)).save(buf, format=fmt)
    buf.seek(0)
    return SimpleUploadedFile(filename, buf.read(), content_type=content_type)


@pytest.fixture
def valid_jpeg():
    return _pillow_upload("JPEG", "image/jpeg", "main.jpg")


@pytest.fixture
def valid_png():
    return _pillow_upload("PNG", "image/png", "gallery.png")


@pytest.fixture
def fake_image_txt():
    """Plain text renamed .jpg with image/jpeg content-type — MIME signature is text/plain."""
    return SimpleUploadedFile(
        "evil.jpg", b"ovo je samo tekst, nije slika", content_type="image/jpeg"
    )


@pytest.fixture
def corrupt_jpeg():
    """JPEG magic header but garbage body — passes MIME sniff, fails Pillow verify()."""
    return SimpleUploadedFile(
        "corrupt.jpg",
        b"\xff\xd8\xff\xe0nije-validna-slika-vec-djubre",
        content_type="image/jpeg",
    )


@pytest.fixture
def valid_pdf():
    return SimpleUploadedFile(
        "katalog.pdf",
        b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n1 0 obj\n<< >>\nendobj\n",
        content_type="application/pdf",
    )


@pytest.fixture
def fake_pdf_is_image(valid_png):
    """A real PNG renamed .pdf with application/pdf content-type — signature is image/png."""
    valid_png.name = "fake.pdf"
    valid_png.content_type = "application/pdf"
    return valid_png


@pytest.fixture
def oversized_image():
    """Valid small JPEG with forced .size > 5 MB (forces the size-cap branch)."""
    up = _pillow_upload("JPEG", "image/jpeg", "velika.jpg")
    up.size = 6 * 1024 * 1024
    return up


@pytest.fixture
def decompression_bomb_png():
    """8000×8000 (64M px) solid-color PNG — declares pixel dimensions > Image.MAX_IMAGE_PIXELS
    (50M) but is only ~30KB on disk (well under MAX_IMAGE_UPLOAD_SIZE).

    Locks the M2 decompression-bomb guard: the size cap does NOT early-out (small on disk),
    so the bomb MUST be caught by validate_image_mime's DecompressionBombWarning→error
    escalation (NOT a numeric assert on the 50M constant). Mirror
    apps/brands/tests/test_brand_crud_admin.py:decompression_bomb_png."""
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (8000, 8000), color="white").save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return SimpleUploadedFile("bomba.png", buf.read(), content_type="image/png")


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────
def _product_admin():
    from apps.products.models import Product

    return admin.site._registry[Product]


def _inline_for(model_name):
    """Return the ProductAdmin inline class whose .model.__name__ == model_name (or None)."""
    for ic in list(_product_admin().inlines):
        if getattr(getattr(ic, "model", None), "__name__", None) == model_name:
            return ic
    return None


def _make_main_form(data=None, files=None, instance=None):
    """Bind ProductAdminForm (lazy import — collection-safe)."""
    from apps.products.admin import ProductAdminForm

    return ProductAdminForm(data=data or {}, files=files, instance=instance)


def _field_errors_text(form, field):
    return " ".join(str(e) for e in form.errors.get(field, []))


def _scrape_change_form(html):
    """name->value for all input/select/textarea fields in an admin change form.
    Re-submits existing rendered values so the multi-inline + per-locale payload stays valid
    (mirror apps/brands/tests + apps/seo/tests scrapers)."""
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
    for tm in re.finditer(r'<textarea[^>]*name="([^"]+)"[^>]*>(.*?)</textarea>', html, re.S):
        data[tm.group(1)] = tm.group(2)
    return data


def _empty_inline_mgmt(data, prefix, total="0"):
    """Set a Django formset management-form to `total` forms with no rows (helper for POSTs)."""
    data[f"{prefix}-TOTAL_FORMS"] = total
    data[f"{prefix}-INITIAL_FORMS"] = "0"
    data[f"{prefix}-MIN_NUM_FORMS"] = "0"
    data[f"{prefix}-MAX_NUM_FORMS"] = "1000"


# ══════════════════════════════════════════════════════════════════════════════
# AC1 — ProductAdmin is TranslationAdmin + multi-locale + changelist/add/change 200
# ══════════════════════════════════════════════════════════════════════════════
# AC-1: ProductAdmin MUST be a TranslationAdmin subclass (not plain ModelAdmin)
def test_ac1_productadmin_is_translationadmin():
    from modeltranslation.admin import TranslationAdmin

    assert isinstance(_product_admin(), TranslationAdmin), (
        "ProductAdmin MORA biti TranslationAdmin instanca (NE plain ModelAdmin — AC1)."
    )


# AC-1: search_fields MUST use the real column name_sr, not the virtual `name` (G-1)
def test_ac1_search_fields_uses_name_sr_not_virtual_name():
    model_admin = _product_admin()
    assert tuple(model_admin.search_fields) == ("name_sr",), (
        "search_fields MORA biti ('name_sr',) — realna DB kolona, NE virtuelni `name` "
        f"(baca FieldError na changelist search — G-1); dobio {model_admin.search_fields!r}."
    )


# AC-1: changelist search by name_sr does NOT raise FieldError (real column — G-1)
def test_ac1_changelist_search_no_field_error(client, superuser, brand):
    from apps.products.tests.factories import ProductFactory

    ProductFactory.create(brand=brand, name="Tražni Traktor")
    client.force_login(superuser)
    resp = client.get(reverse("admin:products_product_changelist"), {"q": "Tražni"})
    assert resp.status_code == 200, (
        f"Changelist search (q=) MORA biti 200 — search_fields=('name_sr',) NE sme baciti "
        f"FieldError (G-1/AC1); dobio {resp.status_code}."
    )


# AC-1: superuser add-view 200 (7-inline + per-locale + GFK render-smoke — G-9)
def test_ac1_add_view_200_superuser(client, superuser):
    client.force_login(superuser)
    resp = client.get(reverse("admin:products_product_add"))
    assert resp.status_code == 200, (
        f"Superuser Product add-view MORA biti 200 (7 inline-ova + per-locale + GFK "
        f"render-tačka loma — AC1/G-9); dobio {resp.status_code}."
    )


# AC-1: change-view renders per-locale fields for name/description/key_features (render-smoke)
def test_ac1_change_view_renders_per_locale_fields(client, superuser, brand):
    from apps.products.tests.factories import ProductFactory

    product = ProductFactory.create(brand=brand, name="Đuro Traktor")
    client.force_login(superuser)
    html = client.get(
        reverse("admin:products_product_change", args=[product.pk])
    ).content.decode()
    for fld in ("name_sr", "name_hu", "name_en", "description_sr"):
        assert f'name="{fld}"' in html, (
            f"Change-view MORA renderovati per-locale polje '{fld}' (render-smoke — AC1)."
        )


# AC-1: admin system checks clean (TranslationAdmin + 7 inlines + prepopulated → 0 admin.E*)
def test_ac1_admin_system_checks_clean():
    from django.core.checks import run_checks

    errors = [e for e in run_checks() if e.is_serious()]
    assert errors == [], (
        f"manage.py check MORA biti čist — TranslationAdmin + 7 inline-ova + fk_name "
        f"ProductSimilar + GFK SeoMetaInline ne smeju baciti admin.E* (AC1/G-9/G-11). "
        f"Greške: {errors}."
    )


# ══════════════════════════════════════════════════════════════════════════════
# AC2 — 6 domain inlines + SeoMetaInline kept; translatable vs plain types
# ══════════════════════════════════════════════════════════════════════════════
# AC-2: all 6 domain inlines + SeoMetaInline present (7 total)
def test_ac2_all_six_domain_inlines_present():
    inline_models = {
        getattr(getattr(ic, "model", None), "__name__", None)
        for ic in list(_product_admin().inlines)
    }
    for required in (
        "ProductImage",
        "ProductVariant",
        "ProductSpecification",
        "ProductBrochure",
        "ProductTestimonial",
        "ProductSimilar",
    ):
        assert required in inline_models, (
            f"ProductAdmin.inlines MORA sadržati inline za {required} (AC2); "
            f"prisutni: {inline_models}."
        )


# AC-2: the 5 translatable inlines are Translation*Inline (per-locale render)
def test_ac2_translatable_inlines_are_translation_inlines():
    from modeltranslation.admin import (
        TranslationStackedInline,
        TranslationTabularInline,
    )

    for model_name in (
        "ProductImage",
        "ProductVariant",
        "ProductSpecification",
        "ProductBrochure",
        "ProductTestimonial",
    ):
        ic = _inline_for(model_name)
        assert ic is not None, f"Inline za {model_name} MORA postojati (AC2)."
        assert issubclass(ic, (TranslationTabularInline, TranslationStackedInline)), (
            f"{model_name}Inline MORA biti Translation*Inline (per-locale polja — AC1/AC2); "
            f"dobio MRO {ic.__mro__}."
        )


# AC-2 (G-12): ProductSimilarInline is a PLAIN TabularInline (NOT translatable)
def test_ac2_productsimilar_inline_is_plain_tabular():
    from modeltranslation.admin import (
        TranslationStackedInline,
        TranslationTabularInline,
    )

    ic = _inline_for("ProductSimilar")
    assert ic is not None, "ProductSimilarInline MORA postojati (AC2)."
    assert issubclass(ic, admin.TabularInline), (
        "ProductSimilarInline MORA biti plain admin.TabularInline (AC2/G-12)."
    )
    assert not issubclass(ic, (TranslationTabularInline, TranslationStackedInline)), (
        "ProductSimilarInline NE SME biti Translation*Inline — ProductSimilar nije "
        "registrovan u translation.py (G-12)."
    )


# AC-2 (G-11): ProductSimilarInline MUST declare fk_name="product" (two FKs → admin.E202)
def test_ac2_productsimilar_inline_has_fk_name_product():
    ic = _inline_for("ProductSimilar")
    assert ic is not None, "ProductSimilarInline MORA postojati (AC2)."
    assert getattr(ic, "fk_name", None) == "product", (
        "ProductSimilarInline MORA imati fk_name='product' (DVA FK ka Product → "
        f"admin.E202 bez ovoga — G-11); dobio {getattr(ic, 'fk_name', None)!r}."
    )


# AC-2: extra = 0 on every domain inline (no spurious required empty rows)
def test_ac2_domain_inlines_extra_zero():
    for model_name in (
        "ProductImage",
        "ProductVariant",
        "ProductSpecification",
        "ProductBrochure",
        "ProductTestimonial",
        "ProductSimilar",
    ):
        ic = _inline_for(model_name)
        assert ic is not None, f"Inline za {model_name} MORA postojati (AC2)."
        assert ic.extra == 0, (
            f"{model_name}Inline.extra MORA biti 0 (bez praznih obaveznih redova — AC2); "
            f"dobio {ic.extra}."
        )


# AC-2 (INVARIANT-LOCK — MAY PASS today: 6.1 already has SeoMetaInline on ProductAdmin)
def test_ac2_seometa_inline_still_on_productadmin():
    from apps.seo.admin import SeoMetaInline

    inlines = list(_product_admin().inlines)
    assert any(ic is SeoMetaInline or issubclass(ic, SeoMetaInline) for ic in inlines), (
        "SeoMetaInline MORA OSTATI na ProductAdmin posle konverzije (6.1 regression — "
        "G-8/AC2/AC12)."
    )


# ══════════════════════════════════════════════════════════════════════════════
# AC3 (SECURITY) — upload MIME/signature double-check (needs Docker/libmagic)
# ══════════════════════════════════════════════════════════════════════════════
# AC-3: upload size constants defined (mirror 8.4 — local, not media_pipeline module default)
def test_ac3_upload_size_constants_defined():
    from apps.products import admin as products_admin

    assert products_admin.MAX_IMAGE_UPLOAD_SIZE == 5 * 1024 * 1024, (
        "MAX_IMAGE_UPLOAD_SIZE MORA biti 5 MB (UPPER_SNAKE_CASE — AC3/OQ-4)."
    )
    assert products_admin.MAX_PDF_UPLOAD_SIZE == 20 * 1024 * 1024, (
        "MAX_PDF_UPLOAD_SIZE MORA biti 20 MB (UPPER_SNAKE_CASE — AC3/OQ-4)."
    )


# AC-3: ProductAdminForm.clean_main_image exists (upload double-check entrypoint)
def test_ac3_main_form_has_clean_main_image():
    from apps.products.admin import ProductAdminForm

    assert hasattr(ProductAdminForm, "clean_main_image"), (
        "ProductAdminForm MORA imati clean_main_image (upload double-check — AC3/G-13)."
    )


# AC-3 (security): fake-extension image rejected with canonical media_pipeline message
def test_ac3_clean_main_image_rejects_fake_image(fake_image_txt):
    form = _make_main_form(
        data={"name_sr": "X", "key_features_sr": "[]"},
        files={"main_image": fake_image_txt},
    )
    assert not form.is_valid(), (
        "Lažna slika (.jpg ali tekst) MORA biti odbijena (MIME — AC3)."
    )
    assert "Nedozvoljen tip slike" in _field_errors_text(form, "main_image"), (
        f"Greška MORA sadržati 'Nedozvoljen tip slike' na `main_image` (validate_image_mime "
        f"kanonska poruka); dobio {form.errors!r}."
    )


# AC-3 (security): corrupt image (valid magic header, fails Pillow verify) rejected
def test_ac3_clean_main_image_rejects_corrupt_image(corrupt_jpeg):
    form = _make_main_form(
        data={"name_sr": "X", "key_features_sr": "[]"},
        files={"main_image": corrupt_jpeg},
    )
    assert not form.is_valid(), (
        "Korumpiran JPEG (magic header OK, Pillow verify pada) MORA biti odbijen (AC3)."
    )
    assert "Slika je oštećena ili nije validan format" in _field_errors_text(
        form, "main_image"
    ), (
        f"Korumpiran JPEG MORA pasti na Pillow verify() sa kanonskom porukom "
        f"'Slika je oštećena ili nije validan format.' na `main_image` (NE goli OSError/500 "
        f"i NE Django default engleska poruka — G-14); dobio {form.errors!r}."
    )


# AC-3 (security): decompression-bomb rejected (64M px, small on disk → bomb guard, M2)
def test_ac3_clean_main_image_rejects_decompression_bomb(decompression_bomb_png):
    """M2 lock — 64M-px PNG (~30KB on disk) MUST be rejected by the blessed
    validate_image_mime decompression-bomb guard (Image.MAX_IMAGE_PIXELS=50M +
    DecompressionBombWarning→error). Reusing the canonical helper restores the guard the
    8.4 inline duplicate lacked. The fixture is a REAL oversized-pixel Pillow image (NOT an
    assert on the 50M constant) so the guard is exercised end-to-end."""
    form = _make_main_form(
        data={"name_sr": "X", "key_features_sr": "[]"},
        files={"main_image": decompression_bomb_png},
    )
    assert not form.is_valid(), (
        "Decompression-bomb slika (64M px, mala na disku) MORA biti odbijena "
        "(validate_image_mime MAX_IMAGE_PIXELS=50M guard — M2)."
    )
    assert "Slika je oštećena ili nije validan format" in _field_errors_text(
        form, "main_image"
    ), (
        f"Bomba MORA dati kanonsku validate_image_mime poruku na `main_image`; "
        f"dobio {form.errors!r}."
    )


# AC-3 (edge): oversized image rejected (> MAX_IMAGE_UPLOAD_SIZE)
def test_ac3_clean_main_image_rejects_oversized(oversized_image):
    form = _make_main_form(
        data={"name_sr": "X", "key_features_sr": "[]"},
        files={"main_image": oversized_image},
    )
    assert not form.is_valid(), (
        "main_image > MAX_IMAGE_UPLOAD_SIZE MORA biti odbijen (AC3)."
    )
    assert "main_image" in form.errors


# AC-3: valid JPEG accepted on main_image (positive path)
def test_ac3_clean_main_image_accepts_valid_image(valid_jpeg, brand):
    # `brand` je OBAVEZAN FK na Product (PROTECT, no null/blank) → mora biti u data-i
    # da raw ProductAdminForm.is_valid() prođe; upload-path je fokus asercije.
    form = _make_main_form(
        data={
            "name": "Validan",
            "slug": "validan",
            "name_sr": "Validan",
            "brand": str(brand.pk),
            "key_features_sr": "[]",
        },
        files={"main_image": valid_jpeg},
    )
    assert form.is_valid(), (
        f"Validan JPEG main_image MORA proći upload double-check (AC3); errors={form.errors!r}."
    )


# AC-3: ProductBrochure inline form rejects non-PDF (validate_pdf_mime canonical message)
def test_ac3_brochure_inline_form_rejects_non_pdf(fake_pdf_is_image):
    from apps.products.admin import ProductBrochureInlineForm

    form = ProductBrochureInlineForm(
        data={"title_sr": "Brošura"},
        files={"pdf_file": fake_pdf_is_image},
    )
    assert not form.is_valid(), (
        "Ne-PDF (slika preimenovana u .pdf) MORA biti odbijen u brošura inline formi (AC3)."
    )
    assert "Nedozvoljen tip fajla" in _field_errors_text(form, "pdf_file"), (
        f"Greška MORA sadržati 'Nedozvoljen tip fajla' na `pdf_file` (validate_pdf_mime "
        f"kanonska poruka); dobio {form.errors!r}."
    )


# AC-3: ProductBrochure inline form accepts valid PDF (positive path)
def test_ac3_brochure_inline_form_accepts_valid_pdf(valid_pdf, brand):
    from apps.products.admin import ProductBrochureInlineForm
    from apps.products.tests.factories import ProductFactory

    # `product` je OBAVEZAN FK na ProductBrochure → kad se inline ModelForm bind-uje
    # DIREKTNO (van inline formset-a) `product` polje je prisutno i required; mora u data-i.
    product = ProductFactory.create(brand=brand)
    form = ProductBrochureInlineForm(
        data={"title_sr": "Brošura", "product": str(product.pk)},
        files={"pdf_file": valid_pdf},
    )
    assert form.is_valid(), (
        f"Validan PDF MORA proći brošura inline upload check (AC3); errors={form.errors!r}."
    )


# AC-3: ProductImage inline form rejects fake image (required field, always validated)
def test_ac3_image_inline_form_rejects_fake_image(fake_image_txt):
    from apps.products.admin import ProductImageInlineForm

    form = ProductImageInlineForm(
        data={"order": "0", "alt_text_sr": ""},
        files={"image": fake_image_txt},
    )
    assert not form.is_valid(), (
        "Lažna slika u obaveznom ProductImage.image polju MORA biti odbijena (MIME — AC3)."
    )
    assert "Nedozvoljen tip slike" in _field_errors_text(form, "image"), (
        f"Greška MORA sadržati 'Nedozvoljen tip slike' na `image` (validate_image_mime); "
        f"dobio {form.errors!r}."
    )


# ══════════════════════════════════════════════════════════════════════════════
# AC3 HARD RULE / BLANK-SKIP — blank-able image fields MUST skip validate_image_mime
# (residual 8.4 M2 gap: unconditional helper RAISES on empty upload → draft-save breaks)
# ══════════════════════════════════════════════════════════════════════════════
# AC-3: main_image blank → main form valid (graceful skip, NOT "Slika je prazna…")
def test_ac3_blank_main_image_skips_gracefully(brand):
    # `brand` je OBAVEZAN FK na Product → mora biti u data-i; fokus je da prazan
    # main_image (blank=True) NE obori formu (graceful skip, NE bezuslovni helper poziv).
    form = _make_main_form(
        data={
            "name": "Bez Slike",
            "slug": "bez-slike",
            "name_sr": "Bez Slike",
            "brand": str(brand.pk),
            "key_features_sr": "[]",
        },
        files={},
    )
    assert form.is_valid(), (
        f"Prazan main_image (blank=True) MORA proći bez greške (graceful skip — AC3 HARD "
        f"RULE; NE bezuslovni validate_image_mime koji RAISE-uje na praznom); "
        f"errors={form.errors!r}."
    )


# AC-3: variant inline form with blank image → valid (graceful skip)
def test_ac3_blank_variant_image_skips_gracefully(brand):
    from apps.products.admin import ProductVariantInlineForm
    from apps.products.tests.factories import ProductFactory

    # `product` je OBAVEZAN FK na ProductVariant → mora u data-i kad se inline form
    # bind-uje direktno; fokus je da prazan image (blank=True) NE obori formu.
    product = ProductFactory.create(brand=brand)
    form = ProductVariantInlineForm(
        data={
            "name_sr": "Sa kabinom",
            "code": "",
            "order": "0",
            "product": str(product.pk),
        },
        files={},
    )
    assert form.is_valid(), (
        f"ProductVariant red sa praznim image (blank=True) MORA proći (graceful skip — AC3 "
        f"HARD RULE); errors={form.errors!r}."
    )


# AC-3 (BLANK-SKIP through the real admin — locks the 8.4 M2 residual gap end-to-end):
# draft product with empty main_image AND a variant row with empty image saves (HTTP 302/200,
# NO "Slika je prazna ili nije priložena." ValidationError).
def test_ac3_draft_product_no_images_saves_through_admin(client, superuser, brand):
    from apps.products.models import Product

    client.force_login(superuser)
    url = reverse("admin:products_product_add")
    data = _scrape_change_form(client.get(url).content.decode())
    data["brand"] = str(brand.pk)
    data["name_sr"] = "Nacrt Bez Slike"
    data["slug"] = "nacrt-bez-slike"
    data["condition"] = "new"
    data["status"] = "draft"
    data["is_published"] = ""  # unchecked → draft (gate not triggered)
    data.setdefault("key_features_sr", "[]")
    resp = client.post(url, data, follow=True)
    assert resp.status_code == 200, (
        f"Draft Product bez slike MORA se sačuvati (graceful blank-skip — AC3 HARD RULE); "
        f"dobio {resp.status_code}."
    )
    saved = Product.objects.filter(name_sr="Nacrt Bez Slike").first()
    assert saved is not None, (
        "Draft Product sa praznim main_image MORA biti kreiran — blank-able slikovna polja "
        "imaju skip i NE pozivaju validate_image_mime bezuslovno (8.4 M2 rezidualni jaz)."
    )


# ══════════════════════════════════════════════════════════════════════════════
# AC6 — Publish-gate (galerija + spec na publish; graceful messages.error + revert)
# ══════════════════════════════════════════════════════════════════════════════
def _draft_product(brand):
    from apps.products.tests.factories import ProductFactory

    return ProductFactory.create(brand=brand, name="Gate Proizvod", is_published=False,
                                 status="draft")


def _post_publish(client, product):
    """Scrape change form, flip to published, return (url, data) for the POST."""
    url = reverse("admin:products_product_change", args=[product.pk])
    data = _scrape_change_form(client.get(url).content.decode())
    data["brand"] = str(product.brand_id)
    data["name_sr"] = product.name_sr or "Gate Proizvod"
    data["is_published"] = "on"
    data["status"] = "published"
    data.setdefault("key_features_sr", "[]")
    return url, data


# AC-6: ProductAdmin overrides save_related (gate lives there, not in form clean — G-5)
def test_ac6_productadmin_overrides_save_related():
    from modeltranslation.admin import TranslationAdmin

    model_admin = _product_admin()
    assert type(model_admin).save_related is not TranslationAdmin.save_related, (
        "ProductAdmin MORA override-ovati save_related (publish-gate čita inline count POSLE "
        "super().save_related — SM-D5/G-5; NE u ProductForm.clean())."
    )


# AC-6 (a): publish with name_sr but NO gallery image → graceful 200, stays draft, error msg
def test_ac6_publish_without_image_reverts_to_draft(client, superuser, brand):
    from apps.products.models import Product
    from apps.products.tests.factories import ProductSpecificationFactory

    client.force_login(superuser)
    product = _draft_product(brand)
    # has a spec but NO image → image is the missing requirement
    ProductSpecificationFactory.create(product=product, section="motor")
    url, data = _post_publish(client, product)
    resp = client.post(url, data, follow=True)
    assert resp.status_code == 200, (
        f"Publish bez slike MORA biti graceful 200 (NE 500 iz save_related raise — G-6); "
        f"dobio {resp.status_code}."
    )
    product.refresh_from_db()
    assert product.is_published is False and product.status == "draft", (
        "Proizvod MORA OSTATI draft/neobjavljen kad fali slika galerije (revert — AC6/G-6); "
        f"is_published={product.is_published}, status={product.status!r}."
    )
    msgs = " ".join(str(m) for m in resp.context["messages"])
    assert "slika galerije" in msgs, (
        f"messages.error MORA navesti da fali 'slika galerije' (konkretan spisak — AC6); "
        f"poruke: {msgs!r}."
    )
    assert Product.objects.get(pk=product.pk).is_published is False


# AC-6 (b): publish with image but NO specification → graceful 200, stays draft, error msg
def test_ac6_publish_without_specification_reverts_to_draft(client, superuser, brand):
    from apps.products.tests.factories import ProductImageFactory

    client.force_login(superuser)
    product = _draft_product(brand)
    ProductImageFactory.create(product=product, order=0)  # has image, NO spec
    url, data = _post_publish(client, product)
    resp = client.post(url, data, follow=True)
    assert resp.status_code == 200, (
        f"Publish bez specifikacije MORA biti graceful 200 (G-6); dobio {resp.status_code}."
    )
    product.refresh_from_db()
    assert product.is_published is False and product.status == "draft", (
        "Proizvod MORA OSTATI draft kad fali specifikacija (revert — AC6/G-6)."
    )
    msgs = " ".join(str(m) for m in resp.context["messages"])
    assert "specifikacija" in msgs, (
        f"messages.error MORA navesti da fali 'specifikacija' (AC6); poruke: {msgs!r}."
    )


# AC-6 (c): publish with ≥1 valid image + ≥1 spec → PASSES, product published
# FIXTURE-PRECISION: the image is created with a valid PNG upload (passes AC3 MIME guard).
def test_ac6_publish_with_image_and_spec_succeeds(client, superuser, brand):
    from apps.products.tests.factories import (
        ProductImageFactory,
        ProductSpecificationFactory,
    )

    client.force_login(superuser)
    product = _draft_product(brand)
    ProductImageFactory.create(product=product, order=0)  # valid PNG upload
    ProductSpecificationFactory.create(product=product, section="motor")
    url, data = _post_publish(client, product)
    resp = client.post(url, data, follow=True)
    assert resp.status_code == 200, (
        f"Kompletan publish MORA biti 200; dobio {resp.status_code}."
    )
    product.refresh_from_db()
    assert product.is_published is True and product.status == "published", (
        "Proizvod sa name_sr + ≥1 slika + ≥1 spec MORA biti objavljen (gate prolazi — AC6); "
        f"is_published={product.is_published}, status={product.status!r}."
    )


# AC-6 (d): DRAFT save with 0 images/specs → PASSES (gate fires ONLY on publish)
def test_ac6_draft_save_with_no_content_passes(client, superuser, brand):
    client.force_login(superuser)
    product = _draft_product(brand)
    url = reverse("admin:products_product_change", args=[product.pk])
    data = _scrape_change_form(client.get(url).content.decode())
    data["brand"] = str(product.brand_id)
    data["name_sr"] = "Gate Proizvod"
    data["is_published"] = ""  # stays draft
    data["status"] = "draft"
    data.setdefault("key_features_sr", "[]")
    resp = client.post(url, data, follow=True)
    assert resp.status_code == 200, (
        f"Draft save bez slika/spec MORA biti 200 (gate se NE okida na draft — AC6); "
        f"dobio {resp.status_code}."
    )
    product.refresh_from_db()
    assert product.is_published is False and product.status == "draft", (
        "Draft proizvod sa 0 slika/spec MORA ostati sačuvan kao draft (gate ne blokira "
        "draft — AC6)."
    )


# ══════════════════════════════════════════════════════════════════════════════
# AC7 — main_image preview (format_html, escaped, truthy-guard)
# ══════════════════════════════════════════════════════════════════════════════
# AC-7: main_image_preview method exists
def test_ac7_main_image_preview_method_exists():
    assert hasattr(_product_admin(), "main_image_preview"), (
        "ProductAdmin MORA imati main_image_preview readonly metodu (AC7)."
    )


# AC-7: preview empty (—, no broken <img>) when main_image absent
def test_ac7_preview_empty_when_no_image(brand):
    from apps.products.tests.factories import ProductFactory

    model_admin = _product_admin()
    product = ProductFactory.create(brand=brand, name="Bez Glavne Slike")
    out = str(model_admin.main_image_preview(product))
    assert "<img" not in out, (
        f"main_image_preview MORA biti prazno (npr. '—') kad slika ne postoji — BEZ "
        f"slomljenog <img> (AC7); dobio {out!r}."
    )


# AC-7: preview renders escaped <img> when main_image set (format_html — G-15)
def test_ac7_preview_renders_img_when_image_set(brand, valid_jpeg):
    from apps.products.tests.factories import ProductFactory

    model_admin = _product_admin()
    product = ProductFactory.create(brand=brand, name="Sa Glavnom Slikom")
    product.main_image.save("main.jpg", valid_jpeg, save=True)
    out = str(model_admin.main_image_preview(product))
    assert "<img" in out and product.main_image.url in out, (
        f"main_image_preview MORA renderovati <img src=...> kad slika postoji (format_html — "
        f"AC7/G-15); dobio {out!r}."
    )


# ══════════════════════════════════════════════════════════════════════════════
# AC8 — listing: list_display / list_filter / list_select_related (N+1) / view_on_site
# ══════════════════════════════════════════════════════════════════════════════
# AC-8: list_display has status indicators + brand
def test_ac8_list_display_has_status_and_brand():
    ld = tuple(_product_admin().list_display)
    for col in ("name", "brand", "is_published", "status"):
        assert col in ld, f"list_display MORA sadržati '{col}' (AC8); dobio {ld}."


# AC-8: list_filter includes is_published/status/brand/condition
def test_ac8_list_filter_columns():
    lf = tuple(_product_admin().list_filter)
    for col in ("is_published", "status", "brand", "condition"):
        assert col in lf, f"list_filter MORA sadržati '{col}' (AC8); dobio {lf}."


# AC-8 (G-10): list_select_related=("brand",) is MANDATORY (Product.__str__ reads brand.name)
def test_ac8_list_select_related_brand():
    lsr = tuple(_product_admin().list_select_related)
    assert "brand" in lsr, (
        "list_select_related MORA uključiti 'brand' (Product.__str__ čita self.brand.name → "
        f"N+1 bez ovoga; models.py:202-206 NOTE traži za 8.6 — AC8/G-10); dobio {lsr}."
    )


# AC-8 (G-10): changelist query count does NOT scale with row count (no N+1 from brand.name)
def test_ac8_changelist_no_n_plus_one(client, superuser, brand):
    """Each changelist row renders Product.__str__ → reads self.brand.name. WITHOUT
    list_select_related=("brand",) every row issues an extra SELECT on brands_brand (N+1).
    This test compares the query count for a small vs a larger row-set: with select_related
    the delta is ~0; under the 6.1 stub (no list_select_related) the delta scales with rows,
    so the assertion fails (true RED). Mirror G-10."""
    from django.test.utils import CaptureQueriesContext
    from django.db import connection

    from apps.products.tests.factories import ProductFactory

    client.force_login(superuser)
    url = reverse("admin:products_product_changelist")

    ProductFactory.create(brand=brand, name="N1 Baseline")
    with CaptureQueriesContext(connection) as small:
        assert client.get(url).status_code == 200
    small_count = len(small)

    for i in range(10):
        ProductFactory.create(brand=brand, name=f"N1 Proizvod {i}")
    with CaptureQueriesContext(connection) as big:
        assert client.get(url).status_code == 200
    big_count = len(big)

    assert big_count - small_count <= 2, (
        f"Changelist query count NE SME da raste sa brojem redova — list_select_related="
        f"('brand',) mora JOIN-ovati brand (G-10/AC8). Delta za +10 redova = "
        f"{big_count - small_count} (baseline={small_count}, big={big_count}); bez "
        f"select_related svaki red izdaje extra SELECT na brands_brand (N+1)."
    )


# AC-8 / SM-D9: ProductAdmin.view_on_site is NOT False (products:detail registered)
def test_ac8_view_on_site_not_disabled():
    assert _product_admin().view_on_site is not False, (
        "ProductAdmin.view_on_site NE SME biti False — products:detail JE registrovan "
        "(urls.py:10) → View on site radi (mirror 8.4 Brand — SM-D9/AC8)."
    )


# AC-8: change-view 200 (does NOT 500 on the View-on-site affordance)
def test_ac8_change_view_200_does_not_break_on_view_on_site(client, superuser, brand):
    from apps.products.tests.factories import ProductFactory

    product = ProductFactory.create(brand=brand, name="View On Site Test")
    client.force_login(superuser)
    resp = client.get(reverse("admin:products_product_change", args=[product.pk]))
    assert resp.status_code == 200, (
        f"Change-view MORA biti 200 (View on site sa registrovanim products:detail ne puca "
        f"— SM-D9); dobio {resp.status_code}."
    )


# ══════════════════════════════════════════════════════════════════════════════
# AC9 — name_sr je BEZUSLOVNO obavezan (model name blank=False; NE relaksirati — M1)
# ══════════════════════════════════════════════════════════════════════════════
def _admin_form_field_required(name):
    from django.contrib.auth.models import AnonymousUser
    from django.test import RequestFactory

    model_admin = _product_admin()
    req = RequestFactory().get("/")
    # ProductAdmin ima FK polja (brand/series/subcategory) → modeltranslation
    # formfield_for_dbfield gradi related-widget koji čita request.user
    # (has_add_permission). Bare RequestFactory request nema .user → moramo ga
    # priložiti (AnonymousUser je dovoljan: has_perm bezbedno vraća False, bez DB).
    req.user = AnonymousUser()
    form_cls = model_admin.get_form(req)
    return form_cls.base_fields[name].required


# AC-9: name_sr is required on the admin-built form (required-promotion NOT relaxed)
def test_ac9_name_sr_required_on_admin_form():
    assert _admin_form_field_required("name_sr") is True, (
        "name_sr MORA biti obavezno na admin ProductForm-u (model `name` blank=False + sr "
        "default lang → TranslationAdmin required-promotion); promotion se NE relaksira (M1)."
    )


# AC-9 (graceful): empty name_sr on add → 200 form-error on name_sr, NO new Product
def test_ac9_empty_name_sr_graceful_form_error(client, superuser, brand):
    from apps.products.models import Product

    before = Product.objects.count()
    client.force_login(superuser)
    url = reverse("admin:products_product_add")
    data = _scrape_change_form(client.get(url).content.decode())
    data["brand"] = str(brand.pk)
    data["name_sr"] = ""
    data["slug"] = ""
    data["condition"] = "new"
    data["status"] = "draft"
    data["is_published"] = ""
    data.setdefault("key_features_sr", "[]")
    resp = client.post(url, data)
    assert resp.status_code == 200, (
        f"Prazan name_sr MORA dati graceful 200 form-error (NIKAD 400/500 iz model full_clean "
        f"escape — AC9/M1); dobio {resp.status_code}."
    )
    form = resp.context["adminform"].form
    assert "name_sr" in form.errors, (
        f"Prazan name_sr MORA dati field grešku na `name_sr` (required); dobio {form.errors!r}."
    )
    assert Product.objects.count() == before, (
        "Nijedan NOV Product NE SME biti kreiran kad je name_sr prazan (AC9/M1)."
    )


# AC-9 (positive): valid name_sr (+brand+slug) → 302 redirect, Product created
def test_ac9_valid_name_sr_creates_product(client, superuser, brand):
    from apps.products.models import Product

    client.force_login(superuser)
    url = reverse("admin:products_product_add")
    data = _scrape_change_form(client.get(url).content.decode())
    data["brand"] = str(brand.pk)
    data["name_sr"] = "Objavljen Proizvod"
    data["slug"] = "objavljen-proizvod"
    data["condition"] = "new"
    data["status"] = "draft"
    data["is_published"] = ""
    data.setdefault("key_features_sr", "[]")
    resp = client.post(url, data)
    assert resp.status_code == 302, (
        f"Validan name_sr (+brand+slug) MORA sačuvati Product i dati 302 (AC9); "
        f"dobio {resp.status_code}."
    )
    assert Product.objects.filter(name_sr="Objavljen Proizvod").exists(), (
        "Validan Product sa name_sr MORA biti kreiran (AC9)."
    )


# ══════════════════════════════════════════════════════════════════════════════
# AC10 — key_features multi-locale validation delegated to Product.clean() (max 3, G-7)
# ══════════════════════════════════════════════════════════════════════════════
# AC-10: > 3 key_features blocked by model clean() (admin does NOT duplicate — G-7)
def test_ac10_four_key_features_blocked_by_model(brand):
    four = '["a", "b", "c", "d"]'
    form = _make_main_form(
        data={
            "name": "KF",
            "slug": "kf",
            "name_sr": "KF",
            "brand": str(brand.pk),
            "key_features_sr": four,
        },
    )
    assert not form.is_valid(), (
        "4 key_features stavke MORA blokirati save (Product.clean() max 3 — AC10/G-7)."
    )
    assert "key_features_sr" in form.errors, (
        f"Greška MORA biti na `key_features_sr` (model clean, NE re-implementacija u adminu — "
        f"G-7); dobio {form.errors!r}."
    )


# AC-10 (error-path): syntactically broken JSON → field-level error, NO 500
def test_ac10_invalid_json_field_error_no_500(brand):
    form = _make_main_form(
        data={
            "name": "KF",
            "slug": "kf",
            "name_sr": "KF",
            "brand": str(brand.pk),
            "key_features_sr": "{ne-zatvoren",
        },
    )
    assert not form.is_valid(), "Sintaksno polomljen JSON MORA biti odbijen (AC10)."
    assert "key_features_sr" in form.errors, (
        f"Nevalidan JSON MORA dati field-level grešku na `key_features_sr` (NE 500 — AC10); "
        f"dobio {form.errors!r}."
    )


# ══════════════════════════════════════════════════════════════════════════════
# AC11 — RBAC: Editor + Superadmin CRUD; anon → 302 (verify, not re-grant — SM-D8)
# ══════════════════════════════════════════════════════════════════════════════
# AC-11 (negative): anonymous → 302 admin login
def test_ac11_anonymous_redirected_to_login(client):
    resp = client.get(reverse("admin:products_product_changelist"))
    assert resp.status_code == 302, (
        f"Anoniman na Product changelist MORA biti 302 (admin login redirect — AC11); "
        f"dobio {resp.status_code}."
    )
    assert reverse("admin:login") in resp["Location"], (
        f"302 MORA voditi na admin:login (NE hardkodovan put — admin na bare /admin-coric/ "
        f"iz 8.1); Location={resp['Location']!r}."
    )


# AC-11: Editor changelist + add-view 200
def test_ac11_editor_changelist_and_add_200(client, editor):
    client.force_login(editor)
    cl = client.get(reverse("admin:products_product_changelist"))
    assert cl.status_code == 200, (
        f"Editor Product changelist MORA biti 200 (8.2 grant netaknut — AC11/SM-D8); "
        f"dobio {cl.status_code}."
    )
    add = client.get(reverse("admin:products_product_add"))
    assert add.status_code == 200, (
        f"Editor Product add-view MORA biti 200 (forma + 7 inline-ova bez admin.E* — AC11); "
        f"dobio {add.status_code}."
    )


# AC-11: Editor can POST-save a valid Product through add-view
def test_ac11_editor_can_add_product(client, editor, brand):
    from apps.products.models import Product

    client.force_login(editor)
    url = reverse("admin:products_product_add")
    data = _scrape_change_form(client.get(url).content.decode())
    data["brand"] = str(brand.pk)
    data["name_sr"] = "Editorov Proizvod"
    data["slug"] = "editorov-proizvod"
    data["condition"] = "new"
    data["status"] = "draft"
    data["is_published"] = ""
    data.setdefault("key_features_sr", "[]")
    resp = client.post(url, data, follow=True)
    assert resp.status_code == 200, f"Editor add POST MORA biti 200; dobio {resp.status_code}."
    assert Product.objects.filter(name_sr="Editorov Proizvod").exists(), (
        "Editor MORA moći da sačuva validan Product kroz admin (AC11)."
    )


# AC-11 (INVARIANT-LOCK — MAY PASS today: 8.2 already granted change_product to Editor)
def test_ac11_editor_has_change_perm_on_product(editor):
    assert editor.has_perm("products.change_product"), (
        "Editor MORA imati products.change_product (8.2 grant — verify, NE re-grant; SM-D8)."
    )
    for related in (
        "productimage",
        "productvariant",
        "productspecification",
        "productbrochure",
        "producttestimonial",
        "productsimilar",
    ):
        assert editor.has_perm(f"products.change_{related}"), (
            f"Editor MORA imati products.change_{related} (8.2 grant — SM-D8)."
        )


# AC-11 (INVARIANT-LOCK — MAY PASS today: 6.1 already subclasses SeoWarningAdminMixin)
def test_ac11_seowarning_mixin_in_mro():
    from apps.seo.admin import SeoWarningAdminMixin

    assert isinstance(_product_admin(), SeoWarningAdminMixin), (
        "ProductAdmin MORA zadržati SeoWarningAdminMixin u MRO (mixin PRVI — G-2/AC11)."
    )


# ══════════════════════════════════════════════════════════════════════════════
# AC12 — no migrations, no regression
# ══════════════════════════════════════════════════════════════════════════════
# AC-12 (INVARIANT-LOCK — MAY PASS today: admin-only story, 0 schema by design)
def test_ac12_no_pending_migration_for_products():
    from django.apps import apps as django_apps
    from django.db.migrations.autodetector import MigrationAutodetector
    from django.db.migrations.loader import MigrationLoader
    from django.db.migrations.state import ProjectState

    loader = MigrationLoader(None, ignore_no_migrations=True)
    autodetector = MigrationAutodetector(
        loader.project_state(),
        ProjectState.from_apps(django_apps),
    )
    changes = autodetector.changes(graph=loader.graph)
    assert "products" not in changes, (
        f"apps.products NE SME imati pending schema migraciju (8.6 je admin-only — AC12); "
        f"autodetector predlaže: {changes.get('products')}."
    )


# AC-12 (regression): superuser changelist 200 (6.1 SeoMeta lock parity)
def test_ac12_changelist_200_superuser(client, superuser, brand):
    from apps.products.tests.factories import ProductFactory

    ProductFactory.create(brand=brand, name="Regresija Proizvod")
    client.force_login(superuser)
    resp = client.get(reverse("admin:products_product_changelist"))
    assert resp.status_code == 200, (
        f"Product changelist MORA ostati 200 posle konverzije (6.1 regression — AC12); "
        f"dobio {resp.status_code}."
    )


# AC-12 (regression): 8.4/8.5 brands admins untouched (SM-D1) — still TranslationAdmin + SeoMetaInline
def test_ac12_brands_admins_untouched():
    from modeltranslation.admin import TranslationAdmin

    from apps.brands.models import Brand, Category, Subcategory
    from apps.seo.admin import SeoMetaInline

    for model in (Brand, Category, Subcategory):
        model_admin = admin.site._registry[model]
        assert isinstance(model_admin, TranslationAdmin), (
            f"{model.__name__}Admin MORA ostati TranslationAdmin (8.4/8.5 netaknut — SM-D1/AC12)."
        )
        inlines = list(model_admin.inlines)
        assert any(ic is SeoMetaInline or issubclass(ic, SeoMetaInline) for ic in inlines), (
            f"{model.__name__}Admin MORA zadržati SeoMetaInline (8.4/8.5 netaknut — SM-D1/AC12)."
        )


# ══════════════════════════════════════════════════════════════════════════════
# BATCH-FIX B (TEST_GAP — 8.4 M2 lesson): inline upload delegation locks.
# Each remaining inline form's clean_*-image/photo MUST fire the media_pipeline
# validate_image_mime delegation. Previously only ProductImage + ProductBrochure(pdf)
# rejection paths were exercised; the 3 below were unproven on the validate path.
# ══════════════════════════════════════════════════════════════════════════════
# AC-3: ProductVariant inline form rejects fake image (blank-able image, validate-on-present)
def test_ac3_variant_inline_form_rejects_fake_image(fake_image_txt):
    from apps.products.admin import ProductVariantInlineForm

    form = ProductVariantInlineForm(
        data={"name_sr": "Sa kabinom", "code": "", "order": "0"},
        files={"image": fake_image_txt},
    )
    assert not form.is_valid(), (
        "Lažna slika u ProductVariant.image polju MORA biti odbijena (MIME — AC3)."
    )
    assert "Nedozvoljen tip slike" in _field_errors_text(form, "image"), (
        f"Greška MORA sadržati 'Nedozvoljen tip slike' na `image` (validate_image_mime "
        f"delegacija u ProductVariantInlineForm); dobio {form.errors!r}."
    )


# AC-3: ProductVariant inline form accepts a valid image (positive delegation path)
def test_ac3_variant_inline_form_accepts_valid_image(valid_jpeg, brand):
    from apps.products.admin import ProductVariantInlineForm
    from apps.products.tests.factories import ProductFactory

    # `product` je OBAVEZAN FK na ProductVariant kad se inline form bind-uje direktno.
    product = ProductFactory.create(brand=brand)
    form = ProductVariantInlineForm(
        data={"name_sr": "Sa kabinom", "code": "", "order": "0", "product": str(product.pk)},
        files={"image": valid_jpeg},
    )
    assert form.is_valid(), (
        f"Validan JPEG MORA proći ProductVariant inline upload check (AC3); "
        f"errors={form.errors!r}."
    )


# AC-3: ProductTestimonial inline form (clean_photo) rejects fake image
def test_ac3_testimonial_inline_form_rejects_fake_photo(fake_image_txt):
    from apps.products.admin import ProductTestimonialInlineForm

    form = ProductTestimonialInlineForm(
        data={"quote_sr": "Odličan traktor.", "author_name": "Marko", "order": "0"},
        files={"photo": fake_image_txt},
    )
    assert not form.is_valid(), (
        "Lažna slika u ProductTestimonial.photo polju MORA biti odbijena (MIME — AC3)."
    )
    assert "Nedozvoljen tip slike" in _field_errors_text(form, "photo"), (
        f"Greška MORA sadržati 'Nedozvoljen tip slike' na `photo` (validate_image_mime "
        f"delegacija u ProductTestimonialInlineForm.clean_photo); dobio {form.errors!r}."
    )


# AC-3: ProductBrochure inline form (clean_cover_thumbnail_image) rejects fake image
def test_ac3_brochure_inline_form_rejects_fake_cover(fake_image_txt):
    from apps.products.admin import ProductBrochureInlineForm

    form = ProductBrochureInlineForm(
        data={"title_sr": "Brošura"},
        files={"cover_thumbnail_image": fake_image_txt},
    )
    assert not form.is_valid(), (
        "Lažna slika u ProductBrochure.cover_thumbnail_image polju MORA biti odbijena "
        "(MIME — AC3)."
    )
    assert "Nedozvoljen tip slike" in _field_errors_text(form, "cover_thumbnail_image"), (
        f"Greška MORA sadržati 'Nedozvoljen tip slike' na `cover_thumbnail_image` "
        f"(validate_image_mime delegacija u clean_cover_thumbnail_image); dobio {form.errors!r}."
    )


# ══════════════════════════════════════════════════════════════════════════════
# BATCH-FIX C (TEST_GAP): required-empty guards + model-clean delegations.
# ══════════════════════════════════════════════════════════════════════════════
# AC-3: ProductImage inline form with EMPTY required image → graceful field-level reject
# (unconditional helper: must NOT silently pass and must NOT 500). The error is either
# Django's required-field message OR the media_pipeline "Slika je prazna ili nije priložena."
def test_ac3_image_inline_form_empty_required_image_rejected():
    from apps.products.admin import ProductImageInlineForm

    form = ProductImageInlineForm(
        data={"order": "0", "alt_text_sr": ""},
        files={},  # required image missing
    )
    assert not form.is_valid(), (
        "Prazno OBAVEZNO ProductImage.image polje MORA biti odbijeno (NE smie tiho proći "
        "niti 500 — AC3 HARD RULE)."
    )
    assert "image" in form.errors, (
        f"Greška MORA biti vezana za `image` polje (required ILI 'Slika je prazna...' "
        f"media_pipeline poruka); dobio {form.errors!r}."
    )


# AC-3: ProductBrochure inline form with EMPTY required pdf_file → graceful field-level reject
def test_ac3_brochure_inline_form_empty_required_pdf_rejected():
    from apps.products.admin import ProductBrochureInlineForm

    form = ProductBrochureInlineForm(
        data={"title_sr": "Brošura"},
        files={},  # required pdf_file missing
    )
    assert not form.is_valid(), (
        "Prazno OBAVEZNO ProductBrochure.pdf_file polje MORA biti odbijeno (NE smie tiho "
        "proći niti 500 — AC3 HARD RULE)."
    )
    assert "pdf_file" in form.errors, (
        f"Greška MORA biti vezana za `pdf_file` polje (required ILI media_pipeline prazno-fajl "
        f"poruka); dobio {form.errors!r}."
    )


# AC-10: non-string key_features element → Product.clean() "Svaka stavka mora biti string."
# (delegated to the model — admin does NOT re-implement; G-7).
def test_ac10_non_string_key_feature_blocked_by_model(brand):
    # Validan JSON list ali element NIJE string (broj) → Product.clean() ga odbija.
    form = _make_main_form(
        data={
            "name": "KF",
            "slug": "kf",
            "name_sr": "KF",
            "brand": str(brand.pk),
            "key_features_sr": '["ok", 123]',
        },
    )
    assert not form.is_valid(), (
        "key_features sa ne-string elementom MORA biti odbijen (Product.clean() — AC10/G-7)."
    )
    assert "Svaka stavka mora biti string." in _field_errors_text(form, "key_features_sr"), (
        f"Greška MORA sadržati 'Svaka stavka mora biti string.' na `key_features_sr` "
        f"(model clean delegacija, NE re-implementacija u adminu — G-7); dobio {form.errors!r}."
    )


def _similar_prefix(data):
    """Discover the ProductSimilar inline formset prefix from scraped change-form data.

    The inline form fields are namespaced `<prefix>-<i>-related_product`. Find the prefix
    whose management form exists AND whose row fields include `related_product` (robust to
    Django's inline-prefix naming for the fk_name='product' two-FK case)."""
    import re

    for key in data:
        m = re.match(r"^(.*)-related_product$", key)
        if m and f"{m.group(1).rsplit('-', 1)[0]}-TOTAL_FORMS" in data:
            return m.group(1).rsplit("-", 1)[0]
    return None


# AC-8/G-7: ProductSimilar self-reference (related_product == product) is rejected by
# ProductSimilar.clean() and surfaces as a GRACEFUL HTTP 200 (NOT 500) through the admin POST.
def test_ac8_similar_self_reference_graceful_200(client, superuser, brand):
    from apps.products.tests.factories import ProductFactory

    client.force_login(superuser)
    product = ProductFactory.create(brand=brand, name="Self Ref Proizvod")
    url = reverse("admin:products_product_change", args=[product.pk])
    data = _scrape_change_form(client.get(url).content.decode())
    data["brand"] = str(product.brand_id)
    data["name_sr"] = product.name_sr or "Self Ref Proizvod"
    data["status"] = "draft"
    data["is_published"] = ""
    data.setdefault("key_features_sr", "[]")

    prefix = _similar_prefix(data)
    assert prefix is not None, (
        f"Nije pronađen ProductSimilar inline prefix u scraped formi; ključevi: "
        f"{sorted(k for k in data if 'similar' in k.lower() or 'related' in k.lower())}"
    )
    # Add ONE inline row pointing related_product back to the SAME product (self-reference).
    data[f"{prefix}-TOTAL_FORMS"] = "1"
    data[f"{prefix}-INITIAL_FORMS"] = "0"
    data.setdefault(f"{prefix}-MIN_NUM_FORMS", "0")
    data.setdefault(f"{prefix}-MAX_NUM_FORMS", "1000")
    data[f"{prefix}-0-related_product"] = str(product.pk)
    data[f"{prefix}-0-order"] = "0"

    resp = client.post(url, data, follow=True)
    assert resp.status_code == 200, (
        f"Self-reference sličan proizvod MORA dati graceful 200 (ProductSimilar.clean() "
        f"ValidationError → admin form-error, NIKAD 500 — AC8/G-7); dobio {resp.status_code}."
    )
    assert "Sličan proizvod ne sme biti isti kao izvorni proizvod." in resp.content.decode(), (
        "Admin MORA prikazati srpsku ProductSimilar.clean() poruku za self-reference "
        "(graceful inline form-error)."
    )
