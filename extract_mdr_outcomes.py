import pandas as pd

# Load the WHO TB outcomes data
source_path = r'd:\research-automation\tb_amr_project\SOURCES DATA\TB_outcomes_2025-11-23.csv'
df = pd.read_csv(source_path)

# Filter for India
df_india = df[df['country'] == 'India']

# Select relevant columns for MDR and XDR outcomes
cols = ['year', 
        'mdr_coh', 'mdr_succ', 'mdr_fail', 'mdr_died', 'mdr_lost',
        'xdr_coh', 'xdr_succ', 'xdr_fail', 'xdr_died', 'xdr_lost']

# Check if columns exist before selecting
available_cols = [c for c in cols if c in df.columns]
df_india_clean = df_india[available_cols]

# Save to processed folder
output_path = r'd:\research-automation\tb_amr_project\data\processed\mdr_tb_india_outcomes.csv'
df_india_clean.to_csv(output_path, index=False)

print(f"Saved India MDR TB outcomes data to {output_path}")
print(df_india_clean)
