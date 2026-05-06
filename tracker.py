#!/usr/bin/env python3
"""
tracker.py — Log and manage construction industry contacts in local SQLite.

This is the core data layer. Every field here maps to something you'll use
when prioritizing outreach. Read through the schema before logging real people.

Fields:
  name           — Full name (required)
  title          — Job title exactly as shown on LinkedIn
  company        — Company name
  company_size   — Employee headcount (integer; use your best estimate)
  subtype        — Construction subtype: GC, Subcontractor, Electrical, etc.
  location       — City, State
  linkedin_url   — Full LinkedIn profile URL
  discovery_date — Auto-set to today
  status         — Pipeline stage (see VALID_STATUSES below)
  notes          — Free text; one sentence is enough
  relevance      — Auto-calculated score (0-100); can be manually overridden
"""

import sqlite3
import datetime
import yaml
import click
from pathlib import Path


DB_PATH = Path(__file__).parent / "data" / "contacts.db"
CONFIG_PATH = Path(__file__).parent / "config.yaml"

VALID_STATUSES = [
    "discovered",    # Found on LinkedIn, not yet contacted
    "queued",        # Chosen for this week's outreach
    "contacted",     # Message sent
    "responded",     # They replied
    "interviewed",   # Had a conversation / discovery call
    "not_relevant",  # Disqualified — wrong fit
    "no_response",   # Contacted but no reply after follow-up window
]

