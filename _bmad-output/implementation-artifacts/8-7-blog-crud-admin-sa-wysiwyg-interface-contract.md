---
story-id: 8-7-blog-crud-admin-sa-wysiwyg
artifact: interface-contract
phase: TEA RED
risk_tier: HIGH
created: 2026-06-09
created_by: TEA (Test Architect, RED phase)
---

# Interface Contract — Story 8.7 Blog CRUD Admin sa WYSIWYG

Ovaj dokument je KANONSKI ugovor koji Dev (GREEN phase) MORA zadovoljiti. Testovi u
`apps/blog/tests/test_8_7_blog_crud_admin.py` su izvršna specifikacija. Sve dole je
izvedeno iz ACs (AC1-AC12) + SM-decisions (SM-D1..D12) + Gotchas (G-1..G-19) story-je
i postojećih konvencija 8.6 (`apps/products/admin.py`), 7.5 (`apps/core/sanitize.py` +
`apps/core/templatetags/legal_html.py`), i media_pipeline guard-a.

---

## 1. Admin klase (`apps/blog/admin.py`)

| Klasa | Bazne klase (MRO) | Ključni atributi |
|-------|-------------------|------------------|
| `PostAdmin` | `SeoWarningAdminMixin, TranslationAdmin` (mixin PRVI — G-2) | `form = PostAdminForm`; `inlines = [SeoMetaInline]` (G-8 HARD LOCK); `search_fields = ("title_sr",)` (G-1 realna kolona); `prepopulated_fields = {"slug": ("title",)}` (G-14); `list_display`/`list_filter`/`date_hierarchy="published_at"` zadržani iz stub-a; `filter_horizontal = ("tags",)` (M2M slobodno dodavanje + `+` add-popup — AC7); `view_on_site` **RE-ENABLED** (NIJE False — SM-D8); `fieldsets` koriste BAZNA imena (`title`/`perex`/`body` auto-ekspanduju per-locale; G-1) |
| `CategoryAdmin` | `TranslationAdmin` | `list_display=("name","slug")`; `search_fields=("name_sr",)` (G-1); `prepopulated_fields={"slug":("name",)}`; **NEMA** SeoMetaInline (SM-D10/G-12) |
| `TagAdmin` | `TranslationAdmin` | `list_display=("name","slug")`; `search_fields=("name_sr",)`; `prepopulated_fields={"slug":("name",)}`; **NEMA** SeoMetaInline (G-12) |

NAPOMENA (SM-D8): `view_on_site` se RE-ENABLE-uje (ukloni `view_on_site=False`) jer je
5-3 registrovao `blog:detail`. Test contract: `PostAdmin.view_on_site is not False`.
DVA postojeća regression-lock testa koja asertuju `view_on_site is False` MORAJU se
ažurirati (test-ownership na 8.7 — G-16):
- `apps/seo/tests/test_seometa_admin_inline.py:test_postadmin_stays_translationadmin_and_view_on_site_false`
- `apps/blog/tests/test_admin.py:test_post_admin_view_on_site_false`

---

## 2. Forme

### `PostAdminForm(forms.ModelForm)` — mirror `ProductAdminForm` (8.6)

| Element | Ugovor |
|---------|--------|
| `main_image` override | `forms.FileField(required=False)` (G-9/G-14 — ImageField `to_python()` pregazi srpsku media_pipeline poruku) |
| `Meta` | `model = Post`; `exclude = ()` ILI `fields = ...` (MANDATORY — G-13) |
| `clean_main_image` | blank-skip prazan upload (`main_image` blank=True) → inače delegira na `validate_image_mime(f, allowed_mimes=ALLOWED_IMAGE_MIME_TYPES, max_size_bytes=MAX_IMAGE_UPLOAD_SIZE)`. NE reimplementiraj (G-10) |
| `title_sr` required | OSTAJE bezuslovno required (AC9/G-11 — NE relaksiraj). Ako direct-bind testovi traže relaksaciju baznog `title`, koristi core helper (SM-D6); `title_sr` NIKAD nije relaksiran |
| `body`/`perex` | `blank=True` na modelu → NISU required na form-sloju (draft sme imati prazan body) |
| WYSIWYG widget | `body_sr`/`body_hu`/`body_en` dobijaju rich-text widget (progressive enhancement IZNAD plain `Textarea`; SM-D2). Widget kroz `formfield_overrides` ILI `PostAdminForm`. Editor je UX; podležno polje OSTAJE `Textarea` |

