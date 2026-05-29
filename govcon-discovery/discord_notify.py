#!/usr/bin/env python3
"""
discord_notify.py — Post pipeline run summaries to a Discord webhook.

No bot token required — uses incoming webhooks (one-way).
Set DISCORD_WEBHOOK_URL in the environment to enable notifications.
All functions are no-ops if the URL is absent or the post fails.
"""

import datetime
import requests


PAGES_URL = "https://dfrausto32.github.io/contract-discovery/"
MAX_EMBED_CHARS = 1900


def _truncate_list(items: list[str], max_items: int = 5) -> str:
    shown = items[:max_items]
    lines = [f"▸ {t[:80]}" for t in shown]
    if len(items) > max_items:
        lines.append(f"…and {len(items) - max_items} more")
    return "\n".join(lines) or "—"


def post_run_summary(counts: dict, kept_titles: list[str],
                     review_titles: list[str], webhook_url: str) -> None:
    """Post a run-complete embed to Discord."""
    if not webhook_url:
        return

    kept    = counts.get("kept", 0)
    review  = counts.get("review", 0)
    skipped = counts.get("skipped_ai", 0) + counts.get("skipped_stage1", 0)
    errors  = counts.get("ai_error", 0)
    new     = counts.get("new", 0)
    today   = datetime.date.today().isoformat()

    color = 0x39FF14 if kept > 0 else (0xFF9500 if review > 0 else 0x6A6045)

    fields = [
        {"name": "✓ Kept",         "value": str(kept),    "inline": True},
        {"name": "⚑ Review Queue", "value": str(review),  "inline": True},
        {"name": "✗ Skipped",      "value": str(skipped), "inline": True},
    ]
    if errors:
        fields.append({"name": "! AI Errors", "value": str(errors), "inline": True})

    if kept_titles:
        fields.append({
            "name": "Kept Opportunities",
            "value": _truncate_list(kept_titles),
            "inline": False,
        })
    if review_titles:
        fields.append({
            "name": "Added to Review Queue",
            "value": _truncate_list(review_titles),
            "inline": False,
        })

    embed = {
        "title": "⚡ GOVCON RUN COMPLETE",
        "color": color,
        "fields": fields,
        "footer": {
            "text": f"{today} · {new} new evaluated · View dashboard → {PAGES_URL}",
        },
    }

    try:
        requests.post(
            webhook_url,
            json={"embeds": [embed]},
            timeout=10,
        ).raise_for_status()
    except Exception:
        pass  # never let a notification failure surface to the caller


def post_verdict_recorded(notice_id: str, title: str,
                          verdict: str, webhook_url: str) -> None:
    """Post a brief notification when a dashboard verdict is recorded."""
    if not webhook_url:
        return

    color  = 0x39FF14 if verdict == "yes" else 0xFF0055
    symbol = "✓ PURSUED" if verdict == "yes" else "✗ PASSED"
    today  = datetime.date.today().isoformat()

    embed = {
        "title": f"{symbol}",
        "description": f"**{title[:120]}**\n`{notice_id}`",
        "color": color,
        "footer": {"text": today},
    }

    try:
        requests.post(
            webhook_url,
            json={"embeds": [embed]},
            timeout=10,
        ).raise_for_status()
    except Exception:
        pass
