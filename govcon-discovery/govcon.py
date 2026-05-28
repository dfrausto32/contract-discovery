#!/usr/bin/env python3
"""
govcon.py — GovCon opportunity discovery for backend/DevOps engineer profile.

Pulls opportunities incrementally via the GovCon delta endpoint (staying in
sync without re-downloading everything), filters them to backend services and
deployment pipeline work in two stages (keyword/NAICS pre-filter, then AI
relevance scoring), and writes a per-contract candidate fit README into the
opportunities/ folder. Contracts are never repeated and the newest postings
are processed first.

Commands:
  run         Incremental delta pull + doc generation (used by the Action)
  health      Check that the GovCon API key is accepted
  reset-sync  Clear saved sync state so the next run does a full lookback
  list        List kept opportunities
  stats       Show evaluation counts by disposition
"""

import os
import json
import datetime
import re
from pathlib import Path

import yaml
import click

import govcon_client
import store
import relevance
import ai_fit


CONFIG_PATH = Path(__file__).parent / "govcon_config.yaml"
DB_PATH = Path(__file__).parent / "data" / "govcon_seen.db"


def load_config() -> dict:
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def _slug(notice_id: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]", "-", notice_id or "unknown")


def _step_summary(line: str) -> None:
    """Append a line to the GitHub Actions job summary, if running in CI."""
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if path:
        with open(path, "a") as f:
            f.write(line + "\n")


def _write_opportunity(rec: dict, markdown: str, out_dir: Path,
                        gameplan: str | None = None,
                        existing_path: str | None = None) -> str:
    if existing_path:
        # Amendment overwriting a kept opp — reuse the existing folder.
        folder = Path(__file__).parent / existing_path
    else:
        folder = out_dir / f"{rec['posted_date']}__{_slug(rec['notice_id'])}"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "README.md").write_text(markdown)
    (folder / "opportunity.json").write_text(json.dumps(rec, indent=2, default=str))
    if gameplan:
        (folder / "gameplan.md").write_text(gameplan)
    return str(folder.relative_to(out_dir.parent))


def _rebuild_index(conn, out_dir: Path) -> None:
    rows = store.kept_opportunities(conn)
    lines = [
        "# GovCon Opportunity Index",
        "",
        f"_Last updated {datetime.date.today().isoformat()} — {len(rows)} "
        "opportunities, newest posted first._",
        "",
        "| Posted | Title | Agency | Type | AI Score | Deadline | SAM.gov |",
        "|--------|-------|--------|------|---------:|----------|---------|",
    ]
    for r in rows:
        title = (r["title"] or "").replace("|", "/")
        agency = (r["agency"] or "").replace("|", "/")
        folder = Path(r["output_path"]).name if r["output_path"] else ""
        title_cell = f"[{title}]({folder})" if folder else title
        link = f"[open]({r['ui_link']})" if r["ui_link"] else ""
        lines.append(
            f"| {r['posted_date']} | {title_cell} | {agency} | "
            f"{r['notice_type']} | {r['ai_score']} | "
            f"{r['response_deadline'] or ''} | {link} |"
        )
    (out_dir / "INDEX.md").write_text("\n".join(lines) + "\n")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

@click.group()
def cli():
    """GovCon opportunity discovery."""
    pass


@cli.command("run")
@click.option("--dry-run", is_flag=True, default=False,
              help="Evaluate and print, but write no files and record nothing.")
@click.option("--since", default=None,
              help="Override the delta start timestamp (ISO 8601, e.g. 2026-05-01T00:00:00Z).")
@click.option("--full", is_flag=True, default=False,
              help="Ignore saved sync state and use the initial_lookback_days window.")
@click.option("--limit", default=None, type=int,
              help="Stop after evaluating this many new opportunities.")
