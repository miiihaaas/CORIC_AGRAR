"""Story 6.5 — {% translated_field obj 'field' %} i18n fallback marker tag.

DRUGI tag-modul u apps.core (uz `htmx_aria.py`). Ekspoze
`{% translated_field obj 'name' %}` `simple_tag(takes_context=True)` koji DETEKTUJE
da li je translated polje fallback-ovano na sr za aktivnu locale i — ako jeste —
renderuje diskretan `coric-fallback-marker` span (sr tekst + inline ⓘ SVG +
CSS-only tooltip „Sadržaj na srpskom — još nije preveden", lokalizovan), sa
`lang="sr"` atributom na fallback tekstu.

CRUX (SM-D1, G1): fallback se NE detektuje kroz `obj.field`. Projekt ima
`MODELTRANSLATION_FALLBACK_LANGUAGES = ("sr",)` (config/settings/base.py:157), pa
`obj.name` na /hu/ VEĆ tiho vraća `name_sr` kad je `name_hu` prazan (silent
fallback chain — to je cela svrha). Poređenje `obj.name == obj.name_sr` bi bilo
LAŽNO (True i na fallback-u i kad je hu slučajno identičan sr). Zato tag čita
SIROVI per-locale accessor `getattr(obj, f"{field}_{lang}", _UNSET)` i testira da
li je TA kolona prazna — JEDINI pouzdan signal.

Security (SM-D2/AC7): vrednost polja UVEK ide kroz `format_html("{}", ...)` →
autoescaped (XSS granica). `mark_safe` SAMO na statičkom `_INFO_ICON_SVG` (nema
user input) — NIKAD na vrednosti polja.
"""

from __future__ import annotations

import itertools

from django import template
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import get_language, gettext

register = template.Library()

# Sentinel: razlikuje „accessor ne postoji" (ne-translated polje / pogrešno ime)
# od „accessor vraća None/prazno" (fallback kandidat).
_UNSET = object()

# Modul-level monotoni brojač — SAMO kao fallback kad `request` nije u context-u
# (shell / management / izolovan render). NIKAD statična string-konstanta (to bi
# dalo svim markerima isti id → slomljena aria-describedby uniqueness; G5).
_FALLBACK_ID_FALLBACK_COUNTER = itertools.count(1)

# Inline ⓘ ikona — STVARNI Bootstrap Icons `info-circle` (MIT) path data. NE
# vendiramo ceo icon font (~100KB+) za jednu ikonu (anti-perf; SM-D5). `mark_safe`
# je OBAVEZAN (statički markup, NE user input → bezbedno): bez njega `format_html`
# escape-uje SVG u literal `&lt;svg&gt;` (G3b). `currentColor` nasleđuje marker boju.
_INFO_ICON_SVG = mark_safe(
    '<svg class="coric-fallback-marker__icon" xmlns="http://www.w3.org/2000/svg"'
    ' width="1em" height="1em" viewBox="0 0 16 16" fill="currentColor"'
    ' aria-hidden="true" focusable="false">'
    '<path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/>'
    '<path d="m8.93 6.588-2.29.287-.082.38.45.083c.294.07.352.176.288.469l-.738 '
    "3.468c-.194.897.105 1.319.808 1.319.545 0 1.178-.252 1.465-.598l.088-.416c-.2."
    "176-.492.246-.686.246-.275 0-.375-.193-.304-.533L8.93 6.588zM9 4.5a1 1 0 1 "
    '1-2 0 1 1 0 0 1 2 0z"/>'
    "</svg>"
)


def _next_tooltip_id(context):
    """Jedinstven `fallback-tooltip-N` id po markeru (SM-D3/AC3/G5).

    Primarno: per-request brojač `request._coric_fallback_counter` (resetuje se
    svaki request → deterministički -1/-2/...). Fallback (request=None): modul-level
    monotoni `itertools.count(1)` (jedinstven unutar render-a, cross-request
    ne-determinizam prihvaćen). NIKAD statična string-konstanta.
    """
    request = context.get("request")
    if request is not None:
        n = getattr(request, "_coric_fallback_counter", 0) + 1
        setattr(request, "_coric_fallback_counter", n)
        return f"fallback-tooltip-{n}"
    return f"fallback-tooltip-{next(_FALLBACK_ID_FALLBACK_COUNTER)}"


def _render_marker(context, sr_text):
    """Renderuj `coric-fallback-marker` span (tooltip je DETE markera; G4).

    `sr_text` i `tooltip_text` su `{}` placeholder-i → AUTOESCAPED (AC7).
    `_INFO_ICON_SVG` je pre-`mark_safe`-ovan → `format_html` ga propušta kao
    SafeString (NE postaje literal `&lt;svg&gt;`).
    """
    tooltip_id = _next_tooltip_id(context)
    # Runtime gettext (NE modul-level / lazy-cache) → po-request visitor locale (SM-D4).
    tooltip_text = gettext("Sadržaj na srpskom — još nije preveden")
    return format_html(
        '<span class="coric-fallback-marker" tabindex="0" aria-describedby="{}"'
        ' lang="sr">{} {}'
        '<span class="coric-fallback-marker__tooltip" id="{}" role="tooltip">{}'
        "</span></span>",
        tooltip_id,
        sr_text,
        _INFO_ICON_SVG,
        tooltip_id,
        tooltip_text,
    )


@register.simple_tag(takes_context=True)
def translated_field(context, obj, field):
    """Vraća SafeString: plain escaped vrednost polja (no fallback) ILI
    `coric-fallback-marker` span (fallback detektovan; SM-D1).
    """
    if obj is None:
        return ""

    # BCP-47 normalizacija (G9): get_language() može vratiti `en-us`/`sr-latn`,
    # a modeltranslation kolone su `name_en`/`name_sr` (BEZ subtag-a). Bez ovoga
    # `name_en-us` accessor uvek promaši → marker se TIHO nikad ne pojavi za en.
    lang = (get_language() or "sr").split("-")[0]

    # sr je izvorni jezik — NIKAD marker (nema fallback-a). Pokriva i None→sr i
    # normalizovan sr-latn→sr.
    if lang == "sr":
        return format_html("{}", str(getattr(obj, field, "") or ""))

    # CRUX (SM-D1/G1): čitaj SIROVI per-locale accessor — NE `obj.field` (već
    # fallback-uje). Signal = „je li `field_<lang>` kolona PRAZNA".
    current = getattr(obj, f"{field}_{lang}", _UNSET)

    if current is _UNSET:
        # Accessor ne postoji (ne-translated polje / pogrešno ime) → graceful plain.
        return format_html("{}", str(getattr(obj, field, "") or ""))

    if current and str(current).strip():
        # Popunjeno za ovu locale (whitespace-only = prazno; G7) → no fallback.
        return format_html("{}", str(current))

    # Prazno/blank current = FALLBACK kandidat.
    sr_val = getattr(obj, f"{field}_sr", None)
    if not (sr_val and str(sr_val).strip()):
        # Ni sr nema vrednost → nema teksta za markirati → plain.
        return format_html("{}", str(getattr(obj, field, "") or ""))
    return _render_marker(context, sr_val)
