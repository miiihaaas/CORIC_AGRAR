"""Story 3.4 — `{% site_setting "field" %}` tag + `|splitlines` filter (SM-D5/SM-D10).

`site_setting` simple_tag radi lazy `SiteSettings.load()` + `getattr` → locale-aware za
translatable polja (modeltranslation virtuelni atribut čita aktivnu lokalu). Radi BEZ view
context-a (view-ovi ostaju netaknuti) i radi na load() default i pre seed-a u test bazi.

Keširanje (contract: „prost query po request-u"):
- PRIMARNI keš (produkcija) = per-request keš na `request` objektu. Header + footer + sve
  {% include %}-ovane partials u JEDNOM response-u dele isti `request` → plaćamo TAČNO
  1 SQL upit po strani. Svež response (novi `request`) re-učitava, pa se save()/delete()/
  QuerySet delete u testovima ispravno reflektuje.
- FALLBACK (context-less render) = uncached `SiteSettings.load()`. Kad nema `request` u
  context-u (npr. `Template().render(Context())` u jediničnim testovima ili interni render
  bez request-a), tag svaki put pozove `load()`. To je YAGNI-prihvatljivo: takav render je
  redak i ne ide na hot path (produkcijske strane uvek imaju `request`).

`splitlines` filter pretvara multi-line `working_hours` u listu nepraznih `.strip()`-ovanih
linija za render kao `<ul>`/`<li>` (SM-D10).
"""

from django import template

from apps.pages.models import SiteSettings

register = template.Library()

_RENDER_CACHE_KEY = "_coric_site_settings"


@register.simple_tag(takes_context=True)
def site_setting(context, field_name):
    """Vrati vrednost SiteSettings polja (locale-aware; 1 upit po request-u).

    PRIMARNI keš: instanca na `request` objektu — preživljava sve {% include %}-ove u
    jednom response-u → TAČNO 1 SQL po strani (produkcijski hot path).
    FALLBACK: kad nema request-a u context-u (context-less render — npr.
    `Template().render(Context())` u jediničnim testovima), uncached `load()` po pozivu.
    """
    request = getattr(context, "request", None) or context.get("request")
    if request is not None:
        cached = getattr(request, _RENDER_CACHE_KEY, None)
        if cached is None:
            cached = SiteSettings.load()
            setattr(request, _RENDER_CACHE_KEY, cached)
        return getattr(cached, field_name, "")

    # Context-less render (nema request): uncached load() — redak put, nije hot path.
    return getattr(SiteSettings.load(), field_name, "")


@register.filter
def splitlines(value):
    """Vrati listu nepraznih, .strip()-ovanih linija; None/"" → []."""
    return [ln.strip() for ln in (value or "").splitlines() if ln.strip()]
