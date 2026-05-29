#!/usr/bin/env python3
"""
dashboard.py — Generate data.json for the React dashboard (dashboard-ui/).

Reads kept rows from data/govcon_seen.db and each opportunity's README.md,
then writes data.json into dashboard-ui/public/ where the Vite build picks it
up. The React app (dashboard-ui/) is built separately by `npm run build` which
outputs the compiled site into site/ for GitHub Pages deployment.
"""

import ast
import re
import json
import datetime
from pathlib import Path

import click
import markdown as md

import store


HERE = Path(__file__).parent
DB_PATH = HERE / "data" / "govcon_seen.db"   # NOT store.DB_PATH (that's trex_seen.db)
DATA_JSON_PATH = HERE / "dashboard-ui" / "public" / "data.json"
DEADLINE_HORIZONS = (7, 14, 30)


def clean_naics(raw) -> list[str]:
    """`naics` is stored as a stringified list (e.g. "['334515']"). Return clean codes."""
    if not raw:
        return []
    if isinstance(raw, list):
        values = raw
    else:
        try:
            parsed = ast.literal_eval(str(raw))
            values = parsed if isinstance(parsed, (list, tuple)) else [parsed]
        except (ValueError, SyntaxError):
            values = re.findall(r"\d{6}", str(raw)) or [str(raw)]
    return [str(v).strip() for v in values if str(v).strip()]


def short_agency(raw: str) -> dict:
    """Reduce a dotted agency path to readable short/full/group_key forms."""
    full = (raw or "").strip()
    segments = [s.strip() for s in full.split(".") if s.strip()]
    if not segments:
        return {"short": "Unknown", "full": full, "group_key": "UNKNOWN"}
    top = segments[0].title()
    leaf = segments[-1]
    short = top if len(segments) == 1 else f"{top} — {leaf.title()}"
    return {"short": short, "full": full, "group_key": leaf.upper()}


def score_band(score) -> str:
    s = score or 0
    if s >= 90:
        return "90-100"
    if s >= 70:
        return "70-89"
    if s >= 50:
        return "50-69"
    return "<50"


def _days_until(deadline: str):
    if not deadline:
        return None
    try:
        d = datetime.date.fromisoformat(deadline[:10])
    except ValueError:
        return None
    return (d - datetime.date.today()).days


def read_gameplan(output_path: str) -> str:
    """Return the game-plan body as HTML, or empty string if none exists."""
    if not output_path:
        return ""
    gp = HERE / output_path / "gameplan.md"
    if not gp.exists():
        return ""
    return md.markdown(gp.read_text().strip(), extensions=["extra", "sane_lists"])


def read_writeup(output_path: str) -> str:
    """Return the AI/template write-up body of an opportunity as HTML."""
    if not output_path:
        return ""
    readme = HERE / output_path / "README.md"
    if not readme.exists():
        return ""
    text = readme.read_text()
    # ai_fit.py separates the header bullet block (already in the DB fields) from
    # the body with a line containing only '---'. Keep just the body; the
    # template fallback has no separator, so render it whole.
    parts = re.split(r"\n-{3,}\n", text, maxsplit=1)
    body = parts[1] if len(parts) == 2 else text
    return md.markdown(body.strip(), extensions=["extra", "sane_lists"])


def read_description_excerpt(output_path: str, max_chars: int = 500) -> str:
    """Read description_text from opportunity.json for pending opps (no README yet)."""
    if not output_path:
        return ""
    opp_json = HERE / output_path / "opportunity.json"
    if not opp_json.exists():
        return ""
    try:
        data = json.loads(opp_json.read_text())
        text = (data.get("description_text") or "").strip()
        if len(text) > max_chars:
            text = text[:max_chars].rsplit(" ", 1)[0] + "…"
        return text
    except Exception:
        return ""


