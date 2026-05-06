#!/usr/bin/env python3
"""
planner.py — Generate a weekly action plan of exactly 8 prioritized contacts.

Logic:
  1. Pull all contacts not yet reached (status: discovered or queued)
  2. Sort by relevance score DESC, then by discovery_date ASC (older first)
  3. Take top 8
  4. Mark them as 'queued' so they don't appear next week unless updated
  5. Print a clean, actionable plan to the terminal

Future: --discord flag sends the plan to a Discord webhook.
"""

import sqlite3
import datetime
import os
import json
import yaml
import click
from pathlib import Path

# Optional: only needed when --discord flag is used
try:
    import urllib.request
    _urllib_available = True
except ImportError:
    _urllib_available = False


DB_PATH = Path(__file__).parent / "data" / "contacts.db"
CONFIG_PATH = Path(__file__).parent / "config.yaml"
WEEKLY_TARGET = 8


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        return {}
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def get_db() -> sqlite3.Connection:
    if not DB_PATH.exists():
        click.echo(
            "Error: No database found. Log contacts first with: python tracker.py add",
            err=True,
        )
        raise SystemExit(1)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def fetch_weekly_contacts(conn: sqlite3.Connection, count: int) -> list:
    """
    Pull top-priority uncontacted contacts.
    Queued contacts are included (they were chosen but not yet sent).
    Discovered contacts are included (fresh picks).
    Everything else is excluded.
    """
    rows = conn.execute("""
        SELECT * FROM contacts
        WHERE status IN ('discovered', 'queued')
        ORDER BY relevance DESC, discovery_date ASC
        LIMIT ?
    """, (count,)).fetchall()
    return rows


def mark_as_queued(conn: sqlite3.Connection, ids: list[int]):
    """Mark selected contacts as queued so the plan is stable week-to-week."""
    now = datetime.datetime.utcnow().isoformat()
    conn.executemany(
        "UPDATE contacts SET status='queued', updated_at=? WHERE id=? AND status='discovered'",
        [(now, cid) for cid in ids],
    )
    conn.commit()


def format_plan_text(contacts: list, week_label: str, config: dict) -> str:
    """Build the human-readable weekly plan string."""
    lines = []
    lines.append("")
    lines.append("=" * 65)
    lines.append(f"  WEEKLY OUTREACH PLAN — {week_label}")
    lines.append(f"  Target: {WEEKLY_TARGET} contacts | Geography: {config.get('geography', {}).get('primary', 'N/A')}")
    lines.append("=" * 65)

    if not contacts:
        lines.append("")
        lines.append("  No contacts available to plan.")
        lines.append("  Run 'python discovery.py people --open' to find more,")
        lines.append("  then 'python tracker.py add' to log them.")
        lines.append("")
        return "\n".join(lines)

    for i, c in enumerate(contacts, 1):
        lines.append("")
        lines.append(f"  [{i}] {c['name']}")
        lines.append(f"      Title    : {c['title'] or 'N/A'}")
        lines.append(f"      Company  : {c['company'] or 'N/A'}"
                     + (f" ({c['company_size']} employees)" if c['company_size'] else ""))
        lines.append(f"      Subtype  : {c['subtype'] or 'N/A'}")
        lines.append(f"      Location : {c['location'] or 'N/A'}")
        lines.append(f"      Score    : {c['relevance']}/100")
        lines.append(f"      LinkedIn : {c['linkedin_url'] or 'N/A'}")
        if c['notes']:
            lines.append(f"      Notes    : {c['notes']}")
        lines.append(f"      Status   : {c['status']}")

    lines.append("")
    lines.append("-" * 65)
    lines.append(f"  {len(contacts)} contact(s) queued for outreach this week.")
    lines.append("  After sending each message, update with:")
    lines.append("    python tracker.py update <ID> --status contacted")
    lines.append("-" * 65)
    lines.append("")

    return "\n".join(lines)


def send_to_discord(webhook_url: str, plan_text: str, week_label: str):
    """
    POST the weekly plan to a Discord webhook.
    Discord has a 2000-char message limit; we chunk if needed.
    """
    # Discord code block formatting
    header = f"**Weekly Outreach Plan — {week_label}**\n"
    chunks = []
    remaining = plan_text
    # Reserve room for header on first chunk
    max_len = 1900
    first = True
    while remaining:
        prefix = header if first else ""
        available = max_len - len(prefix)
        chunk_text = remaining[:available]
        remaining = remaining[available:]
        chunks.append(f"{prefix}```\n{chunk_text}\n```")
        first = False

    for chunk in chunks:
        payload = json.dumps({"content": chunk}).encode("utf-8")
        req = urllib.request.Request(
            webhook_url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req) as resp:
            if resp.status not in (200, 204):
                click.echo(f"Discord webhook returned status {resp.status}", err=True)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

