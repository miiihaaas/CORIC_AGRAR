"""Story 7.1 — `CookiePolicy` SINGLETON model u apps.gdpr.

PRVI model Epic 7 (GDPR & Privacy). Jedan pravni dokument (politika kolačića) —
admin ga uređuje kroz UI bez code change-a, per locale.

Self-rolled singleton (SM-D2 — 1:1 mirror SiteSettings 3-4, NE django-solo dep):
- `save()` UVEK forsira `pk=1` → ne mogu postojati 2 reda. Rešava `created_at`
  auto_now_add gotcha na UPDATE-u (G-4 — KOPIRANO iz SiteSettings.save()).
- `load()` classmethod → `get_or_create(pk=1)` (lazy; bezbedan u view-u pre seed-a).
- `delete()` (instance) RAISE-uje `PermissionDenied` (NE silent no-op).

GRANICA (NIJE bug — mirror SiteSettings): instance `delete()` NE pokriva
`QuerySet.delete()`/`loaddata`/`bulk_create` (zaobilaze instance metode). Singleton
garancija počiva na save() pk=1 + instance delete() raise + admin guard (AC6).

`title`/`body` su translatable (apps/gdpr/translation.py → `_sr/_hu/_en` kolone).
`body` je TextField sa rich-HTML → render `{{ policy.body|legal_html }}` (7.5: nh3
allowlist sanitizacija NA RENDER-u = PRIMARNA XSS granica; mark_safe SAMO posle
sanitizacije; NIKAD sirov `|safe` — stored-XSS granica, SM-D3/G-6). `effective_date`
je editable pravni „važi od" datum, SEMANTIČKI ODVOJEN od auto `updated_at` (SM-D4).
"""

from django.core.exceptions import PermissionDenied
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimestampedModel


class CookiePolicy(TimestampedModel):
    """Singleton model za pravni dokument „Politika kolačića"."""

    title = models.CharField(
        _("Naslov"),
        max_length=255,
        blank=True,
    )
    body = models.TextField(
        _("Sadržaj"),
        blank=True,
    )
    effective_date = models.DateField(
        _("Važi od"),
        null=True,
        blank=True,
        help_text=_(
            "Pravni datum stupanja na snagu. Ažurirajte ga kad menjate sadržaj "
            "politike — ne ažurira se automatski."
        ),
    )

    class Meta:
        verbose_name = _("Politika kolačića")
        verbose_name_plural = _("Politika kolačića")

    def __str__(self):
        return "Politika kolačića"

    def save(self, *args, **kwargs):
        """Singleton: uvek forsiraj pk=1 (drugi save() update-uje isti red).

        Sveža instanca sa forsiranim pk=1 ide u UPDATE put (pk je set), ali
        `created_at` (auto_now_add) se popunjava SAMO na INSERT — pa na UPDATE-u
        ostaje None i ruši NOT NULL. Reši preuzimanjem postojećeg created_at, ili
        force_insert kad red ne postoji. (KOPIRANO iz SiteSettings.save() — G-4.)
        """
        self.pk = 1
        existing_created = (
            type(self).objects.filter(pk=1).values_list("created_at", flat=True).first()
        )
        if existing_created is not None:
            # pk=1 red POSTOJI → mora biti UPDATE. Caller-prosleđen force_insert bi na
            # postojećem pk-u bacio IntegrityError, pa ga uklanjamo (+force_update, koji
            # bi se sukobio sa force_insert). update_fields ostaje validan za UPDATE.
            kwargs.pop("force_insert", None)
            kwargs.pop("force_update", None)
            if self.created_at is None:
                # auto_now_add puni created_at SAMO na INSERT — na UPDATE-u bi ostao None
                # i srušio NOT NULL; preuzimamo postojeću vrednost.
                self.created_at = existing_created
        else:
            # Nema reda — INSERT (created_at se popuni kroz auto_now_add). force_insert ne
            # sme da ide sa update_fields (TypeError), pa ga sklanjamo.
            kwargs["force_insert"] = True
            kwargs.pop("force_update", None)
            kwargs.pop("update_fields", None)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Singleton se ne briše — RAISE (NE silent no-op; SM-D2)."""
        raise PermissionDenied(_("CookiePolicy singleton ne sme da se briše."))

    @classmethod
    def load(cls):
        """Vrati jedinu instancu (lazy get_or_create pk=1)."""
        obj, _created = cls.objects.get_or_create(pk=1)
        return obj

    def get_absolute_url(self):
        """Javna strana — za 7.2 baner + 7.4 footer + 6.1 SeoMeta GFK link (SM-D7)."""
        return reverse("gdpr:cookie_policy")
