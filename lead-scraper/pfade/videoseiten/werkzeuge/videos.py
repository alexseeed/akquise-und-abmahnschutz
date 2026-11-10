#!/usr/bin/env python3
"""Personal videos per lead via the Skael API (SkaelReach).

    python3 werkzeuge/videos.py kampagnen
    python3 werkzeuge/videos.py pruefen  --kampagne 288
    python3 werkzeuge/videos.py test     --kampagne 288 --leads leads.json [--ja]
    python3 werkzeuge/videos.py anlegen  --kampagne 288 --leads leads.json [--ja]
    python3 werkzeuge/videos.py warten   --kampagne 288
    python3 werkzeuge/videos.py zusammenfuehren --kampagne 288 --leads leads.json
    python3 werkzeuge/videos.py geheimnis --kampagne 288

Only first name, company, domain and website go to Skael. E-mail and phone never do:
Skael shows everything it receives on the public video page without login.
State per campaign: arbeit/videos_<kampagne>.json (resumable, nothing is created twice).
Standard library only.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
import wiederholen  # noqa: E402  (shared retry rule, werkzeuge/wiederholen.py)

HIER = Path(__file__).resolve().parents[1]          # pfade/videoseiten
ARBEIT = HIER / "arbeit"
API = "https://api.skael.de/api"
CREDITS_BIS_2_MIN = 110
CREDITS_JE_WEITERE_MINUTE = 55
BESTAETIGUNG_AB = 500                               # credits; above this --ja is mandatory
MAX_NEU_ANLEGEN = 3            # a video that failed for a temporary reason is created anew at most this often
ABBRUCH_NACH_AUSFAELLEN = 3    # consecutive leads that fail with a temporary error: Skael is down, stop the batch
MAX_SEITEN = 100               # pagination guard for the campaign list


# ---------------------------------------------------------------- config

def lade_schluessel() -> str:
    """SKAEL_API_KEY from pfade/videoseiten/.env, else pfade/google-maps/.env. Never printed."""
    for env in (HIER / ".env", HIER.parent / "google-maps" / ".env"):
        if env.is_file():
            for zeile in env.read_text(encoding="utf-8").splitlines():
                zeile = zeile.strip()
                if zeile.startswith("SKAEL_API_KEY="):
                    wert = zeile.split("=", 1)[1].strip().strip('"').strip("'")
                    if wert and "dein_key" not in wert:
                        return wert
    if os.environ.get("SKAEL_API_KEY"):
        return os.environ["SKAEL_API_KEY"]
    sys.exit("Kein Skael-Schlüssel gefunden. Er gehört als SKAEL_API_KEY=… in pfade/videoseiten/.env "
             "(oder pfade/google-maps/.env). Anleitung: wissen/11_zugaenge-und-kosten.md")


# ---------------------------------------------------------------- http

class SkaelFehler(RuntimeError):
    """A Skael call failed. voruebergehend=True: still temporary after all attempts (Skael down, timeouts)."""

    def __init__(self, meldung: str, status: int = 0, voruebergehend: bool = False):
        super().__init__(meldung)
        self.status, self.voruebergehend = status, voruebergehend


def anfrage(methode: str, pfad: str, daten: dict | None = None, versuche: int | None = None) -> dict:
    """Call the Skael API. Temporary errors are retried with backoff (werkzeuge/wiederholen.py),
    permanent ones fail at once with Skael's own message. Attempts: MAX_RETRIES (default 5)."""
    url = pfad if pfad.startswith("http") else API + pfad
    kopf = {
        "Authorization": "Bearer " + lade_schluessel(),
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    erg = wiederholen.wiederholen(lambda: wiederholen.http_json(url, methode, kopf, daten, timeout=120),
                                  was=f"Skael {methode} {pfad}", versuche=versuche)
    if 200 <= erg.status < 300:
        return erg.daten if erg.daten is not None else {}
    if erg.status == 401:
        sys.exit("Skael lehnt den Schlüssel ab (401). Bitte den Schlüssel in der .env prüfen.")
    if erg.status == 402:
        sys.exit("Skael meldet zu wenig Guthaben (402). Bitte Credits aufladen und erneut starten.")
    if erg.status == 404 and "/video-campaigns/" in pfad and methode == "GET":
        sys.exit("Diese Kampagne gibt es in diesem Skael-Konto nicht. Mit dem Befehl `kampagnen` "
                 "die richtige Nummer ablesen (oder es ist der Schlüssel eines anderen Kontos).")
    temporaer = wiederholen.voruebergehend(erg.status, erg.meldung)
    nach = f" (nach {erg.versuche} Versuchen)" if temporaer else ""
    if erg.status == 0:
        raise SkaelFehler(f"Skael nicht erreichbar: {erg.meldung}{nach}", 0, temporaer)
    raise SkaelFehler(f"Skael {methode} {pfad}: HTTP {erg.status}" + (f" {erg.meldung}" if erg.meldung else "") + nach,
                      erg.status, temporaer)


def daten_von(antwort: dict):
    return antwort.get("data", antwort) if isinstance(antwort, dict) else antwort


# ---------------------------------------------------------------- campaign checks

def kosten_je_video(sekunden: float | None) -> int:
    if not sekunden or sekunden <= 120:
        return CREDITS_BIS_2_MIN
    return CREDITS_BIS_2_MIN + CREDITS_JE_WEITERE_MINUTE * math.ceil((sekunden - 120) / 60)


def euro(credits: int) -> str:
    return f"{credits / 1000:.2f} €".replace(".", ",")


def kampagne_laden(kid: int) -> dict:
    return daten_von(anfrage("GET", f"/video-campaigns/{kid}"))


def hat_screenshot_teil(kampagne: dict) -> bool:
    # A personal video needs a screenshot segment in the timeline; recording + facecam alone
    # gives every lead the identical video. The exact type name is not documented, so match loosely.
    for teil in kampagne.get("timeline") or []:
        if "screenshot" in json.dumps(teil).lower():
            return True
    return False


def aufnahme(kampagne: dict) -> tuple[bool, float]:
    """(has recording, seconds). A campaign may record the screen, only the facecam
    (laid over the lead's website screenshot), or both."""
    da = bool(kampagne.get("recording_path") or kampagne.get("face_recording_path"))
    dauer = max(kampagne.get("recording_duration") or 0, kampagne.get("face_recording_duration") or 0)
    return da, dauer


SKAEL_STANDARDFARBE = "#6366f1"  # player colour of a new Skael campaign


def befunde(kampagne: dict) -> list[tuple[str, str]]:
    """List of (level, message); level ok | warnung | fehler."""
    aus: list[tuple[str, str]] = []
    da, dauer = aufnahme(kampagne)
    if not da:
        aus.append(("fehler", "Es ist noch keine Aufnahme hinterlegt. Ohne Aufnahme schlägt jedes Video fehl."))
    else:
        k = kosten_je_video(dauer)
        msg = f"Aufnahme vorhanden, {int(dauer // 60)}:{int(dauer % 60):02d} Minuten, {k} Credits ({euro(k)}) je Video."
        aus.append(("ok" if dauer <= 120 else "warnung", msg + ("" if dauer <= 120 else " Unter 2 Minuten wären es 110 Credits.")))
    if hat_screenshot_teil(kampagne):
        aus.append(("ok", "Der Ablauf enthält einen Screenshot-Teil: jedes Video zeigt die Website des Leads."))
    else:
        aus.append(("warnung", "Im Ablauf ist kein Screenshot-Teil erkennbar. Dann ist das Video für jeden Lead gleich. "
                               "Bitte in Skael einen Website-Abschnitt einbauen (anleitungen/01_skael-video-aufnehmen.md)."))
    if kampagne.get("custom_domain_id"):
        aus.append(("ok", "Eigene Video-Domain ist eingerichtet."))
    else:
        aus.append(("warnung", "Keine eigene Video-Domain. Die Videos laufen dann unter einer Skael-Adresse (optional, Anleitung Teil 4)."))
    farbe = (((kampagne.get("settings") or {}).get("appearance") or {}).get("primary_color") or "").lower()
    if farbe == SKAEL_STANDARDFARBE:
        aus.append(("warnung", "Der Video-Player hat noch die Skael-Standardfarbe (Lila). Auf der Seite wirkt das fremd. "
                               "Bitte in Skael die Markenfarbe eintragen (anleitungen/01_skael-video-aufnehmen.md, Schritt 3)."))
    hooks = kampagne.get("webhooks") or []
    if any("/webhook/skael" in (h.get("url") or "") for h in hooks):
        aus.append(("ok", "Webhook zur eigenen Seite ist eingerichtet."))
    else:
        aus.append(("warnung", "Kein Webhook auf https://<seiten-domain>/webhook/skael. Ohne ihn fehlen die Video-Auswertungen (kommt nach der Server-Einrichtung)."))
    return aus


# ---------------------------------------------------------------- state

def zustand_datei(kid: int) -> Path:
    return ARBEIT / f"videos_{kid}.json"


def zustand_laden(kid: int) -> dict:
    p = zustand_datei(kid)
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {"kampagne": kid, "leads": {}}


def zustand_speichern(kid: int, z: dict) -> None:
    ARBEIT.mkdir(parents=True, exist_ok=True)
    tmp = zustand_datei(kid).with_suffix(".tmp")
    tmp.write_text(json.dumps(z, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(zustand_datei(kid))


def leads_laden(pfad: str) -> list[dict]:
    leads = json.loads(Path(pfad).read_text(encoding="utf-8"))
    if not isinstance(leads, list):
        sys.exit("leads.json muss eine Liste von Leads sein (Export mit --lead-format).")
    return leads


def neu_anlegen_erlaubt(v: dict) -> bool:
    """A video Skael reported as failed for a temporary reason (timeout, overloaded …) may be created anew.
    Permanent causes (e.g. "no chunks": no recording) are not retried."""
    return (v.get("status") == "failed" and wiederholen.voruebergehend_text(str(v.get("fehler") or ""))
            and int(v.get("neu_angelegt") or 0) < MAX_NEU_ANLEGEN)


def prospect_daten(lead: dict) -> dict | None:
    """Fields sent to Skael. Returns None if the lead cannot get a personal video."""
    website = (lead.get("website") or "").strip()
    if website and not website.startswith("http"):
        website = "https://" + website
    if not lead.get("externe_id") or not website:
        return None
    d = {
        "screenshot_url": website,
        "company": lead.get("firma") or "",
        "domain": lead.get("domain") or urlparse(website).netloc.removeprefix("www."),
        "dedupe_value": str(lead["externe_id"]),
        "custom_vars": {"externe_id": str(lead["externe_id"])},
        "async": True,
    }
    if lead.get("vorname"):
        d["first_name"] = lead["vorname"]
    return d


# ---------------------------------------------------------------- commands

def cmd_kampagnen(_a) -> None:
    alle = []
    for seite in range(1, MAX_SEITEN + 1):
        antwort = anfrage("GET", f"/video-campaigns?page={seite}")
        alle += daten_von(antwort) or []
        if not isinstance(antwort, dict) or antwort.get("current_page", 1) >= antwort.get("last_page", 1):
            break
    if not alle:
        print("Noch keine Videokampagne angelegt. Anleitung: anleitungen/01_skael-video-aufnehmen.md")
        return
    for k in alle:
        da, dauer = aufnahme(k)
        print(f"{k['id']:>6}  {k.get('name','')[:60]:<60}  Aufnahme {'ja' if da else 'NEIN'}"
              f"  {int(dauer // 60)}:{int(dauer % 60):02d} min  Screenshot-Teil {'ja' if hat_screenshot_teil(k) else 'nein'}")


def cmd_pruefen(a) -> None:
    k = kampagne_laden(a.kampagne)
    print(f"Kampagne {k.get('id')}: {k.get('name')}")
    for stufe, msg in befunde(k):
        print({"ok": "  ✓", "warnung": "  !", "fehler": "  ✗"}[stufe], msg)
    if any(s == "fehler" for s, _ in befunde(k)):
        sys.exit(1)


def anlegen(a, nur_test: bool) -> None:
    k = kampagne_laden(a.kampagne)
    if not aufnahme(k)[0]:
        sys.exit("Die Kampagne hat noch keine Aufnahme. Erst aufnehmen (anleitungen/01_skael-video-aufnehmen.md), dann erneut.")
    z = zustand_laden(a.kampagne)
    offen = []
    ohne = 0
    for lead in leads_laden(a.leads):
        d = prospect_daten(lead)
        if d is None:
            ohne += 1
            continue
        alt = z["leads"].get(str(lead["externe_id"]))
        if alt:
            if not neu_anlegen_erlaubt(alt):
                continue
            # Skael dedupes by dedupe_value: the failed video would come back. A new value per attempt
            # (like a new idempotency key) creates a fresh one; custom_vars keep the real externe_id.
            d = dict(d, dedupe_value=f"{lead['externe_id']}-w{int(alt.get('neu_angelegt') or 0) + 1}")
        offen.append((lead, d))
    if nur_test:
        offen = offen[:1]
    erneut = sum(1 for lead, _ in offen if str(lead["externe_id"]) in z["leads"])
    je = kosten_je_video(aufnahme(k)[1])
    summe = je * len(offen)
    print(f"{len(offen)} Videos anzulegen, je {je} Credits, zusammen {summe} Credits ({euro(summe)})."
          + (f" Davon {erneut} erneut, weil Skael sie vorübergehend nicht erstellen konnte "
             "(fehlgeschlagene Videos erstattet Skael)." if erneut else "")
          + (f" {ohne} Leads ohne Website oder Kennung bekommen kein Video." if ohne else ""))
    if not offen:
        print("Nichts zu tun: alle Leads haben schon ein Video oder sind übersprungen.")
        return
    if not a.ja:
        print("Noch nichts angelegt. Nach Zustimmung des Nutzers denselben Befehl mit --ja ausführen.")
        return
    if summe > BESTAETIGUNG_AB and nur_test:
        sys.exit("Ein Testvideo darf nicht mehr als 500 Credits kosten. Bitte Aufnahme kürzen.")
    # One lead's error never stops the batch: it is logged, stays open and is tried again next run.
    # Only when several leads in a row fail with a temporary error (Skael down) the batch stops,
    # instead of waiting through the full backoff for every remaining lead.
    fehler: list[tuple[str, str]] = []
    angelegt = in_folge = 0
    abgebrochen = False
    for i, (lead, d) in enumerate(offen, 1):
        ext = str(lead["externe_id"])
        try:
            p = daten_von(anfrage("POST", f"/video-campaigns/{a.kampagne}/prospects", d))
            if not isinstance(p, dict) or not p.get("id"):
                raise SkaelFehler(f"unerwartete Antwort von Skael (keine Video-ID): {str(p)[:120]}")
        except Exception as e:  # noqa: BLE001 - one lead must never stop the batch
            print(f"  ✗ {lead.get('firma')}: {e}")
            fehler.append((lead.get("firma") or ext, str(e)))
            in_folge = in_folge + 1 if getattr(e, "voruebergehend", False) else 0
            if in_folge >= ABBRUCH_NACH_AUSFAELLEN:
                abgebrochen = True
                print(f"  Skael ist gerade nicht erreichbar ({in_folge} Leads nacheinander). Abbruch, damit der Lauf "
                      "nicht hängt; die übrigen Leads bleiben offen.")
                break
            continue
        in_folge = 0
        alt = z["leads"].get(ext)
        eintrag = {
            "prospect_id": p.get("id"), "token": p.get("token"), "status": p.get("status") or "queued",
            "landing_page_url": p.get("landing_page_url"), "thumbnail_url": p.get("thumbnail_url"),
        }
        if alt:
            eintrag["neu_angelegt"] = int(alt.get("neu_angelegt") or 0) + 1
            eintrag["fruehere_prospect_ids"] = [*(alt.get("fruehere_prospect_ids") or []), alt.get("prospect_id")]
        z["leads"][ext] = eintrag
        zustand_speichern(a.kampagne, z)
        angelegt += 1
        if i % 25 == 0 or i == len(offen):
            print(f"  {i}/{len(offen)} angelegt")
    if fehler or abgebrochen:
        nicht_versucht = len(offen) - angelegt - len(fehler)
        print(f"Zusammenfassung: {angelegt} angelegt, {len(fehler)} fehlgeschlagen"
              + (f", {nicht_versucht} nicht versucht" if nicht_versucht else "")
              + ". Diese Leads bleiben offen; derselbe Befehl versucht sie später erneut (nichts wird doppelt angelegt).")
        for firma, grund in fehler[:20]:
            print(f"  - {firma}: {grund}")
        if len(fehler) > 20:
            print(f"  … und {len(fehler) - 20} weitere")
    if angelegt:
        print("Angelegt. Weiter mit: warten --kampagne", a.kampagne)


def cmd_test(a) -> None:
    anlegen(a, nur_test=True)


def cmd_anlegen(a) -> None:
    anlegen(a, nur_test=False)


def cmd_warten(a) -> None:
    z = zustand_laden(a.kampagne)
    frist = time.time() + a.max_minuten * 60
    # Status polling only (never creates a video again): hard deadline --max-minuten; a temporary error
    # is retried with backoff inside anfrage(), and if Skael stays unreachable the round ends and the
    # remaining videos are asked again in the next round.
    while True:
        offen = {e: v for e, v in z["leads"].items() if v.get("status") not in ("ready", "failed")}
        for ext, v in offen.items():
            if time.time() >= frist:
                break
            if not v.get("prospect_id"):
                continue
            try:
                p = daten_von(anfrage("GET", f"/video-prospects/{v['prospect_id']}"))
            except RuntimeError as e:
                print(f"  ! {ext}: {e}")
                if getattr(e, "voruebergehend", False):
                    print("  Skael antwortet gerade nicht; die übrigen Videos werden in der nächsten Runde abgefragt.")
                    break
                continue
            if not isinstance(p, dict):
                print(f"  ! {ext}: unerwartete Antwort von Skael")
                continue
            v.update({"status": p.get("status"), "token": p.get("token") or v.get("token"),
                      "landing_page_url": p.get("landing_page_url") or v.get("landing_page_url"),
                      "thumbnail_url": p.get("thumbnail_url"), "fehler": p.get("error_message")})
        zustand_speichern(a.kampagne, z)
        werte = [v.get("status") for v in z["leads"].values()]
        fertig, fehl = werte.count("ready"), werte.count("failed")
        rest = len(werte) - fertig - fehl
        print(f"fertig {fertig} · fehlgeschlagen {fehl} · in Arbeit {rest}")
        if rest == 0 or time.time() >= frist:
            if rest:
                print("Noch nicht alle fertig. Später denselben Befehl erneut ausführen; Fortschritt bleibt erhalten.")
            if fehl:
                gruende = {v.get("fehler") for v in z["leads"].values() if v.get("status") == "failed"}
                print("Gründe für Fehlschläge:", "; ".join(g for g in gruende if g) or "unbekannt",
                      "(fehlgeschlagene Videos erstattet Skael)")
                erneut = sum(1 for v in z["leads"].values() if neu_anlegen_erlaubt(v))
                if erneut:
                    print(f"{erneut} davon vorübergehend fehlgeschlagen (z. B. Zeitüberschreitung bei Skael). "
                          "`anlegen` mit denselben Leads legt sie neu an (nennt vorher die Kosten).")
            return
        time.sleep(max(0.0, min(30.0, frist - time.time())))


def cmd_zusammenfuehren(a) -> None:
    z = zustand_laden(a.kampagne)
    leads = leads_laden(a.leads)
    mit, ohne = [], []
    for lead in leads:
        v = z["leads"].get(str(lead.get("externe_id")))
        if not v or v.get("status") != "ready" or not v.get("token") or not v.get("landing_page_url"):
            ohne.append(lead.get("externe_id"))
            continue
        host = urlparse(v["landing_page_url"]).netloc
        neu = dict(lead)
        neu["video_url"] = f"https://{host}/embed/{v['token']}"
        neu["video_vorschaubild"] = v.get("thumbnail_url") or ""
        neu["video_titel"] = lead.get("video_titel") or f"Video für {lead.get('firma', '')}".strip()
        mit.append(neu)
    ziel = Path(a.aus) if a.aus else Path(a.leads).with_name(Path(a.leads).stem + "_mit_video.json")
    ziel.write_text(json.dumps(mit, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(mit)} Leads mit fertigem Video → {ziel}")
    if ohne:
        print(f"{len(ohne)} Leads ohne fertiges Video bekommen keine Seite.")


def cmd_geheimnis(a) -> None:
    """Copy the campaign's webhook secret into pfade/videoseiten/.env without ever printing it."""
    k = kampagne_laden(a.kampagne)
    geheim = (k.get("webhook_secret") or "").strip()
    if not geheim:
        sys.exit("Skael hat für diese Kampagne noch kein Webhook-Geheimnis. Es entsteht, sobald der Webhook "
                 "in der Kampagne gespeichert ist (anleitungen/01_skael-video-aufnehmen.md, Teil Webhook).")
    env = HIER / ".env"
    zeilen = env.read_text(encoding="utf-8").splitlines() if env.is_file() else []
    vorhanden: list[str] = []
    rest = []
    for z in zeilen:
        if z.strip().startswith("SKAEL_WEBHOOK_SECRET="):
            vorhanden = [s.strip() for s in z.split("=", 1)[1].strip().strip('"').split(",") if s.strip()]
        else:
            rest.append(z)
    if geheim in vorhanden:
        print("Das Geheimnis dieser Kampagne ist schon eingetragen.")
        return
    rest.append("SKAEL_WEBHOOK_SECRET=" + ",".join(vorhanden + [geheim]))
    env.write_text("\n".join(rest) + "\n", encoding="utf-8")
    os.chmod(env, 0o600)
    print("Webhook-Geheimnis der Kampagne in pfade/videoseiten/.env eingetragen (nicht angezeigt). "
          "Jetzt auf den Server übertragen: python3 werkzeuge/hostinger.py geheimnis --vm <id>")


def main() -> None:
    p = argparse.ArgumentParser(description="Persönliche Videos je Lead über Skael")
    sub = p.add_subparsers(dest="befehl", required=True)
    sub.add_parser("kampagnen", help="Videokampagnen auflisten").set_defaults(f=cmd_kampagnen)
    s = sub.add_parser("pruefen", help="Kampagne prüfen: Aufnahme, Länge, Screenshot-Teil, Domain, Webhook")
    s.add_argument("--kampagne", type=int, required=True); s.set_defaults(f=cmd_pruefen)
    for name, f, hilfe in (("test", cmd_test, "ein Video für den ersten Lead"), ("anlegen", cmd_anlegen, "Videos für alle Leads")):
        s = sub.add_parser(name, help=hilfe)
        s.add_argument("--kampagne", type=int, required=True)
        s.add_argument("--leads", required=True)
        s.add_argument("--ja", action="store_true", help="erst nach Zustimmung des Nutzers zu den genannten Kosten")
        s.set_defaults(f=f)
    s = sub.add_parser("warten", help="warten, bis alle Videos fertig sind")
    s.add_argument("--kampagne", type=int, required=True)
    s.add_argument("--max-minuten", type=int, default=60)
    s.set_defaults(f=cmd_warten)
    s = sub.add_parser("geheimnis", help="Webhook-Geheimnis der Kampagne in die .env schreiben (ohne Anzeige)")
    s.add_argument("--kampagne", type=int, required=True)
    s.set_defaults(f=cmd_geheimnis)
    s = sub.add_parser("zusammenfuehren", help="Video-Daten in die Leads schreiben")
    s.add_argument("--kampagne", type=int, required=True)
    s.add_argument("--leads", required=True)
    s.add_argument("--aus")
    s.set_defaults(f=cmd_zusammenfuehren)
    a = p.parse_args()
    try:
        a.f(a)
    except RuntimeError as e:
        sys.exit(f"Abgebrochen: {e}")


if __name__ == "__main__":
    main()
