"""Offline-Tests für KT-05: Platzhalter-Abbruch und Exit-Code bei Totalausfall.

    python3 -m unittest discover -s tests -v      (aus pfade/google-maps/)
"""
from __future__ import annotations

import contextlib
import io
import logging
import os
import sys
import tempfile
import unittest
from pathlib import Path

TMP = tempfile.mkdtemp()
# Wie im E-Commerce-Test: echte .env-Werte dürfen die Tests nicht kippen,
# Dienste auf einer toten lokalen Adresse: kein Aufruf kostet etwas.
os.environ.update({
    "DB_PATH": str(Path(TMP) / "test.db"),
    "SPERRLISTE_PFLICHT": "false",
    "SPERRLISTE_URL": "https://example.invalid/OWNER-liste.txt",
    "SKAEL_API_KEY": "", "OPENAI_API_KEY": "", "FINDYMAIL_API_KEY": "",
    "SKAEL_BASE_URL": "http://127.0.0.1:9", "OPENAI_BASE_URL": "http://127.0.0.1:9",
    "MAX_RETRIES": "1",
})
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scraper import cli, db  # noqa: E402
from scraper.clients import ApiError  # noqa: E402
from scraper.config import CONFIG  # noqa: E402


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
        CONFIG.db_path = Path(TMP) / f"{self._testMethodName}.db"
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


if __name__ == "__main__":
    unittest.main()
