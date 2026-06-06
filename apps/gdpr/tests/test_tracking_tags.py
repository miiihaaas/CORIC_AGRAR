"""Story 7.3 — AC2/AC3: `{% ga_pixel %}` + `{% fb_pixel %}` tracking tagovi (TEA RED).

Pokriva AC2/AC3 + SM-D3/D4/D10/D11 + Gotcha G-1/G-3/G-5/G-6/G-12/G-13 + CRITICAL-1/2:
- `{% ga_pixel %}` render-uje GA4 gtag SAMO uz consent_state.analytical + neprazan
  GA_MEASUREMENT_ID; inace "". `{% fb_pixel %}` mirror za marketing + FB_PIXEL_ID.
- CRITICAL-1 (brace-safe build): brace-heavy JS telo (`function gtag(){...}`,
  fbq IIFE) render-uje se LITERALNO sa JEDNOSTRUKIM `{`/`}` (NIKAD `{{`), NIKAD 500.
- CRITICAL-2 (strict is True): forged `{"analytical":"yes"}` → context_processor →
  ga_pixel render "" (end-to-end).
- G-1 (privacy-fail-safe): `{% ga_pixel %}` sa `Context()` BEZ consent_state →
  .get(DEFAULT_DENY) → render "" (NEMA trackera, NEMA exception-a; mis-registracija
  je pokrivena dedikovanim registration testom).
- ID escaped kroz format_html (defense-in-depth, G-5).

RED razlog: `apps/gdpr/templatetags/tracking.py` NE postoji → `{% load tracking %}`
baca TemplateSyntaxError ('tracking' is not a registered tag library).

⚠️ COLLECTION-SAFETY: `{% load tracking %}` ide kroz Template().render() UNUTAR
test funkcija; nema module-level zavisnosti od jos-nepostojeceg taga.

Pokrenuti:
    docker compose -f compose/local.yml run --rm django \
        uv run pytest apps/gdpr/tests/test_tracking_tags.py -v

Refs: 7-3 AC2/AC3 + SM-D3/D4/D10/D11 + Gotcha G-1/G-3/G-5/G-6/G-12/G-13;
      7-3-interface-contract § tags.
"""

from __future__ import annotations

from django.template import Context, Template
from django.test import override_settings

# Tagovi su cisti (settings + context) → DB nije potreban.

_GA_TPL = "{% load tracking %}{% ga_pixel %}"
_FB_TPL = "{% load tracking %}{% fb_pixel %}"


def _ctx(analytical=False, marketing=False):
    """Mirror context_processor izlaza: context["consent_state"] je obican dict bool-ova."""
    return Context(
        {
            "consent_state": {
                "necessary": True,
                "analytical": analytical,
                "marketing": marketing,
            }
        }
    )


# ── GA4 (AC2) ────────────────────────────────────────────────────────────────


# AC2: analytical=True + GA_MEASUREMENT_ID set → render-uje gtag snippet sa ID-em
@override_settings(GA_MEASUREMENT_ID="G-TEST123")
def test_ga_pixel_renders_when_analytical_and_id():
    html = Template(_GA_TPL).render(_ctx(analytical=True))
    assert "https://www.googletagmanager.com/gtag/js?id=G-TEST123" in html, (
        f"`{{% ga_pixel %}}` MORA render-ovati gtag.js src sa ID-em. Dobio: {html!r}"
    )
    assert "gtag('config', 'G-TEST123')" in html, (
        f"`{{% ga_pixel %}}` MORA sadrzati inline gtag('config', '<ID>'). Dobio: {html!r}"
    )


# AC2/CRITICAL-1/G-13: brace-heavy gtag telo LITERALNO (jednostruke brace), NIKAD 500
@override_settings(GA_MEASUREMENT_ID="G-TEST123")
def test_ga_snippet_literal_braces_no_500():
    # Render NE sme baciti KeyError/ValueError/IndexError (brace-heavy JS kroz
    # format_html format-string bi 500-ovao — MORA ici kroz mark_safe; SM-D11).
    html = Template(_GA_TPL).render(_ctx(analytical=True))
    assert "function gtag(){dataLayer.push(arguments);}" in html, (
        "CRITICAL-1 (G-13/SM-D11): brace-heavy gtag telo MORA biti render-ovano "
        "LITERALNO sa JEDNOSTRUKIM `{`/`}` (staticki mark_safe string, NE kroz "
        f"format_html format-string). Dobio: {html!r}"
    )
    assert "{{" not in html and "}}" not in html, (
        "Izlaz NE sme sadrzati udvojene `{{`/`}}` (to bi znacilo da je JS proslo "
        f"kroz format_html sa doubling-om umesto mark_safe). Dobio: {html!r}"
    )
    assert "gtag(" in html, f"Snippet MORA sadrzati gtag( poziv. Dobio: {html!r}"


