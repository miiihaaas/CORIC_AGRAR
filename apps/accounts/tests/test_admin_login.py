"""Story 8.1 — Custom Admin Login sa Rate Limiting (TEA RED phase).

Pokriva svih 15 AC (AC1–AC14 + AC9b) sigurnosno-kritične admin auth story:
- URL migracija admin → bare `/admin-coric/` (non-i18n); `/admin/` + `/sr/admin/` → 404.
- django-axes v8 settings (backends order, FAILURE_LIMIT, COOLOFF, LOCKOUT_PARAMETERS,
  AxesMiddleware last, axes in INSTALLED_APPS, SESSION_COOKIE_AGE).
- Axes lockout off-by-one (SM-D16): pokušaji 1–4 → login-fail; 5. → lockout 429 + standalone
  lockout template + srpski tekst.
- AdminLoginForm (email-as-username) STVARNO ožičena u admin.site.login_form + email→authenticate().
- RedirectMiddleware bare `/admin-coric/` skip + open-redirect-na-auth guard.
- robots.txt admin slug NE objavljen.

────────────────────────────────────────────────────────────────────────────────
COLLECTION-SAFETY (KRITIČNO — RED faza):
Sve `axes.*` / `AccessAttempt` / `apps.accounts.*` importe radimo UNUTAR funkcija
(lazy), NIKAD na module-level. Razlog: u RED fazi axes NIJE u INSTALLED_APPS,
apps/accounts NE postoji još, admin je još na /sr/admin/. Module-level import bi
ABORT-ovao collection celog fajla (ImportError/AppRegistryNotReady) i sakrio sve
ostale RED failure-e. Lazy import → svaki test fail-uje pojedinačno (pravi RED).

AXES TEARDOWN (SM-D15 / G-6 / G-12):
`AXES_ENABLED` ostaje True. Lockout testovi POST-uju DIREKTNO na
reverse("admin:login") sa pogrešnim password-om (force_login zaobilazi axes).
Axes stanje perzistira u DB (AccessAttempt) + cache → cross-test lockout bleed.
Fixture `axes_reset` (autouse na lockout testovima) radi reset PRE i POSLE:
axes.utils.reset() + AccessAttempt.objects.all().delete() + cache.clear().

Refs:
- 8-1-custom-admin-login-sa-rate-limiting.md (AC1–AC14, AC9b, SM-D1..D19, G-1..G-16)
- 8-1-interface-contract.md
"""

from __future__ import annotations

import pytest
from django.test import Client
from django.urls import NoReverseMatch, reverse

pytestmark = pytest.mark.django_db


# ──────────────────────────────────────────────────────────────────────────────
# Helpers / fixtures
# ──────────────────────────────────────────────────────────────────────────────
def _reset_axes_state():
    """Reset axes broj-stanja (DB + cache) — collection-safe lazy import.

    U RED fazi axes nije instaliran → import baca ImportError; hvatamo ga tiho
    tako da teardown ne abortuje (test telo ionako fail-uje ranije na svom AC).
    """
    from django.core.cache import cache

    cache.clear()
    try:
        from axes.models import AccessAttempt
        from axes.utils import reset

        reset()
        AccessAttempt.objects.all().delete()
    except (ImportError, RuntimeError, LookupError):
        # ImportError (axes nije instaliran) / AppRegistryNotReady (RuntimeError) /
        # LookupError (app/model nije registrovan) — RED-safe teardown
        pass


@pytest.fixture
def axes_reset():
    """Autouse-na-lockout fixture: reset axes stanja PRE i POSLE testa (G-12)."""
    _reset_axes_state()
    yield
    _reset_axes_state()


def _make_staff_user(email="admin@coricagrar.rs", username="adminuser", password="Sigurna-Lozinka-123!"):
    """Kreira staff usera kroz get_user_model() (NIKAD direktan User import — project-context)."""
    from django.contrib.auth import get_user_model

    User = get_user_model()
    return User.objects.create_user(
        username=username, email=email, password=password, is_staff=True, is_superuser=True
    )


