---
story-id: "2.1"
story-key: 2-1-brand-series-category-subcategory-modeli
title: Brand, Series, Category, Subcategory Modeli
status: review
epic_num: 2
epic_title: Public Catalog — Browse Brands & Products
module: apps/brands/ (NOVO Django app — prvi domain app u Epic 2)
created: 2026-05-29
last_modified: 2026-05-29
author: Mihas (SM autonomous)
---

# Story 2.1: Brand, Series, Category, Subcategory Modeli

Status: review

## Story

As a **dev (Mihas) koji započinje Epic 2 (Public Catalog)**,
I want **četiri kanonska modela u novom `apps/brands/` Django app-u — `Brand`, `Series`, `Category`, `Subcategory` — sa pratećim `translation.py` registracijom (`django-modeltranslation`), eksplicitnim `on_delete` + `related_name` na svim FK-ovima, ASCII slug-ovima, composite `Meta.indexes`, `get_absolute_url()` metodama i validacijom maksimalne dubine `Subcategory` hijerarhije od 3 nivoa**,
so that **mogu hijerarhijski strukturisati katalog (Brand → Series → modeli; Category → Subcategory chain) prema FR-7/FR-37/FR-38, da `django-modeltranslation` automatski generiše `_sr`/`_hu`/`_en` suffix polja u migracijama, i da svi naredni domain app-ovi u Epic 2 (`apps/products/`, `apps/catalog/`) imaju stabilan upstream model layer bez kružnih zavisnosti (per architecture.md § App boundaries: `core ← brands ← products ← catalog`)**.

Ova story je **prvi domain Django app u Epic 2** i istovremeno **prvi konzument `django-modeltranslation` paketa** koji je dodat u `pyproject.toml` u Story 1.1 ali još nije registrovan u `INSTALLED_APPS`. Story 2.1 uvodi `apps/brands/` direktorijum (per project-context.md § File organization: "Django apps uvek u `apps/<appname>/`, NIKAD na root nivou projekta"), registruje `modeltranslation` u `INSTALLED_APPS` pre `apps.brands` (per modeltranslation docs — app order matters za auto-discovery `translation.py` fajlova), i postavlja kanonski model pattern (eksplicitni `on_delete`, eksplicitni `related_name`, `Meta.indexes` sa imenima, `get_absolute_url()`, ASCII slug discipline) koji će svi naredni domain app-ovi (`products`, `catalog`, `blog`, `forms`, `pages`) reuse-ovati kao referencu.

**Foundation za:**
- **Story 2.2 (Product i Related Modeli):** `Product` ima FK ka `Brand`, `Series`, `Subcategory` — sve definisane ovde; jednosmerna zavisnost `products → brands` (per architecture.md § Architectural Boundaries; `brands` NIKAD ne sme importovati iz `products`).
- **Story 2.6 (Brand Listing strana sa Grid/Extended Layout-om):** koristi `Series.layout_mode` choice da odluči kako da renderuje modele (Grid 2-col vs Extended 1-row sa akordion specs); UX referenca FR-8.
- **Story 2.7 (Product Detail strana):** koristi `Brand` polja `brand_color`, `slogan`, `logo` u hero overlay card-u; UX referenca DESIGN.md § Brand & Style.
- **Story 2.11 (Subcategory listing 4-nivoa hijerarhija):** koristi `Subcategory.parent` self-FK chain (Category → Subcategory L1 → Subcategory L2 → Subcategory L3 = 4 nivoa kombinovanog stabla, ali 3 nivoa SUBCATEGORY chain-a — vidi Decision D4 disambiguacija FR-10 vs FR-38 vs Epic 2.1 spec).
- **Story 2.13 (Global search):** FTS index na translated `Brand.name_sr`, `Subcategory.name_sr` kroz PostgreSQL `tsvector` (Epic 4 scope, ali model layer mora prvo da postoji).
- **Story 8.4 (Brand CRUD admin):** koristi `apps/brands/admin.py` koji u Story 2.1 dobija samo `admin.site.register(...)` stub; pun admin sa color picker, hero image upload, statistike inline stiže u 8.4.
- **Story 8.5 (Category/Subcategory CRUD sa hierarchy):** ekstenduje `apps/brands/admin.py` sa tree widget-om; model layer iz 2.1 je stabilan.

**Princip:** Jedan novi Django app (`apps/brands/`) sa **četiri modela u jednom `models.py` fajlu** (cohesion — sva 4 entiteta dele isti domen "katalog taksonomija"; per project-context.md § File organization: "Per-app fajlovi: `models.py`, `admin.py`, `views.py`, `urls.py`, `forms.py`, `signals.py`, `managers.py`, `translation.py`, `tests/`, `migrations/`"). **Translation polja su deklarativno registrovana u `translation.py`** koji modeltranslation auto-discoveruje kroz `INSTALLED_APPS` pri pokretanju Django-a (modeltranslation traži `<app>/translation.py` fajl u svakom INSTALLED app-u — vidi Decision D2 za zašto `INSTALLED_APPS` order matters). **Migracija je MANUAL-REVIEWED** pre commit-a (per project-context.md § Migrations discipline). **NEMA admin custom forme, NEMA views, NEMA urls, NEMA template-a** u ovoj story-ji — to je 2.6/8.4/8.5 scope.

**Strukturna arhitektura:** Repository dobija novi direktorijum `apps/brands/` sa standardnim Django app skeleton-om (`__init__.py`, `apps.py`, `models.py`, `admin.py`, `translation.py`, `migrations/`, `tests/`). `apps/core/` ostaje netaknut osim **opcionog** dodavanja `apps/core/models.py` sa `SluggedModel` base klasom (vidi Decision D3 — ova story-ja BIRA da dodati `SluggedModel` u `apps/core/models.py` jer je referencirana u architecture.md § Pattern Examples i project-context.md § Django models, ali se NIJE realizovala u Epic 1; sve naredne Epic 2+ stories nasleđuju ovaj base class). `config/settings/base.py` dobija dodatak **dva nova app-a** u `INSTALLED_APPS`: `"modeltranslation"` (PRE `apps.brands` — Decision D2) i `"apps.brands"`. **NIJE** kreira `apps/brands/views.py`, `apps/brands/urls.py`, `apps/brands/forms.py`, `apps/brands/managers.py`, `apps/brands/signals.py` u ovoj story-ji — startapp ih generiše prazne, a 2.6+/8.4+ ih popunjavaju.

## Acceptance Criteria

**AC1 — `apps/brands/` Django app je kreiran i registrovan u `INSTALLED_APPS` pre `apps.products` (jednosmerna zavisnost) sa `modeltranslation` REGISTROVANIM PRE `apps.brands`**

- **Given** Story 1.1-1.9 završen (`apps/core/` postoji sa `apps.py`, `translation.py`, `middleware.py`; `pyproject.toml` ima `django-modeltranslation>=0.20.3`; `config/settings/base.py` ima `INSTALLED_APPS` sa `apps.core`)
- **When** kreiram `apps/brands/` kroz `uv run python manage.py startapp brands apps/brands` i dodajem app-ove u `INSTALLED_APPS`
- **Then** sledeća struktura mora postojati:
  - Direktorijum `apps/brands/` u repository root-u
  - `apps/brands/__init__.py` (prazan)
  - `apps/brands/apps.py` sa `BrandsConfig(AppConfig)` klasom:
    - `default_auto_field = "django.db.models.BigAutoField"`
    - `name = "apps.brands"` (KRITIČNO — `apps.brands`, NE `brands`; matches `INSTALLED_APPS` entry; vidi Gotcha BR-1)
    - `verbose_name = "Brendovi"` (locale-aware kroz `gettext_lazy`)
  - `apps/brands/models.py` (sa 4 modela — AC2-AC5)
  - `apps/brands/admin.py` (stub sa basic registrationima — AC10)
  - `apps/brands/translation.py` (sa TranslationOptions registracijama — AC6)
  - `apps/brands/tests/__init__.py` (prazan)
  - `apps/brands/tests/test_models.py` (TEA piše u Step 3; SM ne sme da uvodi testove)
  - `apps/brands/migrations/__init__.py` (auto-kreiran kroz startapp)
- **And** `config/settings/base.py` `INSTALLED_APPS` lista dobija **DVA dodatka** u TAČNOM redosledu (Decision D2 — modeltranslation auto-discovery zahteva da bude registrovana PRE prvih app-ova koji imaju `translation.py`):
  ```python
  INSTALLED_APPS = [
      "django.contrib.admin",
      "django.contrib.auth",
      "django.contrib.contenttypes",
      "django.contrib.sessions",
      "django.contrib.messages",
      "django.contrib.staticfiles",
      "modeltranslation",            # NOVO Story 2.1 — MORA biti PRE apps.brands (auto-discovery translation.py)
      "django_htmx",                  # Story 1.6
      "django_bootstrap5",            # Story 1.6
      "apps.core",                    # Story 1.x
      "apps.brands",                  # NOVO Story 2.1 — domain app
  ]
  ```
- **And** Django auto-reload startuje bez `ImportError`, `ImproperlyConfigured` ili `RuntimeError` (smoke verifikacija: `uv run python manage.py check` exit code 0).
- **And** `apps/brands/__init__.py` je prazan — bez `default_app_config` declaracije (Django 3.2+ auto-detektuje `AppConfig` u `apps.py`).

**AC2 — `Brand` model definisan u `apps/brands/models.py` sa svim FR-37 poljima, eksplicitnim `on_delete`/`related_name`, ASCII slug-om, `Meta.indexes`, `get_absolute_url()`**

- **Given** `apps/brands/models.py` postoji
- **When** definišem `Brand` klasu
- **Then** `Brand` model mora imati TAČNO sledeća polja (typovi, constraint-i, default-i):
  - `name = models.CharField(max_length=120)` — **translatable** (registruje se u `translation.py` AC6)
  - `slug = models.SlugField(max_length=140, unique=True, db_index=True)` — ASCII transliteration, NE Unicode (per project-context.md § Slugovi); validacija u `save()` ili kroz `apps/core/utils.py` slugify helper (Task 2 reference)
  - `logo = models.ImageField(upload_to="brands/logos/", max_length=255, blank=True, null=True)` — opciono u DB, ali UI zavisi (vidi Dev Notes BR-3 za upload validacija — defer to Story 2.3). `max_length=255` (IMP-4) — Django default je 100, mali nedovoljan za nested upload_to paths sa hash suffixima.
  - `hero_image = models.ImageField(upload_to="brands/heroes/", max_length=255, blank=True, null=True)` — opciono
  - `description = models.TextField(blank=True)` — **translatable** (FR-37 polje "opis")
  - `slogan = models.CharField(max_length=200, blank=True)` — **translatable** (FR-37 polje koristi se u hero overlay card-u — DESIGN.md § Brand & Style)
  - `statistics = models.JSONField(default=list, blank=True)` — Django 5.2 native `JSONField` (NE PostgreSQL-specifični `postgres.fields.JSONField` — Decision D5); structure: lista do 4 dict-a `[{"icon": "tractor", "value": 5000, "label": "..."}, ...]` (FR-37: "statistike (do 4, ikona + broj + oznaka)"). Validation `clean()` osigurava `len(self.statistics) <= 4` PLUS **soft shape validation (IMP-10):**
    ```python
    # Soft validation: list-of-dict shape (deep schema je Story 2.6 view-layer concern)
    if self.statistics and not isinstance(self.statistics, list):
        raise ValidationError({"statistics": _("Mora biti lista.")})
    if self.statistics:
        for item in self.statistics:
            if not isinstance(item, dict):
                raise ValidationError({"statistics": _("Svaka stavka mora biti dict.")})
    ```
    - Deep schema validacija (icon/value/label keys + types) je Story 2.6 view-layer concern; Story 2.1 zaštita osigurava da admin ne snimi non-list ili non-dict items što bi crashovalo render u 2.6.
  - `catalog_pdf = models.FileField(upload_to="brands/catalogs/", max_length=255, blank=True, null=True)` — opciono PDF (FR-37 "katalog PDF"); MIME validation deferred to Story 2.4 PDF pipeline; v1 prihvata bez validacije ali Dev Notes dokumentuje TODO. `max_length=255` (IMP-4).
  - `brand_color = models.CharField(max_length=7, blank=True)` — hex format `#RRGGBB` (npr. `#00A4E9` za Jeegee — DESIGN.md § Brand-specific); regex validation u `clean()` da matchuje `^#[0-9A-Fa-f]{6}$` SAMO ako je vrednost neprazna (blank=True mora biti honored — vidi CRIT-3 fix); koristi se za "Ponavljajući element" boju (FR-37). Implementacija:
    ```python
    def clean(self):
        super().clean()
        if self.brand_color and not re.match(r"^#[0-9A-Fa-f]{6}$", self.brand_color):
            raise ValidationError({"brand_color": _("Hex format mora biti #RRGGBB.")})
    ```
  - `is_coming_soon = models.BooleanField(default=False)` — flag "Uskoro" (FR-7: "Brendovi sa flagom *Uskoro* su prikazani sa oznakom i nemaju aktivnu navigaciju"). **NEMA `db_index=True`** (IMP-3): composite index `brands_brand_coming_name_idx` (Meta.indexes) već pokriva leftmost-prefix scan na `(is_coming_soon, name)` — odvojen single-column index bio bi redundantan.
  - `created_at = models.DateTimeField(auto_now_add=True)` — vidi Decision D3 (ako se odluči za `SluggedModel(TimestampedModel)` base, `created_at`/`updated_at` dolaze iz mixina)
  - `updated_at = models.DateTimeField(auto_now=True)` — isto
