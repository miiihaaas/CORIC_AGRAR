"""Story 8.9 — SiteSettings + Navigation Menu Admin (TEA RED phase).

DEFINES the contract Dev (GREEN) must satisfy. Maps AC1-AC8 + SM-decisions (SM-D1..D6)
+ gotchas (G-1..G-6) of `8-9-sitesettings-navigation-menu-admin.md`. Canonical contract:
`8-9-sitesettings-navigation-menu-admin-interface-contract.md`.

8.9 je VERIFY/REGRESSION-LOCK story: `SiteSettingsAdmin` (singleton TranslationAdmin)
VEĆ POSTOJI iz 3-4 i pun je funkcionalan. 8.9 NE „pravi admin" — verifikuje/zaključava
postojeći + dodaje JEDNU novu stvar: `{# [NOTE FOR DEV] ... #}` v1.1 NavigationItem
forward-pointer komentar uz SPOLJNI `<nav class="coric-nav navbar navbar-expand-md">`
u `templates/partials/header.html` (AC6).

RED-PHASE REALNOST: VEĆINA testova ovde su REGRESSION LOCK-ovi koji zaključavaju
postojeće 3-4 ponašanje → oni VEĆ PROLAZE (to je OČEKIVANO i ISPRAVNO, NE forsira se
fail). JEDINI genuinski NOV ugovor je AC6 marker (`test_ac6_header_has_note_for_dev_marker`)
koji MORA da FAIL-uje sada jer komentar još NE postoji u header.html.

SCOPE GRANICA (SM-D1): 8.9 dira SAMO `SiteSettingsAdmin` (verify/lock) + header.html
(SAMO komentar). `PageAdmin` (isti fajl, 8.8) NETAKNUT. `SiteSettings` model NE menja
(0 migracija). gdpr/permissions/templatetags NETAKNUTI. NE uvoditi logo/favicon/hero
polja ni post_save cache signal (SM-D1/SM-D2/OQ-1 DEFER).

────────────────────────────────────────────────────────────────────────────────
COLLECTION-SAFETY: svi `SiteSettingsAdmin` symbol read-ovi su UNUTAR test tela (lazy)
da nedostajući/promenjeni simbol obori TAJ test pojedinačno (pravi RED), nikad collection.

AUTH: `force_login` (NIKAD `client.login` — django-axes iz 8.1 prlja lockout state kroz
authenticate(); ustanovljena lekcija projekta). force_login zaobilazi axes → bez teardown-a.

ADMIN URL: uvek `reverse("admin:pages_sitesettings_*")` — admin na bare /admin-coric/ (8.1),
nikad hardkodovan put.

NE BeautifulSoup (nije instaliran) — regex/string matching.

Refs: 8-9-...md (AC1-AC8, SM-D1..D6, G-1..G-6) + interface contract +
apps/pages/tests/test_sitesettings_admin.py (POSTOJEĆI 3-4 lock-ovi — EXTEND, NE dupliraj) +
apps/pages/tests/test_8_8_page_admin.py (admin-CRUD + RBAC + force_login pattern) +
apps/pages/tests/test_site_setting_tag.py (per-request keš / locale render pattern).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from django.conf import settings
from django.contrib import admin
from django.urls import reverse

pytestmark = pytest.mark.django_db


# ──────────────────────────────────────────────────────────────────────────────
# Fixtures (mirror test_8_8_page_admin.py)
# ──────────────────────────────────────────────────────────────────────────────
@pytest.fixture
def superuser(django_user_model):
    """Superadmin (Marijana) za SiteSettings change-view CRUD smoke.

    `django_user_model` = settings.AUTH_USER_MODEL kroz get_user_model() — NIKAD
    direktan `from django.contrib.auth.models import User`.
    """
    return django_user_model.objects.create_superuser(
        username="settings_admin_8_9",
        email="settings-admin-89@example.com",
        password="tea-pass-12345",
    )


@pytest.fixture
def editor(django_user_model):
    """Editor = is_staff + član `Editor` grupe (8.2 post_migrate je kreirao grupu).

    `pages.sitesettings` je EKSPLICITNO IZOSTAVLJEN iz EDITOR_CONTENT_MODELS
    (8.2 SM-D15 — Editor NE menja globalna podešavanja; mirror gdpr.cookiepolicy).
    Verify NE re-grant (AC5).
    """
    from django.contrib.auth.models import Group

    user = django_user_model.objects.create_user(
        username="settings_editor_8_9",
        email="settings-editor-89@example.com",
        password="tea-pass-12345",
        is_staff=True,
        is_superuser=False,
    )
    user.groups.add(Group.objects.get(name="Editor"))
    return user


def _SiteSettings():
    """Lazy import — collection-safe."""
    from apps.pages.models import SiteSettings

    return SiteSettings


def _settings_admin():
    return admin.site._registry[_SiteSettings()]


def _header_template_text() -> str:
    """Pročitaj sirov izvor templates/partials/header.html (template source read)."""
    tpl = Path(settings.BASE_DIR) / "templates" / "partials" / "header.html"
    return tpl.read_text(encoding="utf-8")


def _scrape_change_form(html):
    """name->value za sva input/select/textarea polja u admin change formi (mirror 8.8).

    Koristi se da POST bude PUN modeltranslation form (SVA _sr/_hu/_en varijantna polja +
    required ne-translatable) — partial POST tiho vraća 200 redisplay sa form errors (AC2).
    """
    import html as html_lib
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
                data[name] = html_lib.unescape(val) if val else "on"
        else:
            data[name] = html_lib.unescape(val)
    for sm in re.finditer(r'<select[^>]*name="([^"]+)"[^>]*>(.*?)</select>', html, re.S):
        name = sm.group(1)
        opts = re.findall(r'<option[^>]*value="([^"]*)"[^>]*selected', sm.group(2))
        data[name] = html_lib.unescape(opts[0]) if opts else ""
    for tm in re.finditer(r'<textarea[^>]*name="([^"]+)"[^>]*>(.*?)</textarea>', html, re.S):
        # HTML entiteti (&amp;, &lt; itd.) u postojećim vrednostima se POST-uju dekodirani,
        # inače bi se enkodirani round-trip-ovali nazad u DB.
        data[tm.group(1)] = html_lib.unescape(tm.group(2))
    return data


# ══════════════════════════════════════════════════════════════════════════════
# AC1 — SiteSettingsAdmin ostaje pun funkcionalan singleton TranslationAdmin
#        (REGRESSION LOCK; 3-4) — ovi PROLAZE danas (zaključavaju postojeće)
# ══════════════════════════════════════════════════════════════════════════════
# AC-1: SiteSettingsAdmin je TranslationAdmin (NE plain ModelAdmin; auto sr/hu/en tabovi)
def test_ac1_sitesettings_admin_is_translation_admin():
    from modeltranslation.admin import TranslationAdmin

    assert isinstance(_settings_admin(), TranslationAdmin), (
        "SiteSettingsAdmin MORA OSTATI TranslationAdmin (per-locale slogan/address/"
        "working_hours tabovi; AC1/SM-D6 — NE degradirati na plain ModelAdmin)."
    )


# AC-1: has_add_permission → False kad red postoji (singleton — nema „Add another")
def test_ac1_has_add_permission_false_when_row_exists():
    from django.test import RequestFactory

    SiteSettings = _SiteSettings()
    SiteSettings.load()  # garantuj da red postoji
    req = RequestFactory().get("/")
    assert _settings_admin().has_add_permission(req) is False, (
        "has_add_permission MORA biti False kad red postoji (singleton; AC1/3-4 lock)."
    )


# AC-1: has_delete_permission → False (i za obj=None — bulk-delete iz changelist-a)
def test_ac1_has_delete_permission_false_including_obj_none():
    from django.test import RequestFactory

    SiteSettings = _SiteSettings()
    req = RequestFactory().get("/")
    obj = SiteSettings.load()
    assert _settings_admin().has_delete_permission(req, obj) is False, (
        "has_delete_permission MORA biti False za singleton instancu (AC1/3-4 lock)."
    )
    assert _settings_admin().has_delete_permission(req, None) is False, (
        "has_delete_permission(obj=None) MORA biti False (bulk delete iz changelist-a; AC1)."
    )


# AC-1: changelist_view → 302 redirect na change-view jedinog objekta (kroz reverse, NE hardkodovano)
def test_ac1_changelist_redirects_to_change_view(client, superuser):
    SiteSettings = _SiteSettings()
    obj = SiteSettings.load()
    client.force_login(superuser)
    changelist_url = reverse("admin:pages_sitesettings_changelist")
    expected_change_url = reverse("admin:pages_sitesettings_change", args=[obj.pk])
    resp = client.get(changelist_url)
    assert resp.status_code == 302, (
        f"Changelist MORA 302 redirect na change-view jedinog objekta (singleton UX; "
        f"AC1/SM-D6/G-6); dobio {resp.status_code}."
    )
    assert resp.url.endswith(expected_change_url) or resp.url == expected_change_url, (
        f"Redirect MORA voditi na change-view {expected_change_url!r}; dobio {resp.url!r}."
    )


# AC-1: change-view → 200 za superuser (kroz reverse())
def test_ac1_change_view_200_superuser(client, superuser):
    SiteSettings = _SiteSettings()
    obj = SiteSettings.load()
    client.force_login(superuser)
    resp = client.get(reverse("admin:pages_sitesettings_change", args=[obj.pk]))
    assert resp.status_code == 200, (
        f"Change-view MORA biti 200 za superuser (AC1/3-4 lock); dobio {resp.status_code}."
    )


# AC-1/AC8: admin system checks čisti (TranslationAdmin + search_fields realna kolona → 0 admin.E*)
def test_ac1_admin_system_checks_clean():
    from django.core.checks import run_checks

    errors = [e for e in run_checks() if e.is_serious()]
    assert errors == [], (
        f"manage.py check MORA biti čist — SiteSettingsAdmin (TranslationAdmin + realne "
        f"search_fields kolone) ne sme baciti admin.E* (AC8/G-2 — ako fieldsets sa "
        f"created_at/updated_at bez readonly_fields → admin.E005). Greške: {errors}."
    )


# ══════════════════════════════════════════════════════════════════════════════
# AC2 — Sva opšta-podešavanja polja editabilna (per locale za translatable) +
#        POST round-trip (NOVE vrednosti, NE samo status assert)
# ══════════════════════════════════════════════════════════════════════════════
# AC-2: change-view GET 200 prikazuje sva polja + per-locale tabove za translatable
def test_ac2_change_view_renders_all_fields_with_locale_tabs(client, superuser):
    SiteSettings = _SiteSettings()
    obj = SiteSettings.load()
    client.force_login(superuser)
    resp = client.get(reverse("admin:pages_sitesettings_change", args=[obj.pk]))
    assert resp.status_code == 200
    html = resp.content.decode()
    # ne-translatable polja → jedno polje svaka
    for fld in ("company_name", "phone_sales", "phone_service", "email",
                "social_facebook", "social_instagram"):
        assert f'name="{fld}"' in html, (
            f"Change-view MORA renderovati ne-translatable polje '{fld}' (AC2)."
        )
    # translatable polja → per-locale varijante (sr/hu/en tabovi)
    for base in ("slogan", "address", "working_hours"):
        for loc in ("sr", "hu", "en"):
            assert f'name="{base}_{loc}"' in html, (
                f"Change-view MORA renderovati per-locale polje '{base}_{loc}' "
                f"(modeltranslation tab; AC2)."
            )


# AC-2: PUN modeltranslation POST → 302 I round-trip load() ima NOVE vrednosti (NE samo status)
def test_ac2_full_post_persists_new_values_round_trip(client, superuser):
    SiteSettings = _SiteSettings()
    obj = SiteSettings.load()
    client.force_login(superuser)
    url = reverse("admin:pages_sitesettings_change", args=[obj.pk])
    # Scrape PUN form (SVA _sr/_hu/_en + required ne-translatable) → onda menjamo vrednosti.
    data = _scrape_change_form(client.get(url).content.decode())
    data["company_name"] = "Ćorić Agrar — IZMENJENO"
    data["slogan_sr"] = "Novi slogan sr (čćžšđ)"
    data["slogan_hu"] = "Új szlogen hu"
    data["address_sr"] = "Nova adresa 42, Bačka Topola"
    data["phone_sales"] = "+381 11 222 333"
    data["email"] = "nova-prodaja@coricagrar.rs"
    data["working_hours_sr"] = "Ponedeljak–Petak: 09–17h"
    resp = client.post(url, data)
    assert resp.status_code == 302, (
        f"PUN validan modeltranslation POST MORA sačuvati i dati 302 (AC2); dobio "
        f"{resp.status_code}. (Ako 200 → form errors; partial/required-fail.)"
    )
    fresh = SiteSettings.load()
    assert fresh.company_name == "Ćorić Agrar — IZMENJENO", (
        f"company_name MORA biti perzistiran posle POST-a (round-trip — NE samo status; AC2); "
        f"dobio {fresh.company_name!r}."
    )
    assert fresh.phone_sales == "+381 11 222 333", (
        f"phone_sales MORA biti perzistiran (AC2); dobio {fresh.phone_sales!r}."
    )
    assert fresh.email == "nova-prodaja@coricagrar.rs", (
        f"email MORA biti perzistiran (AC2); dobio {fresh.email!r}."
    )
    assert fresh.slogan_sr == "Novi slogan sr (čćžšđ)", (
        f"slogan_sr (translatable) MORA biti perzistiran per-locale (AC2); dobio {fresh.slogan_sr!r}."
    )
    assert fresh.slogan_hu == "Új szlogen hu", (
        f"slogan_hu (translatable, ne-default locale) MORA biti perzistiran per-locale — POST "
        f"piše SVE _sr/_hu/_en varijante, ne samo default (AC2); dobio {fresh.slogan_hu!r}."
    )
    assert fresh.working_hours_sr == "Ponedeljak–Petak: 09–17h", (
        f"working_hours_sr (translatable) MORA biti perzistiran (AC2); dobio {fresh.working_hours_sr!r}."
    )


# AC-2 (edge / negative): partial POST bez required polja → 200 redisplay sa form errors (NE 302)
def test_ac2_partial_post_missing_required_redisplays_200(client, superuser):
    SiteSettings = _SiteSettings()
    obj = SiteSettings.load()
    client.force_login(superuser)
    url = reverse("admin:pages_sitesettings_change", args=[obj.pk])
    data = _scrape_change_form(client.get(url).content.decode())
    # company_name je required (CharField blank=False, default postoji ali form traži vrednost) →
    # prazno → form-error → 200 redisplay (NE 302). Round-trip: stara vrednost OSTAJE.
    old_company = obj.company_name
    data["company_name"] = ""
    resp = client.post(url, data)
    assert resp.status_code == 200, (
        f"Partial POST sa praznim required `company_name` MORA dati 200 redisplay sa form "
        f"errors (NE 302 — inače bi status-only assert lažno prošao; AC2); dobio {resp.status_code}."
    )
    form = resp.context["adminform"].form
    assert "company_name" in form.errors, (
        f"Prazno required `company_name` MORA dati field grešku (AC2); dobio {form.errors!r}."
    )
    fresh = SiteSettings.load()
    assert fresh.company_name == old_company, (
        f"Neuspešan POST NE SME promeniti perzistiranu vrednost (`company_name` ostaje "
        f"{old_company!r}; AC2); dobio {fresh.company_name!r}."
    )


# ══════════════════════════════════════════════════════════════════════════════
# AC3 — search_fields REALNE ne-translatable kolone (NEMA G-1 FieldError; verify-lock)
#        + DEFENSE-IN-DEPTH: nijedno translatable polje u search_fields
# ══════════════════════════════════════════════════════════════════════════════
# AC-3: search_fields == ("company_name","phone_sales","email") — SVA realne ne-translatable kolone
def test_ac3_search_fields_are_real_non_translatable_columns():
    assert tuple(_settings_admin().search_fields) == ("company_name", "phone_sales", "email"), (
        "SiteSettingsAdmin.search_fields MORA OSTATI ('company_name','phone_sales','email') — "
        "SVA tri su realne ne-translatable DB kolone (CharField/EmailField; NISU u translation.py). "
        "RAZLIKA od 8.4-8.8 gde je virtuelni name/title bio bug (AC3/SM-D6); dobio "
        f"{_settings_admin().search_fields!r}."
    )


# AC-3 (MANDATORNI defense-in-depth lock; G-1): nijedno TRANSLATABLE polje NIJE u search_fields.
# POSTOJEĆI test_sitesettings_admin.py OVO NE pokriva — TEA piše ovde (story:121/196 eksplicitno).
def test_ac3_no_translatable_field_in_search_fields():
    translatable = {"slogan", "address", "working_hours"}
    search = set(_settings_admin().search_fields)
    leaked = translatable & search
    assert leaked == set(), (
        f"Nijedno TRANSLATABLE polje (slogan/address/working_hours) NE SME biti u search_fields "
        f"— sirovo translatable ime bez _sr sufiksa → runtime FieldError (G-1; defense-in-depth "
        f"protiv budućeg refaktora koji ukloni singleton redirect masking). Procurelo: {leaked!r}."
    )


# AC-3 (REGRESSION LOCK): changelist je 302 (singleton redirect PRE search) — search FieldError
# rizik praktično maskiran, ali lock svejedno potvrđuje da changelist NE 500 (defense-in-depth)
def test_ac3_changelist_with_query_does_not_500(client, superuser):
    SiteSettings = _SiteSettings()
    SiteSettings.load()
    client.force_login(superuser)
    resp = client.get(reverse("admin:pages_sitesettings_changelist"), {"q": "Ćorić"})
    assert resp.status_code in (200, 302), (
        f"Changelist sa ?q= NE SME baciti FieldError 500 — search_fields su realne kolone + "
        f"singleton redirect (AC3/G-1); dobio {resp.status_code}."
    )


# ══════════════════════════════════════════════════════════════════════════════
# AC4 — Promena SiteSettings reflektuje se ODMAH (cache-AC već-zadovoljen; SM-D2)
# ══════════════════════════════════════════════════════════════════════════════
# AC-4: izmena company_name → render {% site_setting %} u NOVOM request-u vidi NOVU vrednost
def test_ac4_new_request_sees_updated_value(client):
    from django.template import Context, Template
    from django.test import RequestFactory
    from django.utils import translation

    SiteSettings = _SiteSettings()
    obj = SiteSettings.load()
    obj.company_name = "VrednostPosleIzmene"
    obj.save()
    # NOVI RequestFactory request (svež `request` objekat → per-request keš NIJE napunjen
    # starom vrednošću) → tag re-učita load() → vidi novu vrednost.
    # `translation.override` umesto goljog `activate("sr")` da locale state ne curi posle testa.
    with translation.override("sr"):
        req = RequestFactory().get("/")
        tpl = Template('{% load site_settings %}{% site_setting "company_name" %}')
        out = tpl.render(Context({"request": req}))
    assert "VrednostPosleIzmene" in out, (
        f"Novi request MORA videti izmenjenu company_name kroz {{% site_setting %}} (nema "
        f"cross-request stale keša; SM-D2/AC4); dobio {out!r}."
    )


# AC-4 (SM-D2 / G-5): apps.pages NEMA signals modul koji dira Django cache (NE izmišljaj keš za invalidaciju)
def test_ac4_pages_has_no_cache_invalidation_signal():
    import apps.pages as pages_pkg

    pages_dir = Path(pages_pkg.__file__).parent
    signals_py = pages_dir / "signals.py"
    if signals_py.exists():
        text = signals_py.read_text(encoding="utf-8")
        compact = text.replace(" ", "")
        assert "cache.delete" not in compact and "cache.clear" not in compact, (
            "apps.pages NE SME imati post_save signal sa cache.delete/cache.clear za SiteSettings "
            "— per-request keš NEMA stale (SM-D2/G-5; YAGNI — keš koji ne postoji se ne invalidira)."
        )
    # site_setting tag NE sme uvesti Django cache framework (per-request samo).
    import re as _re

    tag_py = pages_dir / "templatetags" / "site_settings.py"
    tag_text = tag_py.read_text(encoding="utf-8")
    compact_tag = tag_text.replace(" ", "")
    # Regex na sirovom tekstu hvata SVE varijante importa (`from django.core.cache import`,
    # `from django.core import cache`, `import django.core.cache`) — ne samo jedan oblik.
    assert _re.search(r"django\.core\.cache", tag_text) is None, (
        "site_setting tag NE SME importovati django.core.cache (per-request keš samo; SM-D2/G-5)."
    )
    assert "cache.set" not in compact_tag, (
        "site_setting tag MORA OSTATI per-request keš (NEMA Django cache.set; SM-D2/G-5)."
    )


# ══════════════════════════════════════════════════════════════════════════════
# AC5 — RBAC: SiteSettings je Superadmin-only (NE re-grant; verify) + anon redirect
# ══════════════════════════════════════════════════════════════════════════════
# AC-5 (verify, NE menjaj): pages.sitesettings NIJE u EDITOR_CONTENT_MODELS (Superadmin-only)
def test_ac5_sitesettings_not_in_editor_allowlist():
    from apps.accounts.permissions import EDITOR_CONTENT_MODELS

    assert ("pages", "sitesettings") not in EDITOR_CONTENT_MODELS, (
        "('pages','sitesettings') NE SME biti u EDITOR_CONTENT_MODELS (Superadmin-only; "
        "8.2 SM-D15; AC5/SM-D5 — NE re-grant)."
    )


# AC-5: Editor (is_staff, Editor grupa) → GET change-view → 403 (NE sme menjati globalna podešavanja)
def test_ac5_editor_forbidden_on_change_view(client, editor):
    SiteSettings = _SiteSettings()
    obj = SiteSettings.load()
    client.force_login(editor)
    resp = client.get(reverse("admin:pages_sitesettings_change", args=[obj.pk]))
    assert resp.status_code == 403, (
        f"Editor (bez sitesettings perm) MORA dobiti 403 na change-view (Superadmin-only; "
        f"AC5/SM-D5); dobio {resp.status_code}."
    )


# AC-5: Superadmin → GET change-view → 200
def test_ac5_superadmin_allowed_on_change_view(client, superuser):
    SiteSettings = _SiteSettings()
    obj = SiteSettings.load()
    client.force_login(superuser)
    resp = client.get(reverse("admin:pages_sitesettings_change", args=[obj.pk]))
    assert resp.status_code == 200, (
        f"Superadmin MORA dobiti 200 na change-view (AC5); dobio {resp.status_code}."
    )


# AC-5 (security / negative): anoniman → 302 admin login (admin na bare /admin-coric/, VAN i18n)
def test_ac5_anonymous_redirected_to_login(client):
    SiteSettings = _SiteSettings()
    obj = SiteSettings.load()
    resp = client.get(reverse("admin:pages_sitesettings_change", args=[obj.pk]))
    assert resp.status_code == 302, (
        f"Anoniman na SiteSettings change-view MORA biti 302 login redirect (AC5/security); "
        f"dobio {resp.status_code}."
    )
    assert reverse("admin:login") in resp["Location"], (
        f"302 MORA voditi na admin:login (admin na bare /admin-coric/ iz 8.1); "
        f"Location={resp['Location']!r}."
    )


# ══════════════════════════════════════════════════════════════════════════════
# AC6 — [NOTE FOR DEV] navigacija marker (NOVI ugovor — OVAJ MORA FAIL-ovati sada)
# ══════════════════════════════════════════════════════════════════════════════
# AC-6 (THE genuinely NEW contract — FAIL danas): header.html sadrži [NOTE FOR DEV] komentar uz nav
def test_ac6_header_has_note_for_dev_marker():
    text = _header_template_text()
    assert "[NOTE FOR DEV]" in text, (
        "templates/partials/header.html MORA sadržati `{# [NOTE FOR DEV] ... #}` komentar "
        "(v1.1 NavigationItem forward-pointer; AC6/SM-D4). OVAJ KOMENTAR JOŠ NE POSTOJI → "
        "Dev ga dodaje (RED→GREEN)."
    )
    assert "NavigationItem" in text, (
        "Marker MORA referencirati v1.1 `NavigationItem` model (forward-pointer; AC6/SM-D4/OQ-2)."
    )


# AC-6: marker je uz SPOLJNI <nav class="coric-nav navbar navbar-expand-md"> (~linija 55),
# NE uz unutrašnji <div class="collapse navbar-collapse"> (~linija 76). FAIL danas (komentar nema).
def test_ac6_marker_is_on_outer_nav_not_inner_collapse():
    text = _header_template_text()
    marker_pos = text.find("[NOTE FOR DEV]")
    assert marker_pos != -1, (
        "[NOTE FOR DEV] marker MORA postojati (AC6) — vidi test_ac6_header_has_note_for_dev_marker."
    )
    outer_nav_pos = text.find('<nav class="coric-nav navbar navbar-expand-md"')
    inner_collapse_pos = text.find('<div class="collapse navbar-collapse"')
    assert outer_nav_pos != -1, (
        "SPOLJNI <nav class=\"coric-nav navbar navbar-expand-md\"> MORA postojati (header markup; AC6)."
    )
    # STRUKTURALNI assert (bez magic-prozora): marker mora biti NEPOSREDNO PRE spoljnog <nav>
    # otvaranja — tj. marker dolazi PRE njega, i između markera i <nav>-a nalazi se SAMO
    # whitespace ili drugi {# #} komentari (nijedan drugi HTML element / nav otvaranje).
    assert marker_pos < outer_nav_pos, (
        f"[NOTE FOR DEV] marker MORA biti PRE spoljnog <nav coric-nav navbar navbar-expand-md> "
        f"otvaranja (forward-pointer komentar uz nav; AC6/SM-D4). marker@{marker_pos}, "
        f"outer_nav@{outer_nav_pos}."
    )
    # Marker je {# ... #} komentar; nađi kraj tog komentara pa proveri šta sledi do <nav>-a.
    marker_comment_end = text.find("#}", marker_pos)
    assert marker_comment_end != -1 and marker_comment_end < outer_nav_pos, (
        f"[NOTE FOR DEV] MORA biti Django {{# ... #}} komentar zatvoren PRE spoljnog <nav>-a "
        f"(AC6/SM-D4 — koristi {{# #}}, NE HTML <!-- -->). marker@{marker_pos}, "
        f"comment_end@{marker_comment_end}, outer_nav@{outer_nav_pos}."
    )
    between = text[marker_comment_end + 2 : outer_nav_pos]
    # Ukloni eventualne dodatne {# #} komentare iz međuprostora; ostatak mora biti samo whitespace.
    import re as _re

    residual = _re.sub(r"\{#.*?#\}", "", between, flags=_re.S).strip()
    assert residual == "", (
        f"Između [NOTE FOR DEV] komentara i SPOLJNOG <nav>-a sme biti SAMO whitespace ili drugi "
        f"{{# #}} komentari — marker je poslednji komentar neposredno pre nav-a, NE kod unutrašnjeg "
        f"collapse div-a (~linija 76; AC6/SM-D4). Procureo HTML/sadržaj: {residual!r}. "
        f"inner_collapse@{inner_collapse_pos}."
    )


# AC-6 (funkcionalni assert): nav linkovi NEPROMENJENI — komentar ne menja izlaz markup-a
def test_ac6_nav_links_unchanged():
    text = _header_template_text()
    # Reprezentativni statički {% url %} nav linkovi koji MORAJU OSTATI (marker je samo komentar).
    for url_name in ("pages:home", "products:tractor_list", "pages:service",
                     "pages:about", "pages:contact"):
        assert f"'{url_name}'" in text or f'"{url_name}"' in text, (
            f"Nav link {{% url '{url_name}' %}} MORA OSTATI u header.html (8.9 marker NE menja "
            f"nav markup/linkove; AC6/SM-D4)."
        )


# AC-6 (regression): render header kroz stranu → 200, marker ne ruši render (Django {# #} se ne emituje)
def test_ac6_header_renders_200_and_comment_not_emitted(client):
    SiteSettings = _SiteSettings()
    SiteSettings.load()
    resp = client.get(reverse("pages:home"), HTTP_HOST="localhost")
    assert resp.status_code == 200, (
        f"Strana koja uključuje header MORA biti 200 (marker komentar ne ruši render; AC6); "
        f"dobio {resp.status_code}."
    )
    html = resp.content.decode()
    assert "[NOTE FOR DEV]" not in html, (
        "Django {# ... #} komentar se NE emituje u HTML izlaz — `[NOTE FOR DEV]` NE SME biti "
        "vidljiv u renderu (AC6 — koristi {# #}, NE {% comment %} koji bi takođe bio nevidljiv, "
        "ali NIKAD HTML <!-- --> koji bi procureo)."
    )


# ══════════════════════════════════════════════════════════════════════════════
# AC7 — 0 migracija + 0 dep (admin/verify/marker-only) — PROLAZI danas (lock)
# ══════════════════════════════════════════════════════════════════════════════
# AC-7: nema pending schema migracije za apps.pages (model NETAKNUT; epics:1175 polja DEFER)
def test_ac7_no_pending_migration_for_pages():
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
        f"apps.pages NE SME imati pending schema migraciju (8.9 je verify/marker-only; "
        f"SiteSettings model NETAKNUT — epics:1175 logo/favicon/hero/gdpr_banner_* polja "
        f"DEFER, SM-D1/OQ-1/AC7); autodetector predlaže: {changes.get('pages')}."
    )


# AC-7 (SM-D1 lock): SiteSettings NEMA logo/favicon/hero_image/gdpr_banner_* polja (DEFER — NE dodavati)
def test_ac7_sitesettings_has_no_deferred_upload_or_banner_fields():
    SiteSettings = _SiteSettings()
    field_names = {f.name for f in SiteSettings._meta.get_fields()}
    forbidden = {
        "logo", "favicon", "hero_image", "hero",
        "gdpr_banner_title", "gdpr_banner_body",
    }
    leaked = forbidden & field_names
    assert leaked == set(), (
        f"SiteSettings NE SME imati epics:1175 model-proširenja (logo/favicon/hero/gdpr_banner_*) "
        f"— DEFER za v1 (upload-security + cross-app coupling; SM-D1/OQ-1). Procurela polja: {leaked!r}."
    )


# ══════════════════════════════════════════════════════════════════════════════
# AC8 / G-3 — PageAdmin (isti fajl, 8.8) NETAKNUT — regression lock (PROLAZI danas)
# ══════════════════════════════════════════════════════════════════════════════
# AC-8/G-3: PageAdmin NIJE diran — search_fields ostaju ('title_sr','slug') (8.8 ne smeju da regresiraju)
def test_ac8_pageadmin_untouched():
    from apps.pages.models import Page

    page_admin = admin.site._registry[Page]
    assert tuple(page_admin.search_fields) == ("title_sr", "slug"), (
        "PageAdmin.search_fields MORA OSTATI ('title_sr','slug') — 8.9 dira SAMO "
        f"SiteSettingsAdmin (G-3; PageAdmin 8.8 NETAKNUT); dobio {page_admin.search_fields!r}."
    )
    # PageAdmin NIJE singleton — has_add ostaje default (NE override-ovan kao SiteSettings)
    assert page_admin.prepopulated_fields == {"slug": ("title_sr",)}, (
        "PageAdmin.prepopulated_fields MORA OSTATI {'slug': ('title_sr',)} (8.8 NETAKNUT; G-3)."
    )
