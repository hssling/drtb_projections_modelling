"""
Compare multiple time-series models for India TB notifications and generate forecasts.

Models:
- Linear (deg1) polynomial fit
- Quadratic (deg2) polynomial fit
- ETS additive trend (statsmodels)
- Bayesian linear regression (Gaussian posterior approximation via OLS covariance)

Outputs:
- metrics CSV (RMSE/MAE on holdout)
- combined forecast CSV
- comparison plot
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"
FIGS = ROOT / "figures"
REPORTS = ROOT / "reports"

FIGS.mkdir(parents=True, exist_ok=True)
REPORTS.mkdir(parents=True, exist_ok=True)


def load_series() -> pd.Series:
    """Load GTB-adjusted notifications if present; otherwise national forecast input."""
    candidates: List[Path] = [
        PROC / "national_notifications_gtb_adjusted.csv",
        PROC / "national_notifications_gtb.csv",
        PROC / "national_notifications.csv",
    ]
    for path in candidates:
        if path.exists():
            df = pd.read_csv(path)
            if "notifications" in df.columns and "year" in df.columns:
                return df.set_index("year")["notifications"]
    raise FileNotFoundError("No notification series found.")


def train_test_split(series: pd.Series, holdout: int = 2):
    y = series.values.astype(float)
    years = series.index.values.astype(int)
    return years[:-holdout], y[:-holdout], years[-holdout:], y[-holdout:]


def rmse(a, b):
    return float(np.sqrt(np.mean((a - b) ** 2)))


def mae(a, b):
    return float(np.mean(np.abs(a - b)))


def fit_poly(years: np.ndarray, y: np.ndarray, degree: int, horizon: int) -> Dict:
    coef = np.polyfit(years, y, degree)
    fitted = np.polyval(coef, years)
    future_years = np.arange(years.max() + 1, years.max() + 1 + horizon)
    forecast = np.polyval(coef, future_years)
    resid_std = np.std(y - fitted, ddof=1)
    ci_margin = 1.96 * resid_std
    return {
        "name": f"poly_deg{degree}",
        "coef": coef.tolist(),
        "fitted": fitted,
        "forecast_years": future_years,
        "forecast": forecast,
        "ci_low": forecast - ci_margin,
        "ci_high": forecast + ci_margin,
    }


def fit_ets(train_years: np.ndarray, y: np.ndarray, horizon: int) -> Dict:
    # Simple Holt's linear trend (manual, fixed smoothing)
    alpha, beta = 0.6, 0.2
    level = y[0]
    trend = y[1] - y[0]
    fitted = []
    for obs in y:
        prev_level = level
        level = alpha * obs + (1 - alpha) * (level + trend)
        trend = beta * (level - prev_level) + (1 - beta) * trend
        fitted.append(level + trend)
    fitted = np.array(fitted)
    forecast = []
    last_level = level
    last_trend = trend
    for i in range(1, horizon + 1):
        forecast.append(last_level + i * last_trend)
    forecast = np.array(forecast)
    resid_std = np.std(y - fitted, ddof=1)
    ci_margin = 1.96 * resid_std
    future_years = np.arange(train_years.max() + 1, train_years.max() + 1 + horizon)
    return {
        "name": "ets",
        "fitted": fitted,
        "forecast_years": future_years,
        "forecast": forecast,
        "ci_low": forecast - ci_margin,
        "ci_high": forecast + ci_margin,
    }


def fit_bayesian(years: np.ndarray, y: np.ndarray, horizon: int) -> Dict:
    """Simple Bayesian linear regression via normal posterior approximation."""
    X = np.column_stack([np.ones_like(years), years])
    xtx_inv = np.linalg.inv(X.T @ X)
    coef_mean = xtx_inv @ X.T @ y
    residuals = y - X @ coef_mean
    sigma2 = np.var(residuals, ddof=X.shape[1])
    cov = sigma2 * xtx_inv
    future_years = np.arange(years.max() + 1, years.max() + 1 + horizon)
    X_future = np.column_stack([np.ones_like(future_years), future_years])
    mean_pred = X_future @ coef_mean
    var_pred = np.sum(X_future @ cov * X_future, axis=1) + sigma2
    ci_margin = 1.96 * np.sqrt(var_pred)
    fitted = X @ coef_mean
    return {
        "name": "bayes_lin",
        "fitted": fitted,
        "forecast_years": future_years,
        "forecast": mean_pred,
        "ci_low": mean_pred - ci_margin,
        "ci_high": mean_pred + ci_margin,
    }


def main():
    series = load_series()
    train_years, train_y, test_years, test_y = train_test_split(series, holdout=2)
    horizon = 6

    models = []
    # Poly1 and Poly2
    for deg in (1, 2):
        m = fit_poly(train_years, train_y, deg, horizon)
        m["val_pred"] = np.polyval(m["coef"], test_years)
        models.append(m)

    # ETS
    ets = fit_ets(train_years, train_y, horizon + len(test_y))
    ets["val_pred"] = ets["forecast"][: len(test_y)]
    models.append(ets)

    # Bayesian linear
    bayes = fit_bayesian(train_years, train_y, horizon)
    bayes["val_pred"] = bayes["forecast"][: len(test_y)]
    models.append(bayes)

    # Metrics
    metrics = []
    for m in models:
        metrics.append(
            {
                "model": m["name"],
                "rmse": rmse(test_y, m["val_pred"]),
                "mae": mae(test_y, m["val_pred"]),
            }
        )
    metrics_df = pd.DataFrame(metrics).sort_values("rmse")
    metrics_df.to_csv(REPORTS / "timeseries_model_metrics.csv", index=False)

    # Build combined forecast table
    records = []
    base_years = series.index.values.astype(int)
    for m in models:
        # historical fit on training years
        hist_years = train_years
        records.append(
            pd.DataFrame(
                {
                    "year": hist_years,
                    "model": m["name"],
                    "fitted": m["fitted"],
                    "actual": series.loc[hist_years].values,
                }
            )
        )
        # append holdout actuals (no fitted)
        holdout_df = pd.DataFrame(
            {"year": test_years, "model": m["name"], "actual": test_y}
        )
        records.append(holdout_df)
        # forecast
        records.append(
            pd.DataFrame(
                {
                    "year": m["forecast_years"],
                    "model": m["name"],
                    "forecast": m["forecast"],
                    "lower_95": m["ci_low"],
                    "upper_95": m["ci_high"],
                }
            )
        )
    forecast_df = pd.concat(records, ignore_index=True)
    forecast_df.to_csv(REPORTS / "timeseries_model_forecasts.csv", index=False)

    # Plot comparison for forecasts
    plt.figure(figsize=(10, 6))
    plt.plot(base_years, series.values / 1e6, "k-o", label="Observed")
    colors = {"poly_deg1": "tab:blue", "poly_deg2": "tab:orange", "ets": "tab:green", "bayes_lin": "tab:red"}
    for m in models:
        fc_mask = forecast_df["model"] == m["name"]
        fc = forecast_df[fc_mask & forecast_df["forecast"].notna()]
        plt.plot(fc["year"], fc["forecast"] / 1e6, linestyle="--", color=colors.get(m["name"], None), label=m["name"])
    plt.title("Notification Forecast Comparison (Models)")
    plt.ylabel("Notifications (millions)")
    plt.xlabel("Year")
    plt.grid(alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(FIGS / "timeseries_model_comparison.png", dpi=300)

    # Save model selection info
    with open(REPORTS / "timeseries_model_selection.json", "w") as f:
        json.dump({"metrics": metrics}, f, indent=2)

    print("Timeseries comparison complete.")
    print(metrics_df)


if __name__ == "__main__":
    main()
