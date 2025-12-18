import pandas as pd
import re
import os

# 1. 2017-2019 Data (Manual)
data_2017_2019 = [
    ("Andaman and Nicobar Islands", 292, 556, 580),
    ("Andhra Pradesh", 83118, 91224, 98486),
    ("Arunachal Pradesh", 3154, 3419, 2944),
    ("Assam", 40174, 42867, 48615),
    ("Bihar", 96489, 104886, 122231),
    ("Chandigarh", 5930, 5704, 6959),
    ("Chhattisgarh", 41272, 43026, 43220),
    ("Dadra and Nagar Haveli and Daman and Diu", 1420, 1348, 1487),
    ("Delhi", 65893, 93488, 122695),
    ("Goa", 1935, 2493, 2341),
    ("Gujarat", 149061, 154622, 171569),
    ("Haryana", 40751, 65642, 75317),
    ("Himachal Pradesh", 16451, 16482, 16867),
    ("Jammu and Kashmir", 10476, 12881, 15264),
    ("Jharkhand", 44128, 48450, 54407),
    ("Karnataka", 81187, 83069, 90538),
    ("Kerala", 22754, 24571, 28160),
    ("Ladakh", None, None, None), # Added for merging
    ("Lakshadweep", 46, 19, 27),
    ("Madhya Pradesh", 134333, 160119, 190472),
    ("Maharashtra", 192458, 209574, 227568),
    ("Manipur", 2805, 2923, 3122),
    ("Meghalaya", 3961, 4867, 5243),
    ("Mizoram", 2245, 2567, 2788),
    ("Nagaland", 3013, 4260, 4752),
    ("Odisha", 51044, 56610, 64797),
    ("Puducherry", 2891, 3060, 3350),
    ("Punjab", 40156, 51040, 58189),
    ("Rajasthan", 107936, 133486, 154696),
    ("Sikkim", 1121, 1358, 1391),
    ("Tamil Nadu", 75389, 78200, 84089),
    ("Telangana", 63725, 73245, 76883),
    ("Tripura", 3605, 3979, 4022),
    ("Uttar Pradesh", 302068, 394982, 482617),
    ("Uttarakhand", 15682, 18260, 19448),
    ("West Bengal", 106950, 120536, 135324)
]
df_17_19 = pd.DataFrame(data_2017_2019, columns=["State", "2017", "2018", "2019"])

# 2. Process 2020-2023 Data (Correcting merge errors in 2023)
# Correct order of states in RS_Session file
rs_states_order = [
    "Andaman and Nicobar Islands", "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar",
    "Chandigarh", "Chhattisgarh", "Dadra and Nagar Haveli and Daman and Diu", "Delhi", "Goa",
    "Gujarat", "Haryana", "Himachal Pradesh", "Jammu and Kashmir", "Jharkhand",
    "Karnataka", "Kerala", "Ladakh", "Lakshadweep", "Madhya Pradesh",
    "Maharashtra", "Manipur", "Meghalaya", "Mizoram", "Nagaland",
    "Odisha", "Puducherry", "Punjab", "Rajasthan", "Sikkim",
    "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand",
    "West Bengal"
]

with open(r'd:\research-automation\tb_amr_project\data\raw\RS_Session_260_AU_618_A_to_B_i.csv', 'r') as f:
    content = f.read()

# content cleanup
content = content.replace("Sl. No.,State/UT,2020,2021,2022,20231,Andaman", "Sl. No.,State/UT,2020,2021,2022,2023\n1,Andaman")

data_20_23 = []
for i, state in enumerate(rs_states_order):
    current_idx = i + 1
    # Regex find
    if "Dadra" in state:
        pat_str = r"(Dadra[^,]+),(\d+),(\d+),(\d+),(\d+)"
    else:
        pat_str = re.escape(state) + r",(\d+),(\d+),(\d+),(\d+)"
    
    match = re.search(pat_str, content)
    if match:
        st_name = match.group(1) if "Dadra" in state else state
        v2020 = match.group(1) if "Dadra" not in state else match.group(2)
        v2021 = match.group(2) if "Dadra" not in state else match.group(3)
        v2022 = match.group(3) if "Dadra" not in state else match.group(4)
        raw_v2023 = match.group(4) if "Dadra" not in state else match.group(5)
        
        # Correction logic
        # Next index logic
        # If this is not the last state (West Bengal), strip the suffix
        if state != "West Bengal":
            next_idx = current_idx + 1
            suffix_len = len(str(next_idx))
            if len(raw_v2023) > suffix_len:
                v2023 = raw_v2023[:-suffix_len]
            else:
                v2023 = raw_v2023
        else:
            v2023 = raw_v2023
            
        data_20_23.append([state, v2020, v2021, v2022, v2023])

df_20_23 = pd.DataFrame(data_20_23, columns=["State", "2020", "2021", "2022", "2023"])

# 3. Process 2025 Data
data_2025 = []
with open(r'd:\research-automation\tb_amr_project\SOURCES DATA\Total Notified TB 2025 statewise.txt', 'r') as f:
    lines = f.readlines()
    for line in lines:
        line = line.strip()
        if not line or "State" in line or "Grand Total" in line:
            continue
        parts = re.split(r'\t+', line)
        if len(parts) >= 2:
            state = parts[0].strip()
            val = parts[-1].strip()
            
            # Normalization
            if state == "CHANDIGARH": state = "Chandigarh"
            if "Andaman" in state: state = "Andaman and Nicobar Islands"
            if "Dadra" in state: state = "Dadra and Nagar Haveli and Daman and Diu"
            if "Jammu" in state: state = "Jammu and Kashmir" # Fix & -> and
            
            data_2025.append([state, val])

df_2025 = pd.DataFrame(data_2025, columns=["State", "2025"])

# 4. Merge
df_merged = pd.merge(df_17_19, df_20_23, on="State", how="outer")
df_merged = pd.merge(df_merged, df_2025, on="State", how="outer")

# 5. Numeric conversion
for c in df_merged.columns:
    if c != "State":
        df_merged[c] = pd.to_numeric(df_merged[c], errors='coerce')

# 6. Save
output_path = r'd:\research-automation\tb_amr_project\data\processed\tb_notifications_state_17_25_merged.csv'
df_merged.to_csv(output_path, index=False)
print(f"Refined file saved: {output_path}")
print(df_merged.head(10))
