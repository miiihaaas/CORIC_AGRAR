---
story-id: "5.1"
story-key: 5-1-blogpost-category-tag-modeli-admin-stub
artifact: interface-contract
created: 2026-06-04
author: TEA / Murat (autonomous RED phase)
purpose: Canonical contract za PRVU story Epic 5 — NOVI `apps/blog/` app (Blog „Priče
         sa polja") sa 3 modela (`Category`/`Tag`/`Post`, sva 3 nasleđuju SluggedModel+
         TimestampedModel iz apps.core), modeltranslation registracijom (title/perex/body
         + name/description + name → `_sr/_hu/_en`), Blog-specific `PublishedManager`
         (status="published" AND published_at__lte=now), STUB admin (view_on_site=False),
         i jednom schema migracijom (`0001_initial` CreateModel ×3 + M2M through +
         modeltranslation kolone; NEMA data seed). FK author = `settings.AUTH_USER_MODEL`
         (PRVI author FK u projektu) on_delete=SET_NULL. `get_absolute_url` =
         `reverse("blog:detail")` (raise NoReverseMatch dotle — Gotcha PR-5). DB-value
         lock: status `"draft"`/`"published"`. 3 modela, 1 migracija, 1 manager, 1
         translation.py, 1 admin stub, 1 INSTALLED_APPS edit. 0 view/URL/forme/template/
         context_processor, 0 novi dep. Dev MORA satisfy svaku klauzulu u GREEN.
---

# Interface Contract — Story 5.1 „BlogPost + Category + Tag Modeli + Admin Stub"

Story 5.1 uvodi NOVI `apps/blog/` app (mirror apps/forms 4-1 + apps/products 2-2 scaffolding) sa:

- `class Category(SluggedModel, TimestampedModel)`, `class Tag(SluggedModel, TimestampedModel)`,
  `class Post(SluggedModel, TimestampedModel)` u `apps/blog/models.py` — svi nasleđuju apps.core
  base klase; slug auto-gen iz `name`/`title` kroz `slugify_ascii` (save()/full_clean() pattern iz
  Product 2-2). `Post.status` nested `TextChoices` DRAFT/PUBLISHED (**DB vrednosti `"draft"`/`"published"`
  — STABILAN ugovor**), `published_at` nullable, `category` FK SET_NULL, `tags` M2M, `author` FK →
  `settings.AUTH_USER_MODEL` SET_NULL. `objects` (default) + `published` (PublishedManager).
  `get_absolute_url` → `reverse("blog:detail")` (raise NoReverseMatch dotle).
- `apps/blog/managers.py:PublishedManager` — `get_queryset()` filtrira `status="published"` AND
  `published_at__lte=timezone.now()` (PER-QUERY now()).
- `apps/blog/translation.py` — registruje translatable polja → `_sr/_hu/_en`; **slug NIJE translatable**.
- `apps/blog/migrations/0001_initial.py` — CreateModel Category + Tag (PRE) + Post + M2M `post_tags`
  through + modeltranslation kolone + index `blog_post_status_pub_idx` + `swappable_dependency(AUTH_USER_MODEL)`.
  NEMA data seed.
