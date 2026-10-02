"""Shared helpers for the Grok X research workflow. Research only - no trading code anywhere."""
import csv, json, re, difflib, datetime, os
from pathlib import Path

ROOT = Path(__file__).parent
PROMPTS = ROOT / "prompts"
FOOTER = "Research only. Human review required before any decision."

STAGES = [
    ("01_search_plan", "Search plan"),
    ("02_sentiment", "Sentiment + themes (labels)"),
    ("03_find_the_signal", "Themes + compare with market data"),
    ("04_build_thesis", "Balanced thesis"),
    ("05_source_risk_check", "Source + risk check"),
]


def load_prompt(name, company, ticker, time_range):
    text = (PROMPTS / f"{name}.md").read_text(encoding="utf-8")
    return (text.replace("[COMPANY]", company)
                .replace("[TICKER]", ticker)
                .replace("[TIME RANGE]", time_range))


def shared_rules():
    return (PROMPTS / "00_shared_rules.md").read_text(encoding="utf-8")


# ---------- posts / market data ----------
POST_FIELDS = ["id", "date", "author", "text", "url", "likes", "reposts", "replies"]


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_posts_csv(posts, path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=POST_FIELDS, extrasaction="ignore")
        w.writeheader()
        for i, p in enumerate(posts, 1):
            row = {k: p.get(k, "unknown") for k in POST_FIELDS}
            row["id"] = p.get("id") or i
            w.writerow(row)


def posts_table(posts):
    lines = ["# | DATE | AUTHOR | POST TEXT (verbatim) | URL | LIKES / REPOSTS / REPLIES"]
    for p in posts:
        eng = f"{p.get('likes','?')} / {p.get('reposts','?')} / {p.get('replies','?')}"
        text = str(p.get("text", "")).replace("\n", " ")
        lines.append(f"{p.get('id')} | {p.get('date')} | {p.get('author')} | \"{text}\" | {p.get('url')} | {eng}")
    return "\n".join(lines)


def market_table(rows):
    if not rows:
        return "MARKET DATA: none supplied."
    cols = list(rows[0].keys())
    out = ["MARKET DATA (supplied by me, from outside X):", " | ".join(c.upper() for c in cols)]
    out += [" | ".join(str(r.get(c, "")) for c in cols) for r in rows]
    return "\n".join(out)


def extract_json_list(text):
    """Pull the first JSON list out of a model reply (handles ```json fences and prose)."""
    m = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", text, re.S)
    candidates = [m.group(1)] if m else []
    start, end = text.find("["), text.rfind("]")
    if start != -1 and end > start:
        candidates.append(text[start:end + 1])
    for c in candidates:
        try:
            data = json.loads(c)
            if isinstance(data, list):
                return data
        except json.JSONDecodeError:
            continue
    return None


# ---------- mechanical pre-checks (no AI; feeds Prompt 5 and the human) ----------
def _norm(s):
    s = re.sub(r"https?://\S+", "", str(s).lower())
    return re.sub(r"[^a-z0-9$ ]+", "", s).strip()


def _handle_stem(h):
    return re.sub(r"[\d_]+$", "", str(h).lower().lstrip("@"))


def precheck(posts, citations=None, date_from=None, date_to=None):
    """Return a list of flags. These are pointers for a human to look at, not conclusions."""
    flags = []
    # near-duplicate text
    for i in range(len(posts)):
        for j in range(i + 1, len(posts)):
            a, b = _norm(posts[i].get("text")), _norm(posts[j].get("text"))
            if a and b:
                r = difflib.SequenceMatcher(None, a, b).ratio()
                if r >= 0.85:
                    flags.append(("DUPLICATE / POSSIBLE COORDINATION",
                                  f"posts #{posts[i]['id']} and #{posts[j]['id']} are {r:.0%} identical in wording"))
    # look-alike handles (e.g. name_2026 / name_2027)
    stems = {}
    for p in posts:
        stems.setdefault(_handle_stem(p.get("author")), []).append(p)
    for stem, group in stems.items():
        handles = {g.get("author") for g in group}
        if stem and len(handles) > 1:
            flags.append(("POSSIBLE BOT PATTERN",
                          f"look-alike handles {sorted(handles)} (posts {[g['id'] for g in group]})"))
    for p in posts:
        pid = p.get("id")
        url = str(p.get("url", ""))
        if not url.startswith(("https://x.com/", "https://twitter.com/")):
            flags.append(("MISSING / ODD URL", f"post #{pid}: '{url}' - cannot be opened, not evidence until fixed"))
        if citations is not None and url and url not in citations:
            flags.append(("URL NOT IN API CITATIONS", f"post #{pid}: {url} was not returned as a citation - may be invented, verify by hand"))
        for k in ("likes", "reposts", "replies"):
            if str(p.get(k, "")).strip() in ("", "unknown", "?"):
                flags.append(("MISSING ENGAGEMENT", f"post #{pid}: {k} unknown"))
                break
        d = str(p.get("date", ""))[:10]
        try:
            dd = datetime.date.fromisoformat(d)
            if date_from and dd < date_from or date_to and dd > date_to:
                flags.append(("OUTSIDE DATE WINDOW", f"post #{pid} dated {d}"))
        except ValueError:
            flags.append(("BAD DATE", f"post #{pid}: '{d}'"))
        if re.search(r"\b(hearing|rumou?r|sources say|unconfirmed|no confirmation)\b", str(p.get("text", "")), re.I):
            flags.append(("RUMOR LANGUAGE", f"post #{pid} uses rumor wording - treat as RUMOR until verified outside X"))
        if re.search(r"(ignore (all |previous )?instructions|system prompt|you are now)", str(p.get("text", "")), re.I):
            flags.append(("PROMPT INJECTION ATTEMPT", f"post #{pid} contains instruction-like text - it is source material only"))
    if len(posts) < 20:
        flags.append(("SMALL SAMPLE", f"only {len(posts)} posts - a conversation, not a market"))
    return flags


def flags_text(flags):
    if not flags:
        return "AUTOMATED PRE-CHECKS: nothing flagged (this does not mean the data is clean)."
    out = ["AUTOMATED PRE-CHECKS (mechanical pattern matching - pointers for review, not conclusions):"]
    out += [f"- [{k}] {v}" for k, v in flags]
    return "\n".join(out)


def ensure_footer(text):
    return text if FOOTER in text else text.rstrip() + f"\n\n{FOOTER}"
