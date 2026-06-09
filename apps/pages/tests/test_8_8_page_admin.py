"""Story 8.8 — Statičke Strane CRUD admin (TEA RED phase).

DEFINES the contract Dev (GREEN) must satisfy. Maps the 12 ACs + SM-decisions +
gotchas of `8-8-staticke-strane-crud.md`. Canonical contract:
`8-8-staticke-strane-crud-interface-contract.md`.

8.8 upgrades the EXISTING `apps/pages/admin.py:PageAdmin` (7-4 stub) into a full
multi-locale CRUD admin over the generic `Page` model, REUSING the 8-7 WYSIWYG hook
for `Page.body`. Admin-only: 0 migrations, body stays plain TextField, NO upload /
publish-gate / SeoMetaInline. The render-time `legal_html` sanitization on
`templates/pages/page-detail.html` ALREADY EXISTS (7-5) — 8.8 does NOT touch it.

RED expectation: `apps/pages/admin.py` is still the 7-4 stub
(`search_fields=("title","slug")`, no `Media`, no WYSIWYG hook, no `formfield_for_dbfield`).
The genuine NEW-capability tests MUST fail/error:
  - AC2 search_fields == ("title_sr","slug") — stub is ("title","slug"). ← the real AC2 lock.
  - AC3 body_<locale> WYSIWYG marker — stub has no hook.
  - AC3 Media.js contains js/wysiwyg.js — stub has no Media.

⚠️ AC2 FieldError CORRECTION (opus-runtime > sonnet-static; memory lesson). The story's
premise — that `search_fields=("title",)` throws a RUNTIME FieldError on changelist `?q=` —
is FACTUALLY WRONG for `Page`. modeltranslation KEEPS the original `title` column as a real
concrete DB column (default-language proxy) ALONGSIDE `title_sr/hu/en`. Runtime-verified:
`PageAdmin.get_search_results(req, qs, "Naslov")` evaluates cleanly (no FieldError) and the
admin changelist `?q=` returns 200 EVEN ON THE STUB. (Contrast: brands/products
`name`-search cases where the base column may be virtual.) So the changelist `?q=`→200 test
is a REGRESSION LOCK (search must keep working), NOT a RED bug-repro. The real, RED, AC2
behavior 8.8 must implement is the SEARCH-OVER-THE-SR-COLUMN intent encoded by the
`search_fields == ("title_sr","slug")` value assertion (`test_ac2_search_fields_uses_real_column`),
which fails correctly today. Dev: change `("title","slug")` → `("title_sr","slug")`.

AC12 / AC4 regression locks PASS today (7-5 sanitizer already in place) — they pin that 8.8
opens NO new unsanitized render path and does NOT touch the template.

INVARIANT / REGRESSION locks that MAY pass today (legitimate — they pin contracts 8.8 must
NOT regress): AC1 TranslationAdmin, AC6 not-singleton, AC7 view_on_site default, AC8 RBAC
editor access, AC9 title_sr required, AC10 0-migration, AC12 grep + render-strip.

────────────────────────────────────────────────────────────────────────────────
COLLECTION-SAFETY: all `apps.pages.admin` / `PageAdmin` symbol reads are INSIDE test
bodies (lazy) so a missing/changed symbol fails that test individually (true RED), never
aborts collection of the whole file.

AUTH: authenticate with `force_login` (NEVER `client.login` — django-axes from 8.1
pollutes lockout state through authenticate(); established project lesson).

ADMIN URL: always `reverse("admin:pages_page_*")` — admin is at bare /admin-coric/ (8.1),
never hardcode.

XSS ASSERT (7-5/8-7 lesson): scope to the rendered `coric-static-page__body` fragment +
test STRIP (`"<script" not in body`) NOT escape; NEVER `"alert(1) not in html"`.

Refs: 8-8-...md (AC1-AC12, SM-D1..D9, G-1..G-12) + interface contract +
apps/pages/tests/test_7_4_static_pages.py (existing locks + _privacy_body_fragment pattern) +
apps/blog/tests/test_8_7_blog_crud_admin.py (WYSIWYG widget + admin-CRUD test patterns).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from django.conf import settings
from django.contrib import admin
from django.urls import reverse

pytestmark = pytest.mark.django_db


# ──────────────────────────────────────────────────────────────────────────────
# Fixtures (pages conftest has no superuser fixture → define locally; mirror 7-4)
# ──────────────────────────────────────────────────────────────────────────────
@pytest.fixture
def superuser(django_user_model):
    """Superuser for admin changelist/add/change CRUD smoke.

    `django_user_model` = settings.AUTH_USER_MODEL via get_user_model() — NEVER a
    direct `from django.contrib.auth.models import User`.
    """
    return django_user_model.objects.create_superuser(
        username="pages_admin_8_8",
        email="pages-admin-88@example.com",
        password="tea-pass-12345",
    )


@pytest.fixture
def editor(django_user_model):
    """Editor = is_staff + member of `Editor` group (8.2 post_migrate created it;
    EDITOR_CONTENT_MODELS already carries ('pages','page') — SM-D8, verify NOT re-grant)."""
    from django.contrib.auth.models import Group

    user = django_user_model.objects.create_user(
        username="pages_editor_8_8",
        email="pages-editor-88@example.com",
        password="tea-pass-12345",
        is_staff=True,
        is_superuser=False,
    )
    user.groups.add(Group.objects.get(name="Editor"))
    return user


def _Page():
    """Lazy import — collection-safe."""
    from apps.pages.models import Page

    return Page


def _page_admin():
    return admin.site._registry[_Page()]


def _make_page(slug="info-strana", title="Info strana", body="Telo strane."):
    """update_or_create (NE get_or_create): pages 0004 data-seed AUTO-creates
    Page(slug='politika-privatnosti') in the test DB; use a distinct slug + force
    title/body via _sr columns (mirror 7-4 _make_page)."""
    Page = _Page()
    page, _created = Page.objects.update_or_create(
        slug=slug, defaults={"title_sr": title, "body_sr": body}
    )
    return page


def _static_body_fragment(html):
    """Extract ONLY the sanitized `coric-static-page__body` region (7-4 pattern).

    Asserting `<script` absence over the WHOLE page is unsatisfiable — base.html chrome
    legitimately renders `<script src=...>`/`<img>`/`<div>`. Scope to the body div."""
    marker = 'class="coric-static-page__body"'
    start = html.find(marker)
    assert start != -1, "Static-page body region MORA postojati u renderu (AC4/AC12)."
    end = html.find("</article>", start)
    return html[start : end if end != -1 else len(html)]


def _scrape_change_form(html):
    """name->value for all input/select/textarea fields in an admin change form
    (mirror 8-7 scraper)."""
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
        data[name] = opts[0] if opts else ""
    for tm in re.finditer(r'<textarea[^>]*name="([^"]+)"[^>]*>(.*?)</textarea>', html, re.S):
        data[tm.group(1)] = tm.group(2)
    return data


# ══════════════════════════════════════════════════════════════════════════════
# AC1 — TranslationAdmin multi-locale + CRUD smoke (INVARIANT-LOCK + render-smoke)
# ══════════════════════════════════════════════════════════════════════════════
# AC-1: PageAdmin stays TranslationAdmin (NOT plain ModelAdmin; auto sr/hu/en tabs)
def test_ac1_pageadmin_is_translation_admin():
    from modeltranslation.admin import TranslationAdmin

    assert isinstance(_page_admin(), TranslationAdmin), (
        "PageAdmin MORA OSTATI TranslationAdmin (per-locale title/body tabovi; AC1/SM-D6)."
    )


# AC-1/SM-D6: PageAdmin is NOT a SeoWarningAdminMixin subclass and has NO inlines (Page has no SeoMeta)
def test_ac1_pageadmin_no_seometa_inline():
    from apps.seo.admin import SeoWarningAdminMixin

    model_admin = _page_admin()
    assert not isinstance(model_admin, SeoWarningAdminMixin), (
        "PageAdmin NE SME biti SeoWarningAdminMixin subclass — Page NIJE SeoMeta receiver "
        "(SM-D6/G-3; mirror 7-4 stub)."
    )
    assert list(model_admin.inlines) == [], (
        "PageAdmin NE SME imati inlines (NEMA SeoMetaInline; Page van SeoMeta GFK — SM-D6/G-3); "
        f"dobio {list(model_admin.inlines)!r}."
    )


# AC-1: superuser changelist 200 (NIJE singleton — NE redirect; regression-smoke)
def test_ac1_changelist_200_superuser(client, superuser):
    _make_page()
    client.force_login(superuser)
    resp = client.get(reverse("admin:pages_page_changelist"))
    assert resp.status_code == 200, (
        f"PageAdmin changelist MORA biti 200 za superuser (AC1); dobio {resp.status_code}."
    )


# AC-1: add-view 200 (TranslationAdmin + WYSIWYG widget render-smoke — per-locale fields present)
def test_ac1_add_view_200_renders_per_locale_fields(client, superuser):
    client.force_login(superuser)
    resp = client.get(reverse("admin:pages_page_add"))
    assert resp.status_code == 200, (
        f"PageAdmin add-view MORA biti 200 (TranslationAdmin + WYSIWYG widget ne smeju "
        f"baciti admin.E*/render fail — AC1/AC3); dobio {resp.status_code}."
    )
    html = resp.content.decode()
    for fld in ("title_sr", "title_hu", "title_en", "body_sr", "body_hu", "body_en"):
        assert f'name="{fld}"' in html, (
            f"Add-view MORA renderovati per-locale polje '{fld}' (render-smoke — AC1)."
        )


# AC-1: change-view 200 for an existing Page (regression-smoke)
def test_ac1_change_view_200_superuser(client, superuser):
    page = _make_page()
    client.force_login(superuser)
    resp = client.get(reverse("admin:pages_page_change", args=[page.pk]))
    assert resp.status_code == 200, (
        f"PageAdmin change-view MORA biti 200 za superuser (AC1); dobio {resp.status_code}."
    )


# AC-1/AC11: admin system checks clean (TranslationAdmin + search_fields real column + WYSIWYG → 0 admin.E*)
def test_ac11_admin_system_checks_clean():
    from django.core.checks import run_checks

    errors = [e for e in run_checks() if e.is_serious()]
    assert errors == [], (
        f"manage.py check MORA biti čist — TranslationAdmin + search_fields=('title_sr','slug') "
        f"realna kolona + prepopulated_fields + WYSIWYG widget ne smeju baciti admin.E* "
        f"(AC11/G-1). Greške: {errors}."
    )


# ══════════════════════════════════════════════════════════════════════════════
# AC2 — search_fields realna kolona (LATENT 7-4 BUG FIX — THE load-bearing lock)
# ══════════════════════════════════════════════════════════════════════════════
# AC-2 (the real RED AC2 lock): search_fields == ("title_sr","slug") — sr-suffix DB column
# (intent: search the default-locale column explicitly; SM-D4). Stub is ("title","slug") → RED.
def test_ac2_search_fields_uses_real_column():
    assert tuple(_page_admin().search_fields) == ("title_sr", "slug"), (
        "PageAdmin.search_fields MORA biti ('title_sr','slug') — eksplicitna default-locale "
        "kolona (mirror 8.4-8.7 ('name_sr',)/('title_sr',) konvencija; SM-D4/G-1). Trenutni "
        f"7-4 stub ima ('title','slug') → ISPRAVI na ('title_sr','slug'); dobio "
        f"{_page_admin().search_fields!r}."
    )


# AC-2 (REGRESSION LOCK — green today, must STAY green): changelist with ?q=<term> → 200.
# NOTE (opus-runtime correction): the stub `search_fields=("title",)` does NOT raise a
# FieldError — modeltranslation keeps `title` as a real concrete column, so `?q=` is 200 even
# on the stub (runtime-verified). This test therefore pins that the AC2 fix to ('title_sr','slug')
# does NOT REGRESS changelist search (typing a term still returns 200, not 500), NOT a bug-repro.
def test_ac2_changelist_search_query_returns_200_not_500(client, superuser):
    _make_page(title="Naslov strane")
    client.force_login(superuser)
    resp = client.get(reverse("admin:pages_page_changelist"), {"q": "Naslov"})
    assert resp.status_code == 200, (
        f"Changelist search (?q=) MORA biti 200 — search_fields=('title_sr','slug') je realna "
        f"kolona i NE sme baciti FieldError 500 (AC2/SM-D4/G-1); dobio {resp.status_code}."
    )


# AC-2: virtual `title` STAYS in list_display (correct there — per-locale render, NOT search)
def test_ac2_list_display_keeps_virtual_title():
    assert "title" in tuple(_page_admin().list_display), (
        "list_display MORA zadržati virtuelni `title` (per-active-locale render u changelist-u "
        "je ISPRAVAN — RAZLIKA od search_fields gde treba realna kolona; AC2/G-1)."
    )


# ══════════════════════════════════════════════════════════════════════════════
# AC3 — WYSIWYG editor za Page.body (form-widget, REUSE 8-7 mehanizam)
# ══════════════════════════════════════════════════════════════════════════════
# AC-3: each body_<locale> textarea carries the WYSIWYG marker (wysiwyg class / data-attr)
def test_ac3_body_fields_get_wysiwyg_widget():
    from django.contrib.auth.models import AnonymousUser
    from django.test import RequestFactory

    model_admin = _page_admin()
    req = RequestFactory().get("/")
    req.user = AnonymousUser()
    form_cls = model_admin.get_form(req)
    for fld in ("body_sr", "body_hu", "body_en"):
        assert fld in form_cls.base_fields, (
            f"Admin form MORA imati per-locale polje '{fld}' (AC3)."
        )
    # WYSIWYG = enhancement: EVERY body_<locale> widget MUST carry a marker that distinguishes
    # it from a bare admin Textarea — a custom widget class OR a CSS class / data-attr hook used
    # by static/js/wysiwyg.js (SM-D2 progressive enhancement). A plain AdminTextareaWidget with
    # no marker means no editor was wired. The impl wires ALL THREE locales — assert on each.
    for fld in ("body_sr", "body_hu", "body_en"):
        widget = form_cls.base_fields[fld].widget
        attrs = widget.attrs or {}
        attrs_class = (attrs.get("class") or "").lower()
        is_custom_widget = type(widget).__name__ not in ("AdminTextareaWidget", "Textarea")
        has_editor_hook = (
            "wysiwyg" in attrs_class
            or "rich" in attrs_class
            or any("wysiwyg" in str(k).lower() or "rich" in str(k).lower() for k in attrs)
        )
        assert is_custom_widget or has_editor_hook, (
            f"{fld} widget MORA biti WYSIWYG enhancement (custom widget klasa ILI editor "
            "CSS/data hook na Textarea — AC3/SM-D2 progressive enhancement; mirror 8-7); dobio "
            f"plain {type(widget).__name__} bez marker-a (attrs={attrs!r})."
        )


# AC-3/G-9: `title` widget does NOT get the WYSIWYG marker (body-only; title je jednolinijski)
def test_ac3_title_widget_has_no_wysiwyg_marker():
    from django.contrib.auth.models import AnonymousUser
    from django.test import RequestFactory

    model_admin = _page_admin()
    req = RequestFactory().get("/")
    req.user = AnonymousUser()
    form_cls = model_admin.get_form(req)
    for fld in ("title_sr", "title_hu", "title_en"):
        widget = form_cls.base_fields[fld].widget
        attrs = widget.attrs or {}
        attrs_class = (attrs.get("class") or "").lower()
        assert "wysiwyg" not in attrs_class and not any(
            "wysiwyg" in str(k).lower() for k in attrs
        ), (
            f"{fld} (jednolinijski naslov) NE SME imati WYSIWYG marker — hook je SAMO na body "
            f"(G-9; mirror 8-7 body-only); dobio attrs={attrs!r}."
        )


# AC-3: PageAdmin.Media.js includes js/wysiwyg.js (REUSE 8-7 GRANA B vanilla-JS)
def test_ac3_media_js_includes_wysiwyg():
    # Django's merged `forms.Media` exposes the resolved js list as the private `_js`
    # (no public `.js` attribute on this Django version); read it to prove wysiwyg.js
    # actually lands in the admin's rendered media.
    media = getattr(_page_admin(), "media", None)
    media_js = tuple(getattr(media, "_js", None) or getattr(media, "js", ()) or ())
    assert "js/wysiwyg.js" in media_js, (
        "PageAdmin.Media.js MORA sadržati 'js/wysiwyg.js' (REUSE static/js/wysiwyg.js — "
        f"8-7 GRANA B; AC3/SM-D2); dobio {media_js!r}."
    )


# AC-3/AC10: Page.body stays a plain TextField (WYSIWYG je form-widget — 0 migracija; SM-D2)
def test_ac3_body_stays_plain_textfield():
    from django.db import models as dj_models

    field = _Page()._meta.get_field("body")
    assert type(field) is dj_models.TextField, (
        "Page.body MORA OSTATI plain TextField — WYSIWYG je FORM-widget, NE model promena "
        f"(SM-D2/AC10); dobio {type(field).__name__}."
    )


# ══════════════════════════════════════════════════════════════════════════════
# AC4 — render-time sanitizacija VEĆ POSTOJI (REGRESSION LOCK; template NE menjan)
# ══════════════════════════════════════════════════════════════════════════════
# AC-4 (regression): <script> in body STRIPPED on render (scope to body fragment; strip-not-escape)
def test_ac4_script_payload_stripped_in_rendered_body(client):
    _make_page(slug="info-xss", body="<p>Bezbedan tekst.</p><script>alert(1)</script>")
    resp = client.get("/sr/info-xss/", HTTP_HOST="localhost")
    assert resp.status_code == 200
    body = _static_body_fragment(resp.content.decode())
    assert "<p>Bezbedan tekst.</p>" in body, "Dozvoljen <p> MORA proći sanitizaciju (AC4)."
    assert "<script" not in body, "`<script` MORA biti STRIP-ovan iz body fragmenta (AC4/SM-D5)."
    assert "&lt;script&gt;" not in resp.content.decode(), (
        "nh3 STRIPUJE node (NE escape) — `&lt;script&gt;` NE SME postojati (AC4/SM-D5)."
    )


# AC-4 (regression / security): adversarial vectors all neutralized in the rendered body
def test_ac4_adversarial_vectors_stripped_in_rendered_body(client):
    payload = (
        '<img src=x onerror="alert(1)">'
        '<a href="javascript:alert(1)" onclick="x()">klik</a>'
        "<iframe src='https://evil.test'></iframe>"
        "<p>kraj</p>"
    )
    _make_page(slug="info-adv", body=payload)
    resp = client.get("/sr/info-adv/", HTTP_HOST="localhost")
    assert resp.status_code == 200
    body = _static_body_fragment(resp.content.decode())
    assert "onerror" not in body, "`onerror` handler MORA biti STRIP-ovan (AC4)."
    assert "onclick" not in body, "`onclick` handler na <a> MORA biti STRIP-ovan (AC4)."
    assert "javascript:" not in body, "`javascript:` scheme MORA biti STRIP-ovan (AC4)."
    assert "<iframe" not in body, "<iframe> MORA biti STRIP-ovan iz body-a (AC4/SM-D5)."
    assert "<p>kraj</p>" in body, "Dozvoljen sadržaj posle payload-a MORA proći (AC4)."


# ══════════════════════════════════════════════════════════════════════════════
# AC12 — WYSIWYG NE uvodi NOVI ne-sanitizovan render-path za Page.body (NEW SM lock)
# ══════════════════════════════════════════════════════════════════════════════
# AC-12 (LOAD-BEARING): NO new raw/|safe/|linebreaks render path for page.body anywhere in templates
def test_ac12_no_unsanitized_page_body_render_path():
    """The 8-7/7-5 lesson: editor input is UNTRUSTED; nh3 at render is the ONLY boundary.
    8.8 must not open a parallel unsafe exit (a new partial rendering `body` raw, an admin
    preview using `|safe`, etc.). Grep ALL templates: every `page.body` output goes through
    `legal_html` (or its `rich_html` alias) — NO `page.body|safe` / `page.body|linebreaks` /
    bare `{{ page.body }}`."""
    import re

    templates_dir = Path(settings.BASE_DIR) / "templates"
    offenders = []
    for tpl in templates_dir.rglob("*.html"):
        text = tpl.read_text(encoding="utf-8")
        compact = text.replace(" ", "")
        # forbidden explicit unsafe filters on page.body
        if "page.body|safe" in compact or "page.body|linebreaks" in compact:
            offenders.append(f"{tpl} (eksplicitan |safe/|linebreaks na page.body)")
        # bare {{ page.body }} with NO filter is also an unsanitized path
        for m in re.finditer(r"\{\{\s*page\.body\s*([^}]*)\}\}", text):
            tail = m.group(1).strip()
            if not tail.startswith("|"):
                offenders.append(f"{tpl} (sirov {{{{ page.body }}}} bez filtera)")
            elif not re.search(r"\|\s*(legal_html|rich_html)\b", tail):
                offenders.append(f"{tpl} (page.body kroz ne-sanitizovan filter: {tail!r})")
    assert offenders == [], (
        "8.8 NE SME uvesti NOVI ne-sanitizovan render-path za page.body — JEDINI izlaz OSTAJE "
        "sanitizovani legal_html/rich_html filter (AC12/SM-D5; editor input je untrusted). "
        f"Pronađeni prekršioci: {offenders!r}."
    )


# AC-4/AC-12 (regression): page-detail.html still renders body via legal_html, never |safe/mark_safe
def test_ac4_template_body_uses_legal_html_not_safe():
    """Mirrors the 7-4 lock `test_template_body_uses_legal_html_not_safe`. 8.8 DEFAULT is to
    NOT touch the template (SM-D5) — this pins it stays `legal_html` and never |safe/mark_safe
    on raw body. If Dev (against the default) swaps to rich_html, both this and the 7-4 lock
    would need updating — DON'T."""
    tpl = Path(settings.BASE_DIR) / "templates" / "pages" / "page-detail.html"
    text = tpl.read_text(encoding="utf-8")
    compact = text.replace(" ", "")
    assert "page.body|legal_html" in compact or "page.body|rich_html" in compact, (
        "Template MORA renderovati body kroz |legal_html (ili rich_html alias) — sanitizovan "
        "rich-HTML (AC4/AC12/SM-D5)."
    )
    assert "body|safe" not in compact and "mark_safe" not in text, (
        "Template NE SME |safe / mark_safe na SIROV body (stored-XSS granica; AC4/AC12)."
    )


