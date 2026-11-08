"""Visual HTML report: charts (matplotlib SVGs, text-based for GitHub) + sorted tables + per-ticker cards."""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

def _chart(df_ex, col, title, path, color):
    fig, ax = plt.subplots(figsize=(8, 3.6))
    d = df_ex.sort_values(col)
    ax.barh(d["ticker"], d[col], color=color)
    ax.set_title(title); fig.tight_layout()
    fig.savefig(path, format="svg"); plt.close(fig)

def generate_report(results: list, mode_notes: dict, out_dir: str):
    assets = os.path.join(out_dir, "assets"); os.makedirs(assets, exist_ok=True)
    df = pd.DataFrame(results)
    charts = {}
    for ex, safe in [("Hang Seng (HK)", "hk"), ("KRX (Korea)", "kr")]:
        sub = df[df["exchange"] == ex]
        if sub.empty: continue
        p1 = os.path.join(assets, f"sentiment_{safe}.svg"); _chart(sub, "sentiment_score", f"{ex} — Sentiment score", p1, "#2563eb")
        p2 = os.path.join(assets, f"mentions_{safe}.svg"); _chart(sub, "mentions", f"{ex} — Social mentions (10d)", p2, "#059669")
        charts[ex] = (f"assets/sentiment_{safe}.svg", f"assets/mentions_{safe}.svg")

    def badge(direction):
        c = "#059669" if direction == "Up" else "#dc2626"
        return f'<span style="background:{c};color:#fff;padding:2px 8px;border-radius:10px">{direction}</span>'

    sections = ""
    for ex in ["Hang Seng (HK)", "KRX (Korea)"]:
        sub = df[df["exchange"] == ex].sort_values(["mentions", "sentiment_score"], ascending=False)
        if sub.empty: continue
        rows = "".join(
            f"<tr><td>{r.ticker}</td><td>{r.asset_name}</td><td>{r.current_price:,.2f} {r.currency}</td>"
            f"<td>{r.mentions}</td><td>{r.sentiment_score:+.3f} ({r.sentiment_label})</td>"
            f"<td>{badge(r.direction)}</td><td>{r.position}</td><td>{r.predicted_price_next:,.2f}</td>"
            f"<td>{r.support:,.2f}</td><td>{r.resistance:,.2f}</td></tr>"
            for r in sub.itertuples())
        cards = "".join(
            f"""<div class="card"><h3>{r.ticker} — {r.asset_name}</h3>
            <p>Price: <b>{r.current_price:,.2f} {r.currency}</b> &nbsp;|&nbsp; Predicted n+1: <b>{r.predicted_price_next:,.2f}</b> ({r.pred_return_pct:+.2f}%)</p>
            <p>Sentiment: <b>{r.sentiment_score:+.3f}</b> ({r.sentiment_label}) · Mentions: {r.mentions} · News: {r.news_count} · Direction: {badge(r.direction)} · Position: <b>{r.position}</b></p>
            <p>Support: {r.support:,.2f} · Pivot: {r.pivot:,.2f} · Resistance: {r.resistance:,.2f}</p>
            <p class="src">Sources — Social: {r.social_source} · News: {r.news_source} · Price: {r.price_source}</p></div>"""
            for r in sub.itertuples())
        c1, c2 = charts.get(ex, ("", ""))
        sections += f"""<h2>{ex}</h2><div class="charts"><img src="{c1}"><img src="{c2}"></div>
        <table><tr><th>Ticker</th><th>Asset</th><th>Price</th><th>Mentions</th><th>Sentiment</th>
        <th>Direction</th><th>Position</th><th>Pred n+1</th><th>Support</th><th>Resistance</th></tr>{rows}</table>{cards}"""

    m = mode_notes
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>CWT Sentiment Report</title>
<style>body{{font-family:Arial,sans-serif;max-width:1100px;margin:24px auto;padding:0 16px;color:#111827}}
table{{border-collapse:collapse;width:100%;margin:12px 0}}th,td{{border:1px solid #d1d5db;padding:6px 8px;text-align:left;font-size:14px}}
th{{background:#111827;color:#fff}}.card{{border:1px solid #d1d5db;border-radius:10px;padding:12px 16px;margin:10px 0}}
.charts img{{max-width:49%}}.src{{color:#6b7280;font-size:12px}}.note{{background:#fef3c7;padding:10px 14px;border-radius:8px}}</style></head>
<body><h1>CrowdWisdomTrading — Sentiment Price Prediction Report</h1>
<p>Assets sorted by social mentions, then sentiment score, per exchange. Prediction = price at n+1 (next trading day).</p>
<div class="note"><b>Data mode:</b> Prices: {m.get('price','')} · News: {m.get('news','')} · Social: {m.get('social','')}<br>
<b>Model validation (out-of-sample, TimeSeriesSplit ×5):</b> {m.get('model','')}</div>
{sections}
<h2>How to read this</h2><p>Position = Long if the model predicts up AND sentiment is positive; Short if model predicts down AND sentiment is negative; otherwise Neutral. This is a research prototype, not financial advice.</p>
</body></html>"""
    path = os.path.join(out_dir, "report.html")
    with open(path, "w", encoding="utf-8") as f: f.write(html)
    return path
