"""Offline tests for werkzeuge/hostinger.py (HTTP and ssh are mocked)."""
from __future__ import annotations

import base64
import email.message
import importlib.util
import io
import json
import subprocess
import tempfile
import unittest
import urllib.error
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

HIER = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("hostinger", HIER / "werkzeuge" / "hostinger.py")
hostinger = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hostinger)

TOKEN = "TESTTOKEN_abc123_geheim"
SECRET = "whsec_SUPERGEHEIM_42"
MELDUNG = "https://n8n.example/webhook/GEHEIMPFAD"

VMS = [{
    "id": 1268054, "hostname": "srv1268054.hstgr.cloud", "state": "running", "plan": "KVM 1",
    "data_center_id": 17, "ipv4": [{"id": 1, "address": "203.0.113.10", "ptr": None}], "ipv6": None,
    "template": {"id": 1077, "name": "Ubuntu 24.04 LTS", "description": "Ubuntu 24.04 LTS"},
}]
ZENTREN = [{"id": 17, "name": "fra", "location": "de", "city": "Frankfurt", "continent": "Europe"}]


class Antwort:
    def __init__(self, daten):
        self.roh = json.dumps(daten).encode()

    def read(self):
        return self.roh

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def http_fehler(url: str, code: int, daten: dict) -> urllib.error.HTTPError:
    return urllib.error.HTTPError(url, code, "x", email.message.Message(), io.BytesIO(json.dumps(daten).encode()))


class FakeApi:
    """Routes (method, path) to canned answers and records every request."""

    def __init__(self, routen: dict):
        self.routen = routen
        self.anfragen: list[tuple[str, str, dict, dict | None]] = []

    def __call__(self, req, timeout=None):
        pfad = req.full_url.replace(hostinger.API, "")
        body = json.loads(req.data) if req.data else None
        self.anfragen.append((req.get_method(), pfad, dict(req.header_items()), body))
        antwort = self.routen.get((req.get_method(), pfad))
        if antwort is None:
            raise http_fehler(req.full_url, 404, {"message": "Not found", "correlation_id": "c-1"})
        if isinstance(antwort, Exception):
            raise antwort
        return Antwort(antwort)


