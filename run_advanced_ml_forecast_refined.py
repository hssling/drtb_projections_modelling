import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
from sklearn.preprocessing import PolynomialFeatures, StandardScaler
from sklearn.linear_model import BayesianRidge
from sklearn.pipeline import make_pipeline
from xgboost import XGBRegressor
import warnings

warnings.filterwarnings('ignore')

# --- CONFIG ---
DATA_DIR = r'd:\research-automation\tb_amr_project\data\processed'
OUTPUT_DIR = r'd:\research-automation\tb_amr_project\analysis_results'
os.makedirs(OUTPUT_DIR, exist_ok=True)

def advanced_ml_forecast_refined():
    print("Running Refined Advanced Forecasting (Bayesian Poly, Linear XGB)...")
    
    # 1. Load Data
    df_ts = pd.read_csv(os.path.join(DATA_DIR, 'tb_notifications_comprehensive_17_24.csv'))
    year_cols = [str(y) for y in range(2017, 2025)]
    national_ts = df_ts[year_cols].sum(axis=0)
    
    # X, y
    years = np.array(range(2017, 2025))
    X = years.reshape(-1, 1)
    y = national_ts.values
    
    # Future
    future_years = np.array(range(2025, 2031)).reshape(-1, 1)
    
    # --- MODEL 1: Bayesian Ridge with Polynomial Features (Degree 2) ---
    # This allows capturing the accelerating recovery trend
    # We treat 2020, 2021 as anomalies but allow the model to see them.
    # To improve trend capture, let's fit primarily on the structural trend or use robust features.
    
    model_bayes = make_pipeline(PolynomialFeatures(degree=2), BayesianRidge())
    model_bayes.fit(X, y)
    pred_bayes, pred_std = model_bayes.predict(future_years, return_std=True)
    
    # --- MODEL 2: XGBoost Linear (Extrapolator) ---
    # Standard trees (gbtree) cannot extrapolate. gblinear can.
    model_xgb = XGBRegressor(booster='gblinear', n_estimators=200, learning_rate=0.1)
    model_xgb.fit(X, y)
    pred_xgb = model_xgb.predict(future_years)
    
    # --- SCENARIOS (Driven by Bayesian Uncertainty) ---
    # Defining Scenarios for 2030 Strategy
    # Baseline: The Ensemble Projection
    # Optimistic (Intervention Success): Trend bends downwards (-1.5 sigma from trend)
    # Pessimistic (Resistance/Failure): Trend follows accelerating quadratic path limits
    
    optimistic = pred_bayes - (2.0 * pred_std)
    pessimistic = pred_bayes + (2.0 * pred_std)
    
    # Ensemble (Weighted)
    # 50% Bayesian Poly (captures curvature), 50% Linear XGB (captures steady growth)
    pred_ensemble = (0.5 * pred_bayes) + (0.5 * pred_xgb)
    
    # --- VISUALIZATION ---
    plt.figure(figsize=(10, 6))
    
    # History
    plt.plot(years, y/1e6, 'ko-', label='Observed Cases', linewidth=2)
    
    # Projections
    plt.plot(future_years, pred_bayes/1e6, 'g--', label='Bayesian Polynomial (Trend)', linewidth=1.5)
    plt.plot(future_years, pred_xgb/1e6, 'b:', label='XGBoost Linear', linewidth=1.5)
    plt.plot(future_years, pred_ensemble/1e6, 'm-', label='Ensemble Projection (Final)', linewidth=3)
    
    # Scenarios Coverage
    plt.fill_between(future_years.flatten(), optimistic/1e6, pessimistic/1e6, 
                     color='purple', alpha=0.1, label='Sensitivity Cone (95% CI)')
    
    plt.title('Advanced ML Forecasting & Scenarios (2025-2030)', fontsize=14)
    plt.xlabel('Year')
    plt.ylabel('Notifications (Millions)')
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    plot_path = os.path.join(OUTPUT_DIR, 'advanced_forecast_refined.png')
    plt.savefig(plot_path)
    print(f"Refined Plot saved to {plot_path}")
    
    # Export
    df_res = pd.DataFrame({
        'Year': future_years.flatten(),
        'BayesianRidge_Poly': pred_bayes,
        'XGBoost_Linear': pred_xgb,
        'Ensemble_Projection': pred_ensemble,
        'Scenario_Optimistic': optimistic,
        'Scenario_Pessimistic': pessimistic
    })
    
    output_csv = os.path.join(OUTPUT_DIR, 'advanced_forecast_refined.csv')
    df_res.to_csv(output_csv, index=False)
    print("Refined Forecast Data Saved.")
    print(df_res)
    
    # Scenario Interpretation
    print(f"\n2030 Projection (Ensemble): {int(pred_ensemble[-1]):,}")
    print(f"2030 Pessimistic (High Burden): {int(pessimistic[-1]):,}")
    print(f"2030 Optimistic (Control Success): {int(optimistic[-1]):,}")

if __name__ == "__main__":
    advanced_ml_forecast_refined()
