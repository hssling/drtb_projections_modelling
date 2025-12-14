import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.arima.model import ARIMA
from sklearn.metrics import mean_squared_error
import warnings

warnings.filterwarnings('ignore')

# --- CONFIG ---
DATA_DIR = r'd:\research-automation\tb_amr_project\data\processed'
OUTPUT_DIR = r'd:\research-automation\tb_amr_project\analysis_results'
os.makedirs(OUTPUT_DIR, exist_ok=True)

def project_dr_tb_burden():
    print("Projecting Drug-Resistant TB Burden (to 2030)...")
    
    # Load Master DR-TB Data
    dr_file = os.path.join(DATA_DIR, 'master_dr_tb_national_india.csv')
    df_dr = pd.read_csv(dr_file)
    
    # Filter for years with valid estimates (2015-2024 per previous view)
    df_model = df_dr.dropna(subset=['e_inc_rr_num'])
    if df_model.empty:
        print("Error: No valid DR-TB data found for projection.")
        return

    # 1. DR-TB Incidence Numbers (Absolute Burden)
    ts_burden = df_model.set_index('year')['e_inc_rr_num']
    
    # Model 1: Holt-Winters (Trend)
    model_hw = ExponentialSmoothing(ts_burden, trend='add', damped_trend=True, seasonal=None).fit()
    forecast_hw = model_hw.forecast(6) # 2025-2030
    
    # Model 2: ARIMA (Auto-Regressive)
    # Simple ARIMA(1,1,0) assumption for trend
    model_arima = ARIMA(ts_burden, order=(1,1,0)).fit()
    forecast_arima = model_arima.forecast(6)
    
    # Model 3: Linear Trend (Simple)
    # Using numpy polyfit
    X = ts_burden.index.values
    y = ts_burden.values
    z = np.polyfit(X, y, 1)
    p = np.poly1d(z)
    future_years = np.arange(2025, 2031)
    forecast_linear = p(future_years)
    
    # Combine Forecasts
    df_forecast = pd.DataFrame({
        'Year': future_years,
        'HoltWinters': forecast_hw.values,
        'ARIMA': forecast_arima.values,
        'Linear': forecast_linear
    })
    
    # Plot Comparison
    plt.figure(figsize=(10, 6))
    plt.plot(ts_burden.index, ts_burden.values, 'o-', color='black', label='Historical Estimates (WHO)')
    plt.plot(df_forecast['Year'], df_forecast['HoltWinters'], 'x--', label='Holt-Winters (Damp)')
    plt.plot(df_forecast['Year'], df_forecast['ARIMA'], 's--', label='ARIMA')
    plt.plot(df_forecast['Year'], df_forecast['Linear'], '^--', label='Linear Trend')
    
    plt.title('Projected Incidence of MDR/RR-TB in India (2025-2030)')
    plt.ylabel('Estimated Number of Cases')
    plt.xlabel('Year')
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    output_plot = os.path.join(OUTPUT_DIR, 'drtb_burden_forecast_comparison.png')
    plt.savefig(output_plot)
    print(f"DR-TB Burden Plot saved to {output_plot}")
    
    # 2. Proportion of New Cases with RR-TB (Risk)
    # Analyze the percentage trend: 'e_rr_pct_new'
    ts_pct = df_model.set_index('year')['e_rr_pct_new']
    
    plt.figure(figsize=(10, 6))
    plt.plot(ts_pct.index, ts_pct.values, 'o-', color='purple', label='% New Cases with RR-TB')
    
    # Simple forecast for percentage
    z_pct = np.polyfit(ts_pct.index.values, ts_pct.values, 1)
    p_pct = np.poly1d(z_pct)
    forecast_pct = p_pct(future_years)
    
    plt.plot(future_years, forecast_pct, '--', color='purple', alpha=0.5, label='Trend')
    plt.title('Trend: % of New TB Cases with Drug Resistance')
    plt.ylabel('Percentage (%)')
    plt.grid(True)
    plt.legend()
    plt.savefig(os.path.join(OUTPUT_DIR, 'drtb_percentage_trend.png'))
    
    # Save Data
    df_forecast.to_csv(os.path.join(OUTPUT_DIR, 'drtb_forecast_data.csv'), index=False)
    print(df_forecast)

if __name__ == "__main__":
    project_dr_tb_burden()
