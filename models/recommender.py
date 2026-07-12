"""Product-level item-item co-occurrence recommender (zero tokens). DEMO."""
import pandas as pd


def cooccurrence(orders):
    """P(product B in basket | product A in basket), from real basket pairs."""
    counts = {}
    solo = {}
    for prods in orders["products"].str.split("|"):
        for a in prods:
            solo[a] = solo.get(a, 0) + 1
            for b in prods:
                if a != b:
                    counts[(a, b)] = counts.get((a, b), 0) + 1
    rows = [{"a": a, "b": b, "p": c / solo[a]} for (a, b), c in counts.items()]
    return pd.DataFrame(rows)


def recommend_for_customer(orders, customer_id, co, top_n=5):
    hist = orders[orders["customer_id"] == customer_id]
    if hist.empty:
        return [], []
    bought = set()
    for prods in hist["products"].str.split("|"):
        bought.update(prods)
    cand = co[co["a"].isin(bought) & ~co["b"].isin(bought)]
    if cand.empty:
        return sorted(bought), []
    scores = cand.groupby("b")["p"].sum().sort_values(ascending=False)
    return sorted(bought), scores.head(top_n).index.tolist()


def also_bought(co, product, top_n=5):
    g = co[co["a"] == product].sort_values("p", ascending=False)
    return g.head(top_n)[["b", "p"]]


if __name__ == "__main__":
    orders = pd.read_parquet("data/demo/orders.parquet")
    co = cooccurrence(orders)
    co.to_parquet("data/demo/cooccurrence.parquet")
    for cid in [7, 42, 4901]:
        hist, recs = recommend_for_customer(orders, cid, co)
        print(f"cust {cid}: {len(hist)} products bought -> recommend {recs}")
