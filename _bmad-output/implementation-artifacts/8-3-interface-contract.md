# 8.3 — Interface Contract (Admin Dashboard sa Segmentovanim Lead Count-om)

> TEA canonical ugovor (RED faza). Dev MORA zadovoljiti SVE potpise/ponašanja dole.
> 0 migracija, 0 novih dependency-ja. PINOVAN admin-index override mehanizam (SM-D1).
> Jezik koda: Srpski (latinica), pune dijakritike u user-facing tekstu.

---

## 1. NOVI app `apps/admin_ext/`

Top-level admin-customization sloj. **Nijedan domain app NE sme importovati `apps.admin_ext`**
(project-context:674 / arch:740). Obrnuto (admin_ext čita domain modele READ-ONLY,
lokalni importi unutar funkcija) je dokumentovani izuzetak (SM-D4; mirror pages 3-1).

### 1.1 `apps/admin_ext/__init__.py`
Prazan (paket marker).

### 1.2 `apps/admin_ext/apps.py`
```python
class AdminExtConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.admin_ext"
    verbose_name = _("Admin proširenja")

    def ready(self):
        # Import UNUTAR ready() — circular-safe (mirror accounts/apps.py 8.1/8.2)
        from django.contrib import admin
        from apps.admin_ext.dashboard import dashboard_index  # ili inline u apps.py

        # PINOVAN override (SM-D1 / G-12 / G-1):
        # 1) SAČUVAJ original PRE reassignment-a (recursion guard)
        # 2) zameni admin.site.index wrapper-om koji injektuje stats u extra_context
        #    i DELEGIRA na sačuvani original (app_list zadržan)
        # 3) postavi index_template na ZASEBAN fajl koji {% extends "admin/index.html" %}
        ...
        admin.site.index = dashboard_index
        admin.site.index_template = "admin_ext/dashboard.html"
```

`AppConfig.name == "apps.admin_ext"` (sa `apps.` prefiksom — KRITIČNO).

### 1.3 `apps/admin_ext/models.py`
PRAZAN (NEMA modela → 0 migracija; SM-D3). Samo docstring/komentar dozvoljen.

### 1.4 `apps/admin_ext/migrations/__init__.py`
Prazan (paket marker). `makemigrations --check admin_ext` → "No changes".

---

## 2. `apps/admin_ext/stats.py`

Lokalni importi domain modela UNUTAR funkcija (SM-D4). Samo `.objects`/`count`/`aggregate`
— NIKAD `.save`/`.create`.

### 2.1 `get_lead_stats() -> dict[str, int]`
```python
def get_lead_stats() -> dict[str, int]:
    """Segmentovan lead count za TEKUĆI kalendarski mesec (TZ-aware).

    Vraća TAČNO ključeve:
        {"contact": int, "model_inquiry": int, "service_request": int,
         "part_request": int, "total": int}

    - month_start = timezone.now().replace(day=1, hour=0, minute=0,
                                           second=0, microsecond=0)
    - JEDAN agregat: Lead.objects.filter(created_at__gte=month_start)
                         .values("form_type").annotate(c=Count("id"))
    - svi 4 FormType ključa UVEK prisutni (default 0)
    - ključevi su Lead.FormType.<MEMBER>.value (NE hardkod string)
    - total = ZBIR 4 segmenta (single-source; AC2 total-semantika)
    """
```
- `assertNumQueries(1)` na IZOLOVAN poziv (jedan agregat; AC8).
- ZABRANJENO `created_at__month=N` samostalno (G-4). ZABRANJENO `datetime.now()` (G-5).
- ZABRANJENA per-segment petlja sa 4 `.count()` (G-6).

### 2.2 `get_content_stats() -> dict[str, int]`
```python
def get_content_stats() -> dict[str, int]:
    """Vraća {"published_products": int, "published_posts": int}.

    - published_products = Product.objects.filter(is_published=True).count()
    - published_posts    = Post.published.count()  (NE Post.objects — G-7)
    """
```
Draft/nepublikovani/future-dated se NE broje.