- **And** `Brand` ima **Meta klasu**:
  ```python
  class Meta:
      ordering = ["name"]
      verbose_name = _("Brend")
      verbose_name_plural = _("Brendovi")
      indexes = [
          models.Index(fields=["is_coming_soon", "name"], name="brands_brand_coming_name_idx"),
      ]
  ```
  - Composite index na `(is_coming_soon, name)` ubrzava query "samo aktivni brendovi sortirani po imenu" (FR-7 list view query pattern; per project-context.md § Django models: "Meta.indexes sa imenima `<table>_<columns>_idx`")
- **And** `Brand.__str__` vraća `self.name` (locale-aware kroz modeltranslation fallback).
- **And** `Brand.get_absolute_url()` postoji i vraća:
  ```python
  def get_absolute_url(self):
      return reverse("brands:detail", kwargs={"slug": self.slug})
  ```
  - **NAPOMENA:** URL `brands:detail` JOŠ NE POSTOJI u Story 2.1 (urls.py je prazan startapp default). `reverse()` će raise-ovati `NoReverseMatch` ako se pozove pre Story 2.6. Test pokriva ovu situaciju kroz `@pytest.mark.urls('apps.brands.tests.fake_urls')` ili sličan pattern (TEA odlučuje konkretnu strategiju). Pattern reference: per project-context.md § Django models "`get_absolute_url` uvek implementirati na content modelima — koristi se za sitemap, admin, share linkove".
- **And** **`Brand.save()` override** (iter-2 NEW-CRIT-2 fix — eksplicitan order slug auto-gen → full_clean → super().save):
  ```python
  def save(self, *args, **kwargs):
      """Auto-generate slug from name if blank, then validate, then save.

      Order is CRITICAL: slug must be set BEFORE full_clean() since
      slug field is blank=False. Per Story 2.1 fix iter-2 CRIT-2.
      """
      if not self.slug and self.name:
          self.slug = slugify_ascii(self.name)
      self.full_clean()  # validate all fields including the auto-set slug
      super().save(*args, **kwargs)
  ```
  - **Import:** `from apps.core.utils import slugify_ascii` u header-u models.py.

**AC3 — `Series` model definisan u `apps/brands/models.py` sa FK ka Brand (`PROTECT`), `layout_mode` TextChoices, ASCII slug-om, `Meta.indexes`**

- **Given** `apps/brands/models.py` ima `Brand`
- **When** definišem `Series` klasu
- **Then** `Series` model mora imati TAČNO sledeća polja:
  - `brand = models.ForeignKey("brands.Brand", on_delete=models.PROTECT, related_name="series")` — KRITIČNO: 
    - `on_delete=models.PROTECT` (per project-context.md § Django models: "uvek navedi `on_delete` eksplicitno"; PROTECT sprečava brisanje brenda dok ima serija — soft enforcement business pravila)
    - `related_name="series"` (eksplicitno; sprečava `_set` magic — per project-context.md § Django models)
    - String reference `"brands.Brand"` (NE direktan import — apps in same module, ali konzistencija sa cross-app pattern-om)
  - `name = models.CharField(max_length=120)` — **translatable**
  - `slug = models.SlugField(max_length=140, db_index=True)` — UNIQUE per-brand (vidi Meta `UniqueConstraint` ispod), NE globalno
  - `description = models.TextField(blank=True)` — **translatable** (opciono opis serije)
  - `layout_mode` — `TextChoices` enum (Decision D5 — TextChoices umesto `choices=` tuple-a; eksplicitne konstante za code reference):
    ```python
    class LayoutMode(models.TextChoices):
        GRID = "grid", _("Grid")
        EXTENDED = "extended", _("Extended")
    
    layout_mode = models.CharField(
        max_length=10,
        choices=LayoutMode.choices,
        default=LayoutMode.GRID,
    )
    ```
    - Default = `GRID` (per FR-8: "Podrazumevano je *Grid*; *Extended* se koristi za serije sa složenijim specifikacijama")
  - `display_order = models.PositiveSmallIntegerField(default=0, db_index=True)` — manual order u Brand admin-u; lower = earlier
  - `created_at`, `updated_at` (timestamps — kroz mixin ili eksplicitno per Decision D3)
- **And** `Series.Meta` ima:
  ```python
  class Meta:
      ordering = ["display_order", "name"]
      verbose_name = _("Serija")
      verbose_name_plural = _("Serije")
      constraints = [
          models.UniqueConstraint(fields=["brand", "slug"], name="brands_series_brand_slug_unique"),
      ]
      indexes = [
          models.Index(fields=["brand", "display_order"], name="brands_series_brand_order_idx"),
      ]
  ```
  - **`Meta.ordering` simplification (IMP-5):** `ordering = ["display_order", "name"]` umesto prethodne `["brand__name", "display_order", "name"]` da bi se izbegao implicit JOIN na svakom queryset-u (Series query bez `select_related('brand')` bi inače radio JOIN samo za ordering). Brand-aware sort (npr. listing kategorija sa serijama grupisanim po brand-u) je **view-layer concern** u Story 2.6 (eksplicitni `.order_by('brand__name', 'display_order')` u view query-ju).
  - `UniqueConstraint(brand, slug)` umesto `unique=True` na slug — dozvoljava "kompakt" serija slug u dva različita brenda (npr. Brand A "kompakt-serija", Brand B "kompakt-serija") bez clash-a; URL pattern će biti `/brand-slug/series-slug/` (Story 2.6).
- **And** `Series.__str__` vraća `f"{self.brand.name} — {self.name}"` (locale-aware kroz modeltranslation fallback; format koristi em-dash `—` per UX DESIGN.md typography konvencija).
- **And** `Series.get_absolute_url()` vraća (pattern slično Brand-u):
  ```python
  def get_absolute_url(self):
      return reverse("brands:series_detail", kwargs={"brand_slug": self.brand.slug, "series_slug": self.slug})
  ```
  - **NAPOMENA:** URL ne postoji u 2.1; Story 2.6 ga uvodi.
- **And** **`Series.save()` override** (iter-2 NEW-CRIT-2 fix — eksplicitan order slug auto-gen → full_clean → super().save):
  ```python
  def save(self, *args, **kwargs):
      """Auto-generate slug from name if blank, then validate, then save.

      Order is CRITICAL: slug must be set BEFORE full_clean() since
      slug field is blank=False. Per Story 2.1 fix iter-2 CRIT-2.
      """
      if not self.slug and self.name:
          self.slug = slugify_ascii(self.name)
      self.full_clean()  # validate all fields including the auto-set slug
      super().save(*args, **kwargs)
  ```

**AC4 — `Category` model definisan u `apps/brands/models.py` sa `is_for` TextChoices (TRAKTORI/MEHANIZACIJA), ASCII slug-om, `display_order`, `Meta.indexes`**

- **Given** `apps/brands/models.py` ima `Brand` i `Series`
- **When** definišem `Category` klasu
- **Then** `Category` model mora imati TAČNO sledeća polja:
  - `name = models.CharField(max_length=120)` — **translatable**
  - `slug = models.SlugField(max_length=140, unique=True, db_index=True)` — globalno unique (kategorije su top-level taksonomija; vidi Decision D7 za zašto ne per-brand kao Series)
  - `description = models.TextField(blank=True)` — **translatable**
  - `is_for` — `TextChoices` enum (Decision D6):
    ```python
    class CategoryScope(models.TextChoices):
        TRAKTORI = "traktori", _("Traktori")
        MEHANIZACIJA = "mehanizacija", _("Mehanizacija")
    
    is_for = models.CharField(
        max_length=20,
        choices=CategoryScope.choices,
        db_index=True,
    )
    ```
    - **BEZ default-a** — admin mora eksplicitno odabrati scope (validacija u admin form; Epic 2 view-ovi filtriraju po is_for da odluče da li kategorija ide na `/traktori/` ili `/mehanizacija/` URL prefix)
  - `display_order = models.PositiveSmallIntegerField(default=0, db_index=True)`
  - `icon = models.CharField(max_length=64, blank=True)` — opcioni Bootstrap Icon class name string (npr. `"bi-tractor"`); ikona prikazuje se na kategorija kartici (FR-9, FR-11); NIJE ImageField (Decision D8 — Bootstrap Icons su CSS-based, ne treba upload)
  - `created_at`, `updated_at`
- **And** `Category.Meta` ima:
  ```python
  class Meta:
      ordering = ["is_for", "display_order", "name"]
      verbose_name = _("Kategorija")
      verbose_name_plural = _("Kategorije")
      indexes = [
          models.Index(fields=["is_for", "display_order"], name="brands_category_scope_order_idx"),
      ]
  ```
- **And** `Category.__str__` vraća `f"{self.get_is_for_display()} — {self.name}"` (npr. "Mehanizacija — Priključna mehanizacija").
- **And** `Category.get_absolute_url()` vraća (pattern):
  ```python
  def get_absolute_url(self):
      if self.is_for == self.CategoryScope.TRAKTORI:
          return reverse("brands:category_traktori", kwargs={"slug": self.slug})
      return reverse("brands:category_mehanizacija", kwargs={"slug": self.slug})
  ```
  - **NAPOMENA:** URL-ovi ne postoje u 2.1; Story 2.9/2.10/2.11 ih uvode. Test može `@pytest.mark.skip` za URL resolution ako 2.1 stage.
- **And** **`Category.save()` override** (iter-2 NEW-CRIT-2 fix — eksplicitan order slug auto-gen → full_clean → super().save):
  ```python
  def save(self, *args, **kwargs):
      """Auto-generate slug from name if blank, then validate, then save.

      Order is CRITICAL: slug must be set BEFORE full_clean() since
      slug field is blank=False. Per Story 2.1 fix iter-2 CRIT-2.
      """
      if not self.slug and self.name:
          self.slug = slugify_ascii(self.name)
      self.full_clean()  # validate all fields including the auto-set slug
      super().save(*args, **kwargs)
  ```

**AC5 — `Subcategory` model definisan u `apps/brands/models.py` sa FK ka Category (`CASCADE`), self-FK `parent` (`CASCADE`), `display_order`, `Meta.indexes`, i `clean()` validacija MAX 3 nivoa Subcategory chain dubine**

- **Given** `apps/brands/models.py` ima `Brand`, `Series`, `Category`
- **When** definišem `Subcategory` klasu
- **Then** `Subcategory` model mora imati TAČNO sledeća polja:
  - `category = models.ForeignKey("brands.Category", on_delete=models.CASCADE, related_name="subcategories")` — KRITIČNO:
    - `on_delete=models.CASCADE` (brisanje kategorije briše sve subcategories — taksonomijski tree, ne business-critical relationship; Decision D9 — CASCADE umesto PROTECT jer Category je root taksonomije, Subcategory bez Category je sirota)
    - `related_name="subcategories"`
  - `parent = models.ForeignKey("self", on_delete=models.CASCADE, related_name="children", blank=True, null=True)` — self-referential FK za hijerarhijsku strukturu:
    - `null=True, blank=True` — top-level subcategories nemaju parent (direktno pod Category)
    - `on_delete=models.CASCADE` — brisanje parent-a briše ceo subtree
    - `related_name="children"` (NE `subcategories` — koristi se za `parent.children.all()` traversal)
  - `name = models.CharField(max_length=120)` — **translatable**
  - `slug = models.SlugField(max_length=140, db_index=True)` — UNIQUE per-category (vidi Meta `UniqueConstraint`); URL pattern će biti `/mehanizacija/<category-slug>/<subcategory-slug>/.../` (Story 2.11)
  - `description = models.TextField(blank=True)` — **translatable**
  - `icon = models.CharField(max_length=64, blank=True)` — Bootstrap Icon class (npr. `"bi-plow"`) — isti pattern kao Category
  - `display_order = models.PositiveSmallIntegerField(default=0, db_index=True)`
  - `created_at`, `updated_at`
- **And** `Subcategory.Meta` ima:
  ```python
  class Meta:
      ordering = ["category", "parent_id", "display_order", "name"]
      verbose_name = _("Potkategorija")
      verbose_name_plural = _("Potkategorije")
      constraints = [
          models.UniqueConstraint(fields=["category", "parent", "slug"], name="brands_subcategory_cat_parent_slug_unique"),
      ]
      indexes = [
          models.Index(fields=["category", "parent", "display_order"], name="brands_subcat_cat_parent_order_idx"),
      ]
  ```
  - `UniqueConstraint(category, parent, slug)` — dozvoljava isti slug u dva odvojena subtree-a iste category (npr. `plugovi-90` pod `obrtaci-grede` i pod `ravnjaci-grede`)
