"""Die vier Prozessstufen — Portierung der Clay-Tabellen als ausführbare Schritte.

Drei Kampagnen-Arten nutzen dieselben Stufen (run_meta "pfad"):
  google-maps  Stufen 1–4 wie im Original-Workbook
  recruiting   zusätzlich 3e (offene Stelle auf der Firmen-Website), Weiche RC/NK in 3d,
               Stellen-Opener in 4e
  stellensuche Jobportale statt Maps: 1j (Portale abfragen), 1k (Stellen je Firma bündeln),
               3g (Größen-Check vor der Website-Suche), 3a über find_domain (Impressum-Beleg),
               Stellen-Opener in 4e wie Recruiting

Grundregel für die Fehlerbehandlung: Bei einem API-Fehler wird **nicht** in das Feld
geschrieben, das die Stufe als „erledigt"-Marker abfragt. Stattdessen zählt
`attempts` hoch und `error` hält die Meldung. Die Zeile wird beim nächsten Lauf
erneut versucht — bis `MAX_ATTEMPTS` erreicht ist. Damit verwandelt ein
vorübergehender 429 keinen Lead in einen dauerhaften Ausfall.
"""
from __future__ import annotations

import json
import logging
import sqlite3
import threading
from collections import defaultdict
import time
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from typing import Callable

from . import blockliste as blockliste_mod, clients, db, stellen as S, transforms as T
from .clients import ApiError, FindymailClient, SkaelClient
from .config import CONFIG, PORTALE
from .llm import LLM

log = logging.getLogger(__name__)

MAX_ATTEMPTS = 3
LEBENSZEICHEN_S = 60   # spätestens so oft meldet eine laufende Stufe ihren Stand

# Budget-Deckel (run --budget, testballon): stoppt jede bezahlte Stufe, sobald die echten
# Skael-Credits das Budget erreichen. Gesetzt von kostenzaehler_starten().
BUDGET_OK: Callable[[], bool] | None = None
CREDITS_JE_EURO = 1000   # Skael: 1.000 Credits ≈ 1 €


def kostenzaehler_starten(conn: sqlite3.Connection) -> None:
    """Echte Skael-Credits je fertigem Auftrag buchen (Tabelle `kosten`) und das Budget prüfen.

    Das Budget (`budget_credits` in run_meta) gilt für die Datenabfragen bei Skael, nicht für
    KI-Schritte. Laufende Aufträge werden noch fertig — der Deckel kann um die Kosten von
    höchstens MAX_CONCURRENCY Aufträgen überschritten werden.
    """
    global BUDGET_OK
    stand = {"credits": db.kosten_summe(conn)}
    sperre = threading.Lock()

    def buchen(endpoint: str, credits: float) -> None:
        db.kosten_buchen(conn, endpoint, credits)
        with sperre:
            stand["credits"] += credits

    clients.KOSTEN_ERFASSEN = buchen
    budget = float(db.get_meta(conn, "budget_credits", 0) or 0)
    BUDGET_OK = (lambda: stand["credits"] < budget) if budget > 0 else None
    if budget > 0:
        log.info("Budget: %.0f von %.0f Credits verbraucht", stand["credits"], budget)


def budget_ok() -> bool:
    return BUDGET_OK is None or BUDGET_OK()


def stufe_sicher(name: str, stufe: Callable, *args, **kwargs) -> bool:
    """Eine Stufe ausführen; ein unerwarteter Fehler beendet nur diese Stufe, nicht den Lauf.

    Fehler einzelner Zeilen fangen die Stufen selbst ab (note_failure). Hier geht es um alles
    andere, z. B. eine gesperrte Datenbank. Die Stufen sind idempotent — der nächste Lauf macht
    an derselben Stelle weiter. SystemExit (fehlende Einstellung) bricht weiterhin ab.
    """
    try:
        stufe(*args, **kwargs)
        return True
    except Exception as exc:  # noqa: BLE001
        log.exception("Stufe %s abgebrochen: %s — weiter mit der nächsten Stufe", name, exc)
        return False


def einstellung(conn: sqlite3.Connection, key: str, default):
    """Kampagnen-Einstellung aus run_meta, sonst der Wert aus .env."""
    wert = db.get_meta(conn, key)
    if wert in (None, ""):
        return default
    if isinstance(default, bool):
        return str(wert).strip().lower() in {"1", "true", "yes", "ja", "on"}
    if isinstance(default, int):
        try:
            return int(float(wert))
        except ValueError:
            return default
    return wert


def _run_parallel(items: list, worker: Callable, desc: str, max_workers: int | None = None) -> None:
    """Führt worker(item) parallel aus und protokolliert den Fortschritt."""
    if not items:
        log.info("%s: nichts zu tun", desc)
        return
    workers = max_workers or CONFIG.max_concurrency
    done = failed = gestoppt = 0

    def ausfuehren(item) -> bool:
        if not budget_ok():
            return False   # Budget erreicht: Zeile bleibt offen, nächster Lauf macht weiter
        worker(item)
        return True

    start = letzte_meldung = time.monotonic()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        offen = {pool.submit(ausfuehren, item) for item in items}
        while offen:
            # höchstens LEBENSZEICHEN_S warten, dann melden — langsame Dienste sehen sonst wie Stillstand aus
            fertig, offen = wait(offen, timeout=LEBENSZEICHEN_S, return_when=FIRST_COMPLETED)
            for future in fertig:
                try:
                    if future.result() is False:
                        gestoppt += 1
                except Exception as exc:  # noqa: BLE001
                    failed += 1
                    log.error("%s: %s", desc, exc)
                done += 1
                if done % 25 == 0 or done == len(items):
                    log.info("%s: %s/%s (%s Fehler)", desc, done, len(items), failed)
                    letzte_meldung = time.monotonic()
            if offen and time.monotonic() - letzte_meldung >= LEBENSZEICHEN_S:
                log.info("%s: läuft – %s/%s fertig, %s Fehler, seit %.0f min", desc, done, len(items),
                         failed, (time.monotonic() - start) / 60)
                letzte_meldung = time.monotonic()
    if gestoppt:
        log.warning("%s: Budget erreicht — %s Zeilen nicht bearbeitet", desc, gestoppt)


# ====================================================================== 1
def stufe1_staedte(conn: sqlite3.Connection, skael: SkaelClient) -> None:
    """Clay EINGABE — find_cities je Keyword × Land, Fan-out nach VERARBEITUNG."""
    rows = conn.execute("SELECT * FROM eingabe WHERE status != 'done'").fetchall()
    log.info("Stufe 1 — Städte auflösen: %s offene Kombinationen", len(rows))

    def work(row: sqlite3.Row) -> None:
        try:
            out = skael.find_cities(row["country_code"], row["min_population"], CONFIG.cities_limit)
        except ApiError as exc:
            db.update(conn, "eingabe", row["id"], {"status": "pending", "error": str(exc)[:500]})
            raise

        cities = out.get("cities") or []
        for city in cities:
            name = city.get("name")
            if not name:
                continue
            db.upsert(conn, "verarbeitung", {
                "eingabe_id": row["id"],
                "input_keyword": row["keyword"],
                "input_city": name,
                "input_country": row["country_code"],
                "population": city.get("population"),
                "query": T.build_query(row["keyword"], name, row["country_code"]),
            }, conflict=("eingabe_id", "query"))

        db.update(conn, "eingabe", row["id"], {
            "status": "done",
            "error": None,
            "cities_total": out.get("total"),
            "cities_fetched": len(cities),
        })
        if out.get("total") and len(cities) < out["total"]:
            log.warning(
                "%s: nur %s von %s Städten geholt — CITIES_LIMIT erhöhen für vollständige Abdeckung",
                row["country_code"], len(cities), out["total"],
            )

    _run_parallel(list(rows), work, "Stufe 1", max_workers=3)


