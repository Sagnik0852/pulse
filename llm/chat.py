"""Ask-the-Data chat: TF-IDF retrieval over reviews -> one Sonnet call.

No vector DB, no embeddings model — fits Streamlit Cloud's ~1GB RAM easily.
"""
import sqlite3

import pandas as pd
import yaml
from anthropic import Anthropic
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

CFG = yaml.safe_load(open("config.yaml"))

SYSTEM = """You answer questions about customers of {company} and its competitors
using ONLY the app-store reviews and stats provided. Quote short review snippets
sparingly with the app name. If the data cannot answer the question, say so
plainly instead of guessing. Be direct and specific. Max 200 words."""


def retrieve(question, df, k=30):
    vec = TfidfVectorizer(stop_words="english", max_features=5000)
    m = vec.fit_transform(df["text"])
    q = vec.transform([question])
    idx = cosine_similarity(q, m).ravel().argsort()[-k:][::-1]
    return df.iloc[idx]


def answer(question):
    con = sqlite3.connect(CFG["paths"]["db"])
    df = pd.read_sql("SELECT app, rating, date, text FROM reviews", con)
    if df.empty:
        return "No review data loaded yet — run the scraper first."
    top = retrieve(question, df)
    try:
        stats = pd.read_sql("SELECT * FROM agg_theme_share", con).to_string(index=False)
    except Exception:
        stats = "(no aggregates yet)"
    context = "\n".join(
        f"[{r.app} · {r.rating}★ · {r.date}] {r.text[:280]}" for r in top.itertuples())
    client = Anthropic()
    resp = client.messages.create(
        model=CFG["llm"]["chat_model"],
        max_tokens=500,
        thinking={"type": "disabled"},
        system=SYSTEM.format(company=CFG["company"]["name"]),
        messages=[{"role": "user", "content":
                   f"THEME STATS:\n{stats}\n\nRELEVANT REVIEWS:\n{context}\n\nQUESTION: {question}"}],
    )
    # models may emit thinking blocks before text — take only text blocks
    return "".join(b.text for b in resp.content if b.type == "text")
