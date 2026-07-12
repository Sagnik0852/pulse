import streamlit as st

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from common import COMPANY, footer

st.set_page_config(page_title="How it works", page_icon="🔧", layout="wide")
st.title("🔧 How it works — and how it runs for any consumer brand")

st.markdown(f"""
### Architecture
- **Data in (free):** Google Play reviews for {COMPANY} + 4 competitors, scraped daily by a
  GitHub Actions cron into SQLite. Synthetic order data powers the demo modules.
- **Processing (zero tokens by design):** sentiment comes from star ratings; theme tagging is a
  keyword taxonomy that catches 70–85% of reviews; segmentation, churn and recommendations are
  pure scikit-learn.
- **Claude is used only where an LLM is irreplaceable:** labeling the taxonomy's leftovers
  (batched, Haiku), the Monday digest, chat answers, and win-back copy (all cached).
- **Hosting:** Streamlit Community Cloud. **Total running cost ≈ $1–2/month.**

### Point it at your company in 10 minutes
Everything company-specific lives in one `config.yaml` — name, brand color, Play Store IDs,
competitor list. Change ~10 lines, re-run the scraper, redeploy. Same engine, any consumer brand.

### With internal data
The demo modules (segments, churn, win-back, recommendations) plug into a real order
warehouse in about a day — the feature pipeline maps directly onto an orders table.

---
**Sagnik Paul** · Dual Degree (Econ + Mech), BITS Pilani Hyderabad, 2027 · previously
product @ Coca-Cola India (500K+ MAU platform), PM Growth & Strategy @ Bharatversity ·
can intern up to 12 months straight, converting to full-time.
""")
footer()
