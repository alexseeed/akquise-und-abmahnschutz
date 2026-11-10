"""Testballon: both recruiting ways side by side, each until ~100 ready leads or the budget is used.

    python -m scraper testballon --name <name> --suche "Beruf A,Beruf B" --keywords "Branche" ...

`testballon` (cli.py) creates two campaigns `<name>-website` (Recruiting: firms via Google Maps,
open position on their own website) and `<name>-portale` (Stellensuche: job portals), runs
`testballon-lauf` in each and writes the comparison report.

- `lauf()` runs INSIDE one campaign: small input batches, then only as many firms into the
  paid enrichment as the target still needs. Stops at the target, at the budget
  (pipeline.BUDGET_OK) or when the market is exhausted — after the fallback ladder.
- Fallback ladder when there are too few job ads / firms with an open position:
    portale: 1. wider window (older ads, more pages, larger radius)  2. related search terms (AI)
    website: 1. NK strecke (matching firms without open position, only with a check profile)
             2. smaller cities (lower minimum population)
- `bericht()` reads both campaign databases: cost, quality, funnel, market estimate,
  overlap, sample leads, recommendation.
"""
from __future__ import annotations

import json
import logging
import math
import sqlite3
import statistics
from datetime import date, datetime
from pathlib import Path

from . import db, pipeline, transforms as T
from .clients import FindymailClient, SkaelClient
from .llm import LLM

log = logging.getLogger(__name__)

WEGE = {"website": "recruiting", "portale": "stellensuche"}
WEG_NAME = {"website": "Firmen-Website (Recruiting)", "portale": "Jobportale (Stellensuche)"}

MAX_RUNDEN = 25
START_BATCH = {"recruiting": 3, "stellensuche": 4}     # Maps queries / portal searches per round
MAX_BATCH = {"recruiting": 24, "stellensuche": 32}
QUOTE_ANNAHME = 0.7        # ready leads per handed-over firm until measured
QUOTE_MIN = 0.25
WEBSITE_QUOTE = 0.5        # Stellensuche: own website found per find_domain lookup (measured 10/2026)
MIN_EINWOHNER = 10_000     # lower bound for the "smaller cities" fallback


