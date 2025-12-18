import pandas as pd
import os
import re

def clean_state_name(state):
    """Normalize state names to match the standard dataset."""
    if pd.isna(state):
        return state
    state = state.strip()
    return state.replace('&', 'and').replace('Telangana', 'Telengana') # Example normalization

def process_age_distribution():
    print("Processing Age Distribution Data...")
    
    # Files
    cases_file = r'd:\research-automation\tb_amr_project\SOURCES DATA\RS_Session_266_AU_1736_A_to_C_3 (1).csv'
    deaths_file = r'd:\research-automation\tb_amr_project\SOURCES DATA\RS_Session_266_AU_1736_A_to_C_4.csv'
    
    # 1. Process Cases Distribution
    df_cases = pd.read_csv(cases_file)
    # Rename columns to shorter, meaningful names
    df_cases.columns = [
        'sl_no', 'state', 
        'cases_2023_0_14_pct', 'cases_2023_15_30_pct', 'cases_2023_31_45_pct', 'cases_2023_46_60_pct', 'cases_2023_60plus_pct',
        'cases_2024_0_14_pct', 'cases_2024_15_30_pct', 'cases_2024_31_45_pct', 'cases_2024_46_60_pct', 'cases_2024_60plus_pct'
    ]
    df_cases = df_cases.drop(columns=['sl_no'])
    df_cases['state'] = df_cases['state'].apply(clean_state_name)
    
    # 2. Process Deaths Distribution
    df_deaths = pd.read_csv(deaths_file)
    # The deaths file has similar structure
    df_deaths.columns = [
        'sl_no', 'state', 
        'deaths_2023_0_14_pct', 'deaths_2023_15_30_pct', 'deaths_2023_31_45_pct', 'deaths_2023_46_60_pct', 'deaths_2023_60plus_pct',
        'deaths_2024_0_14_pct', 'deaths_2024_15_30_pct', 'deaths_2024_31_45_pct', 'deaths_2024_46_60_pct', 'deaths_2024_60plus_pct'
    ]
    df_deaths = df_deaths.drop(columns=['sl_no'])
    df_deaths['state'] = df_deaths['state'].apply(clean_state_name)
    
    # Merge
    df_age_dist = pd.merge(df_cases, df_deaths, on='state', how='outer')
    
    output_path = r'd:\research-automation\tb_amr_project\data\processed\tb_age_distribution_state_23_24.csv'
    df_age_dist.to_csv(output_path, index=False)
    print(f"Saved Age Distribution Data to {output_path}")

def process_recent_notifications():
    print("Processing 2023-2024 Notifications and Outcomes...")
    
    # Main source for 2023 complete & 2024 provisional
    file_path = r'd:\research-automation\tb_amr_project\SOURCES DATA\RS_Session_267_AU_3467_1.csv'
    
    df = pd.read_csv(file_path)
    df.columns = ['sl_no', 'state', 'cases_notified_2023', 'treated_succ_2023', 'cases_notified_2024']
    
    # Calculate Success Rate
    df['success_rate_2023_pct'] = (df['treated_succ_2023'] / df['cases_notified_2023'] * 100).round(2)
    
    df = df.drop(columns=['sl_no'])
    df['state'] = df['state'].apply(clean_state_name)
    
    output_path = r'd:\research-automation\tb_amr_project\data\processed\tb_notifications_outcomes_state_23_24.csv'
    df.to_csv(output_path, index=False)
    print(f"Saved Recent Notifications Data to {output_path}")

if __name__ == "__main__":
    os.makedirs(r'd:\research-automation\tb_amr_project\data\processed', exist_ok=True)
    process_age_distribution()
    process_recent_notifications()
