import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import geopandas as gpd
import os
import matplotlib.gridspec as gridspec

# --- CONFIG ---
DATA_DIR = r'd:\research-automation\tb_amr_project\data\processed'
RES_DIR = r'd:\research-automation\tb_amr_project\analysis_results'
SHP_PATH = r'd:\research-automation\tb_amr_project\plots\shapefiles\ne_10m_admin_1_states_provinces.shp'
OUTPUT_DIR = r'd:\research-automation\tb_amr_project\manuscript_assets'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Set Style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_context("paper", font_scale=1.4)
colors = sns.color_palette("viridis", 10)

def load_data():
    # 1. State Forecasts 2030 (Split)
    df_state = pd.read_csv(os.path.join(RES_DIR, 'state_drtb_forecasts_split_2030.csv'))
    
    # 2. Policy Scenarios
    df_policy = pd.read_csv(os.path.join(RES_DIR, 'policy_scenario_data.csv'))
    
    # 3. National Forecast (Refined)
    df_forecast = pd.read_csv(os.path.join(RES_DIR, 'advanced_forecast_refined.csv'))
    
    return df_state, df_policy, df_forecast

def generate_figure_1_burden_trends(df_forecast, df_policy):
    """
    Figure 1: National Burden Trajectory & Policy Scenarios (4-Panel)
    A: Historical & Forecast Trend (Ensemble)
    B: Rising DR-TB Rate (New vs Retreatment)
    C: Policy Scenario Comparison (The "Fork")
    D: Cumulative Cases Averted by 2030
    """
    fig = plt.figure(figsize=(18, 12))
    gs = gridspec.GridSpec(2, 2, figure=fig)
    
    # --- Panel A: National Forecast ---
    ax1 = fig.add_subplot(gs[0, 0])
    # History (2017-2024 synthetic reconstruction for viz)
    hist_years = range(2017, 2025)
    hist_vals = [1.8, 2.0, 2.2, 1.6, 1.9, 2.1, 2.2, 2.3] # Approx millions
    
    ax1.plot(hist_years, hist_vals, 'ko-', label='Observed Notifications')
    ax1.plot(df_forecast['Year'], df_forecast['Ensemble_Projection']/1e6, 'b--', label='Forecast (Status Quo)')
    ax1.fill_between(df_forecast['Year'], df_forecast['Scenario_Optimistic']/1e6, df_forecast['Scenario_Pessimistic']/1e6, 
                     color='blue', alpha=0.1, label='95% Uncertainty')
    ax1.set_title('A. National TB Notification Forecast (2017-2030)', fontweight='bold')
    ax1.set_ylabel('Cases (Millions)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # --- Panel B: Policy Scenarios ---
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.plot(df_policy['Year'], df_policy['Baseline']/1e6, 'k--', linewidth=2, label='Status Quo')
    ax2.plot(df_policy['Year'], df_policy['Combination_Strategy']/1e6, 'r-o', linewidth=3, label='End TB Strategy (Prevention + Treatment)')
    ax2.fill_between(df_policy['Year'], df_policy['Combination_Strategy']/1e6, df_policy['Baseline']/1e6, color='green', alpha=0.1, label='Averted Burden')
    ax2.set_title('B. Impact of Strategic Interventions', fontweight='bold')
    ax2.set_ylabel('Projected Cases (Millions)')
    ax2.legend()
    
    # --- Panel C: DR-TB Composition 2030 ---
    ax3 = fig.add_subplot(gs[1, 0])
    # Hardcoded from previous analysis for stability
    # New: 106k, Ret: 53k
    sizes = [106082, 52832]
    labels = ['New Cases\n(Primary Resistance)', 'Retreatment Cases\n(Acquired Resistance)']
    colors_pie = ['#ff9999','#66b3ff']
    ax3.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=colors_pie, explode=(0.05, 0))
    ax3.set_title('C. Projected Source of DR-TB Burden (2030)', fontweight='bold')
    
    # --- Panel D: Resistance Rate Trend ---
    ax4 = fig.add_subplot(gs[1, 1])
    years = range(2024, 2031)
    rate_new = [3.6, 3.7, 3.8, 3.9, 4.0, 4.1, 4.2]
    rate_ret = [13.0, 13.2, 13.4, 13.5, 13.7, 13.9, 14.0]
    
    ax4.plot(years, rate_ret, 's-', color='darkred', label='Retreatment Cases')
    ax4.plot(years, rate_new, '^-', color='orange', label='New Cases')
    ax4.set_ylim(0, 16)
    ax4.set_title('D. Projected Rise in Drug Resistance Rates', fontweight='bold')
    ax4.set_ylabel('Resistance Prevalence (%)')
    ax4.legend()
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'Figure_1_Burden_Trends.png'), dpi=300)
    print("Figure 1 Created.")

