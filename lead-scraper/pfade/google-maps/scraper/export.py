"""CSV-Export der fertigen Leads.

Vier getrennte Listen statt einer Datei:

  1. Zielgruppe, Geschaeftsfuehrer-Adresse   (anreicherung, Typ "GF")
  2. Zielgruppe, info@-Adresse               (anreicherung, Typ "Info@")
  3. Unsicher                                (datensaetze, Confidence 0,40-0,60)
  4. Nicht Zielgruppe                        (datensaetze, aussortiert oder nicht pruefbar)
  5. Gesperrt                                (Community-Sperrliste: Abmahner-Domains — nie anschreiben)

Vor jedem Export wird die Community-Sperrliste geladen (siehe sperrliste.py). Leads, deren
E-Mail- oder Website-Domain dort steht, landen nur in Liste 5 und nie in den Listen 1 und 2.

Die Listen 3 und 4 enthalten bewusst **nur Firmendaten**. Diese Firmen haben
Stufe 4 nie durchlaufen, es gibt also weder E-Mail noch Anrede.
"""
from __future__ import annotations

import csv
import json
import sqlite3
from datetime import datetime
from pathlib import Path

from . import sperrliste as sperrliste_mod
from .config import EXPORT_DIR, KETTEN_AUSSCHLUSS

# Reihenfolge orientiert sich an den Clay-Spalten der ANREICHERUNG-Tabelle
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
    ("pain_category", "Pain / Angebot"),
    ("pain_beleg", "Einordnung belegt durch"),
    ("partnernetz", "Partnernetz vorhanden"),
    ("video_title", "Videotitel"),
    ("adresse_impressum", "Adresse (Impressum)"),
    ("address", "Adresse (Maps)"),
    ("zip", "PLZ"),
    ("telefon_impressum", "Telefon (Impressum)"),
    ("phone_imported", "Telefon (Maps)"),
    ("category", "Kategorie"),
    ("rating", "Bewertung"),
    ("review_count", "Anzahl Bewertungen"),
    ("linkedin_url", "LinkedIn"),
    ("query_keyword", "Keyword"),
    ("query_city", "Stadt"),
    ("query_country", "Land"),
    ("business_id", "Business ID"),
    ("place_id", "Place ID"),
]

# Firmenlisten (unsicher / nicht Zielgruppe) — ohne Kontaktdaten
FIRMEN_COLUMNS = [
    ("firmenname", "Firmenname"),
    ("website_final", "Website"),
    ("_grund", "Einstufung"),
    ("icp_confidence", "Sicherheit"),
    ("icp_reason", "Begründung"),
    ("category", "Kategorie (Maps)"),
    ("address", "Adresse"),
    ("zip", "PLZ"),
    ("phone", "Telefon"),
    ("rating", "Bewertung"),
    ("review_count", "Anzahl Bewertungen"),
    ("query_keyword", "Keyword"),
    ("query_city", "Stadt"),
    ("query_country", "Land"),
]

# Eine Firma gilt als "unsicher", wenn das Pruefprofil sie in den reservierten
# Confidence-Bereich gelegt oder die Begruendung entsprechend markiert hat.
_UNSICHER = "(icp_confidence BETWEEN 0.40 AND 0.60 OR icp_reason LIKE 'UNSICHER:%')"


def _schreibe(target: Path, spalten: list[tuple[str, str]], rows) -> int:
    with target.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.writer(fh, delimiter=";")
        writer.writerow([label for _, label in spalten])
        for row in rows:
            keys = row.keys() if hasattr(row, "keys") else row
            writer.writerow([row[key] if key in keys else "" for key, _ in spalten])
    return len(rows)


