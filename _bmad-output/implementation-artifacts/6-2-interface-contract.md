# 6.2 Interface Contract — Sitemap Auto-generation sa Hreflang

> TEA canonical contract (RED phase complete). Dev implementira EXACTLY ove
> signature da prebaci 31 RED test u GREEN. **Dev NE piše testove. NEMA migracije
> (0-migration lock). NEMA `uv add` (`django.contrib.sitemaps` je Django core).**

Status: red-confirmed (33 failed [2 su trajni guard-lock-ovi koji pass-uju by design], existing 63 6-1 testova GREEN)

---

## 1. `apps/seo/sitemaps.py` (NOVI fajl) — 5 Sitemap klasa + helper + dict

### Importi (lazy preko urls.py — NIKAD u models.py/apps.ready)

```python
from django.contrib.contenttypes.models import ContentType
from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from apps.blog.models import Post
from apps.brands.models import Brand, Subcategory       # NE Series/Category (CRIT-2)
from apps.products.models import Product
from apps.seo.models import SeoMeta
```

### `_excluded_pks(model) -> set` — deljen GFK exclusion-set helper (JEDAN query)

```python
def _excluded_pks(model):
    ct = ContentType.objects.get_for_model(model)
    return set(
        SeoMeta.objects.filter(
            content_type=ct, exclude_from_sitemap=True
        ).values_list("object_id", flat=True)
    )
```

- JEDAN query po pozivu; pozvati JEDNOM u svakom `items()` (NE per-objekat → NE N+1).
- GFK — NEMA join / NEMA reverse accessor (SeoMeta nema GenericRelation; ARCH-2/SM-D4/SM2-4).

### 5 Sitemap klasa — SVE `i18n = True`, `alternates = True`

| Klasa | `items()` baza (public predikat MINUS excluded) | `location()` | `lastmod()` |
|---|---|---|---|
| `ProductSitemap` | `Product.objects.filter(is_published=True).exclude(pk__in=_excluded_pks(Product))` | default (`get_absolute_url`) | `obj.updated_at` |
| `BrandSitemap` | `Brand.objects.filter(is_coming_soon=False).exclude(pk__in=_excluded_pks(Brand))` | default | `obj.updated_at` |
| `SubcategorySitemap` | `Subcategory.objects.select_related("category", "parent", "parent__parent").exclude(pk__in=_excluded_pks(Subcategory))` | default | `obj.updated_at` |
| `BlogPostSitemap` | `Post.published.all().exclude(pk__in=_excluded_pks(Post))` | default | `obj.updated_at` |
| `PageSitemap` | `["pages:home", "pages:about", "pages:contact"]` (lista URL-imena) | `reverse(item)` | **NEMA metode** (omit) |

- **NEMA `SeriesSitemap` ni `CategorySitemap`** (CRIT-2/SM-D6 — `get_absolute_url` RAISE `NoReverseMatch`; rute ne postoje → uključenje = HTTP 500 ceo sitemap).
- `SubcategorySitemap.items()` MORA `select_related` (GAP-1 — N+1 na `get_ancestors_chain()` × 3 jezika).
- `PageSitemap`: NE definisati `lastmod` metodu (Django proverava `hasattr` → izostavi `<lastmod>`; SM2-7). NE vraćati `None`.
- `changefreq`/`priority` = OMIT (SM-D7/OQ-3). `x_default` = DEFER (OQ-2 — testovi tolerišu ako se doda).

### `sitemaps` modul-level dict (5 ključeva — TAČNO ovi stringovi)

```python
sitemaps = {
    "products": ProductSitemap,
    "brands": BrandSitemap,
    "subcategories": SubcategorySitemap,
    "blog": BlogPostSitemap,
    "pages": PageSitemap,
}
```

- Testovi zaključavaju `set(sitemaps.keys()) == {"products","brands","subcategories","blog","pages"}` (NEMA series/category).

---

## 2. `config/settings/base.py` (EDIT) — INSTALLED_APPS