# ══════════════════════════════════════════════════════════════════════════════
# AC1 — admin URL premešten: /admin/ i /sr/admin/ → 404
# ══════════════════════════════════════════════════════════════════════════════
def test_ac1_old_admin_bare_returns_404():
    """AC1: GET /admin/ (stari put, bez locale) → admin NIJE serviran (404 nakon follow).

    TEST_MODIFICATION (Dev/8.1): originalno je asertovao status_code == 404 na PRVI
    hop. Sa `prefix_default_language=True` + pages catch-all (`/sr/<slug:slug>/`),
    SVAKA bare ne-prefiksovana putanja prolazi kroz Django LocaleMiddleware
    locale-redirect (302 → /sr/...) jer `is_valid_path("/sr/admin/")` == True
    (catch-all matchuje slug='admin'). Krajnji ishod je 404 (PageDetailView nema
    Page 'admin') i admin SE NE servira — namera AC1 očuvana. Asertujemo lanac sa
    follow=True umesto krhke single-hop 404 (TEA previd pages-catch-all interakcije).
    """
    response = Client().get("/admin/", follow=True)
    assert response.status_code == 404, (
        f"GET /admin/ (follow) MORA završiti 404 — admin NIJE serviran na starom putu "
        f"posle SM-D1 premeštanja, dobio {response.status_code}."
    )
    # admin login forma NE sme biti renderovana na finalnom 404 (admin je mrtav ovde)
    body = response.content.decode("utf-8").lower()
    assert 'name="username"' not in body, (
        "Stari /admin/ put NE SME servirati admin login formu (premešten na /admin-coric/)."
    )


def test_ac1_old_admin_locale_prefixed_returns_404():
    """AC1: GET /sr/admin/ (stari realni i18n put) → 404 (uklonjen iz i18n_patterns)."""
    response = Client().get("/sr/admin/")
    assert response.status_code == 404, (
        f"GET /sr/admin/ MORA biti 404 (admin VAĐEN iz i18n_patterns — SM-D1), "
        f"dobio {response.status_code}."
    )


# ══════════════════════════════════════════════════════════════════════════════
# AC2 — novi admin URL radi: /admin-coric/ prikazuje login formu
# ══════════════════════════════════════════════════════════════════════════════
def test_ac2_admin_coric_shows_login_form():
    """AC2: GET /admin-coric/ (neautentifikovan) → admin login (200 sa formom ili 302→login)."""
    response = Client().get("/admin-coric/", follow=True)
    assert response.status_code == 200, (
        f"GET /admin-coric/ MORA završiti na login strani (200 posle follow), "
        f"dobio {response.status_code}."
    )
    body = response.content.decode("utf-8").lower()
    assert "password" in body or "lozink" in body or 'name="username"' in body, (
        "Admin login strana MORA renderovati login formu (password/username polje)."
    )


def test_ac2_admin_coric_login_url_resolves_200():
    """AC2: GET /admin-coric/login/ → 200 (login forma direktno dostupna)."""
    response = Client().get("/admin-coric/login/")
    assert response.status_code == 200, (
        f"GET /admin-coric/login/ MORA biti 200 (login forma), dobio {response.status_code}."
    )


# ══════════════════════════════════════════════════════════════════════════════
# AC3 — admin-coric NIJE locale-prefiksovan
# ══════════════════════════════════════════════════════════════════════════════
def test_ac3_reverse_admin_index_is_bare_admin_coric():
    """AC3: reverse('admin:index') počinje /admin-coric/ (NE /sr/, NE /admin/)."""
    url = reverse("admin:index")
    assert url.startswith("/admin-coric/"), (
        f"reverse('admin:index') MORA početi sa /admin-coric/ (non-i18n, bez locale "
        f"prefiksa — SM-D1/AC3), dobio {url!r}."
    )
    assert not url.startswith("/sr/"), (
        f"reverse('admin:index') NE SME imati locale prefiks /sr/, dobio {url!r} (AC3)."
    )


