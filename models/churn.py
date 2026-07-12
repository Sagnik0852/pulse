"""Churn prediction (zero tokens). DEMO DATA module.

Label definition (stated openly on the dashboard): a customer is churned
if they have placed no order in the last 45 days as of the snapshot date.
We train on features computed 45 days BEFORE the snapshot to avoid leakage.
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

CHURN_WINDOW = 45  # days

FEATURES = ["recency", "frequency", "monetary", "tenure", "avg_gap",
            "gap_trend", "member", "complained"]


def build_features(customers, orders, asof):
    """Features as of `asof` using only orders strictly before it."""
    hist = orders[orders["date"] < asof]
    g = hist.groupby("customer_id")

    feat = g.agg(last=("date", "max"), first=("date", "min"),
                 frequency=("date", "count"), monetary=("amount", "sum")).reset_index()
    feat["recency"] = (asof - feat["last"]).dt.days
    feat["tenure"] = (asof - feat["first"]).dt.days.clip(lower=1)

    def gap_stats(dates):
        d = np.sort(dates.values)
        if len(d) < 3:
            return pd.Series({"avg_gap": np.nan, "gap_trend": 0.0})
        gaps = np.diff(d).astype("timedelta64[D]").astype(float)
        half = len(gaps) // 2
        trend = gaps[half:].mean() - gaps[:half].mean()  # widening gaps = churn signal
        return pd.Series({"avg_gap": gaps.mean(), "gap_trend": trend})

    gs = g["date"].apply(gap_stats).unstack().reset_index()
    feat = feat.merge(gs, on="customer_id", how="left")
    feat["avg_gap"] = feat["avg_gap"].fillna(feat["tenure"])
    feat["gap_trend"] = feat["gap_trend"].fillna(0)
    return feat.merge(customers[["customer_id", "member", "complained"]], on="customer_id")


def build_labels(orders, asof):
    """Churned = no order in [asof, asof + 45d)."""
    future = orders[(orders["date"] >= asof) & (orders["date"] < asof + pd.Timedelta(days=CHURN_WINDOW))]
    active = set(future["customer_id"])
    return lambda cid: 0 if cid in active else 1


def train(customers, orders):
    snapshot = orders["date"].max() - pd.Timedelta(days=CHURN_WINDOW)
    X = build_features(customers, orders, snapshot)
    label_fn = build_labels(orders, snapshot)
    X["churned"] = X["customer_id"].map(label_fn)

    Xtr, Xte, ytr, yte = train_test_split(
        X[FEATURES], X["churned"], test_size=0.25, random_state=42, stratify=X["churned"])
    model = GradientBoostingClassifier(random_state=42).fit(Xtr, ytr)
    auc = roc_auc_score(yte, model.predict_proba(Xte)[:, 1])

    # Score everyone as of TODAY for the action table
    now_feat = build_features(customers, orders, orders["date"].max() + pd.Timedelta(days=1))
    now_feat["churn_prob"] = model.predict_proba(now_feat[FEATURES])[:, 1]

    importances = pd.DataFrame({"feature": FEATURES, "importance": model.feature_importances_}) \
        .sort_values("importance", ascending=False)
    return model, auc, now_feat, importances


def at_risk_table(now_feat, top=50):
    """Top at-risk HIGH-VALUE customers — the table a founder points retention spend at."""
    t = now_feat[(now_feat["churn_prob"] > 0.5) & (now_feat["recency"] < 60)]
    t = t.sort_values(["monetary"], ascending=False).head(top)
    return t[["customer_id", "churn_prob", "recency", "frequency", "monetary", "member"]].round(3)


if __name__ == "__main__":
    customers = pd.read_parquet("data/demo/customers.parquet")
    orders = pd.read_parquet("data/demo/orders.parquet")
    model, auc, scored, imp = train(customers, orders)
    scored.to_parquet("data/demo/churn_scores.parquet")
    imp.to_parquet("data/demo/churn_importances.parquet")
    print(f"AUC: {auc:.3f}")
    print(imp.to_string(index=False))
    print(f"\nAt-risk high-value (top 5):\n{at_risk_table(scored, 5).to_string(index=False)}")
