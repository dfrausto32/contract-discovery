#!/usr/bin/env python3
"""
dashboard.py — Build a static HTML dashboard of kept GovCon opportunities for
GitHub Pages.

Reads the kept rows from the dedup DB (data/govcon_seen.db) and each
opportunity's README.md write-up, then emits a self-contained static site into
site/ (index.html + app.js + style.css copied from templates/, plus a generated
data.json). The site is deployed by the GitHub Action via actions/deploy-pages;
it is never committed (see .gitignore).

All front-end paths are relative so the site works on a project Pages URL
(https://<user>.github.io/<repo>/).
"""

import ast
import re
import json
import shutil
import datetime
from pathlib import Path

import click
import markdown as md

import store


HERE = Path(__file__).parent
DB_PATH = HERE / "data" / "govcon_seen.db"   # NOT store.DB_PATH (that's trex_seen.db)
TEMPLATES_DIR = HERE / "templates"
DEFAULT_SITE_DIR = HERE / "site"
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


def build_records(conn) -> list[dict]:
    records = []
    for row in store.kept_opportunities(conn):
        agency = short_agency(row["agency"])
        records.append({
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
            "score_band": score_band(row["ai_score"]),
            "ai_generated": bool(row["ai_generated"]),
            "writeup_html": read_writeup(row["output_path"]),
            "folder": Path(row["output_path"]).name if row["output_path"] else "",
        })
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
    return {
        "total_kept": len(records),
        "last_updated": datetime.date.today().isoformat(),
        "evaluated_total": sum(dispositions.values()),
        "by_notice_type": _counter([r["notice_type"] for r in records]),
        "by_score_band": _counter([r["score_band"] for r in records]),
        "top_agencies": [{"name": n, "count": c} for n, c in top],
        "deadlines_within": deadlines,
        # If any AI-scored docs exist, scores are real; otherwise keyword fallback.
        "any_ai": any(r["ai_generated"] for r in records),
    }


def write_site(records: list[dict], summary: dict, site_dir: Path) -> None:
    site_dir.mkdir(parents=True, exist_ok=True)
    for asset in ("index.html", "app.js", "style.css"):
        shutil.copyfile(TEMPLATES_DIR / asset, site_dir / asset)
    (site_dir / ".nojekyll").write_text("")
    (site_dir / "data.json").write_text(
        json.dumps({"summary": summary, "opportunities": records},
                   ensure_ascii=False, indent=None)
    )


@click.group()
def cli():
    """Build the GovCon opportunity dashboard."""
    pass


@cli.command("build")
@click.option("--out", default=None, help="Output site directory (default: ./site).")
def build(out):
    """Generate the static dashboard site from the dedup DB + opportunity docs."""
    site_dir = Path(out) if out else DEFAULT_SITE_DIR
    conn = store.get_db(DB_PATH)
    store.init_db(conn)
    records = build_records(conn)
    summary = build_summary(records, conn)
    conn.close()
    write_site(records, summary, site_dir)
    click.echo(f"Built dashboard: {len(records)} opportunities -> {site_dir}")


if __name__ == "__main__":
    cli()