# AC2: analytical=False → "" (NEMA gtag/googletagmanager)
@override_settings(GA_MEASUREMENT_ID="G-TEST123")
def test_ga_pixel_empty_when_analytical_false():
    html = Template(_GA_TPL).render(_ctx(analytical=False))
    assert html.strip() == "", (
        f"analytical=False → `{{% ga_pixel %}}` MORA vratiti \"\". Dobio: {html!r}"
    )
    assert "googletagmanager" not in html and "gtag(" not in html, (
        f"Bez consent-a NEMA tracker tokena. Dobio: {html!r}"
    )


# AC2/G-3: analytical=True ALI GA_MEASUREMENT_ID prazan (dev/test default) → ""
@override_settings(GA_MEASUREMENT_ID="")
def test_ga_pixel_empty_when_id_blank():
    html = Template(_GA_TPL).render(_ctx(analytical=True))
    assert html.strip() == "", (
        "no-ID grana (G-3): prazan GA_MEASUREMENT_ID → `{% ga_pixel %}` vraca \"\" "
        f"CAK I uz analytical=True. Dobio: {html!r}"
    )


# AC2: default-deny consent (analytical False) → ""
@override_settings(GA_MEASUREMENT_ID="G-TEST123")
def test_ga_pixel_empty_when_consent_default_deny():
    html = Template(_GA_TPL).render(_ctx())  # oba False (default-deny)
    assert html.strip() == "", (
        f"DEFAULT-DENY consent → `{{% ga_pixel %}}` vraca \"\". Dobio: {html!r}"
    )


# ── FB Pixel (AC3) ───────────────────────────────────────────────────────────


# AC3: marketing=True + FB_PIXEL_ID set → render-uje fbq init + PageView + noscript
@override_settings(FB_PIXEL_ID="123456")
def test_fb_pixel_renders_when_marketing_and_id():
    html = Template(_FB_TPL).render(_ctx(marketing=True))
    assert "fbq('init', '123456')" in html, (
        f"`{{% fb_pixel %}}` MORA sadrzati fbq('init', '<ID>'). Dobio: {html!r}"
    )
    assert "fbq('track', 'PageView')" in html, (
        f"`{{% fb_pixel %}}` MORA sadrzati fbq('track', 'PageView'). Dobio: {html!r}"
    )
    assert "https://www.facebook.com/tr?id=123456" in html, (
        f"`{{% fb_pixel %}}` MORA sadrzati noscript img ka facebook.com/tr. Dobio: {html!r}"
    )


# AC3/CRITICAL-1/G-13: brace-heavy fbq IIFE LITERALNO (jednostruke brace), NIKAD 500
@override_settings(FB_PIXEL_ID="123456")
def test_fb_snippet_literal_braces_no_500():
    html = Template(_FB_TPL).render(_ctx(marketing=True))
    assert "!function(f,b,e,v,n,t,s){" in html, (
        "CRITICAL-1 (G-13/SM-D11): brace-heavy fbq IIFE MORA biti render-ovan "
        "LITERALNO sa JEDNOSTRUKIM `{` (staticki mark_safe, NE format_html "
        f"format-string). Dobio: {html!r}"
    )
    assert "{{" not in html and "}}" not in html, (
        f"Izlaz NE sme sadrzati udvojene `{{`/`}}` (mark_safe, NE doubling). Dobio: {html!r}"
    )


# AC3: marketing=False → "" (NEMA fbq/facebook tracker UKLJUCUJUCI noscript — G-6)
@override_settings(FB_PIXEL_ID="123456")
def test_fb_pixel_empty_when_marketing_false():
    html = Template(_FB_TPL).render(_ctx(marketing=False))
    assert html.strip() == "", (
        f"marketing=False → `{{% fb_pixel %}}` MORA vratiti \"\". Dobio: {html!r}"
    )
    assert "fbq(" not in html and "facebook.com/tr" not in html, (
        f"Bez marketing consent-a NEMA fbq/facebook.com/tr tokena. Dobio: {html!r}"
    )


# AC3/G-6: noscript FB img je TAKODJE gated — marketing=False → NEMA <noscript> FB img
@override_settings(FB_PIXEL_ID="123456")
def test_fb_noscript_gated_by_consent():
    html = Template(_FB_TPL).render(_ctx(marketing=False))
    assert "facebook.com/tr" not in html and "<noscript>" not in html, (
        "G-6: `<noscript><img ...facebook.com/tr>` je DEO gated render izlaza → "
        "marketing=False → NE sme biti prisutan (bio bi tracker bez consent-a). "
        f"Dobio: {html!r}"
    )


# AC3/G-3: marketing=True ALI FB_PIXEL_ID prazan → ""
@override_settings(FB_PIXEL_ID="")
def test_fb_pixel_empty_when_id_blank():
    html = Template(_FB_TPL).render(_ctx(marketing=True))
    assert html.strip() == "", (
        "no-ID grana (G-3): prazan FB_PIXEL_ID → \"\" CAK I uz marketing=True. "
        f"Dobio: {html!r}"
    )