def test_ac3_reverse_admin_login_is_admin_coric_login():
    """AC3/G-7: reverse('admin:login') == /admin-coric/login/ (lockout POST target)."""
    url = reverse("admin:login")
    assert url == "/admin-coric/login/", (
        f"reverse('admin:login') MORA biti /admin-coric/login/, dobio {url!r} "
        "(axes lockout testovi POST-uju ovde — G-7)."
    )


def test_ac3_sr_admin_coric_does_not_resolve():
    """AC3/G-3: /sr/admin-coric/ NE postoji (admin je VAN i18n_patterns) → 404."""
    response = Client().get("/sr/admin-coric/")
    assert response.status_code == 404, (
        f"/sr/admin-coric/ MORA biti 404 (admin je non-i18n bare slug — G-3), "
        f"dobio {response.status_code}."
    )


# ══════════════════════════════════════════════════════════════════════════════
# AC11 — settings checklist (axes integracija)
# ══════════════════════════════════════════════════════════════════════════════
def test_ac11_axes_in_installed_apps():
    """AC11: 'axes' u INSTALLED_APPS, POSLE django.contrib.contenttypes + auth (G-16)."""
    from django.conf import settings

    assert "axes" in settings.INSTALLED_APPS, "'axes' MORA biti u INSTALLED_APPS (AC11)."
    apps = list(settings.INSTALLED_APPS)
    assert apps.index("axes") > apps.index("django.contrib.contenttypes"), (
        "'axes' MORA biti POSLE django.contrib.contenttypes (apps registry dep — G-16)."
    )
    assert apps.index("axes") > apps.index("django.contrib.auth"), (
        "'axes' MORA biti POSLE django.contrib.auth (G-16)."
    )


def test_ac11_apps_accounts_in_installed_apps():
    """AC11: 'apps.accounts' u INSTALLED_APPS."""
    from django.conf import settings

    assert "apps.accounts" in settings.INSTALLED_APPS, (
        "'apps.accounts' MORA biti u INSTALLED_APPS (AC11)."
    )


def test_ac11_axes_backend_first_in_authentication_backends():
    """AC11/G-1: AxesStandaloneBackend PRVI + ModelBackend prisutan (oba obavezna)."""
    from django.conf import settings

    backends = list(getattr(settings, "AUTHENTICATION_BACKENDS", []))
    assert backends, (
        "AUTHENTICATION_BACKENDS MORA biti eksplicitno definisan (base.py default nema ga — G-1)."
    )
    assert backends[0] == "axes.backends.AxesStandaloneBackend", (
        f"AxesStandaloneBackend MORA biti PRVI backend (v8 standalone — G-4), dobio {backends!r}."
    )
    assert "django.contrib.auth.backends.ModelBackend" in backends, (
        "ModelBackend MORA ostati u backends — bez njega niko se ne loguje (G-1)."
    )


def test_ac11_axes_middleware_last():
    """AC11/G-2: AxesMiddleware POSLEDNJI u MIDDLEWARE (posle LocaleSwitcherMiddleware)."""
    from django.conf import settings

    mw = list(settings.MIDDLEWARE)
    assert mw[-1] == "axes.middleware.AxesMiddleware", (
        f"AxesMiddleware MORA biti POSLEDNJI middleware (posle auth — G-2/SM-D17), "
        f"poslednji je {mw[-1]!r}."
    )


