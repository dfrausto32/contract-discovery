#!/usr/bin/env python3
"""
store.py — SQLite dedup + audit store for GovCon opportunity discovery.

Every opportunity the pipeline evaluates is recorded here, keyed by SAM
notice id. That guarantees a contract is never processed (or written) twice
and that we never re-spend AI tokens on something already seen.

Dispositions:
  kept            — passed both stages; a doc was written
  skipped_ai      — passed stage 1 but AI relevance below threshold
  skipped_stage1  — keyword/NAICS score below threshold
  excluded        — matched an exclude keyword
"""

import sqlite3
import datetime
from pathlib import Path


DB_PATH = Path(__file__).parent / "data" / "trex_seen.db"


def get_db(path: Path = DB_PATH) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS seen (
            notice_id          TEXT PRIMARY KEY,
            title              TEXT,
            posted_date        TEXT,
            notice_type        TEXT,
            naics              TEXT,
            agency             TEXT,
            ui_link            TEXT,
            response_deadline  TEXT,
            solicitation_number TEXT,
            stage1_score       INTEGER,
            ai_score           INTEGER,
            disposition        TEXT NOT NULL,
            ai_generated       INTEGER NOT NULL DEFAULT 0,
            output_path        TEXT,
            first_seen         TEXT NOT NULL
        )
    """)
    # Migration: add solicitation_number to existing databases that predate this column.
    try:
        conn.execute("ALTER TABLE seen ADD COLUMN solicitation_number TEXT")
    except Exception:
        pass  # column already exists
    conn.commit()


def is_seen(conn: sqlite3.Connection, notice_id: str) -> bool:
    """Return True if this exact notice_id has already been evaluated."""
    return conn.execute(
        "SELECT 1 FROM seen WHERE notice_id = ?", (notice_id,)
    ).fetchone() is not None


def get_by_solicitation_number(conn: sqlite3.Connection,
                                sol_num: str) -> sqlite3.Row | None:
    """Return the most recent record for a solicitation number, or None.

    Used to detect amendments: a new notice_id arriving with a sol# we've
    already evaluated. Returns the full row so the caller can check its
    disposition and output_path before deciding how to handle the amendment.
    """
    return conn.execute(
        "SELECT * FROM seen WHERE solicitation_number = ? ORDER BY first_seen DESC LIMIT 1",
        (sol_num,)
    ).fetchone()


def delete_record(conn: sqlite3.Connection, notice_id: str) -> None:
    """Remove a record by notice_id so an amendment can replace it cleanly."""
    conn.execute("DELETE FROM seen WHERE notice_id = ?", (notice_id,))
    conn.commit()


def record(conn: sqlite3.Connection, rec: dict, disposition: str,
           stage1_score: int, ai_score: int | None,
           ai_generated: bool, output_path: str | None) -> None:
    conn.execute("""
        INSERT OR REPLACE INTO seen
            (notice_id, title, posted_date, notice_type, naics, agency,
             ui_link, response_deadline, solicitation_number,
             stage1_score, ai_score, disposition,
             ai_generated, output_path, first_seen)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        rec["notice_id"], rec["title"], rec["posted_date"], rec["type"],
        rec["naics"], rec["agency"], rec["ui_link"], rec["response_deadline"],
        rec.get("solicitation_number") or None,
        stage1_score, ai_score, disposition,
        1 if ai_generated else 0, output_path,
        datetime.date.today().isoformat(),
    ))
    conn.commit()


def kept_opportunities(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    """All kept opportunities, newest-posted-first (for INDEX rebuilds)."""
    return conn.execute("""
        SELECT * FROM seen WHERE disposition = 'kept'
        ORDER BY posted_date DESC, first_seen DESC
    """).fetchall()


def disposition_counts(conn: sqlite3.Connection) -> dict:
    rows = conn.execute(
        "SELECT disposition, COUNT(*) AS n FROM seen GROUP BY disposition"
    ).fetchall()
    return {r["disposition"]: r["n"] for r in rows}
