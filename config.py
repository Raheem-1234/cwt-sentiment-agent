"""Central config — tickers, exchanges, fallback prices, actor IDs.

NEVER put real tokens here. Tokens go in .env (see .env.example).
Actor IDs are public identifiers (not secrets) and are safe to share
for reproducibility — that is what CWT asks for in the submission.
"""
import os

try:
    from dotenv import load_dotenv  # optional
    load_dotenv()
except Exception:
    # Minimal .env loader (no extra dependency required)
    _env = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(_env):
        for line in open(_env, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

APIFY_TOKEN = os.environ.get("APIFY_TOKEN", "").strip()
EXA_API_KEY = os.environ.get("EXA_API_KEY", "").strip()

# Apify actor IDs (public, shareable). Documented for the submission email.
APIFY_ACTORS = {
    "twitter_search": "apidojo/tweet-scraper",          # X/Twitter search by keyword/cashtag
    "twitter_search_alt": "kaitoeasyapi/twitter-x-data-tweet-scraper-pay-per-result-cheapest",
    "reddit_search": "trudax/reddit-scraper",           # Reddit keyword search (2nd social source)
}

# ticker -> metadata. base_price is ONLY used by the synthetic offline fallback.
TICKERS = {
    "Hang Seng (HK)": [
        {"ticker": "0700.HK", "name": "Tencent Holdings", "currency": "HKD", "base_price": 620.0,
         "keywords": ["Tencent", "$0700.HK", "Tencent stock"], "stocktwits": "TCEHY"},
        {"ticker": "9988.HK", "name": "Alibaba Group", "currency": "HKD", "base_price": 145.0,
         "keywords": ["Alibaba", "$9988.HK", "Alibaba stock"], "stocktwits": "BABA"},
        {"ticker": "3690.HK", "name": "Meituan", "currency": "HKD", "base_price": 95.0,
         "keywords": ["Meituan", "$3690.HK", "Meituan stock"], "stocktwits": "MPNGY"},
        {"ticker": "1810.HK", "name": "Xiaomi Corporation", "currency": "HKD", "base_price": 48.0,
         "keywords": ["Xiaomi", "$1810.HK", "Xiaomi stock"], "stocktwits": "XIACY"},
        {"ticker": "2318.HK", "name": "Ping An Insurance", "currency": "HKD", "base_price": 52.0,
         "keywords": ["Ping An Insurance", "$2318.HK", "Ping An stock"], "stocktwits": "PNGAY"},
    ],
    "KRX (Korea)": [
        {"ticker": "005930.KS", "name": "Samsung Electronics", "currency": "KRW", "base_price": 72000.0,
         "keywords": ["Samsung Electronics", "$005930.KS", "Samsung stock"], "stocktwits": "SSNLF"},
        {"ticker": "000660.KS", "name": "SK Hynix", "currency": "KRW", "base_price": 210000.0,
         "keywords": ["SK Hynix", "$000660.KS", "SK Hynix stock"], "stocktwits": "HXSCL"},
        {"ticker": "035420.KS", "name": "NAVER Corporation", "currency": "KRW", "base_price": 210000.0,
         "keywords": ["NAVER", "$035420.KS", "Naver stock"], "stocktwits": "NHNCF"},
        {"ticker": "035720.KS", "name": "Kakao Corporation", "currency": "KRW", "base_price": 38000.0,
         "keywords": ["Kakao", "$035720.KS", "Kakao stock"], "stocktwits": "KKMMY"},
        {"ticker": "005380.KS", "name": "Hyundai Motor", "currency": "KRW", "base_price": 240000.0,
         "keywords": ["Hyundai Motor", "$005380.KS", "Hyundai Motor stock"], "stocktwits": "HYMTF"},
    ],
}

ALL_TICKERS = [t for ex in TICKERS.values() for t in ex]
HISTORY_DAYS = 140   # price history for model training
SOCIAL_DAYS = 10     # assignment: social scrape window = last 10 days
RANDOM_SEED = 42