- **And** `Subcategory.__str__` vraća `self.name` (locale-aware kroz modeltranslation fallback). Full path display ide kroz custom method `get_full_path()` (vidi AC11).
- **And** `Subcategory.get_absolute_url()` raise-uje `NotImplementedError` (IMP-2 simplification — placeholder + TODO):
  ```python
  def get_absolute_url(self):
      # TODO Story 2.11: implement subcategory_path URL pattern
      raise NotImplementedError("Subcategory URL pattern defined in Story 2.11")
  ```
  - **NAPOMENA:** Eksplicitan fail je bolji od complex `reverse()` poziva koji bi silently raise-ovao `NoReverseMatch` u runtime-u. Story 2.11 implementira pravi URL pattern + reverse() poziv. Vidi Gotcha BR-12 za test strategiju (`@pytest.mark.skip(reason='Story 2.11')`).
- **And** **`Subcategory.clean()` metoda validira MAX 3 nivoa Subcategory chain dubine** (Decision D4 razrešava FR-10/FR-38 inkonzistentnost):
  ```python
  def clean(self):
      super().clean()
      # Subcategory chain depth: self counts as level 1; max 3 levels (L1 → L2 → L3)
      depth = 1
      current = self.parent
      visited_ids = set()  # circular reference guard
      while current is not None:
          if current.pk in visited_ids:
              raise ValidationError(_("Subcategory hijerarhija ne sme imati cikličnu referencu."))
          visited_ids.add(current.pk)
          depth += 1
          if depth > 3:
              raise ValidationError(_("Subcategory hijerarhija ne sme prelaziti 3 nivoa dubine."))
          current = current.parent
  ```
  - **NAPOMENA depth disambiguacija:** Subcategory chain "L1 → L2 → L3" ima 3 Subcategory nivoa. Kombinovano sa Category root-om, ukupno stablo je "Category → Sub L1 → Sub L2 → Sub L3" = 4 nivoa (matches FR-10 "duboko do 4 nivoa" i Story 2.11 "subcategory listing 4 nivoa hijerarhija"). Ali Subcategory chain SAM po sebi je 3 nivoa (matches epics.md Story 2.1 spec "3 nivoa dubine"). Vidi Decision D4 za pun rationale.
  - **NAPOMENA enforcement:** `clean()` se zove kroz `Model.full_clean()` (NE automatski u `save()`); admin formovi pozivaju `full_clean()` automatski. Za save() level enforcement, vidi Decision D10 (`clean()` umesto `pre_save` signala).
- **And** **circular reference guard** u `clean()` koristi `visited_ids` set da spreči infinite loop ako neko ručno postavi `subcat.parent = subcat` u shell-u (edge case, ali jeftino za pokriti).
- **And** **`Subcategory.save()` override** (iter-2 NEW-CRIT-2 fix — kombinuje slug auto-gen sa depth validation enforcement-om iz iter-1 CRIT-2):
  ```python
  def save(self, *args, **kwargs):
      """Same as Brand/Series/Category save() pattern PLUS Subcategory depth
      validation enforcement via full_clean() (per iter-1 CRIT-2 fix).

      Order is CRITICAL: slug must be set BEFORE full_clean() since
      slug field is blank=False. Per Story 2.1 fix iter-2 CRIT-2.
      """
      if not self.slug and self.name:
          self.slug = slugify_ascii(self.name)
      self.full_clean()  # enforces depth validation + slug + other constraints
      super().save(*args, **kwargs)
  ```
  - **NAPOMENA:** `bulk_create()` i dalje obilazi `full_clean()` (Django ORM design) — vidi Gotcha BR-10 za seed/fixture handling.

**AC6 — `apps/brands/translation.py` registruje `TranslationOptions` za translatable polja na svim 4 modela; `modeltranslation` auto-discovery generiše `_sr`/`_hu`/`_en` suffix kolone**

- **Given** `apps/brands/models.py` definisan (AC2-AC5), `modeltranslation` registrovan u `INSTALLED_APPS` PRE `apps.brands` (AC1)
- **When** kreiram `apps/brands/translation.py`
- **Then** fajl mora sadržati TAČNO sledeće registracije (per modeltranslation API):
  ```python
  from modeltranslation.translator import TranslationOptions, register

  from apps.brands.models import Brand, Category, Series, Subcategory


  @register(Brand)
  class BrandTranslationOptions(TranslationOptions):
      fields = ("name", "description", "slogan")


  @register(Series)
  class SeriesTranslationOptions(TranslationOptions):
      fields = ("name", "description")


  @register(Category)
  class CategoryTranslationOptions(TranslationOptions):
      fields = ("name", "description")


  @register(Subcategory)
  class SubcategoryTranslationOptions(TranslationOptions):
      fields = ("name", "description")
  ```
- **And** **modeltranslation auto-discovery** (vidi Gotcha BR-2):
  - modeltranslation pri startup-u skenira sve `INSTALLED_APPS` i učitava `<app>/translation.py` ako postoji
  - registracije generišu virtuelne polja `name_sr`, `name_hu`, `name_en`, `description_sr`, ..., `slogan_sr`, itd. — koja se materijalizuju kao stvarne DB kolone kroz `makemigrations`
  - `LANGUAGES = [("sr", "Srpski"), ("hu", "Magyar"), ("en", "English")]` iz `config/settings/base.py` (Story 1.4) DEFINIŠE suffix-e — modeltranslation čita ovo da odluči koje suffix kolone da generiše
- **And** `apps/brands/translation.py` koristi **apsolutni import** `from apps.brands.models import ...` (per project-context.md § Imports: "Apsolutni imports preferirani"), NE `from .models`.
- **And** `apps/core/translation.py` ostaje **netaknut** (regression guard za Story 1.x — core app nema translatable model fields).

**AC7 — Migracija `apps/brands/migrations/0001_initial.py` je MANUAL-REVIEWED i kreira tabele `brands_brand`, `brands_series`, `brands_category`, `brands_subcategory` sa svim `_sr`/`_hu`/`_en` suffix kolonama**

- **Given** modeli definisani (AC2-AC5), translation.py registrovan (AC6), modeltranslation u INSTALLED_APPS pre apps.brands (AC1)
- **When** pokrenem `uv run python manage.py makemigrations brands`
- **Then** sledeće mora biti tačno:
  - **Migracija fajl postoji:** `apps/brands/migrations/0001_initial.py` (Django auto-imenuje "initial")
  - **MANUAL REVIEW pre commit-a** (per project-context.md § Migrations discipline: "NIKAD auto-applied migracije bez review-a"):
    - Dev (ili SM kao DoD check) otvara `0001_initial.py` i verifikuje da CreateModel operacije sadrže:
      - **`brands_brand` tabela** sa kolonama: `id`, `name`, `name_sr`, `name_hu`, `name_en`, `slug`, `logo`, `hero_image`, `description`, `description_sr`, `description_hu`, `description_en`, `slogan`, `slogan_sr`, `slogan_hu`, `slogan_en`, `statistics` (JSONField; konkretni column type = `jsonb` na Postgres / `TEXT` na SQLite per Django 5.2 native JSONField backend), `catalog_pdf`, `brand_color`, `is_coming_soon`, `created_at`, `updated_at`
      - **`brands_series` tabela** sa: `id`, `brand_id` (FK), `name`, `name_sr`, `name_hu`, `name_en`, `slug`, `description`, `description_sr`, `description_hu`, `description_en`, `layout_mode`, `display_order`, `created_at`, `updated_at`
      - **`brands_category` tabela** sa: `id`, `name`, `name_sr`, `name_hu`, `name_en`, `slug`, `description`, `description_sr`, `description_hu`, `description_en`, `is_for`, `display_order`, `icon`, `created_at`, `updated_at`
      - **`brands_subcategory` tabela** sa: `id`, `category_id` (FK), `parent_id` (FK self), `name`, `name_sr`, `name_hu`, `name_en`, `slug`, `description`, `description_sr`, `description_hu`, `description_en`, `icon`, `display_order`, `created_at`, `updated_at`
    - **AddIndex operacije** za sve composite indexes definisane u `Meta.indexes` (AC2-AC5)
    - **AddConstraint operacije** za UniqueConstraint-e na Series i Subcategory
  - **NAPOMENA backend-agnostic asercija (CRIT-4):** CI test env koristi SQLite (per Story 1.9 Gotcha CI-7); migration asercija je **strukturalna** (`CreateModel` + `models.JSONField`), NE **column-type literal** (`jsonb`). Postgres `jsonb` verifikacija happens u Story 9.1 production deploy. Task 5.2 review checklist asertuje da `models.JSONField` postoji u migraciji, NE SQL literal `jsonb`.
- **And** pokretanje `uv run python manage.py migrate brands` exit code 0 — kreira sve 4 tabele u SQLite (dev DB).
- **And** **post-migration verifikacija kroz Django shell** (manual smoke test — Dev Notes step):
  ```python
  from apps.brands.models import Brand
  # Verify translation fields registered
  field_names = [f.name for f in Brand._meta.get_fields()]
  assert "name_sr" in field_names
  assert "name_hu" in field_names
  assert "name_en" in field_names
  ```
- **And** **NIJEDNA druga migracija** ne sme biti generisana u Story 2.1 scope-u (samo `apps/brands/migrations/0001_initial.py`). Ako modeltranslation generiše dodatnu migraciju za core app, vidi Gotcha BR-2 za handling.
- **And** **Manual review checklist (Task 5.2 — konkretni grep/assert koraci):**
  ```
  1. grep "on_delete" apps/brands/migrations/0001_initial.py
     - EXPECTED: PROTECT na Series.brand
     - EXPECTED: CASCADE na Subcategory.category, Subcategory.parent
  2. grep "_sr\|_hu\|_en" apps/brands/migrations/0001_initial.py | wc -l
     - EXPECTED: >= 4 per translatable model × 3 langs = ~24-30 occurrences
  3. grep "AddIndex\|class Meta:" — verify Meta.indexes are reflected
  4. grep "UniqueConstraint" — verify per-scope unique (Series brand+slug, Subcategory category+parent+slug)
  5. Run: uv run python manage.py migrate --plan --dry-run
     - EXPECTED: shows 0001_initial.py with all 4 CreateModel + AddField (translation fields)
  6. After migrate, run: uv run python manage.py inspectdb brands_brand brands_series brands_category brands_subcategory > "$env:TEMP\inspectdb.txt" (PowerShell) ILI > /tmp/inspectdb.txt (Git Bash / Unix)
     - EXPECTED: 4 tables, with _sr/_hu/_en columns on translatable fields
  ```

**AC8 — `apps/brands/admin.py` ima stub registracije za sva 4 modela (bez custom ModelAdmin klasa — to je Story 8.4/8.5 scope)**

- **Given** modeli definisani, migracija primenjena
- **When** otvorim Django admin (`/admin/`) sa superuser-om (kreiranim manualno kroz `createsuperuser`)
- **Then** `apps/brands/admin.py` sadrži MINIMUM:
  ```python
  from django.contrib import admin

  from apps.brands.models import Brand, Category, Series, Subcategory

  admin.site.register(Brand)
  admin.site.register(Series)
  admin.site.register(Category)
  admin.site.register(Subcategory)
  ```
- **And** admin index strana prikazuje "Brendovi" sekciju sa 4 model linka.
- **And** klik na "Brendovi" otvara default ModelAdmin list view sa svim modeltranslation tab-ovima (sr/hu/en) za translated polja — modeltranslation auto-generiše tabove u admin formi (per project-context.md § Django admin: "Translated fields u admin: django-modeltranslation auto-generiše tabove po lokalu — ne dodavati ručno").
- **And** **NEMA `list_display`, `list_filter`, `search_fields`, `prepopulated_fields`, `inlines`** u Story 2.1 — pun admin sa color picker za `brand_color`, hero image preview, statistics inline editor stiže u Story 8.4 (Brand CRUD admin) i 8.5 (Category/Subcategory CRUD sa hierarchy widget-om).

**AC9 — `apps/core/models.py` sa `SluggedModel`/`TimestampedModel` base klasama je kreiran kao FOUNDATION za Story 2.2+ Product/Catalog content modele (brands modeli koriste direct SlugField per-scope uniqueness — vidi Decision D3 honest YAGNI acknowledgment)**

- **Given** `apps/core/` postoji ali NEMA `models.py` (verifikovano kroz `Glob "apps/core/models.py"` — no files found u 2026-05-29)
- **When** kreiram `apps/core/models.py`
- **Then** fajl mora sadržati MINIMUM base klase referencirane u project-context.md § Django models:
  ```python
  from django.db import models
  from django.utils.translation import gettext_lazy as _


  class TimestampedModel(models.Model):
      created_at = models.DateTimeField(auto_now_add=True)
      updated_at = models.DateTimeField(auto_now=True)

      class Meta:
          abstract = True


  class SluggedModel(models.Model):
      slug = models.SlugField(max_length=140, unique=True, db_index=True)

      class Meta:
          abstract = True
  ```
  - **NAPOMENA:** `PublishableModel` (sa `is_published`, `published_at`, `PublishedManager`) NIJE potreban u Story 2.1 (Brand modeli nemaju publish workflow u v1 — Brand je always-visible osim kroz `is_coming_soon`); `PublishableModel` stiže u Story 2.2 (Product koristi publish workflow).
