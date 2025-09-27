#!/usr/bin/env python3
"""
AMR Forecasting with ARIMA - Statistical Time Series Analysis

This script implements ARIMA/SARIMA forecasting for antimicrobial resistance trends.
Uses statistical modeling for prediction without external regressors.

Usage:
    python forecast_arima.py

Outputs:
    - ARIMA forecast charts and CSV results
"""

import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.statespace.sarimax import SARIMAX
from sklearn.metrics import mean_absolute_percentage_error, mean_squared_error
import numpy as np
import os

def find_best_arima_order(ts_data, max_p=3, max_d=2, max_q=3):
    """Find best ARIMA order using grid search."""
    best_aic = float('inf')
    best_order = (1, 1, 1)
    best_model = None

    print(f"🔍 Searching for optimal ARIMA order (max p={max_p}, d={max_d}, q={max_q})...")

    for p in range(max_p + 1):
        for d in range(max_d + 1):
            for q in range(max_q + 1):
                if p + d + q == 0:  # Skip (0,0,0)
                    continue

                try:
                    model = ARIMA(ts_data, order=(p, d, q))
                    fitted_model = model.fit()
                    aic = fitted_model.aic

                    if aic < best_aic and fitted_model.mle_retvals['converged']:
                        best_aic = aic
                        best_order = (p, d, q)
                        best_model = fitted_model

                except Exception as e:
                    continue  # Skip if doesn't fit

    print(f"✅ Best ARIMA order: {best_order} (AIC: {best_aic:.2f})")
    return best_order, best_model

def fit_arima_model(data, pathogen, antibiotic, order=None, seasonal=False):
    """Fit ARIMA model to pathogen-antibiotic pair."""

    # Filter data
    subset = data[(data["pathogen"] == pathogen) & (data["antibiotic"] == antibiotic)].copy()

    if len(subset) < 10:
        raise ValueError(f"Insufficient data for {pathogen}-{antibiotic} forecasting (need ≥10 points)")

    # Prepare time series
    ts_data = subset.set_index('date')['percent_resistant']
    ts_data = ts_data.resample('M').mean().fillna(method='ffill')

    print(f"📊 Training on {len(ts_data)} time series points")

    # Auto-select order if not provided
    if order is None:
        order, _ = find_best_arima_order(ts_data)

    # Fit model
    if seasonal and len(ts_data) >= 12:  # Need at least 12 months for seasonality
        model = SARIMAX(ts_data, order=order, seasonal_order=((1, 0, 1, 12)))
        fitted_model = model.fit(disp=False)
        model_type = f"SARIMA{order}"
    else:
        model = ARIMA(ts_data, order=order)
        fitted_model = model.fit()
        model_type = f"ARIMA{order}"

    print(f"🤖 Fitted {model_type} model successfully")
    return fitted_model, ts_data, model_type

def generate_forecasts(model, ts_data, periods=12, model_name="ARIMA"):
    """Generate ARIMA forecasts with confidence intervals."""

    # Forecast
    forecast_result = model.forecast(steps=periods)

    # Confidence intervals
    try:
        pred_ci = model.get_forecast(steps=periods).conf_int(alpha=0.05)
        lower_bounds = pred_ci.iloc[:, 0]
        upper_bounds = pred_ci.iloc[:, 1]
    except Exception as e:
        print(f"⚠️  Could not calculate confidence intervals: {e}")
        # Approximation using standard error
        se = np.sqrt(model.mse) if hasattr(model, 'mse') else np.std(ts_data.tail(12))
        lower_bounds = forecast_result.values - 1.96 * se
        upper_bounds = forecast_result.values + 1.96 * se

    # Create forecast dataframe
    last_date = ts_data.index[-1]
    forecast_dates = pd.date_range(start=last_date, periods=periods+1, freq='M')[1:]

    forecast_df = pd.DataFrame({
        'ds': forecast_dates,
        'yhat': forecast_result.values,
        'yhat_lower': lower_bounds.values if hasattr(lower_bounds, 'values') else lower_bounds,
        'yhat_upper': upper_bounds.values if hasattr(upper_bounds, 'values') else upper_bounds,
        'model': model_name
    })

    return forecast_df

def create_arima_plot(ts_data, forecast_df, pathogen, antibiotic, model_name):
    """Create comprehensive ARIMA forecast visualization."""

    fig, axes = plt.subplots(2, 1, figsize=(14, 10), gridspec_kw={'height_ratios': [3, 1]})

    # Time series plot
    axes[0].plot(ts_data.index, ts_data.values, label='Historical Data',
                color='black', linewidth=2, marker='o', markersize=4)

    axes[0].plot(forecast_df['ds'], forecast_df['yhat'], label=f'{model_name} Forecast',
                color='#0072B2', linewidth=3, marker='s', markersize=4)

    # Confidence intervals
    axes[0].fill_between(forecast_df['ds'], forecast_df['yhat_lower'], forecast_df['yhat_upper'],
                        color='#0072B2', alpha=0.3, label='95% Confidence Interval')

    # Resistance threshold
    axes[0].axhline(y=80, color='red', linestyle='--', alpha=0.7, label='Critical Threshold (80%)')
    axes[0].axhline(y=70, color='orange', linestyle='--', alpha=0.7, label='Warning Threshold (70%)')

    axes[0].set_title(f'ARIMA Forecast: {pathogen} vs {antibiotic}', fontsize=16, fontweight='bold')
    axes[0].set_xlabel('Date')
    axes[0].set_ylabel('Resistance Percentage (%)')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    # Residuals/Analysis plot
    residuals = []
    for i in range(1, min(len(ts_data), 12)):
        pred = ts_data.shift(i)
        if len(pred.dropna()) > 0:
            residuals.extend((ts_data - pred).dropna().values[:5])  # Take first 5 for plotting

    if residuals:
        axes[1].plot(np.arange(len(residuals)), residuals, 'o-', alpha=0.7)
        axes[1].axhline(y=0, color='red', linestyle='-', alpha=0.5)
        axes[1].set_title('Model Residuals Analysis')
        axes[1].set_xlabel('Observation')
        axes[1].set_ylabel('Residual')
        axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    return fig