@click.group()
def cli():
    """Weekly planner — generate and deliver your 8-contact outreach plan."""
    pass


@cli.command("week")
@click.option("--dry-run", is_flag=True, default=False,
              help="Preview the plan without marking contacts as queued.")
@click.option("--discord", is_flag=True, default=False,
              help="Send the plan to Discord via DISCORD_WEBHOOK_URL env var.")
@click.option("--count", default=WEEKLY_TARGET, type=int,
              help=f"Number of contacts to plan (default: {WEEKLY_TARGET}).")
def weekly_plan(dry_run: bool, discord: bool, count: int):
    """Generate the weekly outreach plan of top-priority contacts."""
    config = load_config()
    conn = get_db()
    contacts = fetch_weekly_contacts(conn, count)

    today = datetime.date.today()
    # Label the plan with the week's Monday date
    monday = today - datetime.timedelta(days=today.weekday())
    week_label = f"Week of {monday.strftime('%B %d, %Y')}"

    plan_text = format_plan_text(contacts, week_label, config)
    click.echo(plan_text)

    if not dry_run and contacts:
        ids = [c["id"] for c in contacts]
        mark_as_queued(conn, ids)
        click.echo(f"  {sum(1 for c in contacts if c['status'] == 'discovered')} "
                   f"contact(s) marked as 'queued'.\n")

    if dry_run:
        click.echo("  (Dry run — no statuses changed.)\n")

    conn.close()

    if discord:
        webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
        if not webhook_url:
            click.echo(
                "Error: DISCORD_WEBHOOK_URL environment variable not set.", err=True
            )
            return
        try:
            send_to_discord(webhook_url, plan_text, week_label)
            click.echo("  Plan sent to Discord.\n")
        except Exception as e:
            click.echo(f"  Discord send failed: {e}", err=True)


@cli.command("progress")
def weekly_progress():
    """Show progress against this week's queued contacts."""
    conn = get_db()
    today = datetime.date.today()
    monday = (today - datetime.timedelta(days=today.weekday())).isoformat()

    # Contacts updated this week across active statuses
    queued = conn.execute(
        "SELECT COUNT(*) FROM contacts WHERE status = 'queued'"
    ).fetchone()[0]
    contacted = conn.execute(
        "SELECT COUNT(*) FROM contacts WHERE status = 'contacted' AND updated_at >= ?",
        (monday,),
    ).fetchone()[0]
    responded = conn.execute(
        "SELECT COUNT(*) FROM contacts WHERE status = 'responded' AND updated_at >= ?",
        (monday,),
    ).fetchone()[0]
    interviewed = conn.execute(
        "SELECT COUNT(*) FROM contacts WHERE status = 'interviewed' AND updated_at >= ?",
        (monday,),
    ).fetchone()[0]
    conn.close()

    click.echo(f"\n{'='*45}")
    click.echo(f"  WEEK PROGRESS (Mon {monday})")
    click.echo(f"{'='*45}")
    click.echo(f"  Still queued (not yet sent) : {queued}")
    click.echo(f"  Contacted this week         : {contacted}")
    click.echo(f"  Responded                   : {responded}")
    click.echo(f"  Interviewed / Called        : {interviewed}")
    click.echo(f"  Weekly target               : {WEEKLY_TARGET}")
    sent = contacted + responded + interviewed
    remaining = max(0, WEEKLY_TARGET - sent)
    click.echo(f"  Sent so far                 : {sent}")
    click.echo(f"  Remaining to hit target     : {remaining}")
    click.echo()


@cli.command("send-discord")
@click.option("--message", required=True, help="Custom message to send to Discord.")
def send_discord_message(message: str):
    """Send a custom message to Discord (for testing the webhook)."""
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        click.echo("Error: DISCORD_WEBHOOK_URL environment variable not set.", err=True)
        return
    try:
        send_to_discord(webhook_url, message, "Manual Send")
        click.echo("  Message sent to Discord.\n")
    except Exception as e:
        click.echo(f"  Discord send failed: {e}", err=True)


if __name__ == "__main__":
    cli()
