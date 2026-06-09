"""Story 8.7 — Blog CRUD Admin sa WYSIWYG (TEA RED phase).

DEFINES the contract Dev (GREEN) must satisfy. Maps to the 12 ACs + SM-decisions +
gotchas of `8-7-blog-crud-admin-sa-wysiwyg.md`. Canonical contract:
`8-7-blog-crud-admin-sa-wysiwyg-interface-contract.md`.

RUN (MUST go through Docker — libmagic/python-magic + Pillow + nh3 are NOT on the
Windows host):
    just test apps/blog/tests/test_8_7_blog_crud_admin.py -v

RED expectation: `apps/blog/admin.py` is still the minimal 5.1 STUB
(`PostAdmin(SeoWarningAdminMixin, TranslationAdmin)` with `inlines=[SeoMetaInline]`,
`view_on_site=False`, NO `PostAdminForm`, NO `MAX_IMAGE_UPLOAD_SIZE`, NO publish-gate,
NO `filter_horizontal`) and `templates/blog/post_detail.html:45` still renders
`{{ post.body|linebreaks }}`. So every NEW-capability test MUST fail/error.

GREEN-TODAY tests (≈22 pass against the stub). TWO categories — both legitimate, NOT
false-greens:
  (1) INVARIANT-LOCK — pin an EXISTING contract that 8.7 must NOT regress (the 5 the
      story names + the regression smokes that already pass):
      - `test_ac1_postadmin_is_translationadmin` — 5.1 stub already is TranslationAdmin.
      - `test_ac1_search_fields_uses_title_sr` — 5.1 stub already uses ("title_sr",).
      - `test_ac2_body_stays_plain_textfield` — model unchanged (AC11 schema lock).
      - `test_ac8_seometa_inline_still_on_postadmin` — 6.1 already has it.
      - `test_ac8_seowarning_mixin_in_mro` — 5.1 already subclasses it.
      - `test_ac8_draft_view_on_site_404_not_500` — 5-3 blog:detail draft→404 boundary.
      - `test_ac9_title_sr_required_on_admin_form` / `_empty_*` / `_whitespace_*` —
        modeltranslation already promotes title_sr to required (NE relaksiraj lock).
      - `test_ac10_editor_can_access_blog_post_changelist` — 8.2 already granted it.
      - `test_ac10_anonymous_redirected_to_login` / `_admin_post_without_csrf_forbidden`
        — admin auth/CSRF baseline.
      - `test_ac11_no_pending_migration_for_blog` — admin-only, 0 migration lock.
      - `test_ac12_legal_html_filter_regression_intact` — 7-5 sanitizer untouched.
  (2) SMOKE that already renders 200 on the stub and must STAY 200 after upgrade:
      - `test_ac1_changelist_search_no_field_error`, `test_ac1_post_add_view_200_superuser`,
        `test_ac1_change_view_renders_per_locale_fields`, `test_ac1_admin_system_checks_clean`,
        `test_ac5_draft_save_with_no_content_passes` (gate-doesn't-fire boundary),
        `test_ac7_tag_and_category_changelist_and_add_200`,
        `test_ac8_post_add_view_renders_inline_200`, `test_ac12_post_changelist_200_superuser`.
None assert a NEW capability while green — every NEW-capability assertion (PostAdminForm,
constants, filter_horizontal, WYSIWYG widget, publish-gate persistence, sanitized render,
view_on_site re-enable) is currently RED.

────────────────────────────────────────────────────────────────────────────────
COLLECTION-SAFETY: all `apps.blog.admin` / `PostAdminForm` imports are INSIDE test
bodies (lazy) so a missing symbol fails that test individually (true RED), never aborts
collection of the whole file.

AUTH: authenticate with `force_login` (NEVER `client.login` — django-axes from 8.1
pollutes lockout state through authenticate(); established project lesson).

ADMIN URL: always `reverse("admin:blog_post_*")` — admin is at bare /admin-coric/ (8.1),
never hardcode.

XSS ASSERT (G-18/SM-D7): scope to the rendered `coric-blog-detail__body` fragment +
test STRIP (`"<script" not in body`) NOT escape (`"&lt;script&gt;" not in body`);
NEVER `"alert(1) not in html"` (7-5 lesson — a correct GREEN render keeps inner text).

Refs: 8-7-...md (AC1-AC12, SM-D1..D12, G-1..G-19) + interface contract +
apps/products/tests/test_8_6_product_crud_admin.py (closest precedent) +
apps/core/tests/test_legal_html.py (sanitizer precedent) + apps/blog/tests/conftest.py
(make_post/make_category/make_tag + superuser/author_user fixtures).
"""

from __future__ import annotations

import io

import pytest
from django.contrib import admin
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

pytestmark = pytest.mark.django_db


# ──────────────────────────────────────────────────────────────────────────────
# Users + upload fixtures  (conftest.py provides superuser / author_user / make_*)
# ──────────────────────────────────────────────────────────────────────────────
@pytest.fixture
def editor(django_user_model):
    """Editor = is_staff + member of the `Editor` group (8.2 post_migrate created it;
    group already carries blog post/category/tag CRUD via EDITOR_CONTENT_MODELS — SM-D11)."""
    from django.contrib.auth.models import Group

    user = django_user_model.objects.create_user(
        username="blog_editor_tea",
        email="blog-editor@example.com",
        password="tea-pass-12345",
        is_staff=True,
        is_superuser=False,
    )
    user.groups.add(Group.objects.get(name="Editor"))
    return user


def _pillow_upload(fmt, content_type, filename):
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (10, 10), color=(34, 64, 47)).save(buf, format=fmt)
    buf.seek(0)
    return SimpleUploadedFile(filename, buf.read(), content_type=content_type)


@pytest.fixture
def valid_jpeg():
    return _pillow_upload("JPEG", "image/jpeg", "glavna.jpg")


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
def oversized_image():
    """Valid small JPEG with forced .size > 5 MB (forces the size-cap branch)."""
    up = _pillow_upload("JPEG", "image/jpeg", "velika.jpg")
    up.size = 6 * 1024 * 1024
    return up


