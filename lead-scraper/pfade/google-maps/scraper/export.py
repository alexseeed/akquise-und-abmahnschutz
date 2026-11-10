"""CSV-Export der fertigen Leads.

Vier getrennte Listen statt einer Datei:

  1. Zielgruppe, Geschaeftsfuehrer-Adresse   (anreicherung, Typ "GF")
  2. Zielgruppe, info@-Adresse               (anreicherung, Typ "Info@")
  3. Unsicher                                (datensaetze, Confidence 0,40-0,60)
  4. Nicht Zielgruppe                        (datensaetze, aussortiert oder nicht pruefbar)
  5. Gesperrt                                (Community-Sperrliste: Abmahner-Domains — nie anschreiben;
                                              eigene Blockliste: bereits kontaktiert)

Vor jedem Export wird die Community-Sperrliste geladen (siehe sperrliste.py). Leads, deren
E-Mail- oder Website-Domain dort steht, landen nur in Liste 5 und nie in den Listen 1 und 2.
Dasselbe gilt für die eigene Blockliste (siehe blockliste.py).

Die Listen 3 und 4 enthalten bewusst **nur Firmendaten**. Diese Firmen haben
Stufe 4 nie durchlaufen, es gibt also weder E-Mail noch Anrede.

Stellensuche schreibt zusaetzlich `0_stellen_…` (eine Zeile je Anzeige); mit `--nur-stellen`
ersetzt `1_firmen_mit_stellen_…` die Lead-Listen. Recruiting und Stellensuche haengen je Lead die
Stellenspalten an (EXTRA_COLUMNS).

Listen 1 und 2 tragen je Datensatz die Herkunft (Externe ID, Quelle URL, Erfasst am) fuer die
Information nach Art. 14 DSGVO. `export --lead-format` schreibt dieselben Leads zusaetzlich im
festen Lead-Format fuer die Landingpages (leads_<kampagne-oder-db>_<stamp>.json).
"""
from __future__ import annotations

import csv
import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path

from . import blockliste as blockliste_mod, db as db_mod, sperrliste as sperrliste_mod, transforms as T
from .config import CONFIG, EXPORT_DIR, KAMPAGNE, KETTEN_AUSSCHLUSS
from .transforms import host_of

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
    # Standard-Ansprache: persönlich nur bei Anrede-Sicherheit > 60, sonst neutral (siehe _lead)
    ("_ansprache", "Ansprache"),
    ("_ansprache_grund", "Ansprache Grund"),
    ("anrede_confidence", "Anrede Sicherheit"),
    ("personalisierung", "Personalisierung"),
    ("_absatz", "Absatz Beobachtung"),
    ("pain_category", "Einordnung"),
    ("pain_beleg", "Einordnung belegt durch"),
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
    # Provenance per record (Art. 14 GDPR) — derived in _schreibe, see _ABGELEITET
    ("externe_id", "Externe ID"),
    ("quelle_url", "Quelle URL"),
    ("erfasst_am", "Erfasst am"),
    ("_pfad", "Kampagnen-Art"),
]

# Zusatzspalten je Kampagnen-Art (Leads in den Listen 1 und 2)
EXTRA_COLUMNS = {
    "recruiting": [
        ("strecke", "Strecke"),
        ("job_title_norm", "Jobtitel"),
        ("job_title", "Stelle (Original)"),
        ("job_bereich", "Bereich"),
        ("job_description", "Stellenbeschreibung"),
    ],
    "stellensuche": [
        ("job_title_norm", "Jobtitel"),
        ("job_title", "Stellenbezeichnung"),
        ("stelle_ort", "Ort der Stelle"),
        ("stelle_datum", "veröffentlicht am"),
        ("stelle_portal", "Portal"),
        ("stelle_url", "Link zur Anzeige"),
        ("stelle_gehalt", "Gehalt"),
        ("stellen_anzahl", "Offene Stellen (Anzahl)"),
        ("stellen_portale", "Gefunden auf"),
    ],
}

# Stellensuche: eine Zeile je Anzeige (Datei 0_stellen_…)
STELLEN_COLUMNS = [
    ("firma_final", "Firma"),
    ("titel", "Stellenbezeichnung"),
    ("ort", "Ort"),
    ("plz", "PLZ"),
    ("veroeffentlicht", "veröffentlicht am"),
    ("portal", "Portal"),
    ("url", "Link zur Anzeige"),
    ("gehalt", "Gehalt"),
    ("website_final", "Website"),
    ("suchbegriff", "Suchbegriff"),
    ("_lead_liste", "Firma in Lead-Liste"),
]

