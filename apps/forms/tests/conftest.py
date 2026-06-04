"""Story 4.1 — TEA RED phase conftest za apps/forms/ test suite.

Email testovi koriste pytest-django `mailoutbox` fixture (auto-postavlja Django
`locmem` backend → `django.core.mail.outbox`). NIKAD pravi network send
(project-context.md:267-271). DB testovi koriste real PostgreSQL test bazu
(`@pytest.mark.django_db`); NEMA `requires_postgres` marker (Lead NEMA FTS,
za razliku od 2-13 search).

Test data inline kroz `Lead.objects.create(...)` — NEMA `factory_boy` (nije dep).

Refs:
- 4-1-lead-model-smtp-setup.md Task 8 + AC1-AC9
- 4-1-interface-contract.md § 1 (tests) + TEA-D1/TEA-D2
"""

from __future__ import annotations

import io

import pytest
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils.translation import activate

_LOCMEM_CACHES = {
    "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
}


@pytest.fixture(autouse=True)
def _pin_and_clear_ratelimit_cache(settings):
    """Pinuje locmem `default` cache (deterministični django-ratelimit backend) i čisti
    brojač PRE i POSLE svakog forms testa.

    KRITIČNO za izolaciju: `htmx_post` koristi FIKSAN default IP (`203.0.113.7`), a
    LocMemCache je process-global → bez ovog clear-a ratelimit brojač za taj IP curi
    KROZ testove (success/error testovi u test_contact_view.py / _aria_live.py /
    _email_failure.py dele isti IP, ukupno >5 POST-ova u istom minutu → spurious 429 u
    GREEN fazi). Autouse na nivou forms conftest-a garantuje svežu 5/m kvotu po testu
    (SM-D10 / Task 3.3). Ratelimit-specifični test dodatno potvrđuje 5-ok/6-ti-429 granicu.
    """
    settings.CACHES = _LOCMEM_CACHES
    cache.clear()
    yield
    cache.clear()


@pytest.fixture(autouse=True)
def _isolate_media_root(settings, tmp_path):
    """Per-test MEDIA_ROOT isolation (established project pattern — media_pipeline/products).

    Story 4.4 LeadAttachment file-upload testovi pišu realne fajlove kroz FileSystemStorage
    (NEMA transakcionog rollback-a za disk). Bez per-test tmp_path izolacije, `kvar.jpg`
    basename curi KROZ testove → FileSystemStorage dodaje random suffix → testovi koji
    asertuju TAČAN basename (`name == "kvar.jpg"`) padaju nedeterministički.
    """
    settings.MEDIA_ROOT = str(tmp_path)


@pytest.fixture
def recipient_env(settings):
    """Popunjava per-segment recipient settings tako da rezolucija po form_type ima
    ne-prazan recipient (inače service tretira prazan recipient kao failed send — C1).

    Override-uje TAČNE settings atribute koje `send_lead_email` čita (SM-D7).
    """
    settings.CONTACT_EMAIL_TO = "kontakt@coricagrar.rs"
    settings.SERVICE_EMAIL_TO = "servis@coricagrar.rs"
    settings.PARTS_EMAIL_TO = "delovi@coricagrar.rs"
    settings.DEFAULT_FROM_EMAIL = "no-reply@coricagrar.rs"
    return settings


@pytest.fixture
def superuser(django_user_model):
    """Superuser za admin smoke testove."""
    return django_user_model.objects.create_superuser(
        username="admin_tea",
        email="admin@example.com",
        password="tea-pass-12345",
    )


# ── Story 4.2 (Opšta kontakt forma) — RED phase fixtures ─────────────────────


@pytest.fixture
def valid_contact_payload() -> dict:
    """Validan POST payload za ContactForm (Task 1.1). Puni dijakritik u `name`."""
    return {
        "name": "Marko Marković",
        "email": "marko@example.com",
        "phone": "+381641234567",
        "message": "Zanima me traktor.",
    }


