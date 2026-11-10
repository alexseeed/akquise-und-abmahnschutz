#!/usr/bin/env bash
# Set up the landing-page server on a fresh Ubuntu 24.04 VPS. Run as root; safe to run again.
#
#   bash einrichten.sh --domain angebot.kunde.de
#
# Expects next to it: server.py, generator.py, Caddyfile, seiten-server.service, and ../vorlage/.
# Installs: Caddy (official repo), python3, ufw (22, 80, 443), unattended-upgrades, rsync.
# Creates: user "seiten", /opt/seiten, /srv/seiten, /srv/daten, /etc/seiten.env (600, no secrets),
# systemd service seiten-server, daily cron for generator.py --aufraeumen.
# Secrets (SKAEL_WEBHOOK_SECRET, MELDUNG_URL) are written later by `hostinger.py geheimnis`.
set -euo pipefail

DOMAIN=""
while [ $# -gt 0 ]; do
  case "$1" in
    --domain) DOMAIN="${2:-}"; shift 2 ;;
    *) echo "FEHLER: unbekannte Option $1. Aufruf: bash einrichten.sh --domain angebot.kunde.de" >&2; exit 1 ;;
  esac
done

if [ "$(id -u)" -ne 0 ]; then
  echo "FEHLER: Skript muss als root laufen." >&2; exit 1
fi
if ! printf '%s' "$DOMAIN" | grep -Eq '^([a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$'; then
  echo "FEHLER: --domain fehlt oder ist ungültig (Beispiel: angebot.kunde.de, klein geschrieben, ohne https://)." >&2; exit 1
fi
. /etc/os-release
if [ "${ID:-}" != "ubuntu" ] || [ "${VERSION_ID:-}" != "24.04" ]; then
  echo "WARNUNG: erwartet Ubuntu 24.04, gefunden ${PRETTY_NAME:-unbekannt}. Fahre trotzdem fort." >&2
fi

QUELLE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
for f in server.py generator.py Caddyfile seiten-server.service; do
  [ -f "$QUELLE/$f" ] || { echo "FEHLER: $QUELLE/$f fehlt. server/ vollständig hochladen." >&2; exit 1; }
done

export DEBIAN_FRONTEND=noninteractive NEEDRESTART_MODE=a
APT=(apt-get -y -q -o DPkg::Lock::Timeout=600 -o Dpkg::Options::=--force-confdef -o Dpkg::Options::=--force-confold)

echo "== 1/8 Pakete aktualisieren"
"${APT[@]}" update
"${APT[@]}" upgrade
"${APT[@]}" install python3 ufw unattended-upgrades rsync curl gpg ca-certificates cron \
  debian-keyring debian-archive-keyring apt-transport-https

echo "== 2/8 Caddy (offizielles Repository, https://caddyserver.com/docs/install)"
if [ ! -f /usr/share/keyrings/caddy-stable-archive-keyring.gpg ]; then
  curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
fi
if [ ! -f /etc/apt/sources.list.d/caddy-stable.list ]; then
  curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' > /etc/apt/sources.list.d/caddy-stable.list
fi
chmod o+r /usr/share/keyrings/caddy-stable-archive-keyring.gpg /etc/apt/sources.list.d/caddy-stable.list
"${APT[@]}" update
"${APT[@]}" install caddy

echo "== 3/8 Automatische Sicherheitsupdates"
cat > /etc/apt/apt.conf.d/20auto-upgrades <<'EOF'
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
EOF
systemctl enable --now unattended-upgrades >/dev/null 2>&1 || true

echo "== 4/8 Firewall (ufw: 22, 80, 443)"
ufw allow 22/tcp >/dev/null
ufw allow 80/tcp >/dev/null
ufw allow 443/tcp >/dev/null
ufw allow 443/udp >/dev/null   # HTTP/3, used by Caddy
ufw --force enable >/dev/null

