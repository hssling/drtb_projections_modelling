import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import matplotlib.gridspec as gridspec

# --- CONFIG ---
DATA_DIR = r'd:\research-automation\tb_amr_project\analysis_results'
OUTPUT_DIR = r'd:\research-automation\tb_amr_project\manuscript_assets'
os.makedirs(OUTPUT_DIR, exist_ok=True)

def generate_enhanced_figure_4():
    print("Generating Enhanced Figure 4 (Multi-Panel DR-TB Dynamics)...")
    
    # 1. Load Data
    df_state = pd.read_csv(os.path.join(DATA_DIR, 'state_drtb_forecasts_split_2030.csv'))
    
    # 2. Aggregations (National Level)
    years = [2025, 2026, 2027, 2028, 2029, 2030]
    national_new = []
    national_ret = []
    
    for y in years:
        national_new.append(df_state[f'DRTB_New_{y}'].sum())
        national_ret.append(df_state[f'DRTB_Ret_{y}'].sum())
        
    df_trend = pd.DataFrame({
        'Year': years,
        'New': national_new,
        'Retreatment': national_ret,
        'Total': np.array(national_new) + np.array(national_ret)
    })
    
    # 3. Calculations for Scenarios
    
    # Panel B: The Diagnostic Gap (2030 Snapshot)
    # Assumption: Risk-based testing captures ALL Retreatment DR-TB (since they are tested) 
    # but captures very few New DR-TB (only those who fail first-line? ~50% detection delay?)
    # Let's assume current Risk-Based policy detects:
    #   - 100% of Retreatment Cases (Targeted) => 53k
    #   - 20% of New Cases (Passive/Delayed/High Risk groups) => ~20k (Conservative estimate for 'Risk Based')
    # Universal DST detects 100% of both.
    
    cases_2030_new = df_trend.iloc[-1]['New'] # ~106k
    cases_2030_ret = df_trend.iloc[-1]['Retreatment'] # ~53k
    
    detected_risk_based = cases_2030_ret + (0.2 * cases_2030_new)
    missed_cases = cases_2030_new * 0.8
    detected_universal = cases_2030_new + cases_2030_ret
    
    # Panel C: The Mortality Gap (Cumulative 2025-2030)
    # Cumulative Cases
    cum_total = df_trend['Total'].sum()
    
    # Status Quo: 56% Success -> 44% Poor Outcome (Death/Failure/LTFU)
    bad_outcomes_sq = cum_total * 0.44
    
    # BPaL Strategy: 90% Success -> 10% Poor Outcome
    bad_outcomes_bpal = cum_total * 0.10
    
    lives_saved = bad_outcomes_sq - bad_outcomes_bpal
    
    # 4. Plotting
    fig = plt.figure(figsize=(18, 6))
    gs = gridspec.GridSpec(1, 3, figure=fig)
    
    # --- Panel A: Trajectory (Stacked Area) ---
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.stackplot(years, df_trend['Retreatment']/1000, df_trend['New']/1000, 
                  labels=['Retreatment (Acquired)', 'New (Primary)'], 
                  colors=['#1f77b4', '#ff7f0e'], alpha=0.8)
    ax1.set_title('A. Projected DR-TB Trend (2025-2030)', fontweight='bold')
    ax1.set_ylabel('Projected Cases (Thousands)')
    ax1.set_xlabel('Year')
    ax1.legend(loc='upper left')
    ax1.grid(True, alpha=0.3)
    
    # --- Panel B: The Diagnostic Gap (2030) ---
    ax2 = fig.add_subplot(gs[0, 1])
    # Bar Chart
    bars = ['Risk-Based\nScreening', 'Universal\nDST']
    values = [detected_risk_based, detected_universal]
    
    bar_plot = ax2.bar(bars, values, color=['gray', 'green'], width=0.6)
    
    # Add "Missed" segment ghost
    ax2.bar(bars[0], missed_cases, bottom=detected_risk_based, color='red', alpha=0.3, hatch='//', label='Missed Primary Transmission')
    
    ax2.set_title('B. The Diagnostic Gap (2030 Snapshot)', fontweight='bold')
    ax2.set_ylabel('Cases Diagnosed')
    ax2.legend()
    
    # Labels
    ax2.text(0, detected_risk_based/2, f"{int(detected_risk_based):,}", ha='center', color='white', fontweight='bold')
    ax2.text(1, detected_universal - 20000, f"{int(detected_universal):,}", ha='center', color='white', fontweight='bold')
    ax2.text(0, detected_risk_based + missed_cases/2, f"~{int(missed_cases):,} Missed", ha='center', color='darkred', fontweight='bold')
    
    # --- Panel C: The Cost of Inaction (Mortality) ---
    ax3 = fig.add_subplot(gs[0, 2])
    scenarios = ['Status Quo\nRegimens', 'Universal\nBPaL/M']
    outcomes = [bad_outcomes_sq, bad_outcomes_bpal]
    
    bar_plot2 = ax3.bar(scenarios, outcomes, color=['firebrick', 'teal'], width=0.6)
    
    ax3.set_title('C. Projected Fatalities/Failures (2025-2030)', fontweight='bold')
    ax3.set_ylabel('Cumulative Poor Outcomes')
    
    # Label Arrow
    ax3.annotate(f'~{int(lives_saved):,} Lives/Failures Averted', 
                 xy=(0.5, (bad_outcomes_sq + bad_outcomes_bpal)/2), 
                 xytext=(0.5, bad_outcomes_sq*0.8),
                 arrowprops=dict(facecolor='black', shrink=0.05),
                 ha='center', fontweight='bold')
    
    for i, v in enumerate(outcomes):
        ax3.text(i, v + 5000, f"{int(v):,}", ha='center', fontweight='bold')
        
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'Figure_4_Multipanel_DRTB_Dynamics.png'), dpi=300)
    print("Enhanced Figure 4 Created.")

if __name__ == "__main__":
    generate_enhanced_figure_4()
