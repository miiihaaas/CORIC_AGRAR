"""Reproducibilan konverzioni alat: statički JPG → AVIF + WebP varijante (Story 9.10).

STATIC slike (`static/img/...`) NEMAJU build pipeline i NISU `ImageField` → sorl-thumbnail
ih NE procesira. Zato LCP hero (`static/img/home/home-hero-1.jpg`) dobija RUČNO-pisani
`<picture>` sa PRE-GENERISANIM `.avif` + `.webp` + `.jpg` varijantama KOMITOVANIM u repo.
Ovaj command je reproducibilan asset-korak (NE ručno-jednokratan) za njihovo generisanje.

Tooling: Pillow native AVIF + WebP (`PIL.features.check('avif')`/`check('webp')`). Nema
`cwebp`/`avifenc`/`pillow_avif` dep-a (YAGNI — native Pillow pokriva oba).

Idempotentnost (AC5): "idempotentno" == **SKIP-IF-EXISTS** (ponovno pokretanje NE menja
već-komitovani output osim ako se prosledi `--force`). Ovo NIJE bit-reproducibilan re-encode:
Pillow AVIF/WebP enkoderi NISU garantovano byte-identični preko verzija/run-ova — NE jurimo
bit-reproducibilnost, samo deterministički skip-if-exists kontrakt.

Size-guard (AC1): posle svakog encode-a uporedi `dst` veličinu sa source JPG-om; ako je
`dst >= src` → fail-loud (CommandError, non-zero exit). Varijanta `>=` source-a se NE sme
tiho komitovati. Override: `--allow-larger`. Best-effort: ako je prvi AVIF encode veći od
source-a, command spušta `quality=` i re-enkoduje pre nego što fail-uje.

Pokretanje:
    python manage.py convert_static_images
    python manage.py convert_static_images --force          # regeneriši postojeće
    python manage.py convert_static_images --allow-larger    # dozvoli varijantu >= source
    python manage.py convert_static_images --source static/img/home/home-hero-1.jpg
"""

from __future__ import annotations

import os
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from PIL import Image, features

# Default target: minimalno LCP hero. Konfigurabilno preko --source / --glob.
DEFAULT_SOURCES = ("static/img/home/home-hero-1.jpg",)

# AVIF je znatno efikasniji od JPG-a za fotografski sadržaj; WebP malo manje.
# Početni quality; size-guard re-enkoduje sa nižim ako je prvi encode prevelik.
AVIF_QUALITY = 60
WEBP_QUALITY = 80
# Best-effort step-down skala kad je AVIF encode >= source.
_AVIF_RETRY_QUALITIES = (50, 40, 30)


