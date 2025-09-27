#!/usr/bin/env python3
"""
AMR Multi-Model Forecasting Pipeline - Prophet vs ARIMA vs LSTM

Batch forecasting script that compares Prophet, ARIMA, and LSTM models
side-by-side using the amr_merged.csv unified dataset.

Usage:
    python pipeline/amr_forecast.py <country> <pathogen> <antibiotic>

Example:
    python pipeline/amr_forecast.py "India" "E.coli" "Ciprofloxacin"

Outputs:
    - Combined Forecast CSV: forecast_{country}_{pathogen}_{antibiotic}.csv
    - Comparison Plot PNG: forecast_comparison_{country}_{pathogen}_{antibiotic}.png
    - Individual Model CSVs: forecast_{model}_{country}_{pathogen}_{antibiotic}.csv
"""

import pandas as pd
import matplotlib.pyplot as plt
import sys
import os
from pathlib import Path
import logging
from datetime import datetime
from models import compare_models

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_unified_data():
    """Load the unified AMR dataset."""
    data_path = Path("data/amr_merged.csv")

    if not data_path.exists():
        print("❌ Unified dataset not found. Please run data extraction first:")
        print("   python simple_amr_extract.py")
        sys.exit(1)

    df = pd.read_csv(data_path)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    print(f"✅ Loaded unified AMR dataset: {len(df)} records")
    print(f"   Sources: {df['source'].nunique()}")
    print(f"   Countries: {df['country'].nunique()}")
    print(f"   Pathogens: {df['pathogen'].nunique()}")

    return df

