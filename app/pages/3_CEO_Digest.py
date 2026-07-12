import glob
import os

import streamlit as st

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from common import CFG, footer

st.set_page_config(page_title="CEO Digest", page_icon="📬", layout="wide")
st.title("📬 Weekly CEO Digest")
st.caption("Auto-written every Monday by the pipeline from that week's review data. "
           "Zero manual effort — this page is what lands in the inbox.")

files = sorted(glob.glob(os.path.join(CFG["paths"]["digests_dir"], "*.md")), reverse=True)
if not files:
    st.info("No digest generated yet. Run `python llm/digest.py` after the pipeline.")
else:
    st.markdown(open(files[0]).read())
    if len(files) > 1:
        st.divider()
        st.subheader("Archive")
        for f in files[1:]:
            with st.expander(os.path.basename(f).replace(".md", "")):
                st.markdown(open(f).read())
footer()
