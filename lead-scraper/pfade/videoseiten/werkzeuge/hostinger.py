#!/usr/bin/env python3
"""Hostinger VPS for the landing pages: check, SSH key, DNS, setup, upload, status.

    python3 werkzeuge/hostinger.py pruefen
    python3 werkzeuge/hostinger.py schluessel --vm 123456
    python3 werkzeuge/hostinger.py dns        --domain kunde.de --name angebot --ip 1.2.3.4
    python3 werkzeuge/hostinger.py einrichten --vm 123456 --domain angebot.kunde.de
    python3 werkzeuge/hostinger.py geheimnis  --vm 123456
    python3 werkzeuge/hostinger.py hochladen  --vm 123456 --seiten arbeit/seiten
    python3 werkzeuge/hostinger.py status     --vm 123456 --domain angebot.kunde.de

Reads HOSTINGER_API_TOKEN (and for `einrichten`/`geheimnis` SKAEL_WEBHOOK_SECRET,
MELDUNG_URL) from pfade/videoseiten/.env. Secret values are never printed.
SSH key and known_hosts live in pfade/videoseiten/arbeit/ssh/ (git-ignored).

Official Hostinger API, base https://developers.hostinger.com, header
"Authorization: Bearer <token>". Spec: https://developers.hostinger.com/openapi/openapi.json
(v2.2.0, fetched 2026-10-25); overview: https://docs.hostinger.com/api-reference/overview.md
Standard library only. Exit codes: 0 ok, 1 error, 2 user action needed.
"""
from __future__ import annotations

import argparse
import base64
import ipaddress
import json
import os
import re
import shutil
import socket
import ssl
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
import wiederholen  # noqa: E402  (shared retry rule, werkzeuge/wiederholen.py)

HIER = Path(__file__).resolve().parents[1]          # pfade/videoseiten
ENV_DATEI = HIER / ".env"
SSH_DIR = HIER / "arbeit" / "ssh"
SCHLUESSEL = SSH_DIR / "id_ed25519"
KNOWN_HOSTS = SSH_DIR / "known_hosts"
API = "https://developers.hostinger.com"
USER_AGENT = "videoseiten-werkzeug/1.0"
REMOTE_STAGING = "/root/seiten-einrichtung"
SEITEN_ZIEL = "/srv/seiten"
GEHEIME_SCHLUESSEL = ("SKAEL_WEBHOOK_SECRET", "MELDUNG_URL")

DOMAIN_RE = re.compile(r"^(?=.{4,253}$)([a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$")
LABEL_RE = re.compile(r"^(@|[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?(\.[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?)*)$")
SEITEN_ID_RE = re.compile(r"^[A-Za-z0-9]{22}$")

STATUS_DE = {
    "running": "läuft", "stopped": "gestoppt", "starting": "startet", "stopping": "stoppt",
    "creating": "wird erstellt", "initial": "noch nicht eingerichtet", "error": "Fehler",
    "suspended": "gesperrt", "recreating": "wird neu installiert", "recovery": "Rettungsmodus",
}


class Abbruch(Exception):
    """Understandable error: what happened, what to do. Never contains secret values."""

    def __init__(self, was: str, tun: str, code: int = 1):
        super().__init__(was)
        self.was, self.tun, self.code = was, tun, code


# ---------------------------------------------------------------- config

def lade_env(pfad: Path | None = None) -> dict[str, str]:
    """Minimal .env parser: KEY=VALUE, optional quotes, '#' comments, optional 'export '."""
    pfad = pfad or ENV_DATEI
    werte: dict[str, str] = {}
    if not pfad.is_file():
        return werte
    for zeile in pfad.read_text(encoding="utf-8-sig").splitlines():
        zeile = zeile.strip()
        if not zeile or zeile.startswith("#") or "=" not in zeile:
            continue
        if zeile.startswith("export "):
            zeile = zeile[7:].lstrip()
        name, wert = zeile.split("=", 1)
        wert = wert.strip()
        if len(wert) >= 2 and wert[0] == wert[-1] and wert[0] in "\"'":
            wert = wert[1:-1]
        werte[name.strip()] = wert
    return werte


def token_holen(pfad: Path | None = None) -> str:
    """HOSTINGER_API_TOKEN from .env (fallback: environment). The value is never printed."""
    pfad = pfad or ENV_DATEI
    token = lade_env(pfad).get("HOSTINGER_API_TOKEN") or os.environ.get("HOSTINGER_API_TOKEN", "")
    token = token.strip()
    if not token or "<" in token or "dein" in token.lower():
        raise Abbruch(
            f"In {pfad} steht noch kein Hostinger-API-Schlüssel (HOSTINGER_API_TOKEN).",
            "Nutzer nach anleitungen/02_hostinger-vps.md, Schritt 4 und 5 einen API-Schlüssel erzeugen lassen; "
            "die Datei .env öffnen, er fügt ihn hinter HOSTINGER_API_TOKEN= ein und speichert.")
    if any(c.isspace() for c in token):
        raise Abbruch("Der Hostinger-API-Schlüssel in .env enthält Leerzeichen oder Zeilenumbrüche.",
                      "Nutzer bitten, den Schlüssel in .env noch einmal sauber in eine Zeile einzufügen.")
    return token