# ══════════════════════════════════════════════════════════════════════════════
# AC5 — axes config vrednosti (settings-level)
# ══════════════════════════════════════════════════════════════════════════════
def test_ac5_axes_failure_limit_is_5():
    """AC5: AXES_FAILURE_LIMIT == 5."""
    from django.conf import settings

    assert getattr(settings, "AXES_FAILURE_LIMIT", None) == 5, (
        f"AXES_FAILURE_LIMIT MORA biti 5, dobio {getattr(settings, 'AXES_FAILURE_LIMIT', None)!r} (AC5)."
    )


def test_ac5_axes_cooloff_time_is_one_hour():
    """AC5: AXES_COOLOFF_TIME == timedelta(hours=1)."""
    from datetime import timedelta

    from django.conf import settings

    assert getattr(settings, "AXES_COOLOFF_TIME", None) == timedelta(hours=1), (
        f"AXES_COOLOFF_TIME MORA biti timedelta(hours=1), dobio "
        f"{getattr(settings, 'AXES_COOLOFF_TIME', None)!r} (AC5)."
    )


def test_ac5_axes_lockout_parameters_ip_based():
    """AC5/SM-D16: AXES_LOCKOUT_PARAMETERS == [['ip_address']] (v8 IP-based)."""
    from django.conf import settings

    assert getattr(settings, "AXES_LOCKOUT_PARAMETERS", None) == [["ip_address"]], (
        f"AXES_LOCKOUT_PARAMETERS MORA biti [['ip_address']] (v8 IP-based — SM-D16), dobio "
        f"{getattr(settings, 'AXES_LOCKOUT_PARAMETERS', None)!r} (AC5)."
    )


def test_ac5_axes_lockout_template_set():
    """AC5 settings-nivo: AXES_LOCKOUT_TEMPLATE == 'accounts/lockout.html' (ožičava AC9 stranu)."""
    from django.conf import settings

    assert getattr(settings, "AXES_LOCKOUT_TEMPLATE", None) == "accounts/lockout.html", (
        f"AXES_LOCKOUT_TEMPLATE MORA biti 'accounts/lockout.html', dobio "
        f"{getattr(settings, 'AXES_LOCKOUT_TEMPLATE', None)!r} (AC5 settings → AC9 template)."
    )


def test_ac6_axes_reset_on_success_true():
    """AC6: AXES_RESET_ON_SUCCESS is True (uspešan login resetuje brojač)."""
    from django.conf import settings

    assert getattr(settings, "AXES_RESET_ON_SUCCESS", None) is True, (
        "AXES_RESET_ON_SUCCESS MORA biti True (uspešan login <5 fail-ova resetuje brojač — AC6)."
    )


def test_ac6_successful_login_resets_failure_counter(axes_reset):
    """AC6 ponašanje: 3 neuspela + 1 USPEŠAN login → brojač se RESETUJE (counter restart).

    Dokaz da AXES_RESET_ON_SUCCESS=True STVARNO radi: posle uspeha brojač kreće od 0,
    pa 4 nova neuspela pokušaja NE smeju zaključati (lock je TEK na 5.). Da reset NIJE
    radio, ukupno 3+4=7 neuspeha bi davno premašilo limit 5 → 429.
    """
    password = "Sigurna-Lozinka-123!"
    _make_staff_user(email="resetme@coricagrar.rs", username="resetme", password=password)
    remote = "203.0.113.77"  # distinct IP → bez bleed-a sa drugim lockout testovima
    client = Client(REMOTE_ADDR=remote)
    login_url = reverse("admin:login")

    # 3 neuspela pokušaja (brojač = 3, < 5 → bez lockout-a)
    for _i in range(3):
        client.get(login_url)
        resp = client.post(
            login_url,
            {"username": "resetme@coricagrar.rs", "password": "POGRESNO", "next": reverse("admin:index")},
        )
        assert resp.status_code != 429, "Pre uspeha pokušaji 1–3 NE smeju zaključati (< limit)."

    # 1 USPEŠAN login → AXES_RESET_ON_SUCCESS resetuje brojač na 0
    client.get(login_url)
    ok = client.post(
        login_url,
        {"username": "resetme@coricagrar.rs", "password": password, "next": reverse("admin:index")},
    )
    assert ok.status_code == 302, (
        f"Uspešan login (3 fail-a < 5) MORA proći (302) — još nije zaključan; dobio {ok.status_code}."
    )

    # 4 nova neuspela pokušaja: ako je reset radio, brojač je sada 1..4 (< 5) → BEZ lockout-a.
    last = None
    for i in range(1, 5):
        client.get(login_url)
        last = client.post(
            login_url,
            {"username": "resetme@coricagrar.rs", "password": "POGRESNO", "next": reverse("admin:index")},
        )
        assert last.status_code != 429, (
            f"Posle uspešnog login-a brojač MORA krenuti od 0 (AXES_RESET_ON_SUCCESS) — "
            f"4 nova fail-a NE smeju zaključati; pokušaj #{i} dao {last.status_code}. "
            "429 ovde = reset NIJE radio (3+ stari fail-ovi i dalje broje)."
        )


