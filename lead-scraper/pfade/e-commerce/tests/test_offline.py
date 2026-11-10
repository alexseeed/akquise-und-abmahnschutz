"""Offline-Test der ganzen Pipeline mit Attrappen statt echter Dienste — kostet nichts.

    python3 -m unittest discover -s tests -v      (aus pfade/e-commerce/)
"""
from __future__ import annotations

import contextlib
import csv
import io
import logging
import os
import subprocess
import sys
import tempfile
import unicodedata
import unittest
from pathlib import Path

TMP = tempfile.mkdtemp()
# Alles, was ein Ergebnis ändert, fest setzen: Einstellungen aus der echten .env (z. B. MIN_AVR_TRAFFIC=5000
# oder DO_PERSONALISIERUNG=false) dürfen die Tests nicht kippen. Gesetzte Variablen überschreibt .env nicht.
# Keine Schlüssel, Dienste auf einer toten lokalen Adresse, Sperrliste ohne Download: kein Aufruf kostet etwas.
os.environ.update({
    "DB_PATH": str(Path(TMP) / "test.db"),
    "SPERRLISTE_PFLICHT": "false",
    "SPERRLISTE_URL": "https://example.invalid/OWNER-liste.txt",
    "SKAEL_API_KEY": "", "OPENAI_API_KEY": "", "FINDYMAIL_API_KEY": "",
    "SKAEL_BASE_URL": "http://127.0.0.1:9", "OPENAI_BASE_URL": "http://127.0.0.1:9",
    "MIN_AVR_TRAFFIC": "1", "MIN_MAX_TRAFFIC_3MO": "1", "TRAFFIC_MODE": "OR",
    "USE_FINDYMAIL": "true", "DO_PERSONALISIERUNG": "true", "DO_VIDEO_TITLE": "true",
    "MAX_RETRIES": "1",
})
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

if sys.version_info < (3, 10):
    from ecom.cli import _check_python
    _check_python()   # dieselbe Meldung wie bei den Befehlen statt vieler Folgefehler

from ecom import cli, clients, config, db, export as export_mod, mailtext as M, pipeline  # noqa: E402
from ecom import sperrliste as sperrliste_mod, transforms as T  # noqa: E402
from ecom.clients import ApiError, FindymailClient, ZugangGesperrt  # noqa: E402
from ecom.config import CONFIG, ROOT  # noqa: E402
from ecom.llm import LLM, render  # noqa: E402

sperrliste_mod.CACHE = Path(TMP) / "sperrliste.txt"   # nie die Kopie im echten data/ lesen oder schreiben

SHOP_TEXT = "Neu im Sortiment – In den Warenkorb – Zur Kasse – Versandkostenfrei ab 50 €"

# Auftrags-Anforderungen wie nach den Buildern (erfundener Absender)
PROFIL = "Passt {{website [Final]}} zu einem Endkunden-Shop?\n\nStartseite:\n{{BodyText}}"
PERSONALISIERUNG = ("Schreibe einen Satz für {{Firmenname}}. Danach folgt diese Mail:\n{{Mailtext}}\n\n"
                    "Startseite:\n{{Bodytext Website}}")
MAILTEXT = """Betreff: Kurze Frage zu {{Firmenname}}

{{Ansprache Normal}},

{{Personalisierung}}

Wir helfen Shops, aus Besuchern Käufer zu machen. Darf ich Ihnen zeigen, wie?

Viele Grüße
Erika Beispiel, Muster Agentur, Musterstraße 1, 12345 Musterstadt
Kein Interesse? Eine kurze Antwort genügt, dann melde ich mich nicht mehr.
"""


def _anforderungen_setzen(conn) -> None:
    db.set_meta(conn, db.META_SHOPPROFIL, PROFIL)
    db.set_meta(conn, db.META_PERSONALISIERUNG, PERSONALISIERUNG)
    db.set_meta(conn, db.META_MAILTEXT, MAILTEXT)


def _csv(pfad: Path) -> list[dict]:
    with pfad.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh, delimiter=";"))


def _kopf(pfad: Path) -> list[str]:
    with pfad.open(encoding="utf-8-sig", newline="") as fh:
        return next(csv.reader(fh, delimiter=";"))


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


class IsolierteDB(unittest.TestCase):
    """Eigene Datenbank und eigener Exportordner je Test."""

    def setUp(self):
        self.original_db = CONFIG.db_path
        self.original_export = export_mod.EXPORT_DIR
        self.ordner = Path(tempfile.mkdtemp(dir=TMP))
        CONFIG.db_path = self.ordner / "test.db"
        export_mod.EXPORT_DIR = self.ordner / "exports"
        self.conn = db.connect()
        db.init(self.conn)

    def tearDown(self):
        self.conn.close()
        CONFIG.db_path = self.original_db
        export_mod.EXPORT_DIR = self.original_export

    def datei(self, name: str, text: str) -> str:
        pfad = self.ordner / name
        pfad.write_text(text, encoding="utf-8")
        return str(pfad)

    def liste(self, label_anfang: str) -> Path:
        for bezeichnung, pfad, _ in export_mod.export_listen(self.conn):
            if bezeichnung.startswith(label_anfang):
                return pfad
        raise AssertionError(label_anfang)


class FakeSkael:
    def __init__(self):
        self.calls: list[tuple[str, str]] = []

    def ai_research_agent(self, system_prompt, user_prompt, schema, max_steps=5, model=""):
        self.calls.append(("agent", user_prompt))
        return {"response": "https://www.gefunden-shop.de/"}

    def web_scraper(self, url):
        self.calls.append(("web_scraper", url))
        if "wartung" in url:
            return {"body_text": "Site under maintenance. Please check back later."}
        if "grosshandel" in url:
            return {"body_text": SHOP_TEXT + " Nur für Gewerbekunden " + url}
        if "kaputt" in url:
            return {"body_text": SHOP_TEXT + " KAPUTT " + url}
        return {"body_text": SHOP_TEXT + " " + url}

    def webtraffic(self, domain):
        self.calls.append(("webtraffic", domain))
        if "ohnetraffic" in domain:
            return {"found": False, "domain": domain}
        return {"found": True, "estimated_monthly_visits": {"2026-07-01": 1000, "2026-08-01": 2001, "2026-09-01": 3000}}

    def imprint_extractor(self, domain):
        self.calls.append(("imprint", domain))
        return {"firmenname": f"{domain} GmbH", "geschaeftsfuehrer": ["Herr Dr. Max Müller"],
                "email": "info(at)" + domain, "telefon": "+49 1", "adresse": "Str. 1, 12345 Ort"}

    def find_email_person(self, domain, full_name):
        self.calls.append(("mailfinder", domain))
        return {"email": "max.mueller@" + T.host_of(domain), "email_status": "valid"}

    def verify_email(self, email):
        self.calls.append(("verify", email))
        return {"email": email, "code": 5}


class FakeOpenAI:
    def __init__(self):
        self.prompts: list[tuple[str, str]] = []

    def complete(self, prompt, *, model=None, json_schema=None, schema_name="", temperature=0.2, web_search=False):
        self.prompts.append((schema_name, prompt))
        if schema_name == "icp_online_shop":
            return {"isActiveOnlineShop": "Warenkorb" in prompt}
        if schema_name == "shopprofil":
            if "KAPUTT" in prompt:
                raise ApiError("OpenAI HTTP 500", 500)
            passt = "Gewerbekunden" not in prompt
            return {"is_icp": passt, "confidence": 0.9, "reason": "Endkunden-Shop" if passt else "nur Gewerbekunden"}
        if schema_name == "anrede":
            return {"anrede": "Herr", "confidence": 100}
        if schema_name == "personalisierung":
            return {"complimentText": "bei Ihnen wirkt das Sortiment durchdacht."}
        if schema_name == "video_title_cleanup":
            return {"cleanedText": "Video für Max Mueller", "cleanedCompanyName": "Shop"}
        raise AssertionError(schema_name)


class FakeFindymail:
    api_key = ""


class KettenProfil(FakeOpenAI):
    """Nachgeschärftes Profil: „Keine Ketten.“ lehnt den Endkunden-Shop ab; der KI-Fehler ist vorbei."""

    def complete(self, prompt, **kwargs):
        if kwargs.get("schema_name") == "shopprofil":
            if "Keine Ketten." in prompt and "endkunde-shop.de" in prompt:
                return {"is_icp": False, "confidence": 0.8, "reason": "Kette"}
            return super().complete(prompt.replace("KAPUTT", ""), **kwargs)
        return super().complete(prompt, **kwargs)


