---
story-id: "3.4"
story-key: 3-4-sitesettings-model-inicijalni-admin
artifact: interface-contract
created: 2026-06-01
author: TEA / Murat (autonomous RED phase)
purpose: Canonical contract za PRVI model u apps/pages — SiteSettings singleton config
         model (pk=1; save() force; load() classmethod; delete() RAISE), modeltranslation
         (slogan/address/working_hours → _sr/_hu/_en), 2 migracije (0001 CreateModel +
         0002 RunPython data seed sa reverse_code), {% site_setting "field" %} simple_tag
         + |splitlines filter (apps/pages/templatetags/site_settings.py), singleton-friendly
         admin (has_add/has_delete guards + changelist→change redirect kroz reverse()), i
         WIRING 3 template lokacije (_contact_info.html + footer.html + header.html) da čitaju
         iz SiteSettings umesto hardkodovanih literala. 1 model, 2 migracije, 0 novih URL/view,
         0 forme, 0 CSS, 0 JS. Dev MORA satisfy svaku klauzulu u GREEN.
---

# Interface Contract — Story 3.4 „SiteSettings Model + Inicijalni Admin"

Story 3.4 uvodi PRVI model u `apps/pages` — `class SiteSettings(TimestampedModel)` singleton
config model u `apps/pages/models.py`, sa self-rolled singleton pattern-om (NE django-solo —
nema dep), modeltranslation registracijom (`apps/pages/translation.py`), DVE migracije
(`0001_initial` CreateModel + `0002_seed_sitesettings` RunPython data seed), `{% site_setting %}`
template tag + `|splitlines` filter (`apps/pages/templatetags/site_settings.py`), singleton-friendly
ModelAdmin (`apps/pages/admin.py`), i WIRING 3 template lokacije
(`_contact_info.html` + `footer.html` + `header.html`) da čitaju kontakt/social vrednosti iz
SiteSettings preko `{% site_setting %}` umesto hardkodovanih literala. NEMA novih URL-ova/view-ova,
forme, HTMX, CSS ni JS.

Ovaj ugovor enumeriše file-system delta + model surface (polja + translatable + singleton metode)
+ migracije (0001 + 0002 seed shape + reverse_code) + template tag/filter potpise + admin contract
(guardovi + changelist redirect + reverse() pravilo) + wiring targete + settings touchpoint-e +
modeltranslation kolone, koje TEA RED-phase testovi verifikuju. Dev GREEN-phase realizuje sve
klauzule; bilo koje odstupanje vraća story u `paused`.

> **NAPOMENA O TEST PARSIRANJU (TEA-D1):** Projekat NEMA `beautifulsoup4` u `pyproject.toml`
> (verifikovano live — postojeći `apps/pages/tests/test_*` koriste **regex** parsiranje
> renderovanog HTML-a). TEA poštuje POSTOJEĆU konvenciju istog modula i koristi **regex** za
> DOM assertion-e (mirror `test_contact_info.py`). Ovo NE menja kontrakt — samo mehaniku.

> **NAPOMENA O TEST DB / SEED (TEA-D2):** pytest-django primenjuje SVE migracije u test bazi —
> uključujući `0002_seed_sitesettings`. Zato seeded `SiteSettings(pk=1)` red POSTOJI po default-u
> u svakom testu (`load()` ga vraća; `phone_sales == "+381 230 468 168"`). Testovi su dizajnirani
> oko toga: `delete()`-raise i `save()`-pk=1 testovi rade nad tom (ili sveže `load()`-ovanom)
> instancom; wiring/tag/locale testovi se oslanjaju na seed default. Empty-social branch test
> EKSPLICITNO postavlja `social_facebook=""` (= seed default) i posebno popunjen URL da pokrije
> obe grane HIDE-WHEN-EMPTY logike.

---

## 1. File-system delta

