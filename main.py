"""CWT Sentiment Agent — end-to-end CLI.

Run:  python main.py
Out:  output/report.html, output/predictions.csv, output/summary.json
Works with NO tokens (real yfinance prices + real Google News RSS +
StockTwits where available; demo fallback only as last resort).
With tokens (.env): Apify for social, Exa for news.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
from config import TICKERS, HISTORY_DAYS, SOCIAL_DAYS
from src.price_data import get_prices
from src.news_exa import get_news
from src.social_apify import get_social_posts
from src.sentiment import score_text, label
from src.features import build_features, daily_sentiment_series, support_resistance
from src.model import validate_and_predict
from src.report import generate_report

def position_for(pred_ret, sentiment, prob_up):
    if pred_ret > 0.003 and sentiment > 0.05: return "Long"
    if pred_ret < -0.003 and sentiment < -0.05: return "Short"
    return "Neutral"

def main():
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    os.makedirs(out_dir, exist_ok=True)
    results, all_metrics, backtests = [], {}, []
    price_modes, news_modes, social_modes = set(), set(), set()

    for exchange, metas in TICKERS.items():
        for meta in metas:
            print(f"[{exchange}] {meta['ticker']} {meta['name']} ...", flush=True)
            prices, pmode = get_prices(meta, HISTORY_DAYS); price_modes.add(pmode)
            news, nmode = get_news(meta, SOCIAL_DAYS); news_modes.add(nmode)
            headlines = [n["title"] for n in news]
            posts, smode = get_social_posts(meta, headlines, SOCIAL_DAYS); social_modes.add(smode)

            for p in posts: p["sentiment"] = score_text(p["text"])
            for n in news: n["sentiment"] = score_text(n["text"])

            mentions = len(posts) + len(news)
            if posts:
                w = [1 + max(p.get("likes", 0), 0) ** 0.5 for p in posts]
                sent = sum(p["sentiment"] * wi for p, wi in zip(posts, w)) / sum(w)
            else:
                sent = 0.0
            if news:
                sent = 0.7 * sent + 0.3 * (sum(n["sentiment"] for n in news) / len(news))

            real_daily = daily_sentiment_series(posts, news, prices["date"])
            feats = build_features(meta, prices, real_daily)
            sr = support_resistance(prices)
            model = validate_and_predict(feats)
            all_metrics[meta["ticker"]] = model["metrics"]
            bt = model["backtest"].copy(); bt["ticker"] = meta["ticker"]; backtests.append(bt)

            current = float(prices.iloc[-1]["close"])
            results.append({
                "exchange": exchange, "ticker": meta["ticker"], "asset_name": meta["name"],
                "currency": meta["currency"], "current_price": round(current, 2),
                "mentions": int(mentions), "social_posts": len(posts), "news_count": len(news),
                "sentiment_score": round(float(sent), 3), "sentiment_label": label(float(sent)),
                "direction": model["direction"], "prob_up": model["prob_up"],
                "predicted_price_next": model["pred_price_next"],
                "pred_return_pct": round(model["pred_return_next"] * 100, 2),
                "position": position_for(model["pred_return_next"], float(sent), model["prob_up"]),
                "support": sr["support"], "resistance": sr["resistance"], "pivot": sr["pivot"],
                "social_source": smode, "news_source": nmode, "price_source": pmode,
            })
            print(f"   price={current:,.2f} sent={sent:+.3f} pred_next={model['pred_price_next']:,.2f} "
                  f"dir_acc_oos={model['metrics']['direction_accuracy_oos']}")

    if backtests:
        pd.concat(backtests).to_csv(os.path.join(out_dir, "backtest_last_split.csv"), index=False)
    pred_df = pd.DataFrame(results).sort_values(["exchange", "mentions", "sentiment_score"], ascending=[True, False, False])
    pred_df.to_csv(os.path.join(out_dir, "predictions.csv"), index=False)

    avg_acc = sum(m["direction_accuracy_oos"] for m in all_metrics.values()) / len(all_metrics)
    mode_notes = {
        "price": "; ".join(sorted(price_modes)),
        "news": "; ".join(sorted(news_modes)),
        "social": "; ".join(sorted(social_modes)),
        "model": f"avg direction accuracy (OOS) = {avg_acc:.3f} across 10 tickers — per-ticker detail in summary.json",
    }
    generate_report(results, mode_notes, out_dir)
    summary = {"mode": mode_notes, "metrics_per_ticker": all_metrics, "n_tickers": len(results)}
    with open(os.path.join(out_dir, "summary.json"), "w") as f: json.dump(summary, f, indent=2)
    print("\nDONE")
    print("Report:      ", os.path.join(out_dir, "report.html"))
    print("Predictions: ", os.path.join(out_dir, "predictions.csv"))
    print("Summary:     ", os.path.join(out_dir, "summary.json"))
    print("Modes:", mode_notes)

if __name__ == "__main__":
    main()