- STUB `apps/blog/admin.py` — registruje 3 modela; `PostAdmin.view_on_site=False`; PROLAZI `manage.py
  check` + changelist 200 (NE „mirror products"; NE pun CRUD/WYSIWYG = 8.7).
- `config/settings/base.py` — `"apps.blog"` u INSTALLED_APPS POSLE `modeltranslation`.

Ovaj ugovor enumeriše file-system delta + model surface (sva 3 modela, FK/M2M on_delete+related_name,
status DB vrednosti) + PublishedManager potpis + translation scope + migracija (operations red +
swappable_dependency) + admin contract (view_on_site=False, reverse() pravilo, BL-2 rezolucija) +
settings/AppConfig touchpoint-e, koje TEA RED-phase testovi verifikuju. Dev GREEN realizuje sve
klauzule; bilo koje odstupanje vraća story u `paused`.

> **NAPOMENA O TEST POLITICI (TEA-D1):** `@pytest.mark.django_db` na svaki test koji dira DB
> (`*.objects.create`, manager queryset, admin changelist render). pytest-django (NE unittest.TestCase;
> project-context.md:233). Test useri za `author` kroz `django_user_model` fixture (= `get_user_model()`
> = `settings.AUTH_USER_MODEL`) — **NIKAD** `from django.contrib.auth.models import User` (project-context.md:595).
> `factory_boy` NIJE blog dep — test data inline kroz `*.objects.create(...)` + conftest factory helpers.

> **NAPOMENA O DB BACKEND-u (TEA-D2):** Blog testovi koriste običan PostgreSQL (NEMA FTS) — NE traže
> `requires_postgres` marker. `just test apps/blog/tests/` pokreće Docker PostgreSQL test bazu;
> `@pytest.mark.django_db` migrira `0001_initial` u test bazi automatski.

> **NAPOMENA O COLLECTION-SAFETY (TEA-D3 — KRITIČNO za RED):** apps.blog NIJE u INSTALLED_APPS pre Dev-a.
> SVI test moduli importuju `apps.blog.*` UNUTAR test funkcija/fixtura (NIKAD module-top-level) → missing
> apps.blog daje per-test FAIL (čist RED), NE collection abort koji bi oborio celu suite (ostali app-ovi
> ostaju zeleni). Migracioni test introspektuje `0001_initial` operations (IMP-7) + ORM round-trip umesto
> `migrate blog zero` round-trip-a (koji bi poremetio deljeno test-DB stanje).

---

## 1. File-system delta

| Path | Status | Vlasništvo |
|---|---|---|
| `apps/blog/__init__.py` | NOVO (Dev) | Python package marker. |
| `apps/blog/apps.py` | NOVO (Dev) | `class BlogConfig(AppConfig)`, `default_auto_field="django.db.models.BigAutoField"`, `name="apps.blog"` (sa `apps.` prefiksom — Gotcha PR-1), `verbose_name=_("Blog")` (mirror `apps/products/apps.py` ProductsConfig). |
| `apps/blog/models.py` | NOVO (Dev) | `Category`, `Tag`, `Post` — vidi §2. Import `SluggedModel`/`TimestampedModel` iz `apps.core.models`, `slugify_ascii` iz `apps.core.utils`, `PublishedManager` iz `apps.blog.managers`, `settings.AUTH_USER_MODEL`. |
| `apps/blog/managers.py` | NOVO (Dev) | `class PublishedManager(models.Manager)` — vidi §3. NE importuje `Post` na vrhu (Gotcha BL-1). |
| `apps/blog/translation.py` | NOVO (Dev) | `@register(Post)`/`(Category)`/`(Tag)` `TranslationOptions` — vidi §4. slug NIJE u fields. |
| `apps/blog/admin.py` | NOVO (Dev) | MINIMALAN STUB — vidi §6. `PostAdmin.view_on_site=False`. Registracija na POSTOJEĆI `admin.site`. |
| `apps/blog/migrations/__init__.py` | NOVO (Dev) | Package marker (NOVI app). |
| `apps/blog/migrations/0001_initial.py` | GENERISANO + MANUAL REVIEW (Dev) | `makemigrations blog` — vidi §5. CreateModel ×3 + M2M + modeltranslation kolone + index + swappable_dependency. NEMA data seed. |
| `config/settings/base.py` | EDIT (Dev) | `"apps.blog"` u `INSTALLED_APPS` — POSLE `modeltranslation` (translatable model zahtev — base.py:34) i POSLE domain app-ova. |
| `apps/blog/tests/__init__.py` | NOVO (TEA) | Package marker. |
| `apps/blog/tests/conftest.py` | NOVO (TEA) | `superuser`/`author_user` + `make_category`/`make_tag`/`make_post` factory helpers + media isolation. |
| `apps/blog/tests/test_models.py` | NOVO (TEA) | AC1 (Task 8.2) |
| `apps/blog/tests/test_published_manager.py` | NOVO (TEA) | AC3 (Task 8.4) |
| `apps/blog/tests/test_translation.py` | NOVO (TEA) | AC4 (Task 8.5) |
| `apps/blog/tests/test_migration.py` | NOVO (TEA) | AC2 (Task 8.6) |
| `apps/blog/tests/test_get_absolute_url.py` | NOVO (TEA) | AC1/SM-D6 (Task 8.3) |
| `apps/blog/tests/test_admin.py` | NOVO (TEA) | AC6 (Task 8.8) |
| `apps/blog/tests/test_app_scaffold.py` | NOVO (TEA) | AC5 (Task 8.7) |

**NETAKNUTO (regression guards):** `apps/core/models.py` (SluggedModel+TimestampedModel REUSE — NE menja se);
`apps/core/utils.py` (slugify_ascii REUSE); svi postojeći app-ovi (`products`/`brands`/`search`/`pages`/`forms`/
`media_pipeline`/`core`); `apps/pages` home `latest_posts=[]` placeholder (3-1 SM-D7); `templates/partials/
footer.html` (1-8/5-4); `apps/search` „Objave" prazna grana (2-13 SM-D3); `config/urls.py` (NEMA blog URL-ova
— 5-2/5-3); `pyproject.toml` (NEMA novog dep — NE django-taggit, NE WYSIWYG; SM-D9/D10); sve CSS/JS; sve
postojeće migracije (`makemigrations` sme dotaknuti SAMO blog/0001).
**0 view/URL/forme/template-strana/context_processor, 0 signal, 0 novi dep, 0 CSS, 0 JS.**

