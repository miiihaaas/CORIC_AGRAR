"""Story 6.1 — `SeoMeta` model (PRVA GenericForeignKey u projektu).

GENERIC-META FOUNDATION: jedan model `SeoMeta(TimestampedModel)` koji nosi
per-objekat SEO meta (meta_title/meta_description translatable, og_image,
exclude_from_sitemap flag) vezan za bilo koji objekat kroz GenericForeignKey
(content_type FK→ContentType + object_id + content_object GFK).

UniqueConstraint(content_type, object_id) = jedan SeoMeta po objektu + služi
kao composite indeks za GFK forward lookup (SM-D4).

NEMA defensive `clean()` (YAGNI; soft warning je admin advisory — SM-D5).
`__str__` NE poziva content_object (izbegava dodatni query / None za obrisan
objekat — Gotcha SEO1-1).
"""

from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import UniqueConstraint
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimestampedModel


class SeoMeta(TimestampedModel):
    content_type = models.ForeignKey(
        "contenttypes.ContentType",
        on_delete=models.CASCADE,
        verbose_name=_("Tip sadržaja"),
    )
    object_id = models.PositiveIntegerField(
        db_index=True, verbose_name=_("ID objekta")
    )
    content_object = GenericForeignKey("content_type", "object_id")  # NIJE DB kolona

    meta_title = models.CharField(
        _("Meta naslov"), max_length=255, blank=True
    )  # translatable
    meta_description = models.TextField(_("Meta opis"), blank=True)  # translatable
    og_image = models.ImageField(
        _("OG slika"),
        upload_to="seo/og/",
        max_length=255,
        null=True,
        blank=True,
    )
    exclude_from_sitemap = models.BooleanField(
        _("Izostavi iz sitemap-a"), default=False, db_index=True
    )

    class Meta:
        verbose_name = _("SEO meta")
        verbose_name_plural = _("SEO meta")
        ordering = ["-updated_at"]
        constraints = [
            UniqueConstraint(
                fields=["content_type", "object_id"],
                name="seo_seometa_ct_obj_uniq",
            ),
        ]

    def __str__(self):
        return f"SeoMeta<{self.content_type} #{self.object_id}>"  # NE poziva content_object


class Redirect(TimestampedModel):
    """Story 6.4 — admin-upravljano 301 redirect pravilo (old_path → new_path).

    `old_path` se matchuje protiv SIROVOG `request.path` (SA locale prefiksom
    `/sr/`, `/hu/`, `/en/` — RedirectMiddleware trči PRE LocaleMiddleware; SM-D1).
    `new_path` je VALIDIRAN u `clean()` (open-redirect guard — SM-D2) i guard je
    obavezan na SVE write puteve kroz `save()` override koji zove `full_clean()`.
    NIJE translatable (ASCII URL path; translation.py netaknut — SM-D6).
    """

    old_path = models.CharField(
        _("Stari put"), max_length=255, unique=True, db_index=True
    )
    new_path = models.CharField(_("Novi put"), max_length=255)
    is_active = models.BooleanField(_("Aktivno"), default=True, db_index=True)

    class Meta:
        verbose_name = _("Preusmerenje")
        verbose_name_plural = _("Preusmerenja")
        ordering = ["old_path"]

    def __str__(self):
        return f"{self.old_path} → {self.new_path}"

    def clean(self):
        super().clean()
        # Open-redirect guard (SM-D2 — SECURITY): new_path MORA biti site-internal.
        # url_has_allowed_host_and_scheme(allowed_hosts=None) odbija scheme-relative
        # //evil.com, apsolutni http(s)://, backslash /\evil.com, javascript:/ftp:
        # i encoded bypass-eve (kanonska Django provera — pokriva slučajeve koje
        # ručni startswith check propušta).
        if not url_has_allowed_host_and_scheme(
            url=self.new_path, allowed_hosts=None
        ):
            raise ValidationError(
                {
                    "new_path": _(
                        "Novi put mora biti interni (site-internal path koji počinje "
                        "sa „/“, bez domena ili šeme)."
                    )
                }
            )
        # new_path leading-slash guard (simetričan old_path guard-u): bez vodećeg
        # „/“ browser resolve-uje new_path RELATIVNO na trenutni URL
        # (npr. „/sr/stara/“ + „sr/nova/“ → „/sr/stara/sr/nova/“) → pogrešna
        # destinacija + agresivno keširan 301. url_has_allowed_host_and_scheme
        # PRIHVATA relativni path bez „/“, pa je eksplicitan check obavezan.
        if not self.new_path.startswith("/"):
            raise ValidationError(
                {
                    "new_path": _(
                        "Novi put mora počinjati sa „/“ (apsolutni site-interni "
                        "path, npr. „/sr/nova/“ — bez vodećeg „/“ browser ga "
                        "resolve-uje relativno na trenutni URL)."
                    )
                }
            )
        # Self-loop guard: identičan old_path/new_path → beskonačni 301.
        if self.old_path == self.new_path:
            raise ValidationError(
                {
                    "new_path": _(
                        "Novi put ne sme biti identičan starom putu "
                        "(preusmerenje bi pravilo beskonačnu petlju)."
                    )
                }
            )
        # old_path leading-slash guard: middleware matchuje protiv request.path
        # koji UVEK počinje sa „/“ — bez „/“ rule je tiho mrtav (nikad ne matchuje).
        if not self.old_path.startswith("/"):
            raise ValidationError(
                {
                    "old_path": _(
                        "Stari put mora počinjati sa „/“ (mora odgovarati request.path, "
                        "npr. „/sr/stara/“)."
                    )
                }
            )

    def save(self, *args, **kwargs):
        """MANDATORY (SM-D2): primeni clean() open-redirect guard na SVE write
        puteve (.save()/.objects.create()/shell/migracije/fixtures) — Django
        save() inače NE zove full_clean().

        BYPASS GRANICE (poznato ograničenje, prihvaćeni rezidualni rizik —
        SM-D2/SEO4-2): `QuerySet.update()`, `bulk_create()` i raw SQL ZAOBILAZE
        `save()`/`full_clean()` (Django ih ne rutira po objektu), pa NE prolaze
        kroz open-redirect guard. Ovo je prihvaćeno jer su to trusted-operator
        putevi (admin/shell/migracije) i NIJEDAN untrusted input ne dospeva do
        `new_path` — redirect tabela se popunjava admin-jedan-po-jedan, ne
        bulk/update putem. Ako ikad uđe untrusted bulk import, validacija MORA
        biti dodata eksplicitno na tom putu (full_clean per-objektu).
        """
        self.full_clean()
        super().save(*args, **kwargs)
