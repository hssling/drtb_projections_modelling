# MDR TB Data Summary for India

## Overview
Two key datasets regarding Multidrug-Resistant (MDR) and Rifampicin-Resistant (RR) TB in India were extracted from WHO sources.

### 1. MDR/RR TB Burden Estimates
**File:** `d:\research-automation\tb_amr_project\data\processed\mdr_tb_india_burden.csv`
**Source:** `MDR_RR_TB_burden_estimates_2025-11-23.csv`
**Years:** 2015 - 2024
**Key Metrics:**
- `e_rr_pct_new`: Estimated % of new cases with RR-TB
- `e_rr_pct_ret`: Estimated % of previously treated cases with RR-TB
- `e_inc_rr_num`: Estimated incidence of RR-TB cases

**Latest Data (2024 Estimates):**
- **% New Cases with RR-TB:** 3.6% (CI: 3.6 - 3.7%)
- **% Retreatment Cases with RR-TB:** 13.0% (CI: 12.0 - 13.0%)
- **Estimated Incident RR-TB Cases:** 130,000 (CI: 100,000 - 150,000)

### 2. MDR/XDR TB Treatment Outcomes
**File:** `d:\research-automation\tb_amr_project\data\processed\mdr_tb_india_outcomes.csv`
**Source:** `TB_outcomes_2025-11-23.csv`
**Years:** 2007 - 2022
**Key Metrics:**
- Cohort sizes (`mdr_coh`, `xdr_coh`)
- Treatment outcomes: Success, Failure, Died, Lost to follow-up

**Latest Data (2022):**
- **MDR TB Cohort:** 33,950
- **MDR TB Success Rate:** ~76.8% (26,076 / 33,950)
- **MDR TB Death Rate:** ~11.9% (4,052 / 33,950)
- **XDR TB Cohort:** 9,186
- **XDR TB Success Rate:** ~72.5% (6,663 / 9,186)

## Analysis & Recommendations
- **Trends:** There is a slight increasing trend in the estimated percentage of new cases with RR-TB (from 2.8% in 2015 to 3.6% in 2024).
- **Outcomes:** Treatment success rates for MDR and XDR TB have improved significantly compare to earlier years, now hovering around 70-75%.
- **Relevance:** This data is critical for the "Drug Resistant TB" section of the manuscript. It provides both the burden (magnitude of the threat) and the system's response effectiveness (treatment outcomes).

## Action Plan
- Use the **Burden Estimates** to frame the problem in the Introduction and for context in the Results.
- Use the **Outcomes Data** to analyze the effectiveness of recent policy changes (like Bedaquiline introduction) in the Discussion.