# ══════════════════════════════════════════════════════════════════════════════
# AC5 — prepopulated_fields slug + slug remains a manual ASCII business key
# ══════════════════════════════════════════════════════════════════════════════
# AC-5: prepopulated slug from title (TranslationAdmin rewrites source `title` → `title_sr`)
def test_ac5_prepopulated_slug_from_title():
    # TranslationAdmin AUTO-rewrites prepopulated source `title` → `title_sr` (default-lang real
    # column) at registration. Declaration is `{"slug": ("title",)}`; runtime is `{"slug": ("title_sr",)}`.
    pf = _page_admin().prepopulated_fields
    assert pf == {"slug": ("title_sr",)}, (
        "PageAdmin MORA imati prepopulated slug iz title (TranslationAdmin → title_sr; AC5/G-2); "
        f"dobio {pf!r}."
    )


# AC-5/G-11: empty slug on add → graceful 200 form-error (Page NEMA auto-slug — NIJE SluggedModel)
def test_ac5_empty_slug_graceful_form_error(client, superuser):
    Page = _Page()
    before = Page.objects.count()
    client.force_login(superuser)
    url = reverse("admin:pages_page_add")
    data = _scrape_change_form(client.get(url).content.decode())
    data["title_sr"] = "Strana bez sluga"
    data["slug"] = ""  # SlugField blank=False → required; Page nema auto-slug (G-11)
    resp = client.post(url, data)
    assert resp.status_code == 200, (
        f"Prazan slug MORA dati graceful 200 form-error (Page NEMA auto-slug — G-11; NIKAD 500); "
        f"dobio {resp.status_code}."
    )
    form = resp.context["adminform"].form
    assert "slug" in form.errors, (
        f"Prazan slug MORA dati field grešku na `slug` (required; G-11); dobio {form.errors!r}."
    )
    assert Page.objects.count() == before, (
        "Nijedan NOV Page NE SME biti kreiran kad je slug prazan (AC5/G-11)."
    )