# ------------------------------------------------------------------ helpers
def _zahl(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> int:
    return int(conn.execute(sql, params).fetchone()[0] or 0)


def _ready(conn: sqlite3.Connection) -> int:
    return _zahl(conn, "SELECT COUNT(*) FROM anreicherung WHERE ready_to_send=1")


def _stand(conn: sqlite3.Connection) -> tuple:
    """Fingerprint of the progress — unchanged after a round means: nothing more to get."""
    return tuple(_zahl(conn, sql) for sql in (
        "SELECT COUNT(*) FROM datensaetze",
        "SELECT COUNT(*) FROM datensaetze WHERE is_icp IS NOT NULL",
        "SELECT COUNT(*) FROM datensaetze WHERE stelle_vorhanden IS NOT NULL",
        "SELECT COUNT(*) FROM datensaetze WHERE domain_status IS NOT NULL",
        "SELECT COUNT(*) FROM datensaetze WHERE groesse_kategorie IS NOT NULL",
        "SELECT COUNT(*) FROM anreicherung",
        "SELECT COUNT(*) FROM anreicherung WHERE ready_to_send=1",
        "SELECT COUNT(*) FROM stellen WHERE ausschluss IS NULL",
    ))


def _offene_eingaben(conn: sqlite3.Connection, pfad: str) -> int:
    if pfad == "recruiting":
        return _zahl(conn, "SELECT COUNT(*) FROM verarbeitung WHERE status != 'done' AND attempts < ?",
                     (pipeline.MAX_ATTEMPTS,))
    max_seiten = pipeline.einstellung(conn, "stellen_max_seiten", pipeline.CONFIG.stellen_max_seiten)
    return _zahl(conn, "SELECT COUNT(*) FROM stellen_suche WHERE attempts < ? AND (status != 'done' OR "
                       "(seiten < ? AND (weiter = 1 OR (weiter IS NULL AND treffer >= seiten * 100))))",
                 (pipeline.MAX_ATTEMPTS, max_seiten))


def fallback_liste(conn: sqlite3.Connection) -> list[dict]:
    try:
        return json.loads(db.get_meta(conn, "ballon_fallback", "[]") or "[]")
    except json.JSONDecodeError:
        return []


def _fallback_merken(conn: sqlite3.Connection, stufe: str, text: str) -> None:
    liste = fallback_liste(conn) + [{"stufe": stufe, "text": text}]
    db.set_meta(conn, "ballon_fallback", json.dumps(liste, ensure_ascii=False))
    log.info("Testballon — Fallback: %s", text)


# ------------------------------------------------------------------ one round
def _eingang(conn: sqlite3.Connection, skael: SkaelClient, pfad: str, batch: int) -> int:
    """Next batch of the cheap input stage. Returns the number of open inputs before the batch."""
    offen = _offene_eingaben(conn, pfad)
    if pfad == "recruiting":
        if offen:
            pipeline.stufe_sicher("2", pipeline.stufe2_maps, conn, skael, limit=batch)
    else:
        if offen:
            pipeline.stufe_sicher("1j", pipeline.stufe1j_stellensuche, conn, skael, limit=batch)
        pipeline.stufe_sicher("1k", pipeline.stufe1k_firmen, conn)
    return offen


def _bedarf(conn: sqlite3.Connection, ziel: int) -> int:
    """How many more firms to hand over: missing leads divided by the measured ready rate."""
    ready = _ready(conn)
    angereichert = _zahl(conn, "SELECT COUNT(*) FROM anreicherung")
    quote = ready / angereichert if angereichert >= 10 else QUOTE_ANNAHME
    return max(0, math.ceil((ziel - ready) / max(quote, QUOTE_MIN)))


def _verarbeiten(conn: sqlite3.Connection, skael: SkaelClient, llm: LLM, findymail: FindymailClient,
                 icp_prompt: str, ziel: int) -> None:
    bedarf = _bedarf(conn, ziel)
    pipeline.stufe_sicher("3g", pipeline.stufe3g_groesse, conn, llm)
    if db.pfad(conn) == "stellensuche":
        pipeline.stufe_sicher("3a", pipeline.stufe3a_domains, conn, llm, skael, limit=max(1, math.ceil(bedarf / WEBSITE_QUOTE)))
    pipeline.stufe_sicher("3b", pipeline.stufe3b_dedupe, conn)
    pipeline.stufe_sicher("3c", pipeline.stufe3c_icp, conn, skael, icp_prompt)
    pipeline.stufe_sicher("3e", pipeline.stufe3e_stellen, conn, skael, llm)
    if bedarf:
        pipeline.stufe_sicher("3d", pipeline.stufe3d_uebergabe, conn, limit=bedarf)
    pipeline.stufe_sicher("4a", pipeline.stufe4a_website_final, conn, llm, skael)
    pipeline.stufe_sicher("4b", pipeline.stufe4b_impressum, conn, skael)
    pipeline.stufe_sicher("4c", pipeline.stufe4c_emails, conn, skael, findymail)
    pipeline.stufe_sicher("4d", pipeline.stufe4d_anrede, conn, llm)
    pipeline.stufe_sicher("4e", pipeline.stufe4e_personalisierung, conn, skael, llm)
    pipeline.stufe_sicher("4f", pipeline.stufe4f_videotitel, conn, llm)
    pipeline.stufe_sicher("4g", pipeline.stufe4g_linkedin, conn, skael)
    pipeline.stufe_sicher("4h", pipeline.stufe4h_ready, conn)


# ------------------------------------------------------------------ fallback ladder
def _naechste_stufe(conn: sqlite3.Connection, skael: SkaelClient, llm: LLM, icp_prompt: str) -> bool:
    """Next fallback step that can bring new firms. False = ladder exhausted."""
    pfad = db.pfad(conn)
    erledigt = {f["stufe"] for f in fallback_liste(conn)}

    if pfad == "stellensuche":
        if "zeitraum" not in erledigt:
            alter = pipeline.einstellung(conn, "stellen_max_alter", pipeline.CONFIG.stellen_max_alter)
            seiten = pipeline.einstellung(conn, "stellen_max_seiten", pipeline.CONFIG.stellen_max_seiten)
            umkreis = pipeline.einstellung(conn, "stellen_umkreis", pipeline.CONFIG.stellen_umkreis)
            neu = (max(alter, 60), max(seiten, 3), max(umkreis, 50))
            if neu != (alter, seiten, umkreis):
                db.set_meta(conn, "stellen_max_alter", str(neu[0]))
                db.set_meta(conn, "stellen_max_seiten", str(neu[1]))
                db.set_meta(conn, "stellen_umkreis", str(neu[2]))
                _fallback_merken(conn, "zeitraum",
                                 f"Suchfenster erweitert: Anzeigen bis {neu[0]} Tage (vorher {alter}), "
                                 f"bis {neu[1]} Seiten je Suche (vorher {seiten}), Umkreis {neu[2]} km "
                                 f"für neue Suchen (vorher {umkreis})")
                return True
            erledigt.add("zeitraum")
        if "synonyme" not in erledigt:
            begriffe = [r[0] for r in conn.execute("SELECT DISTINCT suchbegriff FROM stellen_suche ORDER BY id")]
            neu = llm.suchbegriffe_synonyme(begriffe) or []
            kombis = conn.execute("SELECT DISTINCT portal, ort, land FROM stellen_suche").fetchall()
            for begriff in neu:
                for k in kombis:
                    db.upsert(conn, "stellen_suche", {"portal": k["portal"], "suchbegriff": begriff,
                                                      "ort": k["ort"], "land": k["land"]},
                              conflict=("portal", "suchbegriff", "ort", "land"))
            _fallback_merken(conn, "synonyme",
                             f"Weitere Suchbegriffe ergänzt: {', '.join(neu)}" if neu
                             else "Keine sinnvollen weiteren Suchbegriffe gefunden")
            return bool(neu)
        return False

    if pfad == "recruiting":
        nk_an = pipeline.einstellung(conn, "nk_on", pipeline.CONFIG.nk_on)
        if "nk" not in erledigt and icp_prompt.strip() and not nk_an:
            db.set_meta(conn, "nk_on", "true")
            _fallback_merken(conn, "nk", "NK-Strecke zugeschaltet: passende Firmen ohne offene Stelle "
                                         "bekommen einen Satz zur Website statt zur Stelle")
            return True
        if "region" not in erledigt:
            neu_eingaben = 0
            for e in conn.execute("SELECT * FROM eingabe").fetchall():
                kleiner = max(MIN_EINWOHNER, (e["min_population"] or 0) // 2)
                if (e["min_population"] or 0) > kleiner:
                    db.upsert(conn, "eingabe", {"keyword": e["keyword"], "country_code": e["country_code"],
                                                "min_population": kleiner},
                              conflict=("keyword", "country_code", "min_population"))
                    neu_eingaben += 1
            if neu_eingaben:
                pipeline.stufe1_staedte(conn, skael)
                # Städte, die schon abgefragt sind, nicht noch einmal bezahlen
                with db.write(conn):
                    conn.execute("UPDATE verarbeitung SET status='done' WHERE status != 'done' AND query IN "
                                 "(SELECT query FROM verarbeitung WHERE status='done')")
            kleinste = _zahl(conn, "SELECT COALESCE(MIN(min_population), 0) FROM eingabe")
            _fallback_merken(conn, "region",
                             f"Kleinere Städte aufgenommen (ab {kleinste:,} Einwohnern)".replace(",", ".")
                             if neu_eingaben else "Region lässt sich nicht weiter vergrößern")
            return bool(neu_eingaben) and _offene_eingaben(conn, pfad) > 0
    return False


# ------------------------------------------------------------------ run inside one campaign
def lauf(conn: sqlite3.Connection, skael: SkaelClient, llm: LLM, findymail: FindymailClient, *,
         ziel: int, nur_marktprobe: bool = False) -> dict:
    """Testballon in the current campaign. Returns {grund, ready, runden}; also stored in run_meta."""
    pfad = db.pfad(conn)
    if pfad not in WEGE.values():
        raise SystemExit("Testballon braucht eine Kampagne der Art recruiting oder stellensuche.")
    icp_prompt = db.get_meta(conn, "icp_prompt", "") or ""
    db.set_meta(conn, "ballon_ziel", str(ziel))
    batch = int(db.get_meta(conn, "ballon_batch", 0) or START_BATCH[pfad])
    if pfad == "recruiting":
        pipeline.stufe1_staedte(conn, skael)

    if nur_marktprobe:
        _eingang(conn, skael, pfad, START_BATCH[pfad])
        db.set_meta(conn, "ballon_grund", "marktprobe")
        return {"grund": "marktprobe", "ready": _ready(conn), "runden": 0}

    grund, runde = "runden", 0
    while runde < MAX_RUNDEN:
        runde += 1
        if _ready(conn) >= ziel:
            grund = "ziel"
            break
        if not pipeline.budget_ok():
            grund = "budget"
            break
        vorher = _stand(conn)
        bedarf_vorher = _bedarf(conn, ziel)
        offen = _eingang(conn, skael, pfad, batch)
        _verarbeiten(conn, skael, llm, findymail, icp_prompt, ziel)
        log.info("Testballon — Runde %s: %s versandfertig (Ziel %s)", runde, _ready(conn), ziel)
        if not pipeline.budget_ok():
            grund = "budget"
            break
        if _stand(conn) == vorher and not offen:
            if not _naechste_stufe(conn, skael, llm, icp_prompt):
                grund = "markt"
                break
            continue
        neu = _zahl(conn, "SELECT COUNT(*) FROM anreicherung") - vorher[5]
        if neu < bedarf_vorher:
            batch = min(batch * 2, MAX_BATCH[pfad])
            db.set_meta(conn, "ballon_batch", str(batch))
    if grund == "runden" and _ready(conn) >= ziel:
        grund = "ziel"
    db.set_meta(conn, "ballon_grund", grund)
    db.set_meta(conn, "ballon_runden", str(runde))
    return {"grund": grund, "ready": _ready(conn), "runden": runde}


# ------------------------------------------------------------------ report
GRUND_TEXT = {
    "ziel": "Ziel erreicht",
    "budget": "Budget aufgebraucht",
    "markt": "Markt erschöpft (alle Fallback-Stufen genutzt)",
    "runden": "Rundenlimit erreicht",
    "marktprobe": "nur Marktprobe",
    "": "nicht gelaufen",
}


def _prozent(teil: int, ganz: int) -> str:
    return f"{teil / ganz:.0%}" if ganz else "–"


def _euro(credits: float) -> str:
    return f"{credits / pipeline.CREDITS_JE_EURO:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


def kennzahlen(db_pfad: Path) -> dict:
    """Read one campaign database (read-only)."""
    conn = sqlite3.connect(f"file:{db_pfad}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        meta = {r["key"]: r["value"] for r in conn.execute("SELECT key, value FROM run_meta")}
        pfad = meta.get("pfad", "google-maps")
        ready = conn.execute("SELECT * FROM anreicherung WHERE ready_to_send=1 ORDER BY id").fetchall()
        n = len(ready)
        kosten = [(r[0], r[1], r[2]) for r in conn.execute(
            "SELECT endpoint, aufrufe, credits FROM kosten ORDER BY credits DESC")]
        credits = sum(k[2] for k in kosten)
        persoenlich = sum(1 for r in ready if T.ansprache_sicher(
            r["anrede"], r["last_name"], r["anrede_confidence"])[0] != "Guten Tag")
        mit_stelle = sum(1 for r in ready if (r["strecke"] == "rc" or r["quelle"] == "stellen"))
        alter = []
        for r in ready:
            try:
                alter.append((date.today() - date.fromisoformat(str(r["stelle_datum"])[:10])).days)
            except (TypeError, ValueError):
                pass
        zahl = lambda sql: int(conn.execute(sql).fetchone()[0] or 0)  # noqa: E731
        if pfad == "recruiting":
            eingaben = (zahl("SELECT COUNT(DISTINCT query) FROM verarbeitung WHERE status='done'"),
                        zahl("SELECT COUNT(DISTINCT query) FROM verarbeitung"), "Maps-Suchen")
            mit_stelle_firmen = zahl("SELECT COUNT(*) FROM datensaetze WHERE stelle_vorhanden=1")
        else:
            eingaben = (zahl("SELECT COUNT(*) FROM stellen_suche WHERE status='done'"),
                        zahl("SELECT COUNT(*) FROM stellen_suche"), "Portal-Suchen")
            mit_stelle_firmen = zahl("SELECT COUNT(*) FROM datensaetze WHERE dedupe_status='kept'")
        trichter = [
            ("Firmen gefunden", zahl("SELECT COUNT(*) FROM datensaetze")),
            ("nach Dedupe", zahl("SELECT COUNT(*) FROM datensaetze WHERE dedupe_status='kept'")),
            ("Größen-Check raus", zahl("SELECT COUNT(*) FROM datensaetze WHERE groesse_kategorie IN "
                                       "('konzern','oeffentlich_verband','it_wettbewerber')")),
            ("passend (Profil)", zahl("SELECT COUNT(*) FROM datensaetze WHERE is_icp=1")),
            ("mit offener Stelle", mit_stelle_firmen),
            ("angereichert", zahl("SELECT COUNT(*) FROM anreicherung")),
            ("versandfertig", n),
        ]
        erledigt, gesamt, art = eingaben
        hochrechnung = round(n / erledigt * gesamt) if erledigt and n else None
        beispiele = [{"firma": r["firmenname_final"] or r["firmenname"], "stelle": r["job_title"] or "–",
                      "opener": r["personalisierung"] or "–",
                      "email_typ": {"GF": "Geschäftsführer-Adresse", "Info@": "Info-Adresse"}.get(
                          r["email_final_type"] or "", "–")}
                     for r in ready[:3]]
        return {
            "pfad": pfad, "ready": n, "ziel": int(meta.get("ballon_ziel") or 0),
            "grund": meta.get("ballon_grund", ""), "runden": meta.get("ballon_runden", "0"),
            "fallback": json.loads(meta.get("ballon_fallback") or "[]"),
            "credits": credits, "kosten": kosten,
            "gf": sum(1 for r in ready if r["email_final_type"] == "GF"),
            "safe": sum(1 for r in ready if r["email_final_status"] == "Safe to Send"),
            "persoenlich": persoenlich, "mit_stelle": mit_stelle,
            "alter_median": statistics.median(alter) if alter else None,
            "trichter": trichter, "eingaben": eingaben, "hochrechnung": hochrechnung,
            "domains": {T.registrable_domain(r["website_final"]) for r in ready if r["website_final"]},
            "beispiele": beispiele,
        }
    finally:
        conn.close()


def empfehlung(werte: dict[str, dict]) -> str:
    """Plain recommendation; the user decides."""
    laufend = {w: k for w, k in werte.items() if k and k["grund"] != "marktprobe"}
    if not laufend:
        return "Noch kein Testballon gelaufen — erst den Lauf starten, dann vergleichen."
    erreicht = [w for w, k in laufend.items() if k["ziel"] and k["ready"] >= k["ziel"]]
    if len(laufend) == 1:
        w = next(iter(laufend))
        return f"Nur ein Weg gelaufen ({WEG_NAME[w]})."
    if len(erreicht) == 1:
        w = erreicht[0]
        anderer = next(x for x in laufend if x != w)
        return (f"**{WEG_NAME[w]}** – nur dieser Weg hat das Ziel erreicht. {WEG_NAME[anderer]}: "
                f"{laufend[anderer]['ready']} Leads ({GRUND_TEXT.get(laufend[anderer]['grund'], '')}).")
    je_lead = {w: (k["credits"] / k["ready"] if k["ready"] else math.inf) for w, k in laufend.items()}
    guenstig = min(je_lead, key=je_lead.get)
    anderer = next(x for x in laufend if x != guenstig)
    text = f"**{WEG_NAME[guenstig]}** ist günstiger je fertigem Lead."
    k, a = laufend[guenstig], laufend[anderer]
    for schluessel, name in (("mit_stelle", "konkretem Stellenbezug"), ("gf", "Geschäftsführer-Adresse")):
        q_k = k[schluessel] / k["ready"] if k["ready"] else 0
        q_a = a[schluessel] / a["ready"] if a["ready"] else 0
        if q_a - q_k >= 0.15:
            text += (f" Aber {WEG_NAME[anderer]} liefert deutlich mehr Leads mit {name} "
                     f"({q_a:.0%} statt {q_k:.0%}) – abwägen.")
    if not erreicht:
        text += " Keiner der Wege hat das Ziel erreicht – siehe „Zu wenig Stellen?“."
    return text


def bericht(name: str, db_pfade: dict[str, Path], ziel: int) -> str:
    """Comparison report (Markdown) for the campaigns `<name>-website` / `<name>-portale`."""
    werte = {w: (kennzahlen(p) if p.exists() else None) for w, p in db_pfade.items()}
    wege = [w for w in db_pfade if werte[w]]
    zeilen = [f"# Testballon „{name}“ – Vergleich der Recruiting-Wege",
              "", f"Stand {datetime.now():%d.%m.%Y %H:%M} · Ziel je Weg: {ziel} versandfertige Leads", ""]
    if not wege:
        return "\n".join(zeilen + ["Noch keine Daten – Testballon zuerst laufen lassen."])

    def zeile(titel: str, werte_je_weg: list[str]) -> str:
        return f"| {titel} | " + " | ".join(werte_je_weg) + " |"

    zeilen += ["## Ergebnis", "", "| | " + " | ".join(WEG_NAME[w] for w in wege) + " |",
               "|---|" + "---|" * len(wege)]
    k = {w: werte[w] for w in wege}
    zeilen += [
        zeile("Versandfertige Leads", [f"**{k[w]['ready']}**" for w in wege]),
        zeile("Status", [GRUND_TEXT.get(k[w]["grund"], k[w]["grund"]) for w in wege]),
        zeile("Skael-Kosten", [_euro(k[w]["credits"]) for w in wege]),
        zeile("Kosten je Lead", [_euro(k[w]["credits"] / k[w]["ready"]) if k[w]["ready"] else "–" for w in wege]),
        zeile("Geschäftsführer-Adresse", [_prozent(k[w]["gf"], k[w]["ready"]) for w in wege]),
        zeile("E-Mail „Safe to Send“", [_prozent(k[w]["safe"], k[w]["ready"]) for w in wege]),
        zeile("Persönliche Ansprache", [_prozent(k[w]["persoenlich"], k[w]["ready"]) for w in wege]),
        zeile("Mit konkreter Stelle", [_prozent(k[w]["mit_stelle"], k[w]["ready"]) for w in wege]),
        zeile("Anzeigenalter (Median)", [f"{k[w]['alter_median']:.0f} Tage" if k[w]["alter_median"] is not None
                                         else "–" for w in wege]),
        zeile("Marktgröße (Hochrechnung)", [
            f"ca. {k[w]['hochrechnung']:,} Leads".replace(",", ".") if k[w]["hochrechnung"] else "–"
            for w in wege]),
        "", "KI-Kosten sind nicht enthalten (je nach Modell 0,03–0,5 Cent je Lead).",
        "Hochrechnung: versandfertige Leads je erledigter Suche × alle Suchen der Kampagne.", "",
        "## Empfehlung", "", empfehlung(k), "",
    ]
    if len(wege) == 2:
        a, b = (k[w]["domains"] for w in wege)
        zeilen += ["## Überschneidung", "",
                   f"{len(a & b)} Firmen stehen in beiden Ergebnissen, zusammen {len(a | b)} verschiedene Firmen.",
                   "Beide Wege kombinieren: Liste des einen Weges exportieren, mit `blockliste-import` in die "
                   "Kampagne des anderen übernehmen, dann dort exportieren – so gibt es keine doppelten Mails.", ""]
    zeilen += ["## Trichter", "", "| | " + " | ".join(WEG_NAME[w] for w in wege) + " |",
               "|---|" + "---|" * len(wege)]
    for i, (titel, _) in enumerate(k[wege[0]]["trichter"]):
        zeilen.append(zeile(titel, [str(k[w]["trichter"][i][1]) for w in wege]))
    zeilen.append(zeile("Suchen erledigt", [f"{k[w]['eingaben'][0]} von {k[w]['eingaben'][1]} {k[w]['eingaben'][2]}"
                                            for w in wege]))
    zeilen += ["", "## Zu wenig Stellen?", ""]
    for w in wege:
        stufen = k[w]["fallback"]
        zeilen.append(f"**{WEG_NAME[w]}:** " + ("; ".join(s["text"] for s in stufen)
                                                if stufen else "keine Fallback-Stufe nötig") + ".")
        if k[w]["grund"] == "markt":
            zeilen.append(f"Mit diesen Einstellungen gibt der Markt nur {k[w]['ready']} Leads her. Nächste Hebel: "
                          "weitere Berufe oder Branchen, größere Region, beide Wege kombinieren.")
        zeilen.append("")
    zeilen += ["## Kosten je Schritt", ""]
    for w in wege:
        zeilen.append(f"**{WEG_NAME[w]}:** " + (", ".join(
            f"{ep} {_euro(cr)} ({aufrufe}×)" for ep, aufrufe, cr in k[w]["kosten"][:6]) or "keine Kosten erfasst"))
    zeilen += ["", "## Beispiele", ""]
    for w in wege:
        zeilen.append(f"**{WEG_NAME[w]}**")
        for b in k[w]["beispiele"]:
            zeilen.append(f"- {b['firma']} · Stelle: {b['stelle']} · {b['email_typ']}  \n  „{b['opener']}“")
        if not k[w]["beispiele"]:
            zeilen.append("- noch keine versandfertigen Leads")
        zeilen.append("")
    zeilen += ["## Weiter", "",
               "Weg wählen und in dessen Kampagne weitermachen, z. B. mehr Leads:",
               "`python3 -m scraper --kampagne <name>-<weg> run --stage all --budget <€>`",
               "Die fertigen Listen je Weg liegen in `kampagnen/<name>-<weg>/exports/`."]
    return "\n".join(zeilen) + "\n"
