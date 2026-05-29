#!/usr/bin/env python3
"""
store.py — SQLite dedup + audit store for GovCon opportunity discovery.

Every opportunity the pipeline evaluates is recorded here, keyed by SAM
notice id. That guarantees a contract is never processed (or written) twice
and that we never re-spend AI tokens on something already seen.

Dispositions:
  kept            — AI-enriched and kept; a doc was written
  review          — AI scored in [review_min, score_threshold); awaiting human verdict
  kept_pending    — passed Stage 1 + Stage 2 (combined_score >= keep threshold); awaiting AI enrichment
  pending_low     — passed Stage 1 + Stage 2 at lower confidence; visible on dashboard
  skipped_ai      — passed stages 1+2 but AI relevance below review_min
  skipped_stage1  — keyword/NAICS score below stage1_threshold
  skipped_stage2  — passed stage 1 but combined score below floor
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
            desc_score         INTEGER,
            combined_score     INTEGER,
            ai_score           INTEGER,
            disposition        TEXT NOT NULL,
            ai_generated       INTEGER NOT NULL DEFAULT 0,
            output_path        TEXT,
            first_seen         TEXT NOT NULL,
            human_verdict      TEXT,
            human_notes        TEXT,
            review_flagged     INTEGER NOT NULL DEFAULT 0
        )
    """)
    # Migrations: add columns to existing databases that predate them.
    for col, ddl in [
        ("solicitation_number", "TEXT"),
        ("human_verdict",       "TEXT"),
        ("human_notes",         "TEXT"),
        ("review_flagged",      "INTEGER NOT NULL DEFAULT 0"),
        ("desc_score",          "INTEGER"),
        ("combined_score",      "INTEGER"),
    ]:
        try:
            conn.execute(f"ALTER TABLE seen ADD COLUMN {col} {ddl}")
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
           ai_generated: bool, output_path: str | None,
           desc_score: int | None = None,
           combined_score: int | None = None) -> None:
    conn.execute("""
        INSERT OR REPLACE INTO seen
            (notice_id, title, posted_date, notice_type, naics, agency,
             ui_link, response_deadline, solicitation_number,
             stage1_score, desc_score, combined_score, ai_score, disposition,
             ai_generated, output_path, first_seen)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        rec["notice_id"], rec["title"], rec["posted_date"], rec["type"],
        rec["naics"], rec["agency"], rec["ui_link"], rec["response_deadline"],
        rec.get("solicitation_number") or None,
        stage1_score, desc_score, combined_score, ai_score, disposition,
        1 if ai_generated else 0, output_path,
        datetime.date.today().isoformat(),
    ))
    conn.commit()


def kept_opportunities(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    """All AI-enriched kept opportunities, newest-posted-first (for INDEX rebuilds)."""
    return conn.execute("""
        SELECT * FROM seen WHERE disposition = 'kept'
        ORDER BY posted_date DESC, first_seen DESC
    """).fetchall()


def get_pending_for_enrich(conn: sqlite3.Connection,
                            limit: int | None = None) -> list[sqlite3.Row]:
    """Return kept_pending records ordered by combined_score DESC for AI enrichment."""
    q = """
        SELECT * FROM seen
        WHERE disposition = 'kept_pending'
        ORDER BY combined_score DESC, first_seen ASC
    """
    if limit:
        q += f" LIMIT {int(limit)}"
    return conn.execute(q).fetchall()


def update_disposition(conn: sqlite3.Connection, notice_id: str,
                        disposition: str, ai_score: int | None,
                        ai_generated: bool, output_path: str | None) -> None:
    """Update an existing record's disposition after AI enrichment."""
    conn.execute("""
        UPDATE seen
        SET disposition=?, ai_score=?, ai_generated=?, output_path=?
        WHERE notice_id=?
    """, (disposition, ai_score, 1 if ai_generated else 0, output_path, notice_id))
    conn.commit()


def get_pending_display(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    """All displayable pending records (kept_pending + pending_low), newest first."""
    return conn.execute("""
        SELECT * FROM seen
        WHERE disposition IN ('kept_pending', 'pending_low')
        ORDER BY combined_score DESC, posted_date DESC
    """).fetchall()


def set_verdict(conn: sqlite3.Connection, notice_id: str,
                verdict: str | None, notes: str | None = None) -> None:
    """Record a human yes/no verdict on an opportunity."""
    conn.execute(
        "UPDATE seen SET human_verdict = ?, human_notes = ? WHERE notice_id = ?",
        (verdict, notes, notice_id),
    )
    conn.commit()


def get_review_queue(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    """Return unreviewed review-queue opps, newest-posted first."""
    return conn.execute("""
        SELECT * FROM seen
        WHERE review_flagged = 1 AND human_verdict IS NULL
        ORDER BY posted_date DESC, first_seen DESC
    """).fetchall()


def get_feedback_examples(conn: sqlite3.Connection,
                          limit: int = 10) -> list[dict]:
    """Return recent human verdicts for few-shot AI calibration.

    Returns up to `limit` rows balanced between yes/no verdicts.
    """
    half = limit // 2
    yes_rows = conn.execute("""
        SELECT title, agency, ai_score, naics, human_verdict, human_notes
        FROM seen WHERE human_verdict = 'yes'
        ORDER BY first_seen DESC LIMIT ?
    """, (half,)).fetchall()
    no_rows = conn.execute("""
        SELECT title, agency, ai_score, naics, human_verdict, human_notes
        FROM seen WHERE human_verdict = 'no'
        ORDER BY first_seen DESC LIMIT ?
    """, (half,)).fetchall()
    return [dict(r) for r in yes_rows] + [dict(r) for r in no_rows]


def disposition_counts(conn: sqlite3.Connection) -> dict:
    rows = conn.execute(
        "SELECT disposition, COUNT(*) AS n FROM seen GROUP BY disposition"
    ).fetchall()
    return {r["disposition"]: r["n"] for r in rows}
