"""Story 4.4 — AC3: foto upload double-check (MIME + Pillow + size + count) — TEA RED.

Pokriva AC3 / Task 2.2 (KRITIČNO — security must-have):
- > 3 slike → invalid, greška sadrži „najviše 3";
- > 5 MB slika → invalid, greška sadrži substring „5 MB";
- ne-slika fajl (PDF) → invalid (MIME-signature odbija, NE ekstenzija);
- corrupt „slika" (random bytes, image/jpeg content_type, Pillow verify pada) → invalid;
- 3 validne slike → valid (granica inkluzivna);
- 0 slika → valid (opciono);
- webp odbijen jer NIJE u allowed_mimes (pinovan jpeg/png);
- MIXED-BATCH all-or-nothing: 1 validna + 1 nevalidna → invalid (NIKAD partial-accept).

`clean_photos` MORA pozvati `validate_image_mime` sa allowed_mimes=("image/jpeg","image/png")
i max_size_bytes=5*1024*1024 (behavior-assertovano: webp se odbija → dokazuje allowed_mimes pin).

RED razlog: `apps.forms.forms.ServiceRequestForm` ne postoji → ImportError → SVE padaju.

Pokrenuti:
    just test apps/forms/tests/test_service_request_photo_validation.py -v

Refs: 4-4 AC3 + Task 2.2 + SM-D4/SM-D15; interface-contract § 2.
"""

from __future__ import annotations

import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils.datastructures import MultiValueDict

pytestmark = pytest.mark.django_db


def _jpeg(name="kvar.jpg"):
    from PIL import Image

    buffer = io.BytesIO()
    Image.new("RGB", (10, 10), color=(34, 64, 47)).save(buffer, format="JPEG")
    buffer.seek(0)
    return SimpleUploadedFile(name, buffer.read(), content_type="image/jpeg")


def _make_form(photos):
    """Bind ServiceRequestForm sa listom `photos` fajlova (multi-file getlist putanja)."""
    from apps.forms.forms import ServiceRequestForm

    data = {
        "name": "Stojan Stojanović",
        "phone": "+381641234567",
        "email": "stojan@example.com",
        "machine_type": "tractor",
        "brand_model": "Agri Tracking TB804",
        "description": "Curi ulje iz hidraulike.",
    }
    files = MultiValueDict({"photos": list(photos)})
    return ServiceRequestForm(data, files)


def _errors_text(form) -> str:
    return " ".join(str(e) for errs in form.errors.values() for e in errs)


# AC-3: 0 slika → valid (foto je opciono)
def test_zero_photos_is_valid():
    form = _make_form([])
    assert form.is_valid(), f"0 slika MORA biti valid (foto opciono), errors={form.errors!r}."


# AC-3: 3 validne slike → valid (granica inkluzivna do 3)
def test_three_valid_photos_is_valid():
    form = _make_form([_jpeg("a.jpg"), _jpeg("b.jpg"), _jpeg("c.jpg")])
    assert form.is_valid(), (
        f"3 validne JPG slike MORAJU biti valid (granica je inkluzivna do 3 — AC3), "
        f"errors={form.errors!r}."
    )


# AC-3: > 3 slike → invalid, greška sadrži „najviše 3"
def test_more_than_three_photos_rejected():
    form = _make_form([_jpeg("a.jpg"), _jpeg("b.jpg"), _jpeg("c.jpg"), _jpeg("d.jpg")])
    assert not form.is_valid(), "4 slike MORAJU biti odbijene (do 3 — AC3)."
    assert "najviše 3" in _errors_text(form), (
        f"Greška za > 3 slike MORA sadržati 'najviše 3' (epics.md:814), dobio {_errors_text(form)!r}."
    )


# AC-3: > 5 MB slika → invalid, greška sadrži substring „5 MB"
def test_oversized_photo_rejected(oversized_image):
    form = _make_form([oversized_image])
    assert not form.is_valid(), "Slika > 5 MB MORA biti odbijena (AC3)."
    assert "5 MB" in _errors_text(form), (
        f"Greška za prevelik fajl MORA sadržati substring '5 MB' (konkretan limit — AC3), "
        f"dobio {_errors_text(form)!r}."
    )