# ====================================================================== 2
def stufe2_maps(conn: sqlite3.Connection, skael: SkaelClient, limit: int | None = None) -> None:
    """Clay VERARBEITUNG — maps_search je Stadt-Query, Fan-out nach DATENSÄTZE."""
    sql = (
        "SELECT * FROM verarbeitung WHERE status != 'done' AND attempts < ? "
        "ORDER BY population DESC"
    )
    params: list = [MAX_ATTEMPTS]
    if limit:
        sql += " LIMIT ?"
        params.append(int(limit))
    rows = conn.execute(sql, params).fetchall()
    log.info("Stufe 2 — Google Maps: %s offene Queries", len(rows))

    def work(row: sqlite3.Row) -> None:
        try:
            out = skael.maps_search(row["query"])
        except ApiError as exc:
            db.note_failure(conn, "verarbeitung", row["id"], str(exc))
            raise

        if T.contains_error(out):
            db.note_failure(conn, "verarbeitung", row["id"], "Antwort als Fehler markiert")
            return

        items = out.get("items") or []
        for index, item in enumerate(items):
            # Clay routet alle items weiter. business_id ist laut Skael-Doku immer
            # gesetzt; fehlt es doch, wird ein Ersatzschlüssel gebildet, damit die
            # Firma nicht stillschweigend verloren geht.
            business_id = item.get("business_id") or item.get("place_id") \
                or f"synthetic:{row['id']}:{index}"
            phones = item.get("phone_numbers") or []
            phone = phones[0] if phones else ""
            db.upsert(conn, "datensaetze", {
                "verarbeitung_id": row["id"],
                "business_id": business_id,
                # Rohantwort vollstaendig behalten: Felder, die heute nicht
                # ausgewertet werden, sind fuer spaetere Kampagnen noch da,
                # ohne dass erneut gescrapt werden muss.
                "maps_raw": json.dumps(item, ensure_ascii=False),
                "place_id": item.get("place_id"),
                "firmenname": item.get("name"),
                "website": item.get("website"),
                "address": item.get("full_address"),
                "zip": item.get("zip_code"),
                "category": item.get("type"),
                "phone": phone,
                "phone_export": T.phone_number_export(phone),
                "rating": item.get("rating"),
                "review_count": item.get("review_count"),
                "query": row["query"],
                "query_keyword": row["input_keyword"],
                "query_city": row["input_city"],
                "query_country": row["input_country"],
            }, conflict=("business_id",))

        db.update(conn, "verarbeitung", row["id"], {
            "status": "done",
            "error": None,
            "items_total": out.get("total") or len(items),
        })

    _run_parallel(list(rows), work, "Stufe 2")


# ============================================================ 1j/1k Stellensuche
def nur_stellen(conn: sqlite3.Connection) -> bool:
    """Stellensuche ohne Anreicherung: nur Stellen- und Firmenliste, keine Kontaktdaten."""
    return db.pfad(conn) == "stellensuche" and bool(einstellung(conn, "nur_stellen", False))


def titel_ausschluss(conn: sqlite3.Connection, key: str = "titel_ausschluss") -> list[str]:
    """Wortteile für den Titel-Filter (run_meta, kommagetrennt): `titel_ausschluss` bzw. `titel_pflicht`."""
    return [w.strip().lower() for w in str(db.get_meta(conn, key, "") or "").split(",") if w.strip()]


def stufe1j_stellensuche(conn: sqlite3.Connection, skael: SkaelClient, limit: int | None = None) -> None:
    """Jobportale je Portal × Suchbegriff × Ort abfragen, je Anzeige eine Zeile in `stellen`.

    Eine Seite kostet 1 Credit (bis 100 Anzeigen). Höchstens `stellen_max_seiten` Seiten je
    Suche. Bei einem Fehler bleibt die Suche offen und beginnt beim nächsten Lauf neu —
    schon gespeicherte Anzeigen werden dabei nur aktualisiert, nicht verdoppelt.

    Weiterblättern: Wird `stellen_max_seiten` erhöht, machen erledigte Suchen mit weiteren
    Seiten bei der nächsten Seite weiter. Indeed braucht dafür den gespeicherten Blätter-Code;
    fehlt er (ältere Läufe), wird ab Seite 1 neu abgefragt.
    """
    if db.pfad(conn) != "stellensuche":
        log.info("Stufe 1j übersprungen (nur Pfad Stellensuche)")
        return
    max_seiten = einstellung(conn, "stellen_max_seiten", CONFIG.stellen_max_seiten)
    max_alter = einstellung(conn, "stellen_max_alter", CONFIG.stellen_max_alter)
    umkreis = einstellung(conn, "stellen_umkreis", CONFIG.stellen_umkreis)
    titel_raus = titel_ausschluss(conn)
    titel_muss = titel_ausschluss(conn, "titel_pflicht")

    # offen, oder erledigt mit weiteren Seiten (ältere Läufe ohne `weiter`: letzte Seite war voll)
    sql = ("SELECT * FROM stellen_suche WHERE attempts < ? AND (status != 'done' OR (seiten < ? AND "
           "(weiter = 1 OR (weiter IS NULL AND treffer >= seiten * ?)))) ORDER BY id")
    params: list = [MAX_ATTEMPTS, max_seiten, S.SEITE_GROESSE]
    if limit:
        sql += " LIMIT ?"
        params.append(int(limit))
    rows = conn.execute(sql, params).fetchall()
    log.info("Stufe 1j — Jobportale: %s offene Suchen (je bis %s Seiten)", len(rows), max_seiten)

    def work(row: sqlite3.Row) -> None:
        endpoint = PORTALE[row["portal"]]["endpoint"]
        seite, cursor, gesamt = 1, None, 0
        if row["status"] == "done":
            if row["portal"] != "indeed" or row["cursor"]:
                seite, cursor, gesamt = row["seiten"] + 1, row["cursor"], row["treffer"]
        while True:
            payload = S.anfrage(row["portal"], row["suchbegriff"], row["ort"], row["land"],
                                seite=seite, cursor=cursor, umkreis=umkreis, max_alter=max_alter)
            try:
                out = skael.stellen_suche(endpoint, payload)
            except ApiError as exc:
                db.note_failure(conn, "stellen_suche", row["id"], f"{row['portal']} Seite {seite}: {exc}")
                return
            gefunden = S.stellen_aus_antwort(row["portal"], out, CONFIG.stellen_beschreibung_max)
            for stelle in gefunden:
                db.upsert(conn, "stellen", {
                    **stelle,
                    "suche_id": row["id"],
                    "suchbegriff": row["suchbegriff"],
                    "land": stelle["land"] or row["land"],
                    "ausschluss": S.ausschluss(stelle, max_alter, titel_ausschluss=titel_raus,
                                               titel_pflicht=titel_muss),
                }, conflict=("portal", "portal_id"))
            gesamt += len(gefunden)
            weiter, cursor = S.naechste_seite(row["portal"], out, seite, len(gefunden))
            if not weiter or seite >= max_seiten:
                break
            seite += 1
        db.update(conn, "stellen_suche", row["id"], {
            "status": "done", "seiten": seite, "treffer": gesamt, "weiter": 1 if weiter else 0,
            "cursor": cursor, "error": None})

    # Skael erlaubt 10.000 Anfragen/Minute; Portalsuchen dauern 2–15 s → Parallelität über MAX_CONCURRENCY
    _run_parallel(list(rows), work, "Stufe 1j")


def _stelle_als_dict(row: sqlite3.Row) -> dict:
    return {key: row[key] for key in row.keys()}


