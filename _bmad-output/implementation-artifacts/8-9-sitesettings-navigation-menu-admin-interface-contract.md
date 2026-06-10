# Interface Contract — Story 8.9: SiteSettings + Navigation Menu Admin

> **TEA RED-phase artifact.** Definiše ugovor koji Dev (GREEN) mora ispuniti.
> Test fajl: `apps/pages/tests/test_8_9_sitesettings_admin.py` (25 testova).
> **Priroda story-ja: VERIFY / REGRESSION-LOCK.** Admin (`SiteSettingsAdmin`) VEĆ POSTOJI
> iz 3-4 i pun je. 8.9 zaključava postojeće + dodaje JEDNU novu stvar (AC6 nav komentar).

---

## RED-phase rezultat (baseline)

- **23 PASS** (regression-lock-ovi — zaključavaju postojeće 3-4 ponašanje; OČEKIVANO zeleno).
- **2 FAIL** (genuinski NOV ugovor — AC6 `[NOTE FOR DEV]` marker još NE postoji u header.html).
- **0 errors.**

Failing testovi = Dev TODO (jedina prava GREEN-faza implementacija):
- `test_ac6_header_has_note_for_dev_marker`
- `test_ac6_marker_is_on_outer_nav_not_inner_collapse`

---

## FROZEN interfejsi (NE menjati — regression locks)

### `apps/pages/admin.py:SiteSettingsAdmin` (3-4 — NETAKNUT osim opcione kozmetike)
- `SiteSettingsAdmin(TranslationAdmin)` — OSTAJE TranslationAdmin (NE plain ModelAdmin;
  modeltranslation auto-renderuje sr/hu/en tabove za `slogan`/`address`/`working_hours`).
- `list_display = ("company_name", "phone_sales", "email", "updated_at")`.
- `search_fields = ("company_name", "phone_sales", "email")` — **SVA tri REALNE
  ne-translatable kolone** (NISU u `translation.py`). **NE dodavati translatable polje
  (`slogan`/`address`/`working_hours`) bez `_sr` sufiksa → runtime FieldError (G-1).**
- `has_add_permission(request)` → `False` kad red postoji (singleton).
- `has_delete_permission(request, obj=None)` → `False` (i za `obj=None`).
- `changelist_view` → `302` redirect na change-view jedinog objekta kroz
  `reverse("admin:pages_sitesettings_change", args=[obj.pk])` (NIKAD hardkodovan put).
- change-view → `200` za superuser; POST PUN modeltranslation form → `302` + round-trip
  perzistencija; partial/required-fail → `200` redisplay sa form errors.
- **Opciono (PREPORUKA: preskoči):** `fieldsets` kozmetika — ako se uzme i uključuje
  `created_at`/`updated_at`, MORA `readonly_fields=("created_at","updated_at")` (inače
  `admin.E005`; G-2). Baza imena za translatable polja (auto-ekspanzija per-locale; G-1).

### `apps/pages/models.py:SiteSettings` (NETAKNUT — 0 migracija)
- Polja zamrznuta: `company_name`, `slogan`, `address`, `phone_sales`, `phone_service`,
  `email`, `working_hours`, `social_facebook`, `social_instagram` (+ TimestampedModel).
- **NEMA** `logo`/`favicon`/`hero_image`/`gdpr_banner_*` (epics:1175 DEFER — SM-D1/OQ-1).
- singleton (`save()` pk=1, `delete()` raise, `load()` get_or_create) — NETAKNUT.
- `makemigrations pages --check` = „No changes".

### `apps/pages/templatetags/site_settings.py` (NETAKNUT — cache-AC already-satisfied)
- `site_setting` tag = per-request keš samo (`request._coric_site_settings`); **NEMA
  Django `cache.set()`/Redis**. Promena → sledeći (novi) request vidi novu vrednost
  (zero stale; SM-D2). **NE uvoditi post_save signal + `cache.delete()`** (G-5/YAGNI).

### `apps/accounts/permissions.py:EDITOR_CONTENT_MODELS` (NETAKNUT — RBAC verify)
- `("pages", "sitesettings")` OSTAJE IZOSTAVLJEN (Superadmin-only; 8.2 SM-D15). **NE re-grant.**
- Editor → change-view `403`; Superadmin → `200`; anon → `302` login (admin na bare
  `/admin-coric/`, VAN i18n).

### `apps/pages/admin.py:PageAdmin` (8.8 — NETAKNUT; G-3)
- `search_fields = ("title_sr", "slug")`, `prepopulated_fields = {"slug": ("title_sr",)}` —
  8.9 dira SAMO `SiteSettingsAdmin`, NE PageAdmin.

### gdpr `_consent_banner.html` / `gdpr_banner.py` (cross-app — NETAKNUTI; G-4/OQ-1).

---

## NEW ugovor (Dev GREEN faza — JEDINA implementacija)

