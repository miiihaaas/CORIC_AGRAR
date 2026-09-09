"""Ugovor za ``--profile`` opciju ``seed_sample_data`` komande.

Profil 1 je ISTORIJSKI manifest (Story 9-7) i mora ostati nepromenjen: `seed_e2e_data`
i Playwright E2E ciljaju tacne slug-ove. Profil 2 je kurirani "1:1 snapshot lokalne baze"
manifest (`_seed_profiles/profile2.py`, auto-generisan kroz
``ops/seed/generate_profile2_manifest.py``) — od 2026-09-09 NIJE vise prazan stub.

HOST CAVEAT: pokretati kroz Docker (libmagic baseline na Windows host-u).
"""

from __future__ import annotations

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.core.management.commands._seed_profiles.profile2 import PROFILE_2
from apps.core.management.commands.seed_sample_data import PROFILE_1
from apps.products.models import Product

pytestmark = pytest.mark.django_db

# Slug-ovi na koje se oslanja seed_e2e_data + Playwright E2E (tests/e2e/).
_E2E_LOCKED_SLUGS = {"agri-tracking-tb804", "wuzheng-wz504", "saillong-sl904"}


@pytest.fixture(autouse=True)
def _isolate_media_root(settings, tmp_path):
    """Profil 2 prilaže stvarne seed asset fajlove (slike/PDF) na FileField-ove —
    izoluj MEDIA_ROOT u tmp_path da testovi ne pišu u repo ``media/`` dir (established
    project pattern — vidi apps/blog, apps/forms, apps/media_pipeline conftest.py)."""
    settings.MEDIA_ROOT = str(tmp_path)


def _manifest_product_slugs() -> set[str]:
    """Slug-ovi koje profil 1 STVARNO seed-uje (bez migracijskih tulip-mix-*)."""
    return {
        item["slug"] for item in PROFILE_1["new_tractors"] + PROFILE_1["used_machines"]
    }


def _profile_2_product_slugs() -> set[str]:
    """Slug-ovi koje profil 2 STVARNO seed-uje (bez migracijskih tulip-mix-*)."""
    return {
        item["slug"] for item in PROFILE_2["new_tractors"] + PROFILE_2["used_machines"]
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


def test_profile_2_seeds_expected_product_slugs():
    """Profil 2 (1:1 snapshot lokalne baze) mora seed-ovati tacno svoje manifest slug-ove."""
    call_command("seed_sample_data", force=True, profile="2")
    seeded = set(Product.objects.values_list("slug", flat=True))
    assert _profile_2_product_slugs() <= seeded


def test_profile_2_is_idempotent_on_second_run():
    """Drugo pokretanje profila 2 ne sme praviti duplikate (get_or_create po slug-u)."""
    call_command("seed_sample_data", force=True, profile="2")
    after_first = set(Product.objects.values_list("slug", flat=True))
    call_command(
        "seed_sample_data", force=True, profile="2"
    )  # MUST NOT raise/duplicate
    assert set(Product.objects.values_list("slug", flat=True)) == after_first
    for slug in _profile_2_product_slugs():
        assert Product.objects.filter(slug=slug).count() == 1


def test_profile_2_does_not_remove_profile_1_content():
    """Pokretanje profila 2 ne sme obrisati ni promeniti postojeci sadrzaj profila 1 (aditivno).

    Profili DELE neke slug-ove (npr. agri-tracking-tb804) — profil 2 samo referencira/
    dopunjuje isti red kroz get_or_create, ne pravi drugi. Zato proveravamo da SVI
    profil-1 slug-ovi i dalje postoje, ne da se skup slug-ova ne menja (profil 2
    legitimno dodaje i sopstvene, dodatne proizvode).
    """
    call_command("seed_sample_data", force=True, profile="1")
    slugs_before = set(Product.objects.values_list("slug", flat=True))
    call_command("seed_sample_data", force=True, profile="2")
    slugs_after = set(Product.objects.values_list("slug", flat=True))
    assert slugs_before <= slugs_after


def test_unknown_profile_is_rejected():
    """Argument se prosledjuje kao argv da bi argparse validirao `choices`.

    `call_command(..., profile="99")` (kwarg forma) zaobilazi argparse validaciju —
    kroz argv formu nepoznat profil pada glasno, kako i treba.
    """
    with pytest.raises(CommandError, match="invalid choice"):
        call_command("seed_sample_data", "--force", "--profile=99")
