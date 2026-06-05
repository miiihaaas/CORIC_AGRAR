# Story 6.1 — Interface Contract (TEA canonical; Dev MORA satisfy)

> RED-phase ugovor. Dev implementira TAČNO ove signature da `apps/seo/tests/` (52
> behavioral RED testova) postanu GREEN bez menjanja testova. 5 blog regression-lock
> testova MORAJU ostati GREEN. Mirror-uje apps/blog 5-1 scaffolding + apps/pages
> SiteSettings pattern.

---

## 1. `apps/seo/__init__.py`
Prazan package marker.

## 2. `apps/seo/apps.py`

```python
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class SeoConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.seo"            # KRITIČNO — sa apps. prefiksom (Gotcha PR-1)
    verbose_name = _("SEO")
```

Test lock: `test_app_config.py::test_seoconfig_name` (name == "apps.seo", default_auto_field).

## 3. INSTALLED_APPS — `config/settings/base.py`

Dodaj `"apps.seo"` na KRAJ INSTALLED_APPS — POSLE `modeltranslation` (idx > modeltranslation)
i POSLE `apps.blog` (idx > apps.blog). (SM-D9; generic inline u admin.py importuje
receiving admin-e/modele.)

Test lock: `test_app_config.py::test_seo_in_installed_apps` + `::test_seo_installed_after_modeltranslation_and_blog`.

## 4. `apps/seo/models.py` — `SeoMeta(TimestampedModel)`

```python
from django.contrib.contenttypes.fields import GenericForeignKey
from django.db import models
from django.db.models import UniqueConstraint
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimestampedModel


class SeoMeta(TimestampedModel):
    content_type = models.ForeignKey(
        "contenttypes.ContentType",
        on_delete=models.CASCADE,
        verbose_name=_("Tip sadržaja"),
    )
    object_id = models.PositiveIntegerField(db_index=True, verbose_name=_("ID objekta"))
    content_object = GenericForeignKey("content_type", "object_id")  # NIJE DB kolona

    meta_title = models.CharField(_("Meta naslov"), max_length=255, blank=True)        # translatable
    meta_description = models.TextField(_("Meta opis"), blank=True)                     # translatable
    og_image = models.ImageField(
        _("OG slika"), upload_to="seo/og/", max_length=255, null=True, blank=True,
    )
    exclude_from_sitemap = models.BooleanField(
        _("Izostavi iz sitemap-a"), default=False, db_index=True,
    )

    class Meta:
        verbose_name = _("SEO meta")
        verbose_name_plural = _("SEO meta")
        ordering = ["-updated_at"]
        constraints = [
            UniqueConstraint(
                fields=["content_type", "object_id"], name="seo_seometa_ct_obj_uniq",
            ),
        ]

    def __str__(self):
        return f"SeoMeta<{self.content_type} #{self.object_id}>"   # NE poziva content_object
```

NEMA `clean()` (YAGNI; soft warning je admin advisory). `verbose_name` mora biti TAČNO
string `"SEO meta"` (test asertuje `str(verbose_name) == "SEO meta"`).

Test locks: `test_seometa_model.py` (sva polja/tipovi, GFK trojka, CASCADE, db_index,
ImageField, exclude default False, __str__ sadrži object_id, UniqueConstraint
`(IntegrityError, ValidationError)`, distinct objects allowed, forward lookup).

## 5. `apps/seo/translation.py`

```python
from modeltranslation.translator import TranslationOptions, register

from apps.seo.models import SeoMeta


@register(SeoMeta)
class SeoMetaTranslationOptions(TranslationOptions):
    fields = ("meta_title", "meta_description")
```

`og_image`/`exclude_from_sitemap`/GFK polja NISU u fields → NE translatable.
Generiše `meta_title_sr/_hu/_en` + `meta_description_sr/_hu/_en`.

Test locks: `test_seometa_translation.py` (registrovan u translator; _sr/_hu/_en polja
postoje; non-translatable polja nemaju locale varijante; sr fallback).

## 6. `apps/seo/migrations/0001_initial.py` (makemigrations + MANUAL REVIEW)

`CreateModel("SeoMeta")` sa kolonama: `content_type` FK, `object_id` (db_index),
`meta_title` + `meta_title_sr/_hu/_en`, `meta_description` + `meta_description_sr/_hu/_en`,
`og_image`, `exclude_from_sitemap`, nasleđeni `created_at`/`updated_at`. **`content_object`
NIJE kolona.** `options["constraints"]` sadrži UniqueConstraint `seo_seometa_ct_obj_uniq`.
`dependencies` MORA imati `("contenttypes", "__first__")`. **0 promena u postojećim app
migracijama** (makemigrations --check čist; receiving modeli ne dobijaju migraciju — OQ-4).

