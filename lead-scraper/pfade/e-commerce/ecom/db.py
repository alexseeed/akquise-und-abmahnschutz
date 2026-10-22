"""SQLite-Schicht — ersetzt die zwei Clay-Tabellen und macht Läufe fortsetzbar.

`shops`        = Clay-Tabelle Import
`anreicherung` = Clay-Tabelle ANREICHERUNG
`meta`         = Anforderungen des Auftrags: Shop-Profil, Personalisierung, Mailtext (nicht in Clay)
"""
from __future__ import annotations

import json
import sqlite3
import threading
from contextlib import contextmanager
from typing import Any, Iterable

from .config import CONFIG

_LOCK = threading.Lock()

SCHEMA = """
-- Stufe 1: Shop-Liste prüfen  (entspricht Clay Import)
CREATE TABLE IF NOT EXISTS shops (
    id               INTEGER PRIMARY KEY,
    import_key       TEXT NOT NULL UNIQUE,  -- Website bzw. Firmenname normalisiert: gleiche Zeile nicht doppelt importieren
    firmenname       TEXT,
    website          TEXT,
    quelle           TEXT,                  -- Dateiname der Import-CSV
    company_domain   TEXT,                  -- Clay `Company Domain`?.response (KI-Agent)
    website_final    TEXT,                  -- Clay `website [Final]`
    webscraper_raw   TEXT,                  -- Clay `SKAEL WEBSCRAPER`
    bodytext         TEXT,
    icp_raw          TEXT,                  -- Clay `ICP ONLINE SHOP`
    is_active_shop   INTEGER,
    webtraffic_raw   TEXT,                  -- Clay `SKAEL WEBTRAFFIC`
    avr_traffic      INTEGER,               -- Clay `AVR TRAFFIC`
    max_traffic_3mo  INTEGER,               -- Clay `H T 3 MO`
    send             INTEGER,               -- Clay `SEND`
    uebergeben       INTEGER DEFAULT 0,     -- Clay `Send table data`
    profil_raw       TEXT,                  -- Shop-Profil des Kunden (nicht in Clay), Teil von Stufe 1c
    passt_profil     INTEGER,               -- 1 passt / 0 passt nicht / NULL nicht geprüft
    profil_confidence REAL,
    profil_grund     TEXT,
    attempts         INTEGER NOT NULL DEFAULT 0,
    error            TEXT,
    created_at       TEXT DEFAULT (datetime('now'))
);

-- Stufe 2: angereicherter Lead  (entspricht Clay ANREICHERUNG)
CREATE TABLE IF NOT EXISTS anreicherung (
    id                    INTEGER PRIMARY KEY,
    shop_id               INTEGER NOT NULL UNIQUE REFERENCES shops(id),
    firmenname            TEXT,
    website               TEXT,
    company_domain        TEXT,
    website_final         TEXT,
    avr_traffic           INTEGER,
    max_traffic_3mo       INTEGER,

    impressum_raw         TEXT,
    firmenname_impressum  TEXT,
    firmenname_final      TEXT,
    adresse_impressum     TEXT,
    telefon_impressum     TEXT,
    email_impressum       TEXT,
    email_domain          TEXT,
    dedupe_status         TEXT DEFAULT 'kept',   -- kept | dropped_duplicate  (Clay-Dedupe auf Email [Domain])
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
    personalisierung      TEXT,
    video_title_input     TEXT,
    video_title           TEXT,
    video_company_name    TEXT,

    ready_to_send         INTEGER DEFAULT 0,
    bereits_exportiert    INTEGER DEFAULT 0,
    stage                 TEXT NOT NULL DEFAULT 'new',
    attempts              INTEGER NOT NULL DEFAULT 0,
    error                 TEXT,
    created_at            TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_an_ready ON anreicherung(ready_to_send);
CREATE INDEX IF NOT EXISTS idx_an_domain ON anreicherung(email_domain);

-- Anforderungen des Auftrags (Shop-Profil, Personalisierung, Mailtext), gesetzt per CLI
CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT
);
"""

# Spalten, die in älteren Datenbanken nachgerüstet werden
_MIGRATIONS = {
    "shops": {"profil_raw": "TEXT", "passt_profil": "INTEGER", "profil_confidence": "REAL",
              "profil_grund": "TEXT"},
}

# Schlüssel in `meta`. Fehlt `prompt_shopprofil` ganz, ist noch nicht entschieden;
# "" heißt: bewusst ohne Shop-Profil (jeder aktive Shop zählt).
META_SHOPPROFIL = "prompt_shopprofil"
META_PERSONALISIERUNG = "prompt_personalisierung"
META_MAILTEXT = "mailtext"