class AnredeKaputt(FakeOpenAI):
    def complete(self, prompt, **kwargs):
        if kwargs.get("schema_name") == "anrede":
            raise ApiError("OpenAI HTTP 500", 500)
        return super().complete(prompt, **kwargs)


class TransformTests(unittest.TestCase):
    def test_traffic_wie_clay(self):
        out = {"estimated_monthly_visits": {"a": 1, "b": 2}}
        self.assertEqual(T.avr_traffic(out), 2)          # Math.round(1.5) = 2
        self.assertEqual(T.max_traffic_3mo(out), 2)
        self.assertIsNone(T.avr_traffic({"found": False}))
        self.assertFalse(T.send(None, None, min_avr=1, min_max=1, mode="OR"))  # Number("") = 0
        self.assertTrue(T.send(0, 5, min_avr=1, min_max=1, mode="OR"))
        self.assertFalse(T.send(0, 5, min_avr=1, min_max=1, mode="AND"))

    def test_website_final(self):
        self.assertEqual(T.website_final("shop.de", None), "shop.de")
        self.assertEqual(T.website_final("kein link", "https://a.de"), "https://a.de")
        self.assertEqual(T.website_final("", None), "")

    def test_render_laesst_fremde_platzhalter_stehen(self):
        self.assertEqual(render("{{A}} {{lastName}}", {"A": "x"}), "x {{lastName}}")


class PipelineTest(unittest.TestCase):
    def test_durchlauf(self):
        conn = db.connect()
        db.init(conn)
        for key, name, web in (("beispiel-shop.de", "Beispiel Shop", "https://www.beispiel-shop.de"),
                               ("wartung.de", "Wartung", "wartung.de"),
                               ("ohnetraffic.de", "Ohne Traffic", "ohnetraffic.de"),
                               ("name:nur name", "Nur Name", "")):
            db.insert_ignore(conn, "shops", {"import_key": key, "firmenname": name, "website": web})
        _anforderungen_setzen(conn)
        self.assertEqual(pipeline.fehlende_anforderungen(conn, set(cli.STUFEN_1 + cli.STUFEN_2)), [])
        skael = FakeSkael()
        openai = FakeOpenAI()
        llm = LLM(client=openai, skael=skael)

        pipeline.stufe1a_domain(conn, llm)
        pipeline.stufe1b_webscraper(conn, skael)
        pipeline.stufe1c_onlineshop(conn, llm)
        pipeline.stufe1d_webtraffic(conn, skael)
        pipeline.stufe1e_uebergabe(conn)
        shops = {r["firmenname"]: r for r in conn.execute("SELECT * FROM shops")}
        self.assertEqual(shops["Nur Name"]["website_final"], "https://www.gefunden-shop.de/")
        self.assertEqual(shops["Wartung"]["is_active_shop"], 0)
        self.assertEqual(shops["Ohne Traffic"]["send"], 0)
        self.assertEqual(shops["Beispiel Shop"]["avr_traffic"], 2000)
        self.assertEqual(shops["Beispiel Shop"]["max_traffic_3mo"], 3000)
        self.assertEqual(shops["Beispiel Shop"]["passt_profil"], 1)
        self.assertEqual(shops["Beispiel Shop"]["profil_grund"], "Endkunden-Shop")
        self.assertIsNone(shops["Wartung"]["passt_profil"])          # kein aktiver Shop → keine Profil-Prüfung
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM anreicherung").fetchone()[0], 2)

        pipeline.stufe2a_website_final(conn, llm)
        pipeline.stufe2b_impressum(conn, skael)
        pipeline.stufe2c_emails(conn, skael, FakeFindymail())
        pipeline.stufe2d_anrede(conn, llm)
        pipeline.stufe2e_personalisierung(conn, skael, llm)
        pipeline.stufe2f_videotitel(conn, llm)
        pipeline.stufe2g_ready(conn)

        lead = conn.execute("SELECT * FROM anreicherung WHERE firmenname='Beispiel Shop'").fetchone()
        self.assertEqual(lead["kontaktperson_sauber"], "Max Mueller")
        self.assertEqual(lead["email_final"], "max.mueller@beispiel-shop.de")
        self.assertEqual(lead["email_final_type"], "GF")
        self.assertEqual(lead["ansprache_normal_gt"], "Guten Tag Herr Mueller")
        self.assertEqual(lead["ready_to_send"], 1)
        # Der Website-Abruf aus Stufe 1 wird wiederverwendet, nicht neu bezahlt
        scrapes = [c for c in skael.calls if c == ("web_scraper", "https://www.beispiel-shop.de")]
        self.assertEqual(len(scrapes), 1)

        # Personalisierung nutzt den Prompt des Auftrags: Platzhalter ersetzt, Mailtext wörtlich dabei
        pers = [prompt for name, prompt in openai.prompts if name == "personalisierung"]
        self.assertEqual(len(pers), 2)
        for prompt in pers:
            self.assertNotIn("{{Bodytext Website}}", prompt)
            self.assertNotIn("{{Firmenname}}", prompt.split("Danach folgt")[0])
            self.assertIn("Warenkorb", prompt)
            self.assertIn("Wir helfen Shops", prompt)
            self.assertIn("{{Personalisierung}}", prompt)   # Mailtext steht als Vorlage im Prompt

        export_mod.EXPORT_DIR = Path(TMP) / "exports"
        ergebnis = export_mod.export_listen(conn)
        listen = {name: anzahl for name, _, anzahl in ergebnis}
        self.assertEqual(listen["Geschäftsführer-Adresse"], 2)
        self.assertEqual(listen["Aussortiert · nur zur Nachvollziehbarkeit"], 2)
        gf = next(pfad for name, pfad, _ in ergebnis if name == "Geschäftsführer-Adresse")
        mail = {r["Website"]: r for r in _csv(gf)}["https://www.beispiel-shop.de"]
        self.assertTrue(mail["Mailtext"].startswith(
            "Hallo Herr Mueller,\n\nbei Ihnen wirkt das Sortiment durchdacht.\n\nWir helfen Shops"))
        self.assertEqual(mail["Betreff"], f"Kurze Frage zu {mail['Firmenname']}")


class FindymailClientTest(unittest.TestCase):
    """Antworten laut https://app.findymail.com/docs, ohne Netz."""

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
        self._antwort(200, {"contact": {"name": "Max Mueller", "domain": "shop.de", "email": "max@shop.de"}})
        out = FindymailClient(api_key="k").find_work_email("Max Mueller", "https://www.shop.de/impressum")
        self.assertEqual(out["email"], "max@shop.de")
        self.assertEqual(self.gesendet[0][1], {"name": "Max Mueller", "domain": "shop.de"})

    def test_nichts_gefunden(self):
        self._antwort(404, {"error": "Not found"})
        self.assertIsNone(FindymailClient(api_key="k").find_work_email("Max Mueller", "shop.de")["email"])

    def test_leeres_guthaben_ist_ein_fehler(self):
        self._antwort(402, {"error": "Not enough credits"})
        with self.assertRaises(ApiError):
            FindymailClient(api_key="k").find_work_email("Max Mueller", "shop.de")


class SkaelOhneTreffer(FakeSkael):
    def find_email_person(self, domain, full_name):
        self.calls.append(("mailfinder", domain))
        return {"email": None}


class FindymailMitTreffer:
    api_key = "k"

    def find_work_email(self, full_name, company_domain):
        return {"email": "max.mueller@shop-a.de", "raw": {"contact": {"email": "max.mueller@shop-a.de"}}}


class FindymailOhneGuthaben:
    api_key = "k"

    def find_work_email(self, full_name, company_domain):
        raise ApiError("Findymail HTTP 402: Not enough credits", 402)


class FindymailGestoert:
    api_key = "k"

    def find_work_email(self, full_name, company_domain):
        raise ApiError("Findymail HTTP 503: unbekannter Fehler", 503)