@pytest.fixture
def decompression_bomb_png():
    """8000×8000 (64M px) solid-color PNG — declares pixel dimensions > Image.MAX_IMAGE_PIXELS
    (50M) but is only ~30KB on disk (well under MAX_IMAGE_UPLOAD_SIZE).

    Locks the M2/G-10 decompression-bomb guard: the size cap does NOT early-out (small on
    disk), so the bomb MUST be caught by validate_image_mime's DecompressionBombWarning→error
    escalation (NOT a numeric assert on the 50M constant). Mirror 8.6 fixture."""
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (8000, 8000), color="white").save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return SimpleUploadedFile("bomba.png", buf.read(), content_type="image/png")


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────
def _post_admin():
    from apps.blog.models import Post

    return admin.site._registry[Post]


def _category_admin():
    from apps.blog.models import Category

    return admin.site._registry[Category]


def _tag_admin():
    from apps.blog.models import Tag

    return admin.site._registry[Tag]


def _make_post_form(data=None, files=None, instance=None):
    """Bind PostAdminForm (lazy import — collection-safe)."""
    from apps.blog.admin import PostAdminForm

    return PostAdminForm(data=data or {}, files=files, instance=instance)


def _field_errors_text(form, field):
    return " ".join(str(e) for e in form.errors.get(field, []))


def _scrape_change_form(html):
    """name->value for all input/select/textarea fields in an admin change form.
    Re-submits existing rendered values so the per-locale payload stays valid
    (mirror apps/products/tests + apps/seo/tests scrapers)."""
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
        opts = re.findall(r'<option[^>]*value="([^"]*)"[^>]*selected', sm.group(2))
        # multi-select (filter_horizontal tags) → list; single → scalar
        if len(opts) > 1:
            data[name] = opts
        else:
            data[name] = opts[0] if opts else ""
    for tm in re.finditer(r'<textarea[^>]*name="([^"]+)"[^>]*>(.*?)</textarea>', html, re.S):
        data[tm.group(1)] = tm.group(2)
    return data


def _seo_inline_mgmt(data):
    """Provide an empty SeoMeta GFK inline management form so the admin POST is valid."""
    prefix = "seo-seometa-content_type-object_id"
    data.setdefault(f"{prefix}-TOTAL_FORMS", "0")
    data.setdefault(f"{prefix}-INITIAL_FORMS", "0")
    data.setdefault(f"{prefix}-MIN_NUM_FORMS", "0")
    data.setdefault(f"{prefix}-MAX_NUM_FORMS", "1")
    return data


def _body_fragment(html, css_class="coric-blog-detail__body"):
    """Extract ONLY the sanitized body region from a full page (7-5 G-18 pattern).

    Asserting `<script` absence over the WHOLE page is unsatisfiable — base.html chrome
    legitimately renders `<script src=...>`/`<img>`/`<div>`. Scope to the body div."""
    marker = f'class="{css_class}"'
    start = html.find(marker)
    assert start != -1, f"Body region {css_class!r} MORA postojati u renderu (AC3)."
    end = html.find("</article>", start)
    return html[start : end if end != -1 else len(html)]


# ══════════════════════════════════════════════════════════════════════════════
# AC1 — TranslationAdmin multi-locale za Post / Category / Tag
# ══════════════════════════════════════════════════════════════════════════════
# AC-1: PostAdmin/CategoryAdmin/TagAdmin su TranslationAdmin instance (multi-locale tabovi)
# (INVARIANT-LOCK — Post/Category/Tag already TranslationAdmin in the 5.1 stub)
def test_ac1_postadmin_is_translationadmin():
    from modeltranslation.admin import TranslationAdmin

    for model_admin in (_post_admin(), _category_admin(), _tag_admin()):
        assert isinstance(model_admin, TranslationAdmin), (
            f"{type(model_admin).__name__} MORA biti TranslationAdmin instanca "
            f"(modeltranslation auto sr/hu/en tabovi — AC1)."
        )


# AC-1: search_fields realna kolona title_sr (Post) / name_sr (Category/Tag) — NE virtuelni (G-1)
# (INVARIANT-LOCK — 5.1 stub already uses sr-suffixed columns)
def test_ac1_search_fields_uses_title_sr():
    assert tuple(_post_admin().search_fields) == ("title_sr",), (
        "PostAdmin.search_fields MORA biti ('title_sr',) — realna DB kolona, NE virtuelni "
        f"`title` (FieldError na changelist search — G-1); dobio {_post_admin().search_fields!r}."
    )
    assert tuple(_category_admin().search_fields) == ("name_sr",), (
        "CategoryAdmin.search_fields MORA biti ('name_sr',) — realna kolona (G-1)."
    )
    assert tuple(_tag_admin().search_fields) == ("name_sr",), (
        "TagAdmin.search_fields MORA biti ('name_sr',) — realna kolona (G-1)."
    )


# AC-1: changelist search by title_sr does NOT raise FieldError (real column — G-1)
def test_ac1_changelist_search_no_field_error(client, superuser, make_post, author_user):
    make_post(author=author_user)
    client.force_login(superuser)
    resp = client.get(reverse("admin:blog_post_changelist"), {"q": "Žetva"})
    assert resp.status_code == 200, (
        f"Changelist search (q=) MORA biti 200 — search_fields=('title_sr',) NE sme baciti "
        f"FieldError (G-1/AC1); dobio {resp.status_code}."
    )


# AC-1: superuser Post add-view 200 (TranslationAdmin + SeoMetaInline + WYSIWYG render-smoke)
def test_ac1_post_add_view_200_superuser(client, superuser):
    client.force_login(superuser)
    resp = client.get(reverse("admin:blog_post_add"))
    assert resp.status_code == 200, (
        f"Superuser Post add-view MORA biti 200 (TranslationAdmin + SeoMetaInline + WYSIWYG "
        f"widget ne smeju baciti admin.E*/JS-crash render fail — AC1/AC2); dobio {resp.status_code}."
    )


# AC-1: change-view renders per-locale fields for title/perex/body (render-smoke)
def test_ac1_change_view_renders_per_locale_fields(client, superuser, make_post, author_user):
    post = make_post(author=author_user)
    client.force_login(superuser)
    html = client.get(reverse("admin:blog_post_change", args=[post.pk])).content.decode()
    for fld in ("title_sr", "title_hu", "title_en", "body_sr", "body_hu", "body_en"):
        assert f'name="{fld}"' in html, (
            f"Change-view MORA renderovati per-locale polje '{fld}' (render-smoke — AC1/AC2)."
        )


