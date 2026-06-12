---
story-id: 9-4-uptimerobot-konfiguracija
story_key: 9-4-uptimerobot-konfiguracija
story_id_dotted: 9.4
epic: 9
module: config (Django URLconf — non-i18n urlpatterns blok) + apps/core (mali health-check FBV) + ops/monitoring (runbook docs)
title: "UptimeRobot Konfiguracija"
status: ready-for-dev
risk_tier: MEDIUM
language: Srpski (latinica)
created: 2026-06-12
created_by: SM (autonomous, YOLO)
needs_e2e: false
migrations: 0
new_dependencies: 0   # SAMO Django stdlib (HttpResponse/JsonResponse) — NEMA django-health-check, NEMA bilo kog novog paketa
depends_on:
  - 9-1    # compose/production.yml (django/Gunicorn+nginx) — nginx `location /` catch-all proxy već čini /healthz/ dostupnim
  - 9-2    # nginx 443/HTTPS aktivan + HTTP→HTTPS 301; X-Forwarded-Proto proxy header (zašto health iza TLS-a radi)
  - 9-3    # GlitchTip self-host — UptimeRobot je KOMPLEMENT (uptime, NE errors); GlitchTip URL je jedan od monitor target-a
forward_dep:
  - 9-5    # backup skripte — nepovezano (deferred, NE diraj)
  - 9-6    # Django LOGGING dict — nepovezano (deferred, NE diraj)
---

# Story 9.4: UptimeRobot Konfiguracija

Status: ready-for-dev

## Story

As a **dev**,
I want **lightweight `/healthz/` health-check endpoint u Django-u (200 + keyword "ok", bez auth, bez locale prefiksa, bez ratelimit/redirect) PLUS ops runbook za eksternu UptimeRobot konfiguraciju**,
so that **UptimeRobot free tier može pingovati staging/production/GlitchTip svakih 5 min i poslati email čim sajt vrati non-200 — dobijam alert čim sajt padne (NFR-5 24/7 dostupnost)**.

## Opis

**ČETVRTA Epic 9 (Go-Live Readiness) story** — uvodi uptime monitoring. Ovo je **HIBRIDNA story**: jedan mali IMPLEMENTABILAN deliverable u repo-u (health endpoint) + jedan OPS RUNBOOK koji dokumentuje EKSTERNU (manual) SaaS konfiguraciju.

**ISKRENA SCOPE PODELA (KRITIČNO — pročitaj SM-D1):** epics.md 9.4 ACs opisuju „registrujem UptimeRobot free account, kreiram monitore za staging/production/GlitchTip sa 5-min interval-om, email alerting, maintenance window, opciono public status page". **Stvarno kreiranje account-a i monitora je EKSTERNO i MANUELNO** — radi se u UptimeRobot web dashboard-u, NE u ovom repo-u. **NE izmišljaj UptimeRobot API poziv, NE pretvaraj se da provisioniraš monitore iz koda.** Taj deo je dokumentovan kao **runbook checklist** (`ops/monitoring/uptimerobot.md`) koji se izvršava manuelno na go-live.

**Šta JE implementabilno u ovom repo-u (Dev/TEA STVARNO grade i testiraju):**

1. **`/healthz/` health-check endpoint** — mali FBV koji vraća HTTP 200 sa sitnim plain-text body-jem koji sadrži stabilan keyword (`ok`) za UptimeRobot keyword-check. Bez auth, bez DB-teškog rada, VAN locale prefiksa (živi u non-i18n urlpatterns bloku `config/urls.py` — isti blok gde već žive `admin-coric/`, `robots.txt`, `sitemap.xml`), exempt od ratelimit/redirect, prolazi kroz ALLOWED_HOSTS / security middleware.
2. **Ops runbook** `ops/monitoring/uptimerobot.md` — dokumentuje eksterni UptimeRobot setup (monitor URL-ovi, keyword `ok`, 5-min interval, email alert kontakti, maintenance window za deploy, opcioni public status page, free-tier limiti 50 monitora / 5 min — AR-20). Ovaj doc zadovoljava „registrujem account / kreiram monitore" ACs kao runbook jer je posao manuelan/eksteran.
3. **OPCIONO** nginx nota: da li se dodaje dedikovan `location = /healthz/ { access_log off; proxy_pass ...; }` (smanjuje log šum od 5-min pingova). Frame-uje se kao opciona optimizacija, NE tvrd zahtev — `location /` već pokriva sve non-static/media putanje (nginx.conf:108-118).

NEMA migracija. NEMA modela. NEMA novih dep-ova. NEMA Django app-a (health view ide u postojeći `apps/core`, koji je leaf i trenutno bez view-ova).

### Šta 9.4 STVARNO isporučuje

| # | Artefakt | Tip | Napomena |
|---|---|---|---|
| 1 | `apps/core/views.py` — `healthz` FBV | NEW (popunjava prazan fajl) | `HttpResponse("ok", content_type="text/plain")` ILI `JsonResponse({"status": "ok"})`. Bez auth, bez DB. PLAIN 200 (SM-D4). |
| 2 | `config/urls.py` — `path("healthz/", healthz, name="healthz")` u **non-i18n** urlpatterns bloku (linije ~24-44, uz `admin-coric/`/`robots.txt`/`sitemap.xml`) | UPDATE | VAN `i18n_patterns()` → `/healthz/` rezolvira BEZ locale prefiksa. |
| 3 | `ops/monitoring/uptimerobot.md` | NEW | Runbook: monitor URL-ovi, keyword `ok`, 5-min interval, email alert, maintenance window, public status page, free-tier limiti. |
| 4 | (OPCIONO) `compose/nginx/nginx.conf` — dedikovan `location = /healthz/ { access_log off; }` | UPDATE (opciono) | Samo log-noise optimizacija. NE tvrd zahtev. |
| 5 | `apps/core/tests/test_healthz.py` — INFRA/view testovi | NEW (TEA) | AC1-AC6 (200/keyword/no-auth/no-prefix/no-ratelimit/no-redirect/fast). |

