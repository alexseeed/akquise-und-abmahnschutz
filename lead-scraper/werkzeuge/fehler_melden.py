#!/usr/bin/env python3
"""Meldet eine Fehlermeldung an Agentur Consulting.

    python3 werkzeuge/fehler_melden.py --skript <name> "<Fehlermeldung>"
    python3 werkzeuge/fehler_melden.py --skript <name> < fehler.txt

Nur die Fehlermeldung, nie Lead-Daten. Vor dem Senden werden Geheimnisse
geschwärzt (.env-Werte, Schlüssel, Tokens, fremde E-Mails); der Text wird auf
4000 Zeichen gekürzt. Die Kontakt-E-Mail kommt aus AC_KONTAKT_EMAIL (Umgebung
oder .env). Meldet sich nicht, kracht es nie: Bei Netzfehlern gibt es nur einen
Hinweis (Exit 0).

Nur Python-Standardbibliothek.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

MELDUNG_URL = "https://learning.agentur-consulting.de/scraper-mcp/meldung"
USER_AGENT = "akquise-fehler-melden/1"
TIMEOUT = 10
MAX_TEXT = 4000
MAX_NUTZLAST = 8000  # die Meldestelle nimmt höchstens 8 KB

ROOT = Path(__file__).resolve().parent.parent  # lead-scraper/
GESCHWAERZT = "[geschwärzt]"

_SK_SCHLUESSEL = re.compile(r"sk-[A-Za-z0-9_.\-]+")
_BEARER = re.compile(r"Bearer\s+([A-Za-z0-9_.\~+/=\-]+)")
_LANGER_TOKEN = re.compile(r"[A-Za-z0-9_\-]{32,}")
_EMAIL = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")


def _dotenv_werte(pfad: Path) -> dict[str, str]:
    """Liest eine .env mit denselben Regeln wie _load_dotenv in pfade/*/config.py
    (dort je Pfad privat, deshalb hier nachgebaut statt importiert)."""
    werte: dict[str, str] = {}
    try:
        text = pfad.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        text = pfad.read_text(encoding="cp1252", errors="replace")
    except OSError:
        return werte
    for raw in text.splitlines():
        zeile = raw.strip()
        if not zeile or zeile.startswith("#") or "=" not in zeile:
            continue
        key, _, value = zeile.partition("=")
        werte.setdefault(key.strip(), value.strip().strip('"').strip("'"))
    return werte


def _env_dateien() -> list[Path]:
    kandidaten = [Path.cwd() / ".env", ROOT / ".env", *sorted((ROOT / "pfade").glob("*/.env"))]
    gefunden, gesehen = [], set()
    for pfad in kandidaten:
        if pfad not in gesehen:
            gesehen.add(pfad)
            if pfad.is_file():
                gefunden.append(pfad)
    return gefunden


def kontakt_lesen(dateien: list[Path] | None = None) -> str | None:
    """AC_KONTAKT_EMAIL aus der Umgebung, sonst aus der ersten .env, die sie nennt."""
    kandidaten = [os.environ.get("AC_KONTAKT_EMAIL", "")]
    kandidaten += [_dotenv_werte(p).get("AC_KONTAKT_EMAIL", "") for p in (_env_dateien() if dateien is None else dateien)]
    for kandidat in kandidaten:
        kandidat = (kandidat or "").strip()
        if kandidat and _EMAIL.fullmatch(kandidat):
            return kandidat
    return None


def geheimnisse_lesen(dateien: list[Path] | None = None) -> list[str]:
    geheim = []
    for pfad in (_env_dateien() if dateien is None else dateien):
        # shortcut: Werte unter 8 Zeichen nicht geschwärzt (sonst werden Wörter wie "true"
        # unleserlich); verbessern, sobald kurze Geheimnisse in Fehlermeldungen auftauchen.
        geheim.extend(v for v in _dotenv_werte(pfad).values() if len(v) >= 8)
    return geheim


