"""SQLite-Schicht — ersetzt die vier Clay-Tabellen und macht Läufe fortsetzbar."""
from __future__ import annotations

import json
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable

from .config import CONFIG

_LOCK = threading.Lock()

SCHEMA = """
-- Stufe 1: Keyword × Land  (entspricht Clay EINGABE)
CREATE TABLE IF NOT EXISTS eingabe (
    id             INTEGER PRIMARY KEY,
    keyword        TEXT NOT NULL,
    country_code   TEXT NOT NULL,
    min_population INTEGER NOT NULL DEFAULT 1,
    cities_total   INTEGER,
    cities_fetched INTEGER,
    status         TEXT NOT NULL DEFAULT 'pending',
    error          TEXT,
    created_at     TEXT DEFAULT (datetime('now')),
    UNIQUE (keyword, country_code, min_population)
);

-- Stufe 2: Stadt × Keyword  (entspricht Clay VERARBEITUNG)
CREATE TABLE IF NOT EXISTS verarbeitung (
    id            INTEGER PRIMARY KEY,
    eingabe_id    INTEGER NOT NULL REFERENCES eingabe(id),
    input_keyword TEXT NOT NULL,
    input_city    TEXT,
    input_country TEXT,
    population    INTEGER,
    query         TEXT NOT NULL,
    items_total   INTEGER,
    status        TEXT NOT NULL DEFAULT 'pending',
    attempts      INTEGER NOT NULL DEFAULT 0,
    error         TEXT,
    created_at    TEXT DEFAULT (datetime('now')),
    UNIQUE (eingabe_id, query)
);

-- Stufe 3: Firma  (entspricht Clay DATENSÄTZE)
CREATE TABLE IF NOT EXISTS datensaetze (
    id              INTEGER PRIMARY KEY,
    verarbeitung_id INTEGER REFERENCES verarbeitung(id),
    business_id     TEXT,
    place_id        TEXT,
    firmenname      TEXT,
    website         TEXT,
    address         TEXT,
    zip             TEXT,
    category        TEXT,
    phone           TEXT,
    phone_export    TEXT,
    rating          REAL,
    review_count    INTEGER,
    query           TEXT,
    query_keyword   TEXT,
    query_city      TEXT,
    query_country   TEXT,
    maps_raw        TEXT,          -- vollstaendige Maps-Antwort je Firma
    domain_url      TEXT,          -- KI-Fallback (Clay: Domain URL)
    website_final   TEXT,
    dedupe_key      TEXT,
    dedupe_status   TEXT DEFAULT 'kept',   -- kept | dropped_duplicate | dropped_excluded | dropped_blocked
    icp_raw         TEXT,          -- JSON der icp_checker-Antwort
    is_icp          INTEGER,
    icp_confidence  REAL,
    icp_reason      TEXT,
    icp_label       TEXT,
    status          TEXT NOT NULL DEFAULT 'new',
    attempts        INTEGER NOT NULL DEFAULT 0,
    error           TEXT,
    created_at      TEXT DEFAULT (datetime('now')),
    UNIQUE (business_id)
);
CREATE INDEX IF NOT EXISTS idx_ds_dedupe ON datensaetze(dedupe_key);
CREATE INDEX IF NOT EXISTS idx_ds_status ON datensaetze(status);

-- Stufe 4: angereicherter Lead  (entspricht Clay ANREICHERUNG)
CREATE TABLE IF NOT EXISTS anreicherung (
    id                    INTEGER PRIMARY KEY,
    datensatz_id          INTEGER NOT NULL UNIQUE REFERENCES datensaetze(id),
    business_id           TEXT,
    place_id              TEXT,
    firmenname            TEXT,
    website               TEXT,
    company_domain        TEXT,
    website_final         TEXT,
    address               TEXT,
    zip                   TEXT,
    category              TEXT,
    phone_imported        TEXT,
    rating                REAL,
    review_count          INTEGER,
    query                 TEXT,
    query_keyword         TEXT,
    query_city            TEXT,
    query_country         TEXT,

    impressum_raw         TEXT,
    firmenname_impressum  TEXT,
    firmenname_final      TEXT,
    adresse_impressum     TEXT,
    telefon_impressum     TEXT,
    email_impressum       TEXT,
    email_domain          TEXT,
    kontaktperson         TEXT,
    kontaktperson_sauber  TEXT,
    launch_campaign       INTEGER,

    mailfinder_raw        TEXT,
    findymail_raw         TEXT,
    verify_gf_raw         TEXT,
    verify_info_raw       TEXT,
    email_gf              TEXT,
    email_gf_status       TEXT,
    email_source_gf       TEXT,
    email_info            TEXT,
    email_info_status     TEXT,
    email_final           TEXT,
    email_final_type      TEXT,
    email_final_status    TEXT,

    first_name            TEXT,
    last_name             TEXT,
    anrede                TEXT,
    anrede_confidence     INTEGER,
    formal                TEXT,
    ansprache_formal      TEXT,
    ansprache_normal      TEXT,
    ansprache_normal_gt   TEXT,
    ansprache_persoenlich TEXT,

    webscraper_raw        TEXT,
    bodytext              TEXT,
    site_links            TEXT,
    personalisierung      TEXT,
    pain_category         TEXT,
    pain_beleg            TEXT,
    partnernetz           INTEGER,
    video_title_input     TEXT,
    video_title           TEXT,
    video_company_name    TEXT,

    linkedin_url          TEXT,
    linkedin_confidence   REAL,

    ready_to_send         INTEGER DEFAULT 0,
    bereits_exportiert    INTEGER DEFAULT 0,
    stage                 TEXT NOT NULL DEFAULT 'new',
    attempts              INTEGER NOT NULL DEFAULT 0,
    error                 TEXT,
    created_at            TEXT DEFAULT (datetime('now')),
    updated_at            TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_an_stage ON anreicherung(stage);
CREATE INDEX IF NOT EXISTS idx_an_ready ON anreicherung(ready_to_send);

-- Stellensuche: eine Zeile je Portal × Suchbegriff × Ort (Stufe 1j)
CREATE TABLE IF NOT EXISTS stellen_suche (
    id            INTEGER PRIMARY KEY,
    portal        TEXT NOT NULL,
    suchbegriff   TEXT NOT NULL,
    ort           TEXT NOT NULL DEFAULT '',
    land          TEXT NOT NULL DEFAULT 'DE',
    seiten        INTEGER NOT NULL DEFAULT 0,   -- zuletzt abgerufene Seite
    treffer       INTEGER NOT NULL DEFAULT 0,
    weiter        INTEGER,                      -- 1 = Portal meldet weitere Seiten
    cursor        TEXT,                         -- Blätter-Code (Indeed) für die nächste Seite
    status        TEXT NOT NULL DEFAULT 'pending',
    attempts      INTEGER NOT NULL DEFAULT 0,
    error         TEXT,
    created_at    TEXT DEFAULT (datetime('now')),
    UNIQUE (portal, suchbegriff, ort, land)
);

-- Stellensuche: eine Zeile je Stellenanzeige (Stufe 1j), Firma in datensatz_id (Stufe 1k)
CREATE TABLE IF NOT EXISTS stellen (
    id               INTEGER PRIMARY KEY,
    suche_id         INTEGER REFERENCES stellen_suche(id),
    portal           TEXT NOT NULL,
    portal_id        TEXT NOT NULL,
    suchbegriff      TEXT,
    titel            TEXT,
    firma            TEXT,
    ort              TEXT,
    plz              TEXT,
    land             TEXT,
    veroeffentlicht  TEXT,          -- YYYY-MM-DD
    url              TEXT,          -- Anzeige auf dem Portal
    bewerben_url     TEXT,          -- Bewerbungslink (oft auf der Firmen-Website)
    website          TEXT,          -- Firmen-Website laut Portal, sonst leer
    gehalt           TEXT,
    beschreibung     TEXT,          -- bereinigt: ohne Kontaktblock, E-Mail, Telefon
    ausschluss       TEXT,          -- NULL = übernommen, sonst Grund
    datensatz_id     INTEGER REFERENCES datensaetze(id),
    raw              TEXT,
    created_at       TEXT DEFAULT (datetime('now')),
    UNIQUE (portal, portal_id)
);
CREATE INDEX IF NOT EXISTS idx_stellen_ds ON stellen(datensatz_id);

-- Kostenzähler: echte Skael-Credits je Endpunkt (credits_cost der fertigen Aufträge)
CREATE TABLE IF NOT EXISTS kosten (
    endpoint  TEXT PRIMARY KEY,
    aufrufe   INTEGER NOT NULL DEFAULT 0,
    credits   REAL NOT NULL DEFAULT 0
);

-- Lauf-Metadaten (ICP-Prompt, Keywords, Parameter)
CREATE TABLE IF NOT EXISTS run_meta (
    key   TEXT PRIMARY KEY,
    value TEXT
);
"""