class FindymailPipelineTest(unittest.TestCase):
    """Skael findet nichts → Findymail springt ein. Leeres Guthaben lässt den Lead offen."""

    def setUp(self):
        self.original_db = CONFIG.db_path
        CONFIG.db_path = Path(TMP) / f"{self._testMethodName}.db"
        self.conn = db.connect()
        db.init(self.conn)
        db.insert_ignore(self.conn, "shops", {"import_key": "shop-a.de", "firmenname": "Shop A", "website": "shop-a.de"})
        shop_id = self.conn.execute("SELECT id FROM shops").fetchone()[0]
        db.insert_ignore(self.conn, "anreicherung", {
            "shop_id": shop_id, "firmenname": "Shop A", "website_final": "https://www.shop-a.de",
            "kontaktperson_sauber": "Max Mueller", "launch_campaign": 1, "dedupe_status": "kept"})

    def tearDown(self):
        self.conn.close()
        CONFIG.db_path = self.original_db

    def test_findymail_springt_ein(self):
        pipeline.stufe2c_emails(self.conn, SkaelOhneTreffer(), FindymailMitTreffer())
        lead = self.conn.execute("SELECT * FROM anreicherung").fetchone()
        self.assertEqual(lead["email_final"], "max.mueller@shop-a.de")
        self.assertEqual(lead["email_source_gf"], "Findymail")

    def test_leeres_guthaben_stoppt_stufe_ohne_fehlversuch(self):
        # Zugangsfehler: Lead bleibt offen, verbraucht aber keinen seiner drei Versuche
        with self.assertRaises(ZugangGesperrt) as ctx:
            pipeline.stufe2c_emails(self.conn, SkaelOhneTreffer(), FindymailOhneGuthaben())
        self.assertIn("USE_FINDYMAIL=false", str(ctx.exception))
        lead = self.conn.execute("SELECT * FROM anreicherung").fetchone()
        self.assertIsNone(lead["email_final"])
        self.assertEqual((lead["attempts"], lead["error"]), (0, None))

    def test_stoerung_laesst_lead_offen_und_zaehlt(self):
        pipeline.stufe2c_emails(self.conn, SkaelOhneTreffer(), FindymailGestoert())
        lead = self.conn.execute("SELECT * FROM anreicherung").fetchone()
        self.assertIsNone(lead["email_final"])
        self.assertEqual(lead["attempts"], 1)
        self.assertIn("Findymail", lead["error"])


class MigrationTest(unittest.TestCase):
    def test_alte_datenbank_bekommt_neue_spalten_und_meta(self):
        import sqlite3
        pfad = Path(tempfile.mkdtemp(dir=TMP)) / "alt.db"
        alt = sqlite3.connect(pfad)
        alt.execute("CREATE TABLE shops (id INTEGER PRIMARY KEY, import_key TEXT NOT NULL UNIQUE, firmenname TEXT, "
                    "website TEXT, website_final TEXT, is_active_shop INTEGER, uebergeben INTEGER DEFAULT 0, "
                    "attempts INTEGER NOT NULL DEFAULT 0, error TEXT)")
        alt.execute("INSERT INTO shops (import_key, firmenname) VALUES ('alt.de', 'Alt')")
        alt.commit()
        alt.close()

        original = CONFIG.db_path
        CONFIG.db_path = pfad
        try:
            conn = db.connect()
            db.init(conn)
            spalten = {r["name"] for r in conn.execute("PRAGMA table_info(shops)")}
            self.assertTrue({"profil_raw", "passt_profil", "profil_confidence", "profil_grund"} <= spalten)
            self.assertIsNone(db.get_meta(conn, db.META_SHOPPROFIL))
            db.set_meta(conn, db.META_SHOPPROFIL, "")
            self.assertEqual(db.get_meta(conn, db.META_SHOPPROFIL), "")
            self.assertEqual(conn.execute("SELECT firmenname FROM shops").fetchone()[0], "Alt")
            db.init(conn)   # zweimal ist harmlos
            conn.close()
        finally:
            CONFIG.db_path = original


