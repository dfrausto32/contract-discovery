# Contract Discovery

This repository hosts TReX opportunity-discovery tools (TReX is BlackHorse Solutions'
electronic-warfare product, a Parsons company). Each tool lives in its own folder and
has its own config, dedup database, and `opportunities/` output:

| Folder | Source | Schedule |
|---|---|---|
| [`govcon-discovery/`](govcon-discovery/) | GovCon API (delta sync) | **Daily, 03:00 UTC** (active) |
| [`trex-discovery/`](trex-discovery/) | SAM.gov API directly | Paused (manual dispatch only) |

Workflows live at the repository root in `.github/workflows/` and run from the default
branch. `govcon-daily.yml` runs the GovCon pipeline daily; `trex-daily.yml` is paused
(its schedule is commented out) and runs only on manual dispatch. See each folder's
files for tool-specific details (`govcon-discovery/govcon.py`, `trex-discovery/trex.py`).

The legacy LinkedIn construction-contact CLI also lives at the repository root and is
documented below.

---

# Construction Discovery CLI

A local Python CLI tool for systematic LinkedIn contact discovery in the construction industry. Built to support a weekly commitment of 8 manual outreach contacts — no scraping, no API abuse, fully LinkedIn TOS compliant.

---

## What it does

| Script | Purpose |
|---|---|
| `discovery.py` | Generates targeted LinkedIn search URLs based on your config and opens them in the browser |
| `tracker.py` | Logs contacts into a local SQLite database with relevance scoring |
| `planner.py` | Reads the database and produces a prioritized weekly plan of 8 contacts |

The database lives in `data/contacts.db` — it never leaves your machine unless you explicitly export or push it.

---

## Setup

### 1. Clone and create virtual environment

```bash
git clone <your-repo-url>
cd construction-discovery
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure your search parameters

Open `config.yaml` and update:

- **`geography.primary`** — your target metro (e.g. `"Denver, Colorado"`)
- **`geography.additional`** — nearby regions for expanded search
- **`titles`** — the three tiers are pre-populated; adjust to your market
- **`company_size`** — `sweet_spot_min/max` drives the highest scoring band
- **`construction_subtypes`** — reorder or adjust `weight` values to match your focus

### 3. Initialize the database

The database is created automatically the first time you run `tracker.py add`. There is nothing to run manually.

### 4. Verify setup

```bash
python discovery.py --help
python tracker.py --help
python planner.py --help
```

---

## Weekly workflow

### Monday: Generate search URLs

```bash
# Print URLs to terminal (review before opening)
python discovery.py people

# Open all people search URLs in browser tabs
python discovery.py people --open

# Open company searches to find leads through company pages
python discovery.py companies --open
```

Browse LinkedIn manually. When you find a relevant contact, leave the tab open and move to logging.

### Log each contact

```bash
python tracker.py add
```

You will be prompted for each field interactively. The relevance score (0–100) is calculated automatically from your config. You can override it with `--relevance-override <score>` if you know something the algorithm doesn't.

**Field guide for `tracker.py add`:**

| Field | What to enter |
|---|---|
| Full name | Exactly as shown on LinkedIn |
| Job title | Copy/paste from their profile — precision matters for scoring |
| Company name | Their current employer |
| Company size | LinkedIn shows this as a range (e.g. "11-50 employees") — use the midpoint or your estimate |
| Subtype | Pick the closest match from the list |
| Location | City, State |
| LinkedIn URL | The full profile URL |
| Notes | One sentence: what caught your attention about them |

### Generate your weekly plan

```bash
python planner.py week
```

This prints the top 8 uncontacted contacts by relevance score and marks them as `queued`. Run it once at the start of the week.

```bash
# Preview without changing any statuses
python planner.py week --dry-run
```

### Update contact status after outreach

```bash
# After sending a LinkedIn message
python tracker.py update <ID> --status contacted

# After they reply
python tracker.py update <ID> --status responded --notes "Interested in a call"

# After a discovery call
python tracker.py update <ID> --status interviewed

