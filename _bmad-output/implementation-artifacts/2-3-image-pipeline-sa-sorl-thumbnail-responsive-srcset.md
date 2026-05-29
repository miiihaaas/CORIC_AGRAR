---
story-id: "2.3"
story-key: 2-3-image-pipeline-sa-sorl-thumbnail-responsive-srcset
title: Image Pipeline sa sorl-thumbnail + Responsive Srcset
status: review
epic_num: 2
epic_title: Public Catalog — Browse Brands & Products
module: apps/media_pipeline/ (NOVO Django app — utility/cross-cutting app u Epic 2)
created: 2026-05-29
last_modified: 2026-05-29
author: Mihas (SM autonomous)
---

# Story 2.3: Image Pipeline sa sorl-thumbnail + Responsive Srcset

Status: review

## Opis

As a **dev (Mihas) koji nastavlja Epic 2 (Public Catalog) posle Story 2.1 (brands taksonomija) i 2.2 (Product i 6 related modela)**,
I want **utility Django app `apps/media_pipeline/` koji uvodi: (a) konfiguraciju `sorl-thumbnail` paketa u `config/settings/base.py` (`THUMBNAIL_BACKEND`, `THUMBNAIL_KVSTORE`, `THUMBNAIL_FORMAT`, `THUMBNAIL_QUALITY`, `THUMBNAIL_PREFIX` per Decision MP-D7, `THUMBNAIL_PRESERVE_FORMAT`), (b) `apps/media_pipeline/utils.py` sa `validate_image_mime()` funkcijom koja koristi `python-magic` (`libmagic` system dep) + `Pillow Image.verify()` double-check pattern per project-context.md § Anti-pattern: File upload bez double-check, (c) reusable Django template tag `{% responsive_picture <imagefield> alt=... sizes=... %}` u `apps/media_pipeline/templatetags/media_tags.py` koji renderuje `<picture>` element sa srcset varijantama 400w/800w/1600w (mobile/tablet/desktop responsive breakpoints koji prate DESIGN.md § Responsive grid)**,
so that **svi Product, ProductImage, ProductVariant, ProductTestimonial, Brand i Series image polja (iz Story 2.1/2.2) dobijaju automatski responsive thumbnail pipeline koji 2.6 (Brand Listing), 2.7 (Product Detail), 2.8/2.9 (Tractor/Used Listing) i Epic 3 (Home strana) MOGU direktno da konzumiraju kroz `{% responsive_picture %}` tag, a sve upload polje na svim formama (admin u 8.x + future contact forms) dobijaju jedan kanonski `validate_image_mime()` helper koji elimiše ad-hoc MIME proveru u svakoj formi. Ovo je **utility/cross-cutting app** (per architecture.md § App dependency graph line 732: `media_pipeline ← (utility, importovan od products + brands + blog)`) — može da bude importovan od bilo kog domain app-a, sam ne sme uvoziti domain app-ove (NEMA `apps.products`, `apps.brands` import-a u `media_pipeline/`).**

Ova story je **prvi utility Django app u Epic 2** i istovremeno **prva story koja konzumira `sorl-thumbnail` paket** koji je dodat u `pyproject.toml` u Story 1.1 ali još nije konfigurisan, kao i `python-magic` koji je takođe dostupan kao dep ali bez kanonskog helper-a. Story 2.3 uvodi `apps/media_pipeline/` direktorijum kao **utility app bez modela** (NEMA `models.py` sadržaj, NEMA migracija — utility helpers + template tags only), registruje `sorl.thumbnail` u `INSTALLED_APPS` (sorl-thumbnail zahteva da bude registrovan kao Django app za auto-discovery template tag-ova i admin integration-a), konfiguriše `THUMBNAIL_*` settings u `config/settings/base.py` (posle `STORAGES` blok, pre `BOOTSTRAP5` blok), i dodaje JEDNU migraciju za sorl-thumbnail KVStore tabelu (`thumbnail_kvstore` — sorl-thumbnail generates ovaj kao migracija svog paketa kad se `sorl.thumbnail` registruje u `INSTALLED_APPS` i pokrene `migrate`). **Story 2.3 NIJE dodaje image polja** (sve image polja su već definisane u 2.1 Brand/Series i 2.2 Product/ProductImage/ProductVariant/ProductTestimonial); **Story 2.3 NIJE dodaje image upload validaciju na admin formama** (to je Editor role onboarding gate u Epic 8 — vidi 2.1 Decision D14 / Gotcha BR-11); Story 2.3 **uvodi helper koji 8.x admin forme MORAJU pozvati** kroz `clean_<field>()` metode.

**Foundation za:**

- **Story 2.4 (PDF Cover-thumbnail Generator):** koristi `apps/media_pipeline/` direktorijum (već kreiran u 2.3), proširuje `apps/media_pipeline/utils.py` sa `generate_pdf_cover_thumbnail()` koji koristi `pdf2image` (`poppler-utils` system dep — već u Dockerfile per Story 1.3), i kreira `apps/media_pipeline/signals.py` sa `post_save` handler-om za `ProductBrochure` (Story 2.2 model). 2.4 uvodi `apps/media_pipeline/apps.py.ready()` hook za signal registraciju — Story 2.3 NIJE uvodi `ready()` hook (utility-only u 2.3).
- **Story 2.6 (Brand Listing strana sa Grid/Extended Layout-om):** konzumira `{% responsive_picture brand.logo alt=brand.name sizes="(max-width: 768px) 100vw, 50vw" %}` u `templates/brands/partials/brand_hero_card.html` i `{% responsive_picture product.main_image alt=product.name sizes="(max-width: 768px) 100vw, 25vw" %}` u `templates/products/partials/product_card.html` (Grid layout 4 kolone) i `templates/products/partials/product_extended_row.html` (Extended layout 1 red).
- **Story 2.7 (Product Detail strana):** konzumira `{% responsive_picture %}` u 4 lokacije: (a) hero overlay card glavna slika (`product.main_image` ili `product.images.first().image`), (b) gallery carousel slike (`product.images.all()` loop), (c) variant selektor kartice (`product.variants.all()` loop), (d) testimonial slider fotografije (`product.testimonials.all()` loop).
- **Story 2.8 / 2.9 (Tractor / Used Listing sa HTMX filterima):** konzumira `{% responsive_picture product.main_image sizes="(max-width: 768px) 100vw, 33vw" %}` u listing kartici (HTMX partial template); thumbnail-ovi se generišu lazy on-demand pri prvom HTTP GET-u na URL slike (sorl-thumbnail standard pattern — NE post-save signal koji bi generisao SVE varijante odjednom).
- **Story 2.10 / 2.11 / 2.12 (Jeegee / Subcategory / HZM-Tulip-Mix strane):** koriste isti `{% responsive_picture %}` pattern za brand i category prikaze.
- **Story 3.1 (Home strana sa svim sekcijama):** koristi `{% responsive_picture %}` za featured products carousel + brand logos grid + hero overlay slike.
- **Story 5.3 (Blog post detail strana):** koristi `{% responsive_picture blog_post.cover_image %}` (Epic 5 dodaje BlogPost model sa cover image poljem).
- **Story 8.6 (Product CRUD admin sa multi-locale):** koristi `validate_image_mime()` u `clean_main_image()` / `clean_image()` ProductForm metodama; admin **MORA** da odbije non-image upload sa friendly ValidationError porukom. **Ovo je security MUST per project-context.md § File upload polja: "double-check (Pillow Image.verify() ZA slike + python-magic ZA MIME) u `clean_<field>`"**.
- **Story 8.4 (Brand CRUD admin):** isto pattern — `clean_logo()`, `clean_hero_image()` u `BrandForm` koriste `validate_image_mime()` (CRIT-8 / Decision D14 iz Story 2.1 — Editor role onboarding gate za Brand image upload polja).

**Princip:** Jedan novi Django app (`apps/media_pipeline/`) **bez modela** (utility-only — `models.py` ostaje prazan, NEMA migracije za media_pipeline) sa: jednim helper module-om (`utils.py`), jednim templatetags module-om (`templatetags/media_tags.py`), kanonskom sorl-thumbnail konfiguracijom u `config/settings/base.py`, i registracijom `sorl.thumbnail` u `INSTALLED_APPS` (sa odgovarajućim KVStore migracijom iz sorl-thumbnail paketa). **Translation polja se NE dodaju** (utility app — ne podržava i18n direktno; UI strings koje helper-i generišu (npr. error poruke u `validate_image_mime()`) prolaze kroz `gettext_lazy`). **NEMA models.py promena**, **NEMA admin.py promena u 2.3** — admin integration je 8.x scope.

**Strukturna arhitektura — repository delta:** Repository dobija novi direktorijum `apps/media_pipeline/` sa Django app skeleton-om. `django-admin startapp media_pipeline apps/media_pipeline` generiše: `__init__.py`, `apps.py`, `admin.py`, `models.py`, `tests.py`, `views.py`, `migrations/__init__.py`. Story 2.3 **briše** default-no generisane fajlove koje ne treba (`tests.py` → kreira se `tests/` direktorijum; `views.py` → utility app nema views; `admin.py` → utility app nema admin; `models.py` ostaje prazan ali NE briše se — sorl-thumbnail migration discovery može zatražiti `app_label` kontekst kroz `AppConfig`). Story 2.3 dodaje SAMO `utils.py`, `templatetags/__init__.py`, `templatetags/media_tags.py` u Step 1 deliverable. `config/settings/base.py` dobija **DVA dodatka** u `INSTALLED_APPS`: `"sorl.thumbnail"` (POSLE `apps.products` — sorl-thumbnail je third-party app, ne domain) i `"apps.media_pipeline"` (POSLE `sorl.thumbnail` — utility app može uvoziti sorl-thumbnail template tag-ove). `config/settings/base.py` takođe dobija **THUMBNAIL_* settings blok** posle `STORAGES` blok. **Migracija za `sorl.thumbnail`** se generiše automatski kad se `migrate` pokrene posle registracije — ovo je sorl-thumbnail vlasništvo, NIJE Story 2.3 deliverable kao `apps/media_pipeline/migrations/0001_initial.py`. **`apps/brands/` i `apps/products/` ostaju netaknuti** — Story 2.3 NE dodaje image polja, samo uvodi pipeline koji 2.6+ konzumira preko `{% responsive_picture %}` template tag-a.

## Kriterijumi prihvatanja

**AC1 — `apps/media_pipeline/` Django utility app je kreiran i registrovan u `INSTALLED_APPS` POSLE `apps.products`; `sorl.thumbnail` registrovan POSLE `apps.products` i PRE `apps.media_pipeline`**

- **Given** Story 2.2 završena (`apps/products/` registrovan u `INSTALLED_APPS` sa 7 modela; `pyproject.toml` ima `sorl-thumbnail>=13.0.0`, `python-magic>=0.4.27`; Dockerfile ima `libmagic1` i `poppler-utils` system deps već instalirane per Story 1.3)
- **When** kreiram `apps/media_pipeline/` kroz `uv run python manage.py startapp media_pipeline apps/media_pipeline` i dodajem app-ove u `INSTALLED_APPS`
- **Then** sledeća struktura mora postojati:
  - Direktorijum `apps/media_pipeline/` u repository root-u
  - `apps/media_pipeline/__init__.py` (prazan)
  - `apps/media_pipeline/apps.py` sa `MediaPipelineConfig(AppConfig)` klasom:
    - `default_auto_field = "django.db.models.BigAutoField"`
    - `name = "apps.media_pipeline"` (KRITIČNO — sa `apps.` prefiksom; matches `INSTALLED_APPS` entry; mirror 2.1/2.2 BR-1/PR-1 gotcha)
    - `verbose_name = _("Media pipeline")` (locale-aware kroz `gettext_lazy`)
  - `apps/media_pipeline/models.py` (ostaje prazan — utility-only; NEMA modela u 2.3; 2.4 takođe ne dodaje modele jer signals.py koristi `post_save` na `ProductBrochure` iz `apps.products.models`)
  - `apps/media_pipeline/utils.py` (NOVO — Task 2 deliverable; sadrži `validate_image_mime()` funkciju)
  - `apps/media_pipeline/templatetags/__init__.py` (NOVO — Task 3 prerequisite; prazan paket marker)
  - `apps/media_pipeline/templatetags/media_tags.py` (NOVO — Task 3 deliverable; sadrži `{% responsive_picture %}` template tag)
  - `apps/media_pipeline/tests/` direktorijum (NOVO — Task 1.2; Dev kreira **BEZ `__init__.py`** per TEA REVIEW FIX MP-R1 — kolizija sa root `tests/__init__.py` zbog `importlib` mode-a; testovi su TEA scope u Step 3)
  - `apps/media_pipeline/migrations/__init__.py` (auto-kreiran kroz startapp; ostaje prazan jer NEMA modela u 2.3)
- **And** `apps/media_pipeline/tests.py` je obrisan (mirror 2.1/2.2 disciplina — `tests/` direktorijum, NE `tests.py` fajl)
- **And** `apps/media_pipeline/views.py` je obrisan (utility app NEMA views — mirror 2.2 IMP-iter4-3 discipline)
- **And** `apps/media_pipeline/admin.py` je obrisan (utility app NEMA admin registracija — sorl-thumbnail KVStore se ne registruje custom u admin-u; ostavlja se default sorl-thumbnail behavior)
- **And** `config/settings/base.py` `INSTALLED_APPS` lista dobija **DVA nova entry-ja** APENDOVANA na kraj liste u TAČNOM redosledu (mirror 2.1 D2 / 2.2 PR-D1 dependency-ordered pattern):
  - **VAŽNO — NE rewrite-uj literalni `INSTALLED_APPS` blok.** Live `config/settings/base.py` (linije 41-45) sadrži trailing komentare `# NOVO Story 1.6`, `# NOVO Story 2.1`, `# NOVO Story 2.2` koji su SOURCE OF TRUTH i MORAJU biti preserved.
  - Dev MUST koristiti targeted **Edit tool** da APENDUJE TAČNO dve nove linije:
    - `"sorl.thumbnail",  # NOVO Story 2.3 — third-party paket POSLE domain app-ova (utility lib)` posle `"apps.products",                # NOVO Story 2.2 — ...`
    - `"apps.media_pipeline",  # NOVO Story 2.3 — utility app POSLE sorl.thumbnail (koristi njegove template tags)` posle `"sorl.thumbnail",`
  - Dev MUST NOT prepisivati postojeće linije, MUST NOT strip-ovati trailing komentare, MUST NOT reordovati listu.
  - Verifikacija pre Edit-a: `Select-String -Path config/settings/base.py -Pattern '"apps.products"'` mora vratiti tačno jednu liniju.
  - **Diff su tačno dve linije** — targeted Edit operacija u Task 1.4.
- **And** Django auto-reload startuje bez `ImportError`, `ImproperlyConfigured` ili `RuntimeError` (smoke verifikacija: `uv run python manage.py check` exit code 0).
- **And** `apps/media_pipeline/__init__.py` je prazan — bez `default_app_config` declaracije (Django 3.2+ auto-detektuje `AppConfig` u `apps.py`).