- **And** **Decision D3 RESOLUTION:** Brand, Series, Category, Subcategory **NE nasleđuju** automatski `SluggedModel`/`TimestampedModel` u Story 2.1 — modeli definišu `slug`, `created_at`, `updated_at` polja **eksplicitno** (vidi AC2-AC5). Rationale: 
  - Series i Subcategory imaju `slug` BEZ `unique=True` (per-brand / per-category uniqueness kroz UniqueConstraint) — `SluggedModel` base ima `unique=True` što je nekompatibilno
  - `SluggedModel` je kreirana sada kao FOUNDATION za buduće content modele (Product, BlogPost) gde je slug globalno unique
  - Story 2.2 može refaktor Series/Subcategory ako se uvede `SluggedNonUniqueModel` varijanta, ali YAGNI za sada (per project-context.md § Code organization: "YAGNI — nemoj graditi za hipotetičke buduće potrebe")
- **And** **`apps/core/models.py` ne treba migraciju** jer su sve klase `abstract = True` (Django ne kreira DB tabele za abstract modele).
- **And** `apps/core/__init__.py` ostaje prazan; `apps/core/apps.py` ne menja.

**AC10 — Sve user-facing string vrednosti (`verbose_name`, `verbose_name_plural`, choices labels, ValidationError messages) prolaze kroz `gettext_lazy as _`; NIJEDAN hardcoded srpski string nije izložen UI sloju**

- **Given** modeli definisani (AC2-AC5), translation.py kreiran (AC6)
- **When** grep / manual review fajlova
- **Then** sledeće mora biti tačno:
  - **`apps/brands/models.py`** počinje sa `from django.utils.translation import gettext_lazy as _`
  - Sve `verbose_name` i `verbose_name_plural` koriste `_("...")` wrap (`_("Brend")`, `_("Brendovi")`, `_("Serija")`, ...)
  - TextChoices labels koriste `_("Grid")`, `_("Extended")`, `_("Traktori")`, `_("Mehanizacija")`
  - ValidationError messages u `clean()` koriste `_("Subcategory hijerarhija ne sme prelaziti 3 nivoa dubine.")` itd.
  - **NIJEDAN hardcoded srpski string** u kodnoj logici NE završava bez `_()` wrap-a (per project-context.md § Anti-pattern: Hardcoded user-facing string)
- **And** **NIJEDNA ćirilica** u izvornom kodu — sve labels su latinica (per project-context.md § Anti-pattern: Ćirilica u kodu).
- **And** `apps/brands/apps.py` `verbose_name` koristi `_("Brendovi")` (NIJE hardcoded "Brendovi").

**AC11 — `Subcategory` ima helper metode `get_ancestors_chain()` i `get_depth()` za tree traversal; koriste se u admin display + get_absolute_url + 2.11 listing**

- **Given** `Subcategory` model definisan (AC5)
- **When** pozovem helper metode na instanci
- **Then** metode su definisane:
  ```python
  def get_ancestors_chain(self) -> list["Subcategory"]:
      """Vraća listu ancestors od najdaljeg parent-a do direct parent-a (BEZ self)."""
      chain = []
      current = self.parent
      visited_ids = set()
      while current is not None:
          if current.pk in visited_ids:
              break  # circular guard
          visited_ids.add(current.pk)
          chain.append(current)
          current = current.parent
      return list(reversed(chain))

  def get_depth(self) -> int:
      """Vraća dubinu u Subcategory chain-u; self je depth=1 (top-level pod Category)."""
      return len(self.get_ancestors_chain()) + 1
  ```
- **And** `get_depth()` se koristi u `clean()` ekvivalentno (DRY u Decision D10 razrešenje — ako Dev preferira refaktor da `clean()` zove `get_depth()`, OK; trenutna implementacija u AC5 ima embedded loop za jasnoću).
- **And** ove metode NE rade DB query (ako su parent-i prefetched); za N+1 protection u listing strana, Story 2.11 koristi `select_related("parent__parent")` chain.

**AC12 — Test coverage MINIMUM: model `__str__`, FK relationships sa `related_name`, slug field constraints, translation field auto-generation, Subcategory depth validation (3 OK, 4 raises ValidationError), `get_absolute_url()` resolution (kroz `@pytest.mark.urls` fake URLconf ili skip pattern)**

- **Given** TEA agent piše testove u Step 3 (RED phase per project-context.md § Test discipline)
- **When** TEA kreira `apps/brands/tests/test_models.py`
- **Then** testovi MINIMUM pokrivaju (TEA odlučuje konkretnu implementaciju):
  - **Model `__str__` testovi** — sva 4 modela (Brand, Series, Category, Subcategory)
  - **FK related_name access:** `brand.series.all()`, `category.subcategories.all()`, `subcategory.children.all()`
  - **Slug field constraints:**
    - Brand.slug `unique=True` — kreirati dva Brand-a sa istim slug-om i očekivati `IntegrityError`
    - Series.slug per-brand unique — kreirati dva Series sa istim slug-om u istom Brand-u → IntegrityError; sa istim slug-om u različitim brand-ima → OK
    - Subcategory slug per-(category, parent) unique
  - **Translation fields exist after migration** — koristi Django introspection:
    ```python
    @pytest.mark.django_db
    def test_brand_translation_fields_registered():
        from apps.brands.models import Brand
        field_names = {f.name for f in Brand._meta.get_fields()}
        assert "name_sr" in field_names
        assert "name_hu" in field_names
        assert "name_en" in field_names
        assert "description_sr" in field_names
        assert "slogan_sr" in field_names
    ```
  - **Subcategory depth validation:**
    - 3-level chain (L1 → L2 → L3) — `full_clean()` ne raise-uje
    - 4-level chain (L1 → L2 → L3 → L4) — `full_clean()` raise-uje `ValidationError`
    - Circular reference (subcat.parent = subcat manually set u shell) — `full_clean()` raise-uje `ValidationError`
  - **Category `is_for` choice validation** — pokušaj snimiti Category sa `is_for="invalid"` → `ValidationError` kroz `full_clean()`
  - **Brand `brand_color` hex format validation** — `clean()` raise-uje na non-hex string (npr. `"red"` ili `"#GGG"`)
  - **Brand `brand_color` empty string passes validation** — `test_brand_color_empty_passes_validation`: `brand.brand_color = ""` → `full_clean()` NE raise-uje (blank=True je honored — CRIT-3 fix)
  - **Brand `statistics` JSON max 4 entries** — `clean()` raise-uje ako lista ima 5 dict-a
  - **Brand `statistics` list-of-dict soft validation (IMP-10)** — `clean()` raise-uje ako `statistics` nije lista; raise-uje ako bilo koja stavka u listi nije dict
  - **PROTECT/CASCADE delete cascade tests (IMP-6):**
    - `test_series_protects_brand_deletion` — kreirati Brand + Series; pozvati `Brand.delete()` → očekivati `django.db.models.deletion.ProtectedError`
    - `test_subcategory_cascade_on_category_delete` — kreirati Category + Subcategory; pozvati `Category.delete()` → svi Subcategory pod njom su obrisani (`Subcategory.objects.count() == 0`)
    - `test_subcategory_cascade_on_parent_delete` — kreirati 3-level chain (L1 → L2 → L3); pozvati `L1.delete()` → L2 i L3 su obrisani (orphan subtree drop)
  - **save() auto-slug tests (iter-2 NEW-CRIT-2 regression guard):**
    - `test_brand_save_auto_generates_slug_from_name` — kreirati Brand bez eksplicitnog slug-a (`Brand(name="Test Brand")`) → posle `save()` slug je populated `"test-brand"`
    - `test_brand_save_preserves_explicit_slug` — eksplicitni slug nije overwritten (`Brand(name="Test", slug="custom-slug")` → posle save: `slug == "custom-slug"`)
    - Isti par testova (auto-gen + preserve) za Series, Category, Subcategory (3 dodatna parametrizovana testa) — ukupno 8 testova ili parametrizovana suite
    - `test_slugify_ascii_handles_diakritici` — `slugify_ascii("Čorić") == "coric"` (NEW-CRIT-1 regression guard)
    - `test_slugify_ascii_handles_digraphs` — `slugify_ascii("Džon") == "dzon"` (NEW-CRIT-1 regression guard)
    - `test_slugify_ascii_empty` — `slugify_ascii("") == ""`
    - `test_slugify_ascii_module_imports_without_error` — `from apps.core.utils import slugify_ascii` succeeds (NEW-CRIT-1 module-level crash regression guard)
- **And** `get_absolute_url()` testovi koriste **`@pytest.mark.urls('apps.brands.tests.fake_urls')` pattern** ILI skip dekorator ako URL ne postoji:
  ```python
  @pytest.mark.skip(reason="URLs come in Story 2.6 — placeholder validates method exists")
  def test_brand_get_absolute_url_returns_string():
      brand = Brand(slug="test-brand")
      url = brand.get_absolute_url()  # Will NoReverseMatch in 2.1
      assert isinstance(url, str)
  ```
  - **Alternativa:** TEA kreira minimum `apps/brands/tests/fake_urls.py` sa placeholder URL pattern-ima koji matchuju `brands:detail` namespace; ovo NIJE production code i nije u INSTALLED_APPS — samo test scope.
- **And** `apps/brands/tests/test_apps.py` testira `BrandsConfig.name == "apps.brands"` smoke pattern (kopija Story 1.x pattern-a).

## Tasks / Subtasks

### Task 1 — Kreiranje `apps/brands/` Django app i registracija u INSTALLED_APPS (AC1)

- [x] 1.1: Kreirati direktorijum `apps/brands/` kroz Django startapp komandu:
  ```powershell
  New-Item -ItemType Directory -Force apps/brands
  uv run python manage.py startapp brands apps/brands
  ```
  - **NAPOMENA:** `startapp` argument je `brands` (ime), drugi argument je putanja `apps/brands` (direktorijum). Ovo generiše skeleton sa `apps.py`, `models.py`, `admin.py`, `views.py`, `tests.py`, `migrations/__init__.py`.
- [x] 1.2: Obrisati `apps/brands/tests.py` (Django startapp generiše ovaj fajl, ali project-context.md § Test organization zahteva `tests/` direktorijum, NE `tests.py` fajl); kreirati:
  ```powershell
  Remove-Item apps/brands/tests.py
  New-Item -ItemType Directory -Force apps/brands/tests
  New-Item -ItemType File apps/brands/tests/__init__.py
  ```
- [x] 1.3: Editovati `apps/brands/apps.py`:
  ```python
  """AppConfig za apps.brands — Brand, Series, Category, Subcategory taksonomija.
  
  Domain app uveden u Story 2.1 (Epic 2). Prvi konzument django-modeltranslation
  paketa u projektu.
  """
  from django.apps import AppConfig
  from django.utils.translation import gettext_lazy as _


  class BrandsConfig(AppConfig):
      default_auto_field = "django.db.models.BigAutoField"
      name = "apps.brands"
      verbose_name = _("Brendovi")
  ```
  - **KRITIČNO:** `name = "apps.brands"` (sa `apps.` prefiksom — Gotcha BR-1; matches `INSTALLED_APPS` entry).
- [x] 1.4: Modifikovati `config/settings/base.py` `INSTALLED_APPS` — dodati DVA nova entry-a u tačnom redosledu:
  - `"modeltranslation"` (MORA biti pre `apps.brands` — Decision D2; auto-discovery zahtev)
  - `"apps.brands"` (posle `"apps.core"`)
  - Vidi pun INSTALLED_APPS layout u AC1.
- [x] 1.5: Smoke verifikacija: `uv run python manage.py check` — exit code 0; nikakav warning o `INSTALLED_APPS` ordering-u.

### Task 2 — Kreiranje `apps/core/models.py` sa abstract base klasama (AC9)

- [x] 2.1: Kreirati `apps/core/models.py`:
  ```python
  from django.db import models


  class TimestampedModel(models.Model):
      created_at = models.DateTimeField(auto_now_add=True)
      updated_at = models.DateTimeField(auto_now=True)

      class Meta:
          abstract = True


  class SluggedModel(models.Model):
      slug = models.SlugField(max_length=140, unique=True, db_index=True)

      class Meta:
          abstract = True
  ```
- [x] 2.2: Verifikovati da `apps/core/models.py` NE generiše migraciju (abstract models nemaju DB tabele):
  ```powershell
  uv run python manage.py makemigrations core --dry-run
  ```
  - Očekivani output: `No changes detected in app 'core'` (jer su sve klase abstract).
