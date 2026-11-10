"""Offline-Tests für sperrliste_abgleich.py — ganz ohne Netz.

    python3 -m unittest test_sperrliste_abgleich -v   (aus lead-scraper/werkzeuge/)
"""
import csv
import importlib.util
import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

spec = importlib.util.spec_from_file_location(
    "sperrliste_abgleich", Path(__file__).resolve().parent / "sperrliste_abgleich.py")
abgleich = importlib.util.module_from_spec(spec)
spec.loader.exec_module(abgleich)


class CsvFormelschutzTest(unittest.TestCase):
    """Gescrapte Werte dürfen in Excel/Sheets keine Formel starten; Zahlen/Telefone bleiben lesbar."""

    def test_gleich_und_at_werden_neutralisiert(self):
        for roh, erwartet in (("=1+1", "'=1+1"), ("@SUM(A1)", "'@SUM(A1)")):
            with self.subTest(roh=roh):
                self.assertEqual(abgleich.csv_zelle(roh), erwartet)

    def test_tab_und_cr_werden_neutralisiert(self):
        for roh in ("\t=1", "\r=1"):
            with self.subTest(roh=roh):
                self.assertEqual(abgleich.csv_zelle(roh), "'" + roh)

    def test_plus_minus_ausser_zahl_telefon_werden_neutralisiert(self):
        for roh in ("-2+3", "+cmd|' /C calc'!A0"):
            with self.subTest(roh=roh):
                self.assertEqual(abgleich.csv_zelle(roh), "'" + roh)

    def test_zahl_und_telefon_bleiben(self):
        for roh in ("+49 171 1234567", "-12,5", "+41 (0)44 123 45 67", "-3.2"):
            with self.subTest(roh=roh):
                self.assertEqual(abgleich.csv_zelle(roh), roh)

    def test_harmlose_werte_bleiben(self):
        for roh in ("Müller GmbH", "https://example.com", ""):
            with self.subTest(roh=roh):
                self.assertEqual(abgleich.csv_zelle(roh), roh)
        self.assertEqual(abgleich.csv_zelle(None), "")

    def test_bereinigt_neutralisiert_formel_telefon_bleibt(self):
        with tempfile.TemporaryDirectory() as tmp:
            liste = Path(tmp) / "liste.csv"
            with liste.open("w", encoding="utf-8", newline="") as f:
                w = csv.writer(f, delimiter=";")
                w.writerow(["Firmenname", "Telefon", "Website"])
                w.writerow(["=SUMME(1)", "+49 151 12345678", "https://example.com"])
            argv = ["sperrliste_abgleich.py", str(liste)]
            with mock.patch("sys.argv", argv), \
                    mock.patch.object(abgleich, "lade", return_value=(set(), "test")), \
                    redirect_stdout(io.StringIO()):
                self.assertEqual(abgleich.main(), 0)
            with (Path(tmp) / "liste_bereinigt.csv").open(encoding="utf-8-sig", newline="") as f:
                r = csv.DictReader(f, delimiter=";")
                self.assertEqual(r.fieldnames, ["Firmenname", "Telefon", "Website"])
                (zeile,) = list(r)
            self.assertEqual(zeile["Firmenname"], "'=SUMME(1)")
            self.assertEqual(zeile["Telefon"], "+49 151 12345678")
            self.assertEqual(zeile["Website"], "https://example.com")


if __name__ == "__main__":
    unittest.main()