# ══════════════════════════════════════════════════════════════════════════════
# AC8 — session timeout 4h
# ══════════════════════════════════════════════════════════════════════════════
def test_ac8_session_cookie_age_4h():
    """AC8: SESSION_COOKIE_AGE == 14400 (4h u sekundama)."""
    from django.conf import settings

    assert settings.SESSION_COOKIE_AGE == 14400, (
        f"SESSION_COOKIE_AGE MORA biti 14400 (4h — AC8/epics:1067), dobio {settings.SESSION_COOKIE_AGE}."
    )


def test_ac8_session_not_expire_at_browser_close():
    """AC8/G-10: SESSION_EXPIRE_AT_BROWSER_CLOSE ostaje False (4h apsolutni timeout)."""
    from django.conf import settings

    assert getattr(settings, "SESSION_EXPIRE_AT_BROWSER_CLOSE", False) is False, (
        "SESSION_EXPIRE_AT_BROWSER_CLOSE MORA ostati False (inače poništava 4h trajanje — G-10)."
    )


# ══════════════════════════════════════════════════════════════════════════════
# AC7 — AdminLoginForm email-as-username, STVARNO ožičena
# ══════════════════════════════════════════════════════════════════════════════
def test_ac7_form_class_exists_and_subclasses_admin_auth_form():
    """AC7/SM-D13: AdminLoginForm postoji + subclass AdminAuthenticationForm (is_staff guard)."""
    from django.contrib.admin.forms import AdminAuthenticationForm

    from apps.accounts.forms import AdminLoginForm

    assert issubclass(AdminLoginForm, AdminAuthenticationForm), (
        "AdminLoginForm MORA naslediti AdminAuthenticationForm (zadržava confirm_login_allowed "
        "is_staff proveru — SM-D13)."
    )


def test_ac7_form_wired_into_admin_site():
    """AC7/SM-D13/CRITICAL-5: admin.site.login_form IS AdminLoginForm (STVARNO ožičena)."""
    from django.contrib import admin

    from apps.accounts.forms import AdminLoginForm

    assert admin.site.login_form is AdminLoginForm, (
        "django.contrib.admin.site.login_form MORA BITI AdminLoginForm (ožičeno u "
        "AccountsConfig.ready() — NE dangling klasa; AC7/SM-D13)."
    )