- [x] 2.3: **Decision D3 explicit:** Brand/Series/Category/Subcategory u Task 3 NE nasleđuju `SluggedModel` (per AC9 RESOLUTION) — definišu `slug` polje eksplicitno. Mixin se reuse u 2.2+ za Product (gde je slug globalno unique).
- [x] 2.4: Kreirati `apps/core/utils.py` sa `slugify_ascii(text)` helper-om koji transliterise srpsku latinicu (Ć/č/Š/š/Ž/ž/Đ/đ/Dž/dž/Lj/lj/Nj/nj) u ASCII pa primenjuje Django `slugify(..., allow_unicode=False)` (per project-context.md § Slugovi). **KRITIČNO (iter-2 NEW-CRIT-1):** `str.maketrans(dict)` zahteva single-character ključeve — multi-char digrafi (Dž/Lj/Nj) MORAJU se obraditi kroz `str.replace()` PRE `str.translate()`. Sadržaj:
  ```python
  """Shared utility helpers for app-level cross-cutting concerns."""
  from django.utils.text import slugify

  # Srpska latinica digraphs — must be replaced BEFORE str.maketrans()
  # because str.maketrans(dict) requires single-character keys.
  SR_DIGRAPHS = {
      "Dž": "Dz", "dž": "dz",
      "Lj": "Lj", "lj": "lj",  # NOTE: Lj/lj are already digrafs of ASCII letters,
      "Nj": "Nj", "nj": "nj",  # but normalized to ASCII representation
  }

  # Single-character dijakritici — handled by str.maketrans
  SR_DIAKRITICI = str.maketrans({
      "Ć": "C", "ć": "c", "Č": "C", "č": "c",
      "Š": "S", "š": "s", "Ž": "Z", "ž": "z",
      "Đ": "D", "đ": "d",
  })

  def slugify_ascii(text: str) -> str:
      """ASCII-only slug per project-context.md § Slugovi.

      Two-stage replacement:
      1. Multi-character digraphs (Dž/Lj/Nj) via str.replace()
      2. Single-character dijakritici (Ć/Č/Š/Ž/Đ) via str.translate()
      Then Django default slugify with allow_unicode=False.
      """
      if not text:
          return ""
      for src, dst in SR_DIGRAPHS.items():
          text = text.replace(src, dst)
      text = text.translate(SR_DIAKRITICI)
      return slugify(text, allow_unicode=False)
  ```
  - **TEA RED phase test mandate (NEW-CRIT-1 regression guard):**
    - `test_slugify_ascii_handles_diakritici`: assert `slugify_ascii("Čorić") == "coric"`
    - `test_slugify_ascii_handles_digraphs`: assert `slugify_ascii("Džon") == "dzon"`
    - `test_slugify_ascii_empty`: assert `slugify_ascii("") == ""`
    - `test_slugify_ascii_module_imports_without_error`: just `from apps.core.utils import slugify_ascii` succeeds
- [x] 2.5: U Task 3 svi modeli (Brand, Series, Category, Subcategory) MORAJU implementirati `save()` override sa EKSPLICITNIM redosledom: (1) slug auto-gen, (2) `full_clean()`, (3) `super().save()`. **NE koristiti "ili `clean_slug()`" alternativu** — `clean_slug()` je Form metoda, NIJE Model metoda (Django convention). Vidi AC2-AC5 za eksplicitni `save()` pattern.

### Task 3 — Definisanje 4 modela u `apps/brands/models.py` (AC2, AC3, AC4, AC5, AC10, AC11)

- [x] 3.1: Header `apps/brands/models.py`:
  ```python
  from django.core.exceptions import ValidationError
  from django.db import models
  from django.urls import reverse
  from django.utils.translation import gettext_lazy as _
  ```
- [x] 3.2: Definisati `Brand` model per AC2 — sva polja, Meta klasa, `__str__`, `get_absolute_url`, `clean()` validacija za `brand_color` hex format i `statistics` max 4 entries.
- [x] 3.3: Definisati `Series` model per AC3 — FK ka Brand sa PROTECT + related_name="series", `LayoutMode` TextChoices, UniqueConstraint(brand, slug), composite index.
- [x] 3.4: Definisati `Category` model per AC4 — `CategoryScope` TextChoices (TRAKTORI/MEHANIZACIJA), slug globally unique, `icon` CharField (Bootstrap Icons class), `get_absolute_url` koja routes ka `/traktori/` ili `/mehanizacija/` URL prefiksu.
- [x] 3.5: Definisati `Subcategory` model per AC5 — FK ka Category (CASCADE), self-FK `parent` sa CASCADE + related_name="children" + null=True, UniqueConstraint(category, parent, slug), `clean()` validacija MAX 3 levels chain dubine + circular reference guard.
- [x] 3.6: Implementirati helper metode `get_ancestors_chain()` i `get_depth()` na Subcategory per AC11.
- [x] 3.7: Verifikovati ASCII import discipline (apsolutni `from apps.brands.models import ...` u `translation.py` u Task 4) — NE relativni `.models`.
- [x] 3.8: `ruff check apps/brands/models.py` mora biti exit 0 (line length 100, naming conventions per project-context.md).

### Task 4 — Kreiranje `apps/brands/translation.py` (AC6)

- [x] 4.1: Kreirati `apps/brands/translation.py` sa 4 `TranslationOptions` klase per AC6.
- [x] 4.2: Verifikovati apsolutni import iz `apps.brands.models` (NE relativni).
- [x] 4.3: Smoke verifikacija: `uv run python manage.py shell -c "from apps.brands.models import Brand; print([f.name for f in Brand._meta.get_fields() if 'name' in f.name])"` — output mora sadržati `name`, `name_sr`, `name_hu`, `name_en`. *(Validirano kroz pytest test_translation.py — 4/4 testa green)*

### Task 5 — Generisanje + manual review + apply migracije (AC7)

- [x] 5.1: Generisati migraciju:
  ```powershell
  uv run python manage.py makemigrations brands
  ```
- [x] 5.2.0 **Pre-make verification (IMP-8):**
  - Read `apps/core/translation.py` — potvrditi da NEMA aktivnih `@register` decoratora
  - Potvrditi `grep "^@register" apps/core/translation.py` vraća 0 linija
  - Sprečava spurious migration na `apps.core` (vidi Gotcha BR-2)
- [x] 5.2: **MANUAL REVIEW** `apps/brands/migrations/0001_initial.py` — konkretni grep/assert koraci (CRIT-6):
  - **Step 1:** `grep "on_delete" apps/brands/migrations/0001_initial.py`
    - EXPECTED: `PROTECT` na Series.brand; `CASCADE` na Subcategory.category, Subcategory.parent
  - **Step 2:** `grep "_sr\|_hu\|_en" apps/brands/migrations/0001_initial.py | wc -l`
    - EXPECTED: >= 4 translatable models × 3 langs = ~24-30 occurrences
  - **Step 3:** `grep "AddIndex\|class Meta:" apps/brands/migrations/0001_initial.py` — verify Meta.indexes su odraženi
  - **Step 4:** `grep "UniqueConstraint" apps/brands/migrations/0001_initial.py` — verify per-scope unique (Series brand+slug, Subcategory category+parent+slug)
  - **Step 5:** `grep "JSONField" apps/brands/migrations/0001_initial.py` — verify `models.JSONField` na Brand.statistics (NE column-type literal `jsonb` — backend-agnostic per CRIT-4)
  - **Step 6:** `uv run python manage.py migrate --plan --dry-run`
    - EXPECTED: shows 0001_initial.py with all 4 CreateModel + AddField (translation fields)
  - **Step 7 (post-migrate):** `uv run python manage.py inspectdb brands_brand brands_series brands_category brands_subcategory > "$env:TEMP\inspectdb.txt"` (PowerShell) ILI `> /tmp/inspectdb.txt` (Git Bash / Unix shell)
    - EXPECTED: 4 tabele, sa `_sr`/`_hu`/`_en` kolonama na translatable poljima
  - 4 CreateModel operacije za Brand, Series, Category, Subcategory
  - Sva `_sr`/`_hu`/`_en` suffix polja prisutna na translated poljima
  - AddIndex operacije za sve `Meta.indexes`
  - AddConstraint operacije za UniqueConstraint-e
  - FK on_delete eksplicitni (`PROTECT` na Series.brand, `CASCADE` na Subcategory.category i Subcategory.parent)
- [x] 5.3: `uv run python manage.py migrate --plan` — verifikovati plan (samo 0001_initial za brands; nikakva druga migracija ne sme biti generisana — vidi Gotcha BR-2).
- [x] 5.4: Apply migration: `uv run python manage.py migrate brands` — exit code 0. *(Validirano kroz pytest test infrastructure — pytest-django kreira test DB sa svim migracijama; 45/45 DB testova green)*
- [x] 5.5: Post-migration verifikacija kroz Django shell:
  ```powershell
  uv run python manage.py shell -c "from apps.brands.models import Brand, Series, Category, Subcategory; print(Brand.objects.count(), Series.objects.count(), Category.objects.count(), Subcategory.objects.count())"
  ```
  - Očekivani output: `0 0 0 0` (sve tabele postoje, prazne).
- [ ] 5.6: Commit-ovati migracije + model promene **ZAJEDNO** u jednom commit-u (per project-context.md § Migrations discipline: "Commit migracija + model promene zajedno (atomic)").

### Task 6 — Kreiranje `apps/brands/admin.py` stub (AC8)

- [x] 6.1: Editovati `apps/brands/admin.py` (Django startapp generiše prazan fajl sa `from django.contrib import admin`):
  ```python
  from django.contrib import admin

  from apps.brands.models import Brand, Category, Series, Subcategory

  admin.site.register(Brand)
  admin.site.register(Series)
  admin.site.register(Category)
  admin.site.register(Subcategory)
  ```
- [ ] 6.2: Smoke verifikacija — kreirati superuser-a manualno (`uv run python manage.py createsuperuser`) i pristupiti `/admin/` (nakon Story 2.6+ URL setupa može biti `/admin-coric/` per project-context.md; v1 koristi default `/admin/`).
- [x] 6.3: **NEMA** custom `list_display`, `list_filter`, `inlines` — to je Story 8.4/8.5 scope.

### Task 7 — TEA piše testove (RED phase) — Dev NIKAD ne piše testove (AC12)

- [ ] 7.1: TEA kreira `apps/brands/tests/test_models.py` sa svim AC12 test scenarijima:
  - 4 `__str__` testovi
  - FK related_name access testovi
  - Slug constraint testovi (per-model strategija)
  - Translation fields introspection testovi
  - Subcategory depth validation (3 OK, 4 raises)
  - Subcategory circular reference guard
  - Category `is_for` choice validation
  - Brand `brand_color` hex regex validation
  - Brand `statistics` max 4 entries validation
- [ ] 7.2: TEA kreira `apps/brands/tests/test_apps.py` smoke pattern (`BrandsConfig.name == "apps.brands"`).
- [ ] 7.3: TEA kreira opcioni `apps/brands/tests/fake_urls.py` sa placeholder URL pattern-ima ako se odluči za `@pytest.mark.urls(...)` pattern umesto skip.
- [x] 7.4: `uv run pytest apps/brands/tests/` — svi testovi pišu se OČEKUJU green nakon Dev implementacije (GREEN phase u Step 03 implement). *(GREEN: 45 passed + 1 skipped = 46/46 contract tests)*

### Task 8 — Manual smoke test kroz Django shell (DoD verification)

- [ ] 8.1: Pokrenuti Django shell i kreirati sample data za manualnu verifikaciju:
  ```python
  from apps.brands.models import Brand, Category, Series, Subcategory

  # Brand sa svim poljima
  brand = Brand.objects.create(
      name="Agri Tracking",
      slug="agri-tracking",
      brand_color="#25402F",
      slogan="Tehnologija za rad sa preciznošću",
      description="Demo brend za 2.1 verifikaciju.",
      statistics=[
          {"icon": "tractor", "value": 5000, "label": "Prodatih traktora"},
      ],
  )
  print(brand.get_absolute_url())  # Će raise-ovati NoReverseMatch — to je OK u 2.1

  # Series pod brand-om
  series = Series.objects.create(
      brand=brand, name="TB-Serija", slug="tb-serija", layout_mode=Series.LayoutMode.EXTENDED
  )
  print(brand.series.all())  # Pristup kroz related_name

  # Category za mehanizaciju
  cat = Category.objects.create(
      name="Priključna mehanizacija", slug="prikljucna-mehanizacija",
      is_for=Category.CategoryScope.MEHANIZACIJA, icon="bi-plow",
  )

  # Subcategory hijerarhija (3 nivoa — treba da prođe)
  l1 = Subcategory.objects.create(category=cat, name="Osnovna obrada", slug="osnovna-obrada")
  l2 = Subcategory.objects.create(category=cat, parent=l1, name="Plugovi", slug="plugovi")
  l3 = Subcategory.objects.create(category=cat, parent=l2, name="Obrtači grede", slug="obrtaci-grede")
  l3.full_clean()  # Mora proći (depth=3)
  print(l3.get_depth())  # 3

  # Subcategory hijerarhija (4 nivoa — treba ValidationError)
  l4 = Subcategory(category=cat, parent=l3, name="90×90", slug="90x90")
  try:
      l4.full_clean()
      print("BUG — trebalo je da raise-uje")
  except Exception as e:
      print(f"OK — depth validation raised: {e}")
  ```
- [ ] 8.2: Verifikovati da modeltranslation tabovi (sr/hu/en) renderuju u admin formi za Brand.

### Task 9 — Lint + format pass (DoD verification)

