---
story-id: "2.4"
story-key: 2-4-pdf-cover-thumbnail-generator
title: PDF Cover-thumbnail Generator
status: review
epic_num: 2
epic_title: Public Catalog — Browse Brands & Products
module: apps/media_pipeline/ (PROŠIRENJE postojećeg utility app-a iz Story 2.3 — dodaje signals.py + pdf_utils.py + apps.ready() hook)
created: 2026-05-30
last_modified: 2026-05-30
last_fix_iter: 1
author: Mihas (SM autonomous)
---

# Story 2.4: PDF Cover-thumbnail Generator

Status: review

## Opis

As a **dev (Mihas) koji nastavlja Epic 2 (Public Catalog) posle Story 2.3 (image pipeline foundation — `apps/media_pipeline/` utility app sa `sorl-thumbnail` konfiguracijom + `validate_image_mime()` helper + `{% responsive_picture %}` template tag)**,
I want **PDF cover-thumbnail signal pipeline u `apps/media_pipeline/` koji uvodi: (a) `apps/media_pipeline/pdf_utils.py` sa `generate_brochure_cover_thumbnail(pdf_field) -> ContentFile | None` funkcijom koja koristi `pdf2image` (`poppler-utils` system dep — VEĆ u Dockerfile per Story 1.3, verifikovano linija 42) da render-uje prvu stranu PDF-a kao 240×320px JPG, (b) `apps/media_pipeline/pdf_utils.py validate_pdf_mime(upload)` helper koji prati isti pattern kao `validate_image_mime()` iz Story 2.3 ali za `application/pdf` MIME (python-magic detect-uje PDF magic bytes `b"%PDF-"` iz signature), (c) `apps/media_pipeline/signals.py` sa `handle_brochure_post_save(sender, instance, created, raw, update_fields, **kwargs)` `post_save` handler-om za `ProductBrochure` (kasna resolucija kroz `apps.get_model("products", "ProductBrochure")` u `apps/media_pipeline/apps.py.ready()` hook — boundary regression compliance per Story 2.3 AC8/Gotcha MP-11), (d) `apps/media_pipeline/apps.py.ready()` hook koji wire-uje signal pri Django startup-u kroz `from . import signals` (per Django best practice za signal registraciju), (e) multi-layer infinite-loop guard: (i) `transaction.on_commit()` deferred render → orphan-file safety pri rollback-u (FIX iter-1 CRIT-5), (ii) skip ako `update_fields == frozenset({"cover_thumbnail_image"})` (FIX iter-1 CRIT-3 — uklonjen prethodni `if cover_already_exists: return` skip da bi se popravio Replace-PDF UX bug), (iii) `instance.cover_thumbnail_image.save(..., save=False)` Storage write bez post_save fires + Layer A guard hvata explicit `instance.save(update_fields=[...])`, (iv) trostruki DoS guard layer u `pdf_utils.py` (page count ≤ 200, render timeout ≤ 15s, rendered pixels ≤ 50M — FIX iter-1 CRIT-4)**,
so that **kad Editor (Story 8.6 admin) upload-uje PDF brošuru kroz `ProductBrochure` admin formu, signal automatski renderuje prvu stranu PDF-a u 240×320px JPG i populiše `cover_thumbnail_image` polje BEZ ručnog Editor rada; ako je PDF korumpiran ili nema validnu prvu stranu, signal **gracefully fail-uje** (Python `logger.warning()` sa product slug + brochure id + exception kontekst, save uspeva sa `cover_thumbnail_image=""`), bez ikakvih HTTP 500 grešaka koje bi pucale admin formu; Story 2.7 (Product Detail strana) **MOŽE direktno renderovati `{% responsive_picture brochure.cover_thumbnail_image %}` u brošura card-u** sa sigurnošću da polje ili sadrži automatski generisan thumbnail ili je prazno (fallback — Story 2.7 može renderovati generic PDF icon ako je polje prazno).**

Ova story je **prvi konzument `apps/media_pipeline/signals.py`** (Story 2.3 izričito **NIJE uvodila** signals.py niti `ready()` hook — `apps/media_pipeline/apps.py` (live linija 1-19) nema `ready()` metodu; Story 2.4 dodaje prvu). Story 2.4 je **prva story koja konzumira `pdf2image` paket** (već u `pyproject.toml` linija 17 — `pdf2image>=1.17.0`, verifikovano) i **prva koja proširuje `apps/media_pipeline/utils.py` pattern sa paralelnim `pdf_utils.py` module-om** (PDF MIME validacija + thumbnail rendering — semantički odvojeno od image MIME validacije; vidi Decision PDF-D1 za rationale modulnog razdvajanja). **NEMA model promena** — `ProductBrochure.cover_thumbnail_image` polje je već definisano u Story 2.2 (live `apps/products/models.py` linija 430-436, `ImageField(_("Cover thumbnail"), upload_to="products/brochure_covers/", max_length=255, blank=True, null=True)`). **NEMA migracije u media_pipeline** (utility app i dalje bez modela). **NEMA admin custom widget-a** za PDF preview — to je Story 8.6 scope. **NEMA `apps.products` direktnih import-a u media_pipeline kodu** — sav cross-app referencing kroz `django.apps.apps.get_model("products", "ProductBrochure")` kasnu resoluciju u `ready()` hook-u (per Story 2.3 AC8 boundary test koji je već **registrovan u `tests/integration/test_app_boundaries.py`** linija 130-163, **MORA ostati green posle Story 2.4 implementacije** — vidi AC9).

**Foundation za:**

- **Story 2.7 (Product Detail strana):** konzumira `{% responsive_picture brochure.cover_thumbnail_image alt=brochure.title sizes="(max-width: 768px) 120px, 240px" %}` u brošura card-u (per epics.md line 619-620: "Brošura card (cover-thumbnail + 'X.X MB, PDF' + CTA-light PREUZMI)"). Story 2.4 garantuje da je polje populated automatski; Story 2.7 ne mora da pita Editor da ručno upload-uje cover.
- **Story 8.6 (Product CRUD admin):** ProductBrochureInline (TabularInline) admin form za PDF upload — signal pucanje pri `save_model()` automatski generiše cover; Editor vidi prikazan cover thumbnail u admin list_display kroz Story 8.6 custom widget. Story 8.6 takođe MORA pozvati `validate_pdf_mime()` u `clean_pdf_file()` (per Story 2.3 AC5 pattern za image validation — Story 2.4 deliver-uje PDF analog).
- **Story 9.9 (a11y audit + performance load test):** signal sync (no Celery) pucanje pri PDF upload-u dodaje ~1-3s latency u admin save flow; Story 9.9 može meriti i opcionalno migrirati na async ako Mihas odluči (out-of-scope, dokumentovano kao Decision PDF-D4 trade-off acceptance).

**Princip:** Proširenje `apps/media_pipeline/` direktorijuma sa **dve nove module-a** (`pdf_utils.py` + `signals.py`) i **jednim `apps.py` Edit-om** (dodavanje `ready()` metode). Mirror Story 2.3 strukturalnog patterna: pure utility funkcije u `pdf_utils.py` (nema Django dependency-a osim `ValidationError`, `ContentFile`, `gettext_lazy`), signal handler odvojen u `signals.py` (depend-uje na `apps.get_model()` kasnu resoluciju), signal registracija eksplicitna u `AppConfig.ready()`. **NEMA promena u `apps/products/`** (model i admin ostaju netaknuti). **NEMA Dockerfile promena** (poppler-utils već u runtime stage-u linija 42 — verifikovano). **NEMA `pyproject.toml` promena** (pdf2image već linija 17 — verifikovano). Sav UI text iz signal handler-a je log message-i — koriste Python `logger = logging.getLogger("apps.media_pipeline.signals")` (NE `gettext` jer log poruke nisu user-facing per project-context.md § gettext / i18n u kodu — "Email subjects: koristi gettext runtime, jer subject zavisi od lokala primaoca" implicira da log poruke NISU isti contract); admin verbose_name labels (kojih nema u 2.4 jer NEMA novih modela) ostaju locale-aware kroz Story 2.2 koji ih je već definisao.

**Strukturna arhitektura — repository delta (REVIDIRANO posle FIX iter-1):** Repository dobija dva nova fajla u `apps/media_pipeline/` (`pdf_utils.py` + `signals.py`) i jedan Edit u postojećem fajlu (`apps.py` — dodavanje `ready()` metode). **FIX iter-1 CRIT-2 + IMP-5:** `pyproject.toml` DOBIJA dve nove deps kroz Task 0 — `pytest-mock>=3.14.0` (dev) + `pillow>=10.0` (direct, defensive promote iz tranzitivne). `apps/media_pipeline/utils.py` ostaje **netaknut** (image MIME validation i decompression bomb guard iz Story 2.3 idu nepromenjeni); Decision PDF-D1 razrešava zašto je PDF logika u zasebnom module-u. `apps/media_pipeline/tests/` direktorijum (BEZ `__init__.py` per Story 2.3 REVIEW FIX MP-R1) dobija **dva nova test fajla** (TEA scope, Step 3 deliverable): `test_pdf_utils.py` (PDF MIME validation + thumbnail generation unit tests, ~13 scenarija sa novim DoS + encrypted PDF testovima — FIX iter-1 CRIT-4 + CRIT-8), `test_signals.py` (signal wire-up + infinite loop guard + graceful failure + replace-PDF regen + on_commit callback tests, ~8 scenarija — FIX iter-1 CRIT-3 + CRIT-5 + CRIT-7). Postojeći `apps/media_pipeline/tests/test_apps.py` smoke (Story 2.3 deliverable) takođe dobija dva nova testa: `test_media_pipeline_ready_hook_imports_signals` i `test_post_save_receiver_registered_with_dispatch_uid` (IMP iter-1 IMP-7). **`apps/media_pipeline/conftest.py`** (Story 2.3 deliverable) dobija **jedan novi fixture**: `realistic_pdf_bytes` (per Decision PDF-D5). `tests/integration/test_app_boundaries.py` (Story 2.2 + 2.3 deliverable) ostaje **netaknut** — postojeći `test_media_pipeline_does_not_import_products` i `test_media_pipeline_does_not_import_brands` AC8 testovi (linija 130-163) **MORAJU ostati green** posle Story 2.4 (per Decision PDF-D1 + AC9 enforcement). `apps/products/`, `apps/brands/`, `config/settings/base.py`, `config/urls.py`, `justfile`, `compose/django/Dockerfile` ostaju **netaknuti** (Story 2.4 NEMA cross-cutting infra promenu — Story 2.3 MP-D6 Docker test recept je single source of truth za libmagic/poppler u testovima).

## Kriterijumi prihvatanja

**AC1 — `apps/media_pipeline/pdf_utils.py` sadrži `validate_pdf_mime()` helper sa python-magic check za `application/pdf` MIME signature + size limit (mirror Story 2.3 AC3 image pattern)**

- **Given** Story 2.3 završena (`apps/media_pipeline/utils.py` ima `validate_image_mime()` koji koristi python-magic; `libmagic1` system dep u Dockerfile linija 41; `python-magic>=0.4.27` u pyproject.toml linija 19)
- **When** kreiram `apps/media_pipeline/pdf_utils.py`
- **Then** fajl mora imati TAČNO sledeću strukturu (po istom šablonu kao `apps/media_pipeline/utils.py`):
  ```python
  """Media pipeline PDF utilities — PDF MIME validacija + cover thumbnail generation.

  Story 2.4 (Epic 2) — proširenje Story 2.3 image pipeline foundation-a.
  Konzumiran od:
    - apps/media_pipeline/signals.py (post_save handler za ProductBrochure)
    - Story 8.6 admin ProductBrochureForm.clean_pdf_file() (per Story 2.3 AC5 pattern analog)

  Per project-context.md § Anti-pattern: File upload bez double-check —
  Django FileField validate file extension samo (`.pdf`), NE MIME signature.
  PDF MIME check kroz python-magic detect-uje `application/pdf` iz fajl signature
  (magic bytes `b"%PDF-"`).

  System dependency: poppler-utils (Dockerfile linija 42, verifikovano live) —
  pdf2image.convert_from_path() raise-uje PDFInfoNotInstalledError ako poppler
  nije instaliran. Razdvojeno od utils.py (image module) per Decision PDF-D1:
  separation of concerns + Story 8.6 može import-ovati validate_pdf_mime BEZ
  Pillow tranzitivnih sketch import-a.
  """

  from __future__ import annotations

  import logging
  from io import BytesIO
  from typing import Iterable

  import magic
  from django.core.exceptions import ValidationError
  from django.core.files.base import ContentFile
  from django.core.files.uploadedfile import UploadedFile
  from django.db.models.fields.files import FieldFile
  from django.utils.translation import gettext_lazy as _
  from PIL import Image
  from pdf2image import convert_from_bytes
  from pdf2image.exceptions import (
      PDFInfoNotInstalledError,
      PDFPageCountError,
      PDFPopplerTimeoutError,  # FIX iter-1 CRIT-4 — render timeout exception (pdf2image >= 1.17)
      PDFSyntaxError,
  )

  logger = logging.getLogger("apps.media_pipeline.pdf_utils")

  ALLOWED_PDF_MIME_TYPES: tuple[str, ...] = ("application/pdf",)
  MIME_SNIFF_BYTES: int = 2048
  # FIX iter-1 CRIT-1: smanjeno sa 50MB → 10MB radi sinhronizacije sa Story 2.3 MP-D8
  # (DATA_UPLOAD_MAX_MEMORY_SIZE = 11 MB, FILE_UPLOAD_MAX_MEMORY_SIZE = 10 MB). Bez ove
  # sinhronizacije, Django bi blokirao upload na 11MB PRE nego što validate_pdf_mime fires
  # (request body parsing fails u middleware → Editor vidi generic 413/500 umesto naše
  # locale-aware ValidationError poruke). Realan use case: product brochure PDF-ovi su
  # tipično 2-8 MB; 10 MB je dovoljan ceiling. Vidi Gotcha PDF-11 + Decision PDF-D8.
  MAX_PDF_UPLOAD_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB (sync sa MP-D8 FILE_UPLOAD limit)
  # FIX iter-1 CRIT-4: page count DoS guard — pdfinfo provera PRE render-a.
  MAX_PDF_PAGE_COUNT: int = 200  # vidi Gotcha PDF-11 + AC2
  # FIX iter-1 CRIT-4: pdf2image render timeout (poppler PDF-bomb / loop guard).
  PDF_RENDER_TIMEOUT_SECONDS: int = 15  # pdf2image >= 1.17 podržava timeout_seconds kwarg
  # FIX iter-1 CRIT-4: rendered page pixel ceiling (decompression bomb guard).
  # Pillow Image.MAX_IMAGE_PIXELS je globalno set u apps.media_pipeline (Story 2.3) na
  # 50_000_000, ali pdf2image bypass-uje Pillow load path; eksplicitna provera nužna.
  MAX_RENDERED_PIXELS: int = 50_000_000
  COVER_THUMBNAIL_SIZE: tuple[int, int] = (240, 320)  # AC2 — širina × visina (portrait orientation)
  COVER_THUMBNAIL_QUALITY: int = 85  # matches THUMBNAIL_QUALITY iz Story 2.3 settings
  COVER_THUMBNAIL_FORMAT: str = "JPEG"  # AC2 — JPG izlaz


  def validate_pdf_mime(
      upload: UploadedFile | None,
      *,
      allowed_mimes: Iterable[str] = ALLOWED_PDF_MIME_TYPES,
      max_size_bytes: int = MAX_PDF_UPLOAD_SIZE_BYTES,
  ) -> None:
      """Double-check da je upload validan PDF kroz MIME signature + size limit.

      Raise-uje ValidationError sa locale-aware porukom ako:
      - File je prazan (0 bytes) ili upload is None
      - File je veći od max_size_bytes (DoS guard; default 10MB sync sa MP-D8 — FIX iter-1 CRIT-1)
      - PDF ima više od MAX_PDF_PAGE_COUNT stranica (FIX iter-1 CRIT-4 — DoS guard)
      - python-magic detect-uje MIME koji NIJE u allowed_mimes

      Side-effect: upload.seek(0) na ulazu i izlazu (caller nije obavezan da reset-uje).

      Mirror Story 2.3 validate_image_mime() pattern — isti error message stil,
      isti seek-back discipline, isti gettext_lazy korišćenje.
      """
      if upload is None or not upload.size:
          raise ValidationError(_("PDF brošura je prazna ili nije priložena."))

      if upload.size > max_size_bytes:
          raise ValidationError(
              _("PDF brošura je veća od %(limit)d MB. Maksimalna dozvoljena veličina je %(limit)d MB.")
              % {"limit": max_size_bytes // (1024 * 1024)}
          )

      upload.seek(0)
      header = upload.read(MIME_SNIFF_BYTES)
      upload.seek(0)

      detected_mime = magic.from_buffer(header, mime=True)
      allowed_tuple = tuple(allowed_mimes)
      if detected_mime not in allowed_tuple:
          raise ValidationError(
              _("Nedozvoljen tip fajla: %(mime)s. Dozvoljen je samo PDF format.")
              % {"mime": detected_mime}
          )

      # FIX iter-1 CRIT-4 — DoS guard: page count provera PRE render-a.
      # pdfinfo_from_bytes je lightweight metadata read (ne render-uje content);
      # raise-uje istu listu poznatih poppler exception-a kao convert_from_bytes —
      # zato ih ovde TAKOĐE hvatamo (ako PDF struct je toliko corrupt da ni pdfinfo
      # ne radi, propustimo na generate_brochure_cover_thumbnail() koji će graceful
      # fail-ovati). Cilj ove provere je SAMO da odbije validan-strukturom-ali-prevelik PDF.
      try:
          from pdf2image import pdfinfo_from_bytes  # local import — testovi mogu mock-ovati
          upload.seek(0)
          info = pdfinfo_from_bytes(upload.read())
          upload.seek(0)
          page_count = int(info.get("Pages", 0))
          if page_count > MAX_PDF_PAGE_COUNT:
              raise ValidationError(
                  _("PDF brošura ima %(pages)d stranica. Maksimum je %(limit)d.")
                  % {"pages": page_count, "limit": MAX_PDF_PAGE_COUNT}
              )
      except ValidationError:
          raise
      except Exception:  # noqa: BLE001 — corrupt PDF metadata → defer to render-time graceful fail
          upload.seek(0)
          return
  ```