def geheimnisse_holen(pfad: Path | None = None) -> dict[str, str]:
    """SKAEL_WEBHOOK_SECRET / MELDUNG_URL if set in .env. Values are never printed."""
    env = lade_env(pfad)
    werte = {k: env[k].strip() for k in GEHEIME_SCHLUESSEL if env.get(k, "").strip()}
    for k, v in werte.items():
        if "\n" in v or "\r" in v or "<" in v:
            raise Abbruch(f"Der Wert {k} in .env ist ungültig (Zeilenumbruch oder Platzhalter).",
                          f"Nutzer bitten, {k} in .env neu einzufügen (eine Zeile, ohne < >).")
    if "MELDUNG_URL" in werte and not werte["MELDUNG_URL"].startswith("https://"):
        raise Abbruch("MELDUNG_URL in .env beginnt nicht mit https://.",
                      "Die vollständige https-Adresse des Webhooks (z. B. n8n) in .env eintragen.")
    return werte


# ---------------------------------------------------------------- http

def anfrage(methode: str, pfad: str, token: str, daten: dict | None = None, versuche: int | None = None):
    """Call the Hostinger API (docs.hostinger.com/api-reference/errors.md).

    Temporary errors (network, timeout, invalid JSON, 408/425/429/5xx) are retried with backoff and
    Retry-After (werkzeuge/wiederholen.py, MAX_RETRIES attempts); 401/404/409/422 … fail at once."""
    kopf = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT,
    }
    erg = wiederholen.wiederholen(lambda: wiederholen.http_json(API + pfad, methode, kopf, daten, timeout=30),
                                  was=f"Hostinger {methode} {pfad}", versuche=versuche)
    if 200 <= erg.status < 300:
        return erg.daten if erg.daten is not None else {}
    if erg.status == 0:
        if "CERTIFICATE_VERIFY_FAILED" in erg.meldung or "certificate verify failed" in erg.meldung:
            raise Abbruch("Python kann das HTTPS-Zertifikat von Hostinger nicht prüfen (Zertifikatsspeicher fehlt).",
                          "Auf dem Mac einmal 'Install Certificates.command' im Python-Ordner unter Programme ausführen.")
        raise Abbruch(f"Keine Verbindung zu developers.hostinger.com ({erg.meldung[:120]}; {erg.versuche} Versuche).",
                      "Internetverbindung prüfen und den Befehl in ein paar Minuten wiederholen.")
    inhalt = erg.daten if isinstance(erg.daten, dict) else {"message": erg.meldung}
    raise api_fehler(erg.status, inhalt, pfad)


def api_fehler(status: int, inhalt: dict, pfad: str) -> Abbruch:
    meldung = str(inhalt.get("message") or "")[:200]
    kennung = inhalt.get("correlation_id")
    extra = f" (Hostinger: {meldung})" if meldung else ""
    if status == 401:
        a = Abbruch("Hostinger lehnt den API-Schlüssel ab (abgelaufen, gelöscht oder unvollständig kopiert).",
                    "Nutzer im hPanel unter API einen neuen Schlüssel erzeugen lassen und in .env bei "
                    "HOSTINGER_API_TOKEN ersetzen (anleitungen/02_hostinger-vps.md, Schritt 4 und 5).")
    elif status == 404:
        a = Abbruch(f"Hostinger findet {pfad} in diesem Konto nicht{extra}.",
                    "VM-ID bzw. Domain mit 'pruefen' kontrollieren. Gehört der VPS zu einem anderen Hostinger-Konto, "
                    "braucht es den API-Schlüssel aus genau diesem Konto.")
    elif status == 422:
        fehler = "; ".join(f"{k}: {' '.join(map(str, v))}" for k, v in (inhalt.get("errors") or {}).items())[:300]
        a = Abbruch(f"Hostinger lehnt die Angaben ab{extra}{' – ' + fehler if fehler else ''}.",
                    "Werte (Domain, IP, VM-ID) prüfen und den Befehl korrigiert wiederholen.")
    elif status == 409:
        a = Abbruch(f"Der VPS ist gerade beschäftigt oder der Eintrag existiert schon{extra}.",
                    "Ein bis zwei Minuten warten, dann erneut versuchen.")
    elif status == 429:
        a = Abbruch("Zu viele Anfragen an Hostinger (Grenze 90 pro Minute).", "Eine Minute warten, dann wiederholen.")
    else:
        a = Abbruch(f"Störung bei Hostinger (HTTP {status}){extra}.",
                    "In ein paar Minuten erneut versuchen" + (f"; bei Support-Anfrage diese Kennung nennen: {kennung}." if kennung else "."))
    a.status = status  # type: ignore[attr-defined]
    return a


