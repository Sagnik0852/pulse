import os
import sys

import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from common import COMPANY, footer

st.set_page_config(page_title="Ask the Data", page_icon="💬", layout="wide")
st.title("💬 Ask the Data")
st.caption(f"Ask anything about what customers are saying about {COMPANY} and competitors. "
           "Answers come only from the review corpus — it says so if the data can't answer.")

# Passcode gate — protects the API key on a public URL
code = st.text_input("Access code", type="password")
expected = st.secrets.get("CHAT_PASSCODE", os.environ.get("CHAT_PASSCODE", ""))
if not expected:
    st.info("CHAT_PASSCODE not configured in secrets."); st.stop()
if code != expected:
    if code:
        st.error("Wrong code.")
    st.stop()

if "history" not in st.session_state:
    st.session_state.history = []
for role, msg in st.session_state.history:
    st.chat_message(role).write(msg)

q = st.chat_input("e.g. What do users hate about Blinkit's delivery that we can win on?")
if q:
    st.chat_message("user").write(q)
    os.environ.setdefault("ANTHROPIC_API_KEY", st.secrets.get("ANTHROPIC_API_KEY", ""))
    with st.spinner("Reading reviews..."):
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
        from llm.chat import answer
        try:
            a = answer(q)
        except Exception as e:
            a = f"Error: {e}"
    st.chat_message("assistant").write(a)
    st.session_state.history += [("user", q), ("assistant", a)]

footer()
