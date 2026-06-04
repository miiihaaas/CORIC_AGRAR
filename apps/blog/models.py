"""Story 5.1 — Blog modeli (Category / Tag / Post) — MODEL FOUNDATION Epic 5.

Sva 3 modela nasleđuju `SluggedModel` + `TimestampedModel` iz apps.core
(slug globally unique + created_at/updated_at). Slug auto-gen iz `name`
(Category/Tag) / `title` (Post) kroz `slugify_ascii` (save()/full_clean()
pattern — mirror Product 2-2 CRIT-2). NEMA auto-de-dup slug kolizije (IMP-5 —
drugi save() istog title-a → ValidationError/IntegrityError; YAGNI, matches
Product presedan).

`Post.status` nested TextChoices DRAFT="draft"/PUBLISHED="published" (DB vrednosti
STABILAN cross-story ugovor — PublishedManager + 5.2/5.3/5.4 query-i ciljaju
literal "published"). `objects` (default Manager) definisan PRVI → ostaje
`_default_manager` (BL-3); `published` (PublishedManager) je opt-in javni queryset.

`get_absolute_url` → reverse("blog:detail", ...) raise-uje NoReverseMatch dok
5.2/5.3 ne registruju blog URL-ove (Gotcha PR-5 / SM-D6).

Dep boundary (SM-D1): importuje SAMO apps.core + Django + settings.AUTH_USER_MODEL.
NE FK na products/brands (samostalan content app). author FK = settings.AUTH_USER_MODEL
(NIKAD direktan User import — project-context.md:595 / SM-D3), on_delete=SET_NULL.
"""

from __future__ import annotations

from django.conf import settings
from django.core.validators import MaxLengthValidator
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from apps.core.models import SluggedModel, TimestampedModel
from apps.core.utils import slugify_ascii

from apps.blog.managers import PublishedManager


# =============================================================================
# Category (AC1)
# =============================================================================


class Category(SluggedModel, TimestampedModel):
    """Kategorija blog objave (Ratarstvo, Stočarstvo, ...).

    slug auto-gen iz `name` kroz slugify_ascii. name/description translatable (AC4).
    """

    name = models.CharField(_("Naziv"), max_length=200)
    description = models.TextField(_("Opis"), blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = _("Kategorija")
        verbose_name_plural = _("Kategorije")

    def __str__(self) -> str:
        return self.name

    def full_clean(self, *args, **kwargs):
        """Auto-gen slug iz name PRE field-level validacije (mirror Product 2-2).

        NIKAD self.clean() direktno — super().full_clean() ga već poziva.
        """
        if not self.slug and self.name:
            self.slug = slugify_ascii(self.name)
        super().full_clean(*args, **kwargs)

    def save(self, *args, **kwargs):
        if not self.slug and self.name:
            self.slug = slugify_ascii(self.name)
        self.full_clean()
        super().save(*args, **kwargs)


# =============================================================================
# Tag (AC1)
# =============================================================================


class Tag(SluggedModel, TimestampedModel):
    """Tag blog objave (Žetva, Pšenica, ...). slug auto-gen iz `name` (translatable)."""

    name = models.CharField(_("Naziv"), max_length=100)

    class Meta:
        ordering = ["name"]
        verbose_name = _("Tag")
        verbose_name_plural = _("Tagovi")

    def __str__(self) -> str:
        return self.name

    def full_clean(self, *args, **kwargs):
        if not self.slug and self.name:
            self.slug = slugify_ascii(self.name)
        super().full_clean(*args, **kwargs)

    def save(self, *args, **kwargs):
        if not self.slug and self.name:
            self.slug = slugify_ascii(self.name)
        self.full_clean()
        super().save(*args, **kwargs)


# =============================================================================
# Post (AC1) — root blog content entity
# =============================================================================


class Post(SluggedModel, TimestampedModel):
    """Blog objava („Priča sa polja").

    slug auto-gen iz `title` (globally unique — SluggedModel). title/perex/body
    translatable (AC4). body je PLAIN TextField (NE WYSIWYG model field — SM-D10;
    rich editor je Epic 8.7). category FK SET_NULL, tags M2M, author FK →
    settings.AUTH_USER_MODEL SET_NULL. status TextChoices + published_at = published
    discriminator (PublishedManager filtrira status='published' AND
    published_at__lte=now).
    """

    class Status(models.TextChoices):
        DRAFT = "draft", _("Nacrt")
        PUBLISHED = "published", _("Objavljeno")

    title = models.CharField(_("Naslov"), max_length=200)
    # SECURITY (Code Review M): MaxLengthValidator 50000 char hard cap protiv
    # abuse-a admin Editor role-a (stuffing megabajta teksta). Mirror
    # apps/products/models.py Product.description presedan (iter-1 M2) — forma
    # će postaviti tighter cap; ovo je belt-and-suspenders na model nivou ako se
    # forma bypass-uje. body je high-risk free-text (8.7 otvara WYSIWYG editor).
    perex = models.TextField(
        _("Perex"), blank=True, validators=[MaxLengthValidator(50000)]
    )
    body = models.TextField(
        _("Telo"), blank=True, validators=[MaxLengthValidator(50000)]
    )
    main_image = models.ImageField(
        _("Glavna slika"),
        upload_to="blog/main/",
        max_length=255,
        blank=True,
        null=True,
    )
    category = models.ForeignKey(
        "blog.Category",
        on_delete=models.SET_NULL,
        related_name="posts",
        null=True,
        blank=True,
        verbose_name=_("Kategorija"),
    )
    tags = models.ManyToManyField(
        "blog.Tag",
        related_name="posts",
        blank=True,
        verbose_name=_("Tagovi"),
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="blog_posts",
        null=True,
        blank=True,
        verbose_name=_("Autor"),
    )
    # NOTE I4: NEMA db_index=True — composite index `blog_post_status_pub_idx`
    # ima `status` kao leftmost field, pa B-tree leftmost-prefix scan već pokriva
    # single-column status lookup-e. Eksplicitni db_index=True bi kreirao
    # REDUNDANTAN standalone indeks (mirror apps/products/models.py NOTE I4).
    status = models.CharField(
        _("Status"),
        max_length=12,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    published_at = models.DateTimeField(_("Datum objave"), null=True, blank=True)

    objects = models.Manager()  # PRVI — ostaje _default_manager (BL-3)
    published = PublishedManager()  # DRUGI — opt-in javni queryset

    class Meta:
        ordering = ["-published_at", "-created_at"]
        verbose_name = _("Objava")
        verbose_name_plural = _("Objave")
        indexes = [
            models.Index(
                fields=["status", "-published_at"],
                name="blog_post_status_pub_idx",
            ),
        ]

    def __str__(self) -> str:
        return self.title

    def full_clean(self, *args, **kwargs):
        """Auto-gen slug iz title PRE field-level validacije (mirror Product 2-2)."""
        if not self.slug and self.title:
            self.slug = slugify_ascii(self.title)
        super().full_clean(*args, **kwargs)

    def save(self, *args, **kwargs):
        if not self.slug and self.title:
            self.slug = slugify_ascii(self.title)
        self.full_clean()
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        """URL pattern dolazi u 5.2/5.3 — raise-uje NoReverseMatch dotle (SM-D6/PR-5)."""
        return reverse("blog:detail", kwargs={"slug": self.slug})