def run(dry_run: bool, since: str, full: bool, limit: int):
    """Pull changed opportunities via delta, score them, and write fit docs."""
    config = load_config()
    api_key = os.environ.get("GOVCON_API_KEY")
    if not api_key:
        raise click.ClickException("GOVCON_API_KEY environment variable is not set.")

    if since:
        start = since
    elif full:
        start = govcon_client.initial_since(config)
    else:
        start = govcon_client.read_sync_state() or govcon_client.initial_since(config)

    click.echo(f"GovCon delta since {start}")
    records, server_time = govcon_client.delta_sync(config, api_key, start)
    click.echo(f"  {len(records)} changed opportunities returned")

    allowed_types = set(config["govcon"]["notice_types"])
    records = [r for r in records if r["type"] in allowed_types]
    records.sort(key=lambda r: r["posted_date"] or "", reverse=True)
    click.echo(f"  {len(records)} after notice-type filter (newest first)")

    out_dir = Path(__file__).parent / config["output"]["dir"]
    out_dir.mkdir(parents=True, exist_ok=True)
    conn = store.get_db(DB_PATH)
    store.init_db(conn)

    stage1_threshold = config["relevance"]["stage1_threshold"]
    ai_threshold = config["ai"]["score_threshold"]
    gameplan_threshold = config["ai"].get("gameplan_threshold", 80)
    counts = {"new": 0, "kept": 0, "skipped_stage1": 0,
              "skipped_ai": 0, "excluded": 0, "already_seen": 0,
              "ai_error": 0, "gameplan": 0, "amendment": 0}
    total = len(records)

    click.echo(f"\n{'─'*72}")
    click.echo(f"  {'IDX':>5}  {'S1':>3}  {'AI':>3}  {'RESULT':<10}  DATE        TITLE")
    click.echo(f"{'─'*72}")

    for rec in records:
        if limit is not None and counts["new"] >= limit:
            click.echo(f"{'─'*72}")
            click.echo(f"  Limit of {limit} reached — stopping early.")
            break

        if not rec["notice_id"]:
            continue

        # Skip if this exact notice_id was already processed.
        if store.is_seen(conn, rec["notice_id"]):
            counts["already_seen"] += 1
            continue

        # Detect amendments: same sol#, different notice_id.
        sol_num  = rec.get("solicitation_number") or None
        existing = store.get_by_solicitation_number(conn, sol_num) if sol_num else None
        is_amendment = existing is not None

        counts["new"] += 1
        if is_amendment:
            counts["amendment"] += 1
        idx   = counts["new"]
        title = (rec.get("title") or "(untitled)")[:55]
        date  = rec.get("posted_date") or "—"
        amend_tag = " [AMEND]" if is_amendment else ""

        # Stage 1: keyword / NAICS pre-filter
        s1 = relevance.stage1_score(rec, config)
        if s1["excluded"]:
            counts["excluded"] += 1
            click.echo(f"  {idx:>5}  {s1['score']:>3}   —   {'EXCLUDED':<10}  {date}  {title}{amend_tag}")
            if not dry_run:
                if is_amendment:
                    store.delete_record(conn, existing["notice_id"])
                store.record(conn, rec, "excluded", s1["score"], None, False, None)
            continue
        if s1["score"] < stage1_threshold:
            counts["skipped_stage1"] += 1
            click.echo(f"  {idx:>5}  {s1['score']:>3}   —   {'s1-skip':<10}  {date}  {title}{amend_tag}")
            if not dry_run:
                if is_amendment:
                    store.delete_record(conn, existing["notice_id"])
                store.record(conn, rec, "skipped_stage1", s1["score"], None, False, None)
            continue

        # Stage 2: AI scoring
        result = ai_fit.evaluate_and_write(rec, config, s1)

        if result["status"] == "error":
            counts["ai_error"] += 1
            click.echo(f"  {idx:>5}  {s1['score']:>3}   !   {'AI-ERROR':<10}  {date}  {title}{amend_tag}")
            click.echo(f"         └─ {result.get('error_msg', '(no detail)')}", err=True)
            continue

        ai_score = result["ai_score"]
        ai_tag   = "[AI]" if result["ai_generated"] else "[KW]"
        keep = result["status"] == "no_key" or ai_score >= ai_threshold

        if not keep:
            counts["skipped_ai"] += 1
            click.echo(f"  {idx:>5}  {s1['score']:>3}  {ai_score:>3}  {'ai-skip':<10}  {date}  {title}  {ai_tag}{amend_tag}")
            if not dry_run:
                if is_amendment:
                    store.delete_record(conn, existing["notice_id"])
                store.record(conn, rec, "skipped_ai", s1["score"],
                             ai_score, result["ai_generated"], None)
            continue

        counts["kept"] += 1
        gameplan = None
        if result["ai_generated"] and ai_score >= gameplan_threshold:
            gameplan = ai_fit.generate_gameplan(rec, config, result["markdown"])
            if gameplan:
                counts["gameplan"] += 1

        gp_tag = "  ★ GAME PLAN" if gameplan else ""
        click.echo(f"  {idx:>5}  {s1['score']:>3}  {ai_score:>3}  {'KEEP ✓':<10}  {date}  {title}  {ai_tag}{amend_tag}{gp_tag}")

        if not dry_run:
            # Amendments to kept opps reuse the existing folder so the
            # dashboard path stays stable. Amendments to skipped opps get a
            # new folder since there was no prior output to overwrite.
            existing_path = (
                existing["output_path"]
                if is_amendment and existing and existing["disposition"] == "kept"
                else None
            )
            if is_amendment:
                store.delete_record(conn, existing["notice_id"])
            path = _write_opportunity(rec, result["markdown"], out_dir, gameplan, existing_path)
            store.record(conn, rec, "kept", s1["score"], ai_score,
                         result["ai_generated"], path)

    click.echo(f"{'─'*72}\n")

    if not dry_run and counts["kept"] > 0:
        _rebuild_index(conn, out_dir)
    conn.close()

    # Advance sync state only on a clean, non-dry run. If any opportunity hit an
    # AI error we hold the timestamp so the next run re-pulls this same window and
    # retries them (advancing would push them out of the delta window forever).
    if not dry_run and server_time and counts["ai_error"] == 0:
        govcon_client.write_sync_state(server_time)
        click.echo(f"  sync state advanced to {server_time}")
    elif not dry_run and counts["ai_error"]:
        click.echo("  sync state held (AI errors this run) — this window re-pulls next run")

    summary = (f"new={counts['new']} kept={counts['kept']} "
               f"amendment={counts['amendment']} "
               f"skipped_stage1={counts['skipped_stage1']} "
               f"skipped_ai={counts['skipped_ai']} excluded={counts['excluded']} "
               f"ai_error={counts['ai_error']} already_seen={counts['already_seen']} "
               f"gameplan={counts['gameplan']}")

    click.echo(f"Results (of {total} type-filtered records):")
    click.echo(f"  already seen   : {counts['already_seen']}")
    click.echo(f"  excluded       : {counts['excluded']}")
    click.echo(f"  stage1 skip    : {counts['skipped_stage1']}")
    click.echo(f"  AI skip        : {counts['skipped_ai']}")
    click.echo(f"  AI error       : {counts['ai_error']}")
    click.echo(f"  amendments     : {counts['amendment']}")
    click.echo(f"  KEPT           : {counts['kept']}  (game plans: {counts['gameplan']})")
    click.echo(f"\nDone. {summary}")
    if counts["ai_error"]:
        click.echo(f"  WARNING: {counts['ai_error']} opportunities hit AI errors "
                   "(not kept, will retry next run). Check the provider key/model.")
    if dry_run:
        click.echo("(dry run — nothing written, recorded, or synced)")
    summary_md = "\n".join(f"- {part}" for part in summary.split(" "))
    _step_summary(f"### GovCon run\n\n{summary_md}")


