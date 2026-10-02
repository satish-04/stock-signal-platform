"""PATH 2, step 2: run Prompts 2 -> 5 through Grok with a HUMAN REVIEW STOP after each.

Every stage's output is saved as a file. You approve, edit, re-run, or stop. What
you approve (including your edits) is what the next stage sees. Nothing proceeds
without you, and nothing here can trade.

  python pipeline.py --company "Helio Grid Robotics" --ticker HGRB --range "2026-09-21 to 2026-09-28" \
      --posts output/HGRB_20260928/posts.csv --market my_prices.csv
  python pipeline.py ... --plan-only      # just Prompt 1 (search plan), before you collect
  python pipeline.py ... --dry-run        # no API calls; fake replies to test the flow
"""
import argparse, datetime, json, os, sys
from pathlib import Path
from dotenv import load_dotenv
from lib import (read_csv, posts_table, market_table, load_prompt, shared_rules, precheck,
                 flags_text, ensure_footer, STAGES, FOOTER, ROOT)

p = argparse.ArgumentParser()
p.add_argument("--company", required=True)
p.add_argument("--ticker", required=True)
p.add_argument("--range", required=True)
p.add_argument("--posts", help="posts CSV (from search.py or collected by hand)")
p.add_argument("--market", help="optional market data CSV you supply")
p.add_argument("--citations", help="search_raw.json from search.py (enables citation cross-check)")
p.add_argument("--out", help="output folder (default output/<TICKER>_run_<timestamp>)")
p.add_argument("--plan-only", action="store_true")
p.add_argument("--dry-run", action="store_true")
p.add_argument("--reviewer", default=os.getenv("USER", "human"))
a = p.parse_args()
if not a.plan_only and not a.posts:
    sys.exit("--posts is required (or use --plan-only)")

stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
out = Path(a.out or f"output/{a.ticker}_run_{stamp}")
out.mkdir(parents=True, exist_ok=True)
log_path = out / "review_log.jsonl"


def log(stage, decision, note=""):
    rec = {"time": datetime.datetime.now().isoformat(timespec="seconds"), "stage": stage,
           "decision": decision, "reviewer": a.reviewer, "note": note}
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")


# ---------- model ----------
class Grok:
    def __init__(self):
        load_dotenv()
        key = os.getenv("XAI_API_KEY")
        if not key or key == "your_key_here":
            sys.exit("XAI_API_KEY missing. Copy .env.example to .env (or use --dry-run).")
        from xai_sdk import Client
        self.client, self.model = Client(api_key=key), os.getenv("XAI_MODEL", "grok-4.7")
        self.cost = 0.0

    def ask(self, history):
        from xai_sdk.chat import system, user, assistant
        msgs = [system(shared_rules())]
        for role, text in history:
            msgs.append(user(text) if role == "user" else assistant(text))
        resp = self.client.chat.create(model=self.model, messages=msgs, temperature=0.2).sample()
        self.cost += float(getattr(resp, "cost_usd", 0) or 0)
        return resp.content


class Fake:
    cost = 0.0
    def ask(self, history):
        first = history[-1][1].splitlines()[0]
        return f"[DRY RUN - no API call]\nThis is where Grok's answer to '{first}' would appear.\n\n{FOOTER}"


model = Fake() if a.dry_run else Grok()


# ---------- human gate ----------
def gate(stage_key, title, path):
    """Returns approved text, or exits. Loops until the human approves."""
    while True:
        text = path.read_text(encoding="utf-8")
        print("\n" + "=" * 78 + f"\n{title.upper()}  ->  {path}\n" + "=" * 78)
        print(text[:6000] + ("\n... [truncated on screen - full text in file]" if len(text) > 6000 else ""))
        print("-" * 78)
        print("HUMAN REVIEW. Check every quote/label against the posts before approving.")
        choice = input("[a] approve & continue  [e] I edited the file - reload  [r] re-run this stage  [q] stop\n> ").strip().lower()
        if choice == "a":
            note = input("Optional note for the review log (Enter to skip): ").strip()
            log(stage_key, "approved", note)
            return path.read_text(encoding="utf-8")
        if choice == "e":
            log(stage_key, "edited_by_human")
            continue
        if choice == "r":
            log(stage_key, "rerun_requested")
            return None
        if choice == "q":
            log(stage_key, "stopped")
            sys.exit(f"Stopped at {title}. Everything so far is in {out}/")


