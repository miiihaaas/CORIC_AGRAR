"""Story 6.1 — SeoMetaInline (generic translation inline) + SeoWarningAdminMixin.

SeoMetaInline = generic + modeltranslation inline (SM-D3/Gotcha SEO1-2):
`TranslationGenericStackedInline` (modeltranslation >=0.20.3) kombinuje
GenericStackedInline (handluje content_type+object_id) + per-locale meta polja.
max_num=1 (jedan SeoMeta po objektu — UniqueConstraint AC4), extra=0.

SeoWarningAdminMixin = NON-BLOCKING soft warning (SM-D5/SEO1-7) za predugačak
meta_title (>60) / meta_description (>160). Mehanizam: override save_formset na
roditeljskom ModelAdmin-u (inline nema message_user pristup). C-B GUARD: obradi
SAMO SeoMeta formset-e (drugi inline-ovi prolaze netaknuti). NIKAD add_error/
ValidationError (krši soft semantiku — objekat MORA save-ovati).

⚠️ IMPORT DIREKCIJA (C-C): ovaj modul DEFINIŠE SeoMetaInline + SeoWarningAdminMixin
i NE importuje products/brands/blog admin-e ni njihove modele (GFK inline NE
zahteva model import). Receiving admini importuju IZ apps.seo.admin (jednosmerno).
"""

from django.contrib import admin, messages
from modeltranslation.admin import TranslationGenericStackedInline

from apps.seo.models import Redirect, SeoMeta

_TITLE_MAX = 60
_DESC_MAX = 160


class SeoMetaInline(TranslationGenericStackedInline):
    """Generic + modeltranslation inline za SeoMeta (žičan na receiving admin-e)."""

    model = SeoMeta
    extra = 0
    max_num = 1
    ct_field = "content_type"
    ct_fk_field = "object_id"
    fields = ("meta_title", "meta_description", "og_image", "exclude_from_sitemap")


class SeoWarningAdminMixin:
    """Soft warning (NON-BLOCKING) za predugačak meta_title / meta_description."""

    def save_formset(self, request, form, formset, change):
        # C-B GUARD: obradi SAMO SeoMeta formset-e (drugi inline-ovi prolaze netaknuti)
        if getattr(formset, "model", None) is not SeoMeta:
            return super().save_formset(request, form, formset, change)
        super().save_formset(request, form, formset, change)
        # super().save_formset() poziva formset.save() → populiše new_objects /
        # changed_objects. `formset.instances` NIJE Django atribut (uvek [] →
        # dead loop). Iteriraj STVARNO sačuvane instance (Dev A F-1 fix).
        saved = list(getattr(formset, "new_objects", [])) + [
            obj for obj, _changed in getattr(formset, "changed_objects", [])
        ]
        for instance in saved:
            for lang in ("sr", "hu", "en"):
                title = getattr(instance, f"meta_title_{lang}", "") or ""
                desc = getattr(instance, f"meta_description_{lang}", "") or ""
                if len(title) > _TITLE_MAX:
                    self.message_user(
                        request,
                        _warning_msg_title(),
                        level=messages.WARNING,
                    )
                if len(desc) > _DESC_MAX:
                    self.message_user(
                        request,
                        _warning_msg_desc(),
                        level=messages.WARNING,
                    )


@admin.register(Redirect)
class RedirectAdmin(admin.ModelAdmin):
    """Story 6.4 — samostalan admin za 301 redirect pravila (AC3).

    list_editable na is_active → toggle deaktivacije direktno iz liste; old_path
    ostaje clickable link (changelist zahteva bar jedan link). Admin ModelForm
    poziva full_clean() → clean() open-redirect guard se aktivira na add/edit.
    """

    list_display = ("old_path", "new_path", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("old_path", "new_path")
    list_editable = ("is_active",)


def _warning_msg_title():
    from django.utils.translation import gettext as _

    return _("SEO meta naslov prelazi preporučenih %(n)d znakova.") % {"n": _TITLE_MAX}


def _warning_msg_desc():
    from django.utils.translation import gettext as _

    return _("SEO meta opis prelazi preporučenih %(n)d znakova.") % {"n": _DESC_MAX}
