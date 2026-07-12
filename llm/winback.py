"""Segment-level win-back copy — 1 Sonnet call per segment, cached to disk.

Token-saving design: copy is generated per SEGMENT (5 calls total), never
per customer. Regenerate only via the dashboard button.
"""
import json
import os

import pandas as pd
import yaml
from anthropic import Anthropic

CFG = yaml.safe_load(open("config.yaml"))
CACHE = os.path.join(CFG["paths"]["demo_dir"], "winback.json")

PROMPT = """Write win-back messaging for a segment of {company} ({tagline}) customers.

Segment: {segment}
Profile: {profile}

Return ONLY JSON: {{"push": "<push notification, max 20 words>",
"whatsapp": "<WhatsApp message, max 45 words, warm, no emoji spam>",
"timing": "<when + channel logic in one line>"}}"""


def generate(segment_summary_df, force=False):
    if os.path.exists(CACHE) and not force:
        return json.load(open(CACHE))
    client = Anthropic()
    out = {}
    for _, row in segment_summary_df.iterrows():
        seg = row["segment"]
        profile = (f"{int(row['customers'])} customers, avg recency {row['avg_recency']}d, "
                   f"avg {row['avg_frequency']} orders, avg spend ₹{row['avg_monetary']}, "
                   f"{round(row['member_share']*100)}% members")
        resp = client.messages.create(
            model=CFG["llm"]["digest_model"], max_tokens=300,
            messages=[{"role": "user", "content": PROMPT.format(
                company=CFG["company"]["name"], tagline=CFG["company"]["tagline"],
                segment=seg, profile=profile)}])
        raw = "".join(b.text for b in resp.content if b.type == "text")
        raw = raw.strip().removeprefix("```json").removesuffix("```").strip()
        try:
            out[seg] = json.loads(raw)
        except Exception:
            out[seg] = {"push": raw[:100], "whatsapp": "", "timing": ""}
    os.makedirs(CFG["paths"]["demo_dir"], exist_ok=True)
    json.dump(out, open(CACHE, "w"), indent=2)
    return out
