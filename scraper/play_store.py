"""Scrape Google Play reviews for the company + competitors into SQLite.

Run:  python scraper/play_store.py
Safe to re-run daily — INSERT OR IGNORE dedupes on review_id.
"""
import sqlite3
import time

import yaml
from google_play_scraper import Sort, reviews

CFG = yaml.safe_load(open("config.yaml"))


def get_db() -> sqlite3.Connection:
    con = sqlite3.connect(CFG["paths"]["db"])
    con.execute(
        """CREATE TABLE IF NOT EXISTS reviews(
            review_id TEXT PRIMARY KEY,
            app       TEXT,
            source    TEXT,
            rating    INTEGER,
            text      TEXT,
            date      TEXT,
            themes    TEXT,
            labeled   INTEGER DEFAULT 0
        )"""
    )
    return con


def scrape_app(con, name, app_id, kw_filter=None):
    if not app_id or app_id == "REPLACE_ME":
        print(f"[skip] {name}: play_store_id not set in config.yaml")
        return 0
    target = CFG["scrape"]["reviews_per_app"]
    collected, token = [], None
    while len(collected) < target:
        try:
            batch, token = reviews(
                app_id,
                lang=CFG["scrape"]["lang"],
                country=CFG["scrape"]["country"],
                sort=Sort.NEWEST,
                count=200,
                continuation_token=token,
            )
        except Exception as e:
            print(f"[warn] {name}: scrape error ({e}); keeping what we have")
            break
        if not batch:
            break
        collected += batch
        time.sleep(1)  # be polite
        if token is None:
            break

    stored = 0
    for r in collected:
        txt = (r.get("content") or "").strip()
        if not txt:
            continue
        if kw_filter and kw_filter.lower() not in txt.lower():
            continue
        cur = con.execute(
            "INSERT OR IGNORE INTO reviews VALUES (?,?,?,?,?,?,?,0)",
            (r["reviewId"], name, "play", r["score"], txt, str(r["at"].date()), None),
        )
        stored += cur.rowcount
    con.commit()
    print(f"[ok] {name}: {stored} new reviews stored ({len(collected)} fetched)")
    return stored


if __name__ == "__main__":
    con = get_db()
    c = CFG["company"]
    total = scrape_app(con, c["name"], c["play_store_id"])
    for comp in CFG["competitors"]:
        total += scrape_app(con, comp["name"], comp["play_store_id"], comp.get("keyword_filter"))
    print(f"Done. {total} new reviews total.")
