"""Offline end-to-end tests for the campaign types google-maps, recruiting and stellensuche (no API keys, no costs).

Every external call (Skael, OpenAI) is answered by `FakeApi` with realistic
payloads. The tests drive the real CLI, pipeline, database and export.

    cd pfade/google-maps && python3 -m unittest discover -s tests -v
"""
from __future__ import annotations

import contextlib
import csv
import io
import json
import os
import sqlite3
import tempfile
import threading
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest import mock

# Settings must be in place before the package reads its configuration
os.environ.update({
    "SKAEL_API_KEY": "eak_test", "OPENAI_API_KEY": "sk-test",
    "FINDYMAIL_API_KEY": "", "SPERRLISTE_PFLICHT": "false", "MAX_CONCURRENCY": "2",
    "SKAEL_RATE_LIMIT_PER_SEC": "1000", "OPENAI_RATE_LIMIT_PER_SEC": "1000", "MAX_RETRIES": "1",
    # the fake answers the OpenAI endpoint; Skael chat (LLM_PROVIDER=skael) is covered elsewhere
    "LLM_PROVIDER": "openai", "DOMAINSUCHE": "aus", "KAMPAGNE": "",
})

from scraper import blockliste, cli, export, llm, sperrliste, stellen as S, transforms as T  # noqa: E402
from scraper.config import CONFIG, PROMPTS_DIR  # noqa: E402

# Campaign prompts the repo keeps per campaign (kampagnen/<name>/prompts/) — minimal stand-ins
TEST_PROMPTS = {
    "personalisierung.txt": "Satz zur Firma {{Firmenname}}: {{Webseiteninhalt}}",
    "pain_kategorie.txt": "Einordnung: {{Webseiteninhalt}}",
    "pain_kategorie.schema.json": (PROMPTS_DIR / "beispiele" / "pain_kategorie_grosshandel.schema.json").read_text(),
}

# ---------------------------------------------------------------- fake data

MAPS_ITEMS = [
    {"name": "Alpha Spedition GmbH", "website": "https://alpha-spedition.de", "business_id": "b1",
     "type": "Spedition", "full_address": "Hafenstr. 1, 89073 Ulm", "zip_code": "89073",
     "phone_numbers": ["+49 731 1"], "rating": 4.6, "review_count": 40},
    {"name": "Beta Logistik GmbH", "website": "https://beta-logistik.de", "business_id": "b2",
     "type": "Logistikunternehmen", "phone_numbers": []},
    {"name": "Café Central", "website": "https://cafe-central.de", "business_id": "b3", "type": "Café"},
    {"name": "Alpha Spedition Standort Ulm", "website": "https://www.alpha-spedition.de/standort-ulm",
     "business_id": "b4", "type": "Spedition"},
]

PAGES = {
    "https://alpha-spedition.de": {
        "final_url": "https://alpha-spedition.de/",
        "body_text": "Alpha Spedition – Nah- und Fernverkehr, eigener Fuhrpark mit 40 LKW.",
        "links": ["https://alpha-spedition.de/leistungen", "https://alpha-spedition.de/karriere",
                  "https://facebook.com/alpha"]},
    "https://alpha-spedition.de/karriere": {
        "final_url": "https://alpha-spedition.de/karriere",
        "body_text": "Wir suchen Berufskraftfahrer (m/w/d) CE im Fernverkehr. Führerschein CE, ADR von Vorteil.",
        "links": []},
    "https://beta-logistik.de": {
        "final_url": "https://beta-logistik.de/",
        "body_text": "Beta Logistik – Kontraktlogistik und Lagerlogistik auf 20.000 m².",
        "links": ["https://beta-logistik.de/kontakt"]},
    "https://shop-eins.de": {"final_url": "https://shop-eins.de/", "body_text": "Neu im Sortiment – In den Warenkorb – Kasse – Versand ab 49 €", "links": []},
    "https://shop-zwei.de": {"final_url": "https://shop-zwei.de/", "body_text": "Handgemachte Seifen – In den Warenkorb – Kasse", "links": []},
    "https://agentur-drei.de": {"final_url": "https://agentur-drei.de/", "body_text": "Wir beraten Unternehmen. Kontakt aufnehmen.", "links": []},
}

TRAFFIC = {
    "shop-eins.de": {"estimated_monthly_visits": {"2026-07": 12000, "2026-08": 15001, "2026-09": 9000}},
    "shop-zwei.de": {"estimated_monthly_visits": {"2026-07": 100, "2026-08": 200, "2026-09": 300}},
}

GF = {"alpha-spedition.de": "Max Mustermann", "beta-logistik.de": "Kim Lee",
      "shop-eins.de": "Sabine Schulz", "shop-zwei.de": "Paul Kurz",
      "wilkes.de": "Marc Wilkes", "autohaus-staiger.de": "Peter Staiger", "os-kornwestheim.de": "Olaf Sailer"}

# --- job portals (shapes copied from real Skael answers, October 2026) ---------
def _tage(n: int) -> str:
    return (date.today() - timedelta(days=n)).isoformat()


INDEED = {"success": True, "data": {"jobs": [
    {"id": "i1", "title": "Berufskraftfahrer Stuttgart",
     "company": {"name": "Wilkes GmbH", "website": "http://www.wilkes.de"},
     "location": {"city": "Stuttgart", "postal_code": "70327", "country": "DE", "formatted": "70327 Stuttgart"},
     "salary": None, "date_published": f"{_tage(5)} 05:00:00",
     "apply_url": "https://www.wilkes.de/news/berufskraftfahrer-stuttgart",
     "description_html": "<p>Für unsere Niederlassung in <b>Stuttgart-Wangen</b> suchen wir ab sofort einen "
                         "zuverlässigen Berufskraftfahrer.</p><p><b>Ihr Profil:</b></p><ul>"
                         "<li>Führerschein Klasse C/CE mit Kennzahl 95 und gültiger Fahrerkarte</li>"
                         "<li>Bereitschaft für Mehrtagestouren mit Übernachtungen</li></ul>"
                         "<p>Bei Interesse senden Sie bitte Ihre Unterlagen an Herrn Marc Hettich "
                         "(marc.hettich@wilkes.de), Tel. 0711/707100-11</p>"},
    {"id": "i2", "title": "BERUFSKRAFTFAHRER (M/W/D) Nahverkehr",
     "company": {"name": None, "website": None}, "location": {"city": "Stuttgart", "formatted": "Stuttgart"},
     "date_published": f"{_tage(10)} 05:00:00",
     "apply_url": "https://timetrans-logistik.de/de/jobs/berufskraftfahrer-m-w-d-nahverkehr/",
     "description_html": "<ul><li>Führerschein Klasse C/CE</li><li>Erfahrung als LKW-Fahrer</li></ul>"},
    {"id": "i3", "title": "BERUFSKRAFTFAHRER (M/W/D)",
     "company": {"name": "Schrott- und Metallhandel Eberhard Mayr GmbH & Co KG"},
     "location": {"city": "Stuttgart"}, "date_published": "2023-01-19 06:00:00", "description_html": "<p>alt</p>"},
    {"id": "i4", "title": "Fahrer (m/w/d)", "company": {"name": "Tempton Personaldienstleistungen GmbH"},
     "location": {"city": "Stuttgart"}, "date_published": f"{_tage(1)} 05:00:00"},
], "pagination": {"next_cursor": None, "has_more": False}}}