| Path | Status | Vlasništvo |
|---|---|---|
| `apps/pages/models.py` | NOVO (Dev) | `class SiteSettings(TimestampedModel)` — singleton (`save()` force pk=1; `@classmethod load()` get_or_create pk=1; `delete()` RAISE-uje `PermissionDenied` ili izabran izuzetak, NE silent no-op); polja: `company_name`, `slogan` (transl.), `address` (transl.), `phone_sales`, `phone_service`, `email`, `working_hours` (transl. TextField), `social_facebook` (URLField blank), `social_instagram` (URLField blank); `__str__` → „Podešavanja sajta"; `Meta.verbose_name`/`verbose_name_plural`. NEMA FK, NEMA `get_absolute_url`. `help_text` (gettext_lazy) na `phone_service`/`social_facebook`/`social_instagram` flag-uje placeholder (SM-D11). |
| `apps/pages/translation.py` | NOVO (Dev) | `@register(SiteSettings)` `TranslationOptions(fields=("slogan", "address", "working_hours"))` — mirror `apps/brands/translation.py`. Import iz `apps.pages.models`. MORA postojati PRE `makemigrations`. |
| `apps/pages/admin.py` | NOVO (Dev) | `@admin.register(SiteSettings)` singleton `ModelAdmin`: `has_add_permission` → False kad red postoji; `has_delete_permission` → False; `list_display=("company_name","phone_sales","email","updated_at")`; `search_fields`; `changelist_view` override → redirect na change-view jedinog objekta kroz `reverse("admin:pages_sitesettings_change", args=[SiteSettings.load().pk])`. modeltranslation auto-tabovi (NE ručno). |
| `apps/pages/templatetags/__init__.py` | NOVO (Dev) | Prazan — Python package marker. |
| `apps/pages/templatetags/site_settings.py` | NOVO (Dev) | `register = template.Library()`; `@register.simple_tag def site_setting(field_name)` → `getattr(SiteSettings.load(), field_name)`; `@register.filter def splitlines(value)` → lista nepraznih `.strip()`-ovanih linija. |
| `apps/pages/migrations/__init__.py` | NOVO (Dev) | Python package marker. |
| `apps/pages/migrations/0001_initial.py` | GENERISANO + MANUAL REVIEW (Dev) | `makemigrations pages` — `CreateModel("SiteSettings", ...)` UKLJUČUJUĆI 9 modeltranslation kolona (`slogan_sr/hu/en`, `address_sr/hu/en`, `working_hours_sr/hu/en`) + nasleđena `created_at`/`updated_at`. CreateModel auto-reverzibilan. |
| `apps/pages/migrations/0002_seed_sitesettings.py` | NOVO ručno (Dev) | RunPython data seed: `forward` (`apps.get_model` + `update_or_create(pk=1, defaults=SM-D4 seed)`), `reverse_code` (`filter(pk=1).delete()`). `dependencies=[("pages","0001_initial")]`. `# TODO(OQ-1)` marker iznad placeholder polja. |
| `apps/pages/apps.py` | EDIT docstring (Dev) | Ažuriraj zastareli „NEMA modela … NEMA migracija" docstring. NE menjaj `PagesConfig` klasu/`name`/`verbose_name`. |
| `templates/pages/partials/_contact_info.html` | EDIT WIRING (Dev) | `{% load site_settings %}`; adresa/tel-prodaja/tel-servis/email/social → `{% site_setting %}`; radno vreme `<dl>` → `<ul>` preko `working_hours\|splitlines`; `tel:` href kroz `\|cut:" "`; social HIDE-WHEN-EMPTY; ukloni/„RESOLVED" IMP-SiteSettings marker. Labele ostaju `{% translate %}`. |
| `templates/partials/footer.html` | EDIT WIRING (Dev) | Kontakt kolona (tel/email/address/social) → `{% site_setting %}`; `{% load site_settings %}`; adresa puni-dijakritik iz seed-a; social HIDE-WHEN-EMPTY; `tel:` `\|cut:" "`. NE diraj logo/proizvodi/vesti kolone. |
| `templates/partials/header.html` | EDIT WIRING (Dev) | Top-header (adresa/prodaja/servis IMP-4/social) → `{% site_setting %}`; `{% load site_settings %}`; razreši IMP-4 marker; social HIDE-WHEN-EMPTY; `tel:` `\|cut:" "`. NE diraj nav/logo/search/lang-switcher. |
| `apps/pages/tests/test_sitesettings_model.py` | NOVO (TEA) | AC1 (Task 9.1) |
| `apps/pages/tests/test_sitesettings_singleton.py` | NOVO (TEA) | AC2 (Task 9.2) |
| `apps/pages/tests/test_sitesettings_migration_seed.py` | NOVO (TEA) | AC3+AC4 migracije + seed (Task 9.3) |
| `apps/pages/tests/test_sitesettings_translation.py` | NOVO (TEA) | AC5 (Task 9.4) |
| `apps/pages/tests/test_site_setting_tag.py` | NOVO (TEA) | AC7 tag + splitlines (Task 9.5) |
| `apps/pages/tests/test_sitesettings_admin.py` | NOVO (TEA) | AC6 (Task 9.6) |
| `apps/pages/tests/test_sitesettings_wiring.py` | NOVO (TEA) | AC8+AC9+AC10 (Task 9.7/9.8/9.9) |

