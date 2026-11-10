"""Offline tests for the provenance columns and `export --lead-format`.

Run from pfade/google-maps:  python3 -m unittest discover -s tests -v
No network: the community blocklist and the own blocklist are stubbed.
"""
from __future__ import annotations

import csv
import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scraper import db, export  # noqa: E402
from scraper.blockliste import Blockliste  # noqa: E402
from scraper.sperrliste import Sperrliste  # noqa: E402

# The contract for the landing pages — spelled out here on purpose, not imported
FELDER = [
    "externe_id", "firma", "rechtsform", "domain", "website", "strasse", "plz", "ort", "land",
    "telefon", "branche", "mitarbeiter", "handelsregister", "anrede", "vorname", "nachname",
    "position", "email", "email_typ", "email_status", "kontakt_telefon", "linkedin_url",
    "quelle", "quelle_url", "erfasst_am", "personalisierung", "video_titel",
]

LEADS = [
    {   # list 1: managing director address
        "business_id": "biz-alpha", "place_id": "ChIJalpha",
        "firmenname": "Alpha Ingenieure", "firmenname_final": "Alpha Ingenieure GmbH",
        "website_final": "https://www.alpha-ing.de/kontakt", "zip": "80331",
        "address": "Maps-Weg 9, 80331 München", "adresse_impressum": "Alpha GmbH, Hauptstr. 1, 80331 München",
        "telefon_impressum": "+49 89 123", "phone_imported": "+49 89 999", "category": "Ingenieurbüro",
        "query_keyword": "Ingenieurbüro", "query_city": "München", "query_country": "DE",
        "impressum_raw": json.dumps({"impressum_url": "https://www.alpha-ing.de/impressum",
                                     "handelsregister_court": "Amtsgericht München",
                                     "handelsregister_number": "HRB 12345"}),
        "email_final": "max.muster@alpha-ing.de", "email_final_type": "GF",
        "email_final_status": "Safe to Send", "anrede": "Herr", "first_name": "Max",
        "last_name": "Muster", "linkedin_url": "https://www.linkedin.com/in/max-muster",
        "personalisierung": "Ihr Brückenprojekt in Freising ist mir aufgefallen.",
        "video_title": "Max, kurz zu Alpha", "created_at": "2026-10-17 11:22:23",
        "updated_at": "2026-10-20 08:15:00",
    },
    {   # list 2: info@ address, no Maps ids -> fallback ds-<id>
        "business_id": None, "place_id": None,
        "firmenname": "Beta Planung", "firmenname_final": "Beta Planung OG",
        "website_final": "http://beta-planung.at", "zip": "1010", "address": "",
        "adresse_impressum": "", "telefon_impressum": "", "phone_imported": "+43 1 555",
        "category": "Planungsbüro", "query_keyword": "Planungsbüro", "query_city": "Wien",
        "query_country": "AT", "impressum_raw": "{}", "email_final": "info@beta-planung.at",
        "email_final_type": "Info@", "email_final_status": "Risky", "anrede": "",
        "first_name": "", "last_name": "", "linkedin_url": None, "personalisierung": "",
        "video_title": "Kurz zu Beta", "created_at": "2026-10-18 09:00:00", "updated_at": None,
    },
    {   # list 1 candidate, but on the community blocklist -> list 5 only
        "business_id": "biz-gesperrt", "place_id": "ChIJgesperrt",
        "firmenname": "Gesperrt", "firmenname_final": "Gesperrt GmbH",
        "website_final": "https://gesperrt.de", "zip": "10115", "query_keyword": "Ingenieurbüro",
        "query_city": "Berlin", "query_country": "DE", "email_final": "chef@gesperrt.de",
        "email_final_type": "GF", "email_final_status": "Safe to Send", "anrede": "Frau",
        "first_name": "Erika", "last_name": "Beispiel", "created_at": "2026-10-17 10:00:00",
    },
]


def _lies_csv(pfad: Path) -> list[dict[str, str]]:
    with pfad.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh, delimiter=";"))


class LeadFormatTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        tmp = Path(self.tmp.name)
        self.export_dir = tmp / "exports"
        self.conn = sqlite3.connect(tmp / "leads.db")
        self.conn.row_factory = sqlite3.Row
        db.init(self.conn)
        self.ds_ids = []
        for lead in LEADS:
            cur = self.conn.execute(
                "INSERT INTO datensaetze (business_id, place_id, firmenname) VALUES (?, ?, ?)",
                (lead.get("business_id"), lead.get("place_id"), lead["firmenname"]))
            self.ds_ids.append(cur.lastrowid)
            daten = {**lead, "datensatz_id": cur.lastrowid, "ready_to_send": 1, "bereits_exportiert": 0}
            spalten = ",".join(daten)
            self.conn.execute(f"INSERT INTO anreicherung ({spalten}) VALUES ({','.join('?' * len(daten))})",
                              list(daten.values()))
        self.conn.commit()

        sperre = Sperrliste({"gesperrt.de"}, "Test-Stub")
        self.patches = [
            mock.patch.object(export, "EXPORT_DIR", self.export_dir),
            mock.patch.object(export, "KAMPAGNE", "testkampagne"),
            mock.patch.object(export.sperrliste_mod, "laden", return_value=sperre),
            mock.patch.object(export.blockliste_mod, "laden", return_value=Blockliste(set(), set())),
        ]
        for p in self.patches:
            p.start()

    def tearDown(self) -> None:
        for p in self.patches:
            p.stop()
        self.conn.close()
        self.tmp.cleanup()

    def _export(self, **kwargs) -> dict[str, tuple[Path, int]]:
        ergebnis = export.export_listen(self.conn, **kwargs)
        return {bezeichnung: (pfad, anzahl) for bezeichnung, pfad, anzahl in ergebnis}

    def _datei(self, muster: str) -> Path:
        treffer = sorted(self.export_dir.glob(muster))
        self.assertEqual(len(treffer), 1, f"{muster}: {treffer}")
        return treffer[0]

    def test_csv_listen_haben_herkunftsspalten(self) -> None:
        self._export()
        liste1 = _lies_csv(self._datei("1_zielgruppe_geschaeftsfuehrer_*.csv"))
        liste2 = _lies_csv(self._datei("2_zielgruppe_info_*.csv"))
        for spalte in ("Externe ID", "Quelle URL", "Erfasst am"):
            self.assertIn(spalte, liste1[0])
            self.assertIn(spalte, liste2[0])

        self.assertEqual([r["Firmenname"] for r in liste1], ["Alpha Ingenieure GmbH"])
        alpha = liste1[0]
        self.assertEqual(alpha["Externe ID"], "biz-alpha")
        self.assertEqual(alpha["Quelle URL"], "https://www.alpha-ing.de/impressum")
        self.assertEqual(alpha["Erfasst am"], "2026-10-20")

        beta = liste2[0]
        self.assertEqual(beta["Externe ID"], f"ds-{self.ds_ids[1]}")
        self.assertEqual(beta["Quelle URL"], "")
        self.assertEqual(beta["Erfasst am"], "2026-10-18")   # fallback created_at

        gesperrt = _lies_csv(self._datei("5_gesperrt_sperrliste_*.csv"))
        self.assertEqual([r["Firmenname"] for r in gesperrt], ["Gesperrt"])

    def test_ohne_schalter_kein_lead_format(self) -> None:
        self._export()
        self.assertEqual(list(self.export_dir.glob("leads_testkampagne_*.json")), [])

    def test_lead_format_json(self) -> None:
        ergebnis = self._export(lead_format=True)
        pfad = self._datei("leads_testkampagne_*.json")
        self.assertEqual(ergebnis["Lead-Format (JSON, Listen 1 + 2)"], (pfad, 2))

        leads = json.loads(pfad.read_text(encoding="utf-8"))
        self.assertIsInstance(leads, list)
        self.assertEqual(len(leads), 2)
        for lead in leads:
            self.assertEqual(list(lead), FELDER)
            self.assertTrue(all(isinstance(v, str) for v in lead.values()), lead)

        ids = [l["externe_id"] for l in leads]
        self.assertNotIn("biz-gesperrt", ids)
        self.assertFalse(any("gesperrt" in l["email"] or "gesperrt" in l["domain"] for l in leads))

        alpha, beta = leads
        self.assertEqual(alpha, {
            "externe_id": "biz-alpha",
            "firma": "Alpha Ingenieure GmbH",
            "rechtsform": "",
            "domain": "alpha-ing.de",
            "website": "https://www.alpha-ing.de/kontakt",
            "strasse": "Hauptstr. 1",
            "plz": "80331",
            "ort": "München",
            "land": "DE",
            "telefon": "+49 89 123",
            "branche": "Ingenieurbüro",
            "mitarbeiter": "",
            "handelsregister": "Amtsgericht München HRB 12345",
            "anrede": "Herr",
            "vorname": "Max",
            "nachname": "Muster",
            "position": "Geschäftsführung",
            "email": "max.muster@alpha-ing.de",
            "email_typ": "persoenlich",
            "email_status": "Safe to Send",
            "kontakt_telefon": "",
            "linkedin_url": "https://www.linkedin.com/in/max-muster",
            "quelle": "Google-Maps-Suche nach „Ingenieurbüro“ in München; Kontaktdaten aus dem Impressum",
            "quelle_url": "https://www.alpha-ing.de/impressum",
            "erfasst_am": "2026-10-20",
            "personalisierung": "Ihr Brückenprojekt in Freising ist mir aufgefallen.",
            "video_titel": "Max, kurz zu Alpha",
        })

        self.assertEqual(beta["externe_id"], f"ds-{self.ds_ids[1]}")
        self.assertEqual(beta["domain"], "beta-planung.at")
        self.assertEqual(beta["telefon"], "+43 1 555")      # fallback phone_imported
        self.assertEqual(beta["position"], "")
        self.assertEqual(beta["email_typ"], "funktion")
        self.assertEqual(beta["quelle_url"], "")
        self.assertEqual(beta["strasse"], "")
        self.assertEqual(beta["handelsregister"], "")
        self.assertEqual(beta["linkedin_url"], "")
        self.assertEqual(beta["erfasst_am"], "2026-10-18")
        self.assertEqual(beta["quelle"], "Google-Maps-Suche nach „Planungsbüro“ in Wien")