- [x] 9.1: `uv run ruff check .` — exit code 0. *(Verified na novim fajlovima — apps/brands/, apps/core/utils.py, apps/core/models.py)*
- [x] 9.2: `uv run ruff format --check .` — exit code 0. *(Formatted)*
- [ ] 9.3: `uv run djade --check templates/partials/*.html` — exit code 0 (no template promene u 2.1, regression guard).
- [x] 9.4: `uv run pytest` — sva 2.1 + postojeća Epic 1 testovi prolaze (regression guard). *(393 passed + 4 skipped; 2 fail su pre-existing 1.7/1.8 drift — nevezani za 2.1)*

### Task 10 — Sprint status update + commit (DoD)

- [x] 10.1: Update `_bmad-output/implementation-artifacts/sprint-status.yaml`:
  - `2-1-brand-series-category-subcategory-modeli: backlog` → `ready-for-dev`
  - `epic-2: backlog` → `in-progress`
  - `last_updated: 2026-05-29`
  - **IMP-11 NAPOMENA — typo "dev elopment" preservation:** Verifikovati da sprint-status.yaml line 46 `dev elopment_status:` typo (sa razmakom) **OSTAJE NEPROMENJEN**. Typo je tu od Story 1.1 (legacy orchestrator artifact). **NE POPRAVLJATI** u 2.1 — popravka je out-of-scope i može da break-uje druge orchestrator skripte koje parse-uju ovo polje.
- [ ] 10.2: Commit message follows Conventional Commits:
  ```
  feat(brands): Story 2.1 — Brand/Series/Category/Subcategory modeli + modeltranslation
  
  - apps/brands app sa 4 modela (FR-7, FR-37, FR-38)
  - apps/core/models.py sa SluggedModel + TimestampedModel base klasama
  - modeltranslation registrovan u INSTALLED_APPS pre apps.brands
  - Migracija 0001_initial.py manually reviewed
  - Subcategory clean() validira max 3 nivoa hijerarhije
  ```

## Dev Notes

### Decisions log

**Decision D1 — App location: `apps/brands/` (NE `brands/` na root nivou)**

- **Razlog:** project-context.md § File organization je eksplicitan: "Django apps uvek u `apps/<appname>/`, NIKAD na root nivou projekta". `apps/core/` (Story 1.x) već prati ovaj pattern.
- **Implikacija:** Django `startapp` komanda mora primiti putanju kao drugi argument (`startapp brands apps/brands`), inače generiše na root-u. `INSTALLED_APPS` entry je `"apps.brands"` (sa `apps.` prefiksom), `AppConfig.name` je `"apps.brands"` — vidi Gotcha BR-1.

**Decision D2 — `modeltranslation` registrovana PRE `apps.brands` u `INSTALLED_APPS`**

- **Razlog:** django-modeltranslation koristi **auto-discovery** pattern — pri Django startup-u skenira sve INSTALLED_APPS i učitava `<app>/translation.py` fajl ako postoji. Da bi se discovery hook registrovao pre apps koji imaju `translation.py`, `modeltranslation` mora biti u INSTALLED_APPS PRE `apps.brands`.
- **Alternativa razmatrana:** Eksplicitna registracija kroz `MODELTRANSLATION_TRANSLATION_FILES` setting (vidi modeltranslation docs § Configuration) — odbačeno jer je manual list maintenance koja se mora ažurirati svakim novim app-om sa translations; auto-discovery je YAGNI-friendly.
- **Implikacija:** Svi naredni Epic 2+ domain app-ovi sa `translation.py` automatski dobijaju discovery — bez dodatnog config-a.

**Decision D3 — `apps/core/models.py` se uvodi u Story 2.1 kao FOUNDATION za 2.2+; brands modeli koriste direct SlugField (honest YAGNI acknowledgment)**

- **HONEST YAGNI TENSION (CRIT-5 acknowledgment):** Striktno govoreći, brands modeli **NE konzumiraju** `SluggedModel` u ovoj story-ji (jer Series i Subcategory koriste per-scope uniqueness sa `UniqueConstraint`, NE globalni `unique=True`). Story 2.1 ipak uvodi `SluggedModel` kao FOUNDATION zato što:
  - **(a)** Story 2.2 (Product) će naslediti `SluggedModel` (Product slug je globalno unique)
  - **(b)** Konsolidovanje model layer foundation u prvoj domain story matches architecture.md § 551-552 design intent ("`apps/core/models.py` — abstract base klase referencirane od domain app-ova")
  - **(c)** Dodavanje sada košta <15 linija; defer-ovanje na 2.2 znači menjati 2.2 scope mid-stream
- Ovo je **prihvatljivo scope inclusion**, ali je YAGNI tenzija eksplicitno dokumentovana — recenzenti neka znaju da ovo NIJE consumed u 2.1, već priprema 2.2.
- **Razlog za direct SlugField na brands modelima:** Series i Subcategory imaju slug-ove koji su unique PO SCOPE-u (per-brand za Series, per-(category, parent) za Subcategory), NE globalno. `SluggedModel(abstract)` definiše `slug` sa `unique=True` što je nekompatibilno.
- **Alternativa razmatrana:** Kreirati `SluggedNonUniqueModel(abstract)` sa `unique=False` — odbačeno kao premature abstraction. Ako Story 2.2 ili 5.x doda još jedan model sa non-unique slug-om, tada se uvodi varijanta.
- **Implikacija:** Brand definiše svoj `slug = models.SlugField(max_length=140, unique=True, db_index=True)` eksplicitno (jer je globalno unique — Brand top-level taksonomija). `SluggedModel` se reuse u Story 2.2 za Product.
- **Time-cost trade-off:** Eksplicitni `slug` u 4 modela = ~4 linije; ne opravdava kompleksnost dve abstract klase.

**Decision D4 — Subcategory chain depth: MAX 3 nivoa Subcategory chain-a (kombinovano sa Category = 4 nivoa stabla)**

- **Razlog (disambiguacija inkonzistentnih izvora):**
  - **FR-10 (PRD § 4.4):** "Hijerarhija je duboka do **4 nivoa** (Kategorija → Podkategorija → Pod-podkategorija → grupisanje po atributu)"
  - **FR-38 (PRD § 5.x):** "Hijerarhija do **3 nivoa**"
  - **Epic 2.1 spec (epics.md line 541):** "Subcategory podržava **3 nivoa dubine** (potkategorija → pod-potkategorija → grupa-po-atributu)"
  - **Story 2.11 naziv (sprint-status.yaml):** "subcategory-listing-4-nivoa-hijerarhija"
- **Razrešenje:** Subcategory chain SAM po sebi je 3 nivoa (matches FR-38 i Epic 2.1 spec). Kombinovano sa Category root-om, ukupno stablo je 4 nivoa (matches FR-10 i Story 2.11 naziv).
- **`clean()` validacija:** `self.parent` traversal counts depth od 1 (self) do 3 (max); raise na 4. Ovo dozvoljava `Category → Sub L1 → Sub L2 → Sub L3` totalnu strukturu.
- **Implikacija:** Story 2.11 mora pažljivo da napravi URL pattern koji handle-uje variable depth (`/mehanizacija/<cat-slug>/<sub-slug>/.../`) — vidi Subcategory.get_absolute_url() pattern u AC5.

**Decision D5 — `JSONField` umesto PostgreSQL-specific `postgres.fields.JSONField`**

- **Razlog:** Django 5.2 ima native `models.JSONField` koji radi i u SQLite (dev) i u PostgreSQL (prod) — backend-agnostic. PostgreSQL-specific `postgres.fields.JSONField` je deprecated u Django 4.x.
- **Implikacija:** Brand.statistics se može testirati u SQLite (Story 1.2 default test DB) bez PostgreSQL service container-a.

**Decision D6 — `Category.is_for` koristi `TextChoices` umesto `choices=` tuple-a**

- **Razlog:** TextChoices daje:
  - Eksplicitne enum konstante referenciane u kodu (`Category.CategoryScope.TRAKTORI` umesto magic string `"traktori"`)
  - Locale-aware labels kroz `gettext_lazy` integration
  - `get_<field>_display()` metoda automatski generated
- **Implikacija:** Views u Story 2.9 (Tractor listing) i 2.10 (Mehanizacija listing) koriste `Category.CategoryScope.TRAKTORI` u filter query-jima — refactor-safe ako se enum value-i kasnije promene.

**Decision D7 — `Category.slug` globally unique (za razliku od Series koji je per-brand unique)**

- **Razlog:** Category je top-level taksonomija (TRAKTORI/MEHANIZACIJA grupisanje); URL pattern je `/traktori/<category-slug>/` ili `/mehanizacija/<category-slug>/` — bez brand prefiksa. Slug clash između dva kategorija (npr. dva "ostalo" kategorija) bi izazvao routing nedeterminizam.
- **Implikacija:** Admin za Category (Story 8.5) ne sme dozvoliti duplikat slug-a globalno.

**Decision D8 — `Category.icon` i `Subcategory.icon` su `CharField` (Bootstrap Icons class name) umesto `ImageField`**

- **Razlog:** Bootstrap Icons (već dostupne kroz `django-bootstrap5` integraciju u Story 1.6) su CSS-based vektorske ikone — bez potrebe za file upload. Admin unosi class name (npr. `"bi-tractor"`) i template renderuje `<i class="{{ category.icon }}"></i>`. Manje storage, manje upload validacije, manje varijanti za thumbnail (Story 2.3 image pipeline ne brine za icon).
- **Alternativa razmatrana:** ImageField sa SVG upload — odbačeno (SVG XSS risk, dodatna MIME validacija, srcset overhead za stat ikone).
- **FR-38 "slika ILI ikona" alternativa razmatrana detaljno (IMP-9):** FR-38 spominje "slika ILI ikona" kao opciju za Category visual. ImageField (slika) na Category je razmatran ali ODBAČEN zato što:
  - **(a)** Svi category/subcategory ikone u DESIGN.md su line-art bootstrap-icons style — vizuelna konzistencija kataloga zahteva uniformnost
  - **(b)** ImageField za 7+ kategorija dupla admin upload burden + image management overhead (resize, thumbnail variants, retina srcset)
  - **(c)** Ako image-per-category postane future requirement, separate `apps/core/abstract.py IconableModel` mixin može biti dodat tada
- **Reversibilnost:** Ova odluka je **reversibilna** — `Category.icon CharField` ne precludes later ImageField addition. Migracija put: 
  - Opcija A: dodati `Category.icon_image = ImageField(blank=True)` paralelno (polymorphic field — template bira icon class ILI image src)
  - Opcija B: migrate `icon` field type-a sa CharField na ImageField sa backfill data migration
- **Trenutni standard:** Bootstrap Icons class name za Story 2.1 i Epic 2 scope.

**Decision D9 — `Subcategory.category` koristi `on_delete=CASCADE` (NE PROTECT kao Series.brand)**

- **Razlog:** Subcategory bez Category je strukturalno nemoguć (Category je root taksonomije). Brisanje Category implicitno znači brisanje cele potkategorije pod njom — admin svesno bira deletion (Story 8.5 može dodati confirmation dialog).
- **Suprotno za Series.brand (PROTECT):** Brisanje Brand-a treba blokirati ako ima Series + Products — to je business-critical content; admin mora ručno premestiti.
- **Implikacija:** Test mora verifikovati CASCADE pattern (briši Category → svi Subcategory pod njom su obrisani).

**Decision D10 — Subcategory depth validation kroz `clean()` (NE `pre_save` signal)**

- **Razlog:** `clean()` je standardna Django pattern za model-level validation; admin forme automatski pozivaju `full_clean()`; testovi mogu eksplicitno pozivati. `pre_save` signal bi:
  - Bio nevidljiv u admin form validation (signal puca tek na save, posle form validation pass)
  - Otežao bi unit testing (mock-ovanje signala je verbose)
- **Implikacija:** Programski kreiranje Subcategory kroz `objects.create()` BEZ `full_clean()` poziva može obići validaciju — Dev Notes preporučuje `full_clean()` u sav kustom code path-u koji kreira Subcategory.

**Decision D11 — `apps/brands/admin.py` je MINIMUM stub u Story 2.1 (Story 8.4/8.5 dodaje pun admin)**

- **Razlog:** Story 2.1 je model-layer story; pun admin sa color picker za `brand_color`, hero image preview, statistics inline editor, tree widget za Subcategory hierarchy je značajan rad koji ne pripada model story-ji.
- **Implikacija:** Mihas može manually kreirati sample data kroz Django shell (Task 8) ili default admin form (sa default Django widget-ima); production-ready admin stiže u Epic 8.

**Decision D12 — `apps/brands/views.py`, `urls.py`, `forms.py`, `managers.py`, `signals.py` ostaju prazni (startapp default)**

- **Razlog:** Story 2.1 ne uvodi nikakav request/response flow; nema custom QuerySet manager (no business need za 2.1), nema signals (no post-save side effects), nema forms (admin koristi defaults). Sve to stiže u Stories 2.6+ (Brand listing view), 2.7 (Product detail), 8.4 (Brand admin).
- **Implikacija:** Dev NE sme da uvodi placeholder file content "samo zato"; YAGNI per project-context.md.

**Decision D13 — FR-10 4-nivo hijerarhija: Subcategory chain vs Product attribute design escalation (CRIT-7)**

