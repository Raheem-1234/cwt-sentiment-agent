"""News ingestion — Source 2 of 2.

Priority:
1. Exa API (if EXA_API_KEY set) — https://api.exa.ai/search
2. Google News RSS (REAL headlines, no key needed) — default in this build
3. Clearly-labelled demo headlines (last resort, offline)

Every item records its true source so the report is honest.
"""
import urllib.parse, xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
import requests

HEADERS = {"User-Agent": "Mozilla/5.0 (cwt-sentiment-agent)"}

def _exa(meta, days):
    from config import EXA_API_KEY
    r = requests.post("https://api.exa.ai/search",
        headers={"x-api-key": EXA_API_KEY, "Content-Type": "application/json"},
        json={"query": f"{meta['name']} stock {meta['ticker']}", "type": "news",
              "numResults": 8, "contents": {"text": False}},
        timeout=20)
    r.raise_for_status()
    out = []
    for it in r.json().get("results", []):
        out.append({"ticker": meta["ticker"], "source": "Exa",
                    "title": it.get("title") or "", "text": it.get("title") or "",
                    "published": it.get("publishedDate") or datetime.now(timezone.utc).isoformat(),
                    "url": it.get("url") or ""})
    return out

def _google_news_rss(meta, days):
    q = urllib.parse.quote(f"{meta['name']} stock")
    url = f"https://news.google.com/rss/search?q={q}+when:{days}d&hl=en-US&gl=US&ceid=US:en"
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    root = ET.fromstring(r.content)
    out = []
    for item in root.iter("item"):
        title = (item.findtext("title") or "").strip()
        pub = item.findtext("pubDate") or ""
        link = item.findtext("link") or ""
        try:
            dt = datetime.strptime(pub, "%a, %d %b %Y %H:%M:%S %Z").replace(tzinfo=timezone.utc)
            pub_iso = dt.isoformat()
        except Exception:
            pub_iso = datetime.now(timezone.utc).isoformat()
        if title:
            out.append({"ticker": meta["ticker"], "source": "Google News RSS",
                        "title": title, "text": title, "published": pub_iso, "url": link})
    return out[:10]

_DEMO = [
    "{name} shares move as investors weigh latest earnings and guidance",
    "Analysts mixed on {name} outlook amid sector demand and competition",
    "{name} in focus after new product and market expansion updates",
    "Retail investors debate {name} valuation after recent price momentum",
]

def _demo(meta):
    now = datetime.now(timezone.utc)
    return [{"ticker": meta["ticker"], "source": "DEMO fallback (offline)",
             "title": t.format(name=meta["name"]), "text": t.format(name=meta["name"]),
             "published": (now - timedelta(days=i)).isoformat(), "url": ""}
            for i, t in enumerate(_DEMO)]

def get_news(meta, days=10):
    """Returns (items, source_label)."""
    from config import EXA_API_KEY
    if EXA_API_KEY:
        try:
            items = _exa(meta, days)
            if items: return items, "Exa"
        except Exception:
            pass
    try:
        items = _google_news_rss(meta, days)
        if items: return items, "Google News RSS (Exa fallback — real headlines)"
    except Exception:
        pass
    return _demo(meta), "DEMO fallback (offline)"
