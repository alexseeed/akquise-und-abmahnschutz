"""CSV-Export der fertigen Leads (Semikolon, UTF-8 mit BOM — öffnet sich sauber in Excel).

  1. Geschäftsführer-Adresse   (Clay-Ansicht „Export final“ = Ready to Send, Typ "GF")
  2. info@-Adresse             (dito, Typ "Info@")
  3. Aussortiert               (kein aktiver Shop, passt nicht zum Shop-Profil, kein Traffic, keine E-Mail,
                                Duplikat, mit E-Mail, aber nicht versandfertig …) – nur Firmendaten mit Grund
  4. Gesperrt                  (Community-Sperrliste: Abmahner-Domains — nie anschreiben)
  + Lead-Archiv als JSON mit allen Rohdaten

Vor jedem Export wird die Community-Sperrliste geladen. Treffer landen nur in Liste 4.
Ist ein Mailtext hinterlegt (`set-mailtext`), bekommen Liste 1 und 2 die Spalten „Betreff“
und „Mailtext“, je Lead ausgefüllt.
"""
from __future__ import annotations

import csv
import json
import sqlite3
from datetime import datetime
from pathlib import Path

from . import db, mailtext as mailtext_mod, pipeline, sperrliste as sperrliste_mod
from .config import CONFIG, EXPORT_DIR

PFAD = "e-commerce"

# Reihenfolge folgt der Clay-Ansicht „Export final“, ergänzt um das Standardformat (wissen/07)
COLUMNS = [
    ("firmenname_final", "Firmenname"),
    ("website_final", "Website"),
    ("email_final", "E-Mail"),
    ("email_final_type", "E-Mail Typ"),
    ("email_final_status", "E-Mail Status"),
    ("email_source_gf", "E-Mail Quelle"),
    ("anrede", "Anrede"),
    ("first_name", "Vorname"),
    ("last_name", "Nachname"),
    ("kontaktperson_sauber", "Kontaktperson"),
    ("ansprache_formal", "Ansprache Formal"),
    ("ansprache_normal", "Ansprache Normal"),
    ("ansprache_normal_gt", "Ansprache Guten Tag"),
    ("ansprache_persoenlich", "Ansprache Persönlich"),
    ("personalisierung", "Personalisierung"),
    ("video_title", "Videotitel"),
    ("adresse_impressum", "Adresse (Impressum)"),
    ("telefon_impressum", "Telefon (Impressum)"),
    ("email_impressum", "E-Mail (Impressum)"),
    ("avr_traffic", "Besuche/Monat (Schnitt)"),
    ("max_traffic_3mo", "Besuche/Monat (Höchstwert)"),
    ("firmenname", "Firmenname (Import)"),
    ("quelle", "Quelle"),
    ("_pfad", "Pfad"),
]

# Nur mit hinterlegtem Mailtext, direkt hinter „Videotitel“
MAIL_COLUMNS = [
    ("_betreff", "Betreff"),
    ("_mailtext", "Mailtext"),
]

AUSSORTIERT_COLUMNS = [
    ("firmenname", "Firmenname"),
    ("website_final", "Website"),
    ("_grund", "Grund"),
    ("avr_traffic", "Besuche/Monat (Schnitt)"),
    ("max_traffic_3mo", "Besuche/Monat (Höchstwert)"),
    ("error", "Letzte Fehlermeldung"),
    ("quelle", "Quelle"),
]


def _schreibe(target: Path, spalten: list[tuple[str, str]], rows: list[dict]) -> int:
    with target.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.writer(fh, delimiter=";")
        writer.writerow([label for _, label in spalten])
        for row in rows:
            writer.writerow([row.get(key, "") if row.get(key) is not None else "" for key, _ in spalten])
    return len(rows)


def _leads(conn: sqlite3.Connection, where: str, params: tuple = ()) -> list[dict]:
    rows = conn.execute(
        f"SELECT a.*, s.quelle FROM anreicherung a JOIN shops s ON s.id = a.shop_id WHERE {where} "
        "ORDER BY a.firmenname_final", params).fetchall()
    return [{**{k: r[k] for k in r.keys()}, "_pfad": PFAD} for r in rows]


def _lead_spalten(mailtext: str) -> list[tuple[str, str]]:
    if not mailtext:
        return COLUMNS
    pos = [key for key, _ in COLUMNS].index("video_title") + 1
    return COLUMNS[:pos] + MAIL_COLUMNS + COLUMNS[pos:]


