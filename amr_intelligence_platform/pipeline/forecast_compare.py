#!/usr/bin/env python3
"""
AMR Forecasting Pipeline - Prophet vs ARIMA vs LSTM Model Comparison

Batch forecasting script that compares Prophet, ARIMA, and LSTM models
side-by-side using the amr_merged.csv unified dataset.

Usage:
    python pipeline/forecast_compare.py <country> <pathogen> <antibiotic>

Example:
    python pipeline/forecast_compare.py "India" "E.coli" "Ciprofloxacin"

Outputs:
    - Combined Forecast CSV: forecast_comparison_{country}_{pathogen}_{antibiotic}.csv
    - Comparison Plot PNG: forecast_comparison_{country}_{pathogen}_{antibiotic}.png
    - Individual Model CSVs: forecast_{model}_{country}_{pathogen}_{antibiotic}.csv
"""

import pandas as pd
from prophet import Prophet
from statsmodels.tsa.arima.model import ARIMA
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
import numpy as np
import matplotlib.pyplot as plt
import sys
import os
from pathlib import Path
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

df = pd.read_csv("data/amr_merged.csv")
df["date"] = pd.to_datetime(df["date"], errors="coerce")

def run_prophet(data, periods=24):
    model = Prophet()
    model.fit(data.rename(columns={"date":"ds","percent_resistant":"y"}))
    future = model.make_future_dataframe(periods=periods, freq="M")
    forecast = model.predict(future)
    return forecast[["ds","yhat","yhat_lower","yhat_upper"]]

def run_arima(data, periods=24):
    series = data.set_index("date")["percent_resistant"].dropna()
    model = ARIMA(series, order=(2,1,2))
    model_fit = model.fit()
    forecast = model_fit.forecast(steps=periods)
    future_dates = pd.date_range(start=series.index[-1], periods=periods+1, freq="M")[1:]
    return pd.DataFrame({"ds":future_dates, "yhat":forecast.values})

def run_lstm(data, look_back=3, periods=12):
    series = data.set_index("date")["percent_resistant"].dropna().values.reshape(-1,1)
    scaler = MinMaxScaler()
    scaled = scaler.fit_transform(series)

    def create_dataset(dataset, look_back=3):
        X, Y = [], []
        for i in range(len(dataset)-look_back):
            X.append(dataset[i:i+look_back,0])
            Y.append(dataset[i+look_back,0])
        return np.array(X), np.array(Y)

    X, y = create_dataset(scaled, look_back)
    X = X.reshape((X.shape[0], look_back, 1))

    model = Sequential([
        LSTM(50, input_shape=(look_back,1)),
        Dense(1)
    ])
    model.compile(optimizer="adam", loss="mse")
    model.fit(X, y, epochs=20, batch_size=8, verbose=0)

    # Forecast
    forecast_input = scaled[-look_back:].reshape(1,look_back,1)
    predictions = []
    for _ in range(periods):
        pred = model.predict(forecast_input, verbose=0)
        predictions.append(pred[0,0])
        forecast_input = np.append(forecast_input[:,1:,:], [[pred]], axis=1)

    forecast = scaler.inverse_transform(np.array(predictions).reshape(-1,1))
    future_dates = pd.date_range(start=data["date"].max(), periods=periods+1, freq="M")[1:]
    return pd.DataFrame({"ds":future_dates, "yhat":forecast.flatten()})

def forecast_all(country, pathogen, antibiotic):
    subset = df[(df["country"] == country) &
                (df["pathogen"] == pathogen) &
                (df["antibiotic"] == antibiotic)].dropna()

    if subset.empty:
        print("❌ No data found for this combination")
        return

    print(f"Comparing models for {pathogen} vs {antibiotic} in {country}")

    # Prophet
    prophet_forecast = run_prophet(subset)
    prophet_forecast["model"] = "Prophet"

    # ARIMA
    arima_forecast = run_arima(subset)
    arima_forecast["model"] = "ARIMA"

    # LSTM
    lstm_forecast = run_lstm(subset)
    lstm_forecast["model"] = "LSTM"

    # Merge
    combined = pd.concat([prophet_forecast, arima_forecast, lstm_forecast])
    out_file = f"data/forecast_comparison_{country}_{pathogen}_{antibiotic}.csv".replace(" ","_")
    combined.to_csv(out_file, index=False)
    print(f"✅ Forecast results saved to {out_file}")

    # Plot
    plt.figure(figsize=(10,6))
    for model, group in combined.groupby("model"):
        plt.plot(group["ds"], group["yhat"], label=model)
    plt.legend()
    plt.title(f"Model Comparison: {pathogen} vs {antibiotic} in {country}")
    plt_file = f"data/forecast_comparison_{country}_{pathogen}_{antibiotic}.png".replace(" ","_")
    plt.savefig(plt_file)
    print(f"📊 Comparison plot saved to {plt_file}")
    plt.show()

if __name__ == "__main__":
    if len(sys.argv) == 4:
        _, country, pathogen, antibiotic = sys.argv
        forecast_all(country, pathogen, antibiotic)
    else:
        print("Usage: python pipeline/forecast_compare.py <country> <pathogen> <antibiotic>")