def connect() -> sqlite3.Connection:
    CONFIG.db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(CONFIG.db_path, timeout=60, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        # WAL beschleunigt parallele Läufe deutlich, funktioniert aber nicht auf
        # jedem Netz-/FUSE-Laufwerk. Fällt still auf den Standardmodus zurück.
        conn.execute("PRAGMA journal_mode=WAL")
    except sqlite3.OperationalError:
        pass
    return conn


# Spalten, die in älteren Datenbanken nachgerüstet werden
_MIGRATIONS = {
    "verarbeitung": {"attempts": "INTEGER NOT NULL DEFAULT 0"},
    "datensaetze": {"attempts": "INTEGER NOT NULL DEFAULT 0", "maps_raw": "TEXT",
                    # Kampagnen-Arten Recruiting und Stellensuche
                    "quelle": "TEXT DEFAULT 'maps'",       # maps | stellen
                    "webscraper_raw": "TEXT",              # Startseite (Recruiting 3e), in 4e wiederverwendet
                    "stelle_raw": "TEXT", "stelle_vorhanden": "INTEGER", "stelle_url": "TEXT",
                    "job_title": "TEXT", "job_description": "TEXT", "job_bereich": "TEXT",
                    "stelle_portal": "TEXT", "stelle_datum": "TEXT", "stelle_ort": "TEXT",
                    "stelle_gehalt": "TEXT", "stellen_anzahl": "INTEGER", "stellen_portale": "TEXT",
                    "domain_raw": "TEXT",                  # Antwort von find_domain (Stellensuche 3a)
                    "domain_status": "TEXT",               # portal | verified | unverified | none
                    "groesse_raw": "TEXT",                 # Antwort des Größen-Checks (3g)
                    "groesse_kategorie": "TEXT"},          # mittelstand | konzern | oeffentlich_verband | it_wettbewerber | unbekannt
    "anreicherung": {"attempts": "INTEGER NOT NULL DEFAULT 0", "pain_category": "TEXT",
                     "pain_beleg": "TEXT", "partnernetz": "INTEGER",
                     "site_links": "TEXT",
                     "quelle": "TEXT", "strecke": "TEXT DEFAULT 'gmaps'",   # gmaps | rc | nk
                     "job_title": "TEXT", "job_description": "TEXT", "job_bereich": "TEXT",
                     "job_title_norm": "TEXT",
                     "stelle_url": "TEXT", "stelle_portal": "TEXT", "stelle_datum": "TEXT",
                     "stelle_ort": "TEXT", "stelle_gehalt": "TEXT", "stellen_anzahl": "INTEGER",
                     "stellen_portale": "TEXT"},
    "stellen_suche": {"weiter": "INTEGER", "cursor": "TEXT"},
}


def init(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    for table, columns in _MIGRATIONS.items():
        existing = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})")}
        for name, ddl in columns.items():
            if name not in existing:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}")
    conn.commit()


