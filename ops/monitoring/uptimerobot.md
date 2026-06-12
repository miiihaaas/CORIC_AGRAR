# UptimeRobot Runbook — Uptime Monitoring (Story 9.4)

Ovaj dokument opisuje **eksternu, manuelnu** konfiguraciju UptimeRobot free-tier
naloga za uptime monitoring CORIC AGRAR sajta. Posao se obavlja RUKOM u
UptimeRobot web dashboard-u na go-live — **NE postoji UptimeRobot API/provisioning
kod u ovom repo-u** (SM-D1). Jedini kod-deliverable iz 9.4 je `/healthz/` health
endpoint (`apps/core/views.py` + `config/urls.py`); ovaj fajl pokriva eksterni deo.

UptimeRobot je **komplement** GlitchTip-u (9.3): UptimeRobot prati **dostupnost**
(uptime — da li sajt odgovara), GlitchTip prati **greške** (error tracking). DB
hiccup TREBA da page-uje kroz GlitchTip, NE da flap-uje uptime monitor — zato je
`/healthz/` plain 200 bez DB ping-a (SM-D4).

---

## 1. Health endpoint (implementiran u repo-u)

- **URL putanja:** `/healthz/` (VAN locale prefiksa — bare path, NE `/sr/healthz/`).
- **Odgovor:** HTTP `200`, `Content-Type: text/plain`, body je TAČNO `ok`.
- **Keyword za monitor:** `ok` (lowercase, tačno tako — mora se poklapati sa view body-jem).
- Bez auth, bez ratelimit, bez DB query-ja. Informaciono prazan body (no env/secret/version/hostname leak).

---

## 2. Monitor URL-ovi

> **OQ-1 (go-live gate):** finalni domeni zavise od 9.2 (prod/staging domen + DNS)
> i 9.3 (GlitchTip subdomena vs port). Placeholder-i ispod se zamenjuju pravim
> vrednostima pre go-live (Mihas potvrda).

| Monitor | URL | Tip |
|---|---|---|
| Production | `https://<prod-domen>/healthz/` | HTTP(S) keyword |
| Staging | `https://<staging-domen>/healthz/` | HTTP(S) keyword |
| GlitchTip | `https://<glitchtip-target>/` | HTTP(S) keyword (npr. login/health stranica GlitchTip-a) |

---

## 3. Konfiguracija monitora (za svaki od gornja 3)

- **Monitor Type:** `HTTP(S)` — **keyword monitor**.
- **Keyword:** `ok` (mora se TAČNO poklapati sa body-jem `/healthz/` endpoint-a).
  - Za GlitchTip monitor keyword prilagoditi sadržaju GlitchTip target stranice.
- **HTTP metoda:** **GET** (NE HEAD). Django na `HEAD` request-u vraća 200 ali
  STRIP-uje response body → keyword `ok` se NE bi pronašao → lažni „down" (G-13).
- **URL trailing slash:** MORA imati trailing slash `https://.../healthz/`. BEZ
  trailing slash-a Django `APPEND_SLASH` vraća `301` `/healthz` → `/healthz/`
  (nepotreban hop; UptimeRobot ga prati ali je čistije direktno) (G-13/G-10).
- **Interval:** **5 minuta** (AR-20 free-tier minimum).
- **HTTPS:** koristiti `https://` direktno. Iza nginx-a (9.2) koji terminira TLS
  i šalje `X-Forwarded-Proto: https`, `SECURE_SSL_REDIRECT` NE okida za `/healthz/`
  → 200 direktno, bez SSL redirect loop-a (G-4).

### ⚠️ ALLOWED_HOSTS / domen-ne-IP (G-8)

Monitor MORA koristiti **domen koji je u `DJANGO_ALLOWED_HOSTS`** (npr.
`coricagrar.rs`), **NE goli VPS IP**. Ako monitor pinga goli IP, Django vraća
`400 DisallowedHost` → lažni „down". (Alternativa: dodati IP u ALLOWED_HOSTS —
NE preporučeno; domen je čistiji.)

---

## 4. Alert kontakti

- **Tip:** email alert contact.
- **Recipient:** `<alert-email>` — **OQ-3 (go-live gate):** na koju adresu idu
  down/up alert-i (Mihas / tim / alias)? Potvrda pre go-live.
- UptimeRobot šalje email čim monitor vrati non-200 (down) i ponovo kad se vrati
  (up).

---

## 5. Maintenance window (deploy prozori)

- Tokom deploy prozora **pauzirati / ignorisati** monitore da deploy downtime ne
  generiše lažne down alert-e (epics:1232).
- **OQ-4 (go-live gate):** politika — manuelni pause u dashboard-u tokom deploy-a,
  ILI automatski pause kroz deploy skriptu (UptimeRobot pause API). Auto-pause kroz
  `deploy.sh` je 9.2-style proširenje — **DEFER**, nije 9.4 scope osim ako Mihas ne traži.

---

## 6. Public status page (opciono)

- UptimeRobot nudi opcioni javni status page (epics:1233).
- **OQ-4 (go-live gate):** da li se pravi i sa kim se deli? Opciono — nije obavezan
  deliverable.

---

## 7. Free-tier limiti (AR-20)

- **50 monitora** maksimalno.
- **5 min** minimalni interval.
- 3 monitora (prod / staging / GlitchTip) su komotno unutar limita.

---

## 8. nginx napomena (SM-D5)

Dedikovan `location = /healthz/` blok u `compose/nginx/nginx.conf` **NIJE dodat** —
postojeći `location /` catch-all proxy (`nginx.conf` ~108-118) VEĆ proxy-uje
`/healthz/` ka Gunicorn-u, pa je endpoint dostupan. Dedikovan exact-match location
sa `access_log off` bio bi SAMO log-noise optimizacija (~288 pingova/dan po
monitoru) — svesno preskočeno da blast radius ostane mali. Ako se ikad doda, MORA
replicirati `proxy_set_header X-Forwarded-Proto $scheme` (inače SSL redirect loop, G-4).

---

## 9. Go-live checklist (manual gate — AC8)

- [ ] UptimeRobot free account registrovan (OQ-2)
- [ ] Production monitor kreiran (`https://<prod-domen>/healthz/`, GET, keyword `ok`, 5 min)
- [ ] Staging monitor kreiran (`https://<staging-domen>/healthz/`, GET, keyword `ok`, 5 min)
- [ ] GlitchTip monitor kreiran (`https://<glitchtip-target>/`)
- [ ] Email alert kontakt potvrđen i dodat na sve monitore (OQ-3)
- [ ] Maintenance-window politika dogovorena (manual vs auto-pause) (OQ-4)
- [ ] (opciono) Public status page kreiran i podeljen (OQ-4)

---

## 10. Rezidualne Open Questions (go-live gates)

| OQ | Pitanje | Vlasnik |
|---|---|---|
| OQ-1 | Finalni prod/staging/GlitchTip URL-ovi (zavisi 9.2 domen/DNS + 9.3 GlitchTip target) | Mihas |
| OQ-2 | Registracija free account + 3 monitora (eksterno, manual) | Mihas / operator |
| OQ-3 | Alert email recipient(s) | Mihas |
| OQ-4 | Maintenance-window politika + public status page yes/no | Mihas / infra |
