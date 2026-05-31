"""Story 2.12 — Breadcrumb root parametrization + duplikat reconciliacija (RED phase).

Pokriva SM-D13 / OQ-1a (AC9 breadcrumb fix). SubcategoryListView._build_breadcrumb
dobija parametrizovan root (_breadcrumb_root_for) + reconciliaciju duplikata kada je
category landing-mapirana (radne-masine).

KANONSKI HZM L1 trag (duplikat-free): TAČNO
    ["Početna"(link), "Radne mašine"(link→hzm_radne_masine), "<sub naziv>"(non-link)]
    — length 3, NEMA ponovljene "Radne mašine".

Jeegee regression: root "Priključna mehanizacija" + category.name link stavka ZADRŽANI
    (root-label ≠ category.name pa NEMA kolapsa).

Testovi rade preko response.context["breadcrumb_items"] (live SubcategoryListView ctx
ključ; render kroz brands/partials/_breadcrumb.html).

Pokrenuti sa:
    docker compose -f compose/local.yml run --rm django uv run pytest \\
        apps/brands/tests/test_breadcrumb_root_parametrization.py -v

Refs:
- 2-12-hzm-radne-masine-tulip-mix-prikolice-strane.md (AC9, Subtask 8.4b, SM-D13)
- 2-12-interface-contract.md (§ 2.3 SubcategoryListView UŽA izmena)
"""

from __future__ import annotations

import pytest
from django.urls import reverse
from django.utils.translation import activate

from apps.brands.models import Category
from apps.brands.tests.factories import CategoryFactory, SubcategoryFactory

pytestmark = pytest.mark.django_db


def _hzm_l1_url(sub_slug: str) -> str:
    return f"/sr/mehanizacija/prikljucna/radne-masine/{sub_slug}/"


def _breadcrumb_items(response):
    """Ekstrahuj breadcrumb stavke iz konteksta (SubcategoryListView ctx ključ)."""
    ctx = response.context
    items = ctx.get("breadcrumb_items")
    assert items is not None, (
        "Context MORA sadržati 'breadcrumb_items' (SubcategoryListView._build_breadcrumb)."
    )
    return list(items)


# =============================================================================
# HZM (landing-mapirana category) — duplikat-free full trail
# =============================================================================


def test_hzm_subcategory_breadcrumb_full_trail_no_duplicate(client):
    """SM-D13 KANONSKI FULL-TRAIL: HZM L1 drill-down = TAČNO 3 stavke, duplikat-free.

    GET /sr/mehanizacija/prikljucna/radne-masine/mini-utovarivaci/ →
        [Početna(link), Radne mašine(link→hzm_radne_masine), Mini utovarivači(non-link)]
    """
    activate("sr")
    response = client.get(_hzm_l1_url("mini-utovarivaci"))
    assert response.status_code == 200, (
        f"HZM L1 drill-down MORA rezolvovati Story 2-11 SubcategoryListView (NIJE 404). "
        f"radne-masine Category + mini-utovarivaci Subcategory seed-ovani kroz 0004. "
        f"Dobio {response.status_code}."
    )

    trail = _breadcrumb_items(response)
    labels = [str(i["label"]) for i in trail]

    assert len(trail) == 3, (
        f"HZM L1 breadcrumb MORA imati TAČNO 3 stavke (duplikat-free), dobio {len(trail)}: "
        f"{labels!r}. Ako je 4 (Početna → Radne mašine → Radne mašine → <sub>), "
        f"reconciliacija (SM-D13) NIJE primenjena."
    )

    # Item-by-item
    assert labels[0] == "Početna", f"Stavka 1 MORA biti 'Početna', dobio {labels[0]!r}."
    assert trail[0]["url"] == reverse("pages:home"), (
        "Stavka 'Početna' MORA linkovati na pages:home."
    )

    assert labels[1] == "Radne mašine", (
        f"Stavka 2 (root) MORA biti 'Radne mašine', dobio {labels[1]!r}. NE "
        f"'Priključna mehanizacija' (root-parametrizacija SM-D13)."
    )
    assert trail[1]["url"] == reverse("brands:hzm_radne_masine"), (
        f"Stavka 'Radne mašine' MORA linkovati na brands:hzm_radne_masine, dobio "
        f"{trail[1]['url']!r}."
    )

    assert labels[2] == "Mini utovarivači", (
        f"Stavka 3 (tail) MORA biti naziv subcategory-je 'Mini utovarivači', dobio "
        f"{labels[2]!r}."
    )
    assert trail[2]["is_current"] is True and trail[2]["url"] is None, (
        f"Tail stavka MORA biti NON-link (is_current=True, url=None), dobio "
        f"is_current={trail[2]['is_current']!r} url={trail[2]['url']!r}."
    )

    # EKSPLICITNO: NEMA ponovljene "Radne mašine"
    assert labels.count("Radne mašine") == 1, (
        f"'Radne mašine' se sme pojaviti TAČNO 1 put u tragu, pojavila se "
        f"{labels.count('Radne mašine')} puta: {labels!r}. Susedni duplikat "
        f"'Radne mašine → Radne mašine' MORA biti kolapsiran (SM-D13)."
    )