# AC-5 (graceful / TEST_GAP): duplicate slug on add → 200 form-error (slug unique), NO 2nd Page.
# Pins Django SlugField unique validation as a GRACEFUL path through the REAL admin (8-4 lesson:
# assert through admin POST, NOT form.is_valid — full_clean uniqueness escape must be 200, never 500).
def test_ac5_duplicate_slug_graceful_form_error(client, superuser):
    Page = _Page()
    _make_page(slug="x", title="Prva strana")
    before = Page.objects.count()
    client.force_login(superuser)
    url = reverse("admin:pages_page_add")
    data = _scrape_change_form(client.get(url).content.decode())
    data["title_sr"] = "Druga strana"
    data["slug"] = "x"  # već zauzet → SlugField unique=True → graceful form-error
    resp = client.post(url, data)
    assert resp.status_code == 200, (
        f"Duplikat slug-a MORA dati graceful 200 form-error (Django unique validacija — NIKAD "
        f"500/IntegrityError; AC5/G-2); dobio {resp.status_code}."
    )
    form = resp.context["adminform"].form
    assert "slug" in form.errors, (
        f"Duplikat slug-a MORA dati field grešku na `slug` (uniqueness); dobio {form.errors!r}."
    )
    assert Page.objects.count() == before, (
        "Nijedan DRUGI Page sa istim slug-om NE SME biti perzistiran (AC5/G-2)."
    )