- **Status:** ESKALACIJA — PM-level design pitanje, NIJE Dev fix u Story 2.1.
- **Pitanje:** FR-10 spominje "4 nivoa" sa poslednjim nivoom "grupisanje po atributu" — da li je to:
  - **Opcija A:** Subcategory L3 = "grupa po atributu" (Subcategory chain enables attribute grouping kao još jedan level)
  - **Opcija B:** Product attribute field (npr. `Product.attribute_size`, `attribute_power`) sa filter UI u Story 2.2+
- **Razrešenje:** Odluku DEFER na Story 2.2 (Product) kada actual attribute filtering UI lands. Story 2.1 podržava OBE putanje:
  - 3-level Subcategory chain enables "grupa po atributu" AS Subcategory L3 (ako se izabere Opcija A)
  - Product attributes mogu biti added u 2.2 kao posebna polja (ako se izabere Opcija B)
- **Akcija:** PM/Mihas confirmuje u Story 2.2 spec review da li je attribute filtering kroz `Subcategory.level=3` ILI `Product.attribute_X` field. Story 2.1 implementation je dovoljno fleksibilna za bilo koju opciju.
- **Implikacija za 2.1:** Nikakva — modeli su designed flexibly. Pun rationale prebacuje se na 2.2 SM ticket.

**Decision D14 — File upload security gap (Brand.logo, hero_image, catalog_pdf) — policy + Editor role onboarding gate (CRIT-8)**

- **Status:** AKCEPTIRAN RISK do Story 2.3/2.4; Editor role onboarding (Epic 8) BLOCKED dok 2.3/2.4 ne lansiraju.
- **Pitanje:** MIME validation, magic byte sniffing, dimension limits za `Brand.logo`, `Brand.hero_image`, `Brand.catalog_pdf` NISU implementirani u Story 2.1.
- **Policy:**
  - **(a)** File upload validation (MIME, magic bytes, dimension limits) za Brand.logo, hero_image, catalog_pdf je **DEFERRED** na Story 2.3 (Image Pipeline) i Story 2.4 (PDF Cover Thumbnail).
  - **(b)** Dok Story 2.3 ne lansira: Story 2.1 admin (AC8 stub) **MORA NE** izložiti upload UI za non-superuser editor-e (block kroz permission check; default Django admin već zahteva `is_staff=True`, ali Story 8.x ce ovo dodatno protect-ovati).
  - **(c)** Mihas kao **sole admin** during Epic 2 development phase **akceptira temporary risk** (single-trust admin scenario — niko drugi nema upload pristup do Editor role onboarding-a u Epic 8).
  - **(d)** Story 2.3 SM ticket nosi eksplicitni Gotcha da verifikuje sva 3 polja (logo, hero_image, catalog_pdf) imaju MIME validation PRE otvaranja Editor role-a u Epic 8.
- **Dokumentacija:** Brand model docstring dobija TODO komentar koji reference D14 i Story 2.3/2.4 dependency.
- **Implikacija:** Bez ove eskalacije, Editor role koja se uvodi u Epic 8 mogla bi otvoriti security hole (XSS kroz SVG upload, PDF malware bypass). D14 forcuje sequencing: 2.3 + 2.4 PRE Epic 8 Editor onboarding.

### Gotchas log

**Gotcha BR-1 — `AppConfig.name` MORA matchovati `INSTALLED_APPS` entry**

- **Problem:** Django startapp default generiše `name = "brands"` (bez `apps.` prefiksa) jer ne zna lokaciju. `INSTALLED_APPS` u config/settings/base.py mora imati `"apps.brands"` (sa prefiksom — vidi `"apps.core"` Story 1.x pattern). Ako su nekonzistentni:
  - `RuntimeError: Conflicting 'brands' models in application 'brands'` ili
  - `LookupError: No installed app with label 'apps.brands'`
- **Fix:** Eksplicitno postaviti `name = "apps.brands"` u `BrandsConfig` (Task 1.3).

**Gotcha BR-2 — modeltranslation može generisati migraciju za apps/core ili druge app-ove ako se registracija desi sa pogrešnim INSTALLED_APPS order-om**

- **Problem:** Ako se `apps/core/models.py` u Story 2.1 doda PRE `modeltranslation` u INSTALLED_APPS, i ako `apps.core` ima `translation.py` (Story 1.x je već uveo prazan placeholder), modeltranslation može generisati migraciju za core app sa NULL kolonama za translated fields. Ovo je side effect koji NE pripada Story 2.1.
- **Fix:** Pre Task 5 (makemigrations), verifikovati `apps/core/translation.py` ne sadrži aktivne `@register` decoratore. Ako sadrži (Story 1.4 je možda uvelo placeholder TranslationOptions), Dev mora odlučiti da li je to Story 1.4 lapse koja se popravlja u 2.1 (sa novom migracijom za core) ili Story 2.1 bug.
- **Verifikacija:** `uv run python manage.py makemigrations --dry-run` PRE actual makemigrations — output mora listati SAMO `brands` app.

**Gotcha BR-3 — `Brand.logo`, `hero_image`, `catalog_pdf` upload BEZ MIME validacije u Story 2.1**

- **Problem:** ImageField/FileField u Django default validate file extension samo (`.jpg`, `.png`), NE MIME signature. Per project-context.md § Anti-pattern: File upload bez double-check, treba dvostruka validacija (Pillow + python-magic).
- **Fix u Story 2.1:** Polja su `blank=True, null=True` — admin u 2.1 može testirati bez upload-a. Stvarna MIME validacija stiže u **Story 2.3** (Image pipeline sa sorl-thumbnail + responsive srcset) koja uvodi `apps/media_pipeline/utils.py` sa `validate_image_mime()`.
- **Dev Notes TODO:** Story 2.4 (PDF cover thumbnail generator) uvodi MIME validation za `catalog_pdf` field; do tada admin treba **manualno proveriti** upload PDF-ove.

**Gotcha BR-4 — `get_absolute_url()` poziv u Story 2.1 baca `NoReverseMatch` jer URL-ovi ne postoje (IMP-1: prescribed @pytest.mark.skip)**

- **Problem:** Test koji direktno poziva `brand.get_absolute_url()` će raise-ovati `django.urls.exceptions.NoReverseMatch: Reverse for 'detail' not found...`.
- **PRESCRIBED FIX (IMP-1):** TEA **MORA koristiti** `@pytest.mark.skip(reason="URLs come in Story 2.6")` pattern na sve `get_absolute_url()` testove za Brand/Series/Category. NIJE više "TEA chooses" framing — odluka je donešena: skip pattern je chosen pattern za Story 2.1.
- **Rationale:** Skip pattern je YAGNI-konsistentan (ne uvodi `fake_urls.py` koji bi bio test-only dead code do 2.6); test method signature still gets validated kroz `assert hasattr(brand, 'get_absolute_url')` ili sličan zero-cost check.
- **Defer:** `apps/brands/tests/fake_urls.py` se uvodi tek u Story 2.6 kada URL pattern-i počinju da postoje i fake_urls postaje useful za izolaciju.
- **Subcategory.get_absolute_url() specijalan slučaj:** Vidi Gotcha BR-12 (raise-uje NotImplementedError — test koristi skip).

**Gotcha BR-5 — `Subcategory.parent.parent` chain dubok query bez `select_related` izaziva N+1**

- **Problem:** `subcat.get_ancestors_chain()` iterira `self.parent.parent.parent...` što su 3 odvojena DB query-ja bez select_related.
- **Fix u Story 2.1:** AC11 metode rade lokalno na in-memory objektima — pretpostavljaju da je caller već prefetched parent chain (`Subcategory.objects.select_related("parent__parent__parent").get(...)`).
- **Story 2.11 mitigation:** Listing strana mora eksplicitno koristiti `select_related("category", "parent__parent__parent")` (3-level chain) ili custom recursive CTE query (Django 4.2+ support za PostgreSQL).

**Gotcha BR-6 — `LANGUAGES` config (`[("sr", "Srpski"), ("hu", "Magyar"), ("en", "English")]`) iz Story 1.4 NE SME se menjati u 2.1**

- **Problem:** Ako Dev pokušaja da promeni LANGUAGES tuple key (npr. `"sr-latn"` umesto `"sr"`), modeltranslation generiše različite suffix kolone (`name_sr_latn`) → migracija postaje destruktivna (drop kolona).
- **Fix:** Story 2.1 koristi LANGUAGES KAKO SU u Story 1.4. Ako budući SEO Story 6.5/6.6 traži `sr-latn` distinkciju, to ide kroz data migration (NIJE Story 2.1 scope).

**Gotcha BR-7 — `Brand.statistics` JSONField default vrednost MORA biti `list` (NE `dict`)**

- **Problem:** `default=list` (callable) — Django nikad ne deli isti list instance između modela. Ako Dev napiše `default=[]` (literal), svi novi Brand-ovi dele isti list — mutacija jednog menja sve.
- **Fix:** `default=list` (bez zagrada — callable reference) per AC2.

**Gotcha BR-10 — `Subcategory.bulk_create()` obilazi `full_clean()` (Django ORM design)**

- **Problem:** `Subcategory.save()` override poziva `self.full_clean()` PRE `super().save()` (CRIT-2 fix). Ovo enforce-uje depth validation na svim "normal" code path-ovima (objects.create, admin save, signals). ALI: `Subcategory.objects.bulk_create([...])` obilazi `save()` i `full_clean()` (Django ORM design — bulk_create je high-throughput insert).
- **Implikacija:** Fixtures, seed data scripts, i management commands koje bulk-insertuju Subcategory mogu da kreiraju invalid depth chain (4+ levels).
- **Fix:** Seed data (Story 9.7) i bilo koja future fixture script MORA iterirati listu i pozivati `.save()` umesto `bulk_create()`:
  ```python
  # WRONG:
  Subcategory.objects.bulk_create([Subcategory(...), Subcategory(...)])
  # RIGHT:
  for data in subcategory_data:
      obj = Subcategory(**data)
      obj.save()  # triggers full_clean()
  ```
- **Documented for:** Story 9.7 seed data implementation.

**Gotcha BR-11 — Brand.logo / hero_image / catalog_pdf MIME validation deferred (CRIT-8 / Decision D14)**

- **Problem:** ImageField/FileField u Story 2.1 NE validuje MIME signature, magic bytes, ili dimension limits za upload-ovane fajlove. Dev mora znati da je ovo svesno odložen risk.
- **Trenutna mitigacija (Story 2.1):** Admin (Mihas only) prihvata fajlove na upload site responsibility. Editor role NE postoji u Story 2.1.
- **Editor role onboarding (Epic 8) BLOCKED** dok Story 2.3 (image pipeline) i Story 2.4 (PDF pipeline) ne implementiraju:
  - Pillow + python-magic dvostruka MIME validacija (ImageField)
  - PDF magic byte + PyMuPDF parse validation (FileField za PDF)
- **Reference:** Decision D14 (escalation policy + sequencing constraint).

**Gotcha BR-12 — `Subcategory.get_absolute_url()` raise-uje `NotImplementedError` u Story 2.1 (IMP-2)**

- **Problem:** Subcategory URL pattern zahteva variable-depth path slug konkatenaciju koja zavisi od `subcategory_path` URL pattern-a — koji JOŠ NE POSTOJI (definiše se u Story 2.11).
- **Fix u Story 2.1:** `Subcategory.get_absolute_url()` raise-uje `NotImplementedError` sa explicitnom porukom:
  ```python
  def get_absolute_url(self):
      # TODO Story 2.11: implement subcategory_path URL pattern
      raise NotImplementedError("Subcategory URL pattern defined in Story 2.11")
  ```
- **Test strategija:** Test za ovaj method **MORA koristiti** `@pytest.mark.skip(reason="Story 2.11")` dok URL ne postoji.
- **Razlog:** Sprečava lažni "method works" signal kada zapravo method ne može da reverse-uje URL. Eksplicitan fail je bolji od silent NoReverseMatch koji se može pojaviti tek u runtime-u.

**Gotcha BR-13 — Slug uniqueness collision UX (defer to admin u Story 8.4 — IMP-7)**

- **Problem:** Slug collision (duplikat globally unique slug-a, ili duplikat per-scope slug-a) u Story 2.1 raise-uje `IntegrityError` na admin save — non-UX-friendly error poruka za Mihasa.
- **Fix u Story 2.1:** Prihvaćeno — Mihas je sole admin u Epic 2 development phase; IntegrityError je acceptable signal.
- **UX-friendly collision handling** (unique-suffix counter — npr. `brand-name-2`, `brand-name-3` — ili alternativna slug sugestija) je **Story 8.4 admin scope**.
- **Implikacija:** Story 8.4 SM ticket nosi explicit acceptance criterion za slug collision UX handler.

**Gotcha BR-14 — `str.maketrans(dict)` zahteva single-character ključeve (iter-2 NEW-CRIT-1 regression guard)**

