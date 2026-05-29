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
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import yaml
import click

import govcon_client
import store
import relevance
import description_scan
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


def _write_pending(rec: dict, out_dir: Path,
                   existing_path: str | None = None) -> str:
    """Write opportunity.json only (no README) for pending opps awaiting AI enrichment."""
    if existing_path:
        folder = Path(__file__).parent / existing_path
    else:
        folder = out_dir / f"{rec['posted_date']}__{_slug(rec['notice_id'])}"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "opportunity.json").write_text(json.dumps(rec, indent=2, default=str))
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
    """Pull changed opportunities via delta, score them (Stage 1 + 2), queue for enrichment."""
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

    # Drop past-deadline records immediately — expired opps are useless to pursue.
    today = datetime.date.today().isoformat()
    before = len(records)
    records = [
        r for r in records
        if not r.get("response_deadline") or r["response_deadline"][:10] >= today
    ]
    expired_dropped = before - len(records)

    records.sort(key=lambda r: r["posted_date"] or "", reverse=True)
    click.echo(f"  {len(records)} after notice-type + expired filter "
               f"({expired_dropped} expired dropped, newest first)")

    out_dir = Path(__file__).parent / config["output"]["dir"]
    out_dir.mkdir(parents=True, exist_ok=True)
    conn = store.get_db(DB_PATH)
    store.init_db(conn)

    stage1_threshold = config["relevance"]["stage1_threshold"]
    s2               = config.get("stage2", {})
    desc_keep        = s2.get("desc_score_keep",  65)
    desc_low         = s2.get("desc_score_low",   35)
    desc_floor       = s2.get("desc_score_floor", 20)

    counts = {
        "new": 0, "kept_pending": 0, "pending_low": 0,
        "skipped_stage1": 0, "skipped_stage2": 0,
        "excluded": 0, "already_seen": 0, "amendment": 0,
    }
    total          = len(records)
    pending_titles = []

    click.echo(f"\n{'─'*72}")
    click.echo(f"  {'IDX':>5}  {'S1':>3}  {'S2':>4}  {'CMB':>3}  {'RESULT':<14}  DATE        TITLE")
    click.echo(f"{'─'*72}")

    for rec in records:
        if limit is not None and counts["new"] >= limit:
            click.echo(f"  Limit of {limit} reached — stopping early.")
            break

        if not rec["notice_id"]:
            continue

        if store.is_seen(conn, rec["notice_id"]):
            counts["already_seen"] += 1
            continue

        sol_num  = rec.get("solicitation_number") or None
        existing = store.get_by_solicitation_number(conn, sol_num) if sol_num else None
        is_amendment = existing is not None

        counts["new"] += 1
        if is_amendment:
            counts["amendment"] += 1
        idx       = counts["new"]
        title     = (rec.get("title") or "(untitled)")[:52]
        date      = rec.get("posted_date") or "—"
        amend_tag = " [AMEND]" if is_amendment else ""

        # ── Stage 1 ──────────────────────────────────────────────────────────
        s1 = relevance.stage1_score(rec, config)
        if s1["excluded"]:
            counts["excluded"] += 1
            click.echo(f"  {idx:>5}  {s1['score']:>3}     —    —   {'EXCLUDED':<14}  {date}  {title}{amend_tag}")
            if not dry_run:
                if is_amendment:
                    store.delete_record(conn, existing["notice_id"])
                store.record(conn, rec, "excluded", s1["score"], None, False, None)
            continue

        if s1["score"] < stage1_threshold:
            counts["skipped_stage1"] += 1
            click.echo(f"  {idx:>5}  {s1['score']:>3}     —    —   {'s1-skip':<14}  {date}  {title}{amend_tag}")
            if not dry_run:
                if is_amendment:
                    store.delete_record(conn, existing["notice_id"])
                store.record(conn, rec, "skipped_stage1", s1["score"], None, False, None)
            continue

        # ── Stage 2 — description deep scan ──────────────────────────────────
        d2          = description_scan.scan(rec.get("description_text") or "")
        desc_score  = d2["desc_score"]
        combined    = min(s1["score"] + desc_score, 100)

        if combined < desc_floor:
            counts["skipped_stage2"] += 1
            click.echo(f"  {idx:>5}  {s1['score']:>3}  {desc_score:>4}  {combined:>3}  {'s2-skip':<14}  {date}  {title}{amend_tag}")
            if not dry_run:
                if is_amendment:
                    store.delete_record(conn, existing["notice_id"])
                store.record(conn, rec, "skipped_stage2", s1["score"], None, False, None,
                             desc_score=desc_score, combined_score=combined)
            continue

        # Determine tier
        if combined >= desc_keep:
            disposition = "kept_pending"
            counts["kept_pending"] += 1
            pending_titles.append(rec.get("title") or "(untitled)")
            result_label = "PENDING ◈"
        else:
            disposition = "pending_low"
            counts["pending_low"] += 1
            result_label = "pending-low"

        click.echo(f"  {idx:>5}  {s1['score']:>3}  {desc_score:>4}  {combined:>3}  {result_label:<14}  {date}  {title}{amend_tag}")

        if not dry_run:
            existing_path = (
                existing["output_path"]
                if is_amendment and existing and existing["output_path"]
                else None
            )
            if is_amendment:
                store.delete_record(conn, existing["notice_id"])
            path = _write_pending(rec, out_dir, existing_path)
            store.record(conn, rec, disposition, s1["score"], None, False, path,
                         desc_score=desc_score, combined_score=combined)

    click.echo(f"{'─'*72}\n")

    conn.close()

    if not dry_run and server_time:
        govcon_client.write_sync_state(server_time)
        click.echo(f"  sync state advanced to {server_time}")

    summary = (f"new={counts['new']} kept_pending={counts['kept_pending']} "
               f"pending_low={counts['pending_low']} "
               f"amendment={counts['amendment']} "
               f"skipped_stage1={counts['skipped_stage1']} "
               f"skipped_stage2={counts['skipped_stage2']} "
               f"excluded={counts['excluded']} already_seen={counts['already_seen']}")

    click.echo(f"Results (of {total} type-filtered records):")
    click.echo(f"  already seen   : {counts['already_seen']}")
    click.echo(f"  excluded       : {counts['excluded']}")
    click.echo(f"  stage1 skip    : {counts['skipped_stage1']}")
    click.echo(f"  stage2 skip    : {counts['skipped_stage2']}")
    click.echo(f"  amendments     : {counts['amendment']}")
    click.echo(f"  pending-low    : {counts['pending_low']}")
    click.echo(f"  PENDING ◈      : {counts['kept_pending']}  (run: python govcon.py enrich)")
    click.echo(f"\nDone. {summary}")
    if dry_run:
        click.echo("(dry run — nothing written, recorded, or synced)")
    summary_md = "\n".join(f"- {part}" for part in summary.split(" "))
    _step_summary(f"### GovCon run\n\n{summary_md}")

    # Discord notification (no-op if webhook URL not set).
    discord_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if discord_url and not dry_run:
        try:
            import discord_notify
            discord_notify.post_run_summary(counts, pending_titles, [], discord_url)
        except Exception:
            pass