def note_failure(conn: sqlite3.Connection, table: str, row_id: int, message: str) -> None:
    """Fehler protokollieren, ohne das Idempotenz-Feld zu belegen.

    Damit wird die Zeile beim nächsten Lauf erneut versucht — bis `attempts`
    das Limit erreicht. Clay verhält sich genauso: eine fehlgeschlagene Zelle
    bleibt leer und wird nachgerechnet.
    """
    with write(conn):
        conn.execute(
            f"UPDATE {table} SET attempts = COALESCE(attempts, 0) + 1, error = ? WHERE id = ?",
            (message[:500], row_id),
        )


@contextmanager
def write(conn: sqlite3.Connection):
    """Serialisiert Schreibzugriffe — die Worker-Threads teilen sich eine Verbindung."""
    with _LOCK:
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise


def set_meta(conn: sqlite3.Connection, key: str, value: Any) -> None:
    payload = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    with write(conn):
        conn.execute(
            "INSERT INTO run_meta(key, value) VALUES(?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, payload),
        )


def get_meta(conn: sqlite3.Connection, key: str, default: Any = None) -> Any:
    row = conn.execute("SELECT value FROM run_meta WHERE key=?", (key,)).fetchone()
    return row["value"] if row else default


def pfad(conn: sqlite3.Connection) -> str:
    """Kampagnen-Art dieser Datenbank. Alte Datenbanken ohne Eintrag sind Google Maps."""
    return get_meta(conn, "pfad", "google-maps") or "google-maps"


