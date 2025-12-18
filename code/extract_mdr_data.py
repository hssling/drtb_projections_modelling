import pandas as pd

# Load the WHO MDR TB burden data
source_path = r'd:\research-automation\tb_amr_project\SOURCES DATA\MDR_RR_TB_burden_estimates_2025-11-23.csv'
df = pd.read_csv(source_path)

# Filter for India
df_india = df[df['country'] == 'India']

# Select relevant columns for clarity
cols = ['year', 'e_rr_pct_new', 'e_rr_pct_new_lo', 'e_rr_pct_new_hi', 
        'e_rr_pct_ret', 'e_rr_pct_ret_lo', 'e_rr_pct_ret_hi', 
        'e_inc_rr_num', 'e_inc_rr_num_lo', 'e_inc_rr_num_hi']

df_india_clean = df_india[cols]

# Save to processed folder
output_path = r'd:\research-automation\tb_amr_project\data\processed\mdr_tb_india_burden.csv'
df_india_clean.to_csv(output_path, index=False)

print(f"Saved India MDR TB data to {output_path}")
print(df_india_clean)