# ══════════════════════════════════════════════════════════════════════════════
# AC6 — Page NIJE singleton (add/delete ZADRŽANI — REGRESSION LOCK)
# ══════════════════════════════════════════════════════════════════════════════
# AC-6: has_add_permission / has_delete_permission stay True (NOT overridden like SiteSettingsAdmin)
def test_ac6_not_singleton_permissions():
    from django.test import RequestFactory

    model_admin = _page_admin()
    req = RequestFactory().get("/")
    # Default ModelAdmin.has_add/has_delete reads request.user.has_perm → attach a superuser.
    from django.contrib.auth import get_user_model

    req.user = get_user_model()(is_superuser=True, is_staff=True, is_active=True)
    assert model_admin.has_add_permission(req) is True, (
        "PageAdmin.has_add_permission MORA biti True (NIJE singleton; RAZLIKA od "
        "SiteSettingsAdmin — AC6/SM-D9/G-8)."
    )
    assert model_admin.has_delete_permission(req) is True, (
        "PageAdmin.has_delete_permission MORA biti True (NIJE singleton; AC6/SM-D9)."
    )


# AC-6: multiple Page rows coexist (NO singleton save() pk=1 coercion; changelist 200 with N rows)
def test_ac6_multiple_pages_coexist(client, superuser):
    Page = _Page()
    Page.objects.create(slug="prva-info", title_sr="Prva info")
    Page.objects.create(slug="druga-info", title_sr="Druga info")
    assert Page.objects.filter(slug__in=("prva-info", "druga-info")).count() == 2, (
        "Page NIJE singleton — 2 različita slug-a MORAJU koegzistirati (AC6/SM-D9)."
    )
    client.force_login(superuser)
    resp = client.get(reverse("admin:pages_page_changelist"))
    assert resp.status_code == 200, (
        f"changelist sa N redova MORA biti 200 (NE redirect-na-jedini-objekat kao singleton; "
        f"AC6); dobio {resp.status_code}."
    )