def setze_pfad(conn: sqlite3.Connection, gewuenscht: str) -> None:
    """Legt die Kampagnen-Art fest. Eine Datenbank enthält nie zwei verschiedene Arten."""
    vorhanden = get_meta(conn, "pfad")
    hat_daten = conn.execute("SELECT COUNT(*) FROM datensaetze").fetchone()[0] \
        or conn.execute("SELECT COUNT(*) FROM eingabe").fetchone()[0] \
        or conn.execute("SELECT COUNT(*) FROM stellen_suche").fetchone()[0]
    # Ohne Eintrag, aber mit Daten: ein Google-Maps-Lauf aus der Zeit vor den Kampagnen-Arten
    bestehend = vorhanden or ("google-maps" if hat_daten else None)
    if hat_daten and bestehend != gewuenscht:
        raise SystemExit(
            f"Diese Kampagne enthält schon einen Lauf vom Typ „{bestehend}“.\n"
            f"Für „{gewuenscht}“ eine eigene Kampagne anlegen:  python3 -m scraper neue-kampagne <name>"
        )
    set_meta(conn, "pfad", gewuenscht)


def kosten_buchen(conn: sqlite3.Connection, endpoint: str, credits: float) -> None:
    """Kostenzähler: echte Skael-Credits eines fertigen Auftrags aufsummieren."""
    with write(conn):
        conn.execute(
            "INSERT INTO kosten(endpoint, aufrufe, credits) VALUES(?, 1, ?) "
            "ON CONFLICT(endpoint) DO UPDATE SET aufrufe = aufrufe + 1, credits = credits + excluded.credits",
            (endpoint, credits),
        )


def kosten_summe(conn: sqlite3.Connection) -> float:
    return float(conn.execute("SELECT COALESCE(SUM(credits), 0) FROM kosten").fetchone()[0])


def kosten(conn: sqlite3.Connection) -> list[tuple[str, int, float]]:
    return [(r[0], r[1], r[2]) for r in conn.execute(
        "SELECT endpoint, aufrufe, credits FROM kosten ORDER BY credits DESC")]


def upsert(conn: sqlite3.Connection, table: str, data: dict, conflict: Iterable[str]) -> int:
    cols = list(data.keys())
    placeholders = ",".join("?" for _ in cols)
    conflict_cols = ",".join(conflict)
    updates = ",".join(f"{c}=excluded.{c}" for c in cols if c not in conflict)
    sql = (
        f"INSERT INTO {table} ({','.join(cols)}) VALUES ({placeholders}) "
        f"ON CONFLICT({conflict_cols}) DO UPDATE SET {updates}"
        if updates
        else f"INSERT INTO {table} ({','.join(cols)}) VALUES ({placeholders}) "
             f"ON CONFLICT({conflict_cols}) DO NOTHING"
    )
    with write(conn):
        cur = conn.execute(sql, [data[c] for c in cols])
        if cur.lastrowid:
            return cur.lastrowid
    where = " AND ".join(f"{c}=?" for c in conflict)
    row = conn.execute(f"SELECT id FROM {table} WHERE {where}", [data[c] for c in conflict]).fetchone()
    return row["id"] if row else 0