def test_ac7_email_login_reaches_authenticate_and_succeeds():
    """AC7: login POST sa EMAIL-om kao identifikatorom rezolvuje → authenticate() → uspeh."""
    password = "Sigurna-Lozinka-123!"
    _make_staff_user(email="director@coricagrar.rs", username="director", password=password)
    _reset_axes_state()  # čist axes pre validnog login-a (G-12)

    client = Client()
    login_url = reverse("admin:login")
    # GET prvo da pokupi CSRF token
    client.get(login_url)
    response = client.post(
        login_url,
        {
            "username": "director@coricagrar.rs",  # EMAIL u username polju (email-as-username)
            "password": password,
            "next": reverse("admin:index"),
        },
    )
    _reset_axes_state()
    # uspešan login → redirect (302) na next; NE re-render forme (200 sa greškom)
    assert response.status_code in (302, 200), f"neočekivan status {response.status_code}"
    assert response.status_code == 302, (
        "Validan EMAIL+password POST MORA proći authenticate() i redirektovati (302) na admin "
        f"index — email→user rezolucija radi (AC7/SM-D13). Dobio {response.status_code} "
        "(re-render = email nije rezolvovan na usera)."
    )


def test_ac7_non_staff_email_cannot_login(axes_reset):
    """AC7/SM-D13 SECURITY: non-staff user (is_staff=False) sa VALIDNIM email+password NE sme ući.

    `AdminLoginForm.confirm_login_allowed` (nasleđeno iz AdminAuthenticationForm) MORA
    odbiti ne-staff naloge čak i kad su kredencijali tačni. Zaključavamo ovaj guard
    protiv regresije (email→user rezolucija NE sme zaobići is_staff proveru).
    """
    from django.contrib.auth import get_user_model

    password = "Sigurna-Lozinka-123!"
    User = get_user_model()
    User.objects.create_user(
        username="obicankorisnik",
        email="obican@coricagrar.rs",
        password=password,
        is_staff=False,
        is_superuser=False,
    )

    client = Client()
    login_url = reverse("admin:login")
    client.get(login_url)  # CSRF token
    response = client.post(
        login_url,
        {
            "username": "obican@coricagrar.rs",  # EMAIL u username polju
            "password": password,
            "next": reverse("admin:index"),
        },
    )
    # Odbijen: re-render forme (200), NE redirect (302) na admin index.
    assert response.status_code == 200, (
        "Non-staff nalog sa validnim kredencijalima MORA biti ODBIJEN (200 re-render forme, "
        f"NE 302 redirect — confirm_login_allowed is_staff guard, AC7/SM-D13). Dobio "
        f"{response.status_code} (302 = guard probijen!)."
    )
    # Sesija NE sme biti autentifikovana.
    assert "_auth_user_id" not in client.session, (
        "Non-staff login NE SME autentifikovati sesiju (_auth_user_id mora biti odsutan — "
        "is_staff guard, AC7/SM-D13)."
    )


def test_ac7_form_uses_get_user_model_not_direct_import():
    """AC7: forms.py koristi get_user_model() (NIKAD `from django.contrib.auth.models import User`)."""
    import inspect

    from apps.accounts import forms

    src = inspect.getsource(forms)
    assert "get_user_model" in src, (
        "AdminLoginForm MORA koristiti get_user_model() za email→user rezoluciju (project-context)."
    )
    assert "from django.contrib.auth.models import User" not in src, (
        "NIKAD direktan `from django.contrib.auth.models import User` — koristi get_user_model() "
        "(project-context.md)."
    )


# ══════════════════════════════════════════════════════════════════════════════
# AC4 — axes lockout off-by-one: 1–4 → login-fail; 5. → lockout 429
# ══════════════════════════════════════════════════════════════════════════════
def test_ac4_attempts_1_to_4_not_locked_out(axes_reset):
    """AC4/SM-D16: neuspeli pokušaji 1–4 → NIJE lockout (200/login-fail re-render, NE 429)."""
    _make_staff_user(email="lockme@coricagrar.rs", username="lockme")
    client = Client()
    login_url = reverse("admin:login")

    for i in range(1, 5):  # pokušaji 1,2,3,4
        client.get(login_url)
        response = client.post(
            login_url,
            {"username": "lockme@coricagrar.rs", "password": "POGRESNO", "next": reverse("admin:index")},
        )
        assert response.status_code != 429, (
            f"Pokušaj #{i} (od 4) NE SME biti lockout (429) — axes zaključava TEK na 5. (SM-D16). "
            f"Dobio {response.status_code}."
        )