# AC-1/AC12: admin system checks clean (TranslationAdmin + filter_horizontal + WYSIWYG → 0 admin.E*)
def test_ac1_admin_system_checks_clean():
    from django.core.checks import run_checks

    errors = [e for e in run_checks() if e.is_serious()]
    assert errors == [], (
        f"manage.py check MORA biti čist — TranslationAdmin + SeoMetaInline + filter_horizontal "
        f"+ prepopulated_fields/search_fields + WYSIWYG widget ne smeju baciti admin.E* "
        f"(AC1/AC12/G-1). Greške: {errors}."
    )


# ══════════════════════════════════════════════════════════════════════════════
# AC2 — WYSIWYG editor za Post.body (form-widget, NE model promena; SM-D2)
# ══════════════════════════════════════════════════════════════════════════════
# AC-2: PostAdminForm exists and is wired to PostAdmin
def test_ac2_postadmin_uses_postadminform():
    from apps.blog.admin import PostAdminForm

    assert _post_admin().form is PostAdminForm, (
        "PostAdmin.form MORA biti PostAdminForm (upload double-check + WYSIWYG wiring — AC2/AC4)."
    )


# AC-2: each body_<locale> textarea gets a non-default rich-text widget (enhancement over plain)
def test_ac2_body_fields_get_wysiwyg_widget():
    from django.contrib.auth.models import AnonymousUser
    from django.test import RequestFactory

    model_admin = _post_admin()
    req = RequestFactory().get("/")
    req.user = AnonymousUser()
    form_cls = model_admin.get_form(req)
    for fld in ("body_sr", "body_hu", "body_en"):
        assert fld in form_cls.base_fields, (
            f"Admin form MORA imati per-locale polje '{fld}' (AC2)."
        )
    # WYSIWYG = enhancement: EVERY body_<locale> widget MUST carry a marker that distinguishes
    # it from a bare admin Textarea — either a custom widget class OR a CSS class / data-attr hook
    # used by the static/js editor (SM-D2 progressive enhancement). A plain default
    # AdminTextareaWidget with no marker means no editor was wired. The impl wires ALL THREE
    # locales via the _WYSIWYG_BODY_FIELDS loop — assert it on each (not just body_sr).
    for fld in ("body_sr", "body_hu", "body_en"):
        widget = form_cls.base_fields[fld].widget
        attrs_class = (widget.attrs or {}).get("class", "")
        is_custom_widget = type(widget).__name__ not in ("AdminTextareaWidget", "Textarea")
        has_editor_hook = "wysiwyg" in attrs_class.lower() or "rich" in attrs_class.lower() or any(
            "wysiwyg" in str(k).lower() or "rich" in str(k).lower() for k in (widget.attrs or {})
        )
        assert is_custom_widget or has_editor_hook, (
            f"{fld} widget MORA biti WYSIWYG enhancement (custom widget klasa ILI editor "
            "CSS/data hook na Textarea — SM-D2 progressive enhancement); dobio plain "
            f"{type(widget).__name__} bez marker-a (attrs={widget.attrs!r})."
        )


# AC-2: body stays a plain TextField on the model (0 schema change — SM-D2/AC11)
def test_ac2_body_stays_plain_textfield():
    from django.db import models as dj_models

    from apps.blog.models import Post

    field = Post._meta.get_field("body")
    assert isinstance(field, dj_models.TextField), (
        "Post.body MORA ostati plain TextField — WYSIWYG je FORM-widget, NE model promena "
        f"(SM-D2/AC11); dobio {type(field).__name__}."
    )


# ══════════════════════════════════════════════════════════════════════════════
# AC3 (SECURITY — STORED-XSS GRANICA) — render-time nh3 sanitizacija Post.body
# ══════════════════════════════════════════════════════════════════════════════
# AC-3: post_detail.html no longer uses |linebreaks on body (double-escape bug — G-3)
def test_ac3_post_detail_no_longer_uses_linebreaks_on_body():
    from pathlib import Path

    from django.conf import settings

    tpl = (
        Path(settings.BASE_DIR) / "templates" / "blog" / "post_detail.html"
    ).read_text(encoding="utf-8")
    assert "post.body|linebreaks" not in tpl and "post.body | linebreaks" not in tpl, (
        "templates/blog/post_detail.html NE SME više renderovati `post.body|linebreaks` "
        "(ESCAPE-uje rich HTML → double-escape; mora kroz nh3 sanitizovan filter — AC3/G-3)."
    )


# AC-3: body rendered through the nh3 sanitizer filter (legal_html OR rich_html alias)
def test_ac3_post_detail_uses_sanitized_filter_on_body():
    from pathlib import Path

    from django.conf import settings

    tpl = (
        Path(settings.BASE_DIR) / "templates" / "blog" / "post_detail.html"
    ).read_text(encoding="utf-8").replace(" ", "")
    assert "post.body|legal_html" in tpl or "post.body|rich_html" in tpl, (
        "post_detail.html MORA renderovati body kroz nh3 sanitizovan filter "
        "(`{{ post.body|legal_html }}` ILI `{{ post.body|rich_html }}` alias — AC3/SM-D9). "
        "NIKAD sirovi |safe bez sanitizacije."
    )
    assert "post.body|safe" not in tpl, (
        "post.body NIKAD ne sme kroz sirovi `|safe` bez prethodne nh3 sanitizacije "
        "(stored-XSS — AC3/G-3)."
    )


def _published_post_with_body(make_post, make_category, author_user, body_sr):
    from django.utils import timezone

    cat = make_category()
    return make_post(
        author=author_user,
        category=cat,
        status="published",
        published_at=timezone.now(),
        body_sr=body_sr,
    )


# AC-3 (security): <script> in body STRIPPED on render (scope to body fragment — G-18/SM-D7)
def test_ac3_script_payload_stripped_in_rendered_body(
    client, make_post, make_category, author_user
):
    post = _published_post_with_body(
        make_post, make_category, author_user,
        "<p>Bezbedan tekst.</p><script>alert(1)</script>",
    )
    html = client.get(post.get_absolute_url(), HTTP_HOST="localhost").content.decode()
    body = _body_fragment(html)
    assert "<p>Bezbedan tekst.</p>" in body, "Dozvoljen <p> MORA proći sanitizaciju (AC3)."
    assert "<script" not in body, "`<script` MORA biti STRIP-ovan iz body fragmenta (AC3/SM-D7)."
    assert "&lt;script&gt;" not in body, (
        "nh3 STRIPUJE node (NE escape) — `&lt;script&gt;` NE SME postojati (G-4/SM-D7)."
    )


