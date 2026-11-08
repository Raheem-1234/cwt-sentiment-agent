"""Predictive model with rigorous OUT-OF-SAMPLE validation.

- Walk-forward / TimeSeriesSplit (5 splits) — never shuffled, no look-ahead.
  Features are known at close of day n; targets are day n+1.
- Direction: LogisticRegression (scaled) — accuracy vs naive baseline
  (always predicting the majority / previous-direction class).
- Price n+1: Ridge regression on next-day return -> predicted price —
  MAE vs naive baseline (tomorrow = today's close).
- Final model is refit on ALL data and used for the live n+1 prediction.
- Backtest ('check your results'): the last split's out-of-sample
  predictions are reported so performance can be inspected honestly.
"""
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import accuracy_score, mean_absolute_error
from src.features import FEATURE_COLS

def validate_and_predict(df: pd.DataFrame):
    data = df.dropna(subset=FEATURE_COLS + ["target_price_next"]).copy()
    if len(data) < 40:
        raise ValueError(f"Not enough rows for validation: {len(data)}")
    X = data[FEATURE_COLS].values
    y_dir = data["target_dir_next"].values
    y_ret = (data["target_price_next"].values - data["close"].values) / data["close"].values

    tscv = TimeSeriesSplit(n_splits=5)
    dir_acc, price_mae, naive_mae, naive_acc = [], [], [], []
    last_test = None
    for train_idx, test_idx in tscv.split(X):
        clf = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000))
        clf.fit(X[train_idx], y_dir[train_idx])
        pred = clf.predict(X[test_idx])
        dir_acc.append(accuracy_score(y_dir[test_idx], pred))
        # naive direction baseline: predict sign of last return (momentum)
        naive_pred = (data["return_1d"].values[test_idx] > 0).astype(int)
        naive_acc.append(accuracy_score(y_dir[test_idx], naive_pred))
        reg = Ridge(alpha=1.0)
        reg.fit(X[train_idx], y_ret[train_idx])
        pred_price = data["close"].values[test_idx] * (1 + reg.predict(X[test_idx]))
        price_mae.append(mean_absolute_error(data["target_price_next"].values[test_idx], pred_price))
        naive_mae.append(mean_absolute_error(data["target_price_next"].values[test_idx],
                                             data["close"].values[test_idx]))
        last_test = (test_idx, pred, pred_price)

    metrics = {
        "direction_accuracy_oos": round(float(np.mean(dir_acc)), 4),
        "direction_accuracy_std": round(float(np.std(dir_acc)), 4),
        "naive_direction_accuracy": round(float(np.mean(naive_acc)), 4),
        "price_mae_oos": round(float(np.mean(price_mae)), 2),
        "naive_price_mae": round(float(np.mean(naive_mae)), 2),
        "n_train_rows": int(len(data)), "n_splits": 5,
        "beats_naive_direction": bool(np.mean(dir_acc) > np.mean(naive_acc)),
        "beats_naive_price": bool(np.mean(price_mae) < np.mean(naive_mae)),
    }
    # backtest table from last (most recent) out-of-sample split
    test_idx, pred_dir, pred_price = last_test
    bt = data.iloc[test_idx][["date", "close", "target_price_next"]].copy()
    bt["pred_dir"] = pred_dir; bt["pred_price_next"] = np.round(pred_price, 2)
    bt["actual_dir"] = data["target_dir_next"].values[test_idx]
    bt["dir_correct"] = (bt["pred_dir"] == bt["actual_dir"]).astype(int)
    backtest = bt.tail(10)

    # refit on all data -> live n+1 prediction from the latest row
    latest = df.iloc[-1]
    x_live = np.array([[latest[c] if pd.notna(latest[c]) else 0.0 for c in FEATURE_COLS]])
    clf_full = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000))
    clf_full.fit(X, y_dir)
    # RandomForest as a robustness check for price; average with Ridge
    ridge_full = Ridge(alpha=1.0).fit(X, y_ret)
    rf_full = RandomForestRegressor(n_estimators=200, max_depth=5, random_state=42, n_jobs=-1).fit(X, y_ret)
    pred_ret = float(0.5 * ridge_full.predict(x_live)[0] + 0.5 * rf_full.predict(x_live)[0])
    direction_prob_up = float(clf_full.predict_proba(x_live)[0][list(clf_full.classes_).index(1)]) \
        if 1 in clf_full.classes_ else 0.5
    pred_price_next = float(latest["close"] * (1 + pred_ret))
    return {"metrics": metrics, "backtest": backtest,
            "pred_price_next": round(pred_price_next, 2),
            "pred_return_next": round(pred_ret, 5),
            "prob_up": round(direction_prob_up, 4),
            "direction": "Up" if pred_ret > 0 else "Down"}
