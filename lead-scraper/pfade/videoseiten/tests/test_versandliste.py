"""Offline-Tests für versandliste.py — Formelschutz in den Versand-CSVs.

    python3 -m unittest discover -s tests -v      (aus pfade/videoseiten/)
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

HIER = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("versandliste", HIER / "werkzeuge" / "versandliste.py")
versand = importlib.util.module_from_spec(spec)
spec.loader.exec_module(versand)


def _lese_csv(pfad: Path) -> list[dict]:
    return list(csv.DictReader(pfad.read_text(encoding="utf-8-sig").splitlines(), delimiter=";"))


class CsvFormelschutzTest(unittest.TestCase):
    """Gescrapte Werte dürfen in Excel/Sheets keine Formel starten; Zahlen/Telefone bleiben lesbar."""

    def test_gleich_und_at_werden_neutralisiert(self):
        for roh, erwartet in (("=1+1", "'=1+1"), ("@SUM(A1)", "'@SUM(A1)")):
            with self.subTest(roh=roh):
                self.assertEqual(versand.csv_zelle(roh), erwartet)

    def test_tab_und_cr_werden_neutralisiert(self):
        for roh in ("\t=1", "\r=1"):
            with self.subTest(roh=roh):
                self.assertEqual(versand.csv_zelle(roh), "'" + roh)

    def test_plus_minus_ausser_zahl_telefon_werden_neutralisiert(self):
        for roh in ("-2+3", "+cmd|' /C calc'!A0"):
            with self.subTest(roh=roh):
                self.assertEqual(versand.csv_zelle(roh), "'" + roh)

    def test_zahl_und_telefon_bleiben(self):
        for roh in ("+49 171 1234567", "-12,5", "+41 (0)44 123 45 67", "-3.2"):
            with self.subTest(roh=roh):
                self.assertEqual(versand.csv_zelle(roh), roh)

    def test_harmlose_werte_bleiben(self):
        for roh in ("Müller GmbH", "https://example.com", ""):
            with self.subTest(roh=roh):
                self.assertEqual(versand.csv_zelle(roh), roh)
        self.assertEqual(versand.csv_zelle(None), "")

    def test_links_neutralisiert_formel_telefon_bleibt(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            export = tmp / "1_zielgruppe.csv"
            with export.open("w", encoding="utf-8-sig", newline="") as f:
                w = csv.writer(f, delimiter=";")
                w.writerow(["Firmenname", "Telefon", "Externe ID"])
                w.writerow(["=SUMME(1)", "+49 151 12345678", "ChIJ1"])
            (tmp / "ergebnis.json").write_text(json.dumps({"seiten": [
                {"externe_id": "ChIJ1", "link": "https://angebot.kunde.example/a1",
                 "vorschaubild": "/assets/video-vorschau.svg"}]}), encoding="utf-8")
            with redirect_stdout(io.StringIO()):
                versand.cmd_links(argparse.Namespace(csv=str(export), ergebnis=str(tmp / "ergebnis.json"),
                                                     aus=None))
            (zeile,) = _lese_csv(tmp / "1_zielgruppe_mit_landingpage.csv")
            self.assertEqual(zeile["Firmenname"], "'=SUMME(1)")
            self.assertEqual(zeile["Telefon"], "+49 151 12345678")
            self.assertEqual(zeile["Landingpage"], "https://angebot.kunde.example/a1")

    def test_loeschungen_neutralisiert_formel(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            (tmp / "w.jsonl").write_text(
                json.dumps({"zeit": "2026-10-24T10:00:00+00:00", "seiten_id": "x",
                            "externe_id": "ChIJ1"}) + "\n", encoding="utf-8")
            (tmp / "l.json").write_text(json.dumps([
                {"externe_id": "ChIJ1", "firma": "=SUMME(1)", "domain": "alpha.example",
                 "email": "anna@alpha.example"}]), encoding="utf-8")
            with redirect_stdout(io.StringIO()):
                versand.cmd_loeschungen(argparse.Namespace(datei=str(tmp / "w.jsonl"),
                                                           leads=str(tmp / "l.json"), aus=None))
            (zeile,) = _lese_csv(tmp / "datenloeschungen.csv")
            self.assertEqual(zeile["Firmenname"], "'=SUMME(1)")
            self.assertEqual(zeile["E-Mail"], "anna@alpha.example")


if __name__ == "__main__":
    unittest.main()