- **And** funkcija MORA koristiti `gettext_lazy as _` za sve `ValidationError` poruke (per project-context.md § gettext / i18n u kodu).
- **And** funkcija NIKAD ne raise-uje `magic.MagicException` direktno — `libmagic` SEGFAULT na Windows host-u rešava se kroz `just test` Docker recept (Story 2.3 MP-D6 SOT).
- **And** funkcija NE logu-je (no `logger.warning()` u ovom helper-u — caller form/signal decide-uje kako da reaguje; jedini logging u `pdf_utils.py` je iz `generate_brochure_cover_thumbnail()` koji ima sopstvenu graceful failure logiku per AC4).
- **And** **`MAX_PDF_UPLOAD_SIZE_BYTES = 10 MB`** je IZJEDNAČEN sa image limit-om iz Story 2.3 (10 MB) i sa `FILE_UPLOAD_MAX_MEMORY_SIZE` iz Story 2.3 MP-D8 (per FIX iter-1 CRIT-1). Realan use case: product brochure PDF-ovi su tipično 2-8 MB; 10 MB je dovoljan ceiling. **Ako bi se postavilo veće (npr. 50 MB)** Django `DATA_UPLOAD_MAX_MEMORY_SIZE = 11 MB` bi blokirao request u middleware-u PRE nego što `validate_pdf_mime` fires → Editor bi video generic 413/500 umesto naše locale-aware ValidationError poruke. **NEMA Story 9.x Nginx promene potrebne** — `client_max_body_size 12M` ili sličan (vidi Story 2.3 MP-D8 cross-reference) već pokriva 10 MB ceiling. **DoS guard layering** (per FIX iter-1 CRIT-4): size limit (ovaj AC) → page count limit (`MAX_PDF_PAGE_COUNT = 200`) → render timeout (`PDF_RENDER_TIMEOUT_SECONDS = 15`) → rendered pixel ceiling (`MAX_RENDERED_PIXELS = 50_000_000`). Vidi Gotcha PDF-11.

**AC2 — `apps/media_pipeline/pdf_utils.py` sadrži `generate_brochure_cover_thumbnail(pdf_field) -> ContentFile | None` koja koristi pdf2image da rendera prvu stranu PDF-a u 240×320 JPG**

- **Given** AC1 završen (`pdf_utils.py` postoji sa `validate_pdf_mime()`)
- **When** dodajem `generate_brochure_cover_thumbnail()` u isti fajl
- **Then** funkcija mora imati TAČNO sledeću signaturu i ponašanje:
  ```python
  def generate_brochure_cover_thumbnail(pdf_field: FieldFile) -> ContentFile | None:
      """Render-uje prvu stranu PDF-a kao 240×320 JPG ContentFile (in-memory).

      Args:
          pdf_field: ProductBrochure.pdf_file FieldFile (Django ImageField/FileField proxy)

      Returns:
          ContentFile sa JPEG bytes-ima (ime "brochure-cover.jpg") spreman za save na
          ProductBrochure.cover_thumbnail_image polje. Ako je PDF korumpiran ili nema
          validnu prvu stranu, vraća `None` (caller signal handler interpretira `None` kao
          graceful failure → loguje warning + skip save).

      Used by: apps/media_pipeline/signals.py handle_brochure_post_save() (AC3-AC5).

      NEVER raises — sve exception-e (PDFInfoNotInstalledError, PDFPageCountError,
      PDFPopplerTimeoutError, PDFSyntaxError, OSError, ValueError, generic Exception)
      hvata i loguje kroz logger.warning(). Garantuje da signal handler ne pukne admin
      save flow.

      FIX iter-1 CRIT-4 DoS guards:
      - timeout=PDF_RENDER_TIMEOUT_SECONDS (15s) → PDFPopplerTimeoutError @ render time
      - rendered_pixels > MAX_RENDERED_PIXELS (50M) → graceful None return
      FIX iter-1 CRIT-8: enkriptovan PDF triggeruje PDFSyntaxError (poppler ne može da
      otvori bez password-a) → graceful None.
      """
      if not pdf_field or not getattr(pdf_field, "name", ""):
          return None

      try:
          # Read PDF kao bytes — pdf2image.convert_from_bytes je sigurnije od
          # convert_from_path (ne mora znati apsolutni storage path; Django Storage
          # API može biti S3 ili Whitenoise-served).
          pdf_field.open("rb")
          try:
              pdf_bytes = pdf_field.read()
          finally:
              pdf_field.close()

          # Render samo prvu stranu — dpi=100 (balans kvalitet/brzina; 240×320 thumbnail
          # ne treba viši dpi); fmt="jpeg" je default ali eksplicitno za čitljivost; size
          # parametar ovde NIJE pixel size već "scale to fit within" — radije resize-ujemo
          # ručno kroz Pillow posle.
          # FIX iter-1 CRIT-4: timeout_seconds kwarg (pdf2image >= 1.17) hvata poppler
          # render loop bug-ove / PDF bombs. PDFPopplerTimeoutError je hvaćen niže.
          images = convert_from_bytes(
              pdf_bytes,
              first_page=1,
              last_page=1,
              fmt="jpeg",
              dpi=100,
              timeout=PDF_RENDER_TIMEOUT_SECONDS,
          )
          if not images:
              logger.warning(
                  "Brochure cover render: convert_from_bytes returned empty list (PDF has 0 pages?). "
                  "Brochure ID: %s",
                  getattr(pdf_field.instance, "id", "unknown"),
              )
              return None

          page_image = images[0]

          # FIX iter-1 CRIT-4: decompression bomb guard — pdf2image bypass-uje Pillow
          # load path pa eksplicitna pixel provera nužna. Poppler može render-ovati
          # PDF page sa MediaBox 50000×50000 pri dpi=100 = 5_000_000_000 px → OOM.
          rendered_pixels = page_image.width * page_image.height
          if rendered_pixels > MAX_RENDERED_PIXELS:
              logger.warning(
                  "Brochure cover render: rendered page too large (%d px > %d). "
                  "Brochure ID: %s",
                  rendered_pixels,
                  MAX_RENDERED_PIXELS,
                  getattr(pdf_field.instance, "id", "unknown"),
              )
              return None

          # Pillow resize sa LANCZOS — high-quality downsampling za 240×320 thumbnail
          # Force RGB mode — JPEG ne podržava RGBA/P modes (raise OSError pri save)
          if page_image.mode != "RGB":
              page_image = page_image.convert("RGB")
          page_image.thumbnail(COVER_THUMBNAIL_SIZE, Image.Resampling.LANCZOS)

          buffer = BytesIO()
          page_image.save(buffer, format=COVER_THUMBNAIL_FORMAT, quality=COVER_THUMBNAIL_QUALITY)
          buffer.seek(0)
          return ContentFile(buffer.read(), name="brochure-cover.jpg")

      except (
          PDFInfoNotInstalledError,
          PDFPageCountError,
          PDFPopplerTimeoutError,  # FIX iter-1 CRIT-4 — render timeout
          PDFSyntaxError,           # PDF/Encrypt + corrupt PDF + invalid struct
          OSError,
          ValueError,
      ) as exc:
          logger.warning(
              "Brochure cover render failed (recoverable). Brochure ID: %s. Error: %s",
              getattr(pdf_field.instance, "id", "unknown"),
              exc,
          )
          return None
      except Exception as exc:  # noqa: BLE001 — broad except is intentional, see docstring
          # Defensive catch-all — signal handler NIKAD ne sme pucati admin save flow.
          # Logujemo SVE neočekivane exception-e kao error (ne warning) da Mihas u
          # GlitchTip vidi unexpected failure modes; signal i dalje return-uje None.
          logger.error(
              "Brochure cover render: unexpected exception. Brochure ID: %s. Error: %s",
              getattr(pdf_field.instance, "id", "unknown"),
              exc,
              exc_info=True,
          )
          return None
  ```
- **And** funkcija MORA biti **non-raising** — sve poznate exception-e (`PDFInfoNotInstalledError`, `PDFPageCountError`, `PDFPopplerTimeoutError`, `PDFSyntaxError`, `OSError`, `ValueError`) hvata `except` blokom; nepoznate hvata `except Exception` blokom. Garantuje da signal handler NIKAD ne pucu admin save flow (vidi Gotcha PDF-4 + Gotcha PDF-11).
- **And** **DoS guards (FIX iter-1 CRIT-4):** `timeout=PDF_RENDER_TIMEOUT_SECONDS` kwarg u `convert_from_bytes` poziva (pdf2image >= 1.17.0); eksplicitan `rendered_pixels > MAX_RENDERED_PIXELS` provera posle render-a (decompression bomb guard, pošto pdf2image bypass-uje Pillow `MAX_IMAGE_PIXELS`).
- **And** **enkriptovan PDF (FIX iter-1 CRIT-8):** poppler raise-uje `PDFSyntaxError` kad PDF ima `/Encrypt` dictionary bez password-a → handler graceful return `None` + log warning. Editor vidi save uspeo, cover prazno; Story 8.6 admin može dodati form-level validation poruku kasnije (out-of-scope za 2.4).
- **And** generisan ContentFile MORA imati ime `"brochure-cover.jpg"` (per epics.md AC line 579: "Generated thumbnail je u `media/products/<slug>/brochure-cover.jpg`") — Story 2.2 model definicija (`upload_to="products/brochure_covers/"`) određuje stvarni storage path; ime fajla je samo bazno ime koje Django Storage API koristi pri save-u. **NAPOMENA:** epics.md putanja `media/products/<slug>/brochure-cover.jpg` se RAZLIKUJE od Story 2.2 model `upload_to="products/brochure_covers/"` — Story 2.4 prati Story 2.2 model decision (`upload_to` je već lock-ovan u migraciji; menjati ga bi zahtevalo novu migraciju što je out-of-scope). Vidi Gotcha PDF-6 za rationale.
- **And** Pillow `Image.Resampling.LANCZOS` (Pillow 9.1+; verifikuj `pillow` tranzitivna verzija iz sorl-thumbnail dep-a kroz `uv tree | grep -i pillow` smoke check — sorl-thumbnail 13.0 zahteva Pillow 10.0+ koji ima `LANCZOS`).
- **And** `page_image.thumbnail((240, 320), LANCZOS)` koristi **maintain aspect ratio** semantiku (Pillow `thumbnail()` metod) — ako je PDF stranica A4 portrait (~595×842), rezultat je ~226×320 (ne 240×320 strogo); to je acceptable jer card layout u Story 2.7 koristi `max-width: 240px` (vidi Decision PDF-D3 za rationale aspect-ratio vs strict-resize).
- **And** funkcija MORA force-ovati `RGB` mode pre JPEG save-a (PDF stranice mogu biti rendered kao RGBA/P modes; libjpeg raise-uje `OSError: cannot write mode RGBA as JPEG`).

**AC3 — `apps/media_pipeline/signals.py` sadrži `handle_brochure_post_save` `post_save` handler za `ProductBrochure` koji koristi kasnu resoluciju kroz `apps.get_model()` + `transaction.on_commit` deferred save (FIX iter-1 CRIT-3 + CRIT-5)**

- **Given** AC1 + AC2 završeni (`pdf_utils.py` postoji); Story 2.3 AC8 boundary testovi (`test_media_pipeline_does_not_import_products`) registrovani u `tests/integration/test_app_boundaries.py` linija 130-163
- **When** kreiram `apps/media_pipeline/signals.py`
- **Then** fajl mora imati TAČNO sledeću strukturu:
  ```python
  """Media pipeline signals — automatska post-save logika za media polja.

  Story 2.4 (Epic 2) — prvi signal handler u media_pipeline app-u.
  Wire-uje se kroz apps/media_pipeline/apps.py.ready() (per Django best practice).

  KRITIČNO (Story 2.3 AC8 boundary regression):
    apps.media_pipeline NE SME importovati apps.products direktno.
    `tests/integration/test_app_boundaries.py` enforces ovo kroz AST static check.
    Posledica: signal handler koristi `apps.get_model("products", "ProductBrochure")`
    kasnu resoluciju, NE `from apps.products.models import ProductBrochure`.
    Sender connection takođe ide kroz `apps.get_model()` u ready() hook-u.

  FIX iter-1 CRIT-3 — Replace-PDF UX (idempotency rationale revisited):
    Handler regeneriše cover SVAKI put kad se pdf_file menja. NE skip-uje ako
    `cover_thumbnail_image already exists` (stara verzija je hidirala bug gde
    Editor zameni pdf_file ali cover ostane stale). Detection: ako je
    `update_fields == None` (create + full save) ILI `pdf_file in update_fields`,
    regeneriše. Sa MULTI-LAYER infinite loop guard:
    - Layer A: skip ako update_fields == {"cover_thumbnail_image"} (interni save)
    - Layer B: instance.save(update_fields=["cover_thumbnail_image"]) sa save=False
      na storage.save() poziv (Storage write ne triggeruje signal)

  FIX iter-1 CRIT-5 — Transaction safety:
    ImageField.save() piše na disk PRE commit-a outer transakcije. Ako outer save
    rollback-uje (npr. drugi pre_save signal raise-uje ValidationError nakon ovog
    handler-a), file ostaje orphan na disku. Rešenje: render + storage save unutar
    `transaction.on_commit()` callback-a — izvršava se SAMO ako outer transakcija
    uspešno commit-uje.
  """

  from __future__ import annotations

  import logging
  from typing import Any

  from django.db import transaction
  from django.db.models.signals import post_save

  from apps.media_pipeline.pdf_utils import generate_brochure_cover_thumbnail

  logger = logging.getLogger("apps.media_pipeline.signals")


  def handle_brochure_post_save(
      sender: Any,
      instance: Any,
      created: bool,
      raw: bool,
      update_fields: frozenset[str] | None,
      **kwargs: Any,
  ) -> None:
      """post_save handler za ProductBrochure — auto-populiše cover_thumbnail_image.

      Wire-uje se eksplicitno u apps/media_pipeline/apps.py.ready() kroz
      `post_save.connect(handle_brochure_post_save, sender=ProductBrochure, ...)`.

      Skip conditions (return early):
      - `raw=True` (loaddata fixtures — Django ne triggeruje user save flow)
      - `update_fields == {"cover_thumbnail_image"}` (interni save iz ovog handler-a — infinite loop guard, layer A)
      - `instance.pdf_file` je prazan (brochure bez PDF-a — nema šta da render-uje)

      FIX iter-1 CRIT-3: NIJE više skip ako cover_thumbnail_image već postoji —
      Editor MORA moći da zameni pdf_file i cover se MORA regenerisati (stara
      verzija je propustila bug gde stale cover ostaje na zameni PDF-a).
      Re-generation trigger: update_fields IS None (full create/save) ili
      "pdf_file" in update_fields. Multi-field saves bez pdf_file (npr. samo
      title update) NE regenerišu cover.

      FIX iter-1 CRIT-5: stvarni render + storage save izvršavaju se u
      transaction.on_commit() callback-u → orphan-file safety pri rollback-u.

      Failure modes: NIKAD ne raise-uje. generate_brochure_cover_thumbnail() je
      non-raising po contract-u (AC2); ako vrati `None`, callback logu-je warning.
      """
      if raw:
          # Fixture loading (loaddata) — preskoči signal logiku
          return

      # Layer A — infinite loop guard: interni save iz ovog handler-a
      if (
          update_fields is not None
          and "cover_thumbnail_image" in update_fields
          and len(update_fields) == 1
      ):
          return

      # Defensive guard — pdf_file required po model-u ali AC6 test 3 dokumentuje rationale
      if not instance.pdf_file or not getattr(instance.pdf_file, "name", ""):
          return

      # FIX iter-1 CRIT-3: regeneration trigger detection.
      # update_fields=None → Django save() bez eksplicitnog update_fields → full save
      # (create ili save() bez argumenta). U tom slučaju, regeneriši.
      # update_fields={"pdf_file", ...} → Editor je menjao PDF — regeneriši.
      # update_fields={"title"} ili sl. bez pdf_file → NE regeneriši (nepotrebno).
      pdf_file_touched = update_fields is None or "pdf_file" in update_fields
      if not pdf_file_touched:
          return

      # FIX iter-1 CRIT-5: defer render + storage save u on_commit callback —
      # ako outer transakcija rollback-uje (drugi pre_save raise-uje), callback se
      # NIKAD ne poziva → nema orphan fajla na disku.
      def _generate_cover_on_commit() -> None:
          cover_file = generate_brochure_cover_thumbnail(instance.pdf_file)
          if cover_file is None:
              # Graceful failure — pdf_utils.py je već logovao warning sa kontekstom.
              # Brochure ostaje sa praznim cover_thumbnail_image; Story 2.7 template
              # ima fallback (generic PDF icon).
              return

          # save=False → Storage piše fajl ali NE poziva instance.save() (no signal).
          instance.cover_thumbnail_image.save(cover_file.name, cover_file, save=False)
          # Layer A guard će skip-ovati ovaj save (single-field update_fields).
          instance.save(update_fields=["cover_thumbnail_image"])
          logger.info(
              "Brochure cover generated successfully. Brochure ID: %s. Product slug: %s.",
              instance.id,
              getattr(instance.product, "slug", "unknown"),
          )

      transaction.on_commit(_generate_cover_on_commit)
  ```
