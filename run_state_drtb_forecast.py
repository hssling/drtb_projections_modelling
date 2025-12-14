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

def weighted_state_drtb_forecast():
    print("Generating State-Level DR-TB Forecasts (2025-2030)...")
    
    # 1. Load Data
    # State Total Notifications History
    df_state_ts = pd.read_csv(os.path.join(DATA_DIR, 'tb_notifications_comprehensive_17_24.csv'))
    
    # National DR-TB Percentage Forecast (from previous step)
    # We derived a linear trend for % New Cases with RR-TB: rising from ~3.5% to ~3.7%
    # Let's reconstruct that trend vector for 2025-2030
    # National % in 2024 was approx 3.6%. Trend slope was +0.1% per year approx.
    # Let's load the exact file if possible, or re-calculate for consistency.
    # We will use the 'linear' projection of the percentage we visualized previously.
    # For robust estimation: 
    # Year: [2024, 2025, 2026, 2027, 2028, 2029, 2030]
    # Pct:  [3.6,  3.7,  3.8,  3.9,  4.0,  4.1,  4.2] (Assumption: Aggressive resistance growth scenario)
    # Actually, let's stick to the conservative historical trend: 2015(2.8) -> 2024(3.6) is +0.09/year.
    future_years = [2025, 2026, 2027, 2028, 2029, 2030]
    dr_rate_projections = {
        2025: 0.037,
        2026: 0.038,
        2027: 0.039,
        2028: 0.040,
        2029: 0.041,
        2030: 0.042
    }
    
    # 2. Forecast Total TB for EACH State (2025-2030)
    state_results = []
    
    for index, row in df_state_ts.iterrows():
        state = row['State']
        # Extract history
        history = row[['2017','2018','2019','2020','2021','2022','2023','2024']].astype(float)
        
        # Forecast Model (Exponential Smoothing per state)
        # Handle zeros/missing
        if history.sum() == 0:
            continue
            
        try:
            model = ExponentialSmoothing(history.values, trend='add', damped_trend=True, seasonal=None).fit()
            forecast_total = model.forecast(6) # 6 years
            
            # Calculate DR-TB Burden for each future year
            state_forecast = {'State': state}
            
            for i, year in enumerate(future_years):
                total_cases = max(0, forecast_total[i]) # No negative cases
                dr_rate = dr_rate_projections[year]
                drtb_cases = total_cases * dr_rate
                
                state_forecast[f'Total_{year}'] = int(total_cases)
                state_forecast[f'DRTB_{year}'] = int(drtb_cases)
                
            state_results.append(state_forecast)
            
        except Exception as e:
            print(f"Skipping {state}: {e}")
            
    df_results = pd.DataFrame(state_results)
    
    # 3. Save Results
    output_csv = os.path.join(OUTPUT_DIR, 'state_drtb_forecasts_2030.csv')
    df_results.to_csv(output_csv, index=False)
    print(f"Saved State Forecasts to {output_csv}")
    
    # 4. Visualization: Top 10 High Burden States for DR-TB in 2030
    df_top10 = df_results.sort_values(by='DRTB_2030', ascending=False).head(10)
    
    plt.figure(figsize=(12, 8))
    bars = plt.barh(df_top10['State'], df_top10['DRTB_2030'], color='darkred')
    plt.xlabel('Projected Number of Drug-Resistant TB Cases (2030)')
    plt.title('Projected DR-TB Hotspots in 2030 (Top 10 States)')
    plt.gca().invert_yaxis() # Highest on top
    
    # Add labels
    for bar in bars:
        width = bar.get_width()
        plt.text(width + 50, bar.get_y() + bar.get_height()/2, 
                 f'{int(width):,}', va='center', fontsize=10)
                 
    plt.grid(axis='x', alpha=0.3)
    
    plot_path = os.path.join(OUTPUT_DIR, 'state_drtb_hotspots_2030.png')
    plt.savefig(plot_path)
    print(f"Saved Hotspot Plot to {plot_path}")

if __name__ == "__main__":
    weighted_state_drtb_forecast()