# AC-3: ne-slika fajl (PDF) → invalid (MIME-signature odbija, NE ekstenzija)
def test_non_image_file_rejected(non_image_file):
    form = _make_form([non_image_file])
    assert not form.is_valid(), (
        "PDF (ne-slika) MORA biti odbijen MIME-signature proverom (NE ekstenzijom — AC3 security)."
    )
    assert "photos" in form.errors, (
        f"Greška za ne-sliku MORA biti na `photos`, dobio {form.errors!r}."
    )


# AC-3: corrupt „slika" (random bytes, image/jpeg content_type) → invalid (Pillow verify pada)
def test_corrupt_image_rejected():
    corrupt = SimpleUploadedFile(
        "corrupt.jpg", b"\xff\xd8\xff\xe0nije-validna-slika-vec-djubre", content_type="image/jpeg"
    )
    form = _make_form([corrupt])
    assert not form.is_valid(), (
        "Corrupt slika (Pillow verify pada / MIME signature ne prepoznaje) MORA biti odbijena (AC3)."
    )


# AC-3: webp odbijen jer NIJE u allowed_mimes (pinovan jpeg/png) — dokazuje allowed_mimes pin
def test_webp_rejected_not_in_allowed_mimes(valid_image_webp):
    form = _make_form([valid_image_webp])
    assert not form.is_valid(), (
        "Validan WEBP MORA biti odbijen jer allowed_mimes je pinovan na ('image/jpeg','image/png') "
        "(NE default koji uključuje webp — AC3/SM-D4). Ovo dokazuje da forma prosleđuje pinovan "
        "allowed_mimes argument."
    )


# AC-3 (KRITIČNO): MIXED-BATCH all-or-nothing — 1 validna + 1 nevalidna (PDF) → invalid
def test_mixed_batch_valid_plus_non_image_rejected(valid_image_jpeg, non_image_file):
    form = _make_form([valid_image_jpeg, non_image_file])
    assert not form.is_valid(), (
        "MIXED-BATCH (1 validna JPG + 1 PDF) MORA biti ODBIJEN U CELOSTI — all-or-nothing "
        "(NIKAD partial-accept; AC3/AC7/SM-D4). clean MORA raise-ovati na PRVOM nevalidnom fajlu."
    )


# AC-3 (KRITIČNO): MIXED-BATCH all-or-nothing — 1 validna + 1 prevelika (>5MB) → invalid
def test_mixed_batch_valid_plus_oversized_rejected(valid_image_jpeg, oversized_image):
    form = _make_form([valid_image_jpeg, oversized_image])
    assert not form.is_valid(), (
        "MIXED-BATCH (1 validna JPG + 1 > 5 MB) MORA biti ODBIJEN U CELOSTI — all-or-nothing "
        "(AC3/SM-D4)."
    )
    assert "5 MB" in _errors_text(form), (
        f"MIXED-BATCH sa prevelikim fajlom MORA nositi '5 MB' grešku, dobio {_errors_text(form)!r}."
    )


# AC-3: validate_image_mime se poziva sa pinovanim argumentima (allowed_mimes jpeg/png + 5MB).
# Spy potvrđuje TAČNE keyword argumente (behavior + signature assertion).
def test_clean_calls_validate_image_mime_with_pinned_args(valid_image_jpeg, mocker):
    spy = mocker.patch(
        "apps.forms.forms.validate_image_mime", autospec=True, return_value=None
    )
    form = _make_form([valid_image_jpeg])
    form.is_valid()

    assert spy.call_count >= 1, (
        "clean_photos MORA pozvati validate_image_mime za svaki fajl (REUSE 2.3 — AC3). "
        "Ako count==0, forma ne radi double-check (anti-pattern)."
    )
    _args, kwargs = spy.call_args
    assert tuple(kwargs.get("allowed_mimes", ())) == ("image/jpeg", "image/png"), (
        f"validate_image_mime MORA biti pozvan sa allowed_mimes=('image/jpeg','image/png') "
        f"(NE default sa webp — AC3/SM-D4), dobio {kwargs.get('allowed_mimes')!r}."
    )
    assert kwargs.get("max_size_bytes") == 5 * 1024 * 1024, (
        f"validate_image_mime MORA biti pozvan sa max_size_bytes=5*1024*1024 (epics.md:815 — "
        f"NE default 10 MB), dobio {kwargs.get('max_size_bytes')!r}."
    )