- Dodaj `"django.contrib.sitemaps"` u `INSTALLED_APPS` (u Django contrib grupi, npr. posle `"django.contrib.postgres"` ili `"django.contrib.staticfiles"`).
- **NE dodaj `"django.contrib.sites"`** (SM-D2/SM2-9 — RequestSite fallback; 0-migration lock; test zaključava da `sites` NIJE prisutan).

---

## 3. `config/urls.py` (EDIT) — registracija VAN i18n_patterns

```python
from django.contrib.sitemaps.views import sitemap
from apps.seo.sitemaps import sitemaps as sitemaps_dict
```

Dodati u NO-PREFIX `urlpatterns` blok (gde je `i18n/setlang/`), **VAN `i18n_patterns(...)`**:

```python
urlpatterns = [
    path("i18n/setlang/", set_language, name="set_language"),
    path(
        "sitemap.xml",
        sitemap,
        {"sitemaps": sitemaps_dict},
        name="django.contrib.sitemaps.views.sitemap",
    ),
]
```

- `name=` MORA biti TAČNO `"django.contrib.sitemaps.views.sitemap"` (SM2-10; test: `reverse(...) == "/sitemap.xml"`).
- GET `/sitemap.xml` → 200; GET `/sr/sitemap.xml` → 404 (AC7 lock).

---

## 4. Predikati / loc / namespace koje testovi koriste (Dev reference)

- **Public predikati (SM-D3):** Product `is_published=True`; Brand `is_coming_soon=False`; Subcategory `.all()`; Post `Post.published` (status=published AND published_at<=now → draft + scheduled izostaju); Page home/about/contact.
- **Namespace konstante:** `SM_NS = "http://www.sitemaps.org/schemas/sitemap/0.9"`, `XHTML_NS = "http://www.w3.org/1999/xhtml"`.
- **loc membership** = PATH SUFIKS (`obj.get_absolute_url()`), NE pun apsolutni URL (host=testserver iz RequestSite; IMP-4/SM2-2).
- **Hreflang:** svaki `<url>` ima 3× `<xhtml:link rel="alternate" hreflang="sr|hu|en" href="/sr|/hu|/en/...">` (i18n+alternates True; IMP-5 namespace-aware parse).
- **Exclude:** `SeoMeta.objects.create(content_object=obj, exclude_from_sitemap=True)` → `obj.get_absolute_url()` ABSENT; per-content_type izolacija (Product + Post nezavisni).
- **lastmod:** model `<url>` ima `<lastmod>` sa `updated_at.date().isoformat()` prefiksom; PageSitemap home `<url>` BEZ `<lastmod>`.

---

## 5. Test fajlovi (TEA RED — Dev NE menja)

| Fajl | AC | Tests | Napomena |
|---|---|---|---|
| `test_sitemap_registration.py` | AC1/AC7 | 9 | INSTALLED_APPS + sitemaps dict (5 keys) + i18n/alternates atribut + 200 + /sr/ 404 + reverse |
| `test_sitemap_xml.py` | AC2/AC8 | 6 | 200 + xml content-type + well-formed + urlset ns + xhtml ns + ≥1 loc |
| `test_sitemap_content.py` | AC3 | 7 | svaki tip prisutan + pages + **CRIT-2 guard** (Series/Category seed → STILL 200) |
| `test_sitemap_draft_not_leaked.py` | AC4 | 5 | **SECURITY LOCK** (4 non-public parametrized + 1 public-control) |
| `test_sitemap_hreflang.py` | AC5 | 3 | xhtml:link alternate sr/hu/en + locale-prefiksovan href (namespace-aware) |
| `test_sitemap_exclude.py` | AC6 | 4 | Product+Post exclude absent + non-excluded present (2-content-type izolacija) |
| `test_sitemap_lastmod.py` | AC9 | 2 | model lastmod=updated_at + PageSitemap bez lastmod |

Total: 36 testova (33 fail RED + 2 trajni guard-lock pass [`sites` absent, `/sr/` 404] + 1 — see run). Dev cilj: SVE GREEN posle impl.