VALID_SUBTYPES = [
    "General Contractor",
    "Subcontractor",
    "Electrical",
    "Plumbing",
    "HVAC",
    "Concrete",
    "Framing",
    "Roofing",
    "Excavation",
    "Other",
]


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        return {}
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def get_db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they don't exist. Safe to call repeatedly."""
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS contacts (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT NOT NULL,
            title           TEXT,
            company         TEXT,
            company_size    INTEGER,
            subtype         TEXT,
            location        TEXT,
            linkedin_url    TEXT UNIQUE,
            discovery_date  TEXT NOT NULL,
            status          TEXT NOT NULL DEFAULT 'discovered',
            notes           TEXT,
            relevance       INTEGER NOT NULL DEFAULT 0,
            created_at      TEXT NOT NULL,
            updated_at      TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def calculate_relevance(name: str, title: str, company_size: int,
                         subtype: str, location: str, config: dict) -> int:
    """
    Score a contact 0–100 based on config-driven criteria.
    Higher = contact sooner.

    Breakdown:
      Title tier:        0–35 pts
      Company size:      0–30 pts
      Subtype weight:    0–20 pts
      Location match:    0–15 pts
    """
    score = 0

    # --- Title scoring (35 pts max) ---
    title_lower = (title or "").lower()
    owner_titles = [t.lower() for t in config.get("titles", {}).get("owner_tier", [])]
    operator_titles = [t.lower() for t in config.get("titles", {}).get("operator_tier", [])]
    manager_titles = [t.lower() for t in config.get("titles", {}).get("manager_tier", [])]

    if any(t in title_lower for t in owner_titles):
        score += 35
    elif any(t in title_lower for t in operator_titles):
        score += 22
    elif any(t in title_lower for t in manager_titles):
        score += 12

    # --- Company size scoring (30 pts max) ---
    if company_size:
        sweet_min = config.get("company_size", {}).get("sweet_spot_min", 5)
        sweet_max = config.get("company_size", {}).get("sweet_spot_max", 50)
        acc_min = config.get("company_size", {}).get("acceptable_min", 2)
        acc_max = config.get("company_size", {}).get("acceptable_max", 200)

        if sweet_min <= company_size <= sweet_max:
            score += 30
        elif acc_min <= company_size < sweet_min:
            score += 15  # Very small — might not have budget
        elif sweet_max < company_size <= acc_max:
            score += 18  # Larger but still relevant
        else:
            score += 5   # Outside acceptable range

    # --- Subtype scoring (20 pts max, normalized from config weight) ---
    if subtype:
        subtypes_config = config.get("construction_subtypes", [])
        for st in subtypes_config:
            if st["name"].lower() == subtype.lower():
                # Weights in config are 4–10; normalize to 0–20
                raw_weight = st.get("weight", 5)
                score += int((raw_weight / 10) * 20)
                break

    # --- Location scoring (15 pts max) ---
    if location and config.get("geography", {}).get("local_boost", False):
        primary = config.get("geography", {}).get("primary", "").lower()
        additional = [l.lower() for l in config.get("geography", {}).get("additional", [])]
        location_lower = location.lower()

        # Check if any word from primary location appears in contact location
        primary_words = set(primary.replace(",", "").split())
        contact_words = set(location_lower.replace(",", "").split())
        if primary_words & contact_words:
            score += 15
        elif any(
            set(loc.replace(",", "").split()) & contact_words
            for loc in additional
        ):
            score += 8

    return min(score, 100)


def format_contact_row(row: sqlite3.Row) -> str:
    """Format a single contact for terminal display."""
    status_icons = {
        "discovered": "○",
        "queued": "◎",
        "contacted": "→",
        "responded": "↩",
        "interviewed": "✓",
        "not_relevant": "✗",
        "no_response": "–",
    }
    icon = status_icons.get(row["status"], "?")
    size_str = f"{row['company_size']}e" if row["company_size"] else "?e"
    return (
        f"  [{row['id']:>3}] {icon} {row['name']:<25} | "
        f"{(row['title'] or ''):<30} | "
        f"{(row['company'] or ''):<25} | "
        f"{size_str:<5} | "
        f"Score:{row['relevance']:>3} | "
        f"{row['status']}"
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

@click.group()
def cli():
    """Contact tracker — log and manage your construction discovery pipeline."""
    init_db()


@cli.command("add")
@click.option("--name", prompt="Full name", help="Contact's full name.")
@click.option("--title", prompt="Job title", default="", help="LinkedIn title.")
@click.option("--company", prompt="Company name", default="", help="Company.")
@click.option("--company-size", prompt="Company size (employees, 0 if unknown)",
              type=int, default=0)
@click.option("--subtype", prompt=f"Construction subtype {VALID_SUBTYPES}",
              default="General Contractor", help="Type of construction company.")
@click.option("--location", prompt="Location (City, State)", default="",
              help="Contact's location.")
@click.option("--linkedin-url", prompt="LinkedIn URL", default="",
              help="Full profile URL.")
@click.option("--notes", prompt="Notes (optional)", default="",
              help="One-line note.")
@click.option("--relevance-override", default=None, type=int,
              help="Manually set relevance 0-100 (skips auto-scoring).")
def add_contact(name, title, company, company_size, subtype, location,
                linkedin_url, notes, relevance_override):
    """Log a new contact discovered on LinkedIn."""
    config = load_config()

    # Validate subtype
    if subtype not in VALID_SUBTYPES:
        click.echo(f"Warning: '{subtype}' not in known subtypes. Saving anyway.")

    company_size_val = company_size if company_size > 0 else None

    if relevance_override is not None:
        relevance = max(0, min(100, relevance_override))
    else:
        relevance = calculate_relevance(
            name, title, company_size_val or 0, subtype, location, config
        )

    now = datetime.datetime.utcnow().isoformat()
    today = datetime.date.today().isoformat()

    try:
        conn = get_db()
        conn.execute("""
            INSERT INTO contacts
                (name, title, company, company_size, subtype, location,
                 linkedin_url, discovery_date, status, notes, relevance,
                 created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            name, title or None, company or None,
            company_size_val, subtype or None, location or None,
            linkedin_url or None, today, "discovered",
            notes or None, relevance, now, now,
        ))
        conn.commit()
        contact_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.close()

        click.echo(f"\n  Added: {name} (ID: {contact_id}) — Relevance score: {relevance}/100")
        click.echo(f"  Run 'python planner.py week' to see updated weekly plan.\n")

    except sqlite3.IntegrityError:
        click.echo(f"\n  Error: A contact with that LinkedIn URL already exists.\n", err=True)


@cli.command("update")
@click.argument("contact_id", type=int)
@click.option("--status", type=click.Choice(VALID_STATUSES), default=None,
              help="Update pipeline status.")
@click.option("--notes", default=None, help="Append or replace notes.")
@click.option("--relevance", default=None, type=int, help="Override relevance score.")
@click.option("--append-notes", is_flag=True, default=False,
              help="Append to existing notes instead of replacing.")
def update_contact(contact_id, status, notes, relevance, append_notes):
    """Update a contact's status, notes, or relevance score by ID."""
    conn = get_db()
    row = conn.execute("SELECT * FROM contacts WHERE id = ?", (contact_id,)).fetchone()
    if not row:
        click.echo(f"  No contact found with ID {contact_id}.", err=True)
        conn.close()
        return

    updates = {}
    if status:
        updates["status"] = status
    if notes:
        if append_notes and row["notes"]:
            updates["notes"] = f"{row['notes']} | {notes}"
        else:
            updates["notes"] = notes
    if relevance is not None:
        updates["relevance"] = max(0, min(100, relevance))

    if not updates:
        click.echo("  Nothing to update. Use --status, --notes, or --relevance.")
        conn.close()
        return

    updates["updated_at"] = datetime.datetime.utcnow().isoformat()
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    conn.execute(
        f"UPDATE contacts SET {set_clause} WHERE id = ?",
        (*updates.values(), contact_id),
    )
    conn.commit()
    conn.close()
    click.echo(f"\n  Updated contact {contact_id}: {dict(updates)}\n")


@cli.command("list")
@click.option("--status", type=click.Choice(VALID_STATUSES + ["all"]),
              default="all", help="Filter by status.")
@click.option("--limit", default=50, help="Max contacts to show.")
@click.option("--sort", type=click.Choice(["relevance", "date", "status"]),
              default="relevance")
def list_contacts(status, limit, sort):
    """List contacts with optional status filter."""
    conn = get_db()
    order = {
        "relevance": "relevance DESC, discovery_date DESC",
        "date":      "discovery_date DESC",
        "status":    "status ASC, relevance DESC",
    }[sort]

    if status == "all":
        rows = conn.execute(
            f"SELECT * FROM contacts ORDER BY {order} LIMIT ?", (limit,)
        ).fetchall()
    else:
        rows = conn.execute(
            f"SELECT * FROM contacts WHERE status = ? ORDER BY {order} LIMIT ?",
            (status, limit),
        ).fetchall()
    conn.close()

    if not rows:
        click.echo(f"\n  No contacts found (status={status}).\n")
        return

    click.echo(f"\n{'='*110}")
    click.echo(f"  CONTACTS — {len(rows)} shown, sorted by {sort}")
    click.echo(f"{'='*110}")
    click.echo(
        f"  {'ID':>3}   {'Name':<25}   {'Title':<30}   "
        f"{'Company':<25}   {'Size':<5}   {'Score':>5}   Status"
    )
    click.echo(f"  {'-'*100}")
    for row in rows:
        click.echo(format_contact_row(row))
    click.echo()


@cli.command("show")
@click.argument("contact_id", type=int)
def show_contact(contact_id):
    """Show full details for a single contact."""
    conn = get_db()
    row = conn.execute("SELECT * FROM contacts WHERE id = ?", (contact_id,)).fetchone()
    conn.close()

    if not row:
        click.echo(f"  No contact found with ID {contact_id}.", err=True)
        return

    click.echo(f"\n{'='*60}")
    click.echo(f"  Contact #{row['id']}")
    click.echo(f"{'='*60}")
    for key in row.keys():
        click.echo(f"  {key:<16}: {row[key]}")
    click.echo()


@cli.command("stats")
def show_stats():
    """Show pipeline summary statistics."""
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) FROM contacts").fetchone()[0]
    if total == 0:
        click.echo("\n  No contacts logged yet. Run 'python tracker.py add' to start.\n")
        conn.close()
        return

    avg_score = conn.execute("SELECT AVG(relevance) FROM contacts").fetchone()[0]
    by_status = conn.execute(
        "SELECT status, COUNT(*) as n FROM contacts GROUP BY status ORDER BY n DESC"
    ).fetchall()
    by_subtype = conn.execute(
        "SELECT subtype, COUNT(*) as n FROM contacts GROUP BY subtype ORDER BY n DESC"
    ).fetchall()

    conn.close()

    click.echo(f"\n{'='*50}")
    click.echo(f"  PIPELINE STATS")
    click.echo(f"{'='*50}")
    click.echo(f"  Total contacts : {total}")
    click.echo(f"  Avg relevance  : {avg_score:.1f}/100")
    click.echo(f"\n  By status:")
    for row in by_status:
        click.echo(f"    {row['status']:<15}: {row['n']}")
    click.echo(f"\n  By subtype:")
    for row in by_subtype:
        click.echo(f"    {(row['subtype'] or 'Unknown'):<25}: {row['n']}")
    click.echo()


if __name__ == "__main__":
    cli()