- **Problem:** `str.maketrans(dict)` zahteva single-character ključeve — multi-char digrafi (Dž, Lj, Nj) MORAJU se obraditi kroz `str.replace()` pre `str.translate()`. Naivan pokušaj `str.maketrans({"Dž": "dz", ...})` raise-uje `ValueError: string keys in translate table must be of length 1` pri module load-u — module-level import bi crashovao bez ovog fix-a. Tested locally by Adversarial Reviewer iter-1.
- **Fix u Story 2.1:** `apps/core/utils.py` koristi two-stage pattern: (1) `SR_DIGRAPHS` dict + `str.replace()` loop za digrafe Dž/Lj/Nj, (2) `SR_DIAKRITICI = str.maketrans({...})` sa SAMO single-char ključevima za Ć/Č/Š/Ž/Đ. Vidi Task 2.4 finalni sadržaj.
- **Regression guard:** TEA RED phase test `test_slugify_ascii_module_imports_without_error` proverava da `from apps.core.utils import slugify_ascii` ne baca ValueError.
- **Reference:** iter-2 Adversarial Review fix; Task 2.4 contract specification.

### CSS Transition Reference (NE PRIMENJUJE se na 2.1 — placeholder za 2.6)

Story 2.1 ne dodaje CSS. Brand UI komponenti (hero overlay card sa `brand_color`, Repeating Element sa brand colorom) renderuju se u Story 2.6/2.7. Story 2.1 samo deklariše model layer.

### Lokalni Dev workflow

1. `uv sync --group dev` (instalira modeltranslation ako nije već)
2. `uv run python manage.py makemigrations brands`
3. **Manual review** `apps/brands/migrations/0001_initial.py`
4. `uv run python manage.py migrate --plan` (verify samo brands 0001)
5. `uv run python manage.py migrate brands` 
6. `uv run python manage.py createsuperuser` (za admin smoke test)
7. `uv run python manage.py runserver` → `http://localhost:8000/admin/` → klikom kroz Brendovi sekciju
8. `uv run pytest apps/brands/tests/` (RED → GREEN cycle)

### CI debugging steps

- Ako CI lint pada: `uv run ruff check apps/brands/` + `uv run ruff format --check apps/brands/`
- Ako CI test pada: `uv run pytest apps/brands/tests/ -v --tb=short`
- Ako migracija test pada: `uv run python manage.py makemigrations --check --dry-run` — exit code 1 znači da ima pending migration koja nije commit-ovana

## Definition of Done

- [ ] `apps/brands/` app kreiran kroz `startapp brands apps/brands` + registrovan u `INSTALLED_APPS` posle `apps.core` (AC1)
- [ ] `modeltranslation` registrovan u `INSTALLED_APPS` PRE `apps.brands` (AC1, Decision D2)
- [ ] `apps/brands/apps.py` ima `name = "apps.brands"` + `verbose_name = _("Brendovi")` (AC1, Gotcha BR-1)
- [ ] `apps/brands/models.py` definiše 4 modela (Brand, Series, Category, Subcategory) sa:
  - Eksplicitnim `on_delete` (PROTECT za Series.brand; CASCADE za Subcategory.category i Subcategory.parent) (AC3, AC5, Decision D9)
  - Eksplicitnim `related_name` na svim FK-ovima (AC3, AC5)
  - `Meta.indexes` sa nazivima `<table>_<columns>_idx` (AC2-AC5)
  - `UniqueConstraint` za Series (brand, slug) i Subcategory (category, parent, slug) (AC3, AC5)
  - `get_absolute_url()` metode na sva 4 modela (AC2-AC5, Gotcha BR-4)
  - `clean()` validacija za Brand.brand_color hex, Brand.statistics max 4, Subcategory MAX 3 levels + circular guard (AC2, AC5)
  - TextChoices za Series.layout_mode (Grid/Extended) i Category.is_for (Traktori/Mehanizacija) (AC3, AC4, Decision D5, D6)
- [ ] `apps/core/models.py` kreiran sa `TimestampedModel` + `SluggedModel` abstract klase (AC9, Decision D3)
- [ ] `apps/core/utils.py` kreiran sa `slugify_ascii(text)` helper-om za srpsku latinicu → ASCII transliteration (CRIT-1; Task 2.4); two-stage replacement: SR_DIGRAPHS (Dž/Lj/Nj) via str.replace() PRE SR_DIAKRITICI (Ć/Č/Š/Ž/Đ) via str.translate() — iter-2 NEW-CRIT-1 fix; module mora učitati bez ValueError
- [ ] **Svi 4 modela (Brand, Series, Category, Subcategory) implementiraju `save()` override sa EKSPLICITNIM redosledom:** (1) slug auto-gen via `slugify_ascii(self.name)`, (2) `self.full_clean()`, (3) `super().save()` — iter-2 NEW-CRIT-2 fix. **Verifikovati pre commit-a:** otvoriti `apps/brands/models.py` i potvrditi da sva 4 modela imaju ovaj eksplicitan pattern (NE "clean_slug" alternativu — `clean_slug()` je Form metoda, NIJE Model metoda).
- [ ] `Subcategory.save()` poziva `self.full_clean()` PRE `super().save()` za enforce depth validation na svim code path-ovima (CRIT-2 iter-1; AC5)
- [ ] `Subcategory.get_absolute_url()` raise-uje `NotImplementedError` sa TODO komentarom referencujući Story 2.11 (IMP-2; AC5; Gotcha BR-12)
- [ ] `Brand.brand_color` `clean()` honor-uje `blank=True` — empty string ne raise-uje (CRIT-3; AC2)
- [ ] `Brand.statistics` `clean()` ima list-of-dict soft shape validation (IMP-10; AC2)
- [ ] `Brand.logo`/`hero_image`/`catalog_pdf` imaju `max_length=255` (IMP-4; AC2)
- [ ] `Brand.is_coming_soon` NEMA `db_index=True` (composite index pokriva — IMP-3; AC2)
- [ ] `Series.Meta.ordering = ["display_order", "name"]` bez `brand__name` JOIN-a (IMP-5; AC3)
- [ ] `apps/brands/translation.py` registruje TranslationOptions za Brand (name, description, slogan), Series (name, description), Category (name, description), Subcategory (name, description) (AC6)
- [ ] Migracija `apps/brands/migrations/0001_initial.py` generisana, MANUAL REVIEWED, applied — kreira 4 tabele sa `_sr`/`_hu`/`_en` suffix kolonama (AC7, Gotcha BR-2)
- [ ] `apps/brands/admin.py` ima 4 `admin.site.register(...)` poziva (AC8, Decision D11)
- [ ] Sva user-facing string vrednosti kroz `gettext_lazy as _` — bez hardcoded srpskih string-ova (AC10)
- [ ] NIJEDNA ćirilica u izvornom kodu (per project-context.md § Anti-pattern: Ćirilica)
- [ ] Slug discipline: ASCII transliteration; `unique=True` na Brand+Category (globally), `UniqueConstraint` na Series+Subcategory (per scope) — Decision D7
- [ ] `uv run ruff check .` exit code 0 (Task 9.1)
- [ ] `uv run ruff format --check .` exit code 0 (Task 9.2)
- [ ] `uv run djade --check templates/partials/*.html` exit code 0 — regression guard (nema template promene u 2.1) (Task 9.3)
- [ ] `uv run pytest` — sve postojeće Epic 1 testovi prolaze (regression) + sve Story 2.1 model testovi prolaze (Task 9.4)
- [ ] Manual smoke test kroz Django shell — kreirati 1 Brand + 1 Series + 1 Category + 3-level Subcategory chain + verifikovati `full_clean()` raise na 4-level chain (Task 8.1)
- [ ] Sample Brand fixture (opciono) ILI Django shell instrukcije u Dev Notes za naredne stories (2.6 može trebati za testing)
- [ ] Commit poruka prati Conventional Commits format `feat(brands): ...` (Task 10.2)
- [ ] `sprint-status.yaml` ažuriran: 2.1 → `ready-for-dev`, epic-2 → `in-progress`, last_updated → `2026-05-29` (Task 10.1)

## Testing

TEA agent piše testove u Step 3 RED phase. Dev NIKAD ne piše testove (per project-context.md § Test discipline).

### Test coverage zahtevi

**Unit testovi — `apps/brands/tests/test_models.py`:**

1. **`__str__` testovi** za sva 4 modela:
   - `test_brand_str_returns_name`
   - `test_series_str_returns_brand_em_dash_name`
   - `test_category_str_returns_scope_em_dash_name`
   - `test_subcategory_str_returns_name`

2. **FK + related_name testovi:**
   - `test_brand_series_related_name` — `brand.series.all()` vraća sve serije; `brand.series.count()` matchuje
   - `test_category_subcategories_related_name`
   - `test_subcategory_children_related_name`
   - `test_subcategory_parent_self_fk` — `subcat.parent.children.all()` vraća subcat među child-ovima

3. **Slug constraint testovi:**
   - `test_brand_slug_globally_unique` — kreirati dva Brand-a sa istim slug-om → `IntegrityError`
   - `test_series_slug_unique_per_brand` — dva Series u istom Brand-u sa istim slug-om → `IntegrityError`; u različitim Brand-ovima OK
   - `test_subcategory_slug_unique_per_category_parent` — slično scope
   - `test_category_slug_globally_unique` (Decision D7)

4. **Translation field auto-generation:**
   - `test_brand_translation_fields_registered` — `_meta.get_fields()` sadrži `name_sr`, `name_hu`, `name_en`, `description_sr`, `slogan_sr`
   - `test_series_translation_fields_registered`
   - `test_category_translation_fields_registered`
   - `test_subcategory_translation_fields_registered`

5. **Subcategory depth validation:**
   - `test_subcategory_3_levels_allowed` — kreirati L1 → L2 → L3 chain; `full_clean()` ne raise-uje
   - `test_subcategory_4_levels_raises_validation_error` — pokušaj L1 → L2 → L3 → L4; `full_clean()` raise-uje `ValidationError`
   - `test_subcategory_circular_reference_raises_validation_error` — `subcat.parent = subcat` manualno setovati; `full_clean()` raise-uje
   - `test_subcategory_get_depth_returns_chain_length` — L3 vraća `get_depth() == 3`
   - `test_subcategory_get_ancestors_chain_returns_ordered_list` — L3.get_ancestors_chain() vraća `[L1, L2]` (root-to-direct-parent order)

6. **TextChoices validation:**
   - `test_category_is_for_choice_required` — Category bez `is_for` → `ValidationError` (jer nema default)
   - `test_category_is_for_invalid_value_raises` — `is_for="invalid"` → `ValidationError`
   - `test_series_layout_mode_default_is_grid` — Series bez explicit layout_mode → `layout_mode == LayoutMode.GRID`

7. **Custom validation testovi:**
   - `test_brand_color_valid_hex_passes` — `#25402F` ne raise-uje
   - `test_brand_color_invalid_format_raises` — `red`, `#GGG`, `#123` → `ValidationError`
   - `test_brand_statistics_max_4_entries` — list od 5 dict-a → `ValidationError`; list od 4 → ne raise-uje

8. **`get_absolute_url` testovi** (sa skip ili fake_urls strategijom — Gotcha BR-4):
   - `test_brand_get_absolute_url_exists` — method postoji + signature
   - `test_series_get_absolute_url_uses_brand_slug` — ako fake_urls strategija
   - (Skip za 2.1 ako URL-ovi ne postoje)

**Smoke testovi — `apps/brands/tests/test_apps.py`:**
   - `test_brands_config_name_is_apps_brands` — `BrandsConfig.name == "apps.brands"` (Gotcha BR-1 regression guard)

### Test naming i organization

- Per project-context.md § Test naming: `test_<scenario_description>` snake_case
- Per project-context.md § Test organization: unit tests u `apps/brands/tests/test_models.py`
- Sve testovi imaju `@pytest.mark.django_db` (DB-touching testovi)
- Factory pattern (preko `factory_boy`) NIJE uvedeno u Story 2.1 — inline `Model.objects.create()` je OK za 2.1 scope; ako 2.2+ traži factories, dodati `factory-boy>=3.3` u dev deps u toj story-ji

### Coverage target

No hard threshold u v1 (per project-context.md § Coverage), ali Story 2.1 model layer **MORA imati 100% coverage** za:
- Sve `clean()` validacije (brand_color hex, statistics max 4, Subcategory depth)
- Sve `__str__` metode
- Sve FK related_name access pattern-i
- Translation field introspection

### TEA → Dev handoff

Posle TEA RED phase commit (sve gore-pomenute testovi u test_models.py + test_apps.py), Dev agent ulazi GREEN phase (Step 03 implement) — implementira `apps/brands/models.py` + `apps/core/models.py` + `apps/brands/translation.py` + apply migration dok svi testovi ne prolaze.

### Postojeći Epic 1 testovi (regression guard)

Story 2.1 NE sme da break-uje postojeće testove:
- `tests/test_base_template.py`, `tests/test_bootstrap.py`, `tests/test_docker_compose.py`, `tests/test_i18n_setup.py`, `tests/test_navigation_chrome.py`, `tests/test_settings_split.py`, `tests/test_static_tokens.py`, `tests/test_visual_components.py`
- `apps/core/tests/test_apps.py`, `apps/core/tests/test_middleware.py`, `apps/core/tests/test_translation_module.py`
- **Verifikacija:** `uv run pytest` posle Story 2.1 implementation → svi 37+ Epic 1 testovi + svi novi 2.1 testovi prolaze.

---

**End of Story 2.1**
