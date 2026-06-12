# Retrospektiva — Epic 9: Go-Live Readiness (Production + Quality)

**Datum:** 2026-06-12
**Orkestrator:** Siniša (Epic Orchestrator)
**Priče:** 10/10 done (9-1 … 9-10), 0 blokiranih
**Grana:** `epic-9` (per-story `--no-ff` merge-evi); git strategija = epic grana + EM merge (Mihas izbor)

---

## Rezime isporuke

Epic 9 je kompletan infrastrukturni + kvalitetni sloj pred go-live, isporučen autonomno kroz 10 priča, svaka delegirana svežoj Dani (create→validate→implement→review→report) sa blocking-only mandatom.

| # | Priča | Ključni deliverable | Testovi |
|---|---|---|---|
| 9-1 | Production Docker Compose + Nginx | prod-parity stack (gunicorn, nginx 443, security headers, start.sh) | 37/38 (Docker) |
| 9-2 | Hetzner Deploy + SSL | deploy.sh/rollback.sh, certbot bootstrap, deploy.yml, GHCR | 75/75 |
| 9-3 | GlitchTip 6 Self-host | sentry-sdk DSN-guarded init, compose stack, send_default_pii=False | 32/32 |
| 9-4 | UptimeRobot | `/healthz/` liveness endpoint + runbook | 17/17 |
| 9-5 | pg_dump + restic Backup | off-site encrypted DR, retencija 7/4/3, fail-loud | 49/49 |
| 9-6 | Django Logging | LOGGING dict console→stdout, Sentry-safe propagate | 28/28 |
| 9-7 | Sample Seed Data | idempotentni `seed_sample_data` mgmt command, prod-guard | 32/32 + 130 core |
| 9-8 | Playwright E2E (3 UJ) | pytest-playwright suite, e2e marker izolacija, e2e.yml CI | struct + CI-deferred |
| 9-9 | A11y + Perf Audit | axe WCAG 2.1 AA, Lighthouse budgeti, k6 load, AUDIT-REPORT | harness + CI-deferred |
| 9-10 | WebP/AVIF + Lighthouse | hero AVIF(-59%)/WebP(-41%) `<picture>`, Lighthouse gate ENFORCED | 41/41 |

Epic-level integration (Docker): **2914 passed, 0 epic-9 regresija** (17 pre-existing foundational baseline + 7 CI-deferred e2e — sve van epic-9 scope-a).

---

## Šta je dobro funkcionisalo (Keep)

- **Review-panel diverzitet hvata runtime bugove koje grep-lock testovi ne mogu.** Najveća vrednost epica: paneli su uhvatili stvarne produkcijske bagove na granici "prolazi parser, ne radi u produkciji":
  - 9-2: certbot↔nginx bootstrap gap + GHCR image koji se nikad ne pull-uje (2 BUG-a)
  - 9-5: pg_dump bez PGPASSWORD (prod auth-fail), `restic forget` bez backend-mount (retention pada svaki run), restore SIGPIPE pod pipefail (3 MANDATORY)
  - 9-8: 9 pogrešnih story-pretpostavki o postojećim feature-ima + 4 review BUG-a
  - 9-8 bonus: Dana otkrila i zatvorila REALAN 9-7 seed gap (published-but-unlisted tractors)
- **Honest CI-deferral umesto fabrikovanog green-a.** 9-8/9-9/9-10 su pošteno prijavili da Windows host ne može Playwright browser/Lighthouse/k6, i postavili autoritativne CI runner-e (e2e.yml, lighthouse.yml) umesto lažnih brojeva.
- **Reconciliacija epics.md fikcije vs živi kod** dosledno kroz sve priče (9-1 command:-override broken, 9-5 retention 7/4/3 vs flat-30, 9-10 nema izmišljenog sorl setting-a).
- **Scope disciplina** — svaka priča je tvrdo deferovala susede (9.10 image-opt iz 9.9, uploaded-media WebP iz 9.10).

