# Restore runbook — Story 9.5 (pg_dump + restic + Hetzner Storage Box)

Ovaj runbook opisuje kako restore-ovati encrypted restic backup baze/media i kako
izvršiti **mesečni manual restore-test** (verifikacija da backup NIJE corrupted).

Naming convention: srpska latinica + engleski identifikatori; bez ćirilice.

> **Svi creds** (restic password, Storage Box host/user/SSH key, rclone config,
> GlitchTip notify DSN) žive u box `.env` / rclone.conf — **NIKAD u repo-u**.
> Vidi [`ops/secrets/README.md`](../secrets/README.md) za tačne env var-ove.

---

## 1. Retention politika (7 / 4 / 3)

restic forget koristi **`--keep-daily 7 --keep-weekly 4 --keep-monthly 3 --prune`**
(7 dnevnih + 4 nedeljnih + 3 mesečnih → ~30-dnevna effective coverage). Ovo je
DR-robustnije od flat `--keep-daily 30` (manje snapshot-a, duži recovery horizont).

---

## 2. ⚠️ restic password — backup ODVOJENO / OFFLINE (kritično)

restic enkripcija je **client-side**: bez `RESTIC_PASSWORD` repo je kriptografski
**nepovratan**. **Gubitak password-a = trajni gubitak backup-a.**

- Čuvaj `RESTIC_PASSWORD` **ODVOJENO i OFFLINE** (password manager / sef / štampana
  kopija) — **NIKAD samo na istom boxu** koji backup-uješ. Ako box izgori/ransomware
  zaključa disk, izgubićeš i password i pristup backup-u istovremeno.
- Isto važi za Storage Box SSH key / rclone config.

---

## 3. Listanje snapshot-a

```bash
docker run --rm -e RESTIC_REPOSITORY -e RESTIC_PASSWORD_FILE \
  -v "${RCLONE_CONFIG_DIR}:/root/.config/rclone:ro" \
  "${RESTIC_IMAGE}" snapshots
```

Zabeleži `<snapshotID>` (kratki hash) koji želiš restore-ovati (DB ima `--tag db`,
media `--tag media`).

---

## 4. Restore DB snapshot-a na TEST bazu

`restore.sh` restore-uje na **LOKAL/TEST** cilj (`RESTORE_TARGET_DB`) i učitava plain
dump kroz `gunzip | psql` (NE `pg_restore` — plain-format par je zaključan).

> **DATA-LOSS GUARD (SM-D14):** `RESTORE_TARGET_DB` (ILI `RESTORE_DB_URL`) MORA biti
> postavljen na **TEST bazu** pre pokretanja. `restore.sh` **NIKAD** ne pada nazad na
> prod `DATABASE_URL` — fail-loud ako cilj nije eksplicitno postavljen. Nikad ne pokreći
> restore protiv žive prod baze bez svesne ručne intervencije.

```bash
export RESTORE_TARGET_DB="postgresql://coric:test@localhost:5432/coric_agrar_restore_test"
ops/backup/restore.sh <snapshotID>
```

---

## 5. Mesečni manual restore-test (OBAVEZNO — verify backup nije corrupted)

**Kadenca: jednom mesečno** (project-context:468). Owner je go-live gate (OQ-3 —
ko izvršava + kalendar/podsetnik se potvrđuje pre go-live). Schedule scaffold je
komentovan u `ops/backup/crontab` (1. u mesecu).

Checklist (popuni pri svakom mesečnom restore-test-u):

- [ ] `restic snapshots` izlistano, izabran poslednji `--tag db` snapshot
- [ ] `RESTORE_TARGET_DB` postavljen na TEST bazu (NE prod)
- [ ] `restore.sh <snapshotID>` izvršen bez grešaka
- [ ] `gunzip | psql` load u TEST DB prošao bez grešaka
- [ ] row-count / integrity sanity (npr. `SELECT count(*) FROM ...` na ključnim tabelama)
- [ ] media snapshot (`--tag media`) restore-test (po potrebi)
- [ ] zabeležen datum + ko je radio + rezultat

> **Host preduslov:** restore-test host mora imati instaliran **`postgresql-client`**
> (`psql`) i **`gunzip`** (gzip) — `restore.sh` ucitava plain dump kroz `gunzip -c | psql`
> na hostu (restic restore tece kroz Docker image, ali `gunzip|psql` load NE). Na
> Debian/Ubuntu: `sudo apt-get install -y postgresql-client gzip`.

> **SECURITY (cleanup posle restore-a):** restic restore raspakuje `*.sql.gz` u
> `RESTORE_DIR` (default `ops/backup/.restore`). `gunzip -c | psql` STREAM-uje (NE
> pise plaintext `.sql` na disk), ali raspakovani `*.sql.gz` (pun DB dump) ostaje u
> restore dir-u. Na DELJENOM/test boxu **obrisi restore dir posle verifikacije** da
> pun DB snapshot ne lezi nezasticen:
>
> ```bash
> rm -rf ops/backup/.restore   # ili custom [restoreDir] koji si prosledio
> ```

---

## 6. Troubleshooting

### `restic unlock` — stale repo lock (kill / OOM / network drop)

Prekinut restic run ostavi **stale lock** u repo-u; svaki naredni cron tiho fail-uje
(„repository is already locked exclusively") dok ne stigne GlitchTip notify. Ručno:

```bash
docker run --rm -e RESTIC_REPOSITORY -e RESTIC_PASSWORD_FILE \
  -v "${RCLONE_CONFIG_DIR}:/root/.config/rclone:ro" \
  "${RESTIC_IMAGE}" unlock
```

> `restic unlock` briše SVE lock-ove — NE pokreći ako drugi backup STVARNO trči.

### `restic check` — integritet repo-a (korupcija je tiha do restore-a)

Repo korupcija (bit-rot / parcijalan upload / backend bug) se NE detektuje pri
backup-u — otkriješ je tek kad restore padne (najgori trenutak). Pokreći periodično
(weekly/monthly):

```bash
docker run --rm -e RESTIC_REPOSITORY -e RESTIC_PASSWORD_FILE \
  -v "${RCLONE_CONFIG_DIR}:/root/.config/rclone:ro" \
  "${RESTIC_IMAGE}" check --read-data-subset=10%
```

Fail = repo korumpiran → istraži PRE nego što zatreba restore. Komentovana cron
linija je u `ops/backup/crontab`.

---

## 7. Reference

- Skripte: [`pg_backup.sh`](pg_backup.sh), [`media_backup.sh`](media_backup.sh),
  [`restore.sh`](restore.sh), deljeni helper [`_restic_common.sh`](_restic_common.sh).
- Cron: [`crontab`](crontab) (daily 03:00 UTC DB + weekly media + komentovan check/restore-test).
- Secrets: [`ops/secrets/README.md`](../secrets/README.md) (RESTIC_*, Storage Box, GlitchTip notify).