STEPSTONE = {"success": True, "data": {"jobs": [
    {"id": "s1", "title": "Berufskraftfahrer (m/w/d) mit Führerschein C1E",
     "url": "https://www.stepstone.de/jobs----13816826-inline.html",
     "company": {"name": "Autohaus Staiger GmbH", "url": None}, "location": {"formatted": "Stuttgart"},
     "date_posted": f"{_tage(1)}T15:03:05+00:00", "description": None},
    {"id": "s2", "title": "Kraftfahrer (m/w/d)", "url": "https://www.stepstone.de/jobs----2-inline.html",
     "company": {"name": "Wilkes GmbH", "url": None}, "location": {"formatted": "Stuttgart"},
     "date_posted": f"{_tage(2)}T08:00:00+00:00"},
    {"id": "s3", "title": "Lastkraftfahrer (m/w/d)", "url": "https://www.stepstone.de/jobs----3-inline.html",
     "company": {"name": "O + S Offterdinger & Sailer GmbH", "url": None}, "location": {"formatted": "Kornwestheim"},
     "date_posted": f"{_tage(1)}T08:11:19+00:00"},
], "pagination": {"current_page": 1, "total_pages": 1, "has_more": False}}}

ARBEITSAGENTUR = {"success": True, "data": {"maxErgebnisse": "3", "stellenangebote": [
    {"refnr": "aa1", "titel": "Berufskraftfahrer/in (m/w/d)",
     "arbeitgeber": "Garten- und Landschaftsbau Palmer GmbH & Co. KG",
     "arbeitsort": {"plz": None, "ort": "Stuttgart"}, "aktuelleVeroeffentlichungsdatum": _tage(3)},
    {"refnr": "aa2", "titel": "Berufskraftfahrer (m/w/d)", "arbeitgeber": "STRAUSS Zeitarbeit GmbH",
     "arbeitsort": {"ort": "Stuttgart"}, "aktuelleVeroeffentlichungsdatum": _tage(3)},
    {"refnr": "aa3", "titel": "LKW-Fahrer (m/w/d)", "arbeitgeber": "Offterdinger und Sailer Kornwestheim",
     "arbeitsort": {"plz": "70806", "ort": "Kornwestheim"}, "aktuelleVeroeffentlichungsdatum": _tage(4)},
]}}

FIND_DOMAIN = {
    "Autohaus Staiger GmbH": "autohaus-staiger.de",
    "O + S Offterdinger & Sailer GmbH": "os-kornwestheim.de",
    "Offterdinger und Sailer Kornwestheim": "www.os-kornwestheim.de",
    "timetrans-logistik.de": "timetrans-logistik.de",
}