def run_stage(history, stage_key, title, prompt):
    while True:
        print(f"\n>> Running {title} ...")
        reply = ensure_footer(model.ask(history + [("user", prompt)]))
        path = out / f"{stage_key}.md"
        path.write_text(reply, encoding="utf-8")
        approved = gate(stage_key, title, path)
        if approved is not None:
            return history + [("user", prompt), ("assistant", approved)]


fill = lambda key: load_prompt(key, a.company, a.ticker, a.range)
history = []
print(f"Output folder: {out}\nRESEARCH ONLY - this tool never places, schedules or recommends trades.")

if a.plan_only:
    run_stage(history, *STAGES[0], fill(STAGES[0][0]))
    print(f"\nSearch plan saved in {out}/. Use it to collect posts (by hand, or search.py).")
    sys.exit(0)

posts = read_csv(a.posts)
market = read_csv(a.market) if a.market else []
cites = None
if a.citations:
    cites = set(json.load(open(a.citations, encoding="utf-8")).get("citations", []))
flags = flags_text(precheck(posts, citations=cites))
(out / "00_prechecks.md").write_text(flags, encoding="utf-8")
print("\n" + flags)
if input("\nReviewed the posts & pre-checks, removed anything unverifiable? [y/N] ").strip().lower() != "y":
    log("00_material", "not_confirmed")
    sys.exit("Fix posts.csv first (open every URL), then re-run.")
log("00_material", "approved", f"{len(posts)} posts, {len(market)} market rows")

material = ("POSTS:\n" + posts_table(posts) + "\n\n" + market_table(market))
for i, (key, title) in enumerate(STAGES[1:]):
    prompt = fill(key)
    if i == 0:
        prompt = material + "\n\n" + prompt
    if key == "05_source_risk_check":
        prompt += "\n\n" + flags
    history = run_stage(history, key, title, prompt)

# ---------- risk checklist, answered by the human ----------
print("\n" + "=" * 78 + "\nRISK CHECKLIST - answer each yourself (y = checked / n = not yet), optional note\n" + "=" * 78)
items = [l[6:].strip() for l in (ROOT / "RISK_CHECKLIST.md").read_text(encoding="utf-8").splitlines() if l.startswith("- [ ]")]
answers = []
for it in items:
    ans = input(f"\n{it}\n  [y/n] ").strip().lower() == "y"
    note = input("  note: ").strip()
    answers.append((it, ans, note))
ck = ["# Risk checklist (answered by human)", ""] + [f"- [{'x' if ok else ' '}] {it}" + (f"\n  - note: {n}" if n else "") for it, ok, n in answers]
open_items = sum(1 for _, ok, _ in answers if not ok)
(out / "06_risk_checklist.md").write_text("\n".join(ck), encoding="utf-8")
log("06_checklist", "completed", f"{open_items} unchecked")

# ---------- final report ----------
sections = [f"# Research file — {a.company} ({a.ticker}), {a.range}",
            f"_Compiled {datetime.datetime.now():%Y-%m-%d %H:%M}. Reviewer: {a.reviewer}. "
            f"Posts: {len(posts)}. Market rows: {len(market)}. Unchecked risk items: {open_items}._",
            "\n> **THIS IS NOT A DECISION.** Research only. Human review required before any decision.\n"]
for f in ["00_prechecks", "02_sentiment", "03_find_the_signal", "04_build_thesis", "05_source_risk_check", "06_risk_checklist"]:
    fp = out / f"{f}.md"
    if fp.exists():
        sections += [f"\n---\n## {f}\n", fp.read_text(encoding="utf-8")]
(out / "REPORT.md").write_text("\n".join(sections), encoding="utf-8")
log("07_report", "compiled")
print(f"\nDone. Full research file: {out}/REPORT.md   Review log: {log_path}")
if model.cost:
    print(f"Reported API cost this run: ${model.cost:.4f}")
if open_items:
    print(f"WARNING: {open_items} risk-checklist items are unchecked. Resolve them before forming any view.")
print(FOOTER)
