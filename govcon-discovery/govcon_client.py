#!/usr/bin/env python3
"""
govcon_client.py — Client for the GovCon API (https://govconapi.com).

Uses the delta endpoint to stay in sync incrementally: each run asks for
opportunities changed since the last successful run's server_time, so we never
re-download the whole corpus. Auth is a Bearer token (GOVCON_API_KEY).

Sync state (the last server_time) is persisted in data/govcon_sync.json.
Docs: https://govconapi.com/api-guide
"""

import time
import json
import datetime
from pathlib import Path

import requests


SYNC_PATH = Path(__file__).parent / "data" / "govcon_sync.json"
# GovCon clamps the `since` lookback at 60 days.
MAX_LOOKBACK_DAYS = 60


def _headers(api_key: str) -> dict:
    return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}


def _iso(dt: datetime.datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _get(url: str, params: dict, api_key: str, retries: int = 4) -> requests.Response:
    """GET with exponential backoff on transient network / 5xx errors."""
    delay = 2
    last_exc = None
    for attempt in range(retries):
        try:
            resp = requests.get(url, params=params, headers=_headers(api_key), timeout=60)
            if resp.status_code >= 500:
                last_exc = RuntimeError(f"server error {resp.status_code}")
            else:
                return resp
        except requests.RequestException as exc:
            last_exc = exc
        if attempt < retries - 1:
            time.sleep(delay)
            delay *= 2
    raise RuntimeError(f"GovCon request failed after {retries} attempts: {last_exc}")


# ---------------------------------------------------------------------------
# Sync state
# ---------------------------------------------------------------------------

def read_sync_state() -> str | None:
    if not SYNC_PATH.exists():
        return None
    try:
        return json.loads(SYNC_PATH.read_text()).get("last_sync")
    except ValueError:
        return None


def write_sync_state(server_time: str) -> None:
    SYNC_PATH.parent.mkdir(parents=True, exist_ok=True)
    SYNC_PATH.write_text(json.dumps({"last_sync": server_time}, indent=2))


def reset_sync_state() -> bool:
    if SYNC_PATH.exists():
        SYNC_PATH.unlink()
        return True
    return False


def initial_since(config: dict) -> str:
    days = min(config["govcon"].get("initial_lookback_days", 30), MAX_LOOKBACK_DAYS)
    return _iso(datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days))


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

def check_key(config: dict, api_key: str) -> dict:
    """Probe the delta endpoint to confirm the Bearer key is accepted."""
    url = config["govcon"]["base_url"] + config["govcon"]["delta_path"]
    since = _iso(datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1))
    try:
        resp = _get(url, {"since": since, "limit": 1, "offset": 0}, api_key)
    except RuntimeError as exc:
        return {"ok": False, "status": None, "message": str(exc)}

    if resp.status_code == 200:
        return {"ok": True, "status": 200, "message": "Key is live."}
    if resp.status_code in (401, 403):
        return {"ok": False, "status": resp.status_code,
                "message": "Key rejected (invalid or unauthorized)."}
    if resp.status_code == 429:
        return {"ok": True, "status": 429,
                "message": "Rate limited, but key is recognized."}
    return {"ok": False, "status": resp.status_code, "message": resp.text[:200]}


def _normalize(item: dict) -> dict:
    """Map a GovCon opportunity object to our internal record shape."""
    naics = item.get("naics")
    email = item.get("contact_email")
    return {
        "notice_id": item.get("notice_id"),
        "title": item.get("title") or "",
        "solicitation_number": item.get("solicitation_number"),
        "agency": item.get("agency") or "",
        "posted_date": (item.get("posted_date") or "")[:10],
        "type": item.get("notice_type") or "",
        "set_aside": item.get("set_aside_type"),
        "naics": str(naics) if naics is not None else None,
        "response_deadline": (item.get("response_deadline") or "")[:10] or None,
        "ui_link": item.get("sam_url"),
        # GovCon returns the full body inline, so no separate fetch is needed.
        "description_text": item.get("description_text") or "",
        "contacts": [email] if email else [],
    }


def delta_sync(config: dict, api_key: str, since: str) -> tuple[list[dict], str | None]:
    """
    Pull all opportunities changed since `since`, following offset pagination.
    Returns (normalized_records, server_time). server_time is the timestamp to
    persist as the next run's `since`.
    """
    gc = config["govcon"]
    url = gc["base_url"] + gc["delta_path"]
    page_size = gc.get("page_size", 1000)

    offset = 0
    records: list[dict] = []
    server_time = None
    while True:
        resp = _get(url, {"since": since, "limit": page_size, "offset": offset}, api_key)
        if resp.status_code != 200:
            raise RuntimeError(f"GovCon returned {resp.status_code}: {resp.text[:200]}")
        data = resp.json()
        for item in data.get("data", []):
            records.append(_normalize(item))
        if server_time is None:
            server_time = (data.get("sync") or {}).get("server_time")
        pagination = data.get("pagination") or {}
        if pagination.get("has_next"):
            offset += page_size
        else:
            break
    return records, server_time
