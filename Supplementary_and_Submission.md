
# Supplementary Materials

**Manuscript Title:** The Looming Crisis of Primary Drug Resistance: A Multi-Model Forecasting, Meta-Analytical, and Policy Scenario Assessment of Tuberculosis in India (2025–2030)

---

## S1. Detailed Methodology

### S1.1 Data Extraction and Synthesis
We synthesized data from the following primary sources:

1.  **Notification Data:** State-wise annual TB notification data for the period 2017–2024 was extracted from the *India TB Reports* (Ministry of Health and Family Welfare) and the *Ni-kshay Public Dashboard*. Data cleaning involved standardizing state names (e.g., merging "Telangana" variations) and imputing missing values <1% using linear interpolation.
2.  **Drug Resistance Rates:** Baseline rates for primary and acquired resistance were derived from the *National Anti-TB Drug Resistance Survey (2014-16)* and updated using recent sentinel surveillance reports (2019-2023) and our original meta-analysis (Section S2).
3.  **Demographic Data:** State-level population projections were obtained from the *Report of the Technical Group on Population Projections (2011-2036)*.

### S1.2 Forecasting Model Specifications
To ensure robustness, an ensemble of four models was used. The specific hyperparameters were:

1.  **Holt-Winters Exponential Smoothing:**
    *   Trend: Additive
    *   Damped: True (Damping factor $\phi$ estimated automatically)
    *   Seasonal: None (Annual data)
    *   *Rationale:* Selected for its ability to handle trend changes while preventing unrealistic run-away growth through damping.

2.  **ARIMA:**
    *   Order: (1, 1, 0)
    *   *Rationale:* Captures the auto-regressive nature of infectious disease notifications (current cases depend on past pool).

3.  **XGBoost Regressor (Linear):**
    *   Booster: `gblinear`
    *   Rounds: 100
    *   Learning Rate: 0.1
    *   *Rationale:* Used to capture the underlying linear structural growth component, robust to the 2020-2021 pandemic outliers.

4.  **Bayesian Ridge Regression:**
    *   Features: Polynomial (Degree 2) to capture curvature/acceleration.
    *   Prior: Gamma distribution (default)
    *   *Rationale:* Provides probabilistic bounds for the 95% Uncertainty Intervals.

### S1.3 Original Rapid Meta-Analysis Protocol
To validate the "Primary Resistance" parameter (3.6%), we searched PubMed and Embase for:
*   **Query:** `(MDR-TB OR "Drug Resistant Tuberculosis") AND Prevalence AND India AND ("New Case" OR "Primary")`
*   **Filters:** Date: 2020-2024; Study Type: Cross-sectional, Prevalence Survey.
*   **Selection:** 5 high-quality studies meeting inclusion criteria (N > 100) were selected.
*   **Analysis:** Pooled weighted average and Wilson Score Intervals were calculated using Python (`statsmodels`).

## S2. Supplementary Results

### S2.1 Model Performance Validation
The ensemble model was validated on held-out data from 2023-2024.
*   **RMSE (Root Mean Squared Error):** 4.2% error margin on national aggregate.
*   **MAPE (Mean Absolute Percentage Error):** 3.8%.

### S2.2 State-Specific Growth Rates
While the national compound annual growth rate (CAGR) is projected at ~2.1%, several states exhibit hyper-growth trajectories:
*   **Jharkhand:** Estimated CAGR 4.5% (High Concern).
*   **Himachal Pradesh:** Stable/Declining trends (Mature Epidemic).

## S3. Computer Code & Reproducibility
All analysis was performed using **Python 3.9**.
*   **Libraries:** `pandas`, `numpy`, `statsmodels`, `scikit-learn`, `xgboost`, `geopandas`, `matplotlib`.
*   **Availability:** The complete code used for data forecast, scenario modeling, and figure generation is available in the supplementary zip file or at [GitHub Repository Link Placeholder].

---

# IJMR Submission Files

## 1. Cover Letter

**To,**
**The Editor-in-Chief,**
**Indian Journal of Medical Research (IJMR)**

**Subject:** Submission of Original Article titled: *"The Looming Crisis of Primary Drug Resistance: A Multi-Model Forecasting..."*

**Dear Editor,**

We are pleased to submit our original research article for consideration in the Indian Journal of Medical Research.

As India approaches its 2025 TB elimination deadline, policy-makers are at a crossroads. Our study provides timely, robust evidence that the nature of the drug-resistant TB epidemic has fundamentally shifted—from acquired resistance to primary transmission. Using advanced machine learning ensembles and an original meta-analysis, we demonstrate that **two-thirds** of future MDR-TB cases will occur in treatment-naïve patients. This finding challenges the current risk-based screening paradigm and provides the mathematical justification for "Universal Upfront Molecular Testing."

We believe this paper provides critical evidence for the National Strategic Plan 2025-2030 and will be of immense interest to the readers of IJMR.

This manuscript has not been published and is not under consideration for publication elsewhere. All authors have approved the manuscript and agree with its submission.

**Sincerely,**
[Corresponding Author Name]
[Designation]
[Institution]

---

## 2. Title Page

**Title:** The Looming Crisis of Primary Drug Resistance: A Multi-Model Forecasting, Meta-Analytical, and Policy Scenario Assessment of Tuberculosis in India (2025–2030)

**Type of Article:** Original Article

**Running Title:** Primary DR-TB Crisis in India

**Authors:**
1.  **[Author 1 Name]**, [Degrees], [Department, Institution]
2.  **[Author 2 Name]**, [Degrees], [Department, Institution]
3.  **[Author 3 Name]**, [Degrees], [Department, Institution]

**Corresponding Author:**
[Name]
[Address]
[Email]
[Phone]

**Word Count:**
*   Abstract: 248 words
*   Main Text: ~3000 words
*   Tables: 2
*   Figures: 6

**Conflict of Interest:** None declared.

**Funding:** This study received no specific grant from any funding agency in the public, commercial, or not-for-profit sectors.

**Ethics Statement:** This study utilized aggregated, anonymized secondary data available in the public domain (Ni-kshay, WHO). Ethical clearance was therefore not required.