# AC-3 (security): <img onerror>, javascript: href, onclick, <iframe> all neutralized in body
def test_ac3_adversarial_vectors_stripped_in_rendered_body(
    client, make_post, make_category, author_user
):
    payload = (
        '<img src=x onerror="alert(1)">'
        '<a href="javascript:alert(1)" onclick="x()">klik</a>'
        "<iframe src='https://evil.test'></iframe>"
        "<p>kraj</p>"
    )
    post = _published_post_with_body(make_post, make_category, author_user, payload)
    html = client.get(post.get_absolute_url(), HTTP_HOST="localhost").content.decode()
    body = _body_fragment(html)
    assert "<img" not in body, "<img onerror> (van allowlist-a) MORA biti STRIP-ovan (AC3)."
    assert "onerror" not in body, "`onerror` handler MORA biti STRIP-ovan (AC3)."
    assert "onclick" not in body, "`onclick` handler na <a> MORA biti STRIP-ovan (AC3)."
    assert "javascript:" not in body, "`javascript:` scheme MORA biti STRIP-ovan (AC3)."
    assert "<iframe" not in body, "<iframe> MORA biti STRIP-ovan iz body-a (AC3/SM-D9)."
    assert "<p>kraj</p>" in body, "Dozvoljen sadržaj posle payload-a MORA proći (AC3)."


# AC-3: allowed rich structure (h2/ul/li/strong/a) survives + <a> gets forced rel (G-7)
def test_ac3_allowed_rich_structure_survives_with_forced_rel(
    client, make_post, make_category, author_user
):
    body = (
        "<h2>Naslov</h2><ul><li>stavka</li></ul><strong>jako</strong>"
        '<p>Vidi <a href="https://x.test">link</a>.</p>'
    )
    post = _published_post_with_body(make_post, make_category, author_user, body)
    html = client.get(post.get_absolute_url(), HTTP_HOST="localhost").content.decode()
    frag = _body_fragment(html)
    for tag in ("<h2", "<ul", "<li", "<strong", "<a "):
        assert tag in frag, f"Dozvoljena struktura {tag!r} MORA preživeti sanitizaciju (AC3)."
    assert 'rel="noopener noreferrer"' in frag, (
        'Emitovani <a> MORA imati forsiran rel="noopener noreferrer" (AC3/G-7).'
    )


# ══════════════════════════════════════════════════════════════════════════════
# AC4 (SECURITY) — main_image upload MIME + decompression-bomb guard (REUSE media_pipeline)
# ══════════════════════════════════════════════════════════════════════════════
# AC-4: upload size constant + image MIME allowlist defined (5 MB, no SVG — mirror 8.6)
def test_ac4_upload_constants_defined():
    from apps.blog import admin as blog_admin

    assert blog_admin.MAX_IMAGE_UPLOAD_SIZE == 5 * 1024 * 1024, (
        "MAX_IMAGE_UPLOAD_SIZE MORA biti 5 MB (EKSPLICITAN override 10MB media_pipeline "
        "default — AC4)."
    )
    assert tuple(blog_admin.ALLOWED_IMAGE_MIME_TYPES) == (
        "image/jpeg",
        "image/png",
        "image/webp",
    ), "ALLOWED_IMAGE_MIME_TYPES MORA biti (jpeg, png, webp) — SVG izostavljen (XSS; AC4)."


# AC-4: PostAdminForm.clean_main_image exists (upload double-check entrypoint)
def test_ac4_form_has_clean_main_image():
    from apps.blog.admin import PostAdminForm

    assert hasattr(PostAdminForm, "clean_main_image"), (
        "PostAdminForm MORA imati clean_main_image (upload double-check — AC4/G-13)."
    )


# AC-4: main_image overridden to plain FileField (Pillow to_python() would eat srpska poruka — G-9)
def test_ac4_main_image_is_filefield_override():
    from django import forms

    from apps.blog.admin import PostAdminForm

    field = PostAdminForm.base_fields["main_image"]
    assert isinstance(field, forms.FileField) and not isinstance(field, forms.ImageField), (
        "main_image MORA biti override-ovan u plain forms.FileField (NE ImageField — Pillow "
        f"to_python() pregazi srpsku media_pipeline poruku; G-9/G-14); dobio {type(field).__name__}."
    )


# AC-4 (security): fake-extension image rejected with canonical media_pipeline message
def test_ac4_clean_main_image_rejects_fake_image(fake_image_txt):
    form = _make_post_form(
        data={"title_sr": "Naslov"}, files={"main_image": fake_image_txt}
    )
    assert not form.is_valid(), "Lažna slika (.jpg ali tekst) MORA biti odbijena (MIME — AC4)."
    assert "Nedozvoljen tip slike" in _field_errors_text(form, "main_image"), (
        f"Greška MORA sadržati 'Nedozvoljen tip slike' na `main_image` (validate_image_mime "
        f"kanonska poruka — G-10); dobio {form.errors!r}."
    )


# AC-4 (security): corrupt image (valid magic header, fails Pillow verify) rejected
def test_ac4_clean_main_image_rejects_corrupt_image(corrupt_jpeg):
    form = _make_post_form(
        data={"title_sr": "Naslov"}, files={"main_image": corrupt_jpeg}
    )
    assert not form.is_valid(), "Korumpiran JPEG MORA biti odbijen (Pillow verify — AC4)."
    assert "Slika je oštećena ili nije validan format" in _field_errors_text(form, "main_image"), (
        f"Korumpiran JPEG MORA dati kanonsku 'Slika je oštećena ili nije validan format.' "
        f"poruku na `main_image` (NE goli OSError/500 — G-14); dobio {form.errors!r}."
    )


# AC-4 (security): 64M-px decompression bomb (~30KB on disk) rejected by bomb guard (M2/G-10)
def test_ac4_clean_main_image_rejects_decompression_bomb(decompression_bomb_png):
    form = _make_post_form(
        data={"title_sr": "Naslov"}, files={"main_image": decompression_bomb_png}
    )
    assert not form.is_valid(), (
        "Decompression-bomb slika (64M px, mala na disku) MORA biti odbijena "
        "(validate_image_mime MAX_IMAGE_PIXELS=50M guard — G-10)."
    )
    assert "Slika je oštećena ili nije validan format" in _field_errors_text(form, "main_image"), (
        f"Bomba MORA dati kanonsku validate_image_mime poruku na `main_image`; dobio {form.errors!r}."
    )


