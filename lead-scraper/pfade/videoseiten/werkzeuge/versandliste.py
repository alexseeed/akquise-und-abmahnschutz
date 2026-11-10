#!/usr/bin/env python3
"""Hand-over to the mail tool and processing of deletion requests.

    python3 werkzeuge/versandliste.py links --csv <export-liste.csv> --ergebnis <seiten/ergebnis.json> [--aus <datei.csv>]
    python3 werkzeuge/versandliste.py loeschungen --datei <widersprueche.jsonl> --leads <leads_mit_video.json> [--aus <datei.csv>]

`links` adds two columns to an export list (list 1 or 2 of the scraper, semicolon CSV):
  Landingpage   personal page of the lead
  Vorschaubild  preview image on the own server, for an image link in the mail
                (never Skael's image: the mail client would load it from Skael)
Leads without a page are left out and listed.

`loeschungen` turns the objections collected on the server into a CSV with e-mail and domain,
for the mail tool's suppression list and for `blockliste-import` of the scraper.
Standard library only.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from urllib.parse import urlparse

ID_SPALTEN = ("Externe ID", "externe_id")


def lies_csv(pfad: Path) -> tuple[list[str], list[dict], str]:
    roh = pfad.read_text(encoding="utf-8-sig")
    trenner = ";" if roh.count(";") >= roh.count(",") else ","
    r = csv.DictReader(roh.splitlines(), delimiter=trenner)
    return list(r.fieldnames or []), list(r), trenner


def schreibe_csv(pfad: Path, spalten: list[str], zeilen: list[dict], trenner: str) -> None:
    with pfad.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=spalten, delimiter=trenner, extrasaction="ignore")
        w.writeheader()
        w.writerows(zeilen)


def cmd_links(a) -> None:
    spalten, zeilen, trenner = lies_csv(Path(a.csv))
    id_spalte = next((s for s in ID_SPALTEN if s in spalten), None)
    if not id_spalte:
        sys.exit("In der Liste fehlt die Spalte „Externe ID“. Bitte den Export neu erstellen "
                 "(python3 -m scraper --kampagne <name> export --lead-format).")
    ergebnis = json.loads(Path(a.ergebnis).read_text(encoding="utf-8"))
    links = {str(s["externe_id"]): s["link"] for s in ergebnis.get("seiten", [])}
    vorschau = {}
    for s in ergebnis.get("seiten", []):
        datei = s.get("vorschaubild") or ""
        if datei.startswith("/"):
            basis = "{0.scheme}://{0.netloc}".format(urlparse(s["link"]))
            vorschau[str(s["externe_id"])] = basis + datei
        elif datei:
            vorschau[str(s["externe_id"])] = s["link"].rstrip("/") + "/" + datei
    mit, ohne = [], []
    for z in zeilen:
        ext = str(z.get(id_spalte, "")).strip()
        if ext in links:
            z["Landingpage"] = links[ext]
            z["Vorschaubild"] = vorschau.get(ext, "")
            mit.append(z)
        else:
            ohne.append(z.get("Firmenname") or ext)
    ziel = Path(a.aus) if a.aus else Path(a.csv).with_name(Path(a.csv).stem + "_mit_landingpage.csv")
    schreibe_csv(ziel, spalten + ["Landingpage", "Vorschaubild"], mit, trenner)
    print(f"{len(mit)} Leads mit Landingpage → {ziel}")
    if ohne:
        print(f"{len(ohne)} Leads ohne Seite (kein fertiges Video oder übersprungen), nicht in der Datei: "
              + ", ".join(ohne[:10]) + (" …" if len(ohne) > 10 else ""))


def cmd_loeschungen(a) -> None:
    eintraege = []
    for zeile in Path(a.datei).read_text(encoding="utf-8").splitlines():
        if zeile.strip():
            eintraege.append(json.loads(zeile))
    leads = {str(l.get("externe_id")): l for l in json.loads(Path(a.leads).read_text(encoding="utf-8"))}
    zeilen, unbekannt = [], 0
    for e in eintraege:
        lead = leads.get(str(e.get("externe_id")))
        if not lead:
            unbekannt += 1
            continue
        zeilen.append({"E-Mail": lead.get("email", ""), "Domain": lead.get("domain", ""),
                       "Firmenname": lead.get("firma", ""), "Externe ID": e.get("externe_id"),
                       "Datenlöschung am": (e.get("zeit") or "")[:10]})
    ziel = Path(a.aus) if a.aus else Path(a.datei).with_name("datenloeschungen.csv")
    schreibe_csv(ziel, ["E-Mail", "Domain", "Firmenname", "Externe ID", "Datenlöschung am"], zeilen, ";")
    print(f"{len(zeilen)} Datenlöschungen → {ziel}")
    if unbekannt:
        print(f"{unbekannt} Einträge gehören zu keinem Lead in dieser Liste (andere Kampagne?).")
    print("Jetzt: diese Adressen im Mailtool sperren und mit `blockliste-import` in den Scraper übernehmen.")


def main() -> None:
    p = argparse.ArgumentParser(description="Versandliste mit Landingpages, Datenlöschungen")
    sub = p.add_subparsers(dest="befehl", required=True)
    s = sub.add_parser("links", help="Landingpage-Links in eine Exportliste schreiben")
    s.add_argument("--csv", required=True)
    s.add_argument("--ergebnis", required=True)
    s.add_argument("--aus")
    s.set_defaults(f=cmd_links)
    s = sub.add_parser("loeschungen", help="Datenlöschungen vom Server in eine Sperr-CSV umwandeln")
    s.add_argument("--datei", required=True)
    s.add_argument("--leads", required=True)
    s.add_argument("--aus")
    s.set_defaults(f=cmd_loeschungen)
    a = p.parse_args()
    a.f(a)


if __name__ == "__main__":
    main()