def stufe1k_firmen(conn: sqlite3.Connection) -> None:
    """Übernommene Stellen je Firma bündeln → eine Zeile je Firma in `datensaetze`.

    Schlüssel: Website laut Portal, sonst der bereinigte Firmenname, sonst der Host des
    Bewerbungslinks. Nennt ein Portal für einen Namen die Website, gilt sie für alle
    Stellen dieses Namens — das spart die Domain-Suche. Kostet nichts.
    """
    if db.pfad(conn) != "stellensuche":
        log.info("Stufe 1k übersprungen (nur Pfad Stellensuche)")
        return

    # Filter mit den aktuellen Einstellungen neu anwenden — so lassen sich Alter und
    # Titel-Ausschlüsse nach dem Testlauf ändern, ohne die Portale erneut abzufragen.
    max_alter = einstellung(conn, "stellen_max_alter", CONFIG.stellen_max_alter)
    titel_raus = titel_ausschluss(conn)
    titel_muss = titel_ausschluss(conn, "titel_pflicht")
    alle = [_stelle_als_dict(r) for r in conn.execute("SELECT * FROM stellen").fetchall()]
    with db.write(conn):
        conn.executemany("UPDATE stellen SET ausschluss=? WHERE id=?", [
            (S.ausschluss(s, max_alter, titel_ausschluss=titel_raus, titel_pflicht=titel_muss), s["id"]) for s in alle])
        # Stellen, die jetzt rausfallen, verlieren ihre Firma
        conn.execute("UPDATE stellen SET datensatz_id=NULL WHERE ausschluss IS NOT NULL")

    stellen = [_stelle_als_dict(r) for r in
               conn.execute("SELECT * FROM stellen WHERE ausschluss IS NULL ORDER BY id").fetchall()]

    host_je_name: dict[str, str] = {}
    for s in stellen:
        host = S.firmen_host(s)
        if host and s["firma"]:
            host_je_name.setdefault(S.firmen_name_schluessel(s["firma"]), host)

    gruppen: dict[str, list[dict]] = defaultdict(list)
    for s in stellen:
        name = S.firmen_name_schluessel(s["firma"])
        host = S.firmen_host(s) or host_je_name.get(name, "")
        schluessel = f"web:{host}" if host else (f"name:{name}" if name else f"hinweis:{S.bewerben_host(s)}")
        s["_host"] = host
        gruppen[schluessel].append(s)

    neu = 0
    for schluessel, gruppe in gruppen.items():
        beste = S.beste_stelle(gruppe)
        host = next((s["_host"] for s in gruppe if s["_host"]), "")
        firma = beste["firma"] or next((s["firma"] for s in gruppe if s["firma"]), "") \
            or host or S.bewerben_host(beste)
        felder = {
            "firmenname": firma,
            "zip": beste["plz"] or "",
            "address": " ".join(t for t in (beste["plz"], beste["ort"]) if t),
            "category": "Stellenanzeige",
            "query": beste["suchbegriff"],
            "query_keyword": beste["suchbegriff"],
            "query_city": beste["ort"] or "",
            "query_country": beste["land"] or "",
            "quelle": "stellen",
            "stelle_vorhanden": 1,
            "job_title": beste["titel"],
            "job_description": beste["beschreibung"] or "",
            "job_bereich": "",
            "stelle_url": beste["url"],
            "stelle_portal": beste["portal"],
            "stelle_datum": beste["veroeffentlicht"],
            "stelle_ort": beste["ort"],
            "stelle_gehalt": beste["gehalt"],
            "stellen_anzahl": len(gruppe),
            "stellen_portale": ", ".join(sorted({s["portal"] for s in gruppe})),
        }
        business_id = f"stelle:{schluessel}"
        vorhanden = conn.execute("SELECT id, website FROM datensaetze WHERE business_id=?",
                                 (business_id,)).fetchone()
        if vorhanden:
            ds_id = vorhanden["id"]
            if host and not vorhanden["website"]:
                felder["website"] = f"https://{host}"
            db.update(conn, "datensaetze", ds_id, felder)
        else:
            ds_id = db.upsert(conn, "datensaetze", {
                "business_id": business_id,
                "website": f"https://{host}" if host else "",
                "domain_status": "portal" if host else None,
                **felder,
            }, conflict=("business_id",))
            neu += 1
        with db.write(conn):
            conn.executemany("UPDATE stellen SET datensatz_id=? WHERE id=?",
                             [(ds_id, s["id"]) for s in gruppe])
    with db.write(conn):
        # Firmen, deren Stellen alle herausgefiltert wurden — 3b sortiert sie aus
        conn.execute("UPDATE datensaetze SET stellen_anzahl=0 WHERE quelle='stellen' AND id NOT IN "
                     "(SELECT datensatz_id FROM stellen WHERE datensatz_id IS NOT NULL)")
    log.info("Stufe 1k — %s Stellen bei %s Firmen (%s neu)", len(stellen), len(gruppen), neu)


def _stellen_nach_dedupe(conn: sqlite3.Connection) -> None:
    """Stellen doppelter Firmen der behaltenen Zeile zuordnen und Zähler neu bilden.

    Zwei Firmennamen können erst nach der Domain-Suche als dieselbe Firma erkannt
    werden (gleiche Website). Die Dedupe in 3b behält die ältere Zeile; ihre Stellen
    dürfen dabei nicht verloren gehen.
    """
    with db.write(conn):
        conn.execute("""
            UPDATE stellen SET datensatz_id = (
                SELECT MIN(k.id) FROM datensaetze k JOIN datensaetze d ON d.dedupe_key = k.dedupe_key
                 WHERE d.id = stellen.datensatz_id AND k.dedupe_status = 'kept')
             WHERE datensatz_id IN (SELECT id FROM datensaetze WHERE dedupe_status='dropped_duplicate')
        """)
        conn.execute("""
            UPDATE datensaetze SET
                stellen_anzahl = (SELECT COUNT(*) FROM stellen s WHERE s.datensatz_id = datensaetze.id
                                   AND s.ausschluss IS NULL),
                stellen_portale = (SELECT GROUP_CONCAT(portal, ', ') FROM
                                   (SELECT DISTINCT portal FROM stellen s WHERE s.datensatz_id = datensaetze.id
                                     AND s.ausschluss IS NULL ORDER BY portal))
             WHERE quelle = 'stellen' AND dedupe_status = 'kept'
        """)
        conn.execute("UPDATE datensaetze SET dedupe_status='dropped_excluded' "
                     "WHERE quelle='stellen' AND dedupe_status='kept' AND COALESCE(stellen_anzahl, 0) = 0")


# ====================================================================== 3
# Größen-Check (3g): diese Kategorien fallen vor der Website-Suche heraus
GROESSE_AUSSCHLUSS = {
    "konzern": "Konzern",
    "oeffentlich_verband": "öffentliche Hand/Verband",
    "it_wettbewerber": "IT-Wettbewerber",
}


def groessen_check(conn: sqlite3.Connection) -> bool:
    """Stellensuche mit Anreicherung: Größen-Check aktiv (run_meta `groessen_check`, Standard an)."""
    return (db.pfad(conn) == "stellensuche" and not nur_stellen(conn)
            and bool(einstellung(conn, "groessen_check", True)))


def _groesse_bedingung(conn: sqlite3.Connection) -> str:
    """SQL-Zusatz für 3a und 3c: Aussortierte nie bezahlt prüfen, bei aktivem Check erst nach 3g."""
    if db.pfad(conn) != "stellensuche":
        return ""
    raus = ", ".join(f"'{k}'" for k in GROESSE_AUSSCHLUSS)
    sql = f" AND COALESCE(groesse_kategorie, '') NOT IN ({raus})"
    if groessen_check(conn):
        sql += " AND groesse_kategorie IS NOT NULL"
    return sql


def stufe3g_groesse(conn: sqlite3.Connection, llm: LLM) -> None:
    """Stellensuche: Konzerne, öffentliche Hand/Verbände und IT-Wettbewerber vor 3a aussortieren.

    Das Prüfprofil (3c) sieht nur die Startseite — Zalando, Miele oder CHECK24 zeigen dort
    weder Mitarbeiterzahl noch Investor Relations. Der Check fragt deshalb das Modellwissen
    zu Firmenname (und Website laut Portal) ab, bevor find_domain bezahlt wird. Aussortierte
    bleiben in der Dedupe `kept`, bekommen is_icp=0 und stehen in Liste 4.
    """
    if db.pfad(conn) != "stellensuche":
        log.info("Stufe 3g übersprungen (nur Pfad Stellensuche)")
        return
    if not CONFIG.quali_on:
        log.info("Stufe 3g übersprungen (QUALI_ON=false)")
        return
    if nur_stellen(conn):
        log.info("Stufe 3g übersprungen (nur Stellenliste, keine Anreicherung)")
        return
    if not groessen_check(conn):
        log.info("Stufe 3g übersprungen (Größen-Check für diese Kampagne abgeschaltet)")
        return
    rows = conn.execute(
        "SELECT id, firmenname, website, website_final, stelle_ort, query_city FROM datensaetze "
        "WHERE quelle='stellen' AND dedupe_status='kept' AND groesse_kategorie IS NULL "
        "AND attempts < ? ORDER BY id",
        (MAX_ATTEMPTS,),
    ).fetchall()
    log.info("Stufe 3g — Größen-Check (%s): %s Firmen", CONFIG.model_groesse, len(rows))

    def work(row: sqlite3.Row) -> None:
        result = llm.groessen_check(row["firmenname"] or "", row["website_final"] or row["website"] or "",
                                    row["stelle_ort"] or row["query_city"] or "")
        if result is None:
            db.note_failure(conn, "datensaetze", row["id"], "Größen-Check fehlgeschlagen")
            return
        kategorie = result.get("kategorie") or ""
        if kategorie not in (*GROESSE_AUSSCHLUSS, "mittelstand"):
            kategorie = "unbekannt"
        daten = {"groesse_raw": json.dumps(result, ensure_ascii=False), "groesse_kategorie": kategorie,
                 "error": None}
        if kategorie in GROESSE_AUSSCHLUSS:
            schaetzung = (result.get("mitarbeitende_schaetzung") or "").strip() or "unbekannt"
            if "mitarbeit" not in schaetzung.lower() and schaetzung != "unbekannt":
                schaetzung += " Mitarbeitende"
            grund = f"Größen-Check: {GROESSE_AUSSCHLUSS[kategorie]} ({schaetzung})"
            if result.get("begruendung"):
                grund += f" – {result['begruendung']}"
            daten.update({"is_icp": 0, "icp_label": "False", "icp_confidence": None,
                          "icp_reason": grund, "status": "icp_done"})
        db.update(conn, "datensaetze", row["id"], daten)

    _run_parallel(list(rows), work, "Stufe 3g", max_workers=min(CONFIG.max_concurrency, 4))
    raus = conn.execute("SELECT COUNT(*) FROM datensaetze WHERE groesse_kategorie IN "
                        f"({', '.join(repr(k) for k in GROESSE_AUSSCHLUSS)})").fetchone()[0]
    log.info("Stufe 3g — %s Firmen insgesamt aussortiert (Konzern, öffentlich/Verband, IT-Wettbewerber)", raus)