---

## 2. Model surface — `apps/blog/models.py`

### 2.1 `Category(SluggedModel, TimestampedModel)`

```python
class Category(SluggedModel, TimestampedModel):
    name        = CharField(_("Naziv"), max_length=200)         # translatable (AC4)
    # slug      = nasleđen SluggedModel (SlugField max_length=140 unique db_index); auto-gen iz name
    description = TextField(_("Opis"), blank=True)               # translatable (AC4)

    class Meta:
        verbose_name = _("Kategorija"); verbose_name_plural = _("Kategorije")
        ordering = ["name"]

    def __str__(self): return self.name
```
+ `save()`/`full_clean()` slug auto-gen iz `name` (vidi §2.4).

### 2.2 `Tag(SluggedModel, TimestampedModel)`

```python
class Tag(SluggedModel, TimestampedModel):
    name = CharField(_("Naziv"), max_length=100)                # translatable (AC4)
    # slug = nasleđen; auto-gen iz name

    class Meta:
        verbose_name = _("Tag"); verbose_name_plural = _("Tagovi")
        ordering = ["name"]

    def __str__(self): return self.name
```
+ `save()`/`full_clean()` slug auto-gen iz `name`.

### 2.3 `Post(SluggedModel, TimestampedModel)`

```python
class Post(SluggedModel, TimestampedModel):
    class Status(models.TextChoices):
        DRAFT     = "draft",     _("Nacrt")
        PUBLISHED = "published", _("Objavljeno")

    title        = CharField(_("Naslov"), max_length=200)                          # translatable
    # slug       = nasleđen; auto-gen iz title (globally unique)
    perex        = TextField(_("Perex"), blank=True)                               # translatable
    body         = TextField(_("Telo"), blank=True)                                # translatable (PLAIN — NE WYSIWYG)
    main_image   = ImageField(_("Glavna slika"), upload_to="blog/main/", max_length=255, blank=True, null=True)
    category     = ForeignKey("blog.Category", on_delete=SET_NULL, related_name="posts", null=True, blank=True, verbose_name=_("Kategorija"))
    tags         = ManyToManyField("blog.Tag", related_name="posts", blank=True, verbose_name=_("Tagovi"))
    author       = ForeignKey(settings.AUTH_USER_MODEL, on_delete=SET_NULL, related_name="blog_posts", null=True, blank=True, verbose_name=_("Autor"))
    status       = CharField(_("Status"), max_length=12, choices=Status.choices, default=Status.DRAFT, db_index=True)
    published_at = DateTimeField(_("Datum objave"), null=True, blank=True)

    objects   = models.Manager()       # PRVI — ostaje _default_manager (BL-3)
    published = PublishedManager()     # DRUGI — opt-in javni queryset

    class Meta:
        ordering = ["-published_at", "-created_at"]
        verbose_name = _("Objava"); verbose_name_plural = _("Objave")
        indexes = [models.Index(fields=["status", "-published_at"], name="blog_post_status_pub_idx")]

    def __str__(self): return self.title

    def get_absolute_url(self):
        return reverse("blog:detail", kwargs={"slug": self.slug})   # NoReverseMatch dotle (SM-D6)
```

