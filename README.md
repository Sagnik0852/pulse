# 📡 PULSE — Customer Intelligence Platform

**Live customer & competitor intelligence for consumer brands, built at near-zero cost.**

Layer 1 runs on **real public data**: it scrapes Google Play reviews for a company and its
competitors daily, tags complaint themes, benchmarks sentiment, detects emerging spikes,
writes a Monday CEO digest with Claude, and answers free-form questions over the corpus.

Layer 2 demonstrates **internal-data capabilities** on clearly-badged synthetic data:
RFM/KMeans segmentation, leakage-safe churn prediction, item-item recommendations, and
AI-written per-segment win-back messaging.

**Cost:** ₹0 infrastructure (Streamlit Community Cloud + GitHub Actions free tier) ·
≈ $1–2/month of Claude API. Sentiment = star ratings, theme tagging = keyword taxonomy
first (70–85% coverage), scikit-learn for all ML — Claude only touches what an LLM is
irreplaceable for.

## Run it for YOUR company in 10 minutes
1. Edit `config.yaml` — company name, brand color, Play Store ID, competitor IDs.
2. `pip install -r requirements.txt`
3. `python scraper/play_store.py && python nlp/run_pipeline.py`
4. `python models/synth_data.py && python models/segments.py && python models/churn.py && python models/recommender.py`
5. `streamlit run app/Home.py`

## Deploy (free)
Push to GitHub → share.streamlit.io → New app → entry point `app/Home.py` → add
`ANTHROPIC_API_KEY` and `CHAT_PASSCODE` in Secrets. GitHub Actions handle the daily
scrape and weekly digest (add `ANTHROPIC_API_KEY` under repo Settings → Secrets → Actions).

## Structure
```
config.yaml          # the generalization layer — the only file that changes per company
scraper/             # Google Play review scraper -> SQLite
nlp/                 # taxonomy tagging, Claude batch labeling, aggregates, spike detection
models/              # synthetic data, segments, churn, recommender (demo layer)
llm/                 # CEO digest, ask-the-data chat, win-back copy
app/                 # Streamlit dashboard (7 pages)
.github/workflows/   # daily scrape + weekly digest crons
```

*Independent project on public data. Not affiliated with any company shown.*
*Built by Sagnik Paul · BITS Pilani Hyderabad.*
