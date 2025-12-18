#!/usr/bin/env python3
"""
Bootstrap Confidence Intervals for MDR-TB Forecasts
Implements uncertainty quantification via parametric bootstrap
"""

import numpy as np
import pandas as pd
import json
import matplotlib.pyplot as plt
import seaborn as sns
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from scipy import stats
import os

# Configuration
np.random.seed(42)
N_BOOTSTRAP = 1000
CONFIDENCE_LEVEL = 0.95
OUTPUT_DIR = 'd:/research-automation/tb_amr_project/supplementary_materials'
os.makedirs(OUTPUT_DIR, exist_ok=True)

def load_data():
    """Load historical MDR-TB data"""
    with open('d:/research-automation/tb_amr_project/authentic_drtb_forecast_india_2025.json', 'r') as f:
        data = json.load(f)
    
    df = pd.DataFrame(data['historical_data'])
    return df['estimated_true_burden'].values

def fit_base_model(data):
    """Fit base Holt-Winters model"""
    model = ExponentialSmoothing(
        data,
        trend='add',
        damped_trend=True,
        initialization_method='estimated'
    )
    fitted = model.fit(optimized=True)
    return fitted

def parametric_bootstrap(data, n_bootstrap=N_BOOTSTRAP):
    """
    Parametric bootstrap for Holt-Winters model
    
    Process:
    1. Fit base model to observed data
    2. Extract residuals
    3. For each bootstrap iteration:
       a. Resample residuals with replacement
       b. Generate synthetic time series
       c. Refit model
       d. Generate forecast
    4. Calculate percentile-based confidence intervals
    """
    print(f"Running {n_bootstrap} bootstrap iterations...")
    
    # Fit base model
    base_fitted = fit_base_model(data)
    base_params = base_fitted.params
    residuals = base_fitted.resid
    
    # Storage for bootstrap forecasts
    forecast_horizon = 10  # 2025-2034
    bootstrap_forecasts = np.zeros((n_bootstrap, forecast_horizon))
    
    for i in range(n_bootstrap):
        if (i + 1) % 100 == 0:
            print(f"  Iteration {i+1}/{n_bootstrap}")
        
        # Resample residuals
        resampled_residuals = np.random.choice(residuals, size=len(data), replace=True)
        
        # Generate synthetic data
        synthetic_data = base_fitted.fittedvalues + resampled_residuals
        
        # Refit model to synthetic data
        try:
            model = ExponentialSmoothing(
                synthetic_data,
                trend='add',
                damped_trend=True,
                initialization_method='estimated'
            )
            fitted = model.fit(
                smoothing_level=base_params['smoothing_level'],
                smoothing_trend=base_params['smoothing_trend'],
                damping_trend=base_params['damping_trend'],
                optimized=False  # Use base parameters
            )
            
            # Generate forecast
            forecast = fitted.forecast(steps=forecast_horizon)
            bootstrap_forecasts[i, :] = forecast
            
        except:
            # If fit fails, use base forecast
            bootstrap_forecasts[i, :] = base_fitted.forecast(steps=forecast_horizon)
    
    return bootstrap_forecasts, base_fitted

def calculate_confidence_intervals(bootstrap_forecasts, confidence_level=CONFIDENCE_LEVEL):
    """Calculate percentile-based confidence intervals"""
    alpha = 1 - confidence_level
    lower_percentile = (alpha / 2) * 100
    upper_percentile = (1 - alpha / 2) * 100
    
    lower_bound = np.percentile(bootstrap_forecasts, lower_percentile, axis=0)
    upper_bound = np.percentile(bootstrap_forecasts, upper_percentile, axis=0)
    median = np.percentile(bootstrap_forecasts, 50, axis=0)
    
    return lower_bound, median, upper_bound

