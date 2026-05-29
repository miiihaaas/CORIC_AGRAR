"""Shared utility helpers for app-level cross-cutting concerns.

Story 2.1 — uvodi `slugify_ascii()` koji transliterise srpsku latinicu
(Ć/Č/Š/Ž/Đ + digrafovi Dž/Lj/Nj) u ASCII pa primenjuje Django slugify.
"""

from django.utils.text import slugify

# Srpska latinica digrafovi — MORAJU se zameniti PRE str.maketrans()
# jer str.maketrans(dict) zahteva single-character ključeve.
# Naivan pokušaj str.maketrans({"Dž": "dz", ...}) raise-uje
# ValueError: string keys in translate table must be of length 1
# pri module-level evaluation. Vidi Gotcha BR-14 i Task 2.4.
SR_DIGRAPHS = {
    "Dž": "Dz",
    "dž": "dz",
    "Lj": "Lj",
    "lj": "lj",
    "Nj": "Nj",
    "nj": "nj",
}

# Single-character dijakritici — preko str.maketrans
SR_DIAKRITICI = str.maketrans(
    {
        "Ć": "C",
        "ć": "c",
        "Č": "C",
        "č": "c",
        "Š": "S",
        "š": "s",
        "Ž": "Z",
        "ž": "z",
        "Đ": "D",
        "đ": "d",
    }
)


def slugify_ascii(text: str) -> str:
    """ASCII-only slug per project-context.md § Slugovi.

    Two-stage replacement:
    1. Multi-character digrafovi (Dž/Lj/Nj) preko str.replace()
    2. Single-character dijakritici (Ć/Č/Š/Ž/Đ) preko str.translate()
    Zatim Django default slugify sa allow_unicode=False.
    """
    if not text:
        return ""
    for src, dst in SR_DIGRAPHS.items():
        text = text.replace(src, dst)
    text = text.translate(SR_DIAKRITICI)
    return slugify(text, allow_unicode=False)