# Not the right fit
python tracker.py update <ID> --status not_relevant
```

### Check your week's progress

```bash
python planner.py progress
```

---

## All commands

### discovery.py

```bash
python discovery.py people           # Print people search URLs
python discovery.py people --open    # Open in browser
python discovery.py people --limit 5 # Limit to 5 URLs
python discovery.py companies        # Print company search URLs
python discovery.py companies --open
python discovery.py all --open       # Open all search URLs
```

### tracker.py

```bash
python tracker.py add                        # Log a new contact (interactive)
python tracker.py list                       # List all contacts by relevance
python tracker.py list --status discovered   # Filter by status
python tracker.py list --sort date           # Sort by discovery date
python tracker.py show <ID>                  # Full detail for one contact
python tracker.py update <ID> --status contacted
python tracker.py update <ID> --notes "Had a great call" --append-notes
python tracker.py update <ID> --relevance 90
python tracker.py stats                      # Pipeline summary
```

### planner.py

```bash
python planner.py week              # Generate this week's plan
python planner.py week --dry-run    # Preview only, no status changes
python planner.py week --count 5    # Plan fewer than 8 contacts
python planner.py week --discord    # Also send to Discord (requires env var)
python planner.py progress          # This week's outreach progress
python planner.py send-discord --message "Test message"  # Test Discord
```

---

## Relevance scoring

Scores are calculated automatically on `tracker.py add`. Higher score = outreach sooner.

| Factor | Max points |
|---|---|
| Title: Owner/Founder/President | 35 |
| Title: VP/Director/GM/Operations | 22 |
| Title: PM/Superintendent/Estimator | 12 |
| Company size 5–50 employees | 30 |
| Company size 51–200 employees | 18 |
| Company size 2–4 employees | 15 |
| Subtype weight (GC=10, Sub=7, etc.) | 0–20 |
| Primary geography match | 15 |
| Secondary geography match | 8 |
| **Total possible** | **100** |

Adjust the weights in `config.yaml` to tune the algorithm to your market.

---

## Contact status pipeline

```
discovered → queued → contacted → responded → interviewed
                                             ↘ not_relevant
                              ↘ no_response
```

- **discovered** — logged, not yet scheduled
- **queued** — selected for this week's outreach
- **contacted** — message sent
- **responded** — they replied
- **interviewed** — discovery call completed
- **not_relevant** — disqualified
- **no_response** — contacted, no reply after follow-up window

---

## Discord integration (current + planned)

### Current (manual trigger)

Send the weekly plan to Discord on demand:

```bash
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."
python planner.py week --discord
```

Get a webhook URL from your Discord server: **Server Settings → Integrations → Webhooks → New Webhook**.

### Planned: GitHub Actions automation

The system is structured to support automated weekly delivery via GitHub Actions. When you're ready to enable this:

1. Add `DISCORD_WEBHOOK_URL` as a GitHub Actions secret in your repository settings.
2. Create `.github/workflows/weekly-plan.yml` with a scheduled trigger (`cron: '0 8 * * 1'` for Monday 8am UTC).
3. The workflow installs dependencies, runs `python planner.py week --discord`, and commits the updated database back to the repo.

**Note:** Committing the database to GitHub means your contact list is stored in the repository. Keep the repo private if it contains real contact data.

A starter workflow template:

```yaml
# .github/workflows/weekly-plan.yml
name: Weekly Outreach Plan

on:
  schedule:
    - cron: '0 8 * * 1'   # Every Monday at 8am UTC
  workflow_dispatch:        # Manual trigger from GitHub UI

jobs:
  plan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: python planner.py week --discord
        env:
          DISCORD_WEBHOOK_URL: ${{ secrets.DISCORD_WEBHOOK_URL }}
      - name: Commit updated database
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add data/contacts.db
          git diff --cached --quiet || git commit -m "chore: update contacts.db [skip ci]"
          git push
