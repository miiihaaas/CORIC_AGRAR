"""Story 7.4 — Politika privatnosti (generički Page model) statičke strane (TEA RED).

ČETVRTA i POSLEDNJA story Epic 7 (GDPR & Privacy). Uvodi generički `Page` model
(apps/pages), javnu slug-routed `/sr/politika-privatnosti/` stranu, Lorem Ipsum
seed (PLACEHOLDER), i „pravni" footer red sa linkovima ka OBE politike
(privatnost = NOVA `pages:page_detail` ruta; kolačići = POSTOJEĆA `gdpr:cookie_policy`).

Pokriva sve scenarije iz `## Testing` sekcije + AC1-AC10:
- Model (Page polja, get_absolute_url, __str__, NIJE singleton)
- Translation (title/body _sr/_hu/_en + sr fallback)
- Migracije (0004 seed SAMO privatnost, idempotent, reversible, PLACEHOLDER marker)
- View (200 sr/hu/en, POST 405, 404 nepostojeći, G-1 collision guard)
- AC10 cross-include lock (gdpr/blog/search nisu shadow-ovani — CRITICAL-1)
- Admin (registrovan, changelist/add/change 200, NIJE singleton)
- Template XSS (<script> escape-ovan, NIKAD |safe)
- Footer (oba linka + regression 4 kolone + šišana-latinica fix G-13)

⚠️ COLLECTION-SAFETY: `apps.pages.models.Page` JOŠ NE postoji (RED faza). Svi
importi `Page`/migracija su UNUTAR test funkcija → missing model daje per-test
FAIL (ImportError/AttributeError/404), NE collection-abort cele suite.

Refs:
- 7-4-...-staticke-strane.md AC1-AC10 + Testing + SM-D1..D11 + Gotcha G-1..G-15
- 7-4-interface-contract.md (kanonski ugovor — Dev MORA satisfy)
- apps/gdpr/tests/* (mirror: test_views/test_xss/test_admin/test_data_migration)
"""

from __future__ import annotations

import re
from importlib import import_module

import pytest
from django.utils.translation import override

pytestmark = pytest.mark.django_db

# Public rute pod i18n_patterns (slug ASCII — G-10).
PRIVACY_PATH_SR = "/sr/politika-privatnosti/"
PRIVACY_PATH_HU = "/hu/politika-privatnosti/"
PRIVACY_PATH_EN = "/en/politika-privatnosti/"
COOKIE_PATH_SR = "/sr/politika-kolacica/"
BLOG_PATH_SR = "/sr/blog/"
SEARCH_PATH_SR = "/sr/pretraga/"
NONEXISTENT_PATH_SR = "/sr/nepostojeca-strana/"
PRIVACY_SLUG = "politika-privatnosti"
COOKIE_SLUG = "politika-kolacica"


@pytest.fixture
def superuser(django_user_model):
    """Superuser za admin changelist/add/change smoke (AC6).

    `django_user_model` = settings.AUTH_USER_MODEL kroz get_user_model() —
    NIKAD direktan `from django.contrib.auth.models import User`.
    """
    return django_user_model.objects.create_superuser(
        username="pages_admin_tea",
        email="pages-admin@example.com",
        password="tea-pass-12345",
    )


def _Page():
    """Lazy import — RED faza: Page NE postoji → ImportError/AttributeError."""
    from apps.pages.models import Page

    return Page


def _make_page(slug=PRIVACY_SLUG, title="Politika privatnosti", body="Telo strane."):
    Page = _Page()
    # update_or_create (NE get_or_create): data-seed migracija (0004) AUTO-popunjava
    # Page(slug='politika-privatnosti') u test DB, pa get_or_create NE bi nikad
    # ažurirao title/body koje test traži (vraćao bi PLACEHOLDER seed red). Mirror
    # gdpr test_views._seed_sr „NE oslanja se na data seed" determinizam.
    page, _created = Page.objects.update_or_create(
        slug=slug, defaults={"title_sr": title, "body_sr": body}
    )
    return page


# ─────────────────────────────────────────────────────────────────────────────
# Model — Page polja / get_absolute_url / __str__ / NIJE singleton
# ─────────────────────────────────────────────────────────────────────────────


# AC-1: Page nasleđuje TimestampedModel (created_at/updated_at)
def test_page_inherits_timestamped():
    page = _make_page()
    assert page.created_at is not None and page.updated_at is not None, (
        "Page MORA nasleđivati TimestampedModel (created_at/updated_at; AC1)."
    )


