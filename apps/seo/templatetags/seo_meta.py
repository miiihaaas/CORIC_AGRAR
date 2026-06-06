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
from django.templatetags.static import static
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


def _canonical_url(obj, request):
    """Canonical/og:url shared helper (ARCH-3/SM-D7).

    obj=None → request.path apsolutni (site-level); inače
    build_absolute_uri(get_absolute_url()) sa graceful skip
    (AttributeError/NoReverseMatch → None). request=None → None (NE 500).
    """
    if obj is None:
        return request.build_absolute_uri(request.path) if request is not None else None
    try:
        url = obj.get_absolute_url()
    except (AttributeError, NoReverseMatch):
        return None
    return request.build_absolute_uri(url) if request is not None else url


def _og_type(obj):
    """Duck-type (SM-D5): published_at truthy → article (Post); inače website."""
    return "article" if getattr(obj, "published_at", None) else "website"


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
def seo_head(context, obj=None):
    """GLOBALNI social-meta surface (SM-D1/D2/D3): canonical + pun OG + Twitter Card.

    obj-optional (obj=None → site-level fallback; NE 500 na home/listing/404).
    SVE vrednosti kroz format_html (autoescape — SM-D8; NIKAD |safe na sirovim
    admin/object vrednostima). canonical + og:url DELE _canonical_url (C7 — oba
    se emituju zajedno ili oba skip). og:image UVEK prisutan (og-default fallback).
    """
    request = context.get("request") if context is not None else None
    seo = _resolve_seometa(obj, context)

    # title/description/image — IZRAČUNAJ JEDNOM (reuse za og + twitter; SEO3-11).
    if obj is None:
        title = _company_name(context)
        description = _load_site_settings(context).slogan or ""
    else:
        title = (
            seo.meta_title
            if (seo and (seo.meta_title or "").strip())
            else f"{_display_title(obj)} | {_company_name(context)}"
        )
        description = (
            seo.meta_description
            if (seo and (seo.meta_description or "").strip())
            else _display_description(obj, context)
        )

    # og:image — UVEK prisutan (SM-D3): object og_image ili og-default fallback.
    if seo and seo.og_image:
        image = seo.og_image.url
    else:
        image = static("img/og-default.jpg")
    if request is not None:
        image = request.build_absolute_uri(image)

    og_type = _og_type(obj)
    company = _company_name(context)
    canonical = _canonical_url(obj, request)

    parts = []
    # canonical + og:url su VEZANI (C7) — oba samo kad canonical razrešiv (NE 500).
    if canonical is not None:
        parts.append(format_html('<link rel="canonical" href="{}">', canonical))
    parts.append(format_html('<meta property="og:title" content="{}">', title))
    parts.append(format_html('<meta property="og:description" content="{}">', description))
    parts.append(format_html('<meta property="og:image" content="{}">', image))
    parts.append(format_html('<meta property="og:type" content="{}">', og_type))
    if canonical is not None:
        parts.append(format_html('<meta property="og:url" content="{}">', canonical))
    parts.append(format_html('<meta property="og:site_name" content="{}">', company))
    parts.append('<meta name="twitter:card" content="summary_large_image">')
    parts.append(format_html('<meta name="twitter:title" content="{}">', title))
    parts.append(
        format_html('<meta name="twitter:description" content="{}">', description)
    )
    parts.append(format_html('<meta name="twitter:image" content="{}">', image))

    return mark_safe("\n".join(parts))
