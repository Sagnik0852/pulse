import json
import os
import sys

import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from common import CFG, demo_badge, footer

st.set_page_config(page_title="Recs & Win-back", page_icon="🧲", layout="wide")
st.title("🧲 Recommendations & Win-back")
demo_badge()

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

@st.cache_data
def load():
    orders = pd.read_parquet("data/demo/orders.parquet")
    co = pd.read_parquet("data/demo/cooccurrence.parquet")
    rfm = pd.read_parquet("data/demo/rfm_segments.parquet")
    return orders, co, rfm

try:
    orders, co, rfm = load()
except Exception:
    st.info("Run the models/ scripts first."); st.stop()

st.subheader("Product recommendations (item-item co-occurrence)")
cid = st.number_input("Customer ID", 1, int(orders["customer_id"].max()), 42)
from models.recommender import recommend_for_customer
hist, recs = recommend_for_customer(orders, int(cid), co)
c1, c2 = st.columns(2)
c1.markdown("**Has bought:**")
c1.write(", ".join(hist) if hist else "—")
c2.markdown("**Recommend next:**")
for r in recs:
    c2.success(r)
st.caption("**So what:** zero-ML-infra recommender from basket co-occurrence — the same "
           "signal powers 'frequently bought together' carousels and push targeting.")

st.subheader("AI win-back messaging (per segment)")
cache = os.path.join(CFG["paths"]["demo_dir"], "winback.json")
if os.path.exists(cache):
    data = json.load(open(cache))
    seg = st.selectbox("Segment", list(data))
    d = data[seg]
    st.markdown(f"**Push:** {d.get('push','')}")
    st.markdown(f"**WhatsApp:** {d.get('whatsapp','')}")
    st.markdown(f"**Timing:** {d.get('timing','')}")
else:
    st.info("Win-back copy not generated yet.")
    if st.button("Generate now (5 Claude calls, cached)"):
        os.environ.setdefault("ANTHROPIC_API_KEY", st.secrets.get("ANTHROPIC_API_KEY", ""))
        from models.segments import segment_summary
        from llm.winback import generate
        with st.spinner("Writing copy per segment..."):
            generate(segment_summary(rfm))
        st.rerun()

st.caption("**Loop closed:** identify (segments) → predict (churn) → act (win-back copy). "
           "That's the full retention engine.")
footer()
