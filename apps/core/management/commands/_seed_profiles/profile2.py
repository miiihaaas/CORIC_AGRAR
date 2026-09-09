"""Profil 2 — kurirani demo sadrzaj za prezentaciju (STUB, popunjava se odvojeno).

Ovaj modul je CIST PODATAK. Seed logika (get_or_create po eksplicitnom slug-u,
modeltranslation `_sr` kolone, counters, atomicity, production guard) zivi u
``seed_sample_data.py`` i deli se sa profilom 1 — ovde se NE pise logika.

KAKO POPUNITI
-------------
Svaka sekcija ima isti oblik kao u ``PROFILE_1`` (vidi seed_sample_data.py).
Prazna sekcija se preskace bez greske, pa profil moze da se puni postepeno.

- ``tractor_brands``: {"slug", "name", "description", "slogan"}
- ``referenced_brand_slugs``: tuple slug-ova brendova koje su napravile DATA
  MIGRACIJE (npr. "jeegee", "hzm", "tulip"). Referenciraju se, NE prave iznova.
- ``traktori_category``: {"slug", "name", "description", "is_for", "display_order"}
- ``new_tractors`` / ``used_machines``: {"slug", "brand_slug", "name",
  "description", "key_features" (lista), "horse_power", "year",
  "price_eur" (Decimal)}
- ``headline_specs``: {"product_slug", "specs": [{"section", "key", "value",
  "order"}]} — ``product_slug`` MORA biti seed-ovan u istom profilu, inace
  komanda fail-uje glasno.
- ``blog``: {"category": {...}, "tag": {...}, "posts": [{"slug", "title",
  "perex", "body"}]}

PRAVILA (ista kao profil 1)
---------------------------
1. ``slug`` je ASCII, bez dijakritika — on je lookup kljuc za idempotentnost.
2. Svi tekstovi koje korisnik vidi imaju pune srpske dijakritike (c, c, z, s, dj).
3. Brendove Jeegee/HZM/Tulip i priključne kategorije prave data migracije —
   ovde ih SAMO referenciraj kroz ``referenced_brand_slugs`` / ``brand_slug``.
4. NE dodavati korisnike ni kredencijale — to nije posao seed komande.

Pokretanje: ``just dev-manage seed_sample_data --profile=2``
"""

from __future__ import annotations

PROFILE_2: dict = {
    "tractor_brands": [],
    "referenced_brand_slugs": (),
    "traktori_category": None,
    "new_tractors": [],
    "used_machines": [],
    "headline_specs": None,
    "blog": None,
}
