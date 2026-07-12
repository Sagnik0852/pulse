import pandas as pd
import plotly.express as px
import streamlit as st

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from common import COMPANY, load_reviews, load_table, footer, no_data_msg

st.set_page_config(page_title="Competitor Benchmark", page_icon="⚔️", layout="wide")
st.title("⚔️ Competitor Benchmark")

df = load_reviews()
if df.empty:
    no_data_msg(); st.stop()

st.subheader("Average rating trend (monthly)")
df["month"] = df["date"].dt.to_period("M").dt.start_time
trend = df.groupby(["app", "month"])["rating"].mean().reset_index()
fig = px.line(trend, x="month", y="rating", color="app", markers=True)
fig.update_layout(height=380, legend_title="")
st.plotly_chart(fig, use_container_width=True)

ts = load_table("agg_theme_share")
if not ts.empty:
    st.subheader(f"Where {COMPANY} wins / loses")
    pivot = ts.pivot_table(index="theme", columns="app", values="share", fill_value=0)
    if COMPANY in pivot.columns:
        others = [c for c in pivot.columns if c != COMPANY]
        pivot["competitor_avg"] = pivot[others].mean(axis=1)
        pivot["edge"] = pivot["competitor_avg"] - pivot[COMPANY]
        wins = pivot.sort_values("edge", ascending=False)
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**✅ {COMPANY} wins** (complained about less)")
            for theme, row in wins.head(3).iterrows():
                st.success(f"**{theme}** — {row[COMPANY]*100:.0f}% of {COMPANY} complaints "
                           f"vs {row['competitor_avg']*100:.0f}% competitor avg")
        with col2:
            st.markdown(f"**⚠️ {COMPANY} loses** (complained about more)")
            for theme, row in wins.tail(3).iloc[::-1].iterrows():
                st.error(f"**{theme}** — {row[COMPANY]*100:.0f}% of {COMPANY} complaints "
                         f"vs {row['competitor_avg']*100:.0f}% competitor avg")
        st.caption("**So what:** the left column is acquisition messaging; the right column "
                   "is the ops priority list.")
    st.subheader("Full theme comparison")
    fig2 = px.imshow(pivot.drop(columns=["competitor_avg", "edge"], errors="ignore").T,
                     text_auto=".0%", aspect="auto", color_continuous_scale="Reds")
    fig2.update_layout(height=340, coloraxis_showscale=False)
    st.plotly_chart(fig2, use_container_width=True)

footer()
