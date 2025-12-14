import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import BayesianRidge
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor
import warnings

warnings.filterwarnings('ignore')

# --- CONFIG ---
DATA_DIR = r'd:\research-automation\tb_amr_project\data\processed'
OUTPUT_DIR = r'd:\research-automation\tb_amr_project\analysis_results'
os.makedirs(OUTPUT_DIR, exist_ok=True)

def advanced_ml_forecast_and_scenarios():
    print("Running Advanced Forecasting: Ensemble ML, Bayesian...")
    
    # 1. Load Data
    df_ts = pd.read_csv(os.path.join(DATA_DIR, 'tb_notifications_comprehensive_17_24.csv'))
    
    # Aggregate to National Level
    year_cols = [str(y) for y in range(2017, 2025)]
    national_ts = df_ts[year_cols].sum(axis=0)
    
    X = np.array(range(2017, 2025)).reshape(-1, 1)
    y = national_ts.values
    
    future_years = np.array(range(2025, 2031)).reshape(-1, 1)
    
    # --- MODEL 1: XGBoost ---
    model_xgb = XGBRegressor(n_estimators=100, learning_rate=0.05, objective='reg:squarederror')
    model_xgb.fit(X, y)
    pred_xgb = model_xgb.predict(future_years)
    
    # --- MODEL 2: LightGBM ---
    model_lgbm = LGBMRegressor(n_estimators=100, learning_rate=0.05, verbose=-1)
    model_lgbm.fit(X, y)
    pred_lgbm = model_lgbm.predict(future_years)
    
    # --- MODEL 3: Bayesian Ridge (Probabilistic) ---
    model_bayes = BayesianRidge()
    model_bayes.fit(X, y)
    pred_bayes, pred_std = model_bayes.predict(future_years, return_std=True)
    
    # --- SCENARIO ANALYSIS ---
    # Scenarios defined by Bayesian Uncertainty
    optimistic = pred_bayes - (1.96 * pred_std) # 95% Lower CI (Effective controls)
    pessimistic = pred_bayes + (1.96 * pred_std) # 95% Upper CI (Resistance rise)
    
    # --- HYBRID ENSEMBLE ---
    # Weighted average of XGB, LightGBM, and Bayesian
    # Giving slightly more weight to Bayesian for trend stability on small data
    pred_ensemble = (0.2 * pred_xgb) + (0.2 * pred_lgbm) + (0.6 * pred_bayes)
    
    # --- RESULT DATAFRAME ---
    df_res = pd.DataFrame({
        'Year': future_years.flatten(),
        'XGBoost': pred_xgb,
        'LightGBM': pred_lgbm,
        'BayesianRidge': pred_bayes,
        'Ensemble_Projection': pred_ensemble,
        'Scenario_Optimistic': optimistic,
        'Scenario_Pessimistic': pessimistic
    })
    
    # --- VISUALIZATION ---
    plt.figure(figsize=(12, 8))
    
    # History
    plt.plot(range(2017, 2025), y/1e6, 'ko-', label='Observed (WHO/India)', linewidth=2)
    
    # Models
    plt.plot(future_years, pred_xgb/1e6, 'b:', label='XGBoost')
    plt.plot(future_years, pred_lgbm/1e6, 'c:', label='LightGBM')
    plt.plot(future_years, pred_bayes/1e6, 'g--', label='Bayesian Trend')
    
    # Ensemble
    plt.plot(future_years, pred_ensemble/1e6, 'm-', label='Ensemble Model (Final Projection)', linewidth=3)
    
    # Scenarios
    plt.fill_between(future_years.flatten(), optimistic/1e6, pessimistic/1e6, color='red', alpha=0.1, label='Uncertainty Cone (95% CI)')
    
    plt.title('Advanced Multi-Model TB Forecasting (2025-2030)\nEnsemble ML & Bayesian Scenario Analysis', fontsize=14)
    plt.xlabel('Year')
    plt.ylabel('Notifications (Millions)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plot_path = os.path.join(OUTPUT_DIR, 'advanced_forecast_scenarios.png')
    plt.savefig(plot_path)
    print(f"Plot saved to {plot_path}")
    
    df_res.to_csv(os.path.join(OUTPUT_DIR, 'advanced_forecast_data.csv'), index=False)
    print("Advanced Forecast Data Saved.")
    print(df_res)

if __name__ == "__main__":
    advanced_ml_forecast_and_scenarios()