### 2.3 `get_dashboard_stats() -> dict`
Agregator helper (testabilna jedinica) koji spaja lead + content + GA statistiku u
jedan dict pogodan za `extra_context`. Predloženi oblik:
```python
def get_dashboard_stats() -> dict:
    return {
        "lead_stats": get_lead_stats(),
        "content_stats": get_content_stats(),
        "ga_visits": get_ga_visits(),   # try/except Exception wrap (AC5)
        "lead_form_types": [...],        # (value, label) parovi iz Lead.FormType (SM-D8)
    }
```
Tačan oblik je Dev sloboda DOK god template renderuje 4 segmenta + total + count-ove
+ GA placeholder + 2 brze-akcije linka. GA poziv obavijen `try/except Exception`
(NE bare `except:`) → na izuzetak vrati None-ove + `logger.warning` BEZ PII (AC5/AC9/G-9/G-10).

---

## 3. `apps/admin_ext/analytics.py`

### 3.1 `get_ga_visits() -> dict[str, int | None]`
```python
def get_ga_visits() -> dict[str, int | None]:
    """GA Reporting API stub (v1 — NIJE konfigurisan; SM-D6).

    Vraća {"last_7": None, "last_30": None} BEZ mrežnog poziva i BEZ izuzetka.
    Uključiva kasnije kroz getattr(settings, "GA_PROPERTY_ID", "") (Epic 9 / OQ-1).
    """
```
- NE pravi mrežni poziv u v1. `GA_PROPERTY_ID` NE postoji u base.py → default "" → None-ovi.
- Dashboard placeholder za None-ove: "Posete: N/D — uskoro / Epic 9" (NE goli "N/D").

---

## 4. `apps/admin_ext/dashboard.py` (ili wrapper inline u apps.py)

```python
from django.contrib import admin
from apps.admin_ext.stats import get_dashboard_stats

_original_index = admin.site.index   # SAČUVAJ PRE reassignment-a (G-12 recursion guard)

def dashboard_index(request, extra_context=None):
    ctx = {**(extra_context or {}), **get_dashboard_stats()}
    return _original_index(request, extra_context=ctx)   # delegira na ORIGINAL → app_list zadržan
```
RBAC: standardni admin `is_staff` gate (AC7 / SM-D5) — NE dodatni mixin.

---

## 5. `templates/admin_ext/dashboard.html`

```django
{% extends "admin/index.html" %}   {# parent = Django ugrađeni; NE samog sebe (G-1) #}
{% load i18n %}
{% block content %}
  {# statistika IZNAD: 4 lead segmenta + total istaknut, broj proizvoda/objava,
     GA "Posete: N/D — uskoro / Epic 9" placeholder,
     2 brze-akcije linka: {% url 'admin:products_product_add' %}
                          {% url 'admin:blog_post_add' %} (G-8) #}
  {{ block.super }}   {# default app_list ISPOD (SM-D2 / G-2) #}
{% endblock %}
```
Segment labele iz `Lead.FormType.<X>.label` (SM-D8). SAMO agregati — NIJEDAN sirovi
Lead PII (ime/email/telefon/poruka) se NE renderuje (AC9).

---

## 6. INSTALLED_APPS (EDIT `config/settings/base.py`)

Dodaj `"apps.admin_ext"` POSLE `"apps.accounts"` (admin-customization sloj poslednji;
mora POSLE `django.contrib.admin` — G-3):
```python
    "apps.accounts",
    "apps.admin_ext",  # NOVO Story 8.3 — admin dashboard override (POSLE accounts; G-3)
```

`config/urls.py` NETAKNUT (SM-D1 — default `admin.site` mount na `/admin-coric/`).
`pyproject.toml` NETAKNUT (0 dep).

---

## 7. Sažetak fajlova

| Fajl | Akcija | Napomena |
|------|--------|----------|
| `apps/admin_ext/__init__.py` | NOVI | paket marker |
| `apps/admin_ext/apps.py` | NOVI | AdminExtConfig + ready() override |
| `apps/admin_ext/models.py` | NOVI | PRAZAN (0 migracija) |
| `apps/admin_ext/migrations/__init__.py` | NOVI | paket marker |
| `apps/admin_ext/stats.py` | NOVI | get_lead_stats/get_content_stats/get_dashboard_stats |
| `apps/admin_ext/analytics.py` | NOVI | get_ga_visits stub |
| `apps/admin_ext/dashboard.py` | NOVI (opc.) | dashboard_index wrapper (ili inline u apps.py) |
| `templates/admin_ext/dashboard.html` | NOVI | extends admin/index.html |
| `apps/admin_ext/tests/` | NOVI | TEA RED testovi |
| `config/settings/base.py` | EDIT | INSTALLED_APPS += apps.admin_ext (posle accounts) |