# AC-1: Page polja slug (unique/db_index) + title + body (blank) postoje
def test_page_fields_exist():
    Page = _Page()
    field_names = {f.name for f in Page._meta.get_fields()}
    assert {"slug", "title", "body"} <= field_names, (
        f"Page MORA imati slug/title/body polja (AC1), ima {field_names!r}."
    )
    slug_field = Page._meta.get_field("slug")
    assert slug_field.unique, "Page.slug MORA biti unique (AC1)."
    assert slug_field.db_index, "Page.slug MORA imati db_index=True (AC1)."
    assert Page._meta.get_field("body").blank, "Page.body MORA biti blank=True (AC1)."


# AC-1: get_absolute_url == reverse('pages:page_detail', slug=...)
def test_get_absolute_url():
    from django.urls import reverse

    page = _make_page()
    with override("sr"):
        expected = reverse("pages:page_detail", kwargs={"slug": page.slug})
        assert page.get_absolute_url() == expected, (
            f"get_absolute_url MORA == reverse('pages:page_detail', slug=...) (AC1), "
            f"dobio {page.get_absolute_url()!r} vs {expected!r}."
        )


# AC-1: __str__ vraća title kad postoji, inače slug
def test_str_returns_title_or_slug():
    Page = _Page()
    with_title = Page(slug="ima-naslov", title="Ima Naslov")
    assert str(with_title) == "Ima Naslov", "__str__ MORA vratiti title kad postoji (AC1)."
    without_title = Page(slug="bez-naslova", title="")
    assert str(without_title) == "bez-naslova", (
        "__str__ MORA fallback-ovati na slug kad je title prazan (AC1)."
    )


# AC-1: Page NIJE singleton — može VIŠE redova (count==2), bez save() pk=1 prisile
def test_page_is_not_singleton():
    Page = _Page()
    Page.objects.create(slug="prva", title_sr="Prva")
    Page.objects.create(slug="druga", title_sr="Druga")
    # >= 2 (NE == 2): data-seed (0004) AUTO-kreira Page(slug='politika-privatnosti')
    # u test DB (test_0004_seed_creates_privacy_page tvrdi da postoji), pa apsolutni
    # count uključuje i seed red. Suština AC1 ostaje: 2 RAZLIČITA nova slug-a MORAJU
    # koegzistirati (NEMA save() pk=1 prisile singleton-a).
    assert Page.objects.filter(slug__in=("prva", "druga")).count() == 2, (
        "Page NIJE singleton — 2 različita slug-a MORAJU koegzistirati (AC1; NEMA "
        f"save() pk=1), dobio {Page.objects.filter(slug__in=('prva', 'druga')).count()}."
    )
    assert Page.objects.count() >= 2, (
        f"Page NIJE singleton — count() MORA biti >= 2, dobio {Page.objects.count()}."
    )
    # NEMA singleton recepta (RAZLIKA od CookiePolicy/SiteSettings — G-8)
    assert not hasattr(Page, "load"), "Page NE SME imati load() classmethod (NIJE singleton; AC1)."


# ─────────────────────────────────────────────────────────────────────────────
# Translation — title/body _sr/_hu/_en + sr fallback
# ─────────────────────────────────────────────────────────────────────────────


# AC-4: title_sr/_hu/_en + body_sr/_hu/_en kolone postoje (modeltranslation)
def test_translated_fields_exist():
    Page = _Page()
    field_names = {f.name for f in Page._meta.get_fields()}
    for base in ("title", "body"):
        for lang in ("sr", "hu", "en"):
            assert f"{base}_{lang}" in field_names, (
                f"Page MORA imati {base}_{lang} kolonu (modeltranslation; AC4/G-7)."
            )


# AC-4: slug NIJE translatable (jezik-neutralan ASCII)
def test_slug_not_translatable():
    Page = _Page()
    field_names = {f.name for f in Page._meta.get_fields()}
    for lang in ("sr", "hu", "en"):
        assert f"slug_{lang}" not in field_names, (
            f"slug_{lang} NE SME postojati — slug je ASCII jezik-neutralan (AC4)."
        )


# AC-4: per-locale vrednosti čitljive pod translation.override
def test_per_locale_values():
    Page = _Page()
    page = Page.objects.create(
        slug="visejezicna",
        title_sr="Naslov SR",
        title_hu="Cím HU",
        title_en="Title EN",
    )
    with override("sr"):
        assert page.title == "Naslov SR", "Pod sr context-om title MORA biti _sr (AC4)."
    with override("hu"):
        assert page.title == "Cím HU", "Pod hu context-om title MORA biti _hu (AC4)."
    with override("en"):
        assert page.title == "Title EN", "Pod en context-om title MORA biti _en (AC4)."


