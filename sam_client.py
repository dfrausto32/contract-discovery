#!/usr/bin/env python3
"""
sam_client.py — Thin client for the SAM.gov Get Opportunities API (v2).

Official, key-authenticated access — no scraping. One query is issued per
configured NAICS code over the posted-date window, results are merged and
de-duplicated by notice id, filtered to the configured notice types, and
returned newest-posted-first.

Docs: https://open.gsa.gov/api/get-opportunities-public-api/
"""

import re
import time
import datetime
import requests


HTML_TAG_RE = re.compile(r"<[^>]+>")


def _get(url: str, params: dict, retries: int = 4) -> requests.Response:
    """GET with exponential backoff on transient network / 5xx errors."""
    delay = 2
    last_exc = None
    for attempt in range(retries):
        try:
            resp = requests.get(url, params=params, timeout=30)
            # Retry only on transient server-side failures.
            if resp.status_code >= 500:
                last_exc = RuntimeError(f"server error {resp.status_code}")
            else:
                return resp
        except requests.RequestException as exc:
            last_exc = exc
        if attempt < retries - 1:
            time.sleep(delay)
            delay *= 2
    raise RuntimeError(f"SAM.gov request failed after {retries} attempts: {last_exc}")


def _mmddyyyy(d: datetime.date) -> str:
    return d.strftime("%m/%d/%Y")


def check_key(config: dict, api_key: str) -> dict:
    """
    Probe the API with a minimal request to determine whether the key is live.
    Returns {ok, status, message}. A 401/403 means the key is invalid/expired.
    """
    today = datetime.date.today()
    params = {
        "api_key": api_key,
        "limit": 1,
        "postedFrom": _mmddyyyy(today - datetime.timedelta(days=1)),
        "postedTo": _mmddyyyy(today),
    }
    try:
        resp = _get(config["sam"]["base_url"], params)
    except RuntimeError as exc:
        return {"ok": False, "status": None, "message": str(exc)}

    if resp.status_code == 200:
        return {"ok": True, "status": 200, "message": "Key is live."}
    if resp.status_code in (401, 403):
        return {
            "ok": False,
            "status": resp.status_code,
            "message": "Key rejected (invalid or expired) — rotate it on SAM.gov.",
        }
    if resp.status_code == 429:
        return {
            "ok": True,
            "status": 429,
            "message": "Rate limited, but key is recognized.",
        }
    return {"ok": False, "status": resp.status_code, "message": resp.text[:200]}


def _normalize(item: dict) -> dict:
    """Pull the fields we care about out of a raw SAM opportunity record."""
    posted = (item.get("postedDate") or "")[:10]  # YYYY-MM-DD
    contacts = item.get("pointOfContact") or []
    emails = [c.get("email") for c in contacts if c.get("email")]
    return {
        "notice_id": item.get("noticeId"),
        "title": item.get("title") or "",
        "solicitation_number": item.get("solicitationNumber"),
        "agency": item.get("fullParentPathName") or "",
        "posted_date": posted,
        "type": item.get("type") or "",
        "set_aside": item.get("typeOfSetAsideDescription"),
        "naics": item.get("naicsCode"),
        "response_deadline": (item.get("responseDeadLine") or "")[:10] or None,
        "ui_link": item.get("uiLink"),
        "description_link": item.get("description"),
        "contacts": emails,
        "description_text": None,  # filled later, only for AI-stage candidates
    }


def search_opportunities(config: dict, api_key: str,
                         posted_from: datetime.date,
                         posted_to: datetime.date) -> list[dict]:
    """
    Return normalized, de-duplicated opportunities posted in the given window,
    filtered to the configured notice types, sorted newest-posted-first.
    """
    sam = config["sam"]
    allowed_types = set(sam["notice_types"])
    page_size = sam.get("page_size", 100)

    merged: dict[str, dict] = {}
    for naics in sam["naics"]:
        offset = 0
        while True:
            params = {
                "api_key": api_key,
                "limit": page_size,
                "offset": offset,
                "postedFrom": _mmddyyyy(posted_from),
                "postedTo": _mmddyyyy(posted_to),
                "ncode": naics,
            }
            resp = _get(sam["base_url"], params)
            if resp.status_code != 200:
                raise RuntimeError(
                    f"SAM.gov returned {resp.status_code}: {resp.text[:200]}"
                )
            data = resp.json()
            records = data.get("opportunitiesData") or []
            for item in records:
                rec = _normalize(item)
                if rec["type"] not in allowed_types:
                    continue
                if rec["notice_id"] and rec["notice_id"] not in merged:
                    merged[rec["notice_id"]] = rec

            total = data.get("totalRecords", 0)
            offset += page_size
            if offset >= total or not records:
                break

    results = list(merged.values())
    results.sort(key=lambda r: r["posted_date"] or "", reverse=True)
    return results


def fetch_description(config: dict, api_key: str, description_link: str) -> str:
    """
    Retrieve and de-HTML a notice's full text body. Returns "" on any failure
    so the pipeline can fall back to the title alone.
    """
    if not description_link:
        return ""
    try:
        resp = _get(description_link, {"api_key": api_key})
        if resp.status_code != 200:
            return ""
        try:
            body = resp.json().get("description", "")
        except ValueError:
            body = resp.text
    except RuntimeError:
        return ""
    text = HTML_TAG_RE.sub(" ", body or "")
    return re.sub(r"\s+", " ", text).strip()