def calculate_forecast_metrics(ts_data, forecast_df):
    """Calculate forecast accuracy metrics."""

    # If we have enough historical data, do backtesting
    if len(ts_data) >= 20:
        try:
            # Use 80% for training, 20% for validation
            train_size = int(len(ts_data) * 0.8)
            train_data = ts_data[:train_size]
            test_data = ts_data[train_size:]

            # Refit model on training data
            order, _ = find_best_arima_order(train_data, max_p=2, max_d=1, max_q=2)
            test_model = ARIMA(train_data, order=order).fit()

            # Forecast test period
            test_forecast = test_model.forecast(steps=len(test_data))

            # Calculate metrics
            mape = mean_absolute_percentage_error(test_data, test_forecast)
            rmse = mean_squared_error(test_data, test_forecast, squared=False)

            return {
                'MAPE': mape * 100,
                'RMSE': rmse,
                'Test_Period_Start': test_data.index[0].strftime('%Y-%m'),
                'Test_Period_End': test_data.index[-1].strftime('%Y-%m')
            }

        except Exception as e:
            print(f"⚠️  Backtesting failed: {e}")

    return {'Note': 'Insufficient data for backtesting'}

def main():
    """Main ARIMA forecasting pipeline."""

    print("🔬 Starting ARIMA-based AMR forecasting...")

    # Load processed data
    data_path = "../data/amr_data_processed.csv"
    if not os.path.exists(data_path):
        print("⚠️  Processed data not found. Running preprocessor first...")
        os.system("python pipeline/preprocess.py")
        if not os.path.exists(data_path):
            print(f"❌ Cannot find data file: {data_path}")
            return

    df = pd.read_csv(data_path)
    df['date'] = pd.to_datetime(df['date'])
    print(f"📊 Loaded {len(df):,} processed AMR records")

    # Example forecast for E. coli vs Ciprofloxacin
    pathogen = "E.coli"
    antibiotic = "Ciprofloxacin"

    try:
        # Fit ARIMA model
        model, ts_data, model_type = fit_arima_model(df, pathogen, antibiotic)

        # Generate forecasts (12 months ahead)
        forecast_periods = 12
        forecast_df = generate_forecasts(model, ts_data, periods=forecast_periods, model_name=model_type)

        print(f"📈 Generated {forecast_periods}-month {model_type} forecast")

        # Calculate metrics
        metrics = calculate_forecast_metrics(ts_data, forecast_df)
        if 'MAPE' in metrics:
            print(".2f")

        # Create visualizations
        fig = create_arima_plot(ts_data, forecast_df, pathogen, antibiotic, model_type)

        # Save results
        output_dir = "../reports"
        os.makedirs(output_dir, exist_ok=True)

        # Save plot
        plot_filename = f"{pathogen}_{antibiotic}_arima_forecast.png".replace(' ', '_').lower()
        plot_path = os.path.join(output_dir, plot_filename)
        fig.savefig(plot_path, dpi=300, bbox_inches='tight')
        print(f"📊 Saved forecast plot to: {plot_path}")

        # Save forecast data
        csv_filename = f"{pathogen}_{antibiotic}_arima_forecast.csv".replace(' ', '_').lower()
        csv_path = os.path.join(output_dir, csv_filename)
        forecast_df.to_csv(csv_path, index=False)
        print(f"📋 Saved forecast data to: {csv_path}")

        # Show forecast summary
        final_forecast = forecast_df['yhat'].iloc[-1]
        current_resistance = ts_data.iloc[-1]
        forecast_change = final_forecast - current_resistance

        print("
📈 ARIMA FORECAST SUMMARY:"        print(".1f"        print(".1f"        print("%.1f"        print("%.1f")

        # Threshold alerts
        if final_forecast > 80:
            print("🚨 CRITICAL ALERT: Forecast resistance exceeds 80%!")
        elif final_forecast > 70:
            print("⚠️  WARNING: Forecast resistance exceeds 70%!")

        plt.show()

        print("\n✅ ARIMA forecasting complete! Check reports/ folder for results.")

    except Exception as e:
        print(f"❌ Forecasting failed for {pathogen}-{antibiotic}: {e}")
        print("Try with different pathogen-antibiotic combination or check data quality.")

if __name__ == "__main__":
    main()
