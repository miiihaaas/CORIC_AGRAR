"""Story 3.4 — PRVI model u apps.pages: `SiteSettings` singleton config model.

Centralizuje globalna podešavanja sajta (kontakt-info: adresa, telefon prodaje,
telefon servisa, e-pošta, radno vreme; social: Facebook + Instagram URL) koji su
ranije bili hardkodovani na više template lokacija (_contact_info.html / footer /
top-header). Sva 3 templata sada čitaju kroz `{% site_setting "..." %}` tag.

Self-rolled singleton (SM-D2 — NE django-solo dep):
- `save()` UVEK forsira `pk=1` → ne mogu postojati 2 reda.
- `load()` classmethod → `get_or_create(pk=1)` (lazy; bezbedan za template tag pre seed-a).
- `delete()` (instance) RAISE-uje `PermissionDenied` (NE silent no-op — footgun).

GRANICA: instance `delete()` NE pokriva `QuerySet.delete()`/`loaddata`/`bulk_create`
(ti putevi zaobilaze instance metode i save() override). Singleton garancija počiva na
save() pk=1 + instance delete() raise + admin has_delete_permission=False (UI guard).

modeltranslation registracija (apps/pages/translation.py) čini `slogan`/`address`/
`working_hours` translatable (`_sr/_hu/_en` kolone).
"""

from django.core.exceptions import PermissionDenied
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimestampedModel


class SiteSettings(TimestampedModel):
    """Singleton config model za globalna podešavanja sajta (kontakt + social)."""

    company_name = models.CharField(
        _("Naziv firme"),
        max_length=200,
        default="Ćorić Agrar",
    )
    slogan = models.CharField(
        _("Slogan"),
        max_length=255,
        blank=True,
    )
    address = models.CharField(
        _("Adresa"),
        max_length=255,
        blank=True,
    )
    phone_sales = models.CharField(
        _("Telefon prodaje"),
        max_length=50,
        blank=True,
    )
    phone_service = models.CharField(
        _("Telefon servisa"),
        max_length=50,
        blank=True,
        help_text=_(
            "PLACEHOLDER — privremena vrednost dok biznis ne unese realni broj servisa."
        ),
    )
    email = models.EmailField(
        _("E-pošta"),
        blank=True,
    )
    working_hours = models.TextField(
        _("Radno vreme"),
        blank=True,
        help_text=_("Jedan red po liniji (npr. „Ponedeljak–Petak: 08–16h“)."),
    )
    social_facebook = models.URLField(
        _("Facebook URL"),
        blank=True,
        help_text=_(
            "PLACEHOLDER — prazno dok biznis ne unese realni Facebook URL; "
            "link se sakriva kad je prazno."
        ),
    )
    social_instagram = models.URLField(
        _("Instagram URL"),
        blank=True,
        help_text=_(
            "PLACEHOLDER — prazno dok biznis ne unese realni Instagram URL; "
            "link se sakriva kad je prazno."
        ),
    )

    class Meta:
        verbose_name = _("Podešavanja sajta")
        verbose_name_plural = _("Podešavanja sajta")

    def __str__(self):
        return "Podešavanja sajta"

    def save(self, *args, **kwargs):
        """Singleton: uvek forsiraj pk=1 (drugi save() update-uje isti red).

        Sveža instanca sa forsiranim pk=1 ide u UPDATE put (pk je set), ali
        `created_at` (auto_now_add) se popunjava SAMO na INSERT — pa na UPDATE-u
        ostaje None i ruši NOT NULL. Reši preuzimanjem postojećeg created_at, ili
        force_insert kad red ne postoji.
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
        raise PermissionDenied(_("SiteSettings singleton ne sme da se briše."))

    @classmethod
    def load(cls):
        """Vrati jedinu instancu (lazy get_or_create pk=1)."""
        obj, _created = cls.objects.get_or_create(pk=1)
        return obj


class Page(TimestampedModel):
    """Story 7.4 — generički model za statičke pravne/info strane.

    NIJE singleton (RAZLIKA od SiteSettings/CookiePolicy) — više Page redova
    (politika privatnosti sad; „O nama"/„Servis" CMS-ifikacija u Epic 8.8).
    `slug` ASCII jezik-neutralan unique business key; `title`/`body` translatable
    (`_sr/_hu/_en`). `body` je plain TextField — render `{{ page.body|linebreaks }}`
    (autoescape XSS-safe; NIKAD `|safe`/`mark_safe`; rich-HTML + sanitizacija = 8.7).
    """

    slug = models.SlugField(
        _("Slug"),
        max_length=255,
        unique=True,
        db_index=True,
    )
    title = models.CharField(
        _("Naslov"),
        max_length=255,
    )
    body = models.TextField(
        _("Sadržaj"),
        blank=True,
    )

    class Meta:
        verbose_name = _("Statička strana")
        verbose_name_plural = _("Statičke strane")
        ordering = ("title",)

    def __str__(self):
        return self.title or self.slug

    def get_absolute_url(self):
        return reverse("pages:page_detail", kwargs={"slug": self.slug})
