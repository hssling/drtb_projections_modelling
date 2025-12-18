# Data Processing Log

## Objective
Integrate TB notification data from various sources to create a comprehensive state-wise dataset for India (2017-2025).

## Sources
1. **2017-2019**: Data manually extracted from government reports (PIB, Data.gov.in) via web search.
   - Files: None (Direct extraction).
2. **2020-2023**: Data extracted from `data/raw/RS_Session_260_AU_618_A_to_B_i.csv`.
   - **Note**: The 2023 column in this source appeared to be partial (approx. 50% of expected annual values) or provisional. Values were corrected by stripping the suffix merged from the next row's index.
3. **2025**: Data extracted from `SOURCES DATA/Total Notified TB 2025 statewise.txt`.
   - This dataset includes "Grand Total" of 2,384,502 notifications, suggesting it represents a full year (possibly 2024 labeled as 2025 report, or provisional 2025).

## Processing Steps
1. **Normalization**: State names were normalized to a standard format (e.g., "A&N Islands" -> "Andaman and Nicobar Islands").
2. **Correction**: 
   - `RS_Session_260...` file had a parsing issue where the 2023 value was concatenated with the next row's index. This was programmatically corrected.
   - `Dadra and Nagar Haveli and Daman and Diu` was summed in 2017-2018 to match the merged status in later years.
3. **Merging**: All datasets were merged on `State` name.

## Output
- **File**: `data/processed/tb_notifications_state_17_25_merged.csv`
- **Columns**: State, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2025.

## Notes for Analysis
- **2023 Data**: Be cautious with 2023 column as it shows significantly lower numbers than 2022/2025, indicating it is likely partial year data.
- **2024 Data**: Missing at state level in the processed file (2025 column likely serves as the latest reference).
