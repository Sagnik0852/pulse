"""RFM + KMeans customer segmentation (zero tokens). DEMO DATA module."""
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

SEGMENT_ORDER = ["Champions", "Loyal Regulars", "Big-Basket Occasionals", "At-Risk", "Hibernating"]


def build_rfm(customers, orders, asof=None):
    asof = pd.Timestamp(asof) if asof else orders["date"].max()
    g = orders.groupby("customer_id").agg(
        last_order=("date", "max"),
        first_order=("date", "min"),
        frequency=("date", "count"),
        monetary=("amount", "sum"),
        aov=("amount", "mean"),
    ).reset_index()
    g["recency"] = (asof - g["last_order"]).dt.days
    g["tenure"] = (asof - g["first_order"]).dt.days.clip(lower=1)
    g["orders_per_month"] = g["frequency"] / (g["tenure"] / 30)
    return g.merge(customers[["customer_id", "member", "complained", "city"]], on="customer_id")


def segment(rfm, k=5):
    X = StandardScaler().fit_transform(np.log1p(rfm[["recency", "frequency", "monetary"]]))
    km = KMeans(n_clusters=k, n_init=10, random_state=42).fit(X)
    rfm = rfm.copy()
    rfm["cluster"] = km.labels_

    # Name clusters by centroid behavior: score = value & activity, penalize recency
    prof = rfm.groupby("cluster")[["recency", "frequency", "monetary"]].mean()
    prof["score"] = (
        prof["monetary"].rank() + prof["frequency"].rank() - prof["recency"].rank()
    )
    ranked = prof.sort_values("score", ascending=False).index.tolist()
    # Special-case: highest-monetary-but-low-frequency cluster = Big-Basket Occasionals
    name_map = {}
    for i, cl in enumerate(ranked):
        name_map[cl] = SEGMENT_ORDER[min(i, len(SEGMENT_ORDER) - 1)]
    bb = prof[(prof["monetary"].rank(ascending=False) <= 2) & (prof["frequency"].rank() <= 2)]
    for cl in bb.index:
        name_map[cl] = "Big-Basket Occasionals"
    rfm["segment"] = rfm["cluster"].map(name_map)
    return rfm


def segment_summary(rfm):
    s = rfm.groupby("segment").agg(
        customers=("customer_id", "count"),
        revenue=("monetary", "sum"),
        avg_recency=("recency", "mean"),
        avg_frequency=("frequency", "mean"),
        avg_monetary=("monetary", "mean"),
        member_share=("member", "mean"),
    ).round(1).reset_index()
    s["revenue_share"] = (s["revenue"] / s["revenue"].sum()).round(3)
    return s.sort_values("revenue", ascending=False)


if __name__ == "__main__":
    customers = pd.read_parquet("data/demo/customers.parquet")
    orders = pd.read_parquet("data/demo/orders.parquet")
    rfm = segment(build_rfm(customers, orders))
    rfm.to_parquet("data/demo/rfm_segments.parquet")
    print(segment_summary(rfm).to_string(index=False))
