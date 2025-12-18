import pandas as pd
import os

def merge_notifications_history():
    print("Merging Notification History (2017-2024)...")
    
    # 1. Load History (which has cols: State, 2017, ..., 2025)
    hist_path = r'd:\research-automation\tb_amr_project\data\processed\tb_notifications_state_17_25_merged.csv'
    df_hist = pd.read_csv(hist_path)
    
    # 2. Load New Verified Data (2023, 2024)
    new_path = r'd:\research-automation\tb_amr_project\data\processed\tb_notifications_outcomes_state_23_24.csv'
    df_new = pd.read_csv(new_path)
    
    # 3. Clean Names
    def clean_name(name):
        if pd.isna(name): return name
        return name.strip().replace('&', 'and').replace('Telengana', 'Telangana')
    
    df_hist['State'] = df_hist['State'].apply(clean_name)
    df_new['state'] = df_new['state'].apply(clean_name)
    
    # 4. Update df_hist with verifies values
    # Create a mapping from state -> 2023_val, 2024_val
    map_2023 = df_new.set_index('state')['cases_notified_2023'].to_dict()
    map_2024 = df_new.set_index('state')['cases_notified_2024'].to_dict()
    
    # Update the columns in df_hist
    # Note: df_hist already has '2023' and '2025' columns (2025 likely provisional/partial from previous step)
    # We will OVERWRITE '2023' with the verified verified numbers, and ADD/UPDATE '2024'
    
    df_hist['2023'] = df_hist['State'].map(map_2023).fillna(df_hist['2023']) # Prefer verified, fallback to existing
    df_hist['2024'] = df_hist['State'].map(map_2024)
    
    # Reorder columns to be chronological
    cols = ['State', '2017', '2018', '2019', '2020', '2021', '2022', '2023', '2024']
    # We drop 2025 for now if it's just a fragment, or keep it if we want.
    # The previous file had a '2025' column but it seemed to hold '2025 provisional' or similar. 
    # Let's keep it but rename it to '2025_prov' to avoid confusion if we want.
    # Actually, let's stick to the reliable 17-24 for the main analysis file.
    
    df_final = df_hist[cols]
    
    output_path = r'd:\research-automation\tb_amr_project\data\processed\tb_notifications_comprehensive_17_24.csv'
    df_final.to_csv(output_path, index=False)
    print(f"Saved Comprehensive Data to {output_path}")

def synthesize_dr_tb_analysis():
    print("Synthesizing DR-TB Analysis Datasets...")
    burden_path = r'd:\research-automation\tb_amr_project\data\processed\mdr_tb_india_burden.csv'
    outcomes_path = r'd:\research-automation\tb_amr_project\data\processed\mdr_tb_india_outcomes.csv'
    
    if os.path.exists(burden_path) and os.path.exists(outcomes_path):
        df_burden = pd.read_csv(burden_path)
        df_outcomes = pd.read_csv(outcomes_path)
        df_national_dr = pd.merge(df_burden, df_outcomes, on='year', how='outer')
        nat_output = r'd:\research-automation\tb_amr_project\data\processed\master_dr_tb_national_india.csv'
        df_national_dr.to_csv(nat_output, index=False)
        print(f"Saved National DR-TB Master to {nat_output}")
    else:
        print("Skipping DR-TB synthesis: Input files not found.")

if __name__ == "__main__":
    merge_notifications_history()
    synthesize_dr_tb_analysis()
