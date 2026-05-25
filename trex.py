#!/usr/bin/env python3
"""
trex.py — SAM.gov opportunity discovery for TReX (BlackHorse / Parsons).

Pulls recent federal contract opportunities from the official SAM.gov
Opportunities API, filters them to TReX's electronic-warfare domain in two
stages (keyword/NAICS pre-filter, then AI relevance scoring), and writes a
per-contract "how TReX fits" README into the opportunities/ folder. Contracts
are never repeated and the newest postings are processed first.

Commands:
  run           Daily pull + doc generation (used by the GitHub Action)
  health        Check SAM.gov API key liveness + days until expiry
  set-key-date  Record the date you activated the SAM.gov key
  list          List kept opportunities
  stats         Show evaluation counts by disposition
"""

import os
import json
import datetime
import re
from pathlib import Path

import yaml
import click

import sam_client
import store
import relevance
import ai_fit


CONFIG_PATH = Path(__file__).parent / "trex_config.yaml"
KEY_META_PATH = Path(__file__).parent / "data" / "key_meta.json"


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


def _write_opportunity(rec: dict, markdown: str, out_dir: Path) -> str:
    folder = out_dir / f"{rec['posted_date']}__{_slug(rec['notice_id'])}"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "README.md").write_text(markdown)
    (folder / "opportunity.json").write_text(json.dumps(rec, indent=2, default=str))
    return str(folder.relative_to(out_dir.parent))


