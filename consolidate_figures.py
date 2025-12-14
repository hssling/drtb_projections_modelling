import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import matplotlib.gridspec as gridspec

# --- CONFIG ---
DATA_DIR = r'd:\research-automation\tb_amr_project\analysis_results'
OUTPUT_DIR = r'd:\research-automation\tb_amr_project\manuscript_assets'
os.makedirs(OUTPUT_DIR, exist_ok=True)

def generate_figure_1_combined():
    print("Generating Figure 1: National Trends & Scenarios...")
    
    # Load Data
    df_forecast = pd.read_csv(os.path.join(DATA_DIR, 'advanced_forecast_refined.csv'))
    df_policy = pd.read_csv(os.path.join(DATA_DIR, 'policy_scenario_data.csv'))
    
    fig = plt.figure(figsize=(16, 7))
    gs = gridspec.GridSpec(1, 2, figure=fig)
    
    # --- Panel A: National Forecast ---
    ax1 = fig.add_subplot(gs[0, 0])
    
    # Historic (approx from forecast file structure or synthetic for continuity)
    # We'll use the forecast data itself
    ax1.plot(df_forecast['Year'], df_forecast['Ensemble_Projection']/1e6, 'b--', linewidth=2, label='Status Quo (Ensemble)')
    
    # Uncertainty
    ax1.fill_between(df_forecast['Year'], 
                     df_forecast['Scenario_Optimistic']/1e6, 
                     df_forecast['Scenario_Pessimistic']/1e6, 
                     color='blue', alpha=0.25, label='95% Uncertainty')
    
    ax1.set_title('A. National TB Forecast (2025-2030)', fontweight='bold')
    ax1.set_ylabel('Notifications (Millions)')
    ax1.set_xlabel('Year')
    ax1.set_ylim(2.0, 3.5)
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc='upper left')
    
    # --- Panel B: Policy Scenarios ---
    ax2 = fig.add_subplot(gs[0, 1])
    
    colors = {'Baseline': 'black', 'Treatment Optimization': 'blue', 
              'Prevention First': 'orange', 'Combination Strategy': 'red'}
    styles = {'Baseline': '--', 'Treatment Optimization': '-', 
              'Prevention First': '-', 'Combination Strategy': '-'}
    
    for col in df_policy.columns:
        if col != 'Year':
            ax2.plot(df_policy['Year'], df_policy[col]/1e6, 
                     label=col, color=colors.get(col, 'gray'), 
                     linestyle=styles.get(col, '-'), linewidth=2)
             
    ax2.set_title('B. Policy Scenario Analysis', fontweight='bold')
    ax2.set_ylabel('Notifications (Millions)')
    ax2.set_xlabel('Year')
    ax2.set_ylim(1.0, 3.0)
    ax2.grid(True, alpha=0.3)
    ax2.legend(loc='lower left')
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'Figure_1_Combined_Forecast_Scenarios.png'), dpi=300)
    print("Figure 1 Combined Created.")

def generate_figure_3_refined_dynamics():
    print("Generating Figure 3: Refined DR-TB Dynamics...")
    
    # Load Data (State Split)
    df_state = pd.read_csv(os.path.join(DATA_DIR, 'state_drtb_forecasts_split_2030.csv'))
    
    # Aggregations
    years = [2025, 2026, 2027, 2028, 2029, 2030]
    national_new = [df_state[f'DRTB_New_{y}'].sum() for y in years]
    national_ret = [df_state[f'DRTB_Ret_{y}'].sum() for y in years]
    
    # Calculations
    cases_2030_new = national_new[-1]
    cases_2030_ret = national_ret[-1]
    
    detected_risk_based = cases_2030_ret + (0.2 * cases_2030_new)
    missed_cases = cases_2030_new * 0.8
    detected_universal = cases_2030_new + cases_2030_ret
    
    cum_total = sum(national_new) + sum(national_ret)
    bad_outcomes_sq = cum_total * 0.44
    bad_outcomes_bpal = cum_total * 0.10
    lives_saved = bad_outcomes_sq - bad_outcomes_bpal
    
    # Plotting
    fig = plt.figure(figsize=(18, 6))
    gs = gridspec.GridSpec(1, 3, figure=fig)
    
    # --- Panel A: Trend ---
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.stackplot(years, np.array(national_ret)/1000, np.array(national_new)/1000, 
                  labels=['Retreatment', 'New (Primary)'], 
                  colors=['#1f77b4', '#ff7f0e'], alpha=0.8)
    ax1.set_title('A. Projected DR-TB Trend (2025-2030)', fontweight='bold')
    ax1.set_ylabel('Cases (Thousands)')
    ax1.legend(loc='upper left')
    
    # --- Panel B: Diagnostic Gap ---
    ax2 = fig.add_subplot(gs[0, 1])
    bars = ['Risk-Based\nScreening', 'Universal\nDST']
    ax2.bar(bars, [detected_risk_based, detected_universal], color=['gray', 'green'], width=0.5)
    ax2.bar(bars[0], missed_cases, bottom=detected_risk_based, color='red', alpha=0.3, hatch='//')
    
    ax2.set_title('B. DR-TB Diagnostic Gap (2030)', fontweight='bold') # UPDATED TITLE
    ax2.text(0, detected_risk_based + missed_cases/2, f"~{int(missed_cases):,}\nMissed", ha='center', va='center', color='darkred', fontweight='bold')
    
    # --- Panel C: Cost of Inaction ---
    ax3 = fig.add_subplot(gs[0, 2])
    scenarios = ['Status Quo', 'Universal\nBPaL/M']
    vals = [bad_outcomes_sq, bad_outcomes_bpal]
    ax3.bar(scenarios, vals, color=['firebrick', 'teal'], width=0.5)
    
    ax3.set_title('C. Projected Deaths/Failures (2025-2030)', fontweight='bold')
    
    # UPDATED PLACEMENT: Shift text DOWN to avoid title overlap
    # Arrow points to the top of the 2nd bar (BPaL outcome) to show it is lower?
    # Or to the gap. Let's point to the gap between the two levels.
    
    top_bar_1 = vals[0]
    top_bar_2 = vals[1]
    
    # Text at 80% height of first bar, arrow pointing to difference
    ax3.annotate(f'~{int(lives_saved):,} Averted', 
                 xy=(1.0, top_bar_2 + (lives_saved/2)),  # Arrow tip: Middle of the "saved" visible gap above bar 2
                 xytext=(0.5, top_bar_1 * 0.8), # Text: Centered, lower down
                 arrowprops=dict(facecolor='black', shrink=0.05, width=1.5, headwidth=8),
                 ha='center', fontweight='bold', color='darkgreen', fontsize=10)
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'Figure_3_DRTB_Dynamics.png'), dpi=300)
    print("Figure 3 Refined Created.")

if __name__ == "__main__":
    generate_figure_1_combined()
    generate_figure_3_refined_dynamics()
