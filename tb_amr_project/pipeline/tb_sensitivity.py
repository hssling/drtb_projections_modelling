import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from prophet import Prophet
from pathlib import Path

def run_tb_sensitivity(country="India", drug="Rifampicin (proxy MDR)", case_type="new", horizon=120):
    """
    Simulate policy scenarios for MDR-TB resistance forecasts.
    - horizon: forecast period in months (default 10 years = 120 months)
    """
    df = pd.read_csv("data/tb_merged.csv")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    subset = df[(df["country"] == country) &
                (df["drug"] == drug) &
                (df["type"] == case_type)]

    if subset.empty:
        print("❌ No TB-AMR data for this selection.")
        return

    data = subset[["date", "percent_resistant"]].rename(columns={"date": "ds", "percent_resistant": "y"}).dropna()

    # ---------------- Baseline Prophet Model ----------------
    model = Prophet()
    model.fit(data)
    future = model.make_future_dataframe(periods=horizon, freq="M")
    baseline_forecast = model.predict(future)

    # ---------------- Scenarios ----------------
    scenarios = {}

    # A: BPaL rollout (↓ resistance trajectory by 20% after forecast start)
    bp_forecast = baseline_forecast.copy()
    bp_forecast["yhat"] = bp_forecast["yhat"] * 0.8
    scenarios["BPaL Rollout (-20%)"] = bp_forecast

    # B: Improved adherence (↓ trajectory by 15%)
    ad_forecast = baseline_forecast.copy()
    ad_forecast["yhat"] = ad_forecast["yhat"] * 0.85
    scenarios["Adherence Improvement (-15%)"] = ad_forecast

    # C: Delayed interventions (+10%)
    delay_forecast = baseline_forecast.copy()
    delay_forecast["yhat"] = delay_forecast["yhat"] * 1.1
    scenarios["Delayed Intervention (+10%)"] = delay_forecast

    # ---------------- Plot Results ----------------
    Path("reports").mkdir(exist_ok=True)
    plt.figure(figsize=(10,6))
    plt.plot(data["ds"], data["y"], marker="o", label="Observed")
    plt.plot(baseline_forecast["ds"], baseline_forecast["yhat"], label="Baseline Forecast", linestyle="--")

    for label, forecast in scenarios.items():
        plt.plot(forecast["ds"], forecast["yhat"], label=label, linestyle="--")

    plt.title(f"Sensitivity Analysis: {drug} ({case_type} cases) in {country}")
    plt.ylabel("% Resistant (MDR-TB)")
    plt.legend()
    out_file = f"reports/tb_sensitivity_{country}_{case_type}.png".replace(" ","_")
    plt.savefig(out_file)
    print(f"📊 Sensitivity plot saved → {out_file}")

if __name__ == "__main__":
    run_tb_sensitivity("India", "Rifampicin (proxy MDR)", "new", horizon=120)
