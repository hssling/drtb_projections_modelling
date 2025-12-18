import pandas as pd
import numpy as np
import os
from statsmodels.tsa.holtwinters import ExponentialSmoothing
import warnings

warnings.filterwarnings('ignore')

# --- CONFIG ---
DATA_DIR = r'd:\research-automation\tb_amr_project\data\processed'
OUTPUT_DIR = r'd:\research-automation\tb_amr_project\analysis_results'
os.makedirs(OUTPUT_DIR, exist_ok=True)

def weighted_state_drtb_forecast_split():
    print("Generating State-Level DR-TB Forecasts (New vs Retreatment)...")
    
    # 1. Load State Historic Data (Total Notifications)
    df_state_ts = pd.read_csv(os.path.join(DATA_DIR, 'tb_notifications_comprehensive_17_24.csv'))
    
    # 2. National Projections for Parameters
    # Derived from Analysis: 
    # Retreatment % of Total Cases ≈ 13% (National Standard)
    # DR Rate in New Cases: Rising from 3.6% (2024) to 4.2% (2030)
    # DR Rate in Ret Cases: Rising from 13.0% (2024) to 14.0% (2030)
    
    future_years = [2025, 2026, 2027, 2028, 2029, 2030]
    
    # Define Rate Vectors
    dr_rate_new = {
        2025: 0.037, 2026: 0.038, 2027: 0.039, 
        2028: 0.040, 2029: 0.041, 2030: 0.042
    }
    dr_rate_ret = {
        2025: 0.132, 2026: 0.134, 2027: 0.135,
        2028: 0.137, 2029: 0.139, 2030: 0.140
    }
    
    # Split Ratio
    RET_SHARE = 0.13
    NEW_SHARE = 1.0 - RET_SHARE
    
    state_results = []
    
    for index, row in df_state_ts.iterrows():
        state = row['State']
        history = row[['2017','2018','2019','2020','2021','2022','2023','2024']].astype(float)
        
        if history.sum() == 0: continue
            
        try:
            # Forecast Total Notifications
            model = ExponentialSmoothing(history.values, trend='add', damped_trend=True, seasonal=None).fit()
            forecast_total = model.forecast(6)
            
            state_forecast = {'State': state}
            
            for i, year in enumerate(future_years):
                total = max(0, forecast_total[i])
                
                # Split Volume
                vol_new = total * NEW_SHARE
                vol_ret = total * RET_SHARE
                
                # Apply differential Resistance Rates
                drtb_new = vol_new * dr_rate_new[year]
                drtb_ret = vol_ret * dr_rate_ret[year]
                drtb_total = drtb_new + drtb_ret
                
                # Store
                state_forecast[f'Total_{year}'] = int(total)
                state_forecast[f'DRTB_New_{year}'] = int(drtb_new)
                state_forecast[f'DRTB_Ret_{year}'] = int(drtb_ret)
                state_forecast[f'DRTB_Total_{year}'] = int(drtb_total)
                
            state_results.append(state_forecast)
            
        except Exception as e:
            print(f"Error forecasting {state}: {e}")
            
    df_results = pd.DataFrame(state_results)
    
    # Save Split Forecasts
    output_path = os.path.join(OUTPUT_DIR, 'state_drtb_forecasts_split_2030.csv')
    df_results.to_csv(output_path, index=False)
    print(f"Saved Split Forecasts to {output_path}")
    
    # Summary of National Burden by Type (2030)
    total_new_dr = df_results['DRTB_New_2030'].sum()
    total_ret_dr = df_results['DRTB_Ret_2030'].sum()
    
    print("\n--- 2030 National Projection Summary ---")
    print(f"Projected DR-TB from New Cases: {total_new_dr:,}")
    print(f"Projected DR-TB from Retreatment Cases: {total_ret_dr:,}")
    print(f"Total Projected DR-TB Burden: {total_new_dr + total_ret_dr:,}")
    print("----------------------------------------")

if __name__ == "__main__":
    weighted_state_drtb_forecast_split()