**AC2 — `config/settings/base.py` ima kanonski blok `THUMBNAIL_*` settings (sorl-thumbnail konfiguracija)**

- **Given** AC1 završeno (sorl.thumbnail registrovan u INSTALLED_APPS)
- **When** dodajem `THUMBNAIL_*` settings u `config/settings/base.py` POSLE `STORAGES` blok i PRE `BOOTSTRAP5` blok
- **Then** sledeći settings moraju biti definisani sa TAČNO ovim vrednostima:
  ```python
  # ── sorl-thumbnail (Story 2.3) ───────────────────────────────────────────────
  # Image pipeline za responsive srcset (400w/800w/1600w varijante) na svim
  # Product/Brand/ProductImage/ProductVariant/ProductTestimonial image poljima.
  # Lazy generation: thumbnail-ovi se kreiraju on-demand pri prvom HTTP GET-u
  # na URL slike, NE post-save signal.
  # Vidi project-context.md § Media pipeline + architecture.md § Image processing.
  THUMBNAIL_BACKEND = "sorl.thumbnail.base.ThumbnailBackend"
  THUMBNAIL_KVSTORE = "sorl.thumbnail.kvstores.cached_db_kvstore.KVStore"
  THUMBNAIL_FORMAT = "JPEG"  # default output format (override per call kroz `format="WEBP"` ako treba)
  THUMBNAIL_QUALITY = 85  # JPEG quality — balansa veličina/kvalitet (sorl default 95 prevelik za web)
  THUMBNAIL_PRESERVE_FORMAT = False  # konvertuj sve u JPEG (PNG transparency se gubi — per-call override kroz `format='PNG'` u {% responsive_picture %} tag — vidi Decision MP-D5)
  # FIX-7 / Decision MP-D7: kanonski sorl-thumbnail setting je THUMBNAIL_PREFIX
  # (sa trailing slash), NE THUMBNAIL_DIRNAME (koji NE postoji u sorl source-u —
  # silent no-op assignment u prethodnoj verziji story spec-a).
  THUMBNAIL_PREFIX = "thumbnails/"  # subdir u MEDIA_ROOT — sorl konkatenira sa storage path-om
  # FIX-3 (Security HIGH-2): hardcoded False u svim env-ovima — sorl returnuje stack
  # trace sa Pillow verzijom i MEDIA_ROOT putanjom kad je True, što je info-leak
  # rizik ako DEBUG=True curne u staging. Dev investigation: explicit True u development.py.
  THUMBNAIL_DEBUG = False
  ```
- **And** `MEDIA_URL = "/media/"` i `MEDIA_ROOT = BASE_DIR / "media"` MORAJU biti definisani u `config/settings/base.py`. **Verifikuj prisustvo iz Story 1.2 (Multi-environment settings split) ili Story 1.3 (Docker compose sa media volume)** kroz Select-String pre Edit-a. **Ako NE postoje** (možda previd u prethodnim story-ima), dodaj odmah posle `STATIC_ROOT` definicije:
  ```python
  # ── Media ────────────────────────────────────────────────────────────────────
  # MEDIA_URL ima leading slash radi i18n_patterns kompatibilnosti (matches STATIC_URL pattern).
  # MEDIA_ROOT je BASE_DIR/media (development); production override može menjati za Nginx serving.
  MEDIA_URL = "/media/"
  MEDIA_ROOT = BASE_DIR / "media"
  ```
- **And** `development.py` može override-ovati `THUMBNAIL_DEBUG = True` (opciono, NE obavezno u Story 2.3 — Mihas može dodati kasnije ako treba debug-ovati zašto thumbnail nije generisan).
- **And** `config/urls.py` mora da servira `MEDIA_URL` u development-u kroz `static()` helper (Django 5.2 standard pattern — ako već nije dodato, dodaj kroz `from django.conf.urls.static import static` i `urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)` u `DEBUG` block-u).

**AC3 — `apps/media_pipeline/utils.py` sadrži `validate_image_mime()` funkciju sa python-magic + Pillow double-check**

- **Given** AC1 završeno (apps/media_pipeline kreiran)
- **When** kreiram `apps/media_pipeline/utils.py`
- **Then** fajl mora imati TAČNO sledeću strukturu:
  ```python
  """Media pipeline utility helpers — image MIME validacija + Pillow signature check.

  Story 2.3 (Epic 2) utility-only deliverable. NEMA modela. NEMA admin.
  Konzumiran od Epic 8 admin forme (Story 8.4/8.6) i future contact forms (Epic 4).

  Per project-context.md § Anti-pattern: File upload bez double-check —
  ImageField/FileField u Django default validate file extension samo (`.jpg`, `.png`),
  NE MIME signature. Treba dvostruka provera:
    1. python-magic na prvih 2048 bytes — detect real MIME iz signature
    2. PIL Image.verify() — verify image structure integrity (nije corrupt)

  System dependency: libmagic1 (Dockerfile per Story 1.3) — bez nje python-magic
  importuje ali magic.from_buffer() raise-uje na svakom poziv.
  """

  from __future__ import annotations

  from typing import Iterable

  import magic
  from django.core.exceptions import ValidationError
  from django.core.files.uploadedfile import UploadedFile
  from django.utils.translation import gettext_lazy as _
  from PIL import Image, UnidentifiedImageError

  ALLOWED_IMAGE_MIME_TYPES: tuple[str, ...] = (
      "image/jpeg",
      "image/png",
      "image/webp",
  )
  MIME_SNIFF_BYTES: int = 2048  # standard libmagic recommendation
  MAX_UPLOAD_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB — DoS guard za image upload
  #   Razlog: 50MB+ JPEG → 3× thumbnail gen u Pillow → OOM kill u Gunicorn worker-u.
  #   Per project-context.md § Security must-haves: file size validation na upload boundary.


  def validate_image_mime(
      upload: UploadedFile,
      *,
      allowed_mimes: Iterable[str] = ALLOWED_IMAGE_MIME_TYPES,
      max_size_bytes: int = MAX_UPLOAD_SIZE_BYTES,
  ) -> None:
      """Double-check da je upload validna slika kroz MIME signature + Pillow verify + size limit.

      Raise-uje ValidationError sa locale-aware porukom ako:
      - File je prazan (0 bytes) ili `upload is None`
      - File je veći od `max_size_bytes` (DoS guard; default 10MB)
      - python-magic detect-uje MIME koji NIJE u allowed_mimes
      - PIL Image.verify() raise-uje UnidentifiedImageError ili SyntaxError

      Side-effect: upload.seek(0) na ulazu i izlazu (caller nije obavezan da reset-uje).

      Args:
          upload: Django UploadedFile (in-memory ili temp file)
          allowed_mimes: iterable MIME stringova; default JPEG/PNG/WebP
          max_size_bytes: maksimalna veličina upload-a; default 10MB

      Raises:
          ValidationError: sa porukom prikladnom za form `clean_<field>()` re-raise

      Usage:
          # u FormClass.clean_<image_field>():
          image = self.cleaned_data["main_image"]
          validate_image_mime(image)
          return image
      """
      if upload is None or not upload.size:
          # `not upload.size` hvata i 0 i None — neki UploadedFile subclass-ovi (npr. TemporaryUploadedFile
          # tokom streaming-a) mogu vratiti None za .size dok je upload u progresu.
          raise ValidationError(_("Slika je prazna ili nije priložena."))

      if upload.size > max_size_bytes:
          raise ValidationError(
              _("Slika je veća od %(limit)d MB. Maksimalna dozvoljena veličina je %(limit)d MB.")
              % {"limit": max_size_bytes // (1024 * 1024)}
          )

      upload.seek(0)
      header = upload.read(MIME_SNIFF_BYTES)
      upload.seek(0)

      detected_mime = magic.from_buffer(header, mime=True)
      if detected_mime not in allowed_mimes:
          raise ValidationError(
              _("Nedozvoljen tip slike: %(mime)s. Dozvoljeni tipovi: %(allowed)s.")
              % {
                  "mime": detected_mime,
                  "allowed": ", ".join(allowed_mimes),
              }
          )

      try:
          # Image.verify() troši stream — moramo opet seek(0) posle
          Image.open(upload).verify()
      except (UnidentifiedImageError, SyntaxError, OSError) as exc:
          raise ValidationError(
              _("Slika je oštećena ili nije validan format.")
          ) from exc
      finally:
          upload.seek(0)
  ```
- **And** funkcija NIKAD ne raise-uje `magic.MagicException` direktno — ako `libmagic1` system dep nedostaje (npr. lokalni Windows dev bez Windows magic binary), `import magic` se neće učitati i utility module raise-uje `ImportError` na startup-u. Story 2.3 Dev Notes dokumentuje Windows local dev workaround (vidi Dev Notes § Local development na Windows-u bez libmagic).
- **And** `validate_image_mime` koristi `gettext_lazy as _` za sve error poruke (per project-context.md § gettext / i18n u kodu).
- **And** `validate_image_mime` ne logu-je (no `logger.error()` poziva) — caller form decides kako da reaguje na ValidationError; helper je čist (no side-effects osim upload.seek(0)).
- **And** **NEMA hardcoded MIME stringova u helper-u OSIM** `ALLOWED_IMAGE_MIME_TYPES` konstante — caller može override-ovati kroz keyword arg za future extension (npr. SVG support tek u Epic 9 polish ako se odluči).
- **And** **`validate_image_mime` MORA proveriti size limit** kroz `MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024` konstantu (DoS guard — 50MB+ JPEG → 3× thumbnail gen → OOM kill u Gunicorn worker-u). Helper raise-uje ValidationError sa lokaliziranom porukom `_("Slika je veća od %(limit)d MB.")` ako `upload.size > max_size_bytes` (caller može override kroz keyword arg za special cases).

**AC4 — `apps/media_pipeline/templatetags/media_tags.py` sadrži `{% responsive_picture %}` template tag koji renderuje `<picture>` sa srcset varijantama 400w/800w/1600w + `format` kwarg za PNG transparency preservation**

- **Given** AC1 i AC2 završeno (sorl.thumbnail registrovan, settings konfigurisan)
- **When** kreiram `apps/media_pipeline/templatetags/__init__.py` (prazan) i `apps/media_pipeline/templatetags/media_tags.py`
- **Then** `media_tags.py` mora imati TAČNO sledeću strukturu:
  ```python
  """Media pipeline template tags — responsive srcset helper za `<picture>` element.

  Story 2.3 (Epic 2). Konzumiran od:
  - Story 2.6 (Brand Listing) — brand.logo + product.main_image
  - Story 2.7 (Product Detail) — main image, galerija, varijante, testimonijali
  - Story 2.8/2.9 (Tractor/Used Listing) — product.main_image u HTMX partial
  - Epic 3 (Home strana) — featured carousel + brand grid
  - Epic 5 (Blog) — blog_post.cover_image

  sorl-thumbnail lazy generation: thumbnail-ovi se kreiraju on-demand
  pri prvom HTTP GET-u na URL slike, NE post-save signal. KVStore (cached_db)
  čuva mapping {field+geometry → thumbnail_url} za fast cache hit.
  """

  from __future__ import annotations

  from django import template
  from django.db.models.fields.files import ImageFieldFile
  from sorl.thumbnail import get_thumbnail

  register = template.Library()

  # Standardni breakpoint-i (DESIGN.md § Responsive grid):
  # 400w   — mobilni viewport (max 480px)
  # 800w   — tablet / small desktop (481-1024px)
  # 1600w  — large desktop / retina (>1024px)
  RESPONSIVE_WIDTHS: tuple[int, ...] = (400, 800, 1600)


  @register.inclusion_tag("media_pipeline/responsive_picture.html")
  def responsive_picture(
      image: ImageFieldFile | None,
      alt: str = "",
      sizes: str = "(max-width: 768px) 100vw, 50vw",
      loading: str = "lazy",
      css_class: str = "",
      crop: str = "center",
      format: str = "JPEG",
  ) -> dict:
      """Render `<picture>` element sa srcset varijantama 400w/800w/1600w.

      Args:
          image: ImageFieldFile (npr. product.main_image); None → prazan render
          alt: alt tekst (OBAVEZAN za accessibility; prazna string za dekoraciju)
          sizes: HTML sizes atribut za browser viewport hint
          loading: "lazy" (default) ili "eager" za above-the-fold slike
          css_class: dodatne CSS klase na `<img>` tag (npr. "coric-product-card__image")
          crop: sorl-thumbnail crop strategy ("center", "top", "bottom", "noop")
          format: output format ("JPEG" default — gubi PNG transparency;
                  caller MORA preneti "PNG" za Brand.logo i sve slike sa transparency
                  koje moraju ostati transparentne). Vidi Decision MP-D5.

      Usage u template-u:
          {% load media_tags %}
          {% responsive_picture product.main_image alt=product.name sizes="(max-width: 768px) 100vw, 25vw" %}
          {% responsive_picture brand.logo alt=brand.name format='PNG' %}
      """
      if not image or not getattr(image, "name", ""):
          return {"image": None, "alt": alt, "css_class": css_class}

      from django.conf import settings as _settings
      quality = getattr(_settings, "THUMBNAIL_QUALITY", 85)

      variants = []
      for width in RESPONSIVE_WIDTHS:
          thumb = get_thumbnail(image, f"{width}", crop=crop, quality=quality, format=format)
          variants.append({"url": thumb.url, "width": width})

      # Largest variant kao `<img src>` fallback (za browsers koji ne podržavaju srcset)
      fallback = variants[-1]
      srcset_str = ", ".join(f"{v['url']} {v['width']}w" for v in variants)

      return {
          "image": image,
          "alt": alt,
          "sizes": sizes,
          "loading": loading,
          "css_class": css_class,
          "fallback_url": fallback["url"],
          "srcset": srcset_str,
          "width": fallback["width"],
      }
  ```
- **And** template `templates/media_pipeline/responsive_picture.html` mora postojati sa sledećim sadržajem:
  ```html
  {% comment %}
  Story 2.3 — responsive `<picture>` element za sve ImageField-ove.
  Renderuje se kroz {% responsive_picture <field> alt=... sizes=... %} tag.
  Lazy loading podrazumevan; above-the-fold caller prosleđuje loading="eager".
  {% endcomment %}
  {% if image %}
  <picture>
    <img
      src="{{ fallback_url }}"
      srcset="{{ srcset }}"
      sizes="{{ sizes }}"
      alt="{{ alt }}"
      loading="{{ loading }}"
      width="{{ width }}"
      {% if css_class %}class="{{ css_class }}"{% endif %}
    >
  </picture>
  {% endif %}
  ```
