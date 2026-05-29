#!/usr/bin/env python3
"""
description_scan.py — Stage 2 deterministic description deep-scan.

Runs after Stage 1 (keyword/NAICS pre-filter) on the full description body.
Returns a score delta and a list of matched signal labels so the caller can
compute: combined_score = min(stage1_score + desc_score, 100).

Four signal categories:
  tech_stack   — specific tools/frameworks/standards in the description body
  contract     — positive structural signals (task order, agile, set-aside type)
  disqualify   — scope red-flags that suggest this is NOT IT services work
  clearance    — secret/TS flags; accessible clearances are slight positives,
                 TS/SCI is a negative (not feasible for a small shop)
"""

import re


def _match(kw: str, text: str) -> bool:
    """Word-boundary safe match — prevents 'sso' hitting 'associated', etc."""
    return bool(re.search(r'\b' + re.escape(kw) + r'\b', text))


# ---------------------------------------------------------------------------
# Signal tables
# ---------------------------------------------------------------------------

_TECH_STACK = [
    # DevOps / platform
    "kubernetes", "k8s", "terraform", "ansible", "ci/cd", "devops", "devsecops",
    "continuous integration", "continuous deployment", "continuous delivery",
    "infrastructure as code", "platform engineering", "site reliability",
    "cloud native", "cloud-native", "containerization", "service mesh",
    "observability", "opentelemetry", "prometheus", "grafana",
    # Security / compliance
    "fedramp", "zero trust", "zerotrust", "siem", "ato", "rmf",
    "identity and access management", "iam", "privileged access",
    "sso", "oauth", "saml", "pki", "vulnerability management",
    "penetration test", "security operations center", "soc 2", "nist",
    # Data
    "data pipeline", "etl", "data lake", "data warehouse", "data mesh",
    "apache spark", "kafka", "airflow", "dbt", "snowflake", "postgres",
    "postgresql", "elastic search", "elasticsearch",
    # API / backend
    "api gateway", "rest api", "restful", "graphql", "grpc",
    "microservices", "event-driven", "message queue",
    # Cloud platforms (more specific than "cloud")
    "amazon web services", "azure government", "govcloud", "google cloud",
]

_CONTRACT_SIGNALS = [
    "task order", "task-order",
    "prime contractor", "prime contract",
    "full and open competition", "full and open",
    "small business set-aside", "sdvosb", "8(a)", "hubzone", "wosb",
    "performance-based", "performance based",
    "agile delivery", "agile development", "agile framework",
    "scrum", "sprint", "user story", "backlog",
    "base year", "option year", "period of performance",
]

_DISQUALIFIERS = [
    "physical security officer", "physical access control",
    "facilities management", "facilities maintenance", "building maintenance",
    "construction project", "construction contract",
    "grounds maintenance", "grounds keeping",
    "fleet management", "vehicle fleet",
    "food service", "dining facility",
    "janitorial", "custodial",
    "medical device", "surgical", "laboratory equipment",
    "fire suppression", "hvac system",
    # Hardware / spare parts procurement
    "national stock number", "individual repair part", "irpod",
    "repair part ordering data", "spare part", "spare parts",
    "replacement part", "replacement parts",
    "hull, mechanical and electrical", "propulsion system",
    "airframe", "aircraft component",
]

_CLEARANCE_HIGH = [
    "top secret/sci", "ts/sci", "sci access", "sensitive compartmented",
    "full scope polygraph", "lifestyle polygraph",
]

_CLEARANCE_LOW = [
    "secret clearance", "secret required", "require secret",
    "active secret", "top secret", "public trust",
]

_TECH_WEIGHT        =  8
_CONTRACT_WEIGHT    =  6
_DISQUALIFY_WEIGHT  = -10
_CLEARANCE_HI_WEIGHT = -8
_CLEARANCE_LO_WEIGHT =  4


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def scan(description: str) -> dict:
    """
    Scan a full description body and return {desc_score, signals}.

    desc_score  — integer delta to add to stage1_score (can be negative)
    signals     — list of label strings for logging / dashboard display
    """
    text = (description or "").lower()
    # Collapse whitespace so multi-word phrases match across soft line-breaks.
    text = re.sub(r"\s+", " ", text)

    score = 0
    signals: list[str] = []

    for kw in _TECH_STACK:
        if _match(kw, text):
            score += _TECH_WEIGHT
            signals.append(f"tech:{kw}")

    for kw in _CONTRACT_SIGNALS:
        if _match(kw, text):
            score += _CONTRACT_WEIGHT
            signals.append(f"contract:{kw}")

    for kw in _DISQUALIFIERS:
        if _match(kw, text):
            score += _DISQUALIFY_WEIGHT
            signals.append(f"DISQUALIFY:{kw}")

    for kw in _CLEARANCE_HIGH:
        if _match(kw, text):
            score += _CLEARANCE_HI_WEIGHT
            signals.append(f"CLEARANCE_HIGH:{kw}")

    for kw in _CLEARANCE_LOW:
        if _match(kw, text):
            score += _CLEARANCE_LO_WEIGHT
            signals.append(f"clearance_ok:{kw}")

    return {"desc_score": score, "signals": signals}