@cli.command("health")
def health():
    """Check that the GovCon API key is accepted."""
    config = load_config()
    api_key = os.environ.get("GOVCON_API_KEY")
    if not api_key:
        _step_summary("### GovCon key health\n\n**GOVCON_API_KEY not set.**")
        raise click.ClickException("GOVCON_API_KEY environment variable is not set.")

    live = govcon_client.check_key(config, api_key)
    status_icon = "OK" if live["ok"] else "FAIL"
    click.echo(f"Key liveness: [{status_icon}] {live['message']}")
    _step_summary(f"### GovCon key health\n\n- Liveness: **{status_icon}** — {live['message']}")
    if not live["ok"]:
        raise click.ClickException("GovCon key is not usable.")


@cli.command("reset-sync")
def reset_sync():
    """Clear saved sync state so the next run does a full initial lookback."""
    if govcon_client.reset_sync_state():
        click.echo("Sync state cleared.")
    else:
        click.echo("No sync state to clear.")


@cli.command("list")
def list_kept():
    """List kept opportunities, newest posted first."""
    conn = store.get_db(DB_PATH)
    store.init_db(conn)
    rows = store.kept_opportunities(conn)
    conn.close()
    if not rows:
        click.echo("No kept opportunities yet. Run: python govcon.py run")
        return
    for r in rows:
        click.echo(f"[{r['ai_score']:>3}] {r['posted_date']} | "
                   f"{(r['title'] or '')[:60]:<60} | {r['output_path']}")


@cli.command("stats")
def stats():
    """Show evaluation counts by disposition."""
    conn = store.get_db(DB_PATH)
    store.init_db(conn)
    counts = store.disposition_counts(conn)
    conn.close()
    total = sum(counts.values())
    click.echo(f"Evaluated: {total}")
    for disp, n in sorted(counts.items(), key=lambda x: -x[1]):
        click.echo(f"  {disp:<16}: {n}")


if __name__ == "__main__":
    cli()