class ShopProfilTest(IsolierteDB):
    """Das Shop-Profil des Kunden sortiert aktive Shops aus, bevor Traffic Geld kostet."""

    def setUp(self):
        super().setUp()
        for key, name in (("endkunde-shop.de", "Endkunde"), ("grosshandel-shop.de", "Grosshandel"),
                          ("kaputt-shop.de", "Kaputt")):
            db.insert_ignore(self.conn, "shops", {"import_key": key, "firmenname": name, "website": key})
        self.skael = FakeSkael()
        self.openai = FakeOpenAI()
        self.llm = LLM(client=self.openai, skael=self.skael)

    def stufe1(self):
        pipeline.stufe1a_domain(self.conn, self.llm)
        pipeline.stufe1b_webscraper(self.conn, self.skael)
        pipeline.stufe1c_onlineshop(self.conn, self.llm)
        pipeline.stufe1d_webtraffic(self.conn, self.skael)
        pipeline.stufe1e_uebergabe(self.conn)
        return {r["firmenname"]: r for r in self.conn.execute("SELECT * FROM shops")}

    def test_profil_lehnt_shop_ab(self):
        db.set_meta(self.conn, db.META_SHOPPROFIL, PROFIL)
        shops = self.stufe1()

        self.assertEqual(shops["Endkunde"]["passt_profil"], 1)
        self.assertEqual(shops["Grosshandel"]["passt_profil"], 0)
        self.assertEqual(shops["Grosshandel"]["profil_grund"], "nur Gewerbekunden")
        self.assertAlmostEqual(shops["Grosshandel"]["profil_confidence"], 0.9)
        self.assertEqual(shops["Grosshandel"]["is_active_shop"], 1)
        # KI-Fehler: nichts ins „erledigt“-Feld, Versuch zählt, wird beim nächsten Lauf wiederholt
        self.assertIsNone(shops["Kaputt"]["profil_raw"])
        self.assertIsNone(shops["Kaputt"]["passt_profil"])
        self.assertEqual(shops["Kaputt"]["attempts"], 1)
        self.assertIn("Shop-Profil", shops["Kaputt"]["error"])

        # Traffic (bezahlt) nur für den passenden Shop, übergeben nur er
        traffic = [domain for art, domain in self.skael.calls if art == "webtraffic"]
        self.assertEqual(traffic, ["endkunde-shop.de"])
        self.assertEqual(shops["Endkunde"]["uebergeben"], 1)
        self.assertEqual(shops["Grosshandel"]["uebergeben"], 0)
        self.assertEqual(shops["Kaputt"]["uebergeben"], 0)
        an = [r["firmenname"] for r in self.conn.execute("SELECT firmenname FROM anreicherung")]
        self.assertEqual(an, ["Endkunde"])

        # Profil-Prompt mit eingesetzten Werten
        prompt = next(p for n, p in self.openai.prompts if n == "shopprofil")
        self.assertNotIn("{{BodyText}}", prompt)
        self.assertNotIn("{{website [Final]}}", prompt)

        gruende = {r["Firmenname"]: r["Grund"] for r in _csv(self.liste("Aussortiert"))}
        self.assertEqual(gruende["Grosshandel"], "passt nicht zum Shop-Profil: nur Gewerbekunden")
        self.assertEqual(gruende["Kaputt"], "Profil-Prüfung ausstehend")
        self.assertNotIn("Endkunde", gruende)

    def test_abgelehnter_shop_auch_mit_traffic_in_liste_3(self):
        # Randfall: Traffic lag schon vor, dann lehnt das Profil ab → trotzdem nicht übergeben, Liste 3
        db.set_meta(self.conn, db.META_SHOPPROFIL, "")
        pipeline.stufe1a_domain(self.conn, self.llm)
        pipeline.stufe1b_webscraper(self.conn, self.skael)
        pipeline.stufe1c_onlineshop(self.conn, self.llm)
        pipeline.stufe1d_webtraffic(self.conn, self.skael)
        db.set_meta(self.conn, db.META_SHOPPROFIL, PROFIL)
        pipeline.stufe1c_onlineshop(self.conn, self.llm)
        pipeline.stufe1e_uebergabe(self.conn)
        shop = self.conn.execute("SELECT * FROM shops WHERE firmenname='Grosshandel'").fetchone()
        self.assertEqual((shop["send"], shop["passt_profil"], shop["uebergeben"]), (1, 0, 0))
        gruende = {r["Firmenname"]: r["Grund"] for r in _csv(self.liste("Aussortiert"))}
        self.assertEqual(gruende["Grosshandel"], "passt nicht zum Shop-Profil: nur Gewerbekunden")

    def test_bewusst_ohne_profil_zaehlt_jeder_aktive_shop(self):
        db.set_meta(self.conn, db.META_SHOPPROFIL, "")
        shops = self.stufe1()
        self.assertFalse([n for n, _ in self.openai.prompts if n == "shopprofil"])
        self.assertEqual({n: s["uebergeben"] for n, s in shops.items()},
                         {"Endkunde": 1, "Grosshandel": 1, "Kaputt": 1})

    def test_set_prompt_shopprofil_setzt_nicht_exportierte_zurueck(self):
        db.set_meta(self.conn, db.META_SHOPPROFIL, PROFIL)
        self.stufe1()
        self.conn.execute("UPDATE anreicherung SET bereits_exportiert=1")   # Endkunde schon exportiert
        self.conn.commit()
        code, out, _ = _cli("set-prompt", "shopprofil", self.datei("profil.txt", PROFIL + "\nStrenger."))
        self.assertEqual(code, 0)
        # Grosshandel (abgelehnt) und Kaputt (Prüfung gescheitert, Versuch zählt neu)
        self.assertIn("2 noch nicht übergebene oder noch nicht exportierte Shops zurückgesetzt", out)
        shops = {r["firmenname"]: r for r in self.conn.execute("SELECT * FROM shops")}
        self.assertIsNone(shops["Grosshandel"]["passt_profil"])
        self.assertIsNone(shops["Grosshandel"]["profil_raw"])
        self.assertEqual((shops["Kaputt"]["attempts"], shops["Kaputt"]["error"]), (0, None))
        self.assertEqual(shops["Endkunde"]["passt_profil"], 1)            # exportiert: bleibt
        self.assertTrue(db.get_meta(self.conn, db.META_SHOPPROFIL).endswith("Strenger."))

        code, out, _ = _cli("set-prompt", "shopprofil", "--ohne")
        self.assertEqual(code, 0)
        self.assertEqual(db.get_meta(self.conn, db.META_SHOPPROFIL), "")

    def test_nachgeschaerftes_profil_prueft_testlauf_shops_neu(self):
        # Testlauf: Endkunde passt und wird übergeben und angereichert
        db.set_meta(self.conn, db.META_SHOPPROFIL, PROFIL)
        _anforderungen_setzen_ohne_profil(self.conn)
        self.stufe1()
        pipeline.stufe2a_website_final(self.conn, self.llm)
        pipeline.stufe2b_impressum(self.conn, self.skael)
        pipeline.stufe2c_emails(self.conn, self.skael, FakeFindymail())
        pipeline.stufe2d_anrede(self.conn, self.llm)
        pipeline.stufe2e_personalisierung(self.conn, self.skael, self.llm)
        pipeline.stufe2f_videotitel(self.conn, self.llm)
        pipeline.stufe2g_ready(self.conn)
        self.assertEqual(self.conn.execute("SELECT ready_to_send FROM anreicherung").fetchone()[0], 1)

        # Nutzer: „Endkunde ist drin, obwohl es eine Kette ist“ → Profil schärfen
        code, out, _ = _cli("set-prompt", "shopprofil", self.datei("profil.txt", PROFIL + "\nKeine Ketten."))
        self.assertEqual(code, 0, out)
        self.assertEqual(self.conn.execute("SELECT ready_to_send FROM anreicherung").fetchone()[0], 0)
        llm = LLM(client=KettenProfil(), skael=self.skael)
        pipeline.stufe1c_onlineshop(self.conn, llm)
        pipeline.stufe1d_webtraffic(self.conn, self.skael)
        pipeline.stufe1e_uebergabe(self.conn)
        pipeline.stufe2g_ready(self.conn)

        shop = self.conn.execute("SELECT * FROM shops WHERE firmenname='Endkunde'").fetchone()
        self.assertEqual((shop["passt_profil"], shop["profil_grund"]), (0, "Kette"))
        self.assertEqual(self.conn.execute("SELECT ready_to_send FROM anreicherung").fetchone()[0], 0)
        self.assertEqual(_csv(self.liste("Geschäftsführer")), [])
        gruende = [r["Grund"] for r in _csv(self.liste("Aussortiert")) if r["Firmenname"] == "Endkunde"]
        self.assertEqual(gruende, ["passt nicht zum Shop-Profil: Kette"])   # genau einmal

    def test_gescheiterte_pruefung_laeuft_mit_neuem_profil_wieder(self):
        db.set_meta(self.conn, db.META_SHOPPROFIL, PROFIL)
        for _ in range(3):
            self.stufe1()
        kaputt = self.conn.execute("SELECT * FROM shops WHERE firmenname='Kaputt'").fetchone()
        self.assertEqual((kaputt["attempts"], kaputt["passt_profil"]), (3, None))
        _cli("set-prompt", "shopprofil", self.datei("profil.txt", PROFIL + "\nNeu."))
        pipeline.stufe1c_onlineshop(self.conn, LLM(client=KettenProfil(), skael=self.skael))
        kaputt = self.conn.execute("SELECT * FROM shops WHERE firmenname='Kaputt'").fetchone()
        self.assertEqual(kaputt["passt_profil"], 1)

    def test_1d_und_1e_brauchen_entscheidung_zum_shop_profil(self):
        code, _, err = _cli("run", "--stage", "1d")
        self.assertEqual(code, 2)
        self.assertIn("Shop-Profil", err)
        self.assertTrue(pipeline.fehlende_anforderungen(self.conn, {"1e"}))
        self.assertEqual(pipeline.fehlende_anforderungen(self.conn, {"1a", "1b"}), [])

    def test_set_prompt_shopprofil_ohne_bodytext_wird_abgelehnt(self):
        code, _, err = _cli("set-prompt", "shopprofil", self.datei("profil.txt", "Passt {{website [Final]}}?"))
        self.assertEqual(code, 2)
        self.assertIn("{{BodyText}}", err)
        self.assertIsNone(db.get_meta(self.conn, db.META_SHOPPROFIL))


class AnforderungenTest(IsolierteDB):
    """Ohne geklärte Anforderungen startet kein Lauf – geprüft vor den Zugangsdaten."""

    def test_1c_braucht_entscheidung_zum_shop_profil(self):
        fehlt = pipeline.fehlende_anforderungen(self.conn, {"1c"})
        self.assertEqual(len(fehlt), 1)
        self.assertIn("Shop-Profil", fehlt[0])
        self.assertIn("prompts/shopprofil_builder.md", fehlt[0])
        self.assertEqual(len(pipeline.fehlende_anforderungen(self.conn, {"1d"})), 1)
        self.assertEqual(len(pipeline.fehlende_anforderungen(self.conn, {"1e"})), 1)
        db.set_meta(self.conn, db.META_SHOPPROFIL, "")          # bewusst ohne genügt
        self.assertEqual(pipeline.fehlende_anforderungen(self.conn, {"1c"}), [])
        self.assertEqual(pipeline.fehlende_anforderungen(self.conn, {"1a", "1b", "1d", "1e"}), [])

    def test_2e_braucht_personalisierung_und_mailtext(self):
        fehlt = pipeline.fehlende_anforderungen(self.conn, {"2e"})
        self.assertEqual(len(fehlt), 2)
        self.assertIn("Personalisierung", fehlt[0])
        self.assertIn("prompts/personalisierung_builder.md", fehlt[0])
        self.assertIn("Mailtext", fehlt[1])
        db.set_meta(self.conn, db.META_PERSONALISIERUNG, PERSONALISIERUNG)
        fehlt = pipeline.fehlende_anforderungen(self.conn, {"2e"})
        self.assertEqual(len(fehlt), 1)
        self.assertIn("Mailtext", fehlt[0])
        self.assertIn("Runde 2", fehlt[0])
        db.set_meta(self.conn, db.META_MAILTEXT, MAILTEXT)
        self.assertEqual(pipeline.fehlende_anforderungen(self.conn, {"2e"}), [])

    def test_2e_ohne_personalisierung_braucht_nichts(self):
        original = CONFIG.do_personalisierung
        CONFIG.do_personalisierung = False
        try:
            self.assertEqual(pipeline.fehlende_anforderungen(self.conn, {"2e"}), [])
        finally:
            CONFIG.do_personalisierung = original

    def test_run_bricht_vor_der_schluesselpruefung_ab(self):
        code, out, err = _cli("run", "--stage", "all")
        self.assertEqual(code, 2)
        self.assertIn("Anforderung fehlt", err)
        self.assertIn("shopprofil_builder.md", err)
        self.assertIn("Mailtext", err)
        self.assertNotIn("Zugangsdaten", err)

    def test_status_zeigt_anforderungen(self):
        code, out, _ = _cli("status")
        self.assertEqual(code, 0)
        self.assertIn("Anforderungen", out)
        self.assertIn("✗ fehlt — Builder: prompts/shopprofil_builder.md", out)
        self.assertIn("✗ fehlt — Builder: prompts/personalisierung_builder.md, Runde 2", out)
        db.set_meta(self.conn, db.META_SHOPPROFIL, "")
        _anforderungen_setzen_ohne_profil(self.conn)
        code, out, _ = _cli("status")
        self.assertIn("✓ bewusst ohne", out)
        self.assertIn("✓ gesetzt (Betreff: Kurze Frage zu {{Firmenname}})", out)
        self.assertNotIn("✗", out)