# AC-4 (edge): oversized image rejected (> MAX_IMAGE_UPLOAD_SIZE)
def test_ac4_clean_main_image_rejects_oversized(oversized_image):
    form = _make_post_form(
        data={"title_sr": "Naslov"}, files={"main_image": oversized_image}
    )
    assert not form.is_valid(), "main_image > MAX_IMAGE_UPLOAD_SIZE MORA biti odbijen (AC4)."
    assert "main_image" in form.errors


# AC-4 (edge / HARD RULE): blank main_image skips gracefully (blank=True → draft sme bez slike)
def test_ac4_blank_main_image_skips_gracefully():
    # `slug` je `SluggedModel.SlugField(unique=True)` — NIJE blank → required form-polje koje
    # _relax_* helperi NE relaksiraju (nema `_sr` twin, nema model default). Direct-bind
    # ModelForm-u MORA se proslediti `slug` da `is_valid()` ne padne iz POGREŠNOG razloga
    # (missing slug) i tako lažno potvrdi/obori upload graceful-skip (mirror 8.6
    # test_ac3_clean_main_image_accepts_valid_image koji EKSPLICITNO šalje slug).
    form = _make_post_form(
        data={"title_sr": "Nacrt Bez Slike", "slug": "nacrt-bez-slike", "status": "draft"},
        files={},
    )
    assert form.is_valid(), (
        f"Prazan main_image (blank=True) MORA proći bez greške (graceful skip — AC4 HARD "
        f"RULE; NE bezuslovni validate_image_mime koji RAISE-uje na praznom); errors={form.errors!r}."
    )


# AC-4 (positive): valid JPEG accepted on main_image
def test_ac4_clean_main_image_accepts_valid_image(valid_jpeg):
    # slug + status u payload-u (vidi blank-skip test) — fokus asercije je upload-path,
    # NE slug/status required-noise. is_valid() True MORA biti zbog validnog uploada.
    form = _make_post_form(
        data={"title_sr": "Sa Slikom", "slug": "sa-slikom", "status": "draft"},
        files={"main_image": valid_jpeg},
    )
    assert form.is_valid(), (
        f"Validan JPEG main_image MORA proći upload double-check (AC4); errors={form.errors!r}."
    )


# ══════════════════════════════════════════════════════════════════════════════
# AC5 — Publish-gate (graceful draft revert, NIKAD 500)
# ══════════════════════════════════════════════════════════════════════════════
def _draft_post(make_post, author_user, **overrides):
    return make_post(author=author_user, status="draft", **overrides)


def _post_publish(client, post, *, with_image=None):
    """Scrape change form, flip to published, return (url, data) for the POST."""
    url = reverse("admin:blog_post_change", args=[post.pk])
    data = _scrape_change_form(client.get(url).content.decode())
    data["title_sr"] = post.title_sr or "Gejt Objava"
    data["status"] = "published"
    _seo_inline_mgmt(data)
    return url, data


# AC-5: publish with EMPTY body_sr → graceful 200, stays draft, error message (NOT 500)
def test_ac5_publish_without_body_reverts_to_draft(
    client, superuser, make_post, make_category, author_user, valid_jpeg
):
    from apps.blog.models import Post

    client.force_login(superuser)
    cat = make_category()
    post = _draft_post(make_post, author_user, category=cat, body_sr="")
    post.main_image.save("g.jpg", valid_jpeg, save=True)
    url, data = _post_publish(client, post)
    data["body_sr"] = ""  # missing → gate must block publish
    data["category"] = str(cat.pk)
    resp = client.post(url, data, follow=True)
    assert resp.status_code == 200, (
        f"Publish bez body_sr MORA biti graceful 200 (NE 500 iz gate raise — G-6/G-7); "
        f"dobio {resp.status_code}."
    )
    post.refresh_from_db()
    assert post.status == Post.Status.DRAFT, (
        f"Objava MORA OSTATI draft kad fali body_sr (revert — AC5/G-6); status={post.status!r}."
    )
    # The gate (not an accidental form failure) MUST emit a messages.error naming the
    # missing requirement — this distinguishes a real publish-gate revert from the stub,
    # which has no gate and never produces this message (8.4/8.6 lesson).
    msgs = " ".join(str(m) for m in resp.context["messages"]).lower()
    assert "telo" in msgs or "body" in msgs or "objavljivanje" in msgs, (
        f"Publish-gate MORA emitovati messages.error koja navodi nedostajuće (telo objave) "
        f"pri pokušaju objave bez body_sr (AC5); poruke: {msgs!r}."
    )


# AC-5: publish with NO category → graceful 200, stays draft (OQ-4 default: category required)
def test_ac5_publish_without_category_reverts_to_draft(
    client, superuser, make_post, author_user, valid_jpeg
):
    from apps.blog.models import Post

    client.force_login(superuser)
    post = _draft_post(make_post, author_user, body_sr="<p>Telo objave.</p>")
    post.main_image.save("g.jpg", valid_jpeg, save=True)
    url, data = _post_publish(client, post)
    data["body_sr"] = "<p>Telo objave.</p>"
    data["category"] = ""  # missing category → gate blocks (OQ-4 default)
    resp = client.post(url, data, follow=True)
    assert resp.status_code == 200, (
        f"Publish bez kategorije MORA biti graceful 200 (NE 500 — G-7); dobio {resp.status_code}."
    )
    post.refresh_from_db()
    assert post.status == Post.Status.DRAFT, (
        "Objava MORA OSTATI draft kad fali kategorija (revert — AC5/OQ-4)."
    )
    # Gate message names the missing requirement (distinguishes real gate from stub — AC5).
    msgs = " ".join(str(m) for m in resp.context["messages"]).lower()
    assert "kategorij" in msgs or "objavljivanje" in msgs, (
        f"Publish-gate MORA emitovati messages.error koja navodi nedostajuću kategoriju "
        f"(AC5/OQ-4); poruke: {msgs!r}."
    )


# AC-5: publish with NO main_image → graceful 200, stays draft, error names the missing image
def test_ac5_publish_without_main_image_reverts_to_draft(
    client, superuser, make_post, make_category, author_user
):
    from apps.blog.models import Post

    client.force_login(superuser)
    cat = make_category()
    # Draft sa body_sr + category ALI BEZ main_image (sliku ne snimamo) → gate blokira objavu.
    post = _draft_post(make_post, author_user, category=cat, body_sr="<p>Telo objave.</p>")
    url, data = _post_publish(client, post)
    data["body_sr"] = "<p>Telo objave.</p>"
    data["category"] = str(cat.pk)
    resp = client.post(url, data, follow=True)
    assert resp.status_code == 200, (
        f"Publish bez main_image MORA biti graceful 200 (NE 500 iz gate raise — G-6/G-7); "
        f"dobio {resp.status_code}."
    )
    post.refresh_from_db()
    assert post.status == Post.Status.DRAFT, (
        f"Objava MORA OSTATI draft kad fali main_image (revert — AC5/G-6); status={post.status!r}."
    )
    # Gate message names the missing requirement (distinguishes real gate from stub — AC5).
    msgs = " ".join(str(m) for m in resp.context["messages"]).lower()
    assert "slika" in msgs or "objavljivanje" in msgs, (
        f"Publish-gate MORA emitovati messages.error koja navodi nedostajuću glavnu sliku "
        f"(AC5); poruke: {msgs!r}."
    )