class Command(BaseCommand):
    help = (
        "Konvertuje statičke JPG slike (default: LCP hero home-hero-1.jpg) u "
        ".avif + .webp varijante pored source-a (Pillow native AVIF/WebP). "
        "Idempotentno = skip-if-exists (--force regeneriše). Size-guard: "
        "varijanta >= source fail-uje osim sa --allow-larger."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--source",
            action="append",
            default=None,
            help=(
                "Relativni path (od repo root-a) source JPG-a. Može više puta. "
                "Default: static/img/home/home-hero-1.jpg."
            ),
        )
        parser.add_argument(
            "--glob",
            default=None,
            help="Glob pattern (od repo root-a), npr. 'static/img/home/*.jpg'.",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Regeneriši čak i ako .avif/.webp već postoje (default: skip-if-exists).",
        )
        parser.add_argument(
            "--allow-larger",
            action="store_true",
            help=(
                "Dozvoli komitovanje varijante koja je >= source JPG (override "
                "size-guard-a). Bez ovog flag-a, varijanta >= source-a NE sme da se piše."
            ),
        )

    def handle(self, *args, **options):
        # GUARD (fail-loud, NE tiho preskoči): Pillow mora imati native AVIF + WebP.
        if not features.check("avif"):
            raise CommandError(
                "Pillow NEMA native AVIF podršku (features.check('avif')==False). "
                "Instaliraj Pillow >= 11 sa AVIF-om ili pillow-avif-plugin. Fail-loud."
            )
        if not features.check("webp"):
            raise CommandError(
                "Pillow NEMA native WebP podršku (features.check('webp')==False). "
                "Fail-loud — NE komitujemo bez obe varijante."
            )

        repo_root = Path(settings.BASE_DIR)
        sources = self._resolve_sources(repo_root, options)
        if not sources:
            raise CommandError("Nijedan source JPG nije pronađen za konverziju.")

        force = options["force"]
        allow_larger = options["allow_larger"]

        for src in sources:
            if not src.exists():
                raise CommandError(f"Source JPG ne postoji: {src}")
            src_size = os.stat(src).st_size
            self._convert_one(
                src, src_size, force=force, allow_larger=allow_larger, ext=".avif",
                fmt="AVIF", quality=AVIF_QUALITY, retry_qualities=_AVIF_RETRY_QUALITIES,
            )
            self._convert_one(
                src, src_size, force=force, allow_larger=allow_larger, ext=".webp",
                fmt="WEBP", quality=WEBP_QUALITY, retry_qualities=(70, 60, 50),
            )

        self.stdout.write(self.style.SUCCESS("convert_static_images: gotovo."))

    def _resolve_sources(self, repo_root: Path, options) -> list[Path]:
        rels: list[str] = []
        if options.get("glob"):
            return sorted(repo_root.glob(options["glob"]))
        if options.get("source"):
            rels = list(options["source"])
        else:
            rels = list(DEFAULT_SOURCES)
        return [repo_root / r for r in rels]

    def _convert_one(
        self, src: Path, src_size: int, *, force: bool, allow_larger: bool,
        ext: str, fmt: str, quality: int, retry_qualities: tuple[int, ...],
    ) -> None:
        dst = src.with_suffix(ext)

        # IDEMPOTENCIJA — skip-if-exists default; --force regeneriše. (NE bit-reproducibilno.)
        if dst.exists() and not force:
            self.stdout.write(
                f"SKIP (postoji, skip-if-exists): {dst.name} (koristi --force za regen)"
            )
            return

        with Image.open(src) as im:
            # STYLE guard: alpha/palette drop pri convert("RGB") je tih — upozori
            # ako future --source nije već RGB/L (npr. PNG sa alfa kanalom).
            if im.mode not in ("RGB", "L"):
                self.stdout.write(
                    self.style.WARNING(
                        f"UPOZORENJE: {src.name} mode={im.mode!r} (ne RGB/L) — "
                        f"convert('RGB') odbacuje alpha/palette informaciju."
                    )
                )
            im = im.convert("RGB")
            self._encode_with_size_guard(
                im, src, dst, src_size, fmt=fmt, quality=quality,
                retry_qualities=retry_qualities, allow_larger=allow_larger,
            )

    def _encode_with_size_guard(
        self, im, src: Path, dst: Path, src_size: int, *, fmt: str, quality: int,
        retry_qualities: tuple[int, ...], allow_larger: bool,
    ) -> None:
        # Best-effort: encode na početnom quality-ju; ako je dst >= src, spusti quality
        # i re-enkoduj dok ne postane striktno manji ili dok ne potrošimo retry skalu.
        tmp = dst.with_suffix(dst.suffix + ".tmp")
        last_size = 0  # sentinel: 0 znači „nijedan encode još nije izmeren"
        try:
            for q in (quality, *retry_qualities):
                im.save(tmp, format=fmt, quality=q)
                last_size = os.stat(tmp).st_size
                if last_size < src_size:
                    os.replace(tmp, dst)  # atomic success path — tmp je „potrošen"
                    pct = 100.0 * (1 - last_size / src_size)
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"OK {dst.name}: {last_size} B (q={q}) vs JPG {src_size} B "
                            f"(-{pct:.1f}%)"
                        )
                    )
                    return

            # Sve quality vrednosti dale >= source. Honesty: NE komituj tiho.
            if allow_larger:
                os.replace(tmp, dst)  # atomic override path — tmp „potrošen"
                self.stdout.write(
                    self.style.WARNING(
                        f"ALLOW-LARGER: {dst.name} = {last_size} B >= JPG {src_size} B "
                        f"(override aktivan)."
                    )
                )
                return
        finally:
            # Cleanup: ako im.save() baci ILI nijedan branch ne uspe (>= source bez
            # override-a), .tmp NE sme da procuri. os.replace na success path-u je
            # već premestio tmp → unlink(missing_ok) je tada no-op.
            if tmp.exists():
                tmp.unlink(missing_ok=True)

        raise CommandError(
            f"{dst.name} ({last_size} B) je >= source JPG ({src_size} B) čak i na "
            f"najnižem quality-ju. Varijanta >= source-a se NE komituje. "
            f"Spusti quality dalje ili prosledi --allow-larger ako je namerno."
        )