def version_lesen(changelog: Path = ROOT / "CHANGELOG.md") -> str | None:
    """Erster Versionseintrag der CHANGELOG-Kopfzeilen („## …“), sonst None."""
    try:
        for zeile in changelog.read_text(encoding="utf-8").splitlines():
            zeile = zeile.strip()
            if zeile.startswith("## "):
                return zeile[3:].strip()[:80] or None
    except OSError:
        return None
    return None


def schwaerzen(text: str, geheimnisse: list[str], kontakt: str | None) -> str:
    ausgenommen = (kontakt or "").lower()
    for wert in sorted(set(geheimnisse), key=len, reverse=True):
        if wert and wert.lower() != ausgenommen:
            text = text.replace(wert, GESCHWAERZT)
    text = _SK_SCHLUESSEL.sub(GESCHWAERZT, text)
    text = _BEARER.sub("Bearer " + GESCHWAERZT, text)
    text = _LANGER_TOKEN.sub(GESCHWAERZT, text)
    return _EMAIL.sub(lambda m: m.group(0) if m.group(0).lower() == ausgenommen else GESCHWAERZT, text)


def nutzlast(text: str, skript: str | None, kontakt: str | None, version: str | None) -> dict:
    payload: dict = {"text": text[:MAX_TEXT]}
    if skript:
        payload["skript"] = skript[:200]
    if kontakt:
        payload["kontakt"] = kontakt
    payload["version"] = version
    while len(json.dumps(payload, ensure_ascii=False).encode("utf-8")) > MAX_NUTZLAST and len(payload["text"]) > 10:
        payload["text"] = payload["text"][: max(10, len(payload["text"]) // 2)]
    return payload


def senden(payload: dict) -> str:
    daten = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(MELDUNG_URL, data=daten, method="POST",
                                 headers={"Content-Type": "application/json", "User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as antwort:
        try:
            body = json.loads(antwort.read().decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return ""
    return str(body.get("meldung_id", "") or "") if isinstance(body, dict) else ""


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Fehlermeldung geschwärzt an Agentur Consulting melden.")
    p.add_argument("--skript", default=None, help="Name des gescheiterten Skripts oder Laufs")
    p.add_argument("--dry-run", action="store_true", help="Nur den geschwärzten Text zeigen, nichts senden")
    p.add_argument("text", nargs="?", help="Fehlermeldung (sonst über stdin einlesen)")
    args = p.parse_args(argv)

    if args.text is None:
        if sys.stdin.isatty():
            p.error("Fehlertext fehlt: als Argument übergeben oder über stdin senden.")
        raw = sys.stdin.read()
    else:
        raw = args.text
    if not raw.strip():
        p.error("Fehlertext ist leer – nichts zu melden.")

    kontakt = kontakt_lesen()
    text = schwaerzen(raw.strip(), geheimnisse_lesen(), kontakt)[:MAX_TEXT]
    if len(text) < 10:
        print("Die Fehlermeldung ist zu kurz (mindestens 10 Zeichen) – nichts gesendet.")
        return 0
    if args.dry_run:
        print(text)
        return 0

    try:
        meldung_id = senden(nutzlast(text, args.skript, kontakt, version_lesen()))
    except urllib.error.HTTPError as e:
        if e.code == 429:
            print("Zu viele Meldungen in kurzer Zeit – bitte in einer Stunde erneut versuchen.")
        elif e.code == 413:
            print("Die Fehlermeldung ist zu lang für die Meldestelle – bitte kürzen und erneut versuchen.")
        elif e.code == 400:
            print("Die Meldestelle hat die Meldung abgelehnt – bitte Fehlermeldung prüfen und erneut versuchen.")
        else:
            print(f"Die Meldestelle antwortet gerade nicht (HTTP {e.code}) – bitte später erneut versuchen.")
        return 0
    except Exception:
        print("Fehler konnte nicht gemeldet werden (keine Internetverbindung?) – bitte später erneut versuchen.")
        return 0
    if meldung_id:
        print(f"Fehler an Agentur Consulting gemeldet (ID {meldung_id}). Wir melden uns im Google Chat.")
    else:
        print("Fehler an Agentur Consulting gemeldet. Wir melden uns im Google Chat.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
