"""Story 6.6 — {% hreflang_links %} HTML hreflang tagovi (ZATVARA Epic 6).

DRUGI tag-modul u apps.seo (uz seo_meta.py). Emituje za TRENUTNI `request.path`
TAČNO 4 `<link rel="alternate" hreflang="...">` taga u `<head>`: sr, hu, en,
x-default (x-default href == sr href; SM-D2).

CRUX (SM-D1) — URL generacija kroz `translate_url(request.path, lang)` +
`request.build_absolute_uri(...)`:
- `translate_url` resolve-uje trenutni path → reverse-uje pod `override(lang)` →
  vraća ekvivalentnu URL sa zamenjenim locale prefiksom (`/sr/proizvod/x/` →
  `/hu/proizvod/x/`). GRACEFULNO vraća original URL ako resolve (Resolver404) ILI
  reverse (NoReverseMatch) padne → tag NIKAD ne 500-uje (G2 — NE try/except).
- `prefix_default_language=True` (config/urls.py) → sr DOBIJA `/sr/` prefiks →
  SVE 4 href-a su prefiksovane (NEMA prefix-less sr; G3).
- `request.path` (NE `get_full_path()`) je INHERENTNO param-free → `?page=2`
  NIKAD ne curi u href (SM-D9).

SECURITY (SM-D8): SVAKI href kroz `format_html` autoescape (`&` → `&amp;`,
head-injection-safe); `mark_safe` SAMO na join-u već-escaped delova — NIKAD
`|safe` na sirovoj URL (mirror seo_head). `request is None` → prazan string (G5).

Kodovi se ČITAJU iz `settings.LANGUAGES` (NE hardkoduj — ostaje sinhron sa 6-2
sitemap alternates; G7).
"""

from django import template
from django.conf import settings
from django.urls import translate_url
from django.utils.html import format_html
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag(takes_context=True)
def hreflang_links(context):
    """4 `<link rel="alternate" hreflang="sr|hu|en|x-default">` za request.path."""
    request = context.get("request")
    if request is None:
        return ""

    parts = []
    default_url = None  # sr (LANGUAGE_CODE) href — uhvaćen u loop-u, reuse za x-default.
    for lang_code, _name in settings.LANGUAGES:
        lang_url = request.build_absolute_uri(translate_url(request.path, lang_code))
        if lang_code == settings.LANGUAGE_CODE:
            default_url = lang_url  # x-default == sr href (SM-D2) — bez rekompute.
        parts.append(
            format_html(
                '<link rel="alternate" hreflang="{}" href="{}">', lang_code, lang_url
            )
        )

    # x-default → sr (SM-D2): isti href kao default LANGUAGE_CODE (reuse iz loop-a;
    # fallback rekompute ako sr nije u LANGUAGES — robusnost, x-default nikad ne fali).
    if default_url is None:
        default_url = request.build_absolute_uri(
            translate_url(request.path, settings.LANGUAGE_CODE)
        )
    parts.append(
        format_html(
            '<link rel="alternate" hreflang="x-default" href="{}">', default_url
        )
    )

    return mark_safe("\n".join(parts))
