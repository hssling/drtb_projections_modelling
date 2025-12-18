import pandas as pd
import matplotlib.pyplot as plt
import os

OUTPUT_DIR = r'd:\research-automation\tb_amr_project\manuscript_assets'
os.makedirs(OUTPUT_DIR, exist_ok=True)

def generate_pie_chart():
    # 2030 DR-TB Source Distribution
    sizes = [106082, 52832]
    labels = ['New Cases\n(Primary Resistance)\n67%', 'Retreatment Cases\n(Acquired Resistance)\n33%']
    colors_pie = ['#ff9999','#66b3ff']
    
    plt.figure(figsize=(8, 6))
    patches, texts, autotexts = plt.pie(sizes, labels=labels, autopct='', startangle=90, colors=colors_pie, explode=(0.05, 0), shadow=True)
    
    # Beautify
    for text in texts:
        text.set_fontsize(12)
        text.set_fontweight('bold')
        
    plt.title('Source of Drug-Resistant TB Burden in India (2030 Forecast)', fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'Figure_DRTB_Source_Pie.png'), dpi=300)
    print("Pie Chart Created.")

def generate_tables_markdown():
    # Convert CSVs to Markdown for the DOCX
    
    # Table 1: State Hotspots
    df_hotspots = pd.read_csv(os.path.join(r'd:\research-automation\tb_amr_project\analysis_results', 'Table_2_State_Hotspots.csv'))
    md_table1 = df_hotspots.to_markdown(index=False)
    
    # Table 2: Policy Scenarios
    df_policy = pd.read_csv(os.path.join(r'd:\research-automation\tb_amr_project\analysis_results', 'Table_1_Policy_Scenarios.csv'))
    md_table2 = df_policy.to_markdown(index=False)
    
    return md_table1, md_table2

if __name__ == "__main__":
    generate_pie_chart()
