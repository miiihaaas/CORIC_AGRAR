# Interface Contract — Story 9.10 (WebP/AVIF + Final Lighthouse Pass)

**Story:** `9-10-webp-avif-final-lighthouse-pass`
**Epic:** 9 — Go-Live Readiness (POSLEDNJA story, zatvara epic)
**Type:** NON-app (static image variants + template markup + CI config + audit doc). 0 migracija, 0 novih prod-dep (Pillow već prisutan).
**TDD phase author:** TEA (🧪) — RED. Ovaj dokument PIN-uje kontrakt protiv koga su pisani failing testovi.

> **Host/env reality:** native-Win `pytest` collect pada na `libmagic` (python-magic) baseline — dokumentovani Epic-9 baseline, NIJE regresija. Svi 9.10 testovi su **import-light**: pure `pathlib`+`re` parse template/config izvora, `json` parse `lighthouserc.json`, `yaml` parse `lighthouse.yml`, `PIL.Image`/`os.stat` za binarne varijante. NEMA Playwright, NEMA Lighthouse run, NEMA Docker. Pokreću se sa `python -m pytest <file> -p no:django -q` iz repo root-a (`C:\Programming\dev-bmad\CORIC_AGRAR`). Ne diraju Django app-registry → ne triggeruju libmagic crash.

---

## 1. Static variant file paths (AC1, AC8)

| Path | Status | Kontrakt |
| ---- | ------ | -------- |
| `static/img/home/home-hero-1.jpg` | POSTOJI (≈413 KB / 413348 B) | ZADRŽAN (legacy JPG fallback) |
| `static/img/home/home-hero-1.avif` | Dev kreira (Task 1.3) | `PIL.Image.open(path).format == "AVIF"`; `os.stat().st_size` **STRIKTNO < jpg** |
| `static/img/home/home-hero-1.webp` | Dev kreira (Task 1.3) | `PIL.Image.open(path).format == "WEBP"`; `os.stat().st_size` **STRIKTNO < jpg** |

- Obe varijante **komitovane u repo** (binarni asset-i, atomic commit sa command-om).
- `>=` source nije dozvoljeno (NEMA tihog escape-a; size-guard u command-u — vidi §3).

---

## 2. Hero `<picture>` markup shape (AC2, AC3, AC4, AC9)

Fajl: `templates/pages/partials/_home_hero.html`. Plain `<img>` → `<picture>`:

```django
<picture>
  <source type="image/avif" srcset="{% static 'img/home/home-hero-1.avif' %}">
  <source type="image/webp" srcset="{% static 'img/home/home-hero-1.webp' %}">
  <img src="{% static 'img/home/home-hero-1.jpg' %}"
       alt=""
       aria-hidden="true"
       loading="eager"
       fetchpriority="high"
       class="coric-home-hero__bg">
</picture>
```

**Pinned invarijante:**
- `<picture>` element prisutan.
- `<source type="image/avif" ...>` index **<** `<source type="image/webp" ...>` index (AVIF PRVI — browser bira prvi podržan).
- `<img>` JPG fallback je **POSLEDNJI** child (posle oba `<source>`).
- `<img>` ima **realan `src=`** (jpg) — NE samo `srcset` na source-ovima (legacy-browser fallback, AC9).
- `alt=""` EGZAKTNO prazan (dekorativan — semantiku nosi `<h1>` overlay; NE izmišljaj alt).
- `aria-hidden="true"` EGZAKTNO.
- `loading="eager"` (NE `lazy` — LCP element).
- `class="coric-home-hero__bg"` OČUVAN na `<img>` (CSS cilja `<img>`, NE `<picture>`).
- Sva tri path-a koriste `{% static %}` (statički asset, NE media URL).
- **SHOULD (additivno):** `fetchpriority="high"` na hero `<img>` (LCP boost). Test čini odsustvo VIDLJIVIM (xfail/warn marker, NE tihi prolaz).
- **OPCIONO (additivno):** `sizes="100vw"` (full-bleed hero) — ne testira se hard.
- Overlay (`__overlay`, `<h1>` `{% blocktranslate %}`, lead, CTA) NETAKNUT. Single-line `{# #}` komentar stil zadržan.

---

## 3. Conversion tool — Django management command (AC5, AC1)

**Path:** `apps/media_pipeline/management/commands/convert_static_images.py`
**Command name:** `convert_static_images` (poziva se `manage.py convert_static_images`).
**Package init-ovi:** `apps/media_pipeline/management/__init__.py` + `.../management/commands/__init__.py` (Task 1.2).

**Pinned ponašanje (testira se parse-om command source-a):**
- `Image.open(src)` → `.save(dst, format="AVIF", quality=…)` i `.save(dst, format="WEBP", quality=…)`.
- **PIL.features guard:** `PIL.features.check('avif')` / `check('webp')` (ili `features.check(...)`) — fail-loud sa jasnom porukom ako format nedostaje (NE tiho preskoči).
- **Idempotency = SKIP-IF-EXISTS:** ponovno pokretanje NE menja committed output osim ako se prosledi `--force` (regen flag). Source MORA pominjati skip-if-exists wording + `--force` flag.
- **Size-guard (fail-loud):** posle encode-a `dst.size >= src.size` → warn + **non-zero exit** ILI zahtevaj eksplicitni **`--allow-larger`** override flag. Bez override-a, `>=` varijanta se NE komituje. Source MORA pominjati `--allow-larger`.
- Dokumentovan (docstring) + pomenut u AUDIT-REPORT sign-off (reproducibilnost).

