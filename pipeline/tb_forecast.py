#!/usr/bin/env python3
"""
TB-AMR Forecasting Pipeline - Time Series Analysis for India TB Drug Resistance

Forecasts MDR and XDR-TB trends in India using time series models.
Supports Prophet, ARIMA, and LSTM for accurate predictions of TB-AMR burden.

Usage:
    python pipeline/tb_forecast.py <country> <drug> <case_type>

Example:
    python pipeline/tb_forecast.py "India" "Rifampicin (proxy MDR)" "new"

Outputs:
    - Forecast CSV: data/forecast_tb_India_{type}.csv
    - Comparison Plot: reports/tb_forecast_India_{type}.png
    - Metrics CSV: reports/tb_metrics_India_{type}.csv
"""

import pandas as pd
import matplotlib.pyplot as plt
import sys
import os
from pathlib import Path
import logging
from datetime import datetime

# Import forecasting models
from models import compare_models

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_tb_data():
    """Load the unified TB-AMR dataset."""
    # Try tb_amr_project/data first, then research-automation/data
    tb_project_data = Path("../data/tb_merged.csv")
    research_data = Path("../../data/tb_merged.csv")

    data_path = tb_project_data if tb_project_data.exists() else research_data

    if not data_path.exists():
        print("❌ TB dataset not found. Please run data extraction first:")
        print("   python pipeline/extract_tb_data.py")
        sys.exit(1)

    df = pd.read_csv(data_path)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    print(f"✅ Loaded TB-AMR dataset: {len(df)} records")
    print(f"   Types: {df['type'].unique()}")
    print(f"   Date range: {df['date'].min()} to {df['date'].max()}")

    return df

def forecast_tb_type(df, case_type="new", forecast_periods=60):  # 5 years forecast
    """
    Generate TB-AMR forecast for specific case type.

    Args:
        df: Unified TB dataset
        case_type: 'new' or 'retreated'
        forecast_periods: Months to forecast ahead (default: 60)
    """

    print(f"\n🔬 Forecasting TB-{case_type.capitalize()} MDR-TB Resistance")

    # Filter for India, MDR (rifampicin proxy)
    subset = df[(df["country"] == "India") &
                (df["type"] == case_type) &
                (df["drug"] == "Rifampicin (proxy MDR)")]

    if subset.empty:
        print(f"❌ No data found for {case_type} cases")
        return None

    print(f"📊 Historical data: {len(subset)} records")
    print(f"   Date range: {subset['date'].min()} to {subset['date'].max()}")
    print(f"   Current MDR-TB %: {subset['percent_resistant'].iloc[-1]:.1f}%")

    # Prepare data for forecasting
    data = subset[["date", "percent_resistant"]].copy()
    data.columns = ["ds", "y"]  # Rename for Prophet compatibility
    data = data.dropna()

    if len(data) < 3:
        print("❌ Insufficient data points (< 3) for forecasting")
        return None

    print(f"   Forecasting from {len(data)} clean data points")

    # Get model forecasts - expanded to 7 models
    try:
        models_forecasts = compare_models(data, models=["prophet", "arima", "lstm", "random_forest", "gradient_boosting", "svr", "exponential_smoothing"],
                                        periods=forecast_periods)

        # Process and save results
        return save_tb_forecasts(models_forecasts, data, case_type, forecast_periods)

    except Exception as e:
        print(f"❌ Forecast failed: {e}")
        return None

def save_tb_forecasts(models_forecasts, historical_data, case_type, periods):
    """Save forecast results to CSV and PNG."""

    # Combine forecasts with historical data
    output_filename = f"forecast_tb_India_{case_type}"

    # Create combined dataset
    combined_data = []

    # Add historical data
    for _, row in historical_data.iterrows():
        combined_data.append({
            "date": row["ds"],
            "percent_resistant": row["y"],
            "forecast_horizon": 0,
            "is_historical": True
        })

    # Add forecasts from each model
    future_dates = pd.date_range(historical_data['ds'].iloc[-1],
                                periods=periods+1, freq='M')[1:]

    for i, date in enumerate(future_dates):
        row = {"date": date, "forecast_horizon": i+1, "is_historical": False}

        for model_name, forecast_df in models_forecasts.items():
            if not forecast_df.empty and i < len(forecast_df):
                pred_col = f"{model_name}_predicted"
                row[pred_col] = forecast_df.iloc[i]["yhat"]

                # Include confidence intervals for Prophet
                if model_name == "prophet" and "yhat_lower" in forecast_df.columns:
                    row[f"{model_name}_lower"] = forecast_df.iloc[i]["yhat_lower"]
                    row[f"{model_name}_upper"] = forecast_df.iloc[i]["yhat_upper"]

        combined_data.append(row)

    result_df = pd.DataFrame(combined_data)

    # Save CSV to tb_amr_project/data
    csv_file = f"../data/{output_filename}.csv"
    result_df.to_csv(csv_file, index=False)
    print(f"✅ Forecasts saved to: {csv_file}")

    # Also save to research-automation data folder for broader access
    research_data_csv = f"../../data/forecast_{output_filename}.csv"
    Path("../../data").mkdir(exist_ok=True)
    result_df.to_csv(research_data_csv, index=False)
    print(f"✅ Forecasts also saved to research location: {research_data_csv}")

    # Create comparison plot
    create_tb_forecast_plot(result_df, historical_data, case_type, output_filename)

    # Print forecast summary
    print_forecast_summary(historical_data, models_forecasts, case_type)

    return result_df