## Šta je bolelo (Problems)

- **Dana je orfanirala background validatore na PRVOJ priči (9-1).** Prvi Dana subagent je lansirao 3 validatora preko `run_in_background` pa joj se turn završio — deca su izveštavala parenta (Sinišu), a Dana nije bila živa da ih sakupi. **Fix:** blocking-only mandat ubrizgan u SVAKU sledeću delegaciju (9-2…9-10) → 0 ponavljanja. **Lekcija za workflow: sub-orkestrator NE SME koristiti run_in_background za panele; mora ostati živ kroz ceo lifecycle u jednom turn-u (paralelizam = više BLOCKING Task poziva u jednoj poruci).**
- **Native Windows pytest ne može collection** (libmagic nedostaje → `apps/media_pipeline/pdf_utils.py:import magic` puca na admin autodiscover). Sve verifikacije su morale u Docker. Dokumentovani baseline, ne regresija, ali usporava per-story i epic verifikaciju.
- **Test-ownership drift:** stories 9-1/9-2/9-3 su menjale ci.yml/Dockerfile/compose ali nisu ažurirale stare Epic-1 testove (`test_ci_workflow_config`, `test_docker_compose`) → 4 stale fail-a uhvaćena tek u epic-level integration. **Lekcija: kad priča menja deljeni config, mora reconcile-ovati tuđe testove tog config-a u istom koraku.**

## Probati sledeći put (Try)

- Workflow update: dodati eksplicitan blocking-only guard u Daninu step-02/step-04 panel logiku (da Siniša ne mora ručno da ubrizgava mandat).
- Razmotriti devcontainer/Docker-first test harness da se libmagic baseline ukloni i native verifikacija proradi.
- "Shared-config-touch" pravilo: kad story dira ci.yml/Dockerfile/compose/settings, grep-ovati tuđe testove tog fajla i reconcile-ovati ih u istoj priči.

---

## ⚠️ Akumulirani go-live gate-ovi (van koda — Mihas odluke pre produkcije)

1. **OQ-1 (TVRD, 9-2): `master` → `main`/`staging` branch naming.** `deploy.yml` trig na main/staging, repo default je master. Reši pre push-triggered deploy-a.
2. **RISK-1 (Epic 7): legal sadržaj** — pravne strane su Lorem placeholder; Mihas legal sign-off pre go-live (mehanizam nh3 rešen).
3. **Prod secrets na boxu** (9-2/9-3/9-5): POSTGRES_PASSWORD, DEPLOY_* + host fingerprint, RESTIC_PASSWORD + Storage Box creds, GlitchTip DSN/secret-key, DJANGO_SUPERUSER_* (CI e2e). Nikad u repo.
4. **Staging verifikacija (9-8/9-9/9-10):** stvarni Playwright e2e green + Lighthouse brojevi (a11y≥0.95/LCP<2.5s/TTFB<600/byte<1.5MB) + k6 load + NVDA/keyboard manual potpis — sve CI/staging-autoritativno.
5. **OQ-5 (Epic 8): AXES_IPWARE_PROXY_COUNT** prod-proxy IP — go-live gate.
6. **9-3 OQ-2:** ukupan RAM footprint na deljenom boxu (~512MB GlitchTip) = #1 ops rizik, sizing pre prod.
7. **9-6 OQ-1:** host journald/Docker log rotacija (max-size/max-file = 14d retencija ekvivalent).
8. **9-4:** UptimeRobot account/monitor kreiranje (manual, runbook postoji).
9. **9-10 OQ-4:** Whitenoise `.avif` MIME staging-verify.

## Arhitektonske napomene (deferred)

- 9-7: core→domain seed-command presedan — zabeležiti u project-context.md anti-pattern sekciju (kandidat za buduće).
- 9-10: uploaded-media WebP (sorl `responsive_picture`) deferred — regression-rizik na 6+ caller-a (Epic 2/3/5).