**NETAKNUTO (regression guards):** `apps/core/models.py` `TimestampedModel` (REUSE — NE menja se);
`apps/pages/views.py` `HomeView`/`AboutView`/`ContactView` (NE čitaju SiteSettings — tag radi bez
view context-a); `apps/pages/urls.py` (nema novih URL-ova); `config/settings/*` (apps.pages VEĆ u
INSTALLED_APPS; modeltranslation VEĆ konfigurisan; `TEMPLATES` context_processors NETAKNUTI — tag,
NE context processor; `MODELTRANSLATION_FALLBACK_LANGUAGES=("sr",)`); `config/urls.py` (admin VEĆ
mount-ovan UNUTAR `i18n_patterns`); `pyproject.toml` (NEMA novog dep — NE django-solo);
`templates/pages/partials/_home_hero.html` (slogan NE wire — 3-1 SM-D10); postojeći
`apps/pages/tests/test_contact_info.py::test_contact_info_has_working_hours` (prima `<ul>` →
ostaje green); `apps/{brands,products,core,search,media_pipeline}/*`. **0 novih URL/view, 0 forme,
0 CSS, 0 JS.**

---

## 2. Model surface — `apps/pages/models.py` `SiteSettings`

```python
class SiteSettings(TimestampedModel):           # REUSE apps.core.models.TimestampedModel
    company_name   = CharField(...)             # plain (default „Ćorić Agrar")
    slogan         = CharField(max_length=255)  # TRANSLATABLE (forward-compat; NE čita se v1)
    address        = CharField/TextField        # TRANSLATABLE
    phone_sales    = CharField(...)             # plain
    phone_service  = CharField(blank=True, help_text=_("placeholder…"))  # plain
    email          = EmailField(...)            # plain
    working_hours  = TextField(...)             # TRANSLATABLE (multi-line, jedan red po liniji)
    social_facebook  = URLField(blank=True, help_text=_("placeholder…"))   # plain
    social_instagram = URLField(blank=True, help_text=_("placeholder…"))   # plain
    # nasleđeno: created_at, updated_at (TimestampedModel)

    def __str__(self): return "Podešavanja sajta"        # stabilan, NE per-instance
    def save(self, *a, **kw): self.pk = 1; super().save(*a, **kw)
    @classmethod
    def load(cls): obj, _ = cls.objects.get_or_create(pk=1); return obj
    def delete(self, *a, **kw): raise PermissionDenied(...)   # RAISE — NE silent no-op

    class Meta:
        verbose_name = "Podešavanja sajta"
        verbose_name_plural = "Podešavanja sajta"   # singleton — plural isto
```

**Polja (TAČNO 9 deklarisanih + 2 nasleđena):**

| Polje | Tip | Translatable | Napomena |
|---|---|---|---|
| `company_name` | CharField | NE | default „Ćorić Agrar" |
| `slogan` | CharField(255) | **DA** | forward-compat; NE čita se v1 (SM-D7) |
| `address` | CharField/TextField | **DA** | seed puni-dijakritik „Vojvođanska 1, Basaid, Srbija" |
| `phone_sales` | CharField | NE | „+381 230 468 168" (SA razmacima) |
| `phone_service` | CharField (blank) | NE | placeholder; `help_text` flag |
| `email` | EmailField | NE | prodaja@coricagrar.rs |
| `working_hours` | TextField | **DA** | multi-line newline-separated; render `<ul>`/`<li>` |
| `social_facebook` | URLField(blank) | NE | seed prazan; `help_text` flag; HIDE-WHEN-EMPTY |
| `social_instagram` | URLField(blank) | NE | seed prazan; `help_text` flag; HIDE-WHEN-EMPTY |
| `created_at` | DateTimeField (auto_now_add) | NE | nasleđeno TimestampedModel |
| `updated_at` | DateTimeField (auto_now) | NE | nasleđeno TimestampedModel |

**Singleton metode (SM-D2 — LOCKED):**
- `save()` → uvek `self.pk = 1` pre `super().save()`. Dva uzastopna `SiteSettings(...).save()` →
  `count() == 1` (drugi update-uje pk=1, NE kreira pk=2).