**Polja (TAČNO 9 deklarisanih na Post + slug/created_at/updated_at nasleđena):**

| Polje | Tip | Napomena |
|---|---|---|
| `title` | CharField(200) | translatable; slug-source |
| `perex` | TextField(blank=True) | translatable; kratak lead |
| `body` | TextField(blank=True) | translatable; **PLAIN TextField (NE WYSIWYG model field — SM-D10)** |
| `main_image` | ImageField(upload_to="blog/main/", max_length=255, blank=True, null=True) | mirror Product.main_image |
| `category` | FK→blog.Category, **on_delete=SET_NULL**, related_name="posts", null/blank | brisanje kategorije NE briše objave |
| `tags` | M2M→blog.Tag, related_name="posts", blank | post_tags through-tabela (auto) |
| `author` | FK→**settings.AUTH_USER_MODEL**, **on_delete=SET_NULL**, related_name="blog_posts", null/blank | PRVI author FK; SM-D3 |
| `status` | CharField(max_length=12, choices=Status, default=DRAFT, db_index) | DB `"draft"`/`"published"` |
| `published_at` | DateTimeField(null=True, blank=True) | scheduled-publish kriterijum |
| `slug` | nasleđen SlugField(140, unique, db_index) | auto-gen iz title; NIJE translatable |
| `created_at`/`updated_at` | nasleđeno TimestampedModel | |

**`Status` DB vrednosti (LOCKED — STABILAN cross-story ugovor, NE menjati):**

| Member (uppercase) | DB vrednost (lowercase) | Label (gettext_lazy, pun dijakritik) |
|---|---|---|
| `Status.DRAFT` | `"draft"` | „Nacrt" |
| `Status.PUBLISHED` | `"published"` | „Objavljeno" |

`PublishedManager` + 5.2/5.3/5.4 query-i ciljaju literal `"published"`. `max_length=12` pokriva `"published"` (9).

### 2.4 slug auto-gen pattern (mirror Product 2-2 CRIT-2)

Svi modeli (Category/Tag iz `name`, Post iz `title`):
```python
def full_clean(self, *args, **kwargs):
    if not self.slug and self.<source>:
        self.slug = slugify_ascii(self.<source>)
    super().full_clean(*args, **kwargs)   # NIKAD self.clean() direktno (double-call)

def save(self, *args, **kwargs):
    if not self.slug and self.<source>:
        self.slug = slugify_ascii(self.<source>)
    self.full_clean()
    super().save(*args, **kwargs)
```
- `slugify_ascii` transliterise dijakritike (Ž→z, š→s, Đ→D) → ASCII slug. „Žetva pšenice 2026" → `zetva-psenice-2026`.
- **Slug kolizija (IMP-5):** NEMA auto-de-dup — dve objave istog title-a → drugi `save()` baca
  `ValidationError` (full_clean → validate_unique na Python nivou PRE INSERT-a) ILI `IntegrityError`
  (raw INSERT / full_clean bypass). Test asertuje `(ValidationError, IntegrityError)` OR tuple —
  IDENTIČAN Product presedan (`test_product_slug_globally_unique_raises_on_collision`). KONZISTENTNO
  sa Product-om; editor ručno menja slug (8.7). **NE dodavati de-dup petlju u 5-1** (YAGNI).

**NEMA:**
- defensive validacije (project-context.md:358). Opciono PUBLISHED→published_at `clean()` — **default: NE**
  (PublishedManager filtrira `published_at__lte=now`; scheduled-publish je feature; OQ-2).
- `is_published` boolean (SM-D2 — blog koristi JEDAN `status` field, NE products dual).
- cross-app FK osim AUTH_USER_MODEL (blog samostalan; NE FK na products/brands).