def test_hzm_subcategory_drilldown_breadcrumb_root_is_radne_masine(client):
    """SM-D13: root (druga) breadcrumb stavka == 'Radne mašine' link na hzm_radne_masine.

    NE 'Priključna mehanizacija' (default fallback ne sme se primeniti za radne-masine).
    """
    activate("sr")
    response = client.get(_hzm_l1_url("teleskopski-utovarivaci"))
    assert response.status_code == 200

    trail = _breadcrumb_items(response)
    labels = [str(i["label"]) for i in trail]

    assert "Priključna mehanizacija" not in labels, (
        f"HZM breadcrumb NE SME sadržati 'Priključna mehanizacija' (root-parametrizacija "
        f"mora dati 'Radne mašine'). Trag: {labels!r}."
    )
    root = trail[1]
    assert str(root["label"]) == "Radne mašine"
    assert root["url"] == reverse("brands:hzm_radne_masine")


# =============================================================================
# Jeegee (DEFAULT, ne-mapirana) — regression: NEPROMENJEN trag
# =============================================================================


def test_jeegee_subcategory_breadcrumb_full_trail_unchanged(client):
    """SM-D13 REGRESSION: Jeegee prikljucna drill-down trag NEPROMENJEN.

    Jeegee root 'Priključna mehanizacija' ZADRŽAN + category.name link stavka ZADRŽANA
    (root-label ≠ category.name pa NEMA kolapsa). Koristi seeded osnovna-obrada-zemljista
    Category (0003) + dodaje L1 subcategory factory-jem.
    """
    activate("sr")
    category = Category.objects.get(slug="osnovna-obrada-zemljista")
    SubcategoryFactory(category=category, parent=None, slug="plug", name="Plug")

    response = client.get("/sr/mehanizacija/prikljucna/osnovna-obrada-zemljista/plug/")
    assert response.status_code == 200, (
        f"Jeegee L1 drill-down MORA rezolvovati SubcategoryListView, dobio "
        f"{response.status_code}."
    )

    trail = _breadcrumb_items(response)
    labels = [str(i["label"]) for i in trail]

    # Root i dalje 'Priključna mehanizacija'
    assert labels[1] == "Priključna mehanizacija", (
        f"Jeegee root (stavka 2) MORA ostati 'Priključna mehanizacija', dobio {labels[1]!r}. "
        f"DEFAULT branch NEPROMENJEN."
    )
    assert trail[1]["url"] == reverse("brands:jeegee_prikljucna")

    # category.name link stavka ZADRŽANA (NIJE kolapsirana)
    assert "Osnovna obrada zemljišta" in labels, (
        f"Jeegee category.name 'Osnovna obrada zemljišta' link stavka MORA biti ZADRŽANA "
        f"(NE kolapsirana — Jeegee root-label ≠ category.name). Trag: {labels!r}."
    )
    cat_item = next(i for i in trail if str(i["label"]) == "Osnovna obrada zemljišta")
    assert cat_item["url"] is not None and cat_item["is_current"] is False, (
        "Jeegee category.name stavka MORA biti LINK (NE non-link), regression guard."
    )

    # Tail je leaf non-link
    assert labels[-1] == "Plug"
    assert trail[-1]["is_current"] is True and trail[-1]["url"] is None


def test_jeegee_subcategory_drilldown_breadcrumb_root_unchanged(client):
    """SM-D13 REGRESSION: Jeegee root i dalje 'Priključna mehanizacija' / jeegee_prikljucna."""
    activate("sr")
    category = Category.objects.get(slug="priprema-zemljista")
    SubcategoryFactory(category=category, parent=None, slug="tanjirace", name="Tanjirače")

    response = client.get("/sr/mehanizacija/prikljucna/priprema-zemljista/tanjirace/")
    assert response.status_code == 200

    trail = _breadcrumb_items(response)
    root = trail[1]
    assert str(root["label"]) == "Priključna mehanizacija", (
        f"Jeegee root NEPROMENJEN — 'Priključna mehanizacija', dobio {root['label']!r}."
    )
    assert root["url"] == reverse("brands:jeegee_prikljucna")


def test_breadcrumb_root_fallback_generic_for_unmapped_category(client):
    """SM-D13: nemapirana MEHANIZACIJA category → DEFAULT generički root.

    AŽURIRANO (prior wording flagged): DEFAULT root je generički 'Priključna
    mehanizacija' label linkovan na brands:jeegee_prikljucna (NE category.name).
    Kreira novu MEHANIZACIJA category van mape; root MORA biti generički fallback,
    NE crash, NE category.name kao root.
    """
    activate("sr")
    category = CategoryFactory(
        slug="nova-mehanizacija",
        name="Nova mehanizacija",
        is_for=Category.CategoryScope.MEHANIZACIJA,
    )
    SubcategoryFactory(category=category, parent=None, slug="podkat", name="Podkategorija")

    response = client.get("/sr/mehanizacija/prikljucna/nova-mehanizacija/podkat/")
    assert response.status_code == 200, (
        f"Nemapirana MEHANIZACIJA category drill-down MORA rezolvovati (NE crash), dobio "
        f"{response.status_code}."
    )

    trail = _breadcrumb_items(response)
    labels = [str(i["label"]) for i in trail]
    root = trail[1]

    assert str(root["label"]) == "Priključna mehanizacija", (
        f"DEFAULT (nemapirana) root MORA biti generički 'Priključna mehanizacija' (NE "
        f"category.name 'Nova mehanizacija'), dobio {root['label']!r}."
    )
    assert root["url"] == reverse("brands:jeegee_prikljucna"), (
        f"DEFAULT root MORA linkovati na brands:jeegee_prikljucna, dobio {root['url']!r}."
    )
    # category.name link stavka ZADRŽANA (default branch ne kolapsira)
    assert "Nova mehanizacija" in labels, (
        f"Default branch ZADRŽAVA category.name 'Nova mehanizacija' link stavku, trag: "
        f"{labels!r}."
    )
