"""Offline tests for the Findymail client and its place in stage 4c.

Run from pfade/google-maps:  python3 -m unittest discover -s tests -v
Responses follow https://app.findymail.com/docs; no network.
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scraper import clients, db, pipeline  # noqa: E402
from scraper.clients import ApiError, FindymailClient  # noqa: E402
from scraper.config import CONFIG  # noqa: E402


class FindymailClientTest(unittest.TestCase):
    def setUp(self):
        self.original = clients._request
        self.gesendet: list[tuple[str, dict | None]] = []

    def tearDown(self):
        clients._request = self.original

    def _antwort(self, status, data):
        def fake(url, *, method="POST", headers=None, body=None, timeout=None):
            self.gesendet.append((url, body))
            return status, data
        clients._request = fake

    def test_treffer_und_domain_statt_url(self):
        self._antwort(200, {"contact": {"name": "Max Mueller", "domain": "firma.de", "email": "max@firma.de"}})
        out = FindymailClient(api_key="k").find_work_email("Max Mueller", "https://www.firma.de/impressum")
        self.assertEqual(out["email"], "max@firma.de")
        self.assertEqual(self.gesendet[0][1], {"name": "Max Mueller", "domain": "firma.de"})

    def test_nichts_gefunden(self):
        self._antwort(404, {"error": "Not found"})
        self.assertIsNone(FindymailClient(api_key="k").find_work_email("Max Mueller", "firma.de")["email"])

    def test_leeres_guthaben_ist_ein_fehler(self):
        self._antwort(402, {"error": "Not enough credits"})
        with self.assertRaises(ApiError):
            FindymailClient(api_key="k").find_work_email("Max Mueller", "firma.de")

    def test_restguthaben(self):
        self._antwort(200, {"credits": 150, "verifier_credits": 100})
        self.assertEqual(FindymailClient(api_key="k").credits()["credits"], 150)


class SkaelOhneTreffer:
    def find_email_person(self, website, name):
        return {"email": None}

    def verify_email(self, email):
        return {"email": email, "status": "valid", "result": "deliverable"}


class FindymailOhneGuthaben:
    api_key = "k"

    def find_work_email(self, full_name, company_domain):
        raise ApiError("Findymail HTTP 402: Not enough credits", 402)


class Stufe4cTest(unittest.TestCase):
    """Empty Findymail credit must leave the lead open instead of closing it without an address."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.original = (CONFIG.db_path, CONFIG.use_findymail)
        CONFIG.db_path = Path(self.tmp.name) / "leads.db"
        CONFIG.use_findymail = True
        self.conn = db.connect()
        db.init(self.conn)
        self.conn.execute("PRAGMA foreign_keys=OFF")  # no stage-3 record needed for this test
        self.conn.execute(
            "INSERT INTO anreicherung (datensatz_id, firmenname, website_final, kontaktperson_sauber, launch_campaign) "
            "VALUES (1, 'Firma A', 'https://www.firma-a.de', 'Max Mueller', 1)")
        self.conn.commit()

    def tearDown(self):
        self.conn.close()
        CONFIG.db_path, CONFIG.use_findymail = self.original
        self.tmp.cleanup()

    def test_leeres_guthaben_laesst_lead_offen(self):
        pipeline.stufe4c_emails(self.conn, SkaelOhneTreffer(), FindymailOhneGuthaben())
        lead = self.conn.execute("SELECT * FROM anreicherung").fetchone()
        self.assertIsNone(lead["email_final"])
        self.assertIn("Findymail", lead["error"])


if __name__ == "__main__":
    unittest.main()