def update(conn: sqlite3.Connection, table: str, row_id: int, data: dict) -> None:
    if not data:
        return
    sets = ",".join(f"{c}=?" for c in data)
    if table == "anreicherung" and "updated_at" not in data:
        # Enrichment date for the export column "Erfasst am" (Art. 14 GDPR)
        sets += ",updated_at=datetime('now')"
    with write(conn):
        conn.execute(f"UPDATE {table} SET {sets} WHERE id=?", [*data.values(), row_id])


def stats(conn: sqlite3.Connection) -> dict[str, Any]:
    def one(sql: str) -> int:
        return conn.execute(sql).fetchone()[0]

    return {
        "eingabe": one("SELECT COUNT(*) FROM eingabe"),
        "eingabe_done": one("SELECT COUNT(*) FROM eingabe WHERE status='done'"),
        "verarbeitung": one("SELECT COUNT(*) FROM verarbeitung"),
        "verarbeitung_done": one("SELECT COUNT(*) FROM verarbeitung WHERE status='done'"),
        "datensaetze": one("SELECT COUNT(*) FROM datensaetze"),
        "datensaetze_kept": one("SELECT COUNT(*) FROM datensaetze WHERE dedupe_status='kept'"),
        "icp_true": one("SELECT COUNT(*) FROM datensaetze WHERE is_icp=1"),
        "icp_false": one("SELECT COUNT(*) FROM datensaetze WHERE is_icp=0"),
        "anreicherung": one("SELECT COUNT(*) FROM anreicherung"),
        "mit_email": one("SELECT COUNT(*) FROM anreicherung WHERE email_final <> ''"),
        "ready_to_send": one("SELECT COUNT(*) FROM anreicherung WHERE ready_to_send=1"),
        # Recruiting
        "stelle_geprueft": one("SELECT COUNT(*) FROM datensaetze WHERE stelle_vorhanden IS NOT NULL "
                               "AND COALESCE(quelle,'maps')='maps'"),
        "stelle_ja": one("SELECT COUNT(*) FROM datensaetze WHERE stelle_vorhanden=1 AND is_icp=1 "
                         "AND COALESCE(quelle,'maps')='maps'"),
        "strecke_rc": one("SELECT COUNT(*) FROM anreicherung WHERE strecke='rc'"),
        "strecke_nk": one("SELECT COUNT(*) FROM anreicherung WHERE strecke='nk'"),
        # Stellensuche
        "suchen": one("SELECT COUNT(*) FROM stellen_suche"),
        "suchen_done": one("SELECT COUNT(*) FROM stellen_suche WHERE status='done'"),
        "suchen_seiten": one("SELECT COALESCE(SUM(seiten), 0) FROM stellen_suche"),
        "stellen": one("SELECT COUNT(*) FROM stellen"),
        "stellen_ok": one("SELECT COUNT(*) FROM stellen WHERE ausschluss IS NULL"),
        "stellen_ausschluss": {
            row[0]: row[1] for row in conn.execute(
                "SELECT ausschluss, COUNT(*) FROM stellen WHERE ausschluss IS NOT NULL "
                "GROUP BY ausschluss ORDER BY 2 DESC")
        },
        "firmen_mit_website": one("SELECT COUNT(*) FROM datensaetze WHERE dedupe_status='kept' "
                                  "AND COALESCE(website_final,'') <> ''"),
        "groesse_geprueft": one("SELECT COUNT(*) FROM datensaetze WHERE groesse_kategorie IS NOT NULL"),
        "groesse_raus": {
            row[0]: row[1] for row in conn.execute(
                "SELECT groesse_kategorie, COUNT(*) FROM datensaetze WHERE groesse_kategorie IN "
                "('konzern', 'oeffentlich_verband', 'it_wettbewerber') GROUP BY 1")
        },
        "kosten_credits": conn.execute("SELECT COALESCE(SUM(credits), 0) FROM kosten").fetchone()[0],
    }