# AC-5 (positive): publish with title_sr + body_sr + main_image + category → PUBLISHED
def test_ac5_complete_publish_succeeds(
    client, superuser, make_post, make_category, author_user, valid_jpeg
):
    from apps.blog.models import Post

    client.force_login(superuser)
    cat = make_category()
    post = _draft_post(make_post, author_user, category=cat, body_sr="<p>Telo.</p>")
    post.main_image.save("g.jpg", valid_jpeg, save=True)
    url, data = _post_publish(client, post)
    data["body_sr"] = "<p>Telo.</p>"
    data["category"] = str(cat.pk)
    resp = client.post(url, data, follow=True)
    assert resp.status_code == 200, f"Kompletan publish MORA biti 200; dobio {resp.status_code}."
    post.refresh_from_db()
    assert post.status == Post.Status.PUBLISHED, (
        f"Objava sa title_sr + body_sr + main_image + category MORA biti objavljena "
        f"(gate prolazi — AC5); status={post.status!r}."
    )


# AC-5 (boundary): DRAFT save with empty body/no image/no category → PASSES (gate fires only on publish)
def test_ac5_draft_save_with_no_content_passes(client, superuser, make_post, author_user):
    from apps.blog.models import Post

    client.force_login(superuser)
    post = _draft_post(make_post, author_user, body_sr="")
    url = reverse("admin:blog_post_change", args=[post.pk])
    data = _scrape_change_form(client.get(url).content.decode())
    data["title_sr"] = post.title_sr or "Nacrt"
    data["body_sr"] = ""
    data["status"] = "draft"
    _seo_inline_mgmt(data)
    resp = client.post(url, data, follow=True)
    assert resp.status_code == 200, (
        f"Draft save bez body/slike/kategorije MORA biti 200 (gate se NE okida na draft — AC5); "
        f"dobio {resp.status_code}."
    )
    post.refresh_from_db()
    assert post.status == Post.Status.DRAFT, "Draft objava MORA ostati sačuvana kao draft (AC5)."


# ══════════════════════════════════════════════════════════════════════════════
# AC6 — published_at auto-set pri publish-u ako prazno (timezone.now())
# ══════════════════════════════════════════════════════════════════════════════
# AC-6: publishing with published_at=None auto-sets it (and is timezone-aware)
def test_ac6_published_at_auto_set_on_publish(
    client, superuser, make_post, make_category, author_user, valid_jpeg
):
    from django.utils import timezone

    from apps.blog.models import Post

    client.force_login(superuser)
    cat = make_category()
    post = _draft_post(
        make_post, author_user, category=cat, body_sr="<p>Telo.</p>", published_at=None
    )
    post.main_image.save("g.jpg", valid_jpeg, save=True)
    url, data = _post_publish(client, post)
    data["body_sr"] = "<p>Telo.</p>"
    data["category"] = str(cat.pk)
    data["published_at_0"] = ""  # admin split date/time widget — leave empty
    data["published_at_1"] = ""
    resp = client.post(url, data, follow=True)
    assert resp.status_code == 200
    post.refresh_from_db()
    assert post.status == Post.Status.PUBLISHED, "Objava MORA biti objavljena (AC6 preduslov)."
    assert post.published_at is not None, (
        "published_at MORA biti auto-postavljen pri objavi kad je prazno (AC6/SM-D12)."
    )
    assert timezone.is_aware(post.published_at), (
        "published_at MORA biti timezone-aware (timezone.now(), NIKAD naive datetime.now() — AC6)."
    )


# AC-6: manually set published_at is NOT overwritten on publish (zakazana objava — SM-D12)
def test_ac6_existing_published_at_not_overwritten(
    client, superuser, make_post, make_category, author_user, valid_jpeg
):
    from datetime import timedelta

    from django.utils import timezone

    from apps.blog.models import Post

    client.force_login(superuser)
    cat = make_category()
    future = (timezone.now() + timedelta(days=30)).replace(microsecond=0)
    post = _draft_post(
        make_post, author_user, category=cat, body_sr="<p>Telo.</p>", published_at=future
    )
    post.main_image.save("g.jpg", valid_jpeg, save=True)
    url, data = _post_publish(client, post)
    data["body_sr"] = "<p>Telo.</p>"
    data["category"] = str(cat.pk)
    resp = client.post(url, data, follow=True)
    assert resp.status_code == 200
    post.refresh_from_db()
    # Gate must actually pass (all reqs present) → published; otherwise published_at unchanged
    # is meaningless (the stub never publishes). Pins that publish succeeds AND keeps the date.
    assert post.status == Post.Status.PUBLISHED, (
        "Preduslov AC6: kompletna objava sa budućim published_at MORA biti objavljena (gate prolazi)."
    )
    assert post.published_at is not None and abs(
        (post.published_at - future).total_seconds()
    ) < 60, (
        "Ručno postavljen budući published_at NE SME biti pregažen pri objavi "
        f"(zakazana objava — SM-D12); očekivano ~{future}, dobio {post.published_at}."
    )


# ══════════════════════════════════════════════════════════════════════════════
# AC7 — Tag slobodno dodavanje (filter_horizontal) + Category FK dropdown
# ══════════════════════════════════════════════════════════════════════════════
# AC-7: tags M2M uses filter_horizontal (dual-list + related `+` add-popup)
def test_ac7_tags_filter_horizontal():
    fh = tuple(getattr(_post_admin(), "filter_horizontal", ()))
    assert "tags" in fh, (
        "PostAdmin.filter_horizontal MORA uključiti 'tags' (M2M slobodno dodavanje + "
        f"related `+` add-popup — AC7); dobio {fh!r}."
    )