def _domains_stellensuche(conn: sqlite3.Connection, skael: SkaelClient, limit: int | None = None) -> None:
    """Stellensuche: eigene Website über Skael find_domain, belegt durch das Impressum.

    Stepstone und Arbeitsagentur nennen nur den Firmennamen. Eine nur geratene Domain
    sortiert 3b aus; find_domain liefert dagegen nur eine Domain, deren Impressum genau
    diese Firma nennt (status `verified`). Ohne Beleg bleibt die Website leer — die Firma
    steht dann im Export als „keine eigene Website gefunden“. Rund 15–22 Credits je Firma.
    Firmen, die der Größen-Check (3g) aussortiert hat, werden nicht gesucht.
    """
    bedingung = _groesse_bedingung(conn)
    rows = conn.execute(
        "SELECT id, firmenname, zip, query_city, query_country, query_keyword, job_title FROM datensaetze "
        "WHERE quelle='stellen' AND dedupe_status='kept' AND COALESCE(website,'')='' "
        f"AND domain_status IS NULL AND attempts < ?{bedingung} ORDER BY id LIMIT ?",
        (MAX_ATTEMPTS, int(limit) if limit else -1),
    ).fetchall()
    log.info("Stufe 3a — Website per Impressum-Beleg (find_domain): %s Firmen", len(rows))
    if groessen_check(conn):
        offen = conn.execute(
            "SELECT COUNT(*) FROM datensaetze WHERE quelle='stellen' AND dedupe_status='kept' "
            "AND COALESCE(website,'')='' AND domain_status IS NULL AND groesse_kategorie IS NULL "
            "AND attempts < ?", (MAX_ATTEMPTS,)).fetchone()[0]
        if offen:
            log.info("Stufe 3a — %s Firmen warten auf den Größen-Check (run --stage 3g)", offen)

    # Bewerbungslink auf eigener Domain: wird zuerst geprüft, zählt aber nur mit Impressum-Beleg.
    # Vorab im Hauptthread lesen — parallele Cursor auf derselben Verbindung kollidieren sonst.
    hinweise: dict[int, str] = {}
    for s in conn.execute("SELECT datensatz_id, bewerben_url FROM stellen WHERE datensatz_id IS NOT NULL "
                          "ORDER BY id").fetchall():
        if not hinweise.get(s["datensatz_id"]):
            hinweise[s["datensatz_id"]] = S.bewerben_host({"bewerben_url": s["bewerben_url"]})

    def work(row: sqlite3.Row) -> None:
        hinweis = hinweise.get(row["id"], "")
        try:
            out = skael.find_domain(
                row["firmenname"] or "", city=row["query_city"] or "", postcode=row["zip"] or "",
                country=row["query_country"] or "DE",
                context=f"Arbeitgeber mit offener Stelle „{row['job_title']}“ (Suche: {row['query_keyword']})",
                website=f"https://{hinweis}" if hinweis else "",
                max_pages=CONFIG.find_domain_max_pages)
        except ApiError as exc:
            db.note_failure(conn, "datensaetze", row["id"], f"find_domain: {exc}")
            return
        status = out.get("status") or "none"
        if status in ("queued", "processing", "waiting", "timeout"):
            # Ergebnis noch nicht fertig — nicht als „nichts gefunden“ speichern, später erneut abholen
            db.note_failure(conn, "datensaetze", row["id"], f"find_domain noch nicht fertig ({status})")
            return
        domain = T.host_of(out.get("domain")) if status == "verified" else ""
        db.update(conn, "datensaetze", row["id"], {
            "domain_raw": json.dumps(out, ensure_ascii=False),
            "domain_status": status,
            "domain_url": "",
            "website": f"https://{domain}" if domain else "",
            "error": None,
        })

    # find_domain rechnet bei Skael asynchron (~60 s) — Parallelität über MAX_CONCURRENCY
    _run_parallel(list(rows), work, "Stufe 3a")


def domain_suchen(skael: SkaelClient | None, llm: LLM, firmenname: str, stadt: str = "",
                  land: str = "") -> str | None:
    """Domain einer Firma ohne Website — je nach DOMAINSUCHE über Skael (Impressum-geprüft) oder OpenAI.

    Rückgabe: URL oder "" (nichts gefunden), None bei technischem Fehler (→ erneut versuchen).
    """
    if CONFIG.domainsuche == "skael":
        try:
            out = (skael or SkaelClient()).find_domain(firmenname, city=stadt, country=land)
        except ApiError as exc:
            log.warning("find_domain fehlgeschlagen für %r: %s", firmenname, exc)
            return None
        domain = out.get("domain") if out.get("status") == "verified" else None
        return f"https://{domain}/" if domain else ""
    # Stadt dazu, sonst rät die Suche bei Allerweltsnamen ("Architekturbüro Lode") daneben
    suche = " ".join(t for t in (firmenname, stadt) if t)
    return llm.company_domain(suche)


def stufe3a_domains(conn: sqlite3.Connection, llm: LLM, skael: SkaelClient | None = None,
                    limit: int | None = None) -> None:
    """Clay DATENSÄTZE.`Domain URL` — Domainsuche, wenn Maps keine Website liefert.

    Clay nutzt hier Claygent. Hier: DOMAINSUCHE=skael (Standard) | openai | aus.
    Stellensuche: immer Skael find_domain mit Impressum-Beleg (`_domains_stellensuche`) —
    Stepstone und Arbeitsagentur nennen nur den Firmennamen.
    """
    if db.pfad(conn) == "stellensuche":
        if not CONFIG.quali_on or nur_stellen(conn):
            log.info("Stufe 3a übersprungen (QUALI_ON=false bzw. nur Stellenliste)")
            return
        _domains_stellensuche(conn, skael or SkaelClient(), limit=limit)
        return
    if not CONFIG.quali_on or CONFIG.domainsuche == "aus":
        log.info("Stufe 3a übersprungen (QUALI_ON=false bzw. DOMAINSUCHE=aus)")
        return
    rows = [r for r in conn.execute(
        "SELECT id, firmenname, website, query_city, query_country FROM datensaetze "
        "WHERE domain_url IS NULL AND firmenname IS NOT NULL AND attempts < ?",
        (MAX_ATTEMPTS,),
    ).fetchall() if not r["website"] or T.ist_plattform(r["website"])]
    log.info("Stufe 3a — Domainsuche (%s): %s Firmen ohne Website", CONFIG.domainsuche, len(rows))

    def work(row: sqlite3.Row) -> None:
        response = domain_suchen(skael, llm, row["firmenname"], row["query_city"] or "",
                                 row["query_country"] or "")
        if response is None:
            db.note_failure(conn, "datensaetze", row["id"], "Domainsuche fehlgeschlagen")
            return
        db.update(conn, "datensaetze", row["id"], {"domain_url": response, "error": None})

    _run_parallel(list(rows), work, "Stufe 3a", max_workers=min(CONFIG.max_concurrency, 4))