# ---------------------------------------------------------------- VPS helpers

def vm_holen(token: str, vm_id: int) -> dict:
    # GET /api/vps/v1/virtual-machines/{virtualMachineId}
    return anfrage("GET", f"/api/vps/v1/virtual-machines/{vm_id}", token)


def ipv4(vm: dict) -> str:
    for eintrag in vm.get("ipv4") or []:
        if eintrag.get("address"):
            return eintrag["address"]
    return ""


def os_name(vm: dict) -> str:
    return ((vm.get("template") or {}).get("name") or "").strip()


def vm_ip(token: str, vm_id: int) -> str:
    vm = vm_holen(token, vm_id)
    ip = ipv4(vm)
    if not ip:
        raise Abbruch(f"VPS {vm_id} hat noch keine IPv4-Adresse (Status: {vm.get('state')}).",
                      "Einrichtung im hPanel abschließen oder ein paar Minuten warten, dann 'pruefen' wiederholen.", 2)
    return ip


# ---------------------------------------------------------------- local tools / ssh

def programm(name: str) -> str:
    pfad = shutil.which(name)
    if not pfad:
        tipp = ("Windows: Einstellungen > System > Optionale Features > 'OpenSSH-Client' hinzufügen."
                if os.name == "nt" else "macOS/Linux: OpenSSH ist normalerweise vorhanden; Terminal neu starten.")
        raise Abbruch(f"Das Programm '{name}' fehlt auf diesem Rechner.", tipp)
    return pfad


def ssh_optionen() -> list[str]:
    return ["-i", str(SCHLUESSEL), "-o", "BatchMode=yes", "-o", "IdentitiesOnly=yes",
            "-o", "StrictHostKeyChecking=accept-new", "-o", f"UserKnownHostsFile={KNOWN_HOSTS}",
            "-o", "ConnectTimeout=15", "-o", "ServerAliveInterval=30"]


def ssh(ip: str, befehl: str, eingabe: bytes | None = None, ausgabe_zeigen: bool = False) -> subprocess.CompletedProcess:
    args = [programm("ssh"), *ssh_optionen(), f"root@{ip}", befehl]
    if ausgabe_zeigen:
        return subprocess.run(args, input=eingabe)
    return subprocess.run(args, input=eingabe, capture_output=True)


def ssh_fehler(ergebnis: subprocess.CompletedProcess, ip: str) -> Abbruch:
    text = (ergebnis.stderr or b"").decode(errors="replace") if isinstance(ergebnis.stderr, bytes) else str(ergebnis.stderr or "")
    if "REMOTE HOST IDENTIFICATION HAS CHANGED" in text or "Host key verification failed" in text:
        return Abbruch(f"Der Fingerabdruck von {ip} hat sich geändert (VPS neu installiert?).",
                       "Wenn der VPS bewusst neu installiert wurde: 'schluessel --vm <id> --fingerabdruck-erneuern' ausführen.")
    if "Permission denied" in text:
        return Abbruch(f"Der VPS {ip} akzeptiert den Schlüssel (noch) nicht.",
                       "Zuerst 'schluessel --vm <id>' ausführen; danach 1–2 Minuten warten und erneut versuchen.")
    if "timed out" in text or "Connection refused" in text or "No route" in text:
        return Abbruch(f"Der VPS {ip} ist per SSH nicht erreichbar.",
                       "Mit 'pruefen' kontrollieren, ob er 'läuft'. Ist im hPanel eine Hostinger-Firewall aktiv, muss Port 22 erlaubt sein.")
    zeile = text.strip().splitlines()[-1][:200] if text.strip() else f"Exit-Code {ergebnis.returncode}"
    return Abbruch(f"Befehl auf dem VPS fehlgeschlagen: {zeile}", "Ausgabe oben lesen; bei Bedarf den Befehl wiederholen.")


def ssh_bereit(ip: str) -> None:
    if not SCHLUESSEL.is_file():
        raise Abbruch("Es gibt noch keinen SSH-Schlüssel für den VPS.", "Zuerst 'schluessel --vm <id>' ausführen.")
    ergebnis = ssh(ip, "true")
    if ergebnis.returncode != 0:
        raise ssh_fehler(ergebnis, ip)


