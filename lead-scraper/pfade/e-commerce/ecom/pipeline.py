"""Die Prozessstufen — Portierung des Clay-Workbooks „Vorlage | ECOM 2.0“.

Stufe 1 = Clay-Tabelle Import:        Shop-Liste prüfen (aktiver Onlineshop? passt zum Shop-Profil?
                                      echter Traffic?)
Stufe 2 = Clay-Tabelle ANREICHERUNG:  Impressum, E-Mail, Anrede, Personalisierung, Videotitel

Shop-Profil, Personalisierungs-Prompt und Mailtext sind Anforderungen des Auftrags (Tabelle
`meta`). `fehlende_anforderungen` prüft vor jedem Lauf, ob sie geklärt sind.

Grundregel für die Fehlerbehandlung (wie im Google-Maps-Pfad): Bei einem API-Fehler
wird **nicht** in das Feld geschrieben, das die Stufe als „erledigt“-Marker abfragt.
Stattdessen zählt `attempts` hoch und `error` hält die Meldung. Die Zeile wird beim
nächsten Lauf erneut versucht – bis `MAX_ATTEMPTS` erreicht ist. `fehler-zuruecksetzen`
gibt liegen gebliebenen Zeilen neue Versuche.

Ausnahme (nur E-Commerce): Lehnt ein Dienst den Zugang ab (Schlüssel falsch, Guthaben leer,
`clients.ZugangGesperrt`), bricht die Stufe sofort ab und zählt keinen Fehlversuch – sonst
blieben nach drei Läufen alle Zeilen liegen, obwohl nur der Schlüssel falsch war.
"""
from __future__ import annotations

import json
import logging
import sqlite3
import threading
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable

from . import db, transforms as T
from .clients import ApiError, FindymailClient, SkaelClient, ZugangGesperrt, pruefe_zugang
from .config import CONFIG
from .llm import LLM

log = logging.getLogger(__name__)

MAX_ATTEMPTS = 3

BUILDER_SHOPPROFIL = "prompts/shopprofil_builder.md"
BUILDER_PERSONALISIERUNG = "prompts/personalisierung_builder.md"


def fehlende_anforderungen(conn: sqlite3.Connection, stufen) -> list[str]:
    """Was vor diesen Stufen noch geklärt werden muss — leer = Lauf darf starten.

    Wird vor jedem bezahlten Aufruf geprüft (Gesprächsleitfaden: erst fragen, bis alles da ist).
    """
    fehlt: list[str] = []
    stufen = set(stufen)
    # 1d und 1e hängen am Profil-Ergebnis aus 1c: ohne Entscheidung bekämen alle aktiven Shops Traffic
    if stufen & {"1c", "1d", "1e"} and db.get_meta(conn, db.META_SHOPPROFIL) is None:
        fehlt.append(f"Shop-Profil fehlt (welche Shops passen zum Kunden?) — Builder: {BUILDER_SHOPPROFIL}, "
                     "dann `python3 -m ecom set-prompt shopprofil <datei>`. Bewusst ohne Profil "
                     "(jeder aktive Shop zählt): `python3 -m ecom set-prompt shopprofil --ohne`")
    if "2e" in stufen and CONFIG.do_personalisierung:
        if not (db.get_meta(conn, db.META_PERSONALISIERUNG) or "").strip():
            fehlt.append(f"Personalisierung fehlt (Anleitung für den persönlichen Satz) — Builder: "
                         f"{BUILDER_PERSONALISIERUNG}, dann `python3 -m ecom set-prompt personalisierung <datei>`")
        if not (db.get_meta(conn, db.META_MAILTEXT) or "").strip():
            fehlt.append(f"Mailtext fehlt — Builder: {BUILDER_PERSONALISIERUNG}, Runde 2, "
                         "dann `python3 -m ecom set-mailtext <datei>`")
    return fehlt


def _profil_aktiv(conn: sqlite3.Connection) -> bool:
    return bool((db.get_meta(conn, db.META_SHOPPROFIL) or "").strip())