def stufe3b_dedupe(conn: sqlite3.Connection) -> None:
    """Clay DATENSÄTZE.`Website final` + `Dedupe` + Auto-Dedupe (keep oldest)."""
    rows = conn.execute("SELECT id, website, domain_url FROM datensaetze").fetchall()
    log.info("Stufe 3b — Website final + Dedupe-Schlüssel für %s Zeilen", len(rows))

    for row in rows:
        website_final = T.website_final(row["website"], row["domain_url"])
        db.update(conn, "datensaetze", row["id"], {
            "website_final": website_final,
            "dedupe_key": T.dedupe_key(website_final, bool(row["domain_url"])),
        })

    # "DEDUPE" markiert in Clay die Zeilen, die durch die Auto-Dedupe verschwinden
    # (nicht-DACH-TLD bzw. nur geratene Website). Hier explizit als ausgeschlossen
    # markiert statt gelöscht — nachvollziehbar und reversibel.
    with db.write(conn):
        # 'deferred_menge' = bewusst zurückgestellt (Zielmenge erreicht) — bleibt unangetastet
        conn.execute("UPDATE datensaetze SET dedupe_status='dropped_excluded' "
                     "WHERE dedupe_key='DEDUPE' AND dedupe_status <> 'deferred_menge'")
        conn.execute("UPDATE datensaetze SET dedupe_status='kept' "
                     "WHERE dedupe_key <> 'DEDUPE' AND dedupe_status <> 'deferred_menge'")
        conn.execute("""
            UPDATE datensaetze SET dedupe_status='dropped_duplicate'
            WHERE dedupe_status <> 'deferred_menge' AND dedupe_key IS NOT NULL AND dedupe_key <> '' AND dedupe_key <> 'DEDUPE'
              AND id NOT IN (SELECT MIN(id) FROM datensaetze
                             WHERE dedupe_key IS NOT NULL AND dedupe_key <> '' AND dedupe_key <> 'DEDUPE'
                             GROUP BY dedupe_key)
        """)

    # Eigene Blockliste (bereits kontaktierte Firmen): vor ICP-Check und Anreicherung raus.
    sperre = blockliste_mod.laden()
    if len(sperre):
        kandidaten = conn.execute(
            "SELECT id, website_final FROM datensaetze WHERE dedupe_status='kept' AND website_final <> ''"
        ).fetchall()
        blockiert = [r["id"] for r in kandidaten if sperre.treffer(r["website_final"])]
        with db.write(conn):
            conn.executemany("UPDATE datensaetze SET dedupe_status='dropped_blocked' WHERE id=?",
                             [(i,) for i in blockiert])
        log.info("Stufe 3b — %s Firmen wegen eigener Blockliste übersprungen", len(blockiert))

    if db.pfad(conn) == "stellensuche":
        _stellen_nach_dedupe(conn)

    kept = conn.execute("SELECT COUNT(*) FROM datensaetze WHERE dedupe_status='kept'").fetchone()[0]
    log.info("Stufe 3b — %s Zeilen bleiben nach Dedupe", kept)


def stufe3c_icp(conn: sqlite3.Connection, skael: SkaelClient, icp_prompt: str) -> None:
    """Clay DATENSÄTZE.`ICP Check` — Website gegen den ICP-Prompt prüfen."""
    if not CONFIG.quali_on:
        log.info("Stufe 3c übersprungen (QUALI_ON=false)")
        return
    if nur_stellen(conn):
        log.info("Stufe 3c übersprungen (nur Stellenliste, keine Anreicherung)")
        return
    # Stellensuche: vom Größen-Check Aussortierte nicht prüfen, bei aktivem Check erst nach 3g
    bedingung = _groesse_bedingung(conn)
    if db.pfad(conn) in ("stellensuche", "recruiting") and not icp_prompt.strip():
        # Ohne Prüfprofil ist die offene Stelle selbst das Kriterium (Recruiting: Stufe 3e prüft
        # sie danach auf der Website). Ohne eigene Website lässt sich nicht anreichern — diese
        # Firmen bleiben ungeprüft (Export: Liste 4).
        with db.write(conn):
            cur = conn.execute(f"""
                UPDATE datensaetze SET is_icp=1, icp_label='True', status='icp_done',
                       icp_reason='ohne Prüfprofil: offene Stelle ist das Kriterium'
                 WHERE dedupe_status='kept' AND COALESCE(website_final,'') <> '' AND is_icp IS NULL{bedingung}
            """)
        log.info("Stufe 3c — ohne Prüfprofil: %s Firmen mit Website übernommen", cur.rowcount)
        return
    if not icp_prompt.strip():
        raise SystemExit("Kein ICP-Prompt hinterlegt — bitte `scraper set-icp <datei>` ausführen.")

    rows = conn.execute(
        "SELECT id, website_final FROM datensaetze "
        f"WHERE dedupe_status='kept' AND website_final <> '' AND icp_raw IS NULL AND attempts < ?{bedingung}",
        (MAX_ATTEMPTS,),
    ).fetchall()
    log.info("Stufe 3c — ICP-Check: %s Firmen", len(rows))

    def work(row: sqlite3.Row) -> None:
        try:
            out = skael.icp_checker(row["website_final"], icp_prompt)
        except ApiError as exc:
            db.note_failure(conn, "datensaetze", row["id"], str(exc))
            return
        db.update(conn, "datensaetze", row["id"], {
            "icp_raw": json.dumps(out, ensure_ascii=False),
            "is_icp": 1 if out.get("icp") is True else (0 if out.get("icp") is False else None),
            "icp_confidence": out.get("confidence"),
            "icp_reason": out.get("reason"),
            "icp_label": T.icp_label(out),
            "status": "icp_done",
            "error": None,
        })

    _run_parallel(list(rows), work, "Stufe 3c")


def _webseite_holen(conn: sqlite3.Connection, skael: SkaelClient, row: sqlite3.Row) -> dict | None:
    """Startseite über Skael abrufen oder die schon bezahlte Antwort wiederverwenden.

    Neu geholte Daten werden SOFORT gespeichert — vor den KI-Schritten, die noch
    scheitern können. Sonst kostet jeder Wiederholungslauf den Abruf erneut.
    """
    if row["webscraper_raw"]:
        return json.loads(row["webscraper_raw"])
    try:
        out = skael.web_scraper(row["website_final"])
    except ApiError as exc:
        db.note_failure(conn, "datensaetze", row["id"], f"Webscraper: {exc}")
        return None
    db.update(conn, "datensaetze", row["id"], {"webscraper_raw": json.dumps(out, ensure_ascii=False)})
    return out


def stufe3e_stellen(conn: sqlite3.Connection, skael: SkaelClient, llm: LLM) -> None:
    """Clay DATENSÄTZE.`Stelle` + `Stelle vorhanden` + `JOB TITLE` + `JOB DESCRIPTION`.

    Nur Pfad Recruiting. Clay lässt einen Claygent die Website durchsuchen. Lokal:
    Startseite abrufen, bis zu KARRIERE_SEITEN Karriere-/Jobseiten der eigenen
    Domain nachladen, den Text an die Stellenanalyse geben. Quelle ist allein die Firmen-Website.
    """
    if db.pfad(conn) != "recruiting":
        log.info("Stufe 3e übersprungen (nur Pfad Recruiting)")
        return
    if not CONFIG.quali_on:
        log.info("Stufe 3e übersprungen (QUALI_ON=false)")
        return
    rows = conn.execute(
        "SELECT id, website_final, webscraper_raw FROM datensaetze "
        "WHERE dedupe_status='kept' AND is_icp=1 AND stelle_vorhanden IS NULL "
        "AND website_final <> '' AND attempts < ?",
        (MAX_ATTEMPTS,),
    ).fetchall()
    log.info("Stufe 3e — Stellen-Erkennung: %s Firmen", len(rows))
    # Gesuchte Berufe der Kampagne (init --berufe), eine Zeile je Beruf, Reihenfolge = Priorität
    berufe = db.get_meta(conn, "berufe", "") or ""

    def work(row: sqlite3.Row) -> None:
        url = row["website_final"]
        home = _webseite_holen(conn, skael, row)
        if home is None:
            return
        seiten = [(url, home)]
        for link in T.karriere_links(home, CONFIG.karriere_seiten, basis=url):
            try:
                seiten.append((link, skael.web_scraper(link)))
            except ApiError as exc:
                # Eine nicht ladbare Karriereseite blockiert die Prüfung nicht
                log.warning("Karriereseite %s nicht ladbar: %s", link, exc)
        text = T.stellen_text(seiten, CONFIG.stellen_text_max)
        if not text:
            db.update(conn, "datensaetze", row["id"], {
                "stelle_raw": json.dumps({"grund": "Website ohne lesbaren Text"}),
                "stelle_vorhanden": 0, "job_title": "", "job_description": "", "job_bereich": "",
                "error": None,
            })
            return
        result = llm.stellenanalyse(url, text, berufe)
        if result is None:
            db.note_failure(conn, "datensaetze", row["id"], "Stellenanalyse fehlgeschlagen")
            return
        db.update(conn, "datensaetze", row["id"], {
            "stelle_raw": json.dumps(result, ensure_ascii=False),
            "stelle_url": ", ".join(u for u, _ in seiten[1:]) or url,
            **T.stellen_ergebnis(result),
            "error": None,
        })

    _run_parallel(list(rows), work, "Stufe 3e", max_workers=min(CONFIG.max_concurrency, 4))