# ---------------------------------------------------------------- commands

def cmd_pruefen(args: argparse.Namespace) -> int:
    token = token_holen()
    # GET /api/vps/v1/virtual-machines  (array of VirtualMachineResource)
    vms = anfrage("GET", "/api/vps/v1/virtual-machines", token)
    try:
        # GET /api/vps/v1/data-centers  (id, name, location, city, continent)
        zentren = {z.get("id"): z for z in anfrage("GET", "/api/vps/v1/data-centers", token)}
    except Abbruch:
        zentren = {}
    print("Hostinger-API-Schlüssel ist gültig.")
    if not vms:
        print("Kein VPS in diesem Konto. Kauf abgeschlossen? Ein neuer VPS erscheint nach einigen Minuten.")
        return 2
    zeilen = [("ID", "Hostname", "IP", "Status", "OS", "Standort", "Tarif")]
    hinweise = []
    for vm in vms:
        z = zentren.get(vm.get("data_center_id")) or {}
        ort = ", ".join(x for x in (z.get("city"), (z.get("location") or "").upper()) if x) or "?"
        status = vm.get("state") or "?"
        zeilen.append((str(vm.get("id")), vm.get("hostname") or "-", ipv4(vm) or "-",
                       STATUS_DE.get(status, status), os_name(vm) or "-", ort, vm.get("plan") or "-"))
        if status == "initial":
            hinweise.append(f"VPS {vm.get('id')}: gekauft, aber nicht eingerichtet -> Nutzer schließt die Einrichtung im hPanel ab (Anleitung 02, Schritt 3).")
        elif os_name(vm) and "ubuntu 24.04" not in os_name(vm).lower():
            hinweise.append(f"VPS {vm.get('id')}: Betriebssystem ist '{os_name(vm)}', erwartet wird Ubuntu 24.04 ohne Panel (Anleitung 02, Schritt 3).")
        elif status == "running" and "ubuntu 24.04" in os_name(vm).lower():
            hinweise.append(f"VPS {vm.get('id')}: passt. Weiter mit: schluessel --vm {vm.get('id')}")
    breiten = [max(len(z[i]) for z in zeilen) for i in range(len(zeilen[0]))]
    for z in zeilen:
        print("  ".join(w.ljust(b) for w, b in zip(z, breiten)).rstrip())
    for h in hinweise:
        print(h)
    return 0


def cmd_schluessel(args: argparse.Namespace) -> int:
    token = token_holen()
    ip = vm_ip(token, args.vm)
    SSH_DIR.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(SSH_DIR, 0o700)
    except OSError:
        pass
    if not SCHLUESSEL.is_file():
        subprocess.run([programm("ssh-keygen"), "-q", "-t", "ed25519", "-N", "", "-C", "videoseiten",
                        "-f", str(SCHLUESSEL)], check=True)
        print(f"Neuer SSH-Schlüssel angelegt: {SCHLUESSEL.relative_to(HIER)}")
    oeffentlich = SCHLUESSEL.with_suffix(".pub").read_text(encoding="utf-8").strip()
    kern = oeffentlich.split()[1]

    # GET/POST /api/vps/v1/virtual-machines/{id}/ssh-keys  (keys for root; POST body {"keys": [...]})
    vorhanden = anfrage("GET", f"/api/vps/v1/virtual-machines/{args.vm}/ssh-keys", token) or []
    if any(kern in (k.get("key") or "") or kern == k.get("data") for k in vorhanden):
        print("Schlüssel ist auf dem VPS schon hinterlegt.")
    else:
        anfrage("POST", f"/api/vps/v1/virtual-machines/{args.vm}/ssh-keys", token, {"keys": [oeffentlich]})
        print("Öffentlicher Schlüssel bei Hostinger für root hinterlegt.")

    if args.fingerabdruck_erneuern and KNOWN_HOSTS.is_file():
        subprocess.run([programm("ssh-keygen"), "-R", ip, "-f", str(KNOWN_HOSTS)], capture_output=True)
        print("Alter Fingerabdruck entfernt.")

    # TODO(unverified): how fast Hostinger writes the key into authorized_keys; we poll up to ~3 min.
    letzter = None
    for versuch in range(18):
        letzter = ssh(ip, "true")
        if letzter.returncode == 0:
            print(f"SSH-Verbindung zu root@{ip} funktioniert. Weiter mit: einrichten --vm {args.vm} --domain <seiten-domain>")
            return 0
        text = (letzter.stderr or b"").decode(errors="replace")
        if "IDENTIFICATION HAS CHANGED" in text:
            break
        if versuch == 0:
            print("Warte, bis der Schlüssel auf dem VPS aktiv ist (bis zu 3 Minuten) …")
        time.sleep(10)
    raise ssh_fehler(letzter, ip)


