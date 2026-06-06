"""Story 7.1 — AC1/AC2: CookiePolicy model fields + SINGLETON invarijanta (TEA RED).

Pokriva:
- AC1: TAČNA polja (title CharField, body TextField, effective_date DateField
  null/blank) + nasleđeni created_at/updated_at (TimestampedModel) + __str__ +
  get_absolute_url → reverse("gdpr:cookie_policy").
- AC2: SINGLETON (mirror SiteSettings 3-4) — save() forsira pk=1; dva save() → count==1;
  load() get_or_create(pk=1) (lazy, siguran pre seed-a); instance delete() RAISE
  PermissionDenied (red OSTAJE); created_at preservovan kroz UPDATE (auto_now_add
  gotcha — G-4); QuerySet.delete() bypass granica (dokumentovana, NIJE bug).

⚠️ COLLECTION-SAFETY: apps.gdpr importi UNUTAR funkcija — apps.gdpr NE postoji još →
per-test ImportError (RED), NE collection-abort.

RED razlog: `apps.gdpr.models.CookiePolicy` ne postoji → ImportError.

Refs:
- 7-1-...-admin.md AC1/AC2 + SM-D2/D4/D7 + Gotcha G-4
- apps/pages/models.py:92-130 (SiteSettings save()/load()/delete() — KOPIRAJ)
- apps/pages/tests/test_sitesettings_singleton.py (mirror)
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.django_db


def _get_model():
    from apps.gdpr.models import CookiePolicy

    return CookiePolicy


def _reset():
    """QuerySet-nivo delete (zaobilazi instance delete() raise — dozvoljeno za reset)."""
    _get_model().objects.all().delete()


# ─────────────────────────────────────────────────────────────────────────────
# AC1 — fields / types / inheritance
# ─────────────────────────────────────────────────────────────────────────────


# AC1: CookiePolicy nasleđuje TimestampedModel (created_at/updated_at prisutni)
def test_inherits_timestamped_model():
    from apps.core.models import TimestampedModel

    CookiePolicy = _get_model()
    assert issubclass(CookiePolicy, TimestampedModel), (
        "CookiePolicy MORA naslediti apps.core.TimestampedModel (REUSE — AC1)."
    )


# AC1: TAČNA polja postoje sa očekivanim tipovima
def test_model_has_expected_fields_and_types():
    from django.db import models

    CookiePolicy = _get_model()
    fields = {f.name: f for f in CookiePolicy._meta.get_fields()}

    assert "title" in fields and isinstance(fields["title"], models.CharField), (
        "title MORA biti CharField (translatable — AC1/AC4)."
    )
    assert fields["title"].max_length == 255, (
        f"title.max_length MORA biti 255, dobio {fields['title'].max_length!r} (AC1)."
    )
    assert "body" in fields and isinstance(fields["body"], models.TextField), (
        "body MORA biti TextField (translatable, plain-text |linebreaks — AC1/SM-D3)."
    )
    assert "effective_date" in fields and isinstance(
        fields["effective_date"], models.DateField
    ), "effective_date MORA biti DateField (pravni 'važi od' — SM-D4/AC1)."
    assert {"created_at", "updated_at"} <= set(fields), (
        "created_at/updated_at MORAJU biti nasleđeni iz TimestampedModel (AC1)."
    )


# AC1/SM-D4: effective_date je null=True + blank=True (seed/admin sme ostaviti prazno)
def test_effective_date_nullable_and_blank():
    CookiePolicy = _get_model()
    field = CookiePolicy._meta.get_field("effective_date")
    assert field.null is True, (
        "effective_date.null MORA biti True (seed ga ostavlja None — G-11/SM-D4)."
    )
    assert field.blank is True, (
        "effective_date.blank MORA biti True (admin sme ostaviti prazno — SM-D4)."
    )


# AC1/G-10: effective_date ima help_text (staleness mitigacija — podseti admina)
def test_effective_date_has_help_text():
    CookiePolicy = _get_model()
    field = CookiePolicy._meta.get_field("effective_date")
    assert str(field.help_text).strip() != "", (
        "effective_date MORA imati help_text (staleness mitigacija — G-10/AC1)."
    )


# AC1: __str__ → "Politika kolačića" (puni dijakritik)
def test_str_representation():
    CookiePolicy = _get_model()
    obj = CookiePolicy()
    assert str(obj) == "Politika kolačića", (
        f"__str__ MORA biti 'Politika kolačića' (puni dijakritik — AC1), dobio {str(obj)!r}."
    )


# AC1/SM-D7: get_absolute_url → reverse("gdpr:cookie_policy")
def test_get_absolute_url_resolves_named_route():
    from django.urls import reverse

    CookiePolicy = _get_model()
    obj = CookiePolicy.load()
    assert obj.get_absolute_url() == reverse("gdpr:cookie_policy"), (
        "get_absolute_url() MORA biti reverse('gdpr:cookie_policy') (SM-D7 — za 7.2 "
        "baner + 7.4 footer + SeoMeta GFK link; AC1)."
    )


# ─────────────────────────────────────────────────────────────────────────────
# AC2 — SINGLETON invarijanta (mirror SiteSettings)
# ─────────────────────────────────────────────────────────────────────────────


# AC2: save() UVEK forsira pk=1 (čak i sveža instanca)
def test_save_forces_pk_1():
    CookiePolicy = _get_model()
    obj = CookiePolicy(title="Test naslov")
    obj.save()
    assert obj.pk == 1, (
        f"save() MORA forsirati pk=1 (singleton; SM-D2), dobio pk={obj.pk!r}."
    )


# AC2: dva uzastopna CookiePolicy(...).save() → count()==1 (NE kreira pk=2)
def test_two_saves_yield_single_row():
    CookiePolicy = _get_model()
    _reset()

    first = CookiePolicy(title="Prvi")
    first.save()
    second = CookiePolicy(title="Drugi")
    second.save()

    assert CookiePolicy.objects.count() == 1, (
        "Posle 2 instance save() MORA postojati TAČNO 1 red (drugi UPDATE-uje pk=1, NE "
        f"kreira pk=2; SM-D2), dobio count()={CookiePolicy.objects.count()}."
    )
    assert second.pk == 1, f"Drugi save() MORA biti pk=1, dobio {second.pk!r}."


# AC2/G-4: created_at preservovan kroz UPDATE (auto_now_add gotcha — KOPIRAJ SiteSettings)
def test_created_at_preserved_across_update():
    CookiePolicy = _get_model()
    _reset()

    obj = CookiePolicy(title="Naslov", body="Telo v1")
    obj.save()
    inserted = CookiePolicy.objects.get(pk=1)
    original_created = inserted.created_at
    original_updated = inserted.updated_at
    assert original_created is not None, (
        "created_at MORA biti popunjen na INSERT (auto_now_add). Ako je None — save() "
        "ne rešava force_insert ispravno (G-4)."
    )
    assert original_updated is not None, (
        "updated_at MORA biti popunjen na INSERT (auto_now). Ako je None — save() "
        "ne rešava timestamp put ispravno (G-4)."
    )

    # UPDATE: drugi save() (pk=1) — created_at NE SME postati None / promeniti se,
    # ali updated_at (auto_now) MORA biti bumpovan.
    obj2 = CookiePolicy(title="Naslov", body="Telo v2")
    obj2.save()
    refetched = CookiePolicy.objects.get(pk=1)
    assert refetched.created_at == original_created, (
        "created_at MORA OSTATI nepromenjen kroz UPDATE (auto_now_add se NE puni na "
        "UPDATE → save() mora preuzeti postojeći; G-4). KOPIRAJ SiteSettings.save()."
    )
    assert refetched.body == "Telo v2", "UPDATE MORA promeniti body."
    # G-4 invarijanta potpuno zaključana: slomljen save() koji zamrzne updated_at
    # (npr. preuzme stari kao created_at) bi sada pao.
    assert refetched.updated_at >= original_updated, (
        "updated_at MORA biti >= originalni posle UPDATE-a (auto_now bump; G-4). "
        f"original={original_updated!r}, posle={refetched.updated_at!r}."
    )
    assert refetched.updated_at != original_created, (
        "updated_at NE SME biti zamenjen sa created_at vrednošću kroz UPDATE — "
        "auto_now MORA bumpovati updated_at nezavisno od created_at preserve logike (G-4)."
    )


# AC2: load() get_or_create vraća instancu i kad red ne postoji (NE DoesNotExist)
def test_load_returns_instance_on_empty_db():
    CookiePolicy = _get_model()
    _reset()

    obj = CookiePolicy.load()
    assert obj is not None and obj.pk == 1, (
        f"load() na praznoj bazi MORA get_or_create-ovati instancu pk=1 (lazy, siguran "
        f"PRE seed-a; SM-D2/AC2), dobio {obj!r}."
    )
    assert CookiePolicy.objects.count() == 1, "load() MORA materijalizovati TAČNO 1 red."


# AC2: load() pre seed-a → pk==1, title_sr == "" (prazna placeholder instanca, siguran)
def test_load_before_seed_is_safe_empty():
    CookiePolicy = _get_model()
    _reset()

    obj = CookiePolicy.load()
    assert obj.pk == 1, "load() PRE seed-a MORA dati pk=1."
    assert (obj.title_sr or "") == "", (
        "load() na praznom modelu MORA dati prazan title_sr (blank=True default; AC2)."
    )


# AC2: višestruki load() idempotentan (uvek pk=1, NE dodatni redovi)
def test_load_is_idempotent():
    CookiePolicy = _get_model()
    a = CookiePolicy.load()
    b = CookiePolicy.load()
    assert a.pk == b.pk == 1, "load() MORA uvek vratiti pk=1."
    assert CookiePolicy.objects.count() == 1, (
        "Višestruki load() NE SME kreirati dodatne redove (count()==1; SM-D2)."
    )


# AC2: instance delete() RAISE PermissionDenied (NE silent no-op); red OSTAJE
def test_delete_raises_and_row_stays():
    from django.core.exceptions import PermissionDenied

    CookiePolicy = _get_model()
    obj = CookiePolicy.load()
    count_before = CookiePolicy.objects.count()

    with pytest.raises(PermissionDenied):
        obj.delete()

    assert CookiePolicy.objects.count() == count_before, (
        "Posle pokušaja delete() red MORA OSTATI (delete blokiran; SM-D2/AC2), "
        f"count pre={count_before}, posle={CookiePolicy.objects.count()}."
    )
    assert CookiePolicy.objects.filter(pk=1).exists(), (
        "pk=1 red MORA i dalje postojati posle blokiranog delete()."
    )


# AC2 CAVEAT (dokumentovana granica, NIJE bug): QuerySet.delete() ZAOBILAZI instance guard
def test_queryset_delete_bypasses_instance_guard_boundary_doc():
    CookiePolicy = _get_model()
    CookiePolicy.load()  # garantuj da red postoji
    assert CookiePolicy.objects.filter(pk=1).exists()

    # QuerySet-nivo delete NE prolazi kroz instance delete() override → red NESTAJE.
    CookiePolicy.objects.all().delete()
    assert CookiePolicy.objects.filter(pk=1).exists() is False, (
        "QuerySet.delete() MORA zaobići instance guard i ukloniti red (dokumentovana "
        "granica singleton invarijante; AC2 caveat — mirror SiteSettings)."
    )


# AC1: NEMA clean() defensive validacije (project-context.md:358 — no premature defense)
def test_no_defensive_clean_method():
    from django.db.models import Model

    CookiePolicy = _get_model()
    assert CookiePolicy.clean is Model.clean, (
        "CookiePolicy NE SME definisati custom clean() (NEMA defensive validacije za "
        "nemoguće slučajeve — project-context.md:358 / AC1)."
    )