def forecast_amr(df, country, pathogen, antibiotic, forecast_periods=24):
    """
    Generate AMR forecast for specific combination using Prophet.

    Args:
        df: Unified AMR dataset
        country: Country name
        pathogen: Pathogen name
        antibiotic: Antibiotic name
        forecast_periods: Months to forecast ahead (default: 24)
    """

    print(f"\n🔬 Forecasting: {country} | {pathogen} | {antibiotic}")

    # Filter data for specific combination
    subset = df[(df["country"].str.lower() == country.lower()) &
                (df["pathogen"].str.lower() == pathogen.lower()) &
                (df["antibiotic"].str.lower() == antibiotic.lower())]

    if subset.empty:
        print("❌ No data found for this combination")
        print("\nAvailable combinations:")

        # Show available options
        print(f"Countries: {sorted(df['country'].dropna().unique())[:5]}...")
        print(f"Pathogens: {sorted(df['pathogen'].dropna().unique())[:5]}...")
        print(f"Antibiotics: {sorted(df['antibiotic'].dropna().unique())[:5]}...")
        return None

    print(f"📊 Historical data: {len(subset)} records")
    print(f"   Date range: {subset['date'].min()} to {subset['date'].max()}")
    print(f"   Current resistance: {subset['percent_resistant'].iloc[-1]:.1f}%")
    # Prepare data for Prophet
    data = subset[["date", "percent_resistant"]].copy()
    data = data.rename(columns={"date": "ds", "percent_resistant": "y"})
    data = data.dropna()

    if len(data) < 5:
        print("❌ Insufficient data points (< 5) for forecasting")
        return None

    print(f"   Forecasting from {len(data)} clean data points")

    try:
        # Initialize and fit Prophet model
        model = Prophet(
            yearly_seasonality=True,
            changepoint_prior_scale=0.05,  # Flexibility in trend changes
            seasonality_prior_scale=10.0   # Strength of seasonality
        )

        model.fit(data)

        # Create future dataframe for forecasting
        future = model.make_future_dataframe(periods=forecast_periods, freq="M")
        forecast = model.predict(future)

        # Clean and enhance forecast results
        forecast_clean = forecast[["ds", "yhat", "yhat_lower", "yhat_upper", "trend"]].copy()
        forecast_clean.columns = ["date", "predicted_resistance", "lower_bound", "upper_bound", "trend"]

        # Add metadata
        forecast_clean["country"] = country
        forecast_clean["pathogen"] = pathogen
        forecast_clean["antibiotic"] = antibiotic
        forecast_clean["forecast_horizon"] = [0] * len(data) + list(range(1, forecast_periods + 1))
        forecast_clean["is_historical"] = forecast_clean["forecast_horizon"] == 0
        forecast_clean["generated_at"] = datetime.now().isoformat()

        # Save forecast results
        safe_country = country.replace(" ", "_").replace("/", "_")
        safe_pathogen = pathogen.replace(" ", "_").replace("/", "_")
        safe_antibiotic = antibiotic.replace(" ", "_").replace("/", "_")

        output_prefix = f"forecast_{safe_country}_{safe_pathogen}_{safe_antibiotic}"
        csv_file = f"data/{output_prefix}.csv"
        png_file = f"data/{output_prefix}.png"

        # Save CSV
        forecast_clean.to_csv(csv_file, index=False, float_format="%.2f")
        print(f"✅ Forecast saved to: {csv_file}")

        # Generate and save plot
        fig = plt.figure(figsize=(12, 8))

        # Plot historical data
        plt.scatter(data['ds'], data['y'], color='blue', label='Historical Data', alpha=0.7, s=30)

        # Plot forecast
        plt.plot(forecast['ds'], forecast['yhat'], color='red', linewidth=2, label='Forecast')
        plt.fill_between(forecast['ds'], forecast['yhat_lower'], forecast['yhat_upper'],
                        color='red', alpha=0.2, label='Confidence Interval (95%)')

        # Add resistance threshold lines
        plt.axhline(y=70, color='orange', linestyle='--', alpha=0.7, label='Warning (70%)')
        plt.axhline(y=80, color='red', linestyle='--', alpha=0.7, label='Critical (80%)')

        # Formatting
        plt.title(f'AMR Forecast: {pathogen} vs {antibiotic} in {country}',
                 fontsize=14, fontweight='bold')
        plt.xlabel('Date')
        plt.ylabel('Resistance Percentage (%)')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)

        # Set y-axis limits
        plt.ylim(0, 100)

        plt.tight_layout()
        plt.savefig(png_file, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"📊 Plot saved to: {png_file}")

        # Show forecast summary
        current_resistance = data['y'].iloc[-1]
        max_forecast = forecast_clean['predicted_resistance'].max()
        latest_forecast = forecast_clean['predicted_resistance'].iloc[-1]

        print("\n📈 Forecast Summary:")
        print(f"   Current resistance: {current_resistance:.1f}%")
        print(f"   Peak forecast resistance: {max_forecast:.1f}%")
        print(f"   24-month forecast: {latest_forecast:.1f}%")
        print(f"   Change from current: {latest_forecast - current_resistance:.1f}%")

        # Risk assessment
        if latest_forecast > 80:
            risk_level = "🚨 CRITICAL RISK"
        elif latest_forecast > 70:
            risk_level = "⚠️ HIGH RISK"
        elif latest_forecast > 50:
            risk_level = "🔶 MODERATE RISK"
        else:
            risk_level = "✅ LOW RISK"

        trend_direction = "↗️ Rising" if latest_forecast > current_resistance + 5 else "→ Stable" if latest_forecast > current_resistance - 5 else "↘️ Falling"
        trend_percent = ((latest_forecast - current_resistance) / current_resistance * 100)

        print(f"Risk Assessment: {risk_level}")
        print(f"Trend: {trend_direction} ({trend_percent:+.1f}%)")

        return forecast_clean

    except Exception as e:
        print(f"❌ Forecast failed: {e}")
        return None

def main():
    """Main command-line interface."""
    if len(sys.argv) != 4:
        print("Usage: python pipeline/amr_forecast.py <country> <pathogen> <antibiotic>")
        print("\nExample:")
        print('python pipeline/amr_forecast.py "India" "E.coli" "Ciprofloxacin"')
        print('python pipeline/amr_forecast.py "USA" "Salmonella" "Azithromycin"')
        print("\nFor full list of available combinations, check data/amr_merged.csv")
        sys.exit(1)

    country, pathogen, antibiotic = sys.argv[1], sys.argv[2], sys.argv[3]

    print("🚀 AMR Forecasting Pipeline")
    print("=" * 50)

    # Load unified dataset
    df = load_unified_data()

    # Generate forecast
    result = forecast_amr(df, country, pathogen, antibiotic)

    if result is not None:
        print("\n✅ Forecasting complete!")
        print("📁 Check data/ folder for forecast CSV and plot PNG files")
    else:
        print("\n❌ Forecasting failed. Check parameters and try again.")

if __name__ == "__main__":
    main()