# AC-4/AC-7: prazno _hu → fallback na _sr (MODELTRANSLATION_FALLBACK_LANGUAGES=("sr",))
def test_fallback_to_sr():
    Page = _Page()
    page = Page.objects.create(
        slug="samo-sr", title_sr="Samo srpski naslov", title_hu="", title_en=""
    )
    with override("hu"):
        assert page.title == "Samo srpski naslov", (
            "Prazan title_hu MORA fallback-ovati na title_sr "
            "(MODELTRANSLATION_FALLBACK_LANGUAGES=('sr',); AC4/AC7)."
        )


# ─────────────────────────────────────────────────────────────────────────────
# Migracije — 0004 seed SAMO privatnost, idempotent, reversible, PLACEHOLDER
# ─────────────────────────────────────────────────────────────────────────────


def _import_seed_module():
    try:
        return import_module("apps.pages.migrations.0004_seed_privacy_policy")
    except ImportError:
        pytest.fail(
            "Migration 'apps.pages.migrations.0004_seed_privacy_policy' nije pronađen. "
            "Dev MORA kreirati RunPython data seed migraciju (AC5/SM-D5)."
        )


def _seed_callables(module):
    """Vrati (forward_fn, reverse_fn) iz RunPython operacije ili modul-level funkcija."""
    forward_fn = reverse_fn = None
    for cand in ("seed_privacy_policy", "forward", "seed", "forward_code"):
        forward_fn = getattr(module, cand, None)
        if callable(forward_fn):
            break
        forward_fn = None
    for cand in ("reverse_seed", "reverse", "reverse_code", "unseed_privacy_policy"):
        reverse_fn = getattr(module, cand, None)
        if callable(reverse_fn):
            break
        reverse_fn = None
    from django.db.migrations.operations import RunPython

    for op in module.Migration.operations:
        if isinstance(op, RunPython):
            if forward_fn is None and op.code is not None:
                forward_fn = op.code
            if reverse_fn is None and op.reverse_code is not None:
                reverse_fn = op.reverse_code
    return forward_fn, reverse_fn


class _StubSchemaEditor:
    """No-op schema editor stub za direktan poziv RunPython forward/reverse callable-a."""


def _ensure_seed_applied():
    """Re-primeni 0004 forward seed (idempotentan) → garantuje da privacy Page red
    postoji NEZAVISNO od redosleda izvršavanja testova (test_0004_reverse_... briše
    isti red; pytest NE garantuje redosled). get_or_create na unique slug → no-op
    ako red već postoji."""
    from django.apps import apps as django_apps

    module = _import_seed_module()
    forward_fn, _reverse_fn = _seed_callables(module)
    assert forward_fn is not None, "0004 MORA imati RunPython forward callable (AC5)."
    forward_fn(django_apps, _StubSchemaEditor())


# AC-5: posle migrate, privacy Page postoji sa popunjenim _sr (auto-applied seed)
def test_0004_seed_creates_privacy_page():
    Page = _Page()
    _ensure_seed_applied()  # order-independent: re-primeni seed pre asercije
    page = Page.objects.filter(slug=PRIVACY_SLUG).first()
    assert page is not None, (
        "Posle migracija (0004 seed auto-applied) MORA postojati Page(slug="
        "'politika-privatnosti') — 'postoji pre prvog deploy-a' (AC5/epics.md:1048)."
    )
    assert (page.title_sr or "").strip() != "", "Seed MORA popuniti title_sr (G-2/AC5)."
    assert (page.body_sr or "").strip() != "", "Seed MORA popuniti body_sr (G-2/AC5)."


# AC-2/AC-5: 0004 forward NE seed-uje politika-kolacica (SM-D1 — gdpr je vlasnik)
def test_0004_seed_does_not_create_cookie_policy_page():
    Page = _Page()
    assert not Page.objects.filter(slug=COOKIE_SLUG).exists(), (
        "Seed NE SME kreirati Page(slug='politika-kolacica') — gdpr.CookiePolicy je "
        "AUTORITATIVAN (SM-D1/AC2). Dva izvora istine = zabranjeno."
    )


# AC-5/G-15: seed body_sr sadrži eksplicitan PLACEHOLDER marker (RISK-1 mitigacija)
def test_0004_seed_body_has_placeholder_marker():
    Page = _Page()
    page = Page.objects.get(slug=PRIVACY_SLUG)
    assert "PLACEHOLDER" in (page.body_sr or "").upper(), (
        "Seed body_sr MORA sadržati eksplicitan PLACEHOLDER marker (G-15/RISK-1) da niko "
        "ne deploy-uje Lorem placeholder kao pravu politiku privatnosti."
    )