def test_ac4_fifth_attempt_triggers_lockout_429(axes_reset):
    """AC4/SM-D16: 5. neuspeli pokušaj SAM triggeruje lockout → HTTP 429 (lock AT limit)."""
    _make_staff_user(email="lockme5@coricagrar.rs", username="lockme5")
    client = Client()
    login_url = reverse("admin:login")

    last = None
    for _i in range(5):  # 5 neuspelih pokušaja
        client.get(login_url)
        last = client.post(
            login_url,
            {"username": "lockme5@coricagrar.rs", "password": "POGRESNO", "next": reverse("admin:index")},
        )
    assert last is not None and last.status_code == 429, (
        f"5. neuspeli pokušaj MORA triggerovati lockout (429 — AXES_HTTP_RESPONSE_CODE; "
        f"OFF-BY-ONE lock NA limitu, SM-D16/AC4). Dobio {last.status_code if last else None}."
    )


# ══════════════════════════════════════════════════════════════════════════════
# AC9 / AC9b — lockout template: 429 + srpski + STANDALONE
# ══════════════════════════════════════════════════════════════════════════════
def test_ac9_lockout_response_renders_serbian_text(axes_reset):
    """AC9: lockout odgovor (429) sadrži srpski tekst sa dijakritikama (zaključan)."""
    _make_staff_user(email="srlock@coricagrar.rs", username="srlock")
    client = Client()
    login_url = reverse("admin:login")
    for _i in range(5):
        client.get(login_url)
        resp = client.post(
            login_url,
            {"username": "srlock@coricagrar.rs", "password": "POGRESNO", "next": reverse("admin:index")},
        )
    assert resp.status_code == 429
    body = resp.content.decode("utf-8")
    assert "zaključan" in body or "zaključ" in body or "pokušaj" in body, (
        "Lockout strana MORA sadržati srpski tekst sa dijakritikama (zakljucan/pokusaj) - "
        f"AC9. Telo (prvih 300): {body[:300]!r}"
    )


def test_ac9b_lockout_template_standalone_no_base_html(axes_reset):
    """AC9b/SM-D11/CRITICAL-4: lockout template STANDALONE — renderuje BEZ context-procesor greške.

    Ako extends base.html → render bi mogao baciti grešku (consent_state/latest_blog_posts
    context_processori NISU garantovani VAN view pipeline-a). Asertujemo: 429 + sopstveni
    <!DOCTYPE html> + NEMA base.html markera (footer „Najnovije vesti" / consent banner).
    """
    _make_staff_user(email="standalone@coricagrar.rs", username="standalone")
    client = Client()
    login_url = reverse("admin:login")
    for _i in range(5):
        client.get(login_url)
        resp = client.post(
            login_url,
            {"username": "standalone@coricagrar.rs", "password": "POGRESNO", "next": reverse("admin:index")},
        )
    assert resp.status_code == 429, (
        f"Lockout render MORA uspeti (429) BEZ template/context greške (standalone — AC9b). "
        f"Dobio {resp.status_code}."
    )
    body = resp.content.decode("utf-8")
    assert "<!doctype html" in body.lower() or "<html" in body.lower(), (
        "STANDALONE lockout template MORA imati sopstveni <!DOCTYPE html>/<html> (NE extends "
        "base.html — SM-D11)."
    )
    # base.html footer markeri koji bi se RENDEROVALI da lockout extends base.html.
    # (Rendered footer eyebrow je UPPERCASE „NAJNOVIJE VESTI" preko section_eyebrow.html;
    #  „Najnovije vesti" u footer.html je SAMO {# komentar #} → ne pojavljuje se u telu,
    #  pa case-sensitive provera na tu varijantu NE bi hvatala leak. Koristimo rendered
    #  markere case-insensitive: footer eyebrow + blog-empty-state string.)
    low = body.lower()
    assert "najnovije vesti" not in low, (
        "Lockout template NE SME sadržati base.html footer eyebrow NAJNOVIJE VESTI "
        "(rendered preko latest_blog_posts kolone) — dokazuje STANDALONE (AC9b/SM-D11). "
        f"Telo (prvih 400): {body[:400]!r}"
    )
    assert "uskoro nove priče sa polja" not in low, (
        "Lockout template NE SME sadržati base.html footer blog-empty-state marker — "
        "to bi značilo da extends base.html (latest_blog_posts context processor; AC9b/SM-D11)."
    )


