#!/usr/bin/env python3
"""Prüft die Wissensbibliothek auf veraltete und kaputte Stellen.

    python3 werkzeuge/wissen_pruefen.py            # aus dem Ordner lead-scraper/
    python3 werkzeuge/wissen_pruefen.py --streng   # Warnungen zählen als Fehler

Geprüft wird:
  1. Kopfzeilen: jede Datei in wissen/ nennt **Zweck:** und **Für wen:**.
  2. Ablaufdaten: **Prüfen bis:** JJJJ-MM-TT darf nicht in der Vergangenheit liegen
     (Warnung 14 Tage vorher).
  3. Index: jede Datei in wissen/ steht in wissen/00_INDEX.md.
  4. Verweise: in `Backticks` genannte Dateien (…md, …py, pfade/…) existieren.
     Noch nicht gebaute Dateien im Dokument ausnehmen mit:  <!-- geplante-dateien: a.py, b.py -->
  5. WISSEN_KOMPLETT.md im Paketordner ist aus dem aktuellen wissen/ erzeugt.
  6. SKILL.md hat höchstens 500 Zeilen.

Exit-Code 1 bei Fehlern. Nur Python-Standardbibliothek.
"""
from __future__ import annotations

import argparse
import importlib.util
import re
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent          # lead-scraper/
WISSEN = ROOT / "wissen"
PAKET = ROOT.parent                                     # akquise-und-abmahnschutz/ (falls vorhanden)

PRUEFEN_BIS = re.compile(r"\*\*Prüfen bis:\*\*\s*(\d{4}-\d{2}-\d{2})")
VERWEIS = re.compile(r"`([^`\s]+)`")
DATEI = re.compile(r"^[\w./-]+\.(md|py|js|json|txt|csv|sh|gs)$|^(pfade|wissen|werkzeuge)/[\w./-]+$")
PLATZHALTER = ("…", "<", ">", "NN", "*", "xx", "YYYY", "JJJJ")
LAUFZEIT_ORDNER = {"arbeit", "auftraege", "data", "exports"}   # entstehen erst bei einem Lauf
GEPLANT = re.compile(r"<!--\s*geplante-dateien:\s*(.*?)-->", re.S)
# Verzeichnisse, gegen die ein relativer Verweis aufgelöst wird
# Verweise in einem Pfad gelten relativ zum Pfad-Ordner (z. B. `prompts/…`, `docs/…`)
SUCHORTE = [ROOT, WISSEN, PAKET] + sorted(p for p in (ROOT / "pfade").iterdir() if p.is_dir())


def dokumente() -> list[Path]:
    dateien = sorted(WISSEN.glob("*.md"))
    dateien += [ROOT / "SKILL.md", ROOT / "CLAUDE.md", ROOT / "README.md"]
    for pfad in sorted((ROOT / "pfade").iterdir()):
        if pfad.is_dir():
            dateien += [p for p in (pfad / "README.md", pfad / "ABLAUF.md", pfad / "CLAUDE.md") if p.exists()]
            dateien += sorted((pfad / "referenzen").glob("*.md")) if (pfad / "referenzen").is_dir() else []
            dateien += sorted((pfad / "docs").glob("*.md")) if (pfad / "docs").is_dir() else []
    return [p for p in dateien if p.exists()]


def rel(p: Path) -> str:
    return str(p.relative_to(ROOT))


def pruefe_kopf(fehler: list[str]) -> None:
    for p in sorted(WISSEN.glob("*.md")):
        if p.name == "00_INDEX.md":
            continue
        kopf = p.read_text(encoding="utf-8")[:1500]
        for feld in ("**Zweck:**", "**Für wen:**"):
            if feld not in kopf:
                fehler.append(f"{rel(p)}: Kopfzeile {feld} fehlt")


def pruefe_ablauf(fehler: list[str], warnungen: list[str], heute: date) -> None:
    for p in dokumente():
        for treffer in PRUEFEN_BIS.finditer(p.read_text(encoding="utf-8")):
            frist = date.fromisoformat(treffer.group(1))
            if frist < heute:
                fehler.append(f"{rel(p)}: Prüfen bis {frist} ist abgelaufen – Fakten prüfen, Stand und Frist erneuern")
            elif frist - heute <= timedelta(days=14):
                warnungen.append(f"{rel(p)}: Prüfen bis {frist} läuft bald ab")


