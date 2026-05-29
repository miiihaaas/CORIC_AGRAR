---
story-id: "2.2"
story-key: 2-2-product-i-related-modeli
title: Product i Related Modeli
status: ready-for-dev
epic_num: 2
epic_title: Public Catalog — Browse Brands & Products
module: apps/products/ (NOVO Django app — drugi domain app u Epic 2)
created: 2026-05-29
last_modified: 2026-05-29
author: Mihas (SM autonomous)
---

# Story 2.2: Product i Related Modeli

Status: ready-for-dev

## Story

As a **dev (Mihas) koji nastavlja Epic 2 (Public Catalog) posle Story 2.1 (brands taksonomija)**,
I want **sedam kanonskih modela u novom `apps/products/` Django app-u — `Product` (root entitet) + 6 related modela (`ProductImage`, `ProductVariant`, `ProductSpecification`, `ProductBrochure`, `ProductTestimonial`, `ProductSimilar`) — sa pratećim `translation.py` registracijom (`django-modeltranslation`), eksplicitnim `on_delete` + `related_name` na svim FK-ovima, ASCII slug-om na `Product` kroz `SluggedModel` base mixin iz Story 2.1, `Meta.indexes` sa imenima per `<table>_<columns>_idx` konvencijom, `get_absolute_url()` metodom koja vraća `/proizvod/<slug>/`, `condition`/`status` TextChoices enum-ima, i validacijom maksimuma 3 entry-ja u `Product.key_features` JSON listi**,
so that **mogu da modeliram kompletan content layer za Product Detail stranu (Story 2.7), Tractor/Used listing strane (2.8/2.9), Brand listing extended layout (2.6), Image pipeline thumbnail generation (2.3), PDF cover thumbnail signal (2.4), Global FTS search (2.13 dodaje `search_vector` u zasebnoj migraciji), i Admin Product CRUD multi-locale (8.6) — sve uz strogo poštovanje jednosmerne `products → brands` zavisnosti (per architecture.md § Architectural Boundaries: `core ← brands ← products ← catalog`).**

Ova story je **drugi domain Django app u Epic 2** i **prvi konzument `apps/core/models.py` base mixina** (`TimestampedModel` + `SluggedModel`) koje je Story 2.1 uvela kao FOUNDATION (Decision D3 u 2-1 honest YAGNI acknowledgment — base klase su tada bile pripremljene, sada se prvi put konzumiraju). Story 2.2 uvodi `apps/products/` direktorijum (per project-context.md § File organization), proširuje `INSTALLED_APPS` sa `"apps.products"` (APENDOVAN POSLE `"apps.brands"` zbog jednosmerne zavisnosti — `apps.products.models` import-uje `apps.brands.models.Brand` etc.; obrnuto je STROGO ZABRANJENO per architecture.md § Zabranjene zavisnosti; postojeći redosled iz 2.1 sa `modeltranslation` kao prvim entry-jem ostaje NEPROMENJEN — vidi Decision PR-D1), i registruje 6 translation registracija u `apps/products/translation.py` (Product, ProductImage, ProductVariant, ProductSpecification, ProductBrochure, ProductTestimonial — 6 modela ima translatable polja; `ProductSimilar` je čisto relational i nema translatable polja). **Translation scope je PROŠIREN na 6 entiteta (vs 4 u epics.md spec line 551) — videti Decision PR-D7 za rationale (a11y + multi-locale variant rendering).** Takođe dodaje `MODELTRANSLATION_FALLBACK_LANGUAGES = ("sr",)` u `config/settings/base.py` (locale fallback za prazne translated varijante — architecture-defensive setting koji obezbeđuje deterministički fallback chain ka sr per project-context.md § i18n locale fallback; Story 6.5 / FR-32 gradi UI fallback marker na vrhu ove backend foundation).

**Foundation za:**
- **Story 2.3 (Image Pipeline sa sorl-thumbnail):** koristi `Product.main_image` + `ProductImage.image` + `ProductVariant.image` + `ProductTestimonial.photo` polja kao input za `sorl-thumbnail` srcset helper; uvodi `apps/media_pipeline/utils.py validate_image_mime()` koji 2.2 ne implementira (Gotcha PR-3 — defer to 2.3).
- **Story 2.4 (PDF Cover Thumbnail Generator):** uvodi `post_save` signal na `ProductBrochure` koji koristi `pdf2image` da render-uje prvu stranu PDF-a kao 240×320 JPG u `cover_thumbnail_image` polje; Story 2.2 samo definiše `ProductBrochure.cover_thumbnail_image = ImageField(blank=True)` polje.
- **Story 2.6 (Brand Listing — Grid/Extended Layout):** koristi `Product.is_published` filter, `Product.brand` + `Product.series` joins, `Product.main_image`; Extended layout sekcija prikazuje `ProductSpecification` akordion grupisan po `section` TextChoices.
- **Story 2.7 (Product Detail strana):** TEŽAK konzument 2.2 — koristi sve modele: `Product` (hero + opis), `ProductImage` (galerija sa `<picture>` srcset), `ProductVariant` (selektor sa Lightbox zoom), `ProductSpecification` (akordion grupisan po section), `ProductBrochure` (download card sa cover thumbnail), `ProductTestimonial` (slider "Iz prve ruke"), `ProductSimilar` (FR-20 hibrid logika: manual override ako postoje entry-ji, inače auto-fallback po brand/series). (Story 2.7 breadcrumb implikacija za both-NULL series+subcategory edge case — videti Decision PR-D2+D3 combined; IMP-iter4-6 dedup.)
- **Story 2.8/2.9 (Tractor/Used Listing sa HTMX filterima):** koristi `Product.horse_power`, `Product.price_eur`, `Product.year`, `Product.condition` choices za HTMX range slider filtere.
- **Story 2.11 (Subcategory listing 4-nivoa):** koristi `Product.subcategory` FK kroz `Subcategory.products.filter(is_published=True)` (`related_name="products"`).
- **Story 2.13 (Global Search sa PostgreSQL FTS):** dodaje `Product.search_vector = SearchVectorField()` polje u **zasebnoj migraciji** (`apps/products/migrations/0002_*.py`) — Story 2.2 NE uvodi search_vector (out-of-scope).
- **Story 8.6 (Product CRUD admin):** zamenjuje stub `admin.site.register(Product)` (AC8) sa punim ProductAdmin sa galerija upload inline, specs editor, varijante inline, brošure inline, testimonijali inline, similar manual override widget, multi-locale tab support.

**Princip:** Jedan novi Django app (`apps/products/`) sa **sedam modela u jednom `models.py` fajlu** (cohesion — sva 7 entiteta dele isti domen "product content"; per project-context.md § File organization). **Translation polja deklarativno registrovana u `translation.py`** koji modeltranslation auto-discoveruje pri startup-u (modeltranslation je registrovan u INSTALLED_APPS u Story 2.1, sada `apps.products` automatski dobija discovery). **Migracija je MANUAL-REVIEWED** pre commit-a per project-context.md § Migrations discipline. **NEMA admin custom forme, NEMA views, NEMA urls, NEMA template-a, NEMA signala, NEMA image pipeline-a** u ovoj story-ji — to je 2.3/2.4/2.6/2.7/8.6 scope. **NEMA `search_vector` polja** — to je 2.13 koji uvodi PostgreSQL FTS infrastrukturu u zasebnoj migraciji.

**Strukturna arhitektura — repository delta:**
Repository dobija novi direktorijum `apps/products/` sa Django app skeleton-om. **Šta `django-admin startapp` STVARNO generiše** (IMP-iter4-2 — verifikovano protiv Django 5.2 startapp template): `__init__.py`, `apps.py`, `admin.py`, `models.py`, `tests.py`, `views.py`, `migrations/__init__.py`. To je to — **NE generiše** `urls.py`, `forms.py`, `managers.py`, `signals.py`, `translation.py`. Story 2.2 dodaje SAMO `translation.py` (Task 3) i `tests/__init__.py` direktorijum (Task 1.2) — `urls.py`/`forms.py`/`managers.py`/`signals.py` **NE postoje posle 2.2 scope-a** i kreiraju se u 2.6/2.7/8.6 kad zatreba. Default `views.py` (sa placeholder komentarom) takođe se UKLANJA u Task 1.2b (mirror 2.1 discipline). `apps/core/models.py` se **ne menja** — `SluggedModel` i `TimestampedModel` su već definisani u Story 2.1 i sada se prvi put konzumiraju kroz inheritance. `apps/core/utils.py` se **ne menja** — `slugify_ascii()` helper je već u upotrebi. `config/settings/base.py` dobija **JEDAN nov app** u `INSTALLED_APPS`: `"apps.products"` APENDOVAN POSLE `"apps.brands"` (per app dependency rule — products zavisi od brands; modeltranslation ostaje prvi entry per Story 2.1 D2 / Gotcha BR-2). `apps/brands/` ostaje **netaknut** (jednosmerna zavisnost — brands ne sme da zna za products).

## Acceptance Criteria

**AC1 — `apps/products/` Django app je kreiran i registrovan u `INSTALLED_APPS` POSLE `apps.brands` (jednosmerna zavisnost; modeltranslation auto-discovery hook već postoji iz 2.1)**

- **Given** Story 2.1 završena (`apps/brands/` postoji sa 4 modela; `modeltranslation` registrovan u INSTALLED_APPS pre `apps.brands`; `apps/core/models.py` ima `TimestampedModel` + `SluggedModel`; `apps/core/utils.py` ima `slugify_ascii()`)
- **When** kreiram `apps/products/` kroz `uv run python manage.py startapp products apps/products` i dodajem app u `INSTALLED_APPS`
- **Then** sledeća struktura mora postojati:

  **AC1 — apps/products/ skeleton (Dev scope u 2.2):**
  - Direktorijum `apps/products/` u repository root-u
  - `apps/products/__init__.py` (prazan)
  - `apps/products/apps.py` sa `ProductsConfig(AppConfig)` klasom:
    - `default_auto_field = "django.db.models.BigAutoField"`
    - `name = "apps.products"` (KRITIČNO — `apps.products`, NE `products`; matches `INSTALLED_APPS` entry; vidi Gotcha PR-1)
    - `verbose_name = _("Proizvodi")` (locale-aware kroz `gettext_lazy`)
  - `apps/products/models.py` (sa 7 modela — AC2-AC8)
  - `apps/products/admin.py` (stub sa basic registracijama — AC11)
  - `apps/products/translation.py` (sa TranslationOptions registracijama — AC9)
  - `apps/products/tests/__init__.py` (prazan — Dev kreira)
  - `apps/products/migrations/__init__.py` (auto-kreiran kroz startapp)

  ─────────────────────────────────────────────────────
  **AC1 — TEA deliverables u Step 3 (IMP-iter5-4 — NIJE Dev scope u 2.2):**
  ─────────────────────────────────────────────────────
  - `apps/products/tests/test_models.py` — TEA piše RED phase testove (sva AC13 scenarija)
  - `apps/products/tests/test_apps.py` — TEA smoke (ProductsConfig.name)
  - `tests/integration/test_app_boundaries.py` — TEA kreira posle Task 6.3a (AST static check)
  - **Dev ostavlja `apps/products/tests/` direktorijum SAMO sa `__init__.py`**; videti project-context.md § Test discipline ("TEA piše testove, Dev NIKAD ne piše testove").
  ─────────────────────────────────────────────────────
- **And** `config/settings/base.py` `INSTALLED_APPS` lista dobija **JEDAN nov entry** APENDOVAN na kraj liste (Decision PR-D1 — products MORA biti POSLE brands jer `apps.products.models.Product` import-uje `apps.brands.models.Brand`). **KRITIČNO (CRIT-iter4-1):** ne reorder-uj postojeći redosled — `modeltranslation` MORA ostati PRVI (Story 2.1 Decision D2 / Gotcha BR-2 — modeltranslation patch-uje admin pri `AppConfig.ready()` i mora biti registrovan PRE `django.contrib.admin`). Snippet ispod odgovara **redosledu** live `config/settings/base.py` posle Story 2.1 — komentari su skraćeni za čitljivost; live fajl ima detaljnije Story-X.Y reference (npr. "NOVO Story 1.6 — request.htmx detection" umesto kratkog "Story 1.6"). Task 1.4 dodaje SAMO jednu liniju (`'apps.products'`) — **NE radi block replace** koji bi prebrisao live komentare:
  ```python
  INSTALLED_APPS = [
      # NAPOMENA: modeltranslation MORA biti PRE django.contrib.admin
      # (per django-modeltranslation docs § Configuration — admin integration
      # patch-uje admin pri AppConfig.ready() i mora imati referenciu na
      # admin pre nego što admin registruje own widget-e). Vidi Story 2.1
      # Decision D2 + Gotcha BR-2.
      "modeltranslation",            # Story 2.1 — MORA PRVI (PRE django.contrib.admin)
      "django.contrib.admin",
      "django.contrib.auth",
      "django.contrib.contenttypes",
      "django.contrib.sessions",
      "django.contrib.messages",
      "django.contrib.staticfiles",
      "django_htmx",                  # Story 1.6
      "django_bootstrap5",            # Story 1.6
      "apps.core",                    # Story 1.x
      "apps.brands",                  # Story 2.1
      "apps.products",                # NOVO Story 2.2 — domain app (APENDOVAN POSLE apps.brands per dep rule)
  ]
  ```
  - **Diff je tačno JEDNA linija:** apenduj `"apps.products",` posle `"apps.brands",` — NEMOJ reordovati niti dirati postojeće linije. Task 1.4 (Edit operation, NE full file rewrite) prati ovaj invariant.
- **And** Django auto-reload startuje bez `ImportError`, `ImproperlyConfigured` ili `RuntimeError` (smoke verifikacija: `uv run python manage.py check` exit code 0).
- **And** `apps/products/__init__.py` je prazan — bez `default_app_config` declaracije (Django 3.2+ auto-detektuje `AppConfig` u `apps.py`).
- **And** `apps/products/tests.py` je obrisan (Django startapp generiše ovaj fajl, ali project-context.md § Test organization zahteva `tests/` direktorijum, NE `tests.py` fajl) — kreiran je `apps/products/tests/__init__.py` umesto.
- **And** **`config/settings/base.py` dobija `MODELTRANSLATION_FALLBACK_LANGUAGES = ("sr",)`** (C3 — eksplicitan locale fallback setting). **Rationale (IMP-iter4-1):** Ovo je **architecture-defensive** setting koji modeltranslation zahteva da bi imao deterministički fallback chain — bez njega, pristup translated polju bez aktivnog language context-a (npr. iz management command-a ili Celery task-a) može vratiti `None` umesto sr fallback vrednosti. Postavljanjem na `("sr",)` garantujemo da sve translated polja imaju sr kao canonical default (matches `LANGUAGE_CODE = "sr"` iz Story 1.4 + project-context.md § i18n locale fallback: "Locale fallback: sr je default; ako neki prevod nedostaje → fallback na sr"). **NIJE FR-32 mapiranje** — FR-32 je view-layer UX marker concern za Story 6.5; ovo je backend foundation koja Story 6.5 koristi. Postavlja se kao zasebna setting linija u istom bloku kao i `LANGUAGE_CODE` i `LANGUAGES` (Story 1.4 lokacija). Format:
  ```python
  # config/settings/base.py — dodaj posle LANGUAGES tuple-a
  MODELTRANSLATION_FALLBACK_LANGUAGES = ("sr",)  # Story 2.2 — architecture-defensive locale fallback chain
  ```

**AC2 — `Product` model definisan u `apps/products/models.py` nasleđuje `TimestampedModel` + `SluggedModel` iz `apps.core.models`; ima FK-ove ka Brand (PROTECT), Series (PROTECT, nullable), Subcategory (PROTECT); polja: `name`, `description`, `key_features` JSON (max 3), `main_image`, `year`, `price_eur`, `horse_power`, `condition`/`status` TextChoices, `is_published`; `Meta.indexes`, `get_absolute_url()`, `save()` sa auto-slug**

