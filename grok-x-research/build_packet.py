"""PATH 1 helper (no API key, no cost): turn your hand-collected posts into a
copy-paste packet for grok.com - shared rules + your table + each prompt in order.

  python build_packet.py --company "Helio Grid Robotics" --ticker HGRB \
      --range "2026-09-22 to 2026-09-26" --posts examples/HGRB_posts.csv --market examples/HGRB_market.csv
"""
import argparse, os
from lib import (read_csv, posts_table, market_table, load_prompt, shared_rules,
                 precheck, flags_text, STAGES)

p = argparse.ArgumentParser()
p.add_argument("--company", required=True)
p.add_argument("--ticker", required=True)
p.add_argument("--range", required=True, help='e.g. "2026-09-22 to 2026-09-28"')
p.add_argument("--posts", required=True, help="CSV in templates/posts_template.csv format")
p.add_argument("--market", help="optional CSV in templates/market_data_template.csv format")
a = p.parse_args()

posts = read_csv(a.posts)
market = read_csv(a.market) if a.market else []
flags = flags_text(precheck(posts))
fill = lambda n: load_prompt(n, a.company, a.ticker, a.range)

outdir = f"output/{a.ticker}_manual"
os.makedirs(outdir, exist_ok=True)
path = f"{outdir}/grok_packet.md"
fence = "~~~~"
parts = [
    f"# Grok packet — {a.company} ({a.ticker}), {a.range}",
    "Open a NEW chat at grok.com. Paste each block in order. After each answer, STOP and read it "
    "against your posts before pasting the next block. Save each answer (copy into a file) as you go.\n",
    "## Block 1 — shared rules + your material (paste once)",
    fence, shared_rules(), "", "POSTS (collected by hand, public posts only):", posts_table(posts), "",
    market_table(market), fence,
    "\n**Before you continue:** does Grok's reply acknowledge the rules? If it starts analysing already, fine — read it.",
]
for n, (key, title) in enumerate(STAGES[1:], start=2):
    body = fill(key)
    if key == "05_source_risk_check":
        body += "\n\n" + flags
    parts += [f"\n## Block {n} — {title}", fence, body, fence,
              "\n☐ HUMAN REVIEW: every quote, count and label matches the posts? Anything that doesn't is deleted before you continue."]
parts += ["\n## Last step — open every URL",
          "Every quote, count and label Grok produced must match what you collected. Then run RISK_CHECKLIST.md.",
          "\n**Research only. Human review required before any decision.**"]
open(path, "w", encoding="utf-8").write("\n".join(parts))
print(f"Packet written: {path}")
print(flags)
