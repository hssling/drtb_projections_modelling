# GTB Report 2025 Data Repository Check

## Overview
**Location:** `d:\research-automation\tb_amr_project\SOURCES DATA\gtbreport2025-main\gtbreport2025-main`

The repository contains the code and data used for the Global Tuberculosis Report. The data is organized into several key directories:

### 1. `data/` (CSV Files - Usable)
This directory contains various CSV files related to health indicators, financing, and mortality codes.
- **`datahub/`**: Contains `9A706FD_ALL_LATEST.csv` (Universal Health Coverage Index scores).
- **`gf/`**: Global Fund pledges and contributions (2011-2025).
- **`mortality/`**: Mortality data including `dths_total.csv`, COD rankings, and VR quality.
- **`unaids/`**: TB/HIV co-management and enrollment data.
- **`oecd/`**: Donor and recipient codes and raw data.
- **`gho/`**: Global Health Observatory data.

### 2. `drtb/` (Drug Resistant TB)
- **Status:** Primarily contains R scripts (`.R`) and R Data files (`.rda`).
- **Path:** `drtb/indata/` contains `dr.est.rda` and `rel.rda`.
- **Note:** These files cannot be opened directly with standard text editors or Excel. They require R or specific Python libraries (like `pyreadr`, not currently installed).

### 3. `inc_mort/` (Incidence & Mortality Estimates)
- **Status:** Similar to `drtb`, contains R scripts and `.rda` files.
- **Path:** `inc_mort/estimates2024/` contains `global2024.rda`, `pop.rda` (population), `cty.rda`.
- **Note:** Contains the core estimation models and input data in binary R format.

### 4. `finance/`
- Contains R scripts for financial data analysis.

## Recommendations
- **For immediate analysis:** The CSV files in `data/` (especially mortality and financing) can be integrated immediately.
- **For DR-TB and Incidence/Mortality:** The raw data seems to be stored in `.rda` files. 
    - *Option A:* If you have R installed localy, you can export these to CSV.
    - *Option B:* We can try to assume the "source" csvs for these estimates might be the ones we already found (like `MDR_RR_TB_burden_estimates...csv` which we processed earlier), as `gtbreport` likely generates those outputs.

## Conclusion
The `gtbreport2025` repo is the "source code" for generating the WHO estimates. The final output files (like the one we analyzed in the previous step: `MDR_RR_TB_burden_estimates_2025-11-23.csv`) are likely the *products* of the scripts in this repo running on the `.rda` input data. Unless we need to modify the estimation methodology, working with the published CSV output files (as we did in Step 202) is likely more efficient.