- **And** template-i `responsive_picture.html` se nalaze u `templates/media_pipeline/responsive_picture.html` (NIJE u `apps/media_pipeline/templates/...` jer Django template discovery preferira root `templates/` direktorijum per project-context.md § File organization).
- **And** template tag MORA biti `inclusion_tag` (NE `simple_tag`) jer renderuje strukturirani HTML kroz template fajl — simple_tag bi zahtevao return Markup string što je manje održivo.
- **And** template tag MORA gracefully handle-ovati `None` ili prazan `ImageFieldFile` — caller ne mora wrap-ovati `{% if product.main_image %}` oko taga (defensive na boundary, vidi Dev Notes § Boundary defensive validation rationale).

**AC5 — Upload non-image fajla (npr. PDF) u Product.main_image blokira save sa locale-aware ValidationError porukom kroz `validate_image_mime()`**

- **Given** Product modeli iz Story 2.2 + `validate_image_mime()` helper iz AC3
- **When** TEA (Step 3) piše test koji upload-uje SimpleUploadedFile sa PDF magic bytes (`b"%PDF-1.4\n..."`) ali fake `.jpg` extension u `Product.main_image` polje i poziva `validate_image_mime()` direktno
- **Then** `validate_image_mime()` mora raise-ovati `ValidationError` sa porukom `_("Nedozvoljen tip slike: %(mime)s. Dozvoljeni tipovi: %(allowed)s.")` (detect-uje `application/pdf` MIME)
- **And** **JPEG sa exe bytes (zlonameran upload)** — header `b"MZ\x90\x00..."` ali fake `.jpg` extension → python-magic detect-uje `application/x-dosexec` ili sličan → ValidationError
- **And** **validan JPEG header** (`b"\xff\xd8\xff\xe0..."`) ali corrupt body (truncated bytes) → python-magic detect-uje `image/jpeg` PASS prvi check, ali `Image.open(upload).verify()` raise-uje `UnidentifiedImageError`/`OSError` → ValidationError sa porukom `_("Slika je oštećena ili nije validan format.")`
- **And** **validan PNG** sa `b"\x89PNG\r\n\x1a\n..."` header — PASS oba check-a, no ValidationError raised, helper vraća `None` (success)
- **And** **validan WebP** sa `b"RIFF....WEBP..."` header — PASS oba check-a, no ValidationError raised
- **And** **prazan upload** (`upload.size == 0`) → ValidationError `_("Slika je prazna ili nije priložena.")`
- **And** **None upload** (`upload is None`) → ValidationError `_("Slika je prazna ili nije priložena.")` (no AttributeError raised)
- **And** **Over-size upload** (`upload.size > MAX_UPLOAD_SIZE_BYTES` = 10MB) → ValidationError `_("Slika je veća od %(limit)d MB. Maksimalna dozvoljena veličina je %(limit)d MB.")` (DoS guard)
- **And** AC5 **NE traži** da Dev modifikuje `Product.main_image` polje da pozove `validate_image_mime()` direktno u `clean()` — Story 2.3 utility helper postoji za FUTURE consumption kroz Story 8.4/8.6 admin forme; Story 2.3 NE menja `apps/products/models.py` niti `apps/brands/models.py` (ostaju identični kao posle 2.2). Test pokriva HELPER ponašanje, NE Product.main_image runtime validacije (to je 8.x scope).

**AC6 — Thumbnail-ovi se generišu lazy on-demand u `media/thumbnails/` (sorl-thumbnail default)**

- **Given** AC2 završen (`THUMBNAIL_PREFIX = "thumbnails/"` per Decision MP-D7, `MEDIA_ROOT = BASE_DIR / "media"`)
- **When** TEA (Step 3) piše integration test koji renderuje template sa `{% responsive_picture sample_image alt="Test" %}` na sample product sa real ImageField backed by SimpleUploadedFile sa validan JPEG header
- **Then** posle render-a, sledeće MORA biti istinito:
  - `media/thumbnails/` direktorijum mora biti kreiran (ako ne postoji, sorl-thumbnail ga kreira)
  - `media/thumbnails/` mora sadržati 3 nove fajlove (400×*, 800×*, 1600×* varijante — sorl-thumbnail filename pattern je hash-based, npr. `<hash>.jpg`)
  - sorl-thumbnail KVStore tabela (`thumbnail_kvstore`) mora imati 3 nova entry-ja koji mapiraju `(image_path, width)` → `thumbnail_path`
  - Drugi render istog `{% responsive_picture %}` poziva **NE kreira nove fajlove** (cache hit kroz KVStore — fast path)
- **And** thumbnail file format je JPEG (per `THUMBNAIL_FORMAT = "JPEG"` setting) bez obzira na source format (PNG/WebP source → JPEG output, ako caller ne prosledi `format='PNG'`) — testirati sa PNG sample-om i verifikovati output je `.jpg`
- **And** thumbnail size assertion MORA biti izvršena nad **realističnim source image-om** (≥ 2000px wide). Test fixture `realistic_source_image_bytes` MUST biti generated kroz `PIL.Image.new("RGB", (2400, 1800), color=(120, 80, 200)).save(buf, format="JPEG", quality=95)` u conftest-u — 62-byte minimal JPEG je NE-validan source jer je manji od svih target widths (400/800/1600) pa nema smisla.
- **And** Given source image ≥ 2000px wide, generated 400w/800w/1600w thumbnails MUST biti smaller than source u file-size (heuristika, ne strict bound; verifikacija kroz `os.path.getsize(thumb_path) < os.path.getsize(source_path)`).

**AC7 — `python manage.py migrate` aplicira sorl-thumbnail KVStore migraciju bez grešaka**

- **Given** AC1 završen (`"sorl.thumbnail"` u `INSTALLED_APPS`)
- **When** pokrenem `uv run python manage.py migrate` posle registracije
- **Then** sorl-thumbnail ugrađene migracije moraju biti aplicirane:
  - `thumbnail.0001_initial` (KVStore model — `KVStore(key, value)` tabela)
- **And** `uv run python manage.py showmigrations thumbnail` mora prikazati `[X] 0001_initial`
- **And** `uv run python manage.py migrate --plan` mora pokazati SAMO `thumbnail 0001_initial` (sorl-thumbnail migracija) — NIKAKVA migracija na `apps.media_pipeline` (jer media_pipeline NEMA modela u 2.3)
- **And** AC7 NE traži da Dev kreira `apps/media_pipeline/migrations/0001_initial.py` — Story 2.3 NEMA modela u media_pipeline app-u (utility-only), pa `makemigrations media_pipeline` ne treba pokrenuti i NE generiše ništa.

**AC8 — Postojeći testovi (Story 1.x + 2.1 + 2.2) ostaju zeleni; novi 2.3 testovi prolaze**

- **Given** Sve prethodne testove pišu se OČEKUJU green pre Story 2.3
- **When** `uv run pytest` pokrenut posle Story 2.3 implementacije
- **Then** sve postojeće testove (`apps/brands/tests/`, `apps/products/tests/`, `apps/core/tests/`, `tests/integration/test_app_boundaries.py` iz 2.2) MORAJU biti green
- **And** novi `apps/media_pipeline/tests/` testovi (TEA Step 3 deliverable) MORAJU biti green:
  - `test_validate_image_mime_*` (11 scenarija per AC5 — uključujući oversize DoS guard, seek-back side-effect, i None size streaming edge case)
  - `test_responsive_picture_tag_*` (render output, srcset structure, None/empty image handling, format='PNG' transparency preservation)
  - `test_thumbnail_generation_*` (file creation u media/thumbnails/, KVStore entry, cache hit drugi render)
  - `test_media_pipeline_config_name` (smoke za MediaPipelineConfig.name — mirror 2.1 BR-1 pattern; IMP-13 stronger assertion kroz `apps.get_app_config()`)
- **And** **app boundary regression test** (mirror 2.2 AC12 — extends `tests/integration/test_app_boundaries.py`, **reuse `_assert_no_import` helper iz postojećeg fajla**):
  - `test_media_pipeline_does_not_import_products` — `apps/media_pipeline/**/*.py` NE sme `from apps.products import ...`
  - `test_media_pipeline_does_not_import_brands` — `apps/media_pipeline/**/*.py` NE sme `from apps.brands import ...`
  - Razlog: utility app je generic — domain app-ovi konzumiraju utility kroz template tag-ove ili helper-e, ne obratno (per architecture.md § App dependency graph: `media_pipeline ← utility, importovan od products + brands + blog`)

**AC9 — Code quality + format pass (DoD)**

- **Given** Implementacija završena
- **When** Mihas pokrene quality gate komande
- **Then** sve komande MORAJU exit code 0:
  - `uv run ruff check .` (linter)
  - `uv run ruff format --check .` (formatter)
  - `uv run djade --check templates/` (Django template formatter — uključujući novi `templates/media_pipeline/responsive_picture.html`)
- **And** **NEMA hardcoded UI string-ova bez `gettext`** u `apps/media_pipeline/utils.py` (sve ValidationError poruke prolaze kroz `_()`)
- **And** **NEMA `print()` poziva** u utility kodu (debug print je anti-pattern; logger se ne uvodi u 2.3 — utility je tih)

**AC10 — `{% responsive_picture %}` `format` kwarg preserve-uje PNG transparency**

- **Given** AC4 završen (tag potpisom prima `format` kwarg sa default "JPEG")
- **When** caller pozove `{% responsive_picture brand.logo alt=brand.name format='PNG' %}` sa Brand.logo poljem koje sadrži PNG sa transparency (alpha channel)
- **Then** generated thumbnail-ovi MORAJU biti PNG format (extension `.png`, mimetype `image/png`)
- **And** alpha channel (transparency) MORA biti preserved u output thumbnail-u (Pillow `Image.open(thumb_path).mode` MORA biti "RGBA" ili "LA")
- **And** kad caller ne prosledi `format` kwarg (default "JPEG"), thumbnail-ovi su JPEG (extension `.jpg`) bez obzira na source format (PNG/WebP source → JPEG output sa solid background loss-om transparency)
- **And** `format` kwarg se prosleđuje `sorl.thumbnail.get_thumbnail(image, geometry, format=format, ...)` direktno — sorl-thumbnail kontroliše output extension i format
- **And** Story 2.6 (Brand Listing) MUST koristiti `{% responsive_picture brand.logo alt=brand.name format='PNG' %}` da brand logo zadrži transparent background (out-of-scope ovde, dokumentuje contract)

## Zadaci

### Task 1 — Kreiranje `apps/media_pipeline/` Django utility app i registracija u INSTALLED_APPS (AC1)

- [x] 1.1: Kreirati direktorijum `apps/media_pipeline/` kroz Django startapp komandu:
  ```powershell
  New-Item -ItemType Directory -Force apps/media_pipeline
  uv run python manage.py startapp media_pipeline apps/media_pipeline
  ```
- [x] 1.2: Obrisati `apps/media_pipeline/tests.py` (mirror 2.1/2.2 disciplina) i kreirati `apps/media_pipeline/tests/` direktorijum **BEZ `__init__.py`** (TEA REVIEW FIX MP-R1):
  ```powershell
  Remove-Item apps/media_pipeline/tests.py -ErrorAction SilentlyContinue
  New-Item -ItemType Directory -Force apps/media_pipeline/tests
  ```
  - **KRITIČNO — Razlika u odnosu na 2.1/2.2:** `apps/media_pipeline/tests/` **NE SME imati `__init__.py`** jer
    u njemu postoji `conftest.py`. `pyproject.toml` ima `addopts = "--import-mode=importlib"`. Kombinacija
    `tests/__init__.py` (root `tests/` package) + `apps/media_pipeline/tests/__init__.py` (drugi `tests` package)
    + oba `conftest.py` izaziva `pytest` plugin registration konflikt:
    `ValueError: Plugin already registered under a different name: tests/conftest.py = apps/media_pipeline/tests/conftest.py`.
    Test collection FAIL-uje na bilo kojem kombinovanom run-u (`uv run pytest`).
  - **Tradeoff:** `apps/brands/tests/` i `apps/products/tests/` ostavljaju `__init__.py` jer NEMAJU `conftest.py`
    (no collision). Story 2.3 je prva story koja uvodi per-app `conftest.py` — `__init__.py` se mora izostaviti.
  - **Verifikacija:** `uv run pytest --collect-only -q` mora vratiti sve testove bez ValueError-a.
- [x] 1.2b: Obrisati `apps/media_pipeline/views.py` i `apps/media_pipeline/admin.py` (utility app NEMA views ni admin — mirror 2.2 IMP-iter4-3 discipline za sprečavanje "placeholder fill"):
  ```powershell
  Remove-Item apps/media_pipeline/views.py -ErrorAction SilentlyContinue
  Remove-Item apps/media_pipeline/admin.py -ErrorAction SilentlyContinue
  ```
- [x] 1.2c: `apps/media_pipeline/models.py` ostaje prazan (ne briše se — neki Django auto-discovery hooks proveravaju njegovo postojanje). Sadržaj nakon Task 1.2c MORA biti tačno:
  ```python
  """Media pipeline app — utility-only, no models."""
  ```
- [x] 1.3: Editovati `apps/media_pipeline/apps.py`:
  ```python
  """AppConfig za apps.media_pipeline — image + PDF utility (cross-cutting).

  Story 2.3 (Epic 2) — utility app bez modela. Konzumiran od domain app-ova
  (brands, products, blog) kroz template tagove i helper-e.
  Jednosmerna zavisnost: media_pipeline NE SME uvoziti apps.products / apps.brands.

  Story 2.4 proširuje ovaj app sa post_save signal handler-om za ProductBrochure
  (`signals.py`) i registracijom kroz `ready()` hook — Story 2.3 NEMA ready() hook.
  """
  from django.apps import AppConfig
  from django.utils.translation import gettext_lazy as _


  class MediaPipelineConfig(AppConfig):
      default_auto_field = "django.db.models.BigAutoField"
      name = "apps.media_pipeline"
      verbose_name = _("Media pipeline")
  ```
  - **KRITIČNO:** `name = "apps.media_pipeline"` (sa `apps.` prefiksom — mirror BR-1/PR-1 gotcha; matches `INSTALLED_APPS` entry).
- [x] 1.4: Modifikovati `config/settings/base.py` `INSTALLED_APPS` — **APENDOVATI DVA nova entry-ja** (NE rewrite cele liste). Koristiti targeted Edit:
  - **DO:** Edit operacija koja pronalazi `"apps.products",                # NOVO Story 2.2 — Product i related modeli (POSLE brands per dep rule)` liniju i dodaje sledeće dve linije ispod nje:
    ```python
        "sorl.thumbnail",  # NOVO Story 2.3 — third-party paket POSLE domain app-ova (utility lib)
        "apps.media_pipeline",  # NOVO Story 2.3 — utility app POSLE sorl.thumbnail (koristi njegove template tags)
    ```
  - **DON'T:** Full INSTALLED_APPS block replace — to bi striplo live komentare iz 1.6/2.1/2.2.
  - **Verifikacija pre Edit-a:** `Select-String -Path config/settings/base.py -Pattern '"apps.products"'` mora vratiti tačno jednu liniju.