# AC-5: 0004 forward idempotentan (get_or_create na unique slug — re-run NE duplira; G-8)
def test_0004_seed_idempotent():
    from django.apps import apps as django_apps

    Page = _Page()
    module = _import_seed_module()
    forward_fn, _reverse_fn = _seed_callables(module)
    assert forward_fn is not None, "0004 MORA imati RunPython forward callable (AC5)."

    # order-independent: garantuj da seed red postoji (test_0004_reverse_... ga briše).
    _ensure_seed_applied()
    count_before = Page.objects.filter(slug=PRIVACY_SLUG).count()
    forward_fn(django_apps, _StubSchemaEditor())  # re-run forward
    assert Page.objects.filter(slug=PRIVACY_SLUG).count() == count_before == 1, (
        "0004 forward MORA biti idempotentan (get_or_create na unique slug; G-8) — "
        f"re-run NE sme duplirati, count pre={count_before}, "
        f"posle={Page.objects.filter(slug=PRIVACY_SLUG).count()}."
    )


# AC-5: 0004 reverse_code briše privacy red (filter(slug=...).delete())
def test_0004_reverse_deletes_privacy_page():
    from django.apps import apps as django_apps

    Page = _Page()
    module = _import_seed_module()
    _forward_fn, reverse_fn = _seed_callables(module)
    assert reverse_fn is not None, (
        "0004 RunPython MORA imati reverse_code definisan (NE noop; AC5/SM-D5)."
    )

    # order-independent: garantuj precondition (seed red postoji) bez oslanjanja na
    # auto-applied migraciju koju je možda već obrisao raniji reverse poziv.
    _ensure_seed_applied()
    assert Page.objects.filter(slug=PRIVACY_SLUG).exists(), "Seed red mora postojati pre reverse-a."
    reverse_fn(django_apps, _StubSchemaEditor())
    assert not Page.objects.filter(slug=PRIVACY_SLUG).exists(), (
        "reverse_code MORA obrisati privacy red (filter(slug=...).delete(); AC5/SM-D5)."
    )


# AC-5: 0004 dependencies → ("pages","0003_page") (G-14 — stvarno ime 0003)
def test_0004_depends_on_0003():
    module = _import_seed_module()
    deps = list(module.Migration.dependencies)
    assert any(app == "pages" and name.startswith("0003") for app, name in deps), (
        f"0004 dependencies MORA imati ('pages','0003_...') (AC5/G-14), dobio {deps}."
    )


# AC-5/G-7: 0003 CreateModel('Page') ima translated kolone; slug/timestamp BEZ _sr/hu/en
def test_0003_createmodel_translated_columns():
    from django.db import migrations

    mod = import_module("apps.pages.migrations.0003_page")
    op = None
    for candidate in mod.Migration.operations:
        if isinstance(candidate, migrations.CreateModel) and candidate.name == "Page":
            op = candidate
            break
    assert op is not None, "0003 MORA imati CreateModel('Page') (AC5)."
    field_names = {name for name, _ in op.fields}
    for base in ("title", "body"):
        for lang in ("sr", "hu", "en"):
            assert f"{base}_{lang}" in field_names, (
                f"0003 MORA imati {base}_{lang} kolonu (modeltranslation; AC5/G-7)."
            )
    assert {"slug", "created_at", "updated_at"} <= field_names, (
        "0003 MORA imati slug + created_at/updated_at (AC5)."
    )
    for base in ("slug", "created_at", "updated_at"):
        for lang in ("sr", "hu", "en"):
            assert f"{base}_{lang}" not in field_names, (
                f"{base}_{lang} NE SME postojati — {base} je jezik-neutralan (AC5)."
            )


# ─────────────────────────────────────────────────────────────────────────────
# View — 200 sr/hu/en, POST 405, 404 nepostojeći, G-1 collision guard
# ─────────────────────────────────────────────────────────────────────────────


# AC-7: GET /sr/politika-privatnosti/ → 200 + template + <h1> title + body |linebreaks
def test_privacy_page_200_sr(client):
    _make_page(title="Politika privatnosti", body="Prvi red.\nDrugi red.")
    response = client.get(PRIVACY_PATH_SR, HTTP_HOST="localhost")
    assert response.status_code == 200, (
        f"GET {PRIVACY_PATH_SR} MORA biti 200 (AC7), dobio {response.status_code}."
    )
    template_names = [t.name for t in response.templates if t.name]
    assert "pages/page-detail.html" in template_names, (
        f"Render MORA koristiti 'pages/page-detail.html' (AC7), dobio {template_names!r}."
    )
    html = response.content.decode("utf-8")
    assert "Politika privatnosti" in html, "<h1> MORA sadržati page.title (AC7)."
    assert "Prvi red." in html and "Drugi red." in html, (
        "Telo MORA renderovati page.body kroz |linebreaks (AC7)."
    )