# ══════════════════════════════════════════════════════════════════════════════
# AC7 — view_on_site default (NE False — Page IMA radni get_absolute_url)
# ══════════════════════════════════════════════════════════════════════════════
# AC-7: view_on_site stays default (NOT set to False) — Page URL resolves (SM-D7)
def test_ac7_view_on_site_default_not_false():
    assert _page_admin().view_on_site is not False, (
        "PageAdmin.view_on_site MORA biti default (NIJE False) — Page IMA radni get_absolute_url "
        "(pages:page_detail registrovan 7-4); RAZLIKA od 8.4 Series / 8.5 Subcategory (AC7/SM-D7)."
    )


# AC-7 (positive smoke / TEST_GAP): for a saved Page the admin change-view exposes a working
# "View on site" affordance pointing at get_absolute_url. Robust: assert the absolute_url string
# appears in the change-view response, OR a view_on_site anchor/link is rendered. Defensive fallback:
# if neither (config reason), assert get_absolute_url itself resolves 200-capable + leave a note.
def test_ac7_view_on_site_link_renders_in_change_view(client, superuser):
    page = _make_page(slug="o-nama", title="O nama")
    abs_url = page.get_absolute_url()
    client.force_login(superuser)
    resp = client.get(reverse("admin:pages_page_change", args=[page.pk]))
    assert resp.status_code == 200, (
        f"change-view MORA biti 200 (AC1/AC7); dobio {resp.status_code}."
    )
    html = resp.content.decode()
    # Django renders the "View on site" affordance as <a ... class="viewsitelink"> with
    # href=admin:view_on_site(content_type, pk) → 302 → get_absolute_url. The change-view markup
    # may carry either the resolved absolute_url OR the viewsitelink/view-on-site anchor.
    has_affordance = (
        abs_url in html
        or "viewsitelink" in html
        or 'href="/admin-coric/r/' in html  # admin:view_on_site shortcut route
        or "view-on-site" in html
        or "viewlink" in html
    )
    if has_affordance:
        # If the viewsitelink anchor is present, prove its redirect target resolves to the page.
        from django.contrib.contenttypes.models import ContentType

        ct = ContentType.objects.get_for_model(_Page())
        vos_url = reverse("admin:view_on_site", args=[ct.pk, page.pk])
        vos_resp = client.get(vos_url)
        assert vos_resp.status_code == 302, (
            f"admin:view_on_site MORA 302 ka get_absolute_url (AC7/SM-D7); dobio {vos_resp.status_code}."
        )
        assert abs_url in vos_resp["Location"], (
            f"view_on_site redirect MORA voditi na get_absolute_url ({abs_url!r}); "
            f"Location={vos_resp['Location']!r}."
        )
    else:
        # Defensive fallback (NOTE): admin nije renderovao link iz config razloga — bar dokaži
        # da get_absolute_url razrešava 200-capable (pages:page_detail registrovan 7-4).
        front_resp = client.get(abs_url, HTTP_HOST="localhost")
        assert front_resp.status_code == 200, (
            f"get_absolute_url ({abs_url!r}) MORA biti 200-capable (AC7/SM-D7) čak i ako admin "
            f"affordance nije renderovan; dobio {front_resp.status_code}."
        )