- **And** funkcija NE koristi `@receiver` dekorator — wiring se radi eksplicitno u `apps/media_pipeline/apps.py.ready()` kroz `post_save.connect(handle_brochure_post_save, sender=...)` (per Decision PDF-D6 — eksplicitno wiring je bolje za testabilnost i debuggability nego decorator magic).
- **And** funkcija NE import-uje `from apps.products.models import ProductBrochure` (AC9 boundary regression compliance) — `sender` parameter se rešava u ready() hook-u kroz `apps.get_model("products", "ProductBrochure")`.
- **And** **`update_fields` infinite loop guard semantika:** handler skip-uje SAMO ako `update_fields == frozenset({"cover_thumbnail_image"})` (single-field internal save). FIX iter-1 CRIT-3: NEMA više `cover_thumbnail_image already exists` skip → svaki put kad pdf_file menja, regeneriše. Multi-layer infinite loop guard: (Layer A) handler skip ako update_fields == {"cover_thumbnail_image"}; (Layer B) `instance.cover_thumbnail_image.save(name, content, save=False)` ne triggeruje post_save signal pri Storage-level write-u.
- **And** **Regeneration trigger logic (FIX iter-1 CRIT-3):** `pdf_file_touched = update_fields is None or "pdf_file" in update_fields`. Ako je `pdf_file_touched=False` (npr. Editor menja samo `title`), handler return-uje bez render-a (performance optimization). Ako je `True` (create ILI eksplicit PDF zamena), regeneriše — Editor zamena PDF-a uvek dobija svež cover, nikad stale.
- **And** **Transaction safety (FIX iter-1 CRIT-5):** stvarni render + `instance.cover_thumbnail_image.save(...)` + `instance.save(update_fields=...)` izvršavaju se UNUTAR `transaction.on_commit(_generate_cover_on_commit)` callback-a. Ako outer transakcija (npr. admin save flow sa drugim pre_save signal-om koji raise-uje ValidationError) rollback-uje, callback se NIKAD ne poziva → nema orphan JPG fajla na disku. Pri uspešnom commit-u, callback se izvršava NEPOSREDNO posle commit-a (sync), tako da Editor vidi cover u istom request-response ciklusu (npr. admin redirect na list_display posle save-a).
- **And** `raw=True` skip uslov pokriva `loaddata` fixture importe — Django šalje `raw=True` kad loada-uje data iz JSON fixture-a (admin export/import workflow), signal ne treba da render-uje cover za sve brochure-e u fixture-u (ozbiljan performance hit).
- **And** logging level conventions: **`logger.info`** za uspeh (admin može pratiti aktivnost), **`logger.warning`** za graceful failure (PDF nevalidan ali save uspeo — Editor treba da vidi), **`logger.error`** za neočekivane exception-e (GlitchTip alert worthy).

**AC4 — `apps/media_pipeline/apps.py.ready()` hook wire-uje signal kroz `post_save.connect(handle_brochure_post_save, sender=ProductBrochure)`**

- **Given** AC3 završen (`signals.py` postoji sa `handle_brochure_post_save`); Story 2.3 `apps/media_pipeline/apps.py` postoji sa `MediaPipelineConfig` ali BEZ `ready()` hook-a (live linija 1-19 verifikovano)
- **When** modifikujem `apps/media_pipeline/apps.py`
- **Then** fajl mora imati TAČNO sledeću proširenu strukturu (zadržava Story 2.3 docstring + class skeleton, dodaje `ready()` metodu):
  ```python
  """AppConfig za apps.media_pipeline — image + PDF utility (cross-cutting).

  Story 2.3 (Epic 2) — utility app bez modela. Konzumiran od domain app-ova
  (brands, products, blog) kroz template tagove i helper-e.
  Jednosmerna zavisnost: media_pipeline NE SME uvoziti apps.products / apps.brands.

  Story 2.4 (Epic 2) — DODATO: ready() hook wire-uje post_save signal za
  ProductBrochure (auto-generation cover_thumbnail_image kroz pdf2image).
  Sender se resolviše kasnu kroz apps.get_model("products", "ProductBrochure")
  da očuva Story 2.3 AC8 boundary rule (no `apps.products` import u media_pipeline).
  """

  from django.apps import AppConfig
  from django.db.models.signals import post_save
  from django.utils.translation import gettext_lazy as _


  class MediaPipelineConfig(AppConfig):
      default_auto_field = "django.db.models.BigAutoField"
      name = "apps.media_pipeline"
      verbose_name = _("Media pipeline")

      def ready(self) -> None:
          """Wire post_save signal za ProductBrochure cover thumbnail generator.

          Mora biti import-ovan unutar ready() (NE module-level) jer:
          (a) apps.products još nije loaded pri Django startup-u kad se ovaj fajl
              importuje (INSTALLED_APPS resolve order — modeltranslation prvi, pa
              apps loop-uje kroz registar, media_pipeline je posle apps.products
              ali ready() je guaranteed posle svih AppConfig.import_models()).
          (b) signals.py import-uje pdf_utils.py koji import-uje pdf2image — testovi
              koji ne diraju signals (npr. apps.brands smoke testovi) ne treba da
              učitavaju pdf2image / poppler.
          (c) apps.get_model() je kasna resolucija — ne krši AST boundary check
              jer string-based "products.ProductBrochure" reference NIJE statički import.
          """
          from django.apps import apps

          from apps.media_pipeline.signals import handle_brochure_post_save

          product_brochure_model = apps.get_model("products", "ProductBrochure")
          post_save.connect(
              handle_brochure_post_save,
              sender=product_brochure_model,
              dispatch_uid="apps.media_pipeline.signals.handle_brochure_post_save",
          )
  ```
- **And** `ready()` import-uje `signals` module **UNUTAR metode**, NE na module level (per Django docs § Connecting signals — sender models mogu biti unloaded pri AppConfig.py import vremenu; `ready()` je guaranteed pozvan posle svih `AppConfig.import_models()`).
- **And** `dispatch_uid="apps.media_pipeline.signals.handle_brochure_post_save"` (Django signal best practice) — sprečava double-connect ako se `ready()` slučajno pozove dva puta (npr. testovi sa `pytest-django` koji reload-uju app config).
- **And** **Story 2.3 docstring + class skeleton SU OČUVANI** — Edit operacija dodaje SAMO `ready()` metodu i 2 nova import-a (`post_save` iz `django.db.models.signals`); NE rewrite-uje ceo fajl (mirror Story 2.3 AC1 strict-Edit pattern).
- **And** smoke verifikacija: `docker compose -f compose/local.yml run --rm django uv run python manage.py check` — exit code 0; nema warning-a o duplicate signal connections.

**AC5 — Upload PDF brošure kroz admin (ProductBrochure save) automatski populiše `cover_thumbnail_image` polje sa 240×320 JPG generisanim iz prve strane PDF-a**

- **Given** AC1-AC4 završeni (PDF utils + signals + ready hook); validan PDF brošura fajl sa minimum 1 stranicom
- **When** TEA (Step 3) piše integration test:
  ```python
  # IMP iter-1 IMP-2: transaction=True nužno jer FIX iter-1 CRIT-5 deferred render
  # u transaction.on_commit() — sa default @pytest.mark.django_db (transaction=False),
  # on_commit callback se NE poziva (django-pytest wraps test u savepoint koji NIKAD
  # commit-uje). transaction=True koristi real DB transactions → callback se izvršava.
  @pytest.mark.django_db(transaction=True)
  def test_post_save_generates_cover_thumbnail(realistic_pdf_bytes, temp_media_root, brand, subcategory):
      product = Product.objects.create(
          name="Test traktor",
          brand=brand,
          subcategory=subcategory,
      )
      pdf_upload = SimpleUploadedFile(
          "katalog.pdf",
          realistic_pdf_bytes,
          content_type="application/pdf",
      )
      brochure = ProductBrochure.objects.create(
          product=product,
          pdf_file=pdf_upload,
          title="Tehnička specifikacija",
      )
      # Refresh from DB — signal je sync save, ali bezbedno
      brochure.refresh_from_db()
      assert brochure.cover_thumbnail_image
      assert brochure.cover_thumbnail_image.name.endswith(".jpg")
      # Otvori sliku i proveri dimenzije (240 ili manje × 320 ili manje — aspect ratio preserved)
      with Image.open(brochure.cover_thumbnail_image.path) as img:
          assert img.width <= 240
          assert img.height <= 320
          assert img.format == "JPEG"
          assert img.mode == "RGB"
  ```
- **Then** test mora proći (GREEN phase posle Dev implementacije):
  - `brochure.cover_thumbnail_image` je truthy (polje populated)
  - Fajl ekstenzija je `.jpg`
  - Pillow `Image.open()` na fajl vrača validnu JPEG image-u sa dimenzijama ≤ 240×320 (aspect ratio preserved per Decision PDF-D3)
  - `img.mode == "RGB"` (force-RGB konverzija per AC2)
- **And** test koristi `realistic_pdf_bytes` fixture iz `apps/media_pipeline/tests/conftest.py` (TEA scope u Step 3 — generisan kroz minimal PDF struct ILI static fixture per Decision PDF-D5; SM NIJE deliverable fixture kod).
- **And** test koristi `temp_media_root` fixture iz Story 2.3 conftest-a (re-use; monkeypatch MEDIA_ROOT na pytest tmp_path).
- **And** test radi kroz Docker (`just test apps/media_pipeline/tests/test_signals.py`) — poppler-utils sistemska dep nije dostupna na Windows host-u, isti razlog kao libmagic u Story 2.3 MP-D6.

**AC6 — Korumpiran ili invalid PDF (npr. EXE preimenovan u .pdf, 0-byte fajl, PDF bez stranica) save-uje brochure sa praznim `cover_thumbnail_image` polje + Python logger.warning() poziv**

- **Given** AC1-AC5 završeni; korumpiran "PDF" bytes (npr. `b"NOT_A_PDF"` ili truncated PDF header)
- **When** TEA piše tri scenarija graceful failure-a:
  1. **PDF sa 0 stranica (empty PDF — magic bytes valid ali no pages):**
     ```python
     def test_post_save_graceful_failure_empty_pdf(empty_pdf_bytes, caplog, temp_media_root, brand, subcategory):
         # empty_pdf_bytes je minimalan PDF struct sa 0 stranica
         brochure = ProductBrochure.objects.create(
             product=product,
             pdf_file=SimpleUploadedFile("empty.pdf", empty_pdf_bytes),
         )
         brochure.refresh_from_db()
         assert not brochure.cover_thumbnail_image  # polje ostaje prazno
         assert any("Brochure cover render" in rec.message for rec in caplog.records)
         assert any(rec.levelname == "WARNING" for rec in caplog.records)
     ```
  2. **Random bytes pretvarajući se da je PDF:**
     ```python
     def test_post_save_graceful_failure_corrupt_pdf(caplog, temp_media_root, brand, subcategory):
         brochure = ProductBrochure.objects.create(
             product=product,
             pdf_file=SimpleUploadedFile("corrupt.pdf", b"NOT_A_PDF_AT_ALL"),
         )
         brochure.refresh_from_db()
         assert not brochure.cover_thumbnail_image
         # caplog hvata WARNING — graceful failure
     ```
  3. **Handler skip ako instance.pdf_file je None (FIX iter-1 CRIT-7 — unit test, NE integration):**
     ```python
     def test_handler_skips_when_no_pdf_file(mocker):
         """Defensive guard test — handler MORA tolerisati instance.pdf_file=None.

         FIX iter-1 CRIT-7: prethodna verzija (integration test sa
         ProductBrochure.objects.create(pdf_file=None)) je BILA NEMOGUĆE — model je
         FileField BEZ blank=True (vidi apps/products/models.py linija 425-429).
         Rewritten kao pure unit test: pozivamo handler direktno sa MagicMock instance,
         spy-ujemo generate_brochure_cover_thumbnail i verifikujemo skip semantiku.

         Boundary handler semantika OPRAVDANA: shell skript ili future migration može
         pozvati .objects.create() kroz raw SQL ili bulk_create() bypass; defensive
         guard štiti od edge case-a kad model evoluira (npr. blank=True doda).
         """
         from unittest.mock import MagicMock

         from apps.media_pipeline.signals import handle_brochure_post_save
         from apps.products.models import ProductBrochure

         instance = MagicMock(spec=ProductBrochure)
         instance.pdf_file = None
         instance.cover_thumbnail_image = MagicMock()
         instance.cover_thumbnail_image.name = ""

         generate_spy = mocker.patch(
             "apps.media_pipeline.signals.generate_brochure_cover_thumbnail"
         )
         on_commit_spy = mocker.patch("apps.media_pipeline.signals.transaction.on_commit")

         handle_brochure_post_save(
             sender=ProductBrochure,
             instance=instance,
             created=True,
             raw=False,
             update_fields=None,
         )

         # Handler MORA skip-ovati PRE transaction.on_commit poziva → spy ne pozvan.
         assert generate_spy.call_count == 0
         assert on_commit_spy.call_count == 0
     ```
- **Then** sva tri testa moraju proći:
  - `brochure.cover_thumbnail_image` ostaje prazno (`not brochure.cover_thumbnail_image == True`)
  - Brochure save uspeo (record postoji u DB-u; `brochure.id` truthy)
  - Python `logging` capture (kroz pytest `caplog` fixture) hvata `WARNING` ili `INFO` log entry koji sadrži ID brošure + context o uzroku failure-a
  - NIKAKAV `Exception` ne propagira do test runtime-a (`pytest.raises` ne treba — sigurnosno!)
- **And** caplog assertion testira da je log message **NA SRPSKOM ENGLESKOM** (logger messages NISU lokalizovane per project-context.md § gettext / i18n u kodu — log entries su za dev/sysadmin, ne user-facing).

**AC7 — Signal NE re-trigger-uje sebe pri internom save-u (`update_fields={"cover_thumbnail_image"}`) — infinite loop guard + replace-PDF regen (FIX iter-1 CRIT-3)**

