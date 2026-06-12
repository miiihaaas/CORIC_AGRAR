"""Tests za Story 9.5 — pg_dump + restic + Hetzner Storage Box Backup.

INFRA-VERIFY testovi (needs_e2e=false — NE Playwright/browser). Ovo NIJE Django
app — deliverable-i su SHELL skripte + cron + restore runbook + secrets edit:
  - ops/backup/pg_backup.sh      (daily DB backup: pg_dump -> gzip -> temp -> restic push)
  - ops/backup/media_backup.sh   (weekly restic snapshot media named volume-a)
  - ops/backup/restore.sh        (restore <snapshotID> na LOKAL/TEST: gunzip | psql)
  - ops/backup/_restic_common.sh (OPCIONO deljeni helper — G-14; uracunava se u *.sh grep-ove)
  - ops/backup/crontab           (TZ=UTC + daily 03:00 UTC + weekly media; apsolutne putanje)
  - ops/backup/RESTORE.md        (mesecni restore-test runbook + unlock/check/offline-pass)
  - ops/secrets/README.md        (UPDATE: backup var-ovi RESTIC_*/Storage Box/GlitchTip notify)

Test pristup je IMPORT-LIGHT (mirror tests/test_deployment_ssl.py /
test_glitchtip_monitoring.py host-runnable obrazac):
  - file-parsing (pathlib + re SAMO) za sve grep/marker asercije,
  - opcioni `bash -n` SUBPROCESS parse SAMO ako je `bash` na PATH-u (Git-bash na
    Windows); inace pytest.skip (host-portable — shellcheck/bats NISU instalirani).

NE import-uje Django apps/settings, NE zahteva DB, NE pokrece stvarni restic/pg_dump
(taj run = Docker/CI/box). Zato fajl COLLECT-uje i trci na native Windows host-u
uprkos dokumentovanom libmagic baseline-u (python-magic missing — pre-existing, NIJE
regresija ove story).

Pokrenuti sa (host-friendly):
    python -m pytest tests/test_backup_restic.py -v -p no:cacheprovider

TEA RED faza: SVI testovi MORAJU pasti/error-ovati dok Dev ne kreira artefakte
(ops/backup/ jos NE postoji). `_read_file` fail-uje (RED signal) sa jasnom porukom
kad fajl ne postoji → svaki test fail-uje sa FileNotFound-stilom poruke (mirror
test_deployment_ssl.py / test_glitchtip_monitoring.py RED ponasanja).

Naming convention: srpska latinica + engleski identifikatori; bez cirilice.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest

# =============================================================================
# Konstante (project paths) — mirror REPO_ROOT pattern iz test_deployment_ssl.py
# =============================================================================

REPO_ROOT = Path(__file__).resolve().parent.parent

OPS_DIR = REPO_ROOT / "ops"
BACKUP_DIR = OPS_DIR / "backup"

PG_BACKUP_SH = BACKUP_DIR / "pg_backup.sh"
MEDIA_BACKUP_SH = BACKUP_DIR / "media_backup.sh"
RESTORE_SH = BACKUP_DIR / "restore.sh"
CRONTAB = BACKUP_DIR / "crontab"
RESTORE_MD = BACKUP_DIR / "RESTORE.md"

SECRETS_README = OPS_DIR / "secrets" / "README.md"

# Sve tri OBAVEZNE backup skripte (parametrizovani fail-loud / set -euo pipefail testovi).
ALL_SCRIPTS = [PG_BACKUP_SH, MEDIA_BACKUP_SH, RESTORE_SH]

# Named media volume iz 9.1 (compose/production.yml:203-209).
MEDIA_VOLUME = "coric_agrar_production_media"

# Pg-dump marker koji non-empty guard moze da grep-uje (SM-D7/AC8).
PG_DUMP_MARKER = "-- PostgreSQL database dump"


# =============================================================================
# Helper funkcije (mirror _read_file iz test_deployment_ssl.py)
# =============================================================================


def _read_file(path: Path, owner: str = "Story 9.5") -> str:
    """Procita text fajl. Fail-uje (RED signal) sa jasnom porukom ako ne postoji."""
    if not path.exists():
        pytest.fail(f"Missing required file: {path}\n{owner} Dev ga mora kreirati/azurirati.")
    return path.read_text(encoding="utf-8")


def _read_backup_sh_glob() -> dict[Path, str]:
    """Vrati {path: content} za SVE ops/backup/*.sh (ukljucujuci opcioni _restic_common.sh).

    RETENTION/IDEMPOTENCY grep-ovi gledaju preko SVIH skripti tako da deljeni helper
    (G-14 `_restic_common.sh`) i dalje broji — izbegava false-negative ako Dev extract-uje
    logiku (MEDIUM-10). Fail-uje (RED) ako BACKUP_DIR jos ne postoji."""
    if not BACKUP_DIR.exists():
        pytest.fail(
            f"Missing required dir: {BACKUP_DIR}\n"
            f"Story 9.5 Dev mora kreirati ops/backup/ sa skriptama."
        )
    shs = sorted(BACKUP_DIR.glob("*.sh"))
    if not shs:
        pytest.fail(
            f"Nema nijedne *.sh skripte u {BACKUP_DIR}.\n"
            f"Story 9.5 Dev mora kreirati pg_backup.sh / media_backup.sh / restore.sh."
        )
    return {p: p.read_text(encoding="utf-8") for p in shs}


def _strip_comments(content: str) -> str:
    """Vrati samo izvrsne (non-`#`-prefiks) linije shell skripte.

    Za negative grep-ove i ORDERING-ove koji NE smeju da matchuju komentar-marker tekst.
    """
    return "\n".join(
        ln for ln in content.splitlines() if not ln.lstrip().startswith("#")
    )


def _strip_comments_and_echo(content: str) -> str:
    """Kao `_strip_comments`, ali takodje izbacuje `echo ...` label linije.

    Za ORDERING-ove koji MORAJU verifikovati redosled STVARNIH komandi (npr.
    `restic_run backup` / `restic_run forget`), a NE redosled `echo "[BACKUP] restic
    backup ..."` label-tekstova koji slucajno sadrze iste reci.
    """
    out = []
    for ln in content.splitlines():
        stripped = ln.lstrip()
        if stripped.startswith("#"):
            continue
        if re.match(r"echo\b", stripped):
            continue
        out.append(ln)
    return "\n".join(out)


def _index_of(pattern: str, text: str, flags: int = 0) -> int:
    """Vrati start indeks PRVOG matcha pattern-a u tekstu, ili -1 ako nema."""
    m = re.search(pattern, text, flags)
    return m.start() if m else -1


def _bash_bin() -> str | None:
    """Vrati IZVRSNU `bash` putanju (Git-bash na Windows) ili None.

    HARDENING (host-portability): vrati None i ako `bash` postoji na PATH-u ali NE
    izvrsava (npr. Windows System32 `bash.EXE` je WSL relej koji error-uje umesto da
    pokrene bash) — tako `bash -n` testovi skip-uju na bare Windows hostu bez Git-bash,
    a OSTAJU da trce kad je pravi bash prisutan."""
    bash = shutil.which("bash")
    if bash is None:
        return None
    try:
        probe = subprocess.run(
            [bash, "-c", "true"],
            capture_output=True,
            text=True,
            shell=False,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return bash if probe.returncode == 0 else None


# Forbidden secret-leak pattern-i (AC11/SM-D10) — provera RAW sadrzaja backup fajlova.
# Password-literal regex MORA propustiti bezbedne env-passthrough/default forme
# (`RESTIC_PASSWORD="${RESTIC_PASSWORD:-}"`, `: "${POSTGRES_PASSWORD:?...}"`) i hvatati
# SAMO pravu hardkodovanu vrednost (prvi ne-quote token NIJE `$`-ekspanzija). Negativni
# lookahead `(?!["']?\$)` propusta value koji pocinje (opcionim quote pa) `$` ekspanzijom.
_PASSWORD_LITERAL = (
    r"^\s*(?:export\s+)?(?:RESTIC_PASSWORD|POSTGRES_PASSWORD)\s*=\s*"
    r"(?!\s*$)"             # ne prazna vrednost (`VAR=`)
    r"(?!['\"]?\s*$)"       # ne samo prazan string (`VAR=`)
    r"(?!\"\"\s*$)"         # ne prazan dvostruki quote (`VAR=\"\"`)
    r"(?!''\s*$)"           # ne prazan jednostruki quote (`VAR=''`)
    r"(?!['\"]?\$)"         # ne `$`-ekspanzija (`VAR=$FOO` / `VAR=\"${FOO:-}\"`)
    r"\S"
)
_SECRET_LEAK_PATTERNS = [
    (r"BEGIN [A-Z ]*PRIVATE KEY", "PEM private key block"),
    (_PASSWORD_LITERAL, "hardkodovan ne-prazan password literal"),
    (r"ghp_[A-Za-z0-9]{20,}", "GitHub Personal Access Token"),
]


# =============================================================================
# AC1 — ops/backup/pg_backup.sh postoji + pg_dump correctness (exec -T postgres)
# =============================================================================


def test_ac1_pg_backup_sh_exists():
    """# AC-1/Task 2.1: `ops/backup/pg_backup.sh` MORA postojati (daily DB backup)."""
    assert PG_BACKUP_SH.exists(), (
        f"Missing required file: {PG_BACKUP_SH}\n"
        f"AC1/Task 2: pg_dump -> gzip -> temp -> restic encrypt push -> Storage Box."
    )


def test_ac1_pg_backup_sh_uses_pg_dump_no_owner():
    """# AC-1/SM-D2/G-16: pg_backup.sh poziva `pg_dump` sa `--no-owner` (cist restore u svez DB)."""
    content = _read_file(PG_BACKUP_SH)
    assert re.search(r"\bpg_dump\b", content), (
        "ops/backup/pg_backup.sh ne poziva `pg_dump`. AC1/SM-D2."
    )
    assert re.search(r"--no-owner", content), (
        "ops/backup/pg_backup.sh nema `--no-owner`. SM-D2/G-16: cist restore u svez DB "
        "(bez owner-stmt fail-a na role-koji-ne-postoji)."
    )
    assert re.search(r"--no-privileges", content), (
        "ops/backup/pg_backup.sh nema `--no-privileges`. AC1/SM-D2/G-16: uz `--no-owner`, "
        "izostavlja GRANT/REVOKE stmt-ove → cist restore u svez DB sa drugim role-ovima."
    )


def test_ac1_pg_backup_sh_targets_postgres_service_exec_t():
    """# AC-1/SM-D2/G-2: pg_dump MORA teci PROTIV `postgres` servisa kroz
    `docker compose ... exec -T postgres` (NO TTY za cron; postgres NEMA host port)."""
    content = _strip_comments(_read_file(PG_BACKUP_SH))
    assert re.search(
        r"docker\s+compose\s+.*\bexec\s+-T\b[^\n]*\bpostgres\b", content
    ) or re.search(r"docker\s+compose\s+.*\brun\s+--rm\b[^\n]*\bpostgres\b", content), (
        "ops/backup/pg_backup.sh ne cilja `postgres` servis kroz `docker compose exec -T "
        "postgres` (ILI `run --rm`). SM-D2/G-2: postgres NEMA host port → bare host pg_dump "
        "= connection refused; `-T` (no TTY) je OBAVEZAN za cron."
    )


def test_ac1_pg_backup_sh_plain_format_not_custom_fc():
    """# AC-1/SM-D13: pg_dump je PLAIN format (NE custom `-Fc`) — par sa `gunzip|psql` restore.

    `-Fc` bi zahtevao pg_restore (SM-D13 zakljucava plain par). Negative na izvrsnu liniju.
    """
    content = _strip_comments(_read_file(PG_BACKUP_SH))
    assert not re.search(r"pg_dump[^\n]*-Fc\b", content) and not re.search(
        r"pg_dump[^\n]*--format[= ]c", content
    ), (
        "ops/backup/pg_backup.sh koristi custom `-Fc`/`--format=c` pg_dump. SM-D13: 9.5 "
        "zakljucava PLAIN format (`pg_dump | gzip` ⇒ restore `gunzip | psql`, NE pg_restore)."
    )


def test_ac1_pg_backup_sh_db_creds_from_env_not_literal():
    """# AC-1/SM-D2/SM-D10: DB user/db iz env (`${POSTGRES_USER}`/`${POSTGRES_DB}`), NE literal."""
    content = _read_file(PG_BACKUP_SH)
    assert re.search(r"\$\{?POSTGRES_USER", content), (
        "ops/backup/pg_backup.sh ne koristi `${POSTGRES_USER}` env var (pg_dump -U). "
        "SM-D2/SM-D10: credentials iz env-a, NIKAD literal."
    )
    assert re.search(r"\$\{?POSTGRES_DB", content), (
        "ops/backup/pg_backup.sh ne koristi `${POSTGRES_DB}` env var (pg_dump -d). SM-D2/SM-D10."
    )


# =============================================================================
# AC2 — RETENTION LOCK: TACAN 7/4/3 --prune; NEMA flat keep-daily 30 (SM-D1)
# =============================================================================


def test_ac2_retention_exact_flags_present_across_backup_scripts():
    """# AC-2/SM-D1 (RETENTION LOCK): preko SVIH ops/backup/*.sh — TACNO `--keep-daily 7`,
    `--keep-weekly 4`, `--keep-monthly 3`, `--prune` (epics 7/4/3 SOT, NE flat 30).

    Grep preko svih *.sh (ukljucujuci opcioni _restic_common.sh helper — MEDIUM-10) tako da
    extract-ovana retention logika i dalje broji."""
    blob = "\n".join(_read_backup_sh_glob().values())
    required = {
        "--keep-daily 7": r"--keep-daily\s+7\b",
        "--keep-weekly 4": r"--keep-weekly\s+4\b",
        "--keep-monthly 3": r"--keep-monthly\s+3\b",
        "--prune": r"--prune\b",
    }
    missing = [name for name, pat in required.items() if not re.search(pat, blob)]
    assert not missing, (
        f"ops/backup/*.sh nedostaju TACNI retention flagovi: {missing}. "
        f"AC2/SM-D1: `restic forget --keep-daily 7 --keep-weekly 4 --keep-monthly 3 --prune` "
        f"(epics 7/4/3 je SOT nad project-context flat-30)."
    )


def test_ac2_no_flat_keep_daily_30():
    """# AC-2/SM-D1/G-5 (REVIEW ZAMKA): NIJEDNA backup skripta NE SME imati flat `--keep-daily 30`.

    project-context:467 „30 dana" je lako pogresno mapirati na `--keep-daily 30`; epics 7/4/3 je SOT.
    """
    blob = "\n".join(_read_backup_sh_glob().values())
    assert not re.search(r"--keep-daily\s+30\b", blob), (
        "ops/backup/*.sh sadrzi flat `--keep-daily 30`. AC2/SM-D1/G-5: epics 7/4/3 je SOT — "
        "koristi `--keep-daily 7 --keep-weekly 4 --keep-monthly 3 --prune`, NE flat 30."
    )


def test_ac2_prune_gated_after_nonempty_guard_in_pg_backup():
    """# AC-2/SM-D7/G-17 (PRUNE GATE): `restic forget`/`--prune` dolazi STRUKTURNO POSLE
    non-empty dump guard-a u pg_backup.sh (forget NE sme da prune-uje na nizu losih run-ova).

    Proxy: non-empty check (`test -s`/`[ -s`/marker grep) prethodi `forget`/`--prune` u toku skripte,
    i NEMA `|| true` maskiranja (set -e prekida pre forget-a ako push padne)."""
    # HARDENING: strip-uj i komentare I `echo` label-linije → meri redosled STVARNIH
    # komandi (`restic_run forget`/`--prune`), NE echo-label teksta.
    content = _strip_comments_and_echo(_read_file(PG_BACKUP_SH))
    guard_idx = _index_of(
        rf"test\s+-s\b|\[\s+-s\b|{re.escape(PG_DUMP_MARKER)}", content
    )
    forget_idx = _index_of(r"\bforget\b|--prune\b", content)
    assert guard_idx != -1, (
        "ops/backup/pg_backup.sh nema non-empty dump guard (`test -s`/`[ -s`/marker grep). "
        "AC8/SM-D7: obavezan PRE restic push-a (i pre forget/prune)."
    )
    assert forget_idx != -1, (
        "ops/backup/pg_backup.sh nema `restic forget`/`--prune`. AC2: retention je obavezan."
    )
    assert guard_idx < forget_idx, (
        f"PRUNE-GATE PAO: non-empty guard (idx {guard_idx}) NIJE pre `forget`/`--prune` "
        f"(idx {forget_idx}). AC2/SM-D7/G-17: prune mora biti POSLE uspesnog dump+push-a, "
        f"inace niz losih run-ova prune-uje poslednji DOBAR snapshot."
    )


# =============================================================================
# AC3 — media_backup.sh: restic snapshot named volume-a `:ro` kroz RESTIC_IMAGE
# =============================================================================


def test_ac3_media_backup_sh_exists():
    """# AC-3/Task 3.1: `ops/backup/media_backup.sh` MORA postojati (weekly restic snapshot)."""
    assert MEDIA_BACKUP_SH.exists(), (
        f"Missing required file: {MEDIA_BACKUP_SH}\n"
        f"AC3/SM-D3: weekly restic snapshot media named volume-a."
    )


def test_ac3_media_backup_mounts_named_volume_readonly_via_docker_run():
    """# AC-3/SM-D12/G-9: media_backup.sh koristi `docker run --rm` sa
    `coric_agrar_production_media` mount-ovan `:ro` DIREKTNO u restic kontejner (NE host bind-path)."""
    content = _strip_comments(_read_file(MEDIA_BACKUP_SH))
    assert re.search(r"docker\s+run\s+--rm", content), (
        "ops/backup/media_backup.sh ne koristi `docker run --rm` (SM-D12: restic kroz image, "
        "NE host binarka)."
    )
    assert re.search(rf"-v\s+{re.escape(MEDIA_VOLUME)}:[^\s]*:ro\b", content), (
        f"ops/backup/media_backup.sh ne mount-uje `-v {MEDIA_VOLUME}:<path>:ro`. "
        f"AC3/SM-D12/G-9: named volume se mount-uje read-only DIREKTNO u restic kontejner "
        f"(NE host bind-path — root-only na hostu; `:ro` jer backup NE pise u media)."
    )


def test_ac3_media_backup_uses_restic_image_var():
    """# AC-3/SM-D12: media_backup.sh restic invokacija kroz `${RESTIC_IMAGE}` (pinovan image)."""
    content = _read_file(MEDIA_BACKUP_SH)
    assert re.search(r"\$\{?RESTIC_IMAGE", content), (
        "ops/backup/media_backup.sh ne referencira `${RESTIC_IMAGE}`. SM-D12: restic ide kroz "
        "pinovan `restic/restic` image (`docker run --rm ... \"${RESTIC_IMAGE}\" ...`)."
    )


def test_ac3_media_backup_no_host_bind_path_for_volume():
    """# AC-3/SM-D12/G-9: media_backup.sh NE SME citati named volume preko host bind-path-a
    (`/var/lib/docker/volumes/...`) — to je root-only i lomi se."""
    content = _strip_comments(_read_file(MEDIA_BACKUP_SH))
    assert not re.search(r"/var/lib/docker/volumes/", content), (
        "ops/backup/media_backup.sh cita named volume preko host bind-path-a "
        "(`/var/lib/docker/volumes/...`). AC3/SM-D12/G-9: named volume NIJE citljiv preko "
        "host putanje bez root-a — mount-uj ga DIREKTNO u restic kontejner (`-v <vol>:/data:ro`)."
    )


# =============================================================================
# SM-D12 — RESTIC_IMAGE pin: nikad :latest
# =============================================================================


def test_smd12_restic_image_not_latest():
    """# AC-3/SM-D12/G-15: NIJEDNA backup skripta NE SME koristiti `restic/restic:latest`
    (pin-uj konkretan tag, mirror glitchtip:v6.0 disciplina)."""
    blob = "\n".join(_read_backup_sh_glob().values())
    assert not re.search(r"restic/restic:latest\b", blob), (
        "ops/backup/*.sh koristi `restic/restic:latest`. SM-D12/G-15: pin-uj na konkretan tag "
        "(`RESTIC_IMAGE=restic/restic:<verzija>`), NIKAD `:latest` (nedeterministicki)."
    )


def test_smd12_restic_invoked_via_docker_run_not_host_binary():
    """# AC-3/SM-D12/G-15: restic se poziva kroz `docker run ... restic/restic` image,
    NE kao bare host `restic` binarka (new_dependencies=0 → restic VAN hosta)."""
    # HARDENING: strip-uj komentare PRE asserta — `docker run` u komentaru/marker-tekstu
    # NE sme zadovoljiti uslov (host-restic regresija ne sme proci ostavljajuci samo komentar).
    blob = "\n".join(_strip_comments(c) for c in _read_backup_sh_glob().values())
    # Pozitivno: bar jedna IZVRSNA linija poziva restic kroz docker run + restic/restic ILI RESTIC_IMAGE.
    assert re.search(r"docker\s+run\b[\s\S]*?(restic/restic|RESTIC_IMAGE)", blob), (
        "ops/backup/*.sh ne poziva restic kroz `docker run ... restic/restic`/`${RESTIC_IMAGE}` "
        "na IZVRSNOJ liniji. SM-D12/G-15: restic NIKAD na hostu — uvek kroz pinovan "
        "`restic/restic` image (komentar-marker se NE racuna)."
    )


# =============================================================================
# AC4 — ENCRYPTION: restic password env (RESTIC_PASSWORD / RESTIC_PASSWORD_FILE)
# =============================================================================


def test_ac4_restic_password_env_present():
    """# AC-4/SM-D4: backup skripte referenciraju `RESTIC_PASSWORD` ILI `RESTIC_PASSWORD_FILE`
    (client-side encrypt; password kroz env, NIKAD inline)."""
    blob = "\n".join(_read_backup_sh_glob().values())
    assert re.search(r"RESTIC_PASSWORD(_FILE)?", blob), (
        "ops/backup/*.sh ne referencira `RESTIC_PASSWORD`/`RESTIC_PASSWORD_FILE`. "
        "AC4/SM-D4: restic encrypt password MORA biti env-driven (NE inline literal)."
    )


def test_ac4_restic_repository_env_driven():
    """# AC-4/SM-D5: `RESTIC_REPOSITORY` je env-driven (rclone/sftp backend; NE hardkodovan repo)."""
    blob = "\n".join(_read_backup_sh_glob().values())
    assert re.search(r"RESTIC_REPOSITORY", blob), (
        "ops/backup/*.sh ne referencira `RESTIC_REPOSITORY`. AC4/SM-D5: repo backend "
        "(rclone:/sftp:) env-driven, prosledjen kroz `-e RESTIC_REPOSITORY` u restic kontejner."
    )


# =============================================================================
# AC5 — CRON: TZ=UTC + daily 03:00 UTC (0 3 * * *) + weekly media; apsolutne putanje
# =============================================================================


def test_ac5_crontab_exists():
    """# AC-5/Task 5.1: `ops/backup/crontab` MORA postojati (daily DB + weekly media)."""
    assert CRONTAB.exists(), (
        f"Missing required file: {CRONTAB}\n"
        f"AC5/SM-D6: daily 03:00 UTC pg_backup + weekly media_backup; apsolutne putanje."
    )


def test_ac5_crontab_has_tz_utc():
    """# AC-5/G-8/MEDIUM-9: crontab MORA imati `TZ=UTC` (box-TZ moze biti lokalni → 03:00 lokalno)."""
    content = _read_file(CRONTAB)
    assert re.search(r"^\s*TZ\s*=\s*UTC\b", content, re.MULTILINE), (
        "ops/backup/crontab nema `TZ=UTC`. AC5/G-8: epics trazi 03:00 UTC; bez TZ=UTC "
        "`0 3 * * *` bi bio lokalnih 3 ujutru (ne UTC)."
    )


def test_ac5_crontab_daily_db_at_0300_utc():
    """# AC-5: crontab ima daily `0 3 * * *` koji pokrece pg_backup.sh (03:00 UTC DB backup)."""
    content = _strip_comments(_read_file(CRONTAB))
    # Aktivna (non-comment) cron linija `0 3 * * *` + poziv pg_backup.sh.
    daily = [
        ln for ln in content.splitlines()
        if re.search(r"^\s*0\s+3\s+\*\s+\*\s+\*", ln) and re.search(r"pg_backup\.sh", ln)
    ]
    assert daily, (
        "ops/backup/crontab nema AKTIVNU `0 3 * * * ... pg_backup.sh` liniju (daily 03:00 UTC). "
        "AC5/SM-D6."
    )


def test_ac5_crontab_weekly_media_line():
    """# AC-5/SM-D3: crontab ima weekly (npr. `0 4 * * 0`) liniju koja pokrece media_backup.sh."""
    content = _strip_comments(_read_file(CRONTAB))
    weekly = [
        ln for ln in content.splitlines()
        if re.search(r"media_backup\.sh", ln) and re.search(r"^\s*\S+\s+\S+\s+\S+\s+\S+\s+0\b", ln)
    ]
    assert weekly, (
        "ops/backup/crontab nema AKTIVNU weekly liniju za `media_backup.sh` (npr. `0 4 * * 0`). "
        "AC5/SM-D3: media restic snapshot je WEEKLY."
    )


def test_ac5_crontab_uses_absolute_paths():
    """# AC-5/G-7/SM-D6: cron linije koriste APSOLUTNE putanje do skripti (cron CWD != repo root)."""
    content = _strip_comments(_read_file(CRONTAB))
    script_lines = [
        ln for ln in content.splitlines()
        if re.search(r"(pg_backup|media_backup)\.sh", ln)
    ]
    assert script_lines, "ops/backup/crontab nema cron linije koje pozivaju backup skripte."
    for ln in script_lines:
        m = re.search(r"(/\S*(?:pg_backup|media_backup)\.sh)", ln)
        assert m is not None, (
            f"ops/backup/crontab cron linija ne koristi APSOLUTNU putanju (vodecu `/`): {ln!r}. "
            f"AC5/G-7: relativne putanje FAIL-uju iz cron CWD-a."
        )


# =============================================================================
# AC6 — restore.sh: gunzip|psql (NE pg_restore) + RESTORE_TARGET_DB != prod
# =============================================================================


def test_ac6_restore_sh_exists():
    """# AC-6/Task 4.1: `ops/backup/restore.sh` MORA postojati (restore na lokal/test)."""
    assert RESTORE_SH.exists(), (
        f"Missing required file: {RESTORE_SH}\n"
        f"AC6: restore <snapshotID> na lokal + gunzip|psql load u RESTORE_TARGET_DB."
    )


def test_ac6_restore_sh_fail_loud_on_missing_snapshot_id():
    """# AC-6/Task 4.2: restore.sh fail-loud (exit non-zero + usage) ako `<snapshotID>` nedostaje.

    Proxy: skripta referencira `$1`/Usage + `exit` non-zero (mirror deploy.sh:42-49)."""
    content = _strip_comments(_read_file(RESTORE_SH))
    has_arg = re.search(r"\$\{?1\b|SNAPSHOT_ID|snapshotID", content)
    has_usage_exit = re.search(r"Usage[\s\S]{0,200}?exit\s+[1-9]", content) or re.search(
        r"exit\s+[1-9][\s\S]{0,200}?Usage", content
    )
    assert has_arg, (
        "ops/backup/restore.sh ne cita `$1`/snapshotID argument. AC6/Task 4.2."
    )
    assert has_usage_exit, (
        "ops/backup/restore.sh nema fail-loud usage+`exit` non-zero ako snapshotID nedostaje. "
        "AC6/Task 4.2: mirror deploy.sh:42-49 (`exit 2` + Usage poruka)."
    )


def test_ac6_restore_sh_uses_gunzip_psql_not_pg_restore():
    """# AC-6/SM-D13/G-20: restore.sh load kroz `gunzip` + `psql` (NIKAD `pg_restore` — plain par)."""
    content = _strip_comments(_read_file(RESTORE_SH))
    assert re.search(r"\bgunzip\b", content), (
        "ops/backup/restore.sh ne koristi `gunzip`. SM-D13: plain `pg_dump|gzip` ⇒ "
        "restore `gunzip | psql`."
    )
    assert re.search(r"\bpsql\b", content), (
        "ops/backup/restore.sh ne koristi `psql`. SM-D13: plain dump se ucitava kroz psql, NE pg_restore."
    )
    assert not re.search(r"\bpg_restore\b", content), (
        "ops/backup/restore.sh koristi `pg_restore`. SM-D13/G-20: plain-SQL dump se restore-uje "
        "ISKLJUCIVO kroz `gunzip | psql`; pg_restore radi samo sa custom `-Fc` formatom (9.5 ga NE koristi) "
        "→ fail-uje TEK pri restore-u („input file appears to be a text format dump. Please use psql.\")."
    )


def test_ac6_restore_sh_reads_restore_target_db_env():
    """# AC-6/SM-D14: restore.sh cita EKSPLICITAN `RESTORE_TARGET_DB`/`RESTORE_DB_URL` (default TEST)."""
    content = _read_file(RESTORE_SH)
    assert re.search(r"RESTORE_TARGET_DB|RESTORE_DB_URL", content), (
        "ops/backup/restore.sh ne cita `RESTORE_TARGET_DB`/`RESTORE_DB_URL`. AC6/SM-D14: "
        "restore-cilj je eksplicitan env var (default TEST DB), NIKAD implicitan prod."
    )


def test_ac6_restore_sh_does_not_default_to_prod_database_url():
    """# AC-6/SM-D14/G-22 (DATA-LOSS GUARD): restore.sh NE SME default-ovati na prod `DATABASE_URL`.

    Negative: izvrsna linija NE sme imati `${DATABASE_URL:-...}` ili `${...:-${DATABASE_URL}}`
    fallback (restore-test ne sme tiho prepisati zivu prod bazu)."""
    content = _strip_comments(_read_file(RESTORE_SH))
    # Fallback NA prod DATABASE_URL: `RESTORE_*:-...DATABASE_URL` ILI `DATABASE_URL` kao psql cilj.
    bad_fallback = re.search(r"RESTORE_(?:TARGET_DB|DB_URL)\s*:-[^}]*DATABASE_URL", content) or \
        re.search(r":-\s*\$\{?DATABASE_URL", content)
    assert not bad_fallback, (
        "ops/backup/restore.sh default-uje restore-cilj na prod `DATABASE_URL` "
        "(`${RESTORE_TARGET_DB:-${DATABASE_URL}}` ili slicno). AC6/SM-D14/G-22: restore-test "
        "NIKAD ne sme pasti nazad na prod DB (data-loss). Fail-loud ako cilj nije bezbedno postavljen."
    )


# =============================================================================
# AC7 — RESTORE.md runbook: mesecni restore-test + unlock + check + offline pass
# =============================================================================


def test_ac7_restore_md_exists():
    """# AC-7/Task 6.1: `ops/backup/RESTORE.md` MORA postojati (restore runbook)."""
    assert RESTORE_MD.exists(), (
        f"Missing required file: {RESTORE_MD}\n"
        f"AC7: restore runbook + mesecni manual restore-test + creds reference."
    )


def test_ac7_restore_md_mentions_monthly_restore_test():
    """# AC-7/project-context:468: runbook dokumentuje MESECNI manual restore-test."""
    content = _read_file(RESTORE_MD).lower()
    assert "mesec" in content and "restore" in content, (
        "ops/backup/RESTORE.md ne pominje mesecni restore-test. AC7/project-context:468: "
        "mesecna manual procedura (verify backup nije corrupted) je obavezna."
    )


def test_ac7_restore_md_mentions_unlock_and_check():
    """# AC-7/MEDIUM-6/MEDIUM-7 (G-18/G-19): runbook pominje `restic unlock` (stale-lock) i
    `restic check` (integritet)."""
    content = _read_file(RESTORE_MD)
    assert re.search(r"restic\s+unlock", content), (
        "ops/backup/RESTORE.md ne pominje `restic unlock`. AC7/G-18: stale repo lock "
        "(kill/OOM) tiho fail-uje naredne run-ove — runbook mora dokumentovati unlock."
    )
    assert re.search(r"restic\s+check", content), (
        "ops/backup/RESTORE.md ne pominje `restic check`. AC7/G-19: repo korupcija je tiha "
        "do restore-a — periodican integritet-check je obavezan u runbook-u."
    )


def test_ac7_restore_md_password_offline_warning():
    """# AC-7/SM-D4/G-6: runbook UPOZORAVA da se restic password backup-uje ODVOJENO/offline
    (gubitak password-a = nepovratan backup)."""
    content = _read_file(RESTORE_MD).lower()
    has_password = "password" in content or "lozink" in content
    has_offline = "offline" in content or "odvojen" in content or "nepovrat" in content
    assert has_password and has_offline, (
        "ops/backup/RESTORE.md nema restic-password offline-backup upozorenje. "
        "AC7/SM-D4/G-6: gubitak password-a = kriptografski nepovratan backup → mora se "
        "cuvati ODVOJENO/offline (NE samo na istom boxu)."
    )


# =============================================================================
# AC8 — FAIL-LOUD: set -euo pipefail svuda + NEMA `|| true` + non-empty dump guard
# =============================================================================


@pytest.mark.parametrize(
    "script_path", ALL_SCRIPTS, ids=["pg_backup", "media_backup", "restore"]
)
def test_ac8_set_euo_pipefail_in_every_script(script_path):
    """# AC-8/SM-D7: svaka ops/backup/*.sh skripta MORA poceti sa `set -euo pipefail`
    (eksplicitan `pipefail`, NE samo `set -e` — G-3 maskirani pg_dump fail)."""
    content = _read_file(script_path)
    assert re.search(r"set\s+-euo\s+pipefail", content), (
        f"{script_path.name} nema `set -euo pipefail`. AC8/SM-D7/G-3: bez `pipefail` "
        f"pg_dump fail u pipe-u je TIHO maskiran (najgori ishod)."
    )


@pytest.mark.parametrize(
    "script_path", ALL_SCRIPTS, ids=["pg_backup", "media_backup", "restore"]
)
def test_ac8_no_or_true_masking_on_backup_step(script_path):
    """# AC-8/SM-D7 NEGATIVE: skripte NE SMEJU maskirati pg_dump/restic korak sa `|| true`."""
    content = _strip_comments(_read_file(script_path))
    # Scope na PRAVE backup KOMANDE (NE bare rec "backup" — to bi false-positive-ovalo
    # benignu `mkdir -p .../ops/backup/.tmp || true` temp-dir liniju). `restic backup`
    # je vec pokriven `restic`/`docker ... backup` tokenom.
    masking = [
        ln for ln in content.splitlines()
        if re.search(r"\|\|\s*true\b", ln)
        and re.search(
            r"\bpg_dump\b|\brestic\b|\bgzip\b|\bforget\b|\bprune\b"
            r"|docker\s+run[^\n]*\bbackup\b",
            ln,
        )
    ]
    assert not masking, (
        f"{script_path.name} maskira backup korak sa `|| true`: {masking}. "
        f"AC8/SM-D7: NIKAD `|| true` na pg_dump/restic koraku (tih fail = lazno 'backup uspeo')."
    )


def test_ac8_pg_backup_has_nonempty_dump_guard_before_restic_push():
    """# AC-8/SM-D7/HIGH-1 (OBAVEZNO): pg_backup.sh ima non-empty dump guard
    (`test -s`/`[ -s`/size-floor/marker grep) PRE restic push-a.

    Goli `pipefail` hvata pg_dump≠0 ali NE exit-0-prazan-dump (prazna baza, schema-only race)
    → mora postojati eksplicitan size/marker check."""
    content = _strip_comments(_read_file(PG_BACKUP_SH))
    guard = (
        re.search(r"\btest\s+-s\b", content)
        or re.search(r"\[\s+-s\s+", content)
        or re.search(re.escape(PG_DUMP_MARKER), content)
        or re.search(r"\bstat\b[^\n]*(-c\s*%s|--format=%s)", content)  # size-floor proxy
        or re.search(r"\bwc\s+-c\b", content)
    )
    assert guard, (
        "ops/backup/pg_backup.sh nema OBAVEZAN non-empty dump guard (`test -s`/`[ -s`/size-floor/"
        f"marker grep `{PG_DUMP_MARKER}`) PRE restic push-a. AC8/SM-D7/HIGH-1: goli `pipefail` NE "
        "hvata exit-0-prazan-dump → eksplicitan size/marker check je OBAVEZAN."
    )


def test_ac8_nonempty_guard_before_restic_backup_push():
    """# AC-8/SM-D7 (ORDERING): non-empty guard dolazi PRE restic `backup` push-a u pg_backup.sh.

    HARDENING: strip-uj i `echo` label-linije → meri redosled STVARNE `restic_run backup`
    komande, NE echo-label teksta (`echo "[BACKUP] restic backup ..."`).
    """
    content = _strip_comments_and_echo(_read_file(PG_BACKUP_SH))
    guard_idx = _index_of(
        rf"test\s+-s\b|\[\s+-s\b|{re.escape(PG_DUMP_MARKER)}|wc\s+-c\b", content
    )
    # Push se moze pisati inline (`docker run ... "${RESTIC_IMAGE}" backup ...`),
    # kroz literal `restic ... backup`, ILI kroz sourced helper (`restic_run backup`,
    # `_restic backup` — G-14 `_restic_common.sh` wrapper). Pokrij sve tri forme:
    #  (a) `restic`-prefiksovan token (cmd/fn) pa `backup`,
    #  (b) `RESTIC_IMAGE` pa `backup` (do 80 char),
    #  (c) `docker run ... backup` (do 200 char).
    push_idx = _index_of(
        r"\brestic\w*\b[^\n]*\bbackup\b"
        r"|RESTIC_IMAGE[\s\S]{0,80}?\bbackup\b"
        r"|docker\s+run\b[\s\S]{0,200}?\bbackup\b",
        content,
    )
    assert guard_idx != -1, "pg_backup.sh nema non-empty dump guard (AC8 RED)."
    # push_idx moze biti -1 ako restic push nije naden — i to je RED (skripta nepotpuna).
    assert push_idx != -1, (
        "pg_backup.sh nema restic `backup` push korak. AC1/AC8."
    )
    assert guard_idx < push_idx, (
        f"ORDERING PAO: non-empty guard (idx {guard_idx}) NIJE pre restic `backup` push-a "
        f"(idx {push_idx}). AC8/SM-D7: assert MORA proci PRE bilo kakvog restic push-a."
    )


# =============================================================================
# AC9 — restic init IDEMPOTENT guard + SM-D15 env pre-flight guard
# =============================================================================


def test_ac9_restic_init_idempotency_guard_present():
    """# AC-9/SM-D9/G-4: backup skripte imaju restic-init idempotency guard
    (`restic snapshots ... || ... restic init`) — re-run kad repo postoji NE pada."""
    blob = "\n".join(_read_backup_sh_glob().values())
    # init-only-if-missing: `snapshots` ... `||` ... `init` (kroz restic image).
    assert re.search(r"\bsnapshots\b[\s\S]{0,200}?\|\|[\s\S]{0,200}?\binit\b", blob), (
        "ops/backup/*.sh nema restic-init idempotency guard (`snapshots ... || ... init`). "
        "AC9/SM-D9/G-4: restic init NIJE idempotentan po defaultu — guard init SAMO ako repo "
        "nedostaje (re-run NE sme fail-ovati „repository master key already exists\")."
    )


def test_smd15_restic_env_preflight_guard_present():
    """# SM-D15/G-21 (ORPHANED-REPO ZAMKA): skripte fail-loud ako su `RESTIC_REPOSITORY`/
    `RESTIC_PASSWORD(_FILE)` PRAZNI — PRE snapshots-or-init guard-a.

    `set -u` hvata UNSET ali NE postavljen-ali-prazan → eksplicitan `[ -n "${VAR:-}" ]` ili
    `${VAR:?...}` check je obavezan."""
    blob = "\n".join(_read_backup_sh_glob().values())
    repo_guard = re.search(r"\[\s+-n\s+\"?\$\{?RESTIC_REPOSITORY", blob) or re.search(
        r"\$\{RESTIC_REPOSITORY:\?", blob
    )
    pass_guard = re.search(r"\[\s+-n\s+\"?\$\{?RESTIC_PASSWORD", blob) or re.search(
        r"\$\{RESTIC_PASSWORD(?:_FILE)?:\?", blob
    )
    assert repo_guard, (
        "ops/backup/*.sh nema RESTIC_REPOSITORY pre-flight guard (`[ -n \"${RESTIC_REPOSITORY:-}\" ]` "
        "ili `${RESTIC_REPOSITORY:?...}`). SM-D15/G-21: prazan repo → `snapshots` padne iz "
        "credential razloga → guard pogresno `init` ORPHANED repo. Fail-loud PRE init-guard-a."
    )
    assert pass_guard, (
        "ops/backup/*.sh nema RESTIC_PASSWORD(_FILE) pre-flight guard. SM-D15/G-21: prazan "
        "password → orphaned-repo zamka. Fail-loud ako su i RESTIC_PASSWORD i RESTIC_PASSWORD_FILE prazni."
    )


# =============================================================================
# AC10 — GlitchTip thin fail-notify (trap ERR + env DSN); NE 9.6 LOGGING dict
# =============================================================================


def test_ac10_pg_backup_has_trap_err_and_notify():
    """# AC-10/SM-D8: pg_backup.sh wire-uje `trap ... ERR` + `notify_failure`; kanonski
    `notify_failure` zivi u deljenom `_restic_common.sh` (REFACTOR de-dup — DRY)."""
    content = _read_file(PG_BACKUP_SH)
    assert re.search(r"trap\s+[^\n]*\bERR\b", content), (
        "ops/backup/pg_backup.sh nema `trap ... ERR`. AC10/SM-D8: fail-notify se okida na "
        "non-zero exit (trap ERR → notify_failure)."
    )
    assert re.search(r"notify_failure", content), (
        "ops/backup/pg_backup.sh ne wire-uje `notify_failure` (`trap 'notify_failure' ERR`). "
        "AC10/SM-D8: thin fail-notify hook (kanonska funkcija u _restic_common.sh)."
    )
    assert re.search(r"BACKUP_SCRIPT_NAME", content), (
        "ops/backup/pg_backup.sh ne postavlja `BACKUP_SCRIPT_NAME` (cita ga deljeni "
        "notify_failure za poruku). AC10/SM-D8 — mora biti set PRE source-a helper-a."
    )


def test_ac10_notify_curls_env_driven_glitchtip_not_literal():
    """# AC-10/SM-D8/G-11: kanonski notify hook (u deljenom `_restic_common.sh`, REFACTOR
    de-dup) curl-uje GlitchTip endpoint iz ENV var-a (NE literal DSN)."""
    helper = REPO_ROOT / "ops" / "backup" / "_restic_common.sh"
    content = _read_file(helper)
    assert re.search(r"notify_failure", content), (
        "ops/backup/_restic_common.sh ne definise kanonski `notify_failure`. AC10/SM-D8: "
        "deljeni thin fail-notify hook (DRY — pg_backup/media_backup samo wire-uju trap)."
    )
    assert re.search(r"\bcurl\b", content), (
        "ops/backup/_restic_common.sh notify hook ne koristi `curl`. AC10/SM-D8: thin curl na "
        "GlitchTip ingest endpoint."
    )
    # GlitchTip URL/DSN MORA biti env-driven (npr. ${GLITCHTIP_BACKUP_NOTIFY_DSN}).
    assert re.search(r"\$\{?GLITCHTIP[A-Z_]*", content), (
        "ops/backup/_restic_common.sh notify ne koristi env-driven GlitchTip DSN/URL "
        "(`${GLITCHTIP_BACKUP_NOTIFY_DSN}`/slicno). AC10/SM-D8/G-11/G-12: DSN kroz env, NIKAD literal."
    )


def test_ac10_media_backup_wires_notify_trap_err():
    """# AC-10/SM-D8 (REFACTOR de-dup LOCK): media_backup.sh nezavisno wire-uje
    `trap 'notify_failure' ERR` — uklanjanje notify hook-a iz media_backup.sh bi bilo uhvaceno."""
    content = _read_file(MEDIA_BACKUP_SH)
    assert re.search(r"trap\s+'?notify_failure'?\s+[^\n]*\bERR\b", content), (
        "ops/backup/media_backup.sh ne wire-uje `trap 'notify_failure' ERR`. AC10/SM-D8: "
        "weekly media backup MORA imati fail-notify hook (isto kao daily DB)."
    )
    assert re.search(r"BACKUP_SCRIPT_NAME", content), (
        "ops/backup/media_backup.sh ne postavlja `BACKUP_SCRIPT_NAME` (cita ga deljeni "
        "notify_failure). AC10/SM-D8 — mora biti set PRE source-a helper-a."
    )


def test_ac10_no_django_logging_dict_in_backup_scope():
    """# AC-10/SM-D8/SM-D11/G-11 (SCOPE GUARD): ops/backup/ NE SME uvoditi Django `LOGGING = {`
    dict — 9.6 logging stack ostaje deferred (fail-notify je THIN curl, NE 9.6)."""
    if not BACKUP_DIR.exists():
        pytest.fail(
            f"Missing required dir: {BACKUP_DIR}\nStory 9.5 Dev mora kreirati ops/backup/."
        )
    offenders = []
    for p in BACKUP_DIR.rglob("*"):
        if p.is_file() and p.suffix in (".sh", ".py"):
            text = p.read_text(encoding="utf-8", errors="ignore")
            if re.search(r"\bLOGGING\s*=\s*\{", text):
                offenders.append(p.name)
    assert not offenders, (
        f"ops/backup/ uvodi Django `LOGGING = {{` dict: {offenders}. AC10/SM-D8/SM-D11/G-11: "
        f"9.6 logging stack je DEFERRED — fail-notify je THIN curl hook, NE Django LOGGING dict."
    )


# =============================================================================
# AC11 — SECRETS: 0 literala u ops/backup; ops/secrets/README.md azuriran
# =============================================================================


def test_ac11_no_literal_secrets_in_backup_files():
    """# AC-11/SM-D10/G-12 NEGATIVE: nijedan ops/backup fajl NE SME sadrzati plaintext secret
    (PEM private key, hardkodovan ne-prazan password literal, GitHub PAT)."""
    if not BACKUP_DIR.exists():
        pytest.fail(
            f"Missing required dir: {BACKUP_DIR}\nStory 9.5 Dev mora kreirati ops/backup/."
        )
    found = []
    for p in BACKUP_DIR.rglob("*"):
        if not p.is_file():
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        for pat, desc in _SECRET_LEAK_PATTERNS:
            if re.search(pat, text, re.MULTILINE):
                found.append((p.name, desc))
    assert not found, (
        f"ops/backup/ sadrzi sumnjiv plaintext secret pattern: {found}. AC11/SM-D10/G-12: "
        f"secrets idu kroz box .env / `${{...}}` (van repo-a), NIKAD u repo fajl."
    )


def test_ac11_secrets_readme_has_backup_vars():
    """# AC-11/SM-D10/Task 7.1: `ops/secrets/README.md` azuriran sa backup var-ovima
    (RESTIC_PASSWORD/RESTIC_REPOSITORY/RESTIC_IMAGE/RESTORE_TARGET_DB/Storage Box/GlitchTip notify)."""
    content = _read_file(SECRETS_README, owner="Story 9.5 (UPDATE)")
    required = [
        "RESTIC_PASSWORD",
        "RESTIC_REPOSITORY",
        "RESTIC_IMAGE",
        "RESTORE_TARGET_DB",
        "STORAGE_BOX",  # STORAGE_BOX_HOST / STORAGE_BOX_USER
        "GLITCHTIP",    # GLITCHTIP_BACKUP_NOTIFY_DSN / URL
    ]
    missing = [k for k in required if k not in content]
    assert not missing, (
        f"ops/secrets/README.md nedostaju backup secret var-ovi: {missing}. "
        f"AC11/SM-D10/Task 7.1: dodaj backup redove u box `.env` tabelu (RESTIC_*, Storage Box "
        f"host/user, GlitchTip notify DSN, RESTORE_TARGET_DB)."
    )


# =============================================================================
# bash -n syntax-parse (OPCIONO — skip-guarded ako bash nije na hostu)
# =============================================================================


@pytest.mark.parametrize(
    "script_path", ALL_SCRIPTS, ids=["pg_backup", "media_backup", "restore"]
)
def test_bash_n_syntax_parse(script_path):
    """# AC-1/AC8/Task 9.1a: `bash -n <script>` exit 0 (sintaksa cista) AKO je bash na hostu;
    inace pytest.skip (host-portable — shellcheck/bats NISU instalirani; real run = Docker/CI)."""
    bash = _bash_bin()
    if bash is None:
        pytest.skip("bash nije na PATH-u (Windows bez Git-bash) — preskacem `bash -n` parse.")
    if not script_path.exists():
        pytest.fail(
            f"Missing required file: {script_path}\nStory 9.5 Dev ga mora kreirati (bash -n RED)."
        )
    result = subprocess.run(
        [bash, "-n", str(script_path)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        shell=False,
        timeout=60,
    )
    assert result.returncode == 0, (
        f"`bash -n {script_path.name}` exit {result.returncode} (sintaksna greska).\n"
        f"stderr: {result.stderr}\nTask 9.1a: skripta mora biti sintaksno validna."
    )
