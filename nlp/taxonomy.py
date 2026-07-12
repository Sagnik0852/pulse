"""Zero-token theme tagging via keyword taxonomy.

Catches ~70-85% of reviews for free. Claude only labels the leftovers.
"""
TAXONOMY = {
    "delivery":   ["late", "delay", "delivery boy", "rider", "hours", "never arrived",
                   "slow delivery", "on time", "fast delivery", "quick delivery"],
    "quality":    ["stale", "rotten", "expired", "fresh", "quality", "spoiled",
                   "damaged", "bad product", "premium"],
    "pricing":    ["expensive", "costly", "price", "overpriced", "cheap", "mrp",
                   "loot", "charges", "hidden charge", "surge"],
    "app_ux":     ["crash", "bug", "login", "otp", "hang", "slow app", "ui",
                   "update", "glitch", "not working", "app is"],
    "refunds":    ["refund", "return", "money back", "wallet", "not received",
                   "cancelled", "deducted"],
    "stock":      ["out of stock", "unavailable", "sold out", "not available",
                   "no stock", "items missing"],
    "service":    ["customer care", "customer service", "support", "rude",
                   "no response", "helpline", "chat support", "complaint"],
    "packaging":  ["packaging", "leaked", "spilled", "box", "sealed", "packed"],
    "membership": ["membership", "subscription", "fee", "pass", "plan", "renewal"],
}


def tag(text):
    """Return list of matched themes for a review text."""
    t = (text or "").lower()
    return [theme for theme, kws in TAXONOMY.items() if any(k in t for k in kws)]


def tag_db(con):
    """First-pass tag every unlabeled review in the DB. Returns (#tagged, #leftover)."""
    rows = con.execute(
        "SELECT review_id, text FROM reviews WHERE labeled = 0"
    ).fetchall()
    tagged = 0
    for rid, text in rows:
        themes = tag(text)
        if themes:
            con.execute(
                "UPDATE reviews SET themes = ?, labeled = 1 WHERE review_id = ?",
                (",".join(themes), rid),
            )
            tagged += 1
    con.commit()
    leftover = len(rows) - tagged
    print(f"[taxonomy] tagged {tagged}/{len(rows)} · {leftover} left for Claude")
    return tagged, leftover
