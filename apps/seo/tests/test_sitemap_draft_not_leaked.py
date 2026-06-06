"""Story 6.2 — DRAFT-NOT-LEAKED SECURITY LOCK (TEA RED phase).

Pokriva AC4 (SM-D3) — NAJVAŽNIJI test 6.2. Jedan nacrt u sitemap-u = curenje u
Google indeks (bezbednosni/poslovni propust).

Seed (svaki uz JAVNU kontrolu istog tipa):
- unpublished Product (is_published=False)        vs javni Product (is_published=True)
- coming-soon Brand (is_coming_soon=True)         vs javni Brand (is_coming_soon=False)
- draft Post (status=draft)                       vs published Post
- scheduled Post (status=published, published_at=now+7d)  vs published Post

Then: NIJEDAN non-public get_absolute_url path NIJE u <loc> skupu; SVE javne
kontrole JESU. Polaritet predikata je lako pogrešiti (SM2-5) — ovaj test ga
zaključava behavior-om.

IMP-4: path SUFIKSI (get_absolute_url()), NE puni apsolutni URL.

Refs:
- 6-2-...-hreflang.md AC4 + Task 6.3 + SM-D3 + Gotcha SM2-5
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

import pytest

pytestmark = pytest.mark.django_db

SM_NS = "http://www.sitemaps.org/schemas/sitemap/0.9"


def _loc_texts(content: bytes) -> list[str]:
    root = ET.fromstring(content)
    return [el.text for el in root.findall(f".//{{{SM_NS}}}loc") if el.text]


@pytest.fixture
def leak_scenario(make_post):
    from django.utils import timezone

    from apps.brands.tests.factories import BrandFactory
    from apps.products.tests.factories import ProductFactory

    now = timezone.now()
    future = now + timezone.timedelta(days=7)

    public_product = ProductFactory.create(name="Javni Traktor Sitemap")
    draft_product = ProductFactory.create_unpublished(name="Nacrt Traktor Sitemap")

    public_brand = BrandFactory.create(name="Javni Brend Sitemap")
    coming_soon_brand = BrandFactory.create_coming_soon(name="Uskoro Brend Sitemap")

    public_post = make_post(
        title="Objavljena vest sitemap",
        status="published",
        published_at=now,
    )
    draft_post = make_post(title="Nacrt vest sitemap", status="draft")
    scheduled_post = make_post(
        title="Zakazana vest sitemap",
        status="published",
        published_at=future,
    )

    return {
        "public": [public_product, public_brand, public_post],
        "leaked_candidates": [
            ("unpublished Product", draft_product),
            ("coming-soon Brand", coming_soon_brand),
            ("draft Post", draft_post),
            ("scheduled (future) Post", scheduled_post),
        ],
    }


def test_public_controls_present(client, leak_scenario):
    response = client.get("/sitemap.xml")
    assert response.status_code == 200
    locs = _loc_texts(response.content)
    for obj in leak_scenario["public"]:
        path = obj.get_absolute_url()
        assert any(path in loc for loc in locs), (
            f"JAVNA kontrola {obj} ({path!r}) MORA biti u sitemap-u (pozitivna kontrola; AC4)."
        )


def test_leak_scenario_has_all_four_non_public_cases(leak_scenario):
    assert len(leak_scenario["leaked_candidates"]) == 4, (
        "Fixture mora imati TAČNO 4 non-public slučaja (unpublished Product, "
        "coming-soon Brand, draft Post, scheduled Post) — inače parametrize "
        "indeksi tiho gube pokrivenost (posebno future-Post indeks 3)."
    )


@pytest.mark.parametrize(
    "label_idx",
    [0, 1, 2, 3],
    ids=["unpublished-product", "coming-soon-brand", "draft-post", "scheduled-post"],
)
def test_non_public_not_leaked(client, leak_scenario, label_idx):
    label, obj = leak_scenario["leaked_candidates"][label_idx]
    response = client.get("/sitemap.xml")
    assert response.status_code == 200
    locs = _loc_texts(response.content)
    path = obj.get_absolute_url()
    assert not any(path in loc for loc in locs), (
        f"SECURITY LEAK: {label} ({path!r}) NE SME biti u sitemap-u — curenje "
        f"nacrta u Google indeks (AC4/SM-D3)."
    )