- **Given** AC3 + AC4 završeni
- **When** TEA piše test koji posmatra broj signal poziva:
  ```python
  def test_signal_does_not_loop_on_internal_save(realistic_pdf_bytes, temp_media_root, brand, subcategory, mocker):
      # Spy na generate_brochure_cover_thumbnail iz signals (gde se importuje, ne pdf_utils direktno)
      spy = mocker.spy(signals, "generate_brochure_cover_thumbnail")
      brochure = ProductBrochure.objects.create(
          product=product,
          pdf_file=SimpleUploadedFile("test.pdf", realistic_pdf_bytes),
      )
      # Posle initial create, signal je pozvao generate_brochure_cover_thumbnail TAČNO JEDNOM
      assert spy.call_count == 1
      # Manual update samo title polja → pdf_file_touched=False → handler skip-uje render
      brochure.title = "Updated title"
      brochure.save(update_fields=["title"])
      # Signal NIJE pozvao render ponovo (FIX iter-1 CRIT-3: pdf_file nije u update_fields)
      assert spy.call_count == 1
  ```
- **And** **NOVI test (FIX iter-1 CRIT-3) — replace pdf_file regeneriše cover:**
  ```python
  def test_post_save_regenerates_cover_when_pdf_replaced(
      realistic_pdf_bytes, temp_media_root, brand, subcategory, mocker
  ):
      """FIX iter-1 CRIT-3: Editor menja pdf_file → cover MORA biti regeneration.

      Stara verzija handler-a je imala `if instance.cover_thumbnail_image: return`
      guard koji je hidirao bug — cover bi ostao stale (slika prve strane STAROG
      PDF-a) nakon zamene fajla. AC3 sada zahteva regeneration na svaku PDF promenu.
      """
      spy = mocker.spy(signals, "generate_brochure_cover_thumbnail")

      # Initial create
      brochure = ProductBrochure.objects.create(
          product=product,
          pdf_file=SimpleUploadedFile("v1.pdf", realistic_pdf_bytes),
      )
      assert spy.call_count == 1
      first_cover_name = brochure.cover_thumbnail_image.name

      # Editor menja pdf_file
      brochure.pdf_file = SimpleUploadedFile("v2.pdf", realistic_pdf_bytes)
      brochure.save(update_fields=["pdf_file"])

      # Handler MORA regenerisati cover (pdf_file in update_fields)
      assert spy.call_count == 2
      brochure.refresh_from_db()
      assert brochure.cover_thumbnail_image  # truthy
      # NOTE: name može biti različit (storage append-uje hash suffix) — assert na
      # truthiness + spy count je dovoljan dokaz regeneration-a.
  ```
- **And** **NOVI test (FIX iter-1 CRIT-5) — on_commit callback registration:**
  ```python
  def test_post_save_uses_on_commit_callback(mocker):
      """FIX iter-1 CRIT-5: render + storage save MORAJU biti deferred kroz
      transaction.on_commit. Test verifikuje da handler registruje callback,
      NIJE da ga sinhrono izvršava."""
      from unittest.mock import MagicMock
      from apps.media_pipeline.signals import handle_brochure_post_save
      from apps.products.models import ProductBrochure

      instance = MagicMock(spec=ProductBrochure)
      instance.pdf_file = MagicMock()
      instance.pdf_file.name = "products/brochures/x.pdf"
      instance.cover_thumbnail_image = MagicMock()
      instance.cover_thumbnail_image.name = ""

      on_commit_spy = mocker.patch("apps.media_pipeline.signals.transaction.on_commit")
      generate_spy = mocker.patch(
          "apps.media_pipeline.signals.generate_brochure_cover_thumbnail"
      )

      handle_brochure_post_save(
          sender=ProductBrochure,
          instance=instance,
          created=True,
          raw=False,
          update_fields=None,
      )

      # Callback je registrovan ali NIJE izvršen (mock ga ne poziva).
      assert on_commit_spy.call_count == 1
      # Render NIJE pozvan direktno iz handler-a — samo iz unutar callback-a.
      assert generate_spy.call_count == 0
  ```
- **Then** test mora proći:
  - Prvi `objects.create()` triggeruje 1 poziv `generate_brochure_cover_thumbnail()`
  - Drugi `save(update_fields=["title"])` ne triggeruje render (`pdf_file` nije touched)
  - Replace pdf_file save triggeruje 1 dodatni render (FIX iter-1 CRIT-3 enforcement)
  - Test NIKAD ne dobija beskonačnu petlju (timeout ili RecursionError)
- **And** mocker je iz `pytest-mock` library — **dodaje se kao dev dep u Task 0** (vidi FIX iter-1 CRIT-2).

**AC8 — Postojeći media_pipeline testovi iz Story 2.3 baseline-a + tests/integration/test_app_boundaries.py + apps.brands/apps.products testovi ostaju zeleni; novi Story 2.4 testovi prolaze**

- **Given** Sve prethodne testove (2.1 + 2.2 + 2.3) PASS-uju pre Story 2.4. **IMP iter-1 IMP-3:** baseline broj testova NIJE hardkodovan — uzima se iz `_bmad-output/sprint-status.yaml` (Story 2.3 unos `tests_passed:` polje). Posle Story 2.4, broj testova RASTE; AC8 zahteva da BASELINE ostane green + NOVI testovi GREEN, NE da total broj bude fiksni.
- **When** `just test` (Docker-backed `uv run pytest`) pokrenut posle Story 2.4 implementacije
- **Then** sve postojeće testove (`apps/brands/tests/`, `apps/products/tests/`, `apps/media_pipeline/tests/test_apps.py`, `test_utils.py`, `test_templatetags.py`, `test_thumbnails.py`, `test_settings.py`, `tests/integration/test_app_boundaries.py`) MORAJU biti GREEN
- **And** novi `apps/media_pipeline/tests/test_pdf_utils.py` (TEA Step 3 deliverable) MORA biti green:
  - `test_validate_pdf_mime_accepts_valid_pdf`
  - `test_validate_pdf_mime_rejects_image_as_pdf` (PDF MIME signature mismatch)
  - `test_validate_pdf_mime_rejects_empty_upload`
  - `test_validate_pdf_mime_rejects_none_upload`
  - `test_validate_pdf_mime_rejects_oversize_upload` (>10 MB) — FIX iter-1 CRIT-1 (granica spuštena)
  - `test_validate_pdf_rejects_high_page_count` — FIX iter-1 CRIT-4 (>200 stranica)
  - `test_generate_brochure_cover_thumbnail_returns_content_file_for_valid_pdf`
  - `test_generate_brochure_cover_thumbnail_returns_none_for_corrupt_pdf`
  - `test_generate_brochure_cover_thumbnail_returns_none_for_empty_field`
  - `test_generate_brochure_cover_thumbnail_returns_none_for_encrypted_pdf` — FIX iter-1 CRIT-8
  - `test_generate_returns_none_on_render_timeout` — FIX iter-1 CRIT-4 (mock pdf2image → PDFPopplerTimeoutError)
  - `test_generate_returns_none_on_decompression_bomb` — FIX iter-1 CRIT-4 (mock convert_from_bytes → 50001×50001 PIL Image)
  - `test_generate_brochure_cover_thumbnail_force_rgb_mode_for_jpeg_save`
- **And** novi `apps/media_pipeline/tests/test_signals.py` (TEA Step 3 deliverable) MORA biti green:
  - `test_post_save_generates_cover_thumbnail` (AC5)
  - `test_post_save_graceful_failure_empty_pdf` (AC6)
  - `test_post_save_graceful_failure_corrupt_pdf` (AC6)
  - `test_handler_skips_when_no_pdf_file` — FIX iter-1 CRIT-7 (UNIT test, ne integration)
  - `test_post_save_skips_when_raw_true` (loaddata fixture pattern)
  - `test_post_save_regenerates_cover_when_pdf_replaced` — FIX iter-1 CRIT-3 (NOVI)
  - `test_post_save_uses_on_commit_callback` — FIX iter-1 CRIT-5 (NOVI)
  - `test_signal_does_not_loop_on_internal_save` (AC7)
- **And** prošireni `apps/media_pipeline/tests/test_apps.py` (TEA scope, mirror Story 2.3 pattern):
  - `test_media_pipeline_ready_hook_imports_signals` — verifikuje da `MediaPipelineConfig.ready()` registruje signal
  - `test_post_save_receiver_registered_with_dispatch_uid` — IMP iter-1 IMP-7 (introspect `post_save._live_receivers(sender=ProductBrochure)` + dispatch_uid string check)

**AC9 — Boundary regression: `apps/media_pipeline/**/*.py` NE import-uje `apps.products` ni `apps.brands` (postojeći Story 2.3 AC8 testovi ostaju green)**

- **Given** `tests/integration/test_app_boundaries.py` linija 130-163 ima `test_media_pipeline_does_not_import_products` i `test_media_pipeline_does_not_import_brands` (Story 2.3 deliverable, verifikovano live read)
- **When** `just test tests/integration/test_app_boundaries.py` pokrenut posle Story 2.4 implementacije
- **Then** oba testa MORAJU PASS-ovati — to znači da:
  - `apps/media_pipeline/signals.py` NE SME imati `from apps.products.models import ProductBrochure` (mora koristiti `apps.get_model("products", "ProductBrochure")` u `ready()` hook-u — vidi AC4 implementacija)
  - `apps/media_pipeline/pdf_utils.py` NE SME importovati `apps.products` ni `apps.brands` (pure utility, no domain reference)
  - `apps/media_pipeline/apps.py` može imati `from django.apps import apps` (Django built-in) i `apps.get_model("products", "ProductBrochure")` (string-based reference NIJE statički import — AST check ne hvata, što je TAČNO ponašanje koje hoćemo)
- **And** AST static check u `_assert_no_import()` (linija 33-74 `tests/integration/test_app_boundaries.py`) hvata SAMO `ast.Import` i `ast.ImportFrom` nodove — `apps.get_model("products.ProductBrochure")` je string literal, nije AST import node, pa prolazi.

**AC10 — Code quality + format pass (DoD) + Dockerfile i pyproject.toml verifikacija**

- **Given** Implementacija završena
- **When** Mihas pokrene quality gate komande
- **Then** sve komande MORAJU exit code 0:
  - `uv run ruff check .` (linter — može na host-u, ne dotiče libmagic/poppler)
  - `uv run ruff format --check .` (formatter — može na host-u)
  - `uv run djade --check templates/` (Django template formatter — nema novih template-a u 2.4, ali postojeći moraju ostati pristojni)
- **And** **NEMA hardcoded UI string-ova bez `gettext_lazy`** u `apps/media_pipeline/pdf_utils.py` `validate_pdf_mime()` `ValidationError` porukama
- **And** **Log poruke u `signals.py` i `pdf_utils.py` SU u engleskom** (NE gettext-wrapped — per project-context.md § gettext / i18n u kodu — log entries za sysadmin nisu user-facing)
- **And** **NEMA `print()` poziva** u utility/signal kodu (debug print je anti-pattern; samo `logger.info/warning/error`)
- **And** **`compose/django/Dockerfile` verifikacija** (Pre-implementation smoke):
  - Linija 42 (`poppler-utils` u apt-get install list) **MORA postojati** (verifikovano live read — postoji)
  - Dev MORA potvrditi kroz `Get-Content compose/django/Dockerfile | Select-String "poppler-utils"` pre nego što počne implementaciju (defensive — ako Story 1.3 je obrisala iz nekog razloga, Story 2.4 ZAVISI od ovog system dep-a)
- **And** **`pyproject.toml` verifikacija** (Pre-implementation smoke):
  - Linija 17 (`pdf2image>=1.17.0`) **MORA postojati** (verifikovano live read — postoji)
  - Dev MORA potvrditi kroz `Get-Content pyproject.toml | Select-String "pdf2image"` pre nego što počne implementaciju
- **And** **`pyproject.toml` dev deps verifikacija (FIX iter-1 CRIT-2):**
  - `pytest-mock>=3.14.0` MORA biti u `[dependency-groups].dev` posle Task 0 izvršavanja
  - Verifikacija: `Get-Content pyproject.toml | Select-String "pytest-mock"`
  - Dev DODAJE ovu deps kroz Task 0 sa `uv add --dev pytest-mock>=3.14.0`; ovaj AC SAMO verifikuje DoD compliance
- **And** **`pyproject.toml` Pillow direct dep (IMP iter-1 IMP-5):**
  - Pillow je trenutno tranzitivna dep kroz sorl-thumbnail. Defensive: dodati `"pillow>=10.0",` u direct deps DA budući sorl-thumbnail downgrade ne pukne `Image.Resampling.LANCZOS` enum (Pillow 9.1+).
  - Task 0 takođe dodaje ovu deps: `uv add pillow>=10.0`
- **And** **NEMA Story 9.x Nginx promene (FIX iter-1 CRIT-6):** posto je FIX iter-1 CRIT-1 spustio `MAX_PDF_UPLOAD_SIZE_BYTES` na 10 MB (isti ceiling kao images), `client_max_body_size` config iz Story 2.3 MP-D8 / Story 9.x deployment-a već pokriva PDF upload-e. Story 2.4 NIJE blokirana ni na čemu u Story 9.x.

## Zadaci

### Task 0 — Dev dep prerequisite (FIX iter-1 CRIT-2 + IMP-5)

> ⚠️ **OBAVEZAN PRVI KORAK** — bez ovih dep-a Task 1.3 + AC7 spy testovi failuju.

- [x] 0.1: Dodati `pytest-mock` u dev deps:
  ```powershell
  docker compose -f compose/local.yml run --rm django uv add --dev pytest-mock>=3.14.0
  ```
  - Očekivan rezultat: `pyproject.toml` `[dependency-groups].dev` lista dobija `"pytest-mock>=3.14.0"`.
  - Smoke verify: `docker compose -f compose/local.yml run --rm django uv run python -c "import pytest_mock; print(pytest_mock.__version__)"` exit code 0.
- [x] 0.2: Dodati `Pillow` kao direct dep (IMP iter-1 IMP-5 — defensive guard):
  ```powershell
  docker compose -f compose/local.yml run --rm django uv add "pillow>=10.0"
  ```
  - Očekivan rezultat: `pyproject.toml` `dependencies` lista dobija `"pillow>=10.0"`.
  - Defensive razlog: budući sorl-thumbnail downgrade ne sme pukti `Image.Resampling.LANCZOS` enum (Pillow 9.1+ feature).
  - Smoke verify: `docker compose -f compose/local.yml run --rm django uv run python -c "from PIL import Image; print(Image.Resampling.LANCZOS)"` exit code 0.
- [x] 0.3: Commit `pyproject.toml` + `uv.lock` zasebno pre nego što počne Task 1+.

### Task 1 — Pre-implementation smoke verifikacije (AC10)