# AC-7/AC-8: body je STVARNO renderovan kroz |linebreaks (dvolinijski body → <br> ILI <p>
# struktura), ne samo da je tekst prisutan. Django |linebreaks pretvara jednostruki \n u
# <br> unutar <p>, a dvostruki \n\n u zasebne <p> paragrafe.
def test_body_rendered_through_linebreaks(client):
    _make_page(body="Prvi red.\nDrugi red.\n\nNovi paragraf.")
    response = client.get(PRIVACY_PATH_SR, HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")
    # Jednostruki \n unutar paragrafa → <br>
    assert "Prvi red.<br>" in html or "Prvi red.<br />" in html, (
        "|linebreaks MORA pretvoriti jednostruki \\n u <br> (AC7/AC8) — body NIJE "
        f"renderovan kroz |linebreaks. HTML fragment: {html[html.find('Prvi red.'):html.find('Prvi red.') + 60]!r}"
    )
    # Dvostruki \n\n → zaseban <p> paragraf
    assert "<p>Novi paragraf.</p>" in html, (
        "|linebreaks MORA pretvoriti \\n\\n u zaseban <p> paragraf (AC7/AC8)."
    )


# AC-7: <title> blok sadrži page.title
def test_privacy_page_title_block(client):
    _make_page(title="Naslov u title bloku")
    response = client.get(PRIVACY_PATH_SR, HTTP_HOST="localhost")
    assert response.status_code == 200
    m = re.search(r"<title>(.*?)</title>", response.content.decode("utf-8"), re.I | re.S)
    assert m and "Naslov u title bloku" in m.group(1), (
        "<title> MORA sadržati page.title ({% block title %}; AC7)."
    )


# AC-7: GET /hu/politika-privatnosti/ → 200 (sr fallback; seed SAMO _sr)
def test_privacy_page_200_hu(client):
    _make_page(title="Politika privatnosti SR", body="Srpski sadržaj za HU fallback.")
    response = client.get(PRIVACY_PATH_HU, HTTP_HOST="localhost")
    assert response.status_code == 200, (
        f"GET {PRIVACY_PATH_HU} MORA biti 200 (AC7), dobio {response.status_code}."
    )
    html = response.content.decode("utf-8")
    assert "Politika privatnosti SR" in html, (
        "hu strana MORA prikazati sr fallback title (MODELTRANSLATION_FALLBACK_"
        "LANGUAGES=('sr',); AC7) — hu se NE seed-uje."
    )


# AC-7: GET /en/politika-privatnosti/ → 200 (sr fallback)
def test_privacy_page_200_en(client):
    _make_page(title="Politika privatnosti SR-EN", body="Srpski sadržaj za EN fallback.")
    response = client.get(PRIVACY_PATH_EN, HTTP_HOST="localhost")
    assert response.status_code == 200, (
        f"GET {PRIVACY_PATH_EN} MORA biti 200 (AC7), dobio {response.status_code}."
    )
    assert "Politika privatnosti SR-EN" in response.content.decode("utf-8"), (
        "en strana MORA prikazati sr fallback title (AC7)."
    )


# AC-7/G-12: POST /sr/politika-privatnosti/ → 405 (GET-only http_method_names)
def test_post_returns_405(client):
    _make_page()
    response = client.post(PRIVACY_PATH_SR, HTTP_HOST="localhost")
    assert response.status_code == 405, (
        "PageDetailView je GET-only — POST MORA biti 405 (http_method_names izostavlja "
        f"post; AC7/G-12), dobio {response.status_code}."
    )


# AC-7/G-12: HEAD /sr/politika-privatnosti/ → 200 (PageDetailView dozvoljava head)
def test_head_returns_200(client):
    _make_page()
    response = client.head(PRIVACY_PATH_SR, HTTP_HOST="localhost")
    assert response.status_code == 200, (
        "PageDetailView dozvoljava HEAD (http_method_names sadrži 'head') — "
        f"HEAD MORA biti 200 (AC7/G-12), dobio {response.status_code}."
    )


# AC-7: GET /sr/nepostojeca-strana/ → 404 (nema Page reda)
def test_nonexistent_slug_404(client):
    response = client.get(NONEXISTENT_PATH_SR, HTTP_HOST="localhost")
    assert response.status_code == 404, (
        f"GET {NONEXISTENT_PATH_SR} (nema Page reda) MORA biti 404 (AC7), "
        f"dobio {response.status_code}."
    )


# AC-2/G-1: PageDetailView baca Http404 na slug='politika-kolacica' — ČAK i kad Page red postoji
def test_g1_cookie_policy_slug_404_via_pagedetailview():
    """G-1 collision guard: čak i ručno kreiran Page(slug='politika-kolacica') NE SME
    biti serviran kroz PageDetailView (gdpr je vlasnik; SM-D1).

    ⚠️ KRITIČNO (zašto NE preko HTTP klijenta): posle CRITICAL-1 reorder-a
    `reverse('pages:page_detail', slug='politika-kolacica')` daje TAČNO
    `/sr/politika-kolacica/` — istu URL-u koju POSEDUJE gdpr include (sada PRE
    pages-a u i18n_patterns). Zato `client.get(<ta-URL>)` resolve-uje na
    `gdpr.CookiePolicyView` → 200, i NIKAD ne dosegne PageDetailView (G-1 guard
    se uopšte ne izvrši). HTTP-level test bi bio UNSATISFIABLE protiv ispravne
    produkcije (tražio bi 404 na URL-i koja je legitimno 200).

    Zbog toga G-1 guard testiramo NA NIVOU VIEW-a direktno (RequestFactory +
    PageDetailView.as_view() sa slug kwarg-om) i tvrdimo da diže `Http404` — to
    je JEDINI način da se boundary guard stvarno izvrši. (AC2/SM-D1/G-1.)
    """
    from django.http import Http404
    from django.test import RequestFactory

    from apps.pages.views import PageDetailView

    # Ručno kreiran kolizioni red — guard MORA baciti Http404 i pored njega.
    _make_page(slug=COOKIE_SLUG, title="Pokušaj dupliranja", body="x")
    request = RequestFactory().get("/")
    view = PageDetailView.as_view()
    with pytest.raises(Http404):
        view(request, slug=COOKIE_SLUG)


# ─────────────────────────────────────────────────────────────────────────────
# AC10 — CROSS-INCLUDE neshadow-ovanje (CRITICAL-1 regression lock)
# ─────────────────────────────────────────────────────────────────────────────


# AC-10: GET /sr/politika-kolacica/ → 200 (gdpr cookie policy NIJE shadow-ovan)
def test_cookie_policy_still_200(client):
    response = client.get(COOKIE_PATH_SR, HTTP_HOST="localhost")
    assert response.status_code == 200, (
        f"GET {COOKIE_PATH_SR} MORA biti 200 — pages catch-all NE SME shadow-ovati gdpr "
        f"cookie policy (CRITICAL-1/AC10/SM-D11), dobio {response.status_code}."
    )


# AC-10: GET /sr/blog/ → 200 (blog index NIJE shadow-ovan)
def test_blog_index_still_200(client):
    response = client.get(BLOG_PATH_SR, HTTP_HOST="localhost")
    assert response.status_code == 200, (
        f"GET {BLOG_PATH_SR} MORA biti 200 — pages catch-all NE SME shadow-ovati blog "
        f"index (CRITICAL-1/AC10), dobio {response.status_code}."
    )


# AC-10: /sr/pretraga/ resolve-uje na search view (NIJE shadow-ovana)
def test_search_still_resolves():
    from django.urls import resolve

    match = resolve(SEARCH_PATH_SR)
    assert match.view_name == "search:results", (
        f"{SEARCH_PATH_SR} MORA resolve-ovati na 'search:results' (NIJE shadow-ovana pages "
        f"catch-all-om; AC10), dobio view_name={match.view_name!r}."
    )


# AC-10: resolve() ownership — politika-kolacica pripada gdpr, blog pripada blog
def test_resolve_ownership():
    from django.urls import resolve

    cookie_match = resolve(COOKIE_PATH_SR)
    assert cookie_match.func.__module__.startswith("apps.gdpr"), (
        f"{COOKIE_PATH_SR} MORA pripadati apps.gdpr (NE pages.PageDetailView; AC10), "
        f"dobio module={cookie_match.func.__module__!r}."
    )
    blog_match = resolve(BLOG_PATH_SR)
    assert blog_match.func.__module__.startswith("apps.blog"), (
        f"{BLOG_PATH_SR} MORA pripadati apps.blog (AC10), "
        f"dobio module={blog_match.func.__module__!r}."
    )


# AC-3: home /sr/ i statičke pages rute NISU shadow-ovane catch-all-om
def test_home_and_static_pages_not_shadowed():
    from django.urls import resolve

    home_match = resolve("/sr/")
    assert home_match.view_name == "pages:home", (
        f"/sr/ MORA i dalje resolve-ovati na pages:home (prazan path; AC3), "
        f"dobio {home_match.view_name!r}."
    )
    about_match = resolve("/sr/o-nama/")
    assert about_match.view_name == "pages:about", (
        f"/sr/o-nama/ NE SME biti shadow-ovan catch-all-om unutar pages.urls (G-3/AC3), "
        f"dobio {about_match.view_name!r}."
    )


# AC-3: reverse('pages:page_detail', slug='politika-privatnosti') == /sr/politika-privatnosti/
def test_page_detail_url_reverse_sr():
    from django.urls import NoReverseMatch, reverse

    with override("sr"):
        try:
            url = reverse("pages:page_detail", kwargs={"slug": PRIVACY_SLUG})
        except NoReverseMatch:
            pytest.fail("pages:page_detail ruta MORA postojati (AC3/SM-D3) — RED dok Dev ne doda.")
    assert url == PRIVACY_PATH_SR, (
        f"reverse('pages:page_detail', slug='{PRIVACY_SLUG}') pod sr MORA biti "
        f"{PRIVACY_PATH_SR!r} (i18n_patterns prefiks; AC3), dobio {url!r}."
    )


# ─────────────────────────────────────────────────────────────────────────────
# Admin — registrovan, changelist/add/change 200, NIJE singleton
# ─────────────────────────────────────────────────────────────────────────────


# AC-6: Page registrovan na admin.site kao TranslationAdmin
def test_page_admin_registered_as_translation_admin():
    from django.contrib import admin
    from modeltranslation.admin import TranslationAdmin

    Page = _Page()
    assert Page in admin.site._registry, (
        "Page MORA biti registrovan na admin.site (@admin.register; AC6)."
    )
    assert isinstance(admin.site._registry[Page], TranslationAdmin), (
        "PageAdmin MORA biti TranslationAdmin (per-locale title/body tabovi; AC6/SM-D7)."
    )


# AC-6: changelist 200 za superuser
def test_page_admin_changelist_200(client, superuser):
    from django.urls import reverse

    client.force_login(superuser)
    response = client.get(reverse("admin:pages_page_changelist"))
    assert response.status_code == 200, (
        f"PageAdmin changelist MORA biti 200 za superuser (NIJE singleton — NE redirect; "
        f"AC6), dobio {response.status_code}."
    )


# AC-6: add-view 200 za superuser (TranslationAdmin renderuje per-locale bez greške)
def test_page_admin_add_200(client, superuser):
    from django.urls import reverse

    client.force_login(superuser)
    response = client.get(reverse("admin:pages_page_add"))
    assert response.status_code == 200, (
        f"PageAdmin add-view MORA biti 200 za superuser (NIJE singleton — ima add; AC6), "
        f"dobio {response.status_code}."
    )


# AC-6: change-view 200 za superuser (seed red)
def test_page_admin_change_200(client, superuser):
    from django.urls import reverse

    page = _make_page()
    client.force_login(superuser)
    response = client.get(reverse("admin:pages_page_change", args=[page.pk]))
    assert response.status_code == 200, (
        f"PageAdmin change-view MORA biti 200 za superuser (AC6), dobio {response.status_code}."
    )


# AC-6: NIJE singleton — has_add_permission/has_delete_permission True
def test_page_admin_not_singleton(superuser):
    from django.contrib import admin
    from django.test import RequestFactory

    Page = _Page()
    model_admin = admin.site._registry[Page]
    # Default ModelAdmin.has_add/has_delete_permission čita request.user.has_perm;
    # bare RequestFactory request NEMA .user → AttributeError. Zakači superuser-a
    # (perm-all) da test izvrši DEFAULT (ne-override-ovanu) granu — suština AC6 je
    # da PageAdmin NE override-uje ove metode na False (NIJE singleton).
    req = RequestFactory().get("/")
    req.user = superuser
    assert model_admin.has_add_permission(req) is True, (
        "PageAdmin.has_add_permission MORA biti True (NIJE singleton; RAZLIKA od 7-1/3-4; AC6)."
    )
    assert model_admin.has_delete_permission(req) is True, (
        "PageAdmin.has_delete_permission MORA biti True (NIJE singleton; AC6)."
    )


# ─────────────────────────────────────────────────────────────────────────────
# Template / XSS — body |linebreaks autoescape, NIKAD |safe
# ─────────────────────────────────────────────────────────────────────────────


# AC-8: <script> u body → ESCAPE-ovan (`&lt;script&gt;`), NE sirov tag
def test_script_in_body_escaped(client):
    _make_page(body="<script>alert(1)</script>")
    response = client.get(PRIVACY_PATH_SR, HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")
    assert "&lt;script&gt;" in html, (
        "body MORA biti auto-escape-ovan (`&lt;script&gt;`) — |linebreaks autoescape "
        "(SM-D4/AC8). Odsustvo = potencijalni |safe (stored-XSS)."
    )
    assert "<script>alert" not in html, (
        "SIROV `<script>alert` NE SME biti u response-u (stored-XSS) — body NIKAD |safe; "
        "rich-text = Epic 8.7 (AC8/SM-D4)."
    )


# AC-8: template NE koristi |safe / mark_safe na body (statički guard)
def test_template_body_never_safe():
    from pathlib import Path

    from django.conf import settings

    template_path = Path(settings.BASE_DIR) / "templates" / "pages" / "page-detail.html"
    assert template_path.exists(), (
        f"templates/pages/page-detail.html MORA postojati ({template_path}; AC7). RED: NEMA template-a."
    )
    text = template_path.read_text(encoding="utf-8")
    assert "page.body|linebreaks" in text.replace(" ", "") or "page.body | linebreaks" in text, (
        "Template MORA renderovati body kroz |linebreaks (AC7/AC8)."
    )
    assert "body|safe" not in text.replace(" ", "") and "mark_safe" not in text, (
        "Template NE SME koristiti |safe / mark_safe na body (stored-XSS granica; AC8/SM-D4)."
    )


# ─────────────────────────────────────────────────────────────────────────────
# Footer — oba linka + regression + šišana-latinica fix (G-13)
# ─────────────────────────────────────────────────────────────────────────────


def _render_footer():
    """Render base.html (uključuje footer) na home strani → vrati HTML."""
    from django.test import Client

    response = Client().get("/sr/", HTTP_HOST="localhost")
    return response


# AC-9: footer sadrži privacy link (pages:page_detail slug=politika-privatnosti)
def test_footer_privacy_link_present(client):
    from django.urls import reverse

    _make_page()
    with override("sr"):
        privacy_url = reverse("pages:page_detail", kwargs={"slug": PRIVACY_SLUG})
    response = client.get("/sr/", HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")
    assert f'href="{privacy_url}"' in html, (
        f"Footer MORA sadržati privacy link href={privacy_url!r} "
        "({% url 'pages:page_detail' slug='politika-privatnosti' %}; AC9)."
    )
    assert "Politika privatnosti" in html, (
        "Footer MORA imati link tekst 'Politika privatnosti' (pune dijakritike; AC9)."
    )


# AC-9/G-11: footer sadrži cookie link (gdpr:cookie_policy — POSTOJEĆA ruta, NE pages slug)
def test_footer_cookie_link_present(client):
    from django.urls import reverse

    with override("sr"):
        cookie_url = reverse("gdpr:cookie_policy")
    response = client.get("/sr/", HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")
    assert f'href="{cookie_url}"' in html, (
        f"Footer 'Politika kolačića' MORA koristiti gdpr:cookie_policy href={cookie_url!r} "
        "(POSTOJEĆA 7-1 ruta, NE pages:page_detail slug; AC9/G-11)."
    )
    assert "Politika kolačića" in html, (
        "Footer MORA imati link tekst 'Politika kolačića' (pune dijakritike; AC9)."
    )


# AC-9/G-4: footer regression — 4 kolone + latest_blog_posts loop + copyright intaktni
def test_footer_regression_intact():
    response = _render_footer()
    assert response.status_code == 200
    html = response.content.decode("utf-8")
    assert html.count("coric-footer__col") >= 4, (
        "Footer MORA zadržati 4 kolone (coric-footer__top; G-4 regression; AC9), "
        f"našao {html.count('coric-footer__col')} 'coric-footer__col'."
    )
    assert "coric-footer__news" in html, (
        "Footer MORA zadržati latest_blog_posts sekciju (coric-footer__news; 5-4/G-4; AC9)."
    )
    assert "coric-footer__copyright" in html, (
        "Footer MORA zadržati copyright (1-8/G-4; AC9)."
    )


# AC-9/G-13: šišana-latinica fix — NEMA Pocetna/Sva prava zadrzana., IMA dijakritike
def test_footer_no_sisana_latinica():
    response = _render_footer()
    assert response.status_code == 200
    html = response.content.decode("utf-8")
    assert "Sva prava zadrzana." not in html, (
        "Footer NE SME sadržati šišanu latinicu 'Sva prava zadrzana.' (G-13; "
        "project-context.md zabranjuje šišanu latinicu u UI)."
    )
    assert "Sva prava zadržana." in html, (
        "Footer copyright MORA koristiti pune dijakritike 'Sva prava zadržana.' (G-13)."
    )
    assert 'aria-label="Pocetna"' not in html, (
        "Footer logo aria-label NE SME biti šišano 'Pocetna' (G-13)."
    )
    assert "Početna" in html, (
        "Footer logo aria-label MORA koristiti pune dijakritike 'Početna' (G-13)."
    )