> AC5 ne mandira tačnu lokaciju komande hard (stand-alone skripta je prihvatljiva ako je reproducibilna), ali kontrakt + testovi PIN-uju management-command path kao SOT (SM-D3). Test fajl postojanja gađa contract path.

---

## 4. `lighthouserc.json` asserti (AC6)

Fajl: `lighthouserc.json` (repo root). `ci.assert.assertions` MORA imati (parse JSON):

**Dodato (Task 4.1):**
```json
"categories:best-practices": ["error", { "minScore": 0.90 }],
"categories:seo":            ["error", { "minScore": 0.95 }]
```

**Očuvano EGZAKTNO (4 postojeća — NE diraj):**
```json
"categories:accessibility":  ["error", { "minScore": 0.95 }],
"largest-contentful-paint":  ["error", { "maxNumericValue": 2500 }],
"server-response-time":      ["error", { "maxNumericValue": 600 }],
"total-byte-weight":         ["error", { "maxNumericValue": 1572864 }]
```

- `collect.url` lista (5 URL-ova) + `numberOfRuns: 3` + `upload` NETAKNUTI.
- JSON parse-able.

---

## 5. `lighthouse.yml` enforce gate (AC7)

Fajl: `.github/workflows/lighthouse.yml`. Parse YAML, lociraj step po `name`:

- Step `name` **sadrži** `"Lighthouse CI autorun"` (puno ime: „Lighthouse CI autorun (collect + assert budgeti)") → **NEMA** `continue-on-error: true` (key odsutan ILI `false`). **Pozitivna i negativna** asercija: budget miss SADA obara job.
- Step `name` **sadrži** `"run-at-least-once"` (axe „A11y axe spec — run-at-least-once …") → **ZADRŽAVA** `continue-on-error: true` (NE diraj; a11y je već pokriven Lighthouse `categories:accessibility` assertom; ne dupliraj enforce).
- YAML valid. `on: push: branches:[staging]` + `workflow_dispatch` NETAKNUTI (gate NE crveni PR/master merge — fire-uje tek na staging-push).

---

## 6. `ops/quality/AUDIT-REPORT.md` finalni sign-off (AC10)

Fajl: `ops/quality/AUDIT-REPORT.md`. Dodata nova sekcija (npr. „(g) Final Lighthouse pass / sign-off (9.10)"). Pinned (raw-text grep):

- Heading/sekcija pominje **„Final Lighthouse"** / **„sign-off"** / **„9.10"** (final sign-off marker).
- Dokumentuje image-weight optimizaciju (hero AVIF/WebP + JPG, KB pre/posle).
- Lighthouse gate **ENFORCED** + lista assert-a.
- Eksplicitno razdvaja v1 `runserver --insecure` (indikativni) vs. staging-only (autoritativni TTFB/LCP).
- **Task 3 ishod** eksplicitno zabeležen (`responsive_picture` WebP `<source>`: IMPLEMENTIRAN ILI DEFERRED) — named-condition, NE smije tiho preskočiti.
- „(e) NOTE za 9.10" razrešen (DONE / referenca na sign-off).

---

## 7. Regression guard (AC4)

- `apps/media_pipeline/templatetags/media_tags.py` `responsive_picture` zadržava default `loading: str = "lazy"` (below-the-fold lazy NETAKNUT). Test parse source-a za `loading: str = "lazy"`.

---

## 8. Test fajlovi (lokacije)

| Test fajl | Pokriva |
| --------- | ------- |
| `apps/pages/tests/test_home_hero_picture.py` | AC2/AC3/AC4/AC8/AC9 — hero markup parse + variant exist/format/size (`PIL`/`os.stat`) + `responsive_picture` lazy regression |
| `tests/test_lighthouse_gate_9_10.py` | AC1/AC5/AC6/AC7/AC10 — `lighthouserc.json` JSON parse, `lighthouse.yml` YAML parse, command source parse, AUDIT-REPORT sign-off, variant size/format (co-located file-stat) |

Oba fajla standalone-runnable: `python -m pytest apps/pages/tests/test_home_hero_picture.py tests/test_lighthouse_gate_9_10.py -p no:django -q`.

---

## 9. RED očekivanje

Svi testovi PADAJU/ERROR-uju sada (varijante ne postoje; hero još plain `<img>`; `lighthouserc.json` nema best-practices/seo; `lighthouse.yml` autorun još ima `continue-on-error`; command fajl ne postoji; AUDIT-REPORT nema sign-off). To je korektan RED. Regression guard test (`loading: str = "lazy"`) MOŽE proći već sada — to je dizajn (postojeće ponašanje koje 9.10 NE sme slomiti).