### Postojeće stanje (READ pre izmene — obavezno)

| Fajl | Linija | Sadržaj / zašto je relevantno |
|---|---|---|
| `config/urls.py` | 23-44 | **Non-i18n urlpatterns blok** — `i18n/setlang/`, `sitemap.xml`, `robots.txt`, `admin-coric/` SVE žive OVDE (VAN `i18n_patterns()`, bez locale prefiksa). Non-i18n blok se evaluira PRE `i18n_patterns` → `/healthz/` rezolvira na bare path. **Health path ide TAČNO u ovaj blok** (SM-D2). |
| `config/urls.py` | 47-63 | `i18n_patterns(...)` blok — SVE locale-prefiksovano (`/sr/...`). **NE stavljaj health ovde** (dobio bi `/sr/healthz/`, a `/healthz/` bi 404). `pages.urls` catch-all `<slug:slug>/` je POSLEDNJI u OVOM bloku — NE dotiče non-i18n blok (G-3). |
| `apps/core/views.py` | 1-7 | **PRAZAN** (samo docstring — „Trenutno bez view-ova"; home se preselio u `apps/pages`). `apps/core` je LEAF app (NE sme importovati domain apps — architecture). Health view (Django stdlib only) je SAVRŠEN fit ovde. |
| `compose/nginx/nginx.conf` | 108-118 | `location / { proxy_pass http://django; ... }` — catch-all proxy ka Gunicorn-u. **`/healthz/` je VEĆ dostupan** kroz ovaj catch-all. Dedikovan `location = /healthz/` je SAMO opciona log-noise optimizacija (SM-D5). |
| `compose/nginx/nginx.conf` | 109-117 | `proxy_set_header X-Forwarded-Proto $scheme` (G-3 iz 9.1/9.2) — zašto health iza TLS-a vraća 200 a ne 301 loop. |
| `config/settings/production.py` | 17 | `SECURE_SSL_REDIRECT = env.bool(..., default=True)` — u prod-u Django redirect-uje HTTP→HTTPS. ALI nginx terminira TLS i šalje `X-Forwarded-Proto: https` → Django vidi request kao već-secure → NEMA redirect-a za `/healthz/`. UptimeRobot pinga `https://.../healthz/` direktno → 200 (vidi G-4). |
| `apps/seo/middleware.py` | 37-45 | `RedirectMiddleware.__call__` — redirect SAMO ako `Redirect.objects.filter(old_path=path, is_active=True)` ima red. `/healthz/` neće matchovati osim ako admin slučajno ne kreira red sa tim `old_path` — neutralno (G-5). |
| `apps/core/middleware.py` | 38-61 | `LocaleSwitcherMiddleware` — redirect SAMO na `?lang=X` query param. UptimeRobot pinga golo `/healthz/` (bez `?lang`) → prolazi netaknuto. |
| `config/settings/base.py` | 24 | `ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", ...)` — UptimeRobot pinga preko prod domena (`Host: coricagrar.rs`), koji je u ALLOWED_HOSTS → 200, NE 400 (vidi OQ-1/runbook: monitor MORA koristiti domen koji je u ALLOWED_HOSTS, NE goli IP). |
| `_bmad-output/planning-artifacts/architecture.md` | ~220-221, ~925 | Monitoring tabela: AR-19 GlitchTip + AR-20 UptimeRobot. Uptime monitoring je arhitekturno predviđen. |
| `_bmad-output/planning-artifacts/epics.md` | 1223-1233 | Story 9.4 ACs (registracija account-a + monitori 5-min + email alert + maintenance window + opcioni status page). |
| `_bmad-output/planning-artifacts/epics.md` | 121, 163 | NFR-5 (24/7 dostupnost, razuman uptime target) + AR-20 (UptimeRobot free tier 50 monitora / 5 min interval). |

---

## SM Decisions (autoritativno nad epics.md ilustrativnom formulacijom)

**SM-D1 — EKSTERNI SaaS = RUNBOOK, NE kod. NE izmišljaj API/provisioning.**
epics.md 9.4 ACs („registrujem account, kreiram monitore") opisuju posao koji se radi RUKOM u UptimeRobot web dashboard-u. Taj posao se **NE može i NE sme** simulirati iz repo-a: nema UptimeRobot provisioning koda, nema Terraform/IaC za monitore, nema API key-a u repo-u. **ODLUKA: implementabilan deo = `/healthz/` endpoint; eksterni deo = `ops/monitoring/uptimerobot.md` runbook + go-live manual gate (OQ).** Iskreno razdvajamo „šta Dev gradi i TEA testira" (endpoint) od „šta operator radi ručno na go-live" (account/monitori). Ovo NIJE pukotina u skoupu — to je priroda eksternog SaaS monitoringa. (Mirror 9.3 SM-D8 honesty: test-500-view je manual go-live OQ, NE dead app kod.)

**SM-D2 — Health endpoint živi u NON-i18n urlpatterns bloku `config/urls.py` (bez locale prefiksa).**
UptimeRobot pinga **golu putanju** `/healthz/`, NE `/sr/healthz/`. Monitor ne zna/ne treba da zna za locale prefikse. `config/urls.py:23-44` je non-i18n blok (evaluira se PRE `i18n_patterns`) gde već žive `admin-coric/`, `robots.txt`, `sitemap.xml` — sve VAN locale prostora. **ODLUKA: `path("healthz/", healthz, name="healthz")` ide u TAJ blok.** `/healthz/` rezolvira; `/sr/healthz/` NIJE potrebno i sme da 404 (monitor koristi bare path). NE stavljaj u `i18n_patterns(...)` (G-1) — to bi dalo `/sr/healthz/` i ostavilo `/healthz/` na 404.

**SM-D3 — Path je `/healthz/` (preporuka). Trailing slash konzistentan sa ostatkom projekta.**
`/healthz/` je k8s/cloud-native konvencija, jasno signalizira „health, ne korisnička strana", i malo verovatno kolidira sa korisničkim slug-om. Trailing slash zadržan (Django `APPEND_SLASH` + projekat svuda koristi trailing slash — `robots.txt`/`sitemap.xml` su izuzetak jer su file-like). **Health je endpoint, ne fajl → trailing slash.** UptimeRobot URL u runbook-u: `https://<domen>/healthz/`. (Ako biznis preferira `/health/` ili `/__health__/`, to je trivijalna izmena — ali default `/healthz/`.)

**SM-D4 — PLAIN 200 "ok", BEZ DB ping-a (v1). Uptime monitor NE sme da flap-uje na DB hiccup.**
**ODLUKA: health view vraća čist `HttpResponse("ok", content_type="text/plain")` (ili `JsonResponse({"status": "ok"})`) — NE dira bazu.** Razlozi: (a) UptimeRobot pinga svakih 5 min — mora biti maksimalno jeftino i pouzdano; (b) **DB hiccup TREBA da page-uje kroz GlitchTip (9.3 error tracking), NE da flap-uje uptime monitor** — meša se signal „sajt je gore" sa „DB je sporo"; (c) plain 200 je determinističko i `assertNumQueries(0)`-testabilno. Ako bi biznis kasnije hteo shallow DB ping (npr. `/readyz/` readiness vs `/healthz/` liveness), to je zaseban budući endpoint — NE u 9.4 scope. **v1 = liveness only, plain 200.** (Ako Dev ipak odluči za shallow DB ping, mora degradirati graceful — try/except, vratiti 200 čak i na DB fail za liveness, ILI biti eksplicitan readiness endpoint — ali PREPORUKA je plain 200; vidi OQ-5.)

**ISKREN CAVEAT (G-5/G-9):** SAM VIEW je DB-free (0 query-ja, AC6), ALI request PATH `/healthz/` ipak pogađa `RedirectMiddleware` (`apps/seo/middleware.py`) koji radi jedan `Redirect.objects.filter(...).first()` DB lookup na svakom non-skip path-u — `/healthz/` NIJE u skip setu. Na produkciji sa 5-min interval-om to je ~288 dodatnih lookup-a/dan po monitoru. To NE narušava plain-200 odluku (lookup je indeksiran, jeftin, i ne flap-uje 200), ali je iskreno računovodstvo: „view radi 0 query-ja" ≠ „request radi 0 query-ja". **Dodavanje `/healthz/` u middleware skip set je VAN SCOPE-a za v1** (dotaklo bi `apps/seo/middleware.py` — 9.4-nepovezan fajl), ali je dokumentovana buduća optimizacija. Plain-200 view odluka i dalje stoji.

**SM-D5 — Dedikovan nginx `location = /healthz/` je OPCIONA optimizacija, NE zahtev.**
`compose/nginx/nginx.conf:108-118` `location /` catch-all VEĆ proxy-uje sve non-static/media putanje ka Django-u, pa je `/healthz/` VEĆ dostupan. Dedikovan `location = /healthz/ { access_log off; proxy_pass http://django; ... }` SAMO smanjuje access-log šum od 288 pingova/dan (5-min × 24h). **ODLUKA: Dev MOŽE dodati exact-match location sa `access_log off` (i re-emitovati proxy_set_header blok kao u `location /`), ali to je optimizacija — AC se NE oslanja na nju.** Ako se doda, MORA replicirati `proxy_set_header X-Forwarded-Proto $scheme` (inače SSL redirect loop, G-4). Runbook dokumentuje da/da-ne je dodato.

**SM-D6 — Endpoint NE sme da curi env/secret/version info u body-ju.**
Body je STROGO `ok` ili `{"status": "ok"}` — NIŠTA osetljivo. NEMA verzije, git sha, hostname, env varijabli, DB status detalja, build info-a. Health endpoint je javan i bez auth → mora biti informaciono prazan za napadača. (Ovo je security guard — health endpoint-i su čest info-leak vektor.)

**SM-D7 — Bez ratelimit na `/healthz/`. UptimeRobot pinga često; ratelimit bi lažno oborio monitor.**
Projekat koristi `@ratelimit` na FORMAMA (kontakt, login — project-context.md:178/607). Health view **NE sme** imati `@ratelimit` dekorator — UptimeRobot pinga 1×/5min po monitoru, a sa više monitora (staging+prod+GlitchTip) i retry-jeva to može biti burst. Ratelimit bi vratio 429 → UptimeRobot bi to pročitao kao „sajt dole" → lažni alert. **ODLUKA: NE dodaji ratelimit na health view.** (Health je read-only, idempotentan, bez state-change — nema DoS surface koji ratelimit štiti; plain 200 je jeftiniji od samog ratelimit cache lookup-a.)

**SM-D8 — Health view je FBV (function-based), Django stdlib only, 0 novih dep.**
NE `django-health-check` library (NIJE u epics.md, NIJE u pyproject — uvođenje bi bilo scope creep + nov dep + više površine). NE CBV (preterano za 1-line 200). **ODLUKA: mali FBV u `apps/core/views.py` koristeći `django.http.HttpResponse`/`JsonResponse`.** `apps/core` je leaf app (NE importuje domain apps) → health view (bez ikakvog domain importa) savršeno pripada tu.

**SM-D9 — SCOPE GUARD — šta JESTE i šta NIJE 9.4:**
- **U SCOPE-u:** `healthz` FBV u `apps/core/views.py`; URL wire u non-i18n blok `config/urls.py`; `ops/monitoring/uptimerobot.md` runbook; opciona nginx `location = /healthz/` nota; view/INFRA testovi (AC1-AC7).
- **VAN SCOPE-a (DEFER, NE DIRAJ):**
  - **9.5** (pg_dump/restic backup) — ostaje `backlog`. NE diraj backup skripte.
  - **9.6** (Django LOGGING dict) — ostaje `backlog`. NE diraj logging konfiguraciju.
  - Stvarno UptimeRobot account/monitor kreiranje — EKSTERNO, manual go-live gate (OQ-2..OQ-4), dokumentovano u runbook-u, NE automatizovano.
  - Public status page — OPCIONO (epics.md „opciono"), dokumentovano u runbook-u kao opcija, NE obavezan deliverable (OQ-4).
  - Shallow DB ping / `/readyz/` readiness endpoint — NE u v1 (SM-D4); budući zaseban endpoint ako zatreba.
  - `django-health-check` ili bilo koji nov paket — NE (SM-D8).
  - Migracija — NEMA (nema modela).

---

## Acceptance Criteria

**AC1 — `GET /healthz/` vraća 200 + keyword "ok"** (epics:1230-1231 keyword-check osnova)
**Given** Django app sa registrovanim `healthz` view-om
**When** anoniman klijent pošalje `GET /healthz/`
**Then** odgovor je HTTP **200**
**And** `Content-Type` je `text/plain` (ILI `application/json` ako Dev bira JsonResponse)
**And** response body sadrži stabilan keyword **`ok`** (UptimeRobot keyword-monitor traži tu reč; case kako Dev odluči, runbook MORA dokumentovati tačan keyword/case)
**And** body NE sadrži env/secret/version/hostname info (SM-D6 — informaciono prazan)

**AC2 — `/healthz/` ne zahteva autentifikaciju** (epics:1230 — monitor je anoniman)
**Given** `healthz` endpoint
**When** **NEautentifikovan** (anoniman) klijent pošalje `GET /healthz/`
**Then** odgovor je **200**, NE 302-na-login, NE 403
**And** view nema `@login_required` / permission dekorator

**AC3 — `/healthz/` rezolvira BEZ locale prefiksa** (SM-D2)
**Given** non-i18n urlpatterns blok u `config/urls.py`
**When** se rezolvira putanja `/healthz/` (bez `/sr/` prefiksa)
**Then** `reverse("healthz")` vraća `/healthz/` (NE `/sr/healthz/`)
**And** `GET /healthz/` → 200 (rezolvira u non-i18n bloku)
**And** `/sr/healthz/` NIJE potreban i SME da vrati 404 (monitor koristi bare path) — pozitivna asercija: `/healthz/` radi bez prefiksa

**AC4 — `/healthz/` NIJE rate-limited** (SM-D7)
**Given** `healthz` view bez `@ratelimit` dekoratora
**When** klijent pošalje N brzih uzastopnih `GET /healthz/` zahteva (npr. 20+ u kratkom roku)
**Then** SVI vraćaju **200** (nijedan 429) — funkcionalni burst test
**And** (OBA uslova obavezna, AND) view source NE sadrži `@ratelimit` dekorator (regression guard) — testiraju se OBE asercije, ne jedna ILI druga

**AC5 — `/healthz/` je isključen iz redirect-a** (SM-D2, G-4)
**Given** health endpoint na Django/WSGI sloju
**When** `GET /healthz/` (na Django app sloju, sa secure proxy header simuliranim gde je relevantno)
**Then** odgovor je **200 direktno**, NE 301/302 (ne redirect-uje na locale prefiks, ne na login, ne na HTTPS-loop)
**And** napomena: iza nginx-a (9.2) koji terminira TLS i šalje `X-Forwarded-Proto: https`, `SECURE_SSL_REDIRECT` NE okida za `/healthz/` (Django vidi request kao secure) — UptimeRobot pinga `https://.../healthz/` → 200 (G-4). Test asertuje na Django/WSGI sloju da `GET /healthz/` daje 200, NE redirect status.

**AC6 — View je brz / ne radi težak DB rad** (SM-D4)
**Given** plain-200 health view
**When** se izvrši DIREKTAN poziv `healthz(RequestFactory().get("/healthz/"))` (zaobilazi ceo middleware stack)
**Then** view NE pogađa bazu za health logiku — `assertNumQueries(0)` MORA biti oko TOG direktnog view-callable poziva (NE oko `client.get(...)`). Kanonski AC6 test je RequestFactory direktan poziv jer dokazuje da SAM VIEW emituje 0 query-ja.
**And** **NE asertuj `assertNumQueries(0)` kroz Django test client** — `client.get("/healthz/")` prolazi kroz pun middleware stack koji EMITUJE query-je na `/healthz/` (u OVOM projektu konkretno `RedirectMiddleware`, vidi G-9), pa bi `assertNumQueries(0)` kroz client FAIL-ovao. Client-based 200/keyword test (AC1) ostaje ZASEBAN i NE asertuje query count.
**And** view ne importuje/ne dodiruje domain modele (apps.core leaf čistoća)

**AC7 — `ops/monitoring/uptimerobot.md` runbook postoji i dokumentuje eksterni setup** (epics:1230-1233, AR-20)
**Given** eksterna UptimeRobot konfiguracija (manual)
**When** Dev napiše runbook
**Then** `ops/monitoring/uptimerobot.md` postoji i sadrži:
- monitor URL-ovi: production `https://<prod-domen>/healthz/`, staging `https://<staging-domen>/healthz/`, GlitchTip `https://<glitchtip-domen-ili-port>/` (9.3 OQ-1 target);
- tip monitora: HTTP(S) keyword monitor, keyword = `ok` (tačan keyword/case usaglašen sa AC1);
- interval: **5 min** (AR-20 free-tier minimum);
- alert kontakti: email (go-live recipient — OQ-3);
- maintenance window: pauziraj/ignore monitore tokom deploy prozora (epics:1232);
- opcioni public status page (epics:1233);
- free-tier limiti: **50 monitora / 5 min interval** (AR-20);
- napomena: monitor MORA koristiti **domen iz ALLOWED_HOSTS** (NE goli IP — inače 400; vidi OQ-1);
- napomena: monitor URL MORA imati **trailing slash** `https://.../healthz/` (BEZ trailing slash-a Django `APPEND_SLASH` vraća 301 `/healthz` → `/healthz/` — nepotreban hop; vidi G-13);
- napomena: keyword monitor MORA koristiti **GET** metodu, NE HEAD — Django na HEAD strip-uje response body, pa keyword `ok` NE bi bio pronađen → lažni „down" (vidi G-13);
- checklist forma (kockice) za go-live verifikaciju (AC8).

**AC8 — (Manual / go-live runbook gate) UptimeRobot account + monitori kreirani EKSTERNO** (epics:1229-1230)
**Given** runbook iz AC7
**When** operator na go-live registruje UptimeRobot free account i kreira 3 monitora (staging/production/GlitchTip)
**Then** ovo je **MANUAL gate** verifikovan ručno na go-live (NE automatizovan test) — dokumentovan kao checklist u `ops/monitoring/uptimerobot.md` i kao Open Question (OQ-2)
**And** TEA NE piše automatizovan test koji zahteva živ UptimeRobot account / network egress (mark kao manual-verify)

---

## Tasks / Zadaci

**Task 1 — [x] `healthz` health-check FBV u `apps/core/views.py` (AC1, AC2, AC6, SM-D4, SM-D6, SM-D8)**
1.1. U `apps/core/views.py` (trenutno prazan — samo docstring) dodaj mali FBV:
```python
from django.http import HttpResponse

def healthz(request):
    """Liveness probe za UptimeRobot (Story 9.4). Plain 200, bez auth, bez DB.

    NE dira bazu (SM-D4): uptime monitor NE sme da flap-uje na DB hiccup — DB
    problemi se page-uju kroz GlitchTip (9.3), NE kroz uptime monitor. Body je
    informaciono prazan (SM-D6) — NIKAD env/secret/version/hostname leak.
    """
    return HttpResponse("ok", content_type="text/plain")
```
(Alternativa: `JsonResponse({"status": "ok"})` — Dev bira; runbook MORA dokumentovati tačan keyword/case za UptimeRobot keyword-monitor.)
1.2. NEMA `@login_required`, NEMA `@ratelimit`, NEMA permission dekoratora (AC2/AC4/SM-D7). NEMA DB query-ja (AC6/SM-D4). NEMA import-a domain modela (`apps.core` leaf — SM-D8).
1.3. NEMA env/secret/version u body-ju (SM-D6).

**Task 2 — [x] Wire URL u NON-i18n blok `config/urls.py` (AC3, AC5, SM-D2)**
2.1. Import: `from apps.core.views import healthz` (uz postojeće import-e na vrhu `config/urls.py`).
2.2. Dodaj `path("healthz/", healthz, name="healthz")` u **non-i18n** `urlpatterns` listu (linije ~24-44, uz `admin-coric/`/`robots.txt`/`sitemap.xml`), SA objašnjavajućim komentarom (mirror postojećih „Story X.Y — VAN i18n_patterns" komentara) da je VAN locale prefiksa namerno (UptimeRobot pinga bare `/healthz/`).
2.3. **NE stavljaj u `i18n_patterns(...)` blok** (linije 47-63) — to bi dalo `/healthz/` na 404 i `/sr/healthz/` umesto (G-1). Verifikuj `reverse("healthz") == "/healthz/"`.

**Task 3 — [x] Ops runbook `ops/monitoring/uptimerobot.md` (AC7, AC8, SM-D1)**
3.1. **Kreiraj direktorijum `ops/monitoring/` (NE postoji u repo-u — `ops/` trenutno sadrži SAMO `secrets/`, `deploy/`, `nginx/`; ovo je PRVI fajl u `ops/monitoring/`; uradi `mkdir`/`New-Item -ItemType Directory`)** i unutar njega `uptimerobot.md`. **NAPOMENA:** ranija premisa „mirror 9.3 ops/monitoring lokacija" je FAKTIČKI POGREŠNA — 9.3 je aktivirala zakomentarisan GlitchTip placeholder UNUTAR `compose/production.yml` i NIJE kreirala `ops/monitoring/`. Dakle ovo je nov direktorijum, ne postojeća lokacija. Sadržaj per AC7: monitor URL-ovi (prod/staging/GlitchTip `/healthz/`), HTTP(S) keyword monitor sa keyword `ok`, 5-min interval, email alert kontakti, maintenance window za deploy, opcioni public status page, free-tier limiti (50 monitora / 5 min — AR-20), ALLOWED_HOSTS/domen-ne-IP napomena.
3.2. Dodaj **go-live checklist** (kockice) za manual verifikaciju (AC8): [ ] registrovan free account, [ ] prod monitor, [ ] staging monitor, [ ] GlitchTip monitor, [ ] email alert kontakt potvrđen, [ ] maintenance-window politika dogovorena, [ ] (opciono) public status page.
3.3. Dokumentuj rezidualne OQ (final URL-ovi, alert email, maintenance politika, status page yes/no) kao go-live gate-ove.

**Task 4 — [x] (OPCIONO) nginx dedikovan `location = /healthz/` (SM-D5) — ODLUKA: PRESKOČENO (default), `location /` catch-all pokriva; dokumentovano u runbook sekciji 8**
4.1. **OPCIONO** — ako Dev odluči za log-noise optimizaciju, dodaj u `compose/nginx/nginx.conf` 443 server bloku (PRE `location /` catch-all):
```
location = /healthz/ {
    access_log off;
    proxy_pass http://django;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;   # G-4: bez ovoga SSL redirect loop
    proxy_redirect off;
}
```
4.2. Ako se NE dodaje, dokumentuj u runbook-u da je `location /` catch-all dovoljan (default). NE blokira nijedan AC.
4.3. Ako se dodaje: verifikuj `nginx -t` (ili `docker compose -f compose/production.yml config` ako se health proverava kroz compose) i da `X-Forwarded-Proto` postoji (G-4).

**Task 5 — INFRA/view testovi (AC1-AC6) — TEA RED faza**
5.1. `apps/core/tests/test_healthz.py`:
- AC1: `client.get("/healthz/")` → `status_code == 200`, `b"ok" in response.content`, `Content-Type` text/plain (ili json varijanta).
- AC2: anoniman klijent (default test client je anoniman) → 200, NE 302/403.
- AC3: `reverse("healthz") == "/healthz/"` (bez locale prefiksa); `/healthz/` rezolvira (`resolve("/healthz/")`).
- AC4: OBA (AND, ne ILI) — (1) funkcionalni burst test: petlja 20+ `GET /healthz/` → SVI 200 (nijedan 429); I (2) regression guard: asertuj da view source NE sadrži `@ratelimit` dekorator (npr. `inspect.getsource(healthz)` ili čitanje `apps/core/views.py` → `"ratelimit" not in source`).
- AC5: `GET /healthz/` → status 200, NE 301/302 (`assertNotIn(response.status_code, (301, 302))`).
- AC6: **KANONSKI** — `assertNumQueries(0)` oko DIREKTNOG poziva `healthz(RequestFactory().get("/healthz/"))` (NE kroz `client.get`). Ovo je primarni AC6 test, NE fallback — `client.get("/healthz/")` bi FAIL-ovao jer `RedirectMiddleware` (`apps/seo/middleware.py`) radi DB lookup na `/healthz/` (nije u skip setu; vidi G-9). RequestFactory direktan poziv zaobilazi middleware → dokazuje 0 query-ja u samom view-u.
5.2. **Host caveat (vidi sekciju niže):** native Windows pytest collection FAIL-uje na libmagic (`python-magic` zahteva system libmagic — **pre-existing baseline, NIJE regresija**). Testiraj health view kroz putanju koja izbegava admin autodiscover (npr. `pytest -p no:cacheprovider apps/core/tests/test_healthz.py` ili targetiran modul) ILI pokreni u Docker/CI Linux-u sa libmagic. `RequestFactory` + direktan view poziv izbegava pun URL-resolver/admin autodiscover na host-u.

**Task 6 — [x] Manual review + scope guard** (16/16 healthz testovi PASS Docker; apps/core 97 PASS; seo+pages 506 PASS regresija-čisto; ruff clean; 9.5/9.6 NETAKNUTI; 0 dep / 0 migracija)
6.1. Verifikuj `/healthz/` 200 lokalno (`python manage.py runserver` + curl `/healthz/`, ako host dozvoljava) ili kroz Docker.
6.2. **NE diraj:** 9.5 backup (`backlog`), 9.6 LOGGING (`backlog`), GlitchTip 9.3 fajlove. NE dodaji nov dep. NE dodaji migraciju. NE pravi UptimeRobot API/provisioning kod (SM-D1).

---

## Gotchas

- **G-1 — Health MORA biti u NON-i18n bloku, NE `i18n_patterns`.** Ako Dev iz navike doda `path("healthz/", ...)` u `i18n_patterns(...)` blok (linije 47-63), dobiće `/sr/healthz/` a `/healthz/` će 404. UptimeRobot pinga GOLU putanju → monitor bi odmah pao. MORA u non-i18n `urlpatterns` listu (linije 24-44, uz `admin-coric/`/`robots.txt`).
- **G-2 — `pages.urls` catch-all NE dotiče health.** `i18n_patterns` blok ima `pages.urls` sa `<slug:slug>/` catch-all-om kao POSLEDNJIM (config/urls.py:61, Story 7.4 CRITICAL-1). To je UNUTAR `i18n_patterns` (locale-prefiksovano) i ne polaže pravo na non-i18n `/healthz/`. Non-i18n blok se evaluira PRE i18n bloka → `/healthz/` rezolvira sigurno. Bez kolizije.
- **G-3 — `apps/core` je LEAF app — health view NE sme importovati domain apps.** `apps/core/views.py` trenutno prazan jer je home preselen u `apps/pages` (core ne sme importovati products/brands/pages — architecture boundary). Health view koristi SAMO `django.http` — 0 domain importa → ostaje leaf-clean. NE importuj nijedan model.
- **G-4 — SSL redirect loop / X-Forwarded-Proto.** U prod-u `SECURE_SSL_REDIRECT=True`. Iza nginx-a (9.2), nginx terminira TLS i šalje `X-Forwarded-Proto: https` (nginx.conf:116) → Django (`SECURE_PROXY_SSL_HEADER`, production.py:21) vidi request kao secure → NE redirect-uje `/healthz/`. UptimeRobot MORA pingovati `https://.../healthz/` (NE `http://` — to bi dobilo 301 na https, što UptimeRobot prati ali je čistije monitorovati direktno https). Ako se doda dedikovan nginx `location = /healthz/`, MORA replicirati `proxy_set_header X-Forwarded-Proto $scheme` inače loop. (STYLE napomena, NE blokira: `config/settings/staging.py:13` ima HARDCODED `SECURE_SSL_REDIRECT = True` — NIJE env-override kao production.py:17 — pa lokalni HTTP smoke test pod staging settings-ima pravi 301 loop; koristi production settings sa env-override ili Django runserver/RequestFactory za lokalnu proveru.)
- **G-5 — RedirectMiddleware je neutralan za `/healthz/`.** `apps/seo/middleware.py:RedirectMiddleware` redirect-uje SAMO ako `Redirect` DB red ima `old_path == "/healthz/"`. Default — nema takvog reda → prolazi. (Edge: admin slučajno kreira Redirect sa `old_path=/healthz/` → 301; runbook može napomenuti da se `/healthz/` ne koristi kao redirect source. Nije Dev concern u v1.)
- **G-6 — NE ratelimit (lažni down).** Health view BEZ `@ratelimit`. UptimeRobot + više monitora + retry burst bi pogodio ratelimit → 429 → UptimeRobot čita kao „down" → lažni alert. Plain 200 je jeftiniji od ratelimit cache lookup-a. (SM-D7)
- **G-7 — Body informaciono prazan (security).** Javan endpoint bez auth → NE curi verziju/env/hostname/git-sha. Samo `ok`. (SM-D6 — health endpoint-i su čest info-leak vektor.)
- **G-8 — ALLOWED_HOSTS / domen-ne-IP.** UptimeRobot monitor MORA koristiti DOMEN koji je u `DJANGO_ALLOWED_HOSTS` (npr. `coricagrar.rs`), NE goli VPS IP — inače Django vraća 400 (DisallowedHost) → lažni „down". Runbook dokumentuje ovo (AC7). Alternativa: dodati IP u ALLOWED_HOSTS (NE preporučeno — domen je čistiji).
- **G-9 — `assertNumQueries(0)` kroz test client ĆE FAIL-ovati — koristi RequestFactory direktan poziv.** Test client prolazi kroz pun middleware stack koji EMITUJE query-je na `/healthz/`. **U OVOM projektu faktički uzrok query-ja je `RedirectMiddleware` (`apps/seo/middleware.py`)** koji radi `Redirect.objects.filter(old_path=path, is_active=True).first()` DB lookup na SVAKOM non-skip path-u — a `/healthz/` NIJE u skip setu (`_SKIP_PREFIXES = ("/static/", "/media/")` + admin regex `/admin-coric/`). To **NIJE** session/auth middleware (SessionMiddleware može dodati i svoje, ali primarni izvor je RedirectMiddleware). Zato AC6 `assertNumQueries(0)` MORA biti oko direktnog `healthz(RequestFactory().get("/healthz/"))` poziva — to zaobilazi ceo middleware stack i dokazuje da VIEW SAM emituje 0 query-ja (to je ono što AC6 garantuje). Client-based 200/keyword test (AC1) ostaje zaseban i NE asertuje query count.
- **G-10 — Trailing slash konzistentnost.** `path("healthz/", ...)` sa trailing slash. `APPEND_SLASH` (Django default True) redirect-uje `/healthz` → `/healthz/` (301). UptimeRobot URL u runbook-u MORA imati trailing slash (`/healthz/`) da izbegne nepotreban 301 hop (koji UptimeRobot prati ali je čistije direktno). (SM-D3)
- **G-11 — Eksterni posao je RUNBOOK, ne kod (SM-D1).** Dev NE sme pisati UptimeRobot API klijent / provisioning skriptu / IaC za monitore. To je manual go-live posao. Jedini kod-deliverable je health endpoint + URL. Ostalo je `.md` runbook.
- **G-12 — `LocaleSwitcherMiddleware` je neutralan za `/healthz/`.** `apps/core/middleware.py:LocaleSwitcherMiddleware` redirect-uje SAMO na `?lang=X` query param. UptimeRobot pinga golo `/healthz/` (bez `?lang`) → prolazi netaknuto, bez redirect-a. (Konzistentno sa G-5 RedirectMiddleware neutralnošću.)
- **G-13 — APPEND_SLASH 301 + HEAD-vs-GET keyword zamka (runbook MORA pokriti oba).** (a) `APPEND_SLASH` (Django default True) redirect-uje `/healthz` → `/healthz/` (301) — UptimeRobot monitor URL MORA imati trailing slash `/healthz/` da izbegne 301 hop. (b) Django na **HEAD** request-u vraća 200 ali sa PRAZNIM body-jem (strip-uje sadržaj) → keyword `ok` se NE bi pronašao → lažni „down". UptimeRobot keyword monitor MORA koristiti **GET**, ne HEAD. Oba su runbook zahtevi (AC7).

---

## Open Questions

- **OQ-1 (go-live gate) — finalni prod/staging/GlitchTip URL-ovi za monitore.** Zavisi od 9.2 OQ-2 (finalni domen + DNS) i 9.3 OQ-1 (GlitchTip subdomena `errors.<domena>` vs port). Runbook ostavlja placeholder `<prod-domen>`/`<staging-domen>`/`<glitchtip-target>`. **Mihas potvrda pre go-live.** Monitor MORA koristiti domen iz ALLOWED_HOSTS (G-8).
- **OQ-2 (go-live gate, manual) — registracija UptimeRobot free account + kreiranje 3 monitora.** EKSTERNO, manual (SM-D1, AC8). Ko ima account / koji email? **Mihas/operator na go-live.** Verifikovano ručno kroz runbook checklist.
- **OQ-3 (go-live gate) — alert email recipient(s).** Na koju adresu (Mihas? tim? alias?) UptimeRobot šalje down/up alert? **Mihas potvrda.** Runbook placeholder.
- **OQ-4 — maintenance window politika + public status page yes/no.** Da li se monitori pauziraju automatski tokom deploy prozora (epics:1232) — koji prozor (npr. deploy script poziva UptimeRobot pause API, ili manual)? Da li se pravi opcioni public status page (epics:1233) i sa kim se deli? **Mihas/infra odluka na go-live.** (Auto-pause kroz deploy.sh bi bio 9.2-style proširenje — DEFER, nije 9.4 scope osim ako Mihas ne traži.)
- **OQ-5 — liveness-only vs readiness (shallow DB ping).** v1 je plain 200 liveness (SM-D4). Da li biznis ikad želi zaseban `/readyz/` readiness endpoint sa shallow DB ping-om (signalizira „app može da servira saobraćaj", ne samo „proces živ")? **DEFER — nije 9.4 scope; budući zaseban endpoint ako zatreba.** Plain 200 je svesna v1 odluka.

---

## Host caveat (za Dev/TEA)

Native Windows `pytest` **ne može da collect-uje pun suite** (libmagic missing — `python-magic` zahteva system `libmagic`; dokumentovan **pre-existing baseline**, NIJE regresija ove story). Health view testovi su dizajnirani da to zaobiđu:
- `RequestFactory` + direktan poziv `healthz(request)` — izbegava pun URL-resolver/admin autodiscover koji triggeruje libmagic na host-u (AC1/AC6 mogu se asertovati bez test-client-a).
- Targetiran modul run: `pytest apps/core/tests/test_healthz.py` (ili `-p no:cacheprovider`) izoluje od širokog collect-a.
- Pun suite kroz Docker/CI Linux (sa libmagic) za potpunu verifikaciju.

Svi testovi se izvršavaju bez živog UptimeRobot account-a / network egress-a (AC8 manual gate je jedini eksterni deo, NE automatizovan).

## Definition of Done

- [ ] AC1-AC8 zadovoljeni (AC8 = manual go-live gate, dokumentovan)
- [ ] `GET /healthz/` → 200 + body `ok` (text/plain ili json), bez auth, bez env/secret leak
- [ ] `reverse("healthz") == "/healthz/"` (VAN locale prefiksa — non-i18n blok)
- [ ] `/healthz/` BEZ `@ratelimit` / `@login_required` (regression)
- [ ] `/healthz/` → 200 direktno, NE 301/302 (no-redirect)
- [ ] `assertNumQueries(0)` na view-callable (plain 200, bez DB)
- [ ] `ops/monitoring/uptimerobot.md` postoji (URL-ovi/keyword/5-min/email/maintenance/free-tier/checklist)
- [ ] (opciono) nginx `location = /healthz/` dodat ILI dokumentovano da `location /` catch-all pokriva
- [ ] `apps/core` ostaje leaf (health view 0 domain importa)
- [ ] `just lint` clean (ruff)
- [ ] TEA view/INFRA testovi prolaze (targetiran modul / Docker-CI)
- [ ] 0 migracija (verifikovano)
- [ ] 0 novih dep-ova (verifikovano — Django stdlib only)
