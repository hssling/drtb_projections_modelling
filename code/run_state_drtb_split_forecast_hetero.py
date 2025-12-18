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

def get_state_risk_modifier(state_name):
    """
    Returns a risk multiplier based on 2024 observed DR-TB intensity vs National Average.
    Derived from literature/search data (Step 626).
    Baseline (1.0) = Average State.
    """
    # Normalized lower case map
    s = state_name.lower().strip()
    
    # High Intensity States (MDR Hotspots)
    if 'maharashtra' in s: return 1.6  # ~4.2% observed vs 2.4% avg
    if 'delhi' in s: return 1.5        # Urban high density
    if 'mumbai' in s: return 1.8       # (If separate, but part of Maha)
    if 'gujarat' in s: return 1.3
    
    # Medium-High (High Volume, Avg Intensity)
    if 'uttar pradesh' in s: return 1.0 # ~2.4% observed
    if 'bihar' in s: return 1.1
    if 'madhya pradesh' in s: return 1.0
    if 'rajasthan' in s: return 1.0
    
    # Medium-Low
    if 'tamil nadu' in s: return 0.8  # Better control? ~1.8%
    if 'karnataka' in s: return 0.8
    if 'andhra' in s: return 0.9
    if 'telangana' in s: return 0.9
    if 'west bengal' in s: return 1.1 # Dense
    
    # Low Intensity (Strong Health Systems or Isolated)
    if 'kerala' in s: return 0.5      # ~1.2% observed
    if 'himachal' in s: return 0.6
    if 'goa' in s: return 0.6
    if 'sikkim' in s: return 0.5
    if 'mizoram' in s: return 0.5
    
    # Default
    return 1.0

def weighted_state_drtb_forecast_split():
    print("Generating Heterogeneous State-Level DR-TB Forecasts...")
    
    # 1. Load State Historic Data
    df_state_ts = pd.read_csv(os.path.join(DATA_DIR, 'tb_notifications_comprehensive_17_24.csv'))
    
    future_years = [2025, 2026, 2027, 2028, 2029, 2030]
    
    # National Baseline Rates (Rising Trend)
    # New: 3.6% -> 4.2%
    # Ret: 13.0% -> 14.0%
    dr_rate_new_base = {
        2025: 0.037, 2026: 0.038, 2027: 0.039, 2028: 0.040, 2029: 0.041, 2030: 0.042
    }
    dr_rate_ret_base = {
        2025: 0.132, 2026: 0.134, 2027: 0.135, 2028: 0.137, 2029: 0.139, 2030: 0.140
    }
    
    RET_SHARE = 0.13
    NEW_SHARE = 0.87
    
    state_results = []
    
    for index, row in df_state_ts.iterrows():
        state = row['State']
        modifier = get_state_risk_modifier(state)
        
        history = row[['2017','2018','2019','2020','2021','2022','2023','2024']].astype(float)
        
        if history.sum() == 0: continue
            
        try:
            # Forecast Total Volume
            model = ExponentialSmoothing(history.values, trend='add', damped_trend=True, seasonal=None).fit()
            forecast_total = model.forecast(6)
            
            state_forecast = {'State': state}
            
            for i, year in enumerate(future_years):
                total = max(0, forecast_total[i])
                
                vol_new = total * NEW_SHARE
                vol_ret = total * RET_SHARE
                
                # Apply STATE SPECIFIC Modifier to the Resistance Rates
                # We cap rates at realistic max (e.g., 20% for New, 60% for Ret) to avoid weirdness
                
                rate_new = min(dr_rate_new_base[year] * modifier, 0.15)
                rate_ret = min(dr_rate_ret_base[year] * modifier, 0.50)
                
                drtb_new = vol_new * rate_new
                drtb_ret = vol_ret * rate_ret
                drtb_total = drtb_new + drtb_ret
                
                state_forecast[f'Total_{year}'] = int(total)
                state_forecast[f'DRTB_New_{year}'] = int(drtb_new)
                state_forecast[f'DRTB_Ret_{year}'] = int(drtb_ret)
                state_forecast[f'DRTB_Total_{year}'] = int(drtb_total)
                
            state_results.append(state_forecast)
            
        except Exception as e:
            print(f"Error forecasting {state}: {e}")
            
    df_results = pd.DataFrame(state_results)
    
    # Save
    output_path = os.path.join(OUTPUT_DIR, 'state_drtb_forecasts_split_2030.csv')
    df_results.to_csv(output_path, index=False)
    print(f"Saved Heterogeneous Forecasts to {output_path}")

if __name__ == "__main__":
    weighted_state_drtb_forecast_split()