# Fixed lead format for the landing pages (export --lead-format), lists 1 and 2 only
LEAD_FORMAT_FELDER = (
    "externe_id", "firma", "rechtsform", "domain", "website", "strasse", "plz", "ort", "land",
    "telefon", "branche", "mitarbeiter", "handelsregister", "anrede", "vorname", "nachname",
    "position", "email", "email_typ", "email_status", "kontakt_telefon", "linkedin_url",
    "quelle", "quelle_url", "erfasst_am", "personalisierung", "video_titel",
)

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

EXTRA_FIRMEN_COLUMNS = {
    "recruiting": [
        ("job_title", "Offene Stelle"),
        ("stelle_url", "Gefunden auf"),
    ],
    "stellensuche": [
        ("job_title", "Stellenbezeichnung"),
        ("stelle_ort", "Ort der Stelle"),
        ("stelle_datum", "veröffentlicht am"),
        ("stelle_portal", "Portal"),
        ("stelle_url", "Link zur Anzeige"),
        ("stelle_gehalt", "Gehalt"),
        ("stellen_anzahl", "Offene Stellen (Anzahl)"),
        ("stellen_portale", "Gefunden auf"),
    ],
}


def _spalten(conn: sqlite3.Connection, firmen: bool = False) -> list[tuple[str, str]]:
    pfad = db_mod.pfad(conn)
    if firmen:
        return FIRMEN_COLUMNS + EXTRA_FIRMEN_COLUMNS.get(pfad, [])
    return COLUMNS + EXTRA_COLUMNS.get(pfad, [])


def _lead(row: sqlite3.Row, pfad: str) -> dict:
    """Lead als dict plus berechnete Spalten: Standard-Ansprache (≤ 60 → neutral) und Pfad."""
    daten = {key: row[key] for key in row.keys()}
    daten["_ansprache"], daten["_ansprache_grund"] = T.ansprache_sicher(
        daten.get("anrede"), daten.get("last_name"), daten.get("anrede_confidence"))
    daten["_pfad"] = pfad
    return daten


# Eine Firma gilt als "unsicher", wenn das Pruefprofil sie in den reservierten
# Confidence-Bereich gelegt oder die Begruendung entsprechend markiert hat.
# COALESCE: ohne Sicherheitswert (Prüfung ohne Score) wäre der Ausdruck NULL —
# die Firma fiele dann aus Liste 3 UND Liste 4 heraus.
_UNSICHER = ("(COALESCE(icp_confidence, -1) BETWEEN 0.40 AND 0.60 "
             "OR COALESCE(icp_reason, '') LIKE 'UNSICHER:%')")


def absatz_beobachtung(personalisierung: str | None) -> str:
    """Fertiger Absatz für die Mail: mit Beobachtungssatz oder — ohne konkretes Detail — Standardabsatz."""
    satz = (personalisierung or "").strip()
    if satz:
        return " ".join(t for t in (CONFIG.absatz_einleitung, satz, CONFIG.absatz_folgesatz) if t)
    return CONFIG.absatz_standard


# shortcut: vier identische Kopien (zwei Pfade, zwei Werkzeuge), weil es kein gemeinsames Paket gibt; zusammenlegen, sobald es eines gibt
_ZAHL_TELEFON_ZEICHEN = frozenset("0123456789+-().,/ ")


def _ist_zahl_oder_telefon(text: str) -> bool:
    """Reine Zahl oder Telefonnummer (z. B. -12,5 oder +41 (0)44 …): kein Buchstabe, kein =, kein Rechenzeichen innen."""
    if not any(ch.isdigit() for ch in text):
        return False
    if any(ch not in _ZAHL_TELEFON_ZEICHEN for ch in text):
        return False
    rest = text[1:]
    if not rest or rest[0] in "+-" or "+" in rest:
        return False
    return text[0] == "+" or "-" not in rest  # Minus innen nur bei +… (Telefon), sonst Ausdruck wie -2-3


def csv_zelle(wert) -> str:
    """Macht eine Datenzelle formelsicher: führende = + - @ Tab CR neutralisieren, Zahlen/Telefone bleiben."""
    if wert is None:
        return ""
    text = wert if isinstance(wert, str) else str(wert)
    if not text or text[0] not in "=+-@\t\r":
        return text
    if text[0] in "+-" and _ist_zahl_oder_telefon(text):
        return text
    return "'" + text