- [x] 1.5: Smoke verifikacija: `uv run python manage.py check` — exit code 0; nikakav warning o INSTALLED_APPS ordering-u ili circular import-u.
- [x] 1.6: **Modifikovati `justfile` `test` recept da koristi Docker (per Decision MP-D6)** — libmagic SEGFAULT na Windows host-u onemogućava direktan `uv run pytest`. Edit operacija u `justfile` (linije 38-40):
  - **Pronaći** liniju:
    ```
    # Pokrece test suite
    test:
        uv run pytest
    ```
  - **Zameniti sa:**
    ```
    # Pokrece test suite (kroz Docker — libmagic + poppler-utils system deps NISU dostupni na Windows host-u)
    # Per Story 2.3 Decision MP-D6: konzistentan dev UX, izbegava libmagic SEGFAULT na Windows.
    # Primer sa argumentima: just test apps/media_pipeline/tests/
    test *ARGS:
        docker compose -f compose/local.yml run --rm django uv run pytest {{ARGS}}
    ```
  - **`*ARGS` je obavezno** — bez njega `just test apps/media_pipeline/tests/` failuje sa "got unexpected argument". `{{ARGS}}` prosleđuje sve trailing argumente direktno pytest-u (uključujući pytest flagove tipa `-x`, `-k pattern`, itd).
  - **Verifikacija posle Edit-a:** `Get-Content justfile | Select-String "docker compose.*pytest"` mora vratiti tačno jednu liniju (confirmation da je change applied).
  - **Dependency:** Docker Desktop mora biti pokrenut i `docker compose -f compose/local.yml build` urađen barem jednom (`--rm` flag uklanja kontejner posle run-a, ali image MORA postojati). Mihas može pokrenuti `just dev-build` ako treba refresh image-a.
- [x] 1.7: **Generisati/update-ovati locale catalog** za `MediaPipelineConfig.verbose_name = _("Media pipeline")` admin label (mirror Story 2.1 IMP-11 pattern). Pokrenuti:
  ```powershell
  just messages
  ```
  - **Šta radi:** mapira na `uv run python manage.py makemessages -a && uv run python manage.py compilemessages` — extract-uje sve `gettext_lazy` poruke iz `apps/media_pipeline/apps.py` (i `utils.py`) u `apps/media_pipeline/locale/sr/LC_MESSAGES/django.po` i `apps/media_pipeline/locale/en/LC_MESSAGES/django.po`, kompajluje `.mo` binarne kataloge.
  - **Napomena:** `just messages` recept NE koristi Docker — `makemessages` ne import-uje libmagic-bound module-e, pa Windows host radi bez problema. Ako Mihas hoće radi konzistentnosti, može pokrenuti `docker compose -f compose/local.yml run --rm django uv run python manage.py makemessages -a` ručno.
  - **Verifikacija:** `Get-ChildItem apps/media_pipeline/locale -Recurse -Filter "*.po"` mora vratiti barem dva fajla (sr + en po Story 1.6 LANGUAGES setting).

### Task 2 — Konfiguracija sorl-thumbnail settings + MEDIA_URL u `config/settings/base.py` (AC2)

- [x] 2.1: Verifikovati da `MEDIA_URL` i `MEDIA_ROOT` POSTOJE u `config/settings/base.py`. **Napomena:** Ova settings su trebala biti uvedena u Story 1.2 (Multi-environment settings split) ili Story 1.3 (Docker compose + Dockerfile sa media volume mount). Ako nisu (mogući previd u prethodnim story-ima), Task 2.2 kreira blok. Komanda:
  ```powershell
  Select-String -Path config/settings/base.py -Pattern '^MEDIA_'
  ```
  - **`-Path config/settings/base.py`** — TAČNO ovaj path. **NE skeniraj ceo `config/settings/` direktorijum** — `development.py` i `production.py` mogu imati MEDIA_* override-e (npr. `MEDIA_ROOT = "/srv/coric/media"` za production Nginx serve) koji NISU relevantni za base.py check. Conditional logika Task 2.2 mora biti bazirana SAMO na sadržaju base.py.
  - Ako vraća 2+ linije (`MEDIA_URL`, `MEDIA_ROOT`) → preskoči Task 2.2 (već postoje iz Story 1.2 / 1.3).
  - Ako vraća 0 linija → izvrši Task 2.2 (kreiraj blok; možda previd u Story 1.2).
- [x] 2.2: **(Conditional — ako MEDIA_* ne postoje)** Dodati `Media` blok u `config/settings/base.py` POSLE `STATIC_ROOT` definicije i PRE `STORAGES` blok. Edit operacija — pronaći `STATIC_ROOT = BASE_DIR / "staticfiles"` liniju, dodati ispod:
  ```python

  # ── Media ────────────────────────────────────────────────────────────────────
  # MEDIA_URL ima leading slash radi i18n_patterns kompatibilnosti (matches STATIC_URL).
  # MEDIA_ROOT je BASE_DIR/media (development); production override može menjati za
  # Nginx serving direktno iz disk-a.
  MEDIA_URL = "/media/"
  MEDIA_ROOT = BASE_DIR / "media"
  ```
- [x] 2.3: Dodati `sorl-thumbnail` settings blok POSLE `STORAGES` blok i PRE `BOOTSTRAP5` blok (verifikuj redosled u live fajlu pre Edit-a):
  ```python

  # ── sorl-thumbnail (Story 2.3) ───────────────────────────────────────────────
  # Image pipeline za responsive srcset (400w/800w/1600w varijante) na svim
  # Product/Brand/ProductImage/ProductVariant/ProductTestimonial image poljima.
  # Lazy generation: thumbnail-ovi se kreiraju on-demand pri prvom HTTP GET-u
  # na URL slike, NE post-save signal. KVStore cache-uje (image_path, geometry)
  # → thumbnail URL mapping za fast hit drugi render.
  # Vidi project-context.md § Media pipeline + architecture.md § Image processing.
  THUMBNAIL_BACKEND = "sorl.thumbnail.base.ThumbnailBackend"
  THUMBNAIL_KVSTORE = "sorl.thumbnail.kvstores.cached_db_kvstore.KVStore"
  THUMBNAIL_FORMAT = "JPEG"
  THUMBNAIL_QUALITY = 85
  THUMBNAIL_PRESERVE_FORMAT = False  # per-call override via `format='PNG'` u {% responsive_picture %} tag (Decision MP-D5)
  # FIX-7 / Decision MP-D7: kanonski sorl-thumbnail setting je THUMBNAIL_PREFIX
  # (sa trailing slash), NE THUMBNAIL_DIRNAME (koji NE postoji u sorl source-u —
  # silent no-op assignment u prethodnoj verziji story spec-a).
  THUMBNAIL_PREFIX = "thumbnails/"
  THUMBNAIL_DEBUG = False  # FIX-3 / Security HIGH-2 — hardcoded False
  ```
- [x] 2.4: Editovati `config/urls.py` da servira `MEDIA_URL` u development-u:
  ```powershell
  Select-String -Path config/urls.py -Pattern 'static\(settings.MEDIA_URL'
  ```
  - Ako vraća 1+ linija → već postoji, preskoči Task 2.5.
  - Ako vraća 0 linija → izvrši Task 2.5.
- [x] 2.5: **(Conditional — ako static(MEDIA_URL) nije u urls.py)** Dodati na kraj `config/urls.py`:
  ```python
  from django.conf import settings
  from django.conf.urls.static import static

  if settings.DEBUG:
      urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
  ```
- [x] 2.6: Smoke verifikacija: `uv run python manage.py check` — exit code 0.
- [x] 2.7: Kreirati `media/` direktorijum strukturu (prereq za Django FileSystemStorage — bez `media/` direktorijuma admin upload + smoke test raise-uju `FileNotFoundError`):
  ```powershell
  New-Item -ItemType Directory -Force -Path media/products/main, media/products/gallery, media/thumbnails, media/brands/logos, media/brands/heroes
  ```
- [x] 2.8: Verifikovati `.gitignore` sadrži `media/` line (bind mount u `compose/local.yml` mapira host repo `media/` u kontejner — generated thumbnail-ovi MORAJU biti git-ignorisani da ne završe u repo working tree):
  ```powershell
  Select-String -Path .gitignore -Pattern '^media/$'
  ```
  - Ako vraća 0 linija → dodaj `media/` na kraj `.gitignore` fajla kroz Edit tool.
  - Ako vraća 1+ linija → preskoči (već postoji).

### Task 3 — Kreiranje `apps/media_pipeline/utils.py` sa `validate_image_mime()` (AC3, AC5)

- [x] 3.1: Kreirati `apps/media_pipeline/utils.py` sa kompletnim sadržajem definisanim u AC3.
- [x] 3.2: Verifikovati da Pillow je već dostupan kao tranzitivna zavisnost sorl-thumbnail-a:
  ```powershell
  uv run python -c "import PIL; print(PIL.__version__)"
  ```
  - Ako exit != 0 → `uv add pillow` (sorl-thumbnail >=13 obično ne pinpoint-uje Pillow eksplicitno; verifikuj).
- [x] 3.3: Verifikovati da `python-magic` import radi:
  ```powershell
  uv run python -c "import magic; print(magic.from_buffer(b'\xff\xd8\xff', mime=True))"
  ```
  - Očekivani output: `image/jpeg` (libmagic1 detect-uje JPEG SOI marker).
  - **Windows local dev gotcha:** na Windows-u libmagic nije sistemski paket; alternativa je `python-magic-bin` (Windows-only dep). Vidi Dev Notes § Local dev na Windows-u bez libmagic za workaround opciju. Test pokriva ovaj scenario gracefully (skip test ako import fail).
- [x] 3.4: Verifikovati `ruff check apps/media_pipeline/utils.py` exit 0.

### Task 4 — Kreiranje `apps/media_pipeline/templatetags/` + `media_tags.py` (AC4)

- [x] 4.1: Kreirati `apps/media_pipeline/templatetags/__init__.py` (prazan paket marker):
  ```powershell
  New-Item -ItemType Directory -Force apps/media_pipeline/templatetags
  New-Item -ItemType File apps/media_pipeline/templatetags/__init__.py
  ```
- [x] 4.2: Kreirati `apps/media_pipeline/templatetags/media_tags.py` sa kompletnim sadržajem definisanim u AC4.
- [x] 4.3: Kreirati template direktorijum `templates/media_pipeline/`:
  ```powershell
  New-Item -ItemType Directory -Force templates/media_pipeline
  ```
- [x] 4.4: Kreirati `templates/media_pipeline/responsive_picture.html` sa kompletnim sadržajem definisanim u AC4.
- [x] 4.5: Smoke verifikacija template tag discovery:
  ```powershell
  uv run python manage.py shell -c "from django.template import engines; t = engines['django'].from_string('{% load media_tags %}OK'); print(t.render({}))"
  ```
  - Očekivani output: `OK` (no `TemplateSyntaxError`).
- [x] 4.6: Verifikovati `ruff check apps/media_pipeline/templatetags/` exit 0 + `djade --check templates/media_pipeline/responsive_picture.html` exit 0.

### Task 5 — Migracija sorl-thumbnail KVStore tabele (AC7)

- [x] 5.1: Pokrenuti makemigrations dry-run da potvrdi NEMA migracija na `apps.media_pipeline`:
  ```powershell
  uv run python manage.py makemigrations --dry-run media_pipeline
  ```
  - Očekivani output: `No changes detected in app 'media_pipeline'` (jer NEMA modela).
- [x] 5.2: Pokrenuti migrate sa --plan da verifikuje sorl-thumbnail migration je u redu:
  ```powershell
  uv run python manage.py migrate --plan
  ```
  - Očekivani output sadrži: `thumbnail.0001_initial ... (Pending)` ili (Already applied) ako je apliciran ranije.
- [x] 5.3: Aplicirati migraciju:
  ```powershell
  uv run python manage.py migrate
  ```
  - **Windows dev:** `docker compose -f compose/local.yml run --rm django uv run python manage.py migrate` (migrate ne import-uje libmagic ali konektuje na PostgreSQL kontejner kroz `DATABASES['default']['HOST'] = 'postgres'` koji je dostupan SAMO unutar docker network-a; host-side `uv run` failuje na `psycopg2.OperationalError: connection refused`).
  - Exit code 0; `thumbnail.0001_initial` applied; NEMA spurious migracije na `apps.products`, `apps.brands`, `apps.core` (regression guard).
- [x] 5.4: Verifikacija KVStore tabele:
  ```powershell
  uv run python manage.py shell -c "from sorl.thumbnail.models import KVStore; print(KVStore.objects.count())"
  ```
  - Očekivani output: `0` (prazan KVStore — još nijedan thumbnail nije generisan).

### Task 6 — TEA piše testove (RED phase) — Dev NIKAD ne piše testove (AC5, AC6, AC8)

- [x] 6.1: TEA kreira `apps/media_pipeline/tests/test_utils.py` sa **11 test scenarija** za `validate_image_mime()`:
  - `test_validate_image_mime_accepts_valid_jpeg` (header `b"\xff\xd8\xff\xe0\x00\x10JFIF..."`)
  - `test_validate_image_mime_accepts_valid_png` (Pillow-generated PNG iz `sample_png_bytes` fixture)
  - `test_validate_image_mime_accepts_valid_webp` (Pillow-generated WebP iz `sample_webp_bytes` fixture — NE hardcoded `b"RIFF...WEBP"` stub jer Image.verify() raise-uje UnidentifiedImageError)
  - `test_validate_image_mime_rejects_pdf_as_image` (header `b"%PDF-1.4\n..."` sa `.jpg` extension)
  - `test_validate_image_mime_rejects_exe_as_image` (header `b"MZ\x90\x00..."`)
  - `test_validate_image_mime_rejects_corrupt_jpeg` (`corrupt_jpeg_bytes` fixture — validan JPEG SOI header ali truncated body bez EOI markera)
  - `test_validate_image_mime_rejects_empty_upload` (size=0)
  - `test_validate_image_mime_rejects_none_upload`
  - `test_validate_image_mime_rejects_oversize_upload` (size > 10MB → ValidationError sa MB-aware porukom; IMP-3 DoS guard)
  - `test_validate_image_mime_seeks_back_to_zero_after_validation` (side-effect verifikacija)
  - `test_validate_image_mime_handles_none_size_gracefully` (IMP-A2 — UploadedFile sa `.size = None` streaming case → ValidationError, NE AttributeError; verifikuje `not upload.size` truthy check pattern)
