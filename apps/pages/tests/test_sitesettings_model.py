"""Story 3.4 — AC1: SiteSettings model surface (Task 9.1) — RED phase (TEA).

Verifikuje da `apps/pages/models.py` definiše `class SiteSettings(TimestampedModel)`
sa TAČNO propisanim poljima, stabilnim `__str__`, TimestampedModel nasleđem (created_at/
updated_at), Meta verbose_name „Podešavanja sajta", BEZ FK i BEZ get_absolute_url.

RED razlog: `apps/pages/models.py` NE postoji → `from apps.pages.models import SiteSettings`
baca ImportError → svi testovi padaju u import/setup-u (čitljiv RED razlog).

Dev NE piše testove. Pokrenuti:
    just test apps/pages/tests/test_sitesettings_model.py -v
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.django_db


def _get_model():
    """Import SiteSettings — u RED fazi baca ImportError (model ne postoji)."""
    from apps.pages.models import SiteSettings

    return SiteSettings


def test_sitesettings_has_all_declared_fields():
    """AC1: model ima TAČNO 9 deklarisanih polja (plus 2 nasleđena timestamp-a)."""
    SiteSettings = _get_model()
    field_names = {f.name for f in SiteSettings._meta.get_fields()}

    expected = {
        "company_name",
        "slogan",
        "address",
        "phone_sales",
        "phone_service",
        "email",
        "working_hours",
        "social_facebook",
        "social_instagram",
    }
    missing = expected - field_names
    assert not missing, (
        f"SiteSettings polja nedostaju: {missing}. AC1 zahteva company_name, slogan, "
        f"address, phone_sales, phone_service, email, working_hours, social_facebook, "
        f"social_instagram. Pronađena polja: {sorted(field_names)!r}"
    )


def test_sitesettings_inherits_timestamped_model():
    """AC1/SM-D9: model nasleđuje TimestampedModel → ima created_at + updated_at."""
    from apps.core.models import TimestampedModel

    SiteSettings = _get_model()
    field_names = {f.name for f in SiteSettings._meta.get_fields()}

    assert {"created_at", "updated_at"} <= field_names, (
        "SiteSettings MORA nasleđivati apps.core.models.TimestampedModel "
        f"(created_at + updated_at). Pronađena polja: {sorted(field_names)!r}"
    )
    assert issubclass(SiteSettings, TimestampedModel), (
        "SiteSettings MORA biti subclass TimestampedModel (REUSE base klasa, SM-D9 — "
        "NE PublishableModel koji ne postoji)."
    )


def test_sitesettings_field_types():
    """AC1: social_* su URLField (blank); email je EmailField; working_hours TextField."""
    from django.db import models

    SiteSettings = _get_model()

    fb = SiteSettings._meta.get_field("social_facebook")
    ig = SiteSettings._meta.get_field("social_instagram")
    assert isinstance(fb, models.URLField), "social_facebook MORA biti URLField (AC1)."
    assert isinstance(ig, models.URLField), "social_instagram MORA biti URLField (AC1)."
    assert fb.blank and ig.blank, (
        "social_facebook/social_instagram MORAJU biti blank=True (HIDE-WHEN-EMPTY, "
        "seed je prazan; SM-D8a)."
    )

    email = SiteSettings._meta.get_field("email")
    assert isinstance(email, models.EmailField), "email MORA biti EmailField (AC1)."

    wh = SiteSettings._meta.get_field("working_hours")
    assert isinstance(wh, models.TextField), (
        "working_hours MORA biti TextField (multi-line plain text; SM-D10)."
    )


def test_sitesettings_str_is_stable():
    """AC1: __str__ vraća stabilan string (NE per-instance dinamičan — singleton)."""
    SiteSettings = _get_model()
    obj = SiteSettings.load()
    assert str(obj) == "Podešavanja sajta", (
        f"SiteSettings.__str__ MORA vratiti 'Podešavanja sajta' (stabilno; puni "
        f"dijakritik; AC1), dobio {str(obj)!r}."
    )


def test_sitesettings_meta_verbose_name():
    """AC1: Meta.verbose_name = verbose_name_plural = „Podešavanja sajta" (puni dijakritik)."""
    SiteSettings = _get_model()
    assert str(SiteSettings._meta.verbose_name) == "Podešavanja sajta", (
        f"Meta.verbose_name MORA biti 'Podešavanja sajta', dobio "
        f"{SiteSettings._meta.verbose_name!r}."
    )
    assert str(SiteSettings._meta.verbose_name_plural) == "Podešavanja sajta", (
        "Meta.verbose_name_plural MORA biti 'Podešavanja sajta' (singleton — plural "
        f"isto), dobio {SiteSettings._meta.verbose_name_plural!r}."
    )


def test_sitesettings_has_no_foreign_keys():
    """AC1: model NEMA FK/relacije (config model, NE content sa relacijama)."""
    from django.db.models import ForeignKey, ManyToManyField, OneToOneField

    SiteSettings = _get_model()
    relational = [
        f.name
        for f in SiteSettings._meta.get_fields()
        if isinstance(f, (ForeignKey, ManyToManyField, OneToOneField))
    ]
    assert not relational, (
        f"SiteSettings NE SME imati FK/M2M/O2O relacije (AC1/SM-D3), pronađeno: {relational!r}."
    )


def test_sitesettings_has_no_get_absolute_url():
    """AC1/SM-D3: config model NEMA get_absolute_url (izuzetak od project-context.md:158)."""
    SiteSettings = _get_model()
    assert not hasattr(SiteSettings, "get_absolute_url"), (
        "SiteSettings NE SME imati get_absolute_url (config model, NE content sa javnom "
        "stranom — SM-D3 izuzetak od project-context.md:158)."
    )