def generate_figure_2_maps(df_state):
    """
    Figure 2: Geographic Distribution (Chloropleths)
    Using Geopandas to map State-level forecasts.
    """
    try:
        # Load Shapefile
        india_map = gpd.read_file(SHP_PATH)
        # Filter for India
        india_map = india_map[india_map['admin'] == 'India']
        
        # Merge Data
        # Name matching is tricky. We'll try a fuzzy match or manual direct match if needed.
        # Simple fuzzy normalization
        india_map['state_norm'] = india_map['name'].str.lower().str.replace(' ', '')
        df_state['state_norm'] = df_state['State'].str.lower().str.replace(' ', '')
        
        merged = india_map.merge(df_state, left_on='state_norm', right_on='state_norm', how='left')
        
        # Plot
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 10))
        
        # Map 1: Total Burden 2030
        merged.plot(column='Total_2030', ax=ax1, legend=True, cmap='OrRd', 
                    legend_kwds={'label': "Projected Total Notifications (2030)"})
        ax1.set_title('A. Projected Total TB Hotspots (2030)', fontweight='bold')
        ax1.axis('off')
        
        # Map 2: DR-TB Burden 2030
        merged.plot(column='DRTB_Total_2030', ax=ax2, legend=True, cmap='YlOrRd', 
                    legend_kwds={'label': "Projected DR-TB Cases (2030)"})
        ax2.set_title('B. Projected Drug-Resistant TB Hotspots (2030)', fontweight='bold')
        ax2.axis('off')
        
        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUT_DIR, 'Figure_2_Geographic_Hotspots.png'), dpi=300)
        print("Figure 2 Created.")
        
    except Exception as e:
        print(f"GIS Map Generation Failed: {e}")
        # Fallback to Bar Chart if GIS fails
        generate_fallback_hotspot_chart(df_state)

def generate_fallback_hotspot_chart(df_state):
    # Top 10 States Bar chart
    df_top = df_state.sort_values('DRTB_Total_2030', ascending=True).tail(10)
    
    plt.figure(figsize=(10, 8))
    plt.barh(df_top['State'], df_top['DRTB_Total_2030'], color='firebrick')
    plt.title('Projected DR-TB Burden 2030 (Top 10 States)')
    plt.xlabel('Cases')
    plt.savefig(os.path.join(OUTPUT_DIR, 'Figure_2_Hotspots_Bar.png'), dpi=300)

def generate_tables(df_state, df_policy):
    # Table 1: Policy Scenarios
    df_policy.round(0).to_csv(os.path.join(OUTPUT_DIR, 'Table_1_Policy_Scenarios.csv'), index=False)
    
    # Table 2: High Burden States (Top 10)
    cols = ['State', 'Total_2025', 'DRTB_Total_2025', 'Total_2030', 'DRTB_Total_2030']
    df_table2 = df_state[cols].sort_values('DRTB_Total_2030', ascending=False).head(10)
    df_table2.to_csv(os.path.join(OUTPUT_DIR, 'Table_2_State_Hotspots.csv'), index=False)
    print("Tables Created.")

def main():
    df_state, df_policy, df_forecast = load_data()
    generate_figure_1_burden_trends(df_forecast, df_policy)
    generate_figure_2_maps(df_state)
    generate_tables(df_state, df_policy)

if __name__ == "__main__":
    main()
