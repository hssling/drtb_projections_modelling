
import pandas as pd
df = pd.read_csv('d:/research-automation/tb_amr_project/data/synthetic_state_tb_data_demo.csv')
for state in sorted(df['state_name'].unique()):
    print(state)
