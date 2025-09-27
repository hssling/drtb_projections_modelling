#!/usr/bin/env python3
"""
AMR Forecasting with Prophet - Antimicrobial Resistance Time Series Analysis

This script demonstrates forecasting AMR (antimicrobial resistance) trends using Facebook Prophet.
It uses pathogen-antibiotic pairs and includes antibiotic consumption as a regressor.

Usage:
    python forecast_prophet.py

Outputs:
    - prophet_forecast.png: Forecast visualization chart
    - prophet_forecast.csv: Detailed forecast results with confidence intervals
"""

import pandas as pd
from prophet import Prophet
import matplotlib.pyplot as plt
import os

# Load and prepare dataset
df = pd.read_csv("../data/amr_data.csv")

# Focus on E. coli vs Ciprofloxacin as example
subset = df[(df["pathogen"]=="E.coli") & (df["antibiotic"]=="Ciprofloxacin")]

print(f"📊 Loaded {len(subset)} months of E. coli Ciprofloxacin resistance data")

# Prepare data for Prophet (rename columns)
df_prophet = subset[["date","percent_resistant","ddd"]].rename(
    columns={"date":"ds","percent_resistant":"y","ddd":"consumption"}
)
df_prophet["ds"] = pd.to_datetime(df_prophet["ds"])

print("🔧 Prepared data for Prophet forecasting:")
print(f"   - Time range: {df_prophet['ds'].min().strftime('%Y-%m')} to {df_prophet['ds'].max().strftime('%Y-%m')}")
print(f"   - Current resistance level: {df_prophet['y'].iloc[-1]:.1f}%")

# Build Prophet model with antibiotic consumption regressor
model = Prophet(
    yearly_seasonality=True,
    weekly_seasonality=False,
    daily_seasonality=False,
    changepoint_prior_scale=0.05  # Conservative changepoint detection
)

model.add_regressor("consumption", prior_scale=0.5)
model.fit(df_prophet)

print("🤖 Trained Prophet model with antibiotic consumption regressor")

# Forecast next 24 months
future_periods = 24
future = model.make_future_dataframe(periods=future_periods, freq="M")

# Use last known antibiotic consumption level for forecast
future["consumption"] = df_prophet["consumption"].iloc[-1]
forecast = model.predict(future)

print(f"🎯 Generated {future_periods}-month forecast")

# Create visualization
plt.figure(figsize=(12, 8))
fig = model.plot(forecast)
plt.title("E. coli - Ciprofloxacin Resistance Forecast (Prophet Model)")
plt.xlabel("Date")
plt.ylabel("Resistance Percentage (%)")
plt.grid(True, alpha=0.3)

# Add resistance threshold line
plt.axhline(y=80, color='red', linestyle='--', alpha=0.7, label='Critical Threshold (80%)')
plt.legend()

# Save plot
output_dir = "../reports"
os.makedirs(output_dir, exist_ok=True)
plot_path = os.path.join(output_dir, "prophet_forecast.png")
plt.savefig(plot_path, dpi=300, bbox_inches='tight')
print(f"📊 Saved forecast visualization to: {plot_path}")

# Save forecast data
forecast_data = forecast[["ds","yhat","yhat_lower","yhat_upper"]].tail(future_periods)
forecast_path = os.path.join(output_dir, "prophet_forecast.csv")
forecast_data.to_csv(forecast_path, index=False)
print(f"📋 Saved forecast results to: {forecast_path}")

# Show summary statistics
final_forecast = forecast_data["yhat"].iloc[-1]
forecast_growth = ((final_forecast - df_prophet["y"].iloc[-1]) / df_prophet["y"].iloc[-1]) * 100

print("
📈 FORECAST SUMMARY:"print(f"   - Current resistance: {df_prophet['y'].iloc[-1]:.1f}%")
print(f"   - Forecast 2 years out: {final_forecast:.1f}%")
print(f"   - Projected growth: {forecast_growth:+.1f}%")
print(f"   - Average monthly increase: {forecast_growth/future_periods:.2f}%")

# Check if critical threshold crossed
if final_forecast > 80:
    print("⚠️  WARNING: Forecast resistance exceeds 80% critical threshold!")
elif final_forecast > 70:
    print("⚠️  CAUTION: Forecast resistance approaching 70% resistance level")

plt.show()

print("\n✅ Prophet forecast complete! Check reports/ folder for outputs.")
