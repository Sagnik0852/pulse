"""Synthetic membership quick-commerce dataset for the Layer-2 demo modules.

~5,000 customers, ~12 months of orders, with archetypes, churn behavior,
category preferences and product-level baskets baked in so downstream
models find real structure.
DEMO DATA ONLY — badged as such everywhere in the dashboard.
"""
import numpy as np
import pandas as pd

RNG = np.random.default_rng(42)

PRODUCTS = {
    "fruits_veg":   ["Bananas", "Avocados", "Spinach", "Tomatoes", "Alphonso Mangoes",
                     "Baby Potatoes", "Blueberries", "Coriander"],
    "dairy":        ["A2 Milk", "Greek Yogurt", "Paneer", "Salted Butter",
                     "Cheddar Cheese", "Farm Eggs"],
    "staples":      ["Basmati Rice 5kg", "Whole Wheat Atta", "Toor Dal",
                     "Cold-Pressed Groundnut Oil", "Rock Salt", "Jaggery"],
    "snacks":       ["Banana Chips", "Dark Chocolate", "Makhana", "Peanut Butter",
                     "Granola", "Instant Noodles", "Cold Coffee Can"],
    "personal_care":["Shampoo", "Face Wash", "Toothpaste", "Body Lotion", "Sunscreen"],
    "gourmet":      ["Sourdough Bread", "Burrata", "Extra Virgin Olive Oil",
                     "Kombucha", "Belgian Chocolate", "Trail Mix Imported"],
}
CATEGORIES = list(PRODUCTS)

ARCHETYPES = {
    # name: (share, orders/month λ, AOV mean, AOV sd, churn hazard/month, member prob, cat weights)
    "family_weekly":   (0.30, 4.5, 850, 250, 0.02, 0.75, [.30, .25, .25, .10, .07, .03]),
    "gourmet_premium": (0.12, 3.0, 1600, 500, 0.03, 0.85, [.15, .15, .10, .10, .10, .40]),
    "convenience":     (0.28, 2.2, 420, 150, 0.06, 0.35, [.10, .15, .10, .45, .15, .05]),
    "trial_user":      (0.20, 1.0, 350, 120, 0.18, 0.10, [.20, .15, .20, .30, .10, .05]),
    "bulk_monthly":    (0.10, 1.2, 2100, 600, 0.04, 0.60, [.15, .10, .55, .05, .10, .05]),
}


def generate(n_customers=5000, months=12, end="2026-06-30"):
    end_date = pd.Timestamp(end)
    start_date = end_date - pd.DateOffset(months=months)

    names, shares = list(ARCHETYPES), [a[0] for a in ARCHETYPES.values()]
    custs, orders = [], []
    for cid in range(1, n_customers + 1):
        arch = RNG.choice(names, p=shares)
        _, lam, aov_mu, aov_sd, hazard, member_p, cat_w = ARCHETYPES[arch]
        member = RNG.random() < member_p
        complained = RNG.random() < 0.06
        joined = start_date + pd.Timedelta(days=int(RNG.integers(0, months * 30 - 30)))

        # each customer favors a stable subset of products within their categories
        fav = {c: RNG.choice(PRODUCTS[c], size=min(3, len(PRODUCTS[c])), replace=False)
               for c in CATEGORIES}

        h = hazard * (2.0 if complained else 1.0) * (0.6 if member else 1.0)
        churn_month = next((m for m in range(months) if RNG.random() < h), None)
        active_end = end_date if churn_month is None else min(
            end_date, joined + pd.DateOffset(months=churn_month + 1))

        t = joined
        while t < active_end:
            t = t + pd.Timedelta(days=float(max(1, RNG.exponential(30 / lam))))
            if t >= active_end:
                break
            n_items = int(RNG.integers(2, 8))
            cats = RNG.choice(CATEGORIES, size=n_items, p=cat_w)
            items = []
            for c in cats:
                pool = fav[c] if RNG.random() < 0.7 else PRODUCTS[c]
                items.append(str(RNG.choice(pool)))
            amount = max(120, RNG.normal(aov_mu, aov_sd))
            orders.append({"customer_id": cid, "date": t.normalize(),
                           "amount": round(float(amount), 0),
                           "categories": ",".join(sorted(set(cats))),
                           "products": "|".join(sorted(set(items)))})
        custs.append({"customer_id": cid, "archetype": arch, "member": int(member),
                      "complained": int(complained), "joined": joined.normalize(),
                      "city": RNG.choice(["Bengaluru", "Mumbai", "Delhi NCR", "Hyderabad"],
                                          p=[.45, .25, .18, .12])})
    return pd.DataFrame(custs), pd.DataFrame(orders)


if __name__ == "__main__":
    import os
    os.makedirs("data/demo", exist_ok=True)
    c, o = generate()
    c.to_parquet("data/demo/customers.parquet")
    o.to_parquet("data/demo/orders.parquet")
    print(f"customers: {len(c)}  orders: {len(o)}")