class FakeApi:
    """Stands in for scraper.clients._request and records every call."""

    def __init__(self):
        self.calls: list[str] = []
        self.bodies: list[tuple[str, dict]] = []
        self.async_results: dict[str, dict] = {}
        self.lock = threading.Lock()
        self.polled: set[str] = set()
        self.stepstone_mehr = False
        self.groesse: dict[str, tuple[str, str]] = {}   # name part → (category, headcount); default mittelstand
        self.groesse_fehler = False
        self.credits: float | None = None          # credits_cost per finished Skael job (cost ledger)
        self.synonyme = ["LKW-Fahrer", "Berufskraftfahrer"]

    def __call__(self, url, *, method="POST", headers=None, body=None, timeout=None):
        self.calls.append(url)
        self.bodies.append((url, body or {}))
        if "api.skael.de" in url and method == "GET":
            # long polling GET /api/enrichments/{id}: first answer "still processing" (real Skael shape)
            resource = url.split("/api/enrichments/", 1)[1].split("?", 1)[0]
            with self.lock:
                erster = resource not in self.polled
                self.polled.add(resource)
            if erster:
                return 200, {"id": int(resource), "status": "processing",
                             "message": "Enrichment still processing after 50 seconds. Retry this request."}
            return 200, {"data": {"status": "completed", "output": self.async_results[resource], **self._kosten()}}
        if url.endswith("/kununu_jobs"):
            return 422, {"data": {"status": "failed", "error_message": "Web scraper service kununuJobs failed: HTTP 503"}}
        if url.endswith("/find_domain"):
            with self.lock:
                resource = str(900 + len(self.async_results))
                self.async_results[resource] = self.find_domain(body or {})
            return 202, {"data": {"id": int(resource), "status": "queued"}}
        if "api.skael.de" in url:
            return 200, {"data": {"status": "completed", "output": self.skael(url, body or {}), **self._kosten()}}
        if "api.openai.com" in url:
            if self.groesse_fehler and body["response_format"]["json_schema"]["name"] == "groesse":
                return 500, {"error": {"message": "server error"}}
            return 200, {"choices": [{"message": {"content": json.dumps(self.openai(body))}}]}
        return 404, {"message": f"unexpected {url}"}

    def _kosten(self) -> dict:
        return {} if self.credits is None else {"credits_cost": self.credits}

    def skael(self, url, body):
        from urllib.parse import parse_qs, urlparse
        endpoint = urlparse(url).path.rsplit("/", 1)[-1]
        query = {k: v[0] for k, v in parse_qs(urlparse(url).query).items()}
        if endpoint == "find_cities":
            return {"total": 1, "cities": [{"name": "Ulm", "population": 126000}], "country_code": "DE"}
        if endpoint == "maps_search":
            return {"items": MAPS_ITEMS, "total": len(MAPS_ITEMS)}
        if endpoint == "icp_checker":
            ok = "cafe" not in query["url"]
            return {"icp": ok, "confidence": 0.9 if ok else 0.95, "reason": "Spedition" if ok else "Gastronomie"}
        if endpoint == "web_scraper":
            return PAGES.get(body["url"].rstrip("/"), {"final_url": body["url"], "body_text": "", "links": []})
        if endpoint == "webtraffic":
            return TRAFFIC.get(body["domain"], {})
        if endpoint == "imprint_extractor":
            name = GF.get(body["domain"], "")
            return {"firmenname": body["domain"].split(".")[0].title() + " GmbH",
                    "geschaeftsfuehrer": [name] if name else [], "email": f"info@{body['domain']}",
                    "adresse": "Musterweg 1", "telefon": "+49 1"}
        if endpoint == "find_email_person":
            first, last = body["full_name"].lower().split(" ")
            domain = T.host_of(body["domain"])
            return {"email": f"{first}.{last}@{domain}", "email_status": "valid"}
        if endpoint == "verify_email":
            return {"email": body["email"], "code": 5, "status": "valid"}
        if endpoint == "indeed_jobs":
            return INDEED
        if endpoint == "stepstone_jobs":
            if self.stepstone_mehr:
                if body.get("page", 1) == 1:
                    return {"success": True, "data": {**STEPSTONE["data"],
                                                      "pagination": {"current_page": 1, "has_more": True}}}
                return {"success": True, "data": {"jobs": [
                    {"id": "s4", "title": "Berufskraftfahrer Nahverkehr (m/w/d)", "url": "https://www.stepstone.de/jobs----4-inline.html",
                     "company": {"name": "Seite Zwei Logistik GmbH"}, "location": {"formatted": "Esslingen"},
                     "date_posted": f"{_tage(20)}T08:00:00+00:00"}],
                    "pagination": {"current_page": 2, "has_more": False}}}
            return STEPSTONE
        if endpoint == "arbeitsagentur_jobs":
            assert body["zeitarbeit"] is False and body["angebotsart"] == "1", body
            return ARBEITSAGENTUR
        raise AssertionError(f"unexpected Skael endpoint {endpoint}")

    @staticmethod
    def find_domain(body):
        domain = FIND_DOMAIN.get(body["company_name"])
        if domain:
            return {"domain": domain, "status": "verified", "verdict": "match", "confidence": 0.95}
        return {"domain": None, "status": "unverified", "best_guess": {"domain": "palmer-galabau.de",
                                                                      "verdict": "no_imprint", "confidence": 0}}

    def openai(self, body):
        name = body.get("response_format", {}).get("json_schema", {}).get("name")
        prompt = body["messages"][0]["content"]
        if name == "company_domain":
            return {"response": ""}
        if name == "anrede":
            vorname = prompt.split('(vorname: "', 1)[1].split('"', 1)[0]
            return {"anrede": "Frau" if vorname in ("Erika", "Sabine") else "Herr",
                    "confidence": 50 if vorname == "Kim" else 98}
        if name == "stellenanalyse":
            if "Berufskraftfahrer (m/w/d) CE" in prompt:
                return {"stellenGefunden": True, "anzahl": 1, "stellenangebote": [
                    {"position": "Berufskraftfahrer (m/w/d) CE", "bereich": "Fahrer/Transport",
                     "beschreibung": "Fernverkehr, Führerschein CE, ADR von Vorteil"}]}
            return {"stellenGefunden": False, "anzahl": 0, "stellenangebote": []}
        if name == "jobtitel":
            assert "Jobtitel: " in prompt and "{{" not in prompt
            titel = prompt.rsplit("Jobtitel: ", 1)[1].strip()
            return {"normalisierterTitel": "Disponenten" if "Disponent" in titel
                    else ("LKW-Fahrer" if "LKW" in titel else "Berufskraftfahrer")}
        if name == "personalisierung":
            if "ich habe gesehen, dass Sie" in prompt:
                schluessel = next(k for k in ('"job_title_normalisiert":"', '"job_title_original":"', '"job_title":"') if k in prompt)
                beruf = prompt.split(schluessel, 1)[1].split('"', 1)[0]
                return {"complimentText": f"ich habe gesehen, dass Sie {beruf} suchen, die CE-Führerschein mitbringen."}
            if "You are an experienced German copywriter" in prompt:
                return {"complimentText": "bei Ihnen wirkt es so, als ob jedes Detail durchdacht ist."}
            return {"complimentText": "wie Sie Ihr Sortiment aufstellen, fällt auf."}
        if name == "pain_kategorie":
            return {"painCategory": "Lead Gen", "partnernetzBelegt": False, "beleg": "Sortiment"}
        if name == "video_title":
            return {"cleanedText": "Video für Sie", "cleanedCompanyName": "Firma"}
        if name == "online_shop":
            return {"isActiveOnlineShop": "Warenkorb" in prompt}
        if name == "suchbegriffe":
            assert "{{" not in prompt and "Berufskraftfahrer" in prompt
            return {"suchbegriffe": self.synonyme}
        if name == "groesse":
            assert "{{" not in prompt
            name_zeile = prompt.split("Name: ", 1)[1].split("\n", 1)[0]
            kategorie, anzahl = next((v for k, v in self.groesse.items() if k in name_zeile),
                                     ("mittelstand", "ca. 20–50"))
            return {"kategorie": kategorie, "mitarbeitende_schaetzung": anzahl,
                    "begruendung": f"{name_zeile} eingeordnet als {kategorie}."}
        raise AssertionError(f"unexpected OpenAI schema {name}")


