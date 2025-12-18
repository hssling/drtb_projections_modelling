
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# CONFIG
OUTPUT_DIR = r'd:\research-automation\tb_amr_project\manuscript_assets'
os.makedirs(OUTPUT_DIR, exist_ok=True)
JSON_PATH = r'd:\research-automation\tb_amr_project\authentic_drtb_forecast_india_2025.json'

# Set Style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_context("paper", font_scale=1.5)

def load_authentic_data():
    with open(JSON_PATH, 'r') as f:
        data = json.load(f)
    
    df_hist = pd.DataFrame(data['historical_data'])
    df_fore = pd.DataFrame(data['forecast_scenarios'])
    return df_hist, df_fore

def generate_figure_1_trajectory(df_hist, df_fore):
    """
    Figure 1: Authentic MDR-TB Burden Trajectory (2017-2034)
    """
    plt.figure(figsize=(12, 7))
    
    # Historical Data
    plt.plot(df_hist['year'], df_hist['estimated_true_burden'], 'ko-', label='Estimated True Burden (Historical)', linewidth=2)
    plt.plot(df_hist['year'], df_hist['mdr_rr_detected'], 'bs--', label='Officially Detected Cases', linewidth=1.5, alpha=0.7)
    
    # Forecast Data (Holt-Winters Baseline)
    plt.plot(df_fore['year'], df_fore['forecast_burden'], 'r--', label='Projected Burden (Holt-Winters)', linewidth=2.5)
    
    # Uncertainty / Range (Using Scenarios as bounds)
    plt.fill_between(df_fore['year'], df_fore['Scenario_Optimistic'], df_fore['Scenario_Pessimistic'], 
                     color='red', alpha=0.1, label='Scenario Uncertainty Range')
    
    # Annotate Peak
    # Find peak year
    peak_idx = df_fore['forecast_burden'].idxmax()
    peak_year = df_fore.loc[peak_idx, 'year']
    peak_val = df_fore.loc[peak_idx, 'forecast_burden']
    
    plt.annotate(f'Peak: {int(peak_val):,}', xy=(peak_year, peak_val), xytext=(peak_year, peak_val+5000),
                 arrowprops=dict(facecolor='black', shrink=0.05), ha='center')

    # Forecast Start Line
    plt.axvline(x=2024.5, color='gray', linestyle=':', linewidth=2, label='Forecast Start (2025)')

    plt.title('Authentic MDR-TB Burden Trajectory: Historical & Projected (2017-2034)', fontweight='bold', pad=20)
    plt.xlabel('Year')
    plt.ylabel('MDR-TB Cases (Estimated True Burden)')
    plt.legend(loc='lower left', frameon=True, fancybox=True, framealpha=0.9)
    plt.grid(True, alpha=0.3)
    # Ensure 2025 is visible
    ticks = list(range(2017, 2035, 2))
    if 2025 not in ticks: ticks.append(2025)
    plt.xticks(sorted(ticks))
    
    # Save
    save_path = os.path.join(OUTPUT_DIR, 'Figure_1_MDR_Burden_Authentic.png')
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    print(f"Generated {save_path}")
    plt.close()

def generate_figure_2_scenarios(df_fore):
    """
    Figure 2: Intervention Impact Scenarios
    """
    plt.figure(figsize=(12, 7))
    
    years = df_fore['year']
    
    plt.plot(years, df_fore['Scenario_Pessimistic'], 'r:', linewidth=2, label='Scenario A: Pessimistic (AMR Rise)')
    plt.plot(years, df_fore['Scenario_Status_Quo'], 'k--', linewidth=2.5, label='Scenario B: Status Quo (Baseline)')
    plt.plot(years, df_fore['Scenario_Optimistic'], 'g-.', linewidth=2, label='Scenario C: Optimistic (Elimination)')
    
    # Fill areas to show "Averted Cases"
    plt.fill_between(years, df_fore['Scenario_Status_Quo'], df_fore['Scenario_Optimistic'], color='green', alpha=0.1, label='Averted Burden')
    
    # Forecast Start Line
    plt.axvline(x=2024.5, color='gray', linestyle=':', linewidth=2, label='Forecast Start (2025)')
    
    plt.title('Projected Impact of Intervention Scenarios on MDR-TB Burden (2024-2034)', fontweight='bold', pad=20)
    plt.xlabel('Year')
    plt.ylabel('Projected MDR-TB Cases')
    plt.legend(loc='upper right', frameon=True)
    plt.grid(True, alpha=0.3)
    
    # Ensure 2025 is visible
    ticks = list(range(2025, 2035, 1))
    plt.xticks(ticks)
    
    save_path = os.path.join(OUTPUT_DIR, 'Figure_2_Intervention_Scenarios_Authentic.png')
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    print(f"Generated {save_path}")
    plt.close()

def main():
    print("Generating Authentic Figures from JSON...")
    df_hist, df_fore = load_authentic_data()
    generate_figure_1_trajectory(df_hist, df_fore)
    generate_figure_2_scenarios(df_fore)
    print("Done.")

if __name__ == "__main__":
    main()