# ══════════════════════════════════════════════════════════════════════════════
# AC8 — RBAC verify (NE re-grant) + anon redirect + CSRF
# ══════════════════════════════════════════════════════════════════════════════
# AC-8: Editor can access pages.Page changelist (8.2 EDITOR_CONTENT_MODELS lock — verify, NOT re-grant)
def test_ac8_editor_can_access_page_changelist(client, editor):
    client.force_login(editor)
    resp = client.get(reverse("admin:pages_page_changelist"))
    assert resp.status_code == 200, (
        f"Editor Page changelist MORA biti 200 (8.2 grant ('pages','page') netaknut — verify, "
        f"NE re-grant; AC8/SM-D8); dobio {resp.status_code}."
    )


# AC-8: pages.sitesettings is NOT in the Editor allowlist (Superadmin-only — verify, NE menjaj)
def test_ac8_sitesettings_not_in_editor_allowlist():
    from apps.accounts.permissions import EDITOR_CONTENT_MODELS

    assert ("pages", "page") in EDITOR_CONTENT_MODELS, (
        "('pages','page') MORA OSTATI u EDITOR_CONTENT_MODELS (8.2 grant; AC8/SM-D8)."
    )
    assert ("pages", "sitesettings") not in EDITOR_CONTENT_MODELS, (
        "('pages','sitesettings') NE SME biti u Editor allowlist-u (Superadmin-only; "
        "NE dodavati — 8.9 odluka; AC8/SM-D8)."
    )


