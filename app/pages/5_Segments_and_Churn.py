import pandas as pd
import plotly.express as px
import streamlit as st

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from common import demo_badge, footer

st.set_page_config(page_title="Segments & Churn", page_icon="🎯", layout="wide")
st.title("🎯 Segments & Churn Prediction")
demo_badge()


@st.cache_data
def load():
    rfm = pd.read_parquet("data/demo/rfm_segments.parquet", engine="fastparquet")
    scores = pd.read_parquet("data/demo/churn_scores.parquet", engine="fastparquet")
    imp = pd.read_parquet("data/demo/churn_importances.parquet", engine="fastparquet")
    return rfm, scores, imp

try:
    rfm, scores, imp = load()
except Exception:
    st.info("Run `python models/synth_data.py`, then segments.py and churn.py."); st.stop()

st.subheader("Customer segments (RFM + KMeans)")
summary = rfm.groupby("segment").agg(
    customers=("customer_id", "count"), revenue=("monetary", "sum"),
    avg_recency=("recency", "mean"), avg_orders=("frequency", "mean")).reset_index()
fig = px.treemap(summary, path=["segment"], values="revenue",
                 color="avg_recency", color_continuous_scale="RdYlGn_r",
                 hover_data=["customers", "avg_orders"])
fig.update_layout(height=380)
st.plotly_chart(fig, use_container_width=True)
st.caption("**So what:** box size = revenue, color = how recently they ordered. "
           "Big red boxes are revenue walking out the door.")
st.dataframe(summary.round(1), use_container_width=True, hide_index=True)

st.subheader("Churn model")
st.markdown("**Label:** no order in the last 45 days. Trained on features computed 45 days "
            "*before* the snapshot to avoid leakage. Honest caveat: recency dominates the "
            "model (as it does in most real retention models) — the value is in the *ranking* "
            "of who to save first, not the AUC.")
c1, c2 = st.columns([1, 2])
with c1:
    figi = px.bar(imp, x="importance", y="feature", orientation="h")
    figi.update_layout(height=320, yaxis_title="", xaxis_title="importance")
    st.plotly_chart(figi, use_container_width=True)
with c2:
    st.markdown("**Top at-risk high-value customers** — where retention spend goes first:")
    tbl = scores[(scores["churn_prob"] > 0.5) & (scores["recency"] < 60)] \
        .sort_values("monetary", ascending=False).head(25)
    st.dataframe(tbl[["customer_id", "churn_prob", "recency", "frequency", "monetary", "member"]]
                 .round(3), use_container_width=True, hide_index=True)

footer()