# Shops, deren Profil-Ergebnis noch etwas bewirkt: nicht übergeben, oder übergeben, aber der Lead
# ist noch nicht exportiert (z. B. aus dem Testlauf). Spalten von `shops`, ohne Tabellen-Präfix.
SHOP_NOCH_OFFEN = ("(COALESCE(uebergeben,0)=0 OR id IN "
                   "(SELECT shop_id FROM anreicherung WHERE COALESCE(bereits_exportiert,0)=0))")


def profil_ok_sql(conn: sqlite3.Connection) -> str:
    """Mit Shop-Profil zählen nur geprüfte, passende Shops; ohne Profil jeder Shop, den kein Profil ablehnt.

    NULL-sicher, damit `NOT (…)` auch ungeprüfte Shops trifft (Export, Liste 3).
    """
    return "COALESCE(passt_profil,0)=1" if _profil_aktiv(conn) else "COALESCE(passt_profil,1)=1"


# Bilanz je Stufe: (Bezeichnung, Zeilen, Fehlversuche, häufigster Grund). `run` leert die Liste vor
# dem Lauf und meldet danach Stufen, in denen jede Zeile scheiterte.
BILANZ: list[tuple[str, int, int, str]] = []


def _fehlschlag(conn: sqlite3.Connection, table: str, row_id: int, message: str) -> str:
    """Fehlversuch verbuchen (`db.note_failure`) und die Meldung für die Bilanz zurückgeben."""
    db.note_failure(conn, table, row_id, message)
    return message


def _run_parallel(items: list, worker: Callable, desc: str, max_workers: int | None = None) -> None:
    """Führt worker(item) parallel aus und protokolliert den Fortschritt.

    Ein Worker gibt nach einem verbuchten Fehlversuch dessen Meldung zurück (`_fehlschlag`), sonst None.
    `ZugangGesperrt` stoppt die Stufe: Weitere Zeilen werden nicht mehr angefangen, der Fehler fliegt weiter.
    """
    if not items:
        log.info("%s: nichts zu tun", desc)
        return
    workers = max_workers or CONFIG.max_concurrency
    stop = threading.Event()
    gesperrt: ZugangGesperrt | None = None
    gruende: Counter[str] = Counter()
    done = failed = 0

    def ausfuehren(item):
        return None if stop.is_set() else worker(item)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(ausfuehren, item) for item in items]
        for future in as_completed(futures):
            try:
                ergebnis = future.result()
            except ZugangGesperrt as exc:
                stop.set()
                gesperrt = gesperrt or exc
                continue
            except Exception as exc:  # noqa: BLE001
                ergebnis = f"{type(exc).__name__}: {exc}"
                log.error("%s: %s", desc, exc)
            if isinstance(ergebnis, str):
                failed += 1
                gruende[ergebnis[:120]] += 1
            done += 1
            if not stop.is_set() and (done % 25 == 0 or done == len(items)):
                log.info("%s: %s/%s (%s Fehler)", desc, done, len(items), failed)
    if gesperrt is not None:
        raise gesperrt
    grund = gruende.most_common(1)[0][0] if gruende else ""
    BILANZ.append((desc, len(items), failed, grund))
    if failed:
        log.warning("%s: %s von %s Zeilen fehlgeschlagen, häufigster Grund: %s", desc, failed, len(items), grund)


def _limit(sql: str, params: list, limit: int | None) -> tuple[str, list]:
    if limit:
        return sql + " LIMIT ?", [*params, int(limit)]
    return sql, params