# AC-8 (negative / security): anonymous → 302 admin login (NOT 200, NOT 500)
def test_ac8_anonymous_redirected_to_login(client):
    resp = client.get(reverse("admin:pages_page_changelist"))
    assert resp.status_code == 302, (
        f"Anoniman na Page changelist MORA biti 302 (admin login redirect — AC8); "
        f"dobio {resp.status_code}."
    )
    assert reverse("admin:login") in resp["Location"], (
        f"302 MORA voditi na admin:login (admin na bare /admin-coric/ iz 8.1); "
        f"Location={resp['Location']!r}."
    )


# AC-8 (security / CSRF): admin POST without CSRF token → 403
def test_ac8_admin_post_without_csrf_forbidden(superuser):
    from django.test import Client

    csrf_client = Client(enforce_csrf_checks=True)
    csrf_client.force_login(superuser)
    resp = csrf_client.post(
        reverse("admin:pages_page_add"),
        {"title_sr": "Bez CSRF", "slug": "bez-csrf"},
    )
    assert resp.status_code == 403, (
        f"Admin POST bez CSRF token-a MORA biti 403 (CSRF enforced — AC8/security); "
        f"dobio {resp.status_code}."
    )


# ══════════════════════════════════════════════════════════════════════════════
# AC9 — title_sr bezuslovno obavezan (modeltranslation required-promotion — NE relaksiraj)
# ══════════════════════════════════════════════════════════════════════════════
# AC-9: title_sr is required on the admin-built form (required-promotion NOT relaxed)
def test_ac9_title_sr_required_on_admin_form():
    from django.contrib.auth.models import AnonymousUser
    from django.test import RequestFactory

    model_admin = _page_admin()
    req = RequestFactory().get("/")
    req.user = AnonymousUser()
    form_cls = model_admin.get_form(req)
    assert form_cls.base_fields["title_sr"].required is True, (
        "title_sr MORA biti obavezno na admin PageForm-u (model `title` blank=False + sr default "
        "lang → TranslationAdmin required-promotion); promotion se NE relaksira (AC9/G-6)."
    )