class Basis(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.env = Path(self.tmp.name) / ".env"
        self.env.write_text(
            "# Zugang\n"
            f'export HOSTINGER_API_TOKEN="{TOKEN}"\n'
            f"SKAEL_WEBHOOK_SECRET='{SECRET}'\n"
            f"MELDUNG_URL={MELDUNG}\n", encoding="utf-8")
        self.patches = [mock.patch.object(hostinger, "ENV_DATEI", self.env),
                        mock.patch.object(hostinger.time, "sleep", lambda *_: None)]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in self.patches:
            p.stop()
        self.tmp.cleanup()

    def ausfuehren(self, argv, api: FakeApi | None = None):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            if api is not None:
                with mock.patch.object(hostinger.urllib.request, "urlopen", api):
                    code = hostinger.main(argv)
            else:
                code = hostinger.main(argv)
        return code, out.getvalue() + err.getvalue()

    def assertKeinGeheimnis(self, text: str):
        for wert in (TOKEN, SECRET, MELDUNG, "GEHEIMPFAD"):
            self.assertNotIn(wert, text)


class TokenTest(Basis):
    def test_token_wird_geladen_ohne_ausgabe(self):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            token = hostinger.token_holen(self.env)
        self.assertEqual(token, TOKEN)
        self.assertEqual(out.getvalue() + err.getvalue(), "")

    def test_fehlender_token_klare_meldung(self):
        self.env.write_text("HOSTINGER_API_TOKEN=<dein-schluessel>\n", encoding="utf-8")
        with mock.patch.dict(hostinger.os.environ, {}, clear=True):
            code, text = self.ausfuehren(["pruefen"])
        self.assertEqual(code, 1)
        self.assertIn("FEHLER:", text)
        self.assertIn("WAS TUN:", text)
        self.assertIn("02_hostinger-vps.md", text)

    def test_abgelehnter_token_zeigt_ihn_nicht(self):
        api = FakeApi({("GET", "/api/vps/v1/virtual-machines"):
                       http_fehler("u", 401, {"message": "Unauthenticated.", "correlation_id": "c"})})
        code, text = self.ausfuehren(["pruefen"], api)
        self.assertEqual(code, 1)
        self.assertIn("lehnt den API-Schlüssel ab", text)
        self.assertKeinGeheimnis(text)


class PruefenTest(Basis):
    def test_listet_vms(self):
        api = FakeApi({("GET", "/api/vps/v1/virtual-machines"): VMS, ("GET", "/api/vps/v1/data-centers"): ZENTREN})
        code, text = self.ausfuehren(["pruefen"], api)
        self.assertEqual(code, 0)
        self.assertIn("API-Schlüssel ist gültig", text)
        for erwartet in ("1268054", "srv1268054.hstgr.cloud", "203.0.113.10", "läuft", "Ubuntu 24.04 LTS",
                         "Frankfurt, DE", "KVM 1", "schluessel --vm 1268054"):
            self.assertIn(erwartet, text)
        self.assertKeinGeheimnis(text)
        methode, pfad, kopf, _ = api.anfragen[0]
        self.assertEqual((methode, pfad), ("GET", "/api/vps/v1/virtual-machines"))
        self.assertEqual(kopf.get("Authorization"), f"Bearer {TOKEN}")

    def test_falsches_os_und_keine_vms(self):
        vm = dict(VMS[0], template={"name": "AlmaLinux 9 with CyberPanel"})
        api = FakeApi({("GET", "/api/vps/v1/virtual-machines"): [vm], ("GET", "/api/vps/v1/data-centers"): ZENTREN})
        code, text = self.ausfuehren(["pruefen"], api)
        self.assertIn("erwartet wird Ubuntu 24.04", text)
        api = FakeApi({("GET", "/api/vps/v1/virtual-machines"): [], ("GET", "/api/vps/v1/data-centers"): ZENTREN})
        code, text = self.ausfuehren(["pruefen"], api)
        self.assertEqual(code, 2)
        self.assertIn("Kein VPS", text)


class DnsTest(Basis):
    def test_domain_nicht_bei_hostinger(self):
        api = FakeApi({})  # every call -> 404
        code, text = self.ausfuehren(["dns", "--domain", "kunde.de", "--name", "angebot", "--ip", "203.0.113.10"], api)
        self.assertEqual(code, 2)
        self.assertIn("nicht in diesem Hostinger-Konto", text)
        self.assertIn("anleitungen/03_dns.md", text)
        self.assertIn("Typ A, Name angebot, Ziel 203.0.113.10", text)
        self.assertFalse([a for a in api.anfragen if a[0] == "PUT"])
        self.assertKeinGeheimnis(text)

    def test_setzt_a_record(self):
        zone = [{"name": "@", "type": "A", "ttl": 14400, "records": [{"content": "198.51.100.1", "is_disabled": False}]}]
        api = FakeApi({
            ("GET", "/api/dns/v1/zones/kunde.de"): zone,
            ("POST", "/api/dns/v1/zones/kunde.de/validate"): {"message": "Request accepted"},
            ("PUT", "/api/dns/v1/zones/kunde.de"): {"message": "Request accepted"},
            ("GET", "/api/domains/v1/portfolio/kunde.de"): {"domain": "kunde.de", "name_servers": {"ns1": "a.dns", "ns2": "b.dns"}},
        })
        code, text = self.ausfuehren(["dns", "--domain", "kunde.de", "--name", "angebot.kunde.de", "--ip", "203.0.113.10"], api)
        self.assertEqual(code, 0, text)
        put = [a for a in api.anfragen if a[0] == "PUT"][0]
        self.assertEqual(put[3], {"overwrite": True, "zone": [
            {"name": "angebot", "type": "A", "ttl": 300, "records": [{"content": "203.0.113.10"}]}]})
        self.assertIn("A-Record gesetzt: angebot.kunde.de -> 203.0.113.10", text)

    def test_ungueltige_ip(self):
        code, text = self.ausfuehren(["dns", "--domain", "kunde.de", "--name", "angebot", "--ip", "999.1.1.1"])
        self.assertEqual(code, 1)
        self.assertIn("keine IPv4-Adresse", text)


class GeheimnisTest(Basis):
    def test_geheimnis_nicht_in_ausgabe_und_nicht_in_befehlszeile(self):
        aufrufe = []

        def fake_run(args, input=None, capture_output=False, **kw):
            aufrufe.append((args, input))
            return subprocess.CompletedProcess(args, 0, b"", b"")

        api = FakeApi({("GET", "/api/vps/v1/virtual-machines/1268054"): VMS[0]})
        schluessel = Path(self.tmp.name) / "id_ed25519"
        schluessel.write_text("x")
        with mock.patch.object(hostinger.subprocess, "run", fake_run), \
                mock.patch.object(hostinger, "SCHLUESSEL", schluessel), \
                mock.patch.object(hostinger.shutil, "which", lambda n: f"/usr/bin/{n}"):
            code, text = self.ausfuehren(["geheimnis", "--vm", "1268054"], api)
        self.assertEqual(code, 0, text)
        self.assertIn("SKAEL_WEBHOOK_SECRET", text)
        self.assertKeinGeheimnis(text)
        args, eingabe = aufrufe[-1]
        self.assertEqual(args[-1], "python3 -")
        self.assertKeinGeheimnis(" ".join(map(str, args)))
        # the value travels only inside the stdin script (base64 JSON)
        daten = eingabe.decode().split('b64decode("')[1].split('"')[0]
        self.assertEqual(json.loads(base64.b64decode(daten))["SKAEL_WEBHOOK_SECRET"], SECRET)

    def test_fehlermeldung_zeigt_wert_nicht(self):
        self.env.write_text(f"HOSTINGER_API_TOKEN={TOKEN}\nMELDUNG_URL=http://GEHEIMPFAD\n", encoding="utf-8")
        code, text = self.ausfuehren(["geheimnis", "--vm", "1"])
        self.assertEqual(code, 1)
        self.assertIn("MELDUNG_URL", text)
        self.assertKeinGeheimnis(text)


class HochladenAuswahlTest(unittest.TestCase):
    def test_widersprochene_und_abgelaufene_seiten_bleiben_weg(self):
        with tempfile.TemporaryDirectory() as tmp:
            ordner = Path(tmp)
            (ordner / "assets").mkdir()
            jetzt = datetime.now(timezone.utc)
            ids = {"A" * 22: jetzt + timedelta(days=5), "B" * 22: jetzt + timedelta(days=5), "C" * 22: jetzt - timedelta(days=1)}
            for sid, ablauf in ids.items():
                (ordner / "v" / sid).mkdir(parents=True)
                (ordner / "v" / sid / ".meta.json").write_text(json.dumps({"ablauf": ablauf.isoformat()}))
            pfade, widersprochen, abgelaufen = hostinger.seiten_auswahl(ordner, {"B" * 22})
        self.assertEqual(pfade, ["assets", "v/" + "A" * 22])
        self.assertEqual(widersprochen, ["B" * 22])
        self.assertEqual(abgelaufen, ["C" * 22])


if __name__ == "__main__":
    unittest.main()
