"""Second-pass theme labeling with Claude Haiku, batched 50 per call.

Only touches reviews the keyword taxonomy couldn't tag.
Cost: ~1,500 leftovers ≈ 30 calls ≈ well under $0.50 one-time.
"""
import json
import os
import sqlite3

import yaml
from anthropic import Anthropic

CFG = yaml.safe_load(open("config.yaml"))
THEMES = "delivery, quality, pricing, app_ux, refunds, stock, service, packaging, membership, other"

PROMPT = """You label quick-commerce app reviews with themes.
Allowed themes: {themes}.
Return ONLY a JSON array of EXACTLY {n} arrays; item i is the list of themes for review i.
Every review gets an entry, even if it's just ["other"]. No prose, no markdown fences.

Reviews:
{reviews}"""


def label_leftovers(con, max_batches=None):
    client = Anthropic()  # reads ANTHROPIC_API_KEY from env
    batch_size = CFG["llm"]["label_batch_size"]
    rows = con.execute(
        "SELECT review_id, text FROM reviews WHERE labeled = 0"
    ).fetchall()
    if not rows:
        print("[claude_label] nothing to label")
        return 0

    labeled = 0
    batches = [rows[i : i + batch_size] for i in range(0, len(rows), batch_size)]
    if max_batches:
        batches = batches[:max_batches]
    for bi, batch in enumerate(batches):
        # collapse whitespace/newlines inside reviews so the numbered list stays unambiguous
        numbered = "\n".join(f"{i+1}. {' '.join(t[:300].split())}" for i, (_, t) in enumerate(batch))
        try:
            resp = client.messages.create(
                model=CFG["llm"]["label_model"],
                max_tokens=1500,
                messages=[{"role": "user", "content": PROMPT.format(
                    themes=THEMES, n=len(batch), reviews=numbered)}],
            )
            raw = "".join(b.text for b in resp.content if b.type == "text")
            raw = raw.strip().removeprefix("```json").removesuffix("```").strip()
            parsed = json.loads(raw)
            if len(parsed) != len(batch):
                print(f"[warn] batch {bi}: length mismatch, skipping")
                continue
            for (rid, _), themes in zip(batch, parsed):
                clean = [t for t in themes if isinstance(t, str)] or ["other"]
                con.execute(
                    "UPDATE reviews SET themes = ?, labeled = 1 WHERE review_id = ?",
                    (",".join(clean), rid),
                )
                labeled += 1
            con.commit()
            print(f"[claude_label] batch {bi+1}/{len(batches)} done")
        except Exception as e:
            print(f"[warn] batch {bi}: {e} — skipping, will retry next run")
    return labeled


if __name__ == "__main__":
    con = sqlite3.connect(CFG["paths"]["db"])
    label_leftovers(con)