- **Given** `apps/products/models.py` postoji; `apps/core/models.py` ima `TimestampedModel` + `SluggedModel`; `apps/core/utils.py` ima `slugify_ascii()`
- **When** definišem `Product` klasu
- **Then** `Product` model mora imati TAČNO sledeća polja:
  - **Inheritance:** `class Product(SluggedModel, TimestampedModel):` — KRITIČNO redosled (SluggedModel pre TimestampedModel — Python MRO; oba su `abstract = True` pa se polja merguju). Ovaj inheritance pattern je **prvi konzument** Decision D3 iz 2.1 (consume foundation iz 2.2 kako je obećano).
  - `brand = models.ForeignKey("brands.Brand", on_delete=models.PROTECT, related_name="products", verbose_name=_("Brend"))` — KRITIČNO:
    - `on_delete=models.PROTECT` (brisanje brenda je blokirano ako ima proizvoda — business-critical content; matches arch.md § 478 Pattern Example)
    - `related_name="products"` (eksplicitno; `brand.products.all()` access pattern; sprečava `_set` magic per project-context.md § Django models)
    - `verbose_name=_("Brend")` (matches 2.1 Series.brand pattern — locale-aware admin label)
    - String reference `"brands.Brand"` (cross-app FK obavezno string lazy reference per Django convention — sprečava ciklične import-e na app loading time)
  - `series = models.ForeignKey("brands.Series", on_delete=models.PROTECT, related_name="products", null=True, blank=True, verbose_name=_("Serija"))` — KRITIČNO:
    - `null=True, blank=True` jer **nisu svi proizvodi vezani za seriju** (npr. Jeegee priključna mehanizacija nema "series" koncept — direktno ide pod Subcategory; HZM utovarivači imaju Subcategory ali ne uvek Series). Decision PR-D2 razrešava: Series je opcioni za Product.
    - `on_delete=models.PROTECT` — Series ne sme biti obrisana ako ima proizvoda
    - `related_name="products"`
    - `verbose_name=_("Serija")` (matches 2.1 pattern)
  - `subcategory = models.ForeignKey("brands.Subcategory", on_delete=models.PROTECT, related_name="products", null=True, blank=True, verbose_name=_("Potkategorija"))` — KRITIČNO:
    - `null=True, blank=True` jer **nisu svi proizvodi pod Subcategory** (npr. traktori top-tier idu pod Category "Traktori" bez Subcategory drill-down; samo mehanizacija ima dublji subtree). Decision PR-D3 razrešava: Subcategory je opcioni za Product.
    - `on_delete=models.PROTECT` — Subcategory ne sme biti obrisana ako ima proizvoda
    - `related_name="products"`
    - `verbose_name=_("Potkategorija")` (matches 2.1 pattern)
  - `name = models.CharField(_("Naziv"), max_length=200)` — **translatable** (registruje se u `translation.py` AC9)
  - `description = models.TextField(_("Opis"), blank=True)` — **translatable**
  - `key_features = models.JSONField(_("Ključne karakteristike"), default=list, blank=True)` — **translatable** (modeltranslation podržava JSON registraciju; lista do 3 string-a; renderuje se preko `Repeating Element`-a u hero overlay Story 2.7); validacija u `clean()` MORA pokrivati i base polje i SVE translated varijante (`key_features_sr`, `key_features_hu`, `key_features_en`) jer admin može upisati 5 stavki u `key_features_hu` bez ikakve provere ako se validacija primeni samo na base polje:
    ```python
    def clean(self) -> None:
        super().clean()
        # Validate base + all translated variants (sr/hu/en).
        # Admin može save-ovati key_features_hu sa 5 stavki — bez ovog loop-a
        # validacija bi prošla i bag bi se manifestovao tek u Story 2.7 render-u.
        # NOTE I-iter3-2: `settings.LANGUAGES` import dolazi iz Task 2.1 imports
        # header (`from django.conf import settings`) — NEMOJ duplikovati import
        # unutar metode; modul-level import je single source of truth.
        # NOTE I-iter2-6: `_label` umesto single `_` — `_` u modulu je već
        # `gettext_lazy as _`; loop unpacking u `_` bi shadow-ovao gettext_lazy
        # unutar loop body-ja i prebio `_("Mora biti lista.")` pozive ispod.
        # `# noqa: B007` suppress-uje ruff bugbear "unused loop variable" (ako enabled).
        for lang_code, _label in settings.LANGUAGES:  # noqa: B007
            attr = f"key_features_{lang_code}"
            value = getattr(self, attr, None) or []
            if value:
                if not isinstance(value, list):
                    raise ValidationError(
                        {attr: _("Mora biti lista.")}
                    )
                for item in value:
                    if not isinstance(item, str):
                        raise ValidationError(
                            {attr: _("Svaka stavka mora biti string.")}
                        )
                if len(value) > _PRODUCT_KEY_FEATURES_MAX:  # 3
                    raise ValidationError(
                        {attr: _("Najviše 3 ključne karakteristike.")}
                    )
        # Belt-and-suspenders: validate base accessor too — kovers programmatic set
        # bez language context-a (npr. raw .key_features = [...] u skripti).
        # Base polje (kada nije locale-aware kontekst):
        base_value = self.key_features or []
        if base_value:
            if not isinstance(base_value, list):
                raise ValidationError({"key_features": _("Mora biti lista.")})
            for item in base_value:
                if not isinstance(item, str):
                    raise ValidationError(
                        {"key_features": _("Svaka stavka mora biti string.")}
                    )
            if len(base_value) > _PRODUCT_KEY_FEATURES_MAX:
                raise ValidationError(
                    {"key_features": _("Najviše 3 ključne karakteristike.")}
                )
    ```
  - `main_image = models.ImageField(_("Glavna slika"), upload_to="products/main/", max_length=255, blank=True, null=True)` — **NE translatable**; MIME validacija deferred to Story 2.3 (Gotcha PR-3); `max_length=255` (per 2.1 IMP-4 pattern)
  - `year = models.PositiveSmallIntegerField(_("Godina"), blank=True, null=True)` — godina proizvodnje / godina modela; nullable jer nije obavezan za novokupljene proizvode
  - `price_eur = models.DecimalField(_("Cena (EUR)"), max_digits=10, decimal_places=2, blank=True, null=True)` — Decimal za precision (NE Float — finansijski podaci); `blank=True, null=True` jer cena može biti "Na upit" (FR-21); rendering format `€ XX.XXX` per project-context.md § Format patterns je view-layer concern (template tag)
  - `horse_power = models.PositiveSmallIntegerField(_("Konjska snaga"), blank=True, null=True)` — KS; nullable jer ne odnose se svi proizvodi (npr. priključci nemaju KS); rendering `XX KS` je view-layer
  - `condition` — `TextChoices` enum:
    ```python
    class ConditionChoice(models.TextChoices):
        NEW = "new", _("Novo")
        USED = "used", _("Polovno")

    condition = models.CharField(
        _("Stanje"),
        max_length=10,
        choices=ConditionChoice.choices,
        default=ConditionChoice.NEW,
        # NOTE I4: NEMA db_index=True — composite index `products_product_condition_pub_idx`
        # (Meta.indexes) pokriva leftmost-prefix scan na (condition, is_published).
        # Odvojen single-column index bio bi redundantan (Postgres B-tree leftmost rule).
    )
    ```
  - `status` — `TextChoices` enum (publication workflow):
    ```python
    class StatusChoice(models.TextChoices):
        DRAFT = "draft", _("Nacrt")
        PUBLISHED = "published", _("Objavljen")
        ARCHIVED = "archived", _("Arhiviran")

    # NOTE I4: status ZADRŽAVA db_index=True jer NIJE leftmost u nijednom composite
    # index-u (`products_product_brand_status_idx` ima brand kao leftmost, status drugi).
    # Filter `status=PUBLISHED` bez brand filtera ide brže kroz single-column index.
    status = models.CharField(
        _("Status"),
        max_length=12,
        choices=StatusChoice.choices,
        default=StatusChoice.DRAFT,
        db_index=True,
    )
    ```
  - `is_published = models.BooleanField(_("Objavljen"), default=False)` — koristi se za quick filter u listing view-ovima (Story 2.6/2.7/2.8/2.9); NAPOMENA: `is_published` i `status` su **paralelna polja** (Decision PR-D4 acknowledgment YAGNI tenzija) — epics.md spec eksplicitno traži oba (`is_published flag` + `status choice [draft/published/archived]`). Konvencija: `is_published=True` ↔ `status=PUBLISHED` (admin u Story 8.6 može sync-ovati ova polja kroz form `save()`; v1 ih ne sync-uje automatski). **NOTE I4: NEMA `db_index=True`** — composite index `products_product_pub_created_idx` ima `is_published` kao leftmost field, što pokriva sve `is_published=True` queries kroz leftmost-prefix rule. Odvojen single-column index bio bi redundantan. ⚠️ Dev: NEMOJ "helpfully" dodati `db_index=True` nazad.
  - `created_at`, `updated_at` (dolaze iz `TimestampedModel` mixin — NE redefinisati ih lokalno)
  - `slug` (dolazi iz `SluggedModel` mixin sa `unique=True, max_length=140, db_index=True` — NE redefinisati lokalno; Product slug je globalno unique per architecture.md § Pattern Examples line 477)
- **And** `Product` ima **Meta klasu**:
  ```python
  class Meta:
      ordering = ["-created_at"]
      verbose_name = _("Proizvod")
      verbose_name_plural = _("Proizvodi")
      indexes = [
          models.Index(
              fields=["is_published", "-created_at"],
              name="products_product_pub_created_idx",
          ),
          models.Index(
              fields=["brand", "status"],
              name="products_product_brand_status_idx",
          ),
          models.Index(
              fields=["condition", "is_published"],
              name="products_product_condition_pub_idx",
          ),
      ]
  ```
  - **`products_product_pub_created_idx`** — matches arch.md § 487 Pattern Example; pokriva default listing query "published + recent"
  - **`products_product_brand_status_idx`** — pokriva Brand listing 2.6 query "all products for brand by status"
  - **`products_product_condition_pub_idx`** — pokriva Used Listing 2.9 filter "condition=USED + is_published=True"
- **And** `Product.__str__` vraća:
  ```python
  def __str__(self) -> str:
      return f"{self.brand.name} — {self.name}"
  ```
  (em-dash separator per Series 2.1 konvencija)
- **And** `Product.get_absolute_url()` postoji i vraća:
  ```python
  def get_absolute_url(self) -> str:
      return reverse("products:detail", kwargs={"slug": self.slug})
  ```
  - **NAPOMENA:** URL `products:detail` JOŠ NE POSTOJI u Story 2.2 (urls.py je prazan startapp default). `reverse()` će raise-ovati `NoReverseMatch` ako se pozove pre Story 2.7. Test koristi `@pytest.mark.skip(reason="URLs come in Story 2.7")` pattern (kopija 2.1 Gotcha BR-4 prescribed pattern).
- **And** **`Product.save()` override** (matches 2.1 CRIT-2 iter-2 pattern — eksplicitan order slug auto-gen → full_clean → super().save):
  ```python
  def save(self, *args, **kwargs):
      """Auto-generate slug iz name + full_clean() (matches Story 2.1 CRIT-2 pattern).

      ⚠️ NE refaktoriši — duplikacija slug auto-gen logike sa full_clean() override-om
      je NAMERNA (I5). Story 2.1 Pattern A defensive guard: caller može pozvati
      full_clean() na unsaved instance bez slug-a i validacija će proći; save() path
      remains single source of truth za slug auto-gen pri DB persist-u.
      Tests u AC13 verify oba puta nezavisno.
      """
      if not self.slug and self.name:
          self.slug = slugify_ascii(self.name)
      self.full_clean()
      super().save(*args, **kwargs)
  ```
- **And** **`Product.full_clean()` override** (matches 2.1 pattern — auto-gen slug PRE Django field-level validation za defensive behavior u testovima):
  ```python
  def full_clean(self, *args, **kwargs):
      """Auto-generate slug iz name PRE Django field-level validation.

      ⚠️ NIKAD ne pozivaj self.clean() direktno iz ovog override-a (I10) —
      super().full_clean(*args, **kwargs) već automatski poziva self.clean()
      kao deo svog standardnog flow-a. Double-poziv → duplikacija validation
      errors i potencijalno duplikat ValidationError dict-ova u test asercijama.
      """
      if not self.slug and self.name:
          self.slug = slugify_ascii(self.name)
      super().full_clean(*args, **kwargs)
  ```
- **And** **`Product.clean()`** validira `key_features` JSON shape (list-of-str + max 3) per gore navedeni snippet.

**AC3 — `ProductImage` model: FK Product (`CASCADE`, `related_name="images"`), `image`, `order`, `alt_text` (translatable)**

- **Given** `Product` definisan u `apps/products/models.py`
- **When** definišem `ProductImage` klasu
- **Then** `ProductImage` model mora imati TAČNO sledeća polja:
  - **Inheritance:** `class ProductImage(TimestampedModel):` (samo TimestampedModel — nema slug, nije content entity sa URL-om)
  - `product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images", verbose_name=_("Proizvod"))` — KRITIČNO:
    - `on_delete=models.CASCADE` — brisanje proizvoda briše sve slike (child entitet, nema independent existence)
    - `related_name="images"` (eksplicitno; `product.images.all()` access pattern)
    - `verbose_name=_("Proizvod")` (matches 2.1 FK verbose_name pattern)
    - Direktan import-by-name `Product` (NE string) — isti app, no ciklični risk
  - `image = models.ImageField(_("Slika"), upload_to="products/gallery/", max_length=255)` — REQUIRED (galerija ne sme imati prazne entry-je); MIME validacija deferred to Story 2.3
  - `order = models.PositiveSmallIntegerField(_("Redosled"), default=0, db_index=True)` — manual order u admin inline; lower = earlier
  - `alt_text = models.CharField(_("Alt tekst"), max_length=200, blank=True)` — **translatable** (a11y must-have per project-context.md § A11y must-haves: "Alt text na svim slikama")
- **And** `ProductImage.Meta`:
  ```python
  class Meta:
      ordering = ["order", "id"]
      verbose_name = _("Slika proizvoda")
      verbose_name_plural = _("Slike proizvoda")
      indexes = [
          models.Index(
              fields=["product", "order"],
              name="products_image_product_order_idx",
          ),
      ]
  ```
- **And** `ProductImage.__str__` vraća `f"{self.product.name} — slika {self.order}"`.
- **And** **NEMA** `get_absolute_url()` — ProductImage je child entitet bez nezavisne strane.

**AC4 — `ProductVariant` model: FK Product (`CASCADE`, `related_name="variants"`), `name` (translatable), `code`, `image`, `description` (translatable), `order`**

- **Given** `Product` definisan
- **When** definišem `ProductVariant` klasu
- **Then** `ProductVariant` model mora imati TAČNO sledeća polja:
  - **Inheritance:** `class ProductVariant(TimestampedModel):`
  - `product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants", verbose_name=_("Proizvod"))` — CASCADE; related_name="variants"; verbose_name="Proizvod" (matches 2.1 FK verbose_name pattern)
  - `name = models.CharField(_("Naziv"), max_length=200)` — **translatable** (npr. "Sa kabinom", "Bez kabine")
  - `code = models.CharField(_("Kod"), max_length=50, blank=True)` — **NE translatable** (interni kod, sku-style npr. "TB804-CAB"); ne mora biti unique (variant codes su per-product scope, ne globalno)
  - `image = models.ImageField(_("Slika varijante"), upload_to="products/variants/", max_length=255, blank=True, null=True)` — opciono; MIME validacija deferred to 2.3
  - `description = models.TextField(_("Opis"), blank=True)` — **translatable**
  - `order = models.PositiveSmallIntegerField(_("Redosled"), default=0, db_index=True)`
- **And** `ProductVariant.Meta`:
  ```python
  class Meta:
      ordering = ["order", "id"]
      verbose_name = _("Varijanta")
      verbose_name_plural = _("Varijante")
      indexes = [
          models.Index(
              fields=["product", "order"],
              name="products_variant_product_order_idx",
          ),
      ]
  ```
- **And** `ProductVariant.__str__` vraća `self.name` (locale-aware kroz modeltranslation fallback).

**AC5 — `ProductSpecification` model: FK Product (`CASCADE`, `related_name="specifications"`), `section` TextChoices [Motor/Transmisija/Hidraulika/Ostalo], `key` (translatable), `value` (translatable), `order`**

- **Given** `Product` definisan
- **When** definišem `ProductSpecification` klasu
- **Then** `ProductSpecification` model mora imati TAČNO sledeća polja:
  - **Inheritance:** `class ProductSpecification(TimestampedModel):`
  - `product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="specifications", verbose_name=_("Proizvod"))` — CASCADE; related_name="specifications" (NE "specs" — eksplicitno, čitljivije u QuerySet kodu); verbose_name="Proizvod"
  - `section` — `TextChoices` enum (sekcije akordiona u Story 2.7 Product Detail):
    ```python
    class SpecSection(models.TextChoices):
        MOTOR = "motor", _("Motor")
        TRANSMISIJA = "transmisija", _("Transmisija")
        HIDRAULIKA = "hidraulika", _("Hidraulika")
        OSTALO = "ostalo", _("Ostalo")

    section = models.CharField(
        _("Sekcija"),
        max_length=20,
        choices=SpecSection.choices,
        default=SpecSection.OSTALO,
        db_index=True,
    )
    ```
  - `key = models.CharField(_("Naziv specifikacije"), max_length=200)` — **translatable** (npr. "Snaga motora", "Broj cilindara")
  - `value = models.CharField(_("Vrednost"), max_length=200)` — **translatable** (npr. "80 KS", "4")
  - `order = models.PositiveSmallIntegerField(_("Redosled"), default=0, db_index=True)`
- **And** `ProductSpecification.Meta`:
  ```python
  class Meta:
      # NOTE I3: NE uključuj "section" u ordering — alphabetical sort daje
      # hidraulika → motor → ostalo → transmisija što je SUPROTNO traženom
      # display order-u (Motor → Transmisija → Hidraulika → Ostalo).
      # Display order će biti primenjen u Story 2.7 view-layer kroz Case/When
      # annotation (npr. Case(When(section="motor", then=1), When(section="transmisija", then=2), ...)).
      # Default ordering ovde je samo za stabilan iter unutar iste section.
      ordering = ["product", "order", "id"]
      verbose_name = _("Specifikacija")
      verbose_name_plural = _("Specifikacije")
      indexes = [
          models.Index(
              fields=["product", "section", "order"],
              name="products_spec_product_section_idx",
          ),
      ]
  ```
- **And** `ProductSpecification.__str__` vraća `f"{self.get_section_display()}: {self.key} = {self.value}"`.

**AC6 — `ProductBrochure` model: FK Product (`CASCADE`, `related_name="brochures"`), `pdf_file`, `cover_thumbnail_image`, `title` (translatable)**

- **Given** `Product` definisan
- **When** definišem `ProductBrochure` klasu
- **Then** `ProductBrochure` model mora imati TAČNO sledeća polja:
  - **Inheritance:** `class ProductBrochure(TimestampedModel):`
  - `product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="brochures", verbose_name=_("Proizvod"))` — CASCADE; related_name="brochures"; verbose_name="Proizvod"
  - `pdf_file = models.FileField(_("PDF brošura"), upload_to="products/brochures/", max_length=255)` — REQUIRED; MIME validacija deferred to Story 2.4 (Gotcha PR-4)
  - `cover_thumbnail_image = models.ImageField(_("Cover thumbnail"), upload_to="products/brochure_covers/", max_length=255, blank=True, null=True)` — **AUTO-GENERATED u Story 2.4** kroz `post_save` signal koji koristi `pdf2image`; u Story 2.2 ostaje prazno (admin može manuelno upload-ovati, ali 2.4 ga prebriše automacijom). `blank=True, null=True` jer 2.2 ne implementira signal — admin može save-ovati Brochure bez cover, kasnije Story 2.4 backfill-uje kroz signal pri svakom novom save-u.
  - `title = models.CharField(_("Naslov brošure"), max_length=200, blank=True)` — **translatable** (npr. "Tehnička specifikacija", "Marketing brošura")
- **And** `ProductBrochure.Meta`:
  ```python
  class Meta:
      ordering = ["product", "id"]
      verbose_name = _("Brošura")
      verbose_name_plural = _("Brošure")
      indexes = [
          models.Index(
              fields=["product"],
              name="products_brochure_product_idx",
          ),
      ]
  ```
- **And** `ProductBrochure.__str__` vraća lokalizovan fallback (I-iter3-6 — fallback string MORA biti `gettext_lazy` wrapped per project-context.md § Anti-pattern: Hardcoded user-facing string):
  ```python
  def __str__(self) -> str:
      if self.title:
          return self.title
      # NOTE I-iter3-6: fallback string OBAVEZNO kroz `gettext_lazy` (`_` iz Task 2.1 imports
      # header). `f""` formatting bi eager-evaluovao lazy string i izgubio locale awareness;
      # printf-style `% {name: ...}` format je idiomatski pattern za gettext_lazy interpolaciju.
      # Reference: project-context.md § Anti-pattern: Hardcoded user-facing string.
      # Story 2.1 Series.__str__ koristi format bez label-a (`f"{self.brand.name} — {self.name}"`)
      # pa nije precedent za hardcoded label fallback — ovde label JE potreban (title je opcioni),
      # zato gettext_lazy.
      return _("Brošura — %(name)s") % {"name": self.product.name}
  ```

**AC7 — `ProductTestimonial` model: FK Product (`CASCADE`, `related_name="testimonials"`), `photo`, `quote` (translatable), `author_name`, `location` (translatable), `order`**

- **Given** `Product` definisan
- **When** definišem `ProductTestimonial` klasu
- **Then** `ProductTestimonial` model mora imati TAČNO sledeća polja:
  - **Inheritance:** `class ProductTestimonial(TimestampedModel):`
  - `product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="testimonials", verbose_name=_("Proizvod"))` — CASCADE; related_name="testimonials"; verbose_name="Proizvod"
  - `photo = models.ImageField(_("Fotografija"), upload_to="products/testimonials/", max_length=255, blank=True, null=True)` — opciono; MIME validacija deferred to 2.3
  - `quote = models.TextField(_("Citat"))` — **translatable**; REQUIRED (testimonijal bez citata je besmislen)
  - `author_name = models.CharField(_("Ime autora"), max_length=120)` — **NE translatable** (lično ime se ne prevodi)
  - `location = models.CharField(_("Lokacija"), max_length=120, blank=True)` — **translatable** (npr. "Vojvodina, Srbija" / "Vajdaság, Szerbia" — region može biti lokalizovan)
  - `order = models.PositiveSmallIntegerField(_("Redosled"), default=0, db_index=True)`