def _rebuild_index(conn, out_dir: Path) -> None:
    rows = store.kept_opportunities(conn)
    lines = [
        "# TReX Opportunity Index",
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
        # output_path is repo-root-relative; INDEX.md lives inside out_dir, so
        # link by the folder's basename to keep the relative link valid.
        folder = Path(r["output_path"]).name if r["output_path"] else ""
        title_cell = f"[{title}]({folder})" if folder else title
        link = f"[open]({r['ui_link']})" if r["ui_link"] else ""
        lines.append(
            f"| {r['posted_date']} | {title_cell} | {agency} | "
            f"{r['notice_type']} | {r['ai_score']} | "
            f"{r['response_deadline'] or ''} | {link} |"
        )
    (out_dir / "INDEX.md").write_text("\n".join(lines) + "\n")


def _key_days_remaining(config: dict):
    """Days until the tracked SAM key hits its lifetime, or None if unknown."""
    if not KEY_META_PATH.exists():
        return None
    try:
        activated = json.loads(KEY_META_PATH.read_text())["activated"]
        activated_date = datetime.date.fromisoformat(activated)
    except (ValueError, KeyError):
        return None
    lifetime = config["key_health"]["lifetime_days"]
    expiry = activated_date + datetime.timedelta(days=lifetime)
    return (expiry - datetime.date.today()).days


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

@click.group()
def cli():
    """SAM.gov opportunity discovery for TReX."""
    pass


@cli.command("run")
@click.option("--dry-run", is_flag=True, default=False,
              help="Evaluate and print, but write no files and record nothing.")
@click.option("--lookback", default=None, type=int,
              help="Override lookback_days from config.")
@click.option("--limit", default=None, type=int,
              help="Stop after evaluating this many new opportunities.")
def run(dry_run: bool, lookback: int, limit: int):
    """Pull recent opportunities, score them, and write TReX fit docs."""
    config = load_config()
    api_key = os.environ.get("SAM_API_KEY")
    if not api_key:
        raise click.ClickException("SAM_API_KEY environment variable is not set.")

    days = lookback if lookback is not None else config["sam"]["lookback_days"]
    posted_to = datetime.date.today()
    posted_from = posted_to - datetime.timedelta(days=days)

    click.echo(f"Querying SAM.gov: {posted_from} -> {posted_to} "
               f"({len(config['sam']['naics'])} NAICS codes)")
    records = sam_client.search_opportunities(config, api_key, posted_from, posted_to)
    click.echo(f"  {len(records)} opportunities in window (after notice-type filter)")

    out_dir = Path(__file__).parent / config["output"]["dir"]
    out_dir.mkdir(parents=True, exist_ok=True)
    conn = store.get_db()
    store.init_db(conn)

    stage1_threshold = config["relevance"]["stage1_threshold"]
    ai_threshold = config["ai"]["score_threshold"]
    counts = {"new": 0, "kept": 0, "skipped_stage1": 0,
              "skipped_ai": 0, "excluded": 0, "already_seen": 0}

    for rec in records:
        if limit is not None and counts["new"] >= limit:
            break
        if store.is_seen(conn, rec["notice_id"]):
            counts["already_seen"] += 1
            continue
        counts["new"] += 1

        s1 = relevance.stage1_score(rec, config)
        if s1["excluded"]:
            counts["excluded"] += 1
            if not dry_run:
                store.record(conn, rec, "excluded", s1["score"], None, False, None)
            continue
        if s1["score"] < stage1_threshold:
            counts["skipped_stage1"] += 1
            if not dry_run:
                store.record(conn, rec, "skipped_stage1", s1["score"], None, False, None)
            continue

        # Survivor: fetch full text, then run the AI stage.
        rec["description_text"] = sam_client.fetch_description(
            config, api_key, rec["description_link"]
        )
        result = ai_fit.evaluate_and_write(rec, config, s1)

        keep = (not result["ai_generated"]) or result["ai_score"] >= ai_threshold
        if not keep:
            counts["skipped_ai"] += 1
            if not dry_run:
                store.record(conn, rec, "skipped_ai", s1["score"],
                             result["ai_score"], result["ai_generated"], None)
            continue

        counts["kept"] += 1
        click.echo(f"  KEEP [{result['ai_score']}] {rec['posted_date']} "
                   f"{rec['title'][:70]}")
        if not dry_run:
            path = _write_opportunity(rec, result["markdown"], out_dir)
            store.record(conn, rec, "kept", s1["score"], result["ai_score"],
                         result["ai_generated"], path)

    if not dry_run and counts["kept"] > 0:
        _rebuild_index(conn, out_dir)
    conn.close()

    summary = (f"new={counts['new']} kept={counts['kept']} "
               f"skipped_stage1={counts['skipped_stage1']} "
               f"skipped_ai={counts['skipped_ai']} excluded={counts['excluded']} "
               f"already_seen={counts['already_seen']}")
    click.echo(f"\nDone. {summary}")
    if dry_run:
        click.echo("(dry run — nothing written or recorded)")
    summary_md = "\n".join(f"- {part}" for part in summary.split(" "))
    _step_summary(f"### TReX daily run\n\n{summary_md}")


@cli.command("health")
def health():
    """Check SAM.gov key liveness and days remaining before expiry."""
    config = load_config()
    api_key = os.environ.get("SAM_API_KEY")
    if not api_key:
        _step_summary("### SAM.gov key health\n\n**SAM_API_KEY not set.**")
        raise click.ClickException("SAM_API_KEY environment variable is not set.")

    live = sam_client.check_key(config, api_key)
    days = _key_days_remaining(config)
    warn_within = config["key_health"]["warn_within_days"]

    status_icon = "OK" if live["ok"] else "FAIL"
    click.echo(f"Key liveness: [{status_icon}] {live['message']}")

    if days is None:
        expiry_line = ("Activation date unknown — set it with "
                       "`python trex.py set-key-date YYYY-MM-DD`.")
    elif days < 0:
        expiry_line = f"Key is {-days} day(s) PAST its {config['key_health']['lifetime_days']}-day lifetime — rotate now."
    elif days <= warn_within:
        expiry_line = f"Key expires in {days} day(s) — rotate soon."
    else:
        expiry_line = f"Key has ~{days} day(s) remaining."
    click.echo(expiry_line)

    _step_summary(
        "### SAM.gov key health\n\n"
        f"- Liveness: **{status_icon}** — {live['message']}\n"
        f"- Expiry: {expiry_line}"
    )

    # Hard-fail only when the key is actually rejected, so a near-expiry warning
    # does not break the daily run.
    if not live["ok"]:
        raise click.ClickException("SAM.gov key is not usable.")


@cli.command("set-key-date")
@click.argument("date", required=False)
def set_key_date(date: str):
    """Record the date you activated the SAM.gov key (defaults to today)."""
    activated = date or datetime.date.today().isoformat()
    datetime.date.fromisoformat(activated)  # validate
    KEY_META_PATH.parent.mkdir(parents=True, exist_ok=True)
    KEY_META_PATH.write_text(json.dumps({"activated": activated}, indent=2))
    click.echo(f"Recorded key activation date: {activated}")


@cli.command("list")
def list_kept():
    """List kept opportunities, newest posted first."""
    conn = store.get_db()
    store.init_db(conn)
    rows = store.kept_opportunities(conn)
    conn.close()
    if not rows:
        click.echo("No kept opportunities yet. Run: python trex.py run")
        return
    for r in rows:
        click.echo(f"[{r['ai_score']:>3}] {r['posted_date']} | "
                   f"{(r['title'] or '')[:60]:<60} | {r['output_path']}")


@cli.command("stats")
def stats():
    """Show evaluation counts by disposition."""
    conn = store.get_db()
    store.init_db(conn)
    counts = store.disposition_counts(conn)
    conn.close()
    total = sum(counts.values())
    click.echo(f"Evaluated: {total}")
    for disp, n in sorted(counts.items(), key=lambda x: -x[1]):
        click.echo(f"  {disp:<16}: {n}")


if __name__ == "__main__":
    cli()
