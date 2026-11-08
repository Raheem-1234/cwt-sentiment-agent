"""Social posts — Source 1 of 2.

Priority:
1. Apify (if APIFY_TOKEN set) — runs the documented actor IDs in config.APIFY_ACTORS
   via the Apify API (run-sync-get-dataset-items).
2. StockTwits public API (REAL posts, no key needed) — via the ADR/OTC symbol
   mapped per ticker in config (HK/KRX tickers have no native StockTwits stream).
3. Clearly-labelled DEMO fallback: seeded realistic sample posts generated
   from the ticker's real news headlines, so the pipeline runs end-to-end
   with zero tokens. Demo posts are NEVER presented as real scraped posts.
"""
import hashlib, random
from datetime import datetime, timedelta, timezone
import requests

HEADERS = {"User-Agent": "Mozilla/5.0 (cwt-sentiment-agent)"}

def _seed_for(ticker):
    return int(hashlib.md5(("social"+ticker).encode()).hexdigest()[:8], 16) % (2**31)

def _apify(meta, days):
    from config import APIFY_TOKEN, APIFY_ACTORS
    actor = APIFY_ACTORS["twitter_search"].replace("/", "~")
    url = f"https://api.apify.com/v2/acts/{actor}/run-sync-get-dataset-items?token={APIFY_TOKEN}"
    payload = {"searchTerms": meta["keywords"], "maxItems": 30,
               "queryType": "Latest"}
    r = requests.post(url, json=payload, timeout=120)
    r.raise_for_status()
    out = []
    for it in r.json():
        text = it.get("text") or it.get("full_text") or ""
        if not text: continue
        out.append({"ticker": meta["ticker"], "source": f"Apify ({APIFY_ACTORS['twitter_search']})",
                    "text": text, "published": it.get("createdAt") or datetime.now(timezone.utc).isoformat(),
                    "likes": int(it.get("likeCount") or 0), "reposts": int(it.get("retweetCount") or 0),
                    "views": int(it.get("viewCount") or 0), "followers": int((it.get("author") or {}).get("followers") or 0)})
    return out

def _stocktwits(meta):
    sym = meta.get("stocktwits")
    if not sym: return []
    r = requests.get(f"https://api.stocktwits.com/api/2/streams/symbol/{sym}.json",
                     headers=HEADERS, timeout=15)
    if r.status_code != 200: return []
    out = []
    for m in r.json().get("messages", []):
        body = (m.get("body") or "").strip()
        if not body: continue
        out.append({"ticker": meta["ticker"], "source": f"StockTwits ({sym})",
                    "text": body, "published": m.get("created_at") or datetime.now(timezone.utc).isoformat(),
                    "likes": int(((m.get("likes") or {}).get("total") or 0)),
                    "reposts": 0, "views": 0,
                    "followers": int(((m.get("user") or {}).get("followers") or 0))})
    return out

_POS_T = ["Bullish on {name} here — momentum looks strong, earnings beat expectations. ${cashtag}",
          "{name} breaking out, volume picking up. Long and holding. ${cashtag}",
          "Good quarter from {name}, guidance raised. This rally has legs. ${cashtag}"]
_NEG_T = ["{name} looks weak here, sellers in control. Cutting my position. ${cashtag}",
          "Bearish on {name} — valuation stretched and sentiment turning. ${cashtag}",
          "{name} downgrade chatter everywhere, risky at these levels. ${cashtag}"]
_NEU_T = ["Watching {name} closely today, waiting for a clearer signal. ${cashtag}",
          "{name} sideways for now — support and resistance both holding. ${cashtag}"]

def _demo(meta, headlines):
    rng = random.Random(_seed_for(meta["ticker"]))
    now = datetime.now(timezone.utc)
    posts = []
    cashtag = "$" + meta["ticker"]
    templates = _POS_T * 3 + _NEG_T * 2 + _NEU_T * 2
    for i in range(28):
        t = rng.choice(templates)
        if headlines and rng.random() < 0.35:
            text = f"{rng.choice(headlines)} — watching {meta['name']} closely. {cashtag}"
        else:
            text = t.format(name=meta["name"], cashtag=cashtag)
        posts.append({"ticker": meta["ticker"], "source": "DEMO fallback (seeded sample posts)",
                      "text": text,
                      "published": (now - timedelta(hours=rng.randint(1, 24*10))).isoformat(),
                      "likes": rng.randint(0, 400), "reposts": rng.randint(0, 80),
                      "views": rng.randint(100, 20000), "followers": rng.randint(50, 50000)})
    return posts

def get_social_posts(meta, headlines=None, days=10):
    """Returns (posts, source_label)."""
    from config import APIFY_TOKEN
    if APIFY_TOKEN:
        try:
            posts = _apify(meta, days)
            if posts: return posts, "Apify"
        except Exception:
            pass
    try:
        posts = _stocktwits(meta)
        if len(posts) >= 3:
            return posts, "StockTwits public API (real posts, ADR symbol)"
    except Exception:
        pass
    return _demo(meta, headlines or []), "DEMO fallback (seeded sample posts from headlines)"
