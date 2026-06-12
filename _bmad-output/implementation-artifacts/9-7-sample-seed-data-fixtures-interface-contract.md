# Interface Contract — Story 9-7: Sample Seed Data (`seed_sample_data`)

> TEA RED-phase contract. This is the SPECIFICATION the Dev (GREEN) must satisfy.
> Tests live at `apps/core/tests/test_seed_sample_data.py`. Every assertion below is a
> requirement. Numbers are copied VERBATIM from the story manifest
> (`_bmad-output/implementation-artifacts/9-7-sample-seed-data-fixtures.md`).

## Command

- **Name:** `seed_sample_data`
- **Invocation:** `from django.core.management import call_command; call_command("seed_sample_data")`
- **File:** `apps/core/management/commands/seed_sample_data.py`
- **Package files (MUST exist or Django won't discover the command, G-9):**
  - `apps/core/management/__init__.py`
  - `apps/core/management/commands/__init__.py`
- **Class:** `class Command(BaseCommand)` with `handle(self, *args, **options)`.
- Models imported via DIRECT import (`from apps.products.models import Product`, etc.) — NOT
  `apps.get_model` (this is a runtime management utility, not a historical migration).

## Flags

- `--force` (`action="store_true"`) — bypasses the production guard. Default `False`.
  Invoked in tests as `call_command("seed_sample_data", force=True)`.

## Production guard (SM-D2, MANDATORY)

```python
if not settings.DEBUG and not options["force"]:
    raise CommandError("seed_sample_data je DEV-only; odbijam izvršavanje sa DEBUG=False bez --force")
```

- `DEBUG=False` + no `--force` → raises `django.core.management.base.CommandError`.
- `DEBUG=False` + `force=True` → proceeds, objects created.
- `DEBUG=True` (default test settings `config.settings.development`) → proceeds, no `--force` needed.
- The guard is the FIRST thing `handle()` does, BEFORE any DB write.

## Atomicity (Dev Note "Atomicity")

- Seeding wrapped in `with django.db.transaction.atomic():` (all-or-nothing). SUCCESS summary
  written to stdout only AFTER successful commit.

## Idempotency (SM-D3 / Dev Note "slug je UVEK eksplicitan lookup ključ")

- Every object created via `get_or_create` with the natural unique key as the EXPLICIT lookup
  kwarg: `slug=...` for Brand / brands.Category / Subcategory / Product / blog.Post / blog.Category
  / blog.Tag; `pk=1` for `SiteSettings`.
- `slug` NEVER derived inside `defaults`. All other fields (incl. `name`/`name_sr` etc.) go in `defaults`.
- Running twice creates NO duplicates and raises NO exception. After the 2nd run the exact
  manifest-slug objects still resolve and keep `is_published=True` (no delete-recreate-different-PK).

## Modeltranslation (SM-D4)

- For every translatable field, set BOTH the base accessor and the `_sr` column in the SAME
  `defaults` dict (mirror `apps/brands/migrations/0004`): `name`+`name_sr`, `description`+`description_sr`,
  `title`+`title_sr`, `perex`+`perex_sr`, `body`+`body_sr`, `key_features`+`key_features_sr`.
- All Serbian user-facing text uses FULL diacritics (č/ć/ž/š/đ) — never šišana latinica, never Cyrillic.
- All NEW slugs are ASCII `^[a-z0-9-]+$`.

## Additive / no-collision (SM-D5)

Command references existing migration-seeded objects via `get_or_create` (does NOT duplicate or
delete): Brands `jeegee`/`hzm`/`tulip`; brands.Categories
`osnovna-obrada-zemljista`/`priprema-zemljista`/`masine-za-setvu`/`radne-masine`; Products
`tulip-mix-6m3`/`tulip-mix-8m3`. Each remains exactly 1 instance after seeding.

## Credential safety (SM-D7, CRITICAL)

Command does NOT seed a usable password and (v1 recommendation) creates NO User at all. No new
superuser is created by the command. If any user were created it must have `has_usable_password()` False.

## Key slugs (manifest — FINAL, ASCII)

### TRAKTORI taxonomy
- brands.Category: `traktori` (`is_for="traktori"`, `name="Traktori"`).
- Tractor brand slugs: `wuzheng`, `agri-tracking`, `saillong`.

### NEW tractors (`condition="new"`, `is_published=True`, `status="published"`)
| slug | brand | horse_power | year | price_eur |
|---|---|---|---|---|
| `agri-tracking-tb804` (HEADLINE) | agri-tracking | 80 | 2024 | 28500.00 |
| `wuzheng-wz504` | wuzheng | 50 | 2023 | 19900.00 |
| `saillong-sl904` | saillong | 90 | 2025 | 32400.00 |

Filter determinism: `year__gte=2024` → exactly 2 NEW (`agri-tracking-tb804` + `saillong-sl904`);
`horse_power__lt=60, condition="new"` → exactly `wuzheng-wz504`; `price_eur__lte=20000` → only `wuzheng-wz504`.

### USED machines (`condition="used"`, `is_published=True`, `status="published"`) — 5 total, all `year <= 2022`
| slug | brand | horse_power | year | price_eur |
|---|---|---|---|---|
| `polovni-traktor-agri-tracking-tb804` | agri-tracking | 75 | 2022 | 18500.00 |
| `polovni-tulip-mix-6m3` | tulip | 35 | 2018 | 4200.00 |
| `polovni-hzm-utovarivac` | hzm | 65 | 2020 | 15900.00 |
| `polovni-wuzheng-wz504` | wuzheng | 45 | 2019 | 9800.00 |
| `polovni-saillong-sl904` | saillong | 55 | 2021 | 13400.00 |

### Blog
- blog.Category slug: `ratarstvo`. blog.Tag slug: `zetva`.
- Headline published Post slug: `pet-saveta-za-prolecnu-setvu` (+ 2-4 more published posts).
- 3-5 `blog.Post` total, `status="published"`, `published_at=timezone.now()`, returned by `Post.published`.

### SiteSettings
- `pages.SiteSettings` singleton exists at `pk=1` after the command (defensive `get_or_create`/`load()`,
  no duplicate of the `apps/pages/0002` auto-seed).

## Guard summary

| Scenario | Result |
|---|---|
| `DEBUG=True`, no `--force` | proceeds, seeds |
| `DEBUG=False`, no `--force` | raises `CommandError` |
| `DEBUG=False`, `force=True` | proceeds, seeds |
| run twice | identical counts, no exception, exact slugs still resolve |