def caddy_domain_pruefen(domain: str) -> str:
    domain = domain.strip().lower().rstrip(".")
    if domain.startswith(("http://", "https://")) or "/" in domain or not DOMAIN_RE.match(domain):
        raise Abbruch(f"'{domain}' ist keine gültige Domain.", "Nur den Namen angeben, z. B. angebot.kunde.de (ohne https://).")
    return domain


# Runs on the VPS via "python3 -" (stdin), so secret values never appear in a process list.
ENV_SKRIPT = r"""
import base64, json, os, subprocess
werte = json.loads(base64.b64decode("__DATEN__"))
pfad = "/etc/seiten.env"
zeilen = open(pfad, encoding="utf-8").read().splitlines() if os.path.exists(pfad) else []
def zeile(k, v):
    return k + '="' + v.replace('\\', '\\\\').replace('"', '\\"') + '"'
neu, gesetzt = [], set()
for z in zeilen:
    k = z.split("=", 1)[0].strip()
    if k in werte and k not in gesetzt:
        neu.append(zeile(k, werte[k]))
        gesetzt.add(k)
    elif k not in werte:
        neu.append(z)
neu += [zeile(k, v) for k, v in werte.items() if k not in gesetzt]
os.umask(0o077)
tmp = pfad + ".neu"
with open(tmp, "w", encoding="utf-8") as f:
    f.write("\n".join(neu) + "\n")
os.chmod(tmp, 0o600)
os.replace(tmp, pfad)
raise SystemExit(subprocess.run(["systemctl", "restart", "seiten-server"]).returncode)
"""


def geheimnisse_uebertragen(ip: str, werte: dict[str, str]) -> None:
    """Write values into /etc/seiten.env (600) via stdin, never via the command line."""
    daten = base64.b64encode(json.dumps(werte).encode()).decode()
    skript = ENV_SKRIPT.replace("__DATEN__", daten)
    ergebnis = ssh(ip, "python3 -", eingabe=skript.encode())
    if ergebnis.returncode != 0:
        raise Abbruch("Die Einstellungen konnten auf dem VPS nicht gespeichert werden (Dienst seiten-server startet nicht neu).",
                      "Zuerst 'einrichten' vollständig laufen lassen, dann 'geheimnis' wiederholen.")
    print("Gespeichert in /etc/seiten.env: " + ", ".join(sorted(werte)) + " (Werte nicht angezeigt). Dienst neu gestartet.")


def cmd_einrichten(args: argparse.Namespace) -> int:
    domain = caddy_domain_pruefen(args.domain)
    werte = geheimnisse_holen()
    token = token_holen()
    ip = vm_ip(token, args.vm)
    ssh_bereit(ip)
    for ordner in ("server", "vorlage"):
        if not (HIER / ordner).is_dir():
            raise Abbruch(f"Ordner {ordner}/ fehlt in {HIER}.", "Projekt vollständig auschecken und erneut versuchen.")
    print(f"Kopiere server/ und vorlage/ nach {ip} …")
    r = ssh(ip, f"rm -rf {REMOTE_STAGING} && mkdir -p {REMOTE_STAGING}")
    if r.returncode != 0:
        raise ssh_fehler(r, ip)
    r = subprocess.run([programm("scp"), "-q", "-r", *ssh_optionen(), str(HIER / "server"), str(HIER / "vorlage"),
                        f"root@{ip}:{REMOTE_STAGING}/"], capture_output=True)
    if r.returncode != 0:
        raise ssh_fehler(r, ip)
    print("Starte Einrichtung auf dem VPS (dauert beim ersten Mal einige Minuten) …")
    r = ssh(ip, f"bash {REMOTE_STAGING}/server/einrichten.sh --domain {domain}", ausgabe_zeigen=True)
    if r.returncode != 0:
        raise Abbruch("Das Einrichtungsskript auf dem VPS ist mit einem Fehler beendet worden.",
                      "Die letzten Zeilen oben lesen; der Befehl kann gefahrlos wiederholt werden.")
    if werte:
        geheimnisse_uebertragen(ip, werte)
    else:
        print("Hinweis: SKAEL_WEBHOOK_SECRET ist in .env noch leer. Später nachtragen und 'geheimnis --vm "
              f"{args.vm}' ausführen.")
    print(f"Einrichtung fertig. Prüfen mit: status --vm {args.vm} --domain {domain}")
    return 0