NAPOMENA SM-D6 (BLAST-RADIUS): promociju `_relax_*` shim-a u `apps.core` izvrši SAMO ako
8.7 direct-bind-uje `PostAdminForm` i test zahteva relaksaciju baznog `title`. TEA testovi
direct-bind-uju `PostAdminForm` (vidi `_make_post_form`) i šalju `title_sr`-only payload →
**helper za relaksaciju baznog `title` JE potreban** (bazno `title` ostaje na formi kad raw
ModelForm vidi i `title` i `title_sr`). `title_sr` OSTAJE required u svakom slučaju.

NAPOMENA SLUG (direct-bind payload — TEA REVIEW fix): `Post.slug` je
`SluggedModel.SlugField(unique=True)` — NIJE `blank=True` → required form-polje koje
`_relax_*` helperi NE relaksiraju (nema `_sr` twin, nema model default; auto-gen se dešava
TEK u `Post.save()`/`full_clean()`, POSLE form-validacije). Zato POZITIVNI direct-bind
testovi koji traže `is_valid()` True (`test_ac4_blank_main_image_skips_gracefully`,
`test_ac4_clean_main_image_accepts_valid_image`) MORAJU proslediti `slug` (+ `status`) u
payload-u — mirror 8.6 `test_ac3_clean_main_image_accepts_valid_image` koji EKSPLICITNO
šalje `slug`. Negativni upload testovi NE moraju slug (assert je `not is_valid()` + poruka na
`main_image`; `clean_main_image` se izvršava nezavisno od slug-greške). `slug` ostaje required
na formi (NE relaksiraj — auto-gen je model-layer, NE form-layer).

---

## 3. Modul-nivo konstante (`apps/blog/admin.py`) — mirror 8.6

```python
MAX_IMAGE_UPLOAD_SIZE = 5 * 1024 * 1024          # 5 MB (EKSPLICITNO override 10MB default — AC4)
ALLOWED_IMAGE_MIME_TYPES = ("image/jpeg", "image/png", "image/webp")  # SVG izostavljen — XSS
```

---

## 4. Publish-gate (AC5) + published_at auto-set (AC6)

Lokacija: `PostAdmin.save_model` ILI `save_related` (PREPORUČEN save-put — SM-D5/A).
NEMA inline count-a (sva gate polja su na Post-u) → jednostavnije od 8.6.

| Korak | Ugovor |
|-------|--------|
| Trigger | `instance.status == Post.Status.PUBLISHED` (JEDAN status field — SM-D4, NE dual) |
| Provere pri publish | `title_sr` neprazan + `body_sr` neprazan (`.get("body_sr", "")` — G-19) + `main_image` priložen + `category` izabran (OQ-4 default) |
| Na neuspeh | `messages.error(...)` (srpski, pune dijakritike) + revert kroz `Post.objects.filter(pk=...).update(status=Post.Status.DRAFT)` (QuerySet.update bypass — G-6, NE `instance.save(update_fields=...)`) + in-memory `instance.status = DRAFT`. **NIKAD raise** (G-7 → 500) |
| Draft save | `status == DRAFT` se NIKAD ne gate-uje |
| `published_at` auto-set | kad `status == PUBLISHED` i `published_at is None` → `published_at = timezone.now()` (NIKAD naive `datetime.now()` — AC6/SM-D12). Ako gate FAIL-uje, NE postavlja se. Ako `published_at` već ima vrednost, NE pregazi (zakazana objava) |

