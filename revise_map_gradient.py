import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import geopandas as gpd
import os
import mapclassify

# --- CONFIG ---
DATA_DIR = r'd:\research-automation\tb_amr_project\data\processed'
RES_DIR = r'd:\research-automation\tb_amr_project\analysis_results'
SHP_PATH = r'd:\research-automation\tb_amr_project\plots\shapefiles\ne_10m_admin_1_states_provinces.shp'
OUTPUT_DIR = r'd:\research-automation\tb_amr_project\manuscript_assets'
os.makedirs(OUTPUT_DIR, exist_ok=True)

def regenerate_maps_with_gradient():
    print("Regenerating Maps with enhanced gradient...")
    
    # Load Forecast
    df_state = pd.read_csv(os.path.join(RES_DIR, 'state_drtb_forecasts_split_2030.csv'))
    
    # Calculate Rate
    df_state['DRTB_Rate_2030'] = (df_state['DRTB_Total_2030'] / df_state['Total_2030']) * 100
    
    # Load Shapefile
    india_map = gpd.read_file(SHP_PATH)
    india_map = india_map[india_map['admin'] == 'India']
    
    # Normalize
    india_map['state_norm'] = india_map['name'].str.lower().str.replace(' ', '').replace('orissa', 'odisha')
    df_state['state_norm'] = df_state['State'].str.lower().str.replace(' ', '')
    
    merged = india_map.merge(df_state, on='state_norm', how='left')
    
    # Replace NaN with 0 for plotting
    merged['DRTB_Total_2030'] = merged['DRTB_Total_2030'].fillna(0)
    merged['DRTB_Rate_2030'] = merged['DRTB_Rate_2030'].fillna(0)
    
    # Plot
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(24, 10))
    
    # Map 1: Absolute Volume
    # Use 'NaturalBreaks' or just linear Reds
    merged.plot(column='DRTB_Total_2030', ax=ax1, legend=True, cmap='Reds', 
                legend_kwds={'label': "Projected DR-TB Cases (2030)"})
    ax1.set_title('A. Volume: Total Projected DR-TB Cases (2030)', fontweight='bold', fontsize=14)
    ax1.axis('off')
    
    # Map 2: Intensity (The one that was "all red")
    # Now that we have heterogeneity, we use a spectral scale
    # We use 'quantiles' (e.g., k=7) to force differentiation
    # Or just a good cmap. 'RdYlBu_r' means Red=High, Blue=Low.
    # We will set a custom vmin/vmax range to emphasize high values.
    # Range is likely 2.5% to 8%.
    
    merged.plot(column='DRTB_Rate_2030', ax=ax2, legend=True, cmap='RdYlBu_r', 
                scheme='Quantiles', k=6,  # Use Quantiles to force distinct buckets
                legend_kwds={'loc': 'lower right', 'fmt': '{:.1f}%'})
    
    ax2.set_title('B. Intensity: Projected DR-TB Percentage (2030)', fontweight='bold', fontsize=14)
    ax2.axis('off')
    
    plt.suptitle('Geographic Distribution of Projected DR-TB Burden in India (2030)', fontsize=18)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'Figure_2_Chloropleth_Revised.png'), dpi=300)
    print("Map Revised.")

if __name__ == "__main__":
    regenerate_maps_with_gradient()