def _strecke(pfad: str, stelle_vorhanden: int | None) -> str:
    if pfad == "recruiting":
        return "rc" if stelle_vorhanden == 1 else "nk"
    return "rc" if pfad == "stellensuche" else "gmaps"


def stufe3d_uebergabe(conn: sqlite3.Connection, limit: int | None = None) -> None:
    """Clay DATENSÄTZE.`Send table data` — Treffer nach ANREICHERUNG übergeben.

    Google Maps und Stellensuche: Is Icp. Recruiting: `RC SEND` (Is Icp && Stelle vorhanden),
    optional `NK SEND` (Is Icp && keine Stelle, nur mit NK_ON bzw. init --nk).
    `limit`: höchstens so viele neue Leads (Testballon: nur so viele, wie für das Ziel nötig) —
    Firmen mit offener Stelle zuerst, bei der Stellensuche die mit den meisten Anzeigen.
    """
    if not CONFIG.send_on:
        log.info("Stufe 3d übersprungen (SEND_ON=false)")
        return
    if nur_stellen(conn):
        log.info("Stufe 3d übersprungen (nur Stellenliste, keine Anreicherung)")
        return
    pfad = db.pfad(conn)
    bedingung = "d.is_icp=1"
    if pfad == "recruiting":
        nk_on = einstellung(conn, "nk_on", CONFIG.nk_on)
        bedingung += " AND (d.stelle_vorhanden=1" + (" OR d.stelle_vorhanden=0)" if nk_on else ")")
    rows = conn.execute(f"""
        SELECT d.* FROM datensaetze d
        LEFT JOIN anreicherung a ON a.datensatz_id = d.id
        WHERE d.dedupe_status='kept' AND {bedingung} AND a.id IS NULL
        ORDER BY COALESCE(d.stelle_vorhanden, 1) DESC, COALESCE(d.stellen_anzahl, 0) DESC, d.id
        LIMIT ?
    """, (int(limit) if limit else -1,)).fetchall()
    log.info("Stufe 3d — Übergabe an Anreicherung: %s neue Leads", len(rows))

    for row in rows:
        home = json.loads(row["webscraper_raw"]) if row["webscraper_raw"] else None
        db.upsert(conn, "anreicherung", {
            "quelle": row["quelle"] or "maps",
            "strecke": _strecke(pfad, row["stelle_vorhanden"]),
            "job_title": row["job_title"],
            "job_description": row["job_description"],
            "job_bereich": row["job_bereich"],
            "stelle_url": row["stelle_url"],
            "stelle_portal": row["stelle_portal"],
            "stelle_datum": row["stelle_datum"],
            "stelle_ort": row["stelle_ort"],
            "stelle_gehalt": row["stelle_gehalt"],
            "stellen_anzahl": row["stellen_anzahl"],
            "stellen_portale": row["stellen_portale"],
            # Startseite wurde in 3e schon bezahlt — 4e nutzt sie weiter
            "webscraper_raw": row["webscraper_raw"],
            "bodytext": T.bodytext(home) if home else None,
            "site_links": T.site_links(home) if home else None,
            "datensatz_id": row["id"],
            "business_id": row["business_id"],
            "place_id": row["place_id"],
            "firmenname": row["firmenname"],
            "website": row["website_final"],
            "address": row["address"],
            "zip": row["zip"],
            "category": row["category"],
            "phone_imported": row["phone"],
            "rating": row["rating"],
            "review_count": row["review_count"],
            "query": row["query"],
            "query_keyword": row["query_keyword"],
            "query_city": row["query_city"],
            "query_country": row["query_country"],
        }, conflict=("datensatz_id",))


# ====================================================================== 4
def stufe4a_website_final(conn: sqlite3.Connection, llm: LLM, skael: SkaelClient | None = None) -> None:
    """Clay ANREICHERUNG.`Company Domain` (gpt-4.1-mini) + `website [Final]`."""
    rows = conn.execute(
        "SELECT id, website, firmenname, company_domain FROM anreicherung "
        "WHERE website_final IS NULL AND attempts < ?",
        (MAX_ATTEMPTS,),
    ).fetchall()
    log.info("Stufe 4a — website [Final]: %s Leads", len(rows))

    def work(row: sqlite3.Row) -> None:
        company_domain = row["company_domain"]
        if not row["website"] and company_domain is None:
            if CONFIG.domainsuche == "aus":
                company_domain = ""
            else:
                company_domain = domain_suchen(skael, llm, row["firmenname"] or "")
            if company_domain is None:
                db.note_failure(conn, "anreicherung", row["id"], "Company Domain fehlgeschlagen")
                return
        db.update(conn, "anreicherung", row["id"], {
            "company_domain": company_domain or "",
            "website_final": T.website_final_anreicherung(row["website"], company_domain),
            "stage": "website_done",
            "error": None,
        })

    _run_parallel(list(rows), work, "Stufe 4a", max_workers=min(CONFIG.max_concurrency, 4))


def stufe4b_impressum(conn: sqlite3.Connection, skael: SkaelClient) -> None:
    """Clay ANREICHERUNG.`SKAEL Impressum` und die daraus abgeleiteten Spalten."""
    rows = conn.execute(
        "SELECT id, firmenname, website_final FROM anreicherung "
        "WHERE website_final <> '' AND impressum_raw IS NULL AND attempts < ?",
        (MAX_ATTEMPTS,),
    ).fetchall()
    log.info("Stufe 4b — Impressum: %s Leads", len(rows))

    def work(row: sqlite3.Row) -> None:
        domain = T.host_of(row["website_final"])
        if not domain:
            db.update(conn, "anreicherung", row["id"],
                      {"impressum_raw": "{}", "launch_campaign": 0, "stage": "impressum_leer"})
            return
        try:
            out = skael.imprint_extractor(domain)
        except ApiError as exc:
            db.note_failure(conn, "anreicherung", row["id"], str(exc))
            return

        gf_list = out.get("geschaeftsfuehrer") or []
        kontaktperson = gf_list[0] if gf_list else ""
        clean = T.kontaktperson_sauber(kontaktperson)
        email_imp = T.email_impressum(out.get("email"))

        db.update(conn, "anreicherung", row["id"], {
            "impressum_raw": json.dumps(out, ensure_ascii=False),
            "firmenname_impressum": out.get("firmenname") or "",
            "firmenname_final": (out.get("firmenname") or "") or (row["firmenname"] or ""),
            "adresse_impressum": out.get("adresse") or "",
            "telefon_impressum": out.get("telefon") or "",
            "email_impressum": email_imp,
            "email_domain": T.email_domain(email_imp, row["website_final"] or ""),
            "kontaktperson": kontaktperson,
            "kontaktperson_sauber": clean,
            "first_name": T.first_name(clean),
            "last_name": T.last_name(clean),
            "launch_campaign": 1 if T.launch_campaign(clean, email_imp) else 0,
            "stage": "impressum_done",
            "error": None,
        })

    _run_parallel(list(rows), work, "Stufe 4b")


