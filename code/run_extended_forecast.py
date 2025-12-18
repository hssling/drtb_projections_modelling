import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
from statsmodels.tsa.holtwinters import ExponentialSmoothing
import warnings

warnings.filterwarnings('ignore')

# --- CONFIG ---
DATA_DIR = r'd:\research-automation\tb_amr_project\data\processed'
OUTPUT_DIR = r'd:\research-automation\tb_amr_project\analysis_results'
os.makedirs(OUTPUT_DIR, exist_ok=True)

def extended_forecast():
    print("Generating Extended Forecast (2025-2030)...")
    
    # Load Data
    ts_file = os.path.join(DATA_DIR, 'tb_notifications_comprehensive_17_24.csv')
    df_ts = pd.read_csv(ts_file)
    
    # Prepare National Time Series
    year_cols = [str(y) for y in range(2017, 2025)]
    national_ts = df_ts[year_cols].sum(axis=0)
    national_ts.index = pd.to_datetime([f"{y}-12-31" for y in year_cols])
    
    # Model: Holt-Winters (Trend Only, likely no seasonality in annual data)
    # Damping trend slightly to avoid unrealistic explosive growth over 6 years
    model = ExponentialSmoothing(national_ts, trend='add', damped_trend=True, seasonal=None).fit()
    
    # Forecast 6 years (2025-2030)
    forecast_years = 6
    forecast = model.forecast(forecast_years)
    
    # 95% Confidence Intervals (Simulation based for HW or using simple sigma)
    # Statsmodels forecast output doesn't give intervals directly for HW easily, 
    # we'll approximate using residual std deviation for visualization
    residuals = model.resid
    std_resid = residuals.std()
    
    # Create Forecast DataFrame
    future_years = range(2025, 2031)
    df_forecast = pd.DataFrame({
        'Year': future_years,
        'Predicted_Cases': forecast.values,
        'Lower_CI': forecast.values - (1.96 * std_resid * np.sqrt(np.arange(1, 7))),
        'Upper_CI': forecast.values + (1.96 * std_resid * np.sqrt(np.arange(1, 7)))
    })
    
    # Plotting
    plt.figure(figsize=(12, 7))
    
    # Historical
    plt.plot(national_ts.index.year, national_ts.values / 1e6, 'o-', color='black', label='Observed (2017-2024)', linewidth=2)
    
    # Forecast
    plt.plot(df_forecast['Year'], df_forecast['Predicted_Cases'] / 1e6, 'o--', color='red', label='Forecast (2025-2030)', linewidth=2)
    
    # Confidence Interval
    plt.fill_between(df_forecast['Year'], 
                     df_forecast['Lower_CI'] / 1e6, 
                     df_forecast['Upper_CI'] / 1e6, 
                     color='red', alpha=0.15, label='95% Confidence Interval')
    
    # Goals/Targets (Optional Reference) - e.g., NSP Goal
    # plt.axhline(y=... , color='green', linestyle=':', label='Target')
    
    plt.title('India National TB Notification Forecast (2025-2030)', fontsize=14)
    plt.xlabel('Year', fontsize=12)
    plt.ylabel('Total Notifications (Millions)', fontsize=12)
    plt.grid(True, alpha=0.3, linestyle='--')
    plt.xticks(list(range(2017, 2031)))
    plt.legend(loc='upper left')
    
    # Add labels
    for x, y in zip(df_forecast['Year'], df_forecast['Predicted_Cases']):
        plt.text(x, y/1e6 + 0.05, f"{y/1e6:.2f}M", ha='center', color='darkred', fontsize=9)
        
    output_plot = os.path.join(OUTPUT_DIR, 'national_forecast_2030.png')
    plt.savefig(output_plot, dpi=300)
    print(f"Forecast plot saved: {output_plot}")
    
    output_csv = os.path.join(OUTPUT_DIR, 'national_forecast_2030.csv')
    df_forecast.to_csv(output_csv, index=False)
    print(f"Forecast data saved: {output_csv}")
    print("\nForecast Values:")
    print(df_forecast)

if __name__ == "__main__":
    extended_forecast()
