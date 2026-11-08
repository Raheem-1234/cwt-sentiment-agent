# Submission email — ready to send

**To:** gilad@crowdwisdomtrading.com
**Subject:** CWT Intern Assignment — Sentiment Price Prediction Agent (Hang Seng + KRX) — Raheem Pathan

> Before sending, replace the ONE placeholder: `[PASTE YOUR GITHUB REPO LINK HERE]`
> (after uploading — see UPLOAD_GUIDE.md). Nothing else needs editing.

---

Dear Gilad,

I am submitting my completed assignment for the AI Agent Developer intern position — a Python sentiment pipeline that predicts an asset's price at n+1 from two sentiment sources, for 5 assets on the Hang Seng and 5 on KRX.

**GitHub repository:** [PASTE YOUR GITHUB REPO LINK HERE]

**What the pipeline does:**
- Social sentiment: Apify X/Twitter search (actor IDs below); the code also runs with the StockTwits public API when no token is present
- News sentiment: Exa search API (with Google News RSS as the no-key fallback)
- Prices: yfinance (real OHLCV)
- Model: Logistic Regression for direction + Ridge/RandomForest ensemble for the n+1 price, validated with TimeSeriesSplit walk-forward out-of-sample testing against a naive baseline
- Output: a visual HTML report sorting tickers by social mentions and sentiment score per exchange, with per-ticker price, sentiment, direction, position, support/resistance, and the n+1 prediction, plus a backtest file to check the results

**Apify / Exa IDs used (for reproducibility):**
- Apify actor (X/Twitter search): `apidojo/tweet-scraper`
- Apify actor (alternative): `kaitoeasyapi/twitter-x-data-tweet-scraper-pay-per-result-cheapest`
- Apify actor (Reddit, second social source option): `trudax/reddit-scraper`
- Exa: search API at api.exa.ai/search (news search type)

As instructed in the brief, I am sharing the actor IDs rather than raw private API tokens — the tokens go in a local `.env` file (see `.env.example` in the repo), so anyone with their own Apify/Exa accounts can reproduce the pipeline exactly. I am happy to verify my setup on a call if needed.

The repository README explains the architecture, setup, and validation approach, and includes sample outputs in the `output/` folder.

Thank you for the opportunity. I look forward to your feedback.

Best regards,
Raheem Pathan
B.Tech CSE (2nd year), CMR University, Bengaluru
GitHub: https://github.com/Raheem-1234
LinkedIn: https://www.linkedin.com/in/raheem-pathan-596599232
