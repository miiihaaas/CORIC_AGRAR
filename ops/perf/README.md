# k6 Load Test — runbook (Story 9.9)

Load test harness za Ćorić Agrar javne (read-heavy) rute. Skripta: [`load_test.js`](./load_test.js).

> **SM-D6 — load test je MANUAL go-live korak (OQ-2), NE deo CI v1.** Izvršava se ručno
> protiv **staging**-a pred go-live; rezultat se upisuje u
> [`ops/quality/AUDIT-REPORT.md`](../quality/AUDIT-REPORT.md).
>
> ⚠️ **NIKAD protiv produkcije bez izričitog dogovora.** Skripta je env-driven (`BASE_URL`) i
> **fail-loud** ako `BASE_URL` nije postavljen — nema hardkodovanog prod URL-a. Pre gađanja
> shared staging-a (CX22 box) potvrdi kapacitet sa timom.

---

## 1. Instalacija k6

k6 je jedan statički binar (nema Python/Node runtime zavisnost — SM-D5).

| OS       | Komanda                                                        |
| -------- | ------------------------------------------------------------- |
| Windows  | `winget install k6.k6` ili `choco install k6`                 |
| macOS    | `brew install k6`                                             |
| Linux    | k6 apt repo (vidi snippet ispod) pa `sudo apt-get install k6` |
| Docker   | `docker run --rm -i -e BASE_URL=... grafana/k6 run - <load_test.js` |

Linux (Debian/Ubuntu) — dodaj k6 apt repo pre instalacije (zvanični Grafana snippet):

```bash
sudo gpg -k
sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg \
  --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" \
  | sudo tee /etc/apt/sources.list.d/k6.list
sudo apt-get update
sudo apt-get install k6
```

Provera: `k6 version`.

## 2. Pokretanje

```bash
# Staging (PREPORUČENO — autoritativni go-live brojevi):
k6 run -e BASE_URL=https://staging.coric-agrar.example.tld ops/perf/load_test.js

# Lokalni dev stack (indikativno, runserver/Docker NIJE prod nginx/Whitenoise):
k6 run -e BASE_URL=http://localhost:8000 ops/perf/load_test.js
```

Ako `BASE_URL` nije prosleđen, skripta baca grešku i odmah staje (OQ-2 guard).

## 3. VU profil (stages)

| Faza            | Trajanje | Ciljni VU | Svrha                        |
| --------------- | -------- | --------- | ---------------------------- |
| ramp-up         | 30s      | 0 → 20    | postepeno opterećenje        |
| ramp/hold       | 60s      | 20 → 50   | vršno opterećenje            |
| ramp-down       | 30s      | 50 → 0    | uredno gašenje               |

Rute (read-heavy GET): `/sr/`, `/sr/traktori/`, `/sr/proizvod/agri-tracking-tb804/`, `/sr/blog/`.

## 4. Pragovi (thresholds) — šta znače

| Threshold                          | Značenje                                                          |
| ---------------------------------- | ---------------------------------------------------------------- |
| `http_req_duration: p(95) < 600`   | 95% zahteva mora odgovoriti za **< 600 ms** (TTFB-budget ekvivalent). |
| `http_req_failed: rate < 0.01`     | manje od **1%** zahteva sme da padne (non-2xx/3xx / mrežni fail). |

Ako bilo koji prag **padne**, k6 izlazi sa **non-zero exit kodom** i ispisuje
`✗` pored prekršenog praga u summary tabeli.

## 5. Čitanje izlaza

Na kraju run-a k6 štampa summary. Ključni redovi:

- `http_req_duration ... p(95)=XXXms` — uporedi sa **600 ms** budgetom.
- `http_req_failed ... XX.XX%` — uporedi sa **1%** budgetom.
- `vus` / `vus_max` — broj virtuelnih korisnika (potvrda da je profil dostignut).
- `iterations` / `http_reqs` — ukupan broj prolaza / HTTP zahteva.

Upiši p(95), http_req_failed rate, datum, ciljni env (staging URL) i k6 verziju u
[`AUDIT-REPORT.md`](../quality/AUDIT-REPORT.md) → sekcija „k6 load test". **Ne fabrikuj brojeve** —
ako test nije pokrenut, ostavi „TBD — staging k6 run".

## 6. Go-live gate (OQ-2)

Pre launch-a: pokreni `BASE_URL=<staging> k6 run`, potvrdi da oba praga prolaze (ili
dokumentuj odstupanje + remediation Issue), upiši rezultat u AUDIT-REPORT i potpiši OQ-2.
