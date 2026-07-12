# 📡 PULSE — Customer Intelligence Platform

[![Live App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://sagnikpaulfirstclub.streamlit.app)
[![daily-scrape](https://github.com/Sagnik0852/pulse/actions/workflows/daily_scrape.yml/badge.svg)](https://github.com/Sagnik0852/pulse/actions/workflows/daily_scrape.yml)
[![weekly-digest](https://github.com/Sagnik0852/pulse/actions/workflows/weekly_digest.yml/badge.svg)](https://github.com/Sagnik0852/pulse/actions/workflows/weekly_digest.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**Live customer & competitor intelligence for consumer brands, built at near-zero cost.**

🔗 **Live demo:** [sagnikpaulfirstclub.streamlit.app](https://sagnikpaulfirstclub.streamlit.app) — 9,000+ real Play Store reviews of FirstClub, Zepto, Blinkit, BigBasket & Swiggy Instamart, refreshed daily. *(The Ask-the-Data chat page is passcode-gated to limit API spend — code shared on request.)*

## What it does

**Layer 1 — real public data.** Scrapes Google Play reviews for a company and its competitors daily, tags complaint themes, benchmarks sentiment, detects emerging spikes, writes a Monday CEO digest with Claude, and answers free-form questions over the corpus.

**Layer 2 — internal-data capabilities** on clearly-badged synthetic data: RFM/KMeans segmentation, leakage-safe churn prediction (AUC 0.93), item-item recommendations, and AI-written per-segment win-back messaging.

## Sample findings (July 2026 data)

- **FirstClub has the lowest negative-review share of all five apps** — 16.2% vs Zepto's 41.4% — and delivery-speed complaints are just 5.6% of its negatives vs 10–16% for competitors: the quality-first positioning is measurably landing.
- **Refunds + support are quick-commerce's open wound** — ~32% of negative reviews industry-wide, the #1 complaint macro-theme. FirstClub is best-in-class at 17.8%.
- **The engine also finds the uncomfortable stuff:** FirstClub's own #1 complaint theme is app UX/stability at 27.5% of negatives (~2.5× category norm) — onboarding and cart-sync specifically.

## Engineering choices

**Cost:** ₹0 infrastructure (Streamlit Community Cloud + GitHub Actions free tier) · ≈ $1–2/month of Claude API. Sentiment = star ratings (the customer self-labels), theme tagging = keyword taxonomy first (~70–85% coverage), scikit-learn for all ML — Claude only touches what an LLM is irreplaceable for: labeling ambiguous reviews (Haiku, batched 50/call), the weekly digest, and the chat layer (Sonnet).

SQLite-in-repo instead of a hosted DB (single daily batch writer, read-only dashboard, data history versioned in git). GitHub Actions instead of an orchestrator (linear batch pipeline living next to its code). Synthetic-but-honest demo data instead of fabricated "real-looking" datasets.

## Run it for YOUR company in 10 minutes

1. Edit `config.yaml` — company name, brand color, Play Store ID, competitor IDs. That's the whole generalization layer.
2. `pip install -r requirements.txt`
3. `python scraper/play_store.py && python nlp/run_pipeline.py`
4. `python models/synth_data.py && python models/segments.py && python models/churn.py && python models/recommender.py`
5. `streamlit run app/Home.py`

## Deploy (free)

Push to GitHub → [share.streamlit.io](https://share.streamlit.io) → New app → entry point `app/Home.py` → add `ANTHROPIC_API_KEY` and `CHAT_PASSCODE` in Secrets. GitHub Actions handle the daily scrape and weekly digest (add `ANTHROPIC_API_KEY` under repo Settings → Secrets → Actions, then run the one-click `bootstrap-pipeline` workflow once).

## Structure

```
config.yaml          # the generalization layer — the only file that changes per company
scraper/             # Google Play review scraper -> SQLite
nlp/                 # taxonomy tagging, Claude batch labeling, aggregates, spike detection
models/              # synthetic data, segments, churn, recommender (demo layer)
llm/                 # CEO digest, ask-the-data chat, win-back copy
app/                 # Streamlit dashboard (7 pages)
.github/workflows/   # one-click bootstrap + daily scrape + weekly digest crons
data/                # SQLite DB + parquet outputs + digest archive (committed by CI)
```

---

*Independent project on public data. Not affiliated with FirstClub or any company shown.*
*Built by **Sagnik Paul** · BITS Pilani Hyderabad · [paul1sagnik@gmail.com](mailto:paul1sagnik@gmail.com)*
