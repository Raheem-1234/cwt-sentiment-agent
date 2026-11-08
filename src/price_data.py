"""Price data via yfinance (REAL prices when network is available).
Fallback: seeded synthetic OHLCV — clearly labelled, so the pipeline
still runs end-to-end offline. The mode is reported in the final report."""
import hashlib, time
import numpy as np
import pandas as pd

def _seed_for(ticker: str) -> int:
    return int(hashlib.md5(ticker.encode()).hexdigest()[:8], 16) % (2**31)

def synthetic_prices(meta: dict, days: int = 140) -> pd.DataFrame:
    rng = np.random.default_rng(_seed_for(meta["ticker"]))
    dates = pd.bdate_range(end=pd.Timestamp.utcnow().normalize(), periods=days)
    rets = rng.normal(0.0004, 0.018, size=days)
    close = meta["base_price"] * np.cumprod(1 + rets)
    open_ = close * (1 + rng.normal(0, 0.004, size=days))
    high = np.maximum(open_, close) * (1 + np.abs(rng.normal(0, 0.006, size=days)))
    low = np.minimum(open_, close) * (1 - np.abs(rng.normal(0, 0.006, size=days)))
    vol = rng.integers(1_000_000, 20_000_000, size=days).astype(float)
    return pd.DataFrame({"date": dates, "open": open_, "high": high, "low": low,
                         "close": close, "volume": vol})

def get_prices(meta: dict, days: int = 140):
    """Returns (df, mode). Uses Ticker.history (yf.download gets HTTP 429
    rate-limited on shared IPs); retries twice before falling back."""
    for attempt in range(3):
        try:
            import yfinance as yf
            df = yf.Ticker(meta["ticker"]).history(period="6mo", interval="1d", auto_adjust=False)
            if df is not None and len(df) >= 40:
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = [c[0] for c in df.columns]
                df = df.reset_index().rename(columns=str.lower)
                df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None)
                cols = [c for c in ["date", "open", "high", "low", "close", "volume"] if c in df.columns]
                df = df[cols].dropna(subset=["close"])
                if len(df) >= 40:
                    return df.tail(days).reset_index(drop=True), "real (yfinance)"
        except Exception:
            pass
        time.sleep(2)
    return synthetic_prices(meta, days), "synthetic fallback (offline / no data)"
