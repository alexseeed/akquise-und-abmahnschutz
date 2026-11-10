"""Eigene Blockliste: Firmen, die schon einmal angeschrieben wurden (z. B. aus früheren Kampagnen).

Anders als die Community-Sperrliste ist diese Liste privat und bleibt lokal in data/blockliste.txt
(nie weitergeben, enthält personenbezogene Daten). Eine Zeile je Eintrag:

    beispiel.de             → sperrt die Domain inkl. Subdomains und aller Adressen darunter
    max@t-online.de         → sperrt genau diese Adresse (für Freemail-Adressen)
    # Kommentar

Gegriffen wird an zwei Stellen:
  * Stufe 3b: Firmen, deren Website auf der Liste steht, werden gar nicht erst geprüft oder
    angereichert (dedupe_status='dropped_blocked') — spart Credits.
  * Export: E-Mail und Website werden nochmals abgeglichen, Treffer landen in Liste 5.

Befüllen:  python3 -m scraper blockliste-import <alte_leads.csv>
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

from .config import DATA_DIR, FREEMAIL_DOMAINS
from .sperrliste import norm_domain

DATEI = DATA_DIR / "blockliste.txt"
SPALTEN_MUSTER = re.compile(r"mail|website|webseite|domain|url|homepage|contact", re.I)
AUSNAHMEN = re.compile(r"video|thumbnail|bild|image|logo|linkedin|maps|storefront|assignee|contacted.from|opened|replied|clicked|count|timestamp|visitor|provider", re.I)


class Blockliste:
    def __init__(self, domains: set[str], adressen: set[str]):
        self.domains = domains
        self.adressen = adressen

    def treffer(self, *werte: str | None) -> str | None:
        """Gibt den Eintrag zurück, falls einer der Werte (E-Mail, URL, Domain) blockiert ist."""
        for wert in werte:
            roh = str(wert or "").strip().lower()
            if not roh:
                continue
            if "@" in roh and roh in self.adressen:
                return roh
            d = norm_domain(roh)
            teile = d.split(".")
            for i in range(len(teile) - 1):
                kandidat = ".".join(teile[i:])
                if kandidat in self.domains:
                    return kandidat
        return None

    def __len__(self) -> int:
        return len(self.domains) + len(self.adressen)


def laden() -> Blockliste:
    domains: set[str] = set()
    adressen: set[str] = set()
    if DATEI.exists():
        for zeile in DATEI.read_text(encoding="utf-8").splitlines():
            z = zeile.strip().lower()
            if not z or z.startswith("#"):
                continue
            (adressen if "@" in z else domains).add(z)
    return Blockliste(domains, adressen)


def _eintraege(wert: str | None) -> set[str]:
    """Domain bzw. — bei Freemail — die genaue Adresse aus einem Zellenwert."""
    roh = str(wert or "").strip().lower()
    if not roh or " " in roh:
        return set()
    d = norm_domain(roh)
    if "." not in d:
        return set()
    if d in FREEMAIL_DOMAINS:
        return {roh} if "@" in roh else set()
    return {d}


def importieren(csv_pfad: Path) -> tuple[int, int, list[str]]:
    """Übernimmt Domains/Adressen aus einer Leadliste. Gibt (Zeilen, neue Einträge, Spalten) zurück."""
    with open(csv_pfad, encoding="utf-8-sig", newline="") as fh:
        probe = fh.read(16384)
        fh.seek(0)
        try:
            dialekt = csv.Sniffer().sniff(probe, delimiters=",;\t")
        except csv.Error:
            dialekt = csv.excel
        reader = csv.DictReader(fh, dialect=dialekt)
        felder = [f for f in (reader.fieldnames or []) if f]
        spalten = [f for f in felder if SPALTEN_MUSTER.search(f) and not AUSNAHMEN.search(f)]
        if not spalten:
            raise SystemExit(f"Keine E-Mail-/Website-Spalte erkannt. Vorhanden: {', '.join(felder)}")
        neu: set[str] = set()
        zeilen = 0
        for row in reader:
            zeilen += 1
            for s in spalten:
                neu |= _eintraege(row.get(s))

    vorhanden = laden()
    bekannt = vorhanden.domains | vorhanden.adressen
    hinzu = sorted(neu - bekannt)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with DATEI.open("a", encoding="utf-8") as fh:
        if not DATEI.stat().st_size:
            fh.write("# Eigene Blockliste – bereits kontaktierte Firmen. Privat, nie weitergeben.\n")
        fh.write(f"# Import aus {csv_pfad.name} ({zeilen} Zeilen)\n")
        fh.writelines(e + "\n" for e in hinzu)
    return zeilen, len(hinzu), spalten