Test locks: `test_seometa_migration.py` (modul postoji, initial=True, kolone, NEMA
content_object, UniqueConstraint, contenttypes dep, no pending migrations).

## 7. `apps/seo/admin.py` — `SeoWarningAdminMixin` + `SeoMetaInline`

```python
from django.contrib import admin, messages
from django.contrib.contenttypes.admin import GenericStackedInline  # fallback baza
from modeltranslation.admin import TranslationGenericStackedInline  # 0.20.3 ✓ verifikovano
from django.utils.translation import gettext_lazy as _

from apps.seo.models import SeoMeta

_TITLE_MAX = 60
_DESC_MAX = 160


class SeoMetaInline(TranslationGenericStackedInline):   # primarno (0.20.3 ima); fallback GenericStackedInline + eksplicitan _sr/_hu/_en fields
    model = SeoMeta
    extra = 0
    max_num = 1
    ct_field = "content_type"
    ct_fk_field = "object_id"
    # fields = (meta_title*/meta_description* per-locale + og_image + exclude_from_sitemap)


class SeoWarningAdminMixin:
    """Soft warning (NON-BLOCKING) za predugačak meta_title/meta_description."""

    def save_formset(self, request, form, formset, change):
        # C-B GUARD: obradi SAMO SeoMeta formset-e (drugi inline-ovi prolaze netaknuti)
        if getattr(formset, "model", None) is not SeoMeta:
            return super().save_formset(request, form, formset, change)
        super().save_formset(request, form, formset, change)
        for instance in getattr(formset, "instances", []):
            for lang in ("sr", "hu", "en"):
                t = getattr(instance, f"meta_title_{lang}", "") or ""
                d = getattr(instance, f"meta_description_{lang}", "") or ""
                if len(t) > _TITLE_MAX:
                    self.message_user(request, _("SEO meta naslov prelazi %(n)d znakova (preporuka).") % {"n": _TITLE_MAX}, level=messages.WARNING)
                if len(d) > _DESC_MAX:
                    self.message_user(request, _("SEO meta opis prelazi %(n)d znakova (preporuka).") % {"n": _DESC_MAX}, level=messages.WARNING)
```

NIKAD `form.add_error`/`ValidationError` (krši soft semantiku). Mehanizam asertovan
strukturno: `save_formset` postoji + izvor sadrži `"SeoMeta"` (C-B guard).

### Receiving admin EDIT-ovi (import IZ `apps.seo.admin` — jednosmerno, C-C)

- `apps/products/admin.py`: `Product` bare-register → `@admin.register(Product)` `class ProductAdmin(SeoWarningAdminMixin, admin.ModelAdmin): inlines = [SeoMetaInline]`. Ostali Product* modeli ostaju bare register. (test importuje `apps.products.admin.ProductAdmin`.)
- `apps/brands/admin.py`: SVA 4 (`Brand`/`Series`/`Category`/`Subcategory`) → `@admin.register` `class XAdmin(SeoWarningAdminMixin, admin.ModelAdmin): inlines = [SeoMetaInline]`. **Category UKLJUČEN** (C-F locked — fajl NE polu-konvertovan).
- `apps/blog/admin.py`: `PostAdmin` → `class PostAdmin(SeoWarningAdminMixin, TranslationAdmin)` (**mixin PRVI u MRO** — C-A) + `inlines = [SeoMetaInline]`. **Zadrži `view_on_site = False` + sve postojeće atribute** (C-A). Category/Tag inline DEFERRED (OQ-1).
- `apps/pages/admin.py`: SiteSettings NE dobija inline (OQ-1 — singleton config, nema get_absolute_url).

Test locks: `test_seometa_admin_inline.py` (inline na 5 admin-a + brands.Category;
max_num==1; model==SeoMeta; PostAdmin TranslationAdmin+view_on_site False; changelist/
add-view 200; system checks clean; ProductAdmin subclass SeoWarningAdminMixin;
save_formset postoji + SeoMeta guard; warning NON-BLOCKING — objekat sačuvan i sa
meta_title>60 / meta_description>160).

## 8. `apps/seo/templatetags/seo_meta.py`

