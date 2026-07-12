"""Full NLP pipeline: taxonomy first pass -> Claude leftovers -> aggregates.

Run after every scrape:  python nlp/run_pipeline.py
Skips Claude gracefully if no API key is set (taxonomy still runs).
"""
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import yaml

from taxonomy import tag_db

CFG = yaml.safe_load(open("config.yaml"))


def build_aggregates(con):
    """Precompute weekly sentiment + theme tables so the dashboard is instant."""
    df = pd.read_sql("SELECT * FROM reviews", con, parse_dates=["date"])
    if df.empty:
        print("[aggregates] no reviews yet")
        return
    df["week"] = df["date"].dt.to_period("W").dt.start_time
    df["sentiment"] = df["rating"].map(lambda r: "negative" if r <= 2 else ("neutral" if r == 3 else "positive"))

    # weekly sentiment share per app
    weekly = (
        df.groupby(["app", "week", "sentiment"]).size().unstack(fill_value=0).reset_index()
    )
    for c in ["negative", "neutral", "positive"]:
        if c not in weekly:
            weekly[c] = 0
    weekly["total"] = weekly[["negative", "neutral", "positive"]].sum(axis=1)
    weekly["neg_share"] = (weekly["negative"] / weekly["total"]).round(4)
    weekly.to_sql("agg_weekly_sentiment", con, if_exists="replace", index=False)

    # theme share per app (negative reviews only — complaints)
    neg = df[df["sentiment"] == "negative"].copy()
    neg["themes"] = neg["themes"].fillna("other")
    exploded = neg.assign(theme=neg["themes"].str.split(",")).explode("theme")
    theme_share = (
        exploded.groupby(["app", "theme"]).size().rename("count").reset_index()
    )
    theme_share["share"] = theme_share.groupby("app")["count"].transform(lambda s: s / s.sum())
    theme_share.to_sql("agg_theme_share", con, if_exists="replace", index=False)

    # theme x week for spike detection
    exploded["week"] = exploded["date"].dt.to_period("W").dt.start_time
    tw = exploded.groupby(["app", "theme", "week"]).size().rename("count").reset_index()
    tw.to_sql("agg_theme_week", con, if_exists="replace", index=False)
    print(f"[aggregates] built for {df['app'].nunique()} apps, {len(df)} reviews")


def detect_spikes(con, z=2.0, trailing=8):
    """Flag themes whose latest-week count exceeds mean + z*std of trailing weeks."""
    tw = pd.read_sql("SELECT * FROM agg_theme_week", con, parse_dates=["week"])
    alerts = []
    for (app, theme), g in tw.groupby(["app", "theme"]):
        g = g.sort_values("week")
        if len(g) < trailing + 1:
            continue
        hist, latest = g["count"].iloc[-(trailing + 1):-1], g["count"].iloc[-1]
        if hist.std() > 0 and latest > hist.mean() + z * hist.std():
            alerts.append({"app": app, "theme": theme,
                           "latest": int(latest), "baseline": round(hist.mean(), 1),
                           "week": str(g["week"].iloc[-1].date())})
    pd.DataFrame(alerts).to_sql("agg_spikes", con, if_exists="replace", index=False)
    print(f"[spikes] {len(alerts)} alert(s)")


if __name__ == "__main__":
    con = sqlite3.connect(CFG["paths"]["db"])
    tag_db(con)
    if os.environ.get("ANTHROPIC_API_KEY"):
        import claude_label
        claude_label.label_leftovers(con)
    else:
        print("[pipeline] ANTHROPIC_API_KEY not set — skipping Claude labeling")
    build_aggregates(con)
    detect_spikes(con)