def export_csv(conn: sqlite3.Connection, *, only_ready: bool = True, path: Path | None = None) -> Path:
    """Einzelne Gesamtliste — unveraendertes Verhalten fuer Bestandsaufrufe."""
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    suffix = "ready" if only_ready else "alle"
    target = path or EXPORT_DIR / f"leads_{suffix}_{stamp}.csv"

    where = "WHERE ready_to_send=1 AND bereits_exportiert=0" if only_ready else ""
    alle = conn.execute(f"SELECT * FROM anreicherung {where} ORDER BY firmenname_final").fetchall()
    # Konzerne und Filialketten auch hier ausschliessen — sonst weicht die
    # Gesamtliste von den vier getrennten Listen ab.
    rows = [r for r in alle if not _ist_kette(r["firmenname_final"] or r["firmenname"])]
    sperre = sperrliste_mod.laden()
    if sperre is not None:
        rows = [r for r in rows if not _gesperrt(sperre, r)]
    _schreibe(target, COLUMNS, rows)
    return target


def export_listen(conn: sqlite3.Connection, *, only_ready: bool = True) -> list[tuple[str, Path, int]]:
    """Schreibt die vier Listen. Gibt (Bezeichnung, Pfad, Zeilenzahl) je Liste zurueck."""
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    ergebnis: list[tuple[str, Path, int]] = []
    ketten: list = []
    gesperrt: list[dict] = []
    sperre = sperrliste_mod.laden()   # bricht ab, wenn Pflicht und nicht ladbar

    # --- 1 + 2: Zielgruppe, getrennt nach E-Mail-Typ ---------------------
    basis = "FROM anreicherung WHERE COALESCE(email_final_type,'')=?"
    if only_ready:
        basis += " AND ready_to_send=1 AND bereits_exportiert=0"

    for typ, bezeichnung, dateiname in (
        ("GF", "Zielgruppe · Geschäftsführer-Adresse", "1_zielgruppe_geschaeftsfuehrer"),
        ("Info@", "Zielgruppe · info@-Adresse", "2_zielgruppe_info"),
    ):
        alle = conn.execute(f"SELECT * {basis} ORDER BY firmenname_final", (typ,)).fetchall()
        rows = [r for r in alle if not _ist_kette(r["firmenname_final"] or r["firmenname"])]
        ketten.extend(r for r in alle if _ist_kette(r["firmenname_final"] or r["firmenname"]))
        if sperre is not None:
            frei = []
            for r in rows:
                domain = _gesperrt(sperre, r)
                if domain:
                    eintrag = _mit_grund(r, f"Community-Sperrliste ({domain})")
                    eintrag.setdefault("firmenname", eintrag.get("firmenname_final"))
                    gesperrt.append(eintrag)
                else:
                    frei.append(r)
            rows = frei
        target = EXPORT_DIR / f"{dateiname}_{stamp}.csv"
        ergebnis.append((bezeichnung, target, _schreibe(target, COLUMNS, rows)))

    # --- 3: unsichere Faelle --------------------------------------------
    rows = conn.execute(
        f"SELECT * FROM datensaetze WHERE dedupe_status='kept' AND is_icp=0 AND {_UNSICHER} "
        "ORDER BY icp_confidence DESC, firmenname"
    ).fetchall()
    target = EXPORT_DIR / f"3_unsicher_{stamp}.csv"
    ergebnis.append(("Unsicher · manuell prüfen",
                     target, _schreibe(target, FIRMEN_COLUMNS,
                                       [_mit_grund(r, "unsicher") for r in rows])))

    # --- 4: nicht Zielgruppe (inkl. nicht pruefbar) ----------------------
    aussortiert = conn.execute(
        f"SELECT * FROM datensaetze WHERE dedupe_status='kept' AND is_icp=0 AND NOT {_UNSICHER} "
        "ORDER BY firmenname"
    ).fetchall()
    nicht_pruefbar = conn.execute(
        "SELECT * FROM datensaetze WHERE dedupe_status='kept' AND is_icp IS NULL "
        "ORDER BY firmenname"
    ).fetchall()
    target = EXPORT_DIR / f"4_nicht_zielgruppe_{stamp}.csv"
    daten = ([_mit_grund(r, "aussortiert") for r in aussortiert]
             + [_mit_grund(r, "nicht prüfbar (keine Website)") for r in nicht_pruefbar]
             + [_mit_grund(r, "Konzern/Filialkette") for r in ketten])
    ergebnis.append(("Nicht Zielgruppe", target, _schreibe(target, FIRMEN_COLUMNS, daten)))

    # --- 5: gesperrt (Community-Sperrliste) -------------------------------
    target = EXPORT_DIR / f"5_gesperrt_sperrliste_{stamp}.csv"
    quelle = sperre.quelle if sperre is not None else "nicht geladen (SPERRLISTE_PFLICHT=false)"
    ergebnis.append((f"Gesperrt · Community-Sperrliste, {len(sperre) if sperre else 0} Domains, {quelle}",
                     target, _schreibe(target, FIRMEN_COLUMNS, gesperrt)))

    # Immer zusaetzlich der vollstaendige JSON-Abzug fuers Lead-Archiv
    json_pfad, json_anzahl = export_json(conn)
    ergebnis.append(("Lead-Archiv (JSON, alle Rohdaten)", json_pfad, json_anzahl))

    return ergebnis