---

## 3. PublishedManager — `apps/blog/managers.py`

```python
from django.db import models
from django.utils import timezone

class PublishedManager(models.Manager):
    def get_queryset(self):
        return (
            super().get_queryset()
            .filter(status="published", published_at__lte=timezone.now())
        )
```

**Potpis + semantika (LOCKED):**
- Filtrira **OBA uslova (AND):** `status="published"` AND `published_at__lte=timezone.now()`.
- **`timezone.now()` PER-QUERY** (poziv UNUTAR `get_queryset`, NE module-level konstanta — inače zamrznuto vreme).
- **Status literal `"published"`** (string, NE `Post.Status.PUBLISHED` import) — Gotcha BL-1: izbegava
  managers↔models kružnu zavisnost (NE importuj `Post` na vrhu `managers.py`). Alternativno `self.model.Status.PUBLISHED`
  lazy unutar metode. **DB vrednost `"published"` je locked ugovor** (test asertuje `Post.Status.PUBLISHED.value == "published"`).
- **`Post.objects = models.Manager()` definisan PRVI** (Gotcha BL-3) → `Post._default_manager` ostaje `objects`
  (admin/migracije/relacije vide SAV content); `published = PublishedManager()` je opt-in za javne view-ove.

**Četiri stanja (test matrica AC3):**

| Stanje | `status` | `published_at` | U `Post.published`? |
|---|---|---|---|
| DRAFT | draft | bilo šta | NE |
| PUBLISHED + past | published | prošlost/sada | **DA** |
| PUBLISHED + None | published | None | NE (NULL <= now je False) |
| PUBLISHED + future | published | budućnost | NE (scheduled) |

`Post.objects.all()` vraća SVA 4. `Post.published.all()` vraća SAMO „PUBLISHED + past".

---

## 4. Translation — `apps/blog/translation.py`

```python
from modeltranslation.translator import TranslationOptions, register
from apps.blog.models import Category, Post, Tag

@register(Post)
class PostTranslationOptions(TranslationOptions):
    fields = ("title", "perex", "body")

@register(Category)
class CategoryTranslationOptions(TranslationOptions):
    fields = ("name", "description")

@register(Tag)
class TagTranslationOptions(TranslationOptions):
    fields = ("name",)
```

- modeltranslation auto-discovery (apps.blog POSLE `modeltranslation` u INSTALLED_APPS) → generiše virtuelna
  polja `title_sr/_hu/_en`, `perex_*`, `body_*`, `name_*` (Category+Tag), `description_*` → DB kolone u 0001.
- **`slug` NIJE u `fields`** (SM-D7 — jezik-neutralan ASCII; mirror products). NEMA `slug_sr/_hu/_en`.
- sr fallback kroz `MODELTRANSLATION_FALLBACK_LANGUAGES=("sr",)` (base.py:152) — prazna `hu` varijanta → `sr`.
- `manage.py check` exit 0 (registracija ne baca).

---

## 5. Migracija — `apps/blog/migrations/0001_initial.py`

`makemigrations blog` generiše + Dev MANUAL REVIEW (project-context.md:221):

- **`CreateModel("Category")` + `CreateModel("Tag")` PRE `CreateModel("Post")`** (IMP-6 — Post FK-uje Category +
  M2M-uje Tag → moraju postojati pre Post; Django obično ispravno ordinira, ali manual review POTVRĐUJE).
- **M2M `post_tags` through-tabela** (auto kroz `Post.tags`).
- **modeltranslation `_sr/_hu/_en` kolone** za sva translatable polja: `title/perex/body` (Post),
  `name/description` (Category), `name` (Tag) = 6 translatable polja × 3 = 18 kolona.
- **`models.Index(fields=["status","-published_at"], name="blog_post_status_pub_idx")`** (ime 25 char ≤30 →
  vanilla `models.Index`, NE `_ProductIndex` subclass — Gotcha BL-4).