def connect() -> sqlite3.Connection:
    CONFIG.db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(CONFIG.db_path, timeout=60, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        # WAL beschleunigt parallele Läufe, geht aber nicht auf jedem Netzlaufwerk
        conn.execute("PRAGMA journal_mode=WAL")
    except sqlite3.OperationalError:
        pass
    return conn


def init(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    for table, columns in _MIGRATIONS.items():
        existing = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})")}
        for name, ddl in columns.items():
            if name not in existing:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}")
    # Import-Schlüssel ohne „www.“ (seit 2026-10-09): ältere Schlüssel angleichen, damit ein erneuter
    # Import derselben Liste nichts doppelt anlegt. Gibt es den Schlüssel ohne „www.“ schon, bleibt alles.
    conn.execute("UPDATE shops SET import_key = substr(import_key, 5) WHERE import_key LIKE 'www.%' "
                 "AND substr(import_key, 5) NOT IN (SELECT import_key FROM shops)")
    conn.commit()


def note_failure(conn: sqlite3.Connection, table: str, row_id: int, message: str) -> None:
    """Fehler protokollieren, ohne das Idempotenz-Feld zu belegen.

    Die Zeile wird beim nächsten Lauf erneut versucht, bis `attempts` das Limit
    erreicht. Clay verhält sich genauso: eine fehlgeschlagene Zelle bleibt leer.
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


def insert_ignore(conn: sqlite3.Connection, table: str, data: dict) -> bool:
    """Legt eine Zeile an, wenn der eindeutige Schlüssel noch fehlt. True = neu angelegt."""
    cols = list(data.keys())
    sql = (f"INSERT INTO {table} ({','.join(cols)}) VALUES ({','.join('?' for _ in cols)}) "
           "ON CONFLICT DO NOTHING")
    with write(conn):
        cur = conn.execute(sql, [data[c] for c in cols])
    return cur.rowcount > 0


def update(conn: sqlite3.Connection, table: str, row_id: int, data: dict) -> None:
    if not data:
        return
    sets = ",".join(f"{c}=?" for c in data)
    with write(conn):
        conn.execute(f"UPDATE {table} SET {sets} WHERE id=?", [*data.values(), row_id])


def set_meta(conn: sqlite3.Connection, key: str, value: Any) -> None:
    payload = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    with write(conn):
        conn.execute(
            "INSERT INTO meta(key, value) VALUES(?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, payload),
        )


def get_meta(conn: sqlite3.Connection, key: str, default: Any = None) -> Any:
    row = conn.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
    return row["value"] if row else default


def dumps(value: Any) -> str | None:
    return json.dumps(value, ensure_ascii=False) if value is not None else None


def stats(conn: sqlite3.Connection) -> dict[str, int]:
    def one(sql: str) -> int:
        return conn.execute(sql).fetchone()[0]

    return {
        "shops": one("SELECT COUNT(*) FROM shops"),
        # vor Stufe 1a zählt die Website aus der Liste, danach `website_final` ("" = auch per Suche keine)
        "mit_website": one("SELECT COUNT(*) FROM shops WHERE COALESCE(website_final, website, '') <> ''"),
        "gescrapt": one("SELECT COUNT(*) FROM shops WHERE COALESCE(bodytext,'') <> ''"),
        "aktiver_shop": one("SELECT COUNT(*) FROM shops WHERE is_active_shop=1"),
        "kein_shop": one("SELECT COUNT(*) FROM shops WHERE is_active_shop=0"),
        "mit_traffic": one("SELECT COUNT(*) FROM shops WHERE COALESCE(avr_traffic,0) > 0"),
        "profil_passt": one("SELECT COUNT(*) FROM shops WHERE passt_profil=1"),
        "profil_passt_nicht": one("SELECT COUNT(*) FROM shops WHERE passt_profil=0"),
        "send": one("SELECT COUNT(*) FROM shops WHERE send=1"),
        "uebergeben": one("SELECT COUNT(*) FROM shops WHERE uebergeben=1"),
        "anreicherung": one("SELECT COUNT(*) FROM anreicherung"),
        "duplikate": one("SELECT COUNT(*) FROM anreicherung WHERE dedupe_status='dropped_duplicate'"),
        "mit_email": one("SELECT COUNT(*) FROM anreicherung WHERE COALESCE(email_final,'') <> '' "
                         "AND dedupe_status='kept'"),
        "ready_to_send": one("SELECT COUNT(*) FROM anreicherung WHERE ready_to_send=1"),
    }