def export_json(conn: sqlite3.Connection, path: Path | None = None) -> tuple[Path, int]:
    """Vollstaendiger JSON-Abzug aller qualifizierten Leads — das Lead-Archiv.

    Anders als die CSV-Listen enthaelt der Abzug *alle* Spalten inklusive der
    Rohantworten (Maps, Impressum, Mailfinder, Verify, Website) und der
    Herkunftsdaten aus der Firmentabelle. Damit laesst sich ein Bestand ueber
    mehrere Kampagnen aufbauen, ohne je erneut scrapen zu muessen.
    """
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target = path or EXPORT_DIR / f"leads_archiv_{stamp}.json"

    rows = conn.execute("""
        SELECT a.*,
               d.icp_confidence, d.icp_reason, d.icp_label, d.icp_raw,
               d.maps_raw, d.dedupe_key, d.phone AS maps_phone
          FROM anreicherung a
          LEFT JOIN datensaetze d ON d.id = a.datensatz_id
         ORDER BY a.firmenname_final
    """).fetchall()

    leads = []
    for row in rows:
        eintrag = {k: row[k] for k in row.keys()}
        # Rohantworten als echtes JSON einbetten statt als String
        for feld in ("maps_raw", "impressum_raw", "mailfinder_raw", "findymail_raw",
                     "verify_gf_raw", "verify_info_raw", "webscraper_raw", "icp_raw"):
            if eintrag.get(feld):
                try:
                    eintrag[feld] = json.loads(eintrag[feld])
                except (json.JSONDecodeError, TypeError):
                    pass
        eintrag["site_links"] = (eintrag.get("site_links") or "").splitlines()
        leads.append(eintrag)

    target.write_text(json.dumps(
        {"exportiert_am": datetime.now().isoformat(timespec="seconds"),
         "anzahl": len(leads), "leads": leads},
        ensure_ascii=False, indent=2), encoding="utf-8")
    return target, len(leads)


def _gesperrt(sperre, row) -> str | None:
    """Gesperrte Domain, wenn E-Mail oder Website des Leads auf der Sperrliste steht."""
    keys = row.keys()
    return sperre.treffer(*(row[k] for k in ("email_final", "website_final", "website") if k in keys))


def _ist_kette(name: str | None) -> bool:
    """Deterministischer Nachfilter fuer Konzerne und Filialketten."""
    n = (name or "").lower()
    return any(k in n for k in KETTEN_AUSSCHLUSS)


def _mit_grund(row: sqlite3.Row, grund: str) -> dict:
    """sqlite3.Row ist unveraenderlich — als dict kopieren und Einstufung ergaenzen."""
    daten = {key: row[key] for key in row.keys()}
    daten["_grund"] = grund
    return daten


def mark_exported(conn: sqlite3.Connection) -> int:
    """Setzt `Bereits exportiert` — Gegenstück zur manuellen Clay-Checkbox."""
    from . import db

    with db.write(conn):
        cur = conn.execute("UPDATE anreicherung SET bereits_exportiert=1 WHERE ready_to_send=1")
    return cur.rowcount