- **And** `ProductTestimonial.Meta`:
  ```python
  class Meta:
      ordering = ["order", "id"]
      verbose_name = _("Testimonijal")
      verbose_name_plural = _("Testimonijali")
      indexes = [
          models.Index(
              fields=["product", "order"],
              name="products_testimonial_product_order_idx",
          ),
      ]
  ```
- **And** `ProductTestimonial.__str__` vraća `f"{self.author_name} — {self.product.name}"`.

**AC8 — `ProductSimilar` model: FK Product (`CASCADE`, `related_name="outgoing_similars"`), FK related_Product (`CASCADE`, `related_name="incoming_similars"`), `order` — manual override za FR-20 hibrid logiku**

- **Given** `Product` definisan
- **When** definišem `ProductSimilar` klasu
- **Then** `ProductSimilar` model mora imati TAČNO sledeća polja:
  - **Inheritance:** `class ProductSimilar(TimestampedModel):` (čisto relacioni — nema translatable polja, nije konzument `translation.py`)
  - `product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="outgoing_similars", verbose_name=_("Proizvod"))` — **KRITIČNO related_name**: `outgoing_similars` znači "skup similar entry-ja KOJI POLAZE OD ovog proizvoda" (proizvod je izvor relacije; vidi Decision PR-D5 za semantiku); verbose_name="Proizvod".
  - `related_product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="incoming_similars", verbose_name=_("Sličan proizvod"))` — **KRITIČNO related_name**: `incoming_similars` znači "skup similar entry-ja KOJI POKAZUJU NA ovog proizvoda" (proizvod je meta relacije; vidi Decision PR-D5). Decision PR-D5 razrešava: relacija je **directional** (NE simetrična automatski) — ako admin u Story 8.6 hoće simetriju, mora kreirati DVA entry-ja (A→B i B→A); ovo je svesno design choice jer FR-20 dozvoljava asimetrične preporuke (npr. "uz traktor TB804 preporuči priključke", ali ne obrnuto). verbose_name="Sličan proizvod".
  - `order = models.PositiveSmallIntegerField(_("Redosled"), default=0, db_index=True)` — order u similar sekciji na Product Detail strani
- **And** `ProductSimilar.Meta`:
  ```python
  class Meta:
      ordering = ["product", "order", "id"]
      verbose_name = _("Sličan proizvod")
      verbose_name_plural = _("Slični proizvodi")
      constraints = [
          models.UniqueConstraint(
              fields=["product", "related_product"],
              name="products_similar_pair_unique",
          ),
          # CHECK constraint: product ne sme biti related_product (no self-reference)
          models.CheckConstraint(
              check=~models.Q(product=models.F("related_product")),
              name="products_similar_no_self_reference",
          ),
      ]
      indexes = [
          models.Index(
              fields=["product", "order"],
              name="products_similar_product_order_idx",
          ),
      ]
  ```
- **And** `ProductSimilar.__str__` vraća `f"{self.product.name} → {self.related_product.name}"`.
- **And** **`ProductSimilar.clean()` validira no-self-reference** (defensive — DB CHECK constraint je primarno, ali clean() raise-uje friendly poruku u admin formu):
  ```python
  def clean(self) -> None:
      super().clean()
      if self.product_id is not None and self.related_product_id is not None:
          if self.product_id == self.related_product_id:
              raise ValidationError(
                  _("Sličan proizvod ne sme biti isti kao izvorni proizvod.")
              )
  # NEMA save() override — clean() se poziva SAMO eksplicitno (full_clean())
  # ili kroz admin form save_model(); .objects.create() ili .save() BYPASS-uje
  # clean() i DB-level CheckConstraint je jedina garancija. Vidi Dev Note
  # "ProductSimilar save() bez full_clean() — dva test path-a" (IMP-iter4-4).
  ```
- **And** **NEMA** `get_absolute_url()` — ProductSimilar je junction entity bez nezavisne strane.

**AC9 — `apps/products/translation.py` registruje `TranslationOptions` za translatable polja na 6 od 7 modela (ProductSimilar NEMA translatable polja); modeltranslation auto-discovery generiše `_sr`/`_hu`/`_en` suffix kolone**

- **Given** `apps/products/models.py` definisan (AC2-AC8); modeltranslation registrovan u INSTALLED_APPS u Story 2.1
- **When** kreiram `apps/products/translation.py`
- **Then** fajl mora sadržati TAČNO sledeće registracije (per modeltranslation API):
  ```python
  from modeltranslation.translator import TranslationOptions, register

  from apps.products.models import (
      Product,
      ProductBrochure,
      ProductImage,
      ProductSpecification,
      ProductTestimonial,
      ProductVariant,
  )


  @register(Product)
  class ProductTranslationOptions(TranslationOptions):
      fields = ("name", "description", "key_features")


  @register(ProductImage)
  class ProductImageTranslationOptions(TranslationOptions):
      fields = ("alt_text",)


  @register(ProductVariant)
  class ProductVariantTranslationOptions(TranslationOptions):
      fields = ("name", "description")


  @register(ProductSpecification)
  class ProductSpecificationTranslationOptions(TranslationOptions):
      fields = ("key", "value")


  @register(ProductBrochure)
  class ProductBrochureTranslationOptions(TranslationOptions):
      fields = ("title",)


  @register(ProductTestimonial)
  class ProductTestimonialTranslationOptions(TranslationOptions):
      fields = ("quote", "location")
  ```
- **And** **`ProductSimilar` NIJE registrovan** u translation.py (nema translatable polja — `product`, `related_product`, `order` su sva untranslatable).
- **And** modeltranslation pri startup-u skenira `INSTALLED_APPS` i učitava `apps/products/translation.py` automatski (hook već postoji iz Story 2.1; nikakav dodatan config).
- **And** registracije generišu virtuelna polja:
  - `Product._meta.get_fields()` sadrži: `name_sr`, `name_hu`, `name_en`, `description_sr`/`_hu`/`_en`, `key_features_sr`/`_hu`/`_en`
  - `ProductImage`: `alt_text_sr`/`_hu`/`_en`
  - `ProductVariant`: `name_sr`/`_hu`/`_en`, `description_sr`/`_hu`/`_en`
  - `ProductSpecification`: `key_sr`/`_hu`/`_en`, `value_sr`/`_hu`/`_en`
  - `ProductBrochure`: `title_sr`/`_hu`/`_en`
  - `ProductTestimonial`: `quote_sr`/`_hu`/`_en`, `location_sr`/`_hu`/`_en`
- **And** `apps/products/translation.py` koristi **apsolutni import** `from apps.products.models import ...` (per Story 2.1 pattern — relativni `from .models` je dozvoljen u istom app-u per project-context.md § Imports, ali 2.1 je biralo apsolutne za eksplicitnost; 2.2 prati istu konvenciju), NE relativni `from .models`.

**AC10 — Migracija `apps/products/migrations/0001_initial.py` je MANUAL-REVIEWED i kreira 7 tabela sa svim `_sr`/`_hu`/`_en` suffix kolonama, eksplicitnim FK on_delete-ima, UniqueConstraint + CheckConstraint na ProductSimilar**

- **Given** modeli definisani (AC2-AC8), translation.py registrovan (AC9), modeltranslation u INSTALLED_APPS pre apps.products
- **When** pokrenem `uv run python manage.py makemigrations products`
- **Then** sledeće mora biti tačno:
  - **Migracija fajl postoji:** `apps/products/migrations/0001_initial.py` (Django auto-imenuje "initial")
  - **MANUAL REVIEW pre commit-a** (per project-context.md § Migrations discipline):
    - `products_product` tabela sa kolonama: `id`, `slug` (iz SluggedModel), `created_at`/`updated_at` (iz TimestampedModel), `brand_id` (FK), `series_id` (FK nullable), `subcategory_id` (FK nullable), `name`, `name_sr`/`_hu`/`_en`, `description`, `description_sr`/`_hu`/`_en`, `key_features`, `key_features_sr`/`_hu`/`_en`, `main_image`, `year`, `price_eur`, `horse_power`, `condition`, `status`, `is_published`
    - `products_productimage` tabela: `id`, `created_at`/`updated_at`, `product_id`, `image`, `order`, `alt_text`, `alt_text_sr`/`_hu`/`_en`
    - `products_productvariant` tabela: `id`, `created_at`/`updated_at`, `product_id`, `name`, `name_sr`/`_hu`/`_en`, `code`, `image`, `description`, `description_sr`/`_hu`/`_en`, `order`
    - `products_productspecification` tabela: `id`, `created_at`/`updated_at`, `product_id`, `section`, `key`, `key_sr`/`_hu`/`_en`, `value`, `value_sr`/`_hu`/`_en`, `order`
    - `products_productbrochure` tabela: `id`, `created_at`/`updated_at`, `product_id`, `pdf_file`, `cover_thumbnail_image`, `title`, `title_sr`/`_hu`/`_en`
    - `products_producttestimonial` tabela: `id`, `created_at`/`updated_at`, `product_id`, `photo`, `quote`, `quote_sr`/`_hu`/`_en`, `author_name`, `location`, `location_sr`/`_hu`/`_en`, `order`
    - `products_productsimilar` tabela: `id`, `created_at`/`updated_at`, `product_id`, `related_product_id`, `order`
  - **AddIndex operacije** za sve composite indexes definisane u `Meta.indexes` (AC2-AC8)
  - **AddConstraint operacije**:
    - `products_similar_pair_unique` (UniqueConstraint na ProductSimilar)
    - `products_similar_no_self_reference` (CheckConstraint na ProductSimilar)
  - **FK on_delete eksplicitni:**
    - PROTECT na Product.brand, Product.series, Product.subcategory
    - CASCADE na ProductImage.product, ProductVariant.product, ProductSpecification.product, ProductBrochure.product, ProductTestimonial.product, ProductSimilar.product, ProductSimilar.related_product
  - **NAPOMENA backend-agnostic (per 2.1 CRIT-4):** `models.JSONField` i `models.DecimalField` su materijalizovani strukturalno; CI test env koristi SQLite (per Story 1.9). Postgres-specific verifikacije (jsonb tip) stižu u Story 9.1 production deploy.
- **And** pokretanje `uv run python manage.py migrate products` exit code 0 — kreira sve 7 tabela u SQLite (dev DB).
- **And** **post-migration verifikacija kroz Django shell** (manual smoke test):
  ```python
  from apps.products.models import Product, ProductImage, ProductVariant, ProductSpecification, ProductBrochure, ProductTestimonial, ProductSimilar
  # Verify all 7 tables exist
  assert Product.objects.count() == 0
  assert ProductImage.objects.count() == 0
  assert ProductVariant.objects.count() == 0
  assert ProductSpecification.objects.count() == 0
  assert ProductBrochure.objects.count() == 0
  assert ProductTestimonial.objects.count() == 0
  assert ProductSimilar.objects.count() == 0
  # Verify translation fields registered on Product
  field_names = {f.name for f in Product._meta.get_fields()}
  assert "name_sr" in field_names
  assert "description_sr" in field_names
  assert "key_features_sr" in field_names
  ```