- `@classmethod load()` → `get_or_create(pk=1)[0]`. Na praznoj bazi vraća instancu (NE baca
  `DoesNotExist`). Lazy — bezbedan za template tag pre seed-a.
- `delete()` (instance) → **RAISE** (`PermissionDenied` preporuka). NE silent no-op. Posle pokušaja
  delete, red OSTAJE (`count() == 1`). **GRANICA:** instance `delete()` NE pokriva
  `QuerySet.delete()` / `loaddata` / `bulk_create` (zaobilaze instance metode) — singleton garancija
  počiva na save() pk=1 + instance delete() raise + admin `has_delete_permission=False`. Relevantno
  za Epic 9 9-7 fixture (mora targetirati pk=1).

**NEMA:** FK / relacija; `get_absolute_url` (config, NE content model); defensive validacije.

---

## 3. Migracije

### `0001_initial.py` (CreateModel + modeltranslation kolone — GENERISANO)
- `makemigrations pages` POSLE `translation.py` (Task 2 PRE Task 3 — INAČE 9 kolona NE ulazi u 0001).
- `CreateModel("SiteSettings", ...)` sa SVIM poljima UKLJUČUJUĆI 9 modeltranslation kolona:
  `slogan_sr`, `slogan_hu`, `slogan_en`, `address_sr`, `address_hu`, `address_en`,
  `working_hours_sr`, `working_hours_hu`, `working_hours_en` + nasleđena `created_at`/`updated_at`.
- `apps/pages/migrations/__init__.py` package marker.
- MANUAL REVIEW (project-context.md:221). CreateModel auto-reverzibilan (`migrate pages zero`).

### `0002_seed_sitesettings.py` (RunPython data seed + reverse_code — RUČNO)
- `dependencies = [("pages", "0001_initial")]`.
- **`forward(apps, schema_editor)`** (kroz `apps.get_model("pages","SiteSettings")` — NE direktan
  import; migration-safe) → `update_or_create(pk=1, defaults={...})` sa SM-D4 seed vrednostima
  (puni-dijakritik `_sr`; `_hu`/`_en` SMEJU biti prazni — fallback na sr).
- **`reverse_code(apps, schema_editor)`** → `model.objects.filter(pk=1).delete()` (project-context.md:227).
- `# TODO(OQ-1): placeholder — biznis popunjava realne vrednosti pre go-live` iznad
  `phone_service` / social URL-ova / `working_hours`.

**SM-D4 seed shape (single source):**

| Polje | sr vrednost | hu/en |
|---|---|---|
| `company_name` | Ćorić Agrar | (plain) |
| `slogan` | Prijatelj koji razume zemlju! | prazno (fallback sr) |
| `address` | Vojvođanska 1, Basaid, Srbija | identično sr ili prazno |
| `phone_sales` | +381 230 468 168 | (plain) |
| `phone_service` | +381 XXX XXX XXX (placeholder) | (plain) |
| `email` | prodaja@coricagrar.rs | (plain) |
| `working_hours` | newline-separated: „Ponedeljak–Petak: 08–16h" / „Subota: 08–13h" / „Nedelja: zatvoreno" | prazno (fallback sr) |
| `social_facebook` | „" (prazno) | (plain) |
| `social_instagram` | „" (prazno) | (plain) |

- **Posle migrate:** `SiteSettings.objects.count() == 1`; `SiteSettings.load().phone_sales == "+381 230 468 168"`;
  `address` (sr) sadrži „Vojvođanska" (puni-dijakritik), NE „Vojvodjanska".
- **pytest-django** primenjuje 0002 u test bazi automatski → seeded red postoji po default-u.

---

## 4. Template tag + filter — `apps/pages/templatetags/site_settings.py`

```python
from django import template
from apps.pages.models import SiteSettings

register = template.Library()

@register.simple_tag
def site_setting(field_name):
    return getattr(SiteSettings.load(), field_name)

@register.filter
def splitlines(value):
    return [ln.strip() for ln in (value or "").splitlines() if ln.strip()]
```

- `{% load site_settings %}{% site_setting "phone_sales" %}` → „+381 230 468 168".
- Translatable polje: `{% site_setting "address" %}` čita aktivnu lokalu (getattr → modeltranslation
  virtuelni atribut) sa sr fallback (hu/en prazno).