@cli.command("enrich")
@click.option("--dry-run", is_flag=True, default=False)
@click.option("--limit", default=20, type=int, show_default=True,
              help="Max number of pending records to enrich.")
@click.option("--id", "notice_id", default=None,
              help="Enrich a specific notice_id only.")
def enrich(dry_run: bool, limit: int, notice_id: str):
    """Run AI scoring on kept_pending records (deferred from the daily run)."""
    config = load_config()

    out_dir = Path(__file__).parent / config["output"]["dir"]
    out_dir.mkdir(parents=True, exist_ok=True)
    conn = store.get_db(DB_PATH)
    store.init_db(conn)

    if notice_id:
        rows = conn.execute(
            "SELECT * FROM seen WHERE notice_id=? AND disposition='kept_pending'",
            (notice_id,)
        ).fetchall()
        if not rows:
            click.echo(f"No kept_pending record found for notice_id={notice_id}")
            conn.close()
            return
    else:
        rows = store.get_pending_for_enrich(conn, limit=limit)

    if not rows:
        click.echo("No pending records to enrich. Run `python govcon.py run` first.")
        conn.close()
        return

    click.echo(f"Enriching {len(rows)} pending records with AI ({config['ai'].get('max_workers', 5)} workers)")

    feedback_examples  = store.get_feedback_examples(conn)
    ai_threshold       = config["ai"]["score_threshold"]
    review_min         = config["ai"].get("review_min", 35)
    auto_keep_stage1   = config["ai"].get("auto_keep_stage1", 65)
    gameplan_threshold = config["ai"].get("gameplan_threshold", 80)
    max_workers        = config["ai"].get("max_workers", 5)

    counts = {"kept": 0, "review": 0, "skipped_ai": 0, "ai_error": 0, "gameplan": 0}
    kept_titles   = []
    review_titles = []
    log_lock      = threading.Lock()

    click.echo(f"\n{'─'*72}")
    click.echo(f"  {'IDX':>5}  {'S1':>3}  {'AI':>3}  {'RESULT':<10}  DATE        TITLE")
    click.echo(f"{'─'*72}")

    def _build_rec_from_row(row) -> dict:
        """Reconstruct a minimal rec dict from the DB row for ai_fit."""
        opp_json = Path(__file__).parent / row["output_path"] / "opportunity.json" if row["output_path"] else None
        if opp_json and opp_json.exists():
            return json.loads(opp_json.read_text())
        # Fallback: build from stored columns (description_text won't be available)
        return {
            "notice_id": row["notice_id"],
            "title": row["title"],
            "posted_date": row["posted_date"],
            "type": row["notice_type"],
            "naics": row["naics"],
            "agency": row["agency"],
            "ui_link": row["ui_link"],
            "response_deadline": row["response_deadline"],
            "solicitation_number": row["solicitation_number"],
            "description_text": "",
        }

    def _ai_worker(row):
        rec = _build_rec_from_row(row)
        s1  = {"score": row["stage1_score"] or 0, "matched": [], "excluded": False}
        return row, rec, ai_fit.evaluate_and_write(rec, config, s1, feedback_examples)

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(_ai_worker, row): row for row in rows}
        ai_idx = 0
        for future in as_completed(futures):
            ai_idx += 1
            row = futures[future]
            try:
                row, rec, result = future.result()
            except Exception as exc:
                counts["ai_error"] += 1
                with log_lock:
                    click.echo(f"  {'?':>5}     !   {'AI-ERROR':<10}  {row['title'][:50]}  {exc}", err=True)
                continue

            title     = (row["title"] or "(untitled)")[:55]
            date      = row["posted_date"] or "—"
            s1_score  = row["stage1_score"] or 0

            if result["status"] == "error":
                counts["ai_error"] += 1
                with log_lock:
                    click.echo(f"  {ai_idx:>5}  {s1_score:>3}   !   {'AI-ERROR':<10}  {date}  {title}")
                    click.echo(f"         └─ {result.get('error_msg', '(no detail)')}", err=True)
                continue

            ai_score = result["ai_score"]
            ai_tag   = "[AI]" if result["ai_generated"] else "[KW]"
            no_key   = result["status"] == "no_key"
            strong_s1 = s1_score >= auto_keep_stage1
            keep      = no_key or ai_score >= ai_threshold
            in_review = (not no_key and not strong_s1
                         and review_min <= ai_score < ai_threshold)

            if not keep and not in_review:
                counts["skipped_ai"] += 1
                with log_lock:
                    click.echo(f"  {ai_idx:>5}  {s1_score:>3}  {ai_score:>3}  {'ai-skip':<10}  {date}  {title}  {ai_tag}")
                if not dry_run:
                    store.update_disposition(conn, row["notice_id"], "skipped_ai",
                                             ai_score, result["ai_generated"], row["output_path"])
                continue

            existing_path = row["output_path"] if row["output_path"] else None

            if in_review:
                counts["review"] += 1
                review_titles.append(title)
                with log_lock:
                    click.echo(f"  {ai_idx:>5}  {s1_score:>3}  {ai_score:>3}  {'REVIEW ⚑':<10}  {date}  {title}  {ai_tag}")
                if not dry_run:
                    path = _write_opportunity(rec, result["markdown"], out_dir, None, existing_path)
                    store.update_disposition(conn, row["notice_id"], "review",
                                             ai_score, result["ai_generated"], path)
                    store.set_verdict(conn, row["notice_id"], None)
                    conn.execute("UPDATE seen SET review_flagged=1 WHERE notice_id=?",
                                 (row["notice_id"],))
                    conn.commit()
                continue

            # Keep path
            counts["kept"] += 1
            kept_titles.append(title)
            gameplan = None
            if result["ai_generated"] and ai_score >= gameplan_threshold:
                gameplan = ai_fit.generate_gameplan(rec, config, result["markdown"])
                if gameplan:
                    counts["gameplan"] += 1

            gp_tag = "  ★ GAME PLAN" if gameplan else ""
            with log_lock:
                click.echo(f"  {ai_idx:>5}  {s1_score:>3}  {ai_score:>3}  {'KEEP ✓':<10}  {date}  {title}  {ai_tag}{gp_tag}")

            if not dry_run:
                path = _write_opportunity(rec, result["markdown"], out_dir, gameplan, existing_path)
                store.update_disposition(conn, row["notice_id"], "kept",
                                         ai_score, result["ai_generated"], path)

    click.echo(f"{'─'*72}\n")

    if not dry_run and counts["kept"] > 0:
        _rebuild_index(conn, out_dir)
    conn.close()

    summary = (f"enriched={len(rows)} kept={counts['kept']} "
               f"review={counts['review']} skipped_ai={counts['skipped_ai']} "
               f"ai_error={counts['ai_error']} gameplan={counts['gameplan']}")
    click.echo(f"Enrich done. {summary}")
    if counts["ai_error"]:
        click.echo(f"  WARNING: {counts['ai_error']} AI errors — those records remain kept_pending.")
    if dry_run:
        click.echo("(dry run — nothing written)")
    _step_summary(f"### GovCon enrich\n\n" + "\n".join(f"- {p}" for p in summary.split(" ")))

    discord_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if discord_url and not dry_run and (counts["kept"] + counts["review"]):
        try:
            import discord_notify
            discord_notify.post_run_summary(counts, kept_titles, review_titles, discord_url)
        except Exception:
            pass


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


