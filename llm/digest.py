"""Weekly CEO digest — one Sonnet call on precomputed aggregates (not raw reviews).

Run:  python llm/digest.py     (saves markdown into data/digests/)
"""
import datetime as dt
import json
import os
import sqlite3

import pandas as pd
import yaml
from anthropic import Anthropic

CFG = yaml.safe_load(open("config.yaml"))

PROMPT = """You write a Monday-morning customer intelligence digest for the {persona}.
The data below comes from public app-store reviews of {company} and competitors,
covering the most recent weeks.

Write exactly 5 bullets:
1. The headline shift for {company} this period.
2. The biggest competitor weakness {company} can exploit.
3. Any emerging complaint spike (or "no spikes this week").
4. One verbatim customer quote that matters (short).
5. One recommended action.

Max 130 words total. Plain, direct, specific numbers. No fluff, no marketing language.

DATA:
{data}"""


def gather_aggregates(con):
    out = {}
    for table in ["agg_weekly_sentiment", "agg_theme_share", "agg_spikes"]:
        try:
            df = pd.read_sql(f"SELECT * FROM {table}", con)
            out[table] = df.tail(120).to_dict(orient="records")
        except Exception:
            out[table] = []
    # 10 most recent low-rating reviews for color
    try:
        out["recent_negative_quotes"] = pd.read_sql(
            "SELECT app, rating, text FROM reviews WHERE rating <= 2 "
            "ORDER BY date DESC LIMIT 10", con).to_dict(orient="records")
    except Exception:
        out["recent_negative_quotes"] = []
    return out


def run():
    con = sqlite3.connect(CFG["paths"]["db"])
    data = gather_aggregates(con)
    if not data["agg_weekly_sentiment"]:
        print("[digest] no aggregate data yet — run scraper + pipeline first")
        return
    client = Anthropic()
    resp = client.messages.create(
        model=CFG["llm"]["digest_model"],
        max_tokens=600,
        messages=[{"role": "user", "content": PROMPT.format(
            persona=CFG["digest"]["recipient_persona"],
            company=CFG["company"]["name"],
            data=json.dumps(data, default=str)[:60000],
        )}],
    )
    text = resp.content[0].text
    os.makedirs(CFG["paths"]["digests_dir"], exist_ok=True)
    path = os.path.join(CFG["paths"]["digests_dir"], f"{dt.date.today().isoformat()}.md")
    with open(path, "w") as f:
        f.write(f"# Customer Intelligence Digest — {dt.date.today():%d %b %Y}\n\n{text}\n")
    print(f"[digest] saved {path}")


if __name__ == "__main__":
    run()