def stufe4c_emails(conn: sqlite3.Connection, skael: SkaelClient, findymail: FindymailClient) -> None:
    """Clay ANREICHERUNG: Mailfinder → Findymail-Fallback → verify_email → Info@-Fallback."""
    rows = conn.execute(
        "SELECT * FROM anreicherung WHERE launch_campaign=1 AND email_final IS NULL AND attempts < ?",
        (MAX_ATTEMPTS,),
    ).fetchall()
    log.info("Stufe 4c — E-Mail-Wasserfall: %s Leads", len(rows))

    def work(row: sqlite3.Row) -> None:
        clean = row["kontaktperson_sauber"] or ""
        website_final = row["website_final"] or ""
        impressum_ran = bool(row["impressum_raw"])
        hard_error: str | None = None

        skael_email = findy_email = ""
        mailfinder_raw = findymail_raw = None

        # a) Skael Mailfinder — Clay-Run: Launch Campaign && Kontaktperson [Sauber]
        if clean:
            try:
                out = skael.find_email_person(website_final, clean)
                mailfinder_raw = json.dumps(out, ensure_ascii=False)
                skael_email = out.get("email") or ""
            except ApiError as exc:
                hard_error = f"Mailfinder: {exc}"

        # b) Findymail-Fallback — nur wenn Skael nichts geliefert hat
        #    Nicht nach einem Mailfinder-Fehler: der Lead wird ohnehin wiederholt.
        #    Leeres Guthaben, pausiertes Abo, falscher Schlüssel: Lead bleibt offen.
        if clean and not skael_email and not hard_error and CONFIG.use_findymail and findymail.api_key:
            try:
                out = findymail.find_work_email(clean, website_final)
                findymail_raw = json.dumps(out.get("raw"), ensure_ascii=False)
                findy_email = out.get("email") or ""
            except ApiError as exc:
                hard_error = f"Findymail: {exc}"

        # c) GF-Mail validieren
        verify_gf = None
        candidate = skael_email or findy_email
        if candidate:
            try:
                verify_gf = skael.verify_email(candidate)
            except ApiError as exc:
                hard_error = f"Verify GF: {exc}"

        if hard_error:
            # Transienter Fehler → Zeile bleibt offen und wird erneut versucht
            db.note_failure(conn, "anreicherung", row["id"], hard_error)
            return

        email_gf = T.email_from_verify(verify_gf)
        status_gf = T.email_status(verify_gf, kein_gf=not clean, impressum_ran=impressum_ran)

        # d) Info@-Fallback
        verify_info = None
        email_impressum = row["email_impressum"] or ""
        if not email_gf and email_impressum:
            try:
                verify_info = skael.verify_email(email_impressum)
            except ApiError as exc:
                db.note_failure(conn, "anreicherung", row["id"], f"Verify Info@: {exc}")
                return

        email_info = T.email_from_verify(verify_info)
        status_info = T.email_status(verify_info)

        db.update(conn, "anreicherung", row["id"], {
            "mailfinder_raw": mailfinder_raw,
            "findymail_raw": findymail_raw,
            "verify_gf_raw": json.dumps(verify_gf, ensure_ascii=False) if verify_gf else None,
            "verify_info_raw": json.dumps(verify_info, ensure_ascii=False) if verify_info else None,
            "email_gf": email_gf,
            "email_gf_status": status_gf,
            "email_source_gf": T.email_source_gf(email_gf, skael_email, findy_email),
            "email_info": email_info,
            "email_info_status": status_info,
            "email_final": T.email_final(email_gf, email_info),
            "email_final_type": T.email_final_type(email_gf, email_info, status_gf, status_info),
            "email_final_status": T.email_final_status(email_gf, email_info, status_gf, status_info),
            "stage": "email_done",
            "error": None,
        })

    _run_parallel(list(rows), work, "Stufe 4c")

    # Leads ohne Kontaktperson und ohne Impressum-Mail: Clay setzt "Kein GF"
    with db.write(conn):
        conn.execute("""
            UPDATE anreicherung
               SET email_gf = '', email_gf_status = 'Kein GF', email_info = '',
                   email_info_status = 'Not Run', email_final = '',
                   email_final_type = 'Not Run', email_final_status = 'Not Run'
             WHERE COALESCE(launch_campaign, 0) = 0
               AND impressum_raw IS NOT NULL
               AND email_final IS NULL
        """)


def stufe4d_anrede(conn: sqlite3.Connection, llm: LLM) -> None:
    """Clay ANREICHERUNG.`Anrede [Prompt] (2)` + alle Ansprache-Varianten."""
    rows = conn.execute(
        "SELECT id, first_name, last_name, email_final FROM anreicherung "
        "WHERE first_name <> '' AND email_final <> '' AND anrede IS NULL AND attempts < ?",
        (MAX_ATTEMPTS,),
    ).fetchall()
    log.info("Stufe 4d — Anrede: %s Leads", len(rows))

    def work(row: sqlite3.Row) -> None:
        result = llm.anrede(row["first_name"])
        if result is None:
            db.note_failure(conn, "anreicherung", row["id"], "Anrede-KI fehlgeschlagen")
            return
        anrede = result.get("anrede") or ""
        texts = T.ansprachen(anrede or None, row["first_name"] or "", row["last_name"] or "",
                             row["email_final"] or "")
        db.update(conn, "anreicherung", row["id"], {
            "anrede": anrede,
            "anrede_confidence": result.get("confidence"),
            "formal": T.formal_prefix(anrede),
            **texts,
            "stage": "anrede_done",
            "error": None,
        })

    _run_parallel(list(rows), work, "Stufe 4d", max_workers=min(CONFIG.max_concurrency, 4))

    # Leads ohne Vornamen bekommen die neutralen Ansprachen (Clay: Anrede leer)
    for row in conn.execute(
        "SELECT id, first_name, last_name, email_final FROM anreicherung "
        "WHERE email_final <> '' AND anrede IS NULL"
    ).fetchall():
        texts = T.ansprachen(None, row["first_name"] or "", row["last_name"] or "",
                             row["email_final"] or "")
        db.update(conn, "anreicherung", row["id"], {"anrede": "", "formal": "", **texts})


def stufe4e_personalisierung(conn: sqlite3.Connection, skael: SkaelClient, llm: LLM) -> None:
    """Clay ANREICHERUNG.`SKAEL WEBSCRAPER` → `Bodytext Website` → `Personalisierung AI`.

    Je Strecke ein anderer Text:
      gmaps  Einordnung + Beobachtungssatz (personalisierung.txt der Kampagne)
      rc     Jobtitel normalisieren + „ich habe gesehen, dass Sie gerade jemanden als … suchen“
      nk     Satz zur Website (personalisierung_website.txt) für passende Firmen ohne Stelle
    """
    if not CONFIG.do_personalisierung:
        log.info("Stufe 4e übersprungen (DO_PERSONALISIERUNG=false)")
        return
    rows = conn.execute(
        "SELECT id, website_final, webscraper_raw, strecke, job_title, job_description, "
        "job_title_norm FROM anreicherung "
        "WHERE email_final <> '' AND website_final <> '' AND personalisierung IS NULL "
        "AND attempts < ?",
        (MAX_ATTEMPTS,),
    ).fetchall()
    log.info("Stufe 4e — Personalisierung: %s Leads", len(rows))
    opener_prompt = einstellung(conn, "opener_prompt", "personalisierung_stellenanzeige.txt")

    def work(row: sqlite3.Row) -> None:
        strecke = row["strecke"] or "gmaps"
        if strecke == "rc":
            work_stelle(row)
        elif strecke == "nk":
            work_website(row)
        else:
            work_gmaps(row)

    def work_stelle(row: sqlite3.Row) -> None:
        """Clay RC: `Normalisierter Jobtitel` → `Personalisierung AI` → `Personalisierung`."""
        norm = row["job_title_norm"]
        if norm is None:
            if not row["job_title"]:
                db.update(conn, "anreicherung", row["id"], {
                    "job_title_norm": "", "personalisierung": "", "stage": "personalisierung_leer"})
                return
            norm = llm.jobtitel_normalisieren(row["job_title"])
            if norm is None:
                db.note_failure(conn, "anreicherung", row["id"], "Jobtitel-KI fehlgeschlagen")
                return
            db.update(conn, "anreicherung", row["id"], {"job_title_norm": norm})
        if not norm:
            # Clay-Run-Bedingung: normalisierterTitel muss gefüllt sein
            db.update(conn, "anreicherung", row["id"], {"personalisierung": "", "stage": "personalisierung_leer"})
            return
        text = llm.stellen_opener(norm, row["job_description"] or "", prompt_datei=opener_prompt,
                                  original=row["job_title"] or "")
        if text is None:
            db.note_failure(conn, "anreicherung", row["id"], "Stellen-Opener fehlgeschlagen")
            return
        db.update(conn, "anreicherung", row["id"], {
            "personalisierung": text, "stage": "personalisierung_done", "error": None})

    def work_website(row: sqlite3.Row) -> None:
        """Clay NK: `SKAEL WEBSCRAPER` → `Bodytext Website` → Satz zur Website."""
        if row["webscraper_raw"]:
            out = json.loads(row["webscraper_raw"])
        else:
            try:
                out = skael.web_scraper(row["website_final"])
            except ApiError as exc:
                db.note_failure(conn, "anreicherung", row["id"], f"Webscraper: {exc}")
                return
            db.update(conn, "anreicherung", row["id"], {
                "webscraper_raw": json.dumps(out, ensure_ascii=False),
                "bodytext": T.bodytext(out), "site_links": T.site_links(out)})
        body = T.bodytext(out)
        if not body:
            db.update(conn, "anreicherung", row["id"], {"personalisierung": "", "stage": "personalisierung_leer"})
            return
        text = llm.personalisierung_website(body)
        if text is None:
            db.note_failure(conn, "anreicherung", row["id"], "Personalisierungs-KI fehlgeschlagen")
            return
        db.update(conn, "anreicherung", row["id"], {
            "bodytext": body, "personalisierung": text, "stage": "personalisierung_done", "error": None})

    def work_gmaps(row: sqlite3.Row) -> None:
        # Der Website-Abruf kostet Credits, die KI-Schritte danach koennen
        # scheitern (Rate-Limit). Deshalb: bereits geholte Daten wiederverwenden
        # statt erneut zu bezahlen, und neu geholte SOFORT speichern — vor den
        # KI-Schritten. Ohne das kostet jeder Wiederholungslauf den Abruf erneut.
        if row["webscraper_raw"]:
            out = json.loads(row["webscraper_raw"])
        else:
            try:
                out = skael.web_scraper(row["website_final"])
            except ApiError as exc:
                db.note_failure(conn, "anreicherung", row["id"], f"Webscraper: {exc}")
                return
            db.update(conn, "anreicherung", row["id"], {
                "webscraper_raw": json.dumps(out, ensure_ascii=False),
                "bodytext": T.bodytext(out),
                "site_links": T.site_links(out),
            })

        body = T.bodytext(out)
        meta = json.dumps(out, ensure_ascii=False)
        if not body:
            # Seite lieferte keinen Text — kein Fehler, aber auch keine Personalisierung
            db.update(conn, "anreicherung", row["id"], {
                "webscraper_raw": meta, "bodytext": "", "personalisierung": "",
                "site_links": T.site_links(out), "stage": "personalisierung_leer",
            })
            return

        links = T.site_links(out)
        einordnung = llm.pain_kategorie(body, links)
        if einordnung is None:
            db.note_failure(conn, "anreicherung", row["id"], "Einordnung fehlgeschlagen")
            return
        # Jeder Lead in dieser Tabelle hat das ICP-Profil bestanden. "unklar" heisst
        # hier nur, dass die Startseite wenig hergibt — fachlich ist das der
        # Normalfall der Kampagne (KATEGORIE_NORMALFALL), kein unbekannter.
        if einordnung["kategorie"] in ("unklar", "") and CONFIG.kategorie_normalfall:
            einordnung["kategorie"] = CONFIG.kategorie_normalfall
            if not einordnung["beleg"] or einordnung["beleg"] == "kein Beleg":
                einordnung["beleg"] = "Zielgruppe über Prüfprofil belegt, auf der Startseite nicht ausgeführt"

        text = llm.personalisierung(body, links, einordnung["kategorie"])
        if text is None:
            db.note_failure(conn, "anreicherung", row["id"], "Personalisierungs-KI fehlgeschlagen")
            return
        db.update(conn, "anreicherung", row["id"], {
            "webscraper_raw": meta,
            "bodytext": body,
            "site_links": links,
            "personalisierung": text,
            "pain_category": einordnung["kategorie"],
            "pain_beleg": einordnung["beleg"],
            "partnernetz": 1 if einordnung["netz"] else 0,
            "stage": "personalisierung_done",
            "error": None,
        })

    _run_parallel(list(rows), work, "Stufe 4e")


