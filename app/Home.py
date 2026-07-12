import pandas as pd
import plotly.express as px
import streamlit as st

import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from common import COMPANY, COLOR, load_reviews, load_table, footer, no_data_msg

st.set_page_config(page_title=f"{COMPANY} Pulse", page_icon="📡", layout="wide")
st.title(f"📡 {COMPANY} Customer Intelligence")
st.caption("Voice of Customer · live from public app-store reviews, refreshed daily")

df = load_reviews()
if df.empty:
    no_data_msg()
    st.stop()

df["sentiment"] = df["rating"].map(lambda r: "negative" if r <= 2 else ("neutral" if r == 3 else "positive"))
mine = df[df["app"] == COMPANY]
comp = df[df["app"] != COMPANY]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Reviews analyzed", f"{len(df):,}")
if not mine.empty:
    c2.metric(f"{COMPANY} avg rating", f"{mine['rating'].mean():.2f}★",
              delta=f"{mine['rating'].mean() - comp['rating'].mean():+.2f} vs competitors")
    this_m = mine[mine["date"] >= mine["date"].max() - pd.Timedelta(days=30)] if not mine.empty else mine
    c3.metric(f"{COMPANY} negative share (30d)",
              f"{(this_m['sentiment'].eq('negative').mean() * 100):.0f}%" if len(this_m) else "—")
spikes = load_table("agg_spikes")
c4.metric("Active spike alerts", len(spikes))

st.subheader("Sentiment over time")
weekly = load_table("agg_weekly_sentiment")
if not weekly.empty:
    fig = px.line(weekly, x="week", y="neg_share", color="app",
                  labels={"neg_share": "negative review share", "week": ""})
    fig.update_layout(height=380, legend_title="")
    st.plotly_chart(fig, use_container_width=True)
    st.caption("**So what:** a falling negative share while competitors' rises is the "
               "cleanest public proof that the quality-first positioning is landing.")

st.subheader("What people complain about")
ts = load_table("agg_theme_share")
if not ts.empty:
    fig2 = px.bar(ts, x="theme", y="share", color="app", barmode="group",
                  labels={"share": "share of negative reviews"})
    fig2.update_layout(height=380, legend_title="")
    st.plotly_chart(fig2, use_container_width=True)

if not spikes.empty:
    st.subheader("⚠️ Emerging spikes")
    st.dataframe(spikes, use_container_width=True, hide_index=True)

with st.expander("🔍 Review explorer"):
    app_pick = st.selectbox("App", sorted(df["app"].unique()))
    sent_pick = st.multiselect("Sentiment", ["negative", "neutral", "positive"], default=["negative"])
    sub = df[(df["app"] == app_pick) & (df["sentiment"].isin(sent_pick))].sort_values("date", ascending=False)
    st.dataframe(sub[["date", "rating", "themes", "text"]].head(200),
                 use_container_width=True, hide_index=True)

footer()