# ── Security / escaping (G-5/SM-D4) ──────────────────────────────────────────


# AC2/G-5/SM-D4: ID escaped kroz format_html (defense-in-depth) — sirov "/< NE u izlazu
@override_settings(GA_MEASUREMENT_ID='G-"<x>')
def test_ga_id_is_escaped():
    html = Template(_GA_TPL).render(_ctx(analytical=True))
    # format_html escape-uje ID → maliciozni karakteri (`"`, `<`) iz ID-a postaju
    # entity-ji (&quot;/&lt;). NIKAD mark_safe(f"...{gid}...") na neescapiranom ID-u.
    assert "&quot;" in html and "&lt;" in html, (
        "G-5/SM-D4: ID se injektuje kroz format_html (escape) → `\"`/`<` iz ID-a "
        f"escape-ovani u &quot;/&lt;. Dobio: {html!r}"
    )
    # Sirov `<x>` (iz ID-a, NE legitimni `<script async src=`) NE sme proci neescapiran.
    assert "G-\"<x>" not in html, (
        "Sirov neescapiran ID (`G-\"<x>`) NE sme biti u izlazu (defense-in-depth). "
        f"Dobio: {html!r}"
    )


# ── End-to-end strict is True (CRITICAL-2 / SM-D10) ──────────────────────────


# AC2/CRITICAL-2/SM-D10: forged "yes" → context_processor → ga_pixel render ""
@override_settings(GA_MEASUREMENT_ID="G-TEST123")
def test_forged_string_truthy_renders_nothing():
    from apps.gdpr.context_processors import consent_state
    from django.test import RequestFactory

    request = RequestFactory().get("/sr/")
    request.COOKIES["consent_state"] = '{"analytical": "yes", "marketing": "yes"}'
    ctx_dict = consent_state(request)  # {"consent_state": {... analytical False ...}}

    html_ga = Template(_GA_TPL).render(Context(ctx_dict))
    html_fb = Template(_FB_TPL).render(Context(ctx_dict))
    assert html_ga.strip() == "", (
        "CRITICAL-2 end-to-end: forged `{\"analytical\":\"yes\"}` → context_processor "
        f"daje analytical=False → ga_pixel render \"\". Dobio: {html_ga!r}"
    )
    assert html_fb.strip() == "", (
        f"CRITICAL-2 end-to-end: forged marketing \"yes\" → fb_pixel \"\". Dobio: {html_fb!r}"
    )


# ── Library load + privacy-fail-safe (G-1) ───────────────────────────────────


# AC2: `{% load tracking %}` ucitava tagove (oba)
@override_settings(GA_MEASUREMENT_ID="", FB_PIXEL_ID="")
def test_tracking_library_loads():
    # Ako `tracking` lib / tagovi ne postoje → TemplateSyntaxError pri compile-u.
    html = Template("{% load tracking %}{% ga_pixel %}{% fb_pixel %}").render(_ctx())
    assert html.strip() == "", (
        f"`{{% load tracking %}}` MORA registrovati ga_pixel + fb_pixel. Dobio: {html!r}"
    )


# AC2/G-1: ga_pixel sa Context() BEZ consent_state → .get(DEFAULT_DENY) → "" (NEMA
# exception-a; privacy-fail-safe — config slip / NEregistrovan cp → no-tracking, NE 500).
@override_settings(GA_MEASUREMENT_ID="G-TEST123")
def test_ga_pixel_missing_consent_state_renders_nothing():
    html = Template(_GA_TPL).render(Context({}))  # NEMA consent_state ključa
    assert html.strip() == "", (
        "G-1 (privacy-fail-safe): `{% ga_pixel %}` bez consent_state → "
        f"DEFAULT_DENY → \"\" (no-tracking), NIKAD KeyError/500. Dobio: {html!r}"
    )
    assert "googletagmanager" not in html and "gtag(" not in html, (
        f"Bez consent_state ključa NEMA GA tracker tokena. Dobio: {html!r}"
    )


# AC3/G-1: fb_pixel sa Context() BEZ consent_state → .get(DEFAULT_DENY) → "" (no-tracking)
@override_settings(FB_PIXEL_ID="123456")
def test_fb_pixel_missing_consent_state_renders_nothing():
    html = Template(_FB_TPL).render(Context({}))  # NEMA consent_state ključa
    assert html.strip() == "", (
        "G-1 (privacy-fail-safe): `{% fb_pixel %}` bez consent_state → "
        f"DEFAULT_DENY → \"\" (no-tracking), NIKAD KeyError/500. Dobio: {html!r}"
    )
    assert "fbq(" not in html and "facebook.com/tr" not in html, (
        f"Bez consent_state ključa NEMA FB tracker tokena. Dobio: {html!r}"
    )