class QuelleTest(unittest.TestCase):
    """quelle_url / quelle: imprint URL first, Google Maps entry as fallback."""

    BASIS = {"place_id": "ChIJmaps", "query_keyword": "Statiker", "query_city": "Graz"}

    def test_mit_impressum_url(self) -> None:
        row = {**self.BASIS, "impressum_raw": json.dumps({"impressum_url": "https://statik.at/impressum"})}
        self.assertEqual(export.quelle_url(row), "https://statik.at/impressum")
        self.assertEqual(export.quelle(row),
                         "Google-Maps-Suche nach „Statiker“ in Graz; Kontaktdaten aus dem Impressum")
        self.assertEqual(export.lead_format_eintrag(row)["quelle_url"], "https://statik.at/impressum")

    def test_ohne_impressum_url(self) -> None:
        for raw in (None, "{}", json.dumps({"impressum_url": ""}), "kein json"):
            row = {**self.BASIS, "impressum_raw": raw}
            self.assertEqual(export.quelle_url(row), "https://www.google.com/maps/place/?q=place_id:ChIJmaps")
            self.assertEqual(export.quelle(row), "Google-Maps-Suche nach „Statiker“ in Graz")


class UpdatedAtTest(unittest.TestCase):
    """db.update stamps anreicherung.updated_at; erfasst_am follows it."""

    def setUp(self) -> None:
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        db.init(self.conn)
        ds = self.conn.execute("INSERT INTO datensaetze (business_id) VALUES ('biz-1')").lastrowid
        self.ds = ds
        self.an = self.conn.execute(
            "INSERT INTO anreicherung (datensatz_id, created_at, updated_at) "
            "VALUES (?, '2020-01-01 00:00:00', '2020-01-01 00:00:00')", (ds,)).lastrowid
        self.conn.commit()

    def tearDown(self) -> None:
        self.conn.close()

    def _row(self):
        return self.conn.execute("SELECT * FROM anreicherung WHERE id=?", (self.an,)).fetchone()

    def test_update_setzt_updated_at(self) -> None:
        heute = self.conn.execute("SELECT date('now')").fetchone()[0]
        self.assertEqual(export.erfasst_am(self._row()), "2020-01-01")
        db.update(self.conn, "anreicherung", self.an, {"telefon_impressum": "+49 1"})
        row = self._row()
        self.assertEqual(row["telefon_impressum"], "+49 1")
        self.assertEqual(row["created_at"], "2020-01-01 00:00:00")
        self.assertEqual(row["updated_at"][:10], heute)
        self.assertEqual(export.erfasst_am(row), heute)

    def test_explizites_updated_at_bleibt(self) -> None:
        db.update(self.conn, "anreicherung", self.an, {"updated_at": "2021-05-05 10:00:00"})
        self.assertEqual(self._row()["updated_at"], "2021-05-05 10:00:00")

    def test_andere_tabellen_unveraendert(self) -> None:
        # datensaetze has no updated_at column — update must still work
        db.update(self.conn, "datensaetze", self.ds, {"firmenname": "Neu"})
        name = self.conn.execute("SELECT firmenname FROM datensaetze WHERE id=?", (self.ds,)).fetchone()[0]
        self.assertEqual(name, "Neu")


if __name__ == "__main__":
    unittest.main()