def cmd_geheimnis(args: argparse.Namespace) -> int:
    werte = geheimnisse_holen()
    if not werte:
        raise Abbruch("In .env sind SKAEL_WEBHOOK_SECRET und MELDUNG_URL leer.",
                      "Nutzer das Webhook-Geheimnis aus Skael in .env hinter SKAEL_WEBHOOK_SECRET= einfügen lassen.", 2)
    token = token_holen()
    ip = vm_ip(token, args.vm)
    ssh_bereit(ip)
    geheimnisse_uebertragen(ip, werte)
    return 0


def seiten_auswahl(ordner: Path, gesperrt: set[str]) -> tuple[list[str], list[str], list[str]]:
    """Relative paths to upload; skips objected and expired pages. Returns (paths, objected, expired)."""
    pfade, widersprochen, abgelaufen = [], [], []
    if (ordner / "assets").is_dir():
        pfade.append("assets")
    jetzt = datetime.now(timezone.utc)
    for seite in sorted((ordner / "v").iterdir()) if (ordner / "v").is_dir() else []:
        if not seite.is_dir() or not SEITEN_ID_RE.match(seite.name):
            continue
        if seite.name in gesperrt:
            widersprochen.append(seite.name)
            continue
        try:
            meta = json.loads((seite / ".meta.json").read_text(encoding="utf-8"))
            if datetime.fromisoformat(meta["ablauf"]) <= jetzt:
                abgelaufen.append(seite.name)
                continue
        except (OSError, ValueError, KeyError):
            pass
        pfade.append(f"v/{seite.name}")
    return pfade, widersprochen, abgelaufen


def cmd_hochladen(args: argparse.Namespace) -> int:
    ordner = Path(args.seiten).expanduser()
    if not ordner.is_absolute():
        ordner = (Path.cwd() / ordner) if (Path.cwd() / ordner).is_dir() else (HIER / ordner)
    if not (ordner / "v").is_dir():
        raise Abbruch(f"In {ordner} gibt es keinen Unterordner v/ mit Seiten.",
                      "Zuerst die Seiten mit server/generator.py erzeugen und dessen --ziel-Ordner hier angeben.")
    token = token_holen()
    ip = vm_ip(token, args.vm)
    ssh_bereit(ip)

    # Pages deleted after an objection must never come back.
    r = ssh(ip, "cat /srv/daten/widersprueche.jsonl 2>/dev/null || true")
    gesperrt = set()
    for zeile in (r.stdout or b"").decode(errors="replace").splitlines():
        try:
            gesperrt.add(json.loads(zeile).get("seiten_id"))
        except ValueError:
            continue
    pfade, widersprochen, abgelaufen = seiten_auswahl(ordner, gesperrt)
    anzahl = sum(1 for p in pfade if p.startswith("v/"))
    if not anzahl:
        raise Abbruch("Keine hochladbaren Seiten gefunden.", "Generator erneut laufen lassen und Ordner prüfen.")

    with tempfile.TemporaryDirectory() as tmp:
        liste = Path(tmp) / "liste.txt"
        liste.write_text("\n".join(pfade) + "\n", encoding="utf-8")
        # tar over ssh: available on macOS, Linux and Windows 10+, no rsync needed.
        umgebung = {**os.environ, "COPYFILE_DISABLE": "1"}  # no macOS ._ files
        tar = subprocess.Popen([programm("tar"), "-C", str(ordner), "-czf", "-", "-T", str(liste)],
                               stdout=subprocess.PIPE, env=umgebung)
        r = subprocess.run([programm("ssh"), *ssh_optionen(), f"root@{ip}",
                            f"mkdir -p {SEITEN_ZIEL} && tar -xzf - -C {SEITEN_ZIEL} --no-same-owner --warning=no-unknown-keyword"],
                           stdin=tar.stdout, capture_output=True)
        tar.stdout.close()
        if tar.wait() != 0:
            raise Abbruch("Die Seiten konnten lokal nicht gepackt werden (tar).", "Ordner prüfen und erneut versuchen.")
        if r.returncode != 0:
            raise ssh_fehler(r, ip)
    r = ssh(ip, f"chown -R seiten:seiten {SEITEN_ZIEL} && chmod -R u=rwX,go=rX {SEITEN_ZIEL}")
    if r.returncode != 0:
        raise Abbruch("Seiten hochgeladen, aber Rechte für den Benutzer 'seiten' nicht gesetzt.",
                      "Zuerst 'einrichten' ausführen (legt den Benutzer an), dann 'hochladen' wiederholen.")
    print(f"{anzahl} Seiten hochgeladen nach {SEITEN_ZIEL}.")
    if widersprochen:
        print(f"{len(widersprochen)} Seiten nicht hochgeladen, weil widersprochen wurde: {', '.join(widersprochen)}")
    if abgelaufen:
        print(f"{len(abgelaufen)} abgelaufene Seiten nicht hochgeladen.")
    return 0


