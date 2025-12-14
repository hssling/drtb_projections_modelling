import pandas as pd # turbo
import os

def merge_notifications_history():
    print("Merging Notification History (2017-2024)...")
    
    # 1. Load Historical Data (2017-2025 merged file)
    # Note: We previously merged up to 2025 in 'tb_notifications_state_17_25_merged.csv'
    # but let's ensure we prioritize the high-quality 2023-2024 verified data we just processed.
    hist_path = r'd:\research-automation\tb_amr_project\data\processed\tb_notifications_state_17_25_merged.csv'
    new_path = r'd:\research-automation\tb_amr_project\data\processed\tb_notifications_outcomes_state_23_24.csv'
    
    df_hist = pd.read_csv(hist_path)
    df_new = pd.read_csv(new_path)
    
    # Clean state names again to ensure matching
    def clean_name(name):
        return name.strip().replace('&', 'and').replace('Telengana', 'Telangana')
    
    df_hist['state'] = df_hist['state'].apply(clean_name)
    df_new['state'] = df_new['state'].apply(clean_name)
    
    # Update/Override 2023 and 2024 columns in history with verified new data
    # We will create a clean 'master' dataframe
    
    # Select cols from history (excluding 2023, 2024 duplicates if any)
    # The history file columns were: state, 2017_notified, ..., 2025_notified
    # Let's inspect columns first via logic but for this script we assume standard format or re-merge.
    
    # Actually, simpler approach: Update the specific year columns in df_hist using df_new
    
    # Create dictionary mapping for new data
    map_2023 = df_new.set_index('state')['cases_notified_2023'].to_dict()
    map_2024 = df_new.set_index('state')['cases_notified_2024'].to_dict()
    
    # Update or Create columns
    df_hist['2023_verified'] = df_hist['state'].map(map_2023)
    df_hist['2024_verified'] = df_hist['state'].map(map_2024)
    
    # For now, let's stick to a clean comprehensive file
    output_path = r'd:\research-automation\tb_amr_project\data\processed\tb_notifications_comprehensive_17_24.csv'
    df_hist.to_csv(output_path, index=False)
    print(f"Saved Comprehensive Data to {output_path}")

def synthesize_dr_tb_analysis():
    """
    Creates a master dataset specifically for the DR-TB Analysis objective.
    Combines:
    1. Burden Estimates (National)
    2. Notification Trends (State)
    3. Treatment Outcomes (National/State where available)
    """
    print("Synthesizing DR-TB Analysis Datasets...")
    
    # Load separate components
    burden_path = r'd:\research-automation\tb_amr_project\data\processed\mdr_tb_india_burden.csv'
    outcomes_path = r'd:\research-automation\tb_amr_project\data\processed\mdr_tb_india_outcomes.csv'
    
    df_burden = pd.read_csv(burden_path)
    df_outcomes = pd.read_csv(outcomes_path)
    
    # Merge National Level Data on Year
    df_national_dr = pd.merge(df_burden, df_outcomes, on='year', how='outer')
    
    # Save National DR-TB Master File
    nat_output = r'd:\research-automation\tb_amr_project\data\processed\master_dr_tb_national_india.csv'
    df_national_dr.to_csv(nat_output, index=False)
    print(f"Saved National DR-TB Master to {nat_output}")

if __name__ == "__main__":
    merge_notifications_history()
    synthesize_dr_tb_analysis()