def stufe4f_videotitel(conn: sqlite3.Connection, llm: LLM) -> None:
    """Clay ANREICHERUNG.`Video Title Input` → `Cleaned Video Title` → `Video Title`."""
    if not CONFIG.do_video_title:
        log.info("Stufe 4f übersprungen (DO_VIDEO_TITLE=false)")
        return
    rows = conn.execute(
        "SELECT id, first_name, last_name, firmenname, firmenname_final FROM anreicherung "
        "WHERE email_final <> '' AND video_title IS NULL AND COALESCE(strecke,'gmaps')='gmaps' "
        "AND attempts < ?",
        (MAX_ATTEMPTS,),
    ).fetchall()
    log.info("Stufe 4f — Videotitel: %s Leads (Recruiting und Stellensuche ohne Videotitel)", len(rows))

    def work(row: sqlite3.Row) -> None:
        firmenname = row["firmenname"] or row["firmenname_final"] or ""
        vti = T.video_title_input(row["first_name"] or "", row["last_name"] or "", firmenname)
        result = llm.video_title(vti)
        if result is None:
            db.note_failure(conn, "anreicherung", row["id"], "Videotitel-KI fehlgeschlagen")
            return
        db.update(conn, "anreicherung", row["id"], {
            "video_title_input": vti,
            "video_title": result.get("cleanedText", "") or "",
            "video_company_name": result.get("cleanedCompanyName", "") or "",
            "stage": "video_done",
            "error": None,
        })

    _run_parallel(list(rows), work, "Stufe 4f", max_workers=min(CONFIG.max_concurrency, 4))


def stufe4g_linkedin(conn: sqlite3.Connection, skael: SkaelClient) -> None:
    """Clay ANREICHERUNG.`SKAEL Linked In Search` — im Workbook deaktiviert (`&& false`)."""
    if not CONFIG.do_linkedin:
        log.info("Stufe 4g übersprungen (DO_LINKEDIN=false — wie im Clay-Original)")
        return
    from .llm import prompt_pfad
    from .llm import render

    template = prompt_pfad("linkedin_research_body.json.tpl").read_text(encoding="utf-8")
    rows = conn.execute(
        "SELECT id, kontaktperson_sauber, firmenname_final, firmenname FROM anreicherung "
        "WHERE email_final <> '' AND kontaktperson_sauber <> '' AND linkedin_url IS NULL "
        "AND attempts < ?",
        (MAX_ATTEMPTS,),
    ).fetchall()
    log.info("Stufe 4g — LinkedIn: %s Leads", len(rows))

    def work(row: sqlite3.Row) -> None:
        firma = row["firmenname_final"] or row["firmenname"] or ""
        body = json.loads(render(template, {
            "Kontaktperson [Sauber]": row["kontaktperson_sauber"],
            "Firmenname [Final]": firma,
        }))
        try:
            out = skael.ai_research_agent(
                body["system_prompt"], body["user_prompt"], body["schema"],
                max_steps=body.get("max_steps", 10),
                model=body.get("model", "google/gemini-2.5-flash"),
            )
        except ApiError as exc:
            db.note_failure(conn, "anreicherung", row["id"], f"LinkedIn: {exc}")
            return
        url = out.get("linkedin_url") or ""
        if url == "No LinkedIn profile found":
            url = ""
        db.update(conn, "anreicherung", row["id"], {
            "linkedin_url": url,
            "linkedin_confidence": out.get("confidence"),
            "error": None,
        })

    _run_parallel(list(rows), work, "Stufe 4g", max_workers=2)


def stufe4h_ready(conn: sqlite3.Connection) -> None:
    """Clay ANREICHERUNG.`Ready to Send`.

    Personalisierung und Videotitel zählen nur, wenn die jeweilige Stufe eingeschaltet ist.
    Sonst bliebe bei DO_VIDEO_TITLE=false bzw. DO_PERSONALISIERUNG=false jeder Lead
    „nicht versandfertig“ und der Export wäre leer.
    """
    bedingungen = ["COALESCE(email_final,'') <> ''"]
    if CONFIG.do_personalisierung:
        # Google Maps: leere Personalisierung ist gewollt (kein konkretes Detail) — der Export setzt
        # dann den Standardabsatz ein. Versandfertig heisst dort: Stufe 4e ist gelaufen.
        # Recruiting/Stellensuche (rc, nk): der Satz zur Stelle bzw. Website ist der Aufhänger und
        # muss da sein, bei rc dazu der normalisierte Jobtitel (Clay RC: Email && Job Titel && Personalisierung).
        bedingungen.append("(CASE WHEN COALESCE(strecke,'gmaps')='gmaps' THEN personalisierung IS NOT NULL "
                           "ELSE COALESCE(personalisierung,'') <> '' END)")
        bedingungen.append("(COALESCE(strecke,'gmaps') <> 'rc' OR COALESCE(job_title_norm,'') <> '')")
    if CONFIG.do_video_title:
        bedingungen.append("(COALESCE(strecke,'gmaps') <> 'gmaps' OR COALESCE(video_title,'') <> '')")
    with db.write(conn):
        conn.execute(
            "UPDATE anreicherung SET ready_to_send = CASE WHEN "
            + " AND ".join(bedingungen) + " THEN 1 ELSE 0 END"
        )
    ready = conn.execute("SELECT COUNT(*) FROM anreicherung WHERE ready_to_send=1").fetchone()[0]
    log.info("Ready to Send: %s Leads", ready)