- [x] 6.2: TEA kreira `apps/media_pipeline/tests/test_templatetags.py` sa testovima `{% responsive_picture %}` (10 scenarija — uključujući AC10 format kwarg):
  - `test_responsive_picture_renders_picture_element_with_srcset`
  - `test_responsive_picture_renders_three_widths_400_800_1600`
  - `test_responsive_picture_uses_largest_as_fallback_src`
  - `test_responsive_picture_with_none_image_renders_nothing`
  - `test_responsive_picture_with_empty_image_field_renders_nothing`
  - `test_responsive_picture_applies_css_class`
  - `test_responsive_picture_applies_lazy_loading_by_default`
  - `test_responsive_picture_accepts_eager_loading_override`
  - `test_responsive_picture_format_png_preserves_alpha` (AC10 — uses `sample_png_with_alpha_bytes` fixture; thumbnail output je `.png` sa RGBA mode)
  - `test_responsive_picture_format_jpeg_default_loses_alpha` (AC10 — default format='JPEG' konvertuje PNG-RGBA source u JPG sa solid background)
- [x] 6.3: TEA kreira `apps/media_pipeline/tests/test_thumbnails.py` sa integration testovima (mark `@pytest.mark.django_db`). **Koristi fixtures iz conftest.py — `realistic_source_image_bytes` za size-ratio testove (NIJE 62-byte sample_jpeg_bytes — premali da bi bio source) i `sample_png_bytes` za PNG → JPEG konverziju:**
  - `test_thumbnail_generation_creates_files_in_media_thumbnails_dir` (uses `realistic_source_image_bytes`)
  - `test_thumbnail_generation_populates_kvstore`
  - `test_thumbnail_second_render_uses_kvstore_cache_hit` (no nova fajla na disk-u)
  - `test_thumbnail_format_is_jpeg_regardless_of_source` (PNG source → JPG output; uses `sample_png_bytes` fixture)
  - `test_thumbnail_size_smaller_than_source` (AC6 size-ratio assertion na `realistic_source_image_bytes` 2400×1800 source — sve tri varijante MORAJU biti smaller od source-a u file bytes)
- [x] 6.4: TEA kreira `apps/media_pipeline/tests/test_apps.py` smoke za AppConfig.name (mirror 2.1 BR-1 / 2.2 PR-1 regression guard). **MUST koristiti stronger assertion kroz Django app registry**:
  ```python
  from django.apps import apps

  def test_media_pipeline_config_name():
      """Regression guard za AppConfig.name = 'apps.media_pipeline' (mirror BR-1/PR-1).

      Bez `apps.` prefiksa, INSTALLED_APPS resolve fail-uje sa LookupError pri prvom
      model reference-u. apps.get_app_config() je stroža provera nego direkt
      MediaPipelineConfig.name == "..." jer testira da Django app registry resolve-uje
      label kako treba.
      """
      config = apps.get_app_config("media_pipeline")
      assert config.name == "apps.media_pipeline"
  ```
- [x] 6.5: TEA proširuje `tests/integration/test_app_boundaries.py` sa dve nove test funkcije (AC8 enforcement). **MORA reuse-ovati postojeći `_assert_no_import(path, module)` helper iz postojećeg fajla** — NE pisati novu AST walk logiku (helper već postoji iz Story 2.2 AC12):
  - `test_media_pipeline_does_not_import_products` — poziva `_assert_no_import(pathlib.Path("apps/media_pipeline"), "apps.products")`
  - `test_media_pipeline_does_not_import_brands` — poziva `_assert_no_import(pathlib.Path("apps/media_pipeline"), "apps.brands")`
- [x] 6.6: **Posle Task 1.6 (justfile mod per MP-D6), Dev koristi `just test` za sve test komande** (mapira na Docker kontejner gde libmagic radi — vidi Gotcha MP-7). Da bi se pokrenuli samo media_pipeline testovi: `just test apps/media_pipeline/tests/ tests/integration/test_app_boundaries.py` (just prosleđuje argumente recipe-u). Svi RED testovi pisani; trenutno se OČEKUJE green posle Dev implementacije Task 1-5.

### Task 7 — Lint + format pass + regression (DoD)

- [x] 7.1: `uv run ruff check .` — exit code 0.
- [x] 7.2: `uv run ruff format --check .` — exit code 0.
- [x] 7.3: `uv run djade --check templates/` — exit code 0 (uključujući novi `responsive_picture.html`).
- [x] 7.4: **Posle Task 1.6 (justfile mod), Dev koristi `just test`** (mapira na Docker — libmagic dostupan na svim platformama) — sve postojeće Epic 1 + 2.1 + 2.2 testove + svi novi 2.3 testovi prolaze (AC8 regression). Single test suite run je dovoljan; ne dupliraj manual smoke koji već pokriva TEA integration testovi u Task 6. Linux/macOS dev kome je Docker overhead preglomazan može pokrenuti `uv run pytest` direktno (libmagic1 sistemski paket na Linux-u radi).

### Task 8 — Sprint status update + commit (DoD)

- [x] 8.1: Update `_bmad-output/implementation-artifacts/sprint-status.yaml`:
  - `2-3-image-pipeline-sa-sorl-thumbnail-responsive-srcset: backlog` → `ready-for-dev` (već urađeno u SM Step 4 — proveriti)
  - Update `last_updated` komentar na vrhu fajla
  - **NAPOMENA — typo "dev elopment_status" preservation:** linija 47 `dev elopment_status:` typo OSTAJE NEPROMENJEN (legacy orchestrator artifact, mirror 2.1/2.2 IMP-11).
- [x] 8.2: Commit message follows Conventional Commits:
  ```
  feat(media_pipeline): Story 2.3 — sorl-thumbnail config + validate_image_mime + responsive_picture tag

  - apps/media_pipeline utility app (NEMA modela, NEMA migracija — utility-only)
  - sorl.thumbnail registrovan u INSTALLED_APPS sa THUMBNAIL_* settings
  - validate_image_mime() helper sa python-magic + Pillow Image.verify() double-check
  - {% responsive_picture %} template tag sa srcset 400w/800w/1600w + lazy loading
  - MEDIA_URL + MEDIA_ROOT settings + dev-only static() URL handler
  - sorl-thumbnail KVStore migracija aplicirana (thumbnail.0001_initial)
  - Boundary regression: media_pipeline NE uvozi apps.products / apps.brands
  - Out-of-scope: post_save signal (Story 2.4), admin form integration (Story 8.4/8.6)
  ```

## Dev Notes

### Architecture compliance

- **App boundaries (architecture.md § App dependency graph line 732):** `media_pipeline ← (utility, importovan od products + brands + blog)` — utility app sme da bude importovan ali sam NE SME uvoziti domain app-ove. Test enforces ovo kroz `tests/integration/test_app_boundaries.py` (proširenje 2.2 AC12).
- **App dependency order (mirror 2.1 D2 / 2.2 PR-D1):** `INSTALLED_APPS` redosled je:
  1. `modeltranslation` (mora PRE django.contrib.admin)
  2. Django built-ins
  3. Third-party (`django_htmx`, `django_bootstrap5`)
  4. `apps.core` (foundation)
  5. `apps.brands` (Story 2.1)
  6. `apps.products` (Story 2.2 — zavisi od brands)
  7. **`sorl.thumbnail`** (NOVO Story 2.3 — third-party utility, ne zavisi od domain app-ova)
  8. **`apps.media_pipeline`** (NOVO Story 2.3 — utility app koji koristi sorl.thumbnail template tagove)
- **Naming convention:** mirror 2.1/2.2 — `MediaPipelineConfig.name = "apps.media_pipeline"` (sa `apps.` prefiksom — kritično da matches INSTALLED_APPS entry; bez prefiksa Django bi tražio `media_pipeline/` u sys.path root-u i fail-ovao).

### Library/framework requirements

- **`sorl-thumbnail >= 13.0.0`** — već u `pyproject.toml` (Story 1.1); Story 2.3 prvi konzument. Verzija 13 zahteva Django 4.2+ — kompatibilno sa Django 5.2 LTS koja je pinned.
- **`python-magic >= 0.4.27`** — već u `pyproject.toml` (Story 1.1); Story 2.3 prvi konzument. Sistemska zavisnost `libmagic1` (Linux) ili libmagic binary (macOS/Windows) — verifikuj `Dockerfile` ima `RUN apt-get install -y libmagic1` (per Story 1.3, već postoji u `compose/django/Dockerfile` lines 36-43).
- **Pillow (PIL)** — tranzitivna zavisnost sorl-thumbnail-a (≥10.0); `Image.verify()` API koristi se u `validate_image_mime()`. Ne pin-uj eksplicitno u pyproject.toml — sorl-thumbnail će povući kompatibilnu verziju.
- **`pdf2image >= 1.17.0`** — u pyproject.toml ali Story 2.3 NE konzumira (rezervisano za Story 2.4 PDF cover thumbnail).
- **NEMA novih dependency-ja u 2.3** — sve potrebne libs su već u pyproject.toml.

### File structure

```text
apps/media_pipeline/                            # NOVO Story 2.3
├── __init__.py                                 # prazan (startapp generiše)
├── apps.py                                     # startapp + Task 1.3 edit: MediaPipelineConfig(AppConfig)
├── models.py                                   # NEMA modela (placeholder docstring)
├── utils.py                                    # NEW (Task 3): validate_image_mime()
├── templatetags/                               # NEW (Task 4)
│   ├── __init__.py                             # NEW (Task 4.1) — prazan
│   └── media_tags.py                           # NEW (Task 4.2) — {% responsive_picture %}
├── migrations/
│   └── __init__.py                             # startapp generiše; ostaje prazan (NEMA modela)
└── tests/                                      # NEW directory (Task 1.2)
    ├── __init__.py                             # NEW — Dev deliverable, prazan
    ├── test_utils.py                           # NEW (Task 6.1) — TEA RED phase
    ├── test_templatetags.py                    # NEW (Task 6.2) — TEA RED phase
    ├── test_thumbnails.py                      # NEW (Task 6.3) — TEA RED phase
    └── test_apps.py                            # NEW (Task 6.4) — TEA smoke

templates/media_pipeline/                       # NOVO Story 2.3
└── responsive_picture.html                     # NEW (Task 4.4) — `<picture>` template

# Šta startapp generiše a 2.3 BRIŠE:
# - apps/media_pipeline/tests.py    (Task 1.2 — koristi se tests/ dir umesto)
# - apps/media_pipeline/views.py    (Task 1.2b — utility app NEMA views)
# - apps/media_pipeline/admin.py    (Task 1.2b — utility app NEMA admin)

# Šta startapp NE generiše (i 2.3 ne kreira):
# - apps/media_pipeline/urls.py     (utility app NEMA URL routes)
# - apps/media_pipeline/forms.py    (utility app NEMA forme)
# - apps/media_pipeline/managers.py
# - apps/media_pipeline/signals.py  (Story 2.4 prvi put kreira za ProductBrochure post_save)
```

### sorl-thumbnail config rationale

- **`THUMBNAIL_BACKEND = "sorl.thumbnail.base.ThumbnailBackend"`** — default backend; ne menjaj osim ako Mihas eksplicitno hoće custom backend (out-of-scope za v1).
- **`THUMBNAIL_KVSTORE = "sorl.thumbnail.kvstores.cached_db_kvstore.KVStore"`** — DB-backed + local memory cache wrapper; trade-off ka DB (persistent across server restart) + memory cache za fast hit. Alternativa `redis_kvstore` je premature za v1 (per project-context.md § Critical version constraints: "Bez Celery / Redis u v1").
- **`THUMBNAIL_FORMAT = "JPEG"`** — sve thumbnail-ove konvertuje u JPEG, gubi transparency (PNG source → solid bg JPEG). Editor mora znati: ako traje transparency (npr. brand logo na transparent bg-u), `THUMBNAIL_PRESERVE_FORMAT = True` može biti override per-template-call (`{% thumbnail image "200" format="PNG" preserve_format=True %}`). Story 2.3 default je JPEG za bandwidth optimizaciju; Story 2.6 može override-ovati per brand logo.
- **`THUMBNAIL_QUALITY = 85`** — sorl default je 95 koji je prevelik za web (uglavnom 100KB+ za 800w sliku); 85 je common-knowledge "sweet spot" za web (~30-50KB za 800w). Mihas može tunirati ako Lighthouse performance audit u Story 9.10 pokaže LCP issues.
- **`THUMBNAIL_DEBUG = False`** — u prod False; u development.py opciono `True` ako Mihas debug-uje (sorl-thumbnail raise-uje glasne errore umesto silent fail). NIJE kritično u 2.3.

### `validate_image_mime()` semantika

- **Double-check rationale (project-context.md § File upload polja):** Django ImageField validira SAMO file extension (`.jpg`, `.png`) — attacker može upload-ovati `malware.exe` preimenovan u `image.jpg` i Django neće da prepozna. python-magic detect-uje real MIME iz file signature (magic bytes); Pillow `Image.verify()` dodatno verifies image structure integrity (sprečava deliberate corrupt images koji bi crash-ovali srcset render).
- **Side-effect `upload.seek(0)`:** helper resetuje stream poziciju nakon read-a; caller form ne mora explicit seek-ovati u `clean_<field>()` posle helper poziva.
- **Empty guard truthy check (`not upload.size`):** koristi se truthy check umesto `upload.size == 0` zato što neki `UploadedFile` subclass-ovi (npr. `TemporaryUploadedFile` tokom streaming-a velikog upload-a) mogu vratiti `None` za `.size` dok upload nije završen. `upload.size == 0` PROPUŠTA `None` case → kasnije `upload.size > max_size_bytes` raise-uje `TypeError: '>' not supported between instances of 'NoneType' and 'int'`. `not upload.size` hvata oba (0 i None) deterministički.
- **`gettext_lazy as _`:** error poruke moraju biti lazy jer modul-level evaluacija dolazi pre Django app loading-a — eager `gettext()` bi crash-ovao na import.
- **No logging:** helper je tih — ne loguje warning/error, samo raise-uje ValidationError. Caller form decides kako da reaguje (GlitchTip capture exception kroz Django middleware automatski hvata unhandled iz `clean_<field>()`).
- **Future extension (out-of-scope za 2.3):** PDF MIME validation za `Brand.catalog_pdf` i `ProductBrochure.pdf_file` polja je Story 2.4 scope — proširuje `validate_image_mime()` paralelno sa `validate_pdf_mime()` helper-om koji koristi `application/pdf` MIME check + PyMuPDF (ili samo pdf2image) signature check. Story 2.3 NE uvodi `validate_pdf_mime()`.

### `{% responsive_picture %}` template tag semantika