- [x] 1.1: Verifikovati Dockerfile poppler-utils dep:
  ```powershell
  Get-Content compose/django/Dockerfile | Select-String "poppler-utils"
  ```
  - **Očekivan output:** `        poppler-utils \` (linija 42)
  - Ako 0 linija → STOP. Dodati `poppler-utils` u apt-get install list pre nastavka (out-of-scope task u Story 2.4, ali defensive guard).
- [x] 1.2: Verifikovati pyproject.toml pdf2image dep:
  ```powershell
  Get-Content pyproject.toml | Select-String "pdf2image"
  ```
  - **Očekivan output:** `    "pdf2image>=1.17.0",` (linija 17)
  - Ako 0 linija → STOP. Pokrenuti `uv add pdf2image` pre nastavka.
- [x] 1.3: Verifikovati pytest-mock dostupan (za AC7 spy testove) — defense-in-depth posle Task 0.1:
  ```powershell
  docker compose -f compose/local.yml run --rm django uv run python -c "import pytest_mock; print(pytest_mock.__version__)"
  ```
  - Ako `ModuleNotFoundError` → vrati se na Task 0.1; Task 0 je morao biti izvršen pre Task 1.
- [x] 1.4: Verifikovati Pillow ima `Image.Resampling.LANCZOS`:
  ```powershell
  docker compose -f compose/local.yml run --rm django uv run python -c "from PIL import Image; print(Image.Resampling.LANCZOS)"
  ```
  - Mora exit code 0; Pillow >= 9.1 ima `Resampling` enum.
- [x] 1.5: **IMP iter-1 IMP-1 — INSTALLED_APPS order check.** Verifikovati da `apps.products` dolazi PRE `apps.media_pipeline` u `config/settings/base.py`:
  ```powershell
  Get-Content config/settings/base.py | Select-String "apps.products|apps.media_pipeline" | ForEach-Object { $_.LineNumber, $_.Line }
  ```
  - Očekivan output: `apps.products` linija ~45, `apps.media_pipeline` linija ~47 (verifikovano live read — TAČAN redosled).
  - Razlog: `MediaPipelineConfig.ready()` poziva `apps.get_model("products", "ProductBrochure")` — model registry MORA biti popunjen pre nego što media_pipeline `ready()` fires. Django INSTALLED_APPS order određuje `import_models()` redosled, a `ready()` fires posle SVIH `import_models()` poziva — TEORIJSKI redosled u INSTALLED_APPS ne menja ishod, ALI ovaj smoke check štiti od regression-a ako neko future story preorder-uje listu.

### Task 2 — Kreiranje `apps/media_pipeline/pdf_utils.py` (AC1 + AC2)

- [x] 2.1: Kreirati fajl `apps/media_pipeline/pdf_utils.py` sa kompletnim sadržajem iz AC1 (module docstring + imports + konstante + `validate_pdf_mime()`).
- [x] 2.2: Dodati `generate_brochure_cover_thumbnail()` funkciju iz AC2 (ContentFile return + non-raising semantics + graceful logger.warning).
- [x] 2.3: Smoke verifikacija — `docker compose -f compose/local.yml run --rm django uv run python -c "from apps.media_pipeline.pdf_utils import validate_pdf_mime, generate_brochure_cover_thumbnail; print('OK')"` mora exit code 0.

### Task 3 — Kreiranje `apps/media_pipeline/signals.py` (AC3)

- [x] 3.1: Kreirati fajl `apps/media_pipeline/signals.py` sa kompletnim sadržajem iz AC3 (handler funkcija sa 4 skip uslova + non-raising failure mode).
- [x] 3.2: Verifikovati da `signals.py` NE import-uje `from apps.products.models import ...` (koristi `apps.get_model()` u ready() hook-u):
  ```powershell
  Get-Content apps/media_pipeline/signals.py | Select-String "from apps.products"
  ```
  - Mora vratiti 0 linija (boundary compliance AC9).

### Task 4 — Edit `apps/media_pipeline/apps.py` (AC4 — dodavanje ready() hook-a)

- [x] 4.1: Pročitati live `apps/media_pipeline/apps.py` (Story 2.3 deliverable, linija 1-19).
- [x] 4.2: **Targeted Edit operacija** — dodati nove import-e i `ready()` metodu:
  - Pronaći `from django.apps import AppConfig` i ispod nje dodati `from django.db.models.signals import post_save`
  - Pronaći `verbose_name = _("Media pipeline")` i ispod nje dodati `ready()` metodu iz AC4 (cela metoda — docstring + apps.get_model + post_save.connect sa dispatch_uid).
- [x] 4.3: Dopuniti module docstring sa Story 2.4 napomenom (per AC4 snippet — "Story 2.4 (Epic 2) — DODATO: ready() hook wire-uje post_save signal...").
- [x] 4.4: Smoke verifikacija — `docker compose -f compose/local.yml run --rm django uv run python manage.py check` exit code 0; nema warning-a.

### Task 5 — Lokalni manual smoke (Mihas optional)

- [ ] 5.1: Pokrenuti `just dev` (Docker-backed Django runserver).
- [ ] 5.2: Otvoriti `/admin-coric/products/productbrochure/add/` (Story 2.2 stub admin koji je već registrovan).
- [ ] 5.3: Kreirati Brand + Product (kroz `/admin-coric/brands/brand/add/` + `/admin-coric/products/product/add/`).
- [ ] 5.4: Upload-ovati validan PDF kao `pdf_file` polje ProductBrochure (npr. bilo koji marketing PDF iz `tests/fixtures/`).
- [ ] 5.5: Save i refresh — proveriti da `cover_thumbnail_image` polje sada ima fajl URL (npr. `/media/products/brochure_covers/brochure-cover.jpg`); klik na URL otvara JPG sliku 240×320 (ili manje aspect-ratio adjusted).
- [ ] 5.6: Upload-ovati `not_a_pdf.txt` (preimenovan u .pdf) — Editor će videti save uspeo ali `cover_thumbnail_image` polje ostaje prazno; `docker compose logs django` pokazuje `WARNING ... Brochure cover render failed (recoverable)` log entry.
- [ ] 5.7 (out-of-scope za Story 2.4 ali korisno): otvoriti `/sr/admin-coric/products/productbrochure/<id>/change/` i potvrditi da Editor može ručno upload-ovati cover preko thumbnail-a (admin ImageField default widget) — signal handler skip-uje render jer `cover_thumbnail_image` već postoji (idempotency AC7).

### Task 6 — TEA RED phase (Step 3 — NIJE Dev scope u Story 2.4)

> ⚠️ Sledeći task-ovi su **TEA agent scope u Step 3** (test fixture-e + RED-phase test fajlovi). Dev preskače Task 6, prelazi na Step 3 koordinaciju kroz orkestrator.

- [x] 6.1: TEA proširuje `apps/media_pipeline/tests/conftest.py` sa `realistic_pdf_bytes` + `empty_pdf_bytes` + `corrupt_pdf_bytes` fixture-ima (per Decision PDF-D5 implementacija — minimal PDF struct ili static fixture).
- [x] 6.2: TEA kreira `apps/media_pipeline/tests/test_pdf_utils.py` sa 9 scenarija iz AC8 (validate_pdf_mime + generate_brochure_cover_thumbnail).
- [x] 6.3: TEA kreira `apps/media_pipeline/tests/test_signals.py` sa 7 scenarija iz AC8 (post_save handler integration + AC7 infinite loop guard).
- [x] 6.4: TEA proširuje `apps/media_pipeline/tests/test_apps.py` sa jednim novim testom — `test_media_pipeline_ready_hook_imports_signals` (introspekcija `post_save._live_receivers`).
- [x] 6.5: TEA NE dira `tests/integration/test_app_boundaries.py` (već ima Story 2.3 AC8 testove koji pokrivaju Story 2.4 boundary regression — re-run, ne re-write).

## Dev Notes

### Architecture compliance

- **App boundaries (architecture.md § App dependency graph line 732):** `media_pipeline ← (utility, importovan od products + brands + blog)`. Story 2.4 je **prvi signal handler** u media_pipeline app-u koji **referencira domain model** (`ProductBrochure` iz `apps.products`). Boundary compliance kroz **kasnu resoluciju**: `apps.get_model("products", "ProductBrochure")` u `apps/media_pipeline/apps.py.ready()` (per Django docs § Connecting signals + Story 2.3 AC8 boundary contract). Ovo je **kanonski Django pattern za signal wire-up u cross-app context-u** (referenca: Django docs "Best practices for connecting signals" — "Use sender as a string to avoid early import").
- **Signal handler vs management command trade-off:** Decision PDF-D1 razrešava — signal je prirodan choice jer:
  - (a) Editor UX: admin save → signal fires sync → Editor vidi cover odmah u list_display (no kasniji manual step)
  - (b) Performance: 1-3s sync delay je acceptable za admin save flow (ne za visitor request); per project-context.md § Async / Sync: "Tasks koje se mogu pokrenuti sync (thumbnail gen, email send) idu u signals ili direktno u view"
  - (c) Idempotency: post_save sa `update_fields` guard je deterministički — re-save ne re-render-uje (vidi AC7)
- **Locale awareness (project-context.md § gettext / i18n u kodu):**
  - `ValidationError` poruke u `validate_pdf_mime()` MORAJU biti `gettext_lazy as _` (lazy evaluation za i18n; admin form prikazuje na language Editor-a)
  - `logger.warning() / logger.info()` poruke SU u engleskom (NE gettext) — log entries za sysadmin, ne user-facing per project-context.md § gettext / i18n
  - Admin verbose_name labels (ako bi se dodale — u Story 2.4 NEMA novih modela) bi bile `gettext_lazy`

### Library/framework requirements

- **`pdf2image >= 1.17.0`** — VEĆ u `pyproject.toml` linija 17 (Story 1.1 dodala; Story 2.4 prvi konzument). `convert_from_bytes()` API ovde umesto `convert_from_path()` jer in-memory bytes su jednostavniji + Storage-API-agnostic (S3, Whitenoise, lokalni disk). **FIX iter-1 CRIT-4:** koristi `pdfinfo_from_bytes()` (validate_pdf_mime page count guard) + `timeout` kwarg (convert_from_bytes render timeout — pdf2image >= 1.17.0 feature, verifikuj).
- **`poppler-utils`** — sistemska zavisnost za `pdf2image` — VEĆ u `compose/django/Dockerfile` linija 42 (Story 1.3 dodala). Verifikovati pre Task 2.
- **Pillow** — bila tranzitivna; **FIX iter-1 IMP-5 promovisana u direct dep** (`pillow>=10.0` u pyproject.toml `dependencies`). Razlog: defensive guard od budućeg sorl-thumbnail downgrade-a koji bi mogao pukti `Image.Resampling.LANCZOS` enum (Pillow 9.1+). Task 0.2 dodaje.
- **`python-magic >= 0.4.27`** — VEĆ u pyproject.toml linija 19 (Story 2.3 prvi konzument za image MIME). Story 2.4 koristi za PDF MIME (`application/pdf`).
- **`pytest-mock>=3.14.0` (FIX iter-1 CRIT-2)** — NIJE bilo u pyproject.toml prethodno. **Task 0.1 dodaje** kroz `uv add --dev pytest-mock>=3.14.0`. Potreban za AC6 i AC7 spy testove (mocker.spy + mocker.patch fixtures).

### File structure

```text
apps/media_pipeline/                            # POSTOJI (Story 2.3)
├── __init__.py                                 # postoji, prazan (Story 2.3)
├── apps.py                                     # EDIT u Story 2.4 (Task 4 — dodaje ready())
├── models.py                                   # postoji, prazan (Story 2.3)
├── utils.py                                    # postoji (Story 2.3 — image MIME)
├── pdf_utils.py                                # NOVO Story 2.4 (Task 2 — validate_pdf_mime + generate_brochure_cover_thumbnail)
├── signals.py                                  # NOVO Story 2.4 (Task 3 — handle_brochure_post_save)
├── templatetags/                               # postoji (Story 2.3 — media_tags.py)
│   ├── __init__.py
│   └── media_tags.py
├── migrations/
│   └── __init__.py                             # postoji, prazan (Story 2.3 — utility app NEMA modela; Story 2.4 takođe NEMA migracija)
└── tests/                                      # postoji (Story 2.3, BEZ __init__.py per MP-R1)
    ├── conftest.py                             # EXTEND Story 2.4 (TEA Step 3 — dodaje realistic_pdf_bytes + empty_pdf_bytes + corrupt_pdf_bytes)
    ├── test_apps.py                            # EXTEND Story 2.4 (TEA Step 3 — dodaje test_media_pipeline_ready_hook_imports_signals)
    ├── test_settings.py                        # nepromenjen (Story 2.3)
    ├── test_utils.py                           # nepromenjen (Story 2.3 — image MIME testovi)
    ├── test_pdf_utils.py                       # NOVO Story 2.4 (TEA Step 3 — validate_pdf_mime + generate_brochure_cover_thumbnail unit tests)
    ├── test_signals.py                         # NOVO Story 2.4 (TEA Step 3 — post_save integration + infinite loop guard)
    ├── test_templatetags.py                    # nepromenjen (Story 2.3)
    └── test_thumbnails.py                      # nepromenjen (Story 2.3)

# Šta Story 2.4 NE DIRA:
# - apps/products/models.py (ProductBrochure model nepromenjen, vidi Story 2.2 spec)
# - apps/products/admin.py (Story 8.6 customizes; 2.4 oslanja se na stub register iz 2.2)
# - apps/brands/ (cross-app boundary — nema dotaknute fajlove)
# - config/settings/base.py (sve potrebne settings već iz Story 2.3 — sorl-thumbnail config + MEDIA_*)
# - config/urls.py (nepromenjen)
# - justfile (Docker test recept iz Story 2.3 MP-D6 ostaje SOT)
# - compose/django/Dockerfile (poppler-utils već prisutan)
# - pyproject.toml (pdf2image već prisutan)
# - tests/integration/test_app_boundaries.py (postojeći Story 2.3 testovi pokrivaju Story 2.4 boundary regression — vidi AC9)
```

### Signal wire-up rationale (Decision PDF-D6 expansion)

Story 2.4 koristi **eksplicitan `post_save.connect()` poziv u `ready()` hook-u**, NE `@receiver` decorator. Razlog:

- **Decorator pattern (`@receiver(post_save, sender=...)`):** zahteva sender da bude poznat **u trenutku module import**-a — što za Story 2.4 znači `from apps.products.models import ProductBrochure` na vrhu `signals.py`. **TO KRŠI Story 2.3 AC8 boundary** — `apps/media_pipeline/signals.py` NE SME importovati `apps.products`. Decorator pattern je nekompatibilan sa boundary rule-om.
- **Eksplicitan `post_save.connect()` u `ready()`:** sender se rešava kroz `apps.get_model("products", "ProductBrochure")` — string-based reference koja NIJE statički import. AST boundary check (`_assert_no_import`) NE hvata jer nema `ast.ImportFrom` node-a sa modulom `apps.products`.
- **Sekundarni benefit:** Lakše testirati — TEA može pozvati `handle_brochure_post_save(...)` direktno u unit test-u bez signal infrastructure, ILI proveriti registraciju kroz `post_save._live_receivers(sender=ProductBrochure)` introspection.
- **`dispatch_uid` benefit:** Bez `dispatch_uid` argumenta, Django ne deduplicira `post_save.connect()` pozive — ako se `ready()` slučajno pozove dva puta (pytest-django ima nekoliko edge case-ova sa app_loading), signal bi se pozvao DVA PUTA per save (race condition + nepredvidivo ponašanje). `dispatch_uid="apps.media_pipeline.signals.handle_brochure_post_save"` (full module path string — kanonska konvencija) garantuje single registration.

### Infinite loop prevention (AC7 deep dive — REVIDIRANO posle FIX iter-1 CRIT-3)

Signal handler save-uje cover_thumbnail_image polje preko `instance.save(update_fields=["cover_thumbnail_image"])` UNUTAR `transaction.on_commit()` callback-a (FIX iter-1 CRIT-5). Bez guard-a, Django bi mogao:

1. Editor save → post_save fires → handler registruje on_commit callback → outer transaction commit-uje → callback render-uje cover → callback save-uje brochure → post_save fires PONOVO sa `update_fields=["cover_thumbnail_image"]` → Layer A guard hvata (single-field update_fields == {"cover_thumbnail_image"}) → return.
2. **FIX iter-1 CRIT-3 PROMENA:** uklonjen je `if instance.cover_thumbnail_image: return` skip — handler SADA regeneriše cover na svaku pdf_file promenu. Replace-PDF UX je popravljen (stari skip je hidirao bug gde Editor zameni PDF, cover stay stale).
3. **Multi-layer infinite loop guard:**
   - **Layer A:** `if update_fields == frozenset({"cover_thumbnail_image"}): return` u handler-u (skip interni save iz našeg own callback-a).
   - **Layer B:** `instance.cover_thumbnail_image.save(name, content, save=False)` — `save=False` znači Storage piše fajl ali NE poziva `instance.save()` (no signal). Eksplicitan `instance.save(update_fields=["cover_thumbnail_image"])` posle je SAMO trigger Layer A skip-a — JEDAN save call → JEDAN post_save fire → SKIP.
4. **Pre-regen filter (FIX iter-1 CRIT-3):** `pdf_file_touched = update_fields is None or "pdf_file" in update_fields`. Title-only edit (`update_fields=["title"]`) → `pdf_file_touched=False` → skip (performance optimization, NIJE idempotency).

**Test patterns za AC7 (mirror Story 2.1/2.2 spy patterns):**

```python
def test_signal_does_not_loop_on_internal_save(realistic_pdf_bytes, ..., mocker):
    spy = mocker.spy(signals, "generate_brochure_cover_thumbnail")
    # objects.create() trigger-uje 1 render
    brochure = ProductBrochure.objects.create(...)
    assert spy.call_count == 1
    # save sa update_fields=["title"] NE trigger-uje render (pdf_file_touched=False)
    brochure.title = "Updated"
    brochure.save(update_fields=["title"])
    assert spy.call_count == 1
