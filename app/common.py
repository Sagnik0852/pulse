"""Shared helpers for all dashboard pages."""
import os
import sqlite3

import pandas as pd
import streamlit as st
import yaml

CFG = yaml.safe_load(open("config.yaml"))
COMPANY = CFG["company"]["name"]
COLOR = CFG["company"]["color"]


def db():
    return sqlite3.connect(CFG["paths"]["db"])


@st.cache_data(ttl=3600)
def load_reviews():
    try:
        return pd.read_sql("SELECT * FROM reviews", db(), parse_dates=["date"])
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=3600)
def load_table(name):
    try:
        return pd.read_sql(f"SELECT * FROM {name}", db())
    except Exception:
        return pd.DataFrame()


def demo_badge():
    st.warning("🧪 **DEMO DATA** — this module runs on synthetic data to demonstrate "
               "capability. Plugged into a real order warehouse, it works the same "
               "way — integration is ~a day of work.")


def footer():
    st.divider()
    st.caption(f"Built by **Sagnik Paul** · BITS Pilani Hyderabad · Independent project "
               f"on public app-store review data · Not affiliated with {COMPANY} or any "
               f"company shown. · Swiggy Instamart reviews are keyword-filtered from the "
               f"main Swiggy app.")


def no_data_msg():
    st.info("No review data loaded yet. Run `python scraper/play_store.py` then "
            "`python nlp/run_pipeline.py`, commit `data/pulse.db`, and redeploy.")
