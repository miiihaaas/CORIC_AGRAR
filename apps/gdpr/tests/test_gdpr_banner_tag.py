"""Story 7.2 — AC1: `{% gdpr_banner %}` template tag (TEA RED phase).

Pokriva AC1 + SM-D2 + Gotcha G-1:
- tag renderuje baner partial SAMO kad `consent_state` kolačić ODSUTAN u
  request.COOKIES; vraća "" (prazan string) kad je prisutan (BILO koja vrednost,
  uključujući garbage → presence-only suppression).
- baner sadrži CSRF token (`csrfmiddlewaretoken`) — dokazuje `render_to_string(
  ..., request=request)` (G-1; bez `request=request` kwarg-a `{% csrf_token %}`
  ne radi → forma submit → 403).
- hidden `next` input == `request.get_full_path()`.
- „Više info" href == reverse("gdpr:cookie_policy").

RED razlog: `apps/gdpr/templatetags/gdpr_banner.py` + `templates/gdpr/
_consent_banner.html` NE postoje → `{% load gdpr_banner %}` baca
TemplateSyntaxError, a `reverse("gdpr:set_consent")` NoReverseMatch.

⚠️ COLLECTION-SAFETY: render banera ide kroz `Template`/`render_to_string`
UNUTAR test funkcija; nema module-level zavisnosti od još-nepostojeceg taga.

Pokrenuti:
    docker compose -f compose/local.yml run --rm django \
        uv run pytest apps/gdpr/tests/test_gdpr_banner_tag.py -v

Refs: 7-2 AC1/AC6 + SM-D2 + Gotcha G-1; 7-2-interface-contract § 1 (tag).
"""

from __future__ import annotations

import re

import pytest
from django.template import Context, Template
from django.test import RequestFactory
from django.utils.translation import override

pytestmark = pytest.mark.django_db


def _render_tag(cookies=None, path="/sr/"):
    """Renderuj `{% gdpr_banner %}` sa stvarnim request-om u context-u.

    Mirror base.py:82 `request` context_processor: tag cita `context["request"]`.
    `RequestFactory` daje request sa CSRF processing-om kroz render_to_string.
    """
    rf = RequestFactory()
    request = rf.get(path)
    if cookies:
        request.COOKIES.update(cookies)
    tpl = Template("{% load gdpr_banner %}{% gdpr_banner %}")
    return tpl.render(Context({"request": request}))


# AC1: kolačić ODSUTAN → tag renderuje baner partial (role="dialog", forma, dugme)
def test_banner_rendered_when_cookie_absent():
    with override("sr"):
        html = _render_tag(cookies=None)
    assert 'role="dialog"' in html, (
        "Kad `consent_state` kolačić ODSUTAN, `{% gdpr_banner %}` MORA renderovati "
        f"baner partial sa role=\"dialog\" (AC1/SM-D2). Dobio: {html!r}"
    )
    assert "<form" in html and "method=" in html.lower(), (
        "Baner MORA sadržati <form method=post> (AC1/AC6)."
    )
    assert "Prihvati sve" in html, (
        "Baner MORA sadržati dugme Prihvati sve (AC6)."
    )


# AC1: kolačić PRISUTAN (validna vrednost) → tag vraća "" (baner se NE prikazuje)
def test_banner_empty_when_cookie_present():
    with override("sr"):
        html = _render_tag(
            cookies={"consent_state": '{"necessary": true, "analytical": false, "marketing": false}'}
        )
    assert html.strip() == "", (
        "Kad je `consent_state` kolačić PRISUTAN, `{% gdpr_banner %}` MORA vratiti "
        f'"" (posetilac vec izabrao → baner nestaje; AC1/SM-D2). Dobio: {html!r}'
    )


# AC1: kolačić PRISUTAN ali GARBAGE vrednost → i dalje "" (presence-only suppression)
def test_banner_suppressed_for_garbage_cookie_value():
    with override("sr"):
        html = _render_tag(cookies={"consent_state": "garbage-not-json"})
    assert html.strip() == "", (
        "Presence-only suppression: BILO koja prisutna vrednost `consent_state` "
        "(uključujući neispravnu/forge-ovanu) MORA suzbiti baner — tag suzbija na "
        '`"consent_state" in request.COOKIES`, NE parsira JSON (SM-D2/Boundary 7-2↔7-3). '
        f"Dobio: {html!r}"
    )


# AC1/G-1: render-ovan baner sadrži CSRF token → dokaz render_to_string(request=request)
def test_banner_includes_csrf_token():
    with override("sr"):
        html = _render_tag(cookies=None)
    assert re.search(r'name=["\']csrfmiddlewaretoken["\']', html, re.IGNORECASE), (
        "Baner forma MORA sadržati csrfmiddlewaretoken — dokaz da tag prosledi "
        "`request=request` kwarg u render_to_string (G-1). BEZ njega `{% csrf_token %}` "
        f"ne radi → forma submit → 403. Dobio: {html!r}"
    )


# AC1: hidden `next` input == request.get_full_path()
def test_banner_hidden_next_is_current_path():
    with override("sr"):
        html = _render_tag(cookies=None, path="/sr/proizvodi/")
    m = re.search(
        r'<input[^>]*name=["\']next["\'][^>]*value=["\']([^"\']*)["\']',
        html,
        re.IGNORECASE,
    )
    if not m:
        m = re.search(
            r'<input[^>]*value=["\']([^"\']*)["\'][^>]*name=["\']next["\']',
            html,
            re.IGNORECASE,
        )
    assert m, f"Baner MORA imati hidden input name=\"next\" (AC6). Dobio: {html!r}"
    assert m.group(1) == "/sr/proizvodi/", (
        "hidden `next` MORA biti request.get_full_path() (SM-D2/AC6 — za redirect-back "
        f"bez JS), dobio {m.group(1)!r}."
    )


# AC1/AC6: „Više info" href == reverse("gdpr:cookie_policy") (7-1 ruta)
def test_more_info_links_to_cookie_policy():
    from django.urls import reverse

    with override("sr"):
        html = _render_tag(cookies=None)
        policy_url = reverse("gdpr:cookie_policy")
    assert policy_url in html, (
        f"Vise info link MORA pokazivati na reverse('gdpr:cookie_policy') "
        f"(={policy_url!r}; 7-1 ruta /sr/politika-kolacica/; AC6). Dobio: {html!r}"
    )