```

### `apps.get_model()` kasna resolucija — kanonski pattern

```python
# apps/media_pipeline/apps.py
def ready(self) -> None:
    from django.apps import apps  # Django built-in (NIJE apps.products!)
    from apps.media_pipeline.signals import handle_brochure_post_save

    # apps.get_model() je registry lookup — string-based
    product_brochure_model = apps.get_model("products", "ProductBrochure")
    post_save.connect(
        handle_brochure_post_save,
        sender=product_brochure_model,
        dispatch_uid="apps.media_pipeline.signals.handle_brochure_post_save",
    )
```

**Zašto `django.apps.apps` NIJE krše boundary:**
- `django.apps` je Django built-in modul (NIJE projekat `apps/` direktorijum sa app-ovima). Naming collision je nezgodan ali je standardni Django pattern.
- `apps.get_model("products", "ProductBrochure")` je **registry lookup** — vraća model klasu iz registar-a koji je popunjen kroz INSTALLED_APPS scan. Nema statičkog import-a `apps.products.models.ProductBrochure`.
- AST boundary check u `tests/integration/test_app_boundaries.py` proverava `ast.Import` i `ast.ImportFrom` node-ove — `apps.get_model("products", "ProductBrochure")` je `ast.Call` node sa string literal-ima, NIJE import node. Test prolazi.

### PDF generation parameters rationale

- **`first_page=1, last_page=1`** — TAČNO jedna stranica. Bez ovog argumenta, `convert_from_bytes()` render-uje sve stranice (memory bomb za 100-stranicu brošure!).
- **`dpi=100`** — balans kvalitet/brzina. 240×320 thumbnail ne treba viši dpi (output je heavily downscaled). 300 dpi (default) bi dao 2480×3508 PIL Image za 240×320 final = ~10× više memorije i CPU vremena bez vizuelne dobiti.
- **`fmt="jpeg"`** — eksplicitno; pdf2image default je "ppm" (Portable Pixmap) koji Pillow konvertuje u memoriji. JPEG fmt štedi memoriju (pdf2image piše JPEG bytes direktno).
- **`size=None`** (nije prosleđen) — pdf2image `size` parametar je "scale to fit within" što je manje precizno od Pillow `Image.thumbnail()` posle render-a. Razdvajanje render (dpi=100, native size) + thumbnail (Pillow LANCZOS 240×320) daje deterministički output.

### `validate_pdf_mime()` vs `validate_image_mime()` razlika

| Pattern | Image (Story 2.3) | PDF (Story 2.4 — FIX iter-1) |
|---|---|---|
| MIME signature | `image/jpeg`, `image/png`, `image/webp` | `application/pdf` |
| Size limit | 10 MB | **10 MB (FIX iter-1 CRIT-1 — sync sa MP-D8)** |
| Content verify | Pillow `Image.verify()` | `pdfinfo_from_bytes()` page count check (FIX iter-1 CRIT-4); render verify u `generate_brochure_cover_thumbnail()` |
| Decompression bomb guard | Pillow `MAX_IMAGE_PIXELS = 50_000_000` | **Trostruki layer (FIX iter-1 CRIT-4):** page count ≤ 200, render timeout ≤ 15s, rendered pixels ≤ 50M |
| Encrypted/password-protected | Raise on `Image.open()` | Raise `PDFSyntaxError` (FIX iter-1 CRIT-8 — graceful None) |
| Locale-aware error | `gettext_lazy as _` | `gettext_lazy as _` |
| Side-effect seek-back | `upload.seek(0)` finally | `upload.seek(0)` posle MIME check + posle pdfinfo |

### Out-of-scope za Story 2.4

- **NEMA admin custom widget za PDF preview** — Story 8.6 (Product CRUD admin) dodaje ProductBrochureInline sa cover_thumbnail_image preview u list_display. Story 2.4 koristi stub admin iz Story 2.2 (`admin.site.register(ProductBrochure)`).
- **NEMA ProductBrochureForm.clean_pdf_file()** integration — Story 8.6 prvi konzument `validate_pdf_mime()` u admin formi (mirror Story 2.3 AC5 image deferral pattern). Story 2.4 helper postoji za future Story 8.6 consumption.
- **NEMA migracije u media_pipeline ili products** — Story 2.4 ne menja modele.
- **NEMA Story 2.7 (Product Detail) template integracije** — Brošura card render je Story 2.7 scope; Story 2.4 garantuje da `cover_thumbnail_image` polje je populated (or None) — Story 2.7 render template ima fallback.
- **NEMA Celery / async task queue** — sync signal je acceptable per project-context.md § Async / Sync: "Sync only u v1; tasks koje se mogu pokrenuti sync (thumbnail gen, email send) idu u signals ili direktno u view".
- **NEMA `validate_image_mime()` proširenje** — utils.py ostaje nepromenjen.
- **NEMA cross-cutting infra promene** (Docker, justfile, settings) — Story 2.3 MP-D6 (Docker test recept) ostaje SOT.
- **NEMA Nginx config promene (FIX iter-1 CRIT-6 — removed):** Originalna Story 2.4 spec je zahtevala `client_max_body_size 50M` za Story 9.x Nginx — sada NIJE potrebno jer FIX iter-1 CRIT-1 spušta PDF size limit na 10 MB (isti ceiling kao image). Postojeći Story 2.3 MP-D8 / Story 9.x deployment config pokriva.
- **NEMA `signals.py` koja registruje druge signal handler-e** — Story 2.4 implementira SAMO ProductBrochure post_save. Future stories (Story 2.7 cache invalidation, Story 9.x sitemap re-gen) mogu dodati nove handler-e u isti `signals.py`.

#### Code review FIX iter-2 — deferred items (2026-05-30)

Tokom Story 2.4 code review (Fix iter-2), identifikovane su sledeće stavke koje **NISU u scope Story 2.4** i prebačene na buduće stories:

- **SEC-2 (`ProductBrochure.clean()` belt-and-suspenders) → Story 8.6:** Storage layer (FileField `save()`) trenutno ne poziva `validate_pdf_mime()` automatski — Story 2.4 isporučuje helper, ali integraciona tačka je `ProductBrochureForm.clean_pdf_file()` u Story 8.6 admin (mirror Story 2.3 AC5 image deferral pattern). Story 8.6 takođe može dodati `ProductBrochure.clean()` model-level validaciju za defense-in-depth (admin + management commands + future API).
- **Security hardening sweep → Story 9.x:** (a) `X-Content-Type-Options: nosniff` security header dodavanje, (b) supply chain audit (pip-audit / safety check u CI), (c) Docker base image cadence (renovate / dependabot za python:3.13-slim base updates). Sve out-of-scope za 2.4 jer su cross-cutting (svi epics affected, nije PDF-specifično).
- **Typing modernizacija (`typing.Iterable` → `collections.abc.Iterable`) → Story 9.x style sweep:** Python 3.13 preporučuje `collections.abc` za runtime-checkable abstract types. Style-only fix, ne menja semantics, ostavljamo za bulk sweep.

### Gotchas

- **Gotcha PDF-1 — poppler-utils Docker dep MORA biti prisutan** (cross-reference Story 2.3 MP-7 + MP-D6). `pdf2image.convert_from_bytes()` raise-uje `PDFInfoNotInstalledError` ako poppler-utils binary nije u `PATH`-u kontejnera. **Mihas (Windows host) MUST koristiti `just test` (Docker-backed) za sve Story 2.4 testove** — direktan `uv run pytest` na Windows host-u SEGFAULT-uje na libmagic (Story 2.3 MP-7) + raise-uje PDFInfoNotInstalledError na pdf2image (Story 2.4 PDF-1).
- **Gotcha PDF-2 — `apps.py.ready()` se poziva JEDNOM po Django process** (per Django docs). Ali pytest-django može reload-ovati AppConfig u edge case-ovima (npr. multiple test files menjaju INSTALLED_APPS); `dispatch_uid="apps.media_pipeline.signals.handle_brochure_post_save"` sprečava double-registration. Bez `dispatch_uid`, signal bi se pozvao 2× per save → test asercija `spy.call_count == 1` bi failovala intermitentno.
- **Gotcha PDF-3 — Infinite loop guard MORA proveriti `len(update_fields) == 1`** — bez tog uslova, ako Editor (Story 8.6) eksplicitno pošalje `update_fields=["pdf_file", "cover_thumbnail_image"]` (legitiman multi-field update gde Editor je hand-uploaded cover), guard bi neopravdano skip-ovao render. Logika: skip SAMO ako single-field update je tačno `{cover_thumbnail_image}` (interni signal save), inače fall-through na ostale skip uslove.
- **Gotcha PDF-4 — PDF page 1 može biti validan ali ne mogu se renderovati** (npr. JBIG2 image embedded sa nedostajućim library — poppler raise-uje `PDFSyntaxError` ali stranica strukturno postoji). `generate_brochure_cover_thumbnail()` MORA hvatati **sve** poznate poppler exception-e (`PDFInfoNotInstalledError`, `PDFPageCountError`, `PDFPopplerTimeoutError`, `PDFSyntaxError`) + generic `OSError`/`ValueError` (Pillow `thumbnail()` raise-uje na corrupt PIL Image). Defensive catch-all `except Exception` na kraju je opravdano (vidi AC2 implementation note).

  **FIX iter-1 CRIT-8 dopuna — enkriptovan PDF:** Poppler raise-uje `PDFSyntaxError` (NE poseban `PDFPasswordError` — proverio sa pdf2image 1.17 source code) kada PDF ima `/Encrypt` dictionary bez password-a. Handler graceful return `None` + log warning. Test scenario `test_generate_returns_none_for_encrypted_pdf` u test_pdf_utils.py eksplicitno dokumentuje ovo ponašanje (Editor će videti save uspeo + prazan cover; Story 8.6 admin može dodati form-level "PDF je zaštićen lozinkom — sačuvajte unprotected verziju" poruku kasnije).
- **Gotcha PDF-5 — Signal handler atomic transaction concerns + orphan-file prevention (FIX iter-1 CRIT-5)** — `instance.save(update_fields=["cover_thumbnail_image"])` u handler-u izvršava se u POSTOJEĆOJ DB transakciji od admin save flow-a (Django default `post_save` je u transaction.atomic). Ako handler raise-uje exception (NE bi smela — handler je non-raising po contract-u), Django bi rollback-ovao **ceo** admin save (Editor bi izgubio PDF upload). Zato je AC3 strogo non-raising — gracefull failure return-uje bez raise, brochure save uspe sa `cover_thumbnail_image=""`.

  **FIX iter-1 CRIT-5 dodatak — orphan file safety:** `ImageField.save()` piše JPG na DISK ODMAH (Django Storage API bypassa DB transakciju — fajl na file system-u nije pod transakcijskim kontrolom). Ako outer transakcija ROLLBACK-uje (npr. neki drugi pre_save signal handler iza nas raise-uje ValidationError), DB stanje se vraća ali JPG fajl OSTAJE kao orphan. **Rešenje:** AC3 wrap-uje render + save logic u `transaction.on_commit(_generate_cover_on_commit)` callback. Callback se izvršava SAMO ako outer transakcija uspešno commit-uje. Rollback path = no fajl write. Vidi AC3 implementation block + AC7 `test_post_save_uses_on_commit_callback` test.
- **Gotcha PDF-6 — epics.md vs Story 2.2 putanja neslaganje (PROMOVISANO U Decision PDF-D8 per IMP iter-1 IMP-4)** — Detalji su sada strukturisani kao Decision PDF-D8 (deferred docs sync u Story 9.x). Kratki summary za Dev: Story 2.4 koristi `instance.cover_thumbnail_image.save(name, content)` koji indirektno koristi model `upload_to="products/brochure_covers/"` setting. NEMA hardcoded path-a u signal/utility kodu. Vidi PDF-D8 za pun rationale.
- **Gotcha PDF-7 — `update_fields` može biti `None`** — Django `Model.save()` poziv bez `update_fields` argumenta šalje `update_fields=None` u `post_save` signal. Handler guard `if update_fields and "cover_thumbnail_image" in update_fields` SAFE handle-uje None (truthy check kratko-cirkutira). Bez `update_fields and` prefiksa, `"cover_thumbnail_image" in None` raise-uje `TypeError`.
- **Gotcha PDF-8 — `raw=True` u loaddata** (cross-reference Django docs "Sending signals from model fixtures") — kad Django `loaddata` import-uje fixture sa ProductBrochure recordom, `post_save` signal fires sa `raw=True`. Bez `if raw: return` guard-a, signal bi renderovao cover za svaki record u fixture-u (npr. 100 brochure-a u staging seed → 100× pdf2image render = ~5 minuta). Test seedovanje + admin export/import koristi loaddata, guard je obavezan.
- **Gotcha PDF-9 — Pillow JPEG mode requirement** — `Image.save(buffer, format="JPEG")` raise-uje `OSError: cannot write mode RGBA as JPEG` ako PIL Image nije RGB (PDF render može vratiti RGBA/P/L modes). Force `if page_image.mode != "RGB": page_image = page_image.convert("RGB")` PRE `save()` poziva (per AC2 implementation).
- **Gotcha PDF-10 — `instance.cover_thumbnail_image.save(name, content, save=False)` semantika** — `save=False` argument kaže Django Storage da save fajl na disk ALI NE pozove `instance.save()` posle (drugim rečima, ne triggeruj post_save signal). Ovaj guard je sekundarna zaštita za infinite loop pored `update_fields={"cover_thumbnail_image"}` u explicit `instance.save()` pozivu posle. Bez `save=False`, jedan implicit save iz Storage-a + jedan explicit save iz handler-a = dva post_save fires.

- **Gotcha PDF-11 — PDF DoS protection: page count + render timeout + decompression bomb (FIX iter-1 CRIT-4)** — PDF format dozvoljava: (a) milion stranica u jednom fajlu (Catalog/Pages tree), (b) MediaBox 50000×50000 page size sa raw content stream (poppler render → 5 GB PIL Image), (c) loop bug-ove u embeddedim shading patterns (poppler render hang). Story 2.4 implementuje **trostruki guard layer**:
  1. **Page count guard** (`MAX_PDF_PAGE_COUNT = 200`) — `pdfinfo_from_bytes()` u `validate_pdf_mime()` čita PDF metadata BEZ rendering-a; raise `ValidationError` ako pages > 200.
  2. **Render timeout** (`PDF_RENDER_TIMEOUT_SECONDS = 15`) — `convert_from_bytes(..., timeout=15)` (pdf2image >= 1.17). Poppler subprocess SIGTERM posle 15s → `PDFPopplerTimeoutError` exception.
  3. **Rendered pixel ceiling** (`MAX_RENDERED_PIXELS = 50_000_000`) — eksplicitan `page_image.width * page_image.height > MAX_RENDERED_PIXELS` check posle render-a, pre Pillow thumbnail-a. Pillow `MAX_IMAGE_PIXELS` (globalno set u Story 2.3) **NE pomaže** ovde jer pdf2image bypass-uje Pillow `load()` path (vraća već-loaded PIL Image objekat).
  - **Realan scenario:** Marijana (Editor) accidentally upload-uje neku tehničku knjigu od 800 stranica → AC1 page count guard odbija pri form save-u (ValidationError on admin form). Validan brochure (5-30 stranica) prolazi.
  - **Test pokrivenost:** `test_validate_pdf_rejects_high_page_count`, `test_generate_returns_none_on_render_timeout`, `test_generate_returns_none_on_decompression_bomb` (svi u test_pdf_utils.py).

- **Gotcha PDF-12 — Concurrent upload race condition (IMP iter-1 IMP-6)** — Ako dva Editor user-a istovremeno upload-uju brochure za isti Product (admin u dva tab-a), oba signal handler-a render-uju cover u isto vreme. Django Storage default backend (`FileSystemStorage`) generiše unique-suffix za file name (`brochure-cover_AbCdEf.jpg`) — NEMA file conflict. ALI DB race: oba handler-a pozivaju `instance.save(update_fields=["cover_thumbnail_image"])`; poslednji save wins (overrides cover_thumbnail_image field value sa svojom JPG). Acceptable trade-off za v1 admin scope (single Editor concurrent upload je rare). Future Story (9.x) može uvesti `SELECT FOR UPDATE` lock ako bude potrebno.

### Decisions

**Decision PDF-D1 — Signal handler vs management command za PDF cover generation**

- **Pitanje:** Da li trigger-ovati cover generation kroz post_save signal (automatski na admin save) ili kroz management command (`python manage.py generate_brochure_covers`) koji Editor pokreće manualno?
- **Odluka:** **post_save signal** (sync, no Celery).
- **Rationale:**
  - **(a) Editor UX:** Admin save → cover odmah dostupan u list_display + ProductDetail strana. Bez intermediate koraka. Management command zahteva Editor da otvori shell ili dodatni admin button (visoki cognitive overhead za marketing team koji ne zna kako da pokrene CLI komandu).
  - **(b) Idempotency je laka** — guard `if instance.cover_thumbnail_image: return` skip-uje re-render. Re-run management command-a bio bi takođe idempotent, ali Editor mora znati kad da pokrene (after upload? on schedule?). Signal je deterministički — uvek puca posle save.
  - **(c) Performance acceptable za admin save:** 1-3s sync delay nije kritičan za admin workflow. Story 9.9 može meriti i opcionalno migrirati na async ako Mihas odluči (out-of-scope).
- **Alternative razmatrane:**
  - **Management command:** odbačeno — high Editor UX cost; idempotency manualno tracked.
  - **Celery task queue:** odbačeno — project-context.md § Critical version constraints: "Bez Celery / Redis u v1; signali za thumbnails". Story 2.4 prati v1 SOT.
  - **Admin form `save_model()` override:** moguće, ali signal je generalniji (radi i za fixture-e koji bypass admin form). Vidi MP-D2 Story 2.3 — sorl-thumbnail koristi lazy signal pattern.
- **Reversibilnost:** Reverzibilno. Future Story 9.9 može uvesti Celery + Redis + async task za PDF render — signal handler bi delegirao na task queue umesto sync poziva. Migration path: izmeniti `handle_brochure_post_save` da pozove `tasks.generate_brochure_cover.delay(instance.id)` umesto sync helper. NEMA scheme change.

**Decision PDF-D1.5 — Eager vs lazy regeneration na pdf_file replace (FIX iter-1 CRIT-3 — promovisana sub-decision)**

- **Pitanje:** Kad Editor zameni `pdf_file` polje brochure-a (npr. greška u prvoj verziji → upload V2), da li handler treba da regeneriše cover ili da skip-uje ako cover_thumbnail_image već postoji?
- **Odluka:** **Eager regeneration na svaku pdf_file promenu.** Handler NEMA `if cover_thumbnail_image: return` skip uslov.
- **Rationale:**
  - **(a) Replace-PDF UX:** epics.md AC line 577 zahteva "automatic generation"; Editor očekuje da posle zamene PDF-a cover bude svež. Stara verzija (skip ako cover postoji) je hidirala bug: Editor zameni PDF, cover ostaje stale (slika prve strane STAROG PDF-a). Marijana bi morala da zna da "obriše cover ručno" u admin formi — visok cognitive overhead.
  - **(b) Trigger logic:** `update_fields=None` ili `"pdf_file" in update_fields` → regen. Multi-field saves bez pdf_file (Editor menja samo `title`) NE regenerišu (skip-ujem zbog performance). To je optimization, NIJE idempotency.
  - **(c) Infinite-loop guard očuvan:** Layer A guard (`update_fields == {"cover_thumbnail_image"}` → skip) i dalje funkcioniše. Bez idempotency skip-a, jedinstvena bezbednosna mreža je Layer A — testovi AC7 verifikuju da nema beskonačne petlje.
- **Alternative razmatrane:**
  - **Idempotency skip (stara verzija) + admin "regenerate cover" button:** odbačeno — Story 8.6 admin work; ne želimo blokiraju Story 8.6 design choice-em iz Story 2.4.
  - **Compare PDF hash + skip ako isti:** odbačeno — overkill (hash compare svaki save = extra I/O); replace je rare event.
- **Posledice:**
  - Replace-PDF scenario: 1 render extra po Editor save-u koji menja pdf_file. Acceptable (1-3s).
  - Title-only edit: 0 render-a (handler skip-uje rano). Optimization očuvana.
  - Test AC7 dodaje `test_post_save_regenerates_cover_when_pdf_replaced` koji eksplicitno verifikuje regen ponašanje.

**Decision PDF-D2 — Separator: `pdf_utils.py` (NOVO) vs `utils.py` (extend Story 2.3)**

- **Pitanje:** Dodati `validate_pdf_mime()` + `generate_brochure_cover_thumbnail()` u POSTOJEĆI `apps/media_pipeline/utils.py` (Story 2.3 module) ili kreirati novi `pdf_utils.py`?
- **Odluka:** **Novi `pdf_utils.py`** module.
- **Rationale:**
  - **(a) Separation of concerns:** Image MIME validation + Pillow decompression bomb guard semantički su odvojeni od PDF MIME + pdf2image render. Mešanje u jedan module bi zatamnio bounded contexts.
  - **(b) Import overhead:** Story 8.6 (Brand admin) može import-ovati `validate_pdf_mime` bez učitavanja Pillow-related konstanti iz utils.py (npr. `MAX_IMAGE_PIXELS = 50_000_000` je global side-effect koji NE treba u Brand admin context-u koji ne radi sa PDF-om).
  - **(c) Test isolation:** `test_utils.py` (Story 2.3) testira image; `test_pdf_utils.py` (Story 2.4) testira PDF. Razdvajanje module-a olakšava paralelizaciju + debugging.
  - **(d) Mirror Django convention:** Django sam ima `django.core.files.uploadedfile` + `django.core.files.storage` razdvojeno — različiti context-i različiti module-i.
- **Alternative razmatrane:**
  - **Extend utils.py:** odbijeno — semantička haos + tranzitivni import overhead.
  - **Single `media_utils.py` (rename utils.py):** odbijeno — rename bi tražio update u Story 2.3 production code-u + testove + Story 2.3 docstring-ove. Out-of-scope za Story 2.4.
- **Trade-off:** Dva mali module-a vs jedan veliki — preferiramo razdvajanje. `pdf_utils.py` ostaje relativno mali (~150 lines) sa fokusiranim API-jem.

**Decision PDF-D3 — `Image.thumbnail()` (aspect ratio preserved) vs `Image.resize((240, 320))` (strict resize)**

- **Pitanje:** Da li `cover_thumbnail_image` mora biti TAČNO 240×320 (može distortion) ili max 240×320 sa aspect ratio očuvanim?
- **Odluka:** **Aspect ratio preserved** kroz Pillow `Image.thumbnail((240, 320), LANCZOS)`. Output može biti 240×340 (portrait wider) ili 226×320 (portrait narrower) zavisno od source PDF aspect ratio-a.
- **Rationale:**
  - **(a) PDF stranice nisu uniform aspect ratio:** A4 portrait je ~1:1.414 (595:842 = 0.7071); 240×320 fixed je 1:1.333 (~0.75) — strict resize bi distortovao A4 brošure (sve PDF-e iz prakse). Aspect ratio preservation je vizuelno korektan.
  - **(b) Story 2.7 layout flex:** Story 2.7 Brošura card koristi `max-width: 240px; max-height: 320px` CSS — varianta od ±15% u svakoj dimenziji je acceptable (responsive layout adjustuje).
  - **(c) Pillow `thumbnail()` API design:** Pillow autori su designirali ovo za thumbnails — DPI optimization + in-place mutation. Korišćenje `resize()` bi bilo manualno preciznije ali manje idiomatsko za thumbnail use case.
- **Alternative razmatrane:**
  - **`Image.resize((240, 320))` strict:** odbijeno — distortion neacceptable za vizuelne brošure.
  - **`ImageOps.fit((240, 320), centering=(0.5, 0.0))`** (smart crop, top-aligned):** razmatrano — daje TAČNO 240×320 sa center crop. Trade-off: gubi delove PDF stranice (npr. logo na vrhu može biti odsečen). Story 2.7 layout je tolerantan na variantnu visinu, pa `thumbnail()` je bolji choice.
- **Posledice cross-story:**
  - Story 2.7 CSS: `max-width: 240px; max-height: 320px; object-fit: contain` (ne `cover` — kontain očuva aspect ratio bez crop-a).
  - Story 8.6 admin list_display: thumbnail varijabilan u visini, ali u OK rangu za list rendering.

**Decision PDF-D4 — Sync signal vs async task — accepted trade-off**

- **Pitanje:** post_save signal je sync — admin save flow čeka 1-3s za pdf2image render. Da li ovo blokira Editor UX?
- **Odluka:** **Sync je acceptable za v1.** No Celery / Redis (per project-context.md § Critical version constraints).
- **Rationale:**
  - **(a) Editor frequency:** Editor (Marijana persona) save-uje brochure-e ~5-10 puta dnevno; 1-3s × 10 = 10-30s ukupno čekanja per dan — negligible.
  - **(b) Sync je deterministički:** Editor vidi cover odmah, ne mora refresh-ovati 30 sekundi kasnije. Async bi zahtevao polling ili UI message "cover će biti generisan uskoro".
  - **(c) Infrastructure cost:** Redis + Celery worker + monitoring = +30% complexity. Za v1 scope (single VPS, 1-2 Editor user-a, ~100 brochure-a ukupno u sistemu) nije opravdano.
- **Trade-off:** Visitor request impact je 0 (signal puca SAMO na admin save, ne na visitor browse). Sync signal NIKAD ne usporava public catalog page-e.
- **Reversibilnost:** Future Story 9.9 može uvesti Celery — migration path: replace `generate_brochure_cover_thumbnail()` direktni poziv sa `tasks.generate_brochure_cover.delay(instance.id)`. Tasks module bi importovao isti `pdf_utils.generate_brochure_cover_thumbnail` i radio savojski.

**Decision PDF-D5 — Test fixture za realistic_pdf_bytes — reportlab vs static fixture vs minimal PDF struct**

- **Pitanje:** TEA agent treba da kreira `realistic_pdf_bytes` fixture za `apps/media_pipeline/tests/conftest.py`. Tri pristupa:
  1. **reportlab** library — generiše validan PDF in-memory u fixture-u
  2. **Static fixture** — checked-in PDF fajl u `tests/fixtures/` (binary)
  3. **Minimal raw PDF struct** — bytes konstanta sa minimalnim PDF header + body + xref
- **Odluka:** **Minimal raw PDF struct** kao pre-defined bytes konstanta u conftest-u (mirror Story 2.3 `valid_jpeg_bytes` 62-byte pattern).
- **Rationale:**
  - **(a) NEMA nove dev dep:** reportlab nije u dependency-groups.dev; dodavanje samo za testove je overhead. Minimal struct je inline u conftest.py.
  - **(b) Brzina:** static fixture import (read from disk) je sporiji od bytes konstante.
  - **(c) Determinizam:** Pre-defined bytes su predictable; reportlab može menjati output između verzija.
  - **(d) Pillow + pdf2image radi sa minimal validan PDF struct** (verifikovano kroz adversarial proba — minimal PDF struct sa 1 page i jedan "Hello" text rendera kao 595×842 white image).
- **Implementation note (TEA scope):**
  ```python
  # apps/media_pipeline/tests/conftest.py — EXTEND Story 2.3 conftest
  MINIMAL_PDF_1_PAGE = (
      b"%PDF-1.4\n"
      b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
      b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
      b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
      b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n"
      b"4 0 obj\n<< /Length 44 >>\nstream\nBT /F1 24 Tf 100 700 Td (Hello PDF!) Tj ET\nendstream\nendobj\n"
      b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
      b"xref\n0 6\n0000000000 65535 f\n"
      b"0000000009 00000 n\n0000000058 00000 n\n0000000111 00000 n\n"
      b"0000000212 00000 n\n0000000293 00000 n\n"
      b"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n358\n%%EOF\n"
  )

  @pytest.fixture
  def realistic_pdf_bytes():
      """Minimal 1-page validan PDF (Hello PDF text). Pdf2image radi, Pillow render-uje."""
      return MINIMAL_PDF_1_PAGE

  @pytest.fixture
  def corrupt_pdf_bytes():
      """Random bytes pretvarajući se da je PDF — fail na MIME check ili pdf2image render."""
      return b"NOT_A_PDF_AT_ALL_JUST_RANDOM_BYTES"

  @pytest.fixture
  def empty_pdf_bytes():
      """0-byte upload — guard za empty file."""
      return b""
  ```
- **Alternative razmatrane:**
  - **reportlab:** odbijeno — nova dev dep, overkill za 1 fixture.
  - **Static fixture u tests/fixtures/:** odbijeno — checked-in binary fajl je harder to review + version control diff je nečitljiv.

**Decision PDF-D6 — `apps.py.ready()` eksplicitan `post_save.connect()` vs `@receiver` decorator**

- **Pitanje:** Wire signal kroz `@receiver(post_save, sender=ProductBrochure)` decorator (Django shortcut) ili eksplicitno `post_save.connect(handler, sender=..., dispatch_uid=...)` u `ready()` hook-u?
- **Odluka:** **Eksplicitan `post_save.connect()` u `ready()` hook-u** sa `dispatch_uid`.
- **Rationale:**
  - **(a) Boundary compliance KRITIČNO:** `@receiver` decorator zahteva sender da bude poznat u module import vremenu — što za Story 2.4 znači `from apps.products.models import ProductBrochure` na vrhu `signals.py`. To kršI Story 2.3 AC8 boundary (verified live u `tests/integration/test_app_boundaries.py` linija 130-163). `apps.get_model("products", "ProductBrochure")` u `ready()` je kasnu resoluciju koja NIJE statički import.
  - **(b) Testabilnost:** TEA može pozvati `handle_brochure_post_save(sender=ProductBrochure, instance=..., created=True, raw=False, update_fields=None)` direktno u unit test bez signal infrastructure.
  - **(c) Duplicate registration guard:** `dispatch_uid` (string identifier) garantuje single registration ako `ready()` se slučajno pozove dva puta (pytest-django edge case).
  - **(d) Django docs preporuka:** Django Best Practices za signal connections (https://docs.djangoproject.com/en/5.2/topics/signals/#connecting-receiver-functions) eksplicitno preporučuje wire u `AppConfig.ready()` za apps koji import-uju iz drugih app-ova.
- **Alternative razmatrane:**
  - **`@receiver` decorator + statički import:** odbijeno — kršI boundary rule.
  - **`@receiver` decorator + `sender = None` + manual filter u handler-u:** odbijeno — `sender=None` postavlja handler na SVE modele (sa is_instance check internim) što je memory overhead + brittle. AC4 specifična ProductBrochure connection je sigurnija.
  - **`post_save.connect()` u `signals.py` module level:** odbijeno — module se loaduje pre nego što `apps.products` model registar bude populated; `apps.get_model("products", "ProductBrochure")` u module level bi raise-uo `AppRegistryNotReady`. `ready()` hook je guaranteed pozvan posle app registry-a.

**Decision PDF-D7 — PDF MIME validation — single MIME (`application/pdf`) vs multiple (`application/x-pdf`, `application/acrobat`, ...)**

- **Pitanje:** python-magic može vratiti različite MIME stringove za PDF zavisno od signature variants. Pre-PDF/A standardizovan je samo `application/pdf` — ali file types kao PDF/UA, PDF/X, scanned PDF od starijih scanner-a mogu imati alternate MIME.
- **Odluka:** **Single MIME `("application/pdf",)`** u `ALLOWED_PDF_MIME_TYPES` tuple. Reject sve ostale.
- **Rationale:**
  - **(a) python-magic koristi libmagic database** — moderni libmagic verzije vraćaju `application/pdf` za SVE PDF varijante (PDF 1.0 do PDF 2.0; PDF/A, PDF/UA, PDF/X). Empirijski potvrđeno u libmagic source-u: `magic/Magdir/pdf` regex matchuje `%PDF-` i vraća `application/pdf` bez subtype distinction.
  - **(b) Defensive guard NIJE potrebna:** Ako budući PDF/foo format dobije sopstveni MIME u nekoj future libmagic verziji, `validate_pdf_mime` će raise-ovati ValidationError što je acceptable (Mihas može updatovati `ALLOWED_PDF_MIME_TYPES` tuple ako se ikad desi).
  - **(c) Security:** Multiple MIME whitelist proširuje attack surface (npr. `application/x-pdf` je deprecated MIME koji neke stare libmagic verzije vraćaju za malformed PDF-e — odbijanje je čistija policy).
- **Trade-off:** Ako Mihas u praksi naiđe na PDF koji libmagic vraća kao `application/x-pdf`, `application/octet-stream`, ili sličan, Editor će videti `Nedozvoljen tip fajla: %(mime)s` poruku. To je acceptable trade-off za sigurnost; Mihas može tunirati listu pri encounter-u.
- **Cross-reference:** Mirror Story 2.3 Decision MP-D5 pattern (kanonska MIME lista za image; ovde isto za PDF).

**Decision PDF-D8 — epics.md docs sync deferred to Story 9.x docs update (IMP iter-1 IMP-4 — promovisano iz Gotcha PDF-6)**

- **Pitanje:** epics.md AC line 579 kaže "Generated thumbnail je u `media/products/<slug>/brochure-cover.jpg`" sa product slug podirekturijem. Story 2.2 model definiše `upload_to="products/brochure_covers/"` (linija 432) — flat direktorijum bez slug-a. Šta je SOT?
- **Odluka:** **Story 2.2 model definicija je SOT** za Story 2.4. epics.md docs **deferred** za sync u Story 9.x (docs cleanup / brownfield audit story). Story 2.4 ne dodaje migraciju koja bi menjala `upload_to` (out-of-scope).
- **Rationale:**
  - **(a) Migration cost:** Menjanje `upload_to` zahteva novu migraciju + potencijalno data migration (premeštanje postojećih fajlova). Story 2.4 NEMA model promene.
  - **(b) Editor UX:** Editor ne vidi file path direktno (path je internal); Editor pretražuje brochure-e kroz admin UI. Razlika između `<slug>/` i `brochure_covers/` je nevidljiva u UI.
  - **(c) Docs autoritet:** Story 2.2 je već implementiran (live `apps/products/models.py` linija 425-435 verifikovano); model je lock SOT.
- **Posledice:**
  - Stvarna putanja: `media/products/brochure_covers/<filename>.jpg` (sa Storage backend hash suffix ako conflict).
  - Story 9.x docs update task: rewrite epics.md line 579 da odgovara model definiciji ILI rewrite model definicije + migration — Mihas decide kasnije.
- **Reversibilnost:** Reverzibilno. Story 9.x može dodati `ProductBrochure.cover_thumbnail_image.upload_to = lambda instance, filename: f"products/{instance.product.slug}/{filename}"` callable + migration. Story 2.4 graceful: signal handler ne pretpostavlja putanju; koristi model field `upload_to` indirektno kroz `instance.cover_thumbnail_image.save(name, content)`.

### Cross-references to Story 2.3 decisions (MP-D# pattern reuse)

Story 2.4 oslanja se na sledeće Story 2.3 odluke (NE redefiniše ih, samo konzumira):

- **MP-D1 (sorl-thumbnail vs alternatives):** Story 2.4 NE konzumira `sorl-thumbnail` direktno (PDF cover thumbnail je pre-rendered JPG, ne lazy on-demand srcset varijanta). Ali Story 2.7 template MOŽE pozvati `{% responsive_picture brochure.cover_thumbnail_image %}` koji koristi sorl-thumbnail za 400w/800w varijante.
- **MP-D2 (Lazy generation umesto post_save signal batch):** Story 2.4 koristi **post_save signal** za PDF cover (single thumbnail, no varijante). Ovo NIJE u konfliktu sa MP-D2 koja se odnosi na image varijante (sorl-thumbnail lazy je za 400w/800w/1600w srcset varijante; PDF cover je SAMO JEDAN fajl, sync rendering je opravdan).
- **MP-D3 (raise vs bool return):** Story 2.4 `validate_pdf_mime()` prati isti pattern — **raise ValidationError**. `generate_brochure_cover_thumbnail()` ODSTUPA: vraća `ContentFile | None` jer caller signal handler MORA biti non-raising (vidi AC2 + Gotcha PDF-5).
- **MP-D4 (inclusion_tag vs simple_tag):** N/A — Story 2.4 NEMA template tagove.
- **MP-D5 (PNG transparency format kwarg):** N/A — Story 2.4 PDF cover je uvek JPEG (no transparency u PDF brošurama).
- **MP-D6 (justfile Docker test recept):** **KRITIČNO Story 2.4 SOT za testove.** Mihas (Windows host) MORA koristiti `just test apps/media_pipeline/tests/` umesto direktnog `uv run pytest` — libmagic + poppler-utils nisu dostupni na Windows host-u. Story 2.4 ne menja justfile (recept iz MP-D6 ostaje SOT).
- **MP-D7 (THUMBNAIL_PREFIX vs DIRNAME):** N/A — Story 2.4 ne dotiče sorl-thumbnail KVStore konfiguraciju.
- **MP-D8 (DATA_UPLOAD_MAX_MEMORY_SIZE + FILE_UPLOAD_MAX_MEMORY_SIZE):** **DIREKTNI uticaj na Story 2.4 — FIX iter-1 CRIT-1 + CRIT-6.** Story 2.3 MP-D8 je postavila `DATA_UPLOAD_MAX_MEMORY_SIZE = 11 MB` i `FILE_UPLOAD_MAX_MEMORY_SIZE = 10 MB`. Story 2.4 originalna spec je tražila 50MB PDF ceiling, što bi konflikt-ovalo (Django bi blokirao na 11MB pre validate_pdf_mime). **FIX iter-1 CRIT-1:** Story 2.4 SADA koristi `MAX_PDF_UPLOAD_SIZE_BYTES = 10 MB` (isti kao image) — kongruentno sa MP-D8 limit-om. **FIX iter-1 CRIT-6:** NEMA potrebe za novim Story 9.x Nginx `client_max_body_size` adjustment — postojeći config iz Story 2.3 MP-D8 / Story 9.x deployment-a već pokriva PDF upload-e na 10 MB ceiling-u.

## Testing Notes

### Šta TEA treba da pokrije (RED phase u Step 3)

**Test file org (per project-context.md § Test organization + Story 2.3 conftest pattern):**

- Unit tests kolokovani uz app — `apps/media_pipeline/tests/test_<module>.py`
- Conftest extend Story 2.3 `apps/media_pipeline/tests/conftest.py` (BEZ `__init__.py` per MP-R1 — verifikovano)
- Test discipline: TEA piše testove (RED), Dev piše implementaciju (GREEN) — per project-context.md § Test discipline

**Fixture additions (TEA scope, Step 3):**

- `realistic_pdf_bytes` — Minimal 1-page validan PDF struct (per Decision PDF-D5 implementation)
- `corrupt_pdf_bytes` — random bytes pretvarajući se da je PDF
- `empty_pdf_bytes` — 0-byte upload (size guard test)

**Test coverage per AC:**

| AC | Test file | Test funkcije |
|---|---|---|
| AC1 (validate_pdf_mime) | `apps/media_pipeline/tests/test_pdf_utils.py` | `test_validate_pdf_mime_accepts_valid_pdf`, `test_validate_pdf_mime_rejects_image_as_pdf`, `test_validate_pdf_mime_rejects_empty_upload`, `test_validate_pdf_mime_rejects_none_upload`, `test_validate_pdf_mime_rejects_oversize_upload` (>10 MB — FIX iter-1 CRIT-1), `test_validate_pdf_rejects_high_page_count` (FIX iter-1 CRIT-4 — >200 stranica) |
| AC2 (generate_brochure_cover_thumbnail) | `apps/media_pipeline/tests/test_pdf_utils.py` | `test_generate_returns_content_file_for_valid_pdf`, `test_generate_returns_none_for_corrupt_pdf`, `test_generate_returns_none_for_empty_field`, `test_generate_returns_none_for_encrypted_pdf` (FIX iter-1 CRIT-8), `test_generate_returns_none_on_render_timeout` (FIX iter-1 CRIT-4 — mock PDFPopplerTimeoutError), `test_generate_returns_none_on_decompression_bomb` (FIX iter-1 CRIT-4 — mock 50001×50001 PIL), `test_generate_force_rgb_mode_for_jpeg_save`, `test_generate_thumbnail_within_240x320_bounds` |
| AC3 (signals.py handler) | `apps/media_pipeline/tests/test_signals.py` | `test_post_save_skips_when_raw_true`, `test_handler_skips_when_no_pdf_file` (FIX iter-1 CRIT-7 — UNIT test), `test_post_save_regenerates_cover_when_pdf_replaced` (FIX iter-1 CRIT-3), `test_post_save_uses_on_commit_callback` (FIX iter-1 CRIT-5) |
| AC4 (apps.py ready() hook) | `apps/media_pipeline/tests/test_apps.py` (EXTEND) | `test_media_pipeline_ready_hook_imports_signals`, `test_post_save_receiver_registered_with_dispatch_uid` (IMP iter-1 IMP-7) |
| AC5 (cover generation integration) | `apps/media_pipeline/tests/test_signals.py` | `test_post_save_generates_cover_thumbnail` (integration test sa real PDF + DB — `@pytest.mark.django_db(transaction=True)` per IMP iter-1 IMP-2) |
| AC6 (graceful failure) | `apps/media_pipeline/tests/test_signals.py` | `test_post_save_graceful_failure_corrupt_pdf`, `test_post_save_graceful_failure_empty_pdf`, `test_post_save_logs_warning_on_failure` (sa caplog) — svi sa `transaction=True` |
| AC7 (infinite loop guard + replace PDF) | `apps/media_pipeline/tests/test_signals.py` | `test_signal_does_not_loop_on_internal_save`, `test_post_save_regenerates_cover_when_pdf_replaced` (FIX iter-1 CRIT-3 — duplicirano sa AC3 tabelarno), `test_post_save_uses_on_commit_callback` (FIX iter-1 CRIT-5) |
| AC8 (regression — postojeći testovi) | sve postojeće test fajlove | Re-run `just test` — sve Story 2.1/2.2/2.3 baseline tests (broj uziman dinamički iz sprint-status.yaml — IMP iter-1 IMP-3) MORAJU PASS |
| AC9 (boundary regression) | `tests/integration/test_app_boundaries.py` | NEMA novih testova — postojeći Story 2.3 AC8 testovi (`test_media_pipeline_does_not_import_products`, `test_media_pipeline_does_not_import_brands`) pokrivaju Story 2.4 |
| AC10 (DoD + Dockerfile/pyproject verify) | Manual (Mihas) | `uv run ruff check . && uv run ruff format --check . && uv run djade --check templates/` exit code 0; `Get-Content compose/django/Dockerfile | Select-String "poppler-utils"` + `Get-Content pyproject.toml | Select-String "pdf2image\|pytest-mock\|pillow"` (FIX iter-1 CRIT-2 + IMP-5) |

**Specifični test scenariji za AC5 (signal integration — najkritičniji):**

```python
# IMP iter-1 IMP-2: transaction=True NUŽAN zbog FIX iter-1 CRIT-5 — render je deferred
# u transaction.on_commit() callback. Default @pytest.mark.django_db wraps test u
# savepoint koji nikada ne commit-uje → callback se NE poziva → test failuje.
@pytest.mark.django_db(transaction=True)
def test_post_save_generates_cover_thumbnail(realistic_pdf_bytes, temp_media_root, brand, subcategory):
    """Story 2.4 AC5 — full signal pipeline integration test."""
    from django.core.files.uploadedfile import SimpleUploadedFile
    from PIL import Image
    from apps.products.models import Product, ProductBrochure

    product = Product.objects.create(
        name="Test traktor TB-804",
        brand=brand,
        subcategory=subcategory,
    )
    pdf_upload = SimpleUploadedFile(
        "katalog.pdf",
        realistic_pdf_bytes,
        content_type="application/pdf",
    )
    brochure = ProductBrochure.objects.create(
        product=product,
        pdf_file=pdf_upload,
        title="Tehnička specifikacija",
    )
    brochure.refresh_from_db()

    # AC5 — cover je generated
    assert brochure.cover_thumbnail_image, "cover_thumbnail_image polje MORA biti populated"
    assert brochure.cover_thumbnail_image.name.endswith(".jpg")

    # AC2 — dimenzije ≤ 240×320 (aspect ratio preserved per Decision PDF-D3)
    with Image.open(brochure.cover_thumbnail_image.path) as img:
        assert img.width <= 240, f"width {img.width} > 240"
        assert img.height <= 320, f"height {img.height} > 320"
        assert img.format == "JPEG"
        assert img.mode == "RGB", "Force RGB konverzija per AC2"