- **`status` kolona `max_length >= 9`** (pokriva `"published"`; story koristi 12).
- **`migrations.swappable_dependency(settings.AUTH_USER_MODEL)`** u `dependencies` (author FK; Django auto-generiše).
- **NEMA data seed** — blog startuje PRAZAN (objave runtime kroz admin 8.7).
- **REGRESSION:** `makemigrations --check --dry-run` posle apply → SAMO blog/0001 (nijedan postojeći app NE
  dobija novu migraciju dodavanjem apps.blog). Ako bilo koji postojeći app dobije izmenu → STOP, istraži.
- CreateModel auto-reverzibilan (`migrate blog zero` čisto). Commit modela+migracije ZAJEDNO (atomic).

---

## 6. Admin contract — `apps/blog/admin.py` (MINIMALAN STUB)

- `@admin.register(Post)`/`(Category)`/`(Tag)` na POSTOJEĆI `admin.site` (pojavljuju se pod „Blog").
- `PostAdmin`: `list_display=("title","category","status","published_at","author")`,
  `list_filter=("status","category","tags")`, `date_hierarchy="published_at"`, **`view_on_site=False`** (IMP-1/BL-5).
- `CategoryAdmin`: `list_display=("name","slug")`. `TagAdmin`: `list_display=("name","slug")`.
- `search_fields` + `prepopulated_fields` — **Gotcha BL-2 (Dev bira što PROLAZI `check`):** sa modeltranslation
  base `title`/`name`/`perex`/`body` postaju virtuelni (realne kolone `_sr/_hu/_en`) → `prepopulated_fields=
  {"slug":("title",)}` može baciti `admin.E030`; `search_fields=("title",...)` može baciti `FieldError`. Tri opcije:
  (a) `class PostAdmin(TranslationAdmin)` iz `modeltranslation.admin`; (b) sr-suffiksovane kolone (`title_sr`,
  `name_sr`); (c) ukloni `prepopulated_fields`/suzi `search_fields` i defer richer search za 8.7 (slug auto-gen
  ostaje u `save()` — model-level). **Cilj: stub PROLAZI `manage.py check` + changelist 200 + add-view 200.**

**⛔ `PostAdmin.view_on_site=False` (IMP-1/BL-5 — KRITIČNO):** Post ima `get_absolute_url` → admin renderuje
„View on site" dugme čiji klik poziva `reverse("blog:detail",...)` → `NoReverseMatch` → **HTTP 500** (blog URL-ovi
NE postoje do 5.2/5.3). `view_on_site=False` sprečava render dugmeta. Category/Tag nemaju `get_absolute_url`
(dugme se ne renderuje). Re-enable u 8.7/5.3.

**⛔ reverse() PRAVILO (LOCKED):** admin pod `i18n_patterns` → stvarni URL je locale-prefiksovan
(`/sr/admin/blog/post/...`). Test/smoke MORA koristiti `reverse("admin:blog_post_changelist")` /
`..._category_changelist` / `..._tag_changelist` (+ `_add`/`_change`). **NIKAD** hardkodovan `/admin/` ni `/sr/admin/`.

**NIJE pun CRUD:** NEMA WYSIWYG body editor, NEMA inline image upload/preview, NEMA color picker, NEMA
multi-locale tab UI (= Epic 8 Story 8.7). 5-1 STUB je za inicijalni admin pregled/unos.

---

## 7. Settings / AppConfig touchpoints

**`config/settings/base.py` (EDIT):**
- `INSTALLED_APPS` += `"apps.blog"` — **POSLE `modeltranslation`** (translatable model zahtev — base.py:34) i
  POSLE domain app-ova (blog je samostalan content app; redosled posle products/pages/forms OK).

**`apps/blog/apps.py` (NOVO):**
```python
class BlogConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.blog"            # KRITIČNO — sa apps. prefiksom (Gotcha PR-1)
    verbose_name = _("Blog")
```

- blog dep boundary: importuje SAMO `apps.core` (SluggedModel/TimestampedModel/slugify_ascii) + Django +
  modeltranslation + `settings.AUTH_USER_MODEL`. **NE importuje products/brands/search/pages/forms** (SM-D1).
- **`pyproject.toml` (NETAKNUT):** NEMA `uv add` — NE django-taggit (custom Tag model; SM-D9), NE WYSIWYG lib
  (plain body TextField; SM-D10).

