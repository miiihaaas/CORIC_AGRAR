"""Ugovor za ``--profile`` opciju ``seed_sample_data`` komande.

Profil 1 je ISTORIJSKI manifest (Story 9-7) i mora ostati nepromenjen: `seed_e2e_data`
i Playwright E2E ciljaju tacne slug-ove. Profil 2 je kurirani demo sadrzaj koji se puni
odvojeno (`_seed_profiles/profile2.py`) i sme biti prazan dok se ne popuni.

HOST CAVEAT: pokretati kroz Docker (libmagic baseline na Windows host-u).
"""

from __future__ import annotations

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.core.management.commands.seed_sample_data import PROFILE_1
from apps.products.models import Product

pytestmark = pytest.mark.django_db

# Slug-ovi na koje se oslanja seed_e2e_data + Playwright E2E (tests/e2e/).
_E2E_LOCKED_SLUGS = {"agri-tracking-tb804", "wuzheng-wz504", "saillong-sl904"}


def _manifest_product_slugs() -> set[str]:
    """Slug-ovi koje profil 1 STVARNO seed-uje (bez migracijskih tulip-mix-*)."""
    return {
        item["slug"] for item in PROFILE_1["new_tractors"] + PROFILE_1["used_machines"]
    }


def test_profile_1_is_the_default():
    """Bez `--profile` ponasanje mora biti isto kao `--profile=1` (backward compat)."""
    call_command("seed_sample_data", force=True)
    default_slugs = set(Product.objects.values_list("slug", flat=True))

    # Brise se SAMO ono sto seed pravi. `Product.objects.all().delete()` bi odneo i
    # tulip-mix-* koje pravi migracija brands/0004 — njih seed ne bi vratio, pa bi
    # poredjenje palo iz razloga koji nema veze sa profilima.
    Product.objects.filter(slug__in=_manifest_product_slugs()).delete()
    call_command("seed_sample_data", force=True, profile="1")

    assert set(Product.objects.values_list("slug", flat=True)) == default_slugs


def test_profile_1_manifest_keeps_e2e_locked_slugs():
    """LOCK: promena ovih slug-ova tiho rusi ceo E2E suite."""
    manifest_slugs = {item["slug"] for item in PROFILE_1["new_tractors"]}
    assert _E2E_LOCKED_SLUGS <= manifest_slugs, (
        f"Profil 1 MORA zadržati E2E slug-ove {_E2E_LOCKED_SLUGS}; "
        f"manifest ima {manifest_slugs}."
    )


def test_profile_2_stub_runs_without_error():
    """Prazan profil 2 se preskace bez greske — puni se postepeno.

    Bez tolerantnog rukovanja praznim sekcijama, `_seed_specs` bi pukao na
    `Product.DoesNotExist`, a `_seed_blog` na KeyError.
    """
    before = set(Product.objects.values_list("slug", flat=True))
    call_command("seed_sample_data", force=True, profile="2")
    after = set(Product.objects.values_list("slug", flat=True))
    assert after == before, "Prazan manifest ne sme praviti nove proizvode."


def test_profile_2_does_not_touch_profile_1_content():
    """Pokretanje profila 2 ne sme obrisati ni promeniti sadrzaj profila 1 (aditivno)."""
    call_command("seed_sample_data", force=True, profile="1")
    slugs_before = set(Product.objects.values_list("slug", flat=True))
    call_command("seed_sample_data", force=True, profile="2")
    assert set(Product.objects.values_list("slug", flat=True)) == slugs_before


def test_unknown_profile_is_rejected():
    """Argument se prosledjuje kao argv da bi argparse validirao `choices`.

    `call_command(..., profile="99")` (kwarg forma) zaobilazi argparse validaciju —
    kroz argv formu nepoznat profil pada glasno, kako i treba.
    """
    with pytest.raises(CommandError, match="invalid choice"):
        call_command("seed_sample_data", "--force", "--profile=99")