```

**Specifični test scenariji za AC6 (graceful failure):**

```python
# IMP iter-1 IMP-2: transaction=True NUŽAN — render je u transaction.on_commit() callback-u.
@pytest.mark.django_db(transaction=True)
def test_post_save_graceful_failure_corrupt_pdf(caplog, temp_media_root, brand, subcategory):
    """Story 2.4 AC6 — corrupt PDF ne pucu save; logger.warning() fires."""
    import logging
    from django.core.files.uploadedfile import SimpleUploadedFile
    from apps.products.models import Product, ProductBrochure

    product = Product.objects.create(name="Test", brand=brand, subcategory=subcategory)

    with caplog.at_level(logging.WARNING, logger="apps.media_pipeline.pdf_utils"):
        brochure = ProductBrochure.objects.create(
            product=product,
            pdf_file=SimpleUploadedFile("corrupt.pdf", b"NOT_A_PDF_AT_ALL"),
        )

    brochure.refresh_from_db()
    assert not brochure.cover_thumbnail_image, "Cover MORA ostati prazan"
    assert brochure.id, "Brochure save MORA uspeti"

    # Logger asserij — barem jedan WARNING entry vezan za render failure
    warning_records = [r for r in caplog.records if r.levelno >= logging.WARNING]
    assert warning_records, "Mora postojati barem jedan WARNING log entry"
    assert any("Brochure cover render" in r.message for r in warning_records), \
        "WARNING message mora pominjati 'Brochure cover render'"
