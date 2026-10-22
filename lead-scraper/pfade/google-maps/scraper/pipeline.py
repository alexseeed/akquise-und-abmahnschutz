"""Die vier Prozessstufen — Portierung der Clay-Tabellen als ausführbare Schritte.

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
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable

from . import db, transforms as T
from .clients import ApiError, FindymailClient, SkaelClient
from .config import CONFIG
from .llm import LLM

log = logging.getLogger(__name__)

MAX_ATTEMPTS = 3


def _run_parallel(items: list, worker: Callable, desc: str, max_workers: int | None = None) -> None:
    """Führt worker(item) parallel aus und protokolliert den Fortschritt."""
    if not items:
        log.info("%s: nichts zu tun", desc)
        return
    workers = max_workers or CONFIG.max_concurrency
    done = failed = 0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(worker, item): item for item in items}
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as exc:  # noqa: BLE001
                failed += 1
                log.error("%s: %s", desc, exc)
            done += 1
            if done % 25 == 0 or done == len(items):
                log.info("%s: %s/%s (%s Fehler)", desc, done, len(items), failed)


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


# ====================================================================== 3
def stufe3a_domains(conn: sqlite3.Connection, llm: LLM) -> None:
    """Clay DATENSÄTZE.`Domain URL` — KI-Domainsuche, wenn Maps keine Website liefert.

    Clay nutzt hier gpt-4o-mini (nicht 4.1-mini wie in ANREICHERUNG.`Company Domain`).
    """
    if not CONFIG.quali_on:
        log.info("Stufe 3a übersprungen (QUALI_ON=false)")
        return
    rows = conn.execute(
        "SELECT id, firmenname FROM datensaetze "
        "WHERE (website IS NULL OR website='') AND domain_url IS NULL "
        "AND firmenname IS NOT NULL AND attempts < ?",
        (MAX_ATTEMPTS,),
    ).fetchall()
    log.info("Stufe 3a — Domainsuche per KI: %s Firmen ohne Website", len(rows))

    def work(row: sqlite3.Row) -> None:
        response = llm.company_domain(row["firmenname"], model=CONFIG.model_default)
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
        conn.execute("UPDATE datensaetze SET dedupe_status='dropped_excluded' WHERE dedupe_key='DEDUPE'")
        conn.execute("UPDATE datensaetze SET dedupe_status='kept' WHERE dedupe_key <> 'DEDUPE'")
        conn.execute("""
            UPDATE datensaetze SET dedupe_status='dropped_duplicate'
            WHERE dedupe_key IS NOT NULL AND dedupe_key <> '' AND dedupe_key <> 'DEDUPE'
              AND id NOT IN (SELECT MIN(id) FROM datensaetze
                             WHERE dedupe_key IS NOT NULL AND dedupe_key <> '' AND dedupe_key <> 'DEDUPE'
                             GROUP BY dedupe_key)
        """)

    kept = conn.execute("SELECT COUNT(*) FROM datensaetze WHERE dedupe_status='kept'").fetchone()[0]
    log.info("Stufe 3b — %s Zeilen bleiben nach Dedupe", kept)


def stufe3c_icp(conn: sqlite3.Connection, skael: SkaelClient, icp_prompt: str) -> None:
    """Clay DATENSÄTZE.`ICP Check` — Website gegen den ICP-Prompt prüfen."""
    if not CONFIG.quali_on:
        log.info("Stufe 3c übersprungen (QUALI_ON=false)")
        return
    if not icp_prompt.strip():
        raise SystemExit("Kein ICP-Prompt hinterlegt — bitte `scraper set-icp <datei>` ausführen.")

    rows = conn.execute(
        "SELECT id, website_final FROM datensaetze "
        "WHERE dedupe_status='kept' AND website_final <> '' AND icp_raw IS NULL AND attempts < ?",
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


def stufe3d_uebergabe(conn: sqlite3.Connection) -> None:
    """Clay DATENSÄTZE.`Send table data` — ICP-Treffer nach ANREICHERUNG übergeben."""
    if not CONFIG.send_on:
        log.info("Stufe 3d übersprungen (SEND_ON=false)")
        return
    rows = conn.execute("""
        SELECT d.* FROM datensaetze d
        LEFT JOIN anreicherung a ON a.datensatz_id = d.id
        WHERE d.dedupe_status='kept' AND d.is_icp=1 AND a.id IS NULL
    """).fetchall()
    log.info("Stufe 3d — Übergabe an Anreicherung: %s neue Leads", len(rows))

    for row in rows:
        db.upsert(conn, "anreicherung", {
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
def stufe4a_website_final(conn: sqlite3.Connection, llm: LLM) -> None:
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
            company_domain = llm.company_domain(row["firmenname"] or "", model=CONFIG.model_domain)
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
    """Clay ANREICHERUNG.`SKAEL WEBSCRAPER` → `Bodytext Website` → `Personalisierung AI`."""
    if not CONFIG.do_personalisierung:
        log.info("Stufe 4e übersprungen (DO_PERSONALISIERUNG=false)")
        return
    rows = conn.execute(
        "SELECT id, website_final, webscraper_raw FROM anreicherung "
        "WHERE email_final <> '' AND website_final <> '' AND personalisierung IS NULL "
        "AND attempts < ?",
        (MAX_ATTEMPTS,),
    ).fetchall()
    log.info("Stufe 4e — Personalisierung: %s Leads", len(rows))

    def work(row: sqlite3.Row) -> None:
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
        # Jeder Lead in dieser Tabelle hat PRUEFUNG 2 des ICP-Profils bestanden,
        # verkauft also nachweislich an Firmenkunden. "unklar" heisst hier nur,
        # dass die Startseite die Kundschaft nicht ausformuliert — fachlich ist
        # das trotzdem ein Lead-Gen-Fall, kein unbekannter.
        if einordnung["kategorie"] in ("unklar", ""):
            einordnung["kategorie"] = "Lead Gen"
            if not einordnung["beleg"] or einordnung["beleg"] == "kein Beleg":
                einordnung["beleg"] = "B2B-Verkauf über Prüfprofil belegt, Kanal auf der Seite nicht ausgeführt"

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
        "WHERE email_final <> '' AND video_title IS NULL AND attempts < ?",
        (MAX_ATTEMPTS,),
    ).fetchall()
    log.info("Stufe 4f — Videotitel: %s Leads", len(rows))

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
    from .config import PROMPTS_DIR
    from .llm import render

    template = (PROMPTS_DIR / "linkedin_research_body.json.tpl").read_text(encoding="utf-8")
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
        bedingungen.append("COALESCE(personalisierung,'') <> ''")
    if CONFIG.do_video_title:
        bedingungen.append("COALESCE(video_title,'') <> ''")
    with db.write(conn):
        conn.execute(
            "UPDATE anreicherung SET ready_to_send = CASE WHEN "
            + " AND ".join(bedingungen) + " THEN 1 ELSE 0 END"
        )
    ready = conn.execute("SELECT COUNT(*) FROM anreicherung WHERE ready_to_send=1").fetchone()[0]
    log.info("Ready to Send: %s Leads", ready)