- **`inclusion_tag` vs `simple_tag`:** inclusion_tag renderuje structurirani HTML kroz template fajl (`templates/media_pipeline/responsive_picture.html`) što je održivije i lakše za style-ovanje. simple_tag bi vraćao Markup string što je teško testirati i prilagoditi.
- **`get_thumbnail(image, "400", crop="center", quality=..., format=...)`:** sorl-thumbnail API; `"400"` je geometry string (width only, height auto-scaled za aspect ratio). Crop strategy `"center"` daje konzistentno centrirane crop-ove za product cards. **Quality NIJE hardcoded u tag-u** — tag čita `settings.THUMBNAIL_QUALITY` kroz `getattr(settings, "THUMBNAIL_QUALITY", 85)` da Mihas može tunirati globalno kroz settings (IMP-4 fix). Format kwarg defaults to "JPEG" (per Decision MP-D5), caller može override-ovati na "PNG" za transparency-em.
- **Lazy generation:** sorl-thumbnail kreira thumbnail SAMO pri prvom HTTP GET-u na URL slike; do tada KVStore čuva URL placeholder. To znači da admin upload Product.main_image ne kreira odmah thumbnail-ove — prvi request na `/sr/proizvod/<slug>/` triggers generation. To je željen behavior (no upfront cost; deploy ne čeka thumbnail batch processing).
- **`sizes` atribut:** kritičan za browser da bira odgovarajuću varijantu pre layout-a; default `"(max-width: 768px) 100vw, 50vw"` znači "do 768px viewport-a slika zauzima full širinu; iznad 768px slika zauzima polovinu viewport-a" — caller MORA override-ovati za product card u 4-kolonskom grid-u (`sizes="(max-width: 768px) 100vw, 25vw"`).
- **Srcset breakpoint trade-off (1600w retina-only u default sizes):** Sa default `sizes="(max-width: 768px) 100vw, 50vw"` na desktop viewport-u (≥1200px po DESIGN.md), browser bira varijantu sa najmanjom širinom koja popunjava slot. Slot = `50vw × 1200px = 600px` → browser bira 800w (najbliži, malo veći). **1600w varijanta će biti served SAMO na retina (DPR=2) screens** ili kad caller eksplicitno prosledi `sizes='100vw'` za large hero kontekste. Ovo je **očekivano ponašanje**, ne bug.
- **Sizes override patterns za large-hero kontekste:**
  - Hero slika (above-the-fold, full viewport): `{% responsive_picture image alt='...' sizes='100vw' loading='eager' %}` — browser bira 1600w na desktop, 800w na tablet, 400w na mobile.
  - Product card u 2-kolonskom grid (tablet): `{% responsive_picture image alt='...' sizes='(max-width: 768px) 100vw, 50vw' %}` — default; bira 800w na desktop, 400w na mobile.
  - Product card u 4-kolonskom grid (desktop): `{% responsive_picture image alt='...' sizes='(max-width: 768px) 100vw, 25vw' %}` — bira 400w na desktop (300px slot), 400w na mobile.
  - Brand listing kartica: `{% responsive_picture brand.logo alt=brand.name format='PNG' sizes='(max-width: 768px) 100vw, 33vw' %}` — bira 400w na desktop (400px slot), 400w na mobile.
- **`loading="lazy"` default:** sve slike ispod fold-a lazy-load (project-context.md § Performance must-haves: "loading='lazy' atribut na slikama ispod fold-a"). Above-the-fold (hero) caller prosleđuje `loading="eager"`.
- **Defensive `if not image:` branch:** caller (template) ne mora wrap-ovati `{% if product.main_image %}` oko taga jer helper gracefully renderuje prazno. Ovo je **boundary defensive validation** (project-context.md § Anti-pattern: Defensive validation: "Trust internal code, validate only at boundaries") — tag je BOUNDARY između template i media pipeline, validacija je opravdana.

### Local development na Windows-u bez libmagic — MANDATORY Docker

- **Problem (empirijski potvrđen):** Windows nema native `libmagic` system paket; `python-magic-bin` Windows wheel SEGFAULT-uje (exit code 139) na `magic.from_buffer()` poziv. Adversarial reviewer empirijski testirao — bez izuzetka, libmagic crash-uje proces na Windows host-u.
- **Posledica:** **Mihas (Windows host) MUST pokretati sve Story 2.3 testove i smoke kroz Docker kontejner.** Direktno `uv run pytest` na Windows host-u NIJE PODRŽANO.
- **Sanctioned path:**
  - **Test suite:** `just test` (mapira na `docker compose -f compose/local.yml run --rm django uv run pytest`)
  - **Manual smoke (Task 7):** `docker compose -f compose/local.yml run --rm django uv run python manage.py shell` umesto host shell-a
  - **Lint:** `uv run ruff check .` može na host-u (ne dotiče libmagic) — OK
- **NE RADITI:**
  - NE pokretati `uv run pytest` direktno na Windows PowerShell (SEGFAULT)
  - NE instalirati `python-magic-bin` na Windows host (empirijski potvrđeno: i dalje SEGFAULT-uje)
  - NE skip-ovati testove sa `@pytest.mark.skipif(sys.platform == "win32")` — to maskira problem; Docker je pravo rešenje
- **CI (GitHub Actions):** koristi Linux runner (`ubuntu-latest` per Story 1.9 CI config) gde `libmagic1` apt instalira se u workflow setup; testovi prolaze u CI bez problema.

### Boundary defensive validation rationale

- **Project-context.md kaže "Trust internal code, validate only at boundaries"** — Story 2.3 dvostruka validacija (None/empty + MIME + Image.verify()) može izgledati kao over-engineering ako čitaš isolated. Ali `validate_image_mime` je BOUNDARY funkcija koja prima `UploadedFile` iz untrusted source-a (admin form upload od Editor role-a). Sva validacija JE na boundary-ju per project-context.md § Security must-haves: "MIME validation na svakom upload polju (Pillow + python-magic)".
- **Defensive `if not image:` u template tag-u** — ne validira internal contract (caller je interni Django template), VEĆ gracefully degrade-uje ako ImageField nema fajl prikačen (DB ImageField može biti `null=True, blank=True` što je čest case za Product.main_image kad admin tek dodaje proizvod). Ovo je **graceful fallback**, ne defensive validation.

### Out-of-scope za Story 2.3

- **NEMA `apps/media_pipeline/signals.py`** — Story 2.4 prvi put kreira sa `post_save` na `ProductBrochure` za PDF cover thumbnail generation.
- **NEMA `apps/media_pipeline/apps.py.ready()` hook** — Story 2.4 dodaje za signal registraciju.
- **NEMA `validate_pdf_mime()` helper** — Story 2.4 dodaje paralelno (zaseban helper sa `application/pdf` MIME check).
- **NEMA admin form integration** — Story 8.4 (Brand CRUD) i 8.6 (Product CRUD) konzumiraju `validate_image_mime()` kroz `clean_<field>()` metode; Story 2.3 NE menja `apps/brands/admin.py` niti `apps/products/admin.py`.
- **NEMA models.py promena u apps.brands ili apps.products** — sve image polja su već definisana u 2.1/2.2; Story 2.3 ne dodaje image polja niti menja njihove constraint-e.
- **NEMA Bootstrap card style-ova za responsive_picture** — CSS klase su caller-side concern (Story 2.6/2.7 dodaje `.coric-product-card__image` u `static/css/components/product-card.css`).
- **NEMA migracije na `apps.media_pipeline`** — utility app NEMA modela; jedina migracija je sorl-thumbnail vlasništvo (`thumbnail.0001_initial`).
- **NEMA Lightbox integracije** — Story 2.5 dodaje GLightbox koji koristi thumbnail-ove iz Story 2.3 pipeline-a kroz `<a class="glightbox" href="{full_image_url}"><img src="{thumb_url}"></a>` pattern; Lightbox JS bootstrap je 2.5 scope.
- **NEMA Brand.logo render-a u Story 2.3** — Story 2.6 (Brand Listing) je prvi konzument; MUST koristiti `{% responsive_picture brand.logo alt=brand.name format='PNG' %}` da preserve-uje PNG transparency (per Decision MP-D5).

### Gotchas

- **Gotcha MP-1 — `MediaPipelineConfig.name` MORA imati `apps.` prefix** (mirror BR-1/PR-1). Bez prefiksa Django INSTALLED_APPS ne nalazi app i raise-uje `LookupError: No installed app with label 'media_pipeline'` pri prvom modelu reference.
- **Gotcha MP-2 — sorl-thumbnail MORA biti registrovan PRE `apps.media_pipeline`** (jer `apps/media_pipeline/templatetags/media_tags.py` import-uje `from sorl.thumbnail import get_thumbnail` na module level). Ako redosled obrnuto, Django template engine pokušava da auto-discover media_tags PRE nego što je sorl.thumbnail registrovan, ImportError.
- **Gotcha MP-3 — `media/` direktorijum ne postoji default** — sorl-thumbnail će ga kreirati pri prvom thumbnail generate-u, ali admin upload (Product.main_image) ranije pokušaj može fail-ovati ako media_root path nije writable. Verifikuj `BASE_DIR / "media"` postoji ili kreiraj manually: `New-Item -ItemType Directory -Force media/products/main; media/thumbnails`.
- **Gotcha MP-4 — `MEDIA_URL` mora servirati URL handler u DEBUG** — Django **NE servira media u production-u** (Nginx / Whitenoise je odgovornost); ali u DEBUG mode dev server mora imati `urlpatterns += static(settings.MEDIA_URL, ...)` u `config/urls.py`. Bez toga, render-ovan `<img src="/media/thumbnails/...jpg">` će dati 404 u dev-u i Mihas može pomisliti da je sorl bug.
- **Gotcha MP-5 — sorl-thumbnail KVStore migracija je vlasništvo sorl.thumbnail paketa** — pojavljuje se u `migrate --plan` čak iako `apps/media_pipeline/migrations/` je prazan. Ne tražiti `makemigrations media_pipeline` u Task 5 — to bi vratilo "No changes detected" jer NEMA modela u apps.media_pipeline.
- **Gotcha MP-6 — Pillow `Image.verify()` troši stream** — moramo `upload.seek(0)` u `finally` block-u utility-ja. Bez toga, caller form pokušaj save-a `upload` na disk će ga snimiti prazan jer cursor je na kraju fajla.
- **Gotcha MP-7 — Windows local dev libmagic — MANDATORY Docker za sve testove (`just test` rešava)** — Empirijski potvrđeno (adversarial reviewer): `magic.from_buffer(b"\xff\xd8...")` SEGFAULT-uje na Windows host-u (exit code 139), bez obzira na `python-magic-bin` instalaciju. **Posle Task 1.6 (modify justfile per MP-D6), `just test` korektno mapira na `docker compose -f compose/local.yml run --rm django uv run pytest`** — Dev koristi konzistentnu `just test` komandu kroz Task 6, Task 7, Task 8 bez razloga za manual Docker compose duplikate. Direktno `uv run pytest` na Windows host-u **NIJE PODRŽANO** — libmagic SEGFAULT-uje (potvrđeno empirijski exit 139). Linux/macOS dev environment-i takođe rade kroz `just test` (Docker je cross-platform); ko ne želi Docker overhead na Linux-u može pokrenuti `uv run pytest` direktno (libmagic1 sistemski paket na Linux-u radi). CI (GitHub Actions, Ubuntu) prolazi bez problema jer `libmagic1` apt instalira se u workflow setup.
- **Gotcha MP-8 — `{% responsive_picture %}` inclusion_tag invokacija sintaksa** — Django inclusion_tag-ovi pozivaju se SAMO kao `{% tag arg1=val1 %}` (keyword args MORAJU biti named); positional argument `image` je opciono prvi positional. Ako Editor pošalje `{% responsive_picture image=product.main_image alt="Test" %}` (sa eksplicitnim `image=`), to MORA raditi — testovi pokrivaju oba pattern-a.
- **Gotcha MP-9 — `THUMBNAIL_PRESERVE_FORMAT = False` gubi transparency** — Brand.logo upload-ovan kao PNG sa transparent backgrund-om biće convert-ovan u JPEG sa solid white background-om kroz responsive_picture. Story 2.6 može override-ovati per call sa `format="PNG"` ili Story 2.3 settings update sa `THUMBNAIL_PRESERVE_FORMAT = True` (ali to onda znači većih file size-eva za sve slike, premature optimization na drugu stranu). Editor mora znati ako brand logo izgleda "loše" — to je config trade-off, ne bug.
- **Gotcha MP-10 — sorl-thumbnail thumbnail filename pattern je hash-based** — fajlovi u `media/thumbnails/` imaju imena tipa `<hash>.jpg`, NE human-readable. Mihas ne sme da zavisi od stable filename-a (npr. u testovima ne assertovati exact filename, već `glob.glob("media/thumbnails/*.jpg")` count).
- **Gotcha MP-11 — Boundary regression za media_pipeline** — `apps/media_pipeline/**/*.py` NE SME uvoziti `apps.products` ili `apps.brands` (per architecture.md app dep rule). Test pokriva oba smera u `tests/integration/test_app_boundaries.py`. Ako budući Story doda kasnije `models.py` u media_pipeline koji referencira Product (npr. `MediaAsset` sa FK ka Product), boundary rule se mora preispitati — ali za 2.3, utility-only, pravilo je strogo.
- **Gotcha MP-12 (REVIEW FIX MP-R1) — `apps/media_pipeline/tests/` MORA biti BEZ `__init__.py`** — Story 2.3 je prva story koja uvodi per-app `conftest.py`. Kombinacija `tests/__init__.py` (root) + `apps/media_pipeline/tests/__init__.py` + `--import-mode=importlib` (pyproject.toml) izaziva pytest plugin name collision: `ValueError: Plugin already registered under a different name: tests/conftest.py = apps/media_pipeline/tests/conftest.py`. Test collection FAIL-uje na bilo kojem run-u koji kombinuje root `tests/` sa `apps/media_pipeline/tests/` (uključujući `uv run pytest` bez argumenata). 2.1/2.2 `apps/brands/tests/__init__.py` i `apps/products/tests/__init__.py` ostaju jer NEMAJU per-app `conftest.py`. Future stories koje uvode dodatne per-app `conftest.py`-jeve takođe MORAJU izostaviti `__init__.py` (ili premestiti conftest fixtures u root `tests/conftest.py`).

### Decisions

**Decision MP-D1 — `sorl-thumbnail` umesto `easy-thumbnails` ili `django-imagekit`**

- **Pitanje:** Koji image processing paket koristiti?
- **Odluka:** `sorl-thumbnail >= 13.0.0` (per architecture.md § Image processing line 169: "Battle-tested, lazy generation, srcset helper, manji overhead nego imagekit"). pyproject.toml već ima pin (Story 1.1).
- **Alternative razmatrane:**
  - **`easy-thumbnails`** — manje održavan (poslednji release 2022); manji overhead, ali bez `<picture>` srcset helper-a.
  - **`django-imagekit`** — moćniji (custom processors, in-memory cache opcije), ali kompleksniji setup i veći overhead.
- **Rationale:** sorl-thumbnail je standardni Django image pipeline 2024+; lazy generation + KVStore caching + native Django template tag (`{% thumbnail %}`) odgovara low-touch admin workflow-u (Editor upload-uje, sve ostalo je automatski). Architecture decision iz pre-2.3 phase je stabilan.

**Decision MP-D2 — Lazy generation umesto post_save signal batch**

