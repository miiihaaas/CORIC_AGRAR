"""Story 3.4 — AC2: SiteSettings singleton invarijanta (Task 9.2) — RED phase (TEA).

Verifikuje self-rolled singleton pattern (SM-D2, NE django-solo):
- save() forsira pk=1 → dva uzastopna save() = count()==1 (NE 2 reda)
- load() classmethod (get_or_create pk=1) → vraća instancu i na (praktično) praznoj bazi
- delete() instance RAISE-uje (NE silent no-op) → red OSTAJE posle pokušaja delete

NAPOMENA (TEA-D2): pytest-django primenjuje 0002 seed → seeded pk=1 red postoji po default-u.
Testovi rade nad tom (ili sveže load()-ovanom) instancom; ne oslanjaju se na praznu bazu.

RED razlog: `apps.pages.models.SiteSettings` ne postoji → ImportError.

Dev NE piše testove. Pokrenuti:
    just test apps/pages/tests/test_sitesettings_singleton.py -v
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.django_db


def _get_model():
    from apps.pages.models import SiteSettings

    return SiteSettings


def test_save_forces_pk_1():
    """AC2: save() UVEK postavi pk=1 (čak i sveža instanca ide na pk=1)."""
    SiteSettings = _get_model()
    obj = SiteSettings()
    obj.company_name = "Test Co"
    obj.save()
    assert obj.pk == 1, (
        f"save() MORA forsirati pk=1 (singleton; SM-D2), dobio pk={obj.pk!r}."
    )


def test_two_saves_yield_single_row():
    """AC2: dva uzastopna SiteSettings(...).save() → count()==1 (NE kreira pk=2)."""
    SiteSettings = _get_model()
    # Obriši kroz QuerySet (zaobilazi instance delete() raise — dozvoljeno za reset)
    SiteSettings.objects.all().delete()

    first = SiteSettings(company_name="Prvi")
    first.save()
    second = SiteSettings(company_name="Drugi")
    second.save()

    assert SiteSettings.objects.count() == 1, (
        "Posle 2 instance save() MORA postojati TAČNO 1 red (drugi update-uje pk=1, NE "
        f"kreira pk=2; SM-D2), dobio count()={SiteSettings.objects.count()}."
    )
    assert second.pk == 1, f"Drugi save() MORA biti pk=1, dobio {second.pk!r}."


def test_load_returns_instance_on_empty_db():
    """AC2: load() get_or_create vraća instancu i kad red ne postoji (NE DoesNotExist)."""
    SiteSettings = _get_model()
    SiteSettings.objects.all().delete()  # isprazni (QuerySet path zaobilazi raise)

    obj = SiteSettings.load()
    assert obj is not None and obj.pk == 1, (
        "load() na praznoj bazi MORA get_or_create-ovati instancu pk=1 (NE bacati "
        f"DoesNotExist; SM-D2/AC2), dobio {obj!r}."
    )
    assert SiteSettings.objects.count() == 1, (
        "load() MORA materijalizovati TAČNO 1 red."
    )


def test_delete_raises_and_row_stays():
    """AC2: instance delete() RAISE-uje PermissionDenied (NE silent no-op); red OSTAJE."""
    from django.core.exceptions import PermissionDenied

    SiteSettings = _get_model()
    obj = SiteSettings.load()
    count_before = SiteSettings.objects.count()

    # Implementacija baca PermissionDenied (SM-D2) — uzak izuzetak (NE silent no-op, NE
    # slučajan programmer error kao AttributeError od typo-a).
    with pytest.raises(PermissionDenied):
        obj.delete()

    assert SiteSettings.objects.count() == count_before, (
        "Posle pokušaja delete() red MORA OSTATI (delete je blokiran; SM-D2/AC2), "
        f"count pre={count_before}, posle={SiteSettings.objects.count()}."
    )
    assert SiteSettings.objects.filter(pk=1).exists(), (
        "pk=1 red MORA i dalje postojati posle blokiranog delete()."
    )


def test_queryset_delete_bypasses_instance_guard_boundary_doc():
    """AC2 CAVEAT (invariant boundary, NE kontradikcija): `SiteSettings.objects.all().delete()`
    (QuerySet-nivo) ZAOBILAZI instance delete() guard i UKLANJA red.

    Ovo dokumentuje poznatu granicu (mirror AC2 caveat-a za Epic 9 9-7 fixtures): instance
    .delete() raise NE pokriva QuerySet.delete()/loaddata/bulk_create. NIJE u suprotnosti sa
    `test_delete_raises_and_row_stays` (taj testira INSTANCE put).
    """
    SiteSettings = _get_model()
    SiteSettings.load()  # garantuj da red postoji
    assert SiteSettings.objects.filter(pk=1).exists()

    # QuerySet-nivo delete NE prolazi kroz instance delete() override → red NESTAJE.
    SiteSettings.objects.all().delete()
    assert SiteSettings.objects.filter(pk=1).exists() is False, (
        "QuerySet.delete() MORA zaobići instance guard i ukloniti red (dokumentovana "
        "granica singleton invarijante; AC2 caveat)."
    )


def test_load_is_idempotent():
    """AC2: višestruki load() NE kreira dodatne redove (uvek isti pk=1)."""
    SiteSettings = _get_model()
    a = SiteSettings.load()
    b = SiteSettings.load()
    assert a.pk == b.pk == 1, "load() MORA uvek vratiti pk=1."
    assert SiteSettings.objects.count() == 1, (
        "Višestruki load() NE SME kreirati dodatne redove (count()==1; SM-D2)."
    )