```

---

## Git setup (first time)

```bash
git init
git add .
git commit -m "feat: initial construction discovery CLI"
git remote add origin <your-repo-url>
git push -u origin main
```

**Important:** `data/contacts.db` is in `.gitignore` by default. If you want to sync your database via GitHub (required for the GitHub Actions workflow), remove that line from `.gitignore` and keep the repo private.

---

## Project structure

```
construction-discovery/
├── .gitignore
├── README.md
├── config.yaml          ← Edit this first
├── discovery.py         ← Generate LinkedIn search URLs
├── tracker.py           ← Log and manage contacts
├── planner.py           ← Weekly prioritized action plan
├── requirements.txt
└── data/
    └── contacts.db      ← Auto-created on first use (gitignored by default)
```

---

## Tips

- **Log contacts the same day you find them.** Memory fades; notes don't.
- **One sentence of notes is enough.** "Small GC doing commercial TI in downtown Denver" beats an empty field.
- **Don't overthink the relevance score.** The algorithm gets you 80% of the way. Use `--relevance-override` for the gut-feel cases.
- **Run `planner.py progress` mid-week.** It keeps you honest on the 8-contact commitment.
- **The database compounds.** After 4–6 weeks you'll have enough pipeline to see response rate patterns by subtype and company size.

---

# SAM.gov TReX Opportunity Discovery

A second tool in this repo (independent of the LinkedIn workflow above) that pulls
federal contract opportunities from the **official SAM.gov Opportunities API** and
generates a per-contract writeup of how **TReX** — BlackHorse Solutions' (a Parsons
company) electronic-warfare / spectrum-sensing / signal-detection product — fits each
one. It runs daily via GitHub Actions, prioritizes the most recently posted notices,
and never repeats a contract.

## How it works

1. **Pull** — `sam_client.py` queries the SAM.gov Opportunities API v2 over a short
   posted-date window (default 3 days), one request per configured NAICS code, keeping
   only active pre-award notice types (Solicitation, Combined Synopsis, Presolicitation,
   Sources Sought), newest first.
2. **Dedup** — `store.py` records every evaluated notice in `data/trex_seen.db` keyed by
   SAM notice id, so contracts are never processed or written twice.
3. **Stage 1 (keywords)** — `relevance.py` scores each new notice from config-driven
   NAICS + keyword signals and drops obvious noise.
4. **Stage 2 (AI)** — `ai_fit.py` sends survivors to a pluggable AI provider (Claude by
   default, OpenAI optional) which returns a 0–100 relevance score **and** the fit
   writeup. Without an AI key it falls back to a deterministic template so the pipeline
   still runs.
5. **Write** — kept opportunities land in `opportunities/<posted-date>__<noticeId>/`
   (`README.md` + `opportunity.json`) and `opportunities/INDEX.md` is rebuilt newest-first.

## Setup

1. Generate a free API key from your SAM.gov **Account Details** page.
2. Add repository secrets: **`SAM_API_KEY`** (required) and one of
   **`ANTHROPIC_API_KEY`** / **`OPENAI_API_KEY`** (optional — selects the AI provider via
   `ai.provider` in `trex_config.yaml`).
3. Record when you activated the key so expiry can be tracked:
   `python trex.py set-key-date 2026-05-25` (commit the resulting `data/key_meta.json`).

## Commands

```bash
python trex.py run                 # daily pull + doc generation (used by CI)
python trex.py run --dry-run       # evaluate and print, write nothing
python trex.py health              # SAM.gov key liveness + days until expiry
python trex.py set-key-date DATE   # record key activation date
python trex.py list                # list kept opportunities, newest first
python trex.py stats               # evaluation counts by disposition
```

## Key health

SAM.gov API keys expire ~90 days after creation and the API does not expose the expiry
date. `trex.py health` runs a liveness probe (catching an expired/invalid key) and, using
the activation date in `data/key_meta.json`, reports days remaining — warning when fewer
than `key_health.warn_within_days` (default 10) are left. The daily workflow writes this
to the **GitHub Actions job summary** on every run.

## Automation

`.github/workflows/trex-daily.yml` runs at 08:00 UTC daily (and on manual dispatch):
checks key health, pulls + generates docs, then commits new opportunity folders, the
index, and the dedup DB back to the branch.

## Tuning

Everything lives in `trex_config.yaml` — NAICS codes, boost/include/exclude keywords,
score thresholds, notice types, lookback window, AI provider/model, and the key-expiry
warning threshold.