---

## 5. Render-time nh3 sanitizacija (`templates/blog/post_detail.html:45`) — AC3 (STORED-XSS)

| Element | Ugovor |
|---------|--------|
| Promena | zameni `{{ post.body|linebreaks }}` sanitizovanim renderom |
| Mehanizam | REUSE 7-5: `{{ post.body|legal_html }}` ILI alias `{{ post.body|rich_html }}` (OQ-2 — alias u ISTOM `apps/core/templatetags/legal_html.py`, deli `mark_safe(sanitize_legal_html(...))` backend) |
| Allowlist | identičan 7-5 (`apps.core.sanitize._ALLOWED_TAGS`): p/br/h2-h4/ul/ol/li/a/strong/em/b/i/table-porodica. img/iframe/script/div/style STRIP (SM-D9; OQ-1 defer) |
| Semantika | nh3 STRIPUJE node (NE escape — G-4/SM-D7). NIKAD sirovi `|safe`, NIKAD `|linebreaks` |
| Scope asercija | body fragment `coric-blog-detail__body` (G-18 — NIKAD cela strana) |
| H1/title | `{% translated_field post 'title' %}` na H1 NETAKNUT (6-5); perex ostaje plain auto-escape (SM-D3) |

Ako se uvede `rich_html` alias: 7-5 statički guard `test_marksafe_wraps_only_sanitized_output`
+ postojeći `|legal_html` potrošači (gdpr/pages) MORAJU ostati zeleni (OQ-2/SM-D9).

---

## 6. RBAC (AC10) + migracije (AC11)

- RBAC: 8.2 `EDITOR_CONTENT_MODELS` VEĆ sadrži `("blog","post"/"category"/"tag")` →
  8.7 NE re-grant-uje. Verify: Editor → GET `admin:blog_post_changelist` → 200;
  anon → 302 admin login.
- Migracije: 0 blog migracija očekivano (admin-only; `body` ostaje plain TextField —
  SM-D2). `makemigrations blog --check` = No changes.

---

## 7. Reusable helpers (NE reimplementirati)

| Helper | Modul | Upotreba |
|--------|-------|----------|
| `validate_image_mime(upload, *, allowed_mimes, max_size_bytes)` | `apps.media_pipeline.utils` | `clean_main_image` upload guard (MIME + Pillow verify + `MAX_IMAGE_PIXELS=50M` bomb guard) |
| `sanitize_legal_html(raw) -> str` | `apps.core.sanitize` | nh3 allowlist backend za body render |
| `legal_html` filter (+ opciono `rich_html` alias) | `apps.core.templatetags.legal_html` | `mark_safe(sanitize_legal_html(value))` |
| `SeoMetaInline`, `SeoWarningAdminMixin` | `apps.seo.admin` | PostAdmin inline + soft-warning (G-8 regression) |

Kanonske media_pipeline poruke (za asercije):
- fake MIME → `"Nedozvoljen tip slike: ..."`
- corrupt / decompression-bomb → `"Slika je oštećena ili nije validan format."`
- prazan upload → `"Slika je prazna ili nije priložena."`

---

## 8. Sažetak za Dev (GREEN)

```
admin_classes:    [PostAdmin (SeoWarningAdminMixin, TranslationAdmin),
                   CategoryAdmin (TranslationAdmin),
                   TagAdmin (TranslationAdmin)]
forms:            [PostAdminForm (FileField main_image override + clean_main_image
                   + body WYSIWYG widget + title_sr required)]
sanitizer_helper: apps.core.sanitize.sanitize_legal_html  (via legal_html / rich_html filter)
upload_guards:    [apps.media_pipeline.utils.validate_image_mime]
migrations:       0  (admin-only; body ostaje plain TextField — SM-D2/AC11)
view_on_site:     RE-ENABLED (NIJE False — SM-D8; 2 regression-lock testa ažurirana)
```
