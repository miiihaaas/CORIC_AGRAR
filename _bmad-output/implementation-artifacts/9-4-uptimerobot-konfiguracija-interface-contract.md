# Interface Contract — Story 9.4: UptimeRobot Konfiguracija (`/healthz/` health endpoint)

> TEA RED faza. Ovaj dokument je SPECIFIKACIJA koju Dev (GREEN faza) mora ispuniti.
> Testovi u `apps/core/tests/test_healthz.py` su izvršni oblik ovog ugovora i MORAJU
> pasti dok endpoint nije implementiran i URL ožičen.

## Obim (samo implementabilni deo u repo-u)

| Artefakt | Tip | Vlasnik |
|---|---|---|
| `apps/core/views.py` — `healthz` FBV | NEW (popunjava prazan leaf fajl) | Dev (GREEN) |
| `config/urls.py` — `path("healthz/", healthz, name="healthz")` u NON-i18n bloku | UPDATE | Dev (GREEN) |
| `ops/monitoring/uptimerobot.md` — ops runbook (AC7/AC8 manual gate) | NEW | Dev (GREEN) — NIJE pokriven automatizovanim testovima |
| `apps/core/tests/test_healthz.py` | NEW | TEA (RED) — ovaj ugovor |

## View ugovor

```python
# apps/core/views.py
from django.http import HttpResponse


def healthz(request):
    return HttpResponse("ok", content_type="text/plain")
```

- Function-based view (FBV), Django stdlib only (`django.http.HttpResponse`). 0 novih dep-ova (SM-D8).
- BEZ `@login_required`, BEZ permission, BEZ `@ratelimit` dekoratora (AC2/AC4/SM-D7).
- 0 DB query-ja u samom view-u (AC6/SM-D4).
- Body je TAČNO `b"ok"` — `Content-Type: text/plain`. Informaciono prazan: NEMA env/secret/version/hostname/git-sha (SM-D6/G-7).
- `apps/core` ostaje LEAF — view NE importuje domain modele (`apps.products`/`apps.brands`/`apps.blog`/`apps.pages`) (G-3).

## URL ugovor

```python
# config/urls.py — NON-i18n urlpatterns blok (uz admin-coric/, robots.txt, sitemap.xml)
from apps.core.views import healthz
# ...
urlpatterns = [
    # ...
    path("healthz/", healthz, name="healthz"),
]
```

- `path("healthz/", healthz, name="healthz")` ide u **non-i18n** `urlpatterns` listu (VAN `i18n_patterns()`) — G-1/SM-D2.
- `reverse("healthz") == "/healthz/"` (BEZ `/sr/` prefiksa).
- `resolve("/healthz/").func` je `healthz` callable.
- `GET /healthz/` → 200 direktno, NE 301/302 (pod development settings; AC5/G-4).

## Ponašanje (acceptance)

| AC | Garancija |
|---|---|
| AC1 | `GET /healthz/` → 200, body sadrži `b"ok"` (tačno `b"ok"`), `Content-Type` počinje `text/plain` |
| AC1/SM-D6 | body NE curi env/secret/version/hostname — `response.content == b"ok"` |
| AC2 | anoniman klijent → 200 (NE 302-na-login, NE 403); view bez auth dekoratora |
| AC3 | `reverse("healthz") == "/healthz/"`; `resolve("/healthz/")` → `healthz` |
| AC4 | (a) 20+ burst GET → svi 200, nijedan 429; (b) view source bez `@ratelimit` |
| AC5 | `GET /healthz/` → 200, status NIJE u (301, 302) |
| AC6 | direktan `healthz(RequestFactory().get("/healthz/"))` pod `assertNumQueries(0)` → 200, body `b"ok"`; view source bez domain importa |
| AC7/AC8 | runbook + manual go-live gate — NIJE automatizovan test (TEA ne testira živ UptimeRobot/network egress) |

## Interface contract summary

- urls: `["healthz/ → reverse('healthz') == '/healthz/' (NON-i18n, bez locale prefiksa)"]`
- views: `["apps.core.views.healthz (FBV; HttpResponse('ok', content_type='text/plain'); bez auth/ratelimit/DB)"]`
- models: `[]` (nema modela, nema migracija)
- services: `[]` (nema servisa; eksterni UptimeRobot setup je manual runbook, NE kod)