### `templates/partials/header.html` — `[NOTE FOR DEV]` navigacija marker (AC6)
Dodati Django `{# ... #}` komentar uz **SPOLJNI** nav element
`<nav class="coric-nav navbar navbar-expand-md" ...>` (~linija 55), **NE** uz unutrašnji
`<div class="collapse navbar-collapse" id="coricMainNav">` (~linija 76):

```django
{# [NOTE FOR DEV] v1.1: dinamička navigacija kroz NavigationItem model — trenutno (v1) statički {% url %} linkovi #}
```

Ugovor (test-enforced):
- Tekst sadrži `[NOTE FOR DEV]` **I** `NavigationItem`.
- Marker je u prozoru `< 250` znakova od `<nav class="coric-nav navbar navbar-expand-md"`.
- Koristi Django `{# #}` (NE HTML `<!-- -->`) → komentar se NE emituje u render (`[NOTE FOR
  DEV]` ne sme biti vidljiv u HTML izlazu).
- Nav linkovi NEPROMENJENI: `pages:home`, `products:tractor_list`, `pages:service`,
  `pages:about`, `pages:contact` OSTAJU.
- `djade` clean posle izmene.

---

## Test inventar (25 testova)

| AC | Test | Tip | RED status |
|----|------|-----|-----------|
| AC1 | `test_ac1_sitesettings_admin_is_translation_admin` | lock | PASS |
| AC1 | `test_ac1_has_add_permission_false_when_row_exists` | lock | PASS |
| AC1 | `test_ac1_has_delete_permission_false_including_obj_none` | lock | PASS |
| AC1 | `test_ac1_changelist_redirects_to_change_view` | lock | PASS |
| AC1 | `test_ac1_change_view_200_superuser` | lock | PASS |
| AC1/8 | `test_ac1_admin_system_checks_clean` | lock | PASS |
| AC2 | `test_ac2_change_view_renders_all_fields_with_locale_tabs` | lock | PASS |
| AC2 | `test_ac2_full_post_persists_new_values_round_trip` | lock | PASS |
| AC2 | `test_ac2_partial_post_missing_required_redisplays_200` | edge/negative | PASS |
| AC3 | `test_ac3_search_fields_are_real_non_translatable_columns` | lock | PASS |
| AC3 | `test_ac3_no_translatable_field_in_search_fields` | **NEW assert (G-1 defense)** | PASS |
| AC3 | `test_ac3_changelist_with_query_does_not_500` | lock | PASS |
| AC4 | `test_ac4_new_request_sees_updated_value` | lock | PASS |
| AC4 | `test_ac4_pages_has_no_cache_invalidation_signal` | lock (SM-D2) | PASS |
| AC5 | `test_ac5_sitesettings_not_in_editor_allowlist` | security/verify | PASS |
| AC5 | `test_ac5_editor_forbidden_on_change_view` | security | PASS |
| AC5 | `test_ac5_superadmin_allowed_on_change_view` | security | PASS |
| AC5 | `test_ac5_anonymous_redirected_to_login` | security/negative | PASS |
| **AC6** | `test_ac6_header_has_note_for_dev_marker` | **NEW contract** | **FAIL** |
| **AC6** | `test_ac6_marker_is_on_outer_nav_not_inner_collapse` | **NEW contract** | **FAIL** |
| AC6 | `test_ac6_nav_links_unchanged` | lock | PASS |
| AC6 | `test_ac6_header_renders_200_and_comment_not_emitted` | lock | PASS |
| AC7 | `test_ac7_no_pending_migration_for_pages` | lock | PASS |
| AC7 | `test_ac7_sitesettings_has_no_deferred_upload_or_banner_fields` | lock (SM-D1) | PASS |
| AC8/G-3 | `test_ac8_pageadmin_untouched` | lock | PASS |

**Auth:** `force_login` (NIKAD `client.login` — django-axes; force_login zaobilazi axes →
bez teardown-a). **URL:** uvek `reverse("admin:pages_sitesettings_*")`. **NE BeautifulSoup**
(regex/string matching).

---

## Dev TODO (GREEN faza)

1. Dodaj `{# [NOTE FOR DEV] v1.1: dinamička navigacija kroz NavigationItem model — trenutno (v1)
   statički {% url %} linkovi #}` uz SPOLJNI `<nav class="coric-nav navbar navbar-expand-md">`
   (~linija 55) u `templates/partials/header.html`. `djade` clean.
2. NE diraj: SiteSettings model, site_setting tag, permissions, PageAdmin, gdpr template.
3. (Opciono kozmetika, preporuka preskoči) `fieldsets` na SiteSettingsAdmin + `readonly_fields`
   ako uključuje timestamp polja (G-2).
4. Verifikuj: `makemigrations pages --check` = No changes; `manage.py check` čist; ŠIRI suite
   (pages/accounts/gdpr) zelen; `ruff` + `djade` clean.