- **And** **NIJEDNA druga migracija** ne sme biti generisana u Story 2.2 scope-u (samo `apps/products/migrations/0001_initial.py`). Ako modeltranslation generiše dodatnu migraciju za drugi app, vidi Gotcha PR-2 za handling.
- **And** **Manual review checklist (Task 5 — konkretni koraci; PowerShell ekvivalenti — Windows shell je SOT za projekat):**
  ```
  > **Shell (I-iter3-3):** Sve komande ispod pretpostavljaju PowerShell 5.1+ na Windows-u.
  > Ako koristiš Git Bash / WSL, pokreni preko `pwsh -Command "<cmd>"` ili zameni
  > `Select-String -Pattern '<P>'` sa `grep -E '<P>'` (i `Measure-Object` sa `wc -l`).
  > Verifikuj shell sa `$PSVersionTable.PSVersion` (PowerShell) ili `echo $SHELL` (bash).

  NOTE: Komande su PowerShell. Git Bash / WSL korisnici mogu koristiti `grep` + `wc -l`
  ekvivalente; PowerShell `Select-String` + `Measure-Object` koristi se zato što je
  Windows + PowerShell potvrđeni shell za projekat (videti `New-Item -ItemType` i
  `$env:TEMP` upotrebu na drugim mestima).

  1. Select-String -Path apps/products/migrations/0001_initial.py -Pattern 'on_delete'
     - EXPECTED: PROTECT na Product.brand, Product.series, Product.subcategory
     - EXPECTED: CASCADE na sve child FK-ove (Image, Variant, Spec, Brochure, Testimonial, Similar.product, Similar.related_product)
  2. PER-FIELD translation kolona check (I7 — precizniji od threshold count-a):

     > **CRIT-iter5-1 NAPOMENA (regex pattern):** Patterns koriste `['"]name_sr['"]` — match-uje BILO koji navodnik (single ili double) jer Django default emit-uje single quotes (`'name_sr'`), ali ručno editovan migration može imati double quotes. **NE koristi `^\s*\(` anchor** — Django emit-uje multi-line tuple format gde `(` i field-name stoje na ODVOJENIM linijama (verifikovano empirijski protiv `apps/brands/migrations/0001_initial.py` — anchor pattern vraća 0 match-eva). Pattern ispod broji svaku liniju koja sadrži `'name_sr'` ili `"name_sr"` bez obzira na kontekst (CreateModel tuple ili AddIndex reference). **EXPECTED count-ovi ispod su MINIMUM (≥)** jer modeltranslation `patch_indexes` može emit-ovati dodatne reference u AddIndex operacijama (vidi brands migration: `name_sr` se javlja 5x — 1x CreateModel + 4x indexes). Counts ispod izračunate su konzervativno za CreateModel tuple kao floor.
     >
     > **Empirical verifikacija (Story 2.2 SM):** Protiv `apps/brands/migrations/0001_initial.py`:
     > - OLD broken `^\s*\("name_sr"` → 0 (silently fail)
     > - NEW `['"]name_sr['"]` → 5 (CreateModel + AddIndex references)

     - (Select-String -Path apps/products/migrations/0001_initial.py -Pattern "['""]name_sr['""]").Count → EXPECTED ≥ 2 (Product i ProductVariant oba imaju translatable `name`/`description` polja — vidi AC9 / AC4)
     - (Select-String -Path apps/products/migrations/0001_initial.py -Pattern "['""]name_hu['""]").Count → EXPECTED ≥ 2 (Product + ProductVariant; vidi AC9 / AC4)
     - (Select-String -Path apps/products/migrations/0001_initial.py -Pattern "['""]name_en['""]").Count → EXPECTED ≥ 2 (Product + ProductVariant; vidi AC9 / AC4)
     - (Select-String -Path apps/products/migrations/0001_initial.py -Pattern "['""]description_sr['""]").Count → EXPECTED ≥ 2 (Product + ProductVariant — oba imaju translatable `description`; vidi AC9 / AC4)
     - (Select-String -Path apps/products/migrations/0001_initial.py -Pattern "['""]description_hu['""]").Count → EXPECTED ≥ 2
     - (Select-String -Path apps/products/migrations/0001_initial.py -Pattern "['""]description_en['""]").Count → EXPECTED ≥ 2
     - (Select-String -Path apps/products/migrations/0001_initial.py -Pattern "['""]key_features_sr['""]").Count → EXPECTED ≥ 1 (samo Product ima translatable key_features)
     - (Select-String -Path apps/products/migrations/0001_initial.py -Pattern "['""]key_features_hu['""]").Count → EXPECTED ≥ 1
     - (Select-String -Path apps/products/migrations/0001_initial.py -Pattern "['""]key_features_en['""]").Count → EXPECTED ≥ 1
     - (Select-String -Path apps/products/migrations/0001_initial.py -Pattern "['""]alt_text_sr['""]").Count → EXPECTED ≥ 1 (samo ProductImage)
     - (Select-String -Path apps/products/migrations/0001_initial.py -Pattern "['""]alt_text_hu['""]").Count → EXPECTED ≥ 1
     - (Select-String -Path apps/products/migrations/0001_initial.py -Pattern "['""]alt_text_en['""]").Count → EXPECTED ≥ 1
     - (Select-String -Path apps/products/migrations/0001_initial.py -Pattern "['""]key_sr['""]").Count → EXPECTED ≥ 1 (samo ProductSpecification)
     - (Select-String -Path apps/products/migrations/0001_initial.py -Pattern "['""]key_hu['""]").Count → EXPECTED ≥ 1
     - (Select-String -Path apps/products/migrations/0001_initial.py -Pattern "['""]key_en['""]").Count → EXPECTED ≥ 1
     - (Select-String -Path apps/products/migrations/0001_initial.py -Pattern "['""]value_sr['""]").Count → EXPECTED ≥ 1 (samo ProductSpecification)
     - (Select-String -Path apps/products/migrations/0001_initial.py -Pattern "['""]value_hu['""]").Count → EXPECTED ≥ 1
     - (Select-String -Path apps/products/migrations/0001_initial.py -Pattern "['""]value_en['""]").Count → EXPECTED ≥ 1
     - (Select-String -Path apps/products/migrations/0001_initial.py -Pattern "['""]title_sr['""]").Count → EXPECTED ≥ 1 (samo ProductBrochure)
     - (Select-String -Path apps/products/migrations/0001_initial.py -Pattern "['""]title_hu['""]").Count → EXPECTED ≥ 1
     - (Select-String -Path apps/products/migrations/0001_initial.py -Pattern "['""]title_en['""]").Count → EXPECTED ≥ 1
     - (Select-String -Path apps/products/migrations/0001_initial.py -Pattern "['""]quote_sr['""]").Count → EXPECTED ≥ 1 (samo ProductTestimonial)
     - (Select-String -Path apps/products/migrations/0001_initial.py -Pattern "['""]quote_hu['""]").Count → EXPECTED ≥ 1
     - (Select-String -Path apps/products/migrations/0001_initial.py -Pattern "['""]quote_en['""]").Count → EXPECTED ≥ 1
     - (Select-String -Path apps/products/migrations/0001_initial.py -Pattern "['""]location_sr['""]").Count → EXPECTED ≥ 1 (samo ProductTestimonial)
     - (Select-String -Path apps/products/migrations/0001_initial.py -Pattern "['""]location_hu['""]").Count → EXPECTED ≥ 1
     - (Select-String -Path apps/products/migrations/0001_initial.py -Pattern "['""]location_en['""]").Count → EXPECTED ≥ 1
     - **Aggregate sanity floor (IMP-iter5-3):** (Select-String -Path apps/products/migrations/0001_initial.py -Pattern "['""][a-z_]+_(sr|hu|en)['""]").Count
       - EXPECTED: ≥ 33 (11 translatable polja × 3 jezika = 33 CreateModel tuple entries minimum, plus dodatne AddIndex reference koje modeltranslation može emit-ovati). Pattern matchuje SAMO field-declaration linije (`'fieldname_sr'` style sa quoted boundaries), izbegava false-positives na `name_serijski` ili sličnim non-suffix occurrences.
       - **Aggregate je samo loose floor — per-field count-ovi (step 2 iznad) su rigorozna verifikacija. Aggregate floor failure indikuje totalno odsustvo translation kolona; aggregate pass NIJE garancija ispravnosti** — admin može imati 33+ match-eva ali da i dalje fali konkretno polje (npr. `quote_hu`). Uvek combine sa per-field checks.
  3. Select-String -Path apps/products/migrations/0001_initial.py -Pattern 'JSONField'
     - EXPECTED: models.JSONField na Product.key_features (NE column literal jsonb — backend-agnostic per 2.1 CRIT-4)
  4. Select-String -Path apps/products/migrations/0001_initial.py -Pattern 'DecimalField'
     - EXPECTED: models.DecimalField(max_digits=10, decimal_places=2) na Product.price_eur
  5. Select-String -Path apps/products/migrations/0001_initial.py -Pattern 'UniqueConstraint|CheckConstraint'
     - EXPECTED: products_similar_pair_unique (UniqueConstraint)
     - EXPECTED: products_similar_no_self_reference (CheckConstraint)
  6. (Select-String -Path apps/products/migrations/0001_initial.py -Pattern 'AddIndex' | Measure-Object).Count
     - EXPECTED: ≥ 8 (3 indexes on Product + 1 each on Image/Variant/Spec/Brochure/Testimonial/Similar)
  7. PROTECT/CASCADE explicit counts:
     - (Select-String -Path apps/products/migrations/0001_initial.py -Pattern 'PROTECT').Count → EXPECTED 3 (Product.brand, .series, .subcategory)
     - (Select-String -Path apps/products/migrations/0001_initial.py -Pattern 'CASCADE').Count → EXPECTED 7 (Image, Variant, Spec, Brochure, Testimonial, Similar.product, Similar.related_product)
  8. uv run python manage.py migrate --plan --dry-run
     - EXPECTED: shows 0001_initial.py with 7 CreateModel + AddField (translation fields) + AddIndex + AddConstraint
  9. After migrate, run: uv run python manage.py inspectdb products_product products_productimage products_productvariant products_productspecification products_productbrochure products_producttestimonial products_productsimilar > "$env:TEMP\inspectdb_2_2.txt"
     - EXPECTED: 7 tabele sa _sr/_hu/_en kolonama na translatable poljima
  ```

**AC11 — `apps/products/admin.py` ima stub registracije za svih 7 modela kroz bare `admin.site.register(...)` (mirror 2.1 pattern; modeltranslation tabovi se NE renderuju u stub admin formi — pun `TranslationAdmin` u Story 8.6)**

- **Given** modeli definisani, migracija primenjena
- **When** otvorim Django admin (`/admin/`) sa superuser-om
- **Then** `apps/products/admin.py` sadrži MINIMUM (mirror 2.1 pattern — verifikovano kroz `apps/brands/admin.py`):
  ```python
  from django.contrib import admin

  from apps.products.models import (
      Product,
      ProductBrochure,
      ProductImage,
      ProductSimilar,
      ProductSpecification,
      ProductTestimonial,
      ProductVariant,
  )

  admin.site.register(Product)
  admin.site.register(ProductImage)
  admin.site.register(ProductVariant)
  admin.site.register(ProductSpecification)
  admin.site.register(ProductBrochure)
  admin.site.register(ProductTestimonial)
  admin.site.register(ProductSimilar)
  ```
- **And** admin index strana prikazuje "Proizvodi" sekciju sa 7 model linka.
- **And** klik na "Proizvodi" otvara default ModelAdmin list view — **modeltranslation tabovi (sr/hu/en) se NE renderuju** u stub admin formi sa bare `admin.site.register()`. Umesto toga, admin form prikazuje flat fields (npr. `name`, `name_sr`, `name_hu`, `name_en` kao 4 odvojena CharField-a). Ovo je IDENTIČNO 2.1 pattern-u (verifikovano kroz `apps/brands/admin.py` — bare register, no `TranslationAdmin` base klasa). Pun `TranslationAdmin` stub sa pravim sr/hu/en tabovima dolazi u **Story 8.6 (Product CRUD admin)** zajedno sa galerija inline, specs editor, varijante inline, brošure inline, testimonijali inline, similar manual override widget. Vidi Gotcha PR-11 za detaljan trap explanation.
- **And** **NEMA `list_display`, `list_filter`, `search_fields`, `prepopulated_fields`, `inlines`, `TranslationAdmin` base klasa** u Story 2.2 — sve to je **Story 8.6 (Product CRUD admin sa multi-locale)** scope.

**AC12 — App boundary regression: `apps/brands/` ostaje netaknut (no import ka apps.products); `apps/products/` koristi samo apsolutne import-e iz `apps.brands` + `apps.core`; CI lint pass**

- **Given** Story 2.2 implementacija završena
- **When** grep / static check
- **Then** sledeće mora biti tačno:
  - **`apps/brands/` ZERO import-a iz `apps.products`** (verifikacija: `grep -rn "apps.products" apps/brands/ tests/` mora vratiti 0 linija). Per architecture.md § Zabranjene zavisnosti: "brands NIKAD ne sme importovati products (jednosmerna)".
  - **`apps/products/models.py` koristi string lazy FK reference za cross-app FK-ove:**
    - `models.ForeignKey("brands.Brand", ...)` — NE direktan `from apps.brands.models import Brand`
    - `models.ForeignKey("brands.Series", ...)` — string reference
    - `models.ForeignKey("brands.Subcategory", ...)` — string reference
    - **Rationale:** Lazy string reference sprečava cycle import na app loading time; matches arch.md § 478 Pattern Example
  - **`apps/products/models.py` koristi apsolutni import za in-app FK reference:**
    - `models.ForeignKey(Product, ...)` u ProductImage/Variant/Spec/Brochure/Testimonial/Similar — direktan name reference (isti modul)
  - **`apps/products/models.py` import-uje samo iz `apps.core`** (top-level — `from apps.core.models import TimestampedModel, SluggedModel`; `from apps.core.utils import slugify_ascii`); NE direktan import iz `apps.brands.models`
  - **`apps/products/translation.py` koristi apsolutni import** `from apps.products.models import ...`
  - **`apps/products/apps.py` `verbose_name = _("Proizvodi")`** (locale-aware)
- **And** **NIJEDNA ćirilica** u izvornom kodu (per project-context.md § Anti-pattern: Ćirilica).
- **And** sve user-facing string vrednosti (verbose_name, choices labels, ValidationError messages) prolaze kroz `gettext_lazy as _` (per project-context.md § Anti-pattern: Hardcoded user-facing string).
- **And** `uv run ruff check .` exit code 0 (line length 100, naming conventions per project-context.md § Code Quality).
- **And** `uv run ruff format --check .` exit code 0.

**AC13 — Test coverage MINIMUM: `__str__` testovi (7 modela), FK relationships sa `related_name`, slug field constraints na Product (unique globally per SluggedModel mixin), translation field auto-generation (6 modela × translatable fields), validation rules (Product.key_features max 3, ProductSimilar no-self-ref), CASCADE/PROTECT delete behavior**

- **Given** TEA agent piše testove u Step 3 (RED phase per project-context.md § Test discipline)
- **When** TEA kreira `apps/products/tests/test_models.py`
- **Then** testovi MINIMUM pokrivaju (TEA odlučuje konkretnu implementaciju):
  - **Model `__str__` testovi** — svih 7 modela:
    - `test_product_str_returns_brand_em_dash_name`
    - `test_product_image_str_returns_product_and_order`
    - `test_product_variant_str_returns_name`
    - `test_product_specification_str_returns_section_key_value`
    - `test_product_brochure_str_returns_title_or_fallback`
    - `test_product_testimonial_str_returns_author_and_product`
    - `test_product_similar_str_returns_product_arrow_related`
  - **FK + related_name access:**
    - `test_brand_products_related_name` — `brand.products.all()` accessor radi
    - `test_series_products_related_name` — `series.products.all()`
    - `test_subcategory_products_related_name` — `subcategory.products.all()`
    - `test_product_images_related_name` — `product.images.all()`
    - `test_product_variants_related_name` — `product.variants.all()`
    - `test_product_specifications_related_name` — `product.specifications.all()`
    - `test_product_brochures_related_name` — `product.brochures.all()`
    - `test_product_testimonials_related_name` — `product.testimonials.all()`
    - `test_product_outgoing_similars_related_name` — `product.outgoing_similars.all()` accessor radi (source direction; renamed per I11)
    - `test_product_incoming_similars_related_name` — `product.incoming_similars.all()` (reverse direction; renamed per I11)
  - **Slug field constraints (Product koristi SluggedModel mixin — global unique):**
    - `test_product_slug_globally_unique` — kreirati dva Product-a sa istim slug-om → `IntegrityError`
    - `test_product_save_auto_generates_slug_from_name` — bez eksplicitnog slug-a → posle save slug je populated (matches 2.1 NEW-CRIT-2 pattern regression guard)
    - `test_product_save_preserves_explicit_slug` — explicit slug preserve-uje
    - `test_product_slug_ascii_transliteration` — name "Čorić TB-804" → slug "coric-tb-804"
  - **Translation fields exist after migration** — koristi Django introspection (matches 2.1 AC12 pattern):
    ```python
    @pytest.mark.django_db
    def test_product_translation_fields_registered():
        from apps.products.models import Product
        field_names = {f.name for f in Product._meta.get_fields()}
        for lang in ("sr", "hu", "en"):
            assert f"name_{lang}" in field_names
            assert f"description_{lang}" in field_names
            assert f"key_features_{lang}" in field_names
    ```
    - Identičan pattern za ProductImage (alt_text), ProductVariant (name, description), ProductSpecification (key, value), ProductBrochure (title), ProductTestimonial (quote, location).
  - **`Product.key_features` JSON validation:**
    - `test_product_key_features_max_3_passes` — lista od 3 string-a → `full_clean()` ne raise-uje
    - `test_product_key_features_4_entries_raises` — lista od 4 → ValidationError
    - `test_product_key_features_non_list_raises` — `"string"` ili `{}` → ValidationError
    - `test_product_key_features_non_string_items_raises` — `[1, 2, 3]` → ValidationError
    - `test_product_key_features_empty_list_passes` — `[]` → ne raise-uje (default value)
    - `test_product_key_features_max_3_enforced_on_translated_variants` — KRITIČNI test za C3: kreirati Product i postaviti `key_features_hu = ["a", "b", "c", "d"]` (5 stavki u HU varijanti) → `full_clean()` MORA raise-ovati ValidationError sa key `"key_features_hu"`. Isti pattern za `key_features_sr` i `key_features_en` (parametrizovan test za sva 3 jezika). **NOTE I-iter3-5:** Asercija MORA koristiti membership (`"key_features_hu" in exc.value.message_dict`), NE equality — vidi Dev Notes "ValidationError assertion pattern" za detalje (base accessor + translated variant generišu dual-key entry u message_dict).
    - `test_product_key_features_non_list_raises_on_translated_variants` — postaviti `key_features_en = "string"` → ValidationError sa key `"key_features_en"`. Membership assertion (per I-iter3-5 Dev Note).
  - **`Product.condition` + `Product.status` choices validation:**
    - `test_product_condition_choice_required` — `Product.condition` ima default `NEW`; invalid value → ValidationError
    - `test_product_status_default_is_draft`
    - `test_product_status_invalid_value_raises`
  - **`ProductSimilar.clean()` no-self-reference (IMP-iter4-4 — DVA path-a, vidi Dev Note "ProductSimilar save() bez full_clean()"):**
    - `test_product_similar_self_reference_raises_validation_error` — kreirati `ProductSimilar(product=p, related_product=p)` i pozvati `full_clean()` EKSPLICITNO → `ValidationError` sa `__all__` key u `message_dict`. **NEMA `save()` override-a** — Django default `save()` NE poziva `full_clean()`, pa `clean()` se mora pozvati explicitly.
    - `test_product_similar_db_check_constraint_blocks_self_reference` — koristi `ProductSimilar.objects.create(product=p, related_product=p)` (ili raw INSERT) — to BYPASS-uje `clean()` i hita DB-level CheckConstraint direktno → `IntegrityError`. Test mora biti `@pytest.mark.django_db(transaction=True)` da bi Postgres/SQLite zaista raise-ovao IntegrityError u testu (ne odložio do transaction commit-a). Vidi Dev Note iznad za razlog za nedostatak `save()` override-a.
    - `test_product_similar_unique_pair_constraint` — kreirati duplikat (product, related_product) → IntegrityError
  - **`Product.subcategory` i `Product.series` nullable testovi:**
    - `test_product_without_series_allowed` — kreirati Product bez series → ne raise-uje
    - `test_product_without_subcategory_allowed` — kreirati Product bez subcategory → ne raise-uje
    - `test_product_without_series_and_subcategory_allowed` — kreirati Product sa OBOJE NULL (I9 combined edge case PR-D2+D3) → ne raise-uje; verifikuje "orphan product attached samo na Brand" scenario
  - **PROTECT/CASCADE delete cascade tests:**
    - `test_brand_protects_product_deletion` — kreirati Brand + Product; `Brand.delete()` → `ProtectedError`
    - `test_series_protects_product_deletion` — kreirati Series + Product; `Series.delete()` → `ProtectedError`
    - `test_subcategory_protects_product_deletion` — kreirati Subcategory + Product; `Subcategory.delete()` → `ProtectedError`
    - `test_product_delete_cascades_to_images` — kreirati Product + ProductImage; `Product.delete()` → `ProductImage.objects.count() == 0`. **NOTE I-iter3-4:** `ProductImage.image` je REQUIRED — koristi `SimpleUploadedFile` stub pattern iz Dev Notes "TEA fixture patterns za required file fields".
    - `test_product_delete_cascades_to_variants`
    - `test_product_delete_cascades_to_specifications`
    - `test_product_delete_cascades_to_brochures` — **NOTE I-iter3-4:** `ProductBrochure.pdf_file` je REQUIRED — koristi `ContentFile(b"%PDF-1.4 stub", name="stub.pdf")` pattern iz Dev Notes "TEA fixture patterns za required file fields".
    - `test_product_delete_cascades_to_testimonials`
    - `test_product_delete_cascades_to_similar` — Product.delete() briše `outgoing_similars` + `incoming_similars` entry-je (renamed per I11)
  - **`get_absolute_url` testovi** (sa skip pattern — Gotcha PR-5):
    ```python
    @pytest.mark.skip(reason="URLs come in Story 2.7 — placeholder validates method exists")
    def test_product_get_absolute_url_returns_string():
        product = Product(slug="test-product")
        url = product.get_absolute_url()  # Will NoReverseMatch in 2.2
        assert isinstance(url, str)
    ```
    - **Alternativa:** `assert callable(Product.get_absolute_url)` zero-cost check bez actual reverse poziva
- **And** `apps/products/tests/test_apps.py` testira `ProductsConfig.name == "apps.products"` smoke pattern (kopija 2.1 BR-1 regression guard).
- **And** **app boundary regression test** (AC12 enforcement; I8 — extended sa upper-bound check za apps.products → apps.catalog). **NOTE I-iter3-1:** Fajl živi u `tests/integration/test_app_boundaries.py` (NE `apps/brands/tests/...`) — per project-context.md § Test organization "Integration tests — cross-app → `tests/integration/test_<feature>.py`". Boundary test pokriva dva smera (brands→products + products→catalog) pa logički NE pripada per-app test dir-u nego canonical cross-app integration lokaciji:
  ```python
  # tests/integration/test_app_boundaries.py (NEW file)
  import ast
  import pathlib


  def _assert_no_import(src_dir: pathlib.Path, forbidden_prefix: str) -> None:
      """Walk src_dir/**/*.py (excl. tests/) and assert no import of forbidden_prefix."""
      for py_file in src_dir.rglob("*.py"):
          if "tests" in py_file.parts:
              continue
          tree = ast.parse(py_file.read_text(encoding="utf-8"))
          for node in ast.walk(tree):
              if isinstance(node, ast.ImportFrom) and node.module:
                  assert not node.module.startswith(forbidden_prefix), (
                      f"{py_file} import-uje {node.module} — boundary violation"
                  )
              elif isinstance(node, ast.Import):
                  for alias in node.names:
                      assert not alias.name.startswith(forbidden_prefix), (
                          f"{py_file} import-uje {alias.name} — boundary violation"
                      )


  def test_brands_does_not_import_products():
      """Per architecture.md § Zabranjene zavisnosti — brands NIKAD ne sme importovati products."""
      _assert_no_import(pathlib.Path("apps/brands"), "apps.products")


  def test_products_does_not_import_catalog():
      """Per architecture.md dependency chain `core ← brands ← products ← catalog` —
      products NIKAD ne sme importovati catalog. Defensive: catalog app još NE postoji
      u Story 2.2 (uvedeno u Epic 2.6+), pa ova provera prolazi trivijalno za sada,
      ali ostaje kao regression guard čim catalog uđe u repo. (I8 extension.)
      """
      products_dir = pathlib.Path("apps/products")
      if products_dir.exists():
          _assert_no_import(products_dir, "apps.catalog")
  ```
  - **NOTE I8:** Test je 1-line extension postojećeg AST walk-a. Defensive guard: kada `apps.catalog` ne postoji (Story 2.2 vreme), test PASS jer `forbidden_prefix` nije pronađen ni u jednoj import-u. Kada Epic 3+ uvede `apps.catalog`, postojeći test odmah uhvati svaku `from apps.catalog import ...` linije u apps/products/**/*.py.

## Tasks / Subtasks

### Task 1 — Kreiranje `apps/products/` Django app i registracija u INSTALLED_APPS (AC1)

- [ ] 1.1: Kreirati direktorijum `apps/products/` kroz Django startapp komandu:
  ```powershell
  New-Item -ItemType Directory -Force apps/products
  uv run python manage.py startapp products apps/products
  ```
- [ ] 1.2: Obrisati `apps/products/tests.py` (Django startapp varira — fajl može i ne mora postojati u zavisnosti od šablona) i kreirati `apps/products/tests/` direktorijum. NAPOMENA: Dev kreira SAMO `tests/__init__.py`; **`tests/test_models.py` i `test_apps.py` su TEA deliverable u Step 3 (RED phase)** — Dev NIKAD ne piše testove (per project-context.md § Test discipline; I6 fix):
  ```powershell
  # I15: -ErrorAction SilentlyContinue štiti od false-error ako tests.py nije generisan
  Remove-Item apps/products/tests.py -ErrorAction SilentlyContinue
  New-Item -ItemType Directory -Force apps/products/tests
  New-Item -ItemType File apps/products/tests/__init__.py
  ```
- [ ] 1.2b: **(IMP-iter4-3)** Ukloniti default `apps/products/views.py` koji `startapp` generiše (sadrži samo `# Create your views here.` placeholder — views layer je out-of-scope za 2.2; Story 2.7/2.8 prvi put kreira `views.py` kad zatreba). Razlog: Story 2.1 je istu disciplinu primenila na `apps/brands/` (uklonila default `views.py` posle startapp-a — sprečava confused-Dev "popunjavanje" placeholder fajla). PowerShell komanda (`-ErrorAction SilentlyContinue` štiti od false-error ako fajl već ne postoji):
  ```powershell
  Remove-Item apps/products/views.py -ErrorAction SilentlyContinue
  ```
  **NEMA `urls.py`/`forms.py`/`managers.py`/`signals.py` za uklanjanje** — startapp ih ne generiše (IMP-iter4-2 verifikacija); oni ne postoje posle Task 1.1.
- [ ] 1.3: Editovati `apps/products/apps.py`:
  ```python
  """AppConfig za apps.products — Product i related modeli content layer.

  Domain app uveden u Story 2.2 (Epic 2). Drugi konzument django-modeltranslation
  paketa (posle apps.brands u Story 2.1). Jednosmerna zavisnost: products → brands.
  """
  from django.apps import AppConfig
  from django.utils.translation import gettext_lazy as _


  class ProductsConfig(AppConfig):
      default_auto_field = "django.db.models.BigAutoField"
      name = "apps.products"
      verbose_name = _("Proizvodi")
  ```
  - **KRITIČNO:** `name = "apps.products"` (sa `apps.` prefiksom — Gotcha PR-1; matches `INSTALLED_APPS` entry).
- [ ] 1.4: Modifikovati `config/settings/base.py` `INSTALLED_APPS` — **APENDOVATI JEDAN nov entry** (NE rewrite cele liste):
  - `"apps.products",` (POSLE `"apps.brands",` — per Decision PR-D1 dep rule).
  - **KRITIČNO (CRIT-iter4-1):** koristi targeted Edit operaciju koja menja SAMO blok između `"apps.brands",` linije i `]` zatvarača — dodaj jednu novu liniju `"apps.products",  # NOVO Story 2.2 — domain app (POSLE brands per dep rule)`. NEMOJ replace-ovati ceo INSTALLED_APPS literal niti reordovati `modeltranslation`/`django.contrib.admin`/itd. — postojeći redosled (Story 2.1) je SOURCE OF TRUTH i mora ostati netaknut. Verifikuj live fajl pre Edit-a: `Select-String -Path config/settings/base.py -Pattern '"apps.brands",'` mora vratiti TAČNO jednu liniju.
  - **DO / DON'T (IMP-iter5-2):**
    - **DO:** `Add-Content config/settings/base.py` (PowerShell append na kraj liste je rizično jer `]` zatvara listu pre kraja fajla) ili **targeted Edit** koji pronalazi `"apps.brands",` liniju i dodaje sledeću liniju ispod nje. Preferred: Edit operacija sa `old_string = '    "apps.brands",                  # Story 2.1\n]'` → `new_string = '    "apps.brands",                  # Story 2.1\n    "apps.products",                # NOVO Story 2.2 — domain app (POSLE brands per dep rule)\n]'`.
    - **DON'T:** Full INSTALLED_APPS block replace — to bi striplo live `# NOVO Story 1.6 — request.htmx detection` style komentare koje 2.1 i ranije story-ji ostavili u fajlu. Snippet u AC1 je samo ABSTRACT redosled-reference, ne verbatim copy live fajla.
- [ ] 1.4b: **EKSPLICITAN korak (C3):** dodati `MODELTRANSLATION_FALLBACK_LANGUAGES = ("sr",)` u `config/settings/base.py` (posle `LANGUAGES = [...]` tuple-a iz Story 1.4). Ovo je odvojen korak od INSTALLED_APPS modifikacije da Dev ne propusti zahtev. **Rationale (IMP-iter4-1):** architecture-defensive setting — modeltranslation zahteva fallback chain da bi pristup translated polju bez aktivnog language context-a (management command, Celery task, programmatic access u skripti) imao deterministički sr fallback umesto `None`. Matches `LANGUAGE_CODE = "sr"` iz Story 1.4 i project-context.md § i18n locale fallback ("sr je default; ako neki prevod nedostaje → fallback na sr"). **NIJE FR-32 mapiranje** — FR-32 je UX marker concern za Story 6.5; ovo je backend foundation. Bez ovog setting-a `key_features_hu` (prazan) ne fallback-uje na `key_features_sr` deterministički u svim execution context-ima.
- [ ] 1.5: Smoke verifikacija: `uv run python manage.py check` — exit code 0; nikakav warning o INSTALLED_APPS ordering-u ili circular import-u.

### Task 2 — Definisanje 7 modela u `apps/products/models.py` (AC2, AC3, AC4, AC5, AC6, AC7, AC8, AC12)

- [ ] 2.1: Header `apps/products/models.py`:
  ```python
  """Story 2.2 — Product i related modeli (Epic 2 content layer).

  Sva 7 modela slede 2.1 pattern:
  - Eksplicitni `on_delete` + `related_name` na svim FK-ovima
  - Product nasleđuje SluggedModel + TimestampedModel iz apps.core.models
  - Cross-app FK-ovi (Brand, Series, Subcategory) kroz string lazy reference
  - Meta.indexes sa imenima `<table>_<columns>_idx`
  - `save()` override sa eksplicitnim redosledom: slug auto-gen → full_clean() → super().save()
  - `gettext_lazy as _` za sve user-facing string-ove

  Decision references (vidi 2-2-product-i-related-modeli.md):
  - PR-D1 — apps.products POSLE apps.brands u INSTALLED_APPS (jednosmerna zavisnost)
  - PR-D2 — Product.series nullable (Jeegee/HZM nemaju series koncept)
  - PR-D3 — Product.subcategory nullable (top-tier traktori nemaju subcategory drill-down)
  - PR-D4 — paralelno is_published + status (epic spec eksplicitni; admin sync opciono u 8.6)
  - PR-D5 — ProductSimilar je directional (NE auto-simetrična)

  Out-of-scope za 2.2 (defer references):
  - search_vector polje → Story 2.13 (zasebna migracija)
  - MIME validation za upload polja → Story 2.3 (image) i 2.4 (PDF)
  - post_save signal za ProductBrochure.cover_thumbnail → Story 2.4
  - Custom managers (PublishedProductManager) → Story 2.6 (Brand Listing) je owner za apps/products/managers.py
  - Views/urls/forms → Story 2.7/2.8/8.6
  """

  from __future__ import annotations

  from django.conf import settings
  from django.core.exceptions import ValidationError
  from django.db import models
  from django.urls import reverse
  from django.utils.translation import gettext_lazy as _

  from apps.core.models import SluggedModel, TimestampedModel
  from apps.core.utils import slugify_ascii

  _PRODUCT_KEY_FEATURES_MAX = 3
  ```
- [ ] 2.2: Definisati `Product` model per AC2 — naslediti `SluggedModel, TimestampedModel`; sva polja (brand FK, series FK nullable, subcategory FK nullable, name, description, key_features JSON, main_image, year, price_eur, horse_power, condition TextChoices, status TextChoices, is_published); Meta.indexes (3 indexes); `__str__`; `get_absolute_url()`; `clean()` validacija za key_features (list-of-str, max 3); `save()` + `full_clean()` override sa slug auto-gen.
- [ ] 2.3: Definisati `ProductImage` model per AC3 — naslediti TimestampedModel; FK Product CASCADE related_name="images"; image, order, alt_text (translatable); Meta.
- [ ] 2.4: Definisati `ProductVariant` model per AC4 — naslediti TimestampedModel; FK Product CASCADE related_name="variants"; name (translatable), code, image, description (translatable), order; Meta.
- [ ] 2.5: Definisati `ProductSpecification` model per AC5 — naslediti TimestampedModel; FK Product CASCADE related_name="specifications"; `SpecSection` TextChoices (Motor/Transmisija/Hidraulika/Ostalo); key (translatable), value (translatable), order; Meta.
- [ ] 2.6: Definisati `ProductBrochure` model per AC6 — naslediti TimestampedModel; FK Product CASCADE related_name="brochures"; pdf_file, cover_thumbnail_image (blank/null — auto-gen u 2.4), title (translatable); Meta.
- [ ] 2.7: Definisati `ProductTestimonial` model per AC7 — naslediti TimestampedModel; FK Product CASCADE related_name="testimonials"; photo, quote (translatable), author_name, location (translatable), order; Meta.
- [ ] 2.8: Definisati `ProductSimilar` model per AC8 — naslediti TimestampedModel; FK product CASCADE related_name="outgoing_similars" verbose_name="Proizvod"; FK related_product CASCADE related_name="incoming_similars" verbose_name="Sličan proizvod"; order; Meta sa UniqueConstraint + CheckConstraint (no self-reference); `clean()` raise-uje friendly poruku za self-reference. (related_name renamed per I11; verbose_name added per I1.)
- [ ] 2.9: Verifikovati `ruff check apps/products/models.py` exit 0 (line length 100, naming conventions).
- [ ] 2.10: Verifikovati cross-app FK pattern: sve cross-app FK-ove (Brand, Series, Subcategory) koriste STRING lazy reference (`"brands.Brand"`, NE direktan import).

### Task 3 — Kreiranje `apps/products/translation.py` (AC9)

- [ ] 3.1: Kreirati `apps/products/translation.py` sa 6 `TranslationOptions` klase per AC9 (Product, ProductImage, ProductVariant, ProductSpecification, ProductBrochure, ProductTestimonial — ProductSimilar IZUZET).
- [ ] 3.2: Verifikovati apsolutni import iz `apps.products.models` (NE relativni `.models`).
- [ ] 3.3: Smoke verifikacija auto-discovery:
  ```powershell
  uv run python manage.py shell -c "from apps.products.models import Product; print([f.name for f in Product._meta.get_fields() if 'name' in f.name or 'description' in f.name or 'key_features' in f.name])"
  ```
  Output mora sadržati: `name`, `name_sr`, `name_hu`, `name_en`, `description`, `description_sr/hu/en`, `key_features`, `key_features_sr/hu/en`.

### Task 4 — Generisanje + manual review + apply migracije (AC10)

- [ ] 4.1: Pre-make verification (matches 2.1 IMP-8):
  - Verifikovati `apps/core/translation.py` NEMA aktivnih `@register` decoratora (regression — Story 2.1 ne menja core/translation.py)
  - Sprečava spurious migration na apps.core ili apps.brands (Gotcha PR-2)
- [ ] 4.2: Generisati migraciju:
  ```powershell
  uv run python manage.py makemigrations products
  ```
- [ ] 4.3: **MANUAL REVIEW** `apps/products/migrations/0001_initial.py` — primeniti AC10 manual review checklist verbatim (PowerShell `Select-String` + `Measure-Object` komande za on_delete, per-field translation kolone, JSONField, DecimalField, UniqueConstraint/CheckConstraint, AddIndex, PROTECT/CASCADE counts, dry-run plan, inspectdb). **Single SOT — AC10 je primarni izvor; ne duplikuj komande ovde** (I-iter2-2 — fold-to-AC10 da spreči drift između shell konvencija). Ako bilo koja AC10 verifikacija ne prođe → fix model/migration → re-makemigrations → retry.
- [ ] 4.4: `uv run python manage.py migrate --plan` — verifikovati plan (samo `products 0001_initial`; nikakva druga migracija ne sme biti generisana).
- [ ] 4.5: Apply migration: `uv run python manage.py migrate products` — exit code 0.
- [ ] 4.6: Post-migration verifikacija kroz Django shell:
  ```powershell
  uv run python manage.py shell -c "from apps.products.models import Product, ProductImage, ProductVariant, ProductSpecification, ProductBrochure, ProductTestimonial, ProductSimilar; print(Product.objects.count(), ProductImage.objects.count(), ProductVariant.objects.count(), ProductSpecification.objects.count(), ProductBrochure.objects.count(), ProductTestimonial.objects.count(), ProductSimilar.objects.count())"
  ```
  Očekivani output: `0 0 0 0 0 0 0` (sve tabele postoje, prazne).
- [ ] 4.7: Optional post-migrate inspect (per 2.1 AC7 step 7):
  ```powershell
  uv run python manage.py inspectdb products_product products_productimage products_productvariant products_productspecification products_productbrochure products_producttestimonial products_productsimilar > "$env:TEMP\inspectdb_2_2.txt"
  ```
  Verifikovati `_sr`/`_hu`/`_en` kolone na translatable poljima.
- [ ] 4.8: Commit-ovati migraciju + model promene **ZAJEDNO** u jednom commit-u (per project-context.md § Migrations discipline: atomic commit).

### Task 5 — Kreiranje `apps/products/admin.py` stub (AC11)

- [ ] 5.1: Editovati `apps/products/admin.py` (Django startapp generiše prazan fajl) — **bare `admin.site.register(...)` za svih 7 modela** (mirror 2.1 pattern; NE `TranslationAdmin` base — vidi Gotcha PR-11 i AC11):
  ```python
  from django.contrib import admin

  from apps.products.models import (
      Product,
      ProductBrochure,
      ProductImage,
      ProductSimilar,
      ProductSpecification,
      ProductTestimonial,
      ProductVariant,
  )

  admin.site.register(Product)
  admin.site.register(ProductImage)
  admin.site.register(ProductVariant)
  admin.site.register(ProductSpecification)
  admin.site.register(ProductBrochure)
  admin.site.register(ProductTestimonial)
  admin.site.register(ProductSimilar)
  ```
  - **NAPOMENA (C1):** Bare `admin.site.register()` NE generiše sr/hu/en tabove u admin formi. Translated polja prikazaće se kao flat fields (npr. `name`, `name_sr`, `name_hu`, `name_en` kao 4 odvojena polja). Pun `TranslationAdmin` (sa pravim tabovima) je Story 8.6 scope. Ova story mirror-uje 2.1 deliverable (`apps/brands/admin.py` — bare register).
- [ ] 5.2: Smoke verifikacija (opciono, ako je superuser kreiran u 2.1) — admin index strana prikazuje "Proizvodi" sekciju sa 7 model linka.
- [ ] 5.3: **NEMA** custom `list_display`, `list_filter`, `inlines`, `TranslationAdmin` base klasa — sve to je Story 8.6 scope.

### Task 6 — TEA piše testove (RED phase) — Dev NIKAD ne piše testove (AC13)

- [ ] 6.1: TEA kreira `apps/products/tests/test_models.py` sa svim AC13 test scenarijima:
  - 7 `__str__` testovi
  - FK related_name access testovi (10+ FK access pattern-i; uključuje `outgoing_similars` / `incoming_similars` per I11)
  - Slug constraint testovi (Product global unique, auto-gen, preserve, ASCII transliteration)
  - Translation fields introspection testovi (6 modela)
  - `Product.key_features` validation (max 3, list-of-str shape, empty list ok) + **`test_product_key_features_max_3_enforced_on_translated_variants`** za sr/hu/en variant coverage (C3)
  - `Product.condition`/`status` choices validation
  - `ProductSimilar` no-self-reference (clean + DB CheckConstraint)
  - `ProductSimilar` UniqueConstraint na pair (product, related_product)
  - Nullable `series` + `subcategory` allowed (uključuje I9 edge case: both NULL allowed)
  - PROTECT delete tests (Brand, Series, Subcategory)
  - CASCADE delete tests (Product → 6 child entiteta)
  - `get_absolute_url` skip pattern (Story 2.7 dependency)
- [ ] 6.2: TEA kreira `apps/products/tests/test_apps.py` smoke pattern (`ProductsConfig.name == "apps.products"`).
- [ ] 6.3: TEA kreira `tests/integration/test_app_boundaries.py` (NEW file) sa AST-based static check da apps/brands nikad ne importuje apps.products (AC12 regression). **PLUS** (I8 extension): test_products_does_not_import_catalog — extends AST walk da pokrije `apps/products/**/*.py` upper-bound check za `apps.catalog` import (defensive: PASS dok catalog ne postoji, FAIL čim Epic 3+ uvede catalog AND products poveže). **I-iter3-1 rationale:** cross-app boundary test pripada `tests/integration/` per project-context.md § Test organization (NIJE per-app test, testira arhitekturne invariante između app-ova).
- [ ] 6.3a: **I-iter3-1 prerequisite:** TEA kreira `tests/integration/` direktorijum + `__init__.py` ako ne postoji (Story 2.1 ga nije kreirala). Komande:
  ```powershell
  New-Item -ItemType Directory -Force tests/integration
  New-Item -ItemType File tests/integration/__init__.py
  ```
  Direktorijum + `__init__.py` su TEA territory (Step 3) — Dev ih ne kreira.
- [ ] 6.4: `uv run pytest apps/products/tests/ tests/integration/test_app_boundaries.py` — svi RED testovi pišu se OČEKUJU green nakon Dev implementacije.

### Task 7 — Manual smoke test kroz Django shell (DoD verification)

- [ ] 7.1: Pokrenuti Django shell i kreirati sample Product sa svim related entitetima za manualnu verifikaciju.
  > **Shell (I-iter3-3):** Komande za pokretanje shell-a (npr. `uv run python manage.py shell`) treba pokrenuti u PowerShell 5.1+ na Windows-u. Git Bash / WSL korisnici mogu koristiti isti `uv run` interface (uv je cross-shell). Sam Python kod ispod je shell-agnostic.
  ```python
  from apps.brands.models import Brand, Series, Category, Subcategory  # Subcategory used (IMP-iter4-5)
  from apps.products.models import (
      Product, ProductImage, ProductVariant, ProductSpecification,
      ProductBrochure, ProductTestimonial, ProductSimilar,
  )

  # Kreirati prerequisites (ako ne postoje iz 2.1 manual smoke test)
  brand = Brand.objects.create(name="Demo Brand 2.2", brand_color="#25402F")
  series = Series.objects.create(brand=brand, name="Demo Serija")
  cat = Category.objects.create(name="Demo Kategorija", is_for=Category.CategoryScope.TRAKTORI)
  # IMP-iter4-5: exerciše full cross-app FK chain — Category → Subcategory → Product.subcategory
  # Verifikuje da string lazy reference "brands.Subcategory" radi i da PROTECT on_delete drži.
  # IMP-iter5-1: Subcategory.slug se auto-gen iz `name` (Story 2.1 Pattern A — save() + full_clean()
  # override-i pozivaju slugify_ascii(self.name) ako je slug blank). Drop-ovan eksplicitni `slug=`
  # da smoke test exerciše inherited 2.1 auto-gen pattern, ne hardcoded slug.
  sub = Subcategory.objects.create(category=cat, name="Demo Potkategorija")

  # Kreirati Product (sa Subcategory linked-om — exerciše all 3 cross-app FK-ova)
  product = Product.objects.create(
      brand=brand,
      series=series,
      subcategory=sub,
      name="Demo Traktor TB-804",
      description="Demo opis proizvoda za 2.2 smoke test.",
      key_features=["Snažan motor 80 KS", "Klimatizovana kabina", "ABS kočnice"],
      year=2024,
      price_eur="25000.00",
      horse_power=80,
      condition=Product.ConditionChoice.NEW,
      status=Product.StatusChoice.PUBLISHED,
      is_published=True,
  )
  print(product.slug)  # Mora biti auto-generisan iz name: "demo-traktor-tb-804"
  print(product.brand.products.all())  # Reverse access
  print(f"Subcategory chain: {product.subcategory.category.name} → {product.subcategory.name}")

  # Kreirati 2 ProductImage
  for i in range(2):
      ProductImage.objects.create(
          product=product, image=f"products/gallery/demo-{i}.jpg",
          order=i, alt_text=f"Demo slika {i}",
      )
  print(product.images.count())  # 2

  # Kreirati 1 ProductVariant
  variant = ProductVariant.objects.create(
      product=product, name="Sa kabinom", code="TB804-CAB",
      description="Standardna kabina sa klimom.",
  )

  # Kreirati ProductSpecification u svim 4 sekcije
  ProductSpecification.objects.create(product=product, section="motor", key="Snaga", value="80 KS")
  ProductSpecification.objects.create(product=product, section="transmisija", key="Tip", value="Hidrostatička")
  ProductSpecification.objects.create(product=product, section="hidraulika", key="Protok", value="60 L/min")
  ProductSpecification.objects.create(product=product, section="ostalo", key="Težina", value="3500 kg")

  # ProductBrochure se PRESKAČE u smoke testu (I13) — pdf_file je REQUIRED i smoke
  # test ne stvara real PDF fajl. Pun integration test sa fixture-bazom prepušta se
  # TEA u Step 3 (test_models.py) gde `ContentFile(b"%PDF-1.4 stub", name="stub.pdf")`
  # može da satisfy required FileField bez stvarnog file system upisa.
  # Story 2.4 dodaje `post_save` signal koji popunjava cover_thumbnail_image kroz pdf2image.

  # ProductTestimonial
  ProductTestimonial.objects.create(
      product=product, quote="Najbolji traktor koji sam imao!",
      author_name="Marko Marković", location="Vojvodina",
  )

  # ProductSimilar (kreirati drugi product i povezati)
  product2 = Product.objects.create(brand=brand, name="Demo Traktor TB-905")
  ProductSimilar.objects.create(product=product, related_product=product2, order=0)
  print(product.outgoing_similars.count())  # 1 (product → product2)
  print(product2.incoming_similars.count())  # 1 (reverse direction)

  # Test no-self-reference validation
  try:
      bad = ProductSimilar(product=product, related_product=product)
      bad.full_clean()
      print("BUG — trebalo je da raise-uje")
  except Exception as e:
      print(f"OK — no-self-reference raised: {e}")

  # Test key_features max 3 validation
  try:
      product_bad = Product(brand=brand, name="Bad", key_features=["a", "b", "c", "d"])
      product_bad.full_clean()
      print("BUG — trebalo je da raise-uje")
  except Exception as e:
      print(f"OK — key_features max 3 raised: {e}")
  ```
- [ ] 7.2: Verifikovati u admin formi za Product da su `_sr`/`_hu`/`_en` polja prisutna kao flat fields (4 odvojena CharField-a po translatable polju). **Tabovi (sr/hu/en navigation UI) se NE renderuju** sa bare `admin.site.register()` — to je očekivano u 2.2; pun `TranslationAdmin` sa tabular UI dolazi u Story 8.6 (vidi C1 / Gotcha PR-11).

### Task 8 — Lint + format pass + regression (DoD verification)

- [ ] 8.1: `uv run ruff check .` — exit code 0.
- [ ] 8.2: `uv run ruff format --check .` — exit code 0.
- [ ] 8.3: `uv run djade --check templates/partials/*.html` — exit code 0 (no template promene u 2.2, regression guard).
- [ ] 8.4: `uv run pytest` — sve postojeće Epic 1 + 2.1 testovi prolaze + svi novi 2.2 testovi (regression).

### Task 9 — Sprint status update + commit (DoD)

- [ ] 9.1: Update `_bmad-output/implementation-artifacts/sprint-status.yaml`:
  - `2-2-product-i-related-modeli: backlog` → `ready-for-dev` (već urađeno u SM Step 4 — proveriti)
  - `last_updated: 2026-05-29`
  - **NAPOMENA — typo "dev elopment_status" preservation:** Verifikovati da sprint-status.yaml line 46 `dev elopment_status:` typo OSTAJE NEPROMENJEN (per 2.1 IMP-11; legacy orchestrator artifact).
- [ ] 9.2: Commit message follows Conventional Commits:
  ```
  feat(products): Story 2.2 — Product i related modeli + modeltranslation registracija

  - apps/products app sa 7 modela (Product, ProductImage, ProductVariant,
    ProductSpecification, ProductBrochure, ProductTestimonial, ProductSimilar)
  - Product nasleđuje SluggedModel + TimestampedModel iz apps.core (prvi konzument 2.1 foundation)
  - Cross-app FK-ovi (Brand PROTECT, Series PROTECT nullable, Subcategory PROTECT nullable)
    kroz string lazy reference
  - ProductSimilar sa UniqueConstraint + CheckConstraint (no self-reference)
  - apps/products/translation.py registruje 6 TranslationOptions
  - Migracija 0001_initial.py manually reviewed (7 tabele sa _sr/_hu/_en kolonama)
  - Out-of-scope: search_vector (Story 2.13), MIME validation (2.3/2.4), views/admin (2.7/8.6)
  ```

## Dev Notes

### Architecture compliance

- **App boundaries (architecture.md § Architectural Boundaries lines 716-740):** `apps.products` import-uje samo iz `apps.brands` (jednosmerno) i `apps.core` (utility). `apps.brands` NE SME importovati `apps.products` (Gotcha PR-6 regression test enforce-uje).
- **App dependency graph:** `core ← brands ← products ← catalog` (arch.md line 886). Story 2.2 je drugi link u lancu.
- **Cross-app FK pattern:** Lazy string reference (`"brands.Brand"`) za FK-ove ka drugom app-u; direktan name reference za in-app FK-ove (matches arch.md § 478 Pattern Example).
- **Base mixins iz Story 2.1:** `TimestampedModel` + `SluggedModel` u `apps/core/models.py` (Decision D3 2.1 explicit YAGNI acknowledgment je da su uvedeni 2.1 KAO FOUNDATION za 2.2 Product). Story 2.2 je prvi konzument — validira 2.1 foundation choice.
- **Naming convention:** indexes per `<table>_<columns>_idx` (matches 2.1 Meta.indexes konvencija); modeli per PascalCase; fields per snake_case.

### Library/framework requirements

- **`django-modeltranslation >= 0.20.3`** — već u `pyproject.toml` (Story 1.1); registrovan u INSTALLED_APPS u Story 2.1; auto-discovery hook radi za `apps.products` automatski. **2.2 ZAHTEVA `MODELTRANSLATION_FALLBACK_LANGUAGES = ("sr",)` setting** u `config/settings/base.py` (C3 — vidi AC1 + Task 1.4b; architecture-defensive locale fallback chain ka sr per project-context.md § i18n locale fallback — NIJE FR-32 mapiranje; FR-32 je view-layer UX marker u Story 6.5 koji se gradi na vrhu ove backend foundation).
- **Django 5.2 LTS** — `models.JSONField` (Product.key_features), `models.TextChoices` (ConditionChoice, StatusChoice, SpecSection), `models.CheckConstraint` (ProductSimilar no-self-ref), `models.DecimalField` (Product.price_eur)
- **`psycopg[binary] >= 3.3.4`** — PostgreSQL adapter za production (Story 9.1); SQLite je dev/CI default
- **NEMA novih dependency-ja u 2.2** — sve potrebne libs su već u pyproject.toml (verifikovati `pyproject.toml` nije menjan kao deo ove story)
- **`apps.core.utils.slugify_ascii`** — već implementiran u 2.1 (Two-stage replacement: digrafovi pa dijakritici); NE redefinisati
- **`apps.core.models.SluggedModel` + `TimestampedModel`** — već implementirani u 2.1; NE redefinisati

### File structure

```text
apps/products/                                  # NOVO Story 2.2
├── __init__.py                                 # prazan (startapp generiše)
├── apps.py                                     # startapp + Task 1.3 edit: ProductsConfig(AppConfig) sa name="apps.products"
├── models.py                                   # startapp + Task 2 edit: 7 modela (Product, ProductImage, ProductVariant,
│                                               #                          ProductSpecification, ProductBrochure,
│                                               #                          ProductTestimonial, ProductSimilar)
├── admin.py                                    # startapp + Task 5 edit: stub admin.site.register() za svih 7 modela
├── translation.py                              # NEW (Task 3): 6 TranslationOptions registracija — startapp NE generiše
├── migrations/
│   ├── __init__.py                             # startapp generiše
│   └── 0001_initial.py                         # NEW (Task 4): MANUAL-REVIEWED migracija
└── tests/                                      # NEW directory (Task 1.2 — startapp generiše tests.py file koji se briše)
    ├── __init__.py                             # NEW (Task 1.2) — Dev deliverable, prazan
    ├── test_models.py                          # NEW (Task 6.1) — TEA RED phase (sve AC13 testovi)
    └── test_apps.py                            # NEW (Task 6.2) — TEA smoke (ProductsConfig.name)

# Šta startapp generiše a 2.2 BRIŠE (IMP-iter4-3):
# - apps/products/tests.py    (Task 1.2 — koristi se tests/ dir umesto)
# - apps/products/views.py    (Task 1.2b — views layer je 2.7/2.8 scope; brisanje mirror 2.1 discipline)

# Šta startapp NE generiše (i 2.2 ne kreira — IMP-iter4-2):
# - apps/products/urls.py     (Story 2.7 prvi put kreira)
# - apps/products/forms.py    (Story 2.7/8.6 prvi put kreira)
# - apps/products/managers.py (Story 2.6 prvi put kreira — PublishedProductManager)
# - apps/products/signals.py  (Story 2.4 prvi put kreira — post_save za ProductBrochure cover thumbnail)

apps/brands/                                    # NETAKNUT u 2.2 (regression guard)

tests/                                          # NEW root-level integration tests dir (I-iter3-1)
└── integration/                                # NEW — cross-app integration testovi (per project-context.md § Test organization)
    ├── __init__.py                             # TEA Step 3 deliverable
    └── test_app_boundaries.py                  # TEA NEW file — AST static check (brands→products + products→catalog)

config/settings/base.py                         # UPDATE: APENDUJ "apps.products" u INSTALLED_APPS POSLE "apps.brands" (NE reorder!)
                                                # UPDATE: APENDUJ MODELTRANSLATION_FALLBACK_LANGUAGES = ("sr",) posle LANGUAGES = [...]
```

**File koji se NE menja u 2.2** (regression guard):
- `apps/core/models.py` — TimestampedModel + SluggedModel su iz 2.1; 2.2 konzumira, ne menja
- `apps/core/utils.py` — slugify_ascii je iz 2.1; 2.2 konzumira
- `apps/brands/models.py` — taksonomija je iz 2.1; 2.2 referencira string lazy
- `apps/brands/translation.py` — netaknut
- `apps/brands/admin.py` — netaknut

### Testing notes for TEA (Step 3)

TEA piše testove u Step 3 (RED phase). Dev NIKAD ne piše testove. SM ne piše testove. Ovo su SAMO **opisni** test scenariji — TEA odlučuje konkretnu implementaciju:

**`apps/products/tests/test_models.py`:**
1. **`__str__` testovi** za sva 7 modela (matches 2.1 AC12 pattern)
2. **FK + related_name access testovi:**
   - `brand.products.all()`, `series.products.all()`, `subcategory.products.all()` (reverse iz brands)
   - `product.images.all()`, `.variants.all()`, `.specifications.all()`, `.brochures.all()`, `.testimonials.all()`
   - `product.outgoing_similars.all()` (Product je source) i `product.incoming_similars.all()` (Product je target) — direkcionalna asimetrija per PR-D5; renamed per I11
3. **Slug constraints (Product):**
   - `unique=True` globalno (kroz SluggedModel mixin) — duplikat → IntegrityError
   - `save()` auto-gen iz `name` ako slug prazan (NEW-CRIT-2 2.1 regression guard pattern)
   - Explicit slug preserve-uje
   - ASCII transliteration test: name `"Čorić TB-804"` → slug `"coric-tb-804"`
4. **Translation field introspection** za svih 6 translatable modela — kroz `_meta.get_fields()` set membership check
5. **`Product.key_features` JSON validation:**
   - 3 entries → ok; 4 entries → ValidationError; non-list → ValidationError; non-string items → ValidationError; empty list → ok
6. **`Product.condition` + `Product.status` TextChoices:**
   - Default condition = NEW; default status = DRAFT; invalid value → ValidationError kroz `full_clean()`
7. **`Product.series` + `Product.subcategory` nullable:**
   - Kreirati Product bez `series` → ok; bez `subcategory` → ok
8. **`ProductSimilar` no-self-reference:**
   - `clean()` raise-uje friendly ValidationError ako `product == related_product`
   - DB CheckConstraint blokira (test `transaction=True` ili eksplicitno raw SQL pokušaj)
   - UniqueConstraint (product, related_product) → duplikat pair → IntegrityError
9. **PROTECT delete:**
   - `Brand.delete()` sa Product → `ProtectedError`
   - `Series.delete()` sa Product → `ProtectedError`
   - `Subcategory.delete()` sa Product → `ProtectedError`
10. **CASCADE delete:**
    - `Product.delete()` briše sve `ProductImage`, `ProductVariant`, `ProductSpecification`, `ProductBrochure`, `ProductTestimonial` zapise
    - `Product.delete()` briše sve `ProductSimilar` zapise gde je product source (`outgoing_similars`)
    - `Product.delete()` briše sve `ProductSimilar` zapise gde je product target (`incoming_similars`)
11. **`get_absolute_url()` skip pattern:**
    - `@pytest.mark.skip(reason="URLs come in Story 2.7")` (per 2.1 Gotcha BR-4 prescribed pattern)

**`apps/products/tests/test_apps.py`:**
- `ProductsConfig.name == "apps.products"` (Gotcha PR-1 regression guard)

**`tests/integration/test_app_boundaries.py` (NEW — I-iter3-1):**
- AST-walk pattern (per AC13) — iterira `apps/brands/**/*.py` (excl. tests/), parsira ast, asertuje da nema `import apps.products` ili `from apps.products...` ili `from apps.products.<x>...`. Plus (I8 extension) ista AST-walk procedure preko `apps/products/**/*.py` asertuje da nema import-a `apps.catalog`.
- Lokacija je `tests/integration/` (NE `apps/brands/tests/`) per project-context.md § Test organization — cross-app invariant test pripada canonical integration dir-u; per-app tests dir je samo za in-app behavior.

**Coverage minimum (per 2.1 model layer convention):** 100% coverage za:
- Sve `clean()` validacije (key_features, ProductSimilar no-self-ref)
- Sve `__str__` metode
- Sve FK related_name access pattern-i
- Translation field introspection (6 modela)
- save() auto-slug + preserve
- PROTECT/CASCADE delete behavior

**Factory pattern:** `factory_boy` NIJE u dev deps (per 2.1 Test discipline note); inline `Model.objects.create()` je OK za 2.2 scope.

**TEA fixture patterns za required file fields (I-iter3-4):**

`ProductImage.image` i `ProductBrochure.pdf_file` su REQUIRED file fields. AC13 CASCADE testovi (`test_product_delete_cascades_to_images`, `test_product_delete_cascades_to_brochures`) zahtevaju kreiranje validnih file stub-ova. Eksplicitni fixture pattern-i koje TEA MORA koristiti:

- **Za `ProductImage.image` (REQUIRED, `ImageField`):**
  ```python
  from django.core.files.uploadedfile import SimpleUploadedFile

  image_stub = SimpleUploadedFile(
      name="stub.jpg",
      content=b"\x89PNG\r\n\x1a\n",  # minimal PNG magic header (8 bytes)
      content_type="image/png",
  )
  ProductImage.objects.create(product=product, image=image_stub, order=0)
  ```
  Pillow `Image.verify()` MIME validacija je Story 2.3 scope, NE 2.2 — 2.2 testovi mogu koristiti minimal magic header stub bez stvarnog dekodovanja PNG payload-a.

- **Za `ProductBrochure.pdf_file` (REQUIRED, `FileField`):**
  ```python
  from django.core.files.base import ContentFile

  pdf_stub = ContentFile(b"%PDF-1.4 stub", name="stub.pdf")
  ProductBrochure.objects.create(product=product, pdf_file=pdf_stub)
  ```
  `python-magic` MIME validacija je Story 2.4 scope — 2.2 testovi koriste minimal `%PDF-` header stub.

- **Cleanup:** pytest-django automatski rolluje testne DB transakcije; file-stub se NE piše na disk u test mode kada `MEDIA_ROOT` pokazuje na `tmp_path` per-test (pytest `tmp_path` fixture). Eksplicitno per-test isolation pattern:
  ```python
  @pytest.fixture(autouse=True)
  def _media_root_isolated(tmp_path, settings):
      settings.MEDIA_ROOT = tmp_path
  ```

**ProductSimilar save() bez full_clean() — dva test path-a (IMP-iter4-4):**

`ProductSimilar` NEMA `save()` override (za razliku od `Product` koji override-uje `save()` i poziva `full_clean()`). Django default `save()` NE poziva `full_clean()`. Posledice za AC13 testove:

1. **`test_product_similar_self_reference_raises_validation_error`** — MORA pozvati `ProductSimilar(product=p, related_product=p).full_clean()` EKSPLICITNO; `clean()` se NE poziva automatski. Očekivani exception: `ValidationError` sa `__all__` key u `message_dict` (jer raise je `ValidationError(_("..."))` bez polja — Django stavlja generic poruke pod `__all__`).
   ```python
   import pytest
   from django.core.exceptions import ValidationError

   def test_product_similar_self_reference_raises_validation_error(product):
       sim = ProductSimilar(product=product, related_product=product)
       with pytest.raises(ValidationError) as exc_info:
           sim.full_clean()
       assert "__all__" in exc_info.value.message_dict   # membership, NE equality
   ```

2. **`test_product_similar_db_check_constraint_blocks_self_reference`** — MORA koristiti `ProductSimilar.objects.create(product=p, related_product=p)` (ili raw INSERT) — to BYPASS-uje `clean()` i hita DB-level `CheckConstraint` direktno. Očekivani exception: `IntegrityError`. Test MORA biti `@pytest.mark.django_db(transaction=True)` da bi Postgres/SQLite zaista raise-ovao IntegrityError u testu (bez `transaction=True`, IntegrityError može da se odloži do commit-a koji se nikad ne desi unutar test transaction wrapper-a).
   ```python
   import pytest
   from django.db import IntegrityError

   @pytest.mark.django_db(transaction=True)
   def test_product_similar_db_check_constraint_blocks_self_reference(product):
       with pytest.raises(IntegrityError):
           ProductSimilar.objects.create(product=product, related_product=product)
   ```

**Razlog za nedostatak `save()` override-a:** ProductSimilar je čisto relational entity (samo 3 polja, dva FK + order); save-time validacija nije potrebna (admin form u 8.6 će validirati explicitno preko `form.is_valid()`). Pattern je drugačiji od `Product` jer Product ima slug auto-gen logiku koja MORA da se desi pre save-a.

**ValidationError assertion pattern za key_features testovi (I-iter3-5):**

`Product.clean()` validira OBA: base accessor (`self.key_features`) I sve translated varijante (`key_features_sr/_hu/_en`). Kada je active language `sr` (default), base accessor proxy-uje na `key_features_sr` kroz modeltranslation descriptor — pa `ValidationError.message_dict` sadrži OBA ključa (`"key_features_sr"` I `"key_features"`).

TEA testovi MORAJU asertovati preko `in` operatora (membership), NE preko equality:

```python
import pytest
from django.core.exceptions import ValidationError

with pytest.raises(ValidationError) as exc_info:
    product.full_clean()
assert "key_features_sr" in exc_info.value.message_dict   # ✅ membership
# NE: assert exc_info.value.message_dict == {"key_features_sr": [...]}  # ❌ may fail
```

Razlog: belt-and-suspenders dizajn (kovers programmatic `.key_features = [...]` set bez `activate()` konteksta) generiše dual-key entry u `message_dict`. Test koji koristi equality assertion će fluktuirati u zavisnosti od locale state-a u test setupu — koristi `in` membership uvek.

Test `test_product_key_features_max_3_enforced_on_translated_variants` (AC13) MORA pratiti membership pattern (NE equality). Isti pattern važi i za `test_product_key_features_non_list_raises_on_translated_variants`.

### Previous story intelligence (from 2-1)

Story 2.1 je uvela kanonske pattern-e koje 2.2 mora striktno da prati:

**Pattern A — `save()` + `full_clean()` override sa slug auto-gen (CRIT-2 iter-2 fix):**
```python
def full_clean(self, *args, **kwargs):
    """Auto-generate slug iz name PRE Django field-level validation.

    ⚠️ NIKAD ne pozivaj self.clean() direktno (I10) — super().full_clean()
    to već radi automatski; double-poziv → duplikat ValidationError.
    """
    if not self.slug and self.name:
        self.slug = slugify_ascii(self.name)
    super().full_clean(*args, **kwargs)

def save(self, *args, **kwargs):
    """Auto-generate slug iz name + full_clean() pre super().save()."""
    if not self.slug and self.name:
        self.slug = slugify_ascii(self.name)
    self.full_clean()
    super().save(*args, **kwargs)
```
**⚠️ Ne refaktoriši — duplikacija slug auto-gen logike između `save()` i `full_clean()` je NAMERNI defensive pattern iz 2.1 (I5). Story 2.1 Pattern A omogućava caller-ima da pozovu `full_clean()` na unsaved instance bez slug-a i validacija prolazi; `save()` path zadržava single source of truth za slug auto-gen pri DB persist-u. Tests u AC13 verify oba puta nezavisno.**

**2.2 implikacija:** `Product` (jedini model sa slug-om) MORA imati OBA override-a. Ostala 6 modela nemaju slug pa ovo ne važi.

**Pattern B — TextChoices za enum polja sa locale-aware labels:**
```python
class ChoiceName(models.TextChoices):
    KEY_A = "key_a", _("Label A")
    KEY_B = "key_b", _("Label B")
```
**2.2 implikacija:** `ConditionChoice`, `StatusChoice`, `SpecSection` — sve kao nested TextChoices unutar `Product`/`ProductSpecification` klase (Decision D6 2.1 pattern).

**Pattern C — Meta.indexes sa eksplicitnim imenima `<table>_<columns>_idx`:**
```python
indexes = [
    models.Index(fields=[...], name="products_<concept>_idx"),
]
```
**2.2 implikacija:** Sva imena indeksa počinju sa `products_` prefiksom; matches 2.1 `brands_*` konvencija. Ako modeltranslation `patch_indexes` generiše dodatne 3 variante za translated fields i name-ovi prelaze 30-char Django limit (UserWarning at startup), ovo je acceptable — Story 2.x cleanup TODO iz 2.1 može refactor-ovati.

**Pattern D — Cross-app FK string lazy reference:**
```python
brand = models.ForeignKey("brands.Brand", on_delete=models.PROTECT, related_name="products")
```
**2.2 implikacija:** Brand/Series/Subcategory FK-ovi u Product koriste string. ProductImage FK ka Product u istom modulu — direktan name reference.

**Pattern E — translation.py struktura:**
```python
from modeltranslation.translator import TranslationOptions, register
from apps.<app>.models import ModelA, ModelB

@register(ModelA)
class ModelATranslationOptions(TranslationOptions):
    fields = ("field1", "field2")
```
**2.2 implikacija:** Apsolutni import (per Story 2.1 pattern — relativni `from .models import ...` je dozvoljen u istom app-u per project-context.md § Imports, ali 2.1 je biralo apsolutne za eksplicitnost; 2.2 prati istu konvenciju); 6 registracija; ProductSimilar IZUZET (nema translatable polja).

**Pattern F — User-facing strings kroz `gettext_lazy as _`:**
- Sva `verbose_name`, `verbose_name_plural`, TextChoices labels, ValidationError messages.
- NIJEDAN hardcoded srpski string bez `_()` wrap-a.
- NIJEDNA ćirilica u izvornom kodu.

**Pattern G — Migration discipline:**
- makemigrations → MANUAL REVIEW → migrate --plan → migrate → commit atomic
- Backend-agnostic asercije (CRIT-4) — `models.JSONField` literal, NE `jsonb` SQL type

**Pattern H — `@pytest.mark.skip(reason="URLs come in Story X.Y")` za get_absolute_url testove** (per BR-4 prescribed pattern).

**Pattern I — admin.py stub minimum:**
```python
from django.contrib import admin
from apps.<app>.models import <Models>

admin.site.register(<Model>)
```
Bez `list_display`, `list_filter`, `search_fields`, `inlines` — pun admin je Epic 8 scope.

**Lessons learned iz 2.1:**
- `str.maketrans(dict)` zahteva single-character ključeve (Gotcha BR-14) → već rešeno u `apps/core/utils.py slugify_ascii`; 2.2 samo koristi helper
- modeltranslation može generisati spurious migracije za druge app-ove ako INSTALLED_APPS order pogrešan (Gotcha BR-2) → 2.2 verifikuje pre makemigrations da `apps/core/translation.py` + `apps/brands/translation.py` nemaju new @register entry-je (regression check)
- `Subcategory.bulk_create()` obilazi `full_clean()` (Gotcha BR-10) → 2.2 ne radi bulk_create u smoke testu; Story 9.7 fixtures moraju iteriravanje + save()

### Decisions log

**Decision PR-D1 — `apps.products` MORA biti POSLE `apps.brands` u INSTALLED_APPS (APENDOVAN, NE reorder)**

- **Razlog:** `apps.products.models.Product` referencira `"brands.Brand"`, `"brands.Series"`, `"brands.Subcategory"` (string lazy FK). Iako string reference omogućava lazy app loading, INSTALLED_APPS order odražava conceptual dep graph; products zavisi od brands → mora biti registrovan kasnije.
- **Story 2.1 prerequisite (CRIT-iter4-1):** Story 2.1 Decision D2 / Gotcha BR-2 zahteva da `modeltranslation` bude **PRVI** u `INSTALLED_APPS` (PRE `django.contrib.admin`) — `AppConfig.ready()` modeltranslation paketa patch-uje admin i mora da se dogodi pre nego što admin registruje svoje widget-e. Story 2.2 SAMO umeće `"apps.products"` POSLE `"apps.brands"`, **NE reorder-uje postojeći redosled**. Live `config/settings/base.py` (verifikovan posle Story 2.1) ima sledeći redosled: `modeltranslation → django.contrib.{admin,auth,contenttypes,sessions,messages,staticfiles} → django_htmx → django_bootstrap5 → apps.core → apps.brands`. Story 2.2 diff je TAČNO jedna apendovana linija na kraj.
- **Alternativa razmatrana:** Direktan import `from apps.brands.models import Brand` u products.models — odbačeno jer string lazy reference je Django convention i sprečava circular import potencijal u future stories (forms može importovati Product koji importuje Brand etc.).
- **Implikacija:** Future domain apps (catalog u 2.6+, blog u 5.x, forms u 4.x) moraju biti POSLE products + brands u INSTALLED_APPS ako referenciraju Product/Brand. `modeltranslation`-first invariant je permanentan dok god projekat koristi modeltranslation paket.

**Decision PR-D2 — `Product.series` je nullable (`null=True, blank=True`)**

- **Razlog:** Epics.md spec u Story 2.2 ne kvalifikuje da svi proizvodi moraju imati seriju. Realistično, Jeegee priključna mehanizacija nema "series" koncept (samo Category → Subcategory chain). HZM utovarivači imaju Subcategory ali ne uvek Series. Forcing required Series field zahtevao bi "fake" series za sve non-tractor proizvode.
- **Alternativa razmatrana:** Required Series sa default "ostalo" series po brand-u — odbačeno (admin overhead, data quality lie).
- **Implikacija:** Story 2.6 Brand listing query mora handle-ovati `Product.series IS NULL` slučaj — neki proizvodi prikazani van series grupisanja ("Ostalo" sekcija ili flat list).

**Decision PR-D3 — `Product.subcategory` je nullable (`null=True, blank=True`)**

- **Razlog:** Top-tier traktori (npr. flagship modeli) idu direktno pod Category "Traktori" bez Subcategory drill-down. FR-7 dozvoljava top-tier traktore koji idu direktno pod Category "Traktori" bez Subcategory drill-down [Source: _bmad-output/planning-artifacts/epics.md#FR-7] (I12 — tightened citation). Mehanizacija granular taksonomija zahteva Subcategory; traktori ne.
- **Implikacija:** Story 2.8 Tractor listing query koristi `Product.subcategory IS NULL OR Product.subcategory.category.is_for=TRAKTORI` filter; Story 2.11 Subcategory listing koristi `Product.subcategory IS NOT NULL` filter.

**Decision PR-D2+D3 combined — Product može imati NULL series I NULL subcategory istovremeno (orphan product attached samo na Brand) — I9**

- **Razlog:** PR-D2 nezavisno dozvoljava NULL series; PR-D3 nezavisno dozvoljava NULL subcategory. **Kombinacija nije dodatno zaštićena** (no CHECK constraint koji zahteva barem jedno od dvoga) — Product može biti vezan SAMO za Brand, bez Series ili Subcategory. Ovo je svesno design choice za edge case: brand-only proizvodi (npr. korporativni demo unit, "uskoro" placeholder) koji još nemaju taksonomijsku poziciju.
- **Implikacija za downstream listing strane (2.6 Brand listing, 2.8 Tractor listing):**
  - **Brand listing (2.6):** Brand-only proizvodi (no series, no subcategory) prikazuju se u "Ostalo" / unkategorizovan flat list sekciji; section header se skipuje kada su oba polja NULL.
  - **Tractor/Used listing (2.8/2.9):** Filter logika mora handle-ovati edge case `series IS NULL AND subcategory IS NULL` gracefully.
- **Test scope:** NIJE dodano u 2.2 (model-layer story); view-layer test prepušta se Story 2.6/2.8 SM ticketima.
- **Story 2.7 implikacija (I-iter3-7):** Breadcrumb path u Product Detail strani (Story 2.7) mora gracefully handle-ovati both-NULL slučaj — kada su `product.series` I `product.subcategory` oba NULL, breadcrumb collapse-uje na samo `Home → Brand → Product` (preskoči Series i Subcategory linkove). SM ticket za Story 2.7 dobija ovaj flag kao prerequisite (foundation note, NE 2.2 fix; Story 2.2 model layer je već korektan — view-layer rendering je 2.7 obaveza).

**Decision PR-D4 — Paralelna polja `is_published` (Bool) i `status` (TextChoices) — YAGNI tenzija acknowledged**

- **Razlog:** Epics.md spec eksplicitno traži OBA polja (`is_published flag` + `status choice [draft/published/archived]`). YAGNI bi reklo "izaberi jedno" — ali spec is spec.
- **Konvencija (Story 8.6 admin enforce-uje):** `is_published=True` ↔ `status=PUBLISHED`. `is_published` je quick filter za listing query (boolean indexed scan brži od TextChoices); `status` je workflow state (može dodati ARCHIVED bez breaking is_published filter).
- **2.2 implikacija:** OBA polja postoje sa default-ima (`is_published=False`, `status=DRAFT`). Sync logika je view-layer/admin-layer concern (NE model.save() override) — Story 8.6 admin form `save()` može sync-ovati ova polja kroz `model.is_published = (model.status == StatusChoice.PUBLISHED); model.save()`.
- **Alternativa razmatrana:** `is_published` property `(self.status == PUBLISHED)` — odbačeno jer property je read-only; admin ne može filter-ovati po property (mora field).

**Decision PR-D5 — `ProductSimilar` je directional (NE auto-simetrična); related_name je `outgoing_similars` / `incoming_similars` (I11 rename)**

- **Razlog (directionality):** FR-20 hibrid logika ("ako ProductSimilar set nije prazan koristi manual, inače auto po brendu/seriji") implicira manual override može biti asimetričan. Primer: za traktor TB-804 admin može preporučiti priključni plug; ali za plug ne mora obrnuto preporučiti traktor.
- **Razlog (related_name nazivi — I11):** Prethodno `similar_set_from` / `similar_set_to` je bilo awkward — `_set_*` prefix podseća na default `_set` reverse manager, suffix `_from`/`_to` je dvosmislan u QuerySet kodu. `outgoing_similars` / `incoming_similars` su semantički eksplicitni: `product.outgoing_similars.all()` čita "similar entry-ji KOJI POLAZE OD ovog proizvoda" (source); `product.incoming_similars.all()` čita "similar entry-ji KOJI POKAZUJU NA ovog proizvoda" (target). Story 2.7 view-layer može pisati `product.outgoing_similars.all()` i `product.incoming_similars.all()` bez confusion-a.
- **Implikacija:** Admin u Story 8.6 mora ručno kreirati DVA entry-ja za simetričnu preporuku. Inline widget može imati "Create reciprocal" checkbox kao convenience, ali model layer ne automatski reciprocates.
- **CHECK constraint** sprečava `product == related_product` (self-reference); `UniqueConstraint(product, related_product)` sprečava duplikat pair; oba constraints su enforced na DB nivou.

**Decision PR-D6 — Out-of-scope items su EKSPLICITNO deferred (no scope creep)**

**Interpretation note za search_vector defer (IMP-iter4-7):** epics.md Story 2.13 line 697 fraza "sa search_vector field-om dodatim u migraciji" je ambigvalentna — može se čitati kao (a) field već postoji iz 2.2 migracije, ili (b) field stiže u 2.13 sopstvenoj migraciji. Story 2.2 BIRA interpretaciju (b) jer:

1. `search_vector` zahteva Postgres-specific `SearchVectorField` iz `django.contrib.postgres.search` — narušava 2.1 CRIT-4 backend-agnostic constraint (SQLite dev/CI ne podržava).
2. Migracija u 2.13 omogućava `SeparateDatabaseAndState` pattern za GIN index creation bez touchanja 2.2 scheme.
3. Story 2.13 scope eksplicitno uključuje "search_vector field-om dodatim u migraciji" — vlasništvo je jasno na 2.13 strani.

Reviewer napomena: ako se buduća revizija epics.md menja na "search_vector field MORA postojati iz 2.2", potreban je novi Decision i back-port migration.

Sledeće NE pripadaju Story 2.2 — bilo koji pokušaj implementacije je out-of-scope rejection:
- **`search_vector` polje** → Story 2.13 dodaje kroz `apps/products/migrations/0002_*.py` (zasebna migracija; vidi interpretation note iznad)
- **MIME validation** za `main_image`, `ProductImage.image`, `ProductVariant.image`, `ProductTestimonial.photo` → Story 2.3 (Image Pipeline) uvodi `apps/media_pipeline/utils.py validate_image_mime()`
- **MIME validation** za `ProductBrochure.pdf_file` → Story 2.4 (PDF Cover Thumbnail)
- **`post_save` signal** za auto-generation `ProductBrochure.cover_thumbnail_image` → Story 2.4 (`apps/media_pipeline/signals.py`)
- **`sorl-thumbnail` configuration** + `<picture>` srcset template helper → Story 2.3
- **Custom managers** (`PublishedProductManager`, etc.) → **Story 2.6 (Brand Listing Strana sa Grid/Extended Layout-om)** je owner za `apps/products/managers.py` kreiranje (verifikovano u epics.md line 596); 2.2 ostavlja `apps/products/managers.py` ne-kreiran (startapp ga ne generiše).
- **Views, URLs, forms, templates** → Story 2.7 (Product Detail), 2.8/2.9 (Listings), 8.6 (Admin)
- **Admin customization** (list_display, inlines, color picker, image preview) → Story 8.6
- **Factory_boy fixtures** → potential Story 9.7 (sample seed data); Story 2.2 koristi inline `Model.objects.create()` u smoke test

**Implikacija:** Code review (Step 04) MORA verifikovati da 2.2 implementacija nema nijednu od gore-navedenih dodataka. Scope creep = reject.

**Decision PR-D7 — Translation scope expansion: 6 entiteta / 11 polja (vs 4 entiteta / 9 polja u epics.md liniji 551) — CRIT-iter4-2**

- **Spec u epics.md (line 551):** translation.py registracija za `name`, `description`, `key_features` (Product), `key/value` (ProductSpecification), `title` (ProductBrochure), `quote/location` (ProductTestimonial) — 4 entiteta, 9 polja.
- **Story 2.2 odluka:** PROŠIREN scope na **6 entiteta, 11 polja** — dodato:
  - `ProductImage.alt_text` (CharField, translatable) — razlog: project-context.md § A11y must-haves item 4 ("Alt text na svim slikama"); deskriptivni alt-tekst po lokalu (npr. "Traktor TB-804 sa frontalnom kantom" u sr vs "Tractor TB-804 with front loader" u en) je obavezan za WCAG 2.1 AA i SEO image-alt indexing.
  - `ProductVariant.name` + `ProductVariant.description` (CharField + TextField, translatable) — razlog: varijante kao "Sa kabinom" / "Bez kabine" / "AC paket" su user-facing string-ovi koje korisnik vidi u Lightbox zoom card-u (Story 2.7); HU "Fülkével" / EN "With cab" su neophodne za multi-locale catalog.
- **NE dodato:** `ProductVariant.code` (SKU/interni kod — ne prevodi se), `ProductTestimonial.author_name` (lično ime — ne prevodi se), `ProductSpecification.section` (TextChoice — labelovi su locale-aware preko `gettext_lazy` choices, nije potreban translation.py).
- **Posledice za downstream stories:**
  - Story 2.7 (Product Detail): Lightbox zoom card za ProductVariant koristi `variant.name` + `variant.description` (locale-aware).
  - Story 8.6 (Product CRUD admin): `TranslationAdmin` tabovi za ProductVariant + ProductImage admin formi (3 dodatna tab seta per model).
  - Migracija: 11 translatable polja × 3 jezika = 33 dodatne kolone u `0001_initial.py` (verifikovano u AC10 per-field counts).
- **Alternative razmatrane i odbačene:**
  - Striktno pratiti epics.md (4 modela) → odbačeno: a11y i variant rendering bi morali da se popravljaju kao spec deficit u 2.7 i 2.3 (cycle work).
  - Defer expansion na 2.7 (kad treba) → odbačeno: kasnije dodavanje translation polja na postojeći migration-ovan model = nova migracija + edge cases sa default vrednostima na produkciji.
- **Source citations:** [Source: _bmad-output/planning-artifacts/epics.md#story-22 (line 551 — original 4-model spec)], [Source: _bmad-output/project-context.md#a11y-must-haves item 4 — alt text na svim slikama], [Source: _bmad-output/planning-artifacts/epics.md#story-27 (line 619 — variant card UX rationale)].

### Gotchas log

**Gotcha PR-1 — `ProductsConfig.name` MORA matchovati INSTALLED_APPS entry**

- **Problem:** Django startapp default generiše `name = "products"` (bez `apps.` prefiksa). `INSTALLED_APPS` u `config/settings/base.py` mora imati `"apps.products"`. Nekonzistentni → `RuntimeError: Conflicting 'products' models in application` ili `LookupError: No installed app with label 'apps.products'`.
- **Fix:** Eksplicitno postaviti `name = "apps.products"` u `ProductsConfig` (Task 1.3). Matches 2.1 Gotcha BR-1 pattern.

**Gotcha PR-2 — modeltranslation može generisati spurious migracije**

- **Problem:** Ako se pri `makemigrations` apps/core/translation.py ili apps/brands/translation.py imaju nove `@register` entry-je koje nisu pre Story 2.2 commit-ovane, modeltranslation će generisati migracije za TE app-ove takođe. To NE pripada 2.2 scope-u.
- **Fix:** Pre Task 4.2 (makemigrations), verifikovati:
  - `apps/core/translation.py` nema aktivnih `@register` (regression — Story 1.x je samo placeholder)
  - `apps/brands/translation.py` ima TAČNO 4 `@register` entry-ja (Brand, Series, Category, Subcategory iz 2.1) i ništa više
  - `uv run python manage.py makemigrations --dry-run` output lista SAMO `products` app
- **Recovery ako se ipak generišu spurious migracije:** revert generated files, debug uzrok, retry.

**Gotcha PR-3 — Image polja BEZ MIME validacije u 2.2 (defer to 2.3)**

- **Problem:** `Product.main_image`, `ProductImage.image`, `ProductVariant.image`, `ProductTestimonial.photo` su `ImageField` koji Django validuje extension + Pillow open-check, ALI NE MIME signature ili magic byte. Per project-context.md § Anti-pattern: File upload bez double-check, ovo je security risk za production.
- **Trenutna mitigacija (Story 2.2):** Polja su `blank=True, null=True` osim `ProductImage.image` (REQUIRED, ali galerija je curated by admin u Epic 8). Admin u 2.2 je SAMO Mihas (sole admin) — acceptable risk. Editor role onboarding (Epic 8) BLOCKED dok Story 2.3 ne lansira (matches 2.1 Decision D14 sequencing).
- **Story 2.3 obavezno dodaje:**
  - `apps/media_pipeline/utils.py validate_image_mime()` koji koristi Pillow `Image.verify()` + `python-magic` MIME signature check
  - ImageField `clean_<field>()` override-i u form layer (NE u model layer — model layer ostaje thin)
- **TODO komentar u models.py header dokumentuje ovo** (matches 2.1 Decision D14 pattern).

**Gotcha PR-4 — `ProductBrochure.pdf_file` BEZ MIME validacije u 2.2 (defer to 2.4)**

- **Problem:** `FileField` Django validuje ekstenziju samo. PDF malware (npr. embedded JavaScript) ili masked .exe sa `.pdf` extension može proći.
- **Trenutna mitigacija (Story 2.2):** Mihas-only admin upload phase; trust-by-admin (single-trust).
- **Story 2.4 obavezno dodaje:** Magic byte check za `%PDF-` prefix + PyMuPDF parse validation u `apps/media_pipeline/utils.py validate_pdf_file()`.
- **Reference:** matches 2.1 Decision D14 sequencing constraint (Editor role onboarding gate).

**Gotcha PR-5 — `Product.get_absolute_url()` raise-uje `NoReverseMatch` u 2.2 (URLs come in 2.7)**

- **Problem:** Test koji direktno poziva `product.get_absolute_url()` raise-uje `NoReverseMatch: Reverse for 'detail' not found...` (matches 2.1 Gotcha BR-4 pattern).
- **PRESCRIBED FIX:** TEA MORA koristiti `@pytest.mark.skip(reason="URLs come in Story 2.7 — placeholder validates method exists")` na sve `get_absolute_url()` testove. NIJE "TEA chooses" framing.
- **Alternativa:** zero-cost `assert callable(Product.get_absolute_url)` umesto actual call.
- **Defer:** Real test (sa proper reverse) stiže u Story 2.7 kada URL pattern postoji.

**Gotcha PR-6 — App boundary violation: `apps.brands` NIKAD ne sme importovati `apps.products`**

- **Problem:** Future stories (2.6 Brand listing, 8.4 Brand admin) mogu istelnučiti za convenience import `from apps.products.models import Product` u apps/brands. Ovo VIOLATES architecture.md § Zabranjene zavisnosti.
- **Fix u 2.2:** Reverse access kroz `brand.products.all()` (related_name FK reverse) je SVE što brands treba. Admin u 8.4 može koristiti `Product.objects.filter(brand=brand)` bez importing Product u brands modulu (Story 8.4 SM ticket odlučuje pattern).
- **Regression guard:** `tests/integration/test_app_boundaries.py` (TEA piše u Step 3 — I-iter3-1 lokacija) — AST static check enforce-uje. CI lint pass je obavezan.

**Gotcha PR-7 — `Product.key_features` modeltranslation registracija na JSONField**

- **Problem:** modeltranslation podržava JSON field translation, ali generiše `key_features_sr`, `key_features_hu`, `key_features_en` kao **TRI** zasebna JSONField kolona. Ako admin uredi `key_features` sa default fallback locale (sr), `key_features_hu` i `key_features_en` ostaju null. View layer mora handle-ovati locale fallback.
- **Fix u 2.2 (C3 — close the loop):**
  - **Max-3 validacija sada pokriva i translated `_sr/_hu/_en` varijante** kroz `Product.clean()` iteraciju kroz `settings.LANGUAGES` (videti AC2 snippet). Admin više ne može upisati 5 stavki u `key_features_hu` bez ValidationError.
  - **`MODELTRANSLATION_FALLBACK_LANGUAGES = ("sr",)`** je obavezan config setting (AC1 step + Task 1.4b) — locale fallback chain je deterministički sr-only umesto LANGUAGES default-a. **Rationale (IMP-iter4-1):** architecture-defensive setting per project-context.md § i18n locale fallback; NIJE FR-32 mapiranje (FR-32 je UI marker concern za Story 6.5).
- **Reference:** modeltranslation docs § Fallback configuration; AC2 `Product.clean()` snippet; AC13 `test_product_key_features_max_3_enforced_on_translated_variants`.

**Gotcha PR-8 — `bulk_create()` obilazi `full_clean()` (Django ORM design — matches 2.1 BR-10)**

- **Problem:** `Product.objects.bulk_create([Product(...)])` obilazi `save()` i `full_clean()` → `key_features` max 3 validation se ne aktivira; auto-slug se ne generiše.
- **Implikacija za Story 9.7 seed data:** Iterirati listu sa `obj.save()` umesto `bulk_create()` (matches 2.1 BR-10 documented pattern).
- **2.2 scope:** Smoke test u Task 7 NE radi bulk_create — koristi `Product.objects.create()` koji prolazi kroz save() → full_clean().

**Gotcha PR-9 — `is_published` i `status` polja paralelno postoje (Decision PR-D4 acknowledgment)**

- **Problem:** Admin može save-ovati `is_published=True` sa `status=DRAFT` (inkonzistentno).
- **2.2 stance:** Acceptable u 2.2 model layer (no enforcement). Story 8.6 admin form `save()` enforce-uje sync (vidi PR-D4).
- **View layer (Story 2.6+/2.7+):** Filter koristi `is_published=True` (boolean indexed scan); ako želi striktnu filter sintaksu, koristi `status=PUBLISHED` umesto.

**Gotcha PR-10 — `ProductSimilar` UniqueConstraint + CheckConstraint backend support**

- **Problem:** PostgreSQL podržava CheckConstraint natively; SQLite (dev/CI) podržava od verzije 3.31+. Django 5.2 emit-uje SQL koji oba backend-a razumeju, ali ako CI bazira na starijoj SQLite verziji, test može raise-ovati IntegrityError sa različitom porukom.
- **Trenutna mitigacija:** Test za DB-level CheckConstraint koristi `pytest.raises(IntegrityError)` bez asertacije na konkretnu poruku (per project-context.md § Test patterns).

**Gotcha PR-11 — `admin.site.register(Product)` NE generiše modeltranslation sr/hu/en tabove (C1 trap)**

- **Problem:** modeltranslation **DOES** generiše `_sr`/`_hu`/`_en` kolone u DB čim je `translation.py` registrovan — to je deklarativna model layer integracija. ALI: admin layer tabovi (sr/hu/en visual tab UI) renderuju se **SAMO** kroz `TranslationAdmin` base klasu iz `modeltranslation.admin`. Bare `admin.site.register(Product)` (default ModelAdmin) generiše **flat fields** (`name`, `name_sr`, `name_hu`, `name_en` kao 4 odvojena CharField-a u admin formi) — bez tabular tab navigation.
- **2.1 + 2.2 obe koriste bare register** (verifikovano u `apps/brands/admin.py`) — stub admin layer u model-layer story (2.1, 2.2) **NE renderuju tabove**. To je svesno scope choice: pun `TranslationAdmin` sa color picker, image preview, inlines, i tab UI je **Story 8.6 (Product CRUD)** scope.
- **Šta to znači za 2.2 acceptance:** AC11 NE sme tvrditi da "modeltranslation tabovi se renderuju u admin formi". AC11 tekst sada eksplicitno kaže "tabovi se NE renderuju u stub admin formi; pun TranslationAdmin u Story 8.6".
- **Fix u Story 8.6:** `from modeltranslation.admin import TranslationAdmin`; `class ProductAdmin(TranslationAdmin): ...`; `admin.site.register(Product, ProductAdmin)`. Tabovi tada renderuju automatski.

**Gotcha PR-13 — `Product.save()` slug auto-gen NEMA suffix counter (slug collision = IntegrityError)**

- **Problem:** Dva `Product`-a sa identičnim `name` → identičan slug kroz `slugify_ascii(name)` → `IntegrityError` na `SluggedModel.slug unique=True` constraint-u pri DB persist-u. `Product.save()` NE radi suffix counter retry (npr. `tb-805-2`, `tb-805-3`, ...) — naivno postavlja `self.slug = slugify_ascii(self.name)` jednom i delegira super().save() koji raise-uje IntegrityError ako collision postoji.
- **Inherited iz Story 2.1:** Isti pattern u `Brand/Series/Category/Subcategory.save()` — 2.1 design choice (no suffix counter).
- **2.2 stance:** Admin-curated unique-ness u v1 (Mihas-only admin može videti grešku i ručno setovati slug). **Suffix counter (`tb-805-2`) je out-of-scope za 2.2 i NIJE planiran** ni u 8.6 admin layer-u (može biti TODO za Story 9.x ako se ukaže potreba).
- **Implikacija za bulk fixture import (Story 9.7):** Sample seed data mora pre-dedup-ovati nazive ili ručno postaviti `slug=` pre `obj.save()`-a. Iter-pattern `for fixture: obj.save()` će raise-ovati IntegrityError ako dva fixtura imaju isti `name`. Workaround: append `_idx` suffix u fixture loader-u.
- **Reference:** Pattern A defensive guard (vidi Dev Notes) — `save()` ne re-validira slug uniqueness pre super().save(); IntegrityError je očekivan signal, ne unhandled exception.

**Gotcha PR-14 — `ProductBrochure.pdf_file` NEMA model-level size cap u 2.2 (defer to 2.4 + 8.6)**

- **Problem:** `FileField` ne enforce-uje max size na model layer-u. Admin može upload-ovati 500 MB PDF — Postgres BinaryField overhead minor, ali storage cost balloon-uje.
- **2.2 stance:** NEMA size validacije na model layer-u. Form-level i admin-level size validacija (npr. ≤ 10 MB) odlažu se na Story 8.6 (Product CRUD admin) odnosno Epic 4 (forms layer). MIME validacija (preko `python-magic`) je Story 2.4 obaveza (vidi Gotcha PR-4).
- **Story 8.6/2.4 obavezno dodaje:** `pdf_file.clean()` form-level provera `pdf_file.size > 10 * 1024 * 1024` → ValidationError(`_("PDF brošura ne sme biti veća od 10 MB.")`).
- **Reference:** epics.md ne specifies eksplicitnu max size za PDF brošure; 10 MB je konzervativan default usklađen sa NFR-3 sigurnost (MIME validacija upload-a) + UX (Story 2.7 download experience ne sme blokirati mobilne korisnike).

**Gotcha PR-12 — Story 2.7 mora **kreirati** `apps/products/urls.py` (NE postoji posle 2.2) sa `app_name = "products"` PRE wire-ovanja URL pattern-a**

- **Problem:** `Product.get_absolute_url()` koristi `reverse("products:detail", kwargs={"slug": self.slug})`. Namespace `"products"` zavisi od `app_name = "products"` deklaracije u `apps/products/urls.py` — bez nje `reverse()` raise-uje `NoReverseMatch: 'products' is not a registered namespace`.
- **Story 2.2 scope (IMP-iter4-2 korekcija):** `apps/products/urls.py` **NE POSTOJI** posle Story 2.2 — `django-admin startapp` NE generiše `urls.py` (verifikovano protiv Django 5.2 startapp template). Story 2.2 ga svesno NE kreira (views/URLs su 2.7+ scope). `get_absolute_url()` testovi u 2.2 koriste `@pytest.mark.skip(reason="URLs come in Story 2.7")` pattern (vidi Gotcha PR-5).
- **Story 2.7 zahtev:** Story 2.7 MORA prvi put **kreirati** fajl `apps/products/urls.py` sa sledećim minimum sadržajem PRE wire-ovanja URL pattern-a:
  ```python
  from django.urls import path
  app_name = "products"  # KRITIČNO — bez ovoga reverse("products:detail") raise NoReverseMatch
  urlpatterns = [
      path("proizvod/<slug:slug>/", ProductDetailView.as_view(), name="detail"),
  ]
  ```
  Dev SM ticket za 2.7 mora eksplicitno proveriti ovo — fajl ne postoji u repository-ju dok ga 2.7 ne kreira.
- **Reference:** Django docs § URL namespaces; matches `apps/brands/urls.py` pattern koji će Story 2.6 uspostaviti (takođe novokreiran u 2.6, ne postoji posle 2.1).

### Project structure notes

- **Per project-context.md § File organization:** Django apps uvek u `apps/<appname>/`; per-app `models.py`, `admin.py`, `views.py`, `urls.py`, `forms.py`, `signals.py`, `managers.py`, `translation.py`, `tests/`, `migrations/`. **Šta `startapp` STVARNO generiše (IMP-iter4-2):** `__init__.py`, `apps.py`, `admin.py`, `models.py`, `tests.py`, `views.py`, `migrations/__init__.py` — TO JE TO. **NE generiše:** `urls.py`, `forms.py`, `managers.py`, `signals.py`, `translation.py`. Story 2.2 dodaje SAMO `translation.py` (Task 3) i `tests/__init__.py` (Task 1.2); uklanja default `views.py` (Task 1.2b) i `tests.py` (Task 1.2 — mirror 2.1 discipline). Fajlovi `urls.py`/`forms.py`/`managers.py`/`signals.py` **NE POSTOJE posle 2.2** — kreiraju ih 2.6/2.7/8.6 SM ticketi kad zatreba.
- **Per project-context.md § Imports:** Apsolutni preferred; relativni dozvoljeni samo unutar app-a. Story 2.2 koristi apsolutni `from apps.core.models import ...` i `from apps.products.models import ...` u translation.py.
- **Per project-context.md § Django models:** FK explicit `on_delete` + `related_name`; Meta.indexes sa imenima; `get_absolute_url` na content modelima.
- **Per project-context.md § Migrations discipline:** makemigrations → manual review → migrate --plan → migrate → commit atomic.
- **Per project-context.md § Anti-pattern: Cross-boundary import:** `brands ← products` jednosmerno; `products ← catalog` (future); `core ← everyone`.
- **Per architecture.md § App boundaries (lines 720-733):** `brands ← products, catalog` (products zavisi od brands); `core ← (everyone imports core)`. Story 2.2 je drugi nivo u lancu.

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#pattern-examples (lines 470-505)] — Product model gold reference (slug, FK Brand PROTECT, is_published, Meta.indexes, get_absolute_url)
- [Source: _bmad-output/planning-artifacts/architecture.md#architectural-boundaries (lines 716-740)] — App dependency graph + zabranjene zavisnosti
- [Source: _bmad-output/planning-artifacts/architecture.md#complete-project-tree (lines 573-580)] — `apps/products/` directory layout
- [Source: _bmad-output/planning-artifacts/epics.md#story-22 (lines 543-554)] — original story spec + AC list
- [Source: _bmad-output/planning-artifacts/epics.md#story-23 (lines 556-567)] — Story 2.3 dependency (image pipeline za main_image/ProductImage)
- [Source: _bmad-output/planning-artifacts/epics.md#story-24 (lines 569-580)] — Story 2.4 dependency (PDF cover thumbnail signal)
- [Source: _bmad-output/planning-artifacts/epics.md#story-27 (lines 611-622)] — Story 2.7 dependency (Product Detail koristi sva 7 modela)
- [Source: _bmad-output/planning-artifacts/epics.md#story-213 (lines 691-706)] — Story 2.13 dependency (search_vector polje deferred)
- [Source: _bmad-output/planning-artifacts/epics.md#FR-7] — Top-tier traktori idu direktno pod Category "Traktori" bez Subcategory drill-down (Decision PR-D3 citation; I12)
- [Source: _bmad-output/project-context.md#i18n-locale-fallback] — "sr je default; ako neki prevod nedostaje → fallback na sr" (MODELTRANSLATION_FALLBACK_LANGUAGES architecture-defensive rationale; C3; IMP-iter4-1)
- [Source: _bmad-output/project-context.md#a11y-must-haves] — Alt text na svim slikama (Decision PR-D7 citation za ProductImage.alt_text translatable; CRIT-iter4-2)
- [Source: _bmad-output/planning-artifacts/epics.md#FR-32] — Forward link: Story 6.5 UI fallback marker se gradi NA VRHU 2.2 backend foundation (NIJE 2.2 ownership; IMP-iter4-1 reattribution)
- [Source: _bmad-output/project-context.md#django-models] — base klase, FK on_delete, related_name, Meta.indexes, get_absolute_url konvencije
- [Source: _bmad-output/project-context.md#migrations-discipline] — makemigrations workflow + manual review
- [Source: _bmad-output/project-context.md#test-discipline] — TEA piše testove, Dev NIKAD ne piše testove
- [Source: _bmad-output/project-context.md#anti-patterns] — ćirilica, hardcoded strings, defensive validation, cross-boundary import
- [Source: _bmad-output/implementation-artifacts/2-1-brand-series-category-subcategory-modeli.md] — kanonski model pattern (save/full_clean override sa slug auto-gen; TextChoices; Meta.indexes naming; gettext_lazy discipline; migration manual review procedura; @pytest.mark.skip pattern za get_absolute_url; SluggedModel + TimestampedModel mixin u apps/core/models.py kao FOUNDATION za 2.2)

## Dev Agent Record

### Agent Model Used

_(Dev agent populates posle implementacije)_

### Debug Log References

_(Dev agent populates)_

### Completion Notes List

_(Dev agent populates)_

### File List

_(Dev agent populates)_

---

**End of Story 2.2**