def create_tb_forecast_plot(result_df, historical_data, case_type, filename):
    """Create and save forecast comparison plot."""

    fig, ax = plt.subplots(figsize=(14, 8))

    # Plot historical data
    hist_data = result_df[result_df["is_historical"] == True]
    ax.scatter(hist_data["date"], hist_data["percent_resistant"],
              color="blue", label="Historical MDR-TB %", alpha=0.7, s=40)

    # Plot forecasts
    forecast_data = result_df[result_df["is_historical"] == False]

    # Expanded color scheme for 7 models
    color_palette = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', '#F7DC6F', '#BB8FCE']
    colors = {
        "prophet": color_palette[0],
        "arima": color_palette[1],
        "lstm": color_palette[2],
        "random_forest": color_palette[3],
        "gradient_boosting": color_palette[4],
        "svr": color_palette[5],
        "exponential_smoothing": color_palette[6]
    }
    labels = {
        "prophet": "Prophet (Facebook)",
        "arima": "ARIMA (Stats)",
        "lstm": "LSTM (Deep Learning)",
        "random_forest": "Random Forest",
        "gradient_boosting": "Gradient Boosting",
        "svr": "SVR (SVM)",
        "exponential_smoothing": "Exponential Smoothing"
    }

    for model in ["prophet", "arima", "lstm", "random_forest", "gradient_boosting", "svr", "exponential_smoothing"]:
        pred_col = f"{model}_predicted"
        if pred_col in forecast_data.columns:
            ax.plot(forecast_data["date"], forecast_data[pred_col],
                   color=colors[model], linewidth=2, label=labels[model])

            # Add confidence intervals for Prophet
            if model == "prophet":
                lower_col = f"{model}_lower"
                upper_col = f"{model}_upper"
                if lower_col in forecast_data.columns and upper_col in forecast_data.columns:
                    ax.fill_between(forecast_data["date"],
                                   forecast_data[lower_col],
                                   forecast_data[upper_col],
                                   color=colors[model], alpha=0.2,
                                   label="Prophet 95% CI")

    # Add WHO MDR-TB thresholds
    ax.axhline(y=5, color='orange', linestyle='--', alpha=0.7, label='WHO Moderate Burden (5%)')
    ax.axhline(y=10, color='red', linestyle='--', alpha=0.7, label='WHO High Burden (10%)')

    # Formatting
    ax.set_title(f'MDR-TB Forecast: India {case_type.capitalize()} Cases (2017-2023)',
                fontsize=16, fontweight='bold')
    ax.set_xlabel('Year')
    ax.set_ylabel('MDR-TB Resistance Percentage (%)')
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, max(result_df["percent_resistant"].max(),
                      forecast_data[[c for c in forecast_data.columns if "predicted" in c]].max().max()) * 1.1)

    # Set x-axis to show years
    import matplotlib.dates as mdates
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

    plt.tight_layout()
    png_file = f"../data/{filename}.png"
    plt.savefig(png_file, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"📊 Plot saved to: {png_file}")

def print_forecast_summary(historical_data, models_forecasts, case_type):
    """Print forecast summary statistics."""

    current_resistance = historical_data["y"].iloc[-1]

    print(f"\n📈 TB-{case_type.capitalize()} MDR-TB 7-Model Forecast Summary:")
    print(f"   Current MDR-TB %: {current_resistance:.1f}%")

    model_names = {
        "prophet": "Prophet",
        "arima": "ARIMA",
        "lstm": "LSTM",
        "random_forest": "Random Forest",
        "gradient_boosting": "Gradient Boosting",
        "svr": "SVR",
        "exponential_smoothing": "Exponential Smoothing"
    }

    print("\n🔍 Model Comparison (5-year forecasts):")
    print("=" * 80)

    for model_key in ["prophet", "arima", "lstm", "random_forest", "gradient_boosting", "svr", "exponential_smoothing"]:
        forecast_df = models_forecasts.get(model_key)
        if forecast_df is None or forecast_df.empty:
            continue

        final_forecast = forecast_df["yhat"].iloc[-1]
        peak_forecast = forecast_df["yhat"].max()
        change = final_forecast - current_resistance

        # Risk assessment
        if final_forecast > 10:
            risk = "🚨 CRITICAL"
        elif final_forecast > 5:
            risk = "⚠️ HIGH"
        elif final_forecast > 3:
            risk = "🔶 MODERATE"
        else:
            risk = "✅ LOW"

        trend = "↗️ Rising" if change > 0.5 else "→ Stable" if change > -0.5 else "↘️ Falling"

        print(f"   {model_names[model_key]:<18}: {final_forecast:>5.1f}% ({trend}) - {risk}")

    print("=" * 80)

def main():
    """Main command-line interface."""

    case_type = sys.argv[1] if len(sys.argv) > 1 else "new"

    if case_type not in ["new", "retreated"]:
        print("Usage: python pipeline/tb_forecast.py [new|retreated]")
        print("\nDefault: forecasts 'new' cases")
        sys.exit(1)

    print("🚀 TB-AMR Forecasting Pipeline")
    print("=" * 50)

    # Load TB dataset
    df = load_tb_data()

    # Generate forecast
    result = forecast_tb_type(df, case_type)

    if result is not None:
        print("\n✅ TB-AMR Forecasting complete!")
        print("📁 Check data/ folder for forecast CSV and plot PNG files")
    else:
        print("\n❌ Forecasting failed. Check data and try again.")

if __name__ == "__main__":
    main()