- **Pitanje:** Generisati sva 3 thumbnail varijante (400w/800w/1600w) odmah pri Product save-u (post_save signal), ili lazy on-demand?
- **Odluka:** **Lazy on-demand** kroz sorl-thumbnail standard behavior. Post_save signal za thumbnail generation je **ANTI-PATTERN** u sorl-thumbnail world-u (paket je dizajniran za lazy access).
- **Rationale:**
  - **(a) Performance:** Admin save Product-a ne čeka 3 image generation-a (može trajati 500ms-2s za large images); lazy znači UI je responzivan.
  - **(b) Cost optimizacija:** Ako Product nema views u prvih mesec dana (rare proizvod), nikad ne generišemo thumbnails — ušteda disk space.
  - **(c) Cache hit drugi render:** sorl-thumbnail KVStore čuva mapping; samo PRVI HTTP GET na svaku varijantu kreira fajl. Daljnji request-ovi su file system read direktno iz Nginx-a (bez Python overhead-a).
- **Alternativa razmatrana:** `post_save` signal koji background-batch generiše sve varijante (kao u Story 2.4 PDF cover thumbnail koji je sync u post_save). Razlika: PDF cover je JEDAN fajl (~100KB), image varijante su TRI fajla, ukupno 200-500KB — overhead razlika opravdana.
- **Reversibilnost:** Ova odluka je **reversibilna** — Story 2.4 može uvesti `apps/media_pipeline/signals.py` koji takođe handler-uje `post_save` na Product za eager generation ako Mihas u future hoće (out-of-scope za 2.3).

**Decision MP-D3 — `validate_image_mime()` raise-uje ValidationError umesto bool return**

- **Pitanje:** Treba helper da vrati `bool` (caller decide-uje da raise-uje) ili da raise-uje sam?
- **Odluka:** **Raise-uje ValidationError** sam.
- **Rationale:**
  - **(a) Django form `clean_<field>()` API očekuje ValidationError raise** — bool return zahteva caller wrapping što je boilerplate.
  - **(b) Locale-aware poruke** — helper konstruše error string sa `gettext_lazy`; caller ne mora znati format poruke.
  - **(c) Consistency sa Django built-in validators** — `URLValidator`, `EmailValidator` raise-uju ValidationError, ne return bool.
- **Posledice:** Caller ne sme uvoditi try/except oko helper poziva u `clean_<field>()` — neka ValidationError propagate. Ako caller ipak hoće bool semantiku za neki edge case (npr. multi-image upload gde pojedinačni fail ne treba da prekida batch), može wrap-ovati:
  ```python
  try:
      validate_image_mime(image)
      is_valid = True
  except ValidationError:
      is_valid = False
  ```

**Decision MP-D4 — `responsive_picture` MORA biti `inclusion_tag`, NE `simple_tag` koji vraća `mark_safe(html_string)`**

- **Pitanje:** Inclusion_tag (template-based render) ili simple_tag (Python string return)?
- **Odluka:** **inclusion_tag** sa `templates/media_pipeline/responsive_picture.html`.
- **Rationale:**
  - **(a) Maintainability:** HTML structure u template fajlu je lakše da modifikuje od string concatenacije u Python-u.
  - **(b) djade format pass:** template-based render se validira djade-om u CI; simple_tag string return prolazi kroz Python ruff koji ne hvata HTML format issues.
  - **(c) Testing:** Django template test rendering je standardan pattern; assertion `<picture>` element u rendered output je čist.
- **Posledice:** Caller MORA uključiti `{% load media_tags %}` na vrhu template-a pre `{% responsive_picture ... %}` poziva. Ovo je standard Django pattern (matches `{% load i18n %}`, `{% load thumbnail %}`).

**Decision MP-D5 — `THUMBNAIL_PRESERVE_FORMAT = False` globalno + per-call `format` kwarg override za PNG transparency**

- **Pitanje:** Kako balansirati bandwidth (JPEG default) sa potrebom za PNG transparency-em (Brand.logo)?
- **Odluka:** **Global setting `THUMBNAIL_PRESERVE_FORMAT = False`** (svi thumbnail-ovi po default-u su JPEG za bandwidth) + **per-call override kroz `format` kwarg** u `{% responsive_picture %}` template tagu.
- **Rationale:**
  - **(a) Bandwidth:** 99% slika u sistemu (Product.main_image, ProductImage.image, ProductVariant.image, ProductTestimonial.photo) su fotografije proizvoda — JPEG @ quality=85 daje ~30-50KB za 800w što je optimalno za web. Globalna PNG postavka bi udvostručila bandwidth (~80-150KB za isti 800w).
  - **(b) Transparency:** Brand.logo (Story 2.1) i potencijalno blog cover_image (Epic 5) su PNG sa transparency koji vizuelno **MORA** biti preserved (brand logo na šarenoj pozadini ne sme imati solid white square iza sebe).
  - **(c) Explicit > implicit:** caller koji zna da slika ima transparency MUST explicit prosledi `format='PNG'` — bez forenzike "da li sorl per-image detektuje". Per project-context.md § Anti-pattern: defensive validation, prefer explicit caller intent.
- **Trade-off:** Editor MORA upload-ovati Brand.logo kao PNG sa pravom transparency-em (ne JPEG sa fake white background); Story 2.6 template MORA pozvati tag sa `format='PNG'` kwarg-om. Ako Editor pogreši (upload-uje JPEG kao logo), thumbnail će biti PNG ali bez transparency — nije bug, već Editor error.
- **Alternative razmatrane:**
  - **`THUMBNAIL_PRESERVE_FORMAT = True` globally** — odbačeno: udvostručava bandwidth za 99% slika; PNG za fotografije je waste.
  - **Auto-detect transparency u tag-u** (`image.mode == "RGBA"` provera pre `get_thumbnail` poziva) — odbačeno: defensive validation na boundary između template i sorl-thumbnail; sorl već handle-uje internal logic; eksplicitan kwarg je čistiji contract.
- **Posledice (cross-story):**
  - Story 2.6 (Brand Listing): `{% responsive_picture brand.logo alt=brand.name format='PNG' %}`
  - Story 2.7 (Product Detail): `{% responsive_picture product.main_image alt=product.name %}` — default JPEG (fotografije proizvoda)
  - Epic 5 (Blog): `{% responsive_picture blog_post.cover_image alt=blog_post.title format='PNG' %}` ako cover ima transparency

**Decision MP-D6 — `justfile` `test` recept mapira na Docker (cross-cutting infra)**

- **Pitanje:** Kako rešiti libmagic SEGFAULT na Windows host-u koji blokira `uv run pytest` direktno?
- **Odluka:** **Modifikovati `justfile` `test` recept (Task 1.6)** da koristi `docker compose -f compose/local.yml run --rm django uv run pytest` umesto host-side `uv run pytest`. `just test` postaje kanonska test komanda na svim platformama (Docker je cross-platform).
- **Rationale:**
  - **(a) libmagic SEGFAULT:** Empirijski potvrđeno — `magic.from_buffer()` na Windows host-u exit 139 (SEGFAULT), bez obzira na `python-magic-bin`. Direktan `uv run pytest` NIJE OPCIJA na Windows-u za Story 2.3+ jer svi media_pipeline testovi učitavaju `apps/media_pipeline/utils.py` koji `import magic` na module level.
  - **(b) Future stories:** Story 2.4 dodaje `poppler-utils` system dep (`pdf2image` paket) — isti problem na Windows-u. Epic 4 form upload testovi koji konzumiraju `validate_image_mime()` takođe pogađaju ovo. Cross-cutting infra fix u 2.3 sprečava da svaka future story redefinira sopstveni Docker workaround.
  - **(c) Konzistentan UX:** Mihas već koristi Docker za `just dev` (Django runtime), `just dev-shell`, `just dev-manage`. Test recept koji mapira na Docker je prirodno proširenje — Mihas ne mora memorisati "kad host, kad Docker".
  - **(d) Cross-platform reliability:** Linux/macOS dev environment-i takođe imaju koristi od Docker test recept-a (eliminiše "radi kod mene, ne radi na CI" rizike koji nastaju iz subtle libmagic/Pillow version drift host vs container).
- **Trade-off:** Tests sada zahtevaju Docker Desktop pokrenut + image build-ovan barem jednom (`just dev-build`). `--rm` flag kontrolisno čisti exited kontejner posle svakog run-a (no leak). Overhead `docker compose run --rm` je ~1-2s startup, prihvatljiv za test workflow (CI ne koristi `just test` već direktan `uv run pytest` u Linux runneru gde libmagic radi).
- **Alternative razmatrane:**
  - **Separate `just test-docker` recipe** (zadrži `just test` za Linux/macOS direkt) — odbačeno: deli dev mental model, Mihas mora pamtiti koji koristi kad. Konfuzno za onboarding-Editor scenario u Epic 8.
  - **`@pytest.mark.skipif(sys.platform == "win32")` na testove koji koriste libmagic** — odbačeno: maskira problem, ne rešava ga; Mihas bi imao false-green test suite na Windows host-u bez stvarne security validacije.
  - **`python-magic-bin` Windows wheel** — odbačeno: empirijski potvrđeno da i dalje SEGFAULT-uje.
- **Migration path:** Story 2.3 je breaking change za `just test` ponašanje. Future stories (2.4+) **PRETPOSTAVLJAJU** da `just test` mapira na Docker — story spec-ovi ne moraju ponovo dokumentovati Docker workaround za libmagic/poppler. Gotcha MP-7 je single source of truth za ovaj contract.
- **Posledice (cross-story):**
  - Story 2.4 (PDF cover): `just test` automatski pokriva `poppler-utils` sistemska deps u Docker kontejneru.
  - Epic 4 (Contact forms): `just test` pokriva `validate_image_mime()` testove na Windows host-u.
  - Epic 8 (Admin onboarding): `just test` pokriva `clean_<image_field>()` integration testove.
  - CI (GitHub Actions): NE koristi `just test` — direktan `uv run pytest` u Ubuntu runneru sa `libmagic1` apt-installed. CI workflow ostaje nepromijenjen.

**Decision MP-D7 — Kanonski sorl-thumbnail setting je `THUMBNAIL_PREFIX`, NE `THUMBNAIL_DIRNAME` (post-implementation correction)**

- **Pitanje:** Prethodna verzija AC2 + interface contract-a referencirala je `THUMBNAIL_DIRNAME = "thumbnails"` — ali u sorl-thumbnail source-u taj attribute NE postoji (silent no-op assignment kao Django setting).
- **Odluka:** Rename na `THUMBNAIL_PREFIX = "thumbnails/"` (sa trailing slash) — to je kanonski setting koji sorl interno koristi pri konkatenaciji sa storage path-om za thumbnail URL/file lokaciju.
- **Rationale:**
  - **(a) sorl source verification:** `sorl.thumbnail.conf.defaults.THUMBNAIL_PREFIX = ""` postoji; `THUMBNAIL_DIRNAME` ne postoji u sorl konfig modulu — assignment ne menja ponašanje (false documentation).
  - **(b) Test discovery bug:** test_thumbnails.py je imao 4 `settings.THUMBNAIL_DIRNAME = "thumbnails"` override-a koji su izgledali kao defensive isolation, ali su bili no-op. FIX-7 ih uklanja i delegira na canonical base.py setting.
  - **(c) Trailing slash convention:** sorl konkatenira string-as-is (NEMA path normalization); bez trailing slash-a thumbnail URL-ovi bi bili `/media/thumbnailscache/...` (no separator), prouzrokujući 404.
- **Trade-off:** Ne postoji — pure correction. Production behavior identičan (sorl koristi default `cache` ime kad je THUMBNAIL_PREFIX prazan; sad eksplicitno koristi `thumbnails/`).
- **Posledice (cross-story):**
  - Future stories ne treba da referenciraju THUMBNAIL_DIRNAME (ne radi).
  - Path assertion u testovima koje proveravaju `media/thumbnails/` su sad korektne (oslanjaju se na base.py setting, ne na test-level override).
- **Files modified by FIX-7:**
  - `config/settings/base.py` — `THUMBNAIL_PREFIX = "thumbnails/"` (canonical).
  - `apps/media_pipeline/tests/test_thumbnails.py` — uklonjena 4 settings.THUMBNAIL_DIRNAME no-op assignment-a.
  - `_bmad-output/implementation-artifacts/2-3-interface-contract.md` — rename u section 3 settings_keys_added.

**Decision MP-D8 — `DATA_UPLOAD_MAX_MEMORY_SIZE` + `FILE_UPLOAD_MAX_MEMORY_SIZE` raised project-wide na 10-11MB (cross-cutting infra)**

- **Pitanje:** `validate_image_mime` dozvoljava do 10MB image upload (`MAX_UPLOAD_SIZE_BYTES`), ali Django default `DATA_UPLOAD_MAX_MEMORY_SIZE = 2.5MB` bi raise-uo `RequestDataTooBig` PRE nego što helper dobije šansu da validate-uje. Šta sa upload limit settings?
- **Odluka:** Postaviti **`DATA_UPLOAD_MAX_MEMORY_SIZE = 11 * 1024 * 1024` (11MB)** + **`FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024` (10MB, matches helper)** u `config/settings/base.py`. 11MB DATA buffer daje 1MB margine iznad 10MB FILE limit-a za form metadata (CSRF token, field labels, multi-part boundary).
- **Rationale:**
  - **(a) Helper consistency:** Bez ovog setting-a, Django bi raise-uo `RequestDataTooBig` (HTTP 413) za bilo koji upload > 2.5MB pre nego što stigne do `clean_<field>()`. Editor bi video Django default error stranicu, ne friendly helper poruku — bad UX.
  - **(b) Disk DoS prevention:** Ako `FILE_UPLOAD_MAX_MEMORY_SIZE = 10MB` matches `MAX_UPLOAD_SIZE_BYTES = 10MB`, sve do limit-a se drži u memoriji (no spool to disk); preko limit-a Django odbacuje pre disk spill-a. Razdvajanje (npr. FILE=100MB, helper=10MB) bi dozvolilo attackeru da spool-uje 100MB na disk pre nego što helper odbije → disk DoS vektor.
  - **(c) Cross-epic visibility:** Ovaj setting utiče na **SVE POST endpoints**, ne samo image upload. Future Epic 4 (lead-gen contact forms) text-only POST bodies su < 100KB (irrelevant — well below limit). Epic 8 admin Editor može uploadovati slike per spec. Story 9.x Nginx reverse proxy treba da ima per-location `client_max_body_size` kao defense-in-depth layer.
- **Trade-off:** Limit je **GLOBAL** — sve POST endpoints prihvataju do 11MB body, ne samo image uploads. Za scope CORIC AGRAR-a (no large API ingest, no bulk file upload feature) ovo je acceptable. Story 9.x Nginx config TREBA `client_max_body_size 11M` za public POST endpoints; admin može imati viši limit kroz `client_max_body_size 50M` (ako će Story 8.x bulk product import biti scope).
- **Alternative considered:**
  - **Per-view upload size guard kroz decorator** (`@require_max_upload_size(11*1024*1024)`) — odbijeno: rasipa boilerplate na svaku FormView/CreateView; settings-level je simpler i centralizovan.
  - **Django default 2.5MB + helper raise pre helper-a** — odbijeno: Django RequestDataTooBig stranica je generic + zbunjujuća za Editor onboarding.
  - **`FILE_UPLOAD_HANDLERS` override za streaming** — odbijeno: validate_image_mime ne podržava streaming check; in-memory handler je dovoljan za 10MB scope.