def _anforderungen_setzen_ohne_profil(conn) -> None:
    db.set_meta(conn, db.META_PERSONALISIERUNG, PERSONALISIERUNG)
    db.set_meta(conn, db.META_MAILTEXT, MAILTEXT)


class MailtextTest(unittest.TestCase):
    def fehler(self, text: str) -> str:
        return " | ".join(M.pruefen(text)[0])

    def test_gueltiger_mailtext(self):
        self.assertEqual(M.pruefen(MAILTEXT), ([], []))

    def test_betreff_fehlt(self):
        self.assertIn("Betreff:", self.fehler(MAILTEXT.split("\n", 2)[2]))
        self.assertIn("Betreff ist leer", self.fehler(MAILTEXT.replace("Betreff: Kurze Frage zu {{Firmenname}}",
                                                                        "Betreff:")))

    def test_unbekannter_platzhalter(self):
        self.assertIn("Unbekannter Platzhalter {{Firma}}", self.fehler(MAILTEXT.replace("{{Firmenname}}", "{{Firma}}")))
        self.assertIn("Unbekannter Platzhalter {{ansprache normal}}",
                      self.fehler(MAILTEXT.replace("{{Ansprache Normal}}", "{{ansprache normal}}")))
        self.assertIn("unvollständig", self.fehler(MAILTEXT.replace("{{Firmenname}}", "{{Firmenname}")))

    def test_personalisierung_fehlt(self):
        ohne = MAILTEXT.replace("{{Personalisierung}}\n\n", "")
        self.assertIn("{{Personalisierung}} fehlt", self.fehler(ohne))
        original = CONFIG.do_personalisierung
        CONFIG.do_personalisierung = False
        try:
            self.assertEqual(M.pruefen(ohne)[0], [])
            self.assertIn("ausgeschaltet", " ".join(M.pruefen(MAILTEXT)[1]))
        finally:
            CONFIG.do_personalisierung = original

    def test_begruessung_fehlt(self):
        self.assertIn("Begrüßung", self.fehler(MAILTEXT.replace("{{Ansprache Normal}},", "Hallo,")))

    def test_hinweis_bei_vorname(self):
        text = MAILTEXT.replace("Betreff: Kurze Frage", "Betreff: {{Vorname}}, kurze Frage")
        fehler, hinweise = M.pruefen(text)
        self.assertEqual(fehler, [])
        self.assertTrue(any("{{Vorname}}" in h and "Impressum" in h and "info@" in h for h in hinweise))

    def test_einfache_klammer(self):
        self.assertIn("richtig: {{Vorname}}",
                      self.fehler(MAILTEXT.replace("Viele Grüße", "Viele Grüße an {Vorname}")))
        self.assertIn("richtig: {{Firmenname}}", self.fehler(MAILTEXT.replace("{{Firmenname}}", "{ firmenname }")))
        fehler, hinweise = M.pruefen(MAILTEXT.replace("Viele Grüße", "Viele Grüße {Team}"))
        self.assertEqual(fehler, [])
        self.assertTrue(any("{Team}" in h for h in hinweise))

    def test_position_von_begruessung_und_satz(self):
        mitten = MAILTEXT.replace("{{Ansprache Normal}},\n\n", "Ich bin Erika.\n\n{{Ansprache Normal}},\n\n")
        self.assertIn("erste Zeile", self.fehler(mitten))
        im_ps = MAILTEXT.replace("{{Personalisierung}}\n\n", "") + "\nP.S. {{Personalisierung}}"
        self.assertIn("direkt unter der Begrüßung", self.fehler(im_ps))
        gleiche_zeile = MAILTEXT.replace("{{Ansprache Normal}},\n\n{{Personalisierung}}",
                                         "{{Ansprache Normal}}, {{Personalisierung}}")
        self.assertEqual(M.pruefen(gleiche_zeile)[0], [])

    def test_umlaut_aus_macos_datei(self):
        text = unicodedata.normalize("NFD", MAILTEXT.replace("{{Ansprache Normal}}", "{{Ansprache Persönlich}}"))
        self.assertEqual(M.pruefen(text)[0], [])

    def test_rendern_gf_und_info(self):
        gf = {"firmenname_final": "Shop GmbH", "personalisierung": "bei Ihnen fällt die Größenberatung auf.",
              **T.ansprachen("Herr", "Max", "Mueller", "max@shop.de")}
        betreff, text = M.rendern(MAILTEXT, gf)
        self.assertEqual(betreff, "Kurze Frage zu Shop GmbH")
        self.assertTrue(text.startswith("Hallo Herr Mueller,\n\nbei Ihnen fällt die Größenberatung auf.\n\n"))
        self.assertNotIn("{{", text)

        info = {"firmenname_final": "", "firmenname": "Info Shop", "personalisierung": "bei Ihnen …",
                **T.ansprachen(None, "", "", "info@info-shop.de")}
        betreff, text = M.rendern(MAILTEXT.replace("{{Ansprache Normal}}", "{{Ansprache Guten Tag}}"), info)
        self.assertEqual(betreff, "Kurze Frage zu Info Shop")   # Rückfall auf den Import-Namen
        self.assertTrue(text.startswith("Guten Tag,\n\nbei Ihnen …"))


class ReadyToSendTest(IsolierteDB):
    def test_ohne_ansprache_nicht_versandfertig(self):
        # Anrede-KI scheitert, Personalisierung und Videotitel klappen → keine Mail mit leerem Gruß
        db.insert_ignore(self.conn, "shops", {"import_key": "a.de", "firmenname": "A", "website": "a.de"})
        db.set_meta(self.conn, db.META_SHOPPROFIL, "")
        _anforderungen_setzen_ohne_profil(self.conn)
        skael = FakeSkael()
        llm = LLM(client=AnredeKaputt(), skael=skael)
        pipeline.stufe1a_domain(self.conn, llm)
        pipeline.stufe1b_webscraper(self.conn, skael)
        pipeline.stufe1c_onlineshop(self.conn, llm)
        pipeline.stufe1d_webtraffic(self.conn, skael)
        pipeline.stufe1e_uebergabe(self.conn)
        pipeline.stufe2a_website_final(self.conn, llm)
        pipeline.stufe2b_impressum(self.conn, skael)
        pipeline.stufe2c_emails(self.conn, skael, FakeFindymail())
        pipeline.stufe2d_anrede(self.conn, llm)
        pipeline.stufe2e_personalisierung(self.conn, skael, llm)
        pipeline.stufe2f_videotitel(self.conn, llm)
        pipeline.stufe2g_ready(self.conn)
        lead = self.conn.execute("SELECT * FROM anreicherung").fetchone()
        self.assertIsNone(lead["anrede"])
        self.assertTrue(lead["personalisierung"])
        self.assertEqual(lead["ready_to_send"], 0)
        self.assertEqual(_csv(self.liste("Geschäftsführer")), [])

        pipeline.stufe2d_anrede(self.conn, LLM(client=FakeOpenAI(), skael=skael))   # nächster Lauf klappt
        pipeline.stufe2g_ready(self.conn)
        (zeile,) = _csv(self.liste("Geschäftsführer"))
        self.assertTrue(zeile["Mailtext"].startswith("Hallo Herr Mueller,\n\n"))