def generate_uncertainty_table(bootstrap_forecasts):
    """Generate table of forecast uncertainty"""
    years = range(2025, 2035)
    lower, median, upper = calculate_confidence_intervals(bootstrap_forecasts)
    
    # Load base forecast for comparison
    with open('d:/research-automation/tb_amr_project/authentic_drtb_forecast_india_2025.json', 'r') as f:
        data = json.load(f)
    base_forecast = [item['forecast_burden'] for item in data['forecast_scenarios']]
    
    results = []
    for i, year in enumerate(years):
        results.append({
            'Year': year,
            'Point_Estimate': base_forecast[i],
            'Bootstrap_Median': median[i],
            'CI_Lower_95': lower[i],
            'CI_Upper_95': upper[i],
            'CI_Width': upper[i] - lower[i],
            'Relative_Uncertainty': ((upper[i] - lower[i]) / median[i]) * 100
        })
    
    df = pd.DataFrame(results)
    
    # Save to CSV
    output_path = os.path.join(OUTPUT_DIR, 'Bootstrap_Confidence_Intervals.csv')
    df.to_csv(output_path, index=False)
    print(f"\n✓ Saved uncertainty table to: {output_path}")
    
    return df

def plot_forecast_with_uncertainty(data, bootstrap_forecasts, base_fitted):
    """Generate forecast plot with bootstrap confidence intervals"""
    years_hist = range(2017, 2025)
    years_forecast = range(2025, 2035)
    
    lower, median, upper = calculate_confidence_intervals(bootstrap_forecasts)
    
    # Load base forecast
    with open('d:/research-automation/tb_amr_project/authentic_drtb_forecast_india_2025.json', 'r') as f:
        json_data = json.load(f)
    base_forecast = [item['forecast_burden'] for item in json_data['forecast_scenarios']]
    
    plt.figure(figsize=(14, 8))
    
    # Historical data
    plt.plot(years_hist, data, 'ko-', linewidth=2, markersize=8, label='Historical Data', zorder=5)
    
    # Point forecast
    plt.plot(years_forecast, base_forecast, 'r--', linewidth=2.5, label='Point Forecast (Holt-Winters)', zorder=4)
    
    # Bootstrap median
    plt.plot(years_forecast, median, 'b:', linewidth=2, label='Bootstrap Median', alpha=0.7, zorder=3)
    
    # 95% Confidence interval
    plt.fill_between(years_forecast, lower, upper, alpha=0.3, color='blue', label='95% Confidence Interval (Bootstrap)', zorder=2)
    
    # Forecast start line
    plt.axvline(x=2024.5, color='gray', linestyle=':', linewidth=2, alpha=0.8, label='Forecast Start (2025)')
    
    plt.title('MDR-TB Burden Forecast with Bootstrap Uncertainty Quantification', fontsize=14, fontweight='bold', pad=20)
    plt.xlabel('Year', fontsize=12)
    plt.ylabel('Estimated True Burden (Cases)', fontsize=12)
    plt.legend(loc='lower left', frameon=True, fancybox=True, framealpha=0.9)
    plt.grid(True, alpha=0.3)
    
    # Ensure 2025 is visible
    ticks = list(range(2017, 2035, 2))
    if 2025 not in ticks:
        ticks.append(2025)
    plt.xticks(sorted(ticks))
    
    plt.tight_layout()
    output_path = os.path.join(OUTPUT_DIR, 'Supplementary_Figure_S1_Bootstrap_Uncertainty.png')
    plt.savefig(output_path, dpi=300)
    print(f"✓ Saved uncertainty plot to: {output_path}")
    plt.close()