def grund_shop(row: sqlite3.Row, profil_aktiv: bool = False) -> str:
    """Warum ein Shop aus Stufe 1 nicht in die Anreicherung kam."""
    if not row["website_final"]:
        return "keine Website (auch per Suche nicht gefunden)" if row["website_final"] == "" else "noch nicht geprüft"
    if row["webscraper_raw"] is None:
        return "Website noch nicht abgerufen" if not row["error"] else "Website nicht abrufbar"
    if not row["bodytext"]:
        return "Website ohne Text (leer, gesperrt oder nur JavaScript)"
    if row["is_active_shop"] is None:
        return "Shop-Prüfung ausstehend"
    if row["is_active_shop"] == 0:
        return "kein aktiver Onlineshop"
    if row["passt_profil"] == 0:
        grund = (row["profil_grund"] or "").strip()
        return f"passt nicht zum Shop-Profil: {grund}" if grund else "passt nicht zum Shop-Profil"
    if profil_aktiv and row["profil_raw"] is None:
        return "Profil-Prüfung ausstehend"
    if row["webtraffic_raw"] is None:
        return "Traffic noch nicht abgefragt"
    if row["send"] == 1:
        return "Übergabe an die Anreicherung ausstehend"
    return "kein messbarer Traffic (SimilarWeb ohne Daten oder unter Schwelle)"


def grund_lead(lead: dict) -> str:
    """Warum ein Lead mit E-Mail nicht „Ready to Send“ ist (Liste 3); die Fehlermeldung steht in eigener Spalte."""
    if lead.get("anrede") is None:
        fehlt = "Anrede fehlt"
    elif CONFIG.do_personalisierung and not lead.get("personalisierung"):
        fehlt = ("kein persönlicher Satz (Website ohne Text)" if lead.get("personalisierung") == ""
                 else "kein persönlicher Satz")
    elif CONFIG.do_video_title and not lead.get("video_title"):
        fehlt = "Videotitel fehlt"
    else:
        fehlt = "Ready to Send noch nicht berechnet (run --stage 2g)"
    if (lead.get("attempts") or 0) >= pipeline.MAX_ATTEMPTS:
        fehlt += f" – nach {pipeline.MAX_ATTEMPTS} Fehlversuchen liegen geblieben (fehler-zuruecksetzen)"
    return f"nicht versandfertig: {fehlt}"


