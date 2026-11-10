"""Offline-Tests für KT-05: Platzhalter-Abbruch und Exit-Code bei Totalausfall.

    python3 -m unittest discover -s tests -v      (aus pfade/google-maps/)
"""
from __future__ import annotations

import contextlib
import csv
import io
import logging
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

TMP = tempfile.mkdtemp()
# Echte .env-Werte dürfen die Tests nicht kippen, Sperrliste ohne Download.
# Bewusst keine toten *_BASE_URL: Die Tests ersetzen den Skael-Client ganz und
# mocken den Listenabruf – tote Adressen würden nur CONFIG für später
# importierte Testmodule vergiften (deren Attrappen prüfen den echten Host).
os.environ.update({
    "DB_PATH": str(Path(TMP) / "test.db"),
    "SPERRLISTE_PFLICHT": "false",
    "SPERRLISTE_URL": "https://example.invalid/OWNER-liste.txt",
    "SKAEL_API_KEY": "", "OPENAI_API_KEY": "", "FINDYMAIL_API_KEY": "",
    "MAX_RETRIES": "1", "KAMPAGNE": "",
})
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scraper import cli, db, pipeline  # noqa: E402
from scraper import export as export_mod  # noqa: E402
from scraper.blockliste import Blockliste  # noqa: E402
from scraper.clients import ApiError  # noqa: E402
from scraper.config import CONFIG  # noqa: E402
from scraper.sperrliste import Sperrliste  # noqa: E402


def _cli(*argv: str) -> tuple[int, str, str]:
    """CLI aufrufen, Ausgabe einsammeln. Exit-Code 0 = durchgelaufen."""
    out, err = io.StringIO(), io.StringIO()
    root = logging.getLogger()
    handler, level = list(root.handlers), root.level
    code = 0
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            cli.main(list(argv))
    except SystemExit as exc:
        code = exc.code if isinstance(exc.code, int) else 1
        if not isinstance(exc.code, int):
            err.write(str(exc.code))
    finally:
        root.handlers, root.level = handler, level
    return code, out.getvalue(), err.getvalue()


@contextlib.contextmanager
def _einstellung(**werte):
    """CONFIG-Felder für die Dauer eines Tests ändern."""
    alt = {k: getattr(CONFIG, k) for k in werte}
    for k, v in werte.items():
        setattr(CONFIG, k, v)
    try:
        yield
    finally:
        for k, v in alt.items():
            setattr(CONFIG, k, v)


@contextlib.contextmanager
def _skael_im_cli(klasse):
    """`run` baut seinen Skael-Client selbst – hier durch eine Attrappe ersetzen."""
    original = cli.SkaelClient
    cli.SkaelClient = klasse
    try:
        yield
    finally:
        cli.SkaelClient = original


class SkaelGestoert:
    """Anbieter gestört: jede Abfrage scheitert, ohne Netz."""

    calls: list = []

    def find_cities(self, country_code, min_population, limit=None):
        SkaelGestoert.calls.append((country_code, min_population))
        raise ApiError("find_cities: HTTP 0 nach 1 Versuchen")


class SkaelLeer:
    """Anbieter ok, aber keine Städte – Lauf läuft durch, nichts zu tun danach."""

    def find_cities(self, country_code, min_population, limit=None):
        return {"cities": [], "total": 0}


class PlatzhalterUndExitCodeTest(unittest.TestCase):
    """Platzhalter aus .env.example startet keinen Lauf; Totalausfall gibt Exit 1."""

    def setUp(self):
        self.original_db = CONFIG.db_path
        self.original_url = CONFIG.sperrliste_url
        CONFIG.db_path = Path(TMP) / f"{self._testMethodName}.db"
        # CONFIG kann schon von einem anderen Testmodul geladen sein – hermetisch setzen
        CONFIG.sperrliste_url = "https://example.invalid/OWNER-liste.txt"
        pipeline.BILANZ.clear()
        self.conn = db.connect()
        db.init(self.conn)
        for keyword, country in (("Metallbau", "DE"), ("Schlosserei", "AT")):
            db.upsert(self.conn, "eingabe", {
                "keyword": keyword, "country_code": country, "min_population": 1,
            }, conflict=("keyword", "country_code", "min_population"))
        SkaelGestoert.calls = []

    def tearDown(self):
        self.conn.close()
        CONFIG.db_path = self.original_db
        CONFIG.sperrliste_url = self.original_url

    def test_platzhalter_bricht_vor_dem_lauf_mit_exit_2_ab(self):
        with _einstellung(skael_api_key="eak_dein_key_hier"), _skael_im_cli(SkaelGestoert):
            err_getrennt = io.StringIO()
            with contextlib.redirect_stderr(err_getrennt):
                with self.assertRaises(SystemExit) as ctx:
                    CONFIG.require("skael_api_key")
            self.assertEqual(ctx.exception.code, 2)
            self.assertIn("SKAEL_API_KEY", err_getrennt.getvalue())
            self.assertNotIn("eak_dein_key_hier", err_getrennt.getvalue())
            code, _, err = _cli("run", "--stage", "1")
        self.assertEqual(code, 2)
        self.assertIn("SKAEL_API_KEY", err)
        self.assertNotIn("eak_dein_key_hier", err)
        self.assertEqual(SkaelGestoert.calls, [])   # abgebrochen, bevor etwas abgefragt wurde

    def test_echter_wert_startet_den_lauf(self):
        with _einstellung(skael_api_key="eak_test123"), _skael_im_cli(SkaelLeer):
            code, _, err = _cli("run", "--stage", "1")
        self.assertEqual(code, 0, err)
        done = self.conn.execute("SELECT COUNT(*) FROM eingabe WHERE status='done'").fetchone()[0]
        self.assertEqual(done, 2)

    def test_alle_kombinationen_fehlgeschlagen_gibt_exit_1(self):
        with _einstellung(skael_api_key="eak_test123"), _skael_im_cli(SkaelGestoert):
            code, _, err = _cli("run", "--stage", "1")
        self.assertEqual(code, 1)
        self.assertIn("alle 2 Zeilen fehlgeschlagen", err)
        self.assertEqual(len(SkaelGestoert.calls), 2)