- **Posledice (cross-story):**
  - **Story 9.x (Production Nginx):** MORA imati `client_max_body_size 11M` (ili viši za admin) — bez tog Nginx bi odbacio sa HTTP 413 PRE nego što Django dobije request.
  - **Story 4.x (Contact forme):** NE treba dodatne upload guards (text-only payload, well below 11MB).
  - **Story 8.x (Admin):** Editor može upload-ovati 10MB slika kroz admin formu bez additional config-a.
- **References:** Security MEDIUM-1 (Story 2.3 iter 1 review), Django docs `DATA_UPLOAD_MAX_MEMORY_SIZE`.
- **Files modified by FIX-4 (locked u MP-D8):**
  - `config/settings/base.py` — DATA_UPLOAD_MAX_MEMORY_SIZE + FILE_UPLOAD_MAX_MEMORY_SIZE.
  - `apps/media_pipeline/tests/test_settings.py` — assertions (FIX-14 iter 2).

## Testing Notes

### Šta TEA treba da pokrije (RED phase u Step 3)

**Test file org (per project-context.md § Test organization):**
- Unit testovi kolokovani uz app — `apps/media_pipeline/tests/test_<module>.py`
- Cross-app integration test (boundary) — `tests/integration/test_app_boundaries.py` (proširenje 2.2 fajla)

**Fixture requirements:**
- `pytest-django` ve postavljen (Story 1.x); `pytestmark = pytest.mark.django_db` na test module level za DB testove
- Plain `Model.objects.create()` (factory_boy NIJE u dev deps; mirror 2.2 pattern)
- `SimpleUploadedFile` iz `django.core.files.uploadedfile` za image upload mock-ove
- Inline JPEG/PNG/WebP magic bytes (vidi smoke test Task 7.1 za reference JPEG bytes)

**Test coverage per AC:**

| AC | Test file | Test funkcije |
|---|---|---|
| AC1 (app skeleton) | `apps/media_pipeline/tests/test_apps.py` | `test_media_pipeline_config_name`, `test_media_pipeline_in_installed_apps`, `test_sorl_thumbnail_in_installed_apps` |
| AC2 (settings) | `apps/media_pipeline/tests/test_settings.py` (NEW) | `test_thumbnail_backend_configured`, `test_thumbnail_kvstore_configured`, `test_thumbnail_quality_85`, `test_media_url_and_root_set` |
| AC3 (validate_image_mime) | `apps/media_pipeline/tests/test_utils.py` | 11 test scenarija per Task 6.1 (uključujući IMP-A2 None size streaming edge case) |
| AC4 (responsive_picture tag) | `apps/media_pipeline/tests/test_templatetags.py` | 10 test scenarija per Task 6.2 (uključujući AC10 format kwarg PNG/JPEG testove) |
| AC5 (rejection) | `apps/media_pipeline/tests/test_utils.py` | `test_validate_image_mime_rejects_pdf_as_image`, `test_validate_image_mime_rejects_exe_as_image`, `test_validate_image_mime_rejects_corrupt_jpeg`, `test_validate_image_mime_rejects_oversize_upload` (deo Task 6.1 set-a) |
| AC6 (thumbnail dir + KVStore) | `apps/media_pipeline/tests/test_thumbnails.py` | 4 test scenarija per Task 6.3 |
| AC7 (migracija) | Manual review (mirror 2.2 AC10 pattern) | — |
| AC8 (regression + boundary) | `tests/integration/test_app_boundaries.py` | `test_media_pipeline_does_not_import_products`, `test_media_pipeline_does_not_import_brands` |
| AC10 (format='PNG' preserve) | `apps/media_pipeline/tests/test_templatetags.py` | `test_responsive_picture_format_png_preserves_alpha`, `test_responsive_picture_format_jpeg_default_loses_alpha` |

**Specifični test scenariji za AC5 (kritični security testovi):**

1. **Validan JPEG (mime detect):** `b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01..."` + `.jpg` ext → `validate_image_mime` PASS
2. **Validan PNG:** `b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR..."` + `.png` ext → PASS
3. **Validan WebP:** `b"RIFF\x00\x00\x00\x00WEBP..."` + `.webp` ext → PASS
4. **PDF kao slika:** `b"%PDF-1.4\n..."` + `.jpg` ext (fake) → ValidationError (`Nedozvoljen tip slike: application/pdf`)
5. **EXE kao slika:** `b"MZ\x90\x00..."` + `.jpg` ext → ValidationError
6. **Validan JPEG header + corrupt body:** SOI marker (`\xff\xd8\xff\xe0`) zatim random bytes — PASS prvi MIME check, FAIL Image.verify() → ValidationError (`Slika je oštećena ili nije validan format`)
7. **Prazan upload (size=0):** SimpleUploadedFile("empty.jpg", b"") → ValidationError (`Slika je prazna ili nije priložena`)
8. **None upload:** `validate_image_mime(None)` → ValidationError, NE AttributeError (graceful guard)
9. **Seek side-effect:** posle `validate_image_mime(upload)`, `upload.tell() == 0` (stream resetovan)

**Specifični test scenariji za AC6 (thumbnail pipeline):**

1. **Thumbnail kreira fajl u media/thumbnails/:**
   ```python
   product.main_image = SimpleUploadedFile("test.jpg", JPEG_BYTES)
   product.save()
   t = engines['django'].from_string("{% load media_tags %}{% responsive_picture product.main_image alt='T' %}")
   t.render({"product": product})
   assert any(p.suffix == ".jpg" for p in (settings.MEDIA_ROOT / "thumbnails").rglob("*.jpg"))
   ```
2. **KVStore se populiše:**
   ```python
   from sorl.thumbnail.models import KVStore
   initial_count = KVStore.objects.count()
   # render template
   final_count = KVStore.objects.count()
   assert final_count > initial_count  # bar jedan novi entry per width
   ```
3. **Drugi render — cache hit (no nova fajla):**
   ```python
   # prvi render
   t.render({"product": product})
   files_after_first = set((settings.MEDIA_ROOT / "thumbnails").rglob("*.jpg"))
   # drugi render
   t.render({"product": product})
   files_after_second = set((settings.MEDIA_ROOT / "thumbnails").rglob("*.jpg"))
   assert files_after_first == files_after_second
   ```
4. **PNG source → JPG output:**
   ```python
   product.main_image = SimpleUploadedFile("test.png", PNG_BYTES)
   product.save()
   t.render({"product": product})
   # svi thumbnail-ovi su .jpg
   assert all(p.suffix == ".jpg" for p in (settings.MEDIA_ROOT / "thumbnails").rglob("test_*"))
   ```

**Specifični test scenariji za AC4 (template tag):**

1. **Output sadrži `<picture>` element:**
   ```python
   html = render_template("{% load media_tags %}{% responsive_picture product.main_image alt='Test' %}")
   assert "<picture>" in html
   assert "</picture>" in html
   ```
2. **Srcset ima 3 varijante:**
   ```python
   assert " 400w" in html
   assert " 800w" in html
   assert " 1600w" in html
   ```
3. **Fallback src je largest (1600w):**
   ```python
   # parse srcset, last entry = 1600w; src = isti URL kao 1600w entry
   ```
4. **`None` image → prazan render:**
   ```python
   product.main_image = None
   product.save()
   html = render_template_with(product=product)
   assert "<picture>" not in html  # empty/whitespace render
   ```
5. **Lazy loading default:**
   ```python
   assert 'loading="lazy"' in html
   ```
6. **Eager loading override:**
   ```python
   html = render_template("{% responsive_picture image alt='T' loading='eager' %}")
   assert 'loading="eager"' in html
   ```
7. **CSS klasa primenjuje se:**
   ```python
   html = render_template("{% responsive_picture image alt='T' css_class='my-class' %}")
   assert 'class="my-class"' in html
   ```

**Boundary tests (AC8, mirror 2.2 AC12 pattern):**

```python
# tests/integration/test_app_boundaries.py — DODATI dve nove funkcije
# `_assert_no_import` helper je VEĆ DEFINISAN u ovom fajlu (iz Story 2.2 AC12) —
# samo dodaj test funkcije, NE pisati novu AST walk logiku.
def test_media_pipeline_does_not_import_products():
    """Per architecture.md § App dependency graph — media_pipeline je utility,
    NE SME importovati domain app apps.products.
    """
    _assert_no_import(pathlib.Path("apps/media_pipeline"), "apps.products")


def test_media_pipeline_does_not_import_brands():
    """Per architecture.md § App dependency graph — media_pipeline je utility,
    NE SME importovati domain app apps.brands.
    """
    _assert_no_import(pathlib.Path("apps/media_pipeline"), "apps.brands")
```

**Mock policy (per project-context.md § Mock policy):**
- NEMA mock Django ORM ili PostgreSQL — testovi koriste real test DB
- python-magic NE mock-ovati — testovi koriste real magic bytes; ako `libmagic1` missing na lokalnom Windows-u, test može skip-ovati kroz `@pytest.mark.skipif(not _libmagic_available())` ali u CI mora prolaziti
- sorl-thumbnail NE mock-ovati — integration test koristi real KVStore + real file system write u test temp dir (`settings.MEDIA_ROOT` override na temp path kroz pytest fixture)

**Pytest fixture preporuka za temp MEDIA_ROOT:**

```python
# apps/media_pipeline/tests/conftest.py
import pytest
from io import BytesIO
from PIL import Image
from django.conf import settings


@pytest.fixture
def temp_media_root(monkeypatch, tmp_path):
    """Override MEDIA_ROOT na pytest tmp_path da testovi ne pišu u repo media/ dir."""
    monkeypatch.setattr(settings, "MEDIA_ROOT", tmp_path)
    yield tmp_path
    # cleanup automatski kroz pytest tmp_path


@pytest.fixture
def sample_jpeg_bytes():
    """Minimalan validan JPEG za MIME detection testove (NIJE za thumbnail size assertion).

    Validan SOI marker `FF D8 FF E0` + minimal JFIF + DCT trailer — passes python-magic
    `image/jpeg` detect + PIL Image.verify(). Premali da bi bio source za thumbnail size
    asertion (62 bytes); za to koristi `realistic_source_image_bytes` fixture.
    """
    return (
        b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
        b"\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n"
        b"\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00"
        b"\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\xff\xda\x00\x08\x01\x01\x00\x00?\x00\x7f\xff\xd9"
    )


@pytest.fixture
def sample_png_bytes():
    """Generated PNG (RGB 10×10 red) — koristi se za PNG → JPEG konverziju test."""
    img = Image.new("RGB", (10, 10), color="red")
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def sample_png_with_alpha_bytes():
    """Generated PNG RGBA (10×10) sa transparency — koristi se za format='PNG' kwarg test (AC10)."""
    img = Image.new("RGBA", (10, 10), color=(255, 0, 0, 128))
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def sample_webp_bytes():
    """Generated WebP (RGB 10×10 red) — validan VP8 koji passes PIL Image.verify().

    Hardcoded `RIFF\x00\x00\x00\x00WEBP` byte stub NIJE validan — Image.verify() raise-uje
    UnidentifiedImageError. Generated kroz Pillow je minimalan validan VP8 lossless.
    """
    img = Image.new("RGB", (10, 10), color="red")
    buf = BytesIO()
    img.save(buf, format="WEBP")
    return buf.getvalue()


@pytest.fixture
def realistic_source_image_bytes():
    """Generated realistic JPEG (2400×1800 = ~4.3MP, quality=95) za thumbnail size assertion.

    AC6 traži da generated 400w/800w/1600w thumbnails MUST biti smaller than source —
    moguće je verifikovati SAMO kad source ima realne dimenzije (≥ 2000px wide).
    62-byte minimalni JPEG (sample_jpeg_bytes) je NEVALIDAN source za ovo merenje.

    IMP-A3 rationale: Solid-color slika (Image.new("RGB", ..., color=(120, 80, 200)))
    JPEG-uje na samo ~5-10KB čak i na 2400×1800 (DCT high-compression za uniform polje).
    Posledica: 400w thumbnail solid-color slike može biti VEĆI od source-a u file bytes
    zbog JPEG header overhead-a (~600 bytes) plus quality=85 koeficijenti vs source quality=95.
    Rešenje: Image.effect_noise((2400, 1800), sigma=64) generiše visoko-entropijski noise
    patten koji ne kompresuje dobro (sigma=64 → ~500KB-1MB JPEG @ quality=95) — garantuje
    da su sve tri varijante 400/800/1600 strogo manje u file bytes.
    """
    img = Image.effect_noise((2400, 1800), sigma=64)
    # effect_noise vraća "L" (grayscale) mode — convert na "RGB" radi konzistentnosti sa
    # JPEG output format-om (libjpeg interno radi YCbCr, RGB je standardan input).
    img = img.convert("RGB")
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=95)
    return buf.getvalue()


@pytest.fixture
def corrupt_jpeg_bytes():
    """JPEG sa validnim SOI markerom + truncated body — passes libmagic, FAIL Image.verify().

    Konstrukcija: validan SOI (FF D8 FF E0) + JFIF header + truncated DCT scan
    (presečen u sredini Huffman tabele bez EOI marker-a). python-magic detect-uje
    `image/jpeg` PASS prvi check; PIL Image.verify() raise-uje OSError ili UnidentifiedImageError.
    """
    return (
        b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
        b"\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07"
        # truncated — bez Huffman tabele, bez SOS markera, bez EOI (FF D9)
        b"\x00\x00\x00\x00CORRUPT_TRUNCATED_BODY"
    )
```

### Test discipline reminders (per project-context.md § Test discipline)

- **TEA piše testove (RED phase), Dev piše implementaciju (GREEN phase)** — Dev NIKAD ne piše testove za Story 2.3
- Testovi se commit-uju **pre** implementacije (red phase commit)
- Implementacija se commit-uje kao **green phase** (zasebno commit)
- Failure: ako TEA testovi failuju posle Dev implementacije, story se vraća u `paused` status

### Performance smoke (NFR check)

- Posle Story 2.3, render render Product detail strane (Story 2.7 implementacija) MORA biti < 200ms TTFB lokalno (laptop, no DB load) — proveri Mihas u manual smoke. Ako je sporo, `THUMBNAIL_KVSTORE` može imati slow path; alternativa je dodavanje `LOCMEM` cache wrapper-a (Django built-in) iznad KVStore (out-of-scope za 2.3, ali Story 9.9 Performance audit može uvesti).

---

**End of Story 2.3 spec**