# ====================================================================== 1  (Clay Import)
def stufe1a_domain(conn: sqlite3.Connection, llm: LLM, limit: int | None = None) -> None:
    """Clay Import.`Company Domain` (Run-If: !website && Firmenname) + `website [Final]`."""
    sql, params = _limit(
        "SELECT id, firmenname, website FROM shops WHERE website_final IS NULL AND attempts < ? ORDER BY id",
        [MAX_ATTEMPTS], limit)
    rows = conn.execute(sql, params).fetchall()
    log.info("Stufe 1a — website [Final]: %s Shops", len(rows))

    def work(row: sqlite3.Row) -> str | None:
        response = None
        if not (row["website"] or "").strip() and (row["firmenname"] or "").strip():
            response = llm.company_domain(row["firmenname"])
            if response is None:
                return _fehlschlag(conn, "shops", row["id"], "Company Domain fehlgeschlagen")
        db.update(conn, "shops", row["id"], {
            "company_domain": response,
            "website_final": T.website_final(row["website"], response),
            "error": None,
        })

    _run_parallel(list(rows), work, "Stufe 1a", max_workers=min(CONFIG.max_concurrency, 4))


def stufe1b_webscraper(conn: sqlite3.Connection, skael: SkaelClient, limit: int | None = None) -> None:
    """Clay Import.`SKAEL WEBSCRAPER` (Run-If: !!website [Final])."""
    sql, params = _limit(
        "SELECT id, website_final FROM shops WHERE website_final <> '' AND webscraper_raw IS NULL "
        "AND attempts < ? ORDER BY id", [MAX_ATTEMPTS], limit)
    rows = conn.execute(sql, params).fetchall()
    log.info("Stufe 1b — Website abrufen: %s Shops", len(rows))

    def work(row: sqlite3.Row) -> str | None:
        try:
            out = skael.web_scraper(row["website_final"])
        except ApiError as exc:
            pruefe_zugang(exc, "Skael")
            return _fehlschlag(conn, "shops", row["id"], f"Webscraper: {exc}")
        db.update(conn, "shops", row["id"], {
            "webscraper_raw": db.dumps(out),
            "bodytext": (out or {}).get("body_text") or "",
            "error": None,
        })

    _run_parallel(list(rows), work, "Stufe 1b")


def stufe1c_onlineshop(conn: sqlite3.Connection, llm: LLM, limit: int | None = None) -> None:
    """Clay Import.`ICP ONLINE SHOP` (Run-If: !!website [Final] && !!body_text), danach das Shop-Profil."""
    sql, params = _limit(
        "SELECT id, website_final, bodytext FROM shops WHERE website_final <> '' AND bodytext <> '' "
        "AND icp_raw IS NULL AND attempts < ? ORDER BY id", [MAX_ATTEMPTS], limit)
    rows = conn.execute(sql, params).fetchall()
    log.info("Stufe 1c — aktiver Onlineshop?: %s Shops", len(rows))

    def work(row: sqlite3.Row) -> str | None:
        result = llm.icp_online_shop(row["bodytext"][: CONFIG.icp_bodytext_max_chars], row["website_final"])
        if result is None:
            return _fehlschlag(conn, "shops", row["id"], "ICP ONLINE SHOP fehlgeschlagen")
        aktiv = result.get("isActiveOnlineShop")
        db.update(conn, "shops", row["id"], {
            "icp_raw": db.dumps(result),
            "is_active_shop": 1 if aktiv is True else 0,
            "error": None,
        })

    _run_parallel(list(rows), work, "Stufe 1c", max_workers=min(CONFIG.max_concurrency, 4))
    _stufe1c_shopprofil(conn, llm, limit)