def export_listen(conn: sqlite3.Connection, *, only_ready: bool = True) -> list[tuple[str, Path, int]]:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    ergebnis: list[tuple[str, Path, int]] = []
    vorlage = db.get_meta(conn, db.META_MAILTEXT) or ""
    if vorlage.strip():
        fehler, _ = mailtext_mod.pruefen(vorlage)
        if fehler:
            raise SystemExit("Der hinterlegte Mailtext hat Fehler – Export abgebrochen:\n  - "
                             + "\n  - ".join(fehler)
                             + "\nKorrigieren und neu setzen: python3 -m ecom set-mailtext <datei>")
    spalten = _lead_spalten(vorlage.strip())
    sperre = sperrliste_mod.laden()   # bricht ab, wenn Pflicht und nicht ladbar
    gesperrt: list[dict] = []

    basis = "COALESCE(a.email_final_type,'')=? AND a.dedupe_status='kept'"
    if only_ready:
        basis += " AND a.ready_to_send=1 AND a.bereits_exportiert=0"

    for typ, bezeichnung, dateiname in (
        ("GF", "Geschäftsführer-Adresse", "1_geschaeftsfuehrer"),
        ("Info@", "info@-Adresse", "2_info"),
    ):
        frei = []
        for lead in _leads(conn, basis, (typ,)):
            domain = sperre.treffer(lead.get("email_final"), lead.get("website_final")) if sperre else None
            if domain:
                gesperrt.append({**lead, "_grund": f"Community-Sperrliste ({domain})"})
                continue
            if vorlage.strip():
                lead["_betreff"], lead["_mailtext"] = mailtext_mod.rendern(vorlage, lead)
            frei.append(lead)
        target = EXPORT_DIR / f"{dateiname}_{stamp}.csv"
        ergebnis.append((bezeichnung, target, _schreibe(target, spalten, frei)))

    # --- 3: aussortiert -------------------------------------------------
    # Alle nicht übergebenen Shops – auch solche mit Traffic, die das Shop-Profil abgelehnt hat –
    # und übergebene, noch nicht exportierte, die ein geändertes Profil ablehnt oder noch prüfen muss
    profil_aktiv = bool((db.get_meta(conn, db.META_SHOPPROFIL) or "").strip())
    shops = conn.execute(
        "SELECT * FROM shops WHERE COALESCE(uebergeben,0)=0 OR (id IN (SELECT shop_id FROM anreicherung "
        f"WHERE COALESCE(bereits_exportiert,0)=0) AND NOT ({pipeline.profil_ok_sql(conn)})) "
        "ORDER BY firmenname").fetchall()
    aussortiert = [{**{k: r[k] for k in r.keys()}, "_grund": grund_shop(r, profil_aktiv)} for r in shops]
    schon_drin = {r["id"] for r in shops}
    for lead in _leads(conn, "a.dedupe_status='dropped_duplicate'"):
        if lead["shop_id"] not in schon_drin:
            aussortiert.append({**lead, "_grund": f"Duplikat (E-Mail-Domain {lead.get('email_domain')})"})
    for lead in _leads(conn, "a.dedupe_status='kept' AND a.impressum_raw IS NOT NULL "
                             "AND COALESCE(a.email_final,'') = ''"):
        if lead["shop_id"] not in schon_drin:
            aussortiert.append({**lead, "_grund": f"keine E-Mail ({lead.get('email_final_status') or 'offen'})"})
    if only_ready:
        # mit E-Mail, aber nicht versandfertig (z. B. persönlicher Satz dreimal gescheitert) – sonst in keiner Liste
        for lead in _leads(conn, "a.dedupe_status='kept' AND COALESCE(a.email_final,'') <> '' "
                                 "AND COALESCE(a.ready_to_send,0)=0 AND COALESCE(a.bereits_exportiert,0)=0"):
            if lead["shop_id"] not in schon_drin:
                aussortiert.append({**lead, "_grund": grund_lead(lead)})
    target = EXPORT_DIR / f"3_aussortiert_{stamp}.csv"
    ergebnis.append(("Aussortiert · nur zur Nachvollziehbarkeit", target,
                     _schreibe(target, AUSSORTIERT_COLUMNS, aussortiert)))

    # --- 4: gesperrt ----------------------------------------------------
    target = EXPORT_DIR / f"4_gesperrt_sperrliste_{stamp}.csv"
    quelle = sperre.quelle if sperre is not None else "nicht geladen (SPERRLISTE_PFLICHT=false)"
    ergebnis.append((f"Gesperrt · Community-Sperrliste, {len(sperre) if sperre else 0} Domains, {quelle}",
                     target, _schreibe(target, AUSSORTIERT_COLUMNS, gesperrt)))

    json_pfad, json_anzahl = export_json(conn, stamp)
    ergebnis.append(("Lead-Archiv (JSON, alle Rohdaten)", json_pfad, json_anzahl))
    return ergebnis


def export_json(conn: sqlite3.Connection, stamp: str) -> tuple[Path, int]:
    """Alle Shops mit allen Rohantworten — Bestand aufbauen, ohne erneut abzufragen."""
    target = EXPORT_DIR / f"shops_archiv_{stamp}.json"
    an = {r["shop_id"]: {k: r[k] for k in r.keys()} for r in conn.execute("SELECT * FROM anreicherung")}
    eintraege = []
    for r in conn.execute("SELECT * FROM shops ORDER BY id"):
        shop = {k: r[k] for k in r.keys()}
        shop["anreicherung"] = an.get(r["id"])
        for teil in (shop, shop["anreicherung"] or {}):
            for feld, wert in list(teil.items()):
                if feld.endswith("_raw") and isinstance(wert, str):
                    try:
                        teil[feld] = json.loads(wert)
                    except json.JSONDecodeError:
                        pass
        eintraege.append(shop)
    target.write_text(json.dumps({"exportiert_am": datetime.now().isoformat(timespec="seconds"),
                                  "pfad": PFAD, "anzahl": len(eintraege), "shops": eintraege},
                                 ensure_ascii=False, indent=2), encoding="utf-8")
    return target, len(eintraege)


def mark_exported(conn: sqlite3.Connection) -> int:
    """Exportierte Leads markieren, damit sie beim nächsten Export nicht erneut kommen.

    Markiert alle versandfertigen Leads, auch die gesperrten aus Liste 4. Zählt nur neu markierte.
    """
    with db.write(conn):
        cur = conn.execute("UPDATE anreicherung SET bereits_exportiert=1 "
                           "WHERE ready_to_send=1 AND COALESCE(bereits_exportiert,0)=0")
    return cur.rowcount
