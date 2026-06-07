"""Story 8.4 — Brand CRUD Admin (TEA RED phase).

DEFINES the contract Dev must satisfy. Maps to the 11 ACs + Testing section of
`8-4-brand-crud-admin.md`. Canonical contract: `8-4-brand-crud-admin-interface-contract.md`.

RUN (MUST go through Docker — libmagic/python-magic + Pillow are NOT on the Windows host):
    just test apps/brands/tests/test_brand_crud_admin.py -v

RED expectation: `apps/brands/admin.py` is still the minimal 6.1 stub
(`BrandAdmin(SeoWarningAdminMixin, ModelAdmin)`, no `BrandAdminForm`, no `SeriesInline`,
no `MAX_*_UPLOAD_SIZE`, no preview/has_pdf methods, no `SeriesAdmin.view_on_site`). So
nearly every test MUST fail/error. EXCEPTION: the SeoMetaInline-still-present regression
lock (`test_ac6_seometa_inline_still_on_brandadmin`) MAY pass today (6.1 already has it) —
that is fine and expected (noted inline).

────────────────────────────────────────────────────────────────────────────────
COLLECTION-SAFETY: all `apps.brands.admin` / `BrandAdminForm` imports are INSIDE test
bodies (lazy) so a missing symbol fails that test individually (true RED), never aborts
collection of the whole file.

AUTH: authenticate with `force_login` (NEVER `client.login` — django-axes from 8.1
pollutes lockout state through authenticate(); established project lesson).

ADMIN URL: always `reverse("admin:brands_brand_*")` — admin is at bare `/admin-coric/`
(8.1), never hardcode.

EDITOR USER: `is_staff` + member of `Editor` group. The `Editor` group is created by the
8.2 `sync_rbac_groups` post_migrate handler during test-DB setup, and already carries
brands.add/change/delete/view (EDITOR_CONTENT_MODELS). 8.4 does NOT re-grant (SM-D7).

Refs: 8-4-brand-crud-admin.md (AC1-AC11, SM-D1..D9, G-1..G-13, Testing) +
8-4-brand-crud-admin-interface-contract.md.
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
        username="brand_admin_tea",
        email="brand-admin@example.com",
        password="tea-pass-12345",
    )


@pytest.fixture
def editor(django_user_model):
    """Editor = is_staff + member of the `Editor` group (8.2 post_migrate created it;
    group already carries brands CRUD via EDITOR_CONTENT_MODELS — SM-D7)."""
    from django.contrib.auth.models import Group

    user = django_user_model.objects.create_user(
        username="brand_editor_tea",
        email="brand-editor@example.com",
        password="tea-pass-12345",
        is_staff=True,
        is_superuser=False,
    )
    user.groups.add(Group.objects.get(name="Editor"))
    return user


# ──────────────────────────────────────────────────────────────────────────────
# Upload fixtures (Pillow + raw bytes — mirror apps/forms/tests/conftest.py)
# ──────────────────────────────────────────────────────────────────────────────
def _pillow_upload(fmt, content_type, filename):
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (10, 10), color=(34, 64, 47)).save(buf, format=fmt)
    buf.seek(0)
    return SimpleUploadedFile(filename, buf.read(), content_type=content_type)


@pytest.fixture
def valid_jpeg():
    return _pillow_upload("JPEG", "image/jpeg", "logo.jpg")


@pytest.fixture
def valid_png():
    return _pillow_upload("PNG", "image/png", "hero.png")


@pytest.fixture
def valid_webp():
    """Valid WEBP (story Testing lists jpeg/png/webp; image/webp is in ALLOWED_IMAGE_MIME_TYPES)."""
    return _pillow_upload("WEBP", "image/webp", "logo.webp")


@pytest.fixture
def oversized_png():
    """Valid small PNG with forced .size > 5 MB (hero size-cap parity)."""
    up = _pillow_upload("PNG", "image/png", "velika-hero.png")
    up.size = 6 * 1024 * 1024
    return up


@pytest.fixture
def fake_image_txt():
    """Plain text renamed .jpg with image/jpeg content-type — MIME signature is text/plain."""
    return SimpleUploadedFile(
        "evil.jpg", b"this is just text, not an image at all", content_type="image/jpeg"
    )


@pytest.fixture
def corrupt_jpeg():
    """JPEG magic header but garbage body — passes nothing / fails Pillow verify()."""
    return SimpleUploadedFile(
        "corrupt.jpg", b"\xff\xd8\xff\xe0nije-validna-slika-vec-djubre", content_type="image/jpeg"
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
    """A real PNG renamed .pdf with application/pdf content-type — MIME signature is image/png."""
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
def oversized_pdf():
    """Valid PDF signature with forced .size > 20 MB."""
    up = SimpleUploadedFile(
        "velika.pdf", b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n", content_type="application/pdf"
    )
    up.size = 21 * 1024 * 1024
    return up


@pytest.fixture
def decompression_bomb_png():
    """8000×8000 (64M px) solid-color PNG — declares pixel dimensions > Image.MAX_IMAGE_PIXELS
    (50M) but is only ~30KB on disk (well under MAX_IMAGE_UPLOAD_SIZE).

    Locks the M2 decompression-bomb guard: the size cap does NOT early-out (small on disk),
    so the bomb MUST be caught by validate_image_mime's DecompressionBombWarning→error
    escalation. Mirror apps/media_pipeline/tests/conftest.py:decompression_bomb_bytes.
    """
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (8000, 8000), color="white").save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return SimpleUploadedFile("bomba.png", buf.read(), content_type="image/png")


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────
def _brand_admin():
    from apps.brands.models import Brand

    return admin.site._registry[Brand]


def _make_form(data=None, files=None, instance=None):
    """Bind BrandAdminForm (lazy import — collection-safe). Wraps fields in a way that
    exercises clean_<field> + clean()."""
    from apps.brands.admin import BrandAdminForm

    return BrandAdminForm(data=data or {}, files=files, instance=instance)


def _field_errors_text(form, field):
    return " ".join(str(e) for e in form.errors.get(field, []))


# ══════════════════════════════════════════════════════════════════════════════
# AC1 — BrandAdmin is TranslationAdmin + changelist/add/change 200 (superuser & Editor)
# ══════════════════════════════════════════════════════════════════════════════
# AC-1
def test_ac1_brandadmin_is_translationadmin():
    from modeltranslation.admin import TranslationAdmin

    model_admin = _brand_admin()
    assert isinstance(model_admin, TranslationAdmin), (
        "BrandAdmin MORA biti TranslationAdmin instanca (NE plain ModelAdmin — AC1)."
    )


# AC-1
def test_ac1_brandadmin_has_seowarning_mixin_in_mro():
    from apps.seo.admin import SeoWarningAdminMixin

    assert isinstance(_brand_admin(), SeoWarningAdminMixin), (
        "BrandAdmin MORA zadržati SeoWarningAdminMixin u MRO (mixin PRVI — G-2/AC1)."
    )


# AC-1
def test_ac1_search_fields_uses_name_sr_not_virtual_name():
    model_admin = _brand_admin()
    assert tuple(model_admin.search_fields) == ("name_sr",), (
        "search_fields MORA biti ('name_sr',) — realna DB kolona, NE virtuelni `name` "
        f"(baca FieldError/admin.E* — G-1); dobio {model_admin.search_fields!r}."
    )


# AC-1
def test_ac1_changelist_200_superuser(client, superuser):
    from apps.brands.tests.factories import BrandFactory

    BrandFactory.create(name="John Deere")
    client.force_login(superuser)
    resp = client.get(reverse("admin:brands_brand_changelist"))
    assert resp.status_code == 200, (
        f"Superuser Brand changelist MORA biti 200 (AC1); dobio {resp.status_code}."
    )


# AC-1
def test_ac1_add_view_200_superuser(client, superuser):
    client.force_login(superuser)
    resp = client.get(reverse("admin:brands_brand_add"))
    assert resp.status_code == 200, (
        f"Superuser Brand add-view MORA biti 200 (per-locale + 2 inline render — AC1/G-9); "
        f"dobio {resp.status_code}."
    )


# AC-1
def test_ac1_change_view_200_superuser(client, superuser):
    from apps.brands.tests.factories import BrandFactory

    brand = BrandFactory.create(name="Agri Tracking")
    client.force_login(superuser)
    resp = client.get(reverse("admin:brands_brand_change", args=[brand.pk]))
    assert resp.status_code == 200, (
        f"Superuser Brand change-view MORA biti 200 (AC1); dobio {resp.status_code}."
    )


# AC-1
def test_ac1_change_view_renders_per_locale_fields(client, superuser):
    from apps.brands.tests.factories import BrandFactory

    brand = BrandFactory.create(name="Đuro Đaković")
    client.force_login(superuser)
    html = client.get(reverse("admin:brands_brand_change", args=[brand.pk])).content.decode()
    # NAPOMENA (TEA review): per-locale kolone (`name_sr/_hu/_en`) su MATERIJALIZOVANE DB
    # kolone → renderuju se i pod plain ModelAdmin i pod TranslationAdmin (u ovoj projektnoj
    # konfiguraciji NEMA HTML-diskriminatora između to dvoje — verifikovano). Ovo je zato
    # RENDER-SMOKE (forma sa budućim 2-inline + custom form setup-om se ne ruši i renderuje
    # sve lokale), NE dokaz TranslationAdmin tipa. AC1 tip LOCK je
    # `test_ac1_brandadmin_is_translationadmin` (type-level) — taj je pravi diskriminator.
    for fld in ("name_sr", "name_hu", "name_en", "description_sr", "slogan_sr"):
        assert f'name="{fld}"' in html, (
            f"Change-view MORA renderovati per-locale polje '{fld}' (render-smoke — AC1)."
        )


# AC-1 / AC-10
def test_ac1_add_view_200_editor(client, editor):
    client.force_login(editor)
    resp = client.get(reverse("admin:brands_brand_add"))
    assert resp.status_code == 200, (
        f"Editor Brand add-view MORA biti 200 (forma se renderuje bez admin.E* — AC1/AC10); "
        f"dobio {resp.status_code}."
    )


# AC-1
def test_ac1_admin_system_checks_clean():
    from django.core.checks import run_checks

    errors = [e for e in run_checks() if e.is_serious()]
    assert errors == [], (
        f"manage.py check MORA biti čist — TranslationAdmin + 2 inline-a + prepopulated_fields "
        f"ne smeju baciti admin.E* (AC1/G-9). Greške: {errors}."
    )


# ══════════════════════════════════════════════════════════════════════════════
# AC2 — image preview methods (format_html, escaped, truthy-guard)
# ══════════════════════════════════════════════════════════════════════════════
# AC-2
def test_ac2_preview_methods_exist():
    model_admin = _brand_admin()
    assert hasattr(model_admin, "logo_preview") and hasattr(model_admin, "hero_preview"), (
        "BrandAdmin MORA imati logo_preview + hero_preview readonly metode (AC2)."
    )


# AC-2
def test_ac2_preview_empty_when_no_image():
    from apps.brands.tests.factories import BrandFactory

    model_admin = _brand_admin()
    brand = BrandFactory.create(name="Bez Logoa")  # no logo/hero
    out = str(model_admin.logo_preview(brand))
    assert "<img" not in out, (
        f"logo_preview MORA biti prazno (npr. '—') kad slika ne postoji — BEZ slomljenog "
        f"<img> (AC2); dobio {out!r}."
    )


# AC-2
def test_ac2_preview_renders_escaped_img_when_image_set(valid_jpeg):
    from apps.brands.tests.factories import BrandFactory

    model_admin = _brand_admin()
    brand = BrandFactory.create(name="Sa Logoom")
    brand.logo.save("logo.jpg", valid_jpeg, save=True)
    out = str(model_admin.logo_preview(brand))
    assert "<img" in out and brand.logo.url in out, (
        f"logo_preview MORA renderovati <img src=...> kad logo postoji (format_html — AC2); "
        f"dobio {out!r}."
    )


# AC-2 — hero_preview empty when no image (parity with logo)
def test_ac2_hero_preview_empty_when_no_image():
    from apps.brands.tests.factories import BrandFactory

    model_admin = _brand_admin()
    brand = BrandFactory.create(name="Bez Hero Slike")  # no hero_image
    out = str(model_admin.hero_preview(brand))
    assert "<img" not in out, (
        f"hero_preview MORA biti prazno (npr. '—') kad hero_image ne postoji — BEZ slomljenog "
        f"<img> (AC2); dobio {out!r}."
    )


# AC-2 — hero_preview renders escaped <img> when hero_image set (covers admin.py truthy branch)
def test_ac2_hero_preview_renders_escaped_img_when_image_set(valid_png):
    from apps.brands.tests.factories import BrandFactory

    model_admin = _brand_admin()
    brand = BrandFactory.create(name="Sa Hero Slikom")
    brand.hero_image.save("hero.png", valid_png, save=True)
    out = str(model_admin.hero_preview(brand))
    assert "<img" in out and brand.hero_image.url in out, (
        f"hero_preview MORA renderovati <img src=...> kad hero_image postoji (format_html — AC2); "
        f"dobio {out!r}."
    )


# ══════════════════════════════════════════════════════════════════════════════
# AC3 (SECURITY) — upload MIME/signature double-check (needs Docker/libmagic)
# ══════════════════════════════════════════════════════════════════════════════
# AC-3
def test_ac3_form_has_upload_clean_methods():
    from apps.brands.admin import BrandAdminForm

    for m in ("clean_logo", "clean_hero_image", "clean_catalog_pdf"):
        assert hasattr(BrandAdminForm, m), (
            f"BrandAdminForm MORA imati {m} (upload double-check — AC3/G-13/SM-D9)."
        )


# AC-3
def test_ac3_upload_size_constants_defined():
    from apps.brands import admin as brands_admin

    assert brands_admin.MAX_IMAGE_UPLOAD_SIZE == 5 * 1024 * 1024, (
        "MAX_IMAGE_UPLOAD_SIZE MORA biti 5 MB (UPPER_SNAKE_CASE — AC3/OQ-5)."
    )
    assert brands_admin.MAX_PDF_UPLOAD_SIZE == 20 * 1024 * 1024, (
        "MAX_PDF_UPLOAD_SIZE MORA biti 20 MB (UPPER_SNAKE_CASE — AC3/OQ-5)."
    )


# AC-3 (security)
def test_ac3_clean_logo_rejects_fake_image(fake_image_txt):
    form = _make_form(
        data={"name_sr": "X", "is_coming_soon": "on", "statistics": "[]"},
        files={"logo": fake_image_txt},
    )
    assert not form.is_valid(), "Lažna slika (.jpg ali tekst) MORA biti odbijena (MIME — AC3)."
    # Blessed media_pipeline.validate_image_mime poruka za nedozvoljen MIME (M2 reuse).
    assert "Nedozvoljen tip slike" in _field_errors_text(form, "logo"), (
        f"Greška za lažnu sliku MORA sadržati 'Nedozvoljen tip slike' na `logo` "
        f"(validate_image_mime kanonska poruka); dobio {form.errors!r}."
    )


# AC-3 (security)
def test_ac3_clean_hero_image_rejects_fake_image(fake_image_txt):
    fake_image_txt.name = "evil.png"
    form = _make_form(
        data={"name_sr": "X", "is_coming_soon": "on", "statistics": "[]"},
        files={"hero_image": fake_image_txt},
    )
    assert not form.is_valid(), "Lažna hero slika MORA biti odbijena (MIME — AC3)."
    assert "Nedozvoljen tip slike" in _field_errors_text(form, "hero_image"), (
        f"Greška MORA biti na `hero_image` (validate_image_mime kanonska poruka); "
        f"dobio {form.errors!r}."
    )


# AC-3 (security) — corrupt image passes MIME header check but fails Pillow verify()
def test_ac3_clean_logo_rejects_corrupt_image(corrupt_jpeg):
    form = _make_form(
        data={"name_sr": "X", "is_coming_soon": "on", "statistics": "[]"},
        files={"logo": corrupt_jpeg},
    )
    assert not form.is_valid(), (
        "Korumpiran JPEG (magic header OK, Pillow verify pada) MORA biti odbijen (AC3)."
    )
    # CORRUPT magic-bytes su image/jpeg (verifikovano) → MORA stići do Pillow verify()
    # grane; validate_image_mime hvata OSError/SyntaxError i vraća srpsku poruku (NE 500).
    assert "Slika je oštećena ili nije validan format" in _field_errors_text(form, "logo"), (
        f"Korumpiran JPEG MORA pasti na Pillow verify() sa kanonskom porukom "
        f"'Slika je oštećena ili nije validan format.' na `logo` "
        f"(validate_image_mime — Image.open().verify() wrap-ovan, NE goli OSError/500); "
        f"dobio {form.errors!r}."
    )


# AC-3 (security) — decompression bomb: declared dims > 50M px, small on disk → REJECTED
def test_ac3_clean_logo_rejects_decompression_bomb(decompression_bomb_png):
    """M2 lock — 64M-px PNG (~30KB on disk) MUST be rejected by the blessed
    validate_image_mime decompression-bomb guard (Image.MAX_IMAGE_PIXELS=50M +
    DecompressionBombWarning→error). The inline duplicate validator (pre-M2) had NO
    bomb guard → a 121M-px PNG passed (runtime-proven by Security review). Reusing the
    canonical helper restores the guard."""
    form = _make_form(
        data={"name_sr": "X", "is_coming_soon": "on", "statistics": "[]"},
        files={"logo": decompression_bomb_png},
    )
    assert not form.is_valid(), (
        "Decompression-bomb slika (64M px, mala na disku) MORA biti odbijena "
        "(validate_image_mime MAX_IMAGE_PIXELS=50M guard — M2)."
    )
    assert "Slika je oštećena ili nije validan format" in _field_errors_text(form, "logo"), (
        f"Bomba MORA dati kanonsku validate_image_mime poruku na `logo`; dobio {form.errors!r}."
    )


# AC-3 (security)
def test_ac3_clean_catalog_pdf_rejects_non_pdf(fake_pdf_is_image):
    form = _make_form(
        data={"name_sr": "X", "is_coming_soon": "on", "statistics": "[]"},
        files={"catalog_pdf": fake_pdf_is_image},
    )
    assert not form.is_valid(), "Ne-PDF (slika preimenovana u .pdf) MORA biti odbijen (MIME — AC3)."
    # Blessed validate_pdf_mime poruka: "Nedozvoljen tip fajla: <mime>. Dozvoljen je samo PDF format."
    assert "Nedozvoljen tip fajla" in _field_errors_text(form, "catalog_pdf"), (
        f"Greška MORA biti na `catalog_pdf` (validate_pdf_mime kanonska poruka); "
        f"dobio {form.errors!r}."
    )


# AC-3
def test_ac3_clean_logo_accepts_valid_image(valid_jpeg):
    # name/slug populated: raw BrandAdminForm carries base `name`/`slug` (blank=False) which
    # are required (M1 — required-promotion no longer relaxed). Upload-path assertion is the focus.
    form = _make_form(
        data={
            "name": "Validan", "slug": "validan",
            "name_sr": "Validan", "is_coming_soon": "on", "statistics": "[]",
        },
        files={"logo": valid_jpeg},
    )
    assert form.is_valid(), (
        f"Validan JPEG logo MORA proći upload double-check (AC3); errors={form.errors!r}."
    )


# AC-3 — valid WEBP logo accepted (story Testing lists jpeg/png/webp)
def test_ac3_clean_logo_accepts_valid_webp(valid_webp):
    form = _make_form(
        data={
            "name": "Validan", "slug": "validan",
            "name_sr": "Validan", "is_coming_soon": "on", "statistics": "[]",
        },
        files={"logo": valid_webp},
    )
    assert form.is_valid(), (
        f"Validan WEBP logo MORA proći upload double-check — image/webp je u "
        f"ALLOWED_IMAGE_MIME_TYPES (AC3); errors={form.errors!r}."
    )


# AC-3 — positive hero path: valid image accepted on hero_image
def test_ac3_clean_hero_image_accepts_valid_image(valid_png):
    form = _make_form(
        data={
            "name": "Validan", "slug": "validan",
            "name_sr": "Validan", "is_coming_soon": "on", "statistics": "[]",
        },
        files={"hero_image": valid_png},
    )
    assert form.is_valid(), (
        f"Validan PNG hero_image MORA proći upload double-check (AC3); errors={form.errors!r}."
    )


# AC-3 (security) — corrupt hero image fails Pillow verify() (parity with logo)
def test_ac3_clean_hero_image_rejects_corrupt_image(corrupt_jpeg):
    # Reuse corrupt_jpeg: its \xff\xd8\xff\xe0 magic-bytes are image/jpeg (libmagic) so it
    # PASSES the MIME header check and reaches the Pillow verify() branch on the hero path
    # (parity with test_ac3_clean_logo_rejects_corrupt_image). Filename irrelevant to libmagic.
    form = _make_form(
        data={"name_sr": "X", "is_coming_soon": "on", "statistics": "[]"},
        files={"hero_image": corrupt_jpeg},
    )
    assert not form.is_valid(), (
        "Korumpiran hero_image (magic header OK, Pillow verify pada) MORA biti odbijen (AC3)."
    )
    assert "Slika je oštećena ili nije validan format" in _field_errors_text(
        form, "hero_image"
    ), (
        f"Korumpiran hero MORA pasti na Pillow verify() sa kanonskom porukom na "
        f"`hero_image`; dobio {form.errors!r}."
    )


# AC-3 (edge) — oversized hero image rejected (parity with logo)
def test_ac3_clean_hero_image_rejects_oversized(oversized_png):
    form = _make_form(
        data={"name_sr": "X", "is_coming_soon": "on", "statistics": "[]"},
        files={"hero_image": oversized_png},
    )
    assert not form.is_valid(), "hero_image > MAX_IMAGE_UPLOAD_SIZE MORA biti odbijen (AC3)."
    assert "hero_image" in form.errors


# AC-3
def test_ac3_clean_catalog_pdf_accepts_valid_pdf(valid_pdf):
    form = _make_form(
        data={
            "name": "Validan", "slug": "validan",
            "name_sr": "Validan", "is_coming_soon": "on", "statistics": "[]",
        },
        files={"catalog_pdf": valid_pdf},
    )
    assert form.is_valid(), (
        f"Validan PDF katalog MORA proći (AC3); errors={form.errors!r}."
    )


# AC-3 (edge) — oversized image rejected
def test_ac3_clean_logo_rejects_oversized(oversized_image):
    form = _make_form(
        data={"name_sr": "X", "is_coming_soon": "on", "statistics": "[]"},
        files={"logo": oversized_image},
    )
    assert not form.is_valid(), "Logo > MAX_IMAGE_UPLOAD_SIZE MORA biti odbijen (AC3)."
    assert "logo" in form.errors


# AC-3 (edge) — oversized pdf rejected
def test_ac3_clean_catalog_pdf_rejects_oversized(oversized_pdf):
    form = _make_form(
        data={"name_sr": "X", "is_coming_soon": "on", "statistics": "[]"},
        files={"catalog_pdf": oversized_pdf},
    )
    assert not form.is_valid(), "PDF > MAX_PDF_UPLOAD_SIZE MORA biti odbijen (AC3)."
    assert "catalog_pdf" in form.errors


# AC-3 (edge) — blank/None upload skipped gracefully (no error)
def test_ac3_blank_uploads_skip_gracefully():
    form = _make_form(
        data={
            "name": "Bez Uploada", "slug": "bez-uploada",
            "name_sr": "Bez Uploada", "is_coming_soon": "on", "statistics": "[]",
        },
        files={},
    )
    assert form.is_valid(), (
        f"Prazan/None upload (blank=True polja) MORA proći bez greške (graceful skip — AC3); "
        f"errors={form.errors!r}."
    )


# ══════════════════════════════════════════════════════════════════════════════
# AC4 — brand_color HTML5 color input widget
# ══════════════════════════════════════════════════════════════════════════════
# AC-4
def test_ac4_brand_color_widget_is_color_input():
    form = _make_form()
    widget = form.fields["brand_color"].widget
    assert widget.attrs.get("type") == "color", (
        f"brand_color widget MORA imati attrs type='color' (HTML5 color picker — AC4); "
        f"dobio {widget.attrs!r}."
    )


# AC-4
def test_ac4_change_view_renders_color_input(client, superuser):
    from apps.brands.tests.factories import BrandFactory

    brand = BrandFactory.create(name="Boja Test", brand_color="#1A2B3C")
    client.force_login(superuser)
    html = client.get(reverse("admin:brands_brand_change", args=[brand.pk])).content.decode()
    assert 'type="color"' in html, (
        "Change-view MORA renderovati <input type=\"color\"> za brand_color (AC4)."
    )


# AC-4 — invalid hex blocked by Brand.clean() (model single source, G-7), not duplicated in admin
def test_ac4_invalid_hex_blocked_by_model_clean():
    form = _make_form(
        data={"name_sr": "X", "is_coming_soon": "on", "statistics": "[]", "brand_color": "crvena"},
    )
    assert not form.is_valid(), "Nevalidan brand_color ('crvena') MORA blokirati save (model clean — AC4/G-7)."
    assert "brand_color" in form.errors


# ══════════════════════════════════════════════════════════════════════════════
# AC5 — statistics JSON editor: invalid JSON field error (no 500); model enforces shape/max
# ══════════════════════════════════════════════════════════════════════════════
# AC-5 (error-path) — syntactically broken JSON → field-level ValidationError, no 500
def test_ac5_invalid_json_field_error_no_500():
    form = _make_form(
        data={"name_sr": "X", "is_coming_soon": "on", "statistics": "{ne-zatvoren"},
    )
    assert not form.is_valid(), "Sintaksno polomljen JSON MORA biti odbijen (AC5)."
    assert "statistics" in form.errors, (
        f"Nevalidan JSON MORA dati field-level grešku na `statistics` (NE 500 — AC5); "
        f"dobio {form.errors!r}."
    )


# AC-5 — > 4 entries blocked by model clean() (admin does NOT duplicate — G-7)
def test_ac5_more_than_four_statistics_blocked_by_model():
    five = '[{"v":1},{"v":2},{"v":3},{"v":4},{"v":5}]'
    form = _make_form(
        data={"name_sr": "X", "is_coming_soon": "on", "statistics": five},
    )
    assert not form.is_valid(), "5 statistika MORA blokirati save (Brand.clean() max 4 — AC5/G-7)."
    assert "statistics" in form.errors


# AC-5 — non-dict element blocked by model clean()
def test_ac5_non_dict_statistics_element_blocked_by_model():
    bad = '["nije-dict", 123]'
    form = _make_form(
        data={"name_sr": "X", "is_coming_soon": "on", "statistics": bad},
    )
    assert not form.is_valid(), "Ne-dict element u statistics MORA blokirati save (Brand.clean() — AC5/G-7)."
    assert "statistics" in form.errors


# ══════════════════════════════════════════════════════════════════════════════
# AC6 — SeriesInline + SeoMetaInline regression + SeriesAdmin hardening
# ══════════════════════════════════════════════════════════════════════════════
# AC-6
def test_ac6_series_inline_present_and_translation_stacked():
    from modeltranslation.admin import TranslationStackedInline

    inlines = list(_brand_admin().inlines)
    series_inlines = [
        ic for ic in inlines if getattr(ic, "model", None).__name__ == "Series"
    ]
    assert series_inlines, "BrandAdmin.inlines MORA sadržati SeriesInline (AC6)."
    assert all(issubclass(ic, TranslationStackedInline) for ic in series_inlines), (
        "SeriesInline MORA biti TranslationStackedInline (per-locale name/description — AC6)."
    )


# AC-6 (G-10)
def test_ac6_series_inline_excludes_slug():
    inlines = list(_brand_admin().inlines)
    series_inline = next(
        ic for ic in inlines if getattr(ic, "model", None).__name__ == "Series"
    )
    assert "slug" in tuple(getattr(series_inline, "exclude", ()) or ()), (
        "SeriesInline MORA imati exclude=('slug',) — Series.save() auto-gen slug (G-10/AC6)."
    )


# AC-6 (regression-lock — MAY PASS today: 6.1 already has SeoMetaInline on BrandAdmin)
def test_ac6_seometa_inline_still_on_brandadmin():
    from apps.seo.admin import SeoMetaInline

    inlines = list(_brand_admin().inlines)
    assert any(ic is SeoMetaInline or issubclass(ic, SeoMetaInline) for ic in inlines), (
        "SeoMetaInline MORA OSTATI na BrandAdmin posle konverzije (6.1 regression — G-8/AC6/AC11)."
    )


# AC-6 — adding a Series inline row with ONLY name_sr saves (slug auto-gen via Series.save())
def test_ac6_series_inline_row_name_only_saves(client, superuser):
    from apps.brands.models import Series
    from apps.brands.tests.factories import BrandFactory

    brand = BrandFactory.create(name="Brend Sa Serijom")
    client.force_login(superuser)
    url = reverse("admin:brands_brand_change", args=[brand.pk])
    data = _scrape_change_form(client.get(url).content.decode())

    # populate ONE Series inline row with only name_sr (NO slug)
    prefix = "series"
    data[f"{prefix}-TOTAL_FORMS"] = "1"
    data[f"{prefix}-INITIAL_FORMS"] = "0"
    data[f"{prefix}-MIN_NUM_FORMS"] = "0"
    data[f"{prefix}-MAX_NUM_FORMS"] = "1000"
    data[f"{prefix}-0-name_sr"] = "8R Serija"
    data[f"{prefix}-0-layout_mode"] = "grid"
    data[f"{prefix}-0-display_order"] = "0"
    data[f"{prefix}-0-id"] = ""
    data[f"{prefix}-0-brand"] = str(brand.pk)

    resp = client.post(url, data, follow=True)
    assert resp.status_code == 200, (
        "POST Brand change sa Series inline-om NE sme pasti na brands:series_detail "
        "NoReverseMatch (G-3)."
    )
    saved = Series.objects.filter(brand=brand, name_sr="8R Serija").first()
    assert saved is not None, (
        "Series inline red SAMO sa name_sr MORA biti sačuvan (slug auto-gen, exclude slug — G-10/AC6)."
    )
    assert saved.slug, "Sačuvana Series MORA imati auto-generisan slug (Series.save() — G-10)."


# AC-6 (G-3 / SM-D8) — SeriesAdmin.view_on_site is False
def test_ac6_series_admin_view_on_site_false():
    from apps.brands.models import Series

    model_admin = admin.site._registry[Series]
    assert model_admin.view_on_site is False, (
        "SeriesAdmin.view_on_site MORA biti False (brands:series_detail neregistrovan — "
        "proaktivno otvrdnjavanje, mirror blog BL-5 — G-3/SM-D8/AC6)."
    )


# AC-6 — SeoMetaInline STILL on standalone SeriesAdmin (6.1 regression)
def test_ac6_seometa_inline_still_on_seriesadmin():
    from apps.brands.models import Series
    from apps.seo.admin import SeoMetaInline

    inlines = list(admin.site._registry[Series].inlines)
    assert any(ic is SeoMetaInline or issubclass(ic, SeoMetaInline) for ic in inlines), (
        "SeoMetaInline MORA ostati na samostalnom SeriesAdmin (6.1 regression — SM-D6/AC6)."
    )


# AC-6 — standalone Series changelist + change render 200 (no NoReverseMatch)
def test_ac6_series_changelist_and_change_200(client, superuser):
    from apps.brands.tests.factories import SeriesFactory

    series = SeriesFactory.create()
    client.force_login(superuser)
    cl = client.get(reverse("admin:brands_series_changelist"))
    assert cl.status_code == 200, f"Series changelist MORA biti 200; dobio {cl.status_code}."
    ch = client.get(reverse("admin:brands_series_change", args=[series.pk]))
    assert ch.status_code == 200, (
        f"Series change-view MORA biti 200 (NE pada na series_detail NoReverseMatch — G-3); "
        f"dobio {ch.status_code}."
    )


# ══════════════════════════════════════════════════════════════════════════════
# AC7 — name_sr je BEZUSLOVNO obavezan (model name blank=False + sr default lang);
# prazan name_sr → graceful FORM greška (HTTP 200), NIKAD 400/500; is_coming_soon je
# NEZAVISAN flag i NE relaksira obavezan naziv. (M1 fix — ispravlja pogrešnu step-02
# C2 pretpostavku o "draft sa praznim name_sr".) Testovi vrte REALAN admin POST.
# ══════════════════════════════════════════════════════════════════════════════
def _add_form_payload(client, extra=None):
    """Scrape the Brand add-view (multi-inline + per-locale management forms) → POST dict.
    `extra` overrides/adds fields on top of the scraped baseline.

    NOTE: `slug` is a REQUIRED admin form field (model `slug` blank=False); in a real
    browser `prepopulated_fields={"slug":("name",)}` JS fills it from name. The no-JS test
    scraper leaves it empty, so callers that expect a SUCCESSFUL save MUST pass `slug` in
    `extra` (mirrors browser prepopulate). Callers testing graceful rejection leave it empty."""
    url = reverse("admin:brands_brand_add")
    data = _scrape_change_form(client.get(url).content.decode())
    data.setdefault("statistics", "[]")
    if extra:
        data.update(extra)
    return url, data


def _admin_form_field_required(name):
    """Required-flag of a field on the ADMIN-built BrandForm (TranslationAdmin promotes
    the default-locale `name_sr` to required when base `name` is blank=False — that promotion
    lives on the admin form, NOT the raw BrandAdminForm which still carries base `name`)."""
    from django.test import RequestFactory

    model_admin = _brand_admin()
    req = RequestFactory().get("/")
    form_cls = model_admin.get_form(req)
    return form_cls.base_fields[name].required


# AC-7 (graceful draft attempt) — is_coming_soon=True + empty name_sr → 200 form-error, NO new row
def test_ac7_empty_name_sr_coming_soon_graceful_form_error(client, superuser):
    from apps.brands.models import Brand

    before = Brand.objects.count()
    client.force_login(superuser)
    url, data = _add_form_payload(
        client, extra={"name_sr": "", "is_coming_soon": "on"}
    )
    resp = client.post(url, data)
    # MORA biti graceful: re-render add forme (200) sa field greškom — NIKAD 400/500.
    assert resp.status_code == 200, (
        f"is_coming_soon=True + prazan name_sr MORA dati graceful 200 form-error "
        f"(name_sr bezuslovno obavezan — model name blank=False; NIKAD 400/500 iz model "
        f"full_clean escape-a — AC7/M1); dobio {resp.status_code}."
    )
    form = resp.context["adminform"].form
    assert "name_sr" in form.errors, (
        f"Prazan name_sr MORA dati field grešku na `name_sr` (required, NE publish-gate); "
        f"dobio {form.errors!r}."
    )
    assert Brand.objects.count() == before, (
        "Nijedan NOV Brand red NE SME biti kreiran kad je name_sr prazan (graceful odbijanje — AC7/M1)."
    )


# AC-7 (graceful) — is_coming_soon=False + empty name_sr → isto: 200 form-error, NO new row
def test_ac7_empty_name_sr_published_graceful_form_error(client, superuser):
    from apps.brands.models import Brand

    before = Brand.objects.count()
    client.force_login(superuser)
    url, data = _add_form_payload(
        client, extra={"name_sr": "", "is_coming_soon": ""}  # unchecked → False
    )
    resp = client.post(url, data)
    assert resp.status_code == 200, (
        f"is_coming_soon=False + prazan name_sr MORA dati graceful 200 form-error "
        f"(name_sr bezuslovno obavezan; is_coming_soon je nezavisan flag — AC7/M1); "
        f"dobio {resp.status_code}."
    )
    form = resp.context["adminform"].form
    assert "name_sr" in form.errors, (
        f"Prazan name_sr MORA dati field grešku na `name_sr`; dobio {form.errors!r}."
    )
    assert Brand.objects.count() == before, (
        "Nijedan NOV Brand red NE SME biti kreiran kad je name_sr prazan (AC7/M1)."
    )


# AC-7 (positive) — valid name_sr (+ slug, mirroring browser prepopulate) → 302 redirect, Brand created
def test_ac7_valid_name_sr_creates_brand(client, superuser):
    from apps.brands.models import Brand

    client.force_login(superuser)
    url, data = _add_form_payload(
        client,
        extra={
            "name_sr": "Objavljen Brend",
            "slug": "objavljen-brend",  # prepopulated_fields JS-equivalent (no-JS scraper)
            "is_coming_soon": "",
        },
    )
    resp = client.post(url, data)
    assert resp.status_code == 302, (
        f"Validan name_sr (+ slug) MORA sačuvati Brand i dati 302 redirect na changelist (AC7); "
        f"dobio {resp.status_code}."
    )
    assert Brand.objects.filter(name_sr="Objavljen Brend").exists(), (
        "Validan Brand sa name_sr MORA biti kreiran (AC7)."
    )


# AC-7 — name_sr je obavezan na ADMIN form nivou (model name blank=False; required-promotion NE relaksiran — M1)
def test_ac7_name_sr_field_is_required_on_admin_form():
    assert _admin_form_field_required("name_sr") is True, (
        "name_sr MORA biti obavezno na admin BrandForm-u (model `name` blank=False + sr default "
        "lang → TranslationAdmin required-promotion); promotion se NE relaksira (M1 — sprečava "
        "model full_clean escape u 400/500)."
    )


# AC-7 — is_coming_soon je NEZAVISAN flag: ne menja obaveznost name_sr (oba smera blokirana gore)
def test_ac7_is_coming_soon_does_not_relax_name_requirement(client, superuser):
    from apps.brands.models import Brand

    before = Brand.objects.count()
    client.force_login(superuser)
    for soon in ("on", ""):  # draft (True) i published (False) — oba prazna name_sr
        url, data = _add_form_payload(client, extra={"name_sr": "", "is_coming_soon": soon})
        resp = client.post(url, data)
        assert resp.status_code == 200 and "name_sr" in resp.context["adminform"].form.errors, (
            f"is_coming_soon={soon!r} NE relaksira obavezan name_sr (M1 — nezavisan flag); "
            f"status={resp.status_code}, errors={resp.context['adminform'].form.errors!r}."
        )
    assert Brand.objects.count() == before, "Nijedan nov Brand pri praznom name_sr (M1)."


# ══════════════════════════════════════════════════════════════════════════════
# AC8 / AC9 — list_display / list_filter / has_pdf / search
# ══════════════════════════════════════════════════════════════════════════════
# AC-8
def test_ac8_list_display_and_filter_have_is_coming_soon():
    model_admin = _brand_admin()
    assert "is_coming_soon" in tuple(model_admin.list_display), (
        "list_display MORA sadržati is_coming_soon (status boolean — AC8)."
    )
    assert "is_coming_soon" in tuple(model_admin.list_filter), (
        "list_filter MORA sadržati is_coming_soon (AC8)."
    )
    assert "name" in tuple(model_admin.list_display), (
        "list_display MORA sadržati name (AC9)."
    )
    assert "slug" in tuple(model_admin.list_display), (
        "list_display MORA sadržati slug (AC9 lista ga kao obavezan)."
    )
    assert "brand_color" in tuple(model_admin.list_display), (
        "list_display MORA sadržati brand_color (AC9)."
    )


# AC-9 — has_pdf boolean indicator True/False
def test_ac9_has_pdf_indicator():
    from apps.brands.tests.factories import BrandFactory

    model_admin = _brand_admin()
    assert "has_pdf" in tuple(model_admin.list_display), (
        "list_display MORA sadržati has_pdf boolean indikator (AC9 preporuka)."
    )
    with_pdf = BrandFactory.create_with_catalog_pdf(name="Sa PDF-om")
    without_pdf = BrandFactory.create(name="Bez PDF-a")
    assert model_admin.has_pdf(with_pdf) is True, "has_pdf MORA biti True kad catalog_pdf postoji (AC9)."
    assert model_admin.has_pdf(without_pdf) is False, "has_pdf MORA biti False kad nema catalog_pdf (AC9)."


# AC-9 — has_pdf decorated as boolean display
def test_ac9_has_pdf_is_boolean_display():
    model_admin = _brand_admin()
    assert getattr(model_admin.has_pdf, "boolean", False) is True, (
        "has_pdf MORA biti @admin.display(boolean=True) (boolean ikona — AC9)."
    )


# AC-9 — changelist search by name_sr does NOT raise FieldError (real column)
def test_ac9_changelist_search_no_field_error(client, superuser):
    from apps.brands.tests.factories import BrandFactory

    BrandFactory.create(name="Tražni Brend")
    client.force_login(superuser)
    resp = client.get(reverse("admin:brands_brand_changelist"), {"q": "Tražni"})
    assert resp.status_code == 200, (
        f"Changelist search (q=) MORA biti 200 — search_fields=('name_sr',) NE sme baciti "
        f"FieldError (G-1/AC9); dobio {resp.status_code}."
    )


# ══════════════════════════════════════════════════════════════════════════════
# AC10 / AC11 — RBAC + no migrations
# ══════════════════════════════════════════════════════════════════════════════
# AC-10 (negative) — anonymous → redirect to admin login
def test_ac10_anonymous_redirected_to_login(client):
    resp = client.get(reverse("admin:brands_brand_changelist"))
    assert resp.status_code == 302, (
        f"Anoniman na Brand changelist MORA biti 302 (admin login redirect — AC10); "
        f"dobio {resp.status_code}."
    )
    # login URL is reverse-derived, NEVER hardcoded
    assert reverse("admin:login") in resp["Location"], (
        f"302 MORA voditi na admin:login (NE hardkodovan put — admin je na bare /admin-coric/ "
        f"iz 8.1); Location={resp['Location']!r}."
    )


# AC-10 — Editor changelist 200
def test_ac10_editor_changelist_200(client, editor):
    client.force_login(editor)
    resp = client.get(reverse("admin:brands_brand_changelist"))
    assert resp.status_code == 200, (
        f"Editor Brand changelist MORA biti 200 (8.2 grant netaknut — AC10/SM-D7); "
        f"dobio {resp.status_code}."
    )


# AC-10 — Editor can POST-save a valid Brand through add-view
def test_ac10_editor_can_add_brand(client, editor):
    from apps.brands.models import Brand

    client.force_login(editor)
    url = reverse("admin:brands_brand_add")
    data = _scrape_change_form(client.get(url).content.decode())
    data["name_sr"] = "Editorov Brend"
    data["slug"] = "editorov-brend"  # required field; prepopulated_fields JS-equivalent (no-JS scraper)
    data["is_coming_soon"] = "on"
    data.setdefault("statistics", "[]")
    resp = client.post(url, data, follow=True)
    assert resp.status_code == 200, f"Editor add POST MORA biti 200; dobio {resp.status_code}."
    assert Brand.objects.filter(name_sr="Editorov Brend").exists(), (
        "Editor MORA moći da sačuva validan Brend kroz admin (AC10)."
    )


# AC-11 — makemigrations brands --check = No changes (0 schema)
def test_ac11_no_pending_migration_for_brands():
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
    assert "brands" not in changes, (
        f"apps.brands NE SME imati pending schema migraciju (8.4 je admin-only — AC11); "
        f"autodetector predlaže: {changes.get('brands')}."
    )


# AC-11 — CategoryAdmin / SubcategoryAdmin untouched (8.5 scope, SM-D1)
def test_ac11_category_subcategory_admin_untouched():
    from apps.brands.models import Category, Subcategory
    from apps.seo.admin import SeoMetaInline

    for model in (Category, Subcategory):
        inlines = list(admin.site._registry[model].inlines)
        assert any(ic is SeoMetaInline or issubclass(ic, SeoMetaInline) for ic in inlines), (
            f"{model.__name__}Admin MORA zadržati SeoMetaInline netaknut (8.5 scope — SM-D1/AC11)."
        )


# ──────────────────────────────────────────────────────────────────────────────
# change-form scraper (mirror apps/seo/tests/test_seometa_admin_inline.py) — re-submits
# existing rendered values so the multi-inline + per-locale payload stays valid.
# ──────────────────────────────────────────────────────────────────────────────
def _scrape_change_form(html):
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
