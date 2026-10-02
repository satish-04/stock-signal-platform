# Grok × X research workflow

Research only. There's no brokerage connection, and nothing here places, schedules, or recommends trades. Every stage stops for your review.

```
PICK COMPANY → COLLECT X POSTS → SENTIMENT + THEMES → COMPARE WITH YOUR MARKET DATA
            → BALANCED THESIS → SOURCE + RISK CHECK → HUMAN REVIEW
```

## What's in the folder

| File | What it does |
|---|---|
| `prompts/00–05_*.md` | Shared rules and Prompts 1–5, word for word. Edit these to change behaviour. |
| `RISK_CHECKLIST.md` | The 12-point checklist. The pipeline asks you each item. |
| `templates/posts_template.csv` | One row per post: `id,date,author,text,url,likes,reposts,replies` |
| `templates/market_data_template.csv` | Your prices and volume from outside X |
| `examples/HGRB_*.csv` | The fictional Helio Grid example, for practice |
| `build_packet.py` | **Path 1.** Turns your CSV into a paste-ready packet for grok.com. No key and no cost. |
| `search.py` | **Path 2.** Grok searches X with the `x_search` tool and saves `posts.csv` plus the raw citations. |
| `pipeline.py` | **Path 2.** Runs Prompts 2 → 5 through the API, with an approve / edit / re-run / stop gate after each one. Then it walks you through the checklist and compiles `REPORT.md`. |
| `lib.py` | Shared code: prompt loading, JSON extraction, and the automated pre-checks |

**Automated pre-checks** (`lib.precheck`) are plain pattern matching, with no AI involved. They flag:
- near-duplicate wording and look-alike handles (possible bots)
- rumor words ("hearing", "no confirmation")
- instruction-like text inside posts (prompt injection)
- URLs that the API didn't return as citations (possibly invented)
- missing engagement numbers, dates outside your window, and small samples

The flags go to you and into Prompt 5. They point you at things to look at; they don't decide anything.

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Path 1: manual (start here)

1. Copy `templates/posts_template.csv` and fill in 10–20 public posts you read yourself. Include some that disagree with each other, and at least two from accounts that identify themselves.
2. Optionally add your market data in the market template.
3. Build the packet:
   ```bash
   python build_packet.py --company "Acme Corp" --ticker ACME --range "2026-09-22 to 2026-09-28" \
       --posts my_posts.csv --market my_prices.csv
   ```
4. Open `output/ACME_manual/grok_packet.md`. Paste each block into a new Grok chat, one at a time. Review each answer before pasting the next block.
5. Open every URL. Delete any quote, count or label that doesn't match. Then go through `RISK_CHECKLIST.md`.

Practice run: `python build_packet.py --company "Helio Grid Robotics" --ticker HGRB --range "2026-09-22 to 2026-09-26" --posts examples/HGRB_posts.csv --market examples/HGRB_market.csv`

## Path 2: automated (xAI API; costs money)

```bash
cp .env.example .env        # add XAI_API_KEY from https://console.x.ai (never commit .env)

# optional: Prompt 1 search plan
python pipeline.py --company "Acme Corp" --ticker ACME --range "2026-09-21 to 2026-09-28" --plan-only

# 1) Grok searches X  ->  output/ACME_20260928/posts.csv + search_raw.json
python search.py --company "Acme Corp" --ticker ACME --from 2026-09-21 --to 2026-09-28

# 2) YOU open posts.csv, open every URL, delete what you can't verify

# 3) analysis with a human gate after every stage
python pipeline.py --company "Acme Corp" --ticker ACME --range "2026-09-21 to 2026-09-28" \
    --posts output/ACME_20260928/posts.csv --citations output/ACME_20260928/search_raw.json \
    --market my_prices.csv
```

Test the flow without spending anything by adding `--dry-run` to `pipeline.py`.

Each run folder contains:
- `02…05_*.md`: stage outputs. **If you edit a file and choose [e], your edited version is what the next stage sees.**
- `06_risk_checklist.md`: your answers to the checklist
- `review_log.jsonl`: a timestamped record of every approval, edit and stop
- `REPORT.md`: everything combined, headed "THIS IS NOT A DECISION"

**Costs:** see https://docs.x.ai/developers/models. You pay model tokens plus X Search at about $5 per 1,000 posts fetched. Keep date ranges narrow and `--max-posts` small.
**Model:** set `XAI_MODEL` in `.env` (default `grok-4.7`). If you get a "model not found" error, check the models page for the current name.

## Troubleshooting

| Problem | Fix |
|---|---|
| 401 / auth error | `XAI_API_KEY` is missing or wrong, or `.env` isn't in this folder |
| Zero posts / no citations | Widen the dates, drop the handle filters, use both the name and the ticker |
| "Grok returned prose, not JSON" | Re-run. The raw reply is saved in `search_raw.json`, so you can also copy posts by hand |
| Handle filter error | Max 20 handles. Use `--only-handles` or `--exclude-handles`, not both |
| `URL NOT IN API CITATIONS` flag | Treat the post as possibly invented. Open it, and delete it if it doesn't exist |
| A post URL won't open | It was deleted or made private. Drop it; an unverifiable post isn't evidence |

Sources: xAI [Tools overview](https://docs.x.ai/docs/guides/tools/overview) · [X Search](https://docs.x.ai/developers/tools/x-search) · [Citations](https://docs.x.ai/developers/tools/citations) · [Quickstart](https://docs.x.ai/developers/quickstart) · [Models & pricing](https://docs.x.ai/developers/models)

**Research only. Human review required before any decision.**

### Import a reviewed report into the stock-signal platform

After completing the human review and checklist, import `REPORT.md` from the platform
repository root. The reviewer name is recorded with the artifact; the platform uses it
as context for later signals, never as an order instruction.

```bash
python scripts/import_research.py grok-x-research/output/ACME_run_20260930/REPORT.md \
    --symbol ACME --provider grok-x-research --headline "Reviewed X research" --reviewer "your-name"
```