echo "== 5/8 Benutzer und Ordner"
id -u seiten >/dev/null 2>&1 || useradd --system --user-group --no-create-home --home-dir /nonexistent --shell /usr/sbin/nologin seiten
install -d -o root -g root -m 755 /opt/seiten
install -d -o seiten -g seiten -m 755 /srv/seiten /srv/seiten/v
install -d -o seiten -g seiten -m 700 /srv/daten
install -o root -g root -m 644 "$QUELLE/server.py" "$QUELLE/generator.py" /opt/seiten/
if [ -d "$QUELLE/../vorlage" ]; then
  rm -rf /opt/seiten/vorlage
  cp -r "$QUELLE/../vorlage" /opt/seiten/vorlage
  chown -R root:root /opt/seiten/vorlage
  chmod -R u=rwX,go=rX /opt/seiten/vorlage
fi

echo "== 6/8 Einstellungen /etc/seiten.env"
if [ ! -f /etc/seiten.env ]; then
  cat > /etc/seiten.env <<'EOF'
# Settings for seiten-server (read by systemd). Secrets are set with: hostinger.py geheimnis
SEITEN_DIR=/srv/seiten
DATEN_DIR=/srv/daten
PORT=8080
SKAEL_WEBHOOK_SECRET=
MELDUNG_URL=
EOF
fi
chown root:root /etc/seiten.env
chmod 600 /etc/seiten.env

echo "== 7/8 Dienste (seiten-server, Caddy, Aufräumen)"
install -o root -g root -m 644 "$QUELLE/seiten-server.service" /etc/systemd/system/seiten-server.service
systemctl daemon-reload
systemctl enable seiten-server >/dev/null 2>&1
systemctl restart seiten-server

sed "s/^angebot\.example\.de {/${DOMAIN} {/" "$QUELLE/Caddyfile" > /etc/caddy/Caddyfile.neu
if ! grep -q "^${DOMAIN} {" /etc/caddy/Caddyfile.neu; then
  echo "FEHLER: Domain konnte nicht ins Caddyfile eingesetzt werden (Zeile 'angebot.example.de {' fehlt)." >&2; exit 1
fi
caddy validate --config /etc/caddy/Caddyfile.neu --adapter caddyfile >/dev/null 2>&1 || {
  echo "FEHLER: Caddyfile ist ungültig:" >&2
  caddy validate --config /etc/caddy/Caddyfile.neu --adapter caddyfile >&2 || true
  exit 1
}
mv /etc/caddy/Caddyfile.neu /etc/caddy/Caddyfile
chmod 644 /etc/caddy/Caddyfile
systemctl enable caddy >/dev/null 2>&1
systemctl reload caddy 2>/dev/null || systemctl restart caddy

cat > /etc/cron.d/seiten-aufraeumen <<'EOF'
# Delete expired landing pages daily at 03:30 (server time).
30 3 * * * seiten /usr/bin/python3 /opt/seiten/generator.py --ziel /srv/seiten --aufraeumen >> /srv/daten/aufraeumen.log 2>&1
EOF
chmod 644 /etc/cron.d/seiten-aufraeumen

echo "== 8/8 Kontrolle"
sleep 2
IP="$(ip -4 -o route get 1.1.1.1 2>/dev/null | awk '{for(i=1;i<=NF;i++) if($i=="src") print $(i+1)}' || true)"
DNS="$(getent ahostsv4 "$DOMAIN" | awk 'NR==1{print $1}' || true)"
if [ -n "$IP" ] && [ "$DNS" != "$IP" ]; then
  echo "HINWEIS: $DOMAIN zeigt auf '${DNS:-nichts}', dieser Server hat $IP. Caddy holt das Zertifikat, sobald der A-Record stimmt."
fi
if [ -f /var/run/reboot-required ]; then echo "HINWEIS: Ein Neustart wird empfohlen (Kernel-Update). Befehl: reboot"; fi
echo "STATUS: domain=$DOMAIN seiten-server=$(systemctl is-active seiten-server) caddy=$(systemctl is-active caddy) ufw=$(ufw status | awk 'NR==1{print $2}') cron=$([ -f /etc/cron.d/seiten-aufraeumen ] && echo ja || echo nein)"