class CsvFormelschutzTest(unittest.TestCase):
    """Gescrapte Werte dürfen in Excel/Sheets keine Formel starten; Zahlen/Telefone bleiben lesbar."""

    def test_gleich_und_at_werden_neutralisiert(self):
        for roh, erwartet in (("=1+1", "'=1+1"), ("@SUM(A1)", "'@SUM(A1)")):
            with self.subTest(roh=roh):
                self.assertEqual(export_mod.csv_zelle(roh), erwartet)

    def test_tab_und_cr_werden_neutralisiert(self):
        for roh in ("\t=1", "\r=1"):
            with self.subTest(roh=roh):
                self.assertEqual(export_mod.csv_zelle(roh), "'" + roh)

    def test_plus_minus_ausser_zahl_telefon_werden_neutralisiert(self):
        for roh in ("-2+3", "+cmd|' /C calc'!A0"):
            with self.subTest(roh=roh):
                self.assertEqual(export_mod.csv_zelle(roh), "'" + roh)

    def test_zahl_und_telefon_bleiben(self):
        for roh in ("+49 171 1234567", "-12,5", "+41 (0)44 123 45 67", "-3.2"):
            with self.subTest(roh=roh):
                self.assertEqual(export_mod.csv_zelle(roh), roh)

    def test_harmlose_werte_bleiben(self):
        for roh in ("Müller GmbH", "https://example.com", ""):
            with self.subTest(roh=roh):
                self.assertEqual(export_mod.csv_zelle(roh), roh)
        self.assertEqual(export_mod.csv_zelle(None), "")

    def test_export_neutralisiert_formel_im_firmennamen(self):
        original_db, original_export = CONFIG.db_path, export_mod.EXPORT_DIR
        ordner = Path(tempfile.mkdtemp(dir=TMP))
        CONFIG.db_path, export_mod.EXPORT_DIR = ordner / "test.db", ordner / "exports"
        try:
            conn = db.connect()
            db.init(conn)
            formel = "=SUMME(1)"
            telefon = "+49 151 12345678"
            conn.execute("INSERT INTO datensaetze (business_id, firmenname) VALUES ('formel-1', 'Formel')")
            ds_id = conn.execute("SELECT id FROM datensaetze").fetchone()[0]
            conn.execute("INSERT INTO anreicherung (datensatz_id, firmenname_final, email_final_type,"
                         " telefon_impressum, ready_to_send) VALUES (?, ?, 'GF', ?, 1)",
                         (ds_id, formel, telefon))
            conn.commit()
            with mock.patch.object(export_mod.sperrliste_mod, "laden", return_value=Sperrliste(set(), "test")), \
                    mock.patch.object(export_mod.blockliste_mod, "laden",
                                      return_value=Blockliste(set(), set())):
                pfad = next(p for name, p, _ in export_mod.export_listen(conn)
                            if name.startswith("Zielgruppe · Geschäftsführer"))
            with pfad.open(encoding="utf-8-sig", newline="") as fh:
                (zeile,) = list(csv.DictReader(fh, delimiter=";"))
            self.assertEqual(zeile["Firmenname"], "'" + formel)
            self.assertEqual(zeile["Telefon (Impressum)"], telefon)
            conn.close()
        finally:
            CONFIG.db_path, export_mod.EXPORT_DIR = original_db, original_export


if __name__ == "__main__":
    unittest.main()
