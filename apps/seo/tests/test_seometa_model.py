"""Story 6.1 — SeoMeta model + GenericForeignKey + UniqueConstraint (TEA RED phase).

Pokriva AC1 (model polja + tipovi + nasleđe TimestampedModel + __str__ + Meta) i
AC4 (UniqueConstraint(content_type, object_id) — jedan SeoMeta po objektu).

⚠️ PRVA GenericForeignKey u projektu (Gotcha SEO1-1). GFK pristup:
- `content_object` NIJE DB kolona — composite Python accessor; postavi/pročitaj
  kroz REALNI Product/Post (cross-tip rad).
- Lookup po objektu = `filter(content_type=ContentType.objects.get_for_model(obj),
  object_id=obj.pk)` (NE `filter(content_object=obj)` — GFK ne podržava direktan filter).

⚠️ GUARD: apps.seo importi UNUTAR funkcija (collection-safety) — apps.seo NE postoji
još → per-test FAIL (ModuleNotFoundError / AppRegistryNotReady / assertion), NE
collection-abort.

TEA RED phase: SVI testovi MORAJU pasti dok Dev ne kreira apps.seo + SeoMeta.

Refs:
- 6-1-...-admin.md AC1/AC4 + Task 7.2 + SM-D1/D4/D6 + Gotcha SEO1-1
- 6-1-interface-contract.md § models.py
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.django_db


# AC1: SeoMeta postoji i nasleđuje TimestampedModel (created_at/updated_at)
def test_seometa_inherits_timestamped_model():
    from apps.core.models import TimestampedModel
    from apps.seo.models import SeoMeta

    assert issubclass(SeoMeta, TimestampedModel), (
        "SeoMeta MORA nasleđivati apps.core.TimestampedModel (REUSE — AC1)."
    )
    field_names = {f.name for f in SeoMeta._meta.get_fields()}
    assert {"created_at", "updated_at"} <= field_names, (
        "SeoMeta MORA imati created_at/updated_at (TimestampedModel nasleđe)."
    )


# AC1: GFK trojka — content_type (FK ContentType) + object_id (PositiveInt) + content_object (GFK)
def test_seometa_has_generic_foreign_key_triple():
    from django.contrib.contenttypes.fields import GenericForeignKey
    from django.contrib.contenttypes.models import ContentType
    from django.db import models

    from apps.seo.models import SeoMeta

    # content_type — FK → ContentType, CASCADE
    ct_field = SeoMeta._meta.get_field("content_type")
    assert isinstance(ct_field, models.ForeignKey), "content_type MORA biti ForeignKey."
    assert ct_field.related_model is ContentType, (
        "content_type MORA pokazivati na contenttypes.ContentType (AC1)."
    )
    assert ct_field.remote_field.on_delete is models.CASCADE, (
        "content_type on_delete MORA biti CASCADE (orphaned SeoMeta cleanup — AC1)."
    )

    # object_id — PositiveIntegerField, db_index
    obj_field = SeoMeta._meta.get_field("object_id")
    assert isinstance(obj_field, models.PositiveIntegerField), (
        "object_id MORA biti PositiveIntegerField (AC1)."
    )
    assert obj_field.db_index is True, (
        "object_id MORA imati db_index=True (Django GFK docs preporuka — AC1)."
    )

    # content_object — GenericForeignKey (composite accessor, NE DB kolona)
    gfk = SeoMeta._meta.get_field("content_object")
    assert isinstance(gfk, GenericForeignKey), (
        "content_object MORA biti GenericForeignKey('content_type','object_id') — AC1."
    )


# AC1: content_object resolve-uje na realni Product (cross-tip GFK rad)
def test_content_object_resolves_to_product(product):
    from django.contrib.contenttypes.models import ContentType

    from apps.seo.models import SeoMeta

    seo = SeoMeta.objects.create(content_object=product, meta_title_sr="X")
    seo.refresh_from_db()

    assert seo.content_type == ContentType.objects.get_for_model(product), (
        "content_type MORA biti ContentType za Product kad je content_object=product."
    )
    assert seo.object_id == product.pk
    assert seo.content_object == product, (
        "content_object MORA resolve-ovati nazad na realni Product (GFK accessor)."
    )


# AC1: content_object radi i za blog Post (Post ima `title` NE `name` — drugi tip)
def test_content_object_resolves_to_post(post):
    from apps.seo.models import SeoMeta

    seo = SeoMeta.objects.create(content_object=post, meta_title_sr="Y")
    seo.refresh_from_db()
    assert seo.content_object == post, (
        "content_object MORA resolve-ovati na blog Post (cross-tip GFK — AC1)."
    )


# AC1: translatable meta_title (CharField) + meta_description (TextField)
def test_seometa_meta_fields_types():
    from django.db import models

    from apps.seo.models import SeoMeta

    mt = SeoMeta._meta.get_field("meta_title")
    assert isinstance(mt, models.CharField), "meta_title MORA biti CharField (AC1)."
    assert mt.max_length == 255, "meta_title max_length MORA biti 255 (AC1)."
    assert mt.blank is True, "meta_title MORA biti blank=True (AC1)."

    md = SeoMeta._meta.get_field("meta_description")
    assert isinstance(md, models.TextField), "meta_description MORA biti TextField (AC1)."
    assert md.blank is True, "meta_description MORA biti blank=True (AC1)."


# AC1: og_image = ImageField (NE FileField — SM-D6), nullable, upload_to="seo/og/"
def test_seometa_og_image_is_imagefield():
    from django.db import models

    from apps.seo.models import SeoMeta

    og = SeoMeta._meta.get_field("og_image")
    assert isinstance(og, models.ImageField), (
        "og_image MORA biti ImageField (SM-D6 — Pillow validira sliku, NE FileField)."
    )
    assert og.null is True and og.blank is True, "og_image MORA biti null=True, blank=True."
    assert og.upload_to == "seo/og/", "og_image upload_to MORA biti 'seo/og/' (AC1)."


# AC1: exclude_from_sitemap = BooleanField default=False (FORWARD-SUPPORT 6.2)
def test_seometa_exclude_from_sitemap_default_false():
    from django.db import models

    from apps.seo.models import SeoMeta

    field = SeoMeta._meta.get_field("exclude_from_sitemap")
    assert isinstance(field, models.BooleanField), (
        "exclude_from_sitemap MORA biti BooleanField (AC1 / SM-D8)."
    )
    assert field.default is False, "exclude_from_sitemap default MORA biti False (AC1)."


def test_exclude_from_sitemap_instance_default(product):
    from apps.seo.models import SeoMeta

    seo = SeoMeta.objects.create(content_object=product)
    assert seo.exclude_from_sitemap is False, (
        "Nova SeoMeta instanca → exclude_from_sitemap default False (AC1)."
    )


# AC1: Meta — verbose_name (pun dijakritik), ordering, constraints; __str__ ne dira content_object
def test_seometa_meta_options_and_str(product):
    from apps.seo.models import SeoMeta

    opts = SeoMeta._meta
    assert str(opts.verbose_name) == "SEO meta", "verbose_name MORA biti 'SEO meta' (AC1)."
    assert list(opts.ordering) == ["-updated_at"], (
        "ordering MORA biti ['-updated_at'] (AC1)."
    )
    constraint_names = {c.name for c in opts.constraints}
    assert "seo_seometa_ct_obj_uniq" in constraint_names, (
        "Meta.constraints MORA sadržati UniqueConstraint 'seo_seometa_ct_obj_uniq' (SM-D4)."
    )

    seo = SeoMeta.objects.create(content_object=product)
    s = str(seo)
    assert str(seo.object_id) in s, (
        "__str__ MORA sadržati object_id (npr. 'SeoMeta<...#<pk>>') — AC1."
    )


# AC4: dva SeoMeta za ISTI objekat → IntegrityError ILI ValidationError (UniqueConstraint)
def test_uniqueconstraint_rejects_second_seometa_for_same_object(product):
    from django.core.exceptions import ValidationError
    from django.db import IntegrityError, transaction

    from apps.seo.models import SeoMeta

    SeoMeta.objects.create(content_object=product, meta_title_sr="Prvi")

    with pytest.raises((IntegrityError, ValidationError)):
        with transaction.atomic():
            SeoMeta.objects.create(content_object=product, meta_title_sr="Drugi")


# AC4: razni objekti (različit object_id ili content_type) → razni SeoMeta dozvoljeni
def test_uniqueconstraint_allows_distinct_objects(product, post):
    from django.contrib.contenttypes.models import ContentType

    from apps.seo.models import SeoMeta

    SeoMeta.objects.create(content_object=product)
    SeoMeta.objects.create(content_object=post)  # drugi content_type → OK

    assert (
        SeoMeta.objects.filter(
            content_type=ContentType.objects.get_for_model(product),
            object_id=product.pk,
        ).count()
        == 1
    )
    assert (
        SeoMeta.objects.filter(
            content_type=ContentType.objects.get_for_model(post),
            object_id=post.pk,
        ).count()
        == 1
    )


# A4 / TEA MF-1 — GFK orphan-on-delete: brisanje primaoca OSTAVLJA SeoMeta orphan.
# OQ-4 (deliberate): NEMA GenericRelation → content_type CASCADE fire-uje SAMO na
# brisanje ContentType-a, NE na brisanje pojedinačnog objekta. Ovaj test LOCK-uje
# trenutnu orphan-tolerantnu semantiku — Epic 8 može dodati GenericRelation cleanup
# (tada će ovaj test biti vidljiv signal da se ponašanje namerno menja).
def test_seometa_orphan_persists_after_object_delete(product):
    from apps.seo.models import SeoMeta

    seo = SeoMeta.objects.create(content_object=product, meta_title_sr="Orphan-to-be")
    seo_pk = seo.pk

    product.delete()

    assert SeoMeta.objects.filter(pk=seo_pk).exists() is True, (
        "OQ-4 (NEMA GenericRelation): brisanje Product-a OSTAVLJA orphan SeoMeta "
        "(content_type CASCADE fire-uje SAMO na ContentType delete). Ovaj test "
        "lock-uje trenutnu orphan-toleranciju — Epic 8 može dodati cleanup."
    )


# AC4: forward lookup po (content_type, object_id) vraća tačno taj zapis
def test_forward_lookup_by_content_type_and_object_id(product):
    from django.contrib.contenttypes.models import ContentType

    from apps.seo.models import SeoMeta

    seo = SeoMeta.objects.create(content_object=product, meta_title_sr="Lookup")
    found = SeoMeta.objects.filter(
        content_type=ContentType.objects.get_for_model(product),
        object_id=product.pk,
    ).first()
    assert found == seo, (
        "Forward lookup (content_type, object_id) MORA vratiti SeoMeta zapis (AC4/AC6)."
    )