@pytest.fixture
def contact_submit_url() -> str:
    """Reverse `forms:contact_submit` pod aktivnim `sr` (i18n_patterns prefiks /sr/).

    Hoist-ovan iz 4 test fajla (_submit_url duplikacija) — jedinstven izvor URL-a.
    """
    activate("sr")
    return reverse("forms:contact_submit")


@pytest.fixture
def htmx_post(client):
    """Helper: HTMX POST sa `HX-Request` header-om da `request.htmx` bude True.

    Django test client `HTTP_HX_REQUEST="true"` → django_htmx HtmxMiddleware postavlja
    `request.htmx`. REMOTE_ADDR fiksiran (ratelimit key='ip' stabilnost).
    """

    def _post(url: str, data: dict, *, ip: str = "203.0.113.7", **extra):
        return client.post(
            url,
            data,
            HTTP_HX_REQUEST="true",
            REMOTE_ADDR=ip,
            **extra,
        )

    return _post


# ── Story 4.3 (Model Inquiry forma) — RED phase fixtures ─────────────────────


@pytest.fixture
def model_inquiry_payload() -> dict:
    """Validan POST payload za ModelInquiryForm (Task 1.1) BEZ `product_slug`.

    `product_slug` se popunjava per-test iz fixture product-a (`{**model_inquiry_payload,
    "product_slug": product.slug}`) jer slug zavisi od kreiranog Product-a u svakom testu.
    Puni dijakritik u `name`/`message` (project-context anti-šišana-latinica).
    """
    return {
        "name": "Marko Marković",
        "email": "marko@example.com",
        "phone": "+381641234567",
        "message": "Zanima me ovaj model.",
    }


@pytest.fixture
def model_inquiry_submit_url() -> str:
    """Reverse `forms:model_inquiry_submit` pod aktivnim `sr` (i18n_patterns prefiks /sr/)."""
    activate("sr")
    return reverse("forms:model_inquiry_submit")


@pytest.fixture
def published_product(db):
    """Objavljen Product „Agri Tracking TB804" — kanonski model-inquiry fixture.

    Hoist-ovan iz ~25 inline `ProductFactory.create(name="Agri Tracking TB804")` poziva
    kroz 4.3 test fajlove (TEA cleanup). `db` zavisnost jer factory dira DB.
    """
    from apps.products.tests.factories import ProductFactory

    return ProductFactory.create(name="Agri Tracking TB804")


# ── Story 4.4 (Servisni zahtev forma sa foto upload-om) — RED phase fixtures ──


def _pillow_upload(fmt: str, content_type: str, filename: str) -> SimpleUploadedFile:
    """Generiše VALIDNU malu sliku kroz Pillow in-memory → SimpleUploadedFile.

    Mala (10×10) validna slika koja PROLAZI `validate_image_mime` MIME-signature +
    Pillow `verify()` (za jpeg/png; webp se odbija na nivou `allowed_mimes`, NE
    na signature/verify grani — slika je validna, samo nije dozvoljen tip).
    """
    from PIL import Image

    buffer = io.BytesIO()
    Image.new("RGB", (10, 10), color=(34, 64, 47)).save(buffer, format=fmt)
    buffer.seek(0)
    return SimpleUploadedFile(filename, buffer.read(), content_type=content_type)


@pytest.fixture
def service_request_payload() -> dict:
    """Validan POST payload za ServiceRequestForm (Task 1.1) BEZ `photos`.

    `photos` se dodaje per-test kao lista `SimpleUploadedFile`-ova
    (`{**service_request_payload, "photos": [valid_image_jpeg, ...]}`). Pun dijakritik
    u `name`/`brand_model`/`description` (project-context anti-šišana-latinica).
    """
    return {
        "name": "Stojan Stojanović",
        "phone": "+381641234567",
        "email": "stojan@example.com",
        "machine_type": "tractor",
        "brand_model": "Agri Tracking TB804",
        "description": "Curi ulje iz hidraulike.",
    }


