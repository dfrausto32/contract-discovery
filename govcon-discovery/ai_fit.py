#!/usr/bin/env python3
"""
ai_fit.py — Stage 2: AI relevance scoring + "how TReX fits" doc generation.

Provider-agnostic. Set `ai.provider` in trex_config.yaml to "claude"
(ANTHROPIC_API_KEY) or "openai" (OPENAI_API_KEY). If the relevant key is not
present in the environment, a deterministic template doc is produced instead
and ai_generated is reported as False, so the pipeline runs end-to-end before
any AI key is configured.

A single call returns both a 0-100 relevance score and the full markdown
writeup, to avoid a second round-trip per opportunity.
"""

import os
import re
import json
import datetime
import requests


TREX_CONTEXT = """\
TReX is an electronic-warfare product from BlackHorse Solutions, a Parsons \
company. Its core capabilities are automated electromagnetic spectrum sensing, \
RF signal detection and characterization, signals intelligence (SIGINT), and \
machine-learning-driven / cognitive electronic warfare (electronic attack, \
support, and protection). It operates across the electromagnetic spectrum \
operations (EMSO) and cyber-electromagnetic activities (CEMA) mission space, \
supporting DoD and Intelligence Community customers with autonomous detection, \
identification, geolocation, and defeat of complex communications signals."""


def _build_prompt(rec: dict) -> str:
    return f"""\
{TREX_CONTEXT}

Below is a U.S. federal contract opportunity from SAM.gov. Assess how well \
TReX's capabilities fit this opportunity.

Opportunity:
- Title: {rec.get('title')}
- Agency: {rec.get('agency')}
- Notice type: {rec.get('type')}
- NAICS: {rec.get('naics')}
- Solicitation #: {rec.get('solicitation_number')}
- Posted: {rec.get('posted_date')}
- Response deadline: {rec.get('response_deadline')}
- Link: {rec.get('ui_link')}
- Description: {(rec.get('description_text') or '(no description text retrieved)')[:6000]}

Respond with ONLY a JSON object, no surrounding prose, of the form:
{{
  "score": <integer 0-100, how strongly TReX fits this opportunity>,
  "fit_markdown": "<a one-page markdown writeup: a short summary of the \
opportunity, an explanation of how TReX's specific capabilities map to the \
requirement, a suggested approach/positioning, and any risks or unknowns. \
Be concrete and honest; if the fit is weak, say so.>"
}}"""


def _extract_json(text: str) -> dict:
    """Pull the first JSON object out of a model response."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("no JSON object found in model response")
    return json.loads(match.group(0))


def _call_claude(prompt: str, config: dict, api_key: str) -> str:
    resp = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": config["ai"]["claude_model"],
            "max_tokens": config["ai"]["max_tokens"],
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["content"][0]["text"]


def _call_openai(prompt: str, config: dict, api_key: str) -> str:
    resp = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": config["ai"]["openai_model"],
            "max_tokens": config["ai"]["max_tokens"],
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def _template_doc(rec: dict, stage1: dict, reason: str) -> str:
    """Deterministic fallback doc. `reason` explains why no AI body is present."""
    matched = ", ".join(stage1.get("matched", [])) or "(none)"
    return f"""# {rec.get('title')}

> {reason} Keyword pre-filter only.

- **Agency:** {rec.get('agency')}
- **Notice type:** {rec.get('type')}
- **NAICS:** {rec.get('naics')}
- **Solicitation #:** {rec.get('solicitation_number')}
- **Posted:** {rec.get('posted_date')}
- **Response deadline:** {rec.get('response_deadline')}
- **SAM.gov link:** {rec.get('ui_link')}

## TReX relevance (keyword pre-filter)
Stage-1 score: **{stage1.get('score')}/100**. Matched signals: {matched}.

TReX delivers automated spectrum sensing, RF signal detection, SIGINT, and
ML-driven electronic warfare. Review the matched signals above against this
opportunity's scope to judge fit. Set an AI provider key for a full writeup.
"""


def evaluate_and_write(rec: dict, config: dict, stage1: dict) -> dict:
    """
    Returns {status, ai_score, ai_generated, markdown}, where status is:
      "ok"     — the AI call succeeded; ai_score is the model's relevance score
      "no_key" — no provider key configured; template doc, dev/no-AI mode
      "error"  — key present but the call failed; template doc + the error
    The caller decides what to keep based on status (see govcon.py): an "error"
    must not be silently kept, so a misconfigured/down provider can't flood the
    kept set the way it would if every fallback were treated as a keep.
    """
    provider = config["ai"]["provider"]
    key_env = "ANTHROPIC_API_KEY" if provider == "claude" else "OPENAI_API_KEY"
    api_key = os.environ.get(key_env)

    if not api_key:
        return {
            "status": "no_key",
            "ai_score": stage1["score"],
            "ai_generated": False,
            "markdown": _template_doc(rec, stage1, "Generated without AI (no provider key set)."),
        }

    prompt = _build_prompt(rec)
    try:
        raw = (_call_claude if provider == "claude" else _call_openai)(
            prompt, config, api_key
        )
        parsed = _extract_json(raw)
        score = int(parsed["score"])
        body = parsed["fit_markdown"]
    except Exception as exc:  # noqa: BLE001 — degrade gracefully, never crash the run
        doc = _template_doc(rec, stage1, f"AI generation failed: {exc}")
        return {"status": "error", "ai_score": stage1["score"],
                "ai_generated": False, "markdown": doc}

    header = (
        f"# {rec.get('title')}\n\n"
        f"- **Agency:** {rec.get('agency')}\n"
        f"- **Notice type:** {rec.get('type')}\n"
        f"- **NAICS:** {rec.get('naics')}\n"
        f"- **Solicitation #:** {rec.get('solicitation_number')}\n"
        f"- **Posted:** {rec.get('posted_date')}\n"
        f"- **Response deadline:** {rec.get('response_deadline')}\n"
        f"- **SAM.gov link:** {rec.get('ui_link')}\n"
        f"- **TReX relevance (AI):** {score}/100\n"
        f"- **Generated:** {datetime.date.today().isoformat()}\n\n"
        "---\n\n"
    )
    return {"status": "ok", "ai_score": score, "ai_generated": True,
            "markdown": header + body}
