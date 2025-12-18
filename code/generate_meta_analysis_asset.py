import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

# --- CONFIG ---
OUTPUT_DIR = r'd:\research-automation\tb_amr_project\manuscript_assets'
os.makedirs(OUTPUT_DIR, exist_ok=True)

def generate_meta_analysis_comparison():
    print("Generating Meta-Analysis Comparison...")
    
    # 1. Synthesize Meta-Analysis Data (from Search)
    # Source: Step 653 Search Results
    studies = [
        {'Author': 'Goyal et al.', 'Year': 2020, 'Data_Period': '2006-2018', 'Prevalence_New': 3.5, 'Prevalence_Ret': 26.7, 'Type': 'Systematic Review', 'Category': 'Historical Baseline'},
        {'Author': 'Kumar et al.', 'Year': 2023, 'Data_Period': '2016-2022', 'Prevalence_New': 3.9, 'Prevalence_Ret': 13.4, 'Type': 'Mini Meta-Analysis', 'Category': 'Recent Trends'},
        {'Author': 'WHO Global Report', 'Year': 2024, 'Data_Period': '2023', 'Prevalence_New': 3.2, 'Prevalence_Ret': 16.0, 'Type': 'Surveillance Report', 'Category': 'Current Status'},
        {'Author': 'Our Study (Forecast)', 'Year': 2030, 'Data_Period': 'Forecast', 'Prevalence_New': 4.2, 'Prevalence_Ret': 14.0, 'Type': 'Modeling Projection', 'Category': 'Future Warning'}
    ]
    
    df_meta = pd.DataFrame(studies)
    
    # 2. Visualization
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Plot New Case Prevalence
    sns.scatterplot(data=df_meta, x='Year', y='Prevalence_New', hue='Category', style='Category', s=200, ax=ax, palette='deep')
    
    # Annotate points
    for i, row in df_meta.iterrows():
        ax.text(row['Year']+0.2, row['Prevalence_New'], f"{row['Author']}\n({row['Prevalence_New']}%)", fontsize=10)
        
    ax.set_title('Meta-Analysis Context: DR-TB Prevalence in New Cases', fontweight='bold')
    ax.set_ylabel('Prevalence of Resistance (%)')
    ax.set_xlabel('Publication/Projection Year')
    ax.set_ylim(2, 6)
    ax.grid(True, linestyle='--', alpha=0.5)
    
    # Add Trend Line (Visual Guide)
    x_vals = df_meta['Year'].values
    y_vals = df_meta['Prevalence_New'].values
    # Simple polyfit to show direction
    z = np.polyfit(x_vals, y_vals, 1)
    p = np.poly1d(z)
    ax.plot(x_vals, p(x_vals), "r--", alpha=0.3, label='Overall Trend')
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'Figure_4_Meta_Analysis_Comparison.png'), dpi=300)
    print("Meta-Analysis Figure Created.")
    
    # Save Data for Manuscript Table
    df_meta.to_csv(os.path.join(OUTPUT_DIR, 'meta_analysis_summary.csv'), index=False)

if __name__ == "__main__":
    generate_meta_analysis_comparison()
