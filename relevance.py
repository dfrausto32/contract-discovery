#!/usr/bin/env python3
"""
relevance.py — Stage 1 deterministic pre-filter.

Scores an opportunity 0-100 from config-driven keyword and NAICS signals
before any AI is involved. This gates which candidates are worth an AI call,
keeping the daily run cheap and focused.
"""


def stage1_score(rec: dict, config: dict) -> dict:
    """
    Returns {score, excluded, matched}. `excluded` is True when an exclude
    keyword appears; such records are dropped regardless of score.
    """
    rel = config["relevance"]
    text = f"{rec.get('title', '')} {rec.get('description_text') or ''}".lower()

    matched_exclude = [k for k in rel["exclude_keywords"] if k in text]
    if matched_exclude:
        return {"score": 0, "excluded": True, "matched": matched_exclude}

    score = 0
    matched: list[str] = []

    if rec.get("naics") in set(config["sam"]["naics"]):
        score += rel["naics_weight"]

    for kw in rel["boost_keywords"]:
        if kw in text:
            score += rel["boost_weight"]
            matched.append(kw)

    for kw in rel["include_keywords"]:
        if kw in text:
            score += rel["include_weight"]
            matched.append(kw)

    return {"score": min(score, 100), "excluded": False, "matched": matched}
