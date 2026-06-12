// Story 9.9 — k6 load test (read-heavy javne GET rute) protiv env-driven BASE_URL.
//
// SM-D5: k6 PREKO locust (single static binary, JS skripta, thresholds first-class,
//   0 Python runtime → ne sudara se sa libmagic host baseline-om).
// SM-D6: NE pokrece se u CI v1 — load test = MANUAL go-live korak (OQ-2). Runbook:
//   ops/perf/README.md. NIKAD protiv prod-a bez dogovora; potvrdi staging kapacitet (CX22).
//
// Pokretanje:  k6 run -e BASE_URL=https://staging.example.tld ops/perf/load_test.js
//
// Thresholds (AC5):
//   http_req_duration p(95) < 600ms   — TTFB-ekvivalent server response p95 budget
//   http_req_failed   rate  < 0.01    — < 1% neuspelih zahteva

import http from 'k6/http';
import { check, sleep } from 'k6';

// fail-loud: NIKAD hardkodovan prod URL. Ako BASE_URL nije postavljen → throw (OQ-2 guard).
const BASE_URL = __ENV.BASE_URL;
if (!BASE_URL) {
  throw new Error(
    'BASE_URL env nije postavljen — pokreni: k6 run -e BASE_URL=https://staging... ' +
    'ops/perf/load_test.js (NIKAD prod bez dogovora; OQ-2).',
  );
}

export const options = {
  stages: [
    { duration: '30s', target: 20 },  // ramp 0 → 20 VU
    { duration: '60s', target: 50 },  // ramp/hold 20 → 50 VU
    { duration: '30s', target: 0 },   // ramp-down 50 → 0 VU
  ],
  thresholds: {
    http_req_duration: ['p(95)<600'],  // p95 < 600ms (TTFB-budget ekvivalent)
    http_req_failed: ['rate<0.01'],    // < 1% fail
  },
};

// Read-heavy JAVNE rute (GET) — deterministicki 9-7 seed slug-ovi. Admin/forme NISU ovde
// (login-gated / write-side; load test cilja javni read path).
const ROUTES = [
  '/sr/',
  '/sr/traktori/',
  '/sr/proizvod/agri-tracking-tb804/',
  '/sr/blog/',
];

export default function () {
  for (const path of ROUTES) {
    const res = http.get(`${BASE_URL}${path}`);
    check(res, { 'status 200': (r) => r.status === 200 });
  }
  sleep(1);
}