---

## 8. AC → test traceability

| AC | Test fajl | Testovi (br.) |
|---|---|---|
| AC1 | `test_models.py` | inheritance (SluggedModel+TimestampedModel); nasleđena slug/created_at/updated_at polja; Category polja+slug+str+ordering; Tag polja+slug+str+ordering; Post skalarna polja; category FK SET_NULL related_name; tags M2M related_name; **author FK = AUTH_USER_MODEL** SET_NULL related_name; no-cross-app-FK; Status DB vrednosti (draft/published, **IMP-3 lock**); status default DRAFT db_index; novi Post = DRAFT; slug auto-gen; str; **slug kolizija → (ValidationError, IntegrityError) (IMP-5)**; Meta.ordering; Meta.index blog_post_status_pub_idx; objects+published manageri; verbose_name dijakritik; AUTH_USER_MODEL setting | 21 |
| AC1/SM-D6 | `test_get_absolute_url.py` | get_absolute_url raise NoReverseMatch (PR-5); definisan callable | 2 |
| AC3 | `test_published_manager.py` | published=SAMO PUBLISHED+past; DRAFT excluded; published_at=None excluded; future excluded; objects=svih 4; **_default_manager=objects (BL-3)**; now() per-query; **IMP-3 DB-value lock** | 8 |
| AC4 | `test_translation.py` | 3 modela u translator; Post title/perex/body × _sr/_hu/_en; Category name/description × suffix; Tag name × suffix; **slug NIJE translatable**; sr fallback | 6 |
| AC2 | `test_migration.py` | 0001 Migration postoji; **CreateModel Category/Tag PRE Post (IMP-6)**; **swappable_dependency AUTH_USER_MODEL**; status round-trip „published"; translation kolone persist; M2M post_tags through+related_name; index u Meta; **makemigrations --check no-changes (REGRESSION)**; NEMA data seed (count==0) | 9 |
| AC5 | `test_app_scaffold.py` | BlogConfig.name=="apps.blog"; default_auto_field BigAutoField; u INSTALLED_APPS; POSLE modeltranslation; **dep boundary (ne importuje products/brands/search/pages/forms)**; manage.py check čist | 6 |
| AC6 | `test_admin.py` | 3 modela registrovana; **PostAdmin.view_on_site is False (IMP-1)**; Post changelist 200 (sa redom — NE triggeruje get_absolute_url); Category changelist 200; Tag changelist 200; Post add-view 200 (BL-2 prepopulated/search PROLAZI); admin system checks čist | 7 |

**Test count (TEA RED phase):** models=21, get_absolute_url=2, published_manager=8, translation=6,
migration=9, app_scaffold=6, admin=7. **Ukupno = 59 test funkcija.**

---

## 9. RED-phase očekivanje

Pre Dev GREEN: `apps/blog/` NE postoji (app, modeli, managers, translation, admin, migracija);
`apps.blog` NIJE u INSTALLED_APPS. Svi NOVI testovi MORAJU pasti:
`ModuleNotFoundError: No module named 'apps.blog'` / `ImportError` (`apps.blog.models`/`managers`/`apps`) /
`NoReverseMatch` (`admin:blog_post_changelist`) / `LookupError` / assertion.

**Dozvoljeni IZUZECI u RED fazi (NE-blokirajući, NE zavise od apps.blog):**
- `test_app_scaffold.py::test_blog_config_default_auto_field` ne važi pre app-a (import pada — RED ok).
- `test_app_scaffold.py::test_dep_boundary_*` i `test_manage_check_clean` — direktorijum ne postoji →
  asertuju „apps/blog/ MORA postojati" → FAIL (RED ok); `run_checks()` može biti čist pre apps.blog ali
  je u istom fajlu sa scaffolding assertion-ima koji padaju.

Bilo koji DRUGI neočekivani PASS znači preslab test → istraži/ojačaj. Postojeći testovi drugih app-ova
MORAJU ostati zeleni (apps.blog nije u INSTALLED_APPS, guard-ovani importi → bez collection abort-a).
