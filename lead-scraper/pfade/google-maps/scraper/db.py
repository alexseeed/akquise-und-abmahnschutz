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
    dedupe_status   TEXT DEFAULT 'kept',   -- kept | dropped_duplicate | dropped_excluded
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
    "datensaetze": {"attempts": "INTEGER NOT NULL DEFAULT 0", "maps_raw": "TEXT"},
    "anreicherung": {"attempts": "INTEGER NOT NULL DEFAULT 0", "pain_category": "TEXT",
                     "pain_beleg": "TEXT", "partnernetz": "INTEGER",
                     "site_links": "TEXT"},
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
    }