class ExportMailtextTest(IsolierteDB):
    """Liste 1 und 2 bekommen Betreff und Mailtext nur, wenn ein Mailtext hinterlegt ist."""

    def setUp(self):
        super().setUp()
        for key, name, typ, email, anrede, vorname, nachname in (
                ("gf-shop.de", "GF Shop GmbH", "GF", "max.mueller@gf-shop.de", "Herr", "Max", "Mueller"),
                ("info-shop.de", "Info Shop GmbH", "Info@", "info@info-shop.de", None, "", "")):
            db.insert_ignore(self.conn, "shops", {"import_key": key, "firmenname": name, "website": key,
                                                  "uebergeben": 1, "send": 1})
            shop_id = self.conn.execute("SELECT id FROM shops WHERE import_key=?", (key,)).fetchone()[0]
            db.insert_ignore(self.conn, "anreicherung", {
                "shop_id": shop_id, "firmenname": name, "firmenname_final": name,
                "website_final": f"https://www.{key}", "email_final": email, "email_final_type": typ,
                "dedupe_status": "kept", "ready_to_send": 1, "anrede": anrede or "", "first_name": vorname,
                "last_name": nachname, "personalisierung": "bei Ihnen ist das Sortiment klar gegliedert.",
                "video_title": "Video", **T.ansprachen(anrede, vorname, nachname, email)})

    def test_ohne_mailtext_keine_zusatzspalten(self):
        kopf = _kopf(self.liste("Geschäftsführer"))
        self.assertNotIn("Betreff", kopf)
        self.assertNotIn("Mailtext", kopf)

    def test_mit_mailtext_betreff_und_text_nach_videotitel(self):
        db.set_meta(self.conn, db.META_MAILTEXT, MAILTEXT)
        for liste, erwartet in (("Geschäftsführer", "Hallo Herr Mueller,\n\nbei Ihnen ist das Sortiment"),
                                ("info@", "Hallo,\n\nbei Ihnen ist das Sortiment")):
            pfad = self.liste(liste)
            kopf = _kopf(pfad)
            pos = kopf.index("Videotitel")
            self.assertEqual(kopf[pos + 1:pos + 3], ["Betreff", "Mailtext"])
            (zeile,) = _csv(pfad)
            self.assertTrue(zeile["Mailtext"].startswith(erwartet), zeile["Mailtext"])
            self.assertEqual(zeile["Betreff"], f"Kurze Frage zu {zeile['Firmenname']}")
        kopf = _kopf(self.liste("Aussortiert"))
        self.assertNotIn("Mailtext", kopf)

    def test_fehlerhafter_mailtext_stoppt_export(self):
        db.set_meta(self.conn, db.META_MAILTEXT, MAILTEXT.replace("{{Firmenname}}", "{{Firma}}"))
        with self.assertRaises(SystemExit) as ctx:
            export_mod.export_listen(self.conn)
        self.assertIn("{{Firma}}", str(ctx.exception.code))


class SetPromptMailtextTest(IsolierteDB):
    def setUp(self):
        super().setUp()
        db.insert_ignore(self.conn, "shops", {"import_key": "a.de", "firmenname": "A", "website": "a.de"})
        shop_a = self.conn.execute("SELECT id FROM shops").fetchone()[0]
        db.insert_ignore(self.conn, "shops", {"import_key": "b.de", "firmenname": "B", "website": "b.de"})
        shop_b = self.conn.execute("SELECT id FROM shops WHERE import_key='b.de'").fetchone()[0]
        for shop_id, name, exportiert in ((shop_a, "A", 1), (shop_b, "B", 0)):
            db.insert_ignore(self.conn, "anreicherung", {
                "shop_id": shop_id, "firmenname": name, "email_final": f"info@{name.lower()}.de",
                "personalisierung": "bei Ihnen alter Satz.", "ready_to_send": 1, "bereits_exportiert": exportiert})

    def leads(self) -> dict:
        return {r["firmenname"]: r for r in self.conn.execute("SELECT * FROM anreicherung")}

    def test_set_prompt_personalisierung_setzt_nicht_exportierte_zurueck(self):
        code, out, _ = _cli("set-prompt", "personalisierung", self.datei("p.txt", PERSONALISIERUNG))
        self.assertEqual(code, 0)
        self.assertIn("1 noch nicht exportierte Leads zurückgesetzt", out)
        leads = self.leads()
        self.assertEqual((leads["A"]["personalisierung"], leads["A"]["ready_to_send"]), ("bei Ihnen alter Satz.", 1))
        self.assertEqual((leads["B"]["personalisierung"], leads["B"]["ready_to_send"]), (None, 0))
        self.assertEqual(db.get_meta(self.conn, db.META_PERSONALISIERUNG), PERSONALISIERUNG)

    def test_set_prompt_personalisierung_gibt_neue_versuche(self):
        self.conn.execute("UPDATE anreicherung SET attempts=3, error='Videotitel-KI fehlgeschlagen'")
        self.conn.commit()
        _cli("set-prompt", "personalisierung", self.datei("p.txt", PERSONALISIERUNG))
        b = self.leads()["B"]
        self.assertEqual((b["attempts"], b["error"]), (0, None))     # 2e schreibt den Satz wirklich neu
        self.assertEqual(self.leads()["A"]["attempts"], 3)          # exportiert: unverändert

    def test_set_prompt_personalisierung_ohne_bodytext_wird_abgelehnt(self):
        code, _, err = _cli("set-prompt", "personalisierung", self.datei("p.txt", "Schreibe etwas über {{Mailtext}}"))
        self.assertEqual(code, 2)
        self.assertIn("{{Bodytext Website}}", err)
        self.assertEqual(self.leads()["B"]["personalisierung"], "bei Ihnen alter Satz.")
        code, _, err = _cli("set-prompt", "personalisierung", "--ohne")
        self.assertEqual(code, 2)

    def test_set_mailtext_speichert_und_zeigt_vorschau(self):
        code, out, _ = _cli("set-mailtext", self.datei("mail.txt", "\ufeff" + MAILTEXT.replace("\n", "\r\n")))
        self.assertEqual(code, 0, out)
        self.assertIn("Betreff: Kurze Frage zu Beispiel Shop GmbH", out)
        self.assertIn("Hallo Herr Mustermann,\n\nbei Ihnen fällt sofort auf", out)
        self.assertEqual(db.get_meta(self.conn, db.META_MAILTEXT), MAILTEXT.strip())
        self.assertNotIn("Hinweis", out)       # kein Personalisierungs-Prompt mit {{Mailtext}} hinterlegt

    def test_set_mailtext_hinweis_wenn_saetze_neu_noetig(self):
        db.set_meta(self.conn, db.META_PERSONALISIERUNG, PERSONALISIERUNG)
        code, out, _ = _cli("set-mailtext", self.datei("mail.txt", MAILTEXT))
        self.assertEqual(code, 0)
        self.assertIn("1 persönliche Sätze wurden mit dem alten Mailtext geschrieben", out)
        self.assertEqual(self.leads()["B"]["personalisierung"], "bei Ihnen alter Satz.")   # kein Auto-Reset

    def test_set_mailtext_mit_fehlern_wird_nicht_gespeichert(self):
        code, _, err = _cli("set-mailtext", self.datei("mail.txt", MAILTEXT.split("\n", 2)[2]))
        self.assertEqual(code, 2)
        self.assertIn("Betreff:", err)
        self.assertIsNone(db.get_meta(self.conn, db.META_MAILTEXT))


class ImportSpaltenTest(unittest.TestCase):
    def test_builtwith_export_wird_erkannt(self):
        from ecom.cli import NAME_SPALTEN, WEB_SPALTEN, _spalte
        header = ["Root Domain", "Location on Site", "Primary Domain", "Company", "Emails"]
        # "Location on Site" zeigt Shops auf Subdomains (shop.firma.de), "Root Domain" nur firma.de
        self.assertEqual(_spalte(header, WEB_SPALTEN, None), "Location on Site")
        self.assertEqual(_spalte(header, NAME_SPALTEN, None), "Company")


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


class Skael401(FakeSkael):
    def web_scraper(self, url):
        self.calls.append(("web_scraper", url))
        raise ApiError("HTTP 401", 401, {"message": "Unauthenticated."})