def _schreibe(target: Path, spalten: list[tuple[str, str]], rows) -> int:
    with target.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.writer(fh, delimiter=";")
        writer.writerow([label for _, label in spalten])
        for row in rows:
            keys = row.keys() if hasattr(row, "keys") else row
            werte = []
            for key, _ in spalten:
                if key == "_absatz":
                    werte.append(absatz_beobachtung(row["personalisierung"] if "personalisierung" in keys else ""))
                elif key in _ABGELEITET and key not in keys:
                    werte.append(_ABGELEITET[key](row))
                else:
                    werte.append(row[key] if key in keys else "")
            writer.writerow([csv_zelle(w) for w in werte])
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
    pfad = db_mod.pfad(conn)
    rows = [_lead(r, pfad) for r in alle if not _ist_kette(r["firmenname_final"] or r["firmenname"])]
    sperre = sperrliste_mod.laden()
    if sperre is not None:
        rows = [r for r in rows if not _gesperrt(sperre, r)]
    eigene = blockliste_mod.laden()
    rows = [r for r in rows if not _gesperrt(eigene, r)]
    _schreibe(target, _spalten(conn), rows)
    return target


def export_listen(conn: sqlite3.Connection, *, only_ready: bool = True,
                  lead_format: bool = False) -> list[tuple[str, Path, int]]:
    """Schreibt die vier Listen. Gibt (Bezeichnung, Pfad, Zeilenzahl) je Liste zurueck.

    lead_format=True schreibt zusaetzlich leads_<kampagne-oder-db>_<stamp>.json mit genau
    den Leads der Listen 1 und 2 im festen Lead-Format (siehe LEAD_FORMAT_FELDER).
    """
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    ergebnis: list[tuple[str, Path, int]] = []
    ketten: list = []
    gesperrt: list[dict] = []
    zielgruppe: list = []   # rows actually written to lists 1 and 2
    rausgefiltert: list = []
    sperre = sperrliste_mod.laden()   # bricht ab, wenn Pflicht und nicht ladbar
    eigene = blockliste_mod.laden()
    pfad = db_mod.pfad(conn)
    lead_spalten = _spalten(conn)
    firmen_spalten = _spalten(conn, firmen=True)

    if pfad == "stellensuche":
        target = EXPORT_DIR / f"0_stellen_{stamp}.csv"
        stellen = _stellen_zeilen(conn, sperre)
        ergebnis.append(("Alle Stellen · eine Zeile je Anzeige", target,
                         _schreibe(target, STELLEN_COLUMNS, stellen)))
        if _nur_stellen(conn):
            return ergebnis + _listen_nur_stellen(conn, sperre, eigene, firmen_spalten, stamp)

    # --- 1 + 2: Zielgruppe, getrennt nach E-Mail-Typ ---------------------
    basis = "FROM anreicherung WHERE COALESCE(email_final_type,'')=?"
    if only_ready:
        basis += " AND ready_to_send=1 AND bereits_exportiert=0"

    for typ, bezeichnung, dateiname in (
        ("GF", "Zielgruppe · Geschäftsführer-Adresse", "1_zielgruppe_geschaeftsfuehrer"),
        ("Info@", "Zielgruppe · info@-Adresse", "2_zielgruppe_info"),
    ):
        alle = conn.execute(f"SELECT * {basis} ORDER BY firmenname_final", (typ,)).fetchall()
        # Firmen, die nach der Anreicherung herausgefiltert wurden (z. B. geänderter Titel-Filter
        # der Stellensuche, spätere Dedupe), gehören nicht mehr in die Lead-Listen
        weg = {r[0] for r in conn.execute("SELECT id FROM datensaetze WHERE dedupe_status <> 'kept'")}
        rausgefiltert.extend(r for r in alle if r["datensatz_id"] in weg)
        # nachträglich als nicht passend eingestuft (z. B. Größen-Check) — steht schon in Liste 4
        nicht_icp = {r[0] for r in conn.execute("SELECT id FROM datensaetze WHERE is_icp = 0")}
        alle = [r for r in alle if r["datensatz_id"] not in weg and r["datensatz_id"] not in nicht_icp]
        rows = [_lead(r, pfad) for r in alle if not _ist_kette(r["firmenname_final"] or r["firmenname"])]
        ketten.extend(r for r in alle if _ist_kette(r["firmenname_final"] or r["firmenname"]))
        frei = []
        for r in rows:
            domain = _gesperrt(sperre, r) if sperre is not None else None
            grund = f"Community-Sperrliste ({domain})" if domain else None
            if not grund:
                eintrag = _gesperrt(eigene, r)
                grund = f"Eigene Blockliste – bereits kontaktiert ({eintrag})" if eintrag else None
            if grund:
                eintrag = _mit_grund(r, grund)
                eintrag.setdefault("firmenname", eintrag.get("firmenname_final"))
                gesperrt.append(eintrag)
            else:
                frei.append(r)
        rows = frei
        zielgruppe.extend(rows)
        target = EXPORT_DIR / f"{dateiname}_{stamp}.csv"
        ergebnis.append((bezeichnung, target, _schreibe(target, lead_spalten, rows)))

    # --- 3: unsichere Faelle --------------------------------------------
    rows = conn.execute(
        f"SELECT * FROM datensaetze WHERE dedupe_status='kept' AND is_icp=0 AND {_UNSICHER} "
        "ORDER BY icp_confidence DESC, firmenname"
    ).fetchall()
    target = EXPORT_DIR / f"3_unsicher_{stamp}.csv"
    ergebnis.append(("Unsicher · manuell prüfen",
                     target, _schreibe(target, firmen_spalten,
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
    # Recruiting: passt zum Profil, wurde aber nicht angereichert (keine offene Stelle, NK aus)
    ohne_stelle = conn.execute("""
        SELECT d.* FROM datensaetze d LEFT JOIN anreicherung a ON a.datensatz_id = d.id
         WHERE d.dedupe_status='kept' AND d.is_icp=1 AND a.id IS NULL ORDER BY d.firmenname
    """).fetchall() if pfad == "recruiting" else []
    target = EXPORT_DIR / f"4_nicht_zielgruppe_{stamp}.csv"
    ohne_website = "keine eigene Website gefunden" if pfad == "stellensuche" else "nicht prüfbar (keine Website)"
    daten = ([_mit_grund(r, _grund_aussortiert(r)) for r in aussortiert]
             + [_mit_grund(r, ohne_website) for r in nicht_pruefbar]
             + [_mit_grund(r, "passt, aber keine offene Stelle gefunden" if r["stelle_vorhanden"] == 0
                           else "passt, Stellen-Prüfung noch offen") for r in ohne_stelle]
             + [_mit_grund(r, "Konzern/Filialkette") for r in ketten]
             + [_mit_grund(r, "nach Anreicherung herausgefiltert (keine passende Stelle mehr bzw. Dublette)")
                for r in rausgefiltert])
    ergebnis.append(("Nicht Zielgruppe", target, _schreibe(target, firmen_spalten, daten)))

    # --- 5: gesperrt (Community-Sperrliste) -------------------------------
    target = EXPORT_DIR / f"5_gesperrt_sperrliste_{stamp}.csv"
    quelle = sperre.quelle if sperre is not None else "nicht geladen (SPERRLISTE_PFLICHT=false)"
    ergebnis.append((f"Gesperrt · Community-Sperrliste, {len(sperre) if sperre else 0} Domains, {quelle}; "
                     f"eigene Blockliste, {len(eigene)} Einträge",
                     target, _schreibe(target, firmen_spalten, gesperrt)))

    # Immer zusaetzlich der vollstaendige JSON-Abzug fuers Lead-Archiv
    json_pfad, json_anzahl = export_json(conn)
    ergebnis.append(("Lead-Archiv (JSON, alle Rohdaten)", json_pfad, json_anzahl))

    if lead_format:
        target = EXPORT_DIR / f"leads_{_exportname()}_{stamp}.json"
        leads = [lead_format_eintrag(r) for r in zielgruppe]
        target.write_text(json.dumps(leads, ensure_ascii=False, indent=2), encoding="utf-8")
        ergebnis.append(("Lead-Format (JSON, Listen 1 + 2)", target, len(leads)))

    return ergebnis


def _grund_aussortiert(row: sqlite3.Row) -> str:
    """„aussortiert“ bzw. „Größen-Check: Konzern“ (Stellensuche 3g; Details in der Begründung)."""
    reason = row["icp_reason"] or ""
    if reason.startswith("Größen-Check:"):
        return reason.split(" (", 1)[0].split(" – ", 1)[0]
    return "aussortiert"


def _nur_stellen(conn: sqlite3.Connection) -> bool:
    wert = db_mod.get_meta(conn, "nur_stellen", "") or ""
    return str(wert).strip().lower() in {"1", "true", "yes", "ja", "on"}


def _stellen_zeilen(conn: sqlite3.Connection, sperre) -> list[dict]:
    """Alle übernommenen Anzeigen mit Firma und Website — ohne Firmen auf der Sperrliste."""
    rows = conn.execute("""
        SELECT s.*,
               COALESCE(NULLIF(a.firmenname_final, ''), d.firmenname, s.firma) AS firma_final,
               COALESCE(NULLIF(d.website_final, ''), d.website, s.website)    AS website_final,
               a.ready_to_send, a.email_final_type, a.bereits_exportiert
          FROM stellen s
          LEFT JOIN datensaetze d ON d.id = s.datensatz_id
          LEFT JOIN anreicherung a ON a.datensatz_id = d.id
         WHERE s.ausschluss IS NULL
         ORDER BY firma_final, s.veroeffentlicht DESC
    """).fetchall()
    zeilen = []
    for r in rows:
        if sperre is not None and sperre.treffer(r["website_final"], r["website"]):
            continue
        daten = {k: r[k] for k in r.keys()}
        daten["_lead_liste"] = ({"GF": "1 (Geschäftsführer)", "Info@": "2 (info@)"}
                                .get(r["email_final_type"] or "", "") if r["ready_to_send"] else "")
        zeilen.append(daten)
    return zeilen


def _listen_nur_stellen(conn: sqlite3.Connection, sperre, eigene, firmen_spalten, stamp: str
                        ) -> list[tuple[str, Path, int]]:
    """Stellensuche ohne Anreicherung: Firmenliste statt der Lead-Listen 1–4."""
    frei, gesperrt = [], []
    for r in conn.execute("SELECT * FROM datensaetze WHERE dedupe_status='kept' AND quelle='stellen' "
                          "ORDER BY stellen_anzahl DESC, firmenname").fetchall():
        domain = sperre.treffer(r["website_final"], r["website"]) if sperre is not None else None
        eintrag = None if domain else eigene.treffer(r["website_final"], r["website"])
        if domain:
            gesperrt.append(_mit_grund(r, f"Community-Sperrliste ({domain})"))
        elif eintrag:
            gesperrt.append(_mit_grund(r, f"Eigene Blockliste – bereits kontaktiert ({eintrag})"))
        else:
            frei.append(_mit_grund(r, "Stelle offen" if r["website_final"] else "Stelle offen, Website unbekannt"))
    ergebnis = []
    target = EXPORT_DIR / f"1_firmen_mit_stellen_{stamp}.csv"
    ergebnis.append(("Firmen mit offenen Stellen · ohne Kontaktdaten", target,
                     _schreibe(target, firmen_spalten, frei)))
    target = EXPORT_DIR / f"5_gesperrt_sperrliste_{stamp}.csv"
    quelle = sperre.quelle if sperre is not None else "nicht geladen (SPERRLISTE_PFLICHT=false)"
    ergebnis.append((f"Gesperrt · Community-Sperrliste, {len(sperre) if sperre else 0} Domains, {quelle}; "
                     f"eigene Blockliste, {len(eigene)} Einträge",
                     target, _schreibe(target, firmen_spalten, gesperrt)))
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
    """Gesperrter Eintrag, wenn E-Mail oder Website des Leads auf der Sperr- bzw. Blockliste steht."""
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


def _wert(row, key: str) -> str:
    """Column value as stripped string, '' if missing or NULL."""
    if key not in row.keys():
        return ""
    v = row[key]
    return "" if v is None else str(v).strip()


def externe_id(row) -> str:
    """Stable id per company: business_id, else place_id, else ds-<datensatz_id>."""
    for key in ("business_id", "place_id"):
        if _wert(row, key):
            return _wert(row, key)
    ds = _wert(row, "datensatz_id")
    return f"ds-{ds}" if ds else ""


def _impressum(row) -> dict:
    """Parsed imprint response (impressum_raw), {} if missing or invalid."""
    try:
        imp = json.loads(_wert(row, "impressum_raw") or "{}")
    except json.JSONDecodeError:
        return {}
    return imp if isinstance(imp, dict) else {}


def _impressum_url(row) -> str:
    url = str(_impressum(row).get("impressum_url") or "").strip()
    return url if url.lower().startswith(("http://", "https://")) else ""


def quelle_url(row) -> str:
    """Source of the record: imprint URL if known, else the job ad, else the Google Maps entry."""
    url = _impressum_url(row)
    if url:
        return url
    if _wert(row, "quelle") == "stellen" and _wert(row, "stelle_url"):
        return _wert(row, "stelle_url")
    pid = _wert(row, "place_id")
    return f"https://www.google.com/maps/place/?q=place_id:{pid}" if pid else ""


def quelle(row) -> str:
    """Human-readable source: the Maps search, plus the imprint when contact data came from it."""
    if _wert(row, "quelle") == "stellen":
        portal = _wert(row, "stelle_portal")
        text = f"Stellenanzeige „{_wert(row, 'job_title')}“" + (f" auf {portal}" if portal else "")
        return text + "; Kontaktdaten aus dem Impressum" if _impressum_url(row) else text
    keyword, stadt = _wert(row, "query_keyword"), _wert(row, "query_city")
    if not (keyword or stadt):
        return ""
    text = f"Google-Maps-Suche nach „{keyword}“ in {stadt}"
    return text + "; Kontaktdaten aus dem Impressum" if _impressum_url(row) else text


def erfasst_am(row) -> str:
    """Enrichment date YYYY-MM-DD (updated_at, fallback created_at)."""
    for key in ("updated_at", "created_at"):
        m = re.match(r"\d{4}-\d{2}-\d{2}", _wert(row, key))
        if m:
            return m.group(0)
    return ""


# Derived CSV columns, computed per row when the row has no such column
_ABGELEITET = {"externe_id": externe_id, "quelle_url": quelle_url, "erfasst_am": erfasst_am}

# "Street 1, 12345 City" (optionally "D-12345"); street = last segment before the postcode
_ADRESSE = re.compile(r"^(.+?),\s*(?:[A-Z]{1,2}-)?\d{4,5}\s+\S")


def _strasse(*adressen: str) -> str:
    for adresse in adressen:
        m = _ADRESSE.match(adresse or "")
        if m:
            return m.group(1).split(",")[-1].strip()
    return ""


def _handelsregister(row) -> str:
    """Register court and number from the imprint response, if present."""
    imp = _impressum(row)
    teile = (str(imp.get(k) or "").strip() for k in ("handelsregister_court", "handelsregister_number"))
    return " ".join(t for t in teile if t)


def lead_format_eintrag(row) -> dict[str, str]:
    """One lead (list 1 or 2) in the fixed lead format for landing pages."""
    typ = _wert(row, "email_final_type")
    eintrag = {feld: "" for feld in LEAD_FORMAT_FELDER}
    eintrag.update({
        "externe_id": externe_id(row),
        "firma": _wert(row, "firmenname_final") or _wert(row, "firmenname"),
        "domain": host_of(_wert(row, "website_final")),
        "website": _wert(row, "website_final"),
        "strasse": _strasse(_wert(row, "adresse_impressum"), _wert(row, "address")),
        "plz": _wert(row, "zip"),
        "ort": _wert(row, "query_city") or _wert(row, "stelle_ort"),
        "land": _wert(row, "query_country"),
        "telefon": _wert(row, "telefon_impressum") or _wert(row, "phone_imported"),
        "branche": _wert(row, "category"),
        "handelsregister": _handelsregister(row),
        "anrede": _wert(row, "anrede"),
        "vorname": _wert(row, "first_name"),
        "nachname": _wert(row, "last_name"),
        "position": "Geschäftsführung" if typ == "GF" else "",
        "email": _wert(row, "email_final"),
        "email_typ": {"GF": "persoenlich", "Info@": "funktion"}.get(typ, ""),
        "email_status": _wert(row, "email_final_status"),
        "linkedin_url": _wert(row, "linkedin_url"),
        "quelle": quelle(row),
        "quelle_url": quelle_url(row),
        "erfasst_am": erfasst_am(row),
        "personalisierung": _wert(row, "personalisierung"),
        "video_titel": _wert(row, "video_title"),
    })
    return eintrag


def _exportname() -> str:
    """Campaign name, else the database file name (without extension)."""
    return KAMPAGNE or CONFIG.db_path.stem


def mark_exported(conn: sqlite3.Connection) -> int:
    """Setzt `Bereits exportiert` — Gegenstück zur manuellen Clay-Checkbox."""
    from . import db

    with db.write(conn):
        cur = conn.execute("UPDATE anreicherung SET bereits_exportiert=1 WHERE ready_to_send=1")
    return cur.rowcount
