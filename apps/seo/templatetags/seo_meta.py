"""Story 6.1 — {% seo_title %} / {% seo_meta_description %} / {% seo_head %} tagovi.

NO-DUPLICATE-<title> integracija (SM-D2): base.html drži JEDAN
`<title>{% block title %}` + `<meta name="description"{% block meta_description %}>`
+ `{% block extra_head %}`. seo_title/seo_meta_description vraćaju STRING (pune
base-ove blokove); seo_head emituje SAMO `<link rel="canonical">` +
`<meta property="og:image">` (NIKAD drugi <title>/<meta description> — SM-D2/SEO1-3).

Fallback (SM-D1): kad NEMA SeoMeta (ili meta polje prazno):
- meta_title = _display_title(obj) + " | " + company_name
- meta_description = perex → description → (sopstveni) slogan → _display_title →
  SiteSettings.slogan → ""  (CRIT-1: _display_title rung PRE SiteSettings.slogan —
  prazan-perex Post pada na post.title; čuva test_blog_post_detail.py:410 semantiku).

canonical (SM-D7): request.build_absolute_uri(obj.get_absolute_url()) sa graceful
skip ako objekat nema get_absolute_url ili reverse fails (NoReverseMatch).
"""

from django import template
from django.contrib.contenttypes.models import ContentType
from django.urls import NoReverseMatch
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from apps.pages.models import SiteSettings
from apps.seo.models import SeoMeta

register = template.Library()

# Per-request keš ključ (deli SE sa apps.pages.site_setting tag-om → 1 SQL po strani).
_SITESETTINGS_CACHE_KEY = "_coric_site_settings"
# Per-request keš za SeoMeta forward lookup (seo_title/seo_meta_description/seo_head
# pozivaju _resolve_seometa za ISTI obj u jednom response-u → 1 SQL po strani).
_SEOMETA_CACHE_KEY = "_coric_seometa_cache"


def _load_site_settings(context):
    """SiteSettings.load() sa per-request kešom (deli ključ sa site_setting tag-om)."""
    request = context.get("request") if context is not None else None
    if request is not None:
        cached = getattr(request, _SITESETTINGS_CACHE_KEY, None)
        if cached is None:
            cached = SiteSettings.load()
            setattr(request, _SITESETTINGS_CACHE_KEY, cached)
        return cached
    return SiteSettings.load()


def _resolve_seometa(obj, context=None):
    """Forward GFK lookup (.first() — UniqueConstraint garantuje ≤1; NE .get()).

    Per-request keš (po obj id) → seo_title/seo_meta_description/seo_head dele 1 SQL.
    """
    if obj is None or getattr(obj, "pk", None) is None:
        return None
    # get_for_model zahteva Django model (ima _meta). Ne-model objekti (mock /
    # plain) → graceful None (NE 500) — mirror canonical graceful skip (SM-D7).
    if not hasattr(obj, "_meta"):
        return None

    request = context.get("request") if context is not None else None
    # Content-stable ključ (type-name + pk) umesto id(obj) — id() je memory-address
    # baziran (GC reuse → teoretska kolizija; ARCH-1/N-1). type-name+pk ne zahteva
    # dodatni query (ContentType resolve ostaje 1, deljen kroz 3 taga).
    cache_id = (type(obj).__name__, obj.pk)
    if request is not None:
        cache = getattr(request, _SEOMETA_CACHE_KEY, None)
        if cache is None:
            cache = {}
            setattr(request, _SEOMETA_CACHE_KEY, cache)
        if cache_id in cache:
            return cache[cache_id]

    seo = (
        SeoMeta.objects.filter(
            content_type=ContentType.objects.get_for_model(obj),
            object_id=obj.pk,
        ).first()
    )
    if request is not None:
        cache[cache_id] = seo
    return seo


def _display_title(obj):
    """getattr chain: Product/Brand/... imaju .name; Post ima .title; str() fallback."""
    return getattr(obj, "name", None) or getattr(obj, "title", None) or str(obj)


def _company_name(context):
    return _load_site_settings(context).company_name


def _display_description(obj, context):
    """CRIT-1: _display_title rung MORA biti PRE SiteSettings.slogan."""
    for attr in ("perex", "description", "slogan"):
        val = getattr(obj, attr, None)
        if val:
            return val
    dt = _display_title(obj)
    if dt:
        return dt
    return _load_site_settings(context).slogan or ""


@register.simple_tag(takes_context=True)
def seo_title(context, obj):
    """STRING za {% block title %}: SeoMeta.meta_title (kompletan) ili fallback."""
    seo = _resolve_seometa(obj, context)
    if seo and (seo.meta_title or "").strip():
        return seo.meta_title  # KOMPLETAN — admin unos, bez ' | company' suffiksa
    return f"{_display_title(obj)} | {_company_name(context)}"


@register.simple_tag(takes_context=True)
def seo_meta_description(context, obj):
    """STRING za {% block meta_description %}: SeoMeta.meta_description ili fallback."""
    seo = _resolve_seometa(obj, context)
    if seo and (seo.meta_description or "").strip():
        return seo.meta_description
    return _display_description(obj, context)


@register.simple_tag(takes_context=True)
def seo_head(context, obj):
    """Emituje <link rel="canonical"> + <meta property="og:image"> (NIKAD <title>/desc)."""
    request = context.get("request")
    seo = _resolve_seometa(obj, context)
    parts = []

    # canonical (graceful skip — SM-D7)
    try:
        url = obj.get_absolute_url()
        if request is not None:
            url = request.build_absolute_uri(url)
        parts.append(format_html('<link rel="canonical" href="{}">', url))
    except (AttributeError, NoReverseMatch):
        pass

    # og:image SAMO ako postoji (C-E)
    if seo and seo.og_image:
        img = seo.og_image.url
        if request is not None:
            img = request.build_absolute_uri(img)
        parts.append(format_html('<meta property="og:image" content="{}">', img))

    return mark_safe("\n".join(parts))