# AC-7: TagAdmin + CategoryAdmin independently registered (changelist/add → 200)
def test_ac7_tag_and_category_changelist_and_add_200(client, superuser, make_tag, make_category):
    client.force_login(superuser)
    make_tag()
    make_category()
    for model in ("tag", "category"):
        cl = client.get(reverse(f"admin:blog_{model}_changelist"))
        assert cl.status_code == 200, f"blog_{model}_changelist MORA biti 200 (AC7)."
        add = client.get(reverse(f"admin:blog_{model}_add"))
        assert add.status_code == 200, f"blog_{model}_add MORA biti 200 (AC7)."


# AC-7: CategoryAdmin + TagAdmin have prepopulated slug from name (CRUD usability)
def test_ac7_category_tag_prepopulated_slug():
    # TranslationAdmin AUTO-rewrite-uje prepopulated source `name` → `name_sr` (default-lang
    # realna kolona) pri registraciji — slug se prepopulira iz sr naziva u admin JS (G-14).
    # Deklaracija je `{"slug": ("name",)}`; runtime vrednost je `{"slug": ("name_sr",)}`.
    assert _category_admin().prepopulated_fields == {"slug": ("name_sr",)}, (
        "CategoryAdmin MORA imati prepopulated slug iz name (TranslationAdmin → name_sr; AC7/G-14)."
    )
    assert _tag_admin().prepopulated_fields == {"slug": ("name_sr",)}, (
        "TagAdmin MORA imati prepopulated slug iz name (TranslationAdmin → name_sr; AC7/G-14)."
    )


# ══════════════════════════════════════════════════════════════════════════════
# AC8 — SeoMetaInline + SeoWarningAdminMixin regression + view_on_site re-enable (SM-D8)
# ══════════════════════════════════════════════════════════════════════════════
# AC-8 (INVARIANT-LOCK — MAY PASS today: 6.1 already has SeoMetaInline on PostAdmin)
def test_ac8_seometa_inline_still_on_postadmin():
    from apps.seo.admin import SeoMetaInline

    inlines = list(_post_admin().inlines)
    assert any(ic is SeoMetaInline or issubclass(ic, SeoMetaInline) for ic in inlines), (
        "SeoMetaInline MORA OSTATI na PostAdmin posle nadogradnje (6.1 regression — G-8/AC8)."
    )


# AC-8 (INVARIANT-LOCK — MAY PASS today: 5.1 already subclasses SeoWarningAdminMixin)
def test_ac8_seowarning_mixin_in_mro():
    from apps.seo.admin import SeoWarningAdminMixin

    assert isinstance(_post_admin(), SeoWarningAdminMixin), (
        "PostAdmin MORA zadržati SeoWarningAdminMixin u MRO (mixin PRVI — G-2/G-8/AC8)."
    )


# AC-8 (SM-D8): view_on_site is RE-ENABLED (NOT False) — blog:detail registered (5-3)
def test_ac8_view_on_site_re_enabled():
    assert _post_admin().view_on_site is not False, (
        "PostAdmin.view_on_site MORA biti RE-ENABLED (NIJE False) — 5-3 registrovao blog:detail "
        "→ „View on site“ radi (SM-D8/AC8); 5-1 view_on_site=False se NAMERNO menja u 8.7."
    )


# AC-8 (SM-D8 regression boundary): DRAFT post „View on site“ → blog:detail returns 404 NOT 500
def test_ac8_draft_view_on_site_404_not_500(client, make_post, author_user):
    post = make_post(author=author_user, status="draft")
    # Post.published manager filtrira draft → detail view → 404 (5-3 draft-404). The lock:
    # re-enable MUST NOT introduce a 500/NoReverseMatch; 404 is the accepted behavior.
    resp = client.get(post.get_absolute_url(), HTTP_HOST="localhost")
    assert resp.status_code == 404, (
        f"DRAFT post blog:detail MORA biti 404 (Post.published filtrira draft — 5-3), NE 500/"
        f"NoReverseMatch (SM-D8 re-enable regression boundary); dobio {resp.status_code}."
    )


# AC-8: Post add-view still renders SeoMetaInline (200, regression — G-8)
def test_ac8_post_add_view_renders_inline_200(client, superuser):
    client.force_login(superuser)
    resp = client.get(reverse("admin:blog_post_add"))
    assert resp.status_code == 200, (
        f"Post add-view MORA ostati 200 — SeoMetaInline na TranslationAdmin + WYSIWYG ne ruše "
        f"render (G-8 regression); dobio {resp.status_code}."
    )


# ══════════════════════════════════════════════════════════════════════════════
# AC9 — title_sr bezuslovno obavezan (modeltranslation required-promotion — NE relaksiraj)
# ══════════════════════════════════════════════════════════════════════════════
def _admin_form_field_required(name):
    from django.contrib.auth.models import AnonymousUser
    from django.test import RequestFactory

    model_admin = _post_admin()
    req = RequestFactory().get("/")
    req.user = AnonymousUser()
    form_cls = model_admin.get_form(req)
    return form_cls.base_fields[name].required


# AC-9: title_sr is required on the admin-built form (required-promotion NOT relaxed)
def test_ac9_title_sr_required_on_admin_form():
    assert _admin_form_field_required("title_sr") is True, (
        "title_sr MORA biti obavezno na admin PostForm-u (model `title` blank=False + sr "
        "default lang → TranslationAdmin required-promotion); promotion se NE relaksira (AC9/G-11)."
    )


# AC-9 (graceful): empty title_sr on add → 200 form-error on title_sr, NO new Post (NOT 500)
def test_ac9_empty_title_sr_graceful_form_error(client, superuser):
    from apps.blog.models import Post

    before = Post.objects.count()
    client.force_login(superuser)
    url = reverse("admin:blog_post_add")
    data = _scrape_change_form(client.get(url).content.decode())
    data["title_sr"] = ""
    data["slug"] = ""
    data["status"] = "draft"
    _seo_inline_mgmt(data)
    resp = client.post(url, data)
    assert resp.status_code == 200, (
        f"Prazan title_sr MORA dati graceful 200 form-error (NIKAD 400/500 iz model full_clean "
        f"escape — AC9/G-11); dobio {resp.status_code}."
    )
    form = resp.context["adminform"].form
    assert "title_sr" in form.errors, (
        f"Prazan title_sr MORA dati field grešku na `title_sr` (required); dobio {form.errors!r}."
    )
    assert Post.objects.count() == before, (
        "Nijedan NOV Post NE SME biti kreiran kad je title_sr prazan (AC9/G-11)."
    )