class SkaelGestoert(FakeSkael):
    def web_scraper(self, url):
        raise ApiError("web_scraper: HTTP 0 nach 1 Versuchen")      # z. B. kein Internet


class OpenAIOhneGuthaben(FakeOpenAI):
    def complete(self, prompt, **kwargs):
        raise ApiError("OpenAI HTTP 429", 429, {"error": {"code": "insufficient_quota", "type": "insufficient_quota"}})


class ZugangUndFehlerTest(IsolierteDB):
    """Falscher Schlüssel kostet keine Versuche; Fehler sind sichtbar; liegen gebliebene Zeilen laufen wieder."""

    def setUp(self):
        super().setUp()
        for key in ("a-shop.de", "b-shop.de", "c-shop.de"):
            db.insert_ignore(self.conn, "shops", {"import_key": key, "firmenname": key, "website": key,
                                                  "website_final": key})

    def shops(self) -> list:
        return self.conn.execute("SELECT * FROM shops ORDER BY id").fetchall()

    def test_platzhalter_schluessel_startet_keinen_lauf(self):
        with _einstellung(skael_api_key="eak_dein_key_hier"), _skael_im_cli(Skael401):
            code, _, err = _cli("run", "--stage", "1b")
        self.assertEqual(code, 2)
        self.assertIn("SKAEL_API_KEY in .env ist noch der Platzhalter", err)
        self.assertEqual([s["attempts"] for s in self.shops()], [0, 0, 0])

    def test_falscher_schluessel_stoppt_stufe_ohne_fehlversuch(self):
        with _einstellung(skael_api_key="eak_falsch123"):
            with _skael_im_cli(Skael401):
                code, _, err = _cli("run", "--stage", "1b")
            self.assertEqual(code, 2)
            self.assertIn("Skael lehnt den Zugang ab: Schlüssel falsch oder abgelaufen (HTTP 401)", err)
            self.assertIn("SKAEL_API_KEY", err)
            self.assertEqual([(s["attempts"], s["error"]) for s in self.shops()], [(0, None)] * 3)
            with _skael_im_cli(FakeSkael):                      # Schlüssel repariert: derselbe Befehl läuft
                code, _, _ = _cli("run", "--stage", "1b")
        self.assertEqual(code, 0)
        self.assertTrue(all(s["bodytext"] for s in self.shops()))

    def test_openai_ohne_guthaben_stoppt_stufe(self):
        self.conn.execute("UPDATE shops SET webscraper_raw='{}', bodytext='Warenkorb'")
        self.conn.commit()
        with self.assertRaises(ZugangGesperrt) as ctx:
            pipeline.stufe1c_onlineshop(self.conn, LLM(client=OpenAIOhneGuthaben(), skael=FakeSkael()))
        self.assertIn("OpenAI lehnt den Zugang ab: Konto ohne Guthaben", str(ctx.exception))
        self.assertEqual([(s["attempts"], s["icp_raw"]) for s in self.shops()], [(0, None)] * 3)

    def test_fehler_sichtbar_und_zuruecksetzbar(self):
        with _einstellung(skael_api_key="eak_test123"), _skael_im_cli(SkaelGestoert):
            for _ in range(3):
                code, out, err = _cli("run", "--stage", "1b")
                self.assertEqual(code, 1)                       # jede Zeile gescheitert → kein Exit-Code 0
            self.assertIn("Stufe 1b: 3/3 (3 Fehler)", err)
            self.assertIn("Stufe 1b: alle 3 Zeilen fehlgeschlagen", err)
            self.assertIn("fehler-zuruecksetzen", err)
            self.assertIn("mit Fehler / liegen gebl.  3 / 3   häufigster Grund: Webscraper: web_scraper: HTTP 0", out)
            self.assertIn("Liegen geblieben", out)

            with _skael_im_cli(FakeSkael):                      # Internet wieder da, aber Versuche aufgebraucht
                code, _, err = _cli("run", "--stage", "1b")
                self.assertIn("nichts zu tun", err)
                code, out, _ = _cli("fehler-zuruecksetzen")
                self.assertEqual(code, 0)
                self.assertIn("3 Shops und 0 Leads bekommen neue Versuche", out)
                code, out, _ = _cli("run", "--stage", "1b")
        self.assertEqual(code, 0)
        self.assertTrue(all(s["bodytext"] for s in self.shops()))
        self.assertIn("mit Fehler / liegen gebl.  0 / 0", out)
        gruende = {r["Firmenname"]: r["Grund"] for r in _csv(self.liste("Aussortiert"))}
        self.assertEqual(gruende["a-shop.de"], "Shop-Prüfung ausstehend")

    def test_zuruecksetzen_laesst_exportierte_leads_in_ruhe(self):
        shop_id = self.shops()[0]["id"]
        db.insert_ignore(self.conn, "anreicherung", {"shop_id": shop_id, "bereits_exportiert": 1, "attempts": 3,
                                                     "error": "alt"})
        _cli("fehler-zuruecksetzen")
        lead = self.conn.execute("SELECT attempts, error FROM anreicherung").fetchone()
        self.assertEqual((lead["attempts"], lead["error"]), (3, "alt"))

    def test_1e_und_2g_brauchen_keinen_schluessel(self):
        db.set_meta(self.conn, db.META_SHOPPROFIL, "")
        with _einstellung(skael_api_key="", openai_api_key=""):
            self.assertEqual(_cli("run", "--stage", "1e")[0], 0)
            self.assertEqual(_cli("run", "--stage", "2g")[0], 0)
            code, _, err = _cli("run", "--stage", "1b")
        self.assertEqual(code, 1)
        self.assertIn("SKAEL_API_KEY", err)


class EchteClientsZugangTest(IsolierteDB):
    """Die echten Clients mit gestellten HTTP-Antworten: Status und Fehlertext kommen bis zur Stufe durch."""

    def setUp(self):
        super().setUp()
        self.original = clients._request
        db.insert_ignore(self.conn, "shops", {"import_key": "a.de", "firmenname": "A", "website": "a.de",
                                              "website_final": "a.de", "webscraper_raw": "{}",
                                              "bodytext": "Warenkorb"})
        db.insert_ignore(self.conn, "shops", {"import_key": "b.de", "firmenname": "B", "website": "b.de",
                                              "website_final": "b.de"})

    def tearDown(self):
        clients._request = self.original
        super().tearDown()

    def antwort(self, status, data):
        self.anfragen = 0

        def fake(url, *, method="POST", headers=None, body=None, timeout=None):
            self.anfragen += 1
            return status, data
        clients._request = fake

    def test_skael_401(self):
        self.antwort(401, {"message": "Unauthenticated."})
        with self.assertRaises(ZugangGesperrt):
            pipeline.stufe1b_webscraper(self.conn, clients.SkaelClient(api_key="eak_x"))
        self.assertEqual(self.anfragen, 1)
        b = self.conn.execute("SELECT attempts, error FROM shops WHERE import_key='b.de'").fetchone()
        self.assertEqual((b["attempts"], b["error"]), (0, None))

    def test_openai_ohne_guthaben(self):
        self.antwort(429, {"error": {"code": "insufficient_quota", "type": "insufficient_quota"}})
        llm = LLM(client=clients.OpenAIClient(api_key="sk-x"), skael=FakeSkael())
        with self.assertRaises(ZugangGesperrt):
            pipeline.stufe1c_onlineshop(self.conn, llm)
        a = self.conn.execute("SELECT attempts, icp_raw FROM shops WHERE import_key='a.de'").fetchone()
        self.assertEqual((a["attempts"], a["icp_raw"]), (0, None))

    def test_openai_ueberlastet_zaehlt_als_fehlversuch(self):
        self.antwort(429, {"error": {"code": "rate_limit_exceeded", "type": "requests"}})
        pipeline.stufe1c_onlineshop(self.conn, LLM(client=clients.OpenAIClient(api_key="sk-x"), skael=FakeSkael()))
        a = self.conn.execute("SELECT attempts, error FROM shops WHERE import_key='a.de'").fetchone()
        self.assertEqual((a["attempts"], a["error"]), (1, "ICP ONLINE SHOP fehlgeschlagen"))