def _row_to_record(row, in_review: bool = False, in_pending: bool = False) -> dict:
    agency = short_agency(row["agency"])
    keys   = row.keys()
    return {
        "notice_id": row["notice_id"],
        "title": row["title"] or "(untitled)",
        "posted_date": row["posted_date"],
        "response_deadline": row["response_deadline"],
        "deadline_in_days": _days_until(row["response_deadline"]),
        "notice_type": row["notice_type"] or "",
        "naics": clean_naics(row["naics"]),
        "agency_short": agency["short"],
        "agency_full": agency["full"],
        "agency_group": agency["group_key"],
        "ui_link": row["ui_link"],
        "score": row["ai_score"],
        "combined_score": row["combined_score"] if "combined_score" in keys else None,
        "desc_score": row["desc_score"] if "desc_score" in keys else None,
        "score_band": score_band(row["ai_score"] if row["ai_score"] is not None else row["combined_score"]),
        "ai_generated": bool(row["ai_generated"]),
        "writeup_html": read_writeup(row["output_path"]) if not in_pending else "",
        "description_excerpt": read_description_excerpt(row["output_path"]) if in_pending else "",
        "gameplan_html": read_gameplan(row["output_path"]) if not in_pending else "",
        "folder": Path(row["output_path"]).name if row["output_path"] else "",
        "in_review": in_review,
        "in_pending": in_pending,
        "pending_low": row["disposition"] == "pending_low" if "disposition" in keys else False,
        "review_flagged": bool(row["review_flagged"]) if "review_flagged" in keys else False,
        "human_verdict": row["human_verdict"] if "human_verdict" in keys else None,
    }


def build_records(conn) -> list[dict]:
    records = [_row_to_record(row) for row in store.kept_opportunities(conn)]
    # Review-queue opps (AI scored, awaiting human verdict)
    review_rows = conn.execute("""
        SELECT * FROM seen WHERE disposition = 'review'
        ORDER BY posted_date DESC, first_seen DESC
    """).fetchall()
    records += [_row_to_record(row, in_review=True) for row in review_rows]
    # Pending opps (Stage 1+2 passed, AI not yet run)
    pending_rows = store.get_pending_display(conn)
    records += [_row_to_record(row, in_pending=True) for row in pending_rows]
    return records


def _counter(items) -> dict:
    out: dict = {}
    for it in items:
        out[it] = out.get(it, 0) + 1
    return out


def build_summary(records: list[dict], conn) -> dict:
    top = sorted(_counter([r["agency_group"] for r in records]).items(),
                 key=lambda x: -x[1])[:8]
    deadlines = {
        str(h): sum(1 for r in records
                    if r["deadline_in_days"] is not None and 0 <= r["deadline_in_days"] <= h)
        for h in DEADLINE_HORIZONS
    }
    dispositions = store.disposition_counts(conn)
    kept_records   = [r for r in records if not r["in_review"] and not r["in_pending"]]
    review_pending = sum(1 for r in records if r["in_review"] and not r["human_verdict"])
    pending_count  = sum(1 for r in records if r["in_pending"] and not r["pending_low"])
    return {
        "total_kept": len(kept_records),
        "review_count": review_pending,
        "pending_count": pending_count,
        "last_updated": datetime.date.today().isoformat(),
        "evaluated_total": sum(dispositions.values()),
        "by_notice_type": _counter([r["notice_type"] for r in kept_records]),
        "by_score_band": _counter([r["score_band"] for r in kept_records]),
        "top_agencies": [{"name": n, "count": c} for n, c in top],
        "deadlines_within": deadlines,
        "any_ai": any(r["ai_generated"] for r in records),
    }


def write_data_json(records: list[dict], summary: dict, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(
        json.dumps({"summary": summary, "opportunities": records},
                   ensure_ascii=False, indent=None)
    )


@click.group()
def cli():
    """Build the GovCon opportunity dashboard."""
    pass


@cli.command("build")
@click.option("--out", default=None, help="Override output path for data.json.")
def build(out):
    """Write data.json into dashboard-ui/public/ for the React build to consume."""
    dest = Path(out) if out else DATA_JSON_PATH
    conn = store.get_db(DB_PATH)
    store.init_db(conn)
    records = build_records(conn)
    summary = build_summary(records, conn)
    conn.close()
    write_data_json(records, summary, dest)
    click.echo(f"Wrote data.json: {len(records)} opportunities -> {dest}")


if __name__ == "__main__":
    cli()