# ══════════════════════════════════════════════════════════════════════════════
# AC12 — axes migracije u planu
# ══════════════════════════════════════════════════════════════════════════════
def test_ac12_axes_migrations_in_plan():
    """AC12: axes app ima migracije (loader vidi `axes` migracije bez greške)."""
    from django.db.migrations.loader import MigrationLoader
    from django.db import connection

    loader = MigrationLoader(connection)
    axes_migs = [m for m in loader.disk_migrations if m[0] == "axes"]
    assert axes_migs, (
        "django-axes MORA doneti svoje migracije (axes.0001.. → AccessAttempt/AccessLog/"
        "AccessFailureLog). Loader nije našao nijednu axes migraciju (AC12)."
    )


def test_ac12_accounts_has_no_pending_schema_migration():
    """AC12/Task7.1: apps.accounts NE generiše schema migraciju (prazan models.py)."""
    from django.apps import apps as django_apps

    accounts_models = django_apps.get_app_config("accounts").get_models()
    assert list(accounts_models) == [], (
        "apps.accounts NE SME imati modele u v1 (prazan models.py — SM-D3/AC12); "
        f"našao {[m.__name__ for m in accounts_models]}."
    )


# ══════════════════════════════════════════════════════════════════════════════
# AC10 — regresija: postojeći admin testovi prolaze kroz reverse + force_login
# ══════════════════════════════════════════════════════════════════════════════
def test_ac10_force_login_staff_can_access_admin():
    """AC10: force_login staff usera → admin index (200) na novom /admin-coric/ (reverse resolve)."""
    user = _make_staff_user(email="staff@coricagrar.rs", username="staffuser")
    client = Client()
    client.force_login(user)  # force_login zaobilazi axes (G-5) — blast-radius 0
    response = client.get(reverse("admin:index"))
    assert response.status_code == 200, (
        f"force_login staff → reverse('admin:index') MORA biti 200 na /admin-coric/ "
        f"(regresija postojećih admin testova — AC10/SM-D2). Dobio {response.status_code}."
    )


def test_ac10_anonymous_redirected_to_admin_login():
    """AC10/security: anoniman GET admin index → redirect na admin login (302)."""
    response = Client().get(reverse("admin:index"))
    assert response.status_code == 302, (
        f"Anoniman pristup admin index MORA redirektovati (302) na login (security baseline), "
        f"dobio {response.status_code}."
    )
    assert "/admin-coric/login/" in response.get("Location", ""), (
        f"Redirect MORA voditi na /admin-coric/login/, dobio {response.get('Location')!r}."
    )


# ══════════════════════════════════════════════════════════════════════════════
# Sanity: reverse('admin:index') resolve-uje (NoReverseMatch = admin nije mount-ovan)
# ══════════════════════════════════════════════════════════════════════════════
def test_admin_index_reverse_resolves():
    """Sanity (AC3): reverse('admin:index') NE baca NoReverseMatch (admin je mount-ovan)."""
    try:
        url = reverse("admin:index")
    except NoReverseMatch:
        pytest.fail("reverse('admin:index') baca NoReverseMatch — admin nije mount-ovan na admin-coric/.")
    assert url.startswith("/admin-coric/")