- Radi BEZ view context-a (view-ovi NETAKNUTI); radi na `load()` default i pre seed-a.
- `as` var podržan (`{% site_setting "phone_sales" as ps %}`) — `simple_tag` daje to besplatno.
- `splitlines`: prima string, vraća listu nepraznih `.strip()`-ovanih linija; `None`/prazno → `[]`.
- **NEMA context processor** u `TEMPLATES` (settings NETAKNUTI).

---

## 5. Admin contract — `apps/pages/admin.py`

- `@admin.register(SiteSettings)` na POSTOJEĆI `admin.site` (mirror `apps/brands/admin.py`) — pojavljuje
  se u admin app listi (verbose_name „Podešavanja sajta").
- `has_add_permission(request)` → **False** kad `SiteSettings.objects.exists()` (posle seed-a uvek True →
  „Add" skriven).
- `has_delete_permission(request, obj=None)` → **False** (singleton se ne briše).
- `list_display` definisan (npr. `("company_name","phone_sales","email","updated_at")`); `search_fields`
  definisan (project-context.md:200).
- modeltranslation AUTO-rendera jezičke tabove za `slogan`/`address`/`working_hours` (NE ručno —
  project-context.md:201).
- `changelist_view` override → kad red postoji, **HTTP 302 redirect** na change-view jedinog objekta:
  `HttpResponseRedirect(reverse("admin:pages_sitesettings_change", args=[SiteSettings.load().pk]))`.
- change-view → **HTTP 200** za superuser.

**⛔ reverse() PRAVILO (SM-D6 — LOCKED):** admin je mount-ovan UNUTAR `i18n_patterns` → stvarni URL je
locale-prefiksovan (`/sr/admin/pages/sitesettings/...`). Test/smoke MORA koristiti
`reverse("admin:pages_sitesettings_changelist")` i `reverse("admin:pages_sitesettings_change", args=[obj.pk])`.
**NIKAD** hardkodovan `/admin/...` ni `/sr/admin/...` (bare put → 404). `/admin-coric/` slug +
django-axes = Epic 8 8.1 (van scope-a).

---

## 6. Wiring targeti (koji template renderuje koje polje)

| Template | Polja → `{% site_setting %}` | Posebno |
|---|---|---|
| `templates/pages/partials/_contact_info.html` | `address`, `phone_sales`, `phone_service`, `email`, `working_hours`, `social_facebook`, `social_instagram` | radno vreme `<dl>`→`<ul>` preko `\|splitlines`; `tel:` `\|cut:" "`; social HIDE-WHEN-EMPTY; ukloni IMP-SiteSettings marker; NEMA `\|safe` |
| `templates/partials/footer.html` | `phone_sales`, `email`, `address`, `social_facebook`, `social_instagram` | adresa puni-dijakritik iz seed-a (popravlja šišanu „Vojvodjanska"); `tel:` `\|cut:" "`; social HIDE-WHEN-EMPTY |
| `templates/partials/header.html` (top-header) | `address`, `phone_sales`, `phone_service`, `social_facebook`, `social_instagram` | razreši IMP-4 servis placeholder; `tel:` `\|cut:" "`; social HIDE-WHEN-EMPTY; NE diraj nav/logo/search |

**LOCKED pattern-i:**
- **`tel:` href (SM-D8):** vidljiv tekst SA razmacima; href BEZ razmaka kroz built-in `|cut:" "`:
  `{% site_setting "phone_sales" as ps %}<a href="tel:{{ ps|cut:" " }}">{{ ps }}</a>`.
- **social HIDE-WHEN-EMPTY (SM-D8a):** prazan URL → link SAKRIVEN (NE `href=""` ni `href="#"`):
  `{% site_setting "social_facebook" as fb %}{% if fb %}<a href="{{ fb }}">…</a>{% endif %}`.
- **working_hours (SM-D10):** `{% site_setting "working_hours" as wh %}<ul class="coric-contact-info__hours-list">{% for line in wh|splitlines %}<li>{{ line }}</li>{% endfor %}</ul>`. NIKAD `|safe`.
- **NE WIRE:** `_home_hero.html` slogan (3-1 SM-D10); logo/favicon/hero (nisu polja v1).

---

## 7. Settings touchpoints

- **NEMA.** `apps.pages` VEĆ u INSTALLED_APPS (Story 3.1); modeltranslation VEĆ konfigurisan PRE
  `django.contrib.admin` (Story 1.2/2.1); `MODELTRANSLATION_FALLBACK_LANGUAGES=("sr",)` VEĆ postavljen
  (`config/settings/base.py:124`); `TEMPLATES` context_processors NETAKNUTI (tag, NE context processor);
  admin VEĆ mount-ovan (`config/urls.py`). Jedini „registracioni" touchpoint je `translation.py`
  (auto-discovery pri startup-u — NE settings edit). `pyproject.toml` NETAKNUT (NE django-solo).

---

## 8. modeltranslation kolone (9 — ulaze u 0001)

`slogan_sr`, `slogan_hu`, `slogan_en`, `address_sr`, `address_hu`, `address_en`,
`working_hours_sr`, `working_hours_hu`, `working_hours_en`.

Plain polja (`company_name`, `phone_sales`, `phone_service`, `email`, `social_facebook`,
`social_instagram`) NEMAJU `_sr/hu/en` varijante (jedna vrednost za sve lokale).

---

## 9. AC → test traceability

| AC | Test fajl | Testovi (br.) |
|---|---|---|
| AC1 | `test_sitesettings_model.py` | polja postoje, tipovi, `__str__`, TimestampedModel nasleđe, Meta verbose_name, NE FK, NE get_absolute_url (7) |
| AC2 | `test_sitesettings_singleton.py` | save() pk=1 force, count==1 posle 2 save, load() get_or_create, delete() RAISE + red ostaje, load() na čistoj instanci (5) |
| AC3+AC4 | `test_sitesettings_migration_seed.py` | 0001 ima `_sr/_hu/_en` kolone (DB introspect), seed pk=1 popunjen (count==1, phone_sales, address puni-dijakritik), reverse_code briše pk=1, forward idempotent (4) |
| AC5 | `test_sitesettings_translation.py` | slogan/address/working_hours translatable (`address_sr/hu/en` postoje); plain polja NISU translatable (2) |
| AC7 | `test_site_setting_tag.py` | tag renderuje vrednost, radi bez view context-a, radi na load() default, locale-aware address, splitlines daje neprazne linije, splitlines prazno→[] (6) |
| AC6 | `test_sitesettings_admin.py` | registrovan, has_add False kad red postoji, has_delete False, list_display+search_fields definisani, changelist 302 redirect (reverse), change-view 200 (6) |
| AC8+AC9+AC10 | `test_sitesettings_wiring.py` | contact-info adresa iz seed (puni-dijakritik), working_hours `<ul>`/`<li>` (NE `<dl>`), IMP marker uklonjen, footer+header IMP-4 razrešen, social HIDE-WHEN-EMPTY (obe grane), `tel:` BEZ razmaka, home hero slogan netaknut, sva 3 locale 200, nema ćirilice (wiring+i18n) |

**Test count (TEA RED phase):** model=7, singleton=5, migration_seed=4, translation=2, template_tag=6,
admin=6, wiring=10 (uklj. i18n). **Ukupno = 40.**

---

## 10. RED-phase očekivanje

Pre Dev GREEN: `apps/pages/models.py` NE postoji, `apps/pages/migrations/` NE postoji,
`apps/pages/translation.py` NE postoji, `apps/pages/templatetags/` NE postoji, `apps/pages/admin.py`
NE postoji; template-i još drže hardkodovane literale + IMP markere. Svi NOVI testovi MORAJU pasti —
`ImportError` (`apps.pages.models` / `templatetags.site_settings`) / `LookupError` (no SiteSettings
model) / `TemplateSyntaxError` (`'site_settings' is not a registered tag library`) /
`NoReverseMatch` (`admin:pages_sitesettings_*`) / assertion (template još hardkodovan; `<dl>` umesto
`<ul>`; IMP marker prisutan). **JEDINI dozvoljeni PASS u RED fazi** je regresija-lock:
home/contact strana je trenutno 200 i `_home_hero.html` slogan je netaknut — pa pod-asserti koji
SAMO proveravaju „strana 200" / „slogan još tu" mogu proći; ali svaki asert koji traži da VREDNOST
dolazi iz SiteSettings (npr. radno vreme kao `<ul>`, IMP marker uklonjen, splitlines render) MORA
pasti. Postojeći 3-3 `test_contact_info_has_working_hours` ostaje green (prima `<ul>`) i TEA ga NE menja.
Bilo koji DRUGI neočekivani PASS znači preslab test → istraži/ojačaj.