def pruefe_index(fehler: list[str]) -> None:
    index = (WISSEN / "00_INDEX.md").read_text(encoding="utf-8")
    for p in sorted(WISSEN.glob("*.md")):
        if p.name != "00_INDEX.md" and f"`{p.name}`" not in index:
            fehler.append(f"wissen/{p.name}: fehlt in wissen/00_INDEX.md")


def alle_dateinamen() -> set[str]:
    basis = PAKET if (PAKET / "einrichten.py").exists() else ROOT
    return {p.name for p in basis.rglob("*") if p.is_file()}


def zu_pruefen(verweis: str) -> bool:
    """Nur echte Datei-Verweise: keine URL-Pfade (/meta.json), keine Laufzeit-Dateien, keine Kurzformen (wissen/02)."""
    if verweis.startswith("/") or "://" in verweis or any(x in verweis for x in PLATZHALTER):
        return False
    erster = verweis.split("/")[0]
    if erster in LAUFZEIT_ORDNER or ("/" in verweis and "." in erster and erster != ".."):
        return False  # runtime folder or host name (googletagmanager.com/gtm.js)
    if "/" in verweis:
        return bool(DATEI.match(verweis)) and "." in verweis.rsplit("/", 1)[-1]
    return verweis.endswith((".md", ".py"))


def existiert(verweis: str, basis: Path, namen: set[str]) -> bool:
    ziel = verweis.split("#")[0].rstrip("/")
    if "/" not in ziel:
        return ziel in namen  # bare file name: exists anywhere in the package
    return any((ort / ziel).exists() for ort in [basis] + SUCHORTE)


def pruefe_verweise(warnungen: list[str]) -> None:
    namen = alle_dateinamen()
    for p in dokumente():
        text = p.read_text(encoding="utf-8")
        gemeldet = {g.strip() for m in GEPLANT.findall(text) for g in m.split(",") if g.strip()}
        for verweis in VERWEIS.findall(text):
            if verweis in gemeldet or not zu_pruefen(verweis):
                continue
            if not existiert(verweis, p.parent, namen):
                gemeldet.add(verweis)
                warnungen.append(f"{rel(p)}: Verweis `{verweis}` zeigt auf keine Datei")


def pruefe_komplett(warnungen: list[str]) -> None:
    einrichten = PAKET / "einrichten.py"
    komplett = PAKET / "WISSEN_KOMPLETT.md"
    if not (einrichten.exists() and komplett.exists()):
        return  # Skill-Kopie ohne Paketordner: nichts zu prüfen
    spec = importlib.util.spec_from_file_location("einrichten", einrichten)
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    if komplett.read_text(encoding="utf-8") != modul.wissen_komplett_text():
        warnungen.append("WISSEN_KOMPLETT.md ist veraltet – im Paketordner `python3 einrichten.py --nur-zips` ausführen")


def pruefe_laenge(warnungen: list[str]) -> None:
    zeilen = len((ROOT / "SKILL.md").read_text(encoding="utf-8").splitlines())
    if zeilen > 500:
        warnungen.append(f"SKILL.md hat {zeilen} Zeilen (Richtwert ≤ 500) – Details nach wissen/ auslagern")


def main() -> int:
    a = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--streng", action="store_true", help="Warnungen zählen als Fehler")
    a.add_argument("--heute", help="Datum für die Prüfung (JJJJ-MM-TT), Standard: heute")
    args = a.parse_args()
    heute = date.fromisoformat(args.heute) if args.heute else date.today()

    fehler: list[str] = []
    warnungen: list[str] = []
    pruefe_kopf(fehler)
    pruefe_ablauf(fehler, warnungen, heute)
    pruefe_index(fehler)
    pruefe_verweise(warnungen)
    pruefe_komplett(warnungen)
    pruefe_laenge(warnungen)

    for f in fehler:
        print(f"FEHLER   {f}")
    for w in warnungen:
        print(f"WARNUNG  {w}")
    if not fehler and not warnungen:
        print(f"Wissensbibliothek in Ordnung ({len(dokumente())} Dateien geprüft).")
    return 1 if fehler or (args.streng and warnungen) else 0


if __name__ == "__main__":
    sys.exit(main())