# AC-9 (edge): whitespace-only title_sr is rejected (not silently accepted as blank-bypass)
def test_ac9_whitespace_title_sr_rejected(client, superuser):
    from apps.blog.models import Post

    before = Post.objects.count()
    client.force_login(superuser)
    url = reverse("admin:blog_post_add")
    data = _scrape_change_form(client.get(url).content.decode())
    data["title_sr"] = "   "
    data["slug"] = ""
    data["status"] = "draft"
    _seo_inline_mgmt(data)
    resp = client.post(url, data)
    assert resp.status_code == 200, (
        f"Whitespace-only title_sr MORA dati graceful 200 (NE 500); dobio {resp.status_code}."
    )
    assert Post.objects.count() == before, (
        "Whitespace-only title_sr NE SME kreirati Post (Django strip → prazno → required; AC9)."
    )


# AC-9 (positive): valid title_sr → 302 redirect, Post created (draft)
def test_ac9_valid_title_sr_creates_post(client, superuser):
    from apps.blog.models import Post

    client.force_login(superuser)
    url = reverse("admin:blog_post_add")
    data = _scrape_change_form(client.get(url).content.decode())
    data["title_sr"] = "Objavljena Priča sa polja"
    data["slug"] = "objavljena-prica-sa-polja"
    data["status"] = "draft"
    _seo_inline_mgmt(data)
    resp = client.post(url, data)
    assert resp.status_code == 302, (
        f"Validan title_sr MORA sačuvati Post i dati 302 (AC9); dobio {resp.status_code}."
    )
    assert Post.objects.filter(title_sr="Objavljena Priča sa polja").exists(), (
        "Validan Post sa title_sr MORA biti kreiran (AC9)."
    )


# ══════════════════════════════════════════════════════════════════════════════
# AC10 — RBAC verify (NE re-grant) + anon redirect + CSRF
# ══════════════════════════════════════════════════════════════════════════════
# AC-10 (INVARIANT-LOCK — MAY PASS today: 8.2 already granted blog post changelist to Editor)
def test_ac10_editor_can_access_blog_post_changelist(client, editor):
    client.force_login(editor)
    resp = client.get(reverse("admin:blog_post_changelist"))
    assert resp.status_code == 200, (
        f"Editor Post changelist MORA biti 200 (8.2 grant netaknut — verify, NE re-grant; "
        f"AC10/SM-D11); dobio {resp.status_code}."
    )


# AC-10: Editor add-view 200 + can POST-save a valid draft Post
def test_ac10_editor_can_add_post(client, editor):
    from apps.blog.models import Post

    client.force_login(editor)
    url = reverse("admin:blog_post_add")
    add = client.get(url)
    assert add.status_code == 200, f"Editor Post add-view MORA biti 200 (AC10); dobio {add.status_code}."
    data = _scrape_change_form(add.content.decode())
    data["title_sr"] = "Editorova Priča"
    data["slug"] = "editorova-prica"
    data["status"] = "draft"
    _seo_inline_mgmt(data)
    resp = client.post(url, data, follow=True)
    assert resp.status_code == 200, f"Editor add POST MORA biti 200; dobio {resp.status_code}."
    assert Post.objects.filter(title_sr="Editorova Priča").exists(), (
        "Editor MORA moći da sačuva validan draft Post kroz admin (AC10)."
    )


# AC-10 (negative / security): anonymous → 302 admin login (NOT 200, NOT 500)
def test_ac10_anonymous_redirected_to_login(client):
    resp = client.get(reverse("admin:blog_post_changelist"))
    assert resp.status_code == 302, (
        f"Anoniman na Post changelist MORA biti 302 (admin login redirect — AC10); "
        f"dobio {resp.status_code}."
    )
    assert reverse("admin:login") in resp["Location"], (
        f"302 MORA voditi na admin:login (admin na bare /admin-coric/ iz 8.1); "
        f"Location={resp['Location']!r}."
    )


# AC-10 (security / CSRF): admin POST without CSRF token → 403 (csrf enforced on admin)
def test_ac10_admin_post_without_csrf_forbidden(superuser):
    from django.test import Client

    csrf_client = Client(enforce_csrf_checks=True)
    csrf_client.force_login(superuser)
    resp = csrf_client.post(
        reverse("admin:blog_post_add"),
        {"title_sr": "Bez CSRF", "status": "draft"},
    )
    assert resp.status_code == 403, (
        f"Admin POST bez CSRF token-a MORA biti 403 (CSRF enforced — AC10/security); "
        f"dobio {resp.status_code}."
    )


# ══════════════════════════════════════════════════════════════════════════════
# AC11 — 0 blog migracija (admin-only; body ostaje plain TextField — SM-D2)
# ══════════════════════════════════════════════════════════════════════════════
# AC-11: no pending schema migration for apps.blog (admin-only story)
def test_ac11_no_pending_migration_for_blog():
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
    assert "blog" not in changes, (
        f"apps.blog NE SME imati pending schema migraciju (8.7 je admin-only; body ostaje plain "
        f"TextField — SM-D2/AC11); autodetector predlaže: {changes.get('blog')}."
    )


# ══════════════════════════════════════════════════════════════════════════════
# AC12 — manage.py check čist + regression (changelist 200; legal_html consumers intact)
# ══════════════════════════════════════════════════════════════════════════════
# AC-12 (regression): superuser Post changelist 200 (5.1 + 6.1 lock parity after upgrade)
def test_ac12_post_changelist_200_superuser(client, superuser, make_post, author_user):
    make_post(author=author_user)
    client.force_login(superuser)
    resp = client.get(reverse("admin:blog_post_changelist"))
    assert resp.status_code == 200, (
        f"Post changelist MORA ostati 200 posle nadogradnje (regression — AC12); "
        f"dobio {resp.status_code}."
    )


# AC-12 (regression / SM-D9): legal_html sanitizer + filter still importable (gdpr/pages intact)
def test_ac12_legal_html_filter_regression_intact():
    from django.template import Context, Template

    tpl = Template("{% load legal_html %}{{ body|legal_html }}")
    rendered = tpl.render(Context({"body": "<p>OK</p><script>alert(1)</script>"}))
    assert "<p>OK</p>" in rendered and "<script" not in rendered, (
        "Postojeći legal_html filter MORA ostati funkcionalan (gdpr/pages potrošači — SM-D9/OQ-2). "
        "Ako 8.7 doda rich_html alias, NE SME razbiti legal_html backend."
    )