```

**dispatch_uid registration test pattern (IMP iter-1 IMP-7):**

Story 2.4 koristi `dispatch_uid="apps.media_pipeline.signals.handle_brochure_post_save"` u `post_save.connect()` pozivu (per AC4). TEA `test_apps.py` ekstenzija MORA verifikovati da je signal registrovan kroz introspekciju:

```python
def test_post_save_receiver_registered_with_dispatch_uid():
    """IMP iter-1 IMP-7: verifikuje da MediaPipelineConfig.ready() hook povezuje
    handler-a sa dispatch_uid string-om (sprečava double-registration)."""
    from django.db.models.signals import post_save
    from apps.products.models import ProductBrochure

    expected_uid = "apps.media_pipeline.signals.handle_brochure_post_save"
    # post_save.receivers je lista (key, weakref) tuplova; key je (id(receiver), id(sender))
    # za signal-e bez dispatch_uid, ili (hash(dispatch_uid), id(sender)) za one sa.
    # Live receivers ko-pis SAMO za live weakref-e.
    live = post_save._live_receivers(sender=ProductBrochure)
    # Bar jedan receiver iz media_pipeline modula MORA biti registrovan
    assert any(
        "media_pipeline" in receiver.__module__
        for receiver in live
    ), f"handle_brochure_post_save NIJE registrovan kao post_save receiver za ProductBrochure"
    # Asercija da je upravo handle_brochure_post_save:
    from apps.media_pipeline.signals import handle_brochure_post_save
    assert handle_brochure_post_save in live, \
        "handle_brochure_post_save nije u live_receivers — ready() hook nije izvršen ili dispatch_uid greška"
```

**Mock policy (per project-context.md § Mock policy):**

- **NEMA mock Django ORM ili PostgreSQL** — testovi koriste real test DB (`@pytest.mark.django_db`)
- **pdf2image NE mock-ovati** za integration test (`test_post_save_generates_cover_thumbnail`) — real PDF + real render je critical path
- **pdf2image MOŽE biti spy-ed kroz mocker.spy()** za AC7 infinite loop test (proveriti call_count, ne return value)
- **python-magic NE mock-ovati** — real PDF magic bytes detection je security critical
- **logger NE mock-ovati** — koristiti pytest `caplog` fixture za log assertion

**Performance smoke (NFR check):**

- Pojedinačni signal render (validan 1-stranica PDF) MORA biti **< 5 sekundi** u Docker testu (laptop spec). Ako sporo, proveriti dpi parameter — možda treba spustiti na 75.
- 10 paralelnih brochure save-ova (admin bulk upload) MOGU trajati ~30s ukupno (sync signal nije optimizovan za concurrency) — acceptable za v1 per Decision PDF-D4.

### Test discipline reminders

- **TEA piše testove (RED), Dev piše implementaciju (GREEN)** — Dev NIKAD ne piše testove za Story 2.4
- Testovi se commit-uju **pre** implementacije (red phase commit)
- Implementacija se commit-uje **posle** (green phase commit, zasebno)
- Failure: ako TEA testovi failuju posle Dev implementacije, story se vraća u `paused` status; Dev fix-uje implementaciju, NE testove

---

**End of Story 2.4 spec**
