#!/usr/bin/env bash
# CORIC_AGRAR — Let's Encrypt cert provisioning + first-deploy bootstrap + auto-renewal.
# Story 9.2 (AC6/AC13/AC15).
#
# Certbot trci na HOST-u (system paket + cron — AR-13 `certbot + Nginx auto-renewal cron`),
# NE kao certbot kontejner. Webroot je deljen sa nginx kontejnerom kroz host bind-mount.
#
# PATH-CONTRACT (AC13/SM-D4 — KONKRETAN, LOCKED na 3 mesta):
#   webroot /var/www/certbot identican na 3 mesta: certbot webroot flag, nginx.conf
#   ACME root, production.yml bind-mount.
#
# FIRST-DEPLOY BOOTSTRAP (AC15/SM-D10 — chicken-and-egg):
#   nginx sa aktivnim 443 + nepostojeci cert = nginx ne starta; certbot --webroot trazi
#   nginx koji vec slusa :80. Resenje: HTTP-only bootstrap conf -> certbot izda cert ->
#   swap na pun nginx.conf (443) -> reload.
#
# Naming convention: srpska latinica + engleski identifikatori; bez cirilice.

set -euo pipefail

# ── CWD guard (M6) ─────────────────────────────────────────────────────────────
# Resolvuj repo root iz lokacije skripte (ops/nginx/nginx-init.sh -> ../.. = repo root)
# i cd-uj tamo da relativne compose/ putanje (production.yml, .active-default.conf,
# bootstrap conf) resolve-uju bez obzira odakle se skripta poziva (SSH/manual).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${REPO_ROOT}"

COMPOSE_FILE="compose/production.yml"
DC="docker compose -f ${COMPOSE_FILE}"

# Swappable conf koji production.yml nginx servis bind-mount-uje na default.conf (M1).
# nginx-init.sh popunjava ovaj fajl: bootstrap conf PRE certbot-a, pun nginx.conf POSLE.
ACTIVE_CONF="compose/nginx/.active-default.conf"

# ── Parametrizacija (AC6/SM-D2/Task 4.2) ───────────────────────────────────────
DOMAIN="${DOMAIN:-${DEPLOY_DOMAIN:-coricagrar.rs}}"
ACME_EMAIL="${ACME_EMAIL:-}"
if [[ -z "${ACME_EMAIL}" ]]; then
    echo "[CERT ERROR] ACME_EMAIL nije postavljen (env var). Potreban za Let's Encrypt registraciju." >&2
    exit 2
fi

# Webroot path je KONKRETNO /var/www/certbot (path-contract marker — AC13/SM-D4):
# identican certbot -w, nginx.conf ACME `root`, production.yml bind-mount.
ACME_WEBROOT="/var/www/certbot"

# ── Idempotency guard (AC6/AC15) ───────────────────────────────────────────────
# Ako cert vec postoji, preskoci bootstrap+izdavanje i idi direktno na pun conf.
CERT_LIVE_PATH="/etc/letsencrypt/live/${DOMAIN}/fullchain.pem"
if [[ -f "${CERT_LIVE_PATH}" ]]; then
    echo "[CERT] Cert vec postoji (${CERT_LIVE_PATH}) — preskacem izdavanje (idempotentno)."
    echo "[CERT] Aktiviram pun nginx.conf (443) u .active-default.conf i reload-ujem."
    # M1: production.yml bind-mount-uje .active-default.conf -> default.conf; populiraj ga
    # punim 443 conf-om pre re-create-a (steady-state put kad cert vec postoji).
    cp compose/nginx/nginx.conf "${ACTIVE_CONF}"
    ${DC} up -d nginx
    ${DC} exec nginx nginx -s reload || true
else
    # ── BOOTSTRAP faza (AC15) ───────────────────────────────────────────────────
    # (1) Digni nginx sa HTTP-only bootstrap conf-om (BEZ 443) da :80 servira ACME.
    #     Bootstrap conf reference je PRE certbot poziva (positional ordering — AC15).
    #     M1: .active-default.conf je TARGET koji production.yml mount-uje na default.conf,
    #     pa kopiranje bootstrap conf-a u njega ZAISTA menja sta nginx servira (NE inertno).
    echo "[CERT] Bootstrap: dizem nginx sa compose/nginx/nginx.bootstrap.conf (HTTP-only)."
    BOOTSTRAP_CONF="compose/nginx/nginx.bootstrap.conf"
    cp "${BOOTSTRAP_CONF}" "${ACTIVE_CONF}"
    ${DC} up -d nginx
    mkdir -p "${ACME_WEBROOT}"

    # (2) certbot izda inicijalni cert kroz webroot challenge na :80.
    echo "[CERT] certbot certonly --webroot -w /var/www/certbot za ${DOMAIN}."
    # KONKRETAN webroot path /var/www/certbot (path-contract — AC13/SM-D4): identican
    # nginx.conf ACME `root` i production.yml bind-mount-u (test-locked literal).
    certbot certonly --webroot -w /var/www/certbot \
        -d "${DOMAIN}" -d "www.${DOMAIN}" \
        --email "${ACME_EMAIL}" --agree-tos --non-interactive

    # (3) Swap na pun nginx.conf (443 aktivan) POSLE certbot poziva (positional — AC15).
    #     M1: kopiraj PUN conf u .active-default.conf (NE samo rm) — to je fajl koji se
    #     mount-uje, pa nginx sada vidi 443 blok i startuje ssl listener.
    echo "[CERT] Swap na pun compose/nginx/nginx.conf (443 aktivan) u .active-default.conf."
    cp compose/nginx/nginx.conf "${ACTIVE_CONF}"

    # (4) Re-create / reload nginx da 443 starta (cert sada postoji).
    ${DC} up -d nginx
    ${DC} exec nginx nginx -s reload || true
fi

# ── Auto-renewal (AC6/Task 4.5 + 4.5a) ─────────────────────────────────────────
# Registruj cron entry: certbot renew (LE preporuka 2x dnevno) sa --deploy-hook koji
# reload-uje nginx POSLE uspesne obnove. Renewal-failure VIDLJIVOST: `|| echo ... >&2`
# surface-uje neuspeh u cron/journal (tih neuspeh = istekao cert = sajt down 60-90 dana).
# BASELINE vidljivost; richer alerting (UptimeRobot/GlitchTip) defer-ovan (OQ-6, 9.3/9.4).
# M6: cron CWD NIJE repo root → deploy-hook MORA koristiti APSOLUTNU compose putanju
# (${REPO_ROOT}/compose/production.yml), inace `docker compose -f compose/...` fail-uje
# u cron kontekstu i nginx se nikad ne reload-uje posle obnove.
ABS_COMPOSE_FILE="${REPO_ROOT}/compose/production.yml"
RENEW_HOOK="docker compose -f ${ABS_COMPOSE_FILE} exec nginx nginx -s reload"
CRON_LINE="0 3,15 * * * certbot renew --deploy-hook \"${RENEW_HOOK}\" || echo \"CERT RENEWAL FAILED \$(date)\" >&2"

# Idempotentno dodaj cron liniju (ne dupliraj ako vec postoji).
if ! crontab -l 2>/dev/null | grep -qF "certbot renew"; then
    echo "[CERT] Registrujem auto-renewal cron (certbot renew + --deploy-hook reload)."
    ( crontab -l 2>/dev/null || true; echo "${CRON_LINE}" ) | crontab -
else
    echo "[CERT] Auto-renewal cron vec registrovan — preskacem (idempotentno)."
fi

echo "[CERT] nginx-init zavrsen za domen ${DOMAIN}."