def _stufe1c_shopprofil(conn: sqlite3.Connection, llm: LLM, limit: int | None = None) -> None:
    """Shop-Profil des Kunden (nicht in Clay): passt der aktive Shop zum Wunschkunden?

    Geprüft werden nicht übergebene Shops und übergebene, deren Lead noch nicht exportiert ist
    (nach `set-prompt shopprofil` z. B. die Shops aus dem Testlauf). Lehnt das Profil einen
    übergebenen Shop ab, wird sein Lead in Stufe 2g nicht „Ready to Send“ und steht in Liste 3.
    """
    vorlage = db.get_meta(conn, db.META_SHOPPROFIL) or ""
    if not vorlage.strip():
        log.info("Stufe 1c — Shop-Profil: keins hinterlegt, jeder aktive Shop zählt")
        return
    sql, params = _limit(
        "SELECT id, website_final, bodytext FROM shops WHERE is_active_shop=1 AND profil_raw IS NULL "
        f"AND {SHOP_NOCH_OFFEN} AND attempts < ? ORDER BY id", [MAX_ATTEMPTS], limit)
    rows = conn.execute(sql, params).fetchall()
    log.info("Stufe 1c — passt zum Shop-Profil?: %s Shops", len(rows))

    def work(row: sqlite3.Row) -> str | None:
        result = llm.shopprofil((row["bodytext"] or "")[: CONFIG.icp_bodytext_max_chars],
                                row["website_final"] or "", vorlage)
        if result is None or not isinstance(result.get("is_icp"), bool):
            return _fehlschlag(conn, "shops", row["id"], "Shop-Profil-Prüfung fehlgeschlagen")
        confidence = result.get("confidence")
        db.update(conn, "shops", row["id"], {
            "profil_raw": db.dumps(result),
            "passt_profil": 1 if result["is_icp"] is True else 0,
            "profil_confidence": confidence if isinstance(confidence, (int, float)) else None,
            "profil_grund": result.get("reason") or "",
            "error": None,
        })

    _run_parallel(list(rows), work, "Stufe 1c Shop-Profil", max_workers=min(CONFIG.max_concurrency, 4))


def stufe1d_webtraffic(conn: sqlite3.Connection, skael: SkaelClient, limit: int | None = None) -> None:
    """Clay Import.`SKAEL WEBTRAFFIC` (Run-If: !!website [Final] && isActiveOnlineShop).

    Zusätzlich (nicht in Clay): nur Shops, die zum Shop-Profil passen – abgelehnte kosten nichts.
    """
    sql, params = _limit(
        "SELECT id, website_final FROM shops WHERE website_final <> '' AND is_active_shop=1 "
        f"AND {profil_ok_sql(conn)} AND webtraffic_raw IS NULL AND attempts < ? ORDER BY id",
        [MAX_ATTEMPTS], limit)
    rows = conn.execute(sql, params).fetchall()
    log.info("Stufe 1d — Traffic abfragen: %s Shops", len(rows))

    def work(row: sqlite3.Row) -> str | None:
        try:
            out = skael.webtraffic(row["website_final"])
        except ApiError as exc:
            pruefe_zugang(exc, "Skael")
            return _fehlschlag(conn, "shops", row["id"], f"Webtraffic: {exc}")
        db.update(conn, "shops", row["id"], {"webtraffic_raw": db.dumps(out or {}), "error": None})

    _run_parallel(list(rows), work, "Stufe 1d")


def stufe1e_uebergabe(conn: sqlite3.Connection) -> None:
    """Clay Import.`AVR TRAFFIC`, `H T 3 MO`, `SEND` und `Send table data`.

    Übergeben wird nur, wenn SEND wahr ist. Im Workbook hat `Send table data` keine
    eigene Laufbedingung; vom Betreiber bestätigt, dass SEND der Filter ist (docs/05_ABWEICHUNGEN.md).
    Zusätzlich muss der Shop zum Shop-Profil passen; `send` bleibt die reine Clay-Formel.
    """
    profil_aktiv = _profil_aktiv(conn)
    rows = conn.execute("SELECT * FROM shops").fetchall()
    neu = abgelehnt = 0
    for row in rows:
        traffic = json.loads(row["webtraffic_raw"]) if row["webtraffic_raw"] else None
        avr = T.avr_traffic(traffic)
        maximum = T.max_traffic_3mo(traffic)
        senden = T.send(avr, maximum)
        db.update(conn, "shops", row["id"], {"avr_traffic": avr, "max_traffic_3mo": maximum,
                                             "send": 1 if senden else 0})
        profil_ok = row["passt_profil"] == 1 if profil_aktiv else row["passt_profil"] != 0
        if senden and not profil_ok and not row["uebergeben"]:
            abgelehnt += 1
        if senden and profil_ok and not row["uebergeben"]:
            # Clay rowData: {"Firmenname": {{Firmenname}}, "website [Final]": {{website [Final]}}}
            if db.insert_ignore(conn, "anreicherung", {
                "shop_id": row["id"],
                "firmenname": row["firmenname"] or "",
                "website": row["website_final"] or "",
                "avr_traffic": avr,
                "max_traffic_3mo": maximum,
            }):
                neu += 1
            db.update(conn, "shops", row["id"], {"uebergeben": 1})
    log.info("Stufe 1e — Übergabe an Anreicherung: %s neue Shops", neu)
    if abgelehnt:
        log.info("Stufe 1e — %s Shops mit Traffic nicht übergeben (Shop-Profil passt nicht oder "
                 "Prüfung ausstehend)", abgelehnt)