class Kampagne(unittest.TestCase):
    """Base: temporary database, export folder and blocklist cache per test."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.db = self.tmp / "test.db"
        self.api = FakeApi()
        self.patches = [
            mock.patch("scraper.clients._request", self.api),
            mock.patch.object(export, "EXPORT_DIR", self.tmp / "exports"),
            mock.patch.object(sperrliste, "CACHE", self.tmp / "sperrliste.txt"),
            mock.patch.object(blockliste, "DATEI", self.tmp / "blockliste.txt"),
            mock.patch.object(CONFIG, "db_path", self.db),
            # CONFIG may already be loaded by another test module — set the test values directly
            mock.patch.multiple(CONFIG, skael_api_key="eak_test", openai_api_key="sk-test", findymail_api_key="",
                                sperrliste_pflicht=False, max_concurrency=2, max_retries=1,
                                skael_rate_limit_per_sec=1000.0, openai_rate_limit_per_sec=1000.0,
                                llm_provider="openai", domainsuche="aus"),
            mock.patch.object(llm, "PROMPT_DIRS", [self.tmp / "prompts", PROMPTS_DIR]),
        ]
        (self.tmp / "prompts").mkdir()
        for name, text in TEST_PROMPTS.items():
            (self.tmp / "prompts" / name).write_text(text, encoding="utf-8")
        llm.load_prompt.cache_clear()
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in self.patches:
            p.stop()

    def cli(self, *args: str) -> str:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            cli.main(list(args))
        return out.getvalue()

    def rows(self, sql: str) -> list[sqlite3.Row]:
        conn = sqlite3.connect(self.db)
        conn.row_factory = sqlite3.Row
        try:
            return conn.execute(sql).fetchall()
        finally:
            conn.close()

    def export_listen(self) -> dict[str, list[dict]]:
        self.cli("export")
        listen = {}
        for datei in (self.tmp / "exports").glob("*.csv"):
            with datei.open(encoding="utf-8-sig") as fh:
                listen[datei.name.split("_2")[0]] = list(csv.DictReader(fh, delimiter=";"))
        return listen


class TestRecruiting(Kampagne):
    def init(self, *extra):
        return self.cli("init", "--pfad", "recruiting", "--keywords", "Spedition", "--countries", "DE",
                        "--min-population", "100000", "--icp-prompt", "prompts/beispiele/icp_logistik.txt", *extra)

    def test_maps_einstieg_mit_stelle(self):
        self.init()
        status = self.cli("run", "--stage", "all")
        self.assertIn("Kampagnen-Art: recruiting", status)

        ds = {r["business_id"]: r for r in self.rows("SELECT * FROM datensaetze")}
        self.assertEqual(ds["b4"]["dedupe_status"], "dropped_duplicate")
        self.assertEqual(ds["b3"]["is_icp"], 0)
        self.assertEqual(ds["b1"]["stelle_vorhanden"], 1)
        self.assertEqual(ds["b1"]["job_title"], "Berufskraftfahrer (m/w/d) CE")
        self.assertIn("/karriere", ds["b1"]["stelle_url"])
        self.assertEqual(ds["b2"]["stelle_vorhanden"], 0)
        # Café is not ICP → no job search was paid for
        self.assertIsNone(ds["b3"]["stelle_vorhanden"])

        leads = self.rows("SELECT * FROM anreicherung")
        self.assertEqual(len(leads), 1, "without NK only the company with an open position is enriched")
        lead = leads[0]
        self.assertEqual(lead["strecke"], "rc")
        self.assertEqual(lead["job_title_norm"], "Berufskraftfahrer")
        self.assertTrue(lead["personalisierung"].startswith("ich habe gesehen, dass Sie Berufskraftfahrer suchen"))
        self.assertIsNone(lead["video_title"], "RC has no video title")
        self.assertEqual(lead["ready_to_send"], 1)
        self.assertEqual(lead["email_final"], "max.mustermann@alpha-spedition.de")
        # homepage was fetched once in 3e and reused afterwards
        aufrufe = [c for c in self.api.calls if c.endswith("/web_scraper")]
        self.assertEqual(len(aufrufe), 3, aufrufe)   # alpha home + alpha karriere + beta home

        listen = self.export_listen()
        gf = listen["1_zielgruppe_geschaeftsfuehrer"]
        self.assertEqual(len(gf), 1)
        self.assertEqual(gf[0]["Kampagnen-Art"], "recruiting")
        self.assertEqual(gf[0]["Jobtitel"], "Berufskraftfahrer")
        self.assertEqual(gf[0]["Ansprache"], "Guten Tag Herr Mustermann")
        nicht = {r["Firmenname"]: r["Einstufung"] for r in listen["4_nicht_zielgruppe"]}
        self.assertEqual(nicht["Beta Logistik GmbH"], "passt, aber keine offene Stelle gefunden")
        self.assertEqual(nicht["Café Central"], "aussortiert")

    def test_nk_strecke_und_sperrliste(self):
        (self.tmp / "sperrliste.txt").write_text("beta-logistik.de\n", encoding="utf-8")
        self.init("--nk")
        self.cli("run", "--stage", "all")
        leads = {r["firmenname"]: r for r in self.rows("SELECT * FROM anreicherung")}
        self.assertEqual(leads["Beta Logistik GmbH"]["strecke"], "nk")
        self.assertTrue(leads["Beta Logistik GmbH"]["personalisierung"].startswith("bei Ihnen"))
        self.assertEqual(leads["Beta Logistik GmbH"]["ready_to_send"], 1)
        listen = self.export_listen()
        self.assertEqual([r["Firmenname"] for r in listen["5_gesperrt_sperrliste"]], ["Beta Logistik GmbH"])
        self.assertNotIn("https://beta-logistik.de",
                         [r["Website"].rstrip("/") for r in listen["1_zielgruppe_geschaeftsfuehrer"]])
        self.assertEqual(len(listen["1_zielgruppe_geschaeftsfuehrer"]), 1)

    def test_nk_ansprache_neutral_bei_unsicherem_vornamen(self):
        self.init("--nk")
        self.cli("run", "--stage", "all")
        listen = self.export_listen()
        kim = next(r for r in listen["1_zielgruppe_geschaeftsfuehrer"] if r["Vorname"] == "Kim")
        self.assertEqual((kim["Strecke"], kim["Anrede"], kim["Ansprache"]), ("nk", "Herr", "Guten Tag"))
        self.assertTrue(kim["Ansprache Grund"].startswith("Vorname mehrdeutig"))

    def test_kein_import_indeed_mehr(self):
        with self.assertRaises(SystemExit):
            with contextlib.redirect_stderr(io.StringIO()):
                self.cli("import-indeed", "--suche", "Fahrer")


class TestStellensuche(Kampagne):
    def anlegen(self, *extra):
        return self.cli("stellensuche", "--suche", "Berufskraftfahrer", "--orte", "Stuttgart", *extra)

    def endpunkte(self, name: str) -> list[dict]:
        return [b for u, b in self.api.bodies if u.endswith(f"/{name}")]

    def test_volllauf_mit_anreicherung(self):
        ausgabe = self.anlegen()
        self.assertIn("4 Portale × 1 Suchbegriffe × 1 Orte → 4 offene Suchen", ausgabe)
        status = self.cli("run", "--stage", "all")
        self.assertIn("Kampagnen-Art: stellensuche", status)
        self.assertIn("3/4 erledigt", status, "kununu fails, the other portals carry on")

        st = {r["portal_id"]: r for r in self.rows("SELECT * FROM stellen")}
        self.assertEqual(st["i3"]["ausschluss"], "älter als 30 Tage")
        self.assertEqual(st["i4"]["ausschluss"], "Personaldienstleister")
        self.assertEqual(st["aa2"]["ausschluss"], "Personaldienstleister")
        self.assertIsNone(st["i2"]["ausschluss"], "no company name, but an own apply domain")
        self.assertNotIn("marc.hettich", st["i1"]["beschreibung"])
        self.assertNotIn("Hettich", st["i1"]["beschreibung"], "contact block is cut off")
        self.assertIn("Führerschein Klasse C/CE", st["i1"]["beschreibung"])

        ds = self.rows("SELECT * FROM datensaetze WHERE dedupe_status='kept'")
        wilkes = next(r for r in ds if (r["website_final"] or "").rstrip("/") == "https://wilkes.de")
        self.assertEqual((wilkes["stellen_anzahl"], wilkes["stellen_portale"]), (2, "indeed, stepstone"))
        self.assertEqual(wilkes["job_title"], "Berufskraftfahrer Stuttgart", "posting with text wins")
        os_firmen = [r for r in ds if (r["website_final"] or "").rstrip("/") == "https://os-kornwestheim.de"]
        self.assertEqual(len(os_firmen), 1, "two names, same verified domain → one company")
        self.assertEqual((os_firmen[0]["stellen_anzahl"], os_firmen[0]["stellen_portale"]),
                         (2, "arbeitsagentur, stepstone"))
        palmer = next(r for r in ds if r["firmenname"].startswith("Garten"))
        self.assertEqual((palmer["website_final"], palmer["domain_status"]), ("", "unverified"))

        domain_suche = sorted(b["company_name"] for b in self.endpunkte("find_domain"))
        self.assertNotIn("Wilkes GmbH", domain_suche, "portal named the website, no paid lookup")
        self.assertIn("timetrans-logistik.de", domain_suche)
        hinweis = next(b for b in self.endpunkte("find_domain") if b["company_name"] == "timetrans-logistik.de")
        self.assertEqual(hinweis["website"], "https://timetrans-logistik.de")
        self.assertEqual(len(self.endpunkte("icp_checker")), 0, "no profile → no website check")

        leads = {T.host_of(r["website_final"]): r for r in self.rows("SELECT * FROM anreicherung")}
        self.assertEqual(set(leads), {"wilkes.de", "autohaus-staiger.de", "os-kornwestheim.de",
                                      "timetrans-logistik.de"})
        w = leads["wilkes.de"]
        self.assertEqual((w["strecke"], w["stellen_anzahl"], w["stelle_portal"]), ("rc", 2, "indeed"))
        self.assertTrue(w["personalisierung"].startswith("ich habe gesehen, dass Sie Berufskraftfahrer suchen"))
        self.assertEqual(w["ready_to_send"], 1)
        self.assertEqual(leads["timetrans-logistik.de"]["email_final_type"], "Info@")

        listen = self.export_listen()
        self.assertNotIn("3_unsicher", [k for k, v in listen.items() if v])
        gf = {r["Website"].rstrip("/"): r for r in listen["1_zielgruppe_geschaeftsfuehrer"]}
        self.assertEqual(gf["https://wilkes.de"]["Offene Stellen (Anzahl)"], "2")
        self.assertEqual(gf["https://wilkes.de"]["Link zur Anzeige"], "https://de.indeed.com/viewjob?jk=i1")
        self.assertEqual(gf["https://wilkes.de"]["Kampagnen-Art"], "stellensuche")
        alle = listen["0_stellen"]
        self.assertEqual(len(alle), 7, "all accepted postings, one row each")
        self.assertEqual({r["Firma in Lead-Liste"] for r in alle if "wilkes" in r["Website"]}, {"1 (Geschäftsführer)"})
        nicht = {r["Firmenname"]: r["Einstufung"] for r in listen["4_nicht_zielgruppe"]}
        self.assertEqual(nicht["Garten- und Landschaftsbau Palmer GmbH & Co. KG"], "keine eigene Website gefunden")

    def groesse_aufrufe(self) -> list[dict]:
        return [b for u, b in self.api.bodies if "openai" in u
                and b.get("response_format", {}).get("json_schema", {}).get("name") == "groesse"]

    def test_groessen_check_vor_der_website_suche(self):
        self.api.groesse = {"Autohaus Staiger": ("konzern", "über 10.000"),
                            "Wilkes": ("oeffentlich_verband", "ca. 200 Mitarbeitende")}
        ausgabe = self.anlegen("--icp-prompt", "prompts/beispiele/icp_ki_automation.txt")
        self.assertIn("Größen-Check vor der Website-Suche: an", ausgabe)
        status = self.cli("run", "--stage", "all")
        self.assertIn("Größen-Check", status)

        aufrufe = self.groesse_aufrufe()
        self.assertEqual(len(aufrufe), 6, "every company after 1k is checked once")
        self.assertEqual({(b["model"], b["temperature"]) for b in aufrufe}, {(CONFIG.model_groesse, 0.0)})
        wilkes_prompt = next(b["messages"][0]["content"] for b in aufrufe if "Name: Wilkes GmbH" in b["messages"][0]["content"])
        self.assertIn("Website (falls bekannt): https://wilkes.de", wilkes_prompt, "portal website is passed on")

        self.assertNotIn("Autohaus Staiger GmbH", [b["company_name"] for b in self.endpunkte("find_domain")],
                         "no paid website search for a group company")
        self.assertIn("timetrans-logistik.de", [b["company_name"] for b in self.endpunkte("find_domain")])
        self.assertFalse([b for u, b in self.api.bodies if u.split("?")[0].endswith("/icp_checker") and "wilkes" in u],
                         "excluded company with portal website is not checked against the profile")

        ds = {r["firmenname"]: r for r in self.rows("SELECT * FROM datensaetze")}
        staiger = ds["Autohaus Staiger GmbH"]
        self.assertEqual((staiger["groesse_kategorie"], staiger["is_icp"], staiger["dedupe_status"]),
                         ("konzern", 0, "kept"))
        self.assertTrue(staiger["icp_reason"].startswith("Größen-Check: Konzern (über 10.000 Mitarbeitende) – "))
        self.assertIsNone(staiger["domain_status"])
        self.assertEqual(json.loads(ds["Wilkes GmbH"]["groesse_raw"])["kategorie"], "oeffentlich_verband")
        self.assertEqual(ds["Garten- und Landschaftsbau Palmer GmbH & Co. KG"]["groesse_kategorie"], "mittelstand")

        leads = {T.host_of(r["website_final"]) for r in self.rows("SELECT * FROM anreicherung")}
        self.assertEqual(leads, {"os-kornwestheim.de", "timetrans-logistik.de"})

        listen = self.export_listen()
        nicht = {r["Firmenname"]: r for r in listen["4_nicht_zielgruppe"]}
        self.assertEqual(nicht["Autohaus Staiger GmbH"]["Einstufung"], "Größen-Check: Konzern")
        self.assertEqual(nicht["Wilkes GmbH"]["Einstufung"], "Größen-Check: öffentliche Hand/Verband")
        self.assertTrue(nicht["Wilkes GmbH"]["Begründung"].startswith("Größen-Check: öffentliche Hand/Verband (ca. 200"))
        self.assertNotIn("Wilkes GmbH", [r["Firmenname"] for r in listen["3_unsicher"]])

        self.cli("run", "--stage", "all")
        self.assertEqual(len(self.groesse_aufrufe()), 6, "a finished check is not paid twice")

    def test_groessen_check_abschaltbar(self):
        self.api.groesse = {"Autohaus Staiger": ("konzern", "über 10.000")}
        ausgabe = self.anlegen("--no-groessen-check")
        self.assertIn("Größen-Check vor der Website-Suche: aus", ausgabe)
        self.cli("run", "--stage", "all")
        self.assertEqual(self.groesse_aufrufe(), [])
        self.assertIn("Autohaus Staiger GmbH", [b["company_name"] for b in self.endpunkte("find_domain")])
        self.assertIn("autohaus-staiger.de",
                      {T.host_of(r["website_final"]) for r in self.rows("SELECT * FROM anreicherung")})

    def test_groessen_check_fehler_haelt_website_suche_an(self):
        self.anlegen("--portale", "stepstone")
        self.api.groesse_fehler = True
        self.cli("run", "--stage", "1")
        self.cli("run", "--stage", "3")
        ds = self.rows("SELECT * FROM datensaetze")
        self.assertTrue(all(r["groesse_kategorie"] is None for r in ds))
        self.assertEqual({(r["attempts"], r["error"]) for r in ds}, {(1, "Größen-Check fehlgeschlagen")})
        self.assertEqual(self.endpunkte("find_domain"), [], "no paid lookup before the size check succeeded")

        self.api.groesse_fehler = False
        self.cli("run", "--stage", "3")
        self.assertTrue(all(r["groesse_kategorie"] == "mittelstand" for r in self.rows("SELECT * FROM datensaetze")))
        self.assertEqual(len(self.endpunkte("find_domain")), 3, "all three Stepstone companies, after the check")

    def test_eigener_opener_prompt_je_kampagne(self):
        # campaign prompt folder (kampagnen/<name>/prompts/) — here the temporary one
        (self.tmp / "prompts" / "personalisierung_stellenanzeige_ki.txt").write_text(
            (PROMPTS_DIR / "beispiele" / "personalisierung_stellenanzeige_ki.txt").read_text(encoding="utf-8"),
            encoding="utf-8")
        self.anlegen("--portale", "indeed", "--opener-prompt", "personalisierung_stellenanzeige_ki.txt")
        self.cli("run", "--stage", "all")
        opener = [b["messages"][0]["content"] for u, b in self.api.bodies
                  if "openai" in u and b.get("response_format", {}).get("json_schema", {}).get("name") == "personalisierung"]
        self.assertTrue(opener)
        self.assertTrue(all("jemanden als" in p for p in opener), "campaign prompt is used")
        self.assertIn('"job_title_original":"Berufskraftfahrer Stuttgart"', opener[0] + "".join(opener))
        with self.assertRaises(SystemExit):
            self.anlegen("--opener-prompt", "gibt_es_nicht.txt")

    def test_nur_stellen_ohne_kosten_fuer_anreicherung(self):
        (self.tmp / "sperrliste.txt").write_text("wilkes.de\n", encoding="utf-8")
        self.anlegen("--nur-stellen", "--portale", "indeed,stepstone")
        status = self.cli("run", "--stage", "all")
        self.assertIn("nur Stellenliste", status)
        self.assertFalse([c for c in self.api.calls if "openai" in c], "no AI in list-only mode")
        self.assertEqual(self.endpunkte("find_domain"), [])
        self.assertEqual(self.rows("SELECT COUNT(*) FROM anreicherung")[0][0], 0)

        listen = self.export_listen()
        self.assertEqual(sorted(listen), ["0_stellen", "1_firmen_mit_stellen", "5_gesperrt_sperrliste"])
        self.assertFalse([r for r in listen["0_stellen"] if "wilkes" in r["Website"]], "blocked company left out")
        self.assertEqual([r["Firmenname"] for r in listen["5_gesperrt_sperrliste"]], ["Wilkes GmbH"])
        staiger = next(r for r in listen["1_firmen_mit_stellen"] if r["Firmenname"] == "Autohaus Staiger GmbH")
        self.assertEqual((staiger["Website"], staiger["Einstufung"]), ("", "Stelle offen, Website unbekannt"))
        self.assertEqual(staiger["Link zur Anzeige"], "https://www.stepstone.de/jobs----13816826-inline.html")

    def test_erneuter_lauf_verdoppelt_nichts(self):
        self.anlegen("--portale", "stepstone")
        self.cli("run", "--stage", "1")
        self.cli("stellensuche", "--suche", "Berufskraftfahrer", "--orte", "Stuttgart", "--portale", "stepstone")
        self.cli("run", "--stage", "1")
        self.assertEqual(self.rows("SELECT COUNT(*) FROM stellen")[0][0], 3)
        self.assertEqual(self.rows("SELECT COUNT(*) FROM datensaetze")[0][0], 3)
        self.assertEqual(len(self.endpunkte("stepstone_jobs")), 1, "a finished search is not paid twice")

    def test_titel_ausschluss_nachtraeglich_ohne_neue_abfrage(self):
        self.anlegen("--portale", "stepstone", "--nur-stellen")
        self.cli("run", "--stage", "all")
        self.assertEqual(len(self.rows("SELECT * FROM datensaetze WHERE dedupe_status='kept'")), 3)
        abfragen = len(self.endpunkte("stepstone_jobs"))

        self.anlegen("--portale", "stepstone", "--titel-ausschluss", "Lastkraft, C1E")
        self.cli("run", "--stage", "all")
        self.assertEqual(len(self.endpunkte("stepstone_jobs")), abfragen, "filter change must not re-query")
        st = {r["portal_id"]: r["ausschluss"] for r in self.rows("SELECT * FROM stellen")}
        self.assertEqual((st["s1"], st["s3"], st["s2"]), ("Titel enthält „c1e“", "Titel enthält „lastkraft“", None))
        kept = [r["firmenname"] for r in self.rows("SELECT * FROM datensaetze WHERE dedupe_status='kept'")]
        self.assertEqual(kept, ["Wilkes GmbH"], "companies without remaining postings drop out")
        listen = self.export_listen()
        self.assertEqual([r["Firma"] for r in listen["0_stellen"]], ["Wilkes GmbH"])
        self.assertEqual([r["Firmenname"] for r in listen["1_firmen_mit_stellen"]], ["Wilkes GmbH"])

    def test_weiterblaettern_nach_erhoehung_der_seitenzahl(self):
        self.api.stepstone_mehr = True
        self.anlegen("--portale", "stepstone", "--max-seiten", "1", "--nur-stellen")
        self.cli("run", "--stage", "1")
        suche = self.rows("SELECT * FROM stellen_suche")[0]
        self.assertEqual((suche["seiten"], suche["weiter"]), (1, 1))

        ausgabe = self.cli("stellensuche", "--max-seiten", "3")   # nur Einstellungen, keine neue Suche
        self.assertIn("1 erledigte Suchen blättern weiter bis Seite 3", ausgabe)
        self.assertEqual(len(self.rows("SELECT * FROM stellen_suche")), 1)
        self.cli("run", "--stage", "1")
        seiten = [b.get("page") for b in self.endpunkte("stepstone_jobs")]
        self.assertEqual(seiten, [1, 2], "page 1 is not paid twice")
        suche = self.rows("SELECT * FROM stellen_suche")[0]
        self.assertEqual((suche["seiten"], suche["weiter"], suche["treffer"]), (2, 0, 4))
        self.assertIn("s4", {r["portal_id"] for r in self.rows("SELECT * FROM stellen")})
        self.cli("run", "--stage", "1")
        self.assertEqual(len(self.endpunkte("stepstone_jobs")), 2, "nothing left to page")

    def test_falsche_kampagne_in_derselben_datenbank(self):
        self.cli("init", "--keywords", "Spedition", "--countries", "DE")
        with self.assertRaises(SystemExit):
            self.anlegen()


class TestStellenFunktionen(unittest.TestCase):
    def test_anfrage_je_portal(self):
        aa = S.anfrage("arbeitsagentur", "Fahrer", "Ulm", "DE", seite=2, cursor=None, umkreis=30, max_alter=14)
        self.assertEqual((aa["umkreis"], aa["page"], aa["veroeffentlichtseit"], aa["pav"]), ("50", 2, 14, False))
        st = S.anfrage("stepstone", "Fahrer", "", "DE", seite=1, cursor=None, umkreis=25, max_alter=10)
        self.assertEqual((st["date_posted"], st["location"], st["radius"]), ("30", None, None))
        ku = S.anfrage("kununu", "Fahrer", "Ulm", "DE", seite=1, cursor=None, umkreis=25, max_alter=30)
        self.assertEqual(ku["radius"], 30)

    def test_ausschluss_und_firmenschluessel(self):
        stelle = {"firma": "Müller Transporte GmbH & Co. KG", "website": "", "bewerben_url": "",
                  "veroeffentlicht": _tage(40)}
        self.assertEqual(S.ausschluss(stelle, 30), "älter als 30 Tage")
        self.assertIsNone(S.ausschluss(stelle, 60))
        self.assertEqual(S.firmen_name_schluessel("Müller Transporte GmbH & Co. KG Niederlassung Ulm"),
                         "müller transporte")
        portal = {**stelle, "firma": "t.gohiring.com"}
        self.assertEqual(S.ausschluss(portal, 60), "Jobbörse/Bewerbersystem statt Firma")
        self.assertEqual(S.bewerben_host({"bewerben_url": "https://jobs.ionos.de/stelle/1"}), "ionos.de")
        leer = {"firma": "", "website": "", "bewerben_url": "https://www.personio.de/job/1", "veroeffentlicht": ""}
        self.assertEqual(S.ausschluss(leer, 30), "ohne Firmenname", "an ATS link is no company domain")

    def test_titel_pflicht_mit_wortgrenzen(self):
        pflicht = ["KI", "AI", "automatisier", "n8n"]
        stelle = {"firma": "Muster GmbH", "website": "", "bewerben_url": "", "veroeffentlicht": ""}
        for titel, erwartet in (("KI-Manager (m/w/d)", None), ("AI Engineer", None),
                                ("Automatisierungsexperte Vertrieb", None), ("Entwickler n8n / Make", None),
                                ("Erzieher Kinderkrippe", "Titel passt nicht zur Suche"),
                                ("Supply Chain Coordinator", "Titel passt nicht zur Suche"),
                                ("Trainer Maintenance", "Titel passt nicht zur Suche")):
            self.assertEqual(S.ausschluss({**stelle, "titel": titel}, 0, titel_pflicht=pflicht), erwartet, titel)

    def test_beschreibung_ohne_kontakt(self):
        text = S.beschreibung_bereinigen(
            "<h2>Ihr Profil</h2><ul><li>CE-Führerschein</li><li>ADR-Schein von Vorteil</li></ul>"
            "<p>Ihr Ansprechpartner: Frau Erika Muster, erika@firma.de, 0711 123456</p>")
        self.assertIn("CE-Führerschein", text)
        self.assertNotIn("Erika", text)
        self.assertNotIn("@", text)


class TestGoogleMapsUnveraendert(Kampagne):
    def test_standardpfad(self):
        self.cli("init", "--keywords", "Spedition", "--countries", "DE",
                 "--icp-prompt", "prompts/beispiele/icp_logistik.txt")
        self.cli("run", "--stage", "all")
        leads = self.rows("SELECT * FROM anreicherung ORDER BY firmenname")
        self.assertEqual([r["strecke"] for r in leads], ["gmaps", "gmaps"])
        self.assertTrue(all(r["video_title"] for r in leads))
        self.assertTrue(all(r["personalisierung"].startswith("wie Sie") for r in leads))
        self.assertIsNone(self.rows("SELECT * FROM datensaetze WHERE business_id='b1'")[0]["stelle_vorhanden"])
        listen = self.export_listen()
        self.assertEqual({r["Kampagnen-Art"] for r in listen["1_zielgruppe_geschaeftsfuehrer"]}, {"google-maps"})

    def test_andere_kampagne_in_derselben_datenbank_wird_abgelehnt(self):
        self.cli("init", "--keywords", "Spedition", "--countries", "DE")
        self.cli("run", "--stage", "2")
        with self.assertRaises(SystemExit):
            self.cli("stellensuche", "--suche", "Berufskraftfahrer")


class TestTestballon(Kampagne):
    """Testballon inside one campaign (testballon-lauf) and the comparison report."""

    def portale(self, *extra):
        return self.cli("stellensuche", "--suche", "Berufskraftfahrer", "--orte", "Stuttgart", *extra)

    def meta(self, key):
        rows = self.rows(f"SELECT value FROM run_meta WHERE key='{key}'")
        return rows[0][0] if rows else None

    def test_portale_bis_zum_ziel(self):
        self.portale()
        ausgabe = self.cli("testballon-lauf", "--ziel", "2", "--budget", "5")
        self.assertIn("Ziel erreicht", ausgabe)
        self.assertGreaterEqual(len(self.rows("SELECT * FROM anreicherung WHERE ready_to_send=1")), 2)
        self.assertEqual(self.meta("ballon_grund"), "ziel")

    def test_nur_so_viele_firmen_wie_noetig(self):
        self.portale()
        self.cli("testballon-lauf", "--ziel", "1")
        # target 1, assumed ready rate 70 % -> 2 firms handed over, not all with a website
        self.assertEqual(len(self.rows("SELECT * FROM anreicherung")), 2)

    def test_budget_stoppt_den_lauf(self):
        self.portale()
        self.api.credits = 10
        ausgabe = self.cli("testballon-lauf", "--ziel", "50", "--budget", "0.02")   # 20 credits
        self.assertIn("Budget aufgebraucht", ausgabe)
        self.assertEqual(self.meta("ballon_grund"), "budget")
        gebucht = self.rows("SELECT SUM(credits) FROM kosten")[0][0]
        self.assertLess(gebucht, 20 + 10 * 2 + 1, "at most MAX_CONCURRENCY jobs beyond the cap")
        self.assertEqual(self.rows("SELECT COUNT(*) FROM anreicherung")[0][0], 0, "no enrichment after the cap")

    def test_fallback_leiter_portale(self):
        self.portale("--portale", "arbeitsagentur")
        ausgabe = self.cli("testballon-lauf", "--ziel", "50")
        self.assertIn("Markt erschöpft", ausgabe)
        stufen = [f["stufe"] for f in json.loads(self.meta("ballon_fallback"))]
        self.assertEqual(stufen, ["zeitraum", "synonyme"])
        self.assertEqual(self.meta("stellen_max_alter"), "60")
        begriffe = {r[0] for r in self.rows("SELECT DISTINCT suchbegriff FROM stellen_suche")}
        self.assertEqual(begriffe, {"Berufskraftfahrer", "LKW-Fahrer"}, "known term is not added twice")
        self.assertEqual(len([u for u in self.api.calls if u.endswith("/arbeitsagentur_jobs")]), 2,
                         "one search per term, nothing paid twice")

    def test_fallback_leiter_website_ohne_doppelte_staedte(self):
        self.cli("init", "--pfad", "recruiting", "--keywords", "Spedition", "--countries", "DE",
                 "--min-population", "100000", "--berufe", "Berufskraftfahrer")
        ausgabe = self.cli("testballon-lauf", "--ziel", "50")
        self.assertIn("Markt erschöpft", ausgabe)
        fallback = json.loads(self.meta("ballon_fallback"))
        self.assertEqual([f["stufe"] for f in fallback], ["region"], "no NK strecke without a check profile")
        self.assertEqual(len([u for u in self.api.calls if "/maps_search" in u]), 1, "Ulm is not queried twice")
        ds = {r["firmenname"]: r for r in self.rows("SELECT * FROM datensaetze")}
        self.assertEqual(ds["Alpha Spedition GmbH"]["is_icp"], 1, "without profile the open position decides")
        leads = self.rows("SELECT * FROM anreicherung")
        self.assertEqual([r["firmenname"] for r in leads], ["Alpha Spedition GmbH"])

    def test_website_mit_profil_schaltet_nk_zu(self):
        self.cli("init", "--pfad", "recruiting", "--keywords", "Spedition", "--countries", "DE",
                 "--min-population", "100000", "--berufe", "Berufskraftfahrer",
                 "--icp-prompt", "prompts/beispiele/icp_logistik.txt")
        self.cli("testballon-lauf", "--ziel", "2")
        self.assertEqual(json.loads(self.meta("ballon_fallback"))[0]["stufe"], "nk")
        self.assertEqual({r["strecke"] for r in self.rows("SELECT * FROM anreicherung")}, {"rc", "nk"})
        self.assertEqual(self.meta("ballon_grund"), "ziel")

    def test_marktprobe_ohne_anreicherung(self):
        self.portale()
        self.cli("testballon-lauf", "--nur-marktprobe")
        self.assertTrue(self.rows("SELECT * FROM stellen"))
        self.assertEqual(self.rows("SELECT COUNT(*) FROM anreicherung")[0][0], 0)
        self.assertFalse([u for u in self.api.calls if "openai" in u or u.endswith("/find_domain")])

    def test_vergleichsbericht(self):
        from scraper import testballon
        self.api.credits = 5
        self.portale()
        self.cli("testballon-lauf", "--ziel", "3")
        website_db = self.tmp / "website.db"
        with mock.patch.object(CONFIG, "db_path", website_db):
            self.cli("init", "--pfad", "recruiting", "--keywords", "Spedition", "--countries", "DE",
                     "--min-population", "100000", "--berufe", "Berufskraftfahrer")
            self.cli("testballon-lauf", "--ziel", "3")
        text = testballon.bericht("fahrer", {"website": website_db, "portale": self.db}, 3)
        self.assertIn("| Versandfertige Leads | **1** | **4** |", text)
        self.assertIn("Jobportale (Stellensuche)** – nur dieser Weg hat das Ziel erreicht", text)
        self.assertIn("Überschneidung", text)
        self.assertIn("Kleinere Städte aufgenommen", text)
        self.assertIn("Stelle: Berufskraftfahrer", text)
        self.assertNotIn("@", text, "no e-mail addresses in the report")

    def test_testballon_legt_beide_kampagnen_an(self):
        import shutil
        from scraper import config
        root = self.tmp / "kampagnen"
        shutil.copytree(config.KAMPAGNEN_ROOT / "_vorlage", root / "_vorlage")
        aufrufe = []
        with mock.patch.object(config, "KAMPAGNEN_ROOT", root), \
                mock.patch.object(config, "EXPORT_DIR", self.tmp / "exports"), \
                mock.patch.object(cli, "_scraper", side_effect=lambda k, *b: aufrufe.append((k, b)) or 0):
            ausgabe = self.cli("testballon", "--name", "Fahrer Süd", "--suche", "Berufskraftfahrer",
                               "--keywords", "Spedition", "--orte", "Stuttgart", "--budget", "8")
        env = (root / "fahrer-süd-website" / "kampagne.env").read_text(encoding="utf-8")
        self.assertIn("DO_VIDEO_TITLE=false", env)
        self.assertNotIn("[[", env)
        self.assertFalse((root / "fahrer-süd-portale" / "prompts" / "icp.txt").exists(), "template profile removed")
        self.assertEqual([(k, b[0]) for k, b in aufrufe], [
            ("fahrer-süd-website", "init"), ("fahrer-süd-website", "testballon-lauf"),
            ("fahrer-süd-website", "export"), ("fahrer-süd-portale", "stellensuche"),
            ("fahrer-süd-portale", "testballon-lauf"), ("fahrer-süd-portale", "export")])
        self.assertIn("--berufe", aufrufe[0][1])
        self.assertIn(("--orte", "Stuttgart"), list(zip(aufrufe[3][1], aufrufe[3][1][1:])))
        self.assertIn("--budget", aufrufe[1][1])
        self.assertIn("Noch keine Daten", ausgabe)
        self.assertTrue(list((self.tmp / "exports").glob("testballon_fahrer-süd_*.md")))


class TestTransforms(unittest.TestCase):
    def test_karriere_links(self):
        out = {"final_url": "https://www.firma.de/", "links": [
            "https://www.firma.de/team", "https://www.firma.de/karriere/", "https://jobs.firma.de/stellenangebote",
            "https://andere.de/jobs", "https://www.firma.de/impressum"]}
        self.assertEqual(T.karriere_links(out, 2),
                         ["https://jobs.firma.de/stellenangebote", "https://www.firma.de/karriere"])

    def test_ansprache_sicher(self):
        self.assertEqual(T.ansprache_sicher("Frau", "Muster", 95)[0], "Guten Tag Frau Muster")
        self.assertEqual(T.ansprache_sicher("Herr", "Lee", 60)[0], "Guten Tag")
        self.assertEqual(T.ansprache_sicher("", "", None)[0], "Guten Tag")


if __name__ == "__main__":
    unittest.main()
