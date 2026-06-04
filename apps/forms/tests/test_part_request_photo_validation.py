"""Story 4.5 — AC2: foto upload double-check (MIME + Pillow + size, single-file) — TEA RED.

Pokriva AC2 / Task 2.2 (KRITIČNO — security must-have; single-file `clean_photo`):
- 0 slika → valid (opciono; clean_photo vraća prazno bez poziva util-a);
- 1 validna JPG/PNG → valid;
- > 5 MB slika (`oversized_image` — FORM-nivo forsiran `.size`) → invalid, greška sadrži „5 MB";
- ne-slika fajl (PDF) → invalid (MIME-signature odbija, NE ekstenzija);
- corrupt „slika" (random bytes, image/jpeg content_type, Pillow verify pada) → invalid;
- webp odbijen jer NIJE u allowed_mimes (pinovan jpeg/png) — allowed_mimes EXCLUSION;
- `clean_photo` MORA pozvati `validate_image_mime` sa allowed_mimes=("image/jpeg","image/png")
  i max_size_bytes=5*1024*1024 (spy — behavior + signature assertion).

Story-ova `clean_photo` radi strukturnu size pre-proveru („Slika je veća od 5 MB. Probajte manju.")
PRE poziva util-a — substring „5 MB" je zadovoljen iz BILO KOG izvora (Task 2.2 napomena).

RED razlog: `apps.forms.forms.PartRequestForm` ne postoji → ImportError → SVE padaju.

Pokrenuti:
    just test apps/forms/tests/test_part_request_photo_validation.py -v

Refs: 4-5 AC2 + Task 2.2 + SM-D4; interface-contract § 2.
"""

from __future__ import annotations

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils.datastructures import MultiValueDict

pytestmark = pytest.mark.django_db


def _base_data() -> dict:
    return {
        "tractor_model": "Agri Tracking TB804",
        "part_name": "Filter ulja",
        "extra_description": "Original deo.",
        "name": "Marko Marković",
        "phone": "+381641234567",
        "email": "marko@example.com",
        "payment_method": "cod",
        "delivery_method": "delivery",
        "note": "Pozovite popodne.",
    }


def _make_form(photo=None):
    """Bind PartRequestForm sa JEDNIM `photo` fajlom (single-file putanja; NE lista)."""
    from apps.forms.forms import PartRequestForm

    files = MultiValueDict()
    if photo is not None:
        files["photo"] = photo
    return PartRequestForm(_base_data(), files)


def _errors_text(form) -> str:
    return " ".join(str(e) for errs in form.errors.values() for e in errs)


# AC-2: 0 slika → valid (foto opciono; clean_photo NE poziva util na praznom)
def test_zero_photo_is_valid():
    form = _make_form(None)
    assert form.is_valid(), f"0 slika MORA biti valid (foto opciono — AC2), errors={form.errors!r}."


# AC-2: 1 validna JPG → valid
def test_single_valid_jpeg_is_valid(valid_image_jpeg):
    form = _make_form(valid_image_jpeg)
    assert form.is_valid(), f"1 validna JPG MORA biti valid (AC2), errors={form.errors!r}."


# AC-2: 1 validna PNG → valid
def test_single_valid_png_is_valid(valid_image_png):
    form = _make_form(valid_image_png)
    assert form.is_valid(), f"1 validna PNG MORA biti valid (AC2), errors={form.errors!r}."


# AC-2: > 5 MB slika → invalid, greška sadrži substring „5 MB"
def test_oversized_photo_rejected(oversized_image):
    form = _make_form(oversized_image)
    assert not form.is_valid(), "Slika > 5 MB MORA biti odbijena (AC2)."
    assert "5 MB" in _errors_text(form), (
        f"Greška za prevelik fajl MORA sadržati substring '5 MB' (konkretan limit — AC2), "
        f"dobio {_errors_text(form)!r}."
    )


# AC-2: ne-slika fajl (PDF) → invalid (MIME-signature odbija, NE ekstenzija)
def test_non_image_file_rejected(non_image_file):
    form = _make_form(non_image_file)
    assert not form.is_valid(), (
        "PDF (ne-slika) MORA biti odbijen MIME-signature proverom (NE ekstenzijom — AC2 security)."
    )
    assert "photo" in form.errors, (
        f"Greška za ne-sliku MORA biti na `photo`, dobio {form.errors!r}."
    )


# AC-2: corrupt „slika" (random bytes, image/jpeg content_type) → invalid (Pillow verify / signature pada)
def test_corrupt_image_rejected():
    corrupt = SimpleUploadedFile(
        "corrupt.jpg", b"\xff\xd8\xff\xe0nije-validna-slika-vec-djubre", content_type="image/jpeg"
    )
    form = _make_form(corrupt)
    assert not form.is_valid(), (
        "Corrupt slika (Pillow verify pada / MIME signature ne prepoznaje) MORA biti odbijena (AC2)."
    )


# AC-2: webp odbijen jer NIJE u allowed_mimes (pinovan jpeg/png) — allowed_mimes EXCLUSION.
# NAPOMENA: webp je STRUKTURNO validna slika (PROLAZI MIME-signature + Pillow verify) — odbija
# se ISKLJUČIVO jer nije u pinovanom skupu ("image/jpeg","image/png"), NE zbog corrupt/Pillow-fail.
def test_webp_rejected_not_in_allowed_mimes(valid_image_webp):
    form = _make_form(valid_image_webp)
    assert not form.is_valid(), (
        "Validan WEBP MORA biti odbijen jer allowed_mimes je pinovan na ('image/jpeg','image/png') "
        "(NE default koji uključuje webp — AC2/SM-D4). Ovo dokazuje da forma prosleđuje pinovan "
        "allowed_mimes argument (EXCLUSION, ne Pillow/signature fail)."
    )


# AC-2: clean_photo poziva validate_image_mime sa pinovanim argumentima (allowed_mimes jpeg/png + 5MB).
# Spy potvrđuje TAČNE keyword argumente (behavior + signature assertion).
def test_clean_calls_validate_image_mime_with_pinned_args(valid_image_jpeg, mocker):
    spy = mocker.patch(
        "apps.forms.forms.validate_image_mime", autospec=True, return_value=None
    )
    form = _make_form(valid_image_jpeg)
    form.is_valid()

    assert spy.call_count >= 1, (
        "clean_photo MORA pozvati validate_image_mime za priloženu sliku (REUSE 2.3 — AC2). "
        "Ako count==0, forma ne radi double-check (anti-pattern)."
    )
    _args, kwargs = spy.call_args
    assert tuple(kwargs.get("allowed_mimes", ())) == ("image/jpeg", "image/png"), (
        f"validate_image_mime MORA biti pozvan sa allowed_mimes=('image/jpeg','image/png') "
        f"(NE default sa webp — AC2/SM-D4), dobio {kwargs.get('allowed_mimes')!r}."
    )
    assert kwargs.get("max_size_bytes") == 5 * 1024 * 1024, (
        f"validate_image_mime MORA biti pozvan sa max_size_bytes=5*1024*1024 (SM-D4 — "
        f"NE default 10 MB), dobio {kwargs.get('max_size_bytes')!r}."
    )


# AC-2: prazna slika NE poziva util (clean_photo vraća prazno bez double-check-a na None)
def test_empty_photo_does_not_call_util(mocker):
    spy = mocker.patch(
        "apps.forms.forms.validate_image_mime", autospec=True, return_value=None
    )
    form = _make_form(None)
    form.is_valid()
    assert spy.call_count == 0, (
        "clean_photo NE SME pozvati validate_image_mime kad slika nije priložena (opciono — AC2)."
    )
