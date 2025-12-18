import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import warnings

warnings.filterwarnings('ignore')

# --- CONFIG ---
DATA_DIR = r'd:\research-automation\tb_amr_project\data\processed'
OUTPUT_DIR = r'd:\research-automation\tb_amr_project\analysis_results'
os.makedirs(OUTPUT_DIR, exist_ok=True)

def run_policy_scenarios():
    print("Running Policy Scenario Analysis (2025-2030)...")
    
    # 1. Load Baseline Forecast (Ensemble Model)
    # We use the generated advanced forecast data as the "Status Quo"
    df_base = pd.read_csv(os.path.join(OUTPUT_DIR, 'advanced_forecast_refined.csv'))
    
    # Extract Baseline Vector
    years = df_base['Year'].values
    baseline_cases = df_base['Ensemble_Projection'].values
    
    # 2. Define Intervention Parameters (Derived from Literature)
    # TPT Impact: 10% additional annual decline in incidence (Cumulative)
    # BPaL Impact: Reduces Retreatment cases by ~60% (Success rate 56% -> 90%)
    #   Note: Retreatment is ~13% of total. So BPaL impact on TOTAL is ~0.13 * 0.60 = ~8% reduction.
    
    # Scenario A: Aggressive Prevention (TPT + ACF)
    # Hypothesis: ACF finds missing cases immediately (Spike in 2025/26), TPT reduces future cases.
    # Impact: +5% detection in 2025/26, then -10% cumulative decline from 2027.
    
    def scenario_prevention(base_val, year, start_year=2025):
        if year < 2027:
            return base_val * 1.05 # ACF Spike
        else:
            # Compounding reduction from TPT (10% per year starting 2027)
            years_active = year - 2026
            factor = (1 - 0.10) ** years_active
            return base_val * factor

    # Scenario B: Optimized Treatment (BPaL/M Universal)
    # Hypothesis: Stops the "Retreatment" flywheel.
    # Impact: Reduces total burden by cumulative 2% per year (conservative) as retreatment pool shrinks.
    
    def scenario_treatment(base_val, year, start_year=2025):
        years_active = year - 2024
        factor = (1 - 0.02) ** years_active
        return base_val * factor
    
    # Scenario C: Combination (End TB Strategy)
    # Combining both: Spike in detection, then accelerated decline.
    
    cases_prevention = []
    cases_treatment = []
    cases_combination = []
    
    for i, year in enumerate(years):
        val = baseline_cases[i]
        
        # Apply policies
        s_prev = scenario_prevention(val, year)
        s_treat = scenario_treatment(val, year)
        
        # Combined: Multiplicative effect of both interventions
        # Note: We apply the ACF spike from A, and the reduction from both.
        if year < 2027:
            # ACF Spike + Early Treatment gains
            s_combo = val * 1.05 * ((1 - 0.02) ** (year - 2024))
        else:
            # Full TPT + Treatment efficacy
            years_active_tpt = year - 2026
            years_active_tx = year - 2024
            factor_tpt = (1 - 0.12) ** years_active_tpt # Synergistic 12%
            factor_tx = (1 - 0.02) ** years_active_tx
            s_combo = val * factor_tpt * factor_tx
            
        cases_prevention.append(s_prev)
        cases_treatment.append(s_treat)
        cases_combination.append(s_combo)
        
    # 3. Visualization
    plt.figure(figsize=(12, 8))
    
    # Plot Baseline
    plt.plot(years, baseline_cases/1e6, 'k--', label='Status Quo (Current Trend)', linewidth=2)
    
    # Plot Scenarios
    plt.plot(years, np.array(cases_treatment)/1e6, 'b-o', label='Scenario: Universal BPaL/M (Treatment Opt.)', linewidth=1.5)
    plt.plot(years, np.array(cases_prevention)/1e6, 'g-^', label='Scenario: Aggressive TPT + ACF (Prevention)', linewidth=1.5)
    plt.plot(years, np.array(cases_combination)/1e6, 'r-*', label='Scenario: Combination Strategy (End TB)', linewidth=3)
    
    # Reference Line (2015 Baseline ~2.8M? No, 2025 is target)
    # End TB Goal is 80% reduction. Let's show a "Target Zone" at bottom.
    plt.axhline(y=1.0, color='gray', linestyle=':', label='Intermediate Target (1 Million)')
    
    plt.title('Policy Sensitivity Analysis: TB Notifications India (2025-2030)', fontsize=14)
    plt.xlabel('Year')
    plt.ylabel('Projected Annual Cases (Millions)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plot_path = os.path.join(OUTPUT_DIR, 'policy_scenario_analysis.png')
    plt.savefig(plot_path)
    print(f"Scenario Plot saved to {plot_path}")
    
    # 4. Impact Summary & Export
    # Calculate 'Cases Averted' in 2030 vs Baseline
    base_2030 = baseline_cases[-1]
    combo_2030 = cases_combination[-1]
    averted = base_2030 - combo_2030
    pct_reduction = (averted / base_2030) * 100
    
    df_results = pd.DataFrame({
        'Year': years,
        'Baseline': baseline_cases,
        'Prevention_First': cases_prevention,
        'Treatment_First': cases_treatment,
        'Combination_Strategy': cases_combination
    })
    
    csv_path = os.path.join(OUTPUT_DIR, 'policy_scenario_data.csv')
    df_results.to_csv(csv_path, index=False)
    
    print("\n--- Value of Strategy (2030 Projection) ---")
    print(f"Status Quo 2030:      {int(base_2030):,} cases")
    print(f"Combination Strategy: {int(combo_2030):,} cases")
    print(f"Potential Impact:     {int(averted):,} cases averted in 2030 alone ({pct_reduction:.1f}% reduction)")

if __name__ == "__main__":
    run_policy_scenarios()