def generate_residual_diagnostics(base_fitted):
    """Generate comprehensive residual diagnostic plots"""
    residuals = base_fitted.resid
    fitted_values = base_fitted.fittedvalues
    
    fig, axes = plt.subplots(2, 3, figsize=(16, 10))
    fig.suptitle('Supplementary Figure S2: Model Residual Diagnostics', fontsize=14, fontweight='bold')
    
    # 1. Residuals vs Fitted
    axes[0, 0].scatter(fitted_values, residuals, alpha=0.6, s=100)
    axes[0, 0].axhline(y=0, color='r', linestyle='--', linewidth=2)
    axes[0, 0].set_xlabel('Fitted Values')
    axes[0, 0].set_ylabel('Residuals')
    axes[0, 0].set_title('(A) Residuals vs. Fitted Values')
    axes[0, 0].grid(True, alpha=0.3)
    
    # 2. Q-Q Plot
    stats.probplot(residuals, dist="norm", plot=axes[0, 1])
    axes[0, 1].set_title('(B) Normal Q-Q Plot')
    axes[0, 1].grid(True, alpha=0.3)
    
    # 3. Histogram of Residuals
    axes[0, 2].hist(residuals, bins=5, edgecolor='black', alpha=0.7)
    axes[0, 2].axvline(x=0, color='r', linestyle='--', linewidth=2)
    axes[0, 2].set_xlabel('Residuals')
    axes[0, 2].set_ylabel('Frequency')
    axes[0, 2].set_title('(C) Histogram of Residuals')
    axes[0, 2].grid(True, alpha=0.3)
    
    # 4. ACF Plot
    from statsmodels.graphics.tsaplots import plot_acf
    plot_acf(residuals, lags=3, ax=axes[1, 0], alpha=0.05)
    axes[1, 0].set_title('(D) Autocorrelation Function')
    axes[1, 0].grid(True, alpha=0.3)
    
    # 5. PACF Plot
    from statsmodels.graphics.tsaplots import plot_pacf
    plot_pacf(residuals, lags=3, ax=axes[1, 1], alpha=0.05)
    axes[1, 1].set_title('(E) Partial Autocorrelation Function')
    axes[1, 1].grid(True, alpha=0.3)
    
    # 6. Residuals over Time
    years = range(2017, 2025)
    axes[1, 2].plot(years, residuals, 'bo-', linewidth=2, markersize=8)
    axes[1, 2].axhline(y=0, color='r', linestyle='--', linewidth=2)
    axes[1, 2].set_xlabel('Year')
    axes[1, 2].set_ylabel('Residuals')
    axes[1, 2].set_title('(F) Residuals Over Time')
    axes[1, 2].grid(True, alpha=0.3)
    
    plt.tight_layout()
    output_path = os.path.join(OUTPUT_DIR, 'Supplementary_Figure_S2_Residual_Diagnostics.png')
    plt.savefig(output_path, dpi=300)
    print(f"✓ Saved residual diagnostics to: {output_path}")
    plt.close()

def main():
    """Main execution"""
    print("=" * 60)
    print("BOOTSTRAP UNCERTAINTY QUANTIFICATION")
    print("=" * 60)
    
    # Load data
    print("\n1. Loading historical data...")
    data = load_data()
    print(f"   Loaded {len(data)} years of data (2017-2024)")
    
    # Run bootstrap
    print(f"\n2. Running parametric bootstrap ({N_BOOTSTRAP} iterations)...")
    bootstrap_forecasts, base_fitted = parametric_bootstrap(data, n_bootstrap=N_BOOTSTRAP)
    print("   ✓ Bootstrap complete")
    
    # Generate uncertainty table
    print("\n3. Generating uncertainty quantification table...")
    df_uncertainty = generate_uncertainty_table(bootstrap_forecasts)
    print("\n   Preview:")
    print(df_uncertainty.to_string(index=False))
    
    # Plot forecast with uncertainty
    print("\n4. Generating forecast plot with confidence intervals...")
    plot_forecast_with_uncertainty(data, bootstrap_forecasts, base_fitted)
    
    # Generate residual diagnostics
    print("\n5. Generating residual diagnostic plots...")
    generate_residual_diagnostics(base_fitted)
    
    # Summary statistics
    print("\n" + "=" * 60)
    print("SUMMARY STATISTICS")
    print("=" * 60)
    print(f"\nMedian CI Width (2030): ±{df_uncertainty.loc[df_uncertainty['Year']==2030, 'CI_Width'].values[0]/2:,.0f} cases")
    print(f"Relative Uncertainty (2030): {df_uncertainty.loc[df_uncertainty['Year']==2030, 'Relative_Uncertainty'].values[0]:.1f}%")
    print(f"\nMedian CI Width (2034): ±{df_uncertainty.loc[df_uncertainty['Year']==2034, 'CI_Width'].values[0]/2:,.0f} cases")
    print(f"Relative Uncertainty (2034): {df_uncertainty.loc[df_uncertainty['Year']==2034, 'Relative_Uncertainty'].values[0]:.1f}%")
    
    print("\n" + "=" * 60)
    print("✓ ALL ANALYSES COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()