# ====================================================================== 2  (Clay ANREICHERUNG)
def stufe2a_website_final(conn: sqlite3.Connection, llm: LLM) -> None:
    """Clay ANREICHERUNG.`Company Domain` (Run-If: !website) + `website [Final]`."""
    rows = conn.execute(
        "SELECT id, website, firmenname, company_domain FROM anreicherung "
        "WHERE website_final IS NULL AND attempts < ?", (MAX_ATTEMPTS,)).fetchall()
    log.info("Stufe 2a — website [Final]: %s Leads", len(rows))

    def work(row: sqlite3.Row) -> str | None:
        response = row["company_domain"]
        if not row["website"] and response is None:
            response = llm.company_domain(row["firmenname"] or "")
            if response is None:
                return _fehlschlag(conn, "anreicherung", row["id"], "Company Domain fehlgeschlagen")
        db.update(conn, "anreicherung", row["id"], {
            "company_domain": response or "",
            "website_final": T.website_final(row["website"], response),
            "stage": "website_done",
            "error": None,
        })

    _run_parallel(list(rows), work, "Stufe 2a", max_workers=min(CONFIG.max_concurrency, 4))


def stufe2b_impressum(conn: sqlite3.Connection, skael: SkaelClient) -> None:
    """Clay ANREICHERUNG.`SKAEL Impressum` (Run-If: website [Final]) und die abgeleiteten Spalten.

    Danach die Tabellen-Dedupe von Clay: DEDUPE_FIELD_ID = `Email [Domain]`, ältere Zeile bleibt.
    """
    rows = conn.execute(
        "SELECT id, firmenname, website_final FROM anreicherung "
        "WHERE website_final <> '' AND impressum_raw IS NULL AND attempts < ?", (MAX_ATTEMPTS,)).fetchall()
    log.info("Stufe 2b — Impressum: %s Leads", len(rows))

    def work(row: sqlite3.Row) -> str | None:
        domain = T.host_of(row["website_final"])
        if not domain:
            db.update(conn, "anreicherung", row["id"],
                      {"impressum_raw": "{}", "launch_campaign": 0, "stage": "impressum_leer"})
            return
        try:
            out = skael.imprint_extractor(domain)
        except ApiError as exc:
            pruefe_zugang(exc, "Skael")
            return _fehlschlag(conn, "anreicherung", row["id"], f"Impressum: {exc}")

        gf_list = out.get("geschaeftsfuehrer") or []
        kontaktperson = gf_list[0] if gf_list else ""
        clean = T.kontaktperson_sauber(kontaktperson)
        email_imp = T.email_impressum(out.get("email"))
        db.update(conn, "anreicherung", row["id"], {
            "impressum_raw": db.dumps(out),
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

    _run_parallel(list(rows), work, "Stufe 2b")

    # Clay löscht die jüngere Zeile; hier wird sie markiert statt gelöscht (nachvollziehbar).
    with db.write(conn):
        conn.execute("""
            UPDATE anreicherung SET dedupe_status='dropped_duplicate'
            WHERE COALESCE(email_domain,'') <> ''
              AND id NOT IN (SELECT MIN(id) FROM anreicherung
                             WHERE COALESCE(email_domain,'') <> '' GROUP BY lower(email_domain))
        """)
    doppelt = conn.execute(
        "SELECT COUNT(*) FROM anreicherung WHERE dedupe_status='dropped_duplicate'").fetchone()[0]
    if doppelt:
        log.info("Stufe 2b — %s Leads als Duplikat (gleiche E-Mail-Domain) aussortiert", doppelt)


def stufe2c_emails(conn: sqlite3.Connection, skael: SkaelClient, findymail: FindymailClient) -> None:
    """Clay ANREICHERUNG: Skael Mailfinder → Findymail → verify_email (GF) → Info@-Fallback."""
    rows = conn.execute(
        "SELECT * FROM anreicherung WHERE launch_campaign=1 AND dedupe_status='kept' "
        "AND email_final IS NULL AND attempts < ?", (MAX_ATTEMPTS,)).fetchall()
    log.info("Stufe 2c — E-Mail-Wasserfall: %s Leads", len(rows))

    def work(row: sqlite3.Row) -> str | None:
        clean = row["kontaktperson_sauber"] or ""
        website_final = row["website_final"] or ""
        hard_error: str | None = None
        skael_email = findy_email = ""
        mailfinder_raw = findymail_raw = None

        # a) Skael Mailfinder — Run-If: Launch Campaign && Kontaktperson [Sauber]
        if clean:
            try:
                out = skael.find_email_person(website_final, clean)
                mailfinder_raw = db.dumps(out)
                skael_email = out.get("email") or ""
            except ApiError as exc:
                pruefe_zugang(exc, "Skael")
                hard_error = f"Mailfinder: {exc}"

        # b) Find Work Email (Findymail) — Run-If: ... && !Skael Mailfinder.email
        #    Nicht nach einem Mailfinder-Fehler: der Lead wird ohnehin wiederholt.
        if clean and not skael_email and not hard_error and CONFIG.use_findymail and findymail.api_key:
            try:
                out = findymail.find_work_email(clean, website_final)
                findymail_raw = db.dumps(out.get("raw"))
                findy_email = out.get("email") or ""
            except ApiError as exc:
                pruefe_zugang(exc, "Findymail")
                hard_error = f"Findymail: {exc}"

        # c) Skael Validate GF — Run-If: Mailfinder.email || Findymail.email
        verify_gf = None
        candidate = skael_email or findy_email
        if candidate:
            try:
                verify_gf = skael.verify_email(candidate)
            except ApiError as exc:
                pruefe_zugang(exc, "Skael")
                hard_error = f"Verify GF: {exc}"

        if hard_error:
            return _fehlschlag(conn, "anreicherung", row["id"], hard_error)

        email_gf = T.email_from_verify(verify_gf)
        status_gf = T.email_status(verify_gf, kein_gf=not clean, impressum_ran=bool(row["impressum_raw"]))

        # d) Skael Validate Info@ — Run-If: Launch Campaign && !Email [GF] && Email [Impressum]
        verify_info = None
        email_impressum = row["email_impressum"] or ""
        if not email_gf and email_impressum:
            try:
                verify_info = skael.verify_email(email_impressum)
            except ApiError as exc:
                pruefe_zugang(exc, "Skael")
                return _fehlschlag(conn, "anreicherung", row["id"], f"Verify Info@: {exc}")

        email_info = T.email_from_verify(verify_info)
        status_info = T.email_status(verify_info)
        db.update(conn, "anreicherung", row["id"], {
            "mailfinder_raw": mailfinder_raw,
            "findymail_raw": findymail_raw,
            "verify_gf_raw": db.dumps(verify_gf),
            "verify_info_raw": db.dumps(verify_info),
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

    _run_parallel(list(rows), work, "Stufe 2c")

    # Ohne Kontaktperson und ohne Impressum-Mail läuft in Clay keine E-Mail-Spalte
    with db.write(conn):
        conn.execute("""
            UPDATE anreicherung
               SET email_gf = '', email_gf_status = 'Kein GF', email_info = '',
                   email_info_status = 'Not Run', email_final = '',
                   email_final_type = 'Not Run', email_final_status = 'Not Run'
             WHERE COALESCE(launch_campaign, 0) = 0 AND impressum_raw IS NOT NULL
               AND email_final IS NULL
        """)


def stufe2d_anrede(conn: sqlite3.Connection, llm: LLM) -> None:
    """Clay ANREICHERUNG.`Anrede [Prompt] (2)` (Run-If: First Name [GF] && Email [Final]) + Ansprachen."""
    rows = conn.execute(
        "SELECT id, first_name, last_name, email_final FROM anreicherung "
        "WHERE first_name <> '' AND email_final <> '' AND dedupe_status='kept' "
        "AND anrede IS NULL AND attempts < ?", (MAX_ATTEMPTS,)).fetchall()
    log.info("Stufe 2d — Anrede: %s Leads", len(rows))

    def work(row: sqlite3.Row) -> str | None:
        result = llm.anrede(row["first_name"])
        if result is None:
            return _fehlschlag(conn, "anreicherung", row["id"], "Anrede-KI fehlgeschlagen")
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

    _run_parallel(list(rows), work, "Stufe 2d", max_workers=min(CONFIG.max_concurrency, 4))

    # Ohne Vornamen: neutrale Ansprachen (Clay: Anrede leer → „Hallo“, „Guten Tag“ …)
    for row in conn.execute(
        "SELECT id, first_name, last_name, email_final FROM anreicherung "
        "WHERE email_final <> '' AND dedupe_status='kept' AND anrede IS NULL "
        "AND COALESCE(first_name,'') = ''"
    ).fetchall():
        texts = T.ansprachen(None, "", row["last_name"] or "", row["email_final"] or "")
        db.update(conn, "anreicherung", row["id"], {"anrede": "", "formal": "", **texts})


def stufe2e_personalisierung(conn: sqlite3.Connection, skael: SkaelClient, llm: LLM) -> None:
    """Clay ANREICHERUNG.`SKAEL WEBSCRAPER` → `Bodytext Website` → `Personalisierung AI`.

    Run-If: website [Final] && Personalisierung generieren (= Email [Final] vorhanden).
    Der Website-Abruf aus Stufe 1b (gleiche URL) wird wiederverwendet statt neu bezahlt.
    Prompt und Mailtext kommen aus dem Auftrag (`meta`), nicht aus prompts/personalisierung.txt.
    """
    if not CONFIG.do_personalisierung:
        log.info("Stufe 2e übersprungen (DO_PERSONALISIERUNG=false)")
        return
    fehlt = fehlende_anforderungen(conn, {"2e"})
    if fehlt:
        raise SystemExit("Stufe 2e kann nicht laufen:\n  " + "\n  ".join(fehlt))
    vorlage = db.get_meta(conn, db.META_PERSONALISIERUNG)
    mailtext = db.get_meta(conn, db.META_MAILTEXT)
    rows = conn.execute("""
        SELECT a.id, a.website_final, a.webscraper_raw, a.firmenname_final, a.firmenname,
               s.webscraper_raw AS import_raw, s.website_final AS import_website
          FROM anreicherung a JOIN shops s ON s.id = a.shop_id
         WHERE a.email_final <> '' AND a.website_final <> '' AND a.dedupe_status='kept'
           AND a.personalisierung IS NULL AND a.attempts < ?
    """, (MAX_ATTEMPTS,)).fetchall()
    log.info("Stufe 2e — Personalisierung: %s Leads", len(rows))

    def work(row: sqlite3.Row) -> str | None:
        raw = row["webscraper_raw"]
        if not raw and row["import_raw"] and row["import_website"] == row["website_final"]:
            raw = row["import_raw"]
        if raw:
            out = json.loads(raw)
        else:
            try:
                out = skael.web_scraper(row["website_final"])
            except ApiError as exc:
                pruefe_zugang(exc, "Skael")
                return _fehlschlag(conn, "anreicherung", row["id"], f"Webscraper: {exc}")
        body = T.bodytext(out)
        # Abruf sofort sichern, damit ein KI-Fehler danach ihn nicht erneut kostet
        db.update(conn, "anreicherung", row["id"], {"webscraper_raw": db.dumps(out), "bodytext": body})
        if not body:
            db.update(conn, "anreicherung", row["id"],
                      {"personalisierung": "", "stage": "personalisierung_leer"})
            return
        text = llm.personalisierung(body, vorlage, mailtext,
                                    row["firmenname_final"] or row["firmenname"] or "")
        if text is None:
            return _fehlschlag(conn, "anreicherung", row["id"], "Personalisierungs-KI fehlgeschlagen")
        db.update(conn, "anreicherung", row["id"], {
            "personalisierung": text, "stage": "personalisierung_done", "error": None})

    _run_parallel(list(rows), work, "Stufe 2e")


def stufe2f_videotitel(conn: sqlite3.Connection, llm: LLM) -> None:
    """Clay ANREICHERUNG.`Video Title Input` → `Cleaned Video Title` → `Video Title`.

    Run-If: Video Title Input && Personalisierung generieren (= Email [Final] vorhanden).
    """
    if not CONFIG.do_video_title:
        log.info("Stufe 2f übersprungen (DO_VIDEO_TITLE=false)")
        return
    rows = conn.execute(
        "SELECT id, first_name, last_name, firmenname, firmenname_final FROM anreicherung "
        "WHERE email_final <> '' AND dedupe_status='kept' AND video_title IS NULL AND attempts < ?",
        (MAX_ATTEMPTS,)).fetchall()
    log.info("Stufe 2f — Videotitel: %s Leads", len(rows))

    def work(row: sqlite3.Row) -> str | None:
        # Clay nimmt {{Firmenname}} aus der Import-Liste; ist der leer (nur Website importiert),
        # wird der Name aus dem Impressum genommen (docs/05_ABWEICHUNGEN.md)
        firmenname = row["firmenname"] or row["firmenname_final"] or ""
        vti = T.video_title_input(row["first_name"] or "", row["last_name"] or "", firmenname)
        result = llm.video_title(vti)
        if result is None:
            return _fehlschlag(conn, "anreicherung", row["id"], "Videotitel-KI fehlgeschlagen")
        db.update(conn, "anreicherung", row["id"], {
            "video_title_input": vti,
            "video_title": result.get("cleanedText", "") or "",
            "video_company_name": result.get("cleanedCompanyName", "") or "",
            "stage": "video_done",
            "error": None,
        })

    _run_parallel(list(rows), work, "Stufe 2f", max_workers=min(CONFIG.max_concurrency, 4))


def stufe2g_ready(conn: sqlite3.Connection) -> None:
    """Clay ANREICHERUNG.`Ready to Send` (= Filter der Clay-Ansicht „Export final“).

    Personalisierung und Videotitel zählen nur, wenn die jeweilige Stufe eingeschaltet ist.
    Zusätzlich (docs/05_ABWEICHUNGEN.md, Nr. 9 und 14): Die Ansprachen sind berechnet (`anrede`
    nicht NULL – Stufe 2d setzt "" bei neutraler Anrede), sonst begänne die Mail mit einem leeren
    Gruß; und der Shop passt zum Shop-Profil (nach einem geänderten Profil neu geprüft).
    """
    bedingungen = ["COALESCE(email_final,'') <> ''", "dedupe_status='kept'", "anrede IS NOT NULL",
                   f"shop_id IN (SELECT id FROM shops WHERE {profil_ok_sql(conn)})"]
    if CONFIG.do_personalisierung:
        bedingungen.append("COALESCE(personalisierung,'') <> ''")
    if CONFIG.do_video_title:
        bedingungen.append("COALESCE(video_title,'') <> ''")
    with db.write(conn):
        conn.execute("UPDATE anreicherung SET ready_to_send = CASE WHEN "
                     + " AND ".join(bedingungen) + " THEN 1 ELSE 0 END")
    ready = conn.execute("SELECT COUNT(*) FROM anreicherung WHERE ready_to_send=1").fetchone()[0]
    log.info("Ready to Send: %s Leads", ready)