@cli.command("review")
@click.option("--limit", default=None, type=int, help="Stop after reviewing this many.")
def review(limit: int):
    """Interactively review borderline opportunities in the review queue."""
    conn = store.get_db(DB_PATH)
    store.init_db(conn)
    queue = store.get_review_queue(conn)
    conn.close()

    if not queue:
        click.echo("Review queue is empty. Run `python govcon.py run` to populate it.")
        return

    total_pending = len(queue)
    click.echo(f"\n{'─'*72}")
    click.echo(f"  REVIEW QUEUE — {total_pending} pending")
    click.echo(f"{'─'*72}\n")

    reviewed = kept = skipped_count = 0
    for row in queue:
        if limit is not None and reviewed >= limit:
            break

        click.echo(f"  [{reviewed + 1}/{total_pending}]")
        click.echo(f"  Title  : {row['title']}")
        click.echo(f"  Agency : {row['agency']}")
        click.echo(f"  Scores : stage1={row['stage1_score']}  ai={row['ai_score']}")
        click.echo(f"  NAICS  : {row['naics']}")
        click.echo(f"  Deadline: {row['response_deadline'] or '—'}")
        click.echo(f"  Link   : {row['ui_link'] or '—'}")

        if row["output_path"]:
            readme = Path(__file__).parent / row["output_path"] / "README.md"
            if readme.exists():
                lines = readme.read_text().splitlines()
                # Skip the metadata header (lines up to and including the '---' separator)
                sep = next((i for i, l in enumerate(lines) if l.strip() == "---"), -1)
                body_lines = lines[sep + 1:sep + 22] if sep >= 0 else lines[:22]
                body_lines = [l for l in body_lines if l.strip()][:15]
                if body_lines:
                    click.echo()
                    for l in body_lines:
                        click.echo(f"    {l}")

        click.echo()
        choice = click.prompt(
            "  Keep? [y]es / [n]o / [s]kip / [q]uit",
            default="s",
            show_default=False,
        ).strip().lower()

        if choice == "q":
            break
        if choice == "s":
            click.echo("  — skipped\n")
            reviewed += 1
            continue

        if choice in ("y", "n"):
            verdict = "yes" if choice == "y" else "no"
            notes_raw = click.prompt("  Short note (optional, Enter to skip)", default="", show_default=False).strip()
            notes = notes_raw or None
            conn = store.get_db(DB_PATH)
            store.set_verdict(conn, row["notice_id"], verdict, notes)
            conn.close()
            reviewed += 1
            if verdict == "yes":
                kept += 1
                click.echo("  ✓ KEPT\n")
            else:
                skipped_count += 1
                click.echo("  ✗ PASSED\n")
        else:
            click.echo("  — skipped (unrecognised input)\n")
            reviewed += 1

    remaining = total_pending - reviewed
    click.echo(f"{'─'*72}")
    click.echo(f"  Reviewed {reviewed}  ·  kept {kept}  ·  passed {skipped_count}  ·  {remaining} remaining in queue")
    click.echo(f"{'─'*72}\n")


@cli.command("record-verdict")
@click.option("--notice-id", required=True, help="The notice_id to update.")
@click.option("--verdict", required=True, type=click.Choice(["yes", "no"]),
              help="The human verdict.")
@click.option("--notes", default=None, help="Optional short note.")
def record_verdict(notice_id: str, verdict: str, notes: str):
    """Record a human yes/no verdict (called by the govcon-verdict GitHub Action)."""
    conn = store.get_db(DB_PATH)
    store.init_db(conn)
    store.set_verdict(conn, notice_id, verdict, notes)
    conn.close()
    click.echo(f"Verdict '{verdict}' recorded for {notice_id}")


if __name__ == "__main__":
    cli()