def https_holen(url: str, methode: str = "GET", daten: bytes | None = None):
    req = urllib.request.Request(url, data=daten, method=methode, headers={"User-Agent": USER_AGENT, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:  # noqa: S310 (https only)
            return resp.status, resp.headers
    except urllib.error.HTTPError as exc:
        return exc.code, exc.headers


def cmd_status(args: argparse.Namespace) -> int:
    domain = caddy_domain_pruefen(args.domain)
    token = token_holen()
    ip = vm_ip(token, args.vm)
    ok = True

    try:
        aufgeloest = socket.gethostbyname(domain)
    except OSError:
        aufgeloest = ""
    if aufgeloest == ip:
        print(f"DNS: {domain} zeigt auf {ip}. OK")
    else:
        ok = False
        print(f"DNS: {domain} zeigt auf {aufgeloest or 'nichts'}, erwartet {ip}. -> A-Record setzen (dns-Befehl oder anleitungen/03_dns.md); Änderungen brauchen bis zu einige Stunden.")

    try:
        code, kopf = https_holen(f"https://{domain}/robots.txt")
        robots = (kopf.get("X-Robots-Tag") or "") if kopf else ""
        print(f"HTTPS: Antwort {code}. {'OK' if code == 200 else 'unerwartet'}")
        if "noindex" in robots:
            print(f"X-Robots-Tag: {robots}. OK")
        else:
            ok = False
            print("X-Robots-Tag fehlt. -> 'einrichten' erneut ausführen (Caddyfile).")
        code_api, _ = https_holen(f"https://{domain}/api/m", "POST", b'{"seiten_id":"x","ereignis":"seite_geoeffnet"}')
        if code_api == 204:
            print("Messung (/api/m): erreichbar. OK")
        else:
            ok = False
            print(f"Messung (/api/m): Antwort {code_api}, erwartet 204. -> Dienst seiten-server prüfen.")
        ok = ok and code == 200
    except (urllib.error.URLError, ssl.SSLError, OSError) as exc:
        ok = False
        grund = str(getattr(exc, "reason", exc))
        print(f"HTTPS: keine gültige Antwort ({grund[:120]}). -> Stimmt DNS, holt Caddy das Zertifikat meist innerhalb weniger Minuten; sonst 'einrichten' erneut ausführen.")

    try:
        ssh_bereit(ip)
        r = ssh(ip, "systemctl is-active seiten-server; systemctl is-active caddy")
        dienste = (r.stdout or b"").decode().split()
        namen = ["seiten-server", "caddy"]
        for name, zustand in zip(namen, dienste + ["?"] * (2 - len(dienste))):
            print(f"Dienst {name}: {zustand}{'. OK' if zustand == 'active' else ' -> einrichten erneut ausführen'}")
            ok = ok and zustand == "active"
    except Abbruch as exc:
        ok = False
        print(f"SSH: {exc.was} -> {exc.tun}")

    print("Alles in Ordnung." if ok else "Noch nicht alles in Ordnung (siehe Zeilen mit ->).")
    return 0 if ok else 1


def cmd_dns(args: argparse.Namespace) -> int:
    domain = caddy_domain_pruefen(args.domain)
    name = args.name.strip().lower().rstrip(".")
    if name.endswith("." + domain):
        name = name[: -len(domain) - 1]
    if not LABEL_RE.match(name):
        raise Abbruch(f"'{args.name}' ist kein gültiger Name für den Eintrag.", "Nur den vorderen Teil angeben, z. B. angebot (oder @ für die Domain selbst).")
    try:
        ip = str(ipaddress.IPv4Address(args.ip.strip()))
    except ValueError:
        raise Abbruch(f"'{args.ip}' ist keine IPv4-Adresse.", "IP mit 'pruefen' ablesen und erneut angeben.") from None
    fqdn = domain if name == "@" else f"{name}.{domain}"
    token = token_holen()

    # GET /api/dns/v1/zones/{domain}
    # TODO(unverified): status code for a domain whose zone is not on this account; docs say 404 for
    # resources not visible to the token owner (errors.md), the spec only lists 200/401/500.
    try:
        zone = anfrage("GET", f"/api/dns/v1/zones/{domain}", token)
    except Abbruch as exc:
        if getattr(exc, "status", None) in (400, 404, 422):
            print(f"Die Domain {domain} liegt nicht in diesem Hostinger-Konto (keine DNS-Zone bei Hostinger).")
            print(f"Der Nutzer muss den Eintrag bei seinem Domain-Anbieter setzen: Typ A, Name {name}, Ziel {ip}, TTL 300 "
                  "(Schritt für Schritt: anleitungen/03_dns.md).")
            return 2
        raise

    eigene = [r for r in zone or [] if (r.get("name") or "").lower() == name]
    if any(r.get("type") == "CNAME" for r in eigene):
        raise Abbruch(f"Für {fqdn} gibt es bei Hostinger schon einen CNAME-Eintrag; A und CNAME gehen nicht gleichzeitig.",
                      "Mit dem Nutzer klären, ob der CNAME weg darf (hPanel > Domains > DNS), dann erneut ausführen.", 2)
    for r in eigene:
        if r.get("type") == "A" and [x.get("content") for x in r.get("records") or []] == [ip]:
            print(f"A-Record {fqdn} -> {ip} ist schon gesetzt.")
            return 0

    # PUT /api/dns/v1/zones/{domain}; overwrite=true replaces only RRs with the same name and type.
    auftrag = {"overwrite": True, "zone": [{"name": name, "type": "A", "ttl": 300, "records": [{"content": ip}]}]}
    anfrage("POST", f"/api/dns/v1/zones/{domain}/validate", token, auftrag)
    anfrage("PUT", f"/api/dns/v1/zones/{domain}", token, auftrag)
    print(f"A-Record gesetzt: {fqdn} -> {ip} (TTL 300).")

    try:
        # GET /api/domains/v1/portfolio/{domain} -> name_servers. Hostinger nameservers differ per site
        # (docs.hostinger.com/domains/pointing.md), so we only show them.
        details = anfrage("GET", f"/api/domains/v1/portfolio/{domain}", token, versuche=1)
        ns = ", ".join(v for v in (details.get("name_servers") or {}).values() if v)
        if ns:
            print(f"Nameserver laut Hostinger: {ns}. Zeigt die Domain woanders hin, wirkt der Eintrag nicht.")
    except Abbruch:
        print("Hinweis: Domain ist nicht bei Hostinger registriert, nur die DNS-Zone. Wirkt nur, wenn die Nameserver auf Hostinger zeigen.")
    print(f"Wirksam meist nach Minuten, selten bis zu 24 Stunden. Prüfen mit: status --vm <id> --domain {fqdn}")
    return 0


# ---------------------------------------------------------------- main

def main(argv: list[str] | None = None) -> int:
    for strom in (sys.stdout, sys.stderr):
        try:
            strom.reconfigure(errors="replace")  # type: ignore[attr-defined]
        except AttributeError:
            pass
    p = argparse.ArgumentParser(description="Hostinger-VPS für die Landingpages")
    sub = p.add_subparsers(dest="befehl", required=True)
    sub.add_parser("pruefen", help="API-Schlüssel prüfen, VPS auflisten")
    s = sub.add_parser("schluessel", help="SSH-Schlüssel anlegen, hinterlegen, testen")
    s.add_argument("--vm", type=int, required=True)
    s.add_argument("--fingerabdruck-erneuern", action="store_true", help="nach bewusster Neuinstallation des VPS")
    s = sub.add_parser("dns", help="A-Record setzen, wenn die Domain bei Hostinger liegt")
    s.add_argument("--domain", required=True, help="z. B. kunde.de")
    s.add_argument("--name", required=True, help="z. B. angebot (oder @)")
    s.add_argument("--ip", required=True)
    s = sub.add_parser("einrichten", help="Server auf dem VPS einrichten")
    s.add_argument("--vm", type=int, required=True)
    s.add_argument("--domain", required=True, help="Seiten-Domain, z. B. angebot.kunde.de")
    s = sub.add_parser("geheimnis", help="SKAEL_WEBHOOK_SECRET/MELDUNG_URL aus .env auf den VPS schreiben")
    s.add_argument("--vm", type=int, required=True)
    s = sub.add_parser("hochladen", help="erzeugte Seiten nach /srv/seiten übertragen")
    s.add_argument("--vm", type=int, required=True)
    s.add_argument("--seiten", required=True, help="--ziel-Ordner des Generators")
    s = sub.add_parser("status", help="HTTPS, X-Robots-Tag und Dienste prüfen")
    s.add_argument("--vm", type=int, required=True)
    s.add_argument("--domain", required=True)
    args = p.parse_args(argv)
    befehle = {"pruefen": cmd_pruefen, "schluessel": cmd_schluessel, "dns": cmd_dns, "einrichten": cmd_einrichten,
               "geheimnis": cmd_geheimnis, "hochladen": cmd_hochladen, "status": cmd_status}
    try:
        return befehle[args.befehl](args)
    except Abbruch as exc:
        print(f"FEHLER: {exc.was}\nWAS TUN: {exc.tun}", file=sys.stderr)
        return exc.code
    except KeyboardInterrupt:
        print("Abgebrochen.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