class ImportTest(IsolierteDB):
    """Was Nutzer typischerweise mitbringen: Excel-CSV (Windows-1252), Unicode-Text, .xlsx, www-Varianten."""

    def roh(self, name: str, daten: bytes) -> str:
        pfad = self.ordner / name
        pfad.write_bytes(daten)
        return str(pfad)

    def namen(self) -> list[str]:
        return [r[0] for r in self.conn.execute("SELECT firmenname FROM shops ORDER BY id")]

    def test_excel_csv_windows_1252(self):
        text = "Firmenname;Website\r\nMüller Schuhe GmbH;www.mueller-schuhe.de\r\nGrüße & Söhne;gruesse.de\r\n"
        code, out, err = _cli("import", self.roh("excel.csv", text.encode("cp1252")))
        self.assertEqual(code, 0, err)
        self.assertIn("gelesen als Windows-1252", out)
        self.assertEqual(self.namen(), ["Müller Schuhe GmbH", "Grüße & Söhne"])

    def test_excel_unicode_text_utf16(self):
        text = "Firmenname\tWebsite\r\nMüller Schuhe GmbH\twww.mueller-schuhe.de\r\n"
        code, _, err = _cli("import", self.roh("excel.txt", text.encode("utf-16")))
        self.assertEqual(code, 0, err)
        self.assertEqual(self.namen(), ["Müller Schuhe GmbH"])

    def test_xlsx_wird_mit_anleitung_abgelehnt(self):
        for name in ("liste.xlsx", "liste_falsch_benannt.csv"):
            code, _, err = _cli("import", self.roh(name, b"PK\x03\x04\x14\x00\x06\x00rest"))
            self.assertEqual(code, 2, name)
            self.assertIn("CSV UTF-8", err)
        self.assertEqual(self.namen(), [])

    def test_www_varianten_sind_ein_shop(self):
        code, out, _ = _cli("import", self.datei("www.csv", "Firma;Website\nA;www.shop-x.de\nB;https://www.shop-x.de\n"
                                                            "C;SHOP-X.de\n"))
        self.assertEqual(code, 0)
        self.assertIn("1 Shops neu angelegt, 2 schon vorhanden", out)

    def test_alte_schluessel_mit_www_werden_angeglichen(self):
        for key in ("www.alt.de", "www.beide.de", "beide.de"):
            db.insert_ignore(self.conn, "shops", {"import_key": key, "firmenname": key})
        db.init(self.conn)
        keys = {r[0] for r in self.conn.execute("SELECT import_key FROM shops")}
        self.assertEqual(keys, {"alt.de", "www.beide.de", "beide.de"})
        code, out, _ = _cli("import", self.datei("alt.csv", "Firma;Website\nAlt;www.alt.de\n"))
        self.assertIn("0 Shops neu angelegt, 1 schon vorhanden", out)

    def test_ohne_website_gezaehlt_und_status_zaehlt_website_aus_liste(self):
        code, out, _ = _cli("import", str(ROOT / "beispiel" / "shops_beispiel.csv"))
        self.assertEqual(code, 0)
        self.assertIn("3 Shops neu angelegt", out)
        self.assertIn("Davon ohne Website: 1 – für diese sucht die KI", out)
        code, out, _ = _cli("status", "--shops", "5")
        self.assertIn("mit Website                2", out)
        self.assertIn("Die ersten 3 Shops", out)
        self.assertIn("Stand: noch nicht geprüft", out)

    def test_mailtext_aus_ansi_datei(self):
        code, out, err = _cli("set-mailtext", self.roh("mail.txt", MAILTEXT.encode("cp1252")))
        self.assertEqual(code, 0, err)
        self.assertIn("gelesen als Windows-1252", out)
        self.assertIn("Viele Grüße", db.get_meta(self.conn, db.META_MAILTEXT))

    def test_env_mit_bom_oder_ansi(self):
        for name, daten in (("bom.env", "﻿ECOM_TEST_BOM=ja\n".encode("utf-8")),
                            ("ansi.env", "ECOM_TEST_ANSI=Müller\n".encode("cp1252"))):
            config._load_dotenv(Path(self.roh(name, daten)))
        try:
            self.assertEqual(os.environ.get("ECOM_TEST_BOM"), "ja")
            self.assertEqual(os.environ.get("ECOM_TEST_ANSI"), "Müller")
        finally:
            os.environ.pop("ECOM_TEST_BOM", None)
            os.environ.pop("ECOM_TEST_ANSI", None)


class AusgabeTest(IsolierteDB):
    def test_befehle_ueberleben_cp1252_ausgabe(self):
        # Windows mit umgeleiteter Ausgabe (Claude Code, Git Bash, Pipe): stdout ist cp1252, ✓/✗/─ ließen print abstürzen
        env = {**os.environ, "PYTHONIOENCODING": "cp1252", "DB_PATH": str(self.ordner / "cp.db")}
        for befehl in (["status", "--shops"], ["doctor"], ["set-mailtext", "beispiel/mailtext_beispiel.txt"]):
            ergebnis = subprocess.run([sys.executable, "-m", "ecom", *befehl], cwd=ROOT, env=env,
                                      capture_output=True, timeout=120)
            self.assertEqual(ergebnis.returncode, 0, (befehl, ergebnis.stderr.decode("utf-8", "replace")))
            self.assertNotIn(b"UnicodeEncodeError", ergebnis.stderr)

    def test_doctor_nennt_fehlende_sperrlisten_adresse(self):
        code, out, _ = _cli("doctor")
        self.assertEqual(code, 0)
        self.assertIn("Community-Sperrliste nicht eingerichtet", out)
        self.assertIn("Platzhalter OWNER", out)


class ListeDreiUndMarkierenTest(IsolierteDB):
    def lead(self, name: str, **felder) -> None:
        key = name.lower().replace(" ", "-") + ".de"
        db.insert_ignore(self.conn, "shops", {"import_key": key, "firmenname": name, "website": key,
                                              "uebergeben": 1, "send": 1})
        shop_id = self.conn.execute("SELECT id FROM shops WHERE import_key=?", (key,)).fetchone()[0]
        db.insert_ignore(self.conn, "anreicherung", {
            "shop_id": shop_id, "firmenname": name, "firmenname_final": name, "website_final": f"https://{key}",
            "email_final": f"info@{key}", "email_final_type": "Info@", "dedupe_status": "kept", "anrede": "",
            "personalisierung": "bei Ihnen …", "video_title": "Video", **felder})

    def test_lead_mit_email_aber_nicht_versandfertig_steht_in_liste_3(self):
        self.lead("A GmbH", ready_to_send=1)
        self.lead("B GmbH", personalisierung=None, attempts=3, error="Personalisierungs-KI fehlgeschlagen")
        self.lead("C GmbH", video_title=None)
        zeilen = {r["Firmenname"]: r for r in _csv(self.liste("Aussortiert"))}
        self.assertNotIn("A GmbH", zeilen)
        self.assertEqual(zeilen["B GmbH"]["Grund"], "nicht versandfertig: kein persönlicher Satz – nach 3 "
                                                    "Fehlversuchen liegen geblieben (fehler-zuruecksetzen)")
        self.assertEqual(zeilen["B GmbH"]["Letzte Fehlermeldung"], "Personalisierungs-KI fehlgeschlagen")
        self.assertEqual(zeilen["C GmbH"]["Grund"], "nicht versandfertig: Videotitel fehlt")
        self.assertEqual([r["Firmenname"] for r in _csv(self.liste("info@"))], ["A GmbH"])

    def test_mark_trennt_versandfertige_und_gesperrte(self):
        self.lead("Frei GmbH", ready_to_send=1)
        self.lead("Abmahner GmbH", ready_to_send=1)
        original = sperrliste_mod.laden
        sperrliste_mod.laden = lambda **_: sperrliste_mod.Sperrliste({"abmahner-gmbh.de"}, "Test")
        try:
            code, out, _ = _cli("export", "--mark")
            self.assertEqual(code, 0)
            self.assertIn("2 Leads als 'bereits exportiert' markiert: 1 versandfertige (Liste 1 und 2) "
                          "und 1 gesperrte (Liste 4, nie anschreiben)", out)
            code, out, _ = _cli("export", "--mark")
            self.assertIn("0 Leads als 'bereits exportiert' markiert", out)
        finally:
            sperrliste_mod.laden = original


if __name__ == "__main__":
    unittest.main()
