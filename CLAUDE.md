# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository layout

Three independent tools live here:

| Folder | Tool | Source | Status |
|---|---|---|---|
| `govcon-discovery/` | GovCon opportunity discovery | GovCon API (delta sync) | **Active — daily at 03:00 UTC** |
| `trex-discovery/` | TReX SAM.gov discovery | SAM.gov Opportunities API v2 | Paused — manual dispatch only |
| Root (`discovery.py`, `tracker.py`, `planner.py`) | LinkedIn construction CLI | Local SQLite | Legacy / manual use |

Each pipeline folder is self-contained: its own config, dedup database (`data/`), and `opportunities/` output.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running the pipelines

### GovCon (`govcon-discovery/`)

```bash
cd govcon-discovery
export GOVCON_API_KEY=...
export OPENAI_API_KEY=...        # or ANTHROPIC_API_KEY

python govcon.py run             # incremental delta pull + doc generation
python govcon.py run --dry-run   # evaluate without writing or recording anything
python govcon.py run --full      # ignore saved sync state, use initial_lookback_days
python govcon.py run --since 2026-05-01T00:00:00Z  # explicit start timestamp
python govcon.py health          # verify API key liveness
python govcon.py reset-sync      # clear sync state so next run does full lookback
python govcon.py list            # list kept opportunities
python govcon.py stats           # counts by disposition (kept/skipped/excluded)
```

### TReX (`trex-discovery/`)

```bash
cd trex-discovery
export SAM_API_KEY=...
export OPENAI_API_KEY=...        # or ANTHROPIC_API_KEY

python trex.py run               # daily pull + doc generation
python trex.py run --dry-run     # evaluate without writing or recording
python trex.py run --lookback 30 # override lookback_days from config
python trex.py health            # SAM.gov key liveness + days until expiry
python trex.py set-key-date 2026-05-25  # record key activation date (for expiry tracking)
python trex.py list
python trex.py stats
```

SAM.gov API keys expire ~90 days after creation. Track the activation date with `set-key-date` and check `health` before assuming the key is valid.

### LinkedIn CLI (root)

```bash
python discovery.py people --open   # open LinkedIn people search URLs in browser
python tracker.py add               # log a new contact (interactive)
python tracker.py list
python planner.py week              # generate this week's top-8 outreach plan
python planner.py progress
```

## Pipeline architecture (both govcon and trex follow this pattern)

Each pipeline has four modules wired together by the CLI orchestrator:

```
*_client.py  →  relevance.py  →  ai_fit.py  →  store.py
   (fetch)      (stage 1:         (stage 2:      (dedup +
                 keyword/NAICS     AI score +      audit DB)
                 pre-filter)       writeup)
```

1. **`*_client.py`** — API client. `govcon_client.py` uses the GovCon delta endpoint (incremental, Bearer auth, pagination via offset); `sam_client.py` issues one query per NAICS code over a date window (API key in params, paginates too).
2. **`relevance.py`** — Stage 1 deterministic filter. Scores by NAICS match + boost/include keyword hits; records with `exclude_keywords` are dropped outright. Opportunities below `stage1_threshold` (default 25) never reach the AI.
3. **`ai_fit.py`** — Stage 2 AI scoring and writeup. Calls either Claude (`ANTHROPIC_API_KEY`) or OpenAI (`OPENAI_API_KEY`) based on `ai.provider` in the config. Returns `{ai_score, ai_generated, markdown}`. Falls back to a deterministic template when the key is absent. The govcon version distinguishes three statuses (`ok`, `no_key`, `error`); an `error` leaves the opportunity unrecorded so it retries next run rather than flooding the kept set.
4. **`store.py`** — SQLite dedup store (`data/*.db`). Every evaluated notice is recorded by `notice_id` with its disposition (`kept`, `skipped_stage1`, `skipped_ai`, `excluded`), preventing re-processing and re-spending AI tokens.

Kept opportunities land in `opportunities/<posted-date>__<noticeId>/` as `README.md` + `opportunity.json`. `opportunities/INDEX.md` is rebuilt after each run that kept at least one.

## Key differences between the two pipelines

- **GovCon** uses an incremental delta sync: the last `server_time` is persisted in `data/govcon_sync.json` and used as `since` on the next run. The sync state is only advanced if the run produced zero AI errors. The workflow also builds and deploys a GitHub Pages dashboard (`dashboard.py build`).
- **TReX / SAM.gov** uses a date-window query (default 3-day lookback) with one request per NAICS code. SAM.gov returns the description via a separate `description_link` fetch; govcon includes the body inline.

## Configuration

All tunable parameters live in `*_config.yaml` (never in code):
- `sam.*` / `govcon.*` — API endpoint, lookback window, NAICS codes, notice types, page size
- `relevance.*` — boost/include/exclude keywords, per-signal weights, `stage1_threshold`
- `ai.*` — `provider` (`"openai"` or `"claude"`), model name, `score_threshold`, `max_tokens`
- `output.dir` — where per-contract docs are written
- `key_health.*` (trex only) — key lifetime and warning threshold

## GitHub Actions

- **`govcon-daily.yml`** — runs daily at 03:00 UTC; supports `since` and `full` manual-dispatch inputs. Commits `opportunities/`, `data/govcon_seen.db`, and `data/govcon_sync.json` back to the `contract-discovery` branch, then deploys the dashboard to GitHub Pages.
- **`trex-daily.yml`** — schedule is commented out (paused); manual dispatch only with optional `lookback` override. Commits `opportunities/`, `data/trex_seen.db`, and `data/key_meta.json`.
- Required secrets: `GOVCON_API_KEY`, `SAM_API_KEY`, `OPENAI_API_KEY` / `ANTHROPIC_API_KEY`.
