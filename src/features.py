"""Feature engineering: daily UTC-aligned aggregation + technicals.

Support / Resistance: 20-day rolling high/low + classic pivot points.
RSI: 14-period. Momentum: 5d / 10d returns.
Historical daily sentiment: the real social/news window is only 10 days
(assignment scope). For model training over ~140 days we build a seeded
sentiment *proxy* series for the earlier period (persistent AR(1) noise,
documented in README) and overwrite the last 10 days with the REAL
aggregated sentiment. Price/technical features are real throughout
when yfinance data is available.
"""
import hashlib
import numpy as np
import pandas as pd

def _seed_for(ticker):
    return int(hashlib.md5(("feat"+ticker).encode()).hexdigest()[:8], 16) % (2**31)

def rsi(close: pd.Series, period=14):
    d = close.diff()
    gain = d.clip(lower=0).rolling(period).mean()
    loss = (-d.clip(upper=0)).rolling(period).mean()
    rs = gain / loss.replace(0, np.nan)
    return (100 - 100 / (1 + rs)).fillna(50.0)

def support_resistance(df: pd.DataFrame):
    last = df.iloc[-1]
    window = df.tail(20)
    resistance = float(window["high"].max())
    support = float(window["low"].min())
    pivot = (last["high"] + last["low"] + last["close"]) / 3
    r1 = 2 * pivot - last["low"]; s1 = 2 * pivot - last["high"]
    return {"support": round(support, 2), "resistance": round(resistance, 2),
            "pivot": round(float(pivot), 2), "s1": round(float(s1), 2), "r1": round(float(r1), 2)}

def daily_sentiment_series(posts_scored, news_scored, dates):
    """Aggregate scored posts+news to one row per date (UTC)."""
    rows = {}
    for p in posts_scored:
        d = pd.to_datetime(p["published"], utc=True).date()
        rows.setdefault(d, {"mentions": 0, "s_sum": 0.0, "ew_sum": 0.0, "w_sum": 0.0})
        w = 1 + np.log1p(max(p.get("likes", 0), 0) + max(p.get("reposts", 0), 0))
        rows[d]["mentions"] += 1; rows[d]["s_sum"] += p["sentiment"]
        rows[d]["ew_sum"] += p["sentiment"] * w; rows[d]["w_sum"] += w
    for n in news_scored:
        d = pd.to_datetime(n["published"], utc=True, errors="coerce")
        if pd.isna(d): continue
        d = d.date()
        rows.setdefault(d, {"mentions": 0, "s_sum": 0.0, "ew_sum": 0.0, "w_sum": 0.0})
        rows[d]["mentions"] += 1; rows[d]["s_sum"] += n["sentiment"]
        rows[d]["ew_sum"] += n["sentiment"]; rows[d]["w_sum"] += 1
    out = {}
    for d, r in rows.items():
        out[d] = {"mentions": r["mentions"],
                  "avg_sentiment": r["s_sum"] / max(r["mentions"], 1),
                  "ew_sentiment": r["ew_sum"] / max(r["w_sum"], 1)}
    return out

def build_features(meta, prices: pd.DataFrame, real_daily: dict) -> pd.DataFrame:
    df = prices.copy().sort_values("date").reset_index(drop=True)
    df["date"] = pd.to_datetime(df["date"])
    df["return_1d"] = df["close"].pct_change()
    df["return_5d"] = df["close"].pct_change(5)
    df["return_10d"] = df["close"].pct_change(10)
    df["rsi_14"] = rsi(df["close"])
    df["volatility_10d"] = df["return_1d"].rolling(10).std()
    df["volume_ma_ratio"] = df["volume"] / df["volume"].rolling(10).mean().replace(0, np.nan)
    # seeded sentiment proxy for full history, real values overwrite last days
    rng = np.random.default_rng(_seed_for(meta["ticker"]))
    proxy, val = [], 0.0
    for _ in range(len(df)):
        val = 0.75 * val + rng.normal(0, 0.22)
        proxy.append(float(np.clip(val, -0.9, 0.9)))
    df["sentiment"] = proxy
    df["mentions"] = rng.integers(3, 30, size=len(df)).astype(float)
    df["ew_sentiment"] = df["sentiment"]
    for i, row in df.iterrows():
        d = row["date"].date()
        if d in real_daily:
            df.at[i, "sentiment"] = real_daily[d]["avg_sentiment"]
            df.at[i, "ew_sentiment"] = real_daily[d]["ew_sentiment"]
            df.at[i, "mentions"] = real_daily[d]["mentions"]
    df["sentiment_3d"] = df["sentiment"].rolling(3).mean()
    df["mentions_3d"] = df["mentions"].rolling(3).mean()
    # targets: next-day (n+1)
    df["target_price_next"] = df["close"].shift(-1)
    df["target_dir_next"] = (df["target_price_next"] > df["close"]).astype(int)
    return df

FEATURE_COLS = ["sentiment", "ew_sentiment", "sentiment_3d", "mentions", "mentions_3d",
                "return_1d", "return_5d", "return_10d", "rsi_14", "volatility_10d", "volume_ma_ratio"]