@pytest.fixture
def service_request_submit_url() -> str:
    """Reverse `forms:service_request_submit` pod aktivnim `sr` (i18n_patterns prefiks /sr/)."""
    activate("sr")
    return reverse("forms:service_request_submit")


@pytest.fixture
def valid_image_jpeg() -> SimpleUploadedFile:
    """Validna mala JPEG slika kroz Pillow (prolazi MIME-signature + Pillow verify)."""
    return _pillow_upload("JPEG", "image/jpeg", "kvar.jpg")


@pytest.fixture
def valid_image_png() -> SimpleUploadedFile:
    """Validna mala PNG slika kroz Pillow."""
    return _pillow_upload("PNG", "image/png", "kvar.png")


@pytest.fixture
def valid_image_webp() -> SimpleUploadedFile:
    """Validna mala WEBP slika — služi za „webp odbijen jer NIJE u allowed_mimes" assertion.

    Slika je struktura-validna (Pillow je prihvata), ali `allowed_mimes` je pinovan na
    `("image/jpeg","image/png")` u formi, pa MIME-signature provera odbija webp.
    """
    return _pillow_upload("WEBP", "image/webp", "kvar.webp")


@pytest.fixture
def oversized_image() -> SimpleUploadedFile:
    """VALIDNA mala JPEG sa FORSIRANIM `.size` > 5 MB (Task 1.1 rationale).

    Sirov 5 MB `BytesIO` nula NIJE validna slika → pao bi PRVO na MIME-signature /
    Pillow `verify()` grani i raise-ovao POGREŠNU grešku (NE „5 MB" size poruku). Samo
    validna mala slika sa naduvanim `.size` pouzdano okida size-limit granu u
    `validate_image_mime` (koja proverava `upload.size` PRE čitanja sadržaja) i „5 MB" poruku.
    """
    upload = _pillow_upload("JPEG", "image/jpeg", "velika.jpg")
    upload.size = 6 * 1024 * 1024  # > 5 MB limit — forsira size-limit granu
    return upload


@pytest.fixture
def oversized_image_real() -> SimpleUploadedFile:
    """VALIDNA JPEG čiji REALAN broj bajtova prelazi 5 MB (preživi test-client round-trip).

    `oversized_image` forsira `.size` atribut, ali Django test client serijalizuje fajl kroz
    `file.read()` (encode_file) — forsiran `.size` se NE prenosi preko HTTP granice, a server
    rekonstruiše `UploadedFile` čiji `.size` = stvaran broj bajtova. Za ENDPOINT-nivo oversized
    test (`htmx_post` round-trip) mora postojati fajl sa STVARNO > 5 MB sadržajem, inače mala
    validna slika prođe size granu i Lead se kreira (test bi bio neostvariv).

    Random-noise 2600×2600 JPEG (quality=100) ≈ 12 MB > 5 MB; 6.76M px < `Image.MAX_IMAGE_PIXELS`
    (50M decompression-bomb guard u validate_image_mime) → prolazi MIME+Pillow, pada SAMO na size grani.
    """
    import os

    from PIL import Image

    dim = 2600
    img = Image.frombytes("RGB", (dim, dim), os.urandom(dim * dim * 3))
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=100)
    buffer.seek(0)
    data = buffer.read()
    assert len(data) > 5 * 1024 * 1024, (
        f"oversized_image_real MORA biti > 5 MB realnih bajtova (round-trip safe), "
        f"dobio {len(data) / 1024 / 1024:.2f} MB."
    )
    return SimpleUploadedFile("velika-realna.jpg", data, content_type="image/jpeg")


@pytest.fixture
def non_image_file() -> SimpleUploadedFile:
    """Ne-slika fajl (PDF content-type + PDF signature) — MIME-signature mismatch.

    `validate_image_mime` python-magic signature check detektuje application/pdf koji
    NIJE u allowed_mimes → ValidationError (NE oslanja se na ekstenziju).
    """
    return SimpleUploadedFile(
        "dokument.pdf",
        b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n1 0 obj\n<< >>\nendobj\n",
        content_type="application/pdf",
    )