# AC-9 (graceful): empty title_sr on add → 200 form-error on title_sr, NO new Page (NOT 500)
def test_ac9_empty_title_sr_graceful_form_error(client, superuser):
    Page = _Page()
    before = Page.objects.count()
    client.force_login(superuser)
    url = reverse("admin:pages_page_add")
    data = _scrape_change_form(client.get(url).content.decode())
    data["title_sr"] = ""
    data["slug"] = "prazan-naslov"
    resp = client.post(url, data)
    assert resp.status_code == 200, (
        f"Prazan title_sr MORA dati graceful 200 form-error (NIKAD 400/500 iz model full_clean "
        f"escape — AC9/G-6); dobio {resp.status_code}."
    )
    form = resp.context["adminform"].form
    assert "title_sr" in form.errors, (
        f"Prazan title_sr MORA dati field grešku na `title_sr` (required); dobio {form.errors!r}."
    )
    assert Page.objects.count() == before, (
        "Nijedan NOV Page NE SME biti kreiran kad je title_sr prazan (AC9/G-6)."
    )


# AC-9 (edge): whitespace-only title_sr rejected (NOT silently accepted as blank-bypass)
def test_ac9_whitespace_title_sr_rejected(client, superuser):
    Page = _Page()
    before = Page.objects.count()
    client.force_login(superuser)
    url = reverse("admin:pages_page_add")
    data = _scrape_change_form(client.get(url).content.decode())
    data["title_sr"] = "   "
    data["slug"] = "whitespace-naslov"
    resp = client.post(url, data)
    assert resp.status_code == 200, (
        f"Whitespace-only title_sr MORA dati graceful 200 (NE 500); dobio {resp.status_code}."
    )
    assert Page.objects.count() == before, (
        "Whitespace-only title_sr NE SME kreirati Page (Django strip → prazno → required; AC9)."
    )


# AC-9 (positive): valid title_sr + slug → 302 redirect, Page created
def test_ac9_valid_page_creates(client, superuser):
    Page = _Page()
    client.force_login(superuser)
    url = reverse("admin:pages_page_add")
    data = _scrape_change_form(client.get(url).content.decode())
    data["title_sr"] = "Validna Statička Strana"
    data["slug"] = "validna-staticka-strana"
    data["body_sr"] = "<p>Telo.</p>"
    resp = client.post(url, data)
    assert resp.status_code == 302, (
        f"Validan title_sr + slug MORA sačuvati Page i dati 302 (AC9); dobio {resp.status_code}."
    )
    assert Page.objects.filter(slug="validna-staticka-strana").exists(), (
        "Validan Page sa title_sr + slug MORA biti kreiran (AC9)."
    )


# ══════════════════════════════════════════════════════════════════════════════
# AC10 — 0 migracija accounting (admin-only = 0 migracija očekivano)
# ══════════════════════════════════════════════════════════════════════════════
# AC-10: no pending schema migration for apps.pages (admin-only story; body stays TextField)
def test_ac10_no_pending_migration_for_pages():
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
    assert "pages" not in changes, (
        f"apps.pages NE SME imati pending schema migraciju (8.8 je admin-only; body ostaje plain "
        f"TextField; epics:1161-1164 model-proširenja DEFER — SM-D1/AC10); "
        f"autodetector predlaže: {changes.get('pages')}."
    )