```python
from django import template
from django.contrib.contenttypes.models import ContentType
from django.urls import NoReverseMatch
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from apps.pages.models import SiteSettings
from apps.seo.models import SeoMeta

register = template.Library()


def _resolve_seometa(obj):
    if obj is None or getattr(obj, "pk", None) is None:
        return None
    return SeoMeta.objects.filter(
        content_type=ContentType.objects.get_for_model(obj), object_id=obj.pk,
    ).first()   # ≤1 garantovan (UniqueConstraint) — .first() NE .get()


def _display_title(obj):
    return getattr(obj, "name", None) or getattr(obj, "title", None) or str(obj)


def _company_name():
    return SiteSettings.load().company_name


def _display_description(obj):
    # CRIT-1 RED: display_title rung MORA biti PRE SiteSettings.slogan
    for attr in ("perex", "description", "slogan"):
        val = getattr(obj, attr, None)
        if val:
            return val
    dt = _display_title(obj)
    if dt:
        return dt
    return SiteSettings.load().slogan or ""


@register.simple_tag(takes_context=True)
def seo_title(context, obj):
    seo = _resolve_seometa(obj)
    if seo and (seo.meta_title or "").strip():
        return seo.meta_title                                  # KOMPLETAN — bez ' | company'
    return f"{_display_title(obj)} | {_company_name()}"        # fallback dodaje company


@register.simple_tag(takes_context=True)
def seo_meta_description(context, obj):
    seo = _resolve_seometa(obj)
    if seo and (seo.meta_description or "").strip():
        return seo.meta_description
    return _display_description(obj)


@register.simple_tag(takes_context=True)
def seo_head(context, obj):
    request = context.get("request")
    seo = _resolve_seometa(obj)
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
```

**KRITIČNO (SM-D2):** `seo_head` NIKAD ne emituje `<title>`/`<meta name="description">`.
`seo_title`/`seo_meta_description` vraćaju STRING (pune base-ove blokove).

Test locks: `test_seo_meta_tag.py`, `test_seo_fallback.py`, `test_seo_i18n.py`,
`test_head_integration.py`.

## 9. Detail-template wiring (SM-D2 recept) — `{% load seo_meta %}` na vrhu

| Template | block title | block meta_description | block extra_head |
|---|---|---|---|
| `templates/products/product_detail.html` | `{% seo_title product %}` | `{% seo_meta_description product %}` | `{% seo_head product %}` |
| `templates/brands/brand_detail.html` | `{% seo_title brand %}` | `{% seo_meta_description brand %}` | `{% seo_head brand %}` |
| `templates/blog/post_detail.html` | `{% seo_title post %}` | `{% seo_meta_description post %}` | `{% seo_head post %}` |

`base.html` ostaje NETAKNUT (drži JEDAN `<title>{% block title %}` + JEDAN
`<meta name="description"{% block meta_description %}>` + `{% block extra_head %}`).
Rezultat: TAČNO 1 `<title>` + 1 `<meta description>` (test_head_integration).

## 10. Asertovani simboli / data (sumarno za Dev)

- Model: `apps.seo.models.SeoMeta` + polja `content_type`/`object_id`/`content_object`/
  `meta_title(+_sr/_hu/_en)`/`meta_description(+_sr/_hu/_en)`/`og_image`/`exclude_from_sitemap`;
  Meta.constraints name `seo_seometa_ct_obj_uniq`; `__str__` sadrži object_id.
- Translation: `SeoMeta` u `modeltranslation.translator`.
- Migration: `apps.seo.migrations.0001_initial` (CreateModel, dep contenttypes).
- App: `apps.seo.apps.SeoConfig` (name "apps.seo"); u INSTALLED_APPS.
- Admin: `apps.seo.admin.SeoMetaInline` (model SeoMeta, max_num 1) + `apps.seo.admin.SeoWarningAdminMixin` (save_formset w/ SeoMeta guard); `apps.products.admin.ProductAdmin` (subclass SeoWarningAdminMixin); inline na Product/Brand/Series/Subcategory/brands.Category/Post.
- Tags: `seo_title`, `seo_meta_description`, `seo_head` (svi takes_context=True) u
  `{% load seo_meta %}` biblioteci; `seo_head` emituje `rel="canonical"` (apsolutni,
  locale-prefiksovan) + `property="og:image"` (samo kad og_image).

## 11. Granice (NE implementirati u 6.1)
NEMA sitemap/robots/full-OG-card/twitter/redirect/GenericRelation/views.py/urls.py.
og_image render = SAMO `og:image` (pun OG = 6.3). `exclude_from_sitemap` polje postoji
ali se ne konzumira runtime (6.2).
