"""Story 6.4 — `Redirect(TimestampedModel)` model (TEA RED phase, AC1).

Pokriva AC1: polja (old_path unique+db_index / new_path / is_active default True+db_index),
nasleđe TimestampedModel (created_at/updated_at), `__str__` == "old → new",
old_path unique (IntegrityError), Meta (verbose_name/ordering), i NE-translatable
(NEMA old_path_sr atribut — SM-D6/SEO4-5).

⚠️ GUARD: apps.seo.models.Redirect import UNUTAR test body-ja (collection-safety) —
Redirect klasa JOŠ NE postoji → per-test FAIL (ImportError), NE collection-abort.

Refs:
- 6-4-redirect-manager-301.md AC1 + Task 1 + Testing § test_redirect_model.py
- 6-4-interface-contract.md § 1. Model
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.django_db


# AC1: Redirect nasleđuje TimestampedModel (created_at/updated_at)
def test_redirect_inherits_timestamped_model():
    from apps.core.models import TimestampedModel
    from apps.seo.models import Redirect

    assert issubclass(Redirect, TimestampedModel), (
        "Redirect MORA nasleđivati apps.core.TimestampedModel (REUSE — AC1)."
    )
    field_names = {f.name for f in Redirect._meta.get_fields()}
    assert {"created_at", "updated_at"} <= field_names, (
        "Redirect MORA imati created_at/updated_at (TimestampedModel nasleđe — AC1)."
    )


# AC1: old_path = CharField(max_length=255, unique=True, db_index=True)
def test_old_path_field_config():
    from django.db import models

    from apps.seo.models import Redirect

    f = Redirect._meta.get_field("old_path")
    assert isinstance(f, models.CharField), "old_path MORA biti CharField (NE URLField — SEO4-6)."
    assert f.max_length == 255, "old_path max_length MORA biti 255 (AC1)."
    assert f.unique is True, "old_path MORA biti unique=True (jedan rule po starom putu — SM-D6)."
    assert f.db_index is True, "old_path MORA imati db_index=True (perf lookup — SM-D4)."


# AC1: new_path = CharField(max_length=255)
def test_new_path_field_config():
    from django.db import models

    from apps.seo.models import Redirect

    f = Redirect._meta.get_field("new_path")
    assert isinstance(f, models.CharField), "new_path MORA biti CharField (NE URLField — SEO4-6)."
    assert f.max_length == 255, "new_path max_length MORA biti 255 (AC1)."


# AC1: is_active = BooleanField(default=True, db_index=True)
def test_is_active_field_config():
    from django.db import models

    from apps.seo.models import Redirect

    f = Redirect._meta.get_field("is_active")
    assert isinstance(f, models.BooleanField), "is_active MORA biti BooleanField (AC1)."
    assert f.default is True, "is_active default MORA biti True (AC1)."
    assert f.db_index is True, "is_active MORA imati db_index=True (is_active=True filter — SM-D4)."


# AC1: create radi; is_active default True na instanci
def test_create_defaults_is_active_true():
    from apps.seo.models import Redirect

    r = Redirect.objects.create(old_path="/sr/stari/", new_path="/sr/novi/")
    r.refresh_from_db()
    assert r.is_active is True, (
        "Nova Redirect instanca → is_active default True (AC1)."
    )
    assert r.created_at is not None, "created_at MORA biti popunjen (auto_now_add — AC1)."


# AC1: __str__ == "old_path → new_path" (literal strelica)
def test_str_returns_arrow_format():
    from apps.seo.models import Redirect

    r = Redirect.objects.create(old_path="/sr/stari/", new_path="/sr/novi/")
    assert str(r) == "/sr/stari/ → /sr/novi/", (
        "__str__ MORA vratiti '/sr/stari/ → /sr/novi/' (strelica format — AC1)."
    )


# AC1: old_path unique — drugi rule sa istim old_path → IntegrityError
def test_old_path_unique_rejects_duplicate():
    from django.db import IntegrityError, transaction

    from apps.seo.models import Redirect

    Redirect.objects.create(old_path="/sr/dup/", new_path="/sr/a/")

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            # zaobiđi save()-level full_clean da bismo testirali DB-level unique constraint;
            # bulk_create NE zove save()/full_clean (dokumentovan izuzetak — SM-D2)
            Redirect.objects.bulk_create(
                [Redirect(old_path="/sr/dup/", new_path="/sr/b/")]
            )


# AC1: Meta verbose_name (srpski dijakritika) + ordering
def test_meta_options():
    from apps.seo.models import Redirect

    opts = Redirect._meta
    assert str(opts.verbose_name) == "Preusmerenje", (
        "verbose_name MORA biti 'Preusmerenje' (srpski — AC1)."
    )
    assert str(opts.verbose_name_plural) == "Preusmerenja", (
        "verbose_name_plural MORA biti 'Preusmerenja' (srpski — AC1)."
    )
    assert list(opts.ordering) == ["old_path"], (
        "ordering MORA biti ['old_path'] (AC1)."
    )


# AC1 / SM-D6: Redirect NIJE translatable — NEMA old_path_sr / new_path_sr atribut
def test_redirect_not_translatable():
    from apps.seo.models import Redirect

    r = Redirect(old_path="/sr/x/", new_path="/sr/y/")
    for base in ("old_path", "new_path"):
        for lang in ("sr", "hu", "en"):
            assert not hasattr(r, f"{base}_{lang}"), (
                f"Redirect.{base}_{lang} NE SME postojati — Redirect NIJE translatable "
                "(ASCII URL path; translation.py netaknut — SM-D6/SEO4-5)."
            )
